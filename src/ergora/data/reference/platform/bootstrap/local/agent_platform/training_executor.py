"""Manual execution of one explicitly selected, immutable local experiment."""
from __future__ import annotations

from dataclasses import asdict
from collections.abc import Callable
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess

from .core import PYTHON, STATE, UPSTREAM, git, read, require, write
from .sandbox import Sandbox
from .training import TRAINING, binding_from, fence_path, perf_root


def track(record: dict, folder: Path, manifest: dict, gate: dict | None, screen: dict | None = None) -> str:
    from mlflow import MlflowClient
    from mlflow.entities import ViewType

    client = MlflowClient(tracking_uri='http://127.0.0.1:5000')
    project = record['runner']['project']
    experiment = client.get_experiment_by_name('training-' + project)
    exp_id = experiment.experiment_id if experiment else client.create_experiment('training-' + project)
    binding = record['experiment']['binding']
    runs = client.search_runs([exp_id], filter_string="tags.manifest_sha = '" + binding['manifest_sha'] + "'",
                              run_view_type=ViewType.ALL, max_results=2)
    require(len(runs) <= 1, 'Multiple MLflow runs bind this manifest; reconcile tracking records')
    require(not runs, 'An MLflow run already binds this manifest; reconcile tracking records')
    run_id = client.create_run(exp_id, tags={'manifest_sha': binding['manifest_sha'],
        'experiment_id': binding['experiment_id'], 'baseline_sha': binding['baseline_sha'],
        'candidate_sha': binding['candidate_sha'], 'runner_job_id': record['job_id'],
        'purpose': 'screen' if screen is not None else 'paired-comparison', 'trust_model': 'trusted-current-container'}).info.run_id
    for key in ('baseline_id', 'workload_fingerprint', 'environment_fingerprint', 'dataset_manifest_sha256',
                'initial_checkpoint_sha256', 'base_config_sha256', 'candidate_config_sha256', 'validation_contract_sha256'):
        client.log_param(run_id, key, manifest[key])
    if screen is not None:
        client.set_tag(run_id, 'quality_scope', screen['achieved_quality_tier'])
        client.set_tag(run_id, 'screen_decision', screen['decision'])
        client.log_artifact(run_id, str(folder / 'run-output/screen-result.json'), artifact_path='screen')
    else:
        client.log_metric(run_id, 'gate_passed', int(gate['passed']))
    archive = gate.get('archive_report') if gate is not None else None
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
    client.set_terminated(run_id, status='FINISHED' if screen is not None or gate['passed'] else 'FAILED')
    return run_id


