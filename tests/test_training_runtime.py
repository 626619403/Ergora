"""Explicit native facts stay separate from saved training records and adoption."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil

import pytest

from ergora import reference, training
from test_training import experiments, registration


@pytest.fixture(scope='module')
def installation(tmp_path_factory):
    root = tmp_path_factory.mktemp('training-reference-installation')
    shutil.copytree(reference.ROOT / 'platform', root, dirs_exist_ok=True)
    return root


@pytest.fixture
def runtime_client(monkeypatch):
    pytest.importorskip('temporalio')
    original = reference.processes.run
    fixture = Path(__file__).parent / 'fixtures/training_runtime_client.py'

    def select(scenario):
        def invoke(argv, *args, **kwargs):
            if 'from ergora.reference_training_runtime import main;main()' in argv:
                argv = list(argv)
                argv[-1] = f'import runpy;runpy.run_path({str(fixture)!r},run_name="__main__")'
                kwargs['env'] = {**kwargs['env'], 'ERGORA_TEST_TRAINING_RUNTIME': scenario}
            return original(argv, *args, **kwargs)
        monkeypatch.setattr(reference.processes, 'run', invoke)
    return select


@pytest.mark.parametrize('scenario,phase,terminal', [
    ('running', 'AWAITING_RELEASE', False), ('gate-failed', 'GATE_FAILED', True),
    ('cancel-unconfirmed', 'CANCEL_UNCONFIRMED', True), ('integrated', 'INTEGRATION_TASK_CREATED', True),
    ('terminated', 'NEEDS_RECONCILIATION', True),
])
def test_native_domain_facts_are_run_pinned_without_mutating_the_registry(experiments, runtime_client, scenario, phase, terminal):
    state, definition, runtime, _, _ = experiments
    before = {p: p.read_bytes() for root in (runtime, Path(definition['execution']['config_directory']))
              for p in root.rglob('*') if p.is_file()}
    project = state.project('demo')
    runtime_client(scenario)
    observed = training.status(state, 'demo', 'alpha', run_id='original-run', timeout=5)
    assert observed['runtime_status'] == 'queried' and observed['phase'] == phase and observed['terminal'] is terminal
    assert observed['workflow_id'] == 'perf-experiment/alpha' and observed['run_id'] == 'original-run'
    assert observed['binding'] == json.loads((runtime / 'training/specs/alpha.json').read_bytes())['binding']
    assert state.project('demo') == project
    assert all(p.read_bytes() == value for p, value in before.items())
    offline = training.inspect(state, 'demo', 'alpha')
    assert offline['runtime_status'] == 'not_queried' and offline['experiment']['recorded_gate']['passed'] is False


def test_runtime_absence_is_distinct_from_a_connection_failure(experiments, runtime_client):
    state, _, _, _, _ = experiments
    runtime_client('not-found')
    result = training.status(state, 'demo', 'alpha')
    assert result['runtime_status'] == 'not_found' and result['run_id'] is None
    assert 'phase' not in result and 'terminal' not in result
    runtime_client('unavailable')
    with pytest.raises(ValueError, match='RPC failed: UNAVAILABLE'):
        training.status(state, 'demo', 'alpha')


@pytest.mark.parametrize('scenario,error', [
    ('input-collision', 'complete original Experiment differs'), ('numeric-collision', 'complete original Experiment differs'),
    ('missing-history', 'Original training input unavailable'), ('status-binding', 'status belongs to another binding'),
    ('outcome-binding', 'outcome belongs to another binding'), ('wrong-run', 'another run ID'), ('timeout', 'timed out'),
])
def test_inconsistent_runtime_is_an_error_without_using_saved_success(experiments, runtime_client, scenario, error):
    state, _, _, _, _ = experiments
    runtime_client(scenario)
    with pytest.raises(ValueError, match=error):
        training.status(state, 'demo', 'alpha', run_id='original-run', timeout=1)


def test_query_needs_the_fixed_native_family_and_optional_sdk(experiments, runtime_client, monkeypatch):
    state, definition, _, _, _ = experiments
    runtime_client('running')
    module = Path(definition['execution']['installation']) / 'upstream/temporal/perf_temporal/models.py'
    original_bytes = module.read_bytes()
    module.write_bytes(original_bytes + b'\n# Changed native runtime\n')
    try:
        with pytest.raises(ValueError, match='Unsupported reference runtime identity'):
            training.status(state, 'demo', 'alpha')
    finally:
        module.write_bytes(original_bytes)
    original = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    with pytest.raises(ValueError, match=r'install ergora\[temporal\]'):
        training.status(state, 'demo', 'alpha')


def test_cli_and_http_explicitly_query_the_same_native_run(experiments, runtime_client):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.cli import main
    from ergora.web import create_app

    state, _, _, _, _ = experiments
    runtime_client('running')
    expected = training.status(state, 'demo', 'alpha')
    assert expected['run_id'] == 'training-run-1'
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(['--home', str(state.root), 'training', 'status', 'demo', 'alpha'])
    assert code == 0 and json.loads(stdout.getvalue()) == expected
    client = TestClient(create_app(state.root), base_url='http://127.0.0.1')
    response = client.get('/api/projects/demo/training/alpha/status')
    assert response.status_code == 200 and response.json() == expected
    assert client.get('/api/projects/demo/training/alpha/status', params={'run_id': 'original-run'}).json()['run_id'] == 'original-run'
    runtime_client('unavailable')
    failed = client.get('/api/projects/demo/training/alpha/status')
    assert failed.status_code == 400 and 'UNAVAILABLE' in failed.json()['error']
