"""Single-host persistent handoff bridge. Deploy separately from Symphony/Codex."""
import argparse, asyncio, contextlib, fcntl, json, os, sqlite3, time
from pathlib import Path
from common import load_config, read_bytes, read, atomic, digest, validate_request, admission_state, request_id, request_spec, request_workflow_id, need, Blocked
from tracker import Tracker

@contextlib.contextmanager
def locked(c):
    p=Path(c['state_dir']);p.mkdir(parents=True,exist_ok=True)
    with (p/'bridge.lock').open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX);yield

def admit(c,path,receipt,expires):
    need(bool(receipt.strip()),'An existing CI/operator authorization receipt is required')
    need(time.time()<expires<=time.time()+604800,'Admission expires within 7 days')
    raw=read_bytes(path);r=validate_request(c,raw);b=admission_state(c,r)
    grant={'request_sha256':digest(raw),'baseline':b,'authorization_receipt':receipt,'expires_at':expires}
    eid=request_id(r);p=Path(c['approvals'])/(eid+'.json')
    need(not p.exists(),'Admission is immutable; use a new experiment revision')
    atomic(p,grant);return str(p)

class Bridge:
    def __init__(self,c,transport,tracker):
        self.c,self.transport,self.tracker=c,transport,tracker
        state=Path(c['state_dir']);state.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(state/'bridge.sqlite');self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, issue TEXT, sha TEXT, request TEXT, phase TEXT, run_id TEXT, detail TEXT)')
        # Keep the admitted policy snapshot for recovery after installed profiles evolve.
        if 'spec' not in {r[1] for r in self.db.execute('PRAGMA table_info(runs)')}:
            self.db.execute('ALTER TABLE runs ADD COLUMN spec TEXT')
        if 'lease_owner' not in {r[1] for r in self.db.execute('PRAGMA table_info(runs)')}:
            self.db.execute('ALTER TABLE runs ADD COLUMN lease_owner TEXT')
        self.db.execute('CREATE TABLE IF NOT EXISTS issue_heads (issue TEXT PRIMARY KEY, experiment TEXT)')
        self.db.commit()
        # Upgrade current legacy heads whose receipts predate explicit cleanup safety.
        # Re-deliver saved results; never infer that an unknown external job stopped.
        for row in self.db.execute("SELECT r.* FROM runs r JOIN issue_heads h ON h.experiment=r.id WHERE r.phase='DELIVERED'").fetchall():
            try:receipt=read(Path(c['receipts'])/(row['id']+'.json'))
            except (OSError,ValueError):receipt={}
            if 'safe_to_rework' not in receipt:
                try:result=json.loads(row['detail'])
                except (ValueError,TypeError):result={}
                phase='FINISHED' if result.get('terminal') is True and isinstance(result.get('phase'),str) else 'BLOCKED_UNRESOLVED'
                self.update(row['id'],phase=phase)
        self.leases=None
        self.lease_owner='symphony:'+digest(str(state.resolve()).encode())[:32]
        if c.get('shared_ingress_db'):
            # An old active ledger must be drained/reconciled before enabling a
            # second entrance. Never fabricate claims for already-running work.
            unclaimed=self.db.execute("SELECT id FROM runs WHERE phase!='DELIVERED' AND lease_owner IS NULL LIMIT 1").fetchone()
            if unclaimed:
                self.db.close()
                raise Blocked('Drain/reconcile existing tasks before enabling shared ingress ownership')
            import sys
            sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'platform'))
            from dev_platform.ingress import IngressLeases
            self.leases=IngressLeases(c['shared_ingress_db'])
        elif self.db.execute("SELECT id FROM runs WHERE phase!='DELIVERED' AND lease_owner IS NOT NULL LIMIT 1").fetchone():
            self.db.close()
            raise Blocked('Shared ingress ownership cannot be disabled while tasks are unresolved')
    def close(self):
        self.db.close()
        if self.leases:self.leases.close()
    def update(self,eid,**fields):
        self.db.execute('UPDATE runs SET '+','.join(k+'=?' for k in fields)+' WHERE id=?',list(fields.values())+[eid]);self.db.commit()
    def ingest(self,path):
        raw=read_bytes(path);r=validate_request(self.c,raw);eid=request_id(r)
        need(Path(path).name==eid+'.json','Filename must equal experiment ID')
        prior=self.db.execute('SELECT * FROM runs WHERE id=?',(eid,)).fetchone()
        if prior:
            need(prior['sha']==digest(raw),'Immutable handoff was changed');return
        grant=read(Path(self.c['approvals'])/(eid+'.json'))
        need(grant.get('request_sha256')==digest(raw),'Request is not the admitted bytes')
        need(grant.get('expires_at',0)>time.time(),'Admission expired')
        b=admission_state(self.c,r)
        need(grant.get('baseline')==b,'Repository/baseline policy changed after admission')
        issue=r['tracker']['issue_id'];head=self.db.execute('SELECT experiment FROM issue_heads WHERE issue=?',(issue,)).fetchone()
        if head:
            phase=self.db.execute('SELECT phase FROM runs WHERE id=?',(head['experiment'],)).fetchone()['phase']
            need(phase=='DELIVERED','Another unresolved experiment owns this issue')
        self.tracker.assert_startable(issue)
        spec=request_spec(r)
        if self.leases:
            from dev_platform.contracts import canonical_sha
            self.leases.acquire(r['tracker'],self.lease_owner,eid,canonical_sha(spec))
        with self.db:
            self.db.execute('INSERT INTO runs (id,issue,sha,request,phase,run_id,detail,spec,lease_owner) VALUES (?,?,?,?,?,?,?,?,?)',(eid,issue,digest(raw),raw.decode(), 'NEW',None,'',json.dumps(spec),self.lease_owner if self.leases else None))
            self.db.execute('INSERT INTO issue_heads VALUES (?,?) ON CONFLICT(issue) DO UPDATE SET experiment=excluded.experiment',(issue,eid))
    def release_ownership(self,row):
        if not self.leases or not row['lease_owner']:return
        from dev_platform.contracts import canonical_sha
        need(row['phase']=='DELIVERED','Only durably delivered safe outcomes can release shared ownership')
        r=json.loads(row['request']);spec=json.loads(row['spec'])
        receipt=read(Path(self.c['receipts'])/(row['id']+'.json'))
        need(receipt.get('safe_to_rework') is True and receipt.get('request_sha256')==row['sha'],
             'Exact safe receipt required before releasing shared ownership')
        evidence=canonical_sha({'run_id':row['run_id'],'result':json.loads(row['detail']),
                                'cleanup':receipt.get('reconciliation_sha256')})
        self.leases.release(r['tracker'],row['lease_owner'],row['id'],canonical_sha(spec),evidence)
    def receipt(self,row,value):
        r=json.loads(row['request']);key='task_id' if r['schema_version']==2 else 'experiment_id'
        atomic(Path(self.c['receipts'])/(row['id']+'.json'),{**value,key:row['id'],'issue_id':row['issue'],'request_sha256':row['sha'],'workflow_id':request_workflow_id(r)})
    async def advance(self,row):
        from temporal_transport import NotFound
        eid=row['id'];r=json.loads(row['request']);spec=json.loads(row['spec']) if row['spec'] else request_spec(r);phase=row['phase']
        if self.leases and row['lease_owner']:
            from dev_platform.contracts import canonical_sha
            self.leases.assert_held(r['tracker'],row['lease_owner'],eid,canonical_sha(spec))
        if phase=='NEW':
            # Re-check authorization immediately before the sole first start attempt.
            grant=read(Path(self.c['approvals'])/(eid+'.json'))
            need(grant.get('request_sha256')==row['sha'] and grant.get('expires_at',0)>time.time(),'Admission expired or changed before start')
            need(grant.get('baseline')==admission_state(self.c,r),'Repository/baseline policy changed before start')
            self.tracker.assert_startable(row['issue'])
            self.update(eid,phase='SUBMITTING')  # durable BEFORE network side effect
            try:run_id=await self.transport.start(spec)
            except Exception as e:
                self.update(eid,phase='RECONCILING',detail=type(e).__name__);raise
            self.update(eid,phase='RUNNING',run_id=run_id,detail='')
            phase='RUNNING';row=self.db.execute('SELECT * FROM runs WHERE id=?',(eid,)).fetchone()
        elif phase in ('SUBMITTING','RECONCILING'):
            try:_,desc=await self.transport.lookup(spec)
            except NotFound:
                # No automatic restart after ambiguous submission or history expiry.
                self.receipt(row,{'phase':'RECONCILING','detail':'Workflow not found after a recorded submission intent; operator must inspect Temporal and runner ledger.'});return
            self.update(eid,phase='RUNNING',run_id=desc.run_id,detail='')
            phase='RUNNING';row=self.db.execute('SELECT * FROM runs WHERE id=?',(eid,)).fetchone()
        if phase=='RUNNING':
            self.tracker.transition(row['issue'],'agent-ready','agent-waiting')
            result=await self.transport.poll(spec,row['run_id'])
            self.receipt(row,result)
            if result['terminal']:
                self.update(eid,phase='FINISHED',detail=json.dumps(result));phase='FINISHED'
                row=self.db.execute('SELECT * FROM runs WHERE id=?',(eid,)).fetchone()
        if phase=='FINISHED':
            result=json.loads(row['detail'])
            success='REVIEW_READY' if r['schema_version']==2 else 'INTEGRATION_TASK_CREATED'
            target='agent-review' if result['phase']==success else 'agent-blocked'
            head=self.db.execute('SELECT experiment FROM issue_heads WHERE issue=?',(row['issue'],)).fetchone()
            need(head and head['experiment']==eid,'Stale result cannot change current issue')
            # AWAITING_RELEASE is still RUNNING: never treat gate PASS as final approval.
            status=self.tracker.transition(row['issue'],'agent-waiting',target)
            if r['schema_version']==2:
                safe=result['phase']=='REVIEW_READY' or (result['phase']=='BLOCKED' and result.get('outcome',{}).get('fence',{}).get('confirmed') is True)
            else:safe=result['phase'] in {'INTEGRATION_TASK_CREATED','GATE_FAILED','RELEASE_EXPIRED','FAILED','CANCELLED'}
            self.receipt(row,{**result,'tracker_sync':status,'target_label':target,'safe_to_rework':safe})
            self.update(eid,phase='DELIVERED' if safe else 'BLOCKED_UNRESOLVED')
            if safe:self.release_ownership(self.db.execute('SELECT * FROM runs WHERE id=?',(eid,)).fetchone())
    async def tick(self):
        errors=[]
        # Recover a crash after safe terminal commit but before shared release.
        if self.leases:
            for row in self.db.execute("SELECT * FROM runs WHERE phase='DELIVERED' AND lease_owner IS NOT NULL").fetchall():
                try:self.release_ownership(row)
                except Exception as e:errors.append({'experiment_id':row['id'],'error':type(e).__name__,'detail':str(e)[:300]})
        for p in sorted(Path(self.c['outbox']).glob('*.json')):
            try:self.ingest(p)
            except Exception as e:errors.append({'file':p.name,'error':type(e).__name__,'detail':str(e)[:300]})
        for row in self.db.execute("SELECT * FROM runs WHERE phase NOT IN ('DELIVERED','BLOCKED_UNRESOLVED') ORDER BY id").fetchall():
            try:await self.advance(row)
            except Exception as e:
                errors.append({'experiment_id':row['id'],'error':type(e).__name__,'detail':str(e)[:300]})
                current=self.db.execute('SELECT phase FROM runs WHERE id=?',(row['id'],)).fetchone()
                if current['phase']!='DELIVERED':
                    self.receipt(row,{'phase':'RECONCILING','detail':type(e).__name__+'; inspect bridge/Temporal/runner logs'})
        return errors

