"""A real isolated parent-permit holder or paused stop writer; no scheduler stub."""

import json
import os
from pathlib import Path
import sys

sys.path.insert(0, sys.argv[1])
from ergora.training_execution_protocol import CycleAdmission, decode, read_raw

directory, marker, mode = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
admission = CycleAdmission(directory, decode(read_raw(directory / 'authorization.json')))

if mode == 'hold':
    with admission.permission():
        marker.touch()
        sys.stdin.readline()
    result = {'released': True}
else:
    fsync, opened = os.fsync, os.open
    paused = []

    def pause():
        paused.append(True)
        marker.touch()
        sys.stdin.readline()

    def sync(descriptor):
        path = Path('/proc/self/fd/' + str(descriptor)).resolve()
        target = admission.folder if mode == 'directory-fsync' else admission.stop
        if mode.endswith('fsync') and path == target and not paused:
            pause()
        return fsync(descriptor)

    def create(path, *args, **kwargs):
        descriptor = opened(path, *args, **kwargs)
        if mode == 'create' and path == admission.stop and not paused:
            pause()
        return descriptor

    os.fsync, os.open = sync, create
    if mode == 'concurrent':
        pause()
    result = admission.request_stop(sys.argv[5])

assert not any(name in sys.modules for name in ('yaml', 'jsonschema', 'temporalio', 'dev_platform', 'ergora.state'))
print(json.dumps(result), flush=True)
