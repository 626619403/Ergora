"""Controller admission, recovery, and independent candidate root lifecycles."""

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

from ergora import reference, training
from test_training_submission import (
    controller_admission, controller_dispatch, cycle_budget_root, cycle_candidate, cycle_operation_fault,
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



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_controller_birth_consent_retains_original_actor_clock_and_mode(controller_admission, monkeypatch):
    from ergora import training_cycles

    state, source, selected, authorized, admission = controller_admission
    authorization = authorized['authorization']
    assert authorized['status'] == 'ready' and authorization['schema_version'] == 2
    assert authorized['controller']['consent_recorded'] is True
    assert authorized['coverage']['execution_authorized'] is False
    controller = authorization['controller']
    assert controller['actor_id'] == f'unix:{os.getuid()}:{training_cycles.getpass.getuser()}'
    identity = {key: authorization[key] for key in ('control_home', 'project', 'cycle_id', 'input_sha256')}
    assert controller == {'protocol': 'ergora-training-cycle-v1',
        'workflow_id': 'ergora-training-cycle/' + training_cycles._sha(identity),
        'task_queue': 'ergora-training-cycle-v1', 'execution_scope': 'ordered-selected-native-once',
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
    for cycle in ('controller', 'manual'):
        with pytest.raises(ValueError, match='consent mode'):
            training_cycles.authorize_controller(state, 'demo', cycle, source, selected['sha256'], 1,
                confirm=True, execute_selected=True, program_version=2)
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



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
@pytest.mark.parametrize('program_version', [1, 2])
@pytest.mark.parametrize('boundary', ['authorization-file', 'lock-file', 'lock-directory', 'ready-directory'])
def test_controller_lock_publication_recovers_only_the_original_consent(
        cycle_selection, tmp_path, monkeypatch, boundary, program_version):
    from ergora import training_cycles

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
            confirm=True, execute_selected=True, program_version=program_version)
    assert failed
    original = {p: p.read_bytes() for p in saved.rglob('*') if p.is_file()}
    if boundary == 'authorization-file':
        assert saved.is_dir() and not (saved / 'authorization.json').exists()
        monkeypatch.setattr(os, 'fsync', fsync)
        monkeypatch.setattr(training_cycles.budget_clock, 'authorize',
            lambda *args: pytest.fail('A reserved ID cannot receive another clock'))
        with pytest.raises(FileNotFoundError):
            training_cycles.authorize_controller(state, 'demo', 'interrupted-controller', source, selected['sha256'], 1,
                confirm=True, execute_selected=True, program_version=program_version)
        assert all(p.read_bytes() == raw for p, raw in original.items())
        return
    monkeypatch.setattr(training_cycles, '_measurement_sources',
        lambda: pytest.fail('Recovery must not recapture the measurement source map'))
    monkeypatch.setattr(training_cycles.budget_clock, 'authorize',
        lambda *args: pytest.fail('Recovery must not issue another clock'))
    observed = training_cycles.status(state, 'demo', 'interrupted-controller')
    assert observed['status'] == ('unknown' if boundary == 'ready-directory' else 'pending')
    monkeypatch.setattr(os, 'fsync', fsync)
    recovered = training_cycles.authorize_controller(state, 'demo', 'interrupted-controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True, program_version=program_version)
    assert recovered['status'] == 'ready' and recovered['authorization'] == observed['authorization']
    assert (saved / 'controller/admission.lock').read_bytes() == b''
    assert all(p.read_bytes() == raw for p, raw in original.items())



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_controller_ready_never_recreates_or_accepts_a_changed_parent_lock(controller_admission, tmp_path):
    from ergora import training_cycles

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
    from ergora import budget_clock, training_cycles

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
    from ergora import training_cycles

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
    from ergora import training_cycles

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
    from ergora import training_cycles

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
    from ergora import training_cycles
    from ergora.state import file_lock

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
    from ergora import training_cycles

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
    from ergora import training_cycles
    from ergora.training_execution_protocol import CycleAdmission

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



@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Independent original roots require Linux/WSL2')
def test_cycle_candidate_root_survives_short_calls_and_normal_loop_shutdown(
        controller_admission, cycle_selection, cycle_candidate, service, monkeypatch):
    import asyncio
    from ergora import reference_training_worker as worker, training_execution_protocol as protocol

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
            from ergora import reference_training_worker as worker

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
        if argv[-1] == 'from ergora.reference_training_worker import budget_main;budget_main()':
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



@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Loop shutdown must retain the actual independent Linux root')
@pytest.mark.parametrize('boundary', ['spawn', 'confirm'])
def test_cycle_candidate_loop_shutdown_reaps_a_pending_root(
        cycle_candidate, cycle_selection, cycle_operation_fault, monkeypatch, boundary):
    import asyncio
    import threading
    from ergora import processes

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
        root = argv[-1] == 'from ergora.reference_training_worker import budget_main;budget_main()'
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
    from ergora import processes, reference_training_worker as worker

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
        return reference.training_submission(state.project('demo'), state.root, 'prepare',
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
from ergora.training_execution_protocol import CycleAdmission,decode,read_raw
directory=Path(sys.argv[2])
parent=CycleAdmission(directory,decode(read_raw(directory/'authorization.json')))
parent.bind(decode(read_raw(Path(sys.argv[3]))),decode(read_raw(directory/'cycle.json',10_000_000)))
assert not any(name in sys.modules for name in ('yaml','jsonschema','temporalio','dev_platform','ergora.state'))
print('complete original binding verified without site packages')
''', str(Path(reference.__file__).parent.parent), str(admission.directory), str(prefix / 'alpha.intent.json')],
        capture_output=True, text=True, timeout=10)
    assert isolated.returncode == 0, isolated.stderr



@pytest.mark.skipif(sys.platform != 'linux', reason='Controller dispatch uses the original Linux budget owner')
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
@pytest.mark.parametrize('case', ['not-found', 'closed', 'run', 'memo', 'type', 'queue', 'input', 'accepted'])
def test_controller_fixed_history_gates_the_one_original_start(
        controller_admission, cycle_selection, cycle_candidate, service, monkeypatch, case):
    from ergora import processes, training_cycles
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
        original = intent_path.read_bytes()
        if case != 'accepted':
            reason = ('Original controller run is not found' if case == 'not-found' else
                      'Original controller run, running state or complete intent memo differs' if case in ('closed', 'run', 'memo') else
                      'Original controller type, queue or started input' if case in ('type', 'queue') else
                      'Original controller complete started input or intent memo differs')
            assert result['status'] == 'unknown' and reason in result['reason'], result
            assert not attempt_path.exists() and not (runtime / 'training/jobs/alpha').exists()
            with pytest.raises(ValueError, match='complete original start call'):
                training.resume_start(state, 'demo', 'alpha', 1, training_cycles._sha(json.loads(original)))
        else:
            submitted = result['submission']
            assert submitted['status'] == 'submitted' and submitted['budget']['controller'] == binding['controller']
            assert attempt_path.exists() and json.loads(service[1].read_bytes())['starts'] == 1
        # A later call observes even a live owner without an attempt. It never
        # reuses the lost offer to try a corrected history or another SDK send.
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
    from ergora.state import file_lock

    state, _, _, _, admission = controller_admission
    _, definition, runtime, _, _, request = cycle_selection
    binding = save_controller_binding(admission)
    monkeypatch.setenv('ERGORA_TEST_TRAINING_CONTROLLER', str(admission.folder))
    selector = {key: value for key, value in binding.items() if key != 'task_queue'}
    marker = admission.folder / 'parent-history-observed'
    try:
        assert run_cycle_candidate(cycle_candidate)['submission']['status'] == 'submitted'
        marker.unlink()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with file_lock(runtime / 'training/registry.lock'):
                future = pool.submit(native_budget_create, definition, 'alpha', managed=True)
                until = time.monotonic() + 6
                while not marker.exists() and time.monotonic() < until:
                    time.sleep(.02)
                assert marker.exists()
                stopped = admission.request_stop('Stop while native create waits for the original registry')
                assert stopped['admission_drained'] is None and not (runtime / 'training/jobs/alpha').exists()
            created = future.result(timeout=8)
        assert created.returncode != 0 and 'Original training budget cannot start work: stopped' in created.stderr
        assert not (runtime / 'training/jobs/alpha').exists()
        assert admission.observe(drain=True)['admission_drained'] is True
    finally:
        stop_controller_test_owner(runtime)



@pytest.mark.skipif(sys.platform != 'linux', reason='Parent permits cover the original attempt directory sync')
@pytest.mark.parametrize('controller_admission', [{'control_timeout_seconds': 30}], indirect=True)
def test_controller_stop_after_attempt_sync_never_resends_the_consumed_rpc(
        controller_admission, cycle_selection, cycle_candidate, service, tmp_path, monkeypatch):
    from ergora import training_cycles

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
    from ergora import training_cycles

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
            from ergora.reference_training_runtime import lookup_controller
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
    from ergora import budget_clock

    _, admission, storage, operation = controller_dispatch
    starting = operation('lost-reply')
    first = asyncio.run(starting.run())
    assert first['status'] == 'unknown', first
    assert (admission.folder / 'attempt.json').exists() and (storage / 'request.pb').exists()
    raw = (admission.directory / 'authorization.json').read_bytes()
    clock = admission.authorization['clock']
    wall_seconds = starting.payload['snapshot']['policy']['wall_seconds']
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



@pytest.mark.parametrize('controller_admission', [{'program_version': 2}], indirect=True)
def test_schema3_birth_retains_sources_bytes_and_one_clock(controller_admission, monkeypatch):
    from ergora import training_cycles
    from ergora.training_execution_protocol import MEASUREMENT_SOURCES

    state, source, selected, authorized, admission = controller_admission
    authorization = authorized['authorization']
    assert authorization['schema_version'] == 3 and authorized['coverage']['execution_authorized'] is False
    assert set(authorization['measurement_sources']) == set(MEASUREMENT_SOURCES)
    package = Path(training_cycles.__file__).parent
    assert authorization['measurement_sources'] == {
        name: hashlib.sha256((package / name).read_bytes()).hexdigest() for name in MEASUREMENT_SOURCES}
    controller = authorization['controller']
    identity = {key: authorization[key] for key in ('control_home', 'project', 'cycle_id', 'input_sha256')}
    assert controller['protocol'] == controller['task_queue'] == 'ergora-training-cycle-v2'
    assert controller['workflow_id'] == 'ergora-training-cycle-v2/' + training_cycles._sha(identity)
    original = {p: p.read_bytes() for p in admission.directory.rglob('*') if p.is_file()}
    (source / 'cycle.json').unlink()
    source.rmdir()
    monkeypatch.setattr(training_cycles, '_measurement_sources', lambda: pytest.fail('Ready retries cannot capture sources'))
    monkeypatch.setattr(training_cycles.budget_clock, 'authorize', lambda *args: pytest.fail('Ready retries cannot renew clocks'))
    monkeypatch.setattr(training, 'check_start', lambda *args: pytest.fail('Ready retries cannot repeat admissions'))
    again = training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True, program_version=2)
    assert again['authorization'] == authorization and again['ready'] == authorized['ready']
    for mode in (None, 1):
        with pytest.raises(ValueError, match='consent mode'):
            if mode is None:
                training_cycles.authorize(state, 'demo', 'controller', source, selected['sha256'], 1, confirm=True)
            else:
                training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 1,
                    confirm=True, execute_selected=True)
    with pytest.raises(ValueError, match='different complete input'):
        training_cycles.authorize_controller(state, 'demo', 'controller', source, '0' * 64, 1,
            confirm=True, execute_selected=True, program_version=2)
    with pytest.raises(ValueError, match='revision changed'):
        training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 2,
            confirm=True, execute_selected=True, program_version=2)
    for invalid in (True, False, 1.0, '2'):
        with pytest.raises(ValueError, match='program version'):
            training_cycles.authorize_controller(state, 'demo', 'invalid', source, selected['sha256'], 1,
                confirm=True, execute_selected=True, program_version=invalid)
    assert not (admission.directory.parent / 'invalid').exists()
    assert all(p.read_bytes() == raw for p, raw in original.items())
    # Shape is checked independently of the canonical digest, even offline.
    altered = deepcopy(authorization)
    altered['measurement_sources']['arbitrary.py'] = altered['measurement_sources'].pop(MEASUREMENT_SOURCES[0])
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


@pytest.mark.parametrize('controller_admission', [{'program_version': 2}], indirect=True)
def test_schema3_intent_is_local_and_all_execution_entries_remain_closed(
        controller_admission, cycle_selection, service, monkeypatch):
    from ergora import reference_training_worker as worker, training_cycles

    state, source, selected, authorized, admission = controller_admission
    _, _, runtime, _, _, request = cycle_selection
    original_sources = training_cycles._measurement_sources()
    source_reader = training_cycles._read_bytes
    target = Path(training_cycles.__file__).parent / next(iter(original_sources))
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
    with pytest.raises(ValueError, match='execution is not enabled'):
        training_cycles._claim_controller(state, admission)
    # Cold H bypasses the schema2 snapshot validator; exercise the actual S/H
    # child path and its retained stopped/result records, without a service double.
    import asyncio
    operation = worker._CycleOperation(state.root, 'demo', 'controller', authorized['authorization_sha256'], 'inspect')
    cold = asyncio.run(operation.run())
    assert cold['status'] == 'unknown' and cold['operation_stopped'] is True
    assert 'Schema3 controller execution is not enabled' in cold['reason']
    assert operation.process.returncode is not None
    service[0]('accepted')
    digest = request['candidates'][0]['manifest_sha256']
    for cycle_entry in (True, False):
        with pytest.raises(ValueError, match='execution is not enabled'):
            if cycle_entry:
                training_cycles.start(state, 'demo', 'controller', 'alpha', authorized['authorization_sha256'], 1)
            else:
                training.start(state, 'demo', 'alpha', 1, digest,
                    budget={'cycle_id': 'controller', 'authorization_sha256': authorized['authorization_sha256']})
    assert not (admission.folder / 'attempt.json').exists() and not service[1].exists()
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
        confirm=True, execute_selected=True, program_version=2)['authorization']['measurement_sources'] == original_sources
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
    assert not (admission.folder / 'attempt.json').exists()


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('controller_admission', [{'program_version': 2}], indirect=True)
def test_schema3_native_callback_refuses_before_executor_effects_and_keeps_completed_read(
        controller_admission, request):
    from ergora import training_cycles

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
        PYTHONPATH=os.pathsep.join(map(str, (Path(training_cycles.__file__).parent.parent,
            installation / 'local', installation / 'upstream/platform', installation / 'upstream/temporal', installation / 'upstream',
            *(Path(item) for item in sys.path if 'site-packages' in item)))))
    command = [str(installation / '.venv/bin/python'), '-B', '-P',
        str(Path(__file__).parent / 'fixtures/training_executor_client.py'), 'native-context', str(folder.parent)]
    before = {path: path.read_bytes() for path in folder.parent.rglob('*') if path.is_file()}
    result = subprocess.run(command, input=json.dumps({'cached': context, 'phase': {}}), env=environment,
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {'error_type': 'ValueError', 'error': 'Schema3 controller execution is not enabled'}
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


@pytest.mark.parametrize('controller_admission', [{}, {'program_version': 2}], indirect=True)
def test_controller_original_type_is_authenticated_read_only(controller_admission, tmp_path, monkeypatch):
    import asyncio
    from temporalio.client import Client
    from ergora import training_cycles
    from ergora.reference_training_runtime import lookup_controller_submission
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
    if authorized['authorization']['schema_version'] == 3:
        sdk.case = 'v1-type'
        with pytest.raises(ValueError, match='controller type'):
            asyncio.run(lookup_controller_submission(Client(sdk), prepared['intent'], run_id=sdk.run_id, timeout=2))
    assert all(json.loads(path.read_bytes())['action'] != 'start' for path in storage.glob('call-*.json'))
    assert {path: path.read_bytes() for path in admission.directory.rglob('*') if path.is_file()} == before
    assert not (admission.folder / 'attempt.json').exists()
