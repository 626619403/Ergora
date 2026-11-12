"""New preparation selections keep original stage ownership and complete materials."""

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import tasks, workflow_definitions as workflows
from ergora.reference_inputs import execution_input
from ergora.review_dags import WorkDelivery
from test_work_agents import work_creation, work_graph
from test_registrations import installation, registration
from test_task_creation import creation_project
from test_workflow_definitions import EXAMPLES


@pytest.fixture
def full_graph(work_graph):
    library, grant, _, execution, units = work_graph
    for name in ('preparation-guide', 'prepared-delivery'):
        workflows.import_bundle(library, EXAMPLES / 'composition' / name)
    graph = workflows.preview(library.root, 'prepared-delivery', '1.0.0', grant)
    preparation = {'protocol': 'preparation-v1', 'inventory': 'root/preparation/inventory',
                   'plan': 'root/preparation/plan', 'mode': 'task-mcp', 'repository_paths': ['src']}
    return library, grant, graph, {**execution, 'protocol': 'work-units-v2'}, units, preparation


@pytest.fixture
def full_creation(work_creation, full_graph, tmp_path):
    state, registered, definition = work_creation
    library, grant, _, execution, _, preparation = full_graph
    manifest = workflows.prepare_manifest(library.root, 'prepared-delivery', '1.0.0', grant, tmp_path / 'full-manifest')
    definition['schema_version'] = 4
    definition['composition'].update(manifest=manifest['path'], manifest_digest=manifest['digest'],
                                     execution=execution, preparation=preparation)
    return state, registered, definition


@pytest.mark.parametrize('failure', ['omitted', 'unexecuted-edge', 'overlap', 'read-ceiling', 'work-coverage'])
def test_all_stage_projection_refuses_partial_or_unexecuted_selections(full_graph, failure):
    _, _, graph, execution, units, preparation = full_graph
    if failure == 'omitted':
        preparation = None  # The old contract still rejects hidden preparation leaves.
    elif failure == 'unexecuted-edge':
        next(node for node in graph['instances'] if node['path'] == 'root/preparation')['depends_on'] = ['root/work']
    elif failure == 'overlap':
        preparation['inventory'] = 'root/work/implementation'
    elif failure == 'read-ceiling':
        next(node for node in graph['instances'] if node['path'] == preparation['plan'])['permissions']['read'] = ['definitions']
    else:
        preparation['repository_paths'] = ['src/other']
    with pytest.raises(ValueError, match='cover|root task|inspector|read ceiling'):
        WorkDelivery(graph, execution, 'root/review', units, preparation=preparation)


def test_frozen_preparation_survives_source_removal_and_keeps_its_original_route(full_creation, monkeypatch):
    pytest.importorskip('temporalio')
    from ergora import reference
    from temporalio.workflow import _Definition

    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    state, registered, definition = full_creation
    preview = tasks.preview(state, 'demo', definition, 1)
    document = preview['files']['task.spec.json']
    selected = execution_input(document)
    selected.require_submission()
    assert document['schema_version'] == 8 and preview['schema_version'] == 4
    assert selected.task_queue('dev') == 'dev.composition-v8'
    assert selected.request_root(Path('requests')) == Path('requests-composition-v8')
    assert _Definition.must_from_run_fn(selected.entrypoint).name == 'ErgoraCompositionWorkflowV8'
    code = ('import json,sys;sys.path.insert(0,' + repr(str(Path(reference.__file__).parent.parent)) + ');'
            'from ergora.reference_inputs import execution_input;'
            'selected=execution_input(json.load(sys.stdin));selected.require_submission();'
            'assert not any(name in sys.modules for name in ("jsonschema","temporalio","mcp"));'
            'print(selected.task_queue("dev"))')
    isolated = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code], input=json.dumps(document),
                              capture_output=True, text=True, timeout=20)
    assert isolated.returncode == 0, isolated.stderr
    assert isolated.stdout.strip() == 'dev.composition-v8'
    assert {member['role'] for member in document['composition']['preparation']['members'].values()} == {'inspector', 'planner'}
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    shutil.rmtree(definition['composition']['manifest'])
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    runtime = Path(registered['execution']['state_directory'])
    intent = runtime / 'ergora/task-creations' / (definition['task_id'] + '.intent.json')
    modified = json.loads(intent.read_bytes())
    modified['definition']['composition']['preparation']['repository_paths'] = ['src/other']
    intent.write_text(json.dumps(modified))
    with pytest.raises(ValueError, match='composition differs'):
        tasks.creation(state, 'demo', definition['task_id'])


def test_text_only_cannot_silently_drop_required_skill_attachments(full_creation):
    state, _, definition = full_creation
    definition['composition']['preparation']['mode'] = 'text-only'
    with pytest.raises(ValueError, match='attachments require task-mcp'):
        tasks.preview(state, 'demo', definition, 1)


@pytest.mark.skipif(sys.platform != 'linux', reason='Native stage monitor requires Linux/WSL2')
@pytest.mark.parametrize('case', ['full', 'capacity', 'unread', 'source-artifact', 'issue-source'])
def test_real_preparation_calls_and_original_stage_results(tmp_path, case):
    pytest.importorskip('temporalio')
    pytest.importorskip('mcp')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command',
        'composition-work-materials-' + case], capture_output=True, text=True, timeout=150)
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)
    if record.get('skip'):
        pytest.skip(record['skip'])
    assert record['case'] == case and record['original_owners']
