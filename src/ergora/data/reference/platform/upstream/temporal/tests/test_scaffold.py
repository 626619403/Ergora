"""No GPU/cluster/Cloud side effects. Integration tests use Temporal's ephemeral server."""
import asyncio
from dataclasses import replace
import hashlib
import json
import os
import unittest
from temporalio import workflow
from temporalio.exceptions import ApplicationError
from temporalio.client import WorkflowFailureError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner
from perf_temporal.activities import Activities
from perf_temporal.adapter import load_adapter, AdapterNotConfigured, ApprovalRejected
from perf_temporal.models import (
    Binding, Experiment, Job, Observation, GateDecision, IntegrationTask,
    ReleaseRequest, ReleaseContext, CancelRequest, Cancellation, workflow_id,
)
from perf_temporal.workflow import ExperimentWorkflow


def fixture(name="test-001", max_run_seconds=600, release_wait_seconds=600):
    manifest = {
        "experiment_id": name, "candidate_sha": "a" * 40, "baseline_sha": "b" * 40,
        "runner_template_id": "test-no-gpu", "max_run_seconds": max_run_seconds,
    }
    raw = json.dumps(manifest, sort_keys=True).encode()
    binding = Binding(name, hashlib.sha256(raw).hexdigest(), "a" * 40, "b" * 40)
    return Experiment(binding, "test://manifest", 30, max_run_seconds, release_wait_seconds, 60), raw


class FakeAdapter:
    """Only for tests; never shipped as the default runner or approval verifier."""
    def __init__(self, raw):
        self.raw = raw
        self.job = None
        self.state = "SUCCEEDED"
        self.create_count = 0
        self.cancelled_ids = []
        self.fenced = False
        self.lose_first_submit_response = False
        self.passed = True
        self.tasks = {}
        self.approval_attempts = []
        self.fail_submit_after_accept = False
        self.fail_poll_once = False
        self.fail_cancel = False
        self.control_entered = asyncio.Event()
        self.control_continue = asyncio.Event()

    async def read_manifest(self, uri):
        return self.raw

    async def lookup_job(self, experiment):
        if self.job and self.job.binding != experiment.binding:
            raise ValueError("identity conflict")
        return self.job

    async def create_job_if_absent(self, experiment, manifest):
        if self.fenced:
            raise ValueError("cancelled")
        if self.job is None:
            self.create_count += 1
            self.job = Job(experiment.binding, "job-exact-123")
        if self.fail_submit_after_accept:
            self.control_entered.set()
            await self.control_continue.wait()
            raise ApplicationError("submit response unavailable", non_retryable=True)
        if self.lose_first_submit_response:
            self.lose_first_submit_response = False
            raise TimeoutError("Response lost after scheduler accepted job")
        return self.job

    async def poll_job(self, job):
        if self.fail_poll_once:
            self.fail_poll_once = False
            self.control_entered.set()
            await self.control_continue.wait()
            raise ApplicationError("poll terminal failure", non_retryable=True)
        return Observation(job, self.state)

    async def collect_and_gate(self, job):
        return GateDecision(job, self.passed, "c" * 64, "test://report", "test gate")

    async def fence_and_lookup(self, experiment):
        self.fenced = True
        return await self.lookup_job(experiment)

    async def cancel_job_group(self, job):
        if self.fail_cancel:
            raise ApplicationError("cancel terminal failure", non_retryable=True)
        self.cancelled_ids.append(job.job_id)
        self.state = "CANCELLED"

    async def authorize_release_and_create_task(self, context):
        # Simulates a trusted service lookup, not an auth implementation.
        self.approval_attempts.append(context.request.approval_receipt_id)
        if context.request.approval_receipt_id != "test-trusted-receipt":
            raise ApprovalRejected("Untrusted approval receipt")
        key = (context.experiment.binding.experiment_id, context.gate.evidence_sha)
        self.tasks.setdefault(key, IntegrationTask(context.experiment.binding,
                                                   "integration-123", "test://integration-123"))
        return self.tasks[key]


