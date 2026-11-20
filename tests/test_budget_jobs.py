"""Real job owners and process trees; controlled bodies never call a model."""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

import ergora.native.resources as native_resources
import ergora
import ergora.configuration.registrations as registrations
import ergora.development.application as tasks
from ergora.development import envelopes as task_envelopes
from ergora.development.inputs import execution_input
from ergora.storage.state import State
from test_task_budget import budget_creation, budget_graph, full_creation, full_graph, work_creation, work_graph
from test_registrations import design_policy, installation, registration
from test_task_creation import creation_project, _files
from ergora._paths import IMPORT_ROOT, PACKAGE_ROOT


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Budgeted job owners require Linux/WSL2')


def _prepare(budget_creation, monkeypatch, *, wall=8, reserve=2, omit_admission=False):
    pytest.importorskip('temporalio')
    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=wall, cleanup_seconds=reserve)
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=preview['prepare_sha256'])
    document = preview['files']['task.spec.json']
    runtime = Path(registered['execution']['state_directory'])
    config = Path(registered['execution']['config_directory'])
    roots = {key: str(runtime / key) for key in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    (config / 'adapter.json').write_text(json.dumps({**roots, 'trusted_receipts': True}))
    adapter = execution_input(document).adapter({**roots, 'trusted_receipts': True})
    context = task_envelopes.initial_preparation_contexts(document, document['legacy_spec']['request']['repository']['starting_sha'])[0]
    job = asyncio.run(adapter.submit(context))
    path = adapter.roots['requests'] / definition['task_id'] / (job['job_id'] + '.json')
    if omit_admission:
        envelope = json.loads(path.read_bytes())
        del envelope['context']['admission']
        envelope['job_sha256'] = task_envelopes.identity(envelope['context'])
        path.write_text(json.dumps(envelope))
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=str(config), AGENTFLOW_STATE_DIR=str(runtime),
        PYTHONPATH=os.pathsep.join(map(str, (IMPORT_ROOT,
            Path(registered['execution']['installation']) / 'local',
            Path(registered['execution']['installation']) / 'upstream/platform'))))
    folder = runtime / 'workspaces' / definition['task_id'] / 'jobs' / job['job_id'] / 'budget'
    return state, document, adapter, job, path, environment, folder


