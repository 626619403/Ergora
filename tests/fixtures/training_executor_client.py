"""Real native locking and execution; substitute only sandbox/tracking leaves."""

import json
import os
from pathlib import Path
import subprocess
import sys

mode, folder = sys.argv[1], Path(sys.argv[2])


if mode in ('native-context', 'native-context-isolated'):
    if mode == 'native-context-isolated':
        class WithoutApplication:
            def find_spec(self, fullname, path=None, target=None):
                if fullname.split('.')[0] in ('yaml', 'jsonschema', 'temporalio') or fullname in (
                        'ergora.state', 'ergora.training_rounds', 'ergora.registrations'):
                    raise AssertionError('Native callback imported application or SDK: ' + fullname)
        sys.meta_path.insert(0, WithoutApplication())
    from ergora.reference_training_execution import native_main
    from agent_platform import core
    try:
        native_main(str(core.ROOT))
    except ValueError as error:
        print(json.dumps({'error_type': type(error).__name__, 'error': str(error)}), flush=True)
    sys.exit(0)

from agent_platform import training_executor as executor
from agent_platform.core import Blocked


def admit(job, record):
    if mode == 'hold-admission':
        print(json.dumps({'admitted': record, 'folder': str(job)}), flush=True)
        sys.stdin.readline()
        raise Blocked('Admission declined before business execution')
    raise AssertionError('Admission must not be called for an uncertain or completed job')


if mode == 'prechecked':
    assert not (folder / 'started.json').exists()
    print('prechecked', flush=True)
    sys.stdin.readline()
if mode == 'manual-crash':
    # Native process writes started and holds its real lock before the first Git leaf.
    executor.git = lambda *args, **kwargs: os._exit(73)
if mode == 'run-clean':
    class LocalRunner:
        def run(self, name, checkout, output, command, **kwargs):
            output.mkdir(parents=True)
            with (output / 'execution.log').open('wb') as log:
                return subprocess.run(command, cwd=checkout, stdout=log, stderr=log, timeout=10).returncode

    executor.Sandbox = LocalRunner
    executor.track = lambda *args: 'synthetic-protocol-only-no-tracking'
try:
    if mode in ('prechecked', 'hold-admission', 'completed'):
        value = executor.process(folder, admit=admit)
    else:
        value = executor.process(folder)
    print(json.dumps({'result': value}), flush=True)
except (Blocked, BlockingIOError) as error:
    print(json.dumps({'error_type': type(error).__name__, 'error': str(error)}), flush=True)
