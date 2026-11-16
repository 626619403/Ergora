"""Optional application SDK worker for the versioned, budget-aware training queue."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from contextvars import ContextVar
from dataclasses import asdict
from datetime import timedelta
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

try:
    from temporalio import workflow
except ModuleNotFoundError as error:
    if error.name != 'temporalio':
        raise
    workflow = None

with workflow.unsafe.imports_passed_through() if workflow is not None else nullcontext():
    from . import budget_clock, processes, reference, training_cycles, training_execution_protocol as protocol
    from .reference_training_budget import BudgetedStart, TASK_QUEUE, validate_binding
    from .reference_training_submission import _Submission
    from .reference_training_execution import Execution
    from .state import State, file_lock, now
    from .training_cycles import _CycleCapacityError
    if workflow is not None:
        from temporalio.common import RetryPolicy
        from temporalio.exceptions import ActivityError, ApplicationError


_CREATING = ContextVar('ergora_training_budget_create', default=None)
_CYCLE_LIMIT = 32_768
_ROOT_OBSERVERS = set()


class _RoundRetentionError(RuntimeError):
    pass


def _retain_round_reader(payload: dict, name: str, value: dict) -> None:
    if payload['identity']['mode'] not in protocol.CYCLE_MEASUREMENT_MODES:
        return
    try:
        raw = (json.dumps({'reader': name, 'value': value}, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
        if sys.stderr.buffer.write(raw) != len(raw):
            raise OSError('Complete original reader diagnostic was only partially written')
        sys.stderr.buffer.flush()
    except (OSError, ValueError, TypeError, UnicodeError) as error:
        raise _RoundRetentionError('Complete original round reader diagnostic was not flushed: ' + str(error)) from error


class _CycleOperation:
    """Asynchronously supervise one isolated original-record operation."""

    def __init__(self, home: Path, project: str, cycle_id: str, authorization_sha256: str, mode: str,
                 *, snapshot: dict | None = None, ordinal: int | None = None,
                 reason: str | None = None, inspection_timeout: int = 10,
                 start_context: dict | None = None, window: dict | None = None,
                 activity_context: dict | None = None):
        bootstrap = window
        if mode in protocol.CYCLE_OBSERVATION_MODES and window is None:
            if type(inspection_timeout) is not int or not 1 <= inspection_timeout <= 60:
                raise ValueError('Cold inspection timeout must be 1 to 60 seconds')
            boot, ticks = budget_clock._clock()
            bootstrap = {'boot_id': boot, 'started_ns': ticks,
                         'deadline_ns': ticks + inspection_timeout * 1_000_000_000}
        elif mode in ('prepare-controller', 'submit-controller', 'prepare-candidate', *protocol.CYCLE_MEASUREMENT_MODES) and window is None:
            policy, clock = snapshot['policy'], snapshot['authorization']['clock']
            boot, ticks = budget_clock._clock()
            seconds = min(policy['control_timeout_seconds'], budget_clock.remaining(
                clock, policy['wall_seconds'], policy['cleanup_seconds']))
            bootstrap = {'boot_id': boot, 'started_ns': ticks,
                'deadline_ns': min(ticks + int(seconds * 1_000_000_000), clock['boottime_ns']
                    + (policy['wall_seconds'] - policy['cleanup_seconds']) * 1_000_000_000)}
        self.identity = {'protocol': ('ergora-training-cycle-operation-v2' if mode in
            protocol.CYCLE_MEASUREMENT_MODES else 'ergora-training-cycle-operation-v1'), 'operation_id': uuid.uuid4().hex,
            'mode': mode, 'control_home': str(home), 'project': project, 'cycle_id': cycle_id,
            'input_sha256': snapshot['authorization']['input_sha256'] if snapshot is not None else None,
            'authorization_sha256': authorization_sha256, 'ordinal': ordinal, 'parent': processes.identity(os.getpid())}
        self.payload = {'identity': self.identity, 'snapshot': snapshot, 'bootstrap': bootstrap, 'reason': reason}
        if start_context is not None:
            self.payload['start_context'] = start_context
        if activity_context is not None:
            self.payload['activity_context'] = activity_context
        protocol.validate_cycle_operation(self.payload)
        self.encoded = json.dumps(self.payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if len(self.encoded) > _CYCLE_LIMIT:
            raise _CycleCapacityError('Complete cycle operation request exceeds 32 KiB; nothing was truncated')
        self.output = home / 'operations/training-cycles' / self.identity['operation_id']
        self.response = protocol.PhaseFrames(self.identity, self.output, _CYCLE_LIMIT)
        self.stopping, self.signalled, self.sent = False, False, False
        self.process, self.spawning, self.problem = None, None, None
        self.diagnostics = bytearray()
        self.result_ref = None

    def expired(self) -> bool:
        try:
            return protocol.cycle_operation_remaining(self.payload) <= 0
        except (OSError, ValueError):
            return True

    def request_stop(self) -> None:
        self.stopping = True

    async def _send(self) -> None:
        stream = self.process.stdin
        try:
            stream.write(self.encoded)
            await stream.drain()
            self.sent = True
        finally:
            stream.close()
            await stream.wait_closed()

    async def _read(self, stream, *, diagnostic=False) -> None:
        while raw := await stream.read(65_536):
            if diagnostic:
                self.diagnostics.extend(raw[:max(0, 65_536 - len(self.diagnostics))])
            else:
                self.response.receive(raw)

    def observation(self, result: dict) -> dict:
        return {**result, 'operation_id': self.identity['operation_id'], 'mode': self.identity['mode'],
            'ordinal': self.identity['ordinal'], 'output': str(self.output),
            'operation_stopped': bool(self.response.frames),
            'supervisor_returncode': self.process.returncode if self.process is not None else None}

    async def _run(self) -> dict:
        if self.stopping or self.expired():
            return self.observation({'status': 'unknown', 'reason': 'Original cycle operation allowance is exhausted'})
        self.spawning = asyncio.create_task(asyncio.create_subprocess_exec(sys.executable, '-P', '-c',
            'from ergora.reference_training_worker import cycle_operation_main;cycle_operation_main()',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            env=dict(os.environ), start_new_session=True))
        while self.process is None:
            try:
                self.process = await asyncio.shield(self.spawning)
            except asyncio.CancelledError:
                self.request_stop()
                if self.spawning.cancelled():
                    # The stdlib closes and waits for a cancelled creation.
                    # No request was sent, so S could not have started H.
                    return self.observation({'status': 'unknown',
                        'reason': 'Supervisor creation was cancelled before its request was sent'})
            except OSError as error:
                return self.observation({'status': 'unknown', 'reason': str(error)})
        tasks = [asyncio.create_task(self._send()), asyncio.create_task(self._read(self.process.stdout)),
                 asyncio.create_task(self._read(self.process.stderr, diagnostic=True)),
                 asyncio.create_task(self.process.wait())]
        while True:
            # Loop shutdown cancels inner tasks as well as their caller. Keep
            # draining the original pipes and waiting for the original S;
            # cancelling an observer is not proof that its H subtree stopped.
            if tasks[0].cancelled():
                self.request_stop()
                self.process.stdin.close()
            for index, stream in ((1, self.process.stdout), (2, self.process.stderr)):
                if tasks[index].cancelled():
                    self.request_stop()
                    tasks[index] = asyncio.create_task(self._read(stream, diagnostic=index == 2))
            if tasks[3].cancelled():
                self.request_stop()
                tasks[3] = asyncio.create_task(self.process.wait())
            for task in tasks:
                if task.done() and not task.cancelled() and task.exception() is not None and self.problem is None:
                    self.problem = str(task.exception())
            expired = self.expired()
            if ((self.stopping or self.problem is not None or self.response.problem is not None or expired)
                    and not self.signalled and self.process.returncode is None):
                try:
                    self.process.terminate()
                except ProcessLookupError:
                    pass
                self.signalled = True
            # Only the matching first frame permits killing S after its sole H subtree is reaped.
            if self.response.frames and expired and self.process.returncode is None:
                try:
                    self.process.kill()
                except ProcessLookupError:
                    pass
            if all(task.done() for task in tasks):
                break
            try:
                await asyncio.sleep(.05)
            except asyncio.CancelledError:
                self.request_stop()
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        if (not self.stopping and self.process.returncode == 0 and self.sent and len(self.response.frames) == 2
                and not self.response.buffer and self.response.problem is None
                and not any(isinstance(item, BaseException) for item in outcomes) and not self.expired()):
            value = dict(self.response.frames[1]['result'])
            self.result_ref = value.pop('_stdout_ref', None)
            if self.result_ref is not None:
                protocol._exact(self.result_ref, ('file', 'bytes', 'sha256'), 'Cycle stdout reference')
                if (self.result_ref['file'] != 'helper/stdout.txt' or type(self.result_ref['bytes']) is not int
                        or not 0 <= self.result_ref['bytes'] <= _CYCLE_LIMIT):
                    raise ValueError('Cycle stdout reference has invalid source or size')
                protocol._digest(self.result_ref['sha256'])
            return self.observation(value)
        return self.observation({'status': 'unknown', 'response_rejected': self.response.problem is not None,
            'reason': self.problem or 'Original cycle operation has no complete in-budget result; inspect its operation logs'})

    async def run(self) -> dict:
        # The owned task retains the real spawn and handle even when its caller is cancelled.
        running = asyncio.create_task(self._run())
        try:
            return await asyncio.shield(running)
        except asyncio.CancelledError:
            self.request_stop()
            finished = asyncio.gather(running, return_exceptions=True)
            while not finished.done():
                try:
                    await asyncio.shield(finished)
                except asyncio.CancelledError:
                    continue
            outcome = finished.result()[0]
            if isinstance(outcome, BaseException):
                self.problem = str(outcome)
            raise


class _CycleCandidate:
    """Own one in-memory offer until the complete original owner is confirmed."""

    def __init__(self, home: Path, project: str, cycle_id: str, authorization_sha256: str,
                 *, snapshot: dict, controller: dict, activity_context: dict | None = None):
        self.preparation = _CycleOperation(home, project, cycle_id, authorization_sha256, 'prepare-candidate',
            snapshot=snapshot, ordinal=controller['ordinal'], start_context={'controller': controller},
            activity_context=activity_context)
        self.operation = self.preparation
        self.operations, self.results = [self.preparation], []
        self.stopping, self.handed_off = False, False
        self.spawning, self.root, self.root_identity = None, None, None
        self.cleanup_problem = None

    def stopping_now(self) -> bool:
        return self.stopping or self.preparation.expired()

    def next_operation(self, mode: str, **facts):
        identity, payload = self.preparation.identity, self.preparation.payload
        self.operation = _CycleOperation(Path(identity['control_home']), identity['project'], identity['cycle_id'],
            identity['authorization_sha256'], mode, snapshot=payload['snapshot'], ordinal=identity['ordinal'],
            window=payload['bootstrap'], start_context={**payload['start_context'],
                'origin_operation_id': identity['operation_id'], **facts},
            activity_context=payload.get('activity_context'))
        self.operations.append(self.operation)
        return self.operation

    async def transfer(self, raw: bytes) -> None:
        class InputClosed(asyncio.Protocol):
            def __init__(self):
                self.closed = asyncio.get_running_loop().create_future()

            def connection_lost(self, error):
                if not self.closed.done():
                    if error is None:
                        self.closed.set_result(None)
                    else:
                        self.closed.set_exception(error)

        transport, closing = await asyncio.get_running_loop().connect_write_pipe(InputClosed, self.root.stdin)
        try:
            # The complete request is bounded; close flushes its asynchronous
            # pipe buffer before notifying connection_lost.
            transport.write(raw)
            transport.close()
            await asyncio.shield(closing.closed)
        finally:
            if not closing.closed.done():
                transport.abort()

    async def observe_root(self) -> None:
        # Cancellation on normal loop shutdown only drops this observation.
        # poll() reaps an exited child and never terminates a live budget root.
        while self.root.poll() is None:
            await asyncio.sleep(.05)

    async def discard_root(self) -> None:
        if self.spawning is None:
            return
        # The concurrent Future survives asyncio.run's cancellation of every
        # Task. Retain its actual OS handle even if loop teardown interrupts us.
        while not self.spawning.done():
            try:
                await asyncio.sleep(.02)
            except asyncio.CancelledError:
                self.stopping = True
        try:
            self.root = self.spawning.result()
        except OSError:
            return
        if not self.root.stdin.closed:
            self.root.stdin.close()
        if self.root.poll() is None:
            try:
                expected = self.root_identity or processes.identity(self.root.pid)
                processes.notify_identity(expected, signal.SIGTERM)
            except (OSError, ValueError) as error:
                # EOF can win the poll/notify race. A failed notification of a
                # still-live root must retain the actual handle and exit wait.
                if self.root.poll() is None:
                    self.cleanup_problem = 'Original root notification is unconfirmed: ' + str(error)
        while self.root.poll() is None:
            try:
                await asyncio.sleep(.05)
            except asyncio.CancelledError:
                self.stopping = True
        self.root.wait()

    async def run_operation(self, operation):
        try:
            result = await operation.run()
        except (OSError, ValueError, TypeError, KeyError) as error:
            result = operation.observation({'status': 'capacity_exceeded' if isinstance(error, _CycleCapacityError)
                                           else 'unknown', 'reason': str(error)})
        self.results.append(result)
        return result

    async def _run(self) -> dict:
        prepared = await self.run_operation(self.preparation)
        if prepared['status'] != 'new_offer':
            return prepared
        result = {'status': 'unknown', 'preparation': prepared, 'intent_sha256': prepared['intent_sha256']}
        if self.stopping_now():
            return {**result, 'reason': 'Original start ended after prepare; its intent remains occupied'}
        try:
            launch = prepared['launch']
            if set(launch) != {'request', 'environment'} or set(launch['environment']) != {
                    'PYTHONPATH', 'AGENTFLOW_CONFIG_DIR', 'AGENTFLOW_STATE_DIR'}:
                raise ValueError('Controller root offer has unexpected launch fields')
            request = launch['request']
            protocol.validate_cycle_root_request(request)
            if (request['origin_operation_id'] != self.preparation.identity['operation_id']
                    or request['parent'] != self.preparation.identity['parent']
                    or request['window'] != self.preparation.payload['bootstrap']
                    or request['submission']['intent_sha256'] != prepared['intent_sha256']):
                raise ValueError('Controller root offer differs from its complete prepare response')
            encoded = json.dumps(request, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
            if len(encoded) > _CYCLE_LIMIT:
                raise _CycleCapacityError('Complete controller root request exceeds 32 KiB; intent remains occupied')
            # Only OS creation runs in the thread. Its public concurrent Future
            # cannot be cancelled by the loop's global Task shutdown.
            executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='ergora-budget-spawn')
            try:
                self.spawning = executor.submit(subprocess.Popen,
                    [sys.executable, '-P', '-c', 'from ergora.reference_training_worker import budget_main;budget_main()'],
                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    env={**os.environ, **launch['environment']}, start_new_session=True)
            finally:
                executor.shutdown(wait=False)
            while not self.spawning.done():
                if self.stopping_now():
                    return {**result, 'reason': 'Original start ended while OS process creation was pending'}
                await asyncio.sleep(.02)
            self.root = self.spawning.result()
            self.root_identity = processes.identity(self.root.pid)
            if self.stopping_now():
                return {**result, 'reason': 'Original start ended before root input was sent'}
            sending = asyncio.create_task(self.transfer(encoded))
            try:
                while not sending.done():
                    if self.stopping_now():
                        return {**result, 'reason': 'Original start ended during root input transfer'}
                    await asyncio.sleep(.02)
                sending.result()
            finally:
                if not sending.done():
                    sending.cancel()
                await asyncio.gather(sending, return_exceptions=True)
            while not self.stopping_now() and self.root.poll() is None:
                confirmed = await self.run_operation(self.next_operation('confirm-candidate',
                    intent_sha256=prepared['intent_sha256'], root_process=self.root_identity))
                result['confirmation'] = confirmed
                if confirmed['status'] == 'owner_confirmed' and not self.stopping_now():
                    owner = protocol.owner_record(confirmed['owner'])
                    if (confirmed['intent_sha256'] != prepared['intent_sha256']
                            or owner['intent_sha256'] != prepared['intent_sha256']
                            or {key: owner[key] for key in ('pid', 'start_ticks', 'boot_id')} != self.root_identity):
                        raise ValueError('Root confirmation differs from its complete original offer or process')
                    self.handed_off = True
                    observer = asyncio.create_task(self.observe_root())
                    _ROOT_OBSERVERS.add(observer)
                    observer.add_done_callback(_ROOT_OBSERVERS.discard)
                    dispatched = await self.run_operation(self.next_operation('dispatch-candidate',
                        intent_sha256=prepared['intent_sha256'], owner=owner))
                    return {**dispatched, 'preparation': prepared, 'confirmation': confirmed}
                await asyncio.sleep(.05)
            return {**result, 'reason': 'Original root was not completely confirmed in its one start window'}
        except (OSError, ValueError, TimeoutError) as error:
            return {**result, 'status': 'capacity_exceeded' if isinstance(error, _CycleCapacityError) else 'unknown',
                    'reason': str(error)}
        finally:
            if not self.handed_off:
                await self.discard_root()

    async def run(self) -> dict:
        running = asyncio.create_task(self._run())
        try:
            result = await asyncio.shield(running)
            if self.cleanup_problem is not None:
                return {**result, 'status': 'unknown', 'cleanup_problem': self.cleanup_problem}
            return result
        except asyncio.CancelledError:
            self.stopping = True
            self.operation.request_stop()
            # Retain pending Popen and the exact root until its real handle and
            # pre-handoff cleanup are complete, even under repeated cancellation.
            finished = asyncio.gather(running, return_exceptions=True)
            while not finished.done():
                try:
                    await asyncio.shield(finished)
                except asyncio.CancelledError:
                    continue
            outcome = finished.result()[0]
            if isinstance(outcome, BaseException):
                self.cleanup_problem = str(outcome)
            raise


async def start_cycle_candidate(home: Path, project: str, cycle_id: str, authorization_sha256: str,
                                *, snapshot: dict, controller: dict) -> dict:
    """Start only this call's sole new offer; existing intents are observations."""
    return await _CycleCandidate(home, project, cycle_id, authorization_sha256,
                                 snapshot=snapshot, controller=controller).run()


