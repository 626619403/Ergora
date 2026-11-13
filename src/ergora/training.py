"""Project-scoped observations of the original training experiment registry."""

from pathlib import Path

from . import reference
from .state import State


def inspect(state: State, project_id: str, experiment_id: str | None = None, *,
            limit: int = 50, after: str | None = None) -> dict:
    """Read native records without submitting, querying or approving an experiment."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Training page limit must be 1–100 inspected entries')
    project = state.project(project_id)
    registration = project.get('registration', {})
    if registration.get('status') != 'published' or 'training-optimization' not in registration['definition']['templates']:
        raise ValueError('Training observations require a published project registration with training-optimization selected')
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
