"""A parent template delegates one call to the original persistent task owners."""

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import reference, task_envelopes, tasks, workflow_definitions as workflows
from ergora.native_six_stage import invocation
from ergora.reference_inputs import execution_input
from test_task_budget import budget_creation, full_creation, full_graph, work_creation, work_graph
from test_registrations import installation, registration
from test_task_creation import creation_project
from test_task_submission import native_client, _calls, _resume, _start, _status
from test_workflow_definitions import EXAMPLES


@pytest.fixture
def native_definition(budget_creation, full_graph, tmp_path, request):
    state, registered, definition = budget_creation
    library, grant, _, _, _, _ = full_graph
    source = tmp_path / 'native-parent'
    shutil.copytree(EXAMPLES / 'composition/native-development', source)
    document = json.loads((source / 'workflow.json').read_bytes())
    variant = getattr(request, 'param', 'normal')
    if variant == 'sibling':
        document['nodes'].append({'id': 'unused', 'depends_on': ['development'], 'join': 'all'})
    elif variant == 'second-call':
        document['nodes'].append({**document['nodes'][0], 'id': 'other'})
    elif variant == 'ignored-output':
        document['outputs'] = {'result': {'input': 'task'}}
    (source / 'workflow.json').write_text(json.dumps(document))
    parent = workflows.import_bundle(library, source)
    position = 'root/development'
    if variant == 'nested':
        document['id'] = 'outer-parent'
        document['nodes'] = [{'id': 'delegation', 'ref': {'kind': 'workflow', 'id': 'native-development',
            'version': '1.0.0', 'digest': parent['digest']}, 'depends_on': [], 'inputs': {'task': {'input': 'task'}}}]
        document['outputs'] = {'result': {'node': 'delegation', 'output': 'result'}}
        (source / 'workflow.json').write_text(json.dumps(document))
        workflows.import_bundle(library, source)
        position = 'root/delegation/development'
    manifest = workflows.prepare_manifest(library.root, document['id'], '1.0.0', grant, tmp_path / 'native-manifest')
    option = definition['composition']
    def nested(path):
        return position + '/' + path.removeprefix('root/')
    option['review_instance'] = nested(option['review_instance'])
    option['execution']['instance'] = nested(option['execution']['instance'])
    option['execution']['assignments'] = {key: nested(path) for key, path in option['execution']['assignments'].items()}
    for stage in ('inventory', 'plan'):
        option['preparation'][stage] = nested(option['preparation'][stage])
    option['backend_overrides'] = {nested(path): value for path, value in option['backend_overrides'].items()}
    option.update(manifest=manifest['path'], manifest_digest=manifest['digest'],
                  native={'protocol': 'six-stage-v1', 'instance': position})
    definition['schema_version'] = 6
    return state, registered, definition


def _prepared(creation):
    state, _, definition = creation
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    return preview, preview['files']['task.spec.json']


@pytest.mark.parametrize('native_definition', ['normal', 'nested'], indirect=True)
def test_native_call_freezes_parent_chain_and_recovers_without_source(native_definition, monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.workflow import _Definition

    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    state, registered, definition = native_definition
    preview, document = _prepared(native_definition)
    selected = execution_input(document)
    assert document['schema_version'] == 10 and selected.task_queue('dev') == 'dev.composition-v10'
    assert selected.request_root(Path('requests')) == Path('requests-composition-v10')
    assert _Definition.must_from_run_fn(selected.entrypoint).name == 'ErgoraCompositionWorkflowV10'
    native = document['composition']['native']
    graph = task_envelopes.manifest_graph(document['composition']['manifest'])
    position = definition['composition']['native']['instance']
    chain = [position.rsplit('/', count)[0] for count in range(position.count('/'), -1, -1)]
    assert native == {'protocol': 'six-stage-v1', 'instance': position,
        'task_type': definition['task_type'], 'lineage': [
            {'instance': path, 'definition': next(item['ref'] for item in graph['instances'] if item['path'] == path)}
            for path in chain]}
    parent_text = (EXAMPLES / 'composition/native-development/instructions.md').read_text()
    assert all(parent_text in leaf['prompt'] for leaf in graph['instances'] if leaf['kind'] == 'agent')
    assert document['budget']['instance']['scope']['project_revision'] == 1
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=preview['prepare_sha256'])
    assert created['composition']['native'] == native
    shutil.rmtree(definition['composition']['manifest'])
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    assert execution_input(document).document == document
    # Original-input reading remains stdlib-only and never loads an SDK.
    code = ('import json,sys;sys.path.insert(0,' + repr(str(Path(reference.__file__).parent.parent)) + ');'
        'from ergora.reference_inputs import execution_input;'
        'v=execution_input(json.load(sys.stdin));v.require_submission();'
        'assert not any(n in sys.modules for n in ("jsonschema","temporalio","mcp"));print(v.task_queue("dev"))')
    child = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code], input=json.dumps(document),
                           capture_output=True, text=True, timeout=20)
    assert child.returncode == 0, child.stderr
    assert child.stdout.strip() == 'dev.composition-v10'
    changed = deepcopy(document)
    changed['composition']['native']['lineage'][0]['definition']['version'] = '9.0.0'
    changed['sha256'] = task_envelopes.identity({key: value for key, value in changed.items() if key != 'sha256'})
    with pytest.raises(ValueError, match='frozen instance and ancestors'):
        execution_input(changed)


@pytest.mark.parametrize('native_definition', ['sibling', 'second-call', 'ignored-output'], indirect=True)
def test_prepare_refuses_unexecuted_parent_branches(native_definition):
    state, registered, definition = native_definition
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'failed'
    root = Path(registered['execution']['state_directory'])
    stderr = (root / 'ergora/task-creations' / (definition['task_id'] + '.prepare-work/process/stderr.txt')).read_text()
    assert any(text in stderr for text in ('parent must', 'cover exactly'))
    with pytest.raises(ValueError, match='No confirmed complete preparation'):
        tasks.preview(state, 'demo', definition, 1)
    root = Path(registered['execution']['state_directory'])
    assert not (root / 'tasks' / definition['task_id']).exists()


def test_native_selection_cannot_claim_root_or_another_stage(native_definition):
    state, _, definition = native_definition
    option = definition['composition']
    graph = workflows.inspect_manifest(Path(option['manifest']), material=True)['composition']
    for position in ('root', option['execution']['instance']):
        selection = {**option, 'native': {'protocol': 'six-stage-v1', 'instance': position}}
        with pytest.raises(ValueError, match='ordinary parent|must belong'):
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
    (config / 'platform.json').write_text(json.dumps({'execution_enabled': True, 'codex_bin': str(codex)}))
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
