"""Explicit native facts stay separate from saved training records and adoption."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys

import pytest

from ergora import reference, training
from test_training import experiments, registration
from test_reference import prepared_training_installation


@pytest.fixture(scope='module')
def installation(tmp_path_factory):
    import venv

    root = tmp_path_factory.mktemp('training-reference-installation') / 'managed native'
    if sys.platform == 'linux':
        reference.prepare_training(root, protocol=reference.TRAINING_PROTOCOL)
        venv.EnvBuilder(with_pip=False).create(root / '.venv')
    else:
        shutil.copytree(reference.ROOT / 'platform', root)
        shutil.copyfile(reference.DATA / 'native-runtime' / (reference.TRAINING_PROTOCOL + '.json'),
                        root / 'ergora-native-runtime.json')
    return root


@pytest.mark.parametrize('action', ['run-local', 'approve'])
def test_native_cli_keeps_the_original_loader_at_each_sdk_use(
        prepared_training_installation, tmp_path, action):
    import hashlib
    import os
    import subprocess
    import venv

    pytest.importorskip('temporalio')
    root, _ = prepared_training_installation
    state = tmp_path / 'native-state'
    spec = state / 'training/specs/alpha.json'
    spec.parent.mkdir(parents=True)
    manifest = state / 'training/manifests/alpha.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({'execution': {'operation': 'full-verify'}}))
    binding = {'experiment_id': 'alpha', 'manifest_sha': hashlib.sha256(manifest.read_bytes()).hexdigest(),
               'candidate_sha': 'b' * 40, 'baseline_sha': 'c' * 40}
    value = {'binding': binding, 'manifest_uri': (tmp_path / 'manifest.json').as_uri()}
    environment = {**os.environ, 'AGENTFLOW_STATE_DIR': str(state), 'AGENTFLOW_CONFIG_DIR': str(tmp_path / 'config'),
        'PYTHONPATH': os.pathsep.join(str(root / part) for part in
            ('local', 'upstream/platform', 'upstream/temporal', 'upstream'))}
    program = '''import json,sys
from pathlib import Path
from types import SimpleNamespace
from agent_platform import training
action=sys.argv[1]
calls=[]
if action=='approve' and sys.argv[2]=='sdk':
    from perf_temporal import connection
    from perf_temporal.models import Binding
    binding=Binding(**json.loads((training.TRAINING/'specs/alpha.json').read_bytes())['binding'])
    class Handle:
        async def query(self, *args):
            return SimpleNamespace(phase='AWAITING_RELEASE', binding=binding, evidence_sha='d'*64)
    async def connect():
        return SimpleNamespace(get_workflow_handle=lambda wid:Handle())
    connection.connect=connect
    def send(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0)
    training.subprocess.run=send
arguments=([action,'alpha','--confirm-manifest-sha','0'*64] if action=='run-local'
           else [action,'alpha','--evidence-sha','d'*64])
try:
    result=training.cli(arguments)
    print(json.dumps({'result':result,'calls':calls}))
except (ValueError, TypeError, RuntimeError, ModuleNotFoundError) as error:
    print(json.dumps({'error_type':type(error).__name__,'error':str(error),'calls':calls}))
'''

    def run(python, mode):
        result = subprocess.run([str(python), '-B', '-P', '-c', program, action, mode], env=environment,
                                capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    # Both branches execute the original client's Experiment/Binding validation.
    spec.write_text(json.dumps({**value, 'binding': {**binding, 'candidate_sha': 'invalid'}}))
    rejected = run(sys.executable, 'sdk')
    assert rejected['error_type'] == 'ValueError' and 'candidate_sha' in rejected['error']
    assert not rejected['calls'] and not (state / 'training/approvals').exists()
    spec.write_text(json.dumps(value))
    loaded = run(sys.executable, 'sdk')
    if action == 'run-local':
        assert loaded['error_type'] == 'Blocked' and 'Confirm the exact immutable manifest SHA' in loaded['error']
        assert not loaded['calls'] and not (state / 'training/jobs').exists()
    else:
        assert loaded['result'] is None and len(loaded['calls']) == 1
        assert loaded['calls'][0][1:4] == ['-m', 'perf_temporal.client', 'release']
        approval, = (state / 'training/approvals').glob('*.json')
        saved = json.loads(approval.read_bytes())
        assert saved['binding'] == binding and saved['evidence_sha256'] == 'd' * 64
        before = approval.read_bytes()
    isolated = tmp_path / 'no-sdk'
    venv.EnvBuilder(with_pip=False).create(isolated)
    missing = run(isolated / 'bin/python', 'no-sdk')
    assert missing['error_type'] == 'ModuleNotFoundError' and 'temporalio' in missing['error']
    assert not missing['calls']
    if action == 'approve':
        assert approval.read_bytes() == before


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


@pytest.fixture
def cycle_sdk_completion():
    """Run the SDK activity worker through its final result/failure encoder."""
    pytest.importorskip('temporalio')
    import asyncio
    from types import SimpleNamespace
    from temporalio import activity
    from temporalio.api.common.v1 import WorkflowExecution
    from temporalio.bridge.proto.activity_task import Start
    from temporalio.common import MetricMeter
    from temporalio.converter import DataConverter
    from temporalio.worker._activity import _ActivityWorker, _RunningActivity

    async def complete(fn, value, *, converter=DataConverter.default, sdk_timeout_seconds=30, **source):
        completions = []
        cancelled = source.pop('cancelled_by_request', False)
        class Bridge:
            async def complete_activity_task(self, completion):
                completions.append(completion)

        declared = activity._Definition.must_from_callable(fn).name.endswith('.v4')
        worker = _ActivityWorker(bridge_worker=Bridge, task_queue=source.pop('task_queue', 'ergora-training-cycle-v3' if declared else 'ergora-training-cycle-v2'),
            activities=[fn], activity_executor=None, shared_state_manager=None, data_converter=converter,
            interceptors=[], metric_meter=MetricMeter.noop, client=SimpleNamespace(namespace='default'),
            encode_headers=False)
        definition = activity._Definition.must_from_callable(fn)
        start = Start(activity_id='candidate-0-1', activity_type=definition.name, attempt=1,
            workflow_namespace='default', workflow_type='TrainingCycleWorkflowV3' if declared else 'TrainingCycleWorkflowV2',
            workflow_execution=WorkflowExecution(workflow_id='parent', run_id='parent-run'),
            input=await converter.encode([value]))
        if declared:
            from datetime import datetime, timezone
            start.scheduled_time.FromDatetime(datetime.now(timezone.utc))
            start.started_time.CopyFrom(start.scheduled_time)
            start.schedule_to_close_timeout.FromSeconds(sdk_timeout_seconds)
            start.start_to_close_timeout.FromSeconds(sdk_timeout_seconds)
        for key, item in source.items():
            if key == 'workflow_execution':
                start.workflow_execution.CopyFrom(item)
            else:
                setattr(start, key, item)
        running = _RunningActivity(pending_heartbeats=asyncio.Queue(), cancelled_by_request=cancelled)
        token = b'local-completion'
        worker._running_activities[token] = running
        await worker._handle_start_activity_task(token, start, running)
        return completions[0]

    return complete


@pytest.fixture
def cycle_capacity_converter():
    """Expand legal SDK metadata without changing the supplied business shape."""
    pytest.importorskip('temporalio')
    from dataclasses import replace
    from temporalio.api.common.v1 import Payloads
    from temporalio.converter import DataConverter, DefaultPayloadConverter
    from temporalio.exceptions import ApplicationError
    from ergora.reference_training_worker import _CycleFailureConverter

    def create(wire, size):
        class MetadataConverter(DefaultPayloadConverter):
            def to_payloads(self, values):
                payloads = super().to_payloads(values)
                for value, payload in zip(values, payloads):
                    if not isinstance(value, dict) or value.get('protocol') != wire:
                        continue
                    if size == 'raised-failure':
                        raise ApplicationError('完整编码失败' + '界' * 12000, type='original-serialization-error')
                    payload.metadata['sdk-capacity-padding'] = b''
                    for _ in range(3):
                        count = size - Payloads(payloads=[payload]).ByteSize()
                        payload.metadata['sdk-capacity-padding'] += b'x' * max(0, count)
                        excess = Payloads(payloads=[payload]).ByteSize() - size
                        if excess > 0:
                            payload.metadata['sdk-capacity-padding'] = payload.metadata['sdk-capacity-padding'][:-excess]
                return payloads
        return replace(DataConverter.default, payload_converter_class=MetadataConverter,
                       failure_converter_class=_CycleFailureConverter)

    return create


@pytest.mark.parametrize('source', ['request', 'inspection', 'operation', 'cancel'])
def test_cycle_v3_wrapper_failure_does_not_export_original_error(cycle_sdk_completion, monkeypatch, source):
    if sys.platform != 'linux' and source != 'request':
        pytest.skip('Valid cycle operation construction requires the original Linux boot clock')
    import asyncio
    from types import SimpleNamespace
    from temporalio.converter import DataConverter
    from temporalio.exceptions import CancelledError
    from ergora import reference_training_worker as worker

    activities = worker.create_cycle_activities(SimpleNamespace(namespace='default', data_converter=DataConverter.default), 2)
    original = {'protocol': 'ergora-training-cycle-v2', 'control_home': '/', 'project': 'demo',
        'cycle_id': 'first', 'input_sha256': 'a' * 64, 'authorization_sha256': 'b' * 64}
    raw = 'Complete original small error marker'
    if source == 'request':
        original['protocol'] = 'original-raw-error-marker'
    else:
        async def failed(operation):
            if source == 'inspection':
                return operation.observation({'status': 'capacity_exceeded', 'reason': raw})
            if source == 'cancel':
                raise CancelledError('Original SDK cancellation')
            raise ValueError(raw)
        monkeypatch.setattr(worker._CycleOperation, 'run', failed)
    completion = asyncio.run(cycle_sdk_completion(activities['observe-candidate'],
        {'workflow_input': original, 'ordinal': 0, 'predecessor': None}, cancelled_by_request=source == 'cancel'))
    if source == 'cancel':
        assert completion.result.HasField('cancelled')
        assert completion.result.cancelled.failure.HasField('canceled_failure_info')
        return
    failure = completion.result.failed.failure
    expected = {'request': ('cycle_activity_request_rejected', 'Cycle activity request rejected'),
        'inspection': ('cycle_activity_capacity_exceeded', 'Complete cycle activity capacity exceeded'),
        'operation': ('cycle_activity_failed', 'Cycle activity failed')}[source]
    assert failure.application_failure_info.type == expected[0]
    assert failure.application_failure_info.non_retryable
    assert failure.message == expected[1] and raw.encode() not in failure.SerializeToString()
    assert not failure.HasField('cause') and not failure.application_failure_info.details.payloads


@pytest.mark.parametrize('size', [32767, 32768, 32769])
def test_cycle_sdk_completion_measures_the_final_saved_failure(cycle_sdk_completion, tmp_path, size):
    import asyncio
    from dataclasses import replace
    from temporalio import activity
    from temporalio.api.common.v1 import Payload, Payloads
    from temporalio.api.failure.v1 import ApplicationFailureInfo, Failure
    from temporalio.converter import DataConverter, DefaultFailureConverter
    from ergora.reference_training_worker import _CycleFailureConverter

    original = Failure(message='原始完整错误', stack_trace='original traceback',
        cause=Failure(message='original cause', application_failure_info=ApplicationFailureInfo(type='cause')),
        application_failure_info=ApplicationFailureInfo(type='original-type', non_retryable=True,
            details=Payloads(payloads=[Payload(metadata={'encoding': b'json/plain', 'original': b'metadata'}, data=b'{}')])))
    for _ in range(3):
        original.message += 'x' * max(0, size - original.ByteSize())
        if original.ByteSize() > size:
            original.message = original.message[:-(original.ByteSize() - size)]
    assert original.ByteSize() == size
    error = DefaultFailureConverter().from_failure(original, DataConverter.default.payload_converter)

    @activity.defn
    async def fail(value: dict) -> dict:
        raise error

    bounded = replace(DataConverter.default, failure_converter_class=_CycleFailureConverter)
    completion = asyncio.run(cycle_sdk_completion(fail, {}, converter=bounded))
    failure = completion.result.failed.failure
    (tmp_path / 'original.pb').write_bytes(original.SerializeToString())
    (tmp_path / 'completion.pb').write_bytes(completion.SerializeToString())
    if size <= 32768:
        assert failure == original
        decoded = asyncio.run(bounded.decode_failure(failure))
        assert decoded.type == 'original-type' and decoded.details == ({},)
    else:
        assert failure.ByteSize() <= 32768
        assert failure.application_failure_info.type == 'cycle_failure_capacity_exceeded'
        assert failure.application_failure_info.non_retryable
        assert not failure.HasField('cause') and not failure.stack_trace
        assert not failure.application_failure_info.details.payloads


@pytest.mark.parametrize('part', ['traceback', 'cause', 'context', 'details-metadata', 'aggregate'])
def test_cycle_sdk_completion_bounds_the_whole_default_error_tree(cycle_sdk_completion, tmp_path, part):
    import asyncio
    from dataclasses import replace
    from temporalio import activity
    from temporalio.api.failure.v1 import Failure
    from temporalio.converter import DataConverter, DefaultPayloadConverter
    from temporalio.exceptions import ApplicationError
    from ergora.reference_training_worker import _CycleFailureConverter

    converter = DataConverter.default
    error = ApplicationError('original error', type='original-type')
    if part == 'traceback':
        try:
            exec(compile('raise error', '完整 traceback ' + '界' * 12000, 'exec'), {'error': error})
        except ApplicationError as captured:
            error = captured
    elif part in ('cause', 'context'):
        cause = ApplicationError('完整原因' + '界' * 12000, type='original-cause')
        if part == 'cause':
            error.__cause__ = cause
        else:
            error.__context__ = cause
    elif part == 'details-metadata':
        class MetadataConverter(DefaultPayloadConverter):
            def to_payloads(self, values):
                payloads = super().to_payloads(values)
                for payload in payloads:
                    payload.metadata['original-detail-metadata'] = b'x' * 32768
                return payloads
        converter = replace(converter, payload_converter_class=MetadataConverter)
        error = ApplicationError('original error', {'detail': '完整正文'}, type='original-type')
    else:
        # Each detail/cause is legal alone; only the SDK's complete tree exceeds B.
        error = ApplicationError('original error', 'x' * 17000, type='original-type')
        error.__cause__ = ApplicationError('original cause', '界' * 2700, type='original-cause')

    @activity.defn
    async def fail(value: dict) -> dict:
        raise error

    original = asyncio.run(cycle_sdk_completion(fail, {}, converter=converter)).result.failed.failure
    bounded = replace(converter, failure_converter_class=_CycleFailureConverter)
    completion = asyncio.run(cycle_sdk_completion(fail, {}, converter=bounded))
    failure = completion.result.failed.failure
    (tmp_path / 'original.pb').write_bytes(original.SerializeToString())
    (tmp_path / 'completion.pb').write_bytes(completion.SerializeToString())
    assert original.ByteSize() > 32768
    if part == 'aggregate':
        assert original.cause.ByteSize() < 32768
        without_cause = Failure()
        without_cause.CopyFrom(original)
        without_cause.ClearField('cause')
        assert without_cause.ByteSize() < 32768
    assert failure.application_failure_info.type == 'cycle_failure_capacity_exceeded'
    assert failure.application_failure_info.non_retryable and failure.ByteSize() <= 32768
    assert not failure.HasField('cause') and not failure.stack_trace
    assert not failure.application_failure_info.details.payloads


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


@pytest.mark.skipif(sys.platform != 'linux', reason='SDK work windows use the original Linux boot clock')
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


@pytest.mark.parametrize('fault', ['normal-validate', 'stop-validate', 'validate-during-shutdown', 'stop-fatal',
                                  'v3-normal-validate', 'v3-stop-validate', 'v3-validate-during-shutdown', 'v3-stop-fatal',
                                  'v2-normal-validate', 'v2-stop-validate', 'v2-validate-during-shutdown', 'v2-stop-fatal',
                                  'shutdown', 'cancel', 'normal-run-cancel', 'one-normal-run-cancel'])
def test_cycle_service_closes_peers_with_real_sdk_lifecycle(monkeypatch, tmp_path, fault):
    """Keep SDK run/shutdown ordering; only its bridge and activity poller are local."""
    pytest.importorskip('temporalio')
    import asyncio
    import signal
    import sys
    from types import ModuleType, SimpleNamespace
    from temporalio import activity
    from temporalio.client import Client
    from temporalio.converter import DataConverter
    import temporalio.worker
    from ergora import reference_training_worker as service

    sdk_worker = temporalio.worker.Worker

    async def scenario():
        loop = asyncio.get_running_loop()
        handlers, workers = {}, []
        aborted_workers = set()
        run_cancel = fault.endswith('normal-run-cancel')
        validate_release, cleanup_release = asyncio.Event(), asyncio.Event()
        fatal = RuntimeError(fault)
        failing_index = (None if fault in ('shutdown', 'cancel') or run_cancel else 5 if fault.startswith('v3-stop-') else 2 if fault.startswith('v3-')
                         else 4 if fault.startswith('v2-stop-') else 1 if fault.startswith('v2-') else 3 if fault.startswith('stop-') else 0)

        class Bridge:
            def __init__(self, index):
                self.index = index
                self.stopping = asyncio.Event()
                self.validating = asyncio.Event()
                self.finalized = False

            async def validate(self):
                self.validating.set()
                if self.index == failing_index and not fault.endswith('stop-fatal'):
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
                if self.bridge.index == failing_index and fault.endswith('stop-fatal'):
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
            worker._client = client
            workers.append(worker)
            return worker

        connection = ModuleType('perf_temporal.connection')
        client = Client(SimpleNamespace(config=SimpleNamespace(identity='local-cycle-service')))
        async def connect():
            return client
        connection.connect = connect
        monkeypatch.setitem(sys.modules, 'perf_temporal.connection', connection)
        monkeypatch.setattr(temporalio.worker, 'Worker', construct)
        monkeypatch.setattr(loop, 'add_signal_handler', lambda sig, callback: handlers.setdefault(sig, callback))
        monkeypatch.setattr(loop, 'remove_signal_handler', lambda sig: handlers.pop(sig, None))
        serving = asyncio.create_task(service._serve_cycle())
        try:
            async def registered():
                while len(workers) < 6:
                    await asyncio.sleep(0)
            await asyncio.wait_for(registered(), 2)
            assert [item._config['task_queue'] for item in workers] == [service.protocol.CYCLE_TASK_QUEUE,
                service.protocol.CYCLE_TASK_QUEUE_V2, service.protocol.CYCLE_TASK_QUEUE_V3,
                service.protocol.CYCLE_STOP_TASK_QUEUE, service.protocol.CYCLE_STOP_TASK_QUEUE_V2, service.protocol.CYCLE_STOP_TASK_QUEUE_V3]
            assert workers[0]._client is workers[3]._client is client
            assert workers[1]._client is workers[4]._client
            assert workers[1]._client is not client and workers[1]._client.service_client is client.service_client
            assert client.data_converter is DataConverter.default
            assert workers[1]._client.data_converter.failure_converter_class is service._CycleFailureConverter
            for index, version in enumerate((1, 2, 3)):
                assert workers[index]._config['workflows'] == [service.create_cycle_workflow(version)]
                assert 'workflows' not in workers[index + 3]._config
                names = service.protocol.cycle_activity_names(version)
                assert {activity._Definition.must_from_callable(fn).name
                        for fn in workers[index]._config['activities']} == {name for action, name in names.items()
                                                                           if action != 'stop'}
                assert [activity._Definition.must_from_callable(fn).name
                        for fn in workers[index + 3]._config['activities']] == [names['stop']]
            assert all(item._config['max_concurrent_activities'] == 1 for item in workers)
            await asyncio.gather(*(worker._bridge_worker.validating.wait() for worker in workers))
            if fault.endswith('validate-during-shutdown') or fault in ('shutdown', 'cancel') or run_cancel:
                if fault == 'cancel':
                    serving.cancel()
                else:
                    handlers[signal.SIGTERM]()
                await asyncio.wait_for(workers[0]._shutdown_event.wait(), 2)
            if fault in ('shutdown', 'cancel') or run_cancel:
                await asyncio.gather(*(worker._activity_worker.completing.wait() for worker in workers[:3]))
                assert all(not worker._bridge_worker.stopping.is_set() for worker in workers[3:])
                assert all(worker._activity_worker.running.is_set() for worker in workers[3:])
                assert not serving.done()
                if fault == 'cancel':
                    serving.cancel()
                elif run_cancel:
                    sdk_runs = {task.get_coro().cr_frame.f_locals['self']: task for task in asyncio.all_tasks()
                        if getattr(task.get_coro(), 'cr_code', None) is sdk_worker.run.__code__
                        and task.get_coro().cr_frame.f_locals.get('self') in workers[:3]}
                    assert len(sdk_runs) == 3
                    aborted_workers.update(workers[:1] if fault.startswith('one-') else workers[:3])
                    cancelled_runs = [sdk_runs[worker] for worker in aborted_workers]
                    for task in cancelled_runs:
                        task.cancel()
                    await asyncio.gather(*cancelled_runs, return_exceptions=True)
                    try:
                        await asyncio.wait_for(workers[3]._shutdown_event.wait(), .1)
                        stop_started = True
                    except TimeoutError:
                        stop_started = False
                    observation = {'cleanup_released': cleanup_release.is_set(),
                        'aborted_normal_indexes': [index for index, worker in enumerate(workers[:3])
                                                   if worker in aborted_workers],
                        'normal_tasks': [{'done': sdk_runs[worker].done(), 'cancelled': sdk_runs[worker].cancelled()}
                                         for worker in workers[:3]],
                        'normal_workers': [{'is_shutdown': worker.is_shutdown,
                            'finalized': worker._bridge_worker.finalized} for worker in workers[:3]],
                        'stop_shutdown_started': stop_started, 'serving_done': serving.done()}
                    (tmp_path / 'sdk-run-cancel.json').write_text(json.dumps(observation, indent=2) + '\n')
                    assert not stop_started, 'Stop shutdown began before the original normal SDK cleanup completed'
                    if fault.startswith('one-'):
                        assert not sdk_runs[workers[1]].done()
                        assert not serving.done(), 'An aborted run interrupted its peer normal drain'
            validate_release.set()
            if fault.endswith('stop-fatal'):
                await asyncio.wait_for(workers[failing_index]._activity_worker.completing.wait(), 2)
                # Fatal is known while the failing worker still owns an active cleanup.
                await asyncio.wait_for(workers[0]._bridge_worker.stopping.wait(), 2)
                await asyncio.wait_for(workers[1]._bridge_worker.stopping.wait(), 2)
                assert all(not peer._bridge_worker.stopping.is_set()
                           for index, peer in enumerate(workers) if index >= 3 and index != failing_index)
                assert not serving.done() and not workers[failing_index]._bridge_worker.finalized
                serving.cancel()
                await asyncio.sleep(0)
                serving.cancel()
            cleanup_release.set()
            done, _ = await asyncio.wait((serving,), timeout=2)
            assert done, 'Service hung after SDK run validation failed'
            if run_cancel:
                with pytest.raises(RuntimeError, match='cleanup is incomplete; running state is unknown'):
                    serving.result()
                assert all(not worker._shutdown_event.is_set() for worker in workers[3:])
                assert all(not worker.is_shutdown and not worker._bridge_worker.finalized for worker in aborted_workers)
                # Only the test now closes the still-running stop group through
                # the SDK public API. Aborted normals stay unknown, not finalized.
                await asyncio.gather(*(worker.shutdown() for worker in workers[3:]))
            elif fault == 'shutdown':
                assert serving.result() is None
            elif fault == 'cancel':
                with pytest.raises(asyncio.CancelledError):
                    serving.result()
            else:
                with pytest.raises(RuntimeError, match=fault):
                    serving.result()
            assert all(worker._bridge_worker.finalized for index, worker in enumerate(workers)
                       if worker not in aborted_workers and (index != failing_index or fault.endswith('stop-fatal')))
            assert not handlers
            assert not [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        finally:
            validate_release.set()
            cleanup_release.set()
            if not serving.done():
                serving.cancel()
            await asyncio.gather(*(worker.shutdown() for worker in workers
                                   if worker not in aborted_workers and worker.is_running))
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

        def __init__(self, program_version=1, *, data_converter=None):
            self.program_version = program_version
            self.original = {**self.original, 'protocol': 'ergora-training-cycle-v' + str(program_version)}
            self.workflow_type = 'TrainingCycleWorkflow' + ('V' + str(program_version) if program_version in (2, 3) else '')
            if data_converter is None:
                from ergora.reference_training_worker import _CycleFailureConverter

                data_converter = (replace(DataConverter.default, failure_converter_class=_CycleFailureConverter)
                                  if program_version in (2, 3) else DataConverter.default)
            self.data_converter = data_converter
            self.converter = data_converter.payload_converter
            self.time = 0
            self.commands = []
            async def create():
                cls = create_cycle_workflow(program_version)
                assert (cls.__module__, cls.__name__, cls.__qualname__) == (
                    'ergora.reference_training_worker', self.workflow_type, self.workflow_type)
                runner = SandboxedWorkflowRunner()
                defn = workflow._Definition.must_from_class(cls)
                runner.prepare_workflow(defn)
                return runner.create_instance(WorkflowInstanceDetails(
                    payload_converter_factory=data_converter._new_internal_payload_converter,
                    failure_converter_class=data_converter.failure_converter_class,
                    interceptor_classes=[], defn=defn,
                    info=replace(_fake_info, workflow_id='parent', run_id='parent-run',
                        workflow_type=self.workflow_type, namespace='default',
                        task_queue='ergora-training-cycle-v' + str(program_version)), randomness_seed=1, extern_functions={},
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
            return self.activate(initialize_workflow=wa.InitializeWorkflow(workflow_type=self.workflow_type,
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
            suffix = '.' + action + ('.v4' if self.program_version == 3 else '.v3' if self.program_version == 2 else
                '.v2' if action in ('observe-candidate', 'request-execution-or-observe') else '.v1')
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


@pytest.mark.parametrize('effect,completion', [('start', 'failure'),
    ('request-execution-or-observe', 'failure'), ('request-execution-or-observe', 'partial-envelope')])
def test_cycle_workflow_lost_effect_completion_never_regrants_its_command(cycle_workflow, effect, completion):
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
    if completion == 'failure':
        failure = Failure(message='Completion unavailable', activity_failure_info=ActivityFailureInfo(),
                          cause=Failure(message='RPC deadline', timeout_failure_info=TimeoutFailureInfo()))
        commands = h.activate(resolve_activity=wa.ResolveActivity(seq=command.schedule_activity.seq,
            result=ar.ActivityResolution(failed=ar.Failure(failure=failure))))
    else:
        partial = h.envelope(effect, submitted=True, queued=True)
        partial.update(status='unknown', facts=None)
        commands = h.result(command, partial)
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


@pytest.mark.parametrize('boundary', ['work', 'history-events', 'history-bytes', 'ordinary-count'])
def test_cycle_workflow_final_facts_cannot_bypass_the_stop_guard(cycle_workflow, boundary):
    h = cycle_workflow()
    cold = h.activity(h.start())
    commands = h.result(cold, h.envelope(submitted=True), at=1)
    final_ordinal = 256 if boundary == 'ordinary-count' else 2
    for ordinal in range(2, final_ordinal):
        observe = h.activity(h.timer(commands, at=ordinal))
        commands = h.result(observe, h.envelope(submitted=True), at=ordinal)
    observe = h.activity(h.timer(commands, at=final_ordinal))
    timeout = observe.schedule_activity.schedule_to_close_timeout.ToTimedelta().total_seconds()
    remaining = timeout / 4
    received = final_ordinal + remaining * 2
    assert received - final_ordinal < timeout
    final = h.envelope(submitted=True, queued=True)
    final['facts']['native']['state'] = 'SUCCEEDED'
    final['facts']['runtime']['phase'] = 'AWAITING_RELEASE'
    final['facts']['execution'].update(state='stopped', request_sha256='f' * 64,
        record_sha256={'request': 'f' * 64, 'stopped': 'e' * 64},
        reap_record_observed=True, durable_stop_confirmed=True, executor_stop_confirmed=True)
    changes = {}
    if boundary == 'work':
        final['facts']['budget']['work_remaining_seconds'] = remaining
        assert received > final_ordinal + remaining
    elif boundary == 'history-events':
        changes['history_length'] = 8000
    elif boundary == 'history-bytes':
        changes['history_size'] = 8 * 1024 * 1024
    commands = h.result(observe, final, at=received, **changes)
    assert not any(c.HasField('complete_workflow_execution') for c in commands), (h.query(), len(h.scheduled('stop')))
    stop = h.activity(commands)
    assert stop.schedule_activity.task_queue == 'ergora-training-cycle-stop-v1'
    assert stop.schedule_activity.schedule_to_close_timeout.ToTimedelta().total_seconds() > 0
    commands = h.result(stop, h.envelope('stop'), at=received + remaining)
    outcome = h.converter.from_payloads([next(c.complete_workflow_execution.result for c in commands
                                            if c.HasField('complete_workflow_execution'))])[0]
    assert outcome['outcome'] == 'needs_reconciliation' and len(h.scheduled('stop')) == 1


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


@pytest.mark.parametrize('program_version', [1, 2, 3])
def test_cycle_workflow_evicts_after_stop_before_normal_cancellation_ack(cycle_workflow, cycle_v2_workflow, tmp_path, program_version):
    import subprocess
    from google.protobuf.json_format import MessageToDict
    from temporalio.api.common.v1 import Payloads

    h = cycle_workflow() if program_version == 1 else cycle_v2_workflow(program_version)
    events = []

    def payloads(value):
        return MessageToDict(Payloads(payloads=h.converter.to_payloads([value])))

    def event(kind, attributes, at=0):
        ident = len(events) + 1
        events.append({'eventId': str(ident), 'eventTime': f'2026-01-01T00:00:{at:02d}Z',
            'eventType': 'EVENT_TYPE_' + kind, **attributes})
        return ident

    def workflow_task(at):
        scheduled = event('WORKFLOW_TASK_SCHEDULED', {'workflowTaskScheduledEventAttributes': {
            'taskQueue': {'name': 'ergora-training-cycle-v' + str(program_version)}, 'startToCloseTimeout': '10s', 'attempt': 1}}, at)
        started = event('WORKFLOW_TASK_STARTED', {'workflowTaskStartedEventAttributes': {
            'scheduledEventId': str(scheduled), 'identity': 'test-worker'}}, at)
        return event('WORKFLOW_TASK_COMPLETED', {'workflowTaskCompletedEventAttributes': {
            'scheduledEventId': str(scheduled), 'startedEventId': str(started),
            'sdkMetadata': {'coreUsedFlags': [2, 3, 1]}}}, at)

    def activity(action, ident, request, completed_task, timeout, at):
        return event('ACTIVITY_TASK_SCHEDULED', {'activityTaskScheduledEventAttributes': {
            'activityId': ident, 'activityType': {'name': 'ergora.training_cycle.' + action},
            'taskQueue': {'name': 'ergora-training-cycle-stop-v' + str(program_version) if action.startswith('stop.')
                          else 'ergora-training-cycle-v' + str(program_version)}, 'input': payloads(request),
            'scheduleToCloseTimeout': f'{timeout}s', 'startToCloseTimeout': f'{timeout}s',
            'workflowTaskCompletedEventId': str(completed_task), 'retryPolicy': {'maximumAttempts': 1}}}, at)

    def complete_activity(scheduled, value, at):
        started = event('ACTIVITY_TASK_STARTED', {'activityTaskStartedEventAttributes': {
            'scheduledEventId': str(scheduled), 'attempt': 1}}, at)
        event('ACTIVITY_TASK_COMPLETED', {'activityTaskCompletedEventAttributes': {
            'scheduledEventId': str(scheduled), 'startedEventId': str(started), 'result': payloads(value)}}, at)

    # SDK Core, rather than a hand-authored resolve activation, owns the local
    # cancellation result. The server has not acknowledged normal cancellation.
    event('WORKFLOW_EXECUTION_STARTED', {'workflowExecutionStartedEventAttributes': {
        'workflowType': {'name': h.workflow_type}, 'workflowId': 'parent',
        'taskQueue': {'name': 'ergora-training-cycle-v' + str(program_version)}, 'input': payloads(h.original),
        'workflowTaskTimeout': '10s', 'originalExecutionRunId': 'parent-run',
        'firstExecutionRunId': 'parent-run', 'attempt': 1}})
    request = {'workflow_input': h.original, 'ordinal': 0, **({'predecessor': None} if program_version in (2, 3) else {})}
    suffix = '.v4' if program_version == 3 else '.v3' if program_version == 2 else '.v1'
    cold = activity('observe-candidate' + ('.v2' if program_version == 1 else suffix), 'candidate-0-1', request, workflow_task(0), 10, 0)
    complete_activity(cold, h.envelope(), 1)
    normal = activity('start' + suffix, 'candidate-0-2', request, workflow_task(1), 30 if program_version == 3 else 10, 1)
    event('WORKFLOW_EXECUTION_CANCEL_REQUESTED', {'workflowExecutionCancelRequestedEventAttributes': {}}, 2)
    stopping = workflow_task(2)
    stop = activity('stop' + suffix, 'cycle-stop', {'workflow_input': h.original, 'reason': 'workflow_cancelled'},
                    stopping, 1098, 2)
    event('ACTIVITY_TASK_CANCEL_REQUESTED', {'activityTaskCancelRequestedEventAttributes': {
        'scheduledEventId': str(normal), 'workflowTaskCompletedEventId': str(stopping)}}, 2)
    complete_activity(stop, h.envelope('stop'), 3)
    event('WORKFLOW_EXECUTION_CANCELED', {'workflowExecutionCanceledEventAttributes': {
        'workflowTaskCompletedEventId': str(workflow_task(3))}}, 3)
    history = tmp_path / 'cancel-before-normal-ack.json'
    history.write_text(json.dumps({'events': events}), encoding='utf-8')
    # A broken eviction can leave Replayer waiting indefinitely, so isolate only
    # the real SDK replay in a bounded child and retain its exact error on failure.
    script = '''import asyncio, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from temporalio.client import WorkflowHistory
from temporalio.worker import Replayer
from ergora.reference_training_worker import create_cycle_workflow
async def replay():
    history = WorkflowHistory.from_json('parent', Path(sys.argv[2]).read_text())
    await Replayer(workflows=[create_cycle_workflow(int(sys.argv[3]))]).replay_workflow(history)
    print('REPLAY_AND_EVICTION_COMPLETED', flush=True)
asyncio.run(replay())
'''
    command = [sys.executable, '-I', '-B', '-c', script, str(Path(training.__file__).resolve().parent.parent), str(history), str(program_version)]
    try:
        replay = subprocess.run(command, capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired as error:
        pytest.fail(f'SDK replay/eviction did not finish: {error.stdout!r}\n{error.stderr!r}')
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert 'REPLAY_AND_EVICTION_COMPLETED' in replay.stdout
    assert 'Eviction processed, but' not in replay.stderr


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
    h.signal([])
    assert h.query()['last_signal_rejection'] == 'signal_identity_or_shape_rejected'
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


@pytest.fixture
def cycle_v2_workflow(cycle_workflow):
    """SDK contracts with synthetic inline facts; no schema3 execution or training."""
    from ergora import training_execution_protocol as protocol

    class Harness(cycle_workflow):
        def __init__(self, program_version=2, **config):
            super().__init__(program_version, **config)

        def envelope(self, action='observe-candidate', *, ordinal=0, count=2, submitted=False,
                     queued=False, completed=False, accepted=False, work=1000, total=1100):
            value = super().envelope(submitted=submitted or completed, queued=queued or completed, work=work, total=total)
            value.update(schema_version=4 if self.program_version == 3 else 3,
                protocol='ergora-training-cycle-activity-v4' if self.program_version == 3 else 'ergora-training-cycle-activity-v3', action=action)
            value['observation'].update(boottime_ns=123, observed_at='synthetic-fixture')
            if action == 'stop':
                value['facts'] = None
                return value
            facts = value['facts']
            value['inspection'] = {'operation_id': '0' * 32, 'mode': 'inspect-controller-activity',
                'ordinal': None, 'operation_stopped': True, 'supervisor_returncode': 0,
                'result': {'inline': {'status': 'inspected'}}}
            value['operations'] = [{'operation_id': facts['source_operation_id'],
                'mode': action if action in ('collect-round', 'reconcile-round') else 'observe-candidate',
                'ordinal': ordinal, 'operation_stopped': True, 'supervisor_returncode': 0,
                'result': {'ref': {'file': 'helper/stdout.txt', 'bytes': 100, 'sha256': '1' * 64}}}]
            facts['candidate'].update(ordinal=ordinal, experiment_id='candidate' + str(ordinal))
            facts['submission']['workflow_id'] = 'child' + str(ordinal)
            if queued or completed:
                facts['runtime'].update(workflow_id='child' + str(ordinal))
                facts['runtime']['binding']['experiment_id'] = 'candidate' + str(ordinal)
            facts['selection'] = {'count': count, 'common_sha256': 'a' * 64, 'measurement_sources_sha256': 'b' * 64}
            facts['measurement'] = {'measurement_state': 'pending', 'index_state': 'absent',
                'continuation_ready': False, 'prefix': None, 'acceptance': None}
            if completed:
                facts['execution'].update(state='stopped', request_sha256='f' * 64,
                    record_sha256=dict.fromkeys(('request', 'launch', 'attempt', 'ack', 'stopped'), 'f' * 64),
                    reap_record_observed=True, durable_stop_confirmed=True, executor_stop_confirmed=True)
                facts['runtime']['phase'] = 'AWAITING_RELEASE'
                facts['native']['state'] = 'SUCCEEDED'
            if accepted:
                prefix = {'directory': str(Path(self.original['control_home']) / 'training-cycles/demo/first/controller/rounds' / str(ordinal)),
                    'sha256': '3' * 64, 'bytes': 1000 + ordinal, 'rounds': ordinal + 1,
                    'last_round_sha256': '4' * 64, 'initial_anchor_sha256': '5' * 64}
                acceptance = {'source_operation_id': facts['source_operation_id'],
                    'observation': {'path': str(Path(self.original['control_home']) / 'operations/training-cycles' /
                        facts['source_operation_id'] / 'helper/observation.json'), 'bytes': 2000, 'sha256': '6' * 64},
                    'candidate': {key: facts['candidate'][key] for key in
                                  ('ordinal', 'experiment_id', 'manifest_sha256', 'project_revision')},
                    'submission': {key: facts['submission'][key] for key in ('intent_sha256', 'workflow_id', 'run_id')},
                    'execution': {'owner_sha256': '7' * 64, 'record_sha256': facts['execution']['record_sha256'],
                                  'raw_inventory_sha256': '8' * 64},
                    'runtime': {'namespace': 'default', 'kind': 'status', 'phase': 'AWAITING_RELEASE', 'job_id': 'job',
                        'binding_sha256': protocol.CycleAdmission._sha(facts['runtime']['binding']),
                        'memo_sha256': facts['submission']['intent_sha256'], 'evidence_sha': '9' * 64, 'report_uri': None},
                    'evidence': {'evidence_sha256': '9' * 64, 'gate_report_sha256': 'a' * 64, 'files_sha256': 'b' * 64},
                    'common_sha256': facts['selection']['common_sha256'],
                    'measurement_sources_sha256': facts['selection']['measurement_sources_sha256']}
                acceptance['candidate']['registration_sha256'] = 'c' * 64
                acceptance['submission']['spec_sha256'] = 'd' * 64
                facts['measurement'] = {'measurement_state': 'accepted', 'index_state': 'durable',
                    'continuation_ready': True, 'prefix': prefix, 'acceptance': acceptance}
            return value

    return Harness


@pytest.mark.parametrize('program_version', [2, 3])
def test_cycle_v2_consumes_selected_rounds_with_one_opportunity_each(cycle_v2_workflow, program_version):
    h = cycle_v2_workflow(program_version)
    observe = h.activity(h.start())
    accepted = None
    for ordinal in range(2):
        request = h.converter.from_payloads(observe.schedule_activity.arguments)[0]
        assert request == {'workflow_input': h.original, 'ordinal': ordinal, 'predecessor': accepted}
        start = h.activity(h.result(observe, h.envelope(ordinal=ordinal), at=ordinal * 10 + 1))
        execute = h.activity(h.result(start, h.envelope('start', ordinal=ordinal, submitted=True, queued=True), at=ordinal * 10 + 2))
        collect = h.activity(h.result(execute, h.envelope('request-execution-or-observe', ordinal=ordinal, completed=True), at=ordinal * 10 + 3))
        assert collect.schedule_activity.activity_id == 'candidate-' + str(ordinal) + '-collect'
        assert collect.schedule_activity.retry_policy.maximum_attempts == 1
        value = h.envelope('collect-round', ordinal=ordinal, completed=True, accepted=True)
        accepted = {key: value['facts']['measurement'][key] for key in ('prefix', 'acceptance')}
        commands = h.result(collect, value, at=ordinal * 10 + 4)
        if ordinal == 0:
            observe = h.activity(h.timer(commands, at=5))
    outcome = h.converter.from_payloads([next(c.complete_workflow_execution.result for c in commands
        if c.HasField('complete_workflow_execution'))])[0]
    assert outcome['outcome'] == 'selected_rounds_observed'
    assert (outcome['ordinal'], outcome['confirmed_rounds'], outcome['selection_count']) == (1, 2, 2)
    assert outcome['total_observation_count'] == 8 and outcome['observation_count'] == 4
    assert all(len(h.scheduled(action)) == 2 for action in ('start', 'request-execution-or-observe', 'collect-round'))
    assert not h.scheduled('stop')


def test_cycle_v2_lost_collect_completion_only_reconciles_existing_index(cycle_v2_workflow):
    from temporalio.api.failure.v1 import ActivityFailureInfo, Failure, TimeoutFailureInfo
    from temporalio.bridge.proto import activity_result as ar, workflow_activation as wa
    h = cycle_v2_workflow()
    observe = h.activity(h.start())
    collect = h.activity(h.result(observe, h.envelope(completed=True), at=1))
    failure = Failure(message='Lost completion', activity_failure_info=ActivityFailureInfo(),
                      cause=Failure(message='Timeout', timeout_failure_info=TimeoutFailureInfo()))
    commands = h.activate(resolve_activity=wa.ResolveActivity(seq=collect.schedule_activity.seq,
        result=ar.ActivityResolution(failed=ar.Failure(failure=failure))))
    reconcile = h.activity(h.timer(commands, at=2))
    assert reconcile.schedule_activity.activity_type.endswith('.reconcile-round.v3')
    commands = h.result(reconcile, h.envelope('reconcile-round', completed=True), at=3)
    reconcile = h.activity(h.timer(commands, at=4))
    commands = h.result(reconcile, h.envelope('reconcile-round', completed=True, accepted=True), at=5)
    status = h.query()
    assert status['confirmed_rounds'] == status['ordinal'] == 1
    assert len(h.scheduled('collect-round')) == 1 and len(h.scheduled('reconcile-round')) == 2
    assert not h.scheduled('start') and not h.scheduled('request-execution-or-observe')


@pytest.mark.parametrize('fault', ['selection-drift', 'late-ordinal', 'acceptance-job'])
def test_cycle_v2_rejects_unbound_or_oversized_received_envelope(cycle_v2_workflow, fault):
    h = cycle_v2_workflow()
    observe = h.activity(h.start())
    collect = h.activity(h.result(observe, h.envelope(completed=True), at=1))
    value = h.envelope('collect-round', completed=True, accepted=True)
    if fault == 'selection-drift':
        value['facts']['selection']['count'] = 3
    elif fault == 'late-ordinal':
        value['facts']['candidate']['ordinal'] = 1
    else:
        value['facts']['measurement']['acceptance']['runtime']['job_id'] = 'other-job'
    stop = h.activity(h.result(collect, value, at=2))
    assert stop.schedule_activity.activity_type.endswith('.stop.v3')
    assert h.query()['confirmed_rounds'] == 0 and h.query()['ordinal'] == 0


@pytest.mark.parametrize('size', [32767, 32768, 32769])
def test_cycle_v2_received_aggregate_capacity_preserves_opportunities(cycle_v2_workflow, tmp_path, size):
    from copy import deepcopy
    from temporalio.api.common.v1 import Payloads

    h = cycle_v2_workflow()
    observe = h.activity(h.start())
    start = h.activity(h.result(observe, h.envelope(), at=1))
    request = h.activity(h.result(start, h.envelope('start', submitted=True, queued=True), at=2))
    collect = h.activity(h.result(request, h.envelope('request-execution-or-observe', completed=True), at=3))
    value = h.envelope('collect-round', completed=True, accepted=True)
    unknown = deepcopy(value['inspection'])
    unknown.update(operation_id='2' * 32, mode='observe-candidate', ordinal=0,
                   result={'inline': {'status': 'unknown', 'reason': '完整诊断'}})
    value['operations'].append(unknown)
    reason = unknown['result']['inline']
    for _ in range(3):
        reason['reason'] += 'x' * max(0, size - h.converter.to_payloads_wrapper([value]).ByteSize())
        actual = h.converter.to_payloads_wrapper([value]).ByteSize()
        if actual > size:
            reason['reason'] = reason['reason'][:-(actual - size)]
    received = h.converter.to_payloads_wrapper([value])
    assert received.ByteSize() == size
    assert all(h.converter.to_payloads_wrapper([part]).ByteSize() < 32768
               for part in [value['facts'], value['inspection'], *value['operations']])
    (tmp_path / 'received.pb').write_bytes(received.SerializeToString())
    commands = h.result(collect, value, at=4)
    status = h.query()
    assert all(len(h.scheduled(action)) == 1 for action in ('start', 'request-execution-or-observe', 'collect-round'))
    if size <= 32768:
        assert status['confirmed_rounds'] == status['ordinal'] == 1
        assert status['prefix'] == value['facts']['measurement']['prefix']
        observe = h.activity(h.timer(commands, at=5))
        outgoing = Payloads(payloads=observe.schedule_activity.arguments)
        (tmp_path / 'next-command.pb').write_bytes(observe.SerializeToString())
        request = h.converter.from_payloads(outgoing.payloads)[0]
        assert request['predecessor'] == {key: value['facts']['measurement'][key] for key in ('prefix', 'acceptance')}
        assert outgoing.ByteSize() <= 32768
    else:
        assert status['confirmed_rounds'] == status['ordinal'] == 0 and status['prefix'] is None
        assert all(status[key] for key in ('start_scheduled', 'request_scheduled', 'collect_scheduled'))
        assert h.activity(commands).schedule_activity.activity_type.endswith('.stop.v3')


@pytest.mark.parametrize('size', [32767, 32768, 32769])
def test_cycle_v2_signal_and_stop_command_use_complete_multibyte_payload(cycle_v2_workflow, tmp_path, size):
    from temporalio.api.common.v1 import Payloads

    h = cycle_v2_workflow()
    cold = h.activity(h.start())
    request = {'workflow_input': h.original, 'reason': '完整停止原因' + '界' * 1000}
    for _ in range(3):
        request['reason'] += 'x' * max(0, size - h.converter.to_payloads_wrapper([request]).ByteSize())
        excess = h.converter.to_payloads_wrapper([request]).ByteSize() - size
        if excess > 0:
            request['reason'] = request['reason'][:-excess]
    assert h.converter.to_payloads_wrapper([request]).ByteSize() == size
    h.signal(request)
    if size > 32768:
        assert h.query()['last_signal_rejection'] == 'signal_capacity_exceeded'
        request = {'workflow_input': h.original, 'reason': 'A later complete valid stop'}
        h.signal(request)
    stop = h.activity(h.result(cold, h.envelope(), at=1))
    actual = Payloads(payloads=stop.schedule_activity.arguments)
    assert h.converter.from_payloads(actual.payloads) == [request]
    assert actual.ByteSize() == (size if size <= 32768 else h.converter.to_payloads_wrapper([request]).ByteSize())
    (tmp_path / 'stop-command.pb').write_bytes(stop.SerializeToString())
    commands = h.result(stop, h.envelope('stop'), at=2)
    result = next(command.complete_workflow_execution.result for command in commands
                  if command.HasField('complete_workflow_execution'))
    outcome = h.converter.from_payloads([result])[0]
    assert outcome['stop_activity_status'] == 'returned'
    assert outcome['stop_durable'] is outcome['admission_drained'] is outcome['executor_stop_confirmed'] is None


@pytest.mark.parametrize('size', [32767, 32768, 32769, 'raised-failure'])
def test_cycle_v2_query_and_run_encode_full_status_or_failure(
        cycle_v2_workflow, cycle_capacity_converter, tmp_path, size):
    from temporalio.api.common.v1 import Payloads
    from temporalio.bridge.proto import workflow_activation as wa

    converter = cycle_capacity_converter('ergora-training-cycle-workflow-v2', size)
    h = cycle_v2_workflow(data_converter=converter)
    observe = h.activity(h.start())
    collect = h.activity(h.result(observe, h.envelope(completed=True), at=1))
    accepted = h.envelope('collect-round', completed=True, accepted=True)
    h.result(collect, accepted, at=2)
    commands = h.activate(query_workflow=wa.QueryWorkflow(query_id='status-query', query_type='status'))
    response = next(command.respond_to_query for command in commands if command.HasField('respond_to_query'))
    (tmp_path / 'query.pb').write_bytes(response.SerializeToString())
    oversized = size == 'raised-failure' or size > 32768
    if oversized:
        failure = response.failed
        assert failure.application_failure_info.type == (
            'cycle_failure_capacity_exceeded' if size == 'raised-failure' else 'cycle_workflow_capacity_exceeded')
        assert failure.ByteSize() <= 32768 and failure.application_failure_info.non_retryable
    else:
        assert Payloads(payloads=[response.succeeded.response]).ByteSize() == size
        status = h.converter.from_payloads([response.succeeded.response])[0]
        assert status['prefix'] == accepted['facts']['measurement']['prefix'] and status['confirmed_rounds'] == 1
        assert status['stop_durable'] is status['admission_drained'] is status['executor_stop_confirmed'] is None
    stop = h.activity(h.signal({'workflow_input': h.original, 'reason': 'Finish complete status fixture'}, at=3))
    commands = h.result(stop, h.envelope('stop', ordinal=1), at=4)
    terminal = next(command for command in commands if command.HasField(
        'fail_workflow_execution' if oversized else 'complete_workflow_execution'))
    (tmp_path / 'terminal.pb').write_bytes(terminal.SerializeToString())
    if oversized:
        failure = terminal.fail_workflow_execution.failure
        assert failure.application_failure_info.type == response.failed.application_failure_info.type
        assert failure.ByteSize() <= 32768
    else:
        result = terminal.complete_workflow_execution.result
        assert Payloads(payloads=[result]).ByteSize() == size
        outcome = h.converter.from_payloads([result])[0]
        assert outcome['prefix'] == accepted['facts']['measurement']['prefix']
        assert outcome['stop_activity_status'] == 'returned' and outcome['outcome'] == 'needs_reconciliation'


@pytest.mark.parametrize('size', [32767, 32768, 32769])
def test_cycle_v2_initial_input_counts_actual_converter_metadata(
        cycle_v2_workflow, cycle_capacity_converter, tmp_path, size):
    from temporalio.api.common.v1 import Payloads

    converter = cycle_capacity_converter('ergora-training-cycle-v2', size)
    h = cycle_v2_workflow(data_converter=converter)
    incoming = converter.payload_converter.to_payloads_wrapper([h.original])
    assert incoming.ByteSize() == size
    (tmp_path / 'input.pb').write_bytes(incoming.SerializeToString())
    commands = h.start()
    if size <= 32768:
        command = h.activity(commands)
        actual = Payloads(payloads=command.schedule_activity.arguments)
        request = h.converter.from_payloads(actual.payloads)[0]
        assert request == {'workflow_input': h.original, 'ordinal': 0, 'predecessor': None}
        assert actual.ByteSize() <= 32768
    else:
        failure = next(command.fail_workflow_execution.failure for command in commands
                       if command.HasField('fail_workflow_execution'))
        assert failure.application_failure_info.type == 'cycle_workflow_capacity_exceeded'
        assert failure.ByteSize() <= 32768 and not h.scheduled('observe-candidate')


@pytest.mark.skipif(sys.platform != 'linux', reason='Assembled cycle operations retain the original Linux boot clock')
@pytest.mark.parametrize('size', [32767, 32768, 32769])
@pytest.mark.parametrize('program_version', [2, 3])
def test_cycle_v3_completion_counts_assembled_measurement_and_all_operations(
        cycle_v2_workflow, cycle_capacity_converter, cycle_sdk_completion, monkeypatch, tmp_path, size, program_version):
    """Synthetic H facts enter the real v3 wrapper and final SDK completion."""
    import asyncio
    from copy import deepcopy
    from types import SimpleNamespace
    from temporalio.api.common.v1 import Payloads
    from ergora import budget_clock, reference_training_worker as worker, training_cycles

    h = cycle_v2_workflow(program_version)
    wire = 'ergora-training-cycle-activity-v' + str(program_version + 1)
    clock = budget_clock.authorize(120)
    authorization = {'schema_version': program_version + 1, 'control_home': str(tmp_path), 'project': 'demo', 'cycle_id': 'first',
                     'input_sha256': 'a' * 64, 'clock': clock}
    authorization['sha256'] = training_cycles._sha(authorization)
    h.original.update(control_home=str(tmp_path), authorization_sha256=authorization['sha256'])
    snapshot = {'authorization': authorization, 'candidates': [{}, {}],
        'policy': {'wall_seconds': 120, 'cleanup_seconds': 10, 'control_timeout_seconds': 2}}
    expected = h.envelope('collect-round', completed=True, accepted=True)['facts']
    seen, assembled = [], []

    async def observed(operation):
        seen.append(operation)
        if operation.identity['mode'] == 'inspect-controller-activity':
            return operation.observation({'status': 'inspected', 'snapshot': snapshot,
                'controller': {'workflow_id': 'parent', 'run_id': 'parent-run', 'intent_sha256': 'c' * 64},
                'observation': {'total_remaining_seconds': 120, 'boot_id': clock['boot_id'],
                                'boottime_ns': clock['boottime_ns'], 'observed_at': clock['authorized_at']}})
        facts = deepcopy(expected)
        facts['source_operation_id'] = facts['measurement']['acceptance']['source_operation_id'] = operation.identity['operation_id']
        facts['measurement']['acceptance']['observation']['path'] = str(operation.output / 'helper/observation.json')
        return operation.observation({'status': 'observed', 'facts': facts})

    original_capacity = worker._cycle_capacity
    async def capacity(value, converter):
        if isinstance(value, dict) and value.get('protocol') == wire:
            assembled.append(value)
        await original_capacity(value, converter)

    monkeypatch.setattr(worker._CycleOperation, 'run', observed)
    monkeypatch.setattr(worker, '_cycle_capacity', capacity)
    converter = cycle_capacity_converter(wire, size)
    client = SimpleNamespace(namespace='default', data_converter=converter)
    activities = worker.create_cycle_activities(client, program_version)
    completion = asyncio.run(cycle_sdk_completion(activities['collect-round'],
        {'workflow_input': h.original, 'ordinal': 0, 'predecessor': None}, converter=converter))
    (tmp_path / 'completion.pb').write_bytes(completion.SerializeToString())
    envelope, = assembled
    assert [operation.identity['mode'] for operation in seen] == ['inspect-controller-activity', 'collect-round']
    assert envelope['facts']['selection'] == expected['selection']
    assert envelope['facts']['measurement']['acceptance']['evidence'] == expected['measurement']['acceptance']['evidence']
    assert len(envelope['operations']) == 1 and envelope['inspection']['mode'] == 'inspect-controller-activity'
    full = Payloads(payloads=asyncio.run(converter.encode([envelope])))
    assert full.ByteSize() == size
    if size <= 32768:
        result = completion.result.completed.result
        assert Payloads(payloads=[result]).ByteSize() == size
        assert asyncio.run(converter.decode([result])) == [envelope]
    else:
        failure = completion.result.failed.failure
        assert failure.application_failure_info.type == 'cycle_activity_capacity_exceeded'
        assert failure.application_failure_info.non_retryable and not failure.HasField('cause')


def test_cycle_v2_round_change_never_renews_work_deadline(cycle_v2_workflow):
    h = cycle_v2_workflow()
    observe = h.activity(h.start())
    collect = h.activity(h.result(observe, h.envelope(completed=True, work=5, total=8), at=1))
    commands = h.result(collect, h.envelope('collect-round', completed=True, accepted=True, work=1000, total=1100), at=2)
    observe = h.activity(h.timer(commands, at=3))
    assert observe.schedule_activity.schedule_to_close_timeout.seconds == 2
    stop = h.activity(h.result(observe, h.envelope(ordinal=1, work=1000, total=1100), at=5))
    assert stop.schedule_activity.activity_type.endswith('.stop.v3')
    assert stop.schedule_activity.schedule_to_close_timeout.seconds == 3


@pytest.mark.skipif(sys.platform != 'linux', reason='Operation windows retain the original Linux boot clock')
@pytest.mark.parametrize('action', ['start', 'reconcile', 'request-execution-or-observe', 'observe-candidate',
                                    'collect-round', 'reconcile-round', 'stop'])
@pytest.mark.parametrize('attempt', [1, 2])
def test_cycle_v3_activity_routes_actual_sdk_source_without_reclaiming_retry(
        monkeypatch, tmp_path, cycle_v2_workflow, action, attempt):
    import asyncio
    from dataclasses import replace
    from types import SimpleNamespace
    from temporalio.converter import DataConverter
    from temporalio.testing import ActivityEnvironment
    from ergora import budget_clock, reference_training_worker as worker, training_cycles

    h = cycle_v2_workflow()
    clock = budget_clock.authorize(120)
    authorization = {'schema_version': 3, 'control_home': str(tmp_path), 'project': 'demo', 'cycle_id': 'first',
                     'input_sha256': 'a' * 64, 'clock': clock}
    authorization['sha256'] = training_cycles._sha(authorization)
    snapshot = {'authorization': authorization, 'candidates': [{}, {}],
        'policy': {'wall_seconds': 120, 'cleanup_seconds': 10, 'control_timeout_seconds': 2}}
    original = {**h.original, 'control_home': str(tmp_path), 'authorization_sha256': authorization['sha256']}
    seen = []

    async def observed(operation):
        seen.append(operation)
        if operation.identity['mode'] == 'inspect-controller-activity':
            return operation.observation({'status': 'inspected', 'snapshot': snapshot, 'candidate_exists': None,
                'controller': {'workflow_id': 'parent', 'run_id': 'parent-run', 'intent_sha256': 'c' * 64},
                'observation': {'total_remaining_seconds': 120, 'boot_id': clock['boot_id'],
                                'boottime_ns': clock['boottime_ns'], 'observed_at': clock['authorized_at']}})
        if operation.identity['mode'] == 'prepare-candidate':
            return operation.observation({'status': 'unknown', 'reason': 'Controlled closed offer; no root created'})
        return operation.observation({'status': 'observed', 'facts': h.envelope()['facts']})

    monkeypatch.setattr(worker._CycleOperation, 'run', observed)
    activities = worker.create_cycle_activities(SimpleNamespace(namespace='default', data_converter=DataConverter.default), 2)
    env = ActivityEnvironment()
    env.info = replace(env.info, workflow_id='parent', workflow_run_id='parent-run', workflow_type='TrainingCycleWorkflowV2',
        workflow_namespace='default', namespace='default', task_queue=(worker.protocol.CYCLE_STOP_TASK_QUEUE_V2
            if action == 'stop' else worker.protocol.CYCLE_TASK_QUEUE_V2), attempt=attempt,
        activity_type=worker.protocol.CYCLE_ACTIVITY_NAMES_V3[action])
    request = {'workflow_input': original, **({'reason': 'fixture-stop'} if action == 'stop' else {'ordinal': 0, 'predecessor': None})}
    value = asyncio.run(env.run(activities[action], request))
    assert value['schema_version'] == 3 and value['protocol'] == 'ergora-training-cycle-activity-v3'
    modes = [item.identity['mode'] for item in seen]
    assert all(item.identity['protocol'] == 'ergora-training-cycle-operation-v2' for item in seen)
    if action == 'stop':
        assert modes[1:] == ['stop-writer', 'drain', 'notify-owner', 'observe-execution', 'notify-owner', 'observe-execution']
        assert value['facts'] is None and len(value['operations']) == 6
    else:
        expected = {'start': ['prepare-candidate' if attempt == 1 else 'reconcile-candidate', 'observe-candidate'],
            'reconcile': ['reconcile-candidate', 'observe-candidate'],
            'request-execution-or-observe': ['request-execution-candidate' if attempt == 1 else 'observe-candidate'],
            'observe-candidate': ['observe-candidate'],
            'collect-round': ['collect-round' if attempt == 1 else 'reconcile-round'],
            'reconcile-round': ['reconcile-round']}[action]
        assert modes[1:] == expected
        cold = seen[0].payload['bootstrap']
        for item in seen[1:]:
            assert item.payload['bootstrap']['started_ns'] == cold['started_ns']
            assert item.payload['bootstrap']['deadline_ns'] == min(cold['deadline_ns'],
                cold['started_ns'] + 2_000_000_000, clock['boottime_ns'] + 110_000_000_000)


@pytest.mark.parametrize('registered_version', [2, 3])
def test_cycle_v3_factory_rejects_unknown_program_and_cross_version_request(monkeypatch, tmp_path, registered_version):
    import asyncio
    from types import SimpleNamespace
    from temporalio.converter import DataConverter
    from temporalio.exceptions import ApplicationError
    from temporalio.testing import ActivityEnvironment
    from ergora import reference_training_worker as worker
    client = SimpleNamespace(namespace='default', data_converter=DataConverter.default)
    for version in (True, 0, 4):
        with pytest.raises(ValueError):
            worker.create_cycle_workflow(version)
        with pytest.raises(ValueError):
            worker.create_cycle_activities(client, version)
    def forbidden(*args, **kwargs):
        raise AssertionError('Cross-version request cannot reach an operation')
    monkeypatch.setattr(worker, '_CycleOperation', forbidden)
    actions = worker.create_cycle_activities(client, registered_version)
    original = {'protocol': 'ergora-training-cycle-v1', 'control_home': str(tmp_path), 'project': 'demo',
        'cycle_id': 'first', 'input_sha256': 'a' * 64, 'authorization_sha256': 'b' * 64}
    with pytest.raises(ApplicationError) as rejected:
        asyncio.run(ActivityEnvironment().run(actions['observe-candidate'], {'workflow_input': original, 'ordinal': 0}))
    assert rejected.value.type == 'cycle_activity_request_rejected'


@pytest.mark.parametrize('effect', ['start', 'request-execution-or-observe'])
def test_cycle_v2_lost_start_or_request_never_returns_its_opportunity(cycle_v2_workflow, effect):
    from temporalio.api.failure.v1 import ActivityFailureInfo, Failure, TimeoutFailureInfo
    from temporalio.bridge.proto import activity_result as ar, workflow_activation as wa
    h = cycle_v2_workflow()
    cold = h.activity(h.start())
    command = h.activity(h.result(cold, h.envelope(submitted=effect != 'start', queued=effect != 'start'), at=1))
    failure = Failure(message='Lost effect completion', activity_failure_info=ActivityFailureInfo(),
                      cause=Failure(message='Timeout', timeout_failure_info=TimeoutFailureInfo()))
    commands = h.activate(resolve_activity=wa.ResolveActivity(seq=command.schedule_activity.seq,
        result=ar.ActivityResolution(failed=ar.Failure(failure=failure))))
    observe = h.activity(h.timer(commands, at=2))
    commands = h.result(observe, h.envelope(submitted=effect != 'start', queued=effect != 'start'), at=3)
    assert len(h.scheduled(effect)) == 1
    assert h.query()['start_scheduled' if effect == 'start' else 'request_scheduled'] is True
    if effect == 'start':
        assert h.activity(commands).schedule_activity.activity_type.endswith('.stop.v3')
    else:
        observe = h.activity(h.timer(commands, at=4))
        h.result(observe, h.envelope(submitted=True, queued=True), at=5)
        assert len(h.scheduled(effect)) == 1


def test_cycle_v2_stop_has_its_own_queue_and_never_invents_cycle_stop_proof(cycle_v2_workflow):
    h = cycle_v2_workflow()
    cold = h.activity(h.start())
    pending = h.activity(h.result(cold, h.envelope(), at=1))
    stop = h.activity(h.signal({'workflow_input': h.original, 'reason': 'fixture-stop'}, at=2))
    assert stop.schedule_activity.task_queue == 'ergora-training-cycle-stop-v2'
    assert stop.schedule_activity.activity_id == 'cycle-stop'
    assert stop.schedule_activity.seq != pending.schedule_activity.seq
    assert not h.scheduled('request-execution-or-observe')
    h.signal({'workflow_input': h.original, 'reason': 'second-stop'}, at=3)
    h.result(stop, h.envelope('stop'), at=4)
    status = h.query()
    assert len(h.scheduled('stop')) == 1 and status['outcome'] == 'needs_reconciliation'
    assert status['stop_durable'] is status['admission_drained'] is status['executor_stop_confirmed'] is None


@pytest.mark.parametrize('program_version,control,work,expected', [
    (2, 4, 100, 4), (2, 30, 100, 10), (3, 4, 100, 4), (3, 30, 100, 30), (3, 30, 6, 5)])
def test_cycle_declared_command_window_uses_authenticated_original_policy(
        cycle_v2_workflow, program_version, control, work, expected):
    h = cycle_v2_workflow(program_version)
    cold = h.activity(h.start())
    assert cold.schedule_activity.schedule_to_close_timeout.seconds == 10
    value = h.envelope(work=work)
    value['facts']['budget']['control_timeout_seconds'] = control
    normal = h.activity(h.result(cold, value, at=1)).schedule_activity
    assert normal.schedule_to_close_timeout.seconds == normal.start_to_close_timeout.seconds == expected
    assert normal.activity_id == 'candidate-0-2'
    assert normal.activity_type == 'ergora.training_cycle.start.v' + ('4' if program_version == 3 else '3')
    assert normal.task_queue == 'ergora-training-cycle-v' + str(program_version)
    status = h.query()
    assert status['schema_version'] == program_version
    assert status['protocol'] == 'ergora-training-cycle-workflow-v' + str(program_version)


@pytest.mark.skipif(sys.platform != 'linux', reason='SDK windows retain the original Linux boot clock')
@pytest.mark.parametrize('action,control,work,queue_wait,inspection_elapsed,permit_enabled,sdk_remaining,expected', [
    ('observe-candidate', 4, 100, 1, 1, True, 25, 'admitted'),
    ('observe-candidate', 30, 100, 4, 3, True, 25, 'admitted'),
    ('observe-candidate', 30, 6, 1, 1, True, 25, 'admitted'),
    ('observe-candidate', 30, 100, 0, 11, False, 25, 'inspection_expired'),
    ('observe-candidate', 30, 100, 12, 3, True, 25, 'admitted'),
    ('stop', 30, 100, 4, 3, True, 25, 'admitted'),
    ('stop', 30, 2, 1, 1, False, 25, 'admitted'),
    ('stop', 30, 100, 70, 3, True, 100, 'admitted'),
    ('stop', 30, 80, 70, 3, True, 100, 'admitted'),
    ('observe-candidate', 30, 100, 26, 0, True, 25, 'sdk_wait_expired'),
    ('observe-candidate', 30, 100, 12, 0, True, 10, 'sdk_wait_expired'),
    ('observe-candidate', 30, 100, 12, 11, True, 25, 'inspection_expired'),
    ('observe-candidate', 30, 10, 12, 0, True, 25, 'command_expired'),
    ('observe-candidate', 4, 100, 0, 5, False, 25, 'command_expired')])
def test_cycle_v3_sdk_windows_charge_queue_and_inspection_to_one_origin(
        monkeypatch, tmp_path, action, control, work, queue_wait, inspection_elapsed, permit_enabled,
        sdk_remaining, expected):
    import asyncio
    from dataclasses import replace
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace
    from temporalio.converter import DataConverter
    from temporalio.testing import ActivityEnvironment
    from ergora import budget_clock, reference_training_worker as worker, training_cycles

    clock = budget_clock.authorize(work + 10)
    authorization = {'schema_version': 4, 'control_home': str(tmp_path), 'project': 'demo', 'cycle_id': 'first',
                     'input_sha256': 'a' * 64, 'clock': clock}
    authorization['sha256'] = training_cycles._sha(authorization)
    snapshot = {'authorization': authorization, 'candidates': [{}, {}],
        'policy': {'wall_seconds': work + 10, 'cleanup_seconds': 10, 'control_timeout_seconds': control}}
    original = {key: authorization[key] for key in ('control_home', 'project', 'cycle_id', 'input_sha256')}
    original.update(protocol='ergora-training-cycle-v3', authorization_sha256=authorization['sha256'])
    ticks, seen, admitted = [clock['boottime_ns']], [], []
    monkeypatch.setattr(budget_clock, '_clock', lambda: (clock['boot_id'], ticks[0]))
    class SimulatedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(clock['authorized_at']) + timedelta(
                seconds=(ticks[0] - clock['boottime_ns']) / 1_000_000_000)
    monkeypatch.setattr(budget_clock, 'datetime', SimulatedDatetime)

    class Permit:
        acquired = released = False
        async def acquire(self):
            self.acquired = True
            ticks[0] += queue_wait * 1_000_000_000
        def release(self):
            self.released = True

    async def observed(operation):
        seen.append(operation)
        if operation.expired():
            return operation.observation({'status': 'unknown'})
        if operation.identity['mode'] == 'inspect-controller-activity':
            ticks[0] += inspection_elapsed * 1_000_000_000
            return operation.observation({'status': 'inspected', 'snapshot': snapshot, 'candidate_exists': None,
                'controller': {'workflow_id': 'parent', 'run_id': 'parent-run', 'intent_sha256': 'c' * 64},
                'observation': {'total_remaining_seconds': work + 10, 'boot_id': clock['boot_id'],
                                'boottime_ns': clock['boottime_ns'], 'observed_at': clock['authorized_at']}})
        admitted.append(operation.identity['mode'])
        return operation.observation({'status': 'observed'})

    monkeypatch.setattr(worker._CycleOperation, 'run', observed)
    permit = Permit()
    options = {'normal_permit': permit, 'stop_permit': permit} if permit_enabled else {}
    actions = worker.create_cycle_activities(SimpleNamespace(namespace='default', data_converter=DataConverter.default), 3, **options)
    env, now = ActivityEnvironment(), datetime.now(timezone.utc)
    env.info = replace(env.info, workflow_id='parent', workflow_run_id='parent-run', workflow_type='TrainingCycleWorkflowV3',
        workflow_namespace='default', namespace='default', attempt=1,
        activity_type=worker.protocol.CYCLE_ACTIVITY_NAMES_V4[action],
        task_queue=worker.protocol.CYCLE_STOP_TASK_QUEUE_V3 if action == 'stop' else worker.protocol.CYCLE_TASK_QUEUE_V3,
        scheduled_time=now - timedelta(seconds=5), started_time=now,
        schedule_to_close_timeout=timedelta(seconds=sdk_remaining + 5),
        start_to_close_timeout=timedelta(seconds=sdk_remaining + 15))
    request = {'workflow_input': original, **({'reason': 'fixture-stop'} if action == 'stop' else {'ordinal': 0, 'predecessor': None})}
    if expected in ('sdk_wait_expired', 'inspection_expired'):
        from temporalio.exceptions import ApplicationError
        with pytest.raises(ApplicationError) as rejected:
            asyncio.run(env.run(actions[action], request))
        assert rejected.value.type == 'cycle_activity_request_rejected'
        assert admitted == [] and (not permit_enabled or permit.released)
        assert len(seen) == (0 if expected == 'sdk_wait_expired' else 1)
        return
    value = asyncio.run(env.run(actions[action], request))
    assert value['schema_version'] == 4 and value['protocol'] == 'ergora-training-cycle-activity-v4'
    assert value['status'] == ('observed' if expected == 'admitted' else 'unknown')
    assert all(operation.identity['protocol'] == 'ergora-training-cycle-operation-v3' for operation in seen)
    cold = seen[0].payload['bootstrap']
    assert cold['started_ns'] == clock['boottime_ns']
    charged_wait = queue_wait if permit_enabled else 0
    inspection_cap = min(sdk_remaining, charged_wait + 10)
    actual = (cold['deadline_ns'] - cold['started_ns']) / 1_000_000_000
    assert inspection_cap - .1 < actual <= inspection_cap
    assert bool(admitted) == (expected == 'admitted')
    for operation in seen[1:]:
        window = operation.payload['bootstrap']
        assert window['started_ns'] == cold['started_ns']
        cap = min(work + 10 if action == 'stop' else work, sdk_remaining if action == 'stop' else control, sdk_remaining)
        actual = (window['deadline_ns'] - cold['started_ns']) / 1_000_000_000
        assert cap - .1 < actual <= cap
        assert worker.protocol.cycle_operation_remaining(operation.payload) <= cap - charged_wait - inspection_elapsed
    if action == 'stop':
        assert len(seen) == 7 and value['facts'] is None
    assert not permit_enabled or permit.acquired and permit.released


@pytest.mark.skipif(sys.platform != 'linux', reason='Actual Linux child wait and PID/boot/start identity')
@pytest.mark.parametrize('fault', ['selector-construction', 'selector-registration', 'setup-interrupt', 'read-interrupt'])
def test_training_reader_setup_failure_retains_actual_child_wait(tmp_path, monkeypatch, fault):
    import selectors
    from ergora import processes

    children, waits, identities = [], [], []
    original_spawn, original_selector = reference.subprocess.Popen, selectors.DefaultSelector

    def spawn(*args, **kwargs):
        child = original_spawn(*args, **kwargs)
        children.append(child)
        identities.append(processes.identity(child.pid))
        actual_wait = child.wait

        def wait(*args, **kwargs):
            result = actual_wait(*args, **kwargs)
            waits.append(result)
            return result

        child.wait = wait
        return child

    def selector():
        assert children, 'The boundary must follow actual child creation'
        if fault == 'selector-construction':
            raise OSError('controlled selector setup failure')
        if fault == 'setup-interrupt':
            raise KeyboardInterrupt()
        selected = original_selector()

        def fail(*args, **kwargs):
            if fault == 'read-interrupt':
                raise KeyboardInterrupt()
            raise OSError('controlled selector registration failure')

        monkeypatch.setattr(selected, 'select' if fault == 'read-interrupt' else 'register', fail)
        return selected

    monkeypatch.setattr(reference.subprocess, 'Popen', spawn)
    monkeypatch.setattr(selectors, 'DefaultSelector', selector)
    project = {'registration': {'definition': {'execution': {
        'state_directory': str(tmp_path / 'state'), 'config_directory': str(tmp_path / 'config')}}}}
    try:
        with pytest.raises(KeyboardInterrupt if fault.endswith('interrupt') else ValueError):
            reference._training_reader(project, 'import time;time.sleep(60)', {}, timeout=1.2)
        assert len(children) == 1 and waits == [-9]
        assert children[0].returncode == -9
    finally:
        (tmp_path / 'reader-before-harness-cleanup.json').write_text(json.dumps({
            'fault': fault, 'identities': identities, 'production_waits': list(waits),
            'returncodes': [child.returncode for child in children]}, indent=2) + '\n')
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait()
        (tmp_path / 'reader-after-harness-cleanup.json').write_text(json.dumps({
            'returncodes': [child.returncode for child in children], 'waits': waits}, indent=2) + '\n')


def test_stop_status_uses_declared_adapter_allowance(tmp_path, monkeypatch):
    import asyncio
    from dataclasses import asdict
    from types import SimpleNamespace
    from ergora import reference_training_cancellation as cancellation, reference_training_runtime as runtime

    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/temporal'))
    from perf_temporal import adapter as adapters
    from perf_temporal.models import Binding, Job, Observation

    binding = Binding('declared-adapter', 'a' * 64, 'b' * 40, 'c' * 40)
    job, calls = Job(binding, 'job-original'), []

    class RestrictedAdapter:
        __slots__ = ()

        async def read_manifest(self, uri):
            raise AssertionError('read-only stop observation must not read a new manifest')

        async def lookup_job(self, experiment):
            assert experiment.binding == binding
            await asyncio.sleep(.01)
            return job

        async def create_job_if_absent(self, experiment, manifest):
            raise AssertionError('stop status cannot submit')

        async def poll_job(self, original, *, timeout=20):
            assert original == job and 0 < timeout < 1.2
            calls.append(('poll', timeout))
            return Observation(job, 'RUNNING')

        async def collect_and_gate(self, original):
            raise AssertionError('stop status cannot gate')

        async def collect_screen(self, original, *, timeout=20):
            raise AssertionError('stop status cannot collect')

        async def fence_and_lookup(self, experiment):
            raise AssertionError('stop status cannot fence')

        async def cancel_job_group(self, original):
            raise AssertionError('stop status cannot cancel')

        async def authorize_release_and_create_task(self, context):
            raise AssertionError('stop status cannot authorize')

        async def close(self):
            calls.append(('close',))

    async def observe(*args, **kwargs):
        await asyncio.sleep(.01)
        return {'status': 'observed'}

    async def lookup():
        return object(), object(), None

    def missing(*args):
        raise FileNotFoundError()

    operation = cancellation._Cancellation.__new__(cancellation._Cancellation)
    operation.payload = {'timeout': 1.2, 'control_home': str(tmp_path)}
    operation.spec = {'binding': asdict(binding), 'manifest_uri': 'test://original'}
    operation.start, operation.run_id = {'project_revision': 1, 'workflow_id': 'workflow-original'}, 'run-original'
    operation.submission = SimpleNamespace(native_request=lambda: None, document=missing,
        root=tmp_path, ident=binding.experiment_id, project={'id': 'demo'}, project_revision=1, recovery_context={})
    operation.lookup = lookup
    records = SimpleNamespace(observe=lambda *, durable: {'executor_stop_confirmed': False})
    monkeypatch.setattr(cancellation.training_execution_protocol, 'ExecutionRecords',
        lambda *args: SimpleNamespace(load=lambda: records))
    monkeypatch.setattr(runtime, 'observe', observe)
    monkeypatch.setattr(adapters, 'load_adapter', RestrictedAdapter)
    result = asyncio.run(operation.stop_status())
    assert result['executor_observation'] == asdict(Observation(job, 'RUNNING'))
    assert result['read_only'] and result['execution_success'] is None
    assert [row[0] for row in calls] == ['poll', 'close']


@pytest.mark.skipif(sys.platform != 'linux', reason='Actual Linux child wait and PID/boot/start identity')
@pytest.mark.parametrize('hold_wait', [False, True])
def test_native_reader_per_call_allowance_keeps_actual_wait(tmp_path, monkeypatch, hold_wait):
    import asyncio
    from ergora import processes

    for part in ('upstream', 'upstream/platform', 'upstream/temporal', 'local'):
        monkeypatch.syspath_prepend(str(reference.ROOT / 'platform' / part))
    from agent_platform.training import LocalTrainingAdapter
    from perf_temporal.models import Binding, Job

    async def run():
        original_spawn = asyncio.create_subprocess_exec
        children, confirmation, waited = [], asyncio.Event(), asyncio.Event()
        started = asyncio.get_running_loop().time()
        observed = {}

        async def spawn(*args, **kwargs):
            child = await original_spawn(*args[:-1], 'import sys,time;sys.stdin.buffer.read();time.sleep(60)', **kwargs)
            actual_wait = child.wait
            item = {'child': child, 'identity': processes.identity(child.pid), 'wait': actual_wait}
            children.append(item)

            async def wait():
                code = await actual_wait()
                item['returncode'] = code
                item['actual_wait_elapsed'] = asyncio.get_running_loop().time() - started
                waited.set()
                if hold_wait:
                    await confirmation.wait()
                return code

            child.wait = wait
            return child

        monkeypatch.setattr(asyncio, 'create_subprocess_exec', spawn)
        adapter = LocalTrainingAdapter()
        job = Job(Binding('reader-allowance', 'a' * 64, 'b' * 40, 'c' * 40), 'job-original')
        try:
            with pytest.raises(ValueError, match='allowance exhausted'):
                await adapter.poll_job(job, timeout=0)
            assert not children
            with pytest.raises(ValueError, match='reader_cleanup_unconfirmed' if hold_wait else 'timed out'):
                await adapter.poll_job(job, timeout=1.2)
            observed['reader_return_elapsed'] = asyncio.get_running_loop().time() - started
            await asyncio.wait_for(waited.wait(), 2)
            if hold_wait:
                with pytest.raises(ValueError, match='reader_cleanup_unconfirmed'):
                    await adapter.collect_screen(job, timeout=1.2)
                assert len(children) == 1
                closing = asyncio.create_task(adapter.close())
                await asyncio.sleep(.02)
                assert not closing.done()
                confirmation.set()
                await closing
            await adapter.close()
            assert not adapter._reader_resources
            observed['close_elapsed'] = asyncio.get_running_loop().time() - started
            assert len(children) == 1 and children[0]['returncode'] == -9
            with pytest.raises((OSError, ValueError)):
                processes.identity(children[0]['identity']['pid'])
        finally:
            (tmp_path / 'native-reader-observation.json').write_text(json.dumps({
                'T': 1.2, 'hold_wait': hold_wait, **observed, 'children': [
                    {'identity': item['identity'], 'actual_returncode': item.get('returncode'),
                     'process_returncode': item['child'].returncode,
                     'actual_wait_elapsed': item.get('actual_wait_elapsed')} for item in children]}, indent=2) + '\n')
            confirmation.set()
            for item in children:
                if item['child'].returncode is None:
                    item['child'].kill()
                await item['wait']()
            await adapter.close()

    asyncio.run(run())


def test_budget_completion_spends_one_allowance_across_reader_calls(tmp_path, monkeypatch):
    import asyncio
    from dataclasses import asdict
    from types import SimpleNamespace
    from ergora.reference_training_budget import BudgetedStart

    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/temporal'))
    from perf_temporal.models import Binding, Experiment, Job, Observation, ScreenDecision

    binding = Binding('budget-reader-allowance', 'a' * 64, 'b' * 40, 'c' * 40)
    job, calls = Job(binding, 'job-original'), []
    spec = asdict(Experiment(binding, 'test://original'))
    runner = {'id': 'original-runner'}
    budget = BudgetedStart.__new__(BudgetedStart)
    budget.intent = {'observation': {'experiment': {'spec': spec, 'current_runner': runner}}}
    budget.operation = SimpleNamespace(native_request=lambda: {'experiment': spec, 'runner': runner},
        sha=lambda value: json.dumps(value, sort_keys=True), root=tmp_path, ident=binding.experiment_id)

    class Adapter:
        __slots__ = ()

        async def lookup_job(self, experiment):
            await asyncio.sleep(.01)
            return job

        async def poll_job(self, original, *, timeout=20):
            calls.append(('poll', timeout))
            await asyncio.sleep(.01)
            return Observation(original, 'SCREEN_COMPLETED')

        async def collect_screen(self, original, *, timeout=20):
            calls.append(('screen', timeout))
            return ScreenDecision(original, 'SCREEN_COMPLETED', 'd' * 64, 'test://screen', 'original screen')

    result = asyncio.run(budget.completion(Adapter(), timeout=1.2))
    assert result['status'] == 'completed' and result['gate'] is None
    assert result['screen']['job'] == asdict(job)
    assert [row[0] for row in calls] == ['poll', 'screen']
    assert 0 < calls[1][1] < calls[0][1] < 1.2


@pytest.mark.skipif(sys.platform != 'linux', reason='Actual SIGINT, child wait and PID/boot/start identity')
@pytest.mark.parametrize('boundary', ['poll', 'kill', 'poll-kill-wait', 'kill-error'])
def test_training_reader_cleanup_interrupt_keeps_original_wait(tmp_path, monkeypatch, boundary):
    import signal
    from ergora import processes

    children, identities, waits, interrupts, events = [], [], [], [], []
    pending = boundary.split('-') if boundary != 'kill-error' else []
    original_spawn = reference.subprocess.Popen
    harness_cleanup = False

    def interrupt(operation):
        if not harness_cleanup and pending and pending[0] == operation:
            pending.pop(0)
            events.append(operation + '-SIGINT')
            try:
                signal.raise_signal(signal.SIGINT)
            except KeyboardInterrupt as error:
                interrupts.append(error)
                raise

    def spawn(*args, **kwargs):
        child = original_spawn(*args, **kwargs)
        children.append(child)
        identities.append(processes.identity(child.pid))
        actual_poll, actual_kill, actual_wait = child.poll, child.kill, child.wait

        def poll():
            interrupt('poll')
            return actual_poll()

        def kill():
            interrupt('kill')
            actual_kill()
            if boundary == 'kill-error' and not harness_cleanup:
                raise OSError('controlled kill initiation failure after actual signal')

        def wait(*args, **kwargs):
            interrupt('wait')
            code = actual_wait(*args, **kwargs)
            waits.append(code)
            events.append('actual-wait-confirmed')
            return code

        child.poll, child.kill, child.wait = poll, kill, wait
        return child

    monkeypatch.setattr(reference.subprocess, 'Popen', spawn)
    project = {'registration': {'definition': {'execution': {
        'state_directory': str(tmp_path / 'state'), 'config_directory': str(tmp_path / 'config')}}}}
    try:
        expected = ValueError if boundary == 'kill-error' else KeyboardInterrupt
        with pytest.raises(expected) as caught:
            reference._training_reader(project, 'import sys,time;sys.stdin.buffer.read();time.sleep(60)', {}, timeout=.12)
        events.append('caller-received-' + type(caught.value).__name__)
        assert len(children) == 1 and waits == [-9]
        assert not pending and children[0].returncode == -9
        assert all(stream.closed for stream in (children[0].stdin, children[0].stdout, children[0].stderr))
        with pytest.raises((OSError, ValueError)):
            processes.identity(identities[0]['pid'])
        if boundary == 'kill-error':
            assert 'controlled kill initiation failure' in str(caught.value) and 'overrun=' in str(caught.value)
        else:
            assert caught.value is interrupts[0]
    finally:
        (tmp_path / 'cleanup-before-harness.json').write_text(json.dumps({
            'boundary': boundary, 'identities': identities, 'production_waits': list(waits),
            'returncodes': [child.returncode for child in children], 'events': list(events)}, indent=2) + '\n')
        harness_cleanup = True
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait()
        (tmp_path / 'cleanup-after-harness.json').write_text(json.dumps({
            'returncodes': [child.returncode for child in children], 'waits': waits}, indent=2) + '\n')
