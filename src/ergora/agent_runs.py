"""Independent Agent invocations, frozen context and durable run records."""

import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from . import agent_backends, agent_definitions, agents, contracts, projects, task_mcp, workflow_definitions
from .bindings import validate_binding
from .state import State, now


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
    project = state.project(project_id)
    prepared = workflow_definitions.inspect_input(source, material=True)
    leaf = next(item for item in prepared["composition"]["instances"] if item["path"] == prepared["request"]["instance"])
    permissions = leaf["permissions"]
    if permissions["write"] or permissions["shell"] or permissions["network"]:
        raise ValueError(f"{'Text-only' if mode == 'text-only' else 'Task MCP'} calls cannot satisfy write, shell or network requests; use a read-only leaf")
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
    if mode == "task-mcp":
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
                  read_scope_semantics="Permission paths are upper bounds; only declared fixed resources are provided",
                  sdk_check="top-level package presence only; actual compatibility/readiness checked during run" if mode == "task-mcp" else "not required")
    return prepared, {"schema_version": 1, "kind": "composition-admission", "project": project_id,
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
              codex_bin: str = "codex", supervised: bool = False) -> dict:
    """Explicit independent restricted call; no workflow ports or formal approval."""
    contracts.validate(timeout, {"type": "integer", "minimum": 1, "maximum": 3600}, "Agent timeout")
    prepared, document = _admit_input(state, project_id, source, backend=backend, model=model, reason=reason, mode=mode,
                                      codex_config=codex_config, binding_override=binding_override)
    run_id = uuid.uuid4().hex
    output = state.root / "runs" / run_id
    snapshot = output.with_name(run_id + ".input")
    if snapshot.resolve().is_relative_to(Path(prepared["path"]).resolve()):
        raise ValueError("Run storage cannot be inside the prepared input directory")
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
        if mode == "task-mcp":
            scope = task_mcp.freeze(saved, run_id, output.with_name(run_id + ".scope.json"))
            document["task_mcp"] = {"scope": scope}
            _store(state, document)
            preflight = task_mcp.launch(scope, output.with_name(run_id + ".mcp-preflight.jsonl"))
            document["task_mcp"]["preflight"] = asyncio.run(task_mcp.probe(preflight, output.with_name(run_id + ".mcp-preflight.stderr")))
            native_audit = output.with_name(run_id + ".mcp-native.jsonl")
            native_mcp = task_mcp.launch(scope, native_audit)
        document["status"] = "running"
        _store(state, document)
        working = output.with_name(run_id + ".cwd")
        working.mkdir(mode=0o700)
        document.update(agents.invoke(document["binding"], document["role"], saved["prompt"], working, output, timeout,
            result_schema or agents.result_schema(["response"], document["role"] == "reviewer"),
            codex_config=codex_config, mode=mode, task_mcp=native_mcp, env=env, codex_bin=codex_bin, supervised=supervised))
        if mode == "task-mcp" and document["status"] == "succeeded":
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


def output(state: State, project_id: str, run_id: str) -> dict:
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
    return {"id": run_id, "status": document["status"], "streams": streams}
