"""Independent Agent invocations, frozen context and durable run records."""

import asyncio
from contextlib import ExitStack, nullcontext
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
from threading import Thread
from pathlib import Path
import shutil
import stat
import time
import uuid

import ergora.agents.backends as agent_backends
import ergora.agents.native_sources as native_sources
import ergora.definitions.agents as agent_definitions
import ergora.agents.invocation as agents
import ergora.configuration.projects as projects
import ergora.agents.mcp as task_mcp
import ergora.definitions.workflows as workflow_definitions
import ergora.improvement.document_corrections as document_corrections
from ergora.runtime import budget_clock
from ergora.campaigns.recipient_gate import RecipientBlocked, RecipientGate, require_payload_support
from ergora.campaigns.records import CampaignFiles
from ergora.configuration import catalog as components
from ergora.configuration import validation as contracts
from ergora.development import dags
from ergora.runtime import processes
from ergora.storage.assets import inventory_tree, is_link, publish_directory
from ergora.configuration.bindings import validate_binding
from ergora.definitions.bundles import parse_json
from ergora.storage.state import State, file_lock, now
from ergora._paths import IMPORT_ROOT


_MAX_SESSION_TURNS = 10_000
_PROCESS_START_FIELDS = frozenset({'process_start_receipt', 'process_start_sha256'})


def _store(state: State, document: dict) -> None:
    with state.connect() as db:
        written = db.execute("INSERT INTO agent_runs VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET document=excluded.document "
                             "WHERE agent_runs.project=excluded.project",
                             (document["id"], document["project"], json.dumps(document)))
        if written.rowcount != 1:
            raise ValueError('Agent run ID belongs to another project')


def _prepare_role(state, project_id, role, prompt, timeout, skill_names, recall, template, freeze=None):
    if role not in agents.ROLE_CAPABILITIES:
        raise ValueError(f"Unknown agent role: {role}")
    if not prompt.strip() or not 1 <= timeout <= 3600:
        raise ValueError("Require a prompt and timeout of 1–3600 seconds")
    project = state.project(project_id)
    configuration = projects.effective_configuration(project)
    context = {"skills": [], "memories": []}
    task = prompt
    if skill_names:
        import ergora.definitions.skills as skill_assets

        active = {head["name"]: head for head in skill_assets.versions(state, project_id)["active"]}
        for name in skill_names:
            if name not in active:
                raise ValueError(f"Unknown active skill: {name}")
            bundle = skill_assets.get(state, project_id, active[name]["digest"])
            resource = Path(bundle['path'])
            if freeze is not None:
                before = inventory_tree(resource)
                target = freeze[0] / 'skills' / name
                target.parent.mkdir(exist_ok=True)
                shutil.copytree(resource, target)
                if inventory_tree(target) != before:
                    raise ValueError('Skill changed while freezing ordinary session context')
                resource = freeze[1] / 'skills' / name
            context["skills"].append({"name": name, "digest": bundle["digest"]})
            prompt += f"\n\nSelected skill {name}; resources: {resource}\n" + ((target if freeze is not None else resource) / "SKILL.md").read_text(encoding="utf-8")
    if recall:
        import ergora.improvement.memory as memory

        recalled = memory.search(state, project_id, recall, limit=5, project=project)
        context["memories"] = recalled["results"]
        prompt += "\n\nProject observations with provenance (verify their applicability):\n" + json.dumps(recalled, ensure_ascii=False)
    binding = configuration["layers"][role]["binding"]
    validate_binding(role, binding)
    schema = None
    if template:
        import ergora.native.resources as native_resources
        contract = native_resources.agent_contract(template)
        if role not in contract["agents"]:
            raise ValueError("This template does not use the selected agent role")
        schema = agents.result_schema(contract["agents"][role]["artifacts"], role == "reviewer")
        prompt += "\n\nTemplate role requirements (return exactly one matching JSON object):\n" + json.dumps(
            {"requirements": contract["agents"][role], "result_schema": schema}, ensure_ascii=False)
    return prompt, schema, {'project': project_id, 'role': role, 'binding': binding,
        'project_revision': project['revision'], 'context': context, 'template': template,
        'suffix': prompt[len(task):], 'schema': schema}, configuration


def run_agent(state: State, project_id: str, role: str, prompt: str, timeout: int = 300,
              skill_names: list[str] | None = None, recall: str | None = None,
              template: str | None = None, *, session_intent: str | None = None,
              expected_revision: int | None = None, codex_config: Path | None = None) -> dict:
    if session_intent is not None:
        return _start_session(state, project_id, role, prompt, timeout, skill_names, recall, template,
                              session_intent, expected_revision, codex_config)
    prepared, schema, document, configuration = _prepare_role(state, project_id, role, prompt, timeout, skill_names, recall, template)
    document.pop('suffix')
    document.pop('schema')
    run_id = uuid.uuid4().hex
    document.update(id=run_id, started=now(), status='running',
                    configuration=configuration,
                    prompt_sha256=hashlib.sha256(prepared.encode()).hexdigest())
    _store(state, document)
    try:
        document.update(agents.invoke(document['binding'], role, prepared, Path(state.project(project_id)['repo']),
                                      state.root / 'runs' / run_id, timeout, schema, codex_config=codex_config))
    except (OSError, ValueError) as error:
        document.update(status='failed', error=str(error))
    document['finished'] = now()
    _store(state, document)
    return document


def _admit_input(state: State, project_id: str, source: Path, *, backend: str | None,
                 model: str | None, reason: str | None, mode: str, codex_config: Path | None,
                 binding_override: dict | None = None, input_digest: str | None = None,
                 _fixed_check_proof: dict | None = None) -> tuple[dict, dict]:
    """One current admission produces both the preview and the persisted call contract."""
    contracts.validate(mode, {"enum": ["text-only", "task-mcp"]}, "Composition call mode")
    prepared = workflow_definitions.inspect_input(source, material=True)
    if input_digest is not None and prepared['digest'] != input_digest:
        raise ValueError('Composition input differs from the explicitly selected digest')
    request = prepared['request']
    fixed = dags.fixed_check_review(prepared['composition'])
    if fixed is not None:
        proof = _fixed_check_proof
        if (not isinstance(proof, dict) or proof.get('status') != 'validated' or proof.get('project') != project_id
                or proof.get('instance') != fixed[1]['path'] or request['instance'] != fixed[1]['path']
                or request['input_origin'] != 'workflow-port' or input_digest is None):
            raise ValueError('Fixed-check review input requires its gated graph coordinator')
    leaf = next(item for item in prepared["composition"]["instances"] if item["path"] == request["instance"])
    permissions = leaf["permissions"]
    if permissions["write"] or permissions["shell"] or permissions["network"]:
        raise ValueError(f"{'Text-only' if mode == 'text-only' else 'Task MCP'} calls cannot satisfy write, shell or network requests; use a read-only leaf")
    return prepared, _admission(state, project_id, prepared, backend=backend, model=model, reason=reason,
        mode=mode, codex_config=codex_config, binding_override=binding_override)


def _admission(state, project_id, prepared, *, backend, model, reason, mode, codex_config, binding_override):
    """Share selection and evidence, while each caller owns its authority checks."""
    project = state.project(project_id)
    leaf = next(item for item in prepared['composition']['instances'] if item['path'] == prepared['request']['instance'])
    permissions = leaf['permissions']
    reference = leaf["ref"]
    definition = agent_definitions.library(Path(prepared["path"]) / "assets").get(reference["id"], reference["version"])
    agent_definitions.validate_admission(definition)
    if binding_override is not None and (backend is not None or model is not None):
        raise ValueError("Choose a complete binding override or backend/model fields")
    binding = dict(binding_override) if binding_override is not None else (
        {"tool": backend} if backend and backend != leaf["backend_request"]["tool"]
        else dict(leaf["backend_request"]))
    if model is not None:
        binding["model"] = model
    policy = _composition_policy(leaf['role'], binding, definition['definition'].get('invocation_minimum'), mode, codex_config)
    chain = []
    path = leaf["path"]
    instances = {item["path"]: item for item in prepared["composition"]["instances"]}
    while path is not None:
        item = instances[path]
        chain.append({"path": path, "permissions": item["permissions"]})
        path = item["parent"]
    policy.update(requested_permissions=permissions,
                  permission_ceilings=[{"path": "supplied-grant", "permissions": prepared["request"]["grant"]["permissions"]},
                                       *reversed(chain)],
                  read_scope_semantics=("Declared upper bounds; actual guarantees are in capabilities" if mode == "workspace-task-mcp" else
                                        "Permission paths are upper bounds; only declared fixed resources are provided"),
                  sdk_check="top-level package presence only; actual compatibility/readiness checked during run" if mode != "text-only" else "not required")
    return {"schema_version": 1, "kind": "composition-admission", "project": project_id,
        "project_revision": project["revision"], "role": leaf["role"], "binding": binding,
        "requested_binding": leaf["backend_request"], "backend_reason": reason or (
            "operator-selected override" if backend or model else "definition-selected backend"),
        "input_digest": prepared["digest"], "input_request": prepared["request"],
        "prompt_sha256": prepared["request"]["prompt_sha256"],
        "context": {"resources": [{key: value for key, value in resource.items() if key != "text"}
                                  for resource in leaf["resources"]]},
        "policy": policy, "formal_execution_authorized": False}


def _composition_policy(role, binding, minimum, mode, codex_config):
    agents.validate_binding(role, binding, formal=True)
    components.validate_agent_minimum(binding, minimum)
    adapter = agent_backends.for_binding(binding, {"codex": {"config": codex_config}})
    adapter.check_invocation()
    adapter.check_mode(mode)
    policy = adapter.composition_policy(mode)
    if mode in ("task-mcp", "workspace-task-mcp"):
        task_mcp.check_available()
    return policy


def preflight_graph_leaf(leaf, codex_config):
    """Check the known text-only backend binding through original leaf admission."""
    _composition_policy(leaf['role'], leaf['backend_request'], leaf.get('invocation_minimum'), 'text-only', codex_config)


def check_input(state: State, project_id: str, source: Path, *, backend: str | None = None,
                model: str | None = None, reason: str | None = None, mode: str = "text-only",
                codex_config: Path | None = None, input_digest: str | None = None) -> dict:
    """Current admission only: no model, server, run record or formal authorization."""
    _, document = _admit_input(state, project_id, source, backend=backend, model=model, reason=reason, mode=mode,
                               codex_config=codex_config, input_digest=input_digest)
    return document


