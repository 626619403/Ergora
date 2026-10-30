"""Compile an admitted-shape task; no network, workflow start, or approval side effects."""
import argparse,json
from pathlib import Path
from .adapter import read_json,publish
from .contracts import make_spec
from .registry import TASK_ROOT,load_profile,profile_digest

def main():
    p=argparse.ArgumentParser(description='Trusted task registry and request compiler')
    sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('types')
    f=sub.add_parser('fingerprint');f.add_argument('task_type');f.add_argument('--version',type=int,default=1)
    c=sub.add_parser('compile');c.add_argument('request');c.add_argument('--out',required=True)
    a=p.parse_args()
    if a.action=='types':
        registry=read_json(TASK_ROOT/'registry.json');out=[]
        for name,versions in sorted(registry['types'].items()):
            for version in sorted(versions,key=int):
                profile=load_profile(name,int(version))
                out.append({'task_type':name,'version':int(version),'title':profile['title'],'profile_sha256':profile_digest(profile)})
        print(json.dumps(out,ensure_ascii=False,indent=2))
    elif a.action=='fingerprint':print(profile_digest(load_profile(a.task_type,a.version)))
    else:
        spec=make_spec(read_json(Path(a.request)));publish(Path(a.out),spec)
        print(json.dumps({'spec':str(Path(a.out).resolve()),'task_id':spec['request']['task_id'],'request_sha256':spec['request_sha256'],'status':'VALIDATED_ONLY'},ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError) as error:raise SystemExit('BLOCKED: '+str(error))
