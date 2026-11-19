"""Shipped recipes use the existing immutable definitions and formal contracts."""

import json
import runpy
from copy import deepcopy
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

import ergora.native.resources as native_resources
import ergora.definitions.agents as agent_definitions
import ergora.configuration.registrations as registrations
import ergora.development.application as tasks
import ergora.definitions.workflows as workflows
from ergora.development import budget as reference_budget
from ergora.development import envelopes as task_envelopes
from ergora.development.inputs import execution_input
from ergora.development.dags import ReviewDAG, WorkDelivery
from ergora.storage.state import State
from test_registrations import installation, registration


def _selected_engineering_review(state):
    example = Path(__file__).resolve().parents[1] / 'examples/composition/pr-review-selected'
    installed = workflows.install_preset(state, 'engineering-review')
    base = installed['root']
    document = json.loads((example / 'root.revision.example.json').read_bytes())
    published = workflows.revise(state, base['id'], base['version'], base['digest'], document, publish=True)
    return installed, published


def test_engineering_specialists_use_real_roles_resources_and_review_slots(tmp_path):
    state = State(tmp_path / 'state')
    installed, published = _selected_engineering_review(state)
    assert _selected_engineering_review(state)[1] == published
    base = installed['root']
    original = workflows.get(state, base['id'], base['version'], material=True)
    root = published['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    assert len(ReviewDAG(workflows.preview(state.root, base['id'], base['version'], grant), 'root').members) == 3
    selected = workflows.preview(state.root, root['id'], root['version'], grant)
    assert set(ReviewDAG(selected, 'root').members) == {
        'root/structure/review', 'root/correctness/review', 'root/test-value/review',
        'root/performance', 'root/resource-lifecycle'}
    # Prepare the remaining optional methods through the same standard revision,
    # without installing a second copy of any root resource.
    expanded = deepcopy(root)
    expanded.update(id='all-selected-methods', version='1.0.0')
    available = {item['id']: item for item in installed['agents']}
    for name in ('dependency', 'security', 'measurement'):
        expanded['nodes'].insert(-1, {'id': name, 'ref': available['ergora-' + name + '-reviewer'],
            'role': 'reviewer', 'review_requirement': 'required', 'depends_on': [],
            'permissions': root['permissions'], 'inputs': {'task': {'input': 'task'}}})
        expanded['nodes'][-1]['depends_on'].append(name)
    workflows.revise(state, root['id'], root['version'], published['digest'], expanded, publish=True)
    manifest = workflows.prepare_manifest(state.root, expanded['id'], expanded['version'], grant, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    dag = ReviewDAG(graph, 'root')
    expected_specialties = {
        'root/structure/review': ('ergora-structure-reviewer', ('ergora-structure-reviewer-skill',)),
        'root/correctness/review': ('ergora-correctness-reviewer', ('ergora-correctness-reviewer-skill',)),
        'root/test-value/review': ('ergora-test-value-reviewer', ('ergora-test-value-reviewer-skill',)),
        'root/performance': ('ergora-performance-analyst', ('ergora-performance-analyst-skill',
            'ergora-performance-diagnosis-skill', 'ergora-opt-profiling-proposal-context')),
        'root/resource-lifecycle': ('ergora-resource-lifecycle-reviewer', ('ergora-resource-lifecycle-reviewer-skill',)),
        'root/dependency': ('ergora-dependency-reviewer', ('ergora-dependency-reviewer-skill',)),
        'root/security': ('ergora-security-reviewer', ('ergora-security-reviewer-skill',)),
        'root/measurement': ('ergora-measurement-reviewer', ('ergora-measurement-reviewer-skill',)),
    }
    methods = {}
    for path, (identity, required_resources) in expected_specialties.items():
        reference = available[identity]
        original_agent = agent_definitions.get(state, reference['id'], reference['version'], material=True)
        resources = {resource['id']: resource for resource in original_agent['resources']}
        methods[path] = [resources[resource_id] for resource_id in required_resources]
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    assert dag.members.keys() == expected_specialties.keys()
    for path, leaf in dag.members.items():
        expected_agent = available[expected_specialties[path][0]]
        assert leaf['ref'] == expected_agent
        assert leaf['role'] == 'reviewer' and leaf['review_requirement'] == 'required'
        assert leaf['permissions'] == root['permissions']
        floor = 'max' if path == 'root/performance' else 'high'
        assert leaf['backend_request']['model'] == leaf['invocation_minimum']['model'] == 'gpt-6.1-sol'
        assert leaf['backend_request']['reasoning_effort'] == leaf['invocation_minimum']['reasoning_effort'] == floor
        prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), path,
            b'Complete exact original requirements, source, callers and original check artifacts.',
            tmp_path / path.replace('/', '-'), 1_000_000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        for method in methods[path]:
            inherited = next(resource for resource in leaf['resources'] if resource['id'] == method['id'])
            assert inherited['kind'] == method['kind']
            assert inherited.get('digest', inherited.get('sha256')) == method.get('digest', method.get('sha256'))
            assert inherited['text'] == method['text'] and method['text'] in actual['prompt']
            assert {source['instance'] for source in inherited['sources']} == {path}
            assert all(source['definition'] == expected_agent for source in inherited['sources'])
        for resource in original['resources']:
            inherited = next(item for item in leaf['resources'] if item['id'] == resource['id'])
            assert inherited['text'] == resource['text'] and resource['text'] in actual['prompt']
            assert {source['instance'] for source in inherited['sources']} == {'root'}
        assert all(resource['text'] in actual['prompt'] for resource in leaf['resources'])


@pytest.mark.parametrize('domain', ['pretraining', 'posttraining'])
def test_training_review_common_contract_reaches_domain_and_general_inputs(tmp_path, domain):
    state = State(tmp_path / 'state')
    installed = workflows.install_preset(state, domain + '-review')
    root_ref = installed['root']
    original = workflows.get(state, root_ref['id'], root_ref['version'], material=True)
    root = original['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'], grant, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    common = next(resource for resource in original['resources'] if resource['kind'] == 'instructions')
    for path in ('root/domain/review', 'root/general/structure/review'):
        leaf = next(item for item in graph['instances'] if item['path'] == path)
        inherited = next(resource for resource in leaf['resources'] if resource['id'] == common['id'])
        assert inherited['text'] == common['text']
        assert {source['instance'] for source in inherited['sources']} == {'root'}
        prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), path,
            b'The same complete original source, requirements and check evidence.',
            tmp_path / path.replace('/', '-'), 1_000_000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        assert common['text'] in actual['prompt']
        assert all(resource['text'] in actual['prompt'] for resource in leaf['resources'])


