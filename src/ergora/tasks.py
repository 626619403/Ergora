"""Project-scoped formal task use cases; the native runtime remains authoritative."""

import json
from pathlib import Path
import re

from . import bindings, contracts, projects, reference
from .state import State


_DEFINITION = json.loads((Path(__file__).parent / 'data/schemas/task-definition-v1.json').read_text(encoding='utf-8'))


def _project(state: State, project_id: str) -> dict:
    project = state.project(project_id)
    registration = project.get('registration')
    if not registration or registration['status'] != 'published':
        raise ValueError('Formal tasks require a published unified project registration')
    reference.validate_installation(Path(registration['definition']['execution']['installation']))
    return project


def _revision(project: dict, expected_revision: int) -> None:
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Expected project revision must be a positive integer')
    if project['revision'] != expected_revision:
        raise ValueError('Project revision changed; reload before the task operation')


def _definition(project: dict, definition: dict) -> dict:
    contracts.validate(definition, _DEFINITION, 'Task definition')
    if definition['task_type'] not in project['registration']['definition']['templates']:
        raise ValueError('Task template is not registered for this project')
    if len(json.dumps(definition, ensure_ascii=False, allow_nan=False).encode('utf-8')) > 1_048_576:
        raise ValueError('Task definition exceeds 1 MiB')
    return {'definition': definition,
            'selection': bindings.development_snapshot(project, projects.effective_configuration(project))}


def _digest(value: str, name: str) -> None:
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError(name + ' must be a SHA256 digest')


def _run_id(value: str) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or value.strip() != value:
        raise ValueError('Run ID must be a nonempty opaque identifier of at most 128 characters')


def preview(state: State, project_id: str, definition: dict, expected_revision: int) -> dict:
    """Compile in temporary storage and return the exact proposed task and bindings."""
    project = _project(state, project_id)
    _revision(project, expected_revision)
    return reference.task_creation(project, state.root, 'preview', _definition(project, definition))


def create(state: State, project_id: str, definition: dict, expected_revision: int, preview_sha256: str) -> dict:
    """Publish only an explicitly previewed immutable task, after saving its intent."""
    _digest(preview_sha256, 'Preview')
    # Binding and registration writers use the same SQLite write reservation.
    # Hold it through publication so an approved revision cannot change halfway.
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        _revision(project, expected_revision)
        return reference.task_creation(project, state.root, 'create',
                                       {**_definition(project, definition), 'preview_sha256': preview_sha256})


def creation(state: State, project_id: str, task_id: str) -> dict:
    """Inspect the saved creation intent and native files, without querying execution."""
    project = _project(state, project_id)
    return reference.task_creation(project, state.root, 'status', {'task_id': task_id})


def resume_create(state: State, project_id: str, task_id: str, expected_revision: int, intent_sha256: str) -> dict:
    """Finish the original saved publication without recompiling or changing its bindings."""
    _digest(intent_sha256, 'Intent')
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        _revision(project, expected_revision)
        return reference.task_creation(project, state.root, 'resume',
                                       {'task_id': task_id, 'intent_sha256': intent_sha256})


def status(state: State, project_id: str, task_id: str, *, run_id: str | None = None, timeout: int = 20) -> dict:
    """Read verified native execution facts; absence and transport errors stay distinct."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Task runtime query timeout must be 1–60 seconds')
    if run_id is not None:
        _run_id(run_id)
    project = _project(state, project_id)
    task = reference.task_files(project, task_id=task_id)
    return {'project': project_id, 'project_revision': project['revision'], 'task_id': task_id,
            'request_sha256': task['spec']['request_sha256'], 'profile_sha256': task['spec']['profile_sha256'],
            **reference.task_runtime_status(project, task['spec'], run_id=run_id, timeout=timeout)}


def external_status(state: State, project_id: str, task_id: str, *, run_id: str, timeout: int = 20) -> dict:
    """Read the closed original run's job/receipt/fence evidence without mutations."""
    _run_id(run_id)
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('External evidence query timeout must be 1–60 seconds')
    project = _project(state, project_id)
    return reference.task_external_status(project, state.root, {'task_id': task_id, 'run_id': run_id}, timeout=timeout)


def submission(state: State, project_id: str, task_id: str) -> dict:
    """Inspect local submission facts without connecting to Temporal or reissuing work."""
    project = _project(state, project_id)
    return reference.task_submission(project, state.root, 'status', {'task_id': task_id}, timeout=20)


def reconciliation(state: State, project_id: str, task_id: str) -> dict:
    """Read saved cleanup evidence without querying the run, fencing or releasing."""
    project = _project(state, project_id)
    return reference.task_reconciliation(project, state.root, 'status', {'task_id': task_id}, timeout=20)


def reconcile(state: State, project_id: str, task_id: str, expected_revision: int,
              *, run_id: str, confirm: bool = False, timeout: int = 20) -> dict:
    """Fence a closed original run and release only its confirmed external cleanup."""
    _run_id(run_id)
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_reconciliation, 'prepare',
                                         {'task_id': task_id, 'run_id': run_id}, confirm, timeout)
    if not prepared['created']:
        return prepared['reconciliation']
    return reference.task_reconciliation(project, state.root, 'dispatch',
                                         {'task_id': task_id, 'intent_sha256': prepared['reconciliation']['intent_sha256']},
                                         timeout=timeout)


