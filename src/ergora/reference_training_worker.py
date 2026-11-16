"""Optional application SDK worker for the versioned, budget-aware training queue."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from contextvars import ContextVar
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import math
import os
from pathlib import Path, PurePath
import re
import signal
import stat
import subprocess
import sys
import time
import threading
import uuid

try:
    from temporalio import workflow
except ModuleNotFoundError as error:
    if error.name != 'temporalio':
        raise
    workflow = None

with workflow.unsafe.imports_passed_through() if workflow is not None else nullcontext():
    from . import budget_clock, processes, reference, training_cycles, training_execution_protocol as protocol
    from .reference_training_budget import BudgetedStart, TASK_QUEUE, check_cycle_predecessors, validate_binding
    from .reference_training_submission import _Submission
    from .reference_training_execution import Execution
    from .state import State, file_lock, now
    from .training_cycles import _CycleCapacityError
    if workflow is not None:
        from temporalio.common import RetryPolicy
        from temporalio.converter import DefaultFailureConverter, FailureConverter
        from temporalio.exceptions import ActivityError, ApplicationError


_CREATING = ContextVar('ergora_training_budget_create', default=None)
_CYCLE_LIMIT = 32_768
_REQUEST_RETENTION_PROTOCOL = 'ergora-training-cycle-request-retention-v1'
_ROOT_OBSERVERS = set()


if workflow is not None:
    class _CycleFailureConverter(FailureConverter):
        """Bound the complete SDK failure after the default converter builds its tree."""

        def __init__(self):
            self._default = DefaultFailureConverter()

        def to_failure(self, exception, payload_converter, failure):
            # Delegate the entire tree. Default recursion must never reenter this
            # boundary and hide aggregate overflow by replacing individual causes.
            self._default.to_failure(exception, payload_converter, failure)
            if failure.ByteSize() > _CYCLE_LIMIT:
                failure.Clear()
                failure.message = 'Complete cycle SDK failure exceeds 32 KiB'
                failure.application_failure_info.type = 'cycle_failure_capacity_exceeded'
                failure.application_failure_info.non_retryable = True
                if failure.ByteSize() > _CYCLE_LIMIT:
                    raise _CycleCapacityError('Complete cycle SDK capacity failure cannot be encoded')

        def from_failure(self, failure, payload_converter):
            return self._default.from_failure(failure, payload_converter)


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
        version2 = (snapshot is not None and snapshot['authorization']['schema_version'] == 3 or
            activity_context is not None and activity_context['workflow_input']['protocol'] == 'ergora-training-cycle-v2')
        self.identity = {'protocol': ('ergora-training-cycle-operation-v2' if version2
            else 'ergora-training-cycle-operation-v1'), 'operation_id': uuid.uuid4().hex,
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
        self.capacity_rejected = len(self.encoded) > _CYCLE_LIMIT
        if self.capacity_rejected and (not version2 or snapshot is None or bootstrap is None):
            logging.error('Complete unsent cycle operation request: %s', self.payload)
            raise _CycleCapacityError('Complete cycle operation request exceeds 32 KiB; nothing was truncated')
        self.output = home / 'operations/training-cycles' / self.identity['operation_id']
        self.response = protocol.PhaseFrames(self.identity, self.output, _CYCLE_LIMIT)
        self.stopping, self.signalled, self.sent = False, False, False
        self.process, self.spawning, self.problem = None, None, None
        self.diagnostics = bytearray()
        self.result_ref = None
        self.request_retention = {'status': 'unknown', 'waited': False, 'returncode': None}
        self.retention_response = bytearray()
        self.request_sha256 = None

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
            if self.capacity_rejected:
                envelope = _request_retention_envelope(self.payload, len(self.encoded))
                control = json.dumps(envelope, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
                if len(control) > _CYCLE_LIMIT:
                    raise ValueError('Complete request retention envelope exceeds 32 KiB')
                stream.write(control + b'\n')
                await stream.drain()
                digest = hashlib.sha256()
                raw = memoryview(self.encoded)
                for offset in range(0, len(raw), 65_536):
                    if self.stopping or self.expired():
                        raise ValueError('Original request retention allowance ended during send')
                    chunk = raw[offset:offset + 65_536]
                    digest.update(chunk)
                    stream.write(chunk)
                    await stream.drain()
                    await asyncio.sleep(0)
                self.request_sha256 = digest.hexdigest()
            else:
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
            elif self.capacity_rejected:
                # Keep draining after rejection without retaining unbounded output.
                self.retention_response.extend(raw[:max(0, _CYCLE_LIMIT + 2 - len(self.retention_response))])
            else:
                self.response.receive(raw)

    def observation(self, result: dict) -> dict:
        if self.capacity_rejected:
            result = {'status': 'capacity_exceeded',
                'reason': 'Complete cycle operation request exceeds 32 KiB; nothing was truncated',
                'request_retention': dict(self.request_retention)}
        return {**result, 'operation_id': self.identity['operation_id'], 'mode': self.identity['mode'],
            'ordinal': self.identity['ordinal'], 'output': str(self.output),
            'operation_stopped': bool(self.response.frames),
            'supervisor_returncode': self.process.returncode if self.process is not None and not self.capacity_rejected else None}

    async def _run(self) -> dict:
        if self.stopping or self.expired():
            return self.observation({'status': 'unknown', 'reason': 'Original cycle operation allowance is exhausted'})
        self.spawning = asyncio.create_task(asyncio.create_subprocess_exec(sys.executable, '-P', '-c',
            ('from ergora.reference_training_worker import cycle_request_retention_main;cycle_request_retention_main()'
             if self.capacity_rejected else
             'from ergora.training_execution_protocol import cycle_supervisor_main;cycle_supervisor_main()'),
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
                    self.process.kill() if self.capacity_rejected else self.process.terminate()
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
        if self.capacity_rejected:
            self.request_retention.update(waited=not isinstance(outcomes[3], BaseException),
                                          returncode=self.process.returncode)
            if (not self.stopping and self.process.returncode == 0 and self.sent
                    and not any(isinstance(item, BaseException) for item in outcomes) and not self.expired()):
                try:
                    raw = self.retention_response
                    if not raw.endswith(b'\n') or len(raw) - 1 > _CYCLE_LIMIT or raw.count(b'\n') != 1:
                        raise ValueError('Request retention requires exactly one bounded confirmation and EOF')
                    confirmation = protocol.decode(bytes(raw[:-1]))
                    protocol._exact(confirmation, ('protocol', 'identity', 'ref'), 'Request retention confirmation')
                    protocol._process(confirmation['identity']['parent'])
                    ref = confirmation['ref']
                    protocol._exact(ref, ('file', 'bytes', 'sha256'), 'Original request reference')
                    if (confirmation['protocol'] != _REQUEST_RETENTION_PROTOCOL or confirmation['identity'] != self.identity
                            or type(confirmation['identity']['ordinal']) is not type(self.identity['ordinal'])
                            or ref['file'] != 'request.json' or type(ref['bytes']) is not int
                            or ref['bytes'] != len(self.encoded) or ref['sha256'] != self.request_sha256):
                        raise ValueError('Request retention confirmation differs from the complete original request')
                    self.request_retention.update(status='durable_confirmed', ref=ref)
                except (ValueError, TypeError, KeyError) as error:
                    self.problem = str(error)
            return self.observation({})
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
        if self.capacity_rejected:
            running.add_done_callback(lambda _: logging.error(
                'Cycle request capacity failure: operation_id=%s mode=%s ordinal=%s output=%s request_retention=%s',
                self.identity['operation_id'], self.identity['mode'], self.identity['ordinal'], self.output,
                self.request_retention))
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


def _request_retention_envelope(payload: dict, size: int) -> dict:
    # These are original supervision inputs, never a replacement authorization.
    policy = payload['snapshot']['policy']
    clock = payload['snapshot']['authorization']['clock']
    window = payload['bootstrap']
    return {'protocol': _REQUEST_RETENTION_PROTOCOL, 'identity': payload['identity'], 'bytes': size,
        'bootstrap': window, 'budget': {'clock': {key: clock[key] for key in budget_clock.FIELDS},
            'policy': {key: policy[key] for key in ('wall_seconds', 'cleanup_seconds')}},
        'deadline_ns': min(window['deadline_ns'], clock['boottime_ns']
            + (policy['wall_seconds'] - policy['cleanup_seconds']) * 1_000_000_000)}


def _request_retention_remaining(envelope: dict) -> float:
    window, budget = envelope['bootstrap'], envelope['budget']
    boot, ticks = budget_clock._clock()
    if boot != window['boot_id'] or ticks < window['started_ns']:
        raise ValueError('Request retention lost its original boot clock')
    return min((min(window['deadline_ns'], envelope['deadline_ns']) - ticks) / 1_000_000_000,
        budget_clock.remaining(budget['clock'], budget['policy']['wall_seconds'], budget['policy']['cleanup_seconds']))


def cycle_request_retention_main() -> None:
    """Save only one rejected original request; no H, business dispatch or descendants."""
    source = sys.stdin.buffer
    raw = source.readline(_CYCLE_LIMIT + 2)
    if not raw.endswith(b'\n') or len(raw) - 1 > _CYCLE_LIMIT:
        raise ValueError('Request retention requires one bounded control envelope')
    envelope = protocol.decode(raw[:-1])
    protocol._exact(envelope, ('protocol', 'identity', 'bytes', 'bootstrap', 'budget', 'deadline_ns'),
                    'Request retention envelope')
    identity, window, budget = envelope['identity'], envelope['bootstrap'], envelope['budget']
    protocol._exact(identity, ('protocol', 'operation_id', 'mode', 'control_home', 'project', 'cycle_id',
        'input_sha256', 'authorization_sha256', 'ordinal', 'parent'), 'Request retention identity')
    if (envelope['protocol'] != _REQUEST_RETENTION_PROTOCOL
            or identity['protocol'] != 'ergora-training-cycle-operation-v2'
            or identity['mode'] not in (*protocol.CYCLE_WORK_MODES, 'reconcile-candidate', 'reconcile-controller')
            or not isinstance(identity['operation_id'], str) or re.fullmatch('[a-f0-9]{32}', identity['operation_id']) is None
            or (identity['mode'] in (*protocol.CYCLE_CANDIDATE_MODES, *protocol.CYCLE_MEASUREMENT_MODES)
                and (type(identity['ordinal']) is not int or not 0 <= identity['ordinal'] < 32))
            or (identity['mode'] in ('prepare-controller', 'submit-controller', 'reconcile-controller')
                and identity['ordinal'] is not None)
            or type(envelope['bytes']) is not int or envelope['bytes'] <= _CYCLE_LIMIT):
        raise ValueError('Request retention requires an oversized original operation-v2 request')
    for name, maximum in (('project', 63), ('cycle_id', 79)):
        if not isinstance(identity[name], str) or re.fullmatch(
                '[A-Za-z0-9][A-Za-z0-9_-]{0,' + str(maximum) + '}', identity[name]) is None:
            raise ValueError('Request retention requires portable original IDs')
    home = identity['control_home']
    if not isinstance(home, str) or not Path(home).is_absolute() or '..' in Path(home).parts:
        raise ValueError('Request retention requires its original absolute control directory')
    for name in ('input_sha256', 'authorization_sha256'):
        protocol._digest(identity[name])
    protocol._process(identity['parent'])
    protocol._exact(window, ('boot_id', 'started_ns', 'deadline_ns'), 'Original request retention window')
    protocol._exact(budget, ('clock', 'policy'), 'Original request retention budget')
    clock, policy = budget['clock'], budget['policy']
    protocol._exact(clock, budget_clock.FIELDS, 'Original request retention clock')
    protocol._exact(policy, ('wall_seconds', 'cleanup_seconds'), 'Original request retention policy')
    if (type(policy['wall_seconds']) is not int or type(policy['cleanup_seconds']) is not int
            or not 1 <= policy['cleanup_seconds'] < policy['wall_seconds']):
        raise ValueError('Invalid original request retention policy')
    budget_clock.validate(clock, policy['wall_seconds'])
    if (window['boot_id'] != identity['parent']['boot_id'] or window['boot_id'] != clock['boot_id']
            or type(window['started_ns']) is not int or window['started_ns'] < clock['boottime_ns']
            or type(window['deadline_ns']) is not int or window['deadline_ns'] <= window['started_ns']
            or type(envelope['deadline_ns']) is not int
            or envelope['deadline_ns'] > min(window['deadline_ns'], clock['boottime_ns']
                + (policy['wall_seconds'] - policy['cleanup_seconds']) * 1_000_000_000)):
        raise ValueError('Request retention cannot enlarge the original work allowance')
    cancelled = threading.Event()
    finished = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: cancelled.set())
    signal.signal(signal.SIGINT, lambda *_: cancelled.set())

    def active():
        expected = identity['parent']
        if (cancelled.is_set() or _request_retention_remaining(envelope) <= 0
                or os.getppid() != expected['pid'] or processes.identity(expected['pid']) != expected):
            raise ValueError('Original request retention supervision ended')

    def watch():
        while not finished.wait(.05):
            try:
                active()
            except (OSError, ValueError):
                os.kill(os.getpid(), signal.SIGKILL)

    active()
    watchdog = threading.Thread(target=watch, name='ergora-request-retention-watchdog', daemon=True)
    watchdog.start()
    home = Path(home)
    output = home / 'operations/training-cycles' / identity['operation_id']
    try:
        active()
        for parent in (output, *output.parents):
            try:
                details = parent.lstat()
            except FileNotFoundError:
                continue
            if (not stat.S_ISDIR(details.st_mode) or getattr(details, 'st_file_attributes', 0) & 0x400):
                raise ValueError('Request retention requires original ordinary directories')
        output.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        active()
        output.mkdir(mode=0o700)
        active()
        path = output / 'request.json'
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        try:
            original = os.fstat(descriptor)
            if not stat.S_ISREG(original.st_mode):
                raise ValueError('Request retention requires an ordinary exclusive file')
            digest = hashlib.sha256()
            remaining = envelope['bytes']
            while remaining:
                active()
                chunk = source.read(min(65_536, remaining))
                active()
                if not chunk:
                    raise ValueError('Original request ended before its complete byte count')
                pending = memoryview(chunk)
                while pending:
                    active()
                    written = os.write(descriptor, pending)
                    if written <= 0:
                        raise OSError('Original request write made no progress')
                    pending = pending[written:]
                digest.update(chunk)
                remaining -= len(chunk)
            active()
            if source.read(1):
                raise ValueError('Original request contains data after its complete byte count')
            active()
            os.fsync(descriptor)
            active()
            protocol.sync_directories(output, home)
            active()
            with os.fdopen(protocol._fd(path), 'rb') as saved:
                details = os.fstat(saved.fileno())
                if ((details.st_dev, details.st_ino) != (original.st_dev, original.st_ino)
                        or details.st_size != envelope['bytes']):
                    raise ValueError('Original request file identity or byte count changed')
                reread = hashlib.sha256()
                count = 0
                while True:
                    active()
                    chunk = saved.read(65_536)
                    active()
                    if not chunk:
                        break
                    count += len(chunk)
                    reread.update(chunk)
                current = path.lstat()
                if ((current.st_dev, current.st_ino) != (original.st_dev, original.st_ino)
                        or count != envelope['bytes'] or reread.digest() != digest.digest()):
                    raise ValueError('Original request changed during synchronized raw verification')
            active()
            confirmation = json.dumps({'protocol': _REQUEST_RETENTION_PROTOCOL, 'identity': identity,
                'ref': {'file': 'request.json', 'bytes': count, 'sha256': digest.hexdigest()}},
                ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
            if len(confirmation) > _CYCLE_LIMIT:
                raise ValueError('Complete request retention confirmation exceeds 32 KiB')
            active()
            if sys.stdout.buffer.write(confirmation + b'\n') != len(confirmation) + 1:
                raise OSError('Request retention confirmation was only partially written')
            sys.stdout.buffer.flush()
            active()
        finally:
            os.close(descriptor)
    except (OSError, ValueError):
        # Neither raw nor paths/errors are printed: only the original small identity.
        logging.error('Request retention unknown: operation_id=%s mode=%s', identity['operation_id'], identity['mode'])
        raise SystemExit(1)
    finally:
        finished.set()
        watchdog.join()


class _CycleCandidate:
    """Own one in-memory offer until the complete original owner is confirmed."""

    def __init__(self, home: Path, project: str, cycle_id: str, authorization_sha256: str,
                 *, snapshot: dict, controller: dict, activity_context: dict | None = None,
                 window: dict | None = None):
        self.preparation = _CycleOperation(home, project, cycle_id, authorization_sha256, 'prepare-candidate',
            snapshot=snapshot, ordinal=controller['ordinal'], start_context={'controller': controller},
            activity_context=activity_context, window=window)
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
    if identity['protocol'] != ('ergora-training-cycle-operation-v2' if authorization['schema_version'] == 3
                                else 'ergora-training-cycle-operation-v1'):
        raise ValueError('Cycle operation protocol differs from its complete original authorization')
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
        from .reference_training_runtime import observe_submission

        binding = Binding(**intent['observation']['experiment']['spec']['binding'])

        def remaining():
            active()
            return protocol.cycle_operation_remaining(payload)

        async def runtime():
            async with asyncio.timeout(remaining()):
                client = await connect()
                if client.namespace != payload['activity_context']['service_namespace']:
                    raise ValueError('Candidate runtime namespace differs from its authenticated SDK activity service')
                observed = await observe_submission(client, intent, run_id=submitted['run_id'], timeout=remaining())
                if observed is None:
                    facts['runtime'].update(state='not_found', workflow_id=submitted['workflow_id'],
                                            run_id=submitted['run_id'])
                    return
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
    if authorization['schema_version'] == 3 and identity['mode'] not in protocol.CYCLE_MEASUREMENT_MODES:
        facts.update(selection=protocol.round_selection(plan, authorization), measurement={
            'measurement_state': 'pending', 'index_state': 'absent', 'continuation_ready': False,
            'prefix': None, 'acceptance': None})
    return result


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


def _round_previous(payload, plan, admission, active):
    """H checks a real selected binding before or after child-intent birth."""
    from perf_temporal.connection import connect

    authorization = admission.authorization
    ready = protocol.decode(protocol.read_raw(admission.directory / 'ready.json'))
    binding = {'cycle_id': authorization['cycle_id'], 'authorization_sha256': authorization['sha256'],
               'task_queue': TASK_QUEUE, 'controller': payload['start_context']['controller']}

    def remaining():
        active()
        return protocol.cycle_operation_remaining(payload)

    async def check():
        async with asyncio.timeout(remaining()):
            client = await connect()
            context = payload.get('activity_context')
            if context is not None and client.namespace != context['service_namespace']:
                raise ValueError('Candidate runtime namespace differs from its authenticated SDK activity service')
            return await check_cycle_predecessors(plan, admission, ready, binding, client, remaining)

    previous = asyncio.run(check())
    active()
    return previous


def _round_operation(payload, plan, admission, ready, active):
    from . import training_rounds

    identity = payload['identity']
    ordinal = identity['ordinal']
    state = State(Path(identity['control_home']))
    operation, intent, _ = _round_gate(payload, plan, admission, ready, active, history=True)
    selection = protocol.round_selection(plan, admission.authorization)
    previous = _round_previous(payload, plan, admission, active)
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
    protocol.round_report_binding(saved, plan, ordinal, previous)
    raw = protocol.read_raw(destination / 'rounds.json', protocol.ARTIFACT_LIMIT)
    if hashlib.sha256(raw).hexdigest() != saved['sha256']:
        raise ValueError('Round index changed between its original read and synchronization')
    # A complete preflight cannot bless the index's independently captured native values.
    measurement_state = protocol.round_state(preflight, evidence, saved['report']['rounds'][-1], intent)
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
        protocol.round_report_binding(reread, plan, ordinal, _round_previous(payload, plan, admission, active))
        _round_gate(payload, plan, admission, ready, active)
        index_state = 'durable'
    except (OSError, ValueError) as error:
        return {'status': 'unknown', 'reason': str(error), 'facts': {**preflight['facts'], 'selection': selection,
            'measurement': {'measurement_state': measurement_state, 'index_state': index_state,
                'continuation_ready': False, 'prefix': None, 'acceptance': None}}}
    final = _execution_candidate_operation(payload, plan, admission, active)
    evidence = _round_read_evidence(payload, state, identity['project'], operation.ident, active)
    measurement_state = protocol.round_state(final, evidence, saved['report']['rounds'][-1], intent)
    prefix = protocol.round_pin(saved, raw)
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
    protocol.round_report_binding(saved, plan, ordinal, _round_previous(payload, plan, admission, active))
    _round_gate(payload, plan, admission, ready, active)
    # Recheck the exact durable index after the final observation and gate.
    if training_rounds.read(destination, sha256=saved['sha256']) != saved:
        raise ValueError('Round prefix changed before its final acceptance')
    _round_local_gate(payload, plan, admission, ready, active)
    # All blocking H readers have returned; bind the complete local chain last.
    originals = protocol.authenticate_cycle_candidate(intent, plan, admission, ready)
    protocol.round_report_binding(saved, plan, ordinal, originals[0][0] if originals else None)
    acceptance = protocol.round_acceptance(value, ref, intent) if measurement_state == 'accepted' else None
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
        if identity['ordinal'] != 0 and admission.authorization['schema_version'] != 3:
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
    if (admission.authorization['schema_version'] == 3 and mode in protocol.CYCLE_START_MODES
            and (mode != 'prepare-candidate' or intent is None)):
        _round_previous(payload, plan, admission, active)
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
        if admission.authorization['schema_version'] == 3:
            _round_previous(payload, plan, admission, active)
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
    from temporalio.api.common.v1 import Memo
    from temporalio.converter import WorkflowSerializationContext
    from temporalio.exceptions import ApplicationError, WorkflowAlreadyStartedError
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
        if (activity_context['activity_source']['activity_type'] in (
                protocol.CYCLE_ACTIVITY_NAMES['stop'], protocol.CYCLE_ACTIVITY_NAMES_V3['stop'])
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

            memo_values = {protocol.CYCLE_MEMO_KEY: protocol.CycleAdmission._sha(intent)}
            converter = client.data_converter.with_context(WorkflowSerializationContext(
                namespace=client.namespace, workflow_id=intent['workflow_id']))

            async def capacity():
                await _cycle_capacity(intent['workflow_input'], converter)
                memo = Memo(fields={key: (await converter.encode([value]))[0]
                                    for key, value in memo_values.items()})
                if memo.ByteSize() > 2048:
                    raise _CycleCapacityError('Complete controller Memo exceeds 2 KiB')

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
                await capacity()
                remaining()
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
                await capacity()
                training_cycles._controller_ready(state, admission)
                timeout = remaining()
                try:
                    handle = await client.start_workflow(protocol.cycle_workflow_type(intent['protocol']), intent['workflow_input'],
                        id=intent['workflow_id'], task_queue=intent['task_queue'],
                        id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                        id_conflict_policy=WorkflowIDConflictPolicy.FAIL, retry_policy=RetryPolicy(maximum_attempts=1),
                        memo=memo_values,
                        rpc_timeout=timedelta(seconds=timeout))
                except WorkflowAlreadyStartedError as error:
                    current = training_cycles._record_controller(state, admission, run_id=error.run_id or None, reason='start_conflict')
                    return observation(current, runtime_status='queried')
                current = training_cycles._record_controller(state, admission, run_id=handle.result_run_id)
                active()
                return observation(current, runtime_status='start_acknowledged')
    except (RPCError, TimeoutError, ValueError, ApplicationError) as error:
        exceeded = (isinstance(error, _CycleCapacityError)
            or isinstance(error, ApplicationError) and error.type == 'cycle_activity_capacity_exceeded')
        return observation(admission.submission(), status='capacity_exceeded' if exceeded else 'unknown',
                           runtime_status='unconfirmed', reason=str(error))


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
    """Keep the original entry while the production S uses its pure owner."""
    if supervisor:
        return protocol.cycle_supervisor_main()
    raw = sys.stdin.buffer.read(_CYCLE_LIMIT + 1)
    if len(raw) > _CYCLE_LIMIT:
        raise ValueError('Complete cycle operation request exceeds 32 KiB')
    payload = protocol.decode(raw)
    protocol.validate_cycle_operation(payload)
    identity = payload['identity']
    expected = identity['parent']
    if processes.identity(expected['pid']) != expected:
        raise ValueError('Cycle operation lost its original complete parent identity')
    sys.path[:0] = [str(reference.ROOT / part) for part in
                   ('platform/local', 'platform/upstream/platform', 'platform/upstream/temporal', 'platform/upstream')]
    try:
        result = _cycle_operation(payload)
    except (OSError, ValueError, KeyError, TypeError, _RoundRetentionError) as error:
        result = {'status': 'capacity_exceeded' if isinstance(error, _CycleCapacityError) else 'unknown',
                  'reason': str(error)}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
    return


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
            return self._consume_facts(facts, value, scheduled, 0)

        def _consume_facts(self, facts, value, scheduled, ordinal):
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
            if (type(candidate['ordinal']) is not int or candidate['ordinal'] != ordinal
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


    @workflow.defn(name='TrainingCycleWorkflowV2')
    class TrainingCycleWorkflowV2(TrainingCycleWorkflow):
        """Consume the born selection; history owns each round's three opportunities."""

        @workflow.init
        def __init__(self, original: dict):
            super().__init__(original)
            self._ordinal, self._confirmed = 0, 0
            self._selection = self._prefix = self._predecessor = None
            self._project_revision = self._registration_sha256 = None
            self._advanced = False
            self._state.update(collect_scheduled=False, total_observation_count=0)

        @workflow.query
        def status(self) -> dict:
            info = workflow.info()
            value = {'schema_version': 2, 'protocol': 'ergora-training-cycle-workflow-v2',
                'workflow_id': info.workflow_id, 'run_id': info.run_id,
                'input_sha256': self._input.get('input_sha256'),
                'authorization_sha256': self._input.get('authorization_sha256'),
                'ordinal': self._ordinal, 'selection_count': self._selection['count'] if self._selection else None,
                'confirmed_rounds': self._confirmed, 'prefix': self._prefix, **self._state,
                'stop_durable': None, 'admission_drained': None, 'executor_stop_confirmed': None}
            self._capacity(value)
            return value

        @workflow.signal
        def request_stop(self, request):
            super().request_stop(request)

        async def _ordinary(self, action, *, cold=False):
            if not self._guard():
                return None, None
            scheduled = workflow.now()
            seconds = 10 if cold else min((self._work - scheduled).total_seconds(), self._control, 10)
            if seconds <= 0:
                self._stop_reason = 'work_budget_exhausted'
                return None, None
            request = {'workflow_input': self._input, 'ordinal': self._ordinal, 'predecessor': self._predecessor}
            self._capacity(request)
            self._state['observation_count'] += 1
            self._state['total_observation_count'] += 1
            ident = 'candidate-' + str(self._ordinal) + '-' + (
                'collect' if action == 'collect-round' else str(self._state['observation_count']))
            self._state['last_normal_activity_id'] = ident
            if action == 'start':
                self._state.update(start_scheduled=True, phase='STARTING')
            elif action == 'reconcile':
                self._reconciled = True
                self._state['phase'] = 'RECONCILING'
            elif action == 'request-execution-or-observe':
                self._state.update(request_scheduled=True, phase='REQUESTING')
            elif action == 'collect-round':
                self._state.update(collect_scheduled=True, phase='COLLECTING_ROUND')
            elif action == 'reconcile-round':
                self._state['phase'] = 'RECONCILING_ROUND'
            self._normal = workflow.start_activity(protocol.CYCLE_ACTIVITY_NAMES_V3[action], request,
                activity_id=ident, task_queue=protocol.CYCLE_TASK_QUEUE_V2,
                schedule_to_close_timeout=timedelta(seconds=seconds),
                start_to_close_timeout=timedelta(seconds=seconds), retry_policy=RetryPolicy(maximum_attempts=1),
                cancellation_type=workflow.ActivityCancellationType.TRY_CANCEL)
            self._normal.add_done_callback(lambda done: None if done.cancelled() else done.exception())
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

        def _consume(self, value, action, scheduled):
            self._capacity(value)
            protocol._exact(value, ('schema_version', 'protocol', 'action', 'status', 'workflow_input',
                'controller', 'observation', 'inspection', 'operations', 'runtime_status', 'facts'), 'V3 cycle envelope')
            if (type(value['schema_version']) is not int or value['schema_version'] != 3
                    or value['protocol'] != 'ergora-training-cycle-activity-v3' or value['action'] != action
                    or value['status'] not in ('observed', 'unknown') or value['workflow_input'] != self._input):
                raise ValueError('V3 activity lost its complete original wire or input')
            controller = value['controller']
            protocol._exact(controller, ('workflow_id', 'run_id', 'intent_sha256'), 'Cycle controller projection')
            info = workflow.info()
            protocol._digest(controller['intent_sha256'])
            if (controller['workflow_id'] != info.workflow_id or controller['run_id'] != info.run_id
                    or self._controller is not None and controller != self._controller):
                raise ValueError('V3 activity lost its original controller run')
            self._controller = controller
            observation = value['observation']
            protocol._exact(observation, ('total_remaining_seconds', 'boot_id', 'boottime_ns', 'observed_at'),
                            'Cycle budget observation')
            self._narrow_total(observation, scheduled)
            if value['facts'] is None:
                if value['status'] != 'unknown' and action != 'stop':
                    raise ValueError('An observed ordinary activity requires complete facts')
                return None
            if action == 'stop':
                raise ValueError('Stop observations cannot assert candidate acceptance')
            facts = value['facts']
            base = ('source_operation_id', 'budget', 'candidate', 'submission', 'execution', 'runtime', 'native', 'request_outcome')
            protocol._exact(facts, (*base, 'selection', 'measurement'), 'V3 candidate facts')
            if not isinstance(value['operations'], list):
                raise ValueError('V3 activity requires its complete operation records')
            source_record = None
            for record in [value['inspection'], *value['operations']]:
                protocol._exact(record, ('operation_id', 'mode', 'ordinal', 'operation_stopped',
                    'supervisor_returncode', 'result'), 'Cycle operation projection')
                if (not isinstance(record['operation_id'], str) or re.fullmatch('[a-f0-9]{32}', record['operation_id']) is None
                        or type(record['operation_stopped']) is not bool
                        or record['supervisor_returncode'] is not None and type(record['supervisor_returncode']) is not int):
                    raise ValueError('Cycle operation projection lost its original identity or stop observation')
                result = record['result']
                if not isinstance(result, dict) or set(result) not in ({'ref'}, {'inline'}):
                    raise ValueError('Cycle operation result must retain its complete original reference or inline value')
                if 'inline' in result and not isinstance(result['inline'], dict):
                    raise ValueError('Inline operation result requires its complete object')
                if 'ref' in result:
                    ref = result['ref']
                    protocol._exact(ref, ('file', 'bytes', 'sha256'), 'Cycle stdout reference')
                    if ref['file'] != 'helper/stdout.txt' or type(ref['bytes']) is not int or not 0 < ref['bytes'] <= _CYCLE_LIMIT:
                        raise ValueError('Cycle stdout reference differs from its original bounded result')
                    protocol._digest(ref['sha256'])
                if record['operation_id'] == facts['source_operation_id']:
                    source_record = record
            modes = {'start': ('observe-candidate',), 'reconcile': ('observe-candidate',),
                'request-execution-or-observe': ('request-execution-candidate', 'observe-candidate'),
                'observe-candidate': ('observe-candidate',), 'collect-round': ('collect-round', 'reconcile-round'),
                'reconcile-round': ('reconcile-round',)}[action]
            if (source_record is None or source_record['mode'] not in modes
                    or type(source_record['ordinal']) is not int or source_record['ordinal'] != self._ordinal
                    or source_record['operation_stopped'] is not True or source_record['supervisor_returncode'] != 0):
                raise ValueError('V3 facts have no matching completed original round operation')
            selection = facts['selection']
            protocol._exact(selection, ('count', 'common_sha256', 'measurement_sources_sha256'), 'Cycle selection')
            if type(selection['count']) is not int or not self._ordinal < selection['count'] <= 32:
                raise ValueError('Cycle selection lost its original complete count')
            for key in ('common_sha256', 'measurement_sources_sha256'):
                protocol._digest(selection[key])
            if self._selection is not None and self._selection != selection:
                raise ValueError('Cycle selection changed across observations or rounds')
            if self._project_revision is not None and facts['candidate']['project_revision'] != self._project_revision:
                raise ValueError('Cycle candidate changed the original project revision')
            measurement = facts['measurement']
            protocol._exact(measurement, ('measurement_state', 'index_state', 'continuation_ready', 'prefix', 'acceptance'),
                            'Cycle measurement')
            if (measurement['measurement_state'] not in ('pending', 'accepted', 'rejected', 'unknown')
                    or measurement['index_state'] not in ('absent', 'published_unconfirmed', 'durable', 'unknown')
                    or type(measurement['continuation_ready']) is not bool
                    or facts['request_outcome'] not in ('not_attempted', 'requested', 'unconfirmed', 'existing_only')):
                raise ValueError('Cycle measurement or request outcome is not typed')
            if measurement['prefix'] is not None:
                protocol.validate_round_prefix(measurement['prefix'])
            if measurement['acceptance'] is not None:
                protocol.validate_round_acceptance(measurement['acceptance'])
            self._consume_facts({key: facts[key] for key in base}, value, scheduled, self._ordinal)
            self._selection = selection
            self._project_revision = facts['candidate']['project_revision']
            ready = measurement['continuation_ready']
            if ready:
                prefix, acceptance = measurement['prefix'], measurement['acceptance']
                protocol.validate_round_predecessor({'prefix': prefix, 'acceptance': acceptance}, self._ordinal + 1)
                root = PurePath(self._input['control_home'])
                expected_directory = str(root / 'training-cycles' / self._input['project'] / self._input['cycle_id'] / 'controller/rounds' / str(self._ordinal))
                expected_observation = str(root / 'operations/training-cycles' / facts['source_operation_id'] / 'helper/observation.json')
                candidate, submitted, execution, runtime, native = (facts[key] for key in
                    ('candidate', 'submission', 'execution', 'runtime', 'native'))
                accepted_runtime = acceptance['runtime']
                terminal = runtime['terminal'] is True
                if (action not in protocol.CYCLE_MEASUREMENT_MODES or value['status'] != 'observed'
                        or measurement['measurement_state'] != 'accepted' or measurement['index_state'] != 'durable'
                        or not self._state['collect_scheduled'] or prefix['directory'] != expected_directory
                        or self._prefix is not None and prefix['initial_anchor_sha256'] != self._prefix['initial_anchor_sha256']
                        or self._registration_sha256 is not None and acceptance['candidate']['registration_sha256'] != self._registration_sha256
                        or acceptance['observation']['path'] != expected_observation
                        or acceptance['source_operation_id'] != facts['source_operation_id']
                        or any(acceptance['candidate'][key] != candidate[key] for key in
                            ('ordinal', 'experiment_id', 'manifest_sha256', 'project_revision'))
                        or any(acceptance['submission'][key] != submitted[key] for key in ('intent_sha256', 'workflow_id', 'run_id'))
                        or submitted['state'] != 'submitted' or acceptance['execution']['record_sha256'] != execution['record_sha256']
                        or execution['durable_stop_confirmed'] is not True or execution['executor_stop_confirmed'] is not True
                        or runtime['state'] != 'queried' or runtime['binding'] is None
                        or runtime['job_id'] is None or native != {'state': 'SUCCEEDED', 'job_id': runtime['job_id']}
                        or accepted_runtime['namespace'] != info.namespace or accepted_runtime['job_id'] != runtime['job_id']
                        or accepted_runtime['phase'] != runtime['phase']
                        or accepted_runtime['kind'] != ('outcome' if terminal else 'status')
                        or runtime['temporal_status'] != ('COMPLETED' if terminal else 'RUNNING')
                        or accepted_runtime['binding_sha256'] != protocol.CycleAdmission._sha(runtime['binding'])
                        or accepted_runtime['memo_sha256'] != submitted['intent_sha256']
                        or accepted_runtime['kind'] == 'status' and accepted_runtime['evidence_sha'] != acceptance['evidence']['evidence_sha256']
                        or any(acceptance[key] != selection[key] for key in ('common_sha256', 'measurement_sources_sha256'))):
                    raise ValueError('Round acceptance differs from the complete current candidate facts')
                if not self._guard():
                    return facts
                self._prefix, self._confirmed = prefix, self._ordinal + 1
                self._registration_sha256 = acceptance['candidate']['registration_sha256']
                if self._confirmed == selection['count']:
                    self._state.update(phase='CYCLE_OBSERVED', outcome='selected_rounds_observed')
                else:
                    self._predecessor = {'prefix': prefix, 'acceptance': acceptance}
                    self._ordinal += 1
                    self._candidate = self._binding = self._job = None
                    self._submission, self._records = {}, {}
                    self._existing_execution = self._reconciled = False
                    self._state.update(observation_count=0, start_scheduled=False, request_scheduled=False,
                        collect_scheduled=False, last_normal_activity_id=None, last_facts_operation_id=None,
                        candidate_executor_stop_confirmed=None, phase='OBSERVING_EXECUTION')
                    self._advanced = True
            elif measurement['acceptance'] is not None:
                raise ValueError('Unconfirmed measurement cannot carry an acceptance')
            elif measurement['measurement_state'] == 'rejected':
                self._stop_reason = 'measurement_rejected'
            return facts

        def _next(self, facts, observed):
            if self._advanced:
                self._advanced = False
                return 'observe-candidate'
            if self._state['outcome'] == 'selected_rounds_observed':
                return None
            if self._state['collect_scheduled']:
                return 'reconcile-round' if self._guard() else None
            action = super()._next(facts, observed)
            if self._state['outcome'] == 'first_round_observed_c1d_required':
                self._state.update(outcome=None, phase='COLLECTING_ROUND')
                return 'collect-round'
            return action

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
            self._stop_handle = workflow.start_activity(protocol.CYCLE_ACTIVITY_NAMES_V3['stop'], request,
                activity_id='cycle-stop', task_queue=protocol.CYCLE_STOP_TASK_QUEUE_V2,
                schedule_to_close_timeout=timedelta(seconds=seconds), start_to_close_timeout=timedelta(seconds=seconds),
                retry_policy=RetryPolicy(maximum_attempts=1),
                cancellation_type=workflow.ActivityCancellationType.WAIT_CANCELLATION_COMPLETED)
            while True:
                try:
                    result = await asyncio.shield(self._stop_handle)
                    self._state['stop_activity_status'] = 'returned'
                    self._consume(result, 'stop', scheduled)
                    break
                except asyncio.CancelledError:
                    self._cancelled = True
                except ActivityError:
                    self._state['stop_activity_status'] = 'failed'
                    break
                except (ValueError, KeyError, TypeError, OverflowError, ApplicationError):
                    self._state['stop_activity_status'] = 'observation_rejected'
                    break
            self._state['phase'] = 'NEEDS_RECONCILIATION'

        @workflow.run
        async def run(self, original: dict) -> dict:
            try:
                protocol.validate_cycle_activity_request({'workflow_input': original, 'ordinal': 0, 'predecessor': None},
                                                         'observe-candidate')
                if original['protocol'] != 'ergora-training-cycle-v2':
                    raise ValueError('V2 Workflow requires its original v2 input')
                self._capacity(original)
            except (ValueError, KeyError, TypeError) as error:
                raise ApplicationError(str(error), type='cycle_workflow_input_rejected', non_retryable=True) from error
            action, cold = 'observe-candidate', True
            try:
                while self._guard():
                    value, scheduled = await self._ordinary(action, cold=cold)
                    if value is not None:
                        facts = self._consume(value, action, scheduled)
                        action = self._next(facts, value['status'] == 'observed') if facts is not None else (
                            'reconcile-round' if self._state['collect_scheduled'] else 'observe-candidate')
                    else:
                        action = 'reconcile-round' if self._state['collect_scheduled'] else 'observe-candidate'
                    if self._state['outcome'] == 'selected_rounds_observed':
                        return self.status()
                    if cold and self._work is None:
                        self._stop_reason = self._stop_reason or 'cold_budget_unconfirmed'
                    cold = False
                    if not self._guard():
                        break
                    if action in ('observe-candidate', 'reconcile-round'):
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


