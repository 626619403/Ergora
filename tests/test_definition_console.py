"""The definition console shares immutable libraries and never needs a project."""

import base64
from copy import deepcopy
import hashlib
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
from ergora.asset_trees import digest_tree, inventory_tree


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


def test_manifest_handoff_shares_cli_identity_and_reads_without_live_library(library_console, tmp_path, capsys, monkeypatch):
    client, state = library_console
    root = client.post('/api/composition/presets/repository-governance/install', json={}).json()['root']
    definition = workflows.get(state, root['id'], root['version'])['definition']
    grant = {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}
    payload = {'id': root['id'], 'version': root['version'], 'grant': grant}
    original = client.post('/api/composition/preview', json=payload).json()
    payload['preview_sha256'] = original['preview_sha256']
    response = client.post('/api/composition/manifests', json=payload)
    assert response.status_code == 200, response.text
    saved = response.json()
    assert workflows.inspect_manifest(Path(saved['path']), material=True)['composition'] == original
    grant_file = tmp_path / 'grant.json'
    grant_file.write_text(json.dumps(grant))
    args = ['--home', str(state.root), 'composition']
    assert cli.main([*args, 'freeze-manifest', root['id'], root['version'], '--grant', str(grant_file),
                     '--preview-sha256', original['preview_sha256']]) == 0
    assert json.loads(capsys.readouterr().out) == saved
    url = '/api/composition/manifests/' + original['preview_sha256']

    def unavailable(document):
        raise ValueError('Backend no longer admitted for a new call')

    monkeypatch.setattr(agent_definitions, 'validate_admission', unavailable)
    rejected = client.post('/api/composition/manifests', json=payload)
    assert rejected.status_code == 400 and 'Backend no longer admitted' in rejected.json()['error']
    assert client.get(url).json() == saved
    for kind in ['agent', 'workflow']:
        (state.root / f'{kind}-definitions').rename(tmp_path / f'retired-{kind}-definitions')
    with TestClient(create_app(state.root), base_url='http://127.0.0.1:8977') as reopened:
        assert reopened.get(url).json() == saved
        assert reopened.get(url, params={'material': True}).json()['composition'] == original
    assert cli.main([*args, 'show-manifest', original['preview_sha256']]) == 0
    assert json.loads(capsys.readouterr().out) == saved
    assert projects.list_projects(state) == [] and not (state.root / 'runs').exists()


def test_historical_http_details_remain_readable_when_current_backend_admission_changes(library_console, monkeypatch):
    client, state = library_console
    imported = client.post('/api/composition/presets/repository-governance/install', json={}).json()
    root, agent = imported['root'], imported['agents'][0]
    workflow_before = client.get(f"/api/workflow-definitions/{root['id']}/{root['version']}").json()
    agent_before = client.get(f"/api/agent-definitions/{agent['id']}/{agent['version']}").json()
    previews = {}
    for kind, original in [('agent', agent_before), ('workflow', workflow_before)]:
        path = f"/api/{kind}-definitions/{original['definition']['id']}/{original['definition']['version']}"
        body = {'base_digest': original['digest'], 'definition': {**original['definition'], 'version': '1.0.1'},
                'resource_changes': {'schema_version': 1, 'operations': []}}
        response = client.post(path + '/revisions/preview-resources', json=body)
        assert response.status_code == 200, response.text
        previews[kind] = response.json()

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
        path = f"/api/{kind}-definitions/{definition['id']}/{original['definition']['version']}"
        file = client.post(path + '/files/read', json={'base_digest': original['digest'], 'path': f'{kind}.json'})
        assert file.status_code == 200, file.text
        assert file.json()['sha256'] == original['files'][f'{kind}.json']['sha256'] and file.json()['complete'] is True
        for suffix in ['/check', '']:
            response = client.post(path + '/revisions' + suffix,
                json={'base_digest': original['digest'], 'definition': definition})
            assert response.status_code == 400 and 'Backend no longer admitted' in response.json()['error']
        body = {'base_digest': original['digest'], 'definition': previews[kind]['definition'],
                'resource_changes': {'schema_version': 1, 'operations': []}}
        response = client.post(path + '/revisions/preview-resources', json=body)
        assert response.status_code == 400 and 'Backend no longer admitted' in response.json()['error']
        body['accepted_candidate'] = previews[kind]['candidate']
        response = client.post(path + '/revisions', json=body)
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