class Contracts(unittest.IsolatedAsyncioTestCase):
    async def test_import_and_workflow_sandbox(self):
        SandboxedWorkflowRunner().prepare_workflow(workflow._Definition.must_from_class(ExperimentWorkflow))

    async def test_unconfigured_adapter_fails_closed(self):
        old = os.environ.pop("PERF_CLUSTER_ADAPTER", None)
        try:
            with self.assertRaises(AdapterNotConfigured):
                load_adapter()
        finally:
            if old is not None:
                os.environ["PERF_CLUSTER_ADAPTER"] = old

    async def test_lost_submit_response_does_not_duplicate_job(self):
        spec, raw = fixture()
        fake = FakeAdapter(raw)
        fake.lose_first_submit_response = True
        activities = Activities(fake)
        with self.assertRaises(TimeoutError):
            await activities.submit_or_lookup(spec)
        job = await activities.submit_or_lookup(spec)
        self.assertEqual(job.job_id, "job-exact-123")
        self.assertEqual(fake.create_count, 1)

    async def test_manifest_tamper_fails_before_submit(self):
        spec, raw = fixture()
        fake = FakeAdapter(raw + b" ")
        with self.assertRaises(ApplicationError):
            await Activities(fake).submit_or_lookup(spec)
        self.assertEqual(fake.create_count, 0)

    async def test_cancel_fences_and_cancels_only_exact_group(self):
        spec, raw = fixture()
        fake = FakeAdapter(raw)
        activities = Activities(fake)
        job = await activities.submit_or_lookup(spec)
        await activities.cancel_exact_job(Cancellation(spec, "test"))
        self.assertEqual(fake.cancelled_ids, [job.job_id])
        self.assertTrue(fake.fenced)

    async def test_release_requires_bound_evidence_and_external_receipt(self):
        spec, raw = fixture()
        fake = FakeAdapter(raw)
        activities = Activities(fake)
        job = await activities.submit_or_lookup(spec)
        gate = await activities.collect_and_gate(job)
        forged = ReleaseRequest(spec.binding, gate.evidence_sha, "I-am-admin")
        with self.assertRaises(ApplicationError):
            await activities.create_integration_task(ReleaseContext(spec, gate, forged))
        wrong = ReleaseRequest(replace(spec.binding, baseline_sha="d" * 40),
                               gate.evidence_sha, "test-trusted-receipt")
        with self.assertRaises(ApplicationError):
            await activities.create_integration_task(ReleaseContext(spec, gate, wrong))
        good = replace(forged, approval_receipt_id="test-trusted-receipt")
        first = await activities.create_integration_task(ReleaseContext(spec, gate, good))
        second = await activities.create_integration_task(ReleaseContext(spec, gate, good))
        self.assertEqual(first, second)
        self.assertEqual(len(fake.tasks), 1)

    async def test_signals_reject_stale_baseline(self):
        spec, raw = fixture()
        instance = ExperimentWorkflow()
        instance.experiment = spec
        instance.gate = GateDecision(Job(spec.binding, "job-1"), True, "c" * 64,
                                     "test://report", "pass")
        instance.phase = "AWAITING_RELEASE"
        instance.request_release(ReleaseRequest(replace(spec.binding, baseline_sha="d" * 40),
                                                "c" * 64, "test-trusted-receipt"))
        self.assertIsNone(instance.release)
        self.assertIsNotNone(instance.last_signal_rejection)


@unittest.skipUnless(os.environ.get("RUN_TEMPORAL_INTEGRATION") == "1",
                     "Set RUN_TEMPORAL_INTEGRATION=1 to run ephemeral Temporal test server")
