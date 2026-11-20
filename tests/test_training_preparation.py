"""A confirmed native preparation retains one intent across partial publication."""

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys

import pytest

from ergora._paths import IMPORT_ROOT, PACKAGE_ROOT
import ergora.native.resources as native_resources
import ergora.runtime.processes as processes
import ergora.configuration.projects as projects
import ergora.configuration.registrations as registrations
import ergora.training.application as training
from ergora.storage.state import State
from ergora.training.materials import validate_preparation_intent
from test_training import experiments, registration
from test_training_runtime import installation
from test_training_submission import prepared, service

pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Native experiment preparation requires Linux/WSL2')


@pytest.fixture
def preparation_input(experiments):
    state, definition, runtime, prefix, _ = experiments
    draft = json.loads((prefix / 'experiments/alpha/manifest.json').read_bytes())
    draft.update(experiment_id='gamma', notes='CPU publication contract only; no training or GPU acceptance')
    return state, definition, runtime, prefix, draft


@pytest.fixture
def stop_after(monkeypatch):
    original = processes.run
    fixture = Path(__file__).parent / 'fixtures/training_preparation_process.py'

    def select(index=None, *, sync_failure=None, trace=None, ident='gamma'):
        def invoke(argv, *args, **kwargs):
            if (index is not None or sync_failure) and argv[-1] == 'from ergora.training.runtime.preparation import main;main()':
                argv = [*argv[:-1], f'import runpy;runpy.run_path({str(fixture)!r},run_name="__main__")']
                kwargs['env'] = {**kwargs['env'], 'ERGORA_TEST_PREPARATION_STOP_AFTER': str(index if index is not None else -1),
                                 'ERGORA_TEST_PREPARATION_ID': ident,
                                 'ERGORA_TEST_PREPARATION_SYNC_FAILURE': sync_failure or '',
                                 'ERGORA_TEST_PREPARATION_TRACE': str(trace) if trace else ''}
            return original(argv, *args, **kwargs)
        monkeypatch.setattr(processes, 'run', invoke)
    return select


def test_exact_plan_and_native_binding_preserve_originals_and_same_intent(preparation_input, monkeypatch):
    state, definition, runtime, prefix, draft = preparation_input
    originals = {p: p.read_bytes() for directory in (runtime, Path(definition['execution']['config_directory']))
                 for p in directory.rglob('*') if p.is_file()}
    preview = training.preview_experiment(state, 'demo', draft, 'trusted', max_run_seconds=300)
    assert {p: p.read_bytes() for p in originals} == originals
    assert training.preparation(state, 'demo', 'gamma')['status'] == 'not_recorded'
    result = training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'],
                                         preview['preview_sha256'], max_run_seconds=300)
    assert result['status'] == 'prepared' and result['confirmed_preview_sha256'] == preview['preview_sha256']
    assert result['intent_sha256'] != preview['preview_sha256']
    assert result['execution_success'] is None and all(item['state'] == 'matching' for item in result['files'])
    for path, raw in preview['plan']['files'].items():
        assert (runtime / path).read_bytes() == raw.encode('utf-8')
    detail = training.inspect(state, 'demo', 'gamma')['experiment']
    assert detail['binding']['manifest_sha'] == hashlib.sha256((runtime / 'training/manifests/gamma.json').read_bytes()).hexdigest()
    assert detail['spec']['manifest_uri'] == (runtime / 'training/manifests/gamma.json').as_uri()
    assert detail['max_run_seconds'] == 300 and detail['job_request'] is None
    published = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    assert training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'],
                                       preview['preview_sha256'], max_run_seconds=300)['status'] == 'prepared'
    # Reading local preparation checkpoints has no SDK gate.
    original_spec = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original_spec(name))
    assert training.preparation(state, 'demo', 'gamma')['status'] == 'prepared'
    assert {p: p.read_bytes() for p in published} == published
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert not (runtime / 'training/jobs/gamma').exists() and not (runtime / 'training/fences/gamma.json').exists()


def test_confirmation_revision_and_explicit_window_fail_before_publication(preparation_input):
    state, _, runtime, _, draft = preparation_input
    preview = training.preview_experiment(state, 'demo', draft, 'trusted')
    with pytest.raises(ValueError, match='exact experiment preparation preview'):
        training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], '0' * 64)
    assert not (runtime / 'ergora/training-preparations').exists()
    projects.bind(state, 'demo', 'memory', {'tool': 'sqlite'}, preview['project_revision'])
    with pytest.raises(ValueError, match='revision changed'):
        training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
    for window in (False, 0):
        with pytest.raises(ValueError, match='Explicit max_run_seconds'):
            training.preview_experiment(state, 'demo', draft, 'trusted', max_run_seconds=window)
    assert not (runtime / 'training/manifests/gamma.json').exists()


@pytest.mark.parametrize('checkpoint', ('training/jobs/gamma/request.json', 'training/fences/gamma.json',
                                       'ergora/training-submissions/gamma.intent.json'))
