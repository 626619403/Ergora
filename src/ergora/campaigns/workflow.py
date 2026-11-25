"""Temporal runtime for the original record-only campaign and its deadline."""

import asyncio
from datetime import timedelta
import signal
import time

from temporalio import workflow
from temporalio.api.common.v1 import WorkflowType
from temporalio.api.taskqueue.v1 import TaskQueue
from temporalio.api.workflowservice.v1 import StartWorkflowExecutionRequest
from temporalio.client import (
    Client, WorkflowContinuedAsNewError, WorkflowExecutionStatus, WorkflowFailureError, WorkflowQueryFailedError,
    WorkflowQueryRejectedError,
)
from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy
from temporalio.converter import WorkflowSerializationContext
from temporalio.exceptions import ApplicationError
from temporalio.service import RPCError, RPCStatusCode
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from ergora.campaigns.records import ATTEMPT_MEMO, OPENING_MEMO, WORKFLOW_TYPE, identity, sha256


RPC_SECONDS = 10
RPC_TIMEOUT = timedelta(seconds=RPC_SECONDS)


def record_state(opening, run_id, phase):
    return {'phase': phase, 'opening_sha256': identity(opening), 'workflow_id': opening['workflow_id'],
            'run_id': run_id, 'expires_at': opening['plan']['limits']['expires_at']}


@workflow.defn(name=WORKFLOW_TYPE)
class Campaign:
    @workflow.init
    def __init__(self, opening: dict):
        self.opening = opening
        info = workflow.info()
        if (info.workflow_id != opening['workflow_id'] or info.run_id != info.first_execution_run_id
                or info.namespace != opening['scheduler']['namespace']
                or workflow.memo_value(OPENING_MEMO, default=None) != identity(opening)
                or not sha256(workflow.memo_value(ATTEMPT_MEMO, default=None))):
            raise ApplicationError('Campaign worker input does not match the original start', non_retryable=True)

    @workflow.run
    async def run(self, opening: dict) -> dict:
        remaining = opening['plan']['limits']['expires_at'] - workflow.time()
        if remaining > 0:
            await workflow.sleep(remaining)
        return record_state(opening, workflow.info().run_id, 'expired')

    @workflow.query
    def state(self) -> dict:
        return record_state(self.opening, workflow.info().run_id, 'waiting_for_expiry')


async def connect(opening):
    scheduler = opening['scheduler']
    try:
        return await Client.connect(scheduler['address'], namespace=scheduler['namespace'])
    except (OSError, RuntimeError) as error:
        raise ConnectionError('Original Temporal connection failed') from error


def memo(opening, attempt):
    return {OPENING_MEMO: identity(opening), ATTEMPT_MEMO: identity(attempt)}


async def start(client, opening, attempt):
    namespace = opening['scheduler']['namespace']
    if client.namespace != namespace:
        raise ValueError('Temporal client does not use the original campaign namespace')
    request = StartWorkflowExecutionRequest(
        namespace=namespace, workflow_id=opening['workflow_id'], workflow_type=WorkflowType(name=WORKFLOW_TYPE),
        task_queue=TaskQueue(name=opening['task_queue']), identity=client.identity,
        request_id=attempt['attempt_id'], workflow_id_conflict_policy=WorkflowIDConflictPolicy.FAIL,
        workflow_id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
    )
    converter = client.data_converter.with_context(WorkflowSerializationContext(namespace, request.workflow_id))
    request.input.payloads.extend(await converter.encode([opening]))
    for key, digest in memo(opening, attempt).items():
        request.memo.fields[key].CopyFrom((await converter.encode([digest]))[0])
    # Client.start_workflow always enables SDK transport retries. The saved
    # attempt permits one Start send, then original-History reconciliation.
    response = await client.workflow_service.start_workflow_execution(request, retry=False, timeout=RPC_TIMEOUT)
    if response.started:
        return response.first_execution_run_id or response.run_id
    return None


