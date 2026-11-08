"""Formal creation seals complete compositions without silently running legacy work."""

import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import agent_definitions, contracts, projects, reference, task_envelopes, tasks, workflow_definitions as workflows
from test_registrations import installation, registration
from test_task_creation import creation_project, _inject, _files
from test_workflow_definitions import EXAMPLES, child, definition, grant, leaf, ref, write_bundle


@pytest.fixture
def composed_creation(creation_project, tmp_path):
    state, registration, task = creation_project
    agent = agent_definitions.import_bundle(state, EXAMPLES / 'agents/architecture-reviewer')
    source = write_bundle(tmp_path / 'review-source', definition('formal-review', [leaf('review', ref(agent, 'agent'))]),
                          'Required parent instructions. 所有祖先材料。\n')
    workflows.import_bundle(state, source)
    manifest = tmp_path / 'manifest'
    saved = workflows.prepare_manifest(state.root, 'formal-review', '1.0.0', grant(), manifest)
    task.update(schema_version=2, composition={'manifest': str(manifest), 'manifest_digest': saved['digest'],
        'review_instance': 'root', 'mode': 'text-only', 'backend_overrides': {
            'root/review': {'binding': {'tool': 'claude-code'}, 'reason': 'Use a different review backend'}}})
    return state, registration, task


def test_preview_and_creation_freeze_a_new_envelope_with_the_unchanged_legacy_projection(composed_creation):
    state, registration, task = composed_creation
    contracts.StrictValidator.check_schema(tasks._DEFINITIONS[2])
    before = state.project('demo')
    preview = tasks.preview(state, 'demo', task, 1)
    assert preview == tasks.preview(state, 'demo', task, 1) and state.project('demo') == before
    root = Path(registration['execution']['state_directory'])
    assert not root.exists()
    envelope = preview['files']['task.spec.json']
    spec, composition = task_envelopes.unwrap(envelope)
    assert preview['schema_version'] == 2 and spec == preview['files']['compiled.json']['spec']
    assert composition['manifest']['digest'] == task['composition']['manifest_digest']
    assert composition['members']['root/review']['binding'] == {'tool': 'claude-code'}
    assert composition['diversity']['same_backend_members'] == []
    graph = json.loads(base64.b64decode(composition['manifest']['files']['composition.json']['content_base64']))
    assert 'Required parent instructions.' in graph['instances'][-1]['prompt']
    native = Path(reference.ROOT) / 'platform/upstream/platform'
    environment = dict(os.environ, PYTHONPATH=str(native))
    rejected = subprocess.run([sys.executable, '-S', '-c',
        'import json,sys;from dev_platform.contracts import validate_spec;validate_spec(json.load(sys.stdin))'],
        input=json.dumps(envelope), capture_output=True, text=True, env=environment, timeout=20)
    assert rejected.returncode != 0 and 'execution spec' in rejected.stderr

    created = tasks.create(state, 'demo', task, 1, preview['preview_sha256'])
    assert created['status'] == 'published' and created['intent_sha256'] == preview['preview_sha256']
    assert created['composition']['envelope_sha256'] == envelope['sha256']
    assert created['composition']['runtime_supported'] is False
    shown = tasks.show(state, 'demo', task['task_id'])
    assert shown['spec'] == spec and shown['admission_envelope'] == envelope
    assert tasks.listing(state, 'demo')['items'][0]['composition'] == created['composition']
    original = _files(root)
    shutil.rmtree(Path(task['composition']['manifest']))
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    assert tasks.resume_create(state, 'demo', task['task_id'], 1, created['intent_sha256']) == created
    assert tasks.creation(state, 'demo', task['task_id']) == created and _files(root) == original
    with pytest.raises(ValueError, match='versioned runtime bridge'):
        tasks.status(state, 'demo', task['task_id'])


