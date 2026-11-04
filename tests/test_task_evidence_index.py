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
    data.spec['profile'].update(limits={'max_work_units': 4, 'max_parallel_units': 2},
                               stage_timeout_seconds=180, approval_timeout_seconds=1200, poll_seconds=5)
    data.spec['request'] = {'input': {'work_units': [{'id': 'one'}, {'id': 'two'}]}}
    data.context['spec'] = deepcopy(data.spec)
    digest = data.creation.sha(data.context)
    data.write(data.envelope_path, {'schema_version': 1, 'job_id': data.context['job_id'],
                                    'job_sha256': digest, 'context': data.context})
    data.receipt['job_sha256'] = digest
    data.save_receipt()
    data.contexts = [data.context]
    data.outcome = {'status': 'REVIEW_READY', 'task_id': data.creation.task_id,
                    'request_sha256': data.spec['request_sha256'], 'candidate_sha': 'a' * 40}
    data.intent = {'workflow_id': 'dev-task/task-one', 'creation_sha256': 'c' * 64}
    data.selection = {'reference_project': 'demo', 'project_revision': 2, 'bindings': {'reviewer': {'tool': 'codex'}}}
    data.description = SimpleNamespace(status=WorkflowExecutionStatus.COMPLETED, run_id='original-run')
    data.lookup_ids, data.successor, data.history = [], False, 'normal'
    data.extra_events, data.event_times = [], {}

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
            for extra in data.extra_events:
                event = deepcopy(extra)
                event.event_id = len(events) + 1
                events.append(event)
            end = HistoryEvent(event_id=len(events) + 1)
            terminal = {'COMPLETED': 'completed', 'FAILED': 'failed', 'CANCELED': 'canceled'}[data.description.status.name]
            getattr(end, 'workflow_execution_' + terminal + '_event_attributes').SetInParent()
            events.append(end)
            for event in events:
                if event.event_id in data.event_times:
                    event.event_time.FromJsonString(data.event_times[event.event_id])
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
    assert 'budget' not in legacy and 'usage' not in legacy
    assert indexed['history_jobs_sha256'] == legacy['history_jobs_sha256']


def test_oversized_index_is_rejected_without_a_partial_response(closed_evidence):
    data = closed_evidence
    data.outcome['detail'] = 'x' * 1_048_576
    before = snapshot(data.creation.root)
    with pytest.raises(ValueError, match='Task evidence index exceeds'):
        inspect(data)
    assert snapshot(data.creation.root) == before


def test_budget_uses_the_frozen_profile_without_inventing_process_or_monetary_limits(closed_evidence):
    data = closed_evidence
    before = snapshot(data.creation.root)
    result = inspect(data)
    assert result['budget'] == {'source': 'frozen_task_spec.profile', 'profile_sha256': data.spec['profile_sha256'],
        'scope': 'workflow_admission_and_waiting', 'limits': {'max_work_units': 4, 'max_parallel_units': 2},
        'stage_timeout_seconds': 180, 'approval_timeout_seconds': 1200, 'poll_seconds': 5}
    assert result['usage']['configured_work_units'] == 2
    for name, unit in [('model_calls', 'calls'), ('tokens', 'tokens'), ('cost', 'currency')]:
        expected = {'state': 'not_recorded', 'value': None, 'unit': unit, 'source': None}
        if name == 'cost':
            expected['currency'] = None
        assert result['usage'][name] == expected
    assert result['execution_success'] is None and snapshot(data.creation.root) == before


def test_usage_counts_history_events_and_distinct_jobs_without_inferring_model_attempts(closed_evidence):
    from temporalio.api.history.v1 import HistoryEvent

    data = closed_evidence
    data.contexts.append(deepcopy(data.context))
    poll, started, first_signal, second_signal = [HistoryEvent() for _ in range(4)]
    poll.activity_task_scheduled_event_attributes.activity_type.name = 'dev_poll'
    started.activity_task_started_event_attributes.attempt = 3
    first_signal.workflow_execution_signaled_event_attributes.signal_name = 'approve_plan'
    second_signal.workflow_execution_signaled_event_attributes.signal_name = 'request_cancel'
    data.extra_events = [poll, started, first_signal, second_signal]
    data.event_times = {1: '2026-11-01T00:00:00Z', 8: '2026-11-01T00:01:30.5Z'}
    result = inspect(data)
    usage = result['usage']
    assert {key: usage[key] for key in ('events', 'scheduled_activities', 'recorded_activity_starts',
        'signal_events', 'dev_submit_events', 'unique_jobs')} == {'events': 8, 'scheduled_activities': 3,
        'recorded_activity_starts': 1, 'signal_events': 2, 'dev_submit_events': 2, 'unique_jobs': 1}
    assert usage['source'] == 'original_run_history'
    assert usage['workflow_span'] == {'state': 'recorded', 'source': 'original_run_history',
        'start_event_id': 1, 'close_event_id': 8, 'started_at': '2026-11-01T00:00:00Z',
        'closed_at': '2026-11-01T00:01:30.500Z', 'value': 90.5, 'unit': 'seconds'}
    assert usage['model_calls']['value'] is None and usage['tokens']['value'] is None
    assert result['jobs'][0]['history_event_ids'] == [2, 3]


@pytest.mark.parametrize('times,state,value', [
    ({}, 'not_recorded', None), ({1: '2026-11-01T00:00:00Z'}, 'not_recorded', None),
    ({3: '2026-11-01T00:00:00Z'}, 'not_recorded', None),
    ({1: '2026-11-01T00:00:01Z', 3: '2026-11-01T00:00:00Z'}, 'invalid_timestamps', None),
    ({1: '2026-11-01T00:00:00Z', 3: '2026-11-01T00:00:00Z'}, 'recorded', 0.0),
])
def test_usage_preserves_missing_reversed_and_real_zero_timestamp_facts(closed_evidence, times, state, value):
    data = closed_evidence
    data.event_times = times
    before = snapshot(data.creation.root)
    result = inspect(data)
    assert result['usage']['workflow_span']['state'] == state
    assert result['usage']['workflow_span']['value'] == value
    assert result['usage']['cost']['value'] is None
    assert snapshot(data.creation.root) == before


def test_failed_temporal_run_retains_no_outcome_and_unknown_model_usage(closed_evidence):
    from temporalio.client import WorkflowExecutionStatus

    data = closed_evidence
    data.description.status = WorkflowExecutionStatus.FAILED
    result = inspect(data)
    assert result['original_outcome'] is result['original_outcome_sha256'] is None
    assert result['temporal_status'] == 'FAILED'
    assert result['usage']['events'] == 3 and result['usage']['model_calls']['value'] is None
    assert result['jobs'][0]['outcome_reference_state'] == 'not_recorded'


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
