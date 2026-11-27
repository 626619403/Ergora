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
from test_agents import native_session_case  # noqa: F401
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
    from ergora.campaigns.records import FIXED_TASK_SOURCE, validate_tasks

    source = dict.fromkeys(FIXED_TASK_SOURCE, 'a' * 64)
    source.update(project_revision=7, candidate_sha='a' * 40, operation_id='check',
                  job_id='check-' + 'a' * 40 + '-' + 'b' * 24)
    first = {'task_id': 'first', 'depends_on': [], 'source': source}
    second = {'task_id': 'second', 'depends_on': ['first'], 'source': source}
    validate_tasks([second, first])
    with pytest.raises(ValueError, match='cycle'):
        validate_tasks([{**first, 'depends_on': ['second']}, second])
    with pytest.raises(ValueError, match='absent'):
        validate_tasks([second])
    with pytest.raises(ValueError, match='unique'):
        validate_tasks([first, first])
    with pytest.raises(ValueError, match='exact original'):
        validate_tasks([{**first, 'source': {**source, 'project_revision': True}}])

    pending = {key: value for key, value in source.items() if key not in ('receipt_sha256', 'fixed_results_sha256')}
    validate_tasks([{**first, 'source': {**pending, 'pending': True}}])
    with pytest.raises(ValueError, match='exact original'):
        validate_tasks([{**first, 'source': {**source, 'pending': True}}])
    with pytest.raises(ValueError, match='exact original'):
        validate_tasks([{**first, 'source': {**pending, 'pending': 1}}])


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
    from ergora.campaigns.readback import CampaignReadback
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
            return await CampaignReadback(owner, opening, start, run).read(grant)

        monkeypatch.setattr(asyncio, 'create_subprocess_exec', start_guard)
        env = ActivityEnvironment()
        env.info = replace(env.info, activity_type=records.READBACK_ACTIVITY, workflow_id=opening['workflow_id'],
                           workflow_run_id=run, activity_id=activity_id)
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


def test_campaign_assignment_binds_one_generation_and_two_explicit_tasks():
    from copy import deepcopy

    from ergora.campaigns.records import FIXED_TASK_LOCATOR, assignment_intent, validate_plan

    source = dict.fromkeys(FIXED_TASK_LOCATOR, 'a' * 64)
    source.update(project_revision=7, candidate_sha='b' * 40, operation_id='check', pending=True,
                  job_id='check-' + 'a' * 40 + '-' + 'b' * 24)
    recipient = {'session_id': 'first', 'parent_run_id': 'first', 'intent_id': 'result',
                 'prompt': 'Read the result', 'timeout_seconds': 60}
    waiting = {'task_id': 'wait', 'depends_on': [], 'source': source, 'recipient': recipient,
               'readback': {'due_at': 99, 'deadline_at': 100}}
    independent = {'task_id': 'next', 'recipient': {**recipient, 'session_id': 'second',
                   'parent_run_id': 'second', 'intent_id': 'independent', 'timeout_seconds': 10}}
    assignee = {'role': 'performance-analyst', 'generation': 3}
    plan = {'schema_version': 1, 'goal': 'Hold the original Job', 'acceptance': 'Do independent work',
            'baseline_commit': 'c' * 40, 'evidence_format': 'fixed-check', 'limits': {'expires_at': 100},
            'tasks': [waiting], 'assignment': {'assignee': assignee, 'waiting_task_id': 'wait', 'next_task': independent}}
    validate_plan(plan)
    original = assignment_intent({'workflow_id': 'original', 'plan': plan}, 'run', {'task_id': 'wait'})
    assert original['task_id'] == 'next' and original['source']['waiting_task_id'] == 'wait'
    assert original['expires_at'] == plan['limits']['expires_at']
    for key, values, message in (
        ('assignment', {'waiting_task_id': 'missing'}, 'original selected waiting task'),
        ('assignee', {'generation': True}, 'permission generation'),
        ('next_task', {'task_id': 'wait'}, 'distinct independent task ID'),
        ('recipient', {'session_id': 'first'}, 'separately selected native session'),
        ('recipient', {'timeout_seconds': 0}, 'bounded timeout'),
    ):
        changed = deepcopy(plan)
        node = {'assignment': changed['assignment'], 'assignee': changed['assignment']['assignee'],
                'next_task': changed['assignment']['next_task'],
                'recipient': changed['assignment']['next_task']['recipient']}[key]
        node.update(values)
        with pytest.raises(ValueError, match=message):
            validate_plan(changed)


def test_campaign_assignment_rejects_two_registrations_for_one_native_thread():
    from ergora.campaigns.records import require_assignment_bindings

    role = 'performance-analyst'
    first = {'role': role, 'native_id': '00000000-0000-4000-8000-000000000001',
             'context_digest': 'a'*64, 'payload_sha256': 'b'*64, 'source_executable': '/source',
             'payload_executable': '/payload', 'device': 1, 'inode': 2, 'size': 3}
    second = {**first, 'native_id': '00000000-0000-4000-8000-000000000002'}
    require_assignment_bindings(first, second, role)
    with pytest.raises(ValueError, match='distinct native threads'):
        require_assignment_bindings(first, {**first, 'context_digest': 'c'*64}, role)
    with pytest.raises(ValueError, match='one frozen assignee'):
        require_assignment_bindings(first, {**second, 'role': 'reviewer'}, role)


@pytest.mark.parametrize('decision', ['missing', 'changed', 'accepted'])
def test_campaign_training_assignment_dispatch_uses_one_original_pending_proof(registration, tmp_path, monkeypatch,
                                                                        decision):
    from ergora.campaigns.records import assignment_intent, identity, require_training_assignment_wait, validate_plan

    state, definition = registration
    registrations.register(state, definition, 0)
    projects.bind(state, 'demo', 'scheduler', {'tool': 'temporal', 'address': 'localhost:1',
                                             'namespace': 'default', 'task_queue': 'research'}, 1)
    project = state.project('demo')
    expiry = int(time.time()) + 60
    locator = {'experiment_id': 'alpha', 'workflow_id': 'perf-experiment/alpha', 'run_id': 'original-run',
               'job_id': 'local-perf-alpha', 'native_request_sha256': 'a' * 64, 'attempt_sha256': 'b' * 64}
    first = {'session_id': 'first', 'parent_run_id': 'first', 'intent_id': 'result',
             'prompt': 'Read the result', 'timeout_seconds': 20}
    independent = {'task_id': 'next', 'recipient': {**first, 'session_id': 'second', 'parent_run_id': 'second',
                                                  'intent_id': 'independent'}}
    assignee = {'role': 'performance-analyst', 'generation': 2}
    task = {'task_id': 'wait', 'depends_on': [], 'recipient': first,
            'source': {'kind': 'training_full_result', 'locator': locator, 'wait_for_live': True},
            'readback': {'due_at': expiry - 20, 'deadline_at': expiry}}
    path = tmp_path / 'plan.json'
    digest = plan_file(path, expiry, tasks=[task], assignment={'assignee': assignee, 'waiting_task_id': 'wait',
                                                               'next_task': independent})
    plan = json.loads(path.read_bytes())
    with pytest.raises(ValueError, match='managed full-result live wait'):
        validate_plan({**plan, 'tasks': [{**task, 'source': {key: value for key, value in task['source'].items()
                                                           if key != 'wait_for_live'}}]})
    binding = {'role': assignee['role'], 'native_id': '00000000-0000-4000-8000-000000000001',
               'context_digest': 'a'*64, 'payload_sha256': 'b'*64, 'source_executable': '/source',
               'payload_executable': '/payload', 'device': 1, 'inode': 2, 'size': 3}
    bindings = {'recipient_binding': binding,
                'assignment_binding': {**binding, 'native_id': '00000000-0000-4000-8000-000000000002'}}
    monkeypatch.setattr(application, '_freeze_recipients', lambda *_: bindings)
    checked = []
    receipt = {'status': 'verified_pending', 'project': 'demo', 'project_revision': project['revision'],
               'registration_sha256': project['registration']['sha256'], 'locator': locator,
               'launch_sha256': 'c' * 64, 'acknowledgement_sha256': 'd' * 64}
    starts = []
    run_id = '00000000-0000-4000-8000-000000000003'

    async def verify_pending(_, __, opening, original_task):
        assert original_task == task
        checked.append(opening)
        if decision == 'missing':
            raise ValueError('Original attempt has no acknowledged executor')
        if decision == 'changed' and len(checked) == 2:
            return {**receipt, 'acknowledgement_sha256': 'e' * 64}
        return receipt

    async def connect(opening):
        assert opening['training_wait'] == receipt
        return object()

    async def start(_, opening, attempt):
        assert attempt['opening_sha256'] == identity(opening)
        assert opening['training_wait'] == receipt
        assert assignment_intent(opening, run_id)['source']['waiting_receipt_sha256'] == identity(receipt)
        starts.append(attempt)
        return run_id

    async def original(_, output, opening, attempt, acknowledged, **_options):
        assert opening['training_wait'] == receipt and acknowledged == run_id and attempt == starts[0]
        return {**output, 'run_id': run_id, 'remote_status': 'original_observed'}

    runtime = SimpleNamespace(RPC_SECONDS=2, RPCError=RuntimeError, connect=connect, start=start)
    monkeypatch.setattr(application, '_temporal', lambda: runtime)
    monkeypatch.setattr(application, '_read_training_assignment_wait', verify_pending)
    monkeypatch.setattr(application, '_read_original', original)

    async def create():
        return await application.create(state, 'demo', 'training', path, project['revision'], digest, confirm=True)

    directory = state.root / 'campaigns' / 'demo' / 'training'
    if decision == 'missing':
        with pytest.raises(ValueError, match='no acknowledged executor'):
            asyncio.run(create())
        assert len(checked) == 1 and not directory.exists() and not starts
    elif decision == 'changed':
        with pytest.raises(ValueError, match='pending training proof changed'):
            asyncio.run(create())
        assert len(checked) == 2 and not (directory / 'start-attempt.json').exists() and not starts
    else:
        assert asyncio.run(create())['status'] == 'created'
        assert asyncio.run(create())['status'] == 'observed'
        assert len(checked) == 2 and len(starts) == 1
        opening = json.loads((directory / 'start-intent.json').read_bytes())
        assert opening['training_wait'] == receipt
        for changed in ({'locator': {**locator, 'attempt_sha256': '0' * 64}}, {'project_revision': True},
                        {'launch_sha256': '../foreign'}, {'status': 'succeeded'}):
            with pytest.raises(ValueError, match='exact original pending attempt'):
                require_training_assignment_wait(opening, {**receipt, **changed})


@pytest.mark.parametrize('fault', ['none', 'missing-start', 'other-memo', 'changed-wait'])
def test_training_assignment_history_requires_the_exact_original_started_event(fault):
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.converter import DataConverter
    from ergora.campaigns import records, workflow

    pending = {'status': 'verified_pending', 'project': 'original', 'project_revision': 1,
               'registration_sha256': 'a'*64, 'locator': {'experiment_id': 'alpha'},
               'launch_sha256': 'b'*64, 'acknowledgement_sha256': 'c'*64}
    task = {'task_id': 'wait', 'source': {'kind': 'training_full_result', 'wait_for_live': True,
                                        'locator': pending['locator']},
            'readback': {'due_at': 10, 'deadline_at': 20}, 'recipient': {}}
    plan = {'limits': {'expires_at': 30}, 'tasks': [task],
            'assignment': {'waiting_task_id': 'wait', 'next_task': {'task_id': 'independent'}}}
    opening = {'project': 'original', 'project_revision': 1, 'registration': {'sha256': 'a'*64},
               'workflow_id': 'campaign-original', 'task_queue': 'queue-original', 'scheduler': {'namespace': 'default'},
               'plan': plan, 'training_wait': pending}
    run_id = 'original-run'
    attempt = records.attempt_document(opening, 'original-attempt')
    converter = DataConverter.default

    async def exercise():
        started = HistoryEvent(event_id=1, event_type=EventType.EVENT_TYPE_WORKFLOW_EXECUTION_STARTED)
        attributes = started.workflow_execution_started_event_attributes
        attributes.workflow_type.name = records.WORKFLOW_TYPE
        attributes.task_queue.name = opening['task_queue']
        attributes.first_execution_run_id = attributes.original_execution_run_id = run_id
        attributes.attempt = 1
        snapshot = {**opening, 'training_wait': {**pending, 'launch_sha256': 'd'*64}} if fault == 'changed-wait' else opening
        attributes.input.payloads.extend(await converter.encode([snapshot]))
        for key, value in workflow.memo(opening, attempt).items():
            selected = 'e'*64 if fault == 'other-memo' and key == records.ATTEMPT_MEMO else value
            attributes.memo.fields[key].CopyFrom((await converter.encode([selected]))[0])

        intent = records.assignment_intent(opening, run_id)
        scheduled = HistoryEvent(event_id=3, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED)
        activity = scheduled.activity_task_scheduled_event_attributes
        activity.activity_type.name = records.RECIPIENT_ACTIVITY
        activity.task_queue.name = opening['task_queue']
        activity.activity_id = intent['wake_id']
        activity.retry_policy.maximum_attempts = 1
        activity.input.payloads.extend(await converter.encode([intent]))

        async def history(**_):
            if fault != 'missing-start':
                yield started
            yield scheduled

        client = SimpleNamespace(namespace='default', data_converter=converter)
        handle = SimpleNamespace(id=opening['workflow_id'], run_id=run_id, fetch_history_events=history)
        updates, _, _, _, _, assignment = await workflow.read_task_history(client, handle, opening, (),
                                                                              start_attempt=attempt)
        assert not updates
        if fault == 'none':
            assert assignment['intent'] == intent and assignment['training_wait_started_event_id'] == 1
            assert 'waiting_completed_event_id' not in assignment
        else:
            assert assignment['status'] == 'contradictory' and 'intent' not in assignment

    asyncio.run(exercise())


@pytest.mark.parametrize('history', ('absent', 'contradictory', 'different', 'exact'))
def test_assignment_recipient_requires_its_original_wait_and_schedule_before_reservation(monkeypatch, history):
    pytest.importorskip('temporalio')
    from ergora.campaigns import recipient

    first = {'task_id': 'waiting', 'source': {'pending': True}, 'readback': {}, 'recipient': {}}
    next_task = {'task_id': 'independent'}
    opening = {'plan': {'tasks': [first], 'assignment': {'next_task': next_task}}}
    intent = {'source': {}, 'task_id': 'independent', 'wake_id': 'codex-assignment:original'}
    wait = {'intent': {'task_id': 'waiting'}, 'attempt': {'update_id': 'original-wait'}}
    delivered = []
    files = object()

    def saved_wait(selected, original_opening, start, run_id):
        assert (selected, original_opening, start, run_id) == (files, opening, 'attempt', 'run')
        return wait

    async def read_history(commands, *, independent):
        assert independent and commands == (wait,)
        return {'absent': None, 'contradictory': {'status': 'contradictory'},
                'different': {'intent': {**intent, 'wake_id': 'codex-assignment:another'}},
                'exact': {'intent': intent, 'status': 'scheduled'}}[history]

    worker = recipient.CodexRecipient(files, opening, 'attempt', 'run', read_wake_history=read_history)
    monkeypatch.setattr(recipient, 'assignment_wait', saved_wait)
    monkeypatch.setattr(worker, '_deliver', delivered.append)
    if history == 'exact':
        asyncio.run(worker._deliver_verified(intent))
        assert delivered == [intent]
    else:
        with pytest.raises(ValueError, match='lacks its verified original waiting Update and schedule'):
            asyncio.run(worker._deliver_verified(intent))
        assert not delivered


@pytest.mark.parametrize('kind', ['scheduled', 'started', 'completed', 'lost', 'changed', 'duplicate', 'untimed', 'skewed',
                                 'unstarted', 'foreign-terminal', 'out-of-order', 'duplicate-terminal',
                                 'negative-reuses-start-id', 'wrong-schedule-type', 'wrong-started-type',
                                 'wrong-completion-type', 'start-reuses-schedule-id', 'completion-reuses-start-id',
                                 'foreign-start-schedule', 'foreign-completion-schedule',
                                 'negative-wrong-type', 'negative-foreign-schedule', 'negative-failed',
                                 'negative-failed-before-start', 'negative-canceled', 'negative-untimed'])
