"""Preview baseline content and delegate its single-file publication to native init."""

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


def main() -> None:
    from agent_platform.core import Blocked
    from harness.git_scope import _run_git
    import perfctl

    try:
        payload = json.load(sys.stdin)
        context = _TrainingProject(payload)
        context.registration()
        baseline = payload['baseline']
        if not isinstance(baseline, dict):
            raise ValueError('Baseline must be a JSON object')
        _validate_training_baseline(baseline)
        # Match the native writer, so an accepted document can be read back by
        # the existing bounded readers. This is not the content confirmation SHA.
        raw = (json.dumps(baseline, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        if len(raw) > 1_048_576:
            raise ValueError('Baseline exceeds the native 1 MiB read capacity')
        digest = context.sha(baseline)
        operation = payload['operation']
        if operation not in ('preview-baseline', 'init-baseline'):
            raise ValueError('Unsupported native training setup operation')
        if operation == 'init-baseline' and payload['baseline_sha256'] != digest:
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
                # This is the same publisher used by native training init.
                # Its lock checks again that another coordinator did not init.
                context.adapter.safe_file(context.root, str(target.parent.relative_to(context.root) / '.registry.lock'))
                with redirect_stdout(io.StringIO()):
                    if existing_raw is None:
                        perfctl.main(['--root', str(target.parent), 'init', '--baseline', str(source)])
                existing_raw = context.adapter.read_raw(target)
                existing = json.loads(existing_raw)
                if context.sha(existing) != digest:
                    raise ValueError('Published baseline differs from the confirmed content; read the original registry')
                status = 'initialized' if status == 'not_initialized' else status
        print(json.dumps({'project': context.project['id'], 'project_revision': context.project['revision'],
                          'status': status, 'baseline': baseline, 'baseline_sha256': digest,
                          'current_baseline': existing,
                          'current_baseline_file_sha256': hashlib.sha256(existing_raw).hexdigest() if existing_raw is not None else None,
                          'runtime_status': 'not_queried', 'execution_success': None},
                         ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked, subprocess.SubprocessError) as error:
        raise SystemExit('BLOCKED: ' + str(error))
