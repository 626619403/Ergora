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
from concurrent.futures import ThreadPoolExecutor

fault = os.environ.get('ERGORA_TEST_TRAINING_BUDGET')
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
            time.sleep(60)
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
        own = budget.BudgetedStart.own
        def with_peer(active, mode, context, **kwargs):
            if mode != 'monitor':
                return supervise(active, mode, context, **kwargs)
            active.test_pool = ThreadPoolExecutor(max_workers=1)
            active.test_peer = active.test_pool.submit(budget._BudgetPhase(active, 'cleanup', context, phase_id=peer_id).run)
            until = time.monotonic() + 6
            while not peer_marker.exists() and time.monotonic() < until:
                time.sleep(.02)
            result = supervise(active, mode, context, **kwargs)
            subreaper = ctypes.c_int()
            if ctypes.CDLL(None).prctl(37, ctypes.byref(subreaper), 0, 0, 0) != 0:
                raise OSError('Cannot inspect test owner subreaper state')
            base.storage.with_suffix('.isolation').write_text(json.dumps({
                'owner_subreaper': subreaper.value, 'peer_survived_monitor': not active.test_peer.done()}))
            return result
        def finish_peer(active):
            try:
                return own(active)
            finally:
                if hasattr(active, 'test_peer'):
                    from contextlib import suppress
                    with suppress(OSError, ValueError):
                        identity = json.loads(peer_marker.read_bytes())['supervisor']
                        if budget._process_identity(identity['pid']) == identity:
                            os.kill(identity['pid'], signal.SIGTERM)
                    active.test_peer.result(timeout=10)
                    active.test_pool.shutdown()
        budget.BudgetedStart.supervise = with_peer
        budget.BudgetedStart.own = finish_peer

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
