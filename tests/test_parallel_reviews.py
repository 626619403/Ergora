"""Parallel review follows the original stage, receipt and cancellation contracts."""

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

import pytest

from ergora import agent_definitions, reference, task_envelopes, tasks, workflow_definitions as workflows
from test_composition_tasks import composed_creation
from test_task_creation import creation_project
from test_registrations import installation, registration
from test_task_submission import native_client
from test_workflow_definitions import EXAMPLES, grant


@pytest.fixture
def parallel_creation(composed_creation, tmp_path, request):
    state, registration, definition = composed_creation
    for source in sorted((EXAMPLES / 'composition/agents').iterdir()):
        agent_definitions.import_bundle(state, source)
    for name in ('structure-review', 'correctness-review', 'test-value-review', 'parallel-review'):
        workflows.import_bundle(state, EXAMPLES / 'composition' / name)
    concurrency, root = getattr(request, 'param', 4), 'parallel-review'
    if concurrency == 'nested-scopes':
        narrow = tmp_path / 'narrow'
        shutil.copytree(EXAMPLES / 'composition/parallel-review', narrow)
        document = json.loads((narrow / 'workflow.json').read_bytes())
        document['id'] = 'narrow-review'
        document['limits']['concurrency'] = 1
        (narrow / 'workflow.json').write_text(json.dumps(document), encoding='utf-8')
        imported = workflows.import_bundle(state, narrow)
        root_source = tmp_path / 'scoped'
        shutil.copytree(EXAMPLES / 'composition/parallel-review', root_source)
        document = json.loads((root_source / 'workflow.json').read_bytes())
        document['id'] = root = 'scoped-review'
        branch = deepcopy(document['nodes'][0])
        branch.update(id='a', ref={'kind': 'workflow', 'id': 'narrow-review',
                                  'version': '1.0.0', 'digest': imported['digest']})
        sibling = deepcopy(document['nodes'][0])
        sibling['id'] = 'b'
        document['nodes'] = [branch, sibling, {'id': 'gather', 'join': 'all', 'depends_on': ['a', 'b']}]
        (root_source / 'workflow.json').write_text(json.dumps(document), encoding='utf-8')
        workflows.import_bundle(state, root_source)
        concurrency = 2
    manifest = workflows.prepare_manifest(state.root, root, '1.0.0',
        grant(concurrency=concurrency), tmp_path / 'parallel-manifest')
    definition['composition'].update(manifest=manifest['path'], manifest_digest=manifest['digest'],
                                     backend_overrides={}, diversity={'policy': 'allow-same'})
    return state, registration, definition


@pytest.fixture
def parallel_input(parallel_creation, monkeypatch):
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    state, _, definition = parallel_creation
    return tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']


@pytest.mark.skipif(sys.platform != 'linux', reason='Formal native submission requires Linux / WSL2')
def test_parallel_creation_and_unknown_submission_keep_every_original_member(parallel_creation, native_client, monkeypatch):
    pytest.importorskip('temporalio')
    state, registration, definition = parallel_creation
    root = Path(registration['execution']['state_directory'])
    runtime = Path(registration['execution']['installation']) / '.venv'
    if not runtime.exists():
        runtime.symlink_to(sys.prefix, target_is_directory=True)
    preview = tasks.preview(state, 'demo', definition, 1)
    document = preview['files']['task.spec.json']
    members = task_envelopes.review_members(document['composition'])
    assert set(members) == {'root/structure/review', 'root/correctness/review', 'root/test-value/review'}
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    assert created['composition']['runtime_supported'] is True
    shutil.rmtree(Path(definition['composition']['manifest']))
    shutil.rmtree(state.root / 'agent-definitions')
    shutil.rmtree(state.root / 'workflow-definitions')
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'lost-response')
    with pytest.raises(ValueError, match='timed out'):
        tasks.start(state, 'demo', definition['task_id'], 1, created['intent_sha256'])
    original = tasks.submission(state, 'demo', definition['task_id'])
    monkeypatch.setenv('ERGORA_TEST_SUBMISSION_SCENARIO', 'normal')
    resumed = tasks.resume_start(state, 'demo', definition['task_id'], 1, original['intent_sha256'])
    assert resumed['status'] == 'submitted' and resumed['run_id'] == 'original-run'
    assert json.loads((root / 'sdk-fixture/server.json').read_bytes())['spec'] == document


