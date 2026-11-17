"""Independent Agent invocations, frozen context and durable run records."""

import asyncio
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
import shutil
import stat
import time
import uuid

from . import agent_backends, agent_definitions, agents, budget_clock, components, contracts, processes, projects, task_mcp, workflow_definitions
from .asset_trees import inventory_tree, is_link, publish_directory
from .bindings import validate_binding
from .definition_bundles import parse_json
from .state import State, file_lock, now


_MAX_SESSION_TURNS = 10_000


def _store(state: State, document: dict) -> None:
    with state.connect() as db:
        db.execute("INSERT INTO agent_runs VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET document=excluded.document",
                   (document["id"], document["project"], json.dumps(document)))


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
        from . import skill_assets

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
        from . import memory

        recalled = memory.search(state, project_id, recall, limit=5, project=project)
        context["memories"] = recalled["results"]
        prompt += "\n\nProject observations with provenance (verify their applicability):\n" + json.dumps(recalled, ensure_ascii=False)
    binding = configuration["layers"][role]["binding"]
    validate_binding(role, binding)
    schema = None
    if template:
        from . import reference
        contract = reference.agent_contract(template)
        if role not in contract["agents"]:
            raise ValueError("This template does not use the selected agent role")
        schema = agents.result_schema(contract["agents"][role]["artifacts"], role == "reviewer")
        prompt += "\n\nTemplate role requirements (return exactly one matching JSON object):\n" + json.dumps(
            {"requirements": contract["agents"][role], "result_schema": schema}, ensure_ascii=False)
    return prompt, schema, {'project': project_id, 'role': role, 'binding': binding,
        'project_revision': project['revision'], 'context': context, 'template': template,
        'suffix': prompt[len(task):], 'schema': schema}


def run_agent(state: State, project_id: str, role: str, prompt: str, timeout: int = 300,
              skill_names: list[str] | None = None, recall: str | None = None,
              template: str | None = None, *, session_intent: str | None = None,
              expected_revision: int | None = None, codex_config: Path | None = None) -> dict:
    if session_intent is not None:
        return _start_session(state, project_id, role, prompt, timeout, skill_names, recall, template,
                              session_intent, expected_revision, codex_config)
    prepared, schema, document = _prepare_role(state, project_id, role, prompt, timeout, skill_names, recall, template)
    document.pop('suffix')
    document.pop('schema')
    run_id = uuid.uuid4().hex
    document.update(id=run_id, started=now(), status='running',
                    configuration=projects.effective_configuration(state.project(project_id)),
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
                 binding_override: dict | None = None, input_digest: str | None = None) -> tuple[dict, dict]:
    """One current admission produces both the preview and the persisted call contract."""
    contracts.validate(mode, {"enum": ["text-only", "task-mcp"]}, "Composition call mode")
    prepared = workflow_definitions.inspect_input(source, material=True)
    if input_digest is not None and prepared['digest'] != input_digest:
        raise ValueError('Composition input differs from the explicitly selected digest')
    leaf = next(item for item in prepared["composition"]["instances"] if item["path"] == prepared["request"]["instance"])
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
    agents.validate_binding(leaf["role"], binding, formal=True)
    components.validate_agent_minimum(binding, definition["definition"].get("invocation_minimum"))
    adapter = agent_backends.for_binding(binding, {"codex": {"config": codex_config}})
    adapter.check_invocation()
    adapter.check_mode(mode)
    policy = adapter.composition_policy(mode)
    if mode in ("task-mcp", "workspace-task-mcp"):
        task_mcp.check_available()
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
              input_digest: str | None = None) -> dict:
    """Explicit independent restricted call; no workflow ports or formal approval."""
    contracts.validate(timeout, {"type": "integer", "minimum": 1, "maximum": 3600}, "Agent timeout")
    prepared, document = _admit_input(state, project_id, source, backend=backend, model=model, reason=reason, mode=mode,
                                      codex_config=codex_config, binding_override=binding_override, input_digest=input_digest)
    return _run_prepared(state, prepared, document, timeout, mode=mode, codex_config=codex_config,
        result_schema=result_schema, env=env, codex_bin=codex_bin, supervised=supervised,
        )


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
                  codex_bin, supervised, workspace=None):
    """One immutable snapshot, MCP lifecycle and native invocation evidence owner."""
    run_id = document.get("id") or uuid.uuid4().hex
    output = state.root / "runs" / run_id
    snapshot = output.with_name(run_id + ".input")
    if snapshot.resolve().is_relative_to(Path(prepared["path"]).resolve()):
        raise ValueError("Run storage cannot be inside the prepared input directory")
    schema = result_schema or agents.result_schema(["response"], document["role"] == "reviewer")
    document.update(kind="composition-agent-run", id=run_id, started=now(), status="preparing", template=None)
    _store(state, document)
    try:
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(prepared["path"], snapshot, symlinks=True)
        saved = workflow_definitions.inspect_input(snapshot, material=True)
        if saved["digest"] != prepared["digest"]:
            raise ValueError("Composition input changed while copying the run snapshot")
        document.update(input_path=str(snapshot))
        native_mcp = None
        if mode in ("task-mcp", "workspace-task-mcp"):
            scope = task_mcp.freeze(saved, run_id, output.with_name(run_id + ".scope.json"))
            document["task_mcp"] = {"scope": scope}
            _store(state, document)
            preflight = task_mcp.launch(scope, output.with_name(run_id + ".mcp-preflight.jsonl"))
            document["task_mcp"]["preflight"] = asyncio.run(task_mcp.probe(
                preflight, output.with_name(run_id + ".mcp-preflight.stderr")))
            native_audit = output.with_name(run_id + ".mcp-native.jsonl")
            native_mcp = task_mcp.launch(scope, native_audit)
        document["status"] = "running"
        _store(state, document)
        working = workspace if workspace is not None else output.with_name(run_id + ".cwd")
        if workspace is None:
            working.mkdir(mode=0o700)
        document.update(agents.invoke(document["binding"], document["role"], saved["prompt"], working, output, timeout,
            schema, codex_config=codex_config, mode=mode, task_mcp=native_mcp, env=env, codex_bin=codex_bin,
            supervised=supervised))
        if mode in ("task-mcp", "workspace-task-mcp") and document["status"] == "succeeded":
            document["task_mcp"]["native"] = task_mcp.verify_native(native_audit, scope["sha256"])
    except KeyboardInterrupt:
        # SDK preflight runs before the native process owner handles Ctrl+C.
        document.update(status="cancelled", error="Agent preparation or invocation interrupted")
    except (OSError, ValueError) as error:
        document.update(status="failed", error=str(error))
    document["finished"] = now()
    _store(state, document)
    return document


