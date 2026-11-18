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
def full_graph(work_graph, tmp_path, request):
    from fixtures.full_stage_acceptance import prepare_graph

    library, grant, _, execution, units = work_graph
    identity, version = prepare_graph(tmp_path / 'full-graph', library, EXAMPLES,
                                      concurrency=getattr(request, 'param', 2))
    graph = workflows.preview(library.root, identity, version, grant)
    def nested(path):
        return 'root/development/' + path.removeprefix('root/')
    execution = {**execution, 'protocol': 'work-units-v2', 'instance': nested(execution['instance']),
                 'assignments': {key: nested(path) for key, path in execution['assignments'].items()}}
    preparation = {'protocol': 'preparation-dag-v1', 'mode': 'task-mcp', 'repository_paths': ['src'],
        **{stage: {'instance': 'root/development/preparation/' + stage,
                   'coordinator': 'root/development/preparation/' + stage + '/coordinator'}
           for stage in ('inventory', 'plan')}}
    return library, grant, graph, execution, units, preparation


@pytest.fixture
def full_creation(work_creation, full_graph, tmp_path):
    state, registered, definition = work_creation
    library, grant, graph, execution, _, preparation = full_graph
    manifest = workflows.prepare_manifest(library.root, graph['root']['id'], graph['root']['version'], grant, tmp_path / 'full-manifest')
    definition.update(schema_version=8, budget={'wall_seconds': 120, 'cleanup_seconds': 5, 'model_invocations': 258})
    option = definition['composition']
    option.update(manifest=manifest['path'], manifest_digest=manifest['digest'], execution=execution, preparation=preparation,
                  review_instance='root/development/review', native={'protocol': 'six-stage-v1', 'instance': 'root/development'})
    option['backend_overrides'] = {'root/development/' + path.removeprefix('root/'): value
                                   for path, value in option['backend_overrides'].items()}
    return state, registered, definition


def test_frozen_preparation_survives_source_removal_and_keeps_its_original_route(full_creation, monkeypatch):
    pytest.importorskip('temporalio')
    from ergora import reference
    from temporalio.workflow import _Definition

    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    state, registered, definition = full_creation
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    document = preview['files']['task.spec.json']
    selected = execution_input(document)
    selected.require_submission()
    assert document['schema_version'] == 12 and preview['schema_version'] == 8
    assert selected.task_queue('dev') == 'dev.composition-v12'
    assert selected.request_root(Path('requests')) == Path('requests-composition-v12')
    sdk_definition = _Definition.must_from_run_fn(selected.entrypoint)
    assert sdk_definition.name == 'ErgoraCompositionWorkflowV12'
    import asyncio
    from ergora.reference_worker import _ErgoraPackage
    from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner

    async def prepare_sdk():
        finder = _ErgoraPackage()
        sys.meta_path.insert(0, finder)
        try:
            SandboxedWorkflowRunner().prepare_workflow(sdk_definition)
        finally:
            sys.meta_path.remove(finder)
    asyncio.run(prepare_sdk())
    code = ('import json,sys;sys.path.insert(0,' + repr(str(Path(reference.__file__).parent.parent)) + ');'
            'from ergora.reference_inputs import execution_input;'
            'selected=execution_input(json.load(sys.stdin));selected.require_submission();'
            'assert not any(name in sys.modules for name in ("jsonschema","temporalio","mcp"));'
            'print(selected.task_queue("dev"))')
    isolated = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code], input=json.dumps(document),
                              capture_output=True, text=True, timeout=20)
    assert isolated.returncode == 0, isolated.stderr
    assert isolated.stdout.strip() == 'dev.composition-v12'
    assert {member['role'] for member in document['composition']['preparation']['members'].values()} == {'inspector', 'planner'}
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'],
                           prepare_sha256=preview['prepare_sha256'])
    shutil.rmtree(definition['composition']['manifest'])
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    runtime = Path(registered['execution']['state_directory'])
    intent = runtime / 'ergora/task-creations' / (definition['task_id'] + '.intent.json')
    modified = json.loads(intent.read_bytes())
    modified['definition']['composition']['preparation']['repository_paths'] = ['src/other']
    intent.write_text(json.dumps(modified))
    with pytest.raises(ValueError, match='differs'):
        tasks.creation(state, 'demo', definition['task_id'])


