"""Trusted host hooks. Never execute scripts from the candidate repository."""
import argparse, os, subprocess
from pathlib import Path
from common import load_config, read_bytes, validate_request, expected_workspace, atomic, publish_once, digest, read, need, Blocked, request_id, request_starting_sha

def enqueue(c, workspace):
    workspace=Path(workspace).resolve()
    need(workspace.parent==Path(c['workspace_root']).resolve(), 'Wrong workspace root')
    src=workspace/'.symphony'/'handoff.json'
    if not src.exists():return 'NO_REQUEST'
    need(src.parent.resolve().is_relative_to(workspace), 'Request directory escapes workspace')
    raw=read_bytes(src);r=validate_request(c,raw)
    need(workspace==expected_workspace(c,r),'Workspace does not match issue identity')
    # Candidate changes must already be committed. Remote availability is checked by the trusted runner.
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=workspace,text=True).strip()
    need(sha==request_starting_sha(r),'Candidate HEAD differs from request')
    dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=normal'],cwd=workspace,text=True)
    need(not dirty.strip(),'Candidate changes or new files are not committed')
    out=Path(c['outbox'])/(request_id(r)+'.json')
    publish_once(out,raw)
    return 'QUEUED_FOR_ADMISSION'

def prepare(c, workspace):
    workspace=Path(workspace).resolve()
    need(workspace.parent==Path(c['workspace_root']).resolve(),'Wrong workspace root')
    # after_run is best effort upstream. This second path recovers a pending handoff.
    if (workspace/'.symphony/handoff.json').exists():
        src=workspace/'.symphony/handoff.json'
        need(src.parent.resolve().is_relative_to(workspace),'Request directory escapes workspace')
        raw=read_bytes(src);r=validate_request(c,raw)
        need(workspace==expected_workspace(c,r),'Workspace does not match issue identity')
        eid=request_id(r);receipt=Path(c['receipts'])/(eid+'.json')
        if receipt.exists():
            done=read(receipt)
            if done.get('terminal') is True and done.get('safe_to_rework') is True and done.get('tracker_sync') in ('UPDATED','ALREADY','CLOSED_UNCHANGED','DIVERGED_UNCHANGED','OPERATOR_RECONCILED'):
                key='task_id' if r['schema_version']==2 else 'experiment_id'
                need(done.get(key)==eid and done.get('issue_id')==r['tracker']['issue_id'] and done.get('request_sha256')==digest(raw),'Receipt binding differs')
                history=workspace/'.symphony/history'
                need(history.resolve().is_relative_to(workspace),'History escapes workspace')
                publish_once(history/(eid+'.json'),raw);src.unlink()
                return 'READY_FOR_EXPLICIT_REWORK'
        result=enqueue(c,workspace)
        raise Blocked('Pending immutable handoff: '+result+'; bridge/operator must park or resolve this issue')
    return 'READY'

def bootstrap(c, workspace):
    workspace=Path(workspace).resolve()
    need(workspace.parent==Path(c['workspace_root']).resolve(),'Wrong workspace root')
    if not (workspace/'.git').exists():
        need(not any(workspace.iterdir()),'Refuse clone into nonempty workspace')
        repo=c.get('repo_url','')
        need(repo.startswith(('https://','ssh://','git@')) and not any(x.isspace() for x in repo),'Invalid repository URL')
        subprocess.run(['git','clone','--no-hardlinks','--',repo,'.'],cwd=workspace,check=True,timeout=180)
    (workspace/'.symphony').mkdir(exist_ok=True)
    exclude=workspace/'.git/info/exclude'
    if exclude.is_file() and '\n/.symphony/\n' not in exclude.read_text():
        with exclude.open('a') as f:f.write('\n/.symphony/\n')
    return 'BOOTSTRAPPED'

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['bootstrap','prepare','enqueue']);p.add_argument('--config',required=True);a=p.parse_args()
    try: print(globals()[a.action](load_config(a.config),Path.cwd()))
    except (ValueError,OSError,subprocess.SubprocessError) as e:p.exit(2,'BLOCKED: '+str(e)+'\n')
if __name__=='__main__':main()
