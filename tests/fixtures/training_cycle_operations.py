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
    if ((fault == 'post-stopped' and mode in ('inspect', 'prepare-controller', 'prepare-candidate'))
            or (fault == 'post-stopped-confirm' and mode == 'confirm-candidate')):
        read = training_cycles._read_bytes

        def blocked_result(path, limit):
            if path.name == 'stdout.txt':
                mark('stopped-result-reader')
                time.sleep(60)
            return read(path, limit)

        training_cycles._read_bytes = blocked_result
else:
    if mode in protocol.CYCLE_CANDIDATE_MODES and os.environ.get('ERGORA_TEST_TRAINING_SERVICE'):
        mark('candidate-helper-entered')
        sys.path[:0] = [str(Path(payload['snapshot']['authorization']['execution']['installation']) / part)
                       for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
        sys.path.insert(0, str(Path(__file__).parent))
        selected = payload['snapshot']['candidates'][payload['identity']['ordinal']]
        sys.stdin = io.StringIO(json.dumps({'project': worker.State(Path(payload['identity']['control_home'])).project(
            payload['identity']['project']), 'control_home': payload['identity']['control_home'],
            'experiment_id': selected['experiment_id'], 'operation': 'dispatch',
            'timeout': payload['snapshot']['policy']['control_timeout_seconds']}))
        import training_submission_client
        sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding='utf-8')
        mark('candidate-service-installed')
        if fault == 'candidate-confirm' and mode == 'confirm-candidate':
            mark('candidate-confirm')
            time.sleep(60)
        if fault == 'candidate-lookup' and mode == 'dispatch-candidate':
            describe = training_submission_client.Service.describe_workflow_execution

            async def held_lookup(self, request, **kwargs):
                if request.execution.workflow_id.startswith('perf-experiment/'):
                    mark('candidate-lookup')
                    await worker.asyncio.sleep(60)
                return await describe(self, request, **kwargs)

            training_submission_client.Service.describe_workflow_execution = held_lookup
        if fault == 'candidate-owner-deadline-drift' and mode == 'dispatch-candidate':
            from ergora import budget_clock

            owner_record = worker.BudgetedStart.owner_record

            def owner_after_deadline(budget):
                owner = owner_record(budget)
                if (sys._getframe(1).f_code.co_name == 'dispatch_remaining'
                        and budget.operation.path('.attempt.json').exists()):
                    clock = budget_clock._clock
                    deadline = payload['bootstrap']['deadline_ns']
                    budget_clock._clock = lambda: (clock()[0], max(clock()[1], deadline + 1))
                    mark(fault)
                return owner

            worker.BudgetedStart.owner_record = owner_after_deadline
        if fault in ('candidate-window-drift', 'candidate-owner-drift', 'candidate-activity-context-drift') and mode == 'dispatch-candidate':
            synchronize = training_cycles._sync_directory

            def drift_after_attempt(directory):
                synchronize(directory)
                if (directory / (selected['experiment_id'] + '.attempt.json')).exists():
                    if fault in ('candidate-window-drift', 'candidate-activity-context-drift'):
                        target = (Path(payload['identity']['control_home']) / 'operations/training-cycles'
                                  / payload['start_context']['origin_operation_id'] / 'request.json')
                        value = json.loads(target.read_bytes())
                        if fault == 'candidate-window-drift':
                            value['bootstrap']['deadline_ns'] -= 1
                        else:
                            value['activity_context']['activity_source']['activity_id'] = 'foreign-source'
                    else:
                        target = directory / (selected['experiment_id'] + '.budget/owner.json')
                        value = json.loads(target.read_bytes())
                        value['context_sha256'] = '0' * 64
                    target.write_text(json.dumps(value))
                    mark(fault)

            training_cycles._sync_directory = drift_after_attempt
    if os.environ.get('ERGORA_TEST_CYCLE_DISPATCH') and mode in ('submit-controller', 'reconcile-controller', 'inspect-controller-activity'):
        authorization = payload['snapshot']['authorization'] if payload['snapshot'] else json.loads((
            Path(payload['identity']['control_home']) / 'training-cycles' / payload['identity']['project']
            / payload['identity']['cycle_id'] / 'authorization.json').read_bytes())
        sys.path[:0] = [str(Path(authorization['execution']['installation']) / part)
                       for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
        sys.path.insert(0, str(Path(__file__).parent))
        from perf_temporal import connection
        from temporalio.client import Client
        from training_controller_service import DispatchService

        selected = json.loads(os.environ.get('ERGORA_TEST_CYCLE_DISPATCH_CASES', '{}'))

        async def connect():
            return Client(DispatchService(payload, selected.get(payload['identity']['operation_id'], fault)),
                          namespace='foreign' if fault == 'namespace' else 'default')

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
