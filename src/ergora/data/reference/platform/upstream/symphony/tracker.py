"""Only changes workflow labels; never closes issues, posts comments or merges code."""
import json, os, urllib.request, urllib.error
from urllib.parse import quote
from common import need

class Tracker:
    def __init__(self,c):self.c=c
    def request(self,method,path,body=None):
        token=os.environ.get(self.c['token_env'],'');need(bool(token),'Missing tracker token')
        headers={'Accept':'application/vnd.github+json' if self.c['provider']=='github' else 'application/json','Content-Type':'application/json'}
        if self.c['provider']=='gitlab':headers['PRIVATE-TOKEN']=token
        else:headers.update({'Authorization':'Bearer '+token,'X-GitHub-Api-Version':self.c.get('github_api_version','2026-03-10')})
        req=urllib.request.Request(self.c['api_url'].rstrip('/')+path,headers=headers,method=method,data=None if body is None else json.dumps(body).encode())
        # Reject redirects so credentials never move to another origin.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        try:
            with urllib.request.build_opener(NoRedirect).open(req,timeout=20) as response:
                raw=response.read(1024*1024+1);need(len(raw)<=1024*1024,'Tracker response too large')
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code==404 and method=='DELETE':return None
            raise RuntimeError(f'Tracker {method} failed with HTTP {e.code}') from None
    def path(self,issue):
        project=self.c['project']
        if self.c['provider']=='gitlab':return '/projects/'+quote(project,safe='')+'/issues/'+issue
        return '/repos/'+project+'/issues/'+issue
    def get(self,issue):
        d=self.request('GET',self.path(issue))
        need(isinstance(d,dict),'Bad tracker payload')
        if self.c['provider']=='github':need('pull_request' not in d,'Pull requests are not experiment issues')
        labels={x if isinstance(x,str) else x['name'] for x in d.get('labels',[])}
        return d.get('state'),labels
    def assert_startable(self,issue):
        state,labels=self.get(issue)
        need(state in ('open','opened') and 'agent-ready' in labels,'Issue is closed or no longer agent-ready')
    def transition(self,issue,source,target):
        state,labels=self.get(issue)
        if state not in ('open','opened'):return 'CLOSED_UNCHANGED'
        if source not in labels:
            return 'ALREADY' if target in labels else 'DIVERGED_UNCHANGED'
        path=self.path(issue)
        if self.c['provider']=='gitlab':
            self.request('PUT',path,{'add_labels':target,'remove_labels':source})
        else:
            # Add target first. If removal fails, next poll repeats these idempotent operations.
            self.request('POST',path+'/labels',{'labels':[target]})
            self.request('DELETE',path+'/labels/'+quote(source,safe=''))
        return 'UPDATED'
