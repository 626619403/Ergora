"""Run-bound candidate export preserves Git, native evidence and uncertain writes."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import pytest

from ergora import projects, reference, tasks
from ergora.state import State
from test_registrations import installation, registration
from test_task_creation import creation_project, _files
from test_task_submission import native_client, _start, _root, _calls


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal task operations use Linux/WSL2')


def git(repo, *args, stdin=None, check=True):
    env = dict(os.environ, GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.test',
               GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.test')
    return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args],
                          input=stdin, check=check, env=env, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def export_task(creation_project, native_client, request):
    if sys.platform != 'linux':
        pytest.skip('Formal export uses the Linux reference runtime')
    pytest.importorskip('temporalio')
    state, registration, definition = creation_project
    template = getattr(request, 'param', 'repository-governance')
    definition['task_type'] = template
    definition['input']['risk'] = 'high' if template == 'large-change' else 'standard'
    interpreter = Path(registration['execution']['installation']) / '.venv'
    if not interpreter.exists():
        interpreter.symlink_to(sys.prefix, target_is_directory=True)
    preview = tasks.preview(state, 'demo', definition, 1)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'])
    creation = state, registration, definition, created
    _start(creation)
    root = _root(creation)
    source = root / 'workspaces/new-task/repo.git'
    source.parent.mkdir(parents=True)
    git(root, 'clone', '--bare', registration['repo'], str(source))
    base = git(source, 'rev-parse', 'HEAD')
    tree = git(source, 'mktree', stdin='')
    candidate = git(source, 'commit-tree', tree, '-p', base, stdin='Candidate\n')
    spec = json.loads((root / 'sdk-fixture/server.json').read_text())['spec']
    outcome = {'status': 'REVIEW_READY', 'task_id': 'new-task', 'task_type': template,
               'request_sha256': spec['request_sha256'], 'profile_sha256': spec['profile_sha256'],
               'base_sha': base, 'candidate_sha': candidate, 'fixture_evidence': 'original-result'}
    (root / 'sdk-fixture/outcome.json').write_text(json.dumps(outcome))
    return creation


@pytest.fixture
def export_client(export_task, monkeypatch):
    original = reference.subprocess.run
    fixture = Path(__file__).parent / 'fixtures/task_export_client.py'
    def invoke(argv, **kwargs):
        if 'from ergora.reference_task_export import main;main()' in argv:
            argv = [*argv[:-1], fixture.read_text(encoding='utf-8')]
        return original(argv, **kwargs)
    monkeypatch.setattr(reference.subprocess, 'run', invoke)


def outcome(creation):
    return json.loads((_root(creation) / 'sdk-fixture/outcome.json').read_text())


def export(creation, revision=1, **kwargs):
    return tasks.export(creation[0], 'demo', 'new-task', revision,
                        **{'run_id': 'original-run', 'candidate_sha': outcome(creation)['candidate_sha'],
                           'branch': 'agent/exported', 'confirm': True, **kwargs})


def status(creation):
    return tasks.export_status(State(creation[0].root), 'demo', 'new-task')


def resume(creation, revision=1, **kwargs):
    return tasks.resume_export(State(creation[0].root), 'demo', 'new-task', revision,
                               status(creation)['intent_sha256'], confirm=True, **kwargs)


def lease(creation):
    with closing(sqlite3.connect(_root(creation) / 'ingress/leases.sqlite3')) as db:
        return db.execute('SELECT released_at, evidence_digest FROM claims').fetchone(), db.execute('SELECT count(*) FROM active').fetchone()[0]


@pytest.mark.parametrize('export_task', ['repository-governance', 'large-change'], indirect=True)
def test_exact_candidate_is_exported_once_with_original_native_receipt_and_lease(export_task, export_client):
    repo = Path(export_task[1]['repo'])
    (repo / 'untracked.txt').write_text('User work\n')
    git(repo, 'symbolic-ref', 'HEAD')
    before = git(repo, 'status', '--porcelain'), git(repo, 'rev-parse', 'HEAD')
    native = _root(export_task) / 'tasks/new-task'
    original = {p.name: p.read_bytes() for p in native.iterdir()}
    assert status(export_task)['status'] == 'not_recorded' and lease(export_task)[1] == 1
    result = export(export_task)
    assert result['status'] == 'exported' and result['lease_released'] is True
    assert result['candidate_sha'] == git(repo, 'rev-parse', 'refs/heads/agent/exported')
    assert result['run_id'] == 'original-run' and result['execution_success'] is None
    assert result['checked_out'] is False and result['merged'] is False
    assert json.loads((native / 'export.json').read_text()) == {
        'candidate_sha': result['candidate_sha'], 'repo': str(repo), 'branch': 'agent/exported'}
    released, active = lease(export_task)
    digest = hashlib.sha256(json.dumps(outcome(export_task), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    assert released[0] is not None and released[1] == digest and active == 0
    assert not (repo / '.git/FETCH_HEAD').exists()
    assert (git(repo, 'status', '--porcelain'), git(repo, 'rev-parse', 'HEAD')) == before
    assert all((native / name).read_bytes() == raw for name, raw in original.items())
    calls = _calls(export_task)
    assert export(export_task) == resume(export_task) == status(export_task) == result
    assert _calls(export_task) == calls and calls.count('export-fetch') == calls.count('export-update-ref') == 1
    projects.bind(export_task[0], 'demo', 'reviewer', {'tool': 'codex', 'model': 'later'}, 1)
    assert resume(export_task, revision=2)['intent_sha256'] == result['intent_sha256']
    assert _calls(export_task) == calls


@pytest.mark.parametrize('scenario, expected', [
    ('before-intent', 'not_recorded'), ('after-intent', 'prepared'), ('before-attempt', 'prepared'),
    ('after-attempt', 'unknown'), ('before-fetch', 'unknown'), ('after-fetch', 'unknown'),
    ('before-update-ref', 'unknown'), ('after-update-ref', 'unknown'),
    ('before-native', 'unknown'), ('after-native', 'unknown'), ('before-result', 'unknown'), ('after-result', 'exported'),
])
def test_interrupted_exports_never_repeat_an_uncertain_git_write(export_task, export_client, monkeypatch, scenario, expected):
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', scenario)
    with pytest.raises(ValueError, match='Fixture'):
        export(export_task)
    current = status(export_task)
    assert current['status'] == expected
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'normal')
    before = _calls(export_task)
    if expected == 'not_recorded':
        assert 'export-connect' not in before
        assert export(export_task)['status'] == 'exported'
    elif expected == 'prepared':
        assert export(export_task) == current
        assert resume(export_task)['status'] == 'exported'
    else:
        assert export(export_task) == current
        result = resume(export_task)
        if scenario in ('after-attempt', 'before-fetch', 'after-fetch', 'before-update-ref'):
            assert result['status'] == 'unknown' and result['reconciliation'] == 'branch_not_found'
            assert lease(export_task)[1] == 1
            assert resume(export_task)['status'] == 'unknown'
        else:
            assert result['status'] == 'exported' and lease(export_task)[1] == 0
        assert _calls(export_task).count('export-fetch') == before.count('export-fetch')
        assert _calls(export_task).count('export-update-ref') == before.count('export-update-ref')


@pytest.mark.parametrize('scenario, error', [
    ('wrong-memo', 'matching submission memo'), ('wrong-spec', 'original task spec'),
    ('offline', 'offline'), ('not-found', 'Original export run was not found'),
    ('rpc-unavailable', 'RPC failed: UNAVAILABLE'), ('running', 'completed REVIEW_READY'),
    ('different-actor', 'actor changed'),
])
def test_export_requires_the_owned_original_completed_run(export_task, export_client, monkeypatch, scenario, error):
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', scenario)
    with pytest.raises(ValueError, match=error):
        export(export_task)
    assert status(export_task)['status'] == 'prepared'
    assert 'export-fetch' not in _calls(export_task) and lease(export_task)[1] == 1


@pytest.mark.parametrize('key,value', [('status', 'BLOCKED'), ('task_id', 'other'), ('task_type', 'large-change'),
    ('request_sha256', 'b' * 64), ('profile_sha256', 'b' * 64), ('base_sha', 'b' * 40), ('candidate_sha', 'b' * 40)])
def test_outcome_identity_must_match_every_original_field(export_task, export_client, key, value):
    candidate = outcome(export_task)['candidate_sha']
    changed = {**outcome(export_task), key: value}
    (_root(export_task) / 'sdk-fixture/outcome.json').write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='outcome must match'):
        export(export_task, candidate_sha=candidate)
    assert status(export_task)['status'] == 'prepared' and lease(export_task)[1] == 1


@pytest.mark.parametrize('options,error', [
    ({'run_id': 'other'}, 'original submitted run'), ({'branch': '-bad'}, 'branch'),
    ({'branch': 'bad..ref'}, 'branch'), ({'branch': '@{-1}'}, 'branch'),
    ({'confirm': False}, 'confirmation'),
])
def test_invalid_input_has_no_export_intent_or_git_effect(export_task, export_client, options, error):
    root, repo = _root(export_task), Path(export_task[1]['repo'])
    (repo / 'untracked.txt').write_text('User work\n')
    before = _files(root), _files(repo)
    with pytest.raises(ValueError, match=error):
        export(export_task, **options)
    assert (_files(root), _files(repo)) == before
    assert status(export_task)['status'] == 'not_recorded' and lease(export_task)[1] == 1
    assert 'export-connect' not in _calls(export_task)


@pytest.mark.parametrize('revision', [True, 0, '1', 2])
def test_stale_revision_cannot_reserve_an_export(export_task, export_client, revision):
    with pytest.raises(ValueError, match='revision'):
        export(export_task, revision=revision)
    assert status(export_task)['status'] == 'not_recorded'


@pytest.mark.parametrize('racing', [False, True])
def test_other_owners_branch_is_not_fast_forwarded(export_task, export_client, monkeypatch, racing):
    repo = Path(export_task[1]['repo'])
    base = outcome(export_task)['base_sha']
    if racing:
        monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'branch-race')
    else:
        git(repo, 'update-ref', 'refs/heads/agent/exported', base)
    with pytest.raises(ValueError, match='different commit|Conditional export branch creation failed'):
        export(export_task)
    assert git(repo, 'rev-parse', 'refs/heads/agent/exported') == base
    assert git(repo, 'rev-parse', 'HEAD') == base and lease(export_task)[1] == 1
    assert not (_root(export_task) / 'tasks/new-task/export.json').exists()


def test_existing_candidate_branch_needs_no_fetch_but_still_requires_verified_outcome(export_task, export_client):
    repo = Path(export_task[1]['repo'])
    source = _root(export_task) / 'workspaces/new-task/repo.git'
    git(repo, 'fetch', '--no-write-fetch-head', str(source), outcome(export_task)['candidate_sha'])
    git(repo, 'update-ref', 'refs/heads/agent/exported', outcome(export_task)['candidate_sha'])
    assert export(export_task)['status'] == 'exported'
    assert 'export-fetch' not in _calls(export_task) and 'export-result' in _calls(export_task)


def test_unknown_recovery_preserves_deleted_branch_and_drifted_outcome(export_task, export_client, monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'after-update-ref')
    with pytest.raises(ValueError):
        export(export_task)
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'normal')
    repo = Path(export_task[1]['repo'])
    git(repo, 'update-ref', '-d', 'refs/heads/agent/exported')
    assert resume(export_task)['reconciliation'] == 'branch_not_found'
    git(repo, 'update-ref', 'refs/heads/agent/exported', outcome(export_task)['base_sha'])
    with pytest.raises(ValueError, match='recovery cannot move'):
        resume(export_task)
    git(repo, 'update-ref', 'refs/heads/agent/exported', outcome(export_task)['candidate_sha'])
    raw = (_root(export_task) / 'sdk-fixture/outcome.json').read_bytes()
    changed = {**outcome(export_task), 'fixture_evidence': 'changed-result'}
    (_root(export_task) / 'sdk-fixture/outcome.json').write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='outcome changed'):
        resume(export_task)
    assert lease(export_task)[1] == 1
    (_root(export_task) / 'sdk-fixture/outcome.json').write_bytes(raw)
    assert resume(export_task)['status'] == 'exported'
    assert _calls(export_task).count('export-fetch') == _calls(export_task).count('export-update-ref') == 1


def test_native_legacy_export_is_not_implicitly_adopted(export_task, export_client):
    path = _root(export_task) / 'tasks/new-task/export.json'
    raw = b'{"legacy": true}\n'
    path.write_bytes(raw)
    with pytest.raises(ValueError, match='legacy exports cannot be adopted'):
        export(export_task)
    assert path.read_bytes() == raw and status(export_task)['status'] == 'not_recorded'


def test_remote_export_wait_does_not_reserve_the_control_database(export_task, export_client, monkeypatch):
    state = export_task[0]
    projects.create(state, 'other-project', Path(export_task[1]['repo']))
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'slow-connect')
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(export, export_task)
        deadline = time.monotonic() + 15
        while 'export-connect' not in _calls(export_task):
            assert time.monotonic() < deadline
            time.sleep(.05)
        assert projects.bind(state, 'other-project', 'memory', {'tool': 'sqlite'}, 1)['revision'] == 2
        assert not pending.done()
        with pytest.raises(ValueError, match='temporarily unavailable|locked|would block'):
            export(export_task)
        assert projects.bind(state, 'other-project', 'memory', {'tool': 'sqlite'}, 2)['revision'] == 3
        assert pending.result(timeout=15)['status'] == 'exported'


def test_cli_and_api_share_confirmed_export_and_original_digest_recovery(export_task, export_client, monkeypatch):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora import cli
    from ergora.web import create_app
    client = TestClient(create_app(export_task[0].root), base_url='http://127.0.0.1')
    uri = '/api/projects/demo/tasks/new-task/export'
    headers = {'X-Ergora-Request': '1', 'Origin': 'http://127.0.0.1'}
    body = {'revision': 1, 'run_id': 'original-run', 'candidate_sha': outcome(export_task)['candidate_sha'],
            'branch': 'agent/exported', 'confirm': True}
    assert client.post(uri, json=body).status_code == 403
    for invalid in ({'revision': True}, {'confirm': 1}, {'timeout': True}, {'candidate_sha': 'bad'}):
        assert client.post(uri, json={**body, **invalid}, headers=headers).status_code == 422
    args = ['--home', str(export_task[0].root), 'task']
    assert cli.main([*args, 'export-status', 'demo', 'new-task']) == 0
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'after-update-ref')
    assert client.post(uri, json=body, headers=headers).status_code == 400
    current = client.get(uri).json()
    assert current['status'] == 'unknown'
    assert cli.main([*args, 'export', 'demo', 'new-task', '--revision', '1', '--run-id', 'original-run',
                     '--candidate-sha', body['candidate_sha'], '--branch', body['branch'], '--confirm']) == 1
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'normal')
    restored = client.post(uri + '/resume', json={'revision': 1, 'intent_sha256': current['intent_sha256'], 'confirm': True}, headers=headers)
    assert restored.status_code == 200 and restored.json()['status'] == 'exported'
    assert cli.main([*args, 'resume-export', 'demo', 'new-task', '--revision', '1',
                     '--intent-sha256', current['intent_sha256'], '--confirm']) == 0


@pytest.mark.parametrize('racing', [False, True])
def test_dangling_symbolic_branch_is_not_replaced(export_task, export_client, monkeypatch, racing):
    repo = Path(export_task[1]['repo'])
    if racing:
        monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'branch-race-dangling')
    else:
        git(repo, 'symbolic-ref', 'refs/heads/agent/exported', 'refs/heads/missing')
    with pytest.raises(ValueError, match='symbolic|Conditional export branch creation failed'):
        export(export_task)
    assert git(repo, 'symbolic-ref', 'refs/heads/agent/exported') == 'refs/heads/missing'
    assert git(repo, 'rev-parse', '--verify', '--quiet', 'refs/heads/missing', check=False) == ''
    assert not list((repo / '.git/refs').rglob('*.lock'))
    assert lease(export_task)[1] == 1


def test_parent_reply_loss_preserves_the_completed_export(export_task, export_client, monkeypatch):
    original = reference.task_export
    def lost(project, home, operation, payload, **kwargs):
        result = original(project, home, operation, payload, **kwargs)
        if operation == 'dispatch':
            raise ValueError('Fixture parent reply lost')
        return result
    monkeypatch.setattr(reference, 'task_export', lost)
    with pytest.raises(ValueError, match='parent reply lost'):
        export(export_task)
    result = status(export_task)
    assert result['status'] == 'exported'
    assert export(export_task) == resume(export_task) == result
    assert _calls(export_task).count('export-fetch') == 1


def test_export_inspection_reads_current_git_without_changing_receipt_or_claim(export_task, export_client):
    exported = export(export_task)
    state, repo = export_task[0], Path(export_task[1]['repo'])
    root = _root(export_task)
    original = _files(root), _files(repo), lease(export_task), _calls(export_task)
    def inspect(**changes):
        return tasks.inspect_export(state, 'demo', 'new-task',
            **{'run_id': 'original-run', 'candidate_sha': exported['candidate_sha'], 'base_branch': 'release/稳定', **changes})
    result = inspect()
    assert result['export'] == exported and result['base_sha'] == outcome(export_task)['base_sha']
    assert result['current_branch_sha'] == exported['candidate_sha'] and result['branch_matches_candidate']
    assert (_files(root), _files(repo), lease(export_task), _calls(export_task)) == original
    for options in ({'base_branch': 'bad..ref'}, {'run_id': 'another-run'}, {'candidate_sha': 'f' * 40}):
        with pytest.raises(ValueError, match='branch|original exported'):
            inspect(**options)
    assert (_files(root), _files(repo), lease(export_task), _calls(export_task)) == original
    git(repo, 'update-ref', 'refs/heads/' + exported['branch'], result['base_sha'])
    assert not inspect()['branch_matches_candidate']
    git(repo, 'update-ref', '-d', 'refs/heads/' + exported['branch'])
    missing = inspect()
    assert missing['current_branch_sha'] is None and missing['branch_matches_candidate'] is None
    assert status(export_task) == exported and lease(export_task) == original[2]


@pytest.mark.parametrize('replacement', [False, True])
def test_export_inspection_never_fetches_missing_promisor_content(export_task, export_client, monkeypatch, replacement):
    repo, root = Path(export_task[1]['repo']), _root(export_task)
    git(repo, 'config', 'fetch.unpackLimit', '1000')
    exported = export(export_task)
    source = root / 'workspaces/new-task/repo.git'
    git(repo, 'config', 'remote.origin.url', str(source))
    git(repo, 'config', 'remote.origin.promisor', 'true')
    git(repo, 'config', 'remote.origin.partialclonefilter', 'blob:none')
    git(repo, 'update-ref', '-d', 'refs/heads/' + exported['branch'])
    candidate = exported['candidate_sha']
    if replacement:
        git(repo, 'replace', candidate, outcome(export_task)['base_sha'])
    (repo / '.git/objects' / candidate[:2] / candidate[2:]).unlink()
    monkeypatch.setenv('GIT_NO_LAZY_FETCH', '1')
    before = _files(repo), _files(root), lease(export_task), _calls(export_task)
    error = None
    try:
        tasks.inspect_export(export_task[0], 'demo', 'new-task', run_id='original-run',
                             candidate_sha=candidate, base_branch='main')
    except ValueError as caught:
        error = caught
    assert (_files(repo), _files(root), lease(export_task), _calls(export_task)) == before, 'Read-only inspection fetched missing promisor objects'
    assert error is not None and 'git cat-file' in str(error)
    assert status(export_task) == exported


def test_one_task_cannot_replace_its_original_export_target_or_digest(export_task, export_client):
    original = export(export_task)
    for change in ({'branch': 'agent/another'}, {'candidate_sha': outcome(export_task)['base_sha']}):
        with pytest.raises(ValueError, match='different export target'):
            export(export_task, **change)
    with pytest.raises(ValueError, match='exact original intent'):
        tasks.resume_export(export_task[0], 'demo', 'new-task', 1, 'b' * 64, confirm=True)
    assert status(export_task) == original


@pytest.mark.parametrize('record', ['intent', 'attempt', 'result', 'native'])
def test_conflicting_export_records_are_preserved_and_never_accepted(export_task, export_client, record):
    export(export_task)
    root = _root(export_task)
    path = root / ('tasks/new-task/export.json' if record == 'native' else 'ergora/task-exports/new-task.' + record + '.json')
    value = json.loads(path.read_text())
    value['unexpected'] = 'conflict'
    raw = (json.dumps(value) + '\n').encode()
    path.write_bytes(raw)
    with pytest.raises(ValueError, match='conflicts'):
        status(export_task)
    with pytest.raises(ValueError, match='conflicts'):
        resume(export_task)
    assert path.read_bytes() == raw


def test_export_journal_symlink_cannot_redirect_writes(export_task, export_client, tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    path = _root(export_task) / 'ergora/task-exports'
    path.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='Path escapes trusted root'):
        export(export_task)
    assert not list(outside.iterdir()) and 'export-fetch' not in _calls(export_task)


def test_interrupted_prepared_ref_transaction_releases_its_git_lock(export_task, export_client, monkeypatch):
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'after-ref-prepare')
    with pytest.raises(ValueError, match='Fixture after ref prepare'):
        export(export_task)
    repo = Path(export_task[1]['repo'])
    assert not list((repo / '.git/refs').rglob('*.lock'))
    assert status(export_task)['status'] == 'unknown' and lease(export_task)[1] == 1
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'normal')
    assert resume(export_task)['reconciliation'] == 'branch_not_found'
    assert _calls(export_task).count('export-update-ref') == 1


@pytest.mark.parametrize('scenario', ['slow-fetch', 'slow-ref-prepare'])
def test_timeout_cleans_the_git_group_and_prepared_ref_locks(export_task, export_client, monkeypatch, scenario):
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', scenario)
    with pytest.raises(ValueError, match='timed out'):
        export(export_task, timeout=2)
    repo = Path(export_task[1]['repo'])
    assert not list((repo / '.git/refs').rglob('*.lock'))
    assert status(export_task)['status'] == 'unknown' and lease(export_task)[1] == 1
    if scenario == 'slow-fetch':
        for name in ('git-parent.pid', 'git-child.pid'):
            pid = int((_root(export_task) / 'sdk-fixture' / name).read_text())
            path = Path('/proc') / str(pid) / 'stat'
            assert not path.exists()
    else:
        assert 'export-ref-prepared' in _calls(export_task)
    monkeypatch.setenv('ERGORA_TEST_EXPORT_SCENARIO', 'normal')
    assert resume(export_task)['reconciliation'] == 'branch_not_found'


@pytest.mark.parametrize('linked', [False, True])
def test_export_does_not_resolve_an_existing_worktrees_unborn_head(export_task, export_client, linked):
    repo = Path(export_task[1]['repo'])
    workspace = repo
    if linked:
        workspace = repo.parent / 'linked'
        git(repo, 'worktree', 'add', '--detach', str(workspace), 'HEAD')
    git(workspace, 'checkout', '--orphan', 'agent/exported')
    (workspace / 'user-file.txt').write_text('User work in unborn branch\n')
    head = git(workspace, 'symbolic-ref', 'HEAD')
    checkout = git(workspace, 'status', '--porcelain')
    assert git(workspace, 'rev-parse', '--verify', '--quiet', 'HEAD', check=False) == ''
    with pytest.raises(ValueError, match='checked out'):
        export(export_task)
    assert git(workspace, 'symbolic-ref', 'HEAD') == head
    assert git(workspace, 'rev-parse', '--verify', '--quiet', 'HEAD', check=False) == ''
    assert git(workspace, 'status', '--porcelain') == checkout
    assert not list((repo / '.git/refs').rglob('*.lock'))
    assert lease(export_task)[1] == 1
