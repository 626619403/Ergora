"""Parent-only SDK service double, shared with submission and native-create probes."""

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import uuid

from temporalio.api.common.v1 import Memo, Payloads, WorkflowExecution, WorkflowType
from temporalio.api.history.v1 import History, HistoryEvent, WorkflowExecutionStartedEventAttributes
from temporalio.api.taskqueue.v1 import TaskQueue
from temporalio.api.workflow.v1 import WorkflowExecutionInfo
from temporalio.api.workflowservice.v1 import (DescribeWorkflowExecutionResponse, GetWorkflowExecutionHistoryResponse,
    StartWorkflowExecutionRequest, StartWorkflowExecutionResponse)
from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.common import WorkflowIDReusePolicy, WorkflowIDConflictPolicy
from temporalio.converter import DataConverter
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.service import RPCError, RPCStatusCode

from ergora.training_execution_protocol import CYCLE_MEMO_KEY, CycleAdmission


class Service:
    def __init__(self):
        self.workflow_service = self
        self.config = SimpleNamespace(identity='ergora-parent-sdk-contract')

    def original(self, request):
        folder = Path(os.environ['ERGORA_TEST_TRAINING_CONTROLLER'])
        intent = json.loads((folder / 'intent.json').read_bytes())
        receipt = json.loads((folder / 'receipt.json').read_bytes())
        assert request.execution.workflow_id == intent['workflow_id']
        assert request.execution.run_id == receipt['run_id']
        return folder, intent, receipt, os.environ.get('ERGORA_TEST_TRAINING_CONTROLLER_CASE', '')

    async def memo(self, intent, case):
        digest = CycleAdmission._sha(intent) if case != 'memo' else '0' * 64
        return Memo(fields={CYCLE_MEMO_KEY: (await DataConverter.default.encode([digest]))[0]})

    async def describe_workflow_execution(self, request, **kwargs):
        _, intent, receipt, case = self.original(request)
        if case == 'not-found':
            raise RPCError('Parent not found', RPCStatusCode.NOT_FOUND, b'')
        return DescribeWorkflowExecutionResponse(workflow_execution_info=WorkflowExecutionInfo(
            execution=WorkflowExecution(workflow_id=intent['workflow_id'],
                run_id='another-run' if case == 'run' else receipt['run_id']),
            type=WorkflowType(name='TrainingCycleWorkflow'), memo=await self.memo(intent, case),
            status=WorkflowExecutionStatus.COMPLETED if case == 'closed' else WorkflowExecutionStatus.RUNNING))

    async def get_workflow_execution_history(self, request, **kwargs):
        folder, intent, _, case = self.original(request)
        value = deepcopy(intent['workflow_input'])
        if case == 'input':
            value['input_sha256'] = '0' * 64
        started = WorkflowExecutionStartedEventAttributes(
            workflow_type=WorkflowType(name='ForeignWorkflow' if case == 'type' else 'TrainingCycleWorkflow'),
            task_queue=TaskQueue(name='another-queue' if case == 'queue' else intent['task_queue']),
            input=Payloads(payloads=await DataConverter.default.encode([value])), memo=await self.memo(intent, case))
        (folder / 'parent-history-observed').touch()
        return GetWorkflowExecutionHistoryResponse(history=History(events=[HistoryEvent(event_id=1,
            workflow_execution_started_event_attributes=started)]))


async def connect():
    return Client(Service())