@pytest.mark.parametrize('loss', ['agent-bindings.json', 'task.spec.json'])
def test_interrupted_composition_creation_resumes_original_bytes_after_sources_and_bindings_change(composed_creation, monkeypatch, loss):
    state, registration, task = composed_creation
    preview = tasks.preview(state, 'demo', task, 1)
    _inject(monkeypatch, f'''
original_init = _Creation.__init__
def initialize(self, *args):
    original_init(self, *args)
    write = self.core.write
    def interrupted(path, value, **kwargs):
        if path == self.target / {loss!r}:
            raise OSError('composition publication loss')
        return write(path, value, **kwargs)
    self.core.write = interrupted
_Creation.__init__ = initialize
''')
    with pytest.raises(ValueError, match='publication loss'):
        tasks.create(state, 'demo', task, 1, preview['preview_sha256'])
    monkeypatch.undo()
    pending = tasks.creation(state, 'demo', task['task_id'])
    assert pending['status'] == 'pending' and pending['intent_sha256'] == preview['preview_sha256']
    shutil.rmtree(Path(task['composition']['manifest']))
    projects.bind(state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'changed-model'}, 1)
    _inject(monkeypatch, "def forbidden(self, *args):\n    raise AssertionError('recovery cannot recompile')\n_Creation.compile = forbidden")
    result = tasks.resume_create(state, 'demo', task['task_id'], 2, pending['intent_sha256'])
    assert result['status'] == 'published' and result['created_revision'] == 1
    raw = json.loads((Path(registration['execution']['state_directory']) / 'tasks/new-task/task.spec.json').read_bytes())
    assert raw == preview['files']['task.spec.json']
    assert result['composition']['members']['root/review']['binding'] == {'tool': 'claude-code'}


@pytest.mark.parametrize('policy', ['prefer-distinct', 'require-distinct', 'allow-same'])
def test_each_review_backend_is_explicit_and_same_backend_policy_is_enforced(composed_creation, policy):
    state, registration, task = composed_creation
    option = task['composition']
    option['backend_overrides'] = {'root/review': {'binding': {'tool': 'codex'}, 'reason': 'Claude unavailable; authorized Codex fallback'}}
    option['diversity'] = {'policy': policy}
    if policy != 'allow-same':
        with pytest.raises(ValueError, match='different from|explicit diversity reason'):
            tasks.preview(state, 'demo', task, 1)
        assert not Path(registration['execution']['state_directory']).exists()
        if policy == 'require-distinct':
            return
        option['diversity']['reason'] = 'Claude unavailable; operator accepts the shared backend'
    preview = tasks.preview(state, 'demo', task, 1)
    composition = preview['files']['task.spec.json']['composition']
    assert composition['members']['root/review']['binding'] == {'tool': 'codex'}
    assert composition['diversity']['same_backend_members'] == ['root/review']
    assert composition['diversity']['implementer_backend'] == 'codex'


@pytest.mark.parametrize('case', ['digest', 'instance', 'member', 'backend', 'role', 'mode'])
def test_bad_static_or_backend_selections_do_not_publish_native_files(composed_creation, case):
    state, registration, task = composed_creation
    if case == 'digest':
        task['composition']['manifest_digest'] = '0' * 64
    elif case == 'instance':
        task['composition']['review_instance'] = 'root/review'
    elif case == 'member':
        task['composition']['backend_overrides'] = {'root/missing': {'binding': {'tool': 'codex'}, 'reason': 'explicit'}}
    elif case == 'backend':
        task['composition']['backend_overrides'] = {'root/review': {'binding': {'tool': 'command', 'command': ['echo']}, 'reason': 'explicit'}}
    elif case == 'mode':
        task['composition']['mode'] = 'native'
    else:
        agent = agent_definitions.import_bundle(state, EXAMPLES / 'agents/kernel-implementer')
        node = leaf('implement', ref(agent, 'agent')); node['role'] = 'implementer'
        source = write_bundle(state.root / 'mixed-source', definition('mixed-review', [node]))
        workflows.import_bundle(state, source)
        saved = workflows.prepare_manifest(state.root, 'mixed-review', '1.0.0', grant(), state.root / 'mixed-manifest')
        task['composition'].update(manifest=saved['path'], manifest_digest=saved['digest'])
    with pytest.raises(ValueError):
        tasks.preview(state, 'demo', task, 1)
    assert not Path(registration['execution']['state_directory']).exists()


