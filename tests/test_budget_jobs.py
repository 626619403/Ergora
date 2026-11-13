"""Real job owners and process trees; controlled bodies never call a model."""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from ergora import reference, task_envelopes, tasks
from ergora.reference_inputs import execution_input
from test_task_budget import budget_creation, full_creation, full_graph, work_creation, work_graph
from test_registrations import installation, registration
from test_task_creation import creation_project


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Budgeted job owners require Linux/WSL2')


def _prepare(budget_creation, monkeypatch, *, wall=8, reserve=2, omit_admission=False):
    pytest.importorskip('temporalio')
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
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
    context = task_envelopes.issue_inventory_context(document, document['legacy_spec']['request']['repository']['starting_sha'])
    job = asyncio.run(adapter.submit(context))
    path = adapter.roots['requests'] / definition['task_id'] / (job['job_id'] + '.json')
    if omit_admission:
        envelope = json.loads(path.read_bytes())
        del envelope['context']['admission']
        envelope['job_sha256'] = task_envelopes.identity(envelope['context'])
        path.write_text(json.dumps(envelope))
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=str(config), AGENTFLOW_STATE_DIR=str(runtime),
        PYTHONPATH=os.pathsep.join(map(str, (Path(tasks.__file__).parent.parent,
            Path(registered['execution']['installation']) / 'local',
            Path(registered['execution']['installation']) / 'upstream/platform'))))
    folder = runtime / 'workspaces' / definition['task_id'] / 'jobs' / job['job_id'] / 'budget'
    return state, document, adapter, job, path, environment, folder


def _launch(state, path, environment, *, worker='', owner='', service=False):
    # Only fault injection varies. Public process() selects its owner from the
    # trusted published input; the owner and supervisor are the product code.
    body_prefix = worker
    owner_source = '''
from ergora import processes
original_run = processes.run
def instrument(argv, *args, **kwargs):
    if argv[-1] == 'from ergora.reference_executor import pending_job;pending_job()':
        argv = [*argv[:-1], PREFIX + '\\n' + argv[-1]]
    return original_run(argv, *args, **kwargs)
processes.run = instrument
''' .replace('PREFIX', repr(body_prefix)) + owner + '\nfrom ergora.reference_job_lifecycle import main;main()'
    source = '''
import json,subprocess,sys
from pathlib import Path
original_launch = subprocess.Popen
def launch(argv, **kwargs):
    if argv[-1] == 'from ergora.reference_job_lifecycle import main;main()':
        argv = [*argv[:-1], OWNER]
    return original_launch(argv, **kwargs)
subprocess.Popen = launch
from ergora.reference_executor import process
print(json.dumps(process(Path(sys.argv[1]), Path(sys.argv[2]))))
''' .replace('OWNER', repr(owner_source))
    if service:
        source = source.replace(
            'from ergora.reference_executor import process\nprint(json.dumps(process(Path(sys.argv[1]), Path(sys.argv[2]))))',
            'from ergora.reference_executor import main\nmain(Path(sys.argv[2])'
            + (', request=Path(sys.argv[1]))' if service == 'request' else ')'))
    return subprocess.Popen([sys.executable, '-P', '-c', source, str(path), str(state.root)],
        env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _result(process):
    stdout, stderr = process.communicate(timeout=20)
    assert process.returncode == 0, stdout + stderr
    return json.loads(stdout)


_PENDING = '''
from ergora import reference_executor
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


def test_constructor_lock_consumes_original_budget_and_cannot_reexecute(budget_creation, monkeypatch, tmp_path):
    import fcntl

    state, document, adapter, job, path, env, folder = _prepare(budget_creation, monkeypatch)
    lock_path = tmp_path / 'construction.lock'
    entered = tmp_path / 'construction-entered'
    worker = f'''
import fcntl
from pathlib import Path
from ergora.reference_executor import Executor
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
from ergora.reference_executor import Executor
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
    if argv[-1] == 'from ergora.reference_job_lifecycle import collect;collect()':
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
from ergora.reference_job_lifecycle import BudgetedJob
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
from ergora.reference_job_lifecycle import BudgetedJob
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
from ergora.reference_job_lifecycle import BudgetedJob
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
