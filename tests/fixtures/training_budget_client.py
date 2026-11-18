"""Keep real detached budget owners/helpers; reuse the existing SDK service double."""

import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

fault = os.environ.get('ERGORA_TEST_TRAINING_BUDGET')
light_root = globals().get('light_root', False)

# The controlled blocked observation does not need the SDK service double.
# Keep the original helper authentication and its real S-owned process lifetime.
if fault == 'monitor-blocked' and not light_root:
    blocked_payload = json.load(sys.stdin)
    sys.stdin = io.StringIO(json.dumps(blocked_payload))
    if blocked_payload.get('mode') == 'monitor':
        from ergora import reference_training_budget as budget
        from ergora.reference_training_submission import _Submission

        context = blocked_payload['cached']
        operation = _Submission(blocked_payload)
        if operation.sha(context['intent']) != blocked_payload['intent_sha256']:
            raise ValueError('Controlled observer differs from the original training intent')
        active = budget.BudgetedStart(operation, context['intent'])
        active.validate_cached(context)
        Path(os.environ['ERGORA_TEST_TRAINING_SERVICE']).with_suffix('.monitor-blocked').write_text(
            json.dumps(budget._process_identity(os.getpid())))
        time.sleep(60)
        raise AssertionError('Controlled observation was not stopped within the original deadline')


def install_root_faults(budget, envelope):
    if fault in ('owner-before-publish', 'owner-initialization-held'):
        from ergora import training_execution_protocol as protocol
        from ergora.training_materials import decode_record

        markers = Path(os.environ['ERGORA_TEST_CYCLE_MARKERS'])
        source = decode_record(protocol.read_raw(Path(envelope['submission']['control_home']) / 'operations/training-cycles'
            / envelope['origin_operation_id'] / 'request.json', 32768))
        record_owner = budget.training_cycles._record

        def hold_publication():
            pending = markers / ('owner-held-' + str(os.getpid()) + '.pending')
            pending.write_text(json.dumps({'root': budget._process_identity(os.getpid()), 'fault': fault,
                'entry': 'cycle_root_main' if light_root else 'budget_main', 'imports': [name for name in sys.modules
                    if name == 'ergora.reference_training_worker' or name.startswith('temporalio')]}))
            pending.replace(markers / 'owner-held')
            while not (markers / 'owner-release').exists():
                if protocol.cycle_operation_remaining(source) <= 0:
                    raise ValueError('Injected owner initialization exhausted its original window')
                time.sleep(.02)

        def delayed_owner(path, value, **kwargs):
            if path.name == 'owner.json' and fault == 'owner-before-publish':
                hold_publication()
            result = record_owner(path, value, **kwargs)
            if path.name == 'owner.json' and fault == 'owner-initialization-held':
                hold_publication()
            return result

        budget.training_cycles._record = delayed_owner
        if os.environ.get('ERGORA_TEST_OWNER_CONFIRM_LATE_CONTEXT'):
            start_phase = budget._BudgetPhase.start
            def held_first_phase(phase):
                while not (markers / 'owner-phase-release').exists():
                    if protocol.cycle_operation_remaining(source) <= 0:
                        raise ValueError('Injected owner phase exhausted its original window')
                    time.sleep(.02)
                return start_phase(phase)
            budget._BudgetPhase.start = held_first_phase


def install_launch_fault(budget, payload):
    if fault in ('managed-no-launch', 'managed-launch-failed') and payload['mode'] in ('owner', 'controller-owner'):
        start = budget._BudgetPhase.start
        def refuse_execution(phase):
            if phase.mode == 'execute':
                marker = Path(os.environ['ERGORA_TEST_TRAINING_SERVICE']).with_suffix('.execution-launch')
                if marker.exists():
                    raise AssertionError('The consumed launch must never be offered again')
                marker.write_text(json.dumps({'phase_id': phase.identity['phase_id']}))
                if fault == 'managed-launch-failed':
                    launch = budget.subprocess.Popen
                    def failed_launch(*args, **kwargs):
                        raise OSError('Controlled execute supervisor startup failure')
                    budget.subprocess.Popen = failed_launch
                    try:
                        return start(phase)
                    finally:
                        budget.subprocess.Popen = launch
                return False
            return start(phase)
        budget._BudgetPhase.start = refuse_execution


