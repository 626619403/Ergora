"""Optional application SDK worker for the versioned, budget-aware training queue."""

import asyncio
from contextvars import ContextVar
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import sys

from . import reference, training_cycles
from .reference_training_budget import BudgetedStart, TASK_QUEUE, validate_binding
from .reference_training_submission import _Submission
from .reference_training_execution import Execution
from .state import State


_CREATING = ContextVar('ergora_training_budget_create', default=None)


def create_adapter():
    """Use the pinned native create algorithm; gate its final lookup under its lock."""
    from agent_platform.training import LocalTrainingAdapter, STATE

    class BudgetAdapter(LocalTrainingAdapter):
        def budget_for(self, experiment, intent=None):
            ident = experiment.binding.experiment_id
            if intent is None:
                path = STATE / 'ergora/training-submissions' / (ident + '.intent.json')
                intent = json.loads(training_cycles._read_bytes(path, 16 * 1_048_576))
            validate_binding(intent.get('budget'))
            state = State(Path(intent['control_home']))
            directory = training_cycles._directory(state, intent['project'], intent['budget']['cycle_id'])
            plan, _, _ = training_cycles._load(state, intent['project'], intent['budget']['cycle_id'], directory)
            operation = _Submission({'project': plan['project'], 'control_home': str(state.root),
                                     'experiment_id': ident, 'operation': 'status',
                                     'timeout': plan['definition']['budget']['control_timeout_seconds']})
            original = operation.load()
            if (operation.root != STATE or operation.sha(original) != operation.sha(intent)
                    or operation.sha(original['observation']['experiment']['spec']) != operation.sha(asdict(experiment))):
                raise ValueError('Budget worker input differs from its original native state or complete Experiment')
            return BudgetedStart(operation, original)

        async def create_job_if_absent(self, experiment, manifest):
            path = STATE / 'ergora/training-submissions' / (experiment.binding.experiment_id + '.intent.json')
            try:
                intent = json.loads(training_cycles._read_bytes(path, 16 * 1_048_576))
            except (OSError, ValueError, RecursionError):
                intent = None
            binding = intent.get('budget') if isinstance(intent, dict) else None
            if not isinstance(binding, dict) or 'controller' not in binding:
                # Preserve the original manual gate: existing jobs are returned
                # without rereading start authority. An absent job still reaches
                # budget_for under the original lock and fails on unreadable intent.
                token = _CREATING.set((None, None))
                try:
                    return await super().create_job_if_absent(experiment, manifest)
                finally:
                    _CREATING.reset(token)
            budget = self.budget_for(experiment, intent)
            with budget.permission() as parent:
                await budget.check_controller_history()
                token = _CREATING.set((budget, parent))
                try:
                    return await super().create_job_if_absent(experiment, manifest)
                finally:
                    _CREATING.reset(token)

        async def lookup_job(self, experiment):
            job = await super().lookup_job(experiment)
            creating = _CREATING.get()
            if creating is not None and job is None:
                budget, parent = creating
                if budget is None:
                    budget = self.budget_for(experiment)
                budget.require_active(owner=True)
                if parent is not None:
                    parent.check()
            return job

    return BudgetAdapter()

async def _serve() -> None:
    from perf_temporal.activities import Activities
    from perf_temporal.adapter import load_adapter
    from perf_temporal.connection import connect, task_queue
    from perf_temporal.workflow import ExperimentWorkflow
    from temporalio.worker import Worker

    adapter = load_adapter()
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, stopped.set)

    async def connected():
        async with asyncio.timeout(60):
            while True:
                try:
                    return await connect()
                except (OSError, RuntimeError):
                    await asyncio.sleep(1)

    connecting, stopping = asyncio.create_task(connected()), asyncio.create_task(stopped.wait())
    try:
        await asyncio.wait((connecting, stopping), return_when=asyncio.FIRST_COMPLETED)
        if not stopped.is_set():
            async with Worker(connecting.result(), task_queue=task_queue(), workflows=[ExperimentWorkflow],
                              activities=Activities(adapter).registered(), max_concurrent_activities=8):
                await stopped.wait()
    finally:
        for pending in (connecting, stopping):
            pending.cancel()
        await asyncio.gather(connecting, stopping, return_exceptions=True)
        loop.remove_signal_handler(signal.SIGTERM)


def main(installation: str) -> None:
    root = reference.validate_installation(Path(installation), training=True)
    sys.path[:0] = [str(root / part) for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
    from agent_platform.core import environment

    os.environ.update(environment())
    os.environ.update(PERF_CLUSTER_ADAPTER='ergora.reference_training_worker:create_adapter', PERF_TASK_QUEUE=TASK_QUEUE)
    asyncio.run(_serve())


async def _cleanup(budget, context: dict) -> dict:
    budget.validate_cached(context)
    from .reference_training_cancellation import _Cancellation

    timeout = min(context['policy']['control_timeout_seconds'], budget.remaining(context, cleanup=True))
    if timeout <= 0:
        return {'status': 'unknown', 'reason': 'Original cleanup allowance is exhausted'}
    budget.operation.payload['timeout'] = timeout
    submitted = budget.operation.status(budget.intent)
    if submitted.get('attempt_saved') and not submitted.get('result_saved'):
        await asyncio.wait_for(budget.operation.reconcile(budget.intent), timeout)
        submitted = budget.operation.status(budget.intent)
    if submitted['status'] != 'submitted':
        return {'status': 'unknown', 'reason': 'Original start run is unconfirmed; no cancel was sent'}
    original = context['authorization']['registration']
    project = {**context['published_project'], '_original_registration': {
        **original, 'current_project_revision': budget.intent['project_revision']}}
    payload = {**budget.operation.payload, 'project': project, 'operation': 'prepare',
               'request_id': 'budget-' + budget.identity['intent_sha256'][:32],
               'run_id': submitted['run_id'], 'reason': 'Original training computation budget ended'}
    prepared = await _Cancellation(payload).run()
    result = prepared['cancellation']
    payload.update(operation='resume', intent_sha256=result['intent_sha256'])
    return await _Cancellation(payload).run()

def budget_main() -> None:
    """Dedicated budget process; preserve the original submission context and records."""
    payload = json.load(sys.stdin)
    operation = _Submission(payload)
    if payload['mode'] == 'owner':
        intent = operation.load()
        if intent is None or operation.sha(intent) != payload['intent_sha256']:
            raise ValueError('Independent budget owner requires the complete original training intent')
        result = BudgetedStart(operation, intent).own()
    else:
        context = payload['cached']
        if operation.sha(context['intent']) != payload['intent_sha256']:
            raise ValueError('Supervised budget phase differs from its original training intent')
        budget = BudgetedStart(operation, context['intent'])
        if payload['mode'] == 'phase-supervisor':
            budget.supervise_phase(context)
            return
        result = asyncio.run(_cleanup(budget, context) if payload['mode'] == 'cleanup'
                             else budget.helper(payload['mode'], context))
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


def execution_main() -> None:
    """Prepare an explicit request; business execution belongs to the born owner."""
    from agent_platform.core import Blocked, environment
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        os.environ.update(environment())
        operation = _Submission(payload)
        intent = operation.load()
        if intent is None or 'budget' not in intent:
            raise ValueError('Managed execution requires the original budget-bound submission')
        result = asyncio.run(asyncio.wait_for(Execution(operation, BudgetedStart(operation, intent)).request(), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, ImportError, TimeoutError, RPCError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error) + '; observe the original execution request without resending start') from error
