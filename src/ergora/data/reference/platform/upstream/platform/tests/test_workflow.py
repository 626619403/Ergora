"""Synthetic CPU fixtures only: no Codex, repository CI, merge, or Cloud mutations."""
import asyncio
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from temporalio import workflow
from temporalio.exceptions import ApplicationError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner
from dev_platform.adapter import FileAdapter, ContractViolation, ApprovalRejected, load_adapter, publish, sha
from dev_platform.activities import Activities
from dev_platform.contracts import canonical_sha
from dev_platform.registry import load_profile, make_spec
from dev_platform.workflow import DevelopmentWorkflow, workflow_id, StopWork


def fixture(task_type="repository-governance", task_id="task-001", units=None):
    profile = load_profile(task_type, 1)
    request = {"schema_version": 2, "task_type": task_type, "task_version": 1, "task_id": task_id,
               "profile_sha256": canonical_sha(profile),
               "tracker": {"kind": "gitlab", "project": "group/repo", "issue_id": "7"},
               "repository": {"base_sha": "b" * 40, "starting_sha": "a" * 40},
               "input": {"goal": "Improve the repository within the approved scope", "allowed_paths": ["src", "docs"],
                         "acceptance": ["Existing behavior remains compatible"], "constraints": ["No merge or deployment"],
                         "risk": "standard", "work_units": units or [
                             {"id": "unit-a", "depends_on": [], "paths": ["src/a"], "instructions": "Implement one bounded improvement"}]}}
    return make_spec(request)


class AutomaticFileAdapter(FileAdapter):
    """Test-only executor that fabricates reports; not a real correctness verifier."""
    def __init__(self, folder):
        super().__init__({**{key: str(Path(folder) / key) for key in ("requests", "receipts", "artifacts", "approvals", "fences")}, "trusted_receipts": True})
        self.submitted = []
        self.hold = set()
        self.fail = set()
        self.same_reviewer = False
        self.final_sha = "f" * 40
        self.create_count = 0
        self.polling = 0
        self.peak_polling = 0

    async def submit(self, context):
        job = await super().submit(context)
        if job["job_id"] not in [j["job_id"] for j in self.submitted]:
            self.submitted.append(job); self.create_count += 1
        return job

    def receipt(self, job):
        context = job["context"]; stage = context["stage"].split(":", 1)[0]
        profile = context["spec"]["profile"]
        role = profile["roles"][stage]
        actor = {"id": stage + "-principal", "session_id": job["job_id"] + "-session", "role": role,
                 "kind": "ci" if stage == "verify" else "agent"}
        if stage == "review" and self.same_reviewer: actor["id"] = "work-principal"
        artifact_names = list(profile["artifacts_by_stage"][stage])
        artifacts = []
        for name in artifact_names:
            raw = json.dumps({"synthetic_fixture": True, "stage": context["stage"], "artifact": name}).encode()
            relative = job["task_id"] + "/" + job["job_id"] + "/" + name + ".json"
            path = self.path("artifacts", relative); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
            artifacts.append({"name": name, "path": relative, "sha256": hashlib.sha256(raw).hexdigest()})
        checks = []
        if stage == "verify": checks = [{"id": name, "status": "pass", "artifact": artifacts[0]["name"]} for name in profile["required_checks"]]
        if stage == "review": checks = [{"id": "independent-review", "status": "pass", "artifact": artifacts[0]["name"]}]
        return {"schema_version": 1, "job_id": job["job_id"], "job_sha256": job["job_sha256"],
                "state": "FAILED" if context["stage"] in self.fail else "SUCCEEDED", "actor": actor,
                "candidate_sha": context["expected_candidate_sha"] or self.final_sha,
                "artifacts": artifacts, "checks": checks, "detail": "Synthetic test fixture, not CI evidence"}

    async def poll(self, job):
        if job["context"]["stage"] in self.hold: return None
        self.polling += 1; self.peak_polling = max(self.peak_polling, self.polling)
        try:
            await asyncio.sleep(0.03)
            path = self.path("receipts", job["task_id"] + "/" + job["job_id"] + ".json")
            if not path.exists(): publish(path, self.receipt(job))
            return await super().poll(job)
        finally: self.polling -= 1

    def approve(self, spec, plan_hash, receipt_id="approval-1", **updates):
        value = {"schema_version": 1, "kind": "plan-approval", "task_id": spec["request"]["task_id"],
                 "request_sha256": spec["request_sha256"], "profile_sha256": spec["profile_sha256"],
                 "plan_sha256": plan_hash, "decision": "approve", "principal_type": "human",
                 "actor_id": "human-owner", "role": "owner", "expires_at": time.time() + 3600, "revoked": False}
        value.update(updates)
        publish(self.path("approvals", receipt_id + ".json"), value)
        return {"task_id": spec["request"]["task_id"], "request_sha256": spec["request_sha256"],
                "profile_sha256": spec["profile_sha256"], "plan_sha256": plan_hash, "receipt_id": receipt_id}


