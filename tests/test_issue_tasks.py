"""Frozen issue data is part of a new task's original input, never a grant."""

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from ergora import handoff, issue_sources, issues, projects, reference, registrations, task_envelopes, tasks
from ergora.reference_inputs import execution_input
from test_handoff import evidence
from test_project_issues import bind, native, source
from test_registrations import installation, registration
from test_task_creation import _files, _inject
from test_work_agents import work_graph


@pytest.fixture
def issue_creation(source, registration, work_graph, tmp_path, request):
    if sys.platform != 'linux':
        pytest.skip('Source work-unit publication requires the Linux/WSL2 workspace execution contract')
    state, registered = registration
    provider = getattr(request, 'param', 'github')
    registered['tracker'] = {'kind': provider, 'project': 'team/repo' if provider == 'github' else 'team/sub/repo'}
    registrations.register(state, registered, 0)
    source.state = state
    bind(source, provider)
    source.raw = json.dumps(native(provider, '完整工单正文\nKeep permissions unchanged.')).encode()
    saved = issues.capture(state, 'demo', '7', 2)['snapshot']
    library, grant, _, execution, units = work_graph
    from ergora import workflow_definitions as workflows

    manifest = workflows.prepare_manifest(library.root, 'specialist-delivery', '1.0.0', grant, tmp_path / 'manifest')
    definition = {'schema_version': 3, 'task_id': 'issue-task', 'task_type': 'repository-governance', 'issue_id': '7',
        'source': {'snapshot_sha256': saved['sha256']},
        'input': {'goal': 'Implement the selected issue within the original scope', 'allowed_paths': ['src'],
            'acceptance': ['Preserve original contracts'], 'constraints': [], 'risk': 'standard', 'work_units': units},
        'composition': {'manifest': manifest['path'], 'manifest_digest': manifest['digest'],
            'review_protocol': 'dag-v1', 'review_instance': 'root/review', 'mode': 'text-only',
            'execution': {**execution, 'protocol': 'work-units-v2'},
            'backend_overrides': {path: {'binding': {'tool': 'codex', 'sandbox': 'current-container'},
                'reason': 'Explicit trusted-container test'} for path in execution['assignments'].values()},
            'diversity': {'policy': 'allow-same'}}}
    return source, registered, definition, saved


@pytest.mark.parametrize('issue_creation', ['github', 'gitlab'], indirect=True)
def test_offline_publication_preserves_full_origin_and_uses_a_distinct_input(issue_creation, monkeypatch):
    source, registered, definition, saved = issue_creation
    state = source.state
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'unused-credential')
    binding = state.project('demo')['bindings']['tracker']
    projects.bind(state, 'demo', 'tracker', {**binding, 'token_env': 'ERGORA_FIXTURE_ISSUE_TOKEN'}, 2)
    monkeypatch.delenv('ERGORA_FIXTURE_ISSUE_TOKEN')
    # A credential-reference edit is not an origin edit. Capture revision2 and
    # current execution revision3 remain separate, without another tracker GET.
    preview = tasks.preview(state, 'demo', definition, 3)
    assert preview == tasks.preview(state, 'demo', definition, 3)
    document = preview['files']['task.spec.json']
    assert preview['schema_version'] == 3 and document['schema_version'] == 7
    assert document['issue_source'] == saved and saved['payload']['observation']['context_only'] is True
    selected = execution_input(document)
    assert selected.spec == preview['files']['compiled.json']['spec']
    assert selected.stage_material() == {'issue_source': saved}
    assert selected.artifact_protocol == 'stage-artifacts-v1'
    assert selected.task_queue('dev') == 'dev.composition-v7'
    assert selected.request_root(Path('requests')) == Path('requests-composition-v7')
    selected.require_submission()
    assert not Path(registered['execution']['state_directory']).exists()
    created = tasks.create(state, 'demo', definition, 3, preview['preview_sha256'])
    assert created['status'] == 'published' and created['created_revision'] == 3
    assert created['composition']['issue_source']['observed_project'] == {'id': 'demo', 'revision': 2}
    assert tasks.create(state, 'demo', definition, 3, preview['preview_sha256']) == created
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope'] == document
    runtime = Path(registered['execution']['state_directory'])
    original = _files(runtime)
    shutil.rmtree(Path(definition['composition']['manifest']))
    with state.connect() as db:
        db.execute('DELETE FROM issue_snapshots')
    projects.bind(state, 'demo', 'tracker', {'tool': 'manual'}, 3)
    assert tasks.resume_create(state, 'demo', definition['task_id'], 4, created['intent_sha256'])['status'] == 'published'
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope']['issue_source'] == saved
    assert _files(runtime) == original and len(source.calls) == 1
    assert not any((runtime / name).exists() for name in ('requests', 'requests-composition-v7', 'receipts'))


