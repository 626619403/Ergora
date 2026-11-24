"""Real local child-process proofs for the CI runner's parent observations."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest


NOTICE = '::notice title=CI phase observation::'
DIAGNOSTIC = '::error title=Python diagnostic excerpt::'
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


def child_command(script, directory):
    path = directory.parent / 'controlled child.py'
    path.write_text(CHILD + script, encoding='utf-8')
    return [sys.executable, '-B', '-I', str(path), str(directory)]


def wait_for(predicate, outcome=None):
    deadline = time.monotonic() + 5
    while True:
        if outcome is not None and 'error' in outcome:
            raise outcome['error']
        if predicate():
            return
        if time.monotonic() >= deadline:
            pytest.fail('Fake child or parent observation did not reach the controlled state')
        time.sleep(0.005)


def notice_row(notice):
    payload = notice.removeprefix(NOTICE).replace('%0D', '\r').replace('%0A', '\n').replace('%25', '%')
    return json.loads(payload)


def event_utc(filetime):
    from datetime import datetime, timezone
    seconds, fraction = divmod(filetime - 116444736000000000, 10000000)
    return datetime.fromtimestamp(seconds, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + f'.{fraction:07d}Z'


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

    def start(script, *, fail_on_output=False, windows_returncode=None, pipe_stdin=False):
        outcome = {}

        def popen(command, **options):
            if command[1:6] != ['-u', '-m', 'pytest', '-p', 'pytest_phases']:
                return original_popen(command, **options)
            outcome['command'] = command
            outcome['options'] = {key: value for key, value in options.items() if key != 'env'}
            if pipe_stdin:
                options['stdin'] = subprocess.PIPE
            child = original_popen(child_command(script, directory), **options)
            children.append(child)
            if windows_returncode is not None:
                class WindowsOutcome:
                    pid, stdout = child.pid, child.stdout

                    def poll(self):
                        return windows_returncode if child.poll() is not None else None

                    def wait(self):
                        outcome['actual_child_returncode'] = child.wait()
                        return windows_returncode

                    def __enter__(self):
                        child.__enter__()
                        return self

                    def __exit__(self, *error):
                        child.__exit__(*error)

                return WindowsOutcome()
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
        if windows_returncode is not None:
            monkeypatch.setattr(runner, 'sys', SimpleNamespace(
                executable=r'C:\Owned Python\python.exe', platform='win32', stdout=sys.stdout))
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


@pytest.fixture
def windows_events(ci_runner, monkeypatch):
    from ergora.runtime import processes

    runner, directory, start, children, monitors, notices = ci_runner
    calls, raw = [], {}
    scenario = {'change': None, 'owner_status': 'succeeded', 'returncode': 0}
    ordinary_owner = processes.run

    def query(argv, cwd, output, timeout, **options):
        assert children[0].poll() == 7
        assert json.loads((directory / 'result.json').read_text())['returncode'] == 0xC0000005
        request = json.loads((directory / 'windows-crash-events-request.json').read_text())
        bound = request['binding']
        if scenario.get('real_query'):
            calls.append({'argv': argv, 'timeout': timeout, 'options': options, 'request': request})
            return ordinary_owner(argv, cwd, output, timeout, **options)
        event = {
            'provider': 'Application Error', 'event_id': 1000,
            'event_time': event_utc(bound['reaped_filetime']),
            'ProcessId': hex(children[0].pid),
            'ProcessCreationTime': hex((bound['launch_start_filetime'] + bound['launch_end_filetime']) // 2),
            'AppPath': r'C:\Owned Python\python.exe', 'AppName': 'python.exe', 'AppVersion': '3.12.10.0',
            'ModuleName': 'python312.dll', 'ModuleVersion': '3.12.10.0',
            'ExceptionCode': 'c0000005', 'FaultingOffset': '000000000012abcd',
        }
        payload = {'status': 'ok', 'records': [event]}
        if scenario['change'] is not None:
            scenario['change'](payload, bound)
        output.mkdir()
        raw['stdout'] = scenario.get('raw_stdout', json.dumps(payload).encode() + b'\r\n')
        raw['stderr'] = b'query diagnostic stderr\r\n'
        (output / 'stdout.txt').write_bytes(raw['stdout'])
        (output / 'stderr.txt').write_bytes(raw['stderr'])
        if options.get('command_record') is not None:
            Path(options['command_record']).write_text(json.dumps(argv))
        calls.append({'argv': argv, 'timeout': timeout, 'options': options, 'request': request})
        if scenario.get('owner_error'):
            if scenario.get('owner_interrupt'):
                raise KeyboardInterrupt('controlled query cleanup interruption')
            raise RuntimeError('controlled cleanup uncertainty ' + '\u2603' * 800)
        return {'status': scenario['owner_status'], 'returncode': scenario['returncode'], 'output': str(output)}

    monkeypatch.setattr(processes, 'run', query)
    monkeypatch.setattr(runner, 'shutil', SimpleNamespace(which=lambda name: r'C:\Windows\powershell.exe'), raising=False)

    def run(*, identity=True, code=0xC0000005):
        script = '''
import os
emit('identity', pid=os.getpid(), python=sys.version, executable=r'C:\\Owned Python\\python.exe')
print('complete original stdout', flush=True)
print('complete original stderr', file=sys.stderr, flush=True)
raise SystemExit(7)
'''
        if not identity:
            script = script.replace("emit('identity', pid=os.getpid(), python=sys.version, executable=r'C:\\Owned Python\\python.exe')", '')
        elif isinstance(identity, str):
            changes = {
                'pid': ('pid=os.getpid()', 'pid=os.getpid()+1'),
                'path': (r"executable=r'C:\Owned Python\python.exe'", r"executable=r'C:\Other Python\python.exe'"),
                'python': ('python=sys.version', "python=''"),
                'first-row': ("emit('identity'", "emit('phase'"),
                'oversize': ('python=sys.version', "python='x'*9000"),
                'partial': ("emit('identity', pid=os.getpid(), python=sys.version, executable=r'C:\\Owned Python\\python.exe')",
                            "(directory / 'phases.jsonl').write_text('{\"event\":\"identity\"')"),
            }
            before, after = changes[identity]
            assert before in script
            script = script.replace(before, after)
        outcome, worker = start(script, windows_returncode=code)
        worker.join(timeout=20)
        assert not worker.is_alive() and 'error' not in outcome
        assert outcome['returncode'] == code and children[0].returncode == 7
        assert (directory / 'stdout.txt').read_text() == 'complete original stdout\ncomplete original stderr\n'
        return outcome

    return runner, directory, run, calls, scenario, raw


def test_owned_windows_event_is_bound_after_reap_without_changing_original_failure(windows_events, capsys):
    runner, directory, run, calls, scenario, raw = windows_events
    run()
    assert (directory / 'windows-crash-events.json').is_file(), 'Owned crash evidence is missing after the original native outcome'
    result = json.loads((directory / 'windows-crash-events.json').read_text())
    assert result['status'] == 'matched' and result['cleanup_confirmed'] is True
    assert len(result['records']) == 1 and result['records'][0]['ModuleName'] == 'python312.dll'
    assert result['binding']['python'].startswith(sys.version.split()[0])
    assert result['binding']['executable'] == r'C:\Owned Python\python.exe'
    assert len(calls) == 1 and calls[0]['timeout'] == 5
    assert calls[0]['request']['argv'] == calls[0]['argv']
    assert calls[0]['options']['deadline'] is not None
    assert (directory / 'windows-crash-query/stdout.txt').read_bytes() == raw['stdout']
    assert (directory / 'windows-crash-query/stderr.txt').read_bytes() == raw['stderr']
    assert json.loads((directory / 'result.json').read_text())['returncode'] == 0xC0000005
    console = capsys.readouterr().out
    assert '::error title=Native regression::' in console
    notices = [line for line in console.splitlines() if line.startswith('::notice title=Windows crash event observation::')]
    assert len(notices) == 1 and len(notices[0].split('::', 2)[-1]) <= 3000


@pytest.mark.parametrize('field,change', [
    ('ProcessId', lambda value, bound: hex(bound['pid'] + 1)),
    ('ProcessCreationTime', lambda value, bound: str(bound['launch_start_filetime'] - 1)),
    ('ProcessCreationTime', lambda value, bound: str(bound['launch_end_filetime'] + 1)),
    ('event_time', lambda value, bound: event_utc(bound['launch_start_filetime'] - 1)),
    ('event_time', lambda value, bound: event_utc(bound['reaped_filetime'] + 1)),
    ('AppPath', lambda value, bound: r'C:\Other Python\python.exe'),
    ('AppName', lambda value, bound: 'other.exe'),
    ('ExceptionCode', lambda value, bound: 'c0000006'),
    ('provider', lambda value, bound: 'Other Provider'),
    ('event_id', lambda value, bound: 1001),
    ('FaultingOffset', lambda value, bound: 'malformed-offset'),
    ('ProcessCreationTime', lambda value, bound: None),
    ('ModuleName', lambda value, bound: ''),
    ('ModuleName', lambda value, bound: ' \t\r\n'),
])
def test_unmatched_or_malformed_event_cannot_be_promoted(windows_events, capsys, field, change):
    runner, directory, run, calls, scenario, raw = windows_events
    scenario['change'] = lambda payload, bound: payload['records'][0].update({field: change(None, bound)})
    run()
    result = json.loads((directory / 'windows-crash-events.json').read_text())
    assert result['status'] == 'unknown' and result['records'] == []
    assert result['cleanup_confirmed'] is True and len(calls) == 1
    notices = [line.split('::', 2)[-1] for line in capsys.readouterr().out.splitlines()
               if line.startswith('::notice title=Windows crash event observation::')]
    assert len(notices) == 1 and json.loads(notices[0])['status'] == 'unknown'


@pytest.mark.parametrize('identity', [False, 'pid', 'path', 'python', 'first-row', 'oversize', 'partial'])
def test_unbound_child_identity_does_not_launch_a_machine_event_query(windows_events, identity):
    runner, directory, run, calls, scenario, raw = windows_events
    run(identity=identity)
    result = json.loads((directory / 'windows-crash-events.json').read_text())
    assert result['status'] == 'unknown' and result['records'] == []
    assert result['owner_invoked'] is False and result['cleanup_confirmed'] is None
    assert calls == [] and not (directory / 'windows-crash-query').exists()


def test_unavailable_powershell_is_unknown_without_a_query(windows_events, monkeypatch):
    runner, directory, run, calls, scenario, raw = windows_events
    monkeypatch.setattr(runner.shutil, 'which', lambda name: None)
    run()
    result = json.loads((directory / 'windows-crash-events.json').read_text())
    assert result['status'] == 'unknown' and result['reason'] == 'powershell-unavailable'
    assert result['owner_invoked'] is False and calls == []


@pytest.mark.parametrize('code', [0, 7])
def test_non_native_windows_outcomes_do_not_query_events(windows_events, code):
    runner, directory, run, calls, scenario, raw = windows_events
    run(code=code)
    assert calls == [] and not (directory / 'windows-crash-events.json').exists()
    assert json.loads((directory / 'result.json').read_text())['returncode'] == code


@pytest.mark.parametrize('count', [0, 5, 6])
def test_matching_record_count_is_bounded_and_empty_does_not_mean_no_fault(windows_events, count):
    runner, directory, run, calls, scenario, raw = windows_events
    scenario['change'] = lambda payload, bound: payload.update(records=payload['records'] * count)
    run()
    result = json.loads((directory / 'windows-crash-events.json').read_text())
    assert result['status'] == ('matched' if count == 5 else 'unknown')
    assert len(result['records']) == (5 if count == 5 else 0)


@pytest.mark.parametrize('payload', [b'{broken-json', b'x' * 131073], ids=['malformed', 'oversize'])
def test_bad_or_oversize_query_output_keeps_original_bytes_and_unknown(windows_events, payload):
    runner, directory, run, calls, scenario, raw = windows_events
    scenario['raw_stdout'] = payload
    run()
    result = json.loads((directory / 'windows-crash-events.json').read_text())
    assert result['status'] == 'unknown' and result['records'] == []
    assert (directory / 'windows-crash-query/stdout.txt').read_bytes() == payload
    assert result['stdout']['bytes'] == len(payload)
    assert result['stdout']['complete_read'] == (len(payload) <= 131072)


@pytest.mark.parametrize('owner_status', ['failed', 'timed_out', 'cleanup-error', 'interrupted'])
def test_query_failure_or_unconfirmed_cleanup_never_replaces_native_outcome(windows_events, capsys, owner_status):
    runner, directory, run, calls, scenario, raw = windows_events
    scenario.update(owner_status=owner_status, returncode=1,
                    owner_error=owner_status in ('cleanup-error', 'interrupted'),
                    owner_interrupt=owner_status == 'interrupted')
    run()
    result = json.loads((directory / 'windows-crash-events.json').read_text())
    assert result['status'] == 'unknown' and result['records'] == []
    assert result['cleanup_confirmed'] == (owner_status not in ('cleanup-error', 'interrupted'))
    assert (directory / 'windows-crash-query/stdout.txt').read_bytes() == raw['stdout']
    assert (directory / 'windows-crash-query/stderr.txt').read_bytes() == raw['stderr']
    assert result['stdout']['bytes'] == len(raw['stdout'])
    notices = [line for line in capsys.readouterr().out.splitlines()
               if line.startswith('::notice title=Windows crash event observation::')]
    assert len(notices) == 1 and len(notices[0].split('::', 2)[-1]) <= 3000


def test_phase_identity_records_the_actual_producer_pid(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'scripts/ci/pytest_phases.py'
    spec = importlib.util.spec_from_file_location('owned_identity_under_test', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    log = module.PhaseLog(tmp_path / 'phases', None, source.with_name('linux-groups.json'))
    log.stream.close()
    row = json.loads((tmp_path / 'phases/phases.jsonl').read_text())
    assert row['pid'] == os.getpid() and row['python'] == sys.version and row['executable'] == sys.executable


@pytest.mark.skipif(sys.platform != 'linux', reason='Controlled substitute query process and POSIX group cleanup')
def test_query_timeout_uses_existing_owner_and_stops_descendants(windows_events, tmp_path, monkeypatch):
    runner, directory, run, calls, scenario, raw = windows_events
    owned = tmp_path / 'query-pids.json'
    descendant = tmp_path / 'query-descendant.json'
    tool = tmp_path / 'controlled-powershell'
    code = f'''#!{sys.executable}
import json,os,subprocess,sys,time
from pathlib import Path
Path({str(owned)!r}).write_text(json.dumps({{'pid':os.getpid()}}))
child = subprocess.Popen([sys.executable, '-B', '-I', '-c', 'import json,os,time;from pathlib import Path;Path(' + repr({str(descendant)!r}) + ').write_text(json.dumps({{"pid":os.getpid()}}));time.sleep(30)'])
while not Path({str(descendant)!r}).exists():time.sleep(.005)
sys.stdout.buffer.write(b'partial query stdout\\r\\n');sys.stdout.flush()
sys.stderr.buffer.write(b'partial query stderr\\r\\n');sys.stderr.flush()
time.sleep(30)
'''
    tool.write_text(code)
    tool.chmod(0o700)
    monkeypatch.setattr(runner.shutil, 'which', lambda name: str(tool))
    scenario['real_query'] = True
    started = time.monotonic()
    run()
    assert time.monotonic() - started < 15
    result = json.loads((directory / 'windows-crash-events.json').read_text())
    assert result['status'] == 'unknown' and result['reason'] == 'query-timed_out'
    assert result['cleanup_confirmed'] is True and result['owner_result']['returncode'] is not None
    assert (directory / 'windows-crash-query/stdout.txt').read_bytes() == b'partial query stdout\r\n'
    assert (directory / 'windows-crash-query/stderr.txt').read_bytes() == b'partial query stderr\r\n'
    for path in (owned, descendant):
        pid = json.loads(path.read_text())['pid']
        stat = Path('/proc') / str(pid) / 'stat'
        if stat.exists():
            assert stat.read_text().rpartition(')')[2].split()[0] == 'Z'


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
    wait_for(lambda: any(notice_row(row)['last_observed_complete_row'] is not None for row in notices), outcome)
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
                        for row in notices), outcome)
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
                        for row in notices), outcome)
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
    wait_for(lambda: bool(notices), outcome)
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
    wait_for(lambda: any(notice_row(row)['last_observed_complete_row'] is not None for row in notices), outcome)
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
    wait_for(lambda: len(notices) == 8, outcome)
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
    wait_for(lambda: bool(notices) and notice_row(notices[-1])['observation'] == 'final', outcome)
    assert notice_row(notices[-1])['owned_child_returncode'] == 0
    assert worker.is_alive() and children[0].poll() == 0
    wait_for(lambda: bool(monitors) and not monitors[0].is_alive(), outcome)
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

        wait_for(exited, outcome)
        if observation['state'] == 'Z':
            assert observation['wait_status'] == 0
    (directory / 'descendant-observation.json').write_text(json.dumps(observation, indent=2) + '\n')


def test_parent_exception_stops_monitor_before_the_original_child_wait(ci_runner):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start("print('trigger parent failure', flush=True)\nwait('release')\n",
                            fail_on_output=True)
    wait_for(lambda: bool(notices) and notice_row(notices[-1])['observation'] == 'final', outcome)
    wait_for(lambda: bool(monitors) and not monitors[0].is_alive(), outcome)
    assert children[0].poll() is None and worker.is_alive()
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and isinstance(outcome['error'], RuntimeError)
    assert str(outcome['error']) == 'controlled parent output failure'
    assert children[0].returncode == 0
    assert not (directory / 'result.json').exists()


@pytest.mark.parametrize('header', [
    'Windows fatal exception: access violation',
    'Fatal Python error: Segmentation fault',
    'Timeout (0:01:30)!',
])
@pytest.mark.parametrize('returncode', [0, 7])
def test_long_python_diagnostics_keep_start_and_current_thread_without_changing_outcome(
        ci_runner, capsys, header, returncode):
    runner, directory, start, children, monitors, notices = ci_runner
    first_frame = '  File "native%owner.py", line 41 in first_observed_frame'
    current_frame = '  File "current%owner.py", line 52 in current_observed_frame'
    frames = ''.join(f'  File "framework.py", line {index} in framework_{index}\n'
                     for index in range(120))
    report = (header + '\nThread 0x1234 (most recent call first):\n' + first_frame + '\n'
              + frames + 'Current thread 0x5678 (most recent call first):\n'
              + current_frame + '\n' + frames)
    prologue = ('tests/test_example.py::test_header[Windows fatal exception: access violation] PASSED\n'
                'tests/test_example.py::test_header[Timeout (0:01:30)!] PASSED\n')
    original = prologue + 'tests/test_example.py::test_pending ' + report
    outcome, worker = start(f'''
sys.stdout.write({prologue!r})
sys.stdout.write('tests/test_example.py::test_pending ')
sys.stdout.flush()
sys.stderr.write({report[:12]!r})
sys.stderr.flush()
sys.stderr.write({report[12:]!r})
sys.stderr.flush()
raise SystemExit({returncode})
''')
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome
    assert outcome['returncode'] == children[0].returncode == returncode
    assert all(not monitor.is_alive() for monitor in monitors)
    assert (directory / 'stdout.txt').read_text() == original
    assert json.loads((directory / 'result.json').read_text())['returncode'] == returncode
    assert notice_row(notices[-1])['owned_child_returncode'] == returncode
    assert notice_row(notices[-1])['last_observed_complete_row'] is None
    console = capsys.readouterr().out
    annotations = [line.removeprefix(DIAGNOSTIC) for line in console.splitlines()
                   if line.startswith(DIAGNOSTIC)]
    if not returncode:
        assert annotations == []
        assert '::error ' not in console
        return
    assert len(annotations) == 1
    assert len(annotations[0]) <= 3500
    excerpt = annotations[0].replace('%0D', '\r').replace('%0A', '\n').replace('%25', '%')
    assert excerpt.startswith(header + '\n')
    assert first_frame in excerpt and current_frame in excerpt
    assert 'Current thread 0x5678 (most recent call first):' in excerpt
    assert 'tests/test_example.py::test_pending' not in excerpt
    assert '::error title=Native regression::' in console


def test_real_isolated_faulthandler_timeout_survives_long_traceback(ci_runner, capsys):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start('''
import faulthandler
sys.stdout.write('tests/test_example.py::test_pending[Windows fatal exception: quoted parameter] ')
sys.stdout.flush()
def original_timeout_owner(depth):
    if depth:
        return original_timeout_owner(depth - 1)
    # Keep the armed traceback stack blocked on the original parent's release.
    faulthandler.dump_traceback_later(0.025)
    if sys.stdin.buffer.read(1) != b'x':
        raise RuntimeError('The parent did not release the timeout fixture')
original_timeout_owner(80)
faulthandler.cancel_dump_traceback_later()
raise SystemExit(7)
''', pipe_stdin=True)
    wait_for(lambda: (directory / 'stdout.txt').exists()
             and 'original_timeout_owner' in (directory / 'stdout.txt').read_text(), outcome)
    children[0].stdin.write('x')
    children[0].stdin.flush()
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome
    assert outcome['returncode'] == children[0].returncode == 7
    log = (directory / 'stdout.txt').read_text()
    assert len(log) > 3500 and 'Timeout (0:00:00.025000)!' in log
    console = capsys.readouterr().out
    annotations = [line.removeprefix(DIAGNOSTIC) for line in console.splitlines()
                   if line.startswith(DIAGNOSTIC)]
    assert len(annotations) == 1 and len(annotations[0]) <= 3500
    assert annotations[0].startswith('Timeout (0:00:00.025000)!%0AThread ')
    assert 'original_timeout_owner' in annotations[0]


@pytest.mark.parametrize('parameter_header,actual_header,next_header', [
    ('Timeout (0:01:30)!', 'Windows fatal exception: access violation', 'Timeout (0:01:30)!'),
    ('Windows fatal exception: quoted parameter', 'Timeout (0:01:30)!',
     'Windows fatal exception: access violation'),
])
def test_parameter_marker_before_actual_header_keeps_both_distinct_reports(
        ci_runner, capsys, parameter_header, actual_header, next_header):
    runner, directory, start, children, monitors, notices = ci_runner
    frames = ''.join(f'  File "framework.py", line {index} in background_{index}\n'
                     for index in range(120))
    original = (f'tests/test_example.py::test_pending[{parameter_header}] {actual_header}\n'
                + 'Current thread 0x1234 (most recent call first):\n'
                + '  File "actual-first.py", line 1 in actual_first_owner\n' + frames
                + next_header + '\nThread 0x5678 (most recent call first):\n'
                + '  File "next-first.py", line 2 in next_first_owner\n' + frames)
    outcome, worker = start(f'sys.stderr.write({original!r})\nsys.stderr.flush()\nraise SystemExit(7)\n')
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome
    assert outcome['returncode'] == children[0].returncode == 7
    assert (directory / 'stdout.txt').read_text() == original
    assert json.loads((directory / 'result.json').read_text())['returncode'] == 7
    annotations = [line.removeprefix(DIAGNOSTIC) for line in capsys.readouterr().out.splitlines()
                   if line.startswith(DIAGNOSTIC)]
    assert len(annotations) == 2
    assert annotations[0].startswith(actual_header + '%0A')
    assert 'actual_first_owner' in annotations[0]
    assert annotations[1].startswith(next_header + '%0A')
    assert 'next_first_owner' in annotations[1]
    assert all(len(excerpt) <= 3500 for excerpt in annotations)


def test_quoted_header_in_background_frame_keeps_later_current_thread(ci_runner, capsys):
    runner, directory, start, children, monitors, notices = ci_runner
    frames = ''.join(f'  File "framework.py", line {index} in background_{index}\n'
                     for index in range(120))
    original = ('Windows fatal exception: access violation\n'
                + 'Thread 0x1234 (most recent call first):\n' + frames
                + '  File "Windows fatal exception: harmless.py", line 1 in ordinary_frame\n'
                + 'Current thread 0x5678 (most recent call first):\n'
                + '  File "actual-current.py", line 2 in actual_current_owner\n' + frames)
    outcome, worker = start(f'sys.stderr.write({original!r})\nsys.stderr.flush()\nraise SystemExit(7)\n')
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome
    assert outcome['returncode'] == children[0].returncode == 7
    assert (directory / 'stdout.txt').read_text() == original
    annotations = [line.removeprefix(DIAGNOSTIC) for line in capsys.readouterr().out.splitlines()
                   if line.startswith(DIAGNOSTIC)]
    assert len(annotations) == 1 and len(annotations[0]) <= 3500
    assert annotations[0].startswith('Windows fatal exception: access violation%0A')
    assert 'Current thread 0x5678 (most recent call first):' in annotations[0]
    assert 'actual_current_owner' in annotations[0]


def test_fatal_message_with_bracketed_state_keeps_its_original_header_and_first_frame(ci_runner, capsys):
    runner, directory, start, children, monitors, notices = ci_runner
    header = 'Fatal Python error: native_owner: invalid state [state=7]'
    first_frame = '  File "native-owner.py", line 41 in first_fatal_owner'
    frames = ''.join(f'  File "framework.py", line {index} in later_frame_{index}\n'
                     for index in range(120))
    original = (header + '\nPython runtime state: initialized\n\n'
                + 'Current thread 0x1234 (most recent call first):\n'
                + first_frame + '\n' + frames)
    outcome, worker = start(f'sys.stderr.write({original!r})\nsys.stderr.flush()\nraise SystemExit(7)\n')
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome
    assert outcome['returncode'] == children[0].returncode == 7
    assert (directory / 'stdout.txt').read_text() == original
    assert json.loads((directory / 'result.json').read_text())['returncode'] == 7
    annotations = [line.removeprefix(DIAGNOSTIC) for line in capsys.readouterr().out.splitlines()
                   if line.startswith(DIAGNOSTIC)]
    assert len(annotations) == 1 and len(annotations[0]) <= 3500
    assert annotations[0].startswith(header + '%0A')
    assert first_frame in annotations[0]


def test_ordinary_failure_has_no_python_diagnostic_excerpt(ci_runner, capsys):
    runner, directory, start, children, monitors, notices = ci_runner
    outcome, worker = start('''
print('ordinary failure mentioning a timeout and access violation')
print('tests/test_example.py::test_header[Windows fatal exception: access violation] PASSED')
print('tests/test_example.py::test_header[Timeout (0:01:30)!] PASSED')
print('Fatal Python error: this is quoted ordinary output without a stack')
raise SystemExit(7)
''')
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome and outcome['returncode'] == 7
    console = capsys.readouterr().out
    assert DIAGNOSTIC not in console
    assert '::error title=Native regression::ordinary failure' in console


def test_first_timeout_and_fatal_excerpts_are_separate_and_escaped_within_bounds(ci_runner, capsys):
    runner, directory, start, children, monitors, notices = ci_runner
    reports = []
    for header in ('Timeout (0:01:30)!', 'Windows fatal exception: access violation'):
        reports.append(header + '\nThread 0x1234 (most recent call first):\n'
                       + '  File "first-frame-' + '%' * 4000 + '", line 1 in first_owner\n'
                       + 'Current thread 0x5678 (most recent call first):\n'
                       + '  File "current-first-' + '%' * 4000 + '", line 2 in current_owner\n\n')
        reports.append(header + '\nThread 0x1234 (most recent call first):\n'
                       + '  File "later-report.py", line 3 in later_owner\n\n')
    original = ''.join(reports)
    outcome, worker = start(f'sys.stderr.write({original!r})\nsys.stderr.flush()\nraise SystemExit(7)\n')
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome and outcome['returncode'] == 7
    assert (directory / 'stdout.txt').read_text() == original
    annotations = [line.removeprefix(DIAGNOSTIC) for line in capsys.readouterr().out.splitlines()
                   if line.startswith(DIAGNOSTIC)]
    assert len(annotations) == 2
    assert annotations[0].startswith('Timeout (0:01:30)!%0A')
    assert annotations[1].startswith('Windows fatal exception: access violation%0A')
    for excerpt in annotations:
        assert len(excerpt) <= 3500 and '\r' not in excerpt and '\n' not in excerpt
        assert 'first-frame-%25%25' in excerpt and 'current-first-%25%25' in excerpt
        assert 'later-report.py' not in excerpt


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
            child = original_popen(child_command(script, directory), **options)
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
    wait_for(notice_held.is_set, outcome)
    (directory / 'write').touch()
    wait_for(lambda: (directory / 'stdout.txt').read_text() == 'FAILED raced\n', outcome)
    wait_for(contender.is_set, outcome)
    release_notice.set()
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome and outcome['returncode'] == 7
    assert (directory / 'stdout.txt').read_bytes() == ('FAILED raced' + os.linesep).encode('utf-8')
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
    wait_for(partial_seen.is_set, outcome)
    observed = ''.join(fragments).count(NOTICE)
    wait_for(lambda: ''.join(fragments).count(NOTICE) > observed and ''.join(fragments).endswith('\n'), outcome)
    (directory / 'release').touch()
    worker.join(timeout=5)
    assert not worker.is_alive() and 'error' not in outcome and outcome['returncode'] == 7
    assert (directory / 'stdout.txt').read_bytes() == b'eof partial'
    assert 'eof partial\n::' in ''.join(fragments)
    assert_complete_commands(''.join(fragments), [
        '::error title=Native regression::eof partial',
    ])
