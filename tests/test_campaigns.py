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

    async def cli(args, code=0):
        result = await asyncio.to_thread(subprocess.run, [sys.executable, '-m', 'ergora', *args],
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

                def no_reissue(*args, **kwargs):
                    raise AssertionError('Original observation may only reconcile its saved attempt')

                after = files(state.root)
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
