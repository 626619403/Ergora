"""Interrupt actual publications or fail the original intent's durable confirmation."""

import json
import os
from pathlib import Path

from agent_platform import core
from ergora import training_materials


state = Path(os.environ['AGENTFLOW_STATE_DIR'])
ident = os.environ['ERGORA_TEST_PREPARATION_ID']
intent = state / f'ergora/training-preparations/{ident}.intent.json'
targets = [intent, state / f'training/manifests/{ident}.json',
           state / f'training/projects/demo/perf/experiments/{ident}/manifest.json',
           state / f'training/specs/{ident}.json',
           state / f'training/configurations/{ident}/baseline.json',
           state / f'training/configurations/{ident}/candidate.json']
stop = int(os.environ.get('ERGORA_TEST_PREPARATION_STOP_AFTER', '-1'))
failure = os.environ.get('ERGORA_TEST_PREPARATION_SYNC_FAILURE')
trace = os.environ.get('ERGORA_TEST_PREPARATION_TRACE')


def record(event, path):
    if trace:
        with Path(trace).open('a') as stream:
            stream.write(json.dumps({'event': event, 'path': str(path)}) + '\n')


def published(path):
    if stop >= 0 and Path(path) == targets[stop]:
        os._exit(73)


original_write = core.write


def write(path, value, **kwargs):
    if Path(path) in targets[1:]:
        record('native-output-call', path)
    original_write(path, value, **kwargs)
    published(path)


original_material = training_materials.publish_material


def publish_material(path, raw, root):
    if Path(path) in targets[1:]:
        record('native-output-call', path)
    original_material(path, raw, root)
    published(path)


original_sync = os.fsync
original_open = os.open
root_synchronized = False


def open_file(path, flags, *args, **kwargs):
    global root_synchronized
    if failure == 'readback-open-inode' and root_synchronized and Path(path) == intent:
        root_synchronized = False
        replacement = intent.with_suffix('.replacement')
        replacement.write_bytes(intent.read_bytes())
        replacement.replace(intent)
        record('readback-inode-exchanged', intent)
    return original_open(path, flags, *args, **kwargs)


def synchronize(descriptor):
    global root_synchronized
    path = Path('/proc/self/fd/' + str(descriptor)).resolve()
    selected = {'file': intent, 'parent': intent.parent, 'ancestor': state / 'ergora',
                'root': state}.get(failure)
    if intent.exists() and path == selected:
        record('sync-failed', path)
        raise OSError('Controlled original intent synchronization failure: ' + failure)
    result = original_sync(descriptor)
    if intent.exists() and path == state:
        root_synchronized = True
    if failure == 'readback-inode' and intent.exists() and path == state:
        # Preserve the exact bytes while exchanging the pathname's inode after
        # syncing its chain. A semantic JSON comparison cannot detect this.
        replacement = intent.with_suffix('.replacement')
        replacement.write_bytes(intent.read_bytes())
        replacement.replace(intent)
        record('inode-exchanged', intent)
    return result


core.write = write
training_materials.publish_material = publish_material
os.fsync = synchronize
os.open = open_file
from ergora.reference_training_preparation import main

main()