def _launch(state, path, environment, *, worker='', owner='', service=False, job_owner=False):
    # Public process() selects its owner from the trusted published input;
    # lifecycle-only tests can select the same original owner directly below.
    body_prefix = worker
    owner_source = '''
from ergora.runtime import processes
original_run = processes.run
def instrument(argv, *args, **kwargs):
    if argv[-1] == 'from ergora.development.runtime.executor import pending_job;pending_job()':
        argv = [*argv[:-1], PREFIX + '\\n' + argv[-1]]
    return original_run(argv, *args, **kwargs)
processes.run = instrument
''' .replace('PREFIX', repr(body_prefix)) + owner + '\nfrom ergora.development.runtime.jobs import main;main()'
    source = '''
import json,subprocess,sys
from pathlib import Path
original_launch = subprocess.Popen
def launch(argv, **kwargs):
    if argv[-1] == 'from ergora.development.runtime.jobs import main;main()':
        argv = [*argv[:-1], OWNER]
    return original_launch(argv, **kwargs)
subprocess.Popen = launch
from ergora.development.runtime.executor import process
print(json.dumps(process(Path(sys.argv[1]), Path(sys.argv[2]))))
''' .replace('OWNER', repr(owner_source))
    if job_owner:
        # Controlled lifecycle-only inputs bypass application admission. The
        # original owner, supervisor, process records and ledger remain real.
        source = source.replace('from ergora.development.runtime.executor import process',
            'from ergora.development.runtime.jobs import BudgetedJob\n'
            'def process(path, home):\n'
            '    runtime = Path(__import__("os").environ["AGENTFLOW_STATE_DIR"])\n'
            '    document = json.loads((runtime / "tasks" / path.parent.name / "task.spec.json").read_bytes())\n'
            '    return BudgetedJob(path, home, document).run()')
    if service:
        source = source.replace(
            'from ergora.development.runtime.executor import process\nprint(json.dumps(process(Path(sys.argv[1]), Path(sys.argv[2]))))',
            'from ergora.development.runtime.executor import main\nmain(Path(sys.argv[2])'
            + (', request=Path(sys.argv[1]))' if service == 'request' else ')'))
    return subprocess.Popen([sys.executable, '-P', '-c', source, str(path), str(state.root)],
        env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _result(process):
    stdout, stderr = process.communicate(timeout=20)
    assert process.returncode == 0, stdout + stderr
    return json.loads(stdout)


_PENDING = '''
import ergora.development.runtime.executor as reference_executor
from agent_platform import executor as original
from agent_platform.core import read,STATE
def pending(envelope, home):
    context = envelope['context']
    session = original.claim(envelope['job_id'], envelope['job_sha256'])
    return {'schema_version': 1, 'job_id': envelope['job_id'], 'job_sha256': envelope['job_sha256'],
        'state': 'SUCCEEDED', 'actor': {'id': 'controlled-body', 'session_id': session, 'role': 'inspector', 'kind': 'agent'},
        'candidate_sha': context['expected_candidate_sha'], 'artifacts': [], 'checks': []}
reference_executor._execute = pending
'''


def _monitor_frame(tmp_path, *, cutoff_seconds=1.25, timeout=1.25):
    runtime = tmp_path / 'runtime'
    folder = runtime / 'processes' / ('af-oracle-' + '8' * 64 + '-' + '9' * 64)
    folder.mkdir(parents=True)
    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    marker = tmp_path / 'child.json'
    finished = tmp_path / 'child-finished'
    command = [sys.executable, '-I', '-S', '-B', '-c',
        'import json,os,time;from pathlib import Path;'
        f'Path({str(marker)!r}).write_text(json.dumps({{"pid":os.getpid(),"started":time.monotonic()}}));'
        f'time.sleep(10);Path({str(finished)!r}).touch()']
    request = {'schema_version': 1, 'name': folder.name, 'checkout': str(checkout),
        'output': str(tmp_path / 'output'), 'command': command, 'writable': False, 'fence': None,
        'timeout': timeout, 'model': None, 'protocol': None, 'policy': None,
        'deadline': {'monotonic': time.monotonic() + cutoff_seconds,
                     'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()},
        'binding': {'kind': 'fixed-text-verification-process-v1',
                    'subject': {'job_sha256': '8' * 64}, 'input_sha256': '2' * 64}}
    (folder / 'request.json').write_text(json.dumps(request))
    return runtime, folder, request, marker, finished


def _run_original_monitor(runtime, folder, *, snapshot_delay=0, admission_delay=0):
    # Only Git's readonly snapshot is controlled; admission, timeout and child
    # stopping use the actual native monitor and its original process group.
    source = '''
import json,sys,time
from pathlib import Path
sys.path.insert(0, NATIVE)
from agent_platform import process_job
folder = Path(sys.argv[1])
calls = []
def snapshot(path):
    (folder / 'snapshot-observed').touch()
    if not calls: time.sleep(DELAY)
    calls.append(True)
    return ('same', 'same', 'same')
process_job.snapshot = snapshot
actual_environment = process_job.child_environment
def child_environment(model):
    time.sleep(ADMISSION_DELAY)
    return actual_environment(model)
process_job.child_environment = child_environment
actual_clock = time.monotonic
clock_reads = []
def clock():
    observed = actual_clock()
    clock_reads.append(observed)
    return observed
process_job.time.monotonic = clock
actual_launch = process_job.subprocess.Popen
def launch(command, **kwargs):
    (folder / 'admission.json').write_text(json.dumps({'monotonic': actual_clock(),
        'sampled_monotonic': clock_reads[-1] if clock_reads else None,
        'timeout': float(command[3])}))
    return actual_launch(command, **kwargs)
process_job.subprocess.Popen = launch
process_job.run(folder)
'''.replace('NATIVE', repr(str(native_resources.ROOT / 'platform/local'))).replace(
        'ADMISSION_DELAY', repr(admission_delay)).replace('DELAY', repr(snapshot_delay))
    environment = dict(os.environ, AGENTFLOW_STATE_DIR=str(runtime),
                       AGENTFLOW_CONFIG_DIR=str(runtime.parent / 'config'))
    result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', source, str(folder)],
        env=environment, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads((folder / 'terminal.json').read_bytes())


@pytest.mark.parametrize('delayed_phase', ['snapshot', 'last-admission'])
def test_original_process_monitor_refuses_admission_after_stage_deadline(tmp_path, delayed_phase):
    runtime, folder, request, marker, finished = _monitor_frame(tmp_path)
    request_raw = (folder / 'request.json').read_bytes()
    terminal = _run_original_monitor(runtime, folder,
        **({'snapshot_delay': 1.45} if delayed_phase == 'snapshot' else {'admission_delay': 1.45}))
    assert terminal['returncode'] == 125 and 'deadline' in terminal['detail'].lower()
    assert not marker.exists() and not finished.exists() and not (folder / 'admission.json').exists()
    terminal_raw = (folder / 'terminal.json').read_bytes()
    assert _run_original_monitor(runtime, folder) == terminal
    assert (folder / 'terminal.json').read_bytes() == terminal_raw
    assert (folder / 'request.json').read_bytes() == request_raw
    assert not marker.exists() and not (folder / 'pid.json').exists()


def test_original_process_monitor_preserves_fractional_tail_and_stops_at_original_cutoff(tmp_path):
    runtime, folder, request, marker, finished = _monitor_frame(tmp_path)
    terminal = _run_original_monitor(runtime, folder, snapshot_delay=.6)
    admission = json.loads((folder / 'admission.json').read_bytes())
    assert 0 < admission['timeout'] < 1
    assert admission['timeout'] <= request['deadline']['monotonic'] - admission['sampled_monotonic']
    assert admission['monotonic'] < request['deadline']['monotonic']
    assert marker.exists() and not finished.exists() and terminal['returncode'] != 0
    pid = json.loads((folder / 'pid.json').read_bytes())['pid']
    assert not Path('/proc', str(pid)).exists()
    terminal_raw = (folder / 'terminal.json').read_bytes()
    child_raw = marker.read_bytes()
    assert _run_original_monitor(runtime, folder) == terminal
    assert (folder / 'terminal.json').read_bytes() == terminal_raw and marker.read_bytes() == child_raw

    # A later check shares the original absolute cutoff; the first terminal
    # never grants a fresh interval to another original request.
    successor = folder.with_name('af-oracle-' + '8' * 64 + '-' + 'a' * 64)
    successor.mkdir()
    (successor / 'request.json').write_text(json.dumps({**request, 'name': successor.name}))
    refused = _run_original_monitor(runtime, successor)
    assert refused['returncode'] == 125 and not (successor / 'admission.json').exists()
    assert marker.read_bytes() == child_raw


def test_original_process_monitor_rejects_deadline_from_another_boot(tmp_path):
    runtime, folder, request, marker, finished = _monitor_frame(tmp_path, cutoff_seconds=10)
    request['deadline']['boot_id'] = '0' * 36
    (folder / 'request.json').write_text(json.dumps(request))
    terminal = _run_original_monitor(runtime, folder)
    assert terminal['returncode'] == 125 and 'boot' in terminal['detail'].lower()
    assert not marker.exists() and not finished.exists() and not (folder / 'admission.json').exists()


@pytest.mark.parametrize('boundary', ['sandbox', 'monitor'])
def test_fixed_binding_requires_original_deadline_before_native_admission(tmp_path, boundary):
    runtime, folder, request, marker, finished = _monitor_frame(tmp_path)
    del request['deadline']
    (folder / 'request.json').write_text(json.dumps(request))
    if boundary == 'monitor':
        terminal = _run_original_monitor(runtime, folder)
        assert terminal['returncode'] == 125 and 'deadline' in terminal['detail'].lower()
        assert not (folder / 'started.json').exists() and not (folder / 'admission.json').exists()
        assert not (folder / 'snapshot-observed').exists()
    else:
        source = '''
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0, NATIVE)
from agent_platform.core import Blocked,STATE
from agent_platform.sandbox import Sandbox
request = json.load(sys.stdin)
sandbox = Sandbox.__new__(Sandbox)
sandbox.env = {}
sandbox.probe = lambda: {'available': True}
def forbidden(*args, **kwargs):
    raise AssertionError('A fixed request without its deadline launched a monitor')
subprocess.Popen = forbidden
try:
    sandbox.run(request['name'], Path(request['checkout']), Path(request['output']),
        request['command'], writable=False, timeout=request['timeout'], binding=request['binding'])
except Blocked as error:
    assert 'deadline' in str(error).lower(), str(error)
else:
    raise AssertionError('Fixed process admission omitted its original deadline')
assert not (STATE / 'processes').exists()
'''.replace('NATIVE', repr(str(native_resources.ROOT / 'platform/local')))
        environment = dict(os.environ, AGENTFLOW_STATE_DIR=str(tmp_path / 'sandbox-runtime'),
                           AGENTFLOW_CONFIG_DIR=str(tmp_path / 'config'))
        result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', source], input=json.dumps(request),
            env=environment, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stdout + result.stderr
    assert not marker.exists() and not finished.exists() and not (folder / 'pid.json').exists()


def test_sandbox_original_deadline_does_not_renew_observation_or_completed_request(tmp_path):
    source = '''
import hashlib,json,subprocess,sys,time
from pathlib import Path
sys.path.insert(0, NATIVE)
from agent_platform.core import Blocked,STATE,write
from agent_platform.sandbox import Sandbox
sandbox = Sandbox.__new__(Sandbox)
sandbox.env = {}
sandbox.probe = lambda: {'available': True}
checkout, output = STATE / 'checkout', STATE / 'output'
ordinary = sandbox.request('ordinary', checkout, output, ['true'], writable=False)
assert ordinary == {'schema_version': 1, 'name': 'ordinary', 'checkout': str(checkout.resolve()),
    'output': str(output.resolve()), 'command': ['true'], 'writable': False, 'fence': None,
    'timeout': 1800, 'model': None, 'protocol': None, 'policy': None}
deadline = {'monotonic': time.monotonic() - 31,
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
binding = {'kind': 'fixed-text-verification-process-v1', 'subject': {}, 'input_sha256': '4' * 64}
name = 'af-oracle-' + '5' * 64 + '-' + '6' * 64
folder = STATE / 'processes' / name
def forbidden(*args, **kwargs):
    raise AssertionError('An exhausted original observation window launched another monitor')
subprocess.Popen = forbidden
try:
    sandbox.run(name, checkout, output, ['true'], writable=False, binding=binding, deadline=deadline)
except Blocked as error:
    assert 'outcome unknown' in str(error), str(error)
else:
    raise AssertionError('Missing terminal was accepted')
request_raw = (folder / 'request.json').read_bytes()
request = json.loads(request_raw)
assert request['deadline'] == deadline
digest = hashlib.sha256(json.dumps(request, ensure_ascii=False, sort_keys=True,
    separators=(',', ':'), allow_nan=False).encode()).hexdigest()
write(folder / 'terminal.json', {'name': name, 'returncode': 125,
    'binding': binding, 'request_sha256': digest})
assert sandbox.run(name, checkout, output, ['true'], writable=False,
    binding=binding, deadline=deadline) == 125
assert (folder / 'request.json').read_bytes() == request_raw
assert not (folder / 'started.json').exists() and not (folder / 'pid.json').exists()
'''.replace('NATIVE', repr(str(native_resources.ROOT / 'platform/local')))
    environment = dict(os.environ, AGENTFLOW_STATE_DIR=str(tmp_path / 'runtime'),
                       AGENTFLOW_CONFIG_DIR=str(tmp_path / 'config'))
    result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', source],
        env=environment, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


def test_original_process_monitor_preserves_started_without_terminal_as_unknown(tmp_path):
    """Controlled lost-monitor record; the actual monitor must not manufacture an outcome."""
    runtime = tmp_path / 'runtime'
    folder = runtime / 'processes' / ('af-oracle-' + '1' * 64 + '-' + '2' * 64)
    folder.mkdir(parents=True)
    marker = tmp_path / 'forbidden-second-body'
    request = {'name': folder.name, 'output': str(tmp_path / 'output'),
        'command': [sys.executable, '-c', f'from pathlib import Path;Path({str(marker)!r}).touch()'],
        'binding': {'kind': 'fixed-text-verification-process-v1', 'subject': {}, 'input_sha256': '2' * 64}}
    request_raw = json.dumps(request).encode()
    started_raw = json.dumps({'name': folder.name, 'binding': request['binding'], 'monitor_pid': 99999999}).encode()
    (folder / 'request.json').write_bytes(request_raw)
    (folder / 'started.json').write_bytes(started_raw)
    code = ('import sys;from pathlib import Path;sys.path.insert(0,'
            + repr(str(native_resources.ROOT / 'platform/local')) + ');'
            'from agent_platform.process_job import run;run(Path(sys.argv[1]))')
    environment = dict(os.environ, AGENTFLOW_STATE_DIR=str(runtime), AGENTFLOW_CONFIG_DIR=str(tmp_path / 'config'))
    for _ in range(2):
        result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code, str(folder)],
                                env=environment, capture_output=True, text=True, timeout=10)
        assert result.returncode != 0 and 'unknown outcome' in result.stderr
        assert not marker.exists() and not (folder / 'terminal.json').exists()
        assert (folder / 'request.json').read_bytes() == request_raw
        assert (folder / 'started.json').read_bytes() == started_raw


