"""Offline service double: real SDK request encoding, fixed history and memo decoding."""

import asyncio
import base64
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

from perf_temporal import client as native, connection
from temporalio.api.common.v1 import Payloads, WorkflowExecution, WorkflowType
from temporalio.api.history.v1 import History, HistoryEvent, WorkflowExecutionStartedEventAttributes
from temporalio.api.workflow.v1 import WorkflowExecutionInfo
from temporalio.api.workflowservice.v1 import (DescribeWorkflowExecutionResponse, GetWorkflowExecutionHistoryResponse,
    StartWorkflowExecutionRequest, StartWorkflowExecutionResponse)
from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.common import WorkflowIDReusePolicy, WorkflowIDConflictPolicy
from temporalio.converter import DataConverter
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.service import RPCError, RPCStatusCode

from ergora.reference_training_submission import main

payload = json.load(sys.stdin)
sys.stdin = io.StringIO(json.dumps(payload))
scenario = os.environ['ERGORA_TEST_TRAINING_SUBMISSION']
storage = Path(os.environ['ERGORA_TEST_TRAINING_SERVICE'])
record = json.loads(storage.read_text()) if storage.exists() else {'starts': 0, 'calls': []}
run_id = '00000000-0000-4000-8000-000000000001'
converter = DataConverter.default


def save():
    storage.write_text(json.dumps(record) + '\n')


class Service:
    def __init__(self):
        self.workflow_service = self
        self.config = SimpleNamespace(identity='ergora-offline-sdk-contract')

    async def start_workflow_execution(self, request, **kwargs):
        record['calls'].append(['start', request.workflow_id])
        record['starts'] += 1
        save()
        assert request.workflow_id_reuse_policy == WorkflowIDReusePolicy.REJECT_DUPLICATE
        assert request.workflow_id_conflict_policy == WorkflowIDConflictPolicy.FAIL
        assert request.retry_policy.maximum_attempts == 1
        if scenario == 'race':
            raise WorkflowAlreadyStartedError(request.workflow_id, request.workflow_type.name, run_id=run_id)
        assert 'request' not in record, 'A second native start is a regression'
        record['request'] = base64.b64encode(request.SerializeToString()).decode()
        save()
        if scenario == 'lost-ack':
            raise RPCError('Accepted, reply lost', RPCStatusCode.UNAVAILABLE, b'')
        if scenario == 'timeout-ack':
            await asyncio.sleep(5)
        return StartWorkflowExecutionResponse(run_id=run_id)

    async def describe_workflow_execution(self, request, **kwargs):
        record['calls'].append(['describe', request.execution.run_id])
        save()
        if scenario == 'unavailable':
            raise RPCError('Unavailable', RPCStatusCode.UNAVAILABLE, b'')
        if scenario == 'preexisting' and 'request' not in record:
            spec = json.loads((Path(payload['project']['registration']['definition']['execution']['state_directory'])
                               / 'training/specs' / (payload['experiment_id'] + '.json')).read_text())
            original = StartWorkflowExecutionRequest(input=Payloads(payloads=await converter.encode([spec])))
            record['request'] = base64.b64encode(original.SerializeToString()).decode()
            save()
        if 'request' not in record or scenario == 'not-found':
            raise RPCError('Not found', RPCStatusCode.NOT_FOUND, b'')
        original = StartWorkflowExecutionRequest.FromString(base64.b64decode(record['request']))
        if scenario == 'foreign-memo':
            original.memo.fields.clear()
        return DescribeWorkflowExecutionResponse(workflow_execution_info=WorkflowExecutionInfo(
            execution=WorkflowExecution(workflow_id=request.execution.workflow_id, run_id=run_id),
            type=WorkflowType(name='ExperimentWorkflow'), status=WorkflowExecutionStatus.RUNNING, memo=original.memo))

    async def get_workflow_execution_history(self, request, **kwargs):
        record['calls'].append(['history', request.execution.run_id])
        save()
        assert request.execution.run_id == run_id
        original = StartWorkflowExecutionRequest.FromString(base64.b64decode(record['request']))
        if scenario == 'missing-history':
            return GetWorkflowExecutionHistoryResponse(history=History())
        if scenario == 'input-collision':
            value = deepcopy((await converter.decode(original.input.payloads, [dict]))[0])
            value['poll_seconds'] = float(value['poll_seconds'])
            original.input.CopyFrom(Payloads(payloads=await converter.encode([value])))
        return GetWorkflowExecutionHistoryResponse(history=History(events=[HistoryEvent(event_id=1,
            workflow_execution_started_event_attributes=WorkflowExecutionStartedEventAttributes(input=original.input))]))


async def connect():
    return Client(Service())


connection.connect = native.connect = connect
main()
