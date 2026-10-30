"""Fetch the reviewed Linux x86_64 executable; reject a changed rolling nightly."""
import argparse,hashlib,json,os,platform,tempfile,urllib.request
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','amd64'):p.exit(2,'Use the pinned-source build in README for this platform.\n')
    lock=json.loads(Path(__file__).with_name('upstream.lock.json').read_text());out=Path(a.output)
    if out.exists():p.exit(2,'Refuse to replace an existing runtime.\n')
    out.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=out.parent)
    try:
        with os.fdopen(fd,'wb') as f, urllib.request.urlopen(lock['binary_url'],timeout=60) as r:
            h=hashlib.sha256();total=0
            while chunk:=r.read(1024*1024):
                total+=len(chunk)
                if total>100*1024*1024:raise ValueError('Unexpected binary size')
                h.update(chunk);f.write(chunk)
            f.flush();os.fsync(f.fileno())
        if h.hexdigest()!=lock['binary_sha256']:raise ValueError('Upstream nightly changed. Use the pinned commit build; do not bypass the checksum.')
        os.chmod(tmp,0o755);os.replace(tmp,out);print(out)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
if __name__=='__main__':main()
