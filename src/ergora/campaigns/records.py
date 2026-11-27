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
ROLLOVER_UPDATE_PREFIX = 'ergora-campaign-rollover:'
FIXED_CHECK_LOCATOR = ('operation_id', 'request_file_sha256', 'job_sha256', 'candidate_sha')
FIXED_CHECK_TERMINAL = ('receipt_sha256', 'fixed_results_sha256')
FIXED_TASK_LOCATOR = (*FIXED_CHECK_LOCATOR, 'project_revision', 'job_id', 'authorization_sha256', 'verification_sha256')
FIXED_TASK_SOURCE = (*FIXED_TASK_LOCATOR, *FIXED_CHECK_TERMINAL)
PENDING_JOB_STATES = ('queued', 'attempted')
READBACK_CLEANUP_SECONDS = 0.8
READBACK_ACTIVITY = 'ergora_campaign_fixed_check_readback'
TRAINING_READBACK_ACTIVITY = 'ergora_campaign_training_full_result_readback'
TRAINING_RESULT_SOURCE = 'training_full_result'
FULL_RESULT_RECOVERY_ACTIVITY = 'ergora_campaign_training_full_result_recover_receipt'
FULL_RESULT_REOBSERVATION_ACTIVITY = 'ergora_campaign_training_full_result_reobserve'
TRAINING_RESULT_DIGESTS = ('native_result_sha256', 'reap_record_sha256', 'terminal_output_sha256',
                           'gate_report_sha256', 'evidence_sha256', 'tracking_attempt_sha256')
TRAINING_SCREEN_ACTIVITY = 'ergora_campaign_training_screen_result_readback'
TRAINING_SCREEN_SOURCE = 'training_screen_result'
TRAINING_SCREEN_DIGESTS = ('native_result_sha256', 'screen_result_sha256', 'terminal_output_sha256',
                           'reap_record_sha256', 'clock_sha256')
TRAINING_SCREEN_PROOF = ('native_result_state', 'decision', 'performance_state', 'verification_experiment_id',
                         'full_execution_authorized', 'diagnostics')
TRAINING_GPU_RELEASE_ACTIVITY = 'ergora_campaign_training_gpu_release_readback'
TRAINING_GPU_RELEASE_SOURCE = 'training_gpu_release'
RELEASE_RECOVERY_ACTIVITY = 'ergora_campaign_recover_training_gpu_release'
READBACK_ALREADY_ADMITTED = 'readback_already_admitted'
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


def project_selection(state, project, revision, *, plan=None):
    """Read the scheduler and published registration for the approved project revision."""
    from ergora.configuration import projects, registrations

    if project['revision'] != revision:
        raise ValueError('Project revision changed; use the original approved revision before dispatch')
    if (plan is not None and training_readback_task(readback_task({'plan': plan}))
            and 'training-optimization' not in project.get('registration', {}).get('definition', {}).get('templates', ())):
        raise ValueError('Campaign training result requires the selected registered training project')
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
    selected = project_selection(state, project, opening['project_revision'], plan=opening['plan'])
    if any(opening[key] != value for key, value in selected.items()):
        raise ValueError('Original project registration or scheduler changed before task observation')
    return project


