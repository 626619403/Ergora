"""CPU-only resource-owner checks through the real Linux process/socket boundary."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import time

import pytest

from ergora.runtime import budget_clock
from ergora.runtime import gpu_pool as local_gpu_pool
from ergora.runtime import processes
from ergora._paths import IMPORT_ROOT


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Linux local GPU resource-owner contract')


def _configuration(tmp_path, count=4):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / 'legacy').mkdir(exist_ok=True)
    return {'schema_version': 1, 'kind': 'local-gpu-pool-config', 'pool_id': 'cpu-fixture',
            'coordination_directory': str(tmp_path / 'p'),
            'legacy_sentinel': str(tmp_path / 'legacy' / 'active.json'),
            'device_uuids': [f'GPU-fixture-{index}' for index in range(count)],
            'mode': 'trusted-cooperating-local'}


def _inventory(configuration):
    return [{'index': index, 'uuid': identifier, 'compute_pids': [], 'graphics_pids': [],
             'memory': {'available': False, 'error': 'FixtureMemoryUnavailable'}}
            for index, identifier in enumerate(configuration['device_uuids'])]


def _write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def _start_session(tmp_path, configuration, *, recover=None, setup=''):
    """The injected provider is explicit Python code, never selected by product config."""
    config_path, inventory_path = tmp_path / 'config.json', tmp_path / 'fake-inventory.json'
    _write(config_path, configuration)
    if not inventory_path.exists():
        _write(inventory_path, _inventory(configuration))
    script = (
        'import json,sys;from pathlib import Path;from ergora.runtime import gpu_pool as local_gpu_pool\n'
        'configuration=json.loads(Path(sys.argv[1]).read_text())\n'
        'inventory_path=Path(sys.argv[2])\n'
        + setup + '\n'
        'result=local_gpu_pool.session(configuration, '
        + repr(recover) + ', inventory_provider=lambda:json.loads(inventory_path.read_text()))\n'
        'print(json.dumps(result),flush=True)\n'
    )
    environment = dict(os.environ)
    package_root = str(IMPORT_ROOT)
    environment['PYTHONPATH'] = os.pathsep.join(filter(None, [package_root, environment.get('PYTHONPATH')]))
    return subprocess.Popen([sys.executable, '-c', script, str(config_path), str(inventory_path)],
                            cwd=tmp_path, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _ready(configuration, child, timeout=5):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        if child.poll() is not None:
            stdout, stderr = child.communicate()
            pytest.fail(f'CPU session exited before readiness ({child.returncode}): {stdout}\n{stderr}')
        try:
            pool = local_gpu_pool.LocalGpuPool.connect(configuration)
            pool.inspect()
            return pool
        except (ValueError, OSError) as error:
            last_error = error
        time.sleep(.02)
    pytest.fail(f'CPU session did not become ready: {last_error}')


def _stop_session(child, pool=None):
    if child.poll() is None and pool is not None:
        try:
            pool.close()
            child.wait(timeout=2)
        except (ValueError, OSError, subprocess.TimeoutExpired):
            pass
    if child.poll() is None:
        # Only the CPU session born in this helper is a cleanup target. A retained
        # sentinel is deliberate evidence when a test has made close fail closed.
        child.terminate()
    child.communicate(timeout=5)


@contextmanager
def fake_pool(tmp_path, *, count=4, _setup=''):
    """Yield (public pool client, config, owned CPU process), with fake NVML rows."""
    # A pytest node's directory may already exceed AF_UNIX's 108-byte pathname
    # capacity. This directory owns only this helper's records and socket.
    with tempfile.TemporaryDirectory(prefix='ergora-gpu-', dir='/tmp') as directory:
        configuration = _configuration(tmp_path, count)
        configuration['coordination_directory'] = directory
        child = _start_session(tmp_path, configuration, setup=_setup)
        pool = None
        try:
            pool = _ready(configuration, child)
            yield pool, configuration, child
        finally:
            _stop_session(child, pool)


@contextmanager
def _after_record_read(monkeypatch, path, callback):
    """Schedule once after complete descriptor read, before its final fstat."""
    original = os.fdopen
    fired = False

    class RecordRead:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def fileno(self):
            return self.stream.fileno()

        def read(self, *args):
            nonlocal fired
            raw = self.stream.read(*args)
            if not fired:
                fired = True
                callback(raw)
            return raw

    def fdopen(descriptor, *args, **kwargs):
        target = Path('/proc/self/fd', str(descriptor)).readlink()
        stream = original(descriptor, *args, **kwargs)
        return RecordRead(stream) if target == path else stream

    with monkeypatch.context() as patch:
        patch.setattr(os, 'fdopen', fdopen)
        yield
    assert fired, 'The selected record was not read'


def _origin(tmp_path):
    artifacts = tmp_path / 'artifacts'
    artifacts.mkdir()
    for name in ('attempt.json', 'authorization.json'):
        (artifacts / name).write_text('{}\n', encoding='utf-8')
    def reference(name):
        return {'root': str(artifacts), 'relative_path': name,
                'raw_sha256': hashlib.sha256((artifacts / name).read_bytes()).hexdigest(),
                'semantic_sha256': None}
    return {'kind': 'supervised-command-v1', 'operation_id': 'resource-only',
            'attempt_ref': reference('attempt.json'), 'authorization_ref': reference('authorization.json'),
            'source_sha256': 'a' * 64, 'config_sha256': 'b' * 64,
            'clock': budget_clock.authorize(30), 'wall_seconds': 30, 'cleanup_reserve_seconds': 2,
            'owner_identity': processes.identity(os.getpid())}


@pytest.mark.parametrize('legacy_bytes', [b'{"devices":[0,1]}\n', b'not-complete-json{'])
def test_existing_legacy_sentinel_blocks_every_new_session_without_touching_it(tmp_path, legacy_bytes):
    configuration = _configuration(tmp_path)
    sentinel = Path(configuration['legacy_sentinel'])
    sentinel.write_bytes(legacy_bytes)
    before = sentinel.stat()
    child = _start_session(tmp_path, configuration)
    try:
        stdout, stderr = child.communicate(timeout=5)
        assert child.returncode != 0, stdout
        assert 'external_or_unknown' in stderr
        assert sentinel.read_bytes() == legacy_bytes
        assert (sentinel.stat().st_dev, sentinel.stat().st_ino) == (before.st_dev, before.st_ino)
        assert not (Path(configuration['coordination_directory']) / 'session.sock').exists()
    finally:
        _stop_session(child)


def test_different_coordination_directories_compete_on_the_same_actual_legacy_path(tmp_path):
    with fake_pool(tmp_path / 'first') as (pool, configuration, first):
        sentinel = Path(configuration['legacy_sentinel'])
        original = sentinel.read_bytes(), sentinel.stat().st_ino
        second_configuration = _configuration(tmp_path / 'second')
        second_configuration['legacy_sentinel'] = str(sentinel)
        second = _start_session(tmp_path / 'second', second_configuration)
        try:
            _, stderr = second.communicate(timeout=5)
            assert second.returncode != 0
            assert 'external_or_unknown' in stderr
            assert first.poll() is None
            assert pool.inspect()['requests'] == []
            assert (sentinel.read_bytes(), sentinel.stat().st_ino) == original
            with pytest.raises(FileExistsError):
                sentinel.open('x')
        finally:
            _stop_session(second)


@pytest.mark.parametrize('count', [3, 5])
def test_configured_universe_and_ordered_subset_identity_are_not_fixed_to_eight(tmp_path, count):
    with fake_pool(tmp_path, count=count) as (pool, configuration, _child):
        observation = pool.inspect()
        assert observation['ordered_device_uuids'] == configuration['device_uuids']
        assert len(observation['availability']['nvml']['devices']) == count
        assert observation['availability']['nvml']['available'] is True
        assert all(row['memory']['available'] is False for row in observation['availability']['nvml']['devices'])
        origin = _origin(tmp_path)
        ordered = [configuration['device_uuids'][-1], configuration['device_uuids'][0]]
        identity = processes.identity(os.getpid())
        request_id, lease_id = pool.request_identity(origin, ordered, identity, 'c' * 64)
        assert (request_id, lease_id) == pool.request_identity(origin, ordered, identity, 'c' * 64)
        assert (request_id, lease_id) != pool.request_identity(origin, list(reversed(ordered)), identity, 'c' * 64)
        assert pool.inspect()['requests'] == []


def test_resource_only_request_cannot_grant_without_its_original_live_guard(tmp_path):
    with fake_pool(tmp_path) as (pool, configuration, child):
        origin = _origin(tmp_path)
        selected = [configuration['device_uuids'][1], configuration['device_uuids'][0]]
        request_id, lease_id = pool.request_identity(origin, selected, processes.identity(os.getpid()), 'c' * 64)
        result = pool.request({'request_id': request_id, 'origin': origin, 'ordered_device_uuids': selected,
                               'guard_ready_ref': {'relative_path': f'proofs/{lease_id}/ready.json',
                                                   'raw_sha256': 'd' * 64}})
        assert result['status'] == 'rejected'
        assert pool.inspect()['requests'] == []
        assert Path('/proc', str(child.pid), 'task', str(child.pid), 'children').read_text().strip() == ''


@pytest.mark.parametrize('failure', ['missing-device', 'duplicate-device', 'missing-compute', 'malformed-json'])
def test_required_inventory_failure_is_visible_and_never_becomes_empty_success(tmp_path, failure):
    with fake_pool(tmp_path) as (pool, configuration, _child):
        rows = _inventory(configuration)
        if failure == 'missing-device':
            rows.pop()
        elif failure == 'duplicate-device':
            rows.append(dict(rows[0], index=len(rows)))
        elif failure == 'missing-compute':
            del rows[0]['compute_pids']
        inventory_path = tmp_path / 'fake-inventory.json'
        if failure == 'malformed-json':
            inventory_path.write_text('{', encoding='utf-8')
        else:
            _write(inventory_path, rows)
        observation = pool.inspect()
        assert observation['status'] == 'unavailable'
        assert observation['availability']['nvml']['available'] is False
        assert observation['availability']['nvml']['errors']
        assert observation['requests'] == []
        _write(inventory_path, _inventory(configuration))
        assert pool.inspect()['availability']['nvml']['available'] is True


def test_incomplete_and_invalid_clients_do_not_block_a_complete_inspection(tmp_path):
    with fake_pool(tmp_path) as (pool, configuration, _child):
        clients = []
        try:
            for prefix in (b'\x00', struct.pack('!I', 20) + b'{', struct.pack('!I', 65_537)):
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.connect(str(Path(configuration['coordination_directory']) / 'session.sock'))
                client.sendall(prefix)
                clients.append(client)
            started = time.monotonic()
            assert pool.inspect()['requests'] == []
            assert time.monotonic() - started < .8
        finally:
            for client in clients:
                client.close()


@pytest.mark.parametrize('record', ['journal', 'session', 'descriptor'])
@pytest.mark.parametrize('corruption', ['duplicate-key', 'non-finite', 'unknown-field', 'oversized'])
def test_corrupt_durable_records_are_rejected_and_retained(tmp_path, record, corruption):
    with fake_pool(tmp_path) as (pool, configuration, _child):
        filename = {'journal': 'journal.json', 'session': 'session.json',
                    'descriptor': 'session-descriptor.json'}[record]
        path = pool.directory / filename
        original = json.loads(path.read_text())
        if corruption == 'duplicate-key':
            raw = b'{"schema_version":1,' + path.read_bytes()[1:]
        elif corruption == 'non-finite':
            raw = path.read_bytes().rstrip()[:-1] + b',"extra":NaN}'
        elif corruption == 'unknown-field':
            raw = json.dumps(dict(original, extra=True)).encode()
        else:
            raw = b' ' * (local_gpu_pool.JOURNAL_LIMIT + 1)
        path.write_bytes(raw)
        with pytest.raises((ValueError, OSError)):
            pool.inspect()
        with pytest.raises((ValueError, OSError)):
            local_gpu_pool.LocalGpuPool.connect(configuration)
        assert path.read_bytes() == raw
        assert Path(configuration['legacy_sentinel']).exists()


@pytest.mark.parametrize('drift', ['raw', 'inode', 'symlink', 'lock-inode'])
def test_close_retains_changed_fence_and_never_unlinks_foreign_paths(tmp_path, drift):
    with fake_pool(tmp_path) as (pool, configuration, _child):
        sentinel = Path(configuration['legacy_sentinel'])
        sentinel_raw = sentinel.read_bytes()
        changed = sentinel
        if drift == 'raw':
            sentinel.write_bytes(b'{"foreign":true}\n')
        elif drift in {'inode', 'symlink'}:
            replacement = sentinel.with_name('foreign.json')
            replacement.write_bytes(sentinel_raw if drift == 'inode' else b'foreign target\n')
            sentinel.unlink()
            if drift == 'inode':
                replacement.rename(sentinel)
            else:
                sentinel.symlink_to(replacement)
        else:
            changed = Path(configuration['coordination_directory']) / 'pool.lock'
            replacement = changed.with_name('replacement.lock')
            replacement.touch()
            replacement.replace(changed)
        identity = changed.lstat().st_ino
        raw = changed.read_bytes()
        try:
            result = pool.close()
        except (ValueError, OSError):
            result = None
        assert result is None or result['status'] in {'unavailable', 'unknown', 'rejected'}
        assert sentinel.exists() or sentinel.is_symlink()
        assert changed.lstat().st_ino == identity
        assert changed.read_bytes() == raw


def test_normal_close_releases_own_sentinel_and_preserves_archived_records_and_lock(tmp_path):
    with fake_pool(tmp_path) as (pool, configuration, child):
        sentinel = Path(configuration['legacy_sentinel'])
        lock = Path(configuration['coordination_directory']) / 'pool.lock'
        lock_inode = lock.stat().st_ino
        immutable = {name: (pool.directory / name).read_bytes()
                     for name in ('session.json', 'session-descriptor.json')}
        result = pool.close()
        assert result['status'] == 'released'
        assert result['mode'] == 'closed'
        assert child.wait(timeout=5) == 0
        assert not sentinel.exists()
        assert lock.stat().st_ino == lock_inode
        assert json.loads((pool.directory / 'journal.json').read_text())['mode'] == 'closed'
        assert {name: (pool.directory / name).read_bytes() for name in immutable} == immutable
        with sentinel.open('x') as legacy:
            legacy.write('legacy successor\n')
        assert sentinel.read_text() == 'legacy successor\n'


def test_initial_directory_sync_failure_retains_fence_without_publishing_a_socket(tmp_path):
    configuration = _configuration(tmp_path)
    setup = (
        'original_sync=local_gpu_pool._sync\n'
        'def fail_sync(directory):\n'
        '    if directory == Path(configuration["legacy_sentinel"]).parent:\n'
        '        raise OSError("injected sentinel directory fsync failure")\n'
        '    return original_sync(directory)\n'
        'local_gpu_pool._sync=fail_sync\n'
    )
    child = _start_session(tmp_path, configuration, setup=setup)
    try:
        _, stderr = child.communicate(timeout=5)
        assert child.returncode != 0
        assert 'injected sentinel directory fsync failure' in stderr
        sentinel = Path(configuration['legacy_sentinel'])
        raw = sentinel.read_bytes()
        inode = sentinel.stat().st_ino
        assert not (Path(configuration['coordination_directory']) / 'session.sock').exists()
        retry = _start_session(tmp_path, configuration)
        try:
            _, retry_error = retry.communicate(timeout=5)
            assert retry.returncode != 0
            assert 'external_or_unknown' in retry_error
            assert sentinel.read_bytes() == raw
            assert sentinel.stat().st_ino == inode
        finally:
            _stop_session(retry)
    finally:
        _stop_session(child)


def test_journal_replace_without_directory_sync_cannot_acknowledge_close(tmp_path):
    arm = tmp_path / 'fail-journal-sync'
    setup = (
        'original_sync=local_gpu_pool._sync\n'
        'def fail_sync(directory):\n'
        f'    if Path({str(arm)!r}).exists() and directory.parent.name == "sessions":\n'
        '        raise OSError("injected journal directory fsync failure")\n'
        '    return original_sync(directory)\n'
        'local_gpu_pool._sync=fail_sync\n'
    )
    with fake_pool(tmp_path, _setup=setup) as (pool, configuration, child):
        sentinel = Path(configuration['legacy_sentinel'])
        raw, inode = sentinel.read_bytes(), sentinel.stat().st_ino
        arm.touch()
        result = pool.close()
        assert result['status'] == 'unavailable'
        assert sentinel.read_bytes() == raw
        assert sentinel.stat().st_ino == inode
        journal = json.loads((pool.directory / 'journal.json').read_text())
        assert journal['mode'] == 'draining'
        assert journal['sequence'] >= 1
        assert child.poll() is None
        assert pool.close()['status'] == 'unavailable'
        assert sentinel.read_bytes() == raw
        child.terminate()
        assert child.wait(timeout=5) < 0
        arm.unlink()
        recovered_child = _start_session(tmp_path, configuration, recover=pool.session['session_id'])
        recovered_pool = None
        try:
            recovered_pool = _ready(configuration, recovered_child)
            recovered = recovered_pool.inspect()
            assert recovered['session_id'] == pool.session['session_id']
            assert recovered['owner_epoch'] == result['owner_epoch'] + 1
            assert recovered['sequence'] > journal['sequence']
            assert recovered['requests'] == []
            assert recovered_pool.close()['status'] == 'released'
            assert recovered_child.wait(timeout=5) == 0
            assert not sentinel.exists()
        finally:
            _stop_session(recovered_child, recovered_pool)


@pytest.mark.parametrize('failure', ['partial-write', 'sentinel-file-fsync'])
def test_exclusive_sentinel_publication_failure_retains_original_partial_or_unsynced_fence(tmp_path, failure):
    configuration = _configuration(tmp_path)
    if failure == 'partial-write':
        setup = (
            'original_fdopen=local_gpu_pool.os.fdopen\n'
            'class PartialSentinel:\n'
            '    def __init__(self,stream): self.stream=stream\n'
            '    def __enter__(self): return self\n'
            '    def __exit__(self,*args): return self.stream.__exit__(*args)\n'
            '    def write(self,raw):\n'
            '        self.stream.write(raw[:17]);self.stream.flush()\n'
            '        raise OSError("injected partial sentinel write")\n'
            'def fdopen(descriptor,*args,**kwargs):\n'
            '    target=Path("/proc/self/fd",str(descriptor)).readlink()\n'
            '    stream=original_fdopen(descriptor,*args,**kwargs)\n'
            '    return PartialSentinel(stream) if target == Path(configuration["legacy_sentinel"]) else stream\n'
            'local_gpu_pool.os.fdopen=fdopen\n'
        )
    else:
        setup = (
            'original_fsync=local_gpu_pool.os.fsync\n'
            'def fsync(descriptor):\n'
            '    if Path("/proc/self/fd",str(descriptor)).readlink() == Path(configuration["legacy_sentinel"]):\n'
            '        raise OSError("injected sentinel file fsync")\n'
            '    return original_fsync(descriptor)\n'
            'local_gpu_pool.os.fsync=fsync\n'
        )
    child = _start_session(tmp_path, configuration, setup=setup)
    try:
        _, stderr = child.communicate(timeout=5)
        assert child.returncode != 0
        assert ('injected partial sentinel write' if failure == 'partial-write'
                else 'injected sentinel file fsync') in stderr
        sentinel = Path(configuration['legacy_sentinel'])
        raw, inode = sentinel.read_bytes(), sentinel.stat().st_ino
        if failure == 'partial-write':
            assert len(raw) == 17
            with pytest.raises(json.JSONDecodeError):
                json.loads(raw)
        else:
            assert json.loads(raw)['kind'] == 'ergora-local-gpu-session'
        coordination = Path(configuration['coordination_directory'])
        assert not (coordination / 'session.sock').exists()
        journals = list((coordination / 'sessions').glob('*/journal.json'))
        assert len(journals) == 1
        assert json.loads(journals[0].read_text())['requests'] == []
        retry = _start_session(tmp_path, configuration)
        try:
            _, retry_error = retry.communicate(timeout=5)
            assert retry.returncode != 0
            assert 'external_or_unknown' in retry_error
            assert (sentinel.read_bytes(), sentinel.stat().st_ino) == (raw, inode)
        finally:
            _stop_session(retry)
    finally:
        _stop_session(child)


def test_legacy_writer_and_session_race_at_actual_exclusive_creation_with_exactly_one_winner(tmp_path):
    session_waiting, legacy_waiting = tmp_path / 'session-waiting', tmp_path / 'legacy-waiting'
    go, session_created = tmp_path / 'go', tmp_path / 'session-created'
    with tempfile.TemporaryDirectory(prefix='ergora-gpu-race-', dir='/tmp') as directory:
        configuration = _configuration(tmp_path)
        configuration['coordination_directory'] = directory
        setup = (
            'import time\n'
            'original_open=local_gpu_pool.os.open\n'
            'def competing_open(path,flags,*args,**kwargs):\n'
            '    target=Path(path) == Path(configuration["legacy_sentinel"]) and flags & local_gpu_pool.os.O_EXCL\n'
            '    if target:\n'
            f'        Path({str(session_waiting)!r}).touch()\n'
            '        deadline=time.monotonic()+5\n'
            f'        while not Path({str(go)!r}).exists():\n'
            '            if time.monotonic() >= deadline: raise TimeoutError("legacy race barrier")\n'
            '            time.sleep(.001)\n'
            '    descriptor=original_open(path,flags,*args,**kwargs)\n'
            f'    if target: Path({str(session_created)!r}).touch()\n'
            '    return descriptor\n'
            'local_gpu_pool.os.open=competing_open\n'
        )
        child = _start_session(tmp_path, configuration, setup=setup)
        legacy_code = (
            'import json,sys,time,os;from pathlib import Path\n'
            'sentinel,ready,go=map(Path,sys.argv[1:])\n'
            'ready.touch();deadline=time.monotonic()+5\n'
            'while not go.exists():\n'
            '    if time.monotonic() >= deadline: raise TimeoutError("session race barrier")\n'
            '    time.sleep(.001)\n'
            'try:\n'
            '    with sentinel.open("x") as stream:\n'
            '        stream.write("legacy-winner\\n");stream.flush();os.fsync(stream.fileno())\n'
            '    print(json.dumps({"won":True}))\n'
            'except FileExistsError:\n'
            '    print(json.dumps({"won":False}))\n'
        )
        legacy = subprocess.Popen([sys.executable, '-c', legacy_code, configuration['legacy_sentinel'],
                                   str(legacy_waiting), str(go)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        pool = None
        try:
            deadline = time.monotonic() + 5
            while not (session_waiting.exists() and legacy_waiting.exists()):
                assert child.poll() is None and legacy.poll() is None
                assert time.monotonic() < deadline
                time.sleep(.005)
            assert not Path(configuration['legacy_sentinel']).exists()
            go.touch()
            stdout, stderr = legacy.communicate(timeout=5)
            assert legacy.returncode == 0, stderr
            legacy_won = json.loads(stdout)['won']
            sentinel = Path(configuration['legacy_sentinel'])
            if legacy_won:
                _, session_error = child.communicate(timeout=5)
                assert child.returncode != 0
                assert 'legacy writer won exclusive sentinel creation' in session_error
                assert sentinel.read_bytes() == b'legacy-winner\n'
                assert not (Path(directory) / 'session.sock').exists()
            else:
                pool = _ready(configuration, child)
                assert json.loads(sentinel.read_bytes())['session_id'] == pool.session['session_id']
                assert pool.inspect()['requests'] == []
            assert int(legacy_won) + int(session_created.exists()) == 1
        finally:
            if legacy.poll() is None:
                legacy.terminate()
            legacy.communicate(timeout=5)
            _stop_session(child, pool)


@pytest.mark.parametrize('completion', ['same-owner-retry', 'original-session-recovery'])
def test_sentinel_unlink_failure_retains_exact_fence_until_original_close_completes(tmp_path, completion):
    arm = tmp_path / 'fail-unlink'
    setup = (
        'original_unlink=Path.unlink\n'
        'def unlink(path,*args,**kwargs):\n'
        f'    if path == Path(configuration["legacy_sentinel"]) and Path({str(arm)!r}).exists():\n'
        '        raise PermissionError("injected sentinel unlink failure")\n'
        '    return original_unlink(path,*args,**kwargs)\n'
        'Path.unlink=unlink\n'
    )
    with fake_pool(tmp_path, _setup=setup) as (pool, configuration, child):
        sentinel = Path(configuration['legacy_sentinel'])
        raw, inode = sentinel.read_bytes(), sentinel.stat().st_ino
        immutable = {name: (pool.directory / name).read_bytes()
                     for name in ('session.json', 'session-descriptor.json')}
        arm.touch()
        failed = pool.close()
        assert failed['status'] == 'unavailable'
        assert failed['mode'] == 'closed'
        assert 'close-incomplete' in failed['reason']
        assert 'injected sentinel unlink failure' in failed['reason']
        assert json.loads((pool.directory / 'journal.json').read_text())['mode'] == 'closed'
        assert (sentinel.read_bytes(), sentinel.stat().st_ino) == (raw, inode)
        with pytest.raises(FileExistsError):
            sentinel.open('x')
        assert pool.close()['status'] == 'unavailable'
        assert (sentinel.read_bytes(), sentinel.stat().st_ino) == (raw, inode)
        if completion == 'same-owner-retry':
            arm.unlink()
            completed = pool.close()
            assert completed['session_id'] == failed['session_id']
            assert completed['owner_epoch'] == failed['owner_epoch']
            assert completed['status'] == 'released'
            assert child.wait(timeout=5) == 0
        else:
            child.terminate()
            assert child.wait(timeout=5) < 0
            arm.unlink()
            recovering = _start_session(tmp_path, configuration, recover=failed['session_id'])
            try:
                stdout, stderr = recovering.communicate(timeout=5)
                assert recovering.returncode == 0, stderr
                completed = json.loads(stdout)
                assert completed['session_id'] == failed['session_id']
                assert completed['owner_epoch'] == failed['owner_epoch'] + 1
                assert completed['status'] == 'released'
            finally:
                _stop_session(recovering)
        assert not sentinel.exists()
        assert {name: (pool.directory / name).read_bytes() for name in immutable} == immutable


def test_ready_proof_with_wrong_guard_birth_cannot_bind_the_actual_socket_peer(tmp_path):
    with fake_pool(tmp_path) as (pool, configuration, _child):
        origin = _origin(tmp_path)
        peer = processes.identity(os.getpid())
        wrong_birth = dict(peer, start_ticks=str(int(peer['start_ticks']) + 1))
        selected = configuration['device_uuids'][:1]
        request_id, lease_id = pool.request_identity(origin, selected, wrong_birth, 'c' * 64)
        proof = {'schema_version': 1, 'kind': local_gpu_pool.READY_KIND,
                 'session_id': pool.session['session_id'], 'request_id': request_id,
                 'input_sha256': 'c' * 64, 'origin_sha256': local_gpu_pool._sha(origin),
                 'command_sha256': 'd' * 64, 'ordered_device_uuids': selected,
                 'owner_identity': peer, 'guard_identity': wrong_birth,
                 'guard_source_sha256': local_gpu_pool.guard_source_sha256(), 'prepared_subreaper': True,
                 'ready_at': datetime.now(timezone.utc).isoformat()}
        path = pool.proof_directory(lease_id) / 'ready.json'
        raw = local_gpu_pool._publish(path, proof)
        result = pool.call('guard_ready', {'request_id': request_id, 'ready_ref': {
            'relative_path': f'proofs/{lease_id}/ready.json', 'raw_sha256': hashlib.sha256(raw).hexdigest()}})
        assert result['status'] == 'rejected'
        assert 'original live prepared guard binding' in result['reason']
        assert pool.inspect()['requests'] == []


def test_fabricated_stopped_file_cannot_release_a_real_guard_with_live_payload_children(tmp_path):
    # Import at execution time: the guard tests consume fake_pool from this module.
    from test_local_gpu_guard import _owner, _result, _setup, _until

    with fake_pool(tmp_path / 'pool', count=1) as (pool, configuration, _child):
        setup, _ = _setup(tmp_path / 'task', configuration, configuration['device_uuids'],
            "import time;from pathlib import Path;Path('started').open('a').write('once\\n');time.sleep(30)")
        with _owner(setup) as owner:
            _until(lambda: (setup.parent / 'started').exists())
            request = pool.inspect()['requests'][0]
            assert request['state'] == 'consumed'
            directory = pool.proof_directory(request['lease_id'])
            guardian = json.loads((directory / 'ready.json').read_text())['guard_identity']
            assert local_gpu_pool._children(guardian)
            counterfeit = {'schema_version': 1, 'kind': local_gpu_pool.STOPPED_KIND,
                'session_id': pool.session['session_id'], 'lease_id': request['lease_id'],
                'request_sha256': request['request_sha256'],
                'consume_binding_sha256': local_gpu_pool._sha(request['consume_binding']),
                'guard_identity': guardian, 'origin_sha256': local_gpu_pool._sha(request['origin']),
                'process_result': {'status': 'succeeded', 'returncode': 0, 'output': str(setup.parent)},
                'reaped_at': datetime.now(timezone.utc).isoformat(), 'spawn_closed': True}
            path = directory / 'stopped.json'
            raw = local_gpu_pool._publish(path, counterfeit)
            inode = path.stat().st_ino
            result = pool.release(request['lease_id'], {
                'relative_path': f'proofs/{request["lease_id"]}/stopped.json',
                'raw_sha256': hashlib.sha256(raw).hexdigest()})
            assert result['status'] == 'rejected'
            assert 'original live guard channel' in result['reason']
            observed = pool.reconcile(request['lease_id'])
            assert observed['status'] == 'consumed'
            assert observed['release_ref'] is None
            assert local_gpu_pool._children(guardian)
            assert path.stat().st_ino == inode and path.read_bytes() == raw
            path.unlink()  # Remove only this test's counterfeit before real owner cleanup.
            (setup.parent / 'stop.requested').touch()
            assert _result(owner)['resource']['status'] == 'released'
        assert (setup.parent / 'started').read_text() == 'once\n'


def test_cli_inspection_reports_required_inventory_failure_with_nonzero_exit(tmp_path, capsys):
    import ergora.interfaces.cli as cli

    with fake_pool(tmp_path) as (_pool, configuration, _child):
        arguments = ['gpu-pool', 'inspect', '--config', str(tmp_path / 'config.json')]
        assert cli.main(arguments) == 0
        healthy = json.loads(capsys.readouterr().out)
        assert healthy['status'] == 'pending'
        assert healthy['availability']['nvml']['available'] is True
        rows = _inventory(configuration)
        del rows[0]['compute_pids']
        _write(tmp_path / 'fake-inventory.json', rows)
        assert cli.main(arguments) == 1
        unavailable = json.loads(capsys.readouterr().out)
        assert unavailable['session_id'] == healthy['session_id']
        assert unavailable['status'] == 'unavailable'
        assert unavailable['availability']['nvml']['available'] is False
        assert unavailable['availability']['nvml']['errors']


def test_client_journal_in_place_change_during_descriptor_read_is_rejected(tmp_path, monkeypatch):
    with fake_pool(tmp_path) as (pool, _configuration, _child):
        path = pool.directory / 'journal.json'
        raw, inode = path.read_bytes(), path.stat().st_ino

        def change(raw):
            with path.open('ab') as stream:
                stream.write(b' ')

        with _after_record_read(monkeypatch, path, change):
            with pytest.raises(ValueError):
                pool.inspect()
        assert path.stat().st_ino == inode
        assert path.read_bytes() == raw + b' '


@pytest.mark.parametrize('kind', ['fifo', 'directory', 'symlink'])
def test_client_journal_requires_an_ordinary_file_without_blocking(tmp_path, kind):
    with fake_pool(tmp_path) as (pool, _configuration, _child):
        path = pool.directory / 'journal.json'
        raw = path.read_bytes()
        path.unlink()
        if kind == 'fifo':
            os.mkfifo(path)
        elif kind == 'directory':
            path.mkdir()
        else:
            target = path.with_name('foreign-journal.json')
            target.write_bytes(raw)
            path.symlink_to(target)
        with pytest.raises((ValueError, OSError)):
            pool.inspect()
        assert path.exists()


@pytest.mark.parametrize('record', ['sentinel', 'proof'])
def test_bound_sentinel_and_proof_reads_reject_atomic_path_replacement(tmp_path, monkeypatch, record):
    with fake_pool(tmp_path) as (pool, configuration, _child):
        if record == 'sentinel':
            path = Path(configuration['legacy_sentinel'])
        else:
            path = pool.proof_directory('c' * 64) / 'ready.json'
            local_gpu_pool._publish(path, {'fixture': 'bounded-immutable-proof'})
        raw, inode = path.read_bytes(), path.stat().st_ino

        def replace(observed):
            assert observed == raw
            replacement = path.with_name('replacement.json')
            replacement.write_bytes(raw)
            os.replace(replacement, path)

        with _after_record_read(monkeypatch, path, replace):
            with pytest.raises(ValueError):
                if record == 'sentinel':
                    pool.inspect()
                else:
                    local_gpu_pool._read_bound(path, local_gpu_pool.FRAME_LIMIT)
        assert path.read_bytes() == raw
        assert path.stat().st_ino != inode


def test_old_client_snapshot_cannot_route_across_actual_owner_recovery(tmp_path, monkeypatch):
    with fake_pool(tmp_path) as (pool, configuration, child):
        path = pool.directory / 'journal.json'
        original = pool.inspect()
        restarted, current = None, None

        def recover(raw):
            nonlocal restarted, current
            assert json.loads(raw)['current_owner']['pid'] == child.pid
            child.terminate()
            child.communicate(timeout=5)
            restarted = _start_session(tmp_path, configuration, recover=pool.session['session_id'])
            current = _ready(configuration, restarted)
            assert current.owner_epoch == original['owner_epoch'] + 1

        try:
            with _after_record_read(monkeypatch, path, recover):
                with pytest.raises((local_gpu_pool.PoolUnavailable, FileNotFoundError)):
                    pool.inspect()
            observed = pool.inspect()
            assert observed['owner_epoch'] == original['owner_epoch'] + 1
            assert observed['current_owner'] == processes.identity(restarted.pid)
            assert observed['requests'] == []
        finally:
            if restarted is not None:
                _stop_session(restarted, current)


def test_journal_owner_cannot_bind_a_foreign_actual_socket_peer(tmp_path):
    with fake_pool(tmp_path) as (pool, configuration, child):
        path = Path(configuration['coordination_directory']) / 'session.sock'
        path.unlink()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as foreign:
            foreign.bind(str(path))
            foreign.listen()
            inode = path.stat().st_ino
            try:
                with pytest.raises(ValueError):
                    pool.inspect()
                assert child.poll() is None
                assert pool.current_owner == processes.identity(child.pid)
            finally:
                assert path.stat().st_ino == inode
                path.unlink()


@pytest.mark.parametrize('field', ['session_id', 'owner_epoch'])
def test_client_rejects_a_reply_with_another_session_or_epoch(tmp_path, field):
    arm = tmp_path / 'alter-reply'
    replacement = "result['owner_epoch'] + 1" if field == 'owner_epoch' else repr('0' * 32)
    setup = (
        'original_reply=local_gpu_pool._Session._reply\n'
        'def reply(self,*args,**kwargs):\n'
        '    result=original_reply(self,*args,**kwargs)\n'
        f'    if Path({str(arm)!r}).exists():\n'
        f'        result[{field!r}]={replacement}\n'
        '    return result\n'
        'local_gpu_pool._Session._reply=reply\n'
    )
    with fake_pool(tmp_path, _setup=setup) as (pool, _configuration, _child):
        original = pool.inspect()
        arm.touch()
        try:
            with pytest.raises(ValueError):
                pool.inspect()
        finally:
            arm.unlink()
        assert pool.inspect()['owner_epoch'] == original['owner_epoch']


def test_exact_lease_observation_never_adopts_unconfirmed_owner_state(monkeypatch):
    from types import SimpleNamespace

    owner = object.__new__(local_gpu_pool._Session)
    owner.session = {'session_id': '0' * 32}
    owner.journal_raw = b'original-committed-journal'
    owner.fatal = None
    owner.uncertain = b'visible-replacement'

    def repair(*args, **kwargs):
        pytest.fail('Lease observation must leave repair to the original resource operation')

    monkeypatch.setattr(local_gpu_pool, '_sync', repair)
    monkeypatch.setattr(owner, '_ensure', repair)
    connection = SimpleNamespace(request_id=None)
    message = {'protocol': local_gpu_pool.PROTOCOL, 'session_id': owner.session['session_id'],
               'action': 'observe_lease', 'body': {'lease_id': 'f' * 64}}
    with pytest.raises(local_gpu_pool.PoolUnavailable, match='acknowledgement is unconfirmed'):
        owner._handle(message, connection)
    assert owner.uncertain == b'visible-replacement' and owner.fatal is None
    assert owner.journal_raw == b'original-committed-journal'
    owner.uncertain = None
    monkeypatch.setattr(owner, '_original_journal_bytes', lambda: b'foreign-on-disk-snapshot')
    with pytest.raises(local_gpu_pool.PoolUnavailable, match='bytes are unconfirmed'):
        owner._handle(message, connection)
    assert owner.uncertain is None and owner.fatal is None
    assert owner.journal_raw == b'original-committed-journal'
