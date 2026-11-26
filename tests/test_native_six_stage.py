"""A parent template delegates one call to the original persistent task owners."""

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

import ergora.native.resources as native_resources
import ergora
import ergora.improvement.memory as memory
import ergora.definitions.skills as skill_assets
import ergora.development.application as tasks
import ergora.definitions.workflows as workflows
from ergora.development import envelopes as task_envelopes
from ergora.development.six_stage import invocation
from ergora.development.inputs import execution_input
from test_task_budget import budget_creation, budget_graph, full_creation, full_graph, work_creation, work_graph
from test_registrations import installation, registration
from test_task_creation import creation_project
from test_task_submission import native_client, _calls, _resume, _start, _status
from test_workflow_definitions import EXAMPLES


@pytest.fixture
def native_definition(budget_creation, budget_graph, tmp_path, request):
    state, registered, definition = budget_creation
    library, grant, _, _, _, _ = budget_graph
    source = tmp_path / 'native-parent'
    shutil.copytree(EXAMPLES / 'composition/native-development', source)
    document = json.loads((source / 'workflow.json').read_bytes())
    document['version'] = '1.2.0'
    child = workflows.get(library, 'prepared-delivery', '1.1.0')
    document['nodes'][0]['ref'].update(version='1.1.0', digest=child['digest'])
    variant = getattr(request, 'param', 'normal')
    if variant == 'sibling':
        document['nodes'].append({'id': 'unused', 'depends_on': ['development'], 'join': 'all'})
    elif variant == 'second-call':
        document['nodes'].append({**document['nodes'][0], 'id': 'other'})
    elif variant == 'ignored-output':
        document['outputs'] = {'result': {'input': 'task'}}
    elif variant == 'unsupported-formal-operation':
        document['schema_version'] = 2
        document['inputs'].append('evidence')
        document['nodes'].append({'id': 'proof', 'operation': 'verify-evidence', 'depends_on': [],
                                  'inputs': {'source': {'input': 'evidence'}}})
    (source / 'workflow.json').write_text(json.dumps(document))
    parent = workflows.import_bundle(library, source)
    position = 'root/development'
    if variant == 'nested':
        document['id'] = 'outer-parent'
        document['nodes'] = [{'id': 'delegation', 'ref': {'kind': 'workflow', 'id': 'native-development',
            'version': '1.2.0', 'digest': parent['digest']}, 'depends_on': [], 'inputs': {'task': {'input': 'task'}}}]
        document['outputs'] = {'result': {'node': 'delegation', 'output': 'result'}}
        (source / 'workflow.json').write_text(json.dumps(document))
        workflows.import_bundle(library, source)
        position = 'root/delegation/development'
    if variant == 'root':
        document = child['definition']
        position = 'root'
    manifest = workflows.prepare_manifest(library.root, document['id'], document['version'], grant, tmp_path / 'native-manifest')
    option = definition['composition']
    def nested(path):
        return position + '/' + path.removeprefix('root/development/')
    option['review_instance'] = nested(option['review_instance'])
    option['execution']['instance'] = nested(option['execution']['instance'])
    option['execution']['assignments'] = {key: nested(path) for key, path in option['execution']['assignments'].items()}
    for stage in ('inventory', 'plan'):
        option['preparation'][stage] = {key: nested(path) for key, path in option['preparation'][stage].items()}
    option['backend_overrides'] = {nested(path): value for path, value in option['backend_overrides'].items()}
    option.update(manifest=manifest['path'], manifest_digest=manifest['digest'],
                  native={'protocol': 'six-stage-v1', 'instance': position})
    definition['schema_version'] = 8
    return state, registered, definition


def _prepared(creation):
    state, _, definition = creation
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    return preview, preview['files']['task.spec.json']


