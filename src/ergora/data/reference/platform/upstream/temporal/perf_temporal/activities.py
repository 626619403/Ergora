import asyncio
import hashlib
import json
import re
from temporalio import activity
from temporalio.exceptions import ApplicationError
from .adapter import ClusterAdapter, ApprovalRejected
from .models import (
    Experiment, Job, Observation, GateDecision, ReleaseContext,
    IntegrationTask, Cancellation,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ApplicationError(message, type="ContractViolation", non_retryable=True)


def check_job(job: Job, experiment: Experiment) -> None:
    require(job.binding == experiment.binding, "Job binding mismatch")
    require(bool(job.job_id), "Empty job ID")


class Activities:
    def __init__(self, adapter: ClusterAdapter):
        self.adapter = adapter

    @activity.defn
    async def submit_or_lookup(self, experiment: Experiment) -> Job:
        # Each Temporal retry starts with lookup; never retry blind submission here.
        experiment.validate()
        async with asyncio.timeout(20):
            job = await self.adapter.lookup_job(experiment)
            if job is not None:
                check_job(job, experiment)
                return job
            raw = await self.adapter.read_manifest(experiment.manifest_uri)
            require(len(raw) <= 1_048_576, "Manifest exceeds 1 MiB")
            require(hashlib.sha256(raw).hexdigest() == experiment.binding.manifest_sha,
                    "Manifest bytes do not match manifest_sha")
            try:
                manifest = json.loads(raw)
            except (ValueError, UnicodeError) as error:
                raise ApplicationError("Manifest is not valid JSON", non_retryable=True) from error
            require(isinstance(manifest, dict), "Manifest must be an object")
            for name in ("experiment_id", "candidate_sha", "baseline_sha"):
                require(manifest.get(name) == getattr(experiment.binding, name),
                        f"Manifest {name} mismatch")
            require(isinstance(manifest.get("runner_template_id"), str)
                    and bool(manifest["runner_template_id"]), "Approved runner_template_id required")
            require(manifest.get("max_run_seconds") == experiment.max_run_seconds,
                    "Queue-plus-run lifetime window must match immutable manifest")
            job = await self.adapter.create_job_if_absent(experiment, raw)
            check_job(job, experiment)
            return job

    @activity.defn
    async def poll_job(self, job: Job) -> Observation:
        async with asyncio.timeout(20):
            observation = await self.adapter.poll_job(job)
        require(observation.job == job, "Observation job mismatch")
        require(observation.state in {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"},
                "Unknown scheduler state")
        return observation

    @activity.defn
    async def collect_and_gate(self, job: Job) -> GateDecision:
        async with asyncio.timeout(20):
            result = await self.adapter.collect_and_gate(job)
        require(result.job == job, "Gate result job mismatch")
        require(type(result.passed) is bool, "Gate passed must be boolean")
        require(bool(re.fullmatch(r"[a-f0-9]{64}", result.evidence_sha)), "Invalid evidence digest")
        require(bool(result.report_uri), "Missing gate report")
        return result

    @activity.defn
    async def cancel_exact_job(self, request: Cancellation) -> Job | None:
        async with asyncio.timeout(20):
            job = await self.adapter.fence_and_lookup(request.experiment)
            if job is not None:
                check_job(job, request.experiment)
                await self.adapter.cancel_job_group(job)
            return job

    @activity.defn
    async def create_integration_task(self, context: ReleaseContext) -> IntegrationTask:
        require(context.gate.passed, "Gate did not pass")
        check_job(context.gate.job, context.experiment)
        require(context.request.binding == context.experiment.binding, "Release binding mismatch")
        require(context.request.evidence_sha == context.gate.evidence_sha,
                "Release evidence digest mismatch")
        require(bool(context.request.approval_receipt_id), "Approval receipt required")
        async with asyncio.timeout(20):
            try:
                result = await self.adapter.authorize_release_and_create_task(context)
            except ApprovalRejected as error:
                raise ApplicationError(str(error), type="ApprovalRejected", non_retryable=True) from error
        require(result.binding == context.experiment.binding, "Integration task binding mismatch")
        require(bool(result.task_id) and bool(result.task_url), "Missing integration task")
        return result

    def registered(self):
        return [self.submit_or_lookup, self.poll_job, self.collect_and_gate,
                self.cancel_exact_job, self.create_integration_task]
