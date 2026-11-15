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


def test_cycle_execution_sdk_rejects_untrusted_input_before_any_operation(monkeypatch, tmp_path):
    pytest.importorskip('temporalio')
    import asyncio
    from dataclasses import replace
    from types import SimpleNamespace
    from temporalio.converter import DataConverter
    from temporalio.exceptions import ApplicationError
    from temporalio.testing import ActivityEnvironment
    from ergora import reference_training_worker as worker

    def forbidden(*args, **kwargs):
        raise AssertionError('Rejected SDK input cannot create a supervised operation')

    monkeypatch.setattr(worker, '_CycleOperation', forbidden)
    activities = worker.create_cycle_activities(SimpleNamespace(namespace='default', data_converter=DataConverter.default))
    original = {'protocol': 'ergora-training-cycle-v1', 'control_home': str(tmp_path),
        'project': 'demo', 'cycle_id': 'first', 'input_sha256': 'a' * 64, 'authorization_sha256': 'b' * 64}
    for action in ('request-execution-or-observe', 'observe-candidate'):
        for request, changes in (({'workflow_input': original, 'ordinal': 1}, {}),
                ({'workflow_input': original, 'ordinal': 0, 'confirm': True}, {}),
                ({'workflow_input': original | {'source': 'caller'}, 'ordinal': 0}, {}),
                ({'workflow_input': original, 'ordinal': 0}, {'is_local': True}),
                ({'workflow_input': original, 'ordinal': 0}, {'namespace': 'foreign'}),
                ({'workflow_input': original, 'ordinal': 0}, {'workflow_namespace': 'foreign'}),
                ({'workflow_input': original, 'ordinal': 0}, {'workflow_type': 'OtherWorkflow'}),
                ({'workflow_input': original, 'ordinal': 0}, {'activity_type': worker.protocol.CYCLE_ACTIVITY_NAMES['start']})):
            environment = ActivityEnvironment()
            environment.info = replace(environment.info, workflow_id='original', workflow_run_id='run',
                workflow_type='TrainingCycleWorkflow', workflow_namespace='default', namespace='default',
                activity_type=worker.protocol.CYCLE_ACTIVITY_NAMES[action], task_queue=worker.protocol.CYCLE_TASK_QUEUE)
            environment.info = replace(environment.info, **changes)
            with pytest.raises(ApplicationError) as failed:
                asyncio.run(environment.run(activities[action], request))
            assert failed.value.type == 'cycle_activity_request_rejected' and failed.value.non_retryable


@pytest.mark.parametrize('control,wall,cleanup,attempt', [(30, 900, 170, 1), (2, 900, 170, 1),
                                                         (30, 4, 2, 1), (30, 900, 170, 2)])
