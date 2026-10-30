"""Regression tests for the shared ingress-to-Temporal runtime boundary."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from temporalio.client import WorkflowExecutionStatus
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.service import RPCError, RPCStatusCode

from dev_platform.runtime import DevelopmentTransport, RuntimeNotFound
from test_workflow import fixture


class Handle:
    def __init__(self, spec, status=WorkflowExecutionStatus.RUNNING):
        self.id = "dev-task/" + spec["request"]["task_id"]
        self.describe = AsyncMock(return_value=SimpleNamespace(run_id="run-1", status=status))
        self.signal = AsyncMock()
        self.query = AsyncMock(return_value={"phase": "AWAITING_PLAN_APPROVAL"})
        self.result = AsyncMock(return_value={"status": "CANCEL_UNCONFIRMED"})

    async def fetch_history_events(self, **kwargs):
        yield SimpleNamespace(HasField=lambda field: field == "workflow_execution_started_event_attributes",
                              workflow_execution_started_event_attributes=SimpleNamespace(input=SimpleNamespace(payloads=[])))


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.spec = fixture()
        self.handle = Handle(self.spec)
        self.client = SimpleNamespace(get_workflow_handle=lambda *a, **k: self.handle,
            data_converter=SimpleNamespace(decode=AsyncMock(return_value=[self.spec])), start_workflow=AsyncMock())
        self.runtime = DevelopmentTransport(self.client, "development")

    async def test_cancel_verifies_original_input_before_signal(self):
        other = copy.deepcopy(self.spec); other["request"]["input"]["goal"] = "different"
        self.client.data_converter.decode.return_value = [other]
        with self.assertRaisesRegex(ValueError, "collision"):
            await self.runtime.cancel(self.spec, "run-1", "requested")
        self.handle.signal.assert_not_awaited()

    async def test_signal_is_digest_bound_and_not_workflow_termination(self):
        await self.runtime.cancel(self.spec, "run-1", "requested")
        self.assertEqual(self.handle.signal.call_args.args[1],
                         {"request_sha256": self.spec["request_sha256"], "reason": "requested"})

    async def test_closed_workflow_is_never_signaled(self):
        self.handle.describe.return_value.status = WorkflowExecutionStatus.COMPLETED
        await self.runtime.cancel(self.spec, "run-1", "requested")
        self.handle.signal.assert_not_awaited()

    async def test_transport_failure_is_not_absence(self):
        self.handle.describe.side_effect = RPCError("unavailable", RPCStatusCode.UNAVAILABLE, b"")
        with self.assertRaises(RPCError): await self.runtime.lookup(self.spec)
        self.handle.describe.side_effect = RPCError("missing", RPCStatusCode.NOT_FOUND, b"")
        with self.assertRaises(RuntimeNotFound): await self.runtime.lookup(self.spec)

    async def test_repeated_start_attaches_only_matching_input(self):
        self.client.start_workflow.side_effect = WorkflowAlreadyStartedError("dev-task/task-001", "DevelopmentWorkflow", run_id="run-1")
        self.assertEqual(await self.runtime.start(self.spec), "run-1")
        self.client.data_converter.decode.return_value = [{}]
        with self.assertRaisesRegex(ValueError, "collision"): await self.runtime.start(self.spec)

    async def test_temporal_completion_preserves_unconfirmed_domain_outcome(self):
        self.handle.describe.return_value.status = WorkflowExecutionStatus.COMPLETED
        result = await self.runtime.poll(self.spec, "run-1")
        self.assertEqual(result["phase"], "CANCEL_UNCONFIRMED")
        self.assertTrue(result["terminal"])

    async def test_abnormal_close_requires_reconciliation(self):
        self.handle.describe.return_value.status = WorkflowExecutionStatus.TERMINATED
        result = await self.runtime.poll(self.spec, "run-1")
        self.assertEqual(result["phase"], "NEEDS_RECONCILIATION")
        self.handle.result.assert_not_awaited()

    async def test_cancel_reason_is_bounded(self):
        for reason in ("", "  ", "x" * 1001, None):
            with self.assertRaises(ValueError): await self.runtime.cancel(self.spec, "run-1", reason)
        self.handle.signal.assert_not_awaited()


if __name__ == "__main__": unittest.main()
