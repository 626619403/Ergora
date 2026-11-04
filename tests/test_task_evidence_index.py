"""A closed original run exposes verified references without adopting or rewriting them."""

import asyncio
from copy import deepcopy
import io
import json
import sys
from types import SimpleNamespace

import pytest

from ergora import reference, reference_task_reconciliation, tasks
from test_original_payloads import converter
from test_task_job_evidence import original_job
from test_task_plan import pending_plan, snapshot


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal task operations use Linux/WSL2')


@pytest.fixture
def closed_evidence(original_job, converter, monkeypatch):
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.client import WorkflowExecutionStatus

    data = original_job
    data.contexts = [data.context]
    data.outcome = {'status': 'REVIEW_READY', 'task_id': data.creation.task_id,
                    'request_sha256': data.spec['request_sha256'], 'candidate_sha': 'a' * 40}
    data.intent = {'workflow_id': 'dev-task/task-one', 'creation_sha256': 'c' * 64}
    data.selection = {'reference_project': 'demo', 'project_revision': 2, 'bindings': {'reviewer': {'tool': 'codex'}}}
    data.description = SimpleNamespace(status=WorkflowExecutionStatus.COMPLETED, run_id='original-run')
    data.lookup_ids, data.successor, data.history = [], False, 'normal'

    class Handle:
        async def fetch_history_events(self, **kwargs):
            assert kwargs['page_size'] == 100
            assert kwargs['rpc_timeout'].total_seconds() == 20
            start = HistoryEvent(event_id=1)
            start.workflow_execution_started_event_attributes.SetInParent()
            events = [start]
            for context in data.contexts:
                event = HistoryEvent(event_id=len(events) + 1)
                event.activity_task_scheduled_event_attributes.activity_type.name = 'dev_submit'
                values = [context, context] if data.history == 'multiple' else [context]
                event.activity_task_scheduled_event_attributes.input.payloads.extend(await converter.encode(values))
                events.append(event)
            end = HistoryEvent(event_id=len(events) + 1)
            end.workflow_execution_completed_event_attributes.SetInParent()
            events.append(end)
            if data.history == 'gap':
                events.pop(0)
            elif data.history == 'no-terminal':
                events.pop()
            for event in events:
                yield event

        async def result(self, **kwargs):
            assert kwargs['follow_runs'] is False
            return deepcopy(data.outcome)

    async def lookup(intent, run_id=None):
        assert intent is data.intent
        data.lookup_ids.append(run_id)
        if run_id is None and data.successor:
            return Handle(), SimpleNamespace(run_id='successor-run'), converter
        return Handle(), data.description, converter

    submission = SimpleNamespace(creation=data.creation, spec=data.spec,
        creation_record={'files': {'agent-bindings.json': data.selection}},
        submitted=lambda: (data.intent, 'original-run'), lookup_run=lookup)
    monkeypatch.setattr(reference_task_reconciliation, '_Submission', lambda payload: submission)
    data.payload = {'operation': 'inspect-index', 'run_id': 'original-run', 'timeout': 20}
    return data


def inspect(data, **changes):
    return asyncio.run(reference_task_reconciliation._Inspection({**data.payload, **changes}).run())


def test_original_contract_snapshot_and_published_references_are_read_only(closed_evidence):
    data = closed_evidence
    before = snapshot(data.creation.root)
    result = inspect(data)
    assert result['read_only'] is True and result['execution_success'] is None
    assert result['lease_released_by_operation'] is False
    assert result['published_evidence'] == 'verified' and result['external_confirmed'] is False
    assert result['original_outcome'] == data.outcome
    assert result['original_outcome_sha256'] == data.creation.sha(data.outcome)
    assert result['contract'] == {'spec': data.spec, 'spec_sha256': data.creation.sha(data.spec),
        'creation_sha256': 'c' * 64, 'submission_sha256': data.creation.sha(data.intent),
        'agent_bindings': data.selection, 'agent_bindings_sha256': data.creation.sha(data.selection)}
    job = result['jobs'][0]
    assert job['history_event_ids'] == [2] and job['receipt'] == data.receipt
    assert job['receipt_sha256'] == data.creation.sha(data.receipt)
    assert job['outcome_reference_state'] == 'not_recorded'
    assert all(row == {'state': 'not_recorded'} for row in result['context_snapshots'].values())
    assert data.lookup_ids == ['original-run', None]
    assert snapshot(data.creation.root) == before
    assert 'text' not in job['receipt']['artifacts'][0]


