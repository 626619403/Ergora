"""An accepted native start is never repeated after a lost acknowledgement."""

from contextlib import redirect_stdout
import io
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest

from ergora import reference, training
from test_training import experiments, registration
from test_training_runtime import installation


@pytest.fixture
def prepared(experiments):
    state, definition, runtime, prefix, write = experiments
    for ident in ('alpha', 'beta'):
        shutil.rmtree(runtime / 'training/jobs' / ident)
    (runtime / 'training/negative-results/alpha.json').unlink()
    manifest = json.loads((runtime / 'training/manifests/alpha.json').read_text())
    manifest['comparison_tool_sha256'] = hashlib.sha256(
        (reference.ROOT / 'platform/upstream/compare_runs.py').read_bytes()).hexdigest()
    digest = write(runtime / 'training/manifests/alpha.json', manifest)
    write(prefix / 'experiments/alpha/manifest.json', manifest)
    spec = json.loads((runtime / 'training/specs/alpha.json').read_text())
    spec['binding']['manifest_sha'] = digest
    write(runtime / 'training/specs/alpha.json', spec)
    return state, definition, runtime, prefix, write, digest


@pytest.fixture
def service(prepared, monkeypatch, tmp_path):
    if sys.platform != 'linux':
        pytest.skip('Native training start uses the registered Linux/WSL2 owner')
    pytest.importorskip('temporalio')
    record = tmp_path / 'service.json'
    original = reference.processes.run
    fixture = Path(__file__).parent / 'fixtures/training_submission_client.py'

    def select(scenario):
        def invoke(argv, *args, **kwargs):
            if 'from ergora.reference_training_submission import main;main()' in argv:
                argv = list(argv)
                argv[-1] = f'import runpy;runpy.run_path({str(fixture)!r},run_name="__main__")'
                kwargs['env'] = {**kwargs['env'], 'ERGORA_TEST_TRAINING_SUBMISSION': scenario,
                                 'ERGORA_TEST_TRAINING_SERVICE': str(record)}
            return original(argv, *args, **kwargs)
        monkeypatch.setattr(reference.processes, 'run', invoke)
    select('accepted')
    return select, record


def test_local_submission_inspection_does_not_require_the_optional_sdk(prepared, monkeypatch):
    state, _, _, _, _, _ = prepared
    original = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    result = training.submission(state, 'demo', 'alpha')
    assert result['status'] == 'not_recorded' and result['runtime_status'] == 'not_queried'


def test_submission_read_racing_with_conflict_publication_keeps_valid_checkpoints(tmp_path):
    from ergora.reference_training_submission import _Submission

    operation = _Submission.__new__(_Submission)
    operation.project = {'id': 'demo', 'revision': 1}
    operation.ident = 'alpha'
    operation.identity = {'workflow_id': 'perf-experiment/alpha'}
    operation.sha = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    binding = {'experiment_id': operation.ident, 'manifest_sha': 'a' * 64}
    intent = {'workflow_id': operation.identity['workflow_id'], 'project_revision': 1, 'operation_id': 'a' * 32,
              'observation': {'experiment': {'experiment_id': operation.ident, 'binding': binding,
                                             'spec': {'binding': binding},
                                             'max_run_seconds': 120, 'current_runner': {}}}}
    saved = {}

    def read(suffix):
        observed = saved.get(suffix)
        if suffix == '.attempt.json':
            # Writer publishes after this read; completion must already have
            # been read, so the reader may lag but cannot invent corruption.
            saved['.attempt.json'] = operation.attempt(intent)
            saved['.rejection.json'] = operation.rejection(intent, 'start_conflict', 'original-run')
        return observed

    operation.optional = read
    assert operation.status(intent)['status'] == 'prepared'
    rejected = operation.status(intent)
    assert rejected['status'] == 'rejected' and rejected['conflicting_run_id'] == 'original-run'

    operation.path = lambda suffix: tmp_path / suffix
    saved.clear()

    def read_intent(suffix):
        observed = saved.get(suffix)
        if suffix == '.intent.json':
            saved[suffix] = intent
            operation.path('.attempt.json').touch()
        return observed

    operation.optional = read_intent
    assert operation.load() == intent


