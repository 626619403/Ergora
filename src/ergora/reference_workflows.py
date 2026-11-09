"""Explicit Temporal inputs; composition extends the frozen six-stage workflow."""

import json

from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from dev_platform.activities import Activities
    from dev_platform.adapter import FileAdapter, ContractViolation
    from dev_platform.workflow import DevelopmentWorkflow, StopWork
    from ergora import task_envelopes


class CompositionAdapter(FileAdapter):
    """Publish only a complete v2 admission matching its execution projection."""

    async def submit(self, context):
        try:
            spec, composition = task_envelopes.unwrap(context['admission'])
            if composition is None or not task_envelopes.matches_context(spec, context):
                raise ValueError('Composition context differs from its complete admission')
        except (ValueError, TypeError, KeyError) as error:
            raise ContractViolation(str(error)) from error
        return await super().submit(context)


class CompositionActivities(Activities):
    @activity.defn(name=task_envelopes.COMPOSITION_SUBMIT)
    async def submit(self, context: dict) -> dict:
        return await super().submit(context)


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
        operation = task_envelopes.COMPOSITION_SUBMIT if name == 'dev_submit' else name
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
            spec, composition = task_envelopes.unwrap(document)
            if composition is None:
                raise ValueError("The composition workflow requires a v2 formal admission envelope")
        except (ValueError, TypeError, KeyError) as error:
            raise ApplicationError(str(error), type="ContractViolation", non_retryable=True) from error
        self.admission = document
        outcome = await super().run(spec)
        return {**outcome, "admission_sha256": document["sha256"]}
