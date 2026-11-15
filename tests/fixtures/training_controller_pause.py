"""Pause an actual publication or the original executor's locked callback."""

import os
from pathlib import Path
import time


def pause():
    marker = Path(os.environ['ERGORA_TEST_TRAINING_CONTROLLER_MARKER'])
    marker.touch()
    while not marker.with_suffix('.release').exists():
        time.sleep(.01)


def install():
    from ergora import training_execution_protocol as protocol

    boundary = os.environ['ERGORA_TEST_TRAINING_CONTROLLER_PAUSE']
    if boundary == 'executor-lock':
        from agent_platform import training_executor

        process = training_executor.process
        def locked_process(folder, *, admit):
            def locked_admit(job, record):
                pause()
                return admit(job, record)
            return process(folder, admit=locked_admit)
        training_executor.process = locked_process
    else:
        publish = protocol.publish
        def paused_publish(path, value, root):
            publish(path, value, root)
            if path.name == boundary + '.json':
                pause()
        protocol.publish = paused_publish
