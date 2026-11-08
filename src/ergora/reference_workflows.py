"""Explicit Temporal inputs; composition extends the frozen six-stage workflow."""

from abc import ABC, abstractmethod
import json

from temporalio import workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from dev_platform.workflow import DevelopmentWorkflow, StopWork
    from ergora import task_envelopes


class WorkflowInput(ABC):
    """One original payload and its compatible six-stage execution projection."""

    def __init__(self, document: dict, spec: dict):
        self.document, self.spec = document, spec

    @property
    @abstractmethod
    def entrypoint(self):
        """Return this version's registered workflow run method."""

    async def start(self, client, **options):
        return await client.start_workflow(self.entrypoint, self.document, **options)


class LegacyInput(WorkflowInput):
    version = 1

    @property
    def entrypoint(self):
        return DevelopmentWorkflow.run


class CompositionInput(WorkflowInput):
    version = 2

    @property
    def entrypoint(self):
        return CompositionDevelopmentWorkflow.run


@workflow.defn(name="ErgoraCompositionWorkflowV2")
class CompositionDevelopmentWorkflow(DevelopmentWorkflow):
    """Keep the original scheduler while binding every stage to its admission."""

    def __init__(self):
        super().__init__()
        self.admission = None

    @workflow.query
    def status(self) -> dict:
        return {**super().status(), "admission_sha256": self.admission["sha256"] if self.admission else None}

    async def call(self, name, value, result_type=dict):
        # Only a version-aware worker may publish composition requests. A legacy
        # worker on the same queue must never turn these into single-agent jobs.
        operation = "ergora_composition_submit" if name == "dev_submit" else name
        return await super().call(operation, value, result_type)

    def context(self, stage, expected_sha=None, unit=None, dependencies=None):
        context = {**super().context(stage, expected_sha, unit, dependencies), "admission": self.admission}
        content = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(content) > 1_000_000:
            raise StopWork("Complete composition stage context exceeds 1,000,000 bytes; split the task")
        return context

    @workflow.run
    async def run(self, document: dict) -> dict:
        try:
            selected = execution_input(document)
            if selected.version != 2:
                raise ValueError("The composition workflow requires a v2 formal admission envelope")
        except (ValueError, TypeError, KeyError) as error:
            raise ApplicationError(str(error), type="ContractViolation", non_retryable=True) from error
        self.admission = document
        outcome = await super().run(selected.spec)
        return {**outcome, "admission_sha256": document["sha256"]}


_INPUTS = {1: LegacyInput, 2: CompositionInput}


def execution_input(document: dict) -> WorkflowInput:
    """Select a version here; callers use the same original-input interface."""
    spec, composition = task_envelopes.unwrap(document)
    return _INPUTS[2 if composition is not None else 1](document, spec)
