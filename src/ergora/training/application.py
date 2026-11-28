"""Project-scoped native training observations and explicit local/control operations."""

from functools import partial
from pathlib import Path
import re

import ergora.training.native as training_native
import ergora.configuration.registrations as registrations
from ergora.runtime import action_observations
from ergora.storage.state import State


def preview_baseline(state: State, project_id: str, baseline: dict) -> dict:
    """Validate the entire baseline with the native owner; leave its registry untouched."""
    return training_native.training_setup(_project(state, project_id), state.root, 'preview-baseline', {'baseline': baseline})


def initialize_baseline(state: State, project_id: str, baseline: dict, expected_revision: int,
                        baseline_sha256: str) -> dict:
    """Confirm one baseline; retrying identical content never replaces a different one."""
    return _setup(state, project_id, expected_revision, 'init-baseline',
                  {'baseline': baseline, 'baseline_sha256': baseline_sha256}, training_native.training_setup)


def preview_runner(state: State, project_id: str, runner: dict) -> dict:
    """Use the native registrar in temporary configuration, without running argv."""
    return training_native.training_setup(_project(state, project_id), state.root, 'preview-runner', {'runner': runner})


def register_runner(state: State, project_id: str, runner: dict, expected_revision: int,
                    runner_sha256: str) -> dict:
    """Confirm one project-bound native runner; existing IDs remain immutable."""
    return _setup(state, project_id, expected_revision, 'register-runner',
                  {'runner': runner, 'runner_sha256': runner_sha256}, training_native.training_setup)


def preview_experiment(state: State, project_id: str, experiment: dict, runner_template_id: str,
                       *, max_run_seconds: int | None = None, configuration_materials: dict | None = None) -> dict:
    """Generate the original publication plan entirely in staging."""
    return training_native.training_preparation(_project(state, project_id), state.root, 'preview',
        {'experiment_id': experiment.get('experiment_id') if isinstance(experiment, dict) else None, 'request': {'experiment': experiment,
         'runner_template_id': runner_template_id, 'max_run_seconds': max_run_seconds,
         'configuration_materials': configuration_materials}})


def prepare_experiment(state: State, project_id: str, experiment: dict, runner_template_id: str,
                       expected_revision: int, preview_sha256: str, *, max_run_seconds: int | None = None,
                       configuration_materials: dict | None = None) -> dict:
    """Freeze the confirmed local plan before the original owner publishes any file."""
    return _setup(state, project_id, expected_revision, 'prepare',
        {'experiment_id': experiment.get('experiment_id') if isinstance(experiment, dict) else None, 'preview_sha256': preview_sha256,
         'request': {'experiment': experiment, 'runner_template_id': runner_template_id,
                     'max_run_seconds': max_run_seconds, 'configuration_materials': configuration_materials}}, training_native.training_preparation)


def preparation(state: State, project_id: str, experiment_id: str) -> dict:
    """Read the saved intent and each original publication fact without SDK or service."""
    return training_native.training_preparation(_project(state, project_id), state.root, 'status',
                                          {'experiment_id': experiment_id})


def resume_prepare(state: State, project_id: str, experiment_id: str, expected_revision: int,
                   intent_sha256: str) -> dict:
    """Explicitly complete only the exact original local preparation intent."""
    return _setup(state, project_id, expected_revision, 'resume',
                  {'experiment_id': experiment_id, 'intent_sha256': intent_sha256}, training_native.training_preparation)


def inspect(state: State, project_id: str, experiment_id: str | None = None, *,
            limit: int = 50, after: str | None = None) -> dict:
    """Read native records without submitting, querying or approving an experiment."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Training page limit must be 1–100 inspected entries')
    project = _project(state, project_id)
    return {'project': project_id, 'project_revision': project['revision'],
            **training_native.training_files(project, experiment_id=experiment_id, limit=limit, after=after)}


def status(state: State, project_id: str, experiment_id: str, *, run_id: str | None = None,
           timeout: int = 20) -> dict:
    """Query explicitly; offline records never substitute for runtime facts."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Training runtime query timeout must be 1–60 seconds')
    if run_id is not None and (not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id):
        raise ValueError('Training run ID must be a nonempty string of at most 128 characters without surrounding whitespace')
    observed = inspect(state, project_id, experiment_id)
    project = state.project(project_id)
    if project['revision'] != observed['project_revision']:
        raise ValueError('Project changed during training preflight; read the selected experiment again')
    return {'project': project_id, 'project_revision': project['revision'], 'experiment_id': experiment_id,
            'binding': observed['experiment']['binding'],
            **training_native.training_runtime_status(project, observed['experiment']['spec'], run_id=run_id, timeout=timeout)}


