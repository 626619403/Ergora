"""Exercise the native read process against a deliberately read-only SDK client."""

import asyncio
from copy import deepcopy
from dataclasses import replace
import io
import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

from perf_temporal import connection
from perf_temporal.models import Binding, Outcome, Status
from temporalio.client import WorkflowExecutionStatus
from temporalio.service import RPCError, RPCStatusCode

from ergora.reference_training_runtime import main

payload = json.load(sys.stdin)
sys.stdin = io.StringIO(json.dumps(payload))
spec = payload['spec']
binding = Binding(**spec['binding'])
scenario = os.environ['ERGORA_TEST_TRAINING_RUNTIME']
run_id = payload['run_id'] or 'training-run-1'
handles = []


class Handle:
    async def describe(self, **kwargs):
        if scenario == 'not-found':
            raise RPCError('missing', RPCStatusCode.NOT_FOUND, b'')
        if scenario == 'unavailable':
            raise RPCError('unavailable', RPCStatusCode.UNAVAILABLE, b'')
        status = WorkflowExecutionStatus.RUNNING
        if scenario in ('gate-failed', 'cancel-unconfirmed', 'integrated', 'outcome-binding'):
            status = WorkflowExecutionStatus.COMPLETED
        if scenario == 'terminated':
            status = WorkflowExecutionStatus.TERMINATED
        return SimpleNamespace(run_id='another-run' if scenario == 'wrong-run' else run_id, status=status)

    async def fetch_history_events(self, **kwargs):
        if scenario != 'missing-history':
            yield SimpleNamespace(HasField=lambda name: name == 'workflow_execution_started_event_attributes',
                                  workflow_execution_started_event_attributes=SimpleNamespace(
                                      input=SimpleNamespace(payloads=['experiment'])))

    async def query(self, query, **kwargs):
        selected = replace(binding, manifest_sha='e' * 64) if scenario == 'status-binding' else binding
        return Status('AWAITING_RELEASE', selected, 'local-perf-' + binding.experiment_id, 'd' * 64, None)

    async def result(self, **kwargs):
        assert kwargs['follow_runs'] is False
        selected = replace(binding, manifest_sha='e' * 64) if scenario == 'outcome-binding' else binding
        phase = {'gate-failed': 'GATE_FAILED', 'cancel-unconfirmed': 'CANCEL_UNCONFIRMED',
                 'integrated': 'INTEGRATION_TASK_CREATED', 'outcome-binding': 'GATE_FAILED'}[scenario]
        return Outcome(phase, selected, 'local-perf-' + binding.experiment_id, detail='Synthetic CPU runtime contract')


def handle(wid, *, run_id, result_type):
    assert wid == 'perf-experiment/' + binding.experiment_id
    handles.append(run_id)
    return Handle()


async def connect():
    if scenario == 'timeout':
        await asyncio.sleep(5)
    original = deepcopy(spec)
    if scenario == 'input-collision':
        original['manifest_uri'] += '.another'
    if scenario == 'numeric-collision':
        original['poll_seconds'] = float(original['poll_seconds'])
    return SimpleNamespace(get_workflow_handle=handle,
                           data_converter=SimpleNamespace(decode=AsyncMock(return_value=[original])))


connection.connect = connect
main()
assert handles == ([payload['run_id']] if scenario == 'not-found' else [payload['run_id'], run_id])
