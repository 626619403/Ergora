"""Explicit execution and parallel supervision behind the existing training owners."""

import asyncio
from contextlib import ExitStack
import getpass
import json
import os
from pathlib import Path
import sys
import time
import uuid

import ergora.training.execution_protocol as protocol
import ergora.training.runtime.evidence as execution_evidence
from ergora.training.runtime.status import MEMO_KEY, lookup, observe
import ergora.native.resources as native_resources


class Execution:
    def __init__(self, operation, budget):
        self.operation, self.budget = operation, budget

    async def check(self, context: dict):
        from perf_temporal.connection import connect
        from perf_temporal.models import Binding

        op, budget = self.operation, self.budget
        protocol.require_not_skipped(op.execution, op.ident)
        op.registration()
        budget.require_active(owner=True)
        chain = protocol.ExecutionRecords(context['project'], op.ident, str(op.payload['control_home'])).load()
        if chain.owner is None or chain.owner.get('execution_capability') is None:
            raise ValueError('This original budget owner has no execution capability; it cannot be upgraded or restarted')
        execution_evidence.validate_context(context, chain)
        actor = (context['authorization']['controller']['actor_id'] if context['authorization']['schema_version'] == 5
                 else f'unix:{os.getuid()}:{getpass.getuser()}')
        request = chain.request_record(actor)
        # These checks run in a supervised helper, never inside a DB reservation.
        timeout = min(op.payload['timeout'], budget.remaining(context), context['policy']['control_timeout_seconds'])
        if timeout <= 0:
            raise ValueError('Original computation budget is exhausted')
        client = await connect()
        source = op.payload.get('cycle_operation')
        if source is not None and client.namespace != source['activity_context']['service_namespace']:
            raise ValueError('Execution runtime namespace differs from its authenticated SDK activity service')
        await budget.check_controller_history(client)
        found = await lookup(client, context['intent']['observation']['experiment']['spec'],
                             run_id=request['run_id'], timeout=timeout)
        if found is None or (await found[1].memo()).get(MEMO_KEY) != budget.identity['intent_sha256']:
            raise ValueError('Original submitted run has no matching complete history and intent memo')
        control = await observe(*found, Binding(**context['intent']['observation']['experiment']['spec']['binding']), timeout=timeout)
        if (control.get('terminal') is not False or control.get('phase') != 'QUEUED'
                or control['status']['job_id'] != request['job_id']):
            raise ValueError('Managed execution requires the original QUEUED run and exact native job')
        self.current(context, chain)
        return chain, request

    def current(self, context: dict, chain) -> None:
        from ergora.storage.state import State

        op = self.operation
        protocol.require_not_skipped(op.execution, op.ident)
        if State(Path(op.payload['control_home'])).project(op.project['id'])['revision'] != context['intent']['project_revision']:
            raise ValueError('Project revision changed before explicit execution')
        current = protocol.ExecutionRecords(context['project'], op.ident, str(op.payload['control_home'])).load()
        protocol._match(current.owner, chain.owner, 'Original execution publication owner')
        parent = execution_evidence.validate_context(context, current)
        for path in (chain.folder.parent / 'started.json', chain.folder.parent / 'result.json',
                     chain.root / ('training/fences/' + op.ident + '.json')):
            if path.exists() or path.is_symlink():
                raise ValueError('Native execution, result or fence already exists; do not execute again')
        source = op.payload.get('cycle_operation')
        if source is not None:
            protocol.cycle_execution_source(source, context['intent'])
            if parent is not None:
                parent.check()
            # All synchronous source/identity reads above consume this same window.
            # Coroutine cancellation cannot protect the following synchronous publish.
            if protocol.cycle_operation_remaining(source) <= 0:
                raise ValueError('Original execution request operation window is exhausted')

    async def request(self) -> dict:
        from ergora.storage.state import file_lock

        op, budget = self.operation, self.budget
        context = budget.context()
        chain, request = await self.check(context)
        payload = op.payload
        if (payload['confirm'] is not True or payload['expected_revision'] != request['project_revision']
                or payload['intent_sha256'] != request['start_intent_sha256']
                or payload['run_id'] != request['run_id']
                or payload['request_sha256'] != request['native_request_sha256']):
            raise ValueError('Explicit execution must confirm the complete original revision, intent, run and native request SHA256')
        chain.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        with budget.permission():
            with file_lock(chain.folder / 'execution.lock', blocking=False):
                self.current(context, chain)
                protocol.publish(chain.folder / 'request.json', request, chain.root)
                self.current(context, chain)
        saved = protocol.ExecutionRecords(context['project'], op.ident, str(op.payload['control_home'])).load()
        return {'project': op.project['id'], 'project_revision': request['project_revision'], 'experiment_id': op.ident,
                'status': 'requested', 'request_sha256': saved.sha(request), 'run_id': request['run_id'],
                'execution': saved.observe(), 'instruction': 'Observe this original request; never resend the native start'}

    async def admit(self, context: dict) -> dict:
        from ergora.storage.state import file_lock

        folder = self.operation.root / ('training/jobs/' + self.operation.ident + '/managed-execution')
        while True:
            protocol.require_not_skipped(self.operation.execution, self.operation.ident)
            self.budget.require_active(owner=True)
            if not ((folder / 'request.json').exists() or (folder / 'request.json').is_symlink()):
                await asyncio.sleep(.1)
                continue
            chain, request = await self.check(context)
            if chain.sha(chain.records['request']) != chain.sha(request):
                raise ValueError('Explicit execution request differs from its original identity')
            try:
                with self.budget.permission(), file_lock(chain.folder / 'execution.lock', blocking=False):
                    self.current(context, chain)
                    # Even an empty or partial existing launch consumes this opportunity.
                    try:
                        (chain.folder / 'launch.json').lstat()
                    except FileNotFoundError:
                        pass
                    else:
                        raise ValueError('Original execution launch is already consumed; observe it without relaunching')
                    launch = {'schema_version': 1, 'kind': 'training-execution-launch', 'protocol': protocol.PROTOCOL,
                        'request_sha256': chain.sha(request), 'owner_sha256': chain.sha(chain.owner),
                        'authorization_sha256': chain.owner['authorization_sha256'],
                        'clock_sha256': chain.sha(context['authorization']['clock']),
                        'launch_id': uuid.uuid4().hex, 'execution_phase_id': uuid.uuid4().hex}
                    protocol.publish(chain.folder / 'launch.json', launch, chain.root)
                    self.current(context, chain)
                    return {'status': 'admitted', 'request': request, 'launch': launch}
            except BlockingIOError:
                # The original writer can retain its lock after request becomes
                # visible. Wait within this helper's original compute allowance.
                await asyncio.sleep(.1)

    def drive(self, context: dict, phase_type) -> dict:
        """Interleave the original phase lifecycles without waiting on peer storage."""
        budget, phases, outcome, execution = self.budget, {}, None, None
        stopping = False

        def start(mode, **kwargs):
            phase = phase_type(budget, mode, context, **kwargs)
            try:
                if phase.start():
                    phases[mode] = phase
                    return True
                reason = 'Original training phase did not start within its allowance'
            except OSError as error:
                reason = 'Original training phase startup failed: ' + str(error)
            budget.record_phase(phase, {'status': 'unknown', 'reason': reason})
            return False

        def stop_work():
            for mode, phase in phases.items():
                if mode in ('monitor', 'admission', 'execute'):
                    phase.request_stop()
            # Deliver the stop before a fence launch can wait on process creation.
            for mode, phase in phases.items():
                if mode in ('monitor', 'admission', 'execute'):
                    phase.poll()

        def stop_and_fence():
            nonlocal stopping, outcome
            stopping = True
            stop_work()
            if not start('fence'):
                outcome = {'status': 'unknown', 'reason': 'Original fence phase did not start; cleanup remains unconfirmed'}

        try:
            if not start('monitor') or not start('admission'):
                stop_and_fence()
            while phases or outcome is None:
                try:
                    expired = budget.remaining(context) <= 0
                except (OSError, ValueError):
                    expired = True
                if not stopping and outcome is None and (expired or budget.cancelled):
                    stop_and_fence()
                for mode, phase in list(phases.items()):
                    if phase.poll():
                        continue
                    result = phase.finish()
                    budget.record_phase(phase, result)
                    del phases[mode]
                    if mode == 'admission' and not stopping and outcome is None and result.get('status') == 'admitted':
                        launch = result['launch']
                        # Receipt of this one complete in-memory grant is not replayable.
                        if not budget.cancelled and budget.remaining(context) > 0:
                            if not start('execute', phase_id=launch['execution_phase_id'], execution=result):
                                stop_and_fence()
                    elif mode == 'execute':
                        execution = result.get('execution')
                    elif mode == 'monitor' and not stopping and outcome is None:
                        if result.get('status') == 'completed':
                            outcome = result
                            stop_work()
                        else:
                            stop_and_fence()
                    elif mode == 'fence':
                        outcome = result
                        if result.get('status') == 'fenced':
                            if not start('cleanup'):
                                outcome = {**outcome, 'control': {'status': 'unknown',
                                    'reason': 'Original control cleanup phase did not start'}}
                    elif mode == 'cleanup':
                        outcome = {**(outcome or {}), 'control': result}
                time.sleep(.02)
        finally:
            for phase in phases.values():
                phase.request_stop()
            while phases:
                for mode, phase in list(phases.items()):
                    if not phase.poll():
                        result = phase.finish()
                        budget.record_phase(phase, result)
                        del phases[mode]
                time.sleep(.02)
        return {**(outcome or {'status': 'unknown'}), 'execution': execution,
                'executor_stop_confirmed': execution.get('executor_stop_confirmed') if execution else None}


