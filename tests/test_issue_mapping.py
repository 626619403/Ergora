"""Immutable issue context is recoverable without granting task execution authority."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import backups, issues, projects, registrations, tasks
from ergora.state import State
from test_project_issues import bind, native, source
from test_registrations import installation, registration
from test_task_creation import _inject


@pytest.fixture
def mapping_project(source, registration):
    state, definition = registration
    definition['tracker'] = {'kind': 'github', 'project': 'team/repo'}
    registrations.register(state, definition, 0)
    source.state = state
    bind(source, 'github', token_env='ERGORA_FIXTURE_ISSUE_TOKEN')
    source.raw = json.dumps(native('github')).encode()
    task = {'schema_version': 1, 'task_id': 'implementation', 'task_type': 'repository-governance', 'issue_id': '1',
            'input': {'goal': 'Implement the selected work', 'allowed_paths': ['src'],
                      'acceptance': ['Preserve original contracts'], 'constraints': [], 'risk': 'standard',
                      'work_units': [{'id': 'one', 'depends_on': [], 'paths': ['src'], 'instructions': 'Inspect source'}]}}
    return source, definition, task


def _publish(state, task):
    revision = state.project('demo')['revision']
    preview = tasks.preview(state, 'demo', task, revision)
    return tasks.create(state, 'demo', task, revision, preview['preview_sha256'])


def _files(folder):
    return {path.relative_to(folder).as_posix(): path.read_bytes() for path in folder.rglob('*') if path.is_file()}


def test_repeated_and_parallel_capture_preserves_first_observation_and_all_versions(source):
    bind(source, 'github')
    document = native('github')
    document['title'] = '完整标题' * 80
    source.raw = json.dumps(document).encode()
    first = issues.capture(source.state, 'demo', '7', 2)
    with ThreadPoolExecutor(max_workers=4) as pool:
        repeated = list(pool.map(lambda _: issues.capture(State(source.state.root), 'demo', '7', 2), range(4)))
    assert all(item['snapshot'] == first['snapshot'] for item in repeated)
    assert all(item['observed_at'] != first['observed_at'] for item in repeated)
    saved = first['snapshot']
    assert saved['first_observed_at'] == first['observed_at']
    assert 'observed_at' not in saved['payload']['observation']
    document['body'] = 'Changed body with the same upstream timestamp'
    source.raw = json.dumps(document).encode()
    second = issues.capture(source.state, 'demo', '7', 2)['snapshot']
    assert second['sha256'] != saved['sha256']
    assert second['payload']['observation']['issue']['updated_at'] == saved['payload']['observation']['issue']['updated_at']
    binding = source.state.project('demo')['bindings']['tracker']
    projects.bind(source.state, 'demo', 'tracker', {**binding, 'api_url': source.url.replace('127.0.0.1', 'localhost')}, 2)
    third = issues.capture(source.state, 'demo', '7', 3)['snapshot']
    assert third['sha256'] not in {saved['sha256'], second['sha256']}
    assert third['payload']['observation']['source']['api_url'] != saved['payload']['observation']['source']['api_url']
    assert issues.snapshot(State(source.state.root), 'demo', saved['sha256']) == saved
    listing = issues.snapshots(source.state, 'demo')
    assert len(listing['snapshots']) == 3 and listing['next_cursor'] is None
    assert all(item['title_preview'] == document['title'][:160] and item['title_truncated'] for item in listing['snapshots'])
    assert 'body' not in json.dumps(listing) and 'tracker_binding' not in json.dumps(listing)
    assert not (source.state.root / 'tasks').exists()


def test_capture_keeps_original_binding_when_configuration_changes_during_get(source, monkeypatch):
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'fixture-token')
    binding = bind(source, 'gitlab', token_env='ERGORA_FIXTURE_ISSUE_TOKEN')
    source.raw = json.dumps(native('gitlab')).encode()
    source.on_read = lambda: projects.bind(source.state, 'demo', 'tracker', {'tool': 'manual'}, 2)
    saved = issues.capture(source.state, 'demo', '7', 2)['snapshot']
    monkeypatch.delenv('ERGORA_FIXTURE_ISSUE_TOKEN')
    assert saved['payload']['tracker_binding'] == binding
    observation = saved['payload']['observation']
    assert observation['project']['revision'] == 2 and observation['issue']['native_id'] == 9001
    assert observation['source']['issue_id'] == '7'
    assert 'fixture-token' not in json.dumps(saved)
    assert issues.snapshot(State(source.state.root), 'demo', saved['sha256']) == saved
    assert len(issues.snapshots(source.state, 'demo')['snapshots']) == 1
    with pytest.raises(ValueError, match='revision changed'):
        issues.capture(source.state, 'demo', '7', 2)
    with pytest.raises(ValueError, match='tracker binding'):
        issues.capture(source.state, 'demo', '7', 3)
    assert len(source.calls) == 1


def test_unavailable_capture_leaves_no_partial_history(source):
    bind(source, 'github')
    source.status = 503
    with pytest.raises(ValueError, match='HTTP 503'):
        issues.capture(source.state, 'demo', '7', 2)
    assert issues.snapshots(source.state, 'demo') == {'project': 'demo', 'snapshots': [], 'next_cursor': None}


def test_history_pagination_binds_project_and_filters_without_returning_bodies(source):
    bind(source, 'github')
    expected = set()
    for body in ('one', 'two', 'three'):
        source.raw = json.dumps(native('github', body)).encode()
        expected.add(issues.capture(source.state, 'demo', '7', 2)['snapshot']['sha256'])
    seen, cursor = [], None
    for _ in range(3):
        page = issues.snapshots(source.state, 'demo', limit=1, after=cursor)
        seen.extend(item['sha256'] for item in page['snapshots'])
        cursor = page['next_cursor']
    assert cursor is None and seen == sorted(expected)
    cursor = issues.snapshots(source.state, 'demo', limit=1)['next_cursor']
    projects.create(source.state, 'other', Path(source.state.project('demo')['repo']))
    with pytest.raises(ValueError, match='another query'):
        issues.snapshots(source.state, 'other', after=cursor)
    with pytest.raises(ValueError, match='another query'):
        issues.links(source.state, 'demo', after=cursor)
    with pytest.raises(ValueError, match='Unknown issue snapshot'):
        issues.snapshot(source.state, 'other', seen[0])


def test_many_to_many_links_recover_offline_and_preserve_original_task_bytes(mapping_project, monkeypatch, tmp_path):
    source, definition, task = mapping_project
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'fixture-token')
    state = source.state
    first = issues.capture(state, 'demo', '7', 2)['snapshot']
    implementation = _publish(state, task)
    review_task = deepcopy(task)
    review_task['task_id'] = 'review'
    review = _publish(state, review_task)
    runtime = Path(definition['execution']['state_directory'])
    original = _files(runtime)
    creation = tasks.creation(state, 'demo', task['task_id'])
    with ThreadPoolExecutor(max_workers=3) as pool:
        repeated = list(pool.map(lambda _: issues.link_task(State(state.root), 'demo', first['sha256'],
            'implementation', implementation['intent_sha256'], 2, 'Review this source'), range(3)))
    assert repeated[0] == repeated[1] == repeated[2]
    link = repeated[0]
    assert link['payload']['task']['created_revision'] == 2
    assert link['payload']['relationship'] == 'operator_asserted_context'
    assert link['payload']['context_only'] is True and link['payload']['execution_authorized'] is False
    issues.link_task(state, 'demo', first['sha256'], 'review', review['intent_sha256'], 2, 'Independent review context')
    source.raw = json.dumps(native('github', 'A later explicit context')).encode()
    second = issues.capture(state, 'demo', '7', 2)['snapshot']
    issues.link_task(state, 'demo', second['sha256'], 'implementation', implementation['intent_sha256'], 2, 'Supplement context')
    page = issues.links(state, 'demo', task_id='implementation', limit=1)
    tail = issues.links(state, 'demo', task_id='implementation', limit=1, after=page['next_cursor'])
    assert len(page['links']) == len(tail['links']) == 1 and tail['next_cursor'] is None
    assert page['links'][0]['sha256'] != tail['links'][0]['sha256']
    with pytest.raises(ValueError, match='another query'):
        issues.links(state, 'demo', task_id='review', after=page['next_cursor'])
    assert len(issues.links(state, 'demo', snapshot_sha256=first['sha256'])['links']) == 2
    with pytest.raises(ValueError, match='exact published'):
        issues.link_task(state, 'demo', first['sha256'], 'implementation', '0' * 64, 2, 'Incorrect intent')
    projects.bind(state, 'demo', 'tracker', {'tool': 'manual'}, 2)
    monkeypatch.delenv('ERGORA_FIXTURE_ISSUE_TOKEN')
    with monkeypatch.context() as patch:
        patch.setattr(tasks, 'creation', lambda *args: pytest.fail('Saved links must not inspect the runtime'))
        assert issues.link_task(state, 'demo', first['sha256'], 'implementation', implementation['intent_sha256'],
                                2, 'A retry cannot replace the original reason') == link
        with pytest.raises(ValueError, match='revision changed'):
            issues.link_task(state, 'demo', second['sha256'], 'review', review['intent_sha256'], 2, 'A new relation')
        assert issues.snapshot(state, 'demo', first['sha256']) == first
        before_links = issues.links(state, 'demo')
        archive = tmp_path / 'context-backup'
        result = backups.create(state.root, archive, offline=True)
        assert result['issue_snapshots'] == 2 and result['issue_task_links'] == 3
        assert backups.verify(archive)['manifest_sha256'] == result['manifest_sha256']
        state.root.rename(tmp_path / 'kept-original')
        backups.restore(state.root, archive, offline=True)
        assert issues.links(State(state.root), 'demo') == before_links
        assert issues.snapshot(state, 'demo', first['sha256']) == first
    restored_creation = tasks.creation(state, 'demo', task['task_id'])
    assert restored_creation.pop('project_revision') == 3
    assert creation.pop('project_revision') == 2
    assert restored_creation == creation
    assert _files(runtime) == original
    assert not (runtime / 'requests').exists() and not (runtime / 'receipts').exists()
    assert len(source.calls) == 2


def test_competing_link_publication_wins_before_a_later_revision_edit(mapping_project, monkeypatch):
    source, definition, task = mapping_project
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'fixture-token')
    state = source.state
    saved = issues.capture(state, 'demo', '7', 2)['snapshot']
    target = _publish(state, task)
    original_creation = tasks.creation
    original_files = _files(Path(definition['execution']['state_directory']))
    winner = []

    def competing_request(*args):
        with monkeypatch.context() as patch:
            patch.setattr(tasks, 'creation', original_creation)
            winner.append(issues.link_task(state, 'demo', saved['sha256'], task['task_id'],
                                           target['intent_sha256'], 2, 'First successful request'))
        projects.bind(state, 'demo', 'tracker', {'tool': 'manual'}, 2)
        return original_creation(*args)

    monkeypatch.setattr(tasks, 'creation', competing_request)
    observed = issues.link_task(state, 'demo', saved['sha256'], task['task_id'],
                                target['intent_sha256'], 2, 'Competing response')
    assert observed == winner[0]
    assert issues.links(state, 'demo')['links'] == winner
    assert state.project('demo')['revision'] == 3
    assert _files(Path(definition['execution']['state_directory'])) == original_files


def test_pending_conflicting_and_unrecorded_creations_cannot_be_linked(mapping_project, monkeypatch):
    source, definition, task = mapping_project
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'fixture-token')
    state = source.state
    saved = issues.capture(state, 'demo', '7', 2)['snapshot']
    preview = tasks.preview(state, 'demo', task, 2)
    with monkeypatch.context() as patch:
        _inject(patch, '''
original_init = _Creation.__init__
def initialize(self, *args):
    original_init(self, *args)
    original_write = self.core.write
    def interrupted(path, value, **kwargs):
        if path.parent == self.target:
            raise OSError('simulated publication loss')
        return original_write(path, value, **kwargs)
    self.core.write = interrupted
_Creation.__init__ = initialize
''')
        with pytest.raises(ValueError, match='publication loss'):
            tasks.create(state, 'demo', task, 2, preview['preview_sha256'])
    assert tasks.creation(state, 'demo', task['task_id'])['status'] == 'pending'
    with pytest.raises(ValueError, match='exact published'):
        issues.link_task(state, 'demo', saved['sha256'], task['task_id'], preview['preview_sha256'], 2, 'Pending target')
    tasks.resume_create(state, 'demo', task['task_id'], 2, preview['preview_sha256'])
    compiled = Path(definition['execution']['state_directory']) / 'tasks' / task['task_id'] / 'compiled.json'
    compiled.write_text('{}', encoding='utf-8')
    assert tasks.creation(state, 'demo', task['task_id'])['status'] == 'conflict'
    for task_id in (task['task_id'], 'missing'):
        with pytest.raises(ValueError, match='exact published'):
            issues.link_task(state, 'demo', saved['sha256'], task_id, preview['preview_sha256'], 2, 'Unpublished target')
    assert issues.links(state, 'demo')['links'] == []


@pytest.mark.parametrize('corruption', ['snapshot-document', 'binding-host', 'orphan'])
def test_backup_refuses_corrupted_context_before_publishing(mapping_project, monkeypatch, tmp_path, corruption):
    source, _, task = mapping_project
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'fixture-token')
    state = source.state
    saved = issues.capture(state, 'demo', '7', 2)['snapshot']
    target = _publish(state, task)
    issues.link_task(state, 'demo', saved['sha256'], task['task_id'], target['intent_sha256'], 2, 'Context')
    with state.connect() as db:
        if corruption == 'snapshot-document':
            db.execute("UPDATE issue_snapshots SET document='{}'")
        elif corruption == 'binding-host':
            payload = deepcopy(saved['payload'])
            payload['tracker_binding']['api_url'] = 'https://other.example.invalid'
            # A consistent content hash cannot hide a contradictory binding/source pair.
            digest = issues._identity(payload)
            db.execute('UPDATE issue_snapshots SET sha=?, document=?', (digest, json.dumps(payload)))
        else:
            db.execute('DELETE FROM issue_snapshots')
    destination = tmp_path / 'invalid-backup'
    with pytest.raises(ValueError, match='snapshot|missing'):
        backups.create(state.root, destination, offline=True)
    assert not destination.exists()


def test_cli_and_http_share_capture_link_and_offline_recovery(mapping_project, monkeypatch):
    pytest.importorskip('fastapi')
    pytest.importorskip('httpx')
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    source, _, task = mapping_project
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'fixture-token')
    state = source.state
    target = _publish(state, task)

    def cli(*arguments):
        result = subprocess.run([sys.executable, '-m', 'ergora', '--home', str(state.root), 'issue', *arguments],
                                capture_output=True, text=True, encoding='utf-8', timeout=30)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    captured = cli('capture', 'demo', '7', '--revision', '2')['snapshot']
    with TestClient(create_app(state.root), base_url='http://127.0.0.1:8977') as client:
        url = '/api/projects/demo/issues/7/snapshots'
        assert client.post(url, json={'revision': 2}).status_code == 403
        headers = {'X-Ergora-Request': '1'}
        assert client.post(url, json={'revision': True}, headers=headers).status_code == 422
        assert client.post(url, json={'revision': 2}, headers={**headers, 'Origin': 'https://other.invalid'}).status_code == 403
        response = client.post(url, json={'revision': 2}, headers=headers)
        assert response.status_code == 200 and response.json()['snapshot'] == captured
        body = {'snapshot_sha256': captured['sha256'], 'task_id': task['task_id'],
                'creation_sha256': target['intent_sha256'], 'revision': 2, 'reason': 'Explicit CLI and HTTP association'}
        assert client.post('/api/projects/demo/issue-links', json=body).status_code == 403
        response = client.post('/api/projects/demo/issue-links', json=body, headers=headers)
        assert response.status_code == 200
        link = response.json()
        projects.bind(state, 'demo', 'tracker', {'tool': 'manual'}, 2)
        monkeypatch.delenv('ERGORA_FIXTURE_ISSUE_TOKEN')
        assert cli('snapshot', 'demo', captured['sha256']) == captured
        assert client.get('/api/projects/demo/issue-snapshots/' + captured['sha256']).json() == captured
        assert cli('snapshots', 'demo', '--limit', '1') == client.get('/api/projects/demo/issue-snapshots?limit=1').json()
        assert cli('link-task', 'demo', captured['sha256'], task['task_id'], '--creation-sha256', target['intent_sha256'],
                   '--revision', '2', '--reason', 'Retry') == link
        assert cli('links', 'demo', '--task', task['task_id']) == client.get('/api/projects/demo/issue-links',
            params={'task_id': task['task_id']}).json()
    assert len(source.calls) == 2 and {call['method'] for call in source.calls} == {'GET'}