def test_console_reads_publication_readiness_for_the_exact_prepared_preview(native_definition):
    pytest.importorskip('fastapi')
    pytest.importorskip('httpx')
    from fastapi.testclient import TestClient

    from ergora.configuration import projects
    from ergora.interfaces.web import create_app

    state, _, definition = native_definition
    task_id = definition['task_id']
    preview, _ = _prepared(native_definition)
    query = {key: preview[key] for key in ('prepare_sha256', 'preview_sha256')}
    path = f'/api/projects/demo/tasks/{task_id}/preparation'
    with TestClient(create_app(state.root), base_url='http://127.0.0.1:8977') as client:
        record = client.get(path).json()
        assert record['status'] == 'prepared'
        assert record['outcome']['record_sha256'] == query['preview_sha256']
        exact = client.get(path, params=query)
        assert exact.status_code == 200
        assert exact.json()['next_action'] == 'confirm_create'
        assert exact.json()['status'] == 'available'
        for key in query:
            unconfirmed = client.get(path, params={**query, key: '0' * 64}).json()
            assert unconfirmed['status'] == 'unconfirmed'
            assert unconfirmed['next_action'] == 'read_original_preparation'
        projects.bind(state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'later-model'}, 1)
        changed = client.get(path, params=query).json()
        assert changed['status'] == 'project_revision_changed'
        assert changed['next_action'] == 'read_original_preparation'
        assert client.get(path).json()['prepare_sha256'] == record['prepare_sha256']


@pytest.mark.parametrize('publication', ['pending', 'published'])
def test_console_and_cli_read_original_creation_after_an_uncertain_reply(
        native_definition, monkeypatch, tmp_path, capsys, publication):
    pytest.importorskip('fastapi')
    pytest.importorskip('httpx')
    from fastapi.testclient import TestClient

    from ergora.interfaces import cli
    from ergora.interfaces.web import create_app
    from test_task_budget import _worker_injection
    from test_task_creation import _files

    state, registered, definition = native_definition
    task_id = definition['task_id']
    root = Path(registered['execution']['state_directory'])
    preview, _ = _prepared(native_definition)
    query = {key: preview[key] for key in ('prepare_sha256', 'preview_sha256')}
    original = tasks.create
    definition_file = tmp_path / 'operator-definition.json'
    definition_file.write_text(json.dumps(definition), encoding='utf-8')
    body = {'definition': definition, 'revision': 1}
    base = '/api/projects/demo/tasks'
    headers = {'X-Ergora-Request': '1', 'Origin': 'http://127.0.0.1:8977'}

    def lose_reply(*args, **kwargs):
        assert original(*args, **kwargs)['status'] == 'published'
        raise OSError('Original creation reply was unavailable')

    with TestClient(create_app(state.root), base_url='http://127.0.0.1:8977', headers=headers) as client:
        preview_http = client.post(f'{base}/preview', json=body).json()
        assert preview_http['preview_sha256'] == query['preview_sha256']
        path = f'{base}/{task_id}/preparation'
        assert client.get(path, params=query).json()['next_action'] == 'confirm_create'
        with monkeypatch.context() as patch:
            if publication == 'published':
                patch.setattr(tasks, 'create', lose_reply)
            else:
                _worker_injection(patch, '', """
from ergora.development.runtime.creation import _Creation
def interrupt(self, record, *, save_intent):
    assert save_intent
    self.core.write(self.intent_path, record)
    raise OSError('Original creation was interrupted after saving its intent')
_Creation.publish = interrupt
""")
            uncertain = client.post(base, json={**body, **query})
            assert uncertain.status_code >= 400 and 'Original creation' in uncertain.text

        original_files = _files(root)
        original_record = client.get(f'{base}/{task_id}/creation').json()
        assert original_record['status'] == publication
        assert original_record['intent_sha256'] == query['preview_sha256']
        assert client.get(path).json()['budget_status']['status'] == 'available'
        assert client.post(f'{base}/preview', json=body).json() == preview_http
        readiness = client.get(path, params=query).json()
        assert readiness['status'] == publication and readiness['next_action'] == 'read_original_creation'
        argv = ['--home', str(state.root), 'task', 'preview', 'demo',
                '--definition', str(definition_file), '--revision', '1']
        assert cli.main(argv) == 0
        output = capsys.readouterr()
        assert json.loads(output.out) == preview
        assert f'Original creation for {task_id}: {publication}.' in output.err
        assert f'Next: task creation demo {task_id}' in output.err and 'task create' not in output.err
        assert _files(root) == original_files and not (root / 'ergora/task-submissions').exists()
        if publication == 'published':
            # An incomplete restore can retain the receipt without its intent or task files.
            prefix = root / 'ergora/task-creations'
            (prefix / f'{task_id}.intent.json').rename(tmp_path / 'original-intent.json')
            (root / 'tasks' / task_id).rename(tmp_path / 'original-task')
            assert (prefix / f'{task_id}.result.json').is_file()
            readiness = client.get(path, params=query).json()
            assert readiness['status'] == 'unconfirmed' and readiness['next_action'] == 'read_original_creation'
            assert 'without its original intent' in readiness['detail']


