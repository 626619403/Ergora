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


def mark(name, value=None):
    pending = markers / (name + '-' + str(os.getpid()) + '.pending')
    pending.write_text(json.dumps(processes.identity(os.getpid()) if value is None else value))
    pending.replace(markers / name)


if stage == 'S':
    original_run = processes.run

    def invoke(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.reference_training_worker import cycle_operation_main;cycle_operation_main(False)':
            argv = [sys.executable, '-P', __file__, 'H']
        return original_run(argv, *args, **kwargs)

    processes.run = invoke
    if fault == 'post-stopped' and mode == 'inspect':
        read = training_cycles._read_bytes

        def blocked_result(path, limit):
            if path.name == 'stdout.txt':
                mark('stopped-result-reader')
                time.sleep(60)
            return read(path, limit)

        training_cycles._read_bytes = blocked_result
else:
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
            # Independent H processes may reach these storage seams in any order.
            # Establish overlap before the real notification, within the original clock.
            while True:
                remaining = protocol.cycle_operation_remaining(payload)
                if remaining <= 0:
                    raise ValueError('Original cycle allowance ended before both stop branches blocked')
                if all((markers / name).is_file() for name in ('stop-writer', 'alpha-owner-reader')):
                    break
                time.sleep(min(.01, remaining))
            notify(expected, signum)
            mark('beta-notified', {'target': expected, 'sender': processes.identity(os.getpid())})

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
