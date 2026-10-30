"""Shared data validation. Files in the agent workspace remain untrusted."""
import hashlib, json, os, re, stat, tempfile, sys
from pathlib import Path
from urllib.parse import urlsplit

MAX_JSON = 1024 * 1024
class Blocked(ValueError): pass

def need(ok, message):
    if not ok: raise Blocked(message)

def read_bytes(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        need(stat.S_ISREG(os.fstat(f.fileno()).st_mode), 'Expected a regular file')
        raw = f.read(MAX_JSON + 1)
    need(len(raw) <= MAX_JSON, 'JSON exceeds 1 MiB')
    return raw

def digest(raw): return hashlib.sha256(raw).hexdigest()
def read(path): return json.loads(read_bytes(path))

def atomic(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
    fd, tmp = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def publish_once(path, raw):
    """Publish complete bytes without overwriting an existing experiment."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.publish-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(raw);f.flush();os.fsync(f.fileno())
        try:os.link(tmp,path)
        except FileExistsError:need(read_bytes(path)==raw,'Experiment ID already has different bytes')
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def load_config(path):
    c = read(path)
    need(c.get('schema_version') == 1, 'Unsupported config schema')
    need(c.get('provider') in ('github', 'gitlab'), 'Bridge supports GitHub/GitLab Issues')
    need(isinstance(c.get('project'), str) and re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+', c['project']), 'Invalid project path')
    u=urlsplit(c.get('api_url',''))
    need(u.scheme=='https' and bool(u.hostname) and not u.username and not u.password and not u.query and not u.fragment, 'Tracker API must use HTTPS without embedded credentials')
    enabled=c.get('enabled_task_types',['training-optimization'])
    need(isinstance(enabled,list) and bool(enabled) and all(isinstance(x,str) for x in enabled) and len(enabled)==len(set(enabled)), 'Invalid task type allowlist')
    supported={'training-optimization'}
    if set(enabled)-supported:
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'platform'))
        from dev_platform.registry import registered_types
        supported.update(registered_types())
    need(set(enabled)<=supported,'Unknown task type; register it in the trusted platform first')
    c['enabled_task_types']=enabled
    state_files=[]
    if 'training-optimization' in enabled:state_files.append('baseline_file')
    if set(enabled)-{'training-optimization'}:state_files.append('repository_state_file')
    for k in ('workspace_root','outbox','receipts','approvals','state_dir',*state_files):
        need(Path(c.get(k,'')).is_absolute(), f'{k} must be absolute')
    roots=[Path(c[k]).resolve() for k in ('workspace_root','outbox','receipts','approvals','state_dir')]
    for i,p in enumerate(roots):
        for q in roots[i+1:]:need(not p.is_relative_to(q) and not q.is_relative_to(p), 'Workspace, outbox, receipts and private state must be separate directories')
    for key in state_files:
        for p in roots[:3]:need(not Path(c[key]).resolve().is_relative_to(p),key+' must be outside agent-writable/shared data roots')
    if 'shared_ingress_db' in c:
        shared=Path(c['shared_ingress_db'])
        need(shared.is_absolute() and '..' not in shared.parts,'shared_ingress_db must be an absolute canonical path')
        need(not any(p.is_symlink() for p in (shared,*shared.parents)),'shared_ingress_db cannot contain symlinks')
        for p in roots[:3]:need(not shared.resolve().is_relative_to(p),'shared_ingress_db must be outside agent-writable/shared data roots')
    need(1 <= c.get('max_concurrent_agents', 3) <= 20, 'Invalid coding concurrency')
    need(isinstance(c.get('token_env'),str) and re.fullmatch(r'[A-Z][A-Z0-9_]+',c['token_env']), 'Invalid token env name')
    need(c.get('ready_label')=='agent-ready', 'Reserved ready label must be agent-ready')
    return c

def validate_request(c, raw):
    r=json.loads(raw)
    need(isinstance(r,dict),'Request must be an object')
    if r.get('schema_version')==2:
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'platform'))
        from dev_platform.contracts import validate_task
        try:validate_task(r)
        except (ValueError,TypeError,KeyError) as e:raise Blocked(str(e)) from e
        need(r['task_type'] in c.get('enabled_task_types',[]),'Task type is not enabled for this project')
        t=r['tracker']
        need(t['kind']==c['provider'] and t['project']==c['project'],'Request tracker scope mismatch')
        return r
    need(r.get('schema_version')==1, 'Unsupported request schema')
    need('training-optimization' in c.get('enabled_task_types',['training-optimization']),'Training task type is disabled')
    t=r.get('tracker',{})
    need(t.get('kind')==c['provider'] and t.get('project')==c['project'], 'Request tracker scope mismatch')
    need(isinstance(t.get('issue_id'),str) and re.fullmatch(r'[1-9][0-9]*',t['issue_id']), 'issue_id must be GitHub number / GitLab IID')
    e=r.get('experiment',{});b=e.get('binding',{})
    eid=b.get('experiment_id')
    need(isinstance(eid,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',eid), 'Invalid experiment ID')
    for k in ('candidate_sha','baseline_sha'):
        need(isinstance(b.get(k),str) and re.fullmatch(r'(?:[a-f0-9]{40}|[a-f0-9]{64})',b[k]), 'Full commit required: '+k)
    need(isinstance(b.get('manifest_sha'),str) and re.fullmatch(r'[a-f0-9]{64}',b['manifest_sha']), 'manifest SHA256 required')
    u=urlsplit(e.get('manifest_uri',''))
    need(u.scheme in ('https','s3','gs') and bool(u.netloc) and not u.username and not u.password and not u.query and not u.fragment, 'Use an immutable credential-free manifest URI')
    need(set(e)=={'binding','manifest_uri','poll_seconds','max_run_seconds','release_wait_seconds','cancel_wait_seconds'}, 'Explicit Experiment fields required')
    need(set(b)=={'experiment_id','manifest_sha','candidate_sha','baseline_sha'}, 'Unexpected binding fields')
    for k,lo,hi in [('poll_seconds',30,300),('max_run_seconds',60,86400),('release_wait_seconds',60,604800),('cancel_wait_seconds',30,3600)]:
        need(type(e.get(k)) is int and lo<=e[k]<=hi,'Invalid '+k)
    need(isinstance(r.get('baseline_id'),str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',r['baseline_id']), 'baseline_id required')
    return r

def expected_workspace(c, r):
    prefix='GH-' if c['provider']=='github' else 'GL-'
    return Path(c['workspace_root']).resolve() / (prefix+r['tracker']['issue_id'])

def current_baseline(c):
    b=read(c['baseline_file'])
    for k in ('baseline_id','commit','config_sha256','workload_fingerprint'):need(k in b,'Incomplete baseline: '+k)
    return {k:b[k] for k in ('baseline_id','commit','config_sha256','workload_fingerprint')}

def request_id(r):
    return r['task_id'] if r['schema_version']==2 else r['experiment']['binding']['experiment_id']

def request_starting_sha(r):
    return r['repository']['starting_sha'] if r['schema_version']==2 else r['experiment']['binding']['candidate_sha']

def request_spec(r):
    if r['schema_version']==1:return r['experiment']
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'platform'))
    from dev_platform.contracts import make_spec
    return make_spec(r)

def request_workflow_id(r):
    return ('dev-task/' if r['schema_version']==2 else 'perf-experiment/')+request_id(r)

def admission_state(c,r):
    """Trusted project snapshot; development has no training-baseline dependency."""
    if r['schema_version']==1:
        b=current_baseline(c)
        need(r['baseline_id']==b['baseline_id'] and r['experiment']['binding']['baseline_sha']==b['commit'],'Stale baseline')
        return b
    state=read(c['repository_state_file'])
    need(set(state)=={'project','base_sha','policy_revision'},'Invalid trusted repository state')
    need(state['project']==c['project'] and state['base_sha']==r['repository']['base_sha'],'Repository base changed; replan a new revision')
    need(isinstance(state['policy_revision'],str) and state['policy_revision'].strip(),'Repository policy revision is required')
    # Verify the installed policy is still the exact admitted version.
    spec=request_spec(r)
    return {'repository':state,'profile_sha256':spec['profile_sha256'],'task_type':r['task_type']}
