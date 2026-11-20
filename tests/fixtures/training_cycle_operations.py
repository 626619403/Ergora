"""Faults at real cycle-operation storage boundaries; retain the original supervisor/reaper."""

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import ergora.native.resources as native_resources
import ergora.training.execution_protocol as protocol
from ergora.runtime import processes

stage, fault = sys.argv[1], os.environ['ERGORA_TEST_CYCLE_OPERATION']
if stage != 'S':
    import ergora.training.cycles as training_cycles
    import ergora.training.runtime.worker as worker
    import ergora.training.runtime.evidence as execution_evidence
markers = Path(os.environ['ERGORA_TEST_CYCLE_MARKERS'])


def mark(name, value=None):
    pending = markers / (name + '-' + str(os.getpid()) + '.pending')
    pending.write_text(json.dumps(processes.identity(os.getpid()) if value is None else value))
    pending.replace(markers / name)


if stage == 'D':
    # Branch before the ordinary fixture's read-all/JSON wrapper: this is the
    # real streaming entry, watchdog, fd operations and one actual S process.
    from ergora.runtime import budget_clock
    synchronize, write = os.fsync, os.write
    partial = False

    def request_fd(descriptor):
        return Path('/proc/self/fd/' + str(descriptor)).resolve().name == 'request.json'

    def retention_sync(descriptor):
        if request_fd(descriptor):
            mark('retention-sync')
            if fault in ('retention-blocked', 'retention-clock-drift'):
                if fault == 'retention-clock-drift':
                    from datetime import timedelta
                    original_datetime = budget_clock.datetime
                    class DriftedDateTime(original_datetime):
                        @classmethod
                        def now(cls, tz=None):
                            return original_datetime.now(tz) + timedelta(seconds=10)
                    budget_clock.datetime = DriftedDateTime
                time.sleep(60)
            if fault == 'retention-fsync':
                raise OSError('Injected request synchronization failure')
            if fault in ('retention-replace', 'retention-corrupt'):
                path = Path('/proc/self/fd/' + str(descriptor)).resolve()
                if fault == 'retention-replace':
                    replacement = path.with_name('replacement')
                    replacement.write_bytes(path.read_bytes())
                    replacement.replace(path)
                else:
                    with path.open('r+b') as stream:
                        stream.write(b'!')
        return synchronize(descriptor)

    def retention_write(descriptor, raw):
        global partial
        if fault == 'retention-blocked-write' and request_fd(descriptor):
            mark('retention-write')
            time.sleep(60)
        if fault == 'retention-partial' and request_fd(descriptor):
            if partial:
                raise OSError('Injected disk write failure after a short write')
            partial = True
            return write(descriptor, raw[:17])
        return write(descriptor, raw)

    class Confirmation:
        def write(self, raw):
            mark('retention-confirmation', {'bytes': len(raw) - 1})
            if fault == 'retention-reply-loss':
                return len(raw)
            if fault in ('retention-confirm-sha', 'retention-confirm-identity', 'retention-confirm-ordinal', 'retention-confirm-parent-pid', 'retention-confirm-extra'):
                value = json.loads(raw)
                if fault == 'retention-confirm-sha':
                    value['ref']['sha256'] = '0' * 64
                elif fault == 'retention-confirm-identity':
                    value['identity']['parent']['start_ticks'] += '0'
                elif fault == 'retention-confirm-ordinal':
                    value['identity']['ordinal'] = False
                elif fault == 'retention-confirm-parent-pid':
                    value['identity']['parent']['pid'] = float(value['identity']['parent']['pid'])
                raw = json.dumps(value, separators=(',', ':')).encode() + b'\n'
                if fault == 'retention-confirm-extra':
                    raw += b'{}\n'
                sys.__stdout__.buffer.write(raw)
                # The entry checks the return count against its original frame.
                return len(original_confirmation)
            return sys.__stdout__.buffer.write(raw)
        def flush(self):
            sys.__stdout__.buffer.flush()

    class Output:
        buffer = Confirmation()
        def flush(self):
            self.buffer.flush()

    # Mutated confirmations still present a successful local write to the S;
    # only the parent's final identity/raw/whole-frame check may reject them.
    original_output = sys.stdout
    original_confirmation = b''
    output_write = Output.buffer.write
    def confirmation_write(raw):
        global original_confirmation
        original_confirmation = raw
        return output_write(raw)
    Output.buffer.write = confirmation_write
    sys.stdout = Output()
    os.fsync, os.write = retention_sync, retention_write
    mark('retention-started')
    worker.cycle_request_retention_main()
    raise SystemExit(0)


