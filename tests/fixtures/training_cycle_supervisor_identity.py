"""Observe actual S death while the outer parent lives, without a model or SDK."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from ergora.runtime import processes
import ergora.training.execution_protocol as protocol
from ergora.training.materials import publish_material


stage, home = sys.argv[1], Path(sys.argv[2])


def wait(path):
    deadline = time.monotonic() + 8
    while not path.exists():
        if time.monotonic() >= deadline:
            raise RuntimeError('Owned fixture did not reach its supervision boundary: ' + str(path))
        time.sleep(.01)


if stage == 'H':
    payload = json.loads((home / 'request.json').read_bytes())
    protocol.read_cycle_supervisor(payload, live=True)
    (home / 'h-ready').write_text(json.dumps(processes.identity(os.getpid())))
    wait(home / 'go')
    try:
        protocol.read_cycle_supervisor(payload, live=True)
    except (OSError, ValueError) as error:
        result = {'state': 'blocked', 'reason': str(error), 'parent': os.getppid()}
    else:
        (home / 'model-would-spawn').touch()
        result = {'state': 'incorrectly-admitted', 'parent': os.getppid()}
    (home / 'h-result.json').write_text(json.dumps(result))
elif stage == 'S':
    raw = sys.stdin.buffer.readline().rstrip(b'\n')
    payload = json.loads(raw)
    output = home / 'operations/training-cycles' / payload['identity']['operation_id']
    output.mkdir(parents=True)
    (output / 'request.json').write_bytes(raw)
    record = {'schema_version': 1, 'kind': 'training-cycle-supervisor',
        'identity': payload['identity'], 'request_sha256': hashlib.sha256(raw).hexdigest(),
        'supervisor': processes.identity(os.getpid())}
    publish_material(output / 'supervisor.json', json.dumps(record, sort_keys=True, separators=(',', ':')).encode(), home / 'operations/training-cycles')
    with (output / 'h.stdout').open('xb') as stdout, (output / 'h.stderr').open('xb') as stderr:
        child = subprocess.Popen([sys.executable, '-S', '-P', __file__, 'H', str(output)], stdout=stdout, stderr=stderr)
    wait(output / 'h-ready')
    print(json.dumps({'output': str(output), 'child': child.pid}), flush=True)
    sys.stdin.readline()
else:
    # This isolated fixture owns all test descendants and waits for the adopted H.
    processes.prepare_supervised()
    operation = protocol._CycleOperation(home, 'demo', 'cycle', 'a' * 64, 'inspect')
    supervisor = subprocess.Popen([sys.executable, '-S', '-P', __file__, 'S', str(home)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        supervisor.stdin.write(operation.encoded + b'\n')
        supervisor.stdin.flush()
        ready = supervisor.stdout.readline()
        if not ready:
            raise RuntimeError('Original fixture S failed before H readiness: ' + supervisor.stderr.read().decode())
        value = json.loads(ready)
        output = Path(value['output'])
        supervisor.kill()
        _, stderr = supervisor.communicate(timeout=8)
        assert supervisor.returncode < 0, stderr
        (output / 'go').touch()
        wait(output / 'h-result.json')
        observed = json.loads((output / 'h-result.json').read_bytes())
        waited = processes._reap_children()
        assert observed['state'] == 'blocked' and not (output / 'model-would-spawn').exists()
        assert any(item['wait_pid'] == value['child'] for item in waited)
        assert not (output / 'completion.json').exists()
        print(json.dumps({'observed': observed, 'waited': waited, 'outer': processes.identity(os.getpid())}))
    finally:
        if supervisor.poll() is None:
            supervisor.kill()
            supervisor.communicate(timeout=8)
        processes._reap_children()