class DispatchService:
    """Real SDK codec with a persistent server substitute across supervised H processes."""

    run_id = '00000000-0000-4000-8000-000000000003'
    successor = '00000000-0000-4000-8000-000000000004'

    def __init__(self, payload, case):
        self.workflow_service = self
        self.config = SimpleNamespace(identity='ergora-cycle-dispatch-sdk-contract')
        self.storage = Path(os.environ['ERGORA_TEST_CYCLE_DISPATCH'])
        self.case = case
        identity = payload['identity']
        self.folder = Path(identity['control_home']) / 'training-cycles' / identity['project'] / identity['cycle_id'] / 'controller'
        self.intent = json.loads((self.folder / 'intent.json').read_bytes())

    def record(self, action, request):
        value = {'action': action, 'run_id': request.execution.run_id if action != 'start' else None}
        (self.storage / ('call-' + uuid.uuid4().hex + '.json')).write_text(json.dumps(value))

    async def start_workflow_execution(self, request, **kwargs):
        self.record('start', request)
        assert request.workflow_id == self.intent['workflow_id']
        assert request.workflow_type.name == 'TrainingCycleWorkflow' and request.task_queue.name == self.intent['task_queue']
        assert request.workflow_id_reuse_policy == WorkflowIDReusePolicy.REJECT_DUPLICATE
        assert request.workflow_id_conflict_policy == WorkflowIDConflictPolicy.FAIL and request.retry_policy.maximum_attempts == 1
        assert await DataConverter.default.decode(request.input.payloads, [dict]) == [self.intent['workflow_input']]
        assert await DataConverter.default.decode([request.memo.fields[CYCLE_MEMO_KEY]], [str]) == [CycleAdmission._sha(self.intent)]
        if self.case == 'start-conflict':
            raise WorkflowAlreadyStartedError(request.workflow_id, request.workflow_type.name, run_id=self.run_id)
        with (self.storage / 'request.pb').open('xb') as stream:
            stream.write(request.SerializeToString())
        if self.case == 'authorization-after-start':
            (self.folder.parent / 'authorization.json').write_text('{"incomplete":')
            return StartWorkflowExecutionResponse(run_id=self.run_id, started=True)
        if self.case == 'held-start':
            (self.storage / 'start-held').touch()
            while not (self.storage / 'release-start').exists():
                await asyncio.sleep(.01)
        if self.case != 'accepted' and self.case != 'held-start':
            raise RPCError('Accepted but original reply lost', RPCStatusCode.UNAVAILABLE, b'')
        return StartWorkflowExecutionResponse(run_id=self.run_id, started=True)

    async def original_request(self):
        if (self.storage / 'request.pb').exists():
            return StartWorkflowExecutionRequest.FromString((self.storage / 'request.pb').read_bytes())
        if self.case in ('preexisting', 'collision'):
            return StartWorkflowExecutionRequest(input=Payloads(payloads=await DataConverter.default.encode([self.intent['workflow_input']])),
                memo=Memo(fields={CYCLE_MEMO_KEY: (await DataConverter.default.encode([CycleAdmission._sha(self.intent)]))[0]}))
        raise RPCError('No original run', RPCStatusCode.NOT_FOUND, b'')

    async def describe_workflow_execution(self, request, **kwargs):
        self.record('describe', request)
        if self.case == 'unavailable':
            raise RPCError('Service unavailable', RPCStatusCode.UNAVAILABLE, b'')
        if self.case == 'late-lookup' and not request.execution.run_id and not (self.storage / 'lookup-released').exists():
            (self.storage / 'lookup-held').touch()
            while not (self.storage / 'release-lookup').exists():
                await asyncio.sleep(.01)
            (self.storage / 'lookup-released').touch()
        original = await self.original_request()
        if self.case == 'not-found':
            raise RPCError('Reply still unobservable', RPCStatusCode.NOT_FOUND, b'')
        selected = request.execution.run_id or (self.successor if self.case in ('continued', 'retry', 'reset') else self.run_id)
        memo = original.memo
        if self.case == 'memo':
            memo = Memo(fields={CYCLE_MEMO_KEY: (await DataConverter.default.encode(['0' * 64]))[0]})
        status = (WorkflowExecutionStatus.CONTINUED_AS_NEW if self.case == 'continued' else WorkflowExecutionStatus.FAILED
            if self.case == 'retry' else WorkflowExecutionStatus.COMPLETED if self.case == 'closed' else WorkflowExecutionStatus.RUNNING)
        return DescribeWorkflowExecutionResponse(workflow_execution_info=WorkflowExecutionInfo(
            execution=WorkflowExecution(workflow_id=self.intent['workflow_id'], run_id='foreign-run' if self.case == 'run' else selected),
            type=WorkflowType(name='TrainingCycleWorkflow'), memo=memo, status=status,
            first_run_id=self.successor if self.case == 'first-run' else self.run_id))

    async def get_workflow_execution_history(self, request, **kwargs):
        self.record('history', request)
        original = await self.original_request()
        value = (await DataConverter.default.decode(original.input.payloads, [dict]))[0]
        if self.case in ('input', 'collision'):
            value['input_sha256'] = '0' * 64
        memo = original.memo
        if self.case == 'started-memo':
            memo = Memo(fields={CYCLE_MEMO_KEY: (await DataConverter.default.encode(['0' * 64]))[0]})
        started = WorkflowExecutionStartedEventAttributes(
            workflow_type=WorkflowType(name='ForeignWorkflow' if self.case == 'type' else 'TrainingCycleWorkflow'),
            task_queue=TaskQueue(name='foreign-queue' if self.case == 'queue' else self.intent['task_queue']),
            input=Payloads(payloads=await DataConverter.default.encode([value])), memo=memo,
            first_execution_run_id=self.run_id, original_execution_run_id=self.run_id if self.case == 'reset' else request.execution.run_id,
            continued_execution_run_id='', initiator=0, attempt=1)
        return GetWorkflowExecutionHistoryResponse(history=History(events=[HistoryEvent(event_id=1,
            workflow_execution_started_event_attributes=started)]))