def evidence(state: State, project_id: str, experiment_id: str, *, artifact: str | None = None,
             evidence_sha256: str | None = None, screen_result_sha256: str | None = None,
             offset: int = 0, limit: int = 12_000, retained_archive: bool = False,
             profile_attempt_sha256: str | None = None, profile_capture_sha256: str | None = None) -> dict:
    """Read original training evidence through its accepted or retained archive entry."""
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 65_536:
        raise ValueError('Training evidence uses a nonnegative character offset and limit of 1–65,536')
    if evidence_sha256 is not None and screen_result_sha256 is not None:
        raise ValueError('Artifact reads require exactly one matching full or screen digest')
    selected_sha = evidence_sha256 if evidence_sha256 is not None else screen_result_sha256
    recovering_profile = profile_attempt_sha256 is not None or profile_capture_sha256 is not None
    if recovering_profile:
        if any(not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None
               for digest in (profile_attempt_sha256, profile_capture_sha256)):
            raise ValueError('Profile recovery requires the exact raw attempt and capture SHA-256 values')
        if artifact is not None or selected_sha is not None or retained_archive:
            raise ValueError('Profile recovery is a separate original evidence selection')
    if artifact is not None and (not isinstance(artifact, str) or not artifact
            or not isinstance(selected_sha, str) or re.fullmatch('[a-f0-9]{64}', selected_sha) is None):
        raise ValueError('Training artifact reads require a path from the index and the exact evidence SHA-256')
    if artifact is None and not recovering_profile and (selected_sha is not None or offset != 0):
        raise ValueError('Evidence SHA and character offset apply only to a selected artifact')
    if type(retained_archive) is not bool:
        raise ValueError('Retained archive observation requires an explicit Boolean')
    if retained_archive and screen_result_sha256 is not None:
        raise ValueError('Retained archive artifact requires the exact full evidence SHA-256')
    return training_native.training_evidence(_project(state, project_id), state.root,
        {'operation': 'inspect', 'experiment_id': experiment_id, 'artifact': artifact, 'evidence_sha256': evidence_sha256,
         'screen_result_sha256': screen_result_sha256, 'offset': offset, 'limit': limit,
         'retained_archive': retained_archive, 'profile_attempt_sha256': profile_attempt_sha256,
         'profile_capture_sha256': profile_capture_sha256})


def baseline_reference(state: State, project_id: str, experiment_id: str, *, evidence_sha256: str) -> dict:
    """Inventory one exact accepted archive, without granting current execution or quality."""
    if not isinstance(evidence_sha256, str) or re.fullmatch('[a-f0-9]{64}', evidence_sha256) is None:
        raise ValueError('Baseline reference requires the exact evidence SHA-256')
    return training_native.training_evidence(_project(state, project_id), state.root,
        {'operation': 'baseline-reference', 'experiment_id': experiment_id, 'evidence_sha256': evidence_sha256})


def observe_tracking(state: State, project_id: str, experiment_id: str, *, evidence_sha256: str,
                     tracking_attempt_sha256: str, mlflow_run_id: str, metric: str, artifact: str) -> dict:
    """Observe a previously identified MLflow Run against the retained training attempt."""
    for value, label, size in ((evidence_sha256, 'retained evidence SHA-256', 64),
                               (tracking_attempt_sha256, 'tracking attempt SHA-256', 64),
                               (mlflow_run_id, 'previously observed MLflow Run ID', 32)):
        if not isinstance(value, str) or re.fullmatch(r'[a-f0-9]+', value) is None or len(value) != size:
            raise ValueError('Tracking observation requires the exact ' + label)
    if not isinstance(metric, str) or not 1 <= len(metric) <= 250 or not isinstance(artifact, str) or not artifact:
        raise ValueError('Tracking observation requires one original metric key and one indexed artifact path')
    return training_native.training_evidence(_project(state, project_id), state.root,
        {'operation': 'tracking-observe', 'experiment_id': experiment_id, 'evidence_sha256': evidence_sha256,
         'tracking_attempt_sha256': tracking_attempt_sha256, 'mlflow_run_id': mlflow_run_id,
         'metric': metric, 'artifact': artifact})


