"""Exercise the real HTTP seam without accounts, credentials or remote writes."""

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Lock, Thread
from types import SimpleNamespace

import pytest

from ergora import agent_runs, contracts, issue_backends, issues, projects, registrations, tools
from ergora.state import State
from test_registrations import installation, registration


@pytest.fixture
def source(tmp_path):
    service = SimpleNamespace(calls=[], status=200, raw=b'', headers={'ETag': '"r1"'}, on_read=None,
                              on_write=None, drop_write=False, declared_length=None)
    response_lock = Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            with response_lock:
                service.calls.append({'path': self.path, 'headers': dict(self.headers), 'method': self.command})
                if service.on_read:
                    service.on_read()
                self.respond()

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            with response_lock:
                service.calls.append({'path': self.path, 'headers': dict(self.headers), 'method': self.command, 'body': body})
                if service.on_write:
                    service.on_write()
                if service.drop_write:
                    self.close_connection = True
                    return
                self.respond()

        def respond(self):
            self.send_response(service.status)
            for name, value in service.headers.items():
                self.send_header(name, value)
            self.send_header('Content-Length', str(service.declared_length or len(service.raw)))
            self.end_headers()
            try:
                self.wfile.write(service.raw)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Oversize/redirect clients deliberately close without consuming the body.

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    service.url = f'http://127.0.0.1:{server.server_port}'
    repo = tmp_path / 'source-repo'
    subprocess.run(['git', 'init', str(repo)], check=True, capture_output=True)
    service.state = State(tmp_path / 'issue-control')
    projects.create(service.state, 'demo', repo)
    yield service
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def native(provider, body='Full issue text. 完整正文。'):
    common = {'id': 9001, 'title': 'Implement delivery', 'updated_at': '2026-11-11T01:02:03Z'}
    if provider == 'github':
        return {**common, 'number': 7, 'body': body, 'state': 'open',
                'labels': [{'name': 'agent-ready'}, 'design'], 'html_url': 'https://github.com/team/repo/issues/7'}
    return {**common, 'iid': 7, 'issue_type': 'issue', 'description': body, 'state': 'opened',
            'labels': ['agent-ready', 'design'], 'web_url': 'https://gitlab.com/team/sub/repo/-/issues/7'}


def bind(source, provider, *, token_env=None):
    binding = {'tool': provider, 'project': 'team/repo' if provider == 'github' else 'team/sub/repo',
               'api_url': source.url + ('' if provider == 'github' else '/api/v4')}
    if token_env:
        binding['token_env'] = token_env
    projects.bind(source.state, 'demo', 'tracker', binding, source.state.project('demo')['revision'])
    return binding


@pytest.mark.parametrize('provider,auth_header,auth_value,path', [
    ('github', 'Authorization', 'Bearer fixture-token', '/repos/team/repo/issues/7'),
    ('gitlab', 'Private-Token', 'fixture-token', '/api/v4/projects/team%2Fsub%2Frepo/issues/7'),
])
def test_complete_native_identity_and_context_are_shared_without_running_tasks(source, monkeypatch, provider, auth_header, auth_value, path):
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'fixture-token')
    bind(source, provider, token_env='ERGORA_FIXTURE_ISSUE_TOKEN')
    body = '权限与Skill不受工单文本修改。' * 8000
    document = native(provider, body)
    source.raw = json.dumps(document, ensure_ascii=False).encode()
    before = source.state.project('demo')
    observed = issues.show(source.state, 'demo', '7')
    assert observed['issue']['native_id'] == 9001 and observed['source']['issue_id'] == '7'
    assert observed['issue']['body'] == body and observed['issue']['labels'] == ['agent-ready', 'design']
    assert observed['issue']['updated_at'] == document['updated_at'] and observed['context_only'] is True
    assert observed['response'] == {'sha256': hashlib.sha256(source.raw).hexdigest(), 'etag': '"r1"'}
    assert source.calls == [{'path': path, 'headers': source.calls[0]['headers'], 'method': 'GET'}]
    assert source.calls[0]['headers'][auth_header] == auth_value
    assert 'fixture-token' not in json.dumps(observed)
    contracts.validate(observed, contracts.ISSUE_OBSERVATION, 'Public observation')
    document['title'] = 'Edited by a human'
    source.raw = json.dumps(document).encode()
    edited = issues.show(source.state, 'demo', '7')
    assert edited['response']['sha256'] != observed['response']['sha256']
    assert edited['issue']['updated_at'] == observed['issue']['updated_at']
    assert source.state.project('demo') == before and agent_runs.runs(source.state, 'demo') == []
    assert not (source.state.root / 'tasks').exists()


