"""Identity-bound execution records shared with the dependency-isolated native hook."""

from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta, timezone
import getpass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

from . import budget_clock, processes, reference


PROTOCOL = 'ergora-training-execution-v1'
BUDGET_TASK_QUEUE = 'ergora-training-budget-v1'
CYCLE_MEMO_KEY = 'ergora.training_cycle_sha256'
LIMIT = 1_048_576
GATE_SOURCES = (
    'training_execution_protocol.py', 'reference_training_execution.py',
    'reference_training_submission.py', 'reference_training_context.py',
    'reference_training_runtime.py', 'reference_training_cancellation.py', 'reference_history.py',
    'reference_training_budget.py', 'reference_training_worker.py', 'training.py', 'reference.py',
    'training_cycles.py', 'registrations.py', 'data/schemas/training-cycle-v1.json',
    'data/schemas/project-registration-v1.json', 'definition_bundles.py', 'contracts.py',
    'asset_trees.py', 'state.py', 'budget_clock.py', 'processes.py', 'reference_creation_process.py',
    '__init__.py', 'data/reference-manifest.json', 'data/native-runtime/training-executor-admission-v1.json',
)


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(label + ' has incomplete or unexpected fields')


def _match(actual, expected, label):
    from dev_platform.contracts import canonical_sha

    if canonical_sha(actual) != canonical_sha(expected):
        raise ValueError(label + ' differs from its complete original identity')


def _digest(value):
    if not isinstance(value, str) or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError('Execution record requires a complete SHA256')


def validate_budget_binding(value):
    common = {'cycle_id', 'authorization_sha256', 'task_queue'}
    if (not isinstance(value, dict) or set(value) not in (common, common | {'controller'})
            or not isinstance(value.get('cycle_id'), str)
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value['cycle_id']) is None
            or value.get('task_queue') != BUDGET_TASK_QUEUE):
        raise ValueError('Training intent requires its exact original budget and supported protocol queue')
    _digest(value.get('authorization_sha256'))
    if 'controller' in value:
        controller = value['controller']
        _exact(controller, ('protocol', 'workflow_id', 'run_id', 'intent_sha256', 'ordinal'), 'Controller binding')
        if (controller['protocol'] != 'ergora-training-cycle-v1'
                or not isinstance(controller['workflow_id'], str) or not controller['workflow_id']
                or not isinstance(controller['run_id'], str) or not 1 <= len(controller['run_id']) <= 128
                or controller['run_id'].strip() != controller['run_id']
                or type(controller['ordinal']) is not int or not 0 <= controller['ordinal'] < 32):
            raise ValueError('Controller binding requires its original fixed run and selected ordinal')
        _digest(controller['intent_sha256'])


def _process(value):
    _exact(value, ('pid', 'start_ticks', 'boot_id'), 'Process identity')
    if (type(value['pid']) is not int or value['pid'] < 1
            or not isinstance(value['start_ticks'], str) or re.fullmatch('[0-9]+', value['start_ticks']) is None
            or not isinstance(value['boot_id'], str) or re.fullmatch('[a-f0-9-]{36}', value['boot_id']) is None):
        raise ValueError('Execution process identity is invalid')


