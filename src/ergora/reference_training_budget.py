"""One training intent's budget, native creation gate and independent deadline owner."""

import asyncio
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import sqlite3
import stat
import subprocess
import sys
import time
import uuid

from . import budget_clock, processes, registrations, training_cycles
from .definition_bundles import parse_json
from .state import State, file_lock, now


TASK_QUEUE = 'ergora-training-budget-v1'
_PHASE_PROTOCOL = 'ergora-budget-phase-v1'
_PHASE_MODES = ('monitor', 'fence', 'cleanup', 'publish')
_FINAL_LIMIT = 2 * training_cycles.MAX_RECORD_BYTES


def validate_binding(value: dict) -> None:
    if (not isinstance(value, dict) or set(value) != {'cycle_id', 'authorization_sha256', 'task_queue'}
            or not isinstance(value.get('cycle_id'), str)
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value['cycle_id']) is None
            or not isinstance(value.get('authorization_sha256'), str)
            or re.fullmatch('[a-f0-9]{64}', value['authorization_sha256']) is None
            or value['task_queue'] != TASK_QUEUE):
        raise ValueError('Training intent requires its exact original budget and supported protocol queue')


def prepare_binding(operation, intent: dict, selector: dict) -> dict:
    if not isinstance(selector, dict) or set(selector) != {'cycle_id', 'authorization_sha256'}:
        raise ValueError('Select one original training cycle and complete authorization SHA256')
    binding = {**selector, 'task_queue': TASK_QUEUE}
    validate_binding(binding)
    state = State(Path(operation.payload['control_home']))
    observed = training_cycles.status(state, operation.project['id'], binding['cycle_id'],
                                     authorization_sha256=binding['authorization_sha256'])
    if observed['status'] != 'ready':
        raise ValueError('Original training budget is not ready: ' + observed['status'])
    BudgetedStart(operation, {**intent, 'budget': binding}).require_active()
    return binding


