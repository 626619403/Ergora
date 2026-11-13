"""Independent Agent invocations, frozen context and durable run records."""

import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import time
import uuid

from . import agent_backends, agent_definitions, agents, contracts, projects, task_mcp, workflow_definitions
from .bindings import validate_binding
from .state import State, file_lock, now


def _store(state: State, document: dict) -> None:
    with state.connect() as db:
        db.execute("INSERT INTO agent_runs VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET document=excluded.document",
                   (document["id"], document["project"], json.dumps(document)))


def run_agent(state: State, project_id: str, role: str, prompt: str, timeout: int = 300,
              skill_names: list[str] | None = None, recall: str | None = None,
              template: str | None = None) -> dict:
    if role not in agents.ROLE_CAPABILITIES:
        raise ValueError(f"Unknown agent role: {role}")
    if not prompt.strip() or not 1 <= timeout <= 3600:
        raise ValueError("Require a prompt and timeout of 1–3600 seconds")
    project = state.project(project_id)
    configuration = projects.effective_configuration(project)
    context = {"skills": [], "memories": []}
    if skill_names:
        from . import skill_assets

        active = {head["name"]: head for head in skill_assets.versions(state, project_id)["active"]}
        for name in skill_names:
            if name not in active:
                raise ValueError(f"Unknown active skill: {name}")
            bundle = skill_assets.get(state, project_id, active[name]["digest"])
            context["skills"].append({"name": name, "digest": bundle["digest"]})
            prompt += f"\n\nSelected skill {name}; resources: {bundle['path']}\n" + (Path(bundle["path"]) / "SKILL.md").read_text(encoding="utf-8")
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
    run_id = uuid.uuid4().hex
    document = {"id": run_id, "project": project_id, "role": role, "binding": binding,
                "project_revision": project["revision"], "started": now(), "status": "running",
                "configuration": configuration,
                "context": context, "template": template, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
    _store(state, document)
    try:
        document.update(agents.invoke(binding, role, prompt, Path(project["repo"]), state.root / "runs" / run_id, timeout, schema))
    except (OSError, ValueError) as error:
        document.update(status="failed", error=str(error))
    document["finished"] = now()
    _store(state, document)
    return document


def _admit_input(state: State, project_id: str, source: Path, *, backend: str | None,
                 model: str | None, reason: str | None, mode: str, codex_config: Path | None,
                 binding_override: dict | None = None) -> tuple[dict, dict]:
    """One current admission produces both the preview and the persisted call contract."""
    contracts.validate(mode, {"enum": ["text-only", "task-mcp"]}, "Composition call mode")
    prepared = workflow_definitions.inspect_input(source, material=True)
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
        {"tool": backend} if backend else dict(leaf["backend_request"]))
    if model is not None:
        binding["model"] = model
    agents.validate_binding(leaf["role"], binding, formal=True)
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
                codex_config: Path | None = None) -> dict:
    """Current admission only: no model, server, run record or formal authorization."""
    _, document = _admit_input(state, project_id, source, backend=backend, model=model, reason=reason, mode=mode,
                               codex_config=codex_config)
    return document


def run_input(state: State, project_id: str, source: Path, timeout: int = 300, *,
              backend: str | None = None, model: str | None = None, reason: str | None = None,
              codex_config: Path | None = None, mode: str = "text-only", binding_override: dict | None = None,
              result_schema: dict | None = None, env: dict | None = None,
              codex_bin: str = "codex", supervised: bool = False,
              allow_one_continuation: bool = False) -> dict:
    """Explicit independent restricted call; no workflow ports or formal approval."""
    contracts.validate(timeout, {"type": "integer", "minimum": 1, "maximum": 3600}, "Agent timeout")
    deadline = time.monotonic() + timeout if allow_one_continuation else None
    prepared, document = _admit_input(state, project_id, source, backend=backend, model=model, reason=reason, mode=mode,
                                      codex_config=codex_config, binding_override=binding_override)
    if allow_one_continuation:
        if supervised or result_schema is not None:
            raise ValueError("Continuation sources require an explicitly enabled standalone call with the default schema")
        agent_backends.for_binding(document["binding"]).check_continuation(mode)
    return _run_prepared(state, prepared, document, timeout, mode=mode, codex_config=codex_config,
        result_schema=result_schema, env=env, codex_bin=codex_bin, supervised=supervised,
        continuation={"schema_version": 1, "kind": "source"} if allow_one_continuation else None, deadline=deadline)