def test_cycle_execution_sdk_keeps_one_work_window_without_parent_file_reads(
        monkeypatch, tmp_path, control, wall, cleanup, attempt):
    pytest.importorskip('temporalio')
    import asyncio
    from dataclasses import replace
    from types import SimpleNamespace
    from temporalio.converter import DataConverter
    from temporalio.testing import ActivityEnvironment
    from ergora import budget_clock, reference_training_worker as worker, training_cycles

    clock = budget_clock.authorize(wall)
    authorization = {'schema_version': 2, 'control_home': str(tmp_path), 'project': 'demo', 'cycle_id': 'first',
                     'input_sha256': 'a' * 64, 'clock': clock}
    authorization['sha256'] = training_cycles._sha(authorization)
    snapshot = {'authorization': authorization,
        'policy': {'wall_seconds': wall, 'cleanup_seconds': cleanup, 'control_timeout_seconds': control},
        'candidates': [{'ordinal': 0, 'experiment_id': 'alpha', 'manifest_sha256': 'b' * 64}]}
    workflow_input = {key: authorization[key] for key in ('control_home', 'project', 'cycle_id', 'input_sha256')}
    workflow_input.update(protocol='ergora-training-cycle-v1', authorization_sha256=authorization['sha256'])
    seen = []

    async def observed(operation):
        seen.append(operation)
        result = {'status': 'observed', 'facts': {'source_operation_id': operation.identity['operation_id'],
            'budget': {'state': 'valid', 'work_remaining_seconds': wall - cleanup,
                'total_remaining_seconds': wall, 'control_timeout_seconds': control,
                'boot_id': clock['boot_id'], 'boottime_ns': clock['boottime_ns'], 'observed_at': clock['authorized_at']}}}
        if operation.identity['mode'] == 'inspect-controller-activity':
            result.update(status='inspected', snapshot=snapshot,
                          controller={'workflow_id': 'original', 'run_id': 'run', 'intent_sha256': 'c' * 64})
        return operation.observation(result)

    def forbidden(*args, **kwargs):
        raise AssertionError('SDK parent must not read business records or result refs')

    monkeypatch.setattr(worker._CycleOperation, 'run', observed)
    monkeypatch.setattr(worker.protocol, 'read_raw', forbidden)
    monkeypatch.setattr(worker.State, 'project', forbidden)
    activities = worker.create_cycle_activities(SimpleNamespace(namespace='default', data_converter=DataConverter.default))
    env = ActivityEnvironment()
    env.info = replace(env.info, workflow_id='original', workflow_run_id='run', workflow_type='TrainingCycleWorkflow',
        workflow_namespace='default', namespace='default', task_queue=worker.protocol.CYCLE_TASK_QUEUE, attempt=attempt,
        activity_type=worker.protocol.CYCLE_ACTIVITY_NAMES['request-execution-or-observe'])
    envelope = asyncio.run(env.run(activities['request-execution-or-observe'], {'workflow_input': workflow_input, 'ordinal': 0}))
    cold, ordinary = seen
    assert ordinary.identity['mode'] == ('request-execution-candidate' if attempt == 1 else 'observe-candidate')
    original = cold.payload['bootstrap']
    window = ordinary.payload['bootstrap']
    assert window['started_ns'] == original['started_ns']
    assert original['deadline_ns'] - original['started_ns'] == 10_000_000_000
    assert window['deadline_ns'] == min(original['deadline_ns'], window['started_ns'] + control * 1_000_000_000,
                                       clock['boottime_ns'] + (wall - cleanup) * 1_000_000_000)
    assert worker.protocol.cycle_operation_remaining(ordinary.payload) <= min(10, control, wall - cleanup)
    assert envelope['schema_version'] == 2 and envelope['facts']['source_operation_id'] == ordinary.identity['operation_id']


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
        monkeypatch.setattr(service, 'create_cycle_activities', lambda _: dict.fromkeys(service.protocol.CYCLE_ACTIVITY_NAMES))
        monkeypatch.setattr(loop, 'add_signal_handler', lambda sig, callback: handlers.setdefault(sig, callback))
        monkeypatch.setattr(loop, 'remove_signal_handler', lambda sig: handlers.pop(sig, None))
        serving = asyncio.create_task(service._serve_cycle())
        try:
            while len(workers) < 2:
                await asyncio.sleep(0)
            assert workers[0]._config['workflows'] == [service.create_cycle_workflow()]
            assert 'workflows' not in workers[1]._config
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


