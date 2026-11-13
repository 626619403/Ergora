"""Preview setup documents and delegate immutable publication to their native owners."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from .reference import _validate_training_baseline
from .reference_training_context import _TrainingProject


def _native_bytes(value: dict, name: str) -> bytes:
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if len(raw) > 1_048_576:
        raise ValueError(name + ' exceeds the native 1 MiB read capacity')
    return raw


def _baseline(context: _TrainingProject) -> dict:
    from harness.git_scope import _run_git
    import perfctl

    baseline = context.payload['baseline']
    if not isinstance(baseline, dict):
        raise ValueError('Baseline must be a JSON object')
    _validate_training_baseline(baseline)
    raw = _native_bytes(baseline, 'Baseline')
    digest = context.sha(baseline)
    operation = context.payload['operation']
    if operation == 'init-baseline' and context.payload['baseline_sha256'] != digest:
        raise ValueError('Confirm the exact previewed baseline content SHA-256')
    relative = 'training/projects/' + context.core.slug(context.project['id']) + '/perf/baseline.json'
    target = context.adapter.safe_file(context.root, relative)
    with TemporaryDirectory(prefix='ergora-baseline-preview-') as temporary:
        source = Path(temporary) / 'baseline.json'
        source.write_bytes(raw)
        repo = Path(context.project['repo'])
        if Path(_run_git(repo, 'rev-parse', '--show-toplevel')[1].decode('utf-8').strip()).resolve() != repo:
            raise ValueError('Baseline must retain the registered Git repository root')
        _run_git(repo, 'cat-file', '-e', baseline['commit'] + '^{commit}')
        try:
            existing_raw = context.adapter.read_raw(target)
        except FileNotFoundError:
            existing_raw = None
        existing = json.loads(existing_raw) if existing_raw is not None else None
        current_sha = context.sha(existing) if existing_raw is not None else None
        status = 'not_initialized' if existing_raw is None else 'already_initialized' if current_sha == digest else 'conflict'
        if operation == 'init-baseline':
            if status == 'conflict':
                raise ValueError('Baseline already exists with different content; use a reviewed baseline migration')
            # The original publisher retains its lock and concurrent-init check.
            context.adapter.safe_file(context.root, str(target.parent.relative_to(context.root) / '.registry.lock'))
            with redirect_stdout(io.StringIO()):
                if existing_raw is None:
                    perfctl.main(['--root', str(target.parent), 'init', '--baseline', str(source)])
            existing_raw = context.adapter.read_raw(target)
            existing = json.loads(existing_raw)
            if context.sha(existing) != digest:
                raise ValueError('Published baseline differs from the confirmed content; read the original registry')
            status = 'initialized' if status == 'not_initialized' else status
    return {'status': status, 'baseline': baseline, 'baseline_sha256': digest,
            'current_baseline': existing,
            'current_baseline_file_sha256': hashlib.sha256(existing_raw).hexdigest() if existing_raw is not None else None}


def _runner(context: _TrainingProject) -> dict:
    from agent_platform import training as native

    runner = context.payload['runner']
    if not isinstance(runner, dict):
        raise ValueError('Runner must be a JSON object')
    if runner.get('project') != context.project['id'] or Path(runner['repo']).resolve() != Path(context.project['repo']):
        raise ValueError('Runner must retain the selected project and registered Git repository root')
    # Native registration accepts True == 1, but formal submission requires an
    # integer. Do not register a document that the actual consumer cannot use.
    if type(runner.get('schema_version')) is not int:
        raise ValueError('Runner schema_version must be an integer')
    with TemporaryDirectory(prefix='ergora-runner-preview-') as temporary:
        source = Path(temporary) / 'runner.json'
        source.write_bytes(_native_bytes(runner, 'Runner'))
        config = native.CONFIG
        try:
            # The native validator and serializer have no preview mode. Only
            # this isolated subprocess sees the temporary configuration root.
            native.CONFIG = Path(temporary) / 'config'
            native.register_runner(source)
            relative = 'training-runners/' + runner['runner_template_id'] + '.json'
            normalized = context.document(native.CONFIG, relative)
        finally:
            native.CONFIG = config
        digest = context.sha(normalized)
        if context.payload['operation'] == 'register-runner' and context.payload['runner_sha256'] != digest:
            raise ValueError('Confirm the exact previewed runner content SHA-256')
        target = context.adapter.safe_file(context.config, relative)
        try:
            existing_raw = context.adapter.read_raw(target)
        except FileNotFoundError:
            existing_raw = None
        existing = json.loads(existing_raw) if existing_raw is not None else None
        if existing_raw is not None and (not isinstance(existing, dict) or existing.get('project') != context.project['id']
                                        or existing.get('repo') != context.project['repo']):
            raise ValueError('Runner ID is occupied outside the selected project; choose a project-specific ID')
        current_sha = context.sha(existing) if existing_raw is not None else None
        status = 'not_registered' if existing_raw is None else 'already_registered' if current_sha == digest else 'conflict'
        if context.payload['operation'] == 'register-runner':
            if status == 'conflict':
                raise ValueError('Runner ID already exists with different content; choose a new reviewed runner ID')
            # Publish the resolved document, not a repo alias that could change
            # between validation and the native immutable writer's second read.
            source.write_bytes(_native_bytes(normalized, 'Runner'))
            native.register_runner(source)
            existing_raw = context.adapter.read_raw(target)
            existing = json.loads(existing_raw)
            if context.sha(existing) != digest:
                raise ValueError('Published runner differs from the confirmed content; read the original registry')
            status = 'registered' if status == 'not_registered' else status
    return {'status': status, 'runner': normalized, 'runner_sha256': digest, 'current_runner': existing,
            'current_runner_file_sha256': hashlib.sha256(existing_raw).hexdigest() if existing_raw is not None else None}


def main() -> None:
    from agent_platform.core import Blocked

    try:
        payload = json.load(sys.stdin)
        context = _TrainingProject(payload)
        context.registration()
        operation = payload['operation']
        if operation in ('preview-baseline', 'init-baseline'):
            result = _baseline(context)
        elif operation in ('preview-runner', 'register-runner'):
            result = _runner(context)
        else:
            raise ValueError('Unsupported native training setup operation')
        print(json.dumps({'project': context.project['id'], 'project_revision': context.project['revision'],
                          **result,
                          'runtime_status': 'not_queried', 'execution_success': None},
                         ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked, subprocess.SubprocessError) as error:
        raise SystemExit('BLOCKED: ' + str(error))
