"""Closed-run evidence is a read-only snapshot bound to every original stage job."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

import pytest

from ergora import projects, reference, tasks
from test_registrations import installation, registration
from test_task_creation import creation_project, _files
from test_task_submission import submitted_creation, native_client, _start, _root, _calls
from test_task_export import outcome, lease


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal task operations use Linux/WSL2')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


@pytest.fixture
def external_task(submitted_creation, native_client, monkeypatch):
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from dev_platform.workflow import DevelopmentWorkflow
    from dev_platform.adapter import sha

    _start(submitted_creation)
    root = _root(submitted_creation)
    config = Path(submitted_creation[1]['execution']['config_directory']) / 'adapter.json'
    write(config, {**{key: str(root / key) for key in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')},
                   'trusted_receipts': True})
    workflow = DevelopmentWorkflow()
    workflow.spec = json.loads((root / 'tasks/new-task/task.spec.json').read_text())
    spec = workflow.spec
    base = spec['request']['repository']['base_sha']
    write(root / 'sdk-fixture/outcome.json', {'status': 'REVIEW_READY', 'task_id': 'new-task',
          'task_type': spec['request']['task_type'], 'request_sha256': spec['request_sha256'],
          'profile_sha256': spec['profile_sha256'], 'base_sha': base,
          'candidate_sha': base, 'fixture_evidence': 'original-result'})
    contexts = [workflow.context(stage) for stage in ('inspect', 'plan', 'verify')]
    write(root / 'sdk-fixture/jobs.json', contexts)
    for context in contexts:
        job_id = context['job_id']
        write(root / 'requests/new-task' / (job_id + '.json'),
              {'schema_version': 1, 'job_id': job_id, 'job_sha256': sha(context), 'context': context})
        artifact = (job_id + '\n').encode()
        path = root / 'artifacts/new-task' / (job_id + '.txt')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(artifact)
        write(root / 'receipts/new-task' / (job_id + '.json'),
              {'schema_version': 1, 'job_id': job_id, 'job_sha256': sha(context), 'state': 'SUCCEEDED',
               'actor': {'id': 'fixture-ci', 'session_id': job_id, 'role': context['stage'], 'kind': 'ci'},
               'candidate_sha': outcome(submitted_creation)['candidate_sha'],
               'artifacts': [{'name': 'evidence', 'path': 'new-task/' + job_id + '.txt',
                              'sha256': hashlib.sha256(artifact).hexdigest()}],
               'checks': [{'id': 'fixture-check', 'status': 'pass', 'artifact': 'evidence'}]})
    write(root / 'fences/new-task.json', {'schema_version': 1, 'task_id': 'new-task',
          'request_sha256': workflow.spec['request_sha256']})
    return submitted_creation


@pytest.fixture
def external_client(external_task, monkeypatch):
    original = reference.subprocess.run
    fixture = Path(__file__).parent / 'fixtures/task_external_status_client.py'
    def invoke(argv, **kwargs):
        if 'from ergora.reference_task_reconciliation import main;main()' in argv:
            argv = [*argv[:-1], fixture.read_text(encoding='utf-8')]
        return original(argv, **kwargs)
    monkeypatch.setattr(reference.subprocess, 'run', invoke)


def inspect(creation, **kwargs):
    return tasks.external_status(creation[0], 'demo', 'new-task', **{'run_id': 'original-run', **kwargs})


def paths(creation, key):
    return sorted((_root(creation) / key / 'new-task').glob('*'))


def snapshot(creation):
    return {p.relative_to(_root(creation)).as_posix(): p.read_bytes() for p in _root(creation).rglob('*')
            if p.is_file() and 'sdk-fixture' not in p.parts}


@pytest.mark.parametrize('submitted_creation', ['repository-governance', 'large-change'], indirect=True)
def test_closed_original_evidence_does_not_mutate_outcome_leases_or_files(external_task, external_client):
    before = snapshot(external_task)
    result = inspect(external_task)
    assert result['external_confirmed'] is True
    assert result['original_outcome'] == outcome(external_task)
    assert result['run_id'] == 'original-run' and result['workflow_id'] == 'dev-task/new-task'
    assert result['temporal_status'] == 'COMPLETED' and result['terminal'] is True
    assert {job['stage'] for job in result['jobs']} == {'inspect', 'plan', 'verify'}
    assert all(job['receipt_state'] == 'SUCCEEDED' and job['request_state'] == 'matches' for job in result['jobs'])
    assert result['unexpected_jobs'] == result['unresolved_jobs'] == []
    assert result['lease_released_by_operation'] is False and result['execution_success'] is None
    assert inspect(external_task) == result and snapshot(external_task) == before and lease(external_task)[1] == 1
    assert _calls(external_task).count('external-history-page') == 6
    assert _calls(external_task).count('external-codec-decode') == 10


@pytest.mark.parametrize('scenario,error', [
    ('history-gap', 'complete original run history'), ('history-no-start', 'complete original run history'),
    ('history-no-terminal', 'terminal event'), ('history-wrong-terminal', 'terminal event'),
    ('history-empty', 'terminal event'), ('history-rpc-unavailable', 'RPC failed: UNAVAILABLE'),
    ('history-multiple-contexts', 'single context'),
    ('wrong-spec', 'original task spec'), ('wrong-memo', 'matching submission memo'),
    ('successor-run', 'different run'), ('not-found', 'run was not found'),
    ('rpc-unavailable', 'RPC failed: UNAVAILABLE'), ('offline', 'offline'),
])
def test_original_history_and_ownership_failures_never_confirm_or_write(external_task, external_client, monkeypatch, scenario, error):
    before = snapshot(external_task)
    monkeypatch.setenv('ERGORA_TEST_EXTERNAL_SCENARIO', scenario)
    with pytest.raises(ValueError, match=error):
        inspect(external_task)
    assert snapshot(external_task) == before and lease(external_task)[1] == 1


@pytest.mark.parametrize('temporal_status', ['FAILED', 'CANCELED', 'TERMINATED', 'TIMED_OUT'])
def test_closed_temporal_failures_can_show_external_evidence_without_inventing_an_outcome(external_task, external_client, temporal_status):
    path = _root(external_task) / 'sdk-fixture/server.json'
    write(path, {**json.loads(path.read_text()), 'status': temporal_status})
    result = inspect(external_task)
    assert result['temporal_status'] == temporal_status and result['original_outcome'] is None
    assert result['external_confirmed'] is True and result['execution_success'] is None and lease(external_task)[1] == 1
    assert 'external-result' not in _calls(external_task)


@pytest.mark.parametrize('phase', ['CANCEL_UNCONFIRMED', 'BLOCKED'])
def test_external_confirmation_preserves_the_original_workflow_failure(external_task, external_client, phase):
    root = _root(external_task)
    original = {**outcome(external_task), 'status': phase, 'original_detail': 'Original external state was unconfirmed'}
    write(root / 'sdk-fixture/outcome.json', original)
    before = snapshot(external_task)
    result = inspect(external_task)
    assert result['external_confirmed'] is True and result['original_outcome'] == original
    assert result['execution_success'] is None and snapshot(external_task) == before and lease(external_task)[1] == 1


@pytest.mark.parametrize('temporal_status', ['RUNNING', 'CONTINUED_AS_NEW'])
def test_nonterminal_and_successor_runs_are_rejected(external_task, external_client, temporal_status):
    path = _root(external_task) / 'sdk-fixture/server.json'
    write(path, {**json.loads(path.read_text()), 'status': temporal_status})
    with pytest.raises(ValueError, match='closed run without a successor'):
        inspect(external_task)
    assert 'external-history-page' not in _calls(external_task)


@pytest.mark.parametrize('missing', ['one-request', 'all-requests', 'one-receipt', 'fence'])
def test_missing_records_cannot_become_zero_job_confirmation(external_task, external_client, missing):
    root = _root(external_task)
    if missing == 'one-request':
        paths(external_task, 'requests')[0].unlink()
    elif missing == 'all-requests':
        for path in paths(external_task, 'requests'):
            path.unlink()
        (root / 'requests/new-task').rmdir()
        (root / 'requests').rmdir()
    elif missing == 'one-receipt':
        paths(external_task, 'receipts')[0].unlink()
    else:
        (root / 'fences/new-task.json').unlink()
    before = snapshot(external_task)
    result = inspect(external_task)
    assert result['external_confirmed'] is False and len(result['jobs']) == 3
    assert len(result['unresolved_jobs']) == (3 if missing == 'all-requests' else 0 if missing == 'fence' else 1)
    assert snapshot(external_task) == before


@pytest.mark.parametrize('invalid', ['json', 'identity', 'state', 'unhashable-state', 'artifact', 'symlink'])
def test_damaged_receipts_are_visible_as_unresolved(external_task, external_client, invalid):
    path = paths(external_task, 'receipts')[0]
    receipt = json.loads(path.read_text())
    if invalid == 'json':
        path.write_text('{invalid-json')
    elif invalid == 'artifact':
        (_root(external_task) / 'artifacts' / receipt['artifacts'][0]['path']).write_bytes(b'changed')
    elif invalid == 'symlink':
        original = path.with_suffix('.original')
        path.rename(original)
        path.symlink_to(original)
    else:
        receipt['job_sha256' if invalid == 'identity' else 'state'] = 'a' * 64 if invalid == 'identity' else [] if invalid == 'unhashable-state' else 'RUNNING'
        write(path, receipt)
    result = inspect(external_task)
    job = next(item for item in result['jobs'] if item['job_id'] == receipt['job_id'])
    assert job['receipt_state'] == 'invalid' and job['receipt_error']
    assert result['unresolved_jobs'] == [job['job_id']] and result['external_confirmed'] is False


def test_unexpected_requests_are_kept_even_with_all_known_jobs_settled(external_task, external_client):
    write(_root(external_task) / 'requests/new-task/unexpected.json', {'job_id': 'unexpected'})
    result = inspect(external_task)
    assert len(result['jobs']) == 3 and result['unresolved_jobs'] == result['unexpected_jobs'] == ['unexpected']
    assert result['external_confirmed'] is False


@pytest.mark.parametrize('invalid', [False, True])
def test_orphan_receipts_remain_unresolved_without_a_history_job_or_request(external_task, external_client, invalid):
    path = _root(external_task) / 'receipts/new-task/orphan-job.json'
    if invalid:
        path.write_text('{invalid-json')
    else:
        receipt = json.loads(paths(external_task, 'receipts')[0].read_text())
        write(path, {**receipt, 'job_id': 'orphan-job'})
    before = snapshot(external_task)
    result = inspect(external_task)
    assert result['unexpected_jobs'] == result['unresolved_jobs'] == ['orphan-job']
    assert result['external_confirmed'] is False and snapshot(external_task) == before and lease(external_task)[1] == 1


@pytest.mark.parametrize('record', ['envelope', 'fence', 'adapter-root', 'context', 'same-id-context', 'outcome'])
def test_conflicting_evidence_is_rejected_and_preserved(external_task, external_client, record):
    root = _root(external_task)
    if record == 'envelope':
        write(paths(external_task, 'requests')[0], {'schema_version': 1, 'job_id': 'other'})
    elif record == 'fence':
        write(root / 'fences/new-task.json', {'schema_version': 1, 'task_id': 'other', 'request_sha256': 'a' * 64})
    elif record == 'adapter-root':
        path = Path(external_task[1]['execution']['config_directory']) / 'adapter.json'
        write(path, {**json.loads(path.read_text()), 'requests': str(root / 'another-requests')})
    elif record == 'outcome':
        write(root / 'sdk-fixture/outcome.json', {**outcome(external_task), 'task_id': 'other'})
    else:
        path = root / 'sdk-fixture/jobs.json'
        contexts = json.loads(path.read_text())
        if record == 'same-id-context':
            contexts.append(deepcopy(contexts[0]))
            contexts[-1]['author_ids'] = ['another-author']
        else:
            contexts[0]['profile_sha256'] = 'a' * 64
        write(path, contexts)
    before = snapshot(external_task)
    with pytest.raises(ValueError, match='conflicts|differ|conflicting'):
        inspect(external_task)
    assert snapshot(external_task) == before and lease(external_task)[1] == 1


def test_identical_duplicate_jobs_are_merged_and_terminal_failure_receipts_are_valid(external_task, external_client):
    root = _root(external_task)
    path = root / 'sdk-fixture/jobs.json'
    contexts = json.loads(path.read_text())
    write(path, contexts + [contexts[0]])
    for path, state in zip(paths(external_task, 'receipts'), ['FAILED', 'CANCELLED']):
        write(path, {**json.loads(path.read_text()), 'state': state})
    result = inspect(external_task)
    assert len(result['jobs']) == 3 and result['external_confirmed'] is True
    assert {item['receipt_state'] for item in result['jobs']} == {'SUCCEEDED', 'FAILED', 'CANCELLED'}
    assert result['original_outcome'] == outcome(external_task) and result['execution_success'] is None


def test_full_history_without_submissions_can_confirm_only_an_existing_fence(external_task, external_client):
    write(_root(external_task) / 'sdk-fixture/jobs.json', [])
    for key in ('requests', 'receipts'):
        for path in paths(external_task, key):
            path.unlink()
    result = inspect(external_task)
    assert result['jobs'] == [] and result['external_confirmed'] is True
    (_root(external_task) / 'fences/new-task.json').unlink()
    assert inspect(external_task)['external_confirmed'] is False


@pytest.mark.parametrize('options,error', [({'run_id': 'other'}, 'original submitted run'), ({'timeout': True}, 'timeout')])
def test_queries_require_exact_run_and_bounded_timeout(external_task, external_client, options, error):
    before = _files(_root(external_task))
    with pytest.raises(ValueError, match=error):
        inspect(external_task, **options)
    assert _files(_root(external_task)) == before
    assert 'external-connect' not in _calls(external_task)


def test_cli_and_api_return_the_same_readonly_facts(external_task, external_client, capsys):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora import cli
    from ergora.web import create_app

    client = TestClient(create_app(external_task[0].root), base_url='http://127.0.0.1')
    uri = '/api/projects/demo/tasks/new-task/external-status'
    assert client.get(uri).status_code == 422
    assert client.get(uri, params={'run_id': 'original-run', 'timeout': 'true'}).status_code == 422
    assert client.get(uri, params={'run_id': 'other'}).status_code == 400
    response = client.get(uri, params={'run_id': 'original-run'})
    assert response.status_code == 200
    args = ['--home', str(external_task[0].root), 'task', 'external-status', 'demo', 'new-task', '--run-id', 'original-run']
    assert cli.main(args) == 0 and json.loads(capsys.readouterr().out) == response.json()
    (_root(external_task) / 'fences/new-task.json').unlink()
    assert cli.main(args) == 0 and json.loads(capsys.readouterr().out)['external_confirmed'] is False


def test_query_timeout_and_slow_rpc_do_not_reserve_the_shared_database(external_task, external_client, monkeypatch):
    state = external_task[0]
    projects.create(state, 'other-project', Path(external_task[1]['repo']))
    monkeypatch.setenv('ERGORA_TEST_EXTERNAL_SCENARIO', 'slow-connect')
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(inspect, external_task)
        deadline = time.monotonic() + 15
        while 'external-connect' not in _calls(external_task):
            assert time.monotonic() < deadline
            time.sleep(.05)
        assert projects.bind(state, 'other-project', 'memory', {'tool': 'sqlite'}, 1)['revision'] == 2
        assert not pending.done()
        assert pending.result(timeout=15)['external_confirmed'] is True
    before = snapshot(external_task)
    with pytest.raises(ValueError, match='timed out; no fence or lease was changed'):
        inspect(external_task, timeout=1)
    assert snapshot(external_task) == before and lease(external_task)[1] == 1
