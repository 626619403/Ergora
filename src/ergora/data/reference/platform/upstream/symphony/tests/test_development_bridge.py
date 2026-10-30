"""Development v2 routing shares the durable ledger with training v1."""
import asyncio, json, os, sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT.parent/'platform'))
from test_bridge import fixture,FakeTracker,FakeTransport
from common import atomic,read,read_bytes,load_config,validate_request,Blocked,request_spec,digest
from bridge import Bridge,admit
from workspace import enqueue,prepare
from configure import render
from temporalio import workflow

@workflow.defn(name='DevelopmentWorkflow',sandboxed=False)
class CompletionFixture:
    @workflow.run
    async def run(self,spec:dict)->dict:
        return {'status':'REVIEW_READY','candidate_sha':spec['request']['repository']['starting_sha']}


def dev_fixture(root):
    c,legacy,legacy_path,cfg=fixture(root)
    legacy_path.unlink()
    c.pop('baseline_file')
    c['enabled_task_types']=['repository-governance','large-change']
    c['repository_state_file']=str(root/'repository-state.json')
    atomic(c['repository_state_file'],{'project':c['project'],'base_sha':'b'*40,'policy_revision':'v1'})
    atomic(cfg,c)
    p=ROOT.parent/'platform/task-types/repository-governance/examples/request.json'
    r=read(p);r['task_id']='project-gl7-dev-r1';r['tracker']={'kind':'gitlab','project':c['project'],'issue_id':'7'}
    r['repository']={'base_sha':'b'*40,'starting_sha':'a'*40}
    path=Path(c['outbox'])/(r['task_id']+'.json');atomic(path,r)
    return load_config(cfg),r,path,cfg

class DevelopmentBridgeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.c,self.r,self.path,self.cfg=dev_fixture(self.root)
        self.t=FakeTransport();self.tr=FakeTracker();self.b=Bridge(self.c,self.t,self.tr)
    def tearDown(self):self.b.close();self.tmp.cleanup()
    def grant(self):admit(self.c,self.path,'trusted-ci-receipt',time.time()+3600)
    async def test_development_needs_no_training_baseline(self):
        self.grant();self.assertEqual(await self.b.tick(),[])
        self.assertEqual(self.t.spec['request']['task_type'],'repository-governance')
        receipt=read(Path(self.c['receipts'])/(self.r['task_id']+'.json'))
        self.assertEqual(receipt['workflow_id'],'dev-task/'+self.r['task_id'])
        self.assertNotIn('experiment_id',receipt)
    async def test_stale_repo_policy_never_starts(self):
        self.grant();p=self.c['repository_state_file'];v=read(p);v['policy_revision']='v2';atomic(p,v)
        self.assertTrue(await self.b.tick());self.assertEqual(self.t.starts,0)
    async def test_plan_wait_not_review_ready(self):
        self.grant();self.t.phase='AWAITING_PLAN_APPROVAL';await self.b.tick()
        self.assertEqual(self.tr.labels,{'agent-waiting'})
        self.t.finished=True;self.t.phase='REVIEW_READY';await self.b.tick()
        self.assertEqual(self.tr.labels,{'agent-review'})
    async def test_lost_reply_restart_attaches_original_spec(self):
        self.grant();self.t.lost=True;self.assertTrue(await self.b.tick());self.b.close()
        self.b=Bridge(self.c,self.t,self.tr);self.assertEqual(await self.b.tick(),[]);self.assertEqual(self.t.starts,1)
    async def test_running_keeps_admitted_spec_if_registry_changes(self):
        self.grant();await self.b.tick()
        row=self.b.db.execute('SELECT * FROM runs').fetchone()
        with patch('bridge.request_spec',side_effect=ValueError('registry upgraded')):
            await self.b.advance(row)
        self.assertEqual(self.t.starts,1)
    def test_disabled_type_and_wrong_profile_rejected(self):
        c=dict(self.c,enabled_task_types=['large-change'])
        with self.assertRaises(Blocked):validate_request(c,read_bytes(self.path))
        r=dict(self.r,profile_sha256='0'*64);atomic(self.path,r)
        with self.assertRaises(ValueError):self.grant()
    def test_development_workspace_handoff_and_rework(self):
        w=Path(self.c['workspace_root'])/'GL-7';(w/'.symphony').mkdir(parents=True)
        atomic(w/'.symphony/handoff.json',self.r)
        with patch('workspace.subprocess.check_output',side_effect=['a'*40+'\n','']):
            self.assertEqual(enqueue(self.c,w),'QUEUED_FOR_ADMISSION')
        raw=read_bytes(w/'.symphony/handoff.json')
        atomic(Path(self.c['receipts'])/(self.r['task_id']+'.json'),{'terminal':True,'safe_to_rework':True,'tracker_sync':'UPDATED','task_id':self.r['task_id'],'issue_id':'7','request_sha256':digest(raw)})
        self.assertEqual(prepare(self.c,w),'READY_FOR_EXPLICIT_REWORK')
    def test_development_prompt_is_routed(self):
        txt=render(self.cfg)
        self.assertIn('repository-governance, large-change',txt)
        self.assertIn('schema_version=2',txt)
        self.assertNotIn('@TASK_TYPES@',txt)
    def test_additional_trusted_type_is_configuration_not_hardcoded(self):
        c=dict(self.c,enabled_task_types=['dependency-upgrade']);atomic(self.cfg,c)
        with patch('dev_platform.registry.registered_types',return_value=['dependency-upgrade']):
            self.assertEqual(load_config(self.cfg)['enabled_task_types'],['dependency-upgrade'])
        with self.assertRaises(Blocked):load_config(self.cfg)
    async def test_blocked_review_not_success(self):
        self.grant();self.t.finished=True;self.t.phase='BLOCKED';await self.b.tick()
        self.assertEqual(self.tr.labels,{'agent-blocked'})
    async def test_type_switch_cannot_share_active_issue(self):
        self.grant();await self.b.tick()
        other=read(ROOT.parent/'platform/task-types/large-change/examples/request.json')
        other['tracker']=self.r['tracker'];other['repository']=self.r['repository'];other['task_id']='project-gl7-large-r2'
        p=Path(self.c['outbox'])/(other['task_id']+'.json');atomic(p,other)
        admit(self.c,p,'trusted-ci-2',time.time()+3600)
        self.assertTrue(await self.b.tick());self.assertEqual(self.t.starts,1)

@unittest.skipUnless(os.getenv('RUN_TEMPORAL_INTEGRATION')=='1','Opt-in Temporal test service')
class DevelopmentTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_transport_binds_original_input_and_closed_execution(self):
        from temporalio import workflow
        from temporalio.testing import WorkflowEnvironment
        from temporalio.worker import Worker
        from task_transport import DevelopmentTransport,TaskTransport
        with tempfile.TemporaryDirectory() as tmp:
            c,r,path,cfg=dev_fixture(Path(tmp));spec=request_spec(r)
            async with await WorkflowEnvironment.start_time_skipping() as env:
                async with Worker(env.client,task_queue='dev-transport-test',workflows=[CompletionFixture]):
                    tr=DevelopmentTransport(env.client,'dev-transport-test')
                    rid=await tr.start(spec);h,_=await tr.lookup(spec,rid);await h.result()
                    self.assertEqual(await tr.start(spec),rid)
                    out=await tr.poll(spec,rid);self.assertEqual(out['phase'],'REVIEW_READY');self.assertTrue(out['terminal'])
                    changed=json.loads(json.dumps(r));changed['input']['goal']+=' Different.'
                    with self.assertRaisesRegex(ValueError,'collision'):await tr.start(request_spec(changed))
                    router=TaskTransport(env.client,'train','dev')
                    self.assertIs(router.route(spec),router.development)
                    self.assertIs(router.route({'binding':{}}),router.training)


