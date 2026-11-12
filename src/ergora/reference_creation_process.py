"""Dedicated native creation process, shared by application and executor callers."""

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import uuid


_REFERENCE = Path(__file__).parent / 'data/reference'


def task_preparation(project: dict, home: Path, operation: str, payload: dict) -> dict:
    """Observe a dedicated budget owner without killing its safety cleanup.

    The observation timeout is not an execution grant. If the owner has not
    returned, keep its private files and let preparation status reconcile it.
    """
    if sys.platform != 'linux':
        raise ValueError('Budgeted native preparation requires Linux; use WSL2')
    output = home / 'operations' / 'task-preparations' / uuid.uuid4().hex
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    execution = project['registration']['definition']['execution']
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=str(output / 'compile'))
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        Path(__file__).parent.parent, _REFERENCE / 'platform/local', _REFERENCE / 'platform/upstream/platform')))
    request = {'project': project, 'control_home': str(home), 'operation': operation,
               'budgeted': True, **payload}
    (output / 'request.json').write_text(json.dumps(request, allow_nan=False), encoding='utf-8')
    with (output / 'request.json').open('rb') as stdin, (output / 'stdout.json').open('xb') as stdout, (output / 'stderr.txt').open('xb') as stderr:
        process = subprocess.Popen([sys.executable, '-P', '-S', '-c',
                                    'from ergora.reference_task_creation import main;main()'],
                                   stdin=stdin, stdout=stdout, stderr=stderr, env=environment,
                                   start_new_session=True)
        (output / 'pid.json').write_text(json.dumps({'pid': process.pid}), encoding='utf-8')
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            return {'status': 'unknown', 'operation': operation, 'operation_directory': str(output),
                    'runtime_status': 'not_queried', 'execution_started_by_operation': False,
                    'detail': 'Observation ended; the original owner may still be collecting or cleaning up. '
                              'Inspect preparation and keep the original task ID; no new budget was granted.'}
    if process.returncode:
        lines = (output / 'stderr.txt').read_text(encoding='utf-8').strip().splitlines()
        raise ValueError(lines[-1] if lines else 'Budget preparation owner exited without a result; inspect preparation')
    return json.loads((output / 'stdout.json').read_bytes())


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