def context(spec, stage="verify", **updates):
    result = {"task_id": spec["request"]["task_id"], "job_id": spec["request"]["task_id"] + "-" + stage,
              "spec": spec, "request_sha256": spec["request_sha256"], "profile_sha256": spec["profile_sha256"],
              "stage": stage, "expected_candidate_sha": "f" * 40, "unit": None, "dependencies": {},
              "author_ids": ["work-principal"], "author_sessions": ["author-session"]}
    result.update(updates); return result


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.adapter = AutomaticFileAdapter(self.tmp.name); self.spec = fixture()
    async def asyncTearDown(self): self.tmp.cleanup()

    async def test_workflow_sandbox(self):
        SandboxedWorkflowRunner().prepare_workflow(workflow._Definition.must_from_class(DevelopmentWorkflow))

    async def test_unconfigured_adapter_fails_closed(self):
        previous = os.environ.pop("DEV_ADAPTER_CONFIG", None)
        try:
            with self.assertRaises(Exception): load_adapter()
        finally:
            if previous is not None: os.environ["DEV_ADAPTER_CONFIG"] = previous

    async def test_publication_is_immutable_and_idempotent(self):
        first = await self.adapter.submit(context(self.spec)); second = await self.adapter.submit(context(self.spec))
        self.assertEqual(first, second); self.assertEqual(self.adapter.create_count, 1)
        with self.assertRaises(ContractViolation): await self.adapter.submit(context(self.spec, expected_candidate_sha="e" * 40))

    async def test_oversized_receipt_metadata_rejected(self):
        job = await self.adapter.submit(context(self.spec)); receipt = self.adapter.receipt(job)
        receipt["detail"] = "x" * 32768
        with self.assertRaisesRegex(ContractViolation, "32 KiB"):
            self.adapter.verify_receipt(job, receipt)

    async def test_oversized_context_rejected_before_publication(self):
        with self.assertRaisesRegex(ContractViolation, "1,000,000"):
            await self.adapter.submit(context(self.spec, dependencies={"too-large": "x" * 1_000_001}))
        self.assertFalse(self.adapter.roots["requests"].exists())

    async def test_workflow_bounds_context_before_temporal_serialization(self):
        instance = DevelopmentWorkflow(); instance.spec = self.spec
        with self.assertRaisesRegex(StopWork, "1,000,000"):
            instance.context("integrate", dependencies={"too-large": "x" * 1_000_001})

    async def test_stage_job_binds_the_approved_plan(self):
        instance = DevelopmentWorkflow(); instance.spec = self.spec
        instance.approved_plan = {"plan_sha256": "c" * 64,
                                  "receipt": {"artifacts": [{"name": "execution-plan", "path": "task/plan.json", "sha256": "d" * 64}]},
                                  "approval": {"receipt_id": "trusted-plan-receipt", "approval_sha256": "e" * 64, "actor_id": "human-owner"}}
        ctx = instance.context("work:unit-a", unit=self.spec["request"]["input"]["work_units"][0])
        self.assertEqual(ctx["approved_plan"], instance.approved_plan)
        first = await self.adapter.submit(ctx)
        altered = copy.deepcopy(ctx); altered["approved_plan"]["plan_sha256"] = "f" * 64
        self.assertNotEqual(sha(altered), first["job_sha256"])
        with self.assertRaises(ContractViolation): await self.adapter.submit(altered)

    async def test_receipt_artifact_tampering_rejected(self):
        job = await self.adapter.submit(context(self.spec)); receipt = self.adapter.receipt(job)
        self.adapter.path("artifacts", receipt["artifacts"][0]["path"]).write_text("tampered")
        with self.assertRaises(ContractViolation): self.adapter.verify_receipt(job, receipt)

    async def test_receipt_wrong_job_rejected(self):
        job = await self.adapter.submit(context(self.spec)); receipt = self.adapter.receipt(job); receipt["job_sha256"] = "0" * 64
        with self.assertRaises(ContractViolation): self.adapter.verify_receipt(job, receipt)

    async def test_artifact_escape_and_symlink_rejected(self):
        with self.assertRaises(ContractViolation): self.adapter.path("artifacts", "../outside")
        self.adapter.roots["artifacts"].mkdir(); outside = Path(self.tmp.name) / "outside"; outside.write_text("secret")
        (self.adapter.roots["artifacts"] / "link").symlink_to(outside)
        with self.assertRaises(ContractViolation): self.adapter.path("artifacts", "link")

    async def test_plan_approval_bound_scope_and_expiry(self):
        ctx = self.adapter.approve(self.spec, "c" * 64)
        result = await self.adapter.authorize(ctx); self.assertEqual(result["actor_id"], "human-owner")
        with self.assertRaises(ApprovalRejected): await self.adapter.authorize({**ctx, "plan_sha256": "d" * 64})
        bad = self.adapter.approve(self.spec, "c" * 64, "expired", expires_at=time.time() - 1)
        with self.assertRaises(ApprovalRejected): await self.adapter.authorize(bad)

    async def test_infinite_approval_expiry_rejected(self):
        # JSON can contain Infinity even though the trusted publisher rejects it.
        ctx = self.adapter.approve(self.spec, "c" * 64)
        path = self.adapter.path("approvals", "approval-1.json"); value = json.loads(path.read_text()); value["expires_at"] = float("inf")
        path.write_text(json.dumps(value))
        with self.assertRaises(ApprovalRejected): await self.adapter.authorize(ctx)

    async def store_receipt(self, job, change):
        value = self.adapter.receipt(job); change(value)
        publish(self.adapter.path("receipts", job["task_id"] + "/" + job["job_id"] + ".json"), value)
        return await Activities(self.adapter).poll(job)

    async def test_missing_required_check_rejected(self):
        job = await self.adapter.submit(context(self.spec))
        with self.assertRaises(ApplicationError): await self.store_receipt(job, lambda r: r["checks"].pop())

    async def test_extra_failed_check_rejected(self):
        job = await self.adapter.submit(context(self.spec))
        with self.assertRaises(ApplicationError):
            await self.store_receipt(job, lambda r: r["checks"].append({"id": "unexpected-regression", "status": "fail", "artifact": r["artifacts"][0]["name"]}))

    async def test_stale_candidate_rejected(self):
        job = await self.adapter.submit(context(self.spec))
        with self.assertRaises(ApplicationError): await self.store_receipt(job, lambda r: r.update(candidate_sha="e" * 40))

    async def test_review_rejects_author_principal(self):
        job = await self.adapter.submit(context(self.spec, "review"))
        with self.assertRaises(ApplicationError): await self.store_receipt(job, lambda r: r["actor"].update(id="work-principal"))

    async def test_review_rejects_reused_author_session(self):
        job = await self.adapter.submit(context(self.spec, "review"))
        with self.assertRaises(ApplicationError): await self.store_receipt(job, lambda r: r["actor"].update(session_id="author-session"))

    async def test_verification_requires_ci_principal(self):
        job = await self.adapter.submit(context(self.spec))
        with self.assertRaises(ApplicationError): await self.store_receipt(job, lambda r: r["actor"].update(kind="agent"))

    async def test_fence_reports_unresolved_and_prevents_new_stage(self):
        self.adapter.hold = {"verify"}
        await self.adapter.submit(context(self.spec))
        result = await self.adapter.fence({"task_id": self.spec["request"]["task_id"], "request_sha256": self.spec["request_sha256"]})
        self.assertFalse(result["confirmed"]); self.assertEqual(len(result["unresolved_jobs"]), 1)
        with self.assertRaises(ContractViolation): await self.adapter.submit(context(self.spec, "review"))

    async def test_required_artifacts_rejected_when_missing(self):
        job = await self.adapter.submit(context(self.spec, "review"))
        with self.assertRaises(ApplicationError): await self.store_receipt(job, lambda r: r.update(artifacts=[], checks=[]))


