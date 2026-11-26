"""Actual original-owner/guard processes; NVML alone is a controlled substitute."""

from contextlib import contextmanager, ExitStack
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import pytest

from ergora.runtime import budget_clock
from ergora.runtime import gpu_guard as local_gpu_guard
from ergora.runtime import gpu_pool as local_gpu_pool
from ergora.runtime import processes
from test_local_gpu_pool import fake_pool, _after_record_read, _inventory, _ready, _start_session, _stop_session


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Dedicated Linux local resource guardians')
_OWNER = Path(__file__).parent / 'fixtures' / 'local_gpu_owner.py'


def _ref(path, *, semantic=False):
    raw = path.read_bytes()
    return {'root': str(path.parent), 'relative_path': path.name, 'raw_sha256': hashlib.sha256(raw).hexdigest(),
            'semantic_sha256': local_gpu_pool._sha(local_gpu_pool._decode(raw)) if semantic else None}


def _save(path, value):
    local_gpu_pool._publish(path, value)
    return _ref(path, semantic=True)


def _setup(directory, configuration, uuids, code, *, wall=15, reserve=3):
    directory.mkdir()
    payload = directory / 'payload.py'
    payload.write_text(code, encoding='utf-8')
    sources = [_ref(_OWNER), _ref(payload)]
    guard_sources = [_ref(Path(local_gpu_guard.__file__)), _ref(Path(processes.__file__))]
    config = _save(directory / 'task-config.json', {'fixture': 'original-task'})
    environment = {'PATH': os.defpath, 'PYTHONUTF8': '1', 'CUDA_VISIBLE_DEVICES': ','.join(uuids)}
    command = {'argv': [sys.executable, str(payload)], 'cwd': str(directory), 'env': environment}
    operation = uuid.uuid4().hex
    clock = budget_clock.authorize(wall)
    intent = _save(directory / 'intent.json', {'schema_version': 1, 'kind': 'local-gpu-fixture-intent',
        'scope': 'fixture-only', 'operation_id': operation, 'command_sha256': local_gpu_pool._sha(command),
        'ordered_device_uuids': uuids, 'source_refs': sources, 'config_ref': config, 'guard_source_refs': guard_sources,
        'source_sha256': local_gpu_pool._sha(sources), 'config_sha256': config['semantic_sha256']})
    authorization = _save(directory / 'authorization.json', {'schema_version': 1, 'kind': 'local-gpu-fixture-authorization',
        'scope': 'fixture-only', 'operation_id': operation, 'intent_ref': intent,
        'command_sha256': local_gpu_pool._sha(command), 'clock': clock, 'wall_seconds': wall,
        'cleanup_reserve_seconds': reserve})
    attempt = _save(directory / 'attempt.json', {'schema_version': 1, 'kind': 'local-gpu-fixture-attempt',
        'scope': 'fixture-only', 'operation_id': operation, 'attempt_id': uuid.uuid4().hex,
        'intent_ref': intent, 'authorization_ref': authorization})
    value = {'schema_version': 1, 'pool_config': configuration,
        'origin': {'kind': 'supervised-command-v1', 'operation_id': operation,
            'attempt_ref': attempt, 'source_sha256': local_gpu_pool._sha(sources),
            'config_sha256': config['semantic_sha256'], 'authorization_ref': authorization,
            'clock': clock, 'wall_seconds': wall, 'cleanup_reserve_seconds': reserve},
        'command': command, 'device_uuids': uuids, 'source_refs': sources, 'config_ref': config,
        'guard_source_refs': guard_sources, 'intent_ref': intent}
    _save(directory / 'setup.json', value)
    return directory / 'setup.json', value