@pytest.fixture
def cycle_workflow():
    """Real default sandbox and SDK activation loop, with explicit remote activity results."""
    pytest.importorskip('temporalio')
    import asyncio
    from copy import deepcopy
    from dataclasses import replace
    from datetime import datetime, timezone
    from temporalio import workflow
    from temporalio.api.common.v1 import Payloads
    from temporalio.api.failure.v1 import Failure
    from temporalio.bridge.proto import activity_result as ar, workflow_activation as wa
    from temporalio.converter import DataConverter
    from temporalio.worker._workflow_instance import WorkflowInstanceDetails
    from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner
    from temporalio.worker.workflow_sandbox._runner import _fake_info
    from ergora.reference_training_worker import create_cycle_workflow

    class Harness:
        original = {'protocol': 'ergora-training-cycle-v1', 'control_home': str(Path.cwd().anchor),
            'project': 'demo', 'cycle_id': 'first', 'input_sha256': 'a' * 64, 'authorization_sha256': 'b' * 64}

        def __init__(self):
            self.converter = DataConverter.default.payload_converter
            self.time = 0
            self.commands = []
            async def create():
                cls = create_cycle_workflow()
                assert (cls.__module__, cls.__name__, cls.__qualname__) == (
                    'ergora.reference_training_worker', 'TrainingCycleWorkflow', 'TrainingCycleWorkflow')
                runner = SandboxedWorkflowRunner()
                defn = workflow._Definition.must_from_class(cls)
                runner.prepare_workflow(defn)
                return runner.create_instance(WorkflowInstanceDetails(
                    payload_converter_factory=DataConverter.default._new_internal_payload_converter,
                    failure_converter_class=DataConverter.default.failure_converter_class,
                    interceptor_classes=[], defn=defn,
                    info=replace(_fake_info, workflow_id='parent', run_id='parent-run',
                        workflow_type='TrainingCycleWorkflow', namespace='default',
                        task_queue='ergora-training-cycle-v1'), randomness_seed=1, extern_functions={},
                    disable_eager_activity_execution=False, worker_level_failure_exception_types=[],
                    patch_activation_callback=None, last_completion_result=Payloads(), last_failure=Failure()))
            self.instance = asyncio.run(create())

        def activate(self, **job):
            history_length = job.pop('history_length', 10)
            history_size = job.pop('history_size', 1000)
            self.time = job.pop('at', self.time)
            activation = wa.WorkflowActivation(run_id='parent-run', history_length=history_length,
                history_size_bytes=history_size, jobs=[wa.WorkflowActivationJob(**job)])
            activation.timestamp.FromDatetime(datetime.fromtimestamp(self.time, timezone.utc))
            completion = self.instance.activate(activation)
            assert completion.HasField('successful'), completion
            commands = list(completion.successful.commands)
            self.commands.extend(commands)
            return commands

        def start(self):
            return self.activate(initialize_workflow=wa.InitializeWorkflow(workflow_type='TrainingCycleWorkflow',
                workflow_id='parent', arguments=self.converter.to_payloads([self.original]),
                randomness_seed=1, first_execution_run_id='parent-run', original_execution_run_id='parent-run', attempt=1))

        def result(self, command, value, **changes):
            return self.activate(resolve_activity=wa.ResolveActivity(seq=command.schedule_activity.seq,
                result=ar.ActivityResolution(completed=ar.Success(result=self.converter.to_payload(value)))), **changes)

        def timer(self, commands, **changes):
            timer = next(command.start_timer for command in commands if command.HasField('start_timer'))
            return self.activate(fire_timer=wa.FireTimer(seq=timer.seq), **changes)

        def signal(self, request, **changes):
            return self.activate(signal_workflow=wa.SignalWorkflow(signal_name='request_stop',
                input=self.converter.to_payloads([request])), **changes)

        def cancel(self):
            return self.activate(cancel_workflow=wa.CancelWorkflow(reason='fixture cancellation'))

        def query(self):
            commands = self.activate(query_workflow=wa.QueryWorkflow(query_id='status-query', query_type='status'))
            response = next(c.respond_to_query for c in commands if c.HasField('respond_to_query'))
            return self.converter.from_payloads([response.succeeded.response])[0]

        def envelope(self, action='observe-candidate', *, submitted=False, queued=False, work=1000, total=1100):
            source = '1' * 32
            value = {'schema_version': 2, 'protocol': 'ergora-training-cycle-activity-v2', 'action': action,
                'status': 'observed', 'workflow_input': deepcopy(self.original),
                'controller': {'workflow_id': 'parent', 'run_id': 'parent-run', 'intent_sha256': 'c' * 64},
                'observation': {'total_remaining_seconds': total, 'boot_id': 'original-boot'},
                'inspection': {'operation_id': source}, 'operations': [], 'runtime_status': 'queried'}
            if action in ('start', 'reconcile', 'stop'):
                value.update(schema_version=1, protocol='ergora-training-cycle-activity-v1')
                return value
            binding = {'experiment_id': 'alpha', 'manifest_sha': 'd' * 64, 'candidate_sha': '1' * 40, 'baseline_sha': '2' * 40}
            value['facts'] = {'source_operation_id': source,
                'budget': {'state': 'valid' if work > 0 else 'exhausted', 'work_remaining_seconds': work,
                    'total_remaining_seconds': total, 'control_timeout_seconds': 30,
                    'boot_id': 'original-boot', 'boottime_ns': 123, 'observed_at': 'unused'},
                'candidate': {'ordinal': 0, 'experiment_id': 'alpha', 'manifest_sha256': 'd' * 64,
                    'project_revision': 1, 'current_project_matches': True, 'parent_stop_visible': False},
                'submission': {'state': 'submitted' if submitted else 'not_recorded',
                    'intent_sha256': 'e' * 64 if submitted else None, 'workflow_id': 'child',
                    'run_id': 'child-run' if submitted else None, 'attempt_saved': submitted, 'result_saved': submitted},
                'execution': {'state': 'not_requested', 'request_sha256': None, 'record_sha256': {},
                    'reap_record_observed': False, 'durable_stop_confirmed': None, 'executor_stop_confirmed': None},
                'runtime': {'state': 'queried' if queued else 'not_queried',
                    'workflow_id': 'child' if queued else None, 'run_id': 'child-run' if queued else None,
                    'temporal_status': 'RUNNING' if queued else None, 'terminal': False if queued else None,
                    'phase': 'QUEUED' if queued else None, 'binding': binding if queued else None,
                    'job_id': 'job' if queued else None},
                'native': {'state': 'QUEUED' if queued else 'not_queried', 'job_id': 'job' if queued else None},
                'request_outcome': 'not_attempted'}
            return value

        def activity(self, commands):
            return next(command for command in commands if command.HasField('schedule_activity'))

        def scheduled(self, action):
            suffix = '.' + action + ('.v2' if action in ('observe-candidate', 'request-execution-or-observe') else '.v1')
            return [c.schedule_activity for c in self.commands if c.HasField('schedule_activity')
                    and c.schedule_activity.activity_type.endswith(suffix)]

    return Harness


