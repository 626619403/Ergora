import asyncio
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from ergora.campaigns import application
from ergora.configuration import projects, registrations
from ergora.interfaces.cli import main
from ergora.storage.state import State
from test_registrations import installation, registration  # noqa: F401


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Linux CI for the Unix local operator entry')


def plan_file(path, expiry, **fields):
    value = {'schema_version': 1, 'goal': 'Keep the fixed baseline', 'acceptance': 'Read the original plan',
             'evidence_format': 'original Temporal History', 'baseline_commit': 'f' * 40,
             'limits': {'expires_at': expiry}, **fields}
    raw = json.dumps(value).encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def campaign_args(state, operation, campaign, *extra):
    return ['--home', str(state.root), 'campaign', operation, 'demo', campaign, *map(str, extra)]


def create_args(state, campaign, path, revision, sha):
    return campaign_args(state, 'create', campaign, path, '--revision', revision, '--plan-sha256', sha, '--confirm')


def files(root):
    return {str(item.relative_to(root)): item.read_bytes() for item in root.rglob('*') if item.is_file()}


def test_static_campaign_failures_leave_no_start_intent(registration, tmp_path, monkeypatch, capsys):
    state, definition = registration
    registrations.register(state, definition, 0)
    path = tmp_path / 'plan.json'
    sha = plan_file(path, int(time.time()) + 180)
    # Static failures are useful even on a source test interpreter without the optional SDK.
    monkeypatch.setattr(application, '_temporal', lambda: None)
    for args, error in (
        (create_args(state, 'test', path, 1, 'a' * 64), 'does not match --plan-sha256'),
        (create_args(state, 'test', path, 2, sha), 'Project revision changed'),
        (create_args(state, 'test', path, 1, sha)[:-1], 'requires --confirm'),
        (create_args(state, 'test', path, 1, sha), 'explicitly bound Temporal scheduler'),
    ):
        assert main(args) == 2
        assert error in capsys.readouterr().err
    projects.bind(state, 'demo', 'scheduler', {'tool': 'temporal', 'address': 'localhost:1',
                                             'namespace': 'default', 'task_queue': 'research'}, 1)
    assert main(create_args(state, 'expired', path, 2, plan_file(path, 1))) == 2
    assert 'expiry has passed' in capsys.readouterr().err
    assert main(create_args(state, 'closed', path, 2, plan_file(path, 1, owner_id='fake'))) == 2
    assert 'complete record-only fields' in capsys.readouterr().err
    assert not (state.root / 'campaigns').exists()
    before = files(state.root)
    assert main(campaign_args(state, 'status', 'test')) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'not_recorded'
    assert files(state.root) == before


def test_campaign_start_sends_one_native_request_without_retry():
    pytest.importorskip('temporalio')
    from temporalio.api.workflowservice.v1 import StartWorkflowExecutionResponse
    from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy
    from temporalio.converter import DataConverter
    from ergora.campaigns import workflow as runtime
    from ergora.campaigns.records import attempt_document, identity

    opening = {'workflow_id': 'ergora-campaign:demo:original', 'task_queue': 'saved-campaign-queue',
               'scheduler': {'namespace': 'saved-namespace'}, 'plan': {'goal': 'Exact original'}}
    attempt = attempt_document(opening, 'ef6f5ea1-b9c1-4918-ac9f-178802fd6aa8')
    run_id = '76b46055-eca1-42e6-9649-0f9adc562720'
    converter = DataConverter.default
    calls = []

    async def start_workflow_execution(request, **options):
        calls.append((request, options))
        return StartWorkflowExecutionResponse(started=True, run_id=run_id, first_execution_run_id=run_id)

    client = SimpleNamespace(namespace='saved-namespace', identity='fixture', data_converter=converter,
                             workflow_service=SimpleNamespace(start_workflow_execution=start_workflow_execution))

    async def exercise():
        assert await runtime.start(client, opening, attempt) == run_id
        (request, options), = calls
        assert options == {'retry': False, 'timeout': runtime.RPC_TIMEOUT}
        assert request.namespace == client.namespace and request.identity == client.identity
        assert request.request_id == attempt['attempt_id'] and request.workflow_id == opening['workflow_id']
        assert request.task_queue.name == opening['task_queue'] and request.workflow_type.name == runtime.WORKFLOW_TYPE
        assert request.workflow_id_conflict_policy == WorkflowIDConflictPolicy.FAIL
        assert request.workflow_id_reuse_policy == WorkflowIDReusePolicy.REJECT_DUPLICATE
        assert not request.HasField('retry_policy') and not request.request_eager_execution
        assert await converter.decode(request.input.payloads) == [opening]
        assert {key: (await converter.decode([payload]))[0] for key, payload in request.memo.fields.items()} == {
            runtime.OPENING_MEMO: identity(opening), runtime.ATTEMPT_MEMO: identity(attempt),
        }

    asyncio.run(exercise())