def test_original_client_policies_and_repeated_requests_send_once(prepared, service):
    state, _, runtime, _, _, digest = prepared
    _, record = service
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    revision = state.project('demo')['revision']
    result = training.start(state, 'demo', 'alpha', revision, digest)
    assert result['status'] == 'submitted' and result['run_id']
    assert training.start(state, 'demo', 'alpha', revision, digest) == result
    assert training.resume_start(state, 'demo', 'alpha', revision, result['intent_sha256']) == result
    assert training.submission(state, 'demo', 'alpha') == result
    saved = json.loads(record.read_text())
    assert saved['starts'] == 1 and [c[0] for c in saved['calls']] == ['describe', 'start']
    assert all(p.read_bytes() == value for p, value in before.items())
    assert not (runtime / 'training/jobs/alpha').exists()


def test_valid_large_manifest_can_publish_and_reread_its_aggregate_intent(prepared, service):
    state, _, runtime, prefix, write, _ = prepared
    _, record = service
    path = runtime / 'training/manifests/alpha.json'
    manifest = json.loads(path.read_bytes())
    manifest['notes'] = 'x' * 1_044_000
    digest = write(path, manifest)
    write(prefix / 'experiments/alpha/manifest.json', manifest)
    spec_path = runtime / 'training/specs/alpha.json'
    spec = json.loads(spec_path.read_bytes());spec['binding']['manifest_sha'] = digest
    write(spec_path, spec)
    assert path.stat().st_size < 1_048_576
    result = training.start(state, 'demo', 'alpha', state.project('demo')['revision'], digest)
    assert result['status'] == 'submitted'
    intent = runtime / 'ergora/training-submissions/alpha.intent.json'
    assert intent.stat().st_size > 1_048_576
    assert training.submission(state, 'demo', 'alpha') == result
    assert json.loads(record.read_text())['starts'] == 1


@pytest.mark.parametrize('scenario', ['lost-ack', 'timeout-ack'])
def test_lost_reply_keeps_unknown_then_recovers_only_the_original_run(prepared, service, scenario):
    from ergora.cli import main

    state, definition, runtime, prefix, write, digest = prepared
    select, record = service
    revision = state.project('demo')['revision']
    select(scenario)
    with pytest.raises(ValueError, match='UNAVAILABLE|timed out'):
        training.start(state, 'demo', 'alpha', revision, digest, timeout=1)
    unknown = training.submission(state, 'demo', 'alpha')
    assert unknown['status'] == 'unknown' and unknown['attempt_saved'] and unknown['run_id'] is None
    assert training.start(state, 'demo', 'alpha', revision, digest) == unknown
    select('not-found')
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'resume-start', 'demo', 'alpha',
                     '--revision', str(revision), '--intent-sha256', unknown['intent_sha256']])
    absent = json.loads(output.getvalue())
    assert code == 1
    assert absent['status'] == 'unknown' and absent['reconciliation'] == 'not_found'
    select('unavailable')
    with pytest.raises(ValueError, match='UNAVAILABLE'):
        training.resume_start(state, 'demo', 'alpha', revision, unknown['intent_sha256'])
    # Once attempted, recovery is bound to frozen input, even after a baseline
    # change or runner removal. Neither change is new permission to start.
    baseline = json.loads((prefix / 'baseline.json').read_bytes())
    baseline['config_sha256'] = 'e' * 64
    write(prefix / 'baseline.json', baseline)
    (Path(definition['execution']['config_directory']) / 'training-runners/trusted.json').unlink()
    select('accepted')
    result = training.resume_start(state, 'demo', 'alpha', revision, unknown['intent_sha256'])
    assert result['status'] == 'submitted' and result['run_id'] == '00000000-0000-4000-8000-000000000001'
    assert json.loads(record.read_text())['starts'] == 1


