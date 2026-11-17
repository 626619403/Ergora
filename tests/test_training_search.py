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
from test_task_export import export as export_candidate, export_client, export_task
from test_task_submission import native_client
from test_training import experiments, registration
from test_training_runtime import installation


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
    template.update(baseline_id='baseline-one', baseline_commit='a' * 40, candidate_commit='a' * 40,
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
def search_input(request, search_request):
    if sys.platform != 'linux':
        pytest.skip('Native experiment preparation requires Linux/WSL2')
    pytest.importorskip('temporalio')
    state, definition, runtime, prefix, write = request.getfixturevalue('experiments')
    baseline = json.loads((prefix / 'baseline.json').read_bytes())
    baseline['config_sha256'] = search_request['baseline_configuration']['sha256']
    write(prefix / 'baseline.json', baseline)
    search_request['experiment_template'].update(baseline_commit=baseline['commit'], candidate_commit=baseline['commit'],
                                                workload_fingerprint=baseline['workload_fingerprint'])
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


def test_two_batch_configurations_prepare_real_native_bindings_and_read_offline(search_input, tmp_path, monkeypatch):
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
    observed = training_search.read(directory, sha256=result['sha256'])
    assert observed['plan'] == plan and observed['sha256'] == _sha((directory / 'search.json').read_bytes())
    assert observed['coverage']['configuration_execution'] == 'unavailable'
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
        export_task, export_client, search_request, tmp_path, monkeypatch):
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
        'schema_version': 1, 'runner_template_id': 'trusted', 'project': 'demo', 'repo': definition['repo'],
        'command': [sys.executable, '-c', 'pass'], 'timeout_seconds': 30})
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


@pytest.mark.parametrize('boundary', (1, 2))
def test_partial_native_publication_resumes_frozen_choices_without_reenumeration(
        search_input, tmp_path, monkeypatch, interrupt_publication, boundary):
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
    assert first['status'] == 'partially_prepared'
    assert sum(item['state'] == 'matching' for item in first['files']) == boundary
    frozen = _files(directory)
    published = {runtime / relative: (runtime / relative).read_bytes()
                 for relative in choices[0]['native_plan']['files'] if (runtime / relative).exists()}
    interrupt_publication()
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
                   'cardinality', 'coverage', 'config', 'extra-file', 'config-symlink'):
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
        elif mutate == 'config':
            (directory / choice['configuration']['path']).write_text('{"changed":true}\n')
        elif mutate == 'extra-file':
            (directory / 'unexpected.json').write_text('{}')
        else:
            (directory / choice['configuration']['path']).unlink()
            (directory / choice['configuration']['path']).symlink_to(outside)
        if mutate in ('policy', 'policy-number-kind', 'native-request-number-kind', 'native-plan', 'cardinality', 'coverage'):
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