def test_changed_envelope_or_embedded_bytes_cannot_be_read_as_the_original_task(composed_creation):
    state, registration, task = composed_creation
    preview = tasks.preview(state, 'demo', task, 1)
    tasks.create(state, 'demo', task, 1, preview['preview_sha256'])
    path = Path(registration['execution']['state_directory']) / 'tasks/new-task/task.spec.json'
    envelope = json.loads(path.read_bytes())
    envelope['composition']['members']['root/review']['binding'] = {'tool': 'codex'}
    path.write_text(json.dumps(envelope), encoding='utf-8')
    with pytest.raises(ValueError, match='envelope digest mismatch'):
        tasks.show(state, 'demo', task['task_id'])
    assert tasks.creation(state, 'demo', task['task_id'])['status'] == 'conflict'
    envelope = deepcopy(preview['files']['task.spec.json'])
    envelope['composition']['manifest']['files']['composition.json']['content_base64'] = base64.b64encode(b'{}').decode()
    envelope['sha256'] = task_envelopes.identity({k: v for k, v in envelope.items() if k != 'sha256'})
    path.write_text(json.dumps(envelope), encoding='utf-8')
    with pytest.raises(ValueError, match='original digest'):
        tasks.show(state, 'demo', task['task_id'])


@pytest.mark.skipif(sys.platform != 'linux', reason='Native formal submission is Linux-only')
def test_composition_submission_is_rejected_before_any_legacy_remote_or_dispatch_intent(composed_creation):
    state, registration, task = composed_creation
    preview = tasks.preview(state, 'demo', task, 1)
    created = tasks.create(state, 'demo', task, 1, preview['preview_sha256'])
    root = Path(registration['execution']['state_directory'])
    runtime = Path(registration['execution']['installation']) / '.venv/bin/python'
    runtime.parent.mkdir(parents=True)
    runtime.symlink_to(sys.executable)
    with pytest.raises(ValueError, match='versioned runtime bridge'):
        tasks.start(state, 'demo', task['task_id'], 1, created['intent_sha256'])
    assert not (root / 'ergora/task-submissions').exists()
    assert not (root / 'requests').exists() and not (root / 'receipts').exists()


def test_an_unexecuted_parent_output_cannot_be_invented_by_selecting_a_review_subtree(composed_creation):
    state, registration, task = composed_creation
    agent = agent_definitions.library(state.root).get('architecture-reviewer', '1.0.0')
    nested = child('after', ref(workflows.get(state, 'formal-review', '1.0.0'), 'workflow'))
    nested.update(depends_on=['before'], inputs={'task': {'node': 'before', 'output': 'result'}})
    source = write_bundle(state.root / 'outer-source', definition('outer', [leaf('before', ref(agent, 'agent')), nested]))
    workflows.import_bundle(state, source)
    saved = workflows.prepare_manifest(state.root, 'outer', '1.0.0', grant(), state.root / 'outer-manifest')
    task['composition'].update(manifest=saved['path'], manifest_digest=saved['digest'], review_instance='root/after',
                               backend_overrides={})
    with pytest.raises(ValueError, match='unexecuted external node'):
        tasks.preview(state, 'demo', task, 1)
    assert not Path(registration['execution']['state_directory']).exists()


