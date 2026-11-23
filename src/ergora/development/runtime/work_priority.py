"""Prioritize a pending original unit through an outcome-bearing Temporal Update."""

import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import sys

from ergora.development.inputs import PreparationDAGInput
from ergora.development.runtime.submission import _Submission
from ergora.storage.state import State, file_lock


class _WorkPriority:
    def __init__(self, payload):
        from .workflows import PreparationDAGWorkflow, WORK_PRIORITY_UPDATE_ID_PREFIX

        self.payload = payload
        self.submission = _Submission(payload)
        self.creation = self.submission.creation
        self.intent, self.run_id = self.submission.submitted()
        if self.run_id != payload['run_id']:
            raise ValueError('Work priority must pin the original submitted run ID')
        if not isinstance(self.submission.input, PreparationDAGInput):
            raise ValueError('Work priority requires the current budgeted preparation workflow')
        self.workflow = PreparationDAGWorkflow
        self.decision_id = self.creation.core.slug(payload['decision_id'])
        self.update_id = WORK_PRIORITY_UPDATE_ID_PREFIX + self.decision_id
        self.attempt_path = self.creation.path(
            'ergora/task-submissions/' + self.creation.task_id + '.priority-' + self.decision_id + '.attempt.json')
        self.rpc_timeout = timedelta(seconds=payload['timeout'])

    def attempt(self, revision: int, unit: str, plan: str) -> dict:
        from dev_platform.contracts import SHA256

        if type(revision) is not int or revision < 1 or type(plan) is not str or not SHA256.fullmatch(plan):
            raise ValueError('Work priority requires an exact project revision and plan digest')
        command = {'decision_id': self.decision_id, 'work_unit_id': self.creation.core.slug(unit),
                   'run_id': self.run_id, 'request_sha256': self.submission.spec['request_sha256'],
                   'admission_sha256': self.submission.input.document['sha256'], 'plan_sha256': plan,
                   'project_revision': revision}
        return {'schema_version': 1, 'project': self.creation.project['id'],
                'workflow_id': self.intent['workflow_id'], 'submission_sha256': self.creation.sha(self.intent),
                'update_id': self.update_id, 'command': command}

    def load(self) -> dict | None:
        saved = self.creation.optional(self.attempt_path, 4096)
        if saved is not None:
            command = saved['command']
            expected = self.attempt(command['project_revision'], command['work_unit_id'], command['plan_sha256'])
            if self.creation.sha(saved) != self.creation.sha(expected):
                raise ValueError('Work priority attempt conflicts with its original submission, run or command')
        return saved

    def status(self, status: str, attempt: dict | None = None, **detail) -> dict:
        result = {'status': status, 'project': self.creation.project['id'], 'task_id': self.creation.task_id,
                  'workflow_id': self.intent['workflow_id'], 'run_id': self.run_id,
                  'project_revision': self.creation.project['revision'],
                  'decision_id': self.decision_id, 'update_id': self.update_id, 'attempt_saved': attempt is not None}
        if attempt is not None:
            command = attempt['command']
            result.update(project_revision=command['project_revision'], work_unit_id=command['work_unit_id'],
                          plan_sha256=command['plan_sha256'],
                          command_sha256=self.creation.sha(command))
        return {**result, **detail}

    def reserve(self, attempt: dict) -> bool:
        state = State(Path(self.payload['control_home']))
        with state.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if state.project(self.creation.project['id']) != self.creation.project:
                raise ValueError('Project revision changed; reload before prioritizing work')
            with file_lock(self.creation.lock_path, blocking=False):
                saved = self.load()
                if saved is not None:
                    self.require_same(saved, attempt)
                    return False
                self.creation.core.write(self.attempt_path, attempt)
                descriptor = os.open(self.attempt_path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        return True

    def require_same(self, saved: dict, expected: dict) -> None:
        if self.creation.sha(saved) != self.creation.sha(expected):
            raise ValueError('Work priority decision ID is already bound to a different command')

    async def outcome(self, attempt, result):
        from temporalio.client import WorkflowUpdateFailedError, WorkflowUpdateRPCTimeoutOrCancelledError
        from temporalio.service import RPCError

        try:
            outcome = await result
        except WorkflowUpdateRPCTimeoutOrCancelledError:
            return self.status('unknown', attempt, reason='Update result timed out; inspect this original decision')
        except WorkflowUpdateFailedError:
            return self.status('unknown', attempt, reason='Worker did not return a work-priority outcome')
        except RPCError as error:
            return self.status('unknown', attempt, reason='Original update outcome unavailable: ' + error.status.name)
        if type(outcome) is not dict or outcome.get('command_sha256') != self.creation.sha(attempt['command']):
            raise ValueError('Temporal Update outcome differs from the recorded work priority command')
        if outcome.keys() == {'status', 'command_sha256'} and outcome['status'] == 'applied':
            return self.status('applied', attempt)
        if (outcome.keys() == {'status', 'command_sha256', 'reason'} and outcome['status'] == 'rejected'
                and isinstance(outcome['reason'], str) and 0 < len(outcome['reason']) <= 256):
            return self.status('rejected', attempt, reason=outcome['reason'])
        raise ValueError('Invalid original work priority outcome')

    async def observe(self, attempt, handle=None):
        from dev_platform.runtime import RuntimeNotFound
        from temporalio.service import RPCError

        if handle is None:
            try:
                handle, _, _ = await self.submission.lookup_run(self.intent, self.run_id)
            except RuntimeNotFound:
                return self.status('unknown', attempt, reason='Original run history is unavailable')
            except RPCError as error:
                return self.status('unknown', attempt, reason='Original run observation failed: ' + error.status.name)
        update = handle.get_update_handle(self.update_id, workflow_run_id=self.run_id, result_type=dict)
        return await self.outcome(attempt, update.result(rpc_timeout=self.rpc_timeout))

    async def run(self) -> dict:
        from dev_platform.runtime import RuntimeNotFound
        from temporalio.client import WorkflowExecutionStatus

        saved = self.load()
        if self.payload['operation'] == 'inspect':
            return self.status('not_recorded') if saved is None else await self.observe(saved)
        if self.payload['operation'] != 'prioritize':
            raise ValueError('Unknown work priority operation')
        attempt = self.attempt(self.creation.project['revision'], self.payload['work_unit_id'], self.payload['plan_sha256'])
        if saved is not None:
            self.require_same(saved, attempt)
            return await self.observe(saved)
        try:
            handle, description, _ = await self.submission.lookup_run(self.intent, self.run_id)
        except RuntimeNotFound as error:
            raise ValueError('Work priority requires the verified original running task') from error
        if description.status != WorkflowExecutionStatus.RUNNING:
            return self.status('rejected', reason='Original task run is closed')
        observed = await handle.query(self.workflow.status, rpc_timeout=self.rpc_timeout)
        command = attempt['command']
        if (observed['request_sha256'] != command['request_sha256']
                or observed['admission_sha256'] != command['admission_sha256']):
            raise ValueError('Work priority status differs from the recorded task admission')
        queue = observed.get('work_priority')
        if queue is None:
            return self.status('unsupported', reason='The original run worker does not expose work priority')
        if not queue['available']:
            return self.status('rejected', reason=queue['unavailable_reason'])
        if observed['plan_sha256'] != command['plan_sha256'] or command['work_unit_id'] not in queue['pending_work_unit_ids']:
            return self.status('rejected', reason='Work priority must select the approved plan and a pending original unit')
        if not self.reserve(attempt):
            return await self.observe(attempt, handle)
        return await self.outcome(attempt, handle.execute_update(self.workflow.prioritize_work_unit, command,
            id=self.update_id, rpc_timeout=self.rpc_timeout))


def main() -> None:
    from agent_platform.core import Blocked, environment
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        os.environ.update(environment())
        operation = _WorkPriority(payload)
        result = asyncio.run(asyncio.wait_for(operation.run(), timeout=payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Work priority timed out; inspect the original decision') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: Work priority RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error)) from error