def _cycle_snapshot(plan: dict, authorization: dict) -> dict:
    return {'authorization': authorization, 'policy': plan['definition']['budget'],
        'candidates': [{'ordinal': index, 'experiment_id': item['experiment_id'],
                        'manifest_sha256': item['manifest_sha256']}
                       for index, item in enumerate(plan['definition']['candidates'])]}


def _cycle_submission(plan: dict, admission, ordinal: int):
    """Locate the original bound intent independently of its live owner."""
    authorization = admission.authorization
    ident = plan['definition']['candidates'][ordinal]['experiment_id']
    operation = _Submission({'project': plan['project'], 'control_home': authorization['control_home'],
                             'experiment_id': ident})
    intent = operation.load()
    if intent is None:
        return operation, None
    admission.bind(intent, plan)
    if (intent['project_revision'] != authorization['project_revision']
            or intent['budget']['controller']['ordinal'] != ordinal):
        raise ValueError('Cycle notification differs from the original selected revision or ordinal')
    return operation, intent


def _cycle_target(plan: dict, admission, ordinal: int):
    """Resolve the exact original owner for notification or execution observation."""
    operation, intent = _cycle_submission(plan, admission, ordinal)
    if intent is None:
        return operation, None, None
    try:
        owner = protocol.owner_record(protocol.decode(
            protocol.read_raw(operation.path('.budget/owner.json'))))
    except FileNotFoundError:
        return operation, intent, None
    if (owner['intent_sha256'] != training_cycles._sha(intent)
            or owner['authorization_sha256'] != admission.authorization['sha256']):
        raise ValueError('Cycle target owner differs from its complete original intent or authorization')
    return operation, intent, owner


def _activity_active(payload):
    identity = payload['identity']
    if (protocol.cycle_operation_remaining(payload) <= 0
            or processes.identity(identity['parent']['pid']) != identity['parent']):
        raise ValueError('Original activity observation window or parent ended')


def _activity_binding(payload, admission):
    context = payload['activity_context']
    protocol.validate_cycle_activity_context(context, measurement_action=payload['identity']['mode']
        if payload['identity']['mode'] in protocol.CYCLE_MEASUREMENT_MODES else None)
    saved = admission.submission()
    intent = saved['intent']
    if (intent is None or not saved['attempt_saved'] or saved['status'] == 'rejected'
            or intent['workflow_input'] != context['workflow_input']
            or intent['workflow_id'] != context['activity_source']['workflow_id']
            or saved['run_id'] is not None and saved['run_id'] != context['activity_source']['workflow_run_id']):
        raise ValueError('SDK activity differs from its complete original controller attempt or run')
    if payload['identity']['mode'] != 'inspect-controller-activity' and saved['run_id'] is None:
        raise ValueError('SDK activity requires its authenticated original receipt')
    controller = payload.get('start_context', {}).get('controller')
    if controller is not None and any(controller[key] != value for key, value in {
            'workflow_id': intent['workflow_id'], 'run_id': context['activity_source']['workflow_run_id'],
            'intent_sha256': protocol.CycleAdmission._sha(intent)}.items()):
        raise ValueError('Candidate source differs from its authenticated activity controller')
    return saved


