"""Freeze one native preparation plan; explicitly recover its immutable files."""

from copy import deepcopy
import getpass
import os
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from ergora.training.native import _training_records
from ergora.training.runtime.context import _TrainingProject, _native_bytes
from ergora.storage.state import file_lock
from ergora.training.configuration import validate_runner, bind_cpu_execution_contract
from ergora.training.materials import confirm_file, material_plan, read_raw
import ergora.training.materials as materials


_INTENT_LIMIT = 16 * 1_048_576


class _Preparation(_TrainingProject):
    def __init__(self, payload: dict):
        super().__init__(payload)
        self.ident = self.core.slug(payload['experiment_id'])
        self.prefix = 'ergora/training-preparations/' + self.ident
        self.base_targets = ('training/manifests/' + self.ident + '.json',
                        'training/projects/' + self.project['id'] + '/perf/experiments/' + self.ident + '/manifest.json',
                        'training/specs/' + self.ident + '.json')
        self.identity = {'schema_version': 2, 'operation': 'prepare-training',
                         'control_home': payload['control_home'], 'project': self.project['id'],
                         'repo': self.project['repo'], 'execution': self.execution,
                         'registration_sha256': self.project['registration']['sha256'], 'experiment_id': self.ident}

    def path(self, suffix: str) -> Path:
        return self.adapter.safe_file(self.root, self.prefix + suffix)

    def targets(self, request):
        supplied = request['configuration_materials']
        return (*self.base_targets, *material_plan(self.ident, supplied)[1]) if supplied is not None else self.base_targets

    def confirm_intent(self, intent):
        raw = _native_bytes(intent, 'Preparation intent', _INTENT_LIMIT)
        confirm_file(self.path('.intent.json'), raw, self.root)
        if self.sha(self.load()) != self.sha(intent):
            raise ValueError('Original preparation intent identity changed during durable readback')

    def confirm_prepared(self, intent):
        self.confirm_intent(intent)
        acceptance = self.cpu_admission(intent)
        if acceptance is not None and acceptance['state'] == 'matching':
            confirm_file(acceptance['path'], acceptance['raw'], self.root)
        observed = self.status(intent)
        if observed['status'] == 'prepared':
            for relative, text in intent['files'].items():
                confirm_file(self.adapter.safe_file(self.root, relative), text.encode('utf-8'), self.root)
            acceptance = self.cpu_admission(intent)
            if acceptance is not None:
                confirm_file(acceptance['path'], acceptance['raw'], self.root)
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
            intent = materials.decode_record(read_raw(self.path('.intent.json'), _INTENT_LIMIT))
        except FileNotFoundError:
            return None
        checked = materials.validate_preparation_intent(intent)
        body = checked['body']
        expected = {**self.identity, 'schema_version': body['schema_version']}
        if (any(body.get(key) != value for key, value in expected.items())
                or type(body.get('project_revision')) is not int or body['project_revision'] < 1
                or set(body) != set(expected) | {'project_revision', 'request', 'sources', 'files'}
                or set(body['files']) != set(self.targets(body['request']))
                or body['request']['experiment']['experiment_id'] != self.ident):
            raise ValueError('Training preparation intent differs from its original project or experiment')
        return intent

    def cpu_admission(self, intent, *, create=False):
        expected = materials.make_cpu_preparation_admission(intent)
        if expected is None:
            return None
        path = self.path('.cpu-contract-admission.json')
        raw = materials.observation_bytes(expected) + b'\n'
        try:
            original = read_raw(path)
        except FileNotFoundError:
            if not create:
                return {'path': path, 'raw': raw, 'state': 'missing'}
            self.ensure_unstarted()
            from ergora.training.cycles import assert_preparation_unconsumed
            assert_preparation_unconsumed(self.payload['control_home'], self.project['id'], self.ident, expected['manifest_sha256'])
            bind_cpu_execution_contract(materials.cpu_contract(intent['request']['experiment']),
                                        intent['sources']['runner']['document'])
            materials.publish_material(path, raw, self.root)
            original = read_raw(path)
        if original != raw:
            raise ValueError('Original CPU contract acceptance is corrupt or belongs to another intent')
        materials.validate_cpu_preparation_admission(materials.decode_record(original), intent,
            intent['files']['training/manifests/' + self.ident + '.json'].encode('utf-8'),
            intent['sources']['runner']['document'])
        if create:
            confirm_file(path, original, self.root)
        return {'path': path, 'raw': original, 'state': 'matching'}

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
        request = deepcopy(request)
        execution = request['experiment'].get('execution', {})
        if 'cpu_contract' in execution:
            execution['cpu_contract'] = bind_cpu_execution_contract(execution['cpu_contract'], sources['runner']['document'])
            supplied = request.get('configuration_materials')
            if supplied is not None:
                for arm in ('baseline', 'candidate'):
                    materials.validate_cpu_contract_configuration(execution['cpu_contract'], supplied[arm]['utf8'].encode('utf-8'))
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
            occupied = self.path('.cpu-contract-admission.json').exists() or self.path('.cpu-contract-admission.json').is_symlink() or any(self.adapter.safe_file(self.root, relative).exists() for relative in (*self.base_targets, 'training/configurations/' + self.ident + '/baseline.json',
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
        acceptance = self.cpu_admission(intent)
        if acceptance is not None:
            files.append({'path': acceptance['path'].relative_to(self.root).as_posix(),
                'expected_sha256': hashlib.sha256(acceptance['raw']).hexdigest(),
                'current_sha256': hashlib.sha256(acceptance['raw']).hexdigest() if acceptance['state'] == 'matching' else None,
                'state': acceptance['state']})
        matches = sum(item['state'] == 'matching' for item in files)
        status = ('conflict' if any(item['state'] == 'conflict' for item in files) else
                  'prepared' if matches == len(files) else 'partially_prepared' if matches else 'intent_saved')
        checked = materials.validate_preparation_intent(intent)
        return {**result, 'status': status, 'intent_sha256': checked['intent_sha256'],
                'confirmed_preview_sha256': checked['preview_sha256'], 'intent': intent, 'files': files}

    def ensure_unstarted(self) -> None:
        # A local preparation cannot repair a running, fenced or submitted experiment.
        for relative in ('training/jobs/' + self.ident, 'training/fences/' + self.ident + '.json',
                         'ergora/training-submissions/' + self.ident + '.intent.json',
                         'ergora/training-submissions/' + self.ident + '.attempt.json',
                         'ergora/training-submissions/' + self.ident + '.budget'):
            if self.adapter.safe_file(self.root, relative).exists() or self.adapter.safe_file(self.root, relative).is_symlink():
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
        self.cpu_admission(intent, create=True)
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
            body = self.plan(self.payload['request'], self.project['revision'])
            return {'project': self.project['id'], 'project_revision': self.project['revision'],
                    'experiment_id': self.ident, 'preview_sha256': self.sha(body), 'plan': body,
                    'preparation': self.observe(intent), 'runtime_status': 'not_queried', 'execution_success': None}
        if operation not in ('prepare', 'resume'):
            raise ValueError('Unsupported training preparation operation')
        if intent is not None and intent['schema_version'] != 2:
            raise ValueError('Historical preparation data is read-only; no current publication or acceptance is synthesized')
        body = None
        if operation == 'prepare':
            if intent is None:
                body = self.plan(self.payload['request'], self.project['revision'])
            else:
                body = materials.preparation_preview_body(intent)
                requested = deepcopy(self.payload['request'])
                value = requested['experiment'].get('execution', {}).get('cpu_contract')
                if isinstance(value, dict) and value.get('kind') == 'training-cpu-execution-declaration':
                    original = materials.cpu_contract(body['request']['experiment'])
                    expected = {'kind': value['kind'], **{key: original[key] for key in ('operation', 'conformance', 'input_domain')}} if original else None
                    if value != expected:
                        raise ValueError('Original CPU declaration changed after exact preview')
                    requested['experiment']['execution']['cpu_contract'] = original
                if self.sha(requested) != self.sha(body['request']):
                    raise ValueError('Preparation already has a different original request')
            if self.payload['preview_sha256'] != self.sha(body):
                raise ValueError('Confirm the exact experiment preparation preview SHA-256')
        elif intent is None or self.payload['intent_sha256'] != self.sha(intent):
            raise ValueError('Recovery requires the exact original preparation intent SHA-256')
        lock = self.path('.lock')
        lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with file_lock(lock, blocking=False):
            intent = self.load()
            if operation == 'prepare':
                if intent is not None:
                    if self.sha(materials.preparation_preview_body(intent)) != self.sha(body):
                        raise ValueError('Another preparation intent owns this experiment ID')
                    return self.confirm_prepared(intent)
                else:
                    if self.status(None)['status'] != 'not_recorded':
                        raise ValueError('Native experiment files have no matching preparation intent; inspect original records')
                    for relative in (*self.targets(body['request']), 'training/registry.lock'):
                        self.adapter.safe_file(self.root, relative)
                    if self.sha(self.sources(body['request'])) != self.sha(body['sources']):
                        raise ValueError('Preparation sources changed after preview; preview again')
                    self.ensure_unstarted()
                    intent = {**body, 'confirmed_preview_sha256': self.sha(body), 'confirmation': {
                        'kind': 'training-preparation-confirmation', 'actor_id': f'unix:{os.getuid()}:{getpass.getuser()}',
                        'project_revision': body['project_revision'], 'request_sha256': self.sha(body['request'])}}
                    materials.validate_preparation_intent(intent)
                    _native_bytes(intent, 'Preparation intent', _INTENT_LIMIT)
                    self.core.write(self.path('.intent.json'), intent)
            else:
                if intent is None or self.payload['intent_sha256'] != self.sha(intent):
                    raise ValueError('Original preparation intent changed during recovery')
                checked = materials.validate_preparation_intent(intent)
                if self.sha(self.plan(intent['request'], intent['project_revision'])) != checked['preview_sha256']:
                    raise ValueError('Original preparation sources or native plan changed; no files were replaced')
            return self.publish(intent)


def main() -> None:
    from agent_platform.core import Blocked

    try:
        print(json.dumps(_Preparation(json.load(sys.stdin)).run(), ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked, subprocess.SubprocessError) as error:
        raise SystemExit('BLOCKED: ' + str(error))
