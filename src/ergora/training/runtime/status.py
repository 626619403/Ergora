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


async def observe_submission(client, intent: dict, *, run_id: str, timeout: float):
    """Read one fixed submission's full input, memo and runtime result."""
    from dev_platform.contracts import canonical_sha
    from perf_temporal.models import Binding

    spec = intent['observation']['experiment']['spec']
    found = await lookup(client, spec, run_id=run_id, timeout=timeout)
    if found is None:
        return None
    if (await found[1].memo()).get(MEMO_KEY) != canonical_sha(intent):
        raise ValueError('Original candidate runtime memo differs from its complete start intent')
    return await observe(*found, Binding(**spec['binding']), timeout=timeout)


async def lookup_controller(client, intent: dict, binding: dict, *, timeout: float):
    """Verify a parent's fixed run without interpreting it as an Experiment."""
    from temporalio.client import WorkflowExecutionStatus
    from temporalio.service import RPCError, RPCStatusCode
    from ergora.training.execution_protocol import CYCLE_MEMO_KEY

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
    await _controller_history(client, handle, intent, binding['intent_sha256'], rpc_timeout)
    return handle, description


async def _controller_history(client, handle, intent, digest, rpc_timeout):
    """Share complete input validation without sharing the callers' status policy."""
    from ergora.training.execution_protocol import CYCLE_MEMO_KEY, CycleAdmission, cycle_workflow_type

    started = None
    async for event in handle.fetch_history_events(page_size=1, rpc_timeout=rpc_timeout):
        if event.HasField('workflow_execution_started_event_attributes'):
            started = event.workflow_execution_started_event_attributes
        break
    if (started is None or started.workflow_type.name != cycle_workflow_type(intent['protocol'])
            or started.task_queue.name != intent['task_queue']):
        raise ValueError('Original controller type, queue or started input is unavailable or changed')
    values = await client.data_converter.decode(started.input.payloads, [dict])
    memo = started.memo.fields.get(CYCLE_MEMO_KEY)
    if (CycleAdmission._sha(values) != CycleAdmission._sha([intent['workflow_input']]) or memo is None
            or await client.data_converter.decode([memo], [str]) != [digest]):
        raise ValueError('Original controller complete started input or intent memo differs')
    return started


async def lookup_controller_submission(client, intent: dict, *, run_id: str | None, timeout: float):
    """Authenticate the original start even after close; never follow a successor run.

    Lost-reply recovery assumes the protocol exclusively owns its workflow ID.
    Identical manual ID reuse cannot be excluded by latest metadata alone.
    """
    from temporalio.service import RPCError, RPCStatusCode
    from ergora.training.execution_protocol import CYCLE_MEMO_KEY, CycleAdmission

    rpc_timeout = timedelta(seconds=timeout)
    handle = client.get_workflow_handle(intent['workflow_id'], run_id=run_id)
    try:
        description = await handle.describe(rpc_timeout=rpc_timeout)
        if run_id is None:
            run_id = description.raw_description.workflow_execution_info.first_run_id
            if not run_id:
                raise ValueError('Controller service has no authenticated original first run')
            if description.run_id != run_id:
                raise ValueError('Controller has a successor or reset; recover only an already known original run')
            handle = client.get_workflow_handle(intent['workflow_id'], run_id=run_id)
            description = await handle.describe(rpc_timeout=rpc_timeout)
    except RPCError as error:
        if error.status == RPCStatusCode.NOT_FOUND:
            return None
        raise
    digest = CycleAdmission._sha(intent)
    if (description.id != intent['workflow_id'] or description.run_id != run_id
            or description.raw_description.workflow_execution_info.first_run_id != run_id
            or (await description.memo()).get(CYCLE_MEMO_KEY) != digest):
        raise ValueError('Controller original run or complete intent memo differs')
    started = await _controller_history(client, handle, intent, digest, rpc_timeout)
    if (started.first_execution_run_id != run_id or started.original_execution_run_id != run_id
            or started.continued_execution_run_id or started.initiator != 0 or started.attempt != 1):
        raise ValueError('Controller history is a successor or reset; original ownership remains unknown')
    return handle, description


