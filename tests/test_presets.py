"""Shipped recipes use the existing immutable definitions and formal contracts."""

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import agent_definitions, reference, registrations, task_envelopes, tasks, workflow_definitions as workflows
from ergora.reference_inputs import execution_input
from ergora.review_dags import WorkDelivery
from ergora.state import State
from test_registrations import installation, registration


@pytest.mark.parametrize('direction', ['memory-tuning', 'activation-recompute', 'cpu-offloading',
    'cuda-graphs', 'sequence-packing', 'parallelism', 'megatron-fsdp', 'hierarchical-cp',
    'tp-dp-overlap', 'moe-dispatcher', 'moe-overlap', 'profiling', 'memory-snapshot', 'recipe-model', 'model-verification', 'cluster-resiliency', 'low-precision', 'kernel'])
def test_direction_roots_keep_full_context_when_reusing_v2_experts(tmp_path, direction):
    state = State(tmp_path / 'state')
    installed = workflows.install_preset(state, 'optimization-' + direction)
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
    context = next(resource for resource in materials if resource['kind'] == 'context')
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    for path, leaf in leaves.items():
        assert leaf['ref']['id'] == expected[path] and leaf['ref']['version'] == '2.0.0'
        assert not leaf['permissions']['write'] and not leaf['permissions']['shell'] and not leaf['permissions']['network']
        prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), path,
            b'Use supplied original experiment evidence; retain missing measurements.',
            tmp_path / path.replace('/', '-'), 100000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        assert context['text'] in actual['prompt']
        inherited = next(resource for resource in leaf['resources'] if resource['id'] == context['id'])
        assert inherited['text'] == context['text']
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
        delivery = WorkDelivery(before, execution, 'root/review', units)
        assert set(delivery.work.members) == set(execution['assignments'].values())
        assert {item['backend_request']['tool'] for item in leaves if item['role'] == 'reviewer'} == {'claude-code'}
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


@pytest.mark.parametrize('identity', ['ergora-structure-review', 'ergora-correctness-review', 'ergora-test-value-review'])
def test_bundled_review_can_be_selected_without_its_delivery_parent(registration, tmp_path, identity):
    state, project = registration
    original = reference.template_details('repository-governance')['input']
    project['allowed_paths'] = original['allowed_paths']
    registrations.register(state, project, 0)
    workflows.install_preset(state, 'repository-governance')
    root = workflows.get(state, identity, '1.0.0')['definition']
    manifest = workflows.prepare_manifest(state.root, identity, root['version'],
        {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}, tmp_path / 'manifest')
    for protocol in ({}, {'review_protocol': 'dag-v1'}):
        definition = {'schema_version': 2, 'task_id': 'standalone-review', 'task_type': 'repository-governance',
            'issue_id': '1', 'input': original, 'composition': {'manifest': manifest['path'],
                'manifest_digest': manifest['digest'], 'review_instance': 'root', 'mode': 'task-mcp', **protocol}}
        preview = tasks.preview(state, 'demo', definition, 1)
        selected = execution_input(preview['files']['task.spec.json'])
        selected.require_submission()


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
    assignments = {unit['id']: 'root/work/' + unit['id'] for unit in original['work_units']}
    definition = {'schema_version': 2, 'task_id': 'preset-task', 'task_type': kind, 'issue_id': '1', 'input': original,
        'composition': {'manifest': manifest['path'], 'manifest_digest': manifest['digest'],
            'review_protocol': 'dag-v1', 'review_instance': 'root/review', 'mode': 'task-mcp',
            'execution': {'protocol': 'work-units-v1', 'instance': 'root/work',
                          'mode': 'workspace-task-mcp', 'assignments': assignments},
            'backend_overrides': {path: {'binding': {'tool': 'codex', 'sandbox': 'current-container'},
                                         'reason': 'Explicit trusted-container selection for this acceptance'}
                                  for path in assignments.values()},
            'diversity': {'policy': 'require-distinct'}}}
    preview = tasks.preview(state, 'demo', definition, 1)
    frozen = preview['files']['task.spec.json']
    assert frozen['schema_version'] == 5
    assert frozen['legacy_spec']['request']['input'] == original
    assert frozen['composition']['diversity']['same_backend_members'] == []
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    assert created['status'] == 'published' and created['execution_started_by_operation'] is False
    assert not (Path(project['execution']['state_directory']) / 'requests-composition-v5').exists()