@pytest.fixture
def selected_context_task(native_definition, tmp_path):
    state, registered, definition = native_definition
    record = memory.save(state, 'demo', '保留所有祖先材料与测量来源。', {'uri': 'repo://design', 'revision': 'source-v1'})
    source = tmp_path / 'context-engineering'
    (source / 'references').mkdir(parents=True)
    (source / 'SKILL.md').write_text('---\nname: context-engineering\ndescription: Explicit complete context fixture\n---\nRead references/contract.md completely.\n')
    (source / 'references/contract.md').write_text('Original attachment: complete evidence, no automatic adoption.\n')
    imported = skill_assets.import_bundle(state, 'demo', source)
    head = next(item for item in skill_assets.versions(state, 'demo')['active'] if item['name'] == imported['name'])
    definition.update(schema_version=8, context={'root_version': '1.2.1',
        'memories': [{'id': record['id'], 'revision': record['revision']}],
        'skills': [{key: head[key] for key in ('name', 'digest', 'revision')}]})
    definition['composition']['mode'] = 'task-mcp'
    return state, registered, definition


def test_selected_sources_are_inherited_complete_and_sdk_free(selected_context_task, monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.workflow import _Definition

    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    state, _, definition = selected_context_task
    before = skill_assets.versions(state, 'demo')
    preview, document = _prepared(selected_context_task)
    selected = execution_input(document)
    assert document['schema_version'] == 12 and selected.task_queue('dev') == 'dev.composition-v12'
    assert _Definition.must_from_run_fn(selected.entrypoint).name == 'ErgoraCompositionWorkflowV12'
    frozen = task_envelopes.selected_context(document)
    assert frozen['selection'] == definition['context']
    assert frozen['base_manifest_digest'] == definition['composition']['manifest_digest']
    assert skill_assets.versions(state, 'demo') == before
    graph = task_envelopes.manifest_graph(document['composition']['manifest'])
    assert graph['root']['version'] == '1.2.1' and graph['root']['id'] == frozen['base_root']['id']
    assert document['composition']['native']['instance'] == definition['composition']['native']['instance']
    for leaf in [item for item in graph['instances'] if item['kind'] == 'agent']:
        assert frozen['memories'][0]['text'] in leaf['prompt']
        assert 'context-engineering' in {item.get('skill', {}).get('name') for item in leaf['resources']}
    assert selected.stage_material()['selected_context'] == document['context']
    code = ('import json,sys;sys.path.insert(0,' + repr(str(Path(ergora.__file__).parent.parent)) + ');'
        'from ergora.development.inputs import execution_input;v=execution_input(json.load(sys.stdin));'
        'v.require_submission();assert not any(n in sys.modules for n in ("jsonschema","yaml","temporalio","mcp"));'
        'print(v.task_queue("dev"))')
    child = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code], input=json.dumps(document),
                           capture_output=True, text=True, timeout=20)
    assert child.returncode == 0, child.stderr
    assert child.stdout.strip() == 'dev.composition-v12'
    changed = deepcopy(document)
    changed['context']['selection']['skills'][0]['revision'] += 1
    changed['sha256'] = task_envelopes.identity({key: value for key, value in changed.items() if key != 'sha256'})
    with pytest.raises(ValueError, match='selected task context'):
        execution_input(changed)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=preview['prepare_sha256'])
    assert created['status'] == 'published' and created['composition']['context'] == document['context']


