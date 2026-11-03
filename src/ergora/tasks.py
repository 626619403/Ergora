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
    if run_id is not None and (not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id):
        raise ValueError('Run ID must be a nonempty opaque identifier of at most 128 characters')
    project = _project(state, project_id)
    task = reference.task_files(project, task_id=task_id)
    return {'project': project_id, 'project_revision': project['revision'], 'task_id': task_id,
            'request_sha256': task['spec']['request_sha256'], 'profile_sha256': task['spec']['profile_sha256'],
            **reference.task_runtime_status(project, task['spec'], run_id=run_id, timeout=timeout)}


def submission(state: State, project_id: str, task_id: str) -> dict:
    """Inspect local submission facts without connecting to Temporal or reissuing work."""
    project = _project(state, project_id)
    return reference.task_submission(project, state.root, 'status', {'task_id': task_id}, timeout=20)


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
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        project = _project(state, project_id)
        _revision(project, expected_revision)
        return reference.task_submission(project, state.root, operation, {'task_id': task_id, **payload}, timeout=timeout)


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
