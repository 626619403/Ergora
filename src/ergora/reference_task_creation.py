"""Native task compilation/publication boundary, entered only in a dedicated process."""

from contextlib import ExitStack
import json
import os
from pathlib import Path
import shutil
import signal
import sys
from datetime import datetime, timezone

from .reference import _read_windows_contract, registration_paths
from .state import State, file_lock
from . import issue_sources, reference_budget, task_envelopes


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
        self.prepare_path = self.path(prefix + '.prepare.json')
        self.prepared_path = self.path(prefix + '.prepared.json')
        self.prepare_attempt = self.path(prefix + '.prepare-attempt.json')
        self.prepare_result = self.path(prefix + '.prepare-result.json')
        self.prepare_work = self.path(prefix + '.prepare-work')
        self.active_budget = None

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
        if definition['schema_version'] in (2, 3, 4, 5, 6):
            files['task.spec.json'] = task_envelopes.wrap(files['task.spec.json'], self.payload['composition'],
                                                       self.payload.get('issue_source'), budget=self.payload.get('budget'))
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
                or record['schema_version'] not in (1, 2, 3, 4, 5, 6) or record['schema_version'] != record['definition']['schema_version']):
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
        if spec != compiled['spec'] or (composition is not None) != (record['schema_version'] in (2, 3, 4, 5, 6)):
            raise ValueError('Creation intent execution envelope differs from its original spec')
        if ('issue_source' in files['task.spec.json']) != ('source' in record['definition']):
            raise ValueError('Creation intent source differs from its versioned definition')
        if (composition is not None and 'preparation' in composition) != (record['schema_version'] in (4, 5, 6)):
            raise ValueError('Creation intent preparation differs from its versioned definition')
        if ('budget' in files['task.spec.json']) != (record['schema_version'] in (5, 6)):
            raise ValueError('Creation intent budget differs from its versioned definition')
        if (composition is not None and 'native' in composition) != (record['schema_version'] == 6):
            raise ValueError('Creation native invocation differs from its versioned definition')
        if record['schema_version'] in (5, 6):
            instance = files['task.spec.json']['budget']['instance']
            if (instance['scope'] != reference_budget.scope({**self.project, 'revision': record['project_revision']},
                                                          Path(record['control_home']), record['definition'])
                    or instance['policy'] != record['definition']['budget']
                    or self.optional(self.prepare_path) != instance):
                raise ValueError('Creation budget differs from its original definition or project')
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
            work = composition.get('execution')
            preparation = composition.get('preparation')
            selected = {**composition['members'], **(work['members'] if work else {}),
                        **(preparation['members'] if preparation else {})}
            implementer = selection['bindings']['implementer']['tool']
            tools = sorted({member['binding']['tool'] for member in work['members'].values()}) if work else [implementer]
            same = [path for path, member in composition['members'].items() if member['binding']['tool'] in tools]
            diversity = {**option.get('diversity', {'policy': 'prefer-distinct'}),
                         **({'implementer_backends': tools} if work else {'implementer_backend': implementer}),
                         'same_backend_members': sorted(same)}
            saved_diversity = {**composition['diversity'],
                               'same_backend_members': sorted(composition['diversity']['same_backend_members'])}
            if (composition['manifest']['digest'] != option['manifest_digest']
                    or composition['review_instance'] != option['review_instance']
                    or composition.get('review_protocol') != option.get('review_protocol')
                    or (None if 'native' not in composition else {key: composition['native'][key]
                        for key in ('protocol', 'instance')}) != option.get('native')
                    or (None if work is None else {key: value for key, value in work.items() if key != 'members'}) != option.get('execution')
                    or (None if preparation is None else {key: value for key, value in preparation.items() if key != 'members'}) != option.get('preparation')
                    or overrides.keys() - selected.keys() or saved_diversity != diversity):
                raise ValueError('Creation intent composition differs from its saved selection')
            for path, member in selected.items():
                override = overrides.get(path)
                binding = override['binding'] if override else member['requested_binding']
                reason = override['reason'] if override else 'definition-selected backend'
                mode = (option['mode'] if member['role'] == 'reviewer' else
                        option['execution']['mode'] if member['role'] == 'implementer' else option['preparation']['mode'])
                if member['mode'] != mode or member['binding'] != binding or member['backend_reason'] != reason:
                    raise ValueError('Creation intent composition member differs from its saved selection: ' + path)
        if 'source' in definition:
            source = files['task.spec.json']['issue_source']
            if definition['source'] != {'snapshot_sha256': source['sha256']}:
                raise ValueError('Creation intent source differs from its selected snapshot')
            issue_sources.bind_snapshot(source, record['project'], configuration['layers']['tracker']['binding'], request['tracker'])
        if record['schema_version'] in (3, 4, 5, 6):
            # Inventory has no dynamic receipts or approval yet, so its exact
            # complete context is known before publication. Later stages keep
            # their original complete-material checks as results arrive.
            task_envelopes.issue_inventory_context(files['task.spec.json'], request['repository']['starting_sha'])

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
                   if record['schema_version'] in (2, 3, 4, 5, 6) else {})}

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
            self.check_budget()
            self.core.write(self.intent_path, record)
        # Freeze role choices first; expose the runnable spec only after all inputs.
        for filename in _FILES:
            self.check_budget()
            self.core.write(self.path('tasks/' + self.task_id + '/' + filename), record['files'][filename])
        self.check_budget()
        self.core.write(self.result_path, self.receipt(record))
        return self.status(record)

    def check_budget(self) -> None:
        if self.active_budget is not None:
            reference_budget.require_remaining(self.active_budget)

    def preparation(self) -> dict:
        """Read only the original authorization and its small completion witness."""
        instance = self.optional(self.prepare_path)
        result = {'project': self.project['id'], 'task_id': self.task_id,
                  'runtime_status': 'not_queried', 'execution_started_by_operation': False}
        if instance is None:
            return {**result, 'status': 'not_recorded'}
        reference_budget.validate(instance)
        owner = instance['scope']
        if (owner['control_home'] != self.payload['control_home'] or owner['project'] != self.project['id']
                or owner['repo'] != self.project['repo'] or owner['execution'] != self.execution
                or owner['registration_sha256'] != self.project['registration']['sha256']
                or owner['task_id'] != self.task_id):
            raise ValueError('Preparation belongs to another project, registration or control directory')
        outcome = self.optional(self.prepare_result)
        attempt = self.optional(self.prepare_attempt)
        if attempt is not None and attempt != {'schema_version': 1, 'prepare_sha256': instance['sha256']}:
            raise ValueError('Preparation attempt differs from its original authorization')
        if outcome is not None:
            status = outcome.get('status')
            fields = {'schema_version', 'prepare_sha256', 'cleanup_confirmed', 'process', 'status',
                      'recorded_at', 'elapsed_seconds', 'overrun_seconds'}
            fields |= {'record_sha256'} if status == 'prepared' else {'detail'} if status == 'failed' else set()
            process = outcome.get('process')
            if (set(outcome) != fields or type(outcome.get('schema_version')) is not int
                    or outcome['schema_version'] != 1 or outcome['prepare_sha256'] != instance['sha256']
                    or attempt is None or outcome['cleanup_confirmed'] is not True
                    or status not in ('prepared', 'failed', 'exhausted')
                    or type(outcome['elapsed_seconds']) not in (int, float) or outcome['elapsed_seconds'] < 0
                    or type(outcome['overrun_seconds']) not in (int, float)
                    or outcome['overrun_seconds'] != max(0, outcome['elapsed_seconds'] - instance['policy']['wall_seconds'])
                    or not isinstance(process, dict) or set(process) != {'status', 'returncode'}
                    or process['status'] not in ('succeeded', 'failed', 'cancelled', 'timed_out')
                    or (process['returncode'] is not None and type(process['returncode']) is not int)
                    or (status == 'prepared' and (process != {'status': 'succeeded', 'returncode': 0}
                        or not isinstance(outcome['record_sha256'], str)
                        or len(outcome['record_sha256']) != 64))):
                raise ValueError('Preparation outcome differs from its original authorization, attempt or cleanup witness')
        try:
            left = reference_budget.remaining(instance)
            budget_status = {'status': 'available' if left > 0 else 'exhausted', 'work_remaining_seconds': max(0, left)}
        except ValueError as error:
            budget_status = {'status': 'unsupported_clock', 'detail': str(error)}
        return {**result, 'status': outcome['status'] if outcome else 'unknown' if attempt else 'authorized',
                'prepare_sha256': instance['sha256'], 'budget': instance,
                'budget_status': budget_status,
                **({'outcome': outcome} if outcome else {})}

    def prepared_record(self) -> dict:
        status = self.preparation()
        if status['status'] != 'prepared':
            raise ValueError('No confirmed complete preparation; inspect preparation for the original task ID')
        record = self.document(self.prepared_path, _INTENT_LIMIT)
        self.validate_record(record)
        if (self.sha(record) != status['outcome']['record_sha256']
                or record['files']['task.spec.json']['budget']['instance'] != status['budget']):
            raise ValueError('Prepared materials differ from the original completion witness')
        return record

    def prepare(self) -> dict:
        """Persist once before expensive work; an uncertain attempt never reruns."""
        definition = self.payload['definition']
        owner = reference_budget.scope(self.project, Path(self.payload['control_home']), definition)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with file_lock(self.lock_path, blocking=False):
            status = self.preparation()
            if status['status'] == 'not_recorded':
                if self.intent_path.exists() or self.target.exists() or self.result_path.exists():
                    raise ValueError('Task ID already exists; preparation cannot adopt or renew an original task')
                instance = reference_budget.authorize(definition['budget'], owner)
                self.core.write(self.prepare_path, instance)
                status = self.preparation()
            instance = status['budget']
            if instance['scope'] != owner or instance['policy'] != definition['budget']:
                raise ValueError('Task ID already has a different preparation; its original budget is retained')
            if status['status'] != 'authorized':
                return status
            reference_budget.require_remaining(instance)
            self.core.write(self.prepare_attempt, {'schema_version': 1, 'prepare_sha256': instance['sha256']})
            self.prepare_work.mkdir(mode=0o700)
            scratch = self.prepare_work / 'compile'
            environment = dict(os.environ, AGENTFLOW_STATE_DIR=str(scratch))
            payload = {**self.payload, 'operation': 'prepare-worker', 'instance': instance}
            from . import processes

            def stop(signum, frame):
                processes.cancel_supervised()

            signal.signal(signal.SIGTERM, stop)
            signal.signal(signal.SIGALRM, stop)
            # Attempt publication/fsync consumed this same authorization too.
            remaining = reference_budget.require_remaining(instance)
            signal.setitimer(signal.ITIMER_REAL, remaining)
            try:
                result = processes.run([sys.executable, '-P', '-c',
                    'from ergora.reference_task_creation import preparation_worker;preparation_worker()'],
                    Path(self.payload['control_home']), self.prepare_work / 'process', remaining,
                    json.dumps(payload, allow_nan=False), environment, supervised=True)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                # This safety cleanup may exceed the budget on an unresponsive
                # filesystem. No completion witness exists until it returns.
                if scratch.exists():
                    shutil.rmtree(scratch)
            outcome = {'schema_version': 1, 'prepare_sha256': instance['sha256'], 'cleanup_confirmed': True,
                       'process': {key: value for key, value in result.items() if key != 'output'}}
            if reference_budget.remaining(instance) <= 0:
                outcome['status'] = 'exhausted'
            elif result['status'] != 'succeeded':
                outcome['status'] = 'failed'
                outcome['detail'] = 'Preparation worker failed or stopped; inspect original private process output'
            else:
                record = self.document(self.prepare_work / 'process/stdout.txt', _INTENT_LIMIT)
                # Full record validation took place inside the stoppable worker.
                reference_budget.require_remaining(instance, cleanup=True)
                self.core.write(self.prepared_path, record)
                reference_budget.require_remaining(instance, cleanup=True)
                outcome.update(status='prepared', record_sha256=self.sha(record))
            elapsed = instance['policy']['wall_seconds'] - reference_budget.remaining(instance, cleanup=True)
            if elapsed >= instance['policy']['wall_seconds']:
                outcome['status'] = 'exhausted'
                outcome.pop('record_sha256', None)
                outcome.pop('detail', None)
            outcome.update(recorded_at=datetime.now(timezone.utc).isoformat(), elapsed_seconds=elapsed,
                           overrun_seconds=max(0, elapsed - instance['policy']['wall_seconds']))
            # Fsync the candidate before deciding whether completion was in
            # budget. Publishing the witness then only links existing bytes;
            # a slow final persistence cannot expose an earlier prepared fact.
            candidate = self.prepare_work / 'outcome.json'
            self.core.write(candidate, outcome)
            elapsed = instance['policy']['wall_seconds'] - reference_budget.remaining(instance, cleanup=True)
            if elapsed >= instance['policy']['wall_seconds']:
                outcome.update(status='exhausted', recorded_at=datetime.now(timezone.utc).isoformat(),
                               elapsed_seconds=elapsed,
                               overrun_seconds=elapsed - instance['policy']['wall_seconds'])
                outcome.pop('record_sha256', None)
                outcome.pop('detail', None)
                candidate = self.prepare_work / 'exhausted.json'
                self.core.write(candidate, outcome)
            os.link(candidate, self.prepare_result)
            return self.preparation()

    def budget_run(self) -> dict:
        operation = self.payload['operation']
        if operation == 'prepare':
            return self.prepare()
        if operation == 'preparation':
            return self.preparation()
        if operation in ('create', 'resume'):
            status = self.preparation()
            instance = status.get('budget')
            if instance is None:
                raise ValueError('No original budget preparation')
            # Collection/validation/publication is a dedicated process too.
            # A read-only preview remains a deterministic observation, including
            # after expiration; it cannot authorize execution or publication.
            self.active_budget = instance
            def expired(signum, frame):
                raise ValueError('Original budget is exhausted during creation; inspect the original intent')
            left = reference_budget.remaining(instance)
            if left > 0:
                signal.signal(signal.SIGALRM, expired)
                signal.setitimer(signal.ITIMER_REAL, left)
        with ExitStack() as ownership:
            if operation in ('create', 'resume'):
                # The actual publisher keeps the revision reservation even if
                # its CLI/HTTP observer has already returned unknown.
                state = State(Path(self.payload['control_home']))
                db = ownership.enter_context(state.connect())
                db.execute('BEGIN IMMEDIATE')
                current = state.project(self.project['id'])
                if (current['revision'] != self.project['revision']
                        or current.get('registration') != self.project['registration']):
                    raise ValueError('Project revision changed before budget publication')
            record = self.prepared_record() if operation in ('preview', 'create') else self.load()
            if record is None or record['schema_version'] not in (5, 6):
                raise ValueError('Budget operation requires the original budgeted preparation')
            instance = record['files']['task.spec.json']['budget']['instance']
            self.active_budget = instance
            if operation in ('preview', 'create') and record['definition'] != self.payload['definition']:
                raise ValueError('Task definition differs from its original preparation')
            if operation in ('preview', 'create') and instance['scope'] != reference_budget.scope(
                    self.project, Path(self.payload['control_home']), self.payload['definition']):
                raise ValueError('Project revision changed after preparation; the original authorization is retained')
            if operation == 'preview':
                return {**record, 'prepare_sha256': instance['sha256'], 'preview_sha256': self.sha(record),
                        'status': 'preview', 'runtime_status': 'not_queried', 'execution_started_by_operation': False}
            if operation == 'create' and (self.payload['prepare_sha256'] != instance['sha256']
                    or self.payload['preview_sha256'] != self.sha(record)):
                raise ValueError('Preparation or preview changed; inspect the original preparation')
            if operation == 'resume' and self.payload['intent_sha256'] != self.sha(record):
                raise ValueError('Creation intent digest changed; inspect the original intent before resuming')
            if operation not in ('create', 'resume'):
                raise ValueError('Unsupported budget creation operation')
            with file_lock(self.lock_path, blocking=False):
                status = self.preparation()
                if status.get('budget') != instance or status['status'] != 'prepared':
                    raise ValueError('Creation differs from its original preparation')
                saved = self.load()
                if saved is not None:
                    if self.sha(saved) != self.sha(record):
                        raise ValueError('Task ID already has a different creation intent')
                    if self.status(saved)['status'] == 'published':
                        return self.status(saved)
                elif self.target.exists() or self.result_path.exists():
                    raise ValueError('Task ID exists without its creation intent')
                self.check_budget()
                return self.publish(record, save_intent=saved is None)

    def run(self, temporary: Path) -> dict:
        operation = self.payload['operation']
        if self.payload.get('budgeted'):
            return self.budget_run()
        if operation == 'preparation':
            return self.preparation()
        if self.payload.get('definition', {}).get('schema_version') in (5, 6):
            raise ValueError('Budgeted creation requires its original preparation owner')
        if operation in ('create', 'resume') and self.prepare_path.exists():
            raise ValueError('Task ID has an original budget preparation; use its original preparation owner')
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
                if record['schema_version'] in (5, 6):
                    raise ValueError('Budgeted recovery requires its original preparation owner')
            elif saved is not None:
                if self.sha(saved) != self.sha(record):
                    raise ValueError('Task ID already has a different creation intent; inspect and resume its original intent')
            elif self.target.exists() or self.result_path.exists():
                raise ValueError('Task ID already exists without this creation intent; legacy tasks cannot be adopted')
            return self.publish(record, save_intent=saved is None)