def resume_reconcile(state: State, project_id: str, task_id: str, expected_revision: int,
                     intent_sha256: str, *, confirm: bool = False, timeout: int = 20) -> dict:
    """Resume the original immutable fence and cleanup release after interruption."""
    _digest(intent_sha256, 'Intent')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_reconciliation, 'prepare-resume',
                                         {'task_id': task_id, 'intent_sha256': intent_sha256}, confirm, timeout)
    if prepared['status'] == 'reconciled':
        return prepared
    return reference.task_reconciliation(project, state.root, 'resume',
                                         {'task_id': task_id, 'intent_sha256': intent_sha256}, timeout=timeout)


def start(state: State, project_id: str, task_id: str, expected_revision: int,
          creation_sha256: str, *, timeout: int = 20) -> dict:
    """Submit an explicitly identified creation once through the original admission."""
    _digest(creation_sha256, 'Creation')
    return _submission(state, project_id, task_id, expected_revision, 'start',
                       {'creation_sha256': creation_sha256}, timeout)


def resume_start(state: State, project_id: str, task_id: str, expected_revision: int,
                 intent_sha256: str, *, timeout: int = 20) -> dict:
    """Resume a pre-dispatch intent or reconcile uncertain dispatch by its original ID."""
    _digest(intent_sha256, 'Intent')
    return _submission(state, project_id, task_id, expected_revision, 'resume',
                       {'intent_sha256': intent_sha256}, timeout)


def _submission(state: State, project_id: str, task_id: str, expected_revision: int,
                operation: str, payload: dict, timeout: int) -> dict:
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Task submission timeout must be 1–60 seconds')
    project, prepared = _native_prepare(state, project_id, expected_revision, reference.task_submission,
                                        'prepare' if operation == 'start' else 'prepare-resume',
                                        {'task_id': task_id, **payload}, timeout)
    if operation == 'start':
        status = prepared['submission']
        if not prepared['created']:
            return status
    else:
        status = prepared
        if status['status'] in ('submitted', 'rejected'):
            return status
    return reference.task_submission(project, state.root, 'dispatch' if operation == 'start' else 'resume',
                                     {'task_id': task_id, 'intent_sha256': status['intent_sha256']}, timeout=timeout)


def approval(state: State, project_id: str, task_id: str, decision_id: str) -> dict:
    """Read one durable owner decision without querying or signaling the workflow."""
    project = _project(state, project_id)
    return reference.task_approval(project, state.root, 'status',
                                   {'task_id': task_id, 'decision_id': decision_id}, timeout=20)


def plan(state: State, project_id: str, task_id: str, *, run_id: str, plan_sha256: str, timeout: int = 20) -> dict:
    """Read bounded review materials for the original run's exact pending plan."""
    _run_id(run_id)
    _digest(plan_sha256, 'Plan')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Plan inspection timeout must be 1–60 seconds')
    project = _project(state, project_id)
    return reference.task_plan(project, state.root, {'task_id': task_id, 'run_id': run_id,
                                                    'plan_sha256': plan_sha256}, timeout=timeout)


def approve(state: State, project_id: str, task_id: str, decision_id: str, expected_revision: int,
            *, run_id: str, plan_sha256: str, confirm: bool = False, timeout: int = 20) -> dict:
    """Freeze an explicit owner decision, then signal its exact run and plan once."""
    _run_id(run_id)
    _digest(plan_sha256, 'Plan')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_approval, 'prepare',
                                         {'task_id': task_id, 'decision_id': decision_id,
                                          'run_id': run_id, 'plan_sha256': plan_sha256}, confirm, timeout)
    if not prepared['created']:
        return prepared['approval']
    return reference.task_approval(project, state.root, 'dispatch',
                                   {'task_id': task_id, 'decision_id': decision_id,
                                    'intent_sha256': prepared['approval']['intent_sha256']}, timeout=timeout)


def resume_approve(state: State, project_id: str, task_id: str, decision_id: str, expected_revision: int,
                   intent_sha256: str, *, confirm: bool = False, timeout: int = 20) -> dict:
    """Continue an undispatched decision or find its signal in the original run's history."""
    _digest(intent_sha256, 'Intent')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_approval, 'prepare-resume',
                                         {'task_id': task_id, 'decision_id': decision_id,
                                          'intent_sha256': intent_sha256}, confirm, timeout)
    if prepared['status'] == 'requested':
        return prepared
    return reference.task_approval(project, state.root, 'resume',
                                   {'task_id': task_id, 'decision_id': decision_id,
                                    'intent_sha256': intent_sha256}, timeout=timeout)


def cancellation(state: State, project_id: str, task_id: str, request_id: str) -> dict:
    """Read a durable cancellation request without querying or signaling its run."""
    project = _project(state, project_id)
    return reference.task_cancellation(project, state.root, 'status',
                                       {'task_id': task_id, 'request_id': request_id}, timeout=20)