def test_recipient_history_retains_the_original_wake_and_unknown_delivery(kind):
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.converter import DataConverter
    from ergora.campaigns.records import RECIPIENT_ACTIVITY
    from ergora.campaigns.workflow import _read_recipient_history

    async def exercise():
        converter = DataConverter.default
        intent = {'wake_id': 'codex-recipient:fixed-controlled-intent'}
        ready = HistoryEvent(event_id=18)
        schedule = HistoryEvent(event_id=22, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED)
        attrs = schedule.activity_task_scheduled_event_attributes
        attrs.activity_id = intent['wake_id']
        attrs.activity_type.name = RECIPIENT_ACTIVITY
        attrs.task_queue.name = 'original-queue'
        attrs.retry_policy.maximum_attempts = 1
        values = {**intent, 'changed': True} if kind == 'changed' else intent
        attrs.input.payloads.extend(await converter.encode([values]))
        started = HistoryEvent(event_id=23, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED)
        started.activity_task_started_event_attributes.scheduled_event_id = 22
        started.activity_task_started_event_attributes.attempt = 1
        ending = HistoryEvent(event_id=24, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED)
        if kind != 'untimed':
            ready.event_time.seconds = 4
            ready.event_time.nanos = 90
            schedule.event_time.seconds = 5
            schedule.event_time.nanos = 100
            started.event_time.seconds = 4 if kind == 'skewed' else 5
            started.event_time.nanos = 120
            ending.event_time.seconds = 6
            ending.event_time.nanos = 140
        unknown_delivery = kind in ('lost', 'unstarted', 'foreign-terminal', 'out-of-order', 'duplicate-terminal',
                                    'negative-reuses-start-id', 'negative-wrong-type', 'negative-foreign-schedule',
                                    'negative-failed', 'negative-failed-before-start', 'negative-canceled',
                                    'negative-untimed')
        if unknown_delivery:
            terminal_kind = {'negative-failed': 'failed', 'negative-failed-before-start': 'failed',
                             'negative-canceled': 'canceled'}.get(kind, 'timed_out')
            ending.event_type = EventType.Value('EVENT_TYPE_ACTIVITY_TASK_' + terminal_kind.upper())
            terminal = getattr(ending, f'activity_task_{terminal_kind}_event_attributes')
            terminal.scheduled_event_id = 99 if kind == 'negative-foreign-schedule' else 22
            terminal.started_event_id = {
                'unstarted': 0, 'foreign-terminal': 19, 'duplicate-terminal': 0,
                'negative-failed-before-start': 0}.get(kind, 23)
            if kind == 'negative-wrong-type':
                ending.event_type = EventType.EVENT_TYPE_TIMER_FIRED
            elif kind == 'negative-untimed':
                ending.ClearField('event_time')
        elif kind == 'duplicate':
            ending.event_type = EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED
            ending.activity_task_scheduled_event_attributes.CopyFrom(attrs)
        else:
            completed = ending.activity_task_completed_event_attributes
            completed.scheduled_event_id = 22
            completed.started_event_id = 23
            completed.result.payloads.extend(await converter.encode([{'status': 'observed', 'native_run_id': 'original'}]))
        wrong_types = {'wrong-schedule-type': schedule, 'wrong-started-type': started, 'wrong-completion-type': ending}
        if kind in wrong_types:
            wrong_types[kind].event_type = EventType.EVENT_TYPE_TIMER_FIRED
        if kind == 'start-reuses-schedule-id':
            started.event_id = schedule.event_id
            completed.started_event_id = started.event_id
        elif kind in ('completion-reuses-start-id', 'negative-reuses-start-id'):
            ending.event_id = started.event_id
        elif kind == 'foreign-start-schedule':
            started.activity_task_started_event_attributes.scheduled_event_id = 99
        elif kind == 'foreign-completion-schedule':
            completed.scheduled_event_id = 99
        events = {
            'scheduled': [schedule], 'started': [schedule, started],
            'unstarted': [schedule, ending], 'negative-failed-before-start': [schedule, ending],
            'out-of-order': [schedule, ending, started],
            'duplicate-terminal': [schedule, ending, ending],
        }.get(kind, [schedule, started, ending])
        args = (converter, events, {'task_queue': 'original-queue'}, intent, ready)
        refusals = {'changed': 'original wake intent', 'duplicate': 'second delivery',
                    'wrong-schedule-type': 'original wake intent', 'wrong-started-type': 'original attempt',
                    'wrong-completion-type': 'original start', 'start-reuses-schedule-id': 'original attempt',
                    'completion-reuses-start-id': 'original start', 'foreign-start-schedule': 'original attempt',
                    'foreign-completion-schedule': 'original start'}
        if kind in refusals:
            with pytest.raises(ValueError, match=refusals[kind]):
                await _read_recipient_history(*args)
        else:
            result = await _read_recipient_history(*args, check_pending=True)
            assert result['intent'] == intent and result['scheduled_event_id'] == 22
            pending = kind in ('scheduled', 'started')
            assert ('_verified_pending_activity' in result) is pending
            assert '_verified_pending_activity' not in await _read_recipient_history(*args)
            if pending:
                assert result['status'] == ('scheduled' if kind == 'scheduled' else 'unknown')
                assert 'completed_event_id' not in result and 'terminal_status' not in result and 'outcome' not in result
                return
            uncorroborated = ('foreign-terminal', 'out-of-order', 'duplicate-terminal', 'negative-reuses-start-id',
                              'negative-wrong-type', 'negative-foreign-schedule', 'negative-failed-before-start')
            if kind in uncorroborated:
                assert 'completed_event_id' not in result
            else:
                assert result['completed_event_id'] == ending.event_id
            if unknown_delivery and kind not in uncorroborated:
                assert result['terminal_status'] == ('cancelled' if terminal_kind == 'canceled' else terminal_kind)
            else:
                assert 'terminal_status' not in result
            assert result['status'] == ('unknown' if unknown_delivery else 'observed')
            timing = result['timing']
            assert timing['clock'] == 'temporal_history'
            assert timing['intervals_ns']['scheduled_to_worker_started'] == (
                None if kind in ('untimed', 'skewed', 'unstarted', 'duplicate-terminal',
                                 'negative-failed-before-start') else 20)
            assert timing['intervals_ns']['ready_to_scheduled'] == (None if kind == 'untimed' else 1_000_000_010)
            if kind in (*uncorroborated, 'unstarted', 'negative-untimed'):
                assert timing['intervals_ns']['worker_started_to_delivery_terminal'] is None
                assert ('delivery_terminal' in timing['events']) is (kind == 'unstarted')
            elif unknown_delivery:
                assert timing['events']['delivery_terminal']['event_id'] == ending.event_id
            if kind != 'untimed':
                assert timing['events']['scheduled'] == {'event_id': 22, 'seconds': 5, 'nanos': 100}
            else:
                assert not timing['events']

    asyncio.run(exercise())


def test_pending_wake_observation_refuses_stop_close_cancel_and_conflicting_terminal():
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType
    from temporalio.api.history.v1 import HistoryEvent
    from ergora.campaigns.workflow import STOP_UPDATE, _wake_is_closing

    schedule = HistoryEvent(event_id=12, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED)
    started = HistoryEvent(event_id=13, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED)
    started.activity_task_started_event_attributes.scheduled_event_id = 12
    wake = [schedule, started]
    accepted = HistoryEvent(event_id=14, event_type=EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED)
    accepted.workflow_execution_update_accepted_event_attributes.accepted_request.input.name = STOP_UPDATE
    assert _wake_is_closing(accepted, wake)
    cancel = HistoryEvent(event_id=14, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_CANCEL_REQUESTED)
    cancel.activity_task_cancel_requested_event_attributes.scheduled_event_id = 12
    assert _wake_is_closing(cancel, wake)
    assert _wake_is_closing(HistoryEvent(event_id=14, event_type=EventType.EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED), wake)
    inconsistent = HistoryEvent(event_id=14, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_TIMED_OUT)
    inconsistent.activity_task_timed_out_event_attributes.scheduled_event_id = 999
    inconsistent.activity_task_timed_out_event_attributes.started_event_id = 13
    assert _wake_is_closing(inconsistent, wake)
    inconsistent.activity_task_timed_out_event_attributes.started_event_id = 999
    assert not _wake_is_closing(inconsistent, wake)


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


def test_assignment_launch_refuses_authority_changed_during_executable_preparation(tmp_path, monkeypatch):
    import fcntl
    from contextlib import contextmanager

    from ergora.campaigns import recipient_gate
    from ergora.runtime import budget_clock
    from ergora.storage.state import file_lock

    home = tmp_path
    storage = home / 'runs'
    storage.mkdir()
    folder = storage / 'original.session-turn'
    owner = {'pid': os.getpid(), 'boot_id': 'test-boot', 'start_ticks': '1'}
    executable = home / 'inert-file'
    executable.write_bytes(b'ordinary data for the inert launch hook')
    details = executable.stat()
    state = SimpleNamespace(root=home)
    gate = recipient_gate.RecipientGate.__new__(recipient_gate.RecipientGate)
    gate.binding = {'role': 'performance-analyst', 'native_id': 'original-thread', 'context_digest': 'original-context',
                    'source_executable': str(executable), 'payload_executable': str(executable),
                    'device': details.st_dev, 'inode': details.st_ino}
    role = gate.binding['role']
    gate.opening = {'project_revision': 10, 'plan': {'assignment': {'assignee': {'role': role, 'generation': 7},
                                                                  'next_task': {'task_id': 'assigned'}}}}
    gate.declaration = {'session_id': 'old-session', 'parent_run_id': 'parent', 'intent_id': 'old-intent',
                        'prompt': 'use original result', 'timeout_seconds': 30}
    gate.reference = {'campaign': 'original-campaign'}
    gate.attempt = {'native_run_id': 'original'}
    gate.files = SimpleNamespace(lock=home / 'campaign.lock')
    request = {'session': {'id': gate.declaration['session_id']}, 'native_id': gate.binding['native_id'],
               'context_digest': gate.binding['context_digest'], 'submitted': gate.submission(),
               'clock': budget_clock.authorize(30), 'timeout': 30}
    saved = {'request_sha256': recipient_gate.native_sources.sha(request), 'role': role}
    recorded = {'request_sha256': saved['request_sha256'], 'identity': owner}
    generations = []
    current = 7
    effects = []

    def project(actual_state, opening):
        assert actual_state is state and opening is gate.opening
        generations.append(current)
        return {'revision': 10, 'native_authority_revisions': {role: current}}

    @contextmanager
    def prepare_payload(clock, timeout):
        nonlocal current
        assert clock is request['clock'] and timeout == request['timeout']
        current = 8
        with executable.open('rb') as data:
            yield data.fileno()

    def inert_exec(*args):
        effects.append(args)
        pytest.fail('A stale assignment reached the inert launch hook')

    monkeypatch.setattr(recipient_gate, 'State', lambda root, *, read_only: state)
    monkeypatch.setattr(recipient_gate.native_sources, 'record', lambda *args: saved)
    monkeypatch.setattr(recipient_gate.native_sources, 'turn_folder', lambda *args: folder)
    monkeypatch.setattr(recipient_gate.native_sources, 'packet', lambda path, *args: request if path == folder else recorded)
    monkeypatch.setattr(recipient_gate.processes, 'identity', lambda pid: owner)
    monkeypatch.setattr(recipient_gate.RecipientGate, 'load', lambda *args: gate)
    monkeypatch.setattr(recipient_gate, 'require_check_project', project)
    monkeypatch.setattr(gate, 'leased_payload', prepare_payload)
    monkeypatch.setattr(gate, 'blocker', lambda: None)
    monkeypatch.setattr(fcntl, 'fcntl', lambda fd, command: fcntl.F_RDLCK)
    monkeypatch.setattr(os, 'execve', inert_exec)
    monkeypatch.setattr(os, 'supports_fd', os.supports_fd | {inert_exec})
    with file_lock(storage / 'old-session.session.lock', blocking=False) as lock:
        with pytest.raises(ValueError, match='permission generation changed'):
            recipient_gate._exec(str(home), 'demo', 'original', lock.fileno(),
                                 [str(executable), 'resume', request['native_id'], '-'])
    assert generations == [7, 8] and effects == []


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


@pytest.mark.parametrize('case', (
    'scheduled', 'started', 'offline', 'terminal', 'workflow-closed', 'expired', 'local-stop', 'late-stop',
    'readback-mismatch', 'release-error', 'released', 'refused', 'a2-wrong-role', 'a2-history-conflict',
    'a2-unknown', 'a1-reserved', 'a1-incomplete', 'late-a1-claim', 'a1-unavailable', 'late-release', 'late-release-error',
    'frozen-generation', 'parent-thread', 'parent-not-stopped', 'payload-missing',
))
def test_campaign_release_advisory_requires_live_original_evidence(tmp_path, monkeypatch, case):
    from ergora.agents import native_sources, runs

    role = 'performance-analyst'
    wake = {'session_id': 'a1', 'parent_run_id': 'parent', 'intent_id': 'resume'}
    first = {'task_id': 'result', 'source': {'kind': 'training_full_result', 'wait_for_live': True},
             'readback': {}, 'recipient': wake}
    expiry = int(time.time()) + (-1 if case == 'expired' else 60)
    opening = {'plan': {'tasks': [first], 'limits': {'expires_at': expiry},
                        'assignment': {'next_task': {'task_id': 'a2'}}}}
    executable = tmp_path / 'approved-payload'
    executable.touch()
    payload = executable.stat()
    if case == 'payload-missing':
        executable.unlink()
    opening['recipient_binding'] = {'role': role, 'context_digest': 'original-context', 'native_id': 'original-thread',
                                    'payload_executable': str(executable), 'device': payload.st_dev,
                                    'inode': payload.st_ino, 'size': payload.st_size}
    claim = {'intent': {'wake_id': 'original-independent'}}
    assignment = {'waiting_task_id': 'result', 'claim': claim, 'slot_status': 'claimed', 'release': None,
                  'assignee': {'role': role, 'generation': 4}, 'history': {'intent': claim['intent'], 'status': 'unknown'},
                  'native_receipt': {'dispatch': 'accepted', 'run': {'status': 'running', 'role': role}}}
    if case == 'release-error':
        assignment['release_error'] = 'Scoped error'
    elif case == 'released':
        assignment.update(slot_status='released', release={'run_id': 'original-a2'})
    elif case == 'refused':
        assignment['refusal'] = {'reason': 'stopped'}
    elif case == 'a2-wrong-role':
        assignment['native_receipt']['run']['role'] = 'reviewer'
    elif case == 'a2-history-conflict':
        assignment['history'] = {'status': 'contradictory'}
    elif case == 'a2-unknown':
        assignment['native_receipt']['run']['status'] = 'unknown'
    late = ({**assignment, 'slot_status': 'released', 'release': {'run_id': 'original-a2'}}
            if case == 'late-release' else
            {**assignment, 'release_error': 'Refreshed read failed'} if case == 'late-release-error' else assignment)
    assignments = iter((assignment, late))
    monkeypatch.setattr(application, '_assignment_status', lambda *args, **kwargs: next(assignments))
    monkeypatch.setattr(application, 'require_check_project',
                        lambda *_: {'revision': 5, 'native_authority_revisions': {role: 5 if case == 'frozen-generation' else 4}})
    monkeypatch.setattr(native_sources, 'record', lambda *_: {'session': {'id': 'a1', 'ordinal': 2}})

    def parent(_, project, session, *, after, limit, verify_executable):
        assert (project, session, after, limit, verify_executable) == ('demo', 'a1', 2, 1, False)
        return {'role': role, 'latest_run': 'parent', 'can_continue': True, 'turns': [{
            'id': 'parent', 'role': role, 'execution_stopped': case != 'parent-not-stopped',
            'context_digest': 'original-context',
            'native_session': {'id': 'another-thread' if case == 'parent-thread' else 'original-thread'}}]}

    monkeypatch.setattr(runs, 'inspect_session', parent)

    source = {'status': 'available', 'observation_sha256': 'a' * 64}
    history = {'intent': {'run_id': 'original', 'source': source}, 'status': 'scheduled',
               'scheduled_event_id': 21, '_verified_pending_activity': True}
    if case == 'started':
        history.update(status='unknown', started_event_id=22)
    elif case == 'terminal':
        history.update(status='unknown', started_event_id=22, _verified_pending_activity=False)
    if case == 'readback-mismatch':
        source = {**source, 'observation_sha256': 'b' * 64}
    observed = {'_original_admission_open': case not in ('offline', 'workflow-closed'),
                'readback_completion': {'recipient': history},
                'stop': {'status': 'prepared' if case == 'local-stop' else 'not_recorded'},
                'tasks': {'result': {'readback_observation': source}}}
    reads = iter((None, {'pending': True} if case == 'late-a1-claim' else None))
    files = SimpleNamespace(project='demo', _read=lambda _: next(reads),
                            load_stop=lambda *_: ({'pending': True} if case == 'late-stop' else None, None, None))

    def original_receipt(_, project, session, parent, intent):
        assert (project, session, parent, intent) == ('demo', 'a1', 'parent', 'resume')
        if case == 'a1-unavailable':
            raise OSError('Scoped native receipt read failed')
        return {'dispatch': {'a1-reserved': 'reserved', 'a1-incomplete': 'incomplete'}.get(case, 'unrecorded')}

    monkeypatch.setattr(runs, 'continuation_receipt', original_receipt)
    response = application._recipient_status(None, files, opening, {'saved': True}, {'run_id': 'original'}, observed)
    assert response['assignment'].get('release_unobserved') is (True if case in ('scheduled', 'started') else None)
    assert '_original_admission_open' not in response
    assert '_verified_pending_activity' not in response['recipient']['history']


