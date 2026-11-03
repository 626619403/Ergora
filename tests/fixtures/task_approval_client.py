"""Original transport and signal handlers with a controllable persistent SDK port."""

import asyncio
import io
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from temporalio.service import RPCError, RPCStatusCode

from dev_platform import adapter, connection
from dev_platform.workflow import DevelopmentWorkflow
from ergora import reference_task_approval as approval_module
from ergora.reference_task_approval import _Approval, main

payload=json.load(sys.stdin)
sys.stdin=io.StringIO(json.dumps(payload))
scenario=os.environ.get('ERGORA_TEST_APPROVAL_SCENARIO','normal')
root=Path(payload['project']['registration']['definition']['execution']['state_directory'])/'sdk-fixture'
server=root/'server.json'
history=root/'approval-signals.jsonl'


def log(event):
    with (root/'calls.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps({'event':event})+'\n')


def saved():
    return json.loads(server.read_text())


class Handle:
    async def describe(self,**kwargs):
        log('approval-describe')
        if scenario=='not-found':
            raise RPCError('missing',RPCStatusCode.NOT_FOUND,b'')
        async def memo():
            return {} if scenario=='wrong-memo' else saved()['memo']
        return SimpleNamespace(run_id=saved()['run_id'],memo=memo)

    async def fetch_history_events(self,**kwargs):
        log('approval-history')
        assert kwargs['page_size'] in (1,100)
        yield SimpleNamespace(HasField=lambda key:key=='workflow_execution_started_event_attributes',event_id=1,
            workflow_execution_started_event_attributes=SimpleNamespace(input=SimpleNamespace(payloads=['spec'])))
        if kwargs['page_size']==100 and history.exists():
            for index,line in enumerate(history.read_text().splitlines(),2):
                body=json.loads(line)
                if scenario=='different-history-signal':
                    body['receipt_id']='another-owner-receipt'
                yield SimpleNamespace(HasField=lambda key:key=='workflow_execution_signaled_event_attributes',event_id=index,
                    workflow_execution_signaled_event_attributes=SimpleNamespace(signal_name='approve_plan',
                        input=SimpleNamespace(payloads=[body])))

    async def query(self,method,**kwargs):
        log('approval-query')
        assert method is DevelopmentWorkflow.status
        return {'phase':'WORKING' if scenario=='already-working' else 'AWAITING_PLAN_APPROVAL',
                'request_sha256':saved()['spec']['request_sha256'],
                'plan_sha256':'b'*64 if scenario=='old-plan' else 'a'*64}

    async def signal(self,method,body,**kwargs):
        log('approval-signal')
        assert method is DevelopmentWorkflow.approve_plan
        assert kwargs['rpc_timeout'].total_seconds()==20
        if scenario=='signal-not-sent':
            raise TimeoutError('Signal delivery was interrupted')
        workflow=DevelopmentWorkflow()
        workflow.spec=saved()['spec'];workflow.phase='AWAITING_PLAN_APPROVAL';workflow.plan_sha256='a'*64
        if scenario=='phase-race':workflow.phase='WORKING'
        workflow.approve_plan(body)
        (root/'approval-handler.json').write_text(json.dumps({'pending':workflow.pending_approval}))
        with history.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(body)+'\n')
        if scenario=='lost-ack':
            raise TimeoutError('Signal acknowledgment was lost')


class Converter:
    async def decode(self,payloads,types):
        return [saved()['spec']] if payloads==['spec'] else payloads


class Client:
    data_converter=Converter()
    def get_workflow_handle(self,workflow_id,*,run_id,result_type):
        assert workflow_id=='dev-task/'+payload['task_id']
        assert run_id==saved()['run_id']
        return Handle()


async def connect():
    log('approval-connect')
    if scenario=='slow-connect':await asyncio.sleep(3)
    if scenario=='offline':raise OSError('Fixture approval service is offline')
    return Client()


connection.connect=connect
publish=adapter.publish

def interrupted_publish(path,value):
    if scenario=='before-publish':raise OSError('Fixture before owner publication')
    result=publish(path,value)
    if scenario=='after-publish':raise OSError('Fixture after owner publication')
    return result

adapter.publish=interrupted_publish
if scenario=='expired' and payload['operation']=='prepare':
    approval_module.time=SimpleNamespace(time=lambda:time.time()-86401)
if scenario=='different-actor' and payload['operation']=='dispatch':
    _Approval.actor=staticmethod(lambda:'unix:99999:another-owner')
original_init=_Approval.__init__

def initialize(self,*args):
    original_init(self,*args)
    write=self.core.write
    def interrupted(path,value,**kwargs):
        for name,target in (('intent',self.intent_path),('attempt',self.attempt_path),('result',self.result_path)):
            if path==target and scenario=='before-'+name:raise OSError('Fixture before '+name)
            if path==target and scenario=='after-'+name:
                write(path,value,**kwargs)
                raise OSError('Fixture after '+name)
        return write(path,value,**kwargs)
    self.core.write=interrupted

_Approval.__init__=initialize
main()
