"""Advisory opinions retain failed receipts; operational failure still stops work."""

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

pytest.importorskip('temporalio')

from ergora import agent_definitions, reference, task_envelopes, tasks, workflow_definitions as workflows
from test_composition_tasks import composed_creation
from test_task_creation import creation_project
from test_registrations import installation, registration
from test_workflow_definitions import EXAMPLES, grant


@pytest.fixture
def requirements_creation(composed_creation, tmp_path):
    state, registration, definition = composed_creation
    agent_definitions.import_bundle(state, EXAMPLES / 'composition/agents/test-value-reviewer')
    workflows.import_bundle(state, EXAMPLES / 'composition/review-requirements')
    saved = workflows.prepare_manifest(state.root, 'review-requirements', '1.0.0', grant(), tmp_path / 'requirements')
    definition['composition'].update(manifest=saved['path'], manifest_digest=saved['digest'],
                                     backend_overrides={}, diversity={'policy': 'allow-same'})
    return state, registration, definition


@pytest.fixture
def requirements_input(requirements_creation, monkeypatch):
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    state, _, definition = requirements_creation
    return tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']


def opinion_receipt(job, artifacts, decision='request-changes', *, session=None):
    from dev_platform.adapter import publish

    context = job['context']
    digest = hashlib.sha256(b'Validated model result fixture').hexdigest()
    documents = {name: 'Complete findings remain in the original artifact.'
                 for name in context['spec']['profile']['artifacts_by_stage']['review']}
    documents.update({'composition-invocation': {'status': 'succeeded', 'result_sha256': digest},
        'composition-review-decision': {'schema_version': 1, 'kind': 'formal-review-decision',
            'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
            'candidate_sha': context['expected_candidate_sha'], 'decision': decision, 'result_sha256': digest}})
    inventory = []
    for name, value in documents.items():
        relative = job['job_id'] + '/' + name + '.json'
        publish(artifacts / relative, value)
        inventory.append({'name': name, 'path': relative, 'sha256': hashlib.sha256((artifacts / relative).read_bytes()).hexdigest()})
    return {'schema_version': 1, 'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
        'state': 'SUCCEEDED' if decision == 'approve' else 'FAILED',
        'actor': {'id': 'reviewer', 'session_id': session or context['stage'], 'kind': 'agent', 'role': 'reviewer'},
        'candidate_sha': context['expected_candidate_sha'], 'artifacts': inventory,
        'checks': [{'id': 'independent-review', 'status': 'pass' if decision == 'approve' else 'fail', 'artifact': 'review-report'}]}


def test_v3_freezes_requirements_and_uses_a_separate_registered_workflow(requirements_input, requirements_creation):
    from ergora.reference_inputs import execution_input
    from ergora.reference_task_runtime import VerifiedSpecClient
    from temporalio.workflow import _Definition

    state, registration, definition = requirements_creation
    document = requirements_input
    assert document['schema_version'] == 3
    assert {path: member['review_requirement'] for path, member in document['composition']['members'].items()} == {
        'root/structure': 'required', 'root/test-value': 'advisory'}
    preview = tasks.preview(state, 'demo', definition, 1)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    shutil.rmtree(Path(definition['composition']['manifest']))
    shutil.rmtree(state.root / 'workflow-definitions')
    shutil.rmtree(state.root / 'agent-definitions')
    assert tasks.show(state, 'demo', definition['task_id'])['admission_envelope'] == document
    assert tasks.resume_create(state, 'demo', definition['task_id'], 1, created['intent_sha256']) == created
    selected = execution_input(document)
    native = SimpleNamespace(start_workflow=AsyncMock(return_value='original-v3-handle'))
    client = VerifiedSpecClient(native, document)
    assert asyncio.run(client.start_workflow(None, document['legacy_spec'], task_queue='original', id='v3')) == 'original-v3-handle'
    assert native.start_workflow.call_args.args == (selected.entrypoint, document)
    assert native.start_workflow.call_args.kwargs['task_queue'] == 'original.composition-v3'
    assert _Definition.must_from_run_fn(selected.entrypoint).name == 'ErgoraCompositionWorkflowV3'
    assert selected.request_root(Path(registration['execution']['state_directory']) / 'requests').name == 'requests-composition-v3'


@pytest.mark.parametrize('case', ['approve', 'changes', 'operational', 'missing-decision', 'candidate', 'author-session',
    'check', 'invocation', 'cancelled', 'artifact-change', 'version-bool', 'missing-report', 'read-race',
    'result-null', 'result-text'])