def test_explicit_resume_refuses_later_start_but_status_and_repeat_prepare_remain_readonly(preparation_input, checkpoint):
    state, _, runtime, _, draft = preparation_input
    preview = training.preview_experiment(state, 'demo', draft, 'trusted')
    prepared = training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
    target = runtime / checkpoint
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{}')
    before = {path: path.read_bytes() for path in runtime.rglob('*') if path.is_file()}
    with pytest.raises(ValueError, match='job, fence or submission already exists'):
        training.resume_prepare(state, 'demo', 'gamma', preview['project_revision'], prepared['intent_sha256'])
    assert training.preparation(state, 'demo', 'gamma')['status'] == 'prepared'
    assert training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])['status'] == 'prepared'
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize('boundary', range(4))
def test_real_process_interruption_at_each_publication_recovers_original_intent(preparation_input, stop_after, boundary):
    state, _, runtime, _, draft = preparation_input
    preview = training.preview_experiment(state, 'demo', draft, 'trusted')
    stop_after(boundary)
    with pytest.raises(ValueError, match='status 73'):
        training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
    stop_after(None)
    recovered_state = State(state.root)
    observed = training.preparation(recovered_state, 'demo', 'gamma')
    expected = 'intent_saved' if boundary == 0 else 'prepared' if boundary == 3 else 'partially_prepared'
    assert observed['status'] == expected and sum(item['state'] == 'matching' for item in observed['files']) == boundary
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    repeated = training.prepare_experiment(recovered_state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
    assert repeated['status'] == expected and {p: p.read_bytes() for p in before} == before
    assert sum((runtime / name).exists() for name in preview['plan']['files']) == boundary
    with pytest.raises(ValueError, match='exact original preparation intent'):
        training.resume_prepare(recovered_state, 'demo', 'gamma', preview['project_revision'], '0' * 64)
    result = training.resume_prepare(recovered_state, 'demo', 'gamma', preview['project_revision'], observed['intent_sha256'])
    assert result['status'] == 'prepared' and result['intent_sha256'] == observed['intent_sha256']
    assert all(path.read_bytes() == raw for path, raw in before.items())
    assert training.inspect(recovered_state, 'demo', 'gamma')['experiment']['job_request'] is None


@pytest.mark.parametrize('changed', ('baseline', 'runner', 'published-manifest'))
def test_partial_recovery_refuses_source_drift_or_conflicting_published_bytes(preparation_input, stop_after, changed):
    state, definition, runtime, prefix, draft = preparation_input
    preview = training.preview_experiment(state, 'demo', draft, 'trusted')
    stop_after(1)
    with pytest.raises(ValueError, match='status 73'):
        training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
    stop_after(None)
    if changed == 'baseline':
        target = prefix / 'baseline.json'
    elif changed == 'runner':
        target = Path(definition['execution']['config_directory']) / 'training-runners/trusted.json'
    else:
        target = runtime / 'training/manifests/gamma.json'
    value = json.loads(target.read_bytes())
    if changed == 'runner':
        value['command'].append('changed-after-confirmation')
    else:
        value['notes'] = 'changed-after-confirmation'
    target.write_text(json.dumps(value))
    before = {p: p.read_bytes() for directory in (runtime, Path(definition['execution']['config_directory']))
              for p in directory.rglob('*') if p.is_file()}
    observed = training.preparation(state, 'demo', 'gamma')
    assert observed['status'] == ('conflict' if changed == 'published-manifest' else 'partially_prepared')
    with pytest.raises(ValueError, match='sources or native plan changed|files conflict'):
        training.resume_prepare(state, 'demo', 'gamma', preview['project_revision'], observed['intent_sha256'])
    assert all(path.read_bytes() == raw for path, raw in before.items())
    assert not (runtime / 'training/specs/gamma.json').exists()


def test_foreign_global_id_and_runner_cannot_be_claimed_or_disclosed(preparation_input):
    state, definition, runtime, _, draft = preparation_input
    preview = training.preview_experiment(state, 'demo', draft, 'trusted')
    foreign = runtime / 'training/manifests/gamma.json'
    raw = b'{"local_project":"foreign","private":"unrelated-project-material"}'
    foreign.write_bytes(raw)
    observed = training.preparation(state, 'demo', 'gamma')
    assert observed['status'] == 'native_files_without_intent' and 'unrelated-project-material' not in json.dumps(observed)
    with pytest.raises(ValueError, match='no matching preparation intent'):
        training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
    assert foreign.read_bytes() == raw and not (runtime / 'ergora/training-preparations/gamma.intent.json').exists()
    other = deepcopy(definition)
    other.update(id='other', tracker={'kind': 'local', 'project': 'local/other'})
    registrations.register(state, other, 0)
    with pytest.raises(ValueError, match='belong to the selected project'):
        training.preview_experiment(state, 'other', draft, 'trusted')


def test_fenced_experiment_and_symlinked_registry_lock_fail_without_intent(preparation_input, tmp_path):
    state, _, runtime, _, draft = preparation_input
    preview = training.preview_experiment(state, 'demo', draft, 'trusted')
    fence = runtime / 'training/fences/gamma.json'
    fence.parent.mkdir();fence.write_text('{}')
    with pytest.raises(ValueError, match='job, fence or submission already exists'):
        training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
    assert not (runtime / 'ergora/training-preparations/gamma.intent.json').exists()
    fence.unlink()
    outside = tmp_path / 'outside'
    outside.write_bytes(b'unchanged')
    (runtime / 'training/registry.lock').symlink_to(outside)
    with pytest.raises(ValueError, match='Path escapes trusted root|[Ss]ymlink'):
        training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
    assert outside.read_bytes() == b'unchanged' and not (runtime / 'ergora/training-preparations/gamma.intent.json').exists()


def test_cli_http_use_exact_plan_and_recover_after_actual_lost_success_reply(preparation_input, monkeypatch, tmp_path):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.interfaces.cli import main
    from ergora.interfaces.web import create_app

    state, _, runtime, _, draft = preparation_input
    source = tmp_path / 'experiment.json'
    source.write_text(json.dumps(draft))
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'experiment-preview', 'demo', '--experiment', str(source), '--runner', 'trusted'])
    preview = json.loads(output.getvalue())
    assert code == 0
    headers = {'Origin': 'http://127.0.0.1', 'X-Ergora-Request': '1'}
    client = TestClient(create_app(state.root), base_url=headers['Origin'], headers=headers)
    body = {'experiment': draft, 'runner_template_id': 'trusted'}
    assert client.post('/api/projects/demo/training/experiment-preview', json=body).json() == preview
    original = processes.run

    def lose_reply(*args, **kwargs):
        result = original(*args, **kwargs)
        assert result['status'] == 'succeeded'
        raise ValueError('Lost reply after the actual native preparation finished')

    monkeypatch.setattr(processes, 'run', lose_reply)
    result = client.post('/api/projects/demo/training/prepare', json={**body, 'revision': preview['project_revision'],
                                                                    'preview_sha256': preview['preview_sha256']})
    assert result.status_code == 400 and 'Lost reply' in result.text
    monkeypatch.setattr(processes, 'run', original)
    saved = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    observed = client.get('/api/projects/demo/training/gamma/preparation').json()
    assert observed['status'] == 'prepared'
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'resume-prepare', 'demo', 'gamma',
                     '--revision', str(preview['project_revision']), '--intent-sha256', observed['intent_sha256']])
    assert code == 0 and json.loads(output.getvalue())['status'] == 'prepared'
    assert all(path.read_bytes() == raw for path, raw in saved.items())


@pytest.mark.parametrize('failure', ('file', 'parent', 'ancestor', 'root', 'readback-inode', 'readback-open-inode'))
def test_original_intent_is_confirmed_before_any_native_output_and_equal_visible_recovery(
        preparation_input, stop_after, tmp_path, failure):
    state, _, runtime, _, draft = preparation_input
    preview = training.preview_experiment(state, 'demo', draft, 'trusted')
    trace = tmp_path / 'intent-confirmation.jsonl'
    stop_after(sync_failure=failure, trace=trace)
    with pytest.raises(ValueError, match='intent synchronization failure|changed during durable readback'):
        training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
    intent = runtime / 'ergora/training-preparations/gamma.intent.json'
    original = intent.read_bytes()
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    assert events and not any(item['event'] == 'native-output-call' for item in events)
    assert not any((runtime / name).exists() for name in preview['plan']['files'])
    # The visible intent is retained. Matched prepare and explicit resume must
    # both complete its same durability check before publishing anything.
    for operation in (
            lambda: training.prepare_experiment(state, 'demo', draft, 'trusted',
                preview['project_revision'], preview['preview_sha256']),
            lambda: training.resume_prepare(state, 'demo', 'gamma', preview['project_revision'],
                validate_preparation_intent(json.loads(intent.read_bytes()))['intent_sha256'])):
        with pytest.raises(ValueError, match='intent synchronization failure|changed during durable readback'):
            operation()
    assert intent.read_bytes() == original
    assert not any((runtime / name).exists() for name in preview['plan']['files'])
    stop_after()
    original_identity = validate_preparation_intent(json.loads(original))['intent_sha256']
    recovered = training.resume_prepare(State(state.root), 'demo', 'gamma', preview['project_revision'], original_identity)
    assert recovered['status'] == 'prepared' and recovered['intent_sha256'] == original_identity
    assert recovered['confirmed_preview_sha256'] == preview['preview_sha256']
    assert intent.read_bytes() == original
    if failure == 'parent':
        stop_after(sync_failure=failure, trace=trace)
        with pytest.raises(ValueError, match='intent synchronization failure'):
            training.preparation(state, 'demo', 'gamma')
        with pytest.raises(ValueError, match='intent synchronization failure'):
            training.prepare_experiment(state, 'demo', draft, 'trusted', preview['project_revision'], preview['preview_sha256'])
        assert intent.read_bytes() == original
    assert not (runtime / 'training/jobs/gamma').exists()
    assert not (state.root / 'training-cycles').exists()


