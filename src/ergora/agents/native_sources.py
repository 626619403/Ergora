"""Original Agent artifacts and native source records, without invocation authority.

The native runner and document-correction owner share these immutable readers.
Serializers retain the original native packet identity; fsync confirms existing
material and never publishes a record, starts a process or constructs State.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import TYPE_CHECKING

from ergora.configuration import validation as contracts
from ergora.definitions.bundles import parse_json
from ergora.storage.assets import is_link

if TYPE_CHECKING:
    from ergora.storage.state import State

PACKET_BYTES = 10_000_000


def sync_descriptor(descriptor: int) -> None:
    """Retry one interrupted idempotent sync on the same already-open object."""
    try:
        os.fsync(descriptor)
    except InterruptedError:
        os.fsync(descriptor)


def record(state: State, project_id: str, run_id: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM agent_runs WHERE project=? AND id=?", (project_id, run_id)).fetchone()
    if row is None:
        raise ValueError("Unknown agent run in this project")
    document = parse_json(row[0], "Agent run record", finite=True, bounded=True)
    if not isinstance(document, dict) or document.get("id") != run_id or document.get("project") != project_id:
        raise ValueError("Saved agent run differs from its selected project or run ID")
    return document


def artifact(directory: Path, name: str, byte_limit: int, *, confirm_durable: bool = False) -> bytes:
    if is_link(directory) or not directory.is_dir():
        raise ValueError("Run artifacts require an ordinary directory")
    path = directory / name
    details = path.stat()
    if is_link(path) or not stat.S_ISREG(details.st_mode):
        raise ValueError("Run artifact requires an ordinary file: " + name)
    directory_stamp = directory_identity(directory) if confirm_durable else None
    stream = (os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb')
              if confirm_durable else path.open('rb'))
    with stream:
        if confirm_durable:
            before = os.fstat(stream.fileno())
            def stamp(value):
                return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns
            if not stat.S_ISREG(before.st_mode) or stamp(before) != stamp(details):
                raise ValueError('Run artifact changed before durable confirmation')
        raw = stream.read(min(byte_limit + 1, details.st_size + 1))
        if len(raw) > byte_limit:
            raise ValueError(f"Complete run artifact exceeds its byte limit: {name} > {byte_limit}")
        if confirm_durable:
            sync_descriptor(stream.fileno())
            sync_directory_chain(directory)
            stream.seek(0)
            if stream.read(byte_limit + 1) != raw:
                raise ValueError('Run artifact bytes changed during durable confirmation')
            if (stamp(before) != stamp(os.fstat(stream.fileno()))
                    or stamp(before) != stamp(path.stat(follow_symlinks=False))
                    or directory_stamp != directory_identity(directory)):
                raise ValueError('Run artifact identity changed during durable confirmation')
    return raw


def session_id(value, label='Session ID'):
    contracts.validate(value, {'type': 'string', 'pattern': '^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$'}, label)
    return value


def encode(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(raw) > PACKET_BYTES:
        raise ValueError(f'Complete encoded session packet exceeds {PACKET_BYTES} bytes; it was not truncated')
    return raw


def sha(value):
    return hashlib.sha256(encode(value)).hexdigest()


def sync_directory_chain(directory):
    for parent in (directory, *directory.parents):
        descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            sync_descriptor(descriptor)
        finally:
            os.close(descriptor)


def packet(directory, name='record.json', *, confirm_durable=False):
    return parse_json(artifact(directory, name, PACKET_BYTES, confirm_durable=confirm_durable).decode('utf-8'),
                      'Native session packet', finite=True, bounded=True)


def turn_folder(state, ident):
    return state.root / 'runs' / (session_id(ident) + '.session-turn')


def session_folder(state, ident):
    return state.root / 'runs' / (session_id(ident) + '.session')


def find_run(state, project, ident):
    with state.connect() as db:
        row = db.execute('SELECT document FROM agent_runs WHERE project=? AND id=?', (project, ident)).fetchone()
    return None if row is None else parse_json(row[0], 'Native session run', finite=True, bounded=True)


def directory_identity(path):
    details = path.stat(follow_symlinks=False)
    if is_link(path) or not stat.S_ISDIR(details.st_mode):
        raise ValueError('Session requires an ordinary directory')
    return [details.st_dev, details.st_ino]


def request(state, project_id: str, run_id: str) -> dict:
    """Read exact operator submission and effective input from the original turn."""
    session_id(run_id, 'Run ID')
    document = record(state, project_id, run_id)
    if document.get('kind') != 'native-agent-run':
        raise ValueError('Select an original persistent native turn')
    original = packet(turn_folder(state, run_id), 'request.json')
    if (sha(original) != document.get('request_sha256') or original.get('run_id') != run_id
            or original.get('project') != project_id or original.get('session') != document.get('session')
            or original.get('submitted') != document.get('submitted')):
        raise ValueError('Native source differs from its original request/submission')
    prompt = original.get('prompt')
    if not isinstance(prompt, str) or hashlib.sha256(prompt.encode('utf-8')).hexdigest() != document.get('prompt_sha256'):
        raise ValueError('Native effective prompt differs from its original identity')
    return {'document': document, 'request': original, 'request_sha256': document['request_sha256'],
            'prompt_sha256': document['prompt_sha256']}


def result(state, project_id: str, run_id: str) -> dict:
    """Read a stopped successful plaintext result; no current admission or resend."""
    source = request(state, project_id, run_id)
    original, document = source['request'], source['document']
    final = packet(turn_folder(state, run_id) / 'final', confirm_durable=True)
    if (final.get('id') != run_id or final.get('project') != project_id
            or final.get('session') != original['session']
            or final.get('request_sha256') != source['request_sha256']
            or final.get('submitted') != original['submitted']):
        raise ValueError('Native final differs from its original turn/submission')
    if final.get('status') != 'succeeded' or final.get('execution_stopped') is not True:
        raise ValueError('Native result is not a confirmed stopped success; observe the original turn')
    if original['schema'] is not None:
        raise ValueError('Automatic correction suggestions require an ordinary plaintext native result')
    raw = artifact(state.root / 'runs' / run_id, 'result.txt', 8_388_608, confirm_durable=True)
    if hashlib.sha256(raw).hexdigest() != final.get('result_sha256'):
        raise ValueError('Native result differs from its original complete bytes')
    raw.decode('utf-8')
    return {**source, 'final': final, 'result': raw, 'result_sha256': final['result_sha256']}


def records_present(state, run_id: str) -> bool:
    """Cheap liveness of required evidence, never a cached validity/authority verdict."""
    session_id(run_id, 'Run ID')
    selected = (turn_folder(state, run_id) / 'request.json',
                turn_folder(state, run_id) / 'final' / 'record.json',
                state.root / 'runs' / run_id / 'result.txt')
    try:
        return all(not is_link(path) and stat.S_ISREG(path.stat().st_mode) for path in selected)
    except OSError:
        return False
