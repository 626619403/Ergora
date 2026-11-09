"""The definition console shares immutable libraries and never needs a project."""

import json
import subprocess
import sys

import pytest

pytest.importorskip('fastapi')
pytest.importorskip('httpx')
from fastapi.testclient import TestClient

from ergora import agent_definitions, projects, workflow_definitions as workflows
from ergora.state import State
from ergora.web import create_app


@pytest.fixture
def library_console(tmp_path):
    state = State(tmp_path / 'control')
    with TestClient(create_app(state.root), base_url='http://127.0.0.1:8977',
                    headers={'Origin': 'http://127.0.0.1:8977', 'X-Ergora-Request': '1'}) as client:
        yield client, state


def test_empty_global_library_imports_all_presets_and_shares_exact_cli_versions(library_console):
    client, state = library_console
    assert client.get('/api/agent-definitions').json() == []
    assert client.get('/api/workflow-definitions').json() == []
    listed = client.get('/api/composition/presets').json()
    assert listed == workflows.presets()
    for preset in listed:
        path = f"/api/composition/presets/{preset['id']}/install"
        response = client.post(path, json={})
        assert response.status_code == 200, response.text
        imported = response.json()
        assert imported['execution_authorized'] is False
        assert client.post(path, json={}).json() == imported
        root = imported['root']
        detail = client.get(f"/api/workflow-definitions/{root['id']}/{root['version']}").json()
        assert detail == workflows.get(state, root['id'], root['version'], material=True)
        assert detail['digest'] == root['digest']
    command = [sys.executable, '-I', '-m', 'ergora', '--home', str(state.root), 'composition', 'list']
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    assert client.get('/api/workflow-definitions').json() == json.loads(result.stdout)
    agent = client.get('/api/agent-definitions').json()[0]
    assert client.get(f"/api/agent-definitions/{agent['id']}/{agent['version']}").json() == agent_definitions.get(
        state, agent['id'], agent['version'], material=True)
    filters = {'role': agent['roles'][0], 'specialty': agent['specialties'][0]}
    assert client.get('/api/agent-definitions', params=filters).json() == agent_definitions.definitions(state, **filters)
    assert projects.list_projects(state) == []


def test_http_preview_preserves_full_ancestors_and_leaves_permission_failure_with_owner(library_console):
    client, state = library_console
    root = client.post('/api/composition/presets/large-change/install', json={}).json()['root']
    definition = workflows.get(state, root['id'], root['version'])['definition']
    grant = {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}
    payload = {'id': root['id'], 'version': root['version'], 'grant': grant}
    response = client.post('/api/composition/preview', json=payload)
    assert response.status_code == 200, response.text
    assert response.json() == workflows.preview(state.root, root['id'], root['version'], grant)
    grant['permissions']['read'] = []
    rejected = client.post('/api/composition/preview', json=payload)
    assert rejected.status_code == 400 and 'Permission exceeds ancestor/project' in rejected.json()['error']
    assert workflows.get(state, root['id'], root['version'])['digest'] == root['digest']
    assert projects.list_projects(state) == []


def test_historical_http_details_remain_readable_when_current_backend_admission_changes(library_console, monkeypatch):
    client, state = library_console
    imported = client.post('/api/composition/presets/repository-governance/install', json={}).json()
    root, agent = imported['root'], imported['agents'][0]
    workflow_before = client.get(f"/api/workflow-definitions/{root['id']}/{root['version']}").json()
    agent_before = client.get(f"/api/agent-definitions/{agent['id']}/{agent['version']}").json()

    def unavailable(document):
        raise ValueError('Backend no longer admitted for a new call')

    monkeypatch.setattr(agent_definitions, 'validate_admission', unavailable)
    assert client.get(f"/api/workflow-definitions/{root['id']}/{root['version']}").json() == workflow_before
    assert client.get(f"/api/agent-definitions/{agent['id']}/{agent['version']}").json() == agent_before
    assert client.get('/api/workflow-definitions').json() == workflows.definitions(state)
    definition = workflow_before['definition']
    response = client.post('/api/composition/preview', json={'id': root['id'], 'version': root['version'],
        'grant': {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}})
    assert response.status_code == 400 and 'Backend no longer admitted' in response.json()['error']
