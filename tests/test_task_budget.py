"""Original preparation owns one authorization, complete bytes and stop evidence."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from ergora import projects, reference, task_envelopes, tasks
from ergora.reference_inputs import execution_input, request_roots
from ergora.state import State
from test_full_stage_materials import full_creation, full_graph
from test_work_agents import work_creation, work_graph
from test_registrations import installation, registration
from test_task_creation import creation_project, _files


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Budgeted native preparation requires Linux/WSL2')


@pytest.fixture
def budget_creation(full_creation):
    state, registered, definition = full_creation
    definition.update(schema_version=5, budget={'wall_seconds': 120, 'cleanup_seconds': 5, 'model_invocations': 258})
    return state, registered, definition


def _root(registered):
    return Path(registered['execution']['state_directory'])


def _prefix(registered, definition):
    return _root(registered) / 'ergora/task-creations' / definition['task_id']


def _worker_injection(monkeypatch, code, owner_code=''):
    """Inject slowness at the real application worker, below the process owner."""
    original = subprocess.Popen
    def launch(argv, **kwargs):
        if (argv[-1] == 'from ergora.reference_task_creation import main;main()'
                and '/operations/task-preparations/' in kwargs.get('env', {}).get('AGENTFLOW_STATE_DIR', '')):
            source = (
                'from ergora import processes\n'
                'original = processes.run\n'
                'def invoke(argv, *args, **kwargs):\n'
                '    argv = [*argv[:-1], ' + repr(code + '\n' +
                    'from ergora.reference_task_creation import preparation_worker;preparation_worker()') + ']\n'
                '    return original(argv, *args, **kwargs)\n'
                'processes.run = invoke\n'
                + owner_code + '\n'
                'from ergora.reference_task_creation import main;main()')
            argv = [*argv[:-1], source]
        return original(argv, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', launch)


def test_lost_preparation_reply_keeps_one_budget_and_preview_is_read_only(budget_creation, monkeypatch):
    state, registered, definition = budget_creation
    invoke = tasks.task_preparation
    result = {}
    def lost(*args, **kwargs):
        result.update(invoke(*args, **kwargs))
        raise OSError('Lost preparation reply')
    monkeypatch.setattr(tasks, 'task_preparation', lost)
    with pytest.raises(OSError, match='Lost preparation reply'):
        tasks.prepare(state, 'demo', definition, 1)
    monkeypatch.undo()
    assert result['status'] == 'prepared'
    prefix = _prefix(registered, definition)
    original = _files(prefix.parent)
    restored = tasks.prepare(State(state.root), 'demo', definition, 1)
    assert restored['budget'] == result['budget'] and restored['prepare_sha256'] == result['prepare_sha256']
    assert _files(prefix.parent) == original
    observations = _files(state.root / 'operations')
    preview = tasks.preview(state, 'demo', definition, 1)
    time.sleep(.05)
    assert tasks.preview(state, 'demo', definition, 1) == preview
    assert _files(state.root / 'operations') == observations
    assert _files(prefix.parent) == original and not (_root(registered) / 'tasks').exists()
    document = preview['files']['task.spec.json']
    selected = execution_input(document)
    assert selected.document == document and document['schema_version'] == 9
    assert document['budget']['instance'] == result['budget']
    assert len(document['budget']['slots']) == 2 + len(definition['input']['work_units']) + len(document['composition']['members'])
    assert Path('requests-composition-v9') in request_roots(Path('requests'))
    selected.require_submission()
    assert preview['prepare_sha256'] == restored['prepare_sha256']
    for prepare_sha, preview_sha in [('0' * 64, preview['preview_sha256']), (preview['prepare_sha256'], '0' * 64)]:
        with pytest.raises(ValueError, match='Preparation or preview changed'):
            tasks.create(state, 'demo', definition, 1, preview_sha, prepare_sha256=prepare_sha)
    shutil.rmtree(definition['composition']['manifest'])
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=preview['prepare_sha256'])
    assert created['status'] == 'published' and created['composition']['runtime_supported'] is True
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    assert not any((_root(registered) / name).exists() for name in ('ergora/task-submissions', 'requests-composition-v9', 'ingress'))
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=registered['execution']['config_directory'],
                       AGENTFLOW_STATE_DIR=registered['execution']['state_directory'],
                       PYTHONPATH=os.pathsep.join((str(Path(tasks.__file__).parent.parent),
                           str(reference.ROOT / 'platform/local'), str(reference.ROOT / 'platform/upstream/platform'))))
    # Constructing a budgeted Executor directly cannot bypass its job owner.
    direct = subprocess.run([sys.executable, '-c',
        'import json,sys;from pathlib import Path;from ergora.reference_executor import Executor;'
        'Executor({"context":{"spec":json.load(sys.stdin)}},Path(sys.argv[1]))', str(state.root)],
        input=json.dumps(document['legacy_spec']), env=environment, capture_output=True, text=True, timeout=20)
    assert direct.returncode != 0 and 'requires its original dedicated owner' in direct.stderr
    assert not (_root(registered) / 'workspaces').exists()


def test_concurrent_preparation_observes_original_authorization(budget_creation, monkeypatch, tmp_path):
    state, registered, definition = budget_creation
    marker = tmp_path / 'worker-entered'
    _worker_injection(monkeypatch, f"from pathlib import Path\nimport time\nPath({str(marker)!r}).write_text('entered')\ntime.sleep(.8)")
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(tasks.prepare, state, 'demo', definition, 1)
        deadline = time.monotonic() + 5
        while not marker.exists() and not first.done() and time.monotonic() < deadline:
            time.sleep(.02)
        assert marker.exists()
        second = pool.submit(tasks.prepare, State(state.root), 'demo', definition, 1).result()
        conflicting = deepcopy(definition)
        conflicting['input']['goal'] = 'A different concurrent authorization'
        with pytest.raises(ValueError, match='different preparation'):
            tasks.prepare(State(state.root), 'demo', conflicting, 1)
        completed = first.result()
    assert completed['status'] == 'prepared' and second['status'] in ('authorized', 'unknown', 'prepared')
    assert second['budget'] == completed['budget']
    files = _files(_prefix(registered, definition).parent)
    again = tasks.prepare(state, 'demo', definition, 1)
    assert again['budget'] == completed['budget'] and _files(_prefix(registered, definition).parent) == files


@pytest.mark.parametrize('boundary', ['installation', 'manifest', 'compiler'])
def test_actual_prepare_stops_slow_materials_and_detached_descendants(budget_creation, monkeypatch, tmp_path, boundary):
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=3, cleanup_seconds=1)
    marker = tmp_path / 'slow-worker.json'
    detached = 'import os,signal,time;os.setsid();signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'
    slow = f'''
import json,os,subprocess,sys,time
from pathlib import Path
from ergora import reference, workflow_definitions
from ergora.reference_task_creation import _Creation
def slow(*args, **kwargs):
    child = subprocess.Popen([sys.executable, '-c', {detached!r}])
    stat = Path('/proc/' + str(child.pid) + '/stat').read_text().rsplit(')', 1)[1].split()
    Path({str(marker)!r}).write_text(json.dumps({{'worker': os.getpid(), 'child': child.pid, 'start_ticks': stat[19]}}))
    time.sleep(60)
'''
    target = {'installation': 'reference.validate_installation', 'manifest': 'workflow_definitions.inspect_manifest',
              'compiler': '_Creation.compile'}[boundary]
    _worker_injection(monkeypatch, slow + '\n' + target + ' = slow')
    begin = time.monotonic()
    prepared = tasks.prepare(state, 'demo', definition, 1)
    elapsed = time.monotonic() - begin
    assert marker.exists() and prepared['status'] == 'exhausted', prepared
    assert elapsed < definition['budget']['wall_seconds'] + 1
    identities = json.loads(marker.read_bytes())
    assert not Path('/proc/' + str(identities['worker'])).exists()
    assert not Path('/proc/' + str(identities['child'])).exists()
    assert prepared['outcome']['cleanup_confirmed'] is True
    prefix = _prefix(registered, definition)
    assert not Path(str(prefix) + '.prepare-work/compile').exists()
    assert not Path(str(prefix) + '.prepared.json').exists() and not (_root(registered) / 'tasks').exists()
    original = _files(prefix.parent)
    assert tasks.prepare(state, 'demo', definition, 1)['budget'] == prepared['budget']
    assert _files(prefix.parent) == original
    with pytest.raises(ValueError, match='confirmed complete preparation'):
        tasks.preview(state, 'demo', definition, 1)


def test_expiration_and_revision_cannot_renew_or_publish_an_authorization(budget_creation):
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=3, cleanup_seconds=1)
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    remaining = tasks.preparation(state, 'demo', definition['task_id'])['budget_status']['work_remaining_seconds']
    time.sleep(remaining + .1)
    assert tasks.preview(state, 'demo', definition, 1) == preview
    with pytest.raises(ValueError, match='budget is exhausted'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=prepared['prepare_sha256'])
    assert not (_root(registered) / 'tasks').exists()

    changed = deepcopy(definition)
    changed['budget']['wall_seconds'] += 10
    with pytest.raises(ValueError, match='different preparation'):
        tasks.prepare(state, 'demo', changed, 1)
    projects.bind(state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'changed-model'}, 1)
    with pytest.raises(ValueError, match='revision changed after preparation'):
        tasks.preview(state, 'demo', definition, 2)
    assert tasks.preparation(state, 'demo', definition['task_id'])['budget'] == prepared['budget']


def test_attempt_storage_cannot_move_the_absolute_work_cutoff(budget_creation, monkeypatch, tmp_path):
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=6, cleanup_seconds=1)
    marker = tmp_path / 'slow-work-entered'
    worker = f'''
import time
from pathlib import Path
from ergora import reference
def slow(*args):
    Path({str(marker)!r}).write_text('work entered')
    time.sleep(60)
reference.validate_installation = slow
'''
    owner = '''
import time
from agent_platform import core
write = core.write
def delayed_attempt(path, value, **kwargs):
    result = write(path, value, **kwargs)
    if str(path).endswith('.prepare-attempt.json'):
        time.sleep(2)
    return result
core.write = delayed_attempt
'''
    _worker_injection(monkeypatch, worker, owner)
    result = tasks.prepare(state, 'demo', definition, 1)
    assert marker.exists() and result['status'] == 'exhausted'
    assert result['outcome']['elapsed_seconds'] < definition['budget']['wall_seconds'] + .5


def test_final_witness_storage_cannot_report_a_late_preparation_as_prepared(budget_creation, monkeypatch, tmp_path):
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=3, cleanup_seconds=1)
    marker = tmp_path / 'final-witness-fsync'
    owner = f'''
import os,time
from pathlib import Path
from agent_platform import core
write,fsync = core.write,os.fsync
writing_outcome = False
def track_outcome(path, value, **kwargs):
    global writing_outcome
    writing_outcome = isinstance(value, dict) and value.get('cleanup_confirmed') is True
    try:
        return write(path, value, **kwargs)
    finally:
        writing_outcome = False
def slow_fsync(fd):
    marker = Path({str(marker)!r})
    if writing_outcome and not marker.exists():
        marker.write_text('final outcome is still being persisted')
        time.sleep({definition['budget']['wall_seconds'] + 1})
    return fsync(fd)
core.write,os.fsync = track_outcome,slow_fsync
'''
    _worker_injection(monkeypatch, '', owner)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(tasks.prepare, state, 'demo', definition, 1)
        deadline = time.monotonic() + 10
        while not marker.exists() and not pending.done() and time.monotonic() < deadline:
            time.sleep(.02)
        assert marker.exists()
        assert tasks.preparation(State(state.root), 'demo', definition['task_id'])['status'] == 'unknown'
        result = pending.result(timeout=15)
    assert result['status'] == 'exhausted'
    assert result['outcome']['elapsed_seconds'] >= definition['budget']['wall_seconds']
    assert result['outcome']['overrun_seconds'] > 0
    prefix = _prefix(registered, definition)
    original = _files(prefix.parent)
    assert tasks.prepare(state, 'demo', definition, 1)['outcome'] == result['outcome']
    assert _files(prefix.parent) == original
    with pytest.raises(ValueError, match='confirmed complete preparation'):
        tasks.preview(state, 'demo', definition, 1)


def test_actual_publisher_keeps_revision_lock_after_observer_returns_unknown(budget_creation, monkeypatch, tmp_path):
    import fcntl

    state, registered, definition = budget_creation
    prepared = tasks.prepare(state, 'demo', definition, 1)
    preview = tasks.preview(state, 'demo', definition, 1)
    gate, entered = tmp_path / 'publication.lock', tmp_path / 'publisher-entered'
    owner = f'''
import fcntl
from pathlib import Path
from ergora.reference_task_creation import _Creation
publish = _Creation.publish
def held_publication(self, *args, **kwargs):
    Path({str(entered)!r}).write_text('actual publisher owns revision')
    with Path({str(gate)!r}).open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
    return publish(self, *args, **kwargs)
_Creation.publish = held_publication
'''
    _worker_injection(monkeypatch, '', owner)
    launch = subprocess.Popen
    def short_observation(argv, **kwargs):
        process = launch(argv, **kwargs)
        if '/operations/task-preparations/' in kwargs.get('env', {}).get('AGENTFLOW_STATE_DIR', ''):
            wait = process.wait
            process.wait = lambda timeout=None: wait(timeout=.2 if timeout == 30 else timeout)
        return process
    monkeypatch.setattr(subprocess, 'Popen', short_observation)
    with gate.open('wb') as lock, ThreadPoolExecutor(max_workers=1) as pool:
        fcntl.flock(lock, fcntl.LOCK_EX)
        observed = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                                prepare_sha256=prepared['prepare_sha256'])
        assert observed['status'] == 'unknown'
        try:
            deadline = time.monotonic() + 5
            while not entered.exists() and time.monotonic() < deadline:
                time.sleep(.02)
            assert entered.exists()
            binding = pool.submit(projects.bind, state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'later'}, 1)
            time.sleep(.3)
            assert not binding.done() and state.project('demo')['revision'] == 1
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
        assert binding.result(timeout=5)['revision'] == 2
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = tasks.creation(state, 'demo', definition['task_id'])
        if result['status'] == 'published':
            break
        time.sleep(.02)
    assert result['status'] == 'published' and result['created_revision'] == 1


def test_cap_and_unsupported_dimensions_fail_before_executable_publication(budget_creation):
    state, registered, definition = budget_creation
    definition['budget']['tokens'] = 100
    with pytest.raises(ValueError, match='Additional properties'):
        tasks.prepare(state, 'demo', definition, 1)
    assert not _root(registered).exists()
    del definition['budget']['tokens']
    definition['budget']['model_invocations'] = 1
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'failed' and prepared['outcome']['cleanup_confirmed']
    prefix = _prefix(registered, definition)
    stderr = Path(str(prefix) + '.prepare-work/process/stderr.txt').read_text()
    assert 'Known model call slots exceed' in stderr
    assert not (_root(registered) / 'tasks').exists()


def test_unconfirmed_cleanup_cannot_publish_prepared_materials(budget_creation, monkeypatch, tmp_path):
    import fcntl

    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=5, cleanup_seconds=1)
    gate, entered, native_pid = tmp_path / 'cleanup.lock', tmp_path / 'cleanup-entered', tmp_path / 'native-pid'
    detached = 'import os,signal,time;os.setsid();signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'
    worker = ("import subprocess,sys\nfrom pathlib import Path\n"
              f"child = subprocess.Popen([sys.executable, '-c', {detached!r}])\n"
              f"Path({str(native_pid)!r}).write_text(str(child.pid))\n")
    owner = f'''
import fcntl
from pathlib import Path
reap = processes._reap_children
def held_cleanup():
    Path({str(entered)!r}).write_text('cleanup not confirmed')
    with Path({str(gate)!r}).open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
    reap()
processes._reap_children = held_cleanup
'''
    _worker_injection(monkeypatch, worker, owner)
    with gate.open('wb') as lock, ThreadPoolExecutor(max_workers=1) as pool:
        fcntl.flock(lock, fcntl.LOCK_EX)
        future = pool.submit(tasks.prepare, state, 'demo', definition, 1)
        try:
            deadline = time.monotonic() + 8
            while not entered.exists() and not future.done() and time.monotonic() < deadline:
                time.sleep(.02)
            assert entered.exists()
            status = tasks.preparation(state, 'demo', definition['task_id'])
            assert status['status'] == 'unknown' and 'outcome' not in status
            pid = int(native_pid.read_text())
            assert Path('/proc/' + str(pid)).exists()
            prefix = _prefix(registered, definition)
            assert not Path(str(prefix) + '.prepared.json').exists()
            assert not Path(str(prefix) + '.prepare-result.json').exists()
            # Safety cleanup can finish later; that must not become in-budget success.
            time.sleep(status['budget_status']['work_remaining_seconds'] + definition['budget']['cleanup_seconds'] + .1)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
        result = future.result(timeout=5)
    assert result['status'] == 'exhausted' and result['outcome']['cleanup_confirmed']
    assert not Path('/proc/' + str(pid)).exists()
    assert tasks.prepare(state, 'demo', definition, 1)['budget'] == status['budget']


def test_cli_and_http_use_the_same_original_preparation(budget_creation, tmp_path):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    state, registered, definition = budget_creation
    source = tmp_path / 'task.json'
    source.write_text(json.dumps(definition))
    environment = dict(os.environ, PYTHONPATH=str(Path(tasks.__file__).parent.parent))
    command = [sys.executable, '-m', 'ergora', '--home', str(state.root), 'task']
    prepared = subprocess.run([*command, 'prepare', 'demo', '--definition', str(source), '--revision', '1'],
                              capture_output=True, text=True, env=environment, timeout=40)
    assert prepared.returncode == 0, prepared.stderr
    original = json.loads(prepared.stdout)
    with TestClient(create_app(state.root), base_url='http://127.0.0.1',
                    headers={'Origin': 'http://127.0.0.1', 'X-Ergora-Request': '1'}) as client:
        shown = client.get('/api/projects/demo/tasks/' + definition['task_id'] + '/preparation')
        assert shown.status_code == 200 and shown.json()['budget'] == original['budget']
        duplicate = client.post('/api/projects/demo/tasks/prepare', json={'definition': definition, 'revision': 1})
        assert duplicate.status_code == 200 and duplicate.json()['budget'] == original['budget']
        response = client.post('/api/projects/demo/tasks/preview', json={'definition': definition, 'revision': 1})
        assert response.status_code == 200, response.text
        preview = response.json()
        created = client.post('/api/projects/demo/tasks', json={'definition': definition, 'revision': 1,
            'prepare_sha256': original['prepare_sha256'], 'preview_sha256': preview['preview_sha256']})
        assert created.status_code == 200 and created.json()['status'] == 'published'
        document = preview['files']['task.spec.json']
        modified = deepcopy(document)
        modified['budget']['slots'].pop('inventory')
        modified['sha256'] = task_envelopes.identity({key: value for key, value in modified.items() if key != 'sha256'})
        with pytest.raises(ValueError, match='call slots differ'):
            execution_input(modified)