def submission(state: State, project_id: str, experiment_id: str, *, original_registration: dict | None = None) -> dict:
    """Read local operation receipts; never query or submit a native workflow."""
    project = _project(state, project_id, original_registration)
    return training_native.training_submission(project, state.root, 'status', {'experiment_id': experiment_id}, timeout=20)


def execution(state: State, project_id: str, experiment_id: str) -> dict:
    """Read historical lifecycle records without the selected native installation."""
    project = _project(state, project_id)
    action = action_observations.TrainingExecutionStatus(experiment_id)
    return {'project': project_id, 'project_revision': project['revision'], 'experiment_id': experiment_id,
            **action_observations.observe(action, project, state.root)}


def execute(state: State, project_id: str, experiment_id: str, expected_revision: int, intent_sha256: str,
            run_id: str, request_sha256: str, *, confirm: bool, timeout: int = 20) -> dict:
    """Confirm one original job; never hold a DB reservation across remote checks."""
    if type(expected_revision) is not int or expected_revision < 1 or confirm is not True:
        raise ValueError('Explicit execution requires its positive project revision and confirmation')
    for digest in (intent_sha256, request_sha256):
        if not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None:
            raise ValueError('Explicit execution requires complete original SHA256 values')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Execution request timeout must be 1–60 seconds')
    project = _project(state, project_id)
    if project['revision'] != expected_revision:
        raise ValueError('Project revision changed; reload before explicit execution')
    return training_native.training_execution(project, state.root, 'request', {'experiment_id': experiment_id,
        'expected_revision': expected_revision, 'intent_sha256': intent_sha256, 'run_id': run_id,
        'request_sha256': request_sha256, 'confirm': confirm}, timeout=timeout)


def check_start(state: State, project_id: str, experiment_id: str, manifest_sha256: str) -> dict:
    """Observe native new-start readiness without reserving or sending anything."""
    if not isinstance(manifest_sha256, str) or re.fullmatch('[a-f0-9]{64}', manifest_sha256) is None:
        raise ValueError('Training check requires the exact manifest SHA-256')
    project = _project(state, project_id)
    observed = training_native.training_submission(project, state.root, 'check',
        {'experiment_id': experiment_id, 'manifest_sha256': manifest_sha256}, timeout=20)
    if state.project(project_id)['revision'] != project['revision']:
        raise ValueError('Project changed during training start check; read the selected experiment again')
    return observed


def fence_start(state: State, project_id: str, experiment_id: str, expected_revision: int,
                manifest_sha256: str, *, confirm: bool, timeout: int = 20,
                original_registration: dict | None = None) -> dict:
    """Explicitly fence one local experiment; do not certify run ownership or stop."""
    if confirm is not True:
        raise ValueError('Confirm the local experiment fence and its runner/archive/release effects')
    if not isinstance(manifest_sha256, str) or re.fullmatch('[a-f0-9]{64}', manifest_sha256) is None:
        raise ValueError('Training fence requires the exact original manifest SHA-256')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Training fence timeout must be 1–60 seconds')
    return _setup(state, project_id, expected_revision, 'fence',
                  {'experiment_id': experiment_id, 'manifest_sha256': manifest_sha256},
                  partial(training_native.training_submission, timeout=timeout), original_registration=original_registration)


def start(state: State, project_id: str, experiment_id: str, expected_revision: int,
          manifest_sha256: str, *, timeout: int = 20, budget: dict | None = None) -> dict:
    """Confirm one prepared native manifest and checkpoint its original start."""
    return _submission(state, project_id, experiment_id, expected_revision, manifest_sha256,
                       'prepare', 'manifest_sha256', timeout, budget=budget)


def resume_start(state: State, project_id: str, experiment_id: str, expected_revision: int,
                 intent_sha256: str, *, timeout: int = 20, original_registration: dict | None = None) -> dict:
    """Continue before dispatch, or reconcile the original run after an attempt."""
    return _submission(state, project_id, experiment_id, expected_revision, intent_sha256,
                       'prepare-resume', 'intent_sha256', timeout, original_registration=original_registration)


