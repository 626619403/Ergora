"""Faults at real cycle-operation storage boundaries; retain the original supervisor/reaper."""

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from ergora import processes, reference, training_cycles, training_execution_protocol as protocol
from ergora import reference_training_worker as worker

raw = sys.stdin.buffer.read()
payload = json.loads(raw)
sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding='utf-8')
stage, fault = sys.argv[1], os.environ['ERGORA_TEST_CYCLE_OPERATION']
markers = Path(os.environ['ERGORA_TEST_CYCLE_MARKERS'])
mode = payload['identity']['mode']


def mark(name):
    pending = markers / ('.' + name + '.pending')
    pending.write_text(json.dumps(processes.identity(os.getpid())))
    pending.replace(markers / name)


if stage == 'S':
    original_run = processes.run

    def invoke(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.reference_training_worker import cycle_operation_main;cycle_operation_main(False)':
            argv = [sys.executable, '-P', __file__, 'H']
        return original_run(argv, *args, **kwargs)

    processes.run = invoke
    if fault == 'post-stopped' and mode in ('inspect', 'prepare-controller'):
        read = training_cycles._read_bytes

        def blocked_result(path, limit):
            if path.name == 'stdout.txt':
                mark('stopped-result-reader')
                time.sleep(60)
            return read(path, limit)

        training_cycles._read_bytes = blocked_result
else:
    if os.environ.get('ERGORA_TEST_CYCLE_DISPATCH') and mode in ('submit-controller', 'reconcile-controller'):
        sys.path[:0] = [str(Path(payload['snapshot']['authorization']['execution']['installation']) / part)
                       for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
        sys.path.insert(0, str(Path(__file__).parent))
        from perf_temporal import connection
        from temporalio.client import Client
        from training_controller_service import DispatchService

        selected = json.loads(os.environ.get('ERGORA_TEST_CYCLE_DISPATCH_CASES', '{}'))

        async def connect():
            return Client(DispatchService(payload, selected.get(payload['identity']['operation_id'], fault)))

        connection.connect = connect
        mark('dispatch-helper')
        if fault == 'project-after-claim':
            validate = reference.validate_installation

            def drift_project(*args, **kwargs):
                root = validate(*args, **kwargs)
                authorization = payload['snapshot']['authorization']
                directory = Path(authorization['control_home']) / 'training-cycles' / authorization['project'] / authorization['cycle_id']
                if (directory / 'controller/attempt.json').exists():
                    state = worker.State(Path(authorization['control_home']))
                    with state.connect() as db:
                        row = db.execute('SELECT document FROM projects WHERE id=?', (authorization['project'],)).fetchone()
                        project = json.loads(row[0])
                        project['revision'] += 1
                        db.execute('UPDATE projects SET document=? WHERE id=?', (json.dumps(project), authorization['project']))
                return root

            reference.validate_installation = drift_project
        if fault == 'blocked-attempt-sync':
            synchronize = training_cycles._sync_directory

            def blocked_attempt(directory):
                if (directory / 'attempt.json').exists():
                    mark('attempt-sync')
                    time.sleep(60)
                return synchronize(directory)

            training_cycles._sync_directory = blocked_attempt
        if fault == 'stop-after-claim':
            synchronize = training_cycles._sync_directory

            def stop_claimed(directory):
                synchronize(directory)
                if (directory / 'attempt.json').exists():
                    authorization = payload['snapshot']['authorization']
                    protocol.CycleAdmission(directory.parent, authorization).request_stop('Stop after single slot publication')

            training_cycles._sync_directory = stop_claimed
    if fault == 'blocked-prepare' and mode == 'prepare-controller':
        def blocked_database(self):
            mark('prepare-database-reader')
            time.sleep(60)
            raise AssertionError('The original operation window must reap this blocked database reader')

        worker.State._open = blocked_database
    if fault == 'blocked-stop' and mode == 'stop-writer':
        fsync = os.fsync

        def blocked_sync(descriptor):
            if Path('/proc/self/fd/' + str(descriptor)).resolve().name == 'stop.json':
                mark('stop-writer')
                time.sleep(60)
            return fsync(descriptor)

        os.fsync = blocked_sync
    if fault == 'blocked-stop' and mode == 'notify-owner' and payload['identity']['ordinal'] == 0:
        read = protocol.read_raw

        def blocked_owner(path, *args, **kwargs):
            if path.name == 'owner.json' and path.parent.name == 'alpha.budget':
                mark('alpha-owner-reader')
                time.sleep(60)
            return read(path, *args, **kwargs)

        protocol.read_raw = blocked_owner
    if fault == 'blocked-stop' and mode == 'notify-owner' and payload['identity']['ordinal'] == 1:
        notify = processes.notify_identity

        def record_notification(expected, signum):
            notify(expected, signum)
            (markers / 'beta-notified').write_text(json.dumps({
                'target': expected, 'sender': processes.identity(os.getpid())}))

        processes.notify_identity = record_notification
    if fault == 'blocked-inspect' and mode == 'inspect':
        child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'], start_new_session=True)
        (markers / 'new-session-descendant').write_text(json.dumps(processes.identity(child.pid)))
        mark('inspect-helper')
        time.sleep(60)
    if fault == 'unavailable-sources':
        sys.modules['temporalio'] = None
        def unavailable(*args, **kwargs):
            raise AssertionError('Old-owner cleanup cannot require the current installation or gate sources')
        protocol.validate_sources = reference.validate_installation = unavailable

worker.cycle_operation_main(stage == 'S')