@pytest.mark.parametrize('state', ['matches', 'differs', 'unavailable'])
def test_explicit_outcome_receipt_link_is_separate_from_published_bytes(closed_evidence, state):
    data = closed_evidence
    data.context['stage'] = 'verify'
    data.receipt['job_sha256'] = data.creation.sha(data.context)
    data.write(data.envelope_path, {'schema_version': 1, 'job_id': data.context['job_id'],
        'job_sha256': data.creation.sha(data.context), 'context': data.context})
    data.save_receipt()
    data.outcome['verification'] = deepcopy(data.receipt)
    if state == 'differs':
        data.outcome['verification']['candidate_sha'] = 'b' * 40
    elif state == 'unavailable':
        data.receipt_path.unlink()
    before = snapshot(data.creation.root)
    result = inspect(data)
    assert result['jobs'][0]['outcome_reference_state'] == state
    assert result['published_evidence'] == ('incomplete' if state == 'unavailable' else 'verified')
    assert result['execution_success'] is None and result['original_outcome'] == data.outcome
    assert snapshot(data.creation.root) == before


def test_repeated_schedule_preserves_events_without_changing_original_job_digest(closed_evidence):
    data = closed_evidence
    first = inspect(data)
    data.contexts.append(deepcopy(data.context))
    repeated = inspect(data)
    assert repeated['jobs'][0]['history_event_ids'] == [2, 3] and len(repeated['jobs']) == 1
    assert repeated['history_jobs_sha256'] == first['history_jobs_sha256']
    data.contexts[1]['stage'] = 'different'
    with pytest.raises(ValueError, match='conflicting contexts'):
        inspect(data)


@pytest.mark.parametrize('kind', ['request', 'receipt', 'artifact', 'digest', 'foreign-receipt', 'symlink'])
def test_unavailable_or_untrusted_material_never_becomes_verified(closed_evidence, kind):
    data = closed_evidence
    artifact = data.creation.path('artifacts/' + data.receipt['artifacts'][0]['path'])
    if kind == 'request':
        data.envelope_path.unlink()
    elif kind == 'receipt':
        data.receipt_path.unlink()
    elif kind == 'artifact':
        artifact.unlink()
    elif kind == 'digest':
        artifact.write_bytes(b'changed')
    elif kind == 'foreign-receipt':
        data.receipt['job_sha256'] = 'd' * 64
        data.save_receipt()
    elif kind == 'symlink':
        original = artifact.with_suffix('.original')
        artifact.rename(original)
        artifact.symlink_to(original)
    before = snapshot(data.creation.root)
    result = inspect(data)
    assert result['published_evidence'] == 'incomplete'
    assert result['unresolved_jobs'] == [data.context['job_id']]
    if kind != 'request':
        assert result['jobs'][0]['receipt'] is None
    assert result['original_outcome'] == data.outcome and result['execution_success'] is None
    assert snapshot(data.creation.root) == before


@pytest.mark.parametrize('change,error', [('run', 'original submitted run'),
    ('running', 'closed run'), ('successor', 'different run'), ('gap', 'complete original run history'),
    ('multiple', 'single context'), ('no-terminal', 'terminal event'), ('context', 'recorded task spec')])
