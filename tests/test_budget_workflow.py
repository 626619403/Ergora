"""Real Temporal scheduling for waits that a stage-local timeout cannot cover.

Set ERGORA_TEST_TEMPORAL_BIN to an installed Temporal CLI. No server is downloaded
and no external service or model is used. Ordinary unit CI does not install it.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

import pytest

pytest.importorskip('temporalio')
pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Budgeted native execution requires Linux/WSL2')

from ergora import reference, reference_budget, task_envelopes, tasks, workflow_definitions
from ergora.reference_inputs import execution_input
from test_task_budget import budget_creation, full_creation, full_graph, work_creation, work_graph
from test_registrations import installation, registration
from test_task_creation import creation_project


def test_poll_reference_preserves_receipt_validation_and_rejects_replaced_material(budget_creation, tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from dev_platform.adapter import publish
    from temporalio.exceptions import ApplicationError

    state, _, definition = budget_creation
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    document = tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json']
    selected = execution_input(document)
    roots = {name: str((tmp_path / name).resolve())
             for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    operations = selected.activities({**roots, 'trusted_receipts': True})
    workflow = selected.workflow_type()()
    workflow.spec, workflow.admission = selected.spec, document

    async def exercise():
        job = await operations.submit(workflow.context('inventory'))
        reference = {key: job[key] for key in ('task_id', 'job_id', 'job_sha256')}
        assert await operations.poll(reference) is None
        receipt = {'schema_version': 1, 'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
            'state': 'FAILED', 'candidate_sha': selected.spec['request']['repository']['starting_sha'],
            'actor': {'id': 'controlled-inspector', 'session_id': job['job_id'], 'role': 'inspector', 'kind': 'agent'},
            'artifacts': [], 'checks': []}
        path = operations.adapter.path('receipts', job['task_id'] + '/' + job['job_id'] + '.json')
        publish(path, receipt)
        assert await operations.poll(reference) == await operations.poll(job) == receipt
        request = operations.adapter.path('requests', job['task_id'] + '/' + job['job_id'] + '.json')
        envelope = json.loads(request.read_bytes())
        envelope['context']['stage'] = 'plan'
        request.write_text(json.dumps(envelope))
        with pytest.raises(ApplicationError, match='Poll reference differs'):
            await operations.poll(reference)

    asyncio.run(exercise())


@pytest.mark.parametrize('case', ['queued', 'owner', 'activity-queue', 'poll-retry',
                                 'native-cancel', 'fencing', 'review-scope', 'poll-history'])
def test_original_workflow_uses_one_deadline_for_real_temporal_waits(budget_creation, full_graph, tmp_path, monkeypatch, case):
    binary = os.environ.get('ERGORA_TEST_TEMPORAL_BIN')
    if not binary:
        pytest.skip('Set ERGORA_TEST_TEMPORAL_BIN for the optional real local Temporal acceptance')
    assert Path(binary).is_file()
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from dev_platform.adapter import publish
    from ergora.reference_worker import _ErgoraPackage
    from ergora.reference_workflows import BudgetedAdapter, BudgetedWorkflow
    from temporalio import activity
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Worker

    state, _, definition = budget_creation
    if case == 'review-scope':
        library, grant, *_ = full_graph
        grant['limits']['concurrency'] = 1
        manifest = workflow_definitions.prepare_manifest(library.root, 'prepared-delivery', '1.0.0', grant,
                                                         tmp_path / 'serial-capacity-manifest')
        definition['composition'].update(manifest=manifest['path'], manifest_digest=manifest['digest'])
    definition['budget'].update(wall_seconds=3 if case == 'activity-queue' else 6 if case == 'poll-retry' else 10,
                                cleanup_seconds=1 if case in ('activity-queue', 'poll-retry') else 2)
    trace = []

    class ControlledAdapter(BudgetedAdapter):
        async def submit(self, context):
            job = await super().submit(context)
            trace.append({'operation': 'submit', 'stage': context['stage'],
                          'at': datetime.now(timezone.utc).isoformat()})
            if case in ('owner', 'native-cancel', 'fencing') or (case == 'review-scope' and not context['stage'].startswith('review:')):
                artifacts = []
                stage = context['stage'].split(':', 1)[0]
                for name in context['spec']['profile']['artifacts_by_stage'][stage]:
                    relative = context['task_id'] + '/' + context['job_id'] + '/' + name + '.txt'
                    content = ('Controlled receipt for ' + context['stage'] + '/' + name).encode()
                    path = self.path('artifacts', relative)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
                    artifacts.append({'name': name, 'path': relative, 'sha256': hashlib.sha256(content).hexdigest()})
                receipt = {'schema_version': 1, 'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
                    'state': 'SUCCEEDED', 'candidate_sha': context['expected_candidate_sha'] or
                        context['spec']['request']['repository']['starting_sha'],
                    'actor': {'id': 'controlled-' + context['stage'], 'session_id': job['job_id'],
                              'role': context['spec']['profile']['roles'][stage],
                              'kind': 'ci' if stage == 'verify' else 'agent'},
                    'artifacts': artifacts, 'checks': [{'id': name, 'status': 'pass', 'artifact': artifacts[0]['name']}
                        for name in context['spec']['profile']['required_checks']] if stage == 'verify' else []}
                self.verify_receipt(job, receipt)
                publish(self.path('receipts', context['task_id'] + '/' + job['job_id'] + '.json'), receipt)
            return job

        async def poll(self, job):
            if case == 'poll-retry' and activity.info().activity_type != 'dev_fence':
                trace.append({'operation': 'poll-retry', 'stage': job['context']['stage'],
                              'attempt': activity.info().attempt, 'at': datetime.now(timezone.utc).isoformat()})
                if activity.info().attempt > 1:
                    await asyncio.sleep(30)
                raise RuntimeError('Controlled retryable poll failure')
            return await super().poll(job)

        async def fence(self, context):
            if case == 'fencing':
                trace.append({'operation': 'fence-start', 'at': datetime.now(timezone.utc).isoformat()})
                await asyncio.sleep(max(0, reference_budget.remaining(self.budget_instance)) + .1)
            return await super().fence(context)

    async def exercise():
        async with await WorkflowEnvironment.start_local(dev_server_existing_path=binary,
                dev_server_database_filename=str(tmp_path / 'temporal.sqlite'), dev_server_log_level='error') as service:
            assert (await asyncio.to_thread(tasks.prepare, state, 'demo', definition, 1))['status'] == 'prepared'
            document = (await asyncio.to_thread(tasks.preview, state, 'demo', definition, 1))['files']['task.spec.json']
            selected = execution_input(document)
            selected.require_submission()
            roots = {name: str((tmp_path / name).resolve())
                     for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
            adapter = ControlledAdapter(selected.adapter({**roots, 'trusted_receipts': True}).config)
            adapter.budget_instance = document['budget']['instance']
            operations = selected.activities({**roots, 'trusted_receipts': True})
            operations.adapter = adapter
            queue = 'budget-acceptance-' + uuid.uuid4().hex
            handle = await selected.start(service.client,
                id='budget-' + uuid.uuid4().hex, task_queue=queue)
            if case == 'queued':
                await asyncio.sleep(max(0, reference_budget.remaining(document['budget']['instance'])) + .1)
            finder = _ErgoraPackage()
            sys.meta_path.insert(0, finder)
            try:
                async with Worker(service.client, task_queue=selected.task_queue(queue), workflows=[selected.workflow_type()],
                        activities=[] if case == 'activity-queue' else operations.registered()):
                    if case in ('owner', 'native-cancel', 'fencing', 'review-scope'):
                        async with asyncio.timeout(6):
                            while (status := await handle.query(BudgetedWorkflow.status))['phase'] != 'AWAITING_PLAN_APPROVAL':
                                await asyncio.sleep(.05)
                        if case == 'native-cancel':
                            await handle.cancel()
                        elif case == 'fencing':
                            await handle.signal(BudgetedWorkflow.request_cancel,
                                {'request_sha256': status['request_sha256'], 'reason': 'Controlled cancellation before cutoff'})
                        elif case == 'review-scope':
                            approval = {'schema_version': 1, 'kind': 'plan-approval',
                                'task_id': status['task_id'], 'request_sha256': status['request_sha256'],
                                'profile_sha256': document['legacy_spec']['profile_sha256'], 'plan_sha256': status['plan_sha256'],
                                'decision': 'approve', 'principal_type': 'human', 'actor_id': 'controlled-maintainer',
                                'role': 'maintainer', 'expires_at': time.time() + 60, 'revoked': False}
                            publish(adapter.path('approvals', 'controlled-approval.json'), approval)
                            await handle.signal(BudgetedWorkflow.approve_plan,
                                {'request_sha256': status['request_sha256'], 'plan_sha256': status['plan_sha256'],
                                 'receipt_id': 'controlled-approval'})
                    outcome = await asyncio.wait_for(handle.result(), 15)
                    history = await handle.fetch_history()
            finally:
                sys.meta_path.remove(finder)
            history_raw = history.to_json()
            (tmp_path / 'history.json').write_text(history_raw)
            (tmp_path / 'trace.json').write_text(json.dumps(trace, indent=2) + '\n')
            (tmp_path / 'outcome.json').write_text(json.dumps(outcome, indent=2) + '\n')
            assert outcome['budget']['sha256'] == document['budget']['instance']['sha256']
            assert outcome['budget']['work_exhausted'] is (case != 'native-cancel')
            assert outcome['status'] != 'REVIEW_READY'
            if case in ('queued', 'activity-queue'):
                assert not trace and not list(adapter.roots['requests'].rglob('*.json'))
            elif case in ('owner', 'native-cancel', 'fencing'):
                assert [row['stage'] for row in trace if row['operation'] == 'submit'] == ['inventory', 'plan']
                assert outcome['status'] == 'BLOCKED' and outcome['fence']['confirmed'] is True
                if case == 'fencing':
                    assert len([row for row in trace if row['operation'] == 'fence-start']) == 1
            elif case == 'review-scope':
                reviews = [row['stage'] for row in trace if row['stage'].startswith('review:')]
                assert len(reviews) == 1 and len(document['composition']['members']) == 3
                assert outcome['status'] == 'CANCEL_UNCONFIRMED' and len(outcome['fence']['unresolved_jobs']) == 1
            elif case == 'poll-history':
                polls = [event.activity_task_scheduled_event_attributes for event in history.events
                         if event.HasField('activity_task_scheduled_event_attributes')
                         and event.activity_task_scheduled_event_attributes.activity_type.name == task_envelopes.WORK_POLL]
                assert polls
                for scheduled in polls:
                    job, = await service.client.data_converter.decode(scheduled.input.payloads, [dict])
                    assert set(job) == {'task_id', 'job_id', 'job_sha256'}
                    envelope = json.loads(adapter.path('requests', job['task_id'] + '/' + job['job_id'] + '.json').read_bytes())
                    assert job['job_sha256'] == task_envelopes.identity(envelope['context'])
                    assert envelope['context']['admission'] == document
                assert outcome['status'] == 'CANCEL_UNCONFIRMED'
            else:
                assert [row['stage'] for row in trace if row['operation'] == 'submit'] == ['inventory']
                attempts = [row['attempt'] for row in trace if row['operation'] == 'poll-retry']
                assert attempts == list(range(1, len(attempts) + 1)) and 1 <= len(attempts) < 3
                assert outcome['status'] == 'CANCEL_UNCONFIRMED'
            names = [event.activity_task_scheduled_event_attributes.activity_type.name
                     for event in history.events if event.HasField('activity_task_scheduled_event_attributes')]
            if case == 'queued':
                assert names == ['dev_fence']
            if case == 'activity-queue':
                assert names == ['dev_validate', 'dev_fence']
                assert outcome['status'] == 'NEEDS_RECONCILIATION'
            return outcome

    asyncio.run(exercise())
