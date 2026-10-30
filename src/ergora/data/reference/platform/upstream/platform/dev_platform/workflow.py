"""One durable workflow for both development task templates.

The workflow orchestrates trusted external executors. It never executes arbitrary
repository commands, merges changes, or claims a review receipt is authentication.
"""
import asyncio
import json
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, ApplicationError

with workflow.unsafe.imports_passed_through():
    from .contracts import canonical_sha, validate_spec

RETRY = RetryPolicy(initial_interval=timedelta(seconds=1), maximum_interval=timedelta(seconds=5),
                    maximum_attempts=3, non_retryable_error_types=["ContractViolation", "ApprovalRejected", "AdapterNotConfigured", "ValueError"])


class StopWork(Exception): pass


def workflow_id(spec): return "dev-task/" + spec["request"]["task_id"]


@workflow.defn
class DevelopmentWorkflow:
    def __init__(self):
        self.spec = None
        self.phase = "INITIALIZING"
        self.results = {}
        self.plan_sha256 = None
        self.pending_approval = None
        self.approved_plan = None
        self.used_receipts = set()
        self.cancel_reason = None
        self.last_rejection = None
        self.candidate_sha = None
        self.active_stages = []

    @workflow.query
    def status(self) -> dict:
        return {"phase": self.phase, "task_id": self.spec["request"]["task_id"] if self.spec else None,
                "request_sha256": self.spec["request_sha256"] if self.spec else None,
                "plan_sha256": self.plan_sha256, "candidate_sha": self.candidate_sha,
                "completed_stages": sorted(self.results), "active_stages": sorted(self.active_stages),
                "last_rejection": self.last_rejection}

    @workflow.signal
    def approve_plan(self, signal: dict):
        if (not self.spec or self.phase != "AWAITING_PLAN_APPROVAL" or self.cancel_reason
                or signal.get("request_sha256") != self.spec["request_sha256"]
                or signal.get("plan_sha256") != self.plan_sha256
                or not isinstance(signal.get("receipt_id"), str) or not signal["receipt_id"]
                or signal["receipt_id"] in self.used_receipts):
            self.last_rejection = "Approval ignored: wrong phase, request, plan digest, or reused receipt"
            return
        if self.pending_approval is None:
            self.pending_approval = signal
            self.last_rejection = None

    @workflow.signal
    def request_cancel(self, signal: dict):
        if not self.spec or signal.get("request_sha256") != self.spec["request_sha256"] or not isinstance(signal.get("reason"), str) or not signal["reason"].strip():
            self.last_rejection = "Cancellation ignored: request binding/reason mismatch"
            return
        self.cancel_reason = signal["reason"][:1000]

    async def call(self, name, value, result_type=dict):
        return await workflow.execute_activity(name, value, result_type=result_type,
                    start_to_close_timeout=timedelta(seconds=30),
                    schedule_to_close_timeout=timedelta(minutes=3), retry_policy=RETRY)

    def authors(self):
        receipts = [value for key, value in self.results.items() if key not in {"verify", "review"} and "actor" in value]
        return sorted({r["actor"]["id"] for r in receipts}), sorted({r["actor"]["session_id"] for r in receipts})

    def context(self, stage, expected_sha=None, unit=None, dependencies=None):
        spec = self.spec; request = spec["request"]
        ids, sessions = self.authors()
        context = {"task_id": request["task_id"], "request_sha256": spec["request_sha256"],
                   "profile_sha256": spec["profile_sha256"], "spec": spec, "stage": stage,
                   "expected_candidate_sha": expected_sha, "unit": unit,
                   "dependencies": dependencies or {}, "author_ids": ids, "author_sessions": sessions}
        if self.approved_plan is not None:
            context["approved_plan"] = self.approved_plan
        context["job_id"] = request["task_id"] + "-" + canonical_sha({"stage": stage})[:24]
        # Check before activity serialization to remain below the Temporal payload ceiling.
        encoded = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if len(encoded) > 1_000_000:
            raise StopWork("Stage context exceeds 1,000,000 bytes; reduce metadata, use artifact references, or split the task")
        return context

    async def stage(self, stage, expected_sha=None, unit=None, dependencies=None):
        if self.cancel_reason: raise StopWork(self.cancel_reason)
        self.active_stages.append(stage)
        try:
            job = await self.call("dev_submit", self.context(stage, expected_sha, unit, dependencies))
            deadline = workflow.now() + timedelta(seconds=self.spec["profile"]["stage_timeout_seconds"])
            while True:
                if self.cancel_reason: raise StopWork(self.cancel_reason)
                receipt = await self.call("dev_poll", job, dict | None)
                if receipt is not None:
                    if receipt["state"] != "SUCCEEDED":
                        self.cancel_reason = "Stage " + stage + " ended as " + receipt["state"]
                        raise StopWork(self.cancel_reason)
                    self.results[stage] = receipt
                    return receipt
                remaining = (deadline - workflow.now()).total_seconds()
                if remaining <= 0:
                    self.cancel_reason = "Stage deadline exceeded: " + stage
                    raise StopWork(self.cancel_reason)
                try:
                    await workflow.wait_condition(lambda: self.cancel_reason is not None,
                        timeout=timedelta(seconds=min(self.spec["profile"]["poll_seconds"], remaining)))
                except asyncio.TimeoutError: pass
        finally:
            self.active_stages.remove(stage)

    async def approval(self):
        deadline = workflow.now() + timedelta(seconds=self.spec["profile"]["approval_timeout_seconds"])
        while True:
            self.phase = "AWAITING_PLAN_APPROVAL"
            if self.cancel_reason: raise StopWork(self.cancel_reason)
            remaining = deadline - workflow.now()
            if remaining <= timedelta(0): raise StopWork("Human plan approval expired")
            try:
                await workflow.wait_condition(lambda: self.pending_approval is not None or self.cancel_reason is not None, timeout=remaining)
            except asyncio.TimeoutError: raise StopWork("Human plan approval expired")
            if self.cancel_reason: raise StopWork(self.cancel_reason)
            signal = self.pending_approval; self.pending_approval = None
            self.used_receipts.add(signal["receipt_id"])
            context = {"task_id": self.spec["request"]["task_id"], "request_sha256": self.spec["request_sha256"],
                       "profile_sha256": self.spec["profile_sha256"], "plan_sha256": self.plan_sha256,
                       "receipt_id": signal["receipt_id"]}
            try:
                result = await self.call("dev_authorize_plan", context)
                self.results["plan-approval"] = result
                return
            except ActivityError as error:
                if isinstance(error.cause, ApplicationError) and error.cause.type == "ApprovalRejected":
                    self.last_rejection = "Approval receipt rejected: " + str(error.cause)
                    continue
                raise

    async def units(self):
        units = self.spec["request"]["input"]["work_units"]
        remaining = {u["id"]: u for u in units}
        completed = set()
        concurrency = self.spec["profile"]["limits"]["max_parallel_units"]
        running = {}
        try:
            while remaining or running:
                if self.cancel_reason: raise StopWork(self.cancel_reason)
                ready = [u for u in remaining.values() if set(u["depends_on"]) <= completed]
                for unit in sorted(ready, key=lambda u: u["id"])[:concurrency - len(running)]:
                    # Dependencies carry exact parent commits; executor creates an isolated worktree.
                    dependencies = {key: self.results["work:" + key] for key in unit["depends_on"]}
                    task = asyncio.create_task(self.stage("work:" + unit["id"], unit=unit, dependencies=dependencies))
                    running[unit["id"]] = task; del remaining[unit["id"]]
                if not running: raise StopWork("No runnable work unit; dependency graph cannot progress")
                await workflow.wait(running.values(), return_when=asyncio.FIRST_COMPLETED)
                for key in sorted(list(running)):
                    if running[key].done():
                        await running.pop(key)
                        completed.add(key)
        finally:
            for task in running.values(): task.cancel()
            if running: await asyncio.gather(*running.values(), return_exceptions=True)

    async def stop(self, reason):
        self.phase = "FENCING"
        try:
            result = await self.call("dev_fence", {"task_id": self.spec["request"]["task_id"], "request_sha256": self.spec["request_sha256"]})
            self.phase = "BLOCKED" if result.get("confirmed") else "CANCEL_UNCONFIRMED"
            return {"status": self.phase, "task_id": self.spec["request"]["task_id"],
                    "request_sha256": self.spec["request_sha256"], "candidate_sha": self.candidate_sha,
                    "detail": reason, "fence": result}
        except ActivityError as error:
            self.phase = "NEEDS_RECONCILIATION"
            return {"status": self.phase, "task_id": self.spec["request"]["task_id"],
                    "request_sha256": self.spec["request_sha256"], "candidate_sha": self.candidate_sha,
                    "detail": reason + "; unable to confirm fence: " + str(error)}

    @workflow.run
    async def run(self, spec: dict) -> dict:
        try: validate_spec(spec)
        except ValueError as error: raise ApplicationError(str(error), type="ContractViolation", non_retryable=True) from error
        self.spec = spec; self.candidate_sha = spec["request"]["repository"]["starting_sha"]
        try:
            await self.call("dev_validate", spec)
            self.phase = "INVENTORY"
            inventory = await self.stage("inventory", self.candidate_sha)
            self.phase = "PLANNING"
            plan = await self.stage("plan", self.candidate_sha, dependencies={"inventory": inventory})
            self.plan_sha256 = canonical_sha(plan)
            await self.approval()
            # The plan receipt is authority metadata, not an agent author receipt.
            approval_receipt = self.results.pop("plan-approval")
            self.approved_plan = {"plan_sha256": self.plan_sha256, "receipt": plan, "approval": approval_receipt}
            self.phase = "IMPLEMENTING"
            await self.units()
            self.phase = "INTEGRATING"
            integrated = await self.stage("integrate", dependencies={k: v for k, v in self.results.items() if k.startswith("work:")})
            self.candidate_sha = integrated["candidate_sha"]
            self.phase = "VERIFYING"
            verification = await self.stage("verify", self.candidate_sha, dependencies={"integration": integrated})
            self.phase = "REVIEWING"
            review = await self.stage("review", self.candidate_sha, dependencies={"verification": verification, "plan": plan})
            if self.cancel_reason: raise StopWork(self.cancel_reason)
            self.phase = "REVIEW_READY"
            return {"status": self.phase, "task_id": spec["request"]["task_id"], "task_type": spec["request"]["task_type"],
                    "request_sha256": spec["request_sha256"], "profile_sha256": spec["profile_sha256"],
                    "base_sha": spec["request"]["repository"]["base_sha"], "candidate_sha": self.candidate_sha,
                    "plan_sha256": self.plan_sha256, "plan_approval": approval_receipt,
                    "evidence_sha256": canonical_sha({"verification": verification, "review": review}),
                    "verification": verification, "review": review,
                    "detail": "Ready for human merge review. Revalidate against current target branch and current policy before merge; no merge or deployment was performed."}
        except StopWork as error:
            return await self.stop(str(error))
        except ActivityError as error:
            return await self.stop("Control activity failed: " + str(error.cause))
        except asyncio.CancelledError:
            return await asyncio.shield(self.stop("Native Temporal cancellation; external jobs require confirmed fences/terminal receipts"))
