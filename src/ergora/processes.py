"""Bounded trusted-user commands, with process-group cleanup on timeout."""

import ctypes
import os
from pathlib import Path
import signal
import subprocess


_cancel_requested = False


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
        pids = [int(value) for value in children.read_text().split()]
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
    (output / "stdin.txt").write_text(stdin)
    status = "succeeded"
    if supervised:
        _adopt_children()
    with (output / "stdout.txt").open("w") as stdout, (output / "stderr.txt").open("w") as stderr:
        process = None
        try:
            if not (supervised and _cancel_requested):
                process = subprocess.Popen(
                    argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                    text=True, start_new_session=not supervised,
                    pass_fds=() if lock_fd is None else (lock_fd,),
                )
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
