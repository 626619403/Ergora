"""Project-bound native runner publication never executes or overwrites an argv."""

from concurrent.futures import ThreadPoolExecutor
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

pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Native runner registration requires Linux/WSL2')


@pytest.fixture
def runner_project(registration, tmp_path):
    pytest.importorskip('temporalio')
    state, definition = registration
    registrations.register(state, definition, 0)
    marker = tmp_path / 'must-not-execute'
    runner = {'schema_version': 1, 'runner_template_id': 'demo-training', 'project': 'demo',
              'repo': definition['repo'] + '/.',
              'command': [sys.executable, '-c', f'from pathlib import Path;Path({str(marker)!r}).touch()',
                          '{manifest}', '{output}'], 'timeout_seconds': 300}
    return state, definition, runner, marker


def test_preview_normalizes_with_original_owner_and_same_content_keeps_bytes(runner_project):
    state, definition, runner, marker = runner_project
    config = Path(definition['execution']['config_directory'])
    before = {p: p.read_bytes() for p in config.rglob('*') if p.is_file()}
    project = state.project('demo')
    preview = training.preview_runner(state, 'demo', runner)
    assert preview['status'] == 'not_registered' and preview['runner']['repo'] == definition['repo']
    assert preview['current_runner'] is None and preview['execution_success'] is None
    assert {p: p.read_bytes() for p in config.rglob('*') if p.is_file()} == before
    result = training.register_runner(state, 'demo', runner, preview['project_revision'], preview['runner_sha256'])
    path = config / 'training-runners/demo-training.json'
    raw = path.read_bytes()
    assert result['status'] == 'registered' and result['current_runner'] == preview['runner']
    assert result['current_runner_file_sha256'] == hashlib.sha256(raw).hexdigest()
    canonical = dict(reversed(list(preview['runner'].items())))
    retried = training.register_runner(state, 'demo', canonical, preview['project_revision'], preview['runner_sha256'])
    assert retried['status'] == 'already_registered' and path.read_bytes() == raw
    assert not marker.exists() and not Path(definition['execution']['state_directory']).exists()
    assert state.project('demo') == project


def test_wrong_sha_stale_revision_and_changed_command_never_replace_runner(runner_project):
    state, definition, runner, _ = runner_project
    preview = training.preview_runner(state, 'demo', runner)
    path = Path(definition['execution']['config_directory']) / 'training-runners/demo-training.json'
    with pytest.raises(ValueError, match='exact previewed runner'):
        training.register_runner(state, 'demo', runner, preview['project_revision'], '0' * 64)
    assert not path.exists()
    projects.bind(state, 'demo', 'memory', {'tool': 'sqlite'}, preview['project_revision'])
    with pytest.raises(ValueError, match='revision changed'):
        training.register_runner(state, 'demo', runner, preview['project_revision'], preview['runner_sha256'])
    assert not path.exists()
    fresh = training.preview_runner(state, 'demo', runner)
    training.register_runner(state, 'demo', runner, fresh['project_revision'], fresh['runner_sha256'])
    raw = path.read_bytes()
    changed = {**runner, 'command': ['new-reviewed-command', '{manifest}', '{output}']}
    conflict = training.preview_runner(state, 'demo', changed)
    assert conflict['status'] == 'conflict' and conflict['current_runner'] == fresh['runner']
    with pytest.raises(ValueError, match='new reviewed runner ID'):
        training.register_runner(state, 'demo', changed, fresh['project_revision'], conflict['runner_sha256'])
    assert path.read_bytes() == raw


def test_lost_reply_and_concurrent_same_content_recover_original_file(runner_project, monkeypatch):
    state, definition, runner, marker = runner_project
    preview = training.preview_runner(state, 'demo', runner)
    original = reference.processes.run

    def lose_reply(*args, **kwargs):
        result = original(*args, **kwargs)
        assert result['status'] == 'succeeded'
        raise ValueError('Reply lost after native runner publication')

    monkeypatch.setattr(reference.processes, 'run', lose_reply)
    with pytest.raises(ValueError, match='Reply lost'):
        training.register_runner(state, 'demo', runner, preview['project_revision'], preview['runner_sha256'])
    monkeypatch.setattr(reference.processes, 'run', original)
    path = Path(definition['execution']['config_directory']) / 'training-runners/demo-training.json'
    raw = path.read_bytes()
    observed = training.preview_runner(state, 'demo', runner)
    assert observed['status'] == 'already_registered' and observed['current_runner'] == preview['runner']
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: training.register_runner(state, 'demo', runner, preview['project_revision'],
                                                                  preview['runner_sha256']), range(2)))
    assert all(result['status'] == 'already_registered' for result in results)
    assert path.read_bytes() == raw and not marker.exists()


