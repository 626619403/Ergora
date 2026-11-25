import asyncio
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
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
    from ergora.campaigns.records import stop_attempt, stop_intent, stop_receipt

    opening = {'workflow_id': 'ergora-campaign:demo:plan'}
    intent = stop_intent(opening, 'c' * 64, '76b46055-eca1-42e6-9649-0f9adc562720')
    attempt = stop_attempt(intent, 'ergora-campaign-stop:ef6f5ea1-b9c1-4918-ac9f-178802fd6aa8')
    command = {'intent': intent, 'attempt': attempt}
    receipt = stop_receipt(intent, attempt, 'accepted')
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
