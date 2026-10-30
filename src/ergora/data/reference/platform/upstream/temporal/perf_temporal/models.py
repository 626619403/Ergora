from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Binding:
    experiment_id: str
    manifest_sha: str
    candidate_sha: str
    baseline_sha: str

    def validate(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", self.experiment_id):
            raise ValueError("Invalid experiment_id")
        if not re.fullmatch(r"[a-f0-9]{64}", self.manifest_sha):
            raise ValueError("manifest_sha must be the SHA-256 of the exact manifest bytes")
        for value in (self.candidate_sha, self.baseline_sha):
            if not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", value):
                raise ValueError("candidate_sha and baseline_sha must be full Git object IDs")


@dataclass(frozen=True)
class Experiment:
    binding: Binding
    manifest_uri: str
    poll_seconds: int = 60
    # Legacy name: total QUEUED + RUNNING window after submit/lookup confirmation.
    # The scheduler's execution-only hard walltime is independently set by the runner.
    max_run_seconds: int = 21600
    release_wait_seconds: int = 86400
    cancel_wait_seconds: int = 600

    def validate(self) -> None:
        self.binding.validate()
        if not self.manifest_uri:
            raise ValueError("manifest_uri is required")
        if not 30 <= self.poll_seconds <= 300:
            raise ValueError("poll_seconds must be 30..300")
        if not 60 <= self.max_run_seconds <= 86400:
            raise ValueError("max_run_seconds must be 60..86400")
        if not 60 <= self.release_wait_seconds <= 604800:
            raise ValueError("release_wait_seconds must be 60..604800")
        if not 30 <= self.cancel_wait_seconds <= 3600:
            raise ValueError("cancel_wait_seconds must be 30..3600")


def workflow_id(binding: Binding) -> str:
    # One immutable experiment ID, not a new workflow for every client retry.
    return f"perf-experiment/{binding.experiment_id}"


@dataclass(frozen=True)
class Job:
    binding: Binding
    job_id: str  # exact scheduler parent/job-group ID, never a user or name pattern


@dataclass(frozen=True)
class Observation:
    job: Job
    state: str  # QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED
    detail: str = ""


@dataclass(frozen=True)
class GateDecision:
    job: Job
    passed: bool
    evidence_sha: str
    report_uri: str
    summary: str


@dataclass(frozen=True)
class ReleaseRequest:
    binding: Binding
    evidence_sha: str
    approval_receipt_id: str  # verified against an external authenticated approval service


@dataclass(frozen=True)
class ReleaseContext:
    experiment: Experiment
    gate: GateDecision
    request: ReleaseRequest


@dataclass(frozen=True)
class IntegrationTask:
    binding: Binding
    task_id: str
    task_url: str


@dataclass(frozen=True)
class CancelRequest:
    binding: Binding
    reason: str


@dataclass(frozen=True)
class Cancellation:
    experiment: Experiment
    reason: str


@dataclass(frozen=True)
class Status:
    phase: str
    binding: Binding | None
    job_id: str | None
    evidence_sha: str | None
    last_signal_rejection: str | None


@dataclass(frozen=True)
class Outcome:
    status: str
    binding: Binding
    job_id: str | None = None
    report_uri: str | None = None
    integration_task_url: str | None = None
    detail: str = ""
