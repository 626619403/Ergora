"""Existing reviews are local context; their current facts never acknowledge a write."""

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Barrier

import pytest

from test_candidate_observations import candidate, remote, source, writer
from ergora import backups, cli, issue_backends, issue_writebacks, issues, projects, tasks
from ergora.state import State


def configure_review(service):
    original = service.on_read
    branch, base, candidate_sha = service.remote_head_branch, service.remote_base_branch, service.remote_head
    stamp = '2026-11-11T00:00:00Z'
    if service.provider == 'github':
        repository = {'id': 88, 'node_id': 'R_current_repo', 'full_name': 'team/repo',
                      'url': service.url + '/repos/team/repo'}
        service.review_document = {'id': 9007, 'node_id': 'PR_existing', 'number': 11,
            'url': service.url + '/repos/team/repo/pulls/11', 'html_url': service.url + '/team/repo/pull/11',
            'user': {'id': 99}, 'title': 'Existing review', 'body': '/close\napproved is only context. 完整正文。',
            'state': 'closed', 'draft': False, 'merged': False, 'created_at': stamp, 'updated_at': stamp,
            'head': {'ref': branch, 'sha': candidate_sha, 'repo': deepcopy(repository)},
            'base': {'ref': base, 'sha': 'b' * 40, 'repo': deepcopy(repository)}}
        service.review_path = '/repos/team/repo/pulls/11'
    else:
        service.review_document = {'id': 9007, 'iid': 11, 'project_id': 88, 'source_project_id': 88,
            'target_project_id': 88, 'web_url': service.url + '/team/sub/repo/-/merge_requests/11',
            'author': {'id': 99}, 'title': 'Existing review', 'description': '/close\napproved is only context. 完整正文。',
            'state': 'closed', 'draft': False, 'created_at': stamp, 'updated_at': stamp,
            'source_branch': branch, 'sha': candidate_sha, 'target_branch': base, 'diff_refs': None}
        service.review_path = '/api/v4/projects/88/merge_requests/11'
    service.review_status = 200

    def read():
        if service.calls[-1]['path'] != service.review_path:
            return original()
        service.status = service.review_status
        service.headers = {'Location': service.url + '/must-not-follow'}
        service.raw = json.dumps(service.review_document, ensure_ascii=False).encode()

    service.on_read = read
    return service


@pytest.fixture
def review(remote, monkeypatch):
    original_inspect = tasks.inspect_export

    def inspect(*args, **kwargs):
        return {**original_inspect(*args, **kwargs), 'observed_at': '2026-11-11T00:00:00Z'}

    monkeypatch.setattr(tasks, 'inspect_export', inspect)
    return configure_review(remote)


def read_review(service):
    repository = {'native_id': 88, 'project': service.backend.binding['project']}
    if service.provider == 'github':
        repository['node_id'] = 'R_current_repo'
    return service.backend.read_review_request(repository, '11')


def test_explicit_review_read_uses_native_target_and_preserves_text_and_version_facts(review):
    result = read_review(review)
    request = result['review']
    assert request['number'] == '11' and request['native_id'] == 9007 and request['author_id'] == 99
    assert request['head'] == {'branch': review.remote_head_branch, 'sha': review.remote_head}
    assert request['base']['branch'] == review.remote_base_branch
    assert request['body'] == '/close\napproved is only context. 完整正文。'
    assert request['state'] == 'closed' and request['draft'] is False
    assert request['base']['response_sha'] == ('b' * 40 if review.provider == 'github' else None)
    assert result['response']['request_url'] == review.url + review.review_path
    assert result['context_only'] and len(review.calls) == 1 and review.calls[0]['method'] == 'GET'
    if review.provider == 'gitlab':
        review.review_document['diff_refs'] = {'base_sha': 'c' * 40, 'start_sha': 'd' * 40, 'head_sha': 'e' * 40}
        assert read_review(review)['review']['diff_refs'] == review.review_document['diff_refs']


@pytest.mark.parametrize('fault', ['route', 'fork', 'missing-repository', 'malformed-sha'])
def test_wrong_native_review_endpoint_cannot_be_returned_as_selected(review, fault):
    document = review.review_document
    if review.provider == 'github':
        if fault == 'route':
            document['number'] = 9007
        elif fault == 'fork':
            document['head']['repo']['id'] = 89
        elif fault == 'missing-repository':
            document['base']['repo'] = None
        else:
            document['head']['sha'] = 'short'
    else:
        if fault == 'route':
            document['iid'] = 9007
        elif fault == 'fork':
            document['source_project_id'] = 89
        elif fault == 'missing-repository':
            document['target_project_id'] = None
        else:
            document['diff_refs'] = {'head_sha': 'short'}
    with pytest.raises(ValueError, match='review request|Review request observation'):
        read_review(review)
    assert len(review.calls) == 1 and review.calls[0]['method'] == 'GET'