def test_complete_manifest_bytes_over_the_formal_contract_limit_are_rejected_without_truncation(composed_creation):
    state, registration, task = composed_creation
    agent = agent_definitions.library(state.root).get('architecture-reviewer', '1.0.0')
    document = definition('large-review', [leaf('review', ref(agent, 'agent'))])
    document['limits']['material_bytes'] = 1_000_000
    source = write_bundle(state.root / 'large-source', document, 'Complete required instructions.\n' + 'x' * 600_000)
    workflows.import_bundle(state, source)
    saved = workflows.prepare_manifest(state.root, 'large-review', '1.0.0', grant(material_bytes=1_000_000), state.root / 'large-manifest')
    task['composition'].update(manifest=saved['path'], manifest_digest=saved['digest'])
    with pytest.raises(ValueError, match='task.spec.json exceeds its creation read limit'):
        tasks.preview(state, 'demo', task, 1)
    assert workflows.inspect_manifest(Path(saved['path']))['digest'] == saved['digest']
    assert not Path(registration['execution']['state_directory']).exists()


@pytest.mark.parametrize('origin', ['node', 'ordering', 'root-other', 'root-task'])
def test_review_grandchild_resolves_renamed_input_and_every_ancestor_dependency(composed_creation, origin):
    state, registration, task = composed_creation
    agent = agent_definitions.library(state.root).get('architecture-reviewer', '1.0.0')
    inner = child('inner', ref(workflows.get(state, 'formal-review', '1.0.0'), 'workflow'))
    inner['inputs']['task'] = {'input': 'incoming'}
    middle = definition('middle', [inner]); middle['inputs'] = ['incoming']
    saved_middle = workflows.import_bundle(state, write_bundle(state.root / 'middle-source', middle))
    after = child('after', ref(saved_middle, 'workflow'))
    after['inputs'] = {'incoming': {'node': 'before', 'output': 'result'} if origin == 'node' else
                      {'input': 'notes' if origin == 'root-other' else 'task'}}
    after['depends_on'] = ['before'] if origin in ('node', 'ordering') else []
    outer = definition('outer-deep', [leaf('before', ref(agent, 'agent')), after])
    outer['inputs'] = ['task', 'notes']
    workflows.import_bundle(state, write_bundle(state.root / 'deep-source', outer))
    saved = workflows.prepare_manifest(state.root, 'outer-deep', '1.0.0', grant(), state.root / 'deep-manifest')
    task['composition'].update(manifest=saved['path'], manifest_digest=saved['digest'],
        review_instance='root/after/inner', backend_overrides={}, diversity={'policy': 'allow-same'})
    if origin == 'root-task':
        assert tasks.preview(state, 'demo', task, 1)['files']['task.spec.json']['composition']['review_instance'] == 'root/after/inner'
    else:
        with pytest.raises(ValueError, match='unexecuted external node|root task input'):
            tasks.preview(state, 'demo', task, 1)
    assert not Path(registration['execution']['state_directory']).exists()


@pytest.mark.parametrize('case', ['null-member', 'mode', 'binding', 'binding-fields', 'policy', 'policy-grant', 'policy-bool', 'policy-fields', 'sandbox-fields',
                                'requested-binding', 'diversity-policy', 'diversity-members'])
def test_reader_rejects_malformed_saved_member_values_even_with_a_recomputed_outer_digest(composed_creation, case):
    state, registration, task = composed_creation
    preview = tasks.preview(state, 'demo', task, 1)
    tasks.create(state, 'demo', task, 1, preview['preview_sha256'])
    envelope = preview['files']['task.spec.json']
    composition = envelope['composition']; member = composition['members']['root/review']
    if case == 'null-member':
        composition['members']['root/review'] = None
    elif case == 'mode':
        member['mode'] = 'native'
    elif case == 'binding':
        member['binding'] = {'tool': 3}
    elif case == 'binding-fields':
        member['binding'] = {'tool': 'command', 'command': ['echo']}
    elif case == 'policy':
        member['policy']['mode'] = 'task-mcp'
    elif case == 'policy-grant':
        member['policy']['capabilities']['write'] = {'status': 'enforced', 'effective': ['workspace']}
    elif case == 'policy-bool':
        member['policy']['capabilities']['shell']['effective'] = 0
    elif case == 'policy-fields':
        member['policy']['command'] = ['sh']
    elif case == 'sandbox-fields':
        member['policy']['capabilities']['backend_sandbox'] = {'status': 'enforced', 'command': ['sh']}
    elif case == 'requested-binding':
        member['requested_binding'] = {'tool': 'another-historical-tool'}
    elif case == 'diversity-policy':
        composition['diversity']['policy'] = 'unchecked'
    else:
        composition['diversity']['implementer_backend'] = 'claude-code'
    envelope['sha256'] = task_envelopes.identity({k: v for k, v in envelope.items() if k != 'sha256'})
    path = Path(registration['execution']['state_directory']) / 'tasks/new-task/task.spec.json'
    path.write_text(json.dumps(envelope), encoding='utf-8')
    with pytest.raises(ValueError, match='composition'):
        tasks.show(state, 'demo', task['task_id'])