def cancel(state: State, project_id: str, task_id: str, request_id: str, expected_revision: int,
           *, run_id: str, reason: str, confirm: bool = False, timeout: int = 20) -> dict:
    """Request cooperative cancellation once, or record an already-closed run."""
    _run_id(run_id)
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
        raise ValueError('Cancellation requires a nonempty reason of at most 1000 characters')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_cancellation, 'prepare',
                                         {'task_id': task_id, 'request_id': request_id,
                                          'run_id': run_id, 'reason': reason}, confirm, timeout)
    if not prepared['created']:
        return prepared['cancellation']
    return reference.task_cancellation(project, state.root, 'dispatch',
                                       {'task_id': task_id, 'request_id': request_id,
                                        'intent_sha256': prepared['cancellation']['intent_sha256']}, timeout=timeout)


def resume_cancel(state: State, project_id: str, task_id: str, request_id: str, expected_revision: int,
                   intent_sha256: str, *, confirm: bool = False, timeout: int = 20) -> dict:
    """Continue only an undispatched request; unknown delivery needs original history."""
    _digest(intent_sha256, 'Intent')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_cancellation, 'prepare-resume',
                                         {'task_id': task_id, 'request_id': request_id,
                                          'intent_sha256': intent_sha256}, confirm, timeout)
    if prepared['status'] in ('requested', 'already_closed'):
        return prepared
    return reference.task_cancellation(project, state.root, 'resume',
                                       {'task_id': task_id, 'request_id': request_id,
                                        'intent_sha256': intent_sha256}, timeout=timeout)


def export_status(state: State, project_id: str, task_id: str) -> dict:
    """Read the saved local export, without querying the run or changing Git refs."""
    project = _project(state, project_id)
    return reference.task_export(project, state.root, 'status', {'task_id': task_id}, timeout=20)


def export(state: State, project_id: str, task_id: str, expected_revision: int,
           *, run_id: str, candidate_sha: str, branch: str, confirm: bool = False, timeout: int = 20) -> dict:
    """Confirm one original run, candidate and target branch before local export."""
    _run_id(run_id)
    if not isinstance(candidate_sha, str) or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', candidate_sha):
        raise ValueError('Export requires the exact full candidate commit SHA')
    if not isinstance(branch, str) or not 1 <= len(branch) <= 1024:
        raise ValueError('Export requires a nonempty branch of at most 1024 characters')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_export, 'prepare',
                                         {'task_id': task_id, 'run_id': run_id,
                                          'candidate_sha': candidate_sha, 'branch': branch}, confirm, timeout)
    if not prepared['created']:
        return prepared['export']
    return reference.task_export(project, state.root, 'dispatch',
                                 {'task_id': task_id, 'intent_sha256': prepared['export']['intent_sha256']}, timeout=timeout)


def resume_export(state: State, project_id: str, task_id: str, expected_revision: int,
                  intent_sha256: str, *, confirm: bool = False, timeout: int = 20) -> dict:
    """Continue only a prepared export; uncertain changes require its existing ref."""
    _digest(intent_sha256, 'Intent')
    project, prepared = _decision_prepare(state, project_id, expected_revision, reference.task_export, 'prepare-resume',
                                         {'task_id': task_id, 'intent_sha256': intent_sha256}, confirm, timeout)
    if prepared['status'] == 'exported':
        return prepared
    return reference.task_export(project, state.root, 'resume',
                                 {'task_id': task_id, 'intent_sha256': intent_sha256}, timeout=timeout)


def _decision_prepare(state: State, project_id: str, expected_revision: int, native_operation,
                       operation: str, payload: dict, confirm: bool, timeout: int) -> tuple[dict, dict]:
    if confirm is not True:
        raise ValueError('Task decision requires explicit confirmation of the original run and operation')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Task decision timeout must be 1–60 seconds')
    return _native_prepare(state, project_id, expected_revision, native_operation, operation, payload, timeout)


def _native_prepare(state: State, project_id: str, expected_revision: int, native_operation,
                     operation: str, payload: dict, timeout: int) -> tuple[dict, dict]:
    # Only local intent preparation retains the project revision. The long
    # native phase is authorized by that frozen intent, under its task lock.
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        _revision(project, expected_revision)
        prepared = native_operation(project, state.root, operation, payload, timeout=timeout)
    return project, prepared


def listing(state: State, project_id: str, *, limit: int = 50, after: str | None = None) -> dict:
    """Read a bounded window of native task contracts, without querying execution."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Task page limit must be 1–100 inspected entries')
    project = _project(state, project_id)
    return {'project': project_id, 'project_revision': project['revision'],
            **reference.task_files(project, limit=limit, after=after)}


def show(state: State, project_id: str, task_id: str) -> dict:
    """Read frozen task inputs and optional bindings; no runtime status is inferred."""
    project = _project(state, project_id)
    return {'project': project_id, 'project_revision': project['revision'],
            **reference.task_files(project, task_id=task_id)}