@pytest.mark.parametrize('unsupported', ['partial-join', 'sibling-output', 'root-passthrough', 'nested-passthrough'])
def test_parallel_shape_never_omits_a_required_branch_or_invents_an_unexecuted_input(parallel_creation, tmp_path, unsupported):
    state, _, definition = parallel_creation
    source = tmp_path / 'unsupported'
    shutil.copytree(EXAMPLES / 'composition/parallel-review', source)
    document = json.loads((source / 'workflow.json').read_bytes())
    document['id'] = 'unsupported-review'
    if unsupported == 'partial-join':
        document['nodes'][-1]['depends_on'].remove('test-value')
    elif unsupported == 'sibling-output':
        document['nodes'][1].update(depends_on=['structure'],
            inputs={'task': {'node': 'structure', 'output': 'findings'}})
    elif unsupported == 'root-passthrough':
        document['outputs'] = {'findings': {'input': 'task'}}
    else:
        child = tmp_path / 'passthrough'
        shutil.copytree(EXAMPLES / 'composition/structure-review', child)
        child_document = json.loads((child / 'workflow.json').read_bytes())
        child_document.update(id='passthrough-review', outputs={'findings': {'input': 'task'}})
        (child / 'workflow.json').write_text(json.dumps(child_document), encoding='utf-8')
        imported = workflows.import_bundle(state, child)
        document['nodes'][0]['ref'].update(id='passthrough-review', digest=imported['digest'])
    (source / 'workflow.json').write_text(json.dumps(document), encoding='utf-8')
    workflows.import_bundle(state, source)
    manifest = workflows.prepare_manifest(state.root, 'unsupported-review', '1.0.0', grant(), tmp_path / 'unsupported-manifest')
    definition['composition'].update(manifest=manifest['path'], manifest_digest=manifest['digest'])
    preview = tasks.preview(state, 'demo', definition, 1)
    composition = preview['files']['task.spec.json']['composition']
    assert task_envelopes.summary(preview['files']['task.spec.json'])['runtime_supported'] is False
    with pytest.raises(ValueError, match='covering every|direct root task|output'):
        task_envelopes.review_members(composition)


def test_shared_join_dependencies_require_bounded_traversal(parallel_creation, tmp_path):
    state, _, definition = parallel_creation
    source = tmp_path / 'shared-joins'
    shutil.copytree(EXAMPLES / 'composition/parallel-review', source)
    document = json.loads((source / 'workflow.json').read_bytes())
    document['id'] = 'shared-joins'
    joins = []
    for number in range(24):
        dependencies = (['structure', 'correctness'] if number == 0 else
                        ['structure', 'j0'] if number == 1 else [f'j{number - 2}', f'j{number - 1}'])
        joins.append({'id': f'j{number}', 'join': 'all', 'depends_on': dependencies})
    document.update(nodes=document['nodes'][:2] + joins,
                    outputs={'findings': {'node': joins[-1]['id'], 'output': 'result'}})
    (source / 'workflow.json').write_text(json.dumps(document), encoding='utf-8')
    workflows.import_bundle(state, source)
    manifest = workflows.prepare_manifest(state.root, 'shared-joins', '1.0.0', grant(), tmp_path / 'shared-manifest')
    definition['composition'].update(manifest=manifest['path'], manifest_digest=manifest['digest'])
    composition = tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']['composition']
    calls = 0

    def count(frame, event, argument):
        nonlocal calls
        if event == 'call' and frame.f_code.co_filename == task_envelopes.__file__:
            calls += 1

    previous = sys.getprofile()
    try:
        sys.setprofile(count)
        members = task_envelopes.review_members(composition)
    finally:
        sys.setprofile(previous)
    assert len(members) == 2
    # An externally supplied, small valid DAG must not cause exponential work.
    assert calls <= 10 * (len(joins) + 5)


