"""Independent Agent invocations, frozen context and durable run records."""

import hashlib
import json
from pathlib import Path
import uuid

from . import agents
from .bindings import validate_binding
from .state import State, now


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
