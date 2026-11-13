"""Cooperative cancellation with an immutable request and original-run evidence."""

import asyncio
import getpass
import json
import os
import sys
from types import SimpleNamespace

from .reference_history import find_signal_event
from .reference_task_runtime import VerifiedSpecClient
from .reference_task_submission import _Submission
from .state import file_lock


class _Cancellation:
    def __init__(self, payload: dict):
        self.payload = payload
        self.submission = _Submission(payload)
        self.creation = self.submission.creation
        self.core, self.sha = self.creation.core, self.creation.sha
        self.request_id = self.core.slug(payload['request_id'])
        prefix = 'ergora/task-cancellations/' + self.creation.task_id + '/' + self.request_id
        self.intent_path = self.creation.path(prefix + '.intent.json')
        self.attempt_path = self.creation.path(prefix + '.attempt.json')
        self.result_path = self.creation.path(prefix + '.result.json')

    def prepare(self) -> None:
        self.start_intent, self.run_id = self.submission.submitted()
        self.spec = self.submission.spec

    @staticmethod
    def actor() -> str:
        return f'unix:{os.getuid()}:{getpass.getuser()}'

    def record(self, revision: int, reason: str, actor: str) -> dict:
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
            raise ValueError('Cancellation requires a nonempty reason of at most 1000 characters')
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError('Saved cancellation actor is invalid')
        return {**self.submission.expected, 'operation': 'cancel', 'project_revision': revision,
                'submission_sha256': self.sha(self.start_intent), 'run_id': self.run_id,
                'request_id': self.request_id, 'reason': reason, 'actor_id': actor}

    def load(self) -> dict | None:
        record = self.creation.optional(self.intent_path)
        if record is None:
            if self.attempt_path.exists() or self.result_path.exists():
                raise ValueError('Cancellation records have no original intent; reconcile before requesting again')
            return None
        if type(record.get('project_revision')) is not int or record['project_revision'] < 1:
            raise ValueError('Invalid saved cancellation revision')
        expected = self.record(record['project_revision'], record['reason'], record['actor_id'])
        if self.sha(record) != self.sha(expected):
            raise ValueError('Cancellation intent conflicts with its original project, submission or run')
        return record

    def signal(self, intent: dict) -> dict:
        return {'request_sha256': self.spec['request_sha256'], 'reason': intent['reason'],
                'ergora_operation_sha256': self.sha(intent)}

    def attempt(self, intent: dict) -> dict:
        return {'schema_version': 1, 'intent_sha256': self.sha(intent), 'workflow_id': intent['workflow_id'],
                'run_id': intent['run_id'], 'signal_name': 'request_cancel', 'signal_sha256': self.sha(self.signal(intent))}

    def receipt(self, intent: dict, delivery: str, event_id: int | None) -> dict:
        if not ((delivery == 'acknowledged' and event_id is None)
                or (delivery == 'history' and type(event_id) is int and event_id > 0)):
            raise ValueError('Invalid cancellation signal evidence')
        return {**self.attempt(intent), 'delivery': delivery, 'history_event_id': event_id}

    def closed_receipt(self, intent: dict, temporal_status: str) -> dict:
        from temporalio.client import WorkflowExecutionStatus

        if WorkflowExecutionStatus[temporal_status] == WorkflowExecutionStatus.RUNNING:
            raise ValueError('A running workflow cannot have a closed cancellation receipt')
        return {**self.attempt(intent), 'delivery': 'not_sent', 'temporal_status': temporal_status}

    def status(self, intent: dict | None) -> dict:
        result = {'project': self.creation.project['id'], 'project_revision': self.creation.project['revision'],
                  'task_id': self.creation.task_id, 'request_id': self.request_id, 'run_id': self.run_id,
                  'runtime_status': 'not_queried', 'cancellation_confirmed': None, 'execution_success': None}
        if intent is None:
            return {**result, 'status': 'not_recorded', 'cancel_requested': False}
        receipt = self.creation.optional(self.result_path)
        attempt = self.creation.optional(self.attempt_path)
        if attempt is not None and self.sha(attempt) != self.sha(self.attempt(intent)):
            raise ValueError('Cancellation attempt conflicts with its original intent')
        closed = receipt is not None and receipt.get('delivery') == 'not_sent'
        if receipt is not None:
            if closed:
                expected = self.closed_receipt(intent, receipt['temporal_status'])
            else:
                expected = self.receipt(intent, receipt.get('delivery'), receipt.get('history_event_id'))
            if (attempt is None) != closed or self.sha(receipt) != self.sha(expected):
                raise ValueError('Cancellation result conflicts with its original intent or signal checkpoint')
        return {**result, 'workflow_id': intent['workflow_id'], 'intent_sha256': self.sha(intent),
                'status': 'already_closed' if closed else 'requested' if receipt is not None else 'unknown' if attempt is not None else 'prepared',
                'reason': intent['reason'], 'attempt_saved': attempt is not None, 'result_saved': receipt is not None,
                'cancel_requested': False if closed or attempt is None else True if receipt is not None else None,
                'signal_delivery': receipt['delivery'] if receipt is not None else None,
                'temporal_status': receipt['temporal_status'] if closed else None}

    async def dispatch(self, intent: dict) -> dict:
        from dev_platform.connection import connect, task_queue
        from dev_platform.runtime import DevelopmentTransport

        if intent['actor_id'] != self.actor():
            raise ValueError('Cancellation actor changed; the original request cannot be impersonated')
        operation = self
        acknowledged = False

        class RecordedCancellation(DevelopmentTransport):
            async def lookup(self, spec, run_id=None):
                handle, description = await super().lookup(spec, run_id)
                await operation.submission.verify_run_owner(operation.start_intent, description)
                self.description = description

                async def signal(method, payload, **kwargs):
                    nonlocal acknowledged
                    operation.core.write(operation.attempt_path, operation.attempt(intent))
                    await handle.signal(method, {**payload, 'ergora_operation_sha256': operation.sha(intent)}, **kwargs)
                    acknowledged = True

                return SimpleNamespace(signal=signal), description

        runtime = RecordedCancellation(VerifiedSpecClient(await connect(), self.submission.input.document), task_queue())
        await runtime.cancel(self.spec, intent['run_id'], intent['reason'])
        receipt = (self.receipt(intent, 'acknowledged', None) if acknowledged else
                   self.closed_receipt(intent, runtime.description.status.name))
        self.core.write(self.result_path, receipt)
        return self.status(intent)

    async def reconcile(self, intent: dict) -> dict:
        handle, _, converter = await self.submission.lookup_run(self.start_intent, intent['run_id'])
        event_id = await find_signal_event(handle, converter, 'request_cancel', self.signal(intent))
        if event_id is not None:
            self.core.write(self.result_path, self.receipt(intent, 'history', event_id))
            return self.status(intent)
        return {**self.status(intent), 'reconciliation': 'signal_not_found',
                'instruction': 'Delivery remains uncertain; query the original run, do not resend this request'}

    async def run(self) -> dict:
        operation = self.payload['operation']
        if operation == 'status':
            self.prepare()
            return self.status(self.load())
        preparing = operation in ('prepare', 'prepare-resume')
        with file_lock(self.creation.lock_path, blocking=not preparing):
            self.prepare()
            intent = self.load()
            if operation == 'prepare':
                if self.payload['run_id'] != self.run_id:
                    raise ValueError('Cancellation must pin the original submitted run ID')
                if intent is not None:
                    if intent['reason'] != self.payload['reason']:
                        raise ValueError('Request ID already names a different reason; inspect its original intent')
                    return {'created': False, 'cancellation': self.status(intent)}
                intent = self.record(self.creation.project['revision'], self.payload['reason'], self.actor())
                self.core.write(self.intent_path, intent)
                return {'created': True, 'cancellation': self.status(intent)}
            if intent is None or self.sha(intent) != self.payload['intent_sha256']:
                raise ValueError('Cancellation recovery requires the exact original request intent digest')
            status = self.status(intent)
            if operation == 'prepare-resume':
                return status
            if operation not in ('dispatch', 'resume'):
                raise ValueError('Unsupported cancellation operation')
            if status['status'] in ('requested', 'already_closed'):
                return status
            if status['attempt_saved']:
                return await self.reconcile(intent) if operation == 'resume' else status
            return await self.dispatch(intent)


def main() -> None:
    """Keep cancellation side effects under the task lock and outside the control DB."""
    from agent_platform.core import Blocked, environment
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        if payload['operation'] not in ('status', 'prepare', 'prepare-resume'):
            os.environ.update(environment())
        result = asyncio.run(asyncio.wait_for(_Cancellation(payload).run(), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Cancellation timed out; inspect the original request ID and resume its saved intent') from error
    except RuntimeNotFound as error:
        raise SystemExit('BLOCKED: Original cancellation run was not found; preserve this request and reconcile the original run') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: Cancellation RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
