"""Project-scoped observations of the original training experiment registry."""

from pathlib import Path
import re

from . import reference
from .state import State


def inspect(state: State, project_id: str, experiment_id: str | None = None, *,
            limit: int = 50, after: str | None = None) -> dict:
    """Read native records without submitting, querying or approving an experiment."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Training page limit must be 1–100 inspected entries')
    project = _project(state, project_id)
    registration = project['registration']
    reference.validate_installation(Path(registration['definition']['execution']['installation']))
    return {'project': project_id, 'project_revision': project['revision'],
            **reference.training_files(project, experiment_id=experiment_id, limit=limit, after=after)}


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
            **reference.training_runtime_status(project, observed['experiment']['spec'], run_id=run_id, timeout=timeout)}


def submission(state: State, project_id: str, experiment_id: str) -> dict:
    """Read local operation receipts; never query or submit a native workflow."""
    project = _project(state, project_id)
    return reference.training_submission(project, state.root, 'status', {'experiment_id': experiment_id}, timeout=20)


def start(state: State, project_id: str, experiment_id: str, expected_revision: int,
          manifest_sha256: str, *, timeout: int = 20) -> dict:
    """Confirm one prepared native manifest and checkpoint its original start."""
    return _submission(state, project_id, experiment_id, expected_revision, manifest_sha256,
                       'prepare', 'manifest_sha256', timeout)


def resume_start(state: State, project_id: str, experiment_id: str, expected_revision: int,
                 intent_sha256: str, *, timeout: int = 20) -> dict:
    """Continue before dispatch, or reconcile the original run after an attempt."""
    return _submission(state, project_id, experiment_id, expected_revision, intent_sha256,
                       'prepare-resume', 'intent_sha256', timeout)


def cancellation(state: State, project_id: str, experiment_id: str, request_id: str) -> dict:
    """Read a local cancellation record; no signal or runtime query."""
    return reference.training_cancellation(_project(state, project_id), state.root, 'status',
                {'experiment_id': experiment_id, 'request_id': request_id}, timeout=20)


def cancel(state: State, project_id: str, experiment_id: str, request_id: str, expected_revision: int,
           *, run_id: str, reason: str, timeout: int = 20) -> dict:
    """Confirm one fixed-run request, then deliver it once through the native client."""
    if not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id:
        raise ValueError('Training cancellation requires the exact original run ID')
    return _cancellation(state, project_id, experiment_id, request_id, expected_revision,
                         'prepare', {'run_id': run_id, 'reason': reason}, timeout)


def resume_cancel(state: State, project_id: str, experiment_id: str, request_id: str, expected_revision: int,
                  intent_sha256: str, *, timeout: int = 20) -> dict:
    """Continue an unsent request, or recover attempted delivery only from original history."""
    if not isinstance(intent_sha256, str) or re.fullmatch('[a-f0-9]{64}', intent_sha256) is None:
        raise ValueError('Training cancellation recovery requires the exact original intent SHA-256')
    return _cancellation(state, project_id, experiment_id, request_id, expected_revision,
                         'prepare-resume', {'intent_sha256': intent_sha256}, timeout)


def stop_status(state: State, project_id: str, experiment_id: str, *, timeout: int = 20) -> dict:
    """Explicitly observe original control, native executor and fence facts; change none."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Training stop query timeout must be 1–60 seconds')
    return reference.training_cancellation(_project(state, project_id), state.root, 'stop-status',
                                          {'experiment_id': experiment_id}, timeout=timeout)


def _project(state: State, project_id: str) -> dict:
    project = state.project(project_id)
    registration = project.get('registration', {})
    if registration.get('status') != 'published' or 'training-optimization' not in registration['definition']['templates']:
        raise ValueError('Training operations require a published project with training-optimization selected')
    return project


def _submission(state: State, project_id: str, experiment_id: str, expected_revision: int,
                digest: str, operation: str, digest_name: str, timeout: int) -> dict:
    if not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None:
        raise ValueError('Training operation requires the exact manifest or intent SHA-256')
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Expected project revision must be a positive integer')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Training submission timeout must be 1–60 seconds')
    # Retain the project only while freezing local intent, never across RPCs.
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        if project['revision'] != expected_revision:
            raise ValueError('Project revision changed; reload before the training operation')
        prepared = reference.training_submission(project, state.root, operation,
                     {'experiment_id': experiment_id, digest_name: digest}, timeout=timeout)
    if operation == 'prepare':
        observed = prepared['submission']
        if not prepared['created']:
            return observed
    else:
        observed = prepared
        if observed['status'] in ('submitted', 'rejected'):
            return observed
    return reference.training_submission(project, state.root, 'dispatch' if operation == 'prepare' else 'resume',
                {'experiment_id': experiment_id, 'intent_sha256': observed['intent_sha256']}, timeout=timeout)


def _cancellation(state: State, project_id: str, experiment_id: str, request_id: str, expected_revision: int,
                  operation: str, payload: dict, timeout: int) -> dict:
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Expected project revision must be a positive integer')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Training cancellation timeout must be 1–60 seconds')
    identity = {'experiment_id': experiment_id, 'request_id': request_id}
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        if project['revision'] != expected_revision:
            raise ValueError('Project revision changed; reload before the training cancellation')
        prepared = reference.training_cancellation(project, state.root, operation, {**identity, **payload}, timeout=timeout)
    if operation == 'prepare':
        observed = prepared['cancellation']
        if not prepared['created']:
            return observed
    else:
        observed = prepared
        if observed['status'] in ('requested', 'already_closed'):
            return observed
    return reference.training_cancellation(project, state.root, 'dispatch' if operation == 'prepare' else 'resume',
                    {**identity, 'intent_sha256': observed['intent_sha256']}, timeout=timeout)
