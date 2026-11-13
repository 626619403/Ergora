"""Reuse the start service, exercising real SDK signal/query/history encoding."""

from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import training_submission_client as base

from perf_temporal.models import Binding, CancelRequest, Outcome, Status
from temporalio.api.common.v1 import Payloads
from temporalio.api.history.v1 import (HistoryEvent, WorkflowExecutionCompletedEventAttributes,
                                     WorkflowExecutionSignaledEventAttributes)
from temporalio.api.workflowservice.v1 import (QueryWorkflowResponse, SignalWorkflowExecutionResponse)

from ergora.reference_training_cancellation import main
from dev_platform.contracts import canonical_sha


async def spec():
    original = base.StartWorkflowExecutionRequest.FromString(base.base64.b64decode(base.record['request']))
    return (await base.converter.decode(original.input.payloads, [dict]))[0]


class Service(base.Service):
    async def describe_workflow_execution(self, request, **kwargs):
        response = await super().describe_workflow_execution(request, **kwargs)
        if base.scenario in ('closed', 'control-unconfirmed'):
            response.workflow_execution_info.status = base.WorkflowExecutionStatus.COMPLETED
        if base.scenario == 'wrong-run':
            response.workflow_execution_info.execution.run_id = 'another-run'
        return response

    async def query_workflow(self, request, **kwargs):
        assert request.execution.run_id == base.run_id
        binding = Binding(**(await spec())['binding'])
        if base.scenario == 'status-binding':
            binding = replace(binding, manifest_sha='e' * 64)
        return QueryWorkflowResponse(query_result=Payloads(payloads=await base.converter.encode([
            asdict(Status('POLLING', binding, 'local-perf-alpha', None, None))])))

    async def signal_workflow_execution(self, request, **kwargs):
        assert request.workflow_execution.run_id == base.run_id
        assert request.signal_name == 'request_cancel'
        value = (await base.converter.decode(request.input.payloads, [dict]))[0]
        native = (await base.converter.decode(request.input.payloads, [CancelRequest]))[0]
        assert asdict(native) == {key: value[key] for key in ('binding', 'reason')}
        prefix = (base.Path(base.payload['project']['registration']['definition']['execution']['state_directory'])
                  / 'ergora/training-cancellations' / base.payload['experiment_id'] / base.payload['request_id'])
        intent = base.json.loads(Path(str(prefix) + '.intent.json').read_text())
        attempt = base.json.loads(Path(str(prefix) + '.attempt.json').read_text())
        assert value['ergora_operation_sha256'] == attempt['intent_sha256'] == canonical_sha(intent)
        assert attempt['run_id'] == base.run_id and attempt['signal_sha256'] == canonical_sha(value)
        base.record['signals'] = base.record.get('signals', 0) + 1
        base.record['signal'] = base.base64.b64encode(request.input.SerializeToString()).decode()
        base.save()
        if base.scenario == 'lost-ack':
            raise base.RPCError('Accepted signal, reply lost', base.RPCStatusCode.UNAVAILABLE, b'')
        if base.scenario == 'timeout-ack':
            await base.asyncio.sleep(5)
        return SignalWorkflowExecutionResponse()

    async def get_workflow_execution_history(self, request, **kwargs):
        response = await super().get_workflow_execution_history(request, **kwargs)
        if 'signal' in base.record and base.scenario != 'signal-missing':
            encoded = Payloads.FromString(base.base64.b64decode(base.record['signal']))
            value = deepcopy((await base.converter.decode(encoded.payloads, [dict]))[0])
            if base.scenario == 'foreign-signal':
                value.pop('ergora_operation_sha256')
            if base.scenario == 'wrong-marker':
                value['ergora_operation_sha256'] = '0' * 64
            response.history.events.append(HistoryEvent(event_id=2,
                workflow_execution_signaled_event_attributes=WorkflowExecutionSignaledEventAttributes(
                    signal_name='request_cancel', input=Payloads(payloads=await base.converter.encode([value])))))
        if base.scenario in ('closed', 'control-unconfirmed'):
            binding = Binding(**(await spec())['binding'])
            response.history.events.append(HistoryEvent(event_id=3,
                workflow_execution_completed_event_attributes=WorkflowExecutionCompletedEventAttributes(
                    result=Payloads(payloads=await base.converter.encode([
                        asdict(Outcome('CANCEL_UNCONFIRMED', binding, 'local-perf-alpha', detail='CPU contract'))])))))
        return response


async def connect():
    return base.Client(Service())


base.connection.connect = base.native.connect = connect
main()