@pytest.mark.parametrize('parent_state', ['current', 'revoked', 'missing', 'consumed'])
def test_release_advisory_rechecks_current_chain_using_native_session_owner(native_session_case, monkeypatch, parent_state):
    state, _, config, runs = native_session_case
    role = 'implementer'
    project = state.project('demo')
    revision = project['revision']
    assignee = {'role': role, 'generation': projects.native_authority_revision(project, role)}
    parent = runs.run_agent(state, 'demo', role, 'Seed original advisory recipient', timeout=10,
                            expected_revision=revision, session_intent='advisory-parent', codex_config=config)
    assert parent['status'] == 'succeeded' and parent['execution_stopped'] is True
    selected = {'session_id': parent['id'], 'parent_run_id': parent['id'], 'intent_id': 'original-campaign-wake'}
    executable = Path(runs._read_session_context(state, parent)['inference']['executable'])
    payload = executable.stat()
    binding = {'role': role, 'native_id': parent['native_session']['id'], 'context_digest': parent['context_digest'],
               'payload_executable': str(executable), 'device': payload.st_dev, 'inode': payload.st_ino, 'size': payload.st_size}
    if parent_state == 'revoked':
        projects.bind(state, 'demo', role, {**project['bindings'][role], 'reasoning_effort': 'high'}, revision)
    elif parent_state == 'missing':
        with state.connect() as db:
            db.execute('DELETE FROM agent_runs WHERE project=? AND id=?', ('demo', parent['id']))
    elif parent_state == 'consumed':
        later = runs.continue_session(state, 'demo', parent['id'], parent['id'], 'Another original continuation',
                                      expected_revision=revision, intent_id='already-consumed', timeout=10)
        assert later['status'] == 'succeeded'
    assert runs.continuation_receipt(state, 'demo', **selected)['dispatch'] == 'unrecorded'

    original_digest = hashlib.file_digest
    payload_digests = []

    def observe_digest(stream, *args, **kwargs):
        if stream.name == str(executable):
            payload_digests.append(stream.name)
        return original_digest(stream, *args, **kwargs)

    monkeypatch.setattr(hashlib, 'file_digest', observe_digest)
    if parent_state == 'current':
        assert runs.inspect_session(state, 'demo', parent['id'], limit=1)['can_continue']
        assert payload_digests == [str(executable)]
        payload_digests.clear()

    claim = {'intent': {'wake_id': 'original-a2'}}
    assignment = {'waiting_task_id': 'result', 'claim': claim, 'slot_status': 'claimed', 'release': None,
                  'assignee': assignee, 'history': {'intent': claim['intent'], 'status': 'unknown'},
                  'native_receipt': {'dispatch': 'accepted', 'run': {'status': 'running', 'role': role}}}
    monkeypatch.setattr(application, '_assignment_status', lambda *_args, **_kwargs: assignment)
    monkeypatch.setattr(application, 'require_check_project', lambda *_: state.project('demo'))
    files = SimpleNamespace(project='demo', _read=lambda _: None, load_stop=lambda *_: (None, None, None))
    opening = {'plan': {'limits': {'expires_at': int(time.time()) + 60}}, 'recipient_binding': binding}
    source = {'status': 'available', 'observation_sha256': 'a' * 64}
    output = {'assignment': assignment, 'tasks': {'result': {'readback_observation': source}},
              'stop': {'status': 'not_recorded'}}
    original = {'intent': {'run_id': 'original', 'source': source}}
    observed = application._assignment_release_unobserved(state, files, opening, {'saved': True},
                                                           {'run_id': 'original'}, output, original, selected)
    assert observed is (parent_state == 'current')
    assert payload_digests == []


@pytest.mark.parametrize('independent', [False, True])
@pytest.mark.parametrize(('failure', 'dispatch', 'veto', 'status', 'reason'), [
    ('revoked', 'unrecorded', None, 'blocked', 'recipient_authority_revoked'),
    ('revoked', 'incomplete', None, 'unknown', None),
    ('revoked', 'accepted', None, 'unknown', None),
    ('revoked', 'unavailable', None, None, None),
    ('revoked', 'unrecorded', 'stopped', 'blocked', 'stopped'),
    ('revoked', 'unrecorded', 'expired', 'blocked', 'expired'),
    ('identity', 'unrecorded', None, None, None),
    ('io', 'unrecorded', None, None, None),
])
def test_campaign_recipient_reports_revocation_only_before_native_reservation(monkeypatch, failure, dispatch, veto,
                                                                           status, reason, independent):
    from contextlib import nullcontext

    pytest.importorskip('temporalio')
    from ergora.agents import runs
    from ergora.campaigns import recipient as delivery
    from ergora.campaigns.recipient_gate import assignment_refusal
    from ergora.campaigns.records import ASSIGNMENT_ATTEMPT, ASSIGNMENT_REFUSAL, identity

    selected = {'session_id': 'session', 'parent_run_id': 'parent', 'intent_id': 'original',
                'prompt': 'Read the original result.', 'timeout_seconds': 20}
    intent = {'wake_id': 'original-wake'}
    opening = {'project_revision': 1, 'plan': {'tasks': [{'recipient': selected, 'readback': {},
                                                         'source': {'pending': True}}]}}
    if independent:
        intent['task_id'] = 'independent'
        opening['plan']['assignment'] = {'next_task': {'task_id': 'independent', 'recipient': selected}}
    attempt = {'intent': intent, 'native_run_id': 'original-run'}
    saved = {}

    def write(name, value, *, before_publish=None):
        if before_publish is not None:
            before_publish()
        saved[name] = value

    files = SimpleNamespace(home=None, project='demo', load=lambda: (opening, 'start', 'run'),
                            _read=saved.get, write=write)
    gate = SimpleNamespace(admission=nullcontext, require_open=lambda: None, require_authority=lambda _: None,
                           reference={}, blocker=lambda: veto)
    monkeypatch.setattr(delivery, 'verify_wake_intent', lambda *args: None)
    monkeypatch.setattr(delivery, 'State', lambda *args: None)
    monkeypatch.setattr(delivery, 'attempt_record', lambda *args: attempt)
    monkeypatch.setattr(delivery, 'RecipientGate', lambda *args, **kwargs: gate)
    monkeypatch.setattr(delivery.CodexRecipient, '_first_slot', lambda *args: {'status': 'controlled'})
    reads = iter(('unrecorded', dispatch))

    def read_receipt(*args):
        observed = next(reads)
        if observed == 'unavailable':
            raise OSError('Continuation read unavailable')
        return {'run_id': 'original-run', 'dispatch': observed}

    def refuse(*args, **kwargs):
        if failure == 'revoked':
            raise runs._SessionAuthorityRevoked('Original role generation changed')
        if failure == 'identity':
            raise ValueError('Original repository identity differs')
        raise OSError('Native continuation read unavailable')

    monkeypatch.setattr(runs, 'continuation_receipt', read_receipt)
    monkeypatch.setattr(runs, 'continue_session', refuse)
    activity = delivery.CodexRecipient(files, opening, 'start', 'run', read_wake_history=None)
    if status is None:
        error_type = ValueError if failure == 'identity' else OSError
        with pytest.raises(error_type) as error:
            activity._deliver(intent)
        assert type(error.value) is error_type
    else:
        observed = activity._deliver(intent)
        expected = {'status': status, 'native_run_id': 'original-run'}
        if reason is not None:
            expected['reason'] = reason
        assert observed == expected
    name = ASSIGNMENT_ATTEMPT if independent else 'recipient-attempt'
    expected = {name: attempt}
    if independent and status == 'blocked':
        expected[ASSIGNMENT_REFUSAL] = {'attempt_sha256': identity(attempt), 'reason': reason}
        assert assignment_refusal(files, attempt) == expected[ASSIGNMENT_REFUSAL]
    assert saved == expected


@pytest.mark.parametrize(('case', 'result_task'), [
    ('revoked', 'next'), ('revoked', 'wait'), ('stale-parent', 'next'), ('unrelated', 'next'),
    ('moved-repository', 'next'), ('missing-lock', 'next'), ('busy-lock', 'next'), ('partial-native', 'next'),
    ('different-native-id', 'next'), ('stop-during-proof', 'next'), ('expiry-during-proof', 'next'),
    ('stop-during-final-read', 'next'), ('expiry-during-final-read', 'next'),
])
def test_assignment_proves_preclaim_revocation_without_native_effects(registration, monkeypatch, case, result_task):
    from contextlib import nullcontext
    from uuid import uuid4

    pytest.importorskip('temporalio')
    from ergora.agents import runs
    from ergora.campaigns import recipient
    from ergora.campaigns.records import (
        ASSIGNMENT_ATTEMPT, ASSIGNMENT_REFUSAL, FIXED_TASK_LOCATOR, CampaignFiles, assignment_intent,
        attempt_document, check_intent, check_receipt, identity, manual_wake_source, project_selection,
        result_document, stop_intent, update_attempt, wake_intent,
    )
    from ergora.storage.assets import inventory_tree
    from ergora.storage.state import file_lock

    state, definition = registration
    registered = registrations.register(state, definition, 0)
    scheduler = {'tool': 'temporal', 'address': '127.0.0.1:1', 'namespace': 'default', 'task_queue': 'test'}
    project = projects.bind(state, 'demo', 'scheduler', scheduler, registered['revision'])
    role = 'implementer'
    revision = project['revision']
    generation = projects.native_authority_revision(project, role)
    now = int(time.time())
    turns = {}
    bindings = {}
    declarations = {}
    context_path = Path(project['repo'])
    repo = context_path.stat()
    (state.root / 'runs').mkdir()
    for stage in ('wait', 'next'):
        session = f'{stage}-session'
        declared = {'session_id': session, 'parent_run_id': session, 'intent_id': f'{stage}-intent',
                    'prompt': f'Use original {stage} evidence', 'timeout_seconds': 20}
        declarations[stage] = declared
        context = {'project': 'demo', 'project_revision': revision, 'role': role, 'authority_revision': generation,
                   'repo': str(context_path), 'repo_identity': [repo.st_dev, repo.st_ino],
                   'requested_binding': projects.effective_configuration(project)['layers'][role]['binding']}
        folder = runs.native_sources.session_folder(state, session) / 'context'
        folder.mkdir(parents=True)
        (folder / 'context.json').write_bytes(runs.native_sources.encode(context))
        digest = inventory_tree(folder)[0]
        native = str(uuid4())
        turns[session] = {'id': session, 'kind': 'native-agent-run', 'session': {'id': session, 'ordinal': 0,
                          'parent_run': None}, 'context_digest': digest, 'execution_stopped': True,
                          'native_session': {'id': native}, 'role': role, 'request_sha256': 'd' * 64, 'status': 'succeeded'}
        bindings[stage] = {'role': role, 'native_id': native, 'context_digest': digest, 'source_executable': '/inert',
                           'payload_executable': '/inert', 'payload_sha256': 'e' * 64, 'device': 1, 'inode': 2, 'size': 3}
        (state.root / 'runs' / f'{session}.session.lock').touch()

    source = dict.fromkeys(FIXED_TASK_LOCATOR, 'a' * 64)
    source.update(project_revision=revision, candidate_sha='b' * 40, operation_id='check', pending=True,
                  job_id='check-' + 'a' * 40 + '-' + 'b' * 24)
    waiting_task = {'task_id': 'wait', 'depends_on': [], 'source': source, 'recipient': declarations['wait'],
                    'readback': {'due_at': now + 10, 'deadline_at': now + 30}, 'wake_on_observe': True}
    plan = {'schema_version': 1, 'goal': 'Original assignment', 'acceptance': 'Separate authorized work',
            'baseline_commit': 'a' * 40, 'evidence_format': 'receipts', 'limits': {'expires_at': now + 60},
            'tasks': [waiting_task], 'assignment': {'assignee': {'role': role, 'generation': generation},
                'waiting_task_id': 'wait', 'next_task': {'task_id': 'next', 'recipient': declarations['next']}}}
    owner = CampaignFiles(state.root, 'demo', 'preclaim-revocation')
    owner.ensure_directory()
    opening = application._opening(owner, revision, plan, 'f' * 64, project_selection(state, project, revision),
                                   {'recipient_binding': bindings['wait'], 'assignment_binding': bindings['next']})
    start = attempt_document(opening, str(uuid4()))
    run_id = str(uuid4())
    owner.write('start-intent', opening)
    owner.write('start-attempt', start)
    owner.write('start-result', result_document(opening, start, run_id))
    waiting = check_intent(opening, identity(start), run_id, 'wait', 'a' * 64, job={'status': 'attempted'})
    waiting = {'intent': waiting, 'attempt': update_attempt(waiting, 'ergora-campaign-check:' + str(uuid4()))}
    owner.write('wait-check-wait', waiting)
    if result_task == 'wait':
        result = {'status': 'succeeded', 'receipt_sha256': 'd' * 64, 'fixed_results_sha256': 'e' * 64,
                  'waiting_receipt_sha256': identity(check_receipt(waiting))}
        terminal = check_intent(opening, identity(start), run_id, 'wait', 'c' * 64, job=result)
        terminal = {'intent': terminal, 'attempt': update_attempt(terminal, 'ergora-campaign-check:' + str(uuid4()))}
        owner.write('check-wait', terminal)
        intent = wake_intent(opening, run_id, waiting_task,
                             manual_wake_source(waiting_task, check_receipt(waiting), check_receipt(terminal)))
    else:
        intent = assignment_intent(opening, run_id, check_receipt(waiting))

    if case == 'unrelated':
        changed = projects.bind(state, 'demo', 'scheduler', {**scheduler, 'task_queue': 'changed'}, revision)
    else:
        changed = projects.bind(state, 'demo', role, {'tool': 'codex', 'model': 'gpt-6.1-sol',
                                                      'reasoning_effort': 'high'}, revision)
    assert changed['revision'] > revision
    assert (projects.native_authority_revision(changed, role) > generation) is (case != 'unrelated')
    if case == 'moved-repository':
        context_path.rename(context_path.with_name('original-repo'))
        context_path.mkdir()

    selected = declarations[result_task]
    native_id = runs._continuation_run_id(selected['session_id'], selected['intent_id'])
    session_lock = state.root / 'runs' / f"{selected['session_id']}.session.lock"
    if case == 'missing-lock':
        session_lock.unlink()

    def advance_fence():
        if case.startswith('stop-'):
            owner.write('stop-intent', stop_intent(opening, identity(start), run_id))
        else:
            delay = 61 * 10**9
            wall = time.time_ns()
            boot, ticks = runs.budget_clock._clock()
            monkeypatch.setattr(time, 'time_ns', lambda: wall + delay)
            monkeypatch.setattr(runs.budget_clock, '_clock', lambda: (boot, ticks + delay))

    dispatch_reads = []
    original_receipt = runs.continuation_receipt

    def read_dispatch(*selection):
        observed = original_receipt(*selection)
        dispatch_reads.append(observed['dispatch'])
        if len(dispatch_reads) == 3 and case.endswith('-final-read'):
            assert observed['run_id'] == native_id and observed['dispatch'] == 'unrecorded'
            advance_fence()
        return observed

    def stopped_turns(_state, project_id, session):
        assert _state.root == state.root and project_id == 'demo'
        parent = turns[session]
        if session != selected['session_id']:
            return [parent]
        if case == 'stale-parent':
            return [parent, {**parent, 'id': 'later-turn'}]
        if case == 'partial-native':
            runs.native_sources.turn_folder(state, native_id).mkdir()
        if case == 'different-native-id':
            return [{**parent, 'native_session': {'id': str(uuid4())}}]
        if case.endswith('-proof'):
            advance_fence()
        return [parent]

    monkeypatch.setattr(runs, '_session_turns', stopped_turns)
    monkeypatch.setattr(runs.native_sources, 'find_run', lambda _state, _project, ident: turns.get(ident))
    monkeypatch.setattr(runs, 'continue_session', lambda *args, **kwargs: pytest.fail('Native continuation attempted'))
    monkeypatch.setattr(runs, 'continuation_receipt', read_dispatch)
    delivery = recipient.CodexRecipient(owner, opening, start, run_id, read_wake_history=None)
    with (file_lock(session_lock, blocking=False) if case == 'busy-lock' else nullcontext()):
        reasons = {'revoked': 'recipient_authority_revoked', 'stop-during-proof': 'stopped',
                   'expiry-during-proof': 'expired', 'stop-during-final-read': 'stopped',
                   'expiry-during-final-read': 'expired'}
        if case in reasons:
            reason = reasons[case]
            assert delivery._deliver(intent) == {'status': 'blocked', 'native_run_id': native_id, 'reason': reason}
        else:
            with pytest.raises(ValueError, match='Project revision changed'):
                delivery._deliver(intent)
    if case.endswith('-final-read'):
        assert dispatch_reads == ['unrecorded'] * 3
    for record in (ASSIGNMENT_ATTEMPT, ASSIGNMENT_REFUSAL, 'recipient-attempt'):
        assert owner._read(record) is None
    assert runs.native_sources.turn_folder(state, native_id).is_dir() is (case == 'partial-native')
    if case == 'missing-lock':
        assert not session_lock.exists()