async def original(client, opening, attempt, run_id):
    """Verify the first start event on a pinned run, without following resets or successors."""
    if client.namespace != opening['scheduler']['namespace']:
        raise ValueError('Temporal client does not use the original campaign namespace')
    handle = client.get_workflow_handle(opening['workflow_id'], run_id=run_id)
    description = await handle.describe(rpc_timeout=RPC_TIMEOUT)
    first = description.raw_description.workflow_execution_info.first_run_id
    if first != description.run_id or (run_id is not None and description.run_id != run_id):
        raise ValueError('Campaign observation did not select its original first run')
    run_id = description.run_id
    handle = client.get_workflow_handle(opening['workflow_id'], run_id=run_id)
    expected_memo = memo(opening, attempt)
    if description.id != opening['workflow_id'] or await description.memo() != expected_memo:
        raise ValueError('Campaign workflow ID or original dispatch memo differs')
    async for event in handle.fetch_history_events(page_size=1, rpc_timeout=RPC_TIMEOUT):
        if event.event_id != 1 or not event.HasField('workflow_execution_started_event_attributes'):
            break
        started = event.workflow_execution_started_event_attributes
        if (started.workflow_type.name != WORKFLOW_TYPE or started.task_queue.name != opening['task_queue']
                or started.first_execution_run_id != run_id or started.original_execution_run_id != run_id
                or started.continued_execution_run_id or started.initiator != 0 or started.attempt != 1):
            raise ValueError('Campaign History type, queue or first start differs')
        if set(started.memo.fields) != set(expected_memo):
            raise ValueError('Campaign History does not have its original dispatch memo')
        for key, digest in expected_memo.items():
            if await client.data_converter.decode([started.memo.fields[key]], [str]) != [digest]:
                raise ValueError('Campaign History dispatch memo differs')
        values = await client.data_converter.decode(started.input.payloads)
        if len(values) != 1 or not isinstance(values[0], dict) or identity(values[0]) != identity(opening):
            raise ValueError('Campaign History complete plan input differs')
        return handle, description
    raise ValueError('Campaign original start History is missing its first event')


def require_state(observed, opening, run_id, phase):
    if identity(observed) != identity(record_state(opening, run_id, phase)):
        raise ValueError('Campaign Workflow state differs from the original plan or run')
    return observed


async def runtime_status(handle, description, opening):
    temporal_status = description.status
    if temporal_status == WorkflowExecutionStatus.RUNNING:
        try:
            async with asyncio.timeout(2):
                observed = await handle.query(Campaign.state, rpc_timeout=timedelta(seconds=2))
        except (RPCError, TimeoutError, WorkflowQueryFailedError, WorkflowQueryRejectedError):
            return {'temporal_status': temporal_status.name, 'workflow_state_status': 'unavailable'}
        return {'temporal_status': temporal_status.name, 'workflow_state_status': 'observed',
                'workflow_state': require_state(observed, opening, description.run_id, 'waiting_for_expiry')}
    if temporal_status == WorkflowExecutionStatus.COMPLETED:
        observed = await handle.result(follow_runs=False, rpc_timeout=RPC_TIMEOUT)
        if description.close_time is None or description.close_time.timestamp() < opening['plan']['limits']['expires_at']:
            raise ValueError('Campaign Workflow completion preceded its original expiry')
        return {'temporal_status': temporal_status.name, 'workflow_state_status': 'observed',
                'workflow_state': require_state(observed, opening, description.run_id, 'expired')}
    return {'temporal_status': temporal_status.name, 'workflow_state_status': 'unavailable'}


async def run_worker(client, handle, opening):
    """Poll only the saved queue until the original run closes, or the foreground worker stops."""
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, stopped.set)

    async def wait_for_completion():
        # Only a bounded final poll is needed if the operator starts a worker after expiry.
        after_expiry = max(0, opening['plan']['limits']['expires_at'] - time.time())
        async with asyncio.timeout(after_expiry + RPC_SECONDS):
            return await handle.result(follow_runs=False)

    try:
        worker = Worker(client, task_queue=opening['task_queue'], workflows=[Campaign],
                        graceful_shutdown_timeout=timedelta(0))
        async with worker:
            closing = asyncio.create_task(wait_for_completion())
            stopping = asyncio.create_task(stopped.wait())
            try:
                await asyncio.wait((closing, stopping), return_when=asyncio.FIRST_COMPLETED)
                if closing.done():
                    try:
                        require_state(closing.result(), opening, handle.run_id, 'expired')
                    except (WorkflowFailureError, WorkflowContinuedAsNewError):
                        # The caller reads this pinned run again and reports its actual terminal status.
                        pass
                    return 'closed'
                return 'interrupted'
            finally:
                for task in (closing, stopping):
                    task.cancel()
                await asyncio.gather(closing, stopping, return_exceptions=True)
    finally:
        loop.remove_signal_handler(signal.SIGTERM)
