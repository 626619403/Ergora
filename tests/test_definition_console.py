"""The definition console shares immutable libraries and never needs a project."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip('fastapi')
pytest.importorskip('httpx')
from fastapi.testclient import TestClient

from ergora import agent_definitions, cli, projects, workflow_definitions as workflows
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
    for kind, original in [('agent', agent_before), ('workflow', workflow_before)]:
        definition = {**original['definition'], 'version': '1.0.1'}
        for suffix in ['/check', '']:
            response = client.post(f"/api/{kind}-definitions/{definition['id']}/{original['definition']['version']}/revisions{suffix}",
                json={'base_digest': original['digest'], 'definition': definition})
            assert response.status_code == 400 and 'Backend no longer admitted' in response.json()['error']


@pytest.mark.parametrize('kind,command', [('agent', ['agent', 'definition']), ('workflow', ['composition'])])
def test_revision_http_and_cli_share_candidate_identity_and_keep_base(library_console, tmp_path, capsys, kind, command):
    client, state = library_console
    preset = client.post('/api/composition/presets/repository-governance/install', json={}).json()
    reference = preset['agents'][0] if kind == 'agent' else preset['root']
    base_url = f"/api/{kind}-definitions/{reference['id']}/{reference['version']}"
    original = client.get(base_url).json()
    (Path(original['path']) / f'{kind}.json').chmod(0o444)
    definition = {**original['definition'], 'version': '1.0.1', 'description': 'New immutable revision'}
    payload = {'base_digest': reference['digest'], 'definition': definition}
    response = client.post(base_url + '/revisions/check', json=payload)
    assert response.status_code == 200, response.text
    converted = client.post('/api/definition-documents/convert', json={'text': json.dumps(definition)}).json()
    for format in ['json', 'yaml']:
        document = tmp_path / f'new-definition.{format}'
        document.write_text(converted[format], encoding='utf-8')
        assert cli.main(['--home', str(state.root), *command, 'revise', reference['id'], reference['version'],
            '--base-digest', reference['digest'], '--document', str(document), '--format', format, '--check']) == 0
        assert json.loads(capsys.readouterr().out) == response.json()
    assert client.get(f"/api/{kind}-definitions/{reference['id']}/{definition['version']}").status_code == 400
    published = client.post(base_url + '/revisions', json=payload)
    assert published.status_code == 200, published.text
    assert published.json() == {**response.json(), 'published': True}
    assert client.get(base_url).json() == original
    assert client.get(f"/api/{kind}-definitions/{reference['id']}/{definition['version']}").json()['digest'] == response.json()['digest']
    assert projects.list_projects(state) == []


def test_document_conversion_roundtrips_json_data_without_publishing(library_console):
    client, state = library_console
    definition = {'description': '中文与多行\nContext: keep exact values', 'roles': ['reviewer'],
                  'values': [True, False, None, 1, 1.25], 'nested': {'quoted': 'yes', 'date': '2026-11-10'}}
    response = client.post('/api/definition-documents/convert', json={'text': '\ufeff' + json.dumps(definition)})
    assert response.status_code == 200, response.text
    converted = response.json()
    assert converted['definition'] == definition and json.loads(converted['json']) == definition
    yaml_response = client.post('/api/definition-documents/convert', json={'text': converted['yaml'], 'format': 'yaml'})
    assert yaml_response.status_code == 200, yaml_response.text
    assert yaml_response.json() == converted
    json_response = client.post('/api/definition-documents/convert', json={'text': converted['json']})
    assert json_response.status_code == 200, json_response.text
    assert json_response.json() == converted
    assert client.get('/api/agent-definitions').json() == client.get('/api/workflow-definitions').json() == []
    assert projects.list_projects(state) == [] and not (state.root / 'runs').exists()


@pytest.mark.parametrize('format,text,reason', [
    ('json', '{"outer":{"value":1,"value":2}}', 'Duplicate JSON key'),
    ('yaml', 'outer:\n  value: 1\n  value: 2\n', 'Duplicate YAML key'),
    ('yaml', 'a: &shared [1]\nb: *shared', 'YAML aliases'),
    ('yaml', '1: value', 'keys must be strings'),
    ('yaml', 'date: 2026-11-10', 'JSON-compatible YAML tags'),
    ('yaml', 'a: !!python/object/apply:os.getcwd []', 'JSON-compatible YAML tags'),
    ('yaml', 'a: .nan', 'Out of range float'),
    ('yaml', '- item', 'object root'),
])
def test_untrusted_document_formats_reject_lossy_or_executable_values(library_console, format, text, reason):
    client, _ = library_console
    response = client.post('/api/definition-documents/convert', json={'text': text, 'format': format})
    assert response.status_code == 400 and reason in response.json()['error']


@pytest.mark.parametrize('format', ['json', 'yaml'])
@pytest.mark.parametrize('text', ['{"nested":' * 65 + '0' + '}' * 65,
                                '{"values":[' + ','.join(['0'] * 100_001) + ']}'], ids=['depth', 'values'])
def test_document_conversion_bounds_parser_work_before_publication(library_console, format, text):
    client, _ = library_console
    response = client.post('/api/definition-documents/convert', json={'text': text, 'format': format})
    assert response.status_code == 400 and '64 levels / 100000 values' in response.json()['error']
