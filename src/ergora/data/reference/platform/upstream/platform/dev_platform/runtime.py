"""Shared, verified Temporal runtime port for ingress adapters.

Symphony and A2A own admission and durable delivery; this port owns Temporal
identity, original-input verification, and cooperative cancellation. It never
approves a plan, terminates a workflow, merges code, or restarts a closed run.
"""
from datetime import timedelta
from typing import Protocol

from temporalio.client import WorkflowExecutionStatus
from temporalio.common import RetryPolicy, WorkflowIDConflictPolicy, WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.service import RPCError, RPCStatusCode

from .contracts import validate_spec
from .workflow import DevelopmentWorkflow, workflow_id


class RuntimeNotFound(Exception):
    """Authoritative Temporal NOT_FOUND; transport failures are not absence."""


class DevelopmentRuntime(Protocol):
    async def start(self, spec: dict) -> str: ...
    async def lookup(self, spec: dict, run_id: str | None = None): ...
    async def poll(self, spec: dict, run_id: str) -> dict: ...
    async def cancel(self, spec: dict, run_id: str, reason: str) -> None: ...


class DevelopmentTransport:
    """One immutable execution per domain task ID, shared by all entrances."""

    def __init__(self, client, queue):
        self.client = client
        self.queue = queue

    async def lookup(self, spec, run_id=None):
        validate_spec(spec)
        wid = workflow_id(spec)
        handle = self.client.get_workflow_handle(wid, run_id=run_id, result_type=dict)
        try:
            description = await handle.describe(rpc_timeout=timedelta(seconds=20))
        except RPCError as error:
            if error.status == RPCStatusCode.NOT_FOUND:
                raise RuntimeNotFound from error
            raise
        handle = self.client.get_workflow_handle(wid, run_id=description.run_id, result_type=dict)
        started = None
        async for event in handle.fetch_history_events(page_size=1, rpc_timeout=timedelta(seconds=20)):
            if event.HasField("workflow_execution_started_event_attributes"):
                started = event.workflow_execution_started_event_attributes
            break
        if started is None:
            raise ValueError("Original task spec unavailable; reconcile instead of restarting")
        values = await self.client.data_converter.decode(started.input.payloads, [dict])
        if values != [spec]:
            raise ValueError("Workflow ID collision: original task spec differs")
        return handle, description

    async def start(self, spec):
        validate_spec(spec)
        try:
            handle = await self.client.start_workflow(
                DevelopmentWorkflow.run, spec, id=workflow_id(spec), task_queue=self.queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                id_conflict_policy=WorkflowIDConflictPolicy.FAIL,
                retry_policy=RetryPolicy(maximum_attempts=1), rpc_timeout=timedelta(seconds=20),
            )
            return handle.result_run_id
        except WorkflowAlreadyStartedError:
            _, description = await self.lookup(spec)
            return description.run_id

    async def poll(self, spec, run_id):
        handle, description = await self.lookup(spec, run_id)
        if description.status == WorkflowExecutionStatus.RUNNING:
            status = await handle.query(DevelopmentWorkflow.status, rpc_timeout=timedelta(seconds=20))
            return {"run_id": description.run_id, "terminal": False, "phase": status["phase"], "status": status}
        if description.status == WorkflowExecutionStatus.COMPLETED:
            outcome = await handle.result(follow_runs=False, rpc_timeout=timedelta(seconds=20))
            return {"run_id": description.run_id, "terminal": True, "phase": outcome["status"], "outcome": outcome}
        return {"run_id": description.run_id, "terminal": True, "phase": "NEEDS_RECONCILIATION",
                "temporal_status": description.status.name}

    async def cancel(self, spec, run_id, reason):
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
            raise ValueError("Cancellation requires a nonempty reason of at most 1000 characters")
        handle, description = await self.lookup(spec, run_id)
        if description.status == WorkflowExecutionStatus.RUNNING:
            await handle.signal(DevelopmentWorkflow.request_cancel,
                                {"request_sha256": spec["request_sha256"], "reason": reason},
                                rpc_timeout=timedelta(seconds=20))
        # Returning from a signal is only acknowledgment of intent, never proof
        # of external termination. The caller must poll the fence outcome.
