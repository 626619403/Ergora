"""Original native cancellation over a controllable persistent SDK port."""

import asyncio
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

from temporalio.client import WorkflowExecutionStatus
from temporalio.service import RPCError, RPCStatusCode

from dev_platform import connection
from dev_platform.workflow import DevelopmentWorkflow
from ergora.reference_task_cancellation import _Cancellation, main

payload=json.load(sys.stdin)
sys.stdin=io.StringIO(json.dumps(payload))
scenario=os.environ.get('ERGORA_TEST_CANCELLATION_SCENARIO','normal')
root=Path(payload['project']['registration']['definition']['execution']['state_directory'])/'sdk-fixture'
server=root/'server.json'
history=root/'cancellation-signals.jsonl'


def log(event):
    with (root/'calls.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps({'event':event})+'\n')


def saved():
    return json.loads(server.read_text())


class Handle:
    async def describe(self,**kwargs):
        log('cancellation-describe')
        if scenario=='not-found':
            raise RPCError('missing',RPCStatusCode.NOT_FOUND,b'')
        if scenario=='rpc-unavailable':
            raise RPCError('unavailable',RPCStatusCode.UNAVAILABLE,b'')
        async def memo():
            return {} if scenario=='wrong-memo' else saved()['memo']
        closed='COMPLETED' if scenario in ('closed-before-result','closed-after-result') else scenario[7:]
        status=WorkflowExecutionStatus[closed] if scenario.startswith('closed-') else WorkflowExecutionStatus.RUNNING
        return SimpleNamespace(run_id=saved()['run_id'],status=status,memo=memo)

    async def fetch_history_events(self,**kwargs):
        log('cancellation-history')
        assert kwargs['page_size'] in (1,100)
        yield SimpleNamespace(HasField=lambda key:key=='workflow_execution_started_event_attributes',event_id=1,
            workflow_execution_started_event_attributes=SimpleNamespace(input=SimpleNamespace(payloads=['spec'])))
        if kwargs['page_size']==100:
            if scenario=='history-rpc-unavailable':
                raise RPCError('history unavailable',RPCStatusCode.UNAVAILABLE,b'')
            if history.exists():
                for index,line in enumerate(history.read_text().splitlines(),2):
                    body=json.loads(line)
                    if scenario=='different-history-operation':body['ergora_operation_sha256']='b'*64
                    if scenario=='same-reason-without-marker':body.pop('ergora_operation_sha256')
                    if scenario=='different-history-reason':body['reason']='Another owner reason'
                    yield SimpleNamespace(HasField=lambda key:key=='workflow_execution_signaled_event_attributes',event_id=index,
                        workflow_execution_signaled_event_attributes=SimpleNamespace(signal_name='request_cancel',
                            input=SimpleNamespace(payloads=[body])))

    async def signal(self,method,body,**kwargs):
        log('cancellation-signal')
        assert method is DevelopmentWorkflow.request_cancel
        assert kwargs['rpc_timeout'].total_seconds()==20
        assert len(body['ergora_operation_sha256'])==64
        if scenario=='signal-not-sent':raise TimeoutError('Signal delivery was interrupted')
        workflow=DevelopmentWorkflow()
        workflow.spec=saved()['spec'];workflow.phase='WORKING'
        workflow.request_cancel(body)
        (root/'cancellation-handler.json').write_text(json.dumps({'reason':workflow.cancel_reason}))
        with history.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(body)+'\n')
        if scenario=='lost-ack':raise TimeoutError('Signal acknowledgment was lost')


class Converter:
    async def decode(self,payloads,types):
        if payloads==['spec']:
            spec=saved()['spec']
            if scenario=='wrong-spec':spec['profile']['schema_version']=True
            return [spec]
        return payloads


class Client:
    data_converter=Converter()
    def get_workflow_handle(self,workflow_id,*,run_id,result_type):
        assert workflow_id=='dev-task/'+payload['task_id']
        assert run_id==saved()['run_id']
        return Handle()


async def connect():
    log('cancellation-connect')
    if scenario=='slow-connect':await asyncio.sleep(3)
    if scenario=='offline':raise OSError('Fixture cancellation service is offline')
    return Client()


connection.connect=connect
if scenario=='different-actor' and payload['operation']=='dispatch':
    _Cancellation.actor=staticmethod(lambda:'unix:99999:another-user')
original_init=_Cancellation.__init__


def initialize(self,*args):
    original_init(self,*args)
    write=self.core.write
    def interrupted(path,value,**kwargs):
        for name,target in (('intent',self.intent_path),('attempt',self.attempt_path),('result',self.result_path)):
            if path==target and scenario in ('before-'+name,'closed-before-'+name):raise OSError('Fixture before '+name)
            if path==target and scenario in ('after-'+name,'closed-after-'+name):
                write(path,value,**kwargs)
                raise OSError('Fixture after '+name)
        return write(path,value,**kwargs)
    self.core.write=interrupted


_Cancellation.__init__=initialize
main()
