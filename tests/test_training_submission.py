"""An accepted native start is never repeated after a lost acknowledgement."""

from contextlib import redirect_stdout
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import io
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from ergora import projects, reference, registrations, training
from test_registrations import original_registration
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

    def select(scenario, *, budget_scenario=''):
        def invoke(argv, *args, **kwargs):
            if 'from ergora.reference_training_submission import main;main()' in argv:
                argv = list(argv)
                argv[-1] = f'import runpy;runpy.run_path({str(fixture)!r},run_name="__main__")'
                kwargs['env'] = {**kwargs['env'], 'ERGORA_TEST_TRAINING_SUBMISSION': scenario,
                                 'ERGORA_TEST_TRAINING_SERVICE': str(record),
                                 'ERGORA_TEST_TRAINING_BUDGET': budget_scenario}
            return original(argv, *args, **kwargs)
        monkeypatch.setattr(reference.processes, 'run', invoke)
    select('accepted')
    return select, record


def move_registration(prepared):
    state, definition, _, _, _, _ = prepared
    previous = state.project('demo')
    selected = original_registration(state, previous)
    changed = deepcopy(definition)
    for key in ('config_directory', 'state_directory'):
        changed['execution'][key] += '-new'
    current = registrations.register(state, changed, previous['revision'])
    for name in previous['registration']['files']:
        (Path(definition['execution']['config_directory']) / name).write_text('{"drift": true}')
    return selected, current


def test_original_registration_unknown_start_reconciles_without_resending_or_holding_db(prepared, service, monkeypatch):
    state, definition, runtime, _, _, digest = prepared
    select, record = service
    # Registration, start and current revisions are intentionally all different.
    projects.bind(state, 'demo', 'memory', {'tool': 'sqlite'}, state.project('demo')['revision'])
    start_revision = state.project('demo')['revision']
    select('lost-ack')
    with pytest.raises(ValueError, match='UNAVAILABLE'):
        training.start(state, 'demo', 'alpha', start_revision, digest)
    selected, current = move_registration(prepared)
    (runtime / 'training/specs/alpha.json').unlink()
    (Path(definition['execution']['config_directory']) / 'training-runners/trusted.json').unlink()
    original = reference.training_submission
    rpc_reservations = []

    def unlocked(project, *args, **kwargs):
        if args[1] == 'resume':
            with state.connect() as db:
                db.execute('BEGIN IMMEDIATE')
            rpc_reservations.append(True)
        return original(project, *args, **kwargs)

    monkeypatch.setattr(reference, 'training_submission', unlocked)
    unknown = training.submission(state, 'demo', 'alpha', original_registration=selected)
    assert unknown['status'] == 'unknown' and unknown['submitted_revision'] == start_revision
    context = unknown['original_registration']
    assert context['registration_project_revision'] < start_revision < context['current_project_revision']
    assert unknown['project_revision'] == current['revision']
    assert context['execution'] == definition['execution']
    checkpoints = {p: p.read_bytes() for p in (runtime / 'ergora/training-submissions').glob('*')}
    for scenario, error in [('not-found', None), ('unavailable', 'UNAVAILABLE'), ('foreign-memo', 'matching intent memo'),
                            ('input-collision', 'complete original Experiment differs')]:
        select(scenario)
        if error:
            with pytest.raises(ValueError, match=error):
                training.resume_start(state, 'demo', 'alpha', current['revision'], unknown['intent_sha256'],
                                      original_registration=selected)
        else:
            missing = training.resume_start(state, 'demo', 'alpha', current['revision'], unknown['intent_sha256'],
                                            original_registration=selected)
            assert missing['status'] == 'unknown' and missing['reconciliation'] == 'not_found'
        assert all(p.read_bytes() == raw for p, raw in checkpoints.items())
    select('accepted')
    recovered = training.resume_start(state, 'demo', 'alpha', current['revision'], unknown['intent_sha256'],
                                      original_registration=selected)
    assert recovered['status'] == 'submitted' and recovered['intent_sha256'] == unknown['intent_sha256']
    assert json.loads(record.read_bytes())['starts'] == 1 and len(rpc_reservations) == 5
    assert not Path(current['registration']['definition']['execution']['state_directory']).exists()
    assert state.project('demo') == current


def test_original_prepared_start_is_readable_and_fenceable_but_cannot_dispatch(prepared, monkeypatch, capsys):
    pytest.importorskip('temporalio')
    if sys.platform != 'linux':
        pytest.skip('Native training recovery requires Linux/WSL2')
    from ergora.cli import main

    state, _, runtime, _, _, digest = prepared
    reference.training_submission(state.project('demo'), state.root, 'prepare',
                                  {'experiment_id': 'alpha', 'manifest_sha256': digest}, timeout=20)
    selected, current = move_registration(prepared)
    args = ['--home', str(state.root), 'training', 'submission', 'demo', 'alpha',
            '--original-registration', selected['operation_id'], '--registration-intent-sha256', selected['intent_sha256']]
    assert main(args) == 2
    capsys.readouterr()
    assert main(args + ['--confirm']) == 0
    observed = json.loads(capsys.readouterr().out)
    assert observed['status'] == 'prepared'
    for revision in (current['revision'] - 1, current['revision']):
        with pytest.raises(ValueError, match='revision changed|without its original attempt'):
            training.resume_start(state, 'demo', 'alpha', revision, observed['intent_sha256'], original_registration=selected)
    project = training._project(state, 'demo', selected)
    for operation in ('prepare', 'check', 'dispatch'):
        with pytest.raises(ValueError, match='only original start reconciliation'):
            reference.training_submission(project, state.root, operation,
                {'experiment_id': 'alpha', 'manifest_sha256': digest, 'intent_sha256': observed['intent_sha256']}, timeout=20)
    with pytest.raises(ValueError, match='limited to submission reconciliation'):
        reference.training_release(project, state.root, 'status', {'experiment_id': 'alpha'}, timeout=20)
    with pytest.raises(ValueError, match='existing matching start intent'):
        training.fence_start(state, 'demo', 'beta', current['revision'], digest, confirm=True, original_registration=selected)
    original = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    assert training.submission(state, 'demo', 'alpha', original_registration=selected) == observed
    monkeypatch.setattr(reference.importlib.util, 'find_spec', original)
    fenced = training.fence_start(state, 'demo', 'alpha', current['revision'], digest, confirm=True, original_registration=selected)
    assert fenced['status'] == 'fenced' and fenced['intent_sha256'] == observed['intent_sha256']
    assert not (runtime / 'training/fences/beta.json').exists()
    assert not (runtime / 'ergora/training-submissions/alpha.attempt.json').exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Original training preparation requires Linux/WSL2')
def test_original_registration_is_rechecked_in_the_selected_training_process(prepared, monkeypatch):
    state, _, runtime, _, _, digest = prepared
    reference.training_submission(state.project('demo'), state.root, 'prepare',
                                  {'experiment_id': 'alpha', 'manifest_sha256': digest}, timeout=20)
    selected, _ = move_registration(prepared)
    result = state.root / 'registrations/demo' / (selected['operation_id'] + '.result.json')
    original = reference.processes.run

    def replace(*args, **kwargs):
        value = json.loads(result.read_bytes());value['status'] = 'not-published'
        result.write_text(json.dumps(value))
        return original(*args, **kwargs)

    monkeypatch.setattr(reference.processes, 'run', replace)
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    with pytest.raises(ValueError, match='matching complete published intent'):
        training.submission(state, 'demo', 'alpha', original_registration=selected)
    assert {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()} == before


def test_local_submission_inspection_does_not_require_the_optional_sdk(prepared, monkeypatch):
    state, _, _, _, _, _ = prepared
    original = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    result = training.submission(state, 'demo', 'alpha')
    assert result['status'] == 'not_recorded' and result['runtime_status'] == 'not_queried'


@pytest.mark.skipif(sys.platform != 'linux', reason='Native start preflight requires Linux/WSL2 Git paths')
def test_start_check_is_sdk_free_and_cli_preserves_original_sources(prepared, monkeypatch, capsys):
    from ergora.cli import main

    state, definition, runtime, _, _, digest = prepared
    original = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    config = Path(definition['execution']['config_directory'])
    before = {path: path.read_bytes() for root in (runtime, config) for path in root.rglob('*') if path.is_file()}
    with state.connect() as db:
        database = list(db.iterdump())
    checked = training.check_start(state, 'demo', 'alpha', digest)
    assert checked['ready_for_new_start'] and checked['read_only'] and not checked['execution_authorized']
    assert checked['runtime_status'] == 'not_queried' and checked['submission'] is None
    assert checked['observation']['experiment']['binding']['manifest_sha'] == digest
    assert main(['--home', str(state.root), 'training', 'check-start', 'demo', 'alpha', '--manifest-sha256', digest]) == 0
    assert json.loads(capsys.readouterr().out) == checked
    with pytest.raises(ValueError, match='exact original manifest SHA'):
        training.check_start(state, 'demo', 'alpha', '0' * 64)
    assert {path: path.read_bytes() for root in (runtime, config) for path in root.rglob('*') if path.is_file()} == before
    with state.connect() as db:
        assert list(db.iterdump()) == database


