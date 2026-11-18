"""Finite configuration materials bind to the original native preparation and recovery."""

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from ergora import projects, reference, tasks, training, training_search
from ergora.state import State
from test_task_creation import creation_project
from test_task_export import export as export_candidate, export_client, export_task as _original_export_task
from test_task_submission import native_client
from test_training import experiments, registration
from test_training_runtime import installation
from test_training_preparation import stop_after
from test_training_runner import configuration_source
from test_training_submission import (assert_budget_process_stopped, native_budget_create, prepared, service,
                                      stop_controller_test_owner)


@pytest.fixture
def export_task(creation_project, native_client, request, installation, tmp_path):
    """Give the existing formal export fixture its declared SDK in its own venv."""
    temporalio = pytest.importorskip('temporalio')
    interpreter = Path(installation) / '.venv/bin/python'
    site = Path(temporalio.__file__).parent.parent
    location = subprocess.run([str(interpreter), '-P', '-c',
        'import sysconfig;print(sysconfig.get_path("purelib"))'], capture_output=True, text=True, check=True, timeout=10)
    path = Path(location.stdout.strip()) / 'ergora-test-sdk.pth'
    path.write_text(str(site) + '\n')
    observed = subprocess.run([str(interpreter), '-P', '-c',
        'import json,temporalio,ergora;print(json.dumps({"temporalio":temporalio.__file__,"sdk_version":temporalio.__version__,"ergora":ergora.__file__}))'],
        capture_output=True, text=True, check=True, timeout=10)
    imports = json.loads(observed.stdout)
    assert Path(imports['ergora']).resolve() == Path(reference.__file__).with_name('__init__.py').resolve()
    (tmp_path / 'native-sdk-reuse.json').write_text(json.dumps({
        'pth': str(path), 'content': path.read_text(), 'imports': imports}, indent=2) + '\n')
    return _original_export_task.__wrapped__(creation_project, native_client, request)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical_sha(value):
    return _sha(json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':'), allow_nan=False).encode('utf-8'))


def _files(*roots):
    return {path: path.read_bytes() for root in roots for path in root.rglob('*') if path.is_file()}


@pytest.fixture
def search_request():
    original = json.loads((reference.ROOT / 'platform/templates/training-optimization/experiment.json').read_bytes())
    template = {key: ('c' * 64 if value == 'REPLACE_SHA256' else value) for key, value in original.items()
                if key not in ('experiment_id', 'candidate_config_sha256', 'performance_policy')}
    # Preserve noncanonical baseline bytes, including its BOM, separately from candidate serialization.
    baseline = '\ufeff{ "training": {"global_batch_size": 128, "micro_batch_size": 4},\n "model": {"width": 64}, "precision": "float32" }\r\n'
    template.update(execution={'operation': 'full-verify'},
                    baseline_id='baseline-one', baseline_commit='a' * 40, candidate_commit='a' * 40,
                    base_config_sha256=_sha(baseline.encode('utf-8')), contract_approved=True,
                    owner='fixture-owner', author='fixture-implementer',
                    allowed_changes=['Vary global batch size', 'Vary microbatch organization'])
    configuration = json.loads(baseline.lstrip('\ufeff'))
    return {'schema_version': 1, 'kind': 'training-search-request', 'search_id': 'batch-search',
        'experiment_template': template, 'runner': {'runner_template_id': 'trusted', 'max_run_seconds': 300},
        'baseline_configuration': {'format': 'json-v1', 'utf8': baseline, 'sha256': template['base_config_sha256']},
        'configuration': {'format': 'json-v1', 'template': configuration,
            'schema': {'type': 'object', 'additionalProperties': False,
                'required': ['training', 'model', 'precision'], 'properties': {
                    'training': {'type': 'object', 'additionalProperties': False,
                        'required': ['global_batch_size', 'micro_batch_size'], 'properties': {
                            'global_batch_size': {'type': 'integer', 'minimum': 1},
                            'micro_batch_size': {'type': 'integer', 'minimum': 1}}},
                    'model': {'const': {'width': 64}}, 'precision': {'const': 'float32'}}},
            'mutable': [{'path': ['training', 'global_batch_size'], 'change_type': 'batch_size',
                         'allowed_change': template['allowed_changes'][0]},
                        {'path': ['training', 'micro_batch_size'], 'change_type': 'batch_organization',
                         'allowed_change': template['allowed_changes'][1]}]},
        'dimensions': [{'name': 'batch', 'path': ['training', 'global_batch_size'], 'values': [512, 256]}],
        'selection': {'algorithm': 'ordered_grid_v1', 'seed': None, 'max_trials': 3},
        'family_policy': {'version': 'fixed_family_v1', 'family_error_budget': '0.12'},
        'measurement': {'normalization_source_samples': 256,
            'statistics': {'min_pairs': 6, 'bootstrap_resamples': 20000, 'seed': 17},
            'thresholds': {'min_saved_seconds_at_normalization': 0.02, 'min_speedup_percent': 1.5, 'mode': 'all'}},
        'budget': {'wall_seconds': 600, 'cleanup_seconds': 30, 'control_timeout_seconds': 7},
        'analysis': {'source_flow_sha256': 'd' * 64, 'redundancy_sha256': 'e' * 64,
                     'coverage': 'CPU preparation contract only; no training, effective config, quality, or GPU evidence.'},
        'candidate_source': {'kind': 'unchanged_baseline_v1'}}


@pytest.fixture
def search_input(request, search_request, configuration_source):
    if sys.platform != 'linux':
        pytest.skip('Native experiment preparation requires Linux/WSL2')
    pytest.importorskip('temporalio')
    state, definition, runtime, prefix, write = request.getfixturevalue('experiments')
    baseline = json.loads((prefix / 'baseline.json').read_bytes())
    baseline['config_sha256'] = search_request['baseline_configuration']['sha256']
    write(prefix / 'baseline.json', baseline)
    search_request['experiment_template'].update(baseline_commit=baseline['commit'], candidate_commit=baseline['commit'],
                                                workload_fingerprint=baseline['workload_fingerprint'])
    runner = {'schema_version': 2, 'runner_template_id': 'trusted', 'project': 'demo', 'repo': definition['repo'],
              'command': [str(Path(definition['execution']['installation']) / '.venv/bin/python'),
                          '{configuration_driver}', '{configuration_request}'], 'timeout_seconds': 20,
              'configuration_readback': {'protocol': 'training-configuration-driver-v1',
                  'source': configuration_source['reference'], 'prepared_json_format': 'json-v1',
                  'baseline_reference_protocol': None, 'screen': None,
                  'manifest_configuration_role': 'source-bytes',
                  'observation_scheme': 'fixture-cpu-configuration-v1'}}
    write(Path(definition['execution']['config_directory']) / 'training-runners/trusted.json', runner)
    return state, definition, runtime, prefix, search_request


@pytest.fixture
def interrupt_publication(monkeypatch):
    """Kill the real native child after a chosen original file, using its actual search ID."""
    original = reference.processes.run
    fixture = Path(__file__).parent / 'fixtures/training_preparation_process.py'

    def select(ident=None, boundary=None, observe=None):
        def invoke(argv, *args, **kwargs):
            if argv[-1] == 'from ergora.reference_training_preparation import main;main()':
                payload = json.loads(kwargs['stdin'])
                if payload['operation'] == 'prepare' and observe is not None:
                    observe(payload)
                if boundary is not None:
                    argv = [*argv[:-1], f'import runpy;runpy.run_path({str(fixture)!r},run_name="__main__")']
                    kwargs['env'] = {**kwargs['env'], 'ERGORA_TEST_PREPARATION_STOP_AFTER': str(boundary),
                                     'ERGORA_TEST_PREPARATION_ID': ident}
            return original(argv, *args, **kwargs)
        monkeypatch.setattr(reference.processes, 'run', invoke)
    return select


def _prepare(state, request, preview, directory):
    return training_search.prepare(state, 'demo', request, preview['project_revision'],
                                   preview['preview_sha256'], directory)


def test_request_file_is_bounded_strict_json(tmp_path, search_request):
    source = tmp_path / 'request.json'
    encoded = json.dumps(search_request).encode('utf-8')
    for size in (len(encoded), 1_048_575, 1_048_576):
        source.write_bytes(encoded + b' ' * (size - len(encoded)))
        assert training_search.read_request(source) == search_request
    source.write_bytes(encoded + b' ' * (1_048_577 - len(encoded)))
    with pytest.raises(ValueError):
        training_search.read_request(source)
    for raw in (b'{"schema_version":1,"schema_version":1}', b'{"x":NaN}', b'{"x":1e999}',
                b'!!python/object/apply:os.system [echo untrusted]'):
        source.write_bytes(raw)
        with pytest.raises(ValueError):
            training_search.read_request(source)


def test_trailing_newlines_are_rejected_before_reading_a_project_or_native_state(
        tmp_path, search_request, monkeypatch):
    state = State(tmp_path / 'unselected-control')
    reads = []
    def project_read(*args, **kwargs):
        reads.append('project')
        raise AssertionError('Project lookup reached')
    def native_read(*args, **kwargs):
        pytest.fail('Malformed whole-string input reached native preparation')
    monkeypatch.setattr(State, 'project', project_read)
    monkeypatch.setattr(training, 'preview_experiment', native_read)
    # The valid request reaches the guarded boundary, so the rejection is not a missing-project error.
    with pytest.raises(AssertionError, match='Project lookup reached'):
        training_search.preview(state, 'demo', search_request)
    reads.clear()
    for path in (('family_policy', 'family_error_budget'), ('dimensions', 0, 'name'),
                 ('analysis', 'source_flow_sha256')):
        malformed = deepcopy(search_request)
        node = malformed
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] += '\n'
        with pytest.raises(ValueError):
            training_search.preview(state, 'demo', malformed)
    assert reads == []


def test_cli_passes_exact_confirmation_and_directory_to_the_search_owner(tmp_path, search_request, monkeypatch):
    from ergora.cli import main

    source = tmp_path / 'request.json'
    source.write_text(json.dumps(search_request), encoding='utf-8')
    home, directory = tmp_path / 'control', tmp_path / 'search materials'
    calls = []
    def preview(state, project, request):
        calls.append(('preview', state.root, project, request))
        return {'transport': 'preview'}
    def prepare(state, project, request, revision, digest, destination):
        calls.append(('prepare', state.root, project, request, revision, digest, Path(destination)))
        return {'transport': 'prepare'}
    def read(destination, *, sha256=None):
        calls.append(('read', Path(destination), sha256))
        return {'transport': 'read'}
    monkeypatch.setattr(training_search, 'preview', preview)
    monkeypatch.setattr(training_search, 'prepare', prepare)
    monkeypatch.setattr(training_search, 'read', read)
    for operation, args in (
            ('preview', ['search-preview', 'demo', '--request', str(source)]),
            ('prepare', ['search-prepare', 'demo', '--request', str(source), '--revision', '7',
                         '--preview-sha256', 'a' * 64, '--directory', str(directory)]),
            ('read', ['search-read', str(directory), '--sha256', 'b' * 64])):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(['--home', str(home), 'training', *args])
        assert code == 0 and json.loads(output.getvalue()) == {'transport': operation}
    assert calls == [('preview', home, 'demo', search_request),
                     ('prepare', home, 'demo', search_request, 7, 'a' * 64, directory),
                     ('read', directory, 'b' * 64)]


def test_ordered_and_seeded_choices_use_declared_order_without_changing_sources(search_input):
    state, definition, runtime, _, request = search_input
    request['dimensions'].append({'name': 'micro', 'path': ['training', 'micro_batch_size'], 'values': [2, 8]})
    original_request = deepcopy(request)
    before = _files(runtime, Path(definition['execution']['config_directory']))
    ordered = training_search.preview(state, 'demo', request)
    choices = ordered['plan']['choices']
    assert ordered['plan']['cardinality'] == 4
    assert [(item['ordinal'], item['grid_ordinal'], item['combination']) for item in choices] == [
        (0, 0, [['batch', 512], ['micro', 2]]), (1, 1, [['batch', 512], ['micro', 8]]),
        (2, 2, [['batch', 256], ['micro', 2]])]
    request['selection'].update(algorithm='seeded_without_replacement_v1', seed=-19)
    selected = training_search.preview(state, 'demo', request)
    # Independently calculated from the specified SHA ordering for these four combinations.
    assert [item['grid_ordinal'] for item in selected['plan']['choices']] == [3, 2, 1]
    assert training_search.preview(state, 'demo', deepcopy(request)) == selected
    assert original_request['configuration'] == request['configuration']
    assert _files(runtime, Path(definition['execution']['config_directory'])) == before
    assert not (runtime / 'ergora/training-preparations').exists()


