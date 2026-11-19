from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

import ergora.native.registration as native_registration
import ergora.native.resources as native_resources
import ergora
import subprocess
import ergora.configuration.projects as projects
import ergora.configuration.registrations as registrations
import ergora.development.application as tasks
from ergora.storage.state import State


@pytest.fixture(scope="module")
def installation(tmp_path_factory):
    root = tmp_path_factory.mktemp("reference-installation")
    for part in ("local", "upstream/platform"):
        shutil.copytree(native_resources.ROOT / "platform" / part, root / part)
    return root


@pytest.fixture
def registration(tmp_path, installation):
    repo = tmp_path / "repo"
    repo.mkdir()
    environment = dict(os.environ, GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.test",
                       GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.test")
    for argv in (["init"], ["-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "baseline"]):
        subprocess.run(["git", "-C", str(repo), *argv], check=True, capture_output=True, env=environment)
    definition = {"schema_version": 1, "id": "demo", "repo": str(repo), "templates": list(native_resources.TEMPLATES),
        "execution": {"installation": str(installation), "config_directory": str(tmp_path / "config"),
                      "state_directory": str(tmp_path / "runtime")},
        "tracker": {"kind": "local", "project": "local/demo"}, "allowed_paths": ["src"],
        "checks": {key: [sys.executable, "-c", "pass"] for key in
                   ("behavior", "architecture", "knowledge", "integration", "compatibility", "migration-rollback")},
        "scope_policy": {"schema_version": 1, "protected_paths": [".git"], "max_changed_files": 20}}
    return State(tmp_path / "control"), definition


def original_registration(state, project):
    operation = project['registration']['operation_id']
    result = json.loads((state.root / 'registrations' / project['id'] / (operation + '.result.json')).read_bytes())
    return {'operation_id': operation, 'intent_sha256': result['intent_sha256'], 'confirm': True}


def design_policy():
    """Nondefault requirements, not a human identity or executable profile."""
    profile = {'schema_version': 1, 'kind': 'task-design-policy-profile', 'id': 'fixture-policy-v1',
        'protocol': 'design-knowledge-v1', 'change_kinds': ['structural-refactoring', 'ordinary-repair'],
        'required_sections': ['design-and-tradeoffs', 'acceptance'],
        'minimum_questions': [{'id': 'fixture:design', 'body': 'Which interface preserves 完整原文?\r\nCompare its cost.',
                               'why_required': 'The actual owner must choose the interface.'}],
        'minimum_knowledge_requirements': [{'id': 'fixture:contract', 'missing_information': 'Original contract revision',
            'why_needed': 'Compatibility depends on its exact scope.', 'allowed_source_types': ['company_document'],
            'access_scope_ref': 'authorized:fixture',
            'freshness_rule': {'max_age_seconds': 8640, 'required_version': 'contract-r7'}}],
        'required_actor_assurance': 'protected-owner-channel',
        'limits': {'artifact_bytes': 64000, 'inspection_bytes': 256000, 'source_records': 11,
                   'questions': 17, 'knowledge_requirements': 13, 'revisions': 9,
                   'journal_records': 41, 'journal_bytes': 512000}}
    policy = {'schema_version': 1, 'protocol': 'design-knowledge-v1', 'profile': profile,
        'profile_sha256': registrations._sha(profile),
        'owner_source': {'owner_id': 'fixture:owner', 'source_requirement': 'protected-owner-channel'},
        'applicable_task_types': ['repository-governance'], 'change_kinds': ['important-data'],
        'required_sections': ['data-and-recovery'],
        'minimum_questions': [deepcopy(profile['minimum_questions'][0]),
            {'id': 'project:acceptance', 'body': 'Which oracle decides acceptance?', 'why_required': 'A visible outcome is required.'}],
        'minimum_knowledge_requirements': []}
    policy['sha256'] = registrations._sha(policy)
    return policy


def _saved_files(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob('*') if path.is_file()}


@pytest.mark.parametrize('published_files', range(5))
def test_first_v2_real_native_publication_resumes_complete_policy(registration, monkeypatch, published_files):
    state, definition = registration
    definition.update(schema_version=2, design_policy=design_policy())
    policy = deepcopy(definition['design_policy'])
    original_run, original_record = subprocess.run, registrations._record

    def interrupt(argv, **kwargs):
        if 'from ergora.native.registration import _registration_main;_registration_main()' in argv and json.loads(kwargs['input'])['publish']:
            argv = list(argv)
            argv[-1] = '''from ergora.native.registration import _registration_main
from agent_platform import core
original=core.write
count=0
def write(*args, **kwargs):
 global count
 if count == %d: raise OSError('real native publication loss')
 count += 1
 return original(*args, **kwargs)
core.write=write
_registration_main()
''' % published_files
        return original_run(argv, **kwargs)

    def record(path, value):
        if published_files == 4 and path.name.endswith('.result.json'):
            raise OSError('real native publication loss after final file')
        return original_record(path, value)

    monkeypatch.setattr(subprocess, 'run', interrupt)
    monkeypatch.setattr(registrations, '_record', record)
    with pytest.raises((ValueError, OSError), match='real native publication loss'):
        registrations.register(state, definition, 0)
    project = state.project('demo')
    assert project['registration']['schema_version'] == 2
    config = Path(definition['execution']['config_directory'])
    assert sum((config / relative).exists() for relative in native_registration.registration_paths('demo')) == published_files
    journal = state.root / 'registrations/demo' / (project['registration']['operation_id'] + '.json')
    original_intent = journal.read_bytes()
    definition['design_policy']['profile']['minimum_questions'][0]['body'] = 'Cannot replace original intent'
    monkeypatch.undo()
    resumed = subprocess.run([sys.executable, '-m', 'ergora', '--home', str(state.root), 'project',
        'resume-registration', 'demo', '--revision', '1'], capture_output=True, text=True, timeout=30)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    project = json.loads(resumed.stdout)
    status = registrations.status(State(state.root), 'demo')
    assert status['consistent'] and status['registration_schema_version'] == 2
    assert status['design']['policy'] == policy == project['registration']['definition']['design_policy']
    assert status['design']['effective_requirements']['minimum_questions'] == [
        policy['profile']['minimum_questions'][0], policy['minimum_questions'][1]]
    assert status['design']['effective_requirements']['minimum_knowledge_requirements'] == policy['profile']['minimum_knowledge_requirements']
    assert status['design']['execution_supported'] is False
    assert status['design']['actor_assurance'] == {'required': 'protected-owner-channel', 'available': False,
                                                 'code': 'human_channel_unavailable'}
    assert journal.read_bytes() == original_intent
    selected = original_registration(state, project)
    assert registrations.published_project(state.root, 'demo', selected['operation_id'], selected['intent_sha256']) == project
    assert set(project['registration']['files']) == set(native_registration.registration_paths('demo'))
    assert not Path(definition['execution']['state_directory']).exists()


@pytest.mark.parametrize('has_creation', [False, True])
def test_v1_to_v2_is_refused_before_any_intent_reservation_or_native_write(registration, has_creation):
    state, definition = registration
    before = registrations.register(state, definition, 0)
    if has_creation:
        task = {'schema_version': 1, 'task_id': 'original-task', 'task_type': 'repository-governance', 'issue_id': '1',
            'input': {'goal': 'Keep the original task', 'allowed_paths': ['src'], 'acceptance': ['Keep recovery'],
                'constraints': [], 'risk': 'standard',
                'work_units': [{'id': 'one', 'depends_on': [], 'paths': ['src'], 'instructions': 'Inspect source'}]}}
        preview = tasks.preview(state, 'demo', task, 1)
        created = tasks.create(state, 'demo', task, 1, preview['preview_sha256'])
    journals = _saved_files(state.root / 'registrations')
    config = _saved_files(Path(definition['execution']['config_directory']))
    runtime = _saved_files(Path(definition['execution']['state_directory']))
    definition.update(schema_version=2, design_policy=design_policy())
    with pytest.raises(ValueError, match='first unified registration'):
        registrations.register(state, definition, 1)
    assert state.project('demo') == before
    assert _saved_files(state.root / 'registrations') == journals
    assert _saved_files(Path(definition['execution']['config_directory'])) == config
    assert _saved_files(Path(definition['execution']['state_directory'])) == runtime
    if has_creation:
        assert tasks.resume_create(State(state.root), 'demo', task['task_id'], 1, created['intent_sha256']) == created


def test_v2_first_registration_of_control_project_is_immutable_and_not_native_adoption(registration):
    state, definition = registration
    control = projects.create(state, 'demo', Path(definition['repo']))
    definition.update(schema_version=2, design_policy=design_policy())
    project = registrations.register(state, definition, 1)
    assert project['created'] == control['created'] and project['revision'] == 2
    files = _saved_files(state.root / 'registrations')
    for replacement in (definition, {key: value for key, value in definition.items() if key != 'design_policy'}):
        replacement = deepcopy(replacement)
        replacement['schema_version'] = 2 if 'design_policy' in replacement else 1
        with pytest.raises(ValueError, match='first unified registration'):
            registrations.register(state, replacement, 2)
    assert state.project('demo') == project and _saved_files(state.root / 'registrations') == files
    # An existing native ownership marker is not a new registration merely
    # because another control home has no project row.
    other = State(state.root.parent / 'other-control')
    with pytest.raises(ValueError, match='first unified registration'):
        registrations.register(other, definition, 0)
    assert projects.list_projects(other) == [] and not (other.root / 'registrations').exists()


@pytest.mark.parametrize('winner_version,late_version', [(1, 2), (2, 1), (2, 2)])
def test_interleaved_first_registration_at_different_roots_rejects_before_intent(
        registration, monkeypatch, winner_version, late_version):
    state, winner = registration
    late = deepcopy(winner)
    late['execution']['config_directory'] += '-late'
    late['execution']['state_directory'] += '-late'
    for definition, version in ((winner, winner_version), (late, late_version)):
        if version == 2:
            definition.update(schema_version=2, design_policy=design_policy())
    original_prepare = registrations._prepare
    saved = {}

    def prepare(control, definition, before):
        prepared = original_prepare(control, definition, before)
        if definition is late:
            # Both calls saw no project. Finish the competing publication after
            # this real preparation, before the late call takes its own lock.
            saved['project'] = registrations.register(State(state.root), winner, 0)
            saved['journals'] = _saved_files(state.root / 'registrations')
            saved['native'] = _saved_files(Path(winner['execution']['config_directory']))
            with state.connect() as db:
                saved['database'] = tuple(db.iterdump())
        return prepared

    monkeypatch.setattr(registrations, '_prepare', prepare)
    with pytest.raises(ValueError, match='revision changed'):
        registrations.register(state, late, 0)
    assert state.project('demo') == saved['project']
    journals = _saved_files(state.root / 'registrations')
    assert set(journals) == set(saved['journals'])
    assert journals == saved['journals']
    assert _saved_files(Path(winner['execution']['config_directory'])) == saved['native']
    late_config = Path(late['execution']['config_directory'])
    assert not any((late_config / path).exists() for path in native_registration.registration_paths('demo'))
    assert not Path(late['execution']['state_directory']).exists()
    with state.connect() as db:
        assert tuple(db.iterdump()) == saved['database']


@pytest.mark.parametrize('boundary', ['status', 'resume'])
def test_v1_history_keeps_status_and_resume_after_input_schema_tightening(registration, monkeypatch, boundary):
    state, definition = registration
    definition['tracker']['project'] += '\n'
    # 4ffcfdde added this exact input restriction. Replay its predecessor's
    # accepted schema while writing a real journal, then reopen with today's.
    historical_schema = deepcopy(registrations._SCHEMAS[1])
    historical_schema['properties']['tracker']['properties']['project'].pop('not')
    original_io = native_registration.registration_io

    def interrupt(execution, project_id, **kwargs):
        if kwargs.get('publish'):
            raise OSError('historical publication interrupted')
        return original_io(execution, project_id, **kwargs)

    with monkeypatch.context() as historical:
        historical.setitem(registrations._SCHEMAS, 1, historical_schema)
        if boundary == 'resume':
            historical.setattr(native_registration, 'registration_io', interrupt)
            with pytest.raises(OSError, match='historical publication interrupted'):
                registrations.register(state, definition, 0)
            project = state.project('demo')
        else:
            project = registrations.register(state, definition, 0)
    journal = registrations._journal(state, project)
    original_intent = journal.read_bytes()
    if boundary == 'resume':
        project = registrations.resume(State(state.root), 'demo', project['revision'])
    assert registrations.status(State(state.root), 'demo')['consistent']
    assert journal.read_bytes() == original_intent
    assert project['registration']['definition']['tracker'] == definition['tracker']
    selected = original_registration(state, project)
    # The original published-source reader already used today's schema; this
    # compatibility fix does not relax its separate complete-source contract.
    with pytest.raises(ValueError, match='tracker'):
        registrations.published_project(state.root, 'demo', selected['operation_id'], selected['intent_sha256'])


@pytest.mark.parametrize('damage', ['profile-sha', 'policy-sha', 'conflict', 'capacity', 'inspection-profile'])
def test_policy_identity_and_effective_minimum_conflicts_fail_before_registration(registration, damage):
    state, definition = registration
    policy = design_policy()
    if damage == 'profile-sha':
        policy['profile']['minimum_questions'][0]['body'] += ' changed'
    elif damage == 'policy-sha':
        policy['owner_source']['owner_id'] = 'other:owner'
    elif damage == 'conflict':
        policy['minimum_questions'][0]['body'] += ' conflicting'
    elif damage == 'capacity':
        policy['profile']['limits']['questions'] = 1
        policy['profile_sha256'] = registrations._sha(policy['profile'])
    else:
        policy['profile'] = json.loads((Path(ergora.__file__).parent / 'data/design-profiles/framework-development-v1.json').read_bytes())
        policy['profile_sha256'] = registrations._sha(policy['profile'])
    if damage not in ('profile-sha', 'policy-sha'):
        policy['sha256'] = registrations._sha({key: value for key, value in policy.items() if key != 'sha256'})
    definition.update(schema_version=2, design_policy=policy)
    with pytest.raises(ValueError):
        registrations.register(state, definition, 0)
    assert projects.list_projects(state) == [] and not (state.root / 'registrations').exists()


def test_complete_policy_intent_must_fit_its_recovery_read_bound_before_any_write(registration, monkeypatch):
    state, definition = registration
    definition.update(schema_version=2, design_policy=design_policy())
    prepared = registrations._prepare(state, definition, None)
    record = {'schema_version': 1, 'source': {'kind': 'registration'}, 'before': None, 'after': prepared}
    # Exercise the existing recovery cap with small complete material; changing
    # configured policy limits does not change the writer/reader byte contract.
    encoded = json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8')
    monkeypatch.setattr(registrations, 'MAX_RECOVERY_BYTES', len(encoded) // 2)
    with pytest.raises(ValueError, match='Registration recovery record exceeds'):
        registrations.register(state, definition, 0)
    assert projects.list_projects(state) == []
    assert not (state.root / 'registrations').exists() and not (state.root / '.registrations.lock').exists()
    assert not Path(definition['execution']['config_directory']).exists()
    assert not Path(definition['execution']['state_directory']).exists()


def test_original_published_journal_retains_large_aggregate_and_all_revisions(registration):
    state, definition = registration
    definition['checks']['unused'] = ['echo', 'x' * 600_000]
    first = registrations.register(state, definition, 0)
    second = registrations.register(state, definition, first['revision'])
    selected = original_registration(state, second)
    path = state.root / 'registrations/demo' / (selected['operation_id'] + '.json')
    raw = path.read_bytes()
    assert 1_048_576 < len(raw) < registrations.MAX_RECOVERY_BYTES
    projects.bind(state, 'demo', 'memory', {'tool': 'sqlite'}, second['revision'])
    before = {p: p.read_bytes() for p in path.parent.iterdir()}
    assert registrations.published_project(state.root, 'demo', selected['operation_id'], selected['intent_sha256']) == second
    assert state.project('demo')['revision'] > second['revision']
    assert {p: p.read_bytes() for p in path.parent.iterdir()} == before
    # Trailing whitespace keeps the same JSON/canonical identity; the actual
    # aggregate byte bound must still reject it before accepting that identity.
    path.write_bytes(raw + b' ' * (registrations.MAX_RECOVERY_BYTES - len(raw) + 1))
    with pytest.raises(ValueError, match='exceeds .* MiB'):
        registrations.published_project(state.root, 'demo', selected['operation_id'], selected['intent_sha256'])


@pytest.mark.parametrize('damage', ['intent', 'result', 'missing-result', 'projection', 'home', 'duplicate', 'symlink'])
def test_original_registration_requires_its_own_complete_published_source(registration, tmp_path, damage):
    state, definition = registration
    project = registrations.register(state, definition, 0)
    selected = original_registration(state, project)
    journal = state.root / 'registrations/demo' / (selected['operation_id'] + '.json')
    result = journal.with_suffix('.result.json')
    if damage == 'intent':
        selected['intent_sha256'] = '0' * 64
    elif damage == 'result':
        value = json.loads(result.read_bytes());value['registration_sha256'] = '0' * 64
        result.write_text(json.dumps(value))
    elif damage == 'missing-result':
        result.unlink()
    elif damage == 'projection':
        value = json.loads(journal.read_bytes())
        value['after']['registration']['files']['policies/demo/scope.json']['protected_paths'] = ['foreign']
        journal.write_text(json.dumps(value))
        selected['intent_sha256'] = registrations._sha(value)
        value = json.loads(result.read_bytes());value['intent_sha256'] = selected['intent_sha256']
        result.write_text(json.dumps(value))
    elif damage == 'home':
        other = State(tmp_path / 'other-control')
        shutil.copytree(journal.parent, other.root / 'registrations/demo')
        state = other
    elif damage == 'duplicate':
        journal.write_bytes(journal.read_bytes().replace(b'"schema_version": 1,', b'"schema_version": 1, "schema_version": 1,', 1))
    else:
        saved = journal.with_suffix('.saved')
        journal.rename(saved)
        try:
            journal.symlink_to(saved)
        except OSError:
            pytest.skip('Symlink creation unavailable')
    with pytest.raises((ValueError, FileNotFoundError)):
        registrations.published_project(state.root, 'demo', selected['operation_id'], selected['intent_sha256'])


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


def test_training_only_registration_keeps_plain_command_bindings(registration):
    state, definition = registration
    definition["templates"] = ["training-optimization"]
    definition["bindings"] = {"experiment-planner": {"tool": "command", "argv": ["external-tool"]}}
    registered = registrations.register(state, definition, 0)
    assert registered["registration"]["status"] == "published"
    assert registered["bindings"]["experiment-planner"] == definition["bindings"]["experiment-planner"]


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
    pytest.param(lambda d: d["tracker"].update(project="local/demo\n"), "tracker", id="tracker-newline"),
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
    original = native_registration.registration_io

    def interrupt(execution, project_id, **kwargs):
        if kwargs.get("publish"):
            for path in native_registration.registration_paths(project_id)[:published_files]:
                target = Path(execution["config_directory"]) / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(kwargs["files"][path]), encoding="utf-8")
            raise OSError("simulated process loss")
        return original(execution, project_id, **kwargs)

    monkeypatch.setattr(native_registration, "registration_io", interrupt)
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
    monkeypatch.setattr(native_registration, "registration_io", original)
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
    for relative in native_registration.registration_paths("demo")[1:]:
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
    from ergora.interfaces.web import create_app

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
    selected = original_registration(state, project)
    assert registrations.published_project(state.root, 'demo', selected['operation_id'], selected['intent_sha256']) == project
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
    selected = original_registration(state, project)
    assert registrations.published_project(state.root, 'demo', selected['operation_id'], selected['intent_sha256']) == project


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
    pytest.param(lambda d: d["tracker"].update(project="local/demo\n"), "tracker", id="tracker-newline"),
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


@pytest.mark.parametrize("template", native_resources.TEMPLATES)
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
    original = native_registration.registration_io

    def interrupt(*args, **kwargs):
        if kwargs.get("publish"):
            raise OSError("interrupted legacy adoption")
        return original(*args, **kwargs)

    monkeypatch.setattr(native_registration, "registration_io", interrupt)
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
    from ergora.interfaces.web import create_app

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