def test_text_only_cannot_silently_drop_required_skill_attachments(full_creation):
    state, registered, definition = full_creation
    definition['composition']['preparation']['mode'] = 'text-only'
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'failed'
    runtime = Path(registered['execution']['state_directory'])
    stderr = (runtime / 'ergora/task-creations' / (definition['task_id'] + '.prepare-work/process/stderr.txt')).read_text()
    assert 'attachments require task-mcp' in stderr


@pytest.mark.skipif(sys.platform != 'linux', reason='Native stage monitor requires Linux/WSL2')
@pytest.mark.parametrize('case', ['full', 'serial', 'capacity', 'unread', 'source-artifact', 'source-claim', 'source-receipt', 'owner-source-artifact', 'issue-source'])
def test_real_preparation_calls_and_original_stage_results(tmp_path, case):
    pytest.importorskip('temporalio')
    pytest.importorskip('mcp')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'large-change', 'command',
        'composition-work-materials-' + case], capture_output=True, text=True, timeout=210)
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)
    if record.get('skip'):
        pytest.skip(record['skip'])
    assert record['case'] == case and record['original_owners']


@pytest.mark.parametrize('full_graph,case', [(1, 'complete'), (2, 'complete'), (2, 'duplicate'), (2, 'stop')], indirect=['full_graph'])
def test_preparation_ready_loop_uses_frozen_capacity_and_stops_successors(full_creation, full_graph, monkeypatch, case):
    import asyncio
    from datetime import datetime, timezone
    from ergora import reference, task_envelopes

    pytest.importorskip('temporalio')
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from dev_platform.workflow import StopWork
    from temporalio import workflow

    state, _, definition = full_creation
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    document = tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']
    selected = execution_input(document)
    app = selected.workflow_type()()
    app.spec, app.admission = selected.spec, document
    monkeypatch.setattr(workflow, 'wait', asyncio.wait)
    monkeypatch.setattr(workflow, 'now', lambda: datetime.now(timezone.utc))
    active, maximum, contexts = set(), [], []

    async def call(name, context, result_type=dict):
        if name == 'dev_submit':
            contexts.append(context)
            active.add(context['stage'])
            maximum.append(len(active))
            return context
        assert name == 'dev_poll'
        await asyncio.sleep(.02)
        active.remove(context['stage'])
        if case == 'stop':
            app.cancel_reason = 'Controlled stop before a preparation successor'
        return {'job_id': context['job_id'], 'job_sha256': task_envelopes.identity(context),
                'state': 'SUCCEEDED', 'candidate_sha': context['expected_candidate_sha'],
                'actor': {'id': context['stage'], 'session_id': 'duplicate' if case == 'duplicate' else context['job_id']}}

    app.call = call
    async def exercise():
        starting = selected.spec['request']['repository']['starting_sha']
        inventory = await app.stage('inventory', starting)
        await app.stage('plan', starting, dependencies={'inventory': inventory})
    if case != 'complete':
        with pytest.raises(StopWork, match='distinct|Controlled stop'):
            asyncio.run(exercise())
        assert not any(context['stage'] in ('inventory', 'plan') for context in contexts)
    else:
        asyncio.run(exercise())
        assert len(contexts) == 6 and set(app.results) == set(document['budget']['slots']) - {
            stage for stage in document['budget']['slots'] if stage.startswith(('work:', 'review:'))}
        assert len(app.authors()[1]) == 6
        for context in contexts:
            group_stage = 'inventory' if context['stage'].startswith('inventory') else 'plan'
            assert context['dependencies'] == ({} if group_stage == 'inventory' else {'inventory': app.results['inventory']})
            if context['stage'] in ('inventory', 'plan'):
                assert len(context['preparation_ports']['producers']) == 2
        limit = next(group for group in task_envelopes.preparation_dags(document['composition']).values())['dag']
        expected = min(scope['limit'] for leaf in limit.members.values() for scope in leaf['concurrency_scopes'])
        assert max(maximum) == min(2, expected)
    assert not app.active_stages
