"""Immutable local dispatch evidence and validation for a record-only campaign."""

from graphlib import CycleError, TopologicalSorter
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
from ergora.development.verification import validate_fixed_check_locator, validate_fixed_check_source


WORKFLOW_TYPE = 'ErgoraCampaign'
OPENING_MEMO = 'ergora.campaign.opening_sha256'
ATTEMPT_MEMO = 'ergora.campaign.attempt_sha256'
MAX_PLAN_BYTES = 65_536
MAX_RECORD_BYTES = 2 * MAX_PLAN_BYTES
MAX_FIXED_TASKS = 8
FIXED_TASK_UPDATE_PREFIX = 'ergora-campaign-check:'
FIXED_CHECK_LOCATOR = ('operation_id', 'request_file_sha256', 'job_sha256', 'candidate_sha')
FIXED_CHECK_TERMINAL = ('receipt_sha256', 'fixed_results_sha256')
FIXED_TASK_LOCATOR = (*FIXED_CHECK_LOCATOR, 'project_revision', 'job_id', 'authorization_sha256', 'verification_sha256')
FIXED_TASK_SOURCE = (*FIXED_TASK_LOCATOR, *FIXED_CHECK_TERMINAL)
PENDING_JOB_STATES = ('queued', 'attempted')
READBACK_CLEANUP_SECONDS = 0.8
READBACK_ACTIVITY = 'ergora_campaign_fixed_check_readback'
RECIPIENT_ACTIVITY = 'ergora_campaign_codex_recipient'
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


def project_selection(state, project, revision):
    """Read the scheduler and published registration for the approved project revision."""
    from ergora.configuration import projects, registrations

    if project['revision'] != revision:
        raise ValueError('Project revision changed; use the original approved revision before dispatch')
    config = projects.effective_configuration(project)
    scheduler = config['layers']['scheduler']
    if scheduler['source']['kind'] != 'project' or scheduler['binding']['tool'] != 'temporal':
        raise ValueError('Campaign creation requires an explicitly bound Temporal scheduler')
    if not scheduler['validation']['valid']:
        raise ValueError(scheduler['validation']['error'])
    return {'registration': registrations.publication_identity(state.root, project),
            'configuration_sha256': config['sha256'], 'scheduler': scheduler['binding']}


def verify_registration(state, opening):
    """Verify the original published registration for this saved campaign."""
    from ergora.configuration import registrations

    selected = opening['registration']
    original = registrations.published_project(state.root, opening['project'], selected['operation_id'],
                                               selected['intent_sha256'])
    if original['registration']['sha256'] != selected['sha256'] or original['revision'] > opening['project_revision']:
        raise ValueError('Campaign original registration identity differs')
    return original


def require_check_project(state, opening):
    """Return the same project snapshot that matches the original fixed-check authority."""
    project = state.project(opening['project'])
    selected = project_selection(state, project, opening['project_revision'])
    if any(opening[key] != value for key, value in selected.items()):
        raise ValueError('Original project registration or scheduler changed before task observation')
    return project