@pytest.fixture
def positive_cpu_records(tmp_path):
    """Pure C/B/I/A data, not an actual operator acceptance or budget birth."""
    import ergora.training.materials as materials
    runner = {'schema_version': 2, 'runner_template_id': 'cpu', 'project': 'demo', 'repo': '/original/project',
        'command': ['/original/python', '{configuration_driver}', '{configuration_request}'], 'timeout_seconds': 20,
        'configuration_readback': {'protocol': 'training-configuration-driver-v1',
            'source': {'repo': '/original/source', 'commit': '1' * 40, 'inventory_sha256': '2' * 64, 'entrypoint': 'driver.py'},
            'observation_scheme': 'original-stdlib-cpu-v1'}}
    contract = {'schema_version': 1, 'kind': 'training-cpu-execution-contract', 'operation': 'cpu-diagnostic-v1',
        'implementation': {'source': {**runner['configuration_readback']['source'], 'entrypoint_sha256': '3' * 64},
            'driver_protocol': 'training-configuration-driver-v1', 'observation_scheme': 'original-stdlib-cpu-v1',
            'runner_sha256': materials.observation_sha256(runner), 'wrapper_entry': 'ergora.training.configuration:main',
            'core_sources_sha256': '4' * 64}, 'conformance': dict(materials.CPU_CONFORMANCE),
        'input_domain': {'type': 'object', 'properties': {'batch': {'type': 'integer', 'minimum': 1, 'maximum': 96},
            'strategy': {'type': 'string', 'enum': ['loop', 'closed-form']}},
            'required': ['batch', 'strategy'], 'additionalProperties': False}}
    contract['sha256'] = materials.observation_sha256(contract)
    manifest = {'schema_version': 1, 'experiment_id': 'cpu-original', 'local_project': 'demo',
                'execution': {'operation': 'full-verify', 'cpu_contract': contract}}
    manifest_raw = materials.observation_bytes(manifest) + b'\n'
    body = {'schema_version': 2, 'operation': 'prepare-training', 'control_home': '/original/control', 'project': 'demo',
        'repo': '/original/project', 'execution': {'state_directory': str(tmp_path / 'native-original')}, 'registration_sha256': '5' * 64,
        'experiment_id': 'cpu-original', 'project_revision': 7, 'request': {'experiment': manifest},
        'sources': {'runner': {'document': runner, 'file_sha256': '6' * 64}},
        'files': {'training/manifests/cpu-original.json': manifest_raw.decode()}}
    intent = {**body, 'confirmed_preview_sha256': materials.observation_sha256(body),
        'confirmation': {'kind': 'training-preparation-confirmation', 'actor_id': 'unix:1000:pure-unit',
            'project_revision': 7, 'request_sha256': materials.observation_sha256(body['request'])}}
    admission = materials.make_cpu_preparation_admission(intent)
    return materials, runner, contract, manifest, manifest_raw, body, intent, admission