def _prepare_fixed_verify_job(budget_creation, monkeypatch):
    from ergora.development import verification
    from test_full_stage_materials import _fixed_observation_checks

    state, document, adapter, initial_job, initial_path, env, _ = _prepare(budget_creation, monkeypatch, wall=15)
    project = state.project('demo')
    project['registration']['definition']['trusted_checks'] = _fixed_observation_checks([
        {'id': 'case', 'input': None, 'expected': True}])
    document = {**document, 'verification': verification.snapshot(project)}
    document['sha256'] = task_envelopes.identity({key: value for key, value in document.items() if key != 'sha256'})
    runtime = Path(env['AGENTFLOW_STATE_DIR'])
    (runtime / 'tasks' / initial_job['task_id'] / 'task.spec.json').write_text(json.dumps(document))
    context = {**initial_job['context'], 'stage': 'verify', 'admission': document}
    context['job_id'] = initial_job['task_id'] + '-' + task_envelopes.identity({'stage': 'verify'})[:24]
    job = {'task_id': initial_job['task_id'], 'job_id': context['job_id'],
           'job_sha256': task_envelopes.identity(context), 'context': context}
    path = initial_path.with_name(job['job_id'] + '.json')
    path.write_text(json.dumps({'schema_version': 1, 'job_id': job['job_id'],
                               'job_sha256': job['job_sha256'], 'context': context}))
    folder = runtime / 'workspaces' / job['task_id'] / 'jobs' / job['job_id'] / 'budget'
    (Path(env['AGENTFLOW_CONFIG_DIR']) / 'platform.json').write_text(json.dumps({'stage_walltime_seconds': 30}))
    return state, document, adapter, job, path, env, folder