@contextmanager
def _owner(setup, *, transport_fault=None):
    command = [sys.executable, str(_OWNER), '--input', str(setup)]
    if transport_fault is not None:
        # Inject only denial/corruption/delay in the original owner's transport.
        # Its actual fixture callbacks, frozen authority, and public guard API
        # still run; no test boolean grants execution or bypasses the channel.
        script = '''import importlib.util,json,sys,time
from pathlib import Path
from ergora.runtime import gpu_guard as guard
from ergora.runtime import gpu_pool as pool
spec=importlib.util.spec_from_file_location('original_fixture_owner',sys.argv[1])
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
setup=Path(sys.argv[2]);fault=sys.argv[3];value=json.loads(setup.read_text())
original=guard._wire;phase=None;fired=False
def wire(connection,deadline,*,value=None):
 global phase,fired
 if value is None:
  message=original(connection,deadline)
  if fault=='drop-resource-ack' and message.get('type')=='SUBMIT_ACK':
   setup.with_name('ack-lost').touch()
   raise EOFError('Controlled loss of the original guard acknowledgment')
  if message.get('type')=='CHECK':
   phase=message['body']['phase']
   if not fired and phase=='prelaunch' and fault in ('prelaunch-stop','prelaunch-deadline'):
    fired=True;setup.with_name('fault-observed').touch()
    if fault=='prelaunch-stop':setup.with_name('stop.requested').touch()
    else:
     while pool._remaining(globals()['value']['origin'])>0:time.sleep(.005)
  return message
 if (not fired and value.get('type')=='DECISION' and phase=='running'
     and setup.with_name('started').exists() and fault in ('wrong-nonce','timeout')):
  fired=True;setup.with_name('fault-observed').touch()
  if fault=='wrong-nonce':value={**value,'owner_nonce':'0'*32}
  else:time.sleep(1.25)
 return original(connection,deadline,value=value)
guard._wire=wire
if fault == 'delayed-resource-submit':
 original_request = pool.LocalGpuPool.request
 def deferred_request(instance, request):
  time.sleep(1.1)
  return original_request(instance, request)
 pool.LocalGpuPool.request = deferred_request
if fault == 'stop-after-resource-grant':
 original_request = pool.LocalGpuPool.request
 def held_grant(instance, request):
  result = original_request(instance, request)
  if result['status']!='granted':
   raise ValueError('Expected the original reserved resource before response hold')
  setup.with_name('grant-received').touch()
  while not setup.with_name('release-grant-response').exists():time.sleep(.01)
  raise TimeoutError('Controlled loss of the original resource request reply after grant')
 pool.LocalGpuPool.request = held_grant
if fault == 'stop-before-resource-send':
 original_request = pool.LocalGpuPool.request
 def held_send(instance, request):
  setup.with_name('submit-ack-observed').touch()
  while not setup.with_name('release-original-send').exists():time.sleep(.01)
  return original_request(instance, request)
 pool.LocalGpuPool.request = held_send
raise SystemExit(fixture.main(['--input',str(setup)]))
'''
        command = [sys.executable, '-c', script, str(_OWNER), str(setup), transport_fault]
    child = subprocess.Popen(command,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        yield child
    finally:
        if child.poll() is None:
            child.terminate()  # Fixture handler sets only its original stop flag.
        try:
            child.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate(timeout=5)


def _result(child):
    stdout, stderr = child.communicate(timeout=20)
    assert child.returncode == 0, stdout + stderr
    result = json.loads(stdout)
    assert 'error' not in result, result
    return result


def _until(predicate, *, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.02)
    raise AssertionError('Original process boundary was not observed before timeout')


@pytest.mark.parametrize('exit_code', [0, 3])
def test_public_owner_executes_once_with_ordered_devices_then_reaps_and_releases(tmp_path, exit_code):
    with fake_pool(tmp_path / 'pool', count=3) as (pool, config, session):
        devices = [config['device_uuids'][2], config['device_uuids'][0]]
        code = ("import json,os,sys;from pathlib import Path;"
                "sockets=[os.readlink(p) for p in Path('/proc/self/fd').iterdir() if p.exists()];"
                "Path('marker').open('a').write(json.dumps({'devices':os.environ['CUDA_VISIBLE_DEVICES'],"
                "'sockets':[p for p in sockets if p.startswith('socket:')]})+'\\n');"
                f'sys.exit({exit_code})')
        setup, original = _setup(tmp_path / 'task', config, devices, code)
        with _owner(setup) as owner:
            result = _result(owner)
        assert result['guard_returncode'] == 0, result
        assert result['resource']['status'] == 'released', result
        assert result['process_result']['returncode'] == exit_code
        assert result['process_result']['status'] == ('failed' if exit_code else 'succeeded')
        assert [json.loads(line) for line in (setup.parent / 'marker').read_text().splitlines()] == [
            {'devices': ','.join(devices), 'sockets': []}]
        request = pool.inspect()['requests'][0]
        assert request['ordered_device_uuids'] == devices
        assert request['origin']['clock'] == original['origin']['clock']
        # A lost management reply is reconciled against the exact completed
        # request, including after the original guardian has actually exited.
        retry = pool.request({key: request[key] for key in ('request_id', 'origin', 'ordered_device_uuids', 'guard_ready_ref')})
        assert retry['status'] == 'released'
        assert (setup.parent / 'marker').read_text().count('\n') == 1


def test_guard_waits_for_the_original_request_before_asking_to_consume(tmp_path):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, _):
        setup, _ = _setup(tmp_path / 'task', config, config['device_uuids'],
                         "from pathlib import Path;Path('started').open('a').write('once\\n')")
        with _owner(setup, transport_fault='delayed-resource-submit') as owner:
            result = _result(owner)
        assert result['process_result']['status'] == 'succeeded'
        assert result['resource']['status'] == 'released'
        assert (setup.parent / 'started').read_text().splitlines() == ['once']
        request, = pool.inspect()['requests']
        assert request['consume_binding']['sequence'] < request['release_ref']['sequence']


def test_missing_guard_submission_ack_has_no_resource_effect(tmp_path):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, _):
        setup, _ = _setup(tmp_path / 'task', config, config['device_uuids'],
                         "from pathlib import Path;Path('started').touch()", wall=6, reserve=2)
        with _owner(setup, transport_fault='drop-resource-ack') as owner:
            _until(setup.with_name('ack-lost').exists)
            assert pool.inspect()['requests'] == []
            result = _result(owner)
        assert result['request_id'] is None
        assert pool.inspect()['requests'] == []
        assert not (setup.parent / 'started').exists()


