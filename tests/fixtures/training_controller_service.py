"""Parent-only SDK service double, shared with submission and native-create probes."""

from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace

from temporalio.api.common.v1 import Memo, Payloads, WorkflowExecution, WorkflowType
from temporalio.api.history.v1 import History, HistoryEvent, WorkflowExecutionStartedEventAttributes
from temporalio.api.taskqueue.v1 import TaskQueue
from temporalio.api.workflow.v1 import WorkflowExecutionInfo
from temporalio.api.workflowservice.v1 import DescribeWorkflowExecutionResponse, GetWorkflowExecutionHistoryResponse
from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.converter import DataConverter
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