@pytest.mark.parametrize('contradiction', [False, True])
def test_assignment_status_reads_dependent_release_before_native_snapshot(monkeypatch, contradiction):
    from ergora.agents import runs
    from ergora.campaigns import recipient_gate
    from ergora.campaigns.records import ASSIGNMENT_ATTEMPT

    selected = {'session_id': 'next-session', 'intent_id': 'next-intent'}
    native_id = runs._continuation_run_id(selected['session_id'], selected['intent_id'])
    opening = {'plan': {'assignment': {'assignee': {'role': 'implementer', 'generation': 1},
                'waiting_task_id': 'wait', 'next_task': {'task_id': 'next', 'recipient': selected}}}}
    claim = {'native_run_id': native_id}
    release = {'run_id': native_id, 'request_sha256': 'd' * 64}
    resumed = {'slot_release': release}
    published = False

    def read_record(name):
        nonlocal published
        if name == ASSIGNMENT_ATTEMPT:
            return claim
        if name == 'recipient-attempt':
            published = True
            return resumed

    def read_native(_state, _gate):
        return {'dispatch': 'accepted', 'run': {'status': 'succeeded' if published else 'running',
                'execution_stopped': published, 'request_sha256': 'e' * 64 if contradiction else 'd' * 64}}

    monkeypatch.setattr(recipient_gate, 'RecipientGate', lambda *args: object())
    monkeypatch.setattr(runs, 'campaign_recipient_receipt', read_native)
    files = SimpleNamespace(_read=read_record)
    if contradiction:
        with pytest.raises(ValueError, match='release differs'):
            application._assignment_status(None, files, opening, {}, None)
    else:
        output = application._assignment_status(None, files, opening, {}, None)
        assert output['native_receipt']['run']['execution_stopped'] is True
        assert output['release'] == release and output['slot_status'] == 'released'


@pytest.mark.parametrize(('fence', 'wake_conflict', 'local', 'expected'), (
    ('stopped', True, False, 'unknown'),
    ('expired', True, False, 'unknown'),
    ('active', True, False, 'unknown'),
    ('stopped', False, False, 'blocked'),
    ('expired', False, False, 'blocked'),
    ('stopped', True, True, 'observed'),
))
def test_campaign_status_keeps_wake_conflict_separate_from_stop_and_native_receipt(
        tmp_path, monkeypatch, fence, wake_conflict, local, expected):
    pytest.importorskip('temporalio')
    from ergora.agents import runs
    from ergora.campaigns import recipient_gate, workflow

    run_id = 'original-run'
    state = SimpleNamespace(root=tmp_path)
    recipient = {'session_id': 'session', 'parent_run_id': 'parent', 'intent_id': 'next'}
    task = {'task_id': 'result', 'source': {'kind': 'training_full_result'},
            'readback': {'due_at': 10, 'deadline_at': 80}, 'recipient': recipient}
    opening = {'plan': {'tasks': [task], 'limits': {'expires_at': 100}}}
    start, result = {'start': 'original-attempt'}, {'run_id': run_id}
    stop_receipt = {'decision': 'accepted', 'run_id': run_id}
    stops = ({'run_id': run_id}, {'update_id': 'original-stop'}, {'receipt': stop_receipt})
    stop_records = stops if fence == 'stopped' else (None, None, None)
    original_completion = {'task_id': 'result', 'scheduled_event_id': 11,
                           'recovery_history': {'completed_event_id': 21}}
    original_terminal = {'status': 'timed_out', 'terminal_event_id': 13}
    native_id = runs._continuation_run_id(recipient['session_id'], recipient['intent_id'])
    native_intent = {'wake_id': 'original-wake'}
    local_attempt = {'native_run_id': native_id, 'intent': native_intent} if local else None
    submitted = {'intent_id': recipient['intent_id']}
    native = {'run_id': native_id, 'dispatch': 'accepted', 'native_start': {'status': 'started'},
              'run': {'status': 'succeeded', 'execution_stopped': True,
                      'context_digest': 'original-context', 'submitted': submitted}}
    files = SimpleNamespace(project='demo', load=lambda: (opening, start, result),
                            load_stop=lambda *_: stop_records, load_checks=lambda *_: (run_id, []),
                            _read=lambda key: local_attempt if key == 'recipient-attempt' else None)
    handle = SimpleNamespace(run_id=run_id)

    async def connect(*_):
        return object()

    async def current(*_):
        return handle, SimpleNamespace(run_id=run_id, status=SimpleNamespace(name='COMPLETED')), None

    async def read_stop(*_):
        assert fence == 'stopped'
        return stop_receipt

    async def runtime_status(*_, **__):
        return {'workflow_state_status': 'unavailable'}

    async def read_task_history(*_):
        if wake_conflict:
            raise workflow.WakeHistoryConflict(ValueError('Wake History contradicts its original start'),
                                               ({}, original_completion, original_terminal, None))
        return {}, None, None, None, None, None

    runtime = SimpleNamespace(connect=connect, current=current, read_stop=read_stop, runtime_status=runtime_status,
                              read_task_history=read_task_history, RPC_SECONDS=1, RPCError=RuntimeError)
    monkeypatch.setattr(application, 'CampaignFiles', lambda *_: files)
    monkeypatch.setattr(application, 'verify_registration', lambda *_: None)
    monkeypatch.setattr(application, '_snapshot', lambda *_: {'run_id': run_id, 'attempt_sha256': 'original'})
    monkeypatch.setattr(application, '_temporal', lambda: runtime)
    monkeypatch.setattr(application, 'time', SimpleNamespace(time=lambda: 20 if fence == 'active' else 101))

    def verified_gate(*args):
        assert local and args == (files, opening, start, result, local_attempt)
        return SimpleNamespace(intent=native_intent, submission=lambda: submitted,
                               binding={'context_digest': 'original-context'})

    def native_receipt(*args):
        assert local and args == (state, 'demo', 'session', 'parent', 'next')
        return native

    monkeypatch.setattr(recipient_gate, 'RecipientGate', verified_gate)
    monkeypatch.setattr(runs, 'continuation_receipt', native_receipt)

    output = asyncio.run(application.status(state, 'demo', 'original', online=True, task_id='result'))
    assert '_wake_history_conflict' not in output
    assert output['stop']['receipt'] == (stop_receipt if fence == 'stopped' else None)
    projected = output['recipient']
    assert projected == {'status': expected, 'intent': native_intent if local else None,
                         'native_receipt': native if local else None, 'history': None,
                         **({'reason': fence} if expected == 'blocked' else {})}
    if wake_conflict:
        assert output['task_observation_history_status'] == 'contradictory'
        assert output['readback_completion'] == original_completion and output['readback_terminal'] == original_terminal
        assert output['tasks']['result']['state_source'] == 'history' and output['tasks']['result']['eligible'] is False
    else:
        assert 'task_observation_history_status' not in output


@pytest.mark.parametrize('outcome', ['passing', 'unrelated', 'pending', 'unaccepted', 'changed-grant',
                                     'history-unavailable', 'service-unavailable', 'no-timer',
                                     'changed-command', 'wrong-acceptance', 'changed-receipt', 'accepted-only',
                                     'offline', 'completed-failure', 'duplicate-id',
                                     'wrong-accepted-type', 'wrong-completed-type', 'zero-accepted-id',
                                     'reused-accepted-id', 'completion-before-acceptance', 'unrelated-malformed-update',
                                     'timed', 'timed-missing', 'timed-bad', 'timed-bad-seconds', 'timed-reversed'])
def test_status_recovers_original_task_history_without_worker(registration, tmp_path, monkeypatch, outcome):
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.converter import DataConverter
    from temporalio.service import RPCError, RPCStatusCode
    from ergora.campaigns import workflow as runtime
    from ergora.campaigns.records import (READBACK_ACTIVITY, CampaignFiles, FIXED_TASK_LOCATOR, attempt_document,
                                         check_intent, check_receipt, identity, project_selection, read_plan,
                                         readback_grant, readback_id, result_document, update_attempt)

    timing_case = {
        'timed': ((100, 20), (100, 30), (100, 60), True, 10, 30),
        'timed-missing': ((100, 20), None, (100, 60), False, None, None),
        'timed-bad': ((100, 20), (100, 1_000_000_000), (100, 60), False, None, None),
        'timed-bad-seconds': ((100, 20), (253_402_300_800, 30), (100, 60), False, None, None),
        'timed-reversed': ((100, 20), (100, 10), (100, 60), True, None, 50),
    }.get(outcome)
    if timing_case is not None:
        outcome = 'passing'

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
                HistoryEvent(event_id=event_id, event_type=EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED,
                             workflow_execution_update_accepted_event_attributes={
                    'protocol_instance_id': update_id, 'accepted_request': {'meta': {'update_id': update_id},
                        'input': {'name': runtime.CHECK_UPDATE, 'args': {'payloads': await converter.encode([command])}}}}),
                HistoryEvent(event_id=event_id + 1, event_type=EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_COMPLETED,
                             workflow_execution_update_completed_event_attributes={
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
                HistoryEvent(event_id=4, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED,
                             activity_task_scheduled_event_attributes={
                    'activity_id': activity_id, 'activity_type': {'name': READBACK_ACTIVITY},
                    'task_queue': {'name': opening['task_queue']}, 'retry_policy': {'maximum_attempts': 1},
                    'input': {'payloads': await converter.encode([scheduled_grant])}}),
                HistoryEvent(event_id=5, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED,
                             activity_task_started_event_attributes={'scheduled_event_id': 4, 'attempt': 1}),
                HistoryEvent(event_id=6, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED,
                             activity_task_completed_event_attributes={
                    'scheduled_event_id': 99 if outcome == 'unrelated' else 4, 'started_event_id': 5,
                    'result': {'payloads': await converter.encode([activity_result])}}),
            ])
            if timing_case is not None:
                for event, timestamp in zip(events[-3:], timing_case[:3], strict=True):
                    if timestamp is not None:
                        event.event_time.seconds, event.event_time.nanos = timestamp
        if outcome != 'unaccepted':
            accepted, completed = await update_events(terminal_command, terminal_receipt, 7)
            if outcome == 'wrong-accepted-type':
                accepted.event_type = EventType.EVENT_TYPE_TIMER_FIRED
            elif outcome == 'wrong-completed-type':
                completed.event_type = EventType.EVENT_TYPE_TIMER_FIRED
            elif outcome == 'zero-accepted-id':
                accepted.event_id = 0
                completed.workflow_execution_update_completed_event_attributes.accepted_event_id = 0
            elif outcome == 'reused-accepted-id':
                completed.event_id = accepted.event_id
            elif outcome == 'completion-before-acceptance':
                completed.event_id = accepted.event_id - 1
            elif outcome == 'unrelated-malformed-update':
                foreign_accepted, foreign_completed = HistoryEvent(), HistoryEvent()
                foreign_accepted.CopyFrom(accepted)
                foreign_completed.CopyFrom(completed)
                foreign_accepted.workflow_execution_update_accepted_event_attributes.protocol_instance_id = 'unrelated'
                foreign_completed.workflow_execution_update_completed_event_attributes.meta.update_id = 'unrelated'
                for foreign in (foreign_accepted, foreign_completed):
                    foreign.event_type = EventType.EVENT_TYPE_TIMER_FIRED
                    foreign.event_id = 0
                events.extend((foreign_accepted, foreign_completed))
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
                    'wrong-accepted-type': 'changed or duplicate Update',
                    'zero-accepted-id': 'changed or duplicate Update',
                    'wrong-completed-type': 'completion does not bind its original accepted Update',
                    'reused-accepted-id': 'completion does not bind its original accepted Update',
                    'completion-before-acceptance': 'completion does not bind its original accepted Update',
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
        if outcome in ('passing', 'accepted-only', 'completed-failure', 'unrelated-malformed-update'):
            expected_completion = {
                'task_id': 'wait', 'activity_id': activity_id, 'waiting_receipt_sha256': identity(waiting),
                'scheduled_event_id': 4, 'completed_event_id': 6, 'receipt_sha256': 'd' * 64,
                'fixed_results_sha256': 'e' * 64, 'observation_sha256': identity(observation),
                'reader_cleanup_sha256': 'f' * 64,
            }
            if timing_case is not None:
                scheduled, worker, completed, worker_timed, queue_span, read_span = timing_case
                stamps = {'scheduled': (4, scheduled), 'completed': (6, completed)}
                if worker_timed:
                    stamps['worker_started'] = (5, worker)
                expected_completion['timing'] = {
                    'clock': 'temporal_history',
                    'events': {name: {'event_id': event_id, 'seconds': seconds, 'nanos': nanos}
                               for name, (event_id, (seconds, nanos)) in stamps.items()},
                    'intervals_ns': {'scheduled_to_worker_started': queue_span,
                                     'worker_started_to_completed': read_span},
                }
            assert observed['readback_completion'] == expected_completion
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
    from temporalio.api.enums.v1 import EventType
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

                for run_id, field, reason in (
                        (first, 'workflow_execution_started_event_attributes', 'missing its first event'),
                        (first, 'workflow_execution_continued_as_new_event_attributes', 'lacks its native rollover close'),
                        (current, 'workflow_execution_started_event_attributes', 'lacks its native start')):
                    async def wrong_event_type(handle, *args, **kwargs):
                        async for event in original_fetch(handle, *args, **kwargs):
                            if handle.run_id == run_id and event.HasField(field):
                                copied = type(event).FromString(event.SerializeToString())
                                copied.event_type = EventType.EVENT_TYPE_TIMER_FIRED
                                event = copied
                            yield event

                    with monkeypatch.context() as patch:
                        patch.setattr(WorkflowHandle, 'fetch_history_events', wrong_event_type)
                        with pytest.raises(ValueError, match=reason):
                            await runtime.current(client, saved, opening, attempt, first)

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