def run_input(state: State, project_id: str, source: Path, timeout: int = 300, *,
              backend: str | None = None, model: str | None = None, reason: str | None = None,
              codex_config: Path | None = None, mode: str = "text-only", binding_override: dict | None = None,
              result_schema: dict | None = None, env: dict | None = None,
              codex_bin: str = "codex", supervised: bool = False,
              input_digest: str | None = None, stop_requested=None, remaining=None,
              record_lifecycle: bool = False, deadline: float | None = None, run_id: str | None = None,
              expected_revision: int | None = None, _fixed_check_proof: dict | None = None) -> dict:
    """Run a restricted leaf through explicit admission and retain its original authority."""
    contracts.validate(timeout, {"type": "integer", "minimum": 1, "maximum": 3600}, "Agent timeout")
    prepared, document = _admit_input(state, project_id, source, backend=backend, model=model, reason=reason, mode=mode,
                                      codex_config=codex_config, binding_override=binding_override,
                                      input_digest=input_digest, _fixed_check_proof=_fixed_check_proof)
    if expected_revision is not None and document['project_revision'] != expected_revision:
        raise ValueError('Project revision changed before the workflow leaf was admitted')
    if run_id is not None:
        native_sources.session_id(run_id, 'Agent run ID')
        document['id'] = run_id
    observe_direct_child_start = (run_id is not None and not supervised and mode == 'text-only'
                                  and prepared['request']['input_origin'] == 'workflow-port')
    return _run_prepared(state, prepared, document, timeout, mode=mode, codex_config=codex_config,
        result_schema=result_schema, env=env, codex_bin=codex_bin, supervised=supervised,
        stop_requested=stop_requested, remaining=remaining, record_lifecycle=record_lifecycle, deadline=deadline,
        observe_direct_child_start=observe_direct_child_start)


def run_workspace(state: State, project_id: str, source: Path, cwd: Path, authority: dict, timeout: int, *,
                  binding: dict, codex_config: Path, result_schema: dict, env: dict,
                  codex_bin: str = 'codex', supervised: bool = False) -> dict:
    """Internal stage-driver call; only the original Executor establishes authority.

    A material snapshot remains non-authorizing. There is no CLI run-input mode
    for this operation. The original monitor owns attempts, cancellation and cwd.
    """
    contracts.validate(timeout, {"type": "integer", "minimum": 1, "maximum": 3600}, "Agent timeout")
    prepared = workflow_definitions.inspect_input(source, material=True)
    leaf = next(item for item in prepared['composition']['instances'] if item['path'] == prepared['request']['instance'])
    if (authority.get('kind') != 'formal-workspace-call' or authority.get('schema_version') != 1
            or authority['input_digest'] != prepared['digest']
            or authority['prompt_sha256'] != prepared['request']['prompt_sha256']
            or authority['member'] != leaf['path'] or authority['selection']['binding'] != binding
            or Path(authority['checkout']).resolve() != cwd.resolve()
            or leaf['role'] != 'implementer' or not leaf['permissions']['write']
            or not leaf['permissions']['shell'] or leaf['permissions']['network']):
        raise ValueError('Workspace input differs from the trusted formal work call or its supported capabilities')
    mode = 'workspace-task-mcp'
    document = _admission(state, project_id, prepared, backend=None, model=None,
        reason=authority['selection']['backend_reason'], mode=mode, codex_config=codex_config, binding_override=binding)
    if {key: document['policy'][key] for key in authority['selection']['policy']} != authority['selection']['policy']:
        raise ValueError('Workspace policy changed from the frozen formal work call')
    document.update(formal_call=authority, formal_execution_authorized=True)
    return _run_prepared(state, prepared, document, timeout, mode=mode, codex_config=codex_config,
        result_schema=result_schema, env=env, codex_bin=codex_bin, supervised=supervised, workspace=cwd)


def _run_prepared(state, prepared, document, timeout, *, mode, codex_config, result_schema, env,
                  codex_bin, supervised, workspace=None, stop_requested=None, remaining=None,
                  record_lifecycle=False, deadline=None, observe_direct_child_start=False):
    """One immutable snapshot, MCP lifecycle and native invocation evidence owner."""
    run_id = document.get("id") or uuid.uuid4().hex
    output = state.root / "runs" / run_id
    snapshot = output.with_name(run_id + ".input")
    if snapshot.resolve().is_relative_to(Path(prepared["path"]).resolve()):
        raise ValueError("Run storage cannot be inside the prepared input directory")
    schema = result_schema or agents.result_schema(["response"], document["role"] == "reviewer")
    document.update(kind="composition-agent-run", id=run_id, started=now(), status="preparing", template=None)
    _store(state, document)

    def active():
        if stop_requested is not None and stop_requested():
            if deadline is not None:
                raise KeyboardInterrupt
            raise ValueError('Original parent stopped during composition preparation')

    def copy_resource(source, destination):
        active()
        result = shutil.copy2(source, destination)
        active()
        return result

    try:
        if record_lifecycle:
            processes.prepare_supervised()
        active()
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(prepared["path"], snapshot, symlinks=True, copy_function=copy_resource)
        saved = workflow_definitions.inspect_input(snapshot, material=True)
        active()
        if saved["digest"] != prepared["digest"]:
            raise ValueError("Composition input changed while copying the run snapshot")
        if record_lifecycle:
            _confirm_analysis_input(saved, active=active)
        document.update(input_path=str(snapshot))
        native_mcp = None
        if mode in ("task-mcp", "workspace-task-mcp"):
            scope = task_mcp.freeze(saved, run_id, output.with_name(run_id + ".scope.json"))
            active()
            document["task_mcp"] = {"scope": scope}
            _store(state, document)
            preflight = task_mcp.launch(scope, output.with_name(run_id + ".mcp-preflight.jsonl"))
            document["task_mcp"]["preflight"] = asyncio.run(task_mcp.probe(
                preflight, output.with_name(run_id + ".mcp-preflight.stderr"),
                **({'stop_requested': stop_requested, 'remaining': remaining} if stop_requested is not None else {})))
            active()
            native_audit = output.with_name(run_id + ".mcp-native.jsonl")
            native_mcp = task_mcp.launch(scope, native_audit)
        document["status"] = "running"
        _store(state, document)
        working = workspace if workspace is not None else output.with_name(run_id + ".cwd")
        if workspace is None:
            working.mkdir(mode=0o700)
        active()
        if record_lifecycle:
            document['invocation_entered'] = True
            _store(state, document)
        invoked = agents.invoke(document["binding"], document["role"], saved["prompt"], working, output,
            min(timeout, remaining()) if remaining is not None else timeout,
            schema, codex_config=codex_config, mode=mode, task_mcp=native_mcp, env=env, codex_bin=codex_bin,
            supervised=supervised, **({'stop_requested': stop_requested} if stop_requested is not None else {}),
            **({'deadline': deadline} if deadline is not None else {}),
            **({'record_lifecycle': True} if record_lifecycle else {}),
            **({'observe_direct_child_start': True} if observe_direct_child_start else {}))
        start = invoked.pop('direct_child_start', None)
        document.update(invoked)
        if start is not None:
            receipt = {'binding': _process_start_binding(document, saved['request']), 'observation': start}
            document.update(process_start_receipt=receipt, process_start_sha256=native_sources.sha(receipt))
        if mode in ("task-mcp", "workspace-task-mcp") and document["status"] == "succeeded":
            document["task_mcp"]["native"] = task_mcp.verify_native(native_audit, scope["sha256"])
        if deadline is None or document['status'] != 'cancelled':
            active()
    except KeyboardInterrupt:
        # SDK preflight runs before the native process owner handles Ctrl+C.
        document.update(status="cancelled", error="Agent preparation or invocation interrupted")
    except (OSError, ValueError) as error:
        document.update(status="failed", error=str(error))
    finally:
        if record_lifecycle and not (output / 'process-cleanup.json').exists():
            try:
                descendants = processes._reap_children()
                cleanup = {'schema_version': 1, 'kind': 'composition-preparation-cleanup',
                           'owner': processes.identity(os.getpid()), 'descendants': descendants,
                           'remaining_children': Path(f'/proc/{os.getpid()}/task/{os.getpid()}/children').read_text().split()}
                _publish_session_packet(output.with_name(run_id + '.preparation-cleanup'), {'record.json': native_sources.encode(cleanup)})
            except (OSError, ValueError) as error:
                document.update(status='unknown', error='Original preparation cleanup is unconfirmed: ' + str(error))
    document["finished"] = now()
    _store(state, document)
    return document


def runs(state: State, project_id: str) -> list[dict]:
    state.project(project_id)
    with state.connect() as db:
        return [json.loads(row[0]) for row in db.execute(
            "SELECT document FROM agent_runs WHERE project=? ORDER BY rowid DESC LIMIT 100", (project_id,))]


def cycle_analysis_path(control_home: Path, authorization_sha256: str, ordinal: int, phase: str = 'screen') -> Path:
    """The single opportunity is independent of a caller's proposed packet/run ID."""
    key = {'authorization_sha256': authorization_sha256, 'ordinal': ordinal, 'phase': phase}
    return Path(control_home) / 'runs' / ('.cycle-analysis-' + native_sources.sha(key))


def _analysis_identity(prepared, authority):
    slot = authority['slot']
    contracts.validate(slot['ordinal'], {'type': 'integer', 'minimum': -1, 'maximum': 31}, 'Analysis ordinal')
    if slot['phase'] != ('baseline' if slot['ordinal'] == -1 else 'screen'):
        raise ValueError('Analysis phase differs from its original ordinal')
    request, composition = prepared['request'], prepared['composition']
    leaf = next(item for item in composition['instances'] if item['path'] == request['instance'])
    if (leaf['kind'] != 'agent' or leaf['ref']['digest'] != slot['definition_digest']
            or prepared['digest'] != authority['input_digest']
            or request['preview_sha256'] != authority['composition_preview_sha256']
            or request['prompt_sha256'] != authority['prompt_sha256']
            or request['task_sha256'] != native_sources.sha(authority['packet'])
            or slot['packet_sha256'] != request['task_sha256']
            or authority['mode'] not in ('text-only', 'task-mcp')):
        raise ValueError('Analysis input differs from the complete frozen slot and packet')
    if (Path(prepared['path']) / 'task.txt').read_bytes() != native_sources.encode(authority['packet']):
        raise ValueError('Analysis task is not the complete canonical packet')
    permissions = leaf['permissions']
    if permissions['write'] or permissions['shell'] or permissions['network']:
        raise ValueError('Analysis requires an actual readonly leaf')
    path, chain = leaf['path'], []
    instances = {item['path']: item for item in composition['instances']}
    while path is not None:
        member = instances[path]
        chain.append(member)
        path = member['parent']
    expected_run = native_sources.sha(slot)[:32]
    if authority['fixed_run_id'] != expected_run:
        raise ValueError('Analysis run differs from its deterministic original slot')
    return expected_run, leaf, list(reversed(chain))


def _confirm_analysis_input(prepared, *, active=lambda: None):
    root = Path(prepared['path'])
    _, files, _ = inventory_tree(root, label='Analysis input', max_directories=1000, max_depth=48)
    for name, details in files.items():
        active()
        path = root / name
        raw = native_sources.artifact(path.parent, path.name, native_sources.PACKET_BYTES, confirm_durable=True)
        if hashlib.sha256(raw).hexdigest() != details['sha256']:
            raise ValueError('Analysis input changed during original durable confirmation')
    active()
    if workflow_definitions.inspect_input(root, material=True) != prepared:
        raise ValueError('Analysis complete input changed during durable confirmation')