def test_stop_after_acknowledged_resource_grant_cleans_the_original_lease(tmp_path):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, _):
        setup, _ = _setup(tmp_path / 'task', config, config['device_uuids'],
                         "from pathlib import Path;Path('started').touch()")
        with _owner(setup, transport_fault='stop-after-resource-grant') as owner:
            _until(setup.with_name('grant-received').exists)
            original, = pool.inspect()['requests']
            assert original['state'] == 'granted' and original['consume_binding'] is None
            ready = json.loads((pool.directory / original['guard_ready_ref']['relative_path']).read_bytes())
            try:
                processes.notify_identity(ready['guard_identity'], signal.SIGTERM)
                released = _until(lambda: next((row for row in pool.inspect()['requests']
                    if row['lease_id'] == original['lease_id'] and row['state'] == 'released'), None))
                assert released['release_ref']['guard_identity'] == ready['guard_identity']
                assert released['consume_binding'] is None
            finally:
                setup.with_name('release-grant-response').touch()
            result = _result(owner)
        assert result['resource']['release_ref'] == released['release_ref']
        assert not (setup.parent / 'started').exists()


def test_stop_before_send_keeps_the_acknowledged_guard_through_absent_readback(tmp_path):
    absent = tmp_path / 'absent-request-observed'
    pool_probe = f'''
original_reconcile = local_gpu_pool._Session._reconcile
def observe_absent(self, body):
    try:
        return original_reconcile(self, body)
    except ValueError:
        Path({str(absent)!r}).touch()
        raise
local_gpu_pool._Session._reconcile = observe_absent
'''
    with fake_pool(tmp_path / 'pool', count=1, _setup=pool_probe) as (pool, config, _):
        setup, _ = _setup(tmp_path / 'task', config, config['device_uuids'],
                         "from pathlib import Path;Path('started').touch()")
        with _owner(setup, transport_fault='stop-before-resource-send') as owner:
            _until(setup.with_name('submit-ack-observed').exists)
            ready_file, = pool.directory.glob('proofs/*/ready.json')
            ready = json.loads(ready_file.read_bytes())
            try:
                assert pool.inspect()['requests'] == []
                processes.notify_identity(ready['guard_identity'], signal.SIGTERM)
                _until(absent.exists)
                assert pool.inspect()['requests'] == []
                assert processes.identity(ready['guard_identity']['pid']) == ready['guard_identity']
            finally:
                setup.with_name('release-original-send').touch()
            result = _result(owner)
        original, = pool.inspect()['requests']
        assert original['state'] == 'released' and original['consume_binding'] is None
        assert original['release_ref']['guard_identity'] == ready['guard_identity']
        assert result['resource']['release_ref'] == original['release_ref']
        assert not (setup.parent / 'started').exists()


def test_real_subreaper_drains_setsid_descendant_before_resource_release(tmp_path):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, session):
        descendant = "import os,time;from pathlib import Path;os.setsid();Path('adopted').write_text(str(os.getpid()));time.sleep(30)"
        code = ("import subprocess,sys,time;from pathlib import Path;"
                f'subprocess.Popen([sys.executable,"-c",{descendant!r}]);'
                "\nwhile not Path('adopted').exists():time.sleep(.01)\n")
        setup, _ = _setup(tmp_path / 'task', config, config['device_uuids'], code)
        with _owner(setup) as owner:
            result = _result(owner)
        assert result['resource']['status'] == 'released', result
        assert not Path('/proc', (setup.parent / 'adopted').read_text()).exists()
        assert result['process_result']['status'] == 'succeeded'


@pytest.mark.parametrize('stop_kind', ['stop.requested', 'authorization.revoked', 'source-change', 'deadline'])
def test_pending_live_owner_stop_or_frozen_source_change_never_spawns(tmp_path, monkeypatch, stop_kind):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, session):
        holder, _ = _setup(tmp_path / 'holder', config, config['device_uuids'],
                          "import time;from pathlib import Path;Path('started').touch()\n"
                          "while not Path('release').exists():time.sleep(.01)")
        pending, original = _setup(tmp_path / 'pending', config, config['device_uuids'],
                                  "from pathlib import Path;Path('unexpected').touch()",
                                  wall=4 if stop_kind == 'deadline' else 15, reserve=3)
        with _owner(holder) as first:
            _until(lambda: (holder.parent / 'started').exists())
            with ExitStack() as owners:
                second = None
                journal_path = pool.directory / 'journal.json'

                def submit_after_read(raw):
                    nonlocal second
                    before = json.loads(raw)
                    assert [item['state'] for item in before['requests']] == ['consumed']
                    second = owners.enter_context(_owner(pending))

                    def published():
                        value = json.loads(journal_path.read_bytes())
                        return value if len(value['requests']) == 2 else None

                    after = _until(published)
                    assert after['current_owner'] == before['current_owner']
                    assert after['owner_epoch'] == before['owner_epoch']
                    assert after['sequence'] > before['sequence']
                    assert [item['state'] for item in after['requests']] == ['consumed', 'pending']

                with _after_record_read(monkeypatch, journal_path, submit_after_read):
                    observation = pool.inspect()
                assert second is not None
                assert any(item['origin']['operation_id'] == original['origin']['operation_id']
                           and item['state'] == 'pending' for item in observation['requests'])
                if stop_kind == 'source-change':
                    (pending.parent / 'payload.py').write_text('# modified original source\n')
                elif stop_kind != 'deadline':
                    (pending.parent / stop_kind).touch()
                result = _result(second)
            assert not (pending.parent / 'unexpected').exists()
            assert result['process_result'] is None or result['process_result']['returncode'] is None
            request = pool.inspect()['requests'][1]
            state = request['state']
            assert state in ('expired', 'cancelled') if stop_kind == 'deadline' else state == 'cancelled'
            live = local_gpu_pool.observe_lease(config, pool.session['session_id'], request['lease_id'])
            assert live['status'] == state and live['release_ref'] is None
            assert live['attempt_sha256'] == original['origin']['attempt_ref']['raw_sha256']
            assert first.poll() is None, 'Stopping one original task must leave its sibling running'
            (holder.parent / 'release').touch()
            assert _result(first)['resource']['status'] == 'released'
        assert pool.close()['mode'] == 'closed'
        session.wait(timeout=5)
        archived = local_gpu_pool.observe_lease(config, pool.session['session_id'], request['lease_id'])
        assert archived['status'] == state and archived['release_ref'] is None
        assert archived['attempt_sha256'] == live['attempt_sha256']


