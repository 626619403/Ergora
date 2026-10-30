"""No release/cancel credentials exposed to Codex. Starts one immutable execution."""
from dataclasses import asdict
from datetime import timedelta
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'temporal'))
from temporalio.common import RetryPolicy, WorkflowIDReusePolicy, WorkflowIDConflictPolicy
from temporalio.client import WorkflowExecutionStatus
from temporalio.service import RPCError, RPCStatusCode
from temporalio.exceptions import WorkflowAlreadyStartedError
from perf_temporal.models import Binding, Experiment, Outcome, workflow_id
from perf_temporal.workflow import ExperimentWorkflow

class NotFound(Exception):pass

def experiment(data):
    data=dict(data);data['binding']=Binding(**data['binding']);e=Experiment(**data);e.validate();return e

class Transport:
    def __init__(self,client,queue):self.client,self.queue=client,queue
    async def lookup(self,spec,run_id=None):
        e=experiment(spec);h=self.client.get_workflow_handle(workflow_id(e.binding),run_id=run_id,result_type=Outcome)
        try:desc=await h.describe(rpc_timeout=timedelta(seconds=20))
        except RPCError as err:
            if err.status==RPCStatusCode.NOT_FOUND:raise NotFound from err
            raise
        # Bind the whole original input, including timeout and URI, not only the ID/query.
        h=self.client.get_workflow_handle(h.id,run_id=desc.run_id,result_type=Outcome)
        started=None
        async for event in h.fetch_history_events(page_size=1,rpc_timeout=timedelta(seconds=20)):
            if event.HasField('workflow_execution_started_event_attributes'):
                started=event.workflow_execution_started_event_attributes
            break
        if started is None:raise ValueError('Original workflow input is unavailable; reconcile instead of restarting')
        values=await self.client.data_converter.decode(started.input.payloads,[Experiment])
        if not values or values[0]!=e:raise ValueError('Workflow ID collision: original Experiment differs')
        return h,desc
    async def start(self,spec):
        e=experiment(spec)
        try:
            h=await self.client.start_workflow(ExperimentWorkflow.run,e,id=workflow_id(e.binding),task_queue=self.queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,id_conflict_policy=WorkflowIDConflictPolicy.FAIL,
                retry_policy=RetryPolicy(maximum_attempts=1),rpc_timeout=timedelta(seconds=20))
            return h.result_run_id
        except WorkflowAlreadyStartedError:
            _,desc=await self.lookup(spec)
            return desc.run_id
    async def poll(self,spec,run_id):
        h,desc=await self.lookup(spec,run_id)
        if desc.status==WorkflowExecutionStatus.RUNNING:
            s=await h.query(ExperimentWorkflow.status,rpc_timeout=timedelta(seconds=20))
            return {'run_id':desc.run_id,'terminal':False,'phase':s.phase,'status':asdict(s)}
        if desc.status==WorkflowExecutionStatus.COMPLETED:
            outcome=await h.result(follow_runs=False,rpc_timeout=timedelta(seconds=20))
            return {'run_id':desc.run_id,'terminal':True,'phase':outcome.status,'outcome':asdict(outcome)}
        return {'run_id':desc.run_id,'terminal':True,'phase':'NEEDS_RECONCILIATION','temporal_status':desc.status.name}