def test_cycle_workflow_delays_request_and_keeps_the_first_round_gate(cycle_workflow):
    h = cycle_workflow()
    cold = h.activity(h.start())
    start = h.activity(h.result(cold, h.envelope(), at=1))
    assert start.schedule_activity.activity_type.endswith('.start.v1')
    commands = h.result(start, h.envelope('start'), at=2)
    observe = h.activity(h.timer(commands, at=3))
    early = h.envelope(submitted=True, queued=True)
    early.update(status='unknown')
    early['facts']['runtime'].update(phase='SUBMITTING', job_id=None)
    early['facts']['native'] = {'state': 'unconfirmed', 'job_id': None}
    commands = h.result(observe, early, at=4)
    assert not h.scheduled('request-execution-or-observe')
    observe = h.activity(h.timer(commands, at=5))
    request = h.activity(h.result(observe, h.envelope(submitted=True, queued=True), at=6))
    assert request.schedule_activity.retry_policy.maximum_attempts == 1
    requested = h.envelope('request-execution-or-observe', submitted=True, queued=True)
    requested['facts']['request_outcome'] = 'requested'
    requested['facts']['execution'].update(state='requested', request_sha256='f' * 64, record_sha256={'request': 'f' * 64})
    commands = h.result(request, requested, at=7)
    observe = h.activity(h.timer(commands, at=8))
    native_first = h.envelope(submitted=True, queued=True)
    native_first['facts']['execution'] = requested['facts']['execution'].copy()
    native_first['facts']['native']['state'] = 'SUCCEEDED'
    commands = h.result(observe, native_first, at=9)
    assert h.query()['measurement_accepted'] is None
    observe = h.activity(h.timer(commands, at=10))
    native_first['facts']['execution'].update(state='stopped', durable_stop_confirmed=True, executor_stop_confirmed=True)
    commands = h.result(observe, native_first, at=11)
    assert not any(c.HasField('complete_workflow_execution') for c in commands)
    observe = h.activity(h.timer(commands, at=12))
    native_first['facts']['runtime']['phase'] = 'AWAITING_RELEASE'
    commands = h.result(observe, native_first, at=13)
    outcome = h.converter.from_payloads([next(c.complete_workflow_execution.result for c in commands
                                            if c.HasField('complete_workflow_execution'))])[0]
    assert outcome['outcome'] == 'first_round_observed_c1d_required' and outcome['ordinal'] == 0
    assert outcome['continuation'] == 'disabled_until_c1d' and outcome['measurement_accepted'] is None
    assert len(h.scheduled('start')) == len(h.scheduled('request-execution-or-observe')) == 1
    assert not h.scheduled('stop')


