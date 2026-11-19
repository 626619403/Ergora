"""Original owner for CPU-only local GPU admission tests.

This fixture's intent/authorization/attempt format is private to these tests.
The product guard receives live callbacks, never an authorization boolean.
"""

import argparse
import hashlib
import os
from pathlib import Path
import signal
import sys

from ergora.runtime import budget_clock
from ergora.runtime import gpu_guard as guard
from ergora.runtime import gpu_pool as pool
from ergora.runtime import processes


_SETUP_FIELDS = {'schema_version', 'pool_config', 'origin', 'command', 'device_uuids',
                 'source_refs', 'config_ref', 'guard_source_refs', 'intent_ref'}
_ORIGIN_FIELDS = {'kind', 'operation_id', 'attempt_ref', 'source_sha256', 'config_sha256',
                  'authorization_ref', 'clock', 'wall_seconds', 'cleanup_reserve_seconds'}
_INTENT_FIELDS = {'schema_version', 'kind', 'scope', 'operation_id', 'command_sha256',
                  'ordered_device_uuids', 'source_refs', 'config_ref', 'guard_source_refs',
                  'source_sha256', 'config_sha256'}
_AUTHORIZATION_FIELDS = {'schema_version', 'kind', 'scope', 'operation_id', 'intent_ref',
                         'command_sha256', 'clock', 'wall_seconds', 'cleanup_reserve_seconds'}
_ATTEMPT_FIELDS = {'schema_version', 'kind', 'scope', 'operation_id', 'attempt_id',
                   'intent_ref', 'authorization_ref'}


def _exact(value, fields, name):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('Invalid fixture ' + name + ' fields')


def _document(reference, fields, kind):
    if reference['semantic_sha256'] is None:
        raise ValueError('Fixture JSON needs both raw and semantic identity')
    path = guard._artifact(reference)
    raw = pool._read(path)
    value = pool._decode(raw)
    if (hashlib.sha256(raw).hexdigest() != reference['raw_sha256']
            or pool._sha(value) != reference['semantic_sha256']):
        raise ValueError('Fixture document changed during authority verification')
    _exact(value, fields, kind)
    if (type(value['schema_version']) is not int or value['schema_version'] != 1
            or value['kind'] != kind or value['scope'] != 'fixture-only'):
        raise ValueError('Unsupported fixture document or authorization scope')
    return path, value