def _analysis_cleanup(state, intent, attempt, *, durable):
    storage, run_id = state.root / 'runs', intent['run_id']
    raw = native_sources.artifact(storage / run_id, 'process-cleanup.json', native_sources.PACKET_BYTES, confirm_durable=durable)
    cleanup = parse_json(raw.decode('utf-8'), 'Original model cleanup', finite=True, bounded=True)
    if (cleanup.get('kind') != 'supervised-process-cleanup' or cleanup['owner'] != attempt['owner']
            or cleanup['model'] is None or cleanup['model_waited'] is not True
            or cleanup['remaining_children'] != [] or type(cleanup['returncode']) is not int
            or any(item['process'] is None or item['wait_pid'] != item['process']['pid']
                   or type(item['wait_status']) is not int for item in cleanup['descendants'])):
        raise ValueError('Original model tree lacks confirmed waits and complete cleanup')
    result = {'model': {'state': 'reaped', 'sha256': hashlib.sha256(raw).hexdigest(), 'observation': cleanup},
              'MCP': {'state': 'not_requested'}}
    if intent['authority']['mode'] == 'task-mcp':
        scope_raw = native_sources.artifact(storage, run_id + '.scope.json', task_mcp.MAX_SCOPE_BYTES, confirm_durable=durable)
        scope_sha = hashlib.sha256(scope_raw).hexdigest()
        result['MCP'] = {'state': 'closed', 'scope_sha256': scope_sha}
        for phase in ('preflight', 'native'):
            audit = native_sources.artifact(storage, run_id + '.mcp-' + phase + '.jsonl', 1_000_000, confirm_durable=durable)
            result['MCP'][phase] = task_mcp.verify_cleanup(audit, scope_sha)
    return result


def _analysis_preparation_cleanup(state, run_id, attempt):
    folder = state.root / 'runs' / (run_id + '.preparation-cleanup')
    raw = native_sources.artifact(folder, 'record.json', native_sources.PACKET_BYTES, confirm_durable=True)
    cleanup = parse_json(raw.decode('utf-8'), 'Original preparation cleanup', finite=True, bounded=True)
    if (cleanup['kind'] != 'composition-preparation-cleanup' or cleanup['owner'] != attempt['owner']
            or cleanup['remaining_children'] != [] or not isinstance(cleanup['descendants'], list)
            or any(item['process'] is None or item['wait_pid'] != item['process']['pid']
                   or type(item['wait_status']) is not int for item in cleanup['descendants'])):
        raise ValueError('Original preparation tree lacks complete cleanup')
    return {'state': 'not_started', 'preparation_sha256': hashlib.sha256(raw).hexdigest(), 'observation': cleanup}


def inspect_cycle_analysis(state: State, project_id: str, run_id: str, *, authority: dict | None = None) -> dict:
    """Confirm the same original receipt; never admit, run, or recover an effect."""
    native_sources.session_id(run_id, 'Analysis run ID')
    state.project(project_id)
    if authority is None:
        authority = native_sources.record(state, project_id, run_id)['cycle_analysis']
    slot = authority['slot']
    folder = cycle_analysis_path(state.root, slot['authorization_sha256'], slot['ordinal'], slot['phase'])
    observed = {'schema_version': 1, 'kind': 'training-cycle-analysis-receipt', 'slot': slot, 'run_id': run_id,
                'intent_sha256': None, 'attempt_sha256': None, 'outcome': 'needs_reconciliation',
                'result_sha256': None, 'cleanup': {'model': {'state': 'unknown'}, 'MCP': {'state': 'unknown'}},
                'receipt_sha256': None}
    try:
        intent = native_sources.packet(folder, 'intent.json', confirm_durable=True)
        attempt = native_sources.packet(folder, 'attempt.json', confirm_durable=True)
        observed.update(intent_sha256=native_sources.sha(intent), attempt_sha256=native_sources.sha(attempt))
        if (intent['project'] != project_id or intent['run_id'] != run_id or intent['authority'] != authority
                or attempt['intent_sha256'] != observed['intent_sha256']):
            raise ValueError('Analysis opportunity differs from its original intent/attempt')
        if (folder / 'interrupted').exists() or (folder / 'interrupted').is_symlink():
            raise ValueError('Original parent stopped during final analysis receipt synchronization')
        final = native_sources.packet(folder / 'final', confirm_durable=True)
        receipt = final['receipt']
        if (final['receipt_sha256'] != native_sources.sha(receipt) or receipt['slot'] != slot
                or receipt['run_id'] != run_id or receipt['intent_sha256'] != observed['intent_sha256']
                or receipt['attempt_sha256'] != observed['attempt_sha256']):
            raise ValueError('Analysis receipt differs from its original opportunity')
        if receipt['outcome'] == 'provisional':
            confirmation = native_sources.packet(folder / 'confirmation', confirm_durable=True)
            if (confirmation['schema_version'] != 1 or confirmation['kind'] != 'training-cycle-analysis-confirmation'
                    or confirmation['run_id'] != run_id or confirmation['receipt_sha256'] != final['receipt_sha256']
                    or confirmation['intent_sha256'] != observed['intent_sha256']
                    or confirmation['attempt_sha256'] != observed['attempt_sha256']
                    or confirmation['operation_sha256'] != native_sources.sha(authority['operation'])
                    or confirmation['owner'] != attempt['owner'] or confirmation['boot_id'] != attempt['boot_id']
                    or type(confirmation['confirmed_ns']) is not int or confirmation['confirmed_ns'] < attempt['started_ns']
                    or type(confirmation['remaining_seconds']) not in (int, float)
                    or not 0 < confirmation['remaining_seconds'] <= authority['maximum_seconds']
                    or confirmation['confirmed_ns'] - attempt['started_ns'] >= authority['maximum_seconds'] * 1_000_000_000):
                raise ValueError('Analysis has no original owner confirmation within its fixed allowance')
            origin = authority['preparation']
            path = Path(origin['path'])
            raw_origin = native_sources.artifact(path.parent, path.name, origin['bytes'], confirm_durable=True)
            preparation = parse_json(raw_origin.decode('utf-8'), 'Original slot preparation', finite=True, bounded=True)
            if (hashlib.sha256(raw_origin).hexdigest() != origin['sha256'] or len(raw_origin) != origin['bytes']
                    or preparation['kind'] != 'training-cycle-analysis-preparation'
                    or preparation['authorization_sha256'] != slot['authorization_sha256']
                    or preparation['ordinal'] != slot['ordinal'] or preparation['phase'] != slot['phase']
                    or preparation['operation_id'] != authority['operation']['identity']['operation_id']
                    or preparation['boot_id'] != confirmation['boot_id']
                    or type(preparation['started_ns']) is not int or preparation['started_ns'] > attempt['started_ns']
                    or confirmation['confirmed_ns'] - preparation['started_ns'] >= authority['maximum_seconds'] * 1_000_000_000
                    or confirmation['remaining_seconds'] > authority['maximum_seconds'] -
                    (confirmation['confirmed_ns'] - preparation['started_ns']) / 1_000_000_000):
                raise ValueError('Analysis confirmation lost its immutable slot preparation origin')
            saved = workflow_definitions.inspect_input(state.root / 'runs' / (run_id + '.input'), material=True)
            _analysis_identity(saved, authority)
            _confirm_analysis_input(saved)
            raw = native_sources.artifact(state.root / 'runs' / run_id, 'result.json', 8_388_608, confirm_durable=True)
            if hashlib.sha256(raw).hexdigest() != receipt['result_sha256']:
                raise ValueError('Analysis result changed from the original receipt')
            agents.validate_result(parse_json(raw.decode('utf-8'), 'Analysis result', finite=True, bounded=True),
                                   agents.result_schema(['response'], final['role'] == 'reviewer'))
            prompt = native_sources.artifact(state.root / 'runs' / (run_id + '.protocol'), 'prompt.txt',
                               saved['request']['prompt_bytes'], confirm_durable=True)
            if prompt != saved['prompt'].encode('utf-8'):
                raise ValueError('Analysis original prompt differs from its complete snapshot')
            if (_analysis_cleanup(state, intent, attempt, durable=True) != receipt['cleanup']
                    or receipt['cleanup']['model']['observation']['returncode'] != 0):
                raise ValueError('Analysis cleanup differs from its original receipt')
        return {**receipt, 'receipt_sha256': final['receipt_sha256'],
                'receipt': {'path': str(folder / 'final' / 'record.json'),
                            'sha256': hashlib.sha256(native_sources.encode(final)).hexdigest()}}
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        return {**observed, 'error': str(error)}


def _reserve_analysis(state, project_id, prepared, authority, run_id, chain, folder, stop_requested):
    import ergora.training.cycles as training_cycles
    import ergora.training.execution_protocol as training_execution_protocol
    slot = authority['slot']
    reservation = nullcontext()
    if slot['ordinal'] >= 0:
        plan, authorization = training_execution_protocol.resolve_cycle_snapshot(authority['operation'])
        execution = authorization['execution']
        experiment = plan['definition']['candidates'][slot['ordinal']]['experiment_id']
        submission = Path(execution['state_directory']) / 'ergora' / 'training-submissions'
        native_sources.directory_identity(submission)
        reservation = file_lock(submission / (experiment + '.lock'), blocking=False)
    # The original submission lock precedes our single-slot lock. A skip and
    # an analyst opportunity can never both win their last admission.
    with reservation, file_lock(folder.with_suffix('.lock'), blocking=False):
        if folder.exists() or folder.is_symlink():
            return None
        if slot['ordinal'] >= 0:
            training_execution_protocol.require_not_skipped(execution, experiment)
        training_cycles.validate_analysis_authority(state, project_id, authority, prepared=prepared)
        if stop_requested() or training_cycles.analysis_authority_remaining(authority) <= 0:
            raise ValueError('Original analysis parent stopped before durable reservation')
        contracts.validate(authority['maximum_seconds'], {'type': 'integer', 'minimum': 1, 'maximum': 3600}, 'Analysis cap')
        intent = {'schema_version': 1, 'kind': 'training-cycle-analysis-intent', 'project': project_id,
                  'run_id': run_id, 'authority': authority, 'ancestors': chain}
        boot, ticks = budget_clock._clock()
        attempt = {'schema_version': 1, 'kind': 'training-cycle-analysis-attempt',
                   'intent_sha256': native_sources.sha(intent), 'owner': processes.identity(os.getpid()),
                   'boot_id': boot, 'started_ns': ticks}
        _publish_session_packet(folder, {'intent.json': native_sources.encode(intent), 'attempt.json': native_sources.encode(attempt)})
        return intent, attempt


