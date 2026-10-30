from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
from dataclasses import asdict
import fcntl
import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlsplit, unquote
import uuid

import perfctl
from perf_temporal.adapter import ApprovalRejected, ContractViolation
from perf_temporal.client import load_experiment
from perf_temporal.models import Binding, Experiment, GateDecision, IntegrationTask, Job, Observation, ReleaseContext

from .core import CONFIG, PYTHON, STATE, UPSTREAM, git, read, require, slug, write

TRAINING = STATE / 'training'


@contextmanager
def registry_lock():
    TRAINING.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (TRAINING / 'registry.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def perf_root(project: str) -> Path:
    return TRAINING / 'projects' / slug(project) / 'perf'


def job_folder(experiment_id: str) -> Path:
    return TRAINING / 'jobs' / slug(experiment_id)


def fence_path(experiment_id: str) -> Path:
    return TRAINING / 'fences' / (slug(experiment_id) + '.json')


def binding_from(value: dict) -> Binding:
    return Binding(**value)


def exact_job(job: Job) -> dict:
    record = read(job_folder(job.binding.experiment_id) / 'request.json')
    require(job == Job(binding_from(record['experiment']['binding']), record['job_id']), 'Training job/binding mismatch')
    return record


def register_runner(source: Path) -> dict:
    value = read(source)
    require(set(value) == {'schema_version', 'runner_template_id', 'project', 'repo', 'command', 'timeout_seconds'},
            'Runner requires schema_version, runner_template_id, project, repo, command, timeout_seconds')
    require(value['schema_version'] == 1, 'Unsupported runner template')
    slug(value['runner_template_id']); slug(value['project'])
    repo = Path(value['repo']).resolve()
    require(Path(git(repo, 'rev-parse', '--show-toplevel').stdout.strip()).resolve() == repo, 'Runner must name a Git repository root')
    require(isinstance(value['command'], list) and value['command'] and all(isinstance(x, str) and x for x in value['command']), 'Runner commands use argv arrays')
    require(type(value['timeout_seconds']) is int and 1 <= value['timeout_seconds'] <= 82800, 'Runner execution walltime must be 1..82800 seconds')
    value['repo'] = str(repo)
    write(CONFIG / 'training-runners' / (value['runner_template_id'] + '.json'), value)
    return {'registered_runner': value['runner_template_id'], 'project': value['project']}


def prepare(draft_path: Path, runner_id: str, max_run_seconds: int | None) -> dict:
    draft = read(draft_path)
    perfctl.validate(draft)
    ident = slug(draft['experiment_id'])
    runner = read(CONFIG / 'training-runners' / (slug(runner_id) + '.json'))
    maximum = max_run_seconds or max(60, runner['timeout_seconds'] + 3600)
    require(60 <= maximum <= 86400 and runner['timeout_seconds'] <= maximum, 'Invalid queue-plus-run window')
    for canonical, alias in [('candidate_commit', 'candidate_sha'), ('baseline_commit', 'baseline_sha')]:
        require(alias not in draft or draft[alias] == draft[canonical], 'Conflicting commit alias: ' + alias)
        draft[alias] = draft[canonical]
    draft.update(runner_template_id=runner_id, max_run_seconds=maximum, local_project=runner['project'])
    for commit in (draft['baseline_sha'], draft['candidate_sha']): git(Path(runner['repo']), 'cat-file', '-e', commit + '^{commit}')
    root = perf_root(runner['project'])
    perfctl.baseline_ok(draft, read(root / 'baseline.json'))
    require(draft['comparison_tool_sha256'] == hashlib.sha256((UPSTREAM / 'compare_runs.py').read_bytes()).hexdigest(), 'Comparator version differs from the reviewed contract')
    path = TRAINING / 'manifests' / (ident + '.json')
    write(path, draft)
    raw = path.read_bytes()
    with registry_lock():
        target = root / 'experiments' / ident / 'manifest.json'
        if target.exists(): require(target.read_bytes() == raw, 'Experiment ID already binds another manifest')
        else:
            write(target, draft)
    binding = Binding(ident, hashlib.sha256(raw).hexdigest(), draft['candidate_sha'], draft['baseline_sha'])
    experiment = Experiment(binding, path.as_uri(), poll_seconds=30, max_run_seconds=maximum,
                            release_wait_seconds=86400, cancel_wait_seconds=60)
    experiment.validate()
    spec = TRAINING / 'specs' / (ident + '.json')
    write(spec, asdict(experiment))
    return {'experiment_id': ident, 'spec': str(spec), 'manifest': str(path),
            'manifest_sha256': binding.manifest_sha, 'started': False}


class LocalTrainingAdapter:
    async def read_manifest(self, uri: str) -> bytes:
        parts = urlsplit(uri)
        require(parts.scheme == 'file' and not parts.netloc and not parts.query and not parts.fragment, 'Only local immutable file URIs are allowed')
        path = Path(unquote(parts.path))
        require(not path.is_symlink() and path.resolve().is_relative_to((TRAINING / 'manifests').resolve()), 'Manifest is outside the local manifest store')
        require(path.stat().st_size <= 1_048_576, 'Manifest exceeds 1 MiB')
        return path.read_bytes()

    async def lookup_job(self, experiment: Experiment) -> Job | None:
        experiment.validate()
        path = job_folder(experiment.binding.experiment_id) / 'request.json'
        if not path.exists(): return None
        record = read(path)
        require(record['experiment'] == asdict(experiment), 'Experiment identity was reused with another immutable binding')
        return Job(experiment.binding, record['job_id'])

    async def create_job_if_absent(self, experiment: Experiment, manifest: bytes) -> Job:
        require(hashlib.sha256(manifest).hexdigest() == experiment.binding.manifest_sha, 'Manifest bytes changed')
        value = json.loads(manifest)
        perfctl.validate(value)
        require(value['candidate_commit'] == value['candidate_sha'] == experiment.binding.candidate_sha and
                value['baseline_commit'] == value['baseline_sha'] == experiment.binding.baseline_sha and
                value['experiment_id'] == experiment.binding.experiment_id, 'Manifest commit aliases differ from binding')
        runner = read(CONFIG / 'training-runners' / (slug(value['runner_template_id']) + '.json'))
        require(value['local_project'] == runner['project'] and value['max_run_seconds'] == experiment.max_run_seconds,
                'Runner/project/time window mismatch')
        root = perf_root(runner['project'])
        require((root / 'experiments' / experiment.binding.experiment_id / 'manifest.json').read_bytes() == manifest,
                'Manifest differs from the registered performance contract')
        perfctl.baseline_ok(value, read(root / 'baseline.json'))
        with registry_lock():
            require(not fence_path(experiment.binding.experiment_id).exists(), 'Experiment is fenced against further submission')
            existing = await self.lookup_job(experiment)
            if existing is not None: return existing
            job_id = 'local-perf-' + experiment.binding.experiment_id
            write(job_folder(experiment.binding.experiment_id) / 'request.json',
                  {'schema_version': 1, 'job_id': job_id, 'experiment': asdict(experiment), 'runner': runner})
            return Job(experiment.binding, job_id)

    async def poll_job(self, job: Job) -> Observation:
        exact_job(job)
        folder = job_folder(job.binding.experiment_id)
        if (folder / 'result.json').exists():
            result = read(folder / 'result.json')
            require(result['binding'] == asdict(job.binding) and result['job_id'] == job.job_id, 'Training result identity mismatch')
            return Observation(job, result['state'], result['detail'])
        return Observation(job, 'RUNNING' if (folder / 'started.json').exists() else 'QUEUED')

    async def collect_and_gate(self, job: Job) -> GateDecision:
        record = exact_job(job)
        result = read(job_folder(job.binding.experiment_id) / 'result.json')
        require(result['state'] == 'SUCCEEDED', 'Training job did not finish successfully')
        gate = result['gate']
        report = Path(gate['report'])
        require(hashlib.sha256(report.read_bytes()).hexdigest() == gate['report_sha256'], 'Gate report changed')
        data = read(report)
        require(data['binding'] == asdict(job.binding), 'Gate result belongs to another experiment')
        require(data['passed'] is False or data['manifest_sha256'] == job.binding.manifest_sha, 'Gate manifest mismatch')
        return GateDecision(job, data['passed'], data['evidence_sha256'], report.as_uri(), data['summary'])

    async def fence_and_lookup(self, experiment: Experiment) -> Job | None:
        with registry_lock():
            existing = await self.lookup_job(experiment)
            write(fence_path(experiment.binding.experiment_id), {'binding': asdict(experiment.binding)})
            return existing

    async def cancel_job_group(self, job: Job) -> None:
        exact_job(job)
        write(fence_path(job.binding.experiment_id), {'binding': asdict(job.binding)})

    async def authorize_release_and_create_task(self, context: ReleaseContext) -> IntegrationTask:
        job = context.gate.job
        record = exact_job(job)
        require(context.experiment.binding == job.binding == context.request.binding, 'Release binding mismatch')
        require(context.gate.passed and context.request.evidence_sha == context.gate.evidence_sha, 'Release evidence mismatch')
        current_gate = await self.collect_and_gate(job)
        require(current_gate == context.gate, 'Release gate differs from archived evidence')
        manifest = json.loads(await self.read_manifest(context.experiment.manifest_uri))
        try: perfctl.baseline_ok(manifest, read(perf_root(record['runner']['project']) / 'baseline.json'))
        except perfctl.Invalid as error: raise ContractViolation(str(error)) from error
        receipt_id = slug(context.request.approval_receipt_id)
        try:
            path = TRAINING / 'approvals' / (receipt_id + '.json')
            require(path.stat().st_uid == os.getuid() and not path.stat().st_mode & 0o077, 'Approval must be private and owned by the operator')
            approval = read(path)
            require(approval['binding'] == asdict(job.binding) and approval['evidence_sha256'] == context.gate.evidence_sha,
                    'Approval binding/evidence mismatch')
            require(approval['decision'] == 'approve' and approval['role'] == 'owner' and
                    approval['actor_id'] == f'unix:{os.getuid()}:{getpass.getuser()}' and
                    not approval['revoked'] and time.time() < approval['expires_at'], 'Approval identity/expiry/revocation rejected')
        except (OSError, ValueError, KeyError, RuntimeError) as error:
            raise ApprovalRejected(str(error)) from error
        ident = job.binding.experiment_id + '-' + context.gate.evidence_sha[:16]
        target = TRAINING / 'integration-tickets' / (ident + '.json')
        with registry_lock():
            require(not fence_path(job.binding.experiment_id).exists(), 'Release suppressed by cancellation fence')
            write(target, {'schema_version': 1, 'kind': 'local-integration-revalidation', 'project': record['runner']['project'],
                           'binding': asdict(job.binding), 'evidence_sha256': context.gate.evidence_sha,
                           'approval_receipt_id': receipt_id, 'automatic_merge': False})
        return IntegrationTask(job.binding, ident, target.as_uri())


def create_adapter():
    return LocalTrainingAdapter()


def cli(arguments: list[str]):
    parser = argparse.ArgumentParser(prog='agentflow training')
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('init'); init.add_argument('--project', required=True); init.add_argument('--baseline', type=Path, required=True)
    add = sub.add_parser('runner-add'); add.add_argument('file', type=Path)
    prep = sub.add_parser('prepare'); prep.add_argument('manifest', type=Path); prep.add_argument('--runner', required=True)
    prep.add_argument('--max-run-seconds', type=int)
    run = sub.add_parser('run-local', help='手动执行一个已排队且精确绑定的可信实验')
    run.add_argument('experiment_id'); run.add_argument('--confirm-manifest-sha', required=True)
    sub.add_parser('worker-start'); sub.add_parser('worker-stop')
    for operation in ('start', 'status', 'result', 'cancel', 'approve'):
        command = sub.add_parser(operation); command.add_argument('experiment_id')
        if operation == 'cancel': command.add_argument('--reason', required=True)
        if operation == 'approve': command.add_argument('--evidence-sha', required=True)
    args = parser.parse_args(arguments)
    if args.action == 'init':
        root = perf_root(args.project)
        if (root / 'baseline.json').exists():
            require(read(root / 'baseline.json') == read(args.baseline), 'Baseline already exists; use a reviewed baseline migration')
        else:
            subprocess.run([str(PYTHON), str(UPSTREAM / 'perfctl.py'), '--root', str(root), 'init', '--baseline', str(args.baseline)], check=True, timeout=10)
        return {'project': args.project, 'registry': str(root)}
    if args.action == 'runner-add': return register_runner(args.file)
    if args.action == 'prepare': return prepare(args.manifest, args.runner, args.max_run_seconds)
    if args.action in {'worker-start', 'worker-stop'}:
        from .cli import supervisor
        supervisor('reread'); supervisor('update')
        require(supervisor('start' if args.action == 'worker-start' else 'stop', 'training-worker') == 0,
                'Training control worker operation failed')
        return {'training_control_worker': args.action, 'automatic_training_execution': False}
    spec = TRAINING / 'specs' / (slug(args.experiment_id) + '.json')
    if args.action == 'run-local':
        experiment = load_experiment(str(spec))
        require(args.confirm_manifest_sha == experiment.binding.manifest_sha, 'Confirm the exact immutable manifest SHA before execution')
        request = job_folder(args.experiment_id) / 'request.json'
        require(request.exists(), 'Start the control workflow first and wait for its queued job request')
        from .training_executor import process
        return process(request.parent)
    tail = []
    operation = args.action
    if operation == 'cancel': tail = ['--reason', args.reason]
    if operation == 'approve':
        import re
        require(re.fullmatch('[a-f0-9]{64}', args.evidence_sha), 'Expected exact evidence SHA-256')
        experiment = load_experiment(str(spec))
        async def check_phase():
            from perf_temporal.connection import connect
            from perf_temporal.models import workflow_id
            from perf_temporal.workflow import ExperimentWorkflow
            handle = (await connect()).get_workflow_handle(workflow_id(experiment.binding))
            status = await handle.query(ExperimentWorkflow.status)
            require(status.phase == 'AWAITING_RELEASE' and status.binding == experiment.binding and status.evidence_sha == args.evidence_sha,
                    'Approval must name the exact evidence currently awaiting release')
        asyncio.run(check_phase())
        receipt_id = 'owner-' + uuid.uuid4().hex
        write(TRAINING / 'approvals' / (receipt_id + '.json'), {'binding': asdict(experiment.binding),
              'evidence_sha256': args.evidence_sha, 'decision': 'approve', 'role': 'owner',
              'actor_id': f'unix:{os.getuid()}:{getpass.getuser()}', 'expires_at': time.time() + 86400, 'revoked': False})
        operation = 'release'; tail = ['--receipt-id', receipt_id, '--evidence-sha', args.evidence_sha]
    from .core import environment
    process = subprocess.run([str(PYTHON), '-m', 'perf_temporal.client', operation, str(spec), *tail], env=environment())
    require(process.returncode == 0, 'Training operation failed; inspect worker logs and the exact experiment identity')
    return None