@pytest.mark.parametrize('stop_kind', ['signal', 'owner-eof', 'deadline'])
def test_running_stop_cleans_only_original_tree_and_never_renews_clock(tmp_path, stop_kind):
    with fake_pool(tmp_path / 'pool', count=2) as (pool, config, session):
        code = "import time;from pathlib import Path;Path('started').touch();time.sleep(30);Path('late').touch()"
        setup, original = _setup(tmp_path / 'stopping', config, config['device_uuids'][:1], code,
                                  wall=5 if stop_kind == 'deadline' else 12, reserve=2)
        sibling, _ = _setup(tmp_path / 'sibling', config, config['device_uuids'][1:],
                            "import time;from pathlib import Path;Path('started').touch();time.sleep(4)")
        with _owner(sibling) as other, _owner(setup) as owner:
            _until(lambda: (setup.parent / 'started').exists() and (sibling.parent / 'started').exists())
            if stop_kind == 'signal':
                owner.send_signal(signal.SIGTERM)
                result = _result(owner)
                assert result['resource']['status'] == 'released', result
            elif stop_kind == 'owner-eof':
                owner.kill()
                owner.communicate(timeout=5)
                _until(lambda: any(item['origin']['operation_id'] == original['origin']['operation_id']
                                  and item['state'] == 'released' for item in pool.inspect()['requests']))
            else:
                assert _result(owner)['resource']['status'] == 'released'
            assert not (setup.parent / 'late').exists()
            assert other.poll() is None
            assert _result(other)['resource']['status'] == 'released'
        task = next(item for item in pool.inspect()['requests'] if item['origin']['operation_id'] == original['origin']['operation_id'])
        assert task['origin']['clock'] == original['origin']['clock']


@pytest.mark.parametrize('change', ['attempt', 'command', 'config', 'raw-sha'])
def test_fixture_authority_rejects_changed_original_before_any_guard_or_claim(tmp_path, change):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, session):
        setup, original = _setup(tmp_path / 'task', config, config['device_uuids'],
                                  "from pathlib import Path;Path('unexpected').touch()")
        if change == 'attempt':
            (setup.parent / 'attempt.json').write_text('{}')
        elif change == 'config':
            (setup.parent / 'task-config.json').write_text('{}')
        else:
            if change == 'command':
                original['command']['env']['UNAUTHORIZED'] = '1'
            else:
                original['source_refs'][1]['raw_sha256'] = '0' * 64
            setup.write_bytes(local_gpu_pool._encode(original))
        with _owner(setup) as owner:
            stdout, stderr = owner.communicate(timeout=5)
            assert owner.returncode == 2, stdout + stderr
        assert pool.inspect()['requests'] == []
        assert not (setup.parent / 'unexpected').exists()


def test_owner_authorization_callbacks_are_required_by_public_interface():
    with pytest.raises(TypeError, match='authorize.*stop_requested'):
        local_gpu_guard.run_owned_guard(None, {}, [], Path('/'), {}, device_uuids=[], source_refs=[],
                                        config_ref={}, guard_source_refs=[])


def test_false_authorization_return_cannot_be_interpreted_as_permission(tmp_path):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, session):
        setup, value = _setup(tmp_path / 'task', config, config['device_uuids'],
                             "from pathlib import Path;Path('unexpected').touch()")
        origin = dict(value['origin'], owner_identity=processes.identity(os.getpid()))
        with pytest.raises(ValueError, match='refused guard before creation'):
            local_gpu_guard.run_owned_guard(pool, origin, value['command']['argv'], setup.parent,
                value['command']['env'], device_uuids=value['device_uuids'], source_refs=value['source_refs'],
                config_ref=value['config_ref'], guard_source_refs=value['guard_source_refs'],
                authorize=lambda original: False, stop_requested=lambda: False)
        assert pool.inspect()['requests'] == []
        assert not (setup.parent / 'unexpected').exists()


