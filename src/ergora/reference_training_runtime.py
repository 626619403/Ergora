"""Read original ExperimentWorkflow facts without creating jobs or sending signals."""

import asyncio
from dataclasses import asdict
from datetime import timedelta
import json
import os
import sys


async def lookup(client, spec: dict, *, run_id: str | None, timeout: int):
    """Find a fixed original run, validating its complete initial Experiment."""
    from dev_platform.contracts import canonical_sha
    from perf_temporal.models import Binding, Experiment, Outcome, workflow_id
    from temporalio.service import RPCError, RPCStatusCode

    experiment = Experiment(**{**spec, 'binding': Binding(**spec['binding'])})
    experiment.validate()
    wid = workflow_id(experiment.binding)
    handle = client.get_workflow_handle(wid, run_id=run_id, result_type=Outcome)
    rpc_timeout = timedelta(seconds=timeout)
    try:
        description = await handle.describe(rpc_timeout=rpc_timeout)
    except RPCError as error:
        if error.status == RPCStatusCode.NOT_FOUND:
            return None
        raise
    if run_id is not None and description.run_id != run_id:
        raise ValueError('Training runtime returned another run ID')
    handle = client.get_workflow_handle(wid, run_id=description.run_id, result_type=Outcome)
    started = None
    async for event in handle.fetch_history_events(page_size=1, rpc_timeout=rpc_timeout):
        if event.HasField('workflow_execution_started_event_attributes'):
            started = event.workflow_execution_started_event_attributes
        break
    if started is None:
        raise ValueError('Original training input unavailable; reconcile the original workflow')
    values = await client.data_converter.decode(started.input.payloads, [dict])
    if canonical_sha(values) != canonical_sha([spec]):
        raise ValueError('Training workflow ID collision: complete original Experiment differs')
    return handle, description


MEMO_KEY = 'ergora.training_submission_sha256'


async def lookup_controller(client, intent: dict, binding: dict, *, timeout: float):
    """Verify a parent's fixed run without interpreting it as an Experiment."""
    from temporalio.client import WorkflowExecutionStatus
    from temporalio.service import RPCError, RPCStatusCode
    from .training_execution_protocol import CYCLE_MEMO_KEY, CycleAdmission

    handle = client.get_workflow_handle(binding['workflow_id'], run_id=binding['run_id'])
    rpc_timeout = timedelta(seconds=timeout)
    try:
        description = await handle.describe(rpc_timeout=rpc_timeout)
    except RPCError as error:
        if error.status == RPCStatusCode.NOT_FOUND:
            raise ValueError('Original controller run is not found; no new work is admitted') from error
        raise
    if (description.id != binding['workflow_id'] or description.run_id != binding['run_id']
            or description.status != WorkflowExecutionStatus.RUNNING
            or (await description.memo()).get(CYCLE_MEMO_KEY) != binding['intent_sha256']):
        raise ValueError('Original controller run, running state or complete intent memo differs')
    started = None
    async for event in handle.fetch_history_events(page_size=1, rpc_timeout=rpc_timeout):
        if event.HasField('workflow_execution_started_event_attributes'):
            started = event.workflow_execution_started_event_attributes
        break
    if (started is None or started.workflow_type.name != 'TrainingCycleWorkflow'
            or started.task_queue.name != intent['task_queue']):
        raise ValueError('Original controller type, queue or started input is unavailable or changed')
    values = await client.data_converter.decode(started.input.payloads, [dict])
    memo = started.memo.fields.get(CYCLE_MEMO_KEY)
    if (CycleAdmission._sha(values) != CycleAdmission._sha([intent['workflow_input']]) or memo is None
            or await client.data_converter.decode([memo], [str]) != [binding['intent_sha256']]):
        raise ValueError('Original controller complete started input or intent memo differs')
    return handle, description


async def observe(handle, description, binding, *, timeout: int) -> dict:
    """Read domain facts after the caller has verified the fixed original run."""
    from perf_temporal.workflow import ExperimentWorkflow
    from temporalio.client import WorkflowExecutionStatus

    rpc_timeout = timedelta(seconds=timeout)
    result = {'workflow_id': handle.id, 'run_id': description.run_id, 'runtime_status': 'queried',
              'temporal_status': description.status.name}
    if description.status == WorkflowExecutionStatus.RUNNING:
        status = await handle.query(ExperimentWorkflow.status, rpc_timeout=rpc_timeout)
        if status.binding != binding:
            raise ValueError('Training runtime status belongs to another binding')
        return {**result, 'terminal': False, 'phase': status.phase, 'status': asdict(status)}
    if description.status == WorkflowExecutionStatus.COMPLETED:
        outcome = await handle.result(follow_runs=False, rpc_timeout=rpc_timeout)
        if outcome.binding != binding:
            raise ValueError('Training runtime outcome belongs to another binding')
        return {**result, 'terminal': True, 'phase': outcome.status, 'outcome': asdict(outcome)}
    return {**result, 'terminal': True, 'phase': 'NEEDS_RECONCILIATION'}


async def _status(payload: dict) -> dict:
    from perf_temporal.connection import connect
    from perf_temporal.models import Binding, workflow_id

    binding = Binding(**payload['spec']['binding'])
    found = await lookup(await connect(), payload['spec'], run_id=payload['run_id'], timeout=payload['timeout'])
    if found is None:
        return {'workflow_id': workflow_id(binding), 'run_id': payload['run_id'], 'runtime_status': 'not_found'}
    return await observe(*found, binding, timeout=payload['timeout'])


def main() -> None:
    """Use the selected native connection environment in a bounded query process."""
    from agent_platform.core import Blocked, environment
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        os.environ.update(environment())
        result = asyncio.run(asyncio.wait_for(_status(payload), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Training runtime query timed out; execution state remains unknown') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: Training runtime query RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
