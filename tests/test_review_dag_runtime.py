"""Explicit DAG admissions keep original jobs, opinions and execution ownership."""

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from ergora import agent_definitions, reference, task_envelopes, tasks, workflow_definitions as workflows
from test_composition_tasks import composed_creation
from test_task_creation import creation_project
from test_registrations import installation, registration
from test_task_submission import native_client
from test_workflow_definitions import EXAMPLES, grant


@pytest.fixture
def dag_creation(composed_creation, tmp_path, request):
    state, registered, definition = composed_creation
    for source in sorted((EXAMPLES / 'composition/agents').iterdir()):
        agent_definitions.import_bundle(state, source)
    for name in ('structure-review', 'correctness-review', 'test-value-review', 'serial-review'):
        workflows.import_bundle(state, EXAMPLES / 'composition' / name)
    root, concurrency = 'serial-review', 4
    if getattr(request, 'param', None) == 'unrelated':
        from test_workflow_definitions import write_bundle

        document = json.loads((EXAMPLES / 'composition/serial-review/workflow.json').read_bytes())
        document.update(id='independent-progress', resources=[])
        slow = {**document['nodes'][0], 'id': 'slow'}
        document['nodes'].insert(0, slow)
        document['nodes'][-1]['depends_on'].append('slow')
        workflows.import_bundle(state, write_bundle(tmp_path / 'progress', document))
        root, concurrency = document['id'], 2
    manifest = workflows.prepare_manifest(state.root, root, '1.0.0', grant(concurrency=concurrency), tmp_path / 'dag-manifest')
    definition['composition'].update(manifest=manifest['path'], manifest_digest=manifest['digest'],
        backend_overrides={}, diversity={'policy': 'allow-same'}, review_protocol='dag-v1')
    return state, registered, definition


@pytest.fixture
def dag_input(dag_creation, monkeypatch):
    pytest.importorskip('temporalio')
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    state, _, definition = dag_creation
    return tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']


def test_dag_protocol_is_explicit_frozen_and_routed_by_its_original_input(dag_input, dag_creation):
    from ergora.reference_inputs import execution_input
    from ergora.reference_task_runtime import VerifiedSpecClient
    from temporalio.workflow import _Definition

    state, registered, definition = dag_creation
    old_definition = deepcopy(definition)
    del old_definition['composition']['review_protocol']
    old = tasks.preview(state, 'demo', old_definition, 1)['files']['task.spec.json']
    assert old['schema_version'] == 2 and 'review_protocol' not in old['composition']
    assert task_envelopes.summary(old)['runtime_supported'] is False
    assert dag_input['schema_version'] == 4 and dag_input['legacy_spec'] == old['legacy_spec']
    assert all(member['review_requirement'] == 'required' for member in dag_input['composition']['members'].values())
    selected = execution_input(dag_input)
    selected.require_submission()
    native = SimpleNamespace(start_workflow=AsyncMock(return_value='dag-handle'))
    client = VerifiedSpecClient(native, dag_input)
    assert asyncio.run(client.start_workflow(None, selected.spec, task_queue='development', id='dag')) == 'dag-handle'
    assert native.start_workflow.call_args.args == (selected.entrypoint, dag_input)
    assert native.start_workflow.call_args.kwargs['task_queue'] == 'development.composition-v4'
    assert _Definition.must_from_run_fn(selected.entrypoint).name == 'ErgoraCompositionWorkflowV4'
    assert selected.request_root(Path(registered['execution']['state_directory']) / 'requests').name == 'requests-composition-v4'
    preview = tasks.preview(state, 'demo', definition, 1)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    shutil.rmtree(Path(definition['composition']['manifest']))
    shutil.rmtree(state.root / 'workflow-definitions')
    shutil.rmtree(state.root / 'agent-definitions')
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope'] == dag_input
    intent = Path(registered['execution']['state_directory']) / 'ergora/task-creations' / (definition['task_id'] + '.intent.json')
    changed = json.loads(intent.read_bytes())
    del changed['definition']['composition']['review_protocol']
    intent.write_text(json.dumps(changed), encoding='utf-8')
    with pytest.raises(ValueError, match='composition differs from its saved selection'):
        tasks.creation(state, 'demo', definition['task_id'])


