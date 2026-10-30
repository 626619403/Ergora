"""Implement this protocol against the EXISTING runner/scheduler. Never shell user input.

Every method must finish within 20 seconds (or raise). GPU work is an external job.
The runner owns a durable, atomic experiment-id registry: immutable binding,
job identity, and cancellation fence. It is not another workflow/retry engine.
"""
from typing import Protocol
from .models import Experiment, Job, Observation, GateDecision, ReleaseContext, IntegrationTask


class AdapterNotConfigured(RuntimeError):
    pass


class ContractViolation(RuntimeError):
    pass


class ApprovalRejected(RuntimeError):
    """Definitive receipt denial BEFORE any ticket side effect; a new receipt may be tried."""


class ClusterAdapter(Protocol):
    async def read_manifest(self, uri: str) -> bytes:
        """Read only from allowed artifact stores; enforce size limits and URI policy."""
        ...

    async def lookup_job(self, experiment: Experiment) -> Job | None:
        """Query durable experiment registry, including completed and tombstoned entries.
        Reject a previously registered different binding, including after Temporal retention.
        """
        ...

    async def create_job_if_absent(self, experiment: Experiment, manifest: bytes) -> Job:
        """ATOMIC create with experiment_id as idempotency key. Return the existing job.
        Bind manifest+candidate+baseline; reject conflicts and cancellation fences.
        Persist scheduler ID; reconcile an uncertain previous submission, never blindly
        issue sbatch/create again. Enforce runner template allowlist and its independent
        scheduler execution walltime. max_run_seconds is a workflow queue+run window.
        Disable scheduler/application auto-resubmit: Temporal is the sole retry owner.
        """
        ...

    async def poll_job(self, job: Job) -> Observation:
        """Read exact parent/job-group state. Missing/unavailable is an error, not success."""
        ...

    async def collect_and_gate(self, job: Job) -> GateDecision:
        """Verify immutable run artifacts and preset gates; return bound evidence hash.
        Fail closed if logs, numerical tests, baseline, whole-update metrics or provenance
        required by the manifest are absent. Do not let the candidate edit the validator.
        """
        ...

    async def fence_and_lookup(self, experiment: Experiment) -> Job | None:
        """Atomically fence this experiment against future submits, reconcile in-flight
        creates, and return its exact job. None means no job can appear later. If the
        scheduler outcome is still ambiguous, RAISE; do not pretend cancellation succeeded.
        """
        ...

    async def cancel_job_group(self, job: Job) -> None:
        """Idempotently request cancellation of ONLY this exact scheduler group and ranks.
        Verify its owner/binding. No pkill, scancel -u, wildcard, or all-jobs operation.
        """
        ...

    async def authorize_release_and_create_task(self, context: ReleaseContext) -> IntegrationTask:
        """Verify receipt via trusted approval service (identity, role, expiry, revocation,
        binding and evidence hash). Recheck baseline/current policy, then idempotently
        create an integration/revalidation TICKET keyed by experiment ID + evidence SHA.
        Retry must retrieve the same ticket, never deploy/merge/start a training job.
        A caller-supplied name, boolean, or receipt string alone is NOT authorization.
        Raise ApprovalRejected for definitive authorization denial BEFORE creating any
        ticket. This returns the workflow to its ORIGINAL release deadline; a different
        receipt may then be submitted. Network/unknown-side-effect failures are not denials.
        Baseline/contract drift is ContractViolation, NOT a correctable receipt rejection;
        it requires reconciliation and a new bound experiment/revalidation.
        """
        ...


def load_adapter() -> ClusterAdapter:
    import importlib
    import os
    factory_path = os.environ.get("PERF_CLUSTER_ADAPTER", "")
    if not factory_path or ":" not in factory_path:
        raise AdapterNotConfigured(
            "Set PERF_CLUSTER_ADAPTER=your_package.module:create_adapter after implementing "
            "the protocol. No cluster adapter or approval verifier is bundled."
        )
    module, factory = factory_path.split(":", 1)
    return getattr(importlib.import_module(module), factory)()
