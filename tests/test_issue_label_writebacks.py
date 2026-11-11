"""Native ID operands, durable one-attempt writes and current-page uncertainty."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import backups, cli, issue_backends, issue_writebacks, projects
from ergora.state import State
from test_project_issues import source
from test_issue_writebacks import candidate_for, configure_labels, writer_for


@pytest.fixture
def labelled(source, monkeypatch):
    service = configure_labels(candidate_for(writer_for(source, monkeypatch, 'github'), monkeypatch))
    service.comment_digest = service.digest
    service.prepared_label = issue_writebacks.prepare_label(service.state, 'demo', 'task', service.revision,
        run_id='original-run', candidate_sha='6' * 40, label_name=service.label_name)
    service.digest = service.prepared_label['intent_sha256']
    return service


def test_native_id_label_commits_attempt_before_one_mutation_and_preserves_human_labels(labelled, monkeypatch):
    original = labelled.on_write

    def durable():
        if labelled.calls[-1]['body']['query'].startswith('mutation '):
            process = subprocess.run([sys.executable, '-m', 'ergora', '--home', str(labelled.state.root),
                'issue', 'writeback-status', 'demo', labelled.digest], capture_output=True, text=True, check=True)
            assert json.loads(process.stdout)['status'] == 'unknown' and labelled.label_mutations == []
        original()

    labelled.on_write = durable
    sent = issue_writebacks.send(labelled.state, 'demo', labelled.digest, labelled.revision, confirm=True)
    assert sent['status'] == 'acknowledged' and len(labelled.label_mutations) == 1
    operation = sent['intent']['operation']
    assert operation['url'] == labelled.url + '/graphql'
    assert labelled.label_mutations[0] == operation['body']
    assert operation['body']['variables']['input'] == {'labelableId': 'I_original_issue',
        'labelIds': ['LA_existing_label'], 'clientMutationId': sent['intent']['scope_sha256']}
    assert labelled.label_name not in operation['body']['query']
    assert {item['id'] for item in labelled.label_members} == {'LA_human', 'LA_existing_label'}
    calls = len(labelled.calls)
    monkeypatch.delenv('ERGORA_FIXTURE_ISSUE_TOKEN')
    assert issue_writebacks.status(State(labelled.state.root), 'demo', labelled.digest) == sent
    assert issue_writebacks.send(State(labelled.state.root), 'demo', labelled.digest, labelled.revision, confirm=True) == sent
    assert len(labelled.calls) == calls


def test_lost_response_membership_and_human_removal_never_open_another_attempt(labelled):
    labelled.drop_write = True
    unknown = issue_writebacks.send(labelled.state, 'demo', labelled.digest, labelled.revision, confirm=True)
    assert unknown['status'] == 'unknown' and len(labelled.label_mutations) == 1
    labelled.drop_write = False
    found = issue_writebacks.observe(State(labelled.state.root), 'demo', labelled.digest)
    assert found['status'] == 'unknown' and found['latest_observation']['document']['membership_in_page'] == 'present'
    assert found['latest_observation']['document']['proves_original_attempt'] is False
    labelled.label_members.clear()
    empty = issue_writebacks.observe(labelled.state, 'demo', labelled.digest)
    assert empty['status'] == 'unknown' and empty['latest_observation']['document']['membership_in_page'] == 'not_seen'
    assert issue_writebacks.prepare_label(labelled.state, 'demo', 'task', labelled.revision,
        run_id='original-run', candidate_sha='6' * 40, label_name=labelled.label_name)['intent_sha256'] == labelled.digest
    with pytest.raises(ValueError, match='frozen operand'):
        issue_writebacks.prepare_label(labelled.state, 'demo', 'task', labelled.revision,
            run_id='original-run', candidate_sha='6' * 40, label_name='new-name-cannot-retry')
    issue_writebacks.send(State(labelled.state.root), 'demo', labelled.digest, labelled.revision, confirm=True)
    assert len(labelled.label_mutations) == 1 and labelled.label_members == []


@pytest.mark.parametrize('fault', ['partial-errors', 'wrong-target', 'not-in-selected-page', 'wrong-echo'])
def test_complete_http_200_is_insufficient_without_the_original_matching_graphql_payload(labelled, fault):
    def transform(document):
        payload = document['data']['addLabelsToLabelable']
        if fault == 'partial-errors':
            document['errors'] = [{'message': 'May already have applied'}]
        elif fault == 'wrong-target':
            payload['labelable']['id'] = 'I_another_issue'
        elif fault == 'wrong-echo':
            payload['clientMutationId'] = 'another-client'
        else:
            payload['labelable']['labels'] = {'nodes': [], 'pageInfo': {'hasNextPage': True, 'endCursor': 'opaque-next'}}
        return document

    labelled.graphql_transform = transform
    result = issue_writebacks.send(labelled.state, 'demo', labelled.digest, labelled.revision, confirm=True)
    assert result['status'] == 'unknown' and result['result'] is None and len(labelled.label_mutations) == 1
    assert any(item['id'] == 'LA_existing_label' for item in labelled.label_members)
    issue_writebacks.send(State(labelled.state.root), 'demo', labelled.digest, labelled.revision, confirm=True)
    assert len(labelled.label_mutations) == 1


@pytest.mark.parametrize('change', ['rename', 'delete-recreate'])
def test_definition_drift_is_rejected_without_name_based_retargeting(labelled, change):
    if change == 'rename':
        labelled.label['name'] = 'new-name'
    else:
        labelled.label.update(id=102, node_id='LA_recreated_label')
    with pytest.raises(ValueError, match='label identity|native identity changed'):
        issue_writebacks.send(labelled.state, 'demo', labelled.digest, labelled.revision, confirm=True)
    assert issue_writebacks.status(labelled.state, 'demo', labelled.digest)['status'] == 'prepared'
    assert labelled.label_mutations == []


def test_parallel_confirmations_share_one_original_attempt(labelled):
    def send(_):
        return issue_writebacks.send(State(labelled.state.root), 'demo', labelled.digest, labelled.revision, confirm=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(send, range(2)))
    assert {result['status'] for result in results} <= {'unknown', 'acknowledged'}
    assert issue_writebacks.status(labelled.state, 'demo', labelled.digest)['status'] == 'acknowledged'
    assert len(labelled.label_mutations) == 1


def test_revision_change_after_mutation_leaves_unknown_and_keeps_both_action_records(labelled, tmp_path):
    original = labelled.on_write

    def write():
        original()
        projects.bind(labelled.state, 'demo', 'reviewer',
                      {'tool': 'codex', 'model': 'concurrent-revision', 'sandbox': 'read-only'}, labelled.revision)

    labelled.on_write = write
    with pytest.raises(ValueError, match='revision changed'):
        issue_writebacks.send(labelled.state, 'demo', labelled.digest, labelled.revision, confirm=True)
    before = issue_writebacks.status(labelled.state, 'demo', labelled.digest)
    assert before['status'] == 'unknown'
    issue_writebacks.send(State(labelled.state.root), 'demo', labelled.digest, labelled.revision + 1, confirm=True)
    assert len(labelled.label_mutations) == 1
    comment = issue_writebacks.status(labelled.state, 'demo', labelled.comment_digest)
    backup = tmp_path / 'backup'
    saved = backups.create(labelled.state.root, backup, offline=True)
    assert saved['issue_writebacks'] == 2
    labelled.state.root.rename(tmp_path / 'original-state')
    backups.restore(labelled.state.root, backup, offline=True)
    assert issue_writebacks.status(State(labelled.state.root), 'demo', labelled.digest) == before
    assert issue_writebacks.status(labelled.state, 'demo', labelled.comment_digest) == comment


def test_observe_cursor_reads_one_page_and_cannot_confirm_an_unknown_attempt(labelled):
    labelled.drop_write = True
    issue_writebacks.send(labelled.state, 'demo', labelled.digest, labelled.revision, confirm=True)
    labelled.drop_write = False
    labelled.label_has_next, labelled.label_cursor = True, 'page-two/opaque+cursor'
    first = issue_writebacks.observe(labelled.state, 'demo', labelled.digest)
    assert first['status'] == 'unknown'
    assert first['latest_observation']['document']['native']['page']['page_info']['has_next_page'] is True
    labelled.label_has_next, labelled.label_cursor = False, None
    next_page = issue_writebacks.observe(labelled.state, 'demo', labelled.digest, cursor='page-two/opaque+cursor')
    query = labelled.calls[-1]['body']
    assert query['query'].startswith('query ') and query['variables']['cursor'] == 'page-two/opaque+cursor'
    assert next_page['status'] == 'unknown' and len(labelled.label_mutations) == 1


def test_label_prepare_cli_and_protected_http_use_the_shared_writeback_lifecycle(labelled, capsys):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    command = ['--home', str(labelled.state.root), 'issue', 'writeback-label-prepare', 'demo', 'task',
        '--revision', str(labelled.revision), '--run-id', 'original-run', '--candidate-sha', '6' * 40,
        '--label-name', labelled.label_name]
    assert cli.main(command) == 0
    assert json.loads(capsys.readouterr().out)['intent_sha256'] == labelled.digest
    payload = {'revision': labelled.revision, 'task_id': 'task', 'run_id': 'original-run',
               'candidate_sha': '6' * 40, 'label_name': labelled.label_name}
    headers = {'X-Ergora-Request': '1', 'Origin': 'http://127.0.0.1'}
    base = '/api/projects/demo/issue-writebacks/' + labelled.digest
    with TestClient(create_app(labelled.state.root), base_url='http://127.0.0.1') as client:
        assert client.post('/api/projects/demo/issue-label-writebacks', json=payload).status_code == 403
        prepared = client.post('/api/projects/demo/issue-label-writebacks', json=payload, headers=headers)
        assert prepared.status_code == 200 and prepared.json()['intent_sha256'] == labelled.digest
        assert client.post(base + '/send', json={'revision': labelled.revision, 'confirm': False}, headers=headers).status_code == 400
        sent = client.post(base + '/send', json={'revision': labelled.revision, 'confirm': True}, headers=headers)
        assert sent.status_code == 200 and sent.json()['status'] == 'acknowledged'
        observed = client.post(base + '/observe', json={'cursor': 'some-opaque-cursor'}, headers=headers)
        assert observed.status_code == 200 and observed.json()['latest_observation']['document']['proves_original_attempt'] is False
    assert len(labelled.label_mutations) == 1


def test_gitlab_label_action_is_explicitly_unsupported_without_changing_existing_comment(source, monkeypatch):
    service = candidate_for(writer_for(source, monkeypatch, 'gitlab'), monkeypatch)
    with pytest.raises(ValueError, match='unsupported'):
        issue_writebacks.prepare_label(service.state, 'demo', 'task', service.revision,
            run_id='original-run', candidate_sha='6' * 40, label_name='candidate-ready')
    assert not any(call['method'] != 'GET' for call in service.calls)
    sent = issue_writebacks.send(service.state, 'demo', service.digest, service.revision, confirm=True)
    assert sent['status'] == 'acknowledged' and len(service.notes) == 1


def test_enterprise_graphql_endpoint_uses_the_original_rest_origin():
    backend = issue_backends.for_binding({'tool': 'github', 'project': 'team/repo',
                                         'api_url': 'https://enterprise.invalid/api/v3'})
    operation = backend.label_operation({}, {'issue_id': 'I_issue', 'label_id': 'LA_label'}, 'client-key')
    assert operation['url'] == 'https://enterprise.invalid/api/graphql'


def test_released_comment_record_loads_with_its_original_intent_attempt_and_result():
    fixture = json.loads((Path(__file__).parent / 'fixtures/issue-comment-v1.json').read_text())
    assert issue_writebacks._record(fixture['row']) == fixture['record']