if light_root:
    # Select the actual root entry before importing any SDK service doubles.
    from ergora import reference_training_budget as budget

    envelope = json.load(sys.stdin)
    sys.stdin = io.StringIO(json.dumps(envelope))
    install_root_faults(budget, envelope)
    install_launch_fault(budget, envelope['submission'])
    launch, start_phase = subprocess.Popen, budget._BudgetPhase.start

    def launch_phase(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.reference_training_worker import budget_main;budget_main()':
            argv = [*argv[:-1], f'import runpy;runpy.run_path({__file__!r},run_name="__main__")']
        return launch(argv, *args, **kwargs)

    def checked_phase(phase):
        assert not any(name == 'ergora.reference_training_worker' or name.startswith('temporalio') for name in sys.modules)
        return start_phase(phase)

    subprocess.Popen = launch_phase
    budget._BudgetPhase.start = checked_phase
    from ergora.reference_training_submission import cycle_root_main

    cycle_root_main()
    raise SystemExit(0)

sys.path.insert(0, str(Path(__file__).parent))
import training_submission_client as base
import training_cancellation_client

from ergora.reference_training_worker import budget_main
from ergora import reference_training_budget as budget

if (os.environ.get('ERGORA_TEST_TRAINING_CONTROLLER_PAUSE') in ('attempt', 'ack', 'executor-lock')
        and base.payload['mode'] == 'phase-supervisor' and base.payload['phase']['mode'] == 'execute'):
    from ergora import reference

    worker_command = reference.worker_command
    def paused_native_command(installation, **kwargs):
        command = worker_command(installation, **kwargs)
        if os.environ.get('ERGORA_TEST_NATIVE_PACKAGE'):
            command[-1] = command[-1].replace(repr(str(Path(reference.__file__).parent.parent)),
                                            repr(os.environ['ERGORA_TEST_NATIVE_PACKAGE']))
        fixture = str(Path(__file__).with_name('training_controller_pause.py'))
        sdk_site = str(Path(sys.modules['temporalio'].__file__).parent.parent)
        command[-1] = command[-1].replace('import ergora;sys.path.pop(0);',
            f'import ergora;sys.path.pop(0);sys.path.append({sdk_site!r});'
            f'import runpy;runpy.run_path({fixture!r})["install"]();')
        return command
    reference.worker_command = paused_native_command

if fault == 'configuration-full' and base.payload['mode'] == 'phase-supervisor' and base.payload['phase']['mode'] == 'execute':
    from ergora import reference

    worker_command = reference.worker_command
    def configuration_native_command(installation, **kwargs):
        command = worker_command(installation, **kwargs)
        fixture = str(Path(__file__).with_name('training_configuration_native.py'))
        command[-1] = command[-1].replace('import ergora;sys.path.pop(0);',
            f'import ergora;sys.path.pop(0);import runpy;runpy.run_path({fixture!r})["install"]();')
        return command
    reference.worker_command = configuration_native_command

if os.environ.get('ERGORA_TEST_TRAINING_CONTROLLER') or fault == 'configuration-full':
    training_cancellation_client.Service.query_workflow = base.Service.query_workflow

if base.envelope.get('protocol') == 'ergora-training-cycle-root-v1':
    install_root_faults(budget, base.envelope)

if fault in ('managed-no-launch', 'managed-launch-failed'):
    training_cancellation_client.Service.query_workflow = base.Service.query_workflow
    if base.payload['mode'] == 'admission':
        from contextlib import contextmanager
        from ergora import state as state_owner

        execution_lock = state_owner.file_lock
        @contextmanager
        def observed_contention(path, **kwargs):
            try:
                with execution_lock(path, **kwargs):
                    yield
            except BlockingIOError:
                base.storage.with_suffix('.admission-contended').touch()
                raise
        state_owner.file_lock = observed_contention

install_launch_fault(budget, base.payload)

if fault in ('fence-flush-failed', 'fence-flush-blocked') and base.payload['mode'] == 'fence':
    original = budget.training_cycles._sync_directory
    def flush(directory):
        if directory.name == 'fences':
            if fault == 'fence-flush-blocked':
                time.sleep(60)
            raise OSError('Controlled fence directory fsync failure')
        return original(directory)
    budget.training_cycles._sync_directory = flush
if fault in ('final-file-blocked', 'final-directory-blocked') and base.payload['mode'] in ('owner', 'publish'):
    original = budget.os.fsync
    def fsync(descriptor):
        path = Path('/proc/self/fd/' + str(descriptor)).resolve()
        if (fault == 'final-file-blocked' and path.name.startswith('.pending-')
                and path.parent.name == 'alpha.budget' and 'executor_stop_confirmed' in json.loads(path.read_bytes())
                or fault == 'final-directory-blocked' and path.name == 'alpha.budget' and (path / 'final.json').exists()):
            base.storage.with_suffix('.final-blocked').write_text(fault)
            time.sleep(60)
        return original(descriptor)
    budget.os.fsync = fsync

if fault in ('phase-isolation', 'phase-reap-overrun'):
    peer_id = 'e' * 32
    peer_marker = base.storage.with_suffix('.peer')
    if base.payload['mode'] == 'cleanup' and base.payload.get('phase', {}).get('phase_id') == peer_id:
        import ergora.reference_training_worker as worker
        async def peer_cleanup(active, context):
            active.validate_cached(context)
            peer_marker.write_text(json.dumps({'supervisor': budget._process_identity(os.getppid()),
                                              'helper': budget._process_identity(os.getpid())}))
            def blocked_sync(descriptor):
                base.storage.with_suffix('.peer-blocked-sync').write_text(str(descriptor))
                time.sleep(60)
            budget.os.fsync = blocked_sync
            with base.storage.with_suffix('.peer-output').open('xb') as output:
                output.write(b'peer phase storage')
                output.flush()
                budget.os.fsync(output.fileno())
        worker._cleanup = peer_cleanup
    if base.payload['mode'] == 'monitor':
        completion = budget.BudgetedStart.completion
        async def with_descendant(active, adapter, *, timeout=20):
            marker = base.storage.with_suffix('.descendant')
            if not marker.exists():
                child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'], start_new_session=True)
                marker.write_text(json.dumps(budget._process_identity(child.pid)))
            return await completion(active, adapter, timeout=timeout)
        budget.BudgetedStart.completion = with_descendant
    if fault == 'phase-isolation' and base.payload['mode'] == 'owner':
        from ergora import reference_training_execution

        drive = reference_training_execution.Execution.drive
        def with_peer(execution, context, phase_type):
            active = execution.budget
            original_path = active.path
            def parent_path(name):
                if name.startswith('observations/'):
                    raise AssertionError('A live parent must not validate phase storage paths')
                return original_path(name)
            active.path = parent_path
            peer = phase_type(active, 'cleanup', context, phase_id=peer_id)
            poll, finish = phase_type.poll, phase_type.finish
            def poll_with_peer(phase, *args, **kwargs):
                if phase is not peer and not peer.done:
                    poll(peer)
                return poll(phase, *args, **kwargs)
            def finish_with_peer(phase):
                result = finish(phase)
                if phase.mode == 'monitor':
                    subreaper = ctypes.c_int()
                    if ctypes.CDLL(None).prctl(37, ctypes.byref(subreaper), 0, 0, 0) != 0:
                        raise OSError('Cannot inspect test owner subreaper state')
                    base.storage.with_suffix('.isolation').write_text(json.dumps({
                        'owner_subreaper': subreaper.value, 'peer_survived_monitor': not peer.done}))
                return result
            try:
                assert peer.start()
                until = time.monotonic() + 6
                marker = base.storage.with_suffix('.peer-blocked-sync')
                while not marker.exists() and time.monotonic() < until:
                    poll(peer)
                    time.sleep(.02)
                assert marker.exists(), 'Peer did not reach its controlled fsync'
                phase_type.poll, phase_type.finish = poll_with_peer, finish_with_peer
                return drive(execution, context, phase_type)
            finally:
                phase_type.poll, phase_type.finish = poll, finish
                if peer.process is not None:
                    peer.request_stop()
                    while not peer.done:
                        poll(peer)
                        time.sleep(.02)
                    finish(peer)
                active.path = original_path
        reference_training_execution.Execution.drive = with_peer

if fault == 'phase-reap-overrun' and base.payload['mode'] == 'phase-supervisor' and base.payload['phase']['mode'] == 'monitor':
    reap = budget.processes._reap_children
    context = base.payload['cached']
    def delayed_reap():
        base.storage.with_suffix('.reap-started').write_text(json.dumps(budget._process_identity(os.getpid())))
        while budget.BudgetedStart.remaining(context, cleanup=True) > -.5:
            time.sleep(.05)
        reap()
        base.storage.with_suffix('.reap-finished').write_text(json.dumps({
            'remaining_seconds': budget.BudgetedStart.remaining(context, cleanup=True)}))
    budget.processes._reap_children = delayed_reap

if fault in ('phase-slow-reader', 'phase-held-reader'):
    if base.payload['mode'] == 'owner':
        context = budget.BudgetedStart.context
        def large_context(active):
            return {**context(active), 'transfer_probe': '训练场景' * 65_536}
        budget.BudgetedStart.context = large_context
    if base.payload['mode'] == 'phase-supervisor' and base.payload['phase']['mode'] == 'monitor':
        probe = base.payload['cached']['transfer_probe'].encode('utf-8')
        base.storage.with_suffix('.complete-input').write_text(json.dumps({
            'bytes': len(probe), 'sha256': hashlib.sha256(probe).hexdigest()}))

if fault == 'phase-result-blocked' and base.payload['mode'] == 'phase-supervisor' and base.payload['phase']['mode'] == 'fence':
    document = budget.training_cycles._document
    def blocked_result(path):
        if path.name == 'stdout.txt' and path.parent.name == 'helper':
            base.storage.with_suffix('.result-blocked').write_text(json.dumps(budget._process_identity(os.getpid())))
            time.sleep(60)
        return document(path)
    budget.training_cycles._document = blocked_result

if fault == 'phase-supervisor-killed' and base.payload['mode'] == 'monitor':
    completion = budget.BudgetedStart.completion
    async def kill_supervisor(active, adapter, *, timeout=20):
        marker = base.storage.with_suffix('.killed-supervisor')
        if not marker.exists():
            marker.write_text(json.dumps({'supervisor': budget._process_identity(os.getppid()),
                                          'helper': budget._process_identity(os.getpid())}))
            os.kill(os.getppid(), signal.SIGKILL)
        return await completion(active, adapter, timeout=timeout)
    budget.BudgetedStart.completion = kill_supervisor

if fault == 'phase-stopped-incomplete' and base.payload['mode'] == 'phase-supervisor' and base.payload['phase']['mode'] == 'monitor':
    run = budget.processes.run
    def incomplete_process(*args, **kwargs):
        run(*args, **kwargs)
        base.storage.with_suffix('.incomplete-stopped').write_text(json.dumps(budget._process_identity(os.getpid())))
        return {}
    budget.processes.run = incomplete_process

base.payload['request_id'] = 'budget-' + base.payload['intent_sha256'][:32]
sys.stdin = base.io.StringIO(json.dumps(base.envelope if base.envelope.get('protocol') == 'ergora-training-cycle-root-v1'
                                       else base.payload))
base.install_budget_fixture()
if fault in ('phase-slow-reader', 'phase-held-reader') and base.payload['mode'] == 'owner':
    start_phase = budget._BudgetPhase.start
    launch = subprocess.Popen
    transferring_monitor = False
    def transfer(phase):
        global transferring_monitor
        transferring_monitor = phase.mode == 'monitor'
        try:
            return start_phase(phase)
        finally:
            transferring_monitor = False
    def delayed_reader(argv, *args, **kwargs):
        selected = transferring_monitor and 'from ergora.reference_training_worker import budget_main;budget_main()' in argv
        if selected:
            delay = .25 if fault == 'phase-slow-reader' else 60
            argv = [*argv[:-1], f'import time,runpy;time.sleep({delay});runpy.run_path({__file__!r},run_name="__main__")']
        process = launch(argv, *args, **kwargs)
        if selected:
            base.storage.with_suffix('.reader-delayed').write_text(json.dumps(budget._process_identity(process.pid)))
        return process
    budget._BudgetPhase.start = transfer
    subprocess.Popen = delayed_reader
budget_main()
