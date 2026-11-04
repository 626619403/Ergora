"""HTTP downloads adapt the existing collector and clean each request's files."""

import hashlib
from types import SimpleNamespace

import pytest

pytest.importorskip('fastapi')
pytest.importorskip('httpx')
from fastapi.testclient import TestClient

from ergora import handoff, tasks
from ergora.web import create_app
from test_handoff import evidence


@pytest.fixture
def download(evidence, tmp_path, monkeypatch):
    calls = []
    def collect(state, project, task, *, run_id, output, timeout):
        calls.append((project, task, run_id, timeout, output))
        return handoff.create(evidence[0], lambda artifact: evidence[1], output)
    monkeypatch.setattr(tasks, 'handoff', collect)
    headers = {'Origin': 'http://127.0.0.1:8977', 'X-Ergora-Request': '1'}
    with TestClient(create_app(tmp_path / 'control'), base_url='http://127.0.0.1:8977', headers=headers) as client:
        yield SimpleNamespace(client=client, calls=calls, url='/api/projects/demo/tasks/task-one/handoff')


def test_download_returns_verifiable_packet_and_cleans_before_response(download, tmp_path):
    response = download.client.post(download.url, json={'run_id': 'original-run', 'timeout': 9})
    assert response.status_code == 200, response.text
    assert response.headers['content-type'] == 'application/zip'
    assert response.headers['content-disposition'] == 'attachment; filename="ergora-handoff.zip"'
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-content-type-options'] == 'nosniff'
    digest = response.headers['x-ergora-handoff-sha256']
    assert digest == hashlib.sha256(response.content).hexdigest()
    assert len(download.calls) == 1
    project, task, run_id, timeout, temporary = download.calls[0]
    assert (project, task, run_id, timeout) == ('demo', 'task-one', 'original-run', 9)
    assert not temporary.exists() and not temporary.parent.exists()
    assert str(temporary.parent).encode() not in response.content
    saved = tmp_path / 'download.zip'
    saved.write_bytes(response.content)
    verified = handoff.verify(saved, sha256=digest)
    assert verified['project'] == project and verified['run_id'] == run_id
    assert verified['execution_success'] is None and verified['origin_authenticated'] is False


@pytest.mark.parametrize('body', [{}, {'run_id': ''}, {'run_id': 'x' * 129},
    {'run_id': 'original-run', 'timeout': True}, {'run_id': 'original-run', 'timeout': 0},
    {'run_id': 'original-run', 'timeout': 61}, {'run_id': 'original-run', 'output': '/arbitrary/path'},
    {'run_id': 'original-run', 'source': '/arbitrary/path'}])
def test_invalid_download_body_does_not_collect(download, body):
    assert download.client.post(download.url, json=body).status_code == 422
    assert download.calls == []


@pytest.mark.parametrize('headers', [{'X-Ergora-Request': ''}, {'Origin': 'https://foreign.example'},
                                   {'Sec-Fetch-Site': 'cross-site'}])
def test_download_preserves_local_request_boundary(download, headers):
    assert download.client.post(download.url, json={'run_id': 'original-run'}, headers=headers).status_code == 403
    assert download.calls == []


@pytest.mark.parametrize('failure', ['collection', 'oversized', 'changed'])
def test_download_errors_remove_partial_files_and_return_no_packet(download, monkeypatch, failure):
    paths = []
    def fail(state, project, task, *, run_id, output, timeout):
        paths.append(output)
        raw = b'123456789'
        output.write_bytes(raw)
        if failure == 'collection':
            raise ValueError('Collection fixture failed')
        return {'sha256': '0' * 64 if failure == 'changed' else hashlib.sha256(raw).hexdigest()}
    if failure == 'oversized':
        monkeypatch.setattr(handoff, 'PACKET_LIMIT', 8)
    monkeypatch.setattr(tasks, 'handoff', fail)
    response = download.client.post(download.url, json={'run_id': 'original-run'})
    assert response.status_code == 400, response.text
    assert 'error' in response.json() and 'x-ergora-handoff-sha256' not in response.headers
    assert len(paths) == 1 and not paths[0].parent.exists()


def test_get_cannot_start_collection(download):
    assert download.client.get(download.url).status_code == 405
    assert download.calls == []
