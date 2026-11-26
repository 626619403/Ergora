"""One original execution owner and one dedicated, single-use local guardian.

The pool grants resources. Only the live owner's required callbacks authorize
execution; neither a JSON reference nor a resource grant substitutes for them.
"""

import argparse
from collections.abc import Callable
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import secrets
import select
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time

from ergora.runtime import gpu_pool as resources
from ergora.runtime import processes


_INPUT_FIELDS = {'schema_version', 'kind', 'session_id', 'origin', 'ordered_device_uuids',
                 'command', 'source_refs', 'config_ref', 'guard_source_refs', 'owner_identity', 'owner_nonce'}
_MESSAGE_FIELDS = {'schema_version', 'type', 'owner_nonce', 'sequence', 'owner_identity', 'guard_identity',
                   'input_sha256', 'origin_sha256', 'attempt_raw_sha256', 'budget_sha256', 'command_sha256', 'body'}
_LAUNCHER_REFUSALS = {
    'unavailable': 'Owned guard requires an executable in the actual command environment',
    'lookup_failed': 'Owned guard could not inspect the executable in the actual working directory',
}


class _LauncherPreflightError(ValueError):
    """The original guard refused the launcher before resource admission."""


def _now():
    return datetime.now(timezone.utc).isoformat()


def _exact(value, fields, name):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('Invalid ' + name + ' fields')


def _artifact(reference):
    _exact(reference, {'root', 'relative_path', 'raw_sha256', 'semantic_sha256'}, 'guard artifact')
    root = Path(reference['root'])
    relative = Path(reference['relative_path'])
    if not root.is_absolute() or not relative.parts or relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Guard artifacts need an explicit root and confined relative path')
    path = root / relative
    raw = resources._read(path)
    if hashlib.sha256(raw).hexdigest() != reference['raw_sha256']:
        raise ValueError('Original guard artifact bytes changed')
    if reference['semantic_sha256'] is not None and resources._sha(resources._decode(raw)) != reference['semantic_sha256']:
        raise ValueError('Original guard artifact semantic identity changed')
    return path


def _verify_input(value):
    _exact(value, _INPUT_FIELDS, 'owned guard input')
    if type(value['schema_version']) is not int or value['schema_version'] != 1 or value['kind'] != 'local-owned-guard-input':
        raise ValueError('Unsupported owned guard input')
    origin = value['origin']
    resources._origin(origin)
    if origin['kind'] != 'supervised-command-v1' or value['owner_identity'] != origin['owner_identity']:
        raise ValueError('Guard input differs from the original execution owner')
    resources._remaining(origin)
    _exact(value['command'], {'argv', 'cwd', 'env'}, 'guard command')
    command = value['command']
    if (not isinstance(command['argv'], list) or not command['argv']
            or any(not isinstance(arg, str) or '\0' in arg for arg in command['argv'])
            or not isinstance(command['env'], dict)
            or any(not isinstance(key, str) or not key or '=' in key or '\0' in key
                   or not isinstance(item, str) or '\0' in item for key, item in command['env'].items())):
        raise ValueError('Owned guard requires literal argv and a complete string environment')
    cwd = Path(command['cwd'])
    resources._ordinary(cwd)
    if not cwd.is_absolute() or not cwd.is_dir():
        raise ValueError('Owned guard requires an explicit local working directory')
    uuids = value['ordered_device_uuids']
    if (not isinstance(uuids, list) or not uuids or len(set(uuids)) != len(uuids)
            or any(not isinstance(item, str) or not item.startswith('GPU-') for item in uuids)
            or command['env'].get('CUDA_VISIBLE_DEVICES') != ','.join(uuids)):
        raise ValueError('Guard command must preserve the ordered physical UUID assignment')
    for field in ('source_refs', 'guard_source_refs'):
        if not isinstance(value[field], list) or not value[field]:
            raise ValueError('Guard requires frozen source references')
        for reference in value[field]:
            _artifact(reference)
    _artifact(value['config_ref'])
    _artifact(origin['attempt_ref'])
    _artifact(origin['authorization_ref'])
    guard_paths = {_artifact(reference) for reference in value['guard_source_refs']}
    if not {Path(__file__).absolute(), Path(processes.__file__).absolute()}.issubset(guard_paths):
        raise ValueError('Guard references must include this installed guard and process implementation')
    if not isinstance(value['owner_nonce'], str) or len(value['owner_nonce']) != 32:
        raise ValueError('Invalid original owner channel nonce')
    return value