def native_main(installation: str) -> None:
    """Use the selected venv; the callback remains inside the original executor lock."""
    import ergora.native.resources as native_resources
    from agent_platform import core

    payload = json.load(sys.stdin)
    context, phase = payload['cached'], payload['phase']
    project, intent = context['project'], context['intent']
    native_resources.validate_installation(Path(installation), training=True)
    if (sys.prefix != str(Path(installation) / '.venv') or core.ROOT != Path(installation)
            or core.PYTHON != Path(installation) / '.venv/bin/python'
            or core.STATE != Path(intent['execution']['state_directory'])
            or core.CONFIG != Path(intent['execution']['config_directory'])):
        raise ValueError('Managed native interpreter or registered core paths differ')
    from agent_platform.training_executor import process

    def admit(folder, record):
        nonlocal parent, active
        protocol.require_not_skipped(intent['execution'], intent['experiment_id'])
        chain = protocol.ExecutionRecords(project, intent['experiment_id'], intent['control_home']).load()
        checked_parent = execution_evidence.validate_context(context, chain)
        if parent is None and checked_parent is not None:
            parent = checked_parent
            admissions.enter_context(parent.permission())
        request, launch = chain.records['request'], chain.records['launch']
        if request is None or launch is None or any(chain.records[name] is not None for name in ('attempt', 'ack', 'stopped')):
            raise ValueError('Managed execution requires its one unused consumed launch')
        protocol_phase = {'schema_version': 1, 'intent_sha256': chain.sha(intent),
            'authorization_sha256': chain.owner['authorization_sha256'], 'protocol': 'ergora-budget-phase-v1',
            'phase_id': launch['execution_phase_id'], 'mode': 'execute', 'context_sha256': chain.sha(context),
            'owner': {key: chain.owner[key] for key in ('pid', 'start_ticks', 'boot_id')}}
        protocol._match(phase, protocol_phase, 'Complete execution supervisor phase')
        actor = (context['authorization']['controller']['actor_id'] if context['authorization']['schema_version'] == 5
                 else f'unix:{os.getuid()}:{getpass.getuser()}')
        if (folder != chain.folder.parent
                or launch['clock_sha256'] != chain.sha(context['authorization']['clock'])
                or request['actor_id'] != actor):
            raise ValueError('Native callback differs from its original supervisor, actor or clock')
        protocol._match(record, chain.native, 'Native locked request')
        supervisor, executor = protocol.processes.identity(os.getppid()), protocol.processes.identity(os.getpid())
        protocol._match(phase['owner'], {key: chain.owner[key] for key in ('pid', 'start_ticks', 'boot_id')}, 'Supervisor owner')
        parent_fields = Path('/proc/' + str(supervisor['pid']) + '/stat').read_text().rsplit(')', 1)[1].split()
        if int(parent_fields[1]) != chain.owner['pid']:
            raise ValueError('Native supervisor is not a child of its original budget owner')
        protocol._match(protocol.processes.identity(chain.owner['pid']), phase['owner'], 'Original owner process')
        attempt, ack = None, None

        def active():
            protocol.require_not_skipped(intent['execution'], intent['experiment_id'])
            refreshed = protocol.ExecutionRecords(project, intent['experiment_id'], intent['control_home']).load()
            execution_evidence.validate_context(context, refreshed)
            protocol._match(refreshed.owner, chain.owner, 'Native callback original owner')
            protocol._match(refreshed.records, {**chain.records, 'attempt': attempt, 'ack': ack},
                   'Native callback current publication stage')
            if parent is not None:
                parent.check()
            # Parent authorization reads consume the same original work allowance.
            if ((chain.root / ('training/fences/' + chain.ident + '.json')).exists()
                    or not protocol.owner_active(chain.budget / 'owner.json', chain.owner)
                    or protocol.budget_clock.remaining(context['authorization']['clock'], context['policy']['wall_seconds'],
                                              context['policy']['cleanup_seconds']) <= 0):
                raise ValueError('Original execution fence, owner or computation deadline forbids work')
        active()
        attempt = protocol.managed_attempt(request, launch, supervisor, executor, chain.sha)
        protocol.publish(chain.folder / 'attempt.json', attempt, chain.root)
        active()
        ack = {'schema_version': 1, 'kind': 'training-execution-ack', 'protocol': protocol.PROTOCOL,
            'attempt_sha256': chain.sha(attempt), 'launch_sha256': chain.sha(launch), 'request_sha256': chain.sha(request),
            'owner_sha256': chain.sha(chain.owner), 'executor': executor}
        protocol.publish(chain.folder / 'ack.json', ack, chain.root)
        active()
        import ergora.training.materials as materials
        manifest = materials.decode_record(protocol.read_raw(chain.root / ('training/manifests/' + chain.ident + '.json')))
        accepted = execution_evidence.read_cpu_preparation_admission(chain.root, chain.ident, manifest, record['runner'])
        if accepted is not None:
            protocol.validate_cpu_budget_context(context, expected_budget=phase['owner'], require_complete=False)
            binding = {'intent_sha256': chain.sha(intent), 'authorization_sha256': context['authorization']['sha256']}
            cpu = materials.cpu_context_observation(accepted['contract'], 'native', binding)
            materials.validate_cpu_context_observation(cpu, contract=accepted['contract'], role='native', binding=binding,
                expected_subject=executor, require_complete=False)
            materials.publish_material(chain.folder / 'cpu-native.json', materials.observation_bytes(cpu, 10 * 1_048_576), chain.root)
            relation = {'kind': 'training-cpu-native-parent', 'binding': binding, 'supervisor': supervisor,
                        'supervisor_parent_pid': int(parent_fields[1]), 'budget': phase['owner']}
            materials.publish_material(chain.folder / 'cpu-native-parent.json', materials.observation_bytes(relation), chain.root)
            active()


    def before_runner(folder, record, checkouts, manifest):
        from ergora.training.configuration import stage_request

        if active is None:
            raise ValueError('Configuration runner requires its original managed admission')
        active()
        values = stage_request(folder, record, checkouts, manifest, context, active)
        active()
        return values, active

    chain = protocol.ExecutionRecords(project, intent['experiment_id'], intent['control_home'])
    parent, active = None, None
    with ExitStack() as admissions:
        # Hold the permit before the executor lock. New-version completed
        # results retain their original inert read even after the owner ends;
        # if that record vanishes, the callback still requires fresh admission.
        if context['authorization']['schema_version'] == 5 and not (chain.folder.parent / 'result.json').exists():
            parent = execution_evidence.validate_context(context, chain.load())
            admissions.enter_context(parent.permission())
        print(json.dumps(process(chain.folder.parent, admit=admit, before_runner=before_runner),
                         ensure_ascii=False, allow_nan=False))
