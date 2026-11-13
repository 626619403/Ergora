"""Stop the real preparation subprocess immediately after one original atomic write."""

import os
from pathlib import Path

from agent_platform import core


original = core.write
state = Path(os.environ['AGENTFLOW_STATE_DIR'])
ident = os.environ['ERGORA_TEST_PREPARATION_ID']
targets = [state / f'ergora/training-preparations/{ident}.intent.json',
           state / f'training/manifests/{ident}.json',
           state / f'training/projects/demo/perf/experiments/{ident}/manifest.json',
           state / f'training/specs/{ident}.json']
stop = int(os.environ['ERGORA_TEST_PREPARATION_STOP_AFTER'])


def write(path, value, **kwargs):
    original(path, value, **kwargs)
    if Path(path) == targets[stop]:
        os._exit(73)


core.write = write
from ergora.reference_training_preparation import main

main()