@pytest.mark.parametrize('effect', ['start', 'request-execution-or-observe'])
def test_cycle_workflow_lost_effect_completion_never_regrants_its_command(cycle_workflow, effect):
    h = cycle_workflow()
    cold = h.activity(h.start())
    if effect == 'start':
        command = h.activity(h.result(cold, h.envelope(), at=1))
    else:
        commands = h.result(cold, h.envelope(submitted=True), at=1)
        observe = h.activity(h.timer(commands, at=2))
        command = h.activity(h.result(observe, h.envelope(submitted=True, queued=True), at=3))
    from temporalio.api.failure.v1 import ActivityFailureInfo, Failure, TimeoutFailureInfo
    from temporalio.bridge.proto import activity_result as ar, workflow_activation as wa
    failure = Failure(message='Completion unavailable', activity_failure_info=ActivityFailureInfo(),
                      cause=Failure(message='RPC deadline', timeout_failure_info=TimeoutFailureInfo()))
    commands = h.activate(resolve_activity=wa.ResolveActivity(seq=command.schedule_activity.seq,
        result=ar.ActivityResolution(failed=ar.Failure(failure=failure))))
    observe = h.activity(h.timer(commands, at=4))
    # Even an absent request after a scheduled command cannot grant that effect again.
    value = h.envelope(submitted=effect != 'start', queued=effect != 'start')
    commands = h.result(observe, value, at=5)
    assert len(h.scheduled(effect)) == 1
    if effect != 'start':
        assert h.query()['request_scheduled'] is True
        observe = h.activity(h.timer(commands, at=6))
        h.result(observe, value, at=7)
        assert len(h.scheduled(effect)) == 1


def test_cycle_workflow_budget_uses_schedule_time_and_v1_only_narrows_total(cycle_workflow):
    h = cycle_workflow()
    cold = h.activity(h.start())
    start = h.activity(h.result(cold, h.envelope(work=9, total=12), at=4))
    assert start.schedule_activity.schedule_to_close_timeout.ToTimedelta().total_seconds() == 5
    commands = h.result(start, h.envelope('start', total=1000), at=5)
    observe = h.activity(h.timer(commands, at=6))
    assert observe.schedule_activity.schedule_to_close_timeout.ToTimedelta().total_seconds() == 3
    commands = h.result(observe, h.envelope(submitted=True, work=6, total=1000), at=7)
    observe = h.activity(h.timer(commands, at=8))
    assert observe.schedule_activity.schedule_to_close_timeout.ToTimedelta().total_seconds() == 1
    stop = h.activity(h.result(observe, h.envelope(submitted=True, queued=True, work=1000, total=1000), at=10))
    assert stop.schedule_activity.task_queue == 'ergora-training-cycle-stop-v1'
    assert stop.schedule_activity.schedule_to_close_timeout.ToTimedelta().total_seconds() == 2
    assert not h.scheduled('request-execution-or-observe')


@pytest.mark.parametrize('cancel', [False, True])
def test_cycle_workflow_stop_bypasses_pending_normal_and_survives_repeated_cancel(cycle_workflow, cancel):
    h = cycle_workflow()
    cold = h.activity(h.start())
    commands = h.result(cold, h.envelope(submitted=True), at=1)
    normal = h.activity(h.timer(commands, at=2))
    commands = h.cancel() if cancel else h.signal({'workflow_input': h.original, 'reason': 'Stop original candidate'})
    assert any(c.HasField('request_cancel_activity') and c.request_cancel_activity.seq == normal.schedule_activity.seq for c in commands)
    stop = h.activity(commands)
    assert stop.schedule_activity.task_queue == 'ergora-training-cycle-stop-v1'
    assert not h.cancel()
    assert not h.cancel()
    commands = h.result(stop, h.envelope('stop'), at=3)
    assert len(h.scheduled('stop')) == 1
    assert any(c.HasField('cancel_workflow_execution') for c in commands)
    assert h.query()['stop_durable'] is h.query()['admission_drained'] is None


