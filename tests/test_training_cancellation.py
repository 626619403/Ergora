"""Cancellation delivery is run-bound and separate from stopping an executor."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path

import pytest

from ergora import reference, training
from test_training_submission import prepared, service
from test_training import experiments, registration
from test_training_runtime import installation


@pytest.fixture
def submitted(prepared, service, monkeypatch):
    state, _, _, _, _, digest = prepared
    _, record = service
    receipt = training.start(state, 'demo', 'alpha', state.project('demo')['revision'], digest)
    original = reference.processes.run
    fixture = Path(__file__).parent / 'fixtures/training_cancellation_client.py'

    def select(scenario):
        def invoke(argv, *args, **kwargs):
            if 'from ergora.reference_training_cancellation import main;main()' in argv:
                argv = list(argv)
                argv[-1] = f'import runpy;runpy.run_path({str(fixture)!r},run_name="__main__")'
                kwargs['env'] = {**kwargs['env'], 'ERGORA_TEST_TRAINING_SUBMISSION': scenario,
                                 'ERGORA_TEST_TRAINING_SERVICE': str(record)}
            return original(argv, *args, **kwargs)
        monkeypatch.setattr(reference.processes, 'run', invoke)
    select('accepted')
    return receipt, select, record


def request(prepared, receipt, reason='CPU acceptance complete', request_id='cancel-one', **kwargs):
    state = prepared[0]
    return training.cancel(state, 'demo', 'alpha', request_id, state.project('demo')['revision'],
                           run_id=receipt['run_id'], reason=reason, **kwargs)


def recover(prepared, intent):
    state = prepared[0]
    return training.resume_cancel(state, 'demo', 'alpha', intent['request_id'], state.project('demo')['revision'],
                                  intent['intent_sha256'])


def test_native_cancel_is_single_run_bound_and_locally_readable_without_sdk(prepared, submitted, monkeypatch):
    state, definition, runtime, _, _, _ = prepared
    receipt, _, record = submitted
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    result = request(prepared, receipt, reason='--operator-stop')
    assert result['status'] == 'requested' and result['signal_delivery'] == 'acknowledged'
    assert result['cancellation_confirmed'] is None and result['execution_success'] is None
    assert request(prepared, receipt, reason='--operator-stop') == recover(prepared, result) == result
    assert json.loads(record.read_bytes())['signals'] == 1
    assert all(p.read_bytes() == raw for p, raw in before.items())
    (runtime / 'training/specs/alpha.json').unlink()
    (Path(definition['execution']['config_directory']) / 'training-runners/trusted.json').unlink()
    original = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    assert training.cancellation(state, 'demo', 'alpha', 'cancel-one') == result


@pytest.mark.parametrize('scenario', ['lost-ack', 'timeout-ack'])
def test_unknown_signal_recovers_original_history_without_resending(prepared, submitted, scenario):
    state, definition, runtime, _, _, _ = prepared
    receipt, select, record = submitted
    select(scenario)
    with pytest.raises(ValueError, match='UNAVAILABLE|timed out'):
        request(prepared, receipt, timeout=1)
    unknown = training.cancellation(state, 'demo', 'alpha', 'cancel-one')
    assert unknown['status'] == 'unknown' and unknown['cancel_requested'] is None
    assert request(prepared, receipt) == unknown
    for absent in ('signal-missing', 'foreign-signal', 'wrong-marker'):
        select(absent)
        result = recover(prepared, unknown)
        assert result['status'] == 'unknown' and result['reconciliation'] == 'signal_not_found'
    select('not-found')
    with pytest.raises(ValueError, match='run was not found'):
        recover(prepared, unknown)
    (runtime / 'training/specs/alpha.json').unlink()
    (Path(definition['execution']['config_directory']) / 'training-runners/trusted.json').unlink()
    select('accepted')
    result = recover(prepared, unknown)
    assert result['status'] == 'requested' and result['signal_delivery'] == 'history' and result['run_id'] == receipt['run_id']
    assert json.loads(record.read_bytes())['signals'] == 1


@pytest.mark.parametrize('scenario,error', [
    ('foreign-memo', 'matching start intent memo'), ('input-collision', 'complete original Experiment differs'),
    ('wrong-run', 'another run ID'), ('status-binding', 'binding differs'),
])
def test_conflicting_runtime_cannot_receive_a_cancel(prepared, submitted, scenario, error):
    state = prepared[0]
    receipt, select, record = submitted
    select(scenario)
    with pytest.raises(ValueError, match=error):
        request(prepared, receipt)
    assert training.cancellation(state, 'demo', 'alpha', 'cancel-one')['status'] == 'prepared'
    assert json.loads(record.read_bytes()).get('signals', 0) == 0


def test_closed_workflow_is_not_reported_as_cancelled_and_stop_facts_remain_separate(prepared, submitted):
    state, _, runtime, _, write, _ = prepared
    receipt, select, record = submitted
    select('closed')
    result = request(prepared, receipt)
    assert result['status'] == 'already_closed' and result['signal_delivery'] == 'not_sent'
    assert result['cancel_requested'] is False and result['cancellation_confirmed'] is None
    spec = json.loads((runtime / 'training/specs/alpha.json').read_bytes())
    write(runtime / 'training/jobs/alpha/request.json', {'experiment': spec, 'job_id': 'local-perf-alpha'})
    write(runtime / 'training/jobs/alpha/result.json', {'binding': spec['binding'], 'job_id': 'local-perf-alpha',
                                                      'state': 'CANCELLED', 'detail': 'Original executor result'})
    write(runtime / 'training/fences/alpha.json', {'binding': spec['binding']})
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    observed = training.stop_status(state, 'demo', 'alpha')
    assert observed['control']['phase'] == 'CANCEL_UNCONFIRMED'
    assert observed['executor_observation']['state'] == 'CANCELLED' and observed['fence_recorded']
    assert observed['execution_success'] is None and observed['read_only'] is True
    assert {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()} == before
    assert json.loads(record.read_bytes()).get('signals', 0) == 0


def test_stop_status_keeps_missing_queued_and_running_executor_facts(prepared, submitted):
    state, _, runtime, _, write, _ = prepared
    observed = training.stop_status(state, 'demo', 'alpha')
    assert observed['executor_observation'] is None and observed['fence_recorded'] is False
    spec = json.loads((runtime / 'training/specs/alpha.json').read_bytes())
    write(runtime / 'training/jobs/alpha/request.json', {'experiment': spec, 'job_id': 'local-perf-alpha'})
    assert training.stop_status(state, 'demo', 'alpha')['executor_observation']['state'] == 'QUEUED'
    write(runtime / 'training/jobs/alpha/started.json', {'binding': spec['binding']})
    assert training.stop_status(state, 'demo', 'alpha')['executor_observation']['state'] == 'RUNNING'


def test_cancel_confirmation_and_request_id_cannot_change_the_original_intent(prepared, submitted):
    state = prepared[0]
    receipt, _, record = submitted
    revision = state.project('demo')['revision']
    for expected, run in ((revision + 1, receipt['run_id']), (revision, 'another-run')):
        with pytest.raises(ValueError, match='revision changed|original submitted run'):
            training.cancel(state, 'demo', 'alpha', 'cancel-one', expected, run_id=run, reason='stop')
    result = request(prepared, receipt)
    with pytest.raises(ValueError, match='different training cancellation reason'):
        request(prepared, receipt, reason='other reason')
    with pytest.raises(ValueError, match='exact original request intent SHA'):
        recover(prepared, {**result, 'intent_sha256': '0' * 64})
    assert json.loads(record.read_bytes())['signals'] == 1


def test_cli_http_share_unknown_recovery_and_query_exit_semantics(prepared, submitted):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.cli import main
    from ergora.web import create_app

    state = prepared[0]
    receipt, select, record = submitted
    revision = state.project('demo')['revision']
    headers = {'Origin': 'http://127.0.0.1:8977', 'X-Ergora-Request': '1'}
    client = TestClient(create_app(state.root), base_url=headers['Origin'], headers=headers)
    select('lost-ack')
    failed = client.post('/api/projects/demo/training/alpha/cancel', json={'revision': revision,
        'request_id': 'cancel-one', 'run_id': receipt['run_id'], 'reason': 'stop'})
    assert failed.status_code == 400
    unknown = client.get('/api/projects/demo/training/alpha/cancellations/cancel-one').json()
    select('signal-missing')
    output = io.StringIO()
    args = ['--home', str(state.root), 'training', 'resume-cancel', 'demo', 'alpha', 'cancel-one',
            '--revision', str(revision), '--intent-sha256', unknown['intent_sha256']]
    with redirect_stdout(output):
        code = main(args)
    assert code == 1 and json.loads(output.getvalue())['status'] == 'unknown'
    select('accepted')
    restored = client.post('/api/projects/demo/training/alpha/resume-cancel', json={
        'revision': revision, 'request_id': 'cancel-one', 'intent_sha256': unknown['intent_sha256']})
    assert restored.status_code == 200 and restored.json()['signal_delivery'] == 'history'
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'stop-status', 'demo', 'alpha'])
    assert code == 0 and json.loads(output.getvalue())['executor_observation'] is None
    assert json.loads(record.read_bytes())['signals'] == 1
