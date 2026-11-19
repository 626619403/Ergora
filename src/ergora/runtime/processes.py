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


def _run_windows(argv, cwd, output, timeout, stdin, env):
    from ergora.runtime.windows_job import Job

    environment = dict(os.environ if env is None else env, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    request = json.dumps({"argv": argv, "stdin": stdin}, ensure_ascii=False)
    status = "succeeded"
    with (output / "stdout.txt").open("w", encoding="utf-8") as stdout, (output / "stderr.txt").open("w", encoding="utf-8") as stderr:
        with Job() as job:
            process = subprocess.Popen([sys.executable, "-m", "ergora.runtime.processes", "--windows-child"],
                                       cwd=cwd, env=environment, stdin=subprocess.PIPE, stdout=stdout,
                                       stderr=stderr, text=True, encoding="utf-8",
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            try:
                # Our child waits for stdin. No user program runs before assignment.
                job.assign(process.pid)
                deadline = time.monotonic() + timeout
                payload = request
                while True:
                    try:
                        # Windows native waits can defer Python signal handlers.
                        # Return to Python regularly so Ctrl+C can close the job.
                        process.communicate(payload, timeout=min(.2, max(0, deadline - time.monotonic())))
                        break
                    except subprocess.TimeoutExpired:
                        payload = None  # communicate must receive stdin only once.
                        if time.monotonic() >= deadline:
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


def _reap_children() -> None:
    children = Path(f"/proc/{os.getpid()}/task/{os.getpid()}/children")
    while True:
        pids = [int(value) for value in children.read_text(encoding="utf-8").split()]
        if not pids:
            return
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for pid in pids:
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass


def run(argv: list[str], cwd: Path, output: Path, timeout: int, stdin: str = "",
        env: dict | None = None, *, supervised: bool = False, lock_fd: int | None = None,
        command_record: Path | None = None, stop_requested: Callable[[], bool] | None = None) -> dict:
    should_stop = stop_requested or (lambda: _cancel_requested)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    (output / "stdin.txt").write_text(stdin, encoding="utf-8", newline="\n")
    if os.name == "nt":
        if supervised or lock_fd is not None:
            raise ValueError("Supervised reference execution requires Linux; use WSL2")
        argv = [resolve_program(argv[0], cwd), *argv[1:]]
    if command_record is not None:
        command_record.write_text(json.dumps(argv), encoding="utf-8", newline="\n")
    if os.name == "nt":
        return _run_windows(argv, cwd, output, timeout, stdin, env)
    status = "succeeded"
    if supervised:
        _adopt_children()
    with ((output / "stdout.txt").open("w", encoding="utf-8") as stdout,
          (output / "stderr.txt").open("w", encoding="utf-8") as stderr,
          (output / "stdin.txt").open("rb") as recorded_input):
        process = None
        try:
            if not (supervised and should_stop()):
                process = subprocess.Popen(
                    argv, cwd=cwd, env=env, stdin=recorded_input, stdout=stdout, stderr=stderr,
                    text=True, start_new_session=not supervised,
                    pass_fds=() if lock_fd is None else (lock_fd,), encoding="utf-8")
                try:
                    if supervised:
                        # TERM only requests cancellation, including during final cleanup.
                        while not should_stop():
                            try:
                                process.wait(timeout=0.2)
                                break
                            except subprocess.TimeoutExpired:
                                pass
                    else:
                        process.wait(timeout=timeout)
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
                _reap_children()
    code = process.returncode if process is not None else None
    if supervised and should_stop():
        status = "cancelled"
    if code and status == "succeeded":
        status = "failed"
    return {"status": status, "returncode": code, "output": str(output)}


if __name__ == "__main__":
    if os.name != "nt" or sys.argv[1:] != ["--windows-child"]:
        raise SystemExit("This entry point is the Windows command gate")
    request = json.load(sys.stdin)
    # Binary input preserves the prompt's exact UTF-8 bytes, including mixed LF/CRLF.
    raise SystemExit(subprocess.run(request["argv"], input=request["stdin"].encode("utf-8")).returncode)