def test_refactoring_preset_restarts_with_old_versions_and_complete_parent_materials(tmp_path):
    state = State(tmp_path / 'state')
    original = workflows.install_preset(state, 'large-change')
    old_validator = agent_definitions.get(state, 'ergora-compatibility-validator', '1.0.0')
    installed = workflows.install_preset(state, 'refactoring')
    assert installed == workflows.install_preset(state, 'refactoring')
    assert workflows.install_preset(state, 'large-change') == original
    assert agent_definitions.get(state, 'ergora-compatibility-validator', '1.0.0') == old_validator
    validator = agent_definitions.get(state, 'ergora-compatibility-validator', '2.0.0')
    assert validator['digest'] != old_validator['digest']
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
    assert composition['diversity']['same_backend_members'] == []
    assert {member['binding']['tool'] for member in composition['members'].values()} == {'claude-code'}
    assert all(member['binding']['sandbox'] == 'current-container'
               for member in composition['execution']['members'].values())
    runtime = Path(project['execution']['state_directory'])
    assert not (runtime / 'tasks' / definition['task_id']).exists()
    assert not (runtime / 'requests-composition-v10').exists()


def test_training_v2_keeps_v1_and_prepares_four_readonly_experts_with_skill_references(tmp_path):
    state = State(tmp_path / 'state')
    old = workflows.install_preset(state, 'training-optimization')
    old_root = workflows.get(state, old['root']['id'], old['root']['version'])
    selected = workflows.install_preset(state, 'training-optimization-v2')
    assert selected == workflows.install_preset(state, 'training-optimization-v2')
    assert workflows.install_preset(state, 'training-optimization') == old
    assert workflows.get(state, old['root']['id'], old['root']['version']) == old_root
    assert selected['root']['id'] == old['root']['id']
    assert selected['root']['version'] == '2.0.0'
    root = workflows.get(state, selected['root']['id'], selected['root']['version'])['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'], grant, tmp_path / 'manifest')
    graph = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    instances = {item['path']: item for item in graph['instances']}
    leaves = {item['path']: item for item in graph['instances'] if item['kind'] == 'agent'}
    assert {path: leaf['role'] for path, leaf in leaves.items()} == {
        'root/analysis/design': 'experiment-planner', 'root/analysis/profile': 'performance-analyst',
        'root/kernel': 'kernel-tuner', 'root/measurement/review': 'reviewer'}
    assert all(leaf['ref']['version'] == '2.0.0' for leaf in leaves.values())
    assert all(not leaf['permissions']['write'] and not leaf['permissions']['shell']
               and not leaf['permissions']['network'] for leaf in leaves.values())
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    for path, leaf in leaves.items():
        ancestors = set()
        current = leaf
        while current is not None:
            ancestors.add(current['path'])
            current = instances[current['parent']] if current['parent'] is not None else None
        assert {source['instance'] for resource in leaf['resources'] for source in resource['sources']} == ancestors
        prepared = workflows.prepare_input_from_manifest(Path(manifest['path']), path,
            b'Analyze only supplied evidence; missing measurement remains unverified.',
            tmp_path / path.replace('/', '-'), 100000)
        actual = workflows.inspect_input(Path(prepared['path']), material=True)
        assert all(resource['text'] in actual['prompt'] for resource in leaf['resources'])
        reference = Path(prepared['path']) / 'assets/agent-definitions/objects' / leaf['ref']['digest']
        source = Path(__file__).parents[1] / 'src/ergora/data/presets/agents' / (leaf['ref']['id'] + '-v2')
        relative = 'skills/' + leaf['ref']['id'] + '/references/evidence-contract.md'
        assert (reference / relative).read_bytes() == (source / relative).read_bytes()