def run(setup, signal_requested):
    _exact(setup, _SETUP_FIELDS, 'setup')
    if type(setup['schema_version']) is not int or setup['schema_version'] != 1:
        raise ValueError('Unsupported fixture setup')
    _exact(setup['origin'], _ORIGIN_FIELDS, 'origin')
    _exact(setup['command'], {'argv', 'cwd', 'env'}, 'command')
    origin = {**setup['origin'], 'owner_identity': processes.identity(os.getpid())}
    if (origin['kind'] != 'supervised-command-v1'
            or not isinstance(origin['operation_id'], str) or not origin['operation_id']
            or type(origin['wall_seconds']) is not int or origin['wall_seconds'] <= 0
            or type(origin['cleanup_reserve_seconds']) is not int
            or not 0 <= origin['cleanup_reserve_seconds'] < origin['wall_seconds']):
        raise ValueError('Invalid original fixture operation or budget')
    _exact(origin['clock'], set(budget_clock.FIELDS), 'clock')
    frozen_origin = pool._encode(origin)
    command = setup['command']
    devices = setup['device_uuids']
    if (not isinstance(devices, list) or not devices
            or any(not isinstance(item, str) or not item.startswith('GPU-') for item in devices)
            or len(devices) != len(set(devices))):
        raise ValueError('Fixture requires an ordered physical UUID subset')
    argv, cwd, environment = command['argv'], command['cwd'], command['env']
    if (not isinstance(argv, list) or len(argv) < 2
            or any(not isinstance(item, str) or '\0' in item for item in argv)
            or argv[0] != sys.executable
            or not isinstance(cwd, str) or not Path(cwd).is_absolute()
            or not isinstance(environment, dict)
            or any(not isinstance(key, str) or not key or '=' in key or '\0' in key
                   or not isinstance(value, str) or '\0' in value for key, value in environment.items())):
        raise ValueError('Fixture requires a literal Python payload and complete frozen environment')
    payload_command = {'argv': argv, 'cwd': cwd,
                       'env': {**environment, 'CUDA_VISIBLE_DEVICES': ','.join(devices)}}
    command_sha256 = pool._sha(payload_command)
    sources = setup['source_refs']
    if not isinstance(sources, list) or len(sources) != 2:
        raise ValueError('Fixture sources must be the owner followed by its payload')
    if (not isinstance(setup['guard_source_refs'], list) or not setup['guard_source_refs']
            or setup['config_ref']['semantic_sha256'] is None):
        raise ValueError('Fixture requires frozen guard sources and JSON config')
    intent_path = guard._artifact(setup['intent_ref'])
    directory = intent_path.parent
    if intent_path.name != 'intent.json':
        raise ValueError('Fixture intent must use its original intent.json path')

    def stop_requested():
        if signal_requested():
            return True
        try:
            pool._ordinary(directory)
            for name in ('stop.requested', 'authorization.revoked'):
                try:
                    (directory / name).lstat()
                except FileNotFoundError:
                    continue
                return True  # Any file type, including a dangling symlink, stops.
        except OSError:
            return True
        except ValueError:
            return True
        return False

    def authorize(original_origin):
        if (pool._encode(original_origin) != frozen_origin
                or processes.identity(os.getpid()) != original_origin['owner_identity']
                or stop_requested()):
            raise ValueError('Original fixture owner stopped or its identity changed')
        if pool._remaining(original_origin) <= 0:
            raise ValueError('Original fixture work budget expired')
        _, intent = _document(setup['intent_ref'], _INTENT_FIELDS, 'local-gpu-fixture-intent')
        authorization_path, authorization = _document(original_origin['authorization_ref'],
            _AUTHORIZATION_FIELDS, 'local-gpu-fixture-authorization')
        attempt_path, attempt = _document(original_origin['attempt_ref'],
            _ATTEMPT_FIELDS, 'local-gpu-fixture-attempt')
        if (authorization_path != directory / 'authorization.json'
                or attempt_path != directory / 'attempt.json'):
            raise ValueError('Fixture authority and attempt must be the original sibling records')
        if any(value['operation_id'] != original_origin['operation_id']
               for value in (intent, authorization, attempt)):
            raise ValueError('Fixture operation differs from its original records')
        if not isinstance(attempt['attempt_id'], str) or not attempt['attempt_id']:
            raise ValueError('Fixture attempt identity is required')
        if (authorization['intent_ref'] != setup['intent_ref']
                or attempt['intent_ref'] != setup['intent_ref']
                or attempt['authorization_ref'] != original_origin['authorization_ref']):
            raise ValueError('Fixture intent/authorization/attempt hash chain changed')
        if (intent['command_sha256'] != command_sha256
                or authorization['command_sha256'] != command_sha256
                or intent['ordered_device_uuids'] != devices):
            raise ValueError('Fixture command, environment or device order differs from authority')
        for field in ('clock', 'wall_seconds', 'cleanup_reserve_seconds'):
            if authorization[field] != original_origin[field]:
                raise ValueError('Fixture authority differs from the original budget')
        if (intent['source_refs'] != sources or intent['config_ref'] != setup['config_ref']
                or intent['guard_source_refs'] != setup['guard_source_refs']):
            raise ValueError('Fixture source/config references differ from intent')
        # Verify the actual referenced bytes on every callback before mapping
        # their identities to this owner's original source/config algorithm.
        source_paths = [guard._artifact(reference) for reference in sources]
        if (source_paths[0] != Path(__file__).absolute()
                or source_paths[1] != Path(argv[1]) or not Path(argv[1]).is_absolute()):
            raise ValueError('Fixture source bytes must include this owner and the actual payload')
        guard_paths = {guard._artifact(reference) for reference in setup['guard_source_refs']}
        if not {Path(guard.__file__).absolute(), Path(processes.__file__).absolute()}.issubset(guard_paths):
            raise ValueError('Fixture requires the actual installed guard and process implementation')
        guard._artifact(setup['config_ref'])
        source_sha256 = pool._sha(sources)
        config_sha256 = setup['config_ref']['semantic_sha256']
        if (original_origin['source_sha256'] != source_sha256 or intent['source_sha256'] != source_sha256
                or original_origin['config_sha256'] != config_sha256 or intent['config_sha256'] != config_sha256):
            raise ValueError('Fixture original source/config digest mapping changed')
        if stop_requested() or pool._remaining(original_origin) <= 0:
            raise ValueError('Fixture authority was revoked or its original budget expired')

    # Validate actual authority before even connecting to the resource owner.
    authorize(origin)
    return guard.run_owned_guard(pool.LocalGpuPool.connect(setup['pool_config']), origin,
        argv, Path(cwd), environment, device_uuids=devices, source_refs=sources,
        config_ref=setup['config_ref'], guard_source_refs=setup['guard_source_refs'],
        authorize=authorize, stop_requested=stop_requested)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Fixture-only original execution owner')
    parser.add_argument('--input', required=True)
    arguments = parser.parse_args(argv)
    stopped = False

    def signal_stop(signum, frame):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGINT, signal_stop)
    signal.signal(signal.SIGTERM, signal_stop)
    try:
        result = run(pool._decode(pool._read(Path(arguments.input))), lambda: stopped)
    except (KeyError, TypeError, ValueError, OSError, EOFError, RuntimeError) as error:
        print(pool._encode({'error': {'type': type(error).__name__, 'message': str(error)}}).decode())
        return 2
    print(pool._encode(result).decode())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
