"""Deliver one original fixed-check notice through a newly owned Codex App Server."""

from collections import deque
import hashlib
import json
import os
from pathlib import Path
import selectors
from threading import Thread
import time
from urllib.parse import urlsplit
import uuid

from ergora.agents import native_sources
from ergora.campaigns.records import PENDING_JOB_STATES, original_check_evidence
from ergora.definitions.bundles import parse_json
from ergora.development import application, verification
from ergora.runtime import processes
from ergora.storage.state import file_lock
from ergora.training.materials import read_raw


_VERSION = 'codex-cli 0.172.0'
_MAX_WIRE = 32 * 1024 * 1024


def read_locator(path):
    raw = read_raw(path.expanduser().absolute(), 4096)
    return verification.validate_fixed_check_locator(parse_json(raw.decode('utf-8-sig'), 'Fixed-check locator', finite=True))


def _provider(configuration):
    overrides = {}
    arguments = configuration['arguments']
    for flag, option in zip(arguments, arguments[1:]):
        if flag == '-c':
            key, value = option.split('=', 1)
            overrides[key] = json.loads(value)
    provider = overrides.get('model_provider')
    prefix = f'model_providers.{provider}.'
    url = urlsplit(overrides.get(prefix + 'base_url', ''))
    if (not isinstance(provider, str) or not url.hostname or url.scheme not in ('http', 'https')
            or url.username or url.password or url.query or url.fragment
            or overrides.get(prefix + 'wire_api') != 'responses'
            or overrides.get(prefix + 'requires_openai_auth') is not False):
        raise ValueError('Active fixed-check delivery requires an explicit frozen Responses provider without stored login')
    credentials = {value for key, value in overrides.items()
                   if key == prefix + 'env_key' or key.startswith(prefix + 'env_http_headers.')}
    if any(not isinstance(name, str) or not name.isidentifier()
           or name in {'HOME', 'PATH', 'TMPDIR', 'LANG', 'ENV', 'BASH_ENV', 'OPENAI_BASE_URL'}
           or name.startswith(('CODEX_', 'LD_', 'DYLD_', 'PYTHON', 'NODE_', 'GIT_', 'LC_', 'RUST_'))
           for name in credentials):
        raise ValueError('Active provider environment references cannot change the App Server execution environment')
    return provider, credentials


def command(configuration):
    if (configuration['binding']['tool'] != 'codex' or configuration['version'] != _VERSION
            or configuration['sandbox'] != 'read-only'):
        raise ValueError('Active fixed-check delivery requires read-only Codex App Server 0.172.0')
    _provider(configuration)
    executable = configuration['executable']
    if Path(executable).name == 'codex.js':
        executable, = (file for file in configuration['executable_files'] if Path(file).name == 'codex')
    # App Server lacks exec's ignore flags. The original native home is private and newly created.
    options = [option for option in configuration['arguments'] if option not in ('--ignore-user-config', '--ignore-rules')]
    return [executable, *options, '-c', 'approval_policy="never"', '-c', 'sandbox_mode="read-only"',
            '-c', 'web_search="disabled"',
            '-c', 'project_doc_max_bytes=0', '-c', 'agents.enabled=false', '-c', 'features.view_image=false',
            '--disable', 'shell_tool', '--disable', 'hooks', '--disable', 'apps', '--disable', 'plugins',
            '--disable', 'goals', '--disable', 'memories', '--disable', 'multi_agent_v2',
            'app-server', '--listen', 'stdio://']


class _Ended(Exception):
    pass