@pytest.mark.parametrize('change', ['correction', 'deletion', 'expiry', 'head'])
def test_changed_selection_cannot_publish_a_stale_preview(selected_context_task, change):
    state, registered, definition = selected_context_task
    if change == 'expiry':
        from datetime import datetime, timedelta, timezone
        original = definition['context']['memories'][0]
        corrected = memory.save(state, 'demo', 'Short-lived selected record', {'uri': 'repo://expiry', 'revision': '1'},
            original['id'], original['revision'], expires_at=(datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat())
        original['revision'] = corrected['revision']
    preview, document = _prepared(selected_context_task)
    selected = definition['context']['memories'][0]
    if change == 'correction':
        memory.save(state, 'demo', 'New canonical text', {'uri': 'repo://design', 'revision': '2'}, selected['id'], selected['revision'])
    elif change == 'deletion':
        memory.delete(state, 'demo', selected['id'], selected['revision'])
    elif change == 'expiry':
        from test_task_budget import _worker_injection
        frozen = task_envelopes.selected_context(document)
        # Expire only while the publisher verifies Skill bytes, after an early
        # memory read could have passed. The record and preview stay unchanged.
        expiry = frozen['memories'][0]['expires_at']
        with pytest.MonkeyPatch.context() as patch:
            _worker_injection(patch, '', f'''
import ergora.improvement.memory as memory
import ergora.definitions.skills as skill_assets
clock = {{'at': {frozen['observed_at']!r}}}
memory.now = lambda: clock['at']
original_get = skill_assets.get
def checked_skill(*args, **kwargs):
    result = original_get(*args, **kwargs)
    clock['at'] = {expiry!r}
    return result
skill_assets.get = checked_skill
''')
            with pytest.raises(ValueError, match='expired'):
                tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=preview['prepare_sha256'])
        assert tasks.creation(state, 'demo', definition['task_id'])['status'] == 'not_recorded'
        return
    else:
        head = definition['context']['skills'][0]
        # A same-digest head move still changes its accepted adoption revision.
        skill_assets.move_head(state, 'demo', head['name'], head['digest'], head['revision'], 'rollback', 'Explicit head event')
    with pytest.raises(ValueError, match='changed|deleted'):
        tasks.preview(state, 'demo', definition, 1)
    with pytest.raises(ValueError, match='changed|deleted'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=preview['prepare_sha256'])
    assert tasks.creation(state, 'demo', definition['task_id'])['status'] == 'not_recorded'
    assert not (Path(registered['execution']['state_directory']) / 'tasks' / definition['task_id']).exists()


def test_selected_context_recovery_keeps_original_intent_after_source_deletion(selected_context_task, monkeypatch):
    from test_task_budget import _worker_injection

    state, registered, definition = selected_context_task
    preview, document = _prepared(selected_context_task)
    _worker_injection(monkeypatch, '', '''
from ergora.development.runtime.creation import _Creation
original_publish = _Creation.publish
def interrupted(self, record, *, save_intent):
    original_write = self.core.write
    def write(path, value, **kwargs):
        if path.parent == self.target:
            raise OSError('selected-context publication interrupted')
        return original_write(path, value, **kwargs)
    self.core.write = write
    return original_publish(self, record, save_intent=save_intent)
_Creation.publish = interrupted
''')
    with pytest.raises(ValueError, match='publication interrupted'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=preview['prepare_sha256'])
    monkeypatch.undo()
    pending = tasks.creation(state, 'demo', definition['task_id'])
    assert pending['status'] == 'pending'
    item = definition['context']['memories'][0]
    memory.delete(state, 'demo', item['id'], item['revision'])
    head = definition['context']['skills'][0]
    skill_assets.move_head(state, 'demo', head['name'], head['digest'], head['revision'], 'rollback', 'After intent')
    shutil.rmtree(definition['composition']['manifest'])
    skill = skill_assets.get(state, 'demo', head['digest'])
    shutil.rmtree(skill['path'])
    restored = tasks.resume_create(state, 'demo', definition['task_id'], 1, pending['intent_sha256'])
    assert restored['status'] == 'published' and restored['intent_sha256'] == preview['preview_sha256']
    saved = tasks.show(state, 'demo', definition['task_id'])['admission_envelope']
    assert saved == document and task_envelopes.selected_context(saved)['memories'][0]['text']


