"""Current ref facts cannot become publication receipts or authorization."""

from copy import deepcopy
import json
from urllib.parse import quote, unquote

import pytest

from ergora import cli, issues, projects, tasks
from test_issue_writebacks import candidate, writer
from test_project_issues import source


def configure_remote(service, head_sha, base_sha, head_branch, base_branch):
    original = service.on_read
    service.remote_head, service.remote_base = head_sha, base_sha
    service.remote_head_branch, service.remote_base_branch = head_branch, base_branch
    service.remote_transform = lambda kind, value: value
    service.remote_status, service.before_ref = 200, lambda branch: None

    def read():
        path = service.calls[-1]['path']
        if path == '/repos/team/repo':
            kind = 'repository'
            document = {'id': 88, 'node_id': 'R_current_repo', 'full_name': 'team/repo',
                        'url': service.url + path, 'temp_clone_token': 'sensitive-fixture-clone-token'}
        elif path == '/api/v4/projects/team%2Fsub%2Frepo':
            kind = 'repository'
            document = {'id': 88, 'path_with_namespace': 'team/sub/repo'}
        elif '/git/ref/heads/' in path or '/repository/branches/' in path:
            kind = 'ref'
            branch = unquote(path.split('/git/ref/heads/' if service.provider == 'github' else '/repository/branches/', 1)[1])
            service.before_ref(branch)
            sha = service.remote_head if branch == service.remote_head_branch else service.remote_base
            if service.provider == 'github':
                document = {'ref': 'refs/heads/' + branch, 'object': {'type': 'commit', 'sha': sha},
                            'url': service.url + '/repos/team/repo/git/refs/heads/' + quote(branch, safe='/')}
            else:
                assert path.startswith('/api/v4/projects/88/repository/branches/')
                document = {'name': branch, 'commit': {'id': sha}}
        else:
            return original()
        service.status = service.remote_status if kind == 'ref' else 200
        service.headers = {'Location': service.url + '/must-not-follow'}
        service.raw = json.dumps(service.remote_transform(kind, document), ensure_ascii=False).encode()

    service.on_read = read
    return service


@pytest.fixture
def remote(candidate, monkeypatch):
    head, base = candidate.exported['branch'], 'release/稳定,base'
    configure_remote(candidate, candidate.exported['candidate_sha'], 'a' * 40, head, base)

    def inspect(*args, **kwargs):
        return {'export': deepcopy(candidate.exported), 'base_sha': 'a' * 40,
                'candidate_sha': candidate.exported['candidate_sha'], 'branch': head,
                'current_branch_sha': candidate.exported['candidate_sha'], 'branch_matches_candidate': True,
                'base_branch': kwargs['base_branch'], 'objects_verified_as_commits': True,
                'coverage': 'Controlled local owner port; real native coverage is separate'}

    monkeypatch.setattr(tasks, 'inspect_export', inspect)
    candidate.calls.clear()
    return candidate


def observe(service, **changes):
    return issues.remote_candidate(service.state, 'demo', 'task', service.revision,
        **{'run_id': 'original-run', 'candidate_sha': service.exported['candidate_sha'],
           'base_branch': service.remote_base_branch, **changes})


def logical_state(state):
    with state.connect() as db:
        return list(db.iterdump())


def test_both_protocols_compare_exact_refs_without_writes_or_sensitive_fields(remote):
    before = logical_state(remote.state)
    result = observe(remote)
    assert result['comparisons'] == {'local_export_ref_matches_candidate': True,
                                    'head_matches_candidate': True, 'base_matches_task_base': True}
    assert result['task']['export_intent_sha256'] == remote.exported['intent_sha256']
    assert result['snapshot_sha256'] == remote.saved['sha256']
    assert result['remote']['repository']['native_id'] == 88
    assert result['remote']['head']['ref'] == 'refs/heads/' + remote.remote_head_branch
    assert result['remote']['base']['ref'] == 'refs/heads/' + remote.remote_base_branch
    assert result['context_only'] and not result['execution_authorized'] and not result['proves_original_attempt']
    assert 'sensitive-fixture-clone-token' not in json.dumps(result)
    assert 'original-fixture-token' not in json.dumps(result)
    assert len(remote.calls) == 3 and all(call['method'] == 'GET' for call in remote.calls)
    assert all(result['remote'][key]['observed_at'] and len(result['remote'][key]['response_sha256']) == 64
               for key in ('repository', 'head', 'base'))
    assert logical_state(remote.state) == before