def _fd(path):
    # O_NONBLOCK is necessary before fstat: opening a FIFO must not wait for a writer.
    for parent in (path, *path.parents):
        try:
            details = parent.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(details.st_mode) or getattr(details, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Execution records cannot use symlinks or reparse points')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0)
    descriptor = os.open(path, flags)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError('Execution records require ordinary files')
    return descriptor


def read_raw(path: Path, limit: int = LIMIT) -> bytes:
    with os.fdopen(_fd(path), 'rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Complete execution record exceeds its read capacity')
    return raw


def decode(raw: bytes) -> dict:
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('Duplicate execution record key: ' + key)
            value[key] = item
        return value

    def number(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError('Execution records require finite JSON numbers')
        return value

    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=number, parse_float=number)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Execution record is not complete UTF-8 JSON') from error
    if not isinstance(value, dict):
        raise ValueError('Execution record must be a JSON object')
    return value


class PhaseFrames:
    """Read the ordered stopped/result response for one identity-bound helper."""

    def __init__(self, identity: dict, output: Path, result_limit: int):
        self.identity, self.output, self.result_limit = identity, output, result_limit
        self.frames, self.buffer, self.problem = [], bytearray(), None

    def receive(self, raw: bytes) -> None:
        if self.problem is not None:
            return
        self.buffer.extend(raw)
        while b'\n' in self.buffer:
            line, _, rest = self.buffer.partition(b'\n')
            self.buffer = bytearray(rest)
            event = 'stopped' if not self.frames else 'result'
            limit = 65_536 if event == 'stopped' else self.result_limit
            try:
                if len(self.frames) == 2 or len(line) > limit:
                    raise ValueError('Unexpected or oversized training phase frame')
                frame = decode(line)
                field = 'process' if event == 'stopped' else 'result'
                if (set(frame) != {*self.identity, 'event', field}
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
            except ValueError as error:
                self.problem = str(error)
                return
        limit = 65_536 if not self.frames else self.result_limit
        if len(self.buffer) > limit:
            self.problem = 'Incomplete training phase frame exceeds its complete response capacity'


def owner_record(value: dict) -> dict:
    common = ('schema_version', 'intent_sha256', 'authorization_sha256', 'pid', 'start_ticks', 'boot_id', 'context_sha256')
    version = value.get('schema_version')
    if type(version) is not int or version not in (1, 2):
        raise ValueError('Unsupported original budget owner schema')
    _exact(value, (*common, 'execution_capability') if version == 2 else common, 'Budget owner')
    for name in ('intent_sha256', 'authorization_sha256', 'context_sha256'):
        _digest(value[name])
    _process({key: value[key] for key in ('pid', 'start_ticks', 'boot_id')})
    if version == 2 and value['execution_capability'] is not None:
        capability = value['execution_capability']
        _exact(capability, ('protocol', 'admission_protocol', 'descriptor_sha256', 'installation',
            'native_python', 'cycle_ready_sha256', 'gate_sources'), 'Execution capability')
        if (capability['protocol'] != PROTOCOL or capability['admission_protocol'] != reference.TRAINING_PROTOCOL
                or not isinstance(capability['gate_sources'], dict)
                or set(capability['gate_sources']) != set(GATE_SOURCES)):
            raise ValueError('Unsupported complete execution capability')
        for digest in (*capability['gate_sources'].values(), capability['descriptor_sha256'], capability['cycle_ready_sha256']):
            _digest(digest)
        installation = Path(capability['installation'])
        if not installation.is_absolute() or capability['native_python'] != str(installation / '.venv/bin/python'):
            raise ValueError('Execution capability has no exact native interpreter')
    return value


def owner_active(path: Path, expected: dict) -> bool:
    """Observe the same live owner and both existing locks; never create one."""
    import fcntl

    try:
        value = owner_record(decode(read_raw(path)))
        _match(value, expected, 'Original live owner')
        _match(processes.identity(value['pid']), {key: value[key] for key in ('pid', 'start_ticks', 'boot_id')}, 'Live process')
        with os.fdopen(_fd(path.parent / 'lock'), 'rb') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                with os.fdopen(_fd(path.parent / 'initializing.lock'), 'rb') as ready:
                    try:
                        fcntl.flock(ready, fcntl.LOCK_SH | fcntl.LOCK_NB)
                    except BlockingIOError:
                        return False
                return True
    except (OSError, ValueError):
        return False
    return False


def source_capability(installation: Path, ready: dict) -> dict | None:
    from dev_platform.contracts import canonical_sha

    reference.validate_installation(installation, training=True)
    descriptor = installation / 'ergora-native-runtime.json'
    if not descriptor.exists():
        return None
    return {'protocol': PROTOCOL, 'admission_protocol': reference.TRAINING_PROTOCOL,
        'descriptor_sha256': hashlib.sha256(read_raw(descriptor)).hexdigest(),
        'installation': str(installation), 'native_python': str(installation / '.venv/bin/python'),
        'cycle_ready_sha256': canonical_sha(ready), 'gate_sources': {
            name: hashlib.sha256(read_raw(Path(__file__).parent / name)).hexdigest() for name in GATE_SOURCES}}


def validate_sources(capability: dict) -> None:
    installation = reference.validate_installation(Path(capability['installation']), training=True)
    if hashlib.sha256(read_raw(installation / 'ergora-native-runtime.json')).hexdigest() != capability['descriptor_sha256']:
        raise ValueError('Original native execution descriptor changed')
    for name, expected in capability['gate_sources'].items():
        if hashlib.sha256(read_raw(Path(__file__).parent / name)).hexdigest() != expected:
            raise ValueError('Original execution gate source changed: ' + name)


def publish(path: Path, value: dict, root: Path) -> None:
    """Synchronize an immutable publication; equal retry never grants a launch."""
    from dev_platform import adapter

    adapter.safe_file(root, path.relative_to(root).as_posix())
    # Check existing bytes with the nonblocking reader before native equal retry.
    try:
        _match(decode(read_raw(path)), value, 'Existing execution record')
    except FileNotFoundError:
        pass
    adapter.publish(path, value)
    sync_directories(path.parent, root)


def sync_directories(directory: Path, root: Path) -> None:
    for selected in (directory, *directory.parents):
        descriptor = os.open(selected, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if selected == root:
            return
    raise ValueError('Execution publication escaped its registered root')


class CycleAdmission:
    """A parent's irreversible veto, not a grant to start or execute training.

    Callers validate their complete source and clock before using this permit.
    All storage operations may block; live owners must supervise their caller.
    """

    def __init__(self, directory: Path, authorization: dict):
        if authorization['schema_version'] != 2:
            raise ValueError('Controller admission requires explicit birth-time consent')
        self.directory, self.authorization = directory, authorization
        self.folder = directory / 'controller'
        self.lock = self.folder / 'admission.lock'
        self.stop = self.folder / 'stop.json'
        self.identity = {'schema_version': 1, 'kind': 'training-cycle-stop',
            'protocol': authorization['controller']['protocol'], 'control_home': authorization['control_home'],
            'project': authorization['project'], 'cycle_id': authorization['cycle_id'],
            'input_sha256': authorization['input_sha256'], 'authorization_sha256': authorization['sha256'],
            'actor_id': authorization['controller']['actor_id']}

    @staticmethod
    def _sha(value):
        # This boundary also runs in the dependency-isolated native interpreter.
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()

    def _authorization(self):
        saved = decode(read_raw(self.directory / 'authorization.json'))
        if self._sha(saved) != self._sha(self.authorization):
            raise ValueError('Original controller authorization changed')

    @contextmanager
    def _locked(self, *, shared):
        import fcntl

        with os.fdopen(_fd(self.lock), 'rb') as lock:
            if lock.read(1):
                raise ValueError('Controller admission requires its ordinary empty original lock')
            fcntl.flock(lock, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB)
            yield

    def validate_lock(self, *, synchronize=False):
        with os.fdopen(_fd(self.lock), 'rb') as lock:
            if lock.read(1):
                raise ValueError('Controller admission requires its ordinary empty original lock')
            if synchronize:
                os.fsync(lock.fileno())
                sync_directories(self.folder, self.directory)

    def check(self):
        """Recheck under an existing permit immediately before the original action."""
        self._authorization()
        try:
            self.stop.lstat()
        except FileNotFoundError:
            return
        raise ValueError('Controller stop is visible; no new training action is admitted')

    @contextmanager
    def permission(self):
        """Try one shared permit without waiting, creating files or extending time."""
        with self._locked(shared=True):
            self.check()
            yield self

    def controller_intent(self):
        try:
            intent = decode(read_raw(self.folder / 'intent.json'))
        except FileNotFoundError:
            return None
        authorization, controller = self.authorization, self.authorization['controller']
        workflow_input = {name: authorization[name] for name in
            ('control_home', 'project', 'cycle_id', 'input_sha256')}
        workflow_input.update(protocol=controller['protocol'], authorization_sha256=authorization['sha256'])
        expected = {**workflow_input, 'schema_version': 1, 'kind': 'training-cycle-controller-intent',
            'project_revision': authorization['project_revision'], 'workflow_id': controller['workflow_id'],
            'task_queue': controller['task_queue'], 'workflow_input': workflow_input}
        if self._sha(intent) != self._sha(expected):
            raise ValueError('Controller intent differs from its complete original authorization')
        return intent

    def _intent_sha(self):
        intent = self.controller_intent()
        return self._sha(intent) if intent is not None else None

    def bind(self, intent, plan):
        """Bind one original selected start to the complete local parent receipt.

        Remote history belongs to the application's asynchronous consumers.
        This same local contract is also used by the isolated native gate.
        """
        binding = intent['budget']
        validate_budget_binding(binding)
        if 'controller' not in binding:
            raise ValueError('Controller authorization requires complete controller binding and final admission gates')
        controller = binding['controller']
        parent = self.controller_intent()
        if parent is None:
            raise ValueError('Controller binding has no original complete intent')
        expected = {'schema_version': 1, 'intent_sha256': self._sha(parent),
            'workflow_id': parent['workflow_id'], 'workflow_input_sha256': self._sha(parent['workflow_input'])}
        if self._sha(decode(read_raw(self.folder / 'attempt.json'))) != self._sha(expected):
            raise ValueError('Controller binding differs from its original complete attempt')
        if self._sha(decode(read_raw(self.folder / 'receipt.json'))) != self._sha({**expected, 'run_id': controller['run_id']}):
            raise ValueError('Controller binding differs from its original fixed-run receipt')
        try:
            (self.folder / 'rejection.json').lstat()
        except FileNotFoundError:
            pass
        else:
            raise ValueError('Controller submission was rejected; no new training action is admitted')
        authorization = self.authorization
        if (binding['cycle_id'] != authorization['cycle_id']
                or binding['authorization_sha256'] != authorization['sha256']
                or controller['protocol'] != parent['protocol']
                or controller['workflow_id'] != parent['workflow_id']
                or controller['intent_sha256'] != expected['intent_sha256']
                or controller['ordinal'] >= len(plan['admissions'])):
            raise ValueError('Controller binding differs from its original authorization or selected position')
        selected = plan['admissions'][controller['ordinal']]
        if (selected['experiment_id'] != intent['experiment_id']
                or self._sha(selected['observation']) != self._sha(intent['observation'])):
            raise ValueError('Controller binding differs from its complete original selected admission')
        return parent

    def _stop_record(self, value):
        _exact(value, (*self.identity, 'controller_intent_sha256', 'reason', 'requested_at'), 'Controller stop')
        if value['controller_intent_sha256'] is not None:
            _digest(value['controller_intent_sha256'])
        if value['controller_intent_sha256'] != self._intent_sha():
            raise ValueError('Controller stop differs from its original controller intent')
        if not isinstance(value['reason'], str) or not value['reason'].strip():
            raise ValueError('Controller stop requires a nonempty reason')
        try:
            requested = datetime.fromisoformat(value['requested_at'])
            if requested.utcoffset() != timedelta(0) or requested.isoformat() != value['requested_at']:
                raise ValueError('Controller stop requires its complete UTC time')
        except TypeError as error:
            raise ValueError('Controller stop requires its complete UTC time') from error
        expected = {**value, **self.identity}
        if self._sha(expected) != self._sha(value):
            raise ValueError('Controller stop differs from its original authorization')
        return value

    def observe(self, *, synchronize=False, drain=False):
        """Keep visibility, durable bytes, parent permits and subtree stop separate."""
        observed = {'stop_visible': None, 'identity_matches': None, 'record': None, 'record_sha256': None,
            'stop_durable': None, 'admission_drained': None, 'executor_stop_confirmed': None, 'reason': None}
        try:
            self.stop.lstat()
        except FileNotFoundError:
            return {**observed, 'stop_visible': False}
        except OSError as error:
            return {**observed, 'reason': str(error)}
        observed['stop_visible'] = True
        try:
            self._authorization()
            with os.fdopen(_fd(self.stop), 'rb') as stream:
                raw = stream.read(LIMIT + 1)
                if len(raw) > LIMIT:
                    raise ValueError('Complete controller stop exceeds its read capacity')
                value = self._stop_record(decode(raw))
                observed.update(identity_matches=True, record=value, record_sha256=hashlib.sha256(raw).hexdigest())
                if synchronize or drain:
                    os.fsync(stream.fileno())
                    sync_directories(self.folder, self.directory)
                    observed['identity_matches'] = False
                    self._authorization()
                    with os.fdopen(_fd(self.stop), 'rb') as again:
                        original, current = os.fstat(stream.fileno()), os.fstat(again.fileno())
                        if ((original.st_dev, original.st_ino) != (current.st_dev, current.st_ino)
                                or again.read(LIMIT + 1) != raw):
                            raise ValueError('Controller stop changed during durable observation')
                    self._stop_record(value)
                    observed['identity_matches'] = True
                    observed['stop_durable'] = True
        except (OSError, ValueError) as error:
            if observed['identity_matches'] is None:
                observed['identity_matches'] = False
            return {**observed, 'reason': str(error)}
        if drain:
            try:
                with self._locked(shared=False):
                    after = self.observe(synchronize=True)
                    if after['stop_durable'] is True and after['record_sha256'] == observed['record_sha256']:
                        after['admission_drained'] = True
                    else:
                        after['reason'] = after['reason'] or 'Controller stop changed before parent admission drained'
                    return after
            except (OSError, ValueError) as error:
                observed['reason'] = str(error) or 'Original parent admission permits remain active'
        return observed

    def request_stop(self, reason):
        """Publish the veto before fsync; never repair or replace an existing path."""
        self._authorization()
        self.validate_lock()
        try:
            self.stop.lstat()
        except FileNotFoundError:
            pass
        else:
            return self.observe(synchronize=True, drain=True)
        value = {**self.identity, 'controller_intent_sha256': self._intent_sha(),
            'reason': reason, 'requested_at': datetime.now(timezone.utc).isoformat()}
        self._stop_record(value)
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
        if len(raw) > LIMIT:
            raise ValueError('Complete controller stop exceeds its publication capacity')
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        try:
            descriptor = os.open(self.stop, flags, 0o600)
        except FileExistsError:
            return self.observe(synchronize=True, drain=True)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            sync_directories(self.folder, self.directory)
        except OSError as error:
            return {**self.observe(), 'reason': 'Controller stop durability is unconfirmed: ' + str(error)}
        return self.observe(synchronize=True, drain=True)


class ExecutionRecords:
    """Read and bind one original chain without importing application state or SDKs."""

    def __init__(self, project: dict, ident: str, home: str):
        from agent_platform.core import slug
        from dev_platform import adapter
        from dev_platform.contracts import canonical_sha

        self.project, self.ident, self.home, self.sha, self.adapter = project, slug(ident), home, canonical_sha, adapter
        self.execution = project['registration']['definition']['execution']
        self.root, self.config = (Path(self.execution[key]) for key in ('state_directory', 'config_directory'))
        self.prefix = 'training/jobs/' + self.ident
        self.folder = adapter.safe_file(self.root, self.prefix + '/managed-execution')
        self.budget = adapter.safe_file(self.root, 'ergora/training-submissions/' + self.ident + '.budget')
        self.originals, self.records = {}, {}

    def document(self, path: Path, *, optional=False, limit=LIMIT):
        try:
            raw = read_raw(path, limit)
        except FileNotFoundError:
            if optional:
                return None
            raise
        self.originals[path] = raw
        return decode(raw)

    def load(self):
        # Read descendants first so concurrent append-only publication is safe.
        self.records = {name: self.document(self.folder / (name + '.json'), optional=True)
                        for name in ('stopped', 'ack', 'attempt', 'launch', 'request')}
        self.intent = self.document(self.budget.parent / (self.ident + '.intent.json'), optional=True, limit=16 * LIMIT)
        self.owner = self.document(self.budget / 'owner.json', optional=True)
        if self.owner is not None:
            owner_record(self.owner)
        request = self.records['request']
        if request is None:
            if any(value is not None for value in self.records.values()):
                raise ValueError('Execution records have no original request')
            return self
        if self.intent is None or self.owner is None or self.owner.get('execution_capability') is None:
            raise ValueError('Execution request has no original capable owner and start intent')
        intent = self.intent
        common = ('schema_version', 'kind', 'protocol')
        _exact(request, (*common, 'control_home', 'project', 'project_revision', 'registration_sha256', 'execution',
            'experiment_id', 'job_id', 'workflow_id', 'run_id', 'start_intent_sha256', 'start_attempt_sha256',
            'start_receipt_sha256', 'authorization_sha256', 'owner_sha256', 'native_request_sha256',
            'native_request_semantic_sha256', 'confirmation', 'actor_id'), 'Execution request')
        if (type(request['schema_version']) is not int or type(request['project_revision']) is not int
                or request['project_revision'] < 1 or request['confirmation'] is not True
                or not isinstance(request['actor_id'], str) or not request['actor_id'].startswith('unix:')):
            raise ValueError('Execution request has invalid revision, confirmation or actor')
        expected = self.request_record(request['actor_id'])
        _match(request, expected, 'Execution request')
        _match({key: self.owner[key] for key in ('intent_sha256', 'authorization_sha256')},
            {'intent_sha256': self.sha(intent), 'authorization_sha256': request['authorization_sha256']}, 'Owner authorization')
        launch, attempt, ack, stopped = (self.records[name] for name in ('launch', 'attempt', 'ack', 'stopped'))
        if launch is not None:
            _exact(launch, (*common, 'request_sha256', 'owner_sha256', 'authorization_sha256', 'clock_sha256',
                'launch_id', 'execution_phase_id'), 'Execution launch')
            for name in ('launch_id', 'execution_phase_id'):
                if not isinstance(launch[name], str) or re.fullmatch('[a-f0-9]{32}', launch[name]) is None:
                    raise ValueError('Execution launch has an invalid observation identity')
            _digest(launch['clock_sha256'])
            _match(launch, {'schema_version': 1, 'kind': 'training-execution-launch', 'protocol': PROTOCOL,
                'request_sha256': self.sha(request), 'owner_sha256': self.sha(self.owner),
                'authorization_sha256': request['authorization_sha256'], 'clock_sha256': launch['clock_sha256'],
                'launch_id': launch['launch_id'], 'execution_phase_id': launch['execution_phase_id']}, 'Execution launch')
        if attempt is not None:
            if launch is None:
                raise ValueError('Execution attempt has no consumed launch')
            _process(attempt.get('supervisor'))
            _process(attempt.get('executor'))
            _match(attempt, {'schema_version': 1, 'kind': 'training-execution-attempt', 'protocol': PROTOCOL,
                'launch_sha256': self.sha(launch), 'request_sha256': self.sha(request), 'owner_sha256': self.sha(self.owner),
                'run_id': request['run_id'], 'job_id': request['job_id'], 'native_request_sha256': request['native_request_sha256'],
                'supervisor': attempt['supervisor'], 'executor': attempt['executor']}, 'Execution attempt')
        if ack is not None:
            if attempt is None:
                raise ValueError('Execution ack has no matching attempt')
            _match(ack, {'schema_version': 1, 'kind': 'training-execution-ack', 'protocol': PROTOCOL,
                'attempt_sha256': self.sha(attempt), 'launch_sha256': self.sha(launch),
                'request_sha256': self.sha(request), 'owner_sha256': self.sha(self.owner),
                'executor': attempt['executor']}, 'Execution ack')
        if stopped is not None:
            if ack is None:
                raise ValueError('Execution stop has no complete attempt and ack')
            process = stopped.get('process')
            _exact(process, ('status', 'returncode', 'output'), 'Reaped process')
            if (process['status'] not in ('succeeded', 'failed', 'cancelled', 'timed_out')
                    or process['returncode'] is not None and type(process['returncode']) is not int
                    or process['output'] != str(self.budget / ('observations/execute-' + launch['execution_phase_id']) / 'helper')):
                raise ValueError('Execution stop has no original process observation')
            stamp = datetime.fromisoformat(stopped['reaped_at'])
            if stamp.utcoffset() != timedelta(0) or stamp.isoformat() != stopped['reaped_at']:
                raise ValueError('Execution stop has no UTC reap observation')
            _match(stopped, {'schema_version': 1, 'kind': 'training-execution-stopped', 'protocol': PROTOCOL,
                'request_sha256': self.sha(request), 'launch_sha256': self.sha(launch),
                'attempt_sha256': self.sha(attempt), 'ack_sha256': self.sha(ack),
                'supervisor': attempt['supervisor'], 'process': process, 'reaped_at': stopped['reaped_at']}, 'Execution stop')
        return self

    def request_record(self, actor: str) -> dict:
        intent = self.intent
        start = self.document(self.budget.parent / (self.ident + '.attempt.json'))
        receipt = self.document(self.budget.parent / (self.ident + '.result.json'))
        self.native = self.document(self.root / self.prefix / 'request.json')
        _exact(self.native, ('schema_version', 'job_id', 'experiment', 'runner'), 'Native request')
        if type(self.native['schema_version']) is not int or self.native['schema_version'] != 1:
            raise ValueError('Native request has an invalid schema')
        item = intent['observation']['experiment']
        expected_start = {'schema_version': 1, 'intent_sha256': self.sha(intent), 'workflow_id': intent['workflow_id'],
                          'spec_sha256': self.sha(item['spec'])}
        _match(start, expected_start, 'Original start attempt')
        if not isinstance(receipt.get('run_id'), str) or not 1 <= len(receipt['run_id']) <= 128:
            raise ValueError('Original start receipt has no exact run ID')
        _match(receipt, {**expected_start, 'run_id': receipt['run_id']}, 'Original start receipt')
        _match(self.native, {'schema_version': 1, 'job_id': 'local-perf-' + self.ident,
            'experiment': item['spec'], 'runner': item['current_runner']}, 'Complete native request')
        expected = {'schema_version': 1, 'kind': 'training-execution-request', 'protocol': PROTOCOL,
            'control_home': self.home, 'project': self.project['id'], 'project_revision': intent['project_revision'],
            'registration_sha256': self.project['registration']['sha256'], 'execution': self.execution,
            'experiment_id': self.ident, 'job_id': self.native['job_id'], 'workflow_id': intent['workflow_id'],
            'run_id': receipt['run_id'], 'start_intent_sha256': self.sha(intent), 'start_attempt_sha256': self.sha(start),
            'start_receipt_sha256': self.sha(receipt), 'authorization_sha256': intent['budget']['authorization_sha256'],
            'owner_sha256': self.sha(self.owner),
            'native_request_sha256': hashlib.sha256(self.originals[self.root / self.prefix / 'request.json']).hexdigest(),
            'native_request_semantic_sha256': self.sha(self.native), 'confirmation': True, 'actor_id': actor}
        return expected

    def observe(self, *, durable: bool = False) -> dict:
        request, stopped = self.records['request'], self.records['stopped']
        result = {'status': 'not_requested' if request is None else 'stop_observed' if stopped else 'pending',
            'protocol': PROTOCOL, 'read_only': True, 'runtime_status': 'not_queried',
            'execution_authorized': False, 'execution_success': None,
            'reap_record_observed': stopped is not None, 'durable_stop_confirmed': None, 'executor_stop_confirmed': None,
            'owner': self.owner, 'records': self.records,
            'record_sha256': {name: self.sha(value) for name, value in self.records.items() if value is not None},
            'raw_sha256': {str(path): hashlib.sha256(raw).hexdigest() for path, raw in self.originals.items()}}
        if stopped is not None and durable:
            try:
                for path in self.originals:
                    descriptor = _fd(path)
                    try:
                        os.fsync(descriptor)
                    finally:
                        os.close(descriptor)
                sync_directories(self.folder, self.root)
                for path, raw in self.originals.items():
                    if read_raw(path, 16 * LIMIT) != raw:
                        raise ValueError('Original execution chain changed during durability observation')
                result.update(status='stopped', durable_stop_confirmed=True, executor_stop_confirmed=True,
                              durability_observed_at=datetime.now(timezone.utc).isoformat())
            except (OSError, ValueError) as error:
                result['durability_reason'] = str(error)
        return result


def validate_context(context: dict, chain: ExecutionRecords, *, live=True) -> CycleAdmission | None:
    """Rebind the complete birth context and its original sources, without State."""
    _exact(context, ('intent', 'authorization', 'policy', 'project', 'published_project'), 'Cached execution context')
    owner = chain.owner
    _match(context['intent'], chain.intent, 'Complete cached intent')
    if chain.sha(context) != owner['context_sha256']:
        raise ValueError('Complete execution context differs from the original owner')
    authorization, policy, intent = (context[name] for name in ('authorization', 'policy', 'intent'))
    if (authorization['sha256'] != chain.sha({key: value for key, value in authorization.items() if key != 'sha256'})
            or authorization['sha256'] != owner['authorization_sha256']):
        raise ValueError('Execution authorization differs from its original complete SHA256')
    cycle = Path(intent['control_home']) / 'training-cycles' / intent['project'] / intent['budget']['cycle_id']
    _match(decode(read_raw(cycle / 'authorization.json')), authorization, 'Original cycle authorization')
    raw = read_raw(cycle / 'cycle.json', 10_000_000)
    if hashlib.sha256(raw).hexdigest() != authorization['input_sha256']:
        raise ValueError('Original complete cycle input changed')
    plan = decode(raw)
    validate_budget_binding(intent['budget'])
    parent = None
    if authorization['schema_version'] == 2:
        parent = CycleAdmission(cycle, authorization)
        parent.bind(intent, plan)
    elif 'controller' in intent['budget']:
        raise ValueError('Manual authorization cannot acquire a controller binding')
    _match(plan['definition']['budget'], policy, 'Original complete computation policy')
    _match(plan['project'], context['project'], 'Original cycle project')
    ready = decode(read_raw(cycle / 'ready.json'))
    if (chain.sha(ready) != owner['execution_capability']['cycle_ready_sha256']
            or ready['authorization_sha256'] != authorization['sha256']):
        raise ValueError('Original cycle ready record changed')
    budget_clock.validate(authorization['clock'], policy['wall_seconds'])
    registration = context['published_project']['registration']
    for name, expected in registration['files'].items():
        _match(chain.document(chain.adapter.safe_file(chain.config, name)), expected, 'Original registered document')
    observed = intent['observation']
    for name, expected in {**observed['baseline_files'], **observed['experiment']['files']}.items():
        prefix, relative = name.split('/', 1)
        root = chain.root if prefix == 'state' else chain.config if prefix == 'config' else None
        if root is None or hashlib.sha256(read_raw(chain.adapter.safe_file(root, relative))).hexdigest() != expected:
            raise ValueError('Original experiment source changed: ' + name)
    validate_sources(owner['execution_capability'])
    if live and (not owner_active(chain.budget / 'owner.json', owner)
            or budget_clock.remaining(authorization['clock'], policy['wall_seconds'], policy['cleanup_seconds']) <= 0):
        raise ValueError('Original execution owner or computation budget is no longer active')
    if live and parent is not None:
        parent.check()
    return parent


def native_main(installation: str) -> None:
    """Use the selected venv; the callback remains inside the original executor lock."""
    from agent_platform import core

    payload = json.load(sys.stdin)
    context, phase = payload['cached'], payload['phase']
    project, intent = context['project'], context['intent']
    reference.validate_installation(Path(installation), training=True)
    if (sys.prefix != str(Path(installation) / '.venv') or core.ROOT != Path(installation)
            or core.PYTHON != Path(installation) / '.venv/bin/python'
            or core.STATE != Path(intent['execution']['state_directory'])
            or core.CONFIG != Path(intent['execution']['config_directory'])):
        raise ValueError('Managed native interpreter or registered core paths differ')
    from agent_platform.training_executor import process

    def admit(folder, record):
        chain = ExecutionRecords(project, intent['experiment_id'], intent['control_home']).load()
        validate_context(context, chain)
        request, launch = chain.records['request'], chain.records['launch']
        if request is None or launch is None or any(chain.records[name] is not None for name in ('attempt', 'ack', 'stopped')):
            raise ValueError('Managed execution requires its one unused consumed launch')
        protocol_phase = {'schema_version': 1, 'intent_sha256': chain.sha(intent),
            'authorization_sha256': chain.owner['authorization_sha256'], 'protocol': 'ergora-budget-phase-v1',
            'phase_id': launch['execution_phase_id'], 'mode': 'execute', 'context_sha256': chain.sha(context),
            'owner': {key: chain.owner[key] for key in ('pid', 'start_ticks', 'boot_id')}}
        _match(phase, protocol_phase, 'Complete execution supervisor phase')
        actor = (context['authorization']['controller']['actor_id'] if context['authorization']['schema_version'] == 2
                 else f'unix:{os.getuid()}:{getpass.getuser()}')
        if (folder != chain.folder.parent
                or launch['clock_sha256'] != chain.sha(context['authorization']['clock'])
                or request['actor_id'] != actor):
            raise ValueError('Native callback differs from its original supervisor, actor or clock')
        _match(record, chain.native, 'Native locked request')
        supervisor, executor = processes.identity(os.getppid()), processes.identity(os.getpid())
        _match(phase['owner'], {key: chain.owner[key] for key in ('pid', 'start_ticks', 'boot_id')}, 'Supervisor owner')
        parent_fields = Path('/proc/' + str(supervisor['pid']) + '/stat').read_text().rsplit(')', 1)[1].split()
        if int(parent_fields[1]) != chain.owner['pid']:
            raise ValueError('Native supervisor is not a child of its original budget owner')
        _match(processes.identity(chain.owner['pid']), phase['owner'], 'Original owner process')
        def active():
            if ((chain.root / ('training/fences/' + chain.ident + '.json')).exists()
                    or not owner_active(chain.budget / 'owner.json', chain.owner)
                    or budget_clock.remaining(context['authorization']['clock'], context['policy']['wall_seconds'],
                                              context['policy']['cleanup_seconds']) <= 0):
                raise ValueError('Original execution fence, owner or computation deadline forbids work')
            if parent is not None:
                parent.check()
        active()
        attempt = {'schema_version': 1, 'kind': 'training-execution-attempt', 'protocol': PROTOCOL,
            'launch_sha256': chain.sha(launch), 'request_sha256': chain.sha(request), 'owner_sha256': chain.sha(chain.owner),
            'run_id': request['run_id'], 'job_id': request['job_id'], 'native_request_sha256': request['native_request_sha256'],
            'supervisor': supervisor, 'executor': executor}
        publish(chain.folder / 'attempt.json', attempt, chain.root)
        if parent is not None:
            parent.check()
        publish(chain.folder / 'ack.json', {'schema_version': 1, 'kind': 'training-execution-ack', 'protocol': PROTOCOL,
            'attempt_sha256': chain.sha(attempt), 'launch_sha256': chain.sha(launch), 'request_sha256': chain.sha(request),
            'owner_sha256': chain.sha(chain.owner), 'executor': executor}, chain.root)
        active()
    chain = ExecutionRecords(project, intent['experiment_id'], intent['control_home'])
    parent = validate_context(context, chain.load()) if context['authorization']['schema_version'] == 2 else None
    with parent.permission() if parent is not None else nullcontext():
        print(json.dumps(process(chain.folder.parent, admit=admit), ensure_ascii=False, allow_nan=False))


def record_stopped(context: dict, phase: dict, process: dict) -> dict:
    """Called by S only after original processes.run reaps and emits stopped."""
    intent = context['intent']
    chain = ExecutionRecords(context['project'], intent['experiment_id'], intent['control_home']).load()
    request, launch, attempt, ack = (chain.records[name] for name in ('request', 'launch', 'attempt', 'ack'))
    if ack is None:
        return chain.observe()
    if launch['execution_phase_id'] != phase['phase_id']:
        raise ValueError('Reaped phase differs from its original launch')
    _match(attempt['supervisor'], processes.identity(os.getpid()), 'Actual reaping supervisor')
    stopped = {'schema_version': 1, 'kind': 'training-execution-stopped', 'protocol': PROTOCOL,
        'request_sha256': chain.sha(request), 'launch_sha256': chain.sha(launch),
        'attempt_sha256': chain.sha(attempt), 'ack_sha256': chain.sha(ack),
        'supervisor': attempt['supervisor'], 'process': process, 'reaped_at': datetime.now(timezone.utc).isoformat()}
    publish(chain.folder / 'stopped.json', stopped, chain.root)
    return ExecutionRecords(context['project'], intent['experiment_id'], intent['control_home']).load().observe(durable=True)


def inspect_main() -> None:
    """The frozen offline contract never imports a selected native installation."""
    payload = json.load(sys.stdin)
    chain = ExecutionRecords(payload['project'], payload['experiment_id'], payload['control_home']).load()
    if payload['operation'] == 'sources':
        capability = chain.owner.get('execution_capability') if chain.owner else None
        if capability is None:
            result = {'status': 'not_declared'}
        else:
            validate_sources(capability)
            result = {'status': 'matching'}
    else:
        result = chain.observe(durable=True)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
