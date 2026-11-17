"""Shipped recipes use the existing immutable definitions and formal contracts."""

import json
from copy import deepcopy
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import agent_definitions, reference, registrations, task_envelopes, tasks, workflow_definitions as workflows
from ergora.reference_inputs import execution_input
from ergora.review_dags import ReviewDAG, WorkDelivery
from ergora.state import State
from test_registrations import installation, registration


@pytest.mark.parametrize('direction', ['memory-tuning', 'activation-recompute', 'cpu-offloading',
    'cuda-graphs', 'sequence-packing', 'parallelism', 'megatron-fsdp', 'hierarchical-cp',
    'tp-dp-overlap', 'moe-dispatcher', 'moe-overlap', 'profiling', 'memory-snapshot', 'recipe-model', 'model-verification', 'cluster-resiliency', 'low-precision', 'kernel', 'performance-diagnosis'])
def test_direction_roots_keep_full_context_when_reusing_v2_experts(tmp_path, direction):
    state = State(tmp_path / 'state')
    installed = workflows.install_preset(state, 'optimization-' + direction)
    specialists = {item['id']: item for item in installed['agents']}
    assert installed == workflows.install_preset(state, 'optimization-' + direction)
    root = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'], grant, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    expected = {'root/analysis/design': 'ergora-experiment-designer',
                'root/analysis/profile': 'ergora-performance-analyst',
                'root/measurement/review': 'ergora-measurement-reviewer'}
    if direction in ('low-precision', 'kernel'):
        expected['root/kernel'] = 'ergora-kernel-designer'
    leaves = {item['path']: item for item in graph['instances'] if item['kind'] == 'agent'}
    assert set(leaves) == set(expected)
    materials = workflows.get(state, root['id'], root['version'], material=True)['resources']
    parent_materials = [resource for resource in materials if resource['kind'] in ('context', 'skill')]
    assert parent_materials
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    for path, leaf in leaves.items():
        assert leaf['ref'] == specialists[expected[path]]
        assert not leaf['permissions']['write'] and not leaf['permissions']['shell'] and not leaf['permissions']['network']
        prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), path,
            b'Use supplied original experiment evidence; retain missing measurements.',
            tmp_path / path.replace('/', '-'), 100000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        for material in parent_materials:
            assert material['text'] in actual['prompt']
            inherited = next(resource for resource in leaf['resources'] if resource['id'] == material['id'])
            assert inherited['text'] == material['text']
            assert {source['instance'] for source in inherited['sources']} == {'root'}


@pytest.mark.parametrize('kind', reference.TEMPLATES)
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
    for item in leaves:
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
        units = reference.template_details(kind)['input']['work_units']
        execution = {'protocol': 'work-units-v1', 'instance': 'root/work', 'mode': 'workspace-task-mcp',
                     'assignments': {unit['id']: 'root/work/' + unit['id'] for unit in units}}
        preparation = {'protocol': 'preparation-v1', 'inventory': 'root/preparation/inventory',
            'plan': 'root/preparation/plan', 'mode': 'task-mcp',
            'repository_paths': reference.template_details(kind)['input']['allowed_paths']}
        delivery = WorkDelivery(before, execution, 'root/review', units, preparation=preparation)
        assert set(delivery.work.members) == set(execution['assignments'].values())
        assert {item['backend_request']['tool'] for item in leaves if item['role'] == 'reviewer'} == {'codex'}
        assert {item['backend_request']['tool'] for item in leaves if item['role'] == 'implementer'} == {'codex'}
        selected = 'root/review/structure/review'
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
    original = reference.template_details('repository-governance')['input']
    project['allowed_paths'] = original['allowed_paths']
    registrations.register(state, project, 0)
    installed = workflows.install_preset(state, preset)
    root = workflows.get(state, identity, installed['root']['version'])['definition']
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
    original = reference.template_details(kind)['input']
    project['allowed_paths'] = original['allowed_paths']
    registrations.register(state, project, 0)
    selected = workflows.install_preset(state, kind)
    root = workflows.get(state, selected['root']['id'], selected['root']['version'])['definition']
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'],
        {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    requested = {item['path']: item['backend_request'] for item in graph['instances'] if item['kind'] == 'agent'}
    assignments = {unit['id']: 'root/work/' + unit['id'] for unit in original['work_units']}
    definition = {'schema_version': 4, 'task_id': 'preset-task', 'task_type': kind, 'issue_id': '1', 'input': original,
        'composition': {'manifest': manifest['path'], 'manifest_digest': manifest['digest'],
            'review_protocol': 'dag-v1', 'review_instance': 'root/review', 'mode': 'task-mcp',
            'preparation': {'protocol': 'preparation-v1', 'inventory': 'root/preparation/inventory',
                            'plan': 'root/preparation/plan', 'mode': 'task-mcp',
                            'repository_paths': original['allowed_paths']},
            'execution': {'protocol': 'work-units-v2', 'instance': 'root/work',
                          'mode': 'workspace-task-mcp', 'assignments': assignments},
            'backend_overrides': {path: {'binding': {**requested[path], 'sandbox': 'current-container'},
                                         'reason': 'Explicit trusted-container selection for this acceptance'}
                                  for path in assignments.values()},
            'diversity': {'policy': 'prefer-distinct', 'reason': 'Use the explicitly pinned model for independent review sessions.'}}}
    preview = tasks.preview(state, 'demo', definition, 1)
    frozen = preview['files']['task.spec.json']
    assert frozen['schema_version'] == 8
    preparing = frozen['composition']['preparation']['members']
    assert preparing['root/preparation/plan']['binding'] == {
        'tool': 'codex', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'max'}
    task_envelopes.unwrap(frozen)
    incomplete = deepcopy(definition)
    incomplete['schema_version'] = 2
    del incomplete['composition']['preparation']
    with pytest.raises(ValueError, match='exactly all Agent leaves'):
        tasks.preview(state, 'demo', incomplete, 1)
    lowered = deepcopy(definition)
    lowered['composition']['backend_overrides']['root/preparation/plan'] = {
        'binding': {'tool': 'codex', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'high'},
        'reason': 'Rejected lower planner request'}
    with pytest.raises(ValueError, match='at least max'):
        tasks.preview(state, 'demo', lowered, 1)
    assert frozen['legacy_spec']['request']['input'] == original
    assert set(frozen['composition']['diversity']['same_backend_members']) == set(frozen['composition']['members'])
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    assert created['status'] == 'published' and created['execution_started_by_operation'] is False
    assert not (Path(project['execution']['state_directory']) / 'requests-composition-v8').exists()


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
    assert document['schema_version'] == 10
    assert document['legacy_spec']['request']['task_type'] == 'large-change'
    assert document['legacy_spec']['request']['input'] == definition['input']
    assert selected.request_root(Path('requests')) == Path('requests-composition-v10')
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
    assert not (runtime / 'requests-composition-v10').exists()