def test_drift_and_404_are_distinct_from_matching_publication_receipts(remote):
    remote.remote_head, remote.remote_base = 'b' * 40, 'c' * 40
    changed = observe(remote)
    assert changed['comparisons'] == {'local_export_ref_matches_candidate': True,
                                     'head_matches_candidate': False, 'base_matches_task_base': False}
    remote.remote_status = 404
    missing = observe(remote)
    assert missing['comparisons']['head_matches_candidate'] is None
    assert missing['comparisons']['base_matches_task_base'] is None
    for key in ('head', 'base'):
        assert missing['remote'][key]['resolution'] == 'not_found_or_not_visible'
        assert missing['remote'][key]['http_status'] == 404 and missing['remote'][key]['sha'] is None
    assert all(call['method'] == 'GET' for call in remote.calls)


@pytest.mark.parametrize('failure', ['repository', 'ref', 'object'])
def test_wrong_namespace_exact_ref_or_object_cannot_be_reported_as_candidate(remote, failure):
    def transform(kind, document):
        if failure == 'repository' and kind == 'repository':
            document['full_name' if remote.provider == 'github' else 'path_with_namespace'] = 'another/repository'
        if kind == 'ref':
            if failure == 'ref':
                document['ref' if remote.provider == 'github' else 'name'] += '-same-prefix'
            if failure == 'object':
                if remote.provider == 'github':
                    document['object']['type'] = 'tag'
                else:
                    document['commit']['id'] = 'short-sha'
        return document
    remote.remote_transform = transform
    with pytest.raises(ValueError, match='repository identity|exact branch ref'):
        observe(remote)


@pytest.mark.parametrize('status', [301, 403, 429])
def test_transport_errors_are_not_missing_refs_or_retried(remote, status):
    remote.remote_status = status
    with pytest.raises(ValueError, match='HTTP ' + str(status)):
        observe(remote)
    assert len(remote.calls) == 2 and all(call['method'] == 'GET' for call in remote.calls)


def test_source_candidate_and_project_revision_drift_do_not_redirect_reads(remote):
    before = logical_state(remote.state)
    with pytest.raises(ValueError, match='exact original exported'):
        observe(remote, candidate_sha='e' * 40)
    assert remote.calls == [] and logical_state(remote.state) == before
    changed = False
    def change(branch):
        nonlocal changed
        if not changed:
            projects.bind(remote.state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'later'}, remote.revision)
            changed = True
    remote.before_ref = change
    with pytest.raises(ValueError, match='revision changed'):
        observe(remote)
    assert len(remote.calls) == 3 and all(call['method'] == 'GET' for call in remote.calls)


def test_cli_and_protected_http_use_the_same_read_only_observation(remote, capsys):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    before = logical_state(remote.state)
    argv = ['--home', str(remote.state.root), 'issue', 'candidate-observe', 'demo', 'task',
            '--revision', str(remote.revision), '--run-id', 'original-run',
            '--candidate-sha', remote.exported['candidate_sha'], '--base-branch', remote.remote_base_branch]
    assert cli.main(argv) == 0
    command = json.loads(capsys.readouterr().out)
    with TestClient(create_app(remote.state.root), base_url='http://127.0.0.1') as client:
        uri = '/api/projects/demo/candidate-observations'
        body = {'revision': remote.revision, 'task_id': 'task', 'run_id': 'original-run',
                'candidate_sha': remote.exported['candidate_sha'], 'base_branch': remote.remote_base_branch}
        assert client.post(uri, json=body).status_code == 403
        headers = {'X-Ergora-Request': '1', 'Origin': 'http://127.0.0.1'}
        result = client.post(uri, json=body, headers=headers)
        assert result.status_code == 200
        assert result.json()['comparisons'] == command['comparisons']
        assert result.json()['task'] == command['task']
    assert logical_state(remote.state) == before and len(remote.calls) == 6
    assert all(call['method'] == 'GET' for call in remote.calls)
