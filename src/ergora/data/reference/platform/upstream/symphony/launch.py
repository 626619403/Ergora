import argparse,os
from pathlib import Path
from common import load_config,need

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--workflow',required=True);p.add_argument('--logs-root',required=True);a=p.parse_args();c=load_config(a.config)
    need(bool(os.environ.get(c['token_env'])),'Tracker token is missing')
    for key in ('symphony_bin','codex_bin'):need(os.access(c[key],os.X_OK),key+' is not executable')
    need(not any(k.startswith('TEMPORAL_') for k in os.environ),'Do not give Temporal credentials/config to the Symphony host')
    # Upstream requires this explicit switch. Use isolated, scoped service identities.
    os.execv(c['symphony_bin'],[c['symphony_bin'],str(Path(a.workflow).resolve()),'--logs-root',str(Path(a.logs_root).resolve()),
                              '--i-understand-that-this-will-be-running-without-the-usual-guardrails'])
if __name__=='__main__':main()
