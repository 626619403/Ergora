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
