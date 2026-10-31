"""Bounded trusted-user commands, with process-group cleanup on timeout."""

import ctypes
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys


_cancel_requested = False


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
    from .windows_job import Job

    argv = [resolve_program(argv[0], cwd), *argv[1:]]
    environment = dict(os.environ if env is None else env, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    request = json.dumps({"argv": argv, "stdin": stdin}, ensure_ascii=False)
    status = "succeeded"
    with (output / "stdout.txt").open("w", encoding="utf-8") as stdout, (output / "stderr.txt").open("w", encoding="utf-8") as stderr:
        with Job() as job:
            process = subprocess.Popen([sys.executable, "-m", "ergora.processes", "--windows-child"],
                                       cwd=cwd, env=environment, stdin=subprocess.PIPE, stdout=stdout,
                                       stderr=stderr, text=True, encoding="utf-8",
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            try:
                # Our child waits for stdin. No user program runs before assignment.
                job.assign(process.pid)
                try:
                    process.communicate(request, timeout=timeout)
                except subprocess.TimeoutExpired:
                    status = "timed_out"
                except KeyboardInterrupt:
                    status = "cancelled"
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


def _adopt_children() -> None:
    # The supervised path runs inside a dedicated, single-job stage_driver.
    # Adopt orphaned grandchildren so completion can reap them before evidence checks.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # Linux PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), "Cannot adopt supervised agent descendants")


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
        env: dict | None = None, *, supervised: bool = False, lock_fd: int | None = None) -> dict:
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    (output / "stdin.txt").write_text(stdin, encoding="utf-8", newline="\n")
    if os.name == "nt":
        if supervised or lock_fd is not None:
            raise ValueError("Supervised reference execution requires Linux; use WSL2")
        return _run_windows(argv, cwd, output, timeout, stdin, env)
    status = "succeeded"
    if supervised:
        _adopt_children()
    with (output / "stdout.txt").open("w", encoding="utf-8") as stdout, (output / "stderr.txt").open("w", encoding="utf-8") as stderr:
        process = None
        try:
            if not (supervised and _cancel_requested):
                process = subprocess.Popen(
                    argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                    text=True, start_new_session=not supervised,
                    pass_fds=() if lock_fd is None else (lock_fd,), encoding="utf-8")
                try:
                    if supervised:
                        # TERM only requests cancellation, including during final cleanup.
                        payload = stdin
                        while not _cancel_requested:
                            try:
                                process.communicate(payload, timeout=0.2)
                                break
                            except subprocess.TimeoutExpired:
                                payload = None
                    else:
                        process.communicate(stdin, timeout=timeout)
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
                process.communicate()
            if supervised:
                _reap_children()
    code = process.returncode if process is not None else None
    if supervised and _cancel_requested:
        status = "cancelled"
    if code and status == "succeeded":
        status = "failed"
    return {"status": status, "returncode": code, "output": str(output)}


if __name__ == "__main__":
    if os.name != "nt" or sys.argv[1:] != ["--windows-child"]:
        raise SystemExit("This entry point is the Windows command gate")
    request = json.load(sys.stdin)
    raise SystemExit(subprocess.run(request["argv"], input=request["stdin"], text=True,
                                    encoding="utf-8").returncode)
