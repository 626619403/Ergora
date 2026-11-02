from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import projects, reference, registrations
from ergora.state import State


@pytest.fixture(scope="module")
def installation(tmp_path_factory):
    root = tmp_path_factory.mktemp("reference-installation")
    for part in ("local", "upstream/platform"):
        shutil.copytree(reference.ROOT / "platform" / part, root / part)
    return root


@pytest.fixture
def registration(tmp_path, installation):
    repo = tmp_path / "repo"
    repo.mkdir()
    environment = dict(os.environ, GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.test",
                       GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.test")
    for argv in (["init"], ["-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "baseline"]):
        subprocess.run(["git", "-C", str(repo), *argv], check=True, capture_output=True, env=environment)
    definition = {"schema_version": 1, "id": "demo", "repo": str(repo), "templates": list(reference.TEMPLATES),
        "execution": {"installation": str(installation), "config_directory": str(tmp_path / "config"),
                      "state_directory": str(tmp_path / "runtime")},
        "tracker": {"kind": "local", "project": "local/demo"}, "allowed_paths": ["src"],
        "checks": {key: [sys.executable, "-c", "pass"] for key in
                   ("behavior", "architecture", "knowledge", "integration", "compatibility", "migration-rollback")},
        "scope_policy": {"schema_version": 1, "protected_paths": [".git"], "max_changed_files": 20}}
    return State(tmp_path / "control"), definition


def test_registration_publishes_three_templates_and_readonly_effective_view(registration):
    state, definition = registration
    project = registrations.register(state, definition, 0)
    assert project["revision"] == 1 and project["registration"]["status"] == "published"
    assert project["bindings"] == projects.new_document("demo", Path(definition["repo"]))["bindings"]
    assert registrations.status(State(state.root), "demo")["consistent"]
    config = Path(definition["execution"]["config_directory"])
    assert json.loads((config / "policies/demo/execution.json").read_text())["allowed_task_types"] == ["large-change", "repository-governance"]
    assert not Path(definition["execution"]["state_directory"]).exists()
    view = projects.effective_configuration(project)
    assert view["scope"] == "registered-project" and view["registration"]["status"] == "published"
    assert view["registration"]["definition"]["base_sha"]
    assert "files" not in view["registration"]
    projects.bind(state, "demo", "memory", {"tool": "sqlite"}, 1)
    assert registrations.resume(state, "demo", 2)["revision"] == 2


@pytest.mark.parametrize("mutation,error", [
    (lambda d: d.update(schema_version=True), "schema_version"),
    (lambda d: d.update(unknown=True), "Additional properties"),
    (lambda d: d.update(allowed_paths=["src/../escape"]), "Unsafe path"),
    (lambda d: d.update(allowed_paths=[".git"]), "reserved"),
    (lambda d: d["scope_policy"].update(max_changed_files=True), "max_changed_files"),
    (lambda d: d["checks"].pop("behavior"), "Missing trusted checks"),
    (lambda d: d["checks"].update(behavior=["invalid\0argument"]), "behavior"),
    (lambda d: d.update(bindings={"inspector": {"tool": "command", "argv": ["echo"]}}), "stage-json-v1"),
    (lambda d: d.update(bindings={"reviewer": {"tool": "command", "argv": ["echo"], "protocol": "stage-json-v1", "capabilities": []}}), "capabilities"),
    (lambda d: d["tracker"].update(project="local/../demo"), "traversal"),
    (lambda d: d["tracker"].update(kind="github", project="group/sub/demo"), "owner/repository"),
    (lambda d: d["execution"].update(config_directory=d["repo"]), "outside"),
    (lambda d: d["execution"].update(state_directory="relative"), "absolute"),
    (lambda d: d.update(base_sha="0" * 40), "baseline"),
])
def test_invalid_registration_has_no_control_project_or_published_files(registration, mutation, error):
    state, definition = registration
    mutation(definition)
    with pytest.raises(ValueError, match=error):
        registrations.register(state, definition, 0)
    assert projects.list_projects(state) == []
    assert not (Path(definition["execution"]["config_directory"]) / "projects/demo.json").exists()


def test_existing_project_keeps_bindings_and_rejects_stale_or_different_root(registration):
    state, definition = registration
    project = projects.create(state, "demo", Path(definition["repo"]))
    projects.bind(state, "demo", "reviewer", {"tool": "claude-code"}, 1)
    with pytest.raises(ValueError, match="revision changed"):
        registrations.register(state, definition, 1)
    with pytest.raises(ValueError, match="nonnegative integer"):
        registrations.register(state, definition, True)
    registered = registrations.register(state, definition, 2)
    assert registered["created"] == project["created"] and registered["revision"] == 3
    assert registered["bindings"]["reviewer"]["tool"] == "claude-code"
    other = Path(definition["repo"]) / "nested"
    other.mkdir()
    definition["repo"] = str(other)
    with pytest.raises(ValueError, match="repository root"):
        registrations.register(state, definition, 3)


def test_conflicts_legacy_and_duplicate_tracker_never_overwrite(registration):
    state, definition = registration
    config = Path(definition["execution"]["config_directory"])
    (config / "projects").mkdir(parents=True)
    legacy = config / "projects/demo.json"
    legacy.write_text('{"legacy": true}', encoding="utf-8")
    with pytest.raises(ValueError, match="conflict"):
        registrations.register(state, definition, 0)
    assert legacy.read_text() == '{"legacy": true}' and projects.list_projects(state) == []
    legacy.unlink()
    other = config / "projects/other.json"
    other.write_text(json.dumps({"tracker": definition["tracker"]}), encoding="utf-8")
    with pytest.raises(ValueError, match="already owns"):
        registrations.register(state, definition, 0)
    assert not legacy.exists()


@pytest.mark.parametrize("published_files", [0, 1, 2, 3, 4])
def test_interrupted_publication_resumes_saved_intent_in_new_process(registration, monkeypatch, published_files):
    state, definition = registration
    original = reference.registration_io

    def interrupt(execution, project_id, **kwargs):
        if kwargs.get("publish"):
            for path in reference.registration_paths(project_id)[:published_files]:
                target = Path(execution["config_directory"]) / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(kwargs["files"][path]), encoding="utf-8")
            raise OSError("simulated process loss")
        return original(execution, project_id, **kwargs)

    monkeypatch.setattr(reference, "registration_io", interrupt)
    with pytest.raises(OSError, match="process loss"):
        registrations.register(state, definition, 0)
    pending = State(state.root).project("demo")
    assert pending["registration"]["status"] == "pending"
    with pytest.raises(ValueError, match="pending"):
        projects.bind(state, "demo", "memory", {"tool": "sqlite"}, 1)
    definition["checks"]["behavior"] = ["cannot-replace-intent"]
    with pytest.raises(ValueError, match="pending"):
        registrations.register(state, definition, 1)
    result = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "project",
                             "resume-registration", "demo", "--revision", "1"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    project = json.loads(result.stdout)
    assert project["registration"]["status"] == "published" and project["revision"] == 1
    assert project["registration"]["definition"]["checks"]["behavior"] != ["cannot-replace-intent"]
    monkeypatch.setattr(reference, "registration_io", original)
    assert registrations.status(State(state.root), "demo")["consistent"]


def test_completion_record_failure_and_drift_remain_visible_and_recoverable(registration, monkeypatch):
    state, definition = registration
    original = registrations._record

    def interrupt(path, value):
        if path.name.endswith(".result.json"):
            raise OSError("completion record failed")
        return original(path, value)

    monkeypatch.setattr(registrations, "_record", interrupt)
    with pytest.raises(OSError, match="completion record"):
        registrations.register(state, definition, 0)
    assert state.project("demo")["registration"]["status"] == "published"
    monkeypatch.setattr(registrations, "_record", original)
    registrations.resume(State(state.root), "demo", 1)
    path = Path(definition["execution"]["config_directory"]) / "policies/demo/scope.json"
    raw = '{"drift": true}'
    path.write_text(raw, encoding="utf-8")
    assert registrations.status(state, "demo")["files"]["policies/demo/scope.json"] == "differs"
    with pytest.raises(ValueError, match="conflict"):
        registrations.resume(state, "demo", 1)
    assert path.read_text() == raw


def test_existing_equivalent_legacy_files_require_explicit_import(registration):
    state, definition = registration
    prepared = registrations._prepare(state, definition, None)
    files = prepared["registration"]["files"]
    for relative in reference.registration_paths("demo")[1:]:
        path = Path(definition["execution"]["config_directory"]) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(files[relative], indent=4), encoding="utf-8")
    with pytest.raises(ValueError, match="explicitly import"):
        registrations.register(state, definition, 0)
    assert projects.list_projects(state) == []


def test_registration_cannot_publish_files_larger_than_its_reader_limit(registration):
    state, definition = registration
    definition["checks"]["unused"] = ["echo", "x" * 1_048_576]
    with pytest.raises(ValueError, match="1 MiB read limit"):
        registrations.register(state, definition, 0)
    assert projects.list_projects(state) == []
    assert not (Path(definition["execution"]["config_directory"]) / "projects/demo.json").exists()


def test_recovery_intent_failure_leaves_database_unreserved(registration, monkeypatch):
    state, definition = registration

    def interrupt(*args):
        raise OSError("intent record unavailable")

    monkeypatch.setattr(registrations, "_record", interrupt)
    with pytest.raises(OSError, match="intent record"):
        registrations.register(state, definition, 0)
    assert projects.list_projects(state) == []


def test_registration_rejects_another_git_root_unborn_and_symlink_projection(registration, tmp_path):
    state, definition = registration
    unborn = tmp_path / "unborn"
    unborn.mkdir()
    subprocess.run(["git", "-C", str(unborn), "init"], check=True, capture_output=True)
    other = deepcopy(definition)
    other["repo"] = str(unborn)
    with pytest.raises(ValueError, match="baseline"):
        registrations.register(state, other, 0)
    projects.create(state, "demo", unborn)
    with pytest.raises(ValueError, match="same Git repository"):
        registrations.register(state, definition, 1)
    # A different control does not follow a policy directory symlink.
    config = Path(definition["execution"]["config_directory"])
    config.mkdir()
    target = tmp_path / "outside"
    target.mkdir()
    try:
        (config / "policies").symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symlinks requires Windows developer mode / permission")
    with pytest.raises(ValueError, match="Symlinks|escapes"):
        registrations.register(State(tmp_path / "other-control"), definition, 0)


def test_cli_and_api_register_equivalent_projects_and_reject_coerced_revisions(registration, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    state, definition = registration
    path = tmp_path / "definition.json"
    path.write_text(json.dumps(definition), encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "project", "register",
                             str(path), "--revision", "0"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    cli = json.loads(result.stdout)
    # Independent controls receive the same input after removing the first fixture publication.
    shutil.rmtree(definition["execution"]["config_directory"])
    with TestClient(create_app(tmp_path / "api-control"), base_url="http://127.0.0.1:8977") as client:
        headers = {"Origin": "http://127.0.0.1:8977", "X-Ergora-Request": "1"}
        for revision in (True, "0", -1):
            response = client.post("/api/project-registrations", json={"definition": definition, "revision": revision}, headers=headers)
            assert response.status_code == 422
        response = client.post("/api/project-registrations", json={"definition": definition, "revision": 0}, headers=headers)
        assert response.status_code == 200, response.text
        api = response.json()
        assert projects.effective_configuration(api) == projects.effective_configuration(cli)
        assert api["bindings"] == cli["bindings"]
        assert client.get("/api/projects/demo/registration").json()["consistent"]
        response = client.post("/api/projects/demo/registration/resume", json={"revision": 1}, headers=headers)
        assert response.status_code == 200


@pytest.fixture
def legacy_registration(registration):
    state, definition = registration
    baseline = subprocess.check_output(["git", "-C", definition["repo"], "rev-parse", "HEAD"], text=True).strip()
    project = {"schema_version": 1, "name": "demo", "repo": definition["repo"], "base_sha": baseline,
               **{key: definition[key] for key in ("tracker", "allowed_paths", "checks")}}
    sources = {"projects/demo.json": project, "policies/demo/scope.json": definition["scope_policy"]}
    raw = {}
    for relative, document in sources.items():
        path = Path(definition["execution"]["config_directory"]) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw[relative] = (json.dumps(document, indent=4) + "\r\n").encode("utf-8")
        path.write_bytes(raw[relative])
    specification = {key: deepcopy(definition[key]) for key in ("schema_version", "id", "repo", "templates", "execution")}
    return state, specification, raw


def test_import_preview_is_stable_and_changes_no_project_or_source_files(legacy_registration):
    state, specification, raw = legacy_registration
    preview = registrations.preview_import(state, specification, 0)
    assert preview == registrations.preview_import(State(state.root), specification, 0)
    assert preview["expected_revision"] == 0 and preview["definition"]["repo"] == specification["repo"]
    assert preview["definition"]["base_sha"]
    assert {item["path"] for item in preview["changes"]} == {"/id", "/repo", "/bindings", "/definition"}
    for relative, value in raw.items():
        assert preview["files"][relative]["operation"] == "adopt"
        assert preview["files"][relative]["source_sha256"] == hashlib.sha256(value).hexdigest()
        assert (Path(specification["execution"]["config_directory"]) / relative).read_bytes() == value
    assert preview["files"]["policies/demo/execution.json"]["operation"] == "create"
    assert projects.list_projects(state) == [] and not (state.root / "registrations").exists()
    assert not (Path(specification["execution"]["config_directory"]) / "ergora").exists()


def test_import_preserves_legacy_bytes_tasks_and_compatible_policy_order(legacy_registration):
    state, specification, raw = legacy_registration
    config = Path(specification["execution"]["config_directory"])
    # Membership is the policy meaning; adoption keeps this original order and bytes.
    relative = "policies/demo/execution.json"
    raw[relative] = b'{"allowed_task_types": ["repository-governance", "large-change"]}\r\n'
    (config / relative).write_bytes(raw[relative])
    (config / "credentials.json").write_bytes(b"must not parse this secret fixture")
    (config / "platform.json").write_bytes(b"must not parse service settings")
    task = Path(specification["execution"]["state_directory"]) / "tasks/old-task/task.spec.json"
    task.parent.mkdir(parents=True)
    task.write_bytes(b"existing task must stay unchanged")
    preview = registrations.preview_import(state, specification, 0)
    project = registrations.apply_import(state, specification, 0, preview["preview_sha256"])
    assert project["registration"]["status"] == "published"
    assert project["registration"]["sha256"] == preview["registration_sha256"]
    for relative, value in raw.items():
        assert (config / relative).read_bytes() == value
    assert task.read_bytes() == b"existing task must stay unchanged"
    assert registrations.status(state, "demo")["consistent"]
    journal = state.root / "registrations/demo" / (project["registration"]["operation_id"] + ".json")
    record = json.loads(journal.read_text())
    assert record["source"]["preview_sha256"] == preview["preview_sha256"]
    assert record["source"]["files"] == preview["files"] and record["before"] is None
    assert record["after"]["registration"]["status"] == "pending"
    # Later unchanged registration uses the already-approved materialization.
    updated = registrations.register(state, preview["definition"], 1)
    assert updated["revision"] == 2
    assert (config / "policies/demo/execution.json").read_bytes() == raw["policies/demo/execution.json"]


def test_import_adopts_bounded_raw_json_even_when_its_pretty_encoding_is_larger(legacy_registration):
    state, specification, _ = legacy_registration
    path = Path(specification["execution"]["config_directory"]) / "projects/demo.json"
    document = json.loads(path.read_bytes())
    document["checks"]["unused"] = ["echo", *(["x"] * 110_000)]
    raw = json.dumps(document, separators=(",", ":")).encode("utf-8")
    pretty = (json.dumps(document, indent=2) + "\n").encode("utf-8")
    assert len(raw) <= 1_048_576 < len(pretty)
    path.write_bytes(raw)
    preview = registrations.preview_import(state, specification, 0)
    project = registrations.apply_import(state, specification, 0, preview["preview_sha256"])
    assert project["registration"]["status"] == "published" and path.read_bytes() == raw
    assert registrations.resume(state, "demo", 1) == project
    assert registrations.status(state, "demo")["consistent"]


def test_import_upgrades_control_project_with_pointer_diff_and_before_record(legacy_registration):
    state, specification, _ = legacy_registration
    projects.create(state, "demo", Path(specification["repo"]))
    before = projects.bind(state, "demo", "reviewer", {"tool": "claude-code"}, 1)
    specification["bindings"] = {"reviewer": {"tool": "codex"}}
    preview = registrations.preview_import(state, specification, 2)
    assert {"path": "/bindings/reviewer/tool", "operation": "replace", "before": "claude-code", "after": "codex"} in preview["changes"]
    project = registrations.apply_import(state, specification, 2, preview["preview_sha256"])
    assert project["created"] == before["created"] and project["revision"] == 3
    journal = state.root / "registrations/demo" / (project["registration"]["operation_id"] + ".json")
    assert json.loads(journal.read_text())["before"] == before


@pytest.mark.parametrize("source,change", [
    ("projects/demo.json", "format"), ("policies/demo/scope.json", "format"),
    ("projects/demo.json", "semantic"), ("policies/demo/execution.json", "create"),
])
def test_import_refuses_any_source_change_since_preview(legacy_registration, source, change):
    state, specification, _ = legacy_registration
    preview = registrations.preview_import(state, specification, 0)
    path = Path(specification["execution"]["config_directory"]) / source
    if change == "format":
        path.write_bytes(path.read_bytes() + b"\n")
    elif change == "semantic":
        document = json.loads(path.read_bytes())
        document["checks"]["behavior"] = ["new-command"]
        path.write_text(json.dumps(document), encoding="utf-8")
    else:
        path.write_text('{"allowed_task_types": ["large-change", "repository-governance"]}', encoding="utf-8")
    changed = path.read_bytes()
    with pytest.raises(ValueError, match="preview changed"):
        registrations.apply_import(state, specification, 0, preview["preview_sha256"])
    assert projects.list_projects(state) == [] and path.read_bytes() == changed
    assert not (state.root / "registrations").exists()


@pytest.mark.parametrize("mutation,error", [
    (lambda d: d.update(schema_version=True), "schema_version"),
    (lambda d: d.update(schema_version=2), "schema_version"),
    (lambda d: d.update(extra="unknown"), "Additional properties"),
])
def test_import_rejects_unknown_legacy_project_formats(legacy_registration, mutation, error):
    state, specification, _ = legacy_registration
    path = Path(specification["execution"]["config_directory"]) / "projects/demo.json"
    document = json.loads(path.read_bytes())
    mutation(document)
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        registrations.preview_import(state, specification, 0)
    assert projects.list_projects(state) == []


@pytest.mark.parametrize("encoding", ["utf-8-sig", "utf-16"])
def test_import_refuses_source_encodings_the_original_executor_cannot_read(legacy_registration, encoding):
    state, specification, raw = legacy_registration
    path = Path(specification["execution"]["config_directory"]) / "projects/demo.json"
    path.write_bytes(raw["projects/demo.json"].decode("utf-8").encode(encoding))
    with pytest.raises(ValueError):
        registrations.preview_import(state, specification, 0)
    assert projects.list_projects(state) == []


def test_import_refuses_wrong_roots_missing_scope_duplicate_tracker_and_control_owner(legacy_registration, tmp_path):
    state, specification, raw = legacy_registration
    config = Path(specification["execution"]["config_directory"])
    wrong = deepcopy(specification)
    wrong["repo"] = str(tmp_path / "other-repo")
    with pytest.raises(ValueError, match="same ID and Git repository"):
        registrations.preview_import(state, wrong, 0)
    scope = config / "policies/demo/scope.json"
    scope.unlink()
    with pytest.raises(ValueError, match="requires both"):
        registrations.preview_import(state, specification, 0)
    scope.write_bytes(raw["policies/demo/scope.json"])
    other = config / "projects/other.json"
    other.write_bytes(raw["projects/demo.json"])
    with pytest.raises(ValueError, match="already owns"):
        registrations.preview_import(state, specification, 0)
    other.unlink()
    marker = config / "ergora/registrations/demo.json"
    marker.parent.mkdir(parents=True)
    marker.write_text('{"control_home": "another-control"}', encoding="utf-8")
    with pytest.raises(ValueError, match="control owner"):
        registrations.preview_import(state, specification, 0)
    assert projects.list_projects(state) == [] and marker.exists()


def test_import_refuses_revision_changes_or_an_unapproved_preview(legacy_registration):
    state, specification, _ = legacy_registration
    projects.create(state, "demo", Path(specification["repo"]))
    preview = registrations.preview_import(state, specification, 1)
    projects.bind(state, "demo", "reviewer", {"tool": "claude-code"}, 1)
    with pytest.raises(ValueError, match="revision changed"):
        registrations.apply_import(state, specification, 1, preview["preview_sha256"])
    with pytest.raises(ValueError, match="preview changed"):
        registrations.apply_import(state, specification, 2, preview["preview_sha256"])
    assert "registration" not in state.project("demo")


def test_preview_binds_the_control_owner_and_requires_matching_policy_membership(legacy_registration, tmp_path):
    state, specification, _ = legacy_registration
    preview = registrations.preview_import(state, specification, 0)
    assert preview["control_home"] == str(state.root)
    other = State(tmp_path / "other-control")
    with pytest.raises(ValueError, match="preview changed"):
        registrations.apply_import(other, specification, 0, preview["preview_sha256"])
    path = Path(specification["execution"]["config_directory"]) / "policies/demo/execution.json"
    path.write_text('{"allowed_task_types": ["repository-governance"]}', encoding="utf-8")
    with pytest.raises(ValueError, match="conflict with the legacy execution policy"):
        registrations.preview_import(state, specification, 0)


@pytest.mark.parametrize("template", reference.TEMPLATES)
def test_each_template_can_adopt_legacy_configuration(legacy_registration, template):
    state, specification, _ = legacy_registration
    specification["templates"] = [template]
    preview = registrations.preview_import(state, specification, 0)
    project = registrations.apply_import(state, specification, 0, preview["preview_sha256"])
    assert project["registration"]["definition"]["templates"] == [template]
    assert registrations.status(state, "demo")["consistent"]


def test_interrupted_import_resumes_in_new_process_and_preserves_source_identity(legacy_registration, monkeypatch):
    state, specification, raw = legacy_registration
    preview = registrations.preview_import(state, specification, 0)
    original = reference.registration_io

    def interrupt(*args, **kwargs):
        if kwargs.get("publish"):
            raise OSError("interrupted legacy adoption")
        return original(*args, **kwargs)

    monkeypatch.setattr(reference, "registration_io", interrupt)
    with pytest.raises(OSError, match="interrupted"):
        registrations.apply_import(state, specification, 0, preview["preview_sha256"])
    assert state.project("demo")["registration"]["status"] == "pending"
    result = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "project",
                             "resume-registration", "demo", "--revision", "1"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["registration"]["status"] == "published"
    for relative, value in raw.items():
        assert (Path(specification["execution"]["config_directory"]) / relative).read_bytes() == value


def test_import_detects_source_change_after_reservation_and_can_resume_after_restoration(legacy_registration, monkeypatch):
    state, specification, raw = legacy_registration
    preview = registrations.preview_import(state, specification, 0)
    path = Path(specification["execution"]["config_directory"]) / "projects/demo.json"
    original = registrations._reserve

    def change_after_reservation(*args):
        original(*args)
        path.write_bytes(path.read_bytes() + b"\n")

    monkeypatch.setattr(registrations, "_reserve", change_after_reservation)
    with pytest.raises(ValueError, match="source bytes changed"):
        registrations.apply_import(state, specification, 0, preview["preview_sha256"])
    assert state.project("demo")["registration"]["status"] == "pending"
    with pytest.raises(ValueError, match="source bytes changed"):
        registrations.resume(State(state.root), "demo", 1)
    path.write_bytes(raw["projects/demo.json"])
    assert registrations.resume(State(state.root), "demo", 1)["registration"]["status"] == "published"


def test_cli_api_import_preview_agree_and_only_explicit_approved_apply_writes(legacy_registration, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    state, specification, _ = legacy_registration
    path = tmp_path / "import.json"
    path.write_text(json.dumps(specification), encoding="utf-8")
    argv = [sys.executable, "-m", "ergora", "--home", str(state.root), "project", "import-reference", str(path), "--revision", "0"]
    cli = subprocess.run(argv, capture_output=True, text=True)
    assert cli.returncode == 0, cli.stderr
    preview = json.loads(cli.stdout)
    assert projects.list_projects(state) == []
    refused = subprocess.run([*argv, "--apply"], capture_output=True, text=True)
    assert refused.returncode == 2 and "requires --preview-sha256" in refused.stderr
    with TestClient(create_app(state.root), base_url="http://127.0.0.1:8977") as client:
        headers = {"Origin": "http://127.0.0.1:8977", "X-Ergora-Request": "1"}
        body = {"definition": specification, "revision": 0}
        response = client.post("/api/project-registration-imports/preview", json=body, headers=headers)
        assert response.status_code == 200 and response.json() == preview
        assert client.post("/api/project-registration-imports", json=body, headers=headers).status_code == 422
        response = client.post("/api/project-registration-imports", json={**body, "preview_sha256": preview["preview_sha256"]}, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["registration"]["status"] == "published"