@pytest.mark.parametrize('owned', [False, True])
def test_unknown_dag_submission_requires_its_original_memo_without_restarting(dag_creation, native_client, monkeypatch, owned):
    from test_task_submission import _calls, _resume, _seed_run, _start, _status

    state, registered, definition = dag_creation
    runtime = Path(registered['execution']['installation']) / '.venv'
    if not runtime.exists():
        runtime.symlink_to(sys.prefix, target_is_directory=True)
    preview = tasks.preview(state, 'demo', definition, 1)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    creation = state, registered, definition, created
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'after-attempt')
    with pytest.raises(ValueError, match='interruption after attempt'):
        _start(creation)
    assert _status(creation)['status'] == 'unknown'
    _seed_run(creation, owned=owned)
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'normal')
    if owned:
        assert _resume(creation)['run_id'] == 'owned-run'
    else:
        with pytest.raises(ValueError, match='matching submission memo'):
            _resume(creation)
        assert _status(creation)['status'] == 'unknown'
    assert 'start' not in _calls(creation)


@pytest.mark.parametrize('worker_version', [2, 3])
def test_old_workflow_refuses_dag_before_any_activity(dag_input, worker_version):
    from temporalio.exceptions import ApplicationError

    from ergora.reference_workflows import CompositionDevelopmentWorkflow, ReviewRequirementsWorkflow
    run = (CompositionDevelopmentWorkflow if worker_version == 2 else ReviewRequirementsWorkflow)()
    run.call = AsyncMock(side_effect=AssertionError('No activity before exact version admission'))
    with pytest.raises(ApplicationError, match=f'requires a v{worker_version} formal admission'):
        asyncio.run(run.run(dag_input))
    run.call.assert_not_called()


@pytest.mark.parametrize('failure', ['protocol', 'selection', 'obligation'])
def test_dag_persisted_selection_cannot_be_downgraded_or_reinterpreted(dag_input, failure):
    document = deepcopy(dag_input)
    if failure == 'protocol':
        document['composition']['review_protocol'] = 'implicit'
    elif failure == 'selection':
        document['schema_version'] = 3
    else:
        document['composition']['members']['root/structure/review']['review_requirement'] = 'advisory'
    document['sha256'] = task_envelopes.identity({key: value for key, value in document.items() if key != 'sha256'})
    with pytest.raises(ValueError, match='selection|requirement'):
        task_envelopes.unwrap(document)


@pytest.mark.parametrize('case', ['progress', 'reused-session', 'cancel-on-result'])
def test_serial_predecessors_and_cancelled_results_cannot_launch_successors(dag_input, monkeypatch, case):
    from dev_platform.workflow import StopWork
    from ergora.reference_inputs import execution_input
    from temporalio import workflow

    monkeypatch.setattr(workflow, 'now', lambda: datetime.now(timezone.utc))
    run = execution_input(dag_input).workflow_type()()
    run.spec, run.admission = dag_input['legacy_spec'], dag_input
    candidate = run.spec['request']['repository']['starting_sha']
    contexts = {}

    async def exercise():
        structure_done, successors = asyncio.Event(), asyncio.Queue()

        async def call(name, value, result_type=dict):
            if name == 'dev_submit':
                contexts[value['stage']] = value
                return {'context': value}
            context = value['context']
            path = context['stage'].removeprefix('review:')
            if path == 'root/structure/review':
                await structure_done.wait()
                if case == 'cancel-on-result':
                    run.cancel_reason = 'Cancellation arrived during result delivery'
            else:
                await successors.put(path)
            receipt = {'job_id': context['job_id'], 'job_sha256': task_envelopes.identity(context),
                'state': 'SUCCEEDED', 'candidate_sha': candidate,
                'actor': {'id': 'reviewer', 'session_id': 'shared' if case == 'reused-session' else path},
                'artifacts': [], 'checks': []}
            return {'receipt': receipt, 'review_decision': 'approve'}

        run.call = call
        pending = asyncio.create_task(run.stage('review', candidate))
        while not contexts:
            await asyncio.sleep(0)
        assert set(contexts) == {'review:root/structure/review'}
        structure_done.set()
        if case == 'progress':
            assert {await asyncio.wait_for(successors.get(), 2), await asyncio.wait_for(successors.get(), 2)} == {
                'root/correctness/review', 'root/test-value/review'}
            aggregate = await asyncio.wait_for(pending, 2)
            for stage in ('review:root/correctness/review', 'review:root/test-value/review'):
                supplied = contexts[stage]['review_ports']
                assert supplied['ports']['sources'] == ['root/structure/review']
                assert supplied['producers'] == {'root/structure/review': run.results['review:root/structure/review']}
            assert set(aggregate['members']) == set(dag_input['composition']['members'])
        else:
            with pytest.raises(StopWork, match='distinct independent|Cancellation arrived'):
                await asyncio.wait_for(pending, 2)
            assert 'review' not in run.results
            if case == 'cancel-on-result':
                assert set(contexts) == {'review:root/structure/review'}
        assert not run.active_stages

    asyncio.run(exercise())