def _bindings(value, guardian):
    origin = value['origin']
    return {'schema_version': 1, 'owner_nonce': value['owner_nonce'], 'owner_identity': value['owner_identity'],
            'guard_identity': guardian, 'input_sha256': resources._sha(value), 'origin_sha256': resources._sha(origin),
            'attempt_raw_sha256': origin['attempt_ref']['raw_sha256'],
            'budget_sha256': resources._sha({key: origin[key] for key in ('clock', 'wall_seconds', 'cleanup_reserve_seconds')}),
            'command_sha256': resources._sha(value['command'])}


def _message(binding, kind, sequence, body):
    return {**binding, 'type': kind, 'sequence': sequence, 'body': body}


def _verify_message(message, binding, kind, sequence):
    _exact(message, _MESSAGE_FIELDS, 'original owner channel message')
    if (type(message['schema_version']) is not int or type(message['sequence']) is not int
            or message['type'] != kind or message['sequence'] != sequence
            or any(message[key] != item for key, item in binding.items())):
        raise ValueError('Original owner channel identity, nonce or sequence changed')
    return message['body']


def _wire(connection, deadline, *, value=None):
    """Bound the entire frame, including short reads, to one absolute deadline."""
    def remaining():
        result = deadline - time.monotonic()
        if result <= 0:
            raise TimeoutError('Original owner channel deadline expired')
        connection.settimeout(result)

    if value is not None:
        raw = resources._encode(value)
        if not 0 < len(raw) <= resources.FRAME_LIMIT:
            raise ValueError('Original owner frame exceeds its capacity')
        remaining()
        connection.sendall(struct.pack('!I', len(raw)) + raw)
        return

    def exact(size):
        raw = bytearray()
        while len(raw) < size:
            remaining()
            chunk = connection.recv(size - len(raw))
            if not chunk:
                raise EOFError('Original execution owner channel closed')
            raw.extend(chunk)
        return bytes(raw)

    size, = struct.unpack('!I', exact(4))
    if not 0 < size <= resources.FRAME_LIMIT:
        raise ValueError('Invalid original owner frame size')
    return resources._decode(exact(size))


def _deadline(origin, *, cleanup=False):
    remaining = resources._remaining(origin, cleanup=cleanup)
    if remaining <= 0:
        raise TimeoutError('Original execution clock expired')
    return time.monotonic() + min(1.0, remaining)


def _launcher_refusal(command):
    # Resolve kernel aliases such as /proc/self/cwd in the eventual child cwd.
    # Restore the guard's original cwd before Popen interprets the same argument.
    try:
        original_cwd = os.open('.', os.O_PATH | os.O_DIRECTORY)
        try:
            os.chdir(command['cwd'])
            program = command['argv'][0]
            if os.path.dirname(program):
                return None if shutil.which(program) is not None else 'unavailable'
            for entry in os.get_exec_path(command['env']):
                if shutil.which(os.path.join(entry or '.', program)) is not None:
                    return None
            return 'unavailable'
        finally:
            try:
                os.fchdir(original_cwd)
            finally:
                os.close(original_cwd)
    except OSError:
        return 'lookup_failed'