@pytest.mark.parametrize('difference', ['host', 'api-path', 'namespace', 'local-id', 'native-id'])
def test_wrong_origins_or_changed_native_identity_cannot_publish(issue_creation, difference):
    source, registered, definition, saved = issue_creation
    state = source.state
    binding = state.project('demo')['bindings']['tracker']
    revision = 2
    if difference in ('host', 'api-path', 'namespace'):
        changed = {**binding, **({'project': 'other/repo'} if difference == 'namespace' else
            {'api_url': source.url.replace('127.0.0.1', 'localhost') if difference == 'host' else source.url + '/other-api'})}
        projects.bind(state, 'demo', 'tracker', changed, 2)
        revision = 3
    elif difference == 'local-id':
        definition['issue_id'] = '8'
    else:
        payload = deepcopy(saved['payload'])
        payload['observation']['issue']['native_id'] += 1
        with state.connect() as db:
            db.execute('UPDATE issue_snapshots SET document=? WHERE sha=?', (json.dumps(payload), saved['sha256']))
    with pytest.raises(ValueError, match='snapshot|source'):
        tasks.preview(state, 'demo', definition, revision)
    assert not Path(registered['execution']['state_directory']).exists()
    assert len(source.calls) == 1


def test_source_update_needs_another_creation_and_keeps_the_original_input(issue_creation):
    source, registered, definition, first = issue_creation
    state = source.state
    preview = tasks.preview(state, 'demo', definition, 2)
    created = tasks.create(state, 'demo', definition, 2, preview['preview_sha256'])
    runtime = Path(registered['execution']['state_directory'])
    old_bytes = _files(runtime)
    source.raw = json.dumps(native('github', 'Updated task text')).encode()
    second = issues.capture(state, 'demo', '7', 2)['snapshot']
    definition['source']['snapshot_sha256'] = second['sha256']
    revised = tasks.preview(state, 'demo', definition, 2)
    with pytest.raises(ValueError, match='different creation intent'):
        tasks.create(state, 'demo', definition, 2, revised['preview_sha256'])
    assert _files(runtime) == old_bytes
    definition['task_id'] = 'issue-task-r2'
    revised = tasks.preview(state, 'demo', definition, 2)
    tasks.create(state, 'demo', definition, 2, revised['preview_sha256'])
    assert tasks.creation(state, 'demo', 'issue-task')['intent_sha256'] == created['intent_sha256']
    assert tasks.show(state, 'demo', 'issue-task')['admission_envelope']['issue_source'] == first
    assert tasks.show(state, 'demo', 'issue-task-r2')['admission_envelope']['issue_source'] == second


def test_interrupted_source_publication_recovers_without_snapshot_or_current_binding(issue_creation, monkeypatch):
    source, registered, definition, saved = issue_creation
    state = source.state
    preview = tasks.preview(state, 'demo', definition, 2)
    with monkeypatch.context() as patch:
        _inject(patch, '''
original_init = _Creation.__init__
def initialize(self, *args):
    original_init(self, *args)
    write = self.core.write
    def interrupted(path, value, **kwargs):
        if path == self.target / 'task.spec.json':
            raise OSError('source publication loss')
        return write(path, value, **kwargs)
    self.core.write = interrupted
_Creation.__init__ = initialize
''')
        with pytest.raises(ValueError, match='source publication loss'):
            tasks.create(state, 'demo', definition, 2, preview['preview_sha256'])
    pending = tasks.creation(state, 'demo', definition['task_id'])
    assert pending['status'] == 'pending' and pending['intent_sha256'] == preview['preview_sha256']
    with state.connect() as db:
        db.execute('DELETE FROM issue_snapshots')
    shutil.rmtree(Path(definition['composition']['manifest']))
    projects.bind(state, 'demo', 'tracker', {'tool': 'manual'}, 2)
    completed = tasks.resume_create(state, 'demo', definition['task_id'], 3, pending['intent_sha256'])
    assert completed['status'] == 'published' and completed['created_revision'] == 2
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope'] == preview['files']['task.spec.json']
    assert len(source.calls) == 1


