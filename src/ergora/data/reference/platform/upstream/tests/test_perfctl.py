import contextlib, io, json, shutil, sys, tempfile, unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent if Path(__file__).parent.name=='tests' else Path(__file__).parent))
import demo, perfctl
class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        with contextlib.redirect_stdout(io.StringIO()):self.f=demo.prepare(Path(self.temp.name)/'fixture')
        self.tool=Path(perfctl.__file__).with_name('compare_runs.py')
    def tearDown(self):self.temp.cleanup()
    def gate(self):return perfctl.gate(self.f['state'],self.f['experiment_id'],self.f['evidence'],self.tool)
    def update_evidence(self):
        e=perfctl.read(self.f['evidence'])
        for a in e['artifacts']:a['sha256']=perfctl.digest(self.f['bundle']/a['path'])
        demo.write(self.f['evidence'],e)
    def test_valid_is_not_release(self):self.assertEqual(self.gate()['status'],'ELIGIBLE_FOR_HUMAN_REVIEW')
    def test_stale_baseline_config(self):
        p=self.f['state']/'baseline.json';b=perfctl.read(p);b['config_sha256']='f'*64;demo.write(p,b)
        with self.assertRaisesRegex(perfctl.Invalid,'STALE'):self.gate()
    def test_missing_required_check(self):
        e=perfctl.read(self.f['evidence']);e['checks']['forward']['status']='NOT_RUN';demo.write(self.f['evidence'],e)
        with self.assertRaises(perfctl.Invalid):self.gate()
    def test_old_quality_and_false_outer_pass(self):
        p=self.f['bundle']/'quality.json';original=perfctl.read(p)
        for key,value in [('candidate_commit','c'*40),('manifest_sha256','f'*64),('status','FAIL'),('validation_contract_sha256','e'*64)]:
            q={**original,key:value};demo.write(p,q);self.update_evidence()
            with self.assertRaises(perfctl.Invalid):self.gate()
    def test_wrong_run_bindings(self):
        p=self.f['bundle']/'comparison-input.json';original=perfctl.read(p)
        for key in ['config_sha256','dataset_manifest_sha256','environment_fingerprint','initial_checkpoint_sha256']:
            q=json.loads(json.dumps(original));q['pairs'][0]['candidate'][key]='f'*64;demo.write(p,q);self.update_evidence()
            with self.assertRaises(perfctl.Invalid):self.gate()
    def test_policy_tampering(self):
        p=self.f['bundle']/'comparison-input.json';q=perfctl.read(p);q['thresholds']['min_speedup_percent']=0;demo.write(p,q);self.update_evidence()
        with self.assertRaisesRegex(perfctl.Invalid,'policy'):self.gate()
    def test_artifact_corruption(self):
        (self.f['bundle']/'quality.json').write_text('{}')
        with self.assertRaisesRegex(perfctl.Invalid,'checksum'):self.gate()
    def test_traversal_and_reserved_paths(self):
        for path in ['a/../evidence.json','a//x','../x','/tmp/x','gate-result.json','_archive_meta/x','a\\b']:
            with self.assertRaises(perfctl.Invalid):perfctl.local_file(self.f['bundle'],path)
    def test_manifest_id_reuse(self):
        m=perfctl.read(self.f['manifest']);m['candidate_commit']='c'*40;demo.write(self.f['manifest'],m)
        with self.assertRaisesRegex(perfctl.Invalid,'immutable'):
            perfctl.main(['--root',str(self.f['state']),'register',str(self.f['manifest'])])
    def test_register_uses_validated_bytes(self):
        m=perfctl.read(self.f['manifest']);m['experiment_id']='newrace';demo.write(self.f['manifest'],m)
        raw=self.f['manifest'].read_bytes();original_validate=perfctl.validate
        def validate_then_mutate(value):
            result=original_validate(value)
            self.f['manifest'].write_text('{}')
            return result
        with patch.object(perfctl,'validate',side_effect=validate_then_mutate),contextlib.redirect_stdout(io.StringIO()):
            perfctl.main(['--root',str(self.f['state']),'register',str(self.f['manifest'])])
        self.assertEqual((self.f['state']/'experiments'/'newrace'/'manifest.json').read_bytes(),raw)
    def test_archive_baseline_snapshot_corruption(self):
        args=['--root',str(self.f['state']),'archive',self.f['experiment_id'],'--bundle',str(self.f['evidence'])]
        with contextlib.redirect_stdout(io.StringIO()):perfctl.main(args)
        archived=next((self.f['state']/'experiments'/self.f['experiment_id']/'accepted-evidence').glob('[!.]*'))
        (archived/'_archive_meta'/'baseline.json').write_text('{}')
        with self.assertRaisesRegex(perfctl.Invalid,'baseline snapshot'):perfctl.main(args)
    def test_archive_and_changed_input(self):
        args=['--root',str(self.f['state']),'archive',self.f['experiment_id'],'--bundle',str(self.f['evidence'])]
        with contextlib.redirect_stdout(io.StringIO()):perfctl.main(args);perfctl.main(args)
        archived=next((self.f['state']/'experiments'/self.f['experiment_id']/'accepted-evidence').glob('[!.]*'))
        e=perfctl.read(archived/'evidence.json');e['altered']=True;demo.write(archived/'evidence.json',e)
        with self.assertRaisesRegex(perfctl.Invalid,'content address'):perfctl.main(args)
    def test_archive_gate_record_corruption(self):
        args=['--root',str(self.f['state']),'archive',self.f['experiment_id'],'--bundle',str(self.f['evidence'])]
        with contextlib.redirect_stdout(io.StringIO()):perfctl.main(args)
        archived=next((self.f['state']/'experiments'/self.f['experiment_id']/'accepted-evidence').glob('[!.]*'))
        (archived/'gate-result.json').write_text('{}')
        with self.assertRaisesRegex(perfctl.Invalid,'gate-result'):perfctl.main(args)
    def test_snapshot_preserves_validated_bytes(self):
        target=Path(self.temp.name)/'snapshot';snap=perfctl.snapshot_bundle(self.f['evidence'],target)
        (self.f['bundle']/'quality.json').write_text('changed after snapshot')
        self.assertEqual(perfctl.gate(self.f['state'],self.f['experiment_id'],snap,self.tool)['status'],'ELIGIBLE_FOR_HUMAN_REVIEW')
if __name__=='__main__':unittest.main(verbosity=2)
