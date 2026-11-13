"""One native baseline, with exact content confirmation and recoverable local publication."""

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys

import pytest

from ergora import projects, reference, registrations, training
from test_registrations import registration
from test_training_runtime import installation


@pytest.fixture
def baseline_project(registration):
    state, definition = registration
    registered = registrations.register(state, definition, 0)
    baseline = {'baseline_id': 'real-local-commit', 'commit': registered['registration']['definition']['base_sha'],
                'config_sha256': 'a' * 64, 'workload_fingerprint': 'b' * 64,
                'evidence_uri': 'synthetic:baseline-control-only', 'quality_scope': 'No training or GPU run'}
    return state, definition, baseline


def test_sdk_free_preview_and_confirmed_init_keep_original_baseline(baseline_project, monkeypatch):
    state, definition, baseline = baseline_project
    original = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    runtime = Path(definition['execution']['state_directory'])
    before = state.project('demo')
    preview = training.preview_baseline(state, 'demo', baseline)
    assert preview['status'] == 'not_initialized' and preview['runtime_status'] == 'not_queried'
    assert preview['current_baseline'] is None and not runtime.exists()
    if sys.platform != 'linux':
        with pytest.raises(ValueError, match='Linux'):
            training.initialize_baseline(state, 'demo', baseline, before['revision'], preview['baseline_sha256'])
        return
    result = training.initialize_baseline(state, 'demo', baseline, before['revision'], preview['baseline_sha256'])
    path = runtime / 'training/projects/demo/perf/baseline.json'
    original_raw = path.read_bytes()
    assert result['status'] == 'initialized' and result['execution_success'] is None
    assert result['current_baseline'] == baseline and json.loads(original_raw) == baseline
    assert result['current_baseline_file_sha256'] == hashlib.sha256(original_raw).hexdigest()
    # Content confirmation ignores JSON order; recorded byte SHA is separate.
    reordered = dict(reversed(list(baseline.items())))
    assert training.preview_baseline(state, 'demo', reordered)['baseline_sha256'] == preview['baseline_sha256']
    assert training.initialize_baseline(state, 'demo', reordered, before['revision'], preview['baseline_sha256'])['status'] == 'already_initialized'
    assert training.inspect(state, 'demo')['baseline'] == baseline and path.read_bytes() == original_raw
    assert state.project('demo') == before
    assert not (runtime / 'training/specs').exists() and not (runtime / 'training/jobs').exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Native baseline publication uses the Linux/WSL2 owner')
def test_lost_reply_can_reread_and_retry_without_another_baseline(baseline_project, monkeypatch):
    state, definition, baseline = baseline_project
    preview = training.preview_baseline(state, 'demo', baseline)
    original = reference.processes.run

    def lose_reply(*args, **kwargs):
        result = original(*args, **kwargs)
        assert result['status'] == 'succeeded'
        raise ValueError('Reply lost after the actual original publisher finished')

    monkeypatch.setattr(reference.processes, 'run', lose_reply)
    with pytest.raises(ValueError, match='Reply lost'):
        training.initialize_baseline(state, 'demo', baseline, preview['project_revision'], preview['baseline_sha256'])
    monkeypatch.setattr(reference.processes, 'run', original)
    path = Path(definition['execution']['state_directory']) / 'training/projects/demo/perf/baseline.json'
    before = path.read_bytes()
    assert training.inspect(state, 'demo')['baseline'] == baseline
    recovered = training.initialize_baseline(state, 'demo', baseline, preview['project_revision'], preview['baseline_sha256'])
    assert recovered['status'] == 'already_initialized' and path.read_bytes() == before