def approval(state: State, project_id: str, experiment_id: str) -> dict:
    """Read the original local owner decision; no authorization or RPC implied."""
    return training_native.training_release(_project(state, project_id), state.root, 'status',
                                       {'experiment_id': experiment_id}, timeout=20)


def approve(state: State, project_id: str, experiment_id: str, expected_revision: int, *,
            run_id: str, evidence_sha256: str, confirm: bool, timeout: int = 20) -> dict:
    """Confirm one exact owner decision, then deliver its original release once."""
    if not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id:
        raise ValueError('Training approval requires the exact original run ID')
    if not isinstance(evidence_sha256, str) or re.fullmatch('[a-f0-9]{64}', evidence_sha256) is None:
        raise ValueError('Training approval requires the exact original evidence SHA-256')
    return _release(state, project_id, experiment_id, expected_revision, 'prepare',
                    {'run_id': run_id, 'evidence_sha256': evidence_sha256}, confirm, timeout)


def resume_approve(state: State, project_id: str, experiment_id: str, expected_revision: int,
                   intent_sha256: str, *, confirm: bool, timeout: int = 20) -> dict:
    """Continue an unsent decision, or only reconcile the original attempted signal."""
    if not isinstance(intent_sha256, str) or re.fullmatch('[a-f0-9]{64}', intent_sha256) is None:
        raise ValueError('Training approval recovery requires the exact original intent SHA-256')
    return _release(state, project_id, experiment_id, expected_revision, 'prepare-resume',
                    {'intent_sha256': intent_sha256}, confirm, timeout)


def cancellation(state: State, project_id: str, experiment_id: str, request_id: str, *,
                 original_registration: dict | None = None) -> dict:
    """Read a local cancellation record; no signal or runtime query."""
    return training_native.training_cancellation(_project(state, project_id, original_registration), state.root, 'status',
                {'experiment_id': experiment_id, 'request_id': request_id}, timeout=20)


def cancel(state: State, project_id: str, experiment_id: str, request_id: str, expected_revision: int,
           *, run_id: str, reason: str, timeout: int = 20, original_registration: dict | None = None) -> dict:
    """Confirm one fixed-run request, then deliver it once through the native client."""
    if not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id:
        raise ValueError('Training cancellation requires the exact original run ID')
    return _cancellation(state, project_id, experiment_id, request_id, expected_revision,
                         'prepare', {'run_id': run_id, 'reason': reason}, timeout, original_registration=original_registration)


def resume_cancel(state: State, project_id: str, experiment_id: str, request_id: str, expected_revision: int,
                  intent_sha256: str, *, timeout: int = 20, original_registration: dict | None = None) -> dict:
    """Continue an unsent request, or recover attempted delivery only from original history."""
    if not isinstance(intent_sha256, str) or re.fullmatch('[a-f0-9]{64}', intent_sha256) is None:
        raise ValueError('Training cancellation recovery requires the exact original intent SHA-256')
    return _cancellation(state, project_id, experiment_id, request_id, expected_revision,
                         'prepare-resume', {'intent_sha256': intent_sha256}, timeout, original_registration=original_registration)