@pytest.mark.skipif(sys.platform != 'linux', reason='Native start preflight requires Linux/WSL2 Git paths')
def test_start_check_uses_original_preflight_and_rejects_project_drift(prepared, monkeypatch):
    state, definition, _, _, write, digest = prepared
    original = reference.training_submission

    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        with state.connect() as db:
            project = json.loads(db.execute("SELECT document FROM projects WHERE id='demo'").fetchone()[0])
            project['revision'] += 1
            db.execute("UPDATE projects SET document=? WHERE id='demo'", (json.dumps(project),))
        return result

    monkeypatch.setattr(reference, 'training_submission', changed)
    with pytest.raises(ValueError, match='Project changed during'):
        training.check_start(state, 'demo', 'alpha', digest)
    monkeypatch.setattr(reference, 'training_submission', original)
    runner = Path(definition['execution']['config_directory']) / 'training-runners/trusted.json'
    value = json.loads(runner.read_bytes());value['timeout_seconds'] = 0
    write(runner, value)
    with pytest.raises(ValueError, match='runner command or execution walltime'):
        training.check_start(state, 'demo', 'alpha', digest)


@pytest.mark.skipif(sys.platform != 'linux', reason='Native local training fences require Linux/WSL2')
def test_local_fence_requires_confirmation_and_preserves_sources_without_loading_credentials(prepared, monkeypatch, capsys):
    pytest.importorskip('temporalio')
    from ergora.cli import main

    state, definition, runtime, _, _, digest = prepared
    revision = state.project('demo')['revision']
    config = Path(definition['execution']['config_directory'])
    credentials = config / 'credentials.json'
    credentials.write_text('This local operation must not load credentials', encoding='utf-8')
    before = {p: p.read_bytes() for root in (runtime, config) for p in root.rglob('*') if p.is_file()}
    with state.connect() as db:
        database = list(db.iterdump())
    for expected, sha, confirm in ((revision, digest, False), (revision + 1, digest, True), (revision, '0' * 64, True)):
        with pytest.raises(ValueError):
            training.fence_start(state, 'demo', 'alpha', expected, sha, confirm=confirm)
    original = reference.importlib.util.find_spec
    with monkeypatch.context() as missing:
        missing.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
        with pytest.raises(ValueError, match='optional Temporal SDK'):
            training.fence_start(state, 'demo', 'alpha', revision, digest, confirm=True)
    fence = runtime / 'training/fences/alpha.json'
    assert not fence.exists()
    args = ['--home', str(state.root), 'training', 'fence-start', 'demo', 'alpha',
            '--revision', str(revision), '--manifest-sha256', digest, '--confirm']
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'fenced' and result['submission_status_observed'] == 'not_recorded'
    assert result['existing_job'] is None and result['intent_sha256'] is None
    assert result['executor_stop_confirmed'] is None and result['execution_success'] is None
    assert result['runtime_status'] == 'not_queried'
    assert result['fence'] == {'path': str(fence), 'sha256': hashlib.sha256(fence.read_bytes()).hexdigest()}
    assert training.fence_start(state, 'demo', 'alpha', revision, digest, confirm=True) == result
    assert all(p.read_bytes() == raw for p, raw in before.items())
    assert not (runtime / 'ergora/training-submissions/alpha.intent.json').exists()
    with state.connect() as db:
        assert list(db.iterdump()) == database
    with pytest.raises(ValueError, match='fence records already exist'):
        training.check_start(state, 'demo', 'alpha', digest)


@pytest.mark.parametrize('status', ['prepared', 'unknown'])
def test_local_fence_uses_frozen_start_and_never_reconciles_or_resends(prepared, service, status):
    state, definition, runtime, _, _, digest = prepared
    select, record = service
    if status == 'prepared':
        reference.training_submission(state.project('demo'), state.root, 'prepare',
            {'experiment_id': 'alpha', 'manifest_sha256': digest}, timeout=20)
    else:
        select('lost-ack')
        with pytest.raises(ValueError, match='UNAVAILABLE'):
            training.start(state, 'demo', 'alpha', state.project('demo')['revision'], digest)
    before = training.submission(state, 'demo', 'alpha')
    calls = record.read_bytes() if record.exists() else None
    (runtime / 'training/specs/alpha.json').unlink()
    (Path(definition['execution']['config_directory']) / 'training-runners/trusted.json').unlink()
    checkpoints = {p: p.read_bytes() for p in (runtime / 'ergora/training-submissions').glob('*')}
    result = training.fence_start(state, 'demo', 'alpha', state.project('demo')['revision'], digest, confirm=True)
    assert result['submission_status_observed'] == status and result['intent_sha256'] == before['intent_sha256']
    assert result['binding'] == before['confirmation']['binding']
    assert result['existing_job'] is None and result['executor_stop_confirmed'] is None
    assert training.submission(state, 'demo', 'alpha') == before
    assert all(p.read_bytes() == raw for p, raw in checkpoints.items())
    assert (record.read_bytes() if record.exists() else None) == calls


@pytest.mark.parametrize('scenario', ['accepted', 'preexisting'])
def test_local_fence_refuses_an_observed_completed_submission_without_an_existing_fence(prepared, service, scenario):
    state, _, runtime, _, _, digest = prepared
    select, record = service
    select(scenario)
    if scenario == 'preexisting':
        with pytest.raises(ValueError, match='already exists'):
            training.start(state, 'demo', 'alpha', state.project('demo')['revision'], digest)
    else:
        training.start(state, 'demo', 'alpha', state.project('demo')['revision'], digest)
    calls = record.read_bytes()
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    with pytest.raises(ValueError, match='already submitted or rejected'):
        training.fence_start(state, 'demo', 'alpha', state.project('demo')['revision'], digest, confirm=True)
    assert {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()} == before
    assert record.read_bytes() == calls


@pytest.mark.parametrize('scenario,terminal', [('fence-observed-receipt', 'submitted'), ('fence-observed-rejection', 'rejected')])
def test_local_fence_reports_status_snapshot_when_a_writer_completes_after_the_read(prepared, service, scenario, terminal):
    state, _, runtime, _, _, digest = prepared
    select, record = service
    select(scenario)
    reference.training_submission(state.project('demo'), state.root, 'prepare',
        {'experiment_id': 'alpha', 'manifest_sha256': digest}, timeout=20)
    revision = state.project('demo')['revision']
    first = training.fence_start(state, 'demo', 'alpha', revision, digest, confirm=True)
    assert first['submission_status_observed'] == 'prepared'
    assert training.submission(state, 'demo', 'alpha')['status'] == terminal
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    repeated = training.fence_start(state, 'demo', 'alpha', revision, digest, confirm=True)
    assert repeated == {**first, 'submission_status_observed': terminal}
    assert {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()} == before
    saved = json.loads(record.read_bytes())
    assert saved['completion_published_after_status'] and saved['starts'] == 0 and saved['calls'] == []


@pytest.mark.parametrize('existing', [False, True])
def test_local_fence_does_not_wait_for_inflight_start_and_preserves_native_registry_order(prepared, service, monkeypatch, existing):
    state, _, runtime, _, _, digest = prepared
    select, record = service
    select('held-start-existing' if existing else 'held-start')
    original = reference.processes.run
    lost_reply = []

    def invoke(argv, *args, **kwargs):
        result = original(argv, *args, **kwargs)
        if existing and not lost_reply and json.loads(kwargs.get('stdin', '{}')).get('operation') == 'fence':
            lost_reply.append(True)
            raise ValueError('Simulated loss of the completed local fence reply')
        return result

    monkeypatch.setattr(reference.processes, 'run', invoke)
    revision = state.project('demo')['revision']
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(training.start, state, 'demo', 'alpha', revision, digest)
        try:
            until = time.monotonic() + 10
            while not record.with_suffix('.held').exists() and not future.done() and time.monotonic() < until:
                time.sleep(0.01)
            assert record.with_suffix('.held').exists(), 'Original SDK start never reached its held RPC'
            checkpoints = {p: p.read_bytes() for p in (runtime / 'ergora/training-submissions').glob('*')}
            if existing:
                with pytest.raises(ValueError, match='loss of the completed local fence reply'):
                    training.fence_start(state, 'demo', 'alpha', revision, digest, confirm=True)
            else:
                fenced = training.fence_start(state, 'demo', 'alpha', revision, digest, confirm=True)
                assert fenced['submission_status_observed'] == 'unknown' and fenced['existing_job'] is None
            assert not future.done() and all(p.read_bytes() == raw for p, raw in checkpoints.items())
            fence = (runtime / 'training/fences/alpha.json').read_bytes()
        finally:
            record.with_suffix('.continue').touch()
        completed = future.result(timeout=30)
    assert completed['status'] == 'submitted'
    confirmed = training.fence_start(state, 'demo', 'alpha', revision, digest, confirm=True)
    assert confirmed['submission_status_observed'] == 'submitted'
    assert confirmed['executor_stop_confirmed'] is confirmed['execution_success'] is None
    assert confirmed['runtime_status'] == 'not_queried'
    assert (runtime / 'training/fences/alpha.json').read_bytes() == fence
    saved = json.loads(record.read_bytes())
    assert saved['starts'] == 1 and [call[0] for call in saved['calls']] == ['describe', 'start']
    if existing:
        assert confirmed['existing_job'] == saved['native_job_before'] == saved['native_lookup_after']
        assert lost_reply
    else:
        assert saved['native_lookup_after'] is None and not (runtime / 'training/jobs/alpha/request.json').exists()
    assert 'fenced against further submission' in saved['native_create_error']