@pytest.mark.skipif(sys.platform != 'linux', reason='Original stage monitor requires Linux/WSL2')
def test_original_stages_receive_selected_context_after_canonical_changes(tmp_path):
    pytest.importorskip('temporalio')
    pytest.importorskip('mcp')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command',
        'composition-work-materials-context'], capture_output=True, text=True, timeout=210)
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)
    if record.get('skip'):
        pytest.skip(record['skip'])
    assert record['original_owners'] and record['canonical_changed_after_intent']
    assert len(record['selected_context_calls']) == record['original_model_slot_attempts']


@pytest.mark.parametrize('native_definition', ['normal', 'nested', 'root'], indirect=True)
def test_native_call_freezes_parent_chain_and_recovers_without_source(native_definition, monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.workflow import _Definition

    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    state, registered, definition = native_definition
    root = Path(registered['execution']['state_directory'])
    preflight = tasks.preview(state, 'demo', definition, 1)
    assert preflight['status'] == 'route-preview'
    assert preflight['route_admission'] == {'route': 'native-six-stage', 'status': 'admitted',
        'graph_status': 'valid', 'instance': definition['composition']['native']['instance']}
    assert 'preview_sha256' not in preflight and 'prepare_sha256' not in preflight
    assert preflight['runtime_status'] == 'not_queried'
    assert preflight['manifest_digest'] == definition['composition']['manifest_digest']
    assert preflight['project_revision'] == 1
    assert tasks.preparation(state, 'demo', definition['task_id'])['status'] == 'not_recorded'
    assert not root.exists()
    preview, document = _prepared(native_definition)
    selected = execution_input(document)
    assert document['schema_version'] == 12 and selected.task_queue('dev') == 'dev.composition-v12'
    assert selected.request_root(Path('requests')) == Path('requests-composition-v12')
    assert _Definition.must_from_run_fn(selected.entrypoint).name == 'ErgoraCompositionWorkflowV12'
    native = document['composition']['native']
    graph = task_envelopes.manifest_graph(document['composition']['manifest'])
    position = definition['composition']['native']['instance']
    chain = [position.rsplit('/', count)[0] for count in range(position.count('/'), -1, -1)]
    assert native == {'protocol': 'six-stage-v1', 'instance': position,
        'task_type': definition['task_type'], 'lineage': [
            {'instance': path, 'definition': next(item['ref'] for item in graph['instances'] if item['path'] == path)}
            for path in chain]}
    parent_text = (EXAMPLES / 'composition/native-development/instructions.md').read_text()
    assert all((parent_text in leaf['prompt']) == (position != 'root')
               for leaf in graph['instances'] if leaf['kind'] == 'agent')
    assert document['budget']['instance']['scope']['project_revision'] == 1
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=preview['prepare_sha256'])
    assert created['composition']['native'] == native
    shutil.rmtree(definition['composition']['manifest'])
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    assert execution_input(document).document == document
    # Original-input reading remains stdlib-only and never loads an SDK.
    code = ('import json,sys;sys.path.insert(0,' + repr(str(Path(ergora.__file__).parent.parent)) + ');'
        'from ergora.development.inputs import execution_input;'
        'v=execution_input(json.load(sys.stdin));v.require_submission();'
        'assert not any(n in sys.modules for n in ("jsonschema","temporalio","mcp"));print(v.task_queue("dev"))')
    child = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code], input=json.dumps(document),
                           capture_output=True, text=True, timeout=20)
    assert child.returncode == 0, child.stderr
    assert child.stdout.strip() == 'dev.composition-v12'
    changed = deepcopy(document)
    changed['composition']['native']['lineage'][0]['definition']['version'] = '9.0.0'
    changed['sha256'] = task_envelopes.identity({key: value for key, value in changed.items() if key != 'sha256'})
    with pytest.raises(ValueError, match='frozen instance and ancestors'):
        execution_input(changed)