def test_shared_config_rejects_foreign_runner_without_disclosing_command(runner_project):
    state, definition, runner, _ = runner_project
    preview = training.preview_runner(state, 'demo', runner)
    training.register_runner(state, 'demo', runner, preview['project_revision'], preview['runner_sha256'])
    other = deepcopy(definition)
    other.update(id='other', tracker={'kind': 'local', 'project': 'local/other'})
    registrations.register(state, other, 0)
    path = Path(definition['execution']['config_directory']) / 'training-runners/demo-training.json'
    raw = path.read_bytes()
    foreign = {**runner, 'project': 'other'}
    with pytest.raises(ValueError, match='occupied outside the selected project') as error:
        training.preview_runner(state, 'other', foreign)
    assert runner['command'][2] not in str(error.value) and path.read_bytes() == raw
    with pytest.raises(ValueError, match='selected project'):
        training.preview_runner(state, 'other', runner)


def test_registered_contract_and_capacity_do_not_publish_unusable_runner(runner_project, tmp_path):
    state, definition, runner, _ = runner_project
    for changed, error in [({**runner, 'schema_version': True}, 'must be an integer'),
                           ({**runner, 'timeout_seconds': True}, 'walltime'),
                           ({**runner, 'command': ['x' * 1_048_576]}, 'exceeds the native 1 MiB'),
                           ({**runner, 'repo': str(tmp_path)}, 'registered Git repository root')]:
        with pytest.raises(ValueError, match=error):
            training.preview_runner(state, 'demo', changed)
    config = Path(definition['execution']['config_directory'])
    policy = config / 'policies/demo/scope.json'
    raw = policy.read_bytes()
    policy.write_text('{}')
    with pytest.raises(ValueError, match='configuration drift'):
        training.preview_runner(state, 'demo', runner)
    policy.write_bytes(raw)
    from ergora.cli import main

    source = tmp_path / 'padded-runner.json'
    source.write_bytes(b' ' * 1_048_576 + json.dumps(runner).encode('utf-8'))
    assert main(['--home', str(state.root), 'training', 'runner-preview', 'demo', '--runner', str(source)]) == 2
    assert not (config / 'training-runners').exists()


def test_symlinked_runner_target_does_not_write_outside_registered_config(runner_project, tmp_path):
    state, definition, runner, _ = runner_project
    preview = training.preview_runner(state, 'demo', runner)
    parent = Path(definition['execution']['config_directory']) / 'training-runners'
    parent.mkdir()
    outside = tmp_path / 'outside'
    outside.write_bytes(b'unchanged')
    (parent / 'demo-training.json').symlink_to(outside)
    with pytest.raises(ValueError, match='Path escapes trusted root|[Ss]ymlink'):
        training.register_runner(state, 'demo', runner, preview['project_revision'], preview['runner_sha256'])
    assert outside.read_bytes() == b'unchanged'


def test_cli_http_share_normalized_confirmation_and_original_publisher(runner_project, tmp_path):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.cli import main
    from ergora.web import create_app

    state, definition, runner, marker = runner_project
    path = tmp_path / 'runner.json'
    path.write_text(json.dumps(runner))
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'runner-preview', 'demo', '--runner', str(path)])
    preview = json.loads(output.getvalue())
    assert code == 0 and preview['status'] == 'not_registered'
    headers = {'Origin': 'http://127.0.0.1', 'X-Ergora-Request': '1'}
    client = TestClient(create_app(state.root), base_url=headers['Origin'], headers=headers)
    assert client.post('/api/projects/demo/training/runner-preview', json={'runner': runner}).json() == preview
    body = {'runner': runner, 'revision': preview['project_revision'], 'runner_sha256': preview['runner_sha256']}
    result = client.post('/api/projects/demo/training/register-runner', json=body)
    assert result.status_code == 200 and result.json()['status'] == 'registered'
    raw = (Path(definition['execution']['config_directory']) / 'training-runners/demo-training.json').read_bytes()
    assert client.post('/api/projects/demo/training/register-runner', json={**body, 'revision': True}).status_code == 422
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(['--home', str(state.root), 'training', 'register-runner', 'demo', '--runner', str(path),
                     '--revision', str(body['revision']), '--runner-sha256', body['runner_sha256']])
    assert code == 0 and json.loads(output.getvalue())['status'] == 'already_registered'
    assert (Path(definition['execution']['config_directory']) / 'training-runners/demo-training.json').read_bytes() == raw
    assert not marker.exists()
