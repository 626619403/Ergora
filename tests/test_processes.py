import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from ergora import processes
from ergora.state import file_lock


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
    from ergora import cli, projects, skills
    from ergora.state import State

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
    imported = skills.import_bundle(state, 'demo', bundle)
    assert skills.get(state, 'demo', imported['digest'])['name'] == 'bom-skill'


@pytest.mark.parametrize('finish', ['normal', 'timeout'])
def test_command_completion_stops_descendants(tmp_path, finish):
    ready, late = tmp_path / 'ready', tmp_path / 'late'
    child = f'import time;from pathlib import Path;Path({str(ready)!r}).touch();time.sleep(4);Path({str(late)!r}).touch()'
    code = (
        'import subprocess,sys,time;from pathlib import Path;'
        f'subprocess.Popen([sys.executable,"-c",{child!r}]);\n'
        f'while not Path({str(ready)!r}).exists():time.sleep(.01)\n'
        + ('time.sleep(20)' if finish == 'timeout' else '')
    )
    result = processes.run([sys.executable, '-c', code], tmp_path, tmp_path / 'output', 2 if finish == 'timeout' else 10)
    assert ready.exists(), 'The real descendant must start before completion/timeout'
    assert result['status'] == ('timed_out' if finish == 'timeout' else 'succeeded')
    time.sleep(4.2)
    assert not late.exists()


def test_cross_process_file_lock_exclusion_and_recovery(tmp_path):
    path = tmp_path / 'run.lock'
    script = ('from pathlib import Path;import sys;from ergora.state import file_lock;'
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
    controller = ('from pathlib import Path;import sys;from ergora import processes;'
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
    from ergora.windows_job import Job

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
