"""Unified project registration and recoverable, one-way reference publication."""

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import uuid

from . import agents, components, contracts, projects, reference
from .bindings import validate_binding
from .asset_trees import is_link
from .definition_bundles import parse_json
from .state import State, file_lock


_SCHEMA = json.loads((Path(__file__).parent / "data/schemas/project-registration-v1.json").read_text(encoding="utf-8"))
_IMPORT_FIELDS = ("schema_version", "id", "repo", "templates", "execution", "bindings")
_IMPORT_SCHEMA = {"type": "object", "additionalProperties": False,
                  "required": list(_IMPORT_FIELDS[:-1]),
                  "properties": {key: _SCHEMA["properties"][key] for key in _IMPORT_FIELDS}}
_LEGACY_FIELDS = ("schema_version", "repo", "tracker", "base_sha", "allowed_paths", "checks")
_LEGACY_PROJECT_SCHEMA = {"type": "object", "additionalProperties": False,
                          "required": ["name", *_LEGACY_FIELDS],
                          "properties": {"name": _SCHEMA["properties"]["id"],
                                         **{key: _SCHEMA["properties"][key] for key in _LEGACY_FIELDS}}}
MAX_RECOVERY_BYTES = 32 * 1_048_576


def _execution_directories(execution: dict, repo: Path) -> dict:
    normalized = {}
    for key, value in execution.items():
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise ValueError("Execution directories must be absolute paths")
        path = path.resolve()
        if path.is_relative_to(repo):
            raise ValueError("Execution directories must be outside the business Git repository")
        normalized[key] = str(path)
    return normalized


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


def publication_files(project: dict, definition: dict, control_home: str | Path, digest: str) -> dict:
    """Project a registration's four native documents without reading or publishing."""
    marker, scope, policy, config = reference.registration_paths(project["id"])
    return {
        marker: {"schema_version": 1, "id": project["id"], "control_home": str(control_home), "definition_sha256": digest},
        scope: definition["scope_policy"],
        policy: {"allowed_task_types": [t for t in definition["templates"] if t != "training-optimization"]},
        config: {"schema_version": 1, "name": project["id"], "repo": project["repo"],
                 **{key: definition[key] for key in ("tracker", "base_sha", "allowed_paths", "checks")}},
    }


def _recovery_document(root: Path, relative: Path, limit: int) -> dict:
    path = root / relative
    for selected in (path, *path.parents):
        if selected == root:
            break
        if is_link(selected):
            raise ValueError("Registration recovery records cannot use symlinks or reparse points")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Registration recovery requires ordinary files")
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f"Registration recovery record exceeds {limit // 1_048_576} MiB; nothing was truncated")
    value = parse_json(raw.decode('utf-8'), 'registration recovery record', finite=True)
    if not isinstance(value, dict):
        raise ValueError("Registration recovery record must be a JSON object")
    return value