class Integration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Downloads a test server if not already cached; no Cloud credentials required.
        self.env = await WorkflowEnvironment.start_time_skipping()

    async def asyncTearDown(self):
        await self.env.shutdown()

    async def wait_phase(self, handle, phase):
        for _ in range(300):
            state = await handle.query(ExperimentWorkflow.status)
            if state.phase == phase:
                return state
            await asyncio.sleep(0.01)
        self.fail(f"Workflow did not enter {phase}")

    async def wait_approval_rejected(self, handle):
        for _ in range(300):
            state = await handle.query(ExperimentWorkflow.status)
            if state.phase == "AWAITING_RELEASE" and state.last_signal_rejection:
                return state
            await asyncio.sleep(0.01)
        self.fail("Workflow did not return to approval wait after receipt rejection")

    async def test_workflow_waits_for_bound_release_then_only_creates_ticket(self):
        spec, raw = fixture("integration-release")
        fake = FakeAdapter(raw)
        async with Worker(self.env.client, task_queue="test-q", workflows=[ExperimentWorkflow],
                          activities=Activities(fake).registered()):
            handle = await self.env.client.start_workflow(
                ExperimentWorkflow.run, spec, id=workflow_id(spec.binding), task_queue="test-q")
            state = await self.wait_phase(handle, "AWAITING_RELEASE")
            self.assertEqual(len(fake.tasks), 0)
            await handle.signal(ExperimentWorkflow.request_release,
                                ReleaseRequest(spec.binding, state.evidence_sha, "test-trusted-receipt"))
            outcome = await handle.result()
            self.assertEqual(outcome.status, "INTEGRATION_TASK_CREATED")
            self.assertEqual(fake.create_count, 1)
            self.assertEqual(len(fake.tasks), 1)

    async def test_workflow_cancels_exact_job(self):
        spec, raw = fixture("integration-cancel")
        fake = FakeAdapter(raw)
        fake.state = "RUNNING"
        async with Worker(self.env.client, task_queue="test-q", workflows=[ExperimentWorkflow],
                          activities=Activities(fake).registered()):
            handle = await self.env.client.start_workflow(
                ExperimentWorkflow.run, spec, id=workflow_id(spec.binding), task_queue="test-q")
            await self.wait_phase(handle, "RUNNING")
            await handle.signal(ExperimentWorkflow.request_cancel, CancelRequest(spec.binding, "test"))
            result = await handle.result()
            self.assertEqual(result.status, "CANCELLED")
            self.assertEqual(fake.cancelled_ids, ["job-exact-123"])
            self.assertFalse(fake.tasks)

    async def test_failed_gpu_job_is_not_resubmitted(self):
        spec, raw = fixture("integration-failed")
        fake = FakeAdapter(raw)
        fake.state = "FAILED"
        async with Worker(self.env.client, task_queue="test-q", workflows=[ExperimentWorkflow],
                          activities=Activities(fake).registered()):
            result = await self.env.client.execute_workflow(
                ExperimentWorkflow.run, spec, id=workflow_id(spec.binding), task_queue="test-q")
            self.assertEqual(result.status, "FAILED")
            self.assertEqual(fake.create_count, 1)
            self.assertFalse(fake.tasks)

    async def test_native_cancellation_runs_exact_job_cleanup(self):
        spec, raw = fixture("integration-native-cancel")
        fake = FakeAdapter(raw)
        fake.state = "RUNNING"
        async with Worker(self.env.client, task_queue="test-q", workflows=[ExperimentWorkflow],
                          activities=Activities(fake).registered()):
            handle = await self.env.client.start_workflow(
                ExperimentWorkflow.run, spec, id=workflow_id(spec.binding), task_queue="test-q")
            await self.wait_phase(handle, "RUNNING")
            await handle.cancel()
            with self.assertRaises(WorkflowFailureError):
                await handle.result()
            self.assertEqual(fake.cancelled_ids, ["job-exact-123"])
            self.assertFalse(fake.tasks)

    async def test_job_lifetime_includes_queue_time(self):
        spec, raw = fixture("integration-queue-budget", max_run_seconds=60)
        fake = FakeAdapter(raw)
        fake.state = "QUEUED"
        async with Worker(self.env.client, task_queue="test-q", workflows=[ExperimentWorkflow],
                          activities=Activities(fake).registered()):
            result = await self.env.client.execute_workflow(
                ExperimentWorkflow.run, spec, id=workflow_id(spec.binding), task_queue="test-q")
            self.assertEqual(result.status, "CANCELLED")
            self.assertIn("Queue-plus-run lifetime exceeded", result.detail)
            self.assertEqual(fake.cancelled_ids, ["job-exact-123"])
            self.assertEqual(fake.create_count, 1)

    async def cancellation_during_failed_control(self, which, cleanup_fails=False):
        spec, raw = fixture("integration-" + which + ("-cleanup-fails" if cleanup_fails else ""))
        fake = FakeAdapter(raw)
        fake.state = "RUNNING"
        fake.fail_submit_after_accept = which == "submit"
        fake.fail_poll_once = which == "poll"
        fake.fail_cancel = cleanup_fails
        async with Worker(self.env.client, task_queue="test-q", workflows=[ExperimentWorkflow],
                          activities=Activities(fake).registered()):
            handle = await self.env.client.start_workflow(
                ExperimentWorkflow.run, spec, id=workflow_id(spec.binding), task_queue="test-q")
            await asyncio.wait_for(fake.control_entered.wait(), timeout=5)
            await handle.signal(ExperimentWorkflow.request_cancel,
                                CancelRequest(spec.binding, "cancel during control RPC"))
            fake.control_continue.set()
            result = await handle.result()
            self.assertTrue(fake.fenced)
            self.assertIn("Control activity failed", result.detail)
            self.assertIn("submit response unavailable" if which == "submit" else "poll terminal failure",
                          result.detail)
            self.assertEqual(fake.create_count, 1)
            self.assertFalse(fake.tasks)
            if cleanup_fails:
                self.assertEqual(result.status, "CANCEL_UNCONFIRMED")
                self.assertIn("cancel terminal failure", result.detail)
            else:
                self.assertEqual(result.status, "CANCELLED")
                self.assertEqual(fake.cancelled_ids, ["job-exact-123"])

    async def test_cancel_during_submit_failure_cleans_up(self):
        await self.cancellation_during_failed_control("submit")

    async def test_cancel_during_poll_failure_cleans_up(self):
        await self.cancellation_during_failed_control("poll")

    async def test_failed_cancel_cleanup_preserves_both_errors(self):
        await self.cancellation_during_failed_control("submit", cleanup_fails=True)

    async def test_rejected_receipt_accepts_new_receipt_without_gpu_rerun(self):
        spec, raw = fixture("integration-receipt-retry")
        fake = FakeAdapter(raw)
        async with Worker(self.env.client, task_queue="test-q", workflows=[ExperimentWorkflow],
                          activities=Activities(fake).registered()):
            handle = await self.env.client.start_workflow(
                ExperimentWorkflow.run, spec, id=workflow_id(spec.binding), task_queue="test-q")
            state = await self.wait_phase(handle, "AWAITING_RELEASE")
            bad = ReleaseRequest(spec.binding, state.evidence_sha, "bad-receipt")
            await handle.signal(ExperimentWorkflow.request_release, bad)
            await self.wait_approval_rejected(handle)
            self.assertFalse(fake.tasks)
            await handle.signal(ExperimentWorkflow.request_release, bad)
            await handle.query(ExperimentWorkflow.status)
            self.assertEqual(fake.approval_attempts, ["bad-receipt"])
            await handle.signal(ExperimentWorkflow.request_release,
                                replace(bad, approval_receipt_id="test-trusted-receipt"))
            result = await handle.result()
            self.assertEqual(result.status, "INTEGRATION_TASK_CREATED")
            self.assertEqual(fake.create_count, 1)
            self.assertEqual(len(fake.tasks), 1)
            self.assertEqual(fake.approval_attempts, ["bad-receipt", "test-trusted-receipt"])

    async def test_rejected_receipt_does_not_extend_original_deadline(self):
        spec, raw = fixture("integration-receipt-expiry", release_wait_seconds=60)
        fake = FakeAdapter(raw)
        async with Worker(self.env.client, task_queue="test-q", workflows=[ExperimentWorkflow],
                          activities=Activities(fake).registered()):
            handle = await self.env.client.start_workflow(
                ExperimentWorkflow.run, spec, id=workflow_id(spec.binding), task_queue="test-q")
            state = await self.wait_phase(handle, "AWAITING_RELEASE")
            await self.env.sleep(50)
            await handle.signal(ExperimentWorkflow.request_release,
                                ReleaseRequest(spec.binding, state.evidence_sha, "bad-receipt"))
            await self.wait_approval_rejected(handle)
            result = await handle.result()
            self.assertEqual(result.status, "RELEASE_EXPIRED")
            # Inspect durable workflow history, not the test server's global clock:
            # time skipping can advance that clock to unrelated expired RPC timers.
            history = await handle.fetch_history()
            timers = [event for event in history.events
                      if event.HasField("timer_started_event_attributes")]
            completed = next(event for event in history.events
                             if event.HasField("workflow_execution_completed_event_attributes"))
            self.assertEqual(len(timers), 2)
            self.assertEqual(timers[0].timer_started_event_attributes.start_to_fire_timeout.seconds, 60)
            self.assertLessEqual(timers[1].timer_started_event_attributes.start_to_fire_timeout.seconds, 10)
            elapsed = (completed.event_time.ToNanoseconds() - timers[0].event_time.ToNanoseconds()) / 1e9
            self.assertLess(elapsed, 65)
            self.assertEqual(fake.create_count, 1)
            self.assertFalse(fake.tasks)


if __name__ == "__main__":
    unittest.main()
