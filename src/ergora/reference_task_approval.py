"""Exact owner approval with immutable intent and original-run signal reconciliation."""

import asyncio
from datetime import timedelta
import getpass
import hashlib
import json
import os
import re
import sys
import time
import uuid

from .reference_task_submission import _Submission
from .reference_task_runtime import find_signal_event
from .state import file_lock


async def _plan(payload: dict) -> dict:
    from dev_platform.adapter import identifier
    from dev_platform.workflow import DevelopmentWorkflow

    submission = _Submission(payload)
    intent, run_id = submission.submitted()
    creation, spec = submission.creation, submission.spec
    if payload['run_id'] != run_id:
        raise ValueError('Plan inspection must pin the original submitted run ID')
    handle, description, converter = await submission.lookup_run(intent, run_id)
    if description.status.name != 'RUNNING':
        raise ValueError('Plan inspection requires an original run awaiting an owner decision')
    status = await handle.query(DevelopmentWorkflow.status, rpc_timeout=timedelta(seconds=20))
    if (status['phase'] != 'AWAITING_PLAN_APPROVAL' or status['request_sha256'] != spec['request_sha256']
            or status['plan_sha256'] != payload['plan_sha256']):
        raise ValueError('Plan inspection requires the exact plan currently awaiting an owner decision')

    next_event = 1
    async for event in handle.fetch_history_events(page_size=100, rpc_timeout=timedelta(seconds=20)):
        if (event.event_id != next_event
                or next_event == 1 and not event.HasField('workflow_execution_started_event_attributes')):
            raise ValueError('Plan inspection requires the original history prefix')
        next_event += 1
        if not event.HasField('activity_task_scheduled_event_attributes'):
            continue
        scheduled = event.activity_task_scheduled_event_attributes
        if scheduled.activity_type.name != submission.input.submit_activity:
            continue
        if len(scheduled.input.payloads) != 1:
            raise ValueError('Original plan history has no single job context')
        values = await converter.decode(scheduled.input.payloads, [dict])
        if len(values) != 1 or not isinstance(values[0], dict):
            raise ValueError('Original plan history has no single job context')
        context = values[0]
        if context.get('stage') != 'plan':
            continue
        if (context['request_sha256'] != spec['request_sha256'] or not submission.input.matches_context(context)):
            raise ValueError('Original plan history differs from the recorded task spec')
        job_id = identifier(context['job_id'])
        break
    else:
        raise ValueError('Original history has no submitted plan job')

    job_sha = creation.sha(context)
    adapter = creation.file_adapter(submission.input)
    envelope = creation.document(adapter.path('requests', creation.task_id + '/' + job_id + '.json'))
    if creation.sha(envelope) != creation.sha({'schema_version': 1, 'job_id': job_id,
                                             'job_sha256': job_sha, 'context': context}):
        raise ValueError('Plan request envelope differs from its original history context')
    receipt = creation.document(creation.path('receipts/' + creation.task_id + '/' + job_id + '.json'))
    # The native workflow hashes its accepted receipt, not an individual plan text.
    # That digest also binds metadata we do not display or revalidate here.
    if (creation.sha(receipt) != payload['plan_sha256'] or receipt['job_id'] != job_id
            or receipt['job_sha256'] != job_sha or receipt['state'] != 'SUCCEEDED'):
        raise ValueError('Plan receipt differs from the exact pending plan or its original job')
    artifacts = {artifact['name']: artifact for artifact in receipt['artifacts']}
    materials = []
    for name in spec['profile']['artifacts_by_stage']['plan']:
        if name not in artifacts:
            raise ValueError('Plan receipt is missing a required review artifact: ' + name)
        artifact = artifacts[name]
        raw = creation.adapter.read_raw(creation.path('artifacts/' + artifact['path']), 262_144)
        if hashlib.sha256(raw).hexdigest() != artifact['sha256']:
            raise ValueError('Plan artifact bytes do not match their receipt digest: ' + name)
        materials.append({'name': name, 'sha256': artifact['sha256'], 'bytes': len(raw), 'text': raw.decode('utf-8')})
    result = {'schema_version': 1, 'project': creation.project['id'], 'project_revision': creation.project['revision'],
              'task_id': creation.task_id, 'workflow_id': intent['workflow_id'], 'run_id': run_id,
              'request_sha256': spec['request_sha256'], 'profile_sha256': spec['profile_sha256'],
              'runtime_status': 'queried', 'phase': status['phase'], 'plan_sha256': payload['plan_sha256'],
              'history_plan_event_id': event.event_id, 'job_sha256': job_sha, 'receipt': receipt,
              'materials': materials, 'artifact_limit_bytes': 262_144, 'read_only': True}
    creation.check_size(result, 1_048_576, 'Plan inspection')
    return result


