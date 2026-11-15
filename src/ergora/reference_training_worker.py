"""Optional application SDK worker for the versioned, budget-aware training queue."""

import asyncio
from contextvars import ContextVar
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import uuid

from . import budget_clock, processes, reference, training_cycles, training_execution_protocol as protocol
from .reference_training_budget import BudgetedStart, TASK_QUEUE, validate_binding
from .reference_training_submission import _Submission
from .reference_training_execution import Execution
from .state import State, now


_CREATING = ContextVar('ergora_training_budget_create', default=None)
_CYCLE_LIMIT = 32_768


class _CycleOperation:
    """Asynchronously supervise one isolated original-record operation."""

    def __init__(self, home: Path, project: str, cycle_id: str, authorization_sha256: str, mode: str,
                 *, snapshot: dict | None = None, ordinal: int | None = None,
                 reason: str | None = None, inspection_timeout: int = 10):
        bootstrap = None
        if mode == 'inspect':
            if type(inspection_timeout) is not int or not 1 <= inspection_timeout <= 60:
                raise ValueError('Cold inspection timeout must be 1 to 60 seconds')
            boot, ticks = budget_clock._clock()
            bootstrap = {'boot_id': boot, 'started_ns': ticks,
                         'deadline_ns': ticks + inspection_timeout * 1_000_000_000}
        self.identity = {'protocol': 'ergora-training-cycle-operation-v1', 'operation_id': uuid.uuid4().hex,
            'mode': mode, 'control_home': str(home), 'project': project, 'cycle_id': cycle_id,
            'input_sha256': snapshot['authorization']['input_sha256'] if snapshot is not None else None,
            'authorization_sha256': authorization_sha256, 'ordinal': ordinal, 'parent': processes.identity(os.getpid())}
        self.payload = {'identity': self.identity, 'snapshot': snapshot, 'bootstrap': bootstrap, 'reason': reason}
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
        try:
            self.process = await asyncio.shield(self.spawning)
        except OSError as error:
            return self.observation({'status': 'unknown', 'reason': str(error)})
        tasks = [asyncio.create_task(self._send()), asyncio.create_task(self._read(self.process.stdout)),
                 asyncio.create_task(self._read(self.process.stderr, diagnostic=True)),
                 asyncio.create_task(self.process.wait())]
        while not all(task.done() for task in tasks):
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
            await asyncio.sleep(.05)
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        if (self.process.returncode == 0 and self.sent and len(self.response.frames) == 2
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
            while not running.done():
                try:
                    await asyncio.shield(running)
                except asyncio.CancelledError:
                    continue
            running.result()
            raise


def _cycle_snapshot(plan: dict, authorization: dict) -> dict:
    return {'authorization': authorization, 'policy': plan['definition']['budget'],
        'candidates': [{'ordinal': index, 'experiment_id': item['experiment_id'],
                        'manifest_sha256': item['manifest_sha256']}
                       for index, item in enumerate(plan['definition']['candidates'])]}


def _cycle_target(plan: dict, admission, ordinal: int):
    """Reuse the original start reader; source drift must not prevent exact old-owner cleanup."""
    authorization = admission.authorization
    ident = plan['definition']['candidates'][ordinal]['experiment_id']
    operation = _Submission({'project': plan['project'], 'control_home': authorization['control_home'],
                             'experiment_id': ident})
    intent = operation.load()
    if intent is None:
        return operation, None, None
    admission.bind(intent, plan)
    if (intent['project_revision'] != authorization['project_revision']
            or intent['budget']['controller']['ordinal'] != ordinal):
        raise ValueError('Cycle notification differs from the original selected revision or ordinal')
    try:
        owner = protocol.owner_record(protocol.decode(
            protocol.read_raw(operation.path('.budget/owner.json'))))
    except FileNotFoundError:
        return operation, intent, None
    if owner['intent_sha256'] != training_cycles._sha(intent) or owner['authorization_sha256'] != authorization['sha256']:
        raise ValueError('Cycle target owner differs from its complete original intent or authorization')
    return operation, intent, owner


def _cycle_operation(payload: dict) -> dict:
    """Run inside a separately supervised H, never inside the async parent loop."""
    identity = payload['identity']
    home, project, cycle = Path(identity['control_home']), identity['project'], identity['cycle_id']
    directory = training_cycles._directory(home, project, cycle)
    plan, authorization, _ = training_cycles._load(home, project, cycle, directory)
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
            'observation': {'total_remaining_seconds': total, 'boot_id': boot,
                            'boottime_ns': ticks, 'observed_at': now()}}
    if identity['input_sha256'] != authorization['input_sha256'] or training_cycles._sha(payload['snapshot']) != training_cycles._sha(snapshot):
        raise ValueError('Cycle operation snapshot differs from the complete original records')

    def active():
        if (protocol.cycle_operation_remaining(payload) <= 0
                or processes.identity(identity['parent']['pid']) != identity['parent']):
            raise ValueError('Original cycle operation parent or total allowance ended')

    active()
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

def budget_main() -> None:
    """Dedicated budget process; preserve the original submission context and records."""
    payload = json.load(sys.stdin)
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