class _Stdio:
    def __init__(self, proc, log, guard):
        self.proc, self.log, self.guard = proc, log, guard
        self.in_fd, self.out_fd = proc.stdin.fileno(), proc.stdout.fileno()
        os.set_blocking(self.in_fd, False)
        self.pending = bytearray()
        self.received = 0
        self.request_id = 0
        self.notifications = deque()

    def _wait(self, fd, event, *, until=None):
        with selectors.DefaultSelector() as ready:
            ready.register(fd, event)
            while True:
                self.guard()
                if until is not None and time.monotonic() >= until:
                    return False
                if ready.select(.05):
                    return True

    def _request(self, method, params):
        self.request_id += 1
        return {'id': self.request_id, 'method': method, 'params': params}

    def send(self, message, *, once=False):
        raw = native_sources.encode(message) + b'\n'
        self.guard()
        if once:
            if len(raw) > os.fpathconf(self.in_fd, 'PC_PIPE_BUF'):
                raise ValueError('Selected notification exceeds the atomic pipe write')
            if os.write(self.in_fd, raw) != len(raw):
                raise OSError('Active notification transport wrote an incomplete frame')
            return
        pending = memoryview(raw)
        while pending:
            self._wait(self.in_fd, selectors.EVENT_WRITE)
            try:
                pending = pending[os.write(self.in_fd, pending):]
            except BlockingIOError:
                continue

    def read(self, *, until=None):
        self.guard()
        if self.notifications:
            return self.notifications.popleft()
        return self._receive(until=until)

    def _receive(self, *, until=None, redacted_id=None):
        self.guard()
        while (boundary := self.pending.find(b'\n')) < 0:
            if not self._wait(self.out_fd, selectors.EVENT_READ, until=until):
                return None
            raw = os.read(self.out_fd, 65536)
            if not raw:
                raise _Ended('Original App Server stdio closed')
            self.received += len(raw)
            if self.received > _MAX_WIRE:
                raise ValueError('Complete original App Server stream exceeds its byte limit')
            self.pending.extend(raw)
        raw = bytes(self.pending[:boundary]).decode('utf-8')
        del self.pending[:boundary + 1]
        message = parse_json(raw, 'Original App Server frame', finite=True, bounded=True)
        if not isinstance(message, dict) or ('method' in message and 'id' in message):
            raise ValueError('Unsupported App Server message or interactive request')
        if redacted_id is not None and message.get('id') == redacted_id:
            self.log.write(json.dumps({'id': redacted_id, 'config_read_redacted': True}) + '\n')
        else:
            self.log.write(raw + '\n')
        self.log.flush()
        return message

    def call(self, method, params, *, redact=False):
        request = self._request(method, params)
        self.send(request)
        while True:
            message = self._receive(redacted_id=request['id'] if redact else None)
            if 'id' in message:
                if message['id'] != request['id'] or 'result' not in message:
                    raise ValueError(f'Original App Server rejected or invalidated {method}')
                return message['result']
            self.notifications.append(message)


def _scope(state, document, locator):
    key = native_sources.sha({'project': document['project'], 'role': document['role'], 'source': locator})
    return state.root / 'runs' / ('active-fixed-check-' + key)


def _optional(path):
    try:
        return native_sources.packet(path, confirm_durable=True)
    except FileNotFoundError:
        return None


def _identity(value):
    return str(uuid.UUID(value))


def _turn_event(message, method, original):
    params = message.get('params', {})
    if (message.get('method') == method and params.get('threadId') == original['thread_id']
            and params.get('turn', {}).get('id') == original['turn_id']):
        return params['turn']
    return None


def _exact_item(item, client_id, text, *, cold=False):
    kind, key = ('UserMessage', 'client_id') if cold else ('userMessage', 'clientId')
    content = item.get('content')
    return (item.get('type') == kind and item.get(key) == client_id and isinstance(content, list)
            and len(content) == 1 and isinstance(content[0], dict)
            and content[0].get('type') == 'text' and content[0].get('text') == text)


def _notice(locator, evidence, job):
    return 'Original fixed check passed with confirmed cleanup. ' + native_sources.encode({
        'fixed_check': locator, 'observation_sha256': evidence, **job,
    }).decode('utf-8')