def test_selected_review_members_are_fixed_slots_in_existing_development_projection(tmp_path):
    state = State(tmp_path / 'state')
    _, selected = _selected_engineering_review(state)
    installed = workflows.install_preset(state, 'repository-governance')
    base = next(item for item in installed['workflows'] if item['id'] == 'ergora-governance-delivery')
    root = workflows.get(state, base['id'], base['version'])['definition']
    root.update(id='selected-engineering-delivery', version='1.0.0')
    next(node for node in root['nodes'] if node['id'] == 'review')['ref'] = {
        'kind': 'workflow', 'id': selected['definition']['id'],
        'version': selected['definition']['version'], 'digest': selected['digest']}
    workflows.revise(state, base['id'], base['version'], base['digest'], root, publish=True)
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    graph = workflows.preview(state.root, root['id'], root['version'], grant)
    units = native_resources.template_details('repository-governance')['input']['work_units']
    execution = {'protocol': 'work-units-v1', 'instance': 'root/work', 'mode': 'workspace-task-mcp',
                 'assignments': {unit['id']: 'root/work/' + unit['id'] for unit in units}}
    preparation = {'protocol': 'preparation-dag-v1', 'mode': 'task-mcp', 'repository_paths': ['.'],
        **{stage: {'instance': 'root/preparation/' + stage, 'coordinator': 'root/preparation/' + stage + '/coordinator'}
           for stage in ('inventory', 'plan')}}
    delivery = WorkDelivery(graph, execution, 'root/review', units, preparation=preparation)
    preparation['members'] = {path: leaf for group in delivery.preparation.values() for path, leaf in group['dag'].members.items()}
    slots = reference_budget.call_slots({'preparation': preparation, 'execution': execution, 'members': delivery.review.members})
    review_slots = {key: value for key, value in slots.items() if key.startswith('review:')}
    assert review_slots == {'review:' + path: path for path in delivery.review.members}
    assert len(review_slots) == 5
    assert len(slots) == len(preparation['members']) + len(delivery.work.members) + len(delivery.review.members)


@pytest.mark.parametrize('direction', ['memory-tuning', 'activation-recompute', 'cpu-offloading',
    'cuda-graphs', 'sequence-packing', 'parallelism', 'megatron-fsdp', 'hierarchical-cp',
    'tp-dp-overlap', 'moe-dispatcher', 'moe-overlap', 'profiling', 'memory-snapshot', 'recipe-model', 'model-verification', 'cluster-resiliency', 'low-precision', 'kernel', 'performance-diagnosis'])
def test_direction_roots_select_scoped_experts_and_freeze_their_complete_method(tmp_path, direction):
    state = State(tmp_path / 'state')
    installed = workflows.install_preset(state, 'optimization-' + direction)
    specialists = {item['id']: item for item in installed['agents']}
    assert installed == workflows.install_preset(state, 'optimization-' + direction)
    root = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'], grant, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    expert = {'profiling': 'ergora-performance-analyst', 'performance-diagnosis': 'ergora-performance-analyst',
              'kernel': 'ergora-kernel-designer'}.get(direction, 'ergora-opt-' + direction + '-expert')
    expected = {'root/design': 'ergora-experiment-designer', 'root/specialist': expert,
                'root/measurement/review': 'ergora-measurement-reviewer'}
    if direction == 'low-precision':
        expected['root/kernel'] = 'ergora-kernel-designer'
    leaves = {item['path']: item for item in graph['instances'] if item['kind'] == 'agent'}
    assert set(leaves) == set(expected)
    reference = specialists[expert]
    method = agent_definitions.get(state, reference['id'], reference['version'], material=True)['resources']
    method = [resource for resource in method if resource['kind'] in ('context', 'skill')]
    assert method
    nodes = {item['id']: item for item in root['nodes']}
    assert nodes['analysis-results']['depends_on'] == ['specialist', 'design']
    if direction == 'low-precision':
        assert nodes['kernel']['inputs'] == {'task': {'node': 'analysis-results', 'output': 'result'}}
        assert nodes['measurement']['depends_on'] == ['kernel']
        assert nodes['measurement']['inputs'] == {'task': {'node': 'kernel', 'output': 'result'}}
        assert set(nodes['gather']['depends_on']) == {'specialist', 'design', 'kernel', 'measurement'}
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    for path, leaf in leaves.items():
        assert leaf['ref'] == specialists[expected[path]]
        assert not leaf['permissions']['write'] and not leaf['permissions']['shell'] and not leaf['permissions']['network']
        prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), path,
            b'Use supplied original experiment evidence; retain missing measurements.',
            tmp_path / path.replace('/', '-'), 100000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        assert all(resource['text'] in actual['prompt'] for resource in leaf['resources'])
        if path == 'root/specialist':
            for material in method:
                assert material['text'] in actual['prompt']
                inherited = next(resource for resource in leaf['resources'] if resource['id'] == material['id'])
                assert inherited['text'] == material['text']
                assert {source['instance'] for source in inherited['sources']} == {path}