def run_cycle_analysis(state: State, project_id: str, prepared_input: Path, authority: dict, *, stop_requested) -> dict:
    """One trusted controller opportunity, using its existing operation and clock."""
    import ergora.training.cycles as training_cycles

    slot = authority['slot']
    folder = cycle_analysis_path(state.root, slot['authorization_sha256'], slot['ordinal'], slot['phase'])
    if folder.exists() or folder.is_symlink():
        return inspect_cycle_analysis(state, project_id, authority['fixed_run_id'], authority=authority)
    prepared = workflow_definitions.inspect_input(prepared_input, material=True)
    authority = training_cycles.validate_analysis_authority(state, project_id, authority, prepared=prepared)
    run_id, leaf, chain = _analysis_identity(prepared, authority)
    slot = authority['slot']
    folder = cycle_analysis_path(state.root, slot['authorization_sha256'], slot['ordinal'], slot['phase'])
    storage = state.root / 'runs'
    storage.mkdir(parents=True, exist_ok=True)
    if folder.exists() or folder.is_symlink():
        return inspect_cycle_analysis(state, project_id, run_id, authority=authority)
    try:
        reserved = _reserve_analysis(state, project_id, prepared, authority, run_id, chain, folder, stop_requested)
    except BlockingIOError:
        reserved = None
    if reserved is None:
        return inspect_cycle_analysis(state, project_id, run_id, authority=authority)
    intent, attempt = reserved
    stopped = False

    def remaining():
        actual_boot, actual_ticks = budget_clock._clock()
        if actual_boot != attempt['boot_id'] or actual_ticks < attempt['started_ns']:
            raise ValueError('Analysis original attempt clock changed')
        return min(training_cycles.analysis_authority_remaining(authority),
                   authority['maximum_seconds'] - (actual_ticks - attempt['started_ns']) / 1_000_000_000)

    def should_stop():
        nonlocal stopped
        if not stopped:
            try:
                stopped = bool(stop_requested() or remaining() <= 0)
                if not stopped:
                    training_cycles.validate_analysis_authority(state, project_id, authority, prepared=prepared)
            except (OSError, ValueError, KeyError, TypeError):
                stopped = True
        return stopped

    receipt = {'schema_version': 1, 'kind': 'training-cycle-analysis-receipt', 'slot': slot,
               'run_id': run_id, 'intent_sha256': native_sources.sha(intent), 'attempt_sha256': native_sources.sha(attempt),
               'outcome': 'needs_reconciliation', 'result_sha256': None,
               'cleanup': {'model': {'state': 'unknown'}, 'MCP': {'state': 'unknown'}}}
    try:
        if should_stop():
            raise ValueError('Original parent stopped after analysis reservation')
        document = _admission(state, project_id, prepared, backend=None, model=None,
            reason='frozen controller analyst', mode=authority['mode'], codex_config=None, binding_override=slot['binding'])
        document.update(id=run_id, cycle_analysis=authority, formal_execution_authorized=False)
        run = _run_prepared(state, prepared, document, authority['maximum_seconds'], mode=authority['mode'],
            codex_config=None, result_schema=None, env=None, codex_bin='codex', supervised=True,
            stop_requested=should_stop, remaining=remaining, record_lifecycle=True)
        if run['status'] != 'succeeded':
            receipt['error'] = run.get('error', run['status'])
            if run.get('invocation_entered'):
                receipt.update(cleanup=_analysis_cleanup(state, intent, attempt, durable=True), outcome='failed')
            elif authority['mode'] == 'text-only' and run['status'] != 'unknown':
                receipt.update(outcome='failed', cleanup={
                    'model': _analysis_preparation_cleanup(state, run_id, attempt), 'MCP': {'state': 'not_requested'}})
        else:
            cleanup = _analysis_cleanup(state, intent, attempt, durable=True)
            raw = native_sources.artifact(storage / run_id, 'result.json', 8_388_608, confirm_durable=True)
            if hashlib.sha256(raw).hexdigest() != run['result_sha256'] or should_stop():
                raise ValueError('Analysis result lost its original identity or parent allowance')
            receipt.update(outcome='provisional', result_sha256=run['result_sha256'], cleanup=cleanup)
    except (OSError, ValueError, KeyError, TypeError) as error:
        receipt['error'] = str(error)
    final = {'receipt': receipt, 'receipt_sha256': native_sources.sha(receipt), 'role': leaf['role']}
    _publish_session_packet(folder / 'final', {'record.json': native_sources.encode(final)})
    if receipt['outcome'] == 'provisional':
        try:
            if should_stop():
                raise ValueError('Original parent stopped during final receipt synchronization')
            boot, ticks = budget_clock._clock()
            allowance = remaining()
            confirmation = {'schema_version': 1, 'kind': 'training-cycle-analysis-confirmation',
                'run_id': run_id, 'receipt_sha256': final['receipt_sha256'],
                'intent_sha256': native_sources.sha(intent), 'attempt_sha256': native_sources.sha(attempt),
                'operation_sha256': native_sources.sha(authority['operation']), 'owner': attempt['owner'],
                'boot_id': boot, 'confirmed_ns': ticks, 'remaining_seconds': allowance}
            _publish_session_packet(folder / 'confirmation', {'record.json': native_sources.encode(confirmation)})
            if should_stop():
                raise ValueError('Original parent stopped during confirmation synchronization')
        except (OSError, ValueError, KeyError, TypeError) as error:
            _publish_session_packet(folder / 'interrupted', {'record.json': native_sources.encode({
                'run_id': run_id, 'receipt_sha256': final['receipt_sha256'], 'reason': str(error)})})
    return inspect_cycle_analysis(state, project_id, run_id, authority=authority)






def _process_start_binding(run, request):
    return {'run_id': run['id'], 'project': run['project'], 'project_revision': run['project_revision'],
            'input_digest': run['input_digest'], 'instance': request['instance'],
            'preview_sha256': request['preview_sha256'], 'prompt_sha256': request['prompt_sha256']}


def _observe_process_start(run, saved_input, prompt):
    if _PROCESS_START_FIELDS.isdisjoint(run):
        return {'available': False, 'state': 'not_recorded', 'error': 'No historical direct-child start was recorded'}
    if not _PROCESS_START_FIELDS.issubset(run):
        return {'available': False, 'state': 'missing', 'error': 'Historical direct-child start receipt is incomplete'}
    try:
        receipt, digest = run['process_start_receipt'], run['process_start_sha256']
        if (not isinstance(receipt, dict) or receipt.keys() != {'binding', 'observation'}
                or not isinstance(receipt['binding'], dict) or not isinstance(receipt['observation'], dict)):
            raise ValueError('Invalid historical direct-child start receipt')
        contracts.validate(digest, contracts.COMPOSITION_INPUT['$defs']['digest'], 'Process start receipt SHA256')
        if native_sources.sha(receipt) != digest:
            raise native_sources.ArtifactIdentityError('Historical direct-child start receipt differs from its recorded SHA256')
        for name, evidence in (('input', saved_input), ('prompt', prompt)):
            if not evidence['available']:
                return {'available': False, 'state': evidence['state'],
                        'error': f'Cannot verify process start against original {name}: {evidence["error"]}'}
        request = saved_input['request']
        policy = run.get('policy')
        if (run.get('formal_execution_authorized') is not False or not isinstance(policy, dict)
                or policy.get('mode') != 'text-only' or request['input_origin'] != 'workflow-port'
                or type(run.get('project_revision')) is not int or not isinstance(run.get('finished'), str)
                or run.get('status') not in ('succeeded', 'failed', 'timed_out', 'cancelled')):
            raise ValueError('Historical direct-child start requires an original terminal text-only graph leaf')
        recorded = receipt['binding']
        expected = _process_start_binding(run, request)
        if recorded.keys() != expected.keys() or any(type(recorded[key]) is not type(value)
                                                      for key, value in expected.items()):
            raise ValueError('Invalid historical direct-child start binding')
        if recorded != expected:
            raise native_sources.ArtifactIdentityError('Historical direct-child start differs from its original run or frozen input')
        observation = receipt['observation']
        if (observation.keys() == {'state', 'error'} and observation['state'] in ('missing', 'unknown', 'invalid')
                and isinstance(observation['error'], str)):
            return {'available': False, **observation}
        process = observation.get('process')
        if (observation.keys() != {'process'} or not _process_identity(process)
                or str(uuid.UUID(process['boot_id'])) != process['boot_id']):
            raise ValueError('Invalid historical direct-child process identity')
    except (ValueError, RecursionError) as error:
        return {'available': False, **native_sources.observation_failure(error)}
    return {'available': True, 'state': 'available', 'kind': 'historical-direct-child-start',
            'process': process, 'receipt_sha256': digest}


