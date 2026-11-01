"""Project memories are canonical here; ReMe is an optional retrieval projection."""

import json
import os
import uuid
from urllib.request import Request, urlopen

from .state import State, file_lock, now


def records(state: State, project_id: str, include_deleted: bool = False) -> list[dict]:
    state.project(project_id)
    with state.connect() as db:
        rows = db.execute("""SELECT document FROM memories m WHERE project=? AND revision=(
            SELECT MAX(revision) FROM memories WHERE project=m.project AND id=m.id) ORDER BY rowid DESC""", (project_id,))
        return [doc for row in rows if (doc := json.loads(row[0]))["status"] == "active" or include_deleted]


def history(state: State, project_id: str, memory_id: str) -> list[dict]:
    state.project(project_id)
    with state.connect() as db:
        result = [json.loads(row[0]) for row in db.execute(
            "SELECT document FROM memories WHERE project=? AND id=? ORDER BY revision", (project_id, memory_id))]
    if not result:
        raise ValueError("Unknown memory in this project")
    return result


def save(state: State, project_id: str, text: str, source: dict, memory_id: str | None = None,
         expected_revision: int = 0) -> dict:
    state.project(project_id)
    if not isinstance(text, str) or not text.strip() or len(text) > 100_000:
        raise ValueError("Memory requires 1–100000 characters")
    if not isinstance(source, dict) or set(source) != {"uri", "revision"} or any(
        not isinstance(source[k], str) or not source[k].strip() for k in ("uri", "revision")
    ):
        raise ValueError("Source must contain nonempty uri and revision strings")
    is_correction = memory_id is not None
    memory_id = memory_id or uuid.uuid4().hex
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        latest = db.execute("SELECT MAX(revision) FROM memories WHERE project=? AND id=?", (project_id, memory_id)).fetchone()[0]
        if is_correction and latest is None:
            raise ValueError("Unknown memory in this project")
        if (latest or 0) != expected_revision:
            raise ValueError("Memory revision changed; reload before saving")
        document = {"project": project_id, "id": memory_id, "revision": expected_revision + 1,
                    "text": text, "source": source, "observed": now(), "status": "active"}
        db.execute("INSERT INTO memories VALUES (?, ?, ?, ?)",
                   (project_id, memory_id, document["revision"], json.dumps(document)))
    return document


def delete(state: State, project_id: str, memory_id: str, expected_revision: int) -> dict:
    state.project(project_id)
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        versions = [json.loads(row[0]) for row in db.execute(
            "SELECT document FROM memories WHERE project=? AND id=? ORDER BY revision", (project_id, memory_id))]
        if not versions:
            raise ValueError("Unknown memory in this project")
        latest = db.execute("SELECT MAX(revision) FROM memories WHERE project=? AND id=?", (project_id, memory_id)).fetchone()[0]
        if latest != expected_revision:
            raise ValueError("Memory revision changed; reload before deleting")
        for version in versions:
            version.update(text="", source={}, status="deleted")
            db.execute("UPDATE memories SET document=? WHERE project=? AND id=? AND revision=?",
                       (json.dumps(version), project_id, memory_id, version["revision"]))
        document = {"project": project_id, "id": memory_id, "revision": latest + 1,
                    "text": "", "source": {}, "observed": now(), "status": "deleted"}
        db.execute("INSERT INTO memories VALUES (?, ?, ?, ?)", (project_id, memory_id, latest + 1, json.dumps(document)))
    return {**document, "remote_deletion": "run memory sync to propagate to any configured ReMe mirrors"}


def restore(state: State, project_id: str, memory_id: str, revision: int, expected_revision: int) -> dict:
    versions = history(state, project_id, memory_id)
    selected = next((v for v in versions if v["revision"] == revision), None)
    if selected is None or selected["status"] != "active":
        raise ValueError("Revision unavailable; deleted content cannot be restored")
    return save(state, project_id, selected["text"], selected["source"], memory_id, expected_revision)


