"""Original preparation owns one authorization, complete bytes and stop evidence."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

import ergora.native.resources as native_resources
import ergora.definitions.agents as agent_definitions
import ergora.issues.application as issues
import ergora.improvement.memory as memory
import ergora.configuration.projects as projects
import ergora.configuration.registrations as registrations
import ergora.definitions.skills as skill_assets
import ergora.development.application as tasks
import ergora.definitions.workflows as workflow_definitions
from ergora.development import envelopes as task_envelopes
from ergora.development.inputs import execution_input, request_roots
from ergora.storage.state import State
from test_full_stage_materials import full_creation, full_graph
from test_work_agents import work_creation, work_graph
from test_registrations import design_policy, installation, registration
from test_task_creation import creation_project, _files
from test_project_issues import bind, native, source
from test_workflow_definitions import EXAMPLES, child, definition as workflow_document, leaf, ref, write_bundle
from ergora._paths import IMPORT_ROOT


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Budgeted native preparation requires Linux/WSL2')


@pytest.fixture
def budget_graph(work_graph, tmp_path):
    library, grant, _, execution, units = work_graph
    preparer = agent_definitions.get(library, 'development-preparer', '1.0.0')
    groups = {}
    for stage, role in (('inventory', 'inspector'), ('plan', 'planner')):
        nodes = [{**leaf('expert', ref(preparer, 'agent')), 'role': role},
            {**leaf('coordinator', ref(preparer, 'agent')), 'role': role, 'depends_on': ['expert'],
             'inputs': {'task': {'node': 'expert', 'output': 'result'}}},
            {'id': 'done', 'join': 'all', 'depends_on': ['coordinator']}]
        doc = workflow_document('budget-' + stage, nodes)
        groups[stage] = workflow_definitions.import_bundle(library, write_bundle(tmp_path / stage, doc))
    saved = {}
    for name in ('preparation-guide', 'prepared-delivery', 'native-development'):
        target = tmp_path / name
        shutil.copytree(EXAMPLES / 'composition' / name, target)
        doc = json.loads((target / 'workflow.json').read_bytes())
        doc['version'] = '1.1.0'
        if name == 'preparation-guide':
            doc['nodes'] = [child(stage, ref(group, 'workflow')) for stage, group in groups.items()]
        else:
            doc['nodes'][0]['ref'] = ref(saved['preparation-guide' if name == 'prepared-delivery' else 'prepared-delivery'], 'workflow')
        (target / 'workflow.json').write_text(json.dumps(doc))
        saved[name] = workflow_definitions.import_bundle(library, target)
    position = 'root/development'
    def nested(path):
        return position + '/' + path.removeprefix('root/')
    execution = {**execution, 'protocol': 'work-units-v2', 'instance': nested(execution['instance']),
                 'assignments': {key: nested(path) for key, path in execution['assignments'].items()}}
    preparation = {'protocol': 'preparation-dag-v1', 'mode': 'task-mcp', 'repository_paths': ['src'],
        **{stage: {'instance': position + '/preparation/' + stage,
                   'coordinator': position + '/preparation/' + stage + '/coordinator'} for stage in groups}}
    return library, grant, saved['native-development'], execution, units, preparation


@pytest.fixture
def budget_creation(work_creation, budget_graph, tmp_path):
    state, registered, definition = work_creation
    library, grant, parent, execution, _, preparation = budget_graph
    manifest = workflow_definitions.prepare_manifest(library.root, parent['definition']['id'], parent['definition']['version'],
                                                      grant, tmp_path / 'budget-manifest')
    option = definition['composition']
    option.update(manifest=manifest['path'], manifest_digest=manifest['digest'], execution=execution,
                  preparation=preparation, review_instance='root/development/review',
                  native={'protocol': 'six-stage-v1', 'instance': 'root/development'})
    option['backend_overrides'] = {'root/development/' + path.removeprefix('root/'): value
                                   for path, value in option['backend_overrides'].items()}
    definition.update(schema_version=8, budget={'wall_seconds': 120, 'cleanup_seconds': 5, 'model_invocations': 258})
    return state, registered, definition


def _select_context(state, definition, directory):
    record = memory.save(state, 'demo', 'Original selected source. 完整原文。', {'uri': 'repo://design', 'revision': '1'})
    source = directory / 'selected-guide'
    (source / 'references').mkdir(parents=True)
    (source / 'SKILL.md').write_text('---\nname: selected-guide\ndescription: Frozen source contract\n---\nRead references/contract.md.\n')
    (source / 'references/contract.md').write_bytes(b'Original selected attachment.\r\n')
    imported = skill_assets.import_bundle(state, 'demo', source)
    head = next(item for item in skill_assets.versions(state, 'demo')['active'] if item['name'] == imported['name'])
    definition['context'] = {'root_version': '1.1.1',
        'memories': [{'id': record['id'], 'revision': record['revision']}],
        'skills': [{key: head[key] for key in ('name', 'digest', 'revision')}]}
    definition['composition']['mode'] = 'task-mcp'


def test_linked_preparation_refuses_a_self_link_before_launch(budget_creation):
    from ergora.development.runtime.creation_process import task_preparation

    state, registered, definition = budget_creation
    linked = {**definition, 'amendment': {'project': 'demo', 'project_revision': 1,
        'change': 'Changed acceptance criteria', 'definition_sha256': task_envelopes.identity(definition),
        'predecessor': {'task_id': definition['task_id']}}}
    with pytest.raises(ValueError, match='distinct original and successor task IDs'):
        task_preparation(state.project('demo'), state.root, 'prepare', {'definition': linked})
    assert not (state.root / 'operations/task-preparations').exists()
    assert not (Path(registered['execution']['state_directory']) / 'ergora/task-creations').exists()


@pytest.mark.parametrize('with_context', [False, True])
@pytest.mark.parametrize('with_source', [False, True])
def test_current_public_creation_preserves_one_frame_for_source_context_combinations(
        budget_creation, request, tmp_path, with_context, with_source):
    state, registered, definition = budget_creation
    if with_source:
        service = request.getfixturevalue('source')
        state = State(tmp_path / 'source-task-control')
        registered = {**registered, 'tracker': {'kind': 'github', 'project': 'team/repo'},
            'execution': {**registered['execution'], 'config_directory': str(tmp_path / 'source-task-config'),
                          'state_directory': str(tmp_path / 'source-task-runtime')}}
        registrations.register(state, registered, 0)
        service.state = state
        bind(service, 'github')
        service.raw = json.dumps(native('github', 'Original issue. 完整正文。')).encode()
        saved = issues.capture(state, 'demo', '7', state.project('demo')['revision'])['snapshot']
        definition['issue_id'] = '7'
        definition['source'] = {'snapshot_sha256': saved['sha256']}
    if with_context:
        _select_context(state, definition, tmp_path)
    revision = state.project('demo')['revision']
    prepared = tasks.prepare(state, 'demo', definition, revision)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, revision)
    document = preview['files']['task.spec.json']
    spec, composition = task_envelopes.unwrap(document)
    assert preview['schema_version'] == 8 and document['schema_version'] == 12
    assert ('context' in document) is with_context and ('issue_source' in document) is with_source
    assert document['budget']['instance'] == prepared['budget']
    initial = task_envelopes.initial_preparation_contexts(document, spec['request']['repository']['starting_sha'])
    inventory = task_envelopes.preparation_dags(composition)['inventory']['dag']
    assert {frame['preparation_ports']['member'] for frame in initial} == {
        path for path in inventory.members if not inventory.predecessors[path]}
    assert all(frame['preparation_ports']['producers'] == {} and frame['stage'].startswith('inventory:') for frame in initial)
    created = tasks.create(state, 'demo', definition, revision, preview['preview_sha256'],
                           prepare_sha256=prepared['prepare_sha256'])
    assert created['status'] == 'published' and created['composition']['budget'] == document['budget']
    assert created['composition'].get('context') == document.get('context')
    assert ('issue_source' in created['composition']) is with_source
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope'] == document
    assert tasks.creation(state, 'demo', definition['task_id']) == created
    assert tasks.resume_create(state, 'demo', definition['task_id'], revision, created['intent_sha256']) == created


@pytest.mark.parametrize('change', ['memory', 'skill-head'])
def test_current_source_changes_block_preview_and_first_intent(budget_creation, tmp_path, change):
    state, registered, definition = budget_creation
    _select_context(state, definition, tmp_path)
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    if change == 'memory':
        selected = definition['context']['memories'][0]
        memory.save(state, 'demo', 'Corrected source', {'uri': 'repo://design', 'revision': '2'},
                    selected['id'], selected['revision'])
    else:
        selected = definition['context']['skills'][0]
        skill_assets.move_head(state, 'demo', selected['name'], selected['digest'], selected['revision'],
                               'rollback', 'Explicit same-digest revision event')
    with pytest.raises(ValueError, match='changed'):
        tasks.preview(state, 'demo', definition, 1)
    with pytest.raises(ValueError, match='changed'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                     prepare_sha256=preview['prepare_sha256'])
    assert tasks.creation(state, 'demo', definition['task_id'])['status'] == 'not_recorded'
    assert not (_root(registered) / 'tasks').exists()


def test_saved_current_intent_recovers_frozen_context_after_head_changes(budget_creation, monkeypatch, tmp_path):
    state, registered, definition = budget_creation
    _select_context(state, definition, tmp_path)
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    marker = tmp_path / 'first-publication-interrupted'
    _worker_injection(monkeypatch, '', f'''
from pathlib import Path
from agent_platform import core
original_write = core.write
def interrupted(path, value, **kwargs):
    result = original_write(path, value, **kwargs)
    marker = Path({str(marker)!r})
    if path.name == 'agent-bindings.json' and '/tasks/' in str(path) and not marker.exists():
        marker.write_text('Original intent and first file were saved')
        raise ValueError('Injected first publication interruption')
    return result
core.write = interrupted
''')
    with pytest.raises(ValueError, match='Injected first publication interruption'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                     prepare_sha256=preview['prepare_sha256'])
    pending = tasks.creation(state, 'demo', definition['task_id'])
    assert pending['status'] == 'pending' and marker.exists()
    selected = definition['context']['memories'][0]
    memory.save(state, 'demo', 'New current source', {'uri': 'repo://design', 'revision': '2'},
                selected['id'], selected['revision'])
    restored = tasks.resume_create(state, 'demo', definition['task_id'], 1, pending['intent_sha256'])
    assert restored['status'] == 'published'
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope'] == preview['files']['task.spec.json']


def test_complete_eighteen_leaf_wire_recovers_original_publication_and_job(registration, monkeypatch, tmp_path):
    """The shipped complete graph crosses every persisted request reader."""
    pytest.importorskip('temporalio')
    from temporalio.converter import DataConverter
    from test_presets import _publish_selected_moe
    from test_budget_jobs import _launch, _PENDING, _result

    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    from dev_platform.adapter import read_raw

    state, registered = registration
    example, published = _publish_selected_moe(state)
    definition = json.loads((example / 'task.example.json').read_bytes())
    definition['starting_sha'] = subprocess.check_output(
        ['git', '-C', registered['repo'], 'rev-parse', 'HEAD'], text=True).strip()
    definition['issue_id'] = '1'
    definition['budget'].update(wall_seconds=120, cleanup_seconds=5)
    definition['composition'].update(manifest=published['manifest']['path'], manifest_digest=published['manifest']['digest'])
    registered['allowed_paths'] = definition['input']['allowed_paths']
    registrations.register(state, registered, 0)
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    document = preview['files']['task.spec.json']
    encoded = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode()
    assert 1_048_576 < len(encoded) < task_envelopes.WIRE_LIMIT
    assert len(document['budget']['slots']) == 18
    marker = tmp_path / 'interrupted-large-publication'
    _worker_injection(monkeypatch, '', f'''
from pathlib import Path
from agent_platform import core
original_write = core.write
def interrupted(path, value, **kwargs):
    result = original_write(path, value, **kwargs)
    marker = Path({str(marker)!r})
    if path.name == 'agent-bindings.json' and '/tasks/' in str(path) and not marker.exists():
        marker.write_text('Original complete intent was saved')
        raise ValueError('Injected complete publication interruption')
    return result
core.write = interrupted
''')
    with pytest.raises(ValueError, match='Injected complete publication interruption'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                     prepare_sha256=prepared['prepare_sha256'])
    pending = tasks.creation(state, 'demo', definition['task_id'])
    assert pending['status'] == 'pending'
    shutil.rmtree(definition['composition']['manifest'])
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    restored = tasks.resume_create(state, 'demo', definition['task_id'], 1, pending['intent_sha256'])
    assert restored['status'] == 'published'
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope'] == document
    assert tasks.preparation(state, 'demo', definition['task_id'])['budget'] == prepared['budget']
    runtime, config = (Path(registered['execution'][key]) for key in ('state_directory', 'config_directory'))
    assert task_envelopes.decode_admission(read_raw(
        runtime / 'tasks' / definition['task_id'] / 'task.spec.json', task_envelopes.WIRE_LIMIT)) == document
    roots = {name: str(runtime / name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    adapter_config = {**roots, 'trusted_receipts': True}
    (config / 'adapter.json').write_text(json.dumps(adapter_config))
    selected = execution_input(document)
    operations = selected.activities(adapter_config)
    workflow = selected.workflow_type()()
    workflow.spec, workflow.admission = selected.spec, document
    initial = task_envelopes.initial_preparation_contexts(document, definition['starting_sha'])[0]
    context = workflow.context(initial['stage'], definition['starting_sha'])
    assert context == initial

    async def submit():
        for value in (document, context):
            payloads = await DataConverter.default.encode([value])
            assert await DataConverter.default.decode(payloads) == [value]
        job = await operations.submit(context)
        assert await operations.submit(context) == job
        assert await operations.poll({key: job[key] for key in ('task_id', 'job_id', 'job_sha256')}) is None
        return job

    job = asyncio.run(submit())
    path = operations.adapter.path('requests', definition['task_id'] + '/' + job['job_id'] + '.json')
    assert path.stat().st_size > 1_048_576 and task_envelopes.decode_job(read_raw(path, task_envelopes.WIRE_LIMIT))['context'] == context
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=str(config), AGENTFLOW_STATE_DIR=str(runtime),
        PYTHONPATH=os.pathsep.join(map(str, (IMPORT_ROOT,
            Path(registered['execution']['installation']) / 'local',
            Path(registered['execution']['installation']) / 'upstream/platform'))))
    receipt = _result(_launch(state, path, environment, worker=_PENDING))
    assert receipt['state'] == 'SUCCEEDED'
    assert _result(_launch(state, path, environment, worker="raise AssertionError('Unknown job body was replayed')")) == receipt
    fenced = asyncio.run(operations.adapter.fence(context))
    assert fenced['confirmed'] is True and fenced['unresolved_jobs'] == []
    # The public publisher is a separate SDK-free consumer of this same job.
    publisher_config = tmp_path / 'publisher.json'
    publisher_config.write_text(json.dumps({**adapter_config, 'requests': str(operations.adapter.roots['requests'])}))
    terminal = runtime / 'receipts' / definition['task_id'] / (job['job_id'] + '.json')
    publisher = '''
import importlib.abc, runpy, sys
class PureOnly(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'temporalio', 'mcp', 'jsonschema'} or fullname in {
                'ergora.storage.state', 'ergora.development.inputs', 'ergora.development.runtime.workflows'}:
            raise AssertionError('Publisher imported a runtime dependency: ' + fullname)
sys.meta_path.insert(0, PureOnly())
runpy.run_module('dev_platform.adapter', run_name='__main__')
'''
    published = subprocess.run([sys.executable, '-P', '-S', '-c', publisher, '--config', str(publisher_config),
        'publish-receipt', str(path), str(terminal)], env=environment, capture_output=True, text=True, timeout=20)
    assert published.returncode == 0, published.stdout + published.stderr
    assert json.loads(terminal.read_bytes()) == receipt


def test_complete_wire_rejects_overflow_without_widening_plain_contracts(budget_creation, monkeypatch, tmp_path):
    pytest.importorskip('temporalio')
    monkeypatch.syspath_prepend(str(native_resources.ROOT / 'platform/upstream/platform'))
    from dev_platform.adapter import ContractViolation, FileAdapter
    from dev_platform.adapter import read_raw
    from temporalio.exceptions import ApplicationError

    state, _, definition = budget_creation
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    document = tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']
    roots = {name: str(tmp_path / name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    config = {**roots, 'trusted_receipts': True}
    ordinary = FileAdapter(config)
    with pytest.raises(ContractViolation, match='Stage context exceeds'):
        asyncio.run(ordinary.submit({'padding': 'x' * 1_000_000}))
    plain = tmp_path / 'ordinary.json'
    plain.write_text(json.dumps({'padding': 'x' * 1_048_576}))
    with pytest.raises(ValueError, match='wire byte limit'):
        task_envelopes.decode_admission(read_raw(plain, task_envelopes.WIRE_LIMIT))
    plain.write_text(json.dumps({'context': {'padding': 'x' * 1_048_576}}))
    with pytest.raises(ValueError, match='wire byte limit'):
        task_envelopes.decode_job(read_raw(plain, task_envelopes.WIRE_LIMIT))
    oversized = {**document, 'padding': 'x' * task_envelopes.WIRE_LIMIT}
    with pytest.raises(ValueError, match='admission exceeds 4 MiB'):
        execution_input(oversized)
    # Bound actual file bytes, including otherwise valid JSON whitespace.
    for value, reader in ((document, task_envelopes.decode_admission),
                          ({'context': {'admission': document}}, task_envelopes.decode_job)):
        raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
        plain.write_bytes(raw + b' ' * (task_envelopes.WIRE_LIMIT - len(raw)))
        assert reader(read_raw(plain, task_envelopes.WIRE_LIMIT)) == value
        with plain.open('ab') as stream:
            stream.write(b' ')
        with pytest.raises(ValueError, match='size limit'):
            reader(read_raw(plain, task_envelopes.WIRE_LIMIT))
    operations = execution_input(document).activities(config)
    context = task_envelopes.initial_preparation_contexts(document, definition.get('starting_sha'))[0]
    context['author_ids'] = ['x' * task_envelopes.WIRE_LIMIT]
    with pytest.raises(ApplicationError, match='control-plane payload limit'):
        asyncio.run(operations.submit(context))
    assert not Path(roots['requests']).exists()


def test_v2_old_budgeted_definition_is_rejected_without_authorization_or_intent(budget_creation, monkeypatch):
    state, registered, definition = budget_creation
    # Reuse the existing real composition fixture's definition in a genuinely
    # first registration, without changing the v1 project or its originals.
    state = State(state.root.parent / 'design-control')
    registered = deepcopy(registered)
    registered['execution'] = {**registered['execution'],
        'config_directory': str(state.root.parent / 'design-config'),
        'state_directory': str(state.root.parent / 'design-runtime')}
    registered.update(schema_version=2, design_policy=design_policy())
    project = registrations.register(state, registered, 0)
    before = _files(state.root)
    starts = []
    original = tasks.task_preparation

    def preparation(*args, **kwargs):
        starts.append(args[2])
        return original(*args, **kwargs)

    monkeypatch.setattr(tasks, 'task_preparation', preparation)
    for operation in (lambda: tasks.prepare(state, 'demo', definition, 1),
                      lambda: tasks.preview(state, 'demo', definition, 1),
                      lambda: tasks.create(state, 'demo', definition, 1, '0' * 64, prepare_sha256='1' * 64)):
        with pytest.raises(ValueError, match='design_policy_execution_unsupported'):
            operation()
    assert starts == [] and state.project('demo') == project and _files(state.root) == before
    assert not _files(_root(registered))


def _root(registered):
    return Path(registered['execution']['state_directory'])


def _prefix(registered, definition):
    return _root(registered) / 'ergora/task-creations' / definition['task_id']


def _worker_injection(monkeypatch, code, owner_code=''):
    """Inject slowness at the real application worker, below the process owner."""
    original = subprocess.Popen
    def launch(argv, **kwargs):
        if (argv[-1] == 'from ergora.development.runtime.creation import main;main()'
                and '/operations/task-preparations/' in kwargs.get('env', {}).get('AGENTFLOW_STATE_DIR', '')):
            source = (
                'from ergora.runtime import processes\n'
                'original = processes.run\n'
                'def invoke(argv, *args, **kwargs):\n'
                '    argv = [*argv[:-1], ' + repr(code + '\n' +
                    'from ergora.development.runtime.creation import preparation_worker;preparation_worker()') + ']\n'
                '    return original(argv, *args, **kwargs)\n'
                'processes.run = invoke\n'
                + owner_code + '\n'
                'from ergora.development.runtime.creation import main;main()')
            argv = [*argv[:-1], source]
        return original(argv, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', launch)


def test_lost_preparation_reply_keeps_one_budget_and_preview_is_read_only(budget_creation, monkeypatch):
    state, registered, definition = budget_creation
    invoke = tasks.task_preparation
    result = {}
    def lost(*args, **kwargs):
        result.update(invoke(*args, **kwargs))
        raise OSError('Lost preparation reply')
    monkeypatch.setattr(tasks, 'task_preparation', lost)
    with pytest.raises(OSError, match='Lost preparation reply'):
        tasks.prepare(state, 'demo', definition, 1)
    monkeypatch.undo()
    assert result['status'] == 'prepared'
    prefix = _prefix(registered, definition)
    original = _files(prefix.parent)
    restored = tasks.prepare(State(state.root), 'demo', definition, 1)
    assert restored['budget'] == result['budget'] and restored['prepare_sha256'] == result['prepare_sha256']
    assert _files(prefix.parent) == original
    observations = _files(state.root / 'operations')
    preview = tasks.preview(state, 'demo', definition, 1)
    time.sleep(.05)
    assert tasks.preview(state, 'demo', definition, 1) == preview
    assert _files(state.root / 'operations') == observations
    assert _files(prefix.parent) == original and not (_root(registered) / 'tasks').exists()
    document = preview['files']['task.spec.json']
    selected = execution_input(document)
    assert selected.document == document and document['schema_version'] == 12
    assert document['budget']['instance'] == result['budget']
    assert len(document['budget']['slots']) == (len(document['composition']['preparation']['members'])
        + len(definition['input']['work_units']) + len(document['composition']['members']))
    assert Path('requests-composition-v12') in request_roots(Path('requests'))
    selected.require_submission()
    assert preview['prepare_sha256'] == restored['prepare_sha256']
    for prepare_sha, preview_sha in [('0' * 64, preview['preview_sha256']), (preview['prepare_sha256'], '0' * 64)]:
        with pytest.raises(ValueError, match='Preparation or preview changed'):
            tasks.create(state, 'demo', definition, 1, preview_sha, prepare_sha256=prepare_sha)
    shutil.rmtree(definition['composition']['manifest'])
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=preview['prepare_sha256'])
    assert created['status'] == 'published' and created['composition']['runtime_supported'] is True
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    assert not any((_root(registered) / name).exists() for name in ('ergora/task-submissions', 'requests-composition-v12', 'ingress'))
    environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=registered['execution']['config_directory'],
                       AGENTFLOW_STATE_DIR=registered['execution']['state_directory'],
                       PYTHONPATH=os.pathsep.join((str(IMPORT_ROOT),
                           str(native_resources.ROOT / 'platform/local'), str(native_resources.ROOT / 'platform/upstream/platform'))))
    # Constructing a budgeted Executor directly cannot bypass its job owner.
    direct = subprocess.run([sys.executable, '-c',
        'import json,sys;from pathlib import Path;from ergora.development.runtime.executor import Executor;'
        'Executor({"context":{"spec":json.load(sys.stdin)}},Path(sys.argv[1]))', str(state.root)],
        input=json.dumps(document['legacy_spec']), env=environment, capture_output=True, text=True, timeout=20)
    assert direct.returncode != 0 and 'requires its original dedicated owner' in direct.stderr
    assert not (_root(registered) / 'workspaces').exists()


def test_concurrent_preparation_observes_original_authorization(budget_creation, monkeypatch, tmp_path):
    state, registered, definition = budget_creation
    marker = tmp_path / 'worker-entered'
    _worker_injection(monkeypatch, f"from pathlib import Path\nimport time\nPath({str(marker)!r}).write_text('entered')\ntime.sleep(.8)")
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(tasks.prepare, state, 'demo', definition, 1)
        deadline = time.monotonic() + 5
        while not marker.exists() and not first.done() and time.monotonic() < deadline:
            time.sleep(.02)
        assert marker.exists()
        second = pool.submit(tasks.prepare, State(state.root), 'demo', definition, 1).result()
        conflicting = deepcopy(definition)
        conflicting['input']['goal'] = 'A different concurrent authorization'
        with pytest.raises(ValueError, match='different preparation'):
            tasks.prepare(State(state.root), 'demo', conflicting, 1)
        completed = first.result()
    assert completed['status'] == 'prepared' and second['status'] in ('authorized', 'unknown', 'prepared')
    assert second['budget'] == completed['budget']
    files = _files(_prefix(registered, definition).parent)
    again = tasks.prepare(state, 'demo', definition, 1)
    assert again['budget'] == completed['budget'] and _files(_prefix(registered, definition).parent) == files


@pytest.mark.parametrize('boundary', ['installation', 'manifest', 'compiler'])
def test_actual_prepare_stops_slow_materials_and_detached_descendants(budget_creation, monkeypatch, tmp_path, boundary):
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=3, cleanup_seconds=1)
    marker = tmp_path / 'slow-worker.json'
    detached = 'import os,signal,time;os.setsid();signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'
    slow = f'''
import json,os,subprocess,sys,time
from pathlib import Path
import ergora.native.resources as native_resources
import ergora.definitions.workflows as workflow_definitions
from ergora.development.runtime.creation import _Creation
def slow(*args, **kwargs):
    child = subprocess.Popen([sys.executable, '-c', {detached!r}])
    stat = Path('/proc/' + str(child.pid) + '/stat').read_text().rsplit(')', 1)[1].split()
    Path({str(marker)!r}).write_text(json.dumps({{'worker': os.getpid(), 'child': child.pid, 'start_ticks': stat[19]}}))
    time.sleep(60)
'''
    target = {'installation': 'native_resources.validate_installation', 'manifest': 'workflow_definitions.inspect_manifest',
              'compiler': '_Creation.compile'}[boundary]
    _worker_injection(monkeypatch, slow + '\n' + target + ' = slow')
    begin = time.monotonic()
    prepared = tasks.prepare(state, 'demo', definition, 1)
    elapsed = time.monotonic() - begin
    assert marker.exists() and prepared['status'] == 'exhausted', prepared
    assert elapsed < definition['budget']['wall_seconds'] + 1
    identities = json.loads(marker.read_bytes())
    assert not Path('/proc/' + str(identities['worker'])).exists()
    assert not Path('/proc/' + str(identities['child'])).exists()
    assert prepared['outcome']['cleanup_confirmed'] is True
    prefix = _prefix(registered, definition)
    assert not Path(str(prefix) + '.prepare-work/compile').exists()
    assert not Path(str(prefix) + '.prepared.json').exists() and not (_root(registered) / 'tasks').exists()
    original = _files(prefix.parent)
    assert tasks.prepare(state, 'demo', definition, 1)['budget'] == prepared['budget']
    assert _files(prefix.parent) == original
    with pytest.raises(ValueError, match='confirmed complete preparation'):
        tasks.preview(state, 'demo', definition, 1)


def test_expiration_and_revision_cannot_renew_or_publish_an_authorization(budget_creation):
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=3, cleanup_seconds=1)
    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    remaining = tasks.preparation(state, 'demo', definition['task_id'])['budget_status']['work_remaining_seconds']
    time.sleep(remaining + .1)
    assert tasks.preview(state, 'demo', definition, 1) == preview
    with pytest.raises(ValueError, match='budget is exhausted'):
        tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=prepared['prepare_sha256'])
    assert not (_root(registered) / 'tasks').exists()

    changed = deepcopy(definition)
    changed['budget']['wall_seconds'] += 10
    with pytest.raises(ValueError, match='different preparation'):
        tasks.prepare(state, 'demo', changed, 1)
    projects.bind(state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'changed-model'}, 1)
    with pytest.raises(ValueError, match='revision changed after preparation'):
        tasks.preview(state, 'demo', definition, 2)
    assert tasks.preparation(state, 'demo', definition['task_id'])['budget'] == prepared['budget']


def test_attempt_storage_cannot_move_the_absolute_work_cutoff(budget_creation, monkeypatch, tmp_path):
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=6, cleanup_seconds=1)
    marker = tmp_path / 'slow-work-entered'
    worker = f'''
import time
from pathlib import Path
import ergora.native.resources as native_resources
def slow(*args):
    Path({str(marker)!r}).write_text('work entered')
    time.sleep(60)
native_resources.validate_installation = slow
'''
    owner = '''
import time
from agent_platform import core
write = core.write
def delayed_attempt(path, value, **kwargs):
    result = write(path, value, **kwargs)
    if str(path).endswith('.prepare-attempt.json'):
        time.sleep(2)
    return result
core.write = delayed_attempt
'''
    _worker_injection(monkeypatch, worker, owner)
    result = tasks.prepare(state, 'demo', definition, 1)
    assert marker.exists() and result['status'] == 'exhausted'
    assert result['outcome']['elapsed_seconds'] < definition['budget']['wall_seconds'] + .5


def test_final_witness_storage_cannot_report_a_late_preparation_as_prepared(budget_creation, monkeypatch, tmp_path):
    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=3, cleanup_seconds=1)
    marker = tmp_path / 'final-witness-fsync'
    owner = f'''
import os,time
from pathlib import Path
from agent_platform import core
write,fsync = core.write,os.fsync
writing_outcome = False
def track_outcome(path, value, **kwargs):
    global writing_outcome
    writing_outcome = isinstance(value, dict) and value.get('cleanup_confirmed') is True
    try:
        return write(path, value, **kwargs)
    finally:
        writing_outcome = False
def slow_fsync(fd):
    marker = Path({str(marker)!r})
    if writing_outcome and not marker.exists():
        marker.write_text('final outcome is still being persisted')
        time.sleep({definition['budget']['wall_seconds'] + 1})
    return fsync(fd)
core.write,os.fsync = track_outcome,slow_fsync
'''
    _worker_injection(monkeypatch, '', owner)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(tasks.prepare, state, 'demo', definition, 1)
        deadline = time.monotonic() + 10
        while not marker.exists() and not pending.done() and time.monotonic() < deadline:
            time.sleep(.02)
        assert marker.exists()
        assert tasks.preparation(State(state.root), 'demo', definition['task_id'])['status'] == 'unknown'
        result = pending.result(timeout=15)
    assert result['status'] == 'exhausted'
    assert result['outcome']['elapsed_seconds'] >= definition['budget']['wall_seconds']
    assert result['outcome']['overrun_seconds'] > 0
    prefix = _prefix(registered, definition)
    original = _files(prefix.parent)
    assert tasks.prepare(state, 'demo', definition, 1)['outcome'] == result['outcome']
    assert _files(prefix.parent) == original
    with pytest.raises(ValueError, match='confirmed complete preparation'):
        tasks.preview(state, 'demo', definition, 1)


def test_actual_publisher_keeps_revision_lock_after_observer_returns_unknown(budget_creation, monkeypatch, tmp_path):
    import fcntl

    state, registered, definition = budget_creation
    prepared = tasks.prepare(state, 'demo', definition, 1)
    preview = tasks.preview(state, 'demo', definition, 1)
    gate, entered = tmp_path / 'publication.lock', tmp_path / 'publisher-entered'
    owner = f'''
import fcntl
from pathlib import Path
from ergora.development.runtime.creation import _Creation
publish = _Creation.publish
def held_publication(self, *args, **kwargs):
    Path({str(entered)!r}).write_text('actual publisher owns revision')
    with Path({str(gate)!r}).open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
    return publish(self, *args, **kwargs)
_Creation.publish = held_publication
'''
    _worker_injection(monkeypatch, '', owner)
    launch = subprocess.Popen
    def short_observation(argv, **kwargs):
        process = launch(argv, **kwargs)
        if '/operations/task-preparations/' in kwargs.get('env', {}).get('AGENTFLOW_STATE_DIR', ''):
            wait = process.wait
            process.wait = lambda timeout=None: wait(timeout=.2 if timeout == 30 else timeout)
        return process
    monkeypatch.setattr(subprocess, 'Popen', short_observation)
    with gate.open('wb') as lock, ThreadPoolExecutor(max_workers=1) as pool:
        fcntl.flock(lock, fcntl.LOCK_EX)
        observed = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                                prepare_sha256=prepared['prepare_sha256'])
        assert observed['status'] == 'unknown'
        try:
            deadline = time.monotonic() + 5
            while not entered.exists() and time.monotonic() < deadline:
                time.sleep(.02)
            assert entered.exists()
            binding = pool.submit(projects.bind, state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'later'}, 1)
            time.sleep(.3)
            assert not binding.done() and state.project('demo')['revision'] == 1
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
        assert binding.result(timeout=5)['revision'] == 2
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = tasks.creation(state, 'demo', definition['task_id'])
        if result['status'] == 'published':
            break
        time.sleep(.02)
    assert result['status'] == 'published' and result['created_revision'] == 1


def test_cap_and_unsupported_dimensions_fail_before_executable_publication(budget_creation):
    state, registered, definition = budget_creation
    definition['budget']['tokens'] = 100
    with pytest.raises(ValueError, match='Additional properties'):
        tasks.prepare(state, 'demo', definition, 1)
    assert not _root(registered).exists()
    del definition['budget']['tokens']
    definition['budget']['model_invocations'] = 1
    preview = tasks.preview(state, 'demo', definition, 1)
    assert preview['route_admission']['status'] == 'blocked'
    assert 'Known model call slots exceed' in preview['route_admission']['reason']
    assert preview['runtime_status'] == 'not_queried'
    assert tasks.preparation(state, 'demo', definition['task_id'])['status'] == 'not_recorded'
    assert not _root(registered).exists()

    prepared = tasks.prepare(state, 'demo', definition, 1)
    assert prepared['status'] == 'failed' and prepared['outcome']['cleanup_confirmed']
    prefix = _prefix(registered, definition)
    stderr = Path(str(prefix) + '.prepare-work/process/stderr.txt').read_text()
    assert 'Known model call slots exceed' in stderr
    assert not (_root(registered) / 'tasks').exists()


def test_unconfirmed_cleanup_cannot_publish_prepared_materials(budget_creation, monkeypatch, tmp_path):
    import fcntl

    state, registered, definition = budget_creation
    definition['budget'].update(wall_seconds=5, cleanup_seconds=1)
    gate, entered, native_pid = tmp_path / 'cleanup.lock', tmp_path / 'cleanup-entered', tmp_path / 'native-pid'
    detached = 'import os,signal,time;os.setsid();signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'
    worker = ("import subprocess,sys\nfrom pathlib import Path\n"
              f"child = subprocess.Popen([sys.executable, '-c', {detached!r}])\n"
              f"Path({str(native_pid)!r}).write_text(str(child.pid))\n")
    owner = f'''
import fcntl
from pathlib import Path
reap = processes._reap_children
def held_cleanup():
    Path({str(entered)!r}).write_text('cleanup not confirmed')
    with Path({str(gate)!r}).open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
    reap()
processes._reap_children = held_cleanup
'''
    _worker_injection(monkeypatch, worker, owner)
    with gate.open('wb') as lock, ThreadPoolExecutor(max_workers=1) as pool:
        fcntl.flock(lock, fcntl.LOCK_EX)
        future = pool.submit(tasks.prepare, state, 'demo', definition, 1)
        try:
            deadline = time.monotonic() + 8
            while not entered.exists() and not future.done() and time.monotonic() < deadline:
                time.sleep(.02)
            assert entered.exists()
            status = tasks.preparation(state, 'demo', definition['task_id'])
            assert status['status'] == 'unknown' and 'outcome' not in status
            pid = int(native_pid.read_text())
            assert Path('/proc/' + str(pid)).exists()
            prefix = _prefix(registered, definition)
            assert not Path(str(prefix) + '.prepared.json').exists()
            assert not Path(str(prefix) + '.prepare-result.json').exists()
            # Safety cleanup can finish later; that must not become in-budget success.
            time.sleep(status['budget_status']['work_remaining_seconds'] + definition['budget']['cleanup_seconds'] + .1)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
        result = future.result(timeout=5)
    assert result['status'] == 'exhausted' and result['outcome']['cleanup_confirmed']
    assert not Path('/proc/' + str(pid)).exists()
    assert tasks.prepare(state, 'demo', definition, 1)['budget'] == status['budget']


def test_cli_and_http_use_the_same_original_preparation(budget_creation, tmp_path):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.interfaces.web import create_app

    state, registered, definition = budget_creation
    source = tmp_path / 'task.json'
    source.write_text(json.dumps(definition))
    environment = dict(os.environ, PYTHONPATH=str(IMPORT_ROOT))
    command = [sys.executable, '-m', 'ergora', '--home', str(state.root), 'task']
    prepared = subprocess.run([*command, 'prepare', 'demo', '--definition', str(source), '--revision', '1'],
                              capture_output=True, text=True, env=environment, timeout=40)
    assert prepared.returncode == 0, prepared.stderr
    original = json.loads(prepared.stdout)
    with TestClient(create_app(state.root), base_url='http://127.0.0.1',
                    headers={'Origin': 'http://127.0.0.1', 'X-Ergora-Request': '1'}) as client:
        shown = client.get('/api/projects/demo/tasks/' + definition['task_id'] + '/preparation')
        assert shown.status_code == 200 and shown.json()['budget'] == original['budget']
        duplicate = client.post('/api/projects/demo/tasks/prepare', json={'definition': definition, 'revision': 1})
        assert duplicate.status_code == 200 and duplicate.json()['budget'] == original['budget']
        response = client.post('/api/projects/demo/tasks/preview', json={'definition': definition, 'revision': 1})
        assert response.status_code == 200, response.text
        preview = response.json()
        created = client.post('/api/projects/demo/tasks', json={'definition': definition, 'revision': 1,
            'prepare_sha256': original['prepare_sha256'], 'preview_sha256': preview['preview_sha256']})
        assert created.status_code == 200 and created.json()['status'] == 'published'
        document = preview['files']['task.spec.json']
        modified = deepcopy(document)
        modified['budget']['slots'].pop('inventory')
        modified['sha256'] = task_envelopes.identity({key: value for key, value in modified.items() if key != 'sha256'})
        with pytest.raises(ValueError, match='call slots differ'):
            execution_input(modified)
