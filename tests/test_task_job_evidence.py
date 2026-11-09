"""Read one original job using real SDK messages and the native file adapter."""

import asyncio
from copy import deepcopy
import hashlib
import io
import json
import sys

import pytest

from ergora import reference, reference_task_approval, reference_task_evidence, tasks
from test_task_plan import pending_plan, snapshot


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal task operations use Linux/WSL2')


@pytest.fixture
def original_job(pending_plan, monkeypatch):
    data = pending_plan
    creation = data.creation
    data.receipt.update(actor={'id': 'trusted', 'session_id': 'job-session', 'kind': 'ci', 'role': 'planner'},
                        candidate_sha='a' * 40, checks=[])
    data.save_receipt()
    data.payload = {'run_id': 'original-run', 'event_id': 5, 'artifact': None, 'receipt_sha256': None,
                    'offset': 0, 'limit': 8192}
    monkeypatch.setattr(reference_task_evidence, '_Submission', reference_task_approval._Submission)
    return data


def read(data, **changes):
    return asyncio.run(reference_task_evidence._job({**data.payload, **changes}))


@pytest.mark.parametrize('status', ['RUNNING', 'COMPLETED', 'FAILED'])
def test_original_job_and_published_receipt_are_read_only_without_claiming_workflow_acceptance(original_job, status):
    from temporalio.client import WorkflowExecutionStatus

    data = original_job
    data.description.status = WorkflowExecutionStatus[status]
    before = snapshot(data.creation.root)
    result = read(data)
    assert result['read_only'] is True and result['temporal_status'] == status
    assert result['receipt_status'] == 'published' and result['receipt'] == data.receipt
    assert result['receipt_sha256'] == data.creation.sha(data.receipt)
    assert result['job_id'] == data.context['job_id'] and result['job_sha256'] == data.creation.sha(data.context)
    assert result['history_event_id'] == 5 and result['artifact'] is None
    assert result['execution_success'] is result['workflow_receipt_accepted'] is None
    assert 'context' not in result and 'spec' not in result
    assert data.pages == [b'', b'2', b'4'] and data.decoded == data.looked_up == 1
    assert snapshot(data.creation.root) == before


def test_character_windows_reconstruct_the_same_hashed_utf8_text_with_a_pinned_receipt(original_job):
    data = original_job
    text = '审阅🧪e\u0301\n' * 4
    artifact = data.receipt['artifacts'][0]
    raw = text.encode('utf-8')
    data.creation.path('artifacts/' + artifact['path']).write_bytes(raw)
    artifact['sha256'] = hashlib.sha256(raw).hexdigest()
    data.save_receipt()
    digest = read(data)['receipt_sha256']
    offset, parts = 0, []
    before = snapshot(data.creation.root)
    while True:
        selected = read(data, artifact=artifact['name'], receipt_sha256=digest, offset=offset, limit=3)['artifact']
        assert selected['sha256'] == artifact['sha256'] and selected['bytes'] == len(raw)
        assert selected['characters'] == len(text) and len(selected['text']) <= 3
        assert selected['offset'] == offset
        parts.append(selected['text'])
        if selected['next_offset'] is None:
            break
        offset = selected['next_offset']
    assert ''.join(parts).encode('utf-8') == raw
    end = read(data, artifact=artifact['name'], receipt_sha256=digest, offset=len(text))['artifact']
    assert end['text'] == '' and end['next_offset'] is None
    assert snapshot(data.creation.root) == before
    data.receipt['detail'] = 'new observation'
    data.save_receipt()
    with pytest.raises(ValueError, match='selected original observation'):
        read(data, artifact=artifact['name'], receipt_sha256=digest)


def test_work_unit_suffix_keeps_its_original_stage_and_context(original_job):
    data = original_job
    data.spec['profile']['artifacts_by_stage']['work'] = ['implementation-record']
    data.context.update(stage='work:unit-one', spec=deepcopy(data.spec))
    digest = data.creation.sha(data.context)
    data.write(data.envelope_path, {'schema_version': 1, 'job_id': data.context['job_id'],
                                    'job_sha256': digest, 'context': data.context})
    data.receipt['job_sha256'] = digest
    data.save_receipt()
    assert read(data)['stage'] == 'work:unit-one'


@pytest.mark.parametrize('change,error', [
    ('run', 'original submitted run'), ('gap', 'continuous history prefix'),
    ('no-start', 'continuous history prefix'), ('not-job', 'dev_submit'),
    ('absent', 'currently visible original history'), ('context', 'recorded task spec'),
    ('stage', 'recorded task spec'), ('multiple', 'single context'),
    ('envelope', 'request envelope'), ('receipt', 'another job/context'),
    ('roots', 'registered execution state'),
])
def test_wrong_history_or_trusted_file_identity_fails_without_writes(original_job, change, error):
    data = original_job
    if change == 'run': data.payload['run_id'] = 'different-run'
    elif change in ('gap', 'no-start'): data.history = change
    elif change == 'not-job': data.payload['event_id'] = 4
    elif change == 'absent': data.payload['event_id'] = 9
    elif change == 'context': data.context['spec']['unexpected'] = True
    elif change == 'stage': data.context['stage'] = 'unknown'
    elif change == 'multiple': data.values = [data.context, data.context]
    elif change == 'envelope': data.write(data.envelope_path, {})
    elif change == 'receipt':
        data.receipt['job_sha256'] = 'c' * 64
        data.save_receipt()
    elif change == 'roots':
        path = data.creation.config / 'adapter.json'
        config = json.loads(path.read_text())
        config['artifacts'] = str(data.creation.root / 'other-artifacts')
        data.write(path, config)
    before = snapshot(data.creation.root)
    with pytest.raises(ValueError, match=error): read(data)
    assert snapshot(data.creation.root) == before