@unittest.skipUnless(os.environ.get("RUN_TEMPORAL_INTEGRATION") == "1", "Set RUN_TEMPORAL_INTEGRATION=1 for real ephemeral Temporal integration tests")
class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.env = await WorkflowEnvironment.start_time_skipping()
        self.tmp = tempfile.TemporaryDirectory(); self.adapter = AutomaticFileAdapter(self.tmp.name)
    async def asyncTearDown(self):
        self.tmp.cleanup(); await self.env.shutdown()

    async def wait_phase(self, handle, phase, rejection=False):
        for _ in range(500):
            status = await handle.query(DevelopmentWorkflow.status)
            if status["phase"] == phase and (not rejection or status["last_rejection"]): return status
            await asyncio.sleep(0.01)
        self.fail("Workflow did not reach " + phase + ": " + str(status))

    async def approve(self, handle, spec, receipt_id="approval-1"):
        status = await self.wait_phase(handle, "AWAITING_PLAN_APPROVAL")
        ctx = self.adapter.approve(spec, status["plan_sha256"], receipt_id)
        await handle.signal(DevelopmentWorkflow.approve_plan, {"request_sha256": spec["request_sha256"], "plan_sha256": ctx["plan_sha256"], "receipt_id": receipt_id})

    def worker(self):
        return Worker(self.env.client, task_queue="development-test", workflows=[DevelopmentWorkflow], activities=Activities(self.adapter).registered())

    async def start(self, spec):
        return await self.env.client.start_workflow(DevelopmentWorkflow.run, spec, id=workflow_id(spec), task_queue="development-test")

    async def test_governance_waits_for_trusted_plan_then_review_ready(self):
        spec = fixture()
        async with self.worker():
            handle = await self.start(spec); await self.wait_phase(handle, "AWAITING_PLAN_APPROVAL")
            self.assertEqual([j["context"]["stage"] for j in self.adapter.submitted], ["inventory", "plan"])
            await self.approve(handle, spec)
            result = await handle.result()
        self.assertEqual(result["status"], "REVIEW_READY")
        self.assertEqual(result["candidate_sha"], "f" * 40)
        self.assertEqual(result["review"]["candidate_sha"], result["candidate_sha"])
        self.assertEqual(len(self.adapter.submitted), 6)
        for job in self.adapter.submitted:
            if job["context"]["stage"] in {"inventory", "plan"}:
                self.assertNotIn("approved_plan", job["context"])
                continue
            approved = job["context"]["approved_plan"]
            self.assertEqual(approved["plan_sha256"], result["plan_sha256"])
            self.assertEqual(canonical_sha(approved["receipt"]), result["plan_sha256"])
            self.assertIn("execution-plan", {a["name"] for a in approved["receipt"]["artifacts"]})
            self.assertEqual(approved["approval"]["receipt_id"], "approval-1")
            self.assertEqual(approved["approval"], result["plan_approval"])
            self.assertNotIn("human-owner", job["context"]["author_ids"])

    async def test_large_change_parallel_units_and_dependency_commits(self):
        units = [{"id": "a", "depends_on": [], "paths": ["src/a"], "instructions": "Update A"},
                 {"id": "b", "depends_on": [], "paths": ["src/b"], "instructions": "Update B"},
                 {"id": "c", "depends_on": ["a", "b"], "paths": ["src/c"], "instructions": "Integrate contracts C"}]
        spec = fixture("large-change", units=units)
        async with self.worker():
            handle = await self.start(spec); await self.approve(handle, spec); result = await handle.result()
        self.assertEqual(result["status"], "REVIEW_READY")
        self.assertGreaterEqual(self.adapter.peak_polling, 2)
        stages = [j["context"]["stage"] for j in self.adapter.submitted]
        self.assertLess(stages.index("work:a"), stages.index("work:c")); self.assertLess(stages.index("work:b"), stages.index("work:c"))
        downstream = next(j for j in self.adapter.submitted if j["context"]["stage"] == "work:c")
        self.assertEqual(set(downstream["context"]["dependencies"]), {"a", "b"})
        self.assertEqual(downstream["context"]["dependencies"]["a"]["candidate_sha"], "f" * 40)

    async def test_self_review_blocks_final_success(self):
        self.adapter.same_reviewer = True; spec = fixture()
        async with self.worker():
            handle = await self.start(spec); await self.approve(handle, spec); result = await handle.result()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("own implementation", result["detail"])

    async def test_failed_unit_fences_unresolved_sibling_and_blocks_dependents(self):
        units = [{"id": "a", "depends_on": [], "paths": ["src/a"], "instructions": "Update A"},
                 {"id": "b", "depends_on": [], "paths": ["src/b"], "instructions": "Update B"},
                 {"id": "c", "depends_on": ["a"], "paths": ["src/c"], "instructions": "Update C"}]
        spec = fixture("large-change", units=units); self.adapter.fail = {"work:a"}; self.adapter.hold = {"work:b"}
        async with self.worker():
            handle = await self.start(spec); await self.approve(handle, spec); result = await handle.result()
        self.assertEqual(result["status"], "CANCEL_UNCONFIRMED")
        self.assertEqual(len(result["fence"]["unresolved_jobs"]), 1)
        stages = [j["context"]["stage"] for j in self.adapter.submitted]
        self.assertNotIn("work:c", stages); self.assertNotIn("integrate", stages)

    async def test_untrusted_approval_then_new_receipt_is_accepted(self):
        spec = fixture()
        async with self.worker():
            handle = await self.start(spec); status = await self.wait_phase(handle, "AWAITING_PLAN_APPROVAL")
            await handle.signal(DevelopmentWorkflow.approve_plan, {"request_sha256": spec["request_sha256"], "plan_sha256": status["plan_sha256"], "receipt_id": "forged"})
            await self.wait_phase(handle, "AWAITING_PLAN_APPROVAL", rejection=True)
            self.assertEqual(len(self.adapter.submitted), 2)
            await self.approve(handle, spec, "real-approval"); result = await handle.result()
        self.assertEqual(result["status"], "REVIEW_READY")

    async def test_approval_deadline_blocks_without_any_implementation(self):
        spec = fixture()
        async with self.worker():
            handle = await self.start(spec); await self.wait_phase(handle, "AWAITING_PLAN_APPROVAL"); result = await handle.result()
        self.assertEqual(result["status"], "BLOCKED"); self.assertIn("expired", result["detail"])
        self.assertEqual(len(self.adapter.submitted), 2)

    async def test_stage_timeout_fences_and_does_not_claim_cancellation(self):
        self.adapter.hold = {"inventory"}; spec = fixture()
        async with self.worker():
            handle = await self.start(spec); result = await handle.result()
        self.assertEqual(result["status"], "CANCEL_UNCONFIRMED"); self.assertEqual(len(self.adapter.submitted), 1)

    async def test_cancel_during_approval_stops_before_work(self):
        spec = fixture()
        async with self.worker():
            handle = await self.start(spec); await self.wait_phase(handle, "AWAITING_PLAN_APPROVAL")
            await handle.signal(DevelopmentWorkflow.request_cancel, {"request_sha256": spec["request_sha256"], "reason": "Operator requested stop"})
            result = await handle.result()
        self.assertEqual(result["status"], "BLOCKED"); self.assertEqual(len(self.adapter.submitted), 2)
