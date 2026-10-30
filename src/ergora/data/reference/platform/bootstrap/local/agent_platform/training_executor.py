"""Manual execution of one explicitly selected, immutable local experiment."""
from __future__ import annotations

from dataclasses import asdict
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess

from .core import PYTHON, UPSTREAM, git, read, require, write
from .sandbox import Sandbox
from .training import TRAINING, binding_from, fence_path, perf_root


def track(record: dict, folder: Path, manifest: dict, gate: dict) -> str:
    from mlflow import MlflowClient
    client = MlflowClient(tracking_uri='http://127.0.0.1:5000')
    project = record['runner']['project']
    experiment = client.get_experiment_by_name('training-' + project)
    exp_id = experiment.experiment_id if experiment else client.create_experiment('training-' + project)
    binding = record['experiment']['binding']
    runs = client.search_runs([exp_id], filter_string="tags.manifest_sha = '" + binding['manifest_sha'] + "'", max_results=2)
    require(len(runs) <= 1, 'Multiple MLflow runs bind this manifest; reconcile tracking records')
    if runs: run_id = runs[0].info.run_id
    else:
        run_id = client.create_run(exp_id, tags={'manifest_sha': binding['manifest_sha'],
            'experiment_id': binding['experiment_id'], 'baseline_sha': binding['baseline_sha'],
            'candidate_sha': binding['candidate_sha'], 'runner_job_id': record['job_id'],
            'purpose': 'paired-comparison', 'trust_model': 'trusted-current-container'}).info.run_id
    for key in ('baseline_id', 'workload_fingerprint', 'environment_fingerprint', 'dataset_manifest_sha256',
                'initial_checkpoint_sha256', 'base_config_sha256', 'candidate_config_sha256', 'validation_contract_sha256'):
        client.log_param(run_id, key, manifest[key])
    client.log_metric(run_id, 'gate_passed', int(gate['passed']))
    archive = gate.get('archive_report')
    if archive:
        def metrics(value, prefix='performance'):
            if isinstance(value, dict):
                for key, item in value.items(): metrics(item, prefix + '.' + key)
            elif type(value) in {int, float}: client.log_metric(run_id, prefix, value)
        metrics(archive['performance'])
        client.log_artifacts(run_id, archive['archive_path'], artifact_path='immutable-evidence')
    client.log_artifact(run_id, str(TRAINING / 'manifests' / (binding['experiment_id'] + '.json')))
    for file in ('gate-report.json', 'run-output/execution.log', 'archive-output/execution.log', 'failure-evidence.json'):
        path = folder / file
        if path.exists(): client.log_artifact(run_id, str(path), artifact_path='runner')
    client.set_terminated(run_id, status='FINISHED' if gate['passed'] else 'FAILED')
    return run_id