@pytest.mark.parametrize('scenario,error', [
    ('foreign-memo', 'matching intent memo'), ('input-collision', 'complete original Experiment differs'),
    ('missing-history', 'Original training input unavailable'),
])
def test_recovery_cannot_adopt_an_unproven_run(prepared, service, scenario, error):
    state, _, _, _, _, digest = prepared
    select, record = service
    revision = state.project('demo')['revision']
    select('lost-ack')
    with pytest.raises(ValueError, match='UNAVAILABLE'):
        training.start(state, 'demo', 'alpha', revision, digest)
    unknown = training.submission(state, 'demo', 'alpha')
    select(scenario)
    with pytest.raises(ValueError, match=error):
        training.resume_start(state, 'demo', 'alpha', revision, unknown['intent_sha256'])
    assert training.submission(state, 'demo', 'alpha') == unknown
    assert json.loads(record.read_text())['starts'] == 1


@pytest.mark.parametrize('scenario,attempts', [('preexisting', 0), ('race', 1)])
def test_other_actor_start_is_rejected_without_adoption(prepared, service, scenario, attempts):
    from ergora.cli import main

    state, _, _, _, _, digest = prepared
    select, record = service
    select(scenario)
    revision = state.project('demo')['revision']
    if scenario == 'preexisting':
        with pytest.raises(ValueError, match='already exists'):
            training.start(state, 'demo', 'alpha', revision, digest)
    else:
        training.start(state, 'demo', 'alpha', revision, digest)
    result = training.submission(state, 'demo', 'alpha')
    assert result['status'] == 'rejected' and result['run_id'] is None
    assert training.start(state, 'demo', 'alpha', revision, digest) == result
    assert training.resume_start(state, 'demo', 'alpha', revision, result['intent_sha256']) == result
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'start', 'demo', 'alpha',
                     '--revision', str(revision), '--manifest-sha256', digest])
    assert code == 1 and json.loads(output.getvalue()) == result
    assert json.loads(record.read_text())['starts'] == attempts


def test_stale_confirmation_and_changed_sources_cannot_dispatch(prepared, service):
    state, definition, _, _, write, digest = prepared
    select, record = service
    revision = state.project('demo')['revision']
    with pytest.raises(ValueError, match='revision changed'):
        training.start(state, 'demo', 'alpha', revision + 1, digest)
    with pytest.raises(ValueError, match='exact original manifest SHA'):
        training.start(state, 'demo', 'alpha', revision, '0' * 64)
    assert training.submission(state, 'demo', 'alpha')['status'] == 'not_recorded'
    select('unavailable')
    with pytest.raises(ValueError, match='UNAVAILABLE'):
        training.start(state, 'demo', 'alpha', revision, digest)
    saved = training.submission(state, 'demo', 'alpha')
    assert saved['status'] == 'prepared' and not saved['attempt_saved']
    runner = Path(definition['execution']['config_directory']) / 'training-runners/trusted.json'
    value = json.loads(runner.read_bytes());value['command'] += ['another-argument']
    write(runner, value)
    select('accepted')
    with pytest.raises(ValueError, match='sources changed'):
        training.resume_start(state, 'demo', 'alpha', revision, saved['intent_sha256'])
    assert json.loads(record.read_text())['starts'] == 0


def test_cli_and_http_share_exact_start_and_recovery_contract(prepared, service):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.cli import main
    from ergora.web import create_app

    state, _, _, _, _, digest = prepared
    select, record = service
    revision = state.project('demo')['revision']
    headers = {'Origin': 'http://127.0.0.1:8977', 'X-Ergora-Request': '1'}
    client = TestClient(create_app(state.root), base_url=headers['Origin'], headers=headers)
    select('lost-ack')
    failed = client.post('/api/projects/demo/training/alpha/start', json={'revision': revision, 'manifest_sha256': digest})
    assert failed.status_code == 400
    unknown = client.get('/api/projects/demo/training/alpha/submission').json()
    assert unknown['status'] == 'unknown'
    select('accepted')
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'resume-start', 'demo', 'alpha',
                     '--revision', str(revision), '--intent-sha256', unknown['intent_sha256']])
    result = json.loads(output.getvalue())
    assert code == 0 and result['status'] == 'submitted'
    assert client.get('/api/projects/demo/training/alpha/submission').json() == result
    assert client.post('/api/projects/demo/training/alpha/start', json={'revision': revision, 'manifest_sha256': digest}).json() == result
    assert json.loads(record.read_text())['starts'] == 1