@pytest.mark.parametrize('bound', [{'history_length': 8000}, {'history_size': 8 * 1024 * 1024}])
def test_cycle_workflow_history_bound_reserves_only_stop(cycle_workflow, bound):
    h = cycle_workflow()
    cold = h.activity(h.start())
    stop = h.activity(h.result(cold, h.envelope(), at=1, **bound))
    assert stop.schedule_activity.activity_type.endswith('.stop.v1')
    assert not h.scheduled('start') and not h.scheduled('request-execution-or-observe')


def test_cycle_workflow_counts_failed_observations_and_stops_before_257(cycle_workflow):
    h = cycle_workflow()
    cold = h.activity(h.start())
    commands = h.result(cold, h.envelope(submitted=True), at=1)
    from temporalio.api.failure.v1 import ActivityFailureInfo, Failure
    from temporalio.bridge.proto import activity_result as ar, workflow_activation as wa
    for count in range(2, 257):
        observe = h.activity(h.timer(commands, at=count))
        commands = h.activate(resolve_activity=wa.ResolveActivity(seq=observe.schedule_activity.seq,
            result=ar.ActivityResolution(failed=ar.Failure(failure=Failure(
                message='Read unavailable', activity_failure_info=ActivityFailureInfo())))))
    assert len(h.scheduled('observe-candidate')) == 256
    assert len(h.scheduled('stop')) == 1 and h.query()['observation_count'] == 256


def test_cycle_workflow_signal_rejections_do_not_poison_the_next_valid_stop(cycle_workflow):
    h = cycle_workflow()
    cold = h.activity(h.start())
    oversized = {'workflow_input': h.original, 'reason': ''}
    oversized['reason'] = 'x' * (32768 - len(json.dumps(oversized, separators=(',', ':')).encode()))
    assert len(json.dumps(oversized, separators=(',', ':')).encode()) == 32768
    assert h.converter.to_payloads_wrapper([oversized]).ByteSize() > 32768
    h.signal(oversized)
    assert h.query()['last_signal_rejection'] == 'signal_capacity_exceeded'
    h.signal({'workflow_input': h.original | {'cycle_id': 'foreign'}, 'reason': 'Wrong identity'})
    assert h.query()['last_signal_rejection'] == 'signal_identity_or_shape_rejected'
    h.signal({'workflow_input': h.original, 'reason': 'First complete reason'})
    h.signal({'workflow_input': h.original, 'reason': 'Later reason'})
    stop = h.activity(h.result(cold, h.envelope(), at=1))
    request = h.converter.from_payloads(stop.schedule_activity.arguments)[0]
    assert request['reason'] == 'First complete reason' and not h.scheduled('start')
    commands = h.result(stop, h.envelope('stop'), at=2)
    outcome = h.converter.from_payloads([next(c.complete_workflow_execution.result for c in commands
                                            if c.HasField('complete_workflow_execution'))])[0]
    assert outcome['outcome'] == 'needs_reconciliation' and outcome['stop_activity_status'] == 'returned'
    assert outcome['stop_durable'] is outcome['admission_drained'] is outcome['executor_stop_confirmed'] is None


@pytest.mark.parametrize('fault', ['controller', 'source', 'project', 'budget', 'runtime-job', 'GATE_FAILED'])
def test_cycle_workflow_unconfirmed_identity_never_requests_execution(cycle_workflow, fault):
    h = cycle_workflow()
    cold = h.activity(h.start())
    value = h.envelope(submitted=True, queued=True)
    if fault == 'controller':
        value['controller']['run_id'] = 'foreign'
    elif fault == 'source':
        value['facts']['source_operation_id'] = '2' * 32
    elif fault == 'project':
        value['facts']['candidate']['current_project_matches'] = None
    elif fault == 'budget':
        value['facts']['budget']['work_remaining_seconds'] = True
    elif fault == 'runtime-job':
        value['facts']['runtime']['job_id'] = 'foreign'
    else:
        value['facts']['runtime'].update(phase=fault, terminal=True, temporal_status='COMPLETED')
    h.result(cold, value, at=1)
    assert not h.scheduled('start') and not h.scheduled('request-execution-or-observe')
    assert h.query()['measurement_accepted'] is None
