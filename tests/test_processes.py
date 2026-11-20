import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from ergora.runtime import processes
from ergora.storage.state import file_lock


@pytest.mark.skipif(sys.platform != 'linux', reason='PID-bound Linux local notification')
@pytest.mark.parametrize('wrappers', ['python', 'libc'])
def test_notification_binds_the_original_identity_before_signalling(monkeypatch, wrappers):
    import signal

    if wrappers == 'libc':
        monkeypatch.delattr(os, 'pidfd_open', raising=False)
        monkeypatch.delattr(signal, 'pidfd_send_signal', raising=False)
    child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'], start_new_session=True)
    try:
        expected = processes.identity(child.pid)
        with pytest.raises(ValueError, match='identity changed'):
            processes.notify_identity({**expected, 'start_ticks': str(int(expected['start_ticks']) + 1)}, signal.SIGTERM)
        assert child.poll() is None
        processes.notify_identity(expected, signal.SIGTERM)
        assert child.wait(timeout=5) == -signal.SIGTERM
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()


@pytest.mark.skipif(sys.platform != 'linux', reason='Dedicated supervised Linux process owner')
def test_slow_supervised_reader_receives_complete_large_utf8_input(tmp_path):
    reader = 'import sys,time,hashlib;time.sleep(.35);print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())'
    controller = (
        'import sys,time,json;from pathlib import Path;from ergora.runtime import processes;'
        "payload='漢字\\r\\nline\\n'*32768;started=time.monotonic();"
        f'result=processes.run([sys.executable,"-c",{reader!r}],Path({str(tmp_path)!r}),'
        f'Path({str(tmp_path / "output")!r}),5,payload,supervised=True,'
        'stop_requested=lambda:time.monotonic()-started>=5);print(json.dumps(result))'
    )
    result = subprocess.run([sys.executable, '-c', controller], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['status'] == 'succeeded'
    expected = hashlib.sha256(('漢字\r\nline\n' * 32768).encode()).hexdigest()
    assert (tmp_path / 'output/stdout.txt').read_text().strip() == expected


def test_unicode_paths_and_stdin_are_literal_utf8(tmp_path):
    cwd = tmp_path / '项目 with spaces'
    cwd.mkdir()
    script = cwd / '处理.py'
    script.write_text('import json,sys;print(json.dumps([sys.argv[1:],sys.stdin.read()],ensure_ascii=False))', encoding='utf-8')
    literal = '中文 & $HOME %PATH% !quoted! "value"'
    result = processes.run([sys.executable, str(script), literal], cwd, tmp_path / 'output', 10, literal)
    assert result['status'] == 'succeeded'
    assert json.loads((tmp_path / 'output/stdout.txt').read_text(encoding='utf-8')) == [[literal], literal]


def test_powershell_utf8_bom_inputs_roundtrip(tmp_path, capsys):
    import ergora.interfaces.cli as cli
    import ergora.configuration.projects as projects
    import ergora.definitions.skills as skill_assets
    from ergora.storage.state import State

    repo = tmp_path / '项目'
    subprocess.run(['git', 'init', str(repo)], check=True, capture_output=True)
    state = State(tmp_path / 'data')
    projects.create(state, 'demo', repo)
    binding = tmp_path / 'binding.json'
    binding.write_text(json.dumps({'tool': 'command', 'argv': [sys.executable, '-c',
                       'import sys;print(sys.stdin.read())']}), encoding='utf-8-sig')
    prompt = tmp_path / 'prompt.md'
    prompt.write_text('中文提示', encoding='utf-8-sig')
    prefix = ['--home', str(state.root)]
    assert cli.main(prefix + ['project', 'bind', 'demo', 'reviewer', '--binding', str(binding), '--revision', '1']) == 0
    capsys.readouterr()
    assert cli.main(prefix + ['agent', 'run', 'demo', 'reviewer', '--prompt', str(prompt)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert Path(result['output'], 'stdin.txt').read_text(encoding='utf-8') == '中文提示'
    bundle = tmp_path / 'bom-skill'
    bundle.mkdir()
    (bundle / 'SKILL.md').write_text('---\nname: bom-skill\ndescription: 中文技能\n---\n中文操作\n', encoding='utf-8-sig')
    imported = skill_assets.import_bundle(state, 'demo', bundle)
    assert skill_assets.get(state, 'demo', imported['digest'])['name'] == 'bom-skill'


@pytest.mark.parametrize('finish', ['normal', 'timeout', 'deadline'])
def test_command_completion_stops_descendants(tmp_path, finish):
    ready, late = tmp_path / 'ready', tmp_path / 'late'
    child = f'import time;from pathlib import Path;Path({str(ready)!r}).touch();time.sleep(4);Path({str(late)!r}).touch()'
    code = (
        'import subprocess,sys,time;from pathlib import Path;'
        f'subprocess.Popen([sys.executable,"-c",{child!r}]);\n'
        f'while not Path({str(ready)!r}).exists():time.sleep(.01)\n'
        + ('time.sleep(20)' if finish != 'normal' else '')
    )
    limits = {'deadline': time.monotonic() + 2} if finish == 'deadline' else {}
    result = processes.run([sys.executable, '-c', code], tmp_path, tmp_path / 'output',
                           2 if finish == 'timeout' else 10, **limits)
    assert ready.exists(), 'The real descendant must start before completion/timeout'
    assert result['status'] == ('succeeded' if finish == 'normal' else 'timed_out')
    time.sleep(4.2)
    assert not late.exists()


@pytest.mark.parametrize('setup_seconds', [.5, 1])
def test_absolute_deadline_covers_setup_and_post_spawn_wait(tmp_path, monkeypatch, setup_seconds):
    clock = [10.0]
    monkeypatch.setattr(processes, 'time', SimpleNamespace(monotonic=lambda: clock[0]))
    write = Path.write_text

    def write_input(path, *args, **kwargs):
        result = write(path, *args, **kwargs)
        if path.name == 'stdin.txt':
            clock[0] += setup_seconds
        return result

    monkeypatch.setattr(Path, 'write_text', write_input)
    waits, killed = [], []

    class Process:
        pid = 123
        returncode = 0

        def __init__(self, *args, **kwargs):
            assert clock[0] < 11, 'Expired command must never reach Popen'
            clock[0] += .25

        def wait(self, timeout=None):
            waits.append(timeout)
            return self.returncode

    monkeypatch.setattr(processes.subprocess, 'Popen', Process)
    monkeypatch.setattr(processes.os, 'killpg', lambda *args: killed.append(args), raising=False)
    if os.name == 'nt':
        pytest.skip('POSIX Popen/wait owner; the Windows command gate is tested separately')
    result = processes.run(['fixture'], tmp_path, tmp_path / 'output', 10, deadline=11)
    assert result['status'] == ('succeeded' if setup_seconds < 1 else 'timed_out')
    assert result['returncode'] == (0 if setup_seconds < 1 else None)
    assert waits == ([.25, None] if setup_seconds < 1 else [])
    assert len(killed) == (1 if setup_seconds < 1 else 0)


@pytest.mark.parametrize('setup_seconds,assignment_seconds,completion_seconds,returncode', [
    (0, .1, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, .1, .5, 41), (0, .1, 0, 41)])
def test_windows_deadline_is_not_renewed_at_the_command_gate(
        tmp_path, monkeypatch, setup_seconds, assignment_seconds, completion_seconds, returncode):
    clock = [10.0]
    monkeypatch.setattr(processes, 'time', SimpleNamespace(monotonic=lambda: clock[0]))
    released, closed = [], []

    class Job:
        def __enter__(self):
            clock[0] += setup_seconds
            return self

        def __exit__(self, *args):
            closed.append(True)

        def assign(self, pid):
            clock[0] += assignment_seconds

    class Process:
        pid = 123

        def __init__(self):
            assert clock[0] < 10.5, 'Expired gate must never reach Popen'
            self.returncode = returncode

        def communicate(self, payload=None, timeout=None):
            if payload is not None:
                released.append((json.loads(payload), timeout))
                clock[0] += completion_seconds
            else:
                assert closed, 'The original job must close before final pipe collection'

    monkeypatch.setitem(sys.modules, 'ergora.runtime.windows_job', SimpleNamespace(Job=Job))
    monkeypatch.setattr(processes.subprocess, 'Popen', lambda *args, **kwargs: Process())
    monkeypatch.setattr(processes.subprocess, 'CREATE_NEW_PROCESS_GROUP', 512, raising=False)
    output = tmp_path / 'output'
    output.mkdir()
    result = processes._run_windows(['fixture'], tmp_path, output, 10, 'input', None, deadline=10.5)
    expected = 'timed_out' if setup_seconds + assignment_seconds + completion_seconds >= .5 else 'failed' if returncode else 'succeeded'
    assert result['status'] == expected
    assert len(released) == (1 if setup_seconds + assignment_seconds < .5 else 0)
    if released:
        assert released[0][0] == {'argv': ['fixture'], 'stdin': 'input', 'deadline_monotonic': 10.5}
        assert 0 < released[0][1] <= .2
    assert closed == [True]


@pytest.mark.parametrize('read_seconds,encode_seconds,deadline,admitted', [
    (.1, .1, 10.5, True), (.6, 0, 10.5, False), (0, .6, 10.5, False), (.6, .6, None, True)])
def test_windows_child_admission_checks_after_complete_input_preparation(read_seconds, encode_seconds, deadline, admitted):
    # Execute the exact entry branch on this host, without claiming native Windows.
    entry = ast.parse(Path(processes.__file__).read_text(encoding='utf-8')).body[-1]
    clock, launches = [10.0], []

    class Input(str):
        def encode(self, encoding):
            clock[0] += encode_seconds
            return super().encode(encoding)

    def read_request(stream):
        clock[0] += read_seconds
        return {'argv': ['fixture'], 'stdin': Input('input\r\n漢字'), 'deadline_monotonic': deadline}

    def launch(argv, **kwargs):
        launches.append((clock[0], argv, kwargs['input']))
        return SimpleNamespace(returncode=0)

    namespace = {'__name__': '__main__', 'os': SimpleNamespace(name='nt'),
                 'sys': SimpleNamespace(argv=['processes.py', '--windows-child'], stdin=None),
                 'json': SimpleNamespace(load=read_request), 'subprocess': SimpleNamespace(run=launch),
                 'time': SimpleNamespace(monotonic=lambda: clock[0])}
    with pytest.raises(SystemExit):
        exec(compile(ast.Module(body=[entry], type_ignores=[]), processes.__file__, 'exec'), namespace)
    assert len(launches) == int(admitted)
    if launches:
        actual_time, argv, payload = launches[0]
        assert deadline is None or actual_time < deadline
        assert argv == ['fixture'] and payload == 'input\r\n漢字'.encode('utf-8')


def test_cross_process_file_lock_exclusion_and_recovery(tmp_path):
    path = tmp_path / 'run.lock'
    script = ('from pathlib import Path;import sys;from ergora.storage.state import file_lock;'
              'lock=file_lock(Path(sys.argv[1]),blocking=False);lock.__enter__();print("acquired")')
    with file_lock(path):
        result = subprocess.run([sys.executable, '-c', script, str(path)], capture_output=True, text=True, timeout=10)
        assert result.returncode != 0 and 'BlockingIOError' in result.stderr
    result = subprocess.run([sys.executable, '-c', script, str(path)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0 and 'acquired' in result.stdout


@pytest.mark.skipif(os.name != 'nt', reason='Windows Job Object controller-death contract')
def test_controller_death_kills_job_before_delayed_write(tmp_path):
    ready, late = tmp_path / 'ready', tmp_path / 'late'
    target = f'import time;from pathlib import Path;Path({str(ready)!r}).touch();time.sleep(3);Path({str(late)!r}).touch()'
    controller = ('from pathlib import Path;import sys;from ergora.runtime import processes;'
                  f'processes.run([sys.executable,"-c",{target!r}],Path({str(tmp_path)!r}),Path({str(tmp_path / "output")!r}),20)')
    process = subprocess.Popen([sys.executable, '-c', controller], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists()
        process.kill()
        process.communicate(timeout=10)
        time.sleep(3.2)
        assert not late.exists()
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)


@pytest.mark.skipif(os.name != 'nt', reason='Windows console cancellation contract')
def test_native_console_event_cancels_and_stops_descendants(tmp_path):
    fixture = Path(__file__).parent / 'fixtures/windows_cancel.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path)],
                            creationflags=subprocess.CREATE_NEW_CONSOLE,
                            capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'cancellation and descendant cleanup: PASS' in result.stdout


@pytest.mark.skipif(os.name != 'nt', reason='Windows job assignment gate')
def test_job_assignment_failure_never_launches_command(tmp_path, monkeypatch):
    from ergora.runtime.windows_job import Job

    def refuse(self, pid):
        raise OSError('fixture assignment denied')

    monkeypatch.setattr(Job, 'assign', refuse)
    marker = tmp_path / 'unexpected'
    with pytest.raises(OSError, match='assignment denied'):
        processes.run([sys.executable, '-c', f'from pathlib import Path;Path({str(marker)!r}).touch()'],
                      tmp_path, tmp_path / 'output', 10)
    assert not marker.exists()


@pytest.mark.skipif(os.name != 'nt', reason='Native Windows command selection')
def test_windows_batch_launcher_is_explicitly_rejected(tmp_path):
    script = tmp_path / 'not-native.cmd'
    script.write_text('@echo unexpected', encoding='ascii')
    with pytest.raises(ValueError, match='batch launchers'):
        processes.run([str(script)], tmp_path, tmp_path / 'output', 10)
