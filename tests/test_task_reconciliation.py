"""Explicit cleanup preserves the original run and recovers each durable boundary."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sys
import time

import pytest

from ergora import projects, tasks
from ergora.state import State
from test_registrations import installation, registration
from test_task_creation import creation_project, _files
from test_task_submission import submitted_creation, native_client, _root, _calls
from test_task_export import outcome, lease
from test_task_external_status import external_task, external_client, write, paths, snapshot


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal task operations use Linux/WSL2')


@pytest.fixture
def cleanup(external_task, external_client):
    root = _root(external_task)
    (root / 'fences/new-task.json').unlink()
    write(root / 'sdk-fixture/outcome.json', {**outcome(external_task), 'status': 'CANCEL_UNCONFIRMED',
                                           'detail': 'Original workflow could not confirm its external jobs'})
    return external_task


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def reconcile(creation, revision=1, **options):
    return tasks.reconcile(creation[0], 'demo', 'new-task', revision,
                           **{'run_id': 'original-run', 'confirm': True, **options})


def status(creation):
    return tasks.reconciliation(State(creation[0].root), 'demo', 'new-task')


def resume(creation, revision=1, **options):
    return tasks.resume_reconcile(State(creation[0].root), 'demo', 'new-task', revision,
                                  status(creation)['intent_sha256'], confirm=True, **options)


def record(creation, phase):
    return _root(creation) / 'ergora/task-reconciliations' / ('new-task.' + phase + '.json')


@pytest.mark.parametrize('submitted_creation', ['repository-governance', 'large-change'], indirect=True)
def test_cleanup_releases_exact_claim_and_keeps_the_original_unconfirmed_result(cleanup):
    original = outcome(cleanup)
    before = snapshot(cleanup)
    assert status(cleanup)['status'] == 'not_recorded' and snapshot(cleanup) == before
    result = reconcile(cleanup)
    evidence = json.loads(record(cleanup, 'evidence').read_text())
    assert result['status'] == 'reconciled' and result['lease_released'] is True
    assert result['external_confirmed'] is True and result['execution_success'] is None
    assert result['original_outcome'] == evidence['original_outcome'] == original == outcome(cleanup)
    assert evidence['original_outcome']['status'] == 'CANCEL_UNCONFIRMED'
    assert len(evidence['jobs']) == 3 and evidence['unexpected_jobs'] == evidence['unresolved_jobs'] == []
    assert lease(cleanup)[1] == 0 and lease(cleanup)[0][1] == result['evidence_sha256'] == digest(evidence)
    assert result['release_evidence_sha256'] == digest(evidence)
    assert all((_root(cleanup) / path).read_bytes() == raw for path, raw in before.items()
               if not path.startswith('ingress/'))
    calls, after = _calls(cleanup), snapshot(cleanup)
    assert reconcile(cleanup) == resume(cleanup) == status(cleanup) == result
    assert _calls(cleanup) == calls and snapshot(cleanup) == after
    assert calls.count('reconciliation-fence') == calls.count('reconciliation-release') == 1
    projects.bind(cleanup[0], 'demo', 'memory', {'tool': 'sqlite'}, 1)
    assert resume(cleanup, revision=2)['intent_sha256'] == result['intent_sha256']


@pytest.mark.parametrize('phase', ['REVIEW_READY', 'BLOCKED'])
@pytest.mark.parametrize('already_released', [False, True])
def test_native_eligible_release_keeps_its_original_outcome_digest(cleanup, phase, already_released):
    from dev_platform.ingress import IngressLeases

    root = _root(cleanup)
    original = {**outcome(cleanup), 'status': phase, 'fence': {'confirmed': True}}
    write(root / 'sdk-fixture/outcome.json', original)
    if already_released:
        claim = json.loads((root / 'tasks/new-task/cli-ingress.json').read_text())
        with closing(IngressLeases(root / 'ingress/leases.sqlite3')) as leases:
            leases.release(**claim, evidence_digest=digest(original))
    result = reconcile(cleanup)
    assert result['status'] == 'reconciled' and result['original_outcome'] == original
    assert result['release_evidence_sha256'] == digest(original) == lease(cleanup)[0][1]
    assert lease(cleanup)[1] == 0 and result['evidence_sha256'] != digest(original)


@pytest.mark.parametrize('temporal_status', ['FAILED', 'CANCELED', 'TERMINATED', 'TIMED_OUT'])
def test_closed_run_without_a_result_can_release_confirmed_cleanup(cleanup, temporal_status):
    path = _root(cleanup) / 'sdk-fixture/server.json'
    write(path, {**json.loads(path.read_text()), 'status': temporal_status})
    result = reconcile(cleanup)
    assert result['status'] == 'reconciled' and result['original_outcome'] is None
    assert result['temporal_status'] == temporal_status and lease(cleanup)[1] == 0
    assert 'external-result' not in _calls(cleanup)


@pytest.mark.parametrize('scenario,expected', [
    ('before-intent', 'not_recorded'), ('after-intent', 'prepared'), ('before-attempt', 'prepared'),
    ('after-attempt', 'unknown'), ('before-fence', 'unknown'), ('after-fence', 'unknown'),
    ('before-evidence', 'unknown'), ('after-evidence', 'confirmed'),
    ('before-release-commit', 'confirmed'), ('after-release-commit', 'confirmed'),
    ('before-result', 'confirmed'), ('after-result', 'reconciled'),
])
def test_each_interruption_resumes_only_the_original_immutable_cleanup(cleanup, monkeypatch, scenario, expected):
    original = outcome(cleanup)
    monkeypatch.setenv('ERGORA_TEST_RECONCILIATION_SCENARIO', scenario)
    with pytest.raises(ValueError, match='Fixture reconciliation interruption'):
        reconcile(cleanup)
    current = status(cleanup)
    assert current['status'] == expected and outcome(cleanup) == original
    committed = scenario in ('after-release-commit', 'before-result', 'after-result')
    assert lease(cleanup)[1] == (0 if committed else 1)
    monkeypatch.delenv('ERGORA_TEST_RECONCILIATION_SCENARIO')
    if expected == 'not_recorded':
        assert 'external-connect' not in _calls(cleanup)
        result = reconcile(cleanup)
    else:
        before = _calls(cleanup)
        assert reconcile(cleanup) == current and _calls(cleanup) == before
        result = resume(cleanup)
    assert result['status'] == 'reconciled' and lease(cleanup)[1] == 0
    assert result['original_outcome'] == original and result['evidence_sha256'] == lease(cleanup)[0][1]


@pytest.mark.parametrize('missing', ['request', 'all-requests', 'receipt', 'artifact'])
def test_missing_original_evidence_never_releases_and_can_be_completed_by_its_owner(cleanup, missing):
    root = _root(cleanup)
    if missing == 'all-requests':
        removed = {path: path.read_bytes() for path in paths(cleanup, 'requests')}
    elif missing == 'artifact':
        path = next((root / 'artifacts/new-task').glob('*'))
        removed = {path: path.read_bytes()}
    else:
        path = paths(cleanup, 'requests' if missing == 'request' else 'receipts')[0]
        removed = {path: path.read_bytes()}
    for path in removed:
        path.unlink()
    result = reconcile(cleanup)
    assert result['status'] == 'unknown' and result['external_confirmed'] is False
    assert result['unresolved_jobs'] and result['evidence_saved'] is False and lease(cleanup)[1] == 1
    assert (root / 'fences/new-task.json').exists() and not record(cleanup, 'evidence').exists()
    calls, before = _calls(cleanup), snapshot(cleanup)
    assert status(cleanup)['status'] == 'unknown' and snapshot(cleanup) == before and _calls(cleanup) == calls
    for path, raw in removed.items():
        path.write_bytes(raw)
    assert resume(cleanup)['status'] == 'reconciled' and lease(cleanup)[1] == 0


@pytest.mark.parametrize('folder', ['requests', 'receipts'])
def test_unexpected_scope_is_rejected_before_publishing_any_fence(cleanup, folder):
    write(_root(cleanup) / folder / 'new-task/orphan.json', {'job_id': 'orphan'})
    with pytest.raises(ValueError, match='outside the original run'):
        reconcile(cleanup)
    assert status(cleanup)['status'] == 'prepared' and lease(cleanup)[1] == 1
    assert not record(cleanup, 'attempt').exists() and not (_root(cleanup) / 'fences/new-task.json').exists()


@pytest.mark.parametrize('scenario,error', [
    ('wrong-memo', 'matching submission memo'), ('wrong-spec', 'original task spec'),
    ('successor-run', 'different run'), ('history-gap', 'complete original run history'),
    ('history-no-terminal', 'terminal event'), ('not-found', 'run was not found'),
    ('rpc-unavailable', 'RPC failed: UNAVAILABLE'),
])
def test_remote_preconditions_fail_without_publishing_or_releasing(cleanup, monkeypatch, scenario, error):
    monkeypatch.setenv('ERGORA_TEST_EXTERNAL_SCENARIO', scenario)
    with pytest.raises(ValueError, match=error):
        reconcile(cleanup)
    assert status(cleanup)['status'] == 'prepared' and lease(cleanup)[1] == 1
    assert not record(cleanup, 'attempt').exists() and not (_root(cleanup) / 'fences/new-task.json').exists()


def test_successor_detected_after_fence_does_not_release_the_original_claim(cleanup, monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_RECONCILIATION_SCENARIO', 'successor-after-fence')
    with pytest.raises(ValueError, match='different run'):
        reconcile(cleanup)
    assert status(cleanup)['status'] == 'unknown' and lease(cleanup)[1] == 1
    assert (_root(cleanup) / 'fences/new-task.json').exists() and not record(cleanup, 'evidence').exists()


@pytest.mark.parametrize('scenario', ['orphan-after-fence', 'outcome-after-fence'])
def test_new_scope_or_outcome_during_publication_cannot_release(cleanup, monkeypatch, scenario):
    monkeypatch.setenv('ERGORA_TEST_RECONCILIATION_SCENARIO', scenario)
    if scenario == 'outcome-after-fence':
        with pytest.raises(ValueError, match='changed during external reconciliation'):
            reconcile(cleanup)
    else:
        result = reconcile(cleanup)
        assert result['status'] == 'unknown' and result['external_confirmed'] is False
        assert result['unexpected_jobs'] == result['unresolved_jobs'] == ['orphan']
    assert status(cleanup)['status'] == 'unknown' and lease(cleanup)[1] == 1
    assert not record(cleanup, 'evidence').exists()


def test_running_workflow_cannot_be_fenced_or_released(cleanup):
    path = _root(cleanup) / 'sdk-fixture/server.json'
    write(path, {**json.loads(path.read_text()), 'status': 'RUNNING'})
    with pytest.raises(ValueError, match='closed run without a successor'):
        reconcile(cleanup)
    assert not (_root(cleanup) / 'fences/new-task.json').exists() and lease(cleanup)[1] == 1


def test_complete_zero_job_history_can_be_fenced_without_guessing_from_empty_directories(cleanup):
    write(_root(cleanup) / 'sdk-fixture/jobs.json', [])
    for folder in ('requests', 'receipts'):
        for path in paths(cleanup, folder):
            path.unlink()
    assert reconcile(cleanup)['status'] == 'reconciled' and lease(cleanup)[1] == 0
    assert json.loads(record(cleanup, 'evidence').read_text())['jobs'] == []


def test_missing_ledger_cannot_be_recreated_to_manufacture_ownership(cleanup, monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_RECONCILIATION_SCENARIO', 'after-evidence')
    with pytest.raises(ValueError, match='Fixture'):
        reconcile(cleanup)
    ledger = _root(cleanup) / 'ingress/leases.sqlite3'
    ledger.unlink()
    monkeypatch.delenv('ERGORA_TEST_RECONCILIATION_SCENARIO')
    before = snapshot(cleanup)
    with pytest.raises(ValueError, match='ledger is missing'):
        resume(cleanup)
    assert not ledger.exists() and snapshot(cleanup) == before and not record(cleanup, 'result').exists()


def test_another_release_digest_cannot_be_adopted_as_this_operations_result(cleanup):
    from dev_platform.ingress import IngressLeases

    root = _root(cleanup)
    claim = json.loads((root / 'tasks/new-task/cli-ingress.json').read_text())
    with closing(IngressLeases(root / 'ingress/leases.sqlite3')) as leases:
        leases.release(**claim, evidence_digest='a' * 64)
    with pytest.raises(ValueError, match='release evidence differs'):
        reconcile(cleanup)
    assert status(cleanup)['status'] == 'confirmed' and lease(cleanup)[0][1] == 'a' * 64
    assert not record(cleanup, 'result').exists()


def test_recovery_rejects_another_intent_and_corrupted_journal_before_remote_access(cleanup, monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_RECONCILIATION_SCENARIO', 'after-evidence')
    with pytest.raises(ValueError, match='Fixture'):
        reconcile(cleanup)
    monkeypatch.delenv('ERGORA_TEST_RECONCILIATION_SCENARIO')
    before, calls = snapshot(cleanup), _calls(cleanup)
    with pytest.raises(ValueError, match='exact original intent digest'):
        tasks.resume_reconcile(cleanup[0], 'demo', 'new-task', 1, 'a' * 64, confirm=True)
    assert snapshot(cleanup) == before and _calls(cleanup) == calls
    for phase, changes in [('intent', {'run_id': 'another-run'}), ('attempt', {'workflow_id': 'another-workflow'}),
                           ('evidence', {'jobs': []}), ('result', {'evidence_sha256': 'a' * 64})]:
        path = record(cleanup, phase)
        raw = path.read_bytes() if path.exists() else None
        write(path, {**(json.loads(raw) if raw else {}), **changes})
        corrupted = snapshot(cleanup)
        with pytest.raises(ValueError, match='conflicts|differs'):
            tasks.resume_reconcile(cleanup[0], 'demo', 'new-task', 1,
                                    json.loads(record(cleanup, 'evidence').read_text())['intent_sha256'], confirm=True)
        assert snapshot(cleanup) == corrupted and _calls(cleanup) == calls and lease(cleanup)[1] == 1
        if raw is None:
            path.unlink()
        else:
            path.write_bytes(raw)
    assert resume(cleanup)['status'] == 'reconciled'


@pytest.mark.parametrize('changed', ['outcome', 'history', 'receipt', 'artifact', 'fence', 'claim'])
def test_recovery_rechecks_saved_facts_before_releasing(cleanup, monkeypatch, changed):
    monkeypatch.setenv('ERGORA_TEST_RECONCILIATION_SCENARIO', 'after-evidence')
    with pytest.raises(ValueError, match='Fixture'):
        reconcile(cleanup)
    intent = status(cleanup)['intent_sha256']
    monkeypatch.delenv('ERGORA_TEST_RECONCILIATION_SCENARIO')
    root = _root(cleanup)
    if changed == 'outcome':
        write(root / 'sdk-fixture/outcome.json', {**outcome(cleanup), 'detail': 'Changed after checkpoint'})
    elif changed == 'history':
        path = root / 'sdk-fixture/jobs.json'
        write(path, json.loads(path.read_text())[:-1])
    elif changed == 'receipt':
        path = paths(cleanup, 'receipts')[0]
        write(path, {**json.loads(path.read_text()), 'detail': 'Changed after evidence'})
    elif changed == 'artifact':
        next((root / 'artifacts/new-task').glob('*')).write_bytes(b'changed')
    elif changed == 'fence':
        write(root / 'fences/new-task.json', {'schema_version': 1, 'task_id': 'other'})
    else:
        path = root / 'tasks/new-task/cli-ingress.json'
        write(path, {**json.loads(path.read_text()), 'owner': 'another-owner'})
    before = snapshot(cleanup)
    with pytest.raises(ValueError, match='conflict|outside the original run|no longer confirmed|ownership differs|different content'):
        tasks.resume_reconcile(State(cleanup[0].root), 'demo', 'new-task', 1, intent, confirm=True)
    assert snapshot(cleanup) == before and lease(cleanup)[1] == 1 and not record(cleanup, 'result').exists()


@pytest.mark.parametrize('field,value', [('owner', 'other-owner'), ('task_id', 'other'), ('spec_sha256', 'a' * 64),
                                        ('tracker', {'kind': 'local', 'project': 'other/project', 'issue_id': '1'})])
def test_original_local_ingress_record_cannot_be_substituted(cleanup, field, value):
    path = _root(cleanup) / 'tasks/new-task/cli-ingress.json'
    write(path, {**json.loads(path.read_text()), field: value})
    before = snapshot(cleanup)
    with pytest.raises(ValueError, match='ownership differs'):
        reconcile(cleanup)
    assert snapshot(cleanup) == before and lease(cleanup)[1] == 1


def test_slow_remote_phase_releases_the_control_database_but_keeps_the_task_lock(cleanup, monkeypatch):
    projects.create(cleanup[0], 'other-project', Path(cleanup[1]['repo']))
    monkeypatch.setenv('ERGORA_TEST_EXTERNAL_SCENARIO', 'slow-connect')
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(reconcile, cleanup)
        deadline = time.monotonic() + 15
        while 'external-connect' not in _calls(cleanup):
            assert time.monotonic() < deadline
            time.sleep(.05)
        assert projects.bind(cleanup[0], 'other-project', 'memory', {'tool': 'sqlite'}, 1)['revision'] == 2
        with pytest.raises(ValueError, match='lock|progress|temporarily unavailable'):
            reconcile(cleanup)
        assert status(cleanup)['status'] == 'prepared' and not pending.done()
        assert pending.result(timeout=20)['status'] == 'reconciled'


def test_timeout_preserves_the_original_intent_for_explicit_resume(cleanup, monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_EXTERNAL_SCENARIO', 'slow-connect')
    with pytest.raises(ValueError, match='Reconciliation timed out'):
        reconcile(cleanup, timeout=1)
    assert status(cleanup)['status'] == 'prepared' and lease(cleanup)[1] == 1
    monkeypatch.delenv('ERGORA_TEST_EXTERNAL_SCENARIO')
    assert resume(cleanup)['status'] == 'reconciled'


def test_cli_and_api_use_the_same_recoverable_operation_and_readonly_status(cleanup, capsys):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora import cli
    from ergora.web import create_app

    client = TestClient(create_app(cleanup[0].root), base_url='http://127.0.0.1',
                        headers={'X-Ergora-Request': '1', 'Origin': 'http://127.0.0.1'})
    uri = '/api/projects/demo/tasks/new-task/'
    body = {'revision': 1, 'run_id': 'original-run', 'confirm': True}
    before = _files(_root(cleanup))
    for changes, expected in [({'confirm': 'true'}, 422), ({'confirm': False}, 400),
                              ({'timeout': True}, 422), ({'revision': True}, 422), ({'revision': 2}, 400),
                              ({'run_id': 'another-run'}, 400)]:
        assert client.post(uri + 'reconcile', json={**body, **changes}).status_code == expected
        assert _files(_root(cleanup)) == before
    args = ['--home', str(cleanup[0].root), 'task']
    assert cli.main([*args, 'reconcile', 'demo', 'new-task', '--revision', '1', '--run-id', 'original-run', '--confirm']) == 0
    result = json.loads(capsys.readouterr().out)
    assert client.get(uri + 'reconciliation').json() == result
    assert client.post(uri + 'reconcile', json=body).json() == result
    assert client.post(uri + 'resume-reconcile', json={'revision': 1, 'confirm': True,
                                                       'intent_sha256': result['intent_sha256']}).json() == result
    after = snapshot(cleanup)
    assert cli.main([*args, 'reconciliation', 'demo', 'new-task']) == 0
    assert json.loads(capsys.readouterr().out) == result and snapshot(cleanup) == after
