"""Run actual reader/CPU/archive commands; replace only container and tracking leaves."""

import os
import subprocess


def install():
    from agent_platform import training_executor

    class LocalRunner:
        def run(self, name, checkout, output, command, **options):
            output.mkdir(parents=True, exist_ok=True)
            environment = dict(os.environ)
            if len(command) > 1 and command[1].endswith('/training/configuration.py'):
                for key in ('PYTHONPATH', 'AGENTFLOW_CONFIG_DIR', 'AGENTFLOW_STATE_DIR'):
                    environment.pop(key, None)
            with (output / 'execution.log').open('wb') as log:
                return subprocess.run(command, cwd=checkout, stdout=log, stderr=log,
                                      env=environment, timeout=options['timeout'], check=False).returncode

    training_executor.Sandbox = LocalRunner

    def track(*args):
        failure = os.environ.get('ERGORA_TEST_TRAINING_TRACKING_FAILURE')
        if failure == 'missing-module':
            raise ModuleNotFoundError("No module named 'mlflow'", name='mlflow')
        if failure == 'service':
            raise RuntimeError('Test tracking service unavailable after local archive')
        return 'test-only-tracking-leaf-not-a-service'

    training_executor.track = track
