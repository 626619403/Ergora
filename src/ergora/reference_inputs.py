"""Versioned original inputs and their shared native transport/file contract.

Reading an input or a local journal requires only the standard library. SDK and
native implementation imports stay at the operations that actually use them.
"""

from abc import ABC, abstractmethod
import json
from pathlib import Path

from . import task_envelopes


class WorkflowInput(ABC):
    """Keep the original document and its compatible six-stage projection."""

    queue_suffix = ''
    requests_suffix = ''
    submit_activity = 'dev_submit'
    artifact_protocol = None
    complete_resources = False
    execution_enabled = True

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

    def admission_report(self, original_report, selection: dict) -> dict:
        """Keep the original installation-wide prerequisites for existing inputs."""
        return original_report()

    def require_submission(self) -> None:
        """Refuse unsupported formal execution before dispatch or journal writes."""

    def stage_material(self) -> dict:
        """Additional frozen task data outside the structural resource tree."""
        return {}

    def evidence_contract(self) -> dict:
        """Additional original input bytes needed by the offline evidence reader."""
        return {}


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


class ReviewDAGInput(ReviewRequirementsInput):
    version = 4
    queue_suffix = '.composition-v4'
    requests_suffix = '-composition-v4'
    submit_activity = task_envelopes.DAG_SUBMIT

    @classmethod
    def workflow_type(cls):
        from .reference_workflows import ReviewDAGWorkflow

        return ReviewDAGWorkflow

    @classmethod
    def adapter(cls, config: dict):
        from .reference_workflows import ReviewDAGAdapter

        return ReviewDAGAdapter({**config, 'requests': str(cls.request_root(Path(config['requests'])))})

    @classmethod
    def activities(cls, config: dict):
        from .reference_workflows import ReviewDAGActivities

        return ReviewDAGActivities(cls.adapter(config))


class WorkDeliveryInput(ReviewDAGInput):
    version = 5
    queue_suffix = '.composition-v5'
    requests_suffix = '-composition-v5'
    submit_activity = task_envelopes.WORK_SUBMIT

    @classmethod
    def workflow_type(cls):
        from .reference_workflows import WorkDeliveryWorkflow

        return WorkDeliveryWorkflow

    @classmethod
    def adapter(cls, config: dict):
        from .reference_workflows import WorkDeliveryAdapter

        return WorkDeliveryAdapter({**config, 'requests': str(cls.request_root(Path(config['requests'])))})

    @classmethod
    def activities(cls, config: dict):
        from .reference_workflows import WorkDeliveryActivities

        return WorkDeliveryActivities(cls.adapter(config))

    def require_submission(self) -> None:
        super().require_submission()
        task_envelopes.work_delivery(self.document['composition'], self.spec)


class StageResultsInput(WorkDeliveryInput):
    version = 6
    queue_suffix = '.composition-v6'
    requests_suffix = '-composition-v6'
    artifact_protocol = 'stage-artifacts-v1'

    @classmethod
    def workflow_type(cls):
        from .reference_workflows import StageResultsWorkflow

        return StageResultsWorkflow

    @classmethod
    def adapter(cls, config: dict):
        from .reference_workflows import StageResultsAdapter

        return StageResultsAdapter({**config, 'requests': str(cls.request_root(Path(config['requests'])))})


class IssueSourceInput(StageResultsInput):
    version = 7
    queue_suffix = '.composition-v7'
    requests_suffix = '-composition-v7'

    @classmethod
    def workflow_type(cls):
        from .reference_workflows import IssueSourceWorkflow

        return IssueSourceWorkflow

    @classmethod
    def adapter(cls, config: dict):
        from .reference_workflows import IssueSourceAdapter

        return IssueSourceAdapter({**config, 'requests': str(cls.request_root(Path(config['requests'])))})

    def admission_report(self, original_report, selection: dict) -> dict:
        preparation = [(stage, {'role': self.spec['profile']['roles'][stage],
            'binding': selection['bindings'][self.spec['profile']['roles'][stage]], 'mode': 'native'})
            for stage in ('inventory', 'plan')]
        return _selected_prerequisites(self, selection, preparation)

    def stage_material(self) -> dict:
        return {'issue_source': self.document['issue_source']}

    def evidence_contract(self) -> dict:
        return {'original_input': self.document, 'original_input_sha256': task_envelopes.identity(self.document)}


