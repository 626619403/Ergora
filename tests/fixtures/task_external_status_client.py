"""Controllable RPC boundary with real SDK pagination, codec and history messages."""

import asyncio
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

from temporalio.api.common.v1 import Payload
from temporalio.api.history.v1 import History, HistoryEvent
from temporalio.api.workflowservice.v1 import GetWorkflowExecutionHistoryResponse
from temporalio.client import FetchWorkflowHistoryEventsInput, WorkflowExecutionStatus, WorkflowHistoryEventAsyncIterator
from temporalio.converter import DataConverter, PayloadCodec
from temporalio.service import RPCError, RPCStatusCode

from dev_platform import connection
from ergora.reference_task_reconciliation import main

payload = json.load(sys.stdin)
sys.stdin = io.StringIO(json.dumps(payload))
scenario = os.environ.get('ERGORA_TEST_EXTERNAL_SCENARIO', 'normal')
root = Path(payload['project']['registration']['definition']['execution']['state_directory']) / 'sdk-fixture'


def log(event):
    with (root / 'calls.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'event': event}) + '\n')


def saved():
    return json.loads((root / 'server.json').read_text())


class Codec(PayloadCodec):
    async def encode(self, payloads):
        return [Payload(metadata={'encoding': b'fixture/codec'}, data=value.SerializeToString()) for value in payloads]

    async def decode(self, payloads):
        log('external-codec-decode')
        assert all(value.metadata['encoding'] == b'fixture/codec' for value in payloads)
        return [Payload.FromString(value.data) for value in payloads]


converter = DataConverter(payload_codec=Codec())


async def events():
    spec = saved()['spec']
    if scenario == 'wrong-spec':
        spec['profile']['schema_version'] = True
    first = HistoryEvent(event_id=1)
    first.workflow_execution_started_event_attributes.input.payloads.extend(await converter.encode([spec]))
    result = [first]
    for context in json.loads((root / 'jobs.json').read_text()):
        event = HistoryEvent(event_id=len(result) + 1)
        scheduled = event.activity_task_scheduled_event_attributes
        scheduled.activity_id = str(event.event_id)
        scheduled.activity_type.name = 'dev_submit'
        scheduled.input.payloads.extend(await converter.encode([context]))
        result.append(event)
    end = HistoryEvent(event_id=len(result) + 1)
    status = saved().get('status', 'COMPLETED')
    name = {'COMPLETED': 'completed', 'FAILED': 'failed', 'CANCELED': 'canceled',
            'TERMINATED': 'terminated', 'TIMED_OUT': 'timed_out',
            'RUNNING': 'completed', 'CONTINUED_AS_NEW': 'continued_as_new'}[status]
    getattr(end, 'workflow_execution_' + name + '_event_attributes').SetInParent()
    result.append(end)
    return result


class HistoryService:
    async def get_workflow_execution_history(self, request, **kwargs):
        assert request.execution.workflow_id == 'dev-task/' + payload['task_id']
        assert request.execution.run_id in ('original-run', 'successor-run')
        assert request.history_event_filter_type == 1  # ALL_EVENT
        assert kwargs['timeout'].total_seconds() == 20
        result = await events()
        if request.maximum_page_size == 100:
            log('external-history-page')
            if scenario == 'history-rpc-unavailable':
                raise RPCError('history unavailable', RPCStatusCode.UNAVAILABLE, b'')
            if scenario == 'history-gap':
                result.pop(1)
            if scenario == 'history-no-start':
                result.pop(0)
            if scenario == 'history-no-terminal':
                result.pop()
            if scenario == 'history-wrong-terminal':
                result[-1].ClearField('workflow_execution_completed_event_attributes')
                result[-1].workflow_execution_failed_event_attributes.SetInParent()
            if scenario == 'history-empty':
                result = []
        index = int(request.next_page_token or b'0')
        size = min(request.maximum_page_size, 2)
        page = result[index:index + size]
        token = str(index + size).encode() if index + size < len(result) else b''
        return GetWorkflowExecutionHistoryResponse(history=History(events=page), next_page_token=token)


class Handle:
    def __init__(self, run_id):
        self.run_id = run_id

    async def describe(self, **kwargs):
        log('external-describe')
        if scenario == 'not-found':
            raise RPCError('missing', RPCStatusCode.NOT_FOUND, b'')
        if scenario == 'rpc-unavailable':
            raise RPCError('unavailable', RPCStatusCode.UNAVAILABLE, b'')
        async def memo():
            return {} if scenario == 'wrong-memo' else saved()['memo']
        return SimpleNamespace(run_id=self.run_id, memo=memo,
                               status=WorkflowExecutionStatus[saved().get('status', 'COMPLETED')])

    def fetch_history_events(self, **kwargs):
        return WorkflowHistoryEventAsyncIterator(Client(), FetchWorkflowHistoryEventsInput(
            id='dev-task/' + payload['task_id'], run_id=self.run_id,
            page_size=kwargs['page_size'], next_page_token=None, wait_new_event=False,
            event_filter_type=1, skip_archival=False, rpc_metadata={}, rpc_timeout=kwargs['rpc_timeout']))

    async def result(self, **kwargs):
        log('external-result')
        assert kwargs['follow_runs'] is False and kwargs['rpc_timeout'].total_seconds() == 20
        return json.loads((root / 'outcome.json').read_text())


class Client:
    data_converter = converter
    namespace = 'fixture'
    workflow_service = HistoryService()

    def get_workflow_handle(self, workflow_id, *, run_id, result_type):
        assert workflow_id == 'dev-task/' + payload['task_id'] and result_type is dict
        latest = 'successor-run' if scenario == 'successor-run' else saved()['run_id']
        return Handle(run_id or latest)


async def connect():
    log('external-connect')
    if scenario == 'slow-connect':
        await asyncio.sleep(float(os.environ.get('ERGORA_TEST_EXTERNAL_DELAY', '3')))
    if scenario == 'offline':
        raise OSError('Fixture external service is offline')
    return Client()


connection.connect = connect
main()