@pytest.mark.parametrize('choice', ['mode', 'binding', 'backend-reason', 'diversity'])
def test_recovery_rejects_a_saved_definition_that_contradicts_its_frozen_member_choices(composed_creation, monkeypatch, choice):
    state, registration, task = composed_creation
    preview = tasks.preview(state, 'demo', task, 1)
    _inject(monkeypatch, "def interrupted(self, record, **kwargs):\n    self.core.write(self.intent_path, record)\n    raise OSError('pending composition')\n_Creation.publish = interrupted")
    with pytest.raises(ValueError, match='pending composition'):
        tasks.create(state, 'demo', task, 1, preview['preview_sha256'])
    monkeypatch.undo()
    root = Path(registration['execution']['state_directory'])
    intent = root / 'ergora/task-creations/new-task.intent.json'
    record = json.loads(intent.read_bytes()); option = record['definition']['composition']
    if choice == 'mode':
        option['mode'] = 'task-mcp'
    elif choice == 'binding':
        option['backend_overrides']['root/review']['binding']['model'] = 'different-model'
    elif choice == 'backend-reason':
        option['backend_overrides']['root/review']['reason'] = 'Different saved explanation'
    else:
        option['diversity'] = {'policy': 'allow-same'}
    intent.write_text(json.dumps(record), encoding='utf-8')
    before = _files(root)
    with pytest.raises(ValueError, match='composition'):
        tasks.resume_create(state, 'demo', task['task_id'], 1, task_envelopes.identity(record))
    assert _files(root) == before and not (root / 'tasks').exists()


def test_recovery_checks_individual_contract_capacity_before_any_native_publication(composed_creation, monkeypatch):
    state, registration, task = composed_creation
    preview = tasks.preview(state, 'demo', task, 1)
    _inject(monkeypatch, "def interrupted(self, record, **kwargs):\n    self.core.write(self.intent_path, record)\n    raise OSError('pending composition')\n_Creation.publish = interrupted")
    with pytest.raises(ValueError, match='pending composition'):
        tasks.create(state, 'demo', task, 1, preview['preview_sha256'])
    monkeypatch.undo()
    root = Path(registration['execution']['state_directory'])
    intent = root / 'ergora/task-creations/new-task.intent.json'
    record = json.loads(intent.read_bytes())
    reason = 'x' * 1_048_576
    record['definition']['composition']['backend_overrides']['root/review']['reason'] = reason
    envelope = record['files']['task.spec.json']
    envelope['composition']['members']['root/review']['backend_reason'] = reason
    envelope['sha256'] = task_envelopes.identity({k: v for k, v in envelope.items() if k != 'sha256'})
    intent.write_text(json.dumps(record), encoding='utf-8')
    before = _files(root)
    with pytest.raises(ValueError, match='task.spec.json exceeds its creation read limit'):
        tasks.resume_create(state, 'demo', task['task_id'], 1, task_envelopes.identity(record))
    assert _files(root) == before and not (root / 'tasks').exists()