@pytest.mark.skipif(sys.platform != 'linux', reason='Native local training fences require Linux/WSL2')
@pytest.mark.parametrize('mutation', ['lock-symlink', 'job-symlink', 'fence-symlink', 'job-experiment', 'job-id', 'fence-binding', 'registration'])
def test_frozen_fence_rejects_unsafe_paths_and_original_identity_conflicts(prepared, tmp_path, mutation):
    pytest.importorskip('temporalio')
    state, definition, runtime, _, write, digest = prepared
    reference.training_submission(state.project('demo'), state.root, 'prepare',
        {'experiment_id': 'alpha', 'manifest_sha256': digest}, timeout=20)
    if mutation.endswith('symlink'):
        relative = {'lock-symlink': 'training/registry.lock', 'job-symlink': 'training/jobs/alpha/request.json',
                    'fence-symlink': 'training/fences/alpha.json'}[mutation]
        outside = tmp_path / 'outside-record'
        outside.write_text('External file must remain unchanged')
        path = runtime / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(outside)
    elif mutation in ('job-experiment', 'job-id'):
        spec = json.loads((runtime / 'training/specs/alpha.json').read_bytes())
        if mutation == 'job-experiment':
            spec['poll_seconds'] += 1
        write(runtime / 'training/jobs/alpha/request.json', {'schema_version': 1, 'experiment': spec,
                                                           'job_id': None if mutation == 'job-id' else 'local-perf-alpha'})
    elif mutation == 'fence-binding':
        binding = json.loads((runtime / 'training/specs/alpha.json').read_bytes())['binding']
        write(runtime / 'training/fences/alpha.json', {'binding': {**binding, 'manifest_sha': '0' * 64}})
    else:
        registered_path, registered = next(iter(state.project('demo')['registration']['files'].items()))
        write(Path(definition['execution']['config_directory']) / registered_path, {**registered, 'drift': True})
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    if mutation == 'job-experiment':
        # The original native lock is created before lookup rejects a reused ID.
        before[runtime / 'training/registry.lock'] = b''
    with pytest.raises(ValueError):
        training.fence_start(state, 'demo', 'alpha', state.project('demo')['revision'], digest, confirm=True)
    assert {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()} == before
    if mutation.endswith('symlink'):
        assert outside.read_text() == 'External file must remain unchanged'
    elif mutation != 'fence-binding':
        assert not (runtime / 'training/fences/alpha.json').exists()


@pytest.fixture
def cycle_selection(prepared):
    state, definition, runtime, prefix, write, digest = prepared
    manifest = json.loads((runtime / 'training/manifests/beta.json').read_bytes())
    manifest.update(comparison_tool_sha256=hashlib.sha256(
        (reference.ROOT / 'platform/upstream/compare_runs.py').read_bytes()).hexdigest(),
        track='N', allowed_changes=['Different declared intervention'], candidate_config_sha256='d' * 64)
    second = write(runtime / 'training/manifests/beta.json', manifest)
    write(prefix / 'experiments/beta/manifest.json', manifest)
    spec = json.loads((runtime / 'training/specs/beta.json').read_bytes())
    spec['binding']['manifest_sha'] = second
    write(runtime / 'training/specs/beta.json', spec)
    request = {'schema_version': 1, 'budget': {'wall_seconds': 900, 'cleanup_seconds': 170, 'control_timeout_seconds': 7},
               'candidates': [{'experiment_id': name, 'manifest_sha256': sha,
                               'change': 'Synthetic ' + name, 'next_bottleneck': 'Unmeasured; no speedup claim'}
                              for name, sha in [('alpha', digest), ('beta', second)]]}
    return state, definition, runtime, prefix, write, request


def native_budget_create(definition, experiment_id, *, managed):
    installation = Path(definition['execution']['installation'])
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=definition['execution']['config_directory'],
                       AGENTFLOW_STATE_DIR=definition['execution']['state_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (Path(reference.__file__).parent.parent,
        installation / 'local', installation / 'upstream/platform', installation / 'upstream/temporal', installation / 'upstream')))
    program = '''import asyncio,sys
from perf_temporal.client import load_experiment
from agent_platform.core import STATE
from importlib import import_module
async def run():
    experiment=load_experiment(str(STATE/'training/specs'/ (sys.argv[1]+'.json')))
    adapter=import_module(sys.argv[2]).create_adapter()
    manifest=await adapter.read_manifest(experiment.manifest_uri)
    await adapter.create_job_if_absent(experiment,manifest)
asyncio.run(run())
'''
    return subprocess.run([sys.executable, '-P', '-c', program, experiment_id,
        'ergora.reference_training_worker' if managed else 'agent_platform.training'], env=environment,
        capture_output=True, text=True, timeout=10)


def wait_budget_stopped(runtime, seconds=15):
    from ergora.reference_training_budget import _process_identity
    from ergora.state import file_lock

    folder = runtime / 'ergora/training-submissions/alpha.budget'
    owner = json.loads((folder / 'owner.json').read_bytes())
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        try:
            stopped = _process_identity(owner['pid']) != {key: owner[key] for key in ('pid', 'start_ticks', 'boot_id')}
        except (OSError, ValueError):
            stopped = True
        if stopped:
            try:
                with file_lock(folder / 'lock', blocking=False):
                    return folder
            except BlockingIOError:
                pass
        time.sleep(.05)
    import signal
    os.kill(owner['pid'], signal.SIGKILL)
    raise AssertionError('Original budget owner did not finish its bounded supervision')


def wait_budget_final(runtime, seconds=15):
    return json.loads((wait_budget_stopped(runtime, seconds) / 'final.json').read_bytes())


def authorize_budget(selection, tmp_path, *, wall=14, cleanup=4, timeout=4):
    from ergora import training_cycles

    state, definition, runtime, _, _, request = selection
    request['budget'].update(wall_seconds=wall, cleanup_seconds=cleanup, control_timeout_seconds=timeout)
    source = tmp_path / 'finite-input'
    selected = training_cycles.create(state, 'demo', request, source)
    authorized = training_cycles.authorize(state, 'demo', 'budget', source, selected['sha256'], 1, confirm=True)
    assert authorized['status'] == 'ready'
    return state, definition, runtime, authorized


@pytest.mark.parametrize('fault', ['final-file-blocked', 'final-directory-blocked'])
def test_cycle_final_publication_is_bounded_and_dead_owner_recovers_only_the_same_fence(cycle_selection, service, tmp_path, fault):
    from ergora import training_cycles

    service[0]('accepted', budget_scenario=fault)
    # Retain the same compute window, with room to reach the injected final
    # publication fault after fence and control cleanup.
    state, _, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=24, cleanup=14)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    prefix = runtime / 'ergora/training-submissions'
    # A fast submission can return before the full cleanup allowance elapses.
    # Wait through the selected authorization, then allow process reaping.
    wait_budget_stopped(runtime, seconds=authorized['total_remaining_seconds'] + 5)
    assert service[1].with_suffix('.final-blocked').read_text() == fault
    original = {p: p.read_bytes() for p in prefix.rglob('*') if p.is_file()}
    fence = runtime / 'training/fences/alpha.json'
    raw = fence.read_bytes()
    observed = training.submission(state, 'demo', 'alpha')
    assert observed['budget']['owner_status'] == ('unknown' if fault == 'final-file-blocked' else 'fenced')
    assert observed['budget']['local_fence']['sha256'] == hashlib.sha256(raw).hexdigest()
    assert observed['budget']['executor_stop_confirmed'] is None
    assert all(p.read_bytes() == content for p, content in original.items()) and fence.read_bytes() == raw
    assert training.resume_start(state, 'demo', 'alpha', 1, submitted['intent_sha256'])['status'] == 'submitted'
    assert json.loads(service[1].read_bytes())['starts'] == 1


