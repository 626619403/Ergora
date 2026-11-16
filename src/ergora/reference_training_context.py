"""The selected native training project's paths and published registration."""

import json
import os
from pathlib import Path
import sys

from . import reference
from .reference import _read_windows_contract, registration_paths
from .registrations import published_project


def _native_bytes(value: dict, name: str, limit: int = 1_048_576) -> bytes:
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if len(raw) > limit:
        raise ValueError(f'{name} exceeds the native {limit // 1_048_576} MiB read capacity')
    return raw


class _TrainingProject:
    def __init__(self, payload: dict):
        from agent_platform import core
        from dev_platform import adapter
        from dev_platform.contracts import canonical_sha

        self.core, self.adapter, self.sha = core, adapter, canonical_sha
        if os.name == 'nt':
            adapter.read_raw = _read_windows_contract
        self.payload = payload
        self.project = payload['project']
        self.recovery = self.project.get('_original_registration')
        self.project_revision = self.project['revision']
        if self.recovery is not None:
            original = published_project(payload['control_home'], self.project['id'],
                                         self.recovery['operation_id'], self.recovery['intent_sha256'])
            self.project_revision = self.recovery['current_project_revision']
            if ({key: value for key, value in self.project.items() if key != '_original_registration'} != original
                    or type(self.project_revision) is not int or self.project_revision < 1):
                raise ValueError('Training recovery project differs from its original published registration')
            self.project = original
        self.execution = self.project['registration']['definition']['execution']
        self.recovery_context = {} if self.recovery is None else {'original_registration': {
            **self.recovery, 'registration_project_revision': self.project['revision'],
            'registration_sha256': self.project['registration']['sha256'], 'repo': self.project['repo'],
            'execution': self.execution}}
        self.root = Path(self.execution['state_directory'])
        self.config = Path(self.execution['config_directory'])
        for directory in (self.root, self.config):
            if not directory.is_absolute() or directory.resolve() != directory:
                raise ValueError('Execution directories must retain their registered canonical paths')

    def document(self, root: Path, relative: str, limit: int = 1_048_576) -> dict:
        value = json.loads(self.adapter.read_raw(self.adapter.safe_file(root, relative), limit))
        if not isinstance(value, dict):
            raise ValueError('Training record must be a JSON object')
        return value

    def registration(self) -> None:
        if self.recovery is not None:
            return
        for name, expected in self.project['registration']['files'].items():
            if self.sha(self.document(self.config, name)) != self.sha(expected):
                raise ValueError('Registered reference configuration drift: ' + name)
        marker = self.project['registration']['files'][registration_paths(self.project['id'])[0]]
        if marker['control_home'] != self.payload['control_home']:
            raise ValueError('Registered training project belongs to another control directory')


def _select_cycle_project(authorization: dict, project: dict):
    """Load one selected native project inside H or its independent budget root."""
    execution = authorization['execution']
    installation = reference.validate_installation(Path(execution['installation']), training=True)
    paths = [str(installation / part) for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
    sys.path[:0] = paths
    os.environ.update(AGENTFLOW_CONFIG_DIR=execution['config_directory'], AGENTFLOW_STATE_DIR=execution['state_directory'])
    context = _TrainingProject({'project': project, 'control_home': authorization['control_home']})
    context.registration()
    from agent_platform.core import environment

    os.environ.update(environment())
    # Native environment() replaces PYTHONPATH. Every later phase must still
    # import this exact application together with the selected native sources.
    os.environ['PYTHONPATH'] = os.pathsep.join([str(Path(__file__).parent.parent), *paths])
    return context