def _publish_selected_moe(state):
    example = Path(__file__).resolve().parents[1] / 'examples/composition/optimization-selected-moe'
    return example, runpy.run_path(str(example / 'publish.py'))['publish'](state, example)


def test_selected_moe_revision_freezes_shared_policy_for_every_actual_leaf(tmp_path):
    state = State(tmp_path / 'state')
    example, published = _publish_selected_moe(state)
    assert _publish_selected_moe(state)[1] == published
    publication = json.loads((example / 'publication.json').read_bytes())
    source = publication['policy_source']
    original = workflows.get(state, source['id'], source['version'], material=True)
    assert original['digest'] == source['digest']
    manifest = Path(published['manifest']['path'])
    graph = workflows.inspect_manifest(manifest, material=True)['composition']
    task = json.loads((example / 'task.example.json').read_bytes())
    option = task['composition']
    delivery = WorkDelivery(graph, option['execution'], option['review_instance'],
        task['input']['work_units'], preparation=option['preparation'])
    assert len(delivery.preparation['inventory']['dag'].members) == 5
    assert len(delivery.preparation['plan']['dag'].members) == 5
    assert len(delivery.work.members) == len(delivery.review.members) == 4
    assert all(item['review_requirement'] == 'required' for item in delivery.review.members.values())
    kernel = 'root/development/preparation/plan/kernel'
    coordinator = option['preparation']['plan']['coordinator']
    assert kernel in delivery.preparation['plan']['dag'].predecessors[coordinator]
    assert set(delivery.preparation['inventory']['dag'].predecessors[option['preparation']['inventory']['coordinator']]) == {
        'root/development/preparation/inventory/' + name for name in ('flow', 'profile', 'dispatcher', 'overlap')}
    leaves = {item['path']: item for item in graph['instances'] if item['kind'] == 'agent'}
    assert len(leaves) == 18
    common = [resource for resource in original['resources'] if resource['kind'] != 'instructions']
    policy = next(resource for resource in common if resource['id'] == 'ergora-bottleneck-optimization-skill')
    assert policy['digest'] == '90aaeb7c6041ac0f10fa8eebae48978a504a1cb213fafc0a537078fb8961ea17'
    for name, details in publication['policy_files'].items():
        delivery_ref = publication['published']['delivery']
        current = workflows.get(state, delivery_ref['id'], delivery_ref['version'])
        assert current['files'][name]['sha256'] == details['sha256']
        assert current['files'][name]['executable_bits'] == details['executable_bits']
        assert (Path(current['path']) / name).read_bytes() == (Path(original['path']) / name).read_bytes()
    grant = json.loads((example / 'grant.json').read_bytes())
    for cap in (1, 2):
        narrowed = deepcopy(grant)
        narrowed['limits']['concurrency'] = cap
        preview = workflows.preview(state.root, published['root']['id'], published['root']['version'], narrowed)
        assert len([item for item in preview['instances'] if item['kind'] == 'agent']) == 18
        assert all(item['concurrency_scopes'][0]['limit'] == cap for item in preview['instances'] if item['kind'] == 'agent')
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    for path, leaf in leaves.items():
        prepared = workflows.prepare_input_from_manifest(manifest, path,
            b'Original exact source, workload and complete supplied predecessor results.',
            tmp_path / path.replace('/', '-'), 1000000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        assert actual['composition'] == graph
        for resource in common:
            inherited = next(item for item in leaf['resources'] if resource['id'] == item['id'])
            assert inherited['text'] == resource['text'] and resource['text'] in actual['prompt']
            assert {source['instance'] for source in inherited['sources']} == {'root/development'}
        writable = leaf['role'] == 'implementer'
        assert bool(leaf['permissions']['write']) is writable and leaf['permissions']['shell'] is writable
        assert not leaf['permissions']['network']
        if leaf['role'] == 'planner':
            assert leaf['backend_request']['reasoning_effort'] == leaf['invocation_minimum']['reasoning_effort'] == 'max'


@pytest.mark.skipif(sys.platform != 'linux', reason='Budgeted native preparation requires Linux/WSL2')
def test_selected_moe_example_prepares_exact_eighteen_slots_on_original_native_owner(registration, tmp_path):
    state, project = registration
    example, published = _publish_selected_moe(state)
    definition = json.loads((example / 'task.example.json').read_bytes())
    definition['starting_sha'] = subprocess.check_output(['git', '-C', project['repo'], 'rev-parse', 'HEAD'], text=True).strip()
    definition['issue_id'] = '1'
    definition['composition'].update(manifest=published['manifest']['path'], manifest_digest=published['manifest']['digest'])
    project['allowed_paths'] = definition['input']['allowed_paths']
    registrations.register(state, project, 0)
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    document = preview['files']['task.spec.json']
    execution_input(document).require_submission()
    assert document['schema_version'] == 12 and len(document['budget']['slots']) == 18
    assert document['budget']['instance'] == prepared['budget']
    assert document['composition']['native']['instance'] == 'root/development'
    assert document['composition']['preparation']['protocol'] == 'preparation-dag-v1'
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=prepared['prepare_sha256'])
    assert created['status'] == 'published' and created['execution_started_by_operation'] is False
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope'] == document