def test_source_input_reads_with_only_the_standard_library(issue_creation):
    source, _, definition, saved = issue_creation
    document = tasks.preview(source.state, 'demo', definition, 2)['files']['task.spec.json']
    code = '''import json,sys
from pathlib import Path
from ergora.reference_inputs import execution_input
selected=execution_input(json.load(sys.stdin))
assert not any(name in sys.modules for name in ('jsonschema','temporalio','mcp'))
print(json.dumps({'source':selected.stage_material(),'queue':selected.task_queue('dev')}))
'''
    result = subprocess.run([sys.executable, '-S', '-B', '-c', code], input=json.dumps(document), capture_output=True,
        text=True, timeout=20, env={**os.environ, 'PYTHONPATH': str(Path(reference.__file__).parent.parent)})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {'source': {'issue_source': saved}, 'queue': 'dev.composition-v7'}


def test_source_version_publishes_through_its_real_adapter_and_keeps_the_original_payload(issue_creation, monkeypatch, tmp_path):
    pytest.importorskip('temporalio')
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from temporalio import workflow
    from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner

    source, _, definition, saved = issue_creation
    document = tasks.preview(source.state, 'demo', definition, 2)['files']['task.spec.json']
    selected = execution_input(document)
    run = selected.workflow_type()()
    run.spec, run.admission = selected.spec, document
    context = run.context('inventory', selected.spec['request']['repository']['starting_sha'])
    from ergora.reference_workflows import StageResultsWorkflow
    assert context == StageResultsWorkflow.context(run, 'inventory', selected.spec['request']['repository']['starting_sha'])
    assert context['admission']['issue_source'] == saved
    config = {name: str(tmp_path / name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    activities = selected.activities({**config, 'trusted_receipts': True})
    assert activities.registered()

    class Client:
        async def start_workflow(self, entrypoint, original, **options):
            assert original == document and options['task_queue'] == 'dev.composition-v7'
            assert workflow._Definition.must_from_run_fn(entrypoint).name == 'ErgoraCompositionWorkflowV7'
            return 'original-handle'

    async def exercise():
        SandboxedWorkflowRunner().prepare_workflow(workflow._Definition.must_from_class(selected.workflow_type()))
        job = await activities.submit(context)
        assert job['context']['admission'] == document
        assert await selected.start(Client(), id='dev-task/issue-task', task_queue='dev') == 'original-handle'

    asyncio.run(exercise())
    assert (tmp_path / 'requests-composition-v7' / 'issue-task' / (context['job_id'] + '.json')).exists()
    assert not (tmp_path / 'requests').exists() and not (tmp_path / 'requests-composition-v6').exists()


def test_handoff_binds_complete_original_input_and_preserves_source_offline(issue_creation, evidence, tmp_path):
    source, _, definition, saved = issue_creation
    preview = tasks.preview(source.state, 'demo', definition, 2)
    document = preview['files']['task.spec.json']
    selected = execution_input(document)
    index, binary = evidence
    index.update(task_id=definition['task_id'], workflow_id='dev-task/' + definition['task_id'],
                 request_sha256=selected.spec['request_sha256'], profile_sha256=selected.spec['profile_sha256'])
    selection = preview['files']['agent-bindings.json']
    index['contract'].update(spec=selected.spec, spec_sha256=task_envelopes.identity(selected.spec),
        agent_bindings=selection, agent_bindings_sha256=task_envelopes.identity(selection), **selected.evidence_contract())
    index['original_outcome'].update(task_id=definition['task_id'], request_sha256=selected.spec['request_sha256'],
                                     admission_sha256=document['sha256'])
    index['original_outcome_sha256'] = task_envelopes.identity(index['original_outcome'])
    path = tmp_path / 'issue-source.zip'
    exported = handoff.create(index, lambda artifact: binary, path)
    assert handoff.verify(path, sha256=exported['sha256'])['status'] == 'verified'
    with zipfile.ZipFile(path) as archive:
        assert json.loads(archive.read('manifest.json'))['index']['contract']['original_input']['issue_source'] == saved
    # A different valid source can share the same legacy spec. It must not
    # replace the complete input bound by the original outcome's admission SHA.
    changed = deepcopy(saved)
    changed['payload']['observation']['issue']['body'] += '\nChanged after execution'
    changed['sha256'] = task_envelopes.identity(changed['payload'])
    substituted = task_envelopes.wrap(selected.spec, document['composition'], changed)
    index['contract'].update(execution_input(substituted).evidence_contract())
    with pytest.raises(ValueError, match='outcome identity'):
        handoff.create(index, lambda artifact: binary, tmp_path / 'substituted.zip')


@pytest.mark.parametrize('character', ['a', '中'])
def test_source_plus_ancestor_prompt_limit_rejects_without_publishing(issue_creation, character):
    source, registered, definition, _ = issue_creation
    state = source.state
    graph = task_envelopes.manifest_graph(tasks.preview(state, 'demo', definition, 2)['files']['task.spec.json']['composition']['manifest'])
    # Raw tracker response still fits its 1 MiB read contract. The supplied
    # source plus inherited leaf prompt exceeds the actual prompt byte limit.
    leaf = next(item for item in graph['instances'] if item['path'] == 'root/work/implementation')
    size = (1_000_000 - len(leaf['prompt'].encode())) // len(character.encode())
    source.raw = json.dumps(native('github', character * size), ensure_ascii=False).encode()
    saved = issues.capture(state, 'demo', '7', 2)['snapshot']
    definition['source']['snapshot_sha256'] = saved['sha256']
    with pytest.raises(ValueError, match='input byte limit'):
        tasks.preview(state, 'demo', definition, 2)
    assert not Path(registered['execution']['state_directory']).exists()


@pytest.mark.parametrize('character', ['a', '中'])
def test_complete_first_context_is_checked_at_publication_and_runtime(issue_creation, monkeypatch, character):
    pytest.importorskip('temporalio')
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from dev_platform.workflow import StopWork

    source, registered, definition, saved = issue_creation
    state = source.state
    preview = tasks.preview(state, 'demo', definition, 2)
    selected = execution_input(preview['files']['task.spec.json'])
    starting = selected.spec['request']['repository']['starting_sha']
    encode = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    available = 1_000_000 - len(encode(selected.inventory_context(starting)))
    body_bytes = len(encode(saved['payload']['observation']['issue']['body'])) - 2 + available
    count, remainder = divmod(body_bytes, len(character.encode()))
    body = character * count + 'a' * remainder
    monkeypatch.setattr(issues, 'now', lambda: saved['first_observed_at'])
    source.raw = json.dumps(native('github', body), ensure_ascii=False).encode()
    exact = issues.capture(state, 'demo', '7', 2)['snapshot']
    definition['source']['snapshot_sha256'] = exact['sha256']
    preview = tasks.preview(state, 'demo', definition, 2)
    selected = execution_input(preview['files']['task.spec.json'])
    run = selected.workflow_type()()
    run.spec, run.admission = selected.spec, selected.document
    assert len(encode(run.context('inventory', starting))) == 1_000_000
    tasks.create(state, 'demo', definition, 2, preview['preview_sha256'])
    original = _files(Path(registered['execution']['state_directory']))
    source.raw = json.dumps(native('github', body + character), ensure_ascii=False).encode()
    over = issues.capture(state, 'demo', '7', 2)['snapshot']
    definition['source']['snapshot_sha256'] = over['sha256']
    with pytest.raises(ValueError, match='inventory context exceeds'):
        tasks.preview(state, 'demo', definition, 2)
    document = task_envelopes.wrap(selected.spec, selected.document['composition'], over)
    run.admission = document
    with pytest.raises(StopWork, match='inventory context exceeds'):
        run.context('inventory', starting)
    assert _files(Path(registered['execution']['state_directory'])) == original


def test_snapshot_validation_keeps_strict_types_and_all_saved_bytes(source):
    bind(source, 'github')
    source.raw = json.dumps(native('github')).encode()
    saved = issues.capture(source.state, 'demo', '7', 2)['snapshot']
    issue_sources.validate_snapshot(saved)
    for change in ('boolean-revision', 'boolean-native', 'huge-native', 'body', 'etag', 'extra'):
        corrupted = deepcopy(saved)
        observed = corrupted['payload']['observation']
        if change == 'boolean-revision': observed['project']['revision'] = True
        elif change == 'boolean-native': observed['issue']['native_id'] = True
        elif change == 'huge-native': observed['issue']['native_id'] = 10 ** 1000
        elif change == 'body': observed['issue']['body'] += 'Changed'
        elif change == 'etag': observed['response']['etag'] = False
        else: observed['issue']['extra'] = 'unexpected'
        with pytest.raises(ValueError, match='snapshot'):
            issue_sources.validate_snapshot(corrupted)