def test_typed_scalars_and_maximum_grid_are_accepted_without_expanding_native_trials(search_input):
    state, _, _, _, request = search_input
    request['configuration']['schema']['properties']['training']['properties']['global_batch_size'] = {}
    request['dimensions'][0]['values'] = [True, 1, None]
    choices = training_search.preview(state, 'demo', request)['plan']['choices']
    values = [choice['combination'][0][1] for choice in choices]
    assert [type(value) for value in values] == [bool, int, type(None)]
    request['dimensions'][0]['values'] = list(range(4096))
    request['selection']['max_trials'] = 1
    maximum = training_search.preview(state, 'demo', request)['plan']
    assert maximum['cardinality'] == 4096 and len(maximum['choices']) == 1


@pytest.mark.parametrize('bound', ('depth', 'values'))
def test_preview_rejects_complete_packet_limits_even_when_the_request_is_valid(
        search_input, tmp_path, bound):
    state, definition, runtime, prefix, request = search_input
    if bound == 'depth':
        fixed = 0
        for _ in range(60):
            fixed = {'key': fixed}
    else:
        fixed = [0] * 99_500
    configuration = request['configuration']['template']
    configuration['fixed_material'] = fixed
    request['configuration']['schema'] = {}
    baseline_text = json.dumps(configuration, ensure_ascii=False, separators=(',', ':')) + '\n'
    digest = _sha(baseline_text.encode('utf-8'))
    request['baseline_configuration'].update(utf8=baseline_text, sha256=digest)
    request['experiment_template']['base_config_sha256'] = digest
    baseline_path = prefix / 'baseline.json'
    registered_baseline = json.loads(baseline_path.read_bytes())
    registered_baseline['config_sha256'] = digest
    baseline_path.write_text(json.dumps(registered_baseline) + '\n', encoding='utf-8')
    source = tmp_path / 'request.json'
    encoded = json.dumps(request, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    assert len(encoded) < 1_048_576
    source.write_bytes(encoded)
    # The request is within both data-tree limits; wrapping it with plans adds depth and values.
    assert training_search.read_request(source) == request
    before = _files(runtime, Path(definition['execution']['config_directory']))
    try:
        with pytest.raises(ValueError, match='64 levels / 100000 values'):
            training_search.preview(state, 'demo', request)
    finally:
        assert _files(runtime, Path(definition['execution']['config_directory'])) == before
        assert not (runtime / 'ergora/training-preparations').exists()


def test_invalid_requests_fail_before_native_preview_or_any_publication(search_input, monkeypatch, tmp_path):
    state, definition, runtime, _, original = search_input
    def native_must_not_run(*args, **kwargs):
        pytest.fail('Invalid search data reached native experiment preparation')
    monkeypatch.setattr(training, 'preview_experiment', native_must_not_run)
    before = _files(runtime, Path(definition['execution']['config_directory']))
    invalid = []
    def changed():
        value = deepcopy(original)
        invalid.append(value)
        return value
    changed()['dimensions'][0]['values'] = [1, 1.0]
    changed()['dimensions'][0]['values'] = [0, -0.0]
    changed()['dimensions'][0]['values'] = [{'expression': 'import os'}]
    changed()['dimensions'][0]['path'] = ['training', 'missing']
    changed()['dimensions'].append({'name': 'child', 'path': ['training', 'global_batch_size'], 'values': [1024]})
    changed()['configuration']['template']['model']['width'] = 128
    changed()['configuration']['schema']['properties']['training']['$ref'] = 'https://example.invalid/config.json'
    changed()['configuration']['mutable'][0]['change_type'] = 'model_precision'
    changed()['baseline_configuration']['sha256'] = '0' * 64
    changed()['selection']['max_trials'] = 33
    changed()['measurement']['statistics']['min_pairs'] = True
    changed()['measurement']['statistics']['confidence'] = 0.95
    changed()['experiment_template']['contract_approved'] = False
    changed()['experiment_template']['candidate_commit'] = 'f' * 40
    changed()['candidate_source'] = {'kind': 'exported_six_stage_v1', 'task_id': 'missing-task', 'run_id': 'missing-run',
                                   'creation_sha256': '1' * 64, 'request_sha256': '2' * 64,
                                   'profile_sha256': '3' * 64, 'export_intent_sha256': '4' * 64}
    changed()['unknown'] = 'not an extension point'
    changed()['configuration']['template']['training']['global_batch_size'] = {1, 2}
    overflowing = changed()
    overflowing['dimensions'][0]['values'] = list(range(1, 18))
    overflowing['dimensions'].append({'name': 'micro', 'path': ['training', 'micro_batch_size'], 'values': list(range(1, 242))})
    for request in invalid:
        with pytest.raises(ValueError):
            training_search.preview(state, 'demo', request)
        with pytest.raises(ValueError):
            training_search.prepare(state, 'demo', request, state.project('demo')['revision'], '0' * 64, tmp_path / 'rejected')
    assert not (tmp_path / 'rejected').exists()
    assert _files(runtime, Path(definition['execution']['config_directory'])) == before


def test_two_batch_configurations_prepare_real_native_bindings_and_read_offline(
        search_input, configuration_source, tmp_path, monkeypatch):
    state, definition, runtime, prefix, request = search_input
    originals = _files(runtime, Path(definition['execution']['config_directory']))
    project_before = state.project('demo')
    preview = training_search.preview(state, 'demo', request)
    plan = preview['plan']
    assert plan['family_allocation'] == {'max_trials': 3, 'enabled_thresholds': 2}
    policy = {'normalization_source_samples': 256,
              'statistics': {'min_pairs': 6, 'bootstrap_resamples': 20000, 'seed': 17, 'confidence': 0.98},
              'thresholds': {'min_saved_seconds_at_normalization': 0.02, 'min_speedup_percent': 1.5, 'mode': 'all'}}
    assert plan['performance_policy'] == policy and plan['performance_policy_sha256'] == _canonical_sha(policy)
    directory = tmp_path / 'frozen search'
    result = _prepare(state, request, preview, directory)
    assert result['status'] == 'prepared' and len(result['experiments']) == 2
    assert (directory / 'baseline-config.json').read_bytes() == request['baseline_configuration']['utf8'].encode('utf-8')
    assert len({item['configuration']['sha256'] for item in plan['choices']}) == 2
    assert {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()} == {
        'search.json', 'baseline-config.json', *(item['configuration']['path'] for item in plan['choices'])}
    for item, prepared, batch in zip(plan['choices'], result['experiments'], (512, 256)):
        raw = (directory / item['configuration']['path']).read_bytes()
        assert _sha(raw) == item['configuration']['sha256']
        candidate = json.loads(raw)
        assert raw == (json.dumps(candidate, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
        assert candidate == {'training': {'global_batch_size': batch, 'micro_batch_size': 4},
                             'model': {'width': 64}, 'precision': 'float32'}
        ident = item['experiment_id']
        assert prepared['experiment_id'] == ident and prepared['status'] == 'prepared'
        assert prepared['intent_sha256'] == item['native_preview_sha256']
        for path, text in item['native_plan']['files'].items():
            assert (runtime / path).read_bytes() == text.encode('utf-8')
        manifest_raw = (runtime / f'training/manifests/{ident}.json').read_bytes()
        manifest = json.loads(manifest_raw)
        assert manifest['performance_policy'] == policy
        assert manifest['candidate_config_sha256'] == _sha(raw)
        assert manifest['base_config_sha256'] == request['baseline_configuration']['sha256']
        assert manifest['baseline_id'] == 'baseline-one' and manifest['baseline_commit'] == manifest['candidate_commit']
        assert (prefix / f'experiments/{ident}/manifest.json').read_bytes() == manifest_raw
        spec = json.loads((runtime / f'training/specs/{ident}.json').read_bytes())
        assert spec['binding']['manifest_sha'] == prepared['manifest_sha256'] == _sha(manifest_raw)
        assert spec['manifest_uri'] == (runtime / f'training/manifests/{ident}.json').as_uri()
        assert not (runtime / f'training/jobs/{ident}').exists()
        assert not (runtime / f'training/fences/{ident}.json').exists()
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert state.project('demo') == project_before
    saved = _files(runtime, directory)
    original_spec = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original_spec(name))
    def no_native(*args, **kwargs):
        pytest.fail('Offline packet reading contacted native preparation')
    monkeypatch.setattr(reference.processes, 'run', no_native)
    # Offline packet verification uses frozen declarations even when the live
    # source has disappeared and application state cannot be instantiated.
    source = configuration_source['source']
    source.rename(source.with_name(source.name + '-unavailable'))
    monkeypatch.setattr(State, '__init__', lambda *args, **kwargs: pytest.fail('Offline reader created State'))
    observed = training_search.read(directory, sha256=result['sha256'])
    assert observed['plan'] == plan and observed['sha256'] == _sha((directory / 'search.json').read_bytes())
    assert observed['coverage']['configuration_execution'] == 'requires-original-managed-execution'
    assert observed['coverage']['runtime_status'] == 'not_queried'
    from ergora.cli import main
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'search-read', str(directory), '--sha256', result['sha256']])
    assert code == 0 and json.loads(output.getvalue()) == observed
    # A fresh interpreter also reads the same packet when all SDK imports are unavailable.
    program = '''import importlib.abc,json,sys
class NoSDK(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'temporalio' or fullname.startswith('temporalio.'):
            raise ModuleNotFoundError('SDK unavailable in the offline reader')
sys.meta_path.insert(0, NoSDK())
from ergora.training_search import read
from ergora.state import State
State.__init__ = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('Offline reader constructed State'))
print(json.dumps(read(sys.argv[1],sha256=sys.argv[2]),ensure_ascii=False))
'''
    offline = subprocess.run([sys.executable, '-c', program, str(directory), result['sha256']],
                             capture_output=True, text=True, encoding='utf-8', timeout=20)
    assert offline.returncode == 0, offline.stdout + offline.stderr
    assert json.loads(offline.stdout) == observed
    assert _files(runtime, directory) == saved


@pytest.mark.skipif(sys.platform != 'linux' or importlib.util.find_spec('temporalio') is None,
                    reason='Original native source export requires Linux/WSL2 and the Temporal SDK')
def test_completed_original_six_stage_export_binds_source_without_another_export(
        export_task, export_client, search_request, configuration_source, tmp_path, monkeypatch):
    state, definition, _, _ = export_task
    exported = export_candidate(export_task)
    assert exported['status'] == 'exported'
    created = tasks.creation(state, 'demo', 'new-task')
    original = tasks.show(state, 'demo', 'new-task')
    runtime = Path(definition['execution']['state_directory'])
    config = Path(definition['execution']['config_directory'])
    commit = state.project('demo')['registration']['definition']['base_sha']
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + '\n', encoding='utf-8')
    write(runtime / 'training/projects/demo/perf/baseline.json', {
        'baseline_id': 'baseline-one', 'commit': commit,
        'config_sha256': search_request['baseline_configuration']['sha256'],
        'workload_fingerprint': search_request['experiment_template']['workload_fingerprint'],
        'evidence_uri': 'synthetic:test', 'quality_scope': 'CPU preparation contract only'})
    write(config / 'training-runners/trusted.json', {
        'schema_version': 2, 'runner_template_id': 'trusted', 'project': 'demo', 'repo': definition['repo'],
        'command': [sys.executable, '{configuration_driver}', '{configuration_request}'], 'timeout_seconds': 30,
        'configuration_readback': {'protocol': 'training-configuration-driver-v1',
            'source': configuration_source['reference'], 'prepared_json_format': 'json-v1',
                  'baseline_reference_protocol': None, 'screen': None,
            'manifest_configuration_role': 'source-bytes',
            'observation_scheme': 'fixture-cpu-configuration-v1'}})
    search_request['experiment_template'].update(baseline_commit=commit, candidate_commit=exported['candidate_sha'])
    search_request['candidate_source'] = {
        'kind': 'exported_six_stage_v1', 'task_id': 'new-task', 'run_id': exported['run_id'],
        'creation_sha256': created['intent_sha256'], 'request_sha256': original['request_sha256'],
        'profile_sha256': original['profile_sha256'], 'export_intent_sha256': exported['intent_sha256']}
    before = _files(runtime, config)
    def no_new_source_effect(*args, **kwargs):
        pytest.fail('Search preparation attempted another source export or service inspection')
    monkeypatch.setattr(tasks, 'export', no_new_source_effect)
    monkeypatch.setattr(tasks, 'inspect_export', no_new_source_effect)
    monkeypatch.setattr(tasks, 'exported_source_candidate', no_new_source_effect)
    preview = training_search.preview(state, 'demo', search_request)
    source = preview['plan']['candidate_source']
    assert source['kind'] == 'exported_six_stage_v1'
    assert source['records']['creation'] == created and source['records']['task'] == original
    assert source['records']['export']['intent_sha256'] == exported['intent_sha256']
    assert _prepare(state, search_request, preview, tmp_path / 'source search')['status'] == 'prepared'
    assert all(path.read_bytes() == raw for path, raw in before.items())
    saved = _files(runtime, config)
    def no_native_preview(*args, **kwargs):
        pytest.fail('Wrong source binding reached native experiment preparation')
    monkeypatch.setattr(training, 'preview_experiment', no_native_preview)
    for key, value in (('run_id', 'different-run'), ('request_sha256', '1' * 64),
                       ('profile_sha256', '2' * 64), ('export_intent_sha256', '3' * 64)):
        altered = deepcopy(search_request)
        altered['candidate_source'][key] = value
        with pytest.raises(ValueError):
            training_search.preview(state, 'demo', altered)
    assert _files(runtime, config) == saved