@pytest.mark.skipif(sys.platform != 'linux', reason='Native baseline publication uses the Linux/WSL2 owner')
def test_wrong_confirmation_stale_revision_and_different_existing_baseline_do_not_publish(baseline_project):
    state, definition, baseline = baseline_project
    runtime = Path(definition['execution']['state_directory'])
    preview = training.preview_baseline(state, 'demo', baseline)
    with pytest.raises(ValueError, match='exact previewed baseline'):
        training.initialize_baseline(state, 'demo', baseline, preview['project_revision'], '0' * 64)
    assert not runtime.exists()
    projects.bind(state, 'demo', 'memory', {'tool': 'sqlite'}, preview['project_revision'])
    with pytest.raises(ValueError, match='revision changed'):
        training.initialize_baseline(state, 'demo', baseline, preview['project_revision'], preview['baseline_sha256'])
    assert not runtime.exists()
    fresh = training.preview_baseline(state, 'demo', baseline)
    training.initialize_baseline(state, 'demo', baseline, fresh['project_revision'], fresh['baseline_sha256'])
    before = {p: p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    changed = {**baseline, 'quality_scope': 'Changed full baseline, same identifying fields'}
    conflict = training.preview_baseline(state, 'demo', changed)
    assert conflict['status'] == 'conflict' and conflict['current_baseline'] == baseline
    with pytest.raises(ValueError, match='reviewed baseline migration'):
        training.initialize_baseline(state, 'demo', changed, fresh['project_revision'], conflict['baseline_sha256'])
    assert all(path.read_bytes() == raw for path, raw in before.items())


def test_baseline_setup_keeps_registration_git_root_and_read_capacity(baseline_project, tmp_path):
    state, definition, baseline = baseline_project
    runtime = Path(definition['execution']['state_directory'])
    config = Path(definition['execution']['config_directory'])
    policy = config / 'policies/demo/scope.json'
    original = policy.read_bytes()
    policy.write_text('{}')
    with pytest.raises(ValueError, match='configuration drift'):
        training.preview_baseline(state, 'demo', baseline)
    policy.write_bytes(original)
    with pytest.raises(ValueError, match='exceeds the native 1 MiB'):
        training.preview_baseline(state, 'demo', {**baseline, 'notes': 'x' * 1_048_576})
    with pytest.raises(ValueError, match='Git verification failed'):
        training.preview_baseline(state, 'demo', {**baseline, 'commit': '0' * 40})
    from ergora.cli import main

    source = tmp_path / 'padded-baseline.json'
    source.write_bytes(b' ' * 1_048_576 + json.dumps(baseline).encode('utf-8'))
    # Raw source capacity applies before parsing, even if JSON whitespace would
    # disappear during canonicalization and the parsed object is small.
    assert main(['--home', str(state.root), 'training', 'baseline-preview', 'demo', '--baseline', str(source)]) == 2
    assert not runtime.exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Native baseline publication uses the Linux/WSL2 owner')
def test_project_bound_baselines_do_not_share_records_and_reject_symlinked_lock(baseline_project, tmp_path):
    state, definition, baseline = baseline_project
    other = deepcopy(definition)
    other.update(id='other', tracker={'kind': 'local', 'project': 'local/other'})
    registrations.register(state, other, 0)
    preview = training.preview_baseline(state, 'demo', baseline)
    prefix = Path(definition['execution']['state_directory']) / 'training/projects/demo/perf'
    prefix.mkdir(parents=True)
    outside = tmp_path / 'outside'
    outside.write_bytes(b'unchanged')
    (prefix / '.registry.lock').symlink_to(outside)
    with pytest.raises(ValueError, match='Path escapes trusted root|[Ss]ymlink'):
        training.initialize_baseline(state, 'demo', baseline, preview['project_revision'], preview['baseline_sha256'])
    assert outside.read_bytes() == b'unchanged' and not (prefix / 'baseline.json').exists()
    (prefix / '.registry.lock').unlink()
    training.initialize_baseline(state, 'demo', baseline, preview['project_revision'], preview['baseline_sha256'])
    assert training.inspect(state, 'other')['baseline'] is None


@pytest.mark.skipif(sys.platform != 'linux', reason='Native baseline publication uses the Linux/WSL2 owner')
def test_cli_and_http_share_original_publication_and_content_sha(baseline_project, tmp_path):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.cli import main
    from ergora.web import create_app

    state, _, baseline = baseline_project
    path = tmp_path / 'baseline.json'
    path.write_text(json.dumps(baseline))
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'baseline-preview', 'demo', '--baseline', str(path)])
    preview = json.loads(output.getvalue())
    assert code == 0 and preview['status'] == 'not_initialized'
    headers = {'Origin': 'http://127.0.0.1', 'X-Ergora-Request': '1'}
    client = TestClient(create_app(state.root), base_url=headers['Origin'], headers=headers)
    body = {'baseline': baseline, 'revision': preview['project_revision'], 'baseline_sha256': preview['baseline_sha256']}
    assert client.post('/api/projects/demo/training/baseline-preview', json={'baseline': baseline}).json() == preview
    initialized = client.post('/api/projects/demo/training/init-baseline', json=body)
    assert initialized.status_code == 200 and initialized.json()['status'] == 'initialized'
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'init-baseline', 'demo', '--baseline', str(path),
                     '--revision', str(body['revision']), '--baseline-sha256', body['baseline_sha256']])
    assert code == 0 and json.loads(output.getvalue())['status'] == 'already_initialized'
