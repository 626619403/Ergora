"""Prepare and read an explicitly authorized independent fixed check operation."""

import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time

from agent_platform.core import Blocked, STATE, require
from agent_platform.process_job import candidate_check_gate
from dev_platform.adapter import FileAdapter, publish
from dev_platform.contracts import canonical_sha

from ergora.definitions import workflows
from ergora.development import dags, verification
from ergora.development.review import packets, requests
from ergora.development.runtime import fixed_checks
from ergora.development.runtime.export import _Export
from ergora.development.runtime.jobs import CandidateCheckJob
from ergora.runtime import budget_clock
from ergora.storage.git import GitMaterials
from ergora.storage.state import file_lock


KIND = fixed_checks.KIND
_PENDING_CHECK = ('queued', 'attempted')


async def _status(adapter: FileAdapter, envelope: dict, admission: dict) -> dict:
    context = envelope['context']
    job = {'task_id': context['task_id'], 'job_id': envelope['job_id'], 'job_sha256': envelope['job_sha256'], 'context': context}
    receipt = await adapter.poll(job)
    fence = adapter.path('fences', context['task_id'] + '.json')
    workspace = fixed_checks.check_workspace(context) / 'budget'
    status = 'stopped_pending' if fence.exists() else 'attempted' if (workspace / 'attempt.json').exists() else 'queued'
    result = {'operation_id': admission['operation_id'], 'project': admission['project'],
              'project_revision': admission['project_revision'], 'candidate_sha': admission['request']['candidate_sha'],
              'authorization_sha256': admission['sha256'], 'request_file_sha256': admission['request_file_sha256'],
              'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
              'verification_sha256': admission['verification']['sha256'], 'stop_requested': fence.exists(),
              'status': status, 'cleanup_confirmed': None, 'receipt_sha256': None, 'fixed_results_sha256': None}
    stopped_path = workspace / 'stopped.json'
    not_started = (workspace / 'not-started.json').exists()
    if stopped_path.exists() or not_started or receipt is not None:
        job_path = adapter.path('requests', context['task_id'] + '/' + job['job_id'] + '.json')
        owner = CandidateCheckJob(job_path, Path(admission['control_home']), envelope)
        if not_started:
            rejected = owner.read_not_started()
            require(receipt is None or receipt == rejected, 'Candidate check terminal differs from its original no-body disposition')
            result.update(status='not_started', body_started=False, detail=rejected['detail'])
        else:
            stopped = fixed_checks.read_record(stopped_path)
            require(stopped['cleanup_confirmed'] is True and all(stopped[key] == value for key, value in owner.identity.items()),
                    'Candidate check stopped witness differs from its original owner')
            if owner.unconfirmed_checks():
                require(receipt is None, 'Candidate check receipt cannot coexist with unknown fixed process outcomes')
                result.update(status='unknown', cleanup_confirmed=None, outer_cleanup_confirmed=True)
    if receipt is not None:
        require(owner.read_published_terminal() == receipt, 'Candidate check original terminal changed during readback')
        report = fixed_checks.validate_receipt(adapter, envelope, receipt)
        result.update(status=receipt['state'].lower(), cleanup_confirmed=None if not_started else True,
                      receipt_sha256=canonical_sha(receipt),
                      fixed_results_sha256=receipt['artifacts'][0]['sha256'] if report is not None else None,
                      fixed_check_ids=[item['id'] for item in receipt['checks']], detail=receipt['detail'])
    return result


