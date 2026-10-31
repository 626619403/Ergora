"""Actual Windows console control event, with a private console on CI."""

import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def controller(root):
    from ergora import processes

    # CREATE_NEW_PROCESS_GROUP disables Ctrl+C initially; explicitly enable it.
    if not ctypes.windll.kernel32.SetConsoleCtrlHandler(None, False):
        raise ctypes.WinError()
    signal.signal(signal.SIGINT, signal.default_int_handler)
    child = (f'import time;from pathlib import Path;Path({str(root / "ready")!r}).touch();'
             f'time.sleep(4);Path({str(root / "late")!r}).touch()')
    target = f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{child!r}]);time.sleep(30)'
    result = processes.run([sys.executable, '-c', target], root, root / 'output', 20)
    print(json.dumps(result), flush=True)


def check(root):
    # This driver owns a private console. A Ctrl+C broadcast reaches only its
    # attached processes; the driver ignores it and the controller enables it.
    if not ctypes.windll.kernel32.SetConsoleCtrlHandler(None, True):
        raise ctypes.WinError()
    process = subprocess.Popen([sys.executable, __file__, str(root), '--controller'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    try:
        deadline = time.monotonic() + 10
        while not (root / 'ready').exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        assert (root / 'ready').exists(), 'Descendant did not start'
        os.kill(0, signal.CTRL_C_EVENT)
        out, err = process.communicate(timeout=10)
        assert process.returncode == 0, out + err
        assert json.loads(out)['status'] == 'cancelled', out + err
        time.sleep(4.2)
        assert not (root / 'late').exists()
        print('console cancellation and descendant cleanup: PASS')
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)


if __name__ == '__main__':
    (controller if '--controller' in sys.argv else check)(Path(sys.argv[1]))
