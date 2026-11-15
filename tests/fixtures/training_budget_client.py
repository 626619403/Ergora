"""Keep real detached budget owners/helpers; reuse the existing SDK service double."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import training_submission_client as base
import training_cancellation_client

from ergora.reference_training_worker import budget_main
from ergora import reference_training_budget as budget
import os
import time
import ctypes
import hashlib
import signal
import subprocess

fault = os.environ.get('ERGORA_TEST_TRAINING_BUDGET')
if (os.environ.get('ERGORA_TEST_TRAINING_CONTROLLER_PAUSE') in ('attempt', 'ack', 'executor-lock')
        and base.payload['mode'] == 'phase-supervisor' and base.payload['phase']['mode'] == 'execute'):
    from ergora import reference

    worker_command = reference.worker_command
    def paused_native_command(installation, **kwargs):
        command = worker_command(installation, **kwargs)
        fixture = str(Path(__file__).with_name('training_controller_pause.py'))
        sdk_site = str(Path(sys.modules['temporalio'].__file__).parent.parent)
        command[-1] = command[-1].replace('import ergora;sys.path.pop(0);',
            f'import ergora;sys.path.pop(0);sys.path.append({sdk_site!r});'
            f'import runpy;runpy.run_path({fixture!r})["install"]();')
        return command
    reference.worker_command = paused_native_command

if os.environ.get('ERGORA_TEST_TRAINING_CONTROLLER'):
    training_cancellation_client.Service.query_workflow = base.Service.query_workflow

if fault == 'legacy-owner-schema1' and base.payload['mode'] == 'owner':
    record_owner = budget.training_cycles._record
    def legacy_owner(path, value, **kwargs):
        if path.name == 'owner.json':
            value = {key: item for key, item in value.items() if key != 'execution_capability'}
            value['schema_version'] = 1
        return record_owner(path, value, **kwargs)
    budget.training_cycles._record = legacy_owner

if fault in ('managed-no-launch', 'managed-launch-failed'):
    training_cancellation_client.Service.query_workflow = base.Service.query_workflow
    if base.payload['mode'] == 'admission':
        from contextlib import contextmanager
        from ergora import reference_training_execution

        execution_lock = reference_training_execution.file_lock
        @contextmanager
        def observed_contention(path, **kwargs):
            try:
                with execution_lock(path, **kwargs):
                    yield
            except BlockingIOError:
                base.storage.with_suffix('.admission-contended').touch()
                raise
        reference_training_execution.file_lock = observed_contention

if fault in ('managed-no-launch', 'managed-launch-failed') and base.payload['mode'] == 'owner':
    start = budget._BudgetPhase.start
    def refuse_execution(phase):
        if phase.mode == 'execute':
            marker = base.storage.with_suffix('.execution-launch')
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

if fault == 'monitor-blocked' and base.payload['mode'] == 'monitor':
    async def blocked(_self):
        time.sleep(60)
    budget.BudgetedStart.completion = blocked
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
        async def with_descendant(active):
            marker = base.storage.with_suffix('.descendant')
            if not marker.exists():
                child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'], start_new_session=True)
                marker.write_text(json.dumps(budget._process_identity(child.pid)))
            return await completion(active)
        budget.BudgetedStart.completion = with_descendant
    if fault == 'phase-isolation' and base.payload['mode'] == 'owner':
        supervise = budget.BudgetedStart.supervise
        def with_peer(active, mode, context, **kwargs):
            if mode != 'monitor':
                return supervise(active, mode, context, **kwargs)
            original_path = active.path
            def parent_path(name):
                if name.startswith('observations/'):
                    raise AssertionError('A live parent must not validate phase storage paths')
                return original_path(name)
            active.path = parent_path
            phases = []
            try:
                peer = budget._BudgetPhase(active, 'cleanup', context, phase_id=peer_id)
                assert peer.start()
                phases.append(peer)
                until = time.monotonic() + 6
                marker = base.storage.with_suffix('.peer-blocked-sync')
                while not marker.exists() and time.monotonic() < until:
                    peer.poll()
                    time.sleep(.02)
                assert marker.exists(), 'Peer did not reach its controlled fsync'
                monitor = budget._BudgetPhase(active, mode, context)
                assert monitor.start()
                phases.append(monitor)
                while not monitor.done:
                    for phase in phases:
                        if not phase.done:
                            phase.poll()
                    time.sleep(.02)
                result = monitor.finish()
                phases.remove(monitor)
                subreaper = ctypes.c_int()
                if ctypes.CDLL(None).prctl(37, ctypes.byref(subreaper), 0, 0, 0) != 0:
                    raise OSError('Cannot inspect test owner subreaper state')
                base.storage.with_suffix('.isolation').write_text(json.dumps({
                    'owner_subreaper': subreaper.value, 'peer_survived_monitor': not peer.done}))
                return result
            finally:
                for phase in phases:
                    phase.request_stop()
                while any(not phase.done for phase in phases):
                    for phase in phases:
                        if not phase.done:
                            phase.poll()
                    time.sleep(.02)
                for phase in phases:
                    phase.finish()
                active.path = original_path
        budget.BudgetedStart.supervise = with_peer

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
    async def kill_supervisor(active):
        marker = base.storage.with_suffix('.killed-supervisor')
        if not marker.exists():
            marker.write_text(json.dumps({'supervisor': budget._process_identity(os.getppid()),
                                          'helper': budget._process_identity(os.getpid())}))
            os.kill(os.getppid(), signal.SIGKILL)
        return await completion(active)
    budget.BudgetedStart.completion = kill_supervisor

if fault == 'phase-stopped-incomplete' and base.payload['mode'] == 'phase-supervisor' and base.payload['phase']['mode'] == 'monitor':
    run = budget.processes.run
    def incomplete_process(*args, **kwargs):
        run(*args, **kwargs)
        base.storage.with_suffix('.incomplete-stopped').write_text(json.dumps(budget._process_identity(os.getpid())))
        return {}
    budget.processes.run = incomplete_process

base.payload['request_id'] = 'budget-' + base.payload['intent_sha256'][:32]
sys.stdin = base.io.StringIO(json.dumps(base.payload))
base.install_budget_fixture()
if fault in ('phase-slow-reader', 'phase-held-reader') and base.payload['mode'] == 'owner':
    supervise = budget.BudgetedStart.supervise
    launch = subprocess.Popen
    transferring_monitor = False
    def transfer(active, mode, context, **kwargs):
        global transferring_monitor
        transferring_monitor = mode == 'monitor'
        try:
            return supervise(active, mode, context, **kwargs)
        finally:
            transferring_monitor = False
    def delayed_reader(argv, *args, **kwargs):
        if transferring_monitor and 'from ergora.reference_training_worker import budget_main;budget_main()' in argv:
            delay = .25 if fault == 'phase-slow-reader' else 60
            argv = [*argv[:-1], f'import time,runpy;time.sleep({delay});runpy.run_path({__file__!r},run_name="__main__")']
        return launch(argv, *args, **kwargs)
    budget.BudgetedStart.supervise = transfer
    subprocess.Popen = delayed_reader
budget_main()
