"""Native approve/release bridge with real SDK encoding and offline fixed-run history."""

from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import sys
import hashlib

sys.path.insert(0, str(Path(__file__).parent))
import training_submission_client as base

from agent_platform import training as owner
from dev_platform.contracts import canonical_sha
from perf_temporal.models import Binding, ReleaseRequest, Status
from temporalio.api.common.v1 import Payloads
from temporalio.api.history.v1 import HistoryEvent, WorkflowExecutionSignaledEventAttributes
from temporalio.api.workflowservice.v1 import QueryWorkflowResponse, SignalWorkflowExecutionResponse

from ergora.reference_training_release import main


async def spec():
    original = base.StartWorkflowExecutionRequest.FromString(base.base64.b64decode(base.record['request']))
    return (await base.converter.decode(original.input.payloads, [dict]))[0]


def evidence():
    root = Path(base.payload['project']['registration']['definition']['execution']['state_directory'])
    return base.json.loads((root / 'training/jobs/alpha/gate-report.json').read_bytes())['evidence_sha256']


class Service(base.Service):
    async def describe_workflow_execution(self, request, **kwargs):
        response = await super().describe_workflow_execution(request, **kwargs)
        if base.scenario == 'closed':
            response.workflow_execution_info.status = base.WorkflowExecutionStatus.COMPLETED
        if base.scenario == 'wrong-run':
            response.workflow_execution_info.execution.run_id = 'another-run'
        return response

    async def query_workflow(self, request, **kwargs):
        assert request.execution.run_id == base.run_id
        base.record['queries'] = base.record.get('queries', 0) + 1
        base.save()
        binding = Binding(**(await spec())['binding'])
        if base.scenario == 'status-binding':
            binding = replace(binding, manifest_sha='e' * 64)
        status = Status('POLLING' if base.scenario == 'phase-not-ready' else 'AWAITING_RELEASE', binding,
                        'local-perf-alpha', '0' * 64 if base.scenario == 'evidence-mismatch' else evidence(), None)
        return QueryWorkflowResponse(query_result=Payloads(payloads=await base.converter.encode([asdict(status)])))

    async def signal_workflow_execution(self, request, **kwargs):
        assert request.workflow_execution.run_id == base.run_id and request.signal_name == 'request_release'
        native = (await base.converter.decode(request.input.payloads, [ReleaseRequest]))[0]
        root = Path(base.payload['project']['registration']['definition']['execution']['state_directory'])
        prefix = root / 'ergora/training-approvals/alpha'
        intent = base.json.loads(Path(str(prefix) + '.intent.json').read_bytes())
        attempt = base.json.loads(Path(str(prefix) + '.attempt.json').read_bytes())
        ready = base.json.loads(Path(str(prefix) + '.receipt-ready.json').read_bytes())
        receipt = root / 'training/approvals' / (native.approval_receipt_id + '.json')
        assert ready['receipt_sha256'] == hashlib.sha256(receipt.read_bytes()).hexdigest()
        assert canonical_sha(intent) == attempt['intent_sha256'] == ready['intent_sha256']
        assert attempt['run_id'] == base.run_id and attempt['signal_sha256'] == canonical_sha(asdict(native))
        base.record['signals'] = base.record.get('signals', 0) + 1
        base.record['signal'] = base.base64.b64encode(request.input.SerializeToString()).decode()
        base.save()
        if base.scenario == 'lost-ack':
            raise base.RPCError('Accepted release, reply lost', base.RPCStatusCode.UNAVAILABLE, b'')
        if base.scenario == 'timeout-ack':
            await base.asyncio.sleep(5)
        return SignalWorkflowExecutionResponse()

    async def get_workflow_execution_history(self, request, **kwargs):
        response = await super().get_workflow_execution_history(request, **kwargs)
        if 'signal' in base.record and base.scenario != 'signal-missing':
            encoded = Payloads.FromString(base.base64.b64decode(base.record['signal']))
            value = deepcopy((await base.converter.decode(encoded.payloads, [dict]))[0])
            if base.scenario == 'foreign-receipt':
                value['approval_receipt_id'] = 'owner-someone-else'
            if base.scenario == 'foreign-evidence':
                value['evidence_sha'] = '0' * 64
            response.history.events.append(HistoryEvent(event_id=2,
                workflow_execution_signaled_event_attributes=WorkflowExecutionSignaledEventAttributes(
                    signal_name='request_release', input=Payloads(payloads=await base.converter.encode([value])))))
        return response


async def connect():
    return base.Client(Service())


base.connection.connect = base.native.connect = connect
if base.scenario in ('before-owner', 'after-owner'):
    original_write = owner.write

    def interrupted(path, value):
        if base.scenario == 'before-owner':
            raise ValueError('Interrupted before original owner receipt publication')
        original_write(path, value)
        raise ValueError('Interrupted after original owner receipt publication')

    owner.write = interrupted
main()