@pytest.mark.parametrize('kind', native_resources.TEMPLATES)
def test_bundled_recipe_is_restartable_and_freezes_complete_ancestors(tmp_path, kind):
    state = State(tmp_path / 'state')
    available = next(item for item in workflows.presets() if item['id'] == kind)
    installed = workflows.install_preset(state, kind)
    assert installed['root'] == available['root']
    assert installed == workflows.install_preset(state, kind)
    assert installed['execution_authorized'] is False
    root = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    before = workflows.preview(state.root, root['id'], root['version'], grant)
    leaves = [item for item in before['instances'] if item['kind'] == 'agent']
    planners = {item['id'] for item in installed['agents']
                if 'planner' in agent_definitions.get(state, item['id'], item['version'])['definition']['roles']}
    for item in leaves:
        if item['ref']['id'] in planners:
            assert item['backend_request']['reasoning_effort'] == item['invocation_minimum']['reasoning_effort'] == 'max'
        assert item['backend_request']['model'] == item['invocation_minimum']['model'] == 'gpt-6.1-sol'
        assert item['backend_request']['reasoning_effort'] == item['invocation_minimum']['reasoning_effort']
        if item['role'] in ('planner', 'experiment-planner', 'kernel-tuner') or item['ref']['id'] == 'ergora-api-contract-author':
            assert item['invocation_minimum']['reasoning_effort'] == 'max'
        assert all(resource['text'] in item['prompt'] for resource in item['resources'])
        assert any(source['instance'] == 'root' for resource in item['resources'] for source in resource['sources'])
    if kind == 'training-optimization':
        assert {item['role'] for item in leaves} == {'experiment-planner', 'performance-analyst', 'kernel-tuner', 'reviewer'}
        assert all(not item['permissions']['write'] and not item['permissions']['shell'] for item in leaves)
        selected = 'root/analysis/design'
    else:
        units = native_resources.template_details(kind)['input']['work_units']
        execution = {'protocol': 'work-units-v1', 'instance': 'root/development/work', 'mode': 'workspace-task-mcp',
                     'assignments': {unit['id']: 'root/development/work/' + unit['id'] for unit in units}}
        preparation = {'protocol': 'preparation-dag-v1',
            **{stage: {'instance': 'root/development/preparation/' + stage,
                       'coordinator': 'root/development/preparation/' + stage + '/coordinator'}
               for stage in ('inventory', 'plan')}, 'mode': 'task-mcp',
            'repository_paths': native_resources.template_details(kind)['input']['allowed_paths']}
        delivery = WorkDelivery(before, execution, 'root/development/review', units, preparation=preparation)
        assert set(delivery.work.members) == set(execution['assignments'].values())
        for stage, group in delivery.preparation.items():
            coordinator, dag = group['coordinator'], group['dag']
            prefix = 'root/development/preparation/' + stage + '/'
            assert {path: leaf['ref']['id'] for path, leaf in dag.members.items()} == {
                prefix + 'module': 'ergora-refactoring-engineer',
                prefix + 'validation': 'ergora-compatibility-validator',
                coordinator: 'ergora-development-preparer'}
            assert set(dag.predecessors[coordinator]) == set(dag.input_ports(coordinator)['sources']) == {
                prefix + 'module', prefix + 'validation'}
            assert dag.terminal_sources() == dag.members.keys()
        assert len(leaves) == len(units) + 6 + len(delivery.review.members)
        assert {item['backend_request']['tool'] for item in leaves if item['role'] == 'reviewer'} == {'codex'}
        assert {item['backend_request']['tool'] for item in leaves if item['role'] == 'implementer'} == {'codex'}
        selected = 'root/development/review/structure/review'
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'], grant, tmp_path / 'manifest')
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    assert workflows.inspect_manifest(Path(manifest['path']), material=True)['composition'] == before
    prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), selected, b'Inspect supplied evidence',
                                                     tmp_path / 'input', 100000)
    assert workflows.inspect_input(Path(prepared['path']))['digest'] == prepared['digest']


def test_preset_listing_and_installation_are_real_offline_cli_operations(tmp_path):
    home = tmp_path / 'state'
    command = [sys.executable, '-I', '-m', 'ergora', '--home', str(home), 'composition']
    listed = subprocess.run([*command, 'presets'], capture_output=True, text=True, check=True, timeout=30)
    assert not home.exists()
    assert json.loads(listed.stdout) == workflows.presets()
    installed = subprocess.run([*command, 'install-preset', 'training-optimization'],
                               capture_output=True, text=True, check=True, timeout=30)
    assert json.loads(installed.stdout)['runtime'] == 'proposal-leaves'
    assert workflows.definitions(State(home))