def status(c):
    path=Path(c['state_dir'])/'bridge.sqlite'
    if not path.exists():return []
    db=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:return [dict(r) for r in db.execute('SELECT id,issue,phase,run_id FROM runs ORDER BY id')]
    finally:db.close()

def reconcile(c,eid,evidence_path):
    """Trusted operator attestation AFTER actual external cleanup; never cancels a job."""
    from urllib.parse import urlsplit
    b=Bridge(c,None,None)
    try:
        row=b.db.execute('SELECT * FROM runs WHERE id=?',(eid,)).fetchone()
        need(row is not None and row['phase']=='BLOCKED_UNRESOLVED','Only an unresolved terminal task can be reconciled')
        raw=read_bytes(evidence_path);e=json.loads(raw);r=json.loads(row['request'])
        expected={'schema_version':1,'task_id':eid,'issue_id':row['issue'],'request_sha256':row['sha'],
                  'workflow_id':request_workflow_id(r),'run_id':row['run_id'],'all_external_work_stopped':True}
        need(all(e.get(k)==v for k,v in expected.items()),'Reconciliation receipt binding differs')
        need(e.get('all_external_work_stopped') is True,'Explicit stop confirmation is required')
        need(isinstance(e.get('operator'),str) and bool(e['operator'].strip()),'Operator identity is required')
        need(isinstance(e.get('evidence_sha256'),str) and len(e['evidence_sha256'])==64 and all(x in '0123456789abcdef' for x in e['evidence_sha256']),'Evidence SHA256 required')
        u=urlsplit(e.get('evidence_uri',''));need(u.scheme=='https' and bool(u.hostname) and not u.username and not u.password and not u.query and not u.fragment,'Use credential-free HTTPS cleanup evidence')
        need(type(e.get('confirmed_at')) in (int,float) and time.time()-86400<=e['confirmed_at']<=time.time()+30,'Cleanup confirmation must be current')
        from common import publish_once
        publish_once(Path(c['state_dir'])/'reconciliations'/(eid+'.json'),raw)
        try:old=read(Path(c['receipts'])/(eid+'.json'))
        except (OSError,ValueError):
            old={'terminal':True,'phase':'RECONCILED','run_id':row['run_id'],'tracker_sync':'OPERATOR_RECONCILED'}
        b.receipt(row,{**old,'safe_to_rework':True,'reconciliation_sha256':digest(raw)})
        b.update(eid,phase='DELIVERED')
        b.release_ownership(b.db.execute('SELECT * FROM runs WHERE id=?',(eid,)).fetchone())
        return 'RECONCILED: task ownership released; no merge or deployment performed'
    finally:b.close()