def test_dynamic_disjoint_join_and_older_full_pool_barrier(tmp_path):
    with fake_pool(tmp_path / 'pool', count=4) as (pool, config, session):
        held_code = "import time;from pathlib import Path;Path('started').touch();time.sleep(30)"
        held, _ = _setup(tmp_path / 'held', config, config['device_uuids'][:1], held_code)
        joining, _ = _setup(tmp_path / 'joining', config, config['device_uuids'][1:2], held_code)
        full, full_input = _setup(tmp_path / 'full', config, config['device_uuids'],
                                  "import time;from pathlib import Path;Path('started').touch();time.sleep(1)")
        late, late_input = _setup(tmp_path / 'late', config, config['device_uuids'][2:3],
                                  "from pathlib import Path;Path('started').touch()")
        with _owner(held) as first:
            _until(lambda: (held.parent / 'started').exists())
            with _owner(joining) as second:
                _until(lambda: (joining.parent / 'started').exists())
                assert first.poll() is None, 'Disjoint work must join while another task is live'
                with _owner(full) as whole:
                    _until(lambda: any(item['origin']['operation_id'] == full_input['origin']['operation_id']
                                      and item['state'] == 'pending' for item in pool.inspect()['requests']))
                    with _owner(late) as last:
                        _until(lambda: any(item['origin']['operation_id'] == late_input['origin']['operation_id']
                                          and item['state'] == 'pending' for item in pool.inspect()['requests']))
                        assert not (late.parent / 'started').exists()
                        (joining.parent / 'stop.requested').touch()
                        assert _result(second)['resource']['status'] == 'released'
                        assert not (full.parent / 'started').exists()
                        (held.parent / 'stop.requested').touch()
                        assert _result(first)['resource']['status'] == 'released'
                        _until(lambda: (full.parent / 'started').exists())
                        assert not (late.parent / 'started').exists(), 'Full-pool predecessor must retain its barrier'
                        assert _result(whole)['resource']['status'] == 'released'
                        assert _result(last)['resource']['status'] == 'released'
        assert (late.parent / 'started').exists()
        assert all(item['state'] == 'released' for item in pool.inspect()['requests'])


def test_read_original_closed_release_with_a_successor_pool(tmp_path, capsys, monkeypatch):
    from ergora.interfaces import cli

    directory = tmp_path / 'pool'
    arm = tmp_path / 'fail-close-sync'
    inject = f'''
original_sync=local_gpu_pool._sync
def fail_closed_sync(directory):
    if (Path({str(arm)!r}).exists() and directory.parent.name == "sessions"
            and json.loads((directory / "journal.json").read_text())["mode"] == "closed"):
        raise OSError("injected closed journal sync failure")
    return original_sync(directory)
local_gpu_pool._sync=fail_closed_sync
'''
    with fake_pool(directory, count=1, _setup=inject) as (pool, config, original_owner):
        setup, original = _setup(tmp_path / 'task', config, config['device_uuids'], 'print("complete")')
        with _owner(setup) as child:
            release = _result(child)['resource']
        assert release['status'] == 'released'
        clock = release['release_ref']['owner_decision_clock']
        assert clock['boot_id'] == pool.session['initial_owner']['boot_id']
        original_config = tmp_path / 'original-config.json'
        original_config.write_bytes((directory / 'config.json').read_bytes())
        command = ['gpu-pool', 'inspect', '--config', str(original_config),
                   '--session-id', release['session_id'], '--lease-id', release['lease_id']]

        assert cli.main(command) == 2
        assert 'closed' in capsys.readouterr().err
        arm.touch()
        assert pool.close()['status'] == 'unavailable'
        assert json.loads((pool.directory / 'journal.json').read_text())['mode'] == 'closed'
        assert Path(config['legacy_sentinel']).is_file()
        assert cli.main(command) == 2
        assert 'original sentinel' in capsys.readouterr().err
        _stop_session(original_owner)
        arm.unlink()
        recovering = _start_session(directory, config, recover=release['session_id'])
        try:
            stdout, stderr = recovering.communicate(timeout=5)
            assert recovering.returncode == 0, stderr
            assert json.loads(stdout)['status'] == 'released'
        finally:
            _stop_session(recovering)

        proof = pool.directory / release['release_ref']['proof_ref']['relative_path']
        archived = [pool.directory / name for name in ('session-descriptor.json', 'session.json', 'journal.json')]
        archived.append(proof)
        fingerprints = [(path.read_bytes(), path.stat().st_ino) for path in archived]
        assert cli.main(command) == 0
        receipt = json.loads(capsys.readouterr().out)
        assert receipt['status'] == 'released' and receipt['mode'] == 'closed'
        for name in ('session_id', 'lease_id', 'request_id', 'request_sha256', 'release_ref'):
            assert receipt[name] == release[name]
        assert receipt['attempt_sha256'] == original['origin']['attempt_ref']['raw_sha256']

        next_config = dict(config, device_uuids=[*config['device_uuids'], 'GPU-successor-extra'])
        (directory / 'fake-inventory.json').write_text(json.dumps(_inventory(next_config)), encoding='utf-8')
        successor_owner = _start_session(directory, next_config)
        successor_pool = None
        try:
            successor_pool = _ready(next_config, successor_owner)
            current = successor_pool.inspect()['session_id']
            assert current != receipt['session_id']
            assert cli.main(command) == 0 and json.loads(capsys.readouterr().out) == receipt
            assert cli.main(command[:-1] + ['0' * 64]) == 2
            assert 'Unknown original GPU resource lease' in capsys.readouterr().err
            assert successor_pool.inspect()['session_id'] == current
            assert [(path.read_bytes(), path.stat().st_ino) for path in archived] == fingerprints

            journal = pool.directory / 'journal.json'
            journal_raw = journal.read_bytes()
            retained = json.loads(journal_raw)
            original_ref = retained['requests'][0]['release_ref']
            original_ref['owner_decision_clock']['boot_id'] = str(uuid.uuid4())
            journal.write_bytes(local_gpu_pool._encode(retained))
            assert cli.main(command) == 2
            assert 'original pool boot' in capsys.readouterr().err

            original_ref.pop('owner_decision_clock')
            historical = local_gpu_pool._encode(retained) + b'\n'
            journal.write_bytes(historical)
            assert cli.main(command) == 0
            assert json.loads(capsys.readouterr().out) == {**receipt, 'release_ref': original_ref}
            assert journal.read_bytes() == historical
            journal.write_bytes(journal_raw)

            with _after_record_read(monkeypatch, Path(config['legacy_sentinel']),
                                    lambda _: proof.write_bytes(fingerprints[-1][0] + b' ')):
                assert cli.main(command) == 2
            assert 'proof raw identity changed' in capsys.readouterr().err
        finally:
            _stop_session(successor_owner, successor_pool)


