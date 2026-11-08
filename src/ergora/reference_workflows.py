"""Explicit Temporal inputs; composition extends the frozen six-stage workflow."""

from abc import ABC, abstractmethod
import json
from pathlib import Path

from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from dev_platform.activities import Activities
    from dev_platform.adapter import FileAdapter, ContractViolation
    from dev_platform.contracts import canonical_sha
    from dev_platform.workflow import DevelopmentWorkflow, StopWork
    from ergora import task_envelopes


class WorkflowInput(ABC):
    """One original payload and its compatible six-stage execution projection."""

    def __init__(self, document: dict, spec: dict):
        self.document, self.spec = document, spec

    queue_suffix = ''
    requests_suffix = ''

    @classmethod
    @abstractmethod
    def workflow_type(cls):
        """Return this version's registered workflow class."""

    @property
    def entrypoint(self):
        return self.workflow_type().run

    @classmethod
    def task_queue(cls, original: str) -> str:
        return original + cls.queue_suffix

    @classmethod
    def request_root(cls, original: Path) -> Path:
        return original.with_name(original.name + cls.requests_suffix)

    @classmethod
    def activities(cls, config: dict):
        return Activities(FileAdapter(config))

    @classmethod
    def worker(cls, client, queue: str, config: dict):
        from temporalio.worker import Worker

        return Worker(client, task_queue=cls.task_queue(queue), workflows=[cls.workflow_type()],
                      activities=cls.activities(config).registered(), max_concurrent_activities=16)

    async def start(self, client, **options):
        options['task_queue'] = self.task_queue(options['task_queue'])
        return await client.start_workflow(self.entrypoint, self.document, **options)


class LegacyInput(WorkflowInput):
    version = 1

    @classmethod
    def workflow_type(cls):
        return DevelopmentWorkflow


class CompositionInput(WorkflowInput):
    version = 2
    queue_suffix = '.composition-v2'
    requests_suffix = '-composition-v2'

    @classmethod
    def workflow_type(cls):
        return CompositionDevelopmentWorkflow

    @classmethod
    def activities(cls, config: dict):
        return CompositionActivities(CompositionAdapter({**config,
            'requests': str(cls.request_root(Path(config['requests'])))}))


class CompositionAdapter(FileAdapter):
    """Publish only a complete v2 admission matching its execution projection."""

    async def submit(self, context):
        try:
            selected = execution_input(context['admission'])
            if selected.version != 2 or canonical_sha(selected.spec) != canonical_sha(context['spec']):
                raise ValueError('Composition context differs from its complete admission')
            if (context['task_id'] != selected.spec['request']['task_id']
                    or context['profile_sha256'] != selected.spec['profile_sha256']):
                raise ValueError('Composition context identity differs from its complete admission')
        except (ValueError, TypeError, KeyError) as error:
            raise ContractViolation(str(error)) from error
        return await super().submit(context)


class CompositionActivities(Activities):
    @activity.defn(name='ergora_composition_submit')
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


def workers(client, queue: str, config: dict) -> list:
    """Register every supported version through its own construction contract."""
    return [implementation.worker(client, queue, config) for implementation in _INPUTS.values()]


def execution_input(document: dict) -> WorkflowInput:
    """Select a version here; callers use the same original-input interface."""
    spec, composition = task_envelopes.unwrap(document)
    return _INPUTS[2 if composition is not None else 1](document, spec)
