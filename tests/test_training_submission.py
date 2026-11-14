"""An accepted native start is never repeated after a lost acknowledgement."""

from contextlib import redirect_stdout
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import io
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

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
