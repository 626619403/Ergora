"""Versioned original inputs and their shared native transport/file contract.

Reading an input or a local journal requires only the standard library. SDK and
native implementation imports stay at the operations that actually use them.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from . import task_envelopes


class WorkflowInput(ABC):
    """Keep the original document and its compatible six-stage projection."""

    queue_suffix = ''
    requests_suffix = ''
    submit_activity = 'dev_submit'

    def __init__(self, document: dict, spec: dict):
        self.document, self.spec = document, spec

    @classmethod
    @abstractmethod
    def workflow_type(cls):
        """Return this version's registered SDK workflow class."""

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
    def adapter(cls, config: dict):
        from dev_platform.adapter import FileAdapter

        return FileAdapter(config)

    @classmethod
    def activities(cls, config: dict):
        from dev_platform.activities import Activities

        return Activities(cls.adapter(config))

    @classmethod
    def worker(cls, client, queue: str, config: dict):
        from temporalio.worker import Worker

        return Worker(client, task_queue=cls.task_queue(queue), workflows=[cls.workflow_type()],
                      activities=cls.activities(config).registered(), max_concurrent_activities=16)

    async def start(self, client, **options):
        options['task_queue'] = self.task_queue(options['task_queue'])
        return await client.start_workflow(self.entrypoint, self.document, **options)

    def matches_context(self, context: dict) -> bool:
        return task_envelopes.matches_context(self.spec, context)

    def admission_spec(self, legacy_reader, task_id: str) -> dict:
        """Preserve native v1 reads and their validation/compatibility behavior."""
        return legacy_reader(task_id)

    def require_submission(self) -> None:
        """Refuse unsupported formal execution before dispatch or journal writes."""


class LegacyInput(WorkflowInput):
    version = 1

    @classmethod
    def workflow_type(cls):
        from dev_platform.workflow import DevelopmentWorkflow

        return DevelopmentWorkflow


class CompositionInput(WorkflowInput):
    version = 2
    queue_suffix = '.composition-v2'
    requests_suffix = '-composition-v2'
    submit_activity = task_envelopes.COMPOSITION_SUBMIT

    @classmethod
    def workflow_type(cls):
        from .reference_workflows import CompositionDevelopmentWorkflow

        return CompositionDevelopmentWorkflow

    @classmethod
    def adapter(cls, config: dict):
        from .reference_workflows import CompositionAdapter

        return CompositionAdapter({**config, 'requests': str(cls.request_root(Path(config['requests'])))})

    @classmethod
    def activities(cls, config: dict):
        from .reference_workflows import CompositionActivities

        return CompositionActivities(cls.adapter(config))

    def matches_context(self, context: dict) -> bool:
        return task_envelopes.matches_context(self.spec, context, self.document)

    def admission_spec(self, legacy_reader, task_id: str) -> dict:
        from dev_platform.contracts import validate_spec

        return validate_spec(self.spec)

    def require_submission(self) -> None:
        task_envelopes.review_members(self.document['composition'])


class ReviewRequirementsInput(CompositionInput):
    version = 3
    queue_suffix = '.composition-v3'
    requests_suffix = '-composition-v3'
    submit_activity = task_envelopes.REQUIREMENTS_SUBMIT

    @classmethod
    def workflow_type(cls):
        from .reference_workflows import ReviewRequirementsWorkflow

        return ReviewRequirementsWorkflow

    @classmethod
    def adapter(cls, config: dict):
        from .reference_workflows import ReviewRequirementsAdapter

        return ReviewRequirementsAdapter({**config, 'requests': str(cls.request_root(Path(config['requests'])))})

    @classmethod
    def activities(cls, config: dict):
        from .reference_workflows import ReviewRequirementsActivities

        return ReviewRequirementsActivities(cls.adapter(config))


_INPUTS = {1: LegacyInput, 2: CompositionInput, 3: ReviewRequirementsInput}


def workers(client, queue: str, config: dict) -> list:
    """Register every supported version through its own construction contract."""
    return [implementation.worker(client, queue, config) for implementation in _INPUTS.values()]


def request_roots(original: Path) -> tuple[Path, ...]:
    """The registered input versions own the executor's request namespaces."""
    return tuple(implementation.request_root(original) for implementation in _INPUTS.values())


def execution_input(document: dict) -> WorkflowInput:
    """Select here; transport and file readers use the same original-input interface."""
    spec, composition = task_envelopes.unwrap(document)
    return _INPUTS[document['schema_version'] if composition is not None else 1](document, spec)
