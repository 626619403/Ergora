"""Bounded metadata from the original submitted run, with resumable page positions."""

import asyncio
import base64
from datetime import timedelta
import json
import os
import sys

from .reference_task_submission import _Submission


async def _events(payload: dict) -> dict:
    from temporalio.api.enums.v1 import EventType
    from temporalio.client import WorkflowExecutionStatus
    from dev_platform.runtime import RuntimeNotFound

    submission = _Submission(payload)
    intent, run_id = submission.submitted()
    creation = submission.creation
    if payload['run_id'] != run_id:
        raise ValueError('Task events must pin the original submitted run ID')
    identity = {'schema_version': 1, 'project': creation.project['id'],
                'project_revision': creation.project['revision'], 'task_id': creation.task_id,
                'workflow_id': intent['workflow_id'], 'run_id': run_id,
                'request_sha256': submission.spec['request_sha256'],
                'profile_sha256': submission.spec['profile_sha256'], 'read_only': True,
                'execution_success': None}
    scope = creation.sha({'submission_sha256': creation.sha(intent), 'run_id': run_id})
    token, offset, next_id, page_size = b'', 0, 1, min(payload['limit'], 20)
    if payload['after'] is not None:
        try:
            cursor = json.loads(base64.b64decode(payload['after'].encode('ascii'), altchars=b'-_', validate=True))
            if (not isinstance(cursor, dict) or set(cursor) !=
                    {'version', 'scope', 'page_token', 'page_size', 'offset', 'next_event_id'}
                    or type(cursor['version']) is not int or cursor['version'] != 1 or cursor['scope'] != scope
                    or type(cursor['page_size']) is not int or not 1 <= cursor['page_size'] <= 20
                    or type(cursor['offset']) is not int or cursor['offset'] < 0
                    or type(cursor['next_event_id']) is not int or cursor['next_event_id'] < 1
                    or not isinstance(cursor['page_token'], str)):
                raise ValueError('Cursor differs from the original event scope or position')
            token = base64.b64decode(cursor['page_token'].encode('ascii'), altchars=b'-_', validate=True)
            offset, next_id, page_size = cursor['offset'], cursor['next_event_id'], cursor['page_size']
        except (ValueError, TypeError) as error:
            raise ValueError('Invalid task event cursor') from error
    try:
        handle, description, _ = await submission.lookup_run(intent, run_id)
    except RuntimeNotFound:
        return {**identity, 'runtime_status': 'not_found'}

    history = handle.fetch_history_events(page_size=page_size, next_page_token=token or None,
                                          rpc_timeout=timedelta(seconds=20))
    await history.fetch_next_page()
    page = history.current_page
    if (not token and (not page or page[0].event_id != 1
                      or not page[0].HasField('workflow_execution_started_event_attributes'))):
        raise ValueError('Task event history has no original prefix')
    if offset > len(page) or offset and page[offset - 1].event_id != next_id - 1:
        raise ValueError('Task event cursor no longer matches its original page')
    stop = min(offset + payload['limit'], len(page))
    events = []
    for event in page[offset:stop]:
        if event.event_id != next_id:
            raise ValueError('Task event history is not continuous at the requested position')
        next_id += 1
        row = {'event_id': event.event_id, 'type': EventType.Name(event.event_type).removeprefix('EVENT_TYPE_'),
               'time': event.event_time.ToJsonString() if event.HasField('event_time') else None}
        attributes = event.WhichOneof('attributes')
        if attributes:
            detail = getattr(event, attributes)
            if attributes == 'activity_task_scheduled_event_attributes':
                row['activity'] = {'id': detail.activity_id, 'type': detail.activity_type.name}
            if hasattr(detail, 'scheduled_event_id'):
                row['scheduled_event_id'] = detail.scheduled_event_id
            if attributes == 'workflow_execution_signaled_event_attributes':
                row['signal_name'] = detail.signal_name
        events.append(row)
    has_more = stop < len(page) or history.next_page_token is not None
    terminal = description.status != WorkflowExecutionStatus.RUNNING
    after = None
    if has_more or not terminal:
        # Temporal may return more than page_size. Preserve the unread remainder
        # before advancing; a live tail keeps its page so appends remain visible.
        position_token, position_offset = token, stop
        if stop == len(page) and history.next_page_token is not None:
            position_token, position_offset = history.next_page_token, 0
        cursor = {'version': 1, 'scope': scope, 'page_token': base64.urlsafe_b64encode(position_token).decode('ascii'),
                  'page_size': page_size, 'offset': position_offset, 'next_event_id': next_id}
        after = base64.urlsafe_b64encode(json.dumps(cursor, separators=(',', ':')).encode()).decode('ascii')
        if len(after) > 8192:
            raise ValueError('Task event cursor exceeds 8192 characters')
    result = {**identity, 'runtime_status': 'queried', 'temporal_status': description.status.name,
              'terminal': terminal, 'events': events, 'next_after': after, 'has_more': has_more,
              'at_current_end': not has_more, 'next_event_id': next_id, 'limit': payload['limit'],
              'physical_page_events': len(page), 'response_limit_bytes': 1_048_576}
    creation.check_size(result, 1_048_576, 'Task events')
    return result

def main() -> None:
    """Read-only native entry; never submit, signal, change refs or release claims."""
    from agent_platform.core import Blocked, environment
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        os.environ.update(environment())
        result = asyncio.run(asyncio.wait_for(_events(payload), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Task event query timed out; the unread history remains unknown') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: Task event query RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