class RecoveryBoundaryTests(unittest.IsolatedAsyncioTestCase):
    setUp=DevelopmentBridgeTests.setUp
    tearDown=DevelopmentBridgeTests.tearDown
    grant=DevelopmentBridgeTests.grant
    async def test_unconfirmed_cancel_holds_issue_and_workspace(self):
        self.grant();self.t.finished=True;self.t.phase='CANCEL_UNCONFIRMED';await self.b.tick()
        row=self.b.db.execute('SELECT * FROM runs').fetchone();self.assertEqual(row['phase'],'BLOCKED_UNRESOLVED')
        receipt=read(Path(self.c['receipts'])/(self.r['task_id']+'.json'));self.assertFalse(receipt['safe_to_rework'])
        w=Path(self.c['workspace_root'])/'GL-7';(w/'.symphony').mkdir(parents=True);atomic(w/'.symphony/handoff.json',self.r)
        with patch('workspace.subprocess.check_output',side_effect=['a'*40+'\n','']),self.assertRaises(Blocked):prepare(self.c,w)
        other=json.loads(json.dumps(self.r));other['task_id']='project-gl7-dev-r2';p=self.path.with_name(other['task_id']+'.json');atomic(p,other)
        admit(self.c,p,'trusted-second',time.time()+3600);self.tr.labels={'agent-ready'}
        self.assertTrue(await self.b.tick());self.assertEqual(self.t.starts,1)
    async def test_reconcile_is_exact_and_recovers_missing_receipt(self):
        from bridge import reconcile
        self.grant();self.t.finished=True;self.t.phase='NEEDS_RECONCILIATION';await self.b.tick()
        evidence={'schema_version':1,'task_id':self.r['task_id'],'issue_id':'7','request_sha256':digest(read_bytes(self.path)),
          'workflow_id':'dev-task/'+self.r['task_id'],'run_id':'run-one','all_external_work_stopped':True,
          'operator':'trusted-operator','evidence_uri':'https://evidence.example/cleanup/7','evidence_sha256':'f'*64,'confirmed_at':time.time()}
        p=self.root/'cleanup.json';bad=dict(evidence,run_id='wrong');atomic(p,bad)
        with self.assertRaises(Blocked):reconcile(self.c,self.r['task_id'],p)
        atomic(p,evidence);(Path(self.c['receipts'])/(self.r['task_id']+'.json')).unlink()
        self.assertIn('RECONCILED',reconcile(self.c,self.r['task_id'],p))
        receipt=read(Path(self.c['receipts'])/(self.r['task_id']+'.json'));self.assertTrue(receipt['safe_to_rework'])
        self.assertEqual(receipt['task_id'],self.r['task_id'])
    async def test_legacy_unknown_result_not_released(self):
        # Use separate old-config ledger to verify training v1 also stays held.
        with tempfile.TemporaryDirectory() as td:
            c,r,path,cfg=fixture(Path(td));admit(c,path,'legacy-ci',time.time()+3600)
            tr=FakeTracker();transport=FakeTransport();transport.finished=True;transport.phase='CANCEL_UNCONFIRMED';bridge=Bridge(c,transport,tr)
            try:
                self.assertEqual(await bridge.tick(),[])
                self.assertEqual(bridge.db.execute('SELECT phase FROM runs').fetchone()['phase'],'BLOCKED_UNRESOLVED')
            finally:bridge.close()
    async def test_upgrade_known_terminal_regenerates_safe_receipt(self):
        self.grant();self.t.finished=True;self.t.phase='REVIEW_READY';await self.b.tick()
        p=Path(self.c['receipts'])/(self.r['task_id']+'.json');old=read(p);old.pop('safe_to_rework');atomic(p,old)
        self.b.close();self.b=Bridge(self.c,self.t,self.tr)
        self.assertEqual(self.b.db.execute('SELECT phase FROM runs').fetchone()['phase'],'FINISHED')
        self.assertEqual(await self.b.tick(),[]);self.assertTrue(read(p)['safe_to_rework'])

if __name__=='__main__':unittest.main(verbosity=2)