@pytest.mark.parametrize('native_definition', ['sibling', 'second-call', 'ignored-output'], indirect=True)
def test_prepare_refuses_unexecuted_parent_branches(native_definition):
    state, registered, definition = native_definition
    root = Path(registered['execution']['state_directory'])
    preflight = tasks.preview(state, 'demo', definition, 1)
    assert preflight['status'] == 'route-preview'
    admission = preflight['route_admission']
    assert admission['status'] == 'blocked' and admission['graph_status'] == 'valid'
    assert admission['route'] == 'native-six-stage' and admission['instance'].startswith('root')
    assert any(text in admission['reason'] for text in ('parent must', 'cover exactly'))
    assert preflight['runtime_status'] == 'not_queried' and 'prepare_sha256' not in preflight
    assert not root.exists()

    # Explicit authorization continues to use the original supervised owner.
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'failed'
    root = Path(registered['execution']['state_directory'])
    stderr = (root / 'ergora/task-creations' / (definition['task_id'] + '.prepare-work/process/stderr.txt')).read_text()
    assert any(text in stderr for text in ('parent must', 'cover exactly'))
    with pytest.raises(ValueError, match='No confirmed complete preparation'):
        tasks.preview(state, 'demo', definition, 1)
    root = Path(registered['execution']['state_directory'])
    assert not (root / 'tasks' / definition['task_id']).exists()


@pytest.mark.parametrize('damage', ['missing', 'dangling'])
def test_preparation_evidence_cannot_be_reported_as_a_fresh_route_preview(native_definition, damage):
    state, registered, definition = native_definition
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    prefix = Path(registered['execution']['state_directory']) / 'ergora/task-creations'
    authorization = prefix / (definition['task_id'] + '.prepare.json')
    attempt = prefix / (definition['task_id'] + '.prepare-attempt.json')
    original_attempt = attempt.read_bytes()
    authorization.unlink()
    reason = 'evidence exists without its budget authorization'
    if damage == 'dangling':
        authorization.symlink_to('missing-original-authorization')
        reason = 'Symlinks are not accepted'

    with pytest.raises(ValueError, match=reason):
        tasks.preview(state, 'demo', definition, 1)
    with pytest.raises(ValueError, match=reason):
        tasks.preparation(state, 'demo', definition['task_id'])
    assert attempt.read_bytes() == original_attempt
    assert not authorization.exists()


@pytest.mark.parametrize('retained', ['task directory', 'creation intent', 'creation result'])
def test_incomplete_restore_cannot_report_an_original_task_as_a_fresh_route(native_definition, tmp_path, retained):
    state, registered, definition = native_definition
    preview, document = _prepared(native_definition)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=preview['prepare_sha256'])
    task_id = definition['task_id']
    root = Path(registered['execution']['state_directory'])
    prefix = root / 'ergora/task-creations'
    creation_evidence = {'task directory': root / 'tasks' / task_id,
                         'creation intent': prefix / (task_id + '.intent.json'),
                         'creation result': prefix / (task_id + '.result.json')}
    parked = tmp_path / 'incomplete-restore'
    parked.mkdir()
    hidden = [*prefix.glob(task_id + '.prepare*'),
              *(path for kind, path in creation_evidence.items() if kind != retained)]
    for path in hidden:
        path.rename(parked / path.name)

    with pytest.raises(ValueError, match='task or preparation evidence exists without its budget authorization'):
        tasks.preview(state, 'demo', definition, 1)
    assert creation_evidence[retained].exists() and not any(path.exists() for path in hidden)
    if retained == 'task directory':
        assert tasks.show(state, 'demo', task_id)['admission_envelope'] == document

    for path in hidden:
        (parked / path.name).rename(path)
    assert tasks.resume_create(state, 'demo', task_id, 1, created['intent_sha256']) == created