def test_cpu_contract_confirmation_keeps_preview_and_original_intent_distinct(positive_cpu_records):
    materials, runner, contract, manifest, raw, body, intent, admission = positive_cpu_records
    checked = materials.validate_preparation_intent(intent)
    assert checked['body'] == body and checked['preview_sha256'] == materials.observation_sha256(body)
    assert checked['intent_sha256'] == materials.observation_sha256(intent) != checked['preview_sha256']
    assert materials.validate_cpu_preparation_admission(admission, intent, raw, runner) == contract
    changed = deepcopy(intent)
    changed['confirmation']['actor_id'] = 'unix:1001:other-original-operator'
    assert materials.preparation_preview_body(changed) == body
    assert materials.make_cpu_preparation_admission(changed) != admission
    with pytest.raises(ValueError, match='original confirmation-bearing intent'):
        materials.validate_cpu_preparation_admission(admission, changed, raw, runner)
    changed = deepcopy(intent)
    changed['confirmation']['request_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='original exact preview'):
        materials.validate_preparation_intent(changed)


def test_cpu_contract_domain_binding_and_old_data_never_synthesize_acceptance(positive_cpu_records):
    materials, runner, contract, manifest, raw, body, intent, admission = positive_cpu_records
    assert materials.validate_cpu_contract_configuration(contract, b'{"batch":48,"strategy":"loop"}')['batch'] == 48
    for wrong in (b'{"batch":0,"strategy":"loop"}', b'{"batch":48,"strategy":"remote"}', b'{"batch":true,"strategy":"loop"}'):
        with pytest.raises(ValueError, match='input domain'):
            materials.validate_cpu_contract_configuration(contract, wrong)
    for constraint in ({'enum': [True]}, {'const': True}):
        changed = deepcopy(contract)
        changed['input_domain']['properties']['batch'].update(constraint)
        changed['sha256'] = materials.observation_sha256({key: value for key, value in changed.items() if key != 'sha256'})
        with pytest.raises(ValueError, match='input domain'):
            materials.validate_cpu_contract_configuration(changed, b'{"batch":1,"strategy":"loop"}')
    other = deepcopy(runner)
    other['command'][0] = '/other/python'
    with pytest.raises(ValueError, match='original registered runner'):
        materials.validate_cpu_execution_contract(contract, runner=other)
    old = {**body, 'schema_version': 1}
    with pytest.raises(ValueError, match='historical preparation'):
        materials.make_cpu_preparation_admission(old)
    old['request'] = {'experiment': {**manifest, 'execution': {'operation': 'full-verify'}}}
    ordinary = {**manifest, 'execution': {'operation': 'full-verify'}}
    old['files'] = {'training/manifests/cpu-original.json': json.dumps(ordinary)}
    assert materials.validate_preparation_intent(old)['confirmation'] is None
    assert materials.make_cpu_preparation_admission(old) is None


def test_cpu_contract_original_admission_reader_without_state_or_sdk(positive_cpu_records, tmp_path):
    materials, runner, contract, manifest, raw, body, intent, admission = positive_cpu_records
    from ergora.training.runtime.evidence import read_cpu_preparation_admission
    from ergora.training.materials import cpu_preparation_observation
    root = tmp_path / 'native-original'
    for relative, value in (('training/manifests/cpu-original.json', raw),
        ('ergora/training-preparations/cpu-original.intent.json', materials.observation_bytes(intent) + b'\n'),
        ('ergora/training-preparations/cpu-original.cpu-contract-admission.json', materials.observation_bytes(admission) + b'\n')):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    result = read_cpu_preparation_admission(root, 'cpu-original', manifest, runner)
    observed = cpu_preparation_observation(result, 'cpu-original')
    assert observed['contract_sha256'] == contract['sha256']
    assert observed['intent_utf8'].encode() == result['intent_raw']
    assert read_cpu_preparation_admission(root, 'cpu-original', {'execution': {'operation': 'full-verify'}}, runner) is None
    path = root / 'ergora/training-preparations/cpu-original.cpu-contract-admission.json'
    path.write_bytes(materials.observation_bytes({**admission, 'confirmed_preview_sha256': '0' * 64}))
    with pytest.raises(ValueError, match='original confirmation-bearing intent'):
        read_cpu_preparation_admission(root, 'cpu-original', manifest, runner)


@pytest.mark.parametrize('corruption', [None, 'missing-staged-admission', 'wrong-command', 'symlink-parent', 'fifo-configuration', 'bounded-reads', 'missing-native', 'wrong-output',
    'coherent-no-c', 'coherent-no-c-missing-managed', 'original-no-c-managed', 'original-no-c-unmanaged', 'original-no-c-missing-owner',
    'unbudgeted-app-start', 'unbudgeted-start-mismatch', 'unbudgeted-budget-marker'])
def test_cpu_process_cold_import_uses_original_core_under_native_environment(positive_cpu_records, tmp_path, corruption):
    """Synthetic records prove import resolution only, never a real job/admission."""
    import os
    import subprocess
    import venv
    from ergora.training.configuration import cpu_contract_sources
    materials, runner, original, old_manifest, old_raw, old_body, old_intent, _ = positive_cpu_records
    runner = deepcopy(runner)
    runner['command'][0] = str(tmp_path / 'bare-native-python/bin/python')
    source = PACKAGE_ROOT
    native = native_resources.ROOT / 'platform'
    state = tmp_path / 'state'
    installed = tmp_path / 'original-native'
    installed.mkdir()
    descriptor = b'{"kind":"unit-original-descriptor"}\n'
    (installed / 'ergora-native-runtime.json').write_bytes(descriptor)
    contract = deepcopy(original)
    contract['implementation']['runner_sha256'] = materials.observation_sha256(runner)
    mapping = cpu_contract_sources()
    contract['implementation']['core_sources_sha256'] = materials.observation_sha256(mapping)
    contract['sha256'] = materials.observation_sha256({key: value for key, value in contract.items() if key != 'sha256'})
    manifest = {**old_manifest, 'execution': {'operation': 'full-verify', 'cpu_contract': contract}}
    unbudgeted_app = corruption in ('unbudgeted-app-start', 'unbudgeted-start-mismatch', 'unbudgeted-budget-marker')
    original_no_c = unbudgeted_app or corruption in ('original-no-c-managed', 'original-no-c-unmanaged', 'original-no-c-missing-owner')
    if original_no_c:
        manifest['execution'].pop('cpu_contract')
    if corruption == 'original-no-c-unmanaged' or unbudgeted_app:
        runner['configuration_readback'] = None
        runner['command'] = ['/ordinary/no-c-runner']
    manifest_raw = materials.observation_bytes(manifest) + b'\n'
    body = deepcopy(old_body)
    body['execution'] = {'installation': str(installed), 'state_directory': str(state)}
    body['sources']['runner']['document'] = runner
    body['request']['experiment'] = manifest
    body['files']['training/manifests/cpu-original.json'] = manifest_raw.decode()
    intent = {**body, 'confirmed_preview_sha256': materials.observation_sha256(body),
        'confirmation': {**old_intent['confirmation'], 'request_sha256': materials.observation_sha256(body['request'])}}
    admission = materials.make_cpu_preparation_admission(intent)
    binding = {'experiment_id': 'cpu-original', 'manifest_sha': hashlib.sha256(manifest_raw).hexdigest()}
    native_request = {'experiment': {'binding': binding}, 'runner': runner}
    native_raw = materials.observation_bytes(native_request)
    context = {'authorization': {'sha256': 'a' * 64}, 'intent': {'schema_version': 1, 'operation': 'start',
        'control_home': '/original/control', 'project': 'demo', 'repo': runner['repo'],
        'registration_sha256': '5' * 64, 'workflow_id': 'perf-experiment/cpu-original',
        'project_revision': 7, 'operation_id': 'b' * 32, 'experiment_id': 'cpu-original',
        'budget': {'authorization_sha256': 'a' * 64},
        'execution': {'installation': str(installed), 'state_directory': str(state)},
        'observation': {'experiment': {'experiment_id': 'cpu-original', 'binding': binding, 'spec': native_request['experiment'],
            'manifest': manifest, 'current_runner': runner}}}}
    output = state / 'training/jobs/cpu-original/run-output'
    request = {'binding': binding, 'native_request_sha256': hashlib.sha256(native_raw).hexdigest(),
        'runner_sha256': materials.observation_sha256(runner), 'context': context, 'output': str(output),
        'cpu_contract_core': {'package_directory': str(source), 'sources_sha256': contract['implementation']['core_sources_sha256']}}
    owner = {'intent_sha256': materials.observation_sha256(context['intent']), 'authorization_sha256': 'a' * 64,
        'context_sha256': materials.observation_sha256(context), 'execution_capability': {
        'installation': str(installed), 'descriptor_sha256': hashlib.sha256(descriptor).hexdigest()}}
    managed = {'kind': 'training-execution-request', 'experiment_id': 'cpu-original',
        'native_request_sha256': hashlib.sha256(native_raw).hexdigest(),
        'owner_sha256': materials.observation_sha256(owner), 'start_intent_sha256': materials.observation_sha256(context['intent']),
        'authorization_sha256': 'a' * 64}
    request['managed'] = {'request_sha256': materials.observation_sha256(managed)}
    if original_no_c:
        request.pop('cpu_contract_core')
    files = {'training/manifests/cpu-original.json': manifest_raw,
        'training/jobs/cpu-original/request.json': native_raw,
        'training/jobs/cpu-original/configuration-request.json': materials.observation_bytes(request),
        'training/jobs/cpu-original/managed-execution/request.json': materials.observation_bytes(managed),
        'ergora/training-submissions/cpu-original.intent.json': materials.observation_bytes(context['intent']),
        'ergora/training-submissions/cpu-original.budget/owner.json': materials.observation_bytes(owner),
        'ergora/training-preparations/cpu-original.intent.json': materials.observation_bytes(intent),
        'ergora/training-preparations/cpu-original.cpu-contract-admission.json': materials.observation_bytes(admission),
        'training/jobs/cpu-original/run-output/cpu-contract-admission.json': materials.observation_bytes(admission),
        'training/jobs/cpu-original/run-output/cpu-core-sources.json': materials.observation_bytes({
            'package_directory': str(source), 'sources': mapping, 'contract_sha256': contract['sha256']})}
    if original_no_c:
        files = {name: raw for name, raw in files.items() if not name.endswith('.cpu-contract-admission.json')
                 and not name.endswith('/cpu-contract-admission.json') and not name.endswith('/cpu-core-sources.json')}
    if corruption == 'original-no-c-unmanaged':
        files = {name: raw for name, raw in files.items() if name in ('training/manifests/cpu-original.json', 'training/jobs/cpu-original/request.json')}
    if unbudgeted_app:
        original_start = deepcopy(context['intent'])
        original_start.pop('budget')
        if corruption == 'unbudgeted-start-mismatch':
            original_start['observation']['experiment']['current_runner']['command'] = ['/changed/original-runner']
        if corruption == 'unbudgeted-budget-marker':
            original_start['budget'] = None
        files = {name: raw for name, raw in files.items() if name in ('training/manifests/cpu-original.json', 'training/jobs/cpu-original/request.json')}
        files['ergora/training-submissions/cpu-original.intent.json'] = materials.observation_bytes(original_start)
    for relative, raw in files.items():
        path = state / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    if corruption == 'missing-staged-admission':
        (output / 'cpu-contract-admission.json').unlink()
    if corruption == 'symlink-parent':
        original_job = output.parent
        moved_job = original_job.with_name('moved-original-job')
        original_job.rename(moved_job)
        original_job.symlink_to(moved_job, target_is_directory=True)
    if corruption == 'fifo-configuration':
        config = output.parent / 'configuration-request.json'
        config.unlink()
        os.mkfifo(config)
    if corruption == 'missing-native':
        (output.parent / 'request.json').unlink()
    if corruption in ('coherent-no-c', 'coherent-no-c-missing-managed'):
        changed = deepcopy(manifest)
        changed['execution'] = {'operation': 'full-verify'}
        changed_raw = materials.observation_bytes(changed) + b'\n'
        (state / 'training/manifests/cpu-original.json').write_bytes(changed_raw)
        changed_native = deepcopy(native_request)
        changed_native['experiment']['binding']['manifest_sha'] = hashlib.sha256(changed_raw).hexdigest()
        (output.parent / 'request.json').write_bytes(materials.observation_bytes(changed_native))
        if corruption == 'coherent-no-c-missing-managed':
            (output.parent / 'managed-execution/request.json').unlink()
    if corruption == 'original-no-c-missing-owner':
        (state / 'ergora/training-submissions/cpu-original.budget/owner.json').unlink()
    bare = tmp_path / 'bare-native-python'
    venv.EnvBuilder(with_pip=False).create(bare)
    program = '''import importlib.util,json,sys
from pathlib import Path
from agent_platform import core,process_job
from agent_platform.sandbox import Sandbox
actual=Sandbox().env['PYTHONPATH']
assert sys.argv[1] not in actual.split(':')
assert importlib.util.find_spec('ergora') is None
core.ROOT=Path(sys.argv[2])
command=[sys.executable,sys.argv[3],sys.argv[4]]
output=Path(sys.argv[5])
folder=process_job.STATE/'processes/af-perf-cpu-original-run'
process_request={'name':folder.name}
if sys.argv[6]=='wrong-command': command[1]='/wrong/entry.py'
if sys.argv[6]=='wrong-output': output=output.parent/'wrong-output'
if sys.argv[6] in ('original-no-c-unmanaged','unbudgeted-app-start','unbudgeted-start-mismatch','unbudgeted-budget-marker'): command=['/ordinary/no-c-runner']
if sys.argv[6]=='bounded-reads':
 def no_unbounded(*args,**kwargs): raise AssertionError('Bootstrap used unbounded Path.read_bytes')
 Path.read_bytes=no_unbounded
if sys.argv[6] in ('original-no-c-managed','original-no-c-unmanaged','unbudgeted-app-start'):
 assert process_job._cpu_training_module(command,output,folder,process_request) is None
 print(json.dumps({'ordinary':True}));sys.exit(0)
if sys.argv[6] not in ('None','bounded-reads'):
 folder.mkdir(parents=True)
 process_request.update(schema_version=1,output=str(output),checkout=str(folder),command=command,writable=False,
  fence=None,timeout=1,model=None,protocol=None,policy=None)
 (folder/'request.json').write_text(json.dumps(process_request))
 process_job.snapshot=lambda path:('fixed','','fixed')
 process_job.child_environment=lambda model:{}
 def no_spawn(*args,**kwargs): raise AssertionError('Typed original CPU request reached Popen')
 process_job.subprocess.Popen=no_spawn
 process_job.run(folder)
 terminal=json.loads((folder/'terminal.json').read_text())
 assert terminal['returncode']==125 and not (folder/'pid.json').exists()
 print(json.dumps({'rejected':True}));sys.exit(0)
module=process_job._cpu_training_module(command,output,folder,process_request)
assert Path(module.__file__).resolve()==Path(sys.argv[3])
assert 'ergora.storage.state' not in sys.modules
print(json.dumps({'helper':module.__file__,'native_environment':actual,'scope':'cold import only; no helper/process/window execution'}))
'''
    environment = {**os.environ, 'AGENTFLOW_STATE_DIR': str(state), 'AGENTFLOW_CONFIG_DIR': str(tmp_path / 'config'),
        'PYTHONPATH': os.pathsep.join(str(native / name) for name in ('local','upstream/platform','upstream/temporal','upstream'))}
    result = subprocess.run([str(bare / 'bin/python'), '-P', '-c', program, str(source.parent), str(installed),
        str(source / 'training/configuration.py'), str(state / 'training/jobs/cpu-original/configuration-request.json'), str(output), str(corruption)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=2 if corruption == 'fifo-configuration' else 15)
    assert result.returncode == 0, result.stderr
    if corruption in (None, 'bounded-reads'):
        assert json.loads(result.stdout)['helper'] == str(source / 'training/configuration.py')
    elif corruption in ('original-no-c-managed', 'original-no-c-unmanaged', 'unbudgeted-app-start'):
        assert json.loads(result.stdout)['ordinary'] is True
    else:
        assert json.loads(result.stdout)['rejected'] is True


def test_cpu_process_last_admission_follows_environment_io_and_denies_spawn(tmp_path, monkeypatch):
    """Real process_job control, synthetic source ports, zero Popen/workload calls."""
    import importlib
    from types import SimpleNamespace
    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/local'))
    job = importlib.import_module('agent_platform.process_job')
    import ergora.training.configuration as configuration
    state, output, checkout = tmp_path / 'state', tmp_path / 'output', tmp_path / 'checkout'
    folder = state / 'processes/last-admission-only'
    folder.mkdir(parents=True)
    checkout.mkdir()
    fence = tmp_path / 'fence.json'
    request = {'name': 'last-admission-only', 'output': str(output), 'checkout': str(checkout),
        'command': ['/never-run'], 'fence': str(fence), 'writable': False, 'model': None, 'timeout': 10,
        'protocol': None, 'policy': None}
    (folder / 'request.json').write_text(json.dumps(request))
    monkeypatch.setattr(job, 'STATE', state)
    monkeypatch.setattr(job, 'snapshot', lambda path: ('fixed', '', 'fixed'))
    calls = []
    def environment(model):
        fence.write_text('{}')
        calls.append('environment-io-complete')
        return {}
    def admission(request, raw):
        assert fence.exists() and calls == ['environment-io-complete']
        calls.append('actual-last-admission')
        raise ValueError('Original stop observed after environment I/O')
    monkeypatch.setattr(configuration, '_inputs', admission)
    module = SimpleNamespace(cpu_process_context=lambda *args: ({}, b'original-request'),
        cpu_process_last_admission=configuration.cpu_process_last_admission)
    monkeypatch.setattr(job, '_cpu_training_module', lambda *args: module)
    monkeypatch.setattr(job, 'child_environment', environment)
    monkeypatch.setattr(job.subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('No process may spawn after the late stop'))
    job.run(folder)
    terminal = json.loads((folder / 'terminal.json').read_bytes())
    assert calls == ['environment-io-complete', 'actual-last-admission']
    assert terminal['returncode'] == 125 and 'Original stop observed' in terminal['detail']
    assert not (folder / 'pid.json').exists()


def test_cpu_contract_visible_acceptance_requires_original_durable_confirmation(positive_cpu_records, tmp_path, monkeypatch):
    import ergora.training.materials as materials
    from ergora.training.runtime.evidence import read_cpu_preparation_admission
    _, runner, _, manifest, raw, _, intent, admission = positive_cpu_records
    root = tmp_path / 'native-original'
    records = {'training/manifests/cpu-original.json': raw,
        'ergora/training-preparations/cpu-original.intent.json': materials.observation_bytes(intent) + b'\n',
        'ergora/training-preparations/cpu-original.cpu-contract-admission.json': materials.observation_bytes(admission) + b'\n'}
    for name, original in records.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(original)
    acceptance = root / 'ergora/training-preparations/cpu-original.cpu-contract-admission.json'
    before = acceptance.read_bytes(), acceptance.stat().st_ino
    confirm = materials.confirm_file
    calls = []
    def unavailable(path, original, selected_root):
        if Path(path) == acceptance:
            calls.append('original-A-sync-attempt')
            raise OSError('Original A directory durability is unknown')
        return confirm(path, original, selected_root)
    monkeypatch.setattr(materials, 'confirm_file', unavailable)
    with pytest.raises(OSError, match='durability is unknown'):
        read_cpu_preparation_admission(root, 'cpu-original', manifest, runner)
    assert calls == ['original-A-sync-attempt']
    assert acceptance.read_bytes() == before[0] and acceptance.stat().st_ino == before[1]
    monkeypatch.setattr(materials, 'confirm_file', confirm)
    assert read_cpu_preparation_admission(root, 'cpu-original', manifest, runner)['admission'] == admission
    assert acceptance.read_bytes() == before[0] and acceptance.stat().st_ino == before[1]


def test_cpu_contract_present_null_and_large_confirmation_bounds_are_explicit(positive_cpu_records):
    import ergora.training.materials as m
    for value in (None, False, {}, 'claimed-cpu'):
        with pytest.raises(ValueError):
            m.cpu_contract({'execution': {'operation': 'full-verify', 'cpu_contract': value}})
    _, _, contract, manifest, _, body, _, _ = positive_cpu_records
    large_contract = deepcopy(contract)
    large_contract['input_domain']['properties']['strategy']['enum'] += ['choice-' + str(i) + '-' + 'x' * 36 for i in range(12000)]
    large_contract['sha256'] = m.observation_sha256({key: value for key, value in large_contract.items() if key != 'sha256'})
    larger = deepcopy(body)
    larger['request']['experiment']['execution']['cpu_contract'] = large_contract
    large_manifest = {**manifest, 'execution': {'operation': 'full-verify', 'cpu_contract': large_contract}}
    larger['files']['training/manifests/cpu-original.json'] = (m.observation_bytes(large_manifest) + b'\n').decode()
    preview = hashlib.sha256(m.observation_bytes(larger, 16 * m.LIMIT)).hexdigest()
    request_sha = hashlib.sha256(m.observation_bytes(larger['request'], 16 * m.LIMIT)).hexdigest()
    original = {**larger, 'confirmed_preview_sha256': preview, 'confirmation': {
        'kind': 'training-preparation-confirmation', 'actor_id': 'unix:1000:pure-unit',
        'project_revision': larger['project_revision'], 'request_sha256': request_sha}}
    assert len(m.observation_bytes(original, 16 * m.LIMIT)) > m.LIMIT
    checked = m.validate_preparation_intent(original)
    assert checked['preview_sha256'] == preview and checked['intent_sha256'] != preview
    assert m.make_cpu_preparation_admission(original)['confirmed_preview_sha256'] == preview
    oversized = deepcopy(original)
    oversized['files']['oversized-complete-material'] = 'x' * (16 * m.LIMIT)
    with pytest.raises(ValueError, match='complete read capacity'):
        m.validate_preparation_intent(oversized)


def test_cpu_contract_archived_materials_read_without_original_host_refs(positive_cpu_records, tmp_path, monkeypatch):
    """Mock original actor graph, no real budget/worker/window; archive reader join."""
    import ergora.training.materials as m
    import ergora.training.execution_protocol as protocol
    from ergora.training.runtime.evidence import cpu_contract_evidence
    from ergora.training.materials import cpu_preparation_observation
    _, runner, contract, manifest, manifest_raw, body, intent, admission = positive_cpu_records
    contract, body = deepcopy(contract), deepcopy(body)
    core_sources = {'training/configuration.py': '7' * 64}
    contract['implementation']['core_sources_sha256'] = m.observation_sha256(core_sources)
    contract['sha256'] = m.observation_sha256({key: value for key, value in contract.items() if key != 'sha256'})
    manifest = {**manifest, 'execution': {'operation': 'full-verify', 'cpu_contract': contract}}
    manifest_raw = m.observation_bytes(manifest) + b'\n'
    body['execution']['state_directory'] = '/old-native/state'
    body['request']['experiment'] = manifest
    body['files']['training/manifests/cpu-original.json'] = manifest_raw.decode()
    intent = {**body, 'confirmed_preview_sha256': m.observation_sha256(body),
        'confirmation': {**intent['confirmation'], 'request_sha256': m.observation_sha256(body['request'])}}
    admission = m.make_cpu_preparation_admission(intent)
    output = tmp_path / 'archive'
    output.mkdir()
    def write(name, value):
        raw = value if isinstance(value, bytes) else m.observation_bytes(value)
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    intent_raw, admission_raw = m.observation_bytes(intent) + b'\n', m.observation_bytes(admission) + b'\n'
    write('cpu-contract-preparation-intent.json', intent_raw)
    write('cpu-contract-admission.json', admission_raw)
    checked = m.validate_preparation_intent(intent)
    envelope = cpu_preparation_observation({'contract': contract, 'contract_sha256': contract['sha256'],
        'intent_raw': intent_raw, 'admission_raw': admission_raw,
        'preview_sha256': checked['preview_sha256'], 'intent_sha256': checked['intent_sha256']}, 'cpu-original', output=True)
    authorization = {'schema_version': 1, 'sha256': 'a' * 64}
    submission = {'experiment_id': 'cpu-original', 'execution': body['execution'], 'budget': {'cycle_id': 'mock-manual'},
                  'observation': {'experiment': {'manifest': manifest}}}
    binding = {'intent_sha256': m.observation_sha256(submission), 'authorization_sha256': authorization['sha256']}
    boot = '12345678-1234-1234-1234-123456789abc'
    def frame(role, pid, parent):
        return {'protocol': 'training-cpu-context-v1', 'contract_sha256': contract['sha256'], 'role': role,
            'binding': binding, 'subject': {'pid': pid, 'tid': pid, 'start_ticks': pid, 'parent_pid': parent, 'boot_id': boot},
            'snapshot': None, 'state': 'unsupported', 'reason': 'mock data only; no FD/window proof'}
    sources, refs = [], {}
    for role, pid, parent in (('parent', 10, 1), ('budget', 20, 10)):
        value = frame(role, pid, parent)
        copied = write('cpu-context-sources/' + role + '.raw', value)
        original = {'path': '/unavailable-original/' + role + '.json', 'sha256': copied['sha256'], 'bytes': copied['bytes']}
        refs[role] = original
        sources.append({'original_path': original['path'], 'original_sha256': original['sha256'],
                        'original_bytes': original['bytes'], 'artifact_ref': copied})
    context = {'intent': submission, 'authorization': authorization, 'cpu_context': {**refs, 'cycle': None}}
    original_job = Path('/old-native/state/training/jobs/cpu-original')
    package = '/old-install/site-packages/ergora'
    request = {'binding': {'experiment_id': 'cpu-original', 'manifest_sha': hashlib.sha256(manifest_raw).hexdigest()},
               'context': context, 'output': str(original_job / 'run-output'),
               'manifest': '/old-native/state/training/manifests/cpu-original.json',
               'cpu_contract_core': {'package_directory': package, 'sources_sha256': contract['implementation']['core_sources_sha256']},
               'cpu_contract_preparation': {key: envelope[key] for key in ('intent_ref', 'admission_ref')}}
    managed = {'request': {'original': 'mock normal request'}, 'launch': {'original': 'mock normal launch'}}
    managed['attempt'] = {'request_sha256': m.observation_sha256(managed['request']),
        'launch_sha256': m.observation_sha256(managed['launch']),
        'supervisor': {'pid': 30, 'start_ticks': '30', 'boot_id': boot},
        'executor': {'pid': 40, 'start_ticks': '40', 'boot_id': boot}}
    managed['ack'] = {'attempt_sha256': m.observation_sha256(managed['attempt']), 'executor': managed['attempt']['executor']}
    request['managed'] = {name + '_sha256': m.observation_sha256(value) for name, value in managed.items()}
    managed_refs = {name: write('cpu-managed-' + name + '.json', value) for name, value in managed.items()}
    native = write('cpu-native-context.json', frame('native', 40, 30))
    relation = write('cpu-native-parent.json', {'kind': 'training-cpu-native-parent', 'binding': binding,
        'supervisor': {'pid': 30, 'start_ticks': '30', 'boot_id': boot}, 'supervisor_parent_pid': 20,
        'budget': {'pid': 20, 'start_ticks': '20', 'boot_id': boot}})
    write('cpu-wrapper-context.json', frame('wrapper', 70, 60))
    write('cpu-wrapper-prepared-context.json', frame('wrapper', 70, 60))
    write('cpu-core-sources.json', {'package_directory': package, 'sources': core_sources, 'contract_sha256': contract['sha256']})
    write('cpu-contract-configuration-request.json', request)
    command = [runner['command'][0], package + '/training/configuration.py', str(original_job / 'configuration-request.json')]
    process_records = {'request': write('cpu-process-request.json', {'output': request['output'], 'command': command}),
        'started': write('cpu-process-started.json', {'monitor_pid': 50, 'command': command}),
        'pid': write('cpu-process-pid.json', {'pid': 60})}
    write('cpu-process-context.json', frame('process', 50, 40))
    metadata = {'schema_version': 1, 'kind': 'training-cpu-execution-materials', 'contract_sha256': contract['sha256'],
        'budget_context': context['cpu_context'], 'sources': sources, 'native_ref': native, 'native_parent_ref': relation,
        'managed_records': managed_refs, 'process_records': process_records, 'lineage_reason': None}
    write('cpu-execution-materials.json', metadata)
    live = protocol.read_raw
    def no_original_host(path, *args, **kwargs):
        if str(path).startswith(('/unavailable-original/', '/old-native/', '/old-install/')):
            pytest.fail('Offline CPU evidence followed an original host ref instead of copied raw')
        return live(path, *args, **kwargs)
    monkeypatch.setattr(protocol, 'read_raw', no_original_host)
    assert cpu_contract_evidence(output, request, manifest) == envelope
    with pytest.raises(ValueError, match='allocation eligibility|normal owner'):
        cpu_contract_evidence(output, request, manifest, require_complete=True,
                              expected_owner={'pid': 20, 'start_ticks': '20', 'boot_id': boot})
    wrong = frame('native', 41, 30)
    metadata['native_ref'] = write('cpu-native-context.json', wrong)
    write('cpu-execution-materials.json', metadata)
    with pytest.raises(ValueError, match='original actual process/thread subject'):
        cpu_contract_evidence(output, request, manifest)
    metadata['native_ref'] = write('cpu-native-context.json', frame('native', 40, 30))
    write('cpu-execution-materials.json', metadata)
    with monkeypatch.context() as current:
        current.setattr(protocol, 'validate_cpu_budget_context', lambda *a, **kw: {'placement': 'budget'})
        current.setattr(m, 'validate_cpu_context_observation', lambda *a, **kw: {'placement': 'native'})
        with pytest.raises(ValueError, match='placement changed from budget to native executor'):
            cpu_contract_evidence(output, request, manifest, require_complete=True,
                                  expected_owner={'pid': 20, 'start_ticks': '20', 'boot_id': boot})
    changed = json.loads((output / 'cpu-contract-admission.json').read_bytes())
    changed['confirmation']['actor_id'] = 'unix:999:wrong'
    write('cpu-contract-admission.json', changed)
    with pytest.raises(ValueError, match='original confirmation-bearing intent'):
        cpu_contract_evidence(output, request, manifest)


def test_cpu_contract_data_reader_denies_state_sdk_imports(positive_cpu_records, tmp_path):
    import os
    import subprocess
    _, runner, _, manifest, raw, _, intent, admission = positive_cpu_records
    import ergora.training.materials as m
    root = tmp_path / 'native-original'
    for name, original in (('training/manifests/cpu-original.json', raw),
        ('ergora/training-preparations/cpu-original.intent.json', m.observation_bytes(intent) + b'\n'),
        ('ergora/training-preparations/cpu-original.cpu-contract-admission.json', m.observation_bytes(admission) + b'\n')):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(original)
    source = IMPORT_ROOT
    program = '''import json,sys
from pathlib import Path
class Deny:
 def find_spec(self,name,*args):
  if name in ('ergora.storage.state','jsonschema','temporalio','perf_temporal','dev_platform') or name.startswith(('jsonschema.','temporalio.','perf_temporal.','dev_platform.')):
   raise AssertionError('Pure original CPU reader imported forbidden application/SDK: '+name)
sys.meta_path.insert(0,Deny())
sys.path.insert(0,sys.argv[1])
from ergora.training.runtime.evidence import read_cpu_preparation_admission
payload=json.load(sys.stdin)
value=read_cpu_preparation_admission(Path(sys.argv[2]),'cpu-original',payload['manifest'],payload['runner'])
assert value['contract_sha256']==payload['manifest']['execution']['cpu_contract']['sha256']
assert value['intent_sha256']!=value['preview_sha256']
'''
    result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', program, str(source), str(root)],
        input=json.dumps({'manifest': manifest, 'runner': runner}), text=True, capture_output=True, timeout=10,
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    assert result.returncode == 0, result.stderr


def test_cpu_reuse_missing_core_subject_is_explicitly_unsupported(tmp_path, monkeypatch):
    import ergora.training.runtime.evidence as evidence
    from ergora.training.materials import observation_bytes
    envelope = {'contract_sha256': 'a' * 64, 'intent_ref': {'path': 'original-intent'},
                'admission_ref': {'path': 'original-admission'}}
    proof = {'contract_sha256': envelope['contract_sha256'],
        'preparation': {key: envelope[key] for key in ('intent_ref', 'admission_ref')},
        'before': {'unsupported_reason': 'Original FD observation failed'}, 'after': None}
    subject = {'pid': 70, 'tid': 70, 'start_ticks': 70, 'parent_pid': 60, 'boot_id': 'original-boot'}
    (tmp_path / 'cpu-wrapper-prepared-context.json').write_bytes(observation_bytes({'subject': subject}))
    baseline = {'cpu_contract': envelope, 'cpu_owner': {'pid': 20},
        'cpu_materials': {'output': str(tmp_path), 'request': {}, 'manifest': {}},
        'reference': {'receipt': {'baseline': {'core_cpu_execution': proof},
            'measurement': [{'provenance': {'run_id': 'baseline-run', 'window_id': 'baseline-window'}}]}}}
    screen = {'cpu_contract': envelope, 'cpu_owner': {'pid': 21},
        'cpu_materials': {'output': str(tmp_path), 'request': {}, 'manifest': {}},
        'result': {'workload': {'scope': {'core_cpu_execution': proof}},
            'windows': [{'provenance': {'run_id': 'screen-run', 'window_id': 'screen-window'}}]}}
    monkeypatch.setattr(evidence, 'cpu_contract_evidence', lambda *a, **kw: envelope)
    with pytest.raises(ValueError, match='original core-owned CPU window subject proof is unavailable'):
        evidence.cpu_reuse_identity(baseline, screen)


def test_cpu_full_approval_without_profile_uses_original_job_runner(positive_cpu_records, tmp_path, monkeypatch):
    import importlib
    from types import SimpleNamespace
    for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream'):
        monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform' / part))
    native = importlib.import_module('agent_platform.training')
    client = importlib.import_module('perf_temporal.client')
    _, runner, _, manifest, raw, _, _, _ = positive_cpu_records
    directory = tmp_path / 'training'
    (directory / 'manifests').mkdir(parents=True)
    (directory / 'manifests/cpu-original.json').write_bytes(raw)
    binding = native.Binding(experiment_id='cpu-original', manifest_sha=hashlib.sha256(raw).hexdigest(),
        candidate_sha='b' * 40, baseline_sha='c' * 40)
    monkeypatch.setattr(native, 'TRAINING', directory)
    monkeypatch.setattr(client, 'load_experiment', lambda path: SimpleNamespace(binding=binding))
    calls = []
    monkeypatch.setattr(native, 'exact_job', lambda job: calls.append(job) or {'runner': runner})
    def stop_at_phase(coroutine):
        coroutine.close()
        raise RuntimeError('Original normal approval phase reached; no effect')
    monkeypatch.setattr(native.asyncio, 'run', stop_at_phase)
    with pytest.raises(RuntimeError, match='Original normal approval phase reached'):
        native.cli(['approve', 'cpu-original', '--evidence-sha', 'e' * 64])
    assert len(calls) == 1 and not (directory / 'approvals').exists()


@pytest.mark.parametrize('change', ['oversized', 'fifo', 'symlink-parent', 'inode-change'])
def test_cpu_bootstrap_descriptor_reader_bounds_and_confirms_original_route(tmp_path, monkeypatch, change):
    import importlib
    import os
    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/local'))
    job = importlib.import_module('agent_platform.process_job')
    parent = tmp_path / 'original'
    parent.mkdir()
    path = parent / 'material.raw'
    path.write_bytes(b'original')
    if change == 'oversized':
        path.write_bytes(b'x' * 17)
    elif change == 'fifo':
        path.unlink(); os.mkfifo(path)
    elif change == 'symlink-parent':
        moved = parent.with_name('moved')
        parent.rename(moved); parent.symlink_to(moved, target_is_directory=True)
    else:
        original = job.os.read
        changed = []
        def replace(fd, size):
            raw = original(fd, size)
            if raw and not changed:
                replacement = path.with_name('replacement')
                replacement.write_bytes(b'original'); replacement.replace(path)
                changed.append(True)
            return raw
        monkeypatch.setattr(job.os, 'read', replace)
    with pytest.raises((OSError, RuntimeError), match='ordinary bounded|changed|directory|symbolic'):
        job._cpu_read_raw(path, 16)


def test_unbudgeted_actual_app_start_reaches_native_full_ordinary_boundary(prepared, service, tmp_path):
    """Actual no-budget app intent and run-local; controlled RPC, zero business Popen."""
    import os
    import subprocess
    state, definition, runtime, _, _, digest = prepared
    select, record = service
    select('held-start-existing')
    record.with_suffix('.continue').touch()
    revision = state.project('demo')['revision']
    selected = training.start(state, 'demo', 'alpha', revision, digest, budget=None)
    intent_path = runtime / 'ergora/training-submissions/alpha.intent.json'
    original_intent = intent_path.read_bytes()
    intent = json.loads(original_intent)
    assert 'budget' not in intent and intent['workflow_id'] == 'perf-experiment/alpha'
    assert intent['observation']['experiment']['current_runner']['configuration_readback'] is None
    assert 'cpu_contract' not in intent['observation']['experiment']['manifest']['execution']
    assert not (runtime / 'ergora/training-submissions/alpha.budget').exists()
    submitted = training.resume_start(state, 'demo', 'alpha', revision, selected['intent_sha256'])
    assert submitted['status'] == 'submitted'
    native_path = runtime / 'training/jobs/alpha/request.json'
    original_native = native_path.read_bytes()
    native = json.loads(original_native)
    assert native['experiment'] == intent['observation']['experiment']['spec']
    assert native['runner'] == intent['observation']['experiment']['current_runner']
    assert json.loads(record.read_bytes())['starts'] == 1
    program = '''import json,sys
from pathlib import Path
from agent_platform import process_job,training,training_executor
from agent_platform.sandbox import Sandbox
# Availability is a controlled test port; this checks ordinary routing, not OS isolation.
Sandbox.probe=lambda self:{'available':True}
original_popen=process_job.subprocess.Popen
boundaries=[]
launchers=[]
class Reaped:
 def poll(self):return 0
 def wait(self,timeout=None):return 0
 def __enter__(self):return self
 def __exit__(self,*args):return False
def controlled_popen(argv,*args,**kwargs):
 if len(argv)>3 and argv[1:3]==['-m','agent_platform.process_job']:
  launchers.append(argv)
  process_job.run(Path(argv[-1]))
  return Reaped()
 if argv and argv[0]=='/usr/bin/timeout':
  boundaries.append(argv)
  raise RuntimeError('Controlled ordinary business boundary; workload not spawned')
 return original_popen(argv,*args,**kwargs)
process_job.subprocess.Popen=controlled_popen
training_executor.track=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('No tracking/model/service effect is allowed'))
result=training.cli(['run-local','alpha','--confirm-manifest-sha',sys.argv[1]])
assert len(launchers)==1 and len(boundaries)==1,(launchers,boundaries,result)
job=training.TRAINING/'jobs/alpha'
original=json.loads((job/'request.json').read_text())
assert boundaries[0][4:]==original['runner']['command']
assert result['binding']==original['experiment']['binding']
terminal=json.loads((process_job.STATE/'processes/af-perf-alpha-run/terminal.json').read_text())
assert terminal['returncode']==125 and 'Controlled ordinary business boundary' in terminal['detail']
assert not (process_job.STATE/'processes/af-perf-alpha-run/pid.json').exists()
print(json.dumps({'ordinary_business_boundary':len(boundaries),'source_launcher_reaped':len(launchers),
 'workload_popen':0,'binding':result['binding'],'native_state':result['state']}))
'''
    installation_path = Path(definition['execution']['installation'])
    source = IMPORT_ROOT
    environment = {**os.environ, 'AGENTFLOW_STATE_DIR': str(runtime),
        'AGENTFLOW_CONFIG_DIR': definition['execution']['config_directory'],
        'PYTHONPATH': os.pathsep.join([str(source), *(str(installation_path / part) for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream'))]),
        'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run([sys.executable, '-B', '-P', '-c', program, digest], cwd=tmp_path,
        env=environment, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    checked = json.loads(result.stdout)
    assert checked['ordinary_business_boundary'] == checked['source_launcher_reaped'] == 1
    assert checked['workload_popen'] == 0 and checked['binding'] == native['experiment']['binding']
    assert intent_path.read_bytes() == original_intent and native_path.read_bytes() == original_native
    assert not (runtime / 'ergora/training-submissions/alpha.budget').exists()
    assert not (runtime / 'training/jobs/alpha/managed-execution').exists()
    assert not (state.root / 'training-cycles').exists()