def run_owned_guard(pool, origin, argv, cwd, env, *, device_uuids, source_refs, config_ref, guard_source_refs,
                    authorize: Callable[[dict], None], stop_requested: Callable[[], bool],
                    before_request: Callable[[dict, str, dict], None] | None = None) -> dict:
    """Run exactly one dedicated guard while serving the original owner's authority.

    Both callbacks are required and run in this calling process. They must be
    bounded and check the original authority, attempt, source/config and stop.
    A caller may durably associate the exact request and lease before admission.
    A returned resource release says nothing about training quality or gains.
    """
    if sys.platform != 'linux':
        raise ValueError('Owned local GPU guards require Linux')
    if not callable(authorize) or not callable(stop_requested):
        raise ValueError('Original owner authorization and stop callbacks are required')
    if before_request is not None and not callable(before_request):
        raise ValueError('Original lease publication must be a callback')
    owner = processes.identity(os.getpid())
    if origin['owner_identity'] != owner:
        raise ValueError('Owned guard must be called by the original execution owner')
    environment = dict(env, CUDA_VISIBLE_DEVICES=','.join(device_uuids))
    value = {'schema_version': 1, 'kind': 'local-owned-guard-input', 'session_id': pool.session['session_id'],
             'origin': origin, 'ordered_device_uuids': list(device_uuids),
             'command': {'argv': list(argv), 'cwd': str(cwd), 'env': environment},
             'source_refs': source_refs, 'config_ref': config_ref, 'guard_source_refs': guard_source_refs,
             'owner_identity': owner, 'owner_nonce': secrets.token_hex(16)}
    stopped = False

    def check():
        nonlocal stopped

        def original_stop():
            observation = stop_requested()
            if type(observation) is not bool:
                raise ValueError('Original owner stop callback must return a boolean')
            return observation

        try:
            _verify_input(value)
            if processes.identity(os.getpid()) != owner or stopped or original_stop() or resources._remaining(origin) <= 0:
                raise ValueError('Original execution owner stopped or expired')
            if authorize(origin) is not None:
                raise ValueError('Original owner authorization must return None or raise its refusal')
            if stopped or original_stop() or resources._remaining(origin) <= 0:
                raise ValueError('Original execution owner revoked or expired')
            return {'decision': 'permit', 'reason': None}
        except Exception as error:
            stopped = True
            return {'decision': 'stop', 'reason': type(error).__name__}

    initial = check()
    if initial['decision'] != 'permit':
        raise ValueError('Original owner refused guard before creation: ' + initial['reason'])
    parent, child = socket.socketpair()
    parent.set_inheritable(False)
    child.set_inheritable(False)
    process = None
    request = None
    guardian = None
    channel_error = None
    try:
        process = subprocess.Popen([sys.executable, '-m', 'ergora.runtime.gpu_guard', '--owner-fd', str(child.fileno()),
                                    '--config-json', resources._encode(pool.configuration).decode()],
                                   env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), pass_fds=(child.fileno(),),
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        child.close()
        guardian = processes.identity(process.pid)
        binding = _bindings(value, guardian)
        deadline = _deadline(origin)
        _wire(parent, deadline, value=_message(binding, 'BIND', 0, value))
        response = _wire(parent, deadline)
        if response.get('type') == 'LAUNCHER_REFUSED':
            refusal = _verify_message(response, binding, 'LAUNCHER_REFUSED', 0)
            _exact(refusal, {'reason'}, 'guard launcher refusal')
            reason = refusal['reason']
            if not isinstance(reason, str) or reason not in _LAUNCHER_REFUSALS:
                raise ValueError('Unknown original guard launcher refusal')
            raise _LauncherPreflightError(_LAUNCHER_REFUSALS[reason])
        ready = _verify_message(response, binding, 'READY', 0)
        _exact(ready, {'request_id', 'lease_id', 'ready_ref'}, 'guard ready response')
        expected = pool.request_identity(origin, list(device_uuids), guardian, binding['input_sha256'])
        if (ready['request_id'], ready['lease_id']) != expected:
            raise ValueError('Dedicated guardian returned another resource identity')
        decision = check()
        if decision['decision'] != 'permit':
            raise ValueError('Original owner refused resource admission after guard launcher preflight: ' + decision['reason'])
        selected = {'request_id': ready['request_id'], 'origin': origin,
                    'ordered_device_uuids': list(device_uuids), 'guard_ready_ref': ready['ready_ref']}
        if before_request is not None:
            before_request(selected, ready['lease_id'], guardian)
            decision = check()
            if decision['decision'] != 'permit':
                raise ValueError('Original owner refused resource request after lease publication: ' + decision['reason'])
        _wire(parent, _deadline(origin), value=_message(binding, 'SUBMITTING', 0, {}))
        acknowledged = _verify_message(_wire(parent, _deadline(origin)), binding, 'SUBMIT_ACK', 0)
        _exact(acknowledged, set(), 'guard resource submission acknowledgment')
        decision = check()
        if decision['decision'] != 'permit':
            _wire(parent, _deadline(origin, cleanup=True), value=_message(binding, 'ABORTED', 0, {}))
            raise ValueError('Original owner refused acknowledged resource submission: ' + decision['reason'])
        request = selected
        pool.request(request)
        _wire(parent, _deadline(origin), value=_message(binding, 'SUBMITTED', 0, {}))
        sequence = 1
        while process.poll() is None:
            try:
                if not select.select([parent], [], [], .2)[0]:
                    continue
                message = _wire(parent, time.monotonic() + 1.0)
                body = _verify_message(message, binding, 'CHECK', sequence)
                _exact(body, {'phase'}, 'original owner check')
                if body['phase'] not in ('pending', 'prelaunch', 'running'):
                    raise ValueError('Unknown original execution phase')
                decision = check()
                _wire(parent, time.monotonic() + 1.0, value=_message(binding, 'DECISION', sequence, decision))
                sequence += 1
            except KeyboardInterrupt:
                stopped = True
            except (EOFError, OSError, ValueError) as error:
                channel_error = type(error).__name__
                break
    except _LauncherPreflightError:
        raise
    except BaseException as error:
        stopped = True
        channel_error = type(error).__name__
        if process is None:
            raise
    finally:
        child.close()
        parent.close()  # EOF is an irreversible stop; no new guardian or attempt.
        if request is not None and stopped:
            try:
                pool.cancel(request['request_id'], origin)
            except (OSError, ValueError, EOFError):
                pass  # The original journal, not this failed reply, owns occupancy.
        if process is not None:
            # The guard alone reaps payload descendants. The owner only waits for
            # this actual child; it never releases from absence or signals siblings.
            process.wait()
    resource = None
    result = None
    if request is not None:
        try:
            resource = pool.reconcile(ready['lease_id'])
            proof = pool.proof_directory(ready['lease_id']) / 'stopped.json'
            if proof.exists():
                result = resources._decode(resources._read(proof))['process_result']
        except (OSError, ValueError, EOFError) as error:
            channel_error = channel_error or type(error).__name__
    return {'guard_identity': guardian, 'guard_returncode': process.returncode, 'request_id': request['request_id'] if request else None,
            'process_result': result, 'resource': resource, 'owner_channel_error': channel_error}