@pytest.mark.parametrize('dag_creation', ['unrelated'], indirect=True)
def test_finished_predecessor_can_release_a_successor_while_an_unrelated_branch_is_running(dag_input, monkeypatch):
    from ergora.reference_inputs import execution_input
    from temporalio import workflow

    monkeypatch.setattr(workflow, 'now', lambda: datetime.now(timezone.utc))
    run = execution_input(dag_input).workflow_type()()
    run.spec, run.admission = dag_input['legacy_spec'], dag_input

    async def exercise():
        first, slow, entered = asyncio.Event(), asyncio.Event(), asyncio.Queue()

        async def call(name, value, result_type=dict):
            if name == 'dev_submit':
                return {'context': value}
            context = value['context']
            path = context['stage'].removeprefix('review:')
            await entered.put(path)
            if path == 'root/structure/review':
                await first.wait()
            elif path == 'root/slow/review':
                await slow.wait()
            return {'receipt': {'job_id': context['job_id'], 'job_sha256': task_envelopes.identity(context),
                'actor': {'session_id': path}, 'artifacts': []}, 'review_decision': 'approve'}

        run.call = call
        pending = asyncio.create_task(run.stage('review', run.spec['request']['repository']['starting_sha']))
        try:
            assert {await asyncio.wait_for(entered.get(), 2), await asyncio.wait_for(entered.get(), 2)} == {
                'root/structure/review', 'root/slow/review'}
            first.set()
            assert await asyncio.wait_for(entered.get(), 2) in ('root/correctness/review', 'root/test-value/review')
            assert not slow.is_set() and 'review:root/slow/review' in run.active_stages
            slow.set()
            assert len((await asyncio.wait_for(pending, 2))['members']) == 4
        finally:
            first.set()
            slow.set()
            pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)

    asyncio.run(exercise())


@pytest.mark.parametrize('mode', ['full', 'artifact', 'receipt', 'request', 'claim', 'binding', 'capacity'])
@pytest.mark.skipif(sys.platform != 'linux', reason='Formal executor requires Linux / WSL2')
def test_executor_transports_complete_original_producers_or_rejects_before_the_model(tmp_path, mode):
    pytest.importorskip('temporalio')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command',
        'composition-dag-' + mode], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['mode'] == mode
    if mode == 'full':
        assert summary['complete_artifacts'] and summary['ancestor_materials'] and summary['recovery_preserved']
    else:
        assert summary['before_model'] and summary['state'] == 'FAILED'


@pytest.mark.parametrize('version', [2, 3])
@pytest.mark.skipif(sys.platform != 'linux', reason='Formal executor requires Linux / WSL2')
def test_old_review_executors_keep_their_sdk_free_terminal_receipt_contract(tmp_path, version):
    pytest.importorskip('temporalio')
    result = subprocess.run([sys.executable, str(Path(__file__).parent / 'fixtures/reference_acceptance.py'),
        str(tmp_path), 'repository-governance', 'command', f'composition-no-worker-sdk-v{version}'],
        capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['candidate_bound']
    if version == 3:
        assert summary['receipt_state'] == 'SUCCEEDED' and summary['decision'] == 'approve'
    else:
        assert len(summary['stages']) == 6
