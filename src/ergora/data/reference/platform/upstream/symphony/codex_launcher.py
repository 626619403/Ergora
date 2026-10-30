"""Drop control-plane secrets before starting Codex. Process isolation remains required."""
import argparse,os
from pathlib import Path
from common import load_config,need

def child_env(source):
    allowed={'PATH','HOME','USER','LOGNAME','LANG','LC_ALL','TERM','TMPDIR','CODEX_HOME','OPENAI_API_KEY','OPENAI_BASE_URL',
             'HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy'}
    return {k:v for k,v in source.items() if k in allowed}

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();c=load_config(a.config)
    binary=c['codex_bin'];need(Path(binary).is_absolute() and os.access(binary,os.X_OK),'codex_bin is not executable')
    os.execve(binary,[binary,'app-server'],child_env(os.environ))
if __name__=='__main__':main()
