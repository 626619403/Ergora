"""Parent-only SDK service double, shared with submission and native-create probes."""

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import uuid

from temporalio.api.common.v1 import ActivityType, Memo, Payloads, WorkflowExecution, WorkflowType
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

from ergora.training.execution_protocol import CYCLE_MEMO_KEY, CycleAdmission, cycle_workflow_type, cycle_activity_names


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
        case = os.environ.get('ERGORA_TEST_TRAINING_CONTROLLER_CASE', '')
        if case == 'closed-after-attempt':
            marker = Path(os.environ['ERGORA_TEST_TRAINING_CONTROLLER_MARKER']).with_suffix('.closed')
            case = 'closed' if marker.exists() else ''
        return folder, intent, receipt, case

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
            type=WorkflowType(name=cycle_workflow_type(intent['protocol'])), memo=await self.memo(intent, case),
            first_run_id=receipt['run_id'], status=WorkflowExecutionStatus.COMPLETED if case == 'closed' else WorkflowExecutionStatus.RUNNING))

    async def get_workflow_execution_history(self, request, **kwargs):
        folder, intent, receipt, case = self.original(request)
        value = deepcopy(intent['workflow_input'])
        if case == 'input':
            value['input_sha256'] = '0' * 64
        started = WorkflowExecutionStartedEventAttributes(
            workflow_type=WorkflowType(name='ForeignWorkflow' if case == 'type' else
                cycle_workflow_type(intent['protocol'])),
            task_queue=TaskQueue(name='another-queue' if case == 'queue' else intent['task_queue']),
            input=Payloads(payloads=await DataConverter.default.encode([value])), memo=await self.memo(intent, case),
            first_execution_run_id=receipt['run_id'], original_execution_run_id=receipt['run_id'], attempt=1)
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
        expected_type = cycle_workflow_type(self.intent['protocol'])
        assert request.workflow_type.name == expected_type and request.task_queue.name == self.intent['task_queue']
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
        if self.case in ('preexisting', 'collision', 'v1-type'):
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
            type=WorkflowType(name=(cycle_workflow_type(self.intent['protocol']) if self.case != 'v1-type' else 'TrainingCycleWorkflow')), memo=memo, status=status,
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
            workflow_type=WorkflowType(name='ForeignWorkflow' if self.case == 'type' else
                cycle_workflow_type(self.intent['protocol']) if self.case != 'v1-type' else 'TrainingCycleWorkflow'),
            task_queue=TaskQueue(name='foreign-queue' if self.case == 'queue' else self.intent['task_queue']),
            input=Payloads(payloads=await DataConverter.default.encode([value])), memo=memo,
            first_execution_run_id=self.run_id, original_execution_run_id=self.run_id if self.case == 'reset' else request.execution.run_id,
            continued_execution_run_id='', initiator=0, attempt=1)
        return GetWorkflowExecutionHistoryResponse(history=History(events=[HistoryEvent(event_id=1,
            workflow_execution_started_event_attributes=started)]))


