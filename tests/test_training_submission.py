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
def historical_execution(prepared):
    """A synthetic stopped archive, deliberately carrying no live execution authority."""
    from datetime import datetime, timezone
    from ergora import training_cycles
    from ergora.training_execution_protocol import GATE_SOURCES, PROTOCOL

    state, definition, runtime, _, write, _ = prepared
    project = state.project('demo')
    prefix = runtime / 'ergora/training-submissions'
    intent = {'schema_version': 1, 'operation': 'start', 'control_home': str(state.root),
        'project': project['id'], 'repo': project['repo'], 'execution': definition['execution'],
        'registration_sha256': project['registration']['sha256'], 'experiment_id': 'alpha',
        'workflow_id': 'perf-experiment/alpha', 'project_revision': project['revision'],
        'operation_id': '0' * 32, 'observation': reference.training_files(project, experiment_id='alpha')}
    intent['budget'] = {'cycle_id': 'historical', 'authorization_sha256': 'a' * 64,
                        'task_queue': 'ergora-training-budget-v1'}
    write(prefix / 'alpha.intent.json', intent)
    sha = training_cycles._sha
    start = {'schema_version': 1, 'intent_sha256': sha(intent), 'workflow_id': intent['workflow_id'],
             'spec_sha256': sha(intent['observation']['experiment']['spec'])}
    receipt = {**start, 'run_id': 'historical-run'}
    write(prefix / 'alpha.attempt.json', start)
    write(prefix / 'alpha.result.json', receipt)
    owner = {'schema_version': 2, 'intent_sha256': sha(intent), 'authorization_sha256': 'a' * 64,
        'pid': 1, 'start_ticks': '0', 'boot_id': '0' * 36, 'context_sha256': 'b' * 64,
        'execution_capability': {'protocol': PROTOCOL, 'admission_protocol': reference.TRAINING_PROTOCOL,
            'descriptor_sha256': 'c' * 64, 'installation': definition['execution']['installation'],
            'native_python': str(Path(definition['execution']['installation']) / '.venv/bin/python'),
            'cycle_ready_sha256': 'd' * 64, 'gate_sources': {name: 'e' * 64 for name in GATE_SOURCES}}}
    write(prefix / 'alpha.budget/owner.json', owner)
    native = {'schema_version': 1, 'job_id': 'local-perf-alpha',
        'experiment': intent['observation']['experiment']['spec'],
        'runner': intent['observation']['experiment']['current_runner']}
    native_sha = write(runtime / 'training/jobs/alpha/request.json', native)
    request = {'schema_version': 1, 'kind': 'training-execution-request', 'protocol': PROTOCOL,
        'control_home': str(state.root), 'project': 'demo', 'project_revision': intent['project_revision'],
        'registration_sha256': intent['registration_sha256'], 'execution': intent['execution'],
        'experiment_id': 'alpha', 'job_id': native['job_id'], 'workflow_id': intent['workflow_id'],
        'run_id': receipt['run_id'], 'start_intent_sha256': sha(intent), 'start_attempt_sha256': sha(start),
        'start_receipt_sha256': sha(receipt), 'authorization_sha256': 'a' * 64, 'owner_sha256': sha(owner),
        'native_request_sha256': native_sha, 'native_request_semantic_sha256': sha(native),
        'confirmation': True, 'actor_id': 'unix:999:historical-actor'}
    launch = {'schema_version': 1, 'kind': 'training-execution-launch', 'protocol': PROTOCOL,
        'request_sha256': sha(request), 'owner_sha256': sha(owner), 'authorization_sha256': 'a' * 64,
        'clock_sha256': 'f' * 64, 'launch_id': '1' * 32, 'execution_phase_id': '2' * 32}
    supervisor = {'pid': 2, 'start_ticks': '1', 'boot_id': '0' * 36}
    executor = {'pid': 3, 'start_ticks': '2', 'boot_id': '0' * 36}
    attempt = {'schema_version': 1, 'kind': 'training-execution-attempt', 'protocol': PROTOCOL,
        'launch_sha256': sha(launch), 'request_sha256': sha(request), 'owner_sha256': sha(owner),
        'run_id': receipt['run_id'], 'job_id': native['job_id'], 'native_request_sha256': native_sha,
        'supervisor': supervisor, 'executor': executor}
    ack = {'schema_version': 1, 'kind': 'training-execution-ack', 'protocol': PROTOCOL,
        'attempt_sha256': sha(attempt), 'launch_sha256': sha(launch), 'request_sha256': sha(request),
        'owner_sha256': sha(owner), 'executor': executor}
    stopped = {'schema_version': 1, 'kind': 'training-execution-stopped', 'protocol': PROTOCOL,
        'request_sha256': sha(request), 'launch_sha256': sha(launch), 'attempt_sha256': sha(attempt),
        'ack_sha256': sha(ack), 'supervisor': supervisor,
        'process': {'status': 'cancelled', 'returncode': -9,
            'output': str(prefix / ('alpha.budget/observations/execute-' + launch['execution_phase_id']) / 'helper')},
        'reaped_at': datetime.now(timezone.utc).isoformat()}
    folder = runtime / 'training/jobs/alpha/managed-execution'
    for name, value in [('request', request), ('launch', launch), ('attempt', attempt), ('ack', ack), ('stopped', stopped)]:
        write(folder / (name + '.json'), value)
    return state, definition, runtime, folder


