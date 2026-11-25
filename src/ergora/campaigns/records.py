"""Immutable local dispatch evidence and validation for a record-only campaign."""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from uuid import UUID

from ergora.definitions.bundles import parse_json
from ergora.development.envelopes import identity


WORKFLOW_TYPE = 'ErgoraCampaign'
OPENING_MEMO = 'ergora.campaign.opening_sha256'
ATTEMPT_MEMO = 'ergora.campaign.attempt_sha256'
MAX_PLAN_BYTES = 65_536
MAX_RECORD_BYTES = 2 * MAX_PLAN_BYTES
# Last whole UTC second supported by both Python datetime and protobuf Timestamp.
MAX_EXPIRY = 253_402_300_799


def safe_id(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value) is not None


def sha256(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def uuid_text(value):
    try:
        return isinstance(value, str) and str(UUID(value)) == value
    except ValueError:
        return False


def workflow_id(project, campaign):
    return f'ergora-campaign:{project}:{campaign}'


def worker_queue(project, campaign, scheduler, creation_id):
    suffix = identity({'queue': scheduler['task_queue'], 'creation_id': creation_id})
    return f'ergora-campaign-{project}-{campaign}-{suffix}'


def validate_plan(plan):
    if (not isinstance(plan, dict)
            or set(plan) != {'schema_version', 'goal', 'acceptance', 'baseline_commit', 'evidence_format', 'limits'}
            or type(plan['schema_version']) is not int or plan['schema_version'] != 1):
        raise ValueError('Campaign plan requires schema_version 1 and the complete record-only fields')
    for name in ('goal', 'acceptance', 'evidence_format'):
        if not isinstance(plan[name], str) or not plan[name].strip() or '\0' in plan[name]:
            raise ValueError(f'Campaign plan {name} must be nonempty text')
    if (not isinstance(plan['baseline_commit'], str)
            or re.fullmatch(r'[0-9a-f]{40}(?:[0-9a-f]{24})?', plan['baseline_commit']) is None):
        raise ValueError('Campaign baseline_commit requires a full lowercase Git object ID')
    limits = plan['limits']
    if (not isinstance(limits, dict) or set(limits) != {'expires_at'} or type(limits['expires_at']) is not int
            or not 1 <= limits['expires_at'] <= MAX_EXPIRY):
        raise ValueError('Campaign expiry requires a representable absolute UTC Unix second')
    # Also rejects unpaired Unicode surrogates before an intent can be saved.
    identity(plan)


def operator():
    if not hasattr(os, 'geteuid'):
        raise ValueError('Campaign operations require Unix effective UID and local owner permissions')
    return {'assurance': 'local-process-only', 'euid': os.geteuid()}


def _owned(path: Path, *, kind: str, private: bool = False):
    info = path.lstat()
    expected = stat.S_ISDIR if kind == 'directory' else stat.S_ISREG
    mask = 0o077 if private else 0o022
    if not expected(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & mask:
        raise ValueError(f'Campaign requires an owned {kind} with protected permissions: {path}')


def _bytes(path: Path, size: int):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Campaign input and records require ordinary files')
        raw = stream.read(size + 1)
    if len(raw) > size:
        raise ValueError(f'Campaign file exceeds {size} bytes: {path.name}')
    return raw


def read_plan(path: Path, expected_sha: str):
    raw = _bytes(path, MAX_PLAN_BYTES)
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('Campaign plan file does not match --plan-sha256')
    plan = parse_json(raw.decode('utf-8'), 'campaign plan', finite=True, bounded=True)
    validate_plan(plan)
    return plan


def _sync_directory(path: Path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class CampaignFiles:
    def __init__(self, home: Path, project: str, campaign: str):
        if not safe_id(project) or not safe_id(campaign):
            raise ValueError('Campaign and project IDs require 1–64 letters, digits, underscores or hyphens')
        self.actor = operator()
        _owned(home, kind='directory')
        _owned(home / 'ergora.sqlite3', kind='file')
        self.home = home
        self.project = project
        self.campaign = campaign
        top = home / 'campaigns'
        self.directories = (top, top / project, top / project / campaign)
        self.directory = self.directories[-1]
        self.lock = self.directory / '.start.lock'

    def ensure_directory(self):
        for directory in self.directories:
            directory.mkdir(mode=0o700, exist_ok=True)
            _owned(directory, kind='directory', private=True)
            _sync_directory(directory.parent)
        descriptor = os.open(self.lock, os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        os.close(descriptor)
        _owned(self.lock, kind='file', private=True)

    def _read(self, name):
        path = self.directory / f'{name}.json'
        try:
            _owned(path, kind='file', private=True)
            raw = _bytes(path, MAX_RECORD_BYTES)
        except FileNotFoundError:
            return None
        value = parse_json(raw.decode('utf-8'), path.name, finite=True, bounded=True)
        if not isinstance(value, dict):
            raise ValueError(f'Campaign {name} is not a JSON object')
        return value

    def write(self, name, value):
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        if len(raw) > MAX_RECORD_BYTES:
            raise ValueError('Campaign dispatch record exceeds its byte limit')
        descriptor, temporary = tempfile.mkstemp(dir=self.directory, prefix='.pending-')
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, self.directory / f'{name}.json')
        finally:
            Path(temporary).unlink(missing_ok=True)
        _sync_directory(self.directory)

    def load(self):
        for directory in self.directories:
            try:
                _owned(directory, kind='directory', private=True)
            except FileNotFoundError:
                return None, None, None
        opening = self._read('start-intent')
        # Read completion before attempt so later publications can only make the snapshot incomplete.
        result = self._read('start-result')
        attempt = self._read('start-attempt')
        if opening is None and (attempt is not None or result is not None):
            opening = self._read('start-intent')
            if opening is None:
                raise ValueError('Campaign has dispatch evidence without its original intent')
        if opening is not None:
            self._validate_opening(opening)
        if attempt is not None:
            if (not uuid_text(attempt.get('attempt_id'))
                    or identity(attempt) != identity(attempt_document(opening, attempt['attempt_id']))):
                raise ValueError('Campaign attempt differs from its original intent')
        if result is not None:
            if (attempt is None or not uuid_text(result.get('run_id'))
                    or identity(result) != identity(result_document(opening, attempt, result['run_id']))):
                raise ValueError('Campaign result differs from its original intent or attempt')
        return opening, attempt, result

    def load_stop(self, opening, start_attempt, start_result):
        intent = self._read('stop-intent')
        result = self._read('stop-result')
        attempt = self._read('stop-attempt')
        if intent is None and (attempt is not None or result is not None):
            intent = self._read('stop-intent')
            if intent is None:
                raise ValueError('Campaign stop evidence lacks its original intent')
        if intent is None:
            return None, None, None
        run_id = intent.get('run_id')
        if (opening is None or start_attempt is None or not uuid_text(run_id)
                or (start_result is not None and start_result['run_id'] != run_id)
                or identity(intent) != identity(stop_intent(opening, identity(start_attempt), run_id))):
            raise ValueError('Campaign stop intent differs from the original start or first Run')
        if attempt is not None:
            validate_stop_attempt(intent, attempt)
        if result is not None:
            if attempt is None or result.keys() != {'receipt'}:
                raise ValueError('Campaign stop result lacks its original attempt or receipt')
            require_stop_receipt(intent, attempt, result['receipt'])
        return intent, attempt, result

    def _validate_opening(self, opening):
        fields = {'schema_version', 'mode', 'control_home', 'project', 'project_revision', 'registration',
                  'configuration_sha256', 'campaign', 'actor', 'scheduler', 'creation_id', 'plan', 'plan_sha256',
                  'plan_document_sha256', 'task_queue', 'workflow_id', 'workflow_type'}
        if (set(opening) != fields or type(opening['schema_version']) is not int or opening['schema_version'] != 1
                or opening['mode'] != 'record_only' or opening['control_home'] != str(self.home)
                or opening['project'] != self.project or opening['campaign'] != self.campaign
                or identity(opening['actor']) != identity(self.actor)
                or type(opening['project_revision']) is not int or opening['project_revision'] < 1
                or not uuid_text(opening['creation_id']) or not sha256(opening['plan_sha256'])
                or not sha256(opening['configuration_sha256'])
                or opening['workflow_type'] != WORKFLOW_TYPE
                or opening['workflow_id'] != workflow_id(self.project, self.campaign)):
            raise ValueError('Campaign intent differs from its original project, control home or operator')
        validate_plan(opening['plan'])
        if opening['plan_document_sha256'] != identity(opening['plan']):
            raise ValueError('Campaign intent does not bind its saved plan document')
        scheduler = opening['scheduler']
        if (not isinstance(scheduler, dict) or set(scheduler) != {'tool', 'address', 'namespace', 'task_queue'}
                or scheduler['tool'] != 'temporal'
                or any(not isinstance(value, str) or not value.strip() for value in scheduler.values())
                or opening['task_queue'] != worker_queue(self.project, self.campaign, scheduler, opening['creation_id'])):
            raise ValueError('Campaign intent differs from its original scheduler or dedicated queue')
        registration = opening['registration']
        if (not isinstance(registration, dict) or set(registration) != {'sha256', 'operation_id', 'intent_sha256'}
                or not sha256(registration['sha256']) or not sha256(registration['intent_sha256'])
                or not isinstance(registration['operation_id'], str)
                or re.fullmatch('[0-9a-f]{32}', registration['operation_id']) is None):
            raise ValueError('Campaign intent lacks its original published registration identity')


def attempt_document(opening, attempt_id):
    return {'schema_version': 1, 'attempt_id': attempt_id, 'opening_sha256': identity(opening),
            'workflow_id': opening['workflow_id']}


def result_document(opening, attempt, run_id):
    return {'schema_version': 1, 'workflow_id': opening['workflow_id'], 'run_id': run_id,
            'opening_sha256': identity(opening), 'attempt_sha256': identity(attempt)}


def stop_intent(opening, start_attempt_sha256, run_id):
    return {'schema_version': 1, 'operation': 'stop', 'workflow_id': opening['workflow_id'], 'run_id': run_id,
            'opening_sha256': identity(opening), 'start_attempt_sha256': start_attempt_sha256}


def stop_attempt(intent, update_id):
    return {'schema_version': 1, 'intent_sha256': identity(intent), 'update_id': update_id}


def validate_stop_attempt(intent, attempt):
    update_id = attempt.get('update_id')
    prefix = 'ergora-campaign-stop:'
    if (not isinstance(update_id, str) or not update_id.startswith(prefix) or not uuid_text(update_id[len(prefix):])
            or identity(attempt) != identity(stop_attempt(intent, update_id))):
        raise ValueError('Campaign stop attempt differs from the original intent or Update ID')


def stop_receipt(intent, attempt, decision):
    return {'schema_version': 1, 'decision': decision, 'intent_sha256': identity(intent),
            'attempt_sha256': identity(attempt), 'update_id': attempt['update_id'], 'run_id': intent['run_id']}


def require_stop_receipt(intent, attempt, receipt):
    if (not isinstance(receipt, dict) or receipt.get('decision') not in ('accepted', 'expired')
            or identity(receipt) != identity(stop_receipt(intent, attempt, receipt['decision']))):
        raise ValueError('Campaign stop receipt differs from its exact original Update')
    return receipt