@pytest.mark.parametrize('boundary,matching', ((4, 1), (5, 2), (1, 3), (2, 4), (3, 5)))
def test_partial_native_publication_resumes_frozen_choices_without_reenumeration(
        search_input, tmp_path, monkeypatch, interrupt_publication, boundary, matching):
    state, _, runtime, _, request = search_input
    preview = training_search.preview(state, 'demo', request)
    directory = tmp_path / 'search'
    choices = preview['plan']['choices']
    seen = []
    def packet_precedes_intent(payload):
        observed = training_search.read(directory)
        assert observed['plan'] == preview['plan']
        assert not (runtime / f"ergora/training-preparations/{choices[0]['experiment_id']}.intent.json").exists()
        seen.append(payload['experiment_id'])
    interrupt_publication(choices[0]['experiment_id'], boundary, packet_precedes_intent)
    with pytest.raises(ValueError, match='status 73'):
        _prepare(state, request, preview, directory)
    assert seen == [choices[0]['experiment_id']]
    first = training.preparation(state, 'demo', choices[0]['experiment_id'])
    assert first['status'] == ('prepared' if matching == 5 else 'partially_prepared')
    assert sum(item['state'] == 'matching' for item in first['files']) == matching
    frozen = _files(directory)
    published = {runtime / relative: (runtime / relative).read_bytes()
                 for relative in choices[0]['native_plan']['files'] if (runtime / relative).exists()}
    interrupt_publication()
    if boundary == 4:
        path, original_raw = next(iter(published.items()))
        path.write_bytes(original_raw + b'\n')
        conflicting = _files(runtime, directory)
        with pytest.raises(ValueError):
            _prepare(state, request, preview, directory)
        assert _files(runtime, directory) == conflicting
        path.write_bytes(original_raw)
    def no_new_preview(*args, **kwargs):
        pytest.fail('Recovery regenerated the frozen search or a native preview')
    monkeypatch.setattr(training_search, 'preview', no_new_preview)
    monkeypatch.setattr(training, 'preview_experiment', no_new_preview)
    recovered = _prepare(State(state.root), request, preview, directory)
    assert recovered['status'] == 'prepared'
    assert [item['experiment_id'] for item in recovered['experiments']] == [item['experiment_id'] for item in choices]
    assert [item['intent_sha256'] for item in recovered['experiments']] == [item['native_preview_sha256'] for item in choices]
    assert _files(directory) == frozen
    assert all(path.read_bytes() == raw for path, raw in published.items())


def test_actual_lost_native_reply_and_prepared_repeat_keep_one_original_intent(search_input, tmp_path, monkeypatch):
    state, _, runtime, _, request = search_input
    preview = training_search.preview(state, 'demo', request)
    directory = tmp_path / 'search'
    original = reference.processes.run
    lost = []
    def lose_success(argv, *args, **kwargs):
        result = original(argv, *args, **kwargs)
        if argv[-1] == 'from ergora.reference_training_preparation import main;main()':
            payload = json.loads(kwargs['stdin'])
            if payload['operation'] == 'prepare' and not lost:
                assert result['status'] == 'succeeded'
                lost.append(payload['experiment_id'])
                raise ValueError('Lost actual native preparation success reply')
        return result
    monkeypatch.setattr(reference.processes, 'run', lose_success)
    with pytest.raises(ValueError, match='Lost actual native'):
        _prepare(state, request, preview, directory)
    assert lost == [preview['plan']['choices'][0]['experiment_id']]
    assert training.preparation(state, 'demo', lost[0])['status'] == 'prepared'
    monkeypatch.setattr(reference.processes, 'run', original)
    first_intent = runtime / f'ergora/training-preparations/{lost[0]}.intent.json'
    original_intent = first_intent.read_bytes()
    recovered = _prepare(State(state.root), request, preview, directory)
    assert recovered['status'] == 'prepared' and first_intent.read_bytes() == original_intent
    saved = _files(runtime, directory)
    def no_write_operation(*args, **kwargs):
        pytest.fail('A fully prepared repeat attempted another native publication')
    monkeypatch.setattr(training, 'prepare_experiment', no_write_operation)
    monkeypatch.setattr(training, 'resume_prepare', no_write_operation)
    assert _prepare(state, request, preview, directory)['status'] == 'prepared'
    assert _files(runtime, directory) == saved


@pytest.mark.parametrize('failure_at', ('file', 'directory', 'ancestor'))
def test_visible_packet_sync_failure_has_no_native_intent_and_recovers_without_preview(
        search_input, tmp_path, monkeypatch, failure_at):
    state, _, runtime, _, request = search_input
    preview = training_search.preview(state, 'demo', request)
    directory = tmp_path / 'newA/newB/search' if failure_at == 'ancestor' else tmp_path / 'search'
    original = os.fsync
    failures = []
    def fail_sync(descriptor):
        descriptor_stat = os.fstat(descriptor)
        directory_descriptor = stat.S_ISDIR(descriptor_stat.st_mode)
        target = (directory_descriptor and (tmp_path / 'newA').exists()
                  and os.path.samestat(descriptor_stat, (tmp_path / 'newA').stat())
                  if failure_at == 'ancestor' else directory_descriptor == (failure_at == 'directory'))
        if directory.exists() and target:
            failures.append(failure_at)
            raise OSError('Original packet sync failed after it became visible')
        return original(descriptor)
    monkeypatch.setattr(os, 'fsync', fail_sync)
    try:
        with pytest.raises(OSError, match='packet sync failed'):
            _prepare(state, request, preview, directory)
    finally:
        assert not (runtime / 'ergora/training-preparations').exists()
    assert failures == [failure_at]
    assert training_search.read(directory)['plan'] == preview['plan']
    frozen = _files(directory)
    monkeypatch.setattr(os, 'fsync', original)
    def no_new_preview(*args, **kwargs):
        pytest.fail('Recovery replaced the visible original packet after its sync failure')
    monkeypatch.setattr(training_search, 'preview', no_new_preview)
    monkeypatch.setattr(training, 'preview_experiment', no_new_preview)
    recovered = _prepare(State(state.root), request, preview, directory)
    assert recovered['status'] == 'prepared' and _files(directory) == frozen
    assert [item['intent_sha256'] for item in recovered['experiments']] == [
        item['native_preview_sha256'] for item in preview['plan']['choices']]


def test_revision_source_drift_and_packet_corruption_preserve_partial_originals(
        search_input, tmp_path, monkeypatch, interrupt_publication):
    state, definition, runtime, prefix, request = search_input
    preview = training_search.preview(state, 'demo', request)
    directory = tmp_path / 'search'
    choice = preview['plan']['choices'][0]
    with pytest.raises(ValueError):
        training_search.prepare(state, 'demo', request, preview['project_revision'], '0' * 64, directory)
    assert not directory.exists() and not (runtime / 'ergora/training-preparations').exists()
    directory.mkdir()
    with pytest.raises(ValueError):
        _prepare(state, request, preview, directory)
    assert list(directory.iterdir()) == []
    directory.rmdir()
    foreign = runtime / f"training/manifests/{preview['plan']['choices'][1]['experiment_id']}.json"
    foreign.write_bytes(b'{"foreign":"preserve unrelated second experiment"}\n')
    with pytest.raises(ValueError):
        _prepare(state, request, preview, directory)
    assert foreign.read_bytes() == b'{"foreign":"preserve unrelated second experiment"}\n'
    assert not directory.exists() and not (runtime / 'ergora/training-preparations').exists()
    foreign.unlink()
    interrupt_publication(choice['experiment_id'], 1)
    with pytest.raises(ValueError, match='status 73'):
        _prepare(state, request, preview, directory)
    interrupt_publication()
    original_packet = (directory / 'search.json').read_bytes()
    saved = _files(runtime, directory, Path(definition['execution']['config_directory']))
    outside = tmp_path / 'unrelated-config.json'
    outside.write_bytes(b'{"unrelated":"preserved"}\n')
    for mutate in ('policy', 'policy-number-kind', 'native-request-number-kind', 'native-plan',
                   'cardinality', 'coverage', 'frozen-source', 'config', 'extra-file', 'config-symlink'):
        packet = json.loads(original_packet)
        if mutate == 'policy':
            packet['performance_policy']['statistics']['confidence'] = 0.97
        elif mutate == 'policy-number-kind':
            statistics = packet['performance_policy']['statistics']
            statistics['min_pairs'] = float(statistics['min_pairs'])
        elif mutate == 'native-request-number-kind':
            statistics = packet['choices'][0]['native_request']['experiment']['performance_policy']['statistics']
            statistics['min_pairs'] = float(statistics['min_pairs'])
        elif mutate == 'native-plan':
            packet['choices'][0]['native_plan']['request']['experiment']['notes'] = 'changed native request'
        elif mutate == 'cardinality':
            packet['cardinality'] = 2.0
        elif mutate == 'coverage':
            packet['coverage']['execution_authorized'] = 0
        elif mutate == 'frozen-source':
            for native in packet['choices']:
                native['native_plan']['sources']['runner']['document']['configuration_readback']['source']['commit'] = 'x' * 40
                native['native_preview_sha256'] = _canonical_sha(native['native_plan'])
        elif mutate == 'config':
            (directory / choice['configuration']['path']).write_text('{"changed":true}\n')
        elif mutate == 'extra-file':
            (directory / 'unexpected.json').write_text('{}')
        else:
            (directory / choice['configuration']['path']).unlink()
            (directory / choice['configuration']['path']).symlink_to(outside)
        if mutate in ('policy', 'policy-number-kind', 'native-request-number-kind', 'native-plan', 'cardinality', 'coverage', 'frozen-source'):
            (directory / 'search.json').write_text(json.dumps(packet), encoding='utf-8')
        with pytest.raises(ValueError):
            training_search.read(directory)
        with pytest.raises(ValueError):
            _prepare(state, request, preview, directory)
        assert _files(runtime, Path(definition['execution']['config_directory'])) == {
            path: raw for path, raw in saved.items() if directory not in path.parents}
        if mutate == 'extra-file':
            (directory / 'unexpected.json').unlink()
        if mutate == 'config-symlink':
            (directory / choice['configuration']['path']).unlink()
            assert outside.read_bytes() == b'{"unrelated":"preserved"}\n'
        for path, raw in saved.items():
            path.write_bytes(raw)
    baseline = prefix / 'baseline.json'
    baseline_value = json.loads(baseline.read_bytes())
    baseline_value['quality_scope'] = 'Drift after the original packet and first native manifest'
    baseline.write_text(json.dumps(baseline_value), encoding='utf-8')
    drifted = _files(runtime, directory, Path(definition['execution']['config_directory']))
    with pytest.raises(ValueError):
        _prepare(state, request, preview, directory)
    assert _files(runtime, directory, Path(definition['execution']['config_directory'])) == drifted
    baseline.write_bytes(saved[baseline])
    projects.bind(state, 'demo', 'memory', {'tool': 'sqlite'}, preview['project_revision'])
    with pytest.raises(ValueError):
        _prepare(state, request, preview, directory)
    assert _files(directory) == {path: raw for path, raw in saved.items() if directory in path.parents}
    assert not (runtime / f"training/specs/{choice['experiment_id']}.json").exists()


