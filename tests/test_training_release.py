"""Owner receipt, signal delivery and actual authorization remain separate facts."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

import ergora.training.native as training_native
import ergora.runtime.processes as processes
import importlib
import ergora.training.application as training
from test_training_evidence import archive
from test_training import experiments, registration
from test_training_runtime import installation
from test_training_submission import prepared, synthetic_execution


def test_historical_owner_decision_is_read_only_without_current_release_authority(prepared, monkeypatch):
    from ergora.training.cycles import _sha

    state, _, runtime, prefix, write, _ = prepared
    manifest_path = runtime / 'training/manifests/alpha.json'
    manifest = json.loads(manifest_path.read_bytes())
    manifest.pop('execution')
    manifest_sha = write(manifest_path, manifest)
    write(prefix / 'experiments/alpha/manifest.json', manifest)
    spec_path = runtime / 'training/specs/alpha.json'
    spec = json.loads(spec_path.read_bytes())
    spec['binding']['manifest_sha'] = manifest_sha
    write(spec_path, spec)
    # Construct saved historical records only; this fixture never ran training,
    # granted an owner receipt, or delivered a release signal.
    synthetic_execution(prepared)
    start = json.loads((runtime / 'ergora/training-submissions/alpha.intent.json').read_bytes())
    intent = {key: start[key] for key in ('schema_version', 'control_home', 'project', 'repo', 'execution',
                                        'registration_sha256', 'experiment_id', 'workflow_id')}
    intent.update(operation='approve', project_revision=start['project_revision'], submission_sha256=_sha(start),
                  run_id='historical-run', evidence_sha256='a' * 64, actor_id='unix:999:historical-actor',
                  operation_id='1' * 32, files={})
    approval_prefix = runtime / 'ergora/training-approvals/alpha'
    intent_path = Path(str(approval_prefix) + '.intent.json')
    write(intent_path, intent)
    before = {path: path.read_bytes() for path in runtime.rglob('*') if path.is_file()}
    original = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    observed = training.approval(state, 'demo', 'alpha')
    assert observed['status'] == 'prepared' and observed['intent_sha256'] == _sha(intent)
    assert observed['run_id'] == 'historical-run' and observed['evidence_sha256'] == intent['evidence_sha256']
    assert observed['release_requested'] is False and observed['authorization_status'] == 'not_evaluated'
    monkeypatch.setattr(importlib.util, 'find_spec', original)
    if sys.platform == 'linux':
        operations = ['prepare', 'prepare-resume']
        if original('temporalio') is not None:
            operations += ['dispatch', 'resume']
        for operation in operations:
            with pytest.raises(ValueError, match='full-verify'):
                training_native.training_release(state.project('demo'), state.root, operation,
                    {'experiment_id': 'alpha', 'run_id': 'historical-run', 'evidence_sha256': intent['evidence_sha256'],
                     'intent_sha256': _sha(intent)}, timeout=20)
    assert {path: path.read_bytes() for path in runtime.rglob('*') if path.is_file()} == before
    try:
        write(intent_path, {**intent, 'run_id': 'another-run'})
        with pytest.raises(ValueError, match='original project, submission or run'):
            training.approval(state, 'demo', 'alpha')
    finally:
        intent_path.write_bytes(before[intent_path])


@pytest.fixture
def submitted_archive(archive, monkeypatch, tmp_path):
    if sys.platform != 'linux':
        pytest.skip('Native owner approval mutations require Linux/WSL2')
    pytest.importorskip('temporalio')
    state, definition, runtime, prefix, write, folder, report = archive
    original = processes.run
    record = tmp_path / 'release-service.json'
    fixtures = Path(__file__).parent / 'fixtures'

    def select(scenario):
        def invoke(argv, *args, **kwargs):
            for module, fixture in [('submission', 'training_submission_client.py'), ('release', 'training_release_client.py')]:
                if f'from ergora.training.runtime.{module} import main;main()' in argv:
                    argv = list(argv)
                    argv[-1] = f'import runpy;runpy.run_path({str(fixtures / fixture)!r},run_name="__main__")'
                    kwargs['env'] = {**kwargs['env'], 'ERGORA_TEST_TRAINING_SUBMISSION': scenario,
                                     'ERGORA_TEST_TRAINING_SERVICE': str(record)}
            return original(argv, *args, **kwargs)
        monkeypatch.setattr(processes, 'run', invoke)
    select('accepted')
    # The same frozen native spec is submitted before exposing its prebuilt
    # synthetic job/gate; no actual job or training ran in this service double.
    job = runtime / 'training/jobs/alpha'
    backup = tmp_path / 'prebuilt-native-job'
    job.rename(backup)
    try:
        started = training.start(state, 'demo', 'alpha', state.project('demo')['revision'],
                                 json.loads((runtime / 'training/specs/alpha.json').read_bytes())['binding']['manifest_sha'])
    finally:
        backup.rename(job)
    return started, select, record


def approve(archive, started, **options):
    state, _, _, _, _, _, report = archive
    return training.approve(state, 'demo', 'alpha', state.project('demo')['revision'],
                             run_id=started['run_id'], evidence_sha256=report['evidence_sha256'], confirm=True, **options)


def recover(archive, intent):
    state = archive[0]
    return training.resume_approve(state, 'demo', 'alpha', state.project('demo')['revision'],
                                    intent['intent_sha256'], confirm=True)


@pytest.mark.skipif(sys.platform != 'linux', reason='Original local release and fence owners require Linux/WSL2')
@pytest.mark.parametrize('ticket_first', [False, True])
def test_local_fence_uses_original_release_lock_without_rolling_back_existing_tickets(archive, ticket_first):
    pytest.importorskip('temporalio')
    state, definition, runtime, _, write, _, _ = archive
    spec = json.loads((runtime / 'training/specs/alpha.json').read_bytes())
    # Preserve a second successful experiment while selecting only alpha.
    beta = json.loads((runtime / 'training/specs/beta.json').read_bytes())['binding']
    gate = json.loads((runtime / 'training/jobs/alpha/gate-report.json').read_bytes())
    gate.update(binding=beta, manifest_sha256=beta['manifest_sha'])
    gate_sha = write(runtime / 'training/jobs/beta/gate-report.json', gate)
    result = json.loads((runtime / 'training/jobs/alpha/result.json').read_bytes())
    result.update(binding=beta, job_id='local-perf-beta',
                  gate={**result['gate'], 'report': str(runtime / 'training/jobs/beta/gate-report.json'), 'report_sha256': gate_sha})
    write(runtime / 'training/jobs/beta/result.json', result)
    before_beta = {p: p.read_bytes() for p in (runtime / 'training/jobs/beta').rglob('*') if p.is_file()}
    installation = Path(definition['execution']['installation'])
    environment = {**os.environ, 'AGENTFLOW_CONFIG_DIR': definition['execution']['config_directory'],
                   'AGENTFLOW_STATE_DIR': str(runtime), 'PYTHONDONTWRITEBYTECODE': '1',
                   'PYTHONPATH': os.pathsep.join(str(installation / name) for name in
                                                ('local', 'upstream/platform', 'upstream/temporal', 'upstream'))}
    command = [sys.executable, '-P', str(Path(__file__).parent / 'fixtures/training_fence_registry.py')]
    if ticket_first:
        created = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=20)
        assert created.returncode == 0, created.stderr
    tickets = runtime / 'training/integration-tickets'
    before = {p: p.read_bytes() for p in tickets.glob('*.json')}
    fenced = training.fence_start(state, 'demo', 'alpha', state.project('demo')['revision'],
                                  spec['binding']['manifest_sha'], confirm=True)
    assert fenced['existing_job']['job_id'] == 'local-perf-alpha' and fenced['executor_stop_confirmed'] is None
    refused = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=20)
    assert refused.returncode != 0 and 'Release suppressed by cancellation fence' in refused.stderr
    assert {p: p.read_bytes() for p in tickets.glob('*.json')} == before
    assert bool(before) == ticket_first
    assert all(p.read_bytes() == raw for p, raw in before_beta.items())
    assert training.inspect(state, 'demo', 'beta')['experiment']['recorded_gate']['passed'] is True
    assert not (runtime / 'training/fences/beta.json').exists()
    unselected = subprocess.run([*command, 'beta'], env=environment, capture_output=True, text=True, timeout=20)
    assert unselected.returncode == 0, unselected.stderr
    assert json.loads(unselected.stdout)['binding'] == beta
    assert {p: p.read_bytes() for p in tickets.glob('alpha-*.json')} == before


def test_original_owner_receipt_and_release_are_once_and_status_is_sdk_free(archive, submitted_archive, monkeypatch):
    state, definition, runtime, _, _, _, _ = archive
    started, _, record = submitted_archive
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    assert training.approval(state, 'demo', 'alpha')['status'] == 'not_recorded'
    result = approve(archive, started)
    assert result['status'] == 'requested' and result['signal_delivery'] == 'acknowledged'
    assert result['authorization_status'] == 'not_evaluated' and result['integration_verified'] is None
    assert approve(archive, started) == recover(archive, result) == result
    assert json.loads(record.read_bytes())['signals'] == 1
    assert all(p.read_bytes() == raw for p, raw in before.items())
    owner = runtime / 'training/approvals' / (result['owner_receipt']['approval_receipt_id'] + '.json')
    assert owner.stat().st_mode & 0o077 == 0
    (runtime / 'training/specs/alpha.json').unlink()
    (Path(definition['execution']['config_directory']) / 'training-runners/trusted.json').unlink()
    owner.unlink()
    original = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    assert training.approval(state, 'demo', 'alpha') == result


@pytest.mark.parametrize('scenario', ['lost-ack', 'timeout-ack'])
def test_uncertain_release_uses_only_complete_original_history_even_after_sources_deleted(archive, submitted_archive, scenario):
    state, definition, runtime, prefix, _, folder, _ = archive
    started, select, record = submitted_archive
    select(scenario)
    with pytest.raises(ValueError, match='UNAVAILABLE|timed out'):
        approve(archive, started, timeout=1)
    unknown = training.approval(state, 'demo', 'alpha')
    assert unknown['status'] == 'unknown' and unknown['release_requested'] is None
    assert approve(archive, started) == unknown
    for absent in ('signal-missing', 'foreign-receipt', 'foreign-evidence'):
        select(absent)
        result = recover(archive, unknown)
        assert result['status'] == 'unknown' and result['reconciliation'] == 'signal_not_found'
    (runtime / 'training/specs/alpha.json').unlink()
    (prefix / 'baseline.json').unlink()
    (Path(definition['execution']['config_directory']) / 'training-runners/trusted.json').unlink()
    shutil.rmtree(folder)
    shutil.rmtree(runtime / 'training/approvals')
    select('accepted')
    restored = recover(archive, unknown)
    assert restored['status'] == 'requested' and restored['signal_delivery'] == 'history'
    assert restored['owner_receipt'] == unknown['owner_receipt'] and restored['run_id'] == started['run_id']
    assert json.loads(record.read_bytes())['signals'] == 1


@pytest.mark.parametrize('scenario,error', [
    ('foreign-memo', 'matching start intent memo'), ('input-collision', 'complete original Experiment differs'),
    ('wrong-run', 'another run ID'), ('status-binding', 'exact evidence currently awaiting release'),
    ('phase-not-ready', 'exact evidence currently awaiting release'), ('evidence-mismatch', 'exact evidence currently awaiting release'),
    ('closed', 'run is closed'), ('not-found', 'run was not found'),
])
def test_foreign_or_nonawaiting_run_never_receives_a_release(archive, submitted_archive, scenario, error):
    state, _, runtime, _, _, _, _ = archive
    started, select, record = submitted_archive
    select(scenario)
    with pytest.raises(ValueError, match=error):
        approve(archive, started)
    assert training.approval(state, 'demo', 'alpha')['status'] == 'prepared'
    assert json.loads(record.read_bytes()).get('signals', 0) == 0
    assert not (runtime / 'training/approvals').exists()


def test_interruption_after_native_receipt_reuses_original_bytes_and_expiry(archive, submitted_archive):
    state, _, runtime, _, _, _, _ = archive
    started, select, record = submitted_archive
    select('after-owner')
    with pytest.raises(ValueError, match='Interrupted after original owner receipt'):
        approve(archive, started)
    prepared = training.approval(state, 'demo', 'alpha')
    assert prepared['status'] == 'prepared' and prepared['owner_receipt'] is None
    owner, = (runtime / 'training/approvals').glob('*.json')
    raw = owner.read_bytes()
    select('accepted')
    restored = recover(archive, prepared)
    assert restored['status'] == 'requested' and owner.read_bytes() == raw
    assert restored['owner_receipt']['expires_at'] == json.loads(raw)['expires_at']
    assert json.loads(record.read_bytes())['signals'] == 1


@pytest.mark.parametrize('scenario', ['before-owner', 'after-owner'])
def test_uncertain_receipt_creation_never_recreates_a_missing_original(archive, submitted_archive, scenario):
    state, _, runtime, _, _, _, _ = archive
    started, select, record = submitted_archive
    select(scenario)
    with pytest.raises(ValueError, match='Interrupted .* original owner receipt publication'):
        approve(archive, started)
    prepared = training.approval(state, 'demo', 'alpha')
    assert prepared['owner_receipt_status'] == 'unknown' and not prepared['attempt_saved']
    for owner in (runtime / 'training/approvals').glob('*.json'):
        owner.unlink()
    select('accepted')
    with pytest.raises(ValueError, match='uncertain or missing; do not mint'):
        recover(archive, prepared)
    assert not list((runtime / 'training/approvals').glob('*.json'))
    assert json.loads(record.read_bytes()).get('signals', 0) == 0
    assert training.approval(state, 'demo', 'alpha') == prepared


@pytest.mark.parametrize('change', ['expired', 'revoked', 'public', 'actor', 'evidence', 'future-expiry', 'raw-bytes'])
def test_native_receipt_is_never_renewed_or_replaced_before_attempt(archive, submitted_archive, change):
    state, _, runtime, _, write, _, _ = archive
    started, select, record = submitted_archive
    select('after-owner')
    with pytest.raises(ValueError, match='Interrupted after original owner receipt'):
        approve(archive, started)
    prepared = training.approval(state, 'demo', 'alpha')
    owner, = (runtime / 'training/approvals').glob('*.json')
    value = json.loads(owner.read_bytes())
    if change == 'public':
        owner.chmod(0o644)
    elif change == 'raw-bytes':
        owner.write_bytes(owner.read_bytes() + b'\n')
    else:
        value.update({'expired': {'expires_at': 1.0}, 'revoked': {'revoked': True},
                      'actor': {'actor_id': 'another-owner'}, 'evidence': {'evidence_sha256': '0' * 64}, 'future-expiry': {'expires_at': value['expires_at'] + 3600.0}}[change])
        write(owner, value)
    before = owner.read_bytes()
    select('accepted')
    with pytest.raises(ValueError, match='privacy, expiry or revocation|differ from the creation attempt'):
        recover(archive, prepared)
    assert owner.read_bytes() == before and json.loads(record.read_bytes()).get('signals', 0) == 0
    assert not (runtime / 'ergora/training-approvals/alpha.attempt.json').exists()


@pytest.mark.parametrize('change', ['baseline', 'fence', 'source'])
def test_first_send_cannot_cross_a_changed_training_source(archive, submitted_archive, change):
    state, _, runtime, prefix, write, folder, _ = archive
    started, select, record = submitted_archive
    select('phase-not-ready')
    with pytest.raises(ValueError, match='exact evidence currently awaiting release'):
        approve(archive, started)
    prepared = training.approval(state, 'demo', 'alpha')
    if change == 'baseline':
        baseline = json.loads((prefix / 'baseline.json').read_bytes())
        write(prefix / 'baseline.json', {**baseline, 'baseline_id': 'changed'})
    elif change == 'fence':
        write(runtime / 'training/fences/alpha.json', {'binding': json.loads((runtime / 'training/specs/alpha.json').read_bytes())['binding']})
    else:
        path = folder / 'evidence.json'
        path.write_bytes(path.read_bytes() + b'\n')
    select('accepted')
    with pytest.raises(ValueError, match='baseline and no fence|content address'):
        recover(archive, prepared)
    assert json.loads(record.read_bytes()).get('signals', 0) == 0


def test_cli_http_confirmations_and_unknown_recovery_share_one_intent(archive, submitted_archive):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.interfaces.cli import main
    from ergora.interfaces.web import create_app

    state = archive[0]
    started, select, record = submitted_archive
    revision = state.project('demo')['revision']
    headers = {'Origin': 'http://127.0.0.1:8977', 'X-Ergora-Request': '1'}
    client = TestClient(create_app(state.root), base_url=headers['Origin'], headers=headers)
    body = {'revision': revision, 'run_id': started['run_id'], 'evidence_sha256': archive[-1]['evidence_sha256'], 'confirm': True}
    assert client.post('/api/projects/demo/training/alpha/approve', json={**body, 'confirm': False}).status_code == 400
    for modified in ({'revision': revision + 1}, {'run_id': 'another-run'}, {'evidence_sha256': '0' * 64}):
        assert client.post('/api/projects/demo/training/alpha/approve', json={**body, **modified}).status_code == 400
    assert training.approval(state, 'demo', 'alpha')['status'] == 'not_recorded'
    select('lost-ack')
    assert client.post('/api/projects/demo/training/alpha/approve', json=body).status_code == 400
    unknown = client.get('/api/projects/demo/training/alpha/approval').json()
    select('signal-missing')
    output = io.StringIO()
    args = ['--home', str(state.root), 'training', 'resume-approve', 'demo', 'alpha', '--revision', str(revision),
            '--intent-sha256', unknown['intent_sha256'], '--confirm']
    with redirect_stdout(output):
        code = main(args)
    assert code == 1 and json.loads(output.getvalue())['status'] == 'unknown'
    select('accepted')
    restored = client.post('/api/projects/demo/training/alpha/resume-approve', json={
        'revision': revision, 'intent_sha256': unknown['intent_sha256'], 'confirm': True})
    assert restored.status_code == 200 and restored.json()['signal_delivery'] == 'history'
    assert json.loads(record.read_bytes())['signals'] == 1


def test_profiled_full_still_requires_the_original_archive_preflight(tmp_path):
    from ergora.training.runtime.release import _Release

    policy = {'protocol': 'training-profile-v1', 'tool': 'cprofile', 'reader': 'cprofile-json-v1',
              'source_operation': 'cpu-diagnostic-v1', 'phases': ['baseline', 'screen'], 'ranks': [0],
              'window': {'unit': 'source_samples', 'work': 6, 'warmup_work': 0}, 'captures': 1,
              'maximum_seconds': 4, 'max_raw_bytes': 65536, 'max_derived_bytes': 8192, 'required': True}
    original = object.__new__(_Release)
    original.payload = {'operation': 'prepare', 'run_id': 'original-run', 'evidence_sha256': 'a' * 64}
    original.run_id = 'original-run'
    original.start = {'observation': {'experiment': {
        'manifest': {'execution': {'operation': 'full-verify', 'profile': policy}},
        'current_runner': {'configuration_readback': {'profile': {
            'protocol': 'training-profile-v1', 'operations': ['cpu-diagnostic-v1']}}}}}}
    original.path = lambda suffix: tmp_path / ('approval' + suffix)
    original.load = lambda: None
    reached = []

    def require_archive():
        reached.append('original-archive-preflight')
        raise ValueError('Original archive/quality/source gate has not passed')

    original.preflight = require_archive
    with pytest.raises(ValueError, match='Original archive/quality/source gate has not passed'):
        original.run()
    assert reached == ['original-archive-preflight']
    assert not list(tmp_path.glob('*.intent.json'))