@pytest.mark.parametrize('clock_fault', [None, 'unavailable', 'wrong-boot'])
def test_pending_conflict_waits_for_release_while_later_disjoint_work_runs(tmp_path, clock_fault):
    inject = ''
    if clock_fault is not None:
        inject = f'''
clock = local_gpu_pool.budget_clock._clock
release_code = local_gpu_pool._Session._release.__code__
fault_seen = inventory_path.with_name('clock-fault-observed')
fault_armed = inventory_path.with_name('clock-fault-armed')
def sample():
    if sys._getframe(1).f_code is release_code and fault_armed.exists() and not fault_seen.exists():
        fault_seen.touch()
        if {clock_fault!r} == 'unavailable':
            raise OSError('injected release decision clock unavailable')
        boot_id, ticks = clock()
        wrong_boot = ('1' if boot_id[0] == '0' else '0') + boot_id[1:]
        return wrong_boot, ticks
    return clock()
local_gpu_pool.budget_clock._clock = sample
'''
    with fake_pool(tmp_path / 'pool', count=2, _setup=inject) as (pool, config, pool_owner):
        shared, free = config['device_uuids']
        hold = ("import time;from pathlib import Path;Path('started').touch()\n"
                "while not Path('finish').exists():time.sleep(.01)")
        quick = "from pathlib import Path;Path('started').open('a').write('once\\n')"
        holder, original = _setup(tmp_path / 'holder', config, [shared], hold, wall=30, reserve=5)
        successor, pending = _setup(tmp_path / 'successor', config, [shared], quick, wall=30, reserve=5)
        independent, _ = _setup(tmp_path / 'independent', config, [free], quick, wall=30, reserve=5)
        inventory_path = tmp_path / 'pool' / 'fake-inventory.json'

        def request(task):
            return next((item for item in pool.inspect()['requests']
                         if item['origin']['operation_id'] == task['origin']['operation_id']), {})

        def set_reported_pids(pids):
            inventory = json.loads(inventory_path.read_bytes())
            inventory[0]['compute_pids'] = pids
            replacement = inventory_path.with_suffix('.next')
            replacement.write_text(json.dumps(inventory), encoding='utf-8')
            replacement.replace(inventory_path)

        with _owner(holder) as first:
            _until(lambda: (holder.parent / 'started').exists())
            held = request(original)
            assert held['state'] == 'consumed' and held['release_ref'] is None
            with _owner(successor) as waiting:
                _until(lambda: request(pending).get('state') == 'pending')
                with _owner(independent) as disjoint:
                    finished = _result(disjoint)
                assert finished['resource']['status'] == 'released'
                assert (independent.parent / 'started').read_text().splitlines() == ['once']
                assert request(pending)['state'] == 'pending'
                assert not (successor.parent / 'started').exists()

                set_reported_pids([os.getpid()])  # Synthetic inventory only.
                (holder.parent / 'finish').touch()
                stopped = pool.proof_directory(held['lease_id']) / 'stopped.json'
                _until(stopped.exists)
                assert json.loads(stopped.read_bytes())['process_result']['status'] == 'succeeded'

                def inventory_refuses_release():
                    result = pool.reconcile(held['lease_id'])
                    return result['status'] == 'unavailable' and 'not empty' in result['reason']

                _until(inventory_refuses_release)
                assert request(original)['release_ref'] is None
                assert request(pending)['state'] == 'pending'
                assert not (successor.parent / 'started').exists()

                if clock_fault is not None:
                    inventory_path.with_name('clock-fault-armed').touch()
                set_reported_pids([])
                for owner in (first, waiting):
                    result = _result(owner)
                    assert result['resource']['status'] == 'released'
                    assert result['guard_returncode'] == 0
        assert (successor.parent / 'started').read_text().splitlines() == ['once']
        release_ref = request(original)['release_ref']
        assert release_ref['sequence'] < request(pending)['consume_binding']['sequence']
        assert 'owner_decision_clock' in request(pending)['release_ref']
        if clock_fault is None:
            assert 'owner_decision_clock' in release_ref
        else:
            assert (tmp_path / 'pool' / 'clock-fault-observed').exists()
            assert 'owner_decision_clock' not in release_ref
            assert pool.release(held['lease_id'], release_ref['proof_ref'])['release_ref'] == release_ref
            assert pool.close()['mode'] == 'closed'
            assert pool_owner.wait(timeout=5) == 0
            archived = local_gpu_pool.observe_closed_release(config, pool.session['session_id'], held['lease_id'])
            assert archived['release_ref'] == release_ref


