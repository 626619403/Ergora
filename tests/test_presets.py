"""Shipped recipes use the existing immutable definitions and formal contracts."""

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import reference, registrations, tasks, workflow_definitions as workflows
from ergora.reference_inputs import execution_input
from ergora.review_dags import WorkDelivery
from ergora.state import State
from test_registrations import installation, registration


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
    assert {item['id'] for item in json.loads(listed.stdout)} == set(reference.TEMPLATES)
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
