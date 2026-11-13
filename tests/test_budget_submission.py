"""Budget send gates never turn a lost original start into a new send."""

import json
import os
from pathlib import Path
import sys
import time

import pytest

from ergora import reference_budget, tasks
from test_task_budget import budget_creation, full_creation, full_graph, work_creation, work_graph
from test_registrations import installation, registration
from test_task_creation import creation_project
from test_task_submission import native_client, _calls, _root, _resume, _start, _status


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Budgeted native submission requires Linux/WSL2')


@pytest.fixture
def budget_submission(budget_creation, monkeypatch):
    pytest.importorskip('temporalio')
    pytest.importorskip('mcp')
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=8, cleanup_seconds=2)
    execution = registered['execution']
    interpreter = Path(execution['installation']) / '.venv'
    if not interpreter.exists():
        interpreter.symlink_to(sys.prefix, target_is_directory=True)
    config = Path(execution['config_directory'])
    codex = config / 'selected-codex'
    codex.symlink_to(sys.executable)
    (config / 'claude').symlink_to(sys.executable)
    monkeypatch.setenv('PATH', str(config) + os.pathsep + os.environ.get('PATH', ''))
    (config / 'platform.json').write_text(json.dumps({'execution_enabled': True, 'codex_bin': str(codex)}))
    (config / 'codex.toml').write_text('model = "local-program-probe-only"\n')
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=preview['prepare_sha256'])
    return state, registered, definition, created


@pytest.mark.parametrize('scenario,attempt_saved', [
    ('budget-expire-during-lookup', False), ('budget-slow-attempt', True)])
def test_expiration_before_native_send_does_not_renew_an_attempt(
        budget_submission, native_client, monkeypatch, scenario, attempt_saved):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', scenario)
    with pytest.raises(ValueError, match='budget is exhausted'):
        _start(budget_submission)
    status = _status(budget_submission)
    assert status['attempt_saved'] is attempt_saved and 'start' not in _calls(budget_submission)
    original = list(_calls(budget_submission))
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'normal')
    if attempt_saved:
        resumed = _resume(budget_submission)
        assert resumed['status'] == 'unknown' and resumed['reconciliation'] == 'not_found'
        assert _calls(budget_submission) == [*original, 'connect', 'describe']
    else:
        with pytest.raises(ValueError, match='budget is exhausted'):
            _resume(budget_submission)
        assert _calls(budget_submission) == original


def test_lost_native_start_can_only_lookup_after_original_budget_expires(budget_submission, native_client, monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'lost-response')
    with pytest.raises(ValueError, match='timed out'):
        _start(budget_submission)
    assert _status(budget_submission)['status'] == 'unknown'
    document = json.loads((_root(budget_submission) / 'tasks' / budget_submission[2]['task_id'] / 'task.spec.json').read_bytes())
    time.sleep(max(0, reference_budget.remaining(document['budget']['instance'])) + .1)
    config = Path(budget_submission[1]['execution']['config_directory'])
    (config / 'platform.json').write_text(json.dumps({'execution_enabled': False}))
    (config / 'codex.toml').write_text('invalid TOML [')
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'normal')
    recovered = _resume(budget_submission)
    assert recovered['status'] == 'submitted' and recovered['run_id'] == 'original-run'
    assert _calls(budget_submission).count('start') == 1
    assert _start(budget_submission) == recovered