async def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True)
    sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('admit');a.add_argument('request');a.add_argument('--authorization-receipt',required=True);a.add_argument('--valid-hours',type=int,default=24)
    a=sub.add_parser('reconcile');a.add_argument('task_id');a.add_argument('evidence')
    sub.add_parser('once');sub.add_parser('run');sub.add_parser('status');args=p.parse_args();c=load_config(args.config)
    if args.action=='status':print(json.dumps(status(c),indent=2));return
    if args.action=='admit':
        with locked(c):print(admit(c,args.request,args.authorization_receipt,time.time()+args.valid_hours*3600))
        return
    if args.action=='reconcile':
        with locked(c):print(reconcile(c,args.task_id,args.evidence))
        return
    from perf_temporal.connection import connect,task_queue
    from task_transport import TaskTransport
    transport=TaskTransport(await connect(),task_queue(),os.getenv('DEV_TASK_QUEUE','development-tasks'))
    while True:
        with locked(c):
            bridge=Bridge(c,transport,Tracker(c))
            try:errors=await bridge.tick()
            finally:bridge.close()
        print(json.dumps({'errors':errors},ensure_ascii=False),flush=True)
        if args.action=='once':return
        await asyncio.sleep(15)

if __name__=='__main__':
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'temporal'))
    try:asyncio.run(main())
    except (ValueError,OSError) as e:raise SystemExit('BLOCKED: '+str(e))
