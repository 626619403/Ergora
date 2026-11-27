"""Bind a local native continuation to its original Campaign readback and STOP fence."""

from contextlib import ExitStack, contextmanager
import hashlib
import math
import os
from pathlib import Path
import signal
import sys
import time

from ergora.agents import native_sources
from ergora.campaigns.records import (
    ASSIGNMENT_ATTEMPT, ASSIGNMENT_REFUSAL, CampaignFiles, assignment_intent, assignment_task, check_receipt,
    identity, manual_wake_source, readback_grant, readback_id, readback_proof, readback_reference, readback_result,
    receipt_recovery_activity, receipt_recovery_id, receipt_recovery_proof, recipient_task,
    reobservation_id, reobservation_task, require_check_project, sha256, training_readback_task, wake_intent,
)
from ergora.runtime import budget_clock, processes
from ergora.storage.state import State, file_lock


# Linux UAPI values, also used when Python has no file lease wrappers.
_SET_LEASE = 1024
_GET_LEASE = 1025
_SET_LEASE_SIGNAL = 10  # F_SETSIG
_TURN_MISMATCH = 'Native turn does not match the frozen Campaign recipient, context and submission'


class RecipientBlocked(ValueError):
    """The original Campaign has a verified veto before native admission."""


def require_payload_support():
    if sys.platform != 'linux' or os.execve not in os.supports_fd:
        raise ValueError('Campaign recipient requires Linux executable descriptor and read lease support')


def verified_source(files, opening, start, run_id, task, *, reobservation=False):
    training = training_readback_task(task)
    waiting = None if training else files.load_check(opening, start, run_id, task, waiting=True)
    if waiting is None and not training:
        raise ValueError('Campaign recipient is missing its original waiting attempt')
    grant = readback_grant(opening, run_id, task, check_receipt(waiting) if waiting else None)
    activity = reobservation_id(grant) if reobservation else readback_id(grant)
    prefix = 'reobservation' if reobservation else 'readback'
    readback = files._read(f'{prefix}-result')
    cleanup = files._read(f'{prefix}-cleanup')
    attempt = files._read(f'{prefix}-attempt')
    if (readback is None or cleanup is None or attempt is None or attempt.get('grant') != grant
            or attempt.get('activity_id') != activity or cleanup.get('activity_id') != activity
            or readback.get('reader_cleanup_sha256') != identity(cleanup)
            or cleanup.get('receipt', {}).get('model_waited') is not True
            or cleanup['receipt'].get('remaining_children') != []):
        raise ValueError('Campaign recipient requires its exact original reader result and cleanup')
    if training:
        guard = files._read(f'{prefix}-guard')
        if (guard is None or guard.get('activity_id') != activity or guard.get('worker') != attempt.get('worker')
                or not isinstance(guard.get('guard'), dict) or cleanup['receipt'].get('owner') != guard['guard']):
            raise ValueError('Campaign training recipient requires cleanup by the original readback guard')
    evidence, job = readback_result(opening, task, activity, readback)
    if job['status'] != 'succeeded':
        raise ValueError('Campaign recipient requires a passing original fixed check')
    return {'status': 'available', 'activity_id': activity,
            **readback_reference(grant), **readback_proof(evidence, job, readback)}


def manual_commands(files, opening, start, run_id, task):
    wait = files.load_check(opening, start, run_id, task, waiting=True)
    terminal = files.load_check(opening, start, run_id, task)
    if wait is None or terminal is None:
        raise ValueError('Campaign manual wake requires its protected waiting and terminal attempts')
    return wait, terminal


def verified_receipt_recovery(files, opening, start, run_id, task):
    if receipt_recovery_activity(task) is None:
        raise ValueError('Campaign receipt recovery was not selected')
    names = ('readback-attempt', 'readback-guard', 'readback-result', 'readback-cleanup')
    documents = {name: files._read(name) for name in names}
    source = verified_source(files, opening, start, run_id, task)
    guard, cleanup = (documents[name] for name in ('readback-guard', 'readback-cleanup'))
    finished = cleanup['receipt']
    if (finished.get('kind') != 'supervised-process-cleanup' or finished.get('schema_version') != 1
            or finished.get('returncode') != 0 or not isinstance(finished.get('model'), dict)
            or not guard['deadline_monotonic'] >= guard['work_cutoff_monotonic'] >= cleanup['reaped_at_monotonic']
            or any(files._read(name) != value for name, value in documents.items())):
        raise ValueError('Campaign receipt recovery requires unchanged original guard and reaped reader proof')
    grant = readback_grant(opening, run_id, task, None)
    reply = {'recovery_activity_id': receipt_recovery_id(grant), 'recovery_receipt_sha256': identity(documents),
             'original_result': documents['readback-result']}
    return {**source, **receipt_recovery_proof(grant, reply)}, reply, guard, finished['model']