def published_project(control_home: str | Path, project_id: str, operation_id: str, intent_sha256: str) -> dict:
    """Read one original published journal from this home; never consult native current files."""
    if (not isinstance(project_id, str) or re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', project_id) is None
            or not isinstance(operation_id, str) or re.fullmatch('[a-f0-9]{32}', operation_id) is None
            or not isinstance(intent_sha256, str) or re.fullmatch('[a-f0-9]{64}', intent_sha256) is None):
        raise ValueError("Original registration requires the project ID, operation ID and complete intent SHA-256")
    root = Path(control_home)
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError("Original registration must retain its canonical control directory")
    relative = Path('registrations') / project_id / operation_id
    record = _recovery_document(root, relative.with_suffix('.json'), MAX_RECOVERY_BYTES)
    result = _recovery_document(root, relative.with_suffix('.result.json'), 1_048_576)
    try:
        project = record['after']
        registration = project['registration']
        definition = registration['definition']
        digest = _sha({'id': project_id, 'repo': project['repo'], 'definition': definition})
        if (set(record) != {'schema_version', 'source', 'before', 'after'}
                or type(record['schema_version']) is not int or record['schema_version'] != 1
                or record['source']['kind'] not in ('registration', 'reference-import')
                or type(project['schema_version']) is not int or project['schema_version'] != 1
                or project['id'] != project_id or type(project['revision']) is not int or project['revision'] < 1
                or type(registration['schema_version']) is not int or registration['schema_version'] != 1
                or registration['status'] != 'pending' or registration['operation_id'] != operation_id
                or registration['sha256'] != digest or _sha(record) != intent_sha256
                or _sha(result) != _sha({'schema_version': 1, 'status': 'published', 'operation_id': operation_id,
                                        'intent_sha256': intent_sha256, 'registration_sha256': digest})):
            raise ValueError("Original registration has no matching complete published intent and result")
        contracts.validate({'schema_version': 1, 'id': project_id, 'repo': project['repo'], **definition},
                           _SCHEMA, 'Original project registration')
        if Path(project['repo']).resolve() != Path(project['repo']) or not Path(project['repo']).is_absolute():
            raise ValueError("Original repository must retain its registered canonical path")
        for value in definition['execution'].values():
            path = Path(value)
            if not path.is_absolute() or path.resolve() != path or path.is_relative_to(project['repo']):
                raise ValueError("Original execution must retain its registered canonical paths outside the repository")
        expected = publication_files(project, definition, root, digest)
        policy_path = reference.registration_paths(project_id)[2]
        policy = registration['files'][policy_path]
        normalized = {**registration['files'], policy_path: {**policy, 'allowed_task_types': sorted(policy['allowed_task_types'])}}
        if normalized != expected:
            raise ValueError("Original registration documents differ from their published definition or control directory")
    except (KeyError, TypeError) as error:
        raise ValueError("Original registration lacks its complete published project") from error
    project = deepcopy(project)
    project['registration']['status'] = 'published'
    return project


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
            agents.validate_binding(role, binding, formal=template != "training-optimization")
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
    execution = _execution_directories(selected["execution"], Path(project["repo"]))
    selected["execution"] = execution
    reference.validate_installation(Path(execution["installation"]))
    result = subprocess.run(["git", "-C", project["repo"], "rev-parse", "--verify",
                             selected.get("base_sha", "HEAD") + "^{commit}"],
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    if result.returncode:
        raise ValueError("Registration requires an existing committed baseline")
    selected["base_sha"] = result.stdout.strip()
    reference.registration_io(execution, project["id"], paths=selected["allowed_paths"], scope=selected["scope_policy"])
    digest = _sha({"id": project["id"], "repo": project["repo"], "definition": selected})
    marker = reference.registration_paths(project["id"])[0]
    files = publication_files(project, selected, state.root, digest)
    if before and "registration" in before:
        previous = before["registration"]
        if previous["sha256"] == digest and previous["files"][marker] == files[marker]:
            # An adopted execution allowlist may have a different, equivalent order.
            files = deepcopy(previous["files"])
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
    source_sha256 = {path: item["source_sha256"] for path, item in record["source"].get("files", {}).items()
                     if item["operation"] == "adopt"}
    reference.registration_io(execution, project["id"], files=registration["files"], publish=True,
                              source_sha256=source_sha256)
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


def _differences(before: dict, after: dict, prefix: str = "") -> list[dict]:
    changes = []
    for key in sorted(before.keys() | after.keys()):
        pointer = prefix + "/" + key.replace("~", "~0").replace("/", "~1")
        if key not in before:
            changes.append({"path": pointer, "operation": "add", "after": after[key]})
        elif key not in after:
            changes.append({"path": pointer, "operation": "remove", "before": before[key]})
        elif isinstance(before[key], dict) and isinstance(after[key], dict):
            changes.extend(_differences(before[key], after[key], pointer))
        elif _sha(before[key]) != _sha(after[key]):
            changes.append({"path": pointer, "operation": "replace", "before": before[key], "after": after[key]})
    return changes


def _import_plan(state: State, specification: dict, expected_revision: int) -> tuple[dict, dict, dict | None]:
    _revision(expected_revision)
    contracts.validate(specification, _IMPORT_SCHEMA, "Reference import")
    before = _current(state, specification["id"])
    if (before["revision"] if before else 0) != expected_revision:
        raise ValueError("Project revision changed; reload before importing")
    if before and before.get("registration", {}).get("status") == "pending":
        raise ValueError("Project registration is pending; resume its existing operation")
    repo = Path(specification["repo"]).expanduser().resolve()
    execution = _execution_directories(specification["execution"], repo)
    observed = reference.registration_io(execution, specification["id"])
    marker, scope_path, policy_path, project_path = reference.registration_paths(specification["id"])
    if observed["files"][marker] is not None:
        raise ValueError("Reference registration already has a control owner; use its status/resume instead of importing")
    if observed["files"][project_path] is None or observed["files"][scope_path] is None:
        raise ValueError("Legacy import requires both the project registration and scope policy")
    legacy = observed["files"][project_path]["document"]
    scope = observed["files"][scope_path]["document"]
    contracts.validate(legacy, _LEGACY_PROJECT_SCHEMA, "Legacy project")
    if legacy["name"] != specification["id"] or Path(legacy["repo"]).expanduser().resolve() != repo:
        raise ValueError("Legacy and expected projects must use the same ID and Git repository")
    definition = {**deepcopy(specification), **{key: legacy[key] for key in ("tracker", "base_sha", "allowed_paths", "checks")},
                  "execution": execution, "scope_policy": scope}
    contracts.validate(definition, _SCHEMA, "Imported project registration")
    project = _prepare(state, definition, before)
    registration = project["registration"]
    existing_policy = observed["files"][policy_path]
    if existing_policy is not None:
        policy = existing_policy["document"]
        contracts.validate(policy, {"type": "object", "additionalProperties": False, "required": ["allowed_task_types"],
            "properties": {"allowed_task_types": {"type": "array", "uniqueItems": True,
                "items": {"enum": [t for t in reference.TEMPLATES if t != "training-optimization"]}}}}, "Legacy execution policy")
        if set(policy["allowed_task_types"]) != set(registration["files"][policy_path]["allowed_task_types"]):
            raise ValueError("Selected templates conflict with the legacy execution policy")
        registration["files"][policy_path] = policy
    reference.registration_io(execution, project["id"], files=registration["files"])
    current = {key: before[key] for key in ("id", "repo", "bindings")} if before else {}
    if before and "registration" in before:
        current["definition"] = before["registration"]["definition"]
    proposed = {key: project[key] for key in ("id", "repo", "bindings")}
    proposed["definition"] = registration["definition"]
    preview = {"schema_version": 1, "kind": "reference-import", "project": project["id"],
               "control_home": str(state.root), "expected_revision": expected_revision, "definition": {
                   "schema_version": 1, "id": project["id"], "repo": project["repo"],
                   **deepcopy(registration["definition"]), "bindings": deepcopy(project["bindings"])},
               "registration_sha256": registration["sha256"], "changes": _differences(current, proposed),
               "files": {path: {"operation": "adopt" if value is not None else "create",
                                "source_sha256": value["sha256"] if value is not None else None,
                                "projected_sha256": _sha(registration["files"][path])}
                         for path, value in observed["files"].items()}}
    preview["preview_sha256"] = _sha(preview)
    return preview, project, before


def preview_import(state: State, specification: dict, expected_revision: int) -> dict:
    """Read a legacy registration and describe adoption without writing project files."""
    return _import_plan(state, specification, expected_revision)[0]


def apply_import(state: State, specification: dict, expected_revision: int, preview_sha256: str) -> dict:
    contracts.validate(specification, _IMPORT_SCHEMA, "Reference import")
    execution = _execution_directories(specification["execution"], Path(specification["repo"]).expanduser().resolve())
    with _publication_lock(state, execution):
        preview, project, before = _import_plan(state, specification, expected_revision)
        if preview_sha256 != preview["preview_sha256"]:
            raise ValueError("Import preview changed; review a new preview before applying")
        _reserve(state, before, project, {"kind": "reference-import", "preview_sha256": preview_sha256,
                                        "files": preview["files"]})
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