def test_fixed_stage_cutoff_includes_constructor_and_recovery_keeps_original_deadline(
        budget_creation, monkeypatch, tmp_path):
    from ergora.development import budget as reference_budget

    state, document, adapter, job, path, env, folder = _prepare_fixed_verify_job(budget_creation, monkeypatch)
    (Path(env['AGENTFLOW_CONFIG_DIR']) / 'platform.json').write_text(json.dumps({'stage_walltime_seconds': 2}))
    marker = tmp_path / 'constructor-entered.json'
    worker = f'''
import json,os,time
from pathlib import Path
from ergora.development.runtime.executor import Executor
def blocked(self, *args):
    owner = json.loads((Path(os.environ['ERGORA_REFERENCE_JOB_OWNER']) / 'owner.json').read_bytes())
    Path({str(marker)!r}).write_text(json.dumps({{'monotonic': time.monotonic(),
        'deadline': owner['verification_deadline']}}))
    time.sleep(30)
    raise AssertionError('Expired constructor continued into verification')
Executor.__init__ = blocked
'''
    receipt = _result(_launch(state, path, env, worker=worker, job_owner=True))
    assert receipt['state'] == 'CANCELLED'
    entered = json.loads(marker.read_bytes())
    owner_raw = (folder / 'owner.json').read_bytes()
    owner = json.loads(owner_raw)
    assert entered['deadline'] == owner['verification_deadline']
    assert entered['monotonic'] < owner['verification_deadline']['monotonic']
    assert reference_budget.remaining(document['budget']['instance']) > 0
    stopped = json.loads((folder / 'stopped.json').read_bytes())
    assert stopped['body']['status'] == 'cancelled' and stopped['cleanup_confirmed'] is True
    assert not (folder / 'pending.json').exists() and not (folder / 'model-attempt.json').exists()
    assert not list((Path(env['AGENTFLOW_STATE_DIR']) / 'processes').glob('af-oracle-*'))
    marker_raw = marker.read_bytes()
    assert _result(_launch(state, path, env, worker=worker, job_owner=True)) == receipt
    assert (folder / 'owner.json').read_bytes() == owner_raw and marker.read_bytes() == marker_raw
    assert asyncio.run(adapter.poll(job)) == receipt


def test_fixed_stage_reaping_confirms_cleanup_without_inventing_nested_terminal(
        budget_creation, monkeypatch, tmp_path):
    import sqlite3
    from ergora.development import verification

    state, document, adapter, job, path, env, folder = _prepare_fixed_verify_job(budget_creation, monkeypatch)
    (Path(env['AGENTFLOW_CONFIG_DIR']) / 'platform.json').write_text(json.dumps({'stage_walltime_seconds': 3}))
    marker = tmp_path / 'nested-child.json'
    replay = tmp_path / 'forbidden-body-replay'
    checkout = tmp_path / 'controlled-readonly-checkout'
    checkout.mkdir()
    child = ('import json,os,signal,time;from pathlib import Path;'
        'signal.signal(signal.SIGTERM,signal.SIG_IGN);'
        f'Path({str(marker)!r}).write_text(json.dumps({{"pid":os.getpid()}}));time.sleep(60)')
    monitor = '''
import sys,time
from pathlib import Path
from agent_platform import process_job
process_job.snapshot = lambda path: ('same', 'same', 'same')
def delayed_stop(process):
    time.sleep(30)
process_job.stop = delayed_stop
process_job.run(Path(sys.argv[1]))
'''
    worker = _PENDING + f'''
import os,subprocess,sys
from pathlib import Path
from agent_platform.core import read,write
from agent_platform.sandbox import Sandbox
from ergora.development import verification
def nested(envelope, home):
    binding = {{'kind': 'fixed-text-verification-process-v1', 'subject': {{
        'job_id': envelope['job_id'], 'job_sha256': envelope['job_sha256'],
        'admission_sha256': envelope['context']['admission']['sha256']}}, 'input_sha256': '4' * 64}}
    name = verification.process_name(binding)
    folder = STATE / 'processes' / name
    deadline = read(Path(os.environ['ERGORA_REFERENCE_JOB_OWNER']) / 'owner.json')['verification_deadline']
    sandbox = Sandbox.__new__(Sandbox)
    request = sandbox.request(name, Path({str(checkout)!r}), STATE / 'nested-output',
        [sys.executable, '-I', '-S', '-B', '-c', {child!r}], writable=False,
        timeout=60, binding=binding, deadline=deadline)
    write(folder / 'request.json', request)
    subprocess.run([sys.executable, '-P', '-c', {monitor!r}, str(folder)], check=True)
    raise AssertionError('Unconfirmed nested monitor returned a new receipt')
reference_executor._execute = nested
'''
    process = _launch(state, path, env, worker=worker, job_owner=True)
    stdout, stderr = process.communicate(timeout=20)
    assert process.returncode != 0 and 'fixed process outcome unknown despite confirmed outer cleanup' in stderr, stdout + stderr
    assert marker.exists()
    runtime = Path(env['AGENTFLOW_STATE_DIR'])
    binding = {'kind': 'fixed-text-verification-process-v1', 'subject': {
        'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
        'admission_sha256': document['sha256']}, 'input_sha256': '4' * 64}
    process_folder = runtime / 'processes' / verification.process_name(binding)
    stopped = json.loads((folder / 'stopped.json').read_bytes())
    assert stopped['cleanup_confirmed'] is True and stopped['body']['status'] == 'cancelled'
    owner = (folder / 'owner.json').read_bytes()
    request = (process_folder / 'request.json').read_bytes()
    started = (process_folder / 'started.json').read_bytes()
    assert json.loads(request)['deadline'] == json.loads(owner)['verification_deadline']
    child_pid = json.loads(marker.read_bytes())['pid']
    monitor_pid = json.loads(started)['monitor_pid']
    native_pid = json.loads((process_folder / 'pid.json').read_bytes())['pid']
    assert all(not Path('/proc', str(pid)).exists() for pid in (child_pid, monitor_pid, native_pid))
    assert not (process_folder / 'terminal.json').exists() and asyncio.run(adapter.poll(job)) is None
    repeated = _launch(state, path, env, job_owner=True,
        worker=f'from pathlib import Path\nPath({str(replay)!r}).touch()\n' + _PENDING)
    stdout, stderr = repeated.communicate(timeout=20)
    assert repeated.returncode != 0 and 'fixed process outcome unknown despite confirmed outer cleanup' in stderr, stdout + stderr
    assert not replay.exists() and not (process_folder / 'terminal.json').exists()
    assert (folder / 'owner.json').read_bytes() == owner
    assert (process_folder / 'request.json').read_bytes() == request and (process_folder / 'started.json').read_bytes() == started
    with sqlite3.connect(runtime / 'executor.sqlite3') as db:
        assert db.execute('SELECT hash,state FROM jobs WHERE id=?', (job['job_id'],)).fetchone() == (
            job['job_sha256'], 'OWNED')