def create_cycle_workflow(program_version: int = 1):
    """Resolve the optional SDK class without constructing an unimportable local class."""
    if workflow is None:
        raise RuntimeError('Training cycle Workflow requires ergora[temporal]')
    protocol.cycle_activity_names(program_version)
    return TrainingCycleWorkflow if program_version == 1 else TrainingCycleWorkflowV2


def create_cycle_activities(client, program_version: int = 1, *,
                            normal_permit: asyncio.Semaphore | None = None,
                            stop_permit: asyncio.Semaphore | None = None):
    """Load optional SDK decorators only for the enabled cycle service."""
    from temporalio import activity
    from temporalio.exceptions import ApplicationError, CancelledError

    names = protocol.cycle_activity_names(program_version)
    version3 = program_version == 2

    async def invoke(action, request, window=None):
        await _cycle_capacity(request, client.data_converter)
        try:
            protocol.validate_cycle_activity_request(request, action)
            if request['workflow_input']['protocol'] != ('ergora-training-cycle-v2' if version3 else 'ergora-training-cycle-v1'):
                raise ValueError('Activity request differs from its registered program version')
            info = activity.info()
            if getattr(info, 'is_local', False):
                raise ValueError('Local activities cannot control a training cycle')
            source = {name: getattr(info, name, None) for name in ('workflow_id', 'workflow_run_id',
                'workflow_type', 'workflow_namespace', 'namespace', 'activity_id', 'activity_type', 'task_queue', 'attempt')}
            context = {'workflow_input': request['workflow_input'], 'activity_source': source,
                       'service_namespace': client.namespace}
            protocol.validate_cycle_activity_context(context)
            if source['activity_type'] != names[action]:
                raise ValueError('SDK source differs from the registered activity action')
            if not version3 and action == 'start' and request['ordinal'] != 0:
                raise ValueError('successor_not_enabled')
        except (ValueError, TypeError, KeyError) as error:
            raise ApplicationError(str(error), type='cycle_activity_request_rejected', non_retryable=True) from error
        original = request['workflow_input']
        version2 = action in ('request-execution-or-observe', 'observe-candidate')
        arguments = (Path(original['control_home']), original['project'], original['cycle_id'], original['authorization_sha256'])
        cold = _CycleOperation(*arguments, 'inspect-controller-activity', activity_context=context, window=window)
        inspection = await cold.run()
        if inspection['status'] == 'capacity_exceeded':
            raise ApplicationError(inspection['reason'], type='cycle_activity_capacity_exceeded', non_retryable=True)
        records = [_activity_operation_result(cold, inspection)]
        outcome = inspection
        if inspection['status'] == 'inspected':
            snapshot = inspection['snapshot']
            policy, clock = snapshot['policy'], snapshot['authorization']['clock']
            work_window = dict(cold.payload['bootstrap'])
            work_window['deadline_ns'] = min(work_window['deadline_ns'],
                work_window['started_ns'] + policy['control_timeout_seconds'] * 1_000_000_000,
                clock['boottime_ns'] + (policy['wall_seconds'] - policy['cleanup_seconds']) * 1_000_000_000)
            if version3:
                if snapshot['authorization']['schema_version'] != 3:
                    raise ValueError('V3 activity requires its complete original schema3 authorization')
                if action == 'stop':
                    outcome = await stop_live_controller(*arguments, reason=request['reason'], inspection=inspection,
                        activity_context=context, operation_records=records)
                else:
                    binding = {'protocol': original['protocol'], **inspection['controller'],
                               'ordinal': request['ordinal'], 'predecessor': request['predecessor']}
                    if action == 'start' and source['attempt'] == 1 and not inspection['candidate_exists']:
                        candidate = _CycleCandidate(*arguments, snapshot=snapshot, controller=binding,
                            activity_context=context, window=work_window)
                        outcome = await candidate.run()
                        records.extend(_activity_operation_result(operation, value)
                            for operation, value in zip(candidate.operations, candidate.results))
                    elif action in ('start', 'reconcile'):
                        operation = _CycleOperation(*arguments, 'reconcile-candidate', snapshot=snapshot,
                            ordinal=request['ordinal'], start_context={'controller': binding},
                            activity_context=context, window=work_window)
                        outcome = await operation.run()
                        records.append(_activity_operation_result(operation, outcome))
                    if action in ('collect-round', 'reconcile-round'):
                        mode = 'collect-round' if action == 'collect-round' and source['attempt'] == 1 else 'reconcile-round'
                    else:
                        mode = ('request-execution-candidate' if action == 'request-execution-or-observe'
                                and source['attempt'] == 1 else 'observe-candidate')
                    operation = _CycleOperation(*arguments, mode, snapshot=snapshot,
                        ordinal=request['ordinal'], start_context={'controller': binding},
                        activity_context=context, window=work_window)
                    outcome = await operation.run()
                    records.append(_activity_operation_result(operation, outcome))
            elif version2:
                budget = inspection['facts']['budget']
                if budget['state'] == 'valid' and budget['work_remaining_seconds'] > 0:
                    binding = {'protocol': original['protocol'], **inspection['controller'], 'ordinal': request['ordinal']}
                    mode = ('request-execution-candidate' if action == 'request-execution-or-observe'
                            and source['attempt'] == 1 else 'observe-candidate')
                    operation = _CycleOperation(*arguments, mode, snapshot=snapshot,
                        ordinal=request['ordinal'], start_context={'controller': binding},
                        activity_context=context, window=work_window)
                    outcome = await operation.run()
                    records.append(_activity_operation_result(operation, outcome))
            elif action in ('start', 'reconcile'):
                binding = {'protocol': original['protocol'], **inspection['controller'], 'ordinal': request['ordinal']}
                if action == 'start' and source['attempt'] == 1 and not inspection['candidate_exists']:
                    candidate = _CycleCandidate(*arguments, snapshot=snapshot, controller=binding,
                        activity_context=context, window=work_window if window is not None else None)
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
        envelope = {'schema_version': 3 if version3 else 2 if version2 else 1,
            'protocol': 'ergora-training-cycle-activity-v3' if version3 else 'ergora-training-cycle-activity-v2' if version2 else 'ergora-training-cycle-activity-v1', 'action': action,
            'status': 'observed' if inspection['status'] == 'inspected' and outcome.get('status') != 'unknown' else 'unknown',
            'workflow_input': original, 'controller': inspection.get('controller'),
            'observation': inspection.get('observation'), 'inspection': records[0], 'operations': records[1:],
            'runtime_status': outcome.get('runtime_status', inspection.get('runtime_status', 'not_queried'))}
        if version2 or version3:
            # These are H-produced values already in memory, never reads through refs.
            envelope['facts'] = None if action == 'stop' else outcome.get('facts')
            if outcome.get('candidate_observation', {}).get('status') == 'unknown':
                envelope['status'] = 'unknown'
            if envelope['facts'] is not None:
                budget = envelope['facts']['budget']
                envelope['observation'] = {key: budget[key] for key in
                    ('total_remaining_seconds', 'boot_id', 'boottime_ns', 'observed_at')}
        await _cycle_capacity(envelope, client.data_converter)
        return envelope

    registered = {}
    for action, name in names.items():
        # Each closure is a real async SDK activity with one strict business request.
        def build(selected):
            permit = stop_permit if selected == 'stop' else normal_permit

            async def execute(request: dict) -> dict:
                try:
                    if permit is None:
                        return await invoke(selected, request)
                    # Freeze before queuing. Both versions consume their original
                    # cold window and the SDK's full scheduled/started allowance.
                    loop_started = asyncio.get_running_loop().time()
                    boot, ticks = budget_clock._clock()
                    observed = datetime.now(timezone.utc)
                    info = activity.info()
                    remaining = min(((start + timeout - observed).total_seconds()
                        for start, timeout in ((info.scheduled_time, info.schedule_to_close_timeout),
                                               (info.started_time, info.start_to_close_timeout))
                        if timeout is not None), default=None)
                    if remaining is not None and remaining < 1:
                        raise ApplicationError('Original SDK activity allowance cannot admit a cold observation',
                            type='cycle_activity_request_rejected', non_retryable=True)
                    cold_seconds = 10 if remaining is None else min(10, remaining)
                    window = {'boot_id': boot, 'started_ns': ticks,
                              'deadline_ns': ticks + int(cold_seconds * 1_000_000_000)}
                    sdk_timeout = asyncio.timeout_at(None if remaining is None else loop_started + remaining)
                    waiting_timeout = asyncio.timeout_at(loop_started + cold_seconds)
                    try:
                        async with sdk_timeout:
                            async with waiting_timeout:
                                await permit.acquire()
                            try:
                                current_boot, current_ticks = budget_clock._clock()
                                if (current_boot != boot or current_ticks < ticks
                                        or current_ticks >= window['deadline_ns']):
                                    raise ApplicationError('Original cycle observation window ended while queuing',
                                        type='cycle_activity_request_rejected', non_retryable=True)
                                return await invoke(selected, request, window)
                            finally:
                                # The original run methods wait for S/H, pending
                                # roots and all stop peers before propagating cancel.
                                permit.release()
                    except TimeoutError:
                        if not sdk_timeout.expired() and not waiting_timeout.expired():
                            raise
                        raise ApplicationError('Original cycle activity allowance ended',
                            type='cycle_activity_request_rejected', non_retryable=True) from None
                except CancelledError:
                    raise
                except Exception as error:
                    if not version3:
                        if isinstance(error, _CycleCapacityError):
                            logging.error('Cycle activity request capacity failure: %s', error)
                            raise ApplicationError(str(error), type='cycle_activity_capacity_exceeded', non_retryable=True) from error
                        raise
                    logging.exception('Complete original V3 cycle activity failure')
                    error_type = ('cycle_activity_capacity_exceeded' if isinstance(error, _CycleCapacityError)
                        else error.type if isinstance(error, ApplicationError) and error.type in (
                            'cycle_activity_request_rejected', 'cycle_activity_capacity_exceeded')
                        else 'cycle_activity_failed')
                    message = {'cycle_activity_request_rejected': 'Cycle activity request rejected',
                        'cycle_activity_capacity_exceeded': 'Complete cycle activity capacity exceeded',
                        'cycle_activity_failed': 'Cycle activity failed'}[error_type]
                    raise ApplicationError(message, type=error_type, non_retryable=True) from None
            return execute
        registered[action] = activity.defn(name=name)(build(action))
    return registered