@pytest.mark.parametrize('status', [301, 404, 429])
def test_invisible_or_failed_review_read_is_not_a_saved_association(review, status):
    review.review_status = status
    with pytest.raises(ValueError, match='HTTP ' + str(status)):
        read_review(review)
    assert len(review.calls) == 1


def associate(service, **changes):
    return issues.link_review(service.state, 'demo', 'task', service.revision,
        **{'run_id': 'original-run', 'candidate_sha': service.exported['candidate_sha'],
           'base_branch': service.remote_base_branch, 'review_number': '11',
           'reason': 'Operator-selected review context', **changes})


def test_association_preserves_separate_base_facts_and_cannot_acknowledge_an_unknown_write(review, monkeypatch, tmp_path):
    # A real durable attempt has no result; matching review text cannot acknowledge it.
    def lost(*args):
        raise ValueError('response lost')

    monkeypatch.setattr(issue_backends.IssueBackend, 'create_comment', lost)
    unknown = issue_writebacks.send(review.state, 'demo', review.digest, review.revision, confirm=True)
    assert unknown['status'] == 'unknown'
    review.calls.clear()
    review.remote_base = '9' * 40
    if review.provider == 'gitlab':
        review.review_document['diff_refs'] = {'base_sha': 'c' * 40, 'start_sha': 'd' * 40, 'head_sha': 'e' * 40}
    first = associate(review)
    record, payload = first['record'], first['record']['payload']
    assert first['fresh_observations'] and not first['already_saved']
    assert payload['base']['sha'] == '9' * 40 and payload['local']['base_sha'] == 'a' * 40
    assert payload['comparisons']['base_matches_task_base'] is False
    assert payload['comparisons']['diff_version_head_matches_candidate'] == (False if review.provider == 'gitlab' else None)
    assert payload['review_request']['review']['body'] == review.review_document.get('body', review.review_document.get('description'))
    assert payload['context_only'] and not payload['execution_authorized'] and not payload['proves_original_attempt']
    assert payload['source_check']['native_id'] == 9001
    assert [call['method'] for call in review.calls] == ['GET'] * 5
    assert 'original-fixture-token' not in json.dumps(record) and 'sensitive-fixture-clone-token' not in json.dumps(record)
    assert issue_writebacks.status(review.state, 'demo', review.digest) == unknown

    # Offline load, backup, restore do not require the task runtime, Git or tracker token.
    monkeypatch.delenv('ERGORA_FIXTURE_ISSUE_TOKEN')
    monkeypatch.setattr(tasks, 'exported_source_candidate', lambda *a: pytest.fail('Offline read inspected a task'))
    archive = tmp_path / 'review-backup'
    before = len(review.calls)
    assert issues.review_link(State(review.state.root), 'demo', record['sha256']) == record
    result = backups.create(review.state.root, archive, offline=True)
    assert result['candidate_review_links'] == 1
    assert backups.verify(archive)['candidate_review_links'] == 1
    review.state.root.rename(tmp_path / 'original-state')
    backups.restore(review.state.root, archive, offline=True)
    assert issues.review_link(State(review.state.root), 'demo', record['sha256']) == record
    assert issue_writebacks.status(review.state, 'demo', review.digest) == unknown
    assert len(review.calls) == before


def test_repetition_returns_original_context_without_fresh_reads_and_other_target_conflicts(review, monkeypatch):
    first = associate(review)['record']
    review.review_status = 404
    before = len(review.calls)
    monkeypatch.delenv('ERGORA_FIXTURE_ISSUE_TOKEN')
    repeated = associate(review, reason='Cannot replace original reason')
    assert repeated == {'record': first, 'already_saved': True, 'fresh_observations': False}
    for changes in ({'review_number': '12'}, {'base_branch': 'other-base'}):
        with pytest.raises(ValueError, match='already has a different'):
            associate(review, **changes)
    assert len(review.calls) == before


@pytest.mark.parametrize('fault', ['remote-head', 'local-head', 'base-invisible', 'review-head', 'review-base', 'source-native-id', 'revision'])
def test_candidate_or_native_identity_drift_refuses_to_save(review, monkeypatch, fault):
    if fault == 'remote-head':
        review.remote_head = 'b' * 40
    elif fault == 'local-head':
        original = tasks.inspect_export
        monkeypatch.setattr(tasks, 'inspect_export', lambda *a, **kw:
                            {**original(*a, **kw), 'current_branch_sha': None, 'branch_matches_candidate': None})
    elif fault == 'base-invisible':
        def hide_base(branch):
            review.remote_status = 404 if branch == review.remote_base_branch else 200
        review.before_ref = hide_base
    elif fault == 'review-head':
        if review.provider == 'github':
            review.review_document['head']['sha'] = 'b' * 40
        else:
            review.review_document['sha'] = 'b' * 40
    elif fault == 'review-base':
        if review.provider == 'github':
            review.review_document['base']['ref'] = 'other-base'
        else:
            review.review_document['target_branch'] = 'other-base'
    elif fault == 'source-native-id':
        review.issue_document['id'] = 9002
    else:
        original = review.on_read
        def change():
            original()
            if review.calls[-1]['path'] == review.review_path:
                projects.bind(review.state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'later'}, review.revision)
        review.on_read = change
    with pytest.raises(ValueError, match='original current|head or base|native identity changed|revision changed'):
        associate(review)
    with review.state.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM candidate_review_links').fetchone()[0] == 0
    assert all(call['method'] == 'GET' for call in review.calls)