@pytest.mark.skipif(not os.environ.get('ERGORA_TEST_TEMPORAL_BIN'), reason='Requires the optional local Temporal CLI')
def test_opted_fixed_check_shares_manual_and_guarded_readiness(tmp_path):
    pytest.importorskip('temporalio')
    from uuid import uuid4

    from temporalio import activity
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Replayer, Worker
    from ergora.campaigns import workflow as runtime
    from ergora.campaigns.records import (
        FIXED_TASK_UPDATE_PREFIX, READBACK_ACTIVITY, RECIPIENT_ACTIVITY, attempt_document,
        check_intent, identity, original_check_evidence, readback_id, stop_intent, update_attempt, validate_plan,
    )

    source = {'pending': True, 'project_revision': 1, 'operation_id': 'original',
              'job_id': 'check-' + 'a' * 40 + '-' + 'b' * 24, 'authorization_sha256': 'a' * 64,
              'verification_sha256': 'b' * 64, 'request_file_sha256': 'c' * 64, 'job_sha256': 'd' * 64,
              'candidate_sha': 'a' * 40}
    succeeded = {key: value for key, value in source.items() if key != 'pending'}
    succeeded.update(project='demo', stop_requested=False, status='succeeded', cleanup_confirmed=True,
                     receipt_sha256='e' * 64, fixed_results_sha256='f' * 64)
    pending = {**succeeded, 'cleanup_confirmed': None, 'status': 'attempted',
               'receipt_sha256': None, 'fixed_results_sha256': None}
    deliveries = {}
    held_reads = {name: (asyncio.Event(), asyncio.Event()) for name in ('manual-held', 'conflict')}

    @activity.defn(name=READBACK_ACTIVITY)
    async def original_result(grant: dict) -> dict:
        name = activity.info().workflow_id.rsplit(':', 1)[1]
        if name in held_reads:
            started, release = held_reads[name]
            started.set()
            while not release.is_set():
                activity.heartbeat('original status read is held')
                await asyncio.sleep(.04)
        return {'activity_id': readback_id(grant), 'reader_cleanup_sha256': 'b' * 64, 'observation': succeeded}

    @activity.defn(name=RECIPIENT_ACTIVITY)
    async def recipient(intent: dict) -> dict:
        deliveries.setdefault(intent['workflow_id'], []).append(intent)
        return {'status': 'observed'}

    async def check(client, queue, campaign):
        now = int(time.time())
        due, expiry = now + 4, now + 25
        selected = {'task_id': 'fixed', 'depends_on': [], 'source': source,
                    'wake_on_observe': True, 'readback': {'due_at': due, 'deadline_at': due + 12},
                    'recipient': {'session_id': 'session', 'parent_run_id': 'parent', 'intent_id': 'original',
                                  'prompt': 'Use the original check result.', 'timeout_seconds': 8}}
        child = {'task_id': 'dependent', 'depends_on': ['fixed'], 'source': source}
        plan = {'schema_version': 1, 'goal': 'Verify one fixed check', 'acceptance': 'One original result',
                'evidence_format': 'Native History', 'baseline_commit': source['candidate_sha'],
                'limits': {'expires_at': expiry}, 'tasks': [selected, child]}
        validate_plan(plan)
        workflow_id = f'ergora-campaign:demo:{campaign}'
        opening = {'project': 'demo', 'plan': plan, 'workflow_id': workflow_id, 'task_queue': queue,
                   'scheduler': {'namespace': client.namespace}}
        attempt = attempt_document(opening, str(uuid4()))
        run_id = await runtime.start(client, opening, attempt)
        handle = client.get_workflow_handle(workflow_id, run_id=run_id)

        def command(task, observation, wait=None):
            evidence, job = original_check_evidence(opening, task, observation)
            if wait is not None:
                job = {**job, 'waiting_receipt_sha256': identity(wait)}
            intent = check_intent(opening, identity(attempt), run_id, task['task_id'], evidence, job=job)
            return {'intent': intent, 'attempt': update_attempt(intent, FIXED_TASK_UPDATE_PREFIX + str(uuid4()))}

        async def send(update):
            return await runtime.send_check(client, update, expires_at=expiry)

        waiting = command(selected, pending)
        wait = await send(waiting)
        assert wait['decision'] == 'waiting_job'
        assert await send(waiting) == wait
        assert await send(command(child, succeeded)) is None
        assert await send(command(selected, succeeded)) is None
        commands = [waiting]
        manual_first = campaign == 'manual-first'
        conflict = campaign == 'conflict'
        holds_read = campaign in held_reads
        if holds_read:
            async with asyncio.timeout(10):
                await held_reads[campaign][0].wait()
        if manual_first or holds_read:
            observation = {**succeeded, 'detail': 'different observation'} if conflict else succeeded
            manual = command(selected, observation, wait)
            result = await send(manual)
            assert result['decision'] == 'observed' and await send(manual) == result
            commands.append(manual)
        async with asyncio.timeout(12):
            while workflow_id not in deliveries:
                await asyncio.sleep(.03)
        if holds_read:
            still_held = await handle.query(runtime.Campaign.state)
            assert still_held['timer_readback']['status'] == 'scheduled'
            assert still_held['check_receipts']['fixed'] == result
            assert time.time() < due + 12
            held_reads[campaign][1].set()
            async with asyncio.timeout(10):
                while True:
                    description = await handle.describe()
                    state = await runtime.runtime_status(handle, description, opening, start_attempt_sha256=identity(attempt))
                    read = state['tasks']['fixed']['readback_observation']
                    if read['status'] == ('unknown' if conflict else 'available'):
                        if conflict:
                            assert read['reason'] == 'contradictory_evidence'
                        break
                    await asyncio.sleep(.03)
        later = command(child, succeeded)
        accepted = await send(later)
        assert accepted['decision'] == 'observed'
        commands.append(later)
        updates, readback, wake, terminal, followup_terminal, _ = await runtime.read_task_history(client, handle, opening, commands)
        assert terminal is None and followup_terminal is None
        selected_wake, = deliveries[workflow_id]
        assert wake['intent'] == selected_wake
        if manual_first or holds_read:
            assert selected_wake['source']['update_id'] == result['update_id']
            assert readback is None if manual_first else readback['observation_sha256'] == identity(succeeded)
        else:
            assert selected_wake['source']['activity_id'] == readback['activity_id']
            late = command(selected, succeeded, wait)
            assert await send(late) is None and await send(late) is None
            updates, completion, original_wake, terminal, followup_terminal, _ = await runtime.read_task_history(client, handle, opening, [*commands, late])
            assert terminal is None and followup_terminal is None
            failed = updates[late['attempt']['update_id']]
            assert failed['status'] == 'failed' and failed['receipt'] is None
            assert failed['reason'] == runtime.READBACK_ALREADY_ADMITTED
            assert completion['completed_event_id'] < failed['completed_event_id'] and original_wake['intent'] == selected_wake
            conflicting = command(selected, {**succeeded, 'detail': 'different observation'}, wait)
            assert await send(conflicting) is None
            assert (await handle.query(runtime.Campaign.state))['check_receipts'].keys() == {'dependent'}
        intent = stop_intent(opening, identity(attempt), run_id)
        stop = {'intent': intent, 'attempt': update_attempt(intent, f'ergora-campaign-stop:{uuid4()}')}
        assert (await runtime.send_stop(client, stop))['decision'] == 'accepted'
        assert (await handle.result(follow_runs=False))['phase'] == 'stopped'
        history = await handle.fetch_history()
        scheduled = [event.activity_task_scheduled_event_attributes.activity_type.name for event in history.events
                     if event.HasField('activity_task_scheduled_event_attributes')]
        expected = [RECIPIENT_ACTIVITY] if manual_first else [READBACK_ACTIVITY, RECIPIENT_ACTIVITY]
        assert scheduled == expected
        await Replayer(workflows=[runtime.Campaign], namespace=client.namespace).replay_workflow(history)

    async def exercise():
        async with await WorkflowEnvironment.start_local(
            ip='127.0.0.1', ui=False, dev_server_existing_path=os.environ['ERGORA_TEST_TEMPORAL_BIN'],
            dev_server_database_filename=str(tmp_path / 'intake.sqlite'),
        ) as service:
            queue = 'fixed-check-intake'
            async with Worker(service.client, task_queue=queue, workflows=[runtime.Campaign],
                              activities=[original_result, recipient]):
                await asyncio.gather(*(check(service.client, queue, name)
                                       for name in ('manual-first', 'timer-first', 'manual-held', 'conflict')))

    asyncio.run(exercise())


def test_training_result_source_only_accepts_its_guarded_full_result():
    from ergora.campaigns.records import (
        FIXED_TASK_UPDATE_PREFIX, TRAINING_RESULT_DIGESTS, check_intent, checked_readback, fixed_task_state,
        readback_grant, readback_id, readback_proof, readback_reference, readback_result, update_attempt,
        validate_check_command, validate_tasks,
    )

    locator = {'experiment_id': 'alpha', 'workflow_id': 'perf-experiment/alpha',
               'run_id': 'original-native-run', 'job_id': 'local-perf-alpha',
               'native_request_sha256': 'a'*64, 'attempt_sha256': 'b'*64}
    task = {'task_id': 'full', 'depends_on': [], 'source': {'kind': 'training_full_result', 'locator': locator},
            'readback': {'due_at': 20, 'deadline_at': 30}}
    validate_tasks([task])
    recipient = {'session_id': 'session', 'parent_run_id': 'parent', 'intent_id': 'training-notice',
                 'prompt': 'Acknowledge the readiness notice.', 'timeout_seconds': 30}
    validate_tasks([{**task, 'recipient': recipient}])
    with pytest.raises(ValueError, match='requires an exact session'):
        validate_tasks([{**task, 'recipient': {}}])
    for extra in ({'depends_on': ['full']}, {'wake_on_observe': True}):
        with pytest.raises(ValueError, match='requires one root task'):
            validate_tasks([{**task, **extra}])
    with pytest.raises(ValueError, match='complete original locator'):
        validate_tasks([{**task, 'source': {**task['source'], 'locator': {'experiment_id': 'alpha'}}}])
    live = {**task, 'source': {**task['source'], 'wait_for_live': True}}
    validate_tasks([{**live, 'recipient': recipient, 'recover_full_result_receipt': True}])
    reobserve = {'recipient': recipient, 'reobserve_full_result_after_reader_loss': True}
    validate_tasks([{**live, **reobserve}])
    for unsupported in ({**task, **reobserve}, {**live, **reobserve, 'recover_full_result_receipt': True}):
        with pytest.raises(ValueError, match='selected live full-result wait'):
            validate_tasks([unsupported])
    for invalid in ({'recover_full_result_receipt': False, 'recipient': recipient}, {'recover_full_result_receipt': True}):
        with pytest.raises(ValueError, match='selected original full training result and recipient'):
            validate_tasks([{**live, **invalid}])
    for kind in ('training_screen_result', 'training_gpu_release'):
        recovery_source = {'kind': kind, 'locator': locator}
        if kind == 'training_gpu_release':
            recovery_source['locator'] = {**locator, 'session_id': 'c'*32, 'lease_id': 'd'*64}
        with pytest.raises(ValueError, match='selected original full training result and recipient'):
            validate_tasks([{**task, 'source': recovery_source, 'recipient': recipient, 'recover_full_result_receipt': True}])
    for invalid in (False, 1, None):
        with pytest.raises(ValueError, match='explicitly selected managed full training result'):
            validate_tasks([{**task, 'source': {**task['source'], 'wait_for_live': invalid}}])
    for kind in ('training_screen_result', 'training_gpu_release'):
        with pytest.raises(ValueError, match='explicitly selected managed full training result'):
            validate_tasks([{**live, 'source': {**live['source'], 'kind': kind}}])
    with pytest.raises(ValueError, match='complete original locator'):
        validate_tasks([{**task, 'source': {**task['source'], 'locator': {**locator, 'wait_for_live': True}}}])
    with pytest.raises(ValueError, match='one original readback window'):
        validate_tasks([task, {**task, 'task_id': 'second'}])

    dependent = {'task_id': 'fixed', 'depends_on': ['full'], 'source': {}}
    opening = {'project': 'demo', 'project_revision': 3, 'workflow_id': 'campaign',
               'registration': {'sha256': 'c'*64}, 'plan': {'tasks': [task, dependent]}}
    run, start = 'original-campaign-run', 'd'*64
    grant = readback_grant(opening, run, task, None)
    activity_id = readback_id(grant)
    live_opening = {**opening, 'plan': {'tasks': [live, dependent]}}
    live_grant = readback_grant(live_opening, run, live, None)
    assert live_grant['source_sha256'] != grant['source_sha256']
    assert readback_id(live_grant) != activity_id
    assert activity_id.startswith('training-full-result-readback:')
    assert 'waiting_receipt_sha256' not in grant
    assert fixed_task_state(opening, start, run, {})['fixed']['status'] == 'waiting_dependencies'
    intent = check_intent(opening, start, run, 'full', 'e'*64)
    command = {'intent': intent, 'attempt': update_attempt(intent, FIXED_TASK_UPDATE_PREFIX +
                                                          'ffadc8b3-dd3a-4527-badb-b800466a27bd')}
    with pytest.raises(ValueError, match='admits only its guarded readback'):
        validate_check_command(opening, start, run, command)

    evidence = {'status': 'verified', 'project': 'demo', 'project_revision': 3, 'registration_sha256': 'c'*64,
                'locator': locator, 'native_result_state': 'SUCCEEDED',
                'local_gpu_lease': {'status': 'unknown', 'read_only': True, 'attempt_sha256': 'b'*64},
                **{key: 'e'*64 for key in TRAINING_RESULT_DIGESTS}}
    raw = {'activity_id': activity_id, 'observation': evidence, 'reader_cleanup_sha256': 'f'*64}
    for invalid in ({'native_result_state': 'RUNNING'}, {'project_revision': 2},
                    {'locator': {**locator, 'attempt_sha256': 'f'*64}}, {'native_result_sha256': None},
                    {'local_gpu_lease': {**evidence['local_gpu_lease'], 'attempt_sha256': 'c'*64}}):
        with pytest.raises(ValueError, match='original full training result'):
            readback_result(opening, task, activity_id, {**raw, 'observation': {**evidence, **invalid}})

    digest, accepted = readback_result(opening, task, activity_id, raw)
    selected = {'status': 'available', 'activity_id': activity_id,
                **readback_reference(grant), **readback_proof(digest, accepted, raw)}
    assert checked_readback(opening, run, None, selected) == selected
    assert selected['local_gpu_lease']['status'] == 'unknown'
    tasks = fixed_task_state(opening, start, run, {}, readback=selected)
    assert tasks['full']['status'] == 'observed' and tasks['full']['receipt'] is None
    assert tasks['fixed']['status'] == 'ready'


@pytest.mark.parametrize(('state', 'performance', 'decision'), (
    ('SCREEN_REJECTED', 'unavailable', 'rejected'),
    ('SCREEN_COMPLETED', 'promising', 'promising'),
    ('SCREEN_COMPLETED', 'no_gain', 'stop_direction'),
    ('SCREEN_COMPLETED', 'unavailable', 'inconclusive'),
))
def test_training_screen_readback_preserves_its_exact_decision(state, performance, decision):
    from ergora.campaigns.records import (
        TRAINING_SCREEN_ACTIVITY, TRAINING_SCREEN_DIGESTS, checked_readback, readback_activity,
        readback_grant, readback_id, readback_proof, readback_reference, readback_result, validate_tasks, wake_intent,
    )

    locator = {'experiment_id': 'alpha', 'workflow_id': 'perf-experiment/alpha',
               'run_id': 'original-native-run', 'job_id': 'local-perf-alpha',
               'native_request_sha256': 'a' * 64, 'attempt_sha256': 'b' * 64}
    task = {'task_id': 'screen', 'depends_on': [], 'source': {'kind': 'training_screen_result', 'locator': locator},
            'readback': {'due_at': 20, 'deadline_at': 30},
            'recipient': {'session_id': 'session', 'parent_run_id': 'parent', 'intent_id': 'screen-notice',
                          'prompt': 'Read the selected original screen decision.', 'timeout_seconds': 30}}
    validate_tasks([task])
    opening = {'project': 'demo', 'project_revision': 3, 'workflow_id': 'campaign',
               'registration': {'sha256': 'c' * 64}, 'plan': {'tasks': [task], 'limits': {'expires_at': 60}}}
    run_id = 'original-campaign-run'
    grant = readback_grant(opening, run_id, task, None)
    activity_id = readback_id(grant)
    assert readback_activity(task) == TRAINING_SCREEN_ACTIVITY
    assert activity_id.startswith('training-screen-result-readback:')
    rejected = state == 'SCREEN_REJECTED'
    check = {'id': 'finite', 'kind': 'finite', 'status': 'FAIL' if rejected else 'PASS', 'contract_sha256': 'd' * 64}
    failure = {'path': 'screen-first-failure.json', 'sha256': 'e' * 64, 'bytes': 48} if rejected else None
    diagnostics = {'checks': [check], 'checks_not_run': ['behavior'] if rejected else [],
                   'first_failure_ref': failure, 'profile_receipt_ref': None}
    lease = {'status': 'unknown', 'read_only': True, 'attempt_sha256': locator['attempt_sha256']}
    observation = {'status': 'verified', 'project': 'demo', 'project_revision': 3, 'registration_sha256': 'c' * 64,
                   'locator': locator, 'native_result_state': state, 'performance_state': performance, 'decision': decision,
                   'verification_experiment_id': 'alpha-full', 'full_execution_authorized': False,
                   'diagnostics': diagnostics, 'local_gpu_lease': lease,
                   **dict.fromkeys(TRAINING_SCREEN_DIGESTS, 'e' * 64)}
    raw = {'activity_id': activity_id, 'observation': observation, 'reader_cleanup_sha256': 'f' * 64}
    evidence, job = readback_result(opening, task, activity_id, raw)
    readback = {'status': 'available', 'activity_id': activity_id, **readback_reference(grant),
                **readback_proof(evidence, job, raw)}
    assert checked_readback(opening, run_id, None, readback) == readback
    wake = wake_intent(opening, run_id, task, readback)
    assert wake['source']['decision'] == decision and wake['source']['native_result_state'] == state
    assert wake['source']['diagnostics'] == diagnostics and wake['source']['local_gpu_lease'] == lease
    assert wake['source']['full_execution_authorized'] is False
    for changes in ({'native_result_state': 'SUCCEEDED'}, {'native_result_state': 'FAILED'},
                    {'native_result_state': 'CANCELLED'}, {'decision': 'approved'},
                    {'verification_experiment_id': locator['experiment_id']}, {'full_execution_authorized': True},
                    {'diagnostics': None}, {'screen_result_sha256': None},
                    {'locator': {**locator, 'run_id': 'different-run'}},
                    {'locator': {**locator, 'attempt_sha256': '1' * 64}},
                    {'local_gpu_lease': {**lease, 'attempt_sha256': '1' * 64}}):
        with pytest.raises(ValueError, match='exact verified original screen decision'):
            readback_result(opening, task, activity_id, {**raw, 'observation': {**observation, **changes}})
    with pytest.raises(ValueError, match='exact successful original full training result'):
        readback_result(opening, {**task, 'source': {**task['source'], 'kind': 'training_full_result'}}, activity_id, raw)
    with pytest.raises(ValueError, match='original evidence'):
        checked_readback(opening, run_id, None, {**readback, 'full_execution_authorized': True})


