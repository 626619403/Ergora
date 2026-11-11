"""Project-scoped observations; reading issue text grants no execution authority."""

from . import issue_backends, projects
from .state import State, now


def show(state: State, project_id: str, issue_id: str) -> dict:
    project = state.project(project_id)
    configuration = projects.effective_configuration(project)
    binding = configuration['layers']['tracker']['binding']
    backend = issue_backends.for_binding(binding)
    registration = project.get('registration')
    if registration and registration['definition']['tracker'] != {'kind': binding['tool'], 'project': binding['project']}:
        raise ValueError('Tracker source differs from the registered project namespace; use its registered source')
    observation = backend.read(issue_id)
    return {**observation, 'project': {'id': project_id, 'revision': project['revision']},
            'configuration_sha256': configuration['sha256'], 'observed_at': now()}
