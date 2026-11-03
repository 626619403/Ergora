"""Exact owner approval with immutable intent and original-run signal reconciliation."""

import asyncio
from datetime import timedelta
import getpass
import json
import os
import re
import sys
import time
import uuid

from .reference_task_submission import _Submission
from .state import file_lock


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
        self.submission.prepare()
        self.start_intent = self.submission.load()
        status = self.submission.status(self.start_intent)
        if status['status'] != 'submitted':
            raise ValueError('Approval requires the original recorded submission; inspect task submission first')
        self.run_id = status['run_id']
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
        async for event in handle.fetch_history_events(page_size=100, rpc_timeout=timedelta(seconds=20)):
            if not event.HasField('workflow_execution_signaled_event_attributes'):
                continue
            signal = event.workflow_execution_signaled_event_attributes
            if signal.signal_name != 'approve_plan':
                continue
            values = await converter.decode(signal.input.payloads, [dict])
            if self.sha(values) == self.sha([self.signal(intent)]):
                self.core.write(self.result_path, self.receipt(intent, 'history', event.event_id))
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
    """Only the network phase holds a task lock; it never holds the control DB."""
    from agent_platform.core import Blocked, environment
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        if payload['operation'] not in ('status', 'prepare', 'prepare-resume'):
            os.environ.update(environment())
        result = asyncio.run(asyncio.wait_for(_Approval(payload).run(), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Approval timed out; inspect the original decision ID and resume its saved intent') from error
    except RuntimeNotFound as error:
        raise SystemExit('BLOCKED: Original approval run was not found; preserve this decision and reconcile the original run') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: Approval RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
