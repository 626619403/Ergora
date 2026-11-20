"""Controller admission, recovery, and independent candidate root lifecycles."""

import ergora.training.runtime.evidence as execution_evidence
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from ergora._paths import IMPORT_ROOT, PACKAGE_ROOT
import ergora.native.resources as native_resources
import ergora.training.native as training_native
import ergora
import ergora.training.application as training
from test_training_runtime import cycle_workflow
from test_training_evidence import f1_cpu_snapshot
from test_training_submission import (
    controller_admission, controller_dispatch, cycle_budget_root, cycle_candidate, cycle_operation_fault, cycle_sdk_activity,
    cycle_selection, experiments, historical_execution, installation, native_budget_create, prepared,
    recorded_process_is_active, registration, run_cycle_candidate, save_controller_binding,
    saved_controller_intent, service, stop_controller_test_owner, wait_budget_stopped,
)


def admission_process(admission, tmp_path, mode, *, reason='First controller stop'):
    import ergora

    marker = tmp_path / (mode + '-ready')
    child = subprocess.Popen([sys.executable, '-I', '-S', '-B',
        str(Path(__file__).parent / 'fixtures/training_cycle_admission.py'),
        str(Path(ergora.__file__).parent.parent), str(admission.directory), str(marker), mode, reason],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    until = time.monotonic() + 10
    while time.monotonic() < until and not marker.exists() and child.poll() is None:
        time.sleep(.01)
    if not marker.exists():
        child.kill()
        stdout, stderr = child.communicate(timeout=5)
        raise AssertionError('Parent admission child did not reach its real boundary: ' + stdout + stderr)
    return child



@pytest.mark.skipif(sys.platform != 'linux', reason='Original supervisor identity and stopped frames require Linux')
def test_expired_cycle_supervisor_is_dependency_isolated_and_never_spawns_h(
        controller_admission, tmp_path):
    import shutil
    import ergora.training.runtime.worker as worker
    import ergora.training.execution_protocol as protocol

    state, _, _, authorized, _ = controller_admission
    operation = worker._CycleOperation(state.root, 'demo', 'controller', authorized['authorization_sha256'], 'inspect')
    payload = deepcopy(operation.payload)
    now = time.clock_gettime_ns(time.CLOCK_BOOTTIME)
    payload['bootstrap'].update(started_ns=now - 2_000_000_000, deadline_ns=now - 1_000_000_000)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    isolated = tmp_path / 'pure-package'
    shutil.copytree(PACKAGE_ROOT, isolated / 'ergora',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
    environment = dict(os.environ, PYTHONPATH=str(isolated), PYTHONDONTWRITEBYTECODE='1')
    program = """import subprocess,sys
from ergora.training.execution_protocol import cycle_supervisor_main
def forbidden_spawn(*args,**kwargs):
    raise AssertionError('An expired original supervisor cannot spawn H')
subprocess.Popen=forbidden_spawn
cycle_supervisor_main()
assert all(name not in sys.modules for name in
           ('temporalio','jsonschema','ergora.storage.state','ergora.training.cycles','ergora.training.runtime.worker'))
"""
    result = subprocess.run([sys.executable, '-S', '-P', '-B', '-c', program], input=raw,
                            env=environment, capture_output=True, timeout=8)
    assert result.returncode == 0, result.stderr
    frames = [json.loads(line) for line in result.stdout.splitlines()]
    assert [frame['event'] for frame in frames] == ['stopped', 'result']
    assert frames[0]['process']['status'] == 'cancelled'
    assert frames[1]['result']['status'] == 'unknown'
    assert (operation.output / 'request.json').read_bytes() == raw


@pytest.mark.skipif(sys.platform != 'linux', reason='Original independent root and initialization locks require Linux')
@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.parametrize('pending,fault', [
    pytest.param('before', 'ready', id='missing'), pytest.param('after', 'ready', id='initializing'),
    pytest.param('after', 'foreign', id='foreign'), pytest.param('after', 'malformed', id='malformed'),
    pytest.param('after', 'removed', id='removed'),
    pytest.param('after', 'stop', id='stop'), pytest.param('after', 'source', id='source'),
    pytest.param('after', 'dead', id='dead'), pytest.param('after', 'late-dead', id='late-dead')])
def test_confirm_waits_only_for_its_bound_original_owner(
        cycle_candidate, controller_admission, cycle_selection, cycle_operation_fault, service, monkeypatch, pending, fault):
    import asyncio
    import signal
    from ergora.runtime import processes

    _, _, _, _, admission = controller_admission
    runtime = cycle_selection[2]
    markers = cycle_operation_fault('candidate')
    service[0]('accepted', budget_scenario='owner-before-publish' if pending == 'before' else 'owner-initialization-held')
    monkeypatch.setenv('ERGORA_TEST_OWNER_CONFIRM', '1')
    if fault == 'late-dead':
        monkeypatch.setenv('ERGORA_TEST_OWNER_CONFIRM_LATE_CONTEXT', '1')
    candidate = cycle_candidate()
    prepared = asyncio.run(candidate.preparation.run())
    assert prepared['status'] == 'new_offer', prepared
    launch = prepared['launch']
    root = subprocess.Popen([sys.executable, '-P', '-c',
        'from ergora.training.runtime.submission import cycle_root_main;cycle_root_main()'], stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={**os.environ, **launch['environment']}, start_new_session=True)
    root_identity = processes.identity(root.pid)
    owner_path = runtime / 'ergora/training-submissions/alpha.budget/owner.json'
    descriptor = Path(cycle_selection[1]['execution']['installation']) / 'ergora-native-runtime.json'
    owner_raw, descriptor_raw = None, None
    try:
        root.stdin.write(json.dumps(launch['request'], ensure_ascii=False, separators=(',', ':')).encode())
        root.stdin.close()
        until = time.monotonic() + 10
        while not (markers / 'owner-held').exists() and root.poll() is None and time.monotonic() < until:
            time.sleep(.01)
        assert (markers / 'owner-held').exists(), 'The real root must hold its original initialization lock'
        held = json.loads((markers / 'owner-held').read_bytes())
        assert held['root'] == root_identity and held['entry'] == 'cycle_root_main'
        assert held['imports'] == []
        if owner_path.exists():
            owner_raw = owner_path.read_bytes()
        if fault == 'foreign':
            value = json.loads(owner_raw)
            value.update(processes.identity(os.getpid()))
            owner_path.write_text(json.dumps(value))
        elif fault == 'malformed':
            owner_path.write_bytes(b'{')
        confirm = candidate.next_operation('confirm-candidate',
            intent_sha256=prepared['intent_sha256'], root_process=root_identity)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, confirm.run())
            try:
                if fault in ('foreign', 'malformed'):
                    result = future.result(timeout=8)
                    assert result['status'] == 'unknown', result
                    assert not (markers / 'owner-release').exists()
                else:
                    marker = markers / ('confirm-missing-reads' if pending == 'before' else 'confirm-owner-reads')
                    needed = 4 if pending == 'before' else 2
                    until = time.monotonic() + 10
                    while not future.done() and time.monotonic() < until:
                        if marker.exists() and json.loads(marker.read_bytes())['count'] >= needed:
                            break
                        time.sleep(.01)
                    assert marker.exists() and json.loads(marker.read_bytes())['count'] >= needed, (
                        future.result() if future.done() else 'The same H must observe the real pending owner again')
                    waiting = json.loads(marker.read_bytes())
                    assert waiting['operation_id'] == confirm.identity['operation_id']
                    assert not future.done()
                    if fault == 'stop':
                        admission.request_stop('Stop while original owner initializes')
                    elif fault == 'source':
                        descriptor_raw = descriptor.read_bytes()
                        descriptor.write_bytes(descriptor_raw + b'\n')
                    elif fault == 'removed':
                        owner_path.unlink()
                    elif fault == 'dead':
                        processes.notify_identity(root_identity, signal.SIGKILL)
                        root.wait(timeout=5)
                    else:
                        (markers / 'owner-release').touch()
                        if fault == 'late-dead':
                            until = time.monotonic() + 8
                            while not (markers / 'confirm-last-context').exists() and not future.done() and time.monotonic() < until:
                                time.sleep(.01)
                            assert (markers / 'confirm-last-context').exists()
                            processes.notify_identity(root_identity, signal.SIGKILL)
                            root.wait(timeout=5)
                            (markers / 'confirm-context-release').touch()
                    result = future.result(timeout=8)
                    assert result['status'] == ('owner_confirmed' if fault == 'ready' else 'unknown'), result
                    if fault == 'ready':
                        assert {key: result['owner'][key] for key in root_identity} == root_identity
                assert result['operation_id'] == confirm.identity['operation_id']
                assert result['operation_stopped'] is True
                assert sum(json.loads(path.read_bytes())['identity']['mode'] == 'confirm-candidate'
                           for path in (admission.directory.parents[2] / 'operations/training-cycles').glob('*/request.json')) == 1
            finally:
                if owner_raw is not None:
                    owner_path.write_bytes(owner_raw)
                if descriptor_raw is not None:
                    descriptor.write_bytes(descriptor_raw)
                (markers / 'owner-release').touch()
                (markers / 'confirm-context-release').touch()
                (markers / 'owner-phase-release').touch()
        assert not (runtime / 'ergora/training-submissions/alpha.attempt.json').exists()
    finally:
        if owner_raw is not None:
            owner_path.write_bytes(owner_raw)
        if descriptor_raw is not None:
            descriptor.write_bytes(descriptor_raw)
        (markers / 'owner-release').touch()
        (markers / 'confirm-context-release').touch()
        (markers / 'owner-phase-release').touch()
        try:
            if root.poll() is None:
                processes.notify_identity(root_identity, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        try:
            root.wait(timeout=25)
        finally:
            if root.stdin is not None and not root.stdin.closed:
                root.stdin.close()




@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_controller_birth_consent_retains_original_actor_clock_and_mode(controller_admission, monkeypatch):
    import ergora.training.cycles as training_cycles

    state, source, selected, authorized, admission = controller_admission
    authorization = authorized['authorization']
    assert authorized['status'] == 'ready' and authorization['schema_version'] == 5
    assert authorized['controller']['consent_recorded'] is True
    assert authorized['coverage']['execution_authorized'] is False
    controller = authorization['controller']
    assert controller['actor_id'] == f'unix:{os.getuid()}:{training_cycles.getpass.getuser()}'
    identity = {key: authorization[key] for key in ('control_home', 'project', 'cycle_id', 'input_sha256')}
    assert controller == {'protocol': 'ergora-training-cycle-v3',
        'workflow_id': 'ergora-training-cycle-v3/' + training_cycles._sha(identity),
        'task_queue': 'ergora-training-cycle-v3', 'execution_scope': 'ordered-selected-native-once',
        'continuation': 'accepted-archive-pass', 'actor_id': controller['actor_id'], 'confirmation': True}
    assert authorization['sha256'] == training_cycles._sha({k: v for k, v in authorization.items() if k != 'sha256'})
    save_controller_binding(admission)
    original = {p: p.read_bytes() for p in admission.directory.rglob('*') if p.is_file()}
    monkeypatch.setattr(training_cycles.getpass, 'getuser', lambda: 'different-observer')
    again = training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert again['authorization'] == authorization and again['work_remaining_seconds'] < authorized['work_remaining_seconds']
    with pytest.raises(ValueError, match='consent mode'):
        training_cycles.authorize(state, 'demo', 'controller', source, selected['sha256'], 1, confirm=True)
    manual = training_cycles.authorize(state, 'demo', 'manual', source, selected['sha256'], 1, confirm=True)
    assert manual['authorization']['schema_version'] == 1 and 'controller' not in manual
    assert not (admission.directory.parent / 'manual/controller').exists()
    manual_original = {p: p.read_bytes() for p in (admission.directory.parent / 'manual').rglob('*') if p.is_file()}
    assert all(p.read_bytes() == raw for p, raw in manual_original.items())
    with pytest.raises(ValueError, match='consent mode'):
        training_cycles.authorize_controller(state, 'demo', 'manual', source, selected['sha256'], 1,
            confirm=True, execute_selected=True)
    for flag in (False, 1):
        with pytest.raises(ValueError, match='Explicitly confirm execution'):
            training_cycles.authorize_controller(state, 'demo', 'unconfirmed', source, selected['sha256'], 1,
                confirm=True, execute_selected=flag)
    assert not (admission.directory.parent / 'unconfirmed').exists()
    assert all(p.read_bytes() == raw for p, raw in original.items())
    # A recomputed digest cannot legitimize a nonboolean confirmation.
    altered = deepcopy(authorization)
    altered['controller']['confirmation'] = 1
    altered['sha256'] = training_cycles._sha({k: v for k, v in altered.items() if k != 'sha256'})
    (admission.directory / 'authorization.json').write_text(json.dumps(altered))
    with pytest.raises(ValueError, match='canonical SHA256'):
        training_cycles.status(state, 'demo', 'controller')


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller CLI uses original Linux consent, locks and clock')
def test_controller_cli_records_consent_then_reads_prepares_and_stops_without_sdk(
        cycle_selection, tmp_path, monkeypatch):
    from contextlib import redirect_stderr, redirect_stdout
    import io
    import ergora.training.cycles as training_cycles
    from ergora.interfaces.cli import main

    state, definition, runtime, _, _, request = cycle_selection
    source = tmp_path / 'cli-input'
    selected = training_cycles.create(state, 'demo', request, source)

    def invoke(arguments):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(['--home', str(state.root), 'training', *arguments])
        return code, json.loads(out.getvalue()) if out.getvalue() else None, err.getvalue()

    args = ['cycle-authorize-controller', 'demo', 'cli-controller', '--directory', str(source),
            '--sha256', selected['sha256'], '--revision', '1', '--confirm']
    assert invoke(args)[0] != 0
    directory = state.root / 'training-cycles/demo/cli-controller'
    assert not directory.exists(), 'Missing execution consent cannot reserve an ID or start its clock'
    code, authorized, _ = invoke([*args, '--execute-selected'])
    assert code == 0 and authorized['authorization']['schema_version'] == 5
    original = (directory / 'authorization.json').read_bytes()
    digest = authorized['authorization_sha256']
    common = ['demo', 'cli-controller', '--authorization-sha256', digest]
    code, prepared, _ = invoke(['cycle-controller-prepare', *common, '--revision', '1'])
    assert code == 0 and prepared['created'] is True
    intent = directory / 'controller/intent.json'
    preserved = intent.read_bytes(), intent.stat().st_ino
    assert invoke(['cycle-controller-prepare', *common, '--revision', '1'])[1]['created'] is False
    assert (intent.read_bytes(), intent.stat().st_ino) == preserved
    installation = Path(definition['execution']['installation'])
    moved = installation.with_name(installation.name + '-unavailable')
    installation.rename(moved)
    try:
        with monkeypatch.context() as missing:
            missing.setitem(sys.modules, 'temporalio', None)
            code, stored, _ = invoke(['cycle-controller-status', *common])
            assert code == 0 and stored['status'] == 'prepared'
            assert stored['read_only'] is True and stored['runtime_status'] == 'not_queried'
            assert stored['execution_authorized'] is False
            code, stopped, _ = invoke(['cycle-controller-stop', *common, '--reason', 'Explicit local stop'])
            assert code == 0 and stopped['stop_visible'] is True and stopped['stop_durable'] is True
            assert stopped['executor_stop_confirmed'] is None
    finally:
        moved.rename(installation)
    assert (directory / 'authorization.json').read_bytes() == original
    assert (intent.read_bytes(), intent.stat().st_ino) == preserved
    assert not (directory / 'controller/attempt.json').exists()
    assert not (runtime / 'training/jobs/alpha').exists()



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
@pytest.mark.parametrize('boundary', ['authorization-file', 'lock-file', 'lock-directory', 'ready-directory'])
def test_controller_lock_publication_recovers_only_the_original_consent(
        cycle_selection, tmp_path, monkeypatch, boundary):
    import ergora.training.cycles as training_cycles

    state, _, _, _, _, request = cycle_selection
    source = tmp_path / 'input'
    selected = training_cycles.create(state, 'demo', request, source)
    saved = state.root / 'training-cycles/demo/interrupted-controller'
    fsync, failed = os.fsync, []

    def interrupt(descriptor):
        path = Path('/proc/self/fd/' + str(descriptor)).resolve()
        targeted = ((boundary == 'authorization-file' and path.parent == saved and path.name.startswith('.pending-'))
            or (boundary == 'lock-file' and path.parent == saved / 'controller' and path.name.startswith('.pending-'))
            or (boundary == 'lock-directory' and path == saved / 'controller')
            or (boundary == 'ready-directory' and path == saved and (saved / 'ready.json').exists()))
        if targeted:
            failed.append(str(path))
            if boundary != 'authorization-file':
                assert (saved / 'authorization.json').is_file() and (saved / 'cycle.json').is_file()
            if boundary != 'ready-directory':
                assert not (saved / 'ready.json').exists()
            raise OSError('Interrupted original controller publication')
        return fsync(descriptor)

    monkeypatch.setattr(os, 'fsync', interrupt)
    with pytest.raises(OSError, match='Interrupted original controller publication'):
        training_cycles.authorize_controller(state, 'demo', 'interrupted-controller', source, selected['sha256'], 1,
            confirm=True, execute_selected=True)
    assert failed
    original = {p: p.read_bytes() for p in saved.rglob('*') if p.is_file()}
    if boundary == 'authorization-file':
        assert saved.is_dir() and not (saved / 'authorization.json').exists()
        monkeypatch.setattr(os, 'fsync', fsync)
        monkeypatch.setattr(training_cycles.budget_clock, 'authorize',
            lambda *args: pytest.fail('A reserved ID cannot receive another clock'))
        with pytest.raises(FileNotFoundError):
            training_cycles.authorize_controller(state, 'demo', 'interrupted-controller', source, selected['sha256'], 1,
                confirm=True, execute_selected=True)
        assert all(p.read_bytes() == raw for p, raw in original.items())
        return
    measurement_reader = training_cycles._measurement_sources
    monkeypatch.setattr(training_cycles, '_measurement_sources',
        lambda: pytest.fail('Recovery must not recapture the measurement source map'))
    monkeypatch.setattr(training_cycles.budget_clock, 'authorize',
        lambda *args: pytest.fail('Recovery must not issue another clock'))
    observed = training_cycles.status(state, 'demo', 'interrupted-controller')
    assert observed['status'] == ('unknown' if boundary == 'ready-directory' else 'pending')
    monkeypatch.setattr(os, 'fsync', fsync)
    current_reads = []

    def read_current_sources():
        sources = measurement_reader()
        current_reads.append(sources)
        return sources

    pending_measurement_validation = boundary in ('lock-file', 'lock-directory')
    if pending_measurement_validation:
        monkeypatch.setattr(training_cycles, '_measurement_sources', read_current_sources)
    recovered = training_cycles.authorize_controller(state, 'demo', 'interrupted-controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert recovered['status'] == 'ready' and recovered['authorization'] == observed['authorization']
    assert bool(current_reads) is pending_measurement_validation
    assert all(sources == observed['authorization']['measurement_sources'] for sources in current_reads)
    assert recovered['ready']['authorization_sha256'] == observed['authorization']['sha256']
    assert (saved / 'controller/admission.lock').read_bytes() == b''
    assert all(p.read_bytes() == raw for p, raw in original.items())



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_controller_ready_never_recreates_or_accepts_a_changed_parent_lock(controller_admission, tmp_path):
    import ergora.training.cycles as training_cycles

    state, source, selected, _, admission = controller_admission
    outside = tmp_path / 'outside-lock'
    outside.write_bytes(b'External lock must remain unchanged')
    for shape in ('missing', 'nonempty', 'fifo', 'symlink'):
        admission.lock.unlink(missing_ok=True)
        if shape == 'nonempty':
            admission.lock.write_bytes(b'x')
        elif shape == 'fifo':
            os.mkfifo(admission.lock)
        elif shape == 'symlink':
            admission.lock.symlink_to(outside)
        with pytest.raises((OSError, ValueError)):
            training_cycles.status(state, 'demo', 'controller')
        with pytest.raises((OSError, ValueError)):
            training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 1,
                confirm=True, execute_selected=True)
        if shape == 'missing':
            assert not admission.lock.exists()
    assert outside.read_bytes() == b'External lock must remain unchanged'



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_controller_lock_sync_consumes_the_original_computation_window(cycle_selection, tmp_path, monkeypatch):
    import ergora.training.cycles as training_cycles
    from ergora.runtime import budget_clock

    state, _, _, _, _, request = cycle_selection
    request['budget'].update(wall_seconds=4, cleanup_seconds=1)
    source = tmp_path / 'input'
    selected = training_cycles.create(state, 'demo', request, source)
    saved = state.root / 'training-cycles/demo/slow-controller'
    fsync, delayed = os.fsync, []

    def slow(descriptor):
        if Path('/proc/self/fd/' + str(descriptor)).resolve() == saved / 'controller' and not delayed:
            delayed.append(True)
            authorization = json.loads((saved / 'authorization.json').read_bytes())
            remaining = budget_clock.remaining(authorization['clock'], request['budget']['wall_seconds'],
                request['budget']['cleanup_seconds'])
            time.sleep(max(0, remaining) + .05)
        return fsync(descriptor)

    monkeypatch.setattr(os, 'fsync', slow)
    result = training_cycles.authorize_controller(state, 'demo', 'slow-controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert delayed and result['status'] == 'exhausted' and result['work_remaining_seconds'] <= 0
    assert not (saved / 'ready.json').exists()
    original = (saved / 'authorization.json').read_bytes()
    again = training_cycles.authorize_controller(state, 'demo', 'slow-controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert again['authorization'] == result['authorization'] and (saved / 'authorization.json').read_bytes() == original



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
@pytest.mark.parametrize('boundary', ['create', 'file-fsync', 'directory-fsync'])
def test_controller_visible_stop_denies_new_work_before_durable_confirmation(controller_admission, tmp_path, boundary):
    import ergora.training.cycles as training_cycles

    state, _, _, authorized, admission = controller_admission
    child = admission_process(admission, tmp_path, boundary)
    try:
        observed = admission.observe()
        assert observed['stop_visible'] is True and observed['stop_durable'] is None
        assert observed['identity_matches'] is (boundary != 'create')
        assert observed['executor_stop_confirmed'] is None
        with pytest.raises(ValueError, match='stop is visible'):
            with admission.permission():
                pytest.fail('Visible parent stop must veto new work')
        stdout, stderr = child.communicate('\n', timeout=10)
        assert child.returncode == 0, stderr
        first = json.loads(stdout)
        assert first['stop_durable'] is True and first['admission_drained'] is True
        raw = admission.stop.read_bytes()
        again = training_cycles.stop_controller(state, 'demo', 'controller', authorized['authorization_sha256'], reason='Later reason')
        assert again['record'] == first['record'] and admission.stop.read_bytes() == raw
        assert again['executor_stop_confirmed'] is None
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=5)



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_parent_drain_waits_for_all_original_shared_permits(controller_admission, tmp_path):
    import ergora.training.cycles as training_cycles

    state, _, _, authorized, admission = controller_admission
    children = []
    try:
        for number in range(2):
            folder = tmp_path / str(number)
            folder.mkdir()
            children.append(admission_process(admission, folder, 'hold'))
        stopped = training_cycles.stop_controller(state, 'demo', 'controller', authorized['authorization_sha256'], reason='Stop active permits')
        raw = admission.stop.read_bytes()
        assert stopped['stop_durable'] is True and stopped['admission_drained'] is None
        assert stopped['executor_stop_confirmed'] is None
        for number, child in enumerate(children):
            stdout, stderr = child.communicate('\n', timeout=5)
            assert child.returncode == 0 and json.loads(stdout)['released'], stderr
            drained = admission.observe(drain=True)
            assert drained['admission_drained'] is (True if number == len(children) - 1 else None)
            assert drained['executor_stop_confirmed'] is None
        assert admission.stop.read_bytes() == raw
        assert training_cycles.status(state, 'demo', 'controller')['status'] == 'stopped'
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
@pytest.mark.parametrize('boundary', ['file', 'directory'])
def test_controller_stop_durability_recovers_by_synchronizing_the_same_original(controller_admission, monkeypatch, boundary):
    _, _, _, _, admission = controller_admission
    fsync = os.fsync

    def failing(descriptor):
        target = admission.stop if boundary == 'file' else admission.folder
        if Path('/proc/self/fd/' + str(descriptor)).resolve() == target:
            raise OSError('Controller stop storage synchronization failed')
        return fsync(descriptor)

    monkeypatch.setattr(os, 'fsync', failing)
    result = admission.request_stop('Original stop during storage failure')
    original, details = admission.stop.read_bytes(), admission.stop.stat()
    assert result['stop_visible'] is True and result['identity_matches'] is True
    assert result['stop_durable'] is None and result['admission_drained'] is None
    again = admission.request_stop('Later request must not replace it')
    assert again['stop_durable'] is None and again['record'] == result['record']
    monkeypatch.setattr(os, 'fsync', fsync)
    recovered = admission.observe(drain=True)
    assert recovered['stop_durable'] is True and recovered['admission_drained'] is True
    assert recovered['record'] == result['record'] and admission.stop.read_bytes() == original
    assert admission.stop.stat().st_ino == details.st_ino
    assert recovered['executor_stop_confirmed'] is None



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_stop_binds_the_complete_saved_controller_intent(controller_admission):
    import ergora.training.cycles as training_cycles

    _, _, _, _, admission = controller_admission
    intent = saved_controller_intent(admission)
    saved = admission.folder / 'intent.json'
    saved.write_text(json.dumps({**intent, 'workflow_input': {**intent['workflow_input'], 'input_sha256': '0' * 64}}))
    with pytest.raises(ValueError, match='complete original authorization'):
        admission.request_stop('Cannot bind a different complete input')
    assert not admission.stop.exists()
    saved.write_text(json.dumps(intent))
    result = admission.request_stop('Original bound intent')
    assert result['record']['controller_intent_sha256'] == training_cycles._sha(intent)
    assert result['stop_durable'] is True
    original = admission.stop.read_bytes()
    saved.write_text(json.dumps({**intent, 'workflow_id': 'different-controller'}))
    changed = admission.observe(drain=True)
    assert changed['stop_visible'] is True and changed['identity_matches'] is False
    assert changed['stop_durable'] is None and changed['admission_drained'] is None
    assert admission.stop.read_bytes() == original



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller preparation requires original Linux clocks and flock')
def test_controller_intent_preparation_retains_original_publication_and_clock(controller_admission, monkeypatch):
    import ergora.training.cycles as training_cycles
    from ergora.storage.state import file_lock

    state, _, _, authorized, admission = controller_admission
    original = {p: p.read_bytes() for p in admission.directory.rglob('*') if p.is_file()}
    arguments = (state, 'demo', 'controller', authorized['authorization_sha256'], authorized['project_revision'])
    with pytest.raises(ValueError, match='exact original authorization'):
        training_cycles.prepare_controller(state, 'demo', 'controller', None, authorized['project_revision'])
    # A visible ready link is still pending while its publisher owns the lock.
    with file_lock(admission.directory.parent / '.controller.lock'):
        with pytest.raises(ValueError, match='in progress'):
            training_cycles.prepare_controller(*arguments)
    assert not (admission.folder / 'intent.json').exists()
    prepared = training_cycles.prepare_controller(*arguments)
    assert prepared['created'] is True and prepared['cycle']['status'] == 'ready'
    assert prepared['intent'] == saved_controller_intent(admission)
    assert prepared['intent_sha256'] == training_cycles._sha(prepared['intent'])
    path = admission.folder / 'intent.json'
    raw, inode, sync = path.read_bytes(), path.stat().st_ino, training_cycles._sync_directory

    def fail(directory):
        if directory == admission.folder:
            raise OSError('Controlled controller directory synchronization failure')
        return sync(directory)

    monkeypatch.setattr(training_cycles, '_sync_directory', fail)
    with pytest.raises(OSError, match='synchronization failure'):
        training_cycles.prepare_controller(*arguments)
    monkeypatch.setattr(training_cycles, '_sync_directory', sync)
    again = training_cycles.prepare_controller(*arguments)
    assert again['created'] is False and again['intent'] == prepared['intent']
    assert again['cycle']['authorization'] == authorized['authorization']
    assert again['cycle']['work_remaining_seconds'] < prepared['cycle']['work_remaining_seconds']
    assert path.read_bytes() == raw and path.stat().st_ino == inode
    assert {p: p.read_bytes() for p in admission.directory.rglob('*') if p.is_file()} == {**original, path: raw}



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller preparation requires original Linux clocks and flock')
def test_controller_intent_stop_before_link_preserves_the_original_veto(controller_admission, monkeypatch):
    import ergora.training.cycles as training_cycles

    state, _, _, authorized, admission = controller_admission
    link, stopped = os.link, []

    def stop(source, destination, *args, **kwargs):
        if destination == admission.folder / 'intent.json':
            stopped.append(admission.request_stop('Stop while the original intent is being published'))
        return link(source, destination, *args, **kwargs)

    monkeypatch.setattr(os, 'link', stop)
    arguments = (state, 'demo', 'controller', authorized['authorization_sha256'], authorized['project_revision'])
    with pytest.raises(ValueError, match='stop is visible'):
        training_cycles.prepare_controller(*arguments)
    assert len(stopped) == 1 and stopped[0]['record']['controller_intent_sha256'] is None
    original = {p: p.read_bytes() for p in admission.folder.iterdir()}
    changed = admission.observe(drain=True)
    assert changed['stop_visible'] is True and changed['identity_matches'] is False
    with pytest.raises(ValueError):
        training_cycles.prepare_controller(*arguments)
    assert {p: p.read_bytes() for p in admission.folder.iterdir()} == original
    assert not (admission.folder / 'attempt.json').exists()



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller preparation requires original Linux clocks and flock')
@pytest.mark.parametrize('controller_admission', [{'wall_seconds': 12, 'cleanup_seconds': 3}], indirect=True)
@pytest.mark.parametrize('boundary', ['directory', 'final-check', 'stop-observation'])
def test_controller_intent_io_consumes_the_original_computation_window(controller_admission, monkeypatch, boundary):
    import ergora.training.cycles as training_cycles
    from ergora.training.execution_protocol import CycleAdmission

    state, _, selected, authorized, admission = controller_admission
    sync, delayed = training_cycles._sync_directory, []
    original_check, original_observe = CycleAdmission._authorization, CycleAdmission.observe
    policy = selected['budget']

    def exhaust(selected_boundary):
        if selected_boundary == boundary and (admission.folder / 'intent.json').exists() and not delayed:
            delayed.append(True)
            remaining = training_cycles.budget_clock.remaining(authorized['authorization']['clock'], policy['wall_seconds'])
            time.sleep(max(0, remaining - policy['cleanup_seconds']) + .05)

    def synchronize(directory):
        if directory == admission.folder:
            exhaust('directory')
        return sync(directory)

    def check(candidate):
        original_check(candidate)
        exhaust('final-check')

    def observe(candidate, **options):
        result = original_observe(candidate, **options)
        exhaust('stop-observation')
        return result

    monkeypatch.setattr(training_cycles, '_sync_directory', synchronize)
    monkeypatch.setattr(CycleAdmission, '_authorization', check)
    monkeypatch.setattr(CycleAdmission, 'observe', observe)
    arguments = (state, 'demo', 'controller', authorized['authorization_sha256'], authorized['project_revision'])
    prepared = training_cycles.prepare_controller(*arguments)
    assert delayed == [True] and prepared['cycle']['status'] == 'exhausted'
    assert prepared['cycle']['work_remaining_seconds'] <= 0
    assert prepared['cycle']['authorization'] == authorized['authorization']
    original = {p: p.read_bytes() for p in admission.directory.rglob('*') if p.is_file()}
    with pytest.raises(ValueError, match='deadline has passed'):
        training_cycles.prepare_controller(*arguments)
    assert {p: p.read_bytes() for p in admission.directory.rglob('*') if p.is_file()} == original



@pytest.mark.parametrize('controller_admission,installation', [
    ({'control_timeout_seconds': 30}, None),
    ({'control_timeout_seconds': 30}, 'managed')], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Independent original roots require Linux/WSL2')
def test_cycle_candidate_root_survives_short_calls_and_normal_loop_shutdown(
        controller_admission, cycle_selection, cycle_candidate, cycle_budget_root, service, monkeypatch):
    import asyncio
    import ergora.training.runtime.worker as worker
    import ergora.training.execution_protocol as protocol

    state, _, _, authorized, admission = controller_admission
    runtime = cycle_selection[2]
    original = (admission.directory / 'authorization.json').read_bytes()
    contenders = [cycle_candidate(), cycle_candidate()]
    operation = contenders[0]
    try:
        def forbidden(*args, **kwargs):
            raise AssertionError('The async parent must not enter business storage')

        async def compete():
            return await asyncio.gather(*(item.run() for item in contenders))

        with monkeypatch.context() as boundary:
            boundary.setattr(worker.State, 'connect', forbidden)
            boundary.setattr(protocol, 'read_raw', forbidden)
            outcomes = asyncio.run(compete())
        assert sum(item.spawning is not None for item in contenders) == 1
        position = next(index for index, item in enumerate(contenders) if item.spawning is not None)
        operation, result = contenders[position], outcomes[position]
        assert outcomes[1 - position]['status'] == 'observed' and 'launch' not in outcomes[1 - position]
        assert result['status'] == 'observed', result
        assert result['submission']['status'] == 'submitted'
        assert operation.handed_off is True and operation.root.poll() is None
        assert cycle_budget_root == [
            'from ergora.training.runtime.submission import cycle_root_main;cycle_root_main()'
            if admission.authorization['schema_version'] == 5
            else 'from ergora.training.runtime.worker import budget_main;budget_main()']
        owner = result['confirmation']['owner']
        assert recorded_process_is_active(owner)
        requests = [json.loads((Path(result[name]['output']) / 'request.json').read_bytes())
                    for name in ('preparation', 'confirmation')]
        requests.append(json.loads((Path(result['output']) / 'request.json').read_bytes()))
        assert all(p['bootstrap'] == requests[0]['bootstrap'] for p in requests)
        assert result['operation_stopped'] is True
        assert not worker._ROOT_OBSERVERS
        assert (admission.directory / 'authorization.json').read_bytes() == original
        before = json.loads(service[1].read_bytes())['starts']
        again = run_cycle_candidate(cycle_candidate)
        assert again['status'] == 'observed' and 'launch' not in again
        assert again['submission']['run_id'] == result['submission']['run_id']
        assert json.loads(service[1].read_bytes())['starts'] == before == 1
        assert operation.root.poll() is None and recorded_process_is_active(owner)
        assert owner['authorization_sha256'] == authorized['authorization_sha256']
    finally:
        stop_controller_test_owner(runtime)
        for contender in contenders:
            if contender.root is not None:
                contender.root.wait(timeout=5)


@pytest.mark.skipif(sys.platform != 'linux', reason='Original submission contention requires Linux flock')
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
def test_cycle_prepare_keeps_its_created_offer_during_duplicate_submission_contention(
        cycle_candidate, cycle_selection, cycle_operation_fault, service):
    import asyncio
    from ergora.storage.state import file_lock

    markers = cycle_operation_fault('candidate-prepare-return')
    operation = cycle_candidate()
    prefix = cycle_selection[2] / 'ergora/training-submissions'

    async def prepare():
        task = asyncio.create_task(operation.preparation.run())
        while (not (markers / 'candidate-prepared').exists() and not task.done()
               and not operation.preparation.expired()):
            await asyncio.sleep(.01)
        assert (markers / 'candidate-prepared').exists(), task.result() if task.done() else 'Prepare did not return'
        # Actual native prepare has released its DB reservation and alpha.lock.
        # A duplicate holds that same original lock while the creator returns.
        with file_lock(prefix / 'alpha.lock', blocking=False):
            (markers / 'candidate-prepare-release').touch()
            return await task

    result = asyncio.run(prepare())
    assert result['status'] == 'new_offer', result
    assert result['launch']['request']['origin_operation_id'] == operation.preparation.identity['operation_id']
    assert operation.spawning is None
    original = (prefix / 'alpha.intent.json').read_bytes()
    observed = asyncio.run(cycle_candidate().preparation.run())
    assert observed['status'] == 'observed' and 'launch' not in observed
    assert (prefix / 'alpha.intent.json').read_bytes() == original
    assert not (prefix / 'alpha.attempt.json').exists()
    assert not (prefix / 'alpha.budget/owner.json').exists()
    assert not (cycle_selection[2] / 'training/jobs/alpha').exists()
    assert not service[1].exists() or json.loads(service[1].read_bytes())['starts'] == 0



@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Root handoff and real S-H cancellation require Linux/WSL2')
@pytest.mark.parametrize('boundary', ['transfer', 'confirm', 'lost-confirm', 'lookup', 'attempt-sync', 'sdk-start'])
def test_cycle_candidate_cancellation_distinguishes_root_handoff(
        controller_admission, cycle_selection, cycle_candidate, cycle_operation_fault, service, monkeypatch, tmp_path, boundary):
    import asyncio

    runtime = cycle_selection[2]
    operation = cycle_candidate()
    markers = cycle_operation_fault('post-stopped-confirm' if boundary == 'lost-confirm' else 'candidate-' + boundary)
    marker = markers / ('stopped-result-reader' if boundary == 'lost-confirm' else 'candidate-' + boundary)
    if boundary == 'transfer':
        transfer = operation.transfer

        async def hold_transferred(raw):
            await transfer(raw)
            marker.write_text('The complete original root input was transferred')
            await asyncio.sleep(60)

        monkeypatch.setattr(operation, 'transfer', hold_transferred)
    if boundary == 'attempt-sync':
        monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_PAUSE', 'submission-attempt-sync')
        monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_MARKER', str(marker))
    if boundary == 'sdk-start':
        service[0]('held-start')
        marker = service[1].with_suffix('.held')

    async def cancelled():
        task = asyncio.create_task(operation.run())
        ticks = 0
        try:
            while not marker.exists() and not task.done() and not operation.preparation.expired():
                ticks += 1
                await asyncio.sleep(.02)
            assert marker.exists(), task.result() if task.done() else 'The original boundary was not reached'
            assert ticks > 1 and recorded_process_is_active(operation.root_identity)
            assert operation.handed_off is (boundary not in ('transfer', 'confirm', 'lost-confirm'))
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    try:
        asyncio.run(cancelled())
        assert operation.operation.process.returncode is not None
        assert (operation.root.poll() is None) is (boundary not in ('transfer', 'confirm', 'lost-confirm'))
        assert recorded_process_is_active(operation.root_identity) is (boundary not in ('transfer', 'confirm', 'lost-confirm'))
        if boundary == 'lost-confirm':
            helper = operation.operation.output / 'helper/stdout.txt'
            assert json.loads(helper.read_bytes())['status'] == 'owner_confirmed'
        prefix = runtime / 'ergora/training-submissions'
        assert (prefix / 'alpha.attempt.json').exists() is (boundary in ('attempt-sync', 'sdk-start'))
        assert not (prefix / 'alpha.result.json').exists()
        record = json.loads(service[1].read_bytes()) if service[1].exists() else {'starts': 0}
        assert record['starts'] == (1 if boundary == 'sdk-start' else 0)
        cycle_operation_fault('candidate')
        observed = run_cycle_candidate(cycle_candidate)
        assert observed['status'] == 'observed' and 'launch' not in observed
        assert (json.loads(service[1].read_bytes()) if service[1].exists() else {'starts': 0})['starts'] == record['starts']
        if boundary == 'sdk-start':
            import ergora.training.runtime.worker as worker

            owner_path = prefix / 'alpha.budget/owner.json'
            owner_raw = owner_path.read_bytes()
            attempt_raw = (prefix / 'alpha.attempt.json').read_bytes()
            owner_path.write_bytes(b'{')
            try:
                preparation = operation.preparation
                reconciliation = worker._CycleOperation(Path(preparation.identity['control_home']),
                    preparation.identity['project'], preparation.identity['cycle_id'],
                    preparation.identity['authorization_sha256'], 'reconcile-candidate',
                    snapshot=preparation.payload['snapshot'], ordinal=preparation.identity['ordinal'],
                    start_context=preparation.payload['start_context'], inspection_timeout=30)
                service[0]('not-found')
                missing = asyncio.run(reconciliation.run())
                assert missing['submission']['status'] == 'unknown'
                assert missing['submission']['reconciliation'] == 'not_found'
                assert not (prefix / 'alpha.result.json').exists()
                assert (prefix / 'alpha.attempt.json').read_bytes() == attempt_raw
                assert json.loads(service[1].read_bytes())['starts'] == record['starts']
                service[0]('accepted')
                reconciliation = worker._CycleOperation(Path(preparation.identity['control_home']),
                    preparation.identity['project'], preparation.identity['cycle_id'],
                    preparation.identity['authorization_sha256'], 'reconcile-candidate',
                    snapshot=preparation.payload['snapshot'], ordinal=preparation.identity['ordinal'],
                    start_context=preparation.payload['start_context'], inspection_timeout=30)
                recovered = asyncio.run(reconciliation.run())
                assert recovered['status'] == 'observed', recovered
                assert recovered['submission']['status'] == 'submitted'
                assert recovered['submission']['budget']['owner_status'] == 'unknown'
                assert recovered['submission']['run_id'] == '00000000-0000-4000-8000-000000000001'
                assert owner_path.read_bytes() == b'{' and (prefix / 'alpha.attempt.json').read_bytes() == attempt_raw
                assert json.loads(service[1].read_bytes())['starts'] == record['starts']
            finally:
                owner_path.write_bytes(owner_raw)
    finally:
        stop_controller_test_owner(runtime)
        if operation.root is not None:
            operation.root.wait(timeout=5)



@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Unique original offers use real Linux supervisors')
def test_cycle_candidate_lost_prepare_reply_never_recreates_its_root_offer(
        cycle_selection, cycle_candidate, cycle_operation_fault, service):
    import asyncio

    runtime = cycle_selection[2]
    operation = cycle_candidate()
    markers = cycle_operation_fault('post-stopped')

    async def lose_reply():
        task = asyncio.create_task(operation.run())
        try:
            while (not (markers / 'stopped-result-reader').exists() and not task.done()
                   and not operation.preparation.expired()):
                await asyncio.sleep(.02)
            assert (markers / 'stopped-result-reader').exists()
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(lose_reply())
    prefix = runtime / 'ergora/training-submissions'
    original = (prefix / 'alpha.intent.json').read_bytes()
    assert operation.spawning is None and not (prefix / 'alpha.budget/owner.json').exists()
    cycle_operation_fault('candidate')
    observed = run_cycle_candidate(cycle_candidate)
    assert observed['status'] == 'observed' and observed['submission']['status'] == 'prepared' and 'launch' not in observed
    assert (prefix / 'alpha.intent.json').read_bytes() == original
    assert not (prefix / 'alpha.attempt.json').exists() and not service[1].exists()



@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Pending OS creation must retain its actual Linux child')
@pytest.mark.parametrize('ending', ['cancel', 'deadline'])
def test_cycle_candidate_cancel_retains_a_late_popen_handle_without_sending_input(cycle_candidate, monkeypatch, ending):
    import asyncio
    import threading

    entered, release = threading.Event(), threading.Event()
    original = subprocess.Popen
    operation = cycle_candidate()

    def pending(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.training.runtime.submission import cycle_root_main;cycle_root_main()':
            entered.set()
            release.wait()
        return original(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, 'Popen', pending)

    async def cancel_pending():
        task = asyncio.create_task(operation.run())
        try:
            while not entered.is_set() and not task.done() and not operation.preparation.expired():
                await asyncio.sleep(.02)
            assert entered.is_set()
            if ending == 'cancel':
                task.cancel()
            else:
                while not operation.preparation.expired():
                    await asyncio.sleep(.02)
            await asyncio.sleep(.05)
            assert not task.done() and not operation.spawning.done()
        finally:
            release.set()
            if ending == 'cancel':
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                result = await task
                assert result['status'] == 'unknown' and 'OS process creation was pending' in result['reason']

    asyncio.run(cancel_pending())
    assert operation.root is not None and operation.root.returncode is not None and not operation.handed_off
    assert operation.root.poll() is not None and operation.root.stdin.closed



@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Loop shutdown must retain the actual independent Linux root')
@pytest.mark.parametrize('boundary', ['spawn', 'confirm'])
def test_cycle_candidate_loop_shutdown_reaps_a_pending_root(
        cycle_candidate, cycle_selection, cycle_operation_fault, monkeypatch, boundary):
    import asyncio
    import threading
    from ergora.runtime import processes

    entered, release = threading.Event(), threading.Event()
    original, roots, tasks, waits = subprocess.Popen, [], [], []
    operation = cycle_candidate()
    markers = cycle_operation_fault('candidate-confirm' if boundary == 'confirm' else 'candidate')
    notify, notifications = processes.notify_identity, []

    def notify_after_helper(expected, signum):
        if expected == operation.root_identity:
            notifications.append((operation.operation.process.returncode is not None,
                                  bool(operation.operation.response.frames)))
        return notify(expected, signum)

    def pending(argv, *args, **kwargs):
        root = argv[-1] == 'from ergora.training.runtime.submission import cycle_root_main;cycle_root_main()'
        if root and boundary == 'spawn':
            entered.set()
            release.wait(20)
        child = original(argv, *args, **kwargs)
        if root:
            roots.append(child)
            wait = child.wait

            def real_wait(*args, **kwargs):
                waits.append(True)
                return wait(*args, **kwargs)

            child.wait = real_wait
        return child

    monkeypatch.setattr(subprocess, 'Popen', pending)
    monkeypatch.setattr(processes, 'notify_identity', notify_after_helper)

    async def exit_before_handoff():
        tasks.append(asyncio.create_task(operation.run()))
        while (not (entered.is_set() if boundary == 'spawn' else (markers / 'candidate-confirm').exists())
               and not tasks[0].done() and not operation.preparation.expired()):
            await asyncio.sleep(.02)
        assert entered.is_set() if boundary == 'spawn' else (markers / 'candidate-confirm').exists()
        # Returning makes asyncio.run cancel every pending task simultaneously.
        threading.Timer(.2, release.set).start()

    try:
        asyncio.run(exit_before_handoff())
        assert tasks[0].cancelled() and len(roots) == 1
        assert operation.root is roots[0] and roots[0].returncode is not None
        assert waits and not Path('/proc/' + str(roots[0].pid)).exists()
        assert not operation.handed_off
        if boundary == 'confirm':
            assert operation.operation.process.returncode is not None and operation.operation.response.frames
            assert notifications and all(item == (True, True) for item in notifications)
        assert not (cycle_selection[2] / 'ergora/training-submissions/alpha.attempt.json').exists()
    finally:
        release.set()
        for child in roots:
            if not child.stdin.closed:
                child.stdin.close()
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=5)



@pytest.mark.skipif(sys.platform != 'linux', reason='Exact root cleanup uses Linux process identities')
@pytest.mark.parametrize('fault', ['natural-exit', 'notification-error'])
def test_cycle_candidate_root_cleanup_waits_after_notification_races(monkeypatch, fault):
    import asyncio
    import ergora.training.runtime.worker as worker
    from ergora.runtime import processes

    child = subprocess.Popen([sys.executable, '-I', '-S', '-c',
        'import sys,time;sys.stdin.buffer.read();time.sleep(.2)'], stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    operation = worker._CycleCandidate.__new__(worker._CycleCandidate)
    operation.root, operation.root_identity = child, processes.identity(child.pid)
    operation.cleanup_problem = None
    notify, wait = processes.notify_identity, child.wait
    waits = []

    def record_wait(*args, **kwargs):
        waits.append(True)
        return wait(*args, **kwargs)

    def failed_notification(expected, signum):
        if fault == 'notification-error':
            raise OSError('Controlled pidfd notification unavailable')
        # Observe exit without reaping it, forcing the poll/notification race.
        until = time.monotonic() + 5
        while os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOWAIT | os.WNOHANG) is None:
            if time.monotonic() >= until:
                raise AssertionError('The inert root did not exit after stdin EOF')
            time.sleep(.001)
        notify(expected, signum)

    async def discard():
        operation.spawning = asyncio.create_task(asyncio.sleep(0, result=child))
        await operation.discard_root()

    monkeypatch.setattr(processes, 'notify_identity', failed_notification)
    monkeypatch.setattr(child, 'wait', record_wait)
    try:
        asyncio.run(discard())
        assert child.returncode == 0 and waits == [True]
        assert not Path('/proc/' + str(child.pid)).exists()
        assert (operation.cleanup_problem is not None) is (fault == 'notification-error')
    finally:
        if child.poll() is None:
            child.terminate()
        wait(timeout=5)



@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Final dispatch validates original files under Linux locks')
@pytest.mark.parametrize('drift', ['window', 'owner', 'owner-deadline'])
def test_cycle_candidate_final_gate_preserves_attempt_on_original_source_drift(
        cycle_selection, cycle_candidate, cycle_operation_fault, service, drift):
    runtime = cycle_selection[2]
    markers = cycle_operation_fault('candidate-' + drift + '-drift')
    try:
        result = run_cycle_candidate(cycle_candidate)
        assert result['status'] == 'unknown' and (markers / ('candidate-' + drift + '-drift')).exists(), result
        prefix = runtime / 'ergora/training-submissions'
        original = (prefix / 'alpha.attempt.json').read_bytes()
        assert not (prefix / 'alpha.result.json').exists()
        assert json.loads(service[1].read_bytes())['starts'] == 0
        cycle_operation_fault('candidate')
        observed = run_cycle_candidate(cycle_candidate)
        assert observed['status'] in ('observed', 'unknown') and 'launch' not in observed
        assert (prefix / 'alpha.attempt.json').read_bytes() == original
        assert json.loads(service[1].read_bytes())['starts'] == 0
    finally:
        stop_controller_test_owner(runtime)



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller binding consumes original Linux authorization')
def test_controller_prepare_binds_complete_parent_records_and_original_position(controller_admission, cycle_selection):
    state, _, selected, _, admission = controller_admission
    runtime = cycle_selection[2]
    binding = save_controller_binding(admission)
    selector = {key: value for key, value in binding.items() if key != 'task_queue'}
    source = json.loads((admission.directory / 'cycle.json').read_bytes())
    manifest = source['definition']['candidates'][0]['manifest_sha256']
    prefix = runtime / 'ergora/training-submissions'

    def prepare(value):
        return training_native.training_submission(state.project('demo'), state.root, 'prepare',
            {'experiment_id': 'alpha', 'manifest_sha256': manifest, 'budget': value}, timeout=20)

    for key, value in (('ordinal', True), ('ordinal', -1), ('ordinal', 1), ('ordinal', 31),
                       ('run_id', 'another-run'), ('intent_sha256', '0' * 64)):
        altered = deepcopy(selector)
        altered['controller'][key] = value
        with pytest.raises(ValueError):
            prepare(altered)
        assert not (prefix / 'alpha.intent.json').exists()
    for name in ('intent', 'attempt', 'receipt'):
        path = admission.folder / (name + '.json')
        original = path.read_bytes()
        try:
            value = json.loads(original)
            value['unbound'] = True
            path.write_text(json.dumps(value))
            with pytest.raises(ValueError):
                prepare(selector)
            assert not (prefix / 'alpha.intent.json').exists()
        finally:
            path.write_bytes(original)
    prepared = prepare(selector)
    saved = (prefix / 'alpha.intent.json').read_bytes()
    assert prepared['created'] is True and json.loads(saved)['budget'] == binding
    assert prepare(selector)['created'] is False
    altered = deepcopy(selector)
    altered['controller']['run_id'] = 'another-run'
    with pytest.raises(ValueError):
        prepare(altered)
    assert (prefix / 'alpha.intent.json').read_bytes() == saved
    assert not (prefix / 'alpha.attempt.json').exists() and not (prefix / 'alpha.budget').exists()
    isolated = subprocess.run([sys.executable, '-I', '-S', '-c', '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from ergora.training.execution_protocol import CycleAdmission,read_raw
from ergora.training.materials import decode_record
directory=Path(sys.argv[2])
parent=CycleAdmission(directory,decode_record(read_raw(directory/'authorization.json')))
parent.bind(decode_record(read_raw(Path(sys.argv[3]))),decode_record(read_raw(directory/'cycle.json',10_000_000)))
assert not any(name in sys.modules for name in ('yaml','jsonschema','temporalio','dev_platform','ergora.storage.state'))
print('complete original binding verified without site packages')
''', str(Path(ergora.__file__).parent.parent), str(admission.directory), str(prefix / 'alpha.intent.json')],
        capture_output=True, text=True, timeout=10)
    assert isolated.returncode == 0, isolated.stderr



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux budget owner')
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.parametrize('case', ['not-found', 'closed', 'run', 'memo', 'type', 'queue', 'input', 'accepted'])
def test_controller_fixed_history_gates_the_one_original_start(
        controller_admission, cycle_selection, cycle_candidate, service, monkeypatch, case):
    from ergora.runtime import processes
    import signal

    state, _, _, _, admission = controller_admission
    runtime = cycle_selection[2]
    binding = save_controller_binding(admission)
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER', str(admission.folder))
    owner_path = runtime / 'ergora/training-submissions/alpha.budget/owner.json'
    intent_path = runtime / 'ergora/training-submissions/alpha.intent.json'
    attempt_path = runtime / 'ergora/training-submissions/alpha.attempt.json'
    try:
        if case != 'accepted':
            monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_CASE', case)
        result = run_cycle_candidate(cycle_candidate)
        if case != 'accepted':
            reason = ('Original controller run is not found' if case == 'not-found' else
                      'Original controller run, running state or complete intent memo differs' if case in ('closed', 'run', 'memo') else
                      'Original controller type, queue or started input' if case in ('type', 'queue') else
                      'Original controller complete started input or intent memo differs')
            assert result['status'] == 'unknown' and reason in result['reason'], result
            assert 'launch' not in result
            assert not intent_path.exists() and not attempt_path.exists()
            assert not owner_path.parent.exists() and not (runtime / 'training/jobs/alpha').exists()
            repeated = run_cycle_candidate(cycle_candidate)
            assert repeated['status'] == 'unknown' and reason in repeated['reason'], repeated
            assert 'launch' not in repeated
            assert not intent_path.exists() and not attempt_path.exists()
            assert not owner_path.parent.exists() and not (runtime / 'training/jobs/alpha').exists()
            recorded = json.loads(service[1].read_bytes()) if service[1].exists() else {'starts': 0}
            assert recorded['starts'] == 0
            return
        else:
            original = intent_path.read_bytes()
            submitted = result['submission']
            assert submitted['status'] == 'submitted' and submitted['budget']['controller'] == binding['controller']
            assert attempt_path.exists() and json.loads(service[1].read_bytes())['starts'] == 1
        # Accepted history repeats as an observation of its one original start.
        repeated = run_cycle_candidate(cycle_candidate)
        assert repeated['status'] == 'observed' and 'launch' not in repeated
        assert intent_path.read_bytes() == original
        recorded = json.loads(service[1].read_bytes()) if service[1].exists() else {'starts': 0}
        assert recorded['starts'] == (1 if case == 'accepted' else 0)
    finally:
        if owner_path.exists():
            owner = json.loads(owner_path.read_bytes())
            try:
                processes.notify_identity({key: owner[key] for key in ('pid', 'start_ticks', 'boot_id')}, signal.SIGTERM)
            except (OSError, ValueError):
                pass
            wait_budget_stopped(runtime, seconds=25)



@pytest.mark.skipif(sys.platform != 'linux', reason='Parent permits cover a real late start RPC')
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
def test_controller_stop_drains_original_rpc_and_denies_its_late_create(
        controller_admission, cycle_selection, cycle_candidate, service, monkeypatch):
    state, _, _, _, admission = controller_admission
    runtime = cycle_selection[2]
    binding = save_controller_binding(admission)
    selector = {key: value for key, value in binding.items() if key != 'task_queue'}
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER', str(admission.folder))
    service[0]('held-start')
    marker = service[1].with_suffix('.held')
    operation = cycle_candidate()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(run_cycle_candidate, lambda ordinal: operation)
            try:
                while not marker.exists() and not future.done() and not operation.preparation.expired():
                    time.sleep(.02)
                assert marker.exists(), 'The real SDK start must be in flight with its parent permit'
                stopped = admission.request_stop('Stop the original in-flight RPC')
                assert stopped['stop_durable'] is True and stopped['admission_drained'] is None
            finally:
                service[1].with_suffix('.continue').touch()
            result = future.result(timeout=15)
        assert result['submission']['status'] == 'submitted'
        record = json.loads(service[1].read_bytes())
        assert record['starts'] == 1 and 'Controller stop is visible' in record['native_create_error']
        assert not (runtime / 'training/jobs/alpha').exists()
        assert admission.observe(drain=True)['admission_drained'] is True
    finally:
        stop_controller_test_owner(runtime)



@pytest.mark.skipif(sys.platform != 'linux', reason='The original registry lock must retain the parent permit')
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
def test_controller_worker_rechecks_stop_inside_original_registry_lock(
        controller_admission, cycle_selection, cycle_candidate, service, monkeypatch):
    from ergora.storage.state import file_lock

    state, _, _, _, admission = controller_admission
    _, definition, runtime, _, _, request = cycle_selection
    binding = save_controller_binding(admission)
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER', str(admission.folder))
    selector = {key: value for key, value in binding.items() if key != 'task_queue'}
    marker = admission.folder / 'native-registry-attempt'
    try:
        assert run_cycle_candidate(cycle_candidate)['submission']['status'] == 'submitted'
        with ThreadPoolExecutor(max_workers=1) as pool:
            with file_lock(runtime / 'training/registry.lock'):
                future = pool.submit(native_budget_create, definition, 'alpha', managed=True, registry_marker=marker)
                until = time.monotonic() + 6
                while not marker.exists() and time.monotonic() < until:
                    time.sleep(.02)
                assert marker.exists()
                stopped = admission.request_stop('Stop while native create waits for the original registry')
                assert stopped['admission_drained'] is None and not (runtime / 'training/jobs/alpha').exists()
            created = future.result(timeout=8)
        assert created.returncode != 0
        assert 'stop' in created.stderr.lower()
        assert not (runtime / 'training/jobs/alpha').exists()
        assert admission.observe(drain=True)['admission_drained'] is True
    finally:
        stop_controller_test_owner(runtime)



@pytest.mark.skipif(sys.platform != 'linux', reason='Parent permits cover the original attempt directory sync')
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
def test_controller_stop_after_attempt_sync_never_resends_the_consumed_rpc(
        controller_admission, cycle_selection, cycle_candidate, service, tmp_path, monkeypatch):
    import ergora.training.cycles as training_cycles

    state, _, _, _, admission = controller_admission
    runtime = cycle_selection[2]
    binding = save_controller_binding(admission)
    marker = tmp_path / 'attempt-sync'
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER', str(admission.folder))
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_PAUSE', 'submission-attempt-sync')
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_MARKER', str(marker))
    selector = {key: value for key, value in binding.items() if key != 'task_queue'}
    prefix = runtime / 'ergora/training-submissions'
    operation = cycle_candidate()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(run_cycle_candidate, lambda ordinal: operation)
            try:
                while not marker.exists() and not future.done() and not operation.preparation.expired():
                    time.sleep(.02)
                assert marker.exists(), 'The original attempt directory sync must finish before the pause'
                original = (prefix / 'alpha.attempt.json').read_bytes()
                stopped = admission.request_stop('Stop after the original attempt sync')
                assert stopped['stop_durable'] is True and stopped['admission_drained'] is None
            finally:
                marker.with_suffix('.release').touch()
            result = future.result(timeout=12)
            assert result['status'] == 'unknown' and 'Original training budget cannot start work: stopped' in result['reason']
        intent = json.loads((prefix / 'alpha.intent.json').read_bytes())
        resumed = training.resume_start(state, 'demo', 'alpha', 1, training_cycles._sha(intent))
        assert resumed['status'] == 'unknown' and resumed['attempt_saved'] is True
        assert (prefix / 'alpha.attempt.json').read_bytes() == original
        assert json.loads(service[1].read_bytes())['starts'] == 0
        assert not (runtime / 'training/jobs/alpha').exists()
        assert admission.observe(drain=True)['admission_drained'] is True
    finally:
        marker.with_suffix('.release').touch()
        stop_controller_test_owner(runtime)



@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Original start-attempt synchronization and H/SDK gate require Linux')
def test_controller_remote_close_after_attempt_sync_never_sends_the_consumed_start(
        controller_admission, cycle_selection, cycle_candidate, service, tmp_path, monkeypatch):
    import ergora.training.cycles as training_cycles

    state, _, _, _, admission = controller_admission
    runtime = cycle_selection[2]
    marker = tmp_path / 'remote-close-attempt'
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_CASE', 'closed-after-attempt')
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_PAUSE', 'submission-attempt-sync')
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_MARKER', str(marker))
    operation = cycle_candidate()
    prefix = runtime / 'ergora/training-submissions'
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(run_cycle_candidate, lambda ordinal: operation)
            try:
                until = time.monotonic() + 15
                while not marker.exists() and not future.done() and time.monotonic() < until:
                    time.sleep(.01)
                assert marker.exists(), 'The original attempt must be durable before the remote close'
                path = prefix / 'alpha.attempt.json'
                attempt = path.read_bytes(), path.stat().st_ino
                marker.with_suffix('.closed').touch()
            finally:
                marker.with_suffix('.release').touch()
            result = future.result(timeout=12)
        assert result['status'] == 'unknown' and 'Original controller run' in result['reason'], result
        intent = json.loads((prefix / 'alpha.intent.json').read_bytes())
        resumed = training.resume_start(state, 'demo', 'alpha', 1, training_cycles._sha(intent))
        assert resumed['status'] == 'unknown' and resumed['attempt_saved'] is True
        assert (path.read_bytes(), path.stat().st_ino) == attempt
        assert json.loads(service[1].read_bytes())['starts'] == 0
        assert not (runtime / 'training/jobs/alpha').exists()
    finally:
        marker.with_suffix('.release').touch()
        stop_controller_test_owner(runtime)


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Real request/launch and native locked admission require Linux')
@pytest.mark.parametrize('boundary', ['request', 'launch', 'executor-lock', 'attempt', 'ack'])
def test_controller_stop_at_original_execution_boundaries_preserves_consumed_records(
        controller_admission, cycle_selection, cycle_candidate, service, tmp_path, monkeypatch, boundary):
    state, _, _, _, admission = controller_admission
    _, definition, runtime, _, _, request = cycle_selection
    binding = save_controller_binding(admission)
    selector = {key: value for key, value in binding.items() if key != 'task_queue'}
    marker = tmp_path / 'execution-boundary'
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER', str(admission.folder))
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_PAUSE', boundary)
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER_MARKER', str(marker))
    try:
        submitted = run_cycle_candidate(cycle_candidate)['submission']
        created = native_budget_create(definition, 'alpha', managed=True)
        assert created.returncode == 0, created.stderr
        job = runtime / 'training/jobs/alpha'
        raw_sha = hashlib.sha256((job / 'request.json').read_bytes()).hexdigest()
        # Different ambient username must not replace the original controller actor.
        monkeypatch.setenv('LOGNAME', 'changed-ambient-name')
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(training.execute, state, 'demo', 'alpha', 1, submitted['intent_sha256'],
                submitted['run_id'], raw_sha, confirm=True)
            try:
                until = time.monotonic() + 15
                while not marker.exists() and time.monotonic() < until:
                    time.sleep(.02)
                assert marker.exists(), f'The actual {boundary} boundary must be reached'
                request_record = json.loads((job / 'managed-execution/request.json').read_bytes())
                assert request_record['actor_id'] == admission.authorization['controller']['actor_id']
                if admission.authorization['schema_version'] == 5 and boundary in ('attempt', 'ack'):
                    native = json.loads((job / 'managed-execution/attempt.json').read_bytes())['executor']
                    locked = admission.lock.stat()
                    held = []
                    for descriptor in Path('/proc/' + str(native['pid']) + '/fd').iterdir():
                        try:
                            opened = descriptor.stat()
                            if (opened.st_dev, opened.st_ino) == (locked.st_dev, locked.st_ino):
                                held.extend(line for line in (descriptor.parent.parent / 'fdinfo' / descriptor.name).read_text().splitlines()
                                    if 'FLOCK' in line and 'READ' in line)
                        except FileNotFoundError:
                            continue
                    assert held, 'The actual native executor must retain its own shared parent permit'
                stopped = admission.request_stop('Stop at ' + boundary)
                assert stopped['stop_durable'] is True and stopped['admission_drained'] is None
            finally:
                marker.with_suffix('.release').touch()
            if boundary == 'request':
                with pytest.raises(ValueError, match='Controller stop'):
                    future.result(timeout=12)
            else:
                assert future.result(timeout=12)['status'] == 'requested'
        stop_controller_test_owner(runtime)
        records = training.execution(state, 'demo', 'alpha')['records']
        assert records['request'] is not None
        assert (records['launch'] is not None) == (boundary != 'request')
        assert (records['attempt'] is not None) == (boundary in ('attempt', 'ack'))
        assert (records['ack'] is not None) == (boundary == 'ack')
        assert not (job / 'started.json').exists() and not (job / 'result.json').exists()
        assert json.loads(service[1].read_bytes())['starts'] == 1
        assert admission.observe(drain=True)['admission_drained'] is True
    finally:
        marker.with_suffix('.release').touch()
        stop_controller_test_owner(runtime)



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_null_stop_keeps_its_veto_when_a_later_intent_cannot_be_bound(controller_admission):
    _, _, _, _, admission = controller_admission
    result = admission.request_stop('Stop before any controller intent')
    assert result['record']['controller_intent_sha256'] is None and result['stop_durable'] is True
    original = admission.stop.read_bytes()
    for raw in (json.dumps(saved_controller_intent(admission)), '{"incomplete":'):
        (admission.folder / 'intent.json').write_text(raw)
        changed = admission.observe(drain=True)
        assert changed['stop_visible'] is True and changed['identity_matches'] is False
        assert changed['stop_durable'] is None and changed['admission_drained'] is None
        again = admission.request_stop('No replacement or new intent binding')
        assert again['identity_matches'] is False and again['stop_durable'] is None
        assert admission.stop.read_bytes() == original
        with pytest.raises(ValueError, match='stop is visible'):
            with admission.permission():
                pytest.fail('A later intent must never undo the original stop veto')



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_stop_revalidates_intent_after_the_final_drain_sync(controller_admission, monkeypatch):
    _, _, _, _, admission = controller_admission
    admission.request_stop('Stop before controller intent')
    original, fsync, synchronized = admission.stop.read_bytes(), os.fsync, []

    def late_intent(descriptor):
        if Path('/proc/self/fd/' + str(descriptor)).resolve() == admission.stop:
            synchronized.append(True)
            if len(synchronized) == 2:  # The recursive observation holds the parent exclusive lock.
                (admission.folder / 'intent.json').write_text(json.dumps(saved_controller_intent(admission)))
        return fsync(descriptor)

    monkeypatch.setattr(os, 'fsync', late_intent)
    observed = admission.observe(drain=True)
    assert len(synchronized) == 2
    assert observed['stop_visible'] is True and observed['identity_matches'] is False
    assert observed['stop_durable'] is None and observed['admission_drained'] is None
    assert admission.stop.read_bytes() == original



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_concurrent_stops_preserve_one_original_and_never_repair_corruption(controller_admission, tmp_path):
    state, _, _, _, admission = controller_admission
    children = []
    try:
        for number in range(2):
            folder = tmp_path / str(number)
            folder.mkdir()
            children.append(admission_process(admission, folder, 'concurrent', reason='Reason ' + str(number)))
        for child in children:
            child.stdin.write('\n')
            child.stdin.flush()
        results = []
        for child in children:
            stdout, stderr = child.communicate(timeout=5)
            assert child.returncode == 0, stderr
            results.append(json.loads(stdout))
        original = admission.stop.read_bytes()
        # A loser may observe the winner's partial publication, never a replacement.
        confirmed = admission.observe(drain=True)
        assert confirmed['stop_durable'] is True and confirmed['admission_drained'] is True
        assert confirmed['record']['reason'] in ('Reason 0', 'Reason 1')
        assert all(result['record_sha256'] in (None, confirmed['record_sha256']) for result in results)
        assert admission.stop.read_bytes() == original
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
    for shape in ('partial', 'identity', 'fifo'):
        admission.stop.unlink()
        if shape == 'partial':
            admission.stop.write_bytes(b'{"schema_version":')
        elif shape == 'identity':
            value = json.loads(original)
            value['authorization_sha256'] = '0' * 64
            admission.stop.write_text(json.dumps(value))
        else:
            os.mkfifo(admission.stop)
        before = admission.stop.read_bytes() if shape != 'fifo' else None
        result = admission.request_stop('Do not repair the original')
        assert result['stop_visible'] is True and result['identity_matches'] is False
        assert result['stop_durable'] is None and result['admission_drained'] is None
        with pytest.raises(ValueError, match='stop is visible'):
            with admission.permission():
                pytest.fail('An invalid visible stop still vetoes admission')
        if before is not None:
            assert admission.stop.read_bytes() == before



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller submission requires Linux/WSL2')
def test_controller_consent_cannot_dispatch_through_either_manual_binding_path(controller_admission, cycle_selection, service):
    import ergora.training.cycles as training_cycles

    state, _, selected, authorized, admission = controller_admission
    _, _, runtime, _, _, request = cycle_selection
    service[0]('accepted')
    digest = request['candidates'][0]['manifest_sha256']
    for cycle_entry in (True, False):
        with pytest.raises(ValueError, match='Controller authorization requires complete controller binding'):
            if cycle_entry:
                training_cycles.start(state, 'demo', 'controller', 'alpha', authorized['authorization_sha256'], 1)
            else:
                training.start(state, 'demo', 'alpha', 1, digest,
                    budget={'cycle_id': 'controller', 'authorization_sha256': authorized['authorization_sha256']})
        prefix = runtime / 'ergora/training-submissions'
        assert not (prefix / 'alpha.intent.json').exists() and not (prefix / 'alpha.attempt.json').exists()
        assert not (prefix / 'alpha.budget').exists() and not (runtime / 'training/jobs/alpha').exists()
        assert not service[1].exists()
    assert admission.authorization == authorized['authorization']



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
def test_controller_cli_reconciles_only_its_original_lost_reply(controller_dispatch, cycle_operation_fault):
    from contextlib import redirect_stdout
    import io
    from ergora.interfaces.cli import main

    state, admission, storage, _ = controller_dispatch
    common = ['--home', str(state.root), 'training']
    target = ['demo', 'controller', '--authorization-sha256', admission.authorization['sha256']]

    def invoke(action):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main([*common, 'cycle-controller-' + action, *target])
        assert code == 0
        return json.loads(output.getvalue())

    cycle_operation_fault('lost-reply')
    first = invoke('submit')
    assert first['status'] == 'unknown' and first['attempt_saved'] is True
    attempt = admission.folder / 'attempt.json'
    original = attempt.read_bytes(), attempt.stat().st_ino
    cycle_operation_fault('accepted')
    second = invoke('reconcile')
    assert second['status'] == 'submitted' and second['run_id'] == '00000000-0000-4000-8000-000000000003'
    assert (attempt.read_bytes(), attempt.stat().st_ino) == original
    assert sum(json.loads(p.read_bytes())['action'] == 'start' for p in storage.glob('call-*.json')) == 1


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
@pytest.mark.parametrize('case', ['accepted', 'lost-reply', 'not-found', 'closed', 'continued', 'retry', 'reset'])
def test_cycle_controller_recovers_only_its_single_original_attempt(controller_dispatch, case):
    import asyncio

    state, admission, storage, operation = controller_dispatch
    before = {path: (path.read_bytes(), path.stat().st_ino) for path in admission.directory.rglob('*') if path.is_file()}
    first = asyncio.run(operation(case).run())
    assert first['status'] == ('submitted' if case == 'accepted' else 'unknown'), first
    attempt = admission.folder / 'attempt.json'
    saved = attempt.read_bytes(), attempt.stat().st_ino
    second = asyncio.run(operation(case, 'reconcile-controller').run())
    unresolved = case in ('not-found', 'continued', 'retry', 'reset')
    assert second['status'] == ('unknown' if unresolved else 'submitted'), second
    assert second['runtime_status'] == ('not_found' if case == 'not-found' else 'unconfirmed' if unresolved else 'queried')
    assert second['attempt_saved'] is True and (attempt.read_bytes(), attempt.stat().st_ino) == saved
    if not unresolved:
        assert second['run_id'] == '00000000-0000-4000-8000-000000000003'
        receipt = admission.folder / 'receipt.json'
        original = receipt.read_bytes(), receipt.stat().st_ino
        again = asyncio.run(operation(case).run())
        assert again['run_id'] == second['run_id'] and (receipt.read_bytes(), receipt.stat().st_ino) == original
        if case == 'closed':
            from ergora.training.runtime.status import lookup_controller
            from temporalio.client import Client
            from fixtures.training_controller_service import DispatchService

            parent = operation(case).payload
            with pytest.raises(ValueError, match='running state'):
                asyncio.run(lookup_controller(Client(DispatchService(parent, case)), admission.controller_intent(),
                    {'workflow_id': second['workflow_id'], 'run_id': second['run_id'], 'intent_sha256': second['intent_sha256']}, timeout=2))
    calls = [json.loads(p.read_bytes()) for p in storage.glob('call-*.json')]
    assert sum(call['action'] == 'start' for call in calls) == 1
    assert all(p.read_bytes() == raw and p.stat().st_ino == inode for p, (raw, inode) in before.items())
    assert not (admission.folder / 'rejection.json').exists()
    assert not (Path(admission.authorization['execution']['state_directory']) / 'training/jobs/alpha').exists()



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
def test_cycle_controller_reconcile_preserves_unknown_on_changed_remote_identity(controller_dispatch):
    import asyncio

    _, admission, storage, operation = controller_dispatch
    assert asyncio.run(operation('lost-reply').run())['status'] == 'unknown'
    attempt = admission.folder / 'attempt.json'
    original = attempt.read_bytes(), attempt.stat().st_ino
    for case in ('input', 'memo', 'started-memo', 'type', 'queue', 'run', 'first-run'):
        observed = asyncio.run(operation(case, 'reconcile-controller').run())
        assert observed['status'] == 'unknown' and observed['runtime_status'] == 'unconfirmed', (case, observed)
        assert not (admission.folder / 'receipt.json').exists() and not (admission.folder / 'rejection.json').exists()
    recovered = asyncio.run(operation('accepted', 'reconcile-controller').run())
    assert recovered['status'] == 'submitted' and (attempt.read_bytes(), attempt.stat().st_ino) == original
    calls = [json.loads(p.read_bytes()) for p in storage.glob('call-*.json')]
    assert sum(call['action'] == 'start' for call in calls) == 1



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
def test_cycle_controller_receipt_revalidates_original_authorization_after_sdk_wait(controller_dispatch):
    import asyncio

    _, admission, storage, operation = controller_dispatch
    result = asyncio.run(operation('authorization-after-start').run())
    assert result['status'] == 'unknown', result
    assert (admission.folder / 'attempt.json').exists() and (storage / 'request.pb').exists()
    assert not (admission.folder / 'receipt.json').exists() and not (admission.folder / 'rejection.json').exists()
    assert (admission.directory / 'authorization.json').read_text() == '{"incomplete":'



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
@pytest.mark.parametrize('case,reason,attempted', [
    ('preexisting', 'preexisting_run', False), ('collision', 'lookup_rejected', False),
    ('unavailable', None, False), ('start-conflict', 'start_conflict', True),
])
def test_cycle_controller_conflicts_and_network_failure_keep_distinct_originals(controller_dispatch, case, reason, attempted):
    import asyncio

    _, admission, storage, operation = controller_dispatch
    result = asyncio.run(operation(case).run())
    assert result['status'] == ('rejected' if reason else 'unknown'), result
    assert result['runtime_status'] == ('queried' if reason else 'unconfirmed'), result
    assert (admission.folder / 'attempt.json').exists() is attempted
    rejected = admission.folder / 'rejection.json'
    assert rejected.exists() is (reason is not None)
    if reason is not None:
        record = json.loads(rejected.read_bytes())
        assert record['reason'] == reason
        before = {p: (p.read_bytes(), p.stat().st_ino) for p in admission.folder.iterdir() if p.is_file()}
        assert asyncio.run(operation('accepted').run())['status'] == 'rejected'
        assert {p: (p.read_bytes(), p.stat().st_ino) for p in admission.folder.iterdir() if p.is_file()} == before
    assert not (admission.folder / 'receipt.json').exists()
    calls = [json.loads(p.read_bytes()) for p in storage.glob('call-*.json')]
    assert sum(call['action'] == 'start' for call in calls) == int(attempted)



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
def test_cycle_controller_late_lookup_cannot_reject_a_concurrent_claim_or_hold_sqlite(controller_dispatch, monkeypatch):
    import asyncio

    state, admission, storage, operation = controller_dispatch
    late, start = operation(), operation()
    monkeypatch.setenv('ERGORA_TEST_CYCLE_DISPATCH_CASES', json.dumps({
        late.identity['operation_id']: 'late-lookup', start.identity['operation_id']: 'held-start'}))

    async def wait_for(path):
        async with asyncio.timeout(5):
            while not path.exists():
                await asyncio.sleep(.02)

    async def race():
        late_task = asyncio.create_task(late.run())
        starting = None
        try:
            await wait_for(storage / 'lookup-held')
            starting = asyncio.create_task(start.run())
            await wait_for(storage / 'start-held')
            # An independent writer completes while the actual SDK start is waiting.
            with state.connect() as db:
                db.execute('PRAGMA busy_timeout=100')
                db.execute('BEGIN IMMEDIATE')
                db.execute('UPDATE projects SET document=document WHERE id=?', ('demo',))
            (storage / 'release-lookup').touch()
            recovered = await late_task
            assert recovered['status'] == 'submitted' and not starting.done(), recovered
            assert not (admission.folder / 'rejection.json').exists()
            receipt = admission.folder / 'receipt.json'
            original = receipt.read_bytes(), receipt.stat().st_ino
            (storage / 'release-start').touch()
            acknowledged = await starting
            assert acknowledged['run_id'] == recovered['run_id'] and acknowledged['status'] == 'submitted'
            assert (receipt.read_bytes(), receipt.stat().st_ino) == original
        finally:
            for task in (late_task, starting):
                if task is not None and not task.done():
                    task.cancel()
            await asyncio.gather(*[task for task in (late_task, starting) if task is not None], return_exceptions=True)

    asyncio.run(race())
    calls = [json.loads(p.read_bytes()) for p in storage.glob('call-*.json')]
    assert sum(call['action'] == 'start' for call in calls) == 1



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
@pytest.mark.parametrize('case', ['stop-after-claim', 'project-after-claim'])
def test_cycle_controller_final_admission_preserves_consumed_slot_without_start(controller_dispatch, case):
    import asyncio

    _, admission, storage, operation = controller_dispatch
    result = asyncio.run(operation(case).run())
    assert result['status'] == 'unknown' and result['attempt_saved'] is True, result
    assert (admission.folder / 'attempt.json').exists() and not (admission.folder / 'receipt.json').exists()
    assert not (admission.folder / 'rejection.json').exists()
    calls = [json.loads(p.read_bytes()) for p in storage.glob('call-*.json')]
    assert not any(call['action'] == 'start' for call in calls)


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
@pytest.mark.parametrize('field,size,after_claim', [
    ('input', 32767, False), ('input', 32768, False), ('input', 32769, False),
    ('memo', 2047, False), ('memo', 2048, False), ('memo', 2049, False),
    ('input', 32769, True), ('memo', 2049, True)])
def test_cycle_controller_measures_actual_sdk_input_and_memo_at_both_send_gates(
        controller_dispatch, monkeypatch, field, size, after_claim):
    """Both versions use the original H owner and complete SDK encoding.

    Legal converter metadata expands the original fixed business shape. No extra
    input or Memo fields, rewritten ready gate, or synthetic start request is used.
    """
    import asyncio
    from temporalio.api.workflowservice.v1 import StartWorkflowExecutionRequest

    _, admission, storage, operation = controller_dispatch
    monkeypatch.setenv('ERGORA_TEST_CYCLE_DISPATCH_CAPACITY', json.dumps({
        'field': field, 'size': size, 'after_claim': after_claim}))
    result = asyncio.run(operation().run())
    encodings = json.loads((storage / 'encodings.json').read_bytes())
    exceeded = size > (32768 if field == 'input' else 2048)
    attempt = admission.folder / 'attempt.json'
    if exceeded:
        assert result['status'] == 'capacity_exceeded', result
        assert result['attempt_saved'] is after_claim and attempt.exists() is after_claim
        assert not (storage / 'request.pb').exists() and not (admission.folder / 'receipt.json').exists()
        assert not (admission.folder / 'rejection.json').exists()
        if after_claim:
            original = attempt.read_bytes(), attempt.stat().st_ino
            observed = asyncio.run(operation(mode='reconcile-controller').run())
            assert observed['attempt_saved'] and observed['status'] == 'unknown'
            assert (attempt.read_bytes(), attempt.stat().st_ino) == original
            assert json.loads((storage / 'encodings.json').read_bytes()) == encodings
    else:
        assert result['status'] == 'submitted', result
        request = StartWorkflowExecutionRequest.FromString((storage / 'request.pb').read_bytes())
        actual = request.input if field == 'input' else request.memo
        assert actual.ByteSize() == size
        assert (request.input.ByteSize() <= 32768 and request.memo.ByteSize() <= 2048)
        assert [entry['claimed'] for entry in encodings] == [False, True, True]
    calls = [json.loads(path.read_bytes()) for path in storage.glob('call-*.json')]
    assert sum(call['action'] == 'start' for call in calls) == (0 if exceeded else 1)
    assert all(entry['bytes'] == size for entry in encodings)


@pytest.mark.skipif(sys.platform != 'linux', reason='Encoding consumes the original Linux supervised H window')
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 4}], indirect=True)
def test_cycle_controller_final_encoding_cannot_renew_the_claimed_window(controller_dispatch, monkeypatch):
    import asyncio

    _, admission, storage, operation = controller_dispatch
    monkeypatch.setenv('ERGORA_TEST_CYCLE_DISPATCH_CAPACITY', json.dumps({
        'field': 'input', 'size': 32768, 'after_claim': True, 'blocked': True}))
    current = operation()
    result = asyncio.run(current.run())
    markers = Path(os.environ['ERGORA_TEST_CYCLE_MARKERS'])
    assert result['status'] == 'unknown' and admission.submission()['attempt_saved'], result
    assert (markers / 'dispatch-encoding-blocked').exists() and not (storage / 'request.pb').exists()
    assert not recorded_process_is_active(json.loads((markers / 'dispatch-encoding-blocked').read_bytes()))
    assert current.process.returncode is not None



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 4}], indirect=True)
def test_cycle_controller_attempt_sync_is_bounded_without_blocking_parent_loop(controller_dispatch):
    import asyncio

    _, admission, storage, operation = controller_dispatch
    current = operation('blocked-attempt-sync')
    markers = Path(os.environ['ERGORA_TEST_CYCLE_MARKERS'])
    live = []

    async def exercise():
        running = asyncio.create_task(current.run())
        while not running.done():
            if (markers / 'attempt-sync').exists():
                live.append(time.monotonic())
            await asyncio.sleep(.02)
        return await running

    result = asyncio.run(exercise())
    assert result['status'] == 'unknown' and len(live) >= 2, result
    assert (admission.folder / 'attempt.json').exists() and not (storage / 'request.pb').exists()
    assert current.process.returncode is not None
    assert not recorded_process_is_active(json.loads((markers / 'attempt-sync').read_bytes()))



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
def test_cycle_controller_cancelled_sdk_start_reaps_before_metadata_recovery(controller_dispatch):
    import asyncio

    _, admission, storage, operation = controller_dispatch
    current = operation('held-start')
    markers = Path(os.environ['ERGORA_TEST_CYCLE_MARKERS'])

    async def cancel_waiting_sdk():
        running = asyncio.create_task(current.run())
        try:
            async with asyncio.timeout(5):
                while not (storage / 'start-held').exists():
                    await asyncio.sleep(.02)
            owner = json.loads((markers / 'dispatch-helper').read_bytes())
        finally:
            running.cancel()
            with pytest.raises(asyncio.CancelledError):
                await running
        assert current.process.returncode is not None and not recorded_process_is_active(owner)

    asyncio.run(cancel_waiting_sdk())
    assert not (admission.folder / 'receipt.json').exists()
    attempt = admission.folder / 'attempt.json'
    original = attempt.read_bytes(), attempt.stat().st_ino
    recovered = asyncio.run(operation('accepted', 'reconcile-controller').run())
    assert recovered['status'] == 'submitted' and (attempt.read_bytes(), attempt.stat().st_ino) == original
    calls = [json.loads(p.read_bytes()) for p in storage.glob('call-*.json')]
    assert sum(call['action'] == 'start' for call in calls) == 1



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux supervised operation')
@pytest.mark.parametrize('controller_admission', [{'wall_seconds': 10, 'cleanup_seconds': 2, 'control_timeout_seconds': 5}], indirect=True)
def test_cycle_controller_reconcile_after_original_total_never_renews_execution(controller_dispatch, monkeypatch):
    import asyncio
    from ergora.runtime import budget_clock

    _, admission, storage, operation = controller_dispatch
    starting = operation('lost-reply')
    first = asyncio.run(starting.run())
    assert first['status'] == 'unknown', first
    assert (admission.folder / 'attempt.json').exists() and (storage / 'request.pb').exists()
    raw = (admission.directory / 'authorization.json').read_bytes()
    clock = admission.authorization['clock']
    wall_seconds = starting.payload['snapshot']['budget']['policy']['wall_seconds']
    while budget_clock.remaining(clock, wall_seconds) > 0:
        time.sleep(.02)
    expired = operation()
    create = asyncio.create_subprocess_exec

    async def forbidden_spawn(*args, **kwargs):
        raise AssertionError('Original computation expiry must prevent another submission spawn')

    monkeypatch.setattr(asyncio, 'create_subprocess_exec', forbidden_spawn)
    assert asyncio.run(expired.run())['status'] == 'unknown' and expired.process is None
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', create)
    recovered = asyncio.run(operation('accepted', 'reconcile-controller', inspection_timeout=5).run())
    assert recovered['status'] == 'submitted' and recovered['runtime_status'] == 'queried', recovered
    assert (admission.directory / 'authorization.json').read_bytes() == raw
    assert budget_clock.remaining(clock, wall_seconds) < 0



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_current_controller_birth_retains_sources_bytes_and_one_clock(controller_admission, monkeypatch):
    import ergora.training.cycles as training_cycles
    from ergora.training.execution_protocol import MEASUREMENT_SOURCES

    state, source, selected, authorized, admission = controller_admission
    authorization = authorized['authorization']
    assert authorization['schema_version'] == 5 and authorized['coverage']['execution_authorized'] is False
    assert set(authorization['measurement_sources']) == set(MEASUREMENT_SOURCES)
    package = PACKAGE_ROOT
    assert authorization['measurement_sources'] == {
        name: hashlib.sha256((package / name).read_bytes()).hexdigest() for name in MEASUREMENT_SOURCES}
    controller = authorization['controller']
    identity = {key: authorization[key] for key in ('control_home', 'project', 'cycle_id', 'input_sha256')}
    assert controller['protocol'] == controller['task_queue'] == 'ergora-training-cycle-v3'
    assert controller['workflow_id'] == 'ergora-training-cycle-v3' + '/' + training_cycles._sha(identity)
    original = {p: p.read_bytes() for p in admission.directory.rglob('*') if p.is_file()}
    (source / 'cycle.json').unlink()
    source.rmdir()
    monkeypatch.setattr(training_cycles, '_measurement_sources', lambda: pytest.fail('Ready retries cannot capture sources'))
    monkeypatch.setattr(training_cycles.budget_clock, 'authorize', lambda *args: pytest.fail('Ready retries cannot renew clocks'))
    monkeypatch.setattr(training, 'check_start', lambda *args: pytest.fail('Ready retries cannot repeat admissions'))
    again = training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert again['authorization'] == authorization and again['ready'] == authorized['ready']
    with pytest.raises(ValueError, match='consent mode'):
        training_cycles.authorize(state, 'demo', 'controller', source, selected['sha256'], 1, confirm=True)
    with pytest.raises(ValueError, match='different complete input'):
        training_cycles.authorize_controller(state, 'demo', 'controller', source, '0' * 64, 1,
            confirm=True, execute_selected=True)
    with pytest.raises(ValueError, match='revision changed'):
        training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 2,
            confirm=True, execute_selected=True)
    assert all(p.read_bytes() == raw for p, raw in original.items())
    # Shape is checked independently of the canonical digest, even offline.
    altered = deepcopy(authorization)
    altered['measurement_sources'].pop(MEASUREMENT_SOURCES[0])
    altered['sha256'] = training_cycles._sha({key: value for key, value in altered.items() if key != 'sha256'})
    (admission.directory / 'authorization.json').write_text(json.dumps(altered))
    with pytest.raises(ValueError, match='measurement source map'):
        training_cycles.status(state, 'demo', 'controller')
    # A well-shaped changed digest also fails the original complete authorization SHA.
    altered = deepcopy(authorization)
    altered['measurement_sources'][MEASUREMENT_SOURCES[0]] = '0' * 64
    (admission.directory / 'authorization.json').write_text(json.dumps(altered))
    with pytest.raises(ValueError, match='canonical SHA256'):
        training_cycles.status(state, 'demo', 'controller')


@pytest.mark.skipif(sys.platform != 'linux', reason='Original local recovery locks require Linux flock')
@pytest.mark.parametrize('boundary', ['lock-file', 'lock-directory', 'ready-directory'])
@pytest.mark.parametrize('source_state', ['matching', 'changed'])
def test_schema5_saved_recovery_keeps_original_map_and_clock(tmp_path, monkeypatch, boundary, source_state):
    """Existing static records recover locally; no public authorization or runtime opportunity."""
    import socket
    from types import SimpleNamespace
    import ergora.training.cycles as cycles
    import ergora.training.execution_protocol as protocol

    fixed_at = '2026-01-01T00:00:01+00:00'
    guards = {name: 0 for name in ('authorize', 'public_authorize', 'public_controller_authorize',
                                 'training_start', 'state', 'popen', 'network', 'uuid')}

    def forbidden(name):
        def fail(*args, **kwargs):
            guards[name] += 1
            raise AssertionError('Forbidden static recovery operation: ' + name)
        return fail

    monkeypatch.setattr(cycles.budget_clock, 'authorize', forbidden('authorize'))
    monkeypatch.setattr(cycles, 'authorize', forbidden('public_authorize'))
    monkeypatch.setattr(cycles, 'authorize_controller', forbidden('public_controller_authorize'))
    monkeypatch.setattr(training, 'start', forbidden('training_start'))
    monkeypatch.setattr(cycles, 'State', forbidden('state'))
    monkeypatch.setattr(subprocess, 'Popen', forbidden('popen'))
    monkeypatch.setattr(socket, 'create_connection', forbidden('network'))
    import uuid
    monkeypatch.setattr(uuid, 'uuid4', forbidden('uuid'))
    monkeypatch.setattr(cycles, 'now', lambda: fixed_at)
    home = tmp_path / 'control'
    state = SimpleNamespace(root=home)
    execution = {'installation': str(tmp_path / 'unused-native'), 'config_directory': str(tmp_path / 'unused-config'),
                 'state_directory': str(tmp_path / 'unused-state')}
    project = {'id': 'demo', 'revision': 1, 'repo': str(tmp_path / 'saved-source'),
        'schema_version': 1, 'created': '2026-01-01T00:00:00+00:00',
        'registration': {'operation_id': 'saved-registration', 'sha256': 'c' * 64,
                         'definition': {'execution': execution}, 'files': {}}}
    selected = {'experiment_id': 'saved-candidate', 'manifest_sha256': 'b' * 64}
    admission = {'experiment_id': selected['experiment_id'], 'manifest_sha256': selected['manifest_sha256']}
    plan = {'schema_version': 2, 'control_home': str(home), 'project': project,
        'definition': {'execution_scope': protocol.FULL_SCOPE, 'candidates': [selected],
            'budget': {'wall_seconds': 100, 'cleanup_seconds': 10}}, 'admissions': [admission]}
    plan_raw = (json.dumps(plan, sort_keys=True) + '\n').encode()
    saved_sources = {name: hashlib.sha256((PACKAGE_ROOT / name).read_bytes()).hexdigest()
                     for name in protocol.MEASUREMENT_SOURCES}
    if source_state == 'changed':
        saved_sources[next(iter(saved_sources))] = '0' * 64
    clock = {'authorized_at': '2026-01-01T00:00:00+00:00', 'deadline_at': '2026-01-01T00:01:40+00:00',
             'boot_id': '1' * 36, 'boottime_ns': 100}
    input_sha = hashlib.sha256(plan_raw).hexdigest()
    body = {'schema_version': 5, 'kind': 'training-cycle-authorization', 'control_home': str(home),
        'project': 'demo', 'cycle_id': 'saved-cycle', 'project_revision': project['revision'],
        'input_sha256': input_sha, 'registration': {'operation_id': 'saved-registration', 'intent_sha256': 'd' * 64},
        'execution': execution, 'measurement_sources': saved_sources, 'clock': clock,
        'controller': {'protocol': protocol.CYCLE_TASK_QUEUE_V3, 'task_queue': protocol.CYCLE_TASK_QUEUE_V3,
            'workflow_id': protocol.CYCLE_TASK_QUEUE_V3 + '/' + cycles._sha({'control_home': str(home),
                'project': 'demo', 'cycle_id': 'saved-cycle', 'input_sha256': input_sha}),
            'execution_scope': protocol.FULL_SCOPE, 'continuation': 'accepted-archive-pass',
            'actor_id': 'unix:1000:static-data', 'confirmation': True}}
    authorization = {**body, 'sha256': cycles._sha(body)}
    directory = home / 'training-cycles/demo/saved-cycle'
    directory.mkdir(parents=True)
    original_lock = directory.parent / '.saved-cycle.lock'
    original_lock.write_bytes(b'')
    (directory / 'cycle.json').write_bytes(plan_raw)
    auth_raw = (json.dumps(authorization, sort_keys=True) + '\n').encode()
    (directory / 'authorization.json').write_bytes(auth_raw)
    folder = directory / 'controller'
    if boundary != 'lock-directory':
        folder.mkdir()
    if boundary == 'ready-directory':
        (folder / 'admission.lock').write_bytes(b'')
        (directory / 'ready.json').write_text(json.dumps({'schema_version': 1, 'kind': 'training-cycle-ready',
            'authorization_sha256': authorization['sha256'], 'admissions_sha256': cycles._sha(plan['admissions']),
            'project_revision': 1, 'checked_at': fixed_at}))

    def load(actual_home, actual_project, actual_cycle, actual_directory):
        assert (actual_home, actual_project, actual_cycle, actual_directory) == (home, 'demo', 'saved-cycle', directory)
        assert (directory / 'cycle.json').read_bytes() == plan_raw
        assert (directory / 'authorization.json').read_bytes() == auth_raw
        ready_path = directory / 'ready.json'
        return deepcopy(plan), deepcopy(authorization), json.loads(ready_path.read_bytes()) if ready_path.exists() else None

    def observe(state, plan, authorization, ready):
        return {'status': 'pending' if ready is None else 'ready', 'authorization': deepcopy(authorization),
                'authorization_sha256': authorization['sha256'], 'ready': ready}

    monkeypatch.setattr(cycles, '_load', load)
    monkeypatch.setattr(cycles, '_status', observe)
    monkeypatch.setattr(training, '_project', lambda *args: deepcopy(project))
    admission_reads = []

    def saved_admission(*args):
        assert args == (state, 'demo', selected['experiment_id'], selected['manifest_sha256'])
        admission_reads.append(args)
        return deepcopy(admission)

    monkeypatch.setattr(training, 'check_start', saved_admission)
    current_reader = cycles._measurement_sources
    monkeypatch.setattr(cycles, '_measurement_sources',
        lambda: pytest.fail('Saved status cannot recapture current source bytes'))
    observed = cycles.status(state, 'demo', 'saved-cycle', authorization_sha256=authorization['sha256'])
    assert observed['authorization'] == authorization
    assert (observed['ready'] is not None) is (boundary == 'ready-directory')
    current_reads = []

    def current_sources():
        value = current_reader()
        current_reads.append(value)
        return value

    monkeypatch.setattr(cycles, '_measurement_sources', current_sources)
    try:
        if boundary != 'ready-directory' and source_state == 'changed':
            with pytest.raises(ValueError, match='measurement sources changed'):
                cycles._authorize(state, 'demo', 'saved-cycle', tmp_path / 'absent-input', body['input_sha256'],
                                  1, confirm=True, controller=True)
            assert not (directory / 'ready.json').exists() and not admission_reads
        else:
            recovered = cycles._authorize(state, 'demo', 'saved-cycle', tmp_path / 'absent-input', body['input_sha256'],
                                          1, confirm=True, controller=True)
            assert recovered['status'] == 'ready' and recovered['authorization'] == authorization
            assert recovered['ready']['authorization_sha256'] == authorization['sha256']
            assert (folder / 'admission.lock').read_bytes() == b''
        assert bool(current_reads) is (boundary != 'ready-directory')
        if source_state == 'matching':
            assert all(value == authorization['measurement_sources'] for value in current_reads)
        assert (directory / 'cycle.json').read_bytes() == plan_raw
        assert (directory / 'authorization.json').read_bytes() == auth_raw
        assert authorization['clock'] == clock and original_lock.read_bytes() == b''
    finally:
        (tmp_path / 'recovery-counters.json').write_text(json.dumps({'scope': 'fixed schema5 saved-record recovery only',
            'bound_refusal_guards': guards, 'current_source_reads': len(current_reads),
            'static_admission_reads': len(admission_reads)}, indent=2) + '\n')
        assert all(value == 0 for value in guards.values())


def _saved_measurement_subject(controller_admission):
    """Persist original saved source bytes without admitting the current implementation."""
    import ergora.training.cycles as training_cycles
    from ergora.training.execution_protocol import CycleAdmission, MEASUREMENT_SOURCES

    state, source, selected, authorized, admission = controller_admission
    authorization = deepcopy(authorized['authorization'])
    authorization['measurement_sources'] = {
        name: hashlib.sha256(('saved measurement data: ' + name).encode()).hexdigest()
        for name in MEASUREMENT_SOURCES}
    authorization['sha256'] = training_cycles._sha({key: value for key, value in authorization.items() if key != 'sha256'})
    ready = {**authorized['ready'], 'authorization_sha256': authorization['sha256']}
    (admission.directory / 'authorization.json').write_text(json.dumps(authorization))
    (admission.directory / 'ready.json').write_text(json.dumps(ready))
    return state, source, selected, authorization, CycleAdmission(admission.directory, authorization)


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller records require Linux clocks and flock')
@pytest.mark.parametrize('receipt_saved', [False, True])
def test_saved_measurement_subject_observes_and_stops_without_current_sources(
        controller_admission, monkeypatch, receipt_saved):
    import ergora.training.cycles as training_cycles
    import ergora.training.execution_protocol as protocol

    state, _, _, authorization, admission = _saved_measurement_subject(controller_admission)
    save_controller_binding(admission)
    if not receipt_saved:
        (admission.folder / 'receipt.json').unlink()
    lock = admission.directory.parent / '.controller.lock'
    before = {path: (path.read_bytes(), path.stat().st_ino)
              for path in (*admission.directory.rglob('*'), lock) if path.is_file()}

    def forbidden(*args, **kwargs):
        pytest.fail('Saved observation and storage stop cannot admit current work or read current sources')

    monkeypatch.setattr(training_cycles, '_measurement_sources', forbidden)
    monkeypatch.setattr(training_cycles.budget_clock, 'authorize', forbidden)
    monkeypatch.setattr(training_cycles, '_record', forbidden)
    monkeypatch.setattr(training, 'check_start', forbidden)
    monkeypatch.setattr(protocol, '_CycleOperation', forbidden)
    monkeypatch.setattr(protocol, 'source_capability', forbidden)
    monkeypatch.setattr(protocol, 'validate_sources', forbidden)
    observed = training_cycles.status(state, 'demo', 'controller', authorization_sha256=authorization['sha256'])
    assert observed['authorization'] == authorization and observed['coverage']['execution_authorized'] is False
    assert observed['ready']['authorization_sha256'] == authorization['sha256']
    assert observed['ready']['admissions_sha256'] == training_cycles._sha(
        training_cycles._load(state.root, 'demo', 'controller', admission.directory)[0]['admissions'])
    submission = training_cycles.controller(state, 'demo', 'controller', authorization['sha256'], 'status')
    assert submission['status'] == ('submitted' if receipt_saved else 'unknown')
    assert submission['attempt_saved'] is True and submission['result_saved'] is receipt_saved
    assert submission['read_only'] is True and submission['execution_authorized'] is False
    with pytest.raises(ValueError, match='expected complete canonical SHA256'):
        training_cycles.status(state, 'demo', 'controller', authorization_sha256='0' * 64)
    stopped = training_cycles.controller(state, 'demo', 'controller', authorization['sha256'], 'stop', reason='Original storage stop')
    assert stopped['stop_visible'] is True and stopped['stop_durable'] is True
    stop_raw, stop_inode = admission.stop.read_bytes(), admission.stop.stat().st_ino
    stop = json.loads(stop_raw)
    assert all(stop[key] == value for key, value in admission.identity.items())
    assert stop['controller_intent_sha256'] == submission['intent_sha256']
    assert training_cycles.controller(state, 'demo', 'controller', authorization['sha256'], 'status') == submission
    after = training_cycles.status(state, 'demo', 'controller', authorization_sha256=authorization['sha256'])
    assert after['status'] == 'stopped' and after['authorization'] == authorization
    training_cycles.stop_controller(state, 'demo', 'controller', authorization['sha256'], reason='Cannot replace original stop')
    assert (admission.stop.read_bytes(), admission.stop.stat().st_ino) == (stop_raw, stop_inode)
    assert all((path.read_bytes(), path.stat().st_ino) == original for path, original in before.items())
    assert {path for path in admission.directory.rglob('*') if path.is_file()} == (set(before) - {lock}) | {admission.stop}


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller records require Linux clocks and flock')
def test_saved_measurement_subject_cannot_complete_ready_prepare_or_claim(controller_admission, monkeypatch):
    import ergora.training.cycles as training_cycles

    state, source, selected, authorization, admission = _saved_measurement_subject(controller_admission)
    intent = saved_controller_intent(admission)
    (admission.folder / 'intent.json').write_text(json.dumps(intent))
    original = {path: path.read_bytes() for path in admission.directory.rglob('*') if path.is_file()}
    assert training_cycles.status(state, 'demo', 'controller')['authorization'] == authorization
    with pytest.raises(ValueError, match='measurement sources changed'):
        training_cycles.prepare_controller(state, 'demo', 'controller', authorization['sha256'], 1)
    with pytest.raises(ValueError, match='measurement sources changed'):
        training_cycles._claim_controller(state, admission)
    assert {path: path.read_bytes() for path in admission.directory.rglob('*') if path.is_file()} == original
    (admission.directory / 'ready.json').unlink()
    monkeypatch.setattr(training, 'check_start', lambda *args: pytest.fail('Old sources cannot repeat live admission'))
    with pytest.raises(ValueError, match='measurement sources changed'):
        training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 1,
            confirm=True, execute_selected=True)
    assert not (admission.directory / 'ready.json').exists() and not (admission.folder / 'attempt.json').exists()
    assert all(path.read_bytes() == raw for path, raw in original.items() if path.name != 'ready.json')


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller records require Linux clocks and flock')
@pytest.mark.parametrize('fault', ['missing', 'extra', 'unsafe', 'digest', 'canonical', 'ready'])
def test_saved_measurement_subject_rejects_malformed_or_conflicting_identity(controller_admission, monkeypatch, fault):
    import ergora.training.cycles as training_cycles

    state, _, _, authorization, admission = _saved_measurement_subject(controller_admission)
    sources = authorization['measurement_sources']
    name = next(iter(sources))
    if fault == 'missing':
        sources.pop(name)
    elif fault == 'extra':
        sources['extra.py'] = '1' * 64
    elif fault == 'unsafe':
        sources['../outside.py'] = sources.pop(name)
    elif fault == 'digest':
        sources[name] = 'A' * 64
    elif fault == 'canonical':
        sources[name] = '0' * 64
    else:
        ready = json.loads((admission.directory / 'ready.json').read_bytes())
        ready['authorization_sha256'] = '0' * 64
        (admission.directory / 'ready.json').write_text(json.dumps(ready))
    if fault not in ('canonical', 'ready'):
        authorization['sha256'] = training_cycles._sha({key: value for key, value in authorization.items() if key != 'sha256'})
    (admission.directory / 'authorization.json').write_text(json.dumps(authorization))
    monkeypatch.setattr(training_cycles, '_measurement_sources', lambda: pytest.fail('Malformed saved data cannot read current sources'))
    for action in ('status', 'stop'):
        with pytest.raises(ValueError):
            training_cycles.controller(state, 'demo', 'controller', authorization['sha256'], action, reason='Invalid identity')
    assert not admission.stop.exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch requires Linux clocks and flock')
@pytest.mark.parametrize('source_read', [1, 2])
def test_measurement_source_read_consumes_original_allowance_before_attempt_and_send(
        controller_dispatch, monkeypatch, source_read):
    import asyncio
    from types import SimpleNamespace
    from temporalio.client import Client
    import ergora.training.cycles as training_cycles
    import ergora.training.runtime.worker as worker
    from fixtures.training_controller_service import DispatchService

    state, admission, storage, operation = controller_dispatch
    current = operation()
    plan = training_cycles._load(state.root, 'demo', 'controller', admission.directory)[0]
    sdk = DispatchService(current.payload, 'accepted')

    async def connect():
        return Client(sdk)

    monkeypatch.setattr(worker, '_select_cycle_project', lambda *args: SimpleNamespace(registration=lambda: None))
    monkeypatch.setitem(sys.modules, 'perf_temporal.connection', SimpleNamespace(connect=connect))
    remaining = training_cycles.budget_clock.remaining
    source_reader = training_cycles._measurement_sources
    reads = []

    def read_sources():
        result = source_reader()
        reads.append(result)
        return result

    monkeypatch.setattr(training_cycles, '_measurement_sources', read_sources)
    monkeypatch.setattr(training_cycles.budget_clock, 'remaining', lambda *args, **kwargs:
        plan['definition']['budget']['cleanup_seconds'] if len(reads) >= source_read else remaining(*args, **kwargs))
    before = {path: path.read_bytes() for path in admission.directory.rglob('*') if path.is_file()}
    result = asyncio.run(worker._dispatch_controller(current.payload, plan, admission, lambda: None))
    assert result['status'] == 'unknown' and 'deadline has passed' in result['reason']
    assert len(reads) == source_read and all(item == admission.authorization['measurement_sources'] for item in reads)
    assert not (admission.folder / 'attempt.json').exists() and not (storage / 'request.pb').exists()
    assert not any(json.loads(path.read_bytes())['action'] == 'start' for path in storage.glob('call-*.json'))
    assert {path: path.read_bytes() for path in admission.directory.rglob('*') if path.is_file()} == before


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_current_controller_intent_and_claim_keep_original_sources_and_refuse_manual_binding(
        controller_admission, cycle_selection, service, monkeypatch):
    import ergora.training.runtime.worker as worker
    import ergora.training.cycles as training_cycles

    state, source, selected, authorized, admission = controller_admission
    _, _, runtime, _, _, request = cycle_selection
    original_sources = training_cycles._measurement_sources()
    source_reader = training_cycles._read_bytes
    target = PACKAGE_ROOT / next(iter(original_sources))
    monkeypatch.setattr(training_cycles, '_read_bytes',
        lambda path, limit: source_reader(path, limit) + b'\n# simulated drift\n' if path == target else source_reader(path, limit))
    assert training_cycles.status(state, 'demo', 'controller')['authorization'] == authorized['authorization']
    with pytest.raises(ValueError, match='measurement sources changed'):
        training_cycles.prepare_controller(state, 'demo', 'controller', authorized['authorization_sha256'], 1)
    assert not (admission.folder / 'intent.json').exists()
    monkeypatch.setattr(training_cycles, '_read_bytes', source_reader)
    first = training_cycles.prepare_controller(state, 'demo', 'controller', authorized['authorization_sha256'], 1)
    raw = (admission.folder / 'intent.json').read_bytes()
    second = training_cycles.prepare_controller(state, 'demo', 'controller', authorized['authorization_sha256'], 1)
    assert first['created'] is True and second['created'] is False
    assert first['intent'] == second['intent'] == admission.intent_record()
    assert (admission.folder / 'intent.json').read_bytes() == raw
    assert set(first['intent']['workflow_input']) == {
        'protocol', 'control_home', 'project', 'cycle_id', 'input_sha256', 'authorization_sha256'}
    with monkeypatch.context() as drift:
        drift.setattr(training_cycles, '_read_bytes', lambda path, limit:
            source_reader(path, limit) + b'\n# changed current bytes\n' if path == target else source_reader(path, limit))
        with pytest.raises(ValueError, match='measurement sources changed'):
            training_cycles._claim_controller(state, admission)
    assert not (admission.folder / 'attempt.json').exists()
    assert training_cycles._claim_controller(state, admission) is True
    attempt_path = admission.folder / 'attempt.json'
    attempt = attempt_path.read_bytes(), attempt_path.stat().st_ino
    assert training_cycles._claim_controller(state, admission) is False
    # Readonly current inspection and preparation retain the original start slot.
    import asyncio
    plan = training_cycles._load(state.root, 'demo', 'controller', admission.directory)[0]
    snapshot = worker._cycle_snapshot(admission.directory, plan, authorized['authorization'])
    original = {path: path.read_bytes() for path in admission.directory.rglob('*') if path.is_file()}
    for mode, source_snapshot in (('inspect', None), ('prepare-controller', snapshot)):
        operation = worker._CycleOperation(state.root, 'demo', 'controller', authorized['authorization_sha256'],
            mode, snapshot=source_snapshot)
        cold = asyncio.run(operation.run())
        if mode == 'inspect':
            assert cold['status'] == 'inspected'
        else:
            assert cold['status'] == 'prepared' and cold['created'] is False
            assert cold['intent_sha256'] == training_cycles._sha(first['intent'])
        assert cold['operation_stopped'] is True and operation.process.returncode == 0
        assert operation.response.frames[0]['process']['status'] == 'succeeded'
        assert {path: path.read_bytes() for path in admission.directory.rglob('*') if path.is_file()} == original
    service[0]('accepted')
    digest = request['candidates'][0]['manifest_sha256']
    for cycle_entry in (True, False):
        with pytest.raises(ValueError):
            if cycle_entry:
                training_cycles.start(state, 'demo', 'controller', 'alpha', authorized['authorization_sha256'], 1)
            else:
                training.start(state, 'demo', 'alpha', 1, digest,
                    budget={'cycle_id': 'controller', 'authorization_sha256': authorized['authorization_sha256']})
    assert (attempt_path.read_bytes(), attempt_path.stat().st_ino) == attempt and not service[1].exists()
    prefix = runtime / 'ergora/training-submissions'
    assert not (prefix / 'alpha.intent.json').exists() and not (prefix / 'alpha.attempt.json').exists()
    assert not (prefix / 'alpha.budget').exists() and not (runtime / 'training/jobs/alpha').exists()
    monkeypatch.setattr(training_cycles, '_read_bytes',
        lambda path, limit: source_reader(path, limit) + b'\n# simulated drift\n' if path == target else source_reader(path, limit))
    with pytest.raises(ValueError, match='measurement sources changed'):
        training_cycles.prepare_controller(state, 'demo', 'controller', authorized['authorization_sha256'], 1)
    assert (admission.folder / 'intent.json').read_bytes() == raw
    # The saved authorization never adopts the drift, including an explicit retry.
    assert training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)['authorization']['measurement_sources'] == original_sources
    with monkeypatch.context() as expired:
        expired.setattr(training_cycles.budget_clock, 'remaining', lambda *args, **kwargs: 0)
        with pytest.raises(ValueError, match='deadline has passed'):
            training_cycles.prepare_controller(state, 'demo', 'controller', authorized['authorization_sha256'], 1)
    assert (admission.folder / 'intent.json').read_bytes() == raw
    stopped = training_cycles.stop_controller(state, 'demo', 'controller', authorized['authorization_sha256'], reason='Storage-only stop')
    assert stopped['stop_visible'] is True and stopped['stop_durable'] is True
    assert training_cycles.status(state, 'demo', 'controller')['status'] == 'stopped'
    with pytest.raises(ValueError):
        training_cycles.prepare_controller(state, 'demo', 'controller', authorized['authorization_sha256'], 1)
    assert (attempt_path.read_bytes(), attempt_path.stat().st_ino) == attempt


@pytest.mark.skipif(sys.platform != 'linux', reason='Managed native callback requires Linux')
@pytest.mark.parametrize('installation', ['managed'], indirect=True)
def test_current_controller_native_callback_refuses_legacy_budget_binding_and_keeps_completed_read(
        controller_admission, request):
    import ergora.training.cycles as training_cycles

    state, _, _, authorized, admission = controller_admission
    _, definition, runtime, folder = request.getfixturevalue('historical_execution')
    sha = training_cycles._sha
    prefix = runtime / 'ergora/training-submissions'
    intent = json.loads((prefix / 'alpha.intent.json').read_bytes())
    intent['budget'].update(cycle_id='controller', authorization_sha256=authorized['authorization_sha256'])
    plan = training_cycles._load(state.root, 'demo', 'controller', admission.directory)[0]
    context = {'intent': intent, 'authorization': authorized['authorization'], 'policy': plan['definition']['budget'],
               'project': plan['project'], 'published_project': plan['project']}
    owner_path = prefix / 'alpha.budget/owner.json'
    owner = json.loads(owner_path.read_bytes())
    owner.update(intent_sha256=sha(intent), authorization_sha256=authorized['authorization_sha256'], context_sha256=sha(context))
    def save(path, value):
        path.write_text(json.dumps(value))
    save(prefix / 'alpha.intent.json', intent)
    save(owner_path, owner)
    for name in ('attempt', 'result'):
        path = prefix / ('alpha.' + name + '.json')
        value = json.loads(path.read_bytes())
        value['intent_sha256'] = sha(intent)
        save(path, value)
    for name in ('attempt', 'ack', 'stopped'):
        (folder / (name + '.json')).unlink()
    # Rebind the retained historical fixture's consumed request and launch, with
    # no live owner or grants. The actual native reader still validates the chain.
    execution_request = json.loads((folder / 'request.json').read_bytes())
    execution_request.update(start_intent_sha256=sha(intent), owner_sha256=sha(owner),
        authorization_sha256=authorized['authorization_sha256'],
        start_attempt_sha256=sha(json.loads((prefix / 'alpha.attempt.json').read_bytes())),
        start_receipt_sha256=sha(json.loads((prefix / 'alpha.result.json').read_bytes())))
    save(folder / 'request.json', execution_request)
    launch = json.loads((folder / 'launch.json').read_bytes())
    launch.update(request_sha256=sha(execution_request), owner_sha256=sha(owner),
        authorization_sha256=authorized['authorization_sha256'], clock_sha256=sha(authorized['authorization']['clock']))
    save(folder / 'launch.json', launch)
    installation = Path(definition['execution']['installation'])
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
        AGENTFLOW_CONFIG_DIR=definition['execution']['config_directory'],
        AGENTFLOW_STATE_DIR=definition['execution']['state_directory'],
        PYTHONPATH=os.pathsep.join(map(str, (IMPORT_ROOT,
            installation / 'local', installation / 'upstream/platform', installation / 'upstream/temporal', installation / 'upstream'))))
    command = [str(installation / '.venv/bin/python'), '-B', '-P',
        str(Path(__file__).parent / 'fixtures/training_executor_client.py'),
        'native-context-isolated', str(folder.parent)]
    before = {path: path.read_bytes() for path in folder.parent.rglob('*') if path.is_file()}
    result = subprocess.run(command, input=json.dumps({'cached': context, 'phase': {}}), env=environment,
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['error_type'] == 'ValueError'
    assert {path: path.read_bytes() for path in folder.parent.rglob('*') if path.is_file() and path.name != 'executor.lock'} == before
    assert not any((folder.parent / name).exists() for name in ('started.json', 'repo.git', 'run-output'))
    assert not any((folder / (name + '.json')).exists() for name in ('attempt', 'ack', 'stopped'))
    # Existing native results remain readable without rerunning admission.
    native = json.loads((folder.parent / 'request.json').read_bytes())
    completed = {'job_id': native['job_id'], 'binding': native['experiment']['binding'],
                 'state': 'SUCCEEDED', 'detail': 'Retained synthetic completed result'}
    save(folder.parent / 'result.json', completed)
    again = subprocess.run(command, input=json.dumps({'cached': context, 'phase': {}}), env=environment,
        capture_output=True, text=True, timeout=15)
    assert again.returncode == 0, again.stderr
    assert json.loads(again.stdout) == completed
    assert not (folder.parent / 'started.json').exists() and not (folder / 'attempt.json').exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_controller_original_type_is_authenticated_read_only(controller_admission, tmp_path, monkeypatch):
    import asyncio
    from temporalio.client import Client
    import ergora.training.cycles as training_cycles
    from ergora.training.runtime.status import lookup_controller_submission
    from fixtures.training_controller_service import DispatchService

    state, _, _, authorized, admission = controller_admission
    prepared = training_cycles.prepare_controller(state, 'demo', 'controller', authorized['authorization_sha256'], 1)
    storage = tmp_path / 'read-only-sdk'
    storage.mkdir()
    monkeypatch.setenv('ERGORA_TEST_CYCLE_DISPATCH', str(storage))
    payload = {'identity': prepared['intent']['workflow_input']}
    sdk = DispatchService(payload, 'preexisting')
    before = {path: path.read_bytes() for path in admission.directory.rglob('*') if path.is_file()}
    found = asyncio.run(lookup_controller_submission(Client(sdk), prepared['intent'], run_id=None, timeout=2))
    assert found[1].run_id == sdk.run_id
    if authorized['authorization']['schema_version'] == 5:
        sdk.case = 'v1-type'
        with pytest.raises(ValueError, match='controller type'):
            asyncio.run(lookup_controller_submission(Client(sdk), prepared['intent'], run_id=sdk.run_id, timeout=2))
    assert all(json.loads(path.read_bytes())['action'] != 'start' for path in storage.glob('call-*.json'))
    assert {path: path.read_bytes() for path in admission.directory.rglob('*') if path.is_file()} == before
    assert not (admission.folder / 'attempt.json').exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Original analysis clocks and supervising process identity require Linux/WSL2')
def test_analysis_remaining_observes_time_after_original_stop_io(tmp_path, monkeypatch):
    """A slow original stop/source read must not return a cached positive cap."""
    from ergora.runtime import budget_clock
    import ergora.training.cycles as training_cycles
    import ergora.training.execution_protocol as protocol

    boot, ticks = budget_clock._clock()
    parent = protocol.processes.identity(os.getpid())
    elapsed = [0]
    operation = {'identity': {'parent': parent, 'control_home': str(tmp_path), 'project': 'demo', 'cycle_id': 'cycle'},
        'snapshot': {'budget': {'policy': {'wall_seconds': 100, 'cleanup_seconds': 1}, 'clock': {}}}}
    authority = {'operation': operation, 'maximum_seconds': 1, 'preparation': {}}
    monkeypatch.setattr(protocol, 'validate_cycle_operation', lambda value: None)
    monkeypatch.setattr(protocol, '_cycle_authorization', lambda value: {})
    monkeypatch.setattr(protocol, 'read_cycle_supervisor', lambda value, **kwargs: None)
    monkeypatch.setattr(protocol, 'read_trial_reference', lambda value: {'boot_id': boot, 'started_ns': ticks})
    monkeypatch.setattr(protocol, 'cycle_operation_remaining', lambda value: 100)
    monkeypatch.setattr(budget_clock, 'remaining', lambda *args: 100)
    monkeypatch.setattr(budget_clock, '_clock', lambda: (boot, ticks + elapsed[0]))

    class OriginalAdmission:
        def __init__(self, *args):
            pass

        def check(self):
            elapsed[0] = 2_000_000_000

    monkeypatch.setattr(protocol, 'CycleAdmission', OriginalAdmission)
    with pytest.raises(ValueError, match='allowance ended'):
        training_cycles.analysis_authority_remaining(authority)


@pytest.mark.skipif(sys.platform != 'linux', reason='Direct parent identity and original descendant waits require Linux')
def test_cycle_helper_denies_effect_after_actual_direct_supervisor_dies(tmp_path):
    import ergora

    environment = {**os.environ, 'PYTHONPATH': str(Path(ergora.__file__).parent.parent)}
    result = subprocess.run([sys.executable, '-S', '-P',
        str(Path(__file__).parent / 'fixtures/training_cycle_supervisor_identity.py'), 'P', str(tmp_path / 'owned')],
        env=environment, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert observed['observed']['state'] == 'blocked'
    assert observed['observed']['parent'] == observed['outer']['pid']
    assert observed['waited'] and all(item['wait_pid'] is not None for item in observed['waited'])


@pytest.mark.skipif(sys.platform != 'linux', reason='Original analysis clocks and supervising process identity require Linux/WSL2')
def test_analysis_tail_readback_cannot_advance_after_original_slot_cap(tmp_path, monkeypatch):
    """The H caller must recheck its own cap after the final original-run reader."""
    from contextlib import nullcontext
    from types import SimpleNamespace
    import ergora.agents.runs as agent_runs
    from ergora.runtime import budget_clock
    import ergora.training.cycles as training_cycles
    import ergora.training.execution_protocol as protocol
    import ergora.training.runtime.worker as worker

    boot, ticks = budget_clock._clock()
    elapsed, inspected = [0], []
    state = SimpleNamespace(root=tmp_path / 'control')
    authorization = {'sha256': 'a' * 64, 'control_home': str(state.root)}
    admission = SimpleNamespace(authorization=authorization, folder=tmp_path / 'cycle/controller',
        directory=tmp_path / 'cycle', permission=lambda: nullcontext())
    packet, ordinal, phase = {'kind': 'complete-test-packet'}, 0, 'screen'
    operation = {'identity': {'operation_id': 'b' * 32, 'parent': protocol.processes.identity(os.getpid()),
        'control_home': str(state.root), 'project': 'demo', 'cycle_id': 'cycle'},
        'snapshot': {'budget': {'policy': {'wall_seconds': 100, 'cleanup_seconds': 1}, 'clock': {}}}}
    preparation_path = tmp_path / 'preparation.json'
    preparation_path.write_text(json.dumps({'boot_id': boot, 'started_ns': ticks}))
    preparation_raw = preparation_path.read_bytes()
    authority = {'operation': operation, 'packet': packet, 'maximum_seconds': 1, 'preparation': {
        'path': str(preparation_path), 'bytes': len(preparation_raw), 'sha256': hashlib.sha256(preparation_raw).hexdigest()}}
    opportunity = agent_runs.cycle_analysis_path(state.root, authorization['sha256'], ordinal, phase)
    opportunity.mkdir(parents=True)
    (opportunity / 'intent.json').write_text(json.dumps({'authority': authority, 'run_id': 'c' * 32}))
    folder = admission.folder / 'analysis/screen-0'
    folder.mkdir(parents=True)
    (folder / 'packet.json').write_text(json.dumps(packet))
    receipt = tmp_path / 'receipt.json'
    receipt.write_text(json.dumps({'receipt': {'outcome': 'provisional'}}))

    def inspect(*args, **kwargs):
        inspected.append(args)
        elapsed[0] = 2_000_000_000
        return {'outcome': 'provisional', 'receipt': {'path': str(receipt),
            'sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}}

    monkeypatch.setattr(worker, 'State', lambda root: state)
    monkeypatch.setattr(agent_runs, 'inspect_cycle_analysis', inspect)
    monkeypatch.setattr(protocol, 'validate_cycle_operation', lambda value: None)
    monkeypatch.setattr(protocol, '_cycle_authorization', lambda value: {})
    monkeypatch.setattr(protocol, 'read_cycle_supervisor', lambda value, **kwargs: None)
    monkeypatch.setattr(protocol, 'cycle_operation_remaining', lambda value: 100)
    monkeypatch.setattr(budget_clock, 'remaining', lambda *args: 100)
    monkeypatch.setattr(budget_clock, '_clock', lambda: (boot, ticks + elapsed[0]))
    monkeypatch.setattr(protocol, 'CycleAdmission', lambda *args: SimpleNamespace(check=lambda: None))
    plan = {'project': {'id': 'demo'}, 'analyst': {}}
    with pytest.raises(ValueError, match='allowance ended'):
        worker._trial_analysis(operation, plan, admission, {}, lambda: None,
            lambda: pytest.fail('An occupied analyst opportunity only inspects its original run'), phase, ordinal)
    assert len(inspected) == 1


@pytest.mark.skipif(sys.platform != 'linux', reason='Original controller stop and flock require Linux')
@pytest.mark.parametrize('failure', ['before-controller-folder', 'before-admission-lock'])
def test_partial_controller_birth_can_be_stopped_without_creating_a_lock(cycle_selection, tmp_path, monkeypatch, failure):
    """A rejected live birth retains its clock but must still accept a null-intent veto."""
    import ergora.training.cycles as training_cycles
    import ergora.training.execution_protocol as protocol

    state, _, _, _, _, request = cycle_selection
    source = tmp_path / 'partial-birth-input'
    selected = training_cycles.create(state, 'demo', request, source)
    cycle_id = 'partial-' + failure
    directory = state.root / 'training-cycles/demo' / cycle_id
    calls = []
    original_sources = training_cycles._measurement_sources
    original_record = training_cycles._record_bytes

    def source_check():
        calls.append('source')
        if failure == 'before-controller-folder' and len(calls) == 2:
            raise OSError('Original live birth check was rejected')
        return original_sources()

    def save(path, raw, limit):
        if failure == 'before-admission-lock' and path.name == 'admission.lock':
            raise OSError('Original live birth check was rejected')
        return original_record(path, raw, limit)

    monkeypatch.setattr(training_cycles, '_measurement_sources', source_check)
    monkeypatch.setattr(training_cycles, '_record_bytes', save)
    with pytest.raises(OSError, match='Original live birth check was rejected'):
        training_cycles.authorize_controller(state, 'demo', cycle_id, source, selected['sha256'], 1,
            confirm=True, execute_selected=True)
    authorization_path = directory / 'authorization.json'
    authorization_raw = authorization_path.read_bytes()
    authorization_inode = authorization_path.stat().st_ino
    authorization = json.loads(authorization_raw)
    cycle_raw = (directory / 'cycle.json').read_bytes()
    admission = protocol.CycleAdmission(directory, authorization)
    assert not (directory / 'ready.json').exists()
    assert not admission.lock.exists() and not (admission.folder / 'intent.json').exists()
    assert admission.folder.exists() is (failure == 'before-admission-lock')
    monkeypatch.setattr(training_cycles.budget_clock, 'authorize', lambda *args: pytest.fail('Stop cannot renew a born clock'))
    monkeypatch.setattr(training_cycles.budget_clock, 'remaining', lambda *args: -1)
    stopped = training_cycles.stop_controller(state, 'demo', cycle_id, authorization['sha256'], reason='Cancel rejected original birth')
    assert stopped['stop_visible'] is True and stopped['identity_matches'] is True and stopped['stop_durable'] is True
    assert stopped['record']['controller_intent_sha256'] is None
    assert stopped['admission_drained'] is None and stopped['executor_stop_confirmed'] is None
    assert not admission.lock.exists() and not (admission.folder / 'intent.json').exists()
    with pytest.raises(FileNotFoundError):
        with admission.permission():
            pytest.fail('A stop never creates an execution admission lock')
    stop_raw, stop_inode = admission.stop.read_bytes(), admission.stop.stat().st_ino
    again = training_cycles.stop_controller(state, 'demo', cycle_id, authorization['sha256'], reason='Observe the same original veto')
    assert again['stop_durable'] is True
    assert (admission.stop.read_bytes(), admission.stop.stat().st_ino) == (stop_raw, stop_inode)
    retried = training_cycles.authorize_controller(state, 'demo', cycle_id, source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert retried['status'] == 'stopped' and retried['authorization'] == authorization
    assert not admission.lock.exists() and not (directory / 'ready.json').exists()
    assert (authorization_path.read_bytes(), authorization_path.stat().st_ino) == (authorization_raw, authorization_inode)
    assert (directory / 'cycle.json').read_bytes() == cycle_raw
    admission.stop.write_bytes(b'{')
    corrupt = training_cycles.stop_controller(state, 'demo', cycle_id, authorization['sha256'], reason='Do not repair a damaged existing veto')
    assert corrupt['stop_visible'] is True and corrupt['identity_matches'] is False
    assert admission.stop.read_bytes() == b'{' and not admission.lock.exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Original SDK inspection uses supervised S/H processes')
@pytest.mark.parametrize('cycle_sdk_activity', [{'dispatch_parent': True}], indirect=True)
def test_actual_cold_controller_activity_uses_the_current_factory(cycle_sdk_activity, cycle_selection):
    """A submitted fixed parent must reach the real cold H read without a new start."""
    import asyncio
    import ergora.training.runtime.worker as worker

    state, admission, storage, _, _, environment = cycle_sdk_activity
    _, _, runtime, _, _, _ = cycle_selection
    parent = admission.submission()
    assert parent['status'] == 'submitted' and parent['attempt_saved'] and parent['result_saved']
    records = {path: (path.read_bytes(), path.stat().st_ino)
        for path in admission.directory.rglob('*') if path.is_file()}
    starts_before = [path for path in storage.glob('call-*.json') if json.loads(path.read_bytes())['action'] == 'start']
    assert len(starts_before) == 1
    info = environment('observe-candidate', activity_id='candidate-0-cold-inspection').info
    context = {'workflow_input': parent['intent']['workflow_input'], 'service_namespace': 'default',
        'activity_source': {name: getattr(info, name) for name in ('workflow_id', 'workflow_run_id', 'workflow_type',
            'workflow_namespace', 'namespace', 'activity_id', 'activity_type', 'task_queue', 'attempt')}}
    operation = worker._CycleOperation(state.root, 'demo', 'controller', admission.authorization['sha256'],
        'inspect-controller-activity', ordinal=0, activity_context=context)
    result = asyncio.run(operation.run())
    assert result['status'] == 'inspected', result
    assert result['runtime_status'] == 'queried'
    assert result['controller'] == {key: parent[key] for key in ('workflow_id', 'run_id', 'intent_sha256')}
    assert result['operation_stopped'] is True and result['supervisor_returncode'] == 0
    assert operation.response.frames[0]['process']['status'] == 'succeeded'
    assert operation.response.frames[0]['process']['returncode'] == 0
    starts_after = [path for path in storage.glob('call-*.json') if json.loads(path.read_bytes())['action'] == 'start']
    assert len(starts_after) == 1
    assert all((path.read_bytes(), path.stat().st_ino) == original for path, original in records.items())
    assert not (runtime / 'ergora/training-submissions/alpha.intent.json').exists()
    assert not (runtime / 'training/jobs/alpha').exists() and not (state.root / 'runs').exists()


@pytest.mark.parametrize('cutoff,prefix,unresolved', [
    ('stop', 0, None), ('budget', 1, None), ('stop', 1, 'lost-reply'), ('budget', 1, 'native-failed')])
def test_known_local_search_cutoff_is_partial_but_unresolved_effects_take_precedence(tmp_path, monkeypatch, cutoff, prefix, unresolved):
    """Exercise the projection/absence seam without creating a controller or work clock."""
    from types import SimpleNamespace
    import ergora.training.cycles as training_cycles
    import ergora.training.execution_protocol as protocol

    home, runtime = tmp_path / 'control', tmp_path / 'runtime'
    project = {'id': 'demo', 'repo': str(tmp_path / 'repo'), 'revision': 1}
    authorization = {'schema_version': 5, 'control_home': str(home), 'project': 'demo', 'cycle_id': 'read-only-status',
        'project_revision': 1, 'input_sha256': 'a' * 64, 'sha256': 'b' * 64,
        'clock': {}, 'execution': {'state_directory': str(runtime), 'config_directory': str(tmp_path / 'config')}}
    plan = {'project': project, 'definition': {'budget': {'wall_seconds': 100, 'cleanup_seconds': 10},
        'execution_scope': protocol.D_SCOPE}, 'admissions': [{'experiment_id': 'finished'}, {'experiment_id': 'remaining'}]}
    stopped = {'stop_visible': cutoff == 'stop', 'identity_matches': True if cutoff == 'stop' else None,
        'stop_durable': True if cutoff == 'stop' else None, 'admission_drained': True if cutoff == 'stop' else None,
        'executor_stop_confirmed': None, 'reason': None}
    delivery = {'status': 'submitted' if prefix else 'not_prepared', 'intent': None, 'attempt_saved': bool(prefix),
        'result_saved': bool(prefix), 'workflow_id': 'parent', 'run_id': 'original-run' if prefix else None}

    class OriginalAdmission:
        _sha = staticmethod(protocol.CycleAdmission._sha)

        def __init__(self, *args):
            pass

        def observe(self, **options):
            return stopped

        def submission(self):
            return delivery

    # The prefix validator is a separate tested owner. This test supplies only
    # its already-verified result and exercises the actual remaining-opportunity reader.
    progress = {'status': 'in_progress' if prefix else 'not_started', 'selection_count': 2,
        'sequence_trials': prefix, 'executed_trials': prefix, 'skipped_trials': 0, 'promising_count': 0,
        'verified_gain_count': 0, 'full_accepted_count': 0, 'prefix': None, 'reason': None,
        'coverage': {'runtime_status': 'not_queried', 'execution_authorized': False}}
    monkeypatch.setattr(protocol, 'CycleAdmission', OriginalAdmission)
    monkeypatch.setattr(protocol, 'read_trial_progress', lambda *args: deepcopy(progress))
    monkeypatch.setattr(training_cycles.budget_clock, 'remaining', lambda *args: 9 if cutoff == 'budget' else 90)
    if unresolved == 'lost-reply':
        path = runtime / 'ergora/training-submissions/remaining.attempt.json'
        path.parent.mkdir(parents=True)
        path.write_text('{}')
    elif unresolved == 'native-failed':
        path = runtime / 'training/jobs/remaining/result.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'state': 'FAILED'}))
    lock = home / 'training-cycles/demo/read-only-status/controller/admission.lock'
    lock.parent.mkdir(parents=True)
    lock.write_bytes(b'')
    state = SimpleNamespace(root=home, project=lambda selected: project)
    observed = training_cycles._status(state, plan, authorization, {'saved': 'original-ready'})
    search = observed['search']
    assert search['sequence_trials'] == prefix
    assert search['status'] == ('needs_reconciliation' if unresolved else 'partial')
    assert search['termination'] == cutoff
    assert search['coverage']['remote_controller_status'] == 'not_queried'
    assert search['coverage']['controller_cancellation_confirmed'] is None
    assert search['coverage']['execution_authorized'] is False
    if unresolved:
        assert search['local_effects']['state'] == 'unresolved'
    else:
        assert search['local_effects']['state'] == 'quiescent'


@pytest.mark.parametrize('prefix,unresolved', [(0, False), (1, False), (1, True), (0, 'malformed-stop-facts')])
def test_workflow_stop_consumes_known_local_partial_without_inventing_remote_stop(cycle_workflow, prefix, unresolved):
    """Consume a controlled original-H read summary; no controller birth or work runs."""
    import ergora.training.execution_protocol as protocol

    h = cycle_workflow()
    cold = h.activity(h.start())
    h.result(cold, h.trial_envelope(count=2), at=1)
    stopping = h.activity(h.signal({'workflow_input': h.original, 'reason': 'bounded local cutoff'}, at=2))
    value = h.envelope('stop')
    source = '9' * 32
    root = Path(h.original['control_home']) / 'training-cycles/demo/first/controller/trials/0/trials.json'
    pin = None if not prefix else {'path': str(root), 'sha256': 'a' * 64, 'bytes': 100,
        'trials': 1, 'last_trial_sha256': 'b' * 64}
    value['operations'].append({'operation_id': source, 'mode': 'drain', 'ordinal': None,
        'operation_stopped': True, 'supervisor_returncode': 0, 'result': {'inline': {'status': 'observed'}}})
    value['search'] = {'status': 'partial', 'selection_count': 2, 'sequence_trials': prefix,
        'executed_trials': prefix, 'skipped_trials': 0, 'promising_count': 0, 'verified_gain_count': 0,
        'full_accepted_count': 0, 'prefix': pin, 'reason': 'Known local cutoff', 'termination': 'budget' if prefix else 'stop',
        'local_effects': {'state': 'unresolved' if unresolved is True else 'quiescent', 'checked_from_ordinal': prefix,
            'unresolved': [{'ordinal': 1, 'kind': 'consumed_submission_opportunity'}] if unresolved is True else [],
            'controller_delivery': 'submitted', 'admission_state': 'established'},
        'local_stop': {'stop_visible': True, 'identity_matches': True, 'stop_durable': True, 'admission_drained': True},
        'coverage': {'runtime_status': 'not_queried', 'execution_authorized': False, 'full_quality_approved': False,
            'promotion_approved': False, 'remote_controller_status': 'not_queried',
            'controller_cancellation_confirmed': None, 'executor_stop_confirmed': True if prefix else None},
        'source_operation_id': source, 'authorization_sha256': h.original['authorization_sha256'],
        'input_sha256': h.original['input_sha256']}
    if unresolved == 'malformed-stop-facts':
        value['facts'] = {'not_a_stop_fact': True}
    h.result(stopping, value, at=3)
    observed = h.query()
    assert observed['outcome'] == ('needs_reconciliation' if unresolved else 'partial')
    if not unresolved:
        assert observed['search']['status'] == 'partial'
        assert observed['search']['coverage']['controller_cancellation_confirmed'] is None
        assert observed['sequence_trials'] == prefix
        assert observed['phase'] == 'PARTIAL'
        assert observed['stop_durable'] is observed['admission_drained'] is True
    else:
        assert observed.get('search') is None
        assert observed['stop_activity_status'] == 'observation_rejected'


@pytest.mark.parametrize('change', ['model', 'affinity', 'window'])
def test_unqualified_cpu_observations_reject_reuse_and_isolation_ports_remain_separate(f1_cpu_snapshot, tmp_path, monkeypatch, change):
    """Strict reuse is unavailable; nonqualifying ports test dataflow only, never support."""
    from types import SimpleNamespace
    import ergora.training.materials as materials
    import ergora.training.runtime.evidence as evidence
    import ergora.training.runtime.context as context
    import ergora.training.execution_protocol as protocol

    original_raw, snapshot = f1_cpu_snapshot
    current_raw = deepcopy(original_raw)
    if change == 'model':
        current_raw['models'][0]['model name'] = 'Independent current physical CPU'
    elif change == 'affinity':
        current_raw['affinity'] = [0]
        current_raw['cpus'] = current_raw['cpus'][:1]
    current_snapshot = snapshot(current_raw)
    baseline, screen = {}, {}
    source = {'repo': '/original/source', 'commit': 'a' * 40, 'inventory_sha256': 'b' * 64, 'entrypoint': 'driver.py'}
    environment = {'device': 'CPU', 'python': 'Original CPython 3.12 data', 'implementation': 'CPython',
        'platform': 'Linux-original-x86_64-with-glibc2.39',
        'ranks': [0], 'layout': 'single-process', 'dependencies': 'Python standard library'}
    for phase, target in (('baseline', baseline), ('screen', screen)):
        request = {'binding': {'experiment_id': 'original-' + phase}, 'native_request_sha256': 'c' * 64,
            'managed': {'launch_sha256': phase + '-original-launch'}, 'execution_phase_id': phase + '-phase',
            'configuration_readback': {'source': source}}
        provenance = {'run_id': phase + '-unprofiled-run', 'window_id': phase + '-unprofiled-window', 'execution_phase_id': request['execution_phase_id']}
        selected = [{key: provenance[key] for key in ('run_id', 'window_id')}]
        proof = materials.cpu_window_identity(request, phase, 'unprofiled', selected,
            snapshot(deepcopy(original_raw)), snapshot(deepcopy(original_raw)))
        owner = {key: request[key] for key in ('binding', 'native_request_sha256', 'managed')}
        owner['source'] = source
        profile_selection = {'phase': phase, 'run_id': phase + '-profile-run', 'window_id': phase + '-profile-window'}
        profile = materials.cpu_window_identity(request, phase, 'profiled',
            [{key: profile_selection[key] for key in ('run_id', 'window_id')}],
            snapshot(deepcopy(original_raw)), snapshot(deepcopy(original_raw)))
        target['diagnostics'] = {'status': 'complete', 'raw': [{'capture': {
            'binding': request['binding'], 'managed': request['managed'], 'source': source, 'selection': profile_selection,
            'actual': {'hardware': {'cpu_execution': profile}}}}]}
        if phase == 'baseline':
            owner.update(baseline={'cpu_execution': proof, 'workload': {'layout': {'kind': 'cpu-single-process'}}},
                environment={'observed': environment, 'report_ref': {'path': 'original-environment.json'}},
                measurement=[{'provenance': provenance, 'measurement_mode': 'unprofiled', 'elapsed_seconds': 1.0, 'source_samples': 48}])
            target.update(reference={'receipt': owner}, reference_sha256='d' * 64)
        else:
            owner.update(workload={'scope': {'device': 'CPU', 'environment': environment, 'cpu_execution': proof}},
                windows=[{'provenance': provenance}], reference={'reference_sha256': 'd' * 64})
            target['result'] = owner
    runtime, output = tmp_path / 'runtime', tmp_path / 'old-job/run-output'
    output.mkdir(parents=True)
    screen['output'] = str(output)
    descriptor = {'kind': 'prepared-json', 'format': 'json-v1'}
    observations = {}
    for arm in ('baseline', 'candidate'):
        raw = json.dumps({'original': arm}).encode()
        relative = 'training/configurations/current/' + arm + '.json'
        path = runtime / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        descriptor[arm] = {'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        observations[arm] = {'source_sha256': descriptor[arm]['sha256'], 'workload': {'layout': {'kind': 'cpu-single-process'}}}
    old_plan = {'verification_experiment_id': 'old-full', 'window': {'minimum_work': 48}, 'input_plan': {'scheme': 'original-input'}}
    new_plan = {**deepcopy(old_plan), 'verification_experiment_id': 'current-full'}
    if change == 'window':
        new_plan['window']['minimum_work'] = 64
    (output / 'configuration-receipt.json').write_text(json.dumps({'observations': observations}))
    (output.parent / 'configuration-request.json').write_text(json.dumps({'execution': {'operation': 'training-screen-v1', 'plan': old_plan}}))
    (output / 'baseline-reference-read.json').write_text(json.dumps({'projection': {'allowed_deltas': [], 'relations': [
        {'field': 'initialization', 'relation': 'matched'}]}}))
    runner = {'configuration_readback': {'source': source}, 'command': ['/original/python'], 'timeout_seconds': 20}
    current_manifest = {'experiment_id': 'current', 'execution': {'operation': 'training-screen-v1', 'plan': new_plan},
        'baseline_reference': {'reference_sha256': 'd' * 64}}
    admitted = {'manifest': current_manifest, 'current_runner': runner}
    plan = {'control_home': str(tmp_path / 'control'), 'project': {'registration': {'definition': {'execution': {'state_directory': str(runtime)}}}},
        'admissions': [{'observation': {'experiment': admitted}}]}
    reads = []
    monkeypatch.setattr(context, '_TrainingProject', lambda value: SimpleNamespace())
    monkeypatch.setattr(evidence, '_baseline_reference', lambda *args: baseline)
    monkeypatch.setattr(materials, 'require_driver', lambda *args: descriptor)
    def current_read(*args, **kwargs):
        reads.append('current')
        return deepcopy(current_snapshot['identity'])
    monkeypatch.setattr(materials, 'cpu_execution_identity', lambda: pytest.fail('Saved context reader must not observe its own subject'))
    original_reuse_reader = evidence.cpu_reuse_identity
    with pytest.raises(ValueError, match='unsupported'):
        execution_evidence._failure_actual_identities(screen, plan, 0)
    assert reads == []
    # These explicit data-only ports exercise the two independent dictionaries
    # if a future independently qualified provider is implemented. They do not
    # assert that current v1 observations qualify for matching, or create one.
    monkeypatch.setattr(evidence, 'cpu_reuse_identity', lambda *args: materials._read_cpu_execution_identity(snapshot(original_raw)))
    baseline['cpu_contract'] = {'contract_sha256': 'e' * 64}
    monkeypatch.setattr(execution_evidence, 'read_cpu_preparation_admission', lambda *args: {
        'contract': {'sha256': 'e' * 64}, 'contract_sha256': 'e' * 64})
    monkeypatch.setattr(protocol, 'read_cycle_cpu_context', current_read)
    current_context = {'path': str(tmp_path / 'data-only-context.json'), 'sha256': 'f' * 64, 'bytes': 1}
    operation = {'control_home': plan['control_home'], 'project': 'demo', 'cycle_id': 'data-only-ports', 'ordinal': 0}
    saved = Path(operation['control_home']) / 'training-cycles/demo/data-only-ports/cycle.json'
    saved.parent.mkdir(parents=True)
    saved.write_text(json.dumps(plan))
    monkeypatch.setattr(protocol, 'read_trial_reference', lambda ref: {'operation': operation, 'environment': environment})
    current, historical = execution_evidence._failure_actual_identities(screen, plan, 0, current_context=current_context)
    assert reads == ['current'] and current is not historical
    assert historical['cpu_execution'] == snapshot(original_raw)['identity']
    assert current['cpu_execution'] == current_snapshot['identity']
    old_manifest = {**current_manifest, 'execution': {'operation': 'training-screen-v1', 'plan': old_plan}}
    assert protocol.trial_failure_fingerprint(current_manifest, runner, {}, actual_identity=current) != protocol.trial_failure_fingerprint(
        old_manifest, runner, {}, actual_identity=historical)
    # Missing original typed/window proof is rejected before the independent reader;
    # the controlled old fixture object is not supplemented or rewritten.
    monkeypatch.setattr(evidence, 'cpu_reuse_identity', original_reuse_reader)
    del baseline['cpu_contract']
    del baseline['reference']['receipt']['baseline']['cpu_execution']
    reads.clear()
    with pytest.raises(ValueError, match='unsupported'):
        execution_evidence._failure_actual_identities(screen, plan, 0)
    assert reads == []


def test_no_history_cpu_prepare_path_does_not_invoke_matching_qualification(tmp_path, monkeypatch):
    """Reach the original prepare port, but create no State, submission or work."""
    from types import SimpleNamespace
    import ergora.training.runtime.worker as worker
    import ergora.training.cycles as training_cycles
    import ergora.training.materials as materials
    import ergora.training.runtime.evidence as evidence
    import ergora.training.execution_protocol as protocol

    class OrdinaryPrepareReached(Exception):
        pass

    def forbidden(*args, **kwargs):
        raise AssertionError('No-history CPU preparation must not qualify historical matching')

    def prepare(*args, **kwargs):
        raise OrdinaryPrepareReached()

    monkeypatch.setattr(materials, 'validate_cpu_execution_identity', forbidden)
    monkeypatch.setattr(evidence, 'cpu_reuse_identity', forbidden)
    monkeypatch.setattr(worker, '_select_cycle_project', lambda *args: None)
    monkeypatch.setattr(protocol, 'cycle_start_source', lambda *args: None)
    monkeypatch.setattr(protocol, 'cycle_cpu_context', lambda *args, **kwargs: None)
    monkeypatch.setattr(worker, '_cycle_submission', lambda *args: (SimpleNamespace(), None))
    monkeypatch.setattr(worker, '_round_previous', lambda *args: None)
    monkeypatch.setattr(training_cycles, '_live_materials', lambda *args: None)
    monkeypatch.setattr(worker, 'State', lambda root: SimpleNamespace(root=root))
    monkeypatch.setattr(training, '_prepare_submission', prepare)
    controller = {'ordinal': 0}
    payload = {'identity': {'mode': 'prepare-candidate', 'ordinal': 0, 'control_home': str(tmp_path),
        'project': 'demo', 'cycle_id': 'only-projection', 'authorization_sha256': 'a' * 64},
        'start_context': {'controller': controller}}
    plan = {'project': {}, 'definition': {'execution_scope': protocol.D_SCOPE, 'historical_failures': [],
        'candidates': [{'experiment_id': 'unexecuted', 'manifest_sha256': 'b' * 64}], 'budget': {'control_timeout_seconds': 30}}}
    admission = SimpleNamespace(authorization={'schema_version': 5, 'project_revision': 1}, directory=tmp_path)
    with pytest.raises(OrdinaryPrepareReached):
        worker._candidate_operation(payload, plan, admission, lambda: None)
    assert not list(tmp_path.iterdir())


def test_plain_full_contract_does_not_require_cpu_matching_qualification(monkeypatch):
    import ergora.training.materials as materials

    def forbidden(*args, **kwargs):
        raise AssertionError('Ordinary full data must not acquire a CPU matching prerequisite')

    monkeypatch.setattr(materials, 'validate_cpu_execution_identity', forbidden)
    assert materials.execution_plan({'execution': {'operation': 'full-verify'}}, {}) == {'operation': 'full-verify'}


def test_cpu_role_projection_ports_keep_prepared_full_without_execution(monkeypatch):
    """Pure role wiring; material qualification is a separate strict D reader."""
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials

    monkeypatch.setattr(materials, 'cpu_contract', lambda manifest: manifest['execution'].get('cpu_contract'))
    def material_role(material, *, role, ordinal, manifest, manifest_sha256, runner):
        return {'role': role, 'ordinal': ordinal, 'experiment_id': manifest['experiment_id'],
            'manifest_sha256': manifest_sha256, 'contract_sha256': manifest['execution']['cpu_contract']['sha256']}
    monkeypatch.setattr(protocol, '_cpu_material_role', material_role)
    def selected(stage):
        return {'experiment_id': stage, 'manifest_sha256': stage + '-raw', 'observation': {'experiment': {
            'manifest': {'experiment_id': stage, 'execution': {'operation': stage, 'cpu_contract': {'sha256': 'c' * 64}}},
            'current_runner': {}, 'cpu_contract_preparation': {'controlled': 'material port'}}}}
    screen, full = selected('screen'), selected('full')
    plan = {'definition': {'execution_scope': protocol.D_SCOPE}, 'admissions': [screen],
        'stage_admissions': [{'screen': screen, 'full': full}]}
    roles = protocol.cpu_contract_roles(plan)
    assert next(item for item in roles if item['role'] == 'full')['operations'] == []
    assert next(item for item in roles if item['role'] == 'screen')['operations'] == ['screen', 'profile', 'skip']
    authority = {'cpu_contracts': {'actor_id': 'unix:ports:provenance', 'roles': roles}}
    protocol.validate_cpu_contract_authority(plan, authority, 'screen')
    with pytest.raises(ValueError, match='outside the original selected'):
        protocol.validate_cpu_contract_authority(plan, authority, 'full')
    with pytest.raises(ValueError, match='role collection'):
        protocol.validate_cpu_contract_authority(plan, {'cpu_contracts': {'roles': roles[:1]}}, 'screen')
    plan['stage_admissions'][0]['unexpected-role'] = screen
    with pytest.raises(ValueError, match='stage role collection'):
        protocol.cpu_contract_roles(plan)


def test_cpu_role_material_preserves_original_preview_intent_and_confirmation(tmp_path):
    """Pure C/A serialization only; these data do not prove source or CPU behavior."""
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials

    source = {'repo': str(tmp_path / 'source'), 'commit': 'a' * 40, 'inventory_sha256': 'b' * 64, 'entrypoint': 'driver.py'}
    runner = {'schema_version': 2, 'runner_template_id': 'selected', 'project': 'demo', 'repo': source['repo'],
        'command': ['/original/python'], 'timeout_seconds': 20, 'configuration_readback': {
            'protocol': 'training-configuration-driver-v1', 'source': source, 'observation_scheme': 'data-only-domain'}}
    value = {'schema_version': 1, 'kind': 'training-cpu-execution-contract', 'operation': 'cpu-diagnostic-v1',
        'implementation': {'source': {**source, 'entrypoint_sha256': 'c' * 64},
            'driver_protocol': 'training-configuration-driver-v1', 'observation_scheme': 'data-only-domain',
            'runner_sha256': materials.observation_sha256(runner), 'wrapper_entry': 'ergora.training.configuration:main',
            'core_sources_sha256': 'd' * 64}, 'conformance': deepcopy(materials.CPU_CONFORMANCE),
        'input_domain': {'type': 'object', 'properties': {'batch': {'type': 'integer', 'minimum': 1, 'maximum': 8}},
            'required': ['batch'], 'additionalProperties': False}}
    contract = {**value, 'sha256': materials.observation_sha256(value)}
    manifest = {'experiment_id': 'selected', 'local_project': 'demo',
        'execution': {'operation': 'full-verify', 'cpu_contract': contract}}
    manifest_raw = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    body = {'schema_version': 2, 'operation': 'prepare-training', 'control_home': str(tmp_path), 'project': 'demo',
        'repo': source['repo'], 'execution': {}, 'registration_sha256': 'e' * 64, 'experiment_id': 'selected',
        'project_revision': 1, 'request': {'experiment': manifest}, 'sources': {'runner': {'document': runner}},
        'files': {'training/manifests/selected.json': manifest_raw.decode('utf-8')}}
    preview_sha = materials.observation_sha256(body)
    intent = {**body, 'confirmed_preview_sha256': preview_sha, 'confirmation': {
        'kind': 'training-preparation-confirmation', 'actor_id': 'unix:1000:provenance', 'project_revision': 1,
        'request_sha256': materials.observation_sha256(body['request'])}}
    admission = materials.make_cpu_preparation_admission(intent)
    def original(value, suffix):
        raw = (json.dumps(value, indent=2) + '\n').encode('utf-8')
        return raw.decode('utf-8'), {'path': str(tmp_path / ('selected.' + suffix + '.json')),
            'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    intent_utf8, intent_ref = original(intent, 'intent')
    admission_utf8, admission_ref = original(admission, 'cpu-contract-admission')
    material = {'contract': contract, 'contract_sha256': contract['sha256'], 'preview_sha256': preview_sha,
        'intent_sha256': materials.observation_sha256(intent), 'intent_ref': intent_ref, 'admission_ref': admission_ref,
        'intent_utf8': intent_utf8, 'admission_utf8': admission_utf8}
    args = {'role': 'selected', 'ordinal': 0, 'manifest': manifest,
        'manifest_sha256': hashlib.sha256(manifest_raw).hexdigest(), 'runner': runner}
    role = protocol._cpu_material_role(material, **args)
    assert role['confirmed_preview_sha256'] == preview_sha
    assert role['intent_sha256'] != preview_sha
    with pytest.raises(ValueError, match='confirmed preview or saved intent identity'):
        protocol._cpu_material_role({**material, 'preview_sha256': 'f' * 64}, **args)
    changed = deepcopy(admission)
    changed['confirmation']['actor_id'] = 'unix:1001:another-provenance'
    bad_utf8, bad_ref = original(changed, 'cpu-contract-admission')
    with pytest.raises(ValueError, match='original confirmation-bearing intent'):
        protocol._cpu_material_role({**material, 'admission_utf8': bad_utf8, 'admission_ref': bad_ref}, **args)
    with pytest.raises(ValueError, match='complete original preparation admission'):
        protocol._cpu_material_role(None, **args)


def test_cpu_context_reader_ports_bind_saved_owned_edges_without_live_collection(tmp_path, monkeypatch):
    """Real bounded raw readers with nonqualifying observation ports, no OS probe."""
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials

    contract = {'sha256': 'c' * 64}
    monkeypatch.setattr(protocol, '_cycle_cpu_contract', lambda payload: contract)
    monkeypatch.setattr(materials, 'cpu_execution_identity', lambda: pytest.fail('Offline context must not collect current facts'))
    def validate(frame, *, contract, role, binding, expected_subject, require_complete):
        assert frame['role'] == role and frame['binding'] == binding
        assert all(frame['subject'][key] == value for key, value in expected_subject.items())
        return {'controlled': 'stable data only'}
    monkeypatch.setattr(materials, 'validate_cpu_context_observation', validate)
    identities = {role: {'pid': pid, 'start_ticks': str(pid * 10), 'boot_id': 'b' * 36}
                  for role, pid in (('parent', 310), ('supervisor', 311), ('helper', 312))}
    identity = {'operation_id': 'a' * 32, 'control_home': str(tmp_path), 'project': 'demo',
        'cycle_id': 'data-only', 'ordinal': 0, 'parent': identities['parent']}
    root = tmp_path / 'operations/training-cycles' / identity['operation_id']
    root.mkdir(parents=True)
    def save(path, value):
        raw = json.dumps(value, sort_keys=True).encode('utf-8')
        path.write_bytes(raw)
        return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    request = save(root / 'request.json', {'identity': identity})
    frames, raw_frames = {}, {}
    for role in ('parent', 'supervisor', 'helper'):
        raw_frames[role] = {'role': role, 'binding': {'operation': identity},
            'subject': {**identities[role], 'tid': identities[role]['pid'],
                'parent_pid': 309 if role == 'parent' else 310 if role == 'supervisor' else 311}}
        frames[role] = save(root / ('cpu-' + role + '.json'), raw_frames[role])
    supervisor = save(root / 'supervisor.json', {'schema_version': 1, 'kind': 'training-cycle-supervisor',
        'identity': identity, 'request_sha256': request['sha256'], 'supervisor': identities['supervisor'],
        'cpu_contexts': {role: frames[role] for role in ('parent', 'supervisor')}})
    context = {'schema_version': 1, 'kind': 'training-cycle-cpu-context', 'operation': identity,
        'contract_sha256': contract['sha256'], 'request_ref': request, 'supervisor_ref': supervisor, 'environment': {},
        'subjects': identities, 'frames': frames}
    reference = save(root / 'cpu-context.json', context)
    assert protocol.read_cycle_cpu_context(reference) == {'controlled': 'stable data only'}
    archived = {str(path): path.read_bytes() for path in root.iterdir()}
    def archive_reader(ref):
        raw = archived[ref['path']]
        assert len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256']
        return materials.decode_record(raw)
    with monkeypatch.context() as offline:
        offline.setattr(protocol, 'read_raw', lambda *args: pytest.fail('Archive reader cannot follow original host paths'))
        assert protocol.read_cycle_cpu_context(reference, contract=contract, reader=archive_reader) == {'controlled': 'stable data only'}
    raw_frames['helper']['subject']['parent_pid'] = 999
    context['frames']['helper'] = save(root / 'cpu-helper.json', raw_frames['helper'])
    reference = save(root / 'cpu-context.json', context)
    with pytest.raises(ValueError, match='actual original P/S/H parent edge'):
        protocol.read_cycle_cpu_context(reference)


@pytest.fixture
def source_phase_files(tmp_path, monkeypatch):
    """Ordinary source/descriptor data only; no native interpreter is executed."""
    from types import SimpleNamespace
    import ergora.native.resources as native_resources
    import ergora.training.native as training_native
    import ergora
    import ergora.training.execution_protocol as protocol

    source, data, installation = (tmp_path / name for name in ('sources', 'data', 'installation'))
    source.mkdir()
    for name in ('shared.py', 'measurement.py', 'gate.py'):
        (source / name).write_bytes(('original ' + name).encode())
    bundle = data / 'reference/platform/local/component.py'
    bundle.parent.mkdir(parents=True)
    bundle.write_bytes(b'original native source data')
    installed = installation / 'local/component.py'
    installed.parent.mkdir(parents=True)
    installed.write_bytes(bundle.read_bytes())
    manifest = {'version': 'data-only', 'source_zip_sha256': 'a' * 64, 'source_html_sha256': 'b' * 64,
        'files': {'platform/local/component.py': hashlib.sha256(bundle.read_bytes()).hexdigest()}}
    manifest_raw = (json.dumps(manifest) + '\n').encode()
    (data / 'reference-manifest.json').write_bytes(manifest_raw)
    descriptor_raw = (json.dumps({'protocol_id': native_resources.TRAINING_PROTOCOL,
        'reference_manifest_sha256': hashlib.sha256(manifest_raw).hexdigest()}) + '\n').encode()
    declaration = data / 'native-runtime' / (native_resources.TRAINING_PROTOCOL + '.json')
    declaration.parent.mkdir()
    declaration.write_bytes(descriptor_raw)
    descriptor = installation / 'ergora-native-runtime.json'
    descriptor.write_bytes(descriptor_raw)
    interpreter = installation / '.venv/bin/python'
    interpreter.parent.mkdir(parents=True)
    interpreter.write_bytes(b'ordinary file; never executed')
    monkeypatch.setattr(protocol, 'PACKAGE_ROOT', source)
    monkeypatch.setattr(protocol, 'GATE_SOURCES', ('shared.py', 'gate.py'))
    monkeypatch.setattr(protocol, 'MEASUREMENT_SOURCES', ('shared.py', 'measurement.py'))
    monkeypatch.setattr(native_resources, 'DATA', data)
    monkeypatch.setattr(native_resources, 'ROOT', data / 'reference')
    digest = lambda name: hashlib.sha256((source / name).read_bytes()).hexdigest()
    ready = {'data': 'original ready'}
    capability = {'protocol': protocol.PROTOCOL, 'admission_protocol': native_resources.TRAINING_PROTOCOL,
        'installation': str(installation), 'native_python': str(interpreter),
        'descriptor_sha256': hashlib.sha256(descriptor_raw).hexdigest(),
        'cycle_ready_sha256': protocol.CycleAdmission._sha(ready),
        'gate_sources': {name: digest(name) for name in protocol.GATE_SOURCES}}
    authorization = {'measurement_sources': {name: digest(name) for name in protocol.MEASUREMENT_SOURCES},
        'execution': {'installation': str(installation)}, 'control_home': str(tmp_path / 'control'), 'sha256': 'c' * 64}
    return SimpleNamespace(protocol=protocol, native_resources=native_resources, source=source, installation=installation,
        bundle=bundle, installed=installed, descriptor=descriptor, interpreter=interpreter, digest=digest,
        ready=ready, capability=capability, authorization=authorization, owner={'execution_capability': capability})


def test_source_phase_original_interfaces_validate_distinct_roots_and_unique_sources(source_phase_files):
    f = source_phase_files
    f.protocol._round_sources(f.authorization, f.ready, f.owner)
    f.protocol.validate_sources(f.capability)
    f.protocol._round_sources(f.authorization, f.ready, None)


@pytest.mark.parametrize('fault', ['conflict', 'gate-only', 'measurement-only'])
def test_source_phase_refuses_conflicting_or_unique_source_drift(source_phase_files, fault):
    f = source_phase_files
    if fault == 'conflict':
        f.capability['gate_sources']['shared.py'] = 'f' * 64
    else:
        (f.source / ('gate.py' if fault == 'gate-only' else 'measurement.py')).write_bytes(b'changed after original binding')
    with pytest.raises(ValueError):
        f.protocol._round_sources(f.authorization, f.ready, f.owner)


def test_source_phase_shared_gate_keeps_stricter_limit_and_measurement_only_retains_its_limit(source_phase_files):
    f = source_phase_files
    large = b'x' * (f.protocol.LIMIT + 1)
    (f.source / 'measurement.py').write_bytes(large)
    f.authorization['measurement_sources']['measurement.py'] = f.digest('measurement.py')
    f.protocol._round_sources(f.authorization, f.ready, f.owner)
    (f.source / 'shared.py').write_bytes(large)
    f.authorization['measurement_sources']['shared.py'] = f.digest('shared.py')
    f.capability['gate_sources']['shared.py'] = f.digest('shared.py')
    with pytest.raises(ValueError):
        f.protocol._round_sources(f.authorization, f.ready, f.owner)
    with pytest.raises(ValueError):
        f.protocol.validate_sources(f.capability)
    f.protocol._round_sources(f.authorization, f.ready, None)


@pytest.mark.parametrize('fault', ['missing', 'symlink', 'fifo'])
@pytest.mark.skipif(sys.platform != 'linux', reason='Original no-follow/FIFO native source boundary requires Linux')
def test_source_phase_preserves_nonblocking_ordinary_file_checks(source_phase_files, fault):
    f = source_phase_files
    path = f.source / 'measurement.py'
    path.unlink()
    if fault == 'symlink':
        path.symlink_to(f.source / 'shared.py')
    elif fault == 'fifo':
        os.mkfifo(path)
    with pytest.raises((OSError, ValueError)):
        f.protocol._round_sources(f.authorization, f.ready, f.owner)


@pytest.mark.parametrize('fault', ['source', 'installed', 'descriptor', 'bundle', 'interpreter'])
def test_source_phase_refuses_persistent_drift_during_static_payload(source_phase_files, monkeypatch, fault):
    f = source_phase_files
    verify = f.native_resources.verify
    def during_payload():
        target = {'source': f.source / 'shared.py', 'installed': f.installed,
            'descriptor': f.descriptor, 'bundle': f.bundle, 'interpreter': f.interpreter}[fault]
        target.unlink() if fault == 'interpreter' else target.write_bytes(b'persistent payload drift')
        return verify()
    monkeypatch.setattr(f.native_resources, 'verify', during_payload)
    with pytest.raises((OSError, ValueError)):
        f.protocol._round_sources(f.authorization, f.ready, f.owner)


@pytest.mark.parametrize('entry', ['round', 'standalone'])
def test_source_phase_retains_final_interpreter_presence_after_last_source_read(source_phase_files, monkeypatch, entry):
    f, payload_seen = source_phase_files, []
    verify, read = f.native_resources.verify, f.protocol.read_raw
    def payload():
        result = verify()
        payload_seen.append(True)
        return result
    def last_source_read(path, *args):
        raw = read(path, *args)
        if payload_seen and path.parent == f.source and f.interpreter.exists():
            f.interpreter.unlink()
        return raw
    monkeypatch.setattr(f.native_resources, 'verify', payload)
    monkeypatch.setattr(f.protocol, 'read_raw', last_source_read)
    with pytest.raises(ValueError, match='native interpreter is unavailable'):
        if entry == 'round':
            f.protocol._round_sources(f.authorization, f.ready, f.owner)
        else:
            f.protocol.validate_sources(f.capability)


@pytest.mark.parametrize('fault', ['source', 'stop', 'boot', 'owner', 'deadline'])
def test_source_phase_preserves_separate_outer_and_live_guard_boundaries(source_phase_files, tmp_path, monkeypatch, fault):
    """Original candidate caller with controlled authority ports; no birth/clock."""
    from types import SimpleNamespace
    f, changed = source_phase_files, []
    protocol = f.protocol
    plan = {'project': {'registration': {'files': {}}}, 'definition': {'execution_scope': protocol.FULL_SCOPE}}
    raw_plan = json.dumps(plan).encode()
    directory = tmp_path / 'cycle-data'
    directory.mkdir()
    (directory / 'cycle.json').write_bytes(raw_plan)
    (directory / 'ready.json').write_text(json.dumps(f.ready))
    intent = {'experiment_id': 'selected', 'budget': {'controller': {'ordinal': 0}}}
    owner = {**f.owner, 'intent_sha256': protocol.CycleAdmission._sha(intent),
        'authorization_sha256': f.authorization['sha256']}
    budget_path = tmp_path / 'original-budget'
    intent_path = budget_path.parent / 'selected.intent.json'
    def document(path, **kwargs):
        return owner if path == budget_path / 'owner.json' else intent if path == intent_path else None
    current = SimpleNamespace(budget=budget_path, ident='selected', document=document)
    admission = SimpleNamespace(authorization=f.authorization, _sha=protocol.CycleAdmission._sha,
        directory=directory, bind=lambda *args: None)
    def active():
        if changed and fault != 'source':
            raise ValueError('Original live ' + fault + ' changed during source reads')
    monkeypatch.setattr(protocol, '_round_authority', lambda *args: (raw_plan, active))
    monkeypatch.setattr(protocol, 'validate_budget_binding', lambda *args: None)
    monkeypatch.setattr(protocol, '_round_candidate_intent', lambda *args: None)
    monkeypatch.setattr(protocol, 'ExecutionRecords', lambda *args: current)
    monkeypatch.setattr(protocol, 'owner_record', lambda *args: None)
    if fault != 'source':
        verify = f.native_resources.verify
        def slow_source_payload():
            value = verify()
            if not changed:
                changed.append('during original static source payload')
            return value
        monkeypatch.setattr(f.native_resources, 'verify', slow_source_payload)
    def predecessor(*args):
        if fault == 'source':
            changed.append('between original source guards')
            (f.source / 'gate.py').write_bytes(b'drift after first complete source guard')
        return []
    monkeypatch.setattr(protocol, '_round_predecessors', predecessor)
    with pytest.raises(ValueError):
        execution_evidence.authenticate_cycle_candidate(intent, plan, admission, f.ready)
    assert changed == ['between original source guards' if fault == 'source' else 'during original static source payload']


def test_source_phase_standalone_context_rechecks_after_original_experiment_read(source_phase_files, tmp_path, monkeypatch):
    """Original context caller/data ports only; no State, effect or real clock."""
    from types import SimpleNamespace
    f = source_phase_files
    protocol = f.protocol
    protocol._round_sources(f.authorization, f.ready, f.owner)
    state_root = tmp_path / 'original-state'
    path = state_root / 'training/original.txt'
    path.parent.mkdir(parents=True)
    path.write_bytes(b'original experiment source')
    observed = {'baseline_files': {}, 'experiment': {
        'manifest': {'experiment_id': 'selected', 'execution': {'operation': 'full-verify'}}, 'current_runner': {},
        'files': {'state/training/original.txt': hashlib.sha256(path.read_bytes()).hexdigest()}}}
    project = {'id': 'demo', 'registration': {'files': {}}}
    policy = {'wall_seconds': 100, 'cleanup_seconds': 1}
    plan = {'project': project, 'definition': {'execution_scope': protocol.FULL_SCOPE, 'budget': policy},
        'admissions': [{'experiment_id': 'selected', 'observation': observed,
            'manifest_sha256': hashlib.sha256(json.dumps(observed['experiment']['manifest']).encode()).hexdigest()}]}
    raw_plan = json.dumps(plan).encode()
    value = {**{key: value for key, value in f.authorization.items() if key != 'sha256'},
        'schema_version': 1, 'project': 'demo', 'cycle_id': 'saved-data',
        'input_sha256': hashlib.sha256(raw_plan).hexdigest(), 'clock': {}}
    authorization = {**value, 'sha256': protocol.CycleAdmission._sha(value)}
    intent = {'experiment_id': 'selected', 'project': 'demo', 'control_home': authorization['control_home'],
        'budget': {'cycle_id': authorization['cycle_id'], 'authorization_sha256': authorization['sha256'],
            'task_queue': protocol.BUDGET_TASK_QUEUE},
        'observation': observed}
    context = {'intent': intent, 'authorization': authorization, 'policy': policy,
        'project': project, 'published_project': project}
    ready = {'authorization_sha256': authorization['sha256']}
    f.capability['cycle_ready_sha256'] = protocol.CycleAdmission._sha(ready)
    cycle = Path(authorization['control_home']) / 'training-cycles/demo/saved-data'
    cycle.mkdir(parents=True)
    (cycle / 'cycle.json').write_bytes(raw_plan)
    (cycle / 'authorization.json').write_text(json.dumps(authorization))
    (cycle / 'ready.json').write_text(json.dumps(ready))
    owner = {'schema_version': 2, 'intent_sha256': protocol.CycleAdmission._sha(intent),
        'context_sha256': protocol.CycleAdmission._sha(context), 'authorization_sha256': authorization['sha256'],
        'execution_capability': f.capability, 'pid': 123, 'start_ticks': '456', 'boot_id': 'b' * 36}
    chain = SimpleNamespace(owner=owner, intent=intent, sha=protocol.CycleAdmission._sha,
        root=state_root, config=tmp_path / 'config', adapter=SimpleNamespace(safe_file=lambda root, name: root / name))
    monkeypatch.setattr(protocol.budget_clock, 'validate', lambda *args: None)
    read = protocol.read_raw
    def original_experiment_read(selected, *args):
        raw = read(selected, *args)
        if selected == path:
            (f.source / 'gate.py').write_bytes(b'drift after earlier round check and before standalone check')
        return raw
    monkeypatch.setattr(protocol, 'read_raw', original_experiment_read)
    with pytest.raises(ValueError, match='gate source changed'):
        execution_evidence.validate_context(context, chain, live=False)


@pytest.mark.parametrize('role', ['active', 'prepared-full', 'baseline-reference'])
def test_cpu_preparation_catalog_rejects_existing_stage_clock_reader_ports(tmp_path, monkeypatch, role):
    """Existing authorization-reader port only; never authorizes a real clock."""
    import ergora.training.cycles as training_cycles

    home = tmp_path / 'control'
    cycle = home / 'training-cycles/demo/original'
    cycle.mkdir(parents=True)
    (cycle.parent / '.original.lock').write_bytes(b'')
    plan = {'definition': {'candidates': [{'experiment_id': 'other'}]},
        'admissions': [{'observation': {'experiment': {'manifest': {}}}}]}
    if role == 'active':
        plan['definition']['candidates'][0]['experiment_id'] = 'selected'
    elif role == 'prepared-full':
        plan['stage_admissions'] = [{'screen': {'experiment_id': 'other'}, 'full': {'experiment_id': 'selected'}}]
    else:
        plan['admissions'][0]['observation']['experiment']['manifest']['baseline_reference'] = {'experiment_id': 'selected'}
    reads = []
    def original_reader(*args):
        reads.append(args)
        return plan, {'original': 'authorization/clock data port'}, None
    monkeypatch.setattr(training_cycles, '_load', original_reader)
    with pytest.raises(ValueError, match='original stage authorization/clock opportunity'):
        training_cycles.assert_preparation_unconsumed(home, 'demo', 'selected', 'f' * 64)
    assert reads == [(home, 'demo', 'original', cycle)]


def test_cpu_preparation_catalog_retains_unknown_records_and_allows_unrelated_reader_port(tmp_path, monkeypatch):
    import ergora.training.cycles as training_cycles

    home = tmp_path / 'control'
    training_cycles.assert_preparation_unconsumed(home, 'demo', 'selected', 'a' * 64)
    cycle = home / 'training-cycles/demo/original'
    cycle.mkdir(parents=True)
    lock = cycle.parent / '.original.lock'
    lock.write_bytes(b'')
    with pytest.raises(ValueError, match='cannot prove original authorization/clock absence'):
        training_cycles.assert_preparation_unconsumed(home, 'demo', 'selected', 'a' * 64)
    assert not list(cycle.iterdir()) and lock.read_bytes() == b''
    monkeypatch.setattr(training_cycles, '_load', lambda *args: ({
        'definition': {'candidates': [{'experiment_id': 'different-stage'}]}, 'admissions': []}, {}, None))
    training_cycles.assert_preparation_unconsumed(home, 'demo', 'selected', 'a' * 64)
    orphan = cycle.parent / '.interrupted.lock'
    orphan.write_bytes(b'')
    with pytest.raises(ValueError, match='incomplete original authorization/clock catalog'):
        training_cycles.assert_preparation_unconsumed(home, 'demo', 'selected', 'a' * 64)
    assert orphan.read_bytes() == b''


@pytest.mark.skipif(sys.platform != 'linux', reason='Original nonblocking shared preparation lock uses Linux flock')
def test_cpu_preparation_clock_port_serializes_original_publisher_and_never_repairs_lock(tmp_path, monkeypatch):
    """A sentinel replaces the clock; only original ordinary lock files are used."""
    import fcntl
    import ergora.training.cycles as training_cycles
    import ergora.training.execution_protocol as protocol

    roles = [{'ordinal': 0, 'experiment_id': 'selected'}]
    monkeypatch.setattr(protocol, 'cpu_contract_roles', lambda plan: roles)
    plan = {'project': {'registration': {'definition': {'execution': {'state_directory': str(tmp_path)}}}}}
    lock = tmp_path / 'ergora/training-preparations/selected.lock'
    lock.parent.mkdir(parents=True)
    lock.write_bytes(b'')
    clock_port = []
    with lock.open('rb') as publisher:
        fcntl.flock(publisher.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            with training_cycles._cpu_preparation_locks(plan):
                clock_port.append('would authorize')
        fcntl.flock(publisher.fileno(), fcntl.LOCK_UN)
        with training_cycles._cpu_preparation_locks(plan):
            with pytest.raises(BlockingIOError):
                fcntl.flock(publisher.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            clock_port.append('guarded clock port only')
    assert clock_port == ['guarded clock port only'] and lock.read_bytes() == b''
    lock.unlink()
    with pytest.raises(FileNotFoundError):
        with training_cycles._cpu_preparation_locks(plan):
            pytest.fail('Missing original preparation lock cannot grant a clock')
    assert not lock.exists()
    roles.clear()
    with training_cycles._cpu_preparation_locks({}) as observed:
        assert observed == []


@pytest.fixture
def original_owner_context_ports(tmp_path, monkeypatch, request):
    """Static input ports for the real owner and public request; no creation APIs."""
    if sys.platform != 'linux':
        pytest.skip('Original budget owner synchronization and locks require Linux/WSL2')
    import asyncio
    from datetime import datetime, timedelta, timezone
    from types import ModuleType, SimpleNamespace
    from ergora.runtime import budget_clock
    from ergora.configuration import registrations
    import ergora.training.cycles as training_cycles
    import ergora.training.materials as materials
    import ergora.training.runtime.budget as budgets
    import ergora.training.runtime.execution as execution
    import ergora.training.execution_protocol as protocol

    counters = dict(cpu_recapture=0, reauthorization=0, training_jobs=0, business_popen=0,
        rpc_connect=0, static_capture_port=0, owner_handoff=0, request_boundary=0)
    typed = getattr(request, 'param', True)
    fixed_at = '2026-01-01T00:00:00+00:00'
    class FixedClockDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            fixed = cls(2026, 1, 1, tzinfo=timezone.utc)
            return fixed.replace(tzinfo=None) if tz is None else fixed.astimezone(tz)
    monkeypatch.setattr(budget_clock, 'datetime', FixedClockDatetime)
    monkeypatch.setattr(budgets, 'now', lambda: fixed_at)
    monkeypatch.setattr(training_cycles, 'now', lambda: fixed_at)
    monkeypatch.setattr(budgets.uuid, 'uuid4', lambda: SimpleNamespace(hex='e' * 32))
    def forbidden(name):
        def fail(*args, **kwargs):
            counters[name] += 1
            raise AssertionError('Forbidden source-only operation: ' + name)
        return fail
    monkeypatch.setattr(materials, 'cpu_execution_identity', forbidden('cpu_recapture'))
    monkeypatch.setattr(materials, 'cpu_context_observation', forbidden('cpu_recapture'))
    monkeypatch.setattr(budget_clock, 'authorize', forbidden('reauthorization'))
    monkeypatch.setattr(training_cycles, 'authorize', forbidden('reauthorization'))
    monkeypatch.setattr(training_cycles, 'authorize_controller', forbidden('reauthorization'))
    monkeypatch.setattr(training, 'start', forbidden('training_jobs'))
    monkeypatch.setattr(subprocess, 'Popen', forbidden('business_popen'))
    connection, models = ModuleType('perf_temporal.connection'), ModuleType('perf_temporal.models')
    connection.connect = forbidden('rpc_connect')
    models.Binding = forbidden('training_jobs')
    package = ModuleType('perf_temporal')
    package.__path__ = []
    monkeypatch.setitem(sys.modules, 'perf_temporal', package)
    monkeypatch.setitem(sys.modules, 'perf_temporal.connection', connection)
    monkeypatch.setitem(sys.modules, 'perf_temporal.models', models)

    sha = protocol.CycleAdmission._sha
    home, state, config, installation = (tmp_path / name for name in ('control', 'state', 'config', 'native-data'))
    native = {'installation': str(installation), 'state_directory': str(state), 'config_directory': str(config)}
    project = {'id': 'demo', 'repo': str(tmp_path / 'source'), 'revision': 1,
        'registration': {'sha256': 'e' * 64, 'operation_id': 'registration-data',
            'definition': {'execution': native}, 'files': {}}}
    source = {'repo': project['repo'], 'commit': 'a' * 40, 'inventory_sha256': 'b' * 64, 'entrypoint': 'driver.py'}
    runner = {'project': 'demo', 'repo': project['repo'], 'configuration_readback': {
        'source': source, 'protocol': 'training-configuration-driver-v1', 'observation_scheme': 'static-data'}}
    body = {'schema_version': 1, 'kind': 'training-cpu-execution-contract', 'operation': 'cpu-diagnostic-v1',
        'implementation': {'source': {**source, 'entrypoint_sha256': 'c' * 64},
            'driver_protocol': 'training-configuration-driver-v1', 'observation_scheme': 'static-data',
            'runner_sha256': sha(runner), 'wrapper_entry': 'ergora.training.configuration:main', 'core_sources_sha256': 'd' * 64},
        'conformance': deepcopy(materials.CPU_CONFORMANCE), 'input_domain': {
            'type': 'object', 'properties': {'batch': {'type': 'integer', 'minimum': 1, 'maximum': 8}},
            'required': ['batch'], 'additionalProperties': False}}
    contract = {**body, 'sha256': sha(body)}
    manifest = {'experiment_id': 'original', 'local_project': 'demo', 'execution': {'operation': 'full-verify'}}
    if typed:
        manifest['execution']['cpu_contract'] = contract
    manifest_raw = (json.dumps(manifest, indent=2) + '\n').encode()
    preview = {'schema_version': 2, 'operation': 'prepare-training', 'control_home': str(home), 'project': 'demo',
        'repo': project['repo'], 'execution': native, 'registration_sha256': 'e' * 64, 'experiment_id': 'original',
        'project_revision': 1, 'request': {'experiment': manifest}, 'sources': {'runner': {'document': runner}},
        'files': {'training/manifests/original.json': manifest_raw.decode()}}
    prepared = {**preview, 'confirmed_preview_sha256': sha(preview), 'confirmation': {
        'kind': 'training-preparation-confirmation', 'actor_id': 'unix:1000:static-data', 'project_revision': 1,
        'request_sha256': sha(preview['request'])}}
    acceptance = materials.make_cpu_preparation_admission(prepared)
    def raw_reference(path, value):
        raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}, raw.decode()
    observed = {'baseline_files': {}, 'experiment': {'manifest': manifest, 'current_runner': runner, 'files': {}}}
    if typed:
        intent_ref, intent_utf8 = raw_reference(tmp_path / 'static-input/preparation.json', prepared)
        admission_ref, admission_utf8 = raw_reference(tmp_path / 'static-input/admission.json', acceptance)
        observed['experiment']['cpu_contract_preparation'] = {
            'contract': contract, 'contract_sha256': contract['sha256'], 'preview_sha256': sha(preview),
            'intent_sha256': sha(prepared), 'intent_ref': intent_ref, 'admission_ref': admission_ref,
            'intent_utf8': intent_utf8, 'admission_utf8': admission_utf8}
    policy = {'wall_seconds': 100, 'cleanup_seconds': 10, 'control_timeout_seconds': 10}
    plan = {'control_home': str(home), 'project': project,
        'definition': {'execution_scope': protocol.FULL_SCOPE, 'budget': policy},
        'admissions': [{'experiment_id': 'original', 'manifest_sha256': hashlib.sha256(manifest_raw).hexdigest(),
            'observation': observed}]}
    raw_plan = (json.dumps(plan, sort_keys=True) + '\n').encode()
    now, boot = datetime(2026, 1, 1, tzinfo=timezone.utc), '1' * 36
    clock = {'authorized_at': now.isoformat(), 'deadline_at': (now + timedelta(seconds=100)).isoformat(),
        'boot_id': boot, 'boottime_ns': 100}
    auth_body = {'schema_version': 1, 'kind': 'static-authorization-input', 'control_home': str(home), 'project': 'demo',
        'cycle_id': 'original-input', 'project_revision': 1, 'input_sha256': hashlib.sha256(raw_plan).hexdigest(),
        'execution': native, 'registration': {'operation_id': 'registration-data', 'intent_sha256': 'f' * 64},
        'clock': clock}
    if typed:
        auth_body['cpu_contracts'] = {'actor_id': 'unix:1000:static-data', 'roles': protocol.cpu_contract_roles(plan)}
    authorization = {**auth_body, 'sha256': sha(auth_body)}
    intent = {'control_home': str(home), 'project': 'demo', 'repo': project['repo'], 'project_revision': 1,
        'execution': native, 'registration_sha256': 'e' * 64, 'experiment_id': 'original', 'operation_id': 'static-owner',
        'observation': observed, 'budget': {'cycle_id': 'original-input', 'authorization_sha256': authorization['sha256'],
            'task_queue': protocol.BUDGET_TASK_QUEUE}}
    ready = {'authorization_sha256': authorization['sha256']}
    cycle = home / 'training-cycles/demo/original-input'
    cycle.mkdir(parents=True)
    (cycle / 'cycle.json').write_bytes(raw_plan)
    (cycle / 'authorization.json').write_text(json.dumps(authorization))
    (cycle / 'ready.json').write_text(json.dumps(ready))
    descriptor_raw = (native_resources.DATA / 'native-runtime/training-executor-admission-v3.json').read_bytes()
    installation.mkdir()
    (installation / 'ergora-native-runtime.json').write_bytes(descriptor_raw)
    interpreter = installation / '.venv/bin/python'
    interpreter.parent.mkdir(parents=True)
    interpreter.write_bytes(b'ordinary metadata fixture; never executed')
    capability = {'protocol': protocol.PROTOCOL, 'admission_protocol': native_resources.TRAINING_PROTOCOL,
        'descriptor_sha256': hashlib.sha256(descriptor_raw).hexdigest(), 'installation': str(installation),
        'native_python': str(interpreter), 'cycle_ready_sha256': sha(ready),
        'gate_sources': {name: hashlib.sha256((PACKAGE_ROOT / name).read_bytes()).hexdigest()
            for name in protocol.GATE_SOURCES}}
    owner_id = {'pid': os.getpid(), 'start_ticks': '200', 'boot_id': boot}
    parent_id = {'pid': os.getppid(), 'start_ticks': '100', 'boot_id': boot}
    binding = {'intent_sha256': sha(intent), 'authorization_sha256': authorization['sha256']}
    def frame(role, identity, parent_pid):
        return {'protocol': 'training-cpu-context-v1', 'contract_sha256': contract['sha256'], 'role': role,
            'binding': binding, 'subject': {**identity, 'start_ticks': int(identity['start_ticks']),
                'tid': identity['pid'], 'parent_pid': parent_pid}, 'snapshot': None, 'state': 'unsupported',
            'reason': 'Static input only; CPU facts were not collected'}
    parent_ref = budget_ref = None
    if typed:
        parent_ref, _ = raw_reference(tmp_path / 'static-input/parent.json', frame('parent', parent_id, 1))
        budget_ref, _ = raw_reference(tmp_path / 'static-input/budget.json', frame('budget', owner_id, parent_id['pid']))
    operation = SimpleNamespace(ident='original', root=state, project=project, execution=native,
        payload={'control_home': str(home), 'cpu_parent_ref': parent_ref, 'timeout': 10}, sha=sha,
        path=lambda suffix: state / ('ergora/training-submissions/original' + suffix), registration=lambda: None)
    budget = budgets.BudgetedStart(operation, intent)
    monkeypatch.setattr(budget, 'source', lambda: (None, plan, authorization, ready))
    monkeypatch.setattr(budget, 'require_active', lambda **kwargs: None)
    monkeypatch.setattr(registrations, 'published_project', lambda *args: deepcopy(project))
    monkeypatch.setattr(protocol, 'source_capability', lambda *args: deepcopy(capability))
    monkeypatch.setattr(native_resources, 'validate_installation', lambda path, **kwargs: installation)
    monkeypatch.setattr(budgets.signal, 'signal', lambda *args: None)
    monkeypatch.setattr(budgets, '_process_identity', lambda pid: deepcopy(owner_id if pid == owner_id['pid'] else parent_id))
    monkeypatch.setattr(protocol.processes, 'identity', lambda pid: deepcopy(owner_id if pid == owner_id['pid'] else parent_id))
    monkeypatch.setattr(budget_clock, '_clock', lambda: (boot, 100))
    def captured_input(*args):
        counters['static_capture_port'] += 1
        return deepcopy(budget_ref)
    monkeypatch.setattr(protocol, 'publish_cpu_process_context', captured_input)
    handoffs = []
    class RequestBoundaryReached(Exception):
        pass
    real_validate = execution_evidence.validate_context
    def validate_boundary(context, chain, **kwargs):
        result = real_validate(context, chain, **kwargs)
        counters['request_boundary'] += 1
        raise RequestBoundaryReached()
    monkeypatch.setattr(execution_evidence, 'validate_context', validate_boundary)
    def records(*args):
        return SimpleNamespace(load=lambda: SimpleNamespace(owner=budget.owner_record(), intent=intent, sha=sha,
            root=state, config=config, budget=budget.folder,
            adapter=SimpleNamespace(safe_file=lambda root, name: root / name)))
    monkeypatch.setattr(protocol, 'ExecutionRecords', records)
    case = SimpleNamespace(budget=budget, operation=operation, intent=intent, project=project, plan=plan,
        authorization=authorization, ready=ready, counters=counters, handoffs=handoffs,
        parent_ref=parent_ref, budget_ref=budget_ref, owner_id=owner_id, boundary=RequestBoundaryReached,
        raw_reference=raw_reference, results=tmp_path / 'source-counters.json', typed=typed,
        before_request=lambda: None)
    def drive(self, context, phase_type):
        counters['owner_handoff'] += 1
        handoffs.append(deepcopy(context))
        budget.validate_cached(context)
        case.before_request()
        asyncio.run(execution.Execution(operation, budget).request())
        raise AssertionError('The public request must stop at its validated source boundary')
    monkeypatch.setattr(execution.Execution, 'drive', drive)
    return case


def test_original_owner_context_survives_public_request_without_recapture(original_owner_context_ports):
    case = original_owner_context_ports
    try:
        with pytest.raises(case.boundary):
            case.budget.own()
    finally:
        owner = json.loads(case.budget.path('owner.json').read_bytes())
        case.results.write_text(json.dumps({'counters': case.counters, 'owner_fields': sorted(owner),
            'producer_context_fields': sorted(case.handoffs[0]), 'owner_context_sha256': owner['context_sha256'],
            'producer_context_sha256': case.operation.sha(case.handoffs[0])}, indent=2) + '\n')
        assert all(case.counters[key] == 0 for key in
            ('cpu_recapture', 'reauthorization', 'training_jobs', 'business_popen', 'rpc_connect'))
    assert case.counters['owner_handoff'] == case.counters['request_boundary'] == 1
    assert owner['context_sha256'] == case.operation.sha(case.handoffs[0])


def _save_context_effect_counters(case, scope):
    case.results.write_text(json.dumps({'scope': scope, 'counters': case.counters}, indent=2) + '\n')
    assert all(case.counters[key] == 0 for key in
        ('cpu_recapture', 'reauthorization', 'training_jobs', 'business_popen', 'rpc_connect'))


@pytest.mark.parametrize('damage', ['missing', 'null', 'wrong-ref', 'raw-ref', 'source', 'owner',
    'subject', 'inline-context', 'oversize-owner'])
def test_original_owner_context_refuses_changed_originals_before_request(original_owner_context_ports, damage):
    case = original_owner_context_ports
    def corrupt_original():
        path = case.budget.path('owner.json')
        owner = json.loads(path.read_bytes())
        if damage == 'source':
            case.plan['project'] = deepcopy(case.plan['project'])
            case.plan['project']['repo'] += '-changed'
            return
        if damage == 'raw-ref':
            frame = Path(case.budget_ref['path'])
            frame.write_bytes(frame.read_bytes() + b'\n')
            return
        if damage == 'oversize-owner':
            import ergora.training.execution_protocol as protocol
            path.write_bytes(b' ' * (protocol.LIMIT + 1))
            return
        if damage == 'missing':
            del owner['cpu_context']
        elif damage == 'null':
            owner['cpu_context'] = None
        elif damage == 'owner':
            owner['intent_sha256'] = 'f' * 64
        elif damage == 'inline-context':
            owner['context'] = case.handoffs[0]
        elif damage in ('wrong-ref', 'subject'):
            if damage == 'wrong-ref':
                changed_ref = case.parent_ref
            else:
                frame = json.loads(Path(case.budget_ref['path']).read_bytes())
                frame['subject']['pid'] += 1
                changed_ref, _ = case.raw_reference(Path(case.budget_ref['path']), frame)
            owner['cpu_context']['budget'] = changed_ref
            changed_context = deepcopy(case.handoffs[0])
            changed_context['cpu_context'] = owner['cpu_context']
            owner['context_sha256'] = case.operation.sha(changed_context)
        path.write_text(json.dumps(owner))
    case.before_request = corrupt_original
    try:
        with pytest.raises(ValueError):
            case.budget.own()
    finally:
        _save_context_effect_counters(case, 'current request refuses ' + damage)
    assert case.counters['owner_handoff'] == 1 and case.counters['request_boundary'] == 0
    assert not (case.operation.root / 'training/jobs').exists()


def test_original_owner_context_recovers_durable_refs_without_restarting(original_owner_context_ports, monkeypatch):
    import ergora.training.cycles as training_cycles

    case = original_owner_context_ports
    publish = training_cycles._record
    owner_path = case.budget.path('owner.json')
    def lost_publication_reply(path, value, **kwargs):
        publish(path, value, **kwargs)
        if path == owner_path:
            raise OSError('Controlled reply loss after original durable owner publication')
    monkeypatch.setattr(training_cycles, '_record', lost_publication_reply)
    try:
        with pytest.raises(OSError, match='Controlled reply loss'):
            case.budget.own()
        original = owner_path.read_bytes(), owner_path.stat().st_ino
        owner = json.loads(original[0])
        recovered = case.budget.context()
        assert recovered['cpu_context'] == owner['cpu_context']
        assert case.operation.sha(recovered) == owner['context_sha256']
        with pytest.raises(ValueError, match='cannot be restarted'):
            case.budget.own()
        with pytest.raises(ValueError, match='matching original live owner'):
            case.budget.validate_cached(recovered)
        assert (owner_path.read_bytes(), owner_path.stat().st_ino) == original
        assert case.counters['static_capture_port'] == 1 and case.counters['owner_handoff'] == 0
    finally:
        _save_context_effect_counters(case, 'durable publication recovery; owner remains unconfirmed, never restarted')


@pytest.mark.parametrize('original_owner_context_ports', [False], indirect=True)
def test_original_owner_context_keeps_no_cpu_manual_full_contract(original_owner_context_ports):
    case = original_owner_context_ports
    try:
        with pytest.raises(case.boundary):
            case.budget.own()
    finally:
        _save_context_effect_counters(case, 'original no-C manual/full request source boundary')
    owner = json.loads(case.budget.path('owner.json').read_bytes())
    assert 'cpu_context' not in owner and 'cpu_context' not in case.handoffs[0]
    assert case.counters['static_capture_port'] == 0 and case.counters['request_boundary'] == 1
    assert owner['context_sha256'] == case.operation.sha(case.handoffs[0])


def test_original_owner_context_history_parser_never_reads_host_refs(original_owner_context_ports, monkeypatch):
    import ergora.training.execution_protocol as protocol

    case = original_owner_context_ports
    try:
        with pytest.raises(case.boundary):
            case.budget.own()
        owner = json.loads(case.budget.path('owner.json').read_bytes())
        historical = deepcopy(owner)
        for role in ('parent', 'budget'):
            historical['cpu_context'][role]['path'] = '/unavailable/original/' + role + '.json'
        def no_host_read(*args, **kwargs):
            raise AssertionError('Pure saved owner decoding must not follow original host paths')
        monkeypatch.setattr(protocol, 'read_raw', no_host_read)
        assert protocol.owner_record(historical) == historical
        del historical['cpu_context']
        assert protocol.owner_record(historical) == historical
    finally:
        _save_context_effect_counters(case, 'historical owner shape decoder only, unavailable host refs remain data')


@pytest.fixture
def capacity_reference_case(tmp_path, monkeypatch):
    """Complete public input/authorization data with no native, CPU or service effects.

    The public readers and original authorization validator stay real. Only the
    later live-readiness port is substituted in public admission controls. D1's
    material availability is not exercised; this proves transport/source binding,
    not material or service fitness.
    """
    if sys.platform != 'linux':
        pytest.skip('Controller capacity protocol requires Linux/WSL2')
    import asyncio
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace
    from ergora.configuration import catalog, registrations
    from ergora.runtime import budget_clock
    from ergora.storage.state import State
    import ergora.training.configuration as configuration
    import ergora.training.cycles as cycles
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials

    calls = []
    def forbidden(name):
        def refuse(*args, **kwargs):
            calls.append('FORBIDDEN:' + name)
            raise AssertionError('No-effect capacity fixture reached ' + name)
        return refuse
    monkeypatch.setattr(subprocess, 'Popen', forbidden('process'))
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', forbidden('async-process'))
    monkeypatch.setattr(protocol.processes, 'run', forbidden('supervisor/job/model'))
    monkeypatch.setattr(materials, 'cpu_context_observation', forbidden('CPU-capture'))
    monkeypatch.setattr(budget_clock, 'authorize', forbidden('real-clock'))
    for name in ('training_setup', 'training_preparation', 'training_files', 'training_submission', 'training_execution'):
        if hasattr(training_native, name):
            monkeypatch.setattr(training_native, name, forbidden(name))
    monkeypatch.setattr(training, 'start', forbidden('training-start'))
    monkeypatch.setattr(cycles, '_live_materials', forbidden('live-materials'))
    fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.replace(tzinfo=None) if tz is None else fixed.astimezone(tz)
    boot, ticks = '1' * 36, 123456789
    monkeypatch.setattr(budget_clock, 'datetime', FixedDatetime)
    monkeypatch.setattr(budget_clock, '_clock', lambda: (boot, ticks))
    parent = {'pid': 12345, 'start_ticks': '123456', 'boot_id': boot}
    monkeypatch.setattr(protocol.processes, 'identity', lambda pid: deepcopy(parent))
    sha = protocol.CycleAdmission._sha
    sources = cycles._measurement_sources()
    core_sha = sha(configuration.cpu_contract_sources())

    def build(scope=protocol.FULL_SCOPE, count=32, *, oversized=False):
        root = tmp_path / ('bounded' if scope == protocol.D_SCOPE else 'full')
        state = State(root / 'control Ω space')
        project_id, cycle_id = 'P' + 'p' * 63, 'C' + 'c' * 79
        execution = {name: str(root / leaf) for name, leaf in (
            ('installation', 'native'), ('config_directory', 'config'), ('state_directory', 'state'))}
        project = {'schema_version': 1, 'id': project_id, 'repo': str(root / 'repo'),
            'created': fixed.isoformat(), 'revision': 1, 'bindings': deepcopy(catalog.DEFAULT_BINDINGS)}
        definition = {'templates': ['training-optimization'], 'execution': execution,
            'tracker': {'kind': 'local', 'project': 'local/capacity'}, 'base_sha': 'a' * 40,
            'allowed_paths': ['src'], 'checks': {'behavior': ['x' * 40000 if oversized else 'no-effect']},
            'scope_policy': {'schema_version': 1, 'protected_paths': ['.git']}}
        registration_sha = sha({'id': project_id, 'repo': project['repo'], 'definition': definition})
        project['registration'] = {'schema_version': 1, 'definition': definition, 'sha256': registration_sha,
            'status': 'published', 'operation_id': 'a' * 32,
            'files': registrations.publication_files(project, definition, state.root, registration_sha)}
        pending = deepcopy(project)
        pending['registration']['status'] = 'pending'
        journal = {'schema_version': 1, 'source': {'kind': 'registration'}, 'before': None, 'after': pending}
        folder = state.root / 'registrations' / project_id
        folder.mkdir(parents=True)
        cycles._record(folder / ('a' * 32 + '.json'), journal)
        cycles._record(folder / ('a' * 32 + '.result.json'), {'schema_version': 1, 'status': 'published',
            'operation_id': 'a' * 32, 'intent_sha256': sha(journal), 'registration_sha256': registration_sha})
        with state.connect() as db:
            db.execute('INSERT INTO projects VALUES (?, ?)', (project_id, json.dumps(project)))
        assert registrations.published_project(state.root, project_id, 'a' * 32, sha(journal)) == project
        source = {'repo': project['repo'], 'commit': 'b' * 40, 'inventory_sha256': 'c' * 64, 'entrypoint': 'driver.py'}
        runner = {'schema_version': 2, 'runner_template_id': 'capacity', 'project': project_id,
            'repo': project['repo'], 'command': ['/never-executed/python', '{configuration_driver}', '{configuration_request}'],
            'timeout_seconds': 60, 'configuration_readback': {'protocol': 'training-configuration-driver-v1',
                'source': source, 'prepared_json_format': None, 'manifest_configuration_role': 'source-bytes',
                'observation_scheme': 'capacity', 'baseline_reference_protocol': 'baseline-reference-v1',
                'screen': {'protocol': 'training-screen-v1', 'scheme': 'capacity'}}}
        body = {'schema_version': 1, 'kind': 'training-cpu-execution-contract', 'operation': 'cpu-diagnostic-v1',
            'implementation': {'source': {**source, 'entrypoint_sha256': 'd' * 64},
                'driver_protocol': 'training-configuration-driver-v1', 'observation_scheme': 'capacity',
                'runner_sha256': sha(runner), 'wrapper_entry': 'ergora.training.configuration:main',
                'core_sources_sha256': core_sha}, 'conformance': deepcopy(materials.CPU_CONFORMANCE),
            'input_domain': {'type': 'object', 'properties': {'batch': {'type': 'integer', 'minimum': 1, 'maximum': 8}},
                'required': ['batch'], 'additionalProperties': False}}
        contract = {**body, 'sha256': sha(body)}
        baseline = {'baseline_id': 'capacity-baseline', 'commit': 'e' * 40,
            'config_sha256': 'f' * 64, 'workload_fingerprint': '0' * 64}
        selector = {'experiment_id': 'baseline', 'evidence_sha256': '1' * 64, 'reference_sha256': '2' * 64}
        profile = {'protocol': 'training-profile-v1', 'tool': 'cprofile-json', 'reader': 'cprofile-json-v1',
            'source_operation': 'cpu-diagnostic-v1', 'phases': ['baseline', 'screen'], 'ranks': [0],
            'window': {'unit': 'source_samples', 'work': 1, 'warmup_work': 0}, 'captures': 1,
            'maximum_seconds': 1, 'max_raw_bytes': 1000, 'max_derived_bytes': 1000, 'required': True}
        prefix = 'state/training/projects/' + project_id + '/perf/'
        def admitted(ident, operation='full-verify', verification=None):
            execution_plan = {'operation': operation, 'cpu_contract': contract}
            if verification is not None:
                execution_plan['plan'] = {'scheme': 'capacity', 'requested_tier': 'screened',
                    'verification_experiment_id': verification, 'input_plan': {'scheme': 'capacity', 'sha256': '3' * 64},
                    'window': {'unit': 'source_samples', 'minimum_work': 1, 'maximum_work': 1,
                        'warmup_maximum_work': 0, 'maximum_windows': 1, 'maximum_seconds': 1},
                    'checks': [{'id': kind, 'kind': kind, 'contract_sha256': '4' * 64, 'source_entrypoint': 'driver.py'}
                        for kind in ('finite', 'behavior')], 'resources': [], 'screening': {'target': 'throughput',
                        'minimum_improvement_fraction': 0, 'noise_fraction': 0, 'comparison_scheme': 'capacity'}}
            manifest = {'schema_version': 1, 'experiment_id': ident, 'baseline_id': baseline['baseline_id'],
                'baseline_commit': baseline['commit'], 'candidate_commit': '5' * 40,
                'base_config_sha256': baseline['config_sha256'], 'candidate_config_sha256': '6' * 64,
                'workload_fingerprint': baseline['workload_fingerprint'], 'dataset_manifest_sha256': '7' * 64,
                'initial_checkpoint_sha256': '8' * 64, 'environment_fingerprint': '9' * 64,
                'validation_contract_sha256': 'a' * 64, 'comparison_tool_sha256': 'b' * 64,
                'checks_required': ['behavior'], 'quality_required': True, 'performance_policy': {'minimum_gain': 0},
                'track': 'N', 'allowed_changes': ['Declared fixture intervention'], 'owner': 'fixture', 'author': 'fixture',
                'contract_approved': True, 'candidate_sha': '5' * 40, 'baseline_sha': baseline['commit'],
                'local_project': project_id, 'runner_template_id': 'capacity', 'max_run_seconds': 60,
                'execution': execution_plan, 'baseline_reference': selector,
                'configuration_inputs': {'kind': 'git-source', 'path': 'config.json'}}
            manifest_raw = protocol._cycle_wire_bytes(manifest)
            manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
            preview = {'schema_version': 2, 'operation': 'prepare-training', 'control_home': str(state.root),
                'project': project_id, 'repo': project['repo'], 'execution': execution,
                'registration_sha256': registration_sha, 'experiment_id': ident, 'project_revision': 1,
                'request': {'experiment': manifest}, 'sources': {'runner': {'document': runner}},
                'files': {'training/manifests/' + ident + '.json': manifest_raw.decode()}}
            intent = {**preview, 'confirmed_preview_sha256': sha(preview), 'confirmation': {
                'kind': 'training-preparation-confirmation', 'actor_id': 'unix:1000:capacity',
                'project_revision': 1, 'request_sha256': sha(preview['request'])}}
            acceptance = materials.make_cpu_preparation_admission(intent)
            raw_intent, raw_acceptance = protocol._cycle_wire_bytes(intent), protocol._cycle_wire_bytes(acceptance)
            preparations = Path(execution['state_directory']) / 'ergora/training-preparations'
            preparations.mkdir(parents=True, exist_ok=True)
            material = {'contract': contract, 'contract_sha256': contract['sha256'],
                'preview_sha256': sha(preview), 'intent_sha256': sha(intent),
                'intent_ref': {'path': str(preparations / (ident + '.intent.json')), **protocol._cycle_reference(raw_intent)},
                'admission_ref': {'path': str(preparations / (ident + '.cpu-contract-admission.json')),
                    **protocol._cycle_reference(raw_acceptance)},
                'intent_utf8': raw_intent.decode(), 'admission_utf8': raw_acceptance.decode()}
            Path(material['intent_ref']['path']).write_bytes(raw_intent)
            Path(material['admission_ref']['path']).write_bytes(raw_acceptance)
            (preparations / (ident + '.lock')).write_bytes(b'')
            files = {prefix + 'experiments/' + ident + '/manifest.json': manifest_sha,
                'state/training/manifests/' + ident + '.json': manifest_sha,
                'state/training/specs/' + ident + '.json': 'c' * 64,
                'config/training-runners/capacity.json': sha(runner),
                'state/ergora/training-preparations/' + ident + '.intent.json': material['intent_ref']['sha256'],
                'state/ergora/training-preparations/' + ident + '.cpu-contract-admission.json': material['admission_ref']['sha256']}
            binding = {'experiment_id': ident, 'manifest_sha': manifest_sha,
                'candidate_sha': manifest['candidate_sha'], 'baseline_sha': manifest['baseline_sha']}
            experiment = {'experiment_id': ident, 'binding': binding, 'manifest': manifest, 'spec': {
                'binding': binding, 'manifest_uri': (Path(execution['state_directory']) / 'training/manifests' / (ident + '.json')).as_uri(),
                'poll_seconds': 30, 'max_run_seconds': 60, 'release_wait_seconds': 60, 'cancel_wait_seconds': 30},
                'current_runner': runner, 'files': files, 'track': 'N', 'baseline_id': baseline['baseline_id'],
                'workload_fingerprint': baseline['workload_fingerprint'], 'baseline_matches': True, 'baseline_error': None,
                'max_run_seconds': 60, 'runtime_status': 'not_queried', 'job_id': None, 'started_recorded': False,
                'recorded_result_state': None, 'fence_recorded': False, 'recorded_gate': None, 'job_request': None,
                'started': None, 'result': None, 'gate_report': None, 'fence': None, 'negative_result': None,
                'execution': execution_plan, 'cpu_contract_preparation': material}
            return {'project': project_id, 'project_revision': 1, 'experiment_id': ident, 'manifest_sha256': manifest_sha,
                'ready_for_new_start': True, 'read_only': True, 'execution_authorized': False,
                'runtime_status': 'not_queried', 'submission': None, 'observation': {'baseline': baseline,
                    'baseline_files': {prefix + 'baseline.json': 'd' * 64}, 'experiment': experiment, 'runtime_status': 'not_queried'}}
        stages = []
        for ordinal in range(count):
            ident = ('selected-' + str(ordinal)).ljust(80, 'x')
            stages.append({'screen': admitted(ident, 'training-screen-v1', 'full-' + str(ordinal)),
                'full': admitted('full-' + str(ordinal))} if scope == protocol.D_SCOPE else {'selected': admitted(ident)})
        admissions = [pair['screen' if scope == protocol.D_SCOPE else 'selected'] for pair in stages]
        request = {'schema_version': 2, 'execution_scope': scope,
            'budget': {'wall_seconds': 300, 'cleanup_seconds': 30, 'control_timeout_seconds': 20},
            'candidates': [{'experiment_id': item['experiment_id'], 'manifest_sha256': item['manifest_sha256'],
                'change': 'Declared fixture choice', 'next_bottleneck': 'No measurement claimed'} for item in admissions]}
        plan = {'schema_version': 2, 'kind': 'training-cycle-plan', 'control_home': str(state.root),
            'project': project, 'definition': request, 'admissions': admissions}
        if scope == protocol.D_SCOPE:
            analyst = {'manifest': {'directory': str(root / 'analyst'), 'preview_sha256': 'e' * 64},
                'instance': 'root/analyst', 'binding': catalog.resolve_binding(project, 'implementer')['binding'],
                'maximum_seconds': 5, 'mode': 'text-only'}
            request.update(search={'directory': str(root / 'search'), 'sha256': 'f' * 64}, historical_failures=[],
                profile_policy=profile, analyst=analyst, resources={'kind': 'cpu'})
            choices = []
            for ordinal, pair in enumerate(stages):
                choices.append({'ordinal': ordinal, 'variant_id': 'variant-' + str(ordinal),
                    'configuration': {'sha256': '6' * 64}, 'stages': {name: {'experiment_id': item['experiment_id'],
                        'native_plan': {'files': {'training/manifests/' + item['experiment_id'] + '.json':
                            protocol._cycle_wire_bytes(item['observation']['experiment']['manifest']).decode()}},
                        'native_request': {'experiment': item['observation']['experiment']['manifest']}}
                        for name, item in pair.items()}})
            plan.update(stage_admissions=stages, preparation_sources=[{} for _ in stages], material_files={},
                stage_map=[{'ordinal': number, 'variant_id': choices[number]['variant_id'], **{name: {
                    'experiment_id': item['experiment_id'], 'manifest_sha256': item['manifest_sha256'],
                    'admission_sha256': sha(item)} for name, item in pair.items()}} for number, pair in enumerate(stages)],
                search={'sha256': request['search']['sha256'], 'plan': {'project': {'id': project_id, 'repo': project['repo'],
                    'revision': 1, 'registration_sha256': registration_sha}, 'choices': choices,
                    'performance_policy': admissions[0]['observation']['experiment']['manifest']['performance_policy'],
                    'request': {'profile_policy': profile, 'experiment_template': {'baseline_reference': selector}}}},
                analyst={**analyst, 'definition_id': 'fixture-analyst', 'definition_version': '1.0.0',
                    'definition_digest': 'e' * 64, 'project_binding': catalog.resolve_binding(project, 'implementer'),
                    'composition': {'instances': [{'path': analyst['instance'], 'kind': 'agent',
                        'ref': {'id': 'fixture-analyst', 'version': '1.0.0', 'digest': 'e' * 64},
                        'permissions': {'write': False, 'shell': False, 'network': False},
                        'role': 'implementer', 'backend_request': {}}]}},
                cpu_contract_baseline=admitted('baseline')['observation']['experiment']['cpu_contract_preparation'])
        # Exercise the actual public plan validator, including nested full stages and C/A roles.
        raw_plan = (json.dumps(plan, ensure_ascii=False, indent=1) + '\n').encode()
        assert cycles._decode(raw_plan) == plan
        directory = state.root / 'training-cycles' / project_id / cycle_id
        directory.mkdir(parents=True)
        (directory / 'cycle.json').write_bytes(raw_plan)
        clock = {'authorized_at': fixed.isoformat(), 'deadline_at': (fixed + timedelta(seconds=300)).isoformat(),
            'boot_id': boot, 'boottime_ns': ticks}
        value = {'schema_version': 5, 'kind': 'training-cycle-authorization', 'cycle_id': cycle_id,
            'control_home': str(state.root), 'project': project_id, 'project_revision': 1,
            'input_sha256': hashlib.sha256(raw_plan).hexdigest(), 'registration': cycles._origin(state.root, project),
            'execution': execution, 'clock': clock,
            'controller': cycles._controller(state.root, project_id, cycle_id, hashlib.sha256(raw_plan).hexdigest(),
                'unix:1000:capacity', 5, scope), 'measurement_sources': sources,
            'cpu_contracts': {'actor_id': 'unix:1000:capacity', 'roles': protocol.cpu_contract_roles(plan)}}
        authorization = {**value, 'sha256': sha(value)}
        assert cycles._authorization(state.root, project_id, cycle_id, plan, value['input_sha256'], authorization) == authorization
        cycles._record(directory / 'authorization.json', authorization)
        snapshot = protocol._cycle_snapshot(directory, plan, authorization)
        admission = protocol.CycleAdmission(directory, authorization)
        original = admission.intent_record()['workflow_input']
        return SimpleNamespace(state=state, project=project, plan=plan, directory=directory,
            authorization=authorization, snapshot=snapshot, admission=admission, original=original,
            calls=calls, clock=clock, parent=parent, raw_plan=raw_plan, sources=sources)
    return build


@pytest.mark.parametrize('scope', ['ordered-selected-native-once', 'bounded-screen-profile-skip'])
def test_cycle_reference_public32_complete_originals_and_control_envelopes(
        capacity_reference_case, monkeypatch, record_property, scope):
    """Real public validators/encoders; simulated future owners, no execution fitness claim."""
    import asyncio
    from types import SimpleNamespace
    from temporalio.api.common.v1 import Payloads
    from temporalio.converter import DataConverter
    from ergora.storage.state import file_lock
    import ergora.training.cycles as cycles
    import ergora.training.execution_protocol as protocol
    import ergora.training.runtime.worker as worker
    import ergora.training.runtime.budget as budgets

    f = capacity_reference_case(scope)
    assert len(f.authorization['cpu_contracts']['roles']) == (65 if scope == protocol.D_SCOPE else 32)
    assert f.authorization['measurement_sources'] == cycles._measurement_sources()
    assert f.snapshot['plan_ref'] == protocol._cycle_reference(f.raw_plan)
    assert f.snapshot['authorization_ref']['sha256'] != f.authorization['sha256']
    window = {'boot_id': f.clock['boot_id'], 'started_ns': f.clock['boottime_ns'],
        'deadline_ns': f.clock['boottime_ns'] + 20_000_000_000}
    controller = {'protocol': f.original['protocol'], 'workflow_id': f.authorization['controller']['workflow_id'],
        'run_id': '01234567-89ab-cdef-0123-456789abcdef',
        'intent_sha256': protocol.CycleAdmission._sha(f.admission.intent_record()), 'ordinal': 0, 'predecessor': None}
    def context(action):
        return {'workflow_input': f.original, 'service_namespace': 'capacity Ω', 'activity_source': {
            'workflow_id': controller['workflow_id'], 'workflow_run_id': controller['run_id'],
            'workflow_type': protocol.cycle_workflow_type(f.original['protocol']), 'workflow_namespace': 'capacity Ω',
            'namespace': 'capacity Ω', 'activity_id': 'candidate-0-' + action,
            'activity_type': protocol.cycle_activity_names()[action],
            'task_queue': protocol.CYCLE_STOP_TASK_QUEUE_V3 if action == 'stop' else protocol.CYCLE_TASK_QUEUE_V3,
            'attempt': 1}}
    execution = f.authorization['execution']
    owner = {'schema_version': 2, 'intent_sha256': '1' * 64, 'authorization_sha256': f.authorization['sha256'],
        'context_sha256': '2' * 64, **f.parent, 'execution_capability': {'protocol': protocol.PROTOCOL,
            'admission_protocol': native_resources.TRAINING_PROTOCOL,
            'descriptor_sha256': hashlib.sha256((PACKAGE_ROOT / 'data/native-runtime/training-executor-admission-v3.json').read_bytes()).hexdigest(),
            'installation': execution['installation'], 'native_python': str(Path(execution['installation']) / '.venv/bin/python'),
            'cycle_ready_sha256': '3' * 64, 'gate_sources': {name: hashlib.sha256((PACKAGE_ROOT / name).read_bytes()).hexdigest()
                for name in protocol.GATE_SOURCES}}}
    cpu_root = Path(execution['state_directory']) / 'ergora/training-submissions' / (
        f.plan['definition']['candidates'][0]['experiment_id'] + '.budget')
    cpu_root.mkdir(parents=True)
    owner['cpu_context'] = {}
    for role in ('parent', 'budget', 'cycle'):
        path = cpu_root / ('controlled-' + role + '.json')
        raw = protocol._cycle_wire_bytes({'state': 'unsupported', 'role': role})
        path.write_bytes(raw)
        owner['cpu_context'][role] = {'path': str(path), **protocol._cycle_reference(raw)}
    protocol.owner_record(owner)
    sizes, operations = {}, {}
    for mode in ('prepare-controller', 'submit-controller', 'reconcile-controller', *protocol.CYCLE_CANDIDATE_MODES,
                 *protocol.CYCLE_MEASUREMENT_MODES, 'stop-writer', 'notify-owner', 'drain', 'observe-execution'):
        arguments = {'snapshot': f.snapshot, 'window': window}
        if mode in (*protocol.CYCLE_CANDIDATE_MODES, *protocol.CYCLE_MEASUREMENT_MODES):
            arguments.update(ordinal=0, start_context={'controller': controller})
            action = ('start' if mode in protocol.CYCLE_START_MODES else 'reconcile' if mode == 'reconcile-candidate'
                else 'request-execution-or-observe' if mode == 'request-execution-candidate' else mode)
            arguments['activity_context'] = context(action)
            if mode in ('confirm-candidate', 'dispatch-candidate'):
                arguments['start_context'] = {**arguments['start_context'], 'origin_operation_id': '4' * 32,
                    'intent_sha256': owner['intent_sha256'],
                    **({'root_process': f.parent} if mode == 'confirm-candidate' else {'owner': owner})}
        elif mode in ('notify-owner', 'observe-execution'):
            arguments['ordinal'] = 31
        if mode in ('stop-writer', 'notify-owner', 'drain', 'observe-execution'):
            arguments['activity_context'] = context('stop')
        if mode == 'stop-writer':
            arguments['reason'] = 'Finite operator reason Ω'
        operation = protocol._CycleOperation(f.state.root, f.project['id'], f.authorization['cycle_id'],
            f.authorization['sha256'], mode, **arguments)
        protocol.resolve_cycle_snapshot(operation.payload)
        assert not operation.capacity_rejected
        sizes[mode + '-request'] = len(operation.encoded)
        operations[mode] = operation
    # A nonempty original predecessor and typed owner refs also cross the same
    # current wire. These are complete controlled fact shapes, never real results.
    previous = f.plan['admissions'][30]
    ref_path = f.directory / 'controlled-previous-observation.json'
    ref_raw = protocol._cycle_wire_bytes({'kind': 'controlled-unqualified-facts'})
    ref_path.write_bytes(ref_raw)
    reference = {'path': str(ref_path), **protocol._cycle_reference(ref_raw)}
    digests = {name: '7' * 64 for name in ('request', 'launch', 'attempt', 'ack', 'stopped')}
    if scope == protocol.D_SCOPE:
        entry_body = {'ordinal': 30, 'variant_id': '8' * 64, 'stage_map_sha256': '9' * 64,
            'kind': 'executed', 'predecessor_sha256': 'a' * 64, 'sources': {'operation': reference,
                'intent_sha256': 'b' * 64, 'workflow_id': 'perf-experiment/' + previous['experiment_id'],
                'run_id': controller['run_id'], 'native_binding': previous['observation']['experiment']['binding'],
                'job_id': 'local-perf-' + previous['experiment_id'], 'managed': digests, 'cleanup': reference},
            'observation': reference, 'diagnostics': {key: reference for key in
                ('profile', 'packet', 'analysis', 'baseline_analysis')}}
        entry = {**entry_body, 'sha256': protocol.CycleAdmission._sha(entry_body)}
        predecessor = {'prefix': {'path': str(f.directory / 'controller/trials/trials.json'),
            'sha256': 'c' * 64, 'bytes': 10000, 'trials': 31, 'last_trial_sha256': entry['sha256']}, 'acceptance': entry}
    else:
        acceptance = {'observation': reference, 'source_operation_id': '8' * 32,
            'candidate': {'ordinal': 30, 'experiment_id': previous['experiment_id'],
                'manifest_sha256': previous['manifest_sha256'], 'project_revision': 1,
                'registration_sha256': f.project['registration']['sha256']},
            'submission': {'intent_sha256': '9' * 64, 'workflow_id': 'perf-experiment/' + previous['experiment_id'],
                'run_id': controller['run_id'], 'spec_sha256': 'a' * 64},
            'execution': {'owner_sha256': 'b' * 64, 'record_sha256': digests, 'raw_inventory_sha256': 'c' * 64},
            'runtime': {'namespace': 'capacity Ω', 'kind': 'status', 'phase': 'AWAITING_RELEASE',
                'job_id': 'local-perf-' + previous['experiment_id'], 'binding_sha256': 'd' * 64,
                'memo_sha256': 'e' * 64, 'evidence_sha': 'f' * 64, 'report_uri': None},
            'evidence': {key: '0' * 64 for key in ('evidence_sha256', 'gate_report_sha256', 'files_sha256')},
            'common_sha256': '1' * 64, 'measurement_sources_sha256': protocol.CycleAdmission._sha(f.sources)}
        predecessor = {'prefix': {'directory': str(f.directory / 'controller/rounds/30'), 'sha256': '2' * 64,
            'bytes': 10000, 'rounds': 31, 'last_round_sha256': '3' * 64, 'initial_anchor_sha256': '4' * 64},
            'acceptance': acceptance}
    protocol.validate_round_predecessor(predecessor, 31)
    for mode in ('dispatch-candidate', 'collect-round'):
        payload = deepcopy(operations[mode].payload)
        payload['identity']['ordinal'] = 31
        payload['start_context']['controller'].update(ordinal=31, predecessor=predecessor)
        payload['activity_context']['activity_source']['activity_id'] = 'candidate-31-' + mode
        protocol.validate_cycle_operation(payload)
        resolved, _ = protocol.resolve_cycle_snapshot(payload)
        assert resolved['definition']['candidates'][31] == f.plan['definition']['candidates'][31]
        sizes[mode + '-with-predecessor-request'] = len(protocol._cycle_wire_bytes(payload))
    prepared = operations['prepare-candidate']
    selected = []
    validate = protocol.validate_cpu_contract_authority
    def authority(plan, authorization, ident):
        selected.append(ident)
        return validate(plan, authorization, ident)
    monkeypatch.setattr(protocol, 'validate_cpu_contract_authority', authority)
    for ordinal, candidate in enumerate(f.plan['definition']['candidates']):
        payload = deepcopy(prepared.payload)
        payload['identity']['ordinal'] = ordinal
        protocol._cycle_cpu_contract(payload)
        assert selected[-1] == candidate['experiment_id']
    cold = protocol._CycleOperation(f.state.root, f.project['id'], f.authorization['cycle_id'],
        f.authorization['sha256'], 'inspect')
    inspection = worker._cycle_operation(cold.payload)
    assert inspection['snapshot'] == f.snapshot
    sizes['cold-helper-result'] = len(json.dumps(inspection, ensure_ascii=False, allow_nan=False).encode())
    sizes['cold-result-frame'] = len(protocol._cycle_wire_bytes({**cold.identity, 'event': 'result', 'result': inspection}))
    sizes['stopped-frame'] = len(protocol._cycle_wire_bytes({**cold.identity, 'event': 'stopped', 'process': {
        'status': 'succeeded', 'returncode': 0, 'output': str(cold.output / 'helper')}}))
    # The real root material builder consumes only temporary original records. Its
    # live-readiness port is irrelevant to encoding and is explicitly substituted.
    prepared.output.mkdir(parents=True)
    (prepared.output / 'request.json').write_bytes(prepared.encoded)
    ident = f.plan['definition']['candidates'][0]['experiment_id']
    root = Path(execution['state_directory'])
    prefix = root / 'ergora/training-submissions'
    prefix.mkdir(parents=True, exist_ok=True)
    intent = {'control_home': str(f.state.root), 'project': f.project['id'], 'execution': execution,
        'operation_id': '5' * 32, 'budget': {'cycle_id': f.authorization['cycle_id'],
            'authorization_sha256': f.authorization['sha256'], 'task_queue': protocol.BUDGET_TASK_QUEUE,
            'controller': controller}}
    operation = SimpleNamespace(project=f.project, ident=ident, root=root, execution=execution,
        payload={'timeout': 20}, sha=protocol.CycleAdmission._sha,
        path=lambda suffix: prefix / (ident + suffix))
    budget = budgets.BudgetedStart(operation, intent)
    monkeypatch.setattr(budget, 'require_active', lambda **kwargs: f.calls.append('temporary-source-port'))
    monkeypatch.setattr(budgets, '_process_identity', lambda pid: deepcopy(f.parent))
    with file_lock(operation.path('.lock'), blocking=False):
        launch = budget.launch_context(prepared.payload)
    protocol.validate_cycle_root_request(launch['request'])
    sizes['root-launch'] = len(json.dumps(launch, ensure_ascii=False, allow_nan=False).encode())
    sizes['root-request'] = len(protocol._cycle_wire_bytes(launch['request']))
    sizes['prepare-result-frame'] = len(protocol._cycle_wire_bytes({**prepared.identity, 'event': 'result',
        'result': {'status': 'new_offer', 'intent_sha256': budget.identity['intent_sha256'], 'launch': launch}}))
    retention = protocol._request_retention_envelope(operations['submit-controller'].payload, 40000)
    sizes['retention-control'] = len(protocol._cycle_wire_bytes(retention))
    sizes['retention-confirmation'] = len(protocol._cycle_wire_bytes({'protocol': protocol._REQUEST_RETENTION_PROTOCOL,
        'identity': operations['submit-controller'].identity, 'ref': {'file': 'request.json', 'bytes': 40000, 'sha256': '6' * 64}}))
    records = []
    async def no_effect(operation):
        result = operation.observation({'status': 'unknown', 'reason': 'No-effect source fixture'})
        raw = protocol._cycle_wire_bytes(result)
        operation.output.mkdir(parents=True, exist_ok=True)
        target = operation.output / 'helper/stdout.txt'
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(raw)
        operation.result_ref = {'file': 'helper/stdout.txt', **protocol._cycle_reference(raw)}
        return result
    monkeypatch.setattr(protocol._CycleOperation, 'run', no_effect)
    # Removing originals cannot make parent stop supervision hash large sources.
    (f.directory / 'cycle.json').unlink()
    (f.directory / 'authorization.json').unlink()
    monkeypatch.setattr(protocol, 'resolve_cycle_snapshot', lambda *args: pytest.fail('SDK parent stop cannot resolve original files'))
    outcome = asyncio.run(worker.stop_live_controller(f.state.root, f.project['id'], f.authorization['cycle_id'],
        f.authorization['sha256'], reason='Finite operator reason Ω', inspection=inspection,
        activity_context=context('stop'), operation_records=records, window=window))
    assert len(outcome['operations']) == len(records) == 66
    assert {item['ordinal'] for item in records if item['mode'] == 'notify-owner'} == set(range(32))
    assert protocol.cycle_operation_remaining(prepared.payload) == 20
    envelope = {'schema_version': 4, 'protocol': 'ergora-training-cycle-activity-v4', 'action': 'stop',
        'status': 'unknown', 'workflow_input': f.original, 'controller': controller,
        'observation': inspection['observation'], 'inspection': worker._activity_operation_result(cold,
            cold.observation(inspection)), 'operations': records, 'runtime_status': 'not_queried', 'facts': None}
    async def measure():
        converter = DataConverter.default
        for name, value in [('activity-stop', envelope), ('activity-input', {'workflow_input': f.original,
                'ordinal': 0, 'predecessor': None})]:
            await worker._cycle_capacity(value, converter)
            sizes[name + '-SDK'] = Payloads(payloads=await converter.encode([value])).ByteSize()
    asyncio.run(measure())
    assert max(sizes.values()) <= protocol._CYCLE_LIMIT
    assert not any(item.startswith('FORBIDDEN:') for item in f.calls)
    record_property('capacity_bytes', json.dumps(sizes, sort_keys=True))
    record_property('capacity_scope', 'Complete public plan/_authorization and actual encoders; future SDK/operator values remain bounded at send')


@pytest.mark.parametrize('change', ['plan-bytes', 'plan-format', 'authorization-bytes', 'authorization-format',
    'canonical-authorization', 'clock', 'policy', 'count', 'ordinal'])
def test_cycle_reference_mismatch_refuses_cpu_admission_before_capture(capacity_reference_case, change):
    import ergora.training.execution_protocol as protocol
    f = capacity_reference_case(count=2)
    controller = {'protocol': f.original['protocol'], 'workflow_id': f.authorization['controller']['workflow_id'],
        'run_id': 'capacity-run', 'intent_sha256': protocol.CycleAdmission._sha(f.admission.intent_record()),
        'ordinal': 0, 'predecessor': None}
    operation = protocol._CycleOperation(f.state.root, f.project['id'], f.authorization['cycle_id'],
        f.authorization['sha256'], 'prepare-candidate', snapshot=deepcopy(f.snapshot), ordinal=0,
        start_context={'controller': controller})
    if change in ('plan-bytes', 'authorization-bytes'):
        operation.payload['snapshot']['plan_ref' if change == 'plan-bytes' else 'authorization_ref']['bytes'] += 1
    elif change in ('plan-format', 'authorization-format'):
        path = f.directory / ('cycle.json' if change == 'plan-format' else 'authorization.json')
        path.write_bytes(path.read_bytes() + b'\n')
    elif change == 'canonical-authorization':
        path = f.directory / 'authorization.json'
        value = json.loads(path.read_bytes())
        value['sha256'] = '0' * 64
        raw = protocol._cycle_wire_bytes(value)
        path.write_bytes(raw)
        operation.payload['snapshot']['authorization_ref'] = protocol._cycle_reference(raw)
    elif change == 'clock':
        operation.payload['snapshot']['budget']['clock']['boottime_ns'] += 1
    elif change == 'policy':
        operation.payload['snapshot']['budget']['policy']['control_timeout_seconds'] += 1
    elif change == 'count':
        operation.payload['snapshot']['candidate_count'] = 1
    else:
        operation.payload['identity']['ordinal'] = 2
    with pytest.raises((ValueError, OSError)):
        protocol._cycle_cpu_frame(operation.payload, 'parent', capture=True)
    assert not operation.output.exists() and not f.calls


def test_cycle_reference_public_admission_rejects_impossible_root_before_clock_and_recovers_original(
        capacity_reference_case, monkeypatch):
    from contextlib import contextmanager
    import ergora.training.cycles as cycles
    import ergora.training.execution_protocol as protocol
    from ergora.runtime import budget_clock
    f = capacity_reference_case(oversized=True)
    source = f.directory.parent / 'source'
    source.mkdir()
    (source / 'cycle.json').write_bytes(f.raw_plan)
    original_origin, original_controller, original_authorization = cycles._origin, cycles._controller, cycles._authorization
    order = []
    for name in ('_origin', '_controller', '_authorization'):
        monkeypatch.setattr(cycles, name, lambda *args, _name=name, **kwargs: pytest.fail('Preclock structural refusal reached ' + _name))
    monkeypatch.setattr(cycles.getpass, 'getuser', lambda: pytest.fail('Preclock structural refusal sampled actor'))
    with pytest.raises(protocol._CycleCapacityError):
        cycles.authorize_controller(f.state, f.project['id'], 'impossible', source,
            f.authorization['input_sha256'], 1, confirm=True, execute_selected=True)
    assert not (f.directory.parent / 'impossible').exists() and not f.calls
    assert (f.directory.parent / '.impossible.lock').read_bytes() == b''
    # Occupied IDs retain their original raw records/clock even when new admission
    # would now fail. No preclock capacity pass or new clock is used in recovery.
    monkeypatch.setattr(cycles, '_origin', original_origin)
    monkeypatch.setattr(cycles, '_controller', original_controller)
    monkeypatch.setattr(cycles, '_authorization', original_authorization)
    monkeypatch.setattr(protocol, 'admit_cycle_capacity', lambda *args: pytest.fail('Existing ID cannot be readmitted'))
    monkeypatch.setattr(cycles, '_status', lambda state, plan, authorization, ready: {
        'status': 'unknown', 'authorization': authorization})
    before = {path: path.read_bytes() for path in f.directory.iterdir()}
    recovered = cycles.authorize_controller(f.state, f.project['id'], f.authorization['cycle_id'], source,
        f.authorization['input_sha256'], 1, confirm=True, execute_selected=True)
    assert recovered['authorization'] == f.authorization
    assert {path: path.read_bytes() for path in f.directory.iterdir()} == before and not f.calls


def test_cycle_reference_public_first_publication_uses_one_clock_before_later_checks(
        capacity_reference_case, monkeypatch):
    from ergora.runtime import budget_clock
    import ergora.training.cycles as cycles
    import ergora.training.execution_protocol as protocol
    f = capacity_reference_case(count=2)
    source = f.directory.parent / 'source'
    source.mkdir()
    (source / 'cycle.json').write_bytes(f.raw_plan)
    order = []
    admit, origin, controller, authorization = protocol.admit_cycle_capacity, cycles._origin, cycles._controller, cycles._authorization
    def capacity(*args):
        order.append('capacity')
        return admit(*args)
    def original_origin(*args, **kwargs):
        order.append('origin')
        return origin(*args, **kwargs)
    def original_controller(*args, **kwargs):
        order.append('controller')
        return controller(*args, **kwargs)
    def original_authorization(*args, **kwargs):
        order.append('authorization')
        return authorization(*args, **kwargs)
    def clock(seconds):
        order.append('clock')
        assert seconds == f.plan['definition']['budget']['wall_seconds']
        return deepcopy(f.clock)
    def actor():
        order.append('actor')
        return 'capacity'
    monkeypatch.setattr(protocol, 'admit_cycle_capacity', capacity)
    monkeypatch.setattr(cycles, '_origin', original_origin)
    monkeypatch.setattr(cycles, '_controller', original_controller)
    monkeypatch.setattr(cycles, '_authorization', original_authorization)
    monkeypatch.setattr(cycles.getpass, 'getuser', actor)
    monkeypatch.setattr(budget_clock, 'authorize', clock)
    monkeypatch.setattr(cycles, '_status', lambda state, plan, authorization, ready: {
        'status': 'unknown', 'authorization': authorization})
    observed = cycles.authorize_controller(f.state, f.project['id'], 'first-publication', source,
        f.authorization['input_sha256'], 1, confirm=True, execute_selected=True)
    assert order[:4] == ['capacity', 'origin', 'clock', 'actor']
    assert order.count('clock') == order.count('capacity') == 1 and order.count('actor') == 2
    assert all(index > order.index('clock') for index, name in enumerate(order) if name == 'actor')
    assert order.index('authorization') > order.index('clock')
    destination = f.directory.parent / 'first-publication'
    loaded = cycles._load(f.state.root, f.project['id'], 'first-publication', destination)[1]
    assert observed['authorization'] == loaded and loaded['clock'] == f.clock
    before = {p: p.read_bytes() for p in destination.iterdir()}
    order.clear()
    source.rename(source.with_name('external-source-unavailable'))
    again = cycles.authorize_controller(f.state, f.project['id'], 'first-publication', source,
        f.authorization['input_sha256'], 1, confirm=True, execute_selected=True)
    assert again == observed and not {'clock', 'capacity', 'actor'}.intersection(order)
    assert {p: p.read_bytes() for p in destination.iterdir()} == before and not f.calls


def test_cycle_reference_missing_sources_refuse_new_root_and_preserve_owned_cleanup(
        capacity_reference_case, monkeypatch):
    import asyncio
    from concurrent.futures import Future
    from types import SimpleNamespace
    import ergora.training.execution_protocol as protocol
    import ergora.training.runtime.worker as worker
    import ergora.training.runtime.budget as budgets
    f = capacity_reference_case(count=2)
    controller = {'protocol': f.original['protocol'], 'workflow_id': f.authorization['controller']['workflow_id'],
        'run_id': 'capacity-run', 'intent_sha256': protocol.CycleAdmission._sha(f.admission.intent_record()),
        'ordinal': 0, 'predecessor': None}
    candidate = worker._CycleCandidate(f.state.root, f.project['id'], f.authorization['cycle_id'],
        f.authorization['sha256'], snapshot=f.snapshot, controller=controller)
    preparation = candidate.preparation
    request = {'protocol': 'ergora-training-cycle-root-v1', 'origin_operation_id': preparation.identity['operation_id'],
        'parent': preparation.identity['parent'], 'window': preparation.payload['bootstrap'],
        'submission': {'project': f.project, 'control_home': str(f.state.root),
            'experiment_id': f.plan['definition']['candidates'][0]['experiment_id'], 'timeout': 20,
            'intent_sha256': '1' * 64, 'mode': 'controller-owner'}}
    preparation.output.mkdir(parents=True)
    (preparation.output / 'request.json').write_bytes(preparation.encoded)
    (f.directory / 'authorization.json').unlink()
    with pytest.raises(FileNotFoundError):
        budgets._controller_owner(request, operation_factory=lambda value: pytest.fail('Missing originals cannot construct business root'))
    (f.directory / 'authorization.json').write_bytes(protocol._cycle_wire_bytes(f.authorization) + b'\n')
    async def offered():
        return {'status': 'new_offer', 'intent_sha256': '1' * 64, 'launch': {'request': request,
            'environment': {key: 'controlled-unused' for key in ('PYTHONPATH', 'AGENTFLOW_CONFIG_DIR', 'AGENTFLOW_STATE_DIR')}}}
    monkeypatch.setattr(preparation, 'run', offered)
    result = asyncio.run(candidate.run())
    assert result['status'] == 'unknown' and candidate.root is None and candidate.spawning.done()
    assert isinstance(candidate.spawning.exception(), ValueError)
    # Already-held cleanup uses its exact handle and captured identity. It does
    # not depend on recovering the now-missing authority or creating another root.
    events, states = [], iter((None, None, 0, 0))
    pipe = SimpleNamespace(closed=False)
    def close():
        pipe.closed = True
        events.append('close')
    pipe.close = close
    held = SimpleNamespace(pid=f.parent['pid'], stdin=pipe, poll=lambda: next(states), wait=lambda: events.append('wait'))
    future = Future()
    future.set_result(held)
    candidate.spawning, candidate.root_identity = future, f.parent
    monkeypatch.setattr(protocol, 'resolve_cycle_snapshot', lambda *args: pytest.fail('Owned cleanup must not resolve sources'))
    monkeypatch.setattr(protocol.processes, 'notify_identity', lambda identity, sig: events.append(('notify', identity)))
    asyncio.run(candidate.discard_root())
    assert events == ['close', ('notify', f.parent), 'wait'] and not f.calls


def test_cycle_reference_structural_projection_does_not_reject_fitting_complete_root_boundary(
        capacity_reference_case):
    import ergora.training.execution_protocol as protocol
    f = capacity_reference_case(count=2)
    plan = deepcopy(f.plan)
    controller = {'protocol': f.original['protocol'], 'workflow_id': f.authorization['controller']['workflow_id'],
        'run_id': 'capacity-run', 'intent_sha256': protocol.CycleAdmission._sha(f.admission.intent_record()),
        'ordinal': 0, 'predecessor': None}
    operation = protocol._CycleOperation(f.state.root, f.project['id'], f.authorization['cycle_id'],
        f.authorization['sha256'], 'prepare-candidate', snapshot=f.snapshot, ordinal=0,
        start_context={'controller': controller})
    execution = f.authorization['execution']
    installation = Path(execution['installation'])
    launch = {'request': {'protocol': 'ergora-training-cycle-root-v1',
        'origin_operation_id': operation.identity['operation_id'], 'parent': operation.identity['parent'],
        'window': operation.payload['bootstrap'], 'submission': {'project': plan['project'],
            'control_home': str(f.state.root), 'experiment_id': plan['definition']['candidates'][0]['experiment_id'],
            'timeout': 20, 'intent_sha256': '1' * 64, 'mode': 'controller-owner'}},
        'environment': {'PYTHONPATH': os.pathsep.join(map(str, (IMPORT_ROOT, installation / 'local',
            installation / 'upstream/platform', installation / 'upstream/temporal', installation / 'upstream'))),
            'AGENTFLOW_CONFIG_DIR': execution['config_directory'], 'AGENTFLOW_STATE_DIR': execution['state_directory']}}
    frame = {**operation.identity, 'event': 'result', 'result': {'status': 'new_offer',
        'intent_sha256': '1' * 64, 'launch': launch, '_stdout_ref': {'file': 'helper/stdout.txt',
            'bytes': protocol._CYCLE_LIMIT, 'sha256': '2' * 64}}}
    padding = protocol._CYCLE_LIMIT - len(protocol._cycle_wire_bytes(frame))
    if padding % 2:
        plan['project']['created'] = '2026-01-01T00:00:00.000000+00:00'
        padding = protocol._CYCLE_LIMIT - len(protocol._cycle_wire_bytes(frame))
    assert padding % 2 == 0
    # The original registration definition and its publication projection both
    # retain this complete check argv, so each new character contributes twice.
    plan['project']['registration']['definition']['checks']['behavior'][0] += 'x' * (padding // 2)
    assert len(protocol._cycle_wire_bytes(frame)) == protocol._CYCLE_LIMIT
    assert len(json.dumps(launch, ensure_ascii=False, allow_nan=False).encode()) < protocol._CYCLE_LIMIT
    protocol.validate_cycle_root_request(launch['request'])
    projected = protocol.admit_cycle_capacity(plan, str(f.state.root), f.project['id'],
        f.authorization['cycle_id'], len(f.raw_plan))
    assert max(projected.values()) < protocol._CYCLE_LIMIT and not f.calls