@pytest.mark.parametrize('orphan_owner', ['unrelated', 'current-unsubmitted'])
def test_fixed_budget_job_finalizes_despite_unsubmitted_process_directory(
        budget_creation, monkeypatch, tmp_path, orphan_owner):
    """An interrupted request publication cannot occupy an unrelated job's ledger slot."""
    import sqlite3

    state, document, adapter, job, path, env, folder = _prepare_fixed_verify_job(budget_creation, monkeypatch)
    runtime = Path(env['AGENTFLOW_STATE_DIR'])
    job_sha = 'a' * 64 if orphan_owner == 'unrelated' else job['job_sha256']
    orphan = runtime / 'processes' / ('af-oracle-' + job_sha + '-' + 'b' * 64)
    orphan.mkdir(parents=True)
    receipt = _result(_launch(state, path, env, worker=_PENDING, job_owner=True))
    assert receipt['state'] == 'SUCCEEDED'
    assert json.loads((folder / 'stopped.json').read_bytes())['cleanup_confirmed'] is True
    assert json.loads((folder / 'collection-stopped.json').read_bytes())['cleanup_confirmed'] is True
    assert asyncio.run(adapter.poll(job)) == receipt and list(orphan.iterdir()) == []
    with sqlite3.connect(runtime / 'executor.sqlite3') as db:
        assert db.execute('SELECT hash,state FROM jobs WHERE id=?', (job['job_id'],)).fetchone() == (
            job['job_sha256'], 'SUCCEEDED')
    marker = tmp_path / 'forbidden-body-replay'
    assert _result(_launch(state, path, env, job_owner=True,
        worker=f'from pathlib import Path\nPath({str(marker)!r}).touch()\n' + _PENDING)) == receipt
    assert not marker.exists() and list(orphan.iterdir()) == []


@pytest.mark.parametrize('launch_evidence', ['runner.log', 'lock', 'started.json', 'pid.json', 'terminal.json', 'request.json'])
def test_own_incomplete_fixed_process_publication_remains_unknown_without_replay(
        budget_creation, monkeypatch, tmp_path, launch_evidence):
    import sqlite3

    state, document, adapter, job, path, env, folder = _prepare_fixed_verify_job(budget_creation, monkeypatch)
    runtime = Path(env['AGENTFLOW_STATE_DIR'])
    process_folder = runtime / 'processes' / ('af-oracle-' + job['job_sha256'] + '-' + 'c' * 64)
    process_folder.mkdir(parents=True)
    (process_folder / launch_evidence).write_bytes(b'Incomplete original publication')
    marker = tmp_path / 'forbidden-body-replay'
    for worker in (_PENDING, f'from pathlib import Path\nPath({str(marker)!r}).touch()\n' + _PENDING):
        process = _launch(state, path, env, worker=worker, job_owner=True)
        stdout, stderr = process.communicate(timeout=20)
        assert process.returncode != 0 and 'fixed process outcome unknown despite confirmed outer cleanup' in stderr, stdout + stderr
        assert json.loads((folder / 'stopped.json').read_bytes())['cleanup_confirmed'] is True
        assert asyncio.run(adapter.poll(job)) is None and not (folder / 'collection').exists()
        assert not marker.exists()
        assert (process_folder / launch_evidence).read_bytes() == b'Incomplete original publication'
        with sqlite3.connect(runtime / 'executor.sqlite3') as db:
            assert db.execute('SELECT hash,state FROM jobs WHERE id=?', (job['job_id'],)).fetchone() == (
                job['job_sha256'], 'OWNED')


@pytest.mark.parametrize('collection_attempted', [False, True])
def test_unconfirmed_nested_fixed_process_retains_owned_job_after_outer_cleanup(
        budget_creation, monkeypatch, tmp_path, collection_attempted):
    """A controlled body loses its monitor reply; real cleanup cannot establish that reply."""
    import sqlite3
    from ergora.development import verification

    state, document, _, job, path, env, folder = _prepare_fixed_verify_job(budget_creation, monkeypatch)
    runtime = Path(env['AGENTFLOW_STATE_DIR'])
    binding = {'kind': 'fixed-text-verification-process-v1', 'subject': {
        'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
        'admission_sha256': document['sha256']}, 'input_sha256': '4' * 64}
    process_folder = runtime / 'processes' / verification.process_name(binding)
    marker = tmp_path / 'forbidden-nested-reexecution'
    worker = _PENDING + '''
from agent_platform.core import write
from ergora.development import verification
actual_pending = reference_executor._execute
def lost_nested(envelope, home):
    receipt = actual_pending(envelope, home)
    receipt['state'] = 'FAILED'
    receipt['detail'] = 'Controlled missing nested outcome; this original failure cannot become success'
    binding = {'kind': 'fixed-text-verification-process-v1', 'subject': {
        'job_id': envelope['job_id'], 'job_sha256': envelope['job_sha256'],
        'admission_sha256': envelope['context']['admission']['sha256']}, 'input_sha256': '4' * 64}
    process_folder = STATE / 'processes' / verification.process_name(binding)
    write(process_folder / 'request.json', {'name': process_folder.name, 'binding': binding})
    write(process_folder / 'started.json', {'name': process_folder.name, 'binding': binding})
    return receipt
reference_executor._execute = lost_nested
'''
    first = _launch(state, path, env, worker=worker, job_owner=True)
    stdout, stderr = first.communicate(timeout=20)
    assert first.returncode != 0 and 'fixed process outcome unknown despite confirmed outer cleanup' in stderr, stdout + stderr
    assert json.loads((folder / 'stopped.json').read_bytes())['cleanup_confirmed'] is True
    attempt = (folder / 'attempt.json').read_bytes()
    started = (process_folder / 'started.json').read_bytes()
    pending = (folder / 'pending.json').read_bytes()
    body_output = (folder / 'body/stdout.txt').read_bytes()
    stopped = (folder / 'stopped.json').read_bytes()
    budget = json.dumps(document['budget']['instance'], sort_keys=True)
    forbidden_body = f'from pathlib import Path\nPath({str(marker)!r}).touch()\n' + _PENDING
    repeated = _launch(state, path, env,
        worker=forbidden_body, job_owner=True)
    stdout, stderr = repeated.communicate(timeout=20)
    assert repeated.returncode != 0 and 'fixed process outcome unknown despite confirmed outer cleanup' in stderr, stdout + stderr
    assert not marker.exists() and not (process_folder / 'terminal.json').exists()
    assert not (runtime / 'receipts' / job['task_id'] / (job['job_id'] + '.json')).exists()
    assert (folder / 'attempt.json').read_bytes() == attempt
    assert (process_folder / 'started.json').read_bytes() == started
    with sqlite3.connect(runtime / 'executor.sqlite3') as db:
        row = db.execute('SELECT hash,state FROM jobs WHERE id=?', (job['job_id'],)).fetchone()
    assert row == (job['job_sha256'], 'OWNED')

    # File visibility alone is not a confirmed original process terminal.
    (process_folder / 'terminal.json').write_text(json.dumps({'name': process_folder.name, 'returncode': 125}))
    invalid = _launch(state, path, env, worker=forbidden_body, job_owner=True)
    stdout, stderr = invalid.communicate(timeout=20)
    assert invalid.returncode != 0 and 'fixed process outcome unknown despite confirmed outer cleanup' in stderr
    assert not marker.exists() and not (folder / 'collection').exists()
    assert not (runtime / 'receipts' / job['task_id'] / (job['job_id'] + '.json')).exists()

    # Controlled late arrival of the original process outcome. This does not
    # rerun its body or upgrade the original failed pending receipt to success.
    request = json.loads((process_folder / 'request.json').read_bytes())
    (process_folder / 'terminal.json').write_text(json.dumps({'name': process_folder.name,
        'binding': request['binding'], 'request_sha256': verification.sha(request), 'returncode': 125}))
    if collection_attempted:
        (folder / 'collection').mkdir()
        (folder / 'collection/stdout.txt').write_bytes(b'Original incomplete collection output')
    recovered = _launch(state, path, env, worker=forbidden_body, job_owner=True)
    if collection_attempted:
        stdout, stderr = recovered.communicate(timeout=20)
        assert recovered.returncode != 0 and 'no confirmed stopping witness' in stderr, stdout + stderr
        assert (folder / 'collection/stdout.txt').read_bytes() == b'Original incomplete collection output'
        assert not (folder / 'collection-stopped.json').exists()
        assert not (runtime / 'receipts' / job['task_id'] / (job['job_id'] + '.json')).exists()
        expected_state = 'OWNED'
    else:
        receipt = _result(recovered)
        assert receipt == json.loads(pending) and receipt['state'] == 'FAILED'
        collected = (folder / 'collected.json').read_bytes()
        collection_stopped = (folder / 'collection-stopped.json').read_bytes()
        assert json.loads(collection_stopped)['cleanup_confirmed'] is True
        assert _result(_launch(state, path, env, worker=forbidden_body, job_owner=True)) == receipt
        assert (folder / 'collected.json').read_bytes() == collected
        assert (folder / 'collection-stopped.json').read_bytes() == collection_stopped
        expected_state = 'FAILED'
    assert not marker.exists()
    assert (folder / 'pending.json').read_bytes() == pending
    assert (folder / 'body/stdout.txt').read_bytes() == body_output
    assert (folder / 'stopped.json').read_bytes() == stopped
    assert (folder / 'attempt.json').read_bytes() == attempt
    assert (process_folder / 'started.json').read_bytes() == started
    original_input = json.loads((runtime / 'tasks' / job['task_id'] / 'task.spec.json').read_bytes())
    assert json.dumps(original_input['budget']['instance'], sort_keys=True) == budget
    with sqlite3.connect(runtime / 'executor.sqlite3') as db:
        row = db.execute('SELECT hash,state FROM jobs WHERE id=?', (job['job_id'],)).fetchone()
    assert row == (job['job_sha256'], expected_state)


