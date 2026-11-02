"""Unified project registration and recoverable, one-way reference publication."""

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid

from . import components, contracts, projects, reference
from .bindings import validate_binding
from .state import State, file_lock


_SCHEMA = json.loads((Path(__file__).parent / "data/schemas/project-registration-v1.json").read_text(encoding="utf-8"))


def _sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _revision(value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError("Expected revision must be a nonnegative integer; use 0 for a new project")


def _current(state: State, project_id: str) -> dict | None:
    with state.connect() as db:
        row = db.execute("SELECT document FROM projects WHERE id=?", (project_id,)).fetchone()
    return json.loads(row[0]) if row else None


def _prepare(state: State, definition: dict, before: dict | None) -> dict:
    fresh = projects.new_document(definition["id"], Path(definition["repo"]))
    if before is not None:
        if before["repo"] != fresh["repo"]:
            raise ValueError("Control and registered projects must use the same Git repository")
        if before.get("registration", {}).get("status") == "pending":
            raise ValueError("Project registration is pending; resume its existing operation")
    project = deepcopy(before) if before is not None else fresh
    project["bindings"].update(deepcopy(definition.get("bindings", {})))
    for layer, binding in project["bindings"].items():
        validate_binding(layer, binding)
    selected = deepcopy(definition)
    for key in ("schema_version", "id", "repo", "bindings"):
        selected.pop(key, None)
    selected["templates"] = sorted(selected["templates"])
    for template in selected["templates"]:
        contract = reference.agent_contract(template)
        for role in contract["agents"]:
            binding = components.resolve_binding(project, role)["binding"]
            validate_binding(role, binding)
            if template != "training-optimization" and components.COMPONENTS[binding["tool"]]["implementation"] == "command":
                if binding.get("protocol") != "stage-json-v1":
                    raise ValueError("Formal command agents require stage-json-v1")
        if template != "training-optimization":
            required = set(contract["acceptance"]["required_checks"]) - {"scope", "baseline-regression"}
            missing = required - set(selected["checks"])
            if missing:
                raise ValueError("Missing trusted checks: " + ", ".join(sorted(missing)))
    tracker = selected["tracker"]
    if any(part in (".", "..") for part in tracker["project"].split("/")):
        raise ValueError("Tracker project cannot contain traversal segments")
    if tracker["kind"] == "github" and len(tracker["project"].split("/")) != 2:
        raise ValueError("GitHub tracker requires owner/repository")
    execution = selected["execution"]
    for key, value in execution.items():
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise ValueError("Execution directories must be absolute paths")
        execution[key] = str(path.resolve())
        if Path(execution[key]).is_relative_to(Path(project["repo"])):
            raise ValueError("Execution directories must be outside the business Git repository")
    reference.validate_installation(Path(execution["installation"]))
    result = subprocess.run(["git", "-C", project["repo"], "rev-parse", "--verify",
                             selected.get("base_sha", "HEAD") + "^{commit}"],
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    if result.returncode:
        raise ValueError("Registration requires an existing committed baseline")
    selected["base_sha"] = result.stdout.strip()
    reference.registration_io(execution, project["id"], paths=selected["allowed_paths"], scope=selected["scope_policy"])
    digest = _sha({"id": project["id"], "repo": project["repo"], "definition": selected})
    marker, scope, policy, config = reference.registration_paths(project["id"])
    files = {
        marker: {"schema_version": 1, "id": project["id"], "control_home": str(state.root), "definition_sha256": digest},
        scope: selected["scope_policy"],
        policy: {"allowed_task_types": [t for t in selected["templates"] if t != "training-optimization"]},
        config: {"schema_version": 1, "name": project["id"], "repo": project["repo"],
                 **{key: selected[key] for key in ("tracker", "base_sha", "allowed_paths", "checks")}},
    }
    project["revision"] = before["revision"] + 1 if before else 1
    project["registration"] = {"schema_version": 1, "definition": selected, "sha256": digest,
                               "status": "pending", "operation_id": uuid.uuid4().hex, "files": files}
    return project


@contextmanager
def _publication_lock(state: State, execution: dict):
    config = Path(execution["config_directory"])
    config.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = config / ".ergora-registration.lock"
    if lock.is_symlink():
        raise ValueError("Registration lock must not be a symlink")
    with file_lock(state.root / ".registrations.lock"), file_lock(lock):
        yield


def _record(path: Path, value: dict) -> None:
    """Durable intent precedes the SQLite reservation; retries keep its original bytes."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".pending-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if _sha(json.loads(path.read_text(encoding="utf-8"))) != _sha(value):
                raise ValueError("Registration recovery record conflicts with the saved operation")
    finally:
        Path(temporary).unlink(missing_ok=True)


def _journal(state: State, project: dict) -> Path:
    return state.root / "registrations" / project["id"] / (project["registration"]["operation_id"] + ".json")


def _reserve(state: State, before: dict | None, project: dict, source: dict) -> None:
    _record(_journal(state, project), {"schema_version": 1, "source": source, "before": before, "after": project})
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT document FROM projects WHERE id=?", (project["id"],)).fetchone()
        current = json.loads(row[0]) if row else None
        if current != before:
            raise ValueError("Project revision changed; reload before registering")
        db.execute("INSERT OR REPLACE INTO projects VALUES (?, ?)", (project["id"], json.dumps(project)))


def _finish(state: State, project: dict) -> dict:
    registration = project["registration"]
    journal = _journal(state, project)
    record = json.loads(journal.read_text(encoding="utf-8"))
    if (record["after"]["registration"] != {**registration, "status": "pending"}
            or record["after"]["id"] != project["id"] or record["after"]["repo"] != project["repo"]):
        raise ValueError("Project does not match its saved recovery intent")
    execution = registration["definition"]["execution"]
    reference.validate_installation(Path(execution["installation"]))
    reference.registration_io(execution, project["id"], files=registration["files"], publish=True)
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        current = json.loads(db.execute("SELECT document FROM projects WHERE id=?", (project["id"],)).fetchone()[0])
        if current != project:
            raise ValueError("Project revision changed during publication; reload and resume")
        project = deepcopy(project)
        project["registration"]["status"] = "published"
        db.execute("UPDATE projects SET document=? WHERE id=?", (json.dumps(project), project["id"]))
    _record(journal.with_suffix(".result.json"), {"schema_version": 1, "status": "published",
            "operation_id": registration["operation_id"], "intent_sha256": _sha(record),
            "registration_sha256": registration["sha256"]})
    return project


def register(state: State, definition: dict, expected_revision: int) -> dict:
    _revision(expected_revision)
    contracts.validate(definition, _SCHEMA, "Project registration")
    before = _current(state, definition["id"])
    if (before["revision"] if before else 0) != expected_revision:
        raise ValueError("Project revision changed; reload before registering")
    project = _prepare(state, definition, before)
    registration = project["registration"]
    with _publication_lock(state, registration["definition"]["execution"]):
        observed = reference.registration_io(registration["definition"]["execution"], project["id"], files=registration["files"])
        marker = reference.registration_paths(project["id"])[0]
        if observed["files"][marker] is None and any(value is not None for value in observed["files"].values()):
            raise ValueError("Legacy reference registration detected; preview and explicitly import it")
        _reserve(state, before, project, {"kind": "registration"})
        return _finish(state, project)


def resume(state: State, project_id: str, expected_revision: int) -> dict:
    _revision(expected_revision)
    project = state.project(project_id)
    if project["revision"] != expected_revision:
        raise ValueError("Project revision changed; reload before resuming")
    if "registration" not in project:
        raise ValueError("Project has no saved registration to resume")
    with _publication_lock(state, project["registration"]["definition"]["execution"]):
        return _finish(state, project)


def status(state: State, project_id: str) -> dict:
    project = state.project(project_id)
    if "registration" not in project:
        return {"project": project_id, "revision": project["revision"], "status": "unregistered"}
    registration = project["registration"]
    observed = reference.registration_io(registration["definition"]["execution"], project_id)
    files = {path: "missing" if observed["files"][path] is None else
             "matches" if _sha(observed["files"][path]["document"]) == _sha(value) else "differs"
             for path, value in registration["files"].items()}
    tracker = registration["definition"]["tracker"]
    duplicate_tracker = any(other["tracker"] == tracker for other in observed["other_projects"])
    return {"project": project_id, "revision": project["revision"], "status": registration["status"],
            "sha256": registration["sha256"], "files": files, "duplicate_tracker": duplicate_tracker,
            "consistent": all(value == "matches" for value in files.values()) and not duplicate_tracker,
            "recovery_record": str(_journal(state, project))}
