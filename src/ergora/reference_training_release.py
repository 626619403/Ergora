"""Checkpoint one native owner decision; uncertain release delivery is never resent."""

import asyncio
from contextlib import redirect_stdout
from dataclasses import asdict
from datetime import timedelta
import getpass
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace
import uuid

from .reference_history import find_signal_event
from .reference_training_context import _native_bytes
from .reference_training_submission import _MEMO_KEY, _Submission
from .state import file_lock


class _Release:
    def __init__(self, payload: dict):
        self.payload = payload
        self.submission = _Submission(payload)
        self.submission.registration()
        self.start = self.submission.load()
        submitted = self.submission.status(self.start)
        if submitted['status'] != 'submitted':
            raise ValueError('Recover the original training start receipt before approving its evidence')
        self.core, self.sha = self.submission.core, self.submission.sha
        self.run_id = submitted['run_id']
        self.spec = self.start['observation']['experiment']['spec']
        self.prefix = 'ergora/training-approvals/' + self.submission.ident

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

    def record(self, revision: int, evidence: str, actor: str, operation_id: str, files: dict) -> dict:
        if (type(revision) is not int or revision < 1 or not isinstance(evidence, str)
                or re.fullmatch('[a-f0-9]{64}', evidence) is None
                or not isinstance(operation_id, str) or re.fullmatch('[a-f0-9]{32}', operation_id) is None
                or not isinstance(actor, str) or not actor.strip() or not isinstance(files, dict)):
            raise ValueError('Invalid saved training approval identity')
        return {**self.submission.identity, 'operation': 'approve', 'project_revision': revision,
                'submission_sha256': self.sha(self.start), 'run_id': self.run_id,
                'evidence_sha256': evidence, 'actor_id': actor, 'operation_id': operation_id, 'files': files}

    def load(self) -> dict | None:
        intent = self.optional('.intent.json')
        if intent is None and any(self.path(suffix).exists() for suffix in
                                  ('.receipt-attempt.json', '.receipt-ready.json', '.attempt.json', '.result.json')):
            intent = self.optional('.intent.json')
            if intent is None:
                raise ValueError('Training approval checkpoints have no original intent')
        if intent is not None and self.sha(intent) != self.sha(self.record(
                intent['project_revision'], intent['evidence_sha256'], intent['actor_id'],
                intent['operation_id'], intent['files'])):
            raise ValueError('Training approval intent differs from its original project, submission or run')
        return intent

    def signal(self, intent: dict) -> dict:
        return {'binding': self.spec['binding'], 'evidence_sha': intent['evidence_sha256'],
                'approval_receipt_id': 'owner-' + intent['operation_id']}

    def attempt(self, intent: dict) -> dict:
        return {'schema_version': 1, 'intent_sha256': self.sha(intent), 'workflow_id': intent['workflow_id'],
                'run_id': self.run_id, 'signal_name': 'request_release', 'signal_sha256': self.sha(self.signal(intent))}

    def owner_attempt(self, intent: dict, digest: str, expires: float) -> dict:
        return {**self.ready(intent, digest, expires), 'operation': 'create_owner_receipt'}

    def ready(self, intent: dict, digest: str, expires: float) -> dict:
        if (not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None
                or type(expires) is not float or not math.isfinite(expires) or expires <= 0):
            raise ValueError('Invalid original owner receipt checkpoint')
        return {'schema_version': 1, 'intent_sha256': self.sha(intent),
                'approval_receipt_id': self.signal(intent)['approval_receipt_id'],
                'receipt_sha256': digest, 'expires_at': expires}

    def receipt(self, intent: dict, delivery: str, event_id: int | None = None) -> dict:
        if not ((delivery == 'acknowledged' and event_id is None)
                or (delivery == 'history' and type(event_id) is int and event_id > 0)):
            raise ValueError('Invalid training release delivery evidence')
        return {**self.attempt(intent), 'delivery': delivery, 'history_event_id': event_id}

    def status(self, intent: dict | None) -> dict:
        result = {'project': self.submission.project['id'], 'project_revision': self.submission.project['revision'],
                  'experiment_id': self.submission.ident, 'workflow_id': self.start['workflow_id'], 'run_id': self.run_id,
                  'runtime_status': 'not_queried', 'authorization_status': 'not_evaluated',
                  'integration_verified': None, 'execution_success': None}
        if intent is None:
            return {**result, 'status': 'not_recorded', 'release_requested': False}
        receipt, attempt, ready, owner_attempt = (self.optional(suffix) for suffix in
                                    ('.result.json', '.attempt.json', '.receipt-ready.json', '.receipt-attempt.json'))
        if owner_attempt is not None and self.sha(owner_attempt) != self.sha(self.owner_attempt(
                intent, owner_attempt['receipt_sha256'], owner_attempt['expires_at'])):
            raise ValueError('Owner receipt creation attempt conflicts with the original approval intent')
        if ready is not None and (owner_attempt is None or self.sha(ready) != self.sha(
                self.ready(intent, owner_attempt['receipt_sha256'], owner_attempt['expires_at']))):
            raise ValueError('Owner receipt checkpoint conflicts with the original approval intent')
        if attempt is not None and (ready is None or self.sha(attempt) != self.sha(self.attempt(intent))):
            raise ValueError('Training release attempt has no matching original owner receipt checkpoint')
        if receipt is not None and (attempt is None or self.sha(receipt) != self.sha(
                self.receipt(intent, receipt.get('delivery'), receipt.get('history_event_id')))):
            raise ValueError('Training release result has no matching original attempt')
        return {**result, 'status': 'requested' if receipt else 'unknown' if attempt else 'prepared',
                'intent_sha256': self.sha(intent), 'evidence_sha256': intent['evidence_sha256'],
                'actor_id': intent['actor_id'], 'owner_receipt': ready,
                'owner_receipt_status': 'recorded' if ready else 'unknown' if owner_attempt else 'not_attempted',
                'attempt_saved': attempt is not None,
                'result_saved': receipt is not None, 'signal_delivery': receipt['delivery'] if receipt else None,
                'release_requested': True if receipt else None if attempt else False}

    def preflight(self, intent: dict | None = None) -> dict:
        from .reference_training_evidence import inspect

        observed = inspect({**self.payload, 'artifact': None})
        if (observed['archive_status'] != 'recorded' or not observed['baseline_matches'] or observed['fence_recorded']):
            raise ValueError('Training approval requires the original accepted archive, matching current baseline and no fence')
        current_spec = self.submission.document(self.submission.root, 'training/specs/' + self.submission.ident + '.json')
        if self.sha(current_spec) != self.sha(self.spec):
            raise ValueError('Training approval spec differs from the original submitted experiment')
        if intent is not None and (observed['archive']['evidence_sha256'] != intent['evidence_sha256']
                                  or observed['files'] != intent['files']):
            raise ValueError('Training approval sources changed after the original decision; do not renew or replace it')
        return observed

    async def lookup(self):
        from perf_temporal.connection import connect
        from .reference_training_runtime import lookup
        from temporalio.client import WorkflowExecutionStatus

        client = await connect()
        found = await lookup(client, self.spec, run_id=self.run_id, timeout=self.payload['timeout'])
        if found is None:
            raise ValueError('Original training approval run was not found; preserve its decision and reconcile')
        handle, description = found
        if (await description.memo()).get(_MEMO_KEY) != self.sha(self.start):
            raise ValueError('Original training run has no matching start intent memo')
        return handle, description.status == WorkflowExecutionStatus.RUNNING, client.data_converter

    def dispatch(self, intent: dict) -> dict:
        from agent_platform import training as owner
        from perf_temporal import client as native, connection

        if intent['actor_id'] != self.actor():
            raise ValueError('Training approval actor changed; do not impersonate the original owner')
        self.preflight(intent)
        receipt_id = self.signal(intent)['approval_receipt_id']
        owner_path = self.submission.adapter.safe_file(self.submission.root, 'training/approvals/' + receipt_id + '.json')
        original_connect, original_native_connect = connection.connect, native.connect
        original_uuid, original_write, original_subprocess = owner.uuid, owner.write, owner.subprocess
        original_argv = sys.argv
        timeout = timedelta(seconds=self.payload['timeout'])

        async def connect():
            # lookup uses the original connector while both original CLI stages
            # receive only a handle pinned to the complete original run.
            connection.connect = original_connect
            try:
                handle, running, _ = await asyncio.wait_for(self.lookup(), self.payload['timeout'])
            finally:
                connection.connect = connect
            if not running:
                raise ValueError('Original training run is closed; no new release signal was sent')

            async def query(method, **kwargs):
                return await asyncio.wait_for(handle.query(method, rpc_timeout=timeout, **kwargs), self.payload['timeout'])

            async def signal(method, value, **kwargs):
                if self.sha(asdict(value)) != self.sha(self.signal(intent)):
                    raise ValueError('Native release differs from its original owner decision')
                self.preflight(intent)
                check_owner()
                self.core.write(self.path('.attempt.json'), self.attempt(intent))
                await handle.signal(method, value, rpc_timeout=timeout, **kwargs)

            def fixed_handle(workflow_id, **kwargs):
                if workflow_id != intent['workflow_id']:
                    raise ValueError('Native approval selected another workflow')
                return SimpleNamespace(query=query, signal=signal)

            return SimpleNamespace(get_workflow_handle=fixed_handle,
                                   get_workflow_handle_for=lambda _method, workflow_id: fixed_handle(workflow_id))

        def check_owner() -> dict:
            raw = self.submission.adapter.read_raw(owner_path)
            value = json.loads(raw)
            expected = {'binding': self.spec['binding'], 'evidence_sha256': intent['evidence_sha256'],
                        'decision': 'approve', 'role': 'owner', 'actor_id': intent['actor_id'],
                        'expires_at': value['expires_at'], 'revoked': False}
            if (self.sha(value) != self.sha(expected) or owner_path.stat().st_uid != os.getuid()
                    or owner_path.stat().st_mode & 0o077 or not time.time() < value['expires_at']):
                raise ValueError('Original owner receipt identity, privacy, expiry or revocation changed; no renewal is allowed')
            ready = self.ready(intent, hashlib.sha256(raw).hexdigest(), value['expires_at'])
            created = self.optional('.receipt-attempt.json')
            if created is None or self.sha(ready) != self.sha(self.ready(
                    intent, created['receipt_sha256'], created['expires_at'])):
                raise ValueError('Original owner receipt bytes or expiry differ from the creation attempt')
            return ready

        def write(path, value):
            if Path(path) != owner_path:
                raise ValueError('Native approval attempted an unrelated write')
            if self.optional('.receipt-attempt.json') is None:
                if owner_path.exists():
                    raise ValueError('Owner receipt has no original creation attempt; do not adopt it')
                self.core.write(self.path('.receipt-attempt.json'), self.owner_attempt(
                    intent, hashlib.sha256(_native_bytes(value, 'Native owner receipt')).hexdigest(), value['expires_at']))
                original_write(path, value)
            elif not owner_path.exists():
                raise ValueError('Original owner receipt creation is uncertain or missing; do not mint a replacement')
            # A restart retains the original bytes and expiry. The worker still
            # evaluates the original receipt; this is only a delivery checkpoint.
            self.core.write(self.path('.receipt-ready.json'), check_owner())

        def release(argv, **kwargs):
            expected = [str(owner.PYTHON), '-m', 'perf_temporal.client', 'release',
                        str(owner.TRAINING / 'specs' / (self.submission.ident + '.json')),
                        '--receipt-id', receipt_id, '--evidence-sha', intent['evidence_sha256']]
            if argv != expected:
                raise ValueError('Native approval selected a different release command')
            sys.argv = ['perf_temporal.client', *argv[3:]]
            asyncio.run(asyncio.wait_for(native.main(), self.payload['timeout']))
            return SimpleNamespace(returncode=0)

        try:
            connection.connect = native.connect = connect
            owner.uuid = SimpleNamespace(uuid4=lambda: SimpleNamespace(hex=intent['operation_id']))
            owner.write, owner.subprocess = write, SimpleNamespace(run=release)
            with redirect_stdout(io.StringIO()):
                owner.cli(['approve', self.submission.ident, '--evidence-sha', intent['evidence_sha256']])
        finally:
            connection.connect, native.connect = original_connect, original_native_connect
            owner.uuid, owner.write, owner.subprocess, sys.argv = original_uuid, original_write, original_subprocess, original_argv
        self.core.write(self.path('.result.json'), self.receipt(intent, 'acknowledged'))
        return self.status(intent)

    async def reconcile(self, intent: dict) -> dict:
        handle, _, converter = await self.lookup()
        event_id = await find_signal_event(handle, converter, 'request_release', self.signal(intent))
        if event_id is not None:
            self.core.write(self.path('.result.json'), self.receipt(intent, 'history', event_id))
            return self.status(intent)
        return {**self.status(intent), 'reconciliation': 'signal_not_found',
                'instruction': 'Delivery remains uncertain; preserve this decision, do not resend or mint a new owner receipt'}

    def run(self) -> dict:
        operation = self.payload['operation']
        if operation == 'status':
            return self.status(self.load())
        if operation not in ('prepare', 'prepare-resume', 'dispatch', 'resume'):
            raise ValueError('Unsupported training approval operation')
        lock = self.path('.lock')
        lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with file_lock(lock, blocking=False):
            intent = self.load()
            if operation == 'prepare':
                if self.payload['run_id'] != self.run_id:
                    raise ValueError('Training approval must pin the original submitted run ID')
                if intent is not None:
                    if intent['evidence_sha256'] != self.payload['evidence_sha256']:
                        raise ValueError('This experiment already has a different original owner decision')
                    return {'created': False, 'approval': self.status(intent)}
                observed = self.preflight()
                if observed['archive']['evidence_sha256'] != self.payload['evidence_sha256']:
                    raise ValueError('Confirm the exact original archived evidence SHA-256')
                intent = self.record(self.submission.project['revision'], self.payload['evidence_sha256'],
                                     self.actor(), uuid.uuid4().hex, observed['files'])
                self.core.write(self.path('.intent.json'), intent)
                return {'created': True, 'approval': self.status(intent)}
            if intent is None or self.sha(intent) != self.payload['intent_sha256']:
                raise ValueError('Training approval recovery requires the exact original intent SHA-256')
            status = self.status(intent)
            if operation == 'prepare-resume' or status['status'] == 'requested':
                return status
            from temporalio.service import RPCError

            try:
                if status['attempt_saved']:
                    return asyncio.run(asyncio.wait_for(self.reconcile(intent), self.payload['timeout'])) if operation == 'resume' else status
                return self.dispatch(intent)
            except RPCError as error:
                raise ValueError('Training release RPC failed: ' + error.status.name) from error


def main() -> None:
    from agent_platform.core import Blocked, environment

    try:
        payload = json.load(sys.stdin)
        if payload['operation'] in ('dispatch', 'resume'):
            os.environ.update(environment())
        result = _Release(payload).run()
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Training release timed out; preserve the original owner decision and reconcile') from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))


if __name__ == '__main__':
    main()
