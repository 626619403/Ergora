"""Checkpoint cancellation delivery; observe the original control and executor separately."""

import asyncio
from contextlib import redirect_stdout
from dataclasses import asdict
import getpass
import io
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from .reference_history import find_signal_event
from .reference_training_submission import _MEMO_KEY, _Submission
from .state import file_lock


class _Cancellation:
    def __init__(self, payload: dict):
        self.payload = payload
        self.submission = _Submission(payload)
        self.submission.registration()
        self.start = self.submission.load()
        submitted = self.submission.status(self.start)
        if submitted['status'] != 'submitted':
            raise ValueError('Recover the original training start receipt before cancelling or observing its stop')
        self.core, self.sha = self.submission.core, self.submission.sha
        self.run_id = submitted['run_id']
        self.spec = self.start['observation']['experiment']['spec']
        self.request_id = self.core.slug(payload['request_id']) if 'request_id' in payload else None
        self.prefix = 'ergora/training-cancellations/' + self.submission.ident + '/' + str(self.request_id)

    def path(self, suffix: str) -> Path:
        return self.submission.adapter.safe_file(self.submission.root, self.prefix + suffix)

    def optional(self, suffix: str) -> dict | None:
        try:
            return self.submission.document(self.submission.root, self.prefix + suffix)
        except FileNotFoundError:
            return None

    @staticmethod
    def actor() -> str:
        return f'unix:{os.getuid()}:{getpass.getuser()}'

    def record(self, revision: int, reason: str, actor: str) -> dict:
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
            raise ValueError('Cancellation requires a nonempty reason of at most 1000 characters')
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError('Saved training cancellation actor is invalid')
        return {**self.submission.identity, 'operation': 'cancel', 'project_revision': revision,
                'submission_sha256': self.sha(self.start), 'run_id': self.run_id,
                'request_id': self.request_id, 'reason': reason, 'actor_id': actor}

    def load(self) -> dict | None:
        intent = self.optional('.intent.json')
        if intent is None and any(self.path(suffix).exists() for suffix in ('.attempt.json', '.result.json')):
            intent = self.optional('.intent.json')
            if intent is None:
                raise ValueError('Training cancellation checkpoints have no original intent')
        if intent is None:
            return None
        revision = intent.get('project_revision')
        if type(revision) is not int or revision < 1:
            raise ValueError('Invalid saved training cancellation revision')
        if self.sha(intent) != self.sha(self.record(revision, intent['reason'], intent['actor_id'])):
            raise ValueError('Training cancellation intent differs from its original project, submission or run')
        return intent

    def signal(self, intent: dict) -> dict:
        return {'binding': self.spec['binding'], 'reason': intent['reason'],
                'ergora_operation_sha256': self.sha(intent)}

    def attempt(self, intent: dict) -> dict:
        return {'schema_version': 1, 'intent_sha256': self.sha(intent),
                'workflow_id': intent['workflow_id'], 'run_id': intent['run_id'],
                'signal_name': 'request_cancel', 'signal_sha256': self.sha(self.signal(intent))}

    def receipt(self, intent: dict, delivery: str, event_id: int | None = None) -> dict:
        if not ((delivery == 'acknowledged' and event_id is None)
                or (delivery == 'history' and type(event_id) is int and event_id > 0)):
            raise ValueError('Invalid training cancellation signal evidence')
        return {**self.attempt(intent), 'delivery': delivery, 'history_event_id': event_id}

    def closed_receipt(self, intent: dict, temporal_status: str) -> dict:
        # This local receipt reader must remain usable without the optional SDK.
        if temporal_status not in {'COMPLETED', 'FAILED', 'CANCELED', 'TERMINATED', 'CONTINUED_AS_NEW', 'TIMED_OUT'}:
            raise ValueError('A running or unrecognized workflow cannot have a closed cancellation receipt')
        return {**self.attempt(intent), 'delivery': 'not_sent', 'temporal_status': temporal_status}

    def status(self, intent: dict | None) -> dict:
        result = {'project': self.submission.project['id'], 'project_revision': self.submission.project['revision'],
                  'experiment_id': self.submission.ident, 'request_id': self.request_id,
                  'workflow_id': self.start['workflow_id'], 'run_id': self.run_id,
                  'runtime_status': 'not_queried', 'cancellation_confirmed': None, 'execution_success': None}
        if intent is None:
            return {**result, 'status': 'not_recorded', 'cancel_requested': False}
        receipt, attempt = self.optional('.result.json'), self.optional('.attempt.json')
        if attempt is not None and self.sha(attempt) != self.sha(self.attempt(intent)):
            raise ValueError('Training cancellation attempt conflicts with its original intent')
        closed = receipt is not None and receipt.get('delivery') == 'not_sent'
        if receipt is not None:
            expected = (self.closed_receipt(intent, receipt['temporal_status']) if closed
                        else self.receipt(intent, receipt.get('delivery'), receipt.get('history_event_id')))
            if (attempt is None) != closed or self.sha(receipt) != self.sha(expected):
                raise ValueError('Training cancellation receipt has no matching original checkpoint')
        return {**result, 'status': 'already_closed' if closed else 'requested' if receipt else 'unknown' if attempt else 'prepared',
                'intent_sha256': self.sha(intent), 'reason': intent['reason'],
                'attempt_saved': attempt is not None, 'result_saved': receipt is not None,
                'cancel_requested': False if closed or attempt is None else True if receipt else None,
                'signal_delivery': receipt['delivery'] if receipt else None,
                'temporal_status': receipt['temporal_status'] if closed else None}

    async def lookup(self):
        from perf_temporal.connection import connect
        from .reference_training_runtime import lookup

        client = await connect()
        found = await lookup(client, self.spec, run_id=self.run_id, timeout=self.payload['timeout'])
        if found is None:
            raise ValueError('Original training cancellation run was not found; preserve its request and reconcile')
        handle, description = found
        if (await description.memo()).get(_MEMO_KEY) != self.sha(self.start):
            raise ValueError('Original training run has no matching start intent memo')
        return handle, description, client.data_converter

    async def dispatch(self, intent: dict) -> dict:
        from perf_temporal import client as native
        from temporalio.client import WorkflowExecutionStatus

        if intent['actor_id'] != self.actor():
            raise ValueError('Training cancellation actor changed; do not impersonate the original request')
        handle, description, _ = await self.lookup()
        if description.status != WorkflowExecutionStatus.RUNNING:
            self.core.write(self.path('.result.json'), self.closed_receipt(intent, description.status.name))
            return self.status(intent)

        async def signal(method, value, **kwargs):
            if self.sha(asdict(value)) != self.sha({'binding': self.spec['binding'], 'reason': intent['reason']}):
                raise ValueError('Native cancellation input differs from its frozen request')
            self.core.write(self.path('.attempt.json'), self.attempt(intent))
            await handle.signal(method, self.signal(intent), **kwargs)

        def fixed_handle(_method, workflow_id):
            if workflow_id != intent['workflow_id']:
                raise ValueError('Native cancellation selected another workflow')
            return SimpleNamespace(query=handle.query, signal=signal)

        async def connect():
            return SimpleNamespace(get_workflow_handle_for=fixed_handle)

        original_connect, original_argv = native.connect, sys.argv
        try:
            # Keep the original client loader/validation, without depending on
            # the current mutable spec path or rewriting any native original.
            with TemporaryDirectory(prefix='ergora-training-cancel-') as temporary:
                source = Path(temporary) / 'experiment.json'
                source.write_text(json.dumps(self.spec, allow_nan=False), encoding='utf-8')
                native.connect = connect
                sys.argv = ['perf_temporal.client', 'cancel', str(source), '--reason=' + intent['reason']]
                with redirect_stdout(io.StringIO()):
                    await native.main()
        finally:
            native.connect, sys.argv = original_connect, original_argv
        self.core.write(self.path('.result.json'), self.receipt(intent, 'acknowledged'))
        return self.status(intent)

    async def reconcile(self, intent: dict) -> dict:
        handle, _, converter = await self.lookup()
        event_id = await find_signal_event(handle, converter, 'request_cancel', self.signal(intent))
        if event_id is not None:
            self.core.write(self.path('.result.json'), self.receipt(intent, 'history', event_id))
            return self.status(intent)
        return {**self.status(intent), 'reconciliation': 'signal_not_found',
                'instruction': 'Delivery remains uncertain; do not resend this request or change its ID to bypass it'}

    async def stop_status(self) -> dict:
        from perf_temporal.adapter import load_adapter
        from perf_temporal.models import Binding, Experiment
        from .reference_training_runtime import observe

        handle, description, _ = await self.lookup()
        control = await observe(handle, description, Binding(**self.spec['binding']), timeout=self.payload['timeout'])
        adapter = load_adapter()
        experiment = Experiment(**{**self.spec, 'binding': Binding(**self.spec['binding'])})
        job = await adapter.lookup_job(experiment)
        executor = asdict(await adapter.poll_job(job)) if job is not None else None
        try:
            fence = self.submission.document(self.submission.root, 'training/fences/' + self.submission.ident + '.json')
        except FileNotFoundError:
            fence = None
        if fence is not None and fence != {'binding': self.spec['binding']}:
            raise ValueError('Saved training fence differs from the original binding')
        return {'project': self.submission.project['id'], 'project_revision': self.submission.project['revision'],
                'experiment_id': self.submission.ident, 'workflow_id': self.start['workflow_id'], 'run_id': self.run_id,
                'control': control, 'executor_observation': executor, 'fence_recorded': fence is not None,
                'execution_success': None, 'read_only': True,
                'scope': 'Original control outcome, native adapter observation and saved fence are separate facts; no OS stop or adoption claim'}

    async def run(self) -> dict:
        operation = self.payload['operation']
        if operation == 'stop-status':
            return await self.stop_status()
        if operation == 'status':
            return self.status(self.load())
        if operation not in ('prepare', 'prepare-resume', 'dispatch', 'resume'):
            raise ValueError('Unsupported training cancellation operation')
        lock = self.path('.lock')
        lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with file_lock(lock, blocking=False):
            intent = self.load()
            if operation == 'prepare':
                if self.payload['run_id'] != self.run_id:
                    raise ValueError('Training cancellation must pin the original submitted run ID')
                if intent is not None:
                    if intent['reason'] != self.payload['reason']:
                        raise ValueError('Request ID already names a different training cancellation reason')
                    return {'created': False, 'cancellation': self.status(intent)}
                intent = self.record(self.submission.project['revision'], self.payload['reason'], self.actor())
                self.core.write(self.path('.intent.json'), intent)
                return {'created': True, 'cancellation': self.status(intent)}
            if intent is None or self.sha(intent) != self.payload['intent_sha256']:
                raise ValueError('Training cancellation recovery requires the exact original request intent SHA')
            status = self.status(intent)
            if operation == 'prepare-resume' or status['status'] in ('requested', 'already_closed'):
                return status
            if status['attempt_saved']:
                return await self.reconcile(intent) if operation == 'resume' else status
            return await self.dispatch(intent)


def main() -> None:
    from agent_platform.core import Blocked, environment

    try:
        payload = json.load(sys.stdin)
        operation = _Cancellation(payload)
        if payload['operation'] in ('dispatch', 'resume', 'stop-status'):
            from temporalio.service import RPCError

            os.environ.update(environment())
            try:
                result = asyncio.run(asyncio.wait_for(operation.run(), payload['timeout']))
            except RPCError as error:
                raise ValueError('Training cancellation RPC failed: ' + error.status.name) from error
        else:
            result = asyncio.run(asyncio.wait_for(operation.run(), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Training cancellation timed out; preserve the original request and reconcile') from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))


if __name__ == '__main__':
    main()