def _job(binding: dict, operation: str, payload: dict) -> dict:
    headers = {"Content-Type": "application/json"}
    if binding.get("token_env"):
        token = os.environ.get(binding["token_env"])
        if not token:
            raise ValueError(f"ReMe credential variable is unavailable: {binding['token_env']}")
        headers["Authorization"] = f"Bearer {token}"
    request = Request(binding["endpoint"].rstrip("/") + "/" + operation,
                      data=json.dumps(payload).encode(), headers=headers)
    with urlopen(request, timeout=15) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError("ReMe response exceeded 2 MB")
    result = json.loads(data)
    if not result["success"]:
        if operation == "delete" and result.get("metadata", {}).get("error") == "not found":
            return result
        raise ValueError(f"ReMe {operation} failed; local canonical memory remains intact")
    return result


def sync(state: State, project_id: str, rebuild: bool = False) -> dict:
    project = state.project(project_id)
    # A per-project file lock spans remote requests, without holding a SQLite write transaction.
    lockdir = state.root / "locks"
    lockdir.mkdir(exist_ok=True)
    with file_lock(lockdir / f"memory-{project_id}.lock"):
        current = {doc["id"]: doc for doc in records(state, project_id, include_deleted=True)}
        binding = project["bindings"].get("memory", {"tool": "sqlite"})
        with state.connect() as db:
            if binding["tool"] == "reme":
                for doc in current.values():
                    if doc["status"] == "deleted":
                        continue
                    db.execute("INSERT OR IGNORE INTO memory_mirrors VALUES (?, ?, ?, 0, ?)",
                               (project_id, binding["endpoint"], doc["id"], json.dumps(binding)))
            mirrors = list(db.execute("SELECT * FROM memory_mirrors WHERE project=?", (project_id,)))
        changed = 0
        for row in mirrors:
            doc = current[row["id"]]
            remote_binding = json.loads(row["binding"])
            if binding["tool"] == "reme" and binding["endpoint"] == row["endpoint"]:
                remote_binding = binding
                with state.connect() as db:
                    db.execute("UPDATE memory_mirrors SET binding=? WHERE project=? AND endpoint=? AND id=?",
                               (json.dumps(binding), project_id, row["endpoint"], doc["id"]))
            path = f"digest/ergora/{project_id}/{doc['id']}.md"
            if doc["status"] == "deleted":
                _job(remote_binding, "delete", {"path": path})
                with state.connect() as db:
                    db.execute("DELETE FROM memory_mirrors WHERE project=? AND endpoint=? AND id=?",
                               (project_id, row["endpoint"], doc["id"]))
                changed += 1
            elif rebuild or row["revision"] != doc["revision"]:
                _job(remote_binding, "write", {"path": path, "name": doc["id"], "content": doc["text"],
                     "metadata": {"ergora_project": project_id, "ergora_revision": doc["revision"], "source": doc["source"]}})
                with state.connect() as db:
                    db.execute("UPDATE memory_mirrors SET revision=?, binding=? WHERE project=? AND endpoint=? AND id=?",
                               (doc["revision"], json.dumps(remote_binding), project_id, row["endpoint"], doc["id"]))
                changed += 1
    return {"project": project_id, "changes_acknowledged": changed, "index_visibility": "eventual; controlled by ReMe watcher"}


def search(state: State, project_id: str, query: str, limit: int = 10) -> dict:
    if not query.strip() or not 1 <= limit <= 100:
        raise ValueError("Require a query and limit of 1–100")
    project = state.project(project_id)
    docs = records(state, project_id)
    binding = project["bindings"].get("memory", {"tool": "sqlite"})
    if binding["tool"] == "sqlite":
        terms = query.casefold().split()
        scored = [(sum(term in doc["text"].casefold() for term in terms), doc) for doc in docs]
        matches = [doc for score, doc in sorted(scored, key=lambda pair: pair[0], reverse=True) if score > 0][:limit]
    else:
        sync(state, project_id)
        by_path = {f"digest/ergora/{project_id}/{doc['id']}.md": doc for doc in records(state, project_id)}
        if not by_path:
            return {"project": project_id, "backend": "reme", "results": []}
        response = _job(binding, "search", {"query": query, "limit": limit, "expand_links": False,
                                          "search_filter": {"paths": list(by_path)}})
        matches = []
        seen = set()
        for hit in response["metadata"]["results"]:
            path = hit["path"]
            if path in by_path and path not in seen:
                matches.append(by_path[path])
                seen.add(path)
    return {"project": project_id, "backend": binding["tool"], "results": matches[:limit]}
