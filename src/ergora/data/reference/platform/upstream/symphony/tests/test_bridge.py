import asyncio, json, os, sys, tempfile, time, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT.parent/'temporal'))
from common import atomic,load_config,validate_request,Blocked,read,read_bytes
from bridge import Bridge,admit
from configure import render
from codex_launcher import child_env
from temporal_transport import Transport,NotFound
from tracker import Tracker
from workspace import enqueue,prepare

class FakeTracker:
    def __init__(self):self.labels={'agent-ready'};self.closed=False;self.calls=[];self.fail=False
    def assert_startable(self,issue):
        if self.closed or 'agent-ready' not in self.labels:raise Blocked('Issue not ready')
    def transition(self,issue,source,target):
        if self.fail:raise OSError('tracker unavailable')
        if self.closed:return 'CLOSED_UNCHANGED'
        if source not in self.labels:return 'ALREADY' if target in self.labels else 'DIVERGED_UNCHANGED'
        self.labels.discard(source);self.labels.add(target);self.calls.append((issue,source,target));return 'UPDATED'

class FakeTransport:
    def __init__(self):self.spec=None;self.starts=0;self.lost=False;self.finished=False;self.phase='AWAITING_RELEASE'
    async def start(self,spec):
        self.starts+=1
        if self.spec is not None and self.spec!=spec:raise ValueError('conflicting input')
        self.spec=spec
        if self.lost:self.lost=False;raise TimeoutError('reply lost')
        return 'run-one'
    async def lookup(self,spec,run_id=None):
        if self.spec is None:raise NotFound()
        if spec!=self.spec:raise ValueError('conflicting input')
        return None,SimpleNamespace(run_id='run-one')
    async def poll(self,spec,run_id):
        await self.lookup(spec,run_id)
        return {'run_id':'run-one','terminal':self.finished,'phase':self.phase}

def fixture(root):
    c={'schema_version':1,'provider':'gitlab','project':'group/project','api_url':'https://gitlab.example/api/v4',
       'token_env':'GITLAB_PAT','repo_url':'https://gitlab.example/group/project.git','ready_label':'agent-ready','max_concurrent_agents':3,
       'codex_bin':'/usr/bin/codex','symphony_bin':'/usr/bin/symphony','dashboard_port':4000}
    for key in ['workspace_root','outbox','receipts','approvals','state_dir']:c[key]=str(root/key);Path(c[key]).mkdir()
    c['baseline_file']=str(root/'baseline.json')
    atomic(c['baseline_file'],{'baseline_id':'b1','commit':'b'*40,'config_sha256':'d'*64,'workload_fingerprint':'e'*64})
    r={'schema_version':1,'tracker':{'kind':'gitlab','project':'group/project','issue_id':'7'},'baseline_id':'b1',
       'experiment':{'binding':{'experiment_id':'project-gl7-r1','candidate_sha':'a'*40,'baseline_sha':'b'*40,'manifest_sha':'c'*64},
                     'manifest_uri':'https://artifacts.example/immutable.json','poll_seconds':30,'max_run_seconds':600,'release_wait_seconds':600,'cancel_wait_seconds':60}}
    path=Path(c['outbox'])/'project-gl7-r1.json';atomic(path,r);config=root/'config.json';atomic(config,c)
    return c,r,path,config

class BridgeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.c,self.r,self.path,self.config=fixture(self.root)
        self.tr=FakeTracker();self.t=FakeTransport();self.b=Bridge(self.c,self.t,self.tr)
    def tearDown(self):self.b.close();self.tmp.cleanup()
    def grant(self):admit(self.c,self.path,'ci-approved-test',time.time()+3600)
    async def test_unapproved_never_starts(self):
        errors=await self.b.tick();self.assertTrue(errors);self.assertEqual(self.t.starts,0)
    async def test_repeated_request_starts_once_and_waits(self):
        self.grant();self.assertEqual(await self.b.tick(),[]);self.assertEqual(await self.b.tick(),[])
        self.assertEqual(self.t.starts,1);self.assertEqual(self.tr.labels,{'agent-waiting'})
    async def test_lost_start_reply_attaches(self):
        self.grant();self.t.lost=True;self.assertTrue(await self.b.tick());self.assertEqual(await self.b.tick(),[]);self.assertEqual(self.t.starts,1)
    async def test_restart_uses_durable_ledger(self):
        self.grant();await self.b.tick();self.b.close();self.b=Bridge(self.c,self.t,self.tr);await self.b.tick();self.assertEqual(self.t.starts,1)
    async def test_ambiguous_missing_execution_never_restarts(self):
        self.grant();self.b.ingest(self.path);self.b.update('project-gl7-r1',phase='SUBMITTING');await self.b.tick();self.assertEqual(self.t.starts,0)
    async def test_changed_request_id_rejected(self):
        self.grant();await self.b.tick();r=read(self.path);r['experiment']['binding']['candidate_sha']='f'*40;atomic(self.path,r)
        errors=await self.b.tick();self.assertIn('Immutable',errors[0]['detail']);self.assertEqual(self.t.starts,1)
    async def test_stale_baseline_never_starts(self):
        self.grant();b=read(self.c['baseline_file']);b['config_sha256']='9'*64;atomic(self.c['baseline_file'],b)
        self.assertTrue(await self.b.tick());self.assertEqual(self.t.starts,0)
    async def test_closed_or_unready_issue_never_starts(self):
        self.grant();self.tr.closed=True;self.assertTrue(await self.b.tick());self.assertEqual(self.t.starts,0)
    async def test_concurrent_candidate_same_issue_rejected(self):
        self.grant();await self.b.tick();r=read(self.path);r['experiment']['binding']['experiment_id']='project-gl7-r2';p=self.path.with_name('project-gl7-r2.json');atomic(p,r);admit(self.c,p,'ci-approved-2',time.time()+3600)
        self.assertTrue(await self.b.tick());self.assertEqual(self.t.starts,1)
    async def test_gate_wait_is_not_release(self):
        self.grant();await self.b.tick();self.assertEqual(self.tr.labels,{'agent-waiting'});self.assertNotIn('agent-review',self.tr.labels)
    async def test_success_routes_review_without_ready(self):
        self.grant();self.t.finished=True;self.t.phase='INTEGRATION_TASK_CREATED';await self.b.tick();self.assertEqual(self.tr.labels,{'agent-review'})
    async def test_failure_routes_blocked(self):
        self.grant();self.t.finished=True;self.t.phase='GATE_FAILED';await self.b.tick();self.assertEqual(self.tr.labels,{'agent-blocked'})
    async def test_tracker_failure_does_not_resubmit(self):
        self.grant();self.tr.fail=True;self.assertTrue(await self.b.tick());self.tr.fail=False;self.assertEqual(await self.b.tick(),[]);self.assertEqual(self.t.starts,1)
    async def test_old_result_cannot_overwrite_new_head(self):
        self.grant();await self.b.tick();self.t.finished=True;self.t.phase='INTEGRATION_TASK_CREATED'
        self.b.db.execute("UPDATE issue_heads SET experiment='another' WHERE issue='7'");self.b.db.commit()
        self.assertTrue(await self.b.tick());self.assertEqual(self.tr.labels,{'agent-waiting'})
    async def test_expired_admission_never_starts(self):
        self.grant();p=Path(self.c['approvals'])/'project-gl7-r1.json';g=read(p);g['expires_at']=0;atomic(p,g)
        self.assertTrue(await self.b.tick());self.assertEqual(self.t.starts,0)
    def test_scope_and_uri_rejected(self):
        for edit in ('project','uri'):
            r=json.loads(json.dumps(self.r))
            if edit=='project':r['tracker']['project']='other/repo'
            else:r['experiment']['manifest_uri']='https://store/x?token=secret'
            with self.assertRaises(Blocked):validate_request(self.c,json.dumps(r).encode())
    def test_credentials_removed(self):
        env=child_env({'PATH':'/bin','OPENAI_API_KEY':'model','GITLAB_PAT':'tracker','TEMPORAL_API_KEY':'control','UNRELATED_SECRET':'s'})
        self.assertEqual(env,{'PATH':'/bin','OPENAI_API_KEY':'model'})
    def test_native_workflows_github_gitlab(self):
        import yaml
        for kind in ['gitlab','github']:
            c=dict(self.c,provider=kind);atomic(self.config,c);data=yaml.safe_load(render(self.config).split('---')[1]);self.assertEqual(data['tracker']['kind'],kind)
            self.assertEqual(data['tracker']['required_labels'],['agent-ready']);self.assertIn('enqueue',data['hooks']['after_run']);self.assertNotIn('Merging',data['tracker']['active_states'])
    def test_workspace_identity_and_recovery(self):
        w=Path(self.c['workspace_root'])/'GL-7';(w/'.symphony').mkdir(parents=True);atomic(w/'.symphony/handoff.json',self.r)
        with patch('workspace.subprocess.check_output',side_effect=['a'*40+'\n','']):self.assertEqual(enqueue(self.c,w),'QUEUED_FOR_ADMISSION')
        with patch('workspace.subprocess.check_output',side_effect=['a'*40+'\n','']),self.assertRaisesRegex(Blocked,'Pending immutable'):prepare(self.c,w)
        wrong=Path(self.c['workspace_root'])/'GL-8';(wrong/'.symphony').mkdir(parents=True);atomic(wrong/'.symphony/handoff.json',self.r)
        with self.assertRaisesRegex(Blocked,'identity'):enqueue(self.c,wrong)
    def test_terminal_receipt_allows_explicit_rework(self):
        from common import digest
        w=Path(self.c['workspace_root'])/'GL-7';(w/'.symphony').mkdir(parents=True);atomic(w/'.symphony/handoff.json',self.r)
        raw=read_bytes(w/'.symphony/handoff.json')
        receipt={'terminal':True,'safe_to_rework':True,'tracker_sync':'UPDATED','experiment_id':'project-gl7-r1','issue_id':'7','request_sha256':digest(raw)}
        atomic(Path(self.c['receipts'])/'project-gl7-r1.json',receipt)
        self.assertEqual(prepare(self.c,w),'READY_FOR_EXPLICIT_REWORK')
        self.assertFalse((w/'.symphony/handoff.json').exists());self.assertTrue((w/'.symphony/history/project-gl7-r1.json').exists())
    def test_terminal_receipt_wrong_binding_rejected(self):
        w=Path(self.c['workspace_root'])/'GL-7';(w/'.symphony').mkdir(parents=True);atomic(w/'.symphony/handoff.json',self.r)
        atomic(Path(self.c['receipts'])/'project-gl7-r1.json',{'terminal':True,'safe_to_rework':True,'tracker_sync':'UPDATED','experiment_id':'wrong'})
        with self.assertRaisesRegex(Blocked,'Receipt binding'):prepare(self.c,w)
    def test_symlink_request_rejected(self):
        w=Path(self.c['workspace_root'])/'GL-7';(w/'.symphony').mkdir(parents=True);(w/'.symphony/handoff.json').symlink_to(self.path)
        with self.assertRaises(OSError):enqueue(self.c,w)
    def test_gitlab_label_request_preserves_unrelated(self):
        tr=Tracker(self.c);calls=[]
        def req(method,path,body=None):
            calls.append((method,path,body));return {'state':'opened','labels':['agent-ready','bug']}
        with patch.object(tr,'request',side_effect=req):tr.transition('7','agent-ready','agent-waiting')
        self.assertEqual(calls[-1][2],{'add_labels':'agent-waiting','remove_labels':'agent-ready'})
        self.assertIn('/projects/group%2Fproject/issues/7',calls[-1][1])
    def test_github_label_partial_failure_retry(self):
        tr=Tracker(dict(self.c,provider='github'));calls=[]
        def req(method,path,body=None):
            calls.append((method,path,body));return {'state':'open','labels':[{'name':'agent-ready'},{'name':'agent-waiting'}]}
        with patch.object(tr,'request',side_effect=req):tr.transition('7','agent-ready','agent-waiting')
        self.assertEqual([x[0] for x in calls],['GET','POST','DELETE'])

