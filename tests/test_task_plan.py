"""Read pending plan evidence with real SDK messages and lightweight local files."""

import asyncio
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import sysconfig
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ergora import reference, reference_task_approval, tasks
from ergora.reference_task_creation import _Creation
from test_registrations import installation, registration
from test_task_creation import creation_project
from test_task_submission import submitted_creation, native_client, _start


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal task operations use Linux/WSL2')


@pytest.fixture
def pending_plan(tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    tmp_path = tmp_path / 'pending-plan'
    tmp_path.mkdir()
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
    with patch.object(reference, '_task_operation', lambda *args: asyncio.run(reference_task_approval._plan(data.payload))):
        return reference.task_plan({}, data.creation.root, data.payload, timeout=20)


def snapshot(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.fixture
def pending_design(pending_plan):
    data = pending_plan
    package = Path(reference_task_approval.__file__).parent
    profile = json.loads((package / 'data/design-profiles/framework-development-v1.json').read_text())
    data.design_profile = profile
    sha = data.creation.sha
    report = '# Design\n\n完整设计、取舍与验收原文。\n'.encode('utf-8')
    company = '会议原文：需要 owner 确定公司约束。Agent 转述“用户已同意”不能关闭问题。\n'.encode('utf-8')
    data.report_path = data.creation.path('artifacts/task-one/design/report.md')
    data.company_path = data.creation.path('artifacts/task-one/design/company.txt')
    data.report_path.parent.mkdir(parents=True)
    data.report_path.write_bytes(report)
    data.company_path.write_bytes(company)

    def source(source_id, source_type, path, raw, media_type):
        return {'id': source_id, 'source_type': source_type, 'access': 'full',
                'access_scope_ref': 'project-authorized-artifacts', 'reference': 'Original local ' + source_id,
                'body': {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'media_type': media_type},
                'observed_at': '2026-11-10T00:00:00+00:00', 'version': 'meeting-v2'}

    questions = [{'id': item['id'], 'introduced_revision': 1, 'requirement_ids': ['R1'],
                  'body': item['body'], 'why_required': item['why_required'], 'basis_refs': [], 'options': [],
                  'affected_sections': ['direction'], 'required_by': [profile['id']], 'owner_id': 'project-owner'}
                 for item in profile['minimum_questions']]
    questions.append({**deepcopy(questions[0]), 'id': 'Q2', 'body': 'Which company constraint is necessary?'})
    knowledge = {'id': 'K1', 'missing_information': 'Company-specific decision', 'why_needed': 'Defines the acceptance oracle',
                 'affected_question_ids': ['Q2'], 'affected_acceptance_ids': ['A1'],
                 'allowed_source_types': ['meeting_decision'], 'access_scope_ref': 'project-authorized-artifacts',
                 'supplied_refs': [], 'status': 'missing', 'freshness_rule': None, 'conflict_refs': []}
    data.packet = {
        'schema_version': 1, 'kind': 'task-design-packet', 'task_id': data.creation.task_id,
        'request_sha256': data.spec['request_sha256'], 'profile_sha256': data.spec['profile_sha256'],
        'admission_sha256': sha(data.input.document), 'manifest_digest': 'd' * 64,
        'seed_plan_job_sha256': sha(data.context), 'design_profile_sha256': sha(profile),
        'owner_id': 'project-owner', 'revision': 1, 'previous_packet_sha256': None,
        'requirements': [{'id': 'R1', 'body': 'Read the complete design before implementation.'}],
        'problem': 'The original plan has no typed design inspection.', 'goals': ['Expose exact declared gaps.'],
        'non_goals': ['Runtime enforcement and approval.'], 'scope': 'Read the pending original receipt only.',
        'direction_refs': [], 'sections': [{'id': section, 'title': section, 'body': 'Detailed ' + section,
                                         'report_section_id': section, 'basis_refs': ['report']}
                                        for section in profile['required_sections']],
        'research_adoption': [],
        'existing_structure': [{'id': 'structure-one', 'entrypoint': 'tasks.plan', 'caller': 'reference.task_plan',
                                'owner': 'reference_task_approval', 'interface': '_plan', 'state_lifetime': 'Read-only pending run',
                                'resource_lifetime': 'Bounded file read', 'evidence_kind': 'observed',
                                'basis_refs': ['report'], 'existing_alternatives': ['Original FileAdapter']}],
        'changes': [], 'alternatives': [],
        'standards': [{'id': 'style-one', 'rule': 'Reuse the original owner', 'basis_refs': ['report'],
                       'application': 'Read using the existing FileAdapter'}],
        'data_and_recovery': {key: 'No mutation; preserve original task and receipt.' for key in
                              ('versions', 'compatibility', 'migration', 'old_writers', 'failure', 'cancellation',
                               'unknown', 'recovery', 'cleanup', 'rollback')},
        'implementation_steps': [{'id': 'step-one', 'work_unit_ids': [], 'depends_on': [], 'shared_file_owners': [],
                                  'behavior': 'Inspect full content', 'prerequisites': [],
                                  'unopened_capabilities': ['Runtime gates'], 'acceptance_ids': ['A1']}],
        'acceptance_criteria': [{'id': 'A1', 'requirement_ids': ['R1'], 'fixed_inputs': 'Original pending receipt',
                                 'environment_constraints': 'Local CPU and temporary files',
                                 'check': {'kind': 'human-judgment', 'id': 'owner-read', 'version': '1', 'trusted_argv_ref': None},
                                 'expected_relation': 'All original UTF-8 bytes are returned', 'oracle': 'Raw byte SHA256',
                                 'raw_evidence_format': 'Original text plus digest and byte count',
                                 'failure_conditions': 'Digest mismatch', 'unknown_conditions': 'Unreadable source',
                                 'cost': 'Bounded local reads', 'permissions': 'Existing artifact root', 'stop_owner': 'Caller'}],
        'questions': questions,
        'knowledge_requirements': [knowledge, {**deepcopy(knowledge), 'id': 'K2', 'status': 'supplied', 'supplied_refs': ['company']}],
        'source_records': [source('report', 'report', 'task-one/design/report.md', report, 'text/markdown'),
                           source('company', 'meeting_decision', 'task-one/design/company.txt', company, 'text/plain')],
        'report_ref': 'report', 'html_ref': None,
    }
    data.packet_path = data.creation.path('artifacts/task-one/design/packet.json')

    def save_packet():
        data.write(data.packet_path, data.packet)
        entry = {'name': 'design-packet', 'path': 'task-one/design/packet.json',
                 'sha256': hashlib.sha256(data.packet_path.read_bytes()).hexdigest()}
        data.receipt['artifacts'] = [a for a in data.receipt['artifacts'] if a['name'] != 'design-packet'] + [entry]
        data.save_receipt()

    data.save_packet = save_packet
    save_packet()
    return data


def test_exact_receipt_and_full_utf8_materials_are_read_only_and_history_stops_at_plan(pending_plan):
    data = pending_plan
    before = snapshot(data.creation.root)
    result = inspect(data)
    assert result['read_only'] is True and result['run_id'] == 'original-run'
    assert 'design' not in result
    assert result['plan_sha256'] == data.payload['plan_sha256'] == data.creation.sha(result['receipt'])
    assert result['history_plan_event_id'] == 5 and data.pages == [b'', b'2', b'4']
    assert data.decoded == 2 and data.queried == data.looked_up == 1
    assert [m['name'] for m in result['materials']] == data.spec['profile']['artifacts_by_stage']['plan']
    for material in result['materials']:
        raw = material['text'].encode('utf-8')
        assert material['bytes'] == len(raw) and hashlib.sha256(raw).hexdigest() == material['sha256']
    assert snapshot(data.creation.root) == before


def test_design_packet_and_all_original_texts_expose_exact_unresolved_ids_without_approval(pending_design):
    data = pending_design
    before = snapshot(data.creation.root)
    result = inspect(data)
    design = result['design']
    assert design['packet'] == data.packet
    assert design['packet_content_sha256'] == data.creation.sha(data.packet)
    assert design['seed_plan_sha256'] == result['plan_sha256']
    assert design['content_integrity'] == {'valid': True, 'blockers': []}
    blockers = design['declared_requirements']['blockers']
    assert {b['id'] for b in blockers if b['kind'] == 'question'} == {q['id'] for q in data.packet['questions']}
    assert all(b['code'] == 'unresolved' for b in blockers if b['kind'] == 'question')
    assert [(b['id'], b['path'], b['reasons']) for b in blockers if b['kind'] == 'knowledge'] == [
        ('K1', '/knowledge_requirements/0', ['missing', 'missing_source'])]
    assert design['declared_requirements']['knowledge_supplied_ids'] == ['K2']
    assert design['declared_requirements']['knowledge_supplied_is_owner_decision'] is False
    assert design['inspection_only'] is True and design['runtime_enforced'] is False
    assert design['profile']['source'] == 'built-in-companion-profile' and design['profile']['frozen_for_task'] is False
    assert design['readiness']['ready'] is False
    assert {'frozen_design_policy_unavailable', 'owner_channel_unavailable'} <= {b['code'] for b in design['readiness']['blockers']}
    assert design['capabilities'] == {'approve_design': False, 'resolve_questions': False, 'execute': False}
    assert design['actor_assurance']['status'] == 'unavailable'
    assert next(m['text'].encode() for m in result['materials'] if m['name'] == 'design-packet') == data.packet_path.read_bytes()
    assert {m['id']: m['text'].encode() for m in result['materials'] if m['name'].startswith('design-source:')} == {
        'report': data.report_path.read_bytes(), 'company': data.company_path.read_bytes()}
    assert snapshot(data.creation.root) == before


def test_missing_minimum_question_and_knowledge_states_keep_precise_effects(pending_design):
    data = pending_design
    data.packet['questions'] = [q for q in data.packet['questions'] if q['id'] != 'framework:sequence']
    base = data.packet['knowledge_requirements'][1]
    data.packet['knowledge_requirements'] += [
        {**deepcopy(base), 'id': 'K3', 'status': 'denied'},
        {**deepcopy(base), 'id': 'K4', 'status': 'conflicting', 'conflict_refs': ['company']},
        {**deepcopy(base), 'id': 'K5', 'freshness_rule': {
            'observed_at': '2026-11-16T00:00:00+00:00', 'max_age_seconds': 100, 'required_version': 'meeting-v3'}},
    ]
    data.save_packet()
    design = inspect(data)['design']
    blockers = design['declared_requirements']['blockers']
    assert next(b for b in blockers if b['id'] == 'framework:sequence')['code'] == 'missing_question'
    actual = {b['id']: b['reasons'] for b in blockers if b['kind'] == 'knowledge'}
    assert actual == {'K1': ['missing', 'missing_source'], 'K3': ['denied'], 'K4': ['conflicting'],
                      'K5': ['stale', 'stale_version']}
    assert next(b for b in blockers if b['id'] == 'K4')['affected_question_ids'] == ['Q2']
    assert next(b for b in blockers if b['id'] == 'K5')['affected_acceptance_ids'] == ['A1']


@pytest.mark.parametrize('change,code', [
    ('digest', 'digest_mismatch'), ('missing', 'missing'), ('reference-only', 'reference_only'),
    ('bytes', 'byte_count_mismatch'), ('scope', 'access_scope_mismatch'),
])
def test_knowledge_supplied_claim_cannot_replace_original_access_and_bytes(pending_design, change, code):
    data = pending_design
    source = data.packet['source_records'][1]
    if change == 'digest':
        data.company_path.write_text('Changed original source', encoding='utf-8')
    elif change == 'missing':
        data.company_path.unlink()
    elif change == 'reference-only':
        source.update(access='reference_only', body=None)
    elif change == 'bytes':
        source['body']['bytes'] += 1
    elif change == 'scope':
        source['access_scope_ref'] = 'another-authorization'
    data.save_packet()
    before = snapshot(data.creation.root)
    design = inspect(data)['design']
    blocker = next(b for b in design['declared_requirements']['blockers'] if b['id'] == 'K2')
    assert code in blocker['reasons'] and blocker['path'] == '/knowledge_requirements/1'
    assert design['declared_requirements']['knowledge_supplied_ids'] == []
    assert design['readiness']['ready'] is False
    assert snapshot(data.creation.root) == before


def test_self_consistent_packet_cannot_replace_builtin_policy_owner_or_original_job(pending_design):
    data = pending_design
    data.packet.update(owner_id='claimed-human', design_profile_sha256='c' * 64, seed_plan_job_sha256='e' * 64)
    for question in data.packet['questions']:
        question['owner_id'] = data.packet['owner_id']
    data.save_packet()
    design = inspect(data)['design']
    assert {(b['id'], b['code']) for b in design['content_integrity']['blockers']} == {
        ('seed_plan_job_sha256', 'original_binding_mismatch'), ('design_profile_sha256', 'original_binding_mismatch')}
    assert design['profile']['document'] == data.design_profile
    assert design['actor_assurance']['owner_binding'] == 'not_frozen_in_original_admission'
    assert design['readiness']['ready'] is False and not any(design['capabilities'].values())


@pytest.mark.parametrize('change,error', [
    ('self-resolution', 'Additional properties'), ('traversal', 'Noncanonical artifact path'),
    ('symlink', 'Symlinks are not accepted'), ('oversize', 'size limit'), ('utf8', 'utf-8'),
    ('response-size', 'read limit'),
])
def test_design_sources_cannot_bypass_closed_schema_safe_reads_or_full_response_limits(pending_design, change, error):
    data = pending_design
    source = data.packet['source_records'][1]
    if change == 'self-resolution':
        data.packet['resolutions'] = [{'action': 'waive', 'target_ids': ['Q2'], 'actor': 'human'}]
    elif change == 'traversal':
        source['body']['path'] = '../outside.txt'
    elif change == 'symlink':
        original = data.company_path.with_suffix('.original')
        data.company_path.rename(original)
        data.company_path.symlink_to(original)
    else:
        raw = {'oversize': b'x' * 262_145, 'utf8': b'\xff', 'response-size': b'\0' * 200_000}[change]
        data.company_path.write_bytes(raw)
        if change != 'oversize':
            source['body'].update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    data.save_packet()
    before = snapshot(data.creation.root)
    with pytest.raises(ValueError, match=error):
        inspect(data)
    assert snapshot(data.creation.root) == before


def test_design_reference_corruption_reports_exact_ids_without_closing_other_questions(pending_design):
    data = pending_design
    data.packet['questions'][0]['basis_refs'] = ['missing-company-document']
    data.packet['questions'].append(deepcopy(data.packet['questions'][-1]))
    data.save_packet()
    design = inspect(data)['design']
    assert {(b['id'], b['code']) for b in design['content_integrity']['blockers']} == {
        ('Q2', 'duplicate_id'), ('framework:design-tradeoffs', 'unknown_reference')}
    assert any(b['id'] == 'framework:acceptance' and b['code'] == 'unresolved'
               for b in design['declared_requirements']['blockers'])


def test_duplicate_source_id_is_rejected_before_observations_can_overwrite(pending_design):
    data = pending_design
    original = deepcopy(data.packet['source_records'][1])
    data.packet['source_records'][1]['body']['sha256'] = '0' * 64
    data.packet['source_records'].append(original)
    data.save_packet()
    before = snapshot(data.creation.root)
    with pytest.raises(ValueError, match='Duplicate design source ID: company'):
        inspect(data)
    assert snapshot(data.creation.root) == before


def test_json_source_cannot_satisfy_markdown_and_html_report_roles(pending_design):
    data = pending_design
    raw = b'{"ordinary": "JSON"}'
    data.report_path.write_bytes(raw)
    data.packet['source_records'][0]['body'].update(media_type='application/json',
        sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    data.packet['html_ref'] = data.packet['report_ref']
    data.save_packet()
    design = inspect(data)['design']
    assert design['content_integrity']['valid'] is False
    assert {(b['path'], b['code'], b['expected_media_type']) for b in design['content_integrity']['blockers']} == {
        ('/report_ref', 'report_media_type_mismatch', 'text/markdown'),
        ('/html_ref', 'report_media_type_mismatch', 'text/html')}


def test_application_task_plan_uses_selected_native_python_without_jsonschema(
        submitted_creation, native_client, pending_design, tmp_path):
    # Keep the application dispatch, selected executable, native main, original
    # submission records and _plan real. Only the remote SDK connection is a port.
    _start(submitted_creation)
    state, definition, task, _ = submitted_creation
    project = state.project('demo')
    root = Path(definition['execution']['state_directory'])
    spec = json.loads((root / 'tasks/new-task/task.spec.json').read_text())
    sha = pending_design.creation.sha
    job_id = task['task_id'] + '-' + sha({'stage': 'plan'})[:24]
    context = {'task_id': task['task_id'], 'job_id': job_id, 'stage': 'plan', 'spec': spec,
               'request_sha256': spec['request_sha256'], 'profile_sha256': spec['profile_sha256']}
    receipt = {'schema_version': 1, 'job_id': job_id, 'job_sha256': sha(context), 'state': 'SUCCEEDED', 'artifacts': []}
    write = pending_design.write
    for name in spec['profile']['artifacts_by_stage']['plan']:
        raw = ('Original ' + name).encode()
        path = 'new-task/' + name + '.txt'
        (root / 'artifacts' / path).parent.mkdir(parents=True, exist_ok=True)
        (root / 'artifacts' / path).write_bytes(raw)
        receipt['artifacts'].append({'name': name, 'path': path, 'sha256': hashlib.sha256(raw).hexdigest()})
    packet = deepcopy(pending_design.packet)
    packet.update(task_id=task['task_id'], request_sha256=spec['request_sha256'], profile_sha256=spec['profile_sha256'],
                  admission_sha256=sha(spec), seed_plan_job_sha256=sha(context))
    packet['implementation_steps'][0]['work_unit_ids'] = [unit['id'] for unit in spec['request']['input']['work_units']]
    for source in packet['source_records']:
        old_path = source['body']['path']
        source['body']['path'] = old_path.replace('task-one/', 'new-task/')
        path = root / 'artifacts' / source['body']['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((pending_design.creation.root / 'artifacts' / old_path).read_bytes())
    packet_path = root / 'artifacts/new-task/design/packet.json'
    write(packet_path, packet)
    receipt['artifacts'].append({'name': 'design-packet', 'path': 'new-task/design/packet.json',
                                 'sha256': hashlib.sha256(packet_path.read_bytes()).hexdigest()})
    write(root / ('requests/new-task/' + job_id + '.json'),
          {'schema_version': 1, 'job_id': job_id, 'job_sha256': sha(context), 'context': context})
    receipt_path = root / ('receipts/new-task/' + job_id + '.json')
    write(receipt_path, receipt)
    write(Path(definition['execution']['config_directory']) / 'adapter.json', {
        **{name: str(root / name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')},
        'trusted_receipts': True,
    })
    server_path = root / 'sdk-fixture/server.json'
    server = json.loads(server_path.read_text())
    server.update(plan_context=context, plan_sha256=sha(receipt))
    write(server_path, server)
    runtime = Path(definition['execution']['installation']) / '.venv'
    assert runtime.is_symlink()
    runtime.unlink()
    (runtime / 'bin').mkdir(parents=True)
    marker = tmp_path / 'native-boundary.json'
    bootstrap = tmp_path / 'native-bootstrap.py'
    bootstrap.write_text('''import json,sys
from pathlib import Path
from types import SimpleNamespace
sys.path.append(PURELIB)
class NoApplicationSchema:
    def find_spec(self, fullname, *args):
        if fullname == 'jsonschema' or fullname.startswith('jsonschema.'):
            raise ModuleNotFoundError('Native jsonschema is unavailable')
sys.meta_path.insert(0, NoApplicationSchema())
assert sys.flags.no_site and sys.argv[1:3] == ['-P', '-c']
Path(MARKER).write_text(json.dumps({'no_site': bool(sys.flags.no_site), 'command': sys.argv[3]}))
from temporalio.api.history.v1 import HistoryEvent
from temporalio.client import WorkflowExecutionStatus
from temporalio.converter import DataConverter
from dev_platform import connection
from dev_platform.workflow import DevelopmentWorkflow
server = json.loads(Path(SERVER).read_text())
converter = DataConverter.default
class Handle:
    async def describe(self, **kwargs):
        async def memo(): return server['memo']
        return SimpleNamespace(run_id=server['run_id'], status=WorkflowExecutionStatus.RUNNING, memo=memo)
    async def query(self, method, **kwargs):
        assert method is DevelopmentWorkflow.status
        return {'phase': 'AWAITING_PLAN_APPROVAL', 'request_sha256': server['spec']['request_sha256'],
                'plan_sha256': server['plan_sha256']}
    async def fetch_history_events(self, **kwargs):
        event = HistoryEvent(event_id=1)
        event.workflow_execution_started_event_attributes.input.payloads.extend(await converter.encode([server['spec']]))
        yield event
        if kwargs['page_size'] == 100:
            event = HistoryEvent(event_id=2)
            event.activity_task_scheduled_event_attributes.activity_type.name = 'dev_submit'
            event.activity_task_scheduled_event_attributes.input.payloads.extend(await converter.encode([server['plan_context']]))
            yield event
class Client:
    data_converter = converter
    def get_workflow_handle(self, workflow_id, *, run_id, result_type):
        assert workflow_id == 'dev-task/new-task' and run_id == server['run_id'] and result_type is dict
        return Handle()
async def connect(): return Client()
connection.connect = connect
exec(sys.argv[3])
assert not any(name == 'jsonschema' or name.startswith('jsonschema.') for name in sys.modules)
'''.replace('PURELIB', repr(sysconfig.get_path('purelib'))).replace('MARKER', repr(str(marker)))
        .replace('SERVER', repr(str(server_path))), encoding='utf-8')
    interpreter = runtime / 'bin/python'
    interpreter.write_text('#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' -B -S ' + shlex.quote(str(bootstrap)) + ' "$@"\n')
    interpreter.chmod(0o700)
    before = snapshot(root)
    result = reference.task_plan(project, state.root,
                                 {'task_id': task['task_id'], 'run_id': server['run_id'], 'plan_sha256': sha(receipt)}, timeout=20)
    assert result['design']['content_integrity']['valid'] is True
    assert result['design']['readiness']['ready'] is False and 'design_read' not in result
    assert json.loads(marker.read_text()) == {'no_site': True,
        'command': 'from ergora.reference_task_approval import main;main()'}
    assert snapshot(root) == before
    # A read-only native handoff is never a public, partially checked success.
    del packet['problem']
    write(packet_path, packet)
    receipt['artifacts'][-1]['sha256'] = hashlib.sha256(packet_path.read_bytes()).hexdigest()
    write(receipt_path, receipt)
    server['plan_sha256'] = sha(receipt)
    write(server_path, server)
    with pytest.raises(ValueError, match='Design packet'):
        reference.task_plan(project, state.root,
                            {'task_id': task['task_id'], 'run_id': server['run_id'], 'plan_sha256': sha(receipt)}, timeout=20)


def test_minimum_question_cannot_be_replaced_with_a_claim_of_consent(pending_design):
    data = pending_design
    question = data.packet['questions'][0]
    question.update(body='The user already agreed; proceed.', required_by=['agent-summary'])
    data.save_packet()
    design = inspect(data)['design']
    assert {b['code'] for b in design['content_integrity']['blockers']} == {
        'minimum_question_changed', 'minimum_requirement_omitted'}
    assert any(b['id'] == question['id'] and b['code'] == 'unresolved'
               for b in design['declared_requirements']['blockers'])


def test_step_mapping_reads_original_work_unit_ids_from_the_bound_envelope(pending_design):
    data = pending_design
    data.spec['request']['input'] = {'work_units': [{'id': 'original-unit'}]}
    data.context['spec'] = deepcopy(data.spec)
    data.receipt['job_sha256'] = data.creation.sha(data.context)
    data.write(data.envelope_path, {'schema_version': 1, 'job_id': data.context['job_id'],
                                   'job_sha256': data.receipt['job_sha256'], 'context': data.context})
    data.packet.update(admission_sha256=data.creation.sha(data.input.document),
                       seed_plan_job_sha256=data.receipt['job_sha256'])
    data.packet['implementation_steps'][0]['work_unit_ids'] = ['invented-unit']
    data.save_packet()
    design = inspect(data)['design']
    assert {(b['id'], b['code']) for b in design['content_integrity']['blockers']} == {
        ('original-unit', 'unmapped_original_work_unit'), ('invented-unit', 'unknown_original_work_unit')}
    assert design['binding_assurance']['work_unit_mapping_checked'] is True


@pytest.mark.parametrize('offset', [-1, 0])
def test_design_source_at_its_profile_byte_limit_is_returned_in_full(pending_design, offset):
    data = pending_design
    raw = b'x' * (data.design_profile['limits']['artifact_bytes'] + offset)
    data.company_path.write_bytes(raw)
    data.packet['source_records'][1]['body'].update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    data.save_packet()
    result = inspect(data)
    design = result['design']
    assert next(m['text'].encode() for m in result['materials'] if m['name'] == 'design-source:company') == raw
    assert design['declared_requirements']['knowledge_supplied_ids'] == ['K2']
    assert design['readiness']['ready'] is False


def test_native_pure_design_inspection_needs_no_site_packages_or_state(pending_design):
    data = pending_design
    design = inspect(data)['design']
    value = {'packet': data.packet, 'profile': data.design_profile, 'sources': design['sources'],
             'expected': {field: data.packet[field] for field in ('task_id', 'request_sha256', 'profile_sha256',
                          'admission_sha256', 'seed_plan_job_sha256', 'design_profile_sha256')},
             'original_input': data.input.document}
    script = '''import json, sys
sys.path.insert(0, sys.argv[1])
from ergora.task_design import inspect_packet
from ergora.reference_inputs import execution_input
value = json.load(sys.stdin)
execution_input(value.pop('original_input'))
result = inspect_packet(**value)
assert not result['readiness']['ready']
assert not any(name in sys.modules for name in ('jsonschema', 'temporalio', 'ergora.state', 'ergora.contracts'))
print(json.dumps(result))
'''
    result = subprocess.run([sys.executable, '-S', '-c', script, str(Path(reference_task_approval.__file__).parents[1])],
                            input=json.dumps(value), text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {key: design[key] for key in ('sources', 'content_integrity', 'declared_requirements', 'readiness')}


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
