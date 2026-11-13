"""A confirmed native preparation retains one intent across partial publication."""

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys

import pytest

from ergora import projects, reference, registrations, training
from ergora.state import State
from test_training import experiments, registration
from test_training_runtime import installation

pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Native experiment preparation requires Linux/WSL2')


@pytest.fixture
def preparation_input(experiments):
    pytest.importorskip('temporalio')
    state, definition, runtime, prefix, _ = experiments
    draft = json.loads((prefix / 'experiments/alpha/manifest.json').read_bytes())
    draft.update(experiment_id='gamma', notes='CPU publication contract only; no training or GPU acceptance')
    return state, definition, runtime, prefix, draft


@pytest.fixture
def stop_after(monkeypatch):
    original = reference.processes.run
    fixture = Path(__file__).parent / 'fixtures/training_preparation_process.py'

    def select(index):
        def invoke(argv, *args, **kwargs):
            if index is not None and argv[-1] == 'from ergora.reference_training_preparation import main;main()':
                argv = [*argv[:-1], f'import runpy;runpy.run_path({str(fixture)!r},run_name="__main__")']
                kwargs['env'] = {**kwargs['env'], 'ERGORA_TEST_PREPARATION_STOP_AFTER': str(index),
                                 'ERGORA_TEST_PREPARATION_ID': 'gamma'}
            return original(argv, *args, **kwargs)
        monkeypatch.setattr(reference.processes, 'run', invoke)
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
    assert result['status'] == 'prepared' and result['intent_sha256'] == preview['preview_sha256']
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
    original_spec = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original_spec(name))
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
    from ergora.cli import main
    from ergora.web import create_app

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
    original = reference.processes.run

    def lose_reply(*args, **kwargs):
        result = original(*args, **kwargs)
        assert result['status'] == 'succeeded'
        raise ValueError('Lost reply after the actual native preparation finished')

    monkeypatch.setattr(reference.processes, 'run', lose_reply)
    result = client.post('/api/projects/demo/training/prepare', json={**body, 'revision': preview['project_revision'],
                                                                    'preview_sha256': preview['preview_sha256']})
    assert result.status_code == 400 and 'Lost reply' in result.text
    monkeypatch.setattr(reference.processes, 'run', original)
    saved = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    observed = client.get('/api/projects/demo/training/gamma/preparation').json()
    assert observed['status'] == 'prepared'
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'resume-prepare', 'demo', 'gamma',
                     '--revision', str(preview['project_revision']), '--intent-sha256', observed['intent_sha256']])
    assert code == 0 and json.loads(output.getvalue())['status'] == 'prepared'
    assert all(path.read_bytes() == raw for path, raw in saved.items())