@pytest.mark.skipif(sys.platform != 'linux', reason='Native FileAdapter file semantics require Linux/WSL2')
def test_trusted_poll_distinguishes_opinions_from_process_and_contract_failures(requirements_input, tmp_path, monkeypatch, case):
    from dev_platform.adapter import canonical, publish
    from ergora.reference_inputs import execution_input
    from temporalio.exceptions import ApplicationError

    selected = execution_input(requirements_input)
    config = {name: str(tmp_path / name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    activities = selected.activities({**config, 'trusted_receipts': True})
    run = selected.workflow_type()()
    run.spec, run.admission = selected.spec, requirements_input
    run.results['work:a'] = {'actor': {'id': 'author', 'session_id': 'author-session'}}
    context = run.context('review:root/test-value', selected.spec['request']['repository']['starting_sha'])
    job = asyncio.run(activities.submit(context))
    artifacts = Path(config['artifacts'])
    receipt = opinion_receipt(job, artifacts, 'approve' if case == 'approve' else 'request-changes')
    if case in ('operational', 'missing-decision'):
        receipt['artifacts'] = [item for item in receipt['artifacts'] if item['name'] != 'composition-review-decision']
        receipt['state'] = 'FAILED' if case == 'operational' else 'SUCCEEDED'
    elif case == 'candidate':
        receipt['candidate_sha'] = 'f' * 40
    elif case == 'author-session':
        receipt['actor']['session_id'] = 'author-session'
    elif case == 'check':
        receipt['checks'][0]['status'] = 'pass'
    elif case == 'cancelled':
        receipt['state'] = 'CANCELLED'
    elif case == 'missing-report':
        receipt['artifacts'] = [item for item in receipt['artifacts'] if item['name'] != 'review-report']
        receipt['checks'] = []
    elif case in ('invocation', 'version-bool'):
        name = 'composition-invocation' if case == 'invocation' else 'composition-review-decision'
        item = next(item for item in receipt['artifacts'] if item['name'] == name)
        path = artifacts / item['path']
        value = json.loads(path.read_text())
        value.update({'result_sha256': '0' * 64} if case == 'invocation' else {'schema_version': True})
        path.write_bytes(canonical(value) + b'\n')
        item['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif case in ('result-null', 'result-text'):
        for item in receipt['artifacts']:
            if item['name'] not in ('composition-review-decision', 'composition-invocation'):
                continue
            path = artifacts / item['path']
            value = json.loads(path.read_text())
            value['result_sha256'] = None if case == 'result-null' else 'G' * 64
            path.write_bytes(canonical(value) + b'\n')
            item['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif case in ('artifact-change', 'read-race'):
        item = next(item for item in receipt['artifacts'] if item['name'] == 'composition-review-decision')
        path = artifacts / item['path']
        if case == 'artifact-change':
            path.write_text('{}')
        else:
            original = activities.adapter.poll

            async def changed(job):
                result = await original(job)
                path.write_text('{}')
                return result

            monkeypatch.setattr(activities.adapter, 'poll', changed)
    publish(Path(config['receipts']) / context['task_id'] / (context['job_id'] + '.json'), receipt)
    if case in ('approve', 'changes', 'operational'):
        result = asyncio.run(activities.poll(job))
        assert result['receipt'] == receipt
        assert result['review_decision'] == {'approve': 'approve', 'changes': 'request-changes', 'operational': None}[case]
        assert receipt['state'] == ('SUCCEEDED' if case == 'approve' else 'FAILED')
    else:
        detail = {'missing-decision': 'missing its trusted decision', 'candidate': 'candidate mismatch',
            'author-session': 'independent principal', 'check': 'checks differ', 'invocation': 'actual successful model result',
            'cancelled': 'original terminal state', 'artifact-change': 'Artifact bytes do not match',
            'version-bool': 'decision binding mismatch', 'missing-report': 'Missing required review artifacts',
            'read-race': 'artifact changed while reading',
            'result-null': 'Invalid model result digest', 'result-text': 'Invalid model result digest'}[case]
        with pytest.raises(ApplicationError, match=detail) as rejected:
            asyncio.run(activities.poll(job))
        assert rejected.value.type == 'ContractViolation' and rejected.value.non_retryable
    assert not Path(config['requests']).exists()


@pytest.mark.parametrize('case', ['advisory-changes', 'required-changes', 'operational', 'shared-session', 'cancel'])
@pytest.mark.skipif(sys.platform != 'linux', reason='Native FileAdapter file semantics require Linux/WSL2')
def test_v3_workflow_preserves_raw_receipts_and_only_relaxes_valid_advisory_opinions(requirements_input, tmp_path, monkeypatch, case):
    from dev_platform.adapter import publish
    from dev_platform.workflow import StopWork
    from ergora.reference_inputs import execution_input
    from temporalio import workflow

    monkeypatch.setattr(workflow, 'now', lambda: datetime.now(timezone.utc))
    selected = execution_input(requirements_input)
    config = {name: str(tmp_path / name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    activities = selected.activities({**config, 'trusted_receipts': True})
    run = selected.workflow_type()()
    run.spec, run.admission = selected.spec, requirements_input
    candidate = selected.spec['request']['repository']['starting_sha']
    receipts = {}

    async def exercise():
        entered = asyncio.Event()

        async def call(name, value, result_type=dict):
            if name == 'dev_submit':
                return await activities.submit(value)
            assert name == 'dev_poll'
            entered.set()
            if case == 'cancel':
                await asyncio.Event().wait()
            context = value['context']
            path = context['stage'].removeprefix('review:')
            required = path == 'root/structure'
            decision = 'request-changes' if not required or case == 'required-changes' else 'approve'
            receipt = opinion_receipt(value, Path(config['artifacts']), decision,
                                      session='shared' if case == 'shared-session' else None)
            if case == 'operational' and not required:
                receipt['artifacts'] = [item for item in receipt['artifacts'] if item['name'] != 'composition-review-decision']
            receipts[path] = receipt
            publish(Path(config['receipts']) / context['task_id'] / (context['job_id'] + '.json'), receipt)
            return await activities.poll(value)

        run.call = call
        pending = asyncio.create_task(run.stage('review', candidate))
        await asyncio.wait_for(entered.wait(), 2)
        if case == 'cancel':
            pending.cancel()
        if case == 'advisory-changes':
            return await pending
        with pytest.raises(asyncio.CancelledError if case == 'cancel' else StopWork):
            await pending
        assert 'review' not in run.results

    aggregate = asyncio.run(exercise())
    assert not run.active_stages
    if case == 'advisory-changes':
        assert run.cancel_reason is None and aggregate['schema_version'] == 2 and aggregate['decision'] == 'approve'
        assert aggregate['members']['root/test-value']['decision'] == 'request-changes'
        assert receipts['root/test-value']['state'] == 'FAILED'
        for path, receipt in receipts.items():
            assert run.results['review:' + path] == receipt
            job = {'stage': 'review:' + path, 'job_id': receipt['job_id'], 'job_sha256': receipt['job_sha256'],
                   'receipt': receipt, 'receipt_sha256': task_envelopes.identity(receipt)}
            assert task_envelopes.outcome_reference_state({'review': aggregate}, job) == 'matches'


@pytest.mark.parametrize('change', ['requirement', 'graph-version', 'worker-version'])
def test_v3_cannot_change_frozen_requirements_or_be_adopted_by_the_old_worker(requirements_input, change):
    from ergora.reference_workflows import CompositionDevelopmentWorkflow
    from temporalio.exceptions import ApplicationError

    document = deepcopy(requirements_input)
    if change == 'worker-version':
        run = CompositionDevelopmentWorkflow()
        run.call = AsyncMock(side_effect=AssertionError('No activity before exact-version admission'))
        with pytest.raises(ApplicationError, match='requires a v2 formal admission'):
            asyncio.run(run.run(document))
        run.call.assert_not_called()
        return
    if change == 'requirement':
        document['composition']['members']['root/structure']['review_requirement'] = 'advisory'
    else:
        document['schema_version'] = 2
    document['sha256'] = task_envelopes.identity({key: value for key, value in document.items() if key != 'sha256'})
    with pytest.raises(ValueError, match='requirement|member'):
        task_envelopes.unwrap(document)


@pytest.mark.parametrize('decision', ['approve', 'reject', 'mutate'])
@pytest.mark.skipif(sys.platform != 'linux', reason='Formal executor requires Linux / WSL2')
def test_executor_publishes_decision_only_from_the_original_validated_call_and_preserves_recovery(tmp_path, decision):
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command',
        'composition-requirements-' + decision], capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    if decision == 'mutate':
        assert summary == {'receipt_state': 'FAILED', 'review_decision': None,
            'mutation_detected': True, 'trusted_opinion_published': False}
        return
    assert summary == {'decision': 'request-changes' if decision == 'reject' else 'approve',
        'receipt_state': 'FAILED' if decision == 'reject' else 'SUCCEEDED',
        'candidate_bound': True, 'recovery_preserved': True}