@pytest.mark.parametrize('preset, leaf_path, role', [
    ('training-flow-map', 'root/map', 'performance-analyst'),
    ('evidence-report', 'root/author', 'implementer'),
    ('optimization-report', 'root/author', 'implementer'),
    ('optimization-report-concise', 'root/author', 'implementer'),
])
def test_readonly_analysis_presets_freeze_complete_material_without_changing_training_versions(
        tmp_path, preset, leaf_path, role):
    state = State(tmp_path / 'state')
    original = [workflows.install_preset(state, name)['root']
                for name in ('training-optimization', 'evidence-report',
                             'optimization-report')]
    installed = workflows.install_preset(state, preset)
    assert workflows.install_preset(state, preset) == installed
    assert [workflows.get(state, item['id'], item['version'])['digest'] for item in original] == [
        item['digest'] for item in original]
    definition = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    grant = {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}
    manifest = workflows.prepare_manifest(state.root, definition['id'], definition['version'], grant, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    leaf, = (item for item in graph['instances'] if item['kind'] == 'agent')
    assert leaf['path'] == leaf_path and leaf['role'] == role
    assert not leaf['permissions']['write'] and not leaf['permissions']['shell'] and not leaf['permissions']['network']
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), leaf['path'],
        b'Analyze only the supplied exact evidence; retain unknown runtime facts.', tmp_path / 'input', 100000)
    actual = workflows.inspect_input(Path(prepared['path']), material=True)
    assert actual['composition'] == graph
    assert all(resource['text'] in actual['prompt'] for resource in leaf['resources'])
    assert {source['instance'] for resource in leaf['resources'] for source in resource['sources']} == {'root', leaf_path}


def test_bottleneck_path_retains_kernel_assessment_and_original_task_in_frozen_leaves(tmp_path):
    state = State(tmp_path / 'state')
    installed = workflows.install_preset(state, 'training-optimization')
    assert workflows.install_preset(state, 'training-optimization') == installed
    definition = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    nodes = {item['id']: item for item in definition['nodes']}
    assert {name: nodes[name]['depends_on'] for name in ('flow', 'analysis', 'kernel', 'measurement')} == {
        'flow': [], 'analysis': ['flow'], 'kernel': ['analysis'], 'measurement': ['kernel']}
    assert set(nodes['gather']['depends_on']) == {'flow', 'analysis', 'kernel', 'measurement'}
    assert all(nodes[name]['inputs'] == {'task': {'input': 'task'}}
               for name in ('flow', 'analysis', 'kernel', 'measurement'))
    grant = {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}
    manifest = workflows.prepare_manifest(state.root, definition['id'], definition['version'], grant, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    leaves = {item['path']: item for item in graph['instances'] if item['kind'] == 'agent'}
    assert set(leaves) == {'root/flow/map', 'root/analysis/design', 'root/analysis/profile',
                           'root/kernel/assess', 'root/measurement/review'}
    parent_materials = workflows.get(state, definition['id'], definition['version'], material=True)['resources']
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    task = b'Original exact source and contract. Complete supplied predecessor result envelopes remain task data.'
    for path, leaf in leaves.items():
        assert not leaf['permissions']['write'] and not leaf['permissions']['shell'] and not leaf['permissions']['network']
        prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), path, task,
            tmp_path / path.replace('/', '-'), 100000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        assert actual['composition'] == graph and task.decode() in actual['prompt']
        assert all(resource['text'] in actual['prompt'] for resource in leaf['resources'])
        assert any(source['instance'] == 'root' for resource in leaf['resources'] for source in resource['sources'])
        for material in parent_materials:
            inherited = next(resource for resource in leaf['resources'] if resource['id'] == material['id'])
            assert inherited['text'] == material['text'] and material['text'] in actual['prompt']
            assert {source['instance'] for source in inherited['sources']} == {'root'}


@pytest.mark.parametrize('identity,preset', [
    ('ergora-structure-review', 'repository-governance'),
    ('ergora-correctness-review', 'repository-governance'),
    ('ergora-test-value-review', 'repository-governance'),
    ('ergora-pretraining-review', 'pretraining-review'),
    ('ergora-posttraining-review', 'posttraining-review'),
])
def test_bundled_review_can_be_selected_without_its_delivery_parent(registration, tmp_path, identity, preset):
    state, project = registration
    original = native_resources.template_details('repository-governance')['input']
    project['allowed_paths'] = original['allowed_paths']
    registrations.register(state, project, 0)
    installed = workflows.install_preset(state, preset)
    selected = next(item for item in installed['workflows'] if item['id'] == identity)
    root = workflows.get(state, identity, selected['version'])['definition']
    manifest = workflows.prepare_manifest(state.root, identity, root['version'],
        {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}, tmp_path / 'manifest')
    for protocol in ({}, {'review_protocol': 'dag-v1'}):
        definition = {'schema_version': 2, 'task_id': 'standalone-review', 'task_type': 'repository-governance',
            'issue_id': '1', 'input': original, 'composition': {'manifest': manifest['path'],
                'manifest_digest': manifest['digest'], 'review_instance': 'root', 'mode': 'task-mcp', **protocol}}
        definition['composition']['diversity'] = {
            'policy': 'prefer-distinct', 'reason': 'Use the pinned model in a separate review session.'}
        preview = tasks.preview(state, 'demo', definition, 1)
        selected = execution_input(preview['files']['task.spec.json'])
        selected.require_submission()