class _Approval:
    def __init__(self, payload: dict):
        self.payload = payload
        self.submission = _Submission(payload)
        self.creation = self.submission.creation
        self.core, self.sha = self.creation.core, self.creation.sha
        self.decision_id = self.core.slug(payload['decision_id'])
        prefix = 'ergora/task-approvals/' + self.creation.task_id + '/' + self.decision_id
        self.intent_path = self.creation.path(prefix + '.intent.json')
        self.attempt_path = self.creation.path(prefix + '.attempt.json')
        self.result_path = self.creation.path(prefix + '.result.json')

    def prepare(self) -> None:
        self.start_intent, self.run_id = self.submission.submitted()
        self.spec = self.submission.spec

    @staticmethod
    def actor() -> str:
        return f'unix:{os.getuid()}:{getpass.getuser()}'

    def record(self, revision: int, plan: str, receipt_id: str, created_at: int, actor: str) -> dict:
        approval = {'schema_version': 1, 'kind': 'plan-approval', 'task_id': self.creation.task_id,
                    'request_sha256': self.spec['request_sha256'], 'profile_sha256': self.spec['profile_sha256'],
                    'plan_sha256': plan, 'decision': 'approve', 'principal_type': 'human', 'actor_id': actor,
                    'role': 'owner', 'expires_at': created_at + 86400, 'revoked': False}
        return {**self.submission.expected, 'operation': 'approve', 'project_revision': revision,
                'submission_sha256': self.sha(self.start_intent), 'run_id': self.run_id,
                'decision_id': self.decision_id, 'plan_sha256': plan, 'receipt_id': receipt_id,
                'created_at': created_at, 'approval': approval}

    def load(self) -> dict | None:
        record = self.creation.optional(self.intent_path)
        if record is None:
            if self.attempt_path.exists() or self.result_path.exists():
                raise ValueError('Approval records have no original intent; reconcile before any decision')
            return None
        if (type(record.get('project_revision')) is not int or record['project_revision'] < 1
                or type(record.get('created_at')) is not int or record['created_at'] < 1
                or not isinstance(record.get('plan_sha256'), str) or not re.fullmatch('[0-9a-f]{64}', record['plan_sha256'])
                or not isinstance(record.get('receipt_id'), str) or not re.fullmatch('owner-[0-9a-f]{32}', record['receipt_id'])):
            raise ValueError('Invalid saved approval intent')
        actor = record['approval']['actor_id']
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError('Saved owner identity is invalid')
        expected = self.record(record['project_revision'], record['plan_sha256'], record['receipt_id'], record['created_at'], actor)
        if self.sha(record) != self.sha(expected):
            raise ValueError('Approval intent conflicts with its original project, submission, run or owner receipt')
        return record

    def approval_path(self, intent: dict):
        return self.creation.path('approvals/' + intent['receipt_id'] + '.json')

    def signal(self, intent: dict) -> dict:
        return {'request_sha256': self.spec['request_sha256'], 'plan_sha256': intent['plan_sha256'],
                'receipt_id': intent['receipt_id']}

    def attempt(self, intent: dict) -> dict:
        return {'schema_version': 1, 'intent_sha256': self.sha(intent), 'workflow_id': intent['workflow_id'],
                'run_id': intent['run_id'], 'signal_name': 'approve_plan', 'signal_sha256': self.sha(self.signal(intent)),
                'approval_sha256': self.sha(intent['approval'])}

    def receipt(self, intent: dict, delivery: str, event_id: int | None) -> dict:
        if not ((delivery == 'acknowledged' and event_id is None)
                or (delivery == 'history' and type(event_id) is int and event_id > 0)):
            raise ValueError('Invalid approval signal evidence')
        return {**self.attempt(intent), 'delivery': delivery, 'history_event_id': event_id}

    def status(self, intent: dict | None) -> dict:
        result = {'project': self.creation.project['id'], 'project_revision': self.creation.project['revision'],
                  'task_id': self.creation.task_id, 'decision_id': self.decision_id, 'run_id': self.run_id,
                  'runtime_status': 'not_queried', 'approval_accepted': None, 'execution_success': None}
        if intent is None:
            return {**result, 'status': 'not_recorded'}
        receipt = self.creation.optional(self.result_path)
        attempt = self.creation.optional(self.attempt_path)
        approval = self.creation.optional(self.approval_path(intent))
        if approval is not None and self.sha(approval) != self.sha(intent['approval']):
            raise ValueError('Published owner receipt conflicts with its approval intent')
        if attempt is not None and (approval is None or self.sha(attempt) != self.sha(self.attempt(intent))):
            raise ValueError('Approval attempt has missing or inconsistent owner evidence')
        if receipt is not None and (attempt is None or self.sha(receipt) != self.sha(
                self.receipt(intent, receipt.get('delivery'), receipt.get('history_event_id')))):
            raise ValueError('Approval result conflicts with its original intent or signal checkpoint')
        return {**result, 'workflow_id': intent['workflow_id'], 'intent_sha256': self.sha(intent),
                'status': 'requested' if receipt is not None else 'unknown' if attempt is not None else 'prepared',
                'plan_sha256': intent['plan_sha256'], 'owner_receipt_id': intent['receipt_id'],
                'expires_at': intent['approval']['expires_at'], 'owner_receipt_saved': approval is not None,
                'attempt_saved': attempt is not None, 'result_saved': receipt is not None,
                'signal_delivery': receipt['delivery'] if receipt is not None else None}

    async def dispatch(self, intent: dict) -> dict:
        from dev_platform.adapter import publish
        from dev_platform.workflow import DevelopmentWorkflow

        if intent['approval']['actor_id'] != self.actor():
            raise ValueError('Approval owner identity changed; the original decision cannot be impersonated')
        if time.time() >= intent['approval']['expires_at']:
            raise ValueError('Approval expired; inspect the current plan and make a new explicit decision with a new ID')
        handle, _, _ = await self.submission.lookup_run(self.start_intent, intent['run_id'])
        status = await handle.query(DevelopmentWorkflow.status, rpc_timeout=timedelta(seconds=20))
        if (status['phase'] != 'AWAITING_PLAN_APPROVAL' or status['request_sha256'] != self.spec['request_sha256']
                or status['plan_sha256'] != intent['plan_sha256']):
            raise ValueError('Approval must name the exact plan currently awaiting an owner decision')
        publish(self.approval_path(intent), intent['approval'])
        self.core.write(self.attempt_path, self.attempt(intent))
        await handle.signal(DevelopmentWorkflow.approve_plan, self.signal(intent), rpc_timeout=timedelta(seconds=20))
        self.core.write(self.result_path, self.receipt(intent, 'acknowledged', None))
        return self.status(intent)

    async def reconcile(self, intent: dict) -> dict:
        handle, _, converter = await self.submission.lookup_run(self.start_intent, intent['run_id'])
        event_id = await find_signal_event(handle, converter, 'approve_plan', self.signal(intent))
        if event_id is not None:
            self.core.write(self.result_path, self.receipt(intent, 'history', event_id))
            return self.status(intent)
        return {**self.status(intent), 'reconciliation': 'signal_not_found',
                'instruction': 'Delivery remains uncertain; query the original run, do not resend this decision'}

    async def run(self) -> dict:
        operation = self.payload['operation']
        if operation == 'status':
            self.prepare()
            return self.status(self.load())
        preparing = operation in ('prepare', 'prepare-resume')
        # Preparation runs while the parent reserves the project revision. It
        # must never retain the control DB while waiting for a remote task lock.
        with file_lock(self.creation.lock_path, blocking=not preparing):
            self.prepare()
            intent = self.load()
            if operation == 'prepare':
                if self.payload['run_id'] != self.run_id:
                    raise ValueError('Approval must pin the original submitted run ID')
                if intent is not None:
                    if intent['plan_sha256'] != self.payload['plan_sha256']:
                        raise ValueError('Decision ID already names a different plan; inspect its original intent')
                    return {'created': False, 'approval': self.status(intent)}
                intent = self.record(self.creation.project['revision'], self.payload['plan_sha256'],
                                     'owner-' + uuid.uuid4().hex, int(time.time()), self.actor())
                self.core.write(self.intent_path, intent)
                return {'created': True, 'approval': self.status(intent)}
            if intent is None or self.sha(intent) != self.payload['intent_sha256']:
                raise ValueError('Approval recovery requires the exact original decision intent digest')
            status = self.status(intent)
            if operation == 'prepare-resume':
                return status
            if operation not in ('dispatch', 'resume'):
                raise ValueError('Unsupported approval operation')
            if status['status'] == 'requested':
                return status
            if status['attempt_saved']:
                return await self.reconcile(intent) if operation == 'resume' else status
            return await self.dispatch(intent)


def main() -> None:
    """Approval locks only its network phase; plan inspection is read-only."""
    from agent_platform.core import Blocked, environment
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError

    inspecting = False
    try:
        payload = json.load(sys.stdin)
        inspecting = payload['operation'] == 'inspect-plan'
        if payload['operation'] not in ('status', 'prepare', 'prepare-resume'):
            os.environ.update(environment())
        operation = _plan(payload) if inspecting else _Approval(payload).run()
        result = asyncio.run(asyncio.wait_for(operation, payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        if inspecting:
            raise SystemExit('BLOCKED: Plan inspection timed out; query the original run before inspecting again') from error
        raise SystemExit('BLOCKED: Approval timed out; inspect the original decision ID and resume its saved intent') from error
    except RuntimeNotFound as error:
        if inspecting:
            raise SystemExit('BLOCKED: Original plan run was not found; preserve the run ID and query its status') from error
        raise SystemExit('BLOCKED: Original approval run was not found; preserve this decision and reconcile the original run') from error
    except RPCError as error:
        name = 'Plan inspection' if inspecting else 'Approval'
        raise SystemExit('BLOCKED: ' + name + ' RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