@pytest.mark.skipif(not os.environ.get('ERGORA_TEST_TEMPORAL_BIN'), reason='Requires the optional local Temporal CLI')
def test_campaign_cli_uses_one_original_start_and_worker_after_scheduler_drift(registration, tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType
    from temporalio.api.workflowservice.v1 import RegisterNamespaceRequest
    from temporalio.client import Client
    from temporalio.service import RPCError, RPCStatusCode
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Replayer
    from google.protobuf.duration_pb2 import Duration
    from ergora.campaigns import workflow as runtime

    state, definition = registration
    registrations.register(state, definition, 0)
    path = tmp_path / 'plan.json'
    db = tmp_path / 'campaign-temporal.sqlite'
    start = runtime.start

    async def cli(args, code=0):
        result = await asyncio.to_thread(subprocess.run, [sys.executable, '-m', 'ergora', *args],
                                         capture_output=True, text=True, timeout=30)
        assert result.returncode == code, result.stderr or result.stdout
        return json.loads(result.stdout) if result.stdout else result.stderr

    async def exercise():
        async with await WorkflowEnvironment.start_local(
            ip='127.0.0.1', ui=False, dev_server_existing_path=os.environ['ERGORA_TEST_TEMPORAL_BIN'],
            dev_server_database_filename=str(db),
        ) as env:
            address = env.client.service_client.config.target_host
            await env.client.workflow_service.register_namespace(RegisterNamespaceRequest(
                namespace='drift', workflow_execution_retention_period=Duration(seconds=86400)))
            binding = {'tool': 'temporal', 'address': address, 'namespace': env.client.namespace,
                       'task_queue': 'first-research-queue'}
            projects.bind(state, 'demo', 'scheduler', binding, 1)
            expiry = int(time.time()) + 24
            sha = plan_file(path, expiry)
            created = await cli(create_args(state, 'original', path, 2, sha))
            assert created['status'] == 'created'
            assert created['scheduler'] == binding and created['task_queue'] != binding['task_queue']
            assert created['mode'] == 'record_only' and created['execution_authorized'] is False
            handle = env.client.get_workflow_handle(created['workflow_id'], run_id=created['run_id'])

            async def worker():
                return await asyncio.create_subprocess_exec(sys.executable, '-m', 'ergora',
                    *campaign_args(state, 'worker', 'original'), stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)

            first = await worker()
            try:
                async with asyncio.timeout(12):
                    while not any(event.event_type == EventType.EVENT_TYPE_TIMER_STARTED
                                  for event in (await handle.fetch_history()).events):
                        assert first.returncode is None
                        await asyncio.sleep(.1)
                first.terminate()
                out, err = await asyncio.wait_for(first.communicate(), 8)
                assert first.returncode == 0, err.decode()
                assert json.loads(out)['worker_status'] == 'interrupted'
            finally:
                if first.returncode is None:
                    first.kill()
                    await first.wait()

            # Lose the actual Start acknowledgement and contemporaneous readback, then change both
            # namespace and queue. Concurrent create attempts must stop at the original lock.
            entered, release = asyncio.Event(), asyncio.Event()
            dispatches = []

            async def lose_start(client, opening, attempt):
                dispatches.append(await start(client, opening, attempt))
                entered.set()
                await release.wait()
                raise RPCError('Controlled loss of the Start reply', RPCStatusCode.UNAVAILABLE, b'')

            async def lookup_unavailable(*args):
                raise ConnectionError

            with monkeypatch.context() as patch:
                patch.setattr(runtime, 'start', lose_start)
                patch.setattr(runtime, 'original', lookup_unavailable)
                control = asyncio.create_task(application.create(state, 'demo', 'ambiguous', path, 2, sha, confirm=True))
                try:
                    await asyncio.wait_for(entered.wait(), 8)
                    concurrent = await cli(create_args(state, 'ambiguous', path, 2, sha), code=2)
                    assert 'ERROR:' in concurrent
                    changed_address = '127.0.0.1:' + address.rsplit(':', 1)[1]
                    if changed_address == address:
                        changed_address = 'localhost:' + address.rsplit(':', 1)[1]
                    projects.bind(state, 'demo', 'scheduler', {**binding, 'address': changed_address,
                                                               'namespace': 'drift',
                                                               'task_queue': 'changed-research-queue'}, 2)
                finally:
                    release.set()
                    unknown = await control
            assert unknown['status'] == 'unknown' and unknown['remote_status'] == 'unavailable'
            assert len(dispatches) == 1
            offline = await cli(campaign_args(state, 'status', 'ambiguous'))
            assert offline['status'] == 'unknown' and offline['scheduler'] == binding
            snapshot = files(state.root)
            observed = await cli(campaign_args(state, 'status', 'ambiguous', '--online'))
            assert observed['run_id'] == dispatches[0] and not observed['result_saved']
            assert files(state.root) == snapshot
            replay = await cli(create_args(state, 'ambiguous', path, 2, sha))
            assert replay['status'] == 'observed' and replay['run_id'] == dispatches[0] and replay['result_saved']
            ambiguous_history = await env.client.get_workflow_handle(replay['workflow_id'],
                                                                      run_id=replay['run_id']).fetch_history()
            assert sum(e.event_type == EventType.EVENT_TYPE_WORKFLOW_EXECUTION_STARTED
                       for e in ambiguous_history.events) == 1
            altered = tmp_path / 'altered.json'
            other = plan_file(altered, expiry, goal='Changed goal')
            assert 'different original plan' in await cli(create_args(state, 'ambiguous', altered, 2, other), code=2)
            copied = tmp_path / 'copied'
            shutil.copytree(state.root, copied)
            assert 'original project, control home or operator' in await cli(
                campaign_args(State(copied, read_only=True), 'worker', 'original'), code=2)
            drift = await Client.connect(address, namespace='drift')
            assert [item.id async for item in drift.list_workflows()] == []

            second = await worker()
            try:
                out, err = await asyncio.wait_for(second.communicate(), 35)
                assert second.returncode == 0, err.decode()
                closed = json.loads(out)
                assert closed['worker_status'] == 'closed' and closed['run_id'] == created['run_id']
                assert closed['workflow_state']['phase'] == 'expired'
                assert closed['workflow_state']['expires_at'] == expiry
                assert first.pid != second.pid
            finally:
                if second.returncode is None:
                    second.kill()
                    await second.wait()
            history = await handle.fetch_history()
            types = [event.event_type for event in history.events]
            for observed in (EventType.EVENT_TYPE_WORKFLOW_EXECUTION_STARTED, EventType.EVENT_TYPE_TIMER_STARTED,
                             EventType.EVENT_TYPE_TIMER_FIRED, EventType.EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED):
                assert types.count(observed) == 1
            assert EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED not in types
            assert EventType.EVENT_TYPE_WORKFLOW_EXECUTION_CONTINUED_AS_NEW not in types
            await Replayer(workflows=[runtime.Campaign], namespace=env.client.namespace).replay_workflow(history)
            before_stop = files(state.root)
            expired = await cli(campaign_args(state, 'stop', 'original', '--confirm'), code=1)
            assert expired['workflow_state']['phase'] == 'expired' and expired['stop']['status'] == 'not_recorded'
            assert files(state.root) == before_stop

            # A post-attempt not-found stays held even when there was no successful send.
            opened_from = int(time.time()) + 90
            sha_next = plan_file(path, opened_from)

            async def unsent(*args):
                raise TimeoutError

            with monkeypatch.context() as patch:
                patch.setattr(runtime, 'start', unsent)
                refused = await application.create(state, 'demo', 'held', path, 3, sha_next, confirm=True)
            assert refused['status'] == 'unknown' and refused['remote_status'] == 'original_not_found'
            held = await cli(create_args(state, 'held', path, 3, sha_next), code=1)
            assert held['remote_status'] == 'original_not_found'
            assert [item.id async for item in drift.list_workflows()] == []

            # An independently pre-existing ID must never be adopted by the product worker.
            foreign = await drift.start_workflow(runtime.Campaign.run, {'fake': True},
                id='ergora-campaign:demo:foreign', task_queue='foreign-queue', execution_timeout=timedelta(seconds=30))
            assert 'dispatch memo differs' in await cli(create_args(state, 'foreign', path, 3, sha_next), code=2)
            await foreign.terminate('Test fixture cleanup')
            late = await cli(campaign_args(state, 'worker', 'ambiguous'))
            assert late['run_id'] == replay['run_id'] and late['worker_status'] == 'closed'
            assert late['workflow_state']['phase'] == 'expired' and late['workflow_state']['expires_at'] == expiry
        ps = await asyncio.to_thread(subprocess.run, ['ps', '-eo', 'args'], capture_output=True, text=True, check=True)
        assert str(db) not in ps.stdout
        snapshot = files(state.root)
        offline = await cli(campaign_args(state, 'status', 'original'))
        unavailable = await cli(campaign_args(state, 'status', 'original', '--online'), code=1)
        assert unavailable['remote_status'] == 'unavailable'
        assert unavailable['run_id'] == offline['run_id'] == created['run_id']
        assert files(state.root) == snapshot

    asyncio.run(exercise())


@pytest.mark.parametrize('valid_ack', (True, False), ids=('matching-receipt', 'mismatched-receipt'))
def test_campaign_stop_sends_one_pinned_native_update_without_retry(valid_ack):
    pytest.importorskip('temporalio')
    from temporalio.api.update.v1 import Outcome, UpdateRef
    from temporalio.api.workflowservice.v1 import UpdateWorkflowExecutionResponse
    from temporalio.converter import DataConverter
    from ergora.campaigns import workflow as runtime
    from ergora.campaigns.records import stop_intent, update_attempt, update_receipt

    opening = {'workflow_id': 'ergora-campaign:demo:plan'}
    intent = stop_intent(opening, 'c' * 64, '76b46055-eca1-42e6-9649-0f9adc562720')
    attempt = update_attempt(intent, 'ergora-campaign-stop:ef6f5ea1-b9c1-4918-ac9f-178802fd6aa8')
    command = {'intent': intent, 'attempt': attempt}
    receipt = update_receipt(intent, attempt, 'accepted')
    converter = DataConverter.default
    calls = []

    async def update_workflow_execution(request, **options):
        calls.append((request, options))
        response = UpdateWorkflowExecutionResponse(stage=runtime.UPDATE_COMPLETED, outcome=Outcome(),
            update_ref=UpdateRef(workflow_execution=request.workflow_execution, update_id=attempt['update_id']))
        observed = receipt if valid_ack else {**receipt, 'attempt_sha256': '0' * 64}
        response.outcome.success.payloads.extend(await converter.encode([observed]))
        return response

    client = SimpleNamespace(namespace='saved-namespace', identity='fixture', data_converter=converter,
        workflow_service=SimpleNamespace(update_workflow_execution=update_workflow_execution))

    async def exercise():
        assert await runtime.send_stop(client, command) == (receipt if valid_ack else None)
        (request, options), = calls
        assert options == {'retry': False, 'timeout': runtime.RPC_TIMEOUT}
        assert request.namespace == client.namespace and request.request.meta.identity == client.identity
        assert request.workflow_execution.workflow_id == intent['workflow_id']
        assert request.workflow_execution.run_id == request.first_execution_run_id == intent['run_id']
        assert request.request.meta.update_id == attempt['update_id'] and request.request.input.name == runtime.STOP_UPDATE
        assert request.wait_policy.lifecycle_stage == runtime.UPDATE_COMPLETED
        assert await converter.decode(request.request.input.args.payloads) == [command]

    asyncio.run(exercise())


@pytest.mark.skipif(not os.environ.get('ERGORA_TEST_TEMPORAL_BIN'), reason='Requires the optional local Temporal CLI')
def test_stop_reconciles_one_exact_update_and_keeps_original_closure(registration, tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType
    from temporalio.service import RPCError, RPCStatusCode
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Replayer
    from ergora.campaigns import workflow as runtime

    from ergora.campaigns.records import CampaignFiles

    state, definition = registration
    registrations.register(state, definition, 0)
    path = tmp_path / 'plan.json'
    db = tmp_path / 'campaign-stop.sqlite'
    send = runtime.send_stop

    async def cli(args, code=0):
        result = await asyncio.to_thread(subprocess.run, [sys.executable, '-m', 'ergora', *args],
                                         capture_output=True, text=True, timeout=24)
        assert result.returncode == code, result.stderr or result.stdout
        return json.loads(result.stdout) if result.stdout else result.stderr

    async def exercise():
        async with await WorkflowEnvironment.start_local(
            ip='127.0.0.1', ui=False, dev_server_existing_path=os.environ['ERGORA_TEST_TEMPORAL_BIN'],
            dev_server_database_filename=str(db),
        ) as session:
            binding = {'tool': 'temporal', 'address': session.client.service_client.config.target_host,
                       'namespace': session.client.namespace, 'task_queue': 'original-binding'}
            projects.bind(state, 'demo', 'scheduler', binding, 1)
            cutoff = int(time.time()) + 120
            sha = plan_file(path, cutoff)
            created = await cli(create_args(state, 'original', path, 2, sha))
            handle = session.client.get_workflow_handle(created['workflow_id'], run_id=created['run_id'])
            before_worker = files(state.root)
            unavailable = await cli(campaign_args(state, 'stop', 'original', '--confirm'), code=1)
            assert unavailable['stop']['status'] == 'not_recorded' and unavailable['stop']['retryable']
            assert unavailable['stop']['remote_status'] == 'worker_unavailable'
            assert unavailable['stop']['update_id'] is None and files(state.root) == before_worker
            assert not any(event.HasField('workflow_execution_update_accepted_event_attributes')
                           for event in (await handle.fetch_history()).events)

            async def worker_for(campaign):
                return await asyncio.create_subprocess_exec(sys.executable, '-m', 'ergora',
                    *campaign_args(state, 'worker', campaign), stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)

            async def wait_for_timer(handle, worker):
                async with asyncio.timeout(12):
                    while not any(event.event_type == EventType.EVENT_TYPE_TIMER_STARTED
                                  for event in (await handle.fetch_history()).events):
                        assert worker.returncode is None
                        await asyncio.sleep(.1)

            async def must_not_send(*args):
                raise AssertionError('A stop attempt may only be read back')

            worker = await worker_for('original')
            try:
                await wait_for_timer(handle, worker)
                projects.bind(state, 'demo', 'scheduler', {'tool': 'manual'}, 2)
                previous = files(state.root)
                assert 'requires explicit --confirm' in await cli(campaign_args(state, 'stop', 'original'), code=2)
                copied = tmp_path / 'copied'
                shutil.copytree(state.root, copied)
                assert 'original project, control home or operator' in await cli(
                    campaign_args(State(copied, read_only=True), 'stop', 'original', '--confirm'), code=2)
                assert files(state.root) == previous
                sent = []

                async def lose_reply(client, command):
                    sent.append(await send(client, command))
                    raise RPCError('Controlled loss after exact stop Update', RPCStatusCode.UNAVAILABLE, b'')

                async def temporarily_unavailable(*args):
                    raise RPCError('Controlled loss of stop History readback', RPCStatusCode.UNAVAILABLE, b'')

                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_stop', lose_reply)
                    patch.setattr(runtime, 'read_stop', temporarily_unavailable)
                    unknown = await application.stop(state, 'demo', 'original', confirm=True)
                receipt, = sent
                assert receipt['decision'] == 'accepted'
                assert unknown['stop']['status'] == 'unknown' and unknown['stop']['remote_status'] == 'unavailable'
                assert not unknown['stop']['result_saved'] and unknown.get('workflow_state') is None
                out, err = await asyncio.wait_for(worker.communicate(), 12)
                assert worker.returncode == 0, err.decode()
                completed = json.loads(out)
                assert completed['workflow_state']['phase'] == 'stopped' and completed['run_id'] == created['run_id']
                assert completed['workflow_state']['expires_at'] == cutoff
                before = files(state.root)
                offline = await cli(campaign_args(state, 'status', 'original'))
                assert offline['stop']['status'] == 'unknown' and offline.get('workflow_state') is None
                observed = await cli(campaign_args(state, 'status', 'original', '--online'))
                assert observed['stop']['receipt'] == receipt and not observed['stop']['result_saved']
                assert observed['workflow_state'] == completed['workflow_state'] and files(state.root) == before

                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_stop', must_not_send)
                    stored = await application.stop(state, 'demo', 'original', confirm=True)
                    assert stored['stop']['receipt'] == receipt and stored['stop']['result_saved']
                after = files(state.root)
                repeated = await cli(campaign_args(state, 'stop', 'original', '--confirm'))
                assert repeated['stop'] == stored['stop'] and files(state.root) == after
                assert repeated['scheduler'] == binding

                # The start snapshot can predate the now-published stop chain.
                opening, _, _ = CampaignFiles(state.root, 'demo', 'original').load()
                with monkeypatch.context() as patch:
                    patch.setattr(CampaignFiles, 'load', lambda _: (opening, None, None))
                    prepared = await application.status(state, 'demo', 'original', online=True)
                assert prepared['status'] == 'prepared' and prepared['stop']['status'] == 'not_recorded'

                # The first local stop snapshot can predate the now-closed original Run.
                original_stop_records = CampaignFiles.load_stop
                observations = []

                def load_while_stopping(selected, *args):
                    observations.append(selected.directory)
                    return (None, None, None) if len(observations) == 1 else original_stop_records(selected, *args)

                with monkeypatch.context() as patch:
                    patch.setattr(CampaignFiles, 'load_stop', load_while_stopping)
                    closed = await application.worker(state, 'demo', 'original')
                assert len(observations) == 2 and closed['worker_status'] == 'already_closed'
                assert closed['workflow_state'] == completed['workflow_state'] and files(state.root) == after
                history = await handle.fetch_history()
                event_types = [event.event_type for event in history.events]
                for kind in (EventType.EVENT_TYPE_WORKFLOW_EXECUTION_STARTED, EventType.EVENT_TYPE_TIMER_STARTED,
                             EventType.EVENT_TYPE_TIMER_CANCELED, EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED,
                             EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_COMPLETED,
                             EventType.EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED):
                    assert event_types.count(kind) == 1
                assert event_types.index(EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED) < event_types.index(
                    EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_COMPLETED) < event_types.index(
                    EventType.EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED)
                assert EventType.EVENT_TYPE_TIMER_FIRED not in event_types
                assert EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED not in event_types
                assert EventType.EVENT_TYPE_WORKFLOW_EXECUTION_CONTINUED_AS_NEW not in event_types
                await Replayer(workflows=[runtime.Campaign], namespace=session.client.namespace).replay_workflow(history)
            finally:
                if worker.returncode is None:
                    worker.kill()
                    await worker.wait()

            projects.bind(state, 'demo', 'scheduler', binding, 3)
            pending = await cli(create_args(state, 'held', path, 4, sha))
            pending_handle = session.client.get_workflow_handle(pending['workflow_id'], run_id=pending['run_id'])

            async def lose_before_send(*args):
                raise TimeoutError

            worker = await worker_for('held')
            try:
                await wait_for_timer(pending_handle, worker)
                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_stop', lose_before_send)
                    held = await application.stop(state, 'demo', 'held', confirm=True)
                    assert held['stop']['status'] == 'unknown' and held['stop']['remote_status'] == 'not_found'
                    assert not held['stop']['retryable']
                before = files(state.root)
                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_stop', must_not_send)
                    still_held = await application.stop(state, 'demo', 'held', confirm=True)
                    assert still_held['stop'] == held['stop'] and files(state.root) == before
                history = await pending_handle.fetch_history()
                assert not any(event.HasField('workflow_execution_update_accepted_event_attributes')
                               for event in history.events)
            finally:
                if worker.returncode is None:
                    worker.kill()
                    await worker.wait()
                await pending_handle.terminate('Isolated held-update fixture cleanup')
        ps = await asyncio.to_thread(subprocess.run, ['ps', '-eo', 'args'], capture_output=True, text=True, check=True)
        assert str(db) not in ps.stdout

    asyncio.run(exercise())


@pytest.mark.parametrize(('kind', 'refused'), [('custom', False), ('ignored', True)])
def test_campaign_observation_restores_term_and_wakeup_fd(tmp_path, monkeypatch, kind, refused):
    state = State(tmp_path / 'control')

    async def observe(*args, **kwargs):
        if refused:
            raise ValueError('Controlled original observation refusal')
        return {'status': 'observed'}

    def prior_term(*_):
        raise AssertionError('This control does not deliver SIGTERM')

    monkeypatch.setattr(application, 'observe_check', observe)
    handler = prior_term if kind == 'custom' else signal.SIG_IGN
    read_fd, write_fd = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
    previous_handler = signal.signal(signal.SIGTERM, handler)
    previous_fd = signal.set_wakeup_fd(write_fd)
    try:
        assert main(campaign_args(state, 'observe-check', 'plan', 'check', '--confirm')) == (2 if refused else 0)
        actual_handler = signal.getsignal(signal.SIGTERM)
        actual_fd = signal.set_wakeup_fd(-1)
        assert (actual_handler, actual_fd) == (handler, write_fd)
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
        signal.set_wakeup_fd(previous_fd)
        os.close(read_fd)
        os.close(write_fd)


@pytest.mark.parametrize('interrupted', [False, True])
def test_campaign_worker_preserves_caller_signal_settings(monkeypatch, interrupted):
    pytest.importorskip('temporalio')
    from ergora.campaigns import workflow as runtime

    def prior_term(*_):
        raise AssertionError('The Worker should handle SIGTERM while running')

    class Worker:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            if interrupted:
                asyncio.get_running_loop().call_soon(os.kill, os.getpid(), signal.SIGTERM)

        async def __aexit__(self, *exc):
            pass

    async def result(*, follow_runs):
        if interrupted:
            await asyncio.Event().wait()

    monkeypatch.setattr(runtime, 'Worker', Worker)
    handler = signal.SIG_IGN if interrupted else prior_term
    read_fd, write_fd = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
    previous_handler = signal.signal(signal.SIGTERM, handler)
    previous_fd = signal.set_wakeup_fd(write_fd)
    opening = {'plan': {'limits': {'expires_at': time.time() + 1}}, 'task_queue': 'original'}
    try:
        assert asyncio.run(runtime.run_worker(None, SimpleNamespace(result=result), opening, None, None)) == (
            'interrupted' if interrupted else 'closed')
        actual_handler = signal.getsignal(signal.SIGTERM)
        actual_fd = signal.set_wakeup_fd(-1)
        assert (actual_handler, actual_fd) == (handler, write_fd)
        if interrupted:
            assert os.read(read_fd, 1) == bytes([signal.SIGTERM])
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
        signal.set_wakeup_fd(previous_fd)
        os.close(read_fd)
        os.close(write_fd)


@pytest.mark.parametrize('mode', ['deadline', 'stop', 'cancel', 'terminate'])
def test_campaign_native_observation_reaps_reader_tree(registration, tmp_path, mode):
    from ergora.runtime import processes

    state, definition = registration
    installation = tmp_path / 'controlled-installation'
    shutil.copytree(definition['execution']['installation'], installation, ignore=shutil.ignore_patterns('.venv'))
    definition['execution']['installation'] = str(installation)
    registrations.register(state, definition, 0)
    marker = tmp_path / 'native-reader.json'
    python = installation / '.venv/bin/python'
    python.parent.mkdir(parents=True)
    python.write_text(f"""#!{sys.executable}
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from ergora.runtime.processes import identity

child = subprocess.Popen([sys.executable, '-I', '-S', '-c', 'import time; time.sleep(50)'])
marker = Path({str(marker)!r})
pending = marker.with_suffix('.pending')
pending.write_text(json.dumps([identity(os.getpid()), identity(child.pid)]))
pending.replace(marker)
time.sleep(50)
""", encoding='utf-8')
    python.chmod(0o700)
    source = {'operation_id': 'private-proof', 'job_sha256': 'a' * 64, 'pending': True}
    stopped = threading.Event()

    async def exercise():
        if mode == 'terminate':
            program = """
import asyncio
import sys
import time
from pathlib import Path
from ergora.campaigns import application
from ergora.interfaces.cli import _campaign_check_observation
from ergora.storage.state import State
state = State(Path(sys.argv[1]), read_only=True)
source = {'operation_id': 'private-proof', 'job_sha256': 'a' * 64, 'pending': True}
asyncio.run(_campaign_check_observation(application._read_original_check(state, 'demo', source,
    time.time() + 20, lambda: False)))
"""
            reader = await asyncio.create_subprocess_exec(sys.executable, '-c', program, str(state.root),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        else:
            expires = time.time() + (3 if mode == 'deadline' else 20)
            read_state = State(state.root, read_only=True)
            reader = asyncio.create_task(application._read_original_check(read_state, 'demo', source, expires, stopped.is_set))
        try:
            async with asyncio.timeout(6):
                while not marker.is_file():
                    await asyncio.sleep(.02)
            original = json.loads(marker.read_bytes())
            assert len(original) == 2 and all(processes.identity(item['pid']) == item for item in original)
            if mode == 'terminate':
                reader.terminate()
                _, stderr = await asyncio.wait_for(reader.communicate(), 5)
                assert reader.returncode == 143, stderr.decode()
            elif mode == 'cancel':
                reader.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await reader
            else:
                if mode == 'stop':
                    stopped.set()
                detail = 'reached its deadline' if mode == 'deadline' else 'was cancelled'
                with pytest.raises(ValueError, match=detail):
                    await asyncio.wait_for(reader, 5)
            for item in original:
                try:
                    assert processes.identity(item['pid']) != item
                except (OSError, ValueError):
                    pass
        finally:
            if mode == 'terminate' and reader.returncode is None:
                reader.terminate()
                await asyncio.wait_for(reader.communicate(), 8)
            elif mode != 'terminate' and not reader.done():
                reader.cancel()
                await asyncio.gather(reader, return_exceptions=True)

    asyncio.run(exercise())


def test_campaign_check_native_send_is_bounded_by_the_original_cutoff(monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.api.workflowservice.v1 import UpdateWorkflowExecutionResponse
    from temporalio.converter import DataConverter
    from ergora.campaigns import workflow as runtime
    from ergora.campaigns.records import check_intent, update_attempt

    opening = {'workflow_id': 'ergora-campaign:demo:plan'}
    intent = check_intent(opening, 'c' * 64, '76b46055-eca1-42e6-9649-0f9adc562720', 'task', 'd' * 64)
    attempt = update_attempt(intent, 'ergora-campaign-check:ef6f5ea1-b9c1-4918-ac9f-178802fd6aa8')
    command = {'intent': intent, 'attempt': attempt}
    calls = []
    now = 99
    monkeypatch.setattr(runtime, 'time', SimpleNamespace(time=lambda: now))

    async def update_workflow_execution(request, **options):
        calls.append((request, options))
        return UpdateWorkflowExecutionResponse()

    client = SimpleNamespace(namespace='private', identity='fixture', data_converter=DataConverter.default,
        workflow_service=SimpleNamespace(update_workflow_execution=update_workflow_execution))

    async def exercise():
        nonlocal now
        assert await runtime.send_check(client, command, expires_at=100) is None
        assert calls[0][1]['retry'] is False and calls[0][1]['timeout'].total_seconds() == 1
        now = 100
        assert await runtime.send_check(client, command, expires_at=100) is None
        assert len(calls) == 1

    asyncio.run(exercise())


def test_campaign_fixed_task_plan_checks_exact_dag_and_source():
    from ergora.campaigns.records import FIXED_TASK_SOURCE, validate_fixed_tasks

    source = dict.fromkeys(FIXED_TASK_SOURCE, 'a' * 64)
    source.update(project_revision=7, candidate_sha='a' * 40, operation_id='check',
                  job_id='check-' + 'a' * 40 + '-' + 'b' * 24)
    first = {'task_id': 'first', 'depends_on': [], 'source': source}
    second = {'task_id': 'second', 'depends_on': ['first'], 'source': source}
    validate_fixed_tasks([second, first])
    with pytest.raises(ValueError, match='cycle'):
        validate_fixed_tasks([{**first, 'depends_on': ['second']}, second])
    with pytest.raises(ValueError, match='absent'):
        validate_fixed_tasks([second])
    with pytest.raises(ValueError, match='unique'):
        validate_fixed_tasks([first, first])
    with pytest.raises(ValueError, match='exact original'):
        validate_fixed_tasks([{**first, 'source': {**source, 'project_revision': True}}])

    pending = {key: value for key, value in source.items() if key not in ('receipt_sha256', 'fixed_results_sha256')}
    validate_fixed_tasks([{**first, 'source': {**pending, 'pending': True}}])
    with pytest.raises(ValueError, match='exact original'):
        validate_fixed_tasks([{**first, 'source': {**source, 'pending': True}}])
    with pytest.raises(ValueError, match='exact original'):
        validate_fixed_tasks([{**first, 'source': {**pending, 'pending': 1}}])


def test_readback_guard_dispatch_uses_the_validated_registration_snapshot(registration, tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    from copy import deepcopy
    from ergora.campaigns.readback import _guard
    from ergora.campaigns.records import (CampaignFiles, FIXED_TASK_LOCATOR, attempt_document, check_intent,
                                         check_receipt, identity, project_selection, read_plan, readback_grant,
                                         readback_id, result_document, update_attempt)
    from ergora.development import native
    from ergora.runtime import processes

    state, definition = registration
    registrations.register(state, definition, 0)
    bound = projects.bind(state, 'demo', 'scheduler', {'tool': 'temporal', 'address': '127.0.0.1:1',
                          'namespace': 'default', 'task_queue': 'private-test'}, 1)
    source = dict.fromkeys(FIXED_TASK_LOCATOR, 'a' * 64)
    source.update(project_revision=bound['revision'], candidate_sha='b' * 40, operation_id='check',
                  pending=True, job_id='check-' + 'a' * 40 + '-' + 'b' * 24)
    now = int(time.time())
    task = {'task_id': 'wait', 'depends_on': [], 'source': source,
            'readback': {'due_at': now - 1, 'deadline_at': now + 60}}
    path = tmp_path / 'plan.json'
    sha = plan_file(path, now + 90, tasks=[task])
    plan = read_plan(path, sha)
    files = CampaignFiles(state.root, 'demo', 'readback-snapshot')
    files.ensure_directory()
    opening = application._opening(files, bound['revision'], plan, sha,
                                   project_selection(state, bound, bound['revision']))
    run_id = 'ef6f5ea1-b9c1-4918-ac9f-178802fd6aa8'
    attempt = attempt_document(opening, '4f2f29c3-5e22-446e-a6b4-21febdc545dc')
    intent = check_intent(opening, identity(attempt), run_id, 'wait', 'c' * 64, job={'status': 'queued'})
    waiting = {'intent': intent, 'attempt': update_attempt(intent,
               'ergora-campaign-check:76b46055-eca1-42e6-9649-0f9adc562720')}
    grant = readback_grant(opening, run_id, task, check_receipt(waiting))
    files.write('start-intent', opening)
    files.write('start-attempt', attempt)
    files.write('start-result', result_document(opening, attempt, run_id))
    files.write('wait-check-wait', waiting)
    files.write('readback-attempt', {'grant': grant, 'activity_id': readback_id(grant),
                                     'worker': processes.identity(os.getppid())})

    changed = deepcopy(bound)
    changed['revision'] += 1
    changed_execution = changed['registration']['definition']['execution']
    changed_execution['config_directory'] = str(tmp_path / 'changed-config')
    changed_execution['state_directory'] = str(tmp_path / 'changed-state')
    reads, dispatched = [], []

    def concurrent_registration(*args):
        reads.append(args[1])
        return bound if len(reads) == 1 else changed

    def capture(project, home, operation, payload, **kwargs):
        dispatched.append((project, home, operation, payload))
        raise ValueError('controlled boundary before native launch')

    monkeypatch.setattr(State, 'project', concurrent_registration)
    monkeypatch.setattr(native, 'task_fixed_candidate_check', capture)
    with pytest.raises(ValueError, match='controlled boundary before native launch'):
        _guard(state.root, 'demo', files.campaign)
    assert reads == ['demo']
    assert dispatched == [(bound, state.root, 'status-fixed-check', {'operation_id': 'check',
                           'job_sha256': source['job_sha256'], 'verify_pending': True})]
    assert not (files.directory / 'readback-result.json').exists()


@pytest.mark.parametrize('publication, fail_drain', [
    ('written', False), ('link', False), ('directory-sync', False), ('link', True),
], ids=['written', 'failed-link', 'failed-directory-sync', 'failed-link-and-drain'])
@pytest.mark.parametrize('acknowledged', [False, True], ids=['before-ack', 'after-ack'])
def test_campaign_readback_reaps_guard_after_repeated_cancellation(tmp_path, monkeypatch, acknowledged,
                                                                  publication, fail_drain):
    pytest.importorskip('temporalio')
    from dataclasses import replace
    import errno
    from temporalio.testing import ActivityEnvironment
    from ergora.campaigns import records
    from ergora.campaigns.readback import FixedCheckReadback
    from ergora.campaigns.records import (CampaignFiles, attempt_document, check_intent, check_receipt, identity,
                                         readback_grant, readback_id, update_attempt)
    from ergora.runtime import processes

    owner = CampaignFiles(State(tmp_path).root, 'demo', 'readback-cancel')
    owner.ensure_directory()
    now = int(time.time())
    task = {'task_id': 'wait', 'source': {'pending': True},
            'readback': {'due_at': now - 1, 'deadline_at': now + 30}}
    opening = {'workflow_id': 'ergora-campaign:demo:readback-cancel',
               'plan': {'limits': {'expires_at': now + 30}, 'tasks': [task]}}
    start = attempt_document(opening, '4f2f29c3-5e22-446e-a6b4-21febdc545dc')
    run = 'ef6f5ea1-b9c1-4918-ac9f-178802fd6aa8'
    intent = check_intent(opening, identity(start), run, task['task_id'], 'a' * 64, job={'status': 'queued'})
    waiting = {'intent': intent, 'attempt': update_attempt(intent,
               'ergora-campaign-check:76b46055-eca1-42e6-9649-0f9adc562720')}
    owner.write('wait-check-wait', waiting)
    grant = readback_grant(opening, run, task, check_receipt(waiting))
    activity_id = readback_id(grant)
    spawn = asyncio.create_subprocess_exec
    cancel_path = owner.directory / 'readback-cancel.json'
    write_error = None
    failures = []
    if publication != 'written':
        write_error = OSError(errno.EIO, f'Controlled readback cancellation {publication} failure')

        def fail_publication():
            failures.append(write_error)
            raise write_error

        if publication == 'link':
            link = os.link

            def link_record(source, destination):
                if destination == cancel_path:
                    fail_publication()
                return link(source, destination)

            monkeypatch.setattr(os, 'link', link_record)
        else:
            sync_directory = records._sync_directory

            def sync_record_directory(path):
                if path == owner.directory and cancel_path.exists():
                    fail_publication()
                return sync_directory(path)

            monkeypatch.setattr(records, '_sync_directory', sync_record_directory)
    drain_error = OSError(errno.EIO, 'Controlled guard wait failure after exit') if fail_drain else None

    async def exercise():
        spawned, acknowledge, heartbeat = asyncio.Event(), asyncio.Event(), asyncio.Event()
        child = running = wait_for_exit = None
        tearing_down = False

        async def start_guard(*args, **options):
            nonlocal child, wait_for_exit
            assert args == (sys.executable, '-P', '-m', 'ergora.campaigns.readback', str(owner.home),
                            owner.project, owner.campaign)
            assert options['start_new_session']
            child = await spawn(sys.executable, '-I', '-S', '-c',
                                'import sys\nprint("ready", flush=True)\nsys.stdin.read()',
                                **{**options, 'stdin': asyncio.subprocess.PIPE, 'stdout': asyncio.subprocess.PIPE})
            wait_for_exit = child.wait
            if drain_error is not None:
                async def wait_with_error():
                    returncode = await wait_for_exit()
                    if not tearing_down:
                        raise drain_error
                    return returncode

                monkeypatch.setattr(child, 'wait', wait_with_error)
            if tearing_down:
                child.stdin.close()
            spawned.set()
            await acknowledge.wait()
            return child

        async def read():
            nonlocal running
            running = asyncio.current_task()
            return await FixedCheckReadback(owner, opening, start, run).read(grant)

        monkeypatch.setattr(asyncio, 'create_subprocess_exec', start_guard)
        env = ActivityEnvironment()
        env.info = replace(env.info, workflow_id=opening['workflow_id'], workflow_run_id=run, activity_id=activity_id)
        env.on_heartbeat = lambda *_: heartbeat.set()
        activity = asyncio.create_task(env.run(read))
        try:
            async with asyncio.timeout(10):
                await spawned.wait()
                assert await child.stdout.readline() == b'ready\n'
                if acknowledged:
                    acknowledge.set()
                    await heartbeat.wait()
                assert owner._read('readback-attempt') == {
                    'grant': grant, 'activity_id': activity_id, 'worker': processes.identity(os.getpid()),
                }
                assert running.cancel()
                await asyncio.sleep(0)
                expected = None if publication == 'link' else {'activity_id': activity_id}
                assert owner._read('readback-cancel') == expected
                assert child.returncode is None
                assert not running.done(), 'Activity released its running guard after cancellation publication failed'
                assert running.cancel()
                await asyncio.sleep(0)
                assert child.returncode is None
                assert not running.done(), 'Activity released its running guard before reaping it'
                assert failures == ([write_error] if write_error is not None else [])

                acknowledge.set()
                child.stdin.close()
                error_type = asyncio.CancelledError if write_error is None else OSError
                with pytest.raises(error_type) as failure:
                    await activity
                if write_error is not None:
                    assert failure.value is write_error
                    assert failure.value.__cause__ is drain_error
                assert child.returncode == 0
                assert owner._read('readback-cancel') == expected
                assert owner._read('readback-result') is None
        finally:
            tearing_down = True
            acknowledge.set()
            if child is not None and child.returncode is None:
                child.stdin.close()
                await wait_for_exit()
            await asyncio.gather(activity, return_exceptions=True)

    asyncio.run(exercise())


def test_campaign_one_pending_readback_window_is_frozen():
    from ergora.campaigns.records import FIXED_TASK_LOCATOR, validate_plan

    source = dict.fromkeys(FIXED_TASK_LOCATOR, 'a' * 64)
    source.update(project_revision=7, candidate_sha='b' * 40, operation_id='check', pending=True,
                  job_id='check-' + 'a' * 40 + '-' + 'b' * 24)
    task = {'task_id': 'wait', 'depends_on': [], 'source': source, 'readback': {'due_at': 99, 'deadline_at': 100}}
    plan = {'schema_version': 1, 'goal': 'Bound one read', 'acceptance': 'Read original evidence',
            'baseline_commit': 'c' * 40, 'evidence_format': 'fixed-check', 'limits': {'expires_at': 100}, 'tasks': [task]}
    validate_plan(plan)
    with pytest.raises(ValueError, match='one original readback window'):
        validate_plan({**plan, 'tasks': [task, {**task, 'task_id': 'other'}]})
    with pytest.raises(ValueError, match='original expiry'):
        validate_plan({**plan, 'limits': {'expires_at': 99}})
    with pytest.raises(ValueError, match='one original readback window'):
        validate_plan({**plan, 'tasks': [{**task, 'readback': {'due_at': 100, 'deadline_at': 100}}]})
    pinned = {key: value for key, value in source.items() if key != 'pending'}
    pinned.update(receipt_sha256='d' * 64, fixed_results_sha256='e' * 64)
    with pytest.raises(ValueError, match='explicitly pending'):
        validate_plan({**plan, 'tasks': [{**task, 'source': pinned}]})
    recipient = {'session_id': 'root', 'parent_run_id': 'parent', 'intent_id': 'next',
                 'prompt': 'Use the original evidence', 'timeout_seconds': 60}
    validate_plan({**plan, 'tasks': [{**task, 'recipient': recipient}]})
    with pytest.raises(ValueError, match='selected original timed readback'):
        validate_plan({**plan, 'tasks': [{key: value for key, value in task.items() if key != 'readback'} | {'recipient': recipient}]})
    for change in ({'timeout_seconds': True}, {'intent_id': '../other'}, {'prompt': ' '}):
        with pytest.raises(ValueError, match='exact session, parent, intent, prompt and bounded timeout'):
            validate_plan({**plan, 'tasks': [{**task, 'recipient': {**recipient, **change}}]})


@pytest.mark.parametrize('kind', ['completed', 'lost', 'changed', 'duplicate', 'untimed', 'skewed',
                                 'unstarted', 'foreign-terminal', 'out-of-order', 'duplicate-terminal'])
def test_recipient_history_retains_the_original_wake_and_unknown_delivery(kind):
    pytest.importorskip('temporalio')
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.converter import DataConverter
    from ergora.campaigns.workflow import _read_recipient_history

    async def exercise():
        converter = DataConverter.default
        intent = {'wake_id': 'codex-recipient:fixed-controlled-intent'}
        ready = HistoryEvent(event_id=18)
        schedule = HistoryEvent(event_id=22)
        attrs = schedule.activity_task_scheduled_event_attributes
        attrs.activity_id = intent['wake_id']
        attrs.task_queue.name = 'original-queue'
        attrs.retry_policy.maximum_attempts = 1
        values = {**intent, 'changed': True} if kind == 'changed' else intent
        attrs.input.payloads.extend(await converter.encode([values]))
        started = HistoryEvent(event_id=23)
        started.activity_task_started_event_attributes.scheduled_event_id = 22
        started.activity_task_started_event_attributes.attempt = 1
        ending = HistoryEvent(event_id=24)
        if kind != 'untimed':
            ready.event_time.seconds = 4
            ready.event_time.nanos = 90
            schedule.event_time.seconds = 5
            schedule.event_time.nanos = 100
            started.event_time.seconds = 4 if kind == 'skewed' else 5
            started.event_time.nanos = 120
            ending.event_time.seconds = 6
            ending.event_time.nanos = 140
        unknown_delivery = kind in ('lost', 'unstarted', 'foreign-terminal', 'out-of-order', 'duplicate-terminal')
        if unknown_delivery:
            timed_out = ending.activity_task_timed_out_event_attributes
            timed_out.scheduled_event_id = 22
            timed_out.started_event_id = {
                'lost': 23, 'unstarted': 0, 'foreign-terminal': 19, 'out-of-order': 23, 'duplicate-terminal': 0}[kind]
        elif kind == 'duplicate':
            ending.activity_task_scheduled_event_attributes.CopyFrom(attrs)
        else:
            completed = ending.activity_task_completed_event_attributes
            completed.scheduled_event_id = 22
            completed.started_event_id = 23
            completed.result.payloads.extend(await converter.encode([{'status': 'observed', 'native_run_id': 'original'}]))
        events = {
            'unstarted': [schedule, ending], 'out-of-order': [schedule, ending, started],
            'duplicate-terminal': [schedule, ending, ending],
        }.get(kind, [schedule, started, ending])
        args = (converter, events, {'task_queue': 'original-queue'}, intent, ready)
        if kind in ('changed', 'duplicate'):
            with pytest.raises(ValueError, match='original wake intent|second delivery'):
                await _read_recipient_history(*args)
        else:
            result = await _read_recipient_history(*args)
            assert result['intent'] == intent and result['scheduled_event_id'] == 22 and result['completed_event_id'] == 24
            assert result['status'] == ('unknown' if unknown_delivery else 'observed')
            timing = result['timing']
            assert timing['clock'] == 'temporal_history'
            assert timing['intervals_ns']['scheduled_to_worker_started'] == (
                None if kind in ('untimed', 'skewed', 'unstarted', 'duplicate-terminal') else 20)
            assert timing['intervals_ns']['ready_to_scheduled'] == (None if kind == 'untimed' else 1_000_000_010)
            if kind in ('unstarted', 'foreign-terminal', 'out-of-order', 'duplicate-terminal'):
                assert timing['intervals_ns']['worker_started_to_delivery_terminal'] is None
                assert ('delivery_terminal' in timing['events']) is (kind == 'unstarted')
            if kind != 'untimed':
                assert timing['events']['scheduled'] == {'event_id': 22, 'seconds': 5, 'nanos': 100}
            else:
                assert not timing['events']

    asyncio.run(exercise())


def test_recipient_gate_obeys_the_same_native_cutoff_during_campaign_lock_contention(tmp_path, monkeypatch):
    from ergora.campaigns.recipient_gate import RecipientBlocked, RecipientGate
    from ergora.runtime import budget_clock
    from ergora.storage.state import file_lock

    lock = tmp_path / 'campaign.lock'
    gate = RecipientGate.__new__(RecipientGate)
    gate.files = SimpleNamespace(lock=lock)
    monkeypatch.setattr(gate, 'blocker', lambda: None)
    monkeypatch.setattr(gate, 'remaining', lambda: 120)
    saved_clock = {'original': True}
    allowances = iter((0.5, 0))

    def original_remaining(clock, timeout):
        assert clock is saved_clock and timeout == 1
        return next(allowances)

    monkeypatch.setattr(budget_clock, 'remaining', original_remaining)
    with file_lock(lock, blocking=False):
        with pytest.raises(RecipientBlocked, match='native_turn_expired'):
            with gate.admission(native_clock=saved_clock, native_timeout=1):
                pytest.fail('A contended launch cannot enter after its native turn cutoff')


def test_recipient_write_open_breaks_the_lease_and_kills_its_original_gate(tmp_path):
    import select

    installed = tmp_path / 'codex'
    approved = b'approved original executable bytes'
    installed.write_bytes(approved)
    metadata = installed.stat()
    binding = {'payload_sha256': hashlib.sha256(approved).hexdigest(), 'payload_executable': str(installed),
               'device': metadata.st_dev, 'inode': metadata.st_ino, 'size': len(approved)}
    helper = '''
import json, sys
from ergora.campaigns.recipient_gate import RecipientGate
gate = RecipientGate.__new__(RecipientGate)
gate.binding = json.loads(sys.argv[1])
gate.require_open = lambda **kwargs: None
with gate.leased_payload({}, 1):
    print('leased exact bytes', flush=True)
    sys.stdin.read()
'''
    child = subprocess.Popen([sys.executable, '-P', '-c', helper, json.dumps(binding)], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert select.select([child.stdout], [], [], 10)[0] and child.stdout.readline() == b'leased exact bytes\n'
        try:
            changed = os.open(installed, os.O_WRONLY | os.O_NONBLOCK)
        except BlockingIOError:
            pass
        else:
            os.close(changed)
        assert child.wait(timeout=10) == -signal.SIGKILL
        with installed.open('ab') as changed:
            changed.write(b'different same-inode bytes')
        assert installed.stat().st_ino == metadata.st_ino and installed.read_bytes() != approved
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=10)


@pytest.mark.parametrize('dispatch', ['unrecorded', 'incomplete'])
def test_recipient_status_retains_a_proven_blocker_and_separates_partial_publication(monkeypatch, dispatch):
    from ergora.agents import runs
    from ergora.campaigns import recipient_gate

    recipient = {'session_id': 'session', 'parent_run_id': 'parent', 'intent_id': 'original'}
    native = runs._continuation_run_id(recipient['session_id'], recipient['intent_id'])
    intent = {'wake_id': 'original-wake'}
    saved = {'native_run_id': native, 'intent': intent}
    opening = {'plan': {'tasks': [{'recipient': recipient, 'readback': {}}]}}
    files = SimpleNamespace(project='demo', _read=lambda _: saved)
    monkeypatch.setattr(recipient_gate, 'RecipientGate', lambda *args: SimpleNamespace(intent=intent))
    monkeypatch.setattr(runs, 'continuation_receipt', lambda *args: {'run_id': native, 'dispatch': dispatch, 'run': None})
    prior = {'intent': intent, 'status': 'blocked', 'outcome': {'native_run_id': native, 'reason': 'session_slot_timeout'}}
    output = application._recipient_status(None, files, opening, {'started': True}, None,
                                           {'readback_completion': {'recipient': prior}})['recipient']
    assert output['native_receipt']['dispatch'] == dispatch
    if dispatch == 'unrecorded':
        assert output['status'] == 'blocked' and output['reason'] == 'session_slot_timeout'
    else:
        assert output['status'] == 'unknown' and 'reason' not in output


@pytest.mark.parametrize('outcome', ['passing', 'unrelated', 'pending', 'unaccepted', 'changed-grant',
                                     'history-unavailable', 'service-unavailable', 'no-timer',
                                     'changed-command', 'wrong-acceptance', 'changed-receipt', 'accepted-only',
                                     'offline', 'completed-failure', 'duplicate-id'])
def test_status_recovers_original_task_history_without_worker(registration, tmp_path, monkeypatch, outcome):
    pytest.importorskip('temporalio')
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.converter import DataConverter
    from temporalio.service import RPCError, RPCStatusCode
    from ergora.campaigns import workflow as runtime
    from ergora.campaigns.records import (CampaignFiles, FIXED_TASK_LOCATOR, attempt_document, check_intent,
                                         check_receipt, identity, project_selection, read_plan, readback_grant,
                                         readback_id, result_document, update_attempt)

    state, definition = registration
    registrations.register(state, definition, 0)
    project = projects.bind(state, 'demo', 'scheduler', {'tool': 'temporal', 'address': '127.0.0.1:1',
                            'namespace': 'default', 'task_queue': 'readback-proof'}, 1)
    revision = project['revision']
    source = dict.fromkeys(FIXED_TASK_LOCATOR, 'a' * 64)
    source.update(project_revision=revision, candidate_sha='b' * 40, operation_id='check',
                  pending=True, job_id='check-' + 'a' * 40 + '-' + 'b' * 24)
    now = int(time.time())
    task = {'task_id': 'wait', 'depends_on': [], 'source': source,
            'readback': {'due_at': now - 1, 'deadline_at': now + 60}}
    if outcome == 'no-timer':
        del task['readback']
    pinned = {key: value for key, value in source.items() if key != 'pending'}
    pinned.update(receipt_sha256='d' * 64, fixed_results_sha256='e' * 64)
    no_attempt = {'task_id': 'no-attempt', 'depends_on': ['wait'], 'source': pinned}
    unresolved = {'task_id': 'unresolved', 'depends_on': [], 'source': pinned}
    path = tmp_path / 'readback-plan.json'
    sha = plan_file(path, now + 90, tasks=[task, no_attempt, unresolved])
    owner = CampaignFiles(state.root, 'demo', 'readback-history')
    owner.ensure_directory()
    run_id = 'ef6f5ea1-b9c1-4918-ac9f-178802fd6aa8'
    opening = application._opening(owner, revision, read_plan(path, sha), sha,
                                   project_selection(state, project, revision))
    attempt = attempt_document(opening, '4f2f29c3-5e22-446e-a6b4-21febdc545dc')
    intent = check_intent(opening, identity(attempt), run_id, 'wait', 'c' * 64, job={'status': 'queued'})
    update_id = 'ergora-campaign-check:76b46055-eca1-42e6-9649-0f9adc562720'
    command = {'intent': intent, 'attempt': update_attempt(intent, update_id)}
    waiting = check_receipt(command)
    terminal_job = {'status': 'succeeded', 'waiting_receipt_sha256': identity(waiting),
                    'receipt_sha256': 'd' * 64, 'fixed_results_sha256': 'e' * 64}
    terminal_intent = check_intent(opening, identity(attempt), run_id, 'wait', 'e' * 64, job=terminal_job)
    terminal_id = 'ergora-campaign-check:1d36d638-cadb-42ec-8be8-7d8aa3a1ea4b'
    terminal_command = {'intent': terminal_intent, 'attempt': update_attempt(terminal_intent, terminal_id)}
    terminal_receipt = check_receipt(terminal_command)
    unresolved_intent = check_intent(opening, identity(attempt), run_id, 'unresolved', 'f' * 64)
    unresolved_id = 'ergora-campaign-check:53038d63-20d9-4580-80f2-2632e6258c99'
    if outcome == 'duplicate-id':
        unresolved_id = terminal_id
    unresolved_command = {'intent': unresolved_intent, 'attempt': update_attempt(unresolved_intent, unresolved_id)}
    owner.write('start-intent', opening)
    owner.write('start-attempt', attempt)
    if outcome not in ('service-unavailable', 'offline'):
        owner.write('start-result', result_document(opening, attempt, run_id))
    owner.write('wait-check-wait', command)
    if outcome != 'unaccepted':
        owner.write('check-wait', terminal_command)
    owner.write('check-unresolved', unresolved_command)
    before = files(state.root)

    async def exercise():
        if outcome in ('offline', 'duplicate-id'):
            def unavailable_sdk():
                pytest.fail('Offline status must not load the Temporal runtime')

            monkeypatch.setattr(application, '_temporal', unavailable_sdk)
            if outcome == 'duplicate-id':
                with pytest.raises(ValueError, match='share an original Update ID'):
                    await application.status(state, 'demo', owner.campaign)
                return
            observed = await application.status(state, 'demo', owner.campaign)
            assert observed['remote_status'] == 'not_requested'
            assert observed['run_id'] is None and 'tasks' not in observed
            assert observed['task_observation_history'] == {
                'wait': {
                    'waiting': {'run_id': run_id, 'update_id': update_id, 'status': 'not_requested', 'receipt': None},
                    'terminal': {'run_id': run_id, 'update_id': terminal_id, 'status': 'not_requested', 'receipt': None},
                },
                'unresolved': {
                    'terminal': {'run_id': run_id, 'update_id': unresolved_id, 'status': 'not_requested', 'receipt': None},
                },
            }
            return
        converter = DataConverter.default
        observation = {key: value for key, value in source.items() if key != 'pending'}
        observation.update(project='demo', status='succeeded', stop_requested=False, cleanup_confirmed=True,
                           receipt_sha256='d' * 64, fixed_results_sha256='e' * 64)
        if outcome == 'pending':
            observation.update(status='queued', cleanup_confirmed=None, receipt_sha256=None, fixed_results_sha256=None)
        async def update_events(command, receipt, event_id):
            update_id = command['attempt']['update_id']
            return [
                HistoryEvent(event_id=event_id, workflow_execution_update_accepted_event_attributes={
                    'protocol_instance_id': update_id, 'accepted_request': {'meta': {'update_id': update_id},
                        'input': {'name': runtime.CHECK_UPDATE, 'args': {'payloads': await converter.encode([command])}}}}),
                HistoryEvent(event_id=event_id + 1, workflow_execution_update_completed_event_attributes={
                    'meta': {'update_id': update_id}, 'accepted_event_id': event_id,
                    'outcome': {'success': {'payloads': await converter.encode([receipt])}}}),
            ]

        events = [] if outcome == 'unaccepted' else await update_events(command, waiting, 2)
        if 'readback' in task:
            grant = readback_grant(opening, run_id, task, waiting)
            activity_id = readback_id(grant)
            activity_result = {'activity_id': activity_id, 'observation': observation, 'reader_cleanup_sha256': 'f' * 64}
            scheduled_grant = {**grant, 'deadline_at': now + 61} if outcome == 'changed-grant' else grant
            events.extend([
                HistoryEvent(event_id=4, activity_task_scheduled_event_attributes={
                    'activity_id': activity_id, 'activity_type': {'name': runtime.READBACK_ACTIVITY},
                    'task_queue': {'name': opening['task_queue']}, 'retry_policy': {'maximum_attempts': 1},
                    'input': {'payloads': await converter.encode([scheduled_grant])}}),
                HistoryEvent(event_id=5, activity_task_started_event_attributes={'scheduled_event_id': 4, 'attempt': 1}),
                HistoryEvent(event_id=6, activity_task_completed_event_attributes={
                    'scheduled_event_id': 99 if outcome == 'unrelated' else 4, 'started_event_id': 5,
                    'result': {'payloads': await converter.encode([activity_result])}}),
            ])
        if outcome != 'unaccepted':
            accepted, completed = await update_events(terminal_command, terminal_receipt, 7)
            if outcome == 'changed-command':
                request = accepted.workflow_execution_update_accepted_event_attributes.accepted_request
                request.input.args.payloads[0].data = (await converter.encode([command]))[0].data
            if outcome == 'wrong-acceptance':
                completed.workflow_execution_update_completed_event_attributes.accepted_event_id = 2
            if outcome == 'changed-receipt':
                result = completed.workflow_execution_update_completed_event_attributes.outcome.success
                result.payloads[0].data = (await converter.encode([waiting]))[0].data
            if outcome == 'completed-failure':
                result = completed.workflow_execution_update_completed_event_attributes.outcome
                result.failure.application_failure_info.non_retryable = True
            events.append(accepted)
            if outcome != 'accepted-only':
                events.append(completed)
        history_reads = 0

        async def history(**_):
            nonlocal history_reads
            history_reads += 1
            for event in events:
                yield event
            if outcome == 'history-unavailable':
                raise RPCError('Controlled incomplete History', RPCStatusCode.UNAVAILABLE, b'')

        async def query(*args, **kwargs):
            raise RPCError('Controlled unavailable Worker', RPCStatusCode.UNAVAILABLE, b'')

        async def connect(original_opening):
            assert original_opening == opening
            if outcome == 'service-unavailable':
                raise ConnectionError('Controlled unavailable service')
            return SimpleNamespace(data_converter=converter, namespace='default')

        async def original(client, original_opening, original_attempt, pinned_run):
            assert (original_opening, original_attempt, pinned_run) == (opening, attempt, run_id)
            handle = SimpleNamespace(id=opening['workflow_id'], run_id=run_id, query=query, fetch_history_events=history)
            return handle, SimpleNamespace(status=runtime.WorkflowExecutionStatus.RUNNING, run_id=run_id)

        monkeypatch.setattr(runtime, 'connect', connect)
        monkeypatch.setattr(runtime, 'original', original)
        refusals = {'changed-grant': 'Activity differs from its original grant',
                    'changed-command': 'changed or duplicate Update',
                    'wrong-acceptance': 'completion does not bind its original accepted Update',
                    'changed-receipt': 'receipt differs from its exact original Update'}
        if outcome in refusals:
            with pytest.raises(ValueError, match=refusals[outcome]):
                await application.status(state, 'demo', owner.campaign, online=True)
            return
        observed = await application.status(state, 'demo', owner.campaign, online=True)
        assert observed['workflow_state_status'] == ('not_observed' if outcome == 'service-unavailable' else 'unavailable')
        assert 'tasks' not in observed
        assert history_reads == (0 if outcome == 'service-unavailable' else 1)
        readable = outcome not in ('history-unavailable', 'service-unavailable')
        unresolved_status = 'unresolved' if readable else 'unavailable'
        observations = observed['task_observation_history']
        assert set(observations) == {'wait', 'unresolved'}
        assert observations['unresolved'] == {
            'terminal': {'run_id': run_id, 'update_id': unresolved_id, 'status': unresolved_status, 'receipt': None},
        }
        if readable and outcome != 'unaccepted':
            assert observations['wait']['waiting'] == {
                'run_id': run_id, 'update_id': update_id, 'status': 'verified',
                'receipt': waiting, 'accepted_event_id': 2, 'completed_event_id': 3,
            }
            terminal = {'run_id': run_id, 'update_id': terminal_id, 'status': unresolved_status, 'receipt': None}
            if outcome == 'completed-failure':
                terminal.update(status='failed', accepted_event_id=7, completed_event_id=8)
            elif outcome != 'accepted-only':
                terminal.update(status='verified', receipt=terminal_receipt, accepted_event_id=7, completed_event_id=8)
            assert observations['wait']['terminal'] == terminal
        else:
            assert observations['wait']['waiting'] == {
                'run_id': run_id, 'update_id': update_id, 'status': unresolved_status, 'receipt': None,
            }
        if outcome in ('passing', 'accepted-only', 'completed-failure'):
            assert observed['readback_completion'] == {
                'task_id': 'wait', 'activity_id': activity_id, 'waiting_receipt_sha256': identity(waiting),
                'scheduled_event_id': 4, 'completed_event_id': 6, 'receipt_sha256': 'd' * 64,
                'fixed_results_sha256': 'e' * 64, 'observation_sha256': identity(observation),
                'reader_cleanup_sha256': 'f' * 64,
            }
        else:
            assert 'readback_completion' not in observed

    asyncio.run(exercise())
    assert files(state.root) == before


def test_pending_task_retains_exact_stage_receipts():
    from ergora.campaigns.records import check_intent, check_receipt, fixed_task_state, identity, update_attempt

    task = {'task_id': 'wait', 'depends_on': [], 'source': {'pending': True}}
    dependent = {'task_id': 'next', 'depends_on': ['wait'], 'source': {'pending': True}}
    opening = {'workflow_id': 'ergora-campaign:demo:original', 'plan': {'tasks': [task, dependent]}}
    run = '76b46055-eca1-42e6-9649-0f9adc562720'
    start = 'a' * 64

    def receipt(job, update):
        intent = check_intent(opening, start, run, 'wait', 'b' * 64, job=job)
        return check_receipt({'intent': intent, 'attempt': update_attempt(intent, 'ergora-campaign-check:' + update)})

    pending = receipt({'status': 'queued'}, 'ef6f5ea1-b9c1-4918-ac9f-178802fd6aa8')
    waits = {'wait': pending}
    waiting = fixed_task_state(opening, start, run, {}, waits)
    assert waiting['wait']['status'] == 'waiting_job' and waiting['wait']['waiting_receipt'] == pending
    assert waiting['next']['status'] == 'waiting_dependencies'
    terminal = {'status': 'succeeded', 'receipt_sha256': 'c' * 64, 'fixed_results_sha256': 'd' * 64}
    completed_id = '4f2f29c3-5e22-446e-a6b4-21febdc545dc'
    result = receipt({**terminal, 'waiting_receipt_sha256': identity(pending)}, completed_id)
    complete = fixed_task_state(opening, start, run, {'wait': result}, waits)
    assert complete['wait']['status'] == 'observed' and complete['wait']['waiting_receipt'] == pending
    assert complete['next']['status'] == 'ready'
    direct = receipt(terminal, completed_id)
    assert fixed_task_state(opening, start, run, {'wait': direct})['wait']['waiting_receipt'] is None
    with pytest.raises(ValueError, match='original waiting receipt'):
        fixed_task_state(opening, start, run, {'wait': direct}, waits)


@pytest.mark.skipif(not os.environ.get('ERGORA_TEST_TEMPORAL_BIN'), reason='Requires the optional local Temporal CLI')
def test_frozen_tasks_observe_only_the_original_passing_fixed_check(tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    pytest.importorskip('mcp')
    from temporalio.api.enums.v1 import EventType
    from temporalio.service import RPCError, RPCStatusCode
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Replayer
    from ergora.campaigns import workflow as runtime
    from ergora.campaigns.records import CampaignFiles, FIXED_TASK_SOURCE, identity
    from ergora.development import application as underlying

    private = tmp_path / 'reference'
    private.mkdir()
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    launch = subprocess.run([sys.executable, str(fixture), str(private), 'large-change', 'command',
                             'composition-work-materials-fixed-candidate-check'],
                            capture_output=True, text=True, timeout=210)
    assert launch.returncode == 0, launch.stderr
    reference = json.loads(launch.stdout)
    if reference.get('skip'):
        pytest.skip(reference['skip'])
    independent = reference['independent_check']
    evidence = independent['passing_receipt']
    stopped = independent['stop']
    state = State(private / 'control', read_only=True)
    project = state.project('demo')
    request_root = private / 'runtime/requests/fixed-candidate-check'
    assert len(list(request_root.rglob('*.json'))) == 2 and independent['outer_cleanup_confirmed']
    assert all(Path(value).is_relative_to(private) for value in project['registration']['definition']['execution'].values())
    original = files(private / 'runtime')
    selected = {key: evidence[key] for key in FIXED_TASK_SOURCE}
    cancelled = {**selected, **{key: stopped[key] for key in FIXED_TASK_SOURCE if stopped.get(key) is not None}}
    tasks = [
        {'task_id': 'original', 'depends_on': [], 'source': selected},
        {'task_id': 'dependent', 'depends_on': ['original'], 'source': selected},
        {'task_id': 'other-job', 'depends_on': [], 'source': {**selected, 'job_sha256': stopped['job_sha256']}},
        {'task_id': 'missing', 'depends_on': [], 'source': {**selected, 'operation_id': 'missing-check'}},
        {'task_id': 'cancelled', 'depends_on': [], 'source': cancelled},
        {'task_id': 'changed-receipt', 'depends_on': [], 'source': {**selected, 'receipt_sha256': 'f' * 64}},
        {'task_id': 'held', 'depends_on': [], 'source': selected},
        {'task_id': 'sealed', 'depends_on': [], 'source': selected},
    ]
    path = tmp_path / 'plan.json'
    database = tmp_path / 'campaign-check.sqlite'
    send_check = runtime.send_check
    read_state = runtime.runtime_status
    original_lookup = runtime.original

    async def cli(args, code=0, *, driver=None):
        entry = ['-m', 'ergora'] if driver is None else ['-c', *driver]
        result = await asyncio.to_thread(subprocess.run, [sys.executable, *entry, *args],
                                         capture_output=True, text=True, timeout=30)
        assert result.returncode == code, result.stderr or result.stdout
        return json.loads(result.stdout) if result.stdout else result.stderr

    async def exercise():
        async with await WorkflowEnvironment.start_local(
            ip='127.0.0.1', ui=False, dev_server_existing_path=os.environ['ERGORA_TEST_TEMPORAL_BIN'],
            dev_server_database_filename=str(database),
        ) as service:
            binding = {'tool': 'temporal', 'address': service.client.service_client.config.target_host,
                       'namespace': service.client.namespace, 'task_queue': 'fixed-campaign-scheduler'}
            revision = projects.bind(State(state.root), 'demo', 'scheduler', binding, project['revision'])['revision']
            assert revision == evidence['project_revision'] + 1
            sha = plan_file(path, int(time.time()) + 120, tasks=tasks)
            campaign = 'check-plan'
            created = await cli(create_args(state, campaign, path, revision, sha))
            handle = service.client.get_workflow_handle(created['workflow_id'], run_id=created['run_id'])
            worker = await asyncio.create_subprocess_exec(sys.executable, '-m', 'ergora',
                *campaign_args(state, 'worker', campaign), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            try:
                async with asyncio.timeout(12):
                    while not any(event.event_type == EventType.EVENT_TYPE_TIMER_STARTED
                                  for event in (await handle.fetch_history()).events):
                        assert worker.returncode is None
                        await asyncio.sleep(.1)
                observed = await cli(campaign_args(state, 'status', campaign, '--online'))
                assert observed['tasks']['original']['eligible']
                assert observed['tasks']['dependent']['status'] == 'waiting_dependencies'
                before = files(state.root)
                for task_id, refusal in (
                    ('dependent', 'all dependencies'), ('other-job', 'exact original candidate check job'),
                    ('missing', 'No such file'), ('cancelled', 'exact successful original'),
                    ('changed-receipt', 'exact successful original'),
                ):
                    output = await cli(campaign_args(state, 'observe-check', campaign, task_id, '--confirm'), code=2)
                    assert refusal in output, output
                copied = tmp_path / 'foreign-control'
                shutil.copytree(state.root, copied)
                wrong_home = await cli(campaign_args(State(copied, read_only=True), 'observe-check', campaign,
                                                      'original', '--confirm'), code=2)
                assert 'original project, control home or operator' in wrong_home
                assert files(state.root) == before and files(private / 'runtime') == original
                applied = []

                async def drop_result(client, command, *, expires_at):
                    applied.append(await send_check(client, command, expires_at=expires_at))
                    raise RPCError('Controlled loss after accepted fixed-check Update', RPCStatusCode.UNAVAILABLE, b'')

                async def temporarily_unavailable(*args):
                    raise RPCError('Controlled readback loss', RPCStatusCode.UNAVAILABLE, b'')

                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_check', drop_result)
                    patch.setattr(runtime, 'read_check', temporarily_unavailable)
                    unknown = await application.observe_check(state, 'demo', campaign, 'original', confirm=True)
                receipt, = applied
                assert unknown['status'] == 'unknown' and unknown['receipt'] is None
                assert unknown['run_id'] == created['run_id'] and unknown['update_id'] == receipt['update_id']
                assert receipt['observation_sha256'] == identity(evidence)

                after = files(state.root)
                timeline_args = campaign_args(state, 'status', campaign, '--online', '--task-id', 'original')
                timeline = await cli(timeline_args)
                terminal = timeline['task_observation_history']['original']['terminal']
                assert terminal['status'] == 'verified' and terminal['receipt'] == receipt
                assert (terminal['run_id'], terminal['update_id']) == (unknown['run_id'], unknown['update_id'])
                assert terminal['accepted_event_id'] < terminal['completed_event_id']
                assert timeline['task_evidence']['correlation'] == 'matched'
                assert timeline['task_evidence']['native_job'] == evidence
                assert timeline['task_evidence']['native_job']['cleanup_confirmed'] is True
                assert timeline['task_evidence']['native_observation_sha256'] == receipt['observation_sha256']

                drift_driver = '''
import sys
from ergora.interfaces.cli import main

source, update_id = sys.argv[1:3]
del sys.argv[1:3]
if source == 'native':
    from ergora.runtime import action_observations

    original = action_observations.observe

    def read(*args, **kwargs):
        observed = original(*args, **kwargs)
        return {**observed, 'detail': 'Controlled variance in a later native read'}

    action_observations.observe = read
else:
    from temporalio.client import WorkflowHandle

    original = WorkflowHandle.fetch_history_events

    async def history(handle, *args, **kwargs):
        async for event in original(handle, *args, **kwargs):
            if event.HasField('workflow_execution_update_completed_event_attributes'):
                completed = event.workflow_execution_update_completed_event_attributes
                if completed.meta.update_id == update_id:
                    completed.accepted_event_id += 1
            yield event

    WorkflowHandle.fetch_history_events = history
raise SystemExit(main())
'''
                drifted = await cli(timeline_args, code=1, driver=[drift_driver, 'native', receipt['update_id']])
                assert drifted['task_observation_history']['original']['terminal'] == terminal
                native = drifted['task_evidence']
                assert native['native_job'] == {**evidence, 'detail': 'Controlled variance in a later native read'}
                assert native['native_observation_sha256'] == identity(native['native_job'])
                assert native['native_observation_sha256'] != receipt['observation_sha256']
                assert native['correlation'] == 'different_observation'

                drifted = await cli(timeline_args, code=1, driver=[drift_driver, 'history', receipt['update_id']])
                assert drifted['task_observation_history_status'] == 'contradictory'
                assert 'completion does not bind its original accepted Update' in drifted['task_observation_history_error']
                unverified = drifted['task_observation_history']['original']['terminal']
                assert unverified == {'status': 'unavailable', 'receipt': None,
                                      'run_id': unknown['run_id'], 'update_id': unknown['update_id']}
                assert drifted['task_evidence']['native_job'] == evidence
                assert drifted['task_evidence']['correlation'] == 'pending'

                def no_reissue(*args, **kwargs):
                    raise AssertionError('Original observation may only reconcile its saved attempt')

                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_check', no_reissue)
                    patch.setattr(underlying, 'candidate_check_status', no_reissue)
                    replay = await application.observe_check(state, 'demo', campaign, 'original', confirm=True)
                assert replay['receipt'] == receipt and files(state.root) == after
                assert replay['job_project_revision'] == evidence['project_revision']
                assert replay['campaign_project_revision'] == revision
                observed = await cli(campaign_args(state, 'status', campaign, '--online'))
                assert observed['tasks']['original']['receipt'] == receipt
                assert observed['tasks']['dependent']['eligible']

                async def lose_before_send(*args, **kwargs):
                    raise TimeoutError

                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_check', lose_before_send)
                    held = await application.observe_check(state, 'demo', campaign, 'held', confirm=True)
                assert held['status'] == 'unknown' and held['receipt'] is None
                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_check', no_reissue)
                    patch.setattr(underlying, 'candidate_check_status', no_reissue)
                    assert await application.observe_check(state, 'demo', campaign, 'held', confirm=True) == held
                view = await cli(campaign_args(state, 'status', campaign, '--online'))
                assert view['tasks']['held']['attempt_status'] == 'unknown'
                assert view['tasks']['held']['update_id'] == held['update_id'] and not view['tasks']['held']['eligible']
                current = files(state.root)
                pending = await cli(campaign_args(state, 'status', campaign, '--online', '--task-id', 'held'))
                held_terminal = pending['task_observation_history']['held']['terminal']
                assert held_terminal['status'] == 'unresolved' and held_terminal['update_id'] == held['update_id']
                assert pending['task_evidence']['correlation'] == 'pending'
                assert pending['task_evidence']['native_job'] == evidence
                conflict = await cli(campaign_args(state, 'status', campaign, '--task-id', 'changed-receipt'), code=1)
                assert conflict['task_evidence']['correlation'] == 'contradictory'
                assert conflict['task_evidence']['different_fields'] == ['receipt_sha256']
                assert conflict['task_evidence']['native_job'] == evidence
                wrong_job = await cli(campaign_args(state, 'status', campaign, '--task-id', 'other-job'), code=1)
                wrong = wrong_job['task_evidence']
                assert wrong['correlation'] == 'contradictory' and wrong['different_fields'] == ['job_sha256']
                assert wrong['source'] == tasks[2]['source'] and wrong['native_job'] is None
                assert 'Select the exact original candidate check job' in wrong['native_read_error']
                missing = await cli(campaign_args(state, 'status', campaign, '--task-id', 'missing'), code=1)
                assert missing['task_evidence']['correlation'] == 'unavailable'
                assert missing['task_evidence']['native_job'] is None
                assert files(state.root) == current and files(private / 'runtime') == original
                original_write = CampaignFiles.write
                after_seal = False

                def exhaust_window_after_seal(owner, name, value, **kwargs):
                    nonlocal after_seal
                    original_write(owner, name, value, **kwargs)
                    if name == 'check-sealed':
                        after_seal = True

                clock = SimpleNamespace(time=lambda: created['plan']['limits']['expires_at'] if after_seal else time.time(),
                                        monotonic=time.monotonic)
                with monkeypatch.context() as patch:
                    patch.setattr(CampaignFiles, 'write', exhaust_window_after_seal)
                    patch.setattr(application, 'time', clock)
                    patch.setattr(runtime, 'send_check', no_reissue)
                    sealed = await application.observe_check(state, 'demo', campaign, 'sealed', confirm=True)
                assert after_seal and sealed['status'] == 'unknown' and sealed['receipt'] is None
                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_check', no_reissue)
                    patch.setattr(underlying, 'candidate_check_status', no_reissue)
                    assert await application.observe_check(state, 'demo', campaign, 'sealed', confirm=True) == sealed
                before_stop_description = await handle.describe()
                before_stop_query = await handle.query(runtime.Campaign.state)
                stop = await cli(campaign_args(state, 'stop', campaign, '--confirm'))
                assert stop['stop']['receipt']['decision'] == 'accepted'
                output, error = await asyncio.wait_for(worker.communicate(), 12)
                assert worker.returncode == 0, error.decode()
                closed = json.loads(output)
                assert closed['workflow_state']['phase'] == 'stopped'
                assert closed['tasks']['original']['receipt'] == receipt and not closed['tasks']['dependent']['eligible']
                before_cold_read = files(state.root)
                cold = await cli(timeline_args)
                assert cold['task_observation_history']['original']['terminal'] == terminal
                assert cold['task_evidence'] == timeline['task_evidence']
                assert cold['workflow_state']['phase'] == 'stopped' and files(state.root) == before_cold_read

                async def stale_query(*args, **kwargs):
                    return before_stop_query

                async def observe_stale_stop(*args, **kwargs):
                    original_handle, _ = await original_lookup(*args, **kwargs)
                    stale_handle = SimpleNamespace(id=original_handle.id, run_id=original_handle.run_id,
                        fetch_history_events=original_handle.fetch_history_events, query=stale_query)
                    return stale_handle, before_stop_description

                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'original', observe_stale_stop)
                    stale = await application.status(state, 'demo', campaign, online=True)
                assert stale['temporal_status'] == 'RUNNING' and stale['stop']['receipt'] == stop['stop']['receipt']
                assert stale['tasks']['dependent']['status'] == 'ready' and not stale['tasks']['dependent']['eligible']
                replay_closed = await cli(campaign_args(state, 'observe-check', campaign, 'original', '--confirm'))
                assert replay_closed['receipt'] == receipt
                assert 'no longer admits' in await cli(campaign_args(state, 'observe-check', campaign,
                                                                     'dependent', '--confirm'), code=2)
                history = await handle.fetch_history()
                assert sum(event.event_type == EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED
                           for event in history.events) == 2
                assert not any(event.event_type == EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED
                               for event in history.events)
                await Replayer(workflows=[runtime.Campaign], namespace=service.client.namespace).replay_workflow(history)
            finally:
                if worker.returncode is None:
                    worker.kill()
                    await worker.wait()

            cutoff = int(time.time()) + 5
            expired_sha = plan_file(path, cutoff, tasks=tasks[:2])
            await cli(create_args(state, 'expiry', path, revision, expired_sha))
            await asyncio.sleep(max(0, cutoff - time.time() + .05))
            expired = await cli(campaign_args(state, 'worker', 'expiry'))
            assert expired['workflow_state']['phase'] == 'expired' and not expired['tasks']['original']['eligible']
            assert 'no longer admits' in await cli(campaign_args(state, 'observe-check', 'expiry',
                                                                 'original', '--confirm'), code=2)

            async def cutoff_control(late_boundary):
                campaign = 'deadline-' + late_boundary
                cutoff = int(time.time()) + 10
                sha = plan_file(path, cutoff, tasks=tasks[:1])
                created = await cli(create_args(state, campaign, path, revision, sha))
                handle = service.client.get_workflow_handle(created['workflow_id'], run_id=created['run_id'])
                worker = await asyncio.create_subprocess_exec(sys.executable, '-m', 'ergora',
                    *campaign_args(state, 'worker', campaign), stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
                gate = threading.Event()
                writer = None
                samples = 0
                writes = []

                def hold_project_write():
                    with State(state.root).connect() as db:
                        db.execute('BEGIN IMMEDIATE')
                        gate.set()
                        time.sleep(max(0, cutoff - time.time()) + .05)

                async def delayed_state(*args, **kwargs):
                    nonlocal samples, writer
                    view = await read_state(*args, **kwargs)
                    samples += 1
                    if samples == 2:
                        assert view['tasks']['original']['eligible']
                        if late_boundary == 'query':
                            await asyncio.sleep(max(0, cutoff - time.time()) + .05)
                        else:
                            writer = threading.Thread(target=hold_project_write)
                            writer.start()
                            assert gate.wait(3)
                    return view

                async def expect_no_native_update(*args, **kwargs):
                    writes.append(args)
                    raise AssertionError('No native Update may be sent after the original cutoff')

                try:
                    async with asyncio.timeout(8):
                        while not any(event.event_type == EventType.EVENT_TYPE_TIMER_STARTED
                                      for event in (await handle.fetch_history()).events):
                            assert worker.returncode is None
                            await asyncio.sleep(.05)
                    description = await handle.describe()
                    query = await handle.query(runtime.Campaign.state)
                    opening, attempt, _ = CampaignFiles(state.root, 'demo', campaign).load()
                    native_files = files(state.root)
                    with monkeypatch.context() as patch:
                        patch.setattr(runtime, 'runtime_status', delayed_state)
                        patch.setattr(runtime, 'send_check', expect_no_native_update)
                        with pytest.raises(ValueError, match='no longer admits'):
                            await application.observe_check(state, 'demo', campaign, 'original', confirm=True)
                    assert samples == 2 and not writes and files(state.root) == native_files

                    async def pre_expiry_sample(*args, **kwargs):
                        return query

                    stale_handle = SimpleNamespace(query=pre_expiry_sample)
                    stale = await read_state(stale_handle, description, opening, start_attempt_sha256=identity(attempt))
                    assert stale['temporal_status'] == 'RUNNING'
                    assert stale['tasks']['original']['status'] == 'ready' and not stale['tasks']['original']['eligible']
                    stdout, stderr = await asyncio.wait_for(worker.communicate(), 12)
                    assert worker.returncode == 0, stderr.decode()
                    assert json.loads(stdout)['workflow_state']['phase'] == 'expired'
                    history = await handle.fetch_history()
                    assert not any(event.HasField('workflow_execution_update_accepted_event_attributes')
                                   for event in history.events)
                finally:
                    if worker.returncode is None:
                        worker.kill()
                        await worker.wait()
                    if writer is not None:
                        writer.join(3)
                        assert not writer.is_alive()

            await cutoff_control('query')
            await cutoff_control('sqlite')
            assert files(private / 'runtime') == original
        ps = await asyncio.to_thread(subprocess.run, ['ps', '-eo', 'args'], capture_output=True, text=True, check=True)
        assert str(database) not in ps.stdout

    asyncio.run(exercise())


@pytest.mark.skipif(not os.environ.get('ERGORA_TEST_TEMPORAL_BIN'), reason='Requires the optional local Temporal CLI')
def test_rollover_keeps_the_original_wait_and_fences_unverified_successor(registration, tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.client import WorkflowHandle
    from temporalio.service import RPCError, RPCStatusCode
    from temporalio.testing import WorkflowEnvironment

    from ergora.campaigns import records, workflow as runtime

    state, definition = registration
    registrations.register(state, definition, 0)
    campaign = 'rollover'
    plan = tmp_path / 'rollover.json'
    original_fetch = WorkflowHandle.fetch_history_events
    send_rollover = runtime.send_rollover
    sent = []
    observations = []
    outcome = {'status': 'queued', 'stop_requested': False, 'cleanup_confirmed': None,
               'receipt_sha256': None, 'fixed_results_sha256': None}

    async def observe_native(selected, project, source, expires_at, stopped):
        assert selected.root == state.root and project == 'demo' and not stopped()
        observations.append(source)
        return {**source, **outcome, 'project': 'demo'}

    async def lose_committed_reply(client, command, *, expires_at):
        sent.append(command)
        assert (await send_rollover(client, command, expires_at=expires_at))['decision'] == 'committed'
        raise RPCError('Lost original rollover acknowledgement', RPCStatusCode.UNAVAILABLE, b'')

    async def worker_until_ready(client, opening, run_id):
        child = await asyncio.create_subprocess_exec(sys.executable, '-m', 'ergora',
            *campaign_args(state, 'worker', campaign), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        handle = client.get_workflow_handle(opening['workflow_id'], run_id=run_id)
        try:
            async with asyncio.timeout(14):
                while True:
                    assert child.returncode is None
                    if await runtime.stop_supported(handle, opening):
                        return child
                    await asyncio.sleep(.05)
        except BaseException:
            await reap(child)
            raise

    async def reap(child, *, interrupted=True):
        if interrupted and child.returncode is None:
            child.terminate()
        try:
            async with asyncio.timeout(12):
                output, error = await child.communicate()
        finally:
            if child.returncode is None:
                child.kill()
                await child.wait()
        assert child.returncode == 0, error.decode()
        return json.loads(output)

    async def exercise():
        async with await WorkflowEnvironment.start_local(
            ip='127.0.0.1', ui=False, dev_server_existing_path=os.environ['ERGORA_TEST_TEMPORAL_BIN'],
            dev_server_database_filename=str(tmp_path / 'rollover.sqlite'),
        ) as service:
            client = service.client
            scheduler = {'tool': 'temporal', 'address': client.service_client.config.target_host,
                         'namespace': client.namespace, 'task_queue': 'rollover-proof'}
            revised = projects.bind(state, 'demo', 'scheduler', scheduler, state.project('demo')['revision'])
            source = {'operation_id': 'native', 'request_file_sha256': 'a' * 64,
                      'job_sha256': 'b' * 64, 'candidate_sha': 'c' * 40, 'project_revision': revised['revision'],
                      'job_id': 'check-' + 'd' * 40 + '-' + 'e' * 24, 'authorization_sha256': 'f' * 64,
                      'verification_sha256': '1' * 64, 'pending': True}
            task = {'task_id': 'wait', 'depends_on': [], 'source': source}
            cutoff = int(time.time()) + 100
            digest = plan_file(plan, cutoff, tasks=[task], rollover=True)
            created = await application.create(state, 'demo', campaign, plan, revised['revision'], digest, confirm=True)
            first = created['run_id']
            saved = records.CampaignFiles(state.root, 'demo', campaign)
            opening, attempt, original = saved.load()
            first_worker = await worker_until_ready(client, opening, first)
            try:
                waiting = await application.observe_check(state, 'demo', campaign, 'wait', confirm=True)
                assert waiting['status'] == 'waiting_job' and waiting['run_id'] == first

                async def unsupported(*args):
                    return False

                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'rollover_supported', unsupported)
                    with pytest.raises(ValueError, match='Worker does not support rollover'):
                        await application.rollover(state, 'demo', campaign, confirm=True)
                assert not (saved.directory / 'rollover-command.json').exists()
                with monkeypatch.context() as patch:
                    patch.setattr(runtime, 'send_rollover', lose_committed_reply)
                    result = await application.rollover(state, 'demo', campaign, confirm=True)
                async with asyncio.timeout(8):
                    while (result['rollover']['status'] != 'verified'
                           or result['workflow_state_status'] != 'observed'):
                        result = await application.rollover(state, 'demo', campaign, confirm=True)
                        await asyncio.sleep(.05)
                current = result['current_run_id']
                assert current != first and result['run_id'] == first and saved.load()[2] == original
                assert result['workflow_state']['expires_at'] == cutoff
                assert result['tasks']['wait']['waiting_receipt'] == waiting['receipt']
                assert len(sent) == 1
                yes = result['rollover']

                first_handle = client.get_workflow_handle(opening['workflow_id'], run_id=first)
                current_handle = client.get_workflow_handle(opening['workflow_id'], run_id=current)
                before = (await current_handle.fetch_history()).events

                async def altered(handle, *args, **kwargs):
                    async for event in original_fetch(handle, *args, **kwargs):
                        if (handle.run_id == first and event.HasField('workflow_execution_update_completed_event_attributes')
                                and event.workflow_execution_update_completed_event_attributes.meta.update_id == waiting['update_id']):
                            event.workflow_execution_update_completed_event_attributes.accepted_event_id += 1
                        yield event

                command = saved.directory / 'rollover-command.json'
                missing = command.with_suffix('.held')
                command.rename(missing)
                try:
                    with pytest.raises(ValueError, match='lacks its saved'):
                        await application.stop(state, 'demo', campaign, confirm=True)
                finally:
                    missing.rename(command)
                with monkeypatch.context() as patch:
                    patch.setattr(WorkflowHandle, 'fetch_history_events', altered)
                    with pytest.raises(ValueError, match='original accepted Update'):
                        await application.observe_check(state, 'demo', campaign, 'wait', confirm=True)
                assert (await current_handle.fetch_history()).events == before
                assert len(observations) == 1
                assert not (saved.directory / 'stop-attempt.json').exists()
                assert not (saved.directory / 'check-wait.json').exists()
            finally:
                await reap(first_worker)
            replacement = await worker_until_ready(client, opening, current)
            try:
                outcome.update(status='succeeded', cleanup_confirmed=True, receipt_sha256='2' * 64,
                               fixed_results_sha256='3' * 64)
                terminal = await application.observe_check(state, 'demo', campaign, 'wait', confirm=True)
                assert terminal['status'] == 'observed' and terminal['run_id'] == current
                assert terminal['receipt']['job']['waiting_receipt_sha256'] == records.identity(waiting['receipt'])
                # The fixture's typed evidence reader runs only on the write path. The saved decision can be read alone.
                monkeypatch.setattr(application, '_task_evidence', _no_native_timeline)
                stop = await application.stop(state, 'demo', campaign, confirm=True)
                assert stop['stop']['receipt']['decision'] == 'accepted' and stop['stop']['receipt']['run_id'] == current
                view = await application.status(state, 'demo', campaign, online=True, task_id='wait')
                assert view['rollover'] == yes and view['workflow_state']['phase'] == 'stopped'
                stages = view['task_observation_history']['wait']
                assert stages['waiting']['receipt'] == waiting['receipt']
                assert stages['terminal']['receipt'] == terminal['receipt']
                assert len((await first_handle.fetch_history()).events) > 10
            finally:
                await reap(replacement, interrupted=False)

            from temporalio.worker import Worker

            outcome.update(status='queued', cleanup_confirmed=None, receipt_sha256=None, fixed_results_sha256=None)
            for selected, action in (('held-stop', 'stop'), ('held-rollover', 'rollover')):
                new = await application.create(state, 'demo', selected, plan, revised['revision'], digest, confirm=True)
                handle = client.get_workflow_handle(new['workflow_id'], run_id=new['run_id'])
                child_records = records.CampaignFiles(state.root, 'demo', selected)
                async with Worker(client, task_queue=new['task_queue'], workflows=[runtime.Campaign]):
                    await runtime.stop_supported(handle, child_records.load()[0])
                    assert (await application.observe_check(state, 'demo', selected, 'wait',
                                                           confirm=True))['status'] == 'waiting_job'
                    calls = []

                    async def before_send(*args, **options):
                        calls.append((args, options))
                        raise RPCError('Controlled loss before first native send', RPCStatusCode.UNAVAILABLE, b'')

                    operation = getattr(application, action)
                    with monkeypatch.context() as patch:
                        patch.setattr(runtime, 'send_' + action, before_send)
                        await operation(state, 'demo', selected, confirm=True)
                        await operation(state, 'demo', selected, confirm=True)
                    assert len(calls) == 1
                    if action == 'stop':
                        with pytest.raises(ValueError, match='original STOP'):
                            await application.rollover(state, 'demo', selected, confirm=True)
                        assert not (child_records.directory / 'rollover-command.json').exists()
                    else:
                        with pytest.raises(ValueError, match='rollover attempt is unresolved'):
                            await application.stop(state, 'demo', selected, confirm=True)
                        assert not (child_records.directory / 'stop-attempt.json').exists()
                        observed = await application.status(state, 'demo', selected, online=True)
                        offline = await application.status(state, 'demo', selected)
                        assert observed['rollover']['status'] == 'unresolved'
                        assert not observed['tasks']['wait']['eligible']
                        assert offline['rollover'] == {**observed['rollover'], 'status': 'not_requested'}
                    assert (await handle.describe()).status.name == 'RUNNING'
                    await handle.terminate('Owned isolated unresolved-attempt fixture cleanup')

    async def _no_native_timeline(*args):
        return None

    monkeypatch.setattr(application, '_read_original_check', observe_native)
    asyncio.run(exercise())
