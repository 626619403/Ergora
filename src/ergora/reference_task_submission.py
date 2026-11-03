"""Submit once through native admission; reconcile uncertain delivery by original ID."""

import asyncio
import json
import os
import sys
from types import SimpleNamespace

from .reference_task_creation import _Creation
from .reference_task_runtime import VerifiedSpecClient
from .state import file_lock


_MEMO_KEY = 'ergora.submission_sha256'


class _Submission:
    def __init__(self, payload: dict):
        self.payload = payload
        self.creation = _Creation(payload)
        self.core = self.creation.core
        self.sha = self.creation.sha
        prefix = 'ergora/task-submissions/' + self.creation.task_id
        self.intent_path = self.creation.path(prefix + '.intent.json')
        self.attempt_path = self.creation.path(prefix + '.attempt.json')
        self.result_path = self.creation.path(prefix + '.result.json')
        self.rejection_path = self.creation.path(prefix + '.rejection.json')

    def prepare(self) -> None:
        from dev_platform.workflow import workflow_id

        record = self.creation.published()
        self.spec = record['files']['task.spec.json']
        self.expected = {'schema_version': 1, 'operation': 'start',
                         'control_home': record['control_home'], 'project': record['project'],
                         'project_revision': self.creation.project['revision'],
                         'registration_sha256': record['registration_sha256'], 'execution': record['execution'],
                         'task_id': self.creation.task_id, 'creation_sha256': self.sha(record),
                         'spec_sha256': self.sha(self.spec), 'workflow_id': workflow_id(self.spec)}

    def load(self) -> dict | None:
        record = self.creation.optional(self.intent_path)
        if record is not None:
            if (type(record.get('project_revision')) is not int or record['project_revision'] < 1
                    or self.sha(record) != self.sha({**self.expected, 'project_revision': record['project_revision']})):
                raise ValueError('Submission intent conflicts with its original task, project or control directory')
        elif any(path.exists() for path in (self.attempt_path, self.result_path, self.rejection_path)):
            raise ValueError('Submission records have no original intent; reconcile before starting')
        return record

    def attempt(self, intent: dict) -> dict:
        return {'schema_version': 1, 'intent_sha256': self.sha(intent),
                'workflow_id': intent['workflow_id'], 'spec_sha256': intent['spec_sha256']}

    def receipt(self, intent: dict, run_id: str) -> dict:
        if not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id:
            raise ValueError('Native start did not return a valid run ID; reconcile the original workflow')
        return {**self.attempt(intent), 'run_id': run_id}

    def rejection(self, intent: dict, reason: str, run_id: str | None) -> dict:
        if reason in ('preexisting_run', 'start_conflict') and run_id is not None:
            return {**self.receipt(intent, run_id), 'reason': reason}
        if reason in ('lookup_rejected', 'start_conflict') and run_id is None:
            return {**self.attempt(intent), 'run_id': None, 'reason': reason}
        raise ValueError('Invalid submission ownership rejection')

    def status(self, intent: dict | None) -> dict:
        result = {'project': self.creation.project['id'], 'project_revision': self.creation.project['revision'],
                  'task_id': self.creation.task_id, 'workflow_id': self.expected['workflow_id'],
                  'run_id': None, 'runtime_status': 'not_queried', 'execution_success': None}
        if intent is None:
            return {**result, 'status': 'not_recorded'}
        # Read completion first: an in-flight writer may then add an attempt or
        # result, but cannot make an observed completion precede its checkpoint.
        receipt = self.creation.optional(self.result_path)
        attempt = self.creation.optional(self.attempt_path)
        rejection = self.creation.optional(self.rejection_path)
        if attempt is not None and self.sha(attempt) != self.sha(self.attempt(intent)):
            raise ValueError('Submission attempt conflicts with its saved intent')
        if rejection is not None:
            if (receipt is not None or (attempt is not None) != (rejection.get('reason') == 'start_conflict') or
                    self.sha(rejection) != self.sha(self.rejection(intent, rejection.get('reason'), rejection.get('run_id')))):
                raise ValueError('Submission ownership rejection conflicts with its saved intent')
            return {**result, 'status': 'rejected', 'intent_sha256': self.sha(intent),
                    'creation_sha256': intent['creation_sha256'], 'reason': rejection['reason'],
                    'conflicting_run_id': rejection['run_id'], 'attempt_saved': attempt is not None, 'result_saved': False}
        if receipt is not None:
            if attempt is None or self.sha(receipt) != self.sha(self.receipt(intent, receipt.get('run_id'))):
                raise ValueError('Submission result conflicts with its saved intent or dispatch checkpoint')
            result['run_id'] = receipt['run_id']
        return {**result, 'status': 'submitted' if receipt is not None else 'unknown' if attempt else 'prepared',
                'intent_sha256': self.sha(intent), 'creation_sha256': intent['creation_sha256'],
                'submitted_revision': intent['project_revision'], 'attempt_saved': attempt is not None,
                'result_saved': receipt is not None}

    async def dispatch(self, intent: dict) -> dict:
        from agent_platform import cli
        from dev_platform import runtime
        from temporalio.exceptions import WorkflowAlreadyStartedError

        operation = self
        original = runtime.DevelopmentTransport
        original_spec = cli.task_spec

        def frozen_spec(task_id):
            spec = original_spec(task_id)
            if operation.sha(spec) != intent['spec_sha256']:
                raise ValueError('Task spec changed after submission preflight; restore the original creation')
            return spec

        class CheckpointedTransport(original):
            async def start(self, spec):
                self.client = VerifiedSpecClient(self.client, operation.spec)
                # Refuse to adopt an independently started run. Once this
                # checkpoint exists, resume must only look up, never start.
                try:
                    _, description = await self.lookup(spec)
                except runtime.RuntimeNotFound:
                    pass
                except ValueError:
                    operation.core.write(operation.rejection_path, operation.rejection(intent, 'lookup_rejected', None))
                    raise
                else:
                    operation.core.write(operation.rejection_path,
                                         operation.rejection(intent, 'preexisting_run', description.run_id))
                    raise ValueError('Workflow already exists without this submission attempt; reconcile its owner')
                operation.core.write(operation.attempt_path, operation.attempt(intent))
                native_start = self.client.start_workflow

                async def exclusive_start(*args, **kwargs):
                    try:
                        return await native_start(*args, memo={_MEMO_KEY: operation.sha(intent)}, **kwargs)
                    except WorkflowAlreadyStartedError as error:
                        # A racing entrance can win after our NOT_FOUND. Do not
                        # let the native compatibility path adopt that run.
                        operation.core.write(operation.rejection_path,
                                             operation.rejection(intent, 'start_conflict', error.run_id))
                        raise ValueError('Workflow was already started during submission; reconcile its owner') from error

                self.client.start_workflow = exclusive_start
                return await super().start(spec)

        # task_action imports this port at call time. The override is confined
        # to this dedicated process and preserves doctor, policy and claim.
        runtime.DevelopmentTransport = CheckpointedTransport
        cli.task_spec = frozen_spec
        try:
            observed = await cli.task_action(SimpleNamespace(operation='start', task_id=self.creation.task_id))
        finally:
            runtime.DevelopmentTransport = original
            cli.task_spec = original_spec
        if observed['workflow_id'] != intent['workflow_id']:
            raise ValueError('Native start returned a different workflow; reconcile the original ID')
        self.core.write(self.result_path, self.receipt(intent, observed['run_id']))
        return self.status(intent)

    async def reconcile(self, intent: dict) -> dict:
        from dev_platform.connection import connect, task_queue
        from dev_platform.runtime import DevelopmentTransport, RuntimeNotFound

        transport = DevelopmentTransport(VerifiedSpecClient(await connect(), self.spec), task_queue())
        try:
            _, description = await transport.lookup(self.spec)
        except RuntimeNotFound:
            return {**self.status(intent), 'reconciliation': 'not_found',
                    'instruction': 'Dispatch remains uncertain; do not resubmit or change the task ID to bypass it'}
        # Memo is decoded from the describe response, with no extra RPC. The
        # fixed native workflow never upserts it. This associates recovery with
        # our original start even if saving a known conflict's rejection failed.
        if (await description.memo()).get(_MEMO_KEY) != self.sha(intent):
            raise ValueError('Workflow has no matching submission memo; its ownership remains unconfirmed')
        self.core.write(self.result_path, self.receipt(intent, description.run_id))
        return self.status(intent)

    async def run(self) -> dict:
        operation = self.payload['operation']
        if operation == 'status':
            self.prepare()
            return self.status(self.load())
        # Share creation's per-task lock so publication and native operations
        # cannot observe one another halfway. Project revision is reserved by
        # the parent use case; all native writes belong to this client process.
        with file_lock(self.creation.lock_path):
            self.prepare()
            intent = self.load()
            if operation == 'start':
                if self.payload['creation_sha256'] != self.expected['creation_sha256']:
                    raise ValueError('Creation intent digest changed; inspect creation before starting')
                if intent is not None:
                    return self.status(intent)
                for path in (self.creation.target / 'cli-ingress.json',
                             self.creation.path('requests/' + self.creation.task_id),
                             self.creation.path('receipts/' + self.creation.task_id)):
                    if path.exists():
                        raise ValueError('Native admission or stage records already exist; legacy runs cannot be adopted')
                intent = self.expected
                self.core.write(self.intent_path, intent)
            elif operation == 'resume':
                if intent is None or self.payload['intent_sha256'] != self.sha(intent):
                    raise ValueError('Resume requires the exact original submission intent digest')
                status = self.status(intent)
                if status['status'] in ('submitted', 'rejected'):
                    return status
                if status['attempt_saved']:
                    return await self.reconcile(intent)
            else:
                raise ValueError('Unsupported task submission operation')
            return await self.dispatch(intent)


def main() -> None:
    """Load full native dependencies only for explicit Linux submission/recovery."""
    from agent_platform.core import Blocked, environment

    try:
        payload = json.load(sys.stdin)
        if payload['operation'] != 'status':
            os.environ.update(environment())
        result = asyncio.run(asyncio.wait_for(_Submission(payload).run(), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Submission timed out; inspect task submission and resume its original intent') from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