def test_training_gpu_release_requires_an_exact_accepted_original_lease():
    from ergora.campaigns.records import (
        TRAINING_GPU_RELEASE_ACTIVITY, checked_readback, readback_activity, readback_grant, readback_id,
        readback_proof, readback_reference, readback_result, validate_tasks, wake_intent,
    )

    locator = {'experiment_id': 'alpha', 'workflow_id': 'perf-experiment/alpha',
               'run_id': 'original-native-run', 'job_id': 'local-perf-alpha',
               'native_request_sha256': 'a' * 64, 'attempt_sha256': 'b' * 64,
               'session_id': 'c' * 32, 'lease_id': 'd' * 64}
    recipient = {'session_id': 'session', 'parent_run_id': 'parent', 'intent_id': 'release-notice',
                 'prompt': 'Read the selected original resource release.', 'timeout_seconds': 30}
    task = {'task_id': 'release', 'depends_on': [], 'source': {'kind': 'training_gpu_release', 'locator': locator},
            'readback': {'due_at': 20, 'deadline_at': 30}, 'recipient': recipient}
    validate_tasks([task])
    with pytest.raises(ValueError, match='complete original locator'):
        validate_tasks([{**task, 'source': {**task['source'], 'locator': {
            key: value for key, value in locator.items() if key != 'lease_id'}}}])
    opening = {'project': 'demo', 'project_revision': 3, 'workflow_id': 'campaign',
               'registration': {'sha256': 'e' * 64}, 'plan': {'tasks': [task], 'limits': {'expires_at': 45}}}
    run_id = 'original-campaign-run'
    grant = readback_grant(opening, run_id, task, None)
    activity_id = readback_id(grant)
    assert readback_activity(task) == TRAINING_GPU_RELEASE_ACTIVITY
    assert activity_id.startswith('training-gpu-release-readback:')
    release = {'sequence': 5, 'proof_ref': {'relative_path': f'proofs/{locator["lease_id"]}/stopped.json',
                                           'raw_sha256': 'f' * 64}}
    lease = {'status': 'released', 'read_only': True, 'release_ref': release, 'request_id': '1' * 64,
             'request_sha256': '2' * 64, **{key: locator[key] for key in ('session_id', 'lease_id', 'attempt_sha256')}}
    observation = {'status': 'verified', 'project': 'demo', 'project_revision': 3, 'registration_sha256': 'e' * 64,
                   'locator': locator, 'local_gpu_lease': lease}
    raw = {'activity_id': activity_id, 'observation': observation, 'reader_cleanup_sha256': '3' * 64}
    digest, accepted = readback_result(opening, task, activity_id, raw)
    readback = {'status': 'available', 'activity_id': activity_id, **readback_reference(grant),
                **readback_proof(digest, accepted, raw)}
    assert checked_readback(opening, run_id, None, readback) == readback
    wake = wake_intent(opening, run_id, task, readback)
    assert wake['source']['source_kind'] == 'training_gpu_release'
    assert wake['source']['local_gpu_lease'] == lease
    assert 'native_result_state' not in wake['source'] and 'native_result_sha256' not in wake['source']

    for bad in (None, {**lease, 'status': 'consumed', 'release_ref': None}, {**lease, 'status': 'unknown'},
                {**lease, 'attempt_sha256': '4' * 64}, {**lease, 'lease_id': '5' * 64},
                {**lease, 'session_id': '1' * 32}, {**lease, 'release_ref': {**release, 'proof_ref': None}}):
        with pytest.raises(ValueError, match='exact accepted original GPU release'):
            readback_result(opening, task, activity_id, {**raw, 'observation': {**observation, 'local_gpu_lease': bad}})
        with pytest.raises(ValueError, match='original evidence'):
            checked_readback(opening, run_id, None, {**readback, 'local_gpu_lease': bad})


@pytest.mark.parametrize('kind', ('fixed_check', 'training_full_result', 'training_screen_result', 'training_gpu_release'))
@pytest.mark.parametrize(('case', 'stamp', 'error'), (
    ('before-cutoff', (39, 999_999_999), None),
    ('at-cutoff', (40, 0), 'original cutoff'),
    ('after-cutoff', (40, 1), 'original cutoff'),
    ('missing-clock', None, None),
    ('invalid-clock', (40, -1), None),
    ('wrong-schedule-type', (39, 0), 'original grant'),
    ('wrong-start-type', (39, 0), 'original Activity attempt'),
    ('wrong-completed-type', (39, 0), 'original Activity attempt'),
    ('nonpositive-schedule', (39, 0), 'original grant'),
    ('start-before-schedule', (39, 0), 'original Activity attempt'),
    ('completion-shares-start', (39, 0), 'original Activity attempt'),
))
def test_original_completion_history_checks_ancestry_and_known_cutoff(monkeypatch, kind, case, stamp, error):
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.converter import DataConverter
    from ergora.campaigns import records, workflow as runtime

    task = {'task_id': 'read', 'source': {'kind': kind}, 'readback': {'due_at': 20, 'deadline_at': 40}}
    opening = {'task_queue': 'original-queue', 'plan': {'tasks': [task]}}
    grant = records.readback_grant(opening, 'original-run', task, None)
    activity = records.readback_id(grant)
    result = {'reader_cleanup_sha256': 'a'*64}
    validated = []

    def accept(opened, selected, activity_id, payload):
        assert (opened, selected, activity_id, payload) == (opening, task, activity, result)
        validated.append(payload)
        return 'b'*64, {'status': 'succeeded'}

    monkeypatch.setattr(runtime, 'readback_result', accept)

    async def exercise():
        converter = DataConverter.default
        schedule_id = 0 if case == 'nonpositive-schedule' else 11
        start_id = 10 if case == 'start-before-schedule' else 12
        finish_id = start_id if case == 'completion-shares-start' else 13
        events = [
            HistoryEvent(event_id=schedule_id, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED,
                         event_time={'seconds': 20}, activity_task_scheduled_event_attributes={
                             'activity_id': activity, 'activity_type': {'name': records.readback_activity(task)},
                             'task_queue': {'name': opening['task_queue']}, 'retry_policy': {'maximum_attempts': 1},
                             'input': {'payloads': await converter.encode([grant])}}),
            HistoryEvent(event_id=start_id, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED,
                         event_time={'seconds': 21}, activity_task_started_event_attributes={
                             'scheduled_event_id': schedule_id, 'attempt': 1}),
            HistoryEvent(event_id=finish_id, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED,
                         activity_task_completed_event_attributes={
                             'scheduled_event_id': schedule_id, 'started_event_id': start_id,
                             'result': {'payloads': await converter.encode([result])}}),
        ]
        wrong_types = {'wrong-schedule-type': 0, 'wrong-start-type': 1, 'wrong-completed-type': 2}
        if case in wrong_types:
            events[wrong_types[case]].event_type = EventType.EVENT_TYPE_TIMER_FIRED
        if stamp is not None:
            events[-1].event_time.seconds, events[-1].event_time.nanos = stamp
        return await runtime._readback_history(converter, events, opening, task, grant, activity, [])

    if error is not None:
        with pytest.raises(ValueError, match=error):
            asyncio.run(exercise())
        assert validated == []
    else:
        completion, terminal = asyncio.run(exercise())
        assert terminal is None and validated == [result]
        assert completion['scheduled_event_id'] == 11 and completion['completed_event_id'] == 13
        assert completion['observation_sha256'] == 'b'*64
        assert ('completed' in completion['timing']['events']) is (case == 'before-cutoff')


@pytest.mark.parametrize(('timestamp', 'fault'), (
    (None, 'cutoff'),
    ((39, 1_000_000_000), 'cutoff'),
    ((-62_135_596_801, 0), 'cutoff'),
    ((40, 0), 'cutoff'),
    ((39, 999_999_999), None),
    ((39, 0), 'wrong-schedule-type'),
    ((39, 0), 'wrong-start-type'),
    ((39, 0), 'wrong-completion-type'),
    ((39, 0), 'original-start-before-schedule'),
    ((39, 0), 'recovery-start-before-schedule'),
    ((39, 0), 'completion-before-start'),
    ((39, 0), 'malformed-result'),
), ids=['absent', 'invalid-nanos', 'invalid-seconds', 'at-cutoff', 'before-cutoff',
        'schedule-type', 'start-type', 'completion-type', 'original-order', 'recovery-order', 'completion-order',
        'malformed-result'])
@pytest.mark.parametrize('full_result', (False, True), ids=('release', 'full-result'))
def test_receipt_recovery_history_requires_original_activity_lineage(monkeypatch, timestamp, fault, full_result):
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType, TimeoutType
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.converter import DataConverter
    from ergora.campaigns import records, workflow as runtime

    opening = {'task_queue': 'original-queue'}
    grant = {'deadline_at': 40, 'source_sha256': 'a'*64}
    if full_result:
        task = {'task_id': 'full', 'recover_full_result_receipt': True}
        recovery_type = records.FULL_RESULT_RECOVERY_ACTIVITY
    else:
        task = {'task_id': 'release', 'recover_release_receipt': True}
        grant['source_kind'] = 'training_gpu_release'
        recovery_type = records.RELEASE_RECOVERY_ACTIVITY
    recovery = records.receipt_recovery_id(grant)
    original_id = records.readback_id(grant)
    original_result = {'reader_cleanup_sha256': 'b'*64}
    reply = {'original_result': original_result, 'recovery_activity_id': recovery, 'recovery_receipt_sha256': 'c'*64}
    old = [
        HistoryEvent(event_id=11, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED,
                     activity_task_scheduled_event_attributes={'activity_id': original_id}),
        HistoryEvent(event_id=12, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED,
                     activity_task_started_event_attributes={'scheduled_event_id': 11, 'attempt': 1}),
        HistoryEvent(event_id=13, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_TIMED_OUT,
                     activity_task_timed_out_event_attributes={
            'scheduled_event_id': 11, 'started_event_id': 12, 'failure': {
                'timeout_failure_info': {'timeout_type': TimeoutType.TIMEOUT_TYPE_HEARTBEAT}}}),
    ]
    validated = []

    def readback_result(opened, selected, activity_id, result):
        assert (opened, selected, activity_id, result) == (opening, task, original_id, original_result)
        if fault == 'malformed-result':
            raise KeyError('local_gpu_lease')
        validated.append(result)
        return 'd'*64, {'status': 'succeeded'}

    monkeypatch.setattr(runtime, 'readback_result', readback_result)

    async def exercise():
        converter = DataConverter.default
        events = [
            HistoryEvent(event_id=19, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED,
                         activity_task_scheduled_event_attributes={
                'activity_id': recovery, 'activity_type': {'name': recovery_type},
                'task_queue': {'name': opening['task_queue']}, 'retry_policy': {'maximum_attempts': 1},
                'input': {'payloads': await converter.encode([grant])}}),
            HistoryEvent(event_id=20, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED,
                         activity_task_started_event_attributes={'scheduled_event_id': 19, 'attempt': 1}),
            HistoryEvent(event_id=21, event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED,
                         activity_task_completed_event_attributes={
                'scheduled_event_id': 19, 'started_event_id': 20,
                'result': {'payloads': await converter.encode([reply])}}),
        ]
        if timestamp is not None:
            events[-1].event_time.seconds, events[-1].event_time.nanos = timestamp
        wrong_types = {'wrong-schedule-type': 0, 'wrong-start-type': 1, 'wrong-completion-type': 2}
        if fault in wrong_types:
            events[wrong_types[fault]].event_type = EventType.EVENT_TYPE_MARKER_RECORDED
        if fault == 'original-start-before-schedule':
            old[1].event_id = 10
            old[2].activity_task_timed_out_event_attributes.started_event_id = 10
        if fault == 'recovery-start-before-schedule':
            events[1].event_id = 18
            events[2].activity_task_completed_event_attributes.started_event_id = 18
        if fault == 'completion-before-start':
            events[2].event_id = 20
        return await runtime._readback_followup_history(
            converter, old, events, opening, task, grant, original_id, include_terminal=full_result)

    if fault is None:
        completion, terminal = asyncio.run(exercise())
        assert terminal is None
        assert completion['recovery_history']['completed_event_id'] == 21
        assert validated == [original_result]
    else:
        message = {
            'wrong-schedule-type': 'authorized original read',
            'original-start-before-schedule': 'exact original heartbeat timeout',
            'malformed-result': 'invalid original result',
        }.get(fault, 'original attempt or cutoff')
        with pytest.raises(ValueError, match=message):
            asyncio.run(exercise())
        assert validated == []