def test_cycle_start_returns_before_automatic_fence_blocks_a_late_native_create(cycle_selection, service, tmp_path):
    from ergora import training_cycles
    from temporalio.api.workflowservice.v1 import StartWorkflowExecutionRequest
    import base64

    state, definition, runtime, _, _, request = cycle_selection
    request['budget'].update(wall_seconds=12, cleanup_seconds=3, control_timeout_seconds=4)
    source = tmp_path / 'finite-input'
    selected = training_cycles.create(state, 'demo', request, source)
    authorized = training_cycles.authorize(state, 'demo', 'budget', source, selected['sha256'], 1, confirm=True)
    assert authorized['status'] == 'ready'
    before = {p: p.read_bytes() for p in (state.root / 'training-cycles/demo/budget').iterdir()}
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    assert submitted['status'] == 'submitted' and submitted['budget']['owner_status'] == 'active'
    assert not (runtime / 'training/fences/alpha.json').exists()
    record = json.loads(service[1].read_bytes())
    encoded = StartWorkflowExecutionRequest.FromString(base64.b64decode(record['request']))
    assert encoded.task_queue.name == 'ergora-training-budget-v1'
    prefix = runtime / 'ergora/training-submissions'
    intent = json.loads((prefix / 'alpha.intent.json').read_bytes())
    assert intent['budget']['authorization_sha256'] == authorized['authorization_sha256']
    attempt = (prefix / 'alpha.attempt.json').read_bytes()
    wait_budget_stopped(runtime)
    observed = training.submission(state, 'demo', 'alpha')['budget']
    assert observed['local_fence'] and observed['executor_stop_confirmed'] is None
    late = native_budget_create(definition, 'alpha', managed=False)
    assert late.returncode != 0 and 'fenced against further submission' in late.stderr
    assert not (runtime / 'training/jobs/alpha/request.json').exists()
    assert (prefix / 'alpha.attempt.json').read_bytes() == attempt
    assert all(p.read_bytes() == raw for p, raw in before.items())
    assert json.loads(service[1].read_bytes())['starts'] == 1


def test_cycle_held_start_does_not_hold_the_deadline_owner_or_its_native_fence(cycle_selection, service, tmp_path):
    from ergora import training_cycles

    state, _, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=18, cleanup=6, timeout=20)
    select, record = service
    select('held-start')
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(training_cycles.start, state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
        try:
            until = time.monotonic() + 10
            while not record.with_suffix('.held').exists() and time.monotonic() < until:
                time.sleep(.02)
            assert record.with_suffix('.held').exists()
            wait_budget_stopped(runtime)
            assert (runtime / 'training/fences/alpha.json').exists() and not future.done()
        finally:
            record.with_suffix('.continue').touch()
        assert future.result(timeout=10)['status'] == 'submitted'
    observed = json.loads(record.read_bytes())
    assert 'fenced against further submission' in observed['native_create_error']
    assert observed['native_lookup_after'] is None and observed['starts'] == 1
    assert not (runtime / 'training/jobs/alpha/request.json').exists()


def test_cycle_managed_create_requires_its_live_owner_and_preserves_single_start_slot(cycle_selection, service, tmp_path):
    from ergora import training_cycles

    state, definition, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=24, cleanup=5)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    created = native_budget_create(definition, 'alpha', managed=True)
    assert created.returncode == 0, created.stderr
    prefix = runtime / 'ergora/training-submissions'
    original = {name: (prefix / ('alpha.' + name + '.json')).read_bytes() for name in ('intent', 'attempt', 'result')}
    try:
        assert training.start(state, 'demo', 'alpha', 1, submitted['manifest_sha256'])['status'] == 'submitted'
        assert training.resume_start(state, 'demo', 'alpha', 1, submitted['intent_sha256'])['status'] == 'submitted'
        # A second cycle cannot take ownership of the original immutable intent.
        with pytest.raises(ValueError, match='cannot switch or adopt'):
            training.start(state, 'demo', 'alpha', 1, submitted['manifest_sha256'],
                budget={'cycle_id': 'another', 'authorization_sha256': authorized['authorization_sha256']})
    finally:
        import signal
        owner = json.loads((prefix / 'alpha.budget/owner.json').read_bytes())
        os.kill(owner['pid'], signal.SIGTERM)
        wait_budget_stopped(runtime)
    assert all((prefix / ('alpha.' + name + '.json')).read_bytes() == raw for name, raw in original.items())
    assert json.loads(service[1].read_bytes())['starts'] == 1


def test_cycle_owner_death_blocks_managed_create_without_restarting_or_new_attempt(cycle_selection, service, tmp_path):
    from ergora import training_cycles
    import signal

    state, definition, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=30, cleanup=5)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    prefix = runtime / 'ergora/training-submissions'
    original = {p: p.read_bytes() for p in prefix.glob('alpha.*.json')}
    owner_path = prefix / 'alpha.budget/owner.json'
    owner_bytes = owner_path.read_bytes()
    owner = json.loads(owner_bytes)
    os.kill(owner['pid'], signal.SIGKILL)
    until = time.monotonic() + 5
    from ergora.reference_training_budget import _process_identity
    while time.monotonic() < until:
        try:
            _process_identity(owner['pid'])
        except (OSError, ValueError):
            break
        time.sleep(.02)
    assert not (runtime / 'training/fences/alpha.json').exists()
    denied = native_budget_create(definition, 'alpha', managed=True)
    assert denied.returncode != 0 and 'owner is unconfirmed' in denied.stderr
    observed = training.resume_start(state, 'demo', 'alpha', 1, submitted['intent_sha256'])
    assert observed['budget']['owner_status'] == 'unknown'
    assert not (runtime / 'training/jobs/alpha/request.json').exists()
    assert owner_path.read_bytes() == owner_bytes and all(p.read_bytes() == raw for p, raw in original.items())
    assert json.loads(service[1].read_bytes())['starts'] == 1


