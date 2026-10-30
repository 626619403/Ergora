from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from .core import STATE, UPSTREAM, environment, git, read, require, settings, write


def child_environment(model: str | None) -> dict[str, str]:
    require(model in {None, 'codex'}, 'Unsupported model runner')
    source = environment()
    names = {'PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'TZ', 'TMPDIR', 'TERM',
             'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
             'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}
    if model == 'codex':
        names.add(settings()['codex_env_key'])
    else:
        names.update({'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'LD_LIBRARY_PATH',
                      'OMP_NUM_THREADS', 'MLFLOW_TRACKING_URI'})
        names.update(k for k in source if k.startswith(('NCCL_', 'TORCH_')))
    env = {k: v for k, v in source.items() if k in names or k.startswith('LC_')}
    env.update(PYTHONDONTWRITEBYTECODE='1', DO_NOT_TRACK='1')
    return env


def mapped_command(request: dict) -> list[str]:
    mappings = {'/out': request['output'], '/protocol': request['protocol'],
                '/policy': request['policy'], '/platform/upstream': str(UPSTREAM)}
    command = []
    for item in request['command']:
        for prefix, target in mappings.items():
            if item == prefix or item.startswith(prefix + '/'):
                require(target is not None, 'Missing path mapping: ' + prefix)
                item = target + item[len(prefix):]
                break
        command.append(item)
    return command


def snapshot(checkout: Path) -> tuple[str, str, str]:
    content = hashlib.sha256(git(checkout, 'diff', '--binary', 'HEAD', '--').stdout.encode())
    for relative in git(checkout, 'ls-files', '--others', '--exclude-standard', '-z').stdout.split('\0'):
        if not relative: continue
        path = checkout / relative
        content.update(relative.encode())
        if path.is_symlink(): content.update(os.readlink(path).encode())
        else:
            with path.open('rb') as stream: content.update(hashlib.file_digest(stream, 'sha256').digest())
    return (git(checkout, 'rev-parse', 'HEAD').stdout.strip(),
            git(checkout, 'status', '--porcelain=v1', '-z', '--untracked-files=all').stdout,
            content.hexdigest())


def stop(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def run(folder: Path) -> None:
    require(folder.resolve().is_relative_to((STATE / 'processes').resolve()), 'Job is outside the process registry')
    with (folder / 'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        if (folder / 'terminal.json').exists():
            return
        request = read(folder / 'request.json')
        output = Path(request['output'])
        output.mkdir(parents=True, exist_ok=True, mode=0o700)
        code = 125
        detail = ''
        process = None
        started = time.time()
        log_path = output / 'execution.log'
        try:
            require(not (folder / 'started.json').exists(),
                    'Previous process submission has an unknown outcome. No automatic re-execution; reconcile its recorded PID and output.')
            fence = Path(request['fence']) if request['fence'] else None
            require(fence is None or not fence.exists(), 'Cancelled before process start')
            checkout = Path(request['checkout'])
            before = snapshot(checkout) if not request['writable'] else None
            command = mapped_command(request)
            write(folder / 'started.json', {'time': started, 'name': request['name'], 'command': command,
                                          'monitor_pid': os.getpid()})
            with contextlib.ExitStack() as resources:
                log = resources.enter_context(log_path.open('ab'))
                stdin = subprocess.DEVNULL
                if request['model']:
                    stdin = resources.enter_context((Path(request['protocol']) / 'prompt.txt').open('rb'))
                stdout = log
                process = subprocess.Popen(['/usr/bin/timeout', '--signal=TERM', '--kill-after=5',
                                            str(request['timeout']), *command], cwd=checkout,
                                           stdin=stdin, stdout=stdout, stderr=log,
                                           env=child_environment(request['model']), start_new_session=True,
                                           pass_fds=(lock.fileno(),))
                stat = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()
                write(folder / 'pid.json', {'pid': process.pid, 'start_ticks': stat[19],
                                          'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
                deadline = time.monotonic() + request['timeout'] + 5
                while process.poll() is None:
                    if (fence and fence.exists()) or time.monotonic() >= deadline:
                        detail = 'Cancellation fence observed' if fence and fence.exists() else 'Process walltime exceeded'
                        stop(process)
                        break
                    time.sleep(.2)
                code = process.wait()
            if before is not None and snapshot(checkout) != before:
                code = 126
                detail = 'A stage declared read-only changed the checkout or HEAD; inspect its diff'
        except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
            if process is not None and process.poll() is None:
                stop(process)
            detail = f'{type(error).__name__}: {error}'
            code = 125
        with log_path.open('a') as log:
            log.write('\n' + json.dumps({'returncode': code, 'detail': detail}) + '\n')
        write(folder / 'terminal.json', {'name': request['name'], 'returncode': code,
                                         'detail': detail, 'started_at': started, 'finished_at': time.time()})


if __name__ == '__main__':
    require(len(sys.argv) == 2, 'Expected a process registry directory')
    run(Path(sys.argv[1]))
