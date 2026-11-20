"""One training intent's budget, native creation gate and independent deadline owner."""

import ergora.training.runtime.evidence as execution_evidence
import asyncio
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import sqlite3
import stat
import subprocess
import sys
import time
import uuid

import ergora.training.cycles as training_cycles
import ergora.training.execution_protocol as training_execution_protocol
import ergora.configuration.registrations as registrations
from ergora.runtime import budget_clock
from ergora.runtime import processes
from ergora.runtime.processes import identity as _process_identity
from ergora.training.runtime.context import _select_cycle_project
from ergora.storage.state import State, file_lock, now
from ergora.training.materials import decode_record
from ergora._paths import IMPORT_ROOT


TASK_QUEUE = training_execution_protocol.BUDGET_TASK_QUEUE
_PHASE_PROTOCOL = 'ergora-budget-phase-v1'
_PHASE_MODES = ('monitor', 'fence', 'cleanup', 'publish', 'admission', 'execute')
_COMPUTE_MODES = ('monitor', 'admission', 'execute')
_FINAL_LIMIT = 2 * training_cycles.MAX_RECORD_BYTES


def validate_binding(value: dict) -> None:
    training_execution_protocol.validate_budget_binding(value)


def prepare_binding(operation, intent: dict, selector: dict) -> dict:
    if (not isinstance(selector, dict)
            or set(selector) not in ({'cycle_id', 'authorization_sha256'}, {'cycle_id', 'authorization_sha256', 'controller'})):
        raise ValueError('Select one original training cycle and complete authorization SHA256')
    binding = {**selector, 'task_queue': TASK_QUEUE}
    validate_binding(binding)
    state = State(Path(operation.payload['control_home']))
    observed = training_cycles.status(state, operation.project['id'], binding['cycle_id'],
                                     authorization_sha256=binding['authorization_sha256'])
    if observed['status'] != 'ready':
        raise ValueError('Original training budget is not ready: ' + observed['status'])
    BudgetedStart(operation, {**intent, 'budget': binding}).require_active()
    return binding


async def check_cycle_predecessors(plan, admission, ready, binding, client, remaining):
    """Revalidate predecessor archive and live phase outside writer reservations."""
    from agent_platform.training import LocalTrainingAdapter
    from perf_temporal.models import Binding, Job
    import ergora.training.application as training
    from ergora.training.runtime.status import lookup_controller, observe_submission

    protocol = training_execution_protocol
    authorization, project = admission.authorization, plan['project']
    state = State(Path(authorization['control_home']))

    def retain(ordinal, reader, value):
        print(json.dumps({'reader': f'predecessor.{ordinal}.{reader}', 'value': value},
                         ensure_ascii=False, allow_nan=False), file=sys.stderr, flush=True)

    def active():
        if remaining() <= 0:
            raise ValueError('Original predecessor admission allowance is exhausted')
        admission.check()
        if state.project(project['id']) != project:
            raise ValueError('Previous round admission lost its original registered project')

    adapter = LocalTrainingAdapter()
    try:
        async with asyncio.timeout(remaining()):
            active()
            originals = execution_evidence.authenticate_cycle_binding(binding, plan, admission, ready)
            selection = protocol.round_selection(plan, authorization)
            if plan['definition']['execution_scope'] == protocol.D_SCOPE:
                for value in originals:
                    if value is None:
                        continue
                    observation, original, execution = value
                    active()
                    request = execution['records']['request']
                    runtime = await observe_submission(client, original, run_id=request['run_id'], timeout=remaining())
                    if (runtime is None or runtime['workflow_id'] != request['workflow_id'] or
                            runtime['run_id'] != request['run_id'] or runtime['terminal'] is not True or
                            runtime['phase'] != observation['native']['state']):
                        raise ValueError('Previous typed screen lost its original fixed terminal runtime')
                    native = await adapter.poll_job(Job(Binding(**original['observation']['experiment']['spec']['binding']),
                        request['job_id']), timeout=min(20, remaining()))
                    if native.state != observation['native']['state'] or native.job.job_id != request['job_id']:
                        raise ValueError('Previous typed screen lost its original native result')
                    active()
                await lookup_controller(client, admission.controller_intent(), binding['controller'], timeout=remaining())
                execution_evidence.authenticate_cycle_binding(binding, plan, admission, ready)
                active()
                return None
            for position, (saved, value, original, _) in enumerate(originals):
                active()
                ordinal = value['identity']['ordinal']
                if (value['activity_context']['workflow_input'] != admission.controller_intent()['workflow_input']
                        or value['activity_context']['service_namespace'] != client.namespace
                        or value['selection'] != selection):
                    raise ValueError('Previous observation differs from the current original selection or namespace')
                evidence = training.evidence(state, project['id'], original['experiment_id'])
                retain(ordinal, 'evidence', evidence)
                active()
                if evidence != value['evidence']:
                    raise ValueError('Previous accepted complete archive inventory changed')
                if position != 0:
                    continue
                chain = protocol.ExecutionRecords(project, original['experiment_id'], authorization['control_home']).load()
                request = chain.request_record(authorization['controller']['actor_id'])
                if chain.records['request'] != request:
                    raise ValueError('Previous execution request differs from its complete controller source')
                receipt = chain.document(chain.budget.parent / (chain.ident + '.result.json'))
                runtime = await observe_submission(client, original, run_id=receipt['run_id'], timeout=remaining())
                retain(ordinal, 'runtime', runtime)
                active()
                native = await adapter.poll_job(Job(
                    Binding(**original['observation']['experiment']['spec']['binding']), request['job_id']),
                    timeout=min(20, remaining()))
                retain(ordinal, 'native', asdict(native))
                active()
                execution = chain.observe(durable=True)
                retain(ordinal, 'execution', execution)
                observed = {'status': 'observed' if runtime is not None else 'unknown',
                    'submission': {name: receipt[name] for name in ('workflow_id', 'run_id', 'intent_sha256')},
                    'runtime': runtime, 'native': asdict(native), 'execution': execution,
                    'facts': {'submission': {'state': 'submitted'}, 'candidate': {
                        'current_project_matches': state.project(project['id']) == project,
                        'parent_stop_visible': admission.observe()['stop_visible']}}}
                if protocol.round_state(observed, evidence, saved['report']['rounds'][-1], original) != 'accepted':
                    raise ValueError('Immediately previous round is no longer authenticated accepted')
            await lookup_controller(client, admission.controller_intent(), binding['controller'], timeout=remaining())
            # Blocking archive reads and RPCs cannot leave a stale local admission.
            execution_evidence.authenticate_cycle_binding(binding, plan, admission, ready)
            active()
            return originals[0][0] if originals else None
    finally:
        await adapter.close()


