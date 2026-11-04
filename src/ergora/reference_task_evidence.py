"""Read a selected original job's published receipt and bounded UTF-8 evidence."""

import asyncio
from datetime import timedelta
import hashlib
import json
import os
import sys

from .reference_task_submission import _Submission


async def _job(payload: dict) -> dict:
    from dev_platform.adapter import identifier
    from dev_platform.runtime import RuntimeNotFound

    submission = _Submission(payload)
    intent, run_id = submission.submitted()
    creation, spec = submission.creation, submission.spec
    if payload['run_id'] != run_id:
        raise ValueError('Job evidence must pin the original submitted run ID')
    identity = {'schema_version': 1, 'project': creation.project['id'],
                'project_revision': creation.project['revision'], 'task_id': creation.task_id,
                'workflow_id': intent['workflow_id'], 'run_id': run_id,
                'request_sha256': spec['request_sha256'], 'profile_sha256': spec['profile_sha256'],
                'history_event_id': payload['event_id'], 'read_only': True, 'execution_success': None,
                'workflow_receipt_accepted': None}
    try:
        handle, description, converter = await submission.lookup_run(intent, run_id)
    except RuntimeNotFound:
        return {**identity, 'runtime_status': 'not_found'}

    next_id = 1
    async for event in handle.fetch_history_events(page_size=100, rpc_timeout=timedelta(seconds=20)):
        if (event.event_id != next_id or next_id == 1
                and not event.HasField('workflow_execution_started_event_attributes')):
            raise ValueError('Job evidence requires the original continuous history prefix')
        next_id += 1
        if event.event_id == payload['event_id']:
            break
    else:
        raise ValueError('Selected job event is absent from the currently visible original history')
    if (not event.HasField('activity_task_scheduled_event_attributes')
            or event.activity_task_scheduled_event_attributes.activity_type.name != 'dev_submit'):
        raise ValueError('Select an original dev_submit activity scheduling event')
    scheduled = event.activity_task_scheduled_event_attributes
    if len(scheduled.input.payloads) != 1:
        raise ValueError('Original job event has no single context')
    values = await converter.decode(scheduled.input.payloads, [dict])
    if len(values) != 1 or not isinstance(values[0], dict):
        raise ValueError('Original job event has no single context')
    context = values[0]
    if (context['task_id'] != creation.task_id or context['request_sha256'] != spec['request_sha256']
            or context['profile_sha256'] != spec['profile_sha256'] or creation.sha(context['spec']) != creation.sha(spec)
            or not isinstance(context['stage'], str)
            or context['stage'].split(':', 1)[0] not in spec['profile']['artifacts_by_stage']):
        raise ValueError('Original job event context differs from the recorded task spec')
    job_id = identifier(context['job_id'])
    job_sha = creation.sha(context)
    adapter = creation.file_adapter()
    envelope = creation.document(adapter.path('requests', creation.task_id + '/' + job_id + '.json'))
    if creation.sha(envelope) != creation.sha({'schema_version': 1, 'job_id': job_id,
                                             'job_sha256': job_sha, 'context': context}):
        raise ValueError('Job request envelope differs from its original history context')
    job = {'task_id': creation.task_id, 'job_id': job_id, 'job_sha256': job_sha, 'context': context}
    receipt = await adapter.poll(job)
    result = {**identity, 'runtime_status': 'queried', 'temporal_status': description.status.name,
              'job_id': job_id, 'job_sha256': job_sha, 'stage': context['stage'],
              'receipt_status': 'published' if receipt is not None else 'missing',
              'receipt_sha256': creation.sha(receipt) if receipt is not None else None,
              'receipt': receipt, 'artifact': None, 'artifact_limit_bytes': 16_777_216,
              'history_limit_events': 10_000, 'response_limit_bytes': 1_048_576}
    if payload['artifact'] is not None:
        if receipt is None or creation.sha(receipt) != payload['receipt_sha256']:
            raise ValueError('Job receipt differs from the selected original observation')
        artifact = next((item for item in receipt['artifacts'] if item['name'] == payload['artifact']), None)
        if artifact is None:
            raise ValueError('Selected artifact is absent from the original job receipt')
        raw = creation.adapter.read_raw(adapter.path('artifacts', artifact['path']), 16_777_216)
        if hashlib.sha256(raw).hexdigest() != artifact['sha256']:
            raise ValueError('Artifact bytes do not match the original receipt digest')
        text = raw.decode('utf-8')
        if '\0' in text:
            raise ValueError('Selected artifact contains NUL; only UTF-8 text evidence is supported')
        offset = payload['offset']
        if offset > len(text):
            raise ValueError('Artifact character offset exceeds the original text length')
        stop = min(offset + payload['limit'], len(text))
        result['artifact'] = {'name': artifact['name'], 'sha256': artifact['sha256'], 'bytes': len(raw),
                              'characters': len(text), 'offset': offset, 'limit': payload['limit'],
                              'next_offset': stop if stop < len(text) else None, 'text': text[offset:stop]}
    creation.check_size(result, 1_048_576, 'Job evidence')
    return result


def main() -> None:
    """Inspect only; never publish receipts, signal, execute or change claims/refs."""
    from agent_platform.core import Blocked, environment
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        os.environ.update(environment())
        result = asyncio.run(asyncio.wait_for(_job(payload), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Job evidence query timed out; unread evidence remains unknown') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: Job evidence query RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error)) from error