@pytest.mark.parametrize(('case', 'full_result'), (
    *((case, False) for case in ('exact', 'stop', 'expired', 'missing', 'foreign_guard', 'foreign_attempt',
                                 'unknown_lease', 'unreaped_child', 'original_worker_live')),
    ('exact', True), ('original_worker_live', True), ('original_worker_extra', True),
    ('original_worker_exited', True), ('original_worker_unknown', True), ('original_reader_exited_unreaped', True),
    ('original_worker_padded_ticks', True), ('original_worker_unicode_ticks', True), ('original_worker_zero_ticks', True),
))
def test_receipt_recovery_only_accepts_original_receipt_and_reaped_processes(tmp_path, monkeypatch, case, full_result):
    from dataclasses import replace
    pytest.importorskip('temporalio')

    from temporalio.testing import ActivityEnvironment
    from ergora.campaigns import readback, records

    locator = {'experiment_id': 'alpha', 'workflow_id': 'perf-experiment/alpha',
               'run_id': 'training-run', 'job_id': 'local-perf-alpha',
               'native_request_sha256': 'a'*64, 'attempt_sha256': 'b'*64}
    task = {'task_id': 'result', 'depends_on': [], 'readback': {'due_at': 20, 'deadline_at': 40},
            'recipient': {'session_id': 'session', 'parent_run_id': 'parent', 'intent_id': 'notice',
                          'prompt': 'Read the original training observation.', 'timeout_seconds': 20}}
    if full_result:
        task.update(source={'kind': 'training_full_result', 'locator': locator}, recover_full_result_receipt=True)
    else:
        locator.update(session_id='c'*32, lease_id='d'*64)
        task.update(source={'kind': 'training_gpu_release', 'locator': locator}, recover_release_receipt=True)
    records.validate_tasks([task])
    opening = {'project': 'demo', 'project_revision': 1, 'workflow_id': 'original-campaign',
               'registration': {'sha256': 'e'*64}, 'plan': {'tasks': [task]}}
    run = 'original-run'
    start = {'attempt': 'original'}
    grant = records.readback_grant(opening, run, task, None)
    activity_id = records.readback_id(grant)
    worker, guard, model = [{'pid': process, 'boot_id': 'current-boot', 'start_ticks': '42'}
                            for process in (10001, 10002, 10003)]
    cleanup = {'activity_id': activity_id, 'reaped_at_monotonic': 22,
               'receipt': {'kind': 'supervised-process-cleanup', 'schema_version': 1, 'owner': guard,
                           'model': model, 'model_waited': True, 'remaining_children': [], 'returncode': 0}}
    observation = {'status': 'verified', 'project': 'demo', 'project_revision': 1,
                   'registration_sha256': 'e'*64, 'locator': locator, 'local_gpu_lease': None}
    if full_result:
        observation.update(native_result_state='SUCCEEDED', **{field: 'f'*64 for field in records.TRAINING_RESULT_DIGESTS})
    else:
        observation['local_gpu_lease'] = {
            'status': 'released', 'read_only': True, 'request_id': '1'*64, 'request_sha256': '2'*64,
            **{key: locator[key] for key in ('session_id', 'lease_id', 'attempt_sha256')},
            'release_ref': {'sequence': 5, 'proof_ref': {'relative_path': f'proofs/{locator["lease_id"]}/stopped.json',
                                                        'raw_sha256': 'f'*64}}}
    result = {'activity_id': activity_id, 'reader_cleanup_sha256': records.identity(cleanup),
              'observation': observation}
    documents = {'readback-attempt': {'activity_id': activity_id, 'worker': worker, 'grant': grant},
                 'readback-guard': {'activity_id': activity_id, 'worker': worker, 'guard': guard,
                                    'deadline_monotonic': 40, 'work_cutoff_monotonic': 39},
                 'readback-result': result, 'readback-cleanup': cleanup}
    worker_observed = dict(worker)
    if case == 'original_worker_extra':
        worker['extra'] = True
    elif case == 'original_worker_padded_ticks':
        worker['start_ticks'] = '0' + worker_observed['start_ticks']
    elif case == 'original_worker_unicode_ticks':
        worker['start_ticks'] = '\u0664\u0662'
    elif case == 'original_worker_zero_ticks':
        worker['start_ticks'] = '0'
    if case == 'missing':
        del documents['readback-result']
    elif case == 'foreign_guard':
        documents['readback-guard']['guard'] = worker
    elif case == 'foreign_attempt':
        documents['readback-attempt']['activity_id'] = 'foreign-activity'
    elif case == 'unknown_lease':
        observation['local_gpu_lease'].update(status='unknown', release_ref=None)
    elif case == 'unreaped_child':
        cleanup['receipt']['model_waited'] = False
        result['reader_cleanup_sha256'] = records.identity(cleanup)
    files = SimpleNamespace(home=tmp_path, _read=documents.get, load=lambda: (opening, start, {'run_id': run}),
                            load_stop=lambda *_: ({} if case == 'stop' else None, None, None))
    State(tmp_path)
    monkeypatch.setattr(readback, 'require_check_project', lambda *_: None)
    monkeypatch.setattr(readback.time, 'time', lambda: 41 if case == 'expired' else 30)

    monkeypatch.setattr(readback.time, 'monotonic', lambda: 30)

    def observe(pid):
        if pid == worker['pid'] and case == 'original_worker_live':
            return worker
        if pid == model['pid'] and case == 'original_reader_exited_unreaped':
            raise ValueError('Original process has exited')
        if pid in (worker['pid'], guard['pid'], model['pid']):
            raise FileNotFoundError
        return {'pid': pid, 'boot_id': 'current-boot', 'start_ticks': '100'}

    def observe_worker(pid):
        assert pid == worker['pid']
        if case in ('original_worker_live', 'original_worker_extra', 'original_worker_padded_ticks',
                    'original_worker_unicode_ticks'):
            return 'S', worker_observed
        if case == 'original_worker_exited':
            return 'Z', worker_observed
        if case == 'original_worker_unknown':
            raise PermissionError('Original process status could not be read')
        raise FileNotFoundError

    monkeypatch.setattr(readback.processes, 'identity', observe)
    monkeypatch.setattr(readback.processes, 'observe_process', observe_worker)
    recovery = records.receipt_recovery_id(grant)
    env = ActivityEnvironment()
    env.info = replace(env.info, workflow_id=opening['workflow_id'], workflow_run_id=run,
                       activity_id=recovery, activity_type=records.receipt_recovery_activity(task))
    handler = readback.CampaignReadback(files, opening, start, run)

    async def call():
        return await env.run(handler.recovery_activity_for(task), grant)

    if case in ('exact', 'original_worker_exited', 'original_worker_zero_ticks'):
        assert asyncio.run(call()) == {'recovery_activity_id': recovery, 'original_result': result,
                                       'recovery_receipt_sha256': records.identity(documents)}
    elif case == 'original_worker_unknown':
        with pytest.raises(PermissionError, match='could not be read'):
            asyncio.run(call())
    else:
        with pytest.raises(ValueError):
            asyncio.run(call())


@pytest.mark.parametrize('case', ('exact', 'success-without-result', 'published', 'live', 'foreign',
                                 'unknown', 'boot', 'unreaped', 'stop', 'cancel', 'cutoff', 'duplicate',
                                 'lock-release', 'lock-stop', 'lock-wall-cutoff', 'lock-monotonic-cutoff',
                                 'lock-cancel', 'lock-changed-proof'))
def test_full_result_reobservation_requires_a_closed_unpublished_reader(tmp_path, monkeypatch, case):
    pytest.importorskip('temporalio')
    from ergora.campaigns import readback, records
    from ergora.storage.state import file_lock

    original = {'run_id': 'original-run', 'due_at': 20, 'deadline_at': 40}
    opening, start = {'identity': 'original-opening'}, {'identity': 'original-start'}
    activity = records.readback_id(original)
    worker, guard, model = [{'pid': pid, 'boot_id': 'current-boot', 'start_ticks': '42'}
                            for pid in (10001, 10002, 10003)]
    documents = {
        'readback-attempt': {'grant': original, 'activity_id': activity, 'worker': worker},
        'readback-guard': {'activity_id': activity, 'worker': worker, 'guard': guard,
                           'deadline_monotonic': 40, 'work_cutoff_monotonic': 39},
        'readback-cleanup': {'activity_id': activity, 'reaped_at_monotonic': 22, 'receipt': {
            'kind': 'supervised-process-cleanup', 'schema_version': 1, 'owner': guard,
            'model': model, 'model_waited': True, 'remaining_children': [], 'returncode': -signal.SIGKILL}},
    }
    if case == 'success-without-result':
        documents['readback-cleanup']['receipt']['returncode'] = 0
    elif case == 'published':
        documents['readback-result'] = {'already': 'published'}
    elif case == 'boot':
        worker['boot_id'] = 'original-other-boot'
    elif case == 'unreaped':
        documents['readback-cleanup']['receipt']['model_waited'] = False
    elif case == 'cancel':
        documents['readback-cancel'] = {'activity_id': activity}
    elif case == 'duplicate':
        documents['reobservation-attempt'] = {'original': 'admission'}

    def write(name, packet, *, before_publish):
        before_publish()
        if name in documents:
            raise FileExistsError
        documents[name] = packet

    files = SimpleNamespace(lock=tmp_path / '.start.lock', _read=documents.get, write=write,
                            load=lambda: (opening, start, {'run_id': original['run_id']}),
                            load_stop=lambda *_: ({} if case == 'stop' else None, None, None))
    clock = {'wall': 30, 'monotonic': 39 if case == 'cutoff' else 30}
    monkeypatch.setattr(readback, 'time', SimpleNamespace(time=lambda: clock['wall'], monotonic=lambda: clock['monotonic']))

    def observe_worker(pid):
        assert pid == worker['pid']
        if case == 'live':
            return 'S', worker
        if case == 'foreign':
            return 'S', {**worker, 'start_ticks': '43'}
        if case == 'unknown':
            raise PermissionError('Original Worker state is unknown')
        raise FileNotFoundError

    def observe_other(pid):
        if pid == os.getpid():
            return {'pid': pid, 'boot_id': 'current-boot', 'start_ticks': '100'}
        raise FileNotFoundError

    monkeypatch.setattr(readback.processes, 'observe_process', observe_worker)
    monkeypatch.setattr(readback.processes, 'identity', observe_other)
    activity_runner = readback.CampaignReadback(files, opening, start, original['run_id'])
    packet = {'grant': original, 'activity_id': records.reobservation_id(original)}
    async def exercise():
        if not case.startswith('lock-'):
            return await activity_runner._admit_reobservation(original, packet)
        heartbeat = asyncio.Event()

        def observe_heartbeat(activity_id):
            assert activity_id == packet['activity_id']
            heartbeat.set()

        monkeypatch.setattr(readback.activity, 'heartbeat', observe_heartbeat)
        with file_lock(files.lock):
            admission = asyncio.create_task(activity_runner._admit_reobservation(original, packet))
            try:
                await asyncio.wait_for(heartbeat.wait(), 2)
                assert 'reobservation-attempt' not in documents and not admission.done()
                if case == 'lock-stop':
                    documents['stop-intent'] = {'original': 'stop'}
                elif case == 'lock-wall-cutoff':
                    clock['wall'] = 40
                elif case == 'lock-monotonic-cutoff':
                    clock['monotonic'] = 39
                elif case == 'lock-cancel':
                    admission.cancel()
                elif case == 'lock-changed-proof':
                    documents['readback-guard']['work_cutoff_monotonic'] = 38
                if case in ('lock-stop', 'lock-wall-cutoff', 'lock-monotonic-cutoff', 'lock-cancel'):
                    return await asyncio.wait_for(admission, 2)
            except BaseException:
                if not admission.done():
                    admission.cancel()
                    await asyncio.gather(admission, return_exceptions=True)
                raise
        return await asyncio.wait_for(admission, 2)

    if case in ('exact', 'lock-release'):
        before = records.identity(documents)
        assert asyncio.run(exercise()) == before
        assert documents['reobservation-attempt'] == {**packet, 'interruption_sha256': before}
    else:
        expected = asyncio.CancelledError if case == 'lock-cancel' else (ValueError, OSError)
        message = {'lock-stop': 'no longer admits',
                   'lock-wall-cutoff': 'original work cutoff',
                   'lock-monotonic-cutoff': 'original work cutoff',
                   'lock-changed-proof': 'proof changed while waiting'}.get(case)
        with pytest.raises(expected, match=message):
            asyncio.run(exercise())
        assert documents.get('reobservation-attempt') == ({'original': 'admission'} if case == 'duplicate' else None)


@pytest.mark.parametrize('phase', ('release', 'cutoff', 'stop_waiting', 'stop_acquired', 'stop_before_link', 'write_error'))
def test_training_publication_waits_only_for_its_original_lock_and_window(monkeypatch, phase):
    from contextlib import contextmanager

    pytest.importorskip('temporalio')
    from ergora.campaigns import readback

    clock = [0.]
    accesses, published = [], []
    acquired = prepared = False

    def sleep(seconds):
        assert 0 < seconds <= .025
        clock[0] += seconds

    @contextmanager
    def lock(path, *, blocking):
        nonlocal acquired
        assert path == 'original-lock' and blocking is False
        accesses.append(clock[0])
        if len(accesses) == 1 or phase == 'cutoff':
            raise BlockingIOError()
        acquired = True
        yield

    def stopped():
        return ((phase == 'stop_waiting' and bool(accesses))
                or (phase == 'stop_acquired' and acquired)
                or (phase == 'stop_before_link' and prepared))

    def write(name, record, *, before_publish):
        nonlocal prepared
        prepared = True
        if phase == 'write_error':
            raise BlockingIOError('original write failure')
        before_publish()
        published.append((name, record))

    monkeypatch.setattr(readback, 'time', SimpleNamespace(monotonic=lambda: clock[0], sleep=sleep))
    monkeypatch.setattr(readback, 'file_lock', lock)
    files = SimpleNamespace(lock='original-lock', write=write)
    result = {'activity_id': 'original'}
    if phase == 'release':
        readback._publish_training_result(files, result, .05, stopped)
        assert published == [('readback-result', result)]
    elif phase == 'cutoff':
        with pytest.raises(TimeoutError, match='publication cutoff'):
            readback._publish_training_result(files, result, .05, stopped)
        assert clock[0] == .05 and not prepared
    elif phase == 'write_error':
        with pytest.raises(BlockingIOError, match='original write failure'):
            readback._publish_training_result(files, result, .05, stopped)
    else:
        with pytest.raises(ValueError, match='no longer admits'):
            readback._publish_training_result(files, result, .05, stopped)
        assert prepared is (phase == 'stop_before_link')
    assert len(accesses) == (1 if phase == 'stop_waiting' else 2)
    if phase != 'release':
        assert not published


@pytest.mark.parametrize('training', [True, False])
def test_only_training_readback_projects_its_pending_local_stop_to_the_child(training):
    async def stop_receipt(*args):
        return None

    root = {'task_id': 'root', 'source': {'kind': 'training_full_result'} if training else {},
            'readback': {'due_at': 15, 'deadline_at': 20}}
    opening = {'plan': {'tasks': [root]}}
    tasks = {'fixed': {'status': 'ready', 'eligible': True}, 'root': {'status': 'observed', 'eligible': False}}

    async def status(*args, **kwargs):
        return {'tasks': tasks, 'workflow_state_status': 'observed'}

    runtime = SimpleNamespace(RPC_SECONDS=1, read_stop=stop_receipt, runtime_status=status, RPCError=RuntimeError)
    handle = SimpleNamespace(run_id='original')
    description = SimpleNamespace(run_id='original', status=SimpleNamespace(name='RUNNING'))
    stop = ({'run_id': 'original'}, {'update_id': 'original-stop'}, None)
    output = {'attempt_sha256': 'digest', 'stop': application._stop_snapshot(stop, local_fence=True)}
    result = asyncio.run(application._observe(runtime, output, None, handle, description, opening, stop, True))
    assert result['stop']['local_fence_saved'] is True and result['stop']['remote_status'] == 'not_found'
    assert result['tasks']['root']['status'] == 'observed'
    assert result['tasks']['fixed'] == {'status': 'ready', 'eligible': not training}


@pytest.mark.parametrize('view', ('live', 'history', 'missing', 'wake-contradictory'))
def test_training_task_view_retains_verified_history_without_live_admission(view):
    kind = 'training_full_result' if view == 'wake-contradictory' else 'training_gpu_release'
    root = {'task_id': 'training', 'depends_on': [], 'source': {'kind': kind},
            'readback': {'due_at': 15, 'deadline_at': 20}}
    dependent = {'task_id': 'fixed', 'depends_on': ['training'], 'source': {}}
    opening = {'plan': {'tasks': [root, dependent]}}
    handle = SimpleNamespace(run_id='original')
    description = SimpleNamespace(run_id='original', status=SimpleNamespace(name='RUNNING'))
    live = {'training': {'status': 'observed', 'eligible': False}, 'fixed': {'status': 'ready', 'eligible': True}}
    completion = {'task_id': 'training', 'activity_id': 'original-read', 'completed_event_id': 13}
    terminal = {'status': 'timed_out', 'terminal_event_id': 10}

    async def original(client, plan, attempt, run):
        assert (plan, run) == (opening, 'original')
        return handle, description

    async def state(*args, **kwargs):
        if view == 'live':
            return {'workflow_state_status': 'observed', 'tasks': live}
        return {'workflow_state_status': 'unavailable'}

    async def history(client, selected, plan, commands):
        assert (selected, plan, commands) == (handle, opening, ())
        if view == 'wake-contradictory':
            pytest.importorskip('temporalio')
            from ergora.campaigns.workflow import WakeHistoryConflict

            raise WakeHistoryConflict(ValueError('Wake start is contradictory'), ({}, completion, terminal, None))
        return {}, None if view == 'missing' else completion, None, None, None, None

    runtime = SimpleNamespace(RPC_SECONDS=1, original=original, runtime_status=state,
                              read_task_history=history, RPCError=RuntimeError)
    initial = {'attempt_sha256': 'digest', 'workflow_state_status': 'not_observed'}
    result = asyncio.run(application._read_original(runtime, initial, opening, {}, 'original',
                                                    client=object(), read_state=True))
    if view == 'live':
        assert result['tasks'] == live
    elif view in ('history', 'wake-contradictory'):
        assert result['workflow_state_status'] == 'unavailable'
        assert result['readback_completion'] == completion
        assert result['tasks'] == {'training': {**root, 'status': 'observed', 'receipt': None,
                                               'eligible': False, 'state_source': 'history'}}
        if view == 'wake-contradictory':
            assert result['task_observation_history_status'] == 'contradictory'
            assert result['readback_terminal'] == terminal
            assert 'recipient_history' not in result and 'recipient' not in result['readback_completion']
            assert '_wake_history_conflict' not in result
    else:
        assert 'tasks' not in result
        assert 'readback_completion' not in result