def validate_plan(plan):
    required = {'schema_version', 'goal', 'acceptance', 'baseline_commit', 'evidence_format', 'limits'}
    if (not isinstance(plan, dict) or set(plan) - {'tasks'} != required
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
    if 'tasks' in plan:
        validate_fixed_tasks(plan['tasks'])
        task = readback_task({'plan': plan})
        if task is not None and task['readback']['deadline_at'] > limits['expires_at']:
            raise ValueError('Campaign readback window exceeds the original expiry')
    # Also rejects unpaired Unicode surrogates before an intent can be saved.
    identity(plan)


def validate_fixed_tasks(tasks):
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= MAX_FIXED_TASKS:
        raise ValueError(f'Campaign plan requires 1–{MAX_FIXED_TASKS} original fixed-check tasks when configured')
    dependencies = {}
    scheduled = False
    for task in tasks:
        if not isinstance(task, dict) or task.keys() - {'readback', 'recipient'} != {'task_id', 'depends_on', 'source'}:
            raise ValueError('Campaign task requires task_id, depends_on and an exact fixed-check source')
        task_id, parents, source = task['task_id'], task['depends_on'], task['source']
        if not safe_id(task_id) or task_id in dependencies:
            raise ValueError('Campaign task requires a unique safe ID')
        if not isinstance(parents, list) or not all(safe_id(item) for item in parents) or len(set(parents)) != len(parents):
            raise ValueError('Campaign task dependencies require distinct safe IDs')
        pending = isinstance(source, dict) and source.get('pending') is True
        required = {*FIXED_TASK_LOCATOR, 'pending'} if pending else set(FIXED_TASK_SOURCE)
        if (not isinstance(source, dict) or source.keys() != required
                or type(source['project_revision']) is not int or source['project_revision'] < 1
                or not isinstance(source['job_id'], str) or re.fullmatch(r'check-[0-9a-f]{40}-[0-9a-f]{24}', source['job_id']) is None
                or not all(sha256(source[key]) for key in ('authorization_sha256', 'verification_sha256'))):
            raise ValueError('Campaign task source requires the exact original fixed-check Job identity')
        locator = {key: source[key] for key in FIXED_CHECK_LOCATOR}
        if pending:
            validate_fixed_check_locator(locator)
        else:
            validate_fixed_check_source({**locator, **{key: source[key] for key in FIXED_CHECK_TERMINAL}})
        if 'readback' in task:
            window = task['readback']
            if (scheduled or not pending or not isinstance(window, dict) or window.keys() != {'due_at', 'deadline_at'}
                    or type(window['due_at']) is not int or type(window['deadline_at']) is not int
                    or not 1 <= window['due_at'] < window['deadline_at'] <= MAX_EXPIRY):
                raise ValueError('Campaign admits one original readback window on an explicitly pending task')
            scheduled = True
        if 'recipient' in task:
            validate_recipient(task['recipient'])
            if 'readback' not in task:
                raise ValueError('Campaign Codex recipient requires the selected original timed readback')
        dependencies[task_id] = parents
    if any(parent not in dependencies for parents in dependencies.values() for parent in parents):
        raise ValueError('Campaign task dependency is absent from the frozen plan')
    try:
        TopologicalSorter(dependencies).prepare()
    except CycleError as error:
        raise ValueError('Campaign task dependencies contain a cycle') from error


def fixed_tasks(opening):
    return {task['task_id']: task for task in opening['plan'].get('tasks', ())}


def has_pending_checks(opening):
    return any(task['source'].get('pending') is True for task in fixed_tasks(opening).values())


def readback_task(opening):
    return next((task for task in opening['plan'].get('tasks', ()) if 'readback' in task), None)


def validate_recipient(recipient):
    if (not isinstance(recipient, dict)
            or recipient.keys() != {'session_id', 'parent_run_id', 'intent_id', 'prompt', 'timeout_seconds'}
            or not all(safe_id(recipient[key]) for key in ('session_id', 'parent_run_id', 'intent_id'))
            or not isinstance(recipient['prompt'], str) or not recipient['prompt'].strip() or '\0' in recipient['prompt']
            or type(recipient['timeout_seconds']) is not int or not 1 <= recipient['timeout_seconds'] <= 3600):
        raise ValueError('Campaign Codex recipient requires an exact session, parent, intent, prompt and bounded timeout')


def recipient_task(opening):
    task = readback_task(opening)
    return task if task is not None and 'recipient' in task else None


def require_recipient_binding(binding):
    paths = ('source_executable', 'payload_executable')
    if (not isinstance(binding, dict)
            or binding.keys() != {*paths, 'context_digest', 'role', 'native_id', 'payload_sha256', 'device', 'inode', 'size'}
            or not all(isinstance(binding[key], str) and Path(binding[key]).is_absolute() and '\0' not in binding[key] for key in paths)
            or not safe_id(binding['role']) or not uuid_text(binding['native_id'])
            or not sha256(binding['context_digest']) or not sha256(binding['payload_sha256'])
            or any(type(binding[key]) is not int or binding[key] <= 0 for key in ('device', 'inode', 'size'))):
        raise ValueError('Campaign Codex recipient lacks the original native context and executable binding')


def wake_intent(opening, run_id, task, readback):
    scope = {'opening_sha256': identity(opening), 'workflow_id': opening['workflow_id'], 'run_id': run_id,
             'task_id': task['task_id'], 'source': readback, 'expires_at': opening['plan']['limits']['expires_at']}
    return {'wake_id': 'codex-recipient:' + identity(scope), **scope}


def readback_grant(opening, run_id, task, waiting):
    return {'opening_sha256': identity(opening), 'run_id': run_id, 'task_id': task['task_id'],
            'waiting_receipt_sha256': identity(waiting), **task['readback']}


def readback_id(grant):
    return 'fixed-check-readback:' + identity(grant)


def readback_result(opening, task, activity_id, result):
    if result['activity_id'] != activity_id or not sha256(result['reader_cleanup_sha256']):
        raise ValueError('Original fixed-check readback result identity differs')
    return original_check_evidence(opening, task, result['observation'])


def checked_readback(opening, run_id, waits, observation):
    task = readback_task(opening)
    if not isinstance(observation, dict):
        raise ValueError('Campaign readback is missing its original state')
    status = observation.get('status')
    if observation == {'status': 'not_armed'}:
        return observation
    waiting = waits.get(task['task_id'])
    fields = {'status', 'activity_id', 'waiting_receipt_sha256'}
    if (waiting is None or observation.get('waiting_receipt_sha256') != identity(waiting)
            or observation.get('activity_id') != readback_id(readback_grant(opening, run_id, task, waiting))):
        raise ValueError('Campaign readback differs from its original wait and window')
    if status == 'available':
        proof = {*FIXED_CHECK_TERMINAL, 'observation_sha256', 'reader_cleanup_sha256'}
        if observation.keys() == fields | proof and all(sha256(observation[k]) for k in proof):
            return observation
    elif status == 'unknown':
        if observation.keys() == fields | {'reason'} and observation['reason'] in (
                'campaign_closed', 'read_window_expired', 'original_read_unavailable', 'original_still_pending',
                'task_already_observed'):
            return observation
    elif status in ('armed', 'scheduled') and observation.keys() == fields:
        return observation
    raise ValueError('Campaign readback state differs from its original evidence')


def original_check_evidence(opening, task, observation):
    source = task['source']
    if (not isinstance(observation, dict) or observation.get('project') != opening['project']
            or observation.get('stop_requested') is not False or type(observation.get('project_revision')) is not int
            or any(observation.get(key) != value for key, value in source.items() if key != 'pending')):
        raise ValueError('Task requires the exact successful original fixed check with confirmed cleanup')
    status = observation.get('status')
    if (source.get('pending') is True and status in PENDING_JOB_STATES
            and observation.get('cleanup_confirmed') is None
            and all(observation.get(key) is None for key in FIXED_CHECK_TERMINAL)):
        return identity(observation), {'status': status}
    if (status == 'succeeded' and observation.get('cleanup_confirmed') is True
            and all(sha256(observation.get(key)) for key in FIXED_CHECK_TERMINAL)):
        job = {'status': status, **{key: observation[key] for key in FIXED_CHECK_TERMINAL}}
        return identity(observation), job if source.get('pending') is True else None
    raise ValueError('Task requires the exact successful original fixed check with confirmed cleanup')


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

    def write(self, name, value, *, before_publish=None):
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        if len(raw) > MAX_RECORD_BYTES:
            raise ValueError('Campaign dispatch record exceeds its byte limit')
        descriptor, temporary = tempfile.mkstemp(dir=self.directory, prefix='.pending-')
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if before_publish is not None:
                before_publish()
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

    def load_check(self, opening, start_attempt, run_id, task, *, waiting=False):
        command = self._read(check_record_name(task['task_id'], waiting=waiting))
        if command is not None:
            if run_id is None:
                intent = command.get('intent')
                run_id = intent.get('run_id') if isinstance(intent, dict) else None
                if not uuid_text(run_id):
                    raise ValueError('Saved original check attempt has no valid first Run ID')
            validate_check_command(opening, identity(start_attempt), run_id, command)
            if (command['intent']['task_id'] != task['task_id']
                    or (command['intent']['operation'] == 'wait_check') != waiting):
                raise ValueError('Saved original check attempt names another campaign task or stage')
        return command

    def load_checks(self, opening, start_attempt, run_id):
        """Read saved attempts and keep them all pinned to the same candidate first Run."""
        commands = []
        update_ids = set()
        for task in fixed_tasks(opening).values():
            stages = (False, True) if task['source'].get('pending') is True else (False,)
            for waiting in stages:
                command = self.load_check(opening, start_attempt, run_id, task, waiting=waiting)
                if command is None:
                    continue
                update_id = command['attempt']['update_id']
                if update_id in update_ids:
                    raise ValueError('Saved campaign task attempts share an original Update ID')
                update_ids.add(update_id)
                run_id = command['intent']['run_id']
                commands.append(command)
        return run_id, commands

    def _validate_opening(self, opening):
        fields = {'schema_version', 'mode', 'control_home', 'project', 'project_revision', 'registration',
                  'configuration_sha256', 'campaign', 'actor', 'scheduler', 'creation_id', 'plan', 'plan_sha256',
                  'plan_document_sha256', 'task_queue', 'workflow_id', 'workflow_type'}
        if (set(opening) - {'recipient_binding'} != fields or type(opening['schema_version']) is not int or opening['schema_version'] != 1
                or opening['control_home'] != str(self.home)
                or opening['project'] != self.project or opening['campaign'] != self.campaign
                or identity(opening['actor']) != identity(self.actor)
                or type(opening['project_revision']) is not int or opening['project_revision'] < 1
                or not uuid_text(opening['creation_id']) or not sha256(opening['plan_sha256'])
                or not sha256(opening['configuration_sha256'])
                or opening['workflow_type'] != WORKFLOW_TYPE
                or opening['workflow_id'] != workflow_id(self.project, self.campaign)):
            raise ValueError('Campaign intent differs from its original project, control home or operator')
        validate_plan(opening['plan'])
        recipient = recipient_task(opening)
        if recipient is None:
            if opening['mode'] != 'record_only' or 'recipient_binding' in opening:
                raise ValueError('Record-only Campaign cannot contain recipient execution authority')
        else:
            if opening['mode'] != 'codex_recipient':
                raise ValueError('Campaign opening does not authorize its frozen Codex recipient')
            require_recipient_binding(opening.get('recipient_binding'))
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


def _update_intent(opening, start_attempt_sha256, run_id, operation):
    return {'schema_version': 1, 'operation': operation, 'workflow_id': opening['workflow_id'], 'run_id': run_id,
            'opening_sha256': identity(opening), 'start_attempt_sha256': start_attempt_sha256}


def stop_intent(opening, start_attempt_sha256, run_id):
    return _update_intent(opening, start_attempt_sha256, run_id, 'stop')


def update_attempt(intent, update_id):
    return {'schema_version': 1, 'intent_sha256': identity(intent), 'update_id': update_id}


def validate_stop_attempt(intent, attempt):
    update_id = attempt.get('update_id')
    prefix = 'ergora-campaign-stop:'
    if (not isinstance(update_id, str) or not update_id.startswith(prefix) or not uuid_text(update_id[len(prefix):])
            or identity(attempt) != identity(update_attempt(intent, update_id))):
        raise ValueError('Campaign stop attempt differs from the original intent or Update ID')


def update_receipt(intent, attempt, decision):
    return {'schema_version': 1, 'decision': decision, 'intent_sha256': identity(intent),
            'attempt_sha256': identity(attempt), 'update_id': attempt['update_id'], 'run_id': intent['run_id']}


def require_stop_receipt(intent, attempt, receipt):
    if (not isinstance(receipt, dict) or receipt.get('decision') not in ('accepted', 'expired')
            or identity(receipt) != identity(update_receipt(intent, attempt, receipt['decision']))):
        raise ValueError('Campaign stop receipt differs from its exact original Update')
    return receipt


def check_record_name(task_id, *, waiting):
    return ('wait-check-' if waiting else 'check-') + task_id


def check_intent(opening, start_attempt_sha256, run_id, task_id, evidence_sha256, *, job=None):
    operation = 'wait_check' if job is not None and job['status'] in PENDING_JOB_STATES else 'observe_check'
    intent = {**_update_intent(opening, start_attempt_sha256, run_id, operation),
              'task_id': task_id, 'observation_sha256': evidence_sha256}
    return {**intent, 'job': job} if job is not None else intent


def _validate_check_job(task, job):
    if task['source'].get('pending') is not True:
        if job is not None:
            raise ValueError('Completed-pin task does not admit staged evidence')
        return
    if isinstance(job, dict):
        if job.keys() == {'status'} and job['status'] in PENDING_JOB_STATES:
            return
        if (job.keys() - {'waiting_receipt_sha256'} == {'status', *FIXED_CHECK_TERMINAL}
                and job['status'] == 'succeeded' and all(sha256(job[key]) for key in FIXED_CHECK_TERMINAL)
                and ('waiting_receipt_sha256' not in job or sha256(job['waiting_receipt_sha256']))):
            return
    raise ValueError('Pending-source task requires exact queued, attempted or passing terminal evidence')


def validate_check_command(opening, start_attempt_sha256, run_id, command):
    if not isinstance(command, dict) or command.keys() != {'intent', 'attempt'}:
        raise ValueError('Campaign check command requires its complete intent and attempt')
    intent, attempt = command['intent'], command['attempt']
    if not isinstance(intent, dict) or not isinstance(attempt, dict):
        raise ValueError('Campaign check requires its structured intent and attempt')
    task_id, evidence, job = intent.get('task_id'), intent.get('observation_sha256'), intent.get('job')
    if not safe_id(task_id) or task_id not in fixed_tasks(opening) or not sha256(evidence):
        raise ValueError('Campaign check intent does not bind the original opening, task and first Run')
    _validate_check_job(fixed_tasks(opening)[task_id], job)
    if identity(intent) != identity(check_intent(opening, start_attempt_sha256, run_id, task_id, evidence, job=job)):
        raise ValueError('Campaign check intent does not bind the original opening, task and first Run')
    update_id = attempt.get('update_id')
    if (not isinstance(update_id, str) or not update_id.startswith(FIXED_TASK_UPDATE_PREFIX)
            or not uuid_text(update_id[len(FIXED_TASK_UPDATE_PREFIX):])
            or identity(attempt) != identity(update_attempt(intent, update_id))):
        raise ValueError('Campaign check attempt differs from its original intent or Update ID')


def check_receipt(command):
    intent, attempt = command['intent'], command['attempt']
    decision = 'waiting_job' if intent['operation'] == 'wait_check' else 'observed'
    receipt = {**update_receipt(intent, attempt, decision), 'task_id': intent['task_id'],
               'observation_sha256': intent['observation_sha256']}
    return {**receipt, 'job': intent['job']} if 'job' in intent else receipt


def require_check_receipt(intent, attempt, receipt):
    if identity(receipt) != identity(check_receipt({'intent': intent, 'attempt': attempt})):
        raise ValueError('Campaign check receipt differs from its exact original Update')
    return receipt


def fixed_task_state(opening, start_attempt_sha256, run_id, observations, waits=None):
    tasks = fixed_tasks(opening)
    waits = {} if waits is None else waits
    for expected, receipts in (('observed', observations), ('waiting_job', waits)):
        if not isinstance(receipts, dict) or set(receipts) - set(tasks):
            raise ValueError('Campaign task state differs from the original plan task set')
        for task_id, receipt in receipts.items():
            if (not isinstance(receipt, dict) or receipt.get('decision') != expected
                    or not set(tasks[task_id]['depends_on']) <= observations.keys()):
                raise ValueError('Campaign task receipt differs from its original stage or dependencies')
            job = receipt.get('job')
            _validate_check_job(tasks[task_id], job)
            if expected == 'observed' and job is not None:
                wait = waits.get(task_id)
                if job.get('waiting_receipt_sha256') != (identity(wait) if wait is not None else None):
                    raise ValueError('Campaign terminal check differs from its original waiting receipt')
            intent = check_intent(opening, start_attempt_sha256, run_id, task_id,
                                  receipt.get('observation_sha256'), job=job)
            attempt = update_attempt(intent, receipt.get('update_id'))
            validate_check_command(opening, start_attempt_sha256, run_id, {'intent': intent, 'attempt': attempt})
            require_check_receipt(intent, attempt, receipt)
    views = {}
    for task_id, task in tasks.items():
        status = ('observed' if task_id in observations else 'waiting_job' if task_id in waits else
                  'ready' if set(task['depends_on']) <= observations.keys() else 'waiting_dependencies')
        view = {**task, 'status': status, 'receipt': observations.get(task_id)}
        if task['source'].get('pending') is True:
            view['waiting_receipt'] = waits.get(task_id)
        views[task_id] = view
    return views
