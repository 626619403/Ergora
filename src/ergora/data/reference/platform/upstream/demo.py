#!/usr/bin/env python3
"""CPU-only synthetic fixture. No GPU, model, or real quality claim is involved."""
import argparse, hashlib, json
from pathlib import Path
import compare_runs, perfctl
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');return p
def prepare(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    state=out/'state';bundle=out/'bundle';bundle.mkdir()
    m={'schema_version':1,'experiment_id':'synthetic-demo','baseline_id':'synthetic-b0001','track':'E','contract_approved':True,'owner':'DEMO_ONLY','author':'synthetic-author','baseline_commit':'a'*40,'candidate_commit':'b'*40,'allowed_changes':['SYNTHETIC_FIXTURE_NOT_TRAINING'],'checks_required':['forward','backward','harness_integrity'],'quality_required':True}
    for k in ['workload_fingerprint','environment_fingerprint','dataset_manifest_sha256','initial_checkpoint_sha256','base_config_sha256','candidate_config_sha256','validation_contract_sha256']:m[k]=hashlib.sha256(k.encode()).hexdigest()
    m['comparison_tool_sha256']=perfctl.digest(Path(__file__).with_name('compare_runs.py'))
    data=compare_runs.example();m['performance_policy']={k:data[k] for k in ['normalization_source_samples','statistics','thresholds']}
    b={'baseline_id':m['baseline_id'],'commit':m['baseline_commit'],'config_sha256':m['base_config_sha256'],'workload_fingerprint':m['workload_fingerprint'],'synthetic':True}
    manifest=write(out/'experiment.json',m);base=write(out/'baseline.json',b)
    perfctl.main(['--root',str(state),'init','--baseline',str(base)])
    perfctl.main(['--root',str(state),'register',str(manifest)])
    manifest_sha=perfctl.digest(manifest)
    data.update(experiment_id=m['experiment_id'],manifest_sha256=manifest_sha,workload_fingerprint=m['workload_fingerprint'])
    for pair in data['pairs']:
        for arm in ['baseline','candidate']:
            a=pair[arm];a.update(environment_fingerprint=m['environment_fingerprint'],initial_checkpoint_sha256=m['initial_checkpoint_sha256'],dataset_manifest_sha256=m['dataset_manifest_sha256'],config_sha256=m['base_config_sha256' if arm=='baseline' else 'candidate_config_sha256'])
    inp=write(bundle/'comparison-input.json',data)
    result=compare_runs.compare(data,perfctl.digest(inp));write(bundle/'comparison-report.json',result)
    e={'schema_version':1,'experiment_id':m['experiment_id'],'baseline_id':m['baseline_id'],'candidate_commit':m['candidate_commit'],'manifest_sha256':manifest_sha,'synthetic':True,'checks':{},'comparison':{'input':'comparison-input.json','report':'comparison-report.json'}}
    def att(kind,name,**extra):
        obj={'kind':kind,'status':'PASS','candidate_commit':m['candidate_commit'],'manifest_sha256':manifest_sha,'validation_contract_sha256':m['validation_contract_sha256'],'synthetic':True,**extra}
        write(bundle/name,obj)
        return {'status':'PASS','artifact':name,**extra}
    for k in m['checks_required']:e['checks'][k]=att('check:'+k,'checks/'+k+'.json')
    e['review']=att('review','review.json',reviewer_id='synthetic-reviewer');e['review']['candidate_commit']=m['candidate_commit']
    e['integration']=att('integration','integration.json',baseline_id=m['baseline_id']);e['integration']['candidate_commit']=m['candidate_commit']
    e['quality']=att('quality','quality.json')
    e['artifacts']=[{'path':p.relative_to(bundle).as_posix(),'sha256':perfctl.digest(p)} for p in sorted(bundle.rglob('*')) if p.is_file()]
    evidence=write(bundle/'evidence.json',e)
    return {'out':out,'state':state,'bundle':bundle,'manifest':manifest,'evidence':evidence,'experiment_id':m['experiment_id']}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    f=prepare(a.out)
    perfctl.main(['--root',str(f['state']),'archive',f['experiment_id'],'--bundle',str(f['evidence'])])
    print('SYNTHETIC DEMO ONLY: no training speed, correctness, or quality was measured.')
if __name__=='__main__':main()
