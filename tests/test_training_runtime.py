"""Explicit native facts stay separate from saved training records and adoption."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil

import pytest

from ergora import reference, training
from test_training import experiments, registration
from test_reference import prepared_training_installation


@pytest.fixture(scope='module')
def installation(tmp_path_factory, request):
    root = tmp_path_factory.mktemp('training-reference-installation')
    if getattr(request, 'param', None) == 'managed':
        import venv

        root = root / 'managed native'
        reference.prepare_training(root, protocol=reference.TRAINING_PROTOCOL)
        # The native admission boundary runs without application/SDK dependencies.
        venv.EnvBuilder(with_pip=False).create(root / '.venv')
    else:
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


@pytest.fixture
def native_executor(experiments, prepared_training_installation):
    import os
    import subprocess
    import sys

    if sys.platform != 'linux':
        pytest.skip('Native executor uses Linux/WSL2 flock')
    pytest.importorskip('temporalio')
    _, definition, runtime, _, _ = experiments
    installation, _ = prepared_training_installation
    folder = runtime / 'training/jobs/beta'
    (folder / 'started.json').unlink()
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
        AGENTFLOW_CONFIG_DIR=definition['execution']['config_directory'],
        AGENTFLOW_STATE_DIR=definition['execution']['state_directory'],
        PYTHONPATH=os.pathsep.join(map(str, (installation / 'local', installation / 'upstream/platform',
                                           installation / 'upstream/temporal', installation / 'upstream'))))
    script = Path(__file__).parent / 'fixtures/training_executor_client.py'

    def command(mode):
        return [sys.executable, '-B', '-P', str(script), mode, str(folder)]

    def run(mode):
        return subprocess.run(command(mode), env=environment, text=True, capture_output=True, timeout=15)

    return folder, environment, command, run


def test_native_admission_holds_the_original_lock_and_rejection_has_no_business_result(native_executor):
    import select
    import subprocess

    folder, environment, command, run = native_executor
    request = (folder / 'request.json').read_bytes()
    with subprocess.Popen(command('hold-admission'), env=environment, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as holder:
        try:
            assert select.select([holder.stdout], [], [], 15)[0], 'Admission did not become ready'
            admitted = json.loads(holder.stdout.readline())
            assert admitted == {'admitted': json.loads(request), 'folder': str(folder)}
            competitor = run('no-hook')
            assert competitor.returncode == 0, competitor.stderr
            assert json.loads(competitor.stdout)['error_type'] == 'BlockingIOError'
            stdout, stderr = holder.communicate('\n', timeout=15)
            assert holder.returncode == 0, stderr
            assert json.loads(stdout)['error'] == 'Admission declined before business execution'
        finally:
            if holder.poll() is None:
                holder.kill()
                holder.communicate()
    assert (folder / 'request.json').read_bytes() == request
    assert {p.name for p in folder.iterdir()} == {'request.json', 'executor.lock'}


def test_native_started_written_after_outer_precheck_prevents_a_second_admission(native_executor):
    import select
    import subprocess

    folder, environment, command, run = native_executor
    request = (folder / 'request.json').read_bytes()
    with subprocess.Popen(command('prechecked'), env=environment, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as pending:
        try:
            assert select.select([pending.stdout], [], [], 15)[0], 'Outer precheck did not finish'
            assert pending.stdout.readline().strip() == 'prechecked'
            crashed = run('manual-crash')
            assert crashed.returncode == 73, crashed.stderr
            started = (folder / 'started.json').read_bytes()
            stdout, stderr = pending.communicate('\n', timeout=15)
            assert pending.returncode == 0, stderr
            assert 'earlier executor started without a result' in json.loads(stdout)['error']
        finally:
            if pending.poll() is None:
                pending.kill()
                pending.communicate()
    assert (folder / 'request.json').read_bytes() == request and (folder / 'started.json').read_bytes() == started
    assert {p.name for p in folder.iterdir()} == {'request.json', 'executor.lock', 'started.json'}


@pytest.mark.parametrize('checkpoint', ['managed-directory', 'managed-link', 'started-link'])
def test_native_manual_entry_cannot_take_over_partial_or_uncertain_execution(native_executor, checkpoint):
    folder, _, _, run = native_executor
    if checkpoint == 'managed-directory':
        (folder / 'managed-execution').mkdir()
    else:
        name = 'started.json' if checkpoint == 'started-link' else 'managed-execution'
        (folder / name).symlink_to(folder / 'missing-publication')
    original = (folder / 'request.json').read_bytes()
    result = run('no-hook')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['error_type'] == 'Blocked'
    assert not (folder / 'result.json').exists() and not (folder / 'repo.git').exists()
    assert (folder / 'request.json').read_bytes() == original


def test_native_clean_manual_execution_preserves_git_runner_negative_gate_and_completed_read(native_executor):
    folder, _, _, run = native_executor
    request = (folder / 'request.json').read_bytes()
    completed = run('run-clean')
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)['result']
    assert result['state'] == 'SUCCEEDED'
    gate = json.loads((folder / 'gate-report.json').read_bytes())
    assert gate['passed'] is False and 'did not produce evidence.json' in gate['summary']
    assert (folder / 'baseline/.git').is_file() and (folder / 'candidate/.git').is_file()
    assert (folder / 'run-output/execution.log').is_file()
    assert (folder / 'request.json').read_bytes() == request
    (folder / 'managed-execution').mkdir()
    before = {p: p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    observed = run('completed')
    assert observed.returncode == 0, observed.stderr
    assert json.loads(observed.stdout)['result'] == result
    assert all(p.read_bytes() == raw for p, raw in before.items())


def test_cycle_sdk_capacity_counts_metadata_and_rejects_without_truncation():
    pytest.importorskip('temporalio')
    import asyncio
    from temporalio.api.common.v1 import Payloads
    from temporalio.converter import DataConverter
    from temporalio.exceptions import ApplicationError
    from ergora.reference_training_worker import _cycle_capacity

    value = {'reason': 'x' * 32750}
    assert len(json.dumps(value, separators=(',', ':')).encode()) <= 32768
    encoded = asyncio.run(DataConverter.default.encode([value]))
    assert Payloads(payloads=encoded).ByteSize() > 32768
    with pytest.raises(ApplicationError) as failed:
        asyncio.run(_cycle_capacity(value, DataConverter.default))
    assert failed.value.type == 'cycle_activity_capacity_exceeded' and failed.value.non_retryable


@pytest.mark.parametrize('fault', ['normal-validate', 'stop-validate', 'validate-during-shutdown', 'stop-fatal'])
def test_cycle_service_closes_peers_with_real_sdk_lifecycle(monkeypatch, fault):
    """Keep SDK run/shutdown ordering; only its bridge and activity poller are local."""
    pytest.importorskip('temporalio')
    import asyncio
    import signal
    import sys
    from types import ModuleType, SimpleNamespace
    import temporalio.worker
    from ergora import reference_training_worker as service

    sdk_worker = temporalio.worker.Worker

    async def scenario():
        loop = asyncio.get_running_loop()
        handlers, workers = {}, []
        validate_release, cleanup_release = asyncio.Event(), asyncio.Event()
        fatal = RuntimeError(fault)
        failing_index = 1 if fault.startswith('stop-') else 0

        class Bridge:
            def __init__(self, index):
                self.index = index
                self.stopping = asyncio.Event()
                self.validating = asyncio.Event()
                self.finalized = False

            async def validate(self):
                self.validating.set()
                if self.index == failing_index and fault != 'stop-fatal':
                    await validate_release.wait()
                    raise fatal

            def initiate_shutdown(self):
                self.stopping.set()

            async def finalize_shutdown(self):
                self.finalized = True

        class Poller:
            def __init__(self, bridge):
                self.bridge = bridge
                self.running = asyncio.Event()
                self.completing = asyncio.Event()

            async def run(self):
                self.running.set()
                if self.bridge.index == failing_index and fault == 'stop-fatal':
                    await validate_release.wait()
                    raise fatal
                await self.bridge.stopping.wait()

            def notify_shutdown(self):
                pass

            async def drain_poll_queue(self):
                pass

            async def wait_all_completed(self):
                self.completing.set()
                await cleanup_release.wait()

        def construct(client, **config):
            worker = sdk_worker.__new__(sdk_worker)
            worker._plugins = []
            worker._started = False
            worker._shutdown_event = asyncio.Event()
            worker._shutdown_complete_event = asyncio.Event()
            worker._bridge_worker = Bridge(len(workers))
            worker._activity_worker = Poller(worker._bridge_worker)
            worker._workflow_worker = worker._nexus_worker = None
            worker._config = {'on_fatal_error': None, **config}
            workers.append(worker)
            return worker

        connection = ModuleType('perf_temporal.connection')
        async def connect():
            return SimpleNamespace()
        connection.connect = connect
        monkeypatch.setitem(sys.modules, 'perf_temporal.connection', connection)
        monkeypatch.setattr(temporalio.worker, 'Worker', construct)
        monkeypatch.setattr(service, 'create_cycle_activities', lambda _: dict.fromkeys(('inspect', 'start', 'reconcile', 'stop')))
        monkeypatch.setattr(loop, 'add_signal_handler', lambda sig, callback: handlers.setdefault(sig, callback))
        monkeypatch.setattr(loop, 'remove_signal_handler', lambda sig: handlers.pop(sig, None))
        serving = asyncio.create_task(service._serve_cycle())
        try:
            while len(workers) < 2:
                await asyncio.sleep(0)
            await asyncio.gather(*(worker._bridge_worker.validating.wait() for worker in workers))
            if fault == 'validate-during-shutdown':
                handlers[signal.SIGTERM]()
                await asyncio.wait_for(workers[0]._shutdown_event.wait(), 2)
            validate_release.set()
            if fault == 'stop-fatal':
                await asyncio.wait_for(workers[1]._activity_worker.completing.wait(), 2)
                # Fatal is known while the failing worker still owns an active cleanup.
                await asyncio.wait_for(workers[0]._bridge_worker.stopping.wait(), 2)
                assert not serving.done() and not workers[1]._bridge_worker.finalized
                serving.cancel()
                await asyncio.sleep(0)
                serving.cancel()
            cleanup_release.set()
            done, _ = await asyncio.wait((serving,), timeout=2)
            assert done, 'Service hung after SDK run validation failed'
            with pytest.raises(RuntimeError, match=fault):
                serving.result()
            assert all(worker._bridge_worker.finalized for index, worker in enumerate(workers)
                       if index != failing_index or fault == 'stop-fatal')
            assert not [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        finally:
            validate_release.set()
            cleanup_release.set()
            # Only rescue the known-broken baseline's orphan shutdown waiter so
            # pytest itself can exit. Product code never accesses SDK events.
            for worker in workers:
                worker._shutdown_complete_event.set()
            await asyncio.gather(serving, return_exceptions=True)

    asyncio.run(scenario())
