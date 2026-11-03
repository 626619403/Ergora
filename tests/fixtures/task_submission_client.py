"""Run native admission and transport against a durable, controllable SDK port."""

import asyncio
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.service import RPCError, RPCStatusCode

from agent_platform import core, doctor, projects
from dev_platform import connection
from ergora.reference_task_submission import _Submission, main


payload = json.load(sys.stdin)
sys.stdin = io.StringIO(json.dumps(payload))
scenario = os.environ.get('ERGORA_TEST_SUBMISSION_SCENARIO', 'normal')
fixture = Path(payload['project']['registration']['definition']['execution']['state_directory']) / 'sdk-fixture'
fixture.mkdir(exist_ok=True)
server = fixture / 'server.json'


def log(event):
    with (fixture / 'calls.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'event': event}) + '\n')


def report():
    log('doctor')
    return {'ready_for_real_tasks': scenario != 'doctor-blocked'}


doctor.report = report
if scenario == 'environment-blocked':
    def denied_environment():
        raise core.Blocked('Fixture connection environment denied')
    core.environment = denied_environment
if scenario == 'spec-read-drift':
    original_spec = core.task_spec
    def drifted_spec(task_id):
        spec = original_spec(task_id)
        spec['profile']['schema_version'] = True
        return spec
    core.task_spec = drifted_spec
if scenario == 'policy-blocked':
    def deny(*args):
        raise core.Blocked('Fixture policy denies this task type')
    projects.check_task_type = deny


class Handle:
    async def describe(self, **kwargs):
        log('describe')
        if scenario == 'lookup-unavailable':
            raise RPCError('unavailable', RPCStatusCode.UNAVAILABLE, b'')
        if not server.exists():
            raise RPCError('missing', RPCStatusCode.NOT_FOUND, b'')
        async def memo():
            return json.loads(server.read_text()).get('memo', {})
        return SimpleNamespace(run_id=json.loads(server.read_text())['run_id'], memo=memo)

    async def fetch_history_events(self, **kwargs):
        log('history')
        assert kwargs['page_size'] == 1
        yield SimpleNamespace(HasField=lambda name: name == 'workflow_execution_started_event_attributes',
                              workflow_execution_started_event_attributes=SimpleNamespace(input=SimpleNamespace(payloads=[])))


class Converter:
    async def decode(self, payloads, types):
        return [json.loads(server.read_text())['spec']]


class Client:
    data_converter = Converter()

    def get_workflow_handle(self, workflow_id, *, run_id, result_type):
        assert workflow_id == 'dev-task/' + payload['task_id'] and result_type is dict
        if run_id is not None:
            assert run_id == json.loads(server.read_text())['run_id']
        return Handle()

    async def start_workflow(self, run, spec, **kwargs):
        log('start')
        assert kwargs['id'] == 'dev-task/' + payload['task_id']
        assert kwargs['id_reuse_policy'] == WorkflowIDReusePolicy.REJECT_DUPLICATE
        assert kwargs['id_conflict_policy'] == WorkflowIDConflictPolicy.FAIL
        assert kwargs['retry_policy'].maximum_attempts == 1
        assert not server.exists(), 'Second start was attempted against an existing run'
        assert len(kwargs['memo']['ergora.submission_sha256']) == 64
        if scenario in ('race-foreign-run', 'race-rejection-lost'):
            server.write_text(json.dumps({'run_id': 'race-foreign-run', 'spec': spec, 'memo': {}}), encoding='utf-8')
            raise WorkflowAlreadyStartedError(kwargs['id'], 'DevelopmentWorkflow', run_id='race-foreign-run')
        server.write_text(json.dumps({'run_id': 'original-run', 'spec': spec, 'memo': kwargs['memo']}), encoding='utf-8')
        if scenario == 'lost-response':
            raise TimeoutError('Fixture response was lost after the server accepted start')
        return SimpleNamespace(result_run_id='original-run')


async def connect():
    log('connect')
    if scenario == 'slow-connect':
        await asyncio.sleep(3)
    if scenario == 'connect-blocked':
        raise OSError('Fixture Temporal service is offline')
    return Client()


connection.connect = connect
original_init = _Submission.__init__


def initialize(self, *args):
    original_init(self, *args)
    write = self.core.write
    def interrupted(path, value, **kwargs):
        if path == self.rejection_path and scenario == 'race-rejection-lost':
            raise OSError('Fixture rejection write was lost')
        for name, target in (('intent', self.intent_path), ('attempt', self.attempt_path), ('result', self.result_path)):
            if path == target and scenario == 'before-' + name:
                raise OSError('Fixture interruption before ' + name)
            if path == target and scenario == 'after-' + name:
                write(path, value, **kwargs)
                raise OSError('Fixture interruption after ' + name)
        return write(path, value, **kwargs)
    self.core.write = interrupted


_Submission.__init__ = initialize
main()