def process(folder: Path, *, admit: Callable[[Path, dict], None] | None = None,
            before_runner: Callable[[Path, dict, dict, dict], tuple[dict, Callable[[], None]]] | None = None,
            track_full: Callable[[dict, Path, dict, dict, bytes], str] | None = None) -> dict:
    with (folder / 'executor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (folder / 'result.json').exists(): return read(folder / 'result.json')
        record = read(folder / 'request.json')
        configuration_runner = record['runner']['configuration_readback'] is not None
        if configuration_runner:
            require(admit is not None and before_runner is not None,
                    'Configuration runner requires its original managed execution callback')
        require(not ((folder / 'started.json').exists() or (folder / 'started.json').is_symlink()),
                'An earlier executor started without a result; reconcile it before further execution')
        if admit is None:
            require(not ((folder / 'managed-execution').exists() or (folder / 'managed-execution').is_symlink()),
                    'This job is reserved for managed execution; use its original execution request')
        else:
            admit(folder, record)
        binding = binding_from(record['experiment']['binding'])
        ident = binding.experiment_id
        from ergora.training.execution_protocol import require_not_skipped
        require_not_skipped({'state_directory': str(STATE)}, ident)
        fence = fence_path(ident)
        state, detail = 'FAILED', ''
        gate_reference, screen_reference = None, None
        try:
            require(not fence.exists(), 'Cancelled before training runner start')
            manifest_path = TRAINING / 'manifests' / (ident + '.json')
            require(hashlib.sha256(manifest_path.read_bytes()).hexdigest() == binding.manifest_sha, 'Frozen manifest changed')
            manifest = read(manifest_path)
            from ergora.training.materials import execution_plan
            execution = execution_plan(manifest, record['runner'])
            if execution.get('cpu_contract') is not None:
                from ergora.training.runtime.evidence import read_cpu_preparation_admission
                read_cpu_preparation_admission(STATE, ident, manifest, record['runner'])
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
            if configuration_runner:
                configuration_values, active = before_runner(folder, record, checkouts, manifest)
                values.update(configuration_values)
            command = []
            for arg in record['runner']['command']:
                for key, value in values.items(): arg = arg.replace('{' + key + '}', value)
                command.append(arg)
            if configuration_runner:
                active()
                import ergora.training.execution_protocol as protocol
                configuration = read(folder / 'configuration-request.json')
            runner_timeout = record['runner']['timeout_seconds']
            if configuration_runner:
                import ergora.training.execution_protocol as protocol
                configuration = read(folder / 'configuration-request.json')
                context = configuration['context']
                active()
                remaining = protocol.budget_clock.remaining(context['authorization']['clock'], context['policy']['wall_seconds'], context['policy']['cleanup_seconds'])
                runner_timeout = min(runner_timeout, remaining)
                if execution['operation'] == 'training-screen-v1':
                    runner_timeout = min(runner_timeout, execution['plan']['window']['maximum_seconds'])
                require(runner_timeout >= 1, 'blocked: remaining original wrapper walltime below supported minimum')
            require_not_skipped({'state_directory': str(STATE)}, ident)
            code = Sandbox().run('af-perf-' + ident + '-run', checkouts['candidate'], output,
                command, writable=False, fence=fence, timeout=runner_timeout)
            require(code == 0, f'Training runner exited {code}; inspect {output}/execution.log')
            require(not fence.exists(), 'Cancelled before evidence validation')
            if execution['operation'] == 'training-screen-v1':
                from ergora.training.runtime.evidence import _screen_bundle
                from ergora.training.materials import confirm_file, read_raw
                configuration_raw = read_raw(folder / 'configuration-request.json', 16 * 1_048_576)
                configuration = read(folder / 'configuration-request.json')
                configuration['_raw_sha256'] = hashlib.sha256(configuration_raw).hexdigest()
                bundle = _screen_bundle(output, configuration, manifest)
                for path, (original, _, _, _) in bundle['inventory'].originals.items():
                    confirm_file(path, original, STATE)
                bundle['inventory'].confirm()
                active()
                track(record, folder, manifest, None, bundle['result'])
                bundle['inventory'].confirm()
                active()
                screen_reference = {'report': str(output / 'screen-result.json'), 'report_sha256': bundle['sha256']}
                state, detail = bundle['state'], bundle['result']['decision']
            else:
                evidence = output / 'evidence.json'
                archive_output = folder / 'archive-output'
                archive_report = None
                archive_output_raw = None
                negative_gate = None
                failure = None
                if not evidence.is_file():
                    require(track_full is None, 'Managed archive requires original evidence.json before tracking')
                    failure = 'Runner did not produce evidence.json; no numerical/performance claims can pass'
                else:
                    command = [str(PYTHON), str(UPSTREAM / 'perfctl.py'), '--root', str(perf_root(record['runner']['project'])),
                               'archive', ident, '--bundle', str(evidence)]
                    managed = track_full is not None
                    if managed:
                        from perfctl import ARCHIVE_DURABILITY_EXIT, ARCHIVE_EVALUATED_NEGATIVE_EXIT

                        command.append('--durable-primary')
                    code = Sandbox().run('af-perf-' + ident + '-archive', checkouts['candidate'], archive_output,
                        command, writable=False, fence=fence, timeout=600)
                    if managed:
                        require(code != ARCHIVE_DURABILITY_EXIT,
                                f'Primary archive durability unconfirmed; inspect {archive_output}/execution.log')
                        require(type(code) is int and code in (0, ARCHIVE_EVALUATED_NEGATIVE_EXIT),
                                f'Managed archive has no verified gate (exit {code}); inspect {archive_output}/execution.log')
                    if code and not managed:
                        failure = f'Evidence archive/gate exited {code}; inspect {archive_output}/execution.log'
                    else:
                        archive_output_raw = (archive_output / 'execution.log').read_bytes()
                        report, _ = json.JSONDecoder().raw_decode(archive_output_raw.decode('utf-8').lstrip())
                        require(isinstance(report, dict) and report.get('experiment_id') == ident
                                and report.get('candidate_commit') == binding.candidate_sha
                                and report.get('manifest_sha256') == binding.manifest_sha, 'Evidence archive result binding mismatch')
                        if code == 0:
                            require(report.get('status') == 'ELIGIBLE_FOR_HUMAN_REVIEW', 'Evidence archive has no passing report')
                            archive_report = report
                        else:
                            performance = report.get('performance')
                            with evidence.open('rb') as original_evidence:
                                evidence_sha256 = hashlib.file_digest(original_evidence, 'sha256').hexdigest()
                            require(report.get('status') == 'EVALUATED_NEGATIVE_GATE'
                                    and report.get('baseline_id') == manifest['baseline_id']
                                    and report.get('evidence_sha256') == evidence_sha256
                                    and isinstance(performance, dict)
                                    and performance.get('experiment_id') == ident
                                    and performance.get('manifest_sha256') == binding.manifest_sha
                                    and performance.get('status') in ('FAIL', 'INCONCLUSIVE'),
                                    'Managed archive has no matching evaluated negative gate')
                            failure = 'Performance evidence is ' + performance['status']
                            negative_gate = {'report': report,
                                             'archive_output_sha256': hashlib.sha256(archive_output_raw).hexdigest()}
                if failure:
                    failure_path = folder / 'failure-evidence.json'
                    negative_evidence = {'binding': asdict(binding), 'status': 'FAIL', 'reason': failure,
                                         'run_log_sha256': hashlib.sha256((output / 'execution.log').read_bytes()).hexdigest()}
                    if negative_gate is not None:
                        negative_evidence['evaluated_negative_gate'] = negative_gate
                    write(failure_path, negative_evidence)
                    evidence_sha = hashlib.sha256(failure_path.read_bytes()).hexdigest()
                    summary = failure
                else:
                    evidence_sha = archive_report['evidence_sha256']
                    summary = 'Immutable evidence passed; awaiting local operator approval for an integration/revalidation ticket'
                gate = {'binding': asdict(binding), 'manifest_sha256': binding.manifest_sha, 'passed': failure is None,
                        'evidence_sha256': evidence_sha, 'summary': summary, 'archive_report': archive_report}
                gate_path = folder / 'gate-report.json'
                write(gate_path, gate)
                if track_full is not None:
                    run_id = track_full(record, folder, manifest, gate, archive_output_raw)
                else:
                    run_id = track(record, folder, manifest, gate)
                gate_reference = {'report': str(gate_path), 'report_sha256': hashlib.sha256(gate_path.read_bytes()).hexdigest(),
                                  'mlflow_run_id': run_id}
                state, detail = 'SUCCEEDED', summary
        except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
            state, detail = ('CANCELLED' if fence.exists() else 'FAILED'), f'{type(error).__name__}: {error}'
        if fence.exists(): state, detail = 'CANCELLED', 'Cancellation fence observed; no release allowed'
        result = {'binding': asdict(binding), 'job_id': record['job_id'], 'state': state,
                  'detail': detail, 'gate': gate_reference, 'screen': screen_reference}
        write(folder / 'result.json', result)
        if state not in ('SUCCEEDED', 'SCREEN_COMPLETED') or gate_reference and not read(gate_reference['report'])['passed']:
            write(TRAINING / 'negative-results' / (ident + '.json'),
                  {'project': record['runner']['project'], 'experiment_id': ident, 'binding': asdict(binding),
                   'state': state, 'detail': detail, 'result': str(folder / 'result.json')})
        return result