def stop_status(state: State, project_id: str, experiment_id: str, *, timeout: int = 20,
                original_registration: dict | None = None) -> dict:
    """Explicitly observe original control, native executor and fence facts; change none."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Training stop query timeout must be 1–60 seconds')
    return training_native.training_cancellation(_project(state, project_id, original_registration), state.root, 'stop-status',
                                          {'experiment_id': experiment_id}, timeout=timeout)


def _project(state: State, project_id: str, original_registration: dict | None = None) -> dict:
    project = state.project(project_id)
    if original_registration is not None:
        if (set(original_registration) != {'operation_id', 'intent_sha256', 'confirm'}
                or original_registration['confirm'] is not True):
            raise ValueError('Explicitly confirm the original registration operation and its complete intent SHA-256')
        current_revision = project['revision']
        project = registrations.published_project(state.root, project_id, original_registration['operation_id'],
                                                  original_registration['intent_sha256'])
        project['_original_registration'] = {key: original_registration[key] for key in ('operation_id', 'intent_sha256')}
        project['_original_registration']['current_project_revision'] = current_revision
    registration = project.get('registration', {})
    if registration.get('status') != 'published' or 'training-optimization' not in registration['definition']['templates']:
        raise ValueError('Training operations require a published project with training-optimization selected')
    return project


def _setup(state: State, project_id: str, expected_revision: int, operation: str, payload: dict, publish, *,
           original_registration: dict | None = None) -> dict:
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Expected project revision must be a positive integer')
    # Local setup/preparation owns immutable files; no remote I/O under this reservation.
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id, original_registration)
        if project.get('_original_registration', {}).get('current_project_revision', project['revision']) != expected_revision:
            raise ValueError('Project revision changed; preview the setup document again')
        return publish(project, state.root, operation, payload)


def _submission(state: State, project_id: str, experiment_id: str, expected_revision: int,
                digest: str, operation: str, digest_name: str, timeout: int, *,
                original_registration: dict | None = None, budget: dict | None = None) -> dict:
    project, prepared = _prepare_submission(state, project_id, experiment_id, expected_revision,
        digest, operation, digest_name, timeout, original_registration=original_registration, budget=budget)
    if operation == 'prepare':
        observed = prepared['submission']
        if not prepared['created']:
            return observed
    else:
        observed = prepared
        if observed['status'] in ('submitted', 'rejected'):
            return observed
    return training_native.training_submission(project, state.root, 'dispatch' if operation == 'prepare' else 'resume',
                {'experiment_id': experiment_id, 'intent_sha256': observed['intent_sha256']}, timeout=timeout)


def _prepare_submission(state: State, project_id: str, experiment_id: str, expected_revision: int,
                        digest: str, operation: str, digest_name: str, timeout: int, *,
                        original_registration: dict | None = None, budget: dict | None = None,
                        cycle_operation: dict | None = None) -> tuple[dict, dict]:
    """Freeze the original local start, without entering its remote dispatch."""
    if not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None:
        raise ValueError('Training operation requires the exact manifest or intent SHA-256')
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Expected project revision must be a positive integer')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Training submission timeout must be 1–60 seconds')
    # Retain the project only while freezing local intent, never across RPCs.
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id, original_registration)
        if project.get('_original_registration', {}).get('current_project_revision', project['revision']) != expected_revision:
            raise ValueError('Project revision changed; reload before the training operation')
        prepared = training_native.training_submission(project, state.root, operation,
                     {'experiment_id': experiment_id, digest_name: digest,
                      **({'budget': budget} if budget is not None else {}),
                      **({'cycle_operation': cycle_operation} if cycle_operation is not None else {})}, timeout=timeout)
    return project, prepared


def _cancellation(state: State, project_id: str, experiment_id: str, request_id: str, expected_revision: int,
                  operation: str, payload: dict, timeout: int, *, original_registration: dict | None = None) -> dict:
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Expected project revision must be a positive integer')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Training cancellation timeout must be 1–60 seconds')
    identity = {'experiment_id': experiment_id, 'request_id': request_id}
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id, original_registration)
        if project.get('_original_registration', {}).get('current_project_revision', project['revision']) != expected_revision:
            raise ValueError('Project revision changed; reload before the training cancellation')
        prepared = training_native.training_cancellation(project, state.root, operation, {**identity, **payload}, timeout=timeout)
    if operation == 'prepare':
        observed = prepared['cancellation']
        if not prepared['created']:
            return observed
    else:
        observed = prepared
        if observed['status'] in ('requested', 'already_closed'):
            return observed
    return training_native.training_cancellation(project, state.root, 'dispatch' if operation == 'prepare' else 'resume',
                    {**identity, 'intent_sha256': observed['intent_sha256']}, timeout=timeout)


def _release(state: State, project_id: str, experiment_id: str, expected_revision: int,
             operation: str, payload: dict, confirm: bool, timeout: int) -> dict:
    if confirm is not True:
        raise ValueError('Explicit owner confirmation is required for training approval and recovery')
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Expected project revision must be a positive integer')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Training approval timeout must be 1–60 seconds')
    identity = {'experiment_id': experiment_id}
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        if project['revision'] != expected_revision:
            raise ValueError('Project revision changed; reload before the training approval')
        prepared = training_native.training_release(project, state.root, operation, {**identity, **payload}, timeout=timeout)
    observed = prepared['approval'] if operation == 'prepare' else prepared
    if (operation == 'prepare' and not prepared['created']) or observed['status'] == 'requested':
        return observed
    return training_native.training_release(project, state.root, 'dispatch' if operation == 'prepare' else 'resume',
                    {**identity, 'intent_sha256': observed['intent_sha256']}, timeout=timeout)