@pytest.mark.parametrize('native_missing', [False, True])
def test_v2_rejects_original_budgeted_input_before_job_constructor_or_claim(budget_creation, monkeypatch, tmp_path, native_missing):
    old, document, adapter, job, path, environment, folder = _prepare(budget_creation, monkeypatch)
    original_files = _files(Path(environment['AGENTFLOW_STATE_DIR']))
    registered = json.loads(json.dumps(budget_creation[1]))
    state = State(tmp_path / 'design-control')
    config, runtime = tmp_path / 'design-config', tmp_path / 'design-runtime'
    registered.update(schema_version=2, design_policy=design_policy())
    registered['execution'].update(config_directory=str(config), state_directory=str(runtime))
    registrations.register(state, registered, 0)
    # Replay an intact, genuinely published v1 budget document/job into the new
    # native root. Its old binding is not a supported migration or recovery.
    # Regardless of its later owner checks, it must not claim a new v2 job.
    shutil.copytree(Path(environment['AGENTFLOW_STATE_DIR']) / 'tasks', runtime / 'tasks')
    selected = execution_input(document)
    target = selected.request_root(runtime / 'requests') / path.parent.name / path.name
    target.parent.mkdir(parents=True)
    target.write_bytes(path.read_bytes())
    roots = {key: str(runtime / key) for key in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    (config / 'adapter.json').write_text(json.dumps({**roots, 'trusted_receipts': True}))
    if native_missing:
        (config / 'projects/demo.json').unlink()
    environment.update(AGENTFLOW_CONFIG_DIR=str(config), AGENTFLOW_STATE_DIR=str(runtime))
    source = '''
import hashlib,json,sys
from pathlib import Path
import ergora.development.runtime.executor as driver
from ergora.development.runtime.jobs import BudgetedJob
starts={'job':0,'claim':0,'body':0,'model':0,'commands':0}
def observe(owner,name,label):
 original=getattr(owner,name)
 def counted(*args,**kwargs):
  starts[label]+=1
  return original(*args,**kwargs)
 setattr(owner,name,counted)
observe(BudgetedJob,'__init__','job')
observe(driver.original,'claim','claim')
observe(driver,'_execute','body')
for name in ('model','commands'): observe(driver.Executor,name,name)
try:
 driver.process(Path(sys.argv[1]),Path(sys.argv[2]))
except ValueError as error:
 assert 'design_policy_execution_unsupported' in str(error),str(error)
else: raise AssertionError('Budgeted input was admitted')
assert starts==dict.fromkeys(starts,0),starts
print(json.dumps({'starts':starts,'executor_module':driver.__file__,
 'executor_sha256':hashlib.sha256(Path(driver.__file__).read_bytes()).hexdigest()}))
'''
    result = subprocess.run([sys.executable, '-P', '-c', source, str(target), str(state.root)],
        capture_output=True, text=True, env=environment, timeout=20)
    (tmp_path / 'guard.stdout.txt').write_text(result.stdout)
    (tmp_path / 'guard.stderr.txt').write_text(result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    observation = json.loads(result.stdout)
    assert set(observation['starts'].values()) == {0}
    assert observation['executor_sha256'] == hashlib.sha256(
        (PACKAGE_ROOT / 'development/runtime/executor.py').read_bytes()).hexdigest()
    assert not (runtime / 'executor.sqlite3').exists() and not (runtime / 'workspaces').exists()
    assert _files(Path(budget_creation[1]['execution']['state_directory'])) == original_files


def test_constructor_lock_consumes_original_budget_and_cannot_reexecute(budget_creation, monkeypatch, tmp_path):
    import fcntl

    state, document, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch)
    lock_path = tmp_path / 'construction.lock'
    entered = tmp_path / 'construction-entered'
    worker = f'''
import fcntl
from pathlib import Path
from ergora.development.runtime.executor import Executor
original_constructor = Executor.__init__
def blocked(self, *args):
    Path({str(entered)!r}).touch()
    with Path({str(lock_path)!r}).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
    return original_constructor(self, *args)
Executor.__init__ = blocked
'''
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        outcome = _result(_launch(state, path, env, worker=worker))
    assert entered.exists() and outcome['state'] == 'CANCELLED'
    assert json.loads((folder / 'stopped.json').read_bytes())['cleanup_confirmed'] is True
    assert not (folder / 'model-attempt.json').exists()
    original = (folder / 'attempt.json').read_bytes()
    assert _result(_launch(state, path, env, worker=worker)) == outcome
    assert (folder / 'attempt.json').read_bytes() == original
    assert asyncio.run(adapter.poll(job)) == outcome


def test_real_executor_git_lock_is_inside_original_budget(budget_creation, monkeypatch, tmp_path):
    import fcntl

    state, document, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch)
    config = Path(env['AGENTFLOW_CONFIG_DIR'])
    (config / 'codex.toml').write_text('')
    (config / 'platform.json').write_text('{}')
    lock_path = folder.parents[2] / 'git.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    marker = tmp_path / 'real-prepare-entered'
    worker = f'''
from pathlib import Path
from ergora.development.runtime.executor import Executor
def real_prepare(self):
    Path({str(marker)!r}).touch()
    self.prepare()
    raise AssertionError('Occupied native Git lock was bypassed')
Executor.execute = real_prepare
'''
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        outcome = _result(_launch(state, path, env, worker=worker))
    assert marker.exists() and outcome['state'] == 'CANCELLED'
    assert not (lock_path.parent / 'repo.git').exists()
    assert not (folder / 'model-attempt.json').exists()


