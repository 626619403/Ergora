"""Local GPU resource transactions; a resource allocation never authorizes execution.

The single CPU session owns the legacy exclusive sentinel and a small durable
journal. Dedicated guards own execution and reaping. Neither NVML observations
nor a missing process are sufficient evidence for releasing a child allocation.
"""

import argparse
from contextlib import contextmanager
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import socket
import stat
import struct
import sys
import time
import uuid

from ergora.runtime import budget_clock
from ergora.runtime import processes


FRAME_LIMIT = 65_536
JOURNAL_LIMIT = 8 * 1_048_576
PROTOCOL = 'ergora-local-gpu-pool-v1'
READY_KIND = 'ergora-local-gpu-guard-ready'
STOPPED_KIND = 'ergora-local-gpu-guard-stopped'
_CONFIG_FIELDS = {'schema_version', 'kind', 'pool_id', 'coordination_directory',
                  'legacy_sentinel', 'device_uuids', 'mode'}
_ORIGIN_FIELDS = {'kind', 'operation_id', 'attempt_ref', 'source_sha256', 'config_sha256',
                  'authorization_ref', 'clock', 'wall_seconds', 'cleanup_reserve_seconds',
                  'owner_identity'}
_READY_FIELDS = {'schema_version', 'kind', 'session_id', 'request_id', 'input_sha256',
                 'origin_sha256', 'command_sha256', 'ordered_device_uuids', 'owner_identity',
                 'guard_identity', 'guard_source_sha256', 'prepared_subreaper', 'ready_at'}
_STOPPED_FIELDS = {'schema_version', 'kind', 'session_id', 'lease_id', 'request_sha256',
                   'consume_binding_sha256', 'guard_identity', 'origin_sha256',
                   'process_result', 'reaped_at', 'spawn_closed'}
_REQUEST_FIELDS = {'request_id', 'request_sha256', 'enqueue_sequence', 'origin',
                   'ordered_device_uuids', 'guard_ready_ref', 'state', 'lease_id',
                   'consume_binding', 'release_ref', 'reason'}
_TERMINAL = {'released', 'cancelled', 'expired'}
_RESERVED = {'granted', 'consumed', 'unknown'}
_IO_SECONDS = 1.0


class PoolUnavailable(ValueError):
    """A concrete resource or durability precondition could not be established."""


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def _sha(value):
    return hashlib.sha256(_encode(value)).hexdigest()


def _decode(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('Duplicate GPU admission field: ' + key)
            value[key] = item
        return value

    def constant(value):
        raise ValueError('Non-finite GPU admission JSON: ' + value)

    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)


def _fields(value, fields, description):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError('Invalid ' + description + ' fields')


def _version(value, kind):
    if type(value.get('schema_version')) is not int or value['schema_version'] != 1 or value.get('kind') != kind:
        raise ValueError('Unsupported GPU admission record version or kind')


def _digest(value):
    if not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('GPU admission requires complete SHA256 identities')
    return value


def _session_id(value):
    if not isinstance(value, str) or re.fullmatch('[0-9a-f]{32}', value) is None:
        raise ValueError('Invalid GPU pool session identity')
    return value


def _process_identity(value):
    _fields(value, {'pid', 'start_ticks', 'boot_id'}, 'process identity')
    if (type(value['pid']) is not int or value['pid'] < 1
            or not isinstance(value['start_ticks'], str)
            or re.fullmatch('[0-9]+', value['start_ticks']) is None
            or not isinstance(value['boot_id'], str)
            or re.fullmatch('[0-9a-f-]{36}', value['boot_id']) is None):
        raise ValueError('Invalid original process identity')
    return value


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Invalid GPU admission timestamp')
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed) or parsed.isoformat() != value:
        raise ValueError('GPU admission timestamps require canonical UTC')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _ordinary(path):
    path = Path(path)
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError('GPU admission paths cannot contain symlinks')


def _absolute(value):
    if not isinstance(value, str) or not value or '\0' in value:
        raise ValueError('GPU admission paths require explicit absolute names')
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts or str(path) != value:
        raise ValueError('GPU admission paths require canonical absolute names')
    _ordinary(path)
    return path