def test_execution_history_is_sdk_free_and_survives_missing_installation(historical_execution, capsys):
    from ergora.cli import main

    state, definition, runtime, _ = historical_execution
    original = Path(definition['execution']['installation'])
    moved = original.with_name(original.name + '-unavailable')
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    with state.connect() as db:
        database = list(db.iterdump())
    original.rename(moved)
    try:
        assert main(['--home', str(state.root), 'training', 'execution', 'demo', 'alpha']) == 0
        result = json.loads(capsys.readouterr().out)
    finally:
        moved.rename(original)
    assert result['reap_record_observed'] is True
    assert result['executor_stop_confirmed'] is (True if sys.platform == 'linux' else None)
    assert result['runtime_status'] == 'not_queried' and result['execution_authorized'] is False
    assert result['current_sources']['status'] == 'unavailable_or_changed'
    assert result['execution_success'] is None
    assert all(p.read_bytes() == raw for p, raw in before.items())
    with state.connect() as db:
        assert list(db.iterdump()) == database


@pytest.mark.skipif(sys.platform != 'linux', reason='Read-only durable directory observation requires Linux')
def test_visible_stop_needs_same_file_sync_and_reread(historical_execution):
    state, _, runtime, _ = historical_execution
    entrypoint = '''import json,sys,os
from pathlib import Path
from ergora.training_execution_protocol import ExecutionRecords
p=json.load(sys.stdin)
c=ExecutionRecords(p['project'],p['experiment_id'],p['control_home']).load()
def fail(fd): raise OSError('Controlled existing-file sync failure')
os.fsync=fail
print(json.dumps(c.observe(durable=True)))
'''
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    uncertain = reference._training_reader(state.project('demo'), entrypoint,
        {'project': state.project('demo'), 'experiment_id': 'alpha', 'control_home': str(state.root)})
    assert uncertain['reap_record_observed'] is True and uncertain['executor_stop_confirmed'] is None
    recovered = training.execution(state, 'demo', 'alpha')
    assert recovered['executor_stop_confirmed'] is True
    assert recovered['raw_sha256'] == uncertain['raw_sha256']
    assert all(p.read_bytes() == raw for p, raw in before.items())


@pytest.mark.parametrize('mutation', ['numeric-identity', 'native-runner', 'foreign-ack', 'duplicate', 'fifo'])
def test_execution_reader_rejects_inconsistent_original_chain(historical_execution, mutation):
    state, _, runtime, folder = historical_execution
    if mutation == 'fifo' and sys.platform != 'linux':
        pytest.skip('FIFO open protection is a Linux contract')
    path = folder / 'request.json'
    if mutation == 'numeric-identity':
        value = json.loads(path.read_bytes());value['project_revision'] = True
        path.write_text(json.dumps(value))
    elif mutation == 'native-runner':
        path = folder.parent / 'request.json'
        value = json.loads(path.read_bytes());value['runner']['timeout_seconds'] += 1
        path.write_text(json.dumps(value))
    elif mutation == 'foreign-ack':
        path = folder / 'ack.json'
        value = json.loads(path.read_bytes());value['attempt_sha256'] = '0' * 64
        path.write_text(json.dumps(value))
    elif mutation == 'duplicate':
        path.write_text(path.read_text().replace('{', '{"schema_version":1,', 1))
    else:
        path.unlink();os.mkfifo(path)
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    with pytest.raises(ValueError):
        training.execution(state, 'demo', 'alpha')
    assert all(p.read_bytes() == raw for p, raw in before.items())


@pytest.mark.skipif(sys.platform != 'linux', reason='Original budget publication locks require Linux')
def test_owner_observers_share_the_initialization_read_lock(historical_execution):
    state, _, _, folder = historical_execution
    entrypoint = '''import fcntl,json,os,sys
from pathlib import Path
from ergora import processes
from ergora.training_execution_protocol import owner_active
p=json.load(sys.stdin);d=Path(p['control_home'])/'observer-probe';d.mkdir()
o={"schema_version":2,"intent_sha256":"a"*64,"authorization_sha256":"b"*64,
   **processes.identity(os.getpid()),"context_sha256":"c"*64,"execution_capability":None}
(d/'owner.json').write_text(json.dumps(o))
with (d/'lock').open('w') as lock,(d/'initializing.lock').open('w') as ready:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 fcntl.flock(ready,fcntl.LOCK_EX|fcntl.LOCK_NB)
 initializing=owner_active(d/'owner.json',o)
 fcntl.flock(ready,fcntl.LOCK_SH)
 shared=owner_active(d/'owner.json',o)
print(json.dumps({'initializing':initializing,'shared_observer':shared}))
'''
    observed = reference._training_reader(state.project('demo'), entrypoint, {'control_home': str(state.root)})
    assert observed == {'initializing': False, 'shared_observer': True}


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
            if ('from ergora.reference_training_submission import main;main()' in argv
                    or 'from ergora.reference_training_worker import execution_main;execution_main()' in argv):
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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
    authorized = training_cycles.authorize(state, 'demo', 'budget', source, selected['sha256'],
                                          state.project('demo')['revision'], confirm=True)
    assert authorized['status'] == 'ready'
    return state, definition, runtime, authorized


