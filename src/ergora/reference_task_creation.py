"""Native task compilation/publication boundary, entered only in a dedicated process."""

import json
import os
from pathlib import Path
import sys

from .reference import _read_windows_contract, registration_paths
from .state import file_lock
from . import task_envelopes


_FILES = ('agent-bindings.json', 'task.json', 'policy.json', 'binding.json',
          'compiled.json', 'project.json', 'task.spec.json')
_FILE_LIMIT = 1_048_576
_INTENT_LIMIT = 16 * _FILE_LIMIT


class _Creation:
    """Own the original creation snapshot and its recoverable immutable publication."""

    def __init__(self, payload: dict):
        from agent_platform import core
        from dev_platform import adapter, portable
        from dev_platform.contracts import canonical_sha

        self.core, self.adapter, self.portable = core, adapter, portable
        self.sha = canonical_sha
        if os.name == 'nt':
            adapter.read_raw = _read_windows_contract
            portable._read_bytes = _read_windows_contract
        # Original create_task uses core.read for trusted config and input files.
        # Preserve the same bounded/no-follow boundary as task inspection.
        core.read = self.document
        self.payload = payload
        self.project = payload['project']
        self.execution = self.project['registration']['definition']['execution']
        self.root = Path(self.execution['state_directory'])
        self.config = Path(self.execution['config_directory'])
        for directory in (self.root, self.config):
            if not directory.is_absolute() or directory.resolve() != directory:
                raise ValueError('Execution directories must retain their registered canonical paths')
        self.task_id = core.slug(payload['task_id'] if 'task_id' in payload else payload['definition']['task_id'])
        self.target = self.path('tasks/' + self.task_id)
        prefix = 'ergora/task-creations/' + self.task_id
        self.intent_path = self.path(prefix + '.intent.json')
        self.result_path = self.path(prefix + '.result.json')
        self.lock_path = self.path(prefix + '.lock')

    def path(self, relative: str) -> Path:
        return self.safe_path(self.root, relative)

    def safe_path(self, root: Path, relative: str) -> Path:
        path = self.adapter.safe_file(root, relative)
        if os.name == 'nt':
            for parent in (path, *path.parents):
                if parent.exists() and parent.lstat().st_file_attributes & 0x400:
                    raise ValueError('Symlinked or reparsed creation path is forbidden')
                if parent == root:
                    break
        return path

    def document(self, path: Path, limit: int = _FILE_LIMIT) -> dict:
        if not path.exists():
            raise FileNotFoundError(path)
        if not path.is_file():
            raise ValueError('Creation contract must be a regular file: ' + path.name)
        value = json.loads(self.adapter.read_raw(path, limit).decode('utf-8'))
        if not isinstance(value, dict):
            raise ValueError('Creation contract must be a JSON object: ' + path.name)
        return value

    def optional(self, path: Path, limit: int = _FILE_LIMIT) -> dict | None:
        try:
            return self.document(path, limit)
        except FileNotFoundError:
            return None

    def file_adapter(self, selected=None):
        config = self.document(self.safe_path(self.config, 'adapter.json'))
        adapter = self.adapter.FileAdapter(config)
        expected = {name: self.path(name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
        if adapter.roots != expected:
            raise ValueError('External evidence adapter roots differ from the registered execution state')
        return selected.adapter(config) if selected is not None else adapter

    def check_registration(self) -> None:
        for relative, expected in self.project['registration']['files'].items():
            actual = self.document(self.safe_path(self.config, relative))
            if self.sha(actual) != self.sha(expected):
                raise ValueError('Registered reference configuration drift: ' + relative)
        marker = self.project['registration']['files'][registration_paths(self.project['id'])[0]]
        if marker['control_home'] != self.payload['control_home']:
            raise ValueError('Registered project belongs to another control directory')

    def compile(self, temporary: Path) -> dict:
        from agent_platform.projects import check_task_type, create_task

        self.check_registration()
        definition = self.payload['definition']
        check_task_type(self.project['id'], definition['task_type'])
        input_path = temporary / 'input.json'
        self.core.write(input_path, definition['input'])
        create_task(self.project['id'], definition['task_type'], self.task_id, definition['issue_id'],
                    input_path, definition.get('starting_sha'))
        files = {name: self.document(temporary / 'tasks' / self.task_id / name)
                 for name in _FILES if name != 'agent-bindings.json'}
        files['agent-bindings.json'] = self.payload['selection']
        if definition['schema_version'] == 2:
            files['task.spec.json'] = task_envelopes.wrap(files['task.spec.json'], self.payload['composition'])
        record = {'schema_version': definition['schema_version'], 'control_home': self.payload['control_home'],
                  'project': self.project['id'], 'repo': self.project['repo'],
                  'project_revision': self.project['revision'],
                  'registration_sha256': self.project['registration']['sha256'],
                  'execution': self.execution, 'definition': definition, 'files': files}
        self.validate_record(record)
        return record

    @staticmethod
    def check_size(value: dict, limit: int, name: str) -> None:
        raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        if len(raw) > limit:
            raise ValueError(name + ' exceeds its creation read limit')

    def validate_record(self, record: dict) -> None:
        expected = {'schema_version', 'control_home', 'project', 'repo', 'project_revision',
                    'registration_sha256', 'execution', 'definition', 'files'}
        if (set(record) != expected or type(record['schema_version']) is not int
                or record['schema_version'] not in (1, 2) or record['schema_version'] != record['definition']['schema_version']):
            raise ValueError('Unsupported creation intent format')
        if (record['control_home'] != self.payload['control_home'] or record['project'] != self.project['id']
                or record['repo'] != self.project['repo'] or record['execution'] != self.execution
                or record['registration_sha256'] != self.project['registration']['sha256']):
            raise ValueError('Creation intent belongs to another project, registration or control directory')
        files = record['files']
        if set(files) != set(_FILES):
            raise ValueError('Creation intent must contain exactly the original native contracts and bindings')
        for name, value in files.items():
            self.check_size(value, _FILE_LIMIT, name)
        self.check_size(record, _INTENT_LIMIT, 'creation intent')
        compiled = self.portable.validate_compiled(files['compiled.json'])
        spec, composition = task_envelopes.unwrap(files['task.spec.json'])
        if spec != compiled['spec'] or (composition is not None) != (record['schema_version'] == 2):
            raise ValueError('Creation intent execution envelope differs from its original spec')
        for filename, key in (('task.json', 'task'), ('policy.json', 'policy'), ('binding.json', 'binding')):
            if files[filename] != compiled[key]:
                raise ValueError('Creation intent contract mismatch: ' + filename)
        frozen_project = self.project['registration']['files']['projects/' + self.project['id'] + '.json']
        if files['project.json'] != frozen_project:
            raise ValueError('Creation intent project differs from the registered project')
        definition = record['definition']
        request = compiled['spec']['request']
        if (definition['task_id'] != self.task_id or request['task_id'] != self.task_id
                or request['task_type'] != definition['task_type'] or request['input'] != definition['input']
                or request['tracker'] != {**frozen_project['tracker'], 'issue_id': definition['issue_id']}
                or request['repository'] != {'base_sha': frozen_project['base_sha'],
                    'starting_sha': definition.get('starting_sha', frozen_project['base_sha'])}):
            raise ValueError('Creation intent does not match its original task definition')
        selection = files['agent-bindings.json']
        configuration = selection['configuration']
        if (selection['reference_project'] != self.project['id']
                or type(record['project_revision']) is not int or record['project_revision'] < 1
                or selection['project_revision'] != record['project_revision']
                or configuration['project'] != {'id': record['project'], 'repo': record['repo'],
                                                'revision': record['project_revision']}
                or configuration['sha256'] != self.sha({k: v for k, v in configuration.items() if k != 'sha256'})
                or selection['bindings'] != {role: configuration['layers'][role]['binding']
                                             for role in ('inspector', 'planner', 'implementer', 'reviewer')}):
            raise ValueError('Creation intent contains an inconsistent agent snapshot')
        if composition is not None:
            option = definition['composition']
            overrides = option.get('backend_overrides', {})
            implementer = selection['bindings']['implementer']['tool']
            same = [path for path, member in composition['members'].items() if member['binding']['tool'] == implementer]
            diversity = {**option.get('diversity', {'policy': 'prefer-distinct'}),
                         'implementer_backend': implementer, 'same_backend_members': sorted(same)}
            saved_diversity = {**composition['diversity'],
                               'same_backend_members': sorted(composition['diversity']['same_backend_members'])}
            if (composition['manifest']['digest'] != option['manifest_digest']
                    or composition['review_instance'] != option['review_instance']
                    or overrides.keys() - composition['members'].keys() or saved_diversity != diversity):
                raise ValueError('Creation intent composition differs from its saved selection')
            for path, member in composition['members'].items():
                override = overrides.get(path)
                binding = override['binding'] if override else member['requested_binding']
                reason = override['reason'] if override else 'definition-selected backend'
                if member['mode'] != option['mode'] or member['binding'] != binding or member['backend_reason'] != reason:
                    raise ValueError('Creation intent composition member differs from its saved selection: ' + path)

    def load(self) -> dict | None:
        record = self.optional(self.intent_path, _INTENT_LIMIT)
        if record is not None:
            self.validate_record(record)
        return record

    def published(self) -> dict:
        """Validate this control's complete creation before native operations."""
        self.check_registration()
        record = self.load()
        if record is None:
            raise ValueError('No saved creation intent; legacy tasks cannot be adopted by runtime operations')
        if self.status(record)['status'] != 'published':
            raise ValueError('Task creation is incomplete or conflicted; inspect creation and resume-create first')
        return record

    def file_states(self, record: dict) -> dict:
        states = {}
        for filename in _FILES:
            current = self.optional(self.path('tasks/' + self.task_id + '/' + filename))
            states[filename] = ('missing' if current is None else
                                'matches' if self.sha(current) == self.sha(record['files'][filename]) else 'differs')
        return states

    def receipt(self, record: dict) -> dict:
        return {'schema_version': 1, 'project': record['project'], 'task_id': self.task_id,
                'intent_sha256': self.sha(record), 'compiled_sha256': self.sha(record['files']['compiled.json']),
                'file_content_sha256': {name: self.sha(value) for name, value in record['files'].items()}}

    def status(self, record: dict | None) -> dict:
        result = {'project': self.project['id'], 'project_revision': self.project['revision'],
                  'task_id': self.task_id, 'runtime_status': 'not_queried', 'execution_started_by_operation': False}
        if record is None:
            return {**result, 'status': 'not_recorded', 'task_directory_exists': self.target.exists()}
        states = self.file_states(record)
        receipt = self.optional(self.result_path)
        if receipt is not None and receipt != self.receipt(record):
            raise ValueError('Creation result conflicts with the saved intent')
        status = ('conflict' if 'differs' in states.values() else
                  'published' if receipt is not None and all(v == 'matches' for v in states.values()) else 'pending')
        return {**result, 'status': status, 'files': states, 'result_saved': receipt is not None,
                'intent_sha256': self.sha(record), 'created_revision': record['project_revision'],
                'compiled_sha256': self.sha(record['files']['compiled.json']),
                'agent_bindings': record['files']['agent-bindings.json'],
                **({'composition': task_envelopes.summary(record['files']['task.spec.json'])}
                   if record['schema_version'] == 2 else {})}

    def publish(self, record: dict, *, save_intent: bool) -> dict:
        self.check_registration()
        states = self.file_states(record)
        if 'differs' in states.values():
            raise ValueError('Immutable task files conflict with the saved creation intent')
        receipt = self.optional(self.result_path)
        if receipt is not None and receipt != self.receipt(record):
            raise ValueError('Creation result conflicts with the saved intent')
        # Save the complete contract before publishing any native task files.
        # Existing intents were loaded with the aggregate 16 MiB limit and
        # checked under this task's lock. Keep their original bytes on retries;
        # core.write's ordinary-contract comparison reads only 1 MiB.
        if save_intent:
            self.core.write(self.intent_path, record)
        # Freeze role choices first; expose the runnable spec only after all inputs.
        for filename in _FILES:
            self.core.write(self.path('tasks/' + self.task_id + '/' + filename), record['files'][filename])
        self.core.write(self.result_path, self.receipt(record))
        return self.status(record)

    def run(self, temporary: Path) -> dict:
        operation = self.payload['operation']
        if operation in ('preview', 'create'):
            record = self.compile(temporary)
            if operation == 'preview':
                return {**record, 'preview_sha256': self.sha(record), 'status': 'preview',
                        'runtime_status': 'not_queried', 'execution_started_by_operation': False}
            if self.payload['preview_sha256'] != self.sha(record):
                raise ValueError('Task preview changed; inspect a fresh preview before creating')
        elif operation == 'status':
            return self.status(self.load())
        elif operation == 'published':
            return self.published()
        elif operation != 'resume':
            raise ValueError('Unsupported task creation operation')
        self.lock_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Publication must not wait for a remote operation while holding the control DB.
        with file_lock(self.lock_path, blocking=False):
            saved = self.load()
            if operation == 'resume':
                if saved is None:
                    raise ValueError('No saved creation intent; legacy tasks cannot be adopted by resume-create')
                if self.sha(saved) != self.payload['intent_sha256']:
                    raise ValueError('Creation intent digest changed; inspect the original intent before resuming')
                record = saved
            elif saved is not None:
                if self.sha(saved) != self.sha(record):
                    raise ValueError('Task ID already has a different creation intent; inspect and resume its original intent')
            elif self.target.exists() or self.result_path.exists():
                raise ValueError('Task ID already exists without this creation intent; legacy tasks cannot be adopted')
            return self.publish(record, save_intent=saved is None)


def main() -> None:
    """Compile only in ephemeral storage; publish only to the registered execution root."""
    payload = json.load(sys.stdin)
    # Native core captures STATE at import time. The parent supplies and owns
    # ephemeral storage, including cleanup after a forced process termination.
    from agent_platform.core import Blocked, STATE
    try:
        result = _Creation(payload).run(STATE)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