def _read_snapshot(path, limit=JOURNAL_LIMIT):
    path = Path(path)
    _ordinary(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('GPU admission records require ordinary files')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('GPU admission record changed during observation')
    if len(raw) > limit:
        raise ValueError('Complete GPU admission record exceeds its capacity')
    return raw, {'dev': before.st_dev, 'ino': before.st_ino,
                 'raw_sha256': hashlib.sha256(raw).hexdigest()}


def _read_bound(path, limit=JOURNAL_LIMIT):
    raw, binding = _read_snapshot(path, limit)
    current = Path(path).stat(follow_symlinks=False)
    if (current.st_dev, current.st_ino) != (binding['dev'], binding['ino']):
        raise ValueError('GPU admission record changed during observation')
    return raw, binding


def _read(path, limit=JOURNAL_LIMIT):
    return _read_bound(path, limit)[0]


def _sync(directory):
    _ordinary(directory)
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _publish(path, value, *, replace=False, limit=JOURNAL_LIMIT):
    """Publish one bounded record and acknowledge only durable complete readback."""
    path = Path(path)
    raw = _encode(value) + b'\n'
    if len(raw) > limit:
        raise ValueError('Complete GPU admission record exceeds its capacity')
    _ordinary(path)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    own_stat = os.fstat(descriptor)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
        _sync(path.parent)
        if _read(path, limit) != raw:
            raise ValueError('GPU admission publication changed during durable readback')
    finally:
        try:
            current = temporary.stat(follow_symlinks=False)
            if (current.st_dev, current.st_ino) == (own_stat.st_dev, own_stat.st_ino):
                temporary.unlink()
        except FileNotFoundError:
            pass
    return raw


def _identity():
    return processes.identity(os.getpid())


def _peer(connection):
    pid, uid, _gid = struct.unpack('3i', connection.getsockopt(
        socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i')))
    if uid != os.getuid():
        raise ValueError('GPU admission requires the original local user')
    return processes.identity(pid)


def _send(connection, value):
    raw = _encode(value)
    if not 0 < len(raw) <= FRAME_LIMIT:
        raise ValueError('Complete GPU admission message exceeds 64 KiB')
    connection.sendall(struct.pack('!I', len(raw)) + raw)


def _receive(connection):
    # socket timeouts alone restart after every recv; retain one complete-frame deadline.
    previous = connection.gettimeout()
    deadline = time.monotonic() + min(_IO_SECONDS, previous if previous is not None and previous > 0 else _IO_SECONDS)

    def exact(size):
        result = bytearray()
        while len(result) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('GPU admission frame exceeded its deadline')
            connection.settimeout(remaining)
            chunk = connection.recv(size - len(result))
            if not chunk:
                raise EOFError('GPU admission channel ended before a complete message')
            result.extend(chunk)
        return bytes(result)

    try:
        size, = struct.unpack('!I', exact(4))
        if not 0 < size <= FRAME_LIMIT:
            raise ValueError('Invalid GPU admission frame size')
        return _decode(exact(size))
    finally:
        connection.settimeout(previous)


def _remaining(origin, *, cleanup=False):
    budget_clock.validate(origin['clock'], origin['wall_seconds'])
    return budget_clock.remaining(origin['clock'], origin['wall_seconds'],
                                  0 if cleanup else origin['cleanup_reserve_seconds'])


def _children(identity):
    if processes.identity(identity['pid']) != identity:
        raise ValueError('Original GPU guardian identity changed')
    tasks = Path('/proc', str(identity['pid']), 'task')
    initial = sorted(tasks.iterdir())
    if not initial:
        raise ValueError('Original GPU guardian has no readable threads')
    children = set()
    for task in initial:
        values = (task / 'children').read_text(encoding='ascii').split()
        if any(not value.isdecimal() or int(value) < 1 for value in values):
            raise ValueError('Invalid kernel child observation')
        children.update(int(value) for value in values)
    if sorted(tasks.iterdir()) != initial or processes.identity(identity['pid']) != identity:
        raise ValueError('Original GPU guardian changed during child observation')
    return sorted(children)


def _artifact(value):
    _fields(value, {'root', 'relative_path', 'raw_sha256', 'semantic_sha256'}, 'artifact reference')
    _absolute(value['root'])
    relative = value['relative_path']
    if (not isinstance(relative, str) or not relative or '\0' in relative
            or Path(relative).is_absolute() or '..' in Path(relative).parts or str(Path(relative)) != relative):
        raise ValueError('Invalid original artifact relative path')
    _digest(value['raw_sha256'])
    if value['semantic_sha256'] is not None:
        _digest(value['semantic_sha256'])


def _origin(value):
    _fields(value, _ORIGIN_FIELDS, 'original execution origin')
    if value['kind'] != 'supervised-command-v1' or not isinstance(value['operation_id'], str) or not value['operation_id']:
        raise ValueError('Unsupported original execution protocol')
    _artifact(value['attempt_ref'])
    _artifact(value['authorization_ref'])
    _digest(value['source_sha256'])
    _digest(value['config_sha256'])
    _process_identity(value['owner_identity'])
    _fields(value['clock'], budget_clock.FIELDS, 'original budget clock')
    wall, reserve = value['wall_seconds'], value['cleanup_reserve_seconds']
    if type(wall) is not int or wall <= 0 or type(reserve) is not int or not 0 <= reserve < wall:
        raise ValueError('Invalid original wall duration or cleanup reserve')
    budget_clock.validate(value['clock'], wall)


def validate_configuration(value):
    """Validate the explicit machine-local configuration without querying GPUs."""
    _fields(value, _CONFIG_FIELDS, 'GPU pool configuration')
    _version(value, 'local-gpu-pool-config')
    if not isinstance(value['pool_id'], str) or not value['pool_id']:
        raise ValueError('GPU pool requires an explicit pool identity')
    if value['mode'] != 'trusted-cooperating-local':
        raise ValueError('Unsupported GPU pool deployment mode')
    directory = _absolute(value['coordination_directory'])
    sentinel = _absolute(value['legacy_sentinel'])
    if sentinel == directory:
        raise ValueError('Legacy sentinel cannot be the session coordination directory')
    _devices(value['device_uuids'])
    return value


def _devices(values, universe=None):
    if (not isinstance(values, list) or not values
            or any(not isinstance(value, str) or re.fullmatch('GPU-[A-Za-z0-9-]+', value) is None for value in values)
            or len(set(values)) != len(values)):
        raise ValueError('GPU requests require distinct full physical GPU UUIDs')
    if universe is not None and not set(values) <= set(universe):
        raise ValueError('GPU request is outside the configured device universe')


def guard_source_sha256():
    """Bind the installed cooperating guard and the actual shared reaper source."""
    directory = Path(__file__).parent
    return _sha([{'name': name, 'raw_sha256': hashlib.sha256(_read(directory / name)).hexdigest()}
                 for name in ('gpu_guard.py', 'processes.py')])


def _lease_id(request_id):
    return _sha({'kind': 'local-gpu-child-lease-v1', 'request_id': _digest(request_id)})


def inventory_observation():
    """Observe each real NVML operation; mandatory errors never mean no processes."""
    operations = {}
    result = {'available': False, 'operations': operations, 'devices': [], 'errors': []}

    def failed(name, error):
        detail = {'status': 'unavailable', 'error': type(error).__name__, 'detail': str(error)}
        operations[name] = detail
        result['errors'].append({'operation': name, **detail})

    try:
        import pynvml as nvml
    except ImportError as error:
        failed('import', error)
        for name in ('init', 'uuid', 'mig-mode', 'compute', 'graphics', 'memory-v2', 'shutdown'):
            operations[name] = {'status': 'unavailable', 'detail': 'NVML import unavailable'}
        return result
    operations['import'] = {'status': 'available'}
    try:
        nvml.nvmlInit()
    except Exception as error:
        failed('init', error)
        for name in ('uuid', 'mig-mode', 'compute', 'graphics', 'memory-v2', 'shutdown'):
            operations[name] = {'status': 'unavailable', 'detail': 'NVML initialization unavailable'}
        return result
    operations['init'] = {'status': 'available'}
    for name in ('uuid', 'mig-mode', 'compute', 'graphics', 'memory-v2'):
        operations[name] = {'status': 'unavailable', 'detail': 'Operation not observed'}

    def succeeded(name):
        if 'error' not in operations[name]:
            operations[name] = {'status': 'available'}
    try:
        count = nvml.nvmlDeviceGetCount()
        if type(count) is not int or count < 1:
            raise ValueError('NVML returned no supported physical device inventory')
        for index in range(count):
            handle = nvml.nvmlDeviceGetHandleByIndex(index)
            row = {'index': index}
            try:
                identifier = nvml.nvmlDeviceGetUUID(handle)
                identifier = identifier.decode('ascii') if isinstance(identifier, bytes) else identifier
                _devices([identifier])
                row['uuid'] = identifier
                succeeded('uuid')
            except Exception as error:
                failed('uuid', error)
            try:
                modes = nvml.nvmlDeviceGetMigMode(handle)
                if (not isinstance(modes, (tuple, list)) or len(modes) != 2
                        or any(type(mode) is not int or mode not in (0, 1) for mode in modes)):
                    raise ValueError('Unsupported NVML MIG mode result')
                row['mig_mode'] = {'status': 'available', 'current': modes[0], 'pending': modes[1]}
                if any(modes):
                    raise ValueError('MIG-enabled or pending-MIG devices are unsupported by local GPU admission')
                succeeded('mig-mode')
            except Exception as error:
                unsupported = getattr(nvml, 'NVMLError_NotSupported', None)
                if unsupported is not None and isinstance(error, unsupported):
                    row['mig_mode'] = {'status': 'unsupported', 'detail': 'Physical device reports MIG unsupported'}
                    if operations['mig-mode']['status'] != 'available' and 'error' not in operations['mig-mode']:
                        operations['mig-mode'] = {'status': 'unsupported', 'detail': 'Physical devices report MIG unsupported'}
                else:
                    failed('mig-mode', error)
                    row['mig_mode'] = {'status': 'unavailable', 'error': type(error).__name__, 'detail': str(error)}
            for name, operation in (('compute', nvml.nvmlDeviceGetComputeRunningProcesses),
                                    ('graphics', nvml.nvmlDeviceGetGraphicsRunningProcesses)):
                try:
                    observed = operation(handle)
                    if not isinstance(observed, (list, tuple)):
                        raise ValueError('Unsupported NVML process result')
                    pids = [item.pid for item in observed]
                    if any(type(pid) is not int or pid < 1 for pid in pids):
                        raise ValueError('Unsupported NVML process identity')
                    row[name + '_pids'] = sorted(set(pids))
                    succeeded(name)
                except Exception as error:
                    failed(name, error)
            try:
                memory = nvml.nvmlDeviceGetMemoryInfo(handle, version=nvml.nvmlMemory_v2)
                if type(memory.used) is not int or type(memory.reserved) is not int:
                    raise ValueError('Unsupported NVML memory-v2 result')
                row['memory'] = {'available': True, 'used_bytes': memory.used, 'reserved_bytes': memory.reserved}
                succeeded('memory-v2')
            except Exception as error:
                failed('memory-v2', error)
                row['memory'] = {'available': False, 'error': type(error).__name__, 'detail': str(error)}
            result['devices'].append(row)
    except Exception as error:
        failed('uuid', error)
    finally:
        try:
            nvml.nvmlShutdown()
            operations['shutdown'] = {'status': 'available'}
        except Exception as error:
            failed('shutdown', error)
    try:
        _validate_inventory(result['devices'])
    except (ValueError, TypeError, KeyError) as error:
        failed('uuid', error)
    result['available'] = all(operations.get(name, {}).get('status') == 'available'
                              for name in ('import', 'init', 'uuid', 'compute', 'graphics', 'shutdown')) and (
                                  operations['mig-mode']['status'] in {'available', 'unsupported'})
    return result


def inventory():
    """Return full real device rows, or fail visibly on any mandatory query error."""
    result = inventory_observation()
    if not result['available']:
        raise PoolUnavailable('Mandatory NVML operations unavailable: ' + _encode(result['errors']).decode())
    return result['devices']


def _validate_inventory(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('GPU inventory must contain physical device observations')
    identifiers = []
    indices = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Unsupported GPU inventory row')
        _devices([row['uuid']])
        if type(row['index']) is not int or row['index'] < 0:
            raise ValueError('Unsupported GPU inventory index')
        identifiers.append(row['uuid'])
        indices.append(row['index'])
        for name in ('compute_pids', 'graphics_pids'):
            if not isinstance(row[name], list) or any(type(pid) is not int or pid < 1 for pid in row[name]):
                raise ValueError('Mandatory GPU process observation is unavailable')
        if 'mig_mode' in row:
            mode = row['mig_mode']
            if (not isinstance(mode, dict) or mode.get('status') not in {'available', 'unsupported'}
                    or mode['status'] == 'available' and (mode.get('current') != 0 or mode.get('pending') != 0)):
                raise ValueError('MIG deployment is unsupported or could not be observed')
    if len(set(identifiers)) != len(identifiers) or len(set(indices)) != len(indices):
        raise ValueError('GPU inventory has duplicate device identities')


def _kernel_observation():
    operations = {}
    for name, operation in (
            ('linux-identity', _identity),
            ('proc-children', lambda: _children(_identity())),
            ('socket-peer-credentials', _socket_observation),
            ('subreaper', _subreaper_observation)):
        try:
            if sys.platform != 'linux':
                raise ValueError('Local GPU admission supports Linux only')
            operation()
            operations[name] = {'status': 'available'}
        except Exception as error:
            operations[name] = {'status': 'unsupported' if sys.platform != 'linux' else 'unavailable',
                                'error': type(error).__name__, 'detail': str(error)}
    return operations


def _socket_observation():
    first, second = socket.socketpair()
    try:
        if _peer(first) != _identity() or _peer(second) != _identity():
            raise ValueError('Kernel socket peer identity is unavailable')
    finally:
        first.close()
        second.close()


def _subreaper_observation():
    enabled = ctypes.c_int()
    if ctypes.CDLL(None, use_errno=True).prctl(37, ctypes.byref(enabled), 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'Cannot inspect Linux subreaper capability')


def _descriptor(value, session_id):
    _fields(value, {'schema_version', 'kind', 'session_id', 'pool_id', 'config_sha256',
                    'ordered_device_uuids', 'created_at', 'initial_owner'}, 'session descriptor')
    _version(value, 'ergora-local-gpu-session')
    _process_identity(value['initial_owner'])
    _digest(value['config_sha256'])
    _devices(value['ordered_device_uuids'])
    if (value['session_id'] != session_id or not isinstance(value['pool_id'], str) or not value['pool_id']):
        raise ValueError('GPU pool immutable descriptor binding differs')
    _timestamp(value['created_at'])


def _match_configuration(session, configuration):
    if session['config_sha256'] != _sha(configuration):
        raise ValueError('GPU pool configuration differs from its original session')
    if (session['pool_id'] != configuration['pool_id']
            or session['ordered_device_uuids'] != configuration['device_uuids']):
        raise ValueError('GPU pool immutable descriptor binding differs')


def _archived_session_records(configuration, session_id):
    directory = Path(configuration['coordination_directory']) / 'sessions' / _session_id(session_id)
    descriptor_raw = _read(directory / 'session-descriptor.json')
    descriptor = _decode(descriptor_raw)
    _descriptor(descriptor, session_id)
    _match_configuration(descriptor, configuration)
    session_raw = _read(directory / 'session.json')
    session_record = _decode(session_raw)
    _fields(session_record, {*descriptor, 'legacy_sentinel_binding'}, 'immutable closed session')
    binding = session_record['legacy_sentinel_binding']
    _fields(binding, {'dev', 'ino', 'raw_sha256'}, 'original sentinel binding')
    if (type(binding['dev']) is not int or binding['dev'] < 0
            or type(binding['ino']) is not int or binding['ino'] < 1
            or {name: session_record[name] for name in descriptor} != descriptor):
        raise ValueError('Invalid original closed session descriptor or inode binding')
    _digest(binding['raw_sha256'])
    sentinel_record = {'schema_version': 1, 'kind': 'ergora-local-gpu-session', 'session_id': session_id,
                       'config_sha256': descriptor['config_sha256'], 'boot_id': descriptor['initial_owner']['boot_id'],
                       'initial_owner': descriptor['initial_owner'],
                       'session_record_sha256': hashlib.sha256(descriptor_raw).hexdigest()}
    sentinel_raw = _encode(sentinel_record) + b'\n'
    if hashlib.sha256(sentinel_raw).hexdigest() != binding['raw_sha256']:
        raise ValueError('Original closed session sentinel raw identity differs')
    return directory, session_record, session_raw, descriptor_raw, sentinel_raw


def _closed_session_without_sentinel(configuration, session_id):
    """Recognize the original closed session when finishing directory sync."""
    records = _archived_session_records(configuration, session_id)
    directory, session_record = records[:2]
    original = _journal(_read(directory / 'journal.json'), session_record)
    if original['mode'] != 'closed' or any(item['state'] not in _TERMINAL for item in original['requests']):
        raise PoolUnavailable('Missing sentinel does not prove an open or unknown session closed')
    if Path(configuration['legacy_sentinel']).exists() or Path(configuration['legacy_sentinel']).is_symlink():
        raise PoolUnavailable('A legacy sentinel appeared during original closed-session observation')
    return records


def _session_from_sentinel(coordination, raw, binding, expected_id=None):
    record = _decode(raw)
    _fields(record, {'schema_version', 'kind', 'session_id', 'config_sha256', 'boot_id',
                     'initial_owner', 'session_record_sha256'}, 'session sentinel')
    _version(record, 'ergora-local-gpu-session')
    identity = _session_id(record['session_id'])
    if expected_id is not None and identity != expected_id:
        raise ValueError('Original GPU pool session identity differs')
    _digest(record['config_sha256'])
    _process_identity(record['initial_owner'])
    if record['boot_id'] != record['initial_owner']['boot_id']:
        raise ValueError('GPU pool sentinel boot identity differs')
    directory = Path(coordination) / 'sessions' / identity
    descriptor_raw, _ = _read_bound(directory / 'session-descriptor.json')
    if hashlib.sha256(descriptor_raw).hexdigest() != record['session_record_sha256']:
        raise ValueError('GPU pool immutable descriptor differs from its sentinel')
    descriptor = _decode(descriptor_raw)
    _descriptor(descriptor, identity)
    if (descriptor['initial_owner'] != record['initial_owner']
            or descriptor['config_sha256'] != record['config_sha256']):
        raise ValueError('GPU pool immutable descriptor binding differs')
    session_raw, _ = _read_bound(directory / 'session.json')
    session_record = _decode(session_raw)
    _fields(session_record, {*descriptor, 'legacy_sentinel_binding'}, 'immutable session')
    if session_record != dict(descriptor, legacy_sentinel_binding=binding):
        raise ValueError('GPU pool sentinel inode or raw contents differ')
    return directory, session_record, session_raw, descriptor_raw, raw


def _load_session(configuration, expected_id=None, *, closed_missing=False):
    sentinel = Path(configuration['legacy_sentinel'])
    try:
        raw, binding = _read_bound(sentinel, FRAME_LIMIT)
    except FileNotFoundError:
        if not closed_missing or expected_id is None:
            raise
        return _closed_session_without_sentinel(configuration, expected_id)
    original = _session_from_sentinel(configuration['coordination_directory'], raw, binding, expected_id)
    _match_configuration(original[1], configuration)
    return original


def _journal(raw, session_record):
    value = _decode(raw)
    _fields(value, {'schema_version', 'kind', 'session_id', 'config_sha256', 'sequence',
                    'owner_epoch', 'current_owner', 'mode', 'requests'}, 'GPU resource journal')
    _version(value, 'ergora-local-gpu-journal')
    if (value['session_id'] != session_record['session_id']
            or value['config_sha256'] != session_record['config_sha256']
            or type(value['sequence']) is not int or value['sequence'] < 0
            or type(value['owner_epoch']) is not int or value['owner_epoch'] < 1
            or value['mode'] not in {'active', 'draining', 'recovering', 'unknown', 'closed'}
            or not isinstance(value['requests'], list)):
        raise ValueError('Invalid GPU resource journal identity or state')
    _process_identity(value['current_owner'])
    seen, attempts, leases, enqueue = set(), set(), set(), set()
    for request in value['requests']:
        _fields(request, _REQUEST_FIELDS, 'persisted GPU request')
        _digest(request['request_id'])
        _digest(request['request_sha256'])
        _origin(request['origin'])
        _devices(request['ordered_device_uuids'], session_record['ordered_device_uuids'])
        _proof_reference(request['guard_ready_ref'], request['lease_id'], 'ready')
        if (request['lease_id'] != _lease_id(request['request_id'])
                or request['state'] not in _RESERVED | _TERMINAL | {'pending'}
                or type(request['enqueue_sequence']) is not int or request['enqueue_sequence'] < 1
                or request['enqueue_sequence'] > value['sequence']
                or request['request_id'] in seen or request['lease_id'] in leases
                or request['origin']['attempt_ref']['raw_sha256'] in attempts
                or request['enqueue_sequence'] in enqueue
                or not isinstance(request['reason'], str)):
            raise ValueError('Conflicting persisted GPU request identity')
        if request['request_sha256'] != _sha({name: request[name] for name in (
                'request_id', 'origin', 'ordered_device_uuids', 'guard_ready_ref')}):
            raise ValueError('Persisted GPU request content differs from its immutable identity')
        consume = request['consume_binding']
        if consume is not None:
            _fields(consume, {'owner_epoch', 'sequence', 'lease_id', 'request_sha256',
                             'guard_identity', 'guard_ready_raw_sha256'}, 'resource consume binding')
            _process_identity(consume['guard_identity'])
            if (type(consume['owner_epoch']) is not int or not 1 <= consume['owner_epoch'] <= value['owner_epoch']
                    or type(consume['sequence']) is not int or not 1 <= consume['sequence'] <= value['sequence']
                    or consume['lease_id'] != request['lease_id']
                    or consume['request_sha256'] != request['request_sha256']
                    or consume['guard_ready_raw_sha256'] != request['guard_ready_ref']['raw_sha256']):
                raise ValueError('Invalid persisted consume binding')
        if request['state'] == 'consumed' and consume is None:
            raise ValueError('Consumed resource has no original consume binding')
        if request['state'] in {'pending', 'cancelled', 'expired'} and consume is not None:
            raise ValueError('Unconsumed request contains a consume binding')
        if request['release_ref'] is not None:
            _fields(request['release_ref'], {'proof_ref', 'guard_identity', 'proc_children',
                                            'nvml_observation', 'nvml_sha256', 'sequence'}, 'release reference')
            release = request['release_ref']
            _proof_reference(release['proof_ref'], request['lease_id'], 'stopped')
            _process_identity(release['guard_identity'])
            if (release['proc_children'] != [] or release['nvml_sha256'] != _sha(release['nvml_observation'])
                    or type(release['sequence']) is not int or not 1 <= release['sequence'] <= value['sequence']
                    or request['state'] != 'released'):
                raise ValueError('Invalid persisted release acceptance')
        elif request['state'] == 'released':
            raise ValueError('Released resource has no accepted original proof')
        seen.add(request['request_id'])
        leases.add(request['lease_id'])
        attempts.add(request['origin']['attempt_ref']['raw_sha256'])
        enqueue.add(request['enqueue_sequence'])
    return value


def _proof_reference(value, lease_id, name):
    _fields(value, {'relative_path', 'raw_sha256'}, 'guard proof reference')
    _digest(lease_id)
    _digest(value['raw_sha256'])
    if value['relative_path'] != 'proofs/' + lease_id + '/' + name + '.json':
        raise ValueError('Guard proof must use its fixed original session/lease path')


def _read_proof(directory, reference, lease_id, name):
    _proof_reference(reference, lease_id, name)
    raw, binding = _read_bound(directory / reference['relative_path'], FRAME_LIMIT)
    if binding['raw_sha256'] != reference['raw_sha256']:
        raise ValueError('Original GPU guard proof raw identity changed')
    return _decode(raw), binding


def _stopped_proof(directory, reference, session_id, request, guard_identity):
    proof, binding = _read_proof(directory, reference, request['lease_id'], 'stopped')
    _fields(proof, _STOPPED_FIELDS, 'GPU guard stopped proof')
    _version(proof, STOPPED_KIND)
    _timestamp(proof['reaped_at'])
    result = proof['process_result']
    _fields(result, {'status', 'returncode', 'output'}, 'original process result')
    if (result['status'] not in {'succeeded', 'failed', 'timed_out', 'cancelled'}
            or result['returncode'] is not None and type(result['returncode']) is not int
            or not isinstance(result['output'], str)):
        raise ValueError('Unsupported original process result')
    consume = request['consume_binding']
    if (proof['session_id'] != session_id or proof['lease_id'] != request['lease_id']
            or proof['request_sha256'] != request['request_sha256']
            or proof['consume_binding_sha256'] != (_sha(consume) if consume is not None else None)
            or proof['guard_identity'] != guard_identity or proof['origin_sha256'] != _sha(request['origin'])
            or proof['spawn_closed'] is not True):
        raise ValueError('Stopped proof differs from the original guard/consume/origin')
    return binding


def observe_closed_release(configuration, session_id, lease_id):
    """Read one original release from a closed journal without a current owner."""
    validate_configuration(configuration)
    _digest(lease_id)
    records = _archived_session_records(configuration, session_id)
    directory, session_record = records[:2]
    journal_path = directory / 'journal.json'
    raw, binding = _read_bound(journal_path)
    journal = _journal(raw, session_record)
    if journal['mode'] != 'closed' or any(item['state'] not in _TERMINAL for item in journal['requests']):
        raise PoolUnavailable('Original GPU resource journal is not closed')
    request = next((item for item in journal['requests'] if item['lease_id'] == lease_id), None)
    if request is None:
        raise ValueError('Unknown original GPU resource lease')
    if request['state'] != 'released':
        raise PoolUnavailable('Original GPU resource lease has no accepted release')

    release = request['release_ref']
    consume = request['consume_binding']
    if (release['sequence'] <= request['enqueue_sequence'] or consume is not None and
            (release['sequence'] <= consume['sequence'] or release['guard_identity'] != consume['guard_identity'])):
        raise ValueError('Accepted GPU release differs from its original lease order or guard')
    rows = release['nvml_observation']
    try:
        _validate_inventory(rows)
    except (TypeError, KeyError) as error:
        raise ValueError('Accepted GPU release has invalid original device observations') from error
    if ([row['uuid'] for row in rows] != request['ordered_device_uuids']
            or any(row['compute_pids'] or row['graphics_pids'] for row in rows)):
        raise ValueError('Accepted GPU release lacks empty observations for its assigned devices')
    proof_binding = _stopped_proof(directory, release['proof_ref'], session_id, request, release['guard_identity'])
    try:
        current_raw, current_binding = _read_bound(configuration['legacy_sentinel'], FRAME_LIMIT)
    except FileNotFoundError:
        pass
    else:
        _, current, *_ = _session_from_sentinel(configuration['coordination_directory'], current_raw, current_binding)
        if current['session_id'] == session_id:
            raise PoolUnavailable('Original GPU resource session still owns the original sentinel')
    if _archived_session_records(configuration, session_id) != records:
        raise ValueError('Original closed GPU session changed during observation')
    if _read_proof(directory, release['proof_ref'], lease_id, 'stopped')[1] != proof_binding:
        raise ValueError('Original stopped proof inode changed during observation')
    if _read_bound(journal_path) != (raw, binding):
        raise ValueError('Original closed GPU journal changed during observation')
    return {'status': 'released', 'mode': 'closed', 'session_id': session_id, 'lease_id': lease_id,
            'request_id': request['request_id'], 'request_sha256': request['request_sha256'],
            'attempt_sha256': request['origin']['attempt_ref']['raw_sha256'], 'release_ref': release}


class LocalGpuPool:
    """Client bound to an existing immutable session; connect never creates it."""

    def __init__(self, configuration):
        self.configuration = validate_configuration(configuration)
        self.coordination_directory = Path(configuration['coordination_directory'])
        self.directory, self.session, self._session_raw, self._descriptor_raw, self._sentinel_raw = _load_session(configuration)
        self.current_owner = None
        self.owner_epoch = None
        self._owner()

    @classmethod
    def connect(cls, configuration):
        return cls(configuration)

    def _owner(self):
        directory, session_record, session_raw, descriptor_raw, sentinel_raw = _load_session(
            self.configuration, self.session['session_id'], closed_missing=True)
        if (directory != self.directory or session_raw != self._session_raw
                or descriptor_raw != self._descriptor_raw or sentinel_raw != self._sentinel_raw
                or session_record != self.session):
            raise ValueError('Original GPU pool immutable records changed')
        # The mutable snapshot only routes to an owner; the bound peer and server
        # retain authority over the current resource state.
        raw, _ = _read_snapshot(self.directory / 'journal.json')
        journal = _journal(raw, self.session)
        if processes.identity(journal['current_owner']['pid']) != journal['current_owner']:
            raise PoolUnavailable('Original GPU resource owner is unavailable; explicit recovery is required')
        self.current_owner, self.owner_epoch = journal['current_owner'], journal['owner_epoch']
        return journal

    def request_identity(self, origin, ordered_device_uuids, guard_identity, input_sha256):
        _origin(origin)
        _devices(ordered_device_uuids, self.configuration['device_uuids'])
        _process_identity(guard_identity)
        request_id = _sha({'session_id': self.session['session_id'], 'origin_sha256': _sha(origin),
                           'ordered_device_uuids': ordered_device_uuids, 'guard_identity': guard_identity,
                           'input_sha256': _digest(input_sha256)})
        return request_id, _lease_id(request_id)

    def proof_directory(self, lease_id):
        path = self.directory / 'proofs' / _digest(lease_id)
        _ordinary(path)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        _sync(path.parent)
        return path

    @contextmanager
    def channel(self, timeout=1.0):
        journal = self._owner()
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.set_inheritable(False)
        connection.settimeout(min(_IO_SECONDS, timeout))
        try:
            connection.connect(str(self.coordination_directory / 'session.sock'))
            if _peer(connection) != journal['current_owner']:
                raise ValueError('GPU pool channel differs from its current journal owner')
            yield connection
        finally:
            connection.close()

    def call(self, action, body=None):
        with self.channel() as connection:
            epoch = self.owner_epoch
            _send(connection, {'protocol': PROTOCOL, 'session_id': self.session['session_id'],
                               'action': action, 'body': body})
            result = _receive(connection)
        if (not isinstance(result, dict) or result.get('session_id') != self.session['session_id']
                or result.get('owner_epoch') != epoch):
            raise ValueError('GPU pool reply belongs to another session')
        return result

    def inspect(self):
        return self.call('inspect')

    def request(self, request):
        return self.call('request', request)

    def cancel(self, request_id, origin):
        return self.call('cancel', {'request_id': request_id, 'origin': origin})

    def release(self, lease_id, proof_ref):
        return self.call('release', {'lease_id': lease_id, 'proof_ref': proof_ref})

    def reconcile(self, lease_id):
        return self.call('reconcile', {'lease_id': lease_id})

    def close(self):
        return self.call('close')


class _Session:
    """One owner, one lifetime flock, and serial in-process resource transactions."""

    def __init__(self, configuration, lock_descriptor, recover, inventory_provider):
        self.configuration = configuration
        self.coordination = Path(configuration['coordination_directory'])
        self.sentinel = Path(configuration['legacy_sentinel'])
        self.lock_descriptor = lock_descriptor
        self.lock_stat = os.fstat(lock_descriptor)
        self.provider = inventory_provider
        self.guards = {}
        self.fatal = None
        self.uncertain = None
        self.finished = False
        self.selector = None
        self.listener = None
        self.socket_stat = None
        self.connections = set()
        self.last_inventory = None
        self.kernel = _kernel_observation()
        if any(item['status'] != 'available' for item in self.kernel.values()):
            raise PoolUnavailable('Mandatory Linux resource interfaces are unavailable: ' + _encode(self.kernel).decode())
        self.selector = selectors.DefaultSelector()
        try:
            if recover is None:
                self._create()
            else:
                self._recover(_session_id(recover))
        except BaseException:
            self.selector.close()
            raise

    def _create(self):
        # This read is diagnostic only; O_EXCL below is the ownership decision.
        if self.sentinel.exists() or self.sentinel.is_symlink():
            raw, binding = _read_bound(self.sentinel, FRAME_LIMIT)
            raise PoolUnavailable('external_or_unknown: existing legacy sentinel retained; binding=' + _encode(binding).decode())
        identity = _identity()
        session_id = uuid.uuid4().hex
        self.directory = self.coordination / 'sessions' / session_id
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        _sync(self.directory.parent)
        descriptor = {'schema_version': 1, 'kind': 'ergora-local-gpu-session', 'session_id': session_id,
                      'pool_id': self.configuration['pool_id'], 'config_sha256': _sha(self.configuration),
                      'ordered_device_uuids': self.configuration['device_uuids'], 'created_at': _now(),
                      'initial_owner': identity}
        self.descriptor_raw = _publish(self.directory / 'session-descriptor.json', descriptor)
        self.journal = {'schema_version': 1, 'kind': 'ergora-local-gpu-journal', 'session_id': session_id,
                        'config_sha256': _sha(self.configuration), 'sequence': 0, 'owner_epoch': 1,
                        'current_owner': identity, 'mode': 'active', 'requests': []}
        self.journal_raw = _publish(self.directory / 'journal.json', self.journal)
        sentinel_record = {'schema_version': 1, 'kind': 'ergora-local-gpu-session', 'session_id': session_id,
                           'config_sha256': _sha(self.configuration), 'boot_id': identity['boot_id'],
                           'initial_owner': identity,
                           'session_record_sha256': hashlib.sha256(self.descriptor_raw).hexdigest()}
        raw = _encode(sentinel_record) + b'\n'
        try:
            descriptor_fd = os.open(self.sentinel, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError as error:
            raise PoolUnavailable('external_or_unknown: legacy writer won exclusive sentinel creation') from error
        # Never remove a partially published sentinel, even if a later step fails.
        with os.fdopen(descriptor_fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _sync(self.sentinel.parent)
        self.sentinel_raw, binding = _read_bound(self.sentinel, FRAME_LIMIT)
        if self.sentinel_raw != raw:
            raise PoolUnavailable('GPU session sentinel changed during initial publication')
        self.session = dict(descriptor, legacy_sentinel_binding=binding)
        self.session_raw = _publish(self.directory / 'session.json', self.session)
        _sync(self.coordination)
        self._ensure()

    def _recover(self, session_id):
        (self.directory, self.session, self.session_raw, self.descriptor_raw,
         self.sentinel_raw) = _load_session(self.configuration, session_id, closed_missing=True)
        if _identity()['boot_id'] != self.session['initial_owner']['boot_id']:
            raise PoolUnavailable('Cross-boot GPU resource recovery is unsupported; original fence retained')
        self.journal_raw = _read(self.directory / 'journal.json')
        self.journal = _journal(self.journal_raw, self.session)
        # The lifetime flock has already excluded any still-owning session.
        if self.journal['current_owner'] == _identity():
            raise PoolUnavailable('Recovery requires a distinct original owner lifetime')
        _sync(self.directory)
        if _read(self.directory / 'journal.json') != self.journal_raw:
            raise PoolUnavailable('Original journal changed during durable recovery readback')
        updated = _decode(_encode(self.journal))
        updated['owner_epoch'] += 1
        updated['current_owner'] = _identity()
        if updated['mode'] != 'closed':
            updated['mode'] = 'recovering'
            for request in updated['requests']:
                if request['state'] == 'pending':
                    request['state'], request['reason'] = 'cancelled', 'session_recovery_no_consume'
                elif request['state'] in _RESERVED:
                    request['state'], request['reason'] = 'unknown', 'original_guard_reconciliation_required'
        self._commit(updated, recovering=True)
        if self.journal['mode'] == 'closed':
            self._complete_close()
        elif not any(item['state'] in _RESERVED for item in self.journal['requests']):
            updated = _decode(_encode(self.journal))
            updated['mode'] = 'active'
            self._commit(updated)

    def _ensure(self, *, allow_closed=False, recovery=False):
        if self.fatal is not None:
            raise PoolUnavailable(self.fatal)
        try:
            _ordinary(self.coordination / 'pool.lock')
            lock_stat = (self.coordination / 'pool.lock').stat(follow_symlinks=False)
            if (lock_stat.st_dev, lock_stat.st_ino) != (self.lock_stat.st_dev, self.lock_stat.st_ino):
                raise ValueError('Lifetime GPU pool lock inode changed')
            directory, record, session_raw, descriptor_raw, sentinel_raw = _load_session(
                self.configuration, self.session['session_id'],
                closed_missing=allow_closed and self.journal['mode'] == 'closed')
            if (directory != self.directory or record != self.session or session_raw != self.session_raw
                    or descriptor_raw != self.descriptor_raw or sentinel_raw != self.sentinel_raw):
                raise ValueError('Original GPU pool immutable record changed')
            raw = _read(self.directory / 'journal.json')
            if self.uncertain is not None and raw == self.uncertain:
                _sync(self.directory)
                if _read(self.directory / 'journal.json') != raw:
                    raise ValueError('Uncertain journal changed during durable readback')
                self.journal = _journal(raw, self.session)
                self.journal_raw, self.uncertain = raw, None
            elif raw != self.journal_raw:
                raise ValueError('GPU journal changed outside its sole resource owner')
            if not recovery and self.journal['current_owner'] != _identity():
                raise ValueError('GPU journal current owner changed')
            if self.journal['mode'] == 'closed' and not allow_closed:
                raise PoolUnavailable('Original GPU resource session is closed')
            if _identity()['boot_id'] != self.session['initial_owner']['boot_id']:
                raise ValueError('GPU resource session boot identity changed')
        except PoolUnavailable:
            raise
        except (ValueError, OSError, KeyError, TypeError) as error:
            self.fatal = 'unknown: ' + str(error)
            raise PoolUnavailable(self.fatal) from error

    def _commit(self, updated, *, recovering=False):
        self._ensure(allow_closed=True, recovery=recovering)
        updated['sequence'] = self.journal['sequence'] + 1
        raw = _encode(updated) + b'\n'
        if len(raw) > JOURNAL_LIMIT:
            raise ValueError('GPU resource journal capacity exceeded; original requests retained')
        _journal(raw, self.session)
        try:
            published = _publish(self.directory / 'journal.json', updated, replace=True)
        except (OSError, ValueError) as error:
            # Replace may already be visible. Retain its exact candidate identity;
            # a later original-ID observation must fsync/read it before using it.
            self.uncertain = raw
            raise PoolUnavailable('GPU journal commit acknowledgement unavailable: ' + str(error)) from error
        self.journal, self.journal_raw, self.uncertain = updated, published, None

    def _inventory(self):
        if self.provider is None:
            observation = inventory_observation()
        else:
            # In-process replacement seam for CPU tests, never a config importer.
            try:
                rows = self.provider()
                _validate_inventory(rows)
                observation = {'available': True, 'operations': {'provider': {'status': 'available'}},
                               'devices': rows, 'errors': []}
            except Exception as error:
                observation = {'available': False, 'operations': {'provider': {'status': 'unavailable',
                               'error': type(error).__name__, 'detail': str(error)}}, 'devices': [],
                               'errors': [{'error': type(error).__name__, 'detail': str(error)}]}
        if observation['available']:
            found = {item['uuid'] for item in observation['devices']}
            missing = set(self.configuration['device_uuids']) - found
            if missing:
                observation['available'] = False
                observation['errors'].append({'operation': 'configured-uuid-lookup',
                                             'detail': 'Configured full UUID missing from actual inventory',
                                             'missing': sorted(missing)})
        return observation

    def _reply(self, status, *, request=None, reason='', **fields):
        result = {'session_id': self.session['session_id'], 'status': status,
                  'sequence': self.journal['sequence'], 'owner_epoch': self.journal['owner_epoch'],
                  'reason': reason, **fields}
        if request is not None:
            result.update({name: request[name] for name in ('request_id', 'request_sha256', 'lease_id',
                           'ordered_device_uuids', 'consume_binding', 'release_ref')})
            result['consume_binding_sha256'] = _sha(request['consume_binding']) if request['consume_binding'] is not None else None
        return result

    def _find(self, request_id=None, lease_id=None):
        for request in self.journal['requests']:
            if (request_id is not None and request['request_id'] == request_id
                    or lease_id is not None and request['lease_id'] == lease_id):
                return request
        raise ValueError('Unknown original GPU resource request or lease')

    def _ready(self, request_id, reference, peer):
        lease_id = _lease_id(request_id)
        proof, binding = _read_proof(self.directory, reference, lease_id, 'ready')
        _fields(proof, _READY_FIELDS, 'GPU guard ready proof')
        _version(proof, READY_KIND)
        for key in ('input_sha256', 'origin_sha256', 'command_sha256', 'guard_source_sha256'):
            _digest(proof[key])
        _process_identity(proof['owner_identity'])
        _process_identity(proof['guard_identity'])
        _timestamp(proof['ready_at'])
        _devices(proof['ordered_device_uuids'], self.configuration['device_uuids'])
        if (proof['session_id'] != self.session['session_id'] or proof['request_id'] != request_id
                or proof['guard_identity'] != peer or processes.identity(peer['pid']) != peer
                or proof['prepared_subreaper'] is not True
                or proof['guard_source_sha256'] != guard_source_sha256()):
            raise ValueError('GPU ready proof lacks its original live prepared guard binding')
        existing = next((item for item in self.journal['requests'] if item['request_id'] == request_id), None)
        if (existing is None or existing['state'] == 'pending') and _children(peer):
            raise ValueError('GPU guard is not initially child-free')
        return proof, binding

    def _guard_ready(self, body, connection):
        _fields(body, {'request_id', 'ready_ref'}, 'guard ready message')
        request_id = _digest(body['request_id'])
        proof, binding = self._ready(request_id, body['ready_ref'], connection.peer)
        previous = self.guards.get(request_id)
        if previous is not None and previous is not connection:
            raise ValueError('Original GPU guard already has a live bound channel')
        if connection.request_id is not None and connection.request_id != request_id:
            raise ValueError('One dedicated GPU guard cannot bind another request')
        for request in self.journal['requests']:
            if request['request_id'] == request_id and request['guard_ready_ref'] != body['ready_ref']:
                raise ValueError('Guard ready reference differs from original request')
        connection.request_id, connection.ready, connection.ready_binding = request_id, proof, binding
        connection.ready_ref = body['ready_ref']
        self.guards[request_id] = connection
        return self._reply('pending', reason='guard_ready_bound', request_id=request_id,
                           lease_id=_lease_id(request_id), mode=self.journal['mode'])

    def _bound_guard(self, request, connection=None, *, initial=False):
        guard = self.guards.get(request['request_id'])
        if guard is None or (connection is not None and connection is not guard):
            raise ValueError('Original live GPU guard channel is unavailable')
        if _peer(guard.socket) != guard.peer or processes.identity(guard.peer['pid']) != guard.peer:
            raise ValueError('Original live GPU guard peer identity changed')
        proof, binding = _read_proof(self.directory, request['guard_ready_ref'], request['lease_id'], 'ready')
        if (binding != guard.ready_binding or proof != guard.ready
                or proof['origin_sha256'] != _sha(request['origin'])
                or proof['owner_identity'] != request['origin']['owner_identity']
                or proof['ordered_device_uuids'] != request['ordered_device_uuids']
                or proof['guard_source_sha256'] != guard_source_sha256()):
            raise ValueError('Original GPU guard/request/source binding differs')
        expected = _sha({'session_id': self.session['session_id'], 'origin_sha256': _sha(request['origin']),
                         'ordered_device_uuids': request['ordered_device_uuids'], 'guard_identity': guard.peer,
                         'input_sha256': proof['input_sha256']})
        if expected != request['request_id']:
            raise ValueError('Original GPU request digest differs from its guard binding')
        if initial and _children(guard.peer):
            raise ValueError('GPU guard already has children before admission')
        return guard

    def _request(self, body):
        _fields(body, {'request_id', 'origin', 'ordered_device_uuids', 'guard_ready_ref'}, 'GPU resource request')
        _digest(body['request_id'])
        _origin(body['origin'])
        _devices(body['ordered_device_uuids'], self.configuration['device_uuids'])
        lease_id = _lease_id(body['request_id'])
        _proof_reference(body['guard_ready_ref'], lease_id, 'ready')
        request_sha256 = _sha(body)
        # An original attempt cannot acquire a second opportunity by changing ready,
        # devices, source, clock, or operation metadata after an uncertain reply.
        for original in self.journal['requests']:
            if (original['request_id'] == body['request_id']
                    or original['origin']['attempt_ref']['raw_sha256'] == body['origin']['attempt_ref']['raw_sha256']):
                if original['request_sha256'] != request_sha256:
                    return self._reply('rejected', request=original, reason='original_attempt_or_request_conflict')
                self._admit()
                original = self._find(request_id=body['request_id'])
                return self._decision(original)
        if self.journal['mode'] != 'active':
            return self._reply('unavailable', reason='session_' + self.journal['mode'])
        if len(_encode(body)) > FRAME_LIMIT:
            raise ValueError('Complete GPU resource request exceeds capacity')
        request = dict(body, request_sha256=request_sha256, enqueue_sequence=self.journal['sequence'] + 1,
                       state='pending', lease_id=lease_id, consume_binding=None, release_ref=None, reason='queued')
        self._bound_guard(request, initial=True)
        if processes.identity(body['origin']['owner_identity']['pid']) != body['origin']['owner_identity']:
            raise ValueError('Original execution owner is unavailable')
        if _remaining(body['origin']) <= 0:
            request['state'], request['reason'] = 'expired', 'original_work_deadline'
        updated = _decode(_encode(self.journal))
        updated['requests'].append(request)
        self._commit(updated)
        self._admit()
        return self._decision(self._find(request_id=body['request_id']))

    def _blockers(self, request, requests=None):
        requests = self.journal['requests'] if requests is None else requests
        selected = set(request['ordered_device_uuids'])
        blockers = []
        for other in requests:
            if other['request_id'] == request['request_id']:
                continue
            overlap = selected & set(other['ordered_device_uuids'])
            if overlap and (other['state'] in _RESERVED or other['state'] == 'pending'
                            and other['enqueue_sequence'] < request['enqueue_sequence']):
                blockers.append({'request_id': other['request_id'], 'state': other['state'],
                                 'overlap': sorted(overlap)})
        return blockers

    def _decision(self, request):
        if request['state'] == 'pending' and self.last_inventory is not None and not self.last_inventory['available']:
            return self._reply('unavailable', request=request, reason='mandatory_nvml_operations_unavailable',
                               availability=self.last_inventory, blockers=self._blockers(request))
        return self._reply(request['state'], request=request, reason=request['reason'],
                           blockers=self._blockers(request) if request['state'] == 'pending' else [])

    def _sweep(self):
        updated = _decode(_encode(self.journal))
        changed = False
        for request in updated['requests']:
            if request['state'] not in {'pending', 'granted', 'consumed'}:
                continue
            reason = None
            try:
                if _remaining(request['origin']) <= 0:
                    reason = 'original_work_deadline'
                elif processes.identity(request['origin']['owner_identity']['pid']) != request['origin']['owner_identity']:
                    reason = 'original_owner_unavailable'
                else:
                    self._bound_guard(request)
            except (ValueError, OSError, EOFError) as error:
                reason = 'original_guard_or_owner_unavailable: ' + str(error)
            if reason is not None:
                request['state'] = 'expired' if request['state'] == 'pending' and reason == 'original_work_deadline' else (
                    'cancelled' if request['state'] == 'pending' else 'unknown')
                request['reason'], changed = reason, True
        if changed:
            self._commit(updated)

    def _admit(self):
        self._ensure()
        self._sweep()
        if self.journal['mode'] != 'active' or not any(item['state'] == 'pending' for item in self.journal['requests']):
            return
        observation = self._inventory()
        self.last_inventory = observation
        if not observation['available']:
            return
        rows = {item['uuid']: item for item in observation['devices']}
        updated = _decode(_encode(self.journal))
        changed = False
        for request in sorted(updated['requests'], key=lambda item: item['enqueue_sequence']):
            if request['state'] != 'pending' or self._blockers(request, updated['requests']):
                continue
            try:
                self._bound_guard(request, initial=True)
                if (_remaining(request['origin']) <= 0
                        or processes.identity(request['origin']['owner_identity']['pid']) != request['origin']['owner_identity']):
                    continue
            except (ValueError, OSError):
                continue
            if any(rows[identifier]['compute_pids'] or rows[identifier]['graphics_pids']
                   for identifier in request['ordered_device_uuids']):
                continue
            request['state'], request['reason'], changed = 'granted', 'resource_set_reserved', True
        if changed:
            self._commit(updated)

    def _consume(self, body, connection):
        _fields(body, {'request_id'}, 'resource consume message')
        request = self._find(request_id=_digest(body['request_id']))
        self._bound_guard(request, connection, initial=request['consume_binding'] is None)
        if request['consume_binding'] is not None:
            # Returning the original binding is reconciliation, never another launch.
            return self._decision(request)
        if self.journal['mode'] != 'active' or request['state'] != 'granted':
            return self._reply(request['state'] if request['state'] != 'granted' else 'unavailable',
                               request=request, reason='resource_consume_vetoed')
        if (_remaining(request['origin']) <= 0
                or processes.identity(request['origin']['owner_identity']['pid']) != request['origin']['owner_identity']):
            return self._reply('unavailable', request=request, reason='original_owner_or_work_deadline')
        updated = _decode(_encode(self.journal))
        target = next(item for item in updated['requests'] if item['request_id'] == request['request_id'])
        target['consume_binding'] = {'owner_epoch': self.journal['owner_epoch'],
                                     'sequence': self.journal['sequence'] + 1, 'lease_id': request['lease_id'],
                                     'request_sha256': request['request_sha256'], 'guard_identity': connection.peer,
                                     'guard_ready_raw_sha256': request['guard_ready_ref']['raw_sha256']}
        target['state'], target['reason'] = 'consumed', 'original_guard_single_use_consume'
        self._commit(updated)
        return self._decision(self._find(request_id=request['request_id']))

    def _veto(self, body, connection):
        _fields(body, {'request_id'}, 'resource veto observation')
        request_id = _digest(body['request_id'])
        if connection.request_id != request_id:
            raise ValueError('Resource veto observation belongs to another guard')
        if not any(item['request_id'] == request_id for item in self.journal['requests']):
            return self._reply('pending', reason='original_request_not_submitted', request_id=request_id,
                               lease_id=_lease_id(request_id), veto=self.journal['mode'] != 'active')
        request = self._find(request_id=request_id)
        self._bound_guard(request, connection)
        allowed = (self.journal['mode'] == 'active' and request['state'] in {'pending', 'granted', 'consumed'}
                   or self.journal['mode'] == 'draining' and request['state'] == 'consumed')
        return self._reply(request['state'], request=request, reason=request['reason'], veto=not allowed)

    def _cancel(self, body):
        _fields(body, {'request_id', 'origin'}, 'resource cancellation')
        request = self._find(request_id=_digest(body['request_id']))
        _origin(body['origin'])
        if body['origin'] != request['origin']:
            raise ValueError('Cancellation origin differs from original resource request')
        if request['state'] in _TERMINAL:
            return self._decision(request)
        updated = _decode(_encode(self.journal))
        target = next(item for item in updated['requests'] if item['request_id'] == request['request_id'])
        target['state'] = 'cancelled' if target['state'] == 'pending' else 'unknown'
        target['reason'] = 'original_resource_cancel_requested'
        self._commit(updated)
        self._admit()
        return self._decision(self._find(request_id=request['request_id']))

    def _release(self, body, connection=None):
        _fields(body, {'lease_id', 'proof_ref'}, 'resource release message')
        request = self._find(lease_id=_digest(body['lease_id']))
        _proof_reference(body['proof_ref'], request['lease_id'], 'stopped')
        if request['state'] == 'released':
            if request['release_ref']['proof_ref'] != body['proof_ref']:
                raise ValueError('Release retry differs from the original accepted proof')
            return self._decision(request)
        if request['state'] not in _RESERVED:
            return self._reply('rejected', request=request, reason='resource_was_never_granted')
        guard = self._bound_guard(request, connection)
        if guard.stopped_ref != body['proof_ref']:
            raise ValueError('Release requires stopped notification on the original live guard channel')
        proof_binding = _stopped_proof(self.directory, body['proof_ref'], self.session['session_id'], request, guard.peer)
        if _children(guard.peer):
            raise ValueError('Original GPU guard still has kernel children')
        observation = self._inventory()
        if not observation['available']:
            raise PoolUnavailable('Mandatory release NVML observation unavailable: ' + _encode(observation['errors']).decode())
        by_uuid = {item['uuid']: item for item in observation['devices']}
        assigned = [by_uuid[identifier] for identifier in request['ordered_device_uuids']]
        if any(item['compute_pids'] or item['graphics_pids'] for item in assigned):
            raise PoolUnavailable('Assigned GPU process observations are not empty')
        # No transaction waits for a guard exit. It must remain the same live,
        # spawn-closed, child-free process across the independent NVML snapshot.
        self._ensure()
        self._bound_guard(request, guard)
        if _children(guard.peer):
            raise ValueError('Original GPU guard gained children during release observation')
        if _read_proof(self.directory, body['proof_ref'], request['lease_id'], 'stopped')[1] != proof_binding:
            raise ValueError('Stopped proof inode/raw changed during release observation')
        updated = _decode(_encode(self.journal))
        target = next(item for item in updated['requests'] if item['request_id'] == request['request_id'])
        target['release_ref'] = {'proof_ref': body['proof_ref'], 'guard_identity': guard.peer,
                                 'proc_children': [], 'nvml_observation': assigned,
                                 'nvml_sha256': _sha(assigned), 'sequence': self.journal['sequence'] + 1}
        target['state'], target['reason'] = 'released', 'live_guard_reap_and_assigned_nvml_confirmed'
        if updated['mode'] == 'recovering' and not any(item['state'] in _RESERVED for item in updated['requests']):
            updated['mode'] = 'active'
        self._commit(updated)
        result = self._decision(self._find(request_id=request['request_id']))
        self._admit()
        return result

    def _reconcile(self, body):
        _fields(body, {'lease_id'}, 'resource reconciliation')
        request = self._find(lease_id=_digest(body['lease_id']))
        if request['state'] in _TERMINAL:
            return self._decision(request)
        guard = self.guards.get(request['request_id'])
        if guard is not None and guard.stopped_ref is not None:
            result = self._release({'lease_id': request['lease_id'], 'proof_ref': guard.stopped_ref}, guard)
        else:
            result = self._reply(request['state'], request=request,
                                 reason='original_live_spawn_closed_guard_and_stopped_notification_required',
                                 missing_evidence=['original_live_guard_channel', 'live_child_free_spawn_closed_proof',
                                                   'assigned_device_nvml_observation'])
        return result

    def _complete_close(self):
        self._ensure(allow_closed=True)
        if any(item['state'] not in _TERMINAL for item in self.journal['requests']):
            raise PoolUnavailable('Original GPU children are not all terminal')
        # Recheck the exact immutable sentinel immediately before removing it.
        try:
            raw, binding = _read_bound(self.sentinel, FRAME_LIMIT)
        except FileNotFoundError:
            if self.journal['mode'] != 'closed':
                raise PoolUnavailable('A missing sentinel cannot close an active resource session')
            _sync(self.sentinel.parent)
            self.finished = True
            return
        if binding != self.session['legacy_sentinel_binding'] or raw != self.sentinel_raw:
            self.fatal = 'unknown: refusing to unlink changed or foreign legacy sentinel'
            raise PoolUnavailable(self.fatal)
        self.sentinel.unlink()
        # If fsync fails after unlink, only this already-closed session may
        # finish the parent sync. Never create another fence or execution chance.
        _sync(self.sentinel.parent)
        self.finished = True

    def _close(self):
        if self.journal['mode'] != 'closed':
            updated = _decode(_encode(self.journal))
            updated['mode'] = 'draining'
            for request in updated['requests']:
                if request['state'] == 'pending':
                    request['state'], request['reason'] = 'cancelled', 'session_draining_before_consume'
            self._commit(updated)
            if any(item['state'] in _RESERVED for item in self.journal['requests']):
                return self._reply('pending', reason='session_draining_live_or_unknown_children', mode='draining')
            updated = _decode(_encode(self.journal))
            updated['mode'] = 'closed'
            self._commit(updated)
        try:
            self._complete_close()
        except (OSError, ValueError) as error:
            return self._reply('unavailable', reason='close-incomplete: ' + str(error), mode='closed')
        return self._reply('released', reason='session_closed', mode='closed')

    def _inspect(self):
        observation = self._inventory()
        return self._reply('unknown' if self.fatal else 'unavailable' if not observation['available'] else 'pending',
                           reason=self.fatal or 'observation_only', mode='unknown' if self.fatal else self.journal['mode'],
                           availability={'kernel': self.kernel, 'nvml': observation},
                           requests=self.journal['requests'], initial_owner=self.session['initial_owner'],
                           current_owner=self.journal['current_owner'], ordered_device_uuids=self.configuration['device_uuids'])

    def _handle(self, message, connection):
        _fields(message, {'protocol', 'session_id', 'action', 'body'}, 'GPU pool wire message')
        if message['protocol'] != PROTOCOL or message['session_id'] != self.session['session_id']:
            raise ValueError('GPU resource channel protocol or session differs')
        action, body = message['action'], message['body']
        if action == 'inspect':
            if body is not None or connection.request_id is not None:
                raise ValueError('Invalid resource inspection message')
            try:
                self._ensure(allow_closed=True)
            except PoolUnavailable:
                pass
            return self._inspect()
        self._ensure(allow_closed=action == 'close')
        if action == 'guard_ready':
            return self._guard_ready(body, connection)
        if connection.request_id is not None:
            if action == 'consume':
                return self._consume(body, connection)
            if action == 'veto':
                self._sweep()
                return self._veto(body, connection)
            if action == 'cancel':
                if not isinstance(body, dict) or body.get('request_id') != connection.request_id:
                    raise ValueError('Guard cancellation belongs to another resource request')
                return self._cancel(body)
            if action == 'stopped':
                _fields(body, {'lease_id', 'proof_ref'}, 'guard stopped notification')
                if body['lease_id'] != _lease_id(connection.request_id):
                    raise ValueError('Guard stopped notification belongs to another lease')
                if connection.stopped_ref is not None and connection.stopped_ref != body['proof_ref']:
                    raise ValueError('Guard attempted to replace its original stopped proof')
                connection.stopped_ref = body['proof_ref']
                return self._release(body, connection)
            raise ValueError('Dedicated GPU guard channel does not support this operation')
        if action == 'request':
            return self._request(body)
        if action == 'cancel':
            return self._cancel(body)
        if action == 'release':
            return self._release(body)
        if action == 'reconcile':
            return self._reconcile(body)
        if action == 'close' and body is None:
            return self._close()
        raise ValueError('Unsupported GPU resource operation')

    def _disconnect(self, connection):
        try:
            self.selector.unregister(connection.socket)
        except (KeyError, ValueError):
            pass
        connection.socket.close()
        self.connections.discard(connection)
        if connection.request_id is not None and self.guards.get(connection.request_id) is connection:
            del self.guards[connection.request_id]
            # Never interpret EOF or an elapsed interval as a healthy release.
            if not self.finished and self.fatal is None:
                try:
                    self._sweep()
                except (ValueError, OSError):
                    pass

    def _listen(self):
        path = self.coordination / 'session.sock'
        _ordinary(path)
        if path.exists():
            observed = path.stat(follow_symlinks=False)
            if not stat.S_ISSOCK(observed.st_mode):
                raise PoolUnavailable('Refusing to replace a non-socket resource endpoint')
            # This owner holds the lifetime flock and has verified the original
            # session; a still-listening old endpoint would violate that fence.
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            probe.settimeout(_IO_SECONDS)
            try:
                probe.connect(str(path))
            except (ConnectionRefusedError, FileNotFoundError):
                if path.stat(follow_symlinks=False).st_ino != observed.st_ino:
                    raise PoolUnavailable('Original resource socket changed during recovery')
                path.unlink()
            else:
                raise PoolUnavailable('Original resource socket still has a live owner')
            finally:
                probe.close()
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.set_inheritable(False)
        self.listener.setblocking(False)
        self.listener.bind(str(path))
        os.chmod(path, 0o600)
        self.socket_stat = path.stat(follow_symlinks=False)
        self.listener.listen(64)
        self.selector.register(self.listener, selectors.EVENT_READ, None)

    def _io(self, connection, events):
        if events & selectors.EVENT_WRITE and connection.tx:
            sent = connection.socket.send(connection.tx)
            del connection.tx[:sent]
            if not connection.tx:
                if connection.close_after_reply:
                    self._disconnect(connection)
                    return
                connection.deadline = None
                self.selector.modify(connection.socket, selectors.EVENT_READ, connection)
        if events & selectors.EVENT_READ:
            chunk = connection.socket.recv(FRAME_LIMIT + 5 - len(connection.rx))
            if not chunk:
                self._disconnect(connection)
                return
            if connection.deadline is None:
                connection.deadline = time.monotonic() + _IO_SECONDS
            connection.rx.extend(chunk)
            if len(connection.rx) < 4:
                return
            size, = struct.unpack('!I', connection.rx[:4])
            if not 0 < size <= FRAME_LIMIT or len(connection.rx) > size + 4:
                raise ValueError('Invalid or pipelined GPU resource frame')
            if len(connection.rx) < size + 4:
                return
            message = _decode(bytes(connection.rx[4:]))
            connection.rx.clear()
            try:
                result = self._handle(message, connection)
            except PoolUnavailable as error:
                result = self._reply('unavailable', reason=str(error))
            except (ValueError, KeyError, TypeError, OSError) as error:
                result = self._reply('rejected', reason=str(error))
            raw = _encode(result)
            if len(raw) > FRAME_LIMIT:
                raw = _encode(self._reply('unavailable', reason='Complete resource response exceeds frame capacity; inspect the original bounded journal locally'))
            connection.tx = bytearray(struct.pack('!I', len(raw)) + raw)
            connection.close_after_reply = connection.request_id is None
            connection.deadline = time.monotonic() + _IO_SECONDS
            self.selector.modify(connection.socket, selectors.EVENT_WRITE, connection)

    def run(self, stop_requested):
        if self.finished:
            self.selector.close()
            return self._reply('released', reason='session_closed', mode='closed')
        last_sweep = 0.0
        try:
            self._listen()
            while True:
                if stop_requested is not None and stop_requested() and self.journal['mode'] == 'active':
                    self._close()
                for key, events in self.selector.select(.1):
                    if key.data is None:
                        accepted, _ = self.listener.accept()
                        accepted.setblocking(False)
                        accepted.set_inheritable(False)
                        if len(self.connections) >= 256 or self.finished:
                            accepted.close()
                            continue
                        try:
                            connection = _Connection(accepted)
                        except (ValueError, OSError):
                            accepted.close()
                            continue
                        self.connections.add(connection)
                        self.selector.register(accepted, selectors.EVENT_READ, connection)
                    else:
                        try:
                            self._io(key.data, events)
                        except BlockingIOError:
                            pass
                        except (ValueError, OSError, EOFError, UnicodeError, RecursionError):
                            self._disconnect(key.data)
                now = time.monotonic()
                for connection in list(self.connections):
                    if connection.deadline is not None and now >= connection.deadline:
                        self._disconnect(connection)
                if not self.finished and self.fatal is None and now - last_sweep >= .2:
                    try:
                        self._admit()
                        if self.journal['mode'] == 'draining' and not any(
                                item['state'] in _RESERVED for item in self.journal['requests']):
                            self._close()
                    except (ValueError, OSError):
                        # Exact failed candidate/fence is retained by _commit/_ensure.
                        pass
                    last_sweep = now
                if self.finished and not any(connection.tx for connection in self.connections):
                    return self._reply('released', reason='session_closed', mode='closed')
        finally:
            for connection in list(self.connections):
                self._disconnect(connection)
            if self.listener is not None:
                try:
                    self.selector.unregister(self.listener)
                except KeyError:
                    pass
                self.listener.close()
            self.selector.close()
            # A crashed or interrupted owner leaves the sentinel and journal.
            # Only remove the exact socket inode this owner published.
            if self.socket_stat is not None:
                path = self.coordination / 'session.sock'
                try:
                    observed = path.stat(follow_symlinks=False)
                    if (observed.st_dev, observed.st_ino) == (self.socket_stat.st_dev, self.socket_stat.st_ino):
                        path.unlink()
                except FileNotFoundError:
                    pass


class _Connection:
    def __init__(self, connection):
        self.socket = connection
        self.peer = _peer(connection)
        self.rx, self.tx = bytearray(), bytearray()
        self.deadline = time.monotonic() + _IO_SECONDS
        self.close_after_reply = False
        self.request_id = None
        self.ready = None
        self.ready_binding = None
        self.ready_ref = None
        self.stopped_ref = None


def session(configuration, recover=None, *, inventory_provider=None, stop_requested=None):
    """Run an explicit CPU session; recovery never creates a replacement session.

    ``inventory_provider`` is an in-process test seam returning complete NVML-like
    rows. The module command always uses the real optional NVML provider.
    """
    validate_configuration(configuration)
    if sys.platform != 'linux':
        raise PoolUnavailable('Local GPU admission supports cooperating Linux processes only')
    import fcntl

    directory = Path(configuration['coordination_directory'])
    _ordinary(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not Path(configuration['legacy_sentinel']).parent.is_dir():
        raise ValueError('The explicitly selected legacy sentinel parent must already exist')
    lock_path = directory / 'pool.lock'
    _ordinary(lock_path)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError('GPU pool lifetime lock requires an ordinary fixed inode')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.fsync(descriptor)
        _sync(directory)
        owner = _Session(configuration, descriptor, recover, inventory_provider)
        return owner.run(stop_requested)
    finally:
        os.close(descriptor)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='action', required=True)
    owner = subparsers.add_parser('session')
    owner.add_argument('--config', required=True)
    owner.add_argument('--recover')
    close = subparsers.add_parser('close')
    close.add_argument('--config', required=True)
    args = parser.parse_args(argv)
    try:
        configuration = _decode(_read(Path(args.config), FRAME_LIMIT))
        if args.action == 'session':
            result = session(configuration, args.recover)
        else:
            result = LocalGpuPool.connect(configuration).close()
        print(_encode(result).decode())
        return 0 if result['status'] not in {'unavailable', 'rejected', 'unknown'} else 1
    except (ValueError, OSError, UnicodeError, EOFError) as error:
        print(_encode({'status': 'unavailable', 'reason': str(error)}).decode())
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
