"""Page original-run metadata using the real SDK iterator, including oversized pages."""

import asyncio
import base64
import json
from types import SimpleNamespace

import pytest

from ergora import reference, reference_task_events
from ergora.reference_task_creation import _Creation


@pytest.fixture
def event_history(monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.api.common.v1 import Payload
    from temporalio.api.enums.v1 import EventType
    from temporalio.api.history.v1 import History, HistoryEvent
    from temporalio.api.workflowservice.v1 import GetWorkflowExecutionHistoryResponse
    from temporalio.client import FetchWorkflowHistoryEventsInput, WorkflowExecutionStatus, WorkflowHistoryEventAsyncIterator

    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from dev_platform.contracts import canonical_sha

    data = SimpleNamespace(events=[], pages=[], looked_up=0, failure=None, next_token=None,
                           description=SimpleNamespace(status=WorkflowExecutionStatus.COMPLETED))
    for i in range(1, 10):
        event = HistoryEvent(event_id=i, event_type=EventType.EVENT_TYPE_WORKFLOW_TASK_SCHEDULED)
        event.workflow_task_scheduled_event_attributes.SetInParent()
        data.events.append(event)
    data.events[0].ClearField('workflow_task_scheduled_event_attributes')
    data.events[0].event_type = EventType.EVENT_TYPE_WORKFLOW_EXECUTION_STARTED
    data.events[0].workflow_execution_started_event_attributes.input.payloads.append(Payload(data=b'private-input'))
    scheduled = data.events[2].activity_task_scheduled_event_attributes
    data.events[2].event_type = EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED
    scheduled.activity_id, scheduled.activity_type.name = 'activity-three', 'dev_submit'
    scheduled.input.payloads.append(Payload(data=b'private-prompt'))
    data.events[3].event_type = EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED
    data.events[3].activity_task_completed_event_attributes.scheduled_event_id = 3
    data.events[3].activity_task_completed_event_attributes.result.payloads.append(Payload(data=b'private-result'))
    data.events[4].event_type = EventType.EVENT_TYPE_WORKFLOW_EXECUTION_SIGNALED
    data.events[4].workflow_execution_signaled_event_attributes.signal_name = 'approve_plan'
    data.events[4].workflow_execution_signaled_event_attributes.input.payloads.append(Payload(data=b'private-decision'))

    class Service:
        async def get_workflow_execution_history(self, request, **kwargs):
            assert request.execution.workflow_id == 'dev-task/task-one' and request.execution.run_id == 'original-run'
            assert not request.wait_new_event and request.history_event_filter_type == 1
            assert kwargs['timeout'].total_seconds() == 20
            data.pages.append((request.next_page_token, request.maximum_page_size))
            start = int(request.next_page_token or b'0')
            # Deliberately exceed page_size, as the real server does with event batches.
            return GetWorkflowExecutionHistoryResponse(history=History(events=data.events[start:start + 4]),
                next_page_token=data.next_token if data.next_token is not None else (
                    str(start + 4).encode() if start + 4 < len(data.events) else b''))

    client = SimpleNamespace(namespace='test', workflow_service=Service())

    class Handle:
        def fetch_history_events(self, **kwargs):
            return WorkflowHistoryEventAsyncIterator(client, FetchWorkflowHistoryEventsInput(
                id='dev-task/task-one', run_id='original-run', page_size=kwargs['page_size'],
                next_page_token=kwargs['next_page_token'], wait_new_event=False, event_filter_type=1,
                skip_archival=False, rpc_metadata={}, rpc_timeout=kwargs['rpc_timeout']))

    intent = {'workflow_id': 'dev-task/task-one', 'original_submission': 'one'}
    data.intent = intent
    data.creation = SimpleNamespace(project={'id': 'demo', 'revision': 3}, task_id='task-one',
                                    sha=canonical_sha, check_size=_Creation.check_size)

    async def lookup(saved, run_id):
        assert saved is intent and run_id == 'original-run'
        data.looked_up += 1
        if data.failure:
            raise data.failure
        return Handle(), data.description, object()

    submission = SimpleNamespace(creation=data.creation, spec={'request_sha256': 'a' * 64, 'profile_sha256': 'b' * 64},
                                 submitted=lambda: (intent, 'original-run'), lookup_run=lookup)
    monkeypatch.setattr(reference_task_events, '_Submission', lambda payload: submission)
    data.payload = {'run_id': 'original-run', 'limit': 2, 'after': None}
    return data


def read(data, **changes):
    return asyncio.run(reference_task_events._events({**data.payload, **changes}))


def change_cursor(after, **changes):
    value = json.loads(base64.urlsafe_b64decode(after))
    return base64.urlsafe_b64encode(json.dumps({**value, **changes}).encode()).decode()


def test_physical_page_remainders_and_changed_limits_never_skip_or_duplicate(event_history):
    data, after, observed = event_history, None, []
    for limit in (2, 1, 3, 100, 20):
        result = read(data, limit=limit, after=after)
        assert len(result['events']) <= limit
        assert len(data.pages) == data.looked_up == len(observed) + 1
        observed.append(result)
        after = result['next_after']
        if after is None:
            break
    rows = [event for result in observed for event in result['events']]
    assert [r['event_id'] for r in rows] == list(range(1, 10))
    assert data.pages == [(b'', 2), (b'', 2), (b'', 2), (b'4', 2), (b'8', 2)]
    assert observed[-1]['at_current_end'] and not observed[-1]['has_more'] and after is None
    assert rows[2]['activity'] == {'id': 'activity-three', 'type': 'dev_submit'}
    assert rows[3]['scheduled_event_id'] == 3 and rows[4]['signal_name'] == 'approve_plan'
    assert all(r['time'] is None for r in rows)
    assert 'private-' not in json.dumps(observed) and all(r['execution_success'] is None and r['read_only'] for r in observed)


def test_live_tail_replays_its_page_and_sees_appends_then_closes(event_history):
    from temporalio.client import WorkflowExecutionStatus

    data = event_history
    retained = list(data.events)
    data.events = retained[:3]
    data.description.status = WorkflowExecutionStatus.RUNNING
    first = read(data, limit=100)
    assert [r['event_id'] for r in first['events']] == [1, 2, 3]
    assert not first['has_more'] and first['at_current_end'] and first['next_after']
    empty = read(data, limit=100, after=first['next_after'])
    assert empty['events'] == [] and empty['next_after'] == first['next_after']
    data.events = retained[:5]
    appended = read(data, limit=100, after=empty['next_after'])
    assert [r['event_id'] for r in appended['events']] == [4] and appended['has_more']
    tail = read(data, limit=100, after=appended['next_after'])
    assert [r['event_id'] for r in tail['events']] == [5] and not tail['has_more']
    data.description.status = WorkflowExecutionStatus.COMPLETED
    closed = read(data, limit=100, after=tail['next_after'])
    assert closed['events'] == [] and closed['terminal'] and closed['next_after'] is None
    assert all(size <= 20 for _, size in data.pages)


@pytest.mark.parametrize('change', [
    {'version': True}, {'scope': 'different-submission'}, {'page_size': 21}, {'offset': -1},
    {'next_event_id': 1.0}, {'page_token': 42}, {'page_token': '!invalid!'},
])
def test_invalid_cursor_stops_before_remote_lookup(event_history, change):
    data = event_history
    first = read(data)
    calls = data.looked_up
    with pytest.raises(ValueError, match='Invalid task event cursor'):
        read(data, after=change_cursor(first['next_after'], **change))
    assert data.looked_up == calls


@pytest.mark.parametrize('after', ['not base64', 'bnVsbA==', 'e30='])
def test_non_cursor_encodings_are_not_silently_reset(event_history, after):
    with pytest.raises(ValueError, match='Invalid task event cursor'):
        read(event_history, after=after)
    assert event_history.looked_up == 0


def test_wrong_run_is_not_adopted_and_missing_run_is_distinct_from_rpc_failure(event_history):
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError, RPCStatusCode

    data = event_history
    with pytest.raises(ValueError, match='pin the original'):
        read(data, run_id='another-run')
    assert data.looked_up == 0
    data.failure = RuntimeNotFound()
    missing = read(data)
    assert missing['runtime_status'] == 'not_found' and 'events' not in missing
    data.failure = RPCError('unavailable', RPCStatusCode.UNAVAILABLE, b'')
    with pytest.raises(RPCError):
        read(data)
    assert not data.pages


def test_cursor_anchor_and_page_gaps_fail_without_reset_or_extra_fetch(event_history):
    data = event_history
    first = read(data)
    with pytest.raises(ValueError, match='original page'):
        read(data, after=change_cursor(first['next_after'], offset=100))
    with pytest.raises(ValueError, match='original page'):
        read(data, after=change_cursor(first['next_after'], next_event_id=99))
    data.events[2].event_id = 99
    with pytest.raises(ValueError, match='not continuous'):
        read(data, after=first['next_after'])
    assert len(data.pages) == 4


def test_oversized_metadata_and_unroundtrippable_service_cursor_fail_visibly(event_history):
    data = event_history
    data.events[0].ClearField('workflow_execution_started_event_attributes')
    with pytest.raises(ValueError, match='original prefix'):
        read(data)
    data.events[0].workflow_execution_started_event_attributes.SetInParent()
    data.events[4].workflow_execution_signaled_event_attributes.signal_name = 'x' * 1_048_576
    first = read(data, limit=100)
    with pytest.raises(ValueError, match='Task events exceeds'):
        read(data, limit=100, after=first['next_after'])
    data.events[4].workflow_execution_signaled_event_attributes.signal_name = 'approve_plan'
    data.next_token = b'x' * 8192
    with pytest.raises(ValueError, match='cursor exceeds'):
        read(data, limit=100)
