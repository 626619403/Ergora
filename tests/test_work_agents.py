"""Specialist work uses original units, immutable selection and stage ownership."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

import pytest

from ergora import agent_definitions, agent_runs, agents, task_envelopes, tasks, workflow_definitions as workflows
from ergora.review_dags import WorkDelivery
from test_registrations import installation, registration
from test_task_creation import creation_project
from test_workflow_definitions import EXAMPLES


@pytest.fixture
def work_graph(tmp_path):
    from ergora.state import State

    state = State(tmp_path / 'definitions')
    for path in (EXAMPLES / 'agents/kernel-implementer', EXAMPLES / 'agents/validation-implementer',
                 EXAMPLES / 'agents/architecture-reviewer', *sorted((EXAMPLES / 'composition/agents').iterdir())):
        agent_definitions.import_bundle(state, path)
    for name in ('structure-review', 'correctness-review', 'test-value-review', 'parallel-review',
                 'specialist-work', 'specialist-delivery'):
        workflows.import_bundle(state, EXAMPLES / 'composition' / name)
    grant = json.loads((EXAMPLES / 'composition/preview-grant.json').read_bytes())
    graph = workflows.preview(state.root, 'specialist-delivery', '1.0.0', grant)
    execution = {'protocol': 'work-units-v1', 'instance': 'root/work', 'mode': 'workspace-task-mcp',
                 'assignments': {'implementation': 'root/work/implementation', 'validation': 'root/work/validation'}}
    units = [{'id': 'implementation', 'depends_on': [], 'paths': ['src'], 'instructions': 'Implement'},
             {'id': 'validation', 'depends_on': ['implementation'], 'paths': ['src/tests'], 'instructions': 'Validate'}]
    return state, grant, graph, execution, units


def test_one_graph_projects_work_and_review_without_reinterpreting_root_task(work_graph):
    _, _, graph, execution, units = work_graph
    delivery = WorkDelivery(graph, execution, 'root/review', units)
    assert delivery.work.predecessors['root/work/validation'] == ('root/work/implementation',)
    assert delivery.work.input_ports('root/work/implementation') == {
        'bindings': {'task': 'task'}, 'values': {'task': {'kind': 'task'}}, 'sources': []}
    assert delivery.work.input_ports('root/work/validation')['values'] == {
        'root/work/implementation#result': {'kind': 'work-result', 'instance': 'root/work/implementation'}}
    ports = delivery.review.input_ports('root/review/structure/review')
    assert ports['sources'] == ['root/work/validation']
    assert ports['values']['root/work/validation#result']['kind'] == 'work-result'
    from ergora.review_dags import ReviewDAG
    with pytest.raises(ValueError, match='external'):
        ReviewDAG(graph, 'root/review')


@pytest.mark.parametrize('failure', ['missing', 'duplicate', 'extra', 'order', 'scope', 'extra-leaf', 'reverse-stage'])
def test_work_mapping_refuses_ambiguous_or_unexecuted_graphs(work_graph, failure):
    _, _, graph, execution, units = work_graph
    if failure == 'missing':
        del execution['assignments']['validation']
    elif failure == 'duplicate':
        execution['assignments']['validation'] = execution['assignments']['implementation']
    elif failure == 'extra':
        execution['assignments']['unknown'] = 'root/work/unknown'
    elif failure == 'order':
        units[1]['depends_on'] = []
    elif failure == 'scope':
        next(item for item in graph['instances'] if item['path'] == 'root/work/validation')['permissions']['write'] = ['workspace/docs']
    elif failure == 'extra-leaf':
        graph['instances'].append({**deepcopy(next(item for item in graph['instances'] if item['kind'] == 'agent')),
                                   'path': 'root/ignored'})
    else:
        next(item for item in graph['instances'] if item['path'] == 'root/work')['depends_on'] = ['root/review']
    with pytest.raises(ValueError, match='exactly|order|ceiling|cover|external'):
        WorkDelivery(graph, execution, 'root/review', units)


@pytest.fixture
def work_creation(creation_project, work_graph, tmp_path):
    if sys.platform != 'linux':
        pytest.skip('New workspace execution is explicitly Linux/WSL2')
    state, registration, definition = creation_project
    library, grant, _, execution, units = work_graph
    manifest = workflows.prepare_manifest(library.root, 'specialist-delivery', '1.0.0', grant, tmp_path / 'manifest')
    definition.update(schema_version=2, composition={'manifest': manifest['path'], 'manifest_digest': manifest['digest'],
        'review_protocol': 'dag-v1', 'review_instance': 'root/review', 'mode': 'text-only', 'execution': execution,
        'backend_overrides': {path: {'binding': {'tool': 'codex', 'sandbox': 'current-container'},
                                    'reason': 'Explicit trusted-container acceptance'} for path in execution['assignments'].values()},
        'diversity': {'policy': 'allow-same'}})
    definition['input']['work_units'] = units
    return state, registration, definition


@pytest.mark.parametrize('protocol,version', [('work-units-v1', 5), ('work-units-v2', 6)])
def test_work_creation_freezes_actual_writers_and_uses_its_own_input_route(work_creation, monkeypatch, protocol, version):
    pytest.importorskip('temporalio')
    from ergora import reference
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from ergora.reference_inputs import execution_input
    from temporalio.workflow import _Definition

    state, registered, definition = work_creation
    definition['composition']['execution']['protocol'] = protocol
    preview = tasks.preview(state, 'demo', definition, 1)
    document = preview['files']['task.spec.json']
    assert document['schema_version'] == version
    selected = execution_input(document)
    selected.require_submission()
    assert selected.task_queue('dev') == f'dev.composition-v{version}'
    assert selected.request_root(Path('requests')).name == f'requests-composition-v{version}'
    assert _Definition.must_from_run_fn(selected.entrypoint).name == f'ErgoraCompositionWorkflowV{version}'
    assert document['composition']['diversity']['implementer_backends'] == ['codex']
    assert len(document['composition']['execution']['members']) == 2
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    shutil.rmtree(Path(definition['composition']['manifest']))
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    intent = Path(registered['execution']['state_directory']) / 'ergora/task-creations' / (definition['task_id'] + '.intent.json')
    modified = json.loads(intent.read_bytes())
    modified['definition']['composition']['execution']['assignments']['validation'] = 'root/work/implementation'
    intent.write_text(json.dumps(modified))
    with pytest.raises(ValueError, match='composition differs'):
        tasks.creation(state, 'demo', definition['task_id'])


def test_diversity_compares_actual_writers_instead_of_the_project_default(work_creation):
    state, _, definition = work_creation
    option = definition['composition']
    # Project implementer remains command; all selected writers actually use Codex.
    option['backend_overrides']['root/review/structure/review'] = {
        'binding': {'tool': 'codex'}, 'reason': 'Actual review backend'}
    option['diversity'] = {'policy': 'require-distinct'}
    with pytest.raises(ValueError, match='different from the implementer'):
        tasks.preview(state, 'demo', definition, 1)
    option['diversity'] = {'policy': 'prefer-distinct', 'reason': 'Explicit fallback to the available backend'}
    document = tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']
    assert document['composition']['diversity']['same_backend_members'] == ['root/review/structure/review', 'root/review/test-value/review']


def test_workspace_mode_does_not_relax_the_public_read_only_leaf_entry(work_creation, work_graph, tmp_path):
    state, _, definition = work_creation
    library, _, _, _, _ = work_graph
    source = tmp_path / 'input'
    workflows.prepare_input_from_manifest(Path(definition['composition']['manifest']), 'root/work/implementation',
                                          b'Implement the assigned unit', source, 100000)
    for mode in ('text-only', 'task-mcp', 'workspace-task-mcp'):
        with pytest.raises(ValueError, match='cannot satisfy|not one of'):
            agent_runs.run_input(state, 'demo', source, mode=mode)
    assert agent_runs.runs(state, 'demo') == []


@pytest.mark.skipif(sys.platform != 'linux', reason='Native workflow/monitor is Linux/WSL2')
@pytest.mark.parametrize('case', ['full', 'source-artifact', 'source-claim', 'scope', 'commit', 'recovery',
                                  'recovery-commit', 'recovery-tamper', 'results', 'results-source-artifact'])
def test_formal_work_reuses_original_checks_commits_and_sources(tmp_path, case):
    pytest.importorskip('temporalio')
    pytest.importorskip('mcp')
    import subprocess

    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command',
                             'composition-work-' + case], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)
    if record.get('skip'):
        pytest.skip(record['skip'])
    assert record['case'] == case and record['original_owners']


def test_original_units_admit_an_independent_branch_while_a_nested_scope_is_full(work_creation, work_graph, tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    from ergora import reference
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from ergora.reference_inputs import execution_input
    from test_workflow_definitions import child, ref, write_bundle

    state, _, definition = work_creation
    library, grant, _, _, _ = work_graph
    group = deepcopy(workflows.library(library.root).get('specialist-work', '1.0.0')['definition'])
    group.update(id='limited-workers', resources=[])
    group['limits']['concurrency'] = 1
    group['nodes'][1].update(depends_on=[], inputs={'task': {'input': 'task'}})
    group['nodes'][-1]['depends_on'] = ['implementation', 'validation']
    saved = workflows.import_bundle(library, write_bundle(tmp_path / 'limited', group))
    outer = deepcopy(group)
    outer.update(id='independent-workers')
    outer['limits']['concurrency'] = 2
    outside = {**deepcopy(group['nodes'][0]), 'id': 'outside'}
    outer['nodes'] = [child('limited', ref(saved, 'workflow')), outside,
                      {'id': 'done', 'join': 'all', 'depends_on': ['limited', 'outside']}]
    saved = workflows.import_bundle(library, write_bundle(tmp_path / 'independent', outer))
    delivery = deepcopy(workflows.library(library.root).get('specialist-delivery', '1.0.0')['definition'])
    delivery.update(id='limited-delivery')
    delivery['nodes'][0]['ref'] = ref(saved, 'workflow')
    workflows.import_bundle(library, write_bundle(tmp_path / 'delivery', delivery))
    manifest = workflows.prepare_manifest(library.root, 'limited-delivery', '1.0.0', grant, tmp_path / 'limited-manifest')
    option = definition['composition']
    option.update(manifest=manifest['path'], manifest_digest=manifest['digest'])
    assignments = {'a': 'root/work/limited/implementation', 'b': 'root/work/limited/validation', 'c': 'root/work/outside'}
    option['execution']['assignments'] = assignments
    option['backend_overrides'] = {path: {'binding': {'tool': 'codex', 'sandbox': 'current-container'},
                                         'reason': 'Explicit trusted-container test'} for path in assignments.values()}
    definition['input']['work_units'] = [{'id': key, 'depends_on': [], 'paths': ['src/' + key], 'instructions': 'Test branch'}
                                         for key in assignments]
    document = tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']
    run = execution_input(document).workflow_type()()
    run.spec, run.admission = document['legacy_spec'], document

    async def exercise():
        started, gates = asyncio.Queue(), {key: asyncio.Event() for key in assignments}

        async def stage(stage, expected_sha=None, unit=None, dependencies=None):
            key = unit['id']
            await started.put(key)
            await gates[key].wait()
            receipt = {'actor': {'session_id': key}}
            run.results[stage] = receipt
            return receipt

        run.stage = stage
        task = asyncio.create_task(run.units())
        try:
            assert {await asyncio.wait_for(started.get(), 2), await asyncio.wait_for(started.get(), 2)} == {'a', 'c'}
            assert started.empty()  # b cannot reserve c's original unit slot.
            gates['c'].set()
            await asyncio.sleep(0)
            assert started.empty()
            gates['a'].set()
            assert await asyncio.wait_for(started.get(), 2) == 'b'
            gates['b'].set()
            await asyncio.wait_for(task, 2)
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    asyncio.run(exercise())


def test_cancellation_arriving_with_work_result_does_not_dispatch_a_successor(work_creation, monkeypatch):
    pytest.importorskip('temporalio')
    from ergora import reference
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from dev_platform.workflow import StopWork
    from ergora.reference_inputs import execution_input

    state, _, definition = work_creation
    document = tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']
    run = execution_input(document).workflow_type()()
    run.spec, run.admission = document['legacy_spec'], document
    calls = []

    async def stage(stage, expected_sha=None, unit=None, dependencies=None):
        calls.append(stage)
        run.cancel_reason = 'Cancellation arrived with the first work result'
        return {'actor': {'session_id': 'original-session'}}

    run.stage = stage
    with pytest.raises(StopWork, match='Cancellation arrived'):
        asyncio.run(run.units())
    assert calls == ['work:implementation']