def runs(state: State, project_id: str) -> list[dict]:
    state.project(project_id)
    with state.connect() as db:
        return [json.loads(row[0]) for row in db.execute(
            "SELECT document FROM agent_runs WHERE project=? ORDER BY rowid DESC LIMIT 100", (project_id,))]


def _record(state: State, project_id: str, run_id: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM agent_runs WHERE project=? AND id=?", (project_id, run_id)).fetchone()
    if row is None:
        raise ValueError("Unknown agent run in this project")
    document = parse_json(row[0], "Agent run record", finite=True, bounded=True)
    if not isinstance(document, dict) or document.get("id") != run_id or document.get("project") != project_id:
        raise ValueError("Saved agent run differs from its selected project or run ID")
    return document


def _artifact(directory: Path, name: str, byte_limit: int) -> bytes:
    if is_link(directory) or not directory.is_dir():
        raise ValueError("Run artifacts require an ordinary directory")
    path = directory / name
    details = path.stat()
    if is_link(path) or not stat.S_ISREG(details.st_mode):
        raise ValueError("Run artifact requires an ordinary file: " + name)
    with path.open("rb") as stream:
        raw = stream.read(min(byte_limit + 1, details.st_size + 1))
    if len(raw) > byte_limit:
        raise ValueError(f"Complete run artifact exceeds its byte limit: {name} > {byte_limit}")
    return raw


def inspect_run(state: State, project_id: str, run_id: str, *, max_result_bytes: int = 8_388_608) -> dict:
    """Observe original composition material without current admission or redispatch."""
    contracts.validate(run_id, {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"}, "Run ID")
    contracts.validate(max_result_bytes, {"type": "integer", "minimum": 1}, "Result byte limit")
    document = _record(state, project_id, run_id)
    if document.get("kind") != "composition-agent-run":
        raise ValueError("Select an original composition agent run")
    storage = state.root / "runs"
    observed = {"schema_version": 1, "kind": "composition-run-observation", "run": document,
                "input": {"available": False}, "prompt": {"available": False},
                "result": {"available": False}, "formal_execution_authorized": False}
    try:
        prepared = workflow_definitions.inspect_input(storage / (run_id + ".input"), material=True)
        if (prepared["digest"] != document.get("input_digest") or prepared["request"] != document.get("input_request")
                or prepared["request"]["prompt_sha256"] != document.get("prompt_sha256")):
            raise ValueError("Saved input differs from the original run input identity")
        leaf = next(item for item in prepared['composition']['instances']
                    if item['path'] == prepared['request']['instance'])
        components.validate_agent_minimum(document.get('binding'), leaf.get('invocation_minimum'))
        observed["input"] = {"available": True, **prepared}
    except (OSError, ValueError, RecursionError) as error:
        observed["input"]["error"] = str(error)
    try:
        request = document.get("input_request")
        contracts.validate(request, contracts.COMPOSITION_INPUT, "Original input request")
        raw = _artifact(storage / (run_id + ".protocol"), "prompt.txt", request["prompt_bytes"])
        digest = hashlib.sha256(raw).hexdigest()
        if (len(raw) != request["prompt_bytes"] or digest != request["prompt_sha256"]
                or digest != document.get("prompt_sha256")):
            raise ValueError("Original invocation prompt differs from its recorded identity")
        if observed["input"]["available"] and raw != prepared["prompt"].encode("utf-8"):
            raise ValueError("Original invocation prompt differs from the frozen input")
        observed["prompt"] = {"available": True, "bytes": len(raw), "sha256": digest,
                              "input_compared": observed["input"]["available"]}
    except (OSError, ValueError, RecursionError) as error:
        observed["prompt"]["error"] = str(error)
    if document.get("result_sha256") is None:
        observed["result"]["error"] = "No original structured result identity was recorded"
    else:
        try:
            raw = _artifact(storage / run_id, "result.json", max_result_bytes)
            digest = hashlib.sha256(raw).hexdigest()
            if digest != document["result_sha256"]:
                raise ValueError("Structured result differs from its original run SHA256")
            observed["result"] = {"available": True, "bytes": len(raw), "sha256": digest,
                                  "document": parse_json(raw.decode("utf-8"), "Agent result", finite=True, bounded=True)}
        except (OSError, ValueError, RecursionError) as error:
            observed["result"]["error"] = str(error)
    return observed


def output(state: State, project_id: str, run_id: str, *, native_history: bool = False,
           offset: int = 0, limit: int = 65_536, revision: str | None = None) -> dict:
    document = _record(state, project_id, run_id)
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
                request = _session_packet(_session_folder(state, run_id), 'request.json')
                name = 'result.json' if request['schema'] is not None else 'result.txt'
                raw = _artifact(state.root / 'runs' / run_id, name, 8_388_608)
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
    """Start admission ended before reserving or launching native work."""

    def __init__(self, message, intent_id):
        super().__init__(message)
        self.intent_id = intent_id


def _session_id(value, label='Session ID'):
    contracts.validate(value, {'type': 'string', 'pattern': '^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$'}, label)
    return value


def _session_encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _session_sha(value):
    return hashlib.sha256(_session_encode(value)).hexdigest()


def _sync_directory_chain(directory):
    for parent in (directory, *directory.parents):
        descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _publish_session_packet(destination, values):
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
        _sync_directory_chain(staged)
        publish_directory(staged, destination)
        _sync_directory_chain(destination)
        for name, raw in values.items():
            if _artifact(destination, name, len(raw)) != raw:
                raise ValueError('Session packet changed after durable publication')
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def _session_packet(directory, name='record.json'):
    return parse_json(_artifact(directory, name, 10_000_000).decode('utf-8'), 'Native session packet', finite=True, bounded=True)


def _session_folder(state, ident):
    return state.root / 'runs' / (_session_id(ident) + '.session-turn')


def _root_folder(state, ident):
    return state.root / 'runs' / (_session_id(ident) + '.session')


def _find_run(state, project, ident):
    with state.connect() as db:
        row = db.execute('SELECT document FROM agent_runs WHERE project=? AND id=?', (project, ident)).fetchone()
    return None if row is None else parse_json(row[0], 'Native session run', finite=True, bounded=True)


def _observe_session_run(state, document):
    folder = _session_folder(state, document['id'])
    request = _session_packet(folder, 'request.json')
    if (_session_sha(request) != document['request_sha256'] or request['run_id'] != document['id']
            or request['project'] != document['project'] or request['session'] != document['session']):
        raise ValueError('Session run differs from its original immutable request')
    stop_request = None
    if (folder / 'stop').exists():
        stop_request = _session_packet(folder / 'stop')
        if (stop_request.get('run_id') != document['id'] or stop_request.get('project') != document['project']
                or stop_request.get('session') != document['session']['id']
                or stop_request.get('request_sha256') != document['request_sha256']):
            raise ValueError('Saved stop request differs from its original turn')
    if (folder / 'final').exists():
        final = _session_packet(folder / 'final')
        if final['request_sha256'] != document['request_sha256'] or final['session'] != document['session']:
            raise ValueError('Session final differs from the selected request')
        if final.get('status') == 'succeeded':
            raw = _artifact(state.root / 'runs' / document['id'],
                            'result.json' if request['schema'] is not None else 'result.txt', 8_388_608)
            if hashlib.sha256(raw).hexdigest() != final['result_sha256']:
                raise ValueError('Session result differs from its original complete bytes')
        return {**final, 'stop_request': stop_request}
    observed = dict(document, status='unknown', execution_stopped=False, stop_request=stop_request)
    try:
        owner = _session_packet(folder / 'owner')
        if owner['request_sha256'] == document['request_sha256'] and processes.identity(owner['identity']['pid']) == owner['identity']:
            observed['status'] = 'running'
            observed['owner'] = owner['identity']
    except (FileNotFoundError, ProcessLookupError, ValueError):
        pass
    return observed


def _read_session_context(state, root):
    folder = _root_folder(state, root['session']['id']) / 'context'
    if inventory_tree(folder)[0] != root['context_digest']:
        raise ValueError('Frozen session context or resources changed')
    return _session_packet(folder, 'context.json')


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
    _session_id(ident)
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
        _session_id(intent_id, 'Birth intent')
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
        _session_id(intent, 'Session intent')
        _session_prompt(prompt, timeout)
        if sys.platform != 'linux':
            raise ValueError('Persistent native sessions require Linux/WSL2')
    except ValueError as error:
        raise SessionRejected(str(error), intent) from error
    ident = uuid.uuid5(uuid.NAMESPACE_URL, 'ergora:native-session:' + project_id + ':' + intent).hex
    submitted = {'role': role, 'prompt': prompt, 'timeout': timeout, 'skills': skill_names or [], 'recall': recall,
                 'template': template, 'expected_revision': revision,
                 'codex_config': str(codex_config) if codex_config is not None else None, 'intent_id': intent}
    existing = _find_run(state, project_id, ident)
    if existing is not None:
        if existing['submitted'] != submitted:
            raise ValueError('Session intent was already consumed by a different request')
        return _observe_session_run(state, existing)
    state.root.joinpath('runs').mkdir(exist_ok=True, mode=0o700)
    with file_lock(state.root / 'runs' / (ident + '.session.lock'), blocking=False) as lock:
        if _find_run(state, project_id, ident) is not None:
            return _start_session(state, project_id, role, prompt, timeout, skill_names, recall, template, intent, revision, codex_config)
        project = state.project(project_id)
        if revision != project['revision']:
            raise SessionRejected('Session start requires the current project revision', intent)
        clock = budget_clock.authorize(timeout)
        folder = _root_folder(state, ident)
        folder.mkdir(mode=0o700)
        home = folder / 'native-home'
        home.mkdir(mode=0o700)
        staged = Path(tempfile.mkdtemp(prefix='.context-', dir=folder))
        try:
            full_prompt, schema, context = _prepare_role(state, project_id, role, prompt, timeout, skill_names, recall, template,
                                                       freeze=(staged, folder / 'context'))
            if context['project_revision'] != revision or state.project(project_id)['revision'] != revision:
                raise ValueError('Project changed during session preparation; no native effect was started')
            adapter = agent_backends.for_binding(context['binding'], {'codex': {'config': codex_config, 'role': role}})
            inference = adapter.session_configuration(Path(project['repo']))
            requested = context['binding']
            context.update(binding=inference['binding'], requested_binding=requested, inference=inference,
                           repo=project['repo'], repo_identity=_directory_identity(Path(project['repo'])),
                           native_home=str(home), native_home_identity=_directory_identity(home), grant=None,
                           sandbox=inference['sandbox'])
            (staged / 'context.json').write_bytes(_session_encode(context))
            for path in staged.rglob('*'):
                if path.is_file():
                    with path.open('rb') as stream:
                        os.fsync(stream.fileno())
            for path in sorted((p for p in staged.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                _sync_directory_chain(path)
            _sync_directory_chain(staged)
            publish_directory(staged, folder / 'context')
            _sync_directory_chain(folder / 'context')
            digest = inventory_tree(folder / 'context')[0]
        except (OSError, ValueError) as error:
            raise SessionRejected(str(error), intent) from error
        finally:
            if staged.exists():
                shutil.rmtree(staged)
        # No admission-rejected classification is allowed beyond this point:
        # reservation/attempt failures and lost replies observe the original slot.
        return _reserve_session_turn(state, project_id, ident, None, ident, 0, prompt, timeout, clock,
                                     context, digest, submitted, lock)


def _directory_identity(path):
    details = path.stat(follow_symlinks=False)
    if is_link(path) or not stat.S_ISDIR(details.st_mode):
        raise ValueError('Session requires an ordinary directory')
    return [details.st_dev, details.st_ino]


def continue_session(state: State, project_id: str, session_id: str, parent_run_id: str, prompt: str, *,
                     expected_revision: int, intent_id: str, timeout: int = 300) -> dict:
    _session_id(session_id)
    _session_id(parent_run_id, 'Parent run')
    _session_id(intent_id, 'Turn intent')
    _session_prompt(prompt, timeout)
    ident = uuid.uuid5(uuid.NAMESPACE_URL, 'ergora:native-turn:' + session_id + ':' + intent_id).hex
    submitted = {'parent_run': parent_run_id, 'prompt': prompt, 'expected_revision': expected_revision,
                 'timeout': timeout, 'intent_id': intent_id}
    existing = _find_run(state, project_id, ident)
    if existing is not None:
        if existing['submitted'] != submitted or existing['session']['id'] != session_id:
            raise ValueError('Turn intent was already consumed by a different request')
        return _observe_session_run(state, existing)
    with file_lock(state.root / 'runs' / (session_id + '.session.lock'), blocking=False) as lock:
        turns = _session_turns(state, project_id, session_id)
        if len(turns) >= _MAX_SESSION_TURNS:
            raise ValueError(f'This session reached its {_MAX_SESSION_TURNS}-turn limit; no new turn was reserved')
        latest = turns[-1]
        context = _read_session_context(state, turns[0])
        if expected_revision != context['project_revision']:
            raise ValueError('Turn revision differs from its original session')
        _validate_session_authority(state, context)
        if (latest['id'] != parent_run_id or latest.get('status') in ('unknown', 'reserved', 'running')
                or latest.get('execution_stopped') is not True
                or not latest.get('native_session', {}).get('id')):
            raise ValueError('Select the latest stopped turn with its saved native UUID; consumed or unknown parents cannot be dispatched')
        return _reserve_session_turn(state, project_id, session_id, latest, ident, len(turns), prompt, timeout,
                                     budget_clock.authorize(timeout), context, turns[0]['context_digest'], submitted, lock)


def _reserve_session_turn(state, project, root, parent, ident, ordinal, prompt, timeout, clock, context, digest, submitted, lock):
    _validate_session_authority(state, context)
    full_prompt = prompt + context['suffix']
    if len(full_prompt.encode('utf-8')) > 10_000_000:
        raise ValueError('Complete session prompt exceeds 10 MB; it was not truncated')
    session = {'id': root, 'parent_run': parent['id'] if parent else None, 'ordinal': ordinal}
    request = {'run_id': ident, 'project': project, 'session': session, 'submitted': submitted,
               'context_digest': digest, 'prompt': full_prompt, 'schema': context['schema'],
               'clock': clock, 'timeout': timeout, 'native_id': parent['native_session']['id'] if parent else None}
    folder = _session_folder(state, ident)
    _publish_session_packet(folder, {'request.json': _session_encode(request)})
    document = {'id': ident, 'project': project, 'kind': 'native-agent-run', 'role': context['role'],
                'binding': context['binding'], 'project_revision': context['project_revision'],
                'template': context['template'], 'session': session, 'submitted': submitted,
                'context_digest': digest, 'request_sha256': _session_sha(request),
                'prompt_sha256': hashlib.sha256(full_prompt.encode()).hexdigest(),
                'started': now(), 'status': 'reserved', 'formal_execution_authorized': False}
    _store(state, document)
    if budget_clock.remaining(clock, timeout) <= 0:
        return _observe_session_run(state, document)
    _publish_session_packet(folder / 'attempt', {'record.json': _session_encode({'request_sha256': document['request_sha256']})})
    environment = dict(os.environ)
    source = str(Path(__file__).resolve().parent.parent)
    environment['PYTHONPATH'] = source + (os.pathsep + environment['PYTHONPATH'] if environment.get('PYTHONPATH') else '')
    argv = [sys.executable, '-c', 'from ergora.agent_runs import session_main; session_main()',
            str(state.root), ident, str(lock.fileno())]
    try:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 env=environment, pass_fds=(lock.fileno(),), start_new_session=True)
    except OSError as error:
        failed = dict(document, status='failed', error=str(error), execution_stopped=True, finished=now())
        _publish_session_packet(folder / 'final', {'record.json': _session_encode(failed)})
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
    return _observe_session_run(state, document)


def stop_session(state: State, project_id: str, session_id: str, run_id: str, *, intent_id: str) -> dict:
    _session_id(intent_id, 'Stop intent')
    document = _record(state, project_id, _session_id(run_id))
    if document.get('session', {}).get('id') != _session_id(session_id):
        raise ValueError('Stop must select this project and session turn')
    folder = _session_folder(state, run_id)
    stop = {'project': project_id, 'session': session_id, 'run_id': run_id,
            'request_sha256': document['request_sha256'], 'intent_id': intent_id}
    if (folder / 'stop').exists():
        if _session_packet(folder / 'stop') != stop:
            raise ValueError('The original stop request is already recorded')
        _sync_directory_chain(folder / 'stop')
    else:
        _publish_session_packet(folder / 'stop', {'record.json': _session_encode(stop)})
    notification = 'unconfirmed'
    try:
        owner = _session_packet(folder / 'owner')
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
    document = _find_run(state, _session_packet(_session_folder(state, ident), 'request.json')['project'], ident)
    if document is None:
        raise ValueError('Session turn has no original reservation')
    root = document['session']['id']
    lock_path = state.root / 'runs' / (root + '.session.lock')
    if (os.fstat(fd).st_dev, os.fstat(fd).st_ino) != (lock_path.stat().st_dev, lock_path.stat().st_ino):
        raise ValueError('Session turn lacks its original inherited lifecycle lock')
    import fcntl
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    folder = _session_folder(state, ident)
    request = _session_packet(folder, 'request.json')
    if (_session_sha(request) != document['request_sha256']
            or _session_packet(folder / 'attempt')['request_sha256'] != document['request_sha256']):
        raise ValueError('Session effect differs from its consumed attempt')
    _publish_session_packet(folder / 'owner', {'record.json': _session_encode({
        'identity': processes.identity(os.getpid()), 'request_sha256': document['request_sha256']})})
    stopping = False
    expired = False

    def cancel(_signum, _frame):
        nonlocal stopping
        stopping = True
        processes.cancel_supervised()

    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)

    def should_stop():
        nonlocal expired
        try:
            expired = budget_clock.remaining(request['clock'], request['timeout']) <= 0
        except ValueError:
            expired = True
        return stopping or expired or (folder / 'stop').exists()

    try:
        context = _read_session_context(state, document)
        _validate_session_authority(state, context)
        if should_stop():
            document.update(status='cancelled', error='Turn stopped or expired before native effect')
        else:
            environment = dict(os.environ, CODEX_HOME=context['native_home'])
            native = {'configuration': context['inference'], 'native_id': request['native_id']}
            document.update(agents.invoke(context['binding'], context['role'], request['prompt'], Path(context['repo']),
                state.root / 'runs' / ident, max(.01, budget_clock.remaining(request['clock'], request['timeout'])),
                request['schema'], env=environment, supervised=True, lock_fd=fd, session=native, stop_requested=should_stop))
        if expired:
            document['status'] = 'timed_out'
        document['execution_stopped'] = True
    except (OSError, ValueError, TypeError, KeyError) as error:
        document.update(status='failed', error=str(error), execution_stopped=True)
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
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            _sync_directory_chain(output)
        if document.get('result_sha256') is not None:
            name = 'result.json' if request['schema'] is not None else 'result.txt'
            if hashlib.sha256(_artifact(state.root / 'runs' / ident, name, 8_388_608)).hexdigest() != document['result_sha256']:
                raise ValueError('Durable result readback differs from the original result')
    except (OSError, ValueError) as error:
        document.update(status='unknown', error='Native artifacts lack durable confirmation: ' + str(error))
    document['finished'] = now()
    _publish_session_packet(folder / 'final', {'record.json': _session_encode(document)})
    _store(state, document)