async def _serve_cycle() -> None:
    from perf_temporal.connection import connect
    from temporalio.client import Client
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
        config = client.config()
        config['data_converter'] = replace(client.data_converter, failure_converter_class=_CycleFailureConverter)
        clients = {1: client, 2: Client(**config)}
        normal_permit, stop_permit = asyncio.Semaphore(1), asyncio.Semaphore(1)
        activities = {version: create_cycle_activities(clients[version], version,
            normal_permit=normal_permit, stop_permit=stop_permit) for version in (1, 2)}
        for version, queue in ((1, protocol.CYCLE_TASK_QUEUE), (2, protocol.CYCLE_TASK_QUEUE_V2)):
            workers.append(Worker(clients[version], task_queue=queue, workflows=[create_cycle_workflow(version)],
                activities=[activities[version][action] for action in protocol.cycle_activity_names(version)
                            if action != 'stop'], max_concurrent_activities=1,
                graceful_shutdown_timeout=timedelta(0), on_fatal_error=fatal))
        for version, queue in ((1, protocol.CYCLE_STOP_TASK_QUEUE), (2, protocol.CYCLE_STOP_TASK_QUEUE_V2)):
            workers.append(Worker(clients[version], task_queue=queue, activities=[activities[version]['stop']],
                max_concurrent_activities=1, graceful_shutdown_timeout=timedelta(0), on_fatal_error=fatal))
        running = [asyncio.create_task(worker.run()) for worker in workers]
        done, _ = await asyncio.wait((*running, waiting), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task in running and not task.cancelled() and failure is None:
                failure = task.exception()
    finally:
        async def finish_worker(worker, task):
            nonlocal failure
            shutdown = None
            while not task.done():
                if shutdown is None or shutdown.cancelled():
                    shutdown = asyncio.create_task(worker.shutdown())
                try:
                    await asyncio.wait((task, shutdown), return_when=asyncio.FIRST_COMPLETED)
                except asyncio.CancelledError:
                    continue
            if not task.cancelled() and task.exception() is not None and failure is None:
                failure = task.exception()
            if shutdown is not None:
                if not shutdown.done():
                    shutdown.cancel()
                while not shutdown.done():
                    try:
                        await asyncio.shield(shutdown)
                    except asyncio.CancelledError:
                        continue
                if not shutdown.cancelled():
                    shutdown.result()
            if worker.is_running and not worker.is_shutdown:
                # SDK run cancellation can interrupt shutdown itself. Public
                # shutdown cannot resume it, so task completion proves no drain.
                raise RuntimeError('Cycle worker cleanup is incomplete; running state is unknown')

        # Stop both normal pollers together; keep both stop pollers available
        # until normal S/H and pending-root cleanup have actually returned.
        async def finish():
            for start in (0, 2):
                finishing = asyncio.gather(*(finish_worker(worker, task)
                    for worker, task in zip(workers[start:start + 2], running[start:start + 2])),
                    return_exceptions=True)
                while not finishing.done():
                    try:
                        await asyncio.shield(finishing)
                    except asyncio.CancelledError:
                        continue
                # An aborted SDK run must not interrupt its peer's actual drain
                # or advance shutdown to the stop group.
                for result in finishing.result():
                    if isinstance(result, BaseException):
                        raise result
        cleanup = asyncio.create_task(finish())
        try:
            while not cleanup.done():
                try:
                    await asyncio.shield(cleanup)
                except asyncio.CancelledError:
                    continue
            cleanup.result()
        finally:
            connecting.cancel()
            waiting.cancel()
            settled = asyncio.gather(connecting, waiting, return_exceptions=True)
            try:
                while not settled.done():
                    try:
                        await asyncio.shield(settled)
                    except asyncio.CancelledError:
                        continue
                settled.result()
            finally:
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