@pytest.fixture
def search_execution(search_input, service, configuration_source, tmp_path, request):
    """External JSON, one unchanged source commit, and the original managed CPU path."""
    state, definition, runtime, prefix, search_request = search_input
    options = dict(getattr(request, 'param', {}))
    screen_support = options.pop('screen_support', False)
    if options.pop('baseline_reference_support', False):
        runner_path = Path(definition['execution']['config_directory']) / 'training-runners/trusted.json'
        runner = json.loads(runner_path.read_bytes())
        runner['configuration_readback']['baseline_reference_protocol'] = 'baseline-reference-v1'
        if screen_support:
            runner['configuration_readback']['screen'] = {'protocol': 'training-screen-v1',
                                                         'scheme': 'fixture-cpu-screen-v1'}
        runner_path.write_text(json.dumps(runner) + '\n')
    baseline = '\ufeff{ "global_batch": 12, "microbatch": 3, "strategy": "redundant-loop"'
    if options:
        baseline += ', ' + json.dumps(options)[1:-1]
    baseline += ' }\r\n'
    search_request['experiment_template']['allowed_changes'].append('Remove redundant exact arithmetic')
    candidate = {'global_batch': 24, 'microbatch': 6, 'strategy': 'closed-form', **options}
    search_request['baseline_configuration'] = {'format': 'json-v1', 'utf8': baseline,
                                               'sha256': _sha(baseline.encode('utf-8'))}
    search_request['configuration'] = {
        'format': 'json-v1', 'template': candidate,
        'schema': {'type': 'object', 'additionalProperties': False,
                   'required': list(candidate), 'properties': {
                       name: {'type': 'integer' if type(value) is int else 'string'}
                       for name, value in candidate.items()}},
        'mutable': [{'path': ['global_batch'], 'change_type': 'batch_size',
                     'allowed_change': search_request['experiment_template']['allowed_changes'][0]},
                    {'path': ['microbatch'], 'change_type': 'batch_organization',
                     'allowed_change': search_request['experiment_template']['allowed_changes'][1]},
                    {'path': ['strategy'], 'change_type': 'execution_parameter',
                     'allowed_change': search_request['experiment_template']['allowed_changes'][2]}]}
    search_request['dimensions'] = [{'name': 'batch', 'path': ['global_batch'], 'values': [24, 48]},
                                    {'name': 'chunk', 'path': ['microbatch'], 'values': [6]}]
    search_request['selection']['max_trials'] = 2
    search_request['measurement'] = {'normalization_source_samples': 48,
        'statistics': {'min_pairs': 4, 'bootstrap_resamples': 1000, 'seed': 73},
        'thresholds': {'min_saved_seconds_at_normalization': .001,
                       'min_speedup_percent': None, 'mode': 'all'}}
    search_request['budget'] = {'wall_seconds': 90, 'cleanup_seconds': 15, 'control_timeout_seconds': 10}
    search_request['experiment_template'].update(
        base_config_sha256=_sha(baseline.encode('utf-8')), track='E', quality_required=False,
        checks_required=['cpu_exact_configuration'])
    baseline_path = prefix / 'baseline.json'
    baseline_record = json.loads(baseline_path.read_bytes())
    baseline_record['config_sha256'] = search_request['baseline_configuration']['sha256']
    baseline_path.write_text(json.dumps(baseline_record) + '\n')
    source_commit = baseline_record['commit']
    assert configuration_source['git'](Path(definition['repo']), 'ls-tree', '-r', '--name-only', source_commit) == ''
    assert search_request['experiment_template']['baseline_commit'] == source_commit
    assert search_request['experiment_template']['candidate_commit'] == source_commit
    preview = training_search.preview(state, 'demo', search_request)
    directory = tmp_path / 'external-json-search'
    published = _prepare(state, search_request, preview, directory)
    assert not configuration_source['markers'].exists()
    assert not (state.root / 'training-cycles').exists()
    return {'state': state, 'definition': definition, 'runtime': runtime, 'prefix': prefix,
            'request': search_request, 'preview': preview, 'prepared': published, 'directory': directory,
            'markers': configuration_source['markers'], 'service': service, 'tmp_path': tmp_path,
            'baseline_record': baseline_path.read_bytes(), 'screen_plan': configuration_source['screen_plan']}


def _execute_search(item, *, limit=None, lose_reply=False, wait_completion=False):
    from ergora import training_cycles

    state, definition, runtime = item['state'], item['definition'], item['runtime']
    request = {'schema_version': 1, 'budget': item['request']['budget'],
               'candidates': [{'experiment_id': result['experiment_id'], 'manifest_sha256': result['manifest_sha256'],
                               'change': 'External JSON batch/chunk grouping',
                               'next_bottleneck': 'CPU fixture only; no GPU or model-quality claim'}
                              for result in item['prepared']['experiments']]}
    cycle_id = item.get('cycle_id', 'search')
    source = item['tmp_path'] / (cycle_id + '-cycle-input')
    selected = training_cycles.create(state, 'demo', request, source)
    authorized = training_cycles.authorize(state, 'demo', cycle_id, source, selected['sha256'],
                                          state.project('demo')['revision'], confirm=True)
    item['authorization'] = authorized
    authorization_path = state.root / ('training-cycles/demo/' + cycle_id + '/authorization.json')
    original_clock = authorization_path.read_bytes()
    results = []
    for result in item['prepared']['experiments'][:limit]:
        ident = result['experiment_id']
        record = item['tmp_path'] / (ident + '-service.json')
        item['service'][0]('accepted', budget_scenario='configuration-full', record_path=record)
        try:
            submitted = training_cycles.start(state, 'demo', cycle_id, ident,
                authorized['authorization_sha256'], state.project('demo')['revision'])
            created = native_budget_create(definition, ident, managed=True)
            assert created.returncode == 0, created.stderr
            job = runtime / 'training/jobs' / ident
            native_sha = _sha((job / 'request.json').read_bytes())
            def execute():
                return training.execute(state, 'demo', ident, state.project('demo')['revision'],
                    submitted['intent_sha256'], submitted['run_id'], native_sha, confirm=True)
            if lose_reply and results:
                invoke = reference.training_execution
                def lose_actual_reply(project, home, operation, payload, **kwargs):
                    value = invoke(project, home, operation, payload, **kwargs)
                    if operation == 'request':
                        raise ValueError('Lost actual prepared-JSON execution request reply')
                    return value
                with pytest.MonkeyPatch.context() as patch:
                    patch.setattr(reference, 'training_execution', lose_actual_reply)
                    with pytest.raises(ValueError, match='Lost actual prepared-JSON'):
                        execute()
            else:
                execute()
            import time
            until = time.monotonic() + 30
            while not (job / 'managed-execution/stopped.json').exists() and time.monotonic() < until:
                time.sleep(.03)
            assert (job / 'managed-execution/stopped.json').is_file(), 'The original supervisor must reap its executor'
            observed = training.execution(state, 'demo', ident)
            final = None
            if wait_completion:
                final_path = runtime / f'ergora/training-submissions/{ident}.budget/final.json'
                until = time.monotonic() + 20
                while not final_path.exists() and time.monotonic() < until:
                    time.sleep(.03)
                assert final_path.is_file(), 'Original budget monitor must collect the typed terminal result'
                final = json.loads(final_path.read_bytes())
            results.append({'experiment_id': ident, 'job': job, 'execution': observed,
                            'submission': submitted, 'native_sha256': native_sha, 'service': record,
                            'budget_final': final})
        finally:
            stop_controller_test_owner(runtime, ident=ident)
        assert authorization_path.read_bytes() == original_clock
    item['executions'] = results
    return results


def _prepare_cpu_screens(item, cases):
    """Use one real B archive, then prepare each fixed screen through the public owner."""
    source = _execute_search(item, limit=1)[0]
    source_gate = json.loads((source['job'] / 'gate-report.json').read_bytes())
    assert source_gate['passed'] is True, source_gate
    saved = training.baseline_reference(item['state'], 'demo', source['experiment_id'],
                                        evidence_sha256=source_gate['evidence_sha256'])
    selector = {'experiment_id': source['experiment_id'], 'evidence_sha256': source_gate['evidence_sha256'],
                'reference_sha256': saved['reference_sha256']}
    source_manifest = json.loads((item['runtime'] / f"training/manifests/{source['experiment_id']}.json").read_bytes())
    for field in ('local_project', 'runner_template_id', 'baseline_sha', 'candidate_sha', 'max_run_seconds',
                  'configuration_inputs'):
        source_manifest.pop(field, None)
    prepared = []
    for index, case in enumerate(cases):
        ident = 'cpu-screen-' + str(index)
        candidate = {'global_batch': 24, 'microbatch': 6, 'strategy': 'closed-form', **case}
        candidate_raw = (json.dumps(candidate, sort_keys=True, indent=2) + '\n').encode()
        plan = deepcopy(item['screen_plan'])
        plan['verification_experiment_id'] = ident + '-verification'
        plan['resources'][0]['required'] = case.get('fault') == 'screen-required-resource'
        draft = {**source_manifest, 'experiment_id': ident, 'candidate_config_sha256': _sha(candidate_raw),
                 'baseline_reference': selector, 'execution': {'operation': 'training-screen-v1', 'plan': plan}}
        materials = {'format': 'json-v1',
            'baseline': {'utf8': item['request']['baseline_configuration']['utf8'],
                         'sha256': item['request']['baseline_configuration']['sha256']},
            'candidate': {'utf8': candidate_raw.decode(), 'sha256': _sha(candidate_raw)}}
        preview = training.preview_experiment(item['state'], 'demo', draft, 'trusted',
            max_run_seconds=120, configuration_materials=materials)
        result = training.prepare_experiment(item['state'], 'demo', draft, 'trusted',
            preview['project_revision'], preview['preview_sha256'], max_run_seconds=120,
            configuration_materials=materials)
        assert result['status'] == 'prepared'
        manifest_raw = (item['runtime'] / f'training/manifests/{ident}.json').read_bytes()
        spec = json.loads((item['runtime'] / f'training/specs/{ident}.json').read_bytes())
        assert spec['binding']['manifest_sha'] == _sha(manifest_raw)
        assert result['experiment_id'] == spec['binding']['experiment_id'] == ident
        prepared.append({**result, 'manifest_sha256': _sha(manifest_raw)})
    selected = {**item, 'prepared': {'experiments': prepared}, 'cycle_id': 'screen',
                'request': {**item['request'], 'budget': {'wall_seconds': 240, 'cleanup_seconds': 20,
                                                       'control_timeout_seconds': 10}},
                'reference_source': source, 'reference_saved': saved, 'reference_selector': selector}
    return selected