def preparation_worker() -> None:
    """All expensive preparation runs inside the dedicated supervised tree."""
    from . import tasks
    from .state import State
    from agent_platform.core import STATE

    payload = json.load(sys.stdin)
    instance = payload['instance']
    reference_budget.require_remaining(instance)
    state = State(Path(payload['control_home']))
    project = tasks._project(state, payload['project']['id'])
    if reference_budget.scope(project, state.root, payload['definition']) != instance['scope']:
        raise ValueError('Project or definition changed after original preparation authorization')
    selected = tasks._definition(state, project, payload['definition'])
    budget = {'instance': instance, 'slots': reference_budget.call_slots(selected['composition'])}
    if len(budget['slots']) > instance['policy']['model_invocations']:
        raise ValueError('Known model call slots exceed the original invocation cap')
    reference_budget.require_remaining(instance)
    record = _Creation({**payload, **selected, 'budget': budget}).compile(STATE)
    reference_budget.require_remaining(instance)
    print(json.dumps(record, ensure_ascii=False, allow_nan=False))


def main() -> None:
    """Compile only in ephemeral storage; publish only to the registered execution root."""
    payload = json.load(sys.stdin)
    # Native core captures STATE at import time. The parent supplies and owns
    # ephemeral storage, including cleanup after a forced process termination.
    from agent_platform.core import Blocked, STATE
    try:
        result = _Creation(payload).run(STATE)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except BlockingIOError:
        if payload.get('budgeted') and payload['operation'] == 'prepare':
            # A concurrent owner can still be publishing its initial atomic
            # authorization. Observers never start a second body or timestamp.
            result = _Creation(payload).preparation()
            instance = result.get('budget')
            if instance is not None and (instance['scope'] != reference_budget.scope(
                    payload['project'], Path(payload['control_home']), payload['definition'])
                    or instance['policy'] != payload['definition']['budget']):
                raise SystemExit('BLOCKED: Task ID already has a different preparation; its original budget is retained')
            if result['status'] == 'not_recorded':
                result['status'] = 'busy'
            print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        else:
            raise SystemExit('BLOCKED: Task creation is locked by its original owner')
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