async def _authorize(adapter: FileAdapter, payload: dict, project: dict, task_id: str) -> dict:
    request_text, request_digest = payload['request_text'], payload['request_file_sha256']
    source = fixed_checks.decode_check_request(request_text, request_digest)
    approval_path = adapter.path('approvals', task_id + '.json')
    if approval_path.exists():
        existing = fixed_checks.read_record(approval_path)
        require(existing['request_file_sha256'] == request_digest and existing['request_text'] == request_text
                and existing['project_revision'] == payload['expected_revision'] and existing['actor_id'] == _Export.actor(),
                'Candidate check operation ID already binds a different original authorization')
        return await _observe(adapter, payload, task_id, existing, stop=False)
    clock = budget_clock.authorize(source['wall_seconds'])
    budget = {**clock, 'sha256': canonical_sha(clock)}
    home = Path(payload['control_home'])
    fixed = verification.snapshot(project)
    require(fixed is not None and fixed['sha256'] == source['verification_sha256'], 'Operator must pin the registered fixed checks')
    require(project['revision'] == payload['expected_revision'], 'Candidate check project revision changed')
    origin = _Export({**payload, 'task_id': source['task_id'], 'run_id': source['run_id']})
    origin.prepare()
    intent = origin.load()
    exported = origin.status(intent)
    require(exported['status'] == 'exported' and exported['run_id'] == source['run_id']
            and exported['candidate_sha'] == source['candidate_sha'] and exported['intent_sha256'] == source['export_intent_sha256'],
            'Candidate check requires the exact already exported candidate')
    packet = packets.read(Path(source['packet']), sha256=source['packet_sha256'])['packet']
    require(packet['repository']['head'] == source['candidate_sha'], 'Local review packet targets another candidate')
    checked = workflows.inspect_manifest(Path(source['manifest']), material=True)
    require(checked['digest'] == source['manifest_digest'], 'Candidate check review manifest changed')
    graph = checked['composition']
    gated = dags.fixed_check_review(graph) is not None
    leaf = requests._review_leaf(graph, source['instance'], packet, gated=gated)
    parent = next(item for item in graph['instances'] if item['path'] == leaf['parent'])
    require(parent['ref'] == dags.FIXED_CHECK_REVIEW, 'Select the original correctness-review leaf in the pinned wrapper')
    repository = GitMaterials(Path(project['repo']), git='/usr/bin/git')
    require(repository.read('cat-file', '-t', source['candidate_sha']).strip() == b'commit', 'Candidate is absent from the registered local repository')
    registration = project['registration']
    admission = {'schema_version': 1, 'kind': KIND, 'project': project['id'], 'project_revision': project['revision'],
                 'registration_sha256': registration['sha256'], 'execution': registration['definition']['execution'],
                 'repo': project['repo'], 'control_home': str(home), 'operation_id': payload['operation_id'],
                 'actor_id': origin.actor(), 'request': source, 'request_text': request_text,
                 'request_file_sha256': request_digest, 'verification': fixed,
                 'export_receipt_sha256': origin.sha(origin.creation.document(origin.result_path)), 'budget': budget}
    admission['sha256'] = canonical_sha(admission)
    fixed_checks.check_project(project, home, admission)
    require(fixed_checks.work_remaining(admission) > 0, 'Original check allowance expired before request publication')
    context = fixed_checks.check_context(admission)
    require(context['task_id'] == task_id, 'Candidate check namespace disagrees with its operation ID')
    publish(approval_path, admission)
    require(fixed_checks.work_remaining(admission) > 0, 'Original check allowance expired before request publication')
    job = await adapter.submit(context)
    envelope = {'schema_version': 1, 'job_id': job['job_id'], 'job_sha256': job['job_sha256'], 'context': context}
    return await _status(adapter, envelope, admission)


async def _operate(payload: dict) -> dict:
    project, operation_id = payload['project'], payload['operation_id']
    task_id = fixed_checks.operation_scope(project['id'], operation_id)
    adapter = fixed_checks.check_adapter()
    operation = payload['operation']
    lock = adapter.path('approvals', task_id + '.lock')
    if operation == 'authorize-fixed-check':
        require(payload.get('confirm') is True, 'Candidate checks require explicit operator confirmation')
        adapter.roots['approvals'].mkdir(parents=True, exist_ok=True, mode=0o700)
        with file_lock(lock, blocking=False):
            return await _authorize(adapter, payload, project, task_id)
    require(operation in ('status-fixed-check', 'stop-fixed-check', 'prove-fixed-check'),
            'Unsupported candidate check operation')
    admission = fixed_checks.read_record(adapter.path('approvals', task_id + '.json'))
    if operation == 'prove-fixed-check':
        return await _prove_graph_read(adapter, payload, task_id, admission)
    if operation == 'stop-fixed-check':
        require(payload.get('confirm') is True, 'Stopping a candidate check requires explicit confirmation')
        with file_lock(lock, blocking=False):
            return await _observe(adapter, payload, task_id, admission, stop=True)
    verify_pending = payload.get('verify_pending', False)
    require(type(verify_pending) is bool and (not verify_pending or payload.get('job_sha256') is not None),
            'Pending fixed-check observation requires its exact original Job digest')
    return await _observe(adapter, payload, task_id, admission, stop=False, waiting=verify_pending)


