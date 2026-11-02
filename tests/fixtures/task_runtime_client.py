"""Exercise the real native transport against a read-only SDK client fixture."""

from copy import deepcopy
import asyncio
import io
import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

from temporalio.client import WorkflowExecutionStatus
from temporalio.service import RPCError, RPCStatusCode

from dev_platform import connection
from ergora.reference_task_runtime import main


payload = json.load(sys.stdin)
sys.stdin = io.StringIO(json.dumps(payload))
spec = payload['spec']
scenario = os.environ['ERGORA_TEST_RUNTIME_SCENARIO']
run_id = payload['run_id'] or 'run-1'
queries = []


class Handle:
    async def describe(self, **kwargs):
        if scenario == 'not-found':
            raise RPCError('missing', RPCStatusCode.NOT_FOUND, b'')
        if scenario == 'unavailable':
            raise RPCError('unavailable', RPCStatusCode.UNAVAILABLE, b'')
        status = {'completed': WorkflowExecutionStatus.COMPLETED, 'unconfirmed': WorkflowExecutionStatus.COMPLETED,
                  'terminated': WorkflowExecutionStatus.TERMINATED}.get(scenario, WorkflowExecutionStatus.RUNNING)
        return SimpleNamespace(run_id=run_id, status=status)

    async def fetch_history_events(self, **kwargs):
        assert kwargs['page_size'] == 1
        yield SimpleNamespace(HasField=lambda field: field == 'workflow_execution_started_event_attributes',
                              workflow_execution_started_event_attributes=SimpleNamespace(input=SimpleNamespace(payloads=[])))

    async def query(self, query, **kwargs):
        return {'phase': 'AWAITING_PLAN_APPROVAL', 'request_sha256': spec['request_sha256'], 'plan_sha256': 'a'*64}

    async def result(self, **kwargs):
        assert kwargs['follow_runs'] is False
        return {'status': 'CANCEL_UNCONFIRMED' if scenario == 'unconfirmed' else 'REVIEW_READY', 'candidate_sha': 'b'*40}


def handle(workflow_id, *, run_id, result_type):
    assert workflow_id == 'dev-task/' + spec['request']['task_id']
    queries.append(run_id)
    return Handle()


async def connect():
    if scenario == 'timeout':
        await asyncio.sleep(5)
    if scenario == 'connection-failed':
        raise RuntimeError('controlled connection failure')
    original = deepcopy(spec)
    if scenario == 'collision':
        original['request']['input']['goal'] = 'Another admitted spec'
    return SimpleNamespace(get_workflow_handle=handle,
                           data_converter=SimpleNamespace(decode=AsyncMock(return_value=[original])))


connection.connect = connect
main()
assert queries == ([payload['run_id']] if scenario == 'not-found' else [payload['run_id'], run_id])