@pytest.mark.parametrize('domain', ['pretraining', 'posttraining'])
def test_domain_reviews_keep_general_identities_and_frozen_ancestor_material(tmp_path, domain):
    state = State(tmp_path / 'state')
    original = workflows.install_preset(state, 'repository-governance')
    general_ref = next(item for item in original['workflows'] if item['id'] == 'ergora-delivery-review')
    general = workflows.get(state, general_ref['id'], general_ref['version'])
    installed = workflows.install_preset(state, domain + '-review')
    assert workflows.install_preset(state, domain + '-review') == installed
    assert workflows.install_preset(state, 'repository-governance') == original
    assert workflows.get(state, general_ref['id'], general_ref['version']) == general
    definition = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    manifest = workflows.prepare_manifest(state.root, definition['id'], definition['version'],
        {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    dag = ReviewDAG(graph, 'root')
    assert {item['ref']['id'] for item in dag.members.values()} == {
        'ergora-structure-reviewer', 'ergora-correctness-reviewer', 'ergora-test-value-reviewer',
        'ergora-' + domain + '-reviewer'}
    assert all(leaf['review_requirement'] == 'required' for leaf in dag.members.values())
    assert all(not leaf['permissions']['write'] and not leaf['permissions']['shell']
               and not leaf['permissions']['network'] for leaf in dag.members.values())
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    assert workflows.inspect_manifest(Path(manifest['path']), material=True)['composition'] == graph
    nodes = {item['path']: item for item in graph['instances']}
    for path, leaf in dag.members.items():
        ancestors, current = set(), leaf
        while current is not None:
            ancestors.add(current['path'])
            current = nodes[current['parent']] if current['parent'] is not None else None
        assert {source['instance'] for resource in leaf['resources'] for source in resource['sources']} == ancestors
        prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), path,
            b'Review the complete supplied packet; scope is source and CPU arithmetic only.',
            tmp_path / path.replace('/', '-'), 100000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        assert all(resource['text'] in actual['prompt'] for resource in leaf['resources'])


@pytest.mark.skipif(sys.platform != 'linux', reason='Formal workspace calls require Linux/WSL2')
@pytest.mark.parametrize('kind', ['repository-governance', 'large-change'])
def test_development_preset_creates_original_unit_contract_without_starting(registration, tmp_path, kind):
    state, project = registration
    original = native_resources.template_details(kind)['input']
    project['allowed_paths'] = original['allowed_paths']
    registrations.register(state, project, 0)
    selected = workflows.install_preset(state, kind)
    root = workflows.get(state, selected['root']['id'], selected['root']['version'])['definition']
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'],
        {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    requested = {item['path']: item['backend_request'] for item in graph['instances'] if item['kind'] == 'agent'}
    assignments = {unit['id']: 'root/development/work/' + unit['id'] for unit in original['work_units']}
    definition = {'schema_version': 8, 'task_id': 'preset-task', 'task_type': kind, 'issue_id': '1', 'input': original,
        'composition': {'manifest': manifest['path'], 'manifest_digest': manifest['digest'],
            'review_protocol': 'dag-v1', 'review_instance': 'root/development/review', 'mode': 'task-mcp',
            'native': {'protocol': 'six-stage-v1', 'instance': 'root/development'},
            'preparation': {'protocol': 'preparation-dag-v1',
                            **{stage: {'instance': 'root/development/preparation/' + stage,
                                       'coordinator': 'root/development/preparation/' + stage + '/coordinator'}
                               for stage in ('inventory', 'plan')}, 'mode': 'task-mcp',
                            'repository_paths': original['allowed_paths']},
            'execution': {'protocol': 'work-units-v2', 'instance': 'root/development/work',
                          'mode': 'workspace-task-mcp', 'assignments': assignments},
            'backend_overrides': {path: {'binding': {**requested[path], 'sandbox': 'current-container'},
                                         'reason': 'Explicit trusted-container selection for this acceptance'}
                                  for path in assignments.values()},
            'diversity': {'policy': 'prefer-distinct', 'reason': 'Use the explicitly pinned model for independent review sessions.'}},
        'budget': {'wall_seconds': 120, 'cleanup_seconds': 5, 'model_invocations': 32}}
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    frozen = preview['files']['task.spec.json']
    assert frozen['schema_version'] == 12
    preparing = frozen['composition']['preparation']['members']
    assert preparing['root/development/preparation/plan/coordinator']['binding'] == {
        'tool': 'codex', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'max'}
    task_envelopes.unwrap(frozen)
    incomplete = deepcopy(definition)
    incomplete['schema_version'] = 2
    del incomplete['composition']['preparation']
    del incomplete['composition']['native']
    del incomplete['budget']
    with pytest.raises(ValueError, match='exactly all Agent leaves'):
        tasks.preview(state, 'demo', incomplete, 1)
    lowered = deepcopy(definition)
    # A work invocation retains the max minimum of its Agent's planner role.
    validation = next(path for path in assignments.values()
                      if next(item for item in graph['instances'] if item['path'] == path)['ref']['id']
                      in ('ergora-compatibility-validator', 'ergora-architecture-test-author'))
    lowered['composition']['backend_overrides'][validation] = {
        'binding': {'tool': 'codex', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'high'},
        'reason': 'Rejected lower request for a writer sharing the planner floor'}
    lowered['task_id'] = 'lowered-preset-task'
    rejected = tasks.prepare(state, 'demo', lowered, 1)
    assert rejected['status'] == 'failed'
    runtime = Path(project['execution']['state_directory'])
    failure = runtime / 'ergora/task-creations/lowered-preset-task.prepare-work/process/stderr.txt'
    assert 'at least max' in failure.read_text()
    assert frozen['legacy_spec']['request']['input'] == original
    assert set(frozen['composition']['diversity']['same_backend_members']) == set(frozen['composition']['members'])
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=prepared['prepare_sha256'])
    assert created['status'] == 'published' and created['execution_started_by_operation'] is False
    assert not (Path(project['execution']['state_directory']) / 'requests-composition-v12').exists()


def test_refactoring_preset_freezes_complete_parent_materials(tmp_path):
    state = State(tmp_path / 'state')
    installed = workflows.install_preset(state, 'refactoring')
    assert installed == workflows.install_preset(state, 'refactoring')
    assert installed['execution_authorized'] is False
    root = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    graph = workflows.preview(state.root, root['id'], root['version'], grant)
    instances = {item['path']: item for item in graph['instances']}
    leaves = [item for item in graph['instances'] if item['kind'] == 'agent']
    for leaf in leaves:
        ancestors = set()
        node = leaf
        while node is not None:
            ancestors.add(node['path'])
            node = instances[node['parent']] if node['parent'] is not None else None
        assert {source['instance'] for resource in leaf['resources'] for source in resource['sources']} == ancestors
        assert all(resource['text'] in leaf['prompt'] for resource in leaf['resources'])
    example = Path(__file__).parents[1] / 'examples/composition/refactoring/task.example.json'
    definition = json.loads(example.read_bytes())
    option = definition['composition']
    delivery = WorkDelivery(graph, option['execution'], option['review_instance'],
                            definition['input']['work_units'], preparation=option['preparation'])
    assert set(delivery.work.members) == set(option['execution']['assignments'].values())
    assert set(delivery.preparation) == {'inventory', 'plan'}
    assert set(delivery.review.members) == {
        'root/development/review/' + kind + '/review' for kind in ('structure', 'correctness', 'test-value')}
    assert all(not member['permissions']['write'] and not member['permissions']['shell']
               and not member['permissions']['network'] for member in delivery.review.members.values())
    assert all(member['review_requirement'] == 'required' for member in delivery.review.members.values())
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'], grant, tmp_path / 'manifest')
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    assert workflows.inspect_manifest(Path(manifest['path']), material=True)['composition'] == graph
    selected = 'root/development/review/structure/review'
    prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), selected,
        b'Review the exact refactoring candidate and its real caller migration evidence.', tmp_path / 'input', 100000)
    assert workflows.inspect_input(Path(prepared['path']))['digest'] == prepared['digest']