def verified_interrupted_read(files, grant):
    """Bind one original unsuccessful read and its completed child reap."""
    names = ('readback-attempt', 'readback-guard', 'readback-cleanup')
    documents = {name: files._read(name) for name in names}
    attempt, guard, cleanup = documents.values()
    activity = readback_id(grant)
    if (attempt is None or guard is None or cleanup is None or files._read('readback-result') is not None
            or attempt.keys() != {'grant', 'activity_id', 'worker'} or attempt['grant'] != grant
            or any(row.get('activity_id') != activity for row in documents.values())
            or guard.get('worker') != attempt['worker'] or not isinstance(guard.get('guard'), dict)):
        raise ValueError('Campaign re-observation requires its original unpublished read and guard')
    receipt = cleanup.get('receipt')
    clocks = (cleanup.get('reaped_at_monotonic'), guard.get('work_cutoff_monotonic'), guard.get('deadline_monotonic'))
    if (not isinstance(receipt, dict) or receipt.get('kind') != 'supervised-process-cleanup'
            or receipt.get('schema_version') != 1 or receipt.get('owner') != guard['guard']
            or receipt.get('model_waited') is not True or receipt.get('remaining_children') != []
            or receipt.get('returncode') != -signal.SIGKILL or not isinstance(receipt.get('model'), dict)
            or not all(type(clock) in (int, float) and math.isfinite(clock) for clock in clocks)
            or not 0 <= clocks[0] < clocks[1] < clocks[2]
            or any(files._read(name) != value for name, value in documents.items())):
        raise ValueError('Campaign re-observation requires its original interrupted reader and confirmed reap')
    return identity(documents), guard, receipt['model']


def verified_reobservation_source(files, opening, start, run_id, task):
    if not reobservation_task(task):
        raise ValueError('Campaign re-observation was not selected')
    grant = readback_grant(opening, run_id, task, None)
    interruption, _, _ = verified_interrupted_read(files, grant)
    attempt = files._read('reobservation-attempt')
    if attempt is None or attempt.get('interruption_sha256') != interruption:
        raise ValueError('Campaign re-observation differs from the original interrupted read')
    source = verified_source(files, opening, start, run_id, task, reobservation=True)
    return {**source, 'activity_id': readback_id(grant), 'reobservation_activity_id': source['activity_id'],
            'reobservation_interruption_sha256': interruption}


def assignment_wait(files, opening, start, run_id):
    task = recipient_task(opening)
    waiting = files.load_check(opening, start, run_id, task, waiting=True)
    if waiting is None:
        raise ValueError('Independent task requires the original waiting attempt')
    return waiting


def verify_wake_intent(files, opening, start, run_id, task, intent):
    if task is None:
        raise ValueError('Campaign recipient attempt lacks its declared task')
    if task == assignment_task(opening):
        waiting = check_receipt(assignment_wait(files, opening, start, run_id))
        expected = assignment_intent(opening, run_id, waiting)
        if intent != expected:
            raise ValueError('Independent task Activity differs from its original waiting receipt')
        return expected
    claimed = intent.get('source')
    if not isinstance(claimed, dict):
        raise ValueError('Campaign recipient attempt lacks its original result source')
    if claimed.get('kind') == 'manual_update':
        wait, terminal = manual_commands(files, opening, start, run_id, task)
        source = manual_wake_source(task, check_receipt(wait), check_receipt(terminal))
    elif 'recovery_activity_id' in claimed:
        source, _, _, _ = verified_receipt_recovery(files, opening, start, run_id, task)
    elif 'reobservation_activity_id' in claimed:
        source = verified_reobservation_source(files, opening, start, run_id, task)
    else:
        source = verified_source(files, opening, start, run_id, task)
    expected = wake_intent(opening, run_id, task, source)
    if intent != expected:
        raise ValueError('Campaign recipient attempt differs from its original result and deadline')
    return expected


