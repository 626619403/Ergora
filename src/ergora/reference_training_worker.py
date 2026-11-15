"""Optional application SDK worker for the versioned, budget-aware training queue."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from dataclasses import asdict
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

from . import budget_clock, processes, reference, training_cycles, training_execution_protocol as protocol
from .reference_training_budget import BudgetedStart, TASK_QUEUE, validate_binding
from .reference_training_submission import _Submission
from .reference_training_execution import Execution
from .state import State, file_lock, now


_CREATING = ContextVar('ergora_training_budget_create', default=None)
_CYCLE_LIMIT = 32_768
_ROOT_OBSERVERS = set()


class _CycleOperation:
    """Asynchronously supervise one isolated original-record operation."""

    def __init__(self, home: Path, project: str, cycle_id: str, authorization_sha256: str, mode: str,
                 *, snapshot: dict | None = None, ordinal: int | None = None,
                 reason: str | None = None, inspection_timeout: int = 10,
                 start_context: dict | None = None, window: dict | None = None):
        bootstrap = window
        if mode in protocol.CYCLE_OBSERVATION_MODES:
            if type(inspection_timeout) is not int or not 1 <= inspection_timeout <= 60:
                raise ValueError('Cold inspection timeout must be 1 to 60 seconds')
            boot, ticks = budget_clock._clock()
            bootstrap = {'boot_id': boot, 'started_ns': ticks,
                         'deadline_ns': ticks + inspection_timeout * 1_000_000_000}
        elif mode in ('prepare-controller', 'submit-controller', 'prepare-candidate') and window is None:
            policy, clock = snapshot['policy'], snapshot['authorization']['clock']
            boot, ticks = budget_clock._clock()
            seconds = min(policy['control_timeout_seconds'], budget_clock.remaining(
                clock, policy['wall_seconds'], policy['cleanup_seconds']))
            bootstrap = {'boot_id': boot, 'started_ns': ticks,
                'deadline_ns': min(ticks + int(seconds * 1_000_000_000), clock['boottime_ns']
                    + (policy['wall_seconds'] - policy['cleanup_seconds']) * 1_000_000_000)}
        self.identity = {'protocol': 'ergora-training-cycle-operation-v1', 'operation_id': uuid.uuid4().hex,
            'mode': mode, 'control_home': str(home), 'project': project, 'cycle_id': cycle_id,
            'input_sha256': snapshot['authorization']['input_sha256'] if snapshot is not None else None,
            'authorization_sha256': authorization_sha256, 'ordinal': ordinal, 'parent': processes.identity(os.getpid())}
        self.payload = {'identity': self.identity, 'snapshot': snapshot, 'bootstrap': bootstrap, 'reason': reason}
        if start_context is not None:
            self.payload['start_context'] = start_context
        protocol.validate_cycle_operation(self.payload)
        self.encoded = json.dumps(self.payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if len(self.encoded) > _CYCLE_LIMIT:
            raise ValueError('Complete cycle operation request exceeds 32 KiB; nothing was truncated')
        self.output = home / 'operations/training-cycles' / self.identity['operation_id']
        self.response = protocol.PhaseFrames(self.identity, self.output, _CYCLE_LIMIT)
        self.stopping, self.signalled, self.sent = False, False, False
        self.process, self.spawning, self.problem = None, None, None
        self.diagnostics = bytearray()

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
            return self.observation(self.response.frames[1]['result'])
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
                 *, snapshot: dict, controller: dict):
        self.preparation = _CycleOperation(home, project, cycle_id, authorization_sha256, 'prepare-candidate',
            snapshot=snapshot, ordinal=controller['ordinal'], start_context={'controller': controller})
        self.operation = self.preparation
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
                'origin_operation_id': identity['operation_id'], **facts})
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

    async def _run(self) -> dict:
        prepared = await self.preparation.run()
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
                raise ValueError('Complete controller root request exceeds 32 KiB; intent remains occupied')
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
                confirmed = await self.next_operation('confirm-candidate', intent_sha256=prepared['intent_sha256'],
                    root_process=self.root_identity).run()
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
                    dispatched = await self.next_operation('dispatch-candidate', intent_sha256=prepared['intent_sha256'],
                        owner=owner).run()
                    return {**dispatched, 'preparation': prepared, 'confirmation': confirmed}
                await asyncio.sleep(.05)
            return {**result, 'reason': 'Original root was not completely confirmed in its one start window'}
        except (OSError, ValueError, TimeoutError) as error:
            return {**result, 'reason': str(error)}
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


def _cycle_operation(payload: dict) -> dict:
    """Run inside a separately supervised H, never inside the async parent loop."""
    identity = payload['identity']
    home, project, cycle = Path(identity['control_home']), identity['project'], identity['cycle_id']
    directory = training_cycles._directory(home, project, cycle)
    plan, authorization, ready = training_cycles._load(home, project, cycle, directory)
    admission = protocol.CycleAdmission(directory, authorization)
    if authorization['sha256'] != identity['authorization_sha256']:
        raise ValueError('Cycle operation requires the complete original authorization SHA256')
    snapshot = _cycle_snapshot(plan, authorization)
    mode = identity['mode']
    if mode == 'inspect':
        # This is only a read of original facts, including an already exhausted clock.
        total = budget_clock.remaining(authorization['clock'], snapshot['policy']['wall_seconds'])
        boot, ticks = budget_clock._clock()
        return {'status': 'inspected', 'snapshot': snapshot,
            'submission': {key: value for key, value in admission.submission().items() if key != 'intent'},
            'observation': {'total_remaining_seconds': total, 'boot_id': boot,
                            'boottime_ns': ticks, 'observed_at': now()}}
    if identity['input_sha256'] != authorization['input_sha256'] or training_cycles._sha(payload['snapshot']) != training_cycles._sha(snapshot):
        raise ValueError('Cycle operation snapshot differs from the complete original records')

    def active():
        if (protocol.cycle_operation_remaining(payload) <= 0
                or processes.identity(identity['parent']['pid']) != identity['parent']):
            raise ValueError('Original cycle operation parent or allowance ended')

    active()
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


def _candidate_operation(payload: dict, plan: dict, admission, active) -> dict:
    """Keep all candidate files, locks and SDK calls within the original H."""
    from . import training

    identity, context = payload['identity'], payload['start_context']
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

            async def reconcile():
                current = admission.submission()
                if current['status'] == 'rejected' or not current['attempt_saved']:
                    return observation(current, runtime_status='not_queried')
                found = await lookup_controller_submission(client, intent, run_id=current['run_id'], timeout=remaining())
                if found is None:
                    return observation(current, status='unknown', runtime_status='not_found')
                _, description = found
                current = training_cycles._record_controller(state, admission, run_id=description.run_id)
                active()
                return observation(current, runtime_status='queried', temporal_status=description.status.name)

            if payload['identity']['mode'] == 'reconcile-controller' or saved['attempt_saved']:
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
                    handle = await client.start_workflow('TrainingCycleWorkflow', intent['workflow_input'],
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


async def stop_live_controller(home: Path, project_id: str, cycle_id: str, authorization_sha256: str,
                               *, reason: str, inspection_timeout: int = 10) -> dict:
    """Observe independent stop branches; no one branch implies the others succeeded."""
    inspection = await _CycleOperation(home, project_id, cycle_id, authorization_sha256, 'inspect',
                                      inspection_timeout=inspection_timeout).run()
    if inspection['status'] != 'inspected':
        return {'status': 'unknown', 'inspection': inspection, 'operations': [], 'runtime_status': 'not_queried'}
    snapshot = inspection['snapshot']
    operations = [_CycleOperation(home, project_id, cycle_id, authorization_sha256, 'stop-writer',
                                   snapshot=snapshot, reason=reason),
                  _CycleOperation(home, project_id, cycle_id, authorization_sha256, 'drain', snapshot=snapshot)]
    for ordinal in range(len(snapshot['candidates'])):
        operations.extend(_CycleOperation(home, project_id, cycle_id, authorization_sha256, mode,
                                          snapshot=snapshot, ordinal=ordinal)
                          for mode in ('notify-owner', 'observe-execution'))
    tasks = [asyncio.create_task(operation.run()) for operation in operations]
    try:
        results = await asyncio.gather(*tasks)
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
        except (OSError, ValueError, KeyError, TypeError) as error:
            result = {'status': 'unknown', 'reason': str(error)}
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
            raise ValueError('Complete cycle operation response exceeds its frame capacity')
        sys.stdout.buffer.write(encoded + b'\n')
        sys.stdout.buffer.flush()

    result = processes.run([sys.executable, '-P', '-c',
        'from ergora.reference_training_worker import cycle_operation_main;cycle_operation_main(False)'],
        Path.cwd(), output / 'helper', 60, raw.decode('utf-8'), dict(os.environ),
        supervised=True, stop_requested=stopped)
    frame('stopped', 'process', result)
    observed = protocol.decode(training_cycles._read_bytes(output / 'helper/stdout.txt', _CYCLE_LIMIT)) if result['status'] == 'succeeded' else {
        'status': 'unknown', 'reason': 'Original cycle helper did not complete within its allowance',
        'helper_status': result['status']}
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