@pytest.mark.skipif(sys.platform != 'linux', reason='Budgeted native preparation requires Linux/WSL2')
def test_refactoring_preset_prepares_the_original_large_change_native_contract(registration, tmp_path):
    state, project = registration
    example = Path(__file__).parents[1] / 'examples/composition/refactoring/task.example.json'
    definition = json.loads(example.read_bytes())
    repo = Path(project['repo'])
    sources = {
        'src/example/normalizer.py': 'def normalize(value):\n    return value.strip().lower()\n',
        'src/example/client.py': 'from .normalizer import normalize\n\ndef request(value):\n    return normalize(value)\n',
        'tests/example/test_normalizer.py': 'from src.example.client import request\n\ndef test_request():\n    assert request(" A ") == "a"\n',
        'docs/refactoring/contract.md': 'Preserve normalize and its request caller; rollback restores this exact baseline.\n',
    }
    for name, text in sources.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    subprocess.run(['git', '-C', str(repo), 'add', '--', 'src', 'tests', 'docs'], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'commit.gpgsign=false', '-c', 'user.name=Fixture',
        '-c', 'user.email=fixture@example.test', 'commit', '-m', 'refactoring baseline'], check=True, capture_output=True)
    definition['starting_sha'] = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    definition['issue_id'] = '1'
    project['allowed_paths'] = definition['input']['allowed_paths']
    registrations.register(state, project, 0)
    installed = workflows.install_preset(state, 'refactoring')
    root = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'], grant, tmp_path / 'manifest')
    definition['composition'].update(manifest=manifest['path'], manifest_digest=manifest['digest'])
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    document = preview['files']['task.spec.json']
    selected = execution_input(document)
    selected.require_submission()
    assert document['schema_version'] == 12
    assert document['legacy_spec']['request']['task_type'] == 'large-change'
    assert document['legacy_spec']['request']['input'] == definition['input']
    assert selected.request_root(Path('requests')) == Path('requests-composition-v12')
    composition = document['composition']
    assert [item['instance'] for item in composition['native']['lineage']] == ['root', 'root/development']
    assert composition['native']['task_type'] == 'large-change'
    graph = task_envelopes.manifest_graph(composition['manifest'])
    assert {item['path'] for item in graph['instances'] if item['kind'] == 'agent'} == (
        composition['execution']['members'].keys() | composition['members'].keys()
        | composition['preparation']['members'].keys())
    assert composition['execution']['assignments'] == definition['composition']['execution']['assignments']
    assert set(composition['diversity']['same_backend_members']) == set(composition['members'])
    assert {member['binding']['tool'] for member in composition['members'].values()} == {'codex'}
    assert all(member['binding']['sandbox'] == 'current-container'
               for member in composition['execution']['members'].values())
    leaves = {item['path']: item for item in graph['instances'] if item['kind'] == 'agent'}
    for section, members in ((None, composition['members']), ('preparation', composition['preparation']['members']),
                             ('execution', composition['execution']['members'])):
        path = next(iter(members))
        leaf, member = leaves[path], members[path]
        lowered = {**member['binding'], 'reasoning_effort': 'low'}
        with pytest.raises(ValueError, match='at least'):
            tasks._member(leaf, member['mode'], {'binding': lowered, 'reason': 'Rejected lower selection'})
        changed = deepcopy(document)
        target = changed['composition'][section]['members'] if section else changed['composition']['members']
        target[path]['binding'] = lowered
        changed['sha256'] = task_envelopes.identity({key: value for key, value in changed.items() if key != 'sha256'})
        with pytest.raises(ValueError, match='at least'):
            task_envelopes.unwrap(changed)
    runtime = Path(project['execution']['state_directory'])
    assert not (runtime / 'tasks' / definition['task_id']).exists()
    assert not (runtime / 'requests-composition-v12').exists()


