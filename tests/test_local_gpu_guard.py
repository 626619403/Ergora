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

from ergora import budget_clock, local_gpu_guard, local_gpu_pool, processes
from test_local_gpu_pool import fake_pool, _after_record_read, _ready, _start_session, _stop_session


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
from ergora import local_gpu_guard as guard,local_gpu_pool as pool
spec=importlib.util.spec_from_file_location('original_fixture_owner',sys.argv[1])
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
setup=Path(sys.argv[2]);fault=sys.argv[3];value=json.loads(setup.read_text())
original=guard._wire;phase=None;fired=False
def wire(connection,deadline,*,value=None):
 global phase,fired
 if value is None:
  message=original(connection,deadline)
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
            state = pool.inspect()['requests'][1]['state']
            assert state in ('expired', 'cancelled') if stop_kind == 'deadline' else state == 'cancelled'
            assert first.poll() is None, 'Stopping one original task must leave its sibling running'
            (holder.parent / 'release').touch()
            assert _result(first)['resource']['status'] == 'released'


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