class _BudgetPhase:
    """Transfer one phase without making its caller a shared child subreaper."""

    def __init__(self, budget, mode: str, context: dict, *, phase_id: str | None = None,
                 owner: dict | None = None, final: dict | None = None, execution: dict | None = None):
        phase_id = uuid.uuid4().hex if phase_id is None else phase_id
        if mode not in _PHASE_MODES or not isinstance(phase_id, str) or re.fullmatch('[a-f0-9]{32}', phase_id) is None:
            raise ValueError('Unknown training budget phase or observation identity')
        self.budget, self.mode, self.context = budget, mode, context
        self.identity = {**budget.identity, 'protocol': _PHASE_PROTOCOL, 'phase_id': phase_id, 'mode': mode,
                         'context_sha256': budget.operation.sha(context),
                         'owner': _process_identity(os.getpid()) if owner is None else owner}
        # The budget folder was validated before its owner started. Actual path
        # checks and storage belong to this phase's S, never its live peers.
        self.relative = 'observations/' + mode + '-' + phase_id
        self.output = budget.folder / self.relative
        self.payload = {**budget.operation.payload, 'mode': mode, 'cached': context,
                        'intent_sha256': budget.identity['intent_sha256'],
                        **({'execution': execution} if execution is not None else {}),
                        **({'final': final} if final is not None else {})}
        self.response = training_execution_protocol.PhaseFrames(self.identity, self.output, _FINAL_LIMIT)
        self.supervisor_returncode = None
        self.stopping, self.signalled, self.done = False, False, False
        self.offset = 0
        self.startup_stderr = bytearray()

    def expired(self, *, total: bool = False) -> bool:
        try:
            return self.budget.remaining(self.context, cleanup=total or self.mode not in _COMPUTE_MODES) <= 0
        except (OSError, ValueError):
            return True

    def start(self) -> bool:
        """Launch without reading or writing the business filesystem in the parent."""
        if self.expired() or self.mode in _COMPUTE_MODES and self.budget.cancelled:
            return False
        self.encoded = json.dumps({**self.payload, 'mode': 'phase-supervisor', 'phase': self.identity},
                                  ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.selected = selectors.DefaultSelector()
        self.process = None
        try:
            self.process = subprocess.Popen([sys.executable, '-P', '-c',
                'from ergora.training.runtime.worker import budget_main;budget_main()'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=dict(os.environ), start_new_session=True)
            for stream, event in ((self.process.stdin, selectors.EVENT_WRITE),
                                  (self.process.stdout, selectors.EVENT_READ), (self.process.stderr, selectors.EVENT_READ)):
                os.set_blocking(stream.fileno(), False)
                self.selected.register(stream, event)
        except BaseException:
            self.selected.close()
            # No request bytes have been sent, so this child cannot start work.
            if self.process is not None:
                self.process.terminate()
                self.process.wait()
                for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                    stream.close()
            raise
        return True

    def request_stop(self) -> None:
        """Request this phase's safe reap without waiting for it or a peer."""
        self.stopping = True

    def poll(self, timeout: float = 0) -> bool:
        """Pump this phase's pipes; default polling never waits for a peer."""
        process, selected = self.process, self.selected
        stop = (self.stopping or self.response.problem is not None or self.expired()
                or self.mode in _COMPUTE_MODES and self.budget.cancelled)
        if stop and not self.signalled and process.poll() is None:
            process.terminate()
            self.signalled = True
        # This matching frame proves the only child subtree has been reaped.
        # S may only perform direct storage/observation after that frame.
        if self.response.frames and self.expired(total=True) and process.poll() is None:
            process.kill()
        events = selected.select(timeout)
        for key, event in events:
            stream = key.fileobj
            try:
                if event == selectors.EVENT_WRITE:
                    self.offset += os.write(stream.fileno(), self.encoded[self.offset:self.offset + 65_536])
                    if self.offset == len(self.encoded):
                        selected.unregister(stream)
                        stream.close()
                else:
                    raw = os.read(stream.fileno(), 65_536)
                    if not raw:
                        selected.unregister(stream)
                        stream.close()
                    elif stream is process.stdout:
                        self.response.receive(raw)
                    else:
                        self.startup_stderr.extend(raw[:max(0, 65_536 - len(self.startup_stderr))])
            except BlockingIOError:
                continue
            except BrokenPipeError:
                selected.unregister(stream)
                stream.close()
        self.done = (process.poll() is not None and (not selected.get_map() or not events))
        return not self.done

    def finish(self) -> dict:
        """Collect an exited phase, or safely stop it for a synchronous caller."""
        self.request_stop()
        try:
            while not self.done:
                self.poll(.2)
        finally:
            self.process.wait()
            self.selected.close()
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                if not stream.closed:
                    stream.close()
        self.supervisor_returncode = self.process.returncode
        if (self.process.returncode == 0 and self.offset == len(self.encoded) and len(self.response.frames) == 2
                and not self.response.buffer and self.response.problem is None and not self.expired(total=self.mode == 'execute')):
            return self.response.frames[1]['result']
        return {'status': 'unknown', 'phase_id': self.identity['phase_id'],
                'reason': self.response.problem or self.startup_stderr.decode('utf-8', errors='replace').strip()
                          or 'Original phase has no complete in-budget result',
                'supervisor_returncode': self.process.returncode}

    def run(self) -> dict:
        if not self.start():
            return {'status': 'unknown', 'reason': 'Original training phase allowance is exhausted'}
        try:
            while self.poll(.2):
                pass
        finally:
            result = self.finish()
        return result

    def supervise(self) -> None:
        """Run inside this phase's exclusive Linux subreaper process."""
        if self.identity['owner'] != _process_identity(os.getppid()):
            raise ValueError('Training phase has lost its original parent owner')
        self.output = self.budget.path(self.relative)
        self.output.mkdir(parents=True, mode=0o700)
        with (self.output / 'supervisor.stderr').open('xb') as stderr:
            os.dup2(stderr.fileno(), sys.stderr.fileno())
        cancelled = False

        def cancel(signum, frame):
            nonlocal cancelled
            cancelled = True

        def stopped():
            if cancelled or self.expired():
                return True
            try:
                return self.identity['owner'] != _process_identity(self.identity['owner']['pid'])
            except (OSError, ValueError):
                return True

        def frame(event, field, value):
            print(json.dumps({**self.identity, 'event': event, field: value},
                             ensure_ascii=False, allow_nan=False, separators=(',', ':')), flush=True)

        signal.signal(signal.SIGTERM, cancel)
        signal.signal(signal.SIGINT, cancel)
        command = [sys.executable, '-P', '-c',
                   'from ergora.training.runtime.worker import budget_main;budget_main()']
        environment = dict(os.environ)
        payload = self.payload
        if self.mode == 'execute':
            import ergora.native.commands as native_commands

            owner = self.budget.owner_record()
            capability = owner.get('execution_capability')
            if capability is None:
                raise ValueError('Original owner has no native execution capability')
            grant = payload['execution']
            if (grant['status'] != 'admitted' or grant['launch']['execution_phase_id'] != self.identity['phase_id']
                    or grant['request']['owner_sha256'] != self.budget.operation.sha(owner)):
                raise ValueError('Native execution phase has no original single-use launch grant')
            installation = Path(capability['installation'])
            command = native_commands.worker_command(installation, module='training.runtime.execution', entrypoint='native_main')
            environment['PYTHONPATH'] = os.pathsep.join(str(installation / part) for part in
                ('local', 'upstream/platform', 'upstream/temporal', 'upstream'))
            payload = {**payload, 'phase': self.identity}
        result = processes.run(command, Path.cwd(), self.output / 'helper',
            self.context['policy']['wall_seconds'], json.dumps(payload, ensure_ascii=False, allow_nan=False),
            environment, supervised=True, stop_requested=stopped)
        frame('stopped', 'process', result)
        if self.mode == 'execute':
            # No subprocess may be created after the matching reap frame.
            observed = training_execution_protocol.record_stopped(self.context, self.identity, result)
            frame('result', 'result', {'status': 'executed', 'execution': observed})
            return
        observed = training_cycles._document(self.output / 'helper/stdout.txt') if result['status'] == 'succeeded' else {
            'status': 'unknown', 'process': result}
        frame('result', 'result', observed)


class BudgetedStart:
    """Keep caller-independent ownership behind the original immutable start intent."""

    def __init__(self, operation, intent: dict):
        validate_binding(intent['budget'])
        self.operation, self.intent, self.binding = operation, intent, intent['budget']
        self.folder = operation.path('.budget')
        self.identity = {'schema_version': 1, 'intent_sha256': operation.sha(intent),
                         'authorization_sha256': self.binding['authorization_sha256']}

    def path(self, name: str) -> Path:
        return self.operation.path('.budget/' + name)

    def source(self) -> tuple[State, dict, dict, dict]:
        state = State(Path(self.intent['control_home']))
        directory = training_cycles._directory(state.root, self.intent['project'], self.binding['cycle_id'])
        plan, authorization, ready = training_cycles._load(state.root, self.intent['project'], self.binding['cycle_id'], directory)
        if authorization['schema_version'] == 5:
            execution_evidence.authenticate_cycle_candidate(
                self.intent, plan, training_execution_protocol.CycleAdmission(directory, authorization), ready)
        elif 'controller' in self.binding:
            raise ValueError('Manual authorization cannot acquire a controller binding')
        selected = next((item for item in plan['admissions']
                         if item['experiment_id'] == self.operation.ident), None)
        if (authorization['sha256'] != self.binding['authorization_sha256'] or ready is None
                or authorization['execution'] != self.intent['execution']
                or plan['project']['repo'] != self.intent['repo']
                or plan['project']['registration']['sha256'] != self.intent['registration_sha256']
                or authorization['project_revision'] != self.intent['project_revision']
                or selected is None or self.operation.sha(selected['observation']) != self.operation.sha(self.intent['observation'])):
            raise ValueError('Original training budget differs from its complete start intent, source or admission')
        training_execution_protocol.validate_cpu_contract_authority(plan, authorization, self.operation.ident)
        return state, plan, authorization, ready

    @contextmanager
    def permission(self):
        """Keep the parent's permit for the original action, including its awaits."""
        if 'controller' not in self.binding:
            yield None
            return
        state, _, authorization, _ = self.source()
        directory = training_cycles._directory(state.root, self.intent['project'], self.binding['cycle_id'])
        with training_execution_protocol.CycleAdmission(directory, authorization).permission() as parent:
            yield parent

    async def check_controller_history(self, client=None):
        if 'controller' not in self.binding:
            return
        from ergora.training.runtime.status import lookup_controller

        state, plan, authorization, ready = self.source()
        directory = training_cycles._directory(state.root, self.intent['project'], self.binding['cycle_id'])
        parent = training_execution_protocol.CycleAdmission(directory, authorization).controller_intent()

        def remaining():
            timeout = min(self.operation.payload['timeout'], plan['definition']['budget']['control_timeout_seconds'],
                budget_clock.remaining(authorization['clock'], plan['definition']['budget']['wall_seconds'],
                    plan['definition']['budget']['cleanup_seconds']))
            origin = self.operation.payload.get('cycle_operation')
            if authorization['schema_version'] == 5 and origin is not None:
                return min(timeout, training_execution_protocol.cycle_operation_remaining(origin))
            return timeout

        timeout = remaining()
        if timeout <= 0:
            raise ValueError('Original computation budget is exhausted before controller history check')
        async with asyncio.timeout(timeout):
            if client is None:
                from perf_temporal.connection import connect

                client = await connect()
            if authorization['schema_version'] == 5:
                origin = self.operation.payload.get('cycle_operation')
                context = origin.get('activity_context') if origin is not None else None
                if context is not None and client.namespace != context['service_namespace']:
                    raise ValueError('Candidate runtime namespace differs from its authenticated SDK activity service')
                await check_cycle_predecessors(plan, admission=training_execution_protocol.CycleAdmission(directory, authorization),
                    ready=ready, binding=self.binding, client=client, remaining=remaining)
            else:
                await lookup_controller(client, parent, self.binding['controller'], timeout=timeout)

    def require_active(self, *, owner: bool = False) -> None:
        state, plan, authorization, ready = self.source()
        observed = training_cycles._status(state, plan, authorization, ready)
        if observed['status'] != 'ready':
            raise ValueError('Original training budget cannot start work: ' + observed['status'])
        if owner and (self.path('final.json').exists() or not self.owner_alive()):
            raise ValueError('Original training budget owner is unconfirmed; do not restart or resend')
        # Full source and process checks consume the same computation window.
        if budget_clock.remaining(authorization['clock'], plan['definition']['budget']['wall_seconds'],
                                  plan['definition']['budget']['cleanup_seconds']) <= 0:
            raise ValueError('Original training computation deadline has passed')

    def owner_record(self) -> dict:
        value = training_execution_protocol.owner_record(decode_record(
            training_execution_protocol.read_raw(self.path('owner.json'))))
        process = {name: value.get(name) for name in ('pid', 'start_ticks', 'boot_id')}
        if (any(value[name] != self.identity[name] for name in ('intent_sha256', 'authorization_sha256'))
                or process != _process_identity(value.get('pid'))):
            raise ValueError('Original training budget owner identity is unavailable or changed')
        return value

    def owner_alive(self) -> bool:
        try:
            return training_execution_protocol.owner_active(self.path('owner.json'), self.owner_record())
        except (OSError, ValueError):
            return False

    def ensure_owner(self) -> None:
        if 'controller' in self.binding:
            # A controller's root is born outside the short S-H tree. This
            # last call site must never create a replacement inside that tree.
            self.dispatch_remaining()
            return
        self.require_active()
        if self.path('owner.json').exists():
            self.require_active(owner=True)
            return
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        training_cycles._sync_directory(self.folder.parent)
        # Only this short launcher lock is held by the caller; the owner never
        # acquires the submission lock and inherits neither lifecycle lock.
        with file_lock(self.path('launch.lock'), blocking=False):
            if self.path('owner.json').exists():
                self.require_active(owner=True)
                return
            observation = self.path('launches/' + uuid.uuid4().hex)
            observation.mkdir(parents=True, mode=0o700)
            payload = {**self.operation.payload, 'mode': 'owner', 'intent_sha256': self.identity['intent_sha256']}
            environment = dict(os.environ)
            installation = Path(self.intent['execution']['installation'])
            environment['PYTHONPATH'] = os.pathsep.join(map(str, (
                IMPORT_ROOT, installation / 'local', installation / 'upstream/platform',
                installation / 'upstream/temporal', installation / 'upstream')))
            from ergora.training.materials import cpu_contract

            contract = cpu_contract(self.intent['observation']['experiment']['manifest'])
            if contract is not None:
                payload['cpu_parent_ref'] = training_execution_protocol.publish_cpu_process_context(contract, 'parent',
                    {'intent_sha256': self.identity['intent_sha256'], 'authorization_sha256': self.identity['authorization_sha256']},
                    observation / 'cpu-parent.json', self.folder)
                self.require_active()
            with (observation / 'stdout.json').open('xb') as stdout, (observation / 'stderr.txt').open('xb') as stderr:
                child = subprocess.Popen([sys.executable, '-P', '-c',
                    'from ergora.training.runtime.worker import budget_main;budget_main()'], stdin=subprocess.PIPE,
                    stdout=stdout, stderr=stderr, env=environment, start_new_session=True)
                child.stdin.write(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8'))
                child.stdin.close()
            limit = time.monotonic() + min(5, self.operation.payload['timeout'])
            while time.monotonic() < limit and child.poll() is None:
                if self.owner_alive():
                    self.require_active(owner=True)
                    return
                time.sleep(.02)
            raise ValueError('Independent training budget owner was not confirmed; inspect ' + str(observation))

    def dispatch_remaining(self) -> float | None:
        """Consume the controller's one original start call, never its recovery."""
        if 'controller' not in self.binding:
            return None
        payload = self.operation.payload.get('cycle_operation')
        if not isinstance(payload, dict) or payload.get('identity', {}).get('mode') != 'dispatch-candidate':
            raise ValueError('Controller dispatch requires its complete original start call')
        if (payload['start_context']['intent_sha256'] != self.identity['intent_sha256']
                or self.owner_record() != payload['start_context']['owner']):
            raise ValueError('Controller dispatch lost its original confirmed budget owner')
        return self._start_remaining(payload)

    def _start_remaining(self, payload: dict) -> float:
        """The root and final SDK gate consume the same original prepare request."""
        source = training_execution_protocol.cycle_start_source(payload)
        plan, _ = training_execution_protocol.resolve_cycle_snapshot(source)
        identity, context = payload['identity'], payload['start_context']
        if (context['controller'] != self.binding.get('controller')
                or identity['control_home'] != self.intent['control_home']
                or identity['project'] != self.intent['project'] or identity['cycle_id'] != self.binding['cycle_id']
                or identity['authorization_sha256'] != self.identity['authorization_sha256']
                or plan['definition']['candidates'][identity['ordinal']]['experiment_id'] != self.operation.ident):
            raise ValueError('Controller start differs from its complete original prepare call')
        self.require_active(owner=identity['mode'] == 'dispatch-candidate')
        if _process_identity(identity['parent']['pid']) != identity['parent']:
            raise ValueError('Original controller start parent or operation window ended')
        remaining = training_execution_protocol.cycle_operation_remaining(payload)
        if remaining <= 0:
            raise ValueError('Original controller start parent or operation window ended')
        return remaining

    def launch_context(self, payload: dict) -> dict:
        """Material for the sole prepare winner; this does not launch a process."""
        source = training_execution_protocol.cycle_start_source(payload)
        if (payload['identity']['mode'] != 'prepare-candidate'
                or source['start_context']['controller'] != self.binding.get('controller')):
            raise ValueError('A controller root requires its one original prepare offer')
        self._start_remaining(payload)
        installation = Path(self.intent['execution']['installation'])
        request = {'protocol': 'ergora-training-cycle-root-v1',
            'origin_operation_id': source['identity']['operation_id'], 'parent': source['identity']['parent'],
            'window': source['bootstrap'], 'submission': {'project': self.operation.project,
                'control_home': self.intent['control_home'], 'experiment_id': self.operation.ident,
                'timeout': self.operation.payload['timeout'], 'intent_sha256': self.identity['intent_sha256'],
                'mode': 'controller-owner'}}
        result = {'request': request, 'environment': {
            'PYTHONPATH': os.pathsep.join(map(str, (IMPORT_ROOT, installation / 'local',
                installation / 'upstream/platform', installation / 'upstream/temporal', installation / 'upstream'))),
            'AGENTFLOW_CONFIG_DIR': self.intent['execution']['config_directory'],
            'AGENTFLOW_STATE_DIR': self.intent['execution']['state_directory']}}
        if len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')) > 32_768:
            raise training_cycles._CycleCapacityError(
                'Complete controller root material exceeds 32 KiB; its start intent is already occupied')
        # Consume the original root opportunity under the same submission lock
        # as skip. The existing budget namespace is permanent even on lost reply.
        with file_lock(self.operation.path('.lock'), blocking=False):
            training_execution_protocol.require_not_skipped(self.intent['execution'], self.operation.ident)
            self._start_remaining(payload)
            observation = self.path('launches/' + self.intent['operation_id'])
            observation.mkdir(parents=True, mode=0o700)
            training_execution_protocol.sync_directories(observation, self.operation.root)
            training_execution_protocol.require_not_skipped(self.intent['execution'], self.operation.ident)
            self._start_remaining(payload)
        return result

    def observe(self) -> dict:
        result = {**self.binding, 'owner_status': 'not_started', 'executor_stop_confirmed': None}
        try:
            state, plan, authorization, ready = self.source()
            observed = training_cycles._status(state, plan, authorization, ready)
            result.update(authorization_status=observed['status'],
                          work_remaining_seconds=observed['work_remaining_seconds'],
                          total_remaining_seconds=observed['total_remaining_seconds'])
            if self.path('final.json').exists() and not self.owner_alive():
                training_cycles._sync_directory(self.folder)
                state, plan, authorization, ready = self.source()
                observed = training_cycles._status(state, plan, authorization, ready)
                result.update(authorization_status=observed['status'],
                              work_remaining_seconds=observed['work_remaining_seconds'],
                              total_remaining_seconds=observed['total_remaining_seconds'])
                final = training_cycles._document(self.path('final.json'), limit=_FINAL_LIMIT)
                if any(final.get(key) != value for key, value in self.identity.items()):
                    raise ValueError('Budget final observation differs from the original start intent')
                result.update(owner_status=final['status'], final=final)
                # Recover only the same already-visible fence. Never restart its
                # owner, publish a new fence or replace the historical outcome.
                result['local_fence'] = self.durable_fence()
            elif self.path('owner.json').exists():
                result['owner_status'] = 'active' if self.owner_alive() else 'unknown'
                if result['owner_status'] == 'unknown':
                    result['local_fence'] = self.durable_fence()
        except (OSError, ValueError, sqlite3.Error) as error:
            result.update(authorization_status='unknown', owner_status='unknown', reason=str(error))
        return result

    def durable_fence(self) -> dict | None:
        relative = 'training/fences/' + self.operation.ident + '.json'
        path = self.operation.adapter.safe_file(self.operation.root, relative)
        if not path.exists():
            return None
        expected = {'binding': self.intent['observation']['experiment']['spec']['binding']}
        if self.operation.document(self.operation.root, relative) != expected:
            raise ValueError('Budget fence conflicts with its original complete binding')
        for directory in (path.parent, path.parent.parent, self.operation.root):
            training_cycles._sync_directory(directory)
        raw = self.operation.adapter.read_raw(path)
        if json.loads(raw) != expected:
            raise ValueError('Original budget fence changed during durable publication')
        return {'sha256': hashlib.sha256(raw).hexdigest(), 'durable_at': now()}

    def _source_context(self) -> dict:
        _, plan, authorization, _ = self.source()
        published = registrations.published_project(self.intent['control_home'], self.intent['project'],
            authorization['registration']['operation_id'], authorization['registration']['intent_sha256'])
        return {'intent': self.intent, 'authorization': authorization, 'policy': plan['definition']['budget'],
                'project': plan['project'], 'published_project': published}

    def context(self) -> dict:
        context = self._source_context()
        owner = self.owner_record()
        if 'cpu_context' in owner:
            context['cpu_context'] = owner['cpu_context']
        training_execution_protocol.validate_owner_context(context, owner)
        training_execution_protocol.validate_cpu_budget_context(context, expected_budget={
            name: owner[name] for name in ('pid', 'start_ticks', 'boot_id')})
        return context

    @staticmethod
    def remaining(context: dict, *, cleanup: bool = False) -> float:
        policy = context['policy']
        return budget_clock.remaining(context['authorization']['clock'], policy['wall_seconds'],
                                      0 if cleanup else policy['cleanup_seconds'])

    def supervise(self, mode: str, context: dict, *, final: dict | None = None) -> dict:
        phase = _BudgetPhase(self, mode, context, final=final)
        result = phase.run()
        self.record_phase(phase, result)
        return result

    def record_phase(self, phase, result: dict) -> None:
        helper = phase.response.frames[0]['process'] if phase.response.frames else None
        self.phase_observations.append({'phase_id': phase.identity['phase_id'], 'mode': phase.mode,
            'supervisor_returncode': phase.supervisor_returncode, 'stopped': helper is not None,
            'helper_process': {key: helper[key] for key in ('status', 'returncode')} if helper is not None else None,
            'status': result.get('status', 'unknown'), 'reason': result.get('reason')})

    def supervise_phase(self, context: dict) -> None:
        identity = self.operation.payload['phase']
        phase = _BudgetPhase(self, identity['mode'], context, phase_id=identity['phase_id'],
                             owner=identity['owner'], final=self.operation.payload.get('final'),
                             execution=self.operation.payload.get('execution'))
        if phase.identity != identity:
            raise ValueError('Training supervisor differs from its complete original phase')
        phase.supervise()

    def own(self, *, root_operation: dict | None = None) -> dict:
        if 'controller' in self.binding:
            if root_operation is None or root_operation['identity']['mode'] != 'prepare-candidate':
                raise ValueError('Controller owner requires its one original root bootstrap')
            self._start_remaining(root_operation)
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        with file_lock(self.path('lock'), blocking=False):
            if self.path('owner.json').exists():
                raise ValueError('Original training budget owner cannot be restarted')
            self.require_active()
            context = self._source_context()
            from ergora.training.materials import cpu_contract, validate_cpu_context_observation

            contract = cpu_contract(self.intent['observation']['experiment']['manifest'])
            if contract is not None:
                binding = {'intent_sha256': self.identity['intent_sha256'], 'authorization_sha256': self.identity['authorization_sha256']}
                if root_operation is not None:
                    original = root_operation['identity']
                    parent_path = Path(original['control_home']) / 'operations/training-cycles' / original['operation_id'] / 'cpu-budget-parent.json'
                    raw = training_execution_protocol.read_raw(parent_path, training_execution_protocol.ARTIFACT_LIMIT)
                    parent_ref = {'path': str(parent_path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
                    cycle_ref = training_execution_protocol.cycle_cpu_context(root_operation)
                    parent_identity = original['parent']
                else:
                    parent_ref = self.operation.payload['cpu_parent_ref']
                    cycle_ref = None
                    parent_identity = _process_identity(os.getppid())
                parent_frame = training_execution_protocol.read_trial_reference(parent_ref)
                validate_cpu_context_observation(parent_frame, contract=contract, role='parent', binding=binding,
                    expected_subject=parent_identity, require_complete=False)
                if os.getppid() != parent_identity['pid'] or _process_identity(parent_identity['pid']) != parent_identity:
                    raise ValueError('Typed CPU budget lost its original actual spawn parent')
                budget_ref = training_execution_protocol.publish_cpu_process_context(contract, 'budget', binding,
                    self.path('cpu-context.json'), self.folder)
                context['cpu_context'] = {'parent': parent_ref, 'budget': budget_ref, 'cycle': cycle_ref}
                training_execution_protocol.validate_cpu_budget_context(context, expected_budget=_process_identity(os.getpid()))
                self.require_active()
            self.cancelled = False

            def cancel(signum, frame):
                self.cancelled = True

            signal.signal(signal.SIGTERM, cancel)
            signal.signal(signal.SIGINT, cancel)
            with file_lock(self.path('initializing.lock'), blocking=False):
                training_cycles._sync_directory(self.folder.parent)
                _, _, _, ready = self.source()
                capability = training_execution_protocol.source_capability(Path(self.intent['execution']['installation']), ready)
                if root_operation is not None:
                    self._start_remaining(root_operation)
                owner = {**self.identity, 'schema_version': 2,
                    **_process_identity(os.getpid()), 'context_sha256': self.operation.sha(context),
                    'execution_capability': capability}
                if 'cpu_context' in context:
                    owner['cpu_context'] = context['cpu_context']
                training_cycles._record(self.path('owner.json'), owner)
            self.phase_observations = []
            from ergora.training.runtime.execution import Execution

            outcome = Execution(self.operation, self).drive(context, _BudgetPhase)
            try:
                remaining = self.remaining(context, cleanup=True)
            except (OSError, ValueError):
                remaining = None
            final = {**self.identity, **outcome, 'recorded_at': now(),
                     'total_remaining_seconds': remaining,
                     'overrun_seconds': max(0, -remaining) if remaining is not None else None,
                     'phases': list(self.phase_observations),
                     'executor_stop_confirmed': outcome.get('executor_stop_confirmed')}
            publication = self.supervise('publish', context, final=final)
            return {**final, 'publication': publication}

    def validate_cached(self, context: dict) -> None:
        owner = self.owner_record()
        if (self.operation.sha(context['intent']) != self.identity['intent_sha256']
                or not self.owner_alive()):
            raise ValueError('Supervised training cleanup has no matching original live owner')
        training_execution_protocol.validate_owner_context(context, owner)
        budget_clock.validate(context['authorization']['clock'], context['policy']['wall_seconds'])

    def experiment(self):
        from perf_temporal.models import Binding, Experiment

        spec = self.intent['observation']['experiment']['spec']
        return Experiment(**{**spec, 'binding': Binding(**spec['binding'])})

    async def completion(self, adapter, *, timeout: float = 20) -> dict | None:
        deadline = asyncio.get_running_loop().time() + timeout
        experiment = self.experiment()
        request = self.operation.native_request()
        if request is None:
            return None
        if (self.operation.sha(request['experiment']) != self.operation.sha(asdict(experiment))
                or self.operation.sha(request['runner']) != self.operation.sha(self.intent['observation']['experiment']['current_runner'])):
            raise ValueError('Budget native request differs from its complete original experiment or runner')
        job = await adapter.lookup_job(experiment)
        observation = await adapter.poll_job(job, timeout=max(0, min(20, timeout, deadline - asyncio.get_running_loop().time())))
        if observation.state not in ('SUCCEEDED', 'FAILED', 'CANCELLED', 'SCREEN_COMPLETED', 'SCREEN_REJECTED'):
            return None
        if (self.operation.root / ('training/jobs/' + self.operation.ident + '/managed-execution')).exists():
            stopped = training_execution_protocol.ExecutionRecords(self.operation.project, self.operation.ident,
                str(self.operation.payload['control_home'])).load().observe(durable=True)
            if stopped['executor_stop_confirmed'] is not True:
                return None
        gate = asdict(await adapter.collect_and_gate(job)) if observation.state == 'SUCCEEDED' else None
        screen = (asdict(await adapter.collect_screen(job,
            timeout=max(0, min(20, timeout, deadline - asyncio.get_running_loop().time()))))
            if observation.state in ('SCREEN_COMPLETED', 'SCREEN_REJECTED') else None)
        return {'status': 'completed', 'native': asdict(observation), 'gate': gate, 'screen': screen}

    async def helper(self, mode: str, context: dict) -> dict:
        from agent_platform.training import create_adapter

        if mode in ('monitor', 'fence'):
            adapter = create_adapter()
            try:
                return await self._observe_helper(mode, context, adapter)
            finally:
                await adapter.close()
        return await self._observe_helper(mode, context, None)

    async def _observe_helper(self, mode: str, context: dict, adapter) -> dict:
        self.validate_cached(context)
        if mode == 'publish':
            final = self.operation.payload['final']
            if any(final.get(key) != value for key, value in self.identity.items()):
                raise ValueError('Final budget publication differs from its original start intent')
            training_cycles._record(self.path('final.json'), final, limit=_FINAL_LIMIT)
            return {'status': 'published'}
        if mode == 'monitor':
            while True:
                if not self.owner_alive():
                    return {'status': 'unknown', 'reason': 'Original budget owner disappeared'}
                completed = await self.completion(adapter,
                    timeout=min(20, context['policy']['control_timeout_seconds'], self.remaining(context)))
                if completed is not None:
                    return completed
                self.require_active()
                if self.operation.adapter.safe_file(self.operation.root, 'training/fences/' + self.operation.ident + '.json').exists():
                    return {'status': 'stop', 'reason': 'Original native fence observed'}
                await asyncio.sleep(.1)
        if mode == 'fence':
            completed = await self.completion(adapter,
                timeout=min(20, context['policy']['control_timeout_seconds'], self.remaining(context, cleanup=True)))
            if completed is not None:
                return completed
            relative = 'training/fences/' + self.operation.ident + '.json'
            path = self.operation.adapter.safe_file(self.operation.root, relative)
            for name in ('training/registry.lock', 'training/jobs/' + self.operation.ident + '/request.json', relative):
                self.operation.adapter.safe_file(self.operation.root, name)
            if path.exists() and self.operation.document(self.operation.root, relative) != {'binding': asdict(self.experiment().binding)}:
                raise ValueError('Budget fence conflicts with its original complete binding')
            job = await adapter.fence_and_lookup(self.experiment())
            durable = self.durable_fence()
            if self.remaining(context, cleanup=True) <= 0:
                return {'status': 'unknown', 'reason': 'Original cleanup deadline passed during fence publication'}
            return {'status': 'fenced', 'fence': durable,
                    'existing_job': asdict(job) if job is not None else None}
        if mode == 'admission':
            from ergora.training.runtime.execution import Execution

            training_execution_protocol.validate_cpu_budget_context(context, expected_budget={
                name: self.owner_record()[name] for name in ('pid', 'start_ticks', 'boot_id')})
            return await Execution(self.operation, self).admit(context)
        raise ValueError('Unsupported training budget helper phase')


def _controller_owner(request: dict, *, operation_factory, required_schema_versions: tuple[int, ...] | None = None) -> dict:
    """Bootstrap the actual original root outside every short S-H subtree."""
    protocol = training_execution_protocol
    protocol.validate_cycle_root_request(request)
    payload = request['submission']
    source = decode_record(protocol.read_raw(Path(payload['control_home']) / 'operations/training-cycles'
        / request['origin_operation_id'] / 'request.json', 32_768))
    protocol.cycle_start_source(source)
    plan, authorization = protocol.resolve_cycle_snapshot(source)
    identity = source['identity']
    if (identity['mode'] != 'prepare-candidate' or identity['parent'] != request['parent']
            or source['bootstrap'] != request['window'] or identity['control_home'] != payload['control_home']
            or identity['project'] != payload['project']['id']
            or payload['project']['registration']['definition']['execution'] != authorization['execution']
            or payload['timeout'] != source['snapshot']['budget']['policy']['control_timeout_seconds']
            or plan['definition']['candidates'][identity['ordinal']]['experiment_id'] != payload['experiment_id']
            or os.getppid() != request['parent']['pid']
            or processes.identity(request['parent']['pid']) != request['parent']
            or protocol.cycle_operation_remaining(source) <= 0):
        raise ValueError('Controller root lost its complete original prepare request, parent or window')
    if required_schema_versions is not None and authorization['schema_version'] not in required_schema_versions:
        raise ValueError('Dedicated controller root requires its original schema3 authorization')
    _select_cycle_project(authorization, payload['project'])
    operation = operation_factory(payload)
    intent = operation.load()
    if (intent is None or operation.sha(intent) != payload['intent_sha256']
            or intent.get('budget', {}).get('controller') != source['start_context']['controller']):
        raise ValueError('Controller root lost its complete original selected training intent')
    budget = BudgetedStart(operation, intent)
    observation = budget.path('launches/' + intent['operation_id'])
    with (observation / 'stdout.json').open('xb') as stdout, (observation / 'stderr.txt').open('xb') as stderr:
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stderr.fileno(), sys.stderr.fileno())
    return budget.own(root_operation=source)