def process(folder: Path) -> dict:
    with (folder / 'executor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (folder / 'result.json').exists(): return read(folder / 'result.json')
        record = read(folder / 'request.json')
        binding = binding_from(record['experiment']['binding'])
        ident = binding.experiment_id
        fence = fence_path(ident)
        state, detail = 'FAILED', ''
        gate_reference = None
        try:
            require(not fence.exists(), 'Cancelled before training runner start')
            manifest_path = TRAINING / 'manifests' / (ident + '.json')
            require(hashlib.sha256(manifest_path.read_bytes()).hexdigest() == binding.manifest_sha, 'Frozen manifest changed')
            manifest = read(manifest_path)
            write(folder / 'started.json', {'binding': asdict(binding), 'job_id': record['job_id']})
            mirror = folder / 'repo.git'
            if not mirror.exists(): git(folder, 'clone', '--bare', '--no-local', record['runner']['repo'], str(mirror))
            checkouts = {}
            for arm, commit in [('baseline', binding.baseline_sha), ('candidate', binding.candidate_sha)]:
                checkout = folder / arm
                if not checkout.exists(): git(mirror, 'worktree', 'add', '--detach', str(checkout), commit)
                checkouts[arm] = checkout
            output = folder / 'run-output'
            values = {'manifest': str(manifest_path), 'output': str(output),
                      'baseline_repo': str(checkouts['baseline']), 'candidate_repo': str(checkouts['candidate'])}
            command = []
            for arg in record['runner']['command']:
                for key, value in values.items(): arg = arg.replace('{' + key + '}', value)
                command.append(arg)
            code = Sandbox().run('af-perf-' + ident + '-run', checkouts['candidate'], output,
                command, writable=False, fence=fence, timeout=record['runner']['timeout_seconds'])
            require(code == 0, f'Training runner exited {code}; inspect {output}/execution.log')
            require(not fence.exists(), 'Cancelled before evidence validation')
            evidence = output / 'evidence.json'
            archive_output = folder / 'archive-output'
            archive_report = None
            failure = None
            if not evidence.is_file():
                failure = 'Runner did not produce evidence.json; no numerical/performance claims can pass'
            else:
                command = [str(PYTHON), str(UPSTREAM / 'perfctl.py'), '--root', str(perf_root(record['runner']['project'])),
                           'archive', ident, '--bundle', str(evidence)]
                code = Sandbox().run('af-perf-' + ident + '-archive', checkouts['candidate'], archive_output,
                    command, writable=False, fence=fence, timeout=600)
                if code:
                    failure = f'Evidence archive/gate exited {code}; inspect {archive_output}/execution.log'
                else:
                    archive_report, _ = json.JSONDecoder().raw_decode((archive_output / 'execution.log').read_text().lstrip())
                    require(archive_report['status'] == 'ELIGIBLE_FOR_HUMAN_REVIEW' and
                        archive_report['experiment_id'] == ident and archive_report['candidate_commit'] == binding.candidate_sha and
                        archive_report['manifest_sha256'] == binding.manifest_sha, 'Evidence archive result binding mismatch')
            if failure:
                failure_path = folder / 'failure-evidence.json'
                write(failure_path, {'binding': asdict(binding), 'status': 'FAIL', 'reason': failure,
                                    'run_log_sha256': hashlib.sha256((output / 'execution.log').read_bytes()).hexdigest()})
                evidence_sha = hashlib.sha256(failure_path.read_bytes()).hexdigest()
                summary = failure
            else:
                evidence_sha = archive_report['evidence_sha256']
                summary = 'Immutable evidence passed; awaiting local operator approval for an integration/revalidation ticket'
            gate = {'binding': asdict(binding), 'manifest_sha256': binding.manifest_sha, 'passed': failure is None,
                    'evidence_sha256': evidence_sha, 'summary': summary, 'archive_report': archive_report}
            gate_path = folder / 'gate-report.json'
            write(gate_path, gate)
            run_id = track(record, folder, manifest, gate)
            gate_reference = {'report': str(gate_path), 'report_sha256': hashlib.sha256(gate_path.read_bytes()).hexdigest(),
                              'mlflow_run_id': run_id}
            state, detail = 'SUCCEEDED', summary
        except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
            state, detail = ('CANCELLED' if fence.exists() else 'FAILED'), f'{type(error).__name__}: {error}'
        if fence.exists(): state, detail = 'CANCELLED', 'Cancellation fence observed; no release allowed'
        result = {'binding': asdict(binding), 'job_id': record['job_id'], 'state': state,
                  'detail': detail, 'gate': gate_reference}
        write(folder / 'result.json', result)
        if state != 'SUCCEEDED' or gate_reference and not read(gate_reference['report'])['passed']:
            write(TRAINING / 'negative-results' / (ident + '.json'),
                  {'project': record['runner']['project'], 'experiment_id': ident, 'binding': asdict(binding),
                   'state': state, 'detail': detail, 'result': str(folder / 'result.json')})
        return result
