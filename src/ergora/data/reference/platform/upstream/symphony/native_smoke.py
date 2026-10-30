"""Start the actual Symphony executable with no issues; no Codex/model/tracker requests."""
import argparse,json,os,socket,subprocess,tempfile,time,urllib.request
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--workflow');a=p.parse_args()
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp)
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  config={'tracker':{'kind':'memory','active_states':['Todo'],'terminal_states':['Done']},'workspace':{'root':str(root/'workspaces')},'server':{'host':'127.0.0.1','port':port},'agent':{'max_concurrent_agents':3}}
  if a.workflow:
   generated=json.loads(Path(a.workflow).read_text().split('---')[1]);generated.update(tracker=config['tracker'],workspace=config['workspace'],server=config['server']);config=generated
  path=root/'WORKFLOW.md';path.write_text('---\n'+json.dumps(config)+'\n---\nNo issues. Native smoke only.\n')
  with (root/'stdout.log').open('wb') as log:
   child=subprocess.Popen([str(Path(a.binary).resolve()),str(path),'--logs-root',str(root/'logs'),'--i-understand-that-this-will-be-running-without-the-usual-guardrails'],stdout=log,stderr=log)
   try:
    last=''
    for _ in range(100):
     if child.poll() is not None:raise RuntimeError((root/'stdout.log').read_text()[-2000:])
     try:
      with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/v1/state',timeout=1) as r:state=json.load(r)
      print(json.dumps({'status':'PASS','native_binary':str(Path(a.binary).resolve()),'state':state},ensure_ascii=False));return
     except Exception as e:last=str(e);time.sleep(.1)
    raise RuntimeError('Native dashboard not reachable: '+last)
   finally:
    child.terminate()
    try:child.wait(timeout=10)
    except subprocess.TimeoutExpired:child.kill();child.wait()
if __name__=='__main__':main()
