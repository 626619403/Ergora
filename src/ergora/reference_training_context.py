"""The selected native training project's paths and published registration."""

import json
import os
from pathlib import Path

from .reference import _read_windows_contract, registration_paths


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
        self.execution = self.project['registration']['definition']['execution']
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
        for name, expected in self.project['registration']['files'].items():
            if self.sha(self.document(self.config, name)) != self.sha(expected):
                raise ValueError('Registered reference configuration drift: ' + name)
        marker = self.project['registration']['files'][registration_paths(self.project['id'])[0]]
        if marker['control_home'] != self.payload['control_home']:
            raise ValueError('Registered training project belongs to another control directory')