async def _observe(adapter: FileAdapter, payload: dict, task_id: str, admission: dict, *, stop: bool,
                   waiting: bool = False) -> dict:
    require(admission['project'] == payload['project']['id'] and admission['control_home'] == payload['control_home'],
            'Candidate check belongs to another project or control directory')
    context = fixed_checks.check_context(admission)
    job_id, job_sha = context['job_id'], canonical_sha(context)
    expected = {'schema_version': 1, 'job_id': job_id, 'job_sha256': job_sha, 'context': context}
    fixed_checks.authorized(adapter, expected)
    selected = payload.get('job_sha256')
    require((not stop and selected is None) or selected == job_sha, 'Select the exact original candidate check job')
    relative = task_id + '/' + job_id + '.json'
    request = adapter.path('requests', relative)
    envelope = fixed_checks.read_record(request) if request.exists() else None
    require(envelope is None or envelope == expected, 'Candidate check request differs from its original authorization')
    fence = adapter.path('fences', task_id + '.json')
    if stop:
        terminal = adapter.path('receipts', relative)
        owner = CandidateCheckJob(request, Path(admission['control_home']), envelope) if envelope is not None else None
        with candidate_check_gate(fence):
            if terminal.exists():
                require(owner is not None, 'Candidate check terminal is missing its original request')
                owner.read_published_terminal()
            else:
                # The scope gate covers only the last publication check and fence.
                publish(fence, {'schema_version': 1, 'task_id': task_id, 'request_sha256': context['request_sha256']})
    if envelope is None:
        return {'status': 'request_not_observed', 'operation_id': admission['operation_id'], 'job_id': job_id,
                'job_sha256': job_sha, 'authorization_sha256': admission['sha256'],
                'request_file_sha256': admission['request_file_sha256'], 'cleanup_confirmed': None,
                'stop_requested': fence.exists()}
    status = await _status(adapter, envelope, admission)
    if waiting and status['status'] in _PENDING_CHECK and not status['stop_requested']:
        refusal = STATE / 'rejected-envelopes' / (hashlib.sha256(str(request).encode()).hexdigest() + '.json')
        require(not refusal.exists(), 'Original fixed check request was rejected by its executor')
    return status


def _require_completion(status: dict, *, waiting: bool) -> None:
    detail = 'Graph requires a completed passing original fixed check with confirmed cleanup'
    if waiting:
        detail += ' (observed ' + status['status'] + ')'
    require(status['status'] == 'succeeded' and status['cleanup_confirmed'] is True and not status['stop_requested'], detail)


def _review_task_sha256(admission: dict, review: dict, candidate: str) -> str:
    request = admission['request']
    require(isinstance(review, dict) and review.keys() == {'manifest_digest', 'instance', 'task_sha256', 'packet_sha256'},
            'Graph proof requires the exact review task and manifest binding')
    require(review['manifest_digest'] == request['manifest_digest'] and review['instance'] == request['instance'],
            'Graph manifest or reviewer differs from the original fixed check authorization')
    require(review['packet_sha256'] == request['packet_sha256'], 'Graph packet differs from the original fixed check authorization')
    material = packets.read(Path(request['packet']), sha256=request['packet_sha256'])
    require(material['packet']['repository']['head'] == candidate, 'Original review packet targets another candidate')
    task = requests._task(material, 'local', request['packet_sha256'], request['manifest_digest'])
    task_sha256 = hashlib.sha256(task).hexdigest()
    require(review['task_sha256'] == task_sha256, 'Graph root task differs from the complete original review packet')
    return task_sha256


async def _prove_graph_read(adapter: FileAdapter, payload: dict, task_id: str, admission: dict) -> dict:
    source = verification.validate_fixed_check_source(payload['source'])
    project = payload['project']
    revision, admitted = project['revision'], admission['project_revision']
    require(type(revision) is int and type(admitted) is int and revision == admitted,
            'Graph project revision differs from the original fixed check authorization')
    require(admission['registration_sha256'] == project['registration']['sha256'],
            'Graph fixed check differs from its original registered project')
    waiting = 'wait_seconds' in source
    status = await _observe(adapter, payload, task_id, admission, stop=False, waiting=waiting)
    pending = waiting and status['status'] in _PENDING_CHECK and not status['stop_requested']
    if not pending:
        _require_completion(status, waiting=waiting)
    require(all(status.get(key) == value for key, value in source.items() if key != 'wait_seconds'),
            'Graph locator differs from the original fixed check receipt or candidate')
    review = payload['review']
    task_sha256 = _review_task_sha256(admission, review, source['candidate_sha'])
    if pending:
        deadline = payload['deadline']
        while status['status'] in _PENDING_CHECK and not status['stop_requested']:
            await asyncio.sleep(max(0, min(.25, deadline - time.monotonic())))
            if time.monotonic() >= deadline:
                raise TimeoutError('Original fixed check wait reached its deadline')
            # Observe the same saved Job and approval on every poll.
            status = await _observe(adapter, payload, task_id, admission, stop=False, waiting=True)
        _require_completion(status, waiting=waiting)
        task_sha256 = _review_task_sha256(admission, review, source['candidate_sha'])
    request = admission['request']
    return {**source, 'receipt_sha256': status['receipt_sha256'], 'fixed_results_sha256': status['fixed_results_sha256'],
            'status': 'validated', 'project': admission['project'],
            'project_revision': admission['project_revision'], 'job_id': status['job_id'],
            'authorization_sha256': status['authorization_sha256'], 'verification_sha256': status['verification_sha256'],
            'fixed_check_ids': status['fixed_check_ids'], 'packet_sha256': request['packet_sha256'],
            'manifest_digest': request['manifest_digest'], 'instance': request['instance'], 'task_sha256': task_sha256}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        result = asyncio.run(_operate(payload))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (Blocked, OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit('BLOCKED: ' + str(error)) from error