def validate_plan(plan):
    required = {'schema_version', 'goal', 'acceptance', 'baseline_commit', 'evidence_format', 'limits'}
    if (not isinstance(plan, dict) or set(plan) - {'tasks', 'rollover'} != required
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
        validate_tasks(plan['tasks'])
        task = readback_task({'plan': plan})
        if task is not None and task['readback']['deadline_at'] > limits['expires_at']:
            raise ValueError('Campaign readback window exceeds the original expiry')
    if 'rollover' in plan and (plan['rollover'] is not True or rollover_task({'plan': plan}) is None):
        raise ValueError('Campaign rollover requires one manually observed pending fixed check')
    # Also rejects unpaired Unicode surrogates before an intent can be saved.
    identity(plan)


def validate_tasks(tasks):
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= MAX_FIXED_TASKS:
        raise ValueError(f'Campaign plan requires 1–{MAX_FIXED_TASKS} original tasks when configured')
    dependencies = {}
    scheduled = False
    for task in tasks:
        optional = {'readback', 'recipient', 'wake_on_observe', 'recover_release_receipt', 'recover_full_result_receipt',
                    'reobserve_full_result_after_reader_loss'}
        if not isinstance(task, dict) or task.keys() - optional != {'task_id', 'depends_on', 'source'}:
            raise ValueError('Campaign task requires task_id, depends_on and an exact source')
        task_id, parents, source = task['task_id'], task['depends_on'], task['source']
        if not safe_id(task_id) or task_id in dependencies:
            raise ValueError('Campaign task requires a unique safe ID')
        if not isinstance(parents, list) or not all(safe_id(item) for item in parents) or len(set(parents)) != len(parents):
            raise ValueError('Campaign task dependencies require distinct safe IDs')
        if training_readback_task(task):
            source_keys = {'kind', 'locator'}
            if 'wait_for_live' in source:
                if source['kind'] != TRAINING_RESULT_SOURCE or source['wait_for_live'] is not True:
                    raise ValueError('Campaign live wait requires an explicitly selected managed full training result')
                source_keys.add('wait_for_live')
            if (parents or 'readback' not in task or 'wake_on_observe' in task
                    or source.keys() != source_keys or not isinstance(source['locator'], dict)):
                raise ValueError('Campaign training result requires one root task with a guarded readback and exact locator')
            try:
                training_readback_action(task)
            except TypeError as error:
                raise ValueError('Campaign training result requires the complete original locator') from error
            pending = True
        else:
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
        if 'wake_on_observe' in task and (task['wake_on_observe'] is not True or 'recipient' not in task):
            raise ValueError('Campaign manual wake requires an explicitly enabled original timed recipient')
        if 'recover_release_receipt' in task and (task['recover_release_receipt'] is not True
                or not training_gpu_release_task(task) or 'recipient' not in task):
            raise ValueError('Campaign receipt recovery requires the selected original GPU release and recipient')
        if 'recover_full_result_receipt' in task and (task['recover_full_result_receipt'] is not True
                or not training_readback_task(task) or source['kind'] != TRAINING_RESULT_SOURCE or 'recipient' not in task):
            raise ValueError('Campaign receipt recovery requires the selected original full training result and recipient')
        if 'reobserve_full_result_after_reader_loss' in task and (not reobservation_task(task)
                or not training_readback_task(task) or source['kind'] != TRAINING_RESULT_SOURCE
                or source.get('wait_for_live') is not True or 'recipient' not in task
                or 'recover_full_result_receipt' in task):
            raise ValueError('Campaign re-observation requires a selected live full-result wait and recipient')
        dependencies[task_id] = parents
    if any(parent not in dependencies for parents in dependencies.values() for parent in parents):
        raise ValueError('Campaign task dependency is absent from the frozen plan')
    try:
        TopologicalSorter(dependencies).prepare()
    except CycleError as error:
        raise ValueError('Campaign task dependencies contain a cycle') from error


def tasks_by_id(opening):
    return {task['task_id']: task for task in opening['plan'].get('tasks', ())}


def training_readback_task(task):
    return task is not None and isinstance(task['source'], dict) and task['source'].get('kind') in (
        TRAINING_RESULT_SOURCE, TRAINING_SCREEN_SOURCE, TRAINING_GPU_RELEASE_SOURCE)


def training_screen_task(task):
    return training_readback_task(task) and task['source']['kind'] == TRAINING_SCREEN_SOURCE


def training_gpu_release_task(task):
    return training_readback_task(task) and task['source']['kind'] == TRAINING_GPU_RELEASE_SOURCE


def training_readback_action(task):
    if training_gpu_release_task(task):
        from ergora.runtime.action_observations import TrainingGpuRelease

        return TrainingGpuRelease(**task['source']['locator'])
    if training_screen_task(task):
        from ergora.runtime.action_observations import TrainingScreenDecision

        return TrainingScreenDecision(**task['source']['locator'])
    from ergora.runtime.action_observations import TrainingFullResult

    return TrainingFullResult(**task['source']['locator'], wait_for_live=task['source'].get('wait_for_live', False))


def has_pending_checks(opening):
    return any(task['source'].get('pending') is True for task in tasks_by_id(opening).values())


def rollover_task(opening):
    plan = opening['plan']
    tasks = plan.get('tasks', ())
    if plan.get('rollover') is True and len(tasks) == 1:
        task = tasks[0]
        if task['source'].get('pending') is True and 'readback' not in task and 'recipient' not in task:
            return task
    return None


def readback_task(opening):
    return next((task for task in opening['plan'].get('tasks', ()) if 'readback' in task), None)


def readback_activity(task):
    if training_gpu_release_task(task):
        return TRAINING_GPU_RELEASE_ACTIVITY
    if training_screen_task(task):
        return TRAINING_SCREEN_ACTIVITY
    return TRAINING_READBACK_ACTIVITY if training_readback_task(task) else READBACK_ACTIVITY


def local_readback_stop(opening):
    return recipient_task(opening) is not None or training_readback_task(readback_task(opening))


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


def manual_wake_source(task, waiting, receipt):
    if (task.get('wake_on_observe') is not True or waiting is None or receipt is None
            or waiting.get('decision') != 'waiting_job' or receipt.get('decision') != 'observed'
            or waiting.get('task_id') != task['task_id'] or receipt.get('task_id') != task['task_id']
            or waiting.get('run_id') != receipt.get('run_id')
            or receipt.get('job', {}).get('waiting_receipt_sha256') != identity(waiting)):
        raise ValueError('Campaign manual wake requires its original accepted wait and terminal Update')
    job = receipt['job']
    return {'kind': 'manual_update', 'update_id': receipt['update_id'],
            'waiting_receipt_sha256': job['waiting_receipt_sha256'], 'observation_sha256': receipt['observation_sha256'],
            **{key: job[key] for key in FIXED_CHECK_TERMINAL}}


def readback_ready_tasks(task, readback):
    if (task is not None and (task.get('wake_on_observe') is True or training_readback_task(task))
            and readback.get('status') == 'available'):
        return {task['task_id']}
    return set()


def same_check_observation(first, second):
    return all(first[key] == second.get(key) for key in ('observation_sha256', *FIXED_CHECK_TERMINAL))


def readback_grant(opening, run_id, task, waiting):
    common = {'opening_sha256': identity(opening), 'run_id': run_id, 'task_id': task['task_id']}
    if training_readback_task(task):
        if task['source']['kind'] != TRAINING_RESULT_SOURCE:
            common['source_kind'] = task['source']['kind']
        return {**common, 'source_sha256': identity(task['source']), **task['readback']}
    return {**common, 'waiting_receipt_sha256': identity(waiting), **task['readback']}


def readback_id(grant):
    match grant.get('source_kind'):
        case 'training_gpu_release':
            return 'training-gpu-release-readback:' + identity(grant)
        case 'training_screen_result':
            return 'training-screen-result-readback:' + identity(grant)
    prefix = 'training-full-result-readback:' if 'source_sha256' in grant else 'fixed-check-readback:'
    return prefix + identity(grant)


def receipt_recovery_activity(task):
    if task is not None:
        if task.get('recover_release_receipt') is True:
            return RELEASE_RECOVERY_ACTIVITY
        if task.get('recover_full_result_receipt') is True:
            return FULL_RESULT_RECOVERY_ACTIVITY


def receipt_recovery_id(grant):
    prefix = ('training-gpu-release-recovery:' if grant.get('source_kind') == TRAINING_GPU_RELEASE_SOURCE else
              'training-full-result-recovery:')
    return prefix + identity(grant)


def receipt_recovery_proof(grant, reply):
    if (not isinstance(reply, dict)
            or reply.keys() != {'recovery_activity_id', 'recovery_receipt_sha256', 'original_result'}
            or reply['recovery_activity_id'] != receipt_recovery_id(grant)
            or not sha256(reply['recovery_receipt_sha256'])):
        raise ValueError('Campaign receipt recovery differs from the original read grant')
    return {field: reply[field] for field in ('recovery_activity_id', 'recovery_receipt_sha256')}


def reobservation_task(task):
    return task is not None and task.get('reobserve_full_result_after_reader_loss') is True


def reobservation_id(grant):
    return 'training-full-result-reobservation:' + identity(grant)


def readback_followup_activity(task):
    return FULL_RESULT_REOBSERVATION_ACTIVITY if reobservation_task(task) else receipt_recovery_activity(task)


def readback_followup_id(task, grant):
    return reobservation_id(grant) if reobservation_task(task) else receipt_recovery_id(grant)


def readback_followup_result(task, grant, reply):
    if not reobservation_task(task):
        return receipt_recovery_proof(grant, reply), reply['original_result'], readback_id(grant)
    activity_id = reobservation_id(grant)
    fields = ('reobservation_activity_id', 'reobservation_interruption_sha256')
    if (not isinstance(reply, dict) or reply.keys() != {*fields, 'reobserved_result'}
            or reply['reobservation_activity_id'] != activity_id or not sha256(reply['reobservation_interruption_sha256'])):
        raise ValueError('Campaign re-observation differs from the original read grant')
    return {field: reply[field] for field in fields}, reply['reobserved_result'], activity_id


def readback_reference(grant):
    field = 'source_sha256' if 'source_sha256' in grant else 'waiting_receipt_sha256'
    if 'source_kind' in grant:
        return {field: grant[field], 'source_kind': grant['source_kind']}
    return {field: grant[field]}


def _training_lease_matches(observation, attempt_sha256):
    # The training reader rechecks the original owner. The Campaign only
    # preserves that observation with its own original result and attempt.
    lease = observation['local_gpu_lease']
    if lease is None:
        return True
    if (not isinstance(lease, dict) or lease.get('read_only') is not True or not safe_id(lease.get('status'))
            or lease.get('attempt_sha256', attempt_sha256) != attempt_sha256):
        return False
    if lease['status'] == 'released':
        return (lease.get('attempt_sha256') == attempt_sha256 and isinstance(lease.get('release_ref'), dict)
                and safe_id(lease.get('session_id'))
                and all(sha256(lease.get(key)) for key in ('lease_id', 'request_id', 'request_sha256')))
    return True


def _training_gpu_release_matches(observation, locator):
    lease = observation.get('local_gpu_lease')
    if not isinstance(lease, dict) or lease.get('status') != 'released':
        return False
    if (not _training_lease_matches(observation, locator['attempt_sha256'])
            or any(lease.get(key) != locator[key] for key in ('session_id', 'lease_id'))):
        return False
    release = lease['release_ref']
    proof = release.get('proof_ref')
    return (type(release.get('sequence')) is int and release['sequence'] > 0
            and isinstance(proof, dict) and sha256(proof.get('raw_sha256'))
            and proof.get('relative_path') == f'proofs/{locator["lease_id"]}/stopped.json')


def _screen_diagnostic_ref(ref):
    return ref is None or (isinstance(ref, dict) and ref.keys() == {'path', 'sha256', 'bytes'}
                           and isinstance(ref['path'], str) and bool(ref['path'])
                           and sha256(ref['sha256']) and type(ref['bytes']) is int and ref['bytes'] >= 0)


def _screen_diagnostics_match(diagnostics):
    if (not isinstance(diagnostics, dict)
            or diagnostics.keys() != {'checks', 'checks_not_run', 'first_failure_ref', 'profile_receipt_ref'}
            or not isinstance(diagnostics['checks'], list) or not isinstance(diagnostics['checks_not_run'], list)):
        return False
    return (all(isinstance(check, dict) and check.keys() == {'id', 'kind', 'status', 'contract_sha256'}
                and isinstance(check['id'], str) and bool(check['id']) and check['kind'] in ('finite', 'behavior')
                and check['status'] in ('PASS', 'FAIL') and sha256(check['contract_sha256'])
                for check in diagnostics['checks'])
            and all(isinstance(check_id, str) and bool(check_id) for check_id in diagnostics['checks_not_run'])
            and _screen_diagnostic_ref(diagnostics['first_failure_ref'])
            and _screen_diagnostic_ref(diagnostics['profile_receipt_ref']))


def _screen_decision_matches(observation, locator):
    state, performance, decision = (observation.get(key) for key in ('native_result_state', 'performance_state', 'decision'))
    verdict = (performance, decision)
    valid = (state == 'SCREEN_REJECTED' and verdict == ('unavailable', 'rejected')
             or state == 'SCREEN_COMPLETED' and verdict in (
                 ('promising', 'promising'), ('no_gain', 'stop_direction'),
                 ('below_noise', 'stop_direction'), ('unavailable', 'inconclusive')))
    followup = observation.get('verification_experiment_id')
    return (valid and observation.get('full_execution_authorized') is False
            and isinstance(followup, str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', followup) is not None
            and followup != locator['experiment_id'] and _screen_diagnostics_match(observation.get('diagnostics')))


def readback_result(opening, task, activity_id, result):
    if result['activity_id'] != activity_id or not sha256(result['reader_cleanup_sha256']):
        raise ValueError('Original training readback result identity differs' if training_readback_task(task) else
                         'Original fixed-check readback result identity differs')
    observation = result['observation']
    if not training_readback_task(task):
        return original_check_evidence(opening, task, observation)
    locator = task['source']['locator']
    screen = training_screen_task(task)
    release = training_gpu_release_task(task)
    error = ('Campaign readback requires the exact accepted original GPU release' if release else
             'Campaign readback requires the exact verified original screen decision' if screen else
             'Campaign readback requires the exact successful original full training result')
    if (not isinstance(observation, dict) or observation.get('status') != 'verified'
            or observation.get('project') != opening['project']
            or type(observation.get('project_revision')) is not int
            or observation['project_revision'] != opening['project_revision']
            or observation.get('registration_sha256') != opening['registration']['sha256']
            or observation.get('locator') != locator):
        raise ValueError(error)
    if release:
        if not _training_gpu_release_matches(observation, locator):
            raise ValueError(error)
        return identity(observation), {'status': 'succeeded', 'local_gpu_lease': observation['local_gpu_lease']}
    digests = TRAINING_SCREEN_DIGESTS if screen else TRAINING_RESULT_DIGESTS
    if (not all(sha256(observation.get(key)) for key in digests)
            or (not _screen_decision_matches(observation, locator) if screen else observation.get('native_result_state') != 'SUCCEEDED')
            or not _training_lease_matches(observation, locator['attempt_sha256'])):
        raise ValueError(error)
    fields = (*digests, *TRAINING_SCREEN_PROOF) if screen else digests
    proof = {key: observation[key] for key in (*fields, 'local_gpu_lease')}
    return identity(observation), {'status': 'succeeded', **proof}


def readback_proof(evidence, job, result):
    return {'observation_sha256': evidence, 'reader_cleanup_sha256': result['reader_cleanup_sha256'],
            **{key: value for key, value in job.items() if key != 'status'}}


def checked_readback(opening, run_id, waits, observation):
    task = readback_task(opening)
    if not isinstance(observation, dict):
        raise ValueError('Campaign readback is missing its original state')
    status = observation.get('status')
    if observation == {'status': 'not_armed'}:
        return observation
    waiting = None if waits is None else waits.get(task['task_id'])
    training = training_readback_task(task)
    screen = training_screen_task(task)
    release = training_gpu_release_task(task)
    grant = readback_grant(opening, run_id, task, waiting)
    reference = readback_reference(grant)
    fields = {'status', 'activity_id', *reference}
    if ((waiting is None and not training) or any(observation.get(key) != value for key, value in reference.items())
            or observation.get('activity_id') != readback_id(grant)):
        raise ValueError('Campaign readback differs from its original training grant and window' if training else
                         'Campaign readback differs from its original wait and window')
    if status == 'available':
        source_digests = (() if release else TRAINING_SCREEN_DIGESTS if screen else
                          TRAINING_RESULT_DIGESTS if training else FIXED_CHECK_TERMINAL)
        digests = {*source_digests, 'observation_sha256', 'reader_cleanup_sha256'}
        proof = digests | {'local_gpu_lease'} if training else digests
        if screen:
            proof = proof.union(TRAINING_SCREEN_PROOF)
        if 'recovery_activity_id' in observation:
            if (receipt_recovery_activity(task) is None
                    or observation['recovery_activity_id'] != receipt_recovery_id(grant)):
                raise ValueError('Campaign receipt recovery differs from the original read grant')
            fields.add('recovery_activity_id')
            digests.add('recovery_receipt_sha256')
            proof.add('recovery_receipt_sha256')
        if 'reobservation_activity_id' in observation:
            if (not reobservation_task(task) or observation['reobservation_activity_id'] != reobservation_id(grant)):
                raise ValueError('Campaign re-observation differs from the original read grant')
            fields.add('reobservation_activity_id')
            digests.add('reobservation_interruption_sha256')
            proof.add('reobservation_interruption_sha256')
        if (observation.keys() == fields | proof and all(sha256(observation[key]) for key in digests)
                and (not screen or _screen_decision_matches(observation, task['source']['locator']))
                and (not release or _training_gpu_release_matches(observation, task['source']['locator']))
                and (not training or release or _training_lease_matches(observation, task['source']['locator']['attempt_sha256']))):
            return observation
    elif status == 'unknown':
        if observation.keys() == fields | {'reason'} and observation['reason'] in (
                'campaign_closed', 'read_window_expired', 'original_read_unavailable', 'original_still_pending',
                'task_already_observed', 'contradictory_evidence'):
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
                or (start_result is not None and start_result['run_id'] != run_id and rollover_task(opening) is None)
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
        """Read saved attempts locally. The online owner verifies any successor authority."""
        commands = []
        update_ids = set()
        for task in tasks_by_id(opening).values():
            stages = (False, True) if task['source'].get('pending') is True else (False,)
            for waiting in stages:
                selected_run = run_id if waiting or rollover_task(opening) is None else None
                command = self.load_check(opening, start_attempt, selected_run, task, waiting=waiting)
                if command is None:
                    continue
                update_id = command['attempt']['update_id']
                if update_id in update_ids:
                    raise ValueError('Saved campaign task attempts share an original Update ID')
                update_ids.add(update_id)
                if run_id is None or rollover_task(opening) is None:
                    run_id = command['intent']['run_id']
                commands.append(command)
        return run_id, commands

    def load_rollover(self, opening, start_attempt, first_run_id):
        command = self._read('rollover-command')
        if command is not None:
            validate_rollover_command(opening, identity(start_attempt), first_run_id, command)
        return command

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


def rollover_intent(opening, start_attempt_sha256, run_id, waiting_sha256):
    return {**_update_intent(opening, start_attempt_sha256, run_id, 'rollover'),
            'waiting_receipt_sha256': waiting_sha256}


def validate_rollover_command(opening, start_attempt_sha256, run_id, command):
    if (rollover_task(opening) is None or not uuid_text(run_id) or not isinstance(command, dict)
            or command.keys() != {'intent', 'attempt'}):
        raise ValueError('Campaign rollover requires the saved original first Run and waiting task')
    intent, attempt = command['intent'], command['attempt']
    if not isinstance(intent, dict) or not isinstance(attempt, dict):
        raise ValueError('Campaign rollover requires the complete original command')
    waiting_sha = intent.get('waiting_receipt_sha256')
    update_id = attempt.get('update_id')
    if (not sha256(waiting_sha)
            or identity(intent) != identity(rollover_intent(opening, start_attempt_sha256, run_id, waiting_sha))
            or not isinstance(update_id, str) or not update_id.startswith(ROLLOVER_UPDATE_PREFIX)
            or not uuid_text(update_id[len(ROLLOVER_UPDATE_PREFIX):])
            or identity(attempt) != identity(update_attempt(intent, update_id))):
        raise ValueError('Campaign rollover command differs from its original Run, wait or Update attempt')


def require_rollover_receipt(intent, attempt, receipt):
    if identity(receipt) != identity(update_receipt(intent, attempt, 'committed')):
        raise ValueError('Campaign rollover receipt differs from its exact original Update')
    return receipt


def rollover_checkpoint(opening, start_attempt_sha256, first_run_id, waiting, command):
    return {'schema_version': 1, 'opening_sha256': identity(opening), 'start_attempt_sha256': start_attempt_sha256,
            'predecessor_run_id': first_run_id, 'waiting_receipt': waiting, 'rollover_command': command}


def restore_rollover(opening, start_attempt_sha256, first_run_id, checkpoint):
    task = rollover_task(opening)
    if (task is None or not isinstance(checkpoint, dict)
            or checkpoint.keys() != {'schema_version', 'opening_sha256', 'start_attempt_sha256',
                                     'predecessor_run_id', 'waiting_receipt', 'rollover_command'}):
        raise ValueError('Campaign successor lacks its original rollover checkpoint')
    waiting, command = checkpoint['waiting_receipt'], checkpoint['rollover_command']
    validate_rollover_command(opening, start_attempt_sha256, first_run_id, command)
    fixed_task_state(opening, start_attempt_sha256, first_run_id, {}, {task['task_id']: waiting})
    exact = rollover_checkpoint(opening, start_attempt_sha256, first_run_id, waiting, command)
    if (identity(checkpoint) != identity(exact)
            or identity(waiting) != command['intent']['waiting_receipt_sha256']):
        raise ValueError('Campaign rollover checkpoint differs from its original grant or waiting receipt')
    return {task['task_id']: waiting}


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
    if not safe_id(task_id) or task_id not in tasks_by_id(opening) or not sha256(evidence):
        raise ValueError('Campaign check intent does not bind the original opening, task and first Run')
    task = tasks_by_id(opening)[task_id]
    if training_readback_task(task):
        raise ValueError('Campaign training result admits only its guarded readback')
    _validate_check_job(task, job)
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


def fixed_task_state(opening, start_attempt_sha256, run_id, observations, waits=None, *, waiting_run=None,
                     readback=None):
    tasks = tasks_by_id(opening)
    waits = {} if waits is None else waits
    if not isinstance(observations, dict) or set(observations) - set(tasks):
        raise ValueError('Campaign task state differs from the original plan task set')
    selected = readback_task(opening)
    automatic = readback_ready_tasks(selected, readback or {})
    ready = observations.keys() | automatic
    for task_id in automatic:
        if (not set(tasks[task_id]['depends_on']) <= ready
                or (task_id not in waits and not training_readback_task(tasks[task_id]))):
            raise ValueError('Campaign guarded result lacks its original wait or ready dependencies')
    for expected, receipts in (('observed', observations), ('waiting_job', waits)):
        if not isinstance(receipts, dict) or set(receipts) - set(tasks):
            raise ValueError('Campaign task state differs from the original plan task set')
        for task_id, receipt in receipts.items():
            if (not isinstance(receipt, dict) or receipt.get('decision') != expected
                    or not set(tasks[task_id]['depends_on']) <= ready):
                raise ValueError('Campaign task receipt differs from its original stage or dependencies')
            job = receipt.get('job')
            _validate_check_job(tasks[task_id], job)
            if expected == 'observed' and job is not None:
                wait = waits.get(task_id)
                if job.get('waiting_receipt_sha256') != (identity(wait) if wait is not None else None):
                    raise ValueError('Campaign terminal check differs from its original waiting receipt')
                if task_id in automatic and not same_check_observation(
                        readback, {'observation_sha256': receipt.get('observation_sha256'), **job}):
                    raise ValueError('Campaign original fixed-check observations contradict each other')
            receipt_run = waiting_run if waiting_run is not None and expected == 'waiting_job' else run_id
            intent = check_intent(opening, start_attempt_sha256, receipt_run, task_id,
                                  receipt.get('observation_sha256'), job=job)
            attempt = update_attempt(intent, receipt.get('update_id'))
            validate_check_command(opening, start_attempt_sha256, receipt_run, {'intent': intent, 'attempt': attempt})
            require_check_receipt(intent, attempt, receipt)
    views = {}
    for task_id, task in tasks.items():
        status = ('observed' if task_id in ready else 'waiting_job'
                  if task_id in waits or training_readback_task(task) else
                  'ready' if set(task['depends_on']) <= ready else 'waiting_dependencies')
        view = {**task, 'status': status, 'receipt': observations.get(task_id)}
        if task['source'].get('pending') is True:
            view['waiting_receipt'] = waits.get(task_id)
        views[task_id] = view
    return views