@pytest.mark.parametrize('kind,command', [('agent', ['agent', 'definition']), ('workflow', ['composition'])])
def test_resource_revision_cli_http_roundtrip_preserves_complete_tree(library_console, tmp_path, capsys, kind, command):
    client, state = library_console
    module = agent_definitions if kind == 'agent' else workflows
    installed = workflows.install_preset(state, 'repository-governance')
    reference = installed['agents'][0] if kind == 'agent' else installed['root']
    source = tmp_path / 'base-package'
    module.export(state, reference['id'], reference['version'], source)
    document = json.loads((source / f'{kind}.json').read_bytes())
    document['version'] = '1.0.10'
    (source / 'kept/empty').mkdir(parents=True)
    (source / 'kept.bin').write_bytes(b'\xff\x00 preserved attachment')
    (source / 'remove.bin').write_bytes(b'explicitly removed')
    skill = source / 'skills/resource-sample'
    (skill / 'references/empty').mkdir(parents=True)
    (skill / 'SKILL.md').write_text('---\nname: resource-sample\ndescription: Test complete resource trees.\n---\nRead references/tool.bin.\n')
    (skill / 'references/tool.bin').write_bytes(b'\xff original tool')
    document['resources'].append({'id': 'resource-sample', 'kind': 'skill', 'path': 'skills/resource-sample',
                                  'digest': digest_tree(skill)[0]})
    (source / f'{kind}.json').write_text(json.dumps(document))
    original = module.import_bundle(state, source)
    base_url = f"/api/{kind}-definitions/{reference['id']}/1.0.10"
    original_path = Path(original['path'])
    for directory in [original_path, *[path for path in original_path.rglob('*') if path.is_dir()]]:
        directory.chmod(0o555)
    for path in original_path.rglob('*'):
        if path.is_file():
            path.chmod(path.stat().st_mode & ~0o222)
    before = client.get(base_url).json()
    index = state.root / f'{kind}-definitions/index.json'
    index_before = index.read_bytes()
    definition = deepcopy(before['definition'])
    definition['version'] = '1.0.11'
    definition['resources'].append({'id': 'new-context', 'kind': 'context', 'path': 'new/context.md', 'sha256': '0' * 64})
    instructions = next(item['path'] for item in definition['resources'] if item['kind'] == 'instructions')
    raw_writes = {instructions: 'New instructions 中文\n'.encode(), 'new/context.md': b'Complete additional context\n',
                  'skills/resource-sample/references/tool.bin': b'\x00\xff changed full tool', 'extra.bin': b'\xff\x00 binary attachment'}
    operations = [{'op': 'write', 'path': path, 'content_base64': base64.b64encode(raw).decode()}
                  for path, raw in raw_writes.items()]
    operations[2]['executable_bits'] = 0 if sys.platform == 'win32' else 0o100
    operations += [{'op': 'delete', 'path': 'remove.bin'}, {'op': 'mkdir', 'path': 'new/nested/empty'}]
    changes = {'schema_version': 1, 'operations': operations}
    payload = {'base_digest': before['digest'], 'definition': definition, 'resource_changes': changes}
    preview_response = client.post(base_url + '/revisions/preview-resources', json=payload)
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()
    assert preview['resource_preview'] is True and preview['published'] is False
    assert next(item for item in preview['definition']['resources'] if item['id'] == 'new-context')['sha256'] == hashlib.sha256(raw_writes['new/context.md']).hexdigest()
    assert preview['definition']['resources'][-2]['digest'] != definition['resources'][-2]['digest']
    assert {'kept/empty', 'skills/resource-sample/references/empty', 'new/nested/empty'} <= set(preview['candidate']['directories'])
    assert index.read_bytes() == index_before
    local = tmp_path / 'changes'
    for path, raw in raw_writes.items():
        target = local / 'files' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (local / 'files/ignored.txt').write_text('Not a write or implicit deletion')
    (local / 'changes.json').write_text(json.dumps({'schema_version': 1, 'operations': [
        {key: value for key, value in operation.items() if key != 'content_base64'} for operation in operations]}))
    body = tmp_path / 'definition.json'
    body.write_text(json.dumps(definition))
    args = ['--home', str(state.root), *command, 'revise', reference['id'], '1.0.10', '--base-digest', before['digest'],
            '--document', str(body), '--resources', str(local)]
    assert cli.main([*args, '--preview-resources']) == 0
    assert json.loads(capsys.readouterr().out) == preview
    accepted = tmp_path / 'accepted.json'
    accepted.write_text(json.dumps(preview))
    body.write_text(json.dumps(preview['definition']))
    payload.update(definition=preview['definition'], accepted_candidate=preview['candidate'])
    checked = client.post(base_url + '/revisions/check', json=payload)
    assert checked.status_code == 200, checked.text
    assert cli.main([*args, '--accept-candidate', str(accepted), '--check']) == 0
    assert json.loads(capsys.readouterr().out) == checked.json()
    assert index.read_bytes() == index_before
    published = client.post(base_url + '/revisions', json=payload)
    assert published.status_code == 200, published.text
    assert published.json() == {**checked.json(), 'published': True}
    assert cli.main([*args, '--accept-candidate', str(accepted)]) == 0
    assert json.loads(capsys.readouterr().out) == published.json()
    assert client.get(base_url).json() == before
    saved = module.get(state, reference['id'], '1.0.11')
    assert saved['files']['kept.bin'] == before['files']['kept.bin']
    assert 'remove.bin' not in saved['files'] and 'ignored.txt' not in saved['files']
    for path, raw in raw_writes.items():
        assert (Path(saved['path']) / path).read_bytes() == raw
    assert saved['files']['skills/resource-sample/references/tool.bin']['executable_bits'] == operations[2]['executable_bits']
    exported = tmp_path / 'exported'
    module.export(state, reference['id'], '1.0.11', exported)
    assert inventory_tree(exported)[2] == preview['candidate']['directories']
    other = State(tmp_path / 'other')
    workflows.install_preset(other, 'repository-governance')
    assert module.import_bundle(other, exported)['digest'] == preview['digest']
    assert inventory_tree(Path(module.get(other, reference['id'], '1.0.11')['path']))[2] == preview['candidate']['directories']
    read_url = f"/api/{kind}-definitions/{reference['id']}/1.0.11/files/read"
    window = client.post(read_url, json={'base_digest': saved['digest'], 'path': 'extra.bin', 'limit': 3}).json()
    assert window['complete'] is False and window['next_offset'] == 3
    assert base64.b64decode(window['content_base64']) == raw_writes['extra.bin'][:3]
    assert cli.main(['--home', str(state.root), *command, 'file', reference['id'], '1.0.11', 'extra.bin',
                     '--base-digest', saved['digest'], '--limit', '3']) == 0
    assert json.loads(capsys.readouterr().out) == window
    full = client.post(read_url, json={'base_digest': saved['digest'], 'path': 'extra.bin'}).json()
    assert full['complete'] is True and full['next_offset'] is None
    assert base64.b64decode(full['content_base64']) == raw_writes['extra.bin']
    assert projects.list_projects(state) == [] and not (state.root / 'runs').exists()


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