def test_original_scope_and_complete_history_are_required(closed_evidence, change, error):
    from temporalio.client import WorkflowExecutionStatus

    data = closed_evidence
    if change == 'run':
        data.payload['run_id'] = 'other-run'
    elif change == 'running':
        data.description.status = WorkflowExecutionStatus.RUNNING
    elif change == 'successor':
        data.successor = True
    elif change in ('gap', 'multiple', 'no-terminal'):
        data.history = change
    elif change == 'context':
        data.context['task_id'] = 'another-project-task'
    before = snapshot(data.creation.root)
    with pytest.raises(ValueError, match=error):
        inspect(data)
    assert snapshot(data.creation.root) == before


def test_cancelled_domain_result_and_legacy_external_response_keep_their_original_scope(closed_evidence):
    data = closed_evidence
    data.outcome.update(status='CANCEL_UNCONFIRMED', detail='Original external cleanup was unconfirmed')
    indexed = inspect(data)
    legacy = inspect(data, operation='inspect')
    assert indexed['original_outcome'] == legacy['original_outcome'] == data.outcome
    assert indexed['published_evidence'] == 'verified' and indexed['execution_success'] is None
    assert set(legacy['jobs'][0]) == {'job_id', 'stage', 'job_sha256', 'request_state', 'receipt_state', 'receipt_sha256'}
    assert 'contract' not in legacy and 'read_only' not in legacy
    assert indexed['history_jobs_sha256'] == legacy['history_jobs_sha256']


def test_oversized_index_is_rejected_without_a_partial_response(closed_evidence):
    data = closed_evidence
    data.outcome['detail'] = 'x' * 1_048_576
    before = snapshot(data.creation.root)
    with pytest.raises(ValueError, match='Task evidence index exceeds'):
        inspect(data)
    assert snapshot(data.creation.root) == before


def test_cli_and_api_forward_one_read_only_index_request(tmp_path, monkeypatch, capsys):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora import cli
    from ergora.web import create_app

    seen = []
    monkeypatch.setattr(tasks, '_project', lambda state, project: {'id': project})
    def native(project, home, payload, *, timeout):
        seen.append((project, home, payload, timeout))
        return {'read_only': True, **payload}
    monkeypatch.setattr(reference, 'task_evidence', native)
    assert cli.main(['--home', str(tmp_path), 'task', 'evidence', 'demo', 'task-one',
                     '--run-id', 'original-run', '--timeout', '9']) == 0
    assert json.loads(capsys.readouterr().out)['read_only'] is True
    client = TestClient(create_app(tmp_path), base_url='http://127.0.0.1')
    url = '/api/projects/demo/tasks/task-one/evidence'
    assert client.get(url, params={'run_id': 'original-run', 'timeout': 9}).status_code == 200
    assert len(seen) == 2 and seen[0] == seen[1]
    assert client.get(url).status_code == 422
    assert client.get(url, params={'run_id': '', 'timeout': 9}).status_code == 400
    assert client.get(url, params={'run_id': 'original-run', 'timeout': 61}).status_code == 400
    assert len(seen) == 2


@pytest.mark.parametrize('failure,message', [('timeout', 'index query timed out'),
                                          ('rpc', 'RPC failed: UNAVAILABLE')])
def test_index_errors_do_not_offer_write_recovery(closed_evidence, monkeypatch, failure, message):
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/local'))
    from agent_platform import core
    from temporalio.service import RPCError, RPCStatusCode

    monkeypatch.setattr(core, 'environment', lambda: {})
    async def fail(owner):
        if failure == 'timeout':
            raise TimeoutError()
        raise RPCError('unavailable', RPCStatusCode.UNAVAILABLE, b'')
    monkeypatch.setattr(reference_task_reconciliation._Inspection, 'run', fail)
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps(closed_evidence.payload)))
    with pytest.raises(SystemExit, match=message) as result:
        reference_task_reconciliation.main()
    assert 'resume' not in str(result.value) and 'reconcile' not in str(result.value)
