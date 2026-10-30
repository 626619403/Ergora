"""Schedule real TERM during process creation or the first descendant cleanup."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


DRIVER = r'''
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from ergora import processes, stage_driver

root, boundary = Path(sys.argv[1]), sys.argv[2]
signal.signal(signal.SIGTERM, stage_driver._cancel)
ready, late = root / "ready", root / "late"
child = (
    "import signal,time;from pathlib import Path;"
    "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
    f"Path({str(ready)!r}).touch();time.sleep(2);Path({str(late)!r}).touch()"
)
kept = []
if boundary == "creation":
    real_popen = processes.subprocess.Popen

    def creating(*args, **kwargs):
        process = real_popen([sys.executable, "-c", child], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        kept.append(process)
        while not ready.exists():
            time.sleep(0.01)
        os.kill(os.getpid(), signal.SIGTERM)
        return process

    processes.subprocess.Popen = creating
    argv = [sys.executable, "-c", "pass"]
else:
    parent = (
        "import subprocess,sys,time;from pathlib import Path;"
        f"subprocess.Popen([sys.executable,'-c',{child!r}]);\n"
        f"while not Path({str(ready)!r}).exists():time.sleep(.01)"
    )
    argv = [sys.executable, "-c", parent]
    real_kill = processes.os.kill

    def killing(pid, sig):
        if sig == signal.SIGKILL and not (root / "barrier").exists():
            (root / "barrier").touch()
            deadline = time.monotonic() + 5
            while not (root / "release").exists():
                if time.monotonic() > deadline:
                    raise TimeoutError("Parent did not release the cleanup barrier")
                time.sleep(0.01)
        return real_kill(pid, sig)

    processes.os.kill = killing

result = processes.run(argv, root, root / "output", 5, supervised=True)
(root / "status").write_text(result["status"])
'''


def main():
    root, boundary = Path(sys.argv[1]), sys.argv[2]
    process = subprocess.Popen([sys.executable, "-c", DRIVER, str(root), boundary],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    try:
        if boundary == "cleanup":
            deadline = time.monotonic() + 5
            while not (root / "barrier").exists() and process.poll() is None:
                if time.monotonic() > deadline:
                    raise TimeoutError("Driver did not reach descendant cleanup")
                time.sleep(0.01)
            assert (root / "barrier").exists(), "Driver exited before cleanup"
            os.kill(process.pid, signal.SIGTERM)
            os.kill(process.pid, signal.SIGTERM)
            (root / "release").touch()
        stdout, stderr = process.communicate(timeout=8)
        assert process.returncode == 0, stdout + stderr
        time.sleep(2.5)
        print(json.dumps({"status": (root / "status").read_text(),
                          "late_write": (root / "late").exists()}))
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


if __name__ == "__main__":
    main()