@pytest.mark.parametrize('parallel_creation', [1, 2, 'nested-scopes'], indirect=True)
def test_parallel_stage_obeys_shared_ancestor_limits_and_keeps_reviewers_out_of_authors(parallel_input, monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio import workflow
    from ergora.reference_workflows import CompositionDevelopmentWorkflow

    monkeypatch.setattr(workflow, 'now', lambda: datetime.now(timezone.utc))
    run = CompositionDevelopmentWorkflow()
    run.admission, run.spec = parallel_input, parallel_input['legacy_spec']
    run.results['work:one'] = {'actor': {'id': 'author', 'session_id': 'author-session'}}
    candidate = run.spec['request']['repository']['starting_sha']
    members = task_envelopes.review_members(parallel_input['composition'])
    limit = next(iter(members.values()))['concurrency_scopes'][0]['limit']
    contexts, receipts = {}, {}

    async def exercise():
        entered, release = asyncio.Queue(), asyncio.Event()
        active = peak = 0

        async def call(name, value, result_type=dict):
            nonlocal active, peak
            if name == 'dev_submit':
                contexts[value['stage']] = value
                return {'context': value}
            assert name == 'dev_poll'
            context = value['context']
            active += 1
            peak = max(peak, active)
            await entered.put(context['stage'])
            try:
                await release.wait()
            finally:
                active -= 1
            receipt = {'schema_version': 1, 'job_id': context['job_id'],
                'job_sha256': task_envelopes.identity(context), 'candidate_sha': candidate, 'state': 'SUCCEEDED',
                'actor': {'id': 'reviewer', 'session_id': context['stage'], 'role': 'reviewer', 'kind': 'agent'},
                'artifacts': [], 'checks': []}
            receipts[context['stage']] = receipt
            return receipt

        run.call = call
        pending = asyncio.create_task(run.stage('review', candidate, dependencies={'verification': {}, 'plan': {}}))
        try:
            for _ in range(limit):
                await asyncio.wait_for(entered.get(), 2)
            assert len(contexts) == limit
            release.set()
            result = await asyncio.wait_for(pending, 2)
        finally:
            release.set()
            pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)
        assert peak == limit and not run.active_stages
        return result

    aggregate = asyncio.run(exercise())
    assert aggregate['kind'] == 'composition-review-aggregate' and aggregate['decision'] == 'approve'
    assert aggregate['candidate_sha'] == candidate and set(aggregate['members']) == members.keys()
    assert 'actor' not in aggregate
    for path, reference in aggregate['members'].items():
        context = contexts['review:' + path]
        assert context['author_ids'] == ['author'] and context['author_sessions'] == ['author-session']
        assert context['admission'] == parallel_input and context['expected_candidate_sha'] == candidate
        assert reference['receipt_sha256'] == task_envelopes.identity(receipts[reference['stage']])


@pytest.mark.parametrize('failure', ['failed-member', 'reused-session', 'cancelled'])
def test_parallel_stage_never_aggregates_incomplete_or_nonindependent_reviews(parallel_input, monkeypatch, failure):
    pytest.importorskip('temporalio')
    from temporalio import workflow
    from dev_platform.workflow import StopWork
    from ergora.reference_workflows import CompositionDevelopmentWorkflow

    monkeypatch.setattr(workflow, 'now', lambda: datetime.now(timezone.utc))
    run = CompositionDevelopmentWorkflow()
    run.admission, run.spec = parallel_input, parallel_input['legacy_spec']
    candidate = run.spec['request']['repository']['starting_sha']

    async def exercise():
        entered = asyncio.Event()

        async def call(name, value, result_type=dict):
            if name == 'dev_submit':
                return {'context': value}
            entered.set()
            if failure == 'cancelled':
                await asyncio.Event().wait()
            context = value['context']
            return {'job_id': context['job_id'], 'job_sha256': task_envelopes.identity(context),
                'candidate_sha': candidate, 'state': 'FAILED' if failure == 'failed-member' else 'SUCCEEDED',
                'actor': {'id': 'reviewer', 'session_id': 'reused', 'role': 'reviewer', 'kind': 'agent'}}

        run.call = call
        pending = asyncio.create_task(run.stage('review', candidate))
        await asyncio.wait_for(entered.wait(), 2)
        if failure == 'cancelled':
            pending.cancel()
        with pytest.raises(asyncio.CancelledError if failure == 'cancelled' else StopWork):
            await pending
        assert 'review' not in run.results and not run.active_stages

    asyncio.run(exercise())