def continue_input(state: State, project_id: str, source_run_id: str, source: Path, *,
                   intent_id: str, timeout: int = 300, env: dict | None = None) -> dict:
    """Consume one explicit source slot; saved attempts are never dispatched again."""
    contracts.validate(timeout, {"type": "integer", "minimum": 1, "maximum": 3600}, "Agent timeout")
    contracts.validate(intent_id, {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"}, "Continuation intent")
    deadline = time.monotonic() + timeout
    project = state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM agent_runs WHERE project=? AND id=?", (project_id, source_run_id)).fetchone()
    if row is None:
        raise ValueError("Unknown continuation source in this project")
    original = json.loads(row[0])
    contract = original.get("continuation", {})
    if (original.get("kind") != "composition-agent-run" or original.get("status") != "succeeded"
            or contract.get("schema_version") != 1 or contract.get("kind") != "source"
            or "native" not in contract or original.get("formal_execution_authorized")):
        raise ValueError("Continuation requires a successful explicitly enabled standalone source")
    prepared = workflow_definitions.inspect_input(source, material=True)
    # A deterministic child key gives this source exactly one durable slot,
    # including when the caller disappears before receiving its result.
    child_id = uuid.uuid5(uuid.NAMESPACE_URL, "ergora:one-continuation:" + source_run_id).hex
    request = {"intent_id": intent_id, "input_digest": prepared["digest"], "timeout": timeout}
    with file_lock(state.root / "runs" / (source_run_id + ".continuation.lock"), blocking=False) as lock:
        with state.connect() as db:
            existing = db.execute("SELECT document FROM agent_runs WHERE id=?", (child_id,)).fetchone()
        if existing is not None:
            saved = json.loads(existing[0])
            if (saved.get("project") != project_id or saved.get("continuation", {}).get("source_run") != source_run_id
                    or saved["continuation"]["request"] != request):
                raise ValueError("The source continuation slot is already claimed by a different input intent or budget")
            return saved
        authority = contract["authority"]
        repo = Path(project["repo"])
        details = repo.stat(follow_symlinks=False)
        if (project["revision"] != original["project_revision"] or project["repo"] != authority["repo"]
                or [details.st_dev, details.st_ino] != authority["repo_identity"]):
            raise ValueError("Project revision or repository identity changed; start a new source")
        previous = workflow_definitions.inspect_input(state.root / "runs" / (source_run_id + ".input"), material=True)
        if previous["digest"] != original["input_digest"]:
            raise ValueError("Original continuation input differs from its frozen digest")
        stable = ("root", "instance", "grant", "preview_sha256", "max_prompt_bytes")
        if (prepared["composition"] != previous["composition"]
                or any(prepared["request"][key] != previous["request"][key] for key in stable)):
            raise ValueError("Continuation must preserve the complete composition, material, instance and grant")
        admitted, document = _admit_input(state, project_id, source, backend=None, model=None,
            reason=original["backend_reason"], mode="task-mcp", codex_config=None, binding_override=original["binding"])
        if admitted["digest"] != prepared["digest"] or document["policy"] != original["policy"]:
            raise ValueError("Continuation input or backend policy changed during admission")
        old_scope = original["task_mcp"]["scope"]
        if old_scope["path"] != str(state.root / "runs" / (source_run_id + ".scope.json")):
            raise ValueError("Source scope differs from its original call path")
        old_audit = state.root / "runs" / (source_run_id + ".mcp-native.jsonl")
        old_view = task_mcp.ResourceView.load(Path(old_scope["path"]), old_scope["sha256"]).document
        if (old_view["run_id"] != source_run_id or old_view["input_digest"] != previous["digest"]
                or task_mcp.verify_native(old_audit, old_scope["sha256"]) != original["task_mcp"]["native"]
                or task_mcp.verify_reads(old_view, old_audit.read_bytes()) != original["task_mcp"]["reads"]):
            raise ValueError("Source MCP evidence differs from its frozen complete material")
        adapter = agent_backends.for_binding(original["binding"])
        native = adapter.continuation_source(state.root / "runs" / (source_run_id + ".protocol"),
                                             cwd=state.root / "runs" / (source_run_id + ".cwd"))
        if native != contract["native"] or native["authority"] != authority:
            raise ValueError("Native source no longer matches its original authorization")
        document.update(id=child_id, continuation={"schema_version": 1, "kind": "resume", "source_run": source_run_id,
            "request": request, "state": "reserved", "authority": authority, "source": native})
        # _run_prepared publishes this immutable intent before any preflight or
        # SDK work. No failure path releases the deterministic child slot.
        return _run_prepared(state, prepared, document, timeout, mode="task-mcp", codex_config=None,
            result_schema=authority["schema"], env=env, codex_bin="codex", supervised=False,
            workspace=Path(native["cwd"]), continuation=document["continuation"], lock_fd=lock.fileno(), deadline=deadline)


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
                  codex_bin, supervised, workspace=None, continuation=None, lock_fd=None, deadline=None):
    """One immutable snapshot, MCP lifecycle and native invocation evidence owner."""
    run_id = document.get("id") or uuid.uuid4().hex
    output = state.root / "runs" / run_id
    snapshot = output.with_name(run_id + ".input")
    if snapshot.resolve().is_relative_to(Path(prepared["path"]).resolve()):
        raise ValueError("Run storage cannot be inside the prepared input directory")
    schema = result_schema or agents.result_schema(["response"], document["role"] == "reviewer")
    document.update(kind="composition-agent-run", id=run_id, started=now(), status="preparing", template=None)
    if continuation is not None and continuation["kind"] == "source":
        project = state.project(document["project"])
        details = Path(project["repo"]).stat(follow_symlinks=False)
        continuation["authority"] = {"source_run": run_id, "project": document["project"],
            "project_revision": document["project_revision"], "repo": project["repo"],
            "repo_identity": [details.st_dev, details.st_ino], "schema": schema, "timeout": timeout,
            **{key: document[key] for key in ("role", "binding", "input_digest", "input_request", "policy", "context")}}
        document["continuation"] = continuation
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
            async def probe():
                operation = task_mcp.probe(preflight, output.with_name(run_id + ".mcp-preflight.stderr"))
                return await operation if deadline is None else await asyncio.wait_for(operation, max(0, deadline - time.monotonic()))
            document["task_mcp"]["preflight"] = asyncio.run(probe())
            native_audit = output.with_name(run_id + ".mcp-native.jsonl")
            native_mcp = task_mcp.launch(scope, native_audit)
        document["status"] = "running"
        _store(state, document)
        working = workspace if workspace is not None else output.with_name(run_id + ".cwd")
        if workspace is None:
            working.mkdir(mode=0o700)
        remaining = timeout if deadline is None else deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Agent budget expired during preparation; no SDK was started")
        if continuation is not None and continuation["kind"] == "resume":
            continuation["state"] = "unknown"
            _store(state, document)
        extra = {"continuation": continuation} if continuation is not None else {}
        if lock_fd is not None:
            extra["lock_fd"] = lock_fd
        document.update(agents.invoke(document["binding"], document["role"], saved["prompt"], working, output, remaining,
            schema, codex_config=codex_config, mode=mode, task_mcp=native_mcp, env=env, codex_bin=codex_bin,
            supervised=supervised, **extra))
        if mode in ("task-mcp", "workspace-task-mcp") and document["status"] == "succeeded":
            document["task_mcp"]["native"] = task_mcp.verify_native(native_audit, scope["sha256"])
            if continuation is not None:
                document["task_mcp"]["reads"] = task_mcp.verify_reads(
                    task_mcp.ResourceView.load(Path(scope["path"]), scope["sha256"]).document, native_audit.read_bytes())
                if continuation["kind"] == "source":
                    continuation["native"] = agent_backends.for_binding(document["binding"]).continuation_source(
                        output.with_name(run_id + ".protocol"), cwd=working)
    except KeyboardInterrupt:
        # SDK preflight runs before the native process owner handles Ctrl+C.
        document.update(status="cancelled", error="Agent preparation or invocation interrupted")
    except (OSError, ValueError) as error:
        document.update(status="failed", error=str(error))
    if continuation is not None and continuation["kind"] == "resume":
        # The process owner has finished cleanup. Observe physical additions on
        # failure too; missing receipt/idle must never turn unknown into success.
        try:
            continuation["native"] = agent_backends.for_binding(document["binding"]).continuation_result(
                output.with_name(run_id + ".protocol"), source=continuation["source"])
            if document["status"] == "succeeded":
                if (not continuation["native"]["completed"]
                        or continuation["native"]["result_sha256"] != document["result_sha256"]):
                    raise ValueError("Continuation receipt differs from this call's structured result")
                continuation["state"] = "completed"
        except (OSError, ValueError, TypeError, KeyError) as error:
            continuation["observation_error"] = str(error)
            if document["status"] == "succeeded":
                document.update(status="failed", error=str(error))
    document["finished"] = now()
    _store(state, document)
    return document


def runs(state: State, project_id: str) -> list[dict]:
    state.project(project_id)
    with state.connect() as db:
        return [json.loads(row[0]) for row in db.execute(
            "SELECT document FROM agent_runs WHERE project=? ORDER BY rowid DESC LIMIT 100", (project_id,))]


def output(state: State, project_id: str, run_id: str, *, native_history: bool = False,
           offset: int = 0, limit: int = 65_536, revision: str | None = None) -> dict:
    state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM agent_runs WHERE project=? AND id=?", (project_id, run_id)).fetchone()
    if row is None:
        raise ValueError("Unknown agent run in this project")
    document = json.loads(row[0])
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
