"""Read pending plan evidence with real SDK messages and lightweight local files."""

import asyncio
from copy import deepcopy
import hashlib
import io
import json
import sys
from types import SimpleNamespace

import pytest

from ergora import reference, reference_task_approval, tasks
from ergora.reference_task_creation import _Creation


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal task operations use Linux/WSL2')


@pytest.fixture
def pending_plan(tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio.api.common.v1 import Payload
    from temporalio.api.history.v1 import History, HistoryEvent
    from temporalio.api.workflowservice.v1 import GetWorkflowExecutionHistoryResponse
    from temporalio.client import FetchWorkflowHistoryEventsInput, WorkflowExecutionStatus, WorkflowHistoryEventAsyncIterator
    from temporalio.converter import DataConverter, PayloadCodec

    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from dev_platform import adapter
    from dev_platform.contracts import canonical_sha

    creation = _Creation.__new__(_Creation)
    creation.root, creation.task_id, creation.adapter, creation.sha = tmp_path, 'task-one', adapter, canonical_sha
    creation.project = {'id': 'demo', 'revision': 3}
    creation.config = tmp_path / 'config'
    spec = {'request': {'task_id': creation.task_id}, 'request_sha256': 'a' * 64, 'profile_sha256': 'b' * 64,
            'profile': {'artifacts_by_stage': {'plan': ['execution-plan', 'ownership-map', 'rollback-plan']}}}
    context = {'task_id': 'task-one', 'stage': 'plan', 'request_sha256': spec['request_sha256'],
               'profile_sha256': spec['profile_sha256'], 'spec': deepcopy(spec), 'job_id': 'task-one-plan'}
    data = SimpleNamespace(creation=creation, spec=spec, context=context, pages=[], decoded=0,
                           history='normal', values=None, queried=0, looked_up=0)

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    data.write = write
    write(creation.config / 'adapter.json', {
        **{name: str(creation.path(name)) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')},
        'trusted_receipts': True,
    })
    data.receipt_path = tmp_path / 'receipts/task-one/task-one-plan.json'
    data.envelope_path = tmp_path / 'requests/task-one/task-one-plan.json'
    data.receipt = {'schema_version': 1, 'job_id': context['job_id'], 'job_sha256': canonical_sha(context),
                    'state': 'SUCCEEDED', 'artifacts': []}
    for name in spec['profile']['artifacts_by_stage']['plan']:
        raw = ('审阅 ' + name + '\n').encode('utf-8')
        path = tmp_path / ('artifacts/task-one/' + name + '.txt')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        data.receipt['artifacts'].append({'name': name, 'path': 'task-one/' + name + '.txt',
                                          'sha256': hashlib.sha256(raw).hexdigest()})
    write(data.envelope_path, {'schema_version': 1, 'job_id': context['job_id'],
                              'job_sha256': canonical_sha(context), 'context': context})
    data.status = {'phase': 'AWAITING_PLAN_APPROVAL', 'request_sha256': spec['request_sha256']}
    data.payload = {'run_id': 'original-run', 'plan_sha256': ''}

    def save_receipt():
        write(data.receipt_path, data.receipt)
        data.payload['plan_sha256'] = data.status['plan_sha256'] = canonical_sha(data.receipt)

    data.save_receipt = save_receipt
    save_receipt()

    class Codec(PayloadCodec):
        async def encode(self, payloads):
            return [Payload(metadata={'encoding': b'test/codec'}, data=p.SerializeToString()) for p in payloads]

        async def decode(self, payloads):
            data.decoded += 1
            return [Payload.FromString(p.data) for p in payloads]

    converter = DataConverter(payload_codec=Codec())

    async def events():
        result = [HistoryEvent(event_id=i) for i in range(1, 8)]
        result[0].workflow_execution_started_event_attributes.SetInParent()
        result[1].timer_started_event_attributes.SetInParent()
        submit = getattr(data, 'submit_activity', data.input.submit_activity)
        for event, name, values in ((result[2], submit, [{'stage': 'inventory'}]),
                                    (result[3], 'dev_validate', [spec]),
                                    (result[4], submit, data.values if data.values is not None else [data.context])):
            scheduled = event.activity_task_scheduled_event_attributes
            scheduled.activity_type.name = name
            scheduled.input.payloads.extend(await converter.encode(values))
        if data.history == 'gap':
            result.pop(1)
        elif data.history == 'no-start':
            result[0].ClearField('workflow_execution_started_event_attributes')
        elif data.history == 'no-plan':
            result = result[:4]
        return result

    class HistoryService:
        async def get_workflow_execution_history(self, request, **kwargs):
            assert request.execution.workflow_id == 'dev-task/task-one'
            assert request.execution.run_id == 'original-run'
            assert request.maximum_page_size == 100 and request.history_event_filter_type == 1
            assert kwargs['timeout'].total_seconds() == 20
            data.pages.append(request.next_page_token)
            index = int(request.next_page_token or b'0')
            history = await events()
            return GetWorkflowExecutionHistoryResponse(history=History(events=history[index:index + 2]),
                next_page_token=str(index + 2).encode() if index + 2 < len(history) else b'')

    client = SimpleNamespace(namespace='test', workflow_service=HistoryService())

    class Handle:
        async def query(self, query, **kwargs):
            from dev_platform.workflow import DevelopmentWorkflow
            assert query is DevelopmentWorkflow.status and kwargs['rpc_timeout'].total_seconds() == 20
            data.queried += 1
            return data.status

        def fetch_history_events(self, **kwargs):
            return WorkflowHistoryEventAsyncIterator(client, FetchWorkflowHistoryEventsInput(
                id='dev-task/task-one', run_id='original-run', page_size=kwargs['page_size'],
                next_page_token=None, wait_new_event=False, event_filter_type=1, skip_archival=False,
                rpc_metadata={}, rpc_timeout=kwargs['rpc_timeout']))

    intent = {'workflow_id': 'dev-task/task-one'}
    data.description = SimpleNamespace(status=WorkflowExecutionStatus.RUNNING)

    async def lookup(saved_intent, run_id):
        assert saved_intent is intent and run_id == 'original-run'
        data.looked_up += 1
        return Handle(), data.description, converter

    from ergora.reference_inputs import execution_input

    data.input = execution_input(spec)
    submission = SimpleNamespace(creation=creation, spec=spec, input=data.input,
                                submitted=lambda: (intent, 'original-run'), lookup_run=lookup)
    data.submission = submission
    monkeypatch.setattr(reference_task_approval, '_Submission', lambda payload: submission)
    return data


def inspect(data):
    return asyncio.run(reference_task_approval._plan(data.payload))


def snapshot(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_exact_receipt_and_full_utf8_materials_are_read_only_and_history_stops_at_plan(pending_plan):
    data = pending_plan
    before = snapshot(data.creation.root)
    result = inspect(data)
    assert result['read_only'] is True and result['run_id'] == 'original-run'
    assert result['plan_sha256'] == data.payload['plan_sha256'] == data.creation.sha(result['receipt'])
    assert result['history_plan_event_id'] == 5 and data.pages == [b'', b'2', b'4']
    assert data.decoded == 2 and data.queried == data.looked_up == 1
    assert [m['name'] for m in result['materials']] == data.spec['profile']['artifacts_by_stage']['plan']
    for material in result['materials']:
        raw = material['text'].encode('utf-8')
        assert material['bytes'] == len(raw) and hashlib.sha256(raw).hexdigest() == material['sha256']
    assert snapshot(data.creation.root) == before


@pytest.mark.parametrize('change,error', [
    ('run', 'original submitted run'), ('closed', 'awaiting an owner decision'),
    ('phase', 'exact plan'), ('plan', 'exact plan'), ('request', 'exact plan'),
    ('gap', 'history prefix'), ('no-start', 'history prefix'), ('no-plan', 'no submitted plan job'),
    ('context', 'recorded task spec'), ('multiple-contexts', 'single job context'),
    ('envelope', 'request envelope'), ('receipt', 'Plan receipt differs'),
    ('job', 'Plan receipt differs'), ('missing', 'missing a required review artifact'),
])
def test_wrong_run_history_and_persisted_identity_fail_without_writes(pending_plan, change, error):
    data = pending_plan
    if change == 'run':
        data.payload['run_id'] = 'other-run'
    elif change == 'closed':
        from temporalio.client import WorkflowExecutionStatus
        data.description.status = WorkflowExecutionStatus.COMPLETED
    elif change == 'phase':
        data.status['phase'] = 'IMPLEMENTING'
    elif change in ('plan', 'request'):
        data.status[change + '_sha256'] = 'c' * 64
    elif change in ('gap', 'no-start', 'no-plan'):
        data.history = change
    elif change == 'context':
        data.context['spec']['profile']['schema_version'] = True
    elif change == 'multiple-contexts':
        data.values = [data.context, data.context]
    elif change == 'envelope':
        data.write(data.envelope_path, {'context': data.context})
    elif change == 'receipt':
        data.write(data.receipt_path, {**data.receipt, 'state': 'FAILED'})
    elif change == 'job':
        data.receipt['job_sha256'] = 'c' * 64
        data.save_receipt()
    elif change == 'missing':
        data.receipt['artifacts'].pop()
        data.save_receipt()
    before = snapshot(data.creation.root)
    with pytest.raises(ValueError, match=error):
        inspect(data)
    assert snapshot(data.creation.root) == before


@pytest.mark.parametrize('kind,error', [
    ('digest', 'receipt digest'), ('utf8', 'utf-8'), ('oversize', 'size limit'),
    ('response-size', 'read limit'), ('traversal', 'Noncanonical artifact path'),
    ('symlink', 'Symlinks are not accepted'), ('directory', 'directory|regular file'),
])
def test_material_bytes_limits_encoding_and_safe_paths_are_enforced(pending_plan, kind, error):
    data = pending_plan
    artifact = data.receipt['artifacts'][0]
    path = data.creation.path('artifacts/' + artifact['path'])
    if kind in ('digest', 'utf8', 'oversize', 'response-size'):
        raw = {'digest': b'changed', 'utf8': b'\xff', 'oversize': b'x' * 262_145,
               'response-size': b'\0' * 200_000}[kind]
        path.write_bytes(raw)
        if kind != 'digest':
            artifact['sha256'] = hashlib.sha256(raw).hexdigest()
            data.save_receipt()
    elif kind == 'traversal':
        artifact['path'] = '../outside.txt'
        data.save_receipt()
    elif kind == 'symlink':
        target = path.with_suffix('.original')
        path.rename(target)
        path.symlink_to(target)
    elif kind == 'directory':
        path.unlink()
        path.mkdir()
    before = snapshot(data.creation.root)
    with pytest.raises((ValueError, OSError), match=error):
        inspect(data)
    assert snapshot(data.creation.root) == before


def test_material_at_the_byte_limit_is_returned_in_full(pending_plan):
    data = pending_plan
    artifact = data.receipt['artifacts'][0]
    raw = b'x' * 262_144
    data.creation.path('artifacts/' + artifact['path']).write_bytes(raw)
    artifact['sha256'] = hashlib.sha256(raw).hexdigest()
    data.save_receipt()
    result = inspect(data)
    assert result['materials'][0]['text'].encode('utf-8') == raw


@pytest.mark.parametrize('failure,message', [
    ('environment-timeout', 'Plan inspection timed out'), ('not-found', 'Original plan run was not found'),
    ('rpc', 'Plan inspection RPC failed: UNAVAILABLE'),
])
def test_native_main_distinguishes_read_failures_from_decision_recovery(pending_plan, monkeypatch, failure, message):
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/local'))
    from agent_platform import core
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError, RPCStatusCode

    def environment():
        if failure == 'environment-timeout':
            raise TimeoutError()
        return {}

    async def fail(payload):
        if failure == 'not-found':
            raise RuntimeNotFound('missing')
        raise RPCError('unavailable', RPCStatusCode.UNAVAILABLE, b'')

    monkeypatch.setattr(core, 'environment', environment)
    monkeypatch.setattr(reference_task_approval, '_plan', fail)
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps({'operation': 'inspect-plan', 'timeout': 1})))
    with pytest.raises(SystemExit, match=message):
        reference_task_approval.main()


@pytest.mark.parametrize('kwargs,error', [
    ({'run_id': ''}, 'Run ID'), ({'plan_sha256': 'bad'}, 'Plan must be'),
    ({'timeout': True}, '1–60'), ({'timeout': 0}, '1–60'), ({'timeout': 61}, '1–60'),
])
def test_invalid_inputs_fail_before_project_or_native_access(kwargs, error):
    with pytest.raises(ValueError, match=error):
        tasks.plan(None, 'demo', 'task-one', **{'run_id': 'original-run', 'plan_sha256': 'a' * 64, **kwargs})


def test_cli_and_api_forward_the_exact_read_request_without_confirmation(tmp_path, monkeypatch, capsys):
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora import cli
    from ergora.web import create_app

    seen = []
    monkeypatch.setattr(tasks, '_project', lambda state, project: {'id': project})

    def read(project, home, payload, *, timeout):
        seen.append((project, home, payload, timeout))
        return {'read_only': True, **payload}

    monkeypatch.setattr(reference, 'task_plan', read)
    args = ['--home', str(tmp_path), 'task', 'plan', 'demo', 'task-one', '--run-id', 'original-run',
            '--plan-sha256', 'a' * 64, '--timeout', '7']
    assert cli.main(args) == 0
    assert json.loads(capsys.readouterr().out)['read_only'] is True
    client = TestClient(create_app(tmp_path), base_url='http://127.0.0.1')
    response = client.get('/api/projects/demo/tasks/task-one/plan',
                          params={'run_id': 'original-run', 'plan_sha256': 'a' * 64, 'timeout': 7})
    assert response.status_code == 200 and response.json()['read_only'] is True
    assert len(seen) == 2 and seen[0] == seen[1]
    assert client.get('/api/projects/demo/tasks/task-one/plan').status_code == 422
    assert client.get('/api/projects/demo/tasks/task-one/plan',
                      params={'run_id': 'original-run', 'plan_sha256': 'bad'}).status_code == 400
    assert len(seen) == 2
