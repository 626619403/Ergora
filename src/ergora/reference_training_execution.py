"""Explicit execution and parallel supervision behind the existing training owners."""

import asyncio
import getpass
import os
from pathlib import Path
import time
import uuid

from . import training_execution_protocol as protocol
from .reference_training_runtime import MEMO_KEY, lookup, observe
from .state import State, file_lock


class Execution:
    def __init__(self, operation, budget):
        self.operation, self.budget = operation, budget

    async def check(self, context: dict):
        from perf_temporal.connection import connect
        from perf_temporal.models import Binding

        op, budget = self.operation, self.budget
        op.registration()
        budget.require_active(owner=True)
        chain = protocol.ExecutionRecords(context['project'], op.ident, str(op.payload['control_home'])).load()
        if chain.owner is None or chain.owner.get('execution_capability') is None:
            raise ValueError('This original budget owner has no execution capability; it cannot be upgraded or restarted')
        protocol.validate_context(context, chain)
        actor = (context['authorization']['controller']['actor_id'] if context['authorization']['schema_version'] in (2, 3)
                 else f'unix:{os.getuid()}:{getpass.getuser()}')
        request = chain.request_record(actor)
        # These checks run in a supervised helper, never inside a DB reservation.
        timeout = min(op.payload['timeout'], budget.remaining(context), context['policy']['control_timeout_seconds'])
        if timeout <= 0:
            raise ValueError('Original computation budget is exhausted')
        client = await connect()
        source = op.payload.get('cycle_operation')
        if source is not None and client.namespace != source['activity_context']['service_namespace']:
            raise ValueError('Execution runtime namespace differs from its authenticated SDK activity service')
        await budget.check_controller_history(client)
        found = await lookup(client, context['intent']['observation']['experiment']['spec'],
                             run_id=request['run_id'], timeout=timeout)
        if found is None or (await found[1].memo()).get(MEMO_KEY) != budget.identity['intent_sha256']:
            raise ValueError('Original submitted run has no matching complete history and intent memo')
        control = await observe(*found, Binding(**context['intent']['observation']['experiment']['spec']['binding']), timeout=timeout)
        if (control.get('terminal') is not False or control.get('phase') != 'QUEUED'
                or control['status']['job_id'] != request['job_id']):
            raise ValueError('Managed execution requires the original QUEUED run and exact native job')
        self.current(context, chain)
        return chain, request

    def current(self, context: dict, chain) -> None:
        op = self.operation
        if State(Path(op.payload['control_home'])).project(op.project['id'])['revision'] != context['intent']['project_revision']:
            raise ValueError('Project revision changed before explicit execution')
        current = protocol.ExecutionRecords(context['project'], op.ident, str(op.payload['control_home'])).load()
        protocol._match(current.owner, chain.owner, 'Original execution publication owner')
        parent = protocol.validate_context(context, current)
        for path in (chain.folder.parent / 'started.json', chain.folder.parent / 'result.json',
                     chain.root / ('training/fences/' + op.ident + '.json')):
            if path.exists() or path.is_symlink():
                raise ValueError('Native execution, result or fence already exists; do not execute again')
        source = op.payload.get('cycle_operation')
        if source is not None:
            protocol.cycle_execution_source(source, context['intent'])
            if parent is not None:
                parent.check()
            # All synchronous source/identity reads above consume this same window.
            # Coroutine cancellation cannot protect the following synchronous publish.
            if protocol.cycle_operation_remaining(source) <= 0:
                raise ValueError('Original execution request operation window is exhausted')

    async def request(self) -> dict:
        op, budget = self.operation, self.budget
        context = budget.context()
        chain, request = await self.check(context)
        payload = op.payload
        if (payload['confirm'] is not True or payload['expected_revision'] != request['project_revision']
                or payload['intent_sha256'] != request['start_intent_sha256']
                or payload['run_id'] != request['run_id']
                or payload['request_sha256'] != request['native_request_sha256']):
            raise ValueError('Explicit execution must confirm the complete original revision, intent, run and native request SHA256')
        chain.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        with budget.permission():
            with file_lock(chain.folder / 'execution.lock', blocking=False):
                self.current(context, chain)
                protocol.publish(chain.folder / 'request.json', request, chain.root)
                self.current(context, chain)
        saved = protocol.ExecutionRecords(context['project'], op.ident, str(op.payload['control_home'])).load()
        return {'project': op.project['id'], 'project_revision': request['project_revision'], 'experiment_id': op.ident,
                'status': 'requested', 'request_sha256': saved.sha(request), 'run_id': request['run_id'],
                'execution': saved.observe(), 'instruction': 'Observe this original request; never resend the native start'}

    async def admit(self, context: dict) -> dict:
        folder = self.operation.root / ('training/jobs/' + self.operation.ident + '/managed-execution')
        while True:
            self.budget.require_active(owner=True)
            if not ((folder / 'request.json').exists() or (folder / 'request.json').is_symlink()):
                await asyncio.sleep(.1)
                continue
            chain, request = await self.check(context)
            if chain.sha(chain.records['request']) != chain.sha(request):
                raise ValueError('Explicit execution request differs from its original identity')
            try:
                with self.budget.permission(), file_lock(chain.folder / 'execution.lock', blocking=False):
                    self.current(context, chain)
                    # Even an empty or partial existing launch consumes this opportunity.
                    try:
                        (chain.folder / 'launch.json').lstat()
                    except FileNotFoundError:
                        pass
                    else:
                        raise ValueError('Original execution launch is already consumed; observe it without relaunching')
                    launch = {'schema_version': 1, 'kind': 'training-execution-launch', 'protocol': protocol.PROTOCOL,
                        'request_sha256': chain.sha(request), 'owner_sha256': chain.sha(chain.owner),
                        'authorization_sha256': chain.owner['authorization_sha256'],
                        'clock_sha256': chain.sha(context['authorization']['clock']),
                        'launch_id': uuid.uuid4().hex, 'execution_phase_id': uuid.uuid4().hex}
                    protocol.publish(chain.folder / 'launch.json', launch, chain.root)
                    self.current(context, chain)
                    return {'status': 'admitted', 'request': request, 'launch': launch}
            except BlockingIOError:
                # The original writer can retain its lock after request becomes
                # visible. Wait within this helper's original compute allowance.
                await asyncio.sleep(.1)

    def drive(self, context: dict, phase_type) -> dict:
        """Interleave the original phase lifecycles without waiting on peer storage."""
        budget, phases, outcome, execution = self.budget, {}, None, None
        stopping = False

        def start(mode, **kwargs):
            phase = phase_type(budget, mode, context, **kwargs)
            try:
                if phase.start():
                    phases[mode] = phase
                    return True
                reason = 'Original training phase did not start within its allowance'
            except OSError as error:
                reason = 'Original training phase startup failed: ' + str(error)
            budget.record_phase(phase, {'status': 'unknown', 'reason': reason})
            return False

        def stop_work():
            for mode, phase in phases.items():
                if mode in ('monitor', 'admission', 'execute'):
                    phase.request_stop()
            # Deliver the stop before a fence launch can wait on process creation.
            for mode, phase in phases.items():
                if mode in ('monitor', 'admission', 'execute'):
                    phase.poll()

        def stop_and_fence():
            nonlocal stopping, outcome
            stopping = True
            stop_work()
            if not start('fence'):
                outcome = {'status': 'unknown', 'reason': 'Original fence phase did not start; cleanup remains unconfirmed'}

        try:
            if not start('monitor') or not start('admission'):
                stop_and_fence()
            while phases or outcome is None:
                try:
                    expired = budget.remaining(context) <= 0
                except (OSError, ValueError):
                    expired = True
                if not stopping and outcome is None and (expired or budget.cancelled):
                    stop_and_fence()
                for mode, phase in list(phases.items()):
                    if phase.poll():
                        continue
                    result = phase.finish()
                    budget.record_phase(phase, result)
                    del phases[mode]
                    if mode == 'admission' and not stopping and outcome is None and result.get('status') == 'admitted':
                        launch = result['launch']
                        # Receipt of this one complete in-memory grant is not replayable.
                        if not budget.cancelled and budget.remaining(context) > 0:
                            if not start('execute', phase_id=launch['execution_phase_id'], execution=result):
                                stop_and_fence()
                    elif mode == 'execute':
                        execution = result.get('execution')
                    elif mode == 'monitor' and not stopping and outcome is None:
                        if result.get('status') == 'completed':
                            outcome = result
                            stop_work()
                        else:
                            stop_and_fence()
                    elif mode == 'fence':
                        outcome = result
                        if result.get('status') == 'fenced':
                            if not start('cleanup'):
                                outcome = {**outcome, 'control': {'status': 'unknown',
                                    'reason': 'Original control cleanup phase did not start'}}
                    elif mode == 'cleanup':
                        outcome = {**(outcome or {}), 'control': result}
                time.sleep(.02)
        finally:
            for phase in phases.values():
                phase.request_stop()
            while phases:
                for mode, phase in list(phases.items()):
                    if not phase.poll():
                        result = phase.finish()
                        budget.record_phase(phase, result)
                        del phases[mode]
                time.sleep(.02)
        return {**(outcome or {'status': 'unknown'}), 'execution': execution,
                'executor_stop_confirmed': execution.get('executor_stop_confirmed') if execution else None}