def test_native_route_preview_checks_known_inherited_skill_attachments(selected_context_task, tmp_path):
    from ergora.development import context as task_context

    state, registered, definition = selected_context_task
    option = definition['composition']
    working = tmp_path / 'derived'
    with task_context.selected_manifest(state, 'demo', option, definition.pop('context'), working) as (derived, _):
        source = tmp_path / 'base-with-inherited-attachments'
        shutil.copytree(derived['manifest'], source)
    option.update(manifest=str(source), manifest_digest=derived['manifest_digest'], mode='text-only')

    preview = tasks.preview(state, 'demo', definition, 1)
    assert preview['route_admission'] == {'route': 'native-six-stage', 'status': 'blocked', 'graph_status': 'valid',
        'instance': 'root/development/review/correctness/review',
        'reason': 'Complete Skill attachments require task-mcp mode'}
    assert preview['runtime_status'] == 'not_queried'
    assert tasks.preparation(state, 'demo', definition['task_id'])['status'] == 'not_recorded'
    assert not Path(registered['execution']['state_directory']).exists()

    option['mode'] = 'task-mcp'
    assert tasks.preview(state, 'demo', definition, 1)['route_admission']['status'] == 'admitted'
    assert not Path(registered['execution']['state_directory']).exists()

    option['mode'] = 'text-only'
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'failed' and prepared['outcome']['cleanup_confirmed']
    root = Path(registered['execution']['state_directory'])
    progress = root / 'ergora/task-creations' / (definition['task_id'] + '.prepare-work')
    stderr = (progress / 'process/stderr.txt').read_text()
    assert preview['route_admission']['reason'] in stderr and preview['route_admission']['instance'] in stderr
    assert not (root / 'tasks').exists()


@pytest.mark.parametrize('native_definition', ['unsupported-formal-operation'], indirect=True)
def test_definition_preview_locates_the_same_unsupported_formal_operation(native_definition):
    from ergora.interfaces import composition_preview

    state, registered, definition = native_definition
    option = definition['composition']
    manifest = Path(option['manifest'])
    frozen = workflows.inspect_manifest(manifest, material=True)
    for folder in ('agent-definitions', 'workflow-definitions'):
        shutil.copytree(manifest / 'assets' / folder, state.root / folder)
    root, grant = frozen['manifest']['root'], frozen['manifest']['grant']
    inspection = composition_preview.preview(state.root, root['id'], root['version'], grant,
        {'route': 'formal-task', 'project': 'demo', 'revision': 1, 'definition': definition})
    expected = {'route': 'native-six-stage', 'status': 'blocked', 'graph_status': 'valid', 'instance': 'root/proof',
                'reason': 'Candidate verification evidence reads require standalone graph execution'}
    assert inspection['composition'] == frozen['composition']
    assert inspection['route_admission']['capability'] == tasks.preview(state, 'demo', definition, 1)['route_admission'] == expected
    directory = Path(registered['execution']['state_directory'])
    assert not directory.exists()
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'failed' and prepared['outcome']['cleanup_confirmed']
    output = directory / 'ergora/task-creations' / (definition['task_id'] + '.prepare-work/process/stderr.txt')
    assert expected['reason'] in output.read_text() and expected['instance'] in output.read_text()
    assert not (directory / 'tasks').exists()


