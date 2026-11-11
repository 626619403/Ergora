"""Selected v7 prerequisites share native admission and unknown recovery owners."""

import json
from pathlib import Path
import sys

import pytest

from ergora import agents, projects, tasks
from test_issue_tasks import issue_creation
from test_project_issues import bind, native, source
from test_registrations import installation, registration
from test_task_submission import native_client, _calls, _root
from test_work_agents import work_graph


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal source tasks execute on Linux/WSL2')


@pytest.fixture
def source_submission(issue_creation):
    pytest.importorskip('temporalio')
    source, registered, definition, saved = issue_creation
    state = source.state
    execution = registered['execution']
    config = Path(execution['config_directory'])
    inspector = config / 'selected-inspector'
    inspector.symlink_to(sys.executable)
    binding = {'tool': 'command', 'argv': [sys.executable, '-c', 'pass'],
               'protocol': 'stage-json-v1', 'capabilities': agents.GENERAL_CAPABILITIES}
    for role in ('inspector', 'planner', 'implementer', 'reviewer'):
        selected = binding if role in ('inspector', 'planner') else {**binding, 'argv': ['unselected-missing-program']}
        if role == 'inspector':
            selected = {**binding, 'argv': [str(inspector), '-c', 'pass']}
        projects.bind(state, 'demo', role, selected, state.project('demo')['revision'])
    interpreter = Path(execution['installation']) / '.venv'
    if not interpreter.exists():
        interpreter.symlink_to(sys.prefix, target_is_directory=True)
    program = config / 'selected-codex'
    program.symlink_to(sys.executable)
    (config / 'platform.json').write_text(json.dumps({'execution_enabled': True, 'codex_bin': str(program)}))
    (config / 'codex.toml').write_text('model = "local-program-probe-only"\n')
    revision = state.project('demo')['revision']
    preview = tasks.preview(state, 'demo', definition, revision)
    created = tasks.create(state, 'demo', definition, revision, preview['preview_sha256'])
    return state, registered, definition, created


def test_source_start_ignores_unused_backends_and_broad_doctor(source_submission, native_client):
    state, _, definition, created = source_submission
    revision = state.project('demo')['revision']
    root = _root(source_submission)
    folder = root / 'tasks' / definition['task_id']
    original = {path.name: path.read_bytes() for path in folder.iterdir()}
    started = tasks.start(state, 'demo', definition['task_id'], revision, created['intent_sha256'])
    assert started['status'] == 'submitted' and started['run_id'] == 'original-run'
    assert _calls(source_submission) == ['connect', 'describe', 'start']
    claim = json.loads((folder / 'cli-ingress.json').read_bytes())
    assert claim['owner'] == 'local-cli' and claim['tracker']['issue_id'] == '7'
    assert all((folder / name).read_bytes() == raw for name, raw in original.items())
    assert tasks.resume_start(state, 'demo', definition['task_id'], revision, started['intent_sha256']) == started
    assert _calls(source_submission).count('start') == 1


@pytest.mark.parametrize('failure,match', [
    ('backend', 'work:.*Selected executable is unavailable'),
    ('inspector', 'inventory.*Selected executable is unavailable'),
    ('config', 'inventory|work:'),
    ('disabled', 'automatic-executor.*disabled'),
    ('boundary-blocked', 'execution-boundary.*blocked'),
    ('mcp-missing', 'task-mcp.*requires'),
    ('timeout-missing', 'timeout.*Executable not found'),
])
def test_selected_prerequisite_failure_precedes_connect_claim_and_attempt(source_submission, native_client, monkeypatch, failure, match):
    state, registration, definition, created = source_submission
    config = Path(registration['execution']['config_directory'])
    if failure == 'backend':
        (config / 'selected-codex').unlink()
    elif failure == 'config':
        (config / 'codex.toml').write_text('model = [invalid TOML')
    elif failure == 'disabled':
        settings = json.loads((config / 'platform.json').read_bytes())
        (config / 'platform.json').write_text(json.dumps({**settings, 'execution_enabled': False}))
    elif failure == 'inspector':
        (config / 'selected-inspector').unlink()
    else:
        monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', failure)
    revision = state.project('demo')['revision']
    with pytest.raises(ValueError, match=match):
        tasks.start(state, 'demo', definition['task_id'], revision, created['intent_sha256'])
    status = tasks.submission(state, 'demo', definition['task_id'])
    assert status['status'] == 'prepared' and not status['attempt_saved']
    assert _calls(source_submission) == []
    assert not (_root(source_submission) / 'tasks' / definition['task_id'] / 'cli-ingress.json').exists()


@pytest.mark.parametrize('scenario,match', [('policy-blocked', 'policy denies'), ('foreign-claim', 'Another ingress task owns')])
def test_source_start_keeps_original_policy_and_shared_claim(source_submission, native_client, monkeypatch, scenario, match):
    state, _, definition, created = source_submission
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', scenario)
    with pytest.raises(ValueError, match=match):
        tasks.start(state, 'demo', definition['task_id'], state.project('demo')['revision'], created['intent_sha256'])
    assert tasks.submission(state, 'demo', definition['task_id'])['status'] == 'prepared'
    assert 'start' not in _calls(source_submission)


@pytest.mark.parametrize('drift', [None, 'input', 'memo'])
def test_source_unknown_recovery_uses_original_input_memo_and_never_reprobes(source_submission, native_client, monkeypatch, drift):
    state, registration, definition, created = source_submission
    task_id, revision = definition['task_id'], state.project('demo')['revision']
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'lost-response')
    with pytest.raises(ValueError, match='timed out'):
        tasks.start(state, 'demo', task_id, revision, created['intent_sha256'])
    unknown = tasks.submission(state, 'demo', task_id)
    assert unknown['status'] == 'unknown'
    server = _root(source_submission) / 'sdk-fixture/server.json'
    document = json.loads(server.read_bytes())
    if drift == 'input':
        document['spec']['issue_source']['payload']['observation']['issue']['body'] += 'foreign bytes'
    elif drift == 'memo':
        document['memo'] = {}
    server.write_text(json.dumps(document))
    config = Path(registration['execution']['config_directory'])
    (config / 'selected-codex').unlink()
    (config / 'platform.json').write_text(json.dumps({'execution_enabled': False}))
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'boundary-blocked')
    if drift:
        with pytest.raises(ValueError, match='original task spec differs|matching submission memo'):
            tasks.resume_start(state, 'demo', task_id, revision, unknown['intent_sha256'])
        assert tasks.submission(state, 'demo', task_id)['status'] == 'unknown'
    else:
        recovered = tasks.resume_start(state, 'demo', task_id, revision, unknown['intent_sha256'])
        assert recovered['status'] == 'submitted' and recovered['run_id'] == 'original-run'
    assert _calls(source_submission).count('start') == 1 and 'doctor' not in _calls(source_submission)