@pytest.mark.parametrize('terminal_state', ['SUCCEEDED', 'FAILED', 'CANCELLED'])
def test_pending_terminal_cannot_confirm_fence_while_detached_descendant_lives(
        budget_creation, monkeypatch, tmp_path, terminal_state):
    state, document, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch, wall=12)
    marker, release = tmp_path / 'reaping.json', tmp_path / 'allow-reap'
    worker = _PENDING + f'''
import os,subprocess,sys,time
from pathlib import Path
original_pending = reference_executor._execute
def with_child(*args):
    child = subprocess.Popen([sys.executable, '-c', 'import os,signal,time;os.setsid();signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'])
    receipt = original_pending(*args)
    receipt['state'] = {terminal_state!r}
    return receipt
reference_executor._execute = with_child
'''
    owner = f'''
import json,os,time
from pathlib import Path
original_reap = processes._reap_children
def delayed_reap():
    pids = Path('/proc/' + str(os.getpid()) + '/task/' + str(os.getpid()) + '/children').read_text().split()
    if pids and not Path({str(marker)!r}).exists():
        Path({str(marker)!r}).write_text(json.dumps(pids))
        while not Path({str(release)!r}).exists():
            time.sleep(.02)
    original_reap()
processes._reap_children = delayed_reap
'''
    process = _launch(state, path, env, worker=worker, owner=owner)
    try:
        deadline = time.monotonic() + 6
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        assert marker.exists()
        pids = json.loads(marker.read_bytes())
        assert all(Path('/proc/' + pid).exists() for pid in pids)
        assert (folder / 'pending.json').exists() and asyncio.run(adapter.poll(job)) is None
        fence = asyncio.run(adapter.fence({'task_id': job['task_id'], 'request_sha256': job['context']['request_sha256']}))
        assert fence['confirmed'] is False and fence['unresolved_jobs'] == [job['job_id']]
    finally:
        release.touch()
    outcome = _result(process)
    assert not any(Path('/proc/' + pid).exists() for pid in pids)
    assert outcome['state'] == 'CANCELLED'  # The newly written fence must be honored.
    assert asyncio.run(adapter.fence({'task_id': job['task_id'], 'request_sha256': job['context']['request_sha256']}))['confirmed'] is True


def test_slow_collection_cannot_publish_success(budget_creation, monkeypatch):
    state, document, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch, wall=5, reserve=2)
    owner = '''
collection_run = processes.run
def slow_collection(argv, *args, **kwargs):
    if argv[-1] == 'from ergora.development.runtime.jobs import collect;collect()':
        argv = [*argv[:-1], 'import time;time.sleep(30);' + argv[-1]]
    return collection_run(argv, *args, **kwargs)
processes.run = slow_collection
'''
    outcome = _result(_launch(state, path, env, worker=_PENDING, owner=owner))
    assert outcome['state'] == 'CANCELLED'
    collected = json.loads((folder / 'collection-stopped.json').read_bytes())
    assert collected['collection']['status'] == 'cancelled' and collected['cleanup_confirmed'] is True
    observations = [json.loads(p.read_bytes()) for p in (folder / 'finalizations').glob('*.json')]
    assert observations and observations[-1]['overrun_seconds'] >= 0


def test_final_fsync_cannot_publish_old_success_after_total_deadline(budget_creation, monkeypatch):
    state, document, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch, wall=5, reserve=2)
    owner = '''
import os,time
from pathlib import Path
actual_fsync = os.fsync
delayed = False
def slow_fsync(fd):
    global delayed
    if Path('/proc/self/fd/' + str(fd)).resolve().parent.name == 'finalizations' and not delayed:
        delayed = True
        time.sleep(5)
    return actual_fsync(fd)
os.fsync = slow_fsync
'''
    outcome = _result(_launch(state, path, env, worker=_PENDING, owner=owner))
    assert outcome['state'] == 'CANCELLED'
    observations = [json.loads(p.read_bytes()) for p in (folder / 'finalizations').glob('*.json')]
    assert len(observations) == 2 and any(row['overrun_seconds'] > 0 for row in observations)
    assert asyncio.run(adapter.poll(job)) == outcome


def test_missing_admission_still_uses_trusted_published_budget_owner(budget_creation, monkeypatch):
    state, document, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch, omit_admission=True)
    outcome = _result(_launch(state, path, env))
    assert outcome['state'] == 'FAILED' and 'complete published admission' in outcome['detail']
    assert (folder / 'stopped.json').is_file() and (folder / 'collection-stopped.json').is_file()
    assert not (folder / 'model-attempt.json').exists()


