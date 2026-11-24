"""Bounded trusted-user commands, with process-group cleanup on timeout."""

import ctypes
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
from collections.abc import Callable


_cancel_requested = False


def identity(pid: int) -> dict:
    """Observe one live Linux process without confusing a reused PID or zombie."""
    if type(pid) is not int or pid < 1:
        raise ValueError('Process has no valid identity')
    fields = Path('/proc/' + str(pid) + '/stat').read_text().rsplit(')', 1)[1].split()
    if fields[0] == 'Z':
        raise ValueError('Original process has exited')
    return {'pid': pid, 'start_ticks': fields[19],
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def notify_identity(expected: dict, signum: int) -> None:
    """Signal a PID-bound Linux descriptor even on Python builds without wrappers."""
    libc = ctypes.CDLL(None, use_errno=True)
    if hasattr(os, 'pidfd_open'):
        descriptor = os.pidfd_open(expected['pid'])
    else:
        open_pid = getattr(libc, 'pidfd_open', None)
        if open_pid is None:
            raise OSError('This runtime has no pidfd_open support; local notification is unconfirmed')
        descriptor = open_pid(ctypes.c_int(expected['pid']), ctypes.c_uint(0))
        if descriptor < 0:
            raise OSError(ctypes.get_errno(), 'Cannot bind original process notification')
    try:
        if identity(expected['pid']) != expected:
            raise ValueError('Original process identity changed before local notification')
        if hasattr(signal, 'pidfd_send_signal'):
            signal.pidfd_send_signal(descriptor, signum)
        else:
            send_pid = getattr(libc, 'pidfd_send_signal', None)
            if send_pid is None:
                raise OSError('This runtime has no pidfd_send_signal support; local notification is unconfirmed')
            if send_pid(ctypes.c_int(descriptor), ctypes.c_int(signum), ctypes.c_void_p(), ctypes.c_uint(0)) < 0:
                raise OSError(ctypes.get_errno(), 'Cannot notify original process')
    finally:
        os.close(descriptor)


def resolve_program(program: str, cwd: Path) -> str:
    candidate = str(cwd / program) if os.path.dirname(program) and not Path(program).is_absolute() else program
    native = shutil.which(candidate + ".exe") if os.name == "nt" and not Path(candidate).suffix else None
    resolved = native or shutil.which(candidate)
    if resolved is None:
        raise FileNotFoundError(f"Executable not found: {program}")
    if os.name == "nt" and Path(resolved).suffix.lower() in (".bat", ".cmd"):
        raise ValueError("Windows batch launchers are not supported as agent commands; install the native .exe or select an explicit interpreter executable")
    return resolved


def _run_windows(argv, cwd, output, timeout, stdin, env, deadline=None, stop_requested=None):
    from ergora.runtime.windows_job import Job

    environment = dict(os.environ if env is None else env, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    request = json.dumps({"argv": argv, "stdin": stdin, "deadline_monotonic": deadline}, ensure_ascii=False)
    status = "succeeded"
    with (output / "stdout.txt").open("w", encoding="utf-8") as stdout, (output / "stderr.txt").open("w", encoding="utf-8") as stderr:
        with Job() as job:
            if deadline is not None and time.monotonic() >= deadline:
                return {"status": "timed_out", "returncode": None, "output": str(output)}
            if stop_requested is not None and stop_requested():
                return {"status": "cancelled", "returncode": None, "output": str(output)}
            process = subprocess.Popen([sys.executable, "-m", "ergora.runtime.processes", "--windows-child"],
                                       cwd=cwd, env=environment, stdin=subprocess.PIPE, stdout=stdout,
                                       stderr=stderr, text=True, encoding="utf-8",
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            try:
                # Our child waits for stdin. No user program runs before assignment.
                job.assign(process.pid)
                wait_deadline = deadline if deadline is not None else time.monotonic() + timeout
                payload = request
                while True:
                    if stop_requested is not None and stop_requested():
                        status = "cancelled"
                        break
                    remaining = wait_deadline - time.monotonic()
                    if remaining <= 0:
                        status = "timed_out"
                        break
                    try:
                        # Windows native waits can defer Python signal handlers.
                        # Return to Python regularly so Ctrl+C can close the job.
                        process.communicate(payload, timeout=min(.2, remaining))
                        if deadline is not None and time.monotonic() >= deadline:
                            status = "timed_out"
                        break
                    except subprocess.TimeoutExpired:
                        payload = None  # communicate must receive stdin only once.
                        if time.monotonic() >= wait_deadline:
                            status = "timed_out"
                            break
                    except KeyboardInterrupt:
                        status = "cancelled"
                        break
            except BaseException:
                process.kill()  # Also covers assignment failure before the gate opens.
                process.wait()
                raise
        process.communicate()  # The entire job has stopped, including inherited descendants.
    if process.returncode and status == "succeeded":
        status = "failed"
    return {"status": status, "returncode": process.returncode, "output": str(output)}


def cancel_supervised() -> None:
    """Signal-safe request for the dedicated stage driver; never interrupt its cleanup."""
    global _cancel_requested
    _cancel_requested = True


def prepare_supervised() -> None:
    """Prepare a dedicated, single-job Linux owner to reap orphaned descendants."""
    if sys.platform != 'linux':
        raise ValueError('Supervised process ownership requires Linux; use WSL2')
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # Linux PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), "Cannot adopt supervised agent descendants")
    enabled = ctypes.c_int()
    if libc.prctl(37, ctypes.byref(enabled), 0, 0, 0) != 0:  # PR_GET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), 'Cannot observe supervised process ownership')
    if enabled.value != 1:
        raise OSError('Supervised process ownership was not enabled')


_adopt_children = prepare_supervised


def _process_stamp(pid: int) -> dict:
    fields = Path('/proc/' + str(pid) + '/stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'start_ticks': fields[19],
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def _observe_direct_child_start(pid: int) -> dict:
    try:
        return {'process': _process_stamp(pid)}
    except FileNotFoundError as error:
        return {'state': 'missing', 'error': str(error)}
    except OSError as error:
        return {'state': 'unknown', 'error': str(error)}
    except (IndexError, ValueError) as error:
        return {'state': 'invalid', 'error': str(error)}


def _reap_children() -> list[dict]:
    children = Path(f"/proc/{os.getpid()}/task/{os.getpid()}/children")
    waited = []
    while True:
        pids = [int(value) for value in children.read_text(encoding="utf-8").split()]
        if not pids:
            return waited
        observed = {}
        for pid in pids:
            try:
                observed[pid] = _process_stamp(pid)
                os.kill(pid, signal.SIGKILL)
            except (FileNotFoundError, ProcessLookupError):
                pass
        for pid in pids:
            try:
                actual, status = os.waitpid(pid, 0)
                waited.append({'process': observed.get(pid), 'wait_pid': actual, 'wait_status': status})
            except ChildProcessError:
                waited.append({'process': observed.get(pid), 'wait_pid': None, 'wait_status': None})


def _record_cleanup(output: Path, value: dict) -> None:
    with (output / 'process-cleanup.json').open('xb') as stream:
        stream.write(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8'))
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def run(argv: list[str], cwd: Path, output: Path, timeout: float, stdin: str = "",
        env: dict | None = None, *, supervised: bool = False, lock_fd: int | None = None,
        command_record: Path | None = None, stop_requested: Callable[[], bool] | None = None,
        record_lifecycle: bool = False, deadline: float | None = None,
        on_start: Callable[[dict], None] | None = None, observe_direct_child_start: bool = False) -> dict:
    if (record_lifecycle or on_start is not None) and not supervised:
        raise ValueError('Durable subtree receipts require the original supervised process owner')
    if deadline is not None:
        if supervised:
            raise ValueError('Supervised processes require their original stop owner, not an ordinary deadline')
        deadline = min(deadline, time.monotonic() + timeout)
    def should_stop():
        return (supervised and _cancel_requested) or (stop_requested is not None and stop_requested())
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    (output / "stdin.txt").write_text(stdin, encoding="utf-8", newline="\n")
    if os.name == "nt":
        if supervised or lock_fd is not None:
            raise ValueError("Supervised reference execution requires Linux; use WSL2")
        argv = [resolve_program(argv[0], cwd), *argv[1:]]
    if command_record is not None:
        command_record.write_text(json.dumps(argv), encoding="utf-8", newline="\n")
    if os.name == "nt":
        return _run_windows(argv, cwd, output, timeout, stdin, env, deadline, stop_requested)
    status = "succeeded"
    if supervised:
        _adopt_children()
    owner = identity(os.getpid()) if record_lifecycle else None
    model = None
    direct_child_start = None
    with ((output / "stdout.txt").open("w", encoding="utf-8") as stdout,
          (output / "stderr.txt").open("w", encoding="utf-8") as stderr,
          (output / "stdin.txt").open("rb") as recorded_input):
        process = None
        try:
            if deadline is not None and time.monotonic() >= deadline:
                status = "timed_out"
            elif should_stop():
                status = "cancelled"
            else:
                process = subprocess.Popen(
                    argv, cwd=cwd, env=env, stdin=recorded_input, stdout=stdout, stderr=stderr,
                    text=True, start_new_session=not supervised,
                    pass_fds=() if lock_fd is None else (lock_fd,), encoding="utf-8")
                if record_lifecycle or on_start is not None:
                    model = _process_stamp(process.pid)
                elif observe_direct_child_start and not supervised and sys.platform == 'linux':
                    # The original Popen still owns this child, including an unreaped fast exit.
                    direct_child_start = _observe_direct_child_start(process.pid)
                if on_start is not None:
                    on_start(model)
                try:
                    if supervised or stop_requested is not None:
                        # TERM only requests cancellation, including during final cleanup.
                        wait_deadline = None if supervised else (deadline if deadline is not None else time.monotonic() + timeout)
                        while not should_stop():
                            interval = 0.2 if wait_deadline is None else min(0.2, wait_deadline - time.monotonic())
                            if interval <= 0:
                                status = "timed_out"
                                break
                            try:
                                process.wait(timeout=interval)
                                break
                            except subprocess.TimeoutExpired:
                                pass
                    else:
                        remaining = timeout if deadline is None else deadline - time.monotonic()
                        if remaining <= 0:
                            status = "timed_out"
                        else:
                            process.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    status = "timed_out"
                except KeyboardInterrupt:
                    status = "cancelled"
        finally:
            if process is not None:
                try:
                    if supervised:
                        if process.poll() is None:
                            process.kill()
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            if supervised:
                descendants = _reap_children()
                if record_lifecycle:
                    _record_cleanup(output, {'schema_version': 1, 'kind': 'supervised-process-cleanup',
                        'owner': owner, 'model': model, 'model_waited': process is not None,
                        'returncode': process.returncode if process is not None else None,
                        'descendants': descendants, 'remaining_children':
                        Path(f'/proc/{os.getpid()}/task/{os.getpid()}/children').read_text().split()})
    code = process.returncode if process is not None else None
    if should_stop():
        status = "cancelled"
    if code and status == "succeeded":
        status = "failed"
    result = {"status": status, "returncode": code, "output": str(output)}
    if direct_child_start is not None:
        result['direct_child_start'] = direct_child_start
    return result


if __name__ == "__main__":
    if os.name != "nt" or sys.argv[1:] != ["--windows-child"]:
        raise SystemExit("This entry point is the Windows command gate")
    request = json.load(sys.stdin)
    # Binary input preserves the prompt's exact UTF-8 bytes, including mixed LF/CRLF.
    payload = request["stdin"].encode("utf-8")
    deadline = request["deadline_monotonic"]
    if deadline is not None and time.monotonic() >= deadline:
        raise SystemExit("Windows command deadline expired before admission")
    raise SystemExit(subprocess.run(request["argv"], input=payload).returncode)