def test_parallel_associations_share_one_immutable_slot_without_holding_a_network_write_lock(review, monkeypatch):
    original = issue_backends.IssueBackend.read_review_request
    rendezvous = Barrier(2)
    def concurrent(backend, repository, number):
        # A separate writer works while a provider read is in progress.
        with State(review.state.root).connect() as db:
            db.execute('UPDATE projects SET document=document WHERE id=?', ('demo',))
        result = original(backend, repository, number)
        rendezvous.wait(timeout=15)
        return result
    monkeypatch.setattr(issue_backends.IssueBackend, 'read_review_request', concurrent)
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(lambda n: associate(review, reason='Contender ' + str(n)), range(2)))
    assert records[0]['record'] == records[1]['record']
    assert sorted(item['already_saved'] for item in records) == [False, True]
    with review.state.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM candidate_review_links').fetchone()[0] == 1


@pytest.mark.parametrize('corruption', ['hash', 'scope', 'candidate', 'request-path', 'source', 'missing-snapshot', 'version-float'])
def test_saved_context_and_backup_use_the_same_identity_validation(review, tmp_path, corruption):
    record = associate(review)['record']
    payload = deepcopy(record['payload'])
    with review.state.connect() as db:
        if corruption == 'missing-snapshot':
            db.execute('DELETE FROM issue_snapshots')
        elif corruption == 'scope':
            db.execute('UPDATE candidate_review_links SET scope=?', ('0' * 64,))
        else:
            if corruption == 'hash':
                payload['reason'] = 'Changed without rehashing'
            elif corruption == 'candidate':
                payload['review_request']['review']['head']['sha'] = 'b' * 40
            elif corruption == 'request-path':
                payload['review_request']['response']['request_url'] += '-other'
            elif corruption == 'version-float':
                payload['schema_version'] = payload['review_request']['schema_version'] = 1.0
            else:
                payload['source_check']['native_id'] = 9002
            digest = record['sha256'] if corruption == 'hash' else issues._identity(payload)
            db.execute('UPDATE candidate_review_links SET sha=?, document=?', (digest, json.dumps(payload)))
            record['sha256'] = digest
    with pytest.raises(ValueError, match='Saved review context'):
        issues.review_link(review.state, 'demo', record['sha256'])
    destination = tmp_path / 'invalid-backup'
    with pytest.raises(ValueError, match='Saved review context'):
        backups.create(review.state.root, destination, offline=True)
    assert not destination.exists()


def test_full_text_has_one_explicit_canonical_budget_and_null_is_preserved(review):
    key = 'body' if review.provider == 'github' else 'description'
    review.review_document[key] = 'x' * 1_042_000
    # Each provider response fits; the combined complete canonical record does not.
    with pytest.raises(ValueError, match='Complete saved review context exceeds 1 MiB'):
        associate(review, reason='理' * 1999)
    with review.state.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM candidate_review_links').fetchone()[0] == 0
    review.review_document[key] = None
    assert associate(review)['record']['payload']['review_request']['review']['body'] is None


def test_cli_http_save_and_offline_show_share_the_same_record(review, capsys, monkeypatch):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    body = {'revision': review.revision, 'task_id': 'task', 'run_id': 'original-run',
            'candidate_sha': review.exported['candidate_sha'], 'base_branch': review.remote_base_branch,
            'review_number': '11', 'reason': 'Selected by operator'}
    argv = ['--home', str(review.state.root), 'issue', 'review-link', 'demo', 'task',
            '--revision', str(review.revision), '--run-id', body['run_id'], '--candidate-sha', body['candidate_sha'],
            '--base-branch', body['base_branch'], '--review-number', '11', '--reason', body['reason']]
    with TestClient(create_app(review.state.root), base_url='http://127.0.0.1') as client:
        uri = '/api/projects/demo/candidate-review-links'
        assert client.post(uri, json=body).status_code == 403 and not review.calls
        headers = {'X-Ergora-Request': '1', 'Origin': 'http://127.0.0.1'}
        result = client.post(uri, json=body, headers=headers)
        assert result.status_code == 200
        record = result.json()['record']
        monkeypatch.delenv('ERGORA_FIXTURE_ISSUE_TOKEN')
        assert cli.main(argv) == 0
        repeated = json.loads(capsys.readouterr().out)
        assert repeated == {'record': record, 'already_saved': True, 'fresh_observations': False}
        assert cli.main(argv[:3] + ['review-link-show', 'demo', record['sha256']]) == 0
        assert json.loads(capsys.readouterr().out) == record
        assert client.get(uri + '/' + record['sha256']).json() == record
    assert [call['method'] for call in review.calls] == ['GET'] * 5