def attempt_record(intent, native_run_id):
    boot, ticks = budget_clock._clock()
    wall = time.time_ns()
    if wall >= intent['expires_at'] * 10**9:
        raise RecipientBlocked('expired')
    return {'intent': intent, 'native_run_id': native_run_id, 'boot_id': boot, 'boottime_ns': ticks, 'wall_ns': wall}


class RecipientGate:
    def __init__(self, files, opening, start, result, attempt, *, sealing=False):
        self.files, self.opening, self.start, self.result, self.attempt = files, opening, start, result, attempt
        task = recipient_task(opening)
        if (task is None or start is None or not isinstance(attempt, dict)
                or attempt.keys() - {'slot_release'} != {'intent', 'native_run_id', 'boot_id', 'boottime_ns', 'wall_ns'}
                or not isinstance(attempt['intent'], dict) or not isinstance(attempt['native_run_id'], str)
                or not all(type(attempt[key]) is int and attempt[key] > 0 for key in ('boottime_ns', 'wall_ns'))):
            raise ValueError('Campaign recipient attempt lacks its original durable binding')
        run_id = attempt['intent'].get('run_id')
        if result is not None and result['run_id'] != run_id:
            raise ValueError('Campaign recipient attempt differs from the saved first Run')
        assigned = assignment_task(opening)
        self.independent = assigned is not None and attempt['intent'].get('task_id') == assigned['task_id']
        if self.independent:
            task = assigned
        self.intent = verify_wake_intent(files, opening, start, run_id, task, attempt['intent'])
        if attempt['intent'] != self.intent or attempt['wall_ns'] >= self.intent['expires_at'] * 10**9:
            raise ValueError('Campaign recipient attempt differs from its original source and deadline')
        self.declaration = task['recipient']
        self.binding = opening['assignment_binding' if self.independent else 'recipient_binding']
        slot = attempt.get('slot_release')
        if (assigned is None and 'slot_release' in attempt
                or assigned is not None and not sealing and not isinstance(slot, dict)):
            raise ValueError('Campaign recipient attempt has no original expert slot release')
        if isinstance(slot, dict):
            if self.independent:
                first = recipient_task(opening)['recipient']
                self.require_slot(slot, first['session_id'], first['parent_run_id'], opening['recipient_binding'])
            else:
                original = files._read(ASSIGNMENT_ATTEMPT)
                if original is None and slot != {'status': 'unclaimed'}:
                    raise ValueError('Campaign continuation lacks the independent task claim')
                if original is not None:
                    refused = slot == {'status': 'refused', 'attempt_sha256': identity(original)}
                    if refused and assignment_refusal(files, original) is None:
                        raise ValueError('Campaign continuation lacks the original independent task refusal')
                    if not refused:
                        self.require_slot(slot, assigned['recipient']['session_id'], original['native_run_id'],
                                          opening['assignment_binding'])
        self.reference = {'campaign': files.campaign, 'attempt_sha256': identity(attempt)}

    @staticmethod
    def require_slot(slot, session_id, run_id, binding):
        if (slot.keys() != {'session_id', 'run_id', 'request_sha256', 'context_digest', 'native_id'}
                or slot['session_id'] != session_id or slot['run_id'] != run_id
                or slot['context_digest'] != binding['context_digest'] or slot['native_id'] != binding['native_id']
                or not sha256(slot['request_sha256'])):
            raise ValueError('Campaign expert slot release names a different native turn')

    @classmethod
    def load(cls, home, project, reference):
        if (not isinstance(reference, dict) or reference.keys() != {'campaign', 'attempt_sha256'}
                or not sha256(reference['attempt_sha256'])):
            raise ValueError('Native turn has an invalid Campaign recipient reference')
        files = CampaignFiles(home, project, reference['campaign'])
        opening, start, result = files.load()
        attempt = files._read('recipient-attempt')
        if attempt is None or identity(attempt) != reference['attempt_sha256']:
            attempt = files._read(ASSIGNMENT_ATTEMPT) if opening is not None and assignment_task(opening) else None
        if opening is None or attempt is None or identity(attempt) != reference['attempt_sha256']:
            raise ValueError('Native turn has no matching original Campaign recipient attempt')
        return cls(files, opening, start, result, attempt)

    def remaining(self):
        boot, ticks = budget_clock._clock()
        if boot != self.attempt['boot_id'] or ticks < self.attempt['boottime_ns']:
            raise ValueError('Original Campaign recipient clock is unavailable after a host or boot change')
        expiry = self.intent['expires_at'] * 10**9
        elapsed = ticks - self.attempt['boottime_ns']
        wall = time.time_ns()
        if abs(wall - self.attempt['wall_ns'] - elapsed) > 5 * 10**9:
            raise ValueError('Original Campaign recipient clock cannot be renewed after a clock discontinuity')
        return (expiry - max(wall, self.attempt['wall_ns'] + elapsed)) / 10**9

    def blocker(self):
        stop, _, _ = self.files.load_stop(self.opening, self.start, self.result)
        if stop is not None:
            if stop['run_id'] != self.intent['run_id']:
                raise ValueError('Campaign STOP belongs to another Run')
            return 'stopped'
        return 'expired' if self.remaining() <= 0 else None

    def require_open(self, *, native_clock=None, native_timeout=None):
        reason = self.blocker()
        if reason is not None:
            raise RecipientBlocked(reason)
        if native_clock is not None and budget_clock.remaining(native_clock, native_timeout) <= 0:
            raise RecipientBlocked('native_turn_expired')

    @contextmanager
    def admission(self, *, native_clock=None, native_timeout=None):
        with ExitStack() as stack:
            while True:
                self.require_open(native_clock=native_clock, native_timeout=native_timeout)
                try:
                    stack.enter_context(file_lock(self.files.lock, blocking=False))
                except BlockingIOError:
                    time.sleep(min(.025, max(0.0, self.remaining())))
                else:
                    break
            self.require_open(native_clock=native_clock, native_timeout=native_timeout)
            yield

    def submission(self):
        selected = self.declaration
        return {'parent_run': selected['parent_run_id'], 'prompt': selected['prompt'],
                'expected_revision': self.opening['project_revision'], 'timeout': selected['timeout_seconds'],
                'intent_id': selected['intent_id'], 'campaign_recipient': self.reference}

    def require_turn_context(self, digest, role):
        if digest != self.binding['context_digest'] or role != self.binding['role']:
            raise ValueError(_TURN_MISMATCH)

    def require_turn_identity(self, ident, session, digest, role, native_id, submitted):
        self.require_turn_context(digest, role)
        if (ident != self.attempt['native_run_id'] or session != self.declaration['session_id']
                or native_id != self.binding['native_id'] or submitted != self.submission()):
            raise ValueError(_TURN_MISMATCH)

    def require_turn(self, state, ident, session, digest, role, native_id, submitted):
        self.require_turn_identity(ident, session, digest, role, native_id, submitted)
        self.require_authority(state)

    def require_authority(self, state):
        project = require_check_project(state, self.opening)
        if assignment_task(self.opening) is not None:
            from ergora.configuration.projects import native_authority_revision

            role = self.binding['role']
            assignee = self.opening['plan']['assignment']['assignee']
            if assignee != {'role': role, 'generation': native_authority_revision(project, role)}:
                raise ValueError('Original Campaign expert permission generation changed')

    @contextmanager
    def leased_payload(self, clock, timeout):
        import fcntl

        self.require_open(native_clock=clock, native_timeout=timeout)
        installed = os.open(self.binding['payload_executable'], os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        with os.fdopen(installed, 'rb') as original:
            # A kernel write-open break terminates this inert helper. Nothing can release
            # the lease early and then use stale approved bytes for a new exec.
            fcntl.fcntl(installed, fcntl.F_SETOWN, os.getpid())
            fcntl.fcntl(installed, _SET_LEASE_SIGNAL, signal.SIGKILL)
            try:
                fcntl.fcntl(installed, _SET_LEASE, fcntl.F_RDLCK)
            except OSError as error:
                raise ValueError('Cannot lease the frozen installed Codex executable for protected launch') from error
            stat = os.fstat(original.fileno())
            if (stat.st_dev, stat.st_ino, stat.st_size) != (self.binding['device'], self.binding['inode'], self.binding['size']):
                raise ValueError('Campaign Codex recipient executable no longer matches the frozen installation')
            digest = hashlib.sha256()
            for data in iter(lambda: original.read(1024 * 1024), b''):
                self.require_open(native_clock=clock, native_timeout=timeout)
                digest.update(data)
            if digest.hexdigest() != self.binding['payload_sha256']:
                raise ValueError('Campaign Codex recipient executable differs from the approved bytes')
            yield installed

    def command_prefix(self, run_id, lock_fd):
        return [sys.executable, '-P', '-m', 'ergora.campaigns.recipient_gate', str(self.files.home),
                self.files.project, run_id, str(lock_fd)]

    def payload_identity(self):
        return self.binding['device'], self.binding['inode']


def assignment_refusal(files, attempt):
    refusal = files._read(ASSIGNMENT_REFUSAL)
    if refusal is not None and (refusal.keys() != {'attempt_sha256', 'reason'}
            or refusal['attempt_sha256'] != identity(attempt)
            or refusal['reason'] not in ('stale_parent', 'session_slot_timeout', 'stopped', 'expired',
                                         'native_turn_expired', 'recipient_authority_revoked')):
        raise ValueError('Campaign independent task refusal differs from its original claim')
    return refusal


def stopped_receipt(native):
    run = native['run']
    return (native['dispatch'] not in ('unrecorded', 'incomplete') and run is not None
            and run.get('execution_stopped') is True and run['status'] != 'unknown')


def _exec(home, project, ident, lock_fd, argv):
    import fcntl

    state = State(Path(home), read_only=True)
    saved = native_sources.record(state, project, ident)
    folder = native_sources.turn_folder(state, ident)
    request = native_sources.packet(folder, 'request.json')
    owner = native_sources.packet(folder / 'owner')
    attempt = native_sources.packet(folder / 'attempt')
    if (native_sources.sha(request) != saved['request_sha256'] or owner['request_sha256'] != saved['request_sha256']
            or attempt['request_sha256'] != saved['request_sha256'] or owner['identity'] != processes.identity(os.getppid())):
        raise ValueError('Recipient launch requires the exact native request and original supervision process')
    gate = RecipientGate.load(state.root, project, request['submitted']['campaign_recipient'])
    gate.require_turn(state, ident, request['session']['id'], request['context_digest'], saved['role'],
                      request['native_id'], request['submitted'])
    lock = (state.root / 'runs' / (request['session']['id'] + '.session.lock')).stat(follow_symlinks=False)
    inherited = os.fstat(lock_fd)
    if (inherited.st_dev, inherited.st_ino) != (lock.st_dev, lock.st_ino):
        raise ValueError('Recipient launch lacks the original inherited native session slot')
    if not argv or argv[0] != gate.binding['source_executable'] or argv[-3:] != ['resume', request['native_id'], '-']:
        raise ValueError('Recipient launch must consume the original native Codex resume command')
    if os.execve not in os.supports_fd:
        raise ValueError('Campaign recipient requires executable descriptor handoff on Linux')
    budget_clock.validate(request['clock'], request['timeout'])
    native_budget = {'native_clock': request['clock'], 'native_timeout': request['timeout']}
    with gate.leased_payload(request['clock'], request['timeout']) as payload:
        if fcntl.fcntl(payload, _GET_LEASE) != fcntl.F_RDLCK:
            raise ValueError('Campaign recipient executable lease was broken before launch')
        with gate.admission(**native_budget):
            # Both the local Campaign STOP and a direct native STOP use this lock.
            if assignment_task(gate.opening) is not None:
                gate.require_authority(state)
            if (folder / 'stop').exists():
                raise RecipientBlocked('stopped')
            original_path = Path(gate.binding['payload_executable']).stat(follow_symlinks=False)
            if ((original_path.st_dev, original_path.st_ino) != gate.payload_identity()
                    or fcntl.fcntl(payload, _GET_LEASE) != fcntl.F_RDLCK):
                raise ValueError('Campaign recipient executable path or lease changed before launch')
            gate.require_open(**native_budget)
            os.execve(payload, [gate.binding['payload_executable'], *argv[1:]], os.environ)


if __name__ == '__main__':
    try:
        _exec(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5:])
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise SystemExit(str(error)) from error
