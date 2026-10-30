import asyncio
from dataclasses import replace
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError, ActivityError

with workflow.unsafe.imports_passed_through():
    from .models import (
        Experiment, Job, Observation, GateDecision, ReleaseRequest, ReleaseContext,
        IntegrationTask, CancelRequest, Cancellation, Status, Outcome,
    )


# Temporal alone retries short control-plane operations. Never retries a failed GPU run.
ACTIVITY_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=2), backoff_coefficient=2,
    maximum_interval=timedelta(seconds=10), maximum_attempts=3,
    non_retryable_error_types=["ContractViolation", "AdapterNotConfigured", "ValueError", "ApprovalRejected"],
)


@workflow.defn
class ExperimentWorkflow:
    def __init__(self):
        self.experiment: Experiment | None = None
        self.job: Job | None = None
        self.gate: GateDecision | None = None
        self.release: ReleaseRequest | None = None
        self.processed_receipts: set[str] = set()
        self.cancel_reason: str | None = None
        self.phase = "INITIALIZING"
        self.last_signal_rejection: str | None = None

    @workflow.query
    def status(self) -> Status:
        return Status(self.phase, self.experiment.binding if self.experiment else None,
                      self.job.job_id if self.job else None,
                      self.gate.evidence_sha if self.gate else None, self.last_signal_rejection)

    @workflow.signal
    def request_release(self, request: ReleaseRequest) -> None:
        # This is consistency checking, NOT authentication. An activity verifies the receipt.
        if (self.experiment is None or self.gate is None or not self.gate.passed
                or self.phase != "AWAITING_RELEASE" or self.cancel_reason is not None
                or request.binding != self.experiment.binding
                or request.evidence_sha != self.gate.evidence_sha
                or not request.approval_receipt_id
                or request.approval_receipt_id in self.processed_receipts):
            self.last_signal_rejection = "Release ignored: wrong phase, binding, evidence or receipt"
            return
        if self.release is None:
            self.release = request
            self.last_signal_rejection = None

    @workflow.signal
    def request_cancel(self, request: CancelRequest) -> None:
        if (self.experiment is None or request.binding != self.experiment.binding
                or not request.reason.strip()):
            self.last_signal_rejection = "Cancel ignored: binding or reason mismatch"
            return
        self.cancel_reason = request.reason[:1000]

    async def call(self, name, value, result_type):
        return await workflow.execute_activity(
            name, value, result_type=result_type,
            start_to_close_timeout=timedelta(seconds=30),
            schedule_to_close_timeout=timedelta(minutes=3),
            retry_policy=ACTIVITY_RETRY,
        )

    async def pause(self, seconds: float) -> None:
        try:
            await workflow.wait_condition(lambda: self.cancel_reason is not None,
                                          timeout=timedelta(seconds=seconds))
        except asyncio.TimeoutError:
            pass

    async def cancel_and_confirm(self, experiment: Experiment) -> Outcome:
        self.phase = "CANCELLING"
        self.job = await self.call("cancel_exact_job",
                                  Cancellation(experiment, self.cancel_reason or "cancelled"),
                                  Job | None)
        if self.job is None:
            self.phase = "CANCELLED"
            return Outcome("CANCELLED", experiment.binding,
                           detail=f"Fenced before any job existed; reason={self.cancel_reason}")
        deadline = workflow.now() + timedelta(seconds=experiment.cancel_wait_seconds)
        while workflow.now() < deadline:
            observation = await self.call("poll_job", self.job, Observation)
            if observation.state in {"CANCELLED", "FAILED", "SUCCEEDED"}:
                self.phase = "CANCELLED"
                return Outcome("CANCELLED", experiment.binding, self.job.job_id,
                               detail=f"Release suppressed; scheduler ended as {observation.state}; "
                                      f"reason={self.cancel_reason}")
            # A durable timer; no worker/thread/GPU reservation is held during this wait.
            await workflow.sleep(timedelta(seconds=experiment.poll_seconds))
        self.phase = "CANCEL_UNCONFIRMED"
        return Outcome("CANCEL_UNCONFIRMED", experiment.binding, self.job.job_id,
                       detail="Operator must reconcile exact job; scheduler walltime remains required; "
                              f"reason={self.cancel_reason}")

    @workflow.run
    async def run(self, experiment: Experiment) -> Outcome:
        try:
            experiment.validate()
        except ValueError as error:
            raise ApplicationError(str(error), non_retryable=True) from error
        self.experiment = experiment
        try:
            if self.cancel_reason is not None:
                return await self.cancel_and_confirm(experiment)
            self.phase = "SUBMITTING"
            self.job = await self.call("submit_or_lookup", experiment, Job)
            # Legacy field name: QUEUED time is intentionally included. The runner
            # independently enforces a scheduler execution-only hard walltime.
            job_lifetime_deadline = workflow.now() + timedelta(seconds=experiment.max_run_seconds)
            while True:
                if self.cancel_reason is not None:
                    return await self.cancel_and_confirm(experiment)
                observation = await self.call("poll_job", self.job, Observation)
                self.phase = observation.state
                if observation.state == "SUCCEEDED":
                    break
                if observation.state in {"FAILED", "CANCELLED"}:
                    return Outcome(observation.state, experiment.binding, self.job.job_id,
                                   detail=observation.detail)
                if workflow.now() >= job_lifetime_deadline:
                    self.cancel_reason = "Queue-plus-run lifetime exceeded after submission confirmation"
                    return await self.cancel_and_confirm(experiment)
                await self.pause(experiment.poll_seconds)
            self.phase = "GATING"
            self.gate = await self.call("collect_and_gate", self.job, GateDecision)
            if self.cancel_reason is not None:
                return await self.cancel_and_confirm(experiment)
            if not self.gate.passed:
                self.phase = "GATE_FAILED"
                return Outcome("GATE_FAILED", experiment.binding, self.job.job_id,
                               self.gate.report_uri, detail=self.gate.summary)
            release_deadline = workflow.now() + timedelta(seconds=experiment.release_wait_seconds)
            while True:
                if self.cancel_reason is not None:
                    return await self.cancel_and_confirm(experiment)
                self.phase = "AWAITING_RELEASE"
                remaining = release_deadline - workflow.now()
                try:
                    if remaining <= timedelta(0):
                        raise asyncio.TimeoutError
                    await workflow.wait_condition(
                        lambda: self.release is not None or self.cancel_reason is not None,
                        timeout=remaining,
                    )
                except asyncio.TimeoutError:
                    self.phase = "RELEASE_EXPIRED"
                    return Outcome("RELEASE_EXPIRED", experiment.binding, self.job.job_id,
                                   self.gate.report_uri)
                if self.cancel_reason is not None:
                    return await self.cancel_and_confirm(experiment)
                assert self.release is not None
                request = self.release
                self.release = None
                self.processed_receipts.add(request.approval_receipt_id)
                self.phase = "CREATING_INTEGRATION_TASK"
                try:
                    task = await self.call("create_integration_task",
                                           ReleaseContext(experiment, self.gate, request),
                                           IntegrationTask)
                except ActivityError as error:
                    if isinstance(error.cause, ApplicationError) and error.cause.type == "ApprovalRejected":
                        self.last_signal_rejection = f"Approval rejected: {error.cause}"
                        # Keep the original deadline and GPU job; accept only a NEW receipt.
                        continue
                    raise
                # A ticket can race a later cancellation; it never merges or deploys anything.
                self.phase = "INTEGRATION_TASK_CREATED"
                return Outcome(self.phase, experiment.binding, self.job.job_id,
                               self.gate.report_uri, task.task_url)
        except asyncio.CancelledError:
            # Native Temporal cancellation also tries exact-job cleanup. Termination cannot.
            self.cancel_reason = self.cancel_reason or "Native Temporal cancellation"
            await asyncio.shield(self.cancel_and_confirm(experiment))
            raise
        except ActivityError as error:
            original_failure = f"Control activity failed: {error}; cause={error.cause}"
            if self.cancel_reason is not None:
                if self.phase == "CANCELLING":
                    # The bounded cleanup itself exhausted retries; do not retry it again.
                    self.phase = "CANCEL_UNCONFIRMED"
                    return Outcome(self.phase, experiment.binding,
                                   self.job.job_id if self.job else None, detail=original_failure)
                try:
                    outcome = await self.cancel_and_confirm(experiment)
                except ActivityError as cleanup_error:
                    self.phase = "CANCEL_UNCONFIRMED"
                    return Outcome(self.phase, experiment.binding,
                                   self.job.job_id if self.job else None,
                                   detail=f"{original_failure}; cancellation cleanup failed: "
                                          f"{cleanup_error}; cause={cleanup_error.cause}")
                return replace(outcome, detail=f"{outcome.detail}; {original_failure}")
            # Never silently re-run the GPU job or claim a successful cleanup.
            self.phase = "NEEDS_RECONCILIATION"
            raise
