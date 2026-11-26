#!/usr/bin/env python3
"""Small, offline evidence registry. It does not schedule GPUs or approve code."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

class Invalid(ValueError): pass
class PrimaryArchiveDurabilityError(Invalid): pass


ARCHIVE_DURABILITY_EXIT = 3
ARCHIVE_EVALUATED_NEGATIVE_EXIT = 4


class EvaluatedNegativeGate(Invalid):
    def __init__(self, report):
        super().__init__('Performance evidence is ' + report['performance']['status'])
        self.report = {**report, 'status': 'EVALUATED_NEGATIVE_GATE'}

def fail(message): raise Invalid(message)
def read(path):
    try: return json.loads(Path(path).read_text())
    except (OSError, ValueError) as e: fail(f'Cannot read JSON {path}: {e}')
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(condition, message):
    if not condition: fail(message)
def sha(value, field):
    require(isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value), f'{field}: expected SHA256')
def commit(value,field):
    require(isinstance(value,str) and re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}',value),f'{field}: expected full Git commit ID')
def ident(value):
    require(isinstance(value,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}',value),'Invalid ID')
    return value
def write_raw(path, raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.write-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def write(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.write-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
@contextlib.contextmanager
def lock(root):
    # One coordinator host with local disk. Not a cross-cluster GPU lock.
    import fcntl
    root.mkdir(parents=True,exist_ok=True)
    with (root/'.registry.lock').open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        yield
def validate(m):
    require(m.get('schema_version')==1,'Unsupported schema_version')
    ident(m.get('experiment_id'));ident(m.get('baseline_id'))
    require(m.get('track') in ['E','N','A'],'track must be E/N/A')
    require(m.get('contract_approved') is True,'Contract is not approved')
    require(bool(m.get('owner')) and bool(m.get('author')),'owner and author required')
    for k in ['baseline_commit','candidate_commit']:commit(m.get(k),k)
    for k in ['workload_fingerprint','environment_fingerprint','dataset_manifest_sha256','initial_checkpoint_sha256','base_config_sha256','candidate_config_sha256','validation_contract_sha256','comparison_tool_sha256']:sha(m.get(k),k)
    require(isinstance(m.get('allowed_changes'),list) and m['allowed_changes'],'allowed_changes required')
    require(isinstance(m.get('checks_required'),list) and m['checks_required'],'checks_required required')
    require(len(set(m['checks_required']))==len(m['checks_required']),'Duplicate required checks')
    require(isinstance(m.get('quality_required'),bool),'quality_required must be explicit')
    require(m['track']=='E' or m['quality_required'],'N/A changes require quality evaluation')
    require(isinstance(m.get('performance_policy'),dict) and m['performance_policy'],'performance_policy required')
    return m
def baseline_ok(m,b):
    require(m['baseline_id']==b.get('baseline_id'),'STALE: baseline_id changed')
    require(m['baseline_commit']==b.get('commit'),'STALE: baseline commit changed')
    require(m['base_config_sha256']==b.get('config_sha256'),'STALE: baseline config changed')
    require(m['workload_fingerprint']==b.get('workload_fingerprint'),'Workload contract mismatch')
def local_file(folder,name):
    require(isinstance(name,str) and name and not Path(name).is_absolute(),'Artifact path must be relative')
    require('\\' not in name and all(x not in ('','.','..') for x in name.split('/')),'Artifact path must be canonical')
    require(name.split('/')[0] not in ('evidence.json','gate-result.json','_archive_meta'),'Reserved artifact path')
    root=folder.resolve();p=(folder/name).resolve()
    require(p.is_relative_to(root) and p.is_file(),'Missing/escaping artifact: '+name)
    return p
def snapshot_bundle(source,target):
    source=Path(source).resolve();raw=source.read_bytes();e=json.loads(raw)
    require(isinstance(e.get('artifacts'),list) and e['artifacts'],'Evidence artifacts required')
    target.mkdir(parents=True,exist_ok=True);(target/'evidence.json').write_bytes(raw)
    seen=set()
    for a in e['artifacts']:
        name=a.get('path');p=local_file(source.parent,name)
        require(name not in seen,'Duplicate artifact path');seen.add(name)
        dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    return target/'evidence.json'


def sync_archive_directory(path):
    require(path.resolve(strict=True) == path, 'Archive directory uses a linked path')
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def sync_primary_archive(archive, report, comparison_sha256):
    """Sync the verified index and required metadata, including all nested entries."""
    evidence_path = archive / 'evidence.json'
    saved_gate = archive / 'gate-result.json'
    require(read(saved_gate) == report, 'Original archive gate changed before durability confirmation')
    expected = {item['path']: item['sha256'] for item in read(evidence_path)['artifacts']}
    expected.update({'evidence.json': report['evidence_sha256'], 'gate-result.json': digest(saved_gate),
                     '_archive_meta/manifest.json': report['manifest_sha256'],
                     '_archive_meta/baseline.json': report['baseline_snapshot_sha256'],
                     '_archive_meta/compare_runs.py': comparison_sha256})
    directories = {archive}
    for name, checksum in expected.items():
        path = archive / name
        require(path.is_relative_to(archive) and path.resolve(strict=True) == path,
                'Primary archive verification requires an original unlinked file: ' + name)
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        with os.fdopen(os.open(path, flags), 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode), 'Primary archive evidence must be a regular file: ' + name)
            remaining = before.st_size
            checksum_actual = hashlib.sha256()
            while remaining:
                block = stream.read(min(1_048_576, remaining))
                require(bool(block), 'Primary archive evidence became shorter: ' + name)
                remaining -= len(block)
                checksum_actual.update(block)
            require(checksum_actual.hexdigest() == checksum, 'Primary archive evidence changed: ' + name)
            os.fsync(stream.fileno())
            after = path.stat(follow_symlinks=False)
            identity = ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
            require(all(getattr(after, field) == getattr(before, field) for field in identity),
                    'Primary archive path changed during confirmation: ' + name)
        for directory in path.parents:
            if directory == archive:
                break
            directories.add(directory)
    for directory in sorted(directories, key=lambda path: (len(path.parts), str(path)), reverse=True):
        sync_archive_directory(directory)


def publish_archive(root, staging, report, compare_tool, durable):
    parent = staging.parent
    experiment = parent.parent
    destination = parent / report['evidence_sha256']
    comparison_sha = read(experiment / 'manifest.json')['comparison_tool_sha256']
    existing = destination.exists()
    if existing:
        require(digest(destination / 'evidence.json') == destination.name, 'Archive content address mismatch')
        prior = gate(root, report['experiment_id'], destination / 'evidence.json', compare_tool)
        require(read(destination / 'gate-result.json') == prior, 'Archive gate-result mismatch')
        require(digest(destination / '_archive_meta/manifest.json') == report['manifest_sha256'], 'Archive manifest mismatch')
        require(digest(destination / '_archive_meta/baseline.json') == prior['baseline_snapshot_sha256'], 'Archive baseline snapshot mismatch')
        require(digest(destination / '_archive_meta/compare_runs.py') == comparison_sha, 'Archive comparator mismatch')
    else:
        metadata = staging / '_archive_meta'
        metadata.mkdir()
        shutil.copyfile(experiment / 'manifest.json', metadata / 'manifest.json')
        shutil.copyfile(root / 'baseline.json', metadata / 'baseline.json')
        shutil.copyfile(compare_tool, metadata / 'compare_runs.py')
        write(staging / 'gate-result.json', report)
    if durable:
        sync_primary_archive(destination if existing else staging, report, comparison_sha)
    if not existing:
        os.rename(staging, destination)
    if durable:
        # Publish the rename and the accepted-evidence directory entry before a caller sees PASS.
        for directory in (parent, *parent.parents):
            sync_archive_directory(directory)
            if directory == root:
                break
    return destination


def gate(root,expid,bundle,compare_tool):
    exp=root/'experiments'/ident(expid);m=validate(read(exp/'manifest.json'))
    baseline_ok(m,read(root/'baseline.json'))
    require(digest(compare_tool)==m['comparison_tool_sha256'],'Comparison tool version differs from contract')
    folder=Path(bundle).resolve().parent;e=read(bundle)
    require(e.get('schema_version')==1,'Unsupported evidence schema')
    require(e.get('experiment_id')==expid,'Evidence experiment mismatch')
    require(e.get('manifest_sha256')==digest(exp/'manifest.json'),'Evidence belongs to another manifest')
    require(e.get('candidate_commit')==m['candidate_commit'],'Candidate commit mismatch')
    require(e.get('baseline_id')==m['baseline_id'],'Evidence baseline mismatch')
    artifacts={}
    require(isinstance(e.get('artifacts'),list) and e['artifacts'],'Evidence artifacts required')
    for a in e['artifacts']:
        p=local_file(folder,a.get('path'));sha(a.get('sha256'),'artifact sha256')
        require(a['path'] not in artifacts,'Duplicate artifact path')
        require(digest(p)==a['sha256'],'Artifact checksum mismatch: '+a['path']);artifacts[a['path']]=p
    def linked(name):
        require(name in artifacts,'Evidence link must name a hashed artifact: '+str(name))
        return artifacts[name]
    def attestation(item,kind):
        require(item.get('status')=='PASS','Required attestation not PASS: '+kind)
        actual=read(linked(item.get('artifact')))
        for field,expected in [('status','PASS'),('kind',kind),('candidate_commit',m['candidate_commit']),('manifest_sha256',e['manifest_sha256']),('validation_contract_sha256',m['validation_contract_sha256'])]:
            require(actual.get(field)==expected,'Structured attestation mismatch: '+kind+'/'+field)
            if field in item:require(item[field]==expected,'Outer attestation mismatch: '+kind+'/'+field)
        return actual
    for k in m['checks_required']:
        item=e.get('checks',{}).get(k,{})
        attestation(item,'check:'+k)
    review=e.get('review',{})
    require(review.get('status')=='PASS','Independent review not PASS')
    require(review.get('reviewer_id') and review['reviewer_id']!=m['author'],'Review author is not independent')
    require(review.get('candidate_commit')==m['candidate_commit'],'Stale review')
    actual_review=attestation(review,'review')
    require(actual_review.get('reviewer_id')==review['reviewer_id'],'Reviewer ID mismatch')
    integ=e.get('integration',{})
    require(integ.get('status')=='PASS' and integ.get('candidate_commit')==m['candidate_commit'] and integ.get('baseline_id')==m['baseline_id'],'Integration proof missing or stale')
    actual_integ=attestation(integ,'integration')
    require(actual_integ.get('baseline_id')==m['baseline_id'],'Stale structured integration proof')
    if m['quality_required']:
        attestation(e.get('quality',{}),'quality')
    comparison=e.get('comparison',{})
    inp=linked(comparison.get('input'));reported=linked(comparison.get('report'))
    data=read(inp)
    require(data.get('experiment_id')==expid,'Comparison experiment mismatch')
    require(data.get('manifest_sha256')==e['manifest_sha256'],'Comparison manifest mismatch')
    policy={k:data.get(k) for k in ('normalization_source_samples','statistics','thresholds')}
    require(policy==m['performance_policy'],'Comparison policy differs from approved contract')
    require(data.get('workload_fingerprint')==m['workload_fingerprint'],'Comparison workload differs from approved contract')
    for pair in data.get('pairs',[]):
        for arm in ('baseline','candidate'):
            record=pair.get(arm,{})
            require(record.get('code_sha')==m[arm+'_commit'],'Comparison commits mismatch')
            require(record.get('environment_fingerprint')==m['environment_fingerprint'],'Comparison environment mismatch')
            require(record.get('initial_checkpoint_sha256')==m['initial_checkpoint_sha256'],'Comparison initial checkpoint mismatch')
            require(record.get('config_sha256')==m['base_config_sha256' if arm=='baseline' else 'candidate_config_sha256'],'Comparison effective config mismatch')
            require(record.get('dataset_manifest_sha256')==m['dataset_manifest_sha256'],'Comparison dataset mismatch')
    # Recompute the statistical result; an agent-written PASS string is insufficient.
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)/'comparison.json'
        try:
            result=subprocess.run([sys.executable,str(compare_tool),str(inp),'--output',str(out)],capture_output=True,text=True,timeout=120)
        except subprocess.TimeoutExpired:
            fail('Comparison tool exceeded 120-second limit')
        require(result.returncode==0 and out.is_file(),'Comparison tool failed: '+result.stderr[-600:])
        fresh=read(out);stored=read(reported)
    require(fresh==stored,'Stored comparison differs from recomputed result')
    report = {'status':'ELIGIBLE_FOR_HUMAN_REVIEW','experiment_id':expid,'baseline_id':m['baseline_id'],'baseline_snapshot_sha256':digest(root/'baseline.json'),'candidate_commit':m['candidate_commit'],'manifest_sha256':e['manifest_sha256'],'evidence_sha256':digest(bundle),'track':m['track'],'performance':fresh,'limitation':'Checksums and records do not authenticate authors or prove training quality. Platform permissions and independent review remain required.'}
    if fresh.get('status') in ('FAIL', 'INCONCLUSIVE'):
        raise EvaluatedNegativeGate(report)
    require(fresh.get('status')=='PASS','Performance evidence is '+str(fresh.get('status')))
    return report
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('.perf-state'))
    sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('init');q.add_argument('--baseline',required=True,type=Path)
    q=sub.add_parser('validate');q.add_argument('manifest',type=Path)
    q=sub.add_parser('register');q.add_argument('manifest',type=Path)
    q=sub.add_parser('gate');q.add_argument('experiment_id');q.add_argument('--bundle',required=True,type=Path)
    q=sub.add_parser('archive');q.add_argument('experiment_id');q.add_argument('--bundle',required=True,type=Path)
    q.add_argument('--durable-primary', action='store_true', help='verify and synchronize the indexed archive before reporting success')
    sub.add_parser('status')
    a=p.parse_args(argv);root=a.root.resolve();compare_tool=Path(__file__).with_name('compare_runs.py')
    if a.cmd=='validate':validate(read(a.manifest));print('VALID');return 0
    with lock(root):
        if a.cmd=='init':
            require(not (root/'baseline.json').exists(),'Registry already initialized; update baseline through reviewed workflow')
            b=read(a.baseline);ident(b.get('baseline_id'));commit(b.get('commit'),'commit')
            sha(b.get('config_sha256'),'config_sha256');sha(b.get('workload_fingerprint'),'workload_fingerprint')
            write(root/'baseline.json',b);print('INITIALIZED')
        elif a.cmd=='register':
            raw=a.manifest.read_bytes()
            try:m=validate(json.loads(raw))
            except (ValueError,UnicodeError) as e:fail('Invalid manifest: '+str(e))
            baseline_ok(m,read(root/'baseline.json'))
            dst=root/'experiments'/m['experiment_id']/'manifest.json'
            if dst.exists():
                require(dst.read_bytes()==raw,'ID already has a different immutable manifest')
                print('ALREADY_REGISTERED')
            else:write_raw(dst,raw);print('REGISTERED')
        elif a.cmd in ['gate','archive']:
            durable = a.cmd == 'archive' and a.durable_primary
            parent=root/'experiments'/ident(a.experiment_id)/'accepted-evidence'
            try:
                parent.mkdir(parents=True,exist_ok=True)
                staging=Path(tempfile.mkdtemp(prefix='.archive-',dir=parent))
                try:
                    snapshot=snapshot_bundle(a.bundle,staging)
                    try:
                        report = gate(root, a.experiment_id, snapshot, compare_tool)
                    except EvaluatedNegativeGate as error:
                        if not durable:
                            raise
                        print(json.dumps(error.report, ensure_ascii=False, indent=2))
                        return ARCHIVE_EVALUATED_NEGATIVE_EXIT
                    if a.cmd=='archive':
                        try:
                            report['archive_path'] = str(publish_archive(root, staging, report, compare_tool, durable))
                        except Invalid as error:
                            if durable:
                                raise PrimaryArchiveDurabilityError(str(error)) from error
                            raise
                finally:
                    if staging.exists():shutil.rmtree(staging)
            except OSError as error:
                if durable:
                    raise PrimaryArchiveDurabilityError(str(error)) from error
                raise
            print(json.dumps(report,ensure_ascii=False,indent=2))
        elif a.cmd=='status':
            b=read(root/'baseline.json');rows=[]
            for f in sorted((root/'experiments').glob('*/manifest.json')):
                m=read(f);rows.append({'id':m['experiment_id'],'track':m['track'],'baseline':m['baseline_id'],'stale':m['baseline_id']!=b['baseline_id'] or m['baseline_commit']!=b['commit'] or m['base_config_sha256']!=b['config_sha256'] or m['workload_fingerprint']!=b['workload_fingerprint'],'archived_bundles':len(list((f.parent/'accepted-evidence').glob('[!.]*')))})
            print(json.dumps({'baseline':b,'experiments':rows},ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except PrimaryArchiveDurabilityError as e:print('PRIMARY ARCHIVE DURABILITY UNCONFIRMED: '+str(e),file=sys.stderr);sys.exit(ARCHIVE_DURABILITY_EXIT)
    except (Invalid,OSError,KeyError,TypeError) as e:print('BLOCKED: '+str(e),file=sys.stderr);sys.exit(2)
