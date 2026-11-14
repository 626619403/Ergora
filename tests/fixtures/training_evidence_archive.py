"""Construct synthetic native archive records; never a training or quality result."""

from contextlib import nullcontext, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import sys

import compare_runs
import perfctl


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


payload = json.load(sys.stdin)
runtime, prefix = Path(payload['runtime']), Path(payload['prefix'])
# Replace the parent fixture's negative scenario before constructing this positive one.
(runtime / 'training/negative-results/alpha.json').unlink()
manifest_path = runtime / 'training/manifests/alpha.json'
manifest = json.loads(manifest_path.read_bytes())
comparison = compare_runs.example()
manifest.update(comparison_tool_sha256=perfctl.digest(Path(perfctl.__file__).with_name('compare_runs.py')),
                performance_policy={key: comparison[key] for key in ('normalization_source_samples', 'statistics', 'thresholds')})
manifest_sha = write(manifest_path, manifest)
write(prefix / 'experiments/alpha/manifest.json', manifest)
spec_path = runtime / 'training/specs/alpha.json'
spec = json.loads(spec_path.read_bytes())
spec['binding']['manifest_sha'] = manifest_sha
write(spec_path, spec)
job = runtime / 'training/jobs/alpha'
request = json.loads((job / 'request.json').read_bytes())
request['experiment'] = spec
write(job / 'request.json', request)
write(job / 'started.json', {'binding': spec['binding'], 'job_id': request['job_id']})
comparison.update(experiment_id='alpha', manifest_sha256=manifest_sha, workload_fingerprint=manifest['workload_fingerprint'])
for pair in comparison['pairs']:
    for arm in ('baseline', 'candidate'):
        pair[arm].update(code_sha=manifest[arm + '_commit'], environment_fingerprint=manifest['environment_fingerprint'],
                         initial_checkpoint_sha256=manifest['initial_checkpoint_sha256'], dataset_manifest_sha256=manifest['dataset_manifest_sha256'],
                         config_sha256=manifest['base_config_sha256' if arm == 'baseline' else 'candidate_config_sha256'])
bundle = runtime.parent / 'synthetic-evidence-source'
write(bundle / 'comparison-input.json', comparison)
write(bundle / 'comparison-report.json', compare_runs.compare(comparison, perfctl.digest(bundle / 'comparison-input.json')))
evidence = {'schema_version': 1, 'experiment_id': 'alpha', 'baseline_id': manifest['baseline_id'],
            'candidate_commit': manifest['candidate_commit'], 'manifest_sha256': manifest_sha, 'synthetic': True,
            'checks': {}, 'comparison': {'input': 'comparison-input.json', 'report': 'comparison-report.json'}}


def attestation(kind, path, **extra):
    write(bundle / path, {'kind': kind, 'status': 'PASS', 'candidate_commit': manifest['candidate_commit'],
                         'manifest_sha256': manifest_sha, 'validation_contract_sha256': manifest['validation_contract_sha256'],
                         'synthetic': True, **extra})
    return {'status': 'PASS', 'artifact': path, **extra}


for name in manifest['checks_required']:
    evidence['checks'][name] = attestation('check:' + name, 'checks/' + name + '.json')
evidence['review'] = attestation('review', 'review.json', reviewer_id='independent-synthetic-reviewer', candidate_commit=manifest['candidate_commit'])
evidence['integration'] = attestation('integration', 'integration.json', baseline_id=manifest['baseline_id'], candidate_commit=manifest['candidate_commit'])
evidence['quality'] = attestation('quality', 'quality.json')
(bundle / 'notes.txt').write_text('证据窗口 🧪\nsynthetic only\n', encoding='utf-8')
(bundle / 'trace.bin').write_bytes(b'\0trace')
evidence['artifacts'] = [{'path': path.relative_to(bundle).as_posix(), 'sha256': perfctl.digest(path)}
                         for path in sorted(bundle.rglob('*')) if path.is_file()]
write(bundle / 'evidence.json', evidence)
if os.name == 'nt':
    # Only serialized fixture construction skips the POSIX writer lock.
    # The product is an SDK-free reader of an existing Linux archive.
    perfctl.lock = lambda _root: nullcontext()
captured = io.StringIO()
with redirect_stdout(captured):
    perfctl.main(['--root', str(prefix), 'archive', 'alpha', '--bundle', str(bundle / 'evidence.json')])
archive_report = json.loads(captured.getvalue())
gate = {'binding': spec['binding'], 'manifest_sha256': manifest_sha, 'passed': True,
        'evidence_sha256': archive_report['evidence_sha256'], 'summary': 'Synthetic archive; no real training',
        'archive_report': archive_report}
gate_sha = write(job / 'gate-report.json', gate)
write(job / 'result.json', {'binding': spec['binding'], 'job_id': request['job_id'], 'state': 'SUCCEEDED',
                          'detail': gate['summary'], 'gate': {'report': str(job / 'gate-report.json'),
                          'report_sha256': gate_sha, 'mlflow_run_id': 'synthetic-recorded-only'}})
print(json.dumps({'archive': archive_report, 'bundle': str(bundle), 'native_archive_lock_used': os.name != 'nt'}))