def test_uncertain_original_attempt_never_executes_its_body_again(budget_creation, monkeypatch, tmp_path):
    state, document, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch)
    owner = '''
from ergora.development.runtime.jobs import BudgetedJob
def lost(self, *args, **kwargs):
    raise SystemExit('Controlled loss after original attempt, before body dispatch')
BudgetedJob.supervise = lost
'''
    first = _launch(state, path, env, worker=_PENDING, owner=owner)
    stdout, stderr = first.communicate(timeout=20)
    assert first.returncode != 0 and 'no confirmed terminal' in stderr
    attempt = (folder / 'attempt.json').read_bytes()
    marker = tmp_path / 'forbidden-reexecution'
    second = _launch(state, path, env, worker=f'from pathlib import Path\nPath({str(marker)!r}).touch()\n' + _PENDING)
    stdout, stderr = second.communicate(timeout=20)
    assert second.returncode != 0 and 'no confirmed stopping witness' in stderr
    assert not marker.exists() and not (folder / 'body').exists()
    assert (folder / 'attempt.json').read_bytes() == attempt
    assert asyncio.run(adapter.poll(job)) is None


def test_published_terminal_recovers_only_original_ledger_update(budget_creation, monkeypatch, tmp_path):
    import sqlite3

    state, document, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch, wall=12)
    owner = '''
from ergora.development.runtime.jobs import BudgetedJob
def lost(self, receipt):
    raise SystemExit('Controlled loss after terminal link, before ledger update')
BudgetedJob.record_terminal = lost
'''
    first = _launch(state, path, env, worker=_PENDING, owner=owner)
    stdout, stderr = first.communicate(timeout=20)
    assert first.returncode != 0 and 'no confirmed terminal' in stderr
    original = asyncio.run(adapter.poll(job))
    assert original['state'] == 'SUCCEEDED'
    body_stdout = (folder / 'body/stdout.txt').read_bytes()
    marker = tmp_path / 'forbidden-reexecution'
    (Path(env['AGENTFLOW_CONFIG_DIR']) / 'platform.json').write_text(json.dumps({'max_parallel_jobs': 1}))
    service = _launch(state, path, env, worker=f'from pathlib import Path\nPath({str(marker)!r}).touch()\n' + _PENDING,
                      service=True)
    try:
        deadline = time.monotonic() + 6
        while True:
            with sqlite3.connect(Path(env['AGENTFLOW_STATE_DIR']) / 'executor.sqlite3') as db:
                row = db.execute('SELECT hash,session,state FROM jobs WHERE id=?', (job['job_id'],)).fetchone()
            if row[2] == 'SUCCEEDED' or time.monotonic() >= deadline:
                break
            time.sleep(.05)
        assert row == (job['job_sha256'], original['actor']['session_id'], 'SUCCEEDED')
    finally:
        service.kill()
        service.communicate(timeout=5)
    outcome = _result(_launch(state, path, env, worker=f'from pathlib import Path\nPath({str(marker)!r}).touch()\n' + _PENDING))
    assert outcome == original and not marker.exists()
    assert (folder / 'body/stdout.txt').read_bytes() == body_stdout
    with sqlite3.connect(Path(env['AGENTFLOW_STATE_DIR']) / 'executor.sqlite3') as db:
        row = db.execute('SELECT hash,session,state FROM jobs WHERE id=?', (job['job_id'],)).fetchone()
    assert row == (job['job_sha256'], outcome['actor']['session_id'], 'SUCCEEDED')


@pytest.mark.parametrize('original_state', ['running', 'unknown'])
def test_executor_restart_reserves_original_job_before_admitting_another_task(
        budget_creation, monkeypatch, tmp_path, original_state):
    budget_creation[2]['task_id'] = 'z-task'
    state, _, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch, wall=40)
    config = Path(env['AGENTFLOW_CONFIG_DIR'])
    (config / 'platform.json').write_text(json.dumps({'max_parallel_jobs': 1}))
    entered, release, newcomer = tmp_path / 'original-entered', tmp_path / 'release-original', tmp_path / 'newcomer-entered'
    worker = _PENDING + f'''
import time
from pathlib import Path
actual_pending = reference_executor._execute
def blocked(envelope, home):
    if envelope['context']['task_id'] == 'z-task':
        Path({str(entered)!r}).touch()
        while not Path({str(release)!r}).exists():
            time.sleep(.02)
    else:
        Path({str(newcomer)!r}).touch()
    return actual_pending(envelope, home)
reference_executor._execute = blocked
'''
    owner = '' if original_state == 'running' else f'''
from pathlib import Path
from ergora.development.runtime.jobs import BudgetedJob
def lost(self, *args, **kwargs):
    Path({str(entered)!r}).touch()
    raise SystemExit('Controlled owner loss without a stopping witness')
BudgetedJob.supervise = lost
'''
    first = _launch(state, path, env, worker=worker, owner=owner, service=True)
    restarted = None
    try:
        deadline = time.monotonic() + 8
        while not entered.exists() and first.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        assert entered.exists()
        original_owner = json.loads((folder / 'owner.json').read_bytes())
        if original_state == 'unknown':
            deadline = time.monotonic() + 5
            while not list((Path(env['AGENTFLOW_STATE_DIR']) / 'rejected-envelopes').glob('*.json')) and time.monotonic() < deadline:
                time.sleep(.02)
        first.kill()
        first.communicate(timeout=5)
        assert (Path('/proc') / str(original_owner['pid'])).exists() is (original_state == 'running')
        original_attempt = (folder / 'attempt.json').read_bytes()
        budget_creation[2]['task_id'] = 'a-task'
        _, _, new_adapter, new_job, new_path, _, new_folder = _prepare(budget_creation, monkeypatch, wall=40)
        oneoff = _launch(state, new_path, env, worker=worker, service='request')
        stdout, stderr = oneoff.communicate(timeout=10)
        assert oneoff.returncode != 0 and 'capacity remains occupied' in stderr
        assert not newcomer.exists()
        restarted = _launch(state, new_path, env, worker=worker, service=True)
        # Cover more than one complete service admission tick. a-task sorts
        # before z-task; counting only new futures would launch it immediately.
        time.sleep(3)
        assert restarted.poll() is None and not newcomer.exists()
        assert (folder / 'attempt.json').read_bytes() == original_attempt
        assert not (new_folder / 'attempt.json').exists()
        if original_state == 'running':
            release.touch()
            deadline = time.monotonic() + 8
            while asyncio.run(new_adapter.poll(new_job)) is None and time.monotonic() < deadline:
                time.sleep(.05)
            assert newcomer.exists() and asyncio.run(new_adapter.poll(new_job))['state'] == 'SUCCEEDED'
            assert asyncio.run(adapter.poll(job))['state'] == 'SUCCEEDED'
    finally:
        release.touch()
        if original_state == 'running':
            deadline = time.monotonic() + 8
            while asyncio.run(adapter.poll(job)) is None and time.monotonic() < deadline:
                time.sleep(.05)
        for service in (first, restarted):
            if service is not None and service.poll() is None:
                service.kill()
                service.communicate(timeout=5)