def test_guard_death_after_stopped_proof_keeps_unknown_even_when_nvml_empty(tmp_path):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, session):
        setup, _ = _setup(tmp_path / 'task', config, config['device_uuids'],
                          "import time;from pathlib import Path;Path('started').touch();time.sleep(.7)")
        inventory_path = tmp_path / 'pool' / 'fake-inventory.json'
        with _owner(setup) as owner:
            _until(lambda: (setup.parent / 'started').exists())
            rows = json.loads(inventory_path.read_text())
            rows[0]['compute_pids'] = [os.getpid()]  # Observation only; never a signal target.
            inventory_path.write_text(json.dumps(rows))
            request = pool.inspect()['requests'][0]
            proof = pool.proof_directory(request['lease_id']) / 'stopped.json'
            _until(proof.exists)
            guardian = json.loads(proof.read_text())['guard_identity']
            assert local_gpu_pool._children(guardian) == []
            processes.notify_identity(guardian, signal.SIGKILL)
            result = _result(owner)
        assert result['guard_returncode'] == -signal.SIGKILL
        rows[0]['compute_pids'] = []
        inventory_path.write_text(json.dumps(rows))
        observed = pool.reconcile(request['lease_id'])
        assert observed['status'] == 'unknown'
        assert observed['release_ref'] is None
        assert observed['missing_evidence']
        assert pool.close()['mode'] == 'draining'


def test_original_live_guard_releases_after_same_session_recovery_and_pool_accepts_new_work(tmp_path):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, session):
        setup, original = _setup(tmp_path / 'original', config, config['device_uuids'],
            "import time;from pathlib import Path;Path('started').open('a').write('once\\n');time.sleep(30)")
        restarted = None
        current = None
        try:
            with _owner(setup) as owner:
                _until(lambda: (setup.parent / 'started').exists())
                session.kill()
                session.communicate(timeout=5)
                restarted = _start_session(tmp_path / 'pool', config, recover=pool.session['session_id'])
                current = _ready(config, restarted)
                result = _result(owner)
                assert result['resource']['status'] == 'released', result
            observation = current.inspect()
            assert observation['mode'] == 'active', observation
            assert observation['owner_epoch'] == 2
            assert observation['requests'][0]['origin']['clock'] == original['origin']['clock']
            assert (setup.parent / 'started').read_text() == 'once\n'
            successor, _ = _setup(tmp_path / 'successor', config, config['device_uuids'],
                                 "from pathlib import Path;Path('started').touch()")
            with _owner(successor) as owner:
                assert _result(owner)['resource']['status'] == 'released'
            assert (successor.parent / 'started').exists()
        finally:
            if restarted is not None:
                _stop_session(restarted, current)


@pytest.mark.parametrize('action,expected', [('request', 'granted'), ('consume', 'consumed'), ('stopped', 'released')])
def test_actual_resource_ack_loss_reconciles_original_without_another_payload_launch(tmp_path, action, expected):
    fault_code = f'''
import socket
original_handle=local_gpu_pool._Session._handle
def drop_ack(self,message,connection):
 result=original_handle(self,message,connection)
 if message['action']=={action!r} and result['status']=={expected!r} and not getattr(self,'test_ack_dropped',False):
  self.test_ack_dropped=True
  (inventory_path.parent/'ack-loss.json').write_text(json.dumps({{'action':message['action'],'status':result['status'],'sequence':result['sequence'],'request_id':result.get('request_id')}}))
  connection.socket.shutdown(socket.SHUT_RDWR)
 return result
local_gpu_pool._Session._handle=drop_ack
'''
    with fake_pool(tmp_path / 'pool', count=1, _setup=fault_code) as (pool, config, session):
        setup, original = _setup(tmp_path / 'task', config, config['device_uuids'],
                                 "from pathlib import Path;Path('started').open('a').write('once\\n')")
        with _owner(setup) as owner:
            result = _result(owner)
        lost = json.loads((tmp_path / 'pool' / 'ack-loss.json').read_text())
        assert lost['action'] == action and lost['status'] == expected
        requests = pool.inspect()['requests']
        assert len(requests) == 1 and requests[0]['request_id'] == lost['request_id']
        assert requests[0]['origin']['clock'] == original['origin']['clock']
        assert requests[0]['state'] in ('released', 'cancelled'), result
        marker = setup.parent / 'started'
        assert (marker.read_text().count('\n') if marker.exists() else 0) == (1 if action == 'stopped' else 0)
        assert result['guard_returncode'] == 0, result