@pytest.fixture
def controller_admission(cycle_selection, tmp_path):
    from ergora import training_cycles
    from ergora.training_execution_protocol import CycleAdmission

    state, _, _, _, _, request = cycle_selection
    source = tmp_path / 'controller-input'
    selected = training_cycles.create(state, 'demo', request, source)
    authorized = training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'],
        state.project('demo')['revision'], confirm=True, execute_selected=True)
    directory = state.root / 'training-cycles/demo/controller'
    return state, source, selected, authorized, CycleAdmission(directory, authorized['authorization'])


def admission_process(admission, tmp_path, mode, *, reason='First controller stop'):
    import ergora

    marker = tmp_path / (mode + '-ready')
    child = subprocess.Popen([sys.executable, '-I', '-S', '-B',
        str(Path(__file__).parent / 'fixtures/training_cycle_admission.py'),
        str(Path(ergora.__file__).parent.parent), str(admission.directory), str(marker), mode, reason],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    until = time.monotonic() + 10
    while time.monotonic() < until and not marker.exists() and child.poll() is None:
        time.sleep(.01)
    if not marker.exists():
        child.kill()
        stdout, stderr = child.communicate(timeout=5)
        raise AssertionError('Parent admission child did not reach its real boundary: ' + stdout + stderr)
    return child


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_controller_birth_consent_retains_original_actor_clock_and_mode(controller_admission, monkeypatch):
    from ergora import training_cycles

    state, source, selected, authorized, admission = controller_admission
    authorization = authorized['authorization']
    assert authorized['status'] == 'ready' and authorization['schema_version'] == 2
    assert authorized['controller']['consent_recorded'] is True
    assert authorized['coverage']['execution_authorized'] is False
    controller = authorization['controller']
    assert controller['actor_id'] == f'unix:{os.getuid()}:{training_cycles.getpass.getuser()}'
    identity = {key: authorization[key] for key in ('control_home', 'project', 'cycle_id', 'input_sha256')}
    assert controller == {'protocol': 'ergora-training-cycle-v1',
        'workflow_id': 'ergora-training-cycle/' + training_cycles._sha(identity),
        'task_queue': 'ergora-training-cycle-v1', 'execution_scope': 'ordered-selected-native-once',
        'continuation': 'accepted-archive-pass', 'actor_id': controller['actor_id'], 'confirmation': True}
    assert authorization['sha256'] == training_cycles._sha({k: v for k, v in authorization.items() if k != 'sha256'})
    original = {p: p.read_bytes() for p in admission.directory.rglob('*') if p.is_file()}
    monkeypatch.setattr(training_cycles.getpass, 'getuser', lambda: 'different-observer')
    again = training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert again['authorization'] == authorization and again['work_remaining_seconds'] < authorized['work_remaining_seconds']
    with pytest.raises(ValueError, match='consent mode'):
        training_cycles.authorize(state, 'demo', 'controller', source, selected['sha256'], 1, confirm=True)
    manual = training_cycles.authorize(state, 'demo', 'manual', source, selected['sha256'], 1, confirm=True)
    assert manual['authorization']['schema_version'] == 1 and 'controller' not in manual
    assert not (admission.directory.parent / 'manual/controller').exists()
    with pytest.raises(ValueError, match='consent mode'):
        training_cycles.authorize_controller(state, 'demo', 'manual', source, selected['sha256'], 1,
            confirm=True, execute_selected=True)
    for flag in (False, 1):
        with pytest.raises(ValueError, match='Explicitly confirm execution'):
            training_cycles.authorize_controller(state, 'demo', 'unconfirmed', source, selected['sha256'], 1,
                confirm=True, execute_selected=flag)
    assert not (admission.directory.parent / 'unconfirmed').exists()
    assert all(p.read_bytes() == raw for p, raw in original.items())
    # A recomputed digest cannot legitimize a nonboolean confirmation.
    altered = deepcopy(authorization)
    altered['controller']['confirmation'] = 1
    altered['sha256'] = training_cycles._sha({k: v for k, v in altered.items() if k != 'sha256'})
    (admission.directory / 'authorization.json').write_text(json.dumps(altered))
    with pytest.raises(ValueError, match='canonical SHA256'):
        training_cycles.status(state, 'demo', 'controller')


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
@pytest.mark.parametrize('boundary', ['lock-file', 'lock-directory', 'ready-directory'])
def test_controller_lock_publication_recovers_only_the_original_consent(cycle_selection, tmp_path, monkeypatch, boundary):
    from ergora import training_cycles

    state, _, _, _, _, request = cycle_selection
    source = tmp_path / 'input'
    selected = training_cycles.create(state, 'demo', request, source)
    saved = state.root / 'training-cycles/demo/interrupted-controller'
    fsync, failed = os.fsync, []

    def interrupt(descriptor):
        path = Path('/proc/self/fd/' + str(descriptor)).resolve()
        targeted = ((boundary == 'lock-file' and path.parent == saved / 'controller' and path.name.startswith('.pending-'))
            or (boundary == 'lock-directory' and path == saved / 'controller')
            or (boundary == 'ready-directory' and path == saved and (saved / 'ready.json').exists()))
        if targeted:
            failed.append(str(path))
            assert (saved / 'authorization.json').is_file() and (saved / 'cycle.json').is_file()
            if boundary != 'ready-directory':
                assert not (saved / 'ready.json').exists()
            raise OSError('Interrupted original controller publication')
        return fsync(descriptor)

    monkeypatch.setattr(os, 'fsync', interrupt)
    with pytest.raises(OSError, match='Interrupted original controller publication'):
        training_cycles.authorize_controller(state, 'demo', 'interrupted-controller', source, selected['sha256'], 1,
            confirm=True, execute_selected=True)
    assert failed
    original = {p: p.read_bytes() for p in saved.rglob('*') if p.is_file()}
    observed = training_cycles.status(state, 'demo', 'interrupted-controller')
    assert observed['status'] == ('unknown' if boundary == 'ready-directory' else 'pending')
    monkeypatch.setattr(os, 'fsync', fsync)
    recovered = training_cycles.authorize_controller(state, 'demo', 'interrupted-controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert recovered['status'] == 'ready' and recovered['authorization'] == observed['authorization']
    assert (saved / 'controller/admission.lock').read_bytes() == b''
    assert all(p.read_bytes() == raw for p, raw in original.items())


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_controller_ready_never_recreates_or_accepts_a_changed_parent_lock(controller_admission, tmp_path):
    from ergora import training_cycles

    state, source, selected, _, admission = controller_admission
    outside = tmp_path / 'outside-lock'
    outside.write_bytes(b'External lock must remain unchanged')
    for shape in ('missing', 'nonempty', 'fifo', 'symlink'):
        admission.lock.unlink(missing_ok=True)
        if shape == 'nonempty':
            admission.lock.write_bytes(b'x')
        elif shape == 'fifo':
            os.mkfifo(admission.lock)
        elif shape == 'symlink':
            admission.lock.symlink_to(outside)
        with pytest.raises((OSError, ValueError)):
            training_cycles.status(state, 'demo', 'controller')
        with pytest.raises((OSError, ValueError)):
            training_cycles.authorize_controller(state, 'demo', 'controller', source, selected['sha256'], 1,
                confirm=True, execute_selected=True)
        if shape == 'missing':
            assert not admission.lock.exists()
    assert outside.read_bytes() == b'External lock must remain unchanged'


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')
def test_controller_lock_sync_consumes_the_original_computation_window(cycle_selection, tmp_path, monkeypatch):
    from ergora import budget_clock, training_cycles

    state, _, _, _, _, request = cycle_selection
    request['budget'].update(wall_seconds=4, cleanup_seconds=1)
    source = tmp_path / 'input'
    selected = training_cycles.create(state, 'demo', request, source)
    saved = state.root / 'training-cycles/demo/slow-controller'
    fsync, delayed = os.fsync, []

    def slow(descriptor):
        if Path('/proc/self/fd/' + str(descriptor)).resolve() == saved / 'controller' and not delayed:
            delayed.append(True)
            authorization = json.loads((saved / 'authorization.json').read_bytes())
            remaining = budget_clock.remaining(authorization['clock'], request['budget']['wall_seconds'],
                request['budget']['cleanup_seconds'])
            time.sleep(max(0, remaining) + .05)
        return fsync(descriptor)

    monkeypatch.setattr(os, 'fsync', slow)
    result = training_cycles.authorize_controller(state, 'demo', 'slow-controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert delayed and result['status'] == 'exhausted' and result['work_remaining_seconds'] <= 0
    assert not (saved / 'ready.json').exists()
    original = (saved / 'authorization.json').read_bytes()
    again = training_cycles.authorize_controller(state, 'demo', 'slow-controller', source, selected['sha256'], 1,
        confirm=True, execute_selected=True)
    assert again['authorization'] == result['authorization'] and (saved / 'authorization.json').read_bytes() == original


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
@pytest.mark.parametrize('boundary', ['create', 'file-fsync', 'directory-fsync'])
def test_controller_visible_stop_denies_new_work_before_durable_confirmation(controller_admission, tmp_path, boundary):
    from ergora import training_cycles

    state, _, _, authorized, admission = controller_admission
    child = admission_process(admission, tmp_path, boundary)
    try:
        observed = admission.observe()
        assert observed['stop_visible'] is True and observed['stop_durable'] is None
        assert observed['identity_matches'] is (boundary != 'create')
        assert observed['executor_stop_confirmed'] is None
        with pytest.raises(ValueError, match='stop is visible'):
            with admission.permission():
                pytest.fail('Visible parent stop must veto new work')
        stdout, stderr = child.communicate('\n', timeout=10)
        assert child.returncode == 0, stderr
        first = json.loads(stdout)
        assert first['stop_durable'] is True and first['admission_drained'] is True
        raw = admission.stop.read_bytes()
        again = training_cycles.stop_controller(state, 'demo', 'controller', authorized['authorization_sha256'], reason='Later reason')
        assert again['record'] == first['record'] and admission.stop.read_bytes() == raw
        assert again['executor_stop_confirmed'] is None
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=5)


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_parent_drain_waits_for_all_original_shared_permits(controller_admission, tmp_path):
    from ergora import training_cycles

    state, _, _, authorized, admission = controller_admission
    children = []
    try:
        for number in range(2):
            folder = tmp_path / str(number)
            folder.mkdir()
            children.append(admission_process(admission, folder, 'hold'))
        stopped = training_cycles.stop_controller(state, 'demo', 'controller', authorized['authorization_sha256'], reason='Stop active permits')
        raw = admission.stop.read_bytes()
        assert stopped['stop_durable'] is True and stopped['admission_drained'] is None
        assert stopped['executor_stop_confirmed'] is None
        for number, child in enumerate(children):
            stdout, stderr = child.communicate('\n', timeout=5)
            assert child.returncode == 0 and json.loads(stdout)['released'], stderr
            drained = admission.observe(drain=True)
            assert drained['admission_drained'] is (True if number == len(children) - 1 else None)
            assert drained['executor_stop_confirmed'] is None
        assert admission.stop.read_bytes() == raw
        assert training_cycles.status(state, 'demo', 'controller')['status'] == 'stopped'
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
@pytest.mark.parametrize('boundary', ['file', 'directory'])
def test_controller_stop_durability_recovers_by_synchronizing_the_same_original(controller_admission, monkeypatch, boundary):
    _, _, _, _, admission = controller_admission
    fsync = os.fsync

    def failing(descriptor):
        target = admission.stop if boundary == 'file' else admission.folder
        if Path('/proc/self/fd/' + str(descriptor)).resolve() == target:
            raise OSError('Controller stop storage synchronization failed')
        return fsync(descriptor)

    monkeypatch.setattr(os, 'fsync', failing)
    result = admission.request_stop('Original stop during storage failure')
    original, details = admission.stop.read_bytes(), admission.stop.stat()
    assert result['stop_visible'] is True and result['identity_matches'] is True
    assert result['stop_durable'] is None and result['admission_drained'] is None
    again = admission.request_stop('Later request must not replace it')
    assert again['stop_durable'] is None and again['record'] == result['record']
    monkeypatch.setattr(os, 'fsync', fsync)
    recovered = admission.observe(drain=True)
    assert recovered['stop_durable'] is True and recovered['admission_drained'] is True
    assert recovered['record'] == result['record'] and admission.stop.read_bytes() == original
    assert admission.stop.stat().st_ino == details.st_ino
    assert recovered['executor_stop_confirmed'] is None


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_stop_binds_the_complete_saved_controller_intent(controller_admission):
    from ergora import training_cycles

    _, _, _, _, admission = controller_admission
    intent = saved_controller_intent(admission)
    saved = admission.folder / 'intent.json'
    saved.write_text(json.dumps({**intent, 'workflow_input': {**intent['workflow_input'], 'input_sha256': '0' * 64}}))
    with pytest.raises(ValueError, match='complete original authorization'):
        admission.request_stop('Cannot bind a different complete input')
    assert not admission.stop.exists()
    saved.write_text(json.dumps(intent))
    result = admission.request_stop('Original bound intent')
    assert result['record']['controller_intent_sha256'] == training_cycles._sha(intent)
    assert result['stop_durable'] is True
    original = admission.stop.read_bytes()
    saved.write_text(json.dumps({**intent, 'workflow_id': 'different-controller'}))
    changed = admission.observe(drain=True)
    assert changed['stop_visible'] is True and changed['identity_matches'] is False
    assert changed['stop_durable'] is None and changed['admission_drained'] is None
    assert admission.stop.read_bytes() == original


def saved_controller_intent(admission):
    authorization, controller = admission.authorization, admission.authorization['controller']
    workflow_input = {name: authorization[name] for name in ('control_home', 'project', 'cycle_id', 'input_sha256')}
    workflow_input.update(protocol=controller['protocol'], authorization_sha256=authorization['sha256'])
    return {**workflow_input, 'schema_version': 1, 'kind': 'training-cycle-controller-intent',
        'project_revision': authorization['project_revision'], 'workflow_id': controller['workflow_id'],
        'task_queue': controller['task_queue'], 'workflow_input': workflow_input}


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_null_stop_keeps_its_veto_when_a_later_intent_cannot_be_bound(controller_admission):
    _, _, _, _, admission = controller_admission
    result = admission.request_stop('Stop before any controller intent')
    assert result['record']['controller_intent_sha256'] is None and result['stop_durable'] is True
    original = admission.stop.read_bytes()
    for raw in (json.dumps(saved_controller_intent(admission)), '{"incomplete":'):
        (admission.folder / 'intent.json').write_text(raw)
        changed = admission.observe(drain=True)
        assert changed['stop_visible'] is True and changed['identity_matches'] is False
        assert changed['stop_durable'] is None and changed['admission_drained'] is None
        again = admission.request_stop('No replacement or new intent binding')
        assert again['identity_matches'] is False and again['stop_durable'] is None
        assert admission.stop.read_bytes() == original
        with pytest.raises(ValueError, match='stop is visible'):
            with admission.permission():
                pytest.fail('A later intent must never undo the original stop veto')


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_stop_revalidates_intent_after_the_final_drain_sync(controller_admission, monkeypatch):
    _, _, _, _, admission = controller_admission
    admission.request_stop('Stop before controller intent')
    original, fsync, synchronized = admission.stop.read_bytes(), os.fsync, []

    def late_intent(descriptor):
        if Path('/proc/self/fd/' + str(descriptor)).resolve() == admission.stop:
            synchronized.append(True)
            if len(synchronized) == 2:  # The recursive observation holds the parent exclusive lock.
                (admission.folder / 'intent.json').write_text(json.dumps(saved_controller_intent(admission)))
        return fsync(descriptor)

    monkeypatch.setattr(os, 'fsync', late_intent)
    observed = admission.observe(drain=True)
    assert len(synchronized) == 2
    assert observed['stop_visible'] is True and observed['identity_matches'] is False
    assert observed['stop_durable'] is None and observed['admission_drained'] is None
    assert admission.stop.read_bytes() == original


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller stop requires Linux/WSL2 filesystem and flock')
def test_controller_concurrent_stops_preserve_one_original_and_never_repair_corruption(controller_admission, tmp_path):
    state, _, _, _, admission = controller_admission
    children = []
    try:
        for number in range(2):
            folder = tmp_path / str(number)
            folder.mkdir()
            children.append(admission_process(admission, folder, 'concurrent', reason='Reason ' + str(number)))
        for child in children:
            child.stdin.write('\n')
            child.stdin.flush()
        results = []
        for child in children:
            stdout, stderr = child.communicate(timeout=5)
            assert child.returncode == 0, stderr
            results.append(json.loads(stdout))
        original = admission.stop.read_bytes()
        # A loser may observe the winner's partial publication, never a replacement.
        confirmed = admission.observe(drain=True)
        assert confirmed['stop_durable'] is True and confirmed['admission_drained'] is True
        assert confirmed['record']['reason'] in ('Reason 0', 'Reason 1')
        assert all(result['record_sha256'] in (None, confirmed['record_sha256']) for result in results)
        assert admission.stop.read_bytes() == original
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
    for shape in ('partial', 'identity', 'fifo'):
        admission.stop.unlink()
        if shape == 'partial':
            admission.stop.write_bytes(b'{"schema_version":')
        elif shape == 'identity':
            value = json.loads(original)
            value['authorization_sha256'] = '0' * 64
            admission.stop.write_text(json.dumps(value))
        else:
            os.mkfifo(admission.stop)
        before = admission.stop.read_bytes() if shape != 'fifo' else None
        result = admission.request_stop('Do not repair the original')
        assert result['stop_visible'] is True and result['identity_matches'] is False
        assert result['stop_durable'] is None and result['admission_drained'] is None
        with pytest.raises(ValueError, match='stop is visible'):
            with admission.permission():
                pytest.fail('An invalid visible stop still vetoes admission')
        if before is not None:
            assert admission.stop.read_bytes() == before


@pytest.mark.skipif(sys.platform != 'linux', reason='Controller submission requires Linux/WSL2')
def test_controller_consent_cannot_dispatch_through_either_manual_binding_path(controller_admission, cycle_selection, service):
    from ergora import training_cycles

    state, _, selected, authorized, admission = controller_admission
    _, _, runtime, _, _, request = cycle_selection
    service[0]('accepted')
    digest = request['candidates'][0]['manifest_sha256']
    for cycle_entry in (True, False):
        with pytest.raises(ValueError, match='Controller authorization requires complete controller binding'):
            if cycle_entry:
                training_cycles.start(state, 'demo', 'controller', 'alpha', authorized['authorization_sha256'], 1)
            else:
                training.start(state, 'demo', 'alpha', 1, digest,
                    budget={'cycle_id': 'controller', 'authorization_sha256': authorized['authorization_sha256']})
        prefix = runtime / 'ergora/training-submissions'
        assert not (prefix / 'alpha.intent.json').exists() and not (prefix / 'alpha.attempt.json').exists()
        assert not (prefix / 'alpha.budget').exists() and not (runtime / 'training/jobs/alpha').exists()
        assert not service[1].exists()
    assert admission.authorization == authorized['authorization']


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Native managed admission requires Linux/WSL2')
def test_execution_admission_waits_for_the_original_request_writer(cycle_selection, service, tmp_path, monkeypatch):
    from ergora import processes, training_cycles
    import signal

    service[0]('accepted', budget_scenario='managed-no-launch')
    state, definition, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=50, cleanup=10)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    owner = json.loads((runtime / 'ergora/training-submissions/alpha.budget/owner.json').read_bytes())
    expected = {key: owner[key] for key in ('pid', 'start_ticks', 'boot_id')}
    marker = service[1]
    try:
        created = native_budget_create(definition, 'alpha', managed=True)
        assert created.returncode == 0, created.stderr
        request = runtime / 'training/jobs/alpha/request.json'
        monkeypatch.setenv('ERGORA_TEST_TRAINING_WRITER_LOCK', '1')
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(training.execute, state, 'demo', 'alpha', 1, submitted['intent_sha256'],
                submitted['run_id'], hashlib.sha256(request.read_bytes()).hexdigest(), confirm=True)
            try:
                until = time.monotonic() + 10
                while not marker.with_suffix('.admission-contended').exists() and time.monotonic() < until:
                    time.sleep(.02)
                assert marker.with_suffix('.writer-held').exists() and marker.with_suffix('.admission-contended').exists()
                assert not marker.with_suffix('.execution-launch').exists()
            finally:
                marker.with_suffix('.writer-release').touch()
            assert future.result(timeout=10)['status'] == 'requested'
        until = time.monotonic() + 10
        while not marker.with_suffix('.execution-launch').exists() and time.monotonic() < until:
            time.sleep(.02)
        assert marker.with_suffix('.execution-launch').exists()
    finally:
        try:
            processes.notify_identity(expected, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        wait_budget_stopped(runtime, seconds=25)


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Native managed admission requires Linux/WSL2')
def test_explicit_execution_consumes_one_launch_even_if_no_process_starts(cycle_selection, service, tmp_path, monkeypatch):
    from ergora import processes, training_cycles
    import signal

    service[0]('accepted', budget_scenario='managed-no-launch')
    state, definition, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=50, cleanup=10)
    revision = state.project('demo')['revision']
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], revision)
    budget = runtime / 'ergora/training-submissions/alpha.budget'
    owner = json.loads((budget / 'owner.json').read_bytes())
    expected_owner = {key: owner[key] for key in ('pid', 'start_ticks', 'boot_id')}
    try:
        assert owner['schema_version'] == 2 and owner['execution_capability'] is not None
        created = native_budget_create(definition, 'alpha', managed=True)
        assert created.returncode == 0, created.stderr
        job = runtime / 'training/jobs/alpha'
        request_sha = hashlib.sha256((job / 'request.json').read_bytes()).hexdigest()
        training.submission(state, 'demo', 'alpha')
        assert training.resume_start(state, 'demo', 'alpha', revision, submitted['intent_sha256'])['status'] == 'submitted'
        assert training.execution(state, 'demo', 'alpha')['status'] == 'not_requested'
        assert not (job / 'managed-execution').exists()
        run = submitted['run_id']
        for scenario in ('foreign-memo', 'input-collision', 'nonqueued', 'another-job'):
            service[0](scenario, budget_scenario='managed-no-launch')
            with pytest.raises(ValueError):
                training.execute(state, 'demo', 'alpha', revision, submitted['intent_sha256'], run, request_sha, confirm=True)
            assert not (job / 'managed-execution').exists()
        service[0]('accepted', budget_scenario='managed-no-launch')
        for intent_sha, run_id, native_sha in (('0' * 64, run, request_sha),
                (submitted['intent_sha256'], 'another-run', request_sha), (submitted['intent_sha256'], run, '0' * 64)):
            with pytest.raises(ValueError):
                training.execute(state, 'demo', 'alpha', revision, intent_sha, run_id, native_sha, confirm=True)
            assert not (job / 'managed-execution').exists()

        # The real request is published, but its CLI reply is deliberately lost.
        invoke = reference.training_execution
        def lost_reply(project, home, operation, payload, **kwargs):
            result = invoke(project, home, operation, payload, **kwargs)
            if operation == 'request':
                raise ValueError('Controlled loss of explicit request reply')
            return result
        monkeypatch.setattr(reference, 'training_execution', lost_reply)
        with pytest.raises(ValueError, match='Controlled loss'):
            training.execute(state, 'demo', 'alpha', revision, submitted['intent_sha256'], run, request_sha, confirm=True)
        marker = service[1].with_suffix('.execution-launch')
        until = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < until:
            time.sleep(.03)
        launch = (job / 'managed-execution/launch.json').read_bytes()
        observed = training.execution(state, 'demo', 'alpha')
        assert observed['records']['launch']['execution_phase_id'] == json.loads(marker.read_bytes())['phase_id']
        assert observed['records']['attempt'] is None and observed['executor_stop_confirmed'] is None
        monkeypatch.setattr(reference, 'training_execution', invoke)
        final = budget / 'final.json'
        until = time.monotonic() + 10
        while not final.exists() and time.monotonic() < until:
            time.sleep(.03)
        assert final.exists() and json.loads(final.read_bytes())['status'] == 'fenced'
        with pytest.raises(ValueError):
            training.execute(state, 'demo', 'alpha', revision, submitted['intent_sha256'], run, request_sha, confirm=True)
        assert (job / 'managed-execution/launch.json').read_bytes() == launch
        assert not (job / 'started.json').exists() and not (job / 'result.json').exists()
        assert json.loads(service[1].read_bytes())['starts'] == 1
    finally:
        try:
            processes.notify_identity(expected_owner, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        wait_budget_stopped(runtime, seconds=25)


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.skipif(sys.platform != 'linux', reason='Native managed admission requires Linux/WSL2')
def test_execute_startup_failure_keeps_the_consumed_launch_and_cleans_the_original_run(cycle_selection, service, tmp_path):
    from ergora import training_cycles

    service[0]('accepted', budget_scenario='managed-launch-failed')
    state, definition, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=50, cleanup=10)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    try:
        created = native_budget_create(definition, 'alpha', managed=True)
        assert created.returncode == 0, created.stderr
        job = runtime / 'training/jobs/alpha'
        request_sha = hashlib.sha256((job / 'request.json').read_bytes()).hexdigest()
        training.execute(state, 'demo', 'alpha', 1, submitted['intent_sha256'], submitted['run_id'], request_sha, confirm=True)
        budget = runtime / 'ergora/training-submissions/alpha.budget'
        final_path = budget / 'final.json'
        until = time.monotonic() + 10
        while not final_path.exists() and time.monotonic() < until:
            time.sleep(.03)
        assert final_path.exists(), 'Startup failure must enter original fence/cleanup without waiting for compute expiry'
        final = json.loads(final_path.read_bytes())
        assert final['status'] == 'fenced' and final['control']['status'] == 'requested'
        assert final['control']['signal_delivery'] == 'acknowledged'
        failed = next(item for item in final['phases'] if item['mode'] == 'execute')
        assert failed['status'] == 'unknown' and failed['stopped'] is False
        assert 'Controlled execute supervisor startup failure' in failed['reason']
        launch = (job / 'managed-execution/launch.json').read_bytes()
        assert json.loads(service[1].read_bytes())['starts'] == 1
        assert not (job / 'started.json').exists() and not (job / 'result.json').exists()
        wait_budget_stopped(runtime, seconds=15)
        with pytest.raises(ValueError):
            training.execute(state, 'demo', 'alpha', 1, submitted['intent_sha256'], submitted['run_id'], request_sha, confirm=True)
        assert (job / 'managed-execution/launch.json').read_bytes() == launch
    finally:
        wait_budget_stopped(runtime, seconds=25)


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
@pytest.mark.parametrize('legacy_schema', [1, 2])
def test_cycle_managed_create_requires_its_live_owner_and_preserves_single_start_slot(cycle_selection, service, tmp_path, legacy_schema):
    from ergora import training_cycles

    if legacy_schema == 1:
        service[0]('accepted', budget_scenario='legacy-owner-schema1')
    state, definition, runtime, authorized = authorize_budget(cycle_selection, tmp_path, wall=24, cleanup=5)
    submitted = training_cycles.start(state, 'demo', 'budget', 'alpha', authorized['authorization_sha256'], 1)
    created = native_budget_create(definition, 'alpha', managed=True)
    assert created.returncode == 0, created.stderr
    prefix = runtime / 'ergora/training-submissions'
    original = {name: (prefix / ('alpha.' + name + '.json')).read_bytes() for name in ('intent', 'attempt', 'result')}
    try:
        owner = json.loads((prefix / 'alpha.budget/owner.json').read_bytes())
        assert owner['schema_version'] == legacy_schema and owner.get('execution_capability') is None
        with pytest.raises(ValueError, match='no execution capability'):
            training.execute(state, 'demo', 'alpha', 1, submitted['intent_sha256'], submitted['run_id'],
                hashlib.sha256((runtime / 'training/jobs/alpha/request.json').read_bytes()).hexdigest(), confirm=True)
        assert not (runtime / 'training/jobs/alpha/managed-execution').exists()
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Training phase supervision requires Linux/WSL2')
def test_execute_phase_keeps_stop_proof_within_cleanup_without_granting_more_work(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from ergora.reference_training_budget import _BudgetPhase

    # Exercise the real parent pipe/TERM lifecycle. The reporter substitutes only
    # the child's native work; this is not a native execution or durability test.
    started = time.monotonic()
    budget = SimpleNamespace(folder=tmp_path, cancelled=False,
        identity={'schema_version': 1, 'intent_sha256': 'a' * 64, 'authorization_sha256': 'b' * 64},
        operation=SimpleNamespace(payload={}, sha=lambda value: hashlib.sha256(json.dumps(value).encode()).hexdigest()),
        remaining=lambda context, cleanup=False: (5 if cleanup else .4) - (time.monotonic() - started))
    real_launch = subprocess.Popen
    reporter = '''import json,signal,sys,time
cancelled=False
def stop(*_):
 global cancelled
 cancelled=True
signal.signal(signal.SIGTERM,stop)
payload=json.load(sys.stdin)
phase=payload['phase']
time.sleep(.65)
process={'status':'cancelled','returncode':-15,'output':sys.argv[1]}
print(json.dumps({**phase,'event':'stopped','process':process}),flush=True)
print(json.dumps({**phase,'event':'result','result':{'status':'executed','execution':{'executor_stop_confirmed':cancelled}}}),flush=True)
'''
    phase = _BudgetPhase(budget, 'execute', {})
    monkeypatch.setattr(subprocess, 'Popen', lambda argv, **kwargs: real_launch(
        [sys.executable, '-c', reporter, str(phase.output / 'helper')], **kwargs))
    result = phase.run()
    assert budget.remaining({}) < 0 < budget.remaining({}, cleanup=True)
    assert result['execution']['executor_stop_confirmed'] is True
    assert _BudgetPhase(budget, 'execute', {}).start() is False
    assert _BudgetPhase(budget, 'admission', {}).start() is False


@pytest.mark.parametrize('trigger', ['cancel', 'monitor-failure'])
def test_managed_stop_delivers_peer_stops_before_launching_fence(trigger):
    from types import SimpleNamespace
    from ergora.reference_training_execution import Execution

    events = []
    checks = 0
    def remaining(context):
        nonlocal checks
        checks += 1
        if checks > 8:
            events.append(('deadline', 'exhausted'))
            return -1
        return 10
    budget = SimpleNamespace(cancelled=False, remaining=remaining, record_phase=lambda *args: None)

    class Phase:
        def __init__(self, owner, mode, context, **kwargs):
            self.mode, self.stopping = mode, False

        def start(self):
            events.append(('start', self.mode))
            if self.mode == 'execute' and trigger == 'cancel':
                budget.cancelled = True
            return True

        def request_stop(self):
            self.stopping = True

        def poll(self):
            if self.stopping:
                events.append(('stop-delivered', self.mode))
            if self.mode == 'monitor' and trigger == 'monitor-failure' and ('start', 'execute') in events:
                return False
            return self.mode in ('monitor', 'execute') and not self.stopping

        def finish(self):
            return {'status': 'admitted', 'launch': {'execution_phase_id': 'c' * 32}} if self.mode == 'admission' else {'status': 'unknown'}

    Execution(None, budget).drive({}, Phase)
    assert events.index(('stop-delivered', 'execute')) < events.index(('start', 'fence'))
    assert ('deadline', 'exhausted') not in events


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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


@pytest.mark.skipif(sys.platform != 'linux', reason='Native training start and recovery require Linux/WSL2')
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
