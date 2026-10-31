"""Concrete layer bindings. Selection never silently changes the reference runtime."""

import json
import importlib.util
import hashlib
from pathlib import Path
import re
import sys
import uuid
from urllib.parse import urlsplit

from . import agents, kernel, processes
from .state import State, now


CATALOG = {
    **agents.CHOICES,
    "memory": ["sqlite", "reme"],
    "optimizer": ["manual", "gepa"],
    "research": ["urls"],
    "scheduler": ["manual", "temporal"],
    "kernel": ["manual", "forgekernel"],
}


def validate_binding(layer: str, binding: dict) -> None:
    if layer not in CATALOG or not isinstance(binding, dict) or binding.get("tool") not in CATALOG[layer]:
        raise ValueError(f"Unsupported layer/tool: {layer}; choices: {CATALOG.get(layer, [])}")
    tool = binding["tool"]
    if layer in agents.ROLE_CAPABILITIES:
        agents.validate_binding(layer, binding)
        return
    if layer == "kernel":
        kernel.validate_binding(binding)
        return
    allowed = {"codex": {"tool", "model"}, "claude-code": {"tool", "model"}, "command": {"tool", "argv"},
               "sqlite": {"tool"}, "reme": {"tool", "endpoint", "token_env"},
               "manual": {"tool"}, "gepa": {"tool", "proposer_argv"}, "urls": {"tool"},
               "temporal": {"tool", "address", "namespace", "task_queue"}}[tool]
    if set(binding) - allowed:
        raise ValueError(f"Unknown binding options: {sorted(set(binding) - allowed)}")
    if "model" in binding and (not isinstance(binding["model"], str) or not binding["model"].strip()):
        raise ValueError("model must be a nonempty model ID")
    if tool == "command":
        argv = binding.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x or "\0" in x for x in argv):
            raise ValueError("command requires a nonempty argv array; prompt is passed via stdin")
    if tool == "reme":
        endpoint = binding.get("endpoint")
        if not isinstance(endpoint, str):
            raise ValueError("ReMe requires an endpoint URL")
        url = urlsplit(endpoint)
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("ReMe endpoint requires HTTP(S), without credentials, query or fragment")
        if "token_env" in binding and (not isinstance(binding["token_env"], str) or
                                      not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", binding["token_env"])):
            raise ValueError("token_env must name an environment variable")
    if tool == "gepa":
        validate_binding("implementer", {"tool": "command", "argv": binding.get("proposer_argv")})
    if tool == "temporal":
        for key in ("address", "namespace", "task_queue"):
            if not isinstance(binding.get(key), str) or not binding[key].strip():
                raise ValueError(f"Temporal requires a nonempty {key}")


def catalog() -> dict:
    result = {}
    for layer, choices in CATALOG.items():
        result[layer] = []
        for tool in choices:
            installed = True if tool in ("sqlite", "manual", "urls") else None
            if tool in ("codex", "claude-code"):
                installed = agents.available({"tool": tool}, Path.cwd())
            if tool == "mini-swe-agent":
                installed = importlib.util.find_spec("minisweagent") is not None
            if tool == "gepa":
                installed = importlib.util.find_spec("gepa") is not None
            if tool == "temporal":
                installed = importlib.util.find_spec("temporalio") is not None
            operations = {"memory": ["memory.save", "memory.search", "memory.sync"],
                          "optimizer": ["skill.import"] if tool == "manual" else ["skill.optimize"]}
            operations.update(research=["research.run"], scheduler=["research.run"] if tool == "manual" else ["research.schedule", "research.worker"])
            operations["kernel"] = [] if tool == "manual" else ["kernel.plan", "kernel.prepare", "kernel.run", "kernel.status"]
            supported = tool not in ("forgekernel", "mini-swe-agent") or sys.platform == "linux"
            result[layer].append({"tool": tool, "installed": installed if supported else False,
                                  "supported": supported, "platform_note": "" if supported else "Requires Linux; use WSL2",
                                  "authentication": "not_checked",
                                  "operations": operations.get(layer, ["agent.run"]),
                                  "capabilities": agents.TOOL_CAPABILITIES.get(tool, []),
                                  "requires": agents.ROLE_CAPABILITIES.get(layer, [])})
    return result


def doctor(state: State, project_id: str) -> dict:
    project = state.project(project_id)
    checks = []
    for layer in CATALOG:
        binding = agents.binding_for(project, layer) if layer in agents.ROLE_CAPABILITIES else project["bindings"].get(layer, {"tool": "manual"})
        validate_binding(layer, binding)
        tool = binding["tool"]
        if layer == "kernel":
            checks.append({"layer": layer, "tool": tool, **kernel.available(binding),
                           "authentication": "not_checked", "runtime": "native ForgeKernel campaign; candidate only"})
            continue
        if layer == "memory":
            checks.append({"layer": layer, "tool": tool, "installed": True if tool == "sqlite" else None,
                           "connectivity": "local" if tool == "sqlite" else "not_checked"})
            continue
        if layer == "optimizer":
            checks.append({"layer": layer, "tool": tool, "installed": tool == "manual" or importlib.util.find_spec("gepa") is not None,
                           "authentication": "not_checked"})
            continue
        if layer in ("research", "scheduler"):
            checks.append({"layer": layer, "tool": tool, "installed": tool != "temporal" or importlib.util.find_spec("temporalio") is not None,
                           "connectivity": "not_checked" if tool == "temporal" else "local"})
            continue
        checks.append({"layer": layer, "tool": tool, "installed": agents.available(binding, Path(project["repo"])),
                       "authentication": "not_checked", "runtime": "ergora-agent-invocation",
                       "supported": tool != "mini-swe-agent" or sys.platform == "linux",
                       "platform_note": "Requires Linux/bash; use WSL2" if tool == "mini-swe-agent" and sys.platform != "linux" else ""})
    return {"project": project_id, "checks": checks,
            "reference_runtime": "default agentflow unchanged; opt in with ergora reference executor for new tasks" if sys.platform == "linux" else "Formal reference execution requires Linux; use WSL2"}


def run_agent(state: State, project_id: str, role: str, prompt: str, timeout: int = 300,
              skill_names: list[str] | None = None, recall: str | None = None,
              template: str | None = None) -> dict:
    if role not in agents.ROLE_CAPABILITIES:
        raise ValueError(f"Unknown agent role: {role}")
    if not prompt.strip() or not 1 <= timeout <= 3600:
        raise ValueError("Require a prompt and timeout of 1–3600 seconds")
    project = state.project(project_id)
    context = {"skills": [], "memories": []}
    if skill_names:
        from . import skills

        active = {head["name"]: head for head in skills.versions(state, project_id)["active"]}
        for name in skill_names:
            if name not in active:
                raise ValueError(f"Unknown active skill: {name}")
            bundle = skills.get(state, project_id, active[name]["digest"])
            context["skills"].append({"name": name, "digest": bundle["digest"]})
            prompt += f"\n\nSelected skill {name}; resources: {bundle['path']}\n" + (Path(bundle["path"]) / "SKILL.md").read_text(encoding="utf-8")
    if recall:
        from . import memory

        recalled = memory.search(state, project_id, recall, limit=5)
        context["memories"] = recalled["results"]
        prompt += "\n\nProject observations with provenance (verify their applicability):\n" + json.dumps(recalled, ensure_ascii=False)
    binding = agents.binding_for(project, role)
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
                "context": context, "template": template, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
    with state.connect() as db:
        db.execute("INSERT INTO agent_runs VALUES (?, ?, ?)", (run_id, project_id, json.dumps(document)))
    try:
        document.update(agents.invoke(binding, role, prompt, Path(project["repo"]), state.root / "runs" / run_id, timeout, schema))
    except (OSError, ValueError) as error:
        document.update(status="failed", error=str(error))
    document["finished"] = now()
    with state.connect() as db:
        db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(document), run_id))
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