def _selected_prerequisites(selected_input, selection: dict, preparation: list) -> dict:
    """Probe the actual frozen programs, sharing the v7/v8 local admission owner."""
    from agent_platform.core import Blocked, CONFIG, PYTHON, settings
    from agent_platform.sandbox import Sandbox
    from . import agent_backends, agents, processes, task_mcp

    config = settings()
    boundary = Sandbox().probe()
    checks = {
        'automatic-executor': {'status': 'ready' if config.get('execution_enabled') is True else 'disabled'},
        'execution-boundary': {**boundary, 'status': 'ready' if boundary['available'] else 'blocked'},
    }
    cwd = Path(selection['configuration']['project']['repo'])
    for name, program in (('git', '/usr/bin/git'), ('timeout', '/usr/bin/timeout'), ('python', str(PYTHON))):
        try:
            checks[name] = {'status': 'ready', 'executable': processes.resolve_program(program, cwd)}
        except (OSError, ValueError) as error:
            checks[name] = {'status': 'missing', 'detail': str(error)}

    selected = list(preparation)
    composition = selected_input.document['composition']
    selected.extend(('work:' + path, member) for path, member in composition['execution']['members'].items())
    selected.extend(('review:' + path, member) for path, member in composition['members'].items())
    for name, member in selected:
        binding, mode = member['binding'], member['mode']
        try:
            agents.validate_binding(member['role'], binding, formal=True)
            backend = agent_backends.for_binding(binding, {'codex': {
                'config': CONFIG / 'codex.toml', 'executable': config.get('codex_bin') or 'codex'}})
            backend.check_invocation()
            backend.check_mode(mode)
            if mode != 'native' and backend.composition_policy(mode) != member['policy']:
                raise ValueError('Frozen composition policy differs from the current backend contract')
            if not backend.available(cwd):
                raise ValueError('Selected executable is unavailable: ' + backend.executable())
            checks[name] = {'status': 'ready', 'tool': binding['tool'], 'mode': mode,
                            'executable': backend.executable()}
        except (OSError, ValueError, ImportError) as error:
            checks[name] = {'status': 'blocked', 'tool': binding['tool'], 'mode': mode, 'detail': str(error)}
    if any(member['mode'] in ('task-mcp', 'workspace-task-mcp') for _, member in selected):
        try:
            task_mcp.check_available()
            checks['task-mcp'] = {'status': 'ready'}
        except (OSError, ValueError, ImportError) as error:
            checks['task-mcp'] = {'status': 'blocked', 'detail': str(error)}
    failed = {name: check for name, check in checks.items() if check['status'] != 'ready'}
    if failed:
        raise Blocked('Selected task prerequisites incomplete: ' + json.dumps(failed, ensure_ascii=False))
    return {'checks': checks, 'ready_for_real_tasks': True,
            'scope': 'Selected local programs/configuration and acknowledged current container; '
                     'authentication, capacity and worker liveness are not checked'}


class FullStageMaterialsInput(StageResultsInput):
    """All four model stages consume frozen leaves; the original schedule remains."""

    version = 8
    queue_suffix = '.composition-v8'
    requests_suffix = '-composition-v8'
    complete_resources = True

    @classmethod
    def workflow_type(cls):
        from .reference_workflows import FullStageMaterialsWorkflow

        return FullStageMaterialsWorkflow

    @classmethod
    def adapter(cls, config: dict):
        from .reference_workflows import FullStageMaterialsAdapter

        return FullStageMaterialsAdapter({**config, 'requests': str(cls.request_root(Path(config['requests'])))})

    def admission_report(self, original_report, selection: dict) -> dict:
        preparation = self.document['composition']['preparation']
        return _selected_prerequisites(self, selection,
            [(stage, preparation['members'][preparation[stage]]) for stage in ('inventory', 'plan')])

    def stage_material(self) -> dict:
        return {'issue_source': self.document['issue_source']} if 'issue_source' in self.document else {}

    def evidence_contract(self) -> dict:
        return {'original_input': self.document, 'original_input_sha256': task_envelopes.identity(self.document)}


class BudgetedInput(FullStageMaterialsInput):
    """Readable persisted input; execution stays closed until all owners consume it."""

    version = 9
    queue_suffix = '.composition-v9'
    requests_suffix = '-composition-v9'
    execution_enabled = False

    @classmethod
    def workflow_type(cls):
        raise ValueError('Budgeted six-stage execution is unsupported until the complete lifecycle consumer is available')

    def require_submission(self) -> None:
        self.workflow_type()


_INPUTS = {1: LegacyInput, 2: CompositionInput, 3: ReviewRequirementsInput, 4: ReviewDAGInput,
           5: WorkDeliveryInput, 6: StageResultsInput, 7: IssueSourceInput, 8: FullStageMaterialsInput, 9: BudgetedInput}


def workers(client, queue: str, config: dict) -> list:
    """Register every supported version through its own construction contract."""
    return [implementation.worker(client, queue, config) for implementation in _INPUTS.values() if implementation.execution_enabled]


def request_roots(original: Path) -> tuple[Path, ...]:
    """The registered input versions own the executor's request namespaces."""
    return tuple(implementation.request_root(original) for implementation in _INPUTS.values() if implementation.execution_enabled)


def execution_input(document: dict) -> WorkflowInput:
    """Select here; transport and file readers use the same original-input interface."""
    spec, composition = task_envelopes.unwrap(document)
    return _INPUTS[document['schema_version'] if composition is not None else 1](document, spec)