def _assert_screen_is_not_full(item, result):
    installation = Path(item['definition']['execution']['installation'])
    environment = {**os.environ, 'AGENTFLOW_CONFIG_DIR': item['definition']['execution']['config_directory'],
        'AGENTFLOW_STATE_DIR': item['definition']['execution']['state_directory'],
        'PYTHONPATH': os.pathsep.join(map(str, (Path(reference.__file__).parent.parent,
            installation / 'local', installation / 'upstream/platform', installation / 'upstream/temporal', installation / 'upstream')))}
    program = '''import asyncio,hashlib,json,sys
from copy import deepcopy
from pathlib import Path
from agent_platform import training
from agent_platform.core import Blocked
from perf_temporal.adapter import ContractViolation
from perf_temporal.client import load_experiment
from perf_temporal.models import GateDecision,ReleaseContext,ReleaseRequest
experiment=load_experiment(str(training.TRAINING/'specs'/ (sys.argv[1]+'.json')))
path=training.TRAINING/'jobs'/sys.argv[1]/'result.json'
original=path.read_bytes()
async def run():
    adapter=training.create_adapter()
    errors=[]
    try:
        job=await adapter.lookup_job(experiment)
        for forged in (False,True):
            if forged:
                value=json.loads(original)
                value['state']='SUCCEEDED'
                path.write_text(json.dumps(value))
            context=ReleaseContext(experiment,GateDecision(job,True,'f'*64,path.as_uri(),'forged gate'),
                ReleaseRequest(experiment.binding,'f'*64,'forged-owner'))
            for name,action in (('collect',lambda:adapter.collect_and_gate(job)),
                                ('release',lambda:adapter.authorize_release_and_create_task(context))):
                try:
                    await action()
                except (ContractViolation,Blocked) as error:
                    assert 'full-verify' in str(error)
                    errors.append({'operation':name,'forged_state':forged,'error':str(error)})
                else:
                    raise AssertionError('screen reached a full consumer')
        path.write_bytes(original)
        if json.loads(original)['state']=='SCREEN_COMPLETED':
            from ergora.reference_training_evidence import _screen_data
            output=path.parent/'run-output'
            report=json.loads((output/'screen-result.json').read_bytes())
            original_data=json.loads((output/'screen-source-report.json').read_bytes())
            manifest=training.read(training.TRAINING/'manifests'/ (sys.argv[1]+'.json'))
            request_raw=(path.parent/'configuration-request.json').read_bytes()
            request=json.loads(request_raw)
            request['_raw_sha256']=hashlib.sha256(request_raw).hexdigest()
            def read(ref,metadata=True):
                raw=(output/ref['path']).read_bytes()
                return json.loads(raw) if metadata else raw
            # Only policy derivation is varied; no altered bound bundle is published.
            changed=deepcopy(manifest)
            changed['execution']['plan']['screening']['minimum_improvement_fraction']=report['change_fraction']+1
            derived=_screen_data(original_data,request,changed,read,None)
            assert (derived['performance_state'],derived['decision'])==('no_gain','stop_direction')
            changed['execution']['plan']['screening'].update(minimum_improvement_fraction=0,
                noise_fraction=report['change_fraction']*2)
            derived=_screen_data(original_data,request,changed,read,None)
            assert (derived['performance_state'],derived['decision'])==('below_noise','stop_direction')
            def missing_quality(ref,metadata=True):
                value=read(ref,metadata)
                if ref['path']=='baseline-reference-read.json':
                    value['quality']['state']='unavailable'
                return value
            derived=_screen_data(original_data,request,manifest,missing_quality,None)
            assert (derived['performance_state'],derived['decision'])==('unavailable','inconclusive')
            assert derived['achieved_quality_tier']=='screened'
        return errors
    finally:
        path.write_bytes(original)
        await adapter.close()
print(json.dumps(asyncio.run(run())))
'''
    process = subprocess.run([sys.executable, '-P', '-c', program, result['experiment_id']],
        env=environment, capture_output=True, text=True, timeout=10)
    assert process.returncode == 0, process.stderr
    assert len(json.loads(process.stdout)) == 4
    assert not (item['runtime'] / 'training/approvals').exists()
    assert not (item['runtime'] / 'training/integration-tickets').exists()


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{'baseline_reference_support': True, 'screen_support': True}], indirect=True)
def test_typed_screen_runs_only_two_candidate_windows_against_the_original_cpu_reference(search_execution):
    item = _prepare_cpu_screens(search_execution, [{'global_batch': 24}, {'global_batch': 48}])
    from ergora import training_cycles

    selection = {'schema_version': 1, 'budget': item['request']['budget'], 'candidates': [
        {'experiment_id': prepared['experiment_id'], 'manifest_sha256': prepared['manifest_sha256'],
         'change': 'CPU screen only', 'next_bottleneck': 'No full verification or release authorized'}
        for prepared in item['prepared']['experiments']]}
    controller_input = item['tmp_path'] / 'blocked-controller-input'
    packet = training_cycles.create(item['state'], 'demo', selection, controller_input)
    with pytest.raises(ValueError, match='Controller execution unavailable for screen'):
        training_cycles.authorize_controller(item['state'], 'demo', 'blocked-controller', controller_input,
            packet['sha256'], item['state'].project('demo')['revision'], confirm=True, execute_selected=True)
    assert not (item['state'].root / 'training-cycles/demo/blocked-controller').exists()
    assert not (item['markers'] / 'screen.jsonl').exists()
    source_output = item['reference_source']['job'] / 'run-output'
    historical = (source_output / 'comparison-input.json').read_bytes()
    results = _execute_search(item, wait_completion=True, lose_reply=True)
    groups = []
    for result in results:
        output, observed = result['job'] / 'run-output', result['execution']
        native = json.loads((result['job'] / 'result.json').read_bytes())
        report_raw = (output / 'screen-result.json').read_bytes()
        report = json.loads(report_raw)
        assert native['state'] == 'SCREEN_COMPLETED' and native['gate'] is None
        assert native['screen']['report_sha256'] == _sha(report_raw)
        assert report['requested_tier'] == report['achieved_quality_tier'] == 'screened'
        assert report['decision'] == 'promising' and report['performance_state'] == 'promising'
        assert report['first_failure_ref'] is None and report['checks_not_run'] == []
        assert [check['status'] for check in report['checks']] == ['PASS', 'PASS']
        assert report['reference']['reference_sha256'] == item['reference_saved']['reference_sha256']
        assert report['reference']['quality']['state'] == 'reusable'
        assert report['reference']['timing']['state'] == 'historical_only'
        assert all(observed[key] is True for key in ('executor_stop_confirmed', 'durable_stop_confirmed'))
        assert all(observed['records'][name] is not None for name in ('request', 'launch', 'attempt', 'ack', 'stopped'))
        assert report['managed'] == {name + '_sha256': observed['record_sha256'][name]
                                     for name in ('request', 'launch', 'attempt', 'ack')}
        request_raw = (result['job'] / 'configuration-request.json').read_bytes()
        request = json.loads(request_raw)
        assert report['configuration_request_sha256'] == _sha(request_raw)
        assert report['execution_plan_sha256'] == _canonical_sha(request['execution']['plan'])
        assert len(report['windows']) == 1
        window = report['windows'][0]
        raw_window = json.loads((output / window['raw_ref']['path']).read_bytes())
        actual = json.loads((output / window['input_ref']['path']).read_bytes())
        assert json.loads((output / 'screen/actual-output.txt').read_text()) == json.loads(
            (output / 'screen/expected.json').read_bytes())['values']
        assert window['effective_work'] == actual['effective_work'] == len(actual['values']) == 48
        assert window['updates'] == 'not-applicable' and window['elapsed_seconds'] > 0
        assert report['throughput'] == window['effective_work'] / window['elapsed_seconds']
        read = json.loads((output / 'baseline-reference-read.json').read_bytes())
        assert read['candidate_quality'] == 'not_evaluated'
        assert read['baseline_work_skipped'] is read['independent_pair_supplied'] is read['promotion_approved'] is False
        relations = {entry['field']: entry for entry in read['projection']['relations']}
        historical_windows = item['reference_saved']['reference']['receipt']['baseline']['inputs']['windows']
        assert len(historical_windows) == item['request']['measurement']['statistics']['min_pairs']
        assert relations['input_windows'] == {'field': 'input_windows', 'relation': 'different',
            'reference': _canonical_sha(historical_windows), 'current': _canonical_sha(historical_windows[:1]),
            'unit': 'identity'}
        assert 'input_windows' in read['projection']['allowed_deltas']
        assert _sha(json.dumps(actual['values']).encode()) == historical_windows[0]['fingerprint']
        assert report['workload']['scope']['baseline_work_executed'] is False
        assert report['resources'] == [{**item['screen_plan']['resources'][0],
            'state': 'NOT_RUN', 'observed': None, 'report_ref': None}]
        assert window['provenance']['native_request_sha256'] == result['native_sha256']
        assert window['provenance']['launch_sha256'] == observed['record_sha256']['launch']
        assert window['provenance']['execution_phase_id'] == request['execution_phase_id']
        candidate = json.loads(Path(request['configurations']['candidate']['path']).read_bytes())
        expected_groups = 48 // candidate['global_batch']
        assert len(raw_window['grouping']) == expected_groups
        assert raw_window['grouping'] == [[candidate['microbatch']] *
            (candidate['global_batch'] // candidate['microbatch'])] * expected_groups
        groups.append(expected_groups)
        for entry in report['artifacts']:
            raw = (output / entry['path']).read_bytes()
            assert entry == {'path': entry['path'], 'sha256': _sha(raw), 'bytes': len(raw)}
        assert not (output / 'evidence.json').exists() and not (result['job'] / 'gate-report.json').exists()
        assert not list((output / 'raw').glob('*-baseline.json'))
        assert json.loads(result['service'].read_bytes())['starts'] == 1
        assert result['budget_final']['status'] == 'completed'
        assert result['budget_final']['gate'] is None
        assert result['budget_final']['screen']['state'] == native['state']
        evidence = training.evidence(item['state'], 'demo', result['experiment_id'])
        assert evidence['archive_status'] == 'no_accepted_archive' and evidence['recorded_gate_report'] is None
        assert evidence['screen_status'] == 'complete'
        assert evidence['screen']['result_sha256'] == _sha(report_raw)
        assert evidence['screen']['report'] == report
        assert all(evidence['screen']['cleanup'][name] is True for name in
                   ('durable_stop_confirmed', 'executor_stop_confirmed', 'reap_record_observed'))
        text = (output / 'screen/actual-output.txt').read_text()
        selected = training.evidence(item['state'], 'demo', result['experiment_id'],
            artifact='screen/actual-output.txt', screen_result_sha256=_sha(report_raw), offset=2, limit=10)
        assert selected['artifact']['text'] == text[2:12]
        with pytest.raises(ValueError, match='exact screen result SHA'):
            training.evidence(item['state'], 'demo', result['experiment_id'],
                artifact='screen/actual-output.txt', screen_result_sha256='0' * 64)
        _assert_screen_is_not_full(item, result)
        for name in ('supervisor', 'executor'):
            assert_budget_process_stopped(observed['records']['attempt'][name])
    assert groups == [2, 1]
    installation = Path(item['definition']['execution']['installation'])
    unavailable = installation.with_name(installation.name + '-unavailable')
    installation.rename(unavailable)
    try:
        saved = training.evidence(item['state'], 'demo', results[0]['experiment_id'])
        assert saved['screen_status'] == 'complete'
        assert training.inspect(item['state'], 'demo', results[0]['experiment_id'])['experiment'][
            'recorded_result_state'] == 'SCREEN_COMPLETED'
    finally:
        unavailable.rename(installation)
    assert (source_output / 'comparison-input.json').read_bytes() == historical
    markers = {name: [json.loads(line) for line in (item['markers'] / (name + '.jsonl')).read_text().splitlines()]
               for name in ('prepare', 'first-work', 'reference-read', 'reference-record', 'screen')}
    assert len(markers['prepare']) == 3 and len(markers['first-work']) == len(markers['reference-record']) == 1
    assert [entry['identity'] for entry in markers['prepare'][1:]] == [entry['identity'] for entry in markers['screen']]
    assert [entry['identity'] for entry in markers['reference-read']] == [entry['identity'] for entry in markers['screen']]
    assert all(entry['observations'] == 2 for entry in markers['screen'])
    for entry in [*markers['prepare'], *markers['first-work'], *markers['screen']]:
        assert_budget_process_stopped(entry['process_identity'])
    assert (item['prefix'] / 'baseline.json').read_bytes() == item['baseline_record']


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{'baseline_reference_support': True, 'screen_support': True}], indirect=True)
def test_actual_screen_failures_preserve_first_failure_and_never_become_full_success(search_execution):
    faults = ['screen-nan', 'screen-missing-input', 'screen-wrong-groups',
              'screen-first-failure-then-exception', 'screen-invalid-raw', 'screen-required-resource',
              'reference-read-last-sync-fence', 'reference-read-last-sync-deadline']
    item = _prepare_cpu_screens(search_execution, [{'fault': fault} for fault in faults])
    prepared = item['prepared']['experiments']
    required_index = faults.index('screen-required-resource')
    regular = {**item, 'cycle_id': 'screen-negative', 'prepared': {'experiments': [
        result for index, result in enumerate(prepared) if index != required_index]}}
    required = {**item, 'cycle_id': 'screen-required-resource',
                'prepared': {'experiments': [prepared[required_index]]}}
    # Each manual selection retains one contract and one original clock.
    executed = [*_execute_search(regular, wait_completion=True), *_execute_search(required, wait_completion=True)]
    by_id = {result['experiment_id']: result for result in executed}
    results = [by_id[result['experiment_id']] for result in prepared]
    for fault, result in zip(faults, results):
        output = result['job'] / 'run-output'
        native = json.loads((result['job'] / 'result.json').read_bytes())
        expected_state = ('SCREEN_REJECTED' if fault in faults[:3] else
                          'CANCELLED' if fault == 'reference-read-last-sync-fence' else 'FAILED')
        assert native['state'] == expected_state and native['gate'] is None
        assert result['budget_final']['native']['state'] == expected_state
        assert not (output / 'evidence.json').exists() and not (result['job'] / 'gate-report.json').exists()
        if expected_state == 'SCREEN_REJECTED':
            report = json.loads((output / 'screen-result.json').read_bytes())
            assert report['achieved_quality_tier'] == 'none' and report['decision'] == 'rejected'
            assert any(check['status'] == 'FAIL' for check in report['checks'])
            assert len(report['windows']) == 1
            if fault == 'screen-missing-input':
                assert report['windows'][0]['effective_work'] == 47
            assert report['first_failure_ref']['sha256'] == _sha((output / 'screen-first-failure.json').read_bytes())
            _assert_screen_is_not_full(item, result)
        else:
            assert native.get('screen') is None
        if fault.startswith('reference-read-last-sync-'):
            assert not (output / 'screen').exists(), 'Last reference sync must be followed by fresh live admission'
        if fault in faults[:4]:
            failure_raw = (output / 'screen-first-failure.json').read_bytes()
            failure = json.loads(failure_raw)
            assert failure['failure']['check_id'] == (
                'finite-output' if fault in ('screen-nan', 'screen-first-failure-then-exception') else 'independent-output')
            if fault in ('screen-nan', 'screen-first-failure-then-exception'):
                assert 'nan' in (output / 'screen/actual-output.txt').read_text()
            assert b'NaN' not in failure_raw
        assert result['execution']['executor_stop_confirmed'] is True
        for name in ('supervisor', 'executor'):
            assert_budget_process_stopped(result['execution']['records']['attempt'][name])
    failures = [json.loads(line) for line in
                (item['markers'] / 'screen-first-failure-returned.jsonl').read_text().splitlines()]
    assert len(failures) == 4
    for first, result in zip(failures, results):
        failure = result['job'] / 'run-output/screen-first-failure.json'
        assert first['sha256'] == _sha(failure.read_bytes()) and first['inode'] == failure.stat().st_ino
    screens = [json.loads(line) for line in (item['markers'] / 'screen.jsonl').read_text().splitlines()]
    assert len(screens) == 6
    for entry in screens:
        assert_budget_process_stopped(entry['process_identity'])


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
def test_search_materials_run_two_real_cpu_candidates_on_one_original_clock_and_archive(search_execution):
    item = search_execution
    results = _execute_search(item, lose_reply=True)
    assert len(results) == 2
    actual_grouping = []
    for choice, result in zip(item['preview']['plan']['choices'], results):
        job, ident, observed = result['job'], result['experiment_id'], result['execution']
        assert observed['executor_stop_confirmed'] is True
        assert all(observed['records'][name] is not None for name in ('request', 'launch', 'attempt', 'ack', 'stopped'))
        assert json.loads((job / 'result.json').read_bytes())['state'] == 'SUCCEEDED'
        gate = json.loads((job / 'gate-report.json').read_bytes())
        assert gate['passed'] is True, gate
        manifest = json.loads((item['runtime'] / f'training/manifests/{ident}.json').read_bytes())
        receipt_raw = (job / 'run-output/configuration-receipt.json').read_bytes()
        receipt = json.loads(receipt_raw)
        assert receipt['configuration_inputs'] == manifest['configuration_inputs']
        assert receipt['native_request_sha256'] == result['native_sha256']
        assert receipt['binding'] == json.loads((job / 'request.json').read_bytes())['experiment']['binding']
        for name in ('request', 'launch', 'attempt', 'ack'):
            assert receipt['managed'][name + '_sha256'] == observed['record_sha256'][name]
        archived = training.evidence(item['state'], 'demo', ident)['archive']
        assert archived['evidence_sha256'] == gate['evidence_sha256']
        archive = Path(archived['path'])
        configuration_request = json.loads((job / 'configuration-request.json').read_bytes())
        assert receipt['configurations'] == configuration_request['configurations']
        artifacts = {entry['path']: entry['sha256']
                     for entry in json.loads((job / 'run-output/evidence.json').read_bytes())['artifacts']}
        assert artifacts['configuration-receipt.json'] == _sha(receipt_raw)
        assert (archive / 'configuration-receipt.json').read_bytes() == receipt_raw
        for arm, packet_path in (('baseline', 'baseline-config.json'), ('candidate', choice['configuration']['path'])):
            raw = (item['directory'] / packet_path).read_bytes()
            descriptor = manifest['configuration_inputs'][arm]
            assert descriptor == {'path': f'training/configurations/{ident}/{arm}.json',
                                  'sha256': _sha(raw), 'bytes': len(raw)}
            assert (item['runtime'] / descriptor['path']).read_bytes() == raw
            assert (job / f'run-output/configuration-inputs/{arm}.json').read_bytes() == raw
            assert (archive / f'configuration-inputs/{arm}.json').read_bytes() == raw
            assert receipt['configurations'][arm] == {
                'repo': str(job / arm), 'commit': manifest[arm + '_commit'],
                'path': str(job / f'run-output/configuration-inputs/{arm}.json'), 'source_sha256': _sha(raw)}
            assert artifacts[f'configuration-inputs/{arm}.json'] == _sha(raw)
            observation = receipt['observations'][arm]
            assert observation['source_sha256'] == _sha(raw)
            assert observation['snapshot_sha256'] == _canonical_sha(observation['snapshot'])
            assert observation['semantic_identity']['sha256'] == _sha(
                json.dumps(observation['snapshot'], sort_keys=True).encode())
        candidate = json.loads((item['directory'] / choice['configuration']['path']).read_bytes())
        raw_result = json.loads((job / 'run-output/raw/0-candidate.json').read_bytes())
        groups = raw_result['grouping']
        assert groups == [[candidate['microbatch']] * (candidate['global_batch'] // candidate['microbatch'])] * (
            raw_result['source_samples'] // candidate['global_batch'])
        actual_grouping.append(groups)
        baseline_result = json.loads((job / 'run-output/raw/0-baseline.json').read_bytes())
        assert raw_result['values'] == baseline_result['values']
        assert baseline_result['grouping'] != groups
        assert json.loads(result['service'].read_bytes())['starts'] == 1
        before = _files(job / 'managed-execution')
        with pytest.raises(ValueError):
            training.execute(item['state'], 'demo', ident, item['state'].project('demo')['revision'],
                result['submission']['intent_sha256'], result['submission']['run_id'], result['native_sha256'], confirm=True)
        assert _files(job / 'managed-execution') == before
        for name in ('supervisor', 'executor'):
            assert_budget_process_stopped(observed['records']['attempt'][name])
    assert actual_grouping[0] != actual_grouping[1]
    prepared_contexts = [json.loads(line) for line in (item['markers'] / 'prepare.jsonl').read_text().splitlines()]
    first_work = [json.loads(line) for line in (item['markers'] / 'first-work.jsonl').read_text().splitlines()]
    assert len(prepared_contexts) == len(first_work) == 2
    assert [entry['identity'] for entry in prepared_contexts] == [entry['identity'] for entry in first_work]
    assert all(entry['observations'] == 2 for entry in first_work)
    assert (item['prefix'] / 'baseline.json').read_bytes() == item['baseline_record']


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{'baseline_reference_support': True}], indirect=True)
def test_baseline_reference_is_consumed_by_two_complete_independent_cpu_runs(search_execution):
    item = search_execution
    source = _execute_search(item, limit=1)[0]
    source_gate = json.loads((source['job'] / 'gate-report.json').read_bytes())
    assert source_gate['passed'] is True, source_gate
    saved = training.baseline_reference(item['state'], 'demo', source['experiment_id'],
                                        evidence_sha256=source_gate['evidence_sha256'])
    reference_document = saved['reference']
    assert reference_document['coverage']['inventory'] == 'complete'
    assert reference_document['coverage']['execution_source']['state'] == 'verified'
    assert reference_document['coverage']['cleanup']['state'] == 'verified'
    assert reference_document['coverage']['quality']['baseline_scope_verified'] is True
    assert reference_document['coverage']['quality']['state'] == 'unavailable'
    assert reference_document['coverage']['resources']['state'] == 'unavailable'
    assert reference_document['receipt']['oracle']['coverage']['model_training_quality'] == 'not_evaluated'
    from pathlib import PureWindowsPath

    pending = [reference_document]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, str):
            assert not Path(value).is_absolute() and not PureWindowsPath(value).is_absolute(), value
    source_archive = Path(source_gate['archive_report']['archive_path'])
    original_receipt_raw = (source_archive / 'baseline-reference-receipt.json').read_bytes()
    original_receipt = json.loads(original_receipt_raw)
    assert Path(original_receipt['source']['repo']).is_absolute()
    assert Path(original_receipt['environment']['observed']['executable']).is_absolute()
    assert reference_document['receipt']['source'] == {
        key: value for key, value in original_receipt['source'].items() if key != 'repo'}
    assert reference_document['receipt']['environment']['observed'] == {
        key: value for key, value in original_receipt['environment']['observed'].items() if key != 'executable'}
    environment_ref = original_receipt['environment']['report_ref']
    assert reference_document['receipt']['environment']['report_ref'] == environment_ref
    archive_inventory = {entry['path']: entry for entry in reference_document['inventory']['entries']
                         if entry['root'] == 'archive'}
    for name in ('baseline-reference-receipt.json', environment_ref['path'], 'baseline-reference-source-inventory.raw'):
        raw = (source_archive / name).read_bytes()
        assert archive_inventory[name]['sha256'] == _sha(raw)
        assert archive_inventory[name]['bytes'] == len(raw)
        assert (source['job'] / 'run-output' / name).read_bytes() == raw
    environment_raw = (source_archive / environment_ref['path']).read_bytes()
    assert environment_ref == {'path': environment_ref['path'], 'sha256': _sha(environment_raw), 'bytes': len(environment_raw)}
    assert json.loads(environment_raw) == {'environment': original_receipt['environment']['observed']}
    assert archive_inventory['baseline-reference-source-inventory.raw']['sha256'] == original_receipt['source']['inventory_sha256']
    # A historical map is checked against its archived declaration, independently of current live requirements.
    extension_marker = item['tmp_path'] / 'historical-current-coverage-extension.json'
    extension = f'''import json
from pathlib import Path
from ergora import training_execution_protocol as protocol
name='training_search.py'
assert name not in protocol.GATE_SOURCES and Path(protocol.__file__).with_name(name).is_file()
before=list(protocol.GATE_SOURCES)
protocol.GATE_SOURCES=(*protocol.GATE_SOURCES,name)
Path({str(extension_marker)!r}).write_text(json.dumps({{'before':before,'after':list(protocol.GATE_SOURCES)}}))
'''
    original_reader = reference.subprocess.Popen
    extended_readers = []
    def extend_current_coverage(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.reference_training_evidence import main;main()':
            extended_readers.append(argv)
            argv = [*argv[:-1], extension + argv[-1]]
        return original_reader(argv, *args, **kwargs)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(reference.subprocess, 'Popen', extend_current_coverage)
        assert training.baseline_reference(item['state'], 'demo', source['experiment_id'],
                                           evidence_sha256=source_gate['evidence_sha256']) == saved
    assert len(extended_readers) == 1, 'The coverage extension must reach the actual training reader child'
    assert extension_marker.is_file(), 'The training reader child must record its actual coverage extension'
    extended = json.loads(extension_marker.read_bytes())
    assert extended['after'] == [*extended['before'], 'training_search.py']
    source_output = source['job'] / 'run-output'
    source_comparison = json.loads((source_output / 'comparison-input.json').read_bytes())
    seen_runs = {pair[arm]['run_id'] for pair in source_comparison['pairs'] for arm in ('baseline', 'candidate')}
    selector = {'experiment_id': source['experiment_id'], 'evidence_sha256': source_gate['evidence_sha256'],
                'reference_sha256': saved['reference_sha256']}
    candidate_request = deepcopy(item['request'])
    candidate_request['search_id'] = 'reference-candidates'
    candidate_request['experiment_template']['baseline_reference'] = selector
    preview = training_search.preview(item['state'], 'demo', candidate_request)
    directory = item['tmp_path'] / 'reference-candidate-inputs'
    published = _prepare(item['state'], candidate_request, preview, directory)
    selected = {**item, 'request': candidate_request, 'preview': preview, 'prepared': published,
                'directory': directory, 'cycle_id': 'reuse'}
    results = _execute_search(selected, lose_reply=True)
    projections = []
    read_digests = []
    group_counts = []
    for result in results:
        job, observed = result['job'], result['execution']
        assert json.loads((job / 'result.json').read_bytes())['state'] == 'SUCCEEDED'
        gate = json.loads((job / 'gate-report.json').read_bytes())
        assert gate['passed'] is True, gate
        evidence = training.evidence(item['state'], 'demo', result['experiment_id'])
        archive = Path(evidence['archive']['path'])
        output = job / 'run-output'
        bundle = json.loads((output / 'evidence.json').read_bytes())
        assert bundle['quality']['status'] == 'NOT_RUN'
        indexed = {entry['path']: entry['sha256'] for entry in bundle['artifacts']}
        # Verify every original artifact, including oracle inputs/expected and core source evidence.
        for path, sha in indexed.items():
            raw = (output / path).read_bytes()
            assert _sha(raw) == sha and (archive / path).read_bytes() == raw
        read_raw = (output / 'baseline-reference-read.json').read_bytes()
        read = json.loads(read_raw)
        assert read['selector'] == selector
        assert read['reference_sha256'] == saved['reference_sha256']
        assert read['anchor_sha256'] == saved['anchor_sha256']
        assert read['inventory_sha256'] == reference_document['inventory']['sha256']
        assert read['quality']['state'] == 'reusable'
        assert read['timing']['state'] == 'historical_only'
        assert read['resources']['state'] == 'unavailable'
        assert read['candidate_quality'] == 'not_evaluated'
        assert read['baseline_work_skipped'] is read['independent_pair_supplied'] is read['promotion_approved'] is False
        relations = {entry['field']: entry for entry in read['projection']['relations']}
        assert relations['effective_samples']['current'] == 48
        assert relations['optimizer_updates']['relation'] == 'not_applicable'
        assert relations['optimizer_updates']['current'] is None
        projections.append(read['projection'])
        read_digests.append(_sha(read_raw))
        request = json.loads((job / 'configuration-request.json').read_bytes())
        assert request['baseline_reference'] == selector
        comparison = json.loads((output / 'comparison-input.json').read_bytes())
        assert {pair['order'] for pair in comparison['pairs']} == {'AB', 'BA'}
        first_candidate = json.loads((output / comparison['pairs'][0]['candidate']['raw_ref']['path']).read_bytes())
        configured = json.loads(Path(request['configurations']['candidate']['path']).read_bytes())
        expected_groups = (len(first_candidate['values']) + configured['global_batch'] - 1) // configured['global_batch']
        assert len(first_candidate['grouping']) == expected_groups == relations['batch_groups']['current']
        group_counts.append(expected_groups)
        for pair in comparison['pairs']:
            for arm in ('baseline', 'candidate'):
                record = pair[arm]
                assert record['run_id'] not in seen_runs
                seen_runs.add(record['run_id'])
                raw = json.loads((output / record['raw_ref']['path']).read_bytes())
                assert raw['provenance'] == {
                    'native_request_sha256': result['native_sha256'],
                    'launch_sha256': observed['record_sha256']['launch'],
                    'execution_phase_id': request['execution_phase_id'], 'run_id': record['run_id'],
                    'window_id': raw['provenance']['window_id']}
                assert raw['values'] == json.loads((output / f"expected/{pair['pair_id'].split('-')[-1]}.json").read_bytes())['values']
                assert record['elapsed_seconds'] == raw['elapsed_seconds']
        assert all(observed[name] is True for name in ('executor_stop_confirmed', 'durable_stop_confirmed'))
        assert json.loads(result['service'].read_bytes())['starts'] == 1
        before = _files(job / 'managed-execution')
        with pytest.raises(ValueError):
            training.execute(item['state'], 'demo', result['experiment_id'], item['state'].project('demo')['revision'],
                result['submission']['intent_sha256'], result['submission']['run_id'], result['native_sha256'], confirm=True)
        assert _files(job / 'managed-execution') == before
        for name in ('supervisor', 'executor'):
            assert_budget_process_stopped(observed['records']['attempt'][name])
    assert projections[0]['candidate_observation_sha256'] != projections[1]['candidate_observation_sha256']
    assert read_digests[0] != read_digests[1]
    assert len(set(group_counts)) == len(results)
    assert (item['prefix'] / 'baseline.json').read_bytes() == item['baseline_record']
    assert training.baseline_reference(item['state'], 'demo', source['experiment_id'],
                                       evidence_sha256=source_gate['evidence_sha256']) == saved
    markers = {name: [json.loads(line) for line in (item['markers'] / (name + '.jsonl')).read_text().splitlines()]
               for name in ('prepare', 'first-work', 'reference-read', 'reference-record')}
    assert [entry['identity'] for entry in markers['prepare']] == [entry['identity'] for entry in markers['first-work']]
    assert [entry['identity'] for entry in markers['reference-read']] == [entry['identity'] for entry in markers['first-work'][1:]]
    assert [entry['identity'] for entry in markers['reference-record']] == [entry['identity'] for entry in markers['first-work']]


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution,resource_state', [
    pytest.param({'baseline_reference_support': True, 'resource_limit_bytes': 1_073_741_824}, 'observed', id='within'),
    pytest.param({'baseline_reference_support': True, 'resource_limit_bytes': 1}, 'invalid', id='over'),
], indirect=['search_execution'])
def test_actual_process_resource_soft_limit_preserves_other_reference_dimensions(search_execution, resource_state):
    item = search_execution
    source = _execute_search(item, limit=1)[0]
    gate = json.loads((source['job'] / 'gate-report.json').read_bytes())
    assert gate['passed'] is True, gate
    assert json.loads((source['job'] / 'result.json').read_bytes())['state'] == 'SUCCEEDED'
    archive = Path(gate['archive_report']['archive_path'])
    receipt = json.loads((archive / 'baseline-reference-receipt.json').read_bytes())
    metric, = receipt['resources']
    assert set(metric) == {'metric', 'unit', 'aggregation', 'scope', 'observed', 'limit', 'report_ref'}
    assert (metric['metric'], metric['unit'], metric['aggregation'], metric['scope']) == (
        'peak_rss', 'bytes', 'peak', 'whole_runner_process')
    baseline = json.loads(item['request']['baseline_configuration']['utf8'].lstrip('\ufeff'))
    assert metric['limit'] == baseline['resource_limit_bytes']
    assert type(metric['observed']) is int and metric['observed'] > 0
    assert (metric['observed'] > metric['limit']) is (resource_state == 'invalid')
    resource_ref = metric['report_ref']
    resource_raw = (archive / resource_ref['path']).read_bytes()
    assert resource_ref == {'path': resource_ref['path'], 'sha256': _sha(resource_raw), 'bytes': len(resource_raw)}
    report = json.loads(resource_raw)
    assert report['metric'] == {key: value for key, value in metric.items() if key != 'report_ref'}
    observation = report['observation']
    assert observation['method'] == 'resource.getrusage(RUSAGE_SELF).ru_maxrss'
    assert observation['raw_unit'] == 'KiB' and observation['bytes_per_unit'] == 1024
    assert metric['observed'] == observation['raw_value'] * observation['bytes_per_unit']
    assert observation['pid'] == json.loads((item['markers'] / 'prepare.jsonl').read_text().splitlines()[0])['pid']
    configuration_request = json.loads((source['job'] / 'configuration-request.json').read_bytes())
    assert observation['native_request_sha256'] == source['native_sha256']
    assert observation['launch_sha256'] == source['execution']['record_sha256']['launch']
    assert observation['execution_phase_id'] == configuration_request['execution_phase_id']
    evidence = json.loads((archive / 'evidence.json').read_bytes())
    assert evidence['quality']['status'] == 'NOT_RUN'
    assert sum((archive / entry['path']).stat().st_size for entry in evidence['artifacts']) < 64 * 1_048_576
    for entry in evidence['artifacts']:
        raw = (archive / entry['path']).read_bytes()
        assert _sha(raw) == entry['sha256']
        assert (source['job'] / 'run-output' / entry['path']).read_bytes() == raw
    saved = training.baseline_reference(item['state'], 'demo', source['experiment_id'],
                                        evidence_sha256=gate['evidence_sha256'])
    reference_document = saved['reference']
    coverage = reference_document['coverage']
    assert coverage['inventory'] == 'complete'
    assert coverage['execution_source']['state'] == coverage['cleanup']['state'] == 'verified'
    assert coverage['quality']['baseline_scope_verified'] is True
    assert coverage['quality']['state'] == 'unavailable'
    assert coverage['timing']['state'] == 'historical_only'
    assert coverage['resources']['state'] == resource_state
    assert coverage['resources']['metrics'] == receipt['resources']
    if resource_state == 'invalid':
        assert coverage['resources']['reasons'] == [{
            'code': 'resource_limit_exceeded', 'field': 'resources.peak_rss.limit',
            'expected': metric['limit'], 'observed': metric['observed'], 'source_ref': resource_ref}]
    else:
        assert coverage['resources']['reasons'] == []
    request = deepcopy(item['request'])
    request['search_id'] = 'resource-consumer'
    request['experiment_template']['baseline_reference'] = {
        'experiment_id': source['experiment_id'], 'evidence_sha256': gate['evidence_sha256'],
        'reference_sha256': saved['reference_sha256']}
    request['dimensions'][0]['values'] = [24]
    request['selection']['max_trials'] = 1
    preview = training_search.preview(item['state'], 'demo', request)
    directory = item['tmp_path'] / 'resource-consumer-inputs'
    published = _prepare(item['state'], request, preview, directory)
    selected = {**item, 'request': request, 'preview': preview, 'prepared': published,
                'directory': directory, 'cycle_id': 'resource-read'}
    consumer, = _execute_search(selected)
    consumer_gate = json.loads((consumer['job'] / 'gate-report.json').read_bytes())
    assert consumer_gate['passed'] is True, consumer_gate
    assert json.loads((consumer['job'] / 'result.json').read_bytes())['state'] == 'SUCCEEDED'
    consumer_archive = Path(consumer_gate['archive_report']['archive_path'])
    read = json.loads((consumer_archive / 'baseline-reference-read.json').read_bytes())
    assert read['reference_sha256'] == saved['reference_sha256'] and read['anchor_sha256'] == saved['anchor_sha256']
    assert read['resources'] == coverage['resources']
    assert read['quality']['state'] == 'reusable' and read['timing']['state'] == 'historical_only'
    assert read['candidate_quality'] == 'not_evaluated'
    assert read['baseline_work_skipped'] is read['independent_pair_supplied'] is read['promotion_approved'] is False
    comparison = json.loads((consumer_archive / 'comparison-input.json').read_bytes())
    assert {pair['order'] for pair in comparison['pairs']} == {'AB', 'BA'}
    source_comparison = json.loads((archive / 'comparison-input.json').read_bytes())
    source_runs = {pair[arm]['run_id'] for pair in source_comparison['pairs'] for arm in ('baseline', 'candidate')}
    for pair in comparison['pairs']:
        for arm in ('baseline', 'candidate'):
            assert pair[arm]['run_id'] not in source_runs
            raw = json.loads((consumer_archive / pair[arm]['raw_ref']['path']).read_bytes())
            assert raw['provenance']['native_request_sha256'] == consumer['native_sha256']
            assert raw['provenance']['launch_sha256'] == consumer['execution']['record_sha256']['launch']
    for result in (source, consumer):
        assert result['execution']['executor_stop_confirmed'] is result['execution']['durable_stop_confirmed'] is True
        for name in ('supervisor', 'executor'):
            assert_budget_process_stopped(result['execution']['records']['attempt'][name])
    # A resource-limit outcome does not excuse corrupt resource-report bytes.
    resource_path = archive / resource_ref['path']
    try:
        resource_path.write_bytes(resource_raw + b'\n')
        with pytest.raises(ValueError, match='archive_changed'):
            training.baseline_reference(item['state'], 'demo', source['experiment_id'], evidence_sha256=gate['evidence_sha256'])
    finally:
        resource_path.write_bytes(resource_raw)
    assert training.baseline_reference(item['state'], 'demo', source['experiment_id'],
                                       evidence_sha256=gate['evidence_sha256']) == saved
    assert (item['prefix'] / 'baseline.json').read_bytes() == item['baseline_record']