class RoundService(DispatchService):
    """Only external Temporal responses vary; real SDK protobufs and converters remain."""

    def __init__(self, payload, case):
        self.payload = payload
        self.case = case
        self.workflow_service = self
        self.config = SimpleNamespace(identity='ergora-round-sdk-contract')
        identity = payload['identity']
        self.folder = Path(identity['control_home']) / 'training-cycles' / identity['project'] / identity['cycle_id'] / 'controller'
        self.intent = json.loads((self.folder / 'intent.json').read_bytes())
        self.receipt = json.loads((self.folder / 'receipt.json').read_bytes())
        from ergora.training.execution_protocol import resolve_cycle_snapshot
        plan, authorization = resolve_cycle_snapshot(payload)
        self.runtime = Path(authorization['execution']['state_directory'])
        self.ident = plan['definition']['candidates'][identity['ordinal']]['experiment_id']

    def candidate(self, request):
        if request.execution.workflow_id != self.intent['workflow_id']:
            self.ident = request.execution.workflow_id.removeprefix('perf-experiment/')
            self.start = json.loads((self.runtime / ('ergora/training-submissions/' + self.ident + '.intent.json')).read_bytes())
            self.native_receipt = json.loads((self.runtime / ('ergora/training-submissions/' + self.ident + '.result.json')).read_bytes())

    async def describe_workflow_execution(self, request, **kwargs):
        from ergora.training.runtime.status import MEMO_KEY
        error_bytes = int(os.environ.get('ERGORA_TEST_ROUND_ERROR_BYTES', '0'))
        if error_bytes:
            marker = '原 RPC 容量 🧪'
            raise ValueError(marker + 'x' * (error_bytes - len(marker.encode('utf-8'))))
        self.candidate(request)
        parent = request.execution.workflow_id == self.intent['workflow_id']
        digest = CycleAdmission._sha(self.intent if parent else self.start)
        if not parent and self.case == 'round-memo':
            digest = '0' * 64
        run = self.receipt['run_id'] if parent else self.native_receipt['run_id']
        if not parent and self.case == 'round-run':
            run = 'foreign-run'
        return DescribeWorkflowExecutionResponse(workflow_execution_info=WorkflowExecutionInfo(
            execution=WorkflowExecution(workflow_id=request.execution.workflow_id, run_id=run),
            type=WorkflowType(name=cycle_workflow_type(self.intent['protocol']) if parent else 'ExperimentWorkflow'),
            memo=Memo(fields={(CYCLE_MEMO_KEY if parent else MEMO_KEY): (await DataConverter.default.encode([digest]))[0]}),
            first_run_id=run, status=WorkflowExecutionStatus.COMPLETED if not parent and self.case.startswith('round-outcome')
                else WorkflowExecutionStatus.RUNNING))

    async def get_workflow_execution_history(self, request, **kwargs):
        from temporalio.api.history.v1 import ActivityTaskScheduledEventAttributes
        self.candidate(request)
        parent = request.execution.workflow_id == self.intent['workflow_id']
        if not parent and request.history_event_filter_type == 2:
            from dataclasses import asdict
            from perf_temporal.models import Binding, Outcome
            from temporalio.api.history.v1 import WorkflowExecutionCompletedEventAttributes
            result = json.loads((self.runtime / ('training/jobs/' + self.ident + '/result.json')).read_bytes())
            report = Path(result['gate']['report']).as_uri()
            if self.case == 'round-outcome-uri':
                report += '.foreign'
            outcome = Outcome('RELEASE_EXPIRED', Binding(**self.start['observation']['experiment']['binding']),
                              'local-perf-' + self.ident, report_uri=report, detail='Original synthetic outcome')
            return GetWorkflowExecutionHistoryResponse(history=History(events=[HistoryEvent(event_id=5,
                workflow_execution_completed_event_attributes=WorkflowExecutionCompletedEventAttributes(
                    result=Payloads(payloads=await DataConverter.default.encode([asdict(outcome)]))))]))
        if not parent:
            return GetWorkflowExecutionHistoryResponse(history=History(events=[HistoryEvent(event_id=1,
                workflow_execution_started_event_attributes=WorkflowExecutionStartedEventAttributes(
                    input=Payloads(payloads=await DataConverter.default.encode([self.start['observation']['experiment']['spec']]))))]))
        started = WorkflowExecutionStartedEventAttributes(workflow_type=WorkflowType(name=cycle_workflow_type(self.intent['protocol'])),
            task_queue=TaskQueue(name=self.intent['task_queue']),
            input=Payloads(payloads=await DataConverter.default.encode([self.intent['workflow_input']])),
            memo=Memo(fields={CYCLE_MEMO_KEY: (await DataConverter.default.encode([CycleAdmission._sha(self.intent)]))[0]}),
            first_execution_run_id=self.receipt['run_id'], original_execution_run_id=self.receipt['run_id'], attempt=1)
        events = [HistoryEvent(event_id=1, workflow_execution_started_event_attributes=started)]
        original = {'workflow_input': self.intent['workflow_input'], 'ordinal': self.payload['identity']['ordinal'],
                    'predecessor': self.payload['start_context']['controller']['predecessor']}
        scheduled = ActivityTaskScheduledEventAttributes(activity_id='candidate-' + str(original['ordinal']) + '-collect',
            activity_type=ActivityType(name=cycle_activity_names()['collect-round']),
            task_queue=TaskQueue(name=self.intent['task_queue']), input=Payloads(payloads=await DataConverter.default.encode([original])))
        if self.case == 'round-history-input':
            original['predecessor'] = {'foreign': True}
            scheduled.input.CopyFrom(Payloads(payloads=await DataConverter.default.encode([original])))
        if self.case != 'round-no-collect':
            events.append(HistoryEvent(event_id=2, activity_task_scheduled_event_attributes=scheduled))
        if self.case == 'round-duplicate-collect':
            events.append(HistoryEvent(event_id=3, activity_task_scheduled_event_attributes=scheduled))
        if self.payload['identity']['mode'] == 'reconcile-round':
            current = ActivityTaskScheduledEventAttributes(activity_id=self.payload['activity_context']['activity_source']['activity_id'],
                activity_type=ActivityType(name=cycle_activity_names()['reconcile-round']),
                task_queue=TaskQueue(name=self.intent['task_queue']), input=Payloads(payloads=await DataConverter.default.encode([original])))
            events.append(HistoryEvent(event_id=4, activity_task_scheduled_event_attributes=current))
        if self.case == 'round-history-count':
            events.extend(HistoryEvent(event_id=index) for index in range(10, 8010))
        if self.case == 'round-history-bytes':
            from temporalio.api.common.v1 import Payload
            from temporalio.api.history.v1 import WorkflowExecutionSignaledEventAttributes
            events.append(HistoryEvent(event_id=10, workflow_execution_signaled_event_attributes=
                WorkflowExecutionSignaledEventAttributes(signal_name='request_stop',
                    input=Payloads(payloads=[Payload(data=b'x' * (8 * 1_048_576))]))))
        if self.case == 'round-history-decode':
            events[-1].activity_task_scheduled_event_attributes.input.payloads[0].data = b'{incomplete'
        return GetWorkflowExecutionHistoryResponse(history=History(events=events))

    async def query_workflow(self, request, **kwargs):
        from dataclasses import asdict
        from perf_temporal.models import Binding, Status
        from temporalio.api.workflowservice.v1 import QueryWorkflowResponse
        self.candidate(request)
        binding = self.start['observation']['experiment']['binding']
        gate_path = self.runtime / ('training/jobs/' + self.ident + '/gate-report.json')
        gate = json.loads(gate_path.read_bytes()) if gate_path.exists() else None
        evidence = gate['evidence_sha256'] if gate else None
        if self.case == 'round-evidence':
            evidence = 'f' * 64
        if self.case == 'round-binding':
            binding = {**binding, 'manifest_sha': 'f' * 64}
        detail_size = int(os.environ.get('ERGORA_TEST_ROUND_DETAIL', '0'))
        if self.case == 'round-previous-held':
            marker = Path(os.environ['ERGORA_TEST_CYCLE_MARKERS']) / 'previous-query-held'
            marker.touch()
            while not marker.with_suffix('.release').exists():
                await asyncio.sleep(.01)
        after_intent = (self.case == 'round-previous-after-intent'
            and (self.runtime / 'ergora/training-submissions/beta.intent.json').exists())
        phase = ('CANCELLING' if self.case == 'round-previous-cancelling' or after_intent else
                 'RUNNING' if self.case == 'round-pending' else 'AWAITING_RELEASE')
        status = Status(phase, Binding(**binding),
            'foreign-job' if self.case == 'round-job' else 'local-perf-' + self.ident, evidence, '独特 RPC 原值 🧪' + 'x' * detail_size)
        return QueryWorkflowResponse(query_result=Payloads(payloads=await DataConverter.default.encode([asdict(status)])))