@pytest.mark.parametrize('fault', ['prelaunch-stop', 'prelaunch-deadline'])
def test_consumed_resource_still_requires_live_prelaunch_permission_and_original_work_clock(tmp_path, fault):
    with fake_pool(tmp_path / 'pool', count=1) as (pool, config, session):
        setup, original = _setup(tmp_path / 'task', config, config['device_uuids'],
                                 "from pathlib import Path;Path('unexpected').touch()",
                                 wall=4 if fault == 'prelaunch-deadline' else 12,
                                 reserve=3)
        with _owner(setup, transport_fault=fault) as owner:
            result = _result(owner)
        assert (setup.parent / 'fault-observed').exists(), result
        assert not (setup.parent / 'unexpected').exists()
        request = pool.inspect()['requests'][0]
        assert request['consume_binding'] is not None
        assert request['state'] == 'released', result
        assert request['origin']['clock'] == original['origin']['clock']
        assert result['process_result']['returncode'] is None


@pytest.mark.parametrize('fault', ['wrong-nonce', 'timeout'])
def test_running_owner_channel_fault_cleans_original_tree_while_sibling_runs(tmp_path, fault):
    with fake_pool(tmp_path / 'pool', count=2) as (pool, config, session):
        code = "import time;from pathlib import Path;Path('started').touch();time.sleep(30);Path('late').touch()"
        setup, _ = _setup(tmp_path / 'task', config, config['device_uuids'][:1], code)
        sibling, _ = _setup(tmp_path / 'sibling', config, config['device_uuids'][1:], code)
        with _owner(sibling) as other:
            _until(lambda: (sibling.parent / 'started').exists())
            with _owner(setup, transport_fault=fault) as owner:
                result = _result(owner)
            assert (setup.parent / 'fault-observed').exists()
            assert result['resource']['status'] == 'released', result
            assert not (setup.parent / 'late').exists()
            assert other.poll() is None
            (sibling.parent / 'stop.requested').touch()
            assert _result(other)['resource']['status'] == 'released'


@pytest.mark.parametrize('state', ['granted', 'consumed', 'released'])
@pytest.mark.parametrize('boundary', ['before-replace', 'after-replace-before-directory-fsync'])
def test_uncertain_resource_commit_keeps_original_identity_and_never_reexecutes(tmp_path, state, boundary):
    fault_code = f'''
original_publish=local_gpu_pool._publish
original_replace=local_gpu_pool.os.replace
original_sync=local_gpu_pool._sync
fault_active=False
fault_fired=False
def fail_boundary():
 global fault_active,fault_fired
 fault_active=False;fault_fired=True
 (inventory_path.parent/'commit-fault.json').write_text(json.dumps({{'state':{state!r},'boundary':{boundary!r}}}))
 raise OSError('injected original journal commit boundary')
def replace(source,target):
 if fault_active and {boundary!r}=='before-replace':fail_boundary()
 return original_replace(source,target)
def sync(directory):
 if fault_active and {boundary!r}=='after-replace-before-directory-fsync':fail_boundary()
 return original_sync(directory)
def publish(path,value,**options):
 global fault_active
 selected=path.name=='journal.json' and any(request['state']=={state!r} for request in value.get('requests',[]))
 fault_active=selected and not fault_fired
 if fault_active and {state!r}=='released':
  release=next(request['release_ref'] for request in value['requests'] if request['state']=='released')
  (inventory_path.parent/'release-candidate.json').write_text(json.dumps(release))
 try:return original_publish(path,value,**options)
 finally:fault_active=False
local_gpu_pool.os.replace=replace
local_gpu_pool._sync=sync
local_gpu_pool._publish=publish
'''
    with fake_pool(tmp_path / 'pool', count=1, _setup=fault_code) as (pool, config, session):
        setup, original = _setup(tmp_path / 'task', config, config['device_uuids'],
                                 "from pathlib import Path;Path('started').open('a').write('once\\n')")
        with _owner(setup) as owner:
            result = _result(owner)
        assert json.loads((tmp_path / 'pool' / 'commit-fault.json').read_text()) == {'state': state, 'boundary': boundary}
        requests = pool.inspect()['requests']
        assert len(requests) == 1
        assert requests[0]['state'] == 'released', result
        assert requests[0]['origin']['clock'] == original['origin']['clock']
        assert requests[0]['origin']['attempt_ref'] == original['origin']['attempt_ref']
        marker = setup.parent / 'started'
        assert (marker.read_text().count('\n') if marker.exists() else 0) == (0 if state == 'consumed' else 1)
        assert result['guard_returncode'] == 0, result
        if state == 'released':
            candidate = json.loads((tmp_path / 'pool' / 'release-candidate.json').read_bytes())
            accepted = requests[0]['release_ref']
            assert accepted == result['resource']['release_ref']
            assert pool.release(requests[0]['lease_id'], accepted['proof_ref'])['release_ref'] == accepted
            if boundary == 'before-replace':
                assert accepted['owner_decision_clock']['boottime_ns'] > candidate['owner_decision_clock']['boottime_ns']
            else:
                assert accepted == candidate