@unittest.skipUnless(os.environ.get('RUN_TEMPORAL_INTEGRATION')=='1','Opt-in real Temporal test service')
class RealTemporal(unittest.IsolatedAsyncioTestCase):
    async def test_real_server_bridge_start_attach_complete(self):
        from temporalio.testing import WorkflowEnvironment
        from temporalio.worker import Worker
        from perf_temporal.activities import Activities
        from perf_temporal.workflow import ExperimentWorkflow
        from perf_temporal.models import ReleaseRequest,workflow_id
        from temporal_transport import experiment
        from importlib.util import spec_from_file_location,module_from_spec
        ms=spec_from_file_location('temporal_test_fixtures',ROOT.parent/'temporal/tests/test_scaffold.py');mod=module_from_spec(ms);ms.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            c,r,path,cfg=fixture(Path(tmp));exp,raw=mod.fixture('project-gl7-r1');e=json.loads(json.dumps(__import__('dataclasses').asdict(exp)));e['manifest_uri']='https://artifacts.example/manifest.json'
            r['experiment']=e;atomic(path,r);admit(c,path,'ci-test',time.time()+3600)
            adapter=mod.FakeAdapter(raw);activities=Activities(adapter)
            async with await WorkflowEnvironment.start_time_skipping() as env:
                async with Worker(env.client,task_queue='bridge-test',workflows=[ExperimentWorkflow],activities=[activities.submit_or_lookup,activities.poll_job,activities.collect_and_gate,activities.cancel_exact_job,activities.create_integration_task]):
                    transport=Transport(env.client,'bridge-test');tracker=FakeTracker();b=Bridge(c,transport,tracker)
                    try:
                        self.assertEqual(await b.tick(),[]);self.assertEqual(await b.tick(),[])
                        handle=env.client.get_workflow_handle_for(ExperimentWorkflow.run,workflow_id(exp.binding))
                        for _ in range(100):
                            status=await handle.query(ExperimentWorkflow.status)
                            if status.phase=='AWAITING_RELEASE':break
                            await asyncio.sleep(.02)
                        self.assertEqual(status.phase,'AWAITING_RELEASE');self.assertEqual(adapter.create_count,1)
                        # Same input attaches. Different URI with same ID is a conflict.
                        rid=await transport.start(e);self.assertIsNotNone(rid)
                        bad=dict(e,manifest_uri='https://artifacts.example/other.json')
                        with self.assertRaisesRegex(ValueError,'collision'):await transport.start(bad)
                        await handle.signal(ExperimentWorkflow.request_release,ReleaseRequest(exp.binding,'c'*64,'test-trusted-receipt'))
                        outcome=await handle.result();self.assertEqual(outcome.status,'INTEGRATION_TASK_CREATED')
                        self.assertEqual(await b.tick(),[]);self.assertEqual(tracker.labels,{'agent-review'});self.assertEqual(adapter.create_count,1)
                    finally:b.close()
if __name__=='__main__':unittest.main(verbosity=2)