def inspect_run(state: State, project_id: str, run_id: str, *, max_result_bytes: int = 8_388_608) -> dict:
    """Observe original composition material without current admission or redispatch."""
    contracts.validate(run_id, {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"}, "Run ID")
    contracts.validate(max_result_bytes, {"type": "integer", "minimum": 1}, "Result byte limit")
    document = native_sources.record(state, project_id, run_id)
    if document.get("kind") != "composition-agent-run":
        raise ValueError("Select an original composition agent run")
    storage = state.root / "runs"
    run = {name: value for name, value in document.items() if name not in _PROCESS_START_FIELDS}
    observed = {"schema_version": 1, "kind": "composition-run-observation", "run": run,
                "formal_execution_authorized": False}
    request = document.get("input_request")
    try:
        prepared = workflow_definitions.inspect_input(storage / (run_id + ".input"), material=True)
        if (prepared["digest"] != document.get("input_digest")
                or native_sources.encode(prepared["request"]) != native_sources.encode(request)
                or prepared["request"]["prompt_sha256"] != document.get("prompt_sha256")):
            raise native_sources.ArtifactIdentityError("Saved input differs from the original run input identity")
        leaf = next(item for item in prepared['composition']['instances']
                    if item['path'] == prepared['request']['instance'])
        components.validate_agent_minimum(document.get('binding'), leaf.get('invocation_minimum'))
        observed["input"] = {"available": True, **prepared}
    except (OSError, ValueError, RecursionError) as error:
        observed["input"] = {"available": False, **native_sources.observation_failure(error)}
    try:
        contracts.validate(request, contracts.COMPOSITION_INPUT, "Original input request")
        raw = native_sources.artifact(storage / (run_id + ".protocol"), "prompt.txt", request["prompt_bytes"])
        digest = hashlib.sha256(raw).hexdigest()
        if (len(raw) != request["prompt_bytes"] or digest != request["prompt_sha256"]
                or digest != document.get("prompt_sha256")):
            raise native_sources.ArtifactIdentityError("Original invocation prompt differs from its recorded identity")
        if observed["input"]["available"] and raw != prepared["prompt"].encode("utf-8"):
            raise native_sources.ArtifactIdentityError("Original invocation prompt differs from the frozen input")
        observed["prompt"] = {"available": True, "bytes": len(raw), "sha256": digest,
                              "input_compared": observed["input"]["available"]}
    except (OSError, ValueError, RecursionError) as error:
        observed["prompt"] = {"available": False, **native_sources.observation_failure(error)}
    observed['process_start'] = _observe_process_start(document, observed['input'], observed['prompt'])
    if document.get("result_sha256") is None:
        observed["result"] = {"available": False, "state": "not_recorded",
                              "error": "No original structured result identity was recorded"}
    else:
        try:
            raw = native_sources.artifact(storage / run_id, "result.json", max_result_bytes)
            digest = hashlib.sha256(raw).hexdigest()
            if digest != document["result_sha256"]:
                raise native_sources.ArtifactIdentityError("Structured result differs from its original run SHA256")
            observed["result"] = {"available": True, "bytes": len(raw), "sha256": digest,
                                  "document": parse_json(raw.decode("utf-8"), "Agent result", finite=True, bounded=True)}
        except (OSError, ValueError, RecursionError) as error:
            observed["result"] = {"available": False, **native_sources.observation_failure(error)}
    return observed


def output(state: State, project_id: str, run_id: str, *, native_history: bool = False,
           offset: int = 0, limit: int = 65_536, revision: str | None = None) -> dict:
    document = native_sources.record(state, project_id, run_id)
    if document.get('kind') == 'native-agent-run':
        document = _observe_session_run(state, document)
    streams = {}
    for name in ("stdout", "stderr"):
        path = state.root / "runs" / run_id / f"{name}.txt"
        if not path.exists():
            streams[name] = {"available": False, "text": "", "truncated": False}
            continue
        with path.open("rb") as source:
            content = source.read(65537)
        streams[name] = {"available": True, "text": content[:65536].decode("utf-8", errors="replace"), "truncated": len(content) > 65536}
    result = {"id": run_id, "status": document["status"], "streams": streams}
    if document.get('kind') == 'native-agent-run':
        result['result'] = {'available': False, 'reason': 'No complete original result identity was recorded'}
        if document.get('result_sha256') is not None:
            try:
                request = native_sources.packet(native_sources.turn_folder(state, run_id), 'request.json')
                name = 'result.json' if request['schema'] is not None else 'result.txt'
                raw = native_sources.artifact(state.root / 'runs' / run_id, name, 8_388_608)
                if hashlib.sha256(raw).hexdigest() != document['result_sha256']:
                    raise ValueError('Final message differs from its original result SHA256')
                result['result'] = {'available': True, 'text': raw.decode('utf-8'), 'bytes': len(raw),
                                    'sha256': document['result_sha256']}
            except (OSError, ValueError) as error:
                result['result']['reason'] = str(error)
    if native_history:
        contracts.validate(offset, {"type": "integer", "minimum": 0, "maximum": 2**63 - 1}, "History byte offset")
        contracts.validate(limit, {"type": "integer", "minimum": 4, "maximum": 65_536}, "History byte limit")
        contracts.validate(revision, {"type": ["null", "string"], "pattern": "^[0-9a-f]{64}$"}, "History revision")
        if offset and revision is None:
            raise ValueError("History pages after offset 0 require the observed revision")
        native_owner = document
        continuation = document.get("continuation", {})
        if continuation.get("kind") == "resume":
            source_id = continuation["source_run"]
            with state.connect() as db:
                row = db.execute("SELECT document FROM agent_runs WHERE project=? AND id=?", (project_id, source_id)).fetchone()
            if row is None:
                raise ValueError("Continuation archive source is missing from this project")
            native_owner = json.loads(row[0])
            if (native_owner["id"] != source_id or native_owner.get("continuation", {}).get("kind") != "source"
                    or native_owner["continuation"].get("native") != continuation["source"]
                    or native_owner["binding"] != document["binding"]):
                raise ValueError("Continuation archive lineage differs from its original source")
            result["continuation"] = {"source_run": source_id, "state": continuation["state"],
                                      "native": continuation.get("native")}
        owner_id = native_owner["id"]
        adapter = agent_backends.for_binding(native_owner["binding"], {})
        result["native_history"] = adapter.archived_history(state.root / "runs" / (owner_id + ".protocol"),
            cwd=state.root / "runs" / (owner_id + ".cwd"), offset=offset, limit=limit, revision=revision)
        if continuation.get("kind") == "resume":
            result["native_history"]["source_run"] = owner_id
    return result


# Ordinary native sessions live in the original run store. Provider state is
# private to one root; immutable input/attempt/final packets are owned here.
class SessionRejected(ValueError):
    """This turn's admission ended before reserving or launching native work."""

    def __init__(self, message, intent_id):
        super().__init__(message)
        self.intent_id = intent_id










def _publish_session_packet(destination, values):
    if any(len(raw) > native_sources.PACKET_BYTES for raw in values.values()):
        raise ValueError(f'Complete encoded session packet exceeds {native_sources.PACKET_BYTES} bytes')
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staged = Path(tempfile.mkdtemp(prefix='.session-', dir=destination.parent))
    try:
        for name, raw in values.items():
            path = staged / name
            with path.open('xb') as stream:
                os.chmod(path, 0o600)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        native_sources.sync_directory_chain(staged)
        publish_directory(staged, destination)
        for name, raw in values.items():
            if native_sources.artifact(destination, name, len(raw), confirm_durable=True) != raw:
                raise ValueError('Session packet changed after durable publication')
    finally:
        if staged.exists():
            shutil.rmtree(staged)










def _session_request(folder, document):
    request = native_sources.packet(folder, 'request.json')
    if (not isinstance(request, dict) or native_sources.sha(request) != document.get('request_sha256')
            or request.get('run_id') != document['id']
            or any(request.get(key) != document.get(key) for key in ('project', 'session', 'submitted'))):
        raise ValueError('Session run differs from its original immutable request')
    return request


def _observe_session_run(state, document, *, full_preview=False):
    return _session_outcome(state, document, full_preview=full_preview)[0]


def _session_outcome(state, document, *, full_preview=False, request=None):
    folder = native_sources.turn_folder(state, document['id'])
    if request is None:
        request = _session_request(folder, document)
    stop_request = None
    if (folder / 'stop').exists():
        stop_request = native_sources.packet(folder / 'stop')
        if (not isinstance(stop_request, dict) or stop_request.get('run_id') != document['id']
                or stop_request.get('project') != document['project']
                or stop_request.get('session') != document['session']['id']
                or stop_request.get('request_sha256') != document['request_sha256']):
            raise ValueError('Saved stop request differs from its original turn')
    if (folder / 'final').exists():
        try:
            final = native_sources.packet(folder / 'final', confirm_durable=True)
        except (OSError, ValueError) as error:
            unavailable = dict(document, status='unknown', execution_stopped=False, stop_request=stop_request,
                               error='Final packet durability is unconfirmed: ' + str(error))
            suggestion = _correction_observation(state, request, unavailable, include_preview=full_preview)
            return {**unavailable, **({'correction_suggestion': suggestion} if suggestion is not None else {})}, False
        if (not isinstance(final, dict) or any(final.get(key) != document[key]
                for key in ('request_sha256', 'id', 'project', 'session', 'submitted'))
                or final.get('status') not in ('succeeded', 'failed', 'cancelled', 'timed_out', 'unknown')
                or not isinstance(final.get('finished'), str) or type(final.get('execution_stopped')) is not bool):
            raise ValueError('Session final differs from the selected request')
        if final.get('status') == 'succeeded':
            raw = native_sources.artifact(state.root / 'runs' / document['id'],
                            'result.json' if request['schema'] is not None else 'result.txt', 8_388_608)
            if hashlib.sha256(raw).hexdigest() != final.get('result_sha256'):
                raise ValueError('Session result differs from its original complete bytes')
        suggestion = _correction_observation(state, request, final, include_preview=full_preview)
        return {**final, 'stop_request': stop_request,
                **({'correction_suggestion': suggestion} if suggestion is not None else {})}, True
    observed = dict(document, status='unknown', execution_stopped=False, stop_request=stop_request)
    try:
        owner = native_sources.packet(folder / 'owner')
        if owner['request_sha256'] == document['request_sha256'] and processes.identity(owner['identity']['pid']) == owner['identity']:
            observed['status'] = 'running'
            observed['owner'] = owner['identity']
    except (FileNotFoundError, ProcessLookupError, KeyError, TypeError, ValueError):
        pass
    suggestion = _correction_observation(state, request, observed, include_preview=full_preview)
    return {**observed, **({'correction_suggestion': suggestion} if suggestion is not None else {})}, False


def _correction_observation(state, request, document, *, include_preview=False):
    """Only project already-issued learning material; reads never complete it."""
    reference = request.get('correction_suggestion')
    if reference is None:
        try:
            policy = _read_session_context(state, document).get('correction_suggestions')
        except (OSError, ValueError, KeyError, TypeError):
            return None
        if policy is None:
            return None
        return {'enabled': policy['enabled'], 'available': False, 'status': 'unavailable', 'preview': None,
                'can_apply': False, 'proposal_id': None,
                'reason': 'Complete correction material could not fit this original turn; manual workflow remains available'}
    base = {**reference, 'preview': None, 'can_apply': False}
    if not reference.get('available') or not reference.get('proposal_id'):
        return {**base, 'status': 'unavailable'}
    if document.get('status') != 'succeeded' or document.get('execution_stopped') is not True:
        return {**base, 'available': False, 'status': 'unknown',
                'reason': 'Observe the original native outcome and cleanup; no learning work is redispatched'}
    try:
        observed = document_corrections.inspect_proposal(state, request['project'], reference['proposal_id'], include_preview=include_preview)
        return {**base, **observed,
                'available': observed['status'] not in ('unavailable', 'unknown', 'prepared')}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {**base, 'available': False, 'status': 'unavailable', 'reason': str(error)}


def _correction_policy(project, binding, template):
    enabled = project.get('correction_suggestions_enabled', True) is True
    policy = {'enabled': enabled, 'available': enabled, 'reason': None, 'target': 'AGENTS.md'}
    if not enabled:
        policy.update(available=False, reason='Default project correction suggestions are disabled')
    elif template is not None:
        policy.update(available=False, reason='Structured template results retain their original contract; use the manual document workflow')
    else:
        try:
            components.validate_agent_minimum(binding, {'model': 'gpt-6.1-sol', 'reasoning_effort': 'high'})
        except ValueError as error:
            policy.update(available=False, reason='Document-proposal model minimum is unavailable: ' + str(error))
    return policy


def _read_session_context(state, root):
    folder = native_sources.session_folder(state, root['session']['id']) / 'context'
    if inventory_tree(folder)[0] != root['context_digest']:
        raise ValueError('Frozen session context or resources changed')
    return native_sources.packet(folder, 'context.json')


def _validate_session_authority(state, context):
    project = state.project(context['project'])
    repo = Path(project['repo'])
    details = repo.stat(follow_symlinks=False)
    if (project['revision'] != context['project_revision'] or project['repo'] != context['repo']
            or is_link(repo) or [details.st_dev, details.st_ino] != context['repo_identity']):
        raise ValueError('Project revision or repository identity changed; start a new session')
    requested = projects.effective_configuration(project)['layers'][context['role']]['binding']
    if requested != context['requested_binding']:
        raise ValueError('Current role binding differs from the frozen session')
    agents.validate_binding(context['role'], context['binding'])
    components.validate_agent_minimum(context['binding'], context.get('invocation_minimum'))
    agent_backends.for_binding(context['binding']).validate_session_configuration(context['inference'], repo)
    home = Path(context['native_home'])
    details = home.stat(follow_symlinks=False)
    if is_link(home) or [details.st_dev, details.st_ino] != context['native_home_identity']:
        raise ValueError('Native session home identity changed')


def _session_turns(state, project, ident):
    native_sources.session_id(ident)
    with state.connect() as db:
        rows = db.execute("SELECT document FROM agent_runs WHERE project=? AND json_extract(document,'$.session.id')=? ORDER BY rowid LIMIT ?",
                          (project, ident, _MAX_SESSION_TURNS + 1)).fetchall()
    if not rows or len(rows) > _MAX_SESSION_TURNS:
        raise ValueError(f'Unknown session or session exceeds the {_MAX_SESSION_TURNS}-turn observation limit')
    turns = [_observe_session_run(state, parse_json(row[0], 'Session run', finite=True, bounded=True)) for row in rows]
    previous = None
    for ordinal, turn in enumerate(turns):
        if (turn['session'] != {'id': ident, 'parent_run': previous, 'ordinal': ordinal}
                or turn['project'] != project):
            raise ValueError('Session records do not form one complete parent chain')
        previous = turn['id']
    return turns


def _session_summary(state, project, ident, turns):
    root, latest = turns[0], turns[-1]
    context = _read_session_context(state, root)
    reason = None
    if latest.get('status') in ('unknown', 'reserved', 'running'):
        reason = latest.get('error') or 'The original turn has no confirmed final outcome; observe its saved intent'
    elif latest.get('execution_stopped') is not True:
        reason = 'The latest turn has no confirmed process cleanup; observe the original operation'
    elif not latest.get('native_session', {}).get('id'):
        reason = 'The stopped turn has no saved native session UUID; start a new session explicitly'
    elif len(turns) >= _MAX_SESSION_TURNS:
        reason = f'This session reached its {_MAX_SESSION_TURNS}-turn limit; start a new session explicitly'
    else:
        try:
            _validate_session_authority(state, context)
        except (OSError, ValueError) as error:
            reason = str(error)
    return {'id': ident, 'birth_intent': root['submitted']['intent_id'], 'project': project, 'repo': context['repo'], 'role': context['role'],
            'binding': context['binding'], 'mode': 'native', 'sandbox': context['sandbox'],
            'latest_run': latest['id'], 'status': latest['status'], 'can_continue': reason is None, 'reason': reason}


def sessions(state: State, project_id: str, *, after: int = 0, limit: int = 20, intent_id: str | None = None) -> dict:
    state.project(project_id)
    contracts.validate(after, {'type': 'integer', 'minimum': 0}, 'Session offset')
    contracts.validate(limit, {'type': 'integer', 'minimum': 1, 'maximum': 100}, 'Session limit')
    predicate, parameters = '', [project_id]
    if intent_id is not None:
        native_sources.session_id(intent_id, 'Birth intent')
        predicate = " AND json_extract(document,'$.submitted.intent_id')=?"
        parameters.append(intent_id)
    with state.connect() as db:
        rows = db.execute("SELECT id FROM agent_runs WHERE project=? AND json_extract(document,'$.session.id')=id" +
                          predicate + " ORDER BY rowid DESC LIMIT ? OFFSET ?", (*parameters, limit + 1, after)).fetchall()
    return {'sessions': [_session_summary(state, project_id, row[0], _session_turns(state, project_id, row[0])) for row in rows[:limit]],
            'next_after': after + limit if len(rows) > limit else None}


def inspect_session(state: State, project_id: str, session_id: str, *, after: int = 0, limit: int = 20) -> dict:
    contracts.validate(after, {'type': 'integer', 'minimum': 0}, 'Turn offset')
    contracts.validate(limit, {'type': 'integer', 'minimum': 1, 'maximum': 100}, 'Turn limit')
    turns = _session_turns(state, project_id, session_id)
    return {**_session_summary(state, project_id, session_id, turns), 'turns': turns[after:after + limit],
            'next_after': after + limit if len(turns) > after + limit else None}


def _session_prompt(prompt, timeout):
    contracts.validate(prompt, {'type': 'string', 'pattern': r'\S', 'maxLength': 1_000_000}, 'Session prompt')
    if '\0' in prompt or len(prompt.encode('utf-8')) > 1_000_000:
        raise ValueError('Session prompt requires UTF-8 text without NUL, at most 1 MB')
    contracts.validate(timeout, {'type': 'integer', 'minimum': 1, 'maximum': 3600}, 'Turn timeout')


def _start_session(state, project_id, role, prompt, timeout, skill_names, recall, template,
                   intent, revision, codex_config):
    try:
        native_sources.session_id(intent, 'Session intent')
        _session_prompt(prompt, timeout)
        if sys.platform != 'linux':
            raise ValueError('Persistent native sessions require Linux/WSL2')
    except ValueError as error:
        raise SessionRejected(str(error), intent) from error
    ident = uuid.uuid5(uuid.NAMESPACE_URL, 'ergora:native-session:' + project_id + ':' + intent).hex
    submitted = {'role': role, 'prompt': prompt, 'timeout': timeout, 'skills': skill_names or [], 'recall': recall,
                 'template': template, 'expected_revision': revision,
                 'codex_config': str(codex_config) if codex_config is not None else None, 'intent_id': intent}
    existing = native_sources.find_run(state, project_id, ident)
    if existing is not None:
        if existing['submitted'] != submitted:
            raise ValueError('Session intent was already consumed by a different request')
        return _observe_session_run(state, existing)
    state.root.joinpath('runs').mkdir(exist_ok=True, mode=0o700)
    with file_lock(state.root / 'runs' / (ident + '.session.lock'), blocking=False) as lock:
        if native_sources.find_run(state, project_id, ident) is not None:
            return _start_session(state, project_id, role, prompt, timeout, skill_names, recall, template, intent, revision, codex_config)
        project = state.project(project_id)
        if revision != project['revision']:
            raise SessionRejected('Session start requires the current project revision', intent)
        clock = budget_clock.authorize(timeout)
        folder = native_sources.session_folder(state, ident)
        folder.mkdir(mode=0o700)
        home = folder / 'native-home'
        home.mkdir(mode=0o700)
        staged = Path(tempfile.mkdtemp(prefix='.context-', dir=folder))
        try:
            full_prompt, schema, context, _ = _prepare_role(state, project_id, role, prompt, timeout, skill_names, recall, template,
                                                          freeze=(staged, folder / 'context'))
            if context['project_revision'] != revision or state.project(project_id)['revision'] != revision:
                raise ValueError('Project changed during session preparation; no native effect was started')
            adapter = agent_backends.for_binding(context['binding'], {'codex': {'config': codex_config, 'role': role}})
            inference = adapter.session_configuration(Path(project['repo']))
            requested = context['binding']
            context.update(binding=inference['binding'], requested_binding=requested, inference=inference,
                           repo=project['repo'], repo_identity=native_sources.directory_identity(Path(project['repo'])),
                           native_home=str(home), native_home_identity=native_sources.directory_identity(home), grant=None,
                           sandbox=inference['sandbox'])
            policy = _correction_policy(project, inference['binding'], template)
            if policy is not None:
                context['correction_suggestions'] = policy
            context_file = staged / 'context.json'
            try:
                context_file.write_bytes(native_sources.encode(context))
                inventory_tree(staged)
            except ValueError:
                if 'correction_suggestions' not in context:
                    raise
                # Optional policy must not reduce the original native material
                # range. Absence is observed as unavailable, never backfilled.
                context.pop('correction_suggestions')
                context_file.write_bytes(native_sources.encode(context))
                inventory_tree(staged)
            # Verify the whole frozen package before publishing any context.
            digest = inventory_tree(staged)[0]
            for path in staged.rglob('*'):
                if path.is_file():
                    with path.open('rb') as stream:
                        os.fsync(stream.fileno())
            for path in sorted((p for p in staged.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                native_sources.sync_directory_chain(path)
            native_sources.sync_directory_chain(staged)
            publish_directory(staged, folder / 'context')
            native_sources.sync_directory_chain(folder / 'context')
            if inventory_tree(folder / 'context')[0] != digest:
                raise ValueError('Session context changed during publication')
        except (OSError, ValueError) as error:
            raise SessionRejected(str(error), intent) from error
        finally:
            if staged.exists():
                shutil.rmtree(staged)
        # No admission-rejected classification is allowed beyond this point:
        # reservation/attempt failures and lost replies observe the original slot.
        return _reserve_session_turn(state, project_id, ident, None, ident, 0, prompt, timeout, clock,
                                     context, digest, submitted, lock)




def _continuation_run_id(session_id: str, intent_id: str) -> str:
    native_sources.session_id(session_id)
    native_sources.session_id(intent_id, 'Turn intent')
    return uuid.uuid5(uuid.NAMESPACE_URL, 'ergora:native-turn:' + session_id + ':' + intent_id).hex


def prepare_campaign_recipient(state: State, project_id: str, revision: int, declaration: dict) -> dict:
    """Freeze the exact existing native Codex session and Linux executable before Campaign start."""
    session, parent = declaration['session_id'], declaration['parent_run_id']
    _session_prompt(declaration['prompt'], declaration['timeout_seconds'])
    turns = _session_turns(state, project_id, session)
    latest = turns[-1]
    native_id = latest.get('native_session', {}).get('id')
    if (latest['id'] != parent or latest.get('execution_stopped') is not True or not native_id
            or latest.get('status') in ('unknown', 'reserved', 'running')):
        raise ValueError('Campaign recipient must select the original latest stopped native turn')
    context = _read_session_context(state, turns[0])
    if context['project_revision'] != revision or context['binding']['tool'] != 'codex':
        raise ValueError('Campaign requires a persistent Codex recipient from the approved project revision')
    _validate_session_authority(state, context)
    if (continuation_receipt(state, project_id, session, parent, declaration['intent_id'])['dispatch'] != 'unrecorded'):
        raise ValueError('Campaign recipient intent already has original native dispatch evidence')
    inference = context['inference']
    candidates = []
    for path, expected in inference['executable_files'].items():
        with open(path, 'rb') as stream:
            if stream.read(4) == b'\x7fELF':
                stream.seek(0)
                details = os.fstat(stream.fileno())
                if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
                    raise ValueError('Selected native Codex executable changed while freezing Campaign authority')
                candidates.append((path, expected, details))
    if len(candidates) != 1:
        raise ValueError('Campaign recipient requires one frozen installed Codex ELF and protected Linux descriptor exec')
    require_payload_support()
    path, digest, details = candidates[0]
    return {'context_digest': turns[0]['context_digest'], 'role': context['role'], 'native_id': native_id,
            'source_executable': inference['executable'], 'payload_executable': path, 'payload_sha256': digest,
            'device': details.st_dev, 'inode': details.st_ino, 'size': details.st_size}


def _dispatch_packet(folder: Path, name: str, request_digest: str) -> dict | None:
    path = folder / name
    try:
        packet = native_sources.packet(path, confirm_durable=name == 'native-start')
    except FileNotFoundError as error:
        if error.filename == str(path):
            return None
        raise ValueError(f'Continuation {name} receipt is incomplete') from error
    if not isinstance(packet, dict) or packet.get('request_sha256') != request_digest:
        raise ValueError(f'Continuation {name} differs from its original request')
    return packet


def _process_identity(value) -> bool:
    if (not isinstance(value, dict) or value.keys() != {'pid', 'start_ticks', 'boot_id'}
            or type(value['pid']) is not int or value['pid'] <= 0):
        return False
    ticks, boot_id = value.get('start_ticks'), value.get('boot_id')
    return (isinstance(ticks, str) and len(ticks) <= 20 and ticks.isascii() and ticks.isdecimal()
            and isinstance(boot_id, str) and len(boot_id) == 36)


def _matches_continuation(record, receipt):
    session, submitted = record.get('session'), record.get('submitted')
    return (isinstance(session, dict) and isinstance(submitted, dict)
            and session.get('id') == receipt['session_id']
            and session.get('parent_run') == submitted.get('parent_run') == receipt['parent_run_id']
            and submitted.get('intent_id') == receipt['intent_id'])


def _continuation_without_reservation(state, project_id, folder, receipt):
    session_id = receipt['session_id']
    root = native_sources.find_run(state, project_id, session_id)
    if (root is None or root.get('kind') != 'native-agent-run'
            or root.get('session') != {'id': session_id, 'parent_run': None, 'ordinal': 0}):
        return receipt
    reason = 'Original continuation request evidence is incomplete'
    try:
        request = native_sources.packet(folder, 'request.json')
    except FileNotFoundError as error:
        if error.filename == str(folder):
            return receipt
    except (OSError, ValueError):
        pass
    else:
        if (not isinstance(request, dict) or request.get('project') != project_id
                or request.get('run_id') != receipt['run_id'] or not _matches_continuation(request, receipt)):
            raise ValueError('Continuation request differs from the selected project, session, parent or intent')
        reason = 'Original continuation request has no verified reservation'
    return dict(receipt, dispatch='incomplete', dispatch_error=reason)


def continuation_receipt(state: State, project_id: str, session_id: str, parent_run_id: str, intent_id: str) -> dict:
    """Observe one continuation and its existing dispatch evidence without sending it."""
    ident = _continuation_run_id(session_id, intent_id)
    native_sources.session_id(parent_run_id, 'Parent run')
    state.project(project_id)
    receipt = {'session_id': session_id, 'parent_run_id': parent_run_id, 'intent_id': intent_id,
               'run_id': ident, 'dispatch': 'unrecorded', 'native_start': {'status': 'unrecorded'}, 'run': None}
    folder = native_sources.turn_folder(state, ident)
    saved = native_sources.find_run(state, project_id, ident)
    if saved is None:
        return _continuation_without_reservation(state, project_id, folder, receipt)
    if saved.get('kind') != 'native-agent-run' or not _matches_continuation(saved, receipt):
        raise ValueError('Continuation receipt differs from the selected session, parent or intent')
    request = _session_request(folder, saved)
    try:
        run, final_verified = _session_outcome(state, saved, request=request)
    except (OSError, ValueError) as error:
        run = dict(saved, status='unknown', execution_stopped=False, error='Original outcome unavailable: ' + str(error))
        final_verified = False
    receipt['run'] = run
    # Start, owner and attempt receipts are read in reverse publication order.
    # A racing publication cannot appear to have skipped its predecessor.
    start = None
    try:
        start = _dispatch_packet(folder, 'native-start', saved['request_sha256'])
    except (OSError, ValueError) as error:
        receipt['native_start'] = {'status': 'incomplete', 'error': str(error)}
    evidence = set()
    owner = None
    try:
        for name in ('owner', 'attempt'):
            packet = _dispatch_packet(folder, name, saved['request_sha256'])
            if packet is None:
                continue
            if name == 'owner':
                owner = packet.get('identity')
                if not _process_identity(owner):
                    raise ValueError('Continuation owner receipt lacks its process identity')
            evidence.add(name)
        if 'attempt' not in evidence and ('owner' in evidence or final_verified or saved.get('finished') is not None):
            raise ValueError('Continuation has later evidence but no original attempt')
        # The caller can record a failed supervisor launch before any owner
        # starts. Other finals and a failed native invocation require an owner.
        if ('owner' not in evidence and final_verified
                and (run['status'] != 'failed' or 'output' in run or 'returncode' in run)):
            raise ValueError('Continuation outcome has no original owner receipt')
    except (OSError, ValueError) as error:
        receipt.update(dispatch='incomplete', dispatch_error=str(error))
    else:
        receipt['dispatch'] = 'accepted' if 'owner' in evidence else 'attempted' if evidence else 'reserved'
    if start is not None:
        process = start.get('process')
        binding = {key: start.get(key) for key in ('request_sha256', 'owner', 'process')}
        if (evidence != {'attempt', 'owner'} or start.get('owner') != owner or not _process_identity(process)
                or process['pid'] == owner['pid'] or process['boot_id'] != owner['boot_id']
                or int(process['start_ticks']) < int(owner['start_ticks'])
                or start.get('receipt_sha256') != native_sources.sha(binding)):
            receipt['native_start'] = {'status': 'incomplete', 'error': 'Native start differs from its original attempt or owner'}
        else:
            try:
                active = processes.identity(process['pid']) == process
            except (OSError, ValueError):
                active = False
            if active and final_verified and run['execution_stopped']:
                receipt['native_start'] = {'status': 'incomplete', 'error': 'Live child differs from the original stopped outcome'}
            else:
                receipt['native_start'] = {'status': 'running' if active else 'started', 'process': process}
    elif receipt['native_start']['status'] == 'unrecorded' and run.get('native_start_error'):
        receipt['native_start'] = {'status': 'incomplete', 'error': run['native_start_error']}
    return receipt


class _SessionSlotTimeout(TimeoutError):
    """The selected continuation expired before admission."""


def continue_session(state: State, project_id: str, session_id: str, parent_run_id: str, prompt: str, *,
                     expected_revision: int, intent_id: str, timeout: int = 300, wait_for_slot: bool = False,
                     campaign_recipient: dict | None = None) -> dict:
    ident = _continuation_run_id(session_id, intent_id)
    native_sources.session_id(parent_run_id, 'Parent run')
    _session_prompt(prompt, timeout)
    submitted = {'parent_run': parent_run_id, 'prompt': prompt, 'expected_revision': expected_revision,
                 'timeout': timeout, 'intent_id': intent_id}
    if campaign_recipient is not None:
        submitted['campaign_recipient'] = campaign_recipient

    def observe_existing():
        existing = native_sources.find_run(state, project_id, ident)
        if existing is not None:
            if existing['submitted'] != submitted or existing['session']['id'] != session_id:
                raise ValueError('Turn intent was already consumed by a different request')
            return _observe_session_run(state, existing)

    observed = observe_existing()
    if observed is not None:
        return observed
    gate = RecipientGate.load(state.root, project_id, campaign_recipient) if campaign_recipient is not None else None
    clock = None
    if wait_for_slot:
        clock = budget_clock.authorize(timeout)
        parent = native_sources.find_run(state, project_id, parent_run_id)
        if parent is None or parent.get('session', {}).get('id') != session_id:
            raise ValueError('Wait requires a recorded parent from the selected session')
        if expected_revision != parent['project_revision']:
            raise ValueError('Turn revision differs from its original session')

    lock_path = state.root / 'runs' / (session_id + '.session.lock')
    with ExitStack() as resources:
        while True:
            if gate is not None:
                gate.require_open()
            try:
                lock = resources.enter_context(file_lock(lock_path, blocking=False))
            except BlockingIOError:
                if clock is None:
                    raise
                remaining = budget_clock.remaining(clock, timeout)
                if gate is not None:
                    remaining = min(remaining, gate.remaining())
                if remaining <= 0:
                    raise _SessionSlotTimeout('Timed out waiting for the original session slot') from None
                time.sleep(min(.1, remaining))
            else:
                break

        observed = observe_existing()
        if observed is not None:
            return observed
        turns = _session_turns(state, project_id, session_id)
        if len(turns) >= _MAX_SESSION_TURNS:
            raise ValueError(f'This session reached its {_MAX_SESSION_TURNS}-turn limit; no new turn was reserved')
        latest = turns[-1]
        context = _read_session_context(state, turns[0])
        if expected_revision != context['project_revision']:
            raise ValueError('Turn revision differs from its original session')
        _validate_session_authority(state, context)
        try:
            native_sources.turn_folder(state, ident).lstat()
        except FileNotFoundError:
            pass
        else:
            raise ValueError('Original continuation evidence has no verified reservation; read its continuation receipt')
        if gate is not None and latest['id'] != parent_run_id:
            raise RecipientBlocked('stale_parent')
        if (latest['id'] != parent_run_id or latest.get('status') in ('unknown', 'reserved', 'running')
                or latest.get('execution_stopped') is not True
                or not latest.get('native_session', {}).get('id')):
            raise ValueError('Select the latest stopped turn with its saved native UUID; consumed or unknown parents cannot be dispatched')
        if gate is not None:
            gate.require_turn(state, ident, session_id, turns[0]['context_digest'], context['role'],
                              latest['native_session']['id'], submitted)
        return _reserve_session_turn(state, project_id, session_id, latest, ident, len(turns), prompt, timeout,
                                     clock or budget_clock.authorize(timeout), context, turns[0]['context_digest'],
                                     submitted, lock, check_admission_deadline=wait_for_slot, gate=gate)


def _reserve_session_turn(state, project, root, parent, ident, ordinal, prompt, timeout, clock, context, digest,
                          submitted, lock, *, check_admission_deadline=False, gate=None):
    _validate_session_authority(state, context)
    full_prompt = prompt + context['suffix']
    if len(full_prompt.encode('utf-8')) > 10_000_000:
        raise ValueError('Complete session prompt exceeds 10 MB; it was not truncated')
    session = {'id': root, 'parent_run': parent['id'] if parent else None, 'ordinal': ordinal}
    original_prompt = full_prompt
    policy = context.get('correction_suggestions')
    if gate is not None and policy is not None:
        policy = {**policy, 'available': False, 'reason': 'Campaign authorizes only the frozen native continuation'}
    correction = None
    task = None
    admitted = False

    def admit():
        nonlocal admitted
        # A correction's frozen source can be the first durable write for this intent.
        if check_admission_deadline and not admitted and budget_clock.remaining(clock, timeout) <= 0:
            raise _SessionSlotTimeout('Timed out waiting for the original session slot')
        admitted = True

    if policy is not None:
        correction = {**policy, 'proposal_id': None}
        if policy['available']:
            try:
                task = document_corrections.prepare_native(state, project, ident, session, submitted,
                    context['project_revision'], clock, path=policy['target'],
                    before_publish=admit if check_admission_deadline else None)
                proposed_prompt = full_prompt + '\n\n' + document_corrections.native_prompt(task)
                if len(proposed_prompt.encode('utf-8')) > 10_000_000:
                    raise ValueError('Complete suggestion material cannot fit the original native prompt allowance')
                full_prompt = proposed_prompt
                correction.update(proposal_id=task['proposal_id'], request_sha256=task['request_sha256'])
            except (_SessionSlotTimeout, document_corrections.NativePreparationConflict):
                raise
            except (OSError, ValueError, KeyError, TypeError) as error:
                correction.update(available=False, reason=str(error))
                task = None
    request = {'run_id': ident, 'project': project, 'session': session, 'submitted': submitted,
               'context_digest': digest, 'prompt': full_prompt, 'schema': context['schema'],
               'clock': clock, 'timeout': timeout, 'native_id': parent['native_session']['id'] if parent else None}
    if correction is not None:
        request['correction_suggestion'] = correction
    try:
        try:
            encoded_request = native_sources.encode(request)
        except ValueError:
            if correction is None:
                raise
            request.pop('correction_suggestion')
            request['prompt'] = full_prompt = original_prompt
            task = None
            encoded_request = native_sources.encode(request)
    except ValueError as error:
        raise SessionRejected(str(error), submitted['intent_id']) from error
    folder = native_sources.turn_folder(state, ident)
    with (gate.admission(native_clock=clock, native_timeout=timeout) if gate is not None else nullcontext()):
        admit()
        _publish_session_packet(folder, {'request.json': encoded_request})
        document = {'id': ident, 'project': project, 'kind': 'native-agent-run', 'role': context['role'],
                    'binding': context['binding'], 'project_revision': context['project_revision'],
                    'template': context['template'], 'session': session, 'submitted': submitted,
                    'context_digest': digest, 'request_sha256': hashlib.sha256(encoded_request).hexdigest(),
                    'prompt_sha256': hashlib.sha256(full_prompt.encode()).hexdigest(),
                    'started': now(), 'status': 'reserved', 'formal_execution_authorized': False}
        _store(state, document)
    if task is not None:
        document_corrections.bind_native(state, project, task['proposal_id'], ident)
    if budget_clock.remaining(clock, timeout) <= 0:
        return _observe_session_run(state, document)
    _publish_session_packet(folder / 'attempt', {'record.json': native_sources.encode({'request_sha256': document['request_sha256']})})
    environment = dict(os.environ)
    source = str(IMPORT_ROOT)
    environment['PYTHONPATH'] = source + (os.pathsep + environment['PYTHONPATH'] if environment.get('PYTHONPATH') else '')
    argv = [sys.executable, '-c', 'from ergora.agents.runs import session_main; session_main()',
            str(state.root), ident, str(lock.fileno())]
    try:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 env=environment, pass_fds=(lock.fileno(),), start_new_session=True)
    except OSError as error:
        failed = dict(document, status='failed', error=str(error), execution_stopped=True, finished=now())
        _publish_session_packet(folder / 'final', {'record.json': native_sources.encode(failed)})
        _store(state, failed)
        return failed
    notified = False
    while True:
        try:
            child.wait(timeout=.2)
            break
        except subprocess.TimeoutExpired:
            if not notified and budget_clock.remaining(clock, timeout) <= 0:
                try:
                    processes.notify_identity(processes.identity(child.pid), signal.SIGTERM)
                    notified = True
                except (OSError, ValueError):
                    pass
        except KeyboardInterrupt:
            stop_session(state, project, root, ident, intent_id='caller-interrupted')
    return _observe_session_run(state, document, full_preview=True)


def stop_session(state: State, project_id: str, session_id: str, run_id: str, *, intent_id: str) -> dict:
    native_sources.session_id(intent_id, 'Stop intent')
    document = native_sources.record(state, project_id, native_sources.session_id(run_id))
    if document.get('session', {}).get('id') != native_sources.session_id(session_id):
        raise ValueError('Stop must select this project and session turn')
    folder = native_sources.turn_folder(state, run_id)
    stop = {'project': project_id, 'session': session_id, 'run_id': run_id,
            'request_sha256': document['request_sha256'], 'intent_id': intent_id}
    recipient = document['submitted'].get('campaign_recipient')
    with (file_lock(CampaignFiles(state.root, project_id, recipient['campaign']).lock, blocking=False)
          if recipient is not None else nullcontext()):
        if (folder / 'stop').exists():
            if native_sources.packet(folder / 'stop') != stop:
                raise ValueError('The original stop request is already recorded')
            native_sources.sync_directory_chain(folder / 'stop')
        else:
            _publish_session_packet(folder / 'stop', {'record.json': native_sources.encode(stop)})
    notification = 'unconfirmed'
    try:
        owner = native_sources.packet(folder / 'owner')
        if owner['request_sha256'] != document['request_sha256']:
            raise ValueError('Turn owner differs from the stopped request')
        processes.notify_identity(owner['identity'], signal.SIGTERM)
        notification = 'sent'
    except (OSError, ValueError) as error:
        notification = str(error)
    return {'run_id': run_id, 'stop_requested': True, 'notification': notification,
            'run': _observe_session_run(state, document)}


def session_main():
    """One explicit ordinary turn. Only this process owns native descendants."""
    home, ident, inherited = sys.argv[1:]
    state = State(Path(home))
    fd = int(inherited)
    document = native_sources.find_run(state, native_sources.packet(native_sources.turn_folder(state, ident), 'request.json')['project'], ident)
    if document is None:
        raise ValueError('Session turn has no original reservation')
    root = document['session']['id']
    lock_path = state.root / 'runs' / (root + '.session.lock')
    if (os.fstat(fd).st_dev, os.fstat(fd).st_ino) != (lock_path.stat().st_dev, lock_path.stat().st_ino):
        raise ValueError('Session turn lacks its original inherited lifecycle lock')
    import fcntl
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    folder = native_sources.turn_folder(state, ident)
    request = native_sources.packet(folder, 'request.json')
    if (native_sources.sha(request) != document['request_sha256']
            or native_sources.packet(folder / 'attempt')['request_sha256'] != document['request_sha256']):
        raise ValueError('Session effect differs from its consumed attempt')
    owner = processes.identity(os.getpid())
    _publish_session_packet(folder / 'owner', {'record.json': native_sources.encode({
        'identity': owner, 'request_sha256': document['request_sha256']})})
    stopping = False
    expired = False
    gate = None
    campaign_blocker = None
    observed_stop = False
    start_writer = None
    start_error = None

    def cancel(_signum, _frame):
        nonlocal stopping
        stopping = True
        processes.cancel_supervised()

    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)

    def should_stop():
        nonlocal expired
        nonlocal campaign_blocker
        nonlocal observed_stop
        if gate is not None:
            if observed_stop:
                return True
            if (folder / 'stop').exists():
                observed_stop = True
                return True
            try:
                campaign_blocker = gate.blocker()
            except (OSError, ValueError):
                campaign_blocker = 'authority_unavailable'
            if campaign_blocker is not None:
                observed_stop = True
                return True
        try:
            expired = budget_clock.remaining(request['clock'], request['timeout']) <= 0
        except ValueError:
            expired = True
        requested = stopping or expired or (folder / 'stop').exists()
        if gate is not None:
            observed_stop = requested
        return requested

    def publish_native_start(process):
        nonlocal start_writer, start_error
        binding = {'request_sha256': document['request_sha256'], 'owner': owner, 'process': process}

        def persist():
            nonlocal start_error
            try:
                _publish_session_packet(folder / 'native-start', {'record.json': native_sources.encode({
                    **binding, 'receipt_sha256': native_sources.sha(binding)})})
            except (OSError, ValueError) as error:
                start_error = str(error)

        # The sole native reaper must keep polling even while storage stalls.
        try:
            start_writer = Thread(target=persist, daemon=True)
            start_writer.start()
        except RuntimeError as error:
            start_writer = None
            start_error = str(error)

    invocation_entered = False
    document['execution_stopped'] = False
    try:
        context = _read_session_context(state, document)
        _validate_session_authority(state, context)
        recipient = request['submitted'].get('campaign_recipient')
        if recipient is not None:
            gate = RecipientGate.load(state.root, document['project'], recipient)
            gate.require_turn(state, ident, root, request['context_digest'], document['role'],
                              request['native_id'], request['submitted'])
        if should_stop():
            document.update(status='cancelled', error='Turn stopped or expired before native effect')
        else:
            environment = dict(os.environ, CODEX_HOME=context['native_home'])
            native = {'configuration': context['inference'], 'native_id': request['native_id']}
            remaining = budget_clock.remaining(request['clock'], request['timeout'])
            if gate is not None:
                remaining = min(remaining, gate.remaining())
            invocation_entered = True
            document.update(agents.invoke(context['binding'], context['role'], request['prompt'], Path(context['repo']),
                state.root / 'runs' / ident, max(.01, remaining),
                request['schema'], env=environment, supervised=True, lock_fd=fd, session=native, stop_requested=should_stop,
                **({'launch_prefix': gate.command_prefix(ident, fd), 'payload_executable': gate.payload_identity(),
                    'record_lifecycle': True} if gate is not None else {}),
                on_start=publish_native_start if request['session']['parent_run'] is not None else None))
        if expired or campaign_blocker == 'expired':
            document['status'] = 'timed_out'
        document['execution_stopped'] = True
    except RecipientBlocked as error:
        outcome = 'timed_out' if str(error) in ('expired', 'native_turn_expired') else 'cancelled'
        document.update(status=outcome, error=str(error), execution_stopped=True)
    except (OSError, ValueError, TypeError, KeyError) as error:
        document.update(status='unknown' if invocation_entered else 'failed', error=str(error),
                        execution_stopped=not invocation_entered)
    if start_writer is not None:
        while start_writer.is_alive() and not should_stop():
            start_writer.join(timeout=.2)
        if start_writer.is_alive():
            start_error = 'Original native start receipt publication remained pending at stop or deadline'
    if start_error is None and document.get('payload_exec', {}).get('status') == 'unverified':
        start_error = 'Selected native payload exec was not verified'
    if campaign_blocker is not None:
        document['campaign_recipient_blocker'] = campaign_blocker
    if start_error is not None:
        document['native_start_error'] = start_error
    if document['execution_stopped']:
        try:
            # The native owner has returned from its only reaper. Persist only our
            # own closed artifacts; this is not a claim about provider-internal DBs.
            for output in (state.root / 'runs' / ident, state.root / 'runs' / (ident + '.protocol')):
                if not output.exists():
                    continue
                for path in output.iterdir():
                    if is_link(path) or not path.is_file():
                        raise ValueError('Native output archive contains a non-ordinary file')
                    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                    try:
                        native_sources.sync_descriptor(descriptor)
                    finally:
                        os.close(descriptor)
                native_sources.sync_directory_chain(output)
            if document.get('result_sha256') is not None:
                name = 'result.json' if request['schema'] is not None else 'result.txt'
                if hashlib.sha256(native_sources.artifact(state.root / 'runs' / ident, name, 8_388_608)).hexdigest() != document['result_sha256']:
                    raise ValueError('Durable result readback differs from the original result')
        except (OSError, ValueError) as error:
            document.update(status='unknown', error='Native artifacts lack durable confirmation: ' + str(error))
    document['finished'] = now()
    _publish_session_packet(folder / 'final', {'record.json': native_sources.encode(document)})
    _store(state, document)
    correction = request.get('correction_suggestion', {})
    if (correction.get('available') and correction.get('proposal_id')
            and document['status'] == 'succeeded' and document['execution_stopped'] is True):
        try:
            document_corrections.complete_native(state, document['project'], correction['proposal_id'], ident,
                remaining=lambda: -1 if should_stop() else budget_clock.remaining(request['clock'], request['timeout']))
        except (OSError, ValueError, KeyError, TypeError):
            # Original native final/result remain authoritative. A missing
            # learning completion is only observed as unavailable/unknown.
            pass