def test_source_callbacks_do_not_declare_reference_support(search_input, configuration_source):
    state, _, runtime, _, request = search_input
    request['experiment_template']['baseline_reference'] = {
        'experiment_id': 'alpha', 'evidence_sha256': 'a' * 64, 'reference_sha256': 'b' * 64}
    with pytest.raises(ValueError, match='[Bb]aseline.reference|[Pp]rotocol'):
        training_search.preview(state, 'demo', request)
    assert not configuration_source['markers'].exists()
    assert not (runtime / 'training/search-preparations').exists()


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{'baseline_reference_support': True}], indirect=True)
def test_reference_receipt_raw_durability_and_cached_windows_fail_in_managed_consumer(search_execution):
    item = search_execution
    source = _execute_search(item, limit=1)[0]
    gate = json.loads((source['job'] / 'gate-report.json').read_bytes())
    assert gate['passed'] is True, gate
    saved = training.baseline_reference(item['state'], 'demo', source['experiment_id'],
                                        evidence_sha256=gate['evidence_sha256'])
    for ordinal, fault in enumerate(('reference-read-sync', 'reference-read-last-sync-fence',
                                     'reference-read-last-sync-deadline', 'reference-read-raw-drift',
                                     'reference-cached-window', 'reference-current-coverage-extension')):
        request = deepcopy(item['request'])
        request['search_id'] = 'reference-fault-' + str(ordinal)
        request['experiment_template']['baseline_reference'] = {
            'experiment_id': source['experiment_id'], 'evidence_sha256': gate['evidence_sha256'],
            'reference_sha256': saved['reference_sha256']}
        request['dimensions'][0]['values'] = [24]
        request['selection']['max_trials'] = 1
        preview = training_search.preview(item['state'], 'demo', request)
        directory = item['tmp_path'] / request['search_id']
        published = _prepare(item['state'], request, preview, directory)
        selected = {**item, 'request': request, 'preview': preview, 'prepared': published,
                    'directory': directory, 'cycle_id': 'fault-' + str(ordinal)}
        first_work = (item['markers'] / 'first-work.jsonl').read_bytes()
        with pytest.MonkeyPatch.context() as patch:
            patch.setenv('ERGORA_TEST_REFERENCE_FAULT', fault)
            result = _execute_search(selected)[0]
        job, observed = result['job'], result['execution']
        expected_state = 'CANCELLED' if fault == 'reference-read-last-sync-fence' else 'FAILED'
        assert json.loads((job / 'result.json').read_bytes())['state'] == expected_state
        assert not (job / 'gate-report.json').exists()
        assert (item['markers'] / (fault.replace('reference-cached-window', 'cached-window') + '.jsonl')).is_file()
        if fault in ('reference-read-sync', 'reference-read-last-sync-fence', 'reference-read-last-sync-deadline',
                     'reference-current-coverage-extension'):
            assert (item['markers'] / 'first-work.jsonl').read_bytes() == first_work
        elif fault == 'reference-read-raw-drift':
            mutation = json.loads((item['markers'] / (fault + '.jsonl')).read_text().splitlines()[-1])
            assert mutation['same_decoded_values'] is True
            assert mutation['before_sha256'] != mutation['after_sha256']
        if fault == 'reference-current-coverage-extension':
            injected = json.loads((item['markers'] / (fault + '.jsonl')).read_text().splitlines()[-1])
            assert injected['after'] == [*injected['before'], 'training_search.py']
            assert injected['managed'] == {name + '_sha256': observed['record_sha256'][name]
                                          for name in ('request', 'launch', 'attempt', 'ack')}
            assert 'Current execution source coverage is incomplete or unsupported' in (job / 'run-output/execution.log').read_text()
        assert observed['executor_stop_confirmed'] is observed['durable_stop_confirmed'] is True
        for name in ('supervisor', 'executor'):
            assert_budget_process_stopped(observed['records']['attempt'][name])
    assert training.baseline_reference(item['state'], 'demo', source['experiment_id'],
                                       evidence_sha256=gate['evidence_sha256']) == saved
    assert (item['prefix'] / 'baseline.json').read_bytes() == item['baseline_record']