def test_anonymous_read_keeps_the_selected_snapshot_when_binding_changes_during_request(source):
    binding = bind(source, 'github')
    configuration = projects.effective_configuration(source.state.project('demo'))
    source.raw = json.dumps(native('github')).encode()
    source.on_read = lambda: projects.bind(source.state, 'demo', 'tracker', {'tool': 'manual'}, 2)
    observed = issues.show(source.state, 'demo', '7')
    assert observed['project'] == {'id': 'demo', 'revision': 2}
    assert observed['configuration_sha256'] == configuration['sha256']
    assert observed['source']['project'] == binding['project']
    assert not {'Authorization', 'Private-Token'} & source.calls[0]['headers'].keys()
    assert source.state.project('demo')['revision'] == 3
    with pytest.raises(ValueError, match='tracker binding'):
        issues.show(source.state, 'demo', '7')
    assert len(source.calls) == 1


def test_credentials_and_redirects_cannot_escape_into_errors_or_another_request(source, monkeypatch):
    bind(source, 'github', token_env='ERGORA_FIXTURE_ISSUE_TOKEN')
    monkeypatch.delenv('ERGORA_FIXTURE_ISSUE_TOKEN', raising=False)
    with pytest.raises(ValueError, match='environment variable'):
        issues.show(source.state, 'demo', '7')
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'not-a-real-secret\r\nInjected: value')
    with pytest.raises(ValueError) as invalid:
        issues.show(source.state, 'demo', '7')
    assert 'not-a-real-secret' not in str(invalid.value) and source.calls == []
    monkeypatch.setenv('ERGORA_FIXTURE_ISSUE_TOKEN', 'fixture-token')
    source.status = 302
    source.headers['Location'] = source.url + '/credential-target'
    with pytest.raises(ValueError, match='HTTP 302'):
        issues.show(source.state, 'demo', '7')
    assert [call['path'] for call in source.calls] == ['/repos/team/repo/issues/7']


@pytest.mark.parametrize('scenario', ['wrong-number', 'global-id-as-iid', 'pull-request', 'labels-as-text', 'incident', 'oversize', 'truncated', 'unavailable'])
def test_untrusted_or_incomplete_responses_never_become_observations(source, scenario):
    provider = 'gitlab' if scenario in ('global-id-as-iid', 'labels-as-text', 'incident') else 'github'
    bind(source, provider)
    document = native(provider)
    if scenario == 'wrong-number':
        document['number'] = 8
    elif scenario == 'global-id-as-iid':
        document['iid'] = document['id']
    elif scenario == 'pull-request':
        document['pull_request'] = {'url': 'https://example.invalid/pr'}
    elif scenario == 'labels-as-text':
        document['labels'] = 'agent-ready'
    elif scenario == 'incident':
        document['issue_type'] = 'incident'
    source.raw = json.dumps(document).encode() if scenario != 'oversize' else b'x' * (1_048_576 + 1)
    if scenario == 'truncated':
        source.declared_length = len(source.raw) + 100
    if scenario == 'unavailable':
        source.status = 503
        source.raw = b'provider-internal-sensitive-error'
    before = source.state.project('demo')
    with pytest.raises(ValueError) as rejected:
        issues.show(source.state, 'demo', '7')
    assert 'provider-internal-sensitive-error' not in str(rejected.value)
    assert len(source.calls) == 1 and source.state.project('demo') == before


def test_a_registered_project_cannot_silently_read_another_namespace(source, registration):
    state, definition = registration
    definition['tracker'] = {'kind': 'github', 'project': 'team/repo'}
    registrations.register(state, definition, 0)
    source.state = state
    binding = bind(source, 'github')
    source.raw = json.dumps(native('github')).encode()
    assert issues.show(state, 'demo', '7')['source']['project'] == 'team/repo'
    projects.bind(state, 'demo', 'tracker', {**binding, 'project': 'other/repo'}, 2)
    with pytest.raises(ValueError, match='registered project namespace'):
        issues.show(state, 'demo', '7')
    assert len(source.calls) == 1


def test_cli_http_and_descriptors_share_the_actual_read_use_case(source):
    pytest.importorskip('fastapi')
    pytest.importorskip('httpx')
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    bind(source, 'gitlab')
    source.raw = json.dumps(native('gitlab', None)).encode()
    result = subprocess.run([sys.executable, '-m', 'ergora', '--home', str(source.state.root),
                             'issue', 'show', 'demo', '7'], capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert result.returncode == 0, result.stderr
    cli = json.loads(result.stdout)
    with TestClient(create_app(source.state.root), base_url='http://127.0.0.1:8977') as client:
        response = client.get('/api/projects/demo/issues/7')
        assert response.status_code == 200
        http = response.json()
        assert cli.pop('observed_at') and http.pop('observed_at')
        assert http == cli
        bootstrap = client.get('/api/bootstrap').json()
        tracker = bootstrap['tools']['tracker']
        assert {item['tool'] for item in tracker} == {'manual', 'github', 'gitlab'}
        assert all('issue.show' in item['operations'] for item in tracker if item['tool'] != 'manual')
    assert cli['issue']['body'] == ''
    assert len(source.calls) == 2 and {item['method'] for item in source.calls} == {'GET'}
    before = len(source.calls)
    check = next(item for item in tools.doctor(source.state, 'demo')['checks'] if item['layer'] == 'tracker')
    assert check['authentication'] == 'not_required' and check['connectivity'] == 'not_checked'
    assert len(source.calls) == before