def test_cross_end_revision_freezes_real_experts_complete_ports_and_unchanged_default(tmp_path):
    example = Path(__file__).parents[1] / 'examples/composition/development-specialists'
    state = State(tmp_path / 'state')
    publish = runpy.run_path(str(example / 'publish.py'))['publish']
    published = publish(state, example, version='1.0.0')
    repeated = publish(state, example, version='1.0.0')
    assert published == repeated
    manifest = Path(published['manifest']['path'])
    graph = workflows.inspect_manifest(manifest, material=True)['composition']
    task = json.loads((example / 'task.example.json').read_bytes())
    option = task['composition']
    delivery = WorkDelivery(graph, option['execution'], option['review_instance'],
                            task['input']['work_units'], preparation=option['preparation'])
    installed = published['installation']
    references = {item['id']: item for item in installed['agents']}
    for stage, group in delivery.preparation.items():
        prefix = 'root/development/preparation/' + stage + '/'
        expected = {prefix + name: references[identity] for name, identity in (
            ('contract', 'ergora-api-contract-author'), ('server', 'ergora-server-implementer'),
            ('client', 'ergora-client-implementer'), ('validation', 'ergora-compatibility-validator'),
            ('coordinator', 'ergora-development-preparer'))}
        dag, coordinator = group['dag'], group['coordinator']
        assert {path: leaf['ref'] for path, leaf in dag.members.items()} == expected
        assert set(dag.predecessors[coordinator]) == set(dag.input_ports(coordinator)['sources']) == expected.keys() - {coordinator}
        assert dag.terminal_sources() == expected.keys()
        for name in ('server', 'client'):
            assert dag.input_ports(prefix + name)['sources'] == ([prefix + 'contract'] if stage == 'plan' else [])
    assert len(delivery.work.members) == 4 and len(delivery.review.members) == 3
    leaves = {item['path']: item for item in graph['instances'] if item['kind'] == 'agent'}
    assert len(leaves) == task['budget']['model_invocations'] == 17
    base = installed['root']
    base_definition = workflows.get(state, base['id'], base['version'])['definition']
    default = workflows.preview(state.root, base['id'], base['version'],
        {'schema_version': 1, 'permissions': base_definition['permissions'], 'limits': base_definition['limits']})
    assert len([item for item in default['instances'] if item['kind'] == 'agent']) == 13
    for name in ('preparation', 'delivery', 'root'):
        definition = published['publications'][name]['definition']
        actual = {node['id']: node.get('ref') for node in definition['nodes']}
        children = {'preparation': ('inventory', 'plan'), 'delivery': ('preparation',), 'root': ('delivery',)}[name]
        for child in children:
            assert published['references'][child] in actual.values()
    methods = {identity: agent_definitions.get(state, item['id'], item['version'], material=True)['resources']
               for identity, item in references.items()}
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    for path, leaf in leaves.items():
        prepared = workflows.prepare_input_from_manifest(manifest, path,
            b'Exact approved candidate, original task, complete producer results and original evidence.',
            tmp_path / path.replace('/', '-'), 100000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        assert all(resource['text'] in actual['prompt'] for resource in methods[leaf['ref']['id']])
        if leaf['role'] in ('inspector', 'planner'):
            assert not leaf['permissions']['write'] and not leaf['permissions']['shell'] and not leaf['permissions']['network']
            assert leaf['backend_request']['reasoning_effort'] == leaf['invocation_minimum']['reasoning_effort'] == 'max'
    invalid = deepcopy(graph)
    coordinator = delivery.preparation['plan']['coordinator']
    next(item for item in invalid['instances'] if item['path'] == coordinator)['inputs'] = {'task': {'input': 'task'}}
    with pytest.raises(ValueError, match='coordinator'):
        WorkDelivery(invalid, option['execution'], option['review_instance'],
                     task['input']['work_units'], preparation=option['preparation'])


@pytest.mark.skipif(sys.platform != 'linux', reason='Budgeted native preparation requires Linux/WSL2')
def test_cross_end_revision_prepares_exact_member_slots_on_the_original_native_owner(registration, tmp_path):
    state, project = registration
    example = Path(__file__).parents[1] / 'examples/composition/development-specialists'
    published = runpy.run_path(str(example / 'publish.py'))['publish'](state, example, version='1.0.0')
    definition = json.loads((example / 'task.example.json').read_bytes())
    definition['starting_sha'] = subprocess.check_output(['git', '-C', project['repo'], 'rev-parse', 'HEAD'], text=True).strip()
    definition['issue_id'] = '1'
    definition['composition'].update(manifest=published['manifest']['path'], manifest_digest=published['manifest']['digest'])
    project['allowed_paths'] = definition['input']['allowed_paths']
    registrations.register(state, project, 0)
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    document = preview['files']['task.spec.json']
    execution_input(document).require_submission()
    assert document['schema_version'] == 12 and len(document['budget']['slots']) == 17
    assert document['budget']['instance'] == prepared['budget']
    assert document['composition']['preparation']['protocol'] == 'preparation-dag-v1'
    graph = task_envelopes.manifest_graph(document['composition']['manifest'])
    assert {item['path'] for item in graph['instances'] if item['kind'] == 'agent'} == (
        document['composition']['preparation']['members'].keys()
        | document['composition']['execution']['members'].keys() | document['composition']['members'].keys())
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=prepared['prepare_sha256'])
    assert created['status'] == 'published' and created['execution_started_by_operation'] is False
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope'] == document
