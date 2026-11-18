"""Freeze one native preparation plan; explicitly recover its immutable files."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from .reference import _training_records
from .reference_training_context import _TrainingProject, _native_bytes
from .state import file_lock
from .training_configuration import validate_runner
from .training_materials import confirm_file, material_plan, read_raw


_INTENT_LIMIT = 16 * 1_048_576


class _Preparation(_TrainingProject):
    def __init__(self, payload: dict):
        super().__init__(payload)
        self.ident = self.core.slug(payload['experiment_id'])
        self.prefix = 'ergora/training-preparations/' + self.ident
        self.base_targets = ('training/manifests/' + self.ident + '.json',
                        'training/projects/' + self.project['id'] + '/perf/experiments/' + self.ident + '/manifest.json',
                        'training/specs/' + self.ident + '.json')
        self.identity = {'schema_version': 1, 'operation': 'prepare-training',
                         'control_home': payload['control_home'], 'project': self.project['id'],
                         'repo': self.project['repo'], 'execution': self.execution,
                         'registration_sha256': self.project['registration']['sha256'], 'experiment_id': self.ident}

    def path(self, suffix: str) -> Path:
        return self.adapter.safe_file(self.root, self.prefix + suffix)

    def targets(self, request):
        materials = request['configuration_materials']
        return (*self.base_targets, *material_plan(self.ident, materials)[1]) if materials is not None else self.base_targets

    def confirm_intent(self, intent):
        raw = _native_bytes(intent, 'Preparation intent', _INTENT_LIMIT)
        confirm_file(self.path('.intent.json'), raw, self.root)
        if self.sha(self.load()) != self.sha(intent):
            raise ValueError('Original preparation intent identity changed during durable readback')

    def confirm_prepared(self, intent):
        self.confirm_intent(intent)
        observed = self.status(intent)
        if observed['status'] == 'prepared':
            for relative, text in intent['files'].items():
                confirm_file(self.adapter.safe_file(self.root, relative), text.encode('utf-8'), self.root)
            observed = self.status(intent)
        return observed

    def observe(self, intent):
        observed = self.status(intent)
        if observed['status'] != 'prepared':
            return observed
        # Existing immutable records only: no new intent or output is published.
        with file_lock(self.path('.lock'), blocking=False):
            if self.sha(self.load()) != self.sha(intent):
                raise ValueError('Original preparation intent changed during observation')
            return self.confirm_prepared(intent)

    def load(self) -> dict | None:
        try:
            intent = json.loads(read_raw(self.path('.intent.json'), _INTENT_LIMIT))
        except FileNotFoundError:
            return None
        if (any(intent.get(key) != value for key, value in self.identity.items())
                or type(intent.get('project_revision')) is not int or intent['project_revision'] < 1
                or set(intent) != set(self.identity) | {'project_revision', 'request', 'sources', 'files'}
                or set(intent['files']) != set(self.targets(intent['request']))
                or intent['request']['experiment']['experiment_id'] != self.ident):
            raise ValueError('Training preparation intent differs from its original project or experiment')
        return intent

    def sources(self, request: dict) -> dict:
        runner_id = self.core.slug(request['runner_template_id'])
        locations = {'runner': (self.config, 'training-runners/' + runner_id + '.json'),
                     'baseline': (self.root, 'training/projects/' + self.project['id'] + '/perf/baseline.json')}
        sources = {}
        for name, (directory, relative) in locations.items():
            raw = self.adapter.read_raw(self.adapter.safe_file(directory, relative))
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError('Training preparation source must be a JSON object: ' + name)
            if name == 'runner':
                validate_runner(value)
                if (value.get('project') != self.project['id'] or value.get('repo') != self.project['repo']
                        or value.get('runner_template_id') != runner_id):
                    raise ValueError('Training runner must belong to the selected project and registered Git root')
            sources[name] = {'document': value, 'file_sha256': hashlib.sha256(raw).hexdigest()}
        return sources

    def plan(self, request: dict, revision: int) -> dict:
        from agent_platform import training as native

        maximum = request['max_run_seconds']
        # The native `value or default` treats explicit zero/False as omission.
        if maximum is not None and (type(maximum) is not int or maximum == 0):
            raise ValueError('Explicit max_run_seconds must be an integer; omit it to use the native default')
        if not isinstance(request['experiment'], dict) or request['experiment'].get('experiment_id') != self.ident:
            raise ValueError('Draft must retain the selected experiment ID')
        sources = self.sources(request)
        with TemporaryDirectory(prefix='ergora-experiment-preview-') as temporary:
            root = Path(temporary)
            draft = root / 'draft.json'
            draft.write_bytes(_native_bytes(request['experiment'], 'Experiment draft'))
            runner = root / 'runner.json'
            runner.write_bytes(_native_bytes(sources['runner']['document'], 'Runner'))
            config, training = native.CONFIG, native.TRAINING
            try:
                native.CONFIG, native.TRAINING = root / 'config', root / 'training'
                native.register_runner(runner)
                baseline = native.perf_root(self.project['id']) / 'baseline.json'
                baseline.parent.mkdir(parents=True)
                baseline.write_bytes(_native_bytes(sources['baseline']['document'], 'Baseline'))
                native.prepare(draft, request['runner_template_id'], maximum,
                               configuration_materials=request['configuration_materials'])
                files = {relative: self.adapter.read_raw(root / relative).decode('utf-8') for relative in self.targets(request)}
                spec = json.loads(files[self.base_targets[2]])
                # The only staging address is the manifest URI. The native
                # owner already generated the exact manifest-byte binding.
                spec['manifest_uri'] = self.adapter.safe_file(self.root, self.base_targets[0]).as_uri()
                files[self.base_targets[2]] = _native_bytes(spec, 'Experiment spec').decode('utf-8')
            finally:
                native.CONFIG, native.TRAINING = config, training
        return {**self.identity, 'project_revision': revision, 'request': request, 'sources': sources, 'files': files}

    def status(self, intent: dict | None) -> dict:
        result = {'project': self.project['id'], 'project_revision': self.project['revision'],
                  'experiment_id': self.ident, 'runtime_status': 'not_queried', 'execution_success': None}
        if intent is None:
            occupied = any(self.adapter.safe_file(self.root, relative).exists() for relative in (*self.base_targets, 'training/configurations/' + self.ident + '/baseline.json',
                                                      'training/configurations/' + self.ident + '/candidate.json'))
            return {**result, 'status': 'native_files_without_intent' if occupied else 'not_recorded',
                    'intent_sha256': None, 'files': []}
        files = []
        for relative in self.targets(intent['request']):
            expected = intent['files'][relative].encode('utf-8')
            try:
                raw = read_raw(self.adapter.safe_file(self.root, relative))
            except FileNotFoundError:
                raw = None
            files.append({'path': relative, 'expected_sha256': hashlib.sha256(expected).hexdigest(),
                          'current_sha256': hashlib.sha256(raw).hexdigest() if raw is not None else None,
                          'state': 'missing' if raw is None else 'matching' if raw == expected else 'conflict'})
        matches = sum(item['state'] == 'matching' for item in files)
        status = ('conflict' if any(item['state'] == 'conflict' for item in files) else
                  'prepared' if matches == len(files) else 'partially_prepared' if matches else 'intent_saved')
        return {**result, 'status': status, 'intent_sha256': self.sha(intent), 'intent': intent, 'files': files}

    def ensure_unstarted(self) -> None:
        # A local preparation cannot repair a running, fenced or submitted experiment.
        for relative in ('training/jobs/' + self.ident, 'training/fences/' + self.ident + '.json',
                         'ergora/training-submissions/' + self.ident + '.intent.json'):
            if self.adapter.safe_file(self.root, relative).exists():
                raise ValueError('Native job, fence or submission already exists; do not prepare this experiment again')

    def publish(self, intent: dict) -> dict:
        from agent_platform import training as native

        self.confirm_intent(intent)
        observed = self.status(intent)
        if observed['status'] == 'conflict':
            raise ValueError('Native preparation files conflict with the original intent; no files were replaced')
        self.ensure_unstarted()
        if observed['status'] == 'prepared':
            return self.confirm_prepared(intent)
        if self.sha(self.sources(intent['request'])) != self.sha(intent['sources']):
            raise ValueError('Preparation baseline or runner bytes changed; restore the original sources before recovery')
        self.adapter.safe_file(self.root, 'training/registry.lock')
        with TemporaryDirectory(prefix='ergora-experiment-prepare-') as temporary:
            draft = Path(temporary) / 'draft.json'
            draft.write_bytes(_native_bytes(intent['request']['experiment'], 'Experiment draft'))
            native.prepare(draft, intent['request']['runner_template_id'], intent['request']['max_run_seconds'],
                           configuration_materials=intent['request']['configuration_materials'])
        observed = self.status(intent)
        if observed['status'] != 'prepared':
            raise ValueError('Native preparation differs from the confirmed plan; inspect its original intent and files')
        _training_records({'project': self.project['id'], 'repo': self.project['repo'], 'experiment_id': self.ident})
        return self.confirm_prepared(intent)

    def run(self) -> dict:
        self.registration()
        operation = self.payload['operation']
        intent = self.load()
        if operation == 'status':
            return self.observe(intent)
        if operation == 'preview':
            plan = self.plan(self.payload['request'], self.project['revision'])
            return {'project': self.project['id'], 'project_revision': self.project['revision'],
                    'experiment_id': self.ident, 'preview_sha256': self.sha(plan), 'plan': plan,
                    'preparation': self.observe(intent), 'runtime_status': 'not_queried', 'execution_success': None}
        if operation not in ('prepare', 'resume'):
            raise ValueError('Unsupported training preparation operation')
        if operation == 'prepare':
            if intent is not None:
                if (self.payload['preview_sha256'] != self.sha(intent)
                        or self.sha(self.payload['request']) != self.sha(intent['request'])):
                    raise ValueError('Preparation already has an original intent; inspect and resume that intent')
                plan = intent
            else:
                plan = self.plan(self.payload['request'], self.project['revision'])
                if self.payload['preview_sha256'] != self.sha(plan):
                    raise ValueError('Confirm the exact experiment preparation preview SHA-256')
        elif intent is None or self.payload['intent_sha256'] != self.sha(intent):
            raise ValueError('Recovery requires the exact original preparation intent SHA-256')
        lock = self.path('.lock')
        lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with file_lock(lock, blocking=False):
            intent = self.load()
            if operation == 'prepare':
                if intent is not None:
                    if self.sha(intent) != self.sha(plan):
                        raise ValueError('Another preparation intent owns this experiment ID')
                    return self.confirm_prepared(intent)
                if self.status(None)['status'] != 'not_recorded':
                    raise ValueError('Native experiment files have no matching preparation intent; inspect the original records')
                for relative in (*self.targets(plan['request']), 'training/registry.lock'):
                    self.adapter.safe_file(self.root, relative)
                if self.sha(self.sources(plan['request'])) != self.sha(plan['sources']):
                    raise ValueError('Preparation sources changed after preview; preview again')
                self.ensure_unstarted()
                _native_bytes(plan, 'Preparation intent', _INTENT_LIMIT)
                self.core.write(self.path('.intent.json'), plan)
                intent = plan
            else:
                if intent is None or self.payload['intent_sha256'] != self.sha(intent):
                    raise ValueError('Original preparation intent changed during recovery')
                if self.sha(self.plan(intent['request'], intent['project_revision'])) != self.sha(intent):
                    raise ValueError('Original preparation sources or native plan changed; no files were replaced')
            return self.publish(intent)


def main() -> None:
    from agent_platform.core import Blocked

    try:
        print(json.dumps(_Preparation(json.load(sys.stdin)).run(), ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked, subprocess.SubprocessError) as error:
        raise SystemExit('BLOCKED: ' + str(error))