raw = sys.stdin.buffer.read()
payload = json.loads(raw)
sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding='utf-8')
mode = payload['identity']['mode']


if stage == 'P':
    original_create = worker.asyncio.create_subprocess_exec
    async def diagnostic(*argv, **kwargs):
        if argv[-1] == 'from ergora.training.runtime.worker import cycle_request_retention_main;cycle_request_retention_main()':
            argv = [argv[0], '-P', __file__, 'D']
        return await original_create(*argv, **kwargs)
    worker.asyncio.create_subprocess_exec = diagnostic
    current = worker._CycleOperation(Path(payload['identity']['control_home']), payload['identity']['project'],
        payload['identity']['cycle_id'], payload['identity']['authorization_sha256'], payload['identity']['mode'],
        snapshot=payload['snapshot'], ordinal=payload['identity']['ordinal'], reason=payload['reason'],
        window=payload['bootstrap'], start_context=payload['start_context'], activity_context=payload['activity_context'])
    mark('retention-parent', {'identity': processes.identity(os.getpid()), 'operation': current.identity,
        'bytes': len(current.encoded), 'output': str(current.output)})
    worker.asyncio.run(current.run())
    raise SystemExit(0)


if stage == 'S':
    original_run = processes.run

    def invoke(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.training.runtime.worker import cycle_operation_main;cycle_operation_main(False)':
            argv = [sys.executable, '-P', __file__, 'H']
            if fault == 'execution-sync-window' and mode == 'request-execution-candidate':
                # Let the blocked H return once after its window. Its last gate,
                # rather than S cancellation, must deny the synchronous publish.
                kwargs['stop_requested'] = lambda: False
        return original_run(argv, *args, **kwargs)

    processes.run = invoke
    if fault == 'sdk-permit-blocked' and mode == 'inspect-controller-activity':
        label = payload['activity_context']['activity_source']['activity_id']
        mark('permit-supervisor-' + label)

        class Frames:
            def write(self, raw):
                count = sys.__stdout__.buffer.write(raw)
                sys.__stdout__.buffer.flush()
                if label in ('normal-first', 'stop-first') and json.loads(raw)['event'] == 'stopped':
                    mark('permit-cleanup-' + label)
                    while not (markers / ('permit-finish-' + label)).exists():
                        time.sleep(.01)
                return count

            def flush(self):
                sys.__stdout__.buffer.flush()

        class Output:
            buffer = Frames()
            def flush(self):
                self.buffer.flush()

        sys.stdout = Output()
    if fault == 'round-reply-loss' and mode in protocol.CYCLE_MEASUREMENT_MODES:
        read = protocol._read_cycle_bytes
        def lost_round_reply(path, limit):
            if path.name == 'stdout.txt':
                mark('round-reply-lost')
                raise OSError('Original H completed; S reply read was lost')
            return read(path, limit)
        protocol._read_cycle_bytes = lost_round_reply
    if ((fault == 'post-stopped' and mode in ('inspect', 'prepare-controller', 'prepare-candidate'))
            or (fault == 'post-stopped-request' and mode == 'request-execution-candidate')
            or (fault == 'post-stopped-confirm' and mode == 'confirm-candidate')):
        read = protocol._read_cycle_bytes

        def blocked_result(path, limit):
            if path.name == 'stdout.txt':
                mark('stopped-result-reader')
                time.sleep(60)
            return read(path, limit)

        protocol._read_cycle_bytes = blocked_result
else:
    if payload['snapshot'] is not None:
        original_plan, original_authorization = protocol.resolve_cycle_snapshot(payload)
    if os.environ.get('ERGORA_TEST_OWNER_CONFIRM') and mode == 'confirm-candidate':
        from ergora.training.runtime.budget import BudgetedStart

        record_owner, binding = BudgetedStart.owner_record, execution_evidence.authenticate_cycle_binding
        observed_reads = {'owner': 0, 'missing': 0}

        def observe_owner(active):
            value = record_owner(active)
            observed_reads['owner'] += 1
            mark('confirm-owner-reads', {'count': observed_reads['owner'], 'pid': os.getpid(),
                                       'operation_id': payload['identity']['operation_id']})
            return value

        def observe_missing(*args, **kwargs):
            value = binding(*args, **kwargs)
            execution = original_authorization['execution']
            target = Path(execution['state_directory']) / ('ergora/training-submissions/' +
                original_plan['definition']['candidates'][payload['identity']['ordinal']]['experiment_id'] + '.budget/owner.json')
            if not target.exists():
                observed_reads['missing'] += 1
                mark('confirm-missing-reads', {'count': observed_reads['missing'], 'pid': os.getpid(),
                                             'operation_id': payload['identity']['operation_id']})
            return value

        BudgetedStart.owner_record = observe_owner
        execution_evidence.authenticate_cycle_binding = observe_missing
        if os.environ.get('ERGORA_TEST_OWNER_CONFIRM_LATE_CONTEXT'):
            require_active, read_context = BudgetedStart.require_active, BudgetedStart.context
            final_read = {'ready': False, 'held': False}
            def observed_active(active, **kwargs):
                value = require_active(active, **kwargs)
                if kwargs.get('owner'):
                    final_read['ready'] = True
                return value
            def held_context(active):
                value = read_context(active)
                if final_read['ready'] and not final_read['held']:
                    final_read['held'] = True
                    mark('confirm-last-context', {'operation_id': payload['identity']['operation_id']})
                    while not (markers / 'confirm-context-release').exists():
                        if protocol.cycle_operation_remaining(payload) <= 0:
                            raise ValueError('Injected context read exhausted its original window')
                        time.sleep(.02)
                return value
            BudgetedStart.require_active = observed_active
            BudgetedStart.context = held_context
    if fault == 'sdk-permit-blocked' and mode == 'inspect-controller-activity':
        label = payload['activity_context']['activity_source']['activity_id']
        child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'])
        mark('permit-descendant-' + label, processes.identity(child.pid))
        mark('permit-helper-' + label, {'process': processes.identity(os.getpid()),
            'identity': payload['identity'], 'bootstrap': payload['bootstrap']})
        while not (markers / ('permit-release-' + label)).exists():
            time.sleep(.01)
    if (fault in ('oversized-stdout', 'oversized-frame') and mode == 'stop-writer'
            or fault in ('candidate-oversized-stdout', 'candidate-oversized-frame') and mode == 'observe-candidate'):
        def large_result(payload):
            # Real H bytes cross either the stdout bound or the identity-bearing frame bound.
            return {'status': 'unknown', 'reason': 'x' * (32768 if fault.endswith('oversized-stdout') else 32500)}

        worker._cycle_operation = large_result
    if (mode in protocol.CYCLE_MEASUREMENT_MODES
            or mode in protocol.CYCLE_START_MODES and fault.startswith('round-')):
        sys.path[:0] = [str(Path(original_authorization['execution']['installation']) / part)
                       for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
        sys.path.insert(0, str(Path(__file__).parent))
        from perf_temporal import connection
        from temporalio.client import Client
        from training_controller_service import RoundService
        import ergora.training.application as training
        import ergora.training.rounds as training_rounds
        from ergora.runtime import budget_clock

        async def round_connect():
            return Client(RoundService(payload, fault), namespace='foreign' if fault == 'round-namespace' else 'default')

        connection.connect = round_connect
        mark('round-helper-entered')
        native_root = Path(original_authorization['execution']['state_directory'])
        if fault in ('round-final-index-stop', 'round-final-parent-source', 'round-final-parent-project',
                     'round-final-parent-predecessor', 'round-final-current-intent'):
            observation = (Path(payload['identity']['control_home']) / 'operations/training-cycles'
                           / payload['identity']['operation_id'] / 'helper/observation.json')
            if fault == 'round-final-current-intent':
                original_read = protocol.read_raw
                def final_current_owner_read(path, *args, **kwargs):
                    value = original_read(path, *args, **kwargs)
                    caller = sys._getframe(2)
                    if (Path(path) == native_root / ('ergora/training-submissions/' + selected + '.budget/owner.json')
                            and caller.f_code is execution_evidence.authenticate_cycle_candidate.__code__
                            and 'result' in caller.f_locals and observation.exists()
                            and sys._getframe(3).f_code is worker._round_operation.__code__):
                        mark('round-final-boundary')
                        while not (markers / 'round-final-release').exists():
                            time.sleep(.01)
                    return value
                protocol.read_raw = final_current_owner_read
            elif fault == 'round-final-index-stop':
                original_read = training_rounds.read
                def final_index_read(*args, **kwargs):
                    value = original_read(*args, **kwargs)
                    if sys._getframe(1).f_code is worker._round_operation.__code__ and observation.exists():
                        mark('round-final-boundary')
                        while not (markers / 'round-final-release').exists():
                            time.sleep(.01)
                    return value
                training_rounds.read = final_index_read
            else:
                original_describe = RoundService.describe_workflow_execution
                async def final_parent_describe(self, request, **kwargs):
                    value = await original_describe(self, request, **kwargs)
                    if request.execution.workflow_id == self.intent['workflow_id'] and observation.exists():
                        mark('round-final-boundary')
                        while not (markers / 'round-final-release').exists():
                            await worker.asyncio.sleep(.01)
                    return value
                RoundService.describe_workflow_execution = final_parent_describe
        selected = original_plan['definition']['candidates'][payload['identity']['ordinal']]['experiment_id']
        job = native_root / 'training/jobs' / selected
        if fault in ('round-no-archive', 'round-rejected', 'round-failed'):
            result = json.loads((job / 'result.json').read_bytes())
            if fault == 'round-rejected':
                gate = json.loads((job / 'gate-report.json').read_bytes())
                gate['passed'] = False
                raw_gate = (json.dumps(gate, ensure_ascii=False, indent=2) + '\n').encode()
                (job / 'gate-report.json').write_bytes(raw_gate)
                import hashlib
                result['gate']['report_sha256'] = hashlib.sha256(raw_gate).hexdigest()
            else:
                result.pop('gate')
                if fault == 'round-failed':
                    result['state'] = 'FAILED'
            (job / 'result.json').write_text(json.dumps(result))
        if fault in ('round-baseline-drift', 'round-source-drift'):
            create = training_rounds.create
            def changed_index(*args, **kwargs):
                if fault == 'round-baseline-drift':
                    path = native_root / ('training/projects/' + payload['identity']['project'] + '/perf/baseline.json')
                    baseline = json.loads(path.read_bytes())
                    baseline['baseline_id'] += '-drift'
                    path.write_text(json.dumps(baseline))
                value = create(*args, **kwargs)
                if fault == 'round-source-drift':
                    path = Path(original_authorization['execution']['installation']) / 'ergora-native-runtime.json'
                    path.write_bytes(path.read_bytes() + b'\n')
                return value
            training_rounds.create = changed_index
        if fault == 'round-stop-after-observation':
            validate = protocol.validate_sources
            calls = 0
            def stopped_sources(capability):
                global calls
                validate(capability)
                calls += 1
                if calls == 4:
                    directory = native_root.parents[0] / 'control/training-cycles/demo/controller'
                    protocol.CycleAdmission(directory, original_authorization).request_stop('Stop at final observation gate')
            protocol.validate_sources = stopped_sources
        if fault == 'round-undurable-stop':
            synchronize = os.fsync
            def stopped_fsync(descriptor):
                path = Path('/proc/self/fd/' + str(descriptor)).resolve()
                if path.name == 'stopped.json' and path.parent.name == 'managed-execution':
                    raise OSError('Original stopped file synchronization failed')
                return synchronize(descriptor)
            os.fsync = stopped_fsync
        if fault in ('round-reader-error', 'round-blocked-reader'):
            evidence = training.evidence
            def unavailable_evidence(*args, **kwargs):
                mark('round-evidence-reader')
                if fault == 'round-blocked-reader':
                    time.sleep(60)
                raise ValueError('Injected later evidence reader failure after complete RPC detail')
            training.evidence = unavailable_evidence
        if fault == 'round-create-error':
            def unavailable_create(*args, **kwargs):
                mark('round-create')
                raise ValueError('Injected original index create failure')
            training_rounds.create = unavailable_create
        if fault in ('round-capture-submission-error', 'round-capture-approval-error'):
            # Keep the original index owner and its real readers. Fail only the
            # later capture read, after earlier complete values have returned.
            capture_code = training_rounds.create.__code__
            def capture_reader(name, original):
                def read(*args, **kwargs):
                    capturing = sys._getframe(1).f_code is capture_code
                    if capturing and fault == 'round-capture-' + name + '-error':
                        mark('round-capture-failed', {'reader': name})
                        raise ValueError('Injected later original capture ' + name + ' failure')
                    value = original(*args, **kwargs)
                    if capturing:
                        if name == 'evidence':
                            value['archive']['gate_result']['limitation'] = '刚返回 index evidence 🧪' + 'y' * 1_100_000
                        mark('round-capture-' + name, value)
                    return value
                return read
            for name in ('inspect', 'evidence', 'submission', 'approval'):
                setattr(training, name, capture_reader(name, getattr(training, name)))
        if fault == 'round-read-error':
            def unavailable_read(*args, **kwargs):
                mark('round-read')
                raise ValueError('Injected original index read failure')
            training_rounds.read = unavailable_read
        if fault in ('round-index-fsync', 'round-index-replace', 'round-observation-fsync'):
            synchronize = os.fsync
            def round_fsync(descriptor):
                path = Path('/proc/self/fd/' + str(descriptor)).resolve()
                if path.name == ('observation.json' if fault == 'round-observation-fsync' else 'rounds.json'):
                    mark(fault)
                    if fault == 'round-index-replace':
                        substitute = path.with_name('replacement')
                        substitute.write_bytes(path.read_bytes())
                        substitute.replace(path)
                    else:
                        raise OSError('Injected original artifact fsync failure')
                return synchronize(descriptor)
            os.fsync = round_fsync
    if mode in protocol.CYCLE_CANDIDATE_MODES and os.environ.get('ERGORA_TEST_TRAINING_SERVICE'):
        mark('candidate-helper-entered')
        sys.path[:0] = [str(Path(original_authorization['execution']['installation']) / part)
                       for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
        sys.path.insert(0, str(Path(__file__).parent))
        selected = original_plan['definition']['candidates'][payload['identity']['ordinal']]
        sys.stdin = io.StringIO(json.dumps({'project': worker.State(Path(payload['identity']['control_home'])).project(
            payload['identity']['project']), 'control_home': payload['identity']['control_home'],
            'experiment_id': selected['experiment_id'], 'operation': 'dispatch',
            'timeout': payload['snapshot']['budget']['policy']['control_timeout_seconds']}))
        import training_submission_client
        sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding='utf-8')
        mark('candidate-service-installed')
        if fault == 'candidate-prepare-return' and mode == 'prepare-candidate':
            import ergora.training.application as training

            original_prepare = training._prepare_submission
            def paused_prepare(*args, **kwargs):
                prepared = original_prepare(*args, **kwargs)
                if prepared[1]['created']:
                    mark('candidate-prepared')
                    while not (markers / 'candidate-prepare-release').exists():
                        if protocol.cycle_operation_remaining(payload) <= 0:
                            raise ValueError('Original prepare allowance ended at its return boundary')
                        time.sleep(.01)
                return prepared
            training._prepare_submission = paused_prepare
        if fault in ('execution-sync-window', 'execution-source-drift') and mode == 'request-execution-candidate':
            project = worker.State.project

            def delayed_project(state, *args, **kwargs):
                value = project(state, *args, **kwargs)
                if (sys._getframe(1).f_code.co_name == 'current'
                        and sys._getframe(2).f_code.co_name == 'request'):
                    if fault == 'execution-source-drift':
                        source = (Path(payload['identity']['control_home']) / 'operations/training-cycles'
                                  / payload['identity']['operation_id'] / 'request.json')
                        original = json.loads(source.read_bytes())
                        original['activity_context']['activity_source']['activity_id'] = 'foreign-source'
                        source.write_text(json.dumps(original))
                        mark(fault)
                    else:
                        from ergora.runtime import budget_clock

                        mark('execution-sync-blocked')
                        while budget_clock._clock()[1] <= payload['bootstrap']['deadline_ns']:
                            time.sleep(.01)
                        mark('execution-sync-returned')
                return value

            worker.State.project = delayed_project
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
            from ergora.runtime import budget_clock

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
        authorization = original_authorization if payload['snapshot'] else json.loads((
            Path(payload['identity']['control_home']) / 'training-cycles' / payload['identity']['project']
            / payload['identity']['cycle_id'] / 'authorization.json').read_bytes())
        sys.path[:0] = [str(Path(authorization['execution']['installation']) / part)
                       for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
        sys.path.insert(0, str(Path(__file__).parent))
        from perf_temporal import connection
        from temporalio.client import Client
        from training_controller_service import DispatchService

        selected = json.loads(os.environ.get('ERGORA_TEST_CYCLE_DISPATCH_CASES', '{}'))
        capacity = json.loads(os.environ.get('ERGORA_TEST_CYCLE_DISPATCH_CAPACITY', '{}'))

        async def connect():
            from dataclasses import replace
            from temporalio.api.common.v1 import Memo, Payloads
            from temporalio.converter import DataConverter, DefaultPayloadConverter

            converter = DataConverter.default
            if capacity:
                class DispatchConverter(DefaultPayloadConverter):
                    def to_payloads(self, values):
                        payloads = super().to_payloads(values)
                        for value, encoded in zip(values, payloads):
                            matching = (isinstance(value, dict) if capacity['field'] == 'input' else isinstance(value, str))
                            if not matching:
                                continue
                            directory = (Path(payload['identity']['control_home']) / 'training-cycles'
                                / payload['identity']['project'] / payload['identity']['cycle_id'] / 'controller')
                            claimed = (directory / 'attempt.json').exists()
                            if capacity.get('after_claim') and not claimed:
                                continue
                            if capacity.get('blocked'):
                                mark('dispatch-encoding-blocked')
                                time.sleep(60)
                            encoded.metadata['dispatch-capacity'] = b''
                            def size():
                                return (Payloads(payloads=[encoded]) if capacity['field'] == 'input'
                                    else Memo(fields={protocol.CYCLE_MEMO_KEY: encoded})).ByteSize()
                            for _ in range(3):
                                encoded.metadata['dispatch-capacity'] += b'x' * max(0, capacity['size'] - size())
                                excess = size() - capacity['size']
                                if excess > 0:
                                    encoded.metadata['dispatch-capacity'] = encoded.metadata['dispatch-capacity'][:-excess]
                            path = Path(os.environ['ERGORA_TEST_CYCLE_DISPATCH']) / 'encodings.json'
                            records = json.loads(path.read_bytes()) if path.exists() else []
                            records.append({'bytes': size(), 'claimed': claimed, 'field': capacity['field']})
                            path.write_text(json.dumps(records))
                        return payloads
                converter = replace(converter, payload_converter_class=DispatchConverter)
            return Client(DispatchService(payload, selected.get(payload['identity']['operation_id'], fault)),
                          namespace='foreign' if fault == 'namespace' else 'default', data_converter=converter)

        connection.connect = connect
        mark('dispatch-helper')
        if fault == 'project-after-claim':
            validate = native_resources.validate_installation

            def drift_project(*args, **kwargs):
                root = validate(*args, **kwargs)
                authorization = original_authorization
                directory = Path(authorization['control_home']) / 'training-cycles' / authorization['project'] / authorization['cycle_id']
                if (directory / 'controller/attempt.json').exists():
                    state = worker.State(Path(authorization['control_home']))
                    with state.connect() as db:
                        row = db.execute('SELECT document FROM projects WHERE id=?', (authorization['project'],)).fetchone()
                        project = json.loads(row[0])
                        project['revision'] += 1
                        db.execute('UPDATE projects SET document=? WHERE id=?', (json.dumps(project), authorization['project']))
                return root

            native_resources.validate_installation = drift_project
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
                    authorization = original_authorization
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
    if fault == 'blocked-stop' and mode == 'notify-owner' and payload['identity']['ordinal'] == 1:
        target = worker._cycle_target

        def blocked_target(*args, **kwargs):
            mark('beta-target-reader')
            time.sleep(60)
            return target(*args, **kwargs)

        worker._cycle_target = blocked_target
    if fault == 'blocked-stop' and mode == 'notify-owner' and payload['identity']['ordinal'] == 0:
        notify = processes.notify_identity

        def record_notification(expected, signum):
            # Independent H processes may reach these storage seams in any order.
            # Establish overlap before the real notification, within the original clock.
            while True:
                remaining = protocol.cycle_operation_remaining(payload)
                if remaining <= 0:
                    raise ValueError('Original cycle allowance ended before both stop branches blocked')
                if all((markers / name).is_file() for name in ('stop-writer', 'beta-target-reader')):
                    break
                time.sleep(min(.01, remaining))
            notify(expected, signum)
            mark('alpha-notified', {'target': expected, 'sender': processes.identity(os.getpid())})

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
        protocol.validate_sources = native_resources.validate_installation = unavailable

if stage == 'S':
    protocol.cycle_supervisor_main()
else:
    worker.cycle_operation_main(False)