async def observe_controller_worker(handle, task_queue: str, *, timeout: float) -> dict:
    """Read the first Worker start from an already authenticated original controller handle."""
    scheduled = None
    count = 0
    async for event in handle.fetch_history_events(page_size=8, rpc_timeout=timedelta(seconds=timeout)):
        count += 1
        if count > 32:
            return {'status': 'unobserved'}
        if event.HasField('workflow_task_scheduled_event_attributes'):
            if scheduled is not None or event.workflow_task_scheduled_event_attributes.task_queue.name != task_queue:
                raise ValueError('Worker task schedule differs from the original controller queue')
            scheduled = event.event_id
        elif event.HasField('workflow_task_started_event_attributes'):
            started = event.workflow_task_started_event_attributes
            if scheduled is None or started.scheduled_event_id != scheduled or event.event_id <= scheduled:
                raise ValueError('Worker start does not bind its original scheduled task')
            return {'status': 'started', 'scheduled_event_id': scheduled, 'started_event_id': event.event_id}
        elif event.HasField('workflow_task_timed_out_event_attributes'):
            expired = event.workflow_task_timed_out_event_attributes
            if scheduled is None or expired.scheduled_event_id != scheduled or expired.started_event_id:
                raise ValueError('Worker timeout does not bind its original scheduled task')
            scheduled = None
    return ({'status': 'unobserved'} if scheduled is None else
            {'status': 'scheduled', 'scheduled_event_id': scheduled})


async def observe_controller_queue_polling(client, task_queue: str, *, timeout: float) -> dict:
    """Read the authenticated controller's Workflow Task Queue poller report."""
    from temporalio.api.enums.v1 import TaskQueueType
    from temporalio.api.taskqueue.v1 import TaskQueue
    from temporalio.api.workflowservice.v1 import DescribeTaskQueueRequest

    request = DescribeTaskQueueRequest(namespace=client.namespace, task_queue=TaskQueue(name=task_queue),
                                       task_queue_type=TaskQueueType.TASK_QUEUE_TYPE_WORKFLOW)
    response = await client.workflow_service.describe_task_queue(
        request, retry=False, timeout=timedelta(seconds=timeout))
    return {'status': 'observed', 'poller_count': len(response.pollers)}


async def authenticate_round_collection(client, intent: dict, binding: dict, request: dict,
                                        context: dict, *, timeout: float):
    """Authenticate the single original collect command, consuming the full fixed history."""
    from temporalio.api.history.v1 import History
    from temporalio.client import WorkflowExecutionStatus
    import ergora.training.execution_protocol as protocol

    names = protocol.cycle_activity_names()
    action = ('collect-round' if context['activity_source']['activity_type'] ==
              names['collect-round'] and context['activity_source']['attempt'] == 1
              else 'reconcile-round')
    protocol.validate_cycle_activity_request(request, action)
    protocol.validate_cycle_activity_context(context, measurement_action=action)
    source = context['activity_source']
    if (client.namespace != context['service_namespace'] or request['workflow_input'] != intent['workflow_input']
            or source['workflow_id'] != binding['workflow_id'] or source['workflow_run_id'] != binding['run_id']
            or action == 'collect-round' and source['attempt'] != 1):
        raise ValueError('Round collection differs from its original controller or first attempt')
    async with asyncio.timeout(timeout):
        found = await lookup_controller_submission(client, intent, run_id=binding['run_id'], timeout=timeout)
        if found is None or found[1].status != WorkflowExecutionStatus.RUNNING:
            raise ValueError('Round collection requires its authenticated original RUNNING controller')
        count, size, collects, current = 0, 0, 0, 0
        collect_id = 'candidate-' + str(request['ordinal']) + '-collect'
        async for event in found[0].fetch_history_events(rpc_timeout=timedelta(seconds=timeout)):
            count += 1
            size += History(events=[event]).ByteSize()
            if count > 8000 or size > 8 * 1_048_576:
                raise ValueError('Complete original controller history exceeds round collection capacity')
            if not event.HasField('activity_task_scheduled_event_attributes'):
                continue
            scheduled = event.activity_task_scheduled_event_attributes
            is_collect = scheduled.activity_id == collect_id
            is_current = scheduled.activity_id == source['activity_id']
            # Decode collect commands as well as matching IDs so another command
            # cannot spend the same round's opportunity under a different ID.
            collect_type = scheduled.activity_type.name == names['collect-round']
            if not (is_collect or is_current or collect_type):
                continue
            values = await client.data_converter.decode(scheduled.input.payloads, [dict])
            same_round = (len(values) == 1 and isinstance(values[0], dict)
                          and values[0].get('ordinal') == request['ordinal'])
            if is_collect or collect_type and same_round:
                collects += 1
                if (not is_collect or not collect_type or scheduled.task_queue.name != intent['task_queue']
                        or protocol.CycleAdmission._sha(values) != protocol.CycleAdmission._sha([request])):
                    raise ValueError('Original collect command differs from its complete frozen request')
            if is_current:
                current += 1
                if (scheduled.activity_type.name != source['activity_type']
                        or scheduled.task_queue.name != source['task_queue']
                        or protocol.CycleAdmission._sha(values) != protocol.CycleAdmission._sha([request])):
                    raise ValueError('Current round activity differs from its original scheduled command')
        if collects != 1 or current != 1 or action == 'collect-round' and source['activity_id'] != collect_id:
            raise ValueError('Round collection has no unique original scheduled opportunity')
        return found


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
