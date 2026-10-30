"""A2A SDK -> HTTP serialization -> shared runtime -> real ephemeral Temporal.

The executor emits explicitly synthetic fixtures. This proves integration and
state/authority boundaries, not real model-generated code or production CI.
"""
import asyncio
import os
from pathlib import Path
import tempfile
import time
import unittest

try:
    import httpx
    from a2a.client import ClientConfig, ClientFactory
    from a2a.client.card_resolver import A2ACardResolver
    from a2a.types import a2a_pb2 as pb
except ImportError as error:
    raise unittest.SkipTest("Install requirements-a2a.txt for A2A integration tests") from error

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from dev_platform.a2a_gateway.backend import TemporalBackend
from dev_platform.a2a_gateway.client import send
from dev_platform.a2a_gateway.server import create_app
from dev_platform.a2a_gateway.store import Store
from dev_platform.activities import Activities
from dev_platform.contracts import canonical_sha
from dev_platform.ingress import IngressLeases, OwnershipError
from dev_platform.portable import convert_v2
from dev_platform.workflow import DevelopmentWorkflow, workflow_id
from test_workflow import AutomaticFileAdapter, fixture


@unittest.skipUnless(os.environ.get("RUN_TEMPORAL_INTEGRATION") == "1", "Set RUN_TEMPORAL_INTEGRATION=1")
class A2ATemporalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.env = await WorkflowEnvironment.start_time_skipping()
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.store = Store(root / "gateway" / "ledger.sqlite")
        self.leases = IngressLeases(root / "ownership" / "leases.sqlite")
        self.adapter = AutomaticFileAdapter(root / "executor")
        self.compiled = convert_v2(fixture(task_id="a2a-temporal-test")["request"])
        self.spec = self.compiled["spec"]
        self.ref = self.store.admit(self.compiled, "alice", time.time() + 3600)
        self.queue = "a2a-real-temporal"
        base = "http://127.0.0.1:8765"
        token = "test-only-" + "x" * 40
        app = create_app(self.store, TemporalBackend(self.env.client, self.queue),
                         {"alice": token}, base, self.leases)
        self.http = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=base,
            headers={"Authorization": "Bearer " + token, "A2A-Version": "1.0"})
        card = await A2ACardResolver(self.http, base).get_agent_card()
        self.client = ClientFactory(ClientConfig(httpx_client=self.http, streaming=False, polling=True,
            supported_protocol_bindings=["JSONRPC"], accepted_output_modes=["application/json"])).create(card)

    async def asyncTearDown(self):
        await self.http.aclose()
        self.store.close(); self.leases.close()
        await self.env.shutdown()
        self.tmp.cleanup()

    def worker(self):
        return Worker(self.env.client, task_queue=self.queue, workflows=[DevelopmentWorkflow],
                      activities=Activities(self.adapter).registered())

    async def submit(self):
        task = await send(self.client, self.ref["task_id"], self.ref["compiled_sha256"], "message-1")
        handle = self.env.client.get_workflow_handle_for(DevelopmentWorkflow.run, workflow_id(self.spec))
        return task, handle

    async def phase(self, handle, expected, require_submitted=False):
        for _ in range(500):
            status = await handle.query(DevelopmentWorkflow.status)
            if status["phase"] == expected and (not require_submitted or self.adapter.submitted):
                return status
            await asyncio.sleep(0.01)
        self.fail("Did not reach " + expected)

    async def test_sdk_submission_human_approval_and_sha_bound_completion(self):
        async with self.worker():
            task, handle = await self.submit()
            status = await self.phase(handle, "AWAITING_PLAN_APPROVAL")
            waiting = await self.client.get_task(pb.GetTaskRequest(id=task.id))
            self.assertEqual(waiting.status.state, pb.TASK_STATE_INPUT_REQUIRED)
            receipt = self.adapter.approve(self.spec, status["plan_sha256"])
            await handle.signal(DevelopmentWorkflow.approve_plan,
                {"request_sha256": self.spec["request_sha256"], "plan_sha256": receipt["plan_sha256"], "receipt_id": receipt["receipt_id"]})
            result = await handle.result()
            final = await self.client.get_task(pb.GetTaskRequest(id=task.id))
        self.assertEqual(result["status"], "REVIEW_READY")
        self.assertEqual(final.status.state, pb.TASK_STATE_COMPLETED)
        self.assertFalse(final.metadata["merge_authorized"])
        self.assertEqual(final.metadata["candidate_sha"], result["candidate_sha"])
        self.assertEqual(len(final.artifacts), 1)
        with self.assertRaises(OwnershipError):
            self.leases.assert_held(self.spec["request"]["tracker"], self.store.lease_owner("alice"),
                                    self.ref["task_id"], canonical_sha(self.spec))

    async def test_sdk_cancel_keeps_ownership_until_external_stop_confirmed(self):
        self.adapter.hold = {"inventory"}
        async with self.worker():
            task, handle = await self.submit()
            await self.phase(handle, "INVENTORY", require_submitted=True)
            try:
                await self.client.cancel_task(pb.CancelTaskRequest(id=task.id))
            except Exception:
                # CancelTask is allowed to report that cancellation is not yet
                # complete; the following assertions verify the durable intent.
                pass
            result = await handle.result()
            final = await self.client.get_task(pb.GetTaskRequest(id=task.id))
        self.assertEqual(result["status"], "CANCEL_UNCONFIRMED")
        self.assertEqual(final.status.state, pb.TASK_STATE_INPUT_REQUIRED)
        self.assertTrue(final.metadata["cancel_requested"])
        self.assertFalse(final.metadata["safe_to_rework"])
        self.leases.assert_held(self.spec["request"]["tracker"], self.store.lease_owner("alice"),
                                self.ref["task_id"], canonical_sha(self.spec))
        with self.assertRaises(OwnershipError):
            self.leases.acquire(self.spec["request"]["tracker"], "symphony:another", "next-revision", "f" * 64)


if __name__ == "__main__": unittest.main()