def _cycle_operation(payload: dict) -> dict:
    """Run inside a separately supervised H, never inside the async parent loop."""
    identity = payload['identity']
    home, project, cycle = Path(identity['control_home']), identity['project'], identity['cycle_id']
    directory = training_cycles._directory(home, project, cycle)
    plan, authorization, ready = training_cycles._load(home, project, cycle, directory)
    admission = protocol.CycleAdmission(directory, authorization)
    if authorization['sha256'] != identity['authorization_sha256']:
        raise ValueError('Cycle operation requires the complete original authorization SHA256')
    if authorization['schema_version'] == 3 and identity['mode'] not in protocol.CYCLE_MEASUREMENT_MODES:
        raise ValueError('Schema3 controller execution is not enabled')
    snapshot = _cycle_snapshot(plan, authorization)
    mode = identity['mode']
    if payload.get('activity_context') is not None:
        _activity_binding(payload, admission)
    if mode in ('inspect', 'inspect-controller-activity'):
        authentication = None
        if mode == 'inspect-controller-activity':
            if ready is None:
                raise ValueError('SDK activity requires the original durable ready record')
            authentication = asyncio.run(_dispatch_controller(payload, plan, admission, lambda: _activity_active(payload)))
            if authentication.get('runtime_status') not in ('queried', 'local_binding'):
                return authentication
        # This is only a read of original facts, including an already exhausted clock.
        total = budget_clock.remaining(authorization['clock'], snapshot['policy']['wall_seconds'])
        boot, ticks = budget_clock._clock()
        result = {'status': 'inspected', 'snapshot': snapshot,
            'submission': {key: value for key, value in admission.submission().items() if key != 'intent'},
            'candidate_exists': (_cycle_submission(plan, admission, 0)[1] is not None
                if payload.get('activity_context', {}).get('activity_source', {}).get('activity_type')
                    == protocol.CYCLE_ACTIVITY_NAMES['start'] else None),
            'controller': ({key: authentication[key] for key in ('workflow_id', 'run_id', 'intent_sha256')}
                           if authentication is not None else None),
            'runtime_status': authentication.get('runtime_status', 'not_queried') if authentication else 'not_queried',
            'observation': {'total_remaining_seconds': total, 'boot_id': boot,
                            'boottime_ns': ticks, 'observed_at': now()}}
        if payload.get('activity_context', {}).get('activity_source', {}).get('activity_type') in (
                protocol.CYCLE_ACTIVITY_NAMES['request-execution-or-observe'],
                protocol.CYCLE_ACTIVITY_NAMES['observe-candidate']):
            candidate = _execution_candidate_operation(payload, plan, admission, lambda: _activity_active(payload))
            result['facts'] = candidate.pop('facts')
            result['candidate_observation'] = candidate
            budget = result['facts']['budget']
            result['observation'] = {key: budget[key] for key in
                ('total_remaining_seconds', 'boot_id', 'boottime_ns', 'observed_at')}
        return result
    if identity['input_sha256'] != authorization['input_sha256'] or training_cycles._sha(payload['snapshot']) != training_cycles._sha(snapshot):
        raise ValueError('Cycle operation snapshot differs from the complete original records')

    def active():
        if (protocol.cycle_operation_remaining(payload) <= 0
                or processes.identity(identity['parent']['pid']) != identity['parent']):
            raise ValueError('Original cycle operation parent or allowance ended')

    active()
    if mode in protocol.CYCLE_MEASUREMENT_MODES:
        if ready is None:
            raise ValueError('Round collection requires its original durable ready record')
        _select_cycle_project(authorization, plan['project'])
        return _round_operation(payload, plan, admission, ready, active)
    if mode in ('submit-controller', 'reconcile-controller'):
        if ready is None:
            raise ValueError('Controller delivery requires its original durable ready record')
        return asyncio.run(_dispatch_controller(payload, plan, admission, active))
    if mode == 'prepare-controller':
        prepared = training_cycles.prepare_controller(State(home), project, cycle,
            authorization['sha256'], authorization['project_revision'])
        active()
        return {'status': 'prepared', 'created': prepared['created'],
            'intent_sha256': prepared['intent_sha256'], 'intent_path': str(admission.folder / 'intent.json'),
            'cycle_status': prepared['cycle']['status'],
            'work_remaining_seconds': prepared['cycle']['work_remaining_seconds'],
            'total_remaining_seconds': prepared['cycle']['total_remaining_seconds']}
    if mode in protocol.CYCLE_CANDIDATE_MODES:
        if mode in protocol.CYCLE_EXECUTION_MODES:
            _select_cycle_project(admission.authorization, plan['project'])
            return _execution_candidate_operation(payload, plan, admission, active)
        return _candidate_operation(payload, plan, admission, active)
    if mode == 'stop-writer':
        return {'status': 'observed', **admission.request_stop(payload['reason'])}
    if mode == 'drain':
        while True:
            active()
            observed = admission.observe(synchronize=True, drain=True)
            if observed['admission_drained'] is True or observed['identity_matches'] is False:
                return {'status': 'observed', **observed}
            time.sleep(.05)
    operation, intent, owner = _cycle_target(plan, admission, identity['ordinal'])
    if mode == 'notify-owner':
        if owner is None:
            return {'status': 'not_started' if intent is None else 'unconfirmed',
                    'experiment_id': operation.ident, 'executor_stop_confirmed': None}
        expected = {name: owner[name] for name in ('pid', 'start_ticks', 'boot_id')}
        active()
        processes.notify_identity(expected, signal.SIGTERM)
        return {'status': 'notified', 'experiment_id': operation.ident,
                'owner': expected, 'executor_stop_confirmed': None}
    chain = protocol.ExecutionRecords(plan['project'], operation.ident, str(home)).load()
    if training_cycles._sha(chain.intent) != training_cycles._sha(intent) or training_cycles._sha(chain.owner) != training_cycles._sha(owner):
        raise ValueError('Original cycle execution chain changed during observation')
    observed = chain.observe(durable=True)
    # Keep complete observations off the bounded response, without losing their exact identity.
    raw = (json.dumps(observed, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
    output = home / 'operations/training-cycles' / identity['operation_id'] / 'helper/observation.json'
    with output.open('xb') as stream:
        stream.write(raw)
    return {key: observed.get(key) for key in
        ('status', 'reap_record_observed', 'durable_stop_confirmed', 'executor_stop_confirmed', 'record_sha256', 'durability_reason')} | {
        'experiment_id': operation.ident, 'observation': str(output), 'observation_sha256': hashlib.sha256(raw).hexdigest()}


def _select_cycle_project(authorization: dict, project: dict):
    """Load one selected native project inside H or its independent budget root."""
    from .reference_training_context import _TrainingProject

    execution = authorization['execution']
    installation = reference.validate_installation(Path(execution['installation']), training=True)
    paths = [str(installation / part) for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
    sys.path[:0] = paths
    os.environ.update(AGENTFLOW_CONFIG_DIR=execution['config_directory'], AGENTFLOW_STATE_DIR=execution['state_directory'])
    context = _TrainingProject({'project': project, 'control_home': authorization['control_home']})
    context.registration()
    from agent_platform.core import environment

    os.environ.update(environment())
    # Native environment() replaces PYTHONPATH. Every later phase must still
    # import this exact application together with the selected native sources.
    os.environ['PYTHONPATH'] = os.pathsep.join([str(Path(__file__).parent.parent), *paths])
    return context


def _execution_candidate_operation(payload: dict, plan: dict, admission, active) -> dict:
    """Project original candidate facts in H; only its first request may publish."""
    identity, authorization = payload['identity'], admission.authorization
    ordinal = identity['ordinal'] if identity['ordinal'] is not None else 0
    operation, intent, owner = _cycle_target(plan, admission, ordinal)
    submitted = operation.status(intent)
    facts = {'source_operation_id': identity['operation_id'], 'budget': None,
        'candidate': {'ordinal': ordinal, 'experiment_id': operation.ident,
            'manifest_sha256': plan['definition']['candidates'][ordinal]['manifest_sha256'],
            'project_revision': authorization['project_revision'], 'current_project_matches': None,
            'parent_stop_visible': None},
        'submission': {'state': submitted['status'], 'intent_sha256': submitted.get('intent_sha256'),
            'workflow_id': submitted['workflow_id'], 'run_id': submitted['run_id'],
            'attempt_saved': submitted.get('attempt_saved', False), 'result_saved': submitted.get('result_saved', False)},
        'execution': {'state': 'unknown', 'request_sha256': None, 'record_sha256': {},
            'reap_record_observed': None, 'durable_stop_confirmed': None, 'executor_stop_confirmed': None},
        'runtime': {'state': 'not_queried', 'workflow_id': None, 'run_id': None, 'temporal_status': None,
            'terminal': None, 'phase': None, 'binding': None, 'job_id': None},
        'native': {'state': 'not_queried', 'job_id': None}, 'request_outcome': 'not_attempted'}
    result = {'status': 'observed', 'submission': submitted, 'execution': None,
              'runtime': None, 'native': None, 'problems': {}, 'facts': facts}

    def problem(part, error):
        result['status'] = 'unknown'
        result['problems'][part] = str(error)
        _retain_round_reader(payload, part, {'error': str(error)})

    def execution_observation():
        chain = protocol.ExecutionRecords(plan['project'], operation.ident, identity['control_home']).load()
        if operation.sha(chain.intent) != operation.sha(intent) or operation.sha(chain.owner) != operation.sha(owner):
            raise ValueError('Candidate execution observation lost its complete original intent or owner')
        if identity['mode'] in protocol.CYCLE_MEASUREMENT_MODES:
            expected = chain.request_record(authorization['controller']['actor_id'])
            if chain.records['request'] is not None and chain.records['request'] != expected:
                raise ValueError('Original execution request differs from its complete controller source')
        observed = chain.observe(durable=True)
        result['execution'] = observed
        _retain_round_reader(payload, 'execution', observed)
        state = next((name for record, name in (('stopped', 'stop_observed'), ('ack', 'acknowledged'),
            ('attempt', 'attempted'), ('launch', 'launch_consumed'), ('request', 'requested'))
            if chain.records[record] is not None), 'not_requested')
        facts['execution'] = {'state': 'stopped' if observed['durable_stop_confirmed'] is True else state,
            'request_sha256': observed['record_sha256'].get('request'), 'record_sha256': observed['record_sha256'],
            **{key: observed[key] for key in
               ('reap_record_observed', 'durable_stop_confirmed', 'executor_stop_confirmed')}}
        return chain

    chain = None
    try:
        chain = execution_observation()
    except (OSError, ValueError, KeyError, TypeError) as error:
        problem('execution', error)
    try:
        facts['candidate']['current_project_matches'] = (State(Path(identity['control_home'])).project(
            identity['project'])['revision'] == authorization['project_revision'])
    except (OSError, ValueError, KeyError, TypeError) as error:
        problem('project', error)
    parent = admission.observe()
    facts['candidate']['parent_stop_visible'] = parent['stop_visible']
    if parent['reason'] is not None:
        problem('parent', parent['reason'])

    if identity['mode'] in (*protocol.CYCLE_EXECUTION_MODES, *protocol.CYCLE_MEASUREMENT_MODES) and submitted['status'] == 'submitted':
        from agent_platform.core import Blocked
        from agent_platform.training import LocalTrainingAdapter
        from perf_temporal.connection import connect
        from perf_temporal.models import Binding, Job
        from temporalio.service import RPCError
        from .reference_training_runtime import MEMO_KEY, lookup, observe

        binding = Binding(**intent['observation']['experiment']['spec']['binding'])

        def remaining():
            active()
            return protocol.cycle_operation_remaining(payload)

        async def runtime():
            async with asyncio.timeout(remaining()):
                client = await connect()
                if client.namespace != payload['activity_context']['service_namespace']:
                    raise ValueError('Candidate runtime namespace differs from its authenticated SDK activity service')
                found = await lookup(client, intent['observation']['experiment']['spec'],
                                     run_id=submitted['run_id'], timeout=remaining())
                if found is None:
                    facts['runtime'].update(state='not_found', workflow_id=submitted['workflow_id'],
                                            run_id=submitted['run_id'])
                    return
                if (await found[1].memo()).get(MEMO_KEY) != operation.sha(intent):
                    raise ValueError('Original candidate runtime memo differs from its complete start intent')
                observed = await observe(*found, binding, timeout=remaining())
                result['runtime'] = observed
                _retain_round_reader(payload, 'runtime', observed)
                detail = observed.get('status', observed.get('outcome', {}))
                facts['runtime'] = {'state': 'queried', **{key: observed.get(key) for key in
                    ('workflow_id', 'run_id', 'temporal_status', 'terminal', 'phase')},
                    'binding': detail.get('binding'), 'job_id': detail.get('job_id')}

        try:
            asyncio.run(runtime())
        except (OSError, ValueError, KeyError, TypeError, TimeoutError, RPCError) as error:
            facts['runtime']['state'] = 'unconfirmed'
            problem('runtime', error)
        request = None
        try:
            active()
            if chain is None or owner is None or owner.get('execution_capability') is None:
                raise ValueError('Original native observation has no complete capable execution owner')
            request = chain.request_record(authorization['controller']['actor_id'])
            if (identity['mode'] in protocol.CYCLE_MEASUREMENT_MODES and chain.records['request'] is not None
                    and chain.records['request'] != request):
                raise ValueError('Original execution request differs from its controller actor or complete native request')

            async def native():
                async with asyncio.timeout(remaining()):
                    return await LocalTrainingAdapter().poll_job(Job(binding, request['job_id']))

            observed = asyncio.run(native())
            result['native'] = asdict(observed)
            _retain_round_reader(payload, 'native', result['native'])
            if observed.state not in ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED'):
                raise ValueError('Original native observation has an unsupported state')
            facts['native'] = {'state': observed.state, 'job_id': observed.job.job_id}
        except (OSError, ValueError, KeyError, TypeError, TimeoutError, Blocked) as error:
            facts['native']['state'] = 'unconfirmed'
            problem('native', error)
        if (request is not None and facts['runtime']['state'] == 'queried'
                and facts['runtime']['job_id'] is not None and facts['runtime']['job_id'] != request['job_id']):
            facts['runtime']['state'] = 'unconfirmed'
            problem('runtime', 'Original candidate runtime job differs from its complete native request')
        if chain is not None and any(value is not None for value in chain.records.values()):
            facts['request_outcome'] = 'existing_only'
        elif (identity['mode'] == 'request-execution-candidate'
                and payload['activity_context']['activity_source']['attempt'] == 1
                and result['status'] == 'observed' and request is not None
                and facts['candidate']['current_project_matches'] is True
                and facts['candidate']['parent_stop_visible'] is False
                and facts['runtime']['state'] == 'queried' and facts['runtime']['terminal'] is False
                and facts['runtime']['phase'] == 'QUEUED' and facts['runtime']['job_id'] == request['job_id']
                and facts['native'] == {'state': 'QUEUED', 'job_id': request['job_id']}
                and not any(path.exists() or path.is_symlink() for path in (
                    chain.folder.parent / 'started.json', chain.folder.parent / 'result.json',
                    chain.root / ('training/fences/' + operation.ident + '.json')))):
            operation.payload.update(expected_revision=request['project_revision'],
                intent_sha256=request['start_intent_sha256'], run_id=request['run_id'],
                request_sha256=request['native_request_sha256'], confirm=True,
                timeout=remaining(), cycle_operation=payload)

            async def publish():
                async with asyncio.timeout(remaining()):
                    return await Execution(operation, BudgetedStart(operation, intent)).request()

            try:
                asyncio.run(publish())
                facts['request_outcome'] = 'requested'
            except (OSError, ValueError, KeyError, TypeError, TimeoutError, RPCError) as error:
                facts['request_outcome'] = 'unconfirmed'
                problem('request', error)
            try:
                execution_observation()
            except (OSError, ValueError, KeyError, TypeError) as error:
                facts['execution'].update(state='unknown', durable_stop_confirmed=None, executor_stop_confirmed=None)
                problem('execution', error)
    elif identity['mode'] in protocol.CYCLE_EXECUTION_MODES and chain is not None and any(
            value is not None for value in chain.records.values()):
        facts['request_outcome'] = 'existing_only'

    policy = plan['definition']['budget']
    budget = {'state': 'unknown', 'work_remaining_seconds': None, 'total_remaining_seconds': None,
              'control_timeout_seconds': policy['control_timeout_seconds'],
              'boot_id': authorization['clock']['boot_id'], 'boottime_ns': authorization['clock']['boottime_ns'],
              'observed_at': now()}
    try:
        boot, ticks = budget_clock._clock()
        budget.update(boot_id=boot, boottime_ns=ticks, observed_at=now())
        work = budget_clock.remaining(authorization['clock'], policy['wall_seconds'], policy['cleanup_seconds'])
        total = budget_clock.remaining(authorization['clock'], policy['wall_seconds'])
        boot, ticks = budget_clock._clock()
        budget.update(state='valid' if work > 0 else 'exhausted', work_remaining_seconds=work,
                      total_remaining_seconds=total, boot_id=boot, boottime_ns=ticks, observed_at=now())
    except (OSError, ValueError) as error:
        problem('budget', error)
    facts['budget'] = budget
    return result


def _round_selection(plan: dict, authorization: dict) -> dict:
    manifest = plan['admissions'][0]['observation']['experiment']['manifest']
    return {'count': len(plan['admissions']),
        'common_sha256': protocol.CycleAdmission._sha({key: manifest[key] for key in training_cycles._COMMON}),
        'measurement_sources_sha256': protocol.CycleAdmission._sha(authorization['measurement_sources'])}


def _round_local_gate(payload, plan, admission, ready, active):
    """Recheck complete original local authority after any blocking observation."""
    from .reference_training_context import _TrainingProject

    active()
    authorization = admission.authorization
    current_plan, current_authorization, current_ready = training_cycles._load(
        Path(authorization['control_home']), authorization['project'], authorization['cycle_id'], admission.directory)
    if (current_plan != plan or current_authorization != authorization or current_ready != ready
            or State(Path(authorization['control_home'])).project(authorization['project']) != plan['project']):
        raise ValueError('Round collection lost its original plan, ready or registered project')
    admission.check()
    ordinal = payload['identity']['ordinal']
    operation, intent, owner = _cycle_target(plan, admission, ordinal)
    if (intent is None or owner is None or owner.get('execution_capability') is None
            or intent['budget']['controller'] != payload['start_context']['controller']
            or intent['execution'] != authorization['execution']
            or intent['registration_sha256'] != plan['project']['registration']['sha256']
            or intent['repo'] != plan['project']['repo']):
        raise ValueError('Round collection has no complete original capable candidate source')
    capability = owner['execution_capability']
    if (capability['cycle_ready_sha256'] != operation.sha(ready)
            or capability['installation'] != authorization['execution']['installation']):
        raise ValueError('Round collection differs from its original ready or selected installation')
    protocol.validate_sources(capability)
    if training_cycles._measurement_sources() != authorization['measurement_sources']:
        raise ValueError('Original round measurement source bytes changed')
    # validate_sources pins the manifest itself before verify consumes its full inventory.
    reference.verify()
    _TrainingProject({'project': plan['project'], 'control_home': authorization['control_home']}).registration()
    # Source and registration checks perform local I/O. Stop and both original
    # allowances must still hold after those reads have actually returned.
    if budget_clock.remaining(authorization['clock'], plan['definition']['budget']['wall_seconds'],
                              plan['definition']['budget']['cleanup_seconds']) <= 0:
        raise ValueError('Original round collection work allowance is exhausted')
    active()
    admission.check()
    return operation, intent, owner


def _round_gate(payload, plan, admission, ready, active, *, history=False):
    """Recheck original authority, source bytes, parent and clock without granting execution."""
    from .reference_training_runtime import authenticate_round_collection, lookup_controller_submission
    from perf_temporal.connection import connect
    from temporalio.client import WorkflowExecutionStatus

    operation, intent, owner = _round_local_gate(payload, plan, admission, ready, active)
    ordinal = payload['identity']['ordinal']
    saved = admission.submission()
    controller = payload['start_context']['controller']
    request = {'workflow_input': payload['activity_context']['workflow_input'], 'ordinal': ordinal,
               'predecessor': controller['predecessor']}

    async def parent():
        active()
        async with asyncio.timeout(protocol.cycle_operation_remaining(payload)):
            client = await connect()
            if client.namespace != payload['activity_context']['service_namespace']:
                raise ValueError('Original controller service namespace changed')
            timeout = protocol.cycle_operation_remaining(payload)
            if history:
                await authenticate_round_collection(client, saved['intent'], controller, request,
                                                     payload['activity_context'], timeout=timeout)
            else:
                found = await lookup_controller_submission(client, saved['intent'], run_id=controller['run_id'], timeout=timeout)
                if found is None or found[1].status != WorkflowExecutionStatus.RUNNING:
                    raise ValueError('Original controller is not authenticated RUNNING')
    asyncio.run(parent())
    active()
    admission.check()
    return operation, intent, owner


def _round_report_binding(saved, plan, ordinal, previous):
    report = saved['report']
    if (report['project'] != {'id': plan['project']['id'], 'repo': plan['project']['repo'],
                             'registration_sha256': plan['project']['registration']['sha256']}
            or len(report['rounds']) != ordinal + 1):
        raise ValueError('Round index differs from its original registered selection or complete count')
    for index, item in enumerate(report['rounds']):
        selected = plan['definition']['candidates'][index]
        admitted = plan['admissions'][index]['observation']['experiment']
        if (item['experiment_id'] != selected['experiment_id']
                or item['annotation'] != {key: selected[key] for key in ('change', 'next_bottleneck')}
                or item['native']['records']['experiment']['manifest'] != admitted['manifest']
                or item['native']['records']['experiment']['spec'] != admitted['spec']
                or item['comparison']['manifest_sha256'] != selected['manifest_sha256']):
            raise ValueError('Round index changed a frozen candidate, manifest or annotation')
    if previous is None:
        if report['previous_report'] is not None:
            raise ValueError('First round index cannot replace a prior prefix')
    elif (report['rounds'][:-1] != previous['report']['rounds']
            or report['initial_anchor'] != previous['report']['initial_anchor']
            or report['previous_report'] != {'sha256': previous['sha256'],
                'rounds': len(previous['report']['rounds']),
                'last_round_sha256': previous['report']['rounds'][-1]['sha256']}):
        raise ValueError('Round index differs from its complete original previous prefix')


def _round_pin(saved, raw):
    if hashlib.sha256(raw).hexdigest() != saved['sha256']:
        raise ValueError('Round prefix changed its complete original raw bytes after read')
    return {'directory': saved['directory'], 'sha256': saved['sha256'], 'bytes': len(raw),
        'rounds': len(saved['report']['rounds']), 'last_round_sha256': saved['report']['rounds'][-1]['sha256'],
        'initial_anchor_sha256': protocol.CycleAdmission._sha(saved['report']['initial_anchor'])}


def _round_sync_file(path: Path, root: Path, active, *, raw: bytes | None = None, validate=None) -> bytes:
    """Confirm the same ordinary fd, directory chain and reopened raw/inode."""
    active()
    if raw is not None:
        # Check all ancestors using the original nonblocking safe-file owner.
        for parent in (path.parent, *path.parent.parents):
            if parent.is_symlink() or not parent.is_dir():
                raise ValueError('Round observation requires ordinary original directories')
        stream = path.open('x+b')
    else:
        stream = os.fdopen(protocol._fd(path), 'rb')
    with stream:
        if raw is not None:
            stream.write(raw)
            stream.flush()
        else:
            raw = stream.read(protocol.ARTIFACT_LIMIT + 1)
            if not 0 < len(raw) <= protocol.ARTIFACT_LIMIT:
                raise _CycleCapacityError('Complete original round index exceeds its artifact capacity')
        original = os.fstat(stream.fileno())
        if validate is not None:
            validate(raw)
        active()
        os.fsync(stream.fileno())
        active()
        protocol.sync_directories(path.parent, root)
    active()
    with os.fdopen(protocol._fd(path), 'rb') as reopened:
        current = os.fstat(reopened.fileno())
        if ((original.st_dev, original.st_ino) != (current.st_dev, current.st_ino)
                or reopened.read(len(raw) + 1) != raw):
            raise ValueError('Original round artifact changed inode or complete raw bytes during synchronization')
    active()
    return raw


def _round_read_evidence(payload, state, project, experiment, active):
    from . import training

    active()
    observed = training.evidence(state, project, experiment, artifact=None)
    _retain_round_reader(payload, 'evidence', observed)
    active()
    return observed


def _round_state(observed, evidence, item, intent):
    """Combine the four original owners; local approval is never a positive predicate."""
    if observed['status'] != 'observed':
        return 'unknown'
    facts, native, runtime, execution = (observed[key] for key in ('facts', 'native', 'runtime', 'execution'))
    if not all(isinstance(value, dict) for value in (native, runtime, execution)):
        return 'unknown'
    binding = intent['observation']['experiment']['binding']
    records, indexed_evidence, submitted = (item['native'][key] for key in ('records', 'evidence', 'submission'))
    experiment = records['experiment']
    detail = runtime.get('status', runtime.get('outcome', {}))
    request = execution['records'].get('request')
    if (evidence != indexed_evidence or evidence['binding'] != binding
            or experiment['binding'] != binding or experiment['manifest'] != intent['observation']['experiment']['manifest']
            or experiment['spec'] != intent['observation']['experiment']['spec']
            or evidence['recorded_gate_report'] != experiment['gate_report']
            or records['project_revision'] != intent['project_revision']
            or submitted['status'] != 'submitted' or facts['submission']['state'] != 'submitted'
            or any(submitted[key] != observed['submission'][key] for key in ('workflow_id', 'run_id', 'intent_sha256'))
            or runtime['workflow_id'] != submitted['workflow_id'] or runtime['run_id'] != submitted['run_id']
            or detail.get('binding') != binding or native.get('job', {}).get('binding') != binding
            or request is None or request['job_id'] != native.get('job', {}).get('job_id')
            or detail.get('job_id') != request['job_id'] or experiment['job_id'] != request['job_id']
            or request['start_intent_sha256'] != protocol.CycleAdmission._sha(intent)
            or facts['candidate']['current_project_matches'] is not True
            or facts['candidate']['parent_stop_visible'] is not False
            or evidence['baseline_matches'] is not True or evidence['fence_recorded'] is not False):
        return 'unknown'
    result = experiment['result']
    if (result is not None and (native['state'] != result['state'] or native.get('detail') != result['detail'])
            or any(evidence['files'].get(name) != digest for name, digest in
                   {**records['baseline_files'], **experiment['files']}.items())):
        return 'unknown'
    gate = evidence['recorded_gate_report']
    if native['state'] in ('FAILED', 'CANCELLED') or gate is not None and gate['passed'] is False:
        return 'rejected'
    if native['state'] in ('QUEUED', 'RUNNING') or execution['durable_stop_confirmed'] is not True:
        return 'pending'
    if (native['state'] != 'SUCCEEDED' or experiment['recorded_result_state'] != 'SUCCEEDED'
            or execution['executor_stop_confirmed'] is not True or execution['reap_record_observed'] is not True
            or set(execution['record_sha256']) != {'request', 'launch', 'attempt', 'ack', 'stopped'}
            or gate is None or gate['passed'] is not True or evidence['archive_status'] != 'recorded'
            or evidence['archive'] is None or evidence['archive']['artifact_content_status'] != 'not_read'):
        return 'unknown'
    evidence_sha = evidence['archive']['evidence_sha256']
    if gate['evidence_sha256'] != evidence_sha:
        return 'unknown'
    if (runtime['temporal_status'] == 'RUNNING' and runtime['terminal'] is False
            and runtime['phase'] == 'AWAITING_RELEASE' and 'status' in runtime
            and detail.get('evidence_sha') == evidence_sha):
        return 'accepted'
    if (runtime['temporal_status'] == 'COMPLETED' and runtime['terminal'] is True
            and runtime['phase'] in ('RELEASE_EXPIRED', 'INTEGRATION_TASK_CREATED') and 'outcome' in runtime
            and detail.get('report_uri') == Path(result['gate']['report']).as_uri()):
        return 'accepted'
    if runtime['temporal_status'] == 'RUNNING' and runtime['terminal'] is False and runtime['phase'] in (
            'QUEUED', 'RUNNING', 'COLLECTING', 'GATING'):
        return 'pending'
    return 'unknown'


def _round_acceptance(value, ref, intent):
    sha = protocol.CycleAdmission._sha
    facts, runtime, evidence, execution = (value[key] for key in ('facts', 'runtime', 'evidence', 'execution'))
    kind = 'status' if 'status' in runtime else 'outcome'
    detail = runtime[kind]
    return {'observation': ref, 'source_operation_id': value['identity']['operation_id'],
        'candidate': {key: facts['candidate'][key] for key in ('ordinal', 'experiment_id', 'manifest_sha256', 'project_revision')}
            | {'registration_sha256': intent['registration_sha256']},
        'submission': {key: facts['submission'][key] for key in ('intent_sha256', 'workflow_id', 'run_id')}
            | {'spec_sha256': sha(intent['observation']['experiment']['spec'])},
        'execution': {'owner_sha256': sha(execution['owner']), 'record_sha256': execution['record_sha256'],
                      'raw_inventory_sha256': sha(execution['raw_sha256'])},
        'runtime': {'namespace': value['activity_context']['service_namespace'], 'kind': kind, 'phase': runtime['phase'],
            'job_id': detail['job_id'], 'binding_sha256': sha(detail['binding']), 'memo_sha256': sha(intent),
            'evidence_sha': detail['evidence_sha'] if kind == 'status' else None,
            'report_uri': detail['report_uri'] if kind == 'outcome' else None},
        'evidence': {'evidence_sha256': evidence['archive']['evidence_sha256'],
            'gate_report_sha256': sha(evidence['recorded_gate_report']), 'files_sha256': sha(evidence['files'])},
        'common_sha256': value['selection']['common_sha256'],
        'measurement_sources_sha256': value['selection']['measurement_sources_sha256']}


def _round_previous(payload, plan, admission, selection, active):
    """Read every confirmed original prefix and observation; never scan for alternatives."""
    from . import training_rounds

    predecessor = payload['start_context']['controller']['predecessor']
    ordinal = payload['identity']['ordinal']
    previous, extension = None, None
    state = State(Path(payload['identity']['control_home']))
    for index in range(ordinal - 1, -1, -1):
        active()
        protocol.validate_round_predecessor(predecessor, index + 1)
        pin, acceptance = predecessor['prefix'], predecessor['acceptance']
        expected = admission.folder / 'rounds' / str(index)
        if pin['directory'] != str(expected):
            raise ValueError('Previous round prefix belongs to another original cycle')
        saved = training_rounds.read(expected, sha256=pin['sha256'])
        raw = protocol.read_raw(expected / 'rounds.json', protocol.ARTIFACT_LIMIT)
        if _round_pin(saved, raw) != pin:
            raise ValueError('Previous round pin differs from its complete raw original index')
        if extension is not None:
            _round_report_binding(extension, plan, index + 1, saved)
        if previous is None:
            previous = saved
        value = protocol.read_round_observation(acceptance['observation'], home=state.root,
                                                operation_id=acceptance['source_operation_id'])
        operation, intent, owner = _cycle_target(plan, admission, index)
        source_path = state.root / 'operations/training-cycles' / acceptance['source_operation_id']
        source = protocol.decode(protocol.read_raw(source_path / 'request.json', _CYCLE_LIMIT))
        protocol.validate_cycle_operation(source)
        reply = protocol.decode(protocol.read_raw(source_path / 'helper/stdout.txt', _CYCLE_LIMIT))
        if (value['identity'] != source['identity'] or value['activity_context'] != source['activity_context']
                or source['snapshot'] != payload['snapshot'] or value['prefix'] != pin or value['selection'] != selection
                or value['predecessor'] != intent['budget']['controller']['predecessor']
                or source['start_context']['controller'] != intent['budget']['controller']
                or value['activity_context']['workflow_input'] != payload['activity_context']['workflow_input']
                or value['activity_context']['service_namespace'] != payload['activity_context']['service_namespace']
                or reply.get('status') != 'observed' or reply['facts']['measurement'] != {
                    'measurement_state': 'accepted', 'index_state': 'durable', 'continuation_ready': True,
                    'prefix': pin, 'acceptance': acceptance}
                or _round_acceptance(value, acceptance['observation'], intent) != acceptance):
            raise ValueError('Previous acceptance differs from its complete original source operation or candidate')
        evidence = _round_read_evidence(payload, state, plan['project']['id'], operation.ident, active)
        chain = protocol.ExecutionRecords(plan['project'], operation.ident, str(state.root)).load()
        observed = chain.observe(durable=True)
        _retain_round_reader(payload, 'execution', observed)
        if (observed['owner'] != value['execution']['owner'] or owner != observed['owner']
                or observed['records'] != value['execution']['records']
                or observed['record_sha256'] != value['execution']['record_sha256']
                or observed['raw_sha256'] != value['execution']['raw_sha256']
                or observed['durable_stop_confirmed'] is not True or observed['executor_stop_confirmed'] is not True
                or evidence != value['evidence']):
            raise ValueError('Previous accepted execution or complete archive inventory changed')
        recorded = {'status': 'observed', 'submission': operation.status(intent), **value}
        if _round_state(recorded, evidence, saved['report']['rounds'][-1], intent) != 'accepted':
            raise ValueError('Previous original observation does not authenticate all four accepted facts')
        if index == ordinal - 1:
            target = {**payload, 'identity': {**payload['identity'], 'ordinal': index}}
            current = _execution_candidate_operation(target, plan, admission, active)
            if _round_state(current, evidence, saved['report']['rounds'][-1], intent) != 'accepted':
                raise ValueError('Immediately previous round is no longer authenticated accepted')
        extension = saved
        predecessor = value['predecessor']
    if extension is not None:
        _round_report_binding(extension, plan, 0, None)
    return previous


def _round_operation(payload, plan, admission, ready, active):
    from . import training_rounds

    identity = payload['identity']
    ordinal = identity['ordinal']
    state = State(Path(identity['control_home']))
    operation, intent, _ = _round_gate(payload, plan, admission, ready, active, history=True)
    selection = _round_selection(plan, admission.authorization)
    previous = _round_previous(payload, plan, admission, selection, active)
    preflight = _execution_candidate_operation(payload, plan, admission, active)
    evidence = _round_read_evidence(payload, state, identity['project'], operation.ident, active)
    if preflight['status'] != 'observed' or not all(isinstance(preflight[key], dict) for key in ('runtime', 'native', 'execution')):
        raise ValueError('Round collection lacks complete authenticated original observations')
    destination = admission.folder / 'rounds' / str(ordinal)
    for parent in (destination, *destination.parents):
        if parent.is_symlink() or parent.exists() and not parent.is_dir():
            raise ValueError('Round publication requires its original ordinary directory chain')
    active()
    try:
        destination.lstat()
    except FileNotFoundError:
        if identity['mode'] != 'collect-round' or payload['activity_context']['activity_source']['attempt'] != 1:
            raise ValueError('Reconciliation only reads the existing original round index')
        _round_gate(payload, plan, admission, ready, active)
        selected = plan['definition']['candidates'][ordinal]
        try:
            training_rounds.create(state, identity['project'], {'schema_version': 1, 'rounds': [
                {key: selected[key] for key in ('experiment_id', 'change', 'next_bottleneck')}]}, destination,
                previous=Path(previous['directory']) if previous else None,
                previous_sha256=previous['sha256'] if previous else None,
                on_reader_return=lambda name, value: _retain_round_reader(payload, 'index.' + name, value))
        except FileExistsError:
            # The sole deterministic destination won a race; never republish it.
            pass
    active()
    saved = training_rounds.read(destination)
    _round_report_binding(saved, plan, ordinal, previous)
    raw = protocol.read_raw(destination / 'rounds.json', protocol.ARTIFACT_LIMIT)
    if hashlib.sha256(raw).hexdigest() != saved['sha256']:
        raise ValueError('Round index changed between its original read and synchronization')
    # A complete preflight cannot bless the index's independently captured native values.
    measurement_state = _round_state(preflight, evidence, saved['report']['rounds'][-1], intent)
    index_state = 'published_unconfirmed'
    try:
        def validate_index(current_raw):
            if current_raw != raw or training_rounds.read(destination, sha256=saved['sha256']) != saved:
                raise ValueError('Round index changed while its original fd was held')
        confirmed = _round_sync_file(destination / 'rounds.json', admission.directory, active, validate=validate_index)
        if confirmed != raw:
            raise ValueError('Round index changed before its same-fd synchronization')
        reread = training_rounds.read(destination, sha256=saved['sha256'])
        if reread != saved:
            raise ValueError('Round index complete prefix changed after synchronization')
        _round_report_binding(reread, plan, ordinal, _round_previous(payload, plan, admission, selection, active))
        _round_gate(payload, plan, admission, ready, active)
        index_state = 'durable'
    except (OSError, ValueError) as error:
        return {'status': 'unknown', 'reason': str(error), 'facts': {**preflight['facts'], 'selection': selection,
            'measurement': {'measurement_state': measurement_state, 'index_state': index_state,
                'continuation_ready': False, 'prefix': None, 'acceptance': None}}}
    final = _execution_candidate_operation(payload, plan, admission, active)
    evidence = _round_read_evidence(payload, state, identity['project'], operation.ident, active)
    measurement_state = _round_state(final, evidence, saved['report']['rounds'][-1], intent)
    prefix = _round_pin(saved, raw)
    value = {'schema_version': 1, 'kind': 'training-cycle-round-observation', 'identity': identity,
        'activity_context': payload['activity_context'], 'predecessor': payload['start_context']['controller']['predecessor'],
        'selection': selection, 'facts': final['facts'], **{key: final[key] for key in ('runtime', 'native', 'execution')},
        'evidence': evidence, 'prefix': prefix}
    protocol.validate_round_observation(value)
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
    path = state.root / 'operations/training-cycles' / identity['operation_id'] / 'helper/observation.json'
    if len(raw) > protocol.ARTIFACT_LIMIT:
        # Preserve the entire oversized original in H's existing supervised output.
        _round_sync_file(path, state.root / 'operations/training-cycles', active, raw=raw)
        raise _CycleCapacityError('Complete round observation exceeds 10 MB; original raw was retained without acceptance')
    _round_sync_file(path, state.root / 'operations/training-cycles', active, raw=raw)
    ref = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    if protocol.read_round_observation(ref, home=state.root, operation_id=identity['operation_id']) != value:
        raise ValueError('Complete round observation changed after same-inode synchronization')
    _round_report_binding(saved, plan, ordinal, _round_previous(payload, plan, admission, selection, active))
    _round_gate(payload, plan, admission, ready, active)
    # Recheck the exact durable index after the final observation and gate.
    if training_rounds.read(destination, sha256=saved['sha256']) != saved:
        raise ValueError('Round prefix changed before its final acceptance')
    _round_local_gate(payload, plan, admission, ready, active)
    acceptance = _round_acceptance(value, ref, intent) if measurement_state == 'accepted' else None
    if acceptance is not None:
        protocol.validate_round_acceptance(acceptance)
    return {'status': 'observed' if final['status'] == 'observed' else 'unknown',
        'facts': {**final['facts'], 'selection': selection, 'measurement': {
            'measurement_state': measurement_state, 'index_state': index_state,
            'continuation_ready': acceptance is not None, 'prefix': prefix, 'acceptance': acceptance}}}


def _candidate_operation(payload: dict, plan: dict, admission, active) -> dict:
    """Keep all candidate files, locks and SDK calls within the original H."""
    from . import training

    identity, context = payload['identity'], payload['start_context']
    activity = payload.get('activity_context')
    mode = identity['mode']
    if mode == 'prepare-candidate' and activity is not None:
        if identity['ordinal'] != 0:
            raise ValueError('successor_not_enabled')
        if activity['activity_source']['attempt'] > 1:
            raise ValueError('Retried SDK start may only reconcile existing records')
        authentication = asyncio.run(_dispatch_controller(payload, plan, admission, active))
        if authentication.get('temporal_status') != 'RUNNING':
            raise ValueError('Original controller is not authenticated RUNNING; no new offer is admitted')
    _select_cycle_project(admission.authorization, plan['project'])
    mode = identity['mode']
    if mode in protocol.CYCLE_START_MODES:
        protocol.cycle_start_source(payload)
    operation, intent = _cycle_submission(plan, admission, identity['ordinal'])
    if intent is not None and intent['budget']['controller'] != context['controller']:
        raise ValueError('Candidate operation differs from its complete original controller binding')
    if mode == 'prepare-candidate':
        selected = plan['definition']['candidates'][identity['ordinal']]
        selector = {'cycle_id': identity['cycle_id'], 'authorization_sha256': identity['authorization_sha256'],
                    'controller': context['controller']}
        active()
        project, prepared = training._prepare_submission(State(Path(identity['control_home'])), identity['project'],
            selected['experiment_id'], admission.authorization['project_revision'], selected['manifest_sha256'],
            'prepare', 'manifest_sha256', plan['definition']['budget']['control_timeout_seconds'], budget=selector)
        active()
        operation = _Submission({'project': project, 'control_home': identity['control_home'],
            'experiment_id': selected['experiment_id'], 'timeout': plan['definition']['budget']['control_timeout_seconds']})
        intent = operation.load()
        budget = BudgetedStart(operation, intent)
        if not prepared['created']:
            return {'status': 'observed', 'submission': operation.status(intent)}
        # The immutable intent is the only offer. Losing any later reply never
        # grants another launch, even if this synchronization fails.
        protocol.sync_directories(operation.path('.intent.json').parent, operation.root)
        launch = budget.launch_context(payload)
        active()
        return {'status': 'new_offer', 'intent_sha256': operation.sha(intent),
                'submission': prepared['submission'], 'launch': launch}
    if intent is None:
        return {'status': 'observed', 'submission': operation.status(None), 'owner': None}
    if mode == 'reconcile-candidate':
        with file_lock(operation.path('.lock'), blocking=False):
            submitted = operation.status(intent)
            if submitted['status'] not in ('submitted', 'rejected') and submitted['attempt_saved']:
                operation.payload['timeout'] = protocol.cycle_operation_remaining(payload)

                async def reconcile():
                    async with asyncio.timeout(operation.payload['timeout']):
                        return await operation.reconcile(intent)

                submitted = asyncio.run(reconcile())
            active()
            return {'status': 'observed', 'submission': submitted}
    if operation.sha(intent) != context['intent_sha256']:
        raise ValueError('Candidate operation lost its exact original training intent')
    budget = BudgetedStart(operation, intent)
    if mode == 'confirm-candidate':
        budget.require_active(owner=True)
        owner = budget.owner_record()
        if ({key: owner[key] for key in ('pid', 'start_ticks', 'boot_id')} != context['root_process']
                or owner['context_sha256'] != operation.sha(budget.context())):
            raise ValueError('Candidate root differs from its complete original owner or context')
        active()
        return {'status': 'owner_confirmed', 'intent_sha256': operation.sha(intent), 'owner': owner}
    operation.payload.update(operation='dispatch', intent_sha256=context['intent_sha256'],
        timeout=plan['definition']['budget']['control_timeout_seconds'], cycle_operation=payload)

    async def dispatch():
        async with asyncio.timeout(protocol.cycle_operation_remaining(payload)):
            return await operation.run()

    submitted = asyncio.run(dispatch())
    active()
    return {'status': 'observed', 'submission': submitted}


async def _dispatch_controller(payload: dict, plan: dict, admission, active) -> dict:
    """SDK orchestration belongs to H; immutable claims belong to training_cycles."""
    from temporalio.common import RetryPolicy, WorkflowIDReusePolicy, WorkflowIDConflictPolicy
    from temporalio.exceptions import WorkflowAlreadyStartedError
    from temporalio.service import RPCError
    from .reference_training_runtime import lookup_controller_submission

    state = State(Path(payload['identity']['control_home']))
    saved = admission.submission()
    intent = saved['intent']
    if intent is None:
        raise ValueError('Prepare the complete original controller intent before dispatch or reconciliation')

    def observation(value, *, status=None, **facts):
        return {**{key: item for key, item in value.items() if key != 'intent'},
            'submission_status': value['status'], 'status': status or value['status'], **facts}

    activity_context = payload.get('activity_context')
    if activity_context is not None:
        _activity_binding(payload, admission)
        if (activity_context['activity_source']['activity_type'] == protocol.CYCLE_ACTIVITY_NAMES['stop']
                and saved['run_id'] is not None):
            return observation(saved, runtime_status='local_binding')
    if saved['status'] == 'rejected':
        return observation(saved, runtime_status='not_queried')
    context = _select_cycle_project(admission.authorization, plan['project'])
    installation = Path(admission.authorization['execution']['installation'])
    from perf_temporal.connection import connect

    def remaining():
        active()
        return protocol.cycle_operation_remaining(payload)

    try:
        async with asyncio.timeout(remaining()):
            client = await connect()
            if activity_context is not None and client.namespace != activity_context['service_namespace']:
                raise ValueError('Actual controller query namespace differs from its SDK activity service')

            async def reconcile():
                current = admission.submission()
                if current['status'] == 'rejected' or not current['attempt_saved']:
                    return observation(current, runtime_status='not_queried')
                actual_run = activity_context['activity_source']['workflow_run_id'] if activity_context else current['run_id']
                found = await lookup_controller_submission(client, intent, run_id=actual_run, timeout=remaining())
                if found is None:
                    return observation(current, status='unknown', runtime_status='not_found')
                _, description = found
                if activity_context is not None and (description.run_id != actual_run
                        or description.raw_description.workflow_execution_info.type.name != protocol.cycle_workflow_type(intent['protocol'])
                        or description.status.name == 'CONTINUED_AS_NEW'):
                    raise ValueError('Actual activity run or description type differs')
                current = training_cycles._record_controller(state, admission, run_id=description.run_id)
                active()
                return observation(current, runtime_status='queried', temporal_status=description.status.name)

            if payload['identity']['mode'] in ('reconcile-controller', 'inspect-controller-activity') or saved['attempt_saved']:
                return await reconcile()
            with admission.permission():
                training_cycles._controller_ready(state, admission)
                try:
                    found = await lookup_controller_submission(client, intent, run_id=None, timeout=remaining())
                except ValueError:
                    current = training_cycles._record_controller(state, admission, run_id=None, reason='lookup_rejected')
                else:
                    current = (training_cycles._record_controller(state, admission,
                        run_id=found[1].run_id, reason='preexisting_run') if found is not None else None)
                if current is not None:
                    return await reconcile() if current['attempt_saved'] and current['status'] == 'unknown' else observation(
                        current, runtime_status='queried')
                if not training_cycles._claim_controller(state, admission):
                    return await reconcile()
                # Claim/fsync, source reads and the original ready observation all consume this same window.
                reference.validate_installation(installation, training=True)
                context.registration()
                current = admission.submission()
                if current['status'] in ('submitted', 'rejected'):
                    return await reconcile()
                if not current['attempt_saved']:
                    raise ValueError('Original controller start attempt disappeared; do not dispatch again')
                training_cycles._controller_ready(state, admission)
                timeout = remaining()
                try:
                    handle = await client.start_workflow(protocol.cycle_workflow_type(intent['protocol']), intent['workflow_input'],
                        id=intent['workflow_id'], task_queue=intent['task_queue'],
                        id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                        id_conflict_policy=WorkflowIDConflictPolicy.FAIL, retry_policy=RetryPolicy(maximum_attempts=1),
                        memo={protocol.CYCLE_MEMO_KEY: protocol.CycleAdmission._sha(intent)},
                        rpc_timeout=timedelta(seconds=timeout))
                except WorkflowAlreadyStartedError as error:
                    current = training_cycles._record_controller(state, admission, run_id=error.run_id or None, reason='start_conflict')
                    return observation(current, runtime_status='queried')
                current = training_cycles._record_controller(state, admission, run_id=handle.result_run_id)
                active()
                return observation(current, runtime_status='start_acknowledged')
    except (RPCError, TimeoutError, ValueError) as error:
        return observation(admission.submission(), status='unknown', runtime_status='unconfirmed', reason=str(error))


def _activity_operation_result(operation, result):
    identity = operation.identity
    return {'operation_id': identity['operation_id'], 'mode': identity['mode'], 'ordinal': identity['ordinal'],
        'operation_stopped': result['operation_stopped'], 'supervisor_returncode': result['supervisor_returncode'],
        'result': {'ref': operation.result_ref} if operation.result_ref is not None else {'inline': result}}


async def stop_live_controller(home: Path, project_id: str, cycle_id: str, authorization_sha256: str,
                               *, reason: str, inspection_timeout: int = 10,
                               activity_context: dict | None = None, inspection: dict | None = None,
                               operation_records: list | None = None) -> dict:
    """Observe every independent branch, retaining each real task through cleanup."""
    if inspection is None:
        inspection = await _CycleOperation(home, project_id, cycle_id, authorization_sha256, 'inspect',
                                          inspection_timeout=inspection_timeout).run()
    if inspection['status'] != 'inspected':
        return {'status': 'unknown', 'inspection': inspection, 'operations': [], 'runtime_status': 'not_queried'}
    snapshot = inspection['snapshot']
    branches = [('stop-writer', None), ('drain', None)]
    branches.extend((mode, ordinal) for ordinal in range(len(snapshot['candidates']))
                    for mode in ('notify-owner', 'observe-execution'))
    operations, tasks, results = [], [], [None] * len(branches)

    async def run_branch(index, operation):
        try:
            value = await operation.run()
        except (OSError, ValueError, TypeError, KeyError) as error:
            value = operation.observation({'status': 'capacity_exceeded' if isinstance(error, _CycleCapacityError)
                                           else 'unknown', 'reason': str(error)})
        results[index] = value
        if operation_records is not None:
            operation_records.append(_activity_operation_result(operation, value))

    try:
        for index, (mode, ordinal) in enumerate(branches):
            try:
                operation = _CycleOperation(home, project_id, cycle_id, authorization_sha256, mode,
                    snapshot=snapshot, reason=reason if mode == 'stop-writer' else None,
                    ordinal=ordinal, activity_context=activity_context)
            except (OSError, ValueError, TypeError, KeyError) as error:
                value = {'operation_id': uuid.uuid4().hex, 'mode': mode, 'ordinal': ordinal,
                    'operation_stopped': False, 'supervisor_returncode': None,
                    'status': 'capacity_exceeded' if isinstance(error, _CycleCapacityError) else 'unknown',
                    'reason': str(error)}
                results[index] = value
                if operation_records is not None:
                    operation_records.append({key: value[key] for key in ('operation_id', 'mode', 'ordinal',
                        'operation_stopped', 'supervisor_returncode')} | {'result': {'inline': value}})
                continue
            operations.append(operation)
            tasks.append(asyncio.create_task(run_branch(index, operation)))
        await asyncio.gather(*tasks)
    finally:
        for operation in operations:
            operation.request_stop()
        finishing = asyncio.gather(*tasks, return_exceptions=True)
        while not finishing.done():
            try:
                await asyncio.shield(finishing)
            except asyncio.CancelledError:
                continue
    return {'status': 'stop_observations', 'cycle_id': cycle_id, 'project': project_id,
        'input_sha256': snapshot['authorization']['input_sha256'], 'authorization_sha256': authorization_sha256,
        'inspection': inspection, 'operations': results, 'runtime_status': 'not_queried'}


def cycle_operation_main(supervisor: bool = True) -> None:
    """Run as one S or its single H; never spawn after the stopped frame."""
    cancelled = False

    def cancel(signum, frame):
        nonlocal cancelled
        cancelled = True

    if supervisor:
        signal.signal(signal.SIGTERM, cancel)
        signal.signal(signal.SIGINT, cancel)
    raw = sys.stdin.buffer.read(_CYCLE_LIMIT + 1)
    if len(raw) > _CYCLE_LIMIT:
        raise ValueError('Complete cycle operation request exceeds 32 KiB')
    payload = protocol.decode(raw)
    protocol.validate_cycle_operation(payload)
    identity = payload['identity']
    expected = identity['parent']
    if processes.identity(expected['pid']) != expected or supervisor and os.getppid() != expected['pid']:
        raise ValueError('Cycle operation lost its original complete parent identity')
    output = Path(identity['control_home']) / 'operations/training-cycles' / identity['operation_id']
    if not supervisor:
        sys.path[:0] = [str(reference.ROOT / part) for part in
                       ('platform/local', 'platform/upstream/platform', 'platform/upstream/temporal', 'platform/upstream')]
        try:
            result = _cycle_operation(payload)
        except (OSError, ValueError, KeyError, TypeError, _RoundRetentionError) as error:
            result = {'status': 'capacity_exceeded' if isinstance(error, _CycleCapacityError) else 'unknown',
                      'reason': str(error)}
        print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
        return
    for parent in (output, *output.parents):
        if parent.is_symlink() or parent.exists() and not parent.is_dir():
            raise ValueError('Cycle operation output requires original ordinary directories')
    output.mkdir(parents=True, mode=0o700)
    with (output / 'supervisor.stderr').open('xb') as stderr:
        os.dup2(stderr.fileno(), sys.stderr.fileno())
    with (output / 'request.json').open('xb') as request:
        request.write(raw)

    def stopped():
        try:
            return (cancelled or protocol.cycle_operation_remaining(payload) <= 0
                    or processes.identity(expected['pid']) != expected)
        except (OSError, ValueError):
            return True

    def frame(event, field, value):
        encoded = json.dumps({**identity, 'event': event, field: value},
                             ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if len(encoded) > (65_536 if event == 'stopped' else _CYCLE_LIMIT):
            if event == 'stopped':
                raise ValueError('Complete cycle operation stopped frame exceeds its capacity')
            logging.error('Complete cycle operation response exceeds frame capacity: %s', value)
            failure = {'status': 'capacity_exceeded',
                       'reason': 'Complete original result exceeds the cycle frame capacity'}
            if '_stdout_ref' in value:
                failure['_stdout_ref'] = value['_stdout_ref']
            encoded = json.dumps({**identity, 'event': event, field: failure},
                ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if identity['protocol'] == 'ergora-training-cycle-operation-v2' and len(encoded) > (
                65_536 if event == 'stopped' else _CYCLE_LIMIT):
            raise ValueError('Complete replacement cycle operation frame still exceeds its capacity')
        sys.stdout.buffer.write(encoded + b'\n')
        sys.stdout.buffer.flush()

    result = processes.run([sys.executable, '-P', '-c',
        'from ergora.reference_training_worker import cycle_operation_main;cycle_operation_main(False)'],
        Path.cwd(), output / 'helper', 60, raw.decode('utf-8'), dict(os.environ),
        supervised=True, stop_requested=stopped)
    frame('stopped', 'process', result)
    observed = {
        'status': 'unknown', 'reason': 'Original cycle helper did not complete within its allowance',
        'helper_status': result['status']}
    if result['status'] == 'succeeded':
        try:
            stdout = training_cycles._read_bytes(output / 'helper/stdout.txt', _CYCLE_LIMIT)
        except _CycleCapacityError as error:
            logging.exception('Complete cycle helper stdout retained at %s', output / 'helper/stdout.txt')
            observed = {'status': 'capacity_exceeded', 'reason': str(error)}
        else:
            observed = protocol.decode(stdout)
            observed['_stdout_ref'] = {'file': 'helper/stdout.txt', 'bytes': len(stdout),
                                       'sha256': hashlib.sha256(stdout).hexdigest()}
    frame('result', 'result', observed)


def create_adapter():
    """Use the pinned native create algorithm; gate its final lookup under its lock."""
    from agent_platform.training import LocalTrainingAdapter, STATE

    class BudgetAdapter(LocalTrainingAdapter):
        def budget_for(self, experiment, intent=None):
            ident = experiment.binding.experiment_id
            if intent is None:
                path = STATE / 'ergora/training-submissions' / (ident + '.intent.json')
                intent = json.loads(training_cycles._read_bytes(path, 16 * 1_048_576))
            validate_binding(intent.get('budget'))
            state = State(Path(intent['control_home']))
            directory = training_cycles._directory(state.root, intent['project'], intent['budget']['cycle_id'])
            plan, _, _ = training_cycles._load(state.root, intent['project'], intent['budget']['cycle_id'], directory)
            operation = _Submission({'project': plan['project'], 'control_home': str(state.root),
                                     'experiment_id': ident, 'operation': 'status',
                                     'timeout': plan['definition']['budget']['control_timeout_seconds']})
            original = operation.load()
            if (operation.root != STATE or operation.sha(original) != operation.sha(intent)
                    or operation.sha(original['observation']['experiment']['spec']) != operation.sha(asdict(experiment))):
                raise ValueError('Budget worker input differs from its original native state or complete Experiment')
            return BudgetedStart(operation, original)

        async def create_job_if_absent(self, experiment, manifest):
            path = STATE / 'ergora/training-submissions' / (experiment.binding.experiment_id + '.intent.json')
            try:
                intent = json.loads(training_cycles._read_bytes(path, 16 * 1_048_576))
            except (OSError, ValueError, RecursionError):
                intent = None
            binding = intent.get('budget') if isinstance(intent, dict) else None
            if not isinstance(binding, dict) or 'controller' not in binding:
                # Preserve the original manual gate: existing jobs are returned
                # without rereading start authority. An absent job still reaches
                # budget_for under the original lock and fails on unreadable intent.
                token = _CREATING.set((None, None))
                try:
                    return await super().create_job_if_absent(experiment, manifest)
                finally:
                    _CREATING.reset(token)
            budget = self.budget_for(experiment, intent)
            with budget.permission() as parent:
                await budget.check_controller_history()
                token = _CREATING.set((budget, parent))
                try:
                    return await super().create_job_if_absent(experiment, manifest)
                finally:
                    _CREATING.reset(token)

        async def lookup_job(self, experiment):
            job = await super().lookup_job(experiment)
            creating = _CREATING.get()
            if creating is not None and job is None:
                budget, parent = creating
                if budget is None:
                    budget = self.budget_for(experiment)
                budget.require_active(owner=True)
                if parent is not None:
                    parent.check()
            return job

    return BudgetAdapter()

async def _cycle_capacity(value, converter):
    from temporalio.api.common.v1 import Payloads
    from temporalio.exceptions import ApplicationError

    encoded = await converter.encode([value])
    if Payloads(payloads=encoded).ByteSize() > _CYCLE_LIMIT:
        logging.error('Complete cycle activity capacity failure; full unsent value: %s', value)
        raise ApplicationError('Complete cycle activity payload exceeds 32 KiB; no facts were truncated',
                               type='cycle_activity_capacity_exceeded', non_retryable=True)


if workflow is not None:
    @workflow.defn(name='TrainingCycleWorkflow')
    class TrainingCycleWorkflow:
        """Observe one original candidate; history owns its two effect opportunities."""

        @workflow.init
        def __init__(self, original: dict):
            # init receives the original input before any early signal handler runs.
            self._input = original
            self._controller = self._candidate = self._binding = self._job = None
            self._submission, self._records = {}, {}
            self._boot = self._control = self._work = self._total = None
            self._normal = self._stop_handle = None
            self._stop_reason = None
            self._cancelled = self._existing_execution = self._reconciled = False
            self._state = {'phase': 'COLD_OBSERVING', 'outcome': None, 'observation_count': 0,
                'start_scheduled': False, 'request_scheduled': False, 'last_normal_activity_id': None,
                'stop_activity_id': None, 'stop_activity_status': 'not_scheduled',
                'last_facts_operation_id': None, 'last_signal_rejection': None,
                'candidate_executor_stop_confirmed': None}

        def _capacity(self, value):
            if workflow.payload_converter().to_payloads_wrapper([value]).ByteSize() > _CYCLE_LIMIT:
                raise ApplicationError('Complete cycle Workflow payload exceeds 32 KiB; nothing was truncated',
                                       type='cycle_workflow_capacity_exceeded', non_retryable=True)

        @workflow.query
        def status(self) -> dict:
            info = workflow.info()
            value = {'schema_version': 1, 'protocol': 'ergora-training-cycle-workflow-v1',
                'workflow_id': info.workflow_id, 'run_id': info.run_id,
                'input_sha256': self._input.get('input_sha256'),
                'authorization_sha256': self._input.get('authorization_sha256'), 'ordinal': 0,
                **self._state, 'continuation': 'disabled_until_c1d', 'measurement_accepted': None,
                'stop_durable': None, 'admission_drained': None, 'executor_stop_confirmed': None}
            self._capacity(value)
            return value

        @workflow.signal
        def request_stop(self, request):
            try:
                self._capacity(request)
                protocol.validate_cycle_activity_request(request, 'stop')
                if request['workflow_input'] != self._input:
                    raise ValueError('Stop signal differs from the complete original Workflow input')
            except ApplicationError:
                self._state['last_signal_rejection'] = 'signal_capacity_exceeded'
                return
            except (ValueError, KeyError, TypeError):
                self._state['last_signal_rejection'] = 'signal_identity_or_shape_rejected'
                return
            if self._stop_reason is None:
                self._stop_reason = request['reason']

        def _guard(self):
            info = workflow.info()
            if self._state['observation_count'] >= 256:
                self._stop_reason = self._stop_reason or 'ordinary_activity_limit'
            elif info.get_current_history_length() >= 8000 or info.get_current_history_size() >= 8 * 1024 * 1024:
                self._stop_reason = self._stop_reason or 'history_capacity_limit'
            elif self._work is not None and workflow.now() >= self._work:
                self._stop_reason = self._stop_reason or 'work_budget_exhausted'
            return self._stop_reason is None

        async def _ordinary(self, action, *, cold=False):
            if not self._guard():
                return None, None
            scheduled = workflow.now()
            seconds = 10 if cold else min((self._work - scheduled).total_seconds(), self._control, 10)
            if seconds <= 0:
                self._stop_reason = 'work_budget_exhausted'
                return None, None
            request = {'workflow_input': self._input, 'ordinal': 0}
            self._capacity(request)
            self._state['observation_count'] += 1
            ident = 'candidate-0-' + str(self._state['observation_count'])
            self._state['last_normal_activity_id'] = ident
            if action == 'start':
                self._state.update(start_scheduled=True, phase='STARTING')
            elif action == 'reconcile':
                self._reconciled = True
                self._state['phase'] = 'RECONCILING'
            elif action == 'request-execution-or-observe':
                self._state.update(request_scheduled=True, phase='REQUESTING')
            self._normal = workflow.start_activity(protocol.CYCLE_ACTIVITY_NAMES[action], request,
                activity_id=ident, task_queue=protocol.CYCLE_TASK_QUEUE,
                schedule_to_close_timeout=timedelta(seconds=seconds),
                start_to_close_timeout=timedelta(seconds=seconds), retry_policy=RetryPolicy(maximum_attempts=1),
                cancellation_type=workflow.ActivityCancellationType.TRY_CANCEL)
            # Retrieving an eventual failure retains ownership even when independent stop finishes first.
            self._normal.add_done_callback(lambda done: None if done.cancelled() else done.exception())
            # Never await the activity directly: cancellation must reach run before H cleanup finishes.
            await workflow.wait_condition(lambda: self._normal.done() or (not cold and self._stop_reason is not None))
            if not self._normal.done():
                return None, scheduled
            try:
                return self._normal.result(), scheduled
            except ActivityError as error:
                if isinstance(error.cause, ApplicationError) and error.cause.type in (
                        'cycle_activity_request_rejected', 'cycle_activity_capacity_exceeded'):
                    self._stop_reason = self._stop_reason or 'activity_rejected'
                return None, scheduled

        @staticmethod
        def _number(value):
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('Cycle budget requires a finite number')
            return value

        def _narrow_total(self, sample, scheduled):
            total = self._number(sample['total_remaining_seconds'])
            boot = sample['boot_id']
            if not isinstance(boot, str) or not boot or self._boot is not None and boot != self._boot:
                raise ValueError('Cycle budget lost its original BOOT identity')
            deadline = scheduled + timedelta(seconds=total)
            self._total = min(self._total, deadline) if self._total is not None else deadline
            self._boot = boot

        def _consume(self, value, action, scheduled):
            version2 = action in ('observe-candidate', 'request-execution-or-observe')
            protocol._exact(value, ('schema_version', 'protocol', 'action', 'status', 'workflow_input',
                'controller', 'observation', 'inspection', 'operations', 'runtime_status',
                *(('facts',) if version2 else ())), 'Cycle activity envelope')
            if (type(value['schema_version']) is not int or value['schema_version'] != (2 if version2 else 1)
                    or value['protocol'] != ('ergora-training-cycle-activity-v2' if version2 else 'ergora-training-cycle-activity-v1')
                    or value['action'] != action or value['status'] not in ('observed', 'unknown')
                    or value['workflow_input'] != self._input):
                raise ValueError('Cycle activity lost its original wire or Workflow input')
            controller = value['controller']
            protocol._exact(controller, ('workflow_id', 'run_id', 'intent_sha256'), 'Cycle controller projection')
            info = workflow.info()
            protocol._digest(controller['intent_sha256'])
            if (controller['workflow_id'] != info.workflow_id or controller['run_id'] != info.run_id
                    or self._controller is not None and controller != self._controller):
                raise ValueError('Cycle activity lost its original controller run')
            self._controller = controller
            if not version2:
                self._narrow_total(value['observation'], scheduled)
                return None
            facts = value['facts']
            if (facts is None and value['status'] == 'unknown' and action == 'request-execution-or-observe'
                    and self._state['request_scheduled'] and self._work is not None):
                # H can publish, then lose its completion frame. The authenticated
                # cold envelope may only narrow total; the consumed request stays consumed.
                self._narrow_total(value['observation'], scheduled)
                return None
            protocol._exact(facts, ('source_operation_id', 'budget', 'candidate', 'submission',
                'execution', 'runtime', 'native', 'request_outcome'), 'Cycle candidate facts')
            records = [value['inspection'], *value['operations']]
            if (not isinstance(facts['source_operation_id'], str)
                    or re.fullmatch('[a-f0-9]{32}', facts['source_operation_id']) is None
                    or not any(isinstance(item, dict) and item.get('operation_id') == facts['source_operation_id'] for item in records)):
                raise ValueError('Candidate facts have no original operation in this envelope')
            candidate = facts['candidate']
            protocol._exact(candidate, ('ordinal', 'experiment_id', 'manifest_sha256', 'project_revision',
                'current_project_matches', 'parent_stop_visible'), 'Cycle candidate projection')
            protocol._digest(candidate['manifest_sha256'])
            identity = {key: candidate[key] for key in ('ordinal', 'experiment_id', 'manifest_sha256', 'project_revision')}
            if (type(candidate['ordinal']) is not int or candidate['ordinal'] != 0
                    or not isinstance(candidate['experiment_id'], str) or not candidate['experiment_id']
                    or type(candidate['project_revision']) is not int or candidate['project_revision'] < 1
                    or candidate['current_project_matches'] is not True or candidate['parent_stop_visible'] is not False
                    or self._candidate is not None and identity != self._candidate):
                raise ValueError('Candidate identity, project or parent stop is not confirmed')
            submitted, execution, runtime, native = (facts[key] for key in ('submission', 'execution', 'runtime', 'native'))
            protocol._exact(submitted, ('state', 'intent_sha256', 'workflow_id', 'run_id',
                'attempt_saved', 'result_saved'), 'Candidate submission projection')
            if (submitted['state'] not in ('not_recorded', 'prepared', 'unknown', 'submitted', 'rejected')
                    or type(submitted['attempt_saved']) is not bool or type(submitted['result_saved']) is not bool
                    or not isinstance(submitted['workflow_id'], str) or not submitted['workflow_id']):
                raise ValueError('Candidate submission has no complete original identity')
            for key in ('intent_sha256', 'workflow_id', 'run_id'):
                previous = self._submission.get(key)
                current = submitted[key]
                if previous is not None and previous != current:
                    raise ValueError('Candidate submission original identity changed')
                if current is not None:
                    if not isinstance(current, str) or not current:
                        raise ValueError('Candidate submission identity is incomplete')
                    if key == 'intent_sha256':
                        protocol._digest(current)
            for key in ('attempt_saved', 'result_saved'):
                if self._submission.get(key) is True and submitted[key] is not True:
                    raise ValueError('Candidate submission lost an immutable checkpoint')
            if (submitted['state'] == 'not_recorded' and (submitted['intent_sha256'] is not None
                    or submitted['run_id'] is not None or submitted['attempt_saved'] or submitted['result_saved'])
                    or submitted['state'] != 'not_recorded' and submitted['intent_sha256'] is None
                    or submitted['state'] == 'submitted' and (not submitted['attempt_saved']
                        or not submitted['result_saved'] or submitted['run_id'] is None)):
                raise ValueError('Candidate submission state conflicts with its checkpoints')
            protocol._exact(execution, ('state', 'request_sha256', 'record_sha256', 'reap_record_observed',
                'durable_stop_confirmed', 'executor_stop_confirmed'), 'Candidate execution projection')
            if not isinstance(execution['record_sha256'], dict) or execution['state'] not in (
                    'unknown', 'not_requested', 'requested', 'launch_consumed', 'attempted', 'acknowledged', 'stop_observed', 'stopped'):
                raise ValueError('Candidate execution projection is incomplete')
            for key, digest in execution['record_sha256'].items():
                if key not in ('request', 'launch', 'attempt', 'ack', 'stopped'):
                    raise ValueError('Unknown candidate execution record')
                protocol._digest(digest)
            if any(execution['record_sha256'].get(key) != digest for key, digest in self._records.items()):
                raise ValueError('Candidate execution lost an original immutable record')
            if (execution['request_sha256'] != execution['record_sha256'].get('request')
                    or execution['state'] == 'not_requested' and execution['record_sha256']):
                raise ValueError('Candidate request differs from its original execution chain')
            for key in ('reap_record_observed', 'durable_stop_confirmed', 'executor_stop_confirmed'):
                if execution[key] is not None and type(execution[key]) is not bool:
                    raise ValueError('Candidate execution stop fact is not typed')
            protocol._exact(runtime, ('state', 'workflow_id', 'run_id', 'temporal_status', 'terminal',
                'phase', 'binding', 'job_id'), 'Candidate runtime projection')
            protocol._exact(native, ('state', 'job_id'), 'Candidate native projection')
            if (runtime['state'] not in ('not_queried', 'queried', 'unconfirmed', 'not_found')
                    or native['state'] not in ('not_queried', 'unconfirmed', 'QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED')):
                raise ValueError('Unsupported candidate runtime or native state')
            if runtime['state'] == 'queried':
                if (runtime['workflow_id'] != submitted['workflow_id'] or runtime['run_id'] != submitted['run_id']
                        or submitted['state'] != 'submitted' or type(runtime['terminal']) is not bool):
                    raise ValueError('Candidate runtime differs from the fixed submitted run')
                binding = runtime['binding']
                if binding is not None:
                    protocol._exact(binding, ('experiment_id', 'manifest_sha', 'candidate_sha', 'baseline_sha'), 'Candidate Binding')
                    if (binding['experiment_id'] != candidate['experiment_id'] or binding['manifest_sha'] != candidate['manifest_sha256']
                            or self._binding is not None and binding != self._binding):
                        raise ValueError('Candidate runtime Binding changed')
                    for key in ('candidate_sha', 'baseline_sha'):
                        if not isinstance(binding[key], str) or re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}', binding[key]) is None:
                            raise ValueError('Candidate Binding requires full Git object IDs')
                    self._binding = binding
            if runtime['job_id'] is not None and native['job_id'] is not None and runtime['job_id'] != native['job_id']:
                raise ValueError('Candidate runtime and native job differ')
            for job in (runtime['job_id'] if runtime['state'] == 'queried' else None,
                        native['job_id'] if native['state'] not in ('not_queried', 'unconfirmed') else None):
                if job is not None:
                    if not isinstance(job, str) or not job or self._job is not None and job != self._job:
                        raise ValueError('Candidate lost its original job identity')
                    self._job = job
            budget = facts['budget']
            protocol._exact(budget, ('state', 'work_remaining_seconds', 'total_remaining_seconds',
                'control_timeout_seconds', 'boot_id', 'boottime_ns', 'observed_at'), 'Candidate budget projection')
            work = self._number(budget['work_remaining_seconds'])
            control = self._number(budget['control_timeout_seconds'])
            if (budget['state'] not in ('valid', 'exhausted') or control <= 0
                    or self._control is not None and control != self._control):
                raise ValueError('Candidate budget is not its original valid policy')
            self._narrow_total(budget, scheduled)
            deadline = scheduled + timedelta(seconds=work)
            self._work = min(self._work, deadline) if self._work is not None else deadline
            self._control, self._candidate, self._submission = control, identity, submitted
            self._records = execution['record_sha256']
            self._existing_execution |= bool(self._records) or execution['state'] not in ('unknown', 'not_requested')
            self._state.update(last_facts_operation_id=facts['source_operation_id'],
                candidate_executor_stop_confirmed=execution['executor_stop_confirmed'])
            return facts

        def _next(self, facts, observed):
            if not self._guard():
                return None
            candidate, submitted, execution, runtime, native = (facts[key] for key in
                ('candidate', 'submission', 'execution', 'runtime', 'native'))
            if (submitted['state'] == 'rejected' or execution['state'] == 'unknown'
                    or runtime['state'] == 'not_found' or native['state'] in ('FAILED', 'CANCELLED')
                    or runtime['state'] == 'queried' and (runtime['phase'] in (
                        'GATE_FAILED', 'NEEDS_RECONCILIATION', 'CANCELLED', 'CANCEL_UNCONFIRMED', 'FAILED')
                        or runtime['terminal'] and runtime['phase'] not in ('RELEASE_EXPIRED', 'INTEGRATION_TASK_CREATED'))):
                self._stop_reason = 'candidate_needs_reconciliation'
                return None
            same_job = (isinstance(runtime['job_id'], str) and bool(runtime['job_id'])
                        and native['job_id'] == runtime['job_id'])
            if (observed and submitted['state'] == 'submitted' and runtime['state'] == 'queried'
                    and runtime['binding'] is not None and same_job and native['state'] == 'SUCCEEDED'
                    and execution['durable_stop_confirmed'] is True and execution['executor_stop_confirmed'] is True
                    and (runtime['phase'] == 'AWAITING_RELEASE' and runtime['terminal'] is False
                        or runtime['phase'] in ('RELEASE_EXPIRED', 'INTEGRATION_TASK_CREATED') and runtime['terminal'] is True)):
                self._state.update(phase='FIRST_ROUND_OBSERVED', outcome='first_round_observed_c1d_required')
                return None
            positive = (observed and facts['budget']['state'] == 'valid'
                        and candidate['current_project_matches'] is True and candidate['parent_stop_visible'] is False)
            if submitted['state'] == 'not_recorded':
                if positive and not self._state['start_scheduled'] and not self._existing_execution:
                    return 'start'
                self._stop_reason = self._stop_reason or 'submission_not_confirmed'
                return None
            if submitted['state'] in ('prepared', 'unknown'):
                if submitted['attempt_saved'] and not self._reconciled:
                    return 'reconcile'
                self._stop_reason = 'submission_not_confirmed'
                return None
            self._state['phase'] = 'OBSERVING_EXECUTION' if self._existing_execution or self._state['request_scheduled'] else 'WAITING_FOR_QUEUED'
            if (positive and not self._existing_execution and not self._state['request_scheduled']
                    and execution['state'] == 'not_requested' and runtime['state'] == 'queried'
                    and runtime['terminal'] is False and runtime['phase'] == 'QUEUED'
                    and runtime['binding'] is not None and native['state'] == 'QUEUED' and same_job):
                return 'request-execution-or-observe'
            return 'observe-candidate'

        async def _stop(self):
            self._state.update(phase='STOPPING', outcome='needs_reconciliation')
            if self._normal is not None and not self._normal.done():
                self._normal.cancel()
            scheduled = workflow.now()
            seconds = (self._total - scheduled).total_seconds() if self._total is not None else 0
            if seconds <= 0:
                self._state.update(phase='NEEDS_RECONCILIATION', stop_activity_status='budget_unconfirmed_or_exhausted')
                return
            request = {'workflow_input': self._input, 'reason': self._stop_reason}
            self._capacity(request)
            self._state.update(stop_activity_id='cycle-stop', stop_activity_status='scheduled')
            self._stop_handle = workflow.start_activity(protocol.CYCLE_ACTIVITY_NAMES['stop'], request,
                activity_id='cycle-stop', task_queue=protocol.CYCLE_STOP_TASK_QUEUE,
                schedule_to_close_timeout=timedelta(seconds=seconds), start_to_close_timeout=timedelta(seconds=seconds),
                retry_policy=RetryPolicy(maximum_attempts=1),
                cancellation_type=workflow.ActivityCancellationType.WAIT_CANCELLATION_COMPLETED)
            while True:
                try:
                    result = await asyncio.shield(self._stop_handle)
                    # Old stop.v1 transports observations; it has no cycle-level durable stop proof.
                    self._state['stop_activity_status'] = 'returned'
                    self._consume(result, 'stop', scheduled)
                    break
                except asyncio.CancelledError:
                    self._cancelled = True
                except ActivityError:
                    self._state['stop_activity_status'] = 'failed'
                    break
                except (ValueError, KeyError, TypeError, OverflowError):
                    self._state['stop_activity_status'] = 'observation_rejected'
                    break
            self._state['phase'] = 'NEEDS_RECONCILIATION'

        @workflow.run
        async def run(self, original: dict) -> dict:
            try:
                protocol.validate_cycle_activity_request({'workflow_input': original}, 'inspect')
                self._capacity(original)
            except (ValueError, KeyError, TypeError) as error:
                raise ApplicationError(str(error), type='cycle_workflow_input_rejected', non_retryable=True) from error
            action, cold = 'observe-candidate', True
            try:
                while self._guard():
                    value, scheduled = await self._ordinary(action, cold=cold)
                    if value is not None:
                        facts = self._consume(value, action, scheduled)
                        if self._stop_reason is None and facts is not None:
                            action = self._next(facts, value['status'] == 'observed')
                        else:
                            action = 'observe-candidate'
                    else:
                        action = 'observe-candidate'
                    if self._state['outcome'] == 'first_round_observed_c1d_required':
                        return self.status()
                    if cold and self._work is None:
                        self._stop_reason = self._stop_reason or 'cold_budget_unconfirmed'
                    cold = False
                    if not self._guard():
                        break
                    if action == 'observe-candidate':
                        try:
                            await workflow.wait_condition(lambda: self._stop_reason is not None,
                                timeout=timedelta(seconds=min(1, (self._work - workflow.now()).total_seconds())))
                        except TimeoutError:
                            pass
            except asyncio.CancelledError:
                self._cancelled = True
                self._stop_reason = self._stop_reason or 'workflow_cancelled'
            except ApplicationError:
                self._stop_reason = self._stop_reason or 'workflow_payload_rejected'
            except (ValueError, KeyError, TypeError, OverflowError):
                self._stop_reason = self._stop_reason or 'activity_observation_rejected'
            await self._stop()
            if self._cancelled:
                raise asyncio.CancelledError()
            return self.status()


def create_cycle_workflow():
    """Resolve the optional SDK class without constructing an unimportable local class."""
    if workflow is None:
        raise RuntimeError('Training cycle Workflow requires ergora[temporal]')
    return TrainingCycleWorkflow


def create_cycle_activities(client):
    """Load optional SDK decorators only for the enabled cycle service."""
    from temporalio import activity
    from temporalio.exceptions import ApplicationError

    async def invoke(action, request):
        await _cycle_capacity(request, client.data_converter)
        try:
            protocol.validate_cycle_activity_request(request, action)
            info = activity.info()
            if getattr(info, 'is_local', False):
                raise ValueError('Local activities cannot control a training cycle')
            source = {name: getattr(info, name, None) for name in ('workflow_id', 'workflow_run_id',
                'workflow_type', 'workflow_namespace', 'namespace', 'activity_id', 'activity_type', 'task_queue', 'attempt')}
            context = {'workflow_input': request['workflow_input'], 'activity_source': source,
                       'service_namespace': client.namespace}
            protocol.validate_cycle_activity_context(context)
            if source['activity_type'] != protocol.CYCLE_ACTIVITY_NAMES[action]:
                raise ValueError('SDK source differs from the registered activity action')
            if action == 'start' and request['ordinal'] != 0:
                raise ValueError('successor_not_enabled')
        except (ValueError, TypeError, KeyError) as error:
            raise ApplicationError(str(error), type='cycle_activity_request_rejected', non_retryable=True) from error
        original = request['workflow_input']
        version2 = action in ('request-execution-or-observe', 'observe-candidate')
        arguments = (Path(original['control_home']), original['project'], original['cycle_id'], original['authorization_sha256'])
        cold = _CycleOperation(*arguments, 'inspect-controller-activity', activity_context=context)
        inspection = await cold.run()
        if inspection['status'] == 'capacity_exceeded':
            raise ApplicationError(inspection['reason'], type='cycle_activity_capacity_exceeded', non_retryable=True)
        records = [_activity_operation_result(cold, inspection)]
        outcome = inspection
        if inspection['status'] == 'inspected':
            snapshot = inspection['snapshot']
            if version2:
                policy, clock = snapshot['policy'], snapshot['authorization']['clock']
                window = dict(cold.payload['bootstrap'])
                window['deadline_ns'] = min(window['deadline_ns'],
                    window['started_ns'] + policy['control_timeout_seconds'] * 1_000_000_000,
                    clock['boottime_ns'] + (policy['wall_seconds'] - policy['cleanup_seconds']) * 1_000_000_000)
                budget = inspection['facts']['budget']
                if budget['state'] == 'valid' and budget['work_remaining_seconds'] > 0:
                    binding = {'protocol': original['protocol'], **inspection['controller'], 'ordinal': request['ordinal']}
                    mode = ('request-execution-candidate' if action == 'request-execution-or-observe'
                            and source['attempt'] == 1 else 'observe-candidate')
                    operation = _CycleOperation(*arguments, mode, snapshot=snapshot,
                        ordinal=request['ordinal'], start_context={'controller': binding},
                        activity_context=context, window=window)
                    outcome = await operation.run()
                    records.append(_activity_operation_result(operation, outcome))
            elif action in ('start', 'reconcile'):
                binding = {'protocol': original['protocol'], **inspection['controller'], 'ordinal': request['ordinal']}
                if action == 'start' and source['attempt'] == 1 and not inspection['candidate_exists']:
                    candidate = _CycleCandidate(*arguments, snapshot=snapshot, controller=binding, activity_context=context)
                    outcome = await candidate.run()
                    records.extend(_activity_operation_result(operation, value)
                                   for operation, value in zip(candidate.operations, candidate.results))
                    # H references do not archive observations made later by its parent.
                    # Keep a separate inline observation of that same actual operation.
                    parent_result = {key: value for key, value in outcome.items()
                                     if key not in ('preparation', 'confirmation')}
                    if parent_result != candidate.results[-1]:
                        records.append(_activity_operation_result(candidate.operation, candidate.results[-1])
                                       | {'result': {'inline': parent_result}})
                else:
                    operation = _CycleOperation(*arguments, 'reconcile-candidate', snapshot=snapshot,
                        ordinal=request['ordinal'], start_context={'controller': binding},
                        activity_context=context, window=cold.payload['bootstrap'])
                    outcome = await operation.run()
                    records.append(_activity_operation_result(operation, outcome))
            elif action == 'stop':
                outcome = await stop_live_controller(*arguments, reason=request['reason'], inspection=inspection,
                    activity_context=context, operation_records=records)
        if outcome.get('status') == 'capacity_exceeded' or any(
                item.get('status') == 'capacity_exceeded' for item in outcome.get('operations', [])):
            logging.error('Complete cycle operation capacity failure; outcome: %s; operations: %s', outcome, records)
            raise ApplicationError('Complete original operation result exceeded its frame capacity',
                                   type='cycle_activity_capacity_exceeded', non_retryable=True)
        envelope = {'schema_version': 2 if version2 else 1,
            'protocol': 'ergora-training-cycle-activity-v2' if version2 else 'ergora-training-cycle-activity-v1', 'action': action,
            'status': 'observed' if inspection['status'] == 'inspected' and outcome.get('status') != 'unknown' else 'unknown',
            'workflow_input': original, 'controller': inspection.get('controller'),
            'observation': inspection.get('observation'), 'inspection': records[0], 'operations': records[1:],
            'runtime_status': outcome.get('runtime_status', inspection.get('runtime_status', 'not_queried'))}
        if version2:
            # These are H-produced values already in memory, never reads through refs.
            envelope['facts'] = outcome.get('facts')
            if outcome.get('candidate_observation', {}).get('status') == 'unknown':
                envelope['status'] = 'unknown'
            if envelope['facts'] is not None:
                budget = envelope['facts']['budget']
                envelope['observation'] = {key: budget[key] for key in
                    ('total_remaining_seconds', 'boot_id', 'boottime_ns', 'observed_at')}
        await _cycle_capacity(envelope, client.data_converter)
        return envelope

    registered = {}
    for action, name in protocol.CYCLE_ACTIVITY_NAMES.items():
        # Each closure is a real async SDK activity with one strict business request.
        def build(selected):
            async def execute(request: dict) -> dict:
                try:
                    return await invoke(selected, request)
                except _CycleCapacityError as error:
                    logging.error('Cycle activity request capacity failure: %s', error)
                    raise ApplicationError(str(error), type='cycle_activity_capacity_exceeded', non_retryable=True) from error
            return execute
        registered[action] = activity.defn(name=name)(build(action))
    return registered


async def _serve_cycle() -> None:
    from perf_temporal.connection import connect
    from temporalio.worker import Worker

    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(signum, stopped.set)
    workers, running = [], []
    waiting = asyncio.create_task(stopped.wait())

    async def connect_bounded():
        async with asyncio.timeout(60):
            while True:
                try:
                    return await connect()
                except (OSError, RuntimeError):
                    await asyncio.sleep(1)

    connecting = asyncio.create_task(connect_bounded())
    failure = None

    async def fatal(error):
        nonlocal failure
        if failure is None:
            failure = error
        # SDK calls this before waiting for active activities to finish cleanup.
        stopped.set()

    try:
        await asyncio.wait((connecting, waiting), return_when=asyncio.FIRST_COMPLETED)
        if stopped.is_set():
            return
        client = connecting.result()
        activities = create_cycle_activities(client)
        workers = [Worker(client, task_queue=protocol.CYCLE_TASK_QUEUE,
            workflows=[create_cycle_workflow()],
            activities=[activities[action] for action in protocol.CYCLE_ACTIVITY_NAMES if action != 'stop'],
            max_concurrent_activities=1, graceful_shutdown_timeout=timedelta(0), on_fatal_error=fatal),
            Worker(client, task_queue=protocol.CYCLE_STOP_TASK_QUEUE, activities=[activities['stop']],
            max_concurrent_activities=1, graceful_shutdown_timeout=timedelta(0), on_fatal_error=fatal)]
        running = [asyncio.create_task(worker.run()) for worker in workers]
        done, _ = await asyncio.wait((*running, waiting), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task in running and not task.cancelled() and failure is None:
                failure = task.exception()
    finally:
        # Explicit ordered shutdown retains stop capacity while normal owns live S/H or a pending root.
        async def finish():
            nonlocal failure
            for worker, task in zip(workers, running):
                shutdown = None
                if not task.done():
                    shutdown = asyncio.create_task(worker.shutdown())
                    # Validation can fail after the check above. A terminal run
                    # owns no remaining cleanup, but SDK shutdown may still wait.
                    await asyncio.wait((task, shutdown), return_when=asyncio.FIRST_COMPLETED)
                outcome = (await asyncio.gather(task, return_exceptions=True))[0]
                if shutdown is not None:
                    if not shutdown.done():
                        shutdown.cancel()
                    await asyncio.gather(shutdown, return_exceptions=True)
                if isinstance(outcome, Exception) and failure is None:
                    failure = outcome
        cleanup = asyncio.create_task(finish())
        while not cleanup.done():
            try:
                await asyncio.shield(cleanup)
            except asyncio.CancelledError:
                continue
        cleanup.result()
        connecting.cancel()
        waiting.cancel()
        await asyncio.gather(connecting, waiting, return_exceptions=True)
        for signum in (signal.SIGTERM, signal.SIGINT):
            loop.remove_signal_handler(signum)
    if failure is not None:
        raise failure


def cycle_main(installation: str) -> None:
    try:
        import temporalio.worker  # noqa: F401 -- validate the optional dependency before native loading
    except ImportError as error:
        raise SystemExit('Training cycle service requires ergora[temporal]') from error
    root = reference.validate_installation(Path(installation), training=True)
    sys.path[:0] = [str(root / part) for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
    from agent_platform.core import environment

    os.environ.update(environment())
    # H and the independent budget root must import this exact application installation.
    os.environ['PYTHONPATH'] = os.pathsep.join([str(Path(__file__).parent.parent),
        *[str(root / part) for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]])
    asyncio.run(_serve_cycle())


async def _serve() -> None:
    from perf_temporal.activities import Activities
    from perf_temporal.adapter import load_adapter
    from perf_temporal.connection import connect, task_queue
    from perf_temporal.workflow import ExperimentWorkflow
    from temporalio.worker import Worker

    adapter = load_adapter()
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, stopped.set)

    async def connected():
        async with asyncio.timeout(60):
            while True:
                try:
                    return await connect()
                except (OSError, RuntimeError):
                    await asyncio.sleep(1)

    connecting, stopping = asyncio.create_task(connected()), asyncio.create_task(stopped.wait())
    try:
        await asyncio.wait((connecting, stopping), return_when=asyncio.FIRST_COMPLETED)
        if not stopped.is_set():
            async with Worker(connecting.result(), task_queue=task_queue(), workflows=[ExperimentWorkflow],
                              activities=Activities(adapter).registered(), max_concurrent_activities=8):
                await stopped.wait()
    finally:
        for pending in (connecting, stopping):
            pending.cancel()
        await asyncio.gather(connecting, stopping, return_exceptions=True)
        loop.remove_signal_handler(signal.SIGTERM)


def main(installation: str) -> None:
    root = reference.validate_installation(Path(installation), training=True)
    sys.path[:0] = [str(root / part) for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
    from agent_platform.core import environment

    os.environ.update(environment())
    os.environ.update(PERF_CLUSTER_ADAPTER='ergora.reference_training_worker:create_adapter', PERF_TASK_QUEUE=TASK_QUEUE)
    asyncio.run(_serve())


async def _cleanup(budget, context: dict) -> dict:
    budget.validate_cached(context)
    from .reference_training_cancellation import _Cancellation

    timeout = min(context['policy']['control_timeout_seconds'], budget.remaining(context, cleanup=True))
    if timeout <= 0:
        return {'status': 'unknown', 'reason': 'Original cleanup allowance is exhausted'}
    budget.operation.payload['timeout'] = timeout
    submitted = budget.operation.status(budget.intent)
    if submitted.get('attempt_saved') and not submitted.get('result_saved'):
        await asyncio.wait_for(budget.operation.reconcile(budget.intent), timeout)
        submitted = budget.operation.status(budget.intent)
    if submitted['status'] != 'submitted':
        return {'status': 'unknown', 'reason': 'Original start run is unconfirmed; no cancel was sent'}
    original = context['authorization']['registration']
    project = {**context['published_project'], '_original_registration': {
        **original, 'current_project_revision': budget.intent['project_revision']}}
    payload = {**budget.operation.payload, 'project': project, 'operation': 'prepare',
               'request_id': 'budget-' + budget.identity['intent_sha256'][:32],
               'run_id': submitted['run_id'], 'reason': 'Original training computation budget ended'}
    prepared = await _Cancellation(payload).run()
    result = prepared['cancellation']
    payload.update(operation='resume', intent_sha256=result['intent_sha256'])
    return await _Cancellation(payload).run()

def _controller_owner(request: dict) -> dict:
    """Bootstrap the actual original root outside every short S-H subtree."""
    protocol.validate_cycle_root_request(request)
    payload = request['submission']
    source = protocol.decode(protocol.read_raw(Path(payload['control_home']) / 'operations/training-cycles'
        / request['origin_operation_id'] / 'request.json', _CYCLE_LIMIT))
    protocol.cycle_start_source(source)
    identity = source['identity']
    if (identity['mode'] != 'prepare-candidate' or identity['parent'] != request['parent']
            or source['bootstrap'] != request['window'] or identity['control_home'] != payload['control_home']
            or identity['project'] != payload['project']['id']
            or payload['project']['registration']['definition']['execution'] != source['snapshot']['authorization']['execution']
            or payload['timeout'] != source['snapshot']['policy']['control_timeout_seconds']
            or source['snapshot']['candidates'][identity['ordinal']]['experiment_id'] != payload['experiment_id']
            or os.getppid() != request['parent']['pid']
            or processes.identity(request['parent']['pid']) != request['parent']
            or protocol.cycle_operation_remaining(source) <= 0):
        raise ValueError('Controller root lost its complete original prepare request, parent or window')
    _select_cycle_project(source['snapshot']['authorization'], payload['project'])
    operation = _Submission(payload)
    intent = operation.load()
    if (intent is None or operation.sha(intent) != payload['intent_sha256']
            or intent.get('budget', {}).get('controller') != source['start_context']['controller']):
        raise ValueError('Controller root lost its complete original selected training intent')
    budget = BudgetedStart(operation, intent)
    observation = budget.path('launches/' + intent['operation_id'])
    with (observation / 'stdout.json').open('xb') as stdout, (observation / 'stderr.txt').open('xb') as stderr:
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stderr.fileno(), sys.stderr.fileno())
    return budget.own(root_operation=source)


def budget_main() -> None:
    """Dedicated budget process; preserve the original submission context and records."""
    payload = json.load(sys.stdin)
    if payload.get('protocol') == 'ergora-training-cycle-root-v1':
        if len(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')) > _CYCLE_LIMIT:
            raise ValueError('Complete controller root request exceeds 32 KiB')
        result = _controller_owner(payload)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return
    operation = _Submission(payload)
    if payload['mode'] == 'owner':
        intent = operation.load()
        if intent is None or operation.sha(intent) != payload['intent_sha256']:
            raise ValueError('Independent budget owner requires the complete original training intent')
        result = BudgetedStart(operation, intent).own()
    else:
        context = payload['cached']
        if operation.sha(context['intent']) != payload['intent_sha256']:
            raise ValueError('Supervised budget phase differs from its original training intent')
        budget = BudgetedStart(operation, context['intent'])
        if payload['mode'] == 'phase-supervisor':
            budget.supervise_phase(context)
            return
        result = asyncio.run(_cleanup(budget, context) if payload['mode'] == 'cleanup'
                             else budget.helper(payload['mode'], context))
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


def execution_main() -> None:
    """Prepare an explicit request; business execution belongs to the born owner."""
    from agent_platform.core import Blocked, environment
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        os.environ.update(environment())
        operation = _Submission(payload)
        intent = operation.load()
        if intent is None or 'budget' not in intent:
            raise ValueError('Managed execution requires the original budget-bound submission')
        result = asyncio.run(asyncio.wait_for(Execution(operation, BudgetedStart(operation, intent)).request(), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, ImportError, TimeoutError, RPCError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error) + '; observe the original execution request without resending start') from error