def test_definition_preview_uses_selected_context_and_keeps_the_base_identity(selected_context_task):
    from ergora.interfaces import composition_preview

    state, registered, definition = selected_context_task
    option = definition['composition']
    option['mode'] = 'text-only'
    base = Path(option['manifest'])
    frozen = workflows.inspect_manifest(base, material=True)
    for folder in ('agent-definitions', 'workflow-definitions'):
        shutil.copytree(base / 'assets' / folder, state.root / folder)
    root, grant = frozen['manifest']['root'], frozen['manifest']['grant']
    inspection = composition_preview.preview(state.root, root['id'], root['version'], grant,
        {'route': 'formal-task', 'project': 'demo', 'revision': 1, 'definition': definition})
    observed = inspection['route_admission']
    assert inspection['composition'] == frozen['composition']
    assert observed['manifest_digest'] == frozen['digest'] and observed['preview_sha256'] == frozen['manifest']['preview_sha256']
    assert observed['capability'] == {'route': 'native-six-stage', 'status': 'blocked', 'graph_status': 'valid',
        'instance': 'root/development/review/correctness/review', 'reason': 'Complete Skill attachments require task-mcp mode'}
    directory = Path(registered['execution']['state_directory'])
    assert not directory.exists()
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'failed' and prepared['outcome']['cleanup_confirmed']
    stderr = (directory / 'ergora/task-creations' / (definition['task_id'] + '.prepare-work/process/stderr.txt')).read_text()
    assert observed['capability']['instance'] in stderr and observed['capability']['reason'] in stderr


def test_native_selection_cannot_claim_the_wrapper_or_another_stage(native_definition):
    state, _, definition = native_definition
    option = definition['composition']
    graph = workflows.inspect_manifest(Path(option['manifest']), material=True)['composition']
    for position in ('root', option['execution']['instance']):
        selection = {**option, 'native': {'protocol': 'six-stage-v1', 'instance': position}}
        with pytest.raises(ValueError, match='must be direct child|must belong'):
            invocation(graph, selection, definition['task_type'])


@pytest.mark.parametrize('recovery', ['normal', 'wrong-memo', 'other-full-input'])
def test_native_lost_start_reuses_original_run_and_full_input(native_definition, native_client, monkeypatch, recovery):
    pytest.importorskip('temporalio')
    pytest.importorskip('mcp')
    state, registered, definition = native_definition
    interpreter = Path(registered['execution']['installation']) / '.venv'
    if not interpreter.exists():
        interpreter.symlink_to(sys.prefix, target_is_directory=True)
    config = Path(registered['execution']['config_directory'])
    codex = config / 'selected-codex'
    codex.symlink_to(sys.executable)
    (config / 'claude').symlink_to(sys.executable)
    monkeypatch.setenv('PATH', str(config) + os.pathsep + os.environ.get('PATH', ''))
    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/local'))
    from agent_platform.sandbox import container_identity
    identity = container_identity()
    if identity is None:
        pytest.skip('Reference task admission requires an acknowledged container boundary')
    (config / 'platform.json').write_text(json.dumps({'execution_enabled': True, 'codex_bin': str(codex),
        'current_container_trust_acknowledged': True, 'container_boundary': identity}))
    (config / 'codex.toml').write_text('model = "native-input-probe-only"\n')
    preview, document = _prepared(native_definition)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=preview['prepare_sha256'])
    creation = (state, registered, definition, created)
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'lost-response')
    with pytest.raises(ValueError, match='timed out'):
        _start(creation)
    assert _status(creation)['status'] == 'unknown'
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'normal')
    server = Path(registered['execution']['state_directory']) / 'sdk-fixture/server.json'
    saved = json.loads(server.read_bytes())
    assert saved['spec'] == document
    if recovery == 'normal':
        recovered = _resume(creation)
        assert recovered['status'] == 'submitted' and recovered['run_id'] == 'original-run'
        assert _start(creation) == recovered
    else:
        if recovery == 'wrong-memo':
            saved['memo'] = {}
        else:
            saved['spec']['composition']['native']['lineage'][0]['definition']['version'] = '9.0.0'
            saved['spec']['sha256'] = task_envelopes.identity({key: value for key, value in saved['spec'].items() if key != 'sha256'})
        server.write_text(json.dumps(saved))
        with pytest.raises(ValueError, match='matching submission memo|original task spec differs'):
            _resume(creation)
    assert _calls(creation).count('start') == 1