def _guard(connection, pool):
    """Dedicated child: prepare once, consume once, run once, then close spawning."""
    stopped = False

    def cancel(signum, frame):
        nonlocal stopped
        stopped = True
        processes.cancel_supervised()

    signal.signal(signal.SIGINT, cancel)
    signal.signal(signal.SIGTERM, cancel)
    guardian = processes.identity(os.getpid())
    message = _wire(connection, time.monotonic() + 1.0)
    value = _verify_input(message.get('body'))
    binding = _bindings(value, guardian)
    _verify_message(message, binding, 'BIND', 0)
    origin = value['origin']
    if (resources._peer(connection) != value['owner_identity'] or os.getppid() != value['owner_identity']['pid']
            or processes.identity(os.getppid()) != value['owner_identity'] or value['session_id'] != pool.session['session_id']):
        raise ValueError('Dedicated guard lost its original parent or pool session')
    processes.prepare_supervised()
    if resources._children(guardian):
        raise ValueError('Dedicated guard already owns children before admission')
    refusal = _launcher_refusal(value['command'])
    if stopped or resources._remaining(origin) <= 0:
        return 0
    if refusal is not None:
        _wire(connection, _deadline(origin), value=_message(binding, 'LAUNCHER_REFUSED', 0, {'reason': refusal}))
        return 1
    request_id, lease_id = pool.request_identity(origin, value['ordered_device_uuids'], guardian, binding['input_sha256'])
    directory = pool.proof_directory(lease_id)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    ready = {'schema_version': 1, 'kind': resources.READY_KIND, 'session_id': value['session_id'],
             'request_id': request_id, 'input_sha256': binding['input_sha256'], 'origin_sha256': binding['origin_sha256'],
             'command_sha256': binding['command_sha256'], 'ordered_device_uuids': value['ordered_device_uuids'],
             'owner_identity': value['owner_identity'], 'guard_identity': guardian,
             'guard_source_sha256': resources.guard_source_sha256(), 'prepared_subreaper': True, 'ready_at': _now()}
    raw = resources._publish(directory / 'ready.json', ready)
    ready_ref = {'relative_path': 'proofs/' + lease_id + '/ready.json', 'raw_sha256': hashlib.sha256(raw).hexdigest()}
    sequence = 1
    running = False

    def owner_check(phase):
        nonlocal stopped, sequence
        if stopped:
            return False
        try:
            _verify_input(value)
            if os.getppid() != value['owner_identity']['pid'] or processes.identity(os.getppid()) != value['owner_identity']:
                raise ValueError('Original execution owner exited')
            deadline = _deadline(origin)
            _wire(connection, deadline, value=_message(binding, 'CHECK', sequence, {'phase': phase}))
            decision = _verify_message(_wire(connection, deadline), binding, 'DECISION', sequence)
            sequence += 1
            _exact(decision, {'decision', 'reason'}, 'original owner decision')
            if decision['decision'] != 'permit' or stopped or resources._remaining(origin) <= 0:
                raise ValueError('Original execution owner refused work')
            return True
        except (OSError, ValueError, EOFError):
            stopped = True
            return False

    def exchange(channel, action, body):
        channel.settimeout(max(.001, min(1.0, resources._remaining(origin, cleanup=True))))
        resources._send(channel, {'protocol': resources.PROTOCOL, 'session_id': value['session_id'], 'action': action, 'body': body})
        reply = resources._receive(channel)
        if reply.get('session_id') != value['session_id']:
            raise ValueError('Resource reply lost its original session')
        return reply

    with pool.channel() as channel:
        registered = exchange(channel, 'guard_ready', {'request_id': request_id, 'ready_ref': ready_ref})
        if registered['status'] == 'rejected':
            raise ValueError('Pool rejected the dedicated guard')
        _wire(connection, _deadline(origin), value=_message(binding, 'READY', 0,
              {'request_id': request_id, 'lease_id': lease_id, 'ready_ref': ready_ref}))

        def read_submission(kinds, *, cleanup=False):
            message = _wire(connection, _deadline(origin, cleanup=cleanup))
            kind = message.get('type')
            if kind not in kinds:
                raise ValueError('Unexpected original resource submission progress')
            _exact(_verify_message(message, binding, kind, 0), set(), 'resource submission progress')
            return kind

        def await_submission(kinds):
            while not stopped and resources._remaining(origin) > 0:
                if select.select([connection], [], [], min(.05, max(0, resources._remaining(origin))))[0]:
                    return read_submission(kinds)
            return None

        try:
            if await_submission(('SUBMITTING',)) is None or stopped:
                return 0
            _wire(connection, _deadline(origin), value=_message(binding, 'SUBMIT_ACK', 0, {}))
        except (OSError, ValueError, EOFError):
            return 0  # The owner cannot submit without the complete acknowledgment.
        disposition = None
        try:
            disposition = await_submission(('SUBMITTED', 'ABORTED'))
        except (OSError, ValueError, EOFError):
            disposition = 'unknown'
        if disposition == 'ABORTED':
            return 0  # Only the original pre-send owner may establish this fact.
        if disposition != 'SUBMITTED':
            stopped = True
        consumed = None
        while owner_check('pending'):
            try:
                observation = exchange(channel, 'veto', {'request_id': request_id})
                if observation['status'] == 'granted':
                    consumed = exchange(channel, 'consume', {'request_id': request_id})
                    break
                if observation['status'] != 'pending' or observation.get('veto', False):
                    stopped = True
                    break
            except (OSError, ValueError, EOFError):
                # The consume may already be durable. This same live guard
                # closes spawning and uses original journal reconciliation.
                stopped = True
                break
            time.sleep(min(.2, max(0, resources._remaining(origin))))
        if consumed is not None and consumed['status'] != 'consumed':
            stopped = True

        def should_stop():
            nonlocal running, stopped
            if stopped:
                return True
            phase = 'running' if running else 'prelaunch'
            if not owner_check(phase):
                return True
            try:
                observation = exchange(channel, 'veto', {'request_id': request_id})
                if observation['status'] != 'consumed' or observation.get('veto', False):
                    stopped = True
                if resources._remaining(origin) <= 0 or processes.identity(origin['owner_identity']['pid']) != origin['owner_identity']:
                    stopped = True
            except (OSError, ValueError, EOFError):
                stopped = True
            running = True
            return stopped

        output = directory / 'command-output'
        if consumed is not None and consumed['status'] == 'consumed':
            try:
                result = processes.run(value['command']['argv'], Path(value['command']['cwd']), output,
                                       origin['wall_seconds'], env=value['command']['env'], supervised=True,
                                       stop_requested=should_stop)
            except OSError:
                # An exec error can escape after consume. Only this prepared
                # subreaper can establish that its process tree is now empty.
                if resources._children(guardian):
                    raise
                result = {'status': 'failed', 'returncode': None, 'output': str(output)}
        else:
            result = {'status': 'cancelled', 'returncode': None, 'output': str(output)}
        # Irreversible spawn closure. Only existing channels/file operations and
        # resource ACKs follow this point; no user code or subprocess may run.
        stopped = True
        observation = None
        while resources._remaining(origin, cleanup=True) > 0:
            if disposition is None and select.select([connection], [], [], 0)[0]:
                try:
                    disposition = read_submission(('SUBMITTED', 'ABORTED'), cleanup=True)
                except (OSError, ValueError, EOFError):
                    disposition = 'unknown'
                if disposition == 'ABORTED':
                    return 0
            try:
                if consumed is None:
                    pool.cancel(request_id, origin)
                current = pool.reconcile(lease_id)
                if current.get('request_id') == request_id and current.get('lease_id') == lease_id:
                    observation = current
                    break
            except (OSError, ValueError, EOFError):
                pass
            # An absent snapshot cannot dispose of an acknowledged in-flight request.
            time.sleep(min(.2, max(0, resources._remaining(origin, cleanup=True))))
        if observation is None:
            return 1
        if observation['status'] in ('pending', 'cancelled', 'expired', 'rejected'):
            return 0 if observation['status'] != 'pending' else 1
        if observation['status'] == 'released':
            return 0
        stopped_proof = {'schema_version': 1, 'kind': resources.STOPPED_KIND, 'session_id': value['session_id'],
                         'lease_id': lease_id, 'request_sha256': observation['request_sha256'],
                         'consume_binding_sha256': observation['consume_binding_sha256'], 'guard_identity': guardian,
                         'origin_sha256': binding['origin_sha256'], 'process_result': result,
                         'reaped_at': _now(), 'spawn_closed': True}
        raw = resources._publish(directory / 'stopped.json', stopped_proof)
        proof_ref = {'relative_path': 'proofs/' + lease_id + '/stopped.json', 'raw_sha256': hashlib.sha256(raw).hexdigest()}
        original_channel = True
        while resources._remaining(origin, cleanup=True) > 0:
            try:
                if original_channel:
                    response = exchange(channel, 'stopped', {'lease_id': lease_id, 'proof_ref': proof_ref})
                else:
                    with pool.channel() as replacement:
                        registration = exchange(replacement, 'guard_ready', {'request_id': request_id, 'ready_ref': ready_ref})
                        if registration['status'] in ('rejected', 'unavailable'):
                            raise ValueError('Original guard reconnect unavailable')
                        response = exchange(replacement, 'stopped', {'lease_id': lease_id, 'proof_ref': proof_ref})
                if response['status'] == 'released':
                    return 0
                if response['status'] == 'rejected':
                    return 1
            except (OSError, ValueError, EOFError):
                # Only the same live, spawn-closed guardian may reconnect. A
                # lost resource ACK never opens another execution opportunity.
                channel.close()
                original_channel = False
            time.sleep(min(.2, max(0, resources._remaining(origin, cleanup=True))))
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description='Dedicated local guard; requires its live original owner channel')
    parser.add_argument('--owner-fd', type=int, required=True)
    parser.add_argument('--config-json', required=True)
    args = parser.parse_args(argv)
    with socket.socket(fileno=args.owner_fd) as connection:
        connection.set_inheritable(False)
        return _guard(connection, resources.LocalGpuPool.connect(resources._decode(args.config_json.encode())))


if __name__ == '__main__':
    raise SystemExit(main())