def _save(publish, folder, record, guard):
    raw = native_sources.encode(record)
    errors = []

    def persist():
        try:
            publish(folder, {'record.json': raw})
        except (OSError, ValueError) as error:
            errors.append(error)

    guard()
    writer = Thread(target=persist, daemon=True)
    writer.start()
    while writer.is_alive():
        guard()
        writer.join(timeout=.05)
    guard()
    if errors:
        raise errors[0]


def _observe(state, document, locator, deadline, should_stop):
    observation = application.candidate_check_status(state, document['project'], locator['operation_id'],
        job_sha256=locator['job_sha256'], verify_pending=True, deadline=deadline, stop_requested=should_stop)
    source = {**locator, 'project_revision': document['project_revision'], 'pending': True}
    evidence, job = original_check_evidence({'project': document['project']}, {'source': source}, observation)
    return observation, evidence, job


def run(state, document, request, context, environment, inherited, remaining, *, should_stop, check_authority, publish):
    """Drive one original process. The inherited native supervisor remains the sole reaper."""
    folder = native_sources.turn_folder(state, document['id'])
    configuration = context['inference']
    locator = request['submitted']['active_fixed_check']
    scope = _scope(state, document, locator)
    home, cwd = Path(context['native_home']), Path(context['repo'])
    output = state.root / 'runs' / document['id']
    deadline = time.monotonic() + remaining
    request_sha = document['request_sha256']
    argv = command(configuration)
    provider, credentials = _provider(configuration)
    executable = Path(argv[0]).stat()

    def guard():
        if should_stop() or time.monotonic() >= deadline:
            raise _Ended('Original session STOP or deadline')

    try:
        if _optional(scope) is not None:
            return {'status': 'failed', 'error': 'Original fixed-check notice already has a send attempt'}
        initial, _, job = _observe(state, document, locator, deadline, should_stop)
        _save(publish, folder / 'active-source', {'request_sha256': request_sha, 'observation': initial}, guard)
        if job['status'] not in PENDING_JOB_STATES:
            return {'status': 'failed', 'error': 'Original fixed-check must be pending at App Server preflight'}
    except (_Ended, OSError, ValueError) as error:
        return {'status': 'cancelled' if should_stop() else 'failed', 'error': str(error)}

    outcome = {}
    final_text = None

    def exchange(proc, log):
        nonlocal final_text
        wire = _Stdio(proc, log, guard)
        try:
            actual = Path(f'/proc/{proc.pid}/exe').stat()
            if (actual.st_dev, actual.st_ino) != (executable.st_dev, executable.st_ino):
                raise ValueError('Original App Server child does not match its pinned executable')
            initialized = wire.call('initialize', {'clientInfo': {'name': 'ergora-active-fixed-check', 'version': '1'},
                                                   'capabilities': {'experimentalApi': False}})
            if initialized.get('codexHome') != str(home):
                raise ValueError('App Server did not bind this original native home')
            wire.send({'method': 'initialized'})
            effective = wire.call('config/read', {'cwd': str(cwd), 'includeLayers': False}, redact=True)
            settings, origins = effective['config'], effective['origins']
            if (settings.get('mcp_servers') or settings.get('tools') or settings.get('browser_use')
                    or settings.get('computer_use') or settings.get('sandbox_mode') != 'read-only'
                    or settings.get('approval_policy') != 'never' or settings.get('model_provider') != provider
                    or any(key.startswith(('mcp_servers.', 'tools.')) for key in origins)):
                raise ValueError('App Server effective policy differs from the read-only no-MCP role')
            selected = wire.call('thread/start', {'approvalPolicy': 'never', 'sandbox': 'read-only', 'cwd': str(cwd),
                'model': configuration['binding']['model'], 'ephemeral': False})
            thread = selected['thread']
            rollout = Path(thread['path']).resolve()
            if (thread['cwd'] != str(cwd) or selected['model'] != configuration['binding']['model']
                    or selected['modelProvider'] != provider
                    or not rollout.is_relative_to(home)):
                raise ValueError('App Server thread is outside its original workspace or home')
            thread_id = _identity(thread['id'])
            first = wire.call('turn/start', {'threadId': thread_id,
                                             'input': [{'type': 'text', 'text': request['prompt']}]})['turn']
            if first.get('status') != 'inProgress':
                raise ValueError('App Server did not start the selected original turn')
            original = {'thread_id': thread_id, 'turn_id': _identity(first['id']), 'rollout': str(rollout.relative_to(home)),
                        'request_sha256': request_sha, 'app_server': processes.identity(proc.pid),
                        'executable_sha256': configuration['executable_files'][str(Path(argv[0]).resolve())]}
            outcome['native_session'] = {'id': thread_id, 'completed': False, 'observed_in_turn': True, 'usage': None}
            while _turn_event(wire.read(), 'turn/started', original) is None:
                pass
            _save(publish, folder / 'active-owner', original, guard)

            steer = None
            next_read = 0.0
            while True:
                message = wire.read(until=next_read if steer is None else None)
                if message is None:
                    observation, evidence, job = _observe(state, document, locator, deadline, should_stop)
                    if job['status'] != 'succeeded':
                        next_read = time.monotonic() + .2
                        continue
                    payload = _notice(locator, evidence, job)
                    client_id = str(uuid.uuid5(uuid.NAMESPACE_URL, 'ergora:active-fixed-check:' + request_sha))
                    steer = wire._request('turn/steer', {'threadId': original['thread_id'],
                        'expectedTurnId': original['turn_id'], 'clientUserMessageId': client_id,
                        'input': [{'type': 'text', 'text': payload}]})
                    intent = {'owner': original, 'source': observation, 'frame': steer}
                    _save(publish, folder / 'active-intent', intent, guard)
                    try:
                        _save(publish, scope, {'run_id': document['id'], 'intent_sha256': native_sources.sha(intent),
                            'frame_sha256': native_sources.sha(steer)}, guard)
                    except FileExistsError:
                        outcome['error'] = 'Original fixed-check notice already has a send attempt'
                        break
                    if check_authority()['revision'] != document['project_revision']:
                        raise ValueError('Original project revision changed before active delivery')
                    # Only the final STOP probe and one bounded pipe write share the STOP lock.
                    with file_lock(folder / 'active-send.lock', blocking=False):
                        wire.send(steer, once=True)
                    continue
                if steer is not None and message.get('id') == steer['id']:
                    if message.get('result') == {'turnId': original['turn_id']}:
                        _save(publish, folder / 'active-ack',
                              {'frame_sha256': native_sources.sha(steer), 'response': message}, guard)
                    elif 'error' not in message:
                        raise ValueError('Active notice RPC response differs from the selected original turn')
                    continue
                event = message.get('params', {})
                if (steer is not None and message.get('method') == 'item/completed'
                        and event.get('threadId') == original['thread_id'] and event.get('turnId') == original['turn_id']
                        and _exact_item(event.get('item', {}), client_id, payload)):
                    observed = {'frame_sha256': native_sources.sha(steer), 'item_id': _identity(event['item']['id'])}
                    _save(publish, folder / 'active-item', observed, guard)
                finished = _turn_event(message, 'turn/completed', original)
                if finished is not None:
                    if finished['status'] == 'completed':
                        messages = [item['text'] for item in finished['items'] if item.get('type') == 'agentMessage']
                        if messages and messages[-1].strip():
                            final_text = messages[-1]
                            outcome['native_session']['completed'] = True
                    break
        except (_Ended, OSError, ValueError, KeyError, TypeError) as error:
            outcome['error'] = str(error)
        finally:
            proc.stdin.close()

    local_env = {key: value for key, value in environment.items() if key in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR')}
    local_env.update({name: environment[name] for name in credentials if name in environment})
    local_env.update(HOME=str(home), CODEX_HOME=str(home))
    result = processes.run(argv, cwd, output, remaining, request['prompt'], local_env,
        supervised=True, lock_fd=inherited, stop_requested=should_stop, record_lifecycle=True, stdio_exchange=exchange,
        command_record=folder / 'active-command.json')
    result.update(outcome)
    if result['status'] == 'succeeded':
        if final_text is None:
            result.update(status='unknown', error=outcome.get('error', 'Original native terminal response is unavailable'))
        else:
            raw = final_text.encode('utf-8')
            if len(raw) > 8_388_608:
                raise ValueError('Original App Server final message exceeds the native result limit')
            (output / 'result.txt').write_bytes(raw)
            result.update(result=str(output / 'result.txt'), result_sha256=hashlib.sha256(raw).hexdigest())
    return result


def receipt(state, document, request, folder):
    locator = request['submitted']['active_fixed_check']
    scope = _scope(state, document, locator)
    view = {'status': 'unrecorded', 'source': locator}
    try:
        attempt = _optional(scope)
        intent = _optional(folder / 'active-intent')
        if attempt is None:
            return {**view, 'status': 'unresolved'} if intent is not None else view
        if attempt['run_id'] != document['id']:
            return {**view, 'status': 'blocked', 'reason': 'original_notice_attempt_exists'}
        view['status'] = 'unresolved'
        owner = _optional(folder / 'active-owner')
        if (owner is None or intent is None or attempt['intent_sha256'] != native_sources.sha(intent)
                or owner['request_sha256'] != document['request_sha256'] or intent['owner'] != owner):
            raise ValueError('Original active notice lacks its immutable binding')
        frame = intent['frame']
        digest = native_sources.sha(frame)
        args = frame['params']
        if (attempt['frame_sha256'] != digest or args['threadId'] != owner['thread_id']
                or args['expectedTurnId'] != owner['turn_id']):
            raise ValueError('Original active notice frame differs from the selected turn')
        client_id = args['clientUserMessageId']
        text = args['input'][0]['text']
        view.update(thread_id=owner['thread_id'], turn_id=owner['turn_id'], client_user_message_id=client_id,
                    payload_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(), rpc_acknowledged=False)
        ack = _optional(folder / 'active-ack')
        if ack is not None:
            if ack != {'frame_sha256': digest, 'response': {'id': frame['id'], 'result': {'turnId': owner['turn_id']}}}:
                raise ValueError('Original active acknowledgement differs from its send attempt')
            view['rpc_acknowledged'] = True

        home = native_sources.session_folder(state, document['session']['id']) / 'native-home'
        rollout = home / owner['rollout']
        if not rollout.is_relative_to(home) or rollout.resolve(strict=True) != rollout:
            raise ValueError('Original native rollout lies outside its selected home')
        raw = native_sources.artifact(rollout.parent, rollout.name, _MAX_WIRE, confirm_durable=True)
        records = [parse_json(line, 'Original Codex rollout record', finite=True) for line in raw.decode('utf-8').splitlines()]
        threads = [entry['payload'].get('id') for entry in records if entry['type'] == 'session_meta']
        if threads != [owner['thread_id']]:
            raise ValueError('Original App Server rollout thread differs from the send attempt')
        events = [entry['payload'] for entry in records if entry['type'] == 'event_msg']
        matches = [event['item'] for event in events if event.get('type') == 'item_completed'
                   and event.get('thread_id') == owner['thread_id'] and event.get('turn_id') == owner['turn_id']
                   and _exact_item(event.get('item', {}), client_id, text, cold=True)]
        live = _optional(folder / 'active-item')
        if len(matches) == 1:
            item_id = _identity(matches[0]['id'])
            if live is not None and live != {'frame_sha256': digest, 'item_id': item_id}:
                raise ValueError('Active notice live item contradicts the original rollout')
            view.update(status='delivered', native_item_id=item_id)
        elif len(matches) > 1:
            raise ValueError('Original native history contains multiple matching notice items')
    except (OSError, ValueError, KeyError, TypeError) as error:
        view.update(status='unresolved', reason=str(error))
    return view