@pytest.mark.parametrize('prepared_format', (None, 'missing'))
def test_search_requires_declared_json_execution_before_any_intent_or_import(
        search_input, configuration_source, tmp_path, prepared_format):
    state, definition, runtime, _, request = search_input
    path = Path(definition['execution']['config_directory']) / 'training-runners/trusted.json'
    runner = json.loads(path.read_bytes())
    if prepared_format == 'missing':
        runner['configuration_readback'].pop('prepared_json_format')
    else:
        runner['configuration_readback']['prepared_json_format'] = prepared_format
    path.write_text(json.dumps(runner) + '\n')
    before = _files(runtime, path.parent)
    with pytest.raises(ValueError):
        training_search.preview(state, 'demo', request)
    with pytest.raises(ValueError):
        training_search.prepare(state, 'demo', request, state.project('demo')['revision'], '0' * 64, tmp_path / 'unavailable')
    assert _files(runtime, path.parent) == before
    assert not configuration_source['markers'].exists()
    assert not (tmp_path / 'unavailable').exists()
    assert not (runtime / 'ergora/training-preparations').exists()
    assert not (state.root / 'training-cycles').exists()


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{'fault': 'last-material-fence'},
                                           {'fault': 'last-material-deadline'}], indirect=True)
def test_prepared_driver_checks_live_authority_after_the_last_actual_material_read(search_execution):
    item = search_execution
    result, = _execute_search(item, limit=1)
    observed, job = result['execution'], result['job']
    assert observed['executor_stop_confirmed'] is True
    assert (item['markers'] / 'last-material-returned.jsonl').is_file()
    assert (item['markers'] / 'last-guard-rejected.jsonl').is_file()
    assert len((item['markers'] / 'prepare.jsonl').read_text().splitlines()) == 1
    assert len((item['markers'] / 'describe.jsonl').read_text().splitlines()) == 2
    assert not (item['markers'] / 'first-work.jsonl').exists()
    assert not (job / 'run-output/evidence.json').exists()
    assert not (job / 'gate-report.json').exists()
    receipt = json.loads((job / 'run-output/configuration-receipt.json').read_bytes())
    assert receipt['managed'] == {name + '_sha256': observed['record_sha256'][name]
                                  for name in ('request', 'launch', 'attempt', 'ack')}
    assert json.loads(result['service'].read_bytes())['starts'] == 1
    for name in ('supervisor', 'executor'):
        assert_budget_process_stopped(observed['records']['attempt'][name])


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{'fault': 'configuration-drift'}], indirect=True)
def test_prepared_actual_input_drift_after_construction_never_reaches_first_work(search_execution):
    item = search_execution
    result, = _execute_search(item, limit=1)
    assert result['execution']['executor_stop_confirmed'] is True
    assert len((item['markers'] / 'prepare.jsonl').read_text().splitlines()) == 1
    assert not (item['markers'] / 'first-work.jsonl').exists()
    assert json.loads((result['job'] / 'result.json').read_bytes())['state'] == 'FAILED'
    assert not (result['job'] / 'gate-report.json').exists()
    assert not (result['job'] / 'run-output/evidence.json').exists()


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('mutation', ('raw-bytes', 'symlink'))
def test_native_material_drift_cannot_enter_the_original_cycle_source_inventory(search_execution, tmp_path, mutation):
    item = search_execution
    ident = item['prepared']['experiments'][0]['experiment_id']
    path = item['runtime'] / f'training/configurations/{ident}/candidate.json'
    original = path.read_bytes()
    if mutation == 'raw-bytes':
        path.write_bytes(original + b'\n')
    else:
        outside = tmp_path / 'same-external-data.json'
        outside.write_bytes(original)
        path.unlink()
        path.symlink_to(outside)
    with pytest.raises(ValueError):
        _execute_search(item)
    assert not item['markers'].exists()
    assert not (item['runtime'] / 'ergora/training-submissions').exists()
    assert not (item['state'].root / 'training-cycles/demo/search/authorization.json').exists()
    if mutation == 'symlink':
        assert outside.read_bytes() == original


