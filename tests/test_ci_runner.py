"""Real local child-process proofs for the CI runner's parent observations."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest


NOTICE = '::notice title=CI phase observation::'
CHILD = '''
import json
from pathlib import Path
import sys
import time

directory = Path(sys.argv[1])

def emit(event, **fields):
    with (directory / 'phases.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'elapsed': 1.25, 'event': event, **fields}) + '\\n')

def wait(name):
    deadline = time.monotonic() + 10
    while not (directory / name).exists():
        if time.monotonic() >= deadline:
            raise RuntimeError('Fake child control was not released: ' + name)
        time.sleep(0.005)
'''


def wait_for(predicate):
    deadline = time.monotonic() + 5
    while not predicate():
        if time.monotonic() >= deadline:
            pytest.fail('Fake child or parent observation did not reach the controlled state')
        time.sleep(0.005)


def notice_row(notice):
    payload = notice.removeprefix(NOTICE).replace('%0D', '\r').replace('%0A', '\n').replace('%25', '%')
    return json.loads(payload)


@pytest.fixture
def ci_runner(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'scripts/ci/run.py'
    spec = importlib.util.spec_from_file_location('ci_runner_under_test', source)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    directory = tmp_path / 'result directory'
    children, monitors, workers, notices = [], [], [], []
    original_popen, original_monitor = subprocess.Popen, runner._monitor_phases
    original_writer = runner._stdout_writer

    def monitor(*args):
        monitors.append(threading.current_thread())
        original_monitor(*args, offsets=tuple(0.05 * index for index in range(1, 9)),
                         poll_interval=0.005)

    def start(script, *, fail_on_output=False):
        outcome = {}

        def popen(command, **options):
            outcome['command'], outcome['options'] = command, options
            child = original_popen([sys.executable, '-B', '-I', '-c', CHILD + script, str(directory)],
                                   **options)
            children.append(child)
            return child

        def writer():
            emit = original_writer()

            def output(message, *, annotation=False):
                if fail_on_output and message == 'trigger parent failure\n':
                    raise RuntimeError('controlled parent output failure')
                emit(message, annotation=annotation)
                if annotation and message.startswith(NOTICE):
                    notices.append(message)

            return output

        def run():
            try:
                outcome['returncode'] = runner.main()
            except BaseException as error:
                outcome['error'] = error

        monkeypatch.setattr(runner.subprocess, 'Popen', popen)
        monkeypatch.setattr(runner, '_monitor_phases', monitor)
        monkeypatch.setattr(runner, '_stdout_writer', writer)
        monkeypatch.setattr(sys, 'argv', [str(source), '--output', str(directory), '--group', '2'])
        worker = threading.Thread(target=run, name='test-ci-runner')
        workers.append(worker)
        worker.start()
        return outcome, worker

    yield runner, directory, start, children, monitors, notices

    if directory.exists():
        for name in ('release', 'advance', 'exit'):
            (directory / name).touch()
    cleanup = []
    for child in children:
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=5)
        cleanup.append({'pid': child.pid, 'returncode': child.returncode, 'argv': child.args})
    for worker in workers:
        worker.join(timeout=5)
        assert not worker.is_alive()
    assert all(not monitor.is_alive() for monitor in monitors)
    (tmp_path / 'cleanup.json').write_text(json.dumps({
        'children': cleanup,
        'monitor_threads': [{'name': monitor.name, 'alive': monitor.is_alive()} for monitor in monitors],
        'runner_threads': [{'name': worker.name, 'alive': worker.is_alive()} for worker in workers],
    }, indent=2) + '\n')
    (tmp_path / 'notices.jsonl').write_text(''.join(json.dumps(notice) + '\n' for notice in notices))


def test_silent_stdout_reports_actual_phase_updates_and_preserves_runner_outputs(ci_runner, capsys):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start('''
emit('phase-start', nodeid='tests/test_example.py::test_silent', when='call')
wait('advance')
emit('phase', nodeid='tests/test_example.py::test_silent', when='call', outcome='passed', seconds=0.75)
wait('release')
print('first output', flush=True)
print('stderr output', file=sys.stderr, flush=True)
emit('finish', exitstatus=7)
raise SystemExit(7)
''')
    wait_for(lambda: any(notice_row(row)['last_observed_complete_row'] is not None for row in notices))
    assert children[0].poll() is None and worker.is_alive()
    assert (directory / 'stdout.txt').read_text() == ''
    first = notice_row(notices[-1])
    assert first['last_observed_complete_row'] == {
        'event': 'phase-start', 'when': 'call', 'elapsed': 1.25,
        'nodeid': 'tests/test_example.py::test_silent',
    }
    assert first['parent_elapsed_seconds'] >= 0 and first['owned_child_returncode'] is None
    (directory / 'advance').touch()
    wait_for(lambda: any((notice_row(row)['last_observed_complete_row'] or {}).get('event') == 'phase'
                        for row in notices))
    completed = notice_row(notices[-1])['last_observed_complete_row']
    assert completed['outcome'] == 'passed' and completed['seconds'] == 0.75
    assert completed['elapsed'] == 1.25
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome
    assert outcome['returncode'] == children[0].returncode == 7
    assert all(not monitor.is_alive() for monitor in monitors)
    assert (directory / 'stdout.txt').read_text() == 'first output\nstderr output\n'
    console = capsys.readouterr().out
    assert 'first output\nstderr output\n' in console
    final = notice_row(notices[-1])
    assert final['observation'] == 'final' and final['owned_child_returncode'] == 7
    assert final['last_observed_complete_row'] == {'event': 'finish', 'elapsed': 1.25, 'exitstatus': 7}
    assert json.loads((directory / 'result.json').read_text())['returncode'] == 7
    request = json.loads((directory / 'request.json').read_text())
    assert request['argv'] == outcome['command'] and request['group'] == '2'
    assert request['argv'][1:6] == ['-u', '-m', 'pytest', '-p', 'pytest_phases']
    assert request['cwd'] == str(outcome['options']['cwd'])
    assert outcome['options']['stderr'] == subprocess.STDOUT
    assert outcome['options']['stdout'] == subprocess.PIPE
    assert outcome['options']['text'] is True and outcome['options']['encoding'] == 'utf-8'


@pytest.mark.parametrize('event,fields', [
    ('collection', {'nodeid': 'tests/test_import.py', 'outcome': 'failed', 'detail': 'import failed'}),
    ('finish', {'exitstatus': 2}),
])
def test_complete_collection_and_finish_rows_remain_observations(ci_runner, event, fields):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start(f"emit({event!r}, **{fields!r})\nwait('release')\n")
    wait_for(lambda: any((notice_row(row)['last_observed_complete_row'] or {}).get('event') == event
                        for row in notices))
    recorded = notice_row(notices[-1])['last_observed_complete_row']
    assert recorded == {'event': event, 'elapsed': 1.25,
                        **{key: value for key, value in fields.items() if key != 'detail'}}
    assert 'active' not in notices[-1]
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and outcome['returncode'] == 0


@pytest.mark.parametrize('tail', [
    '',
    '{"elapsed": 2, "event": "phase-start", "nodeid": "uncommitted-node"}',
    json.dumps({'elapsed': 2, 'event': 'phase-start', 'nodeid': 'oversize-' + 'x' * 70000}) + '\n',
])
def test_missing_partial_and_oversize_rows_do_not_fabricate_a_phase(ci_runner, tail):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start(f"(directory / 'phases.jsonl').write_text({tail!r})\nwait('release')\n")
    wait_for(lambda: bool(notices))
    assert notice_row(notices[-1])['last_observed_complete_row'] is None
    assert 'uncommitted-node' not in notices[-1] and 'oversize-' not in notices[-1]
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and outcome['returncode'] == 0
    assert notice_row(notices[-1])['last_observed_complete_row'] is None


def test_partial_tail_keeps_only_the_last_complete_row(ci_runner):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start('''
emit('phase', nodeid='completed-node', when='teardown', outcome='passed', seconds=0.125)
with (directory / 'phases.jsonl').open('a') as stream:
    stream.write('{"elapsed": 3, "event": "phase-start", "nodeid": "partial-node"}')
wait('release')
''')
    wait_for(lambda: any(notice_row(row)['last_observed_complete_row'] is not None for row in notices))
    assert notice_row(notices[-1])['last_observed_complete_row']['nodeid'] == 'completed-node'
    assert 'partial-node' not in notices[-1]
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and outcome['returncode'] == 0


def test_notice_escaping_payload_and_count_are_bounded(ci_runner):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start('''
emit('phase', nodeid='percent%\\r\\n::error title=injected::no' + 'x' * 10000,
     when='call', outcome='passed', seconds=0.5)
wait('release')
''')
    wait_for(lambda: len(notices) == 8)
    time.sleep(0.05)
    assert len(notices) == 8 and children[0].poll() is None
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and outcome['returncode'] == 0
    assert len(notices) == 9
    for notice in notices:
        assert len(notice.removeprefix(NOTICE)) <= 3000
        assert '\r' not in notice and '\n' not in notice
    assert 'percent%25\\r\\n::error' in notices[-1]
    assert '"event": "phase"' in notices[-1] and '"outcome": "passed"' in notices[-1]
    assert '"elapsed": 1.25' in notices[-1] and '"seconds": 0.5' in notices[-1]


def test_owned_child_exit_is_observed_while_a_descendant_holds_stdout(ci_runner):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start("""
import subprocess
descendant = '''
import json
import os
from pathlib import Path
import sys
import time
directory = Path(sys.argv[1])
deadline = time.monotonic() + 10
while not (directory / 'release').exists() and time.monotonic() < deadline:
    time.sleep(0.005)
(directory / 'descendant-exit.json').write_text(json.dumps({'pid': os.getpid(), 'before_exit': 0}))
'''
child = subprocess.Popen([sys.executable, '-B', '-I', '-c', descendant, str(directory)])
(directory / 'descendant-pid.json').write_text(json.dumps({'pid': child.pid, 'argv': child.args}))
emit('finish', exitstatus=0)
""")
    wait_for(lambda: bool(notices) and notice_row(notices[-1])['observation'] == 'final')
    assert notice_row(notices[-1])['owned_child_returncode'] == 0
    assert worker.is_alive() and children[0].poll() == 0
    wait_for(lambda: bool(monitors) and not monitors[0].is_alive())
    assert not (directory / 'result.json').exists()
    descendant = json.loads((directory / 'descendant-pid.json').read_text())
    observation = {'pid': descendant['pid'], 'stdout_closed_after_release': False}
    stat = Path('/proc') / str(descendant['pid']) / 'stat'
    if sys.platform == 'linux':
        fields = stat.read_text().rpartition(')')[2].split()
        observation['start_ticks'] = fields[19]
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and outcome['returncode'] == 0
    observation['stdout_closed_after_release'] = True
    observation['exit_receipt'] = json.loads((directory / 'descendant-exit.json').read_text())
    assert observation['exit_receipt']['pid'] == descendant['pid']
    if sys.platform == 'linux':
        def exited():
            try:
                fields = stat.read_text().rpartition(')')[2].split()
            except FileNotFoundError:
                observation['state'] = 'absent'
                return True
            observation['state'], observation['wait_status'] = fields[0], int(fields[49])
            assert fields[19] == observation['start_ticks']
            return fields[0] == 'Z'

        wait_for(exited)
        if observation['state'] == 'Z':
            assert observation['wait_status'] == 0
    (directory / 'descendant-observation.json').write_text(json.dumps(observation, indent=2) + '\n')


def test_parent_exception_stops_monitor_before_the_original_child_wait(ci_runner):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start("print('trigger parent failure', flush=True)\nwait('release')\n",
                            fail_on_output=True)
    wait_for(lambda: bool(notices) and notice_row(notices[-1])['observation'] == 'final')
    wait_for(lambda: bool(monitors) and not monitors[0].is_alive())
    assert children[0].poll() is None and worker.is_alive()
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and isinstance(outcome['error'], RuntimeError)
    assert str(outcome['error']) == 'controlled parent output failure'
    assert children[0].returncode == 0
    assert not (directory / 'result.json').exists()


@pytest.fixture
def raw_ci_runner(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'scripts/ci/run.py'
    spec = importlib.util.spec_from_file_location('raw_ci_runner_under_test', source)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    directory = tmp_path / 'raw result'
    fragments, children, monitors, workers = [], [], [], []
    notice_held, release_notice, contender, partial_seen = (threading.Event() for _ in range(4))
    original_popen, original_monitor = subprocess.Popen, runner._monitor_phases
    original_lock = threading.Lock

    class OutputLock:
        def __init__(self):
            self.lock = original_lock()

        def __enter__(self):
            if self.lock.locked():
                contender.set()
            self.lock.acquire()

        def __exit__(self, *error):
            self.lock.release()

    class RawStream:
        block_notice = False

        def write(self, text):
            if self.block_notice and NOTICE in text:
                self.block_notice = False
                head, separator, rest = text.partition('\n')
                fragments.append(head)
                notice_held.set()
                if not release_notice.wait(5):
                    raise RuntimeError('Controlled notice write was not released')
                fragments.append(separator + rest)
            else:
                fragments.append(text)
                if text == 'FAILED raced\n':
                    contender.set()
                if text == 'eof partial':
                    partial_seen.set()
            return len(text)

        def flush(self):
            pass

    stream = RawStream()

    def monitor(*args):
        monitors.append(threading.current_thread())
        original_monitor(*args, offsets=tuple(0.05 * index for index in range(1, 9)),
                         poll_interval=0.005)

    def start(script, *, block_notice=False):
        outcome = {}
        stream.block_notice = block_notice

        def popen(command, **options):
            child = original_popen([sys.executable, '-B', '-I', '-c', CHILD + script, str(directory)],
                                   **options)
            children.append(child)
            return child

        def run():
            try:
                outcome['returncode'] = runner.main()
            except BaseException as error:
                outcome['error'] = error

        monkeypatch.setattr(runner.subprocess, 'Popen', popen)
        monkeypatch.setattr(runner, '_monitor_phases', monitor)
        monkeypatch.setattr(runner, 'threading', SimpleNamespace(
            Lock=OutputLock, Event=threading.Event, Thread=threading.Thread))
        monkeypatch.setattr(sys, 'stdout', stream)
        monkeypatch.setattr(sys, 'argv', [str(source), '--output', str(directory)])
        worker = threading.Thread(target=run, name='test-ci-raw-runner')
        workers.append(worker)
        worker.start()
        return outcome, worker

    yield directory, start, fragments, notice_held, release_notice, contender, partial_seen

    release_notice.set()
    if directory.exists():
        for name in ('write', 'release'):
            (directory / name).touch()
    for child in children:
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=5)
    for worker in workers:
        worker.join(timeout=5)
        assert not worker.is_alive()
    assert all(not monitor.is_alive() for monitor in monitors)
    (tmp_path / 'raw-stdout.txt').write_bytes(''.join(fragments).encode('utf-8'))
    (tmp_path / 'raw-write-fragments.json').write_text(json.dumps(fragments, indent=2) + '\n')
    (tmp_path / 'cleanup.json').write_text(json.dumps({
        'children': [{'pid': child.pid, 'returncode': child.returncode, 'argv': child.args}
                     for child in children],
        'monitor_threads': [{'name': monitor.name, 'alive': monitor.is_alive()} for monitor in monitors],
        'runner_threads': [{'name': worker.name, 'alive': worker.is_alive()} for worker in workers],
    }, indent=2) + '\n')


def assert_complete_commands(raw, expected_errors):
    commands = [line for line in raw.splitlines() if line.startswith('::')]
    notices = [line for line in commands if line.startswith(NOTICE)]
    assert len(notices) == raw.count(NOTICE)
    assert 1 <= len(notices) <= 9
    for line in notices:
        row = json.loads(line.removeprefix(NOTICE))
        assert line == NOTICE + json.dumps(row, ensure_ascii=True)
    assert [line for line in commands if not line.startswith(NOTICE)] == expected_errors


def test_raw_notice_and_failed_tee_writes_remain_complete_commands(raw_ci_runner):
    directory, start, fragments, notice_held, release_notice, contender, partial_seen = raw_ci_runner
    outcome, worker = start('''
emit('phase-start', nodeid='raw-node', when='call')
wait('write')
print('FAILED raced', flush=True)
wait('release')
raise SystemExit(7)
''', block_notice=True)
    assert notice_held.wait(5)
    (directory / 'write').touch()
    wait_for(lambda: (directory / 'stdout.txt').read_text() == 'FAILED raced\n')
    assert contender.wait(5)
    release_notice.set()
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome and outcome['returncode'] == 7
    assert (directory / 'stdout.txt').read_bytes() == b'FAILED raced\n'
    assert_complete_commands(''.join(fragments), [
        '::error title=Failed test::FAILED raced',
        '::error title=Native regression::FAILED raced%0A',
    ])


def test_raw_annotation_after_partial_child_eof_starts_a_new_line(raw_ci_runner):
    directory, start, fragments, notice_held, release_notice, contender, partial_seen = raw_ci_runner
    outcome, worker = start('''
import os
emit('phase-start', nodeid='partial-node', when='call')
sys.stdout.write('eof partial')
sys.stdout.flush()
os.close(sys.stdout.fileno())
os.close(sys.stderr.fileno())
sys.stdout = sys.stderr = None
wait('release')
raise SystemExit(7)
''')
    assert partial_seen.wait(5)
    observed = ''.join(fragments).count(NOTICE)
    wait_for(lambda: ''.join(fragments).count(NOTICE) > observed and ''.join(fragments).endswith('\n'))
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome and outcome['returncode'] == 7
    assert (directory / 'stdout.txt').read_bytes() == b'eof partial'
    assert 'eof partial\n::' in ''.join(fragments)
    assert_complete_commands(''.join(fragments), [
        '::error title=Native regression::eof partial',
    ])