@pytest.mark.parametrize('case', ('failed', 'unbounded_cause', 'timed_out', 'before_start_timeout',
                                 'schedule_to_start_after_start', 'heartbeat_without_start', 'canceled',
                                 'cancel_without_start', 'request_before_start', 'missing_cancel_request',
                                 'foreign_cancel_request', 'wrong_cancel_link', 'wrong_cancel_event_type',
                                 'wrong_schedule_event_type', 'wrong_start_event_type', 'wrong_terminal_event_type',
                                 'missing', 'unavailable', 'foreign_schedule', 'foreign_start',
                                 'foreign_start_standard', 'wrong_attempt', 'duplicate', 'live'))
def test_full_result_history_exposes_only_exact_terminal_blocker(case):
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType, TimeoutType
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.converter import DataConverter
    from ergora.campaigns import records, workflow

    locator = {'experiment_id': 'alpha', 'workflow_id': 'perf-experiment/alpha',
               'run_id': 'training-run', 'job_id': 'local-perf-alpha',
               'native_request_sha256': 'a'*64, 'attempt_sha256': 'b'*64}
    root = {'task_id': 'full', 'depends_on': [], 'source': {'kind': 'training_full_result', 'locator': locator},
            'readback': {'due_at': 100, 'deadline_at': 120}}
    child = {'task_id': 'fixed', 'depends_on': ['full'], 'source': {}}
    opening = {'workflow_id': 'campaign', 'task_queue': 'original-queue', 'plan': {'tasks': [root, child]}}
    run = 'original-run'
    grant = records.readback_grant(opening, run, root, None)
    activity_id = records.readback_id(grant)
    live_tasks = {'full': {'status': 'waiting_job', 'eligible': False},
                  'fixed': {'status': 'waiting_dependencies', 'eligible': False}}
    typed = {'kind': 'application', 'type': 'ReaderUnavailable', 'non_retryable': True}

    def event(event_id, kind, attributes, *, declared=None):
        return HistoryEvent(event_id=event_id,
                            event_type=EventType.Value('EVENT_TYPE_ACTIVITY_TASK_' + (declared or kind)),
                            **{f'activity_task_{kind.lower()}_event_attributes': attributes})

    async def exercise():
        converter = DataConverter.default
        events = [event(11, 'SCHEDULED', {
            'activity_id': activity_id, 'activity_type': {'name': records.TRAINING_READBACK_ACTIVITY},
            'task_queue': {'name': opening['task_queue']}, 'retry_policy': {'maximum_attempts': 1},
            'input': {'payloads': await converter.encode([grant])}},
            declared='FAILED' if case == 'wrong_schedule_event_type' else None)]
        start = None if case in ('before_start_timeout', 'heartbeat_without_start', 'cancel_without_start') else 12
        if case == 'request_before_start':
            start = 14
        if start is not None:
            events.append(event(start, 'STARTED', {'scheduled_event_id': 11, 'attempt': 2 if case == 'wrong_attempt' else 1},
                                declared='FAILED' if case == 'wrong_start_event_type' else None))
        terminal_fields = {'scheduled_event_id': 11, 'started_event_id': start or 0}
        terminal_id = 13
        if case in ('foreign_start', 'foreign_start_standard'):
            terminal_fields['started_event_id'] = 99
        if case == 'foreign_schedule':
            terminal_fields['scheduled_event_id'] = 99
        if case in ('timed_out', 'before_start_timeout', 'schedule_to_start_after_start', 'heartbeat_without_start'):
            cause = {'before_start_timeout': 'SCHEDULE_TO_CLOSE',
                     'schedule_to_start_after_start': 'SCHEDULE_TO_START'}.get(case, 'HEARTBEAT')
            events.append(event(13, 'TIMED_OUT', {
                **terminal_fields, 'failure': {'timeout_failure_info': {
                    'timeout_type': TimeoutType.Value('TIMEOUT_TYPE_' + cause)}}}))
            disposition, detail = 'timed_out', {'kind': 'timeout', 'type': cause}
        elif case in ('canceled', 'cancel_without_start', 'request_before_start', 'missing_cancel_request',
                      'foreign_cancel_request', 'wrong_cancel_link', 'wrong_cancel_event_type'):
            terminal_id = 15 if case == 'request_before_start' else 14
            if case != 'missing_cancel_request':
                events.append(event(13, 'CANCEL_REQUESTED', {
                    'scheduled_event_id': 99 if case == 'foreign_cancel_request' else 11,
                    'workflow_task_completed_event_id': 10},
                    declared='FAILED' if case == 'wrong_cancel_event_type' else None))
            events.append(event(terminal_id, 'CANCELED', {
                **terminal_fields, 'latest_cancel_requested_event_id': 99 if case == 'wrong_cancel_link' else 13}))
            disposition, detail = 'cancelled', None
        else:
            error_type = '/private/' + 'unbounded'*20 if case == 'unbounded_cause' else typed['type']
            if case not in ('missing', 'unavailable'):
                events.append(event(13, 'FAILED', {
                    **terminal_fields, 'failure': {'message': 'private reader output',
                        'stack_trace': '/private/stack.py', 'application_failure_info': {
                            'type': error_type, 'non_retryable': True}}},
                    declared='COMPLETED' if case == 'wrong_terminal_event_type' else None))
            if case == 'duplicate':
                events.append(event(14, 'FAILED', terminal_fields))
            disposition = 'failed'
            detail = {key: value for key, value in typed.items() if key != 'type'} if case == 'unbounded_cause' else typed

        class Handle:
            id = opening['workflow_id']
            run_id = run

            async def fetch_history_events(self, *, rpc_timeout):
                if case == 'unavailable':
                    raise TimeoutError('original History reader unavailable')
                for entry in sorted(events, key=lambda item: item.event_id):
                    yield entry

        async def original(*_):
            return Handle(), SimpleNamespace(run_id=run, status=SimpleNamespace(name='RUNNING'))

        async def live_state(*_, **__):
            if case == 'live':
                return {'workflow_state_status': 'observed', 'tasks': live_tasks}
            return {'workflow_state_status': 'unavailable'}

        runtime = SimpleNamespace(RPC_SECONDS=1, original=original, runtime_status=live_state,
                                  read_task_history=workflow.read_task_history, RPCError=RuntimeError)
        client = SimpleNamespace(data_converter=converter, namespace='default')
        observed = await application._read_original(runtime, {'attempt_sha256': 'original'}, opening, {}, run,
            client=client, read_state=True, include_task_history=case != 'foreign_start_standard')
        assert 'readback_completion' not in observed
        if case == 'live':
            assert observed['tasks'] == live_tasks
        else:
            assert 'tasks' not in observed
        if case in ('foreign_start', 'foreign_start_standard', 'wrong_attempt', 'duplicate', 'heartbeat_without_start',
                    'schedule_to_start_after_start', 'missing_cancel_request', 'foreign_cancel_request', 'wrong_cancel_link',
                    'wrong_cancel_event_type', 'wrong_schedule_event_type', 'wrong_start_event_type', 'wrong_terminal_event_type'):
            assert observed['task_observation_history_status'] == 'contradictory'
            assert 'readback_terminal' not in observed
        elif case in ('missing', 'unavailable', 'foreign_schedule'):
            assert observed['readback_history_status'] == ('unavailable' if case == 'unavailable' else 'unresolved')
            assert 'readback_terminal' not in observed
        else:
            expected = {'status': disposition, 'run_id': run, 'task_id': 'full', 'activity_id': activity_id,
                        'source_sha256': grant['source_sha256'], 'scheduled_event_id': 11, 'started_event_id': start,
                        'terminal_event_id': terminal_id}
            if disposition == 'cancelled':
                expected['cancel_requested_event_id'] = 13
            if detail is not None:
                expected['cause'] = detail
            assert observed['readback_terminal'] == expected

    asyncio.run(exercise())


@pytest.mark.parametrize('case', ('heartbeat', 'scheduled-only', 'started-only', 'before-start', 'foreign-schedule',
                                 'receipt-failure', 'cancelled', 'missing-cancel', 'wrong-grant', 'wrong-start',
                                 'wrong-attempt', 'wrong-type', 'duplicate-terminal', 'wrong-original-timeout',
                                 'wrong-original-start'))
def test_full_result_followup_terminal_is_separate_read_only_history(case):
    pytest.importorskip('temporalio')
    from temporalio.api.enums.v1 import EventType, TimeoutType
    from temporalio.api.history.v1 import HistoryEvent
    from temporalio.converter import DataConverter
    from ergora.campaigns import records, workflow

    locator = {'experiment_id': 'alpha', 'workflow_id': 'perf-experiment/alpha',
               'run_id': 'training-run', 'job_id': 'local-perf-alpha',
               'native_request_sha256': 'a'*64, 'attempt_sha256': 'b'*64}
    root = {'task_id': 'full', 'depends_on': [], 'source': {'kind': 'training_full_result', 'locator': locator},
            'readback': {'due_at': 100, 'deadline_at': 120}}
    option = 'recover_full_result_receipt' if case == 'receipt-failure' else 'reobserve_full_result_after_reader_loss'
    root[option] = True
    opening = {'workflow_id': 'campaign', 'task_queue': 'original-queue', 'plan': {'tasks': [root]}}
    run = 'original-run'
    grant = records.readback_grant(opening, run, root, None)
    activity_id = records.readback_id(grant)
    followup_id = records.readback_followup_id(root, grant)
    followup_type = records.readback_followup_activity(root)
    live_tasks = {'full': {'status': 'waiting_job', 'eligible': False}}

    def event(event_id, kind, attributes, *, declared=None):
        return HistoryEvent(event_id=event_id,
                            event_type=EventType.Value('EVENT_TYPE_ACTIVITY_TASK_' + (declared or kind)),
                            **{f'activity_task_{kind.lower()}_event_attributes': attributes})

    async def exercise():
        converter = DataConverter.default

        async def scheduled(ident, action, payload):
            return {'activity_id': ident, 'activity_type': {'name': action},
                    'task_queue': {'name': opening['task_queue']}, 'retry_policy': {'maximum_attempts': 1},
                    'input': {'payloads': await converter.encode([payload])}}

        def timeout(scheduled_id, started_id, cause):
            return {'scheduled_event_id': scheduled_id, 'started_event_id': started_id,
                    'failure': {'timeout_failure_info': {'timeout_type': TimeoutType.Value('TIMEOUT_TYPE_' + cause)}}}

        initial_cause = 'START_TO_CLOSE' if case == 'wrong-original-timeout' else 'HEARTBEAT'
        initial_start = 98 if case == 'wrong-original-start' else 12
        following_grant = {**grant, 'run_id': 'foreign'} if case == 'wrong-grant' else grant
        events = [event(11, 'SCHEDULED', await scheduled(activity_id, records.TRAINING_READBACK_ACTIVITY, grant)),
                  event(12, 'STARTED', {'scheduled_event_id': 11, 'attempt': 1}),
                  event(13, 'TIMED_OUT', timeout(11, initial_start, initial_cause)),
                  event(19, 'SCHEDULED', await scheduled(followup_id, followup_type, following_grant))]
        start = None if case in ('scheduled-only', 'before-start') else 20
        if start is not None:
            events.append(event(start, 'STARTED', {'scheduled_event_id': 19, 'attempt': 2 if case == 'wrong-attempt' else 1}))
        terminal_id, expected_status = 21, 'timed_out'
        cause = {'kind': 'timeout', 'type': 'HEARTBEAT'}
        if case == 'receipt-failure':
            events.append(event(21, 'FAILED', {'scheduled_event_id': 19, 'started_event_id': start, 'failure': {
                'message': 'private reader output', 'application_failure_info': {
                    'type': '/private/unsanitized-type', 'non_retryable': True}}}))
            expected_status, cause = 'failed', {'kind': 'application', 'non_retryable': True}
        elif case in ('cancelled', 'missing-cancel'):
            if case == 'cancelled':
                events.append(event(21, 'CANCEL_REQUESTED', {'scheduled_event_id': 19,
                                                              'workflow_task_completed_event_id': 18}))
            terminal_id, expected_status, cause = 22, 'cancelled', None
            events.append(event(22, 'CANCELED', {'scheduled_event_id': 19, 'started_event_id': start,
                                                  'latest_cancel_requested_event_id': 21}))
        elif case not in ('scheduled-only', 'started-only'):
            if case == 'before-start':
                cause = {'kind': 'timeout', 'type': 'SCHEDULE_TO_CLOSE'}
            event_attributes = timeout(99 if case == 'foreign-schedule' else 19,
                                       98 if case == 'wrong-start' else start or 0, cause['type'])
            finished = event(21, 'TIMED_OUT', event_attributes, declared='FAILED' if case == 'wrong-type' else None)
            # Terminal timeouts can be recorded after the configured success cutoff.
            finished.event_time.seconds = 123
            events.append(finished)
            if case == 'duplicate-terminal':
                events.append(event(22, 'TIMED_OUT', event_attributes))

        class Handle:
            id = opening['workflow_id']
            run_id = run

            async def fetch_history_events(self, *, rpc_timeout):
                for entry in events:
                    yield entry

        async def original(*_):
            return Handle(), SimpleNamespace(run_id=run, status=SimpleNamespace(name='RUNNING'))

        async def state(*_, **__):
            return {'workflow_state_status': 'observed', 'tasks': live_tasks}

        runtime = SimpleNamespace(RPC_SECONDS=1, original=original, runtime_status=state,
                                  read_task_history=workflow.read_task_history, RPCError=RuntimeError)
        client = SimpleNamespace(data_converter=converter, namespace='default')
        stop = {'status': 'observed', 'receipt': {'decision': 'accepted'}}
        view = await application._read_original(runtime, {'attempt_sha256': 'original', 'stop': stop}, opening, {}, run,
                                               client=client, read_state=True)
        assert view['tasks'] == live_tasks and view['stop'] == stop
        assert 'readback_completion' not in view and 'recipient_history' not in view
        if case == 'wrong-original-start':
            assert view['task_observation_history_status'] == 'contradictory'
            assert 'readback_terminal' not in view and 'readback_followup_terminal' not in view
            return
        assert view['readback_terminal'] == {
            'status': 'timed_out', 'run_id': run, 'task_id': 'full', 'activity_id': activity_id,
            'source_sha256': grant['source_sha256'], 'scheduled_event_id': 11, 'started_event_id': 12,
            'terminal_event_id': 13, 'cause': {'kind': 'timeout', 'type': initial_cause},
        }
        rejected = {'missing-cancel', 'wrong-grant', 'wrong-start', 'wrong-attempt', 'wrong-type',
                    'duplicate-terminal', 'wrong-original-timeout'}
        if case in rejected:
            assert view['task_observation_history_status'] == 'contradictory'
            assert 'readback_followup_terminal' not in view
            return
        if case in ('scheduled-only', 'started-only', 'foreign-schedule'):
            assert 'readback_followup_terminal' not in view
            return
        expected = {'status': expected_status, 'run_id': run, 'task_id': 'full', 'activity_id': followup_id,
                    'activity_type': followup_type, 'source_sha256': grant['source_sha256'],
                    'original_timeout_event_id': 13, 'scheduled_event_id': 19, 'started_event_id': start,
                    'terminal_event_id': terminal_id}
        if cause is not None:
            expected['cause'] = cause
        if case == 'cancelled':
            expected['cancel_requested_event_id'] = 21
        assert view['readback_followup_terminal'] == expected

    asyncio.run(exercise())


@pytest.mark.parametrize('history', ('absent', 'different', 'exact'))
@pytest.mark.parametrize('kind', ('training_full_result', 'training_screen_result', 'training_gpu_release'))
def test_training_recipient_binds_original_wake_history_before_reservation(monkeypatch, history, kind):
    pytest.importorskip('temporalio')
    from ergora.campaigns.recipient import CodexRecipient

    task = {'source': {'kind': kind}, 'readback': {}, 'recipient': {}}
    opening = {'plan': {'tasks': [task]}}
    intent = {'source': {'native_result_sha256': 'a'*64}, 'wake_id': 'original-wake'}
    delivered = []

    async def history_read(commands):
        assert commands == ()
        if history == 'absent':
            return None
        return {'intent': intent if history == 'exact' else {**intent, 'wake_id': 'different-wake'}}

    worker = CodexRecipient(None, opening, 'attempt', 'run', read_wake_history=history_read)
    monkeypatch.setattr(worker, '_deliver', delivered.append)
    if history == 'exact':
        asyncio.run(worker._deliver_verified(intent))
        assert delivered == [intent]
    else:
        with pytest.raises(ValueError, match='lacks its verified original result and schedule'):
            asyncio.run(worker._deliver_verified(intent))
        assert not delivered