def _process_identity(pid: int) -> dict:
    if type(pid) is not int or pid < 1:
        raise ValueError('Budget owner has no valid process identity')
    fields = Path('/proc/' + str(pid) + '/stat').read_text().rsplit(')', 1)[1].split()
    if fields[0] == 'Z':
        raise ValueError('Original budget owner has exited')
    return {'pid': pid, 'start_ticks': fields[19],
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


class _BudgetPhase:
    """Transfer one phase without making its caller a shared child subreaper."""

    def __init__(self, budget, mode: str, context: dict, *, phase_id: str | None = None,
                 owner: dict | None = None, final: dict | None = None):
        phase_id = uuid.uuid4().hex if phase_id is None else phase_id
        if mode not in _PHASE_MODES or not isinstance(phase_id, str) or re.fullmatch('[a-f0-9]{32}', phase_id) is None:
            raise ValueError('Unknown training budget phase or observation identity')
        self.budget, self.mode, self.context = budget, mode, context
        self.identity = {**budget.identity, 'protocol': _PHASE_PROTOCOL, 'phase_id': phase_id, 'mode': mode,
                         'context_sha256': budget.operation.sha(context),
                         'owner': _process_identity(os.getpid()) if owner is None else owner}
        # The budget folder was validated before its owner started. Actual path
        # checks and storage belong to this phase's S, never its live peers.
        self.relative = 'observations/' + mode + '-' + phase_id
        self.output = budget.folder / self.relative
        self.payload = {**budget.operation.payload, 'mode': mode, 'cached': context,
                        'intent_sha256': budget.identity['intent_sha256'],
                        **({'final': final} if final is not None else {})}
        self.frames, self.buffer, self.problem = [], bytearray(), None
        self.supervisor_returncode = None
        self.stopping, self.signalled, self.done = False, False, False
        self.offset = 0
        self.startup_stderr = bytearray()

    def expired(self, *, total: bool = False) -> bool:
        try:
            return self.budget.remaining(self.context, cleanup=total or self.mode != 'monitor') <= 0
        except (OSError, ValueError):
            return True

    def receive(self, raw: bytes) -> None:
        if self.problem is not None:
            return
        self.buffer.extend(raw)
        while b'\n' in self.buffer:
            line, _, rest = self.buffer.partition(b'\n')
            self.buffer = bytearray(rest)
            event = 'stopped' if not self.frames else 'result'
            limit = 65_536 if event == 'stopped' else 2 * training_cycles.MAX_RECORD_BYTES
            try:
                if len(self.frames) == 2 or len(line) > limit:
                    raise ValueError('Unexpected or oversized training phase frame')
                frame = parse_json(line.decode('utf-8'), 'training budget phase', finite=True)
                field = 'process' if event == 'stopped' else 'result'
                if (not isinstance(frame, dict) or set(frame) != {*self.identity, 'event', field}
                        or any(frame.get(key) != value for key, value in self.identity.items())
                        or frame['event'] != event or not isinstance(frame[field], dict)):
                    raise ValueError('Training phase response differs from its complete original identity or order')
                if event == 'stopped':
                    process = frame[field]
                    if (set(process) != {'status', 'returncode', 'output'}
                            or process['status'] not in ('succeeded', 'failed', 'cancelled', 'timed_out')
                            or process['returncode'] is not None and type(process['returncode']) is not int
                            or process['output'] != str(self.output / 'helper')):
                        raise ValueError('Training phase stopped frame has no complete process observation')
                self.frames.append(frame)
            except (UnicodeError, ValueError) as error:
                self.problem = str(error)
                return
        limit = 65_536 if not self.frames else 2 * training_cycles.MAX_RECORD_BYTES
        if len(self.buffer) > limit:
            self.problem = 'Incomplete training phase frame exceeds its complete response capacity'

    def start(self) -> bool:
        """Launch without reading or writing the business filesystem in the parent."""
        if self.expired() or self.mode == 'monitor' and self.budget.cancelled:
            return False
        self.encoded = json.dumps({**self.payload, 'mode': 'phase-supervisor', 'phase': self.identity},
                                  ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.selected = selectors.DefaultSelector()
        self.process = None
        try:
            self.process = subprocess.Popen([sys.executable, '-P', '-c',
                'from ergora.reference_training_worker import budget_main;budget_main()'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=dict(os.environ), start_new_session=True)
            for stream, event in ((self.process.stdin, selectors.EVENT_WRITE),
                                  (self.process.stdout, selectors.EVENT_READ), (self.process.stderr, selectors.EVENT_READ)):
                os.set_blocking(stream.fileno(), False)
                self.selected.register(stream, event)
        except BaseException:
            self.selected.close()
            # No request bytes have been sent, so this child cannot start work.
            if self.process is not None:
                self.process.terminate()
                self.process.wait()
                for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                    stream.close()
            raise
        return True

    def request_stop(self) -> None:
        """Request this phase's safe reap without waiting for it or a peer."""
        self.stopping = True

    def poll(self, timeout: float = 0) -> bool:
        """Pump this phase's pipes; default polling never waits for a peer."""
        process, selected = self.process, self.selected
        stop = (self.stopping or self.problem is not None or self.expired()
                or self.mode == 'monitor' and self.budget.cancelled)
        if stop and not self.signalled and process.poll() is None:
            process.terminate()
            self.signalled = True
        # This matching frame proves the only child subtree has been reaped.
        # S may only perform direct storage/observation after that frame.
        if self.frames and self.expired(total=True) and process.poll() is None:
            process.kill()
        events = selected.select(timeout)
        for key, event in events:
            stream = key.fileobj
            try:
                if event == selectors.EVENT_WRITE:
                    self.offset += os.write(stream.fileno(), self.encoded[self.offset:self.offset + 65_536])
                    if self.offset == len(self.encoded):
                        selected.unregister(stream)
                        stream.close()
                else:
                    raw = os.read(stream.fileno(), 65_536)
                    if not raw:
                        selected.unregister(stream)
                        stream.close()
                    elif stream is process.stdout:
                        self.receive(raw)
                    else:
                        self.startup_stderr.extend(raw[:max(0, 65_536 - len(self.startup_stderr))])
            except BlockingIOError:
                continue
            except BrokenPipeError:
                selected.unregister(stream)
                stream.close()
        self.done = (process.poll() is not None and (not selected.get_map() or not events))
        return not self.done

    def finish(self) -> dict:
        """Collect an exited phase, or safely stop it for a synchronous caller."""
        self.request_stop()
        try:
            while not self.done:
                self.poll(.2)
        finally:
            self.process.wait()
            self.selected.close()
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                if not stream.closed:
                    stream.close()
        self.supervisor_returncode = self.process.returncode
        if (self.process.returncode == 0 and self.offset == len(self.encoded) and len(self.frames) == 2
                and not self.buffer and self.problem is None and not self.expired()):
            return self.frames[1]['result']
        return {'status': 'unknown', 'phase_id': self.identity['phase_id'],
                'reason': self.problem or self.startup_stderr.decode('utf-8', errors='replace').strip()
                          or 'Original phase has no complete in-budget result',
                'supervisor_returncode': self.process.returncode}

    def run(self) -> dict:
        if not self.start():
            return {'status': 'unknown', 'reason': 'Original training phase allowance is exhausted'}
        try:
            while self.poll(.2):
                pass
        finally:
            result = self.finish()
        return result

    def supervise(self) -> None:
        """Run inside this phase's exclusive Linux subreaper process."""
        if self.identity['owner'] != _process_identity(os.getppid()):
            raise ValueError('Training phase has lost its original parent owner')
        self.output = self.budget.path(self.relative)
        self.output.mkdir(parents=True, mode=0o700)
        with (self.output / 'supervisor.stderr').open('xb') as stderr:
            os.dup2(stderr.fileno(), sys.stderr.fileno())
        cancelled = False

        def cancel(signum, frame):
            nonlocal cancelled
            cancelled = True

        def stopped():
            if cancelled or self.expired():
                return True
            try:
                return self.identity['owner'] != _process_identity(self.identity['owner']['pid'])
            except (OSError, ValueError):
                return True

        def frame(event, field, value):
            print(json.dumps({**self.identity, 'event': event, field: value},
                             ensure_ascii=False, allow_nan=False, separators=(',', ':')), flush=True)

        signal.signal(signal.SIGTERM, cancel)
        signal.signal(signal.SIGINT, cancel)
        result = processes.run([sys.executable, '-P', '-c',
            'from ergora.reference_training_worker import budget_main;budget_main()'], Path.cwd(), self.output / 'helper',
            self.context['policy']['wall_seconds'], json.dumps(self.payload, ensure_ascii=False, allow_nan=False),
            dict(os.environ), supervised=True, stop_requested=stopped)
        frame('stopped', 'process', result)
        observed = training_cycles._document(self.output / 'helper/stdout.txt') if result['status'] == 'succeeded' else {
            'status': 'unknown', 'process': result}
        frame('result', 'result', observed)


class BudgetedStart:
    """Keep caller-independent ownership behind the original immutable start intent."""

    def __init__(self, operation, intent: dict):
        validate_binding(intent['budget'])
        self.operation, self.intent, self.binding = operation, intent, intent['budget']
        self.folder = operation.path('.budget')
        self.identity = {'schema_version': 1, 'intent_sha256': operation.sha(intent),
                         'authorization_sha256': self.binding['authorization_sha256']}

    def path(self, name: str) -> Path:
        return self.operation.path('.budget/' + name)

    def source(self) -> tuple[State, dict, dict, dict]:
        state = State(Path(self.intent['control_home']))
        directory = training_cycles._directory(state, self.intent['project'], self.binding['cycle_id'])
        plan, authorization, ready = training_cycles._load(state, self.intent['project'], self.binding['cycle_id'], directory)
        selected = next((item for item in plan['admissions']
                         if item['experiment_id'] == self.operation.ident), None)
        if (authorization['sha256'] != self.binding['authorization_sha256'] or ready is None
                or authorization['execution'] != self.intent['execution']
                or plan['project']['repo'] != self.intent['repo']
                or plan['project']['registration']['sha256'] != self.intent['registration_sha256']
                or authorization['project_revision'] != self.intent['project_revision']
                or selected is None or self.operation.sha(selected['observation']) != self.operation.sha(self.intent['observation'])):
            raise ValueError('Original training budget differs from its complete start intent, source or admission')
        return state, plan, authorization, ready

    def require_active(self, *, owner: bool = False) -> None:
        state, plan, authorization, ready = self.source()
        observed = training_cycles._status(state, plan, authorization, ready)
        if observed['status'] != 'ready':
            raise ValueError('Original training budget cannot start work: ' + observed['status'])
        if owner and (self.path('final.json').exists() or not self.owner_alive()):
            raise ValueError('Original training budget owner is unconfirmed; do not restart or resend')
        # Full source and process checks consume the same computation window.
        if budget_clock.remaining(authorization['clock'], plan['definition']['budget']['wall_seconds'],
                                  plan['definition']['budget']['cleanup_seconds']) <= 0:
            raise ValueError('Original training computation deadline has passed')

    def owner_record(self) -> dict:
        value = training_cycles._document(self.path('owner.json'))
        process = {name: value.get(name) for name in ('pid', 'start_ticks', 'boot_id')}
        digest = value.get('context_sha256')
        if (not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None
                or value != {**self.identity, **process, 'context_sha256': digest}
                or process != _process_identity(value.get('pid'))):
            raise ValueError('Original training budget owner identity is unavailable or changed')
        return value

    def owner_alive(self) -> bool:
        import fcntl

        try:
            self.owner_record()
            descriptor = os.open(self.path('lock'), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, 'rb') as lock:
                if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode):
                    raise ValueError('Original budget owner lock must be an ordinary file')
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    initializing = os.open(self.path('initializing.lock'), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                    with os.fdopen(initializing, 'rb') as ready:
                        if not stat.S_ISREG(os.fstat(ready.fileno()).st_mode):
                            raise ValueError('Original owner publication lock must be an ordinary file')
                        try:
                            fcntl.flock(ready, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        except BlockingIOError:
                            return False
                    return True
        except (OSError, ValueError):
            return False
        return False

    def ensure_owner(self) -> None:
        self.require_active()
        if self.path('owner.json').exists():
            self.require_active(owner=True)
            return
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        training_cycles._sync_directory(self.folder.parent)
        # Only this short launcher lock is held by the caller; the owner never
        # acquires the submission lock and inherits neither lifecycle lock.
        with file_lock(self.path('launch.lock'), blocking=False):
            if self.path('owner.json').exists():
                self.require_active(owner=True)
                return
            observation = self.path('launches/' + uuid.uuid4().hex)
            observation.mkdir(parents=True, mode=0o700)
            payload = {**self.operation.payload, 'mode': 'owner', 'intent_sha256': self.identity['intent_sha256']}
            environment = dict(os.environ)
            installation = Path(self.intent['execution']['installation'])
            environment['PYTHONPATH'] = os.pathsep.join(map(str, (
                Path(__file__).parent.parent, installation / 'local', installation / 'upstream/platform',
                installation / 'upstream/temporal', installation / 'upstream')))
            with (observation / 'stdout.json').open('xb') as stdout, (observation / 'stderr.txt').open('xb') as stderr:
                child = subprocess.Popen([sys.executable, '-P', '-c',
                    'from ergora.reference_training_worker import budget_main;budget_main()'], stdin=subprocess.PIPE,
                    stdout=stdout, stderr=stderr, env=environment, start_new_session=True)
                child.stdin.write(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8'))
                child.stdin.close()
            limit = time.monotonic() + min(5, self.operation.payload['timeout'])
            while time.monotonic() < limit and child.poll() is None:
                if self.owner_alive():
                    self.require_active(owner=True)
                    return
                time.sleep(.02)
            raise ValueError('Independent training budget owner was not confirmed; inspect ' + str(observation))

    def observe(self) -> dict:
        result = {**self.binding, 'owner_status': 'not_started', 'executor_stop_confirmed': None}
        try:
            state, plan, authorization, ready = self.source()
            observed = training_cycles._status(state, plan, authorization, ready)
            result.update(authorization_status=observed['status'],
                          work_remaining_seconds=observed['work_remaining_seconds'],
                          total_remaining_seconds=observed['total_remaining_seconds'])
            if self.path('final.json').exists() and not self.owner_alive():
                training_cycles._sync_directory(self.folder)
                state, plan, authorization, ready = self.source()
                observed = training_cycles._status(state, plan, authorization, ready)
                result.update(authorization_status=observed['status'],
                              work_remaining_seconds=observed['work_remaining_seconds'],
                              total_remaining_seconds=observed['total_remaining_seconds'])
                final = training_cycles._document(self.path('final.json'), limit=_FINAL_LIMIT)
                if any(final.get(key) != value for key, value in self.identity.items()):
                    raise ValueError('Budget final observation differs from the original start intent')
                result.update(owner_status=final['status'], final=final)
                # Recover only the same already-visible fence. Never restart its
                # owner, publish a new fence or replace the historical outcome.
                result['local_fence'] = self.durable_fence()
            elif self.path('owner.json').exists():
                result['owner_status'] = 'active' if self.owner_alive() else 'unknown'
                if result['owner_status'] == 'unknown':
                    result['local_fence'] = self.durable_fence()
        except (OSError, ValueError, sqlite3.Error) as error:
            result.update(authorization_status='unknown', owner_status='unknown', reason=str(error))
        return result

    def durable_fence(self) -> dict | None:
        relative = 'training/fences/' + self.operation.ident + '.json'
        path = self.operation.adapter.safe_file(self.operation.root, relative)
        if not path.exists():
            return None
        expected = {'binding': self.intent['observation']['experiment']['spec']['binding']}
        if self.operation.document(self.operation.root, relative) != expected:
            raise ValueError('Budget fence conflicts with its original complete binding')
        for directory in (path.parent, path.parent.parent, self.operation.root):
            training_cycles._sync_directory(directory)
        raw = self.operation.adapter.read_raw(path)
        if json.loads(raw) != expected:
            raise ValueError('Original budget fence changed during durable publication')
        return {'sha256': hashlib.sha256(raw).hexdigest(), 'durable_at': now()}

    def context(self) -> dict:
        _, plan, authorization, _ = self.source()
        published = registrations.published_project(self.intent['control_home'], self.intent['project'],
            authorization['registration']['operation_id'], authorization['registration']['intent_sha256'])
        return {'intent': self.intent, 'authorization': authorization, 'policy': plan['definition']['budget'],
                'project': plan['project'], 'published_project': published}

    @staticmethod
    def remaining(context: dict, *, cleanup: bool = False) -> float:
        policy = context['policy']
        return budget_clock.remaining(context['authorization']['clock'], policy['wall_seconds'],
                                      0 if cleanup else policy['cleanup_seconds'])

    def supervise(self, mode: str, context: dict, *, final: dict | None = None) -> dict:
        phase = _BudgetPhase(self, mode, context, final=final)
        result = phase.run()
        helper = phase.frames[0]['process'] if phase.frames else None
        self.phase_observations.append({'phase_id': phase.identity['phase_id'], 'mode': mode,
            'supervisor_returncode': phase.supervisor_returncode, 'stopped': helper is not None,
            'helper_process': {key: helper[key] for key in ('status', 'returncode')} if helper is not None else None,
            'status': result.get('status', 'unknown'), 'reason': result.get('reason')})
        return result

    def supervise_phase(self, context: dict) -> None:
        identity = self.operation.payload['phase']
        phase = _BudgetPhase(self, identity['mode'], context, phase_id=identity['phase_id'],
                             owner=identity['owner'], final=self.operation.payload.get('final'))
        if phase.identity != identity:
            raise ValueError('Training supervisor differs from its complete original phase')
        phase.supervise()

    def own(self) -> dict:
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        with file_lock(self.path('lock'), blocking=False):
            if self.path('owner.json').exists():
                raise ValueError('Original training budget owner cannot be restarted')
            self.require_active()
            context = self.context()
            self.cancelled = False

            def cancel(signum, frame):
                self.cancelled = True

            signal.signal(signal.SIGTERM, cancel)
            signal.signal(signal.SIGINT, cancel)
            with file_lock(self.path('initializing.lock'), blocking=False):
                training_cycles._sync_directory(self.folder.parent)
                training_cycles._record(self.path('owner.json'), {**self.identity, **_process_identity(os.getpid()),
                    'context_sha256': self.operation.sha(context)})
            self.phase_observations = []
            observed = self.supervise('monitor', context)
            if observed.get('status') == 'completed':
                outcome = observed
            else:
                outcome = self.supervise('fence', context)
                if outcome.get('status') == 'fenced':
                    outcome = {**outcome, 'control': self.supervise('cleanup', context)}
            try:
                remaining = self.remaining(context, cleanup=True)
            except (OSError, ValueError):
                remaining = None
            final = {**self.identity, **outcome, 'recorded_at': now(),
                     'total_remaining_seconds': remaining,
                     'overrun_seconds': max(0, -remaining) if remaining is not None else None,
                     'phases': list(self.phase_observations),
                     'executor_stop_confirmed': None}
            publication = self.supervise('publish', context, final=final)
            return {**final, 'publication': publication}

    def validate_cached(self, context: dict) -> None:
        if (self.operation.sha(context['intent']) != self.identity['intent_sha256']
                or self.operation.sha(context) != self.owner_record()['context_sha256']
                or not self.owner_alive()):
            raise ValueError('Supervised training cleanup has no matching original live owner')
        budget_clock.validate(context['authorization']['clock'], context['policy']['wall_seconds'])

    def experiment(self):
        from perf_temporal.models import Binding, Experiment

        spec = self.intent['observation']['experiment']['spec']
        return Experiment(**{**spec, 'binding': Binding(**spec['binding'])})

    async def completion(self) -> dict | None:
        from agent_platform.training import create_adapter

        experiment = self.experiment()
        request = self.operation.native_request()
        if request is None:
            return None
        if (self.operation.sha(request['experiment']) != self.operation.sha(asdict(experiment))
                or self.operation.sha(request['runner']) != self.operation.sha(self.intent['observation']['experiment']['current_runner'])):
            raise ValueError('Budget native request differs from its complete original experiment or runner')
        adapter = create_adapter()
        job = await adapter.lookup_job(experiment)
        observation = await adapter.poll_job(job)
        if observation.state not in ('SUCCEEDED', 'FAILED', 'CANCELLED'):
            return None
        gate = asdict(await adapter.collect_and_gate(job)) if observation.state == 'SUCCEEDED' else None
        return {'status': 'completed', 'native': asdict(observation), 'gate': gate}

    async def helper(self, mode: str, context: dict) -> dict:
        from agent_platform.training import create_adapter

        self.validate_cached(context)
        if mode == 'publish':
            final = self.operation.payload['final']
            if any(final.get(key) != value for key, value in self.identity.items()):
                raise ValueError('Final budget publication differs from its original start intent')
            training_cycles._record(self.path('final.json'), final, limit=_FINAL_LIMIT)
            return {'status': 'published'}
        if mode == 'monitor':
            while True:
                if not self.owner_alive():
                    return {'status': 'unknown', 'reason': 'Original budget owner disappeared'}
                completed = await self.completion()
                if completed is not None:
                    return completed
                self.require_active()
                if self.operation.adapter.safe_file(self.operation.root, 'training/fences/' + self.operation.ident + '.json').exists():
                    return {'status': 'stop', 'reason': 'Original native fence observed'}
                await asyncio.sleep(.1)
        if mode == 'fence':
            completed = await self.completion()
            if completed is not None:
                return completed
            relative = 'training/fences/' + self.operation.ident + '.json'
            path = self.operation.adapter.safe_file(self.operation.root, relative)
            for name in ('training/registry.lock', 'training/jobs/' + self.operation.ident + '/request.json', relative):
                self.operation.adapter.safe_file(self.operation.root, name)
            if path.exists() and self.operation.document(self.operation.root, relative) != {'binding': asdict(self.experiment().binding)}:
                raise ValueError('Budget fence conflicts with its original complete binding')
            job = await create_adapter().fence_and_lookup(self.experiment())
            durable = self.durable_fence()
            if self.remaining(context, cleanup=True) <= 0:
                return {'status': 'unknown', 'reason': 'Original cleanup deadline passed during fence publication'}
            return {'status': 'fenced', 'fence': durable,
                    'existing_job': asdict(job) if job is not None else None}
        raise ValueError('Unsupported training budget helper phase')