def test_cycle_completed_native_success_keeps_its_evidence_and_manual_release_unfenced(cycle_selection, service, tmp_path):
    from ergora import training_cycles

    state, definition, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=24, cleanup=5)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    created = native_budget_create(definition, 'alpha', managed=True)
    assert created.returncode == 0, created.stderr
    write = cycle_selection[4]
    job = runtime / 'training/jobs/alpha'
    request = json.loads((job / 'request.json').read_bytes())
    detail = 'Synthetic completed CPU contract'
    native_job = {'binding': request['experiment']['binding'], 'job_id': request['job_id']}
    prior = {'schema_version': 1, 'intent_sha256': submitted['intent_sha256'],
        'authorization_sha256': authorized['authorization_sha256'], 'status': 'completed',
        'native': {'job': native_job, 'state': 'SUCCEEDED', 'detail': detail},
        'gate': {'job': native_job, 'passed': True, 'evidence_sha': 'd' * 64,
                 'report_uri': (job / 'gate-report.json').as_uri(), 'summary': ''},
        'recorded_at': '2000-01-01T00:00:00.000000+00:00', 'total_remaining_seconds': 0.0,
        'executor_stop_confirmed': None}
    # Fill the original final envelope, leaving room for its variable timestamp
    # and remaining time, but less than the new phase observation overhead.
    prior_bytes = len((json.dumps(prior, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8'))
    summary = 'A' * (training_cycles.MAX_RECORD_BYTES - prior_bytes - 128) + '训练✓'
    gate = {'binding': request['experiment']['binding'], 'manifest_sha256': submitted['manifest_sha256'],
            'passed': True, 'evidence_sha256': 'd' * 64, 'summary': summary}
    digest = write(job / 'gate-report.json', gate)
    write(job / 'result.json', {'binding': gate['binding'], 'job_id': request['job_id'],
        'state': 'SUCCEEDED', 'detail': detail, 'gate': {'report': str(job / 'gate-report.json'),
        'report_sha256': digest, 'mlflow_run_id': 'synthetic-no-training'}})
    originals = {p: p.read_bytes() for p in job.iterdir()}
    folder = wait_budget_stopped(runtime)
    diagnostic = json.loads(next((folder / 'launches').glob('*/stdout.json')).read_bytes())
    prior = {key: value for key, value in diagnostic.items() if key not in ('phases', 'overrun_seconds', 'publication')}
    current = {key: value for key, value in diagnostic.items() if key != 'publication'}
    size = lambda value: len((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8'))
    assert size(prior) <= training_cycles.MAX_RECORD_BYTES < size(current)
    assert next((folder / 'observations').glob('monitor-*/helper/stdout.txt')).stat().st_size <= training_cycles.MAX_RECORD_BYTES
    assert (folder / 'final.json').stat().st_size <= 2 * training_cycles.MAX_RECORD_BYTES
    final = json.loads((folder / 'final.json').read_bytes())
    assert final['status'] == 'completed' and final['gate']['passed'] is True
    assert final['gate']['summary'] == summary
    public = training.submission(state, 'demo', 'alpha')['budget']
    assert public['owner_status'] == 'completed' and public['final'] == final
    assert not (runtime / 'training/fences/alpha.json').exists()
    assert not (runtime / 'ergora/training-cancellations').exists()
    assert all(p.read_bytes() == raw for p, raw in originals.items())


@pytest.mark.parametrize('fault', ['monitor-blocked', 'fence-flush-failed', 'fence-flush-blocked'])
def test_cycle_supervises_blocking_observation_and_recovers_only_the_original_visible_fence(cycle_selection, service, tmp_path, fault):
    from ergora import training_cycles

    service[0]('accepted', budget_scenario=fault)
    state, _, runtime, authorized = authorize_budget(cycle_selection, tmp_path)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    prefix = runtime / 'ergora/training-submissions'
    attempt = (prefix / 'alpha.attempt.json').read_bytes()
    folder = wait_budget_stopped(runtime, seconds=20)
    final_path = folder / 'final.json'
    if final_path.exists():
        assert json.loads(final_path.read_bytes())['status'] == ('fenced' if fault == 'monitor-blocked' else 'unknown')
    fence = runtime / 'training/fences/alpha.json'
    fence_bytes = fence.read_bytes()
    originals = {p: p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    observed = training.submission(state, 'demo', 'alpha')
    assert observed['budget']['local_fence']['sha256'] == hashlib.sha256(fence_bytes).hexdigest()
    assert observed['budget']['executor_stop_confirmed'] is None
    assert training.resume_start(state, 'demo', 'alpha', 1, submitted['intent_sha256'])['status'] == 'submitted'
    assert fence.read_bytes() == fence_bytes and all(p.read_bytes() == raw for p, raw in originals.items())
    assert (prefix / 'alpha.attempt.json').read_bytes() == attempt
    assert json.loads(service[1].read_bytes())['starts'] == 1


def test_cycle_registry_lock_can_exhaust_cleanup_without_claiming_a_fence(cycle_selection, service, tmp_path):
    from ergora import training_cycles
    from ergora.state import file_lock

    state, _, runtime, authorized = authorize_budget(cycle_selection, tmp_path)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    with file_lock(runtime / 'training/registry.lock'):
        folder = wait_budget_stopped(runtime, seconds=20)
        assert not (folder / 'final.json').exists()
    assert not (runtime / 'training/fences/alpha.json').exists()
    observed = training.submission(state, 'demo', 'alpha')['budget']
    assert observed['owner_status'] == 'unknown' and observed['executor_stop_confirmed'] is None
    assert training.resume_start(state, 'demo', 'alpha', 1, submitted['intent_sha256'])['status'] == 'submitted'
    assert json.loads(service[1].read_bytes())['starts'] == 1


def test_cycle_lost_ack_and_missing_authorization_only_reconcile_the_original_start(cycle_selection, service, tmp_path):
    from ergora import training_cycles
    import signal

    state, definition, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=30, cleanup=5)
    select, record = service
    select('lost-ack')
    with pytest.raises(ValueError, match='UNAVAILABLE'):
        training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    original = training.submission(state, 'demo', 'alpha')
    prefix = runtime / 'ergora/training-submissions'
    attempt = (prefix / 'alpha.attempt.json').read_bytes()
    authorization = state.root / 'training-cycles/demo/budget/authorization.json'
    raw = authorization.read_bytes()
    authorization.unlink()
    try:
        assert training.submission(state, 'demo', 'alpha')['budget']['authorization_status'] == 'unknown'
        select('not-found')
        observed = training.resume_start(state, 'demo', 'alpha', 1, original['intent_sha256'])
        # The independent cleanup may have reconciled the accepted original run
        # already. Both observations retain the one original start slot.
        assert observed['intent_sha256'] == original['intent_sha256']
        assert observed['status'] == 'submitted' or observed['reconciliation'] == 'not_found'
        assert native_budget_create(definition, 'alpha', managed=True).returncode != 0
    finally:
        authorization.write_bytes(raw)
        select('accepted')
        from contextlib import suppress
        with suppress(ProcessLookupError):
            os.kill(json.loads((prefix / 'alpha.budget/owner.json').read_bytes())['pid'], signal.SIGTERM)
        wait_budget_final(runtime)
    observed = training.resume_start(state, 'demo', 'alpha', 1, original['intent_sha256'])
    assert observed['status'] == 'submitted' and observed['intent_sha256'] == original['intent_sha256']
    assert (prefix / 'alpha.attempt.json').read_bytes() == attempt
    assert json.loads(record.read_bytes())['starts'] == 1


def assert_budget_process_stopped(identity):
    from ergora.reference_training_budget import _process_identity

    until = time.monotonic() + 5
    while time.monotonic() < until:
        try:
            if _process_identity(identity['pid']) != identity:
                return
        except (OSError, ValueError):
            return
        time.sleep(.05)
    # Cleanup is restricted to this test's exact captured process identity.
    import signal
    try:
        descriptor = os.pidfd_open(identity['pid'])
    except ProcessLookupError:
        return
    try:
        if _process_identity(identity['pid']) != identity:
            return
        signal.pidfd_send_signal(descriptor, signal.SIGKILL)
    finally:
        os.close(descriptor)
    raise AssertionError('Original phase process has not stopped')


def test_budget_phase_supervisors_keep_their_peer_and_reap_a_new_session_descendant(cycle_selection, service, tmp_path):
    from ergora import training_cycles

    service[0]('accepted', budget_scenario='phase-isolation')
    state, _, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=24, cleanup=8)
    training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    wait_budget_stopped(runtime, seconds=35)
    observed = json.loads(service[1].with_suffix('.isolation').read_bytes())
    assert observed == {'owner_subreaper': 0, 'peer_survived_monitor': True}
    assert service[1].with_suffix('.peer-blocked-sync').is_file()
    assert_budget_process_stopped(json.loads(service[1].with_suffix('.descendant').read_bytes()))
    for identity in json.loads(service[1].with_suffix('.peer').read_bytes()).values():
        assert_budget_process_stopped(identity)


def test_budget_phase_reap_survives_total_deadline_and_catchable_owner_cancel(cycle_selection, service, tmp_path):
    from ergora import training_cycles
    import signal

    service[0]('accepted', budget_scenario='phase-reap-overrun')
    state, _, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=24, cleanup=8)
    training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    marker = service[1].with_suffix('.reap-started')
    until = time.monotonic() + 25
    while not marker.exists() and time.monotonic() < until:
        time.sleep(.05)
    supervisor = json.loads(marker.read_bytes())
    folder = runtime / 'ergora/training-submissions/alpha.budget'
    owner = json.loads((folder / 'owner.json').read_bytes())
    os.kill(owner['pid'], signal.SIGTERM)
    wait_budget_stopped(runtime, seconds=15)
    assert json.loads(service[1].with_suffix('.reap-finished').read_bytes())['remaining_seconds'] <= -.5
    assert_budget_process_stopped(supervisor)
    assert_budget_process_stopped(json.loads(service[1].with_suffix('.descendant').read_bytes()))
    observed = json.loads(next((folder / 'launches').glob('*/stdout.json')).read_bytes())
    monitor = next(item for item in observed['phases'] if item['mode'] == 'monitor')
    assert monitor['stopped'] is True and monitor['supervisor_returncode'] in (0, -signal.SIGKILL)
    assert monitor['status'] == 'unknown' and observed['overrun_seconds'] >= .5
    assert observed['publication']['status'] == 'unknown' and observed['executor_stop_confirmed'] is None
    assert not (folder / 'final.json').exists() and not (runtime / 'training/fences/alpha.json').exists()
    assert [path.name.split('-')[0] for path in (folder / 'observations').iterdir()] == ['monitor']


@pytest.mark.parametrize('fault', ['phase-slow-reader', 'phase-held-reader'])
def test_budget_phase_large_input_is_complete_and_a_held_reader_does_not_block_the_deadline(cycle_selection, service, tmp_path, fault):
    from ergora import training_cycles

    service[0]('accepted', budget_scenario=fault)
    state, _, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=24, cleanup=8)
    training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    wait_budget_stopped(runtime, seconds=30)
    marker = service[1].with_suffix('.complete-input')
    if fault == 'phase-slow-reader':
        probe = ('训练场景' * 65_536).encode('utf-8')
        assert json.loads(marker.read_bytes()) == {'bytes': len(probe), 'sha256': hashlib.sha256(probe).hexdigest()}
    else:
        assert not marker.exists()
    observed = training.submission(state, 'demo', 'alpha')['budget']
    assert observed['local_fence'] and observed['executor_stop_confirmed'] is None


@pytest.mark.parametrize('fault', ['phase-result-blocked', 'phase-supervisor-killed', 'phase-stopped-incomplete'])
def test_budget_phase_interruption_preserves_the_original_fence_without_claiming_executor_stop(cycle_selection, service, tmp_path, fault):
    from ergora import training_cycles

    service[0]('accepted', budget_scenario=fault)
    state, _, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=24, cleanup=8)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    wait_budget_stopped(runtime, seconds=30)
    marker = {'phase-result-blocked': '.result-blocked', 'phase-supervisor-killed': '.killed-supervisor',
              'phase-stopped-incomplete': '.incomplete-stopped'}[fault]
    identities = json.loads(service[1].with_suffix(marker).read_bytes())
    if fault != 'phase-supervisor-killed':
        identities = {'supervisor': identities}
    for identity in identities.values():
        assert_budget_process_stopped(identity)
    prefix = runtime / 'ergora/training-submissions'
    original = {p: p.read_bytes() for p in prefix.rglob('*') if p.is_file()}
    fence = (runtime / 'training/fences/alpha.json').read_bytes()
    observed = training.resume_start(state, 'demo', 'alpha', 1, submitted['intent_sha256'])
    assert observed['budget']['local_fence']['sha256'] == hashlib.sha256(fence).hexdigest()
    assert observed['budget']['executor_stop_confirmed'] is None
    assert all(p.read_bytes() == raw for p, raw in original.items())
    if fault == 'phase-supervisor-killed':
        import signal
        monitor = next(item for item in observed['budget']['final']['phases'] if item['mode'] == 'monitor')
        assert monitor['status'] == 'unknown' and monitor['stopped'] is False
        assert monitor['supervisor_returncode'] == -signal.SIGKILL
    if fault == 'phase-stopped-incomplete':
        # Cleanup can exhaust the allowance before final is durably published.
        diagnostic = json.loads(next((prefix / 'alpha.budget/launches').glob('*/stdout.json')).read_bytes())
        monitor = next(item for item in diagnostic['phases'] if item['mode'] == 'monitor')
        assert monitor['status'] == 'unknown' and monitor['stopped'] is False
        assert monitor['reason'] == 'Training phase stopped frame has no complete process observation'


@pytest.mark.skipif(sys.platform != 'linux', reason='Native start preflight requires Linux/WSL2 Git paths')
def test_cycle_freezes_full_admissions_and_reads_offline_without_touching_sources(cycle_selection, tmp_path, monkeypatch, capsys):
    from ergora import training_cycles
    from ergora.cli import main

    state, definition, runtime, _, _, request = cycle_selection
    before = {p: p.read_bytes() for root in (runtime, Path(definition['execution']['config_directory']))
              for p in root.rglob('*') if p.is_file()}
    with state.connect() as db:
        database = list(db.iterdump())
    original = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    source, destination = tmp_path / 'selection.json', tmp_path / 'cycle'
    source.write_text(json.dumps(request), encoding='utf-8')
    assert main(['--home', str(state.root), 'training', 'cycle-create', 'demo', '--definition', str(source),
                 '--directory', str(destination)]) == 0
    created = json.loads(capsys.readouterr().out)
    observed = training_cycles.read(destination, sha256=created['sha256'])
    plan = observed['plan']
    assert plan['project'] == state.project('demo') and plan['definition'] == request
    assert plan['admissions'] == [training.check_start(state, 'demo', item['experiment_id'], item['manifest_sha256'])
                                  for item in request['candidates']]
    assert not observed['coverage']['budget_started'] and not observed['coverage']['execution_authorized']
    assert observed['coverage']['runtime_status'] == 'not_queried'
    assert all(p.read_bytes() == raw for p, raw in before.items())
    with state.connect() as db:
        assert list(db.iterdump()) == database

    def no_admission(*args, **kwargs):
        raise AssertionError('Offline cycle reads must not access the current project or native owner')

    monkeypatch.setattr(training, '_project', no_admission)
    unused = tmp_path / 'unused-control'
    assert main(['--home', str(unused), 'training', 'cycle-read', str(destination), '--sha256', created['sha256']]) == 0
    assert json.loads(capsys.readouterr().out) == observed and not unused.exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Native start preflight requires Linux/WSL2 Git paths')
def test_cycle_read_binds_full_sha_and_preserves_existing_publication(cycle_selection, tmp_path):
    from ergora import training_cycles

    state, _, _, _, _, request = cycle_selection
    destination = tmp_path / 'cycle'
    created = training_cycles.create(state, 'demo', request, destination)
    path = destination / 'cycle.json'
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        training_cycles.create(state, 'demo', request, destination)
    assert path.read_bytes() == original
    with pytest.raises(ValueError, match='expected complete SHA256'):
        training_cycles.read(destination, sha256='0' * 64)
    saved = json.loads(original)
    saved['definition']['candidates'] = saved['definition']['candidates'][:1]
    saved['admissions'] = saved['admissions'][:1]
    marker, scope, policy, _ = reference.registration_paths(saved['project']['id'])
    variants = [
        lambda plan: plan['admissions'][0].update(execution_authorized=True),
        lambda plan: plan['project']['registration'].update(files={marker: plan['project']['registration']['files'][marker]}),
        lambda plan: plan['project']['registration']['files'][scope].update(protected_paths=[]),
        lambda plan: plan['admissions'][0]['observation'].update(baseline={}),
        lambda plan: plan['admissions'][0]['observation']['experiment']['manifest'].update(baseline_id='different-baseline'),
        lambda plan: plan['admissions'][0]['observation']['experiment']['spec'].update(max_run_seconds=60),
        lambda plan: plan['admissions'][0]['observation']['experiment']['current_runner'].update(runner_template_id='other'),
        lambda plan: plan['admissions'][0]['observation']['experiment'].update(files={'unrelated': 'z'}),
        lambda plan: plan['admissions'][0]['observation']['experiment']['files'].update({'state/training/manifests/alpha.json': '0' * 64}),
    ]
    for mutation in variants:
        plan = deepcopy(saved)
        mutation(plan)
        raw = json.dumps(plan).encode('utf-8')
        path.write_bytes(raw)
        with pytest.raises(ValueError):
            training_cycles.read(destination, sha256=hashlib.sha256(raw).hexdigest())
    # Legacy imports preserve an equivalent execution-policy list order.
    saved['project']['registration']['files'][policy]['allowed_task_types'].reverse()
    path.write_text(json.dumps(saved), encoding='utf-8')
    assert training_cycles.read(destination)['plan'] == saved


@pytest.mark.skipif(sys.platform != 'linux', reason='Native start preflight requires Linux/WSL2 Git paths')
@pytest.mark.parametrize('field', ['dataset_manifest_sha256', 'performance_policy'])
def test_cycle_refuses_different_semantics_or_measurement_policy(cycle_selection, tmp_path, field):
    from ergora import training_cycles

    state, _, runtime, prefix, write, request = cycle_selection
    manifest = json.loads((runtime / 'training/manifests/beta.json').read_bytes())
    if field == 'performance_policy':
        manifest[field]['thresholds']['min_saved_seconds_at_normalization'] *= 2
    else:
        manifest[field] = 'e' * 64
    digest = write(runtime / 'training/manifests/beta.json', manifest)
    write(prefix / 'experiments/beta/manifest.json', manifest)
    spec = json.loads((runtime / 'training/specs/beta.json').read_bytes())
    spec['binding']['manifest_sha'] = digest
    write(runtime / 'training/specs/beta.json', spec)
    request['candidates'][1]['manifest_sha256'] = digest
    assert training.check_start(state, 'demo', 'beta', digest)['ready_for_new_start']
    destination = tmp_path / 'different-contract'
    with pytest.raises(ValueError, match='initial baseline, workload, semantic and measurement contract'):
        training_cycles.create(state, 'demo', request, destination)
    assert not destination.exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Native start preflight requires Linux/WSL2 Git paths')
def test_cycle_rejects_cross_candidate_project_drift(cycle_selection, tmp_path, monkeypatch):
    from ergora import training_cycles

    state, _, _, _, _, request = cycle_selection
    original = training.check_start

    def drift(*args):
        result = original(*args)
        with state.connect() as db:
            project = json.loads(db.execute("SELECT document FROM projects WHERE id='demo'").fetchone()[0])
            project['revision'] += 1
            db.execute("UPDATE projects SET document=? WHERE id='demo'", (json.dumps(project),))
        return result

    monkeypatch.setattr(training, 'check_start', drift)
    destination = tmp_path / 'drift'
    with pytest.raises(ValueError, match='Project changed while capturing'):
        training_cycles.create(state, 'demo', request, destination)
    assert not destination.exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Native start preflight requires Linux/WSL2 Git paths')
def test_cycle_rejects_complete_aggregate_capacity_before_publication(cycle_selection, tmp_path):
    from ergora import training_cycles

    state, _, runtime, prefix, write, request = cycle_selection
    manifest = json.loads((runtime / 'training/manifests/alpha.json').read_bytes())
    spec = json.loads((runtime / 'training/specs/alpha.json').read_bytes())
    manifest['notes'] = 'x' * 900_000
    request['candidates'] = []
    for number in range(12):
        ident = 'capacity-' + str(number)
        manifest['experiment_id'] = ident
        digest = write(runtime / ('training/manifests/' + ident + '.json'), manifest)
        write(prefix / ('experiments/' + ident + '/manifest.json'), manifest)
        spec['binding'].update(experiment_id=ident, manifest_sha=digest)
        spec['manifest_uri'] = (runtime / ('training/manifests/' + ident + '.json')).as_uri()
        write(runtime / ('training/specs/' + ident + '.json'), spec)
        request['candidates'].append({'experiment_id': ident, 'manifest_sha256': digest,
                                      'change': 'Complete large native candidate', 'next_bottleneck': 'Not measured'})
    destination = tmp_path / 'oversized'
    with pytest.raises(ValueError, match='exceeds 10 MB'):
        training_cycles.create(state, 'demo', request, destination)
    assert not destination.exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Training authorization requires Linux/WSL2 clocks')
def test_cycle_authorization_cli_retains_complete_input_and_lost_reply(cycle_selection, tmp_path, monkeypatch, capsys):
    from ergora import training_cycles
    from ergora.cli import main

    state, definition, runtime, _, _, request = cycle_selection
    source = tmp_path / 'original-input'
    selected = training_cycles.create(state, 'demo', request, source)
    raw = (source / 'cycle.json').read_bytes()
    revision = state.project('demo')['revision']
    before = {p: p.read_bytes() for root in (runtime, Path(definition['execution']['config_directory']))
              for p in root.rglob('*') if p.is_file()}
    with state.connect() as db:
        database = list(db.iterdump())
    args = ['--home', str(state.root), 'training', 'cycle-authorize', 'demo', 'first', '--directory', str(source),
            '--sha256', selected['sha256'], '--revision', str(revision), '--confirm']
    assert main(args) == 0
    authorized = json.loads(capsys.readouterr().out)
    assert authorized['status'] == 'ready' and authorized['ready']['authorization_sha256'] == authorized['authorization_sha256']
    assert authorized['coverage'] == {'records': 'original-local-authorization', 'origin_authenticated': True,
        'runtime_status': 'not_queried', 'budget_started': True, 'execution_authorized': False}
    saved = state.root / 'training-cycles/demo/first'
    assert (saved / 'cycle.json').read_bytes() == raw
    originals = {p: p.read_bytes() for p in saved.iterdir()}
    shutil.rmtree(source)

    def no_check(*args, **kwargs):
        raise AssertionError('An acknowledged or lost-reply ready authorization must retain its original checks')

    monkeypatch.setattr(training, 'check_start', no_check)
    assert main(args) == 0
    again = json.loads(capsys.readouterr().out)
    assert again['authorization'] == authorized['authorization'] and again['ready'] == authorized['ready']
    assert again['work_remaining_seconds'] < authorized['work_remaining_seconds']
    assert main(['--home', str(state.root), 'training', 'cycle-status', 'demo', 'first',
                 '--authorization-sha256', authorized['authorization_sha256']]) == 0
    assert json.loads(capsys.readouterr().out)['authorization'] == authorized['authorization']
    assert {p: p.read_bytes() for p in saved.iterdir()} == originals
    assert all(p.read_bytes() == value for p, value in before.items())
    with state.connect() as db:
        assert list(db.iterdump()) == database
    projects.bind(state, 'demo', 'memory', {'tool': 'sqlite'}, revision)
    changed = training_cycles.status(state, 'demo', 'first')
    assert changed['status'] == 'project-changed' and not changed['current_project_matches']
    assert changed['authorization'] == authorized['authorization']
    with pytest.raises(ValueError, match='cannot be renewed'):
        training_cycles.authorize(state, 'demo', 'first', source, selected['sha256'], revision + 1, confirm=True)


@pytest.mark.skipif(sys.platform != 'linux', reason='Training authorization requires Linux/WSL2 clocks')
@pytest.mark.parametrize('boundary', ['first-check', 'second-check', 'input-fsync', 'ready-fsync', 'ready-directory-fsync'])
def test_cycle_admission_and_publication_consume_the_original_deadline(cycle_selection, tmp_path, monkeypatch, boundary):
    from ergora import training_cycles

    state, _, _, _, _, request = cycle_selection
    request['budget'].update(wall_seconds=4, cleanup_seconds=1)
    source = tmp_path / 'input'
    selected = training_cycles.create(state, 'demo', request, source)
    saved = state.root / 'training-cycles/demo/short'
    original_check, original_fsync = training.check_start, os.fsync
    calls, delayed = [], []

    def check(*args):
        # The complete source and clock must already exist before even the first live admission.
        assert (saved / 'authorization.json').is_file() and (saved / 'cycle.json').is_file()
        calls.append(args[2])
        result = original_check(*args)
        if boundary == ('first-check' if len(calls) == 1 else 'second-check'):
            time.sleep(max(0, training_cycles.status(state, 'demo', 'short')['work_remaining_seconds']) + .05)
        return result

    def fsync(descriptor):
        path = Path('/proc/self/fd/' + str(descriptor)).resolve()
        input_present = (saved / 'cycle.json').exists()
        targeted = ((boundary == 'input-fsync' and path.parent == saved and path.name.startswith('.pending-')
                     and (saved / 'authorization.json').exists() and not input_present)
                    or (boundary == 'ready-fsync' and path.parent == saved and path.name.startswith('.pending-') and input_present)
                    or (boundary == 'ready-directory-fsync' and path == saved and (saved / 'ready.json').exists()))
        if targeted and not delayed:
            delayed.append(str(path))
            if boundary == 'ready-directory-fsync':
                concurrent = training_cycles.status(state, 'demo', 'short')
                assert concurrent['status'] == 'pending' and concurrent['ready'] is None
            time.sleep(request['budget']['wall_seconds'] - request['budget']['cleanup_seconds'] + .05)
        return original_fsync(descriptor)

    monkeypatch.setattr(training, 'check_start', check)
    monkeypatch.setattr(os, 'fsync', fsync)
    result = training_cycles.authorize(state, 'demo', 'short', source, selected['sha256'], 1, confirm=True)
    assert result['status'] == 'exhausted' and result['work_remaining_seconds'] <= 0
    assert not result['coverage']['execution_authorized']
    assert calls == ([] if boundary == 'input-fsync' else ['alpha'] if boundary == 'first-check' else ['alpha', 'beta'])
    assert len(delayed) == int(boundary.endswith('fsync'))
    original = {p: p.read_bytes() for p in saved.iterdir()}
    again = training_cycles.authorize(state, 'demo', 'short', source, selected['sha256'], 1, confirm=True)
    assert again['authorization'] == result['authorization'] and again['status'] == 'exhausted'
    assert {p: p.read_bytes() for p in saved.iterdir()} == original


@pytest.mark.skipif(sys.platform != 'linux', reason='Training authorization requires Linux/WSL2 clocks')
def test_cycle_interrupted_initial_publication_retains_the_original_id_and_clock(cycle_selection, tmp_path, monkeypatch):
    from ergora import budget_clock, training_cycles

    state, _, _, _, _, request = cycle_selection
    source = tmp_path / 'input'
    selected = training_cycles.create(state, 'demo', request, source)
    saved = state.root / 'training-cycles/demo/interrupted'
    record, start = training_cycles._record, budget_clock.authorize
    clocks, originals = [], []

    def clock(*args):
        value = start(*args)
        clocks.append(value)
        return value

    def interrupt(path, value):
        record(path, value)
        if path.name == 'authorization.json':
            originals.append(path.read_bytes())
            raise OSError('Lost durable authorization acknowledgement')

    monkeypatch.setattr(budget_clock, 'authorize', clock)
    monkeypatch.setattr(training_cycles, '_record', interrupt)
    with pytest.raises(OSError, match='Lost durable authorization acknowledgement'):
        training_cycles.authorize(state, 'demo', 'interrupted', source, selected['sha256'], 1, confirm=True)
    assert saved.is_dir() and (saved / 'authorization.json').read_bytes() == originals[0]
    monkeypatch.setattr(training_cycles, '_record', record)
    # An incomplete original cannot be silently replaced, even when its external source is still available.
    with pytest.raises(FileNotFoundError):
        training_cycles.authorize(state, 'demo', 'interrupted', source, selected['sha256'], 1, confirm=True)
    assert len(clocks) == 1 and (saved / 'authorization.json').read_bytes() == originals[0]


@pytest.mark.skipif(sys.platform != 'linux', reason='Training authorization requires Linux/WSL2 clocks')
def test_cycle_ready_directory_failure_is_unknown_until_original_publication_is_durable(cycle_selection, tmp_path, monkeypatch):
    from ergora import training_cycles

    state, _, _, _, _, request = cycle_selection
    source = tmp_path / 'input'
    selected = training_cycles.create(state, 'demo', request, source)
    saved = state.root / 'training-cycles/demo/ready-interrupted'
    fsync = os.fsync

    def failing(descriptor):
        if Path('/proc/self/fd/' + str(descriptor)).resolve() == saved and (saved / 'ready.json').exists():
            raise OSError('Original directory flush failed')
        return fsync(descriptor)

    monkeypatch.setattr(os, 'fsync', failing)
    with pytest.raises(OSError, match='Original directory flush failed'):
        training_cycles.authorize(state, 'demo', 'ready-interrupted', source, selected['sha256'], 1, confirm=True)
    originals = {p: p.read_bytes() for p in saved.iterdir()}
    unknown = training_cycles.status(state, 'demo', 'ready-interrupted')
    assert unknown['status'] == 'unknown' and 'durability' in unknown['reason']
    assert unknown['ready'] is None and not unknown['coverage']['execution_authorized']
    again = training_cycles.authorize(state, 'demo', 'ready-interrupted', source, selected['sha256'], 1, confirm=True)
    assert again['status'] == 'unknown' and again['authorization'] == unknown['authorization']
    monkeypatch.setattr(os, 'fsync', fsync)
    recovered = training_cycles.status(state, 'demo', 'ready-interrupted')
    assert recovered['status'] == 'ready' and recovered['authorization'] == unknown['authorization']
    assert {p: p.read_bytes() for p in saved.iterdir()} == originals
    operation = recovered['authorization']['registration']['operation_id']
    journal = state.root / 'registrations/demo' / (operation + '.json')
    journal_raw = journal.read_bytes()

    def lost_source(descriptor):
        result = fsync(descriptor)
        if Path('/proc/self/fd/' + str(descriptor)).resolve() == saved:
            journal.unlink()
        return result

    monkeypatch.setattr(os, 'fsync', lost_source)
    with pytest.raises(FileNotFoundError):
        training_cycles.status(state, 'demo', 'ready-interrupted')
    journal.write_bytes(journal_raw)
    assert {p: p.read_bytes() for p in saved.iterdir()} == originals


@pytest.mark.skipif(sys.platform != 'linux', reason='Training authorization requires Linux/WSL2 clocks')
def test_cycle_partial_checks_recover_concurrently_without_reauthorizing(cycle_selection, tmp_path, monkeypatch):
    from ergora import training_cycles
    from ergora.state import State

    state, _, _, _, _, request = cycle_selection
    source = tmp_path / 'input'
    selected = training_cycles.create(state, 'demo', request, source)
    original_check = training.check_start
    calls = []

    def interrupted(*args):
        calls.append(args[2])
        if len(calls) == 2:
            raise OSError('Interrupted admission')
        return original_check(*args)

    monkeypatch.setattr(training, 'check_start', interrupted)
    with pytest.raises(OSError, match='Interrupted admission'):
        training_cycles.authorize(state, 'demo', 'pending', source, selected['sha256'], 1, confirm=True)
    pending = training_cycles.status(state, 'demo', 'pending')
    assert pending['status'] == 'pending' and pending['ready'] is None
    saved = state.root / 'training-cycles/demo/pending'
    original = {p: p.read_bytes() for p in saved.iterdir()}
    shutil.rmtree(source)
    calls.clear()

    def recovered(*args):
        calls.append(args[2])
        return original_check(*args)

    monkeypatch.setattr(training, 'check_start', recovered)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(training_cycles.authorize, State(state.root), 'demo', 'pending', source, selected['sha256'], 1, confirm=True)
        second = pool.submit(training_cycles.authorize, State(state.root), 'demo', 'pending', source, selected['sha256'], 1, confirm=True)
        results = [first.result(timeout=30), second.result(timeout=30)]
    assert calls == ['alpha', 'beta']
    assert all(result['status'] == 'ready' and result['authorization'] == pending['authorization'] for result in results)
    assert all(p.read_bytes() == raw for p, raw in original.items())
    with pytest.raises(ValueError, match='different complete input'):
        training_cycles.authorize(state, 'demo', 'pending', source, '0' * 64, 1, confirm=True)


@pytest.mark.skipif(sys.platform != 'linux', reason='Training authorization requires Linux/WSL2 clocks')
def test_cycle_authorization_reads_its_source_and_rejects_conflicting_records(cycle_selection, tmp_path, monkeypatch):
    from ergora import budget_clock, training_cycles

    state, _, _, _, _, request = cycle_selection
    source = tmp_path / 'input'
    selected = training_cycles.create(state, 'demo', request, source)
    result = training_cycles.authorize(state, 'demo', 'bound', source, selected['sha256'], 1, confirm=True)
    saved = state.root / 'training-cycles/demo/bound'
    registration = result['authorization']['registration']
    published = state.root / 'registrations/demo' / (registration['operation_id'] + '.result.json')
    files = {p: p.read_bytes() for p in (saved / 'authorization.json', saved / 'ready.json', saved / 'cycle.json', published)}
    mutations = [
        (saved / 'authorization.json', lambda value: value['clock'].update(boottime_ns=value['clock']['boottime_ns'] + 1)),
        (saved / 'ready.json', lambda value: value.update(admissions_sha256='0' * 64)),
        (saved / 'cycle.json', lambda value: value['definition']['budget'].update(wall_seconds=request['budget']['wall_seconds'] + 1)),
        (published, lambda value: value.update(intent_sha256='0' * 64)),
    ]
    for path, mutate in mutations:
        value = json.loads(files[path])
        mutate(value)
        path.write_text(json.dumps(value), encoding='utf-8')
        with pytest.raises(ValueError):
            training_cycles.status(state, 'demo', 'bound')
        path.write_bytes(files[path])
    path = saved / 'ready.json'
    for raw in (b'{"checked_at":NaN}', b'{"schema_version":1,"schema_version":1}', b' ' * (training_cycles.MAX_RECORD_BYTES + 1)):
        path.write_bytes(raw)
        with pytest.raises(ValueError):
            training_cycles.status(state, 'demo', 'bound')
    path.unlink()
    linked = tmp_path / 'linked-ready.json'
    linked.write_bytes(files[path])
    path.symlink_to(linked)
    with pytest.raises(ValueError, match='symlinks'):
        training_cycles.status(state, 'demo', 'bound')
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(ValueError, match='ordinary files'):
        training_cycles.status(state, 'demo', 'bound')
    path.unlink()
    path.write_bytes(files[path])
    assert training_cycles.status(state, 'demo', 'bound')['authorization'] == result['authorization']
    clock = budget_clock._clock
    _, ticks = clock()
    monkeypatch.setattr(budget_clock, '_clock', lambda: ('00000000-0000-0000-0000-000000000000', ticks))
    unknown = training_cycles.status(state, 'demo', 'bound')
    assert unknown['status'] == 'unknown' and 'across boot or host' in unknown['reason']
    assert unknown['authorization'] == result['authorization']
    monkeypatch.setattr(budget_clock, '_clock', lambda: (result['authorization']['clock']['boot_id'], 0))
    assert training_cycles.status(state, 'demo', 'bound')['status'] == 'unknown'
    assert all(p.read_bytes() == raw for p, raw in files.items())


def test_submission_read_racing_with_conflict_publication_keeps_valid_checkpoints(tmp_path):
    from ergora.reference_training_submission import _Submission

    operation = _Submission.__new__(_Submission)
    operation.project = {'id': 'demo', 'revision': 1}
    operation.project_revision = operation.project['revision']
    operation.recovery_context = {}
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
    checked = training.check_start(state, 'demo', 'alpha', digest)
    assert not checked['ready_for_new_start'] and checked['submission'] == result and checked['observation'] is None
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
    from ergora import training_cycles
    from ergora.cli import main

    state, definition, runtime, prefix, write, digest = prepared
    select, record = service
    revision = state.project('demo')['revision']
    select(scenario)
    with pytest.raises(ValueError, match='UNAVAILABLE|timed out'):
        training.start(state, 'demo', 'alpha', revision, digest, timeout=1)
    unknown = training.submission(state, 'demo', 'alpha')
    assert unknown['status'] == 'unknown' and unknown['attempt_saved'] and unknown['run_id'] is None
    checked = training.check_start(state, 'demo', 'alpha', digest)
    assert not checked['ready_for_new_start'] and checked['submission'] == unknown
    request = {'schema_version': 1, 'budget': {'wall_seconds': 300, 'cleanup_seconds': 90, 'control_timeout_seconds': 5},
               'candidates': [{'experiment_id': 'alpha', 'manifest_sha256': digest,
                               'change': 'Uncertain original start', 'next_bottleneck': 'Reconcile first'}]}
    destination = state.root / 'unresolved-cycle'
    with pytest.raises(ValueError, match='cannot adopt an existing submission'):
        training_cycles.create(state, 'demo', request, destination)
    assert not destination.exists() and training.submission(state, 'demo', 'alpha') == unknown
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
    projects.bind(state, 'demo', 'memory', {'tool': 'sqlite'}, state.project('demo')['revision'])
    revision = state.project('demo')['revision']
    if scenario == 'preexisting':
        with pytest.raises(ValueError, match='already exists'):
            training.start(state, 'demo', 'alpha', revision, digest)
    else:
        training.start(state, 'demo', 'alpha', revision, digest)
    result = training.submission(state, 'demo', 'alpha')
    assert result['status'] == 'rejected' and result['run_id'] is None
    checked = training.check_start(state, 'demo', 'alpha', digest)
    assert not checked['ready_for_new_start'] and checked['submission'] == result
    assert training.start(state, 'demo', 'alpha', revision, digest) == result
    assert training.resume_start(state, 'demo', 'alpha', revision, result['intent_sha256']) == result
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'start', 'demo', 'alpha',
                     '--revision', str(revision), '--manifest-sha256', digest])
    assert code == 1 and json.loads(output.getvalue()) == result
    assert json.loads(record.read_text())['starts'] == attempts
    selected, current = move_registration(prepared)
    recovered = training.submission(state, 'demo', 'alpha', original_registration=selected)
    assert recovered['original_registration']['registration_project_revision'] < revision < current['revision']
    assert recovered['submitted_revision'] == revision and recovered['project_revision'] == current['revision']
    assert recovered['status'] == result['status'] and recovered['intent_sha256'] == result['intent_sha256']


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
    checked = training.check_start(state, 'demo', 'alpha', digest)
    assert not checked['ready_for_new_start'] and checked['submission'] == saved
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
