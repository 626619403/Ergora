"""Render a native Symphony WORKFLOW.md; configuration stays outside candidate repos."""
import argparse, json, shlex
from pathlib import Path
from common import load_config, need
ROOT=Path(__file__).resolve().parent

def render(path):
    c=load_config(path)
    provider={'api_url':c['api_url']}
    if c['provider']=='gitlab':provider.update(project_path=c['project'],api_key='$'+c['token_env'])
    else:provider.update(repo=c['project'],token='$'+c['token_env'])
    hook=lambda action:'python3 '+shlex.quote(str(ROOT/'workspace.py'))+' '+action+' --config '+shlex.quote(str(Path(path).resolve()))
    conf={
        'tracker':{'kind':c['provider'],'provider':provider,'required_labels':['agent-ready'],
                   'active_states':['opened' if c['provider']=='gitlab' else 'open'],'terminal_states':['closed']},
        'workspace':{'root':c['workspace_root']},'polling':{'interval_ms':15000},
        'hooks':{'after_create':hook('bootstrap'),'before_run':hook('prepare'),'after_run':hook('enqueue'),'timeout_ms':240000},
        'agent':{'max_concurrent_agents':c['max_concurrent_agents'],'max_turns':8},
        'codex':{'command':'python3 '+shlex.quote(str(ROOT/'codex_launcher.py'))+' --config '+shlex.quote(str(Path(path).resolve())),
                 'approval_policy':{'reject':{'sandbox_approval':True,'rules':True,'mcp_elicitations':True}},
                 'thread_sandbox':'workspace-write','turn_sandbox_policy':{'type':'workspaceWrite','networkAccess':True}},
        'server':{'host':'127.0.0.1','port':c.get('dashboard_port',4000)}}
    prompt=(ROOT/'PROMPT.md').read_text().replace('@TRACKER@',c['provider']).replace('@PROJECT@',c['project']).replace('@KIT_ROOT@',str(ROOT.parent)).replace('@TASK_TYPES@',', '.join(c['enabled_task_types']))
    return '---\n'+json.dumps(conf,ensure_ascii=False,indent=2)+'\n---\n\n'+prompt

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);need(not out.exists(),'Refuse to overwrite workflow; use a new output path')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(render(a.config));print(out)
if __name__=='__main__':main()