def test_missing_receipt_is_unknown_evidence_and_not_a_success(original_job):
    data = original_job
    data.receipt_path.unlink()
    result = read(data)
    assert result['receipt_status'] == 'missing' and result['receipt'] is result['receipt_sha256'] is None
    assert result['execution_success'] is None
    with pytest.raises(ValueError, match='selected original observation'):
        read(data, artifact='execution-plan', receipt_sha256='a' * 64)


def test_missing_original_run_does_not_read_files_or_invent_a_job(original_job):
    from dev_platform.runtime import RuntimeNotFound

    data = original_job
    submission = reference_task_evidence._Submission({})
    async def missing(*args):
        raise RuntimeNotFound('missing')
    submission.lookup_run = missing
    result = read(data)
    assert result['runtime_status'] == 'not_found' and result['execution_success'] is None
    assert 'job_id' not in result and data.pages == []


@pytest.mark.parametrize('kind,error', [
    ('digest', 'receipt digest'), ('utf8', 'utf-8'), ('nul', 'NUL'), ('oversize', 'size limit'),
    ('traversal', 'Noncanonical artifact path'), ('symlink', 'Symlinks are not accepted'),
    ('missing', 'No such file'), ('unknown', 'absent from the original job receipt'),
    ('offset', 'exceeds the original text length'),
])
def test_text_and_safe_path_boundaries_are_enforced(original_job, kind, error):
    data = original_job
    artifact = data.receipt['artifacts'][0]
    path = data.creation.path('artifacts/' + artifact['path'])
    selected_name, offset = artifact['name'], 0
    if kind in ('digest', 'utf8', 'nul', 'oversize'):
        raw = b'x' * 16_777_217 if kind == 'oversize' else {
            'digest': b'changed', 'utf8': b'\xff', 'nul': b'hello\0world'}[kind]
        path.write_bytes(raw)
        if kind != 'digest': artifact['sha256'] = hashlib.sha256(raw).hexdigest()
    elif kind == 'traversal': artifact['path'] = '../outside.txt'
    elif kind == 'symlink':
        target = path.with_suffix('.original')
        path.rename(target)
        path.symlink_to(target)
    elif kind == 'missing': path.unlink()
    elif kind == 'unknown': selected_name = '../outside.txt'
    elif kind == 'offset': offset = 9999
    data.save_receipt()
    before = snapshot(data.creation.root)
    with pytest.raises((OSError, ValueError), match=error):
        read(data, artifact=selected_name, receipt_sha256=data.creation.sha(data.receipt), offset=offset)
    assert snapshot(data.creation.root) == before


def test_full_sized_artifact_returns_only_the_requested_window(original_job):
    data = original_job
    artifact = data.receipt['artifacts'][0]
    raw = b'x' * 16_777_216
    data.creation.path('artifacts/' + artifact['path']).write_bytes(raw)
    artifact['sha256'] = hashlib.sha256(raw).hexdigest()
    data.save_receipt()
    selected = read(data, artifact=artifact['name'], receipt_sha256=data.creation.sha(data.receipt),
                    offset=len(raw) - 16_384, limit=16_384)['artifact']
    assert selected['bytes'] == len(raw) and selected['text'] == 'x' * 16_384 and selected['next_offset'] is None


def test_cli_and_http_forward_the_same_read_only_window(tmp_path, monkeypatch, capsys):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora import cli
    from ergora.web import create_app

    seen = []
    monkeypatch.setattr(tasks, '_project', lambda state, project: {'id': project})
    def native(project, home, payload, *, timeout):
        seen.append((project, home, payload, timeout))
        return {'read_only': True, **payload}
    monkeypatch.setattr(reference, 'task_job', native)
    args = ['--home', str(tmp_path), 'task', 'job', 'demo', 'task-one', '--run-id', 'original-run',
            '--event-id', '5', '--artifact', 'model-log', '--receipt-sha256', 'a' * 64,
            '--offset', '7', '--limit', '3', '--timeout', '9']
    assert cli.main(args) == 0 and json.loads(capsys.readouterr().out)['read_only'] is True
    client = TestClient(create_app(tmp_path), base_url='http://127.0.0.1')
    url = '/api/projects/demo/tasks/task-one/jobs/5'
    response = client.get(url, params={'run_id': 'original-run', 'artifact': 'model-log',
                                      'receipt_sha256': 'a' * 64, 'offset': 7, 'limit': 3, 'timeout': 9})
    assert response.status_code == 200 and response.json()['read_only'] is True
    assert len(seen) == 2 and seen[0] == seen[1]
    assert client.get(url).status_code == 422
    assert client.get(url, params={'run_id': 'original-run', 'artifact': 'model-log'}).status_code == 400
    assert len(seen) == 2


@pytest.mark.parametrize('failure,message', [
    ('timeout', 'Job evidence query timed out'), ('rpc', 'Job evidence query RPC failed: UNAVAILABLE'),
])
def test_native_read_failures_do_not_offer_write_recovery(original_job, monkeypatch, failure, message):
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/local'))
    from agent_platform import core
    from temporalio.service import RPCError, RPCStatusCode

    monkeypatch.setattr(core, 'environment', lambda: {})
    async def fail(payload):
        if failure == 'timeout': raise TimeoutError()
        raise RPCError('unavailable', RPCStatusCode.UNAVAILABLE, b'')
    monkeypatch.setattr(reference_task_evidence, '_job', fail)
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps({'timeout': 1})))
    with pytest.raises(SystemExit, match=message): reference_task_evidence.main()
