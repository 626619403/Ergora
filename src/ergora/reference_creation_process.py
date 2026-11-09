"""Dedicated native creation process, shared by application and executor callers."""

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


_REFERENCE = Path(__file__).parent / 'data/reference'


def task_creation(project: dict, home: Path, operation: str, payload: dict) -> dict:
    """Isolate native compilation and recoverable file publication from application globals."""
    execution = project['registration']['definition']['execution']
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        Path(__file__).parent.parent, _REFERENCE / 'platform/local', _REFERENCE / 'platform/upstream/platform')))
    try:
        # The caller owns temporary storage so timeout/forced child termination
        # still removes compiled materials after subprocess.run reaps the child.
        with TemporaryDirectory(prefix='ergora-task-compile-') as directory:
            environment['AGENTFLOW_STATE_DIR'] = directory
            result = subprocess.run([sys.executable, '-P', '-S', '-c',
                                     'from ergora.reference_task_creation import main;main()'],
                                    input=json.dumps({'project': project, 'control_home': str(home),
                                                      'operation': operation, **payload}, allow_nan=False),
                                    capture_output=True, text=True, encoding='utf-8', env=environment, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise ValueError('Task creation timed out; inspect task creation status and resume the original intent') from error
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        raise ValueError(lines[-1] if lines else f'Task creation process exited with status {result.returncode}; inspect creation status')
    return json.loads(result.stdout)
