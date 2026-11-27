"""Run actual reader/CPU/archive commands; replace only container and tracking leaves."""

import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
from types import ModuleType, SimpleNamespace


def install():
    from agent_platform import training_executor
    from agent_platform.core import Blocked

    class LocalRunner:
        def run(self, name, checkout, output, command, **options):
            output.mkdir(parents=True, exist_ok=True)
            environment = dict(os.environ)
            if len(command) > 1 and command[1].endswith('/training/configuration.py'):
                for key in ('PYTHONPATH', 'AGENTFLOW_CONFIG_DIR', 'AGENTFLOW_STATE_DIR'):
                    environment.pop(key, None)
            sync_mode = environment.get('ERGORA_TEST_PRIMARY_SYNC') if name.endswith('-archive') else None
            if sync_mode:
                environment['ERGORA_TEST_PRIMARY_SYNC_LOG'] = str(output.parent / 'test-primary-sync.jsonl')
                command = [command[0], str(Path(__file__).resolve()), *command[1:]]
                if sync_mode == 'timeout':
                    command = ['/usr/bin/timeout', '--kill-after=1', '3', *command]
            timeout = options['timeout']
            if environment.get('ERGORA_TEST_GUARDED_TRAINING') == '1':
                command = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=5', str(timeout), *command]
                timeout += 7
            with (output / 'execution.log').open('wb') as log:
                result = subprocess.run(command, cwd=checkout, stdout=log, stderr=log,
                                        env=environment, timeout=timeout, check=False)
            if sync_mode == 'monitor':
                raise Blocked('Original process started without a confirmed terminal')
            return result.returncode

    training_executor.Sandbox = LocalRunner

    original_track = training_executor.track

    def track(*args):
        failure = os.environ.get('ERGORA_TEST_TRAINING_TRACKING_FAILURE')
        if os.environ.get('ERGORA_TEST_PRIMARY_SYNC'):
            _, folder, _, gate = args
            with (folder / 'test-primary-sync.jsonl').open('a') as stream:
                stream.write(json.dumps({'operation': 'tracking', 'path': gate['archive_report']['archive_path']
                                         if gate['passed'] else None}) + '\n')
        if failure == 'missing-module':
            sys.modules['mlflow'] = None
            return original_track(*args)
        if failure == 'service':
            raise RuntimeError('Test tracking service unavailable after local archive')
        if failure in ('lost-after-send', 'existing-run'):
            _, folder, _, _ = args

            class TrackingClient:
                def __init__(self, *, tracking_uri):
                    assert tracking_uri == 'http://127.0.0.1:5000'

                def get_experiment_by_name(self, name):
                    return SimpleNamespace(experiment_id='isolated-tracking')

                def search_runs(self, *args, **kwargs):
                    assert kwargs['run_view_type'] == 3  # MLflow ViewType.ALL
                    if failure == 'existing-run':
                        return [SimpleNamespace(info=SimpleNamespace(run_id='original-private-run'))]
                    return []

                def create_run(self, experiment_id, *, tags):
                    checkpoint = folder / 'managed-execution/tracking-attempt.json'
                    assert checkpoint.is_file()
                    with (folder / 'test-tracking-send').open('xb') as marker:
                        marker.write(tags['manifest_sha'].encode('ascii'))
                    os._exit(79)

            mlflow = ModuleType('mlflow')
            mlflow.MlflowClient = TrackingClient
            sys.modules['mlflow'] = mlflow
            entities = ModuleType('mlflow.entities')
            entities.ViewType = SimpleNamespace(ALL=3)
            sys.modules['mlflow.entities'] = entities
            return original_track(*args)
        return 'test-only-tracking-leaf-not-a-service'

    training_executor.track = track


if __name__ == '__main__':
    mode = os.environ['ERGORA_TEST_PRIMARY_SYNC']
    log = Path(os.environ['ERGORA_TEST_PRIMARY_SYNC_LOG'])
    fsync, rename = os.fsync, os.rename
    published = False

    def observe(operation, path):
        with log.open('a') as stream:
            stream.write(json.dumps({'operation': operation, 'path': str(path)}) + '\n')

    def sync(fd):
        path = Path(os.readlink(f'/proc/self/fd/{fd}'))
        if published and path.name == 'accepted-evidence' and mode in ('timeout', 'signal'):
            observe('sync-held', path)
            if mode == 'signal':
                os.kill(os.getpid(), signal.SIGTERM)
            signal.pause()
        if (mode == 'artifact' and path.name == '0-baseline.json'
                or mode == 'parent' and published and path.name == 'accepted-evidence'):
            observe('sync-failed', path)
            raise OSError('Controlled archive sync failed for ' + str(path))
        fsync(fd)
        observe('sync', path)

    def publish(source, target):
        global published
        rename(source, target)
        published = True
        observe('rename', target)

    os.fsync, os.rename = sync, publish
    sys.argv = sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name='__main__')