def test_prepared_intent_directory_sync_precedes_all_five_native_outputs_and_resumes_same_id(
        search_input, configuration_source, stop_after, tmp_path):
    state, _, runtime, _, request = search_input
    preview = training_search.preview(state, 'demo', request)
    choice = preview['plan']['choices'][0]
    ident = choice['experiment_id']
    assert len(choice['native_plan']['files']) == 5
    trace = tmp_path / 'prepared-intent-sync.jsonl'
    directory = tmp_path / 'prepared-inputs'
    stop_after(sync_failure='parent', trace=trace, ident=ident)
    with pytest.raises(ValueError, match='intent synchronization failure'):
        _prepare(state, request, preview, directory)
    original = (runtime / f'ergora/training-preparations/{ident}.intent.json').read_bytes()
    assert training_search.read(directory)['plan'] == preview['plan']
    assert not any((runtime / name).exists() for name in choice['native_plan']['files'])
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    assert events and not any(event['event'] == 'native-output-call' for event in events)
    assert not configuration_source['markers'].exists()
    assert not (state.root / 'training-cycles').exists()
    stop_after()
    restored = _prepare(state, request, preview, directory)
    assert restored['status'] == 'prepared'
    assert restored['experiments'][0]['experiment_id'] == ident
    assert restored['experiments'][0]['intent_sha256'] == choice['native_preview_sha256']
    assert (runtime / f'ergora/training-preparations/{ident}.intent.json').read_bytes() == original
    for relative, raw in choice['native_plan']['files'].items():
        assert (runtime / relative).read_bytes() == raw.encode('utf-8')
    assert not configuration_source['markers'].exists()
    assert not (state.root / 'training-cycles').exists()


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{'fault': 'receipt-raw-drift'}], indirect=True)
def test_prepared_receipt_raw_drift_during_work_never_enters_archive(search_execution):
    item = search_execution
    result, = _execute_search(item, limit=1)
    job, observed, ident = result['job'], result['execution'], result['experiment_id']
    before = (item['markers'] / 'receipt-before.raw').read_bytes()
    after = (item['markers'] / 'receipt-after.raw').read_bytes()
    assert after == before + b'\n' and json.loads(before) == json.loads(after)
    receipt = json.loads(before)
    assert receipt['native_request_sha256'] == result['native_sha256']
    assert receipt['managed'] == {name + '_sha256': observed['record_sha256'][name]
                                 for name in ('request', 'launch', 'attempt', 'ack')}
    assert observed['executor_stop_confirmed'] is True
    assert all(observed['records'][name] is not None for name in ('request', 'launch', 'attempt', 'ack', 'stopped'))
    assert len((item['markers'] / 'first-work.jsonl').read_text().splitlines()) == 1
    assert json.loads((job / 'result.json').read_bytes())['state'] == 'FAILED'
    assert 'Configuration or baseline reference receipt changed during training work' in (job / 'run-output/execution.log').read_text()
    assert not (job / 'gate-report.json').exists()
    assert not (item['prefix'] / 'experiments' / ident / 'accepted-evidence').exists()
    artifacts = json.loads((job / 'run-output/evidence.json').read_bytes())['artifacts']
    assert not any(entry['path'] == 'configuration-receipt.json' for entry in artifacts)
    for name in ('supervisor', 'executor'):
        assert_budget_process_stopped(observed['records']['attempt'][name])


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{'fault': 'receipt-readback-inode'}], indirect=True)
def test_prepared_receipt_readback_confirms_the_actual_inode_before_work(search_execution):
    item = search_execution
    result, = _execute_search(item, limit=1)
    observed, job = result['execution'], result['job']
    drift, = [json.loads(line) for line in (item['markers'] / 'receipt-inode-drift.jsonl').read_text().splitlines()]
    assert drift['same_raw'] is True and drift['before_inode'] != drift['after_inode']
    assert observed['executor_stop_confirmed'] is True
    assert len((item['markers'] / 'prepare.jsonl').read_text().splitlines()) == 1
    assert len((item['markers'] / 'describe.jsonl').read_text().splitlines()) == 1
    assert not (item['markers'] / 'first-work.jsonl').exists()
    assert not (job / 'run-output/evidence.json').exists()
    assert not (job / 'gate-report.json').exists()
    assert json.loads((job / 'result.json').read_bytes())['state'] == 'FAILED'
    assert 'changed during durable readback' in (job / 'run-output/execution.log').read_text()
    for name in ('supervisor', 'executor'):
        assert_budget_process_stopped(observed['records']['attempt'][name])
