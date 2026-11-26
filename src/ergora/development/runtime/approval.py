"""Exact owner approval with immutable intent and original-run signal reconciliation."""

import asyncio
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import stat
import tempfile
import time
import uuid

from ergora.development.runtime.submission import _Submission
from ergora.development import plan_methods
from ergora.native.history import find_signal_event
from ergora.storage.state import file_lock
from ergora._paths import DATA_ROOT
from ergora._paths import DATA_ROOT


def _read_design(creation, selected, context: dict, material: dict) -> tuple[dict, list]:
    """Read bounded facts for application validation, using the original adapter."""
    data = DATA_ROOT
    profile = json.loads((data / 'design-profiles/framework-development-v1.json').read_text(encoding='utf-8'))
    limits = profile['limits']
    if material['bytes'] > limits['artifact_bytes']:
        raise ValueError('Design packet exceeds its inspection profile artifact limit')
    packet = json.loads(material['text'])
    # These checks own only safe, bounded source I/O. The application validates
    # the full schema before it publishes any inspection result.
    records = packet.get('source_records') if isinstance(packet, dict) else None
    if not isinstance(records, list) or len(records) > limits['source_records']:
        raise ValueError('Design source_records must be a list within its inspection profile limit')
    seen = set()
    for source in records:
        if not isinstance(source, dict) or not isinstance(source.get('id'), str):
            raise ValueError('Design source record requires a text ID')
        if source['id'] in seen:
            raise ValueError('Duplicate design source ID: ' + source['id'])
        seen.add(source['id'])
    sources, materials = {}, []
    for source in records:
        source_id = source['id']
        if source.get('access') == 'reference_only':
            sources[source_id] = {'status': 'reference_only'}
            continue
        if source.get('access') != 'full' or not isinstance(source.get('body'), dict):
            raise ValueError('Design source requires full body or reference_only access: ' + source_id)
        path = creation.safe_path(creation.path('artifacts'), source['body'].get('path'))
        try:
            raw = creation.adapter.read_raw(path, limits['artifact_bytes'])
        except FileNotFoundError:
            sources[source_id] = {'status': 'missing'}
            continue
        except PermissionError:
            sources[source_id] = {'status': 'denied'}
            continue
        digest = hashlib.sha256(raw).hexdigest()
        sources[source_id] = {'status': 'read', 'sha256': digest, 'bytes': len(raw)}
        materials.append({'id': source_id, 'path': source['body']['path'], 'sha256': digest,
                          'bytes': len(raw), 'text': raw.decode('utf-8')})
    expected = {'task_id': creation.task_id, 'request_sha256': selected.spec['request_sha256'],
                'profile_sha256': selected.spec['profile_sha256'], 'admission_sha256': creation.sha(selected.document),
                'seed_plan_job_sha256': creation.sha(context), 'design_profile_sha256': creation.sha(profile)}
    if 'composition' in selected.document:
        expected['manifest_digest'] = selected.document['composition']['manifest']['digest']
    units = selected.spec['request'].get('input', {}).get('work_units')
    return {'packet': packet, 'profile': profile, 'expected': expected, 'sources': sources,
            'work_unit_ids': [unit['id'] for unit in units] if units is not None else None}, materials


def _require_method_window(status: dict, submission: _Submission) -> None:
    capability = status.get('plan_method_addendum')
    if capability is None or status.get('admission_sha256') != submission.input.document.get('sha256'):
        raise ValueError('Original worker cannot attest to the method addendum checkpoint')
    if capability['available'] is not True:
        raise ValueError(capability['unavailable_reason'])


async def _plan(payload: dict) -> dict:
    from dev_platform.adapter import identifier
    from dev_platform.workflow import DevelopmentWorkflow

    submission = _Submission(payload)
    intent, run_id = submission.submitted()
    creation, spec = submission.creation, submission.spec
    if payload['run_id'] != run_id:
        raise ValueError('Plan inspection must pin the original submitted run ID')
    handle, description, converter = await submission.lookup_run(intent, run_id)
    if description.status.name != 'RUNNING':
        raise ValueError('Plan inspection requires an original run awaiting an owner decision')
    status = await handle.query(DevelopmentWorkflow.status, rpc_timeout=timedelta(seconds=20))
    if (status['phase'] != 'AWAITING_PLAN_APPROVAL' or status['request_sha256'] != spec['request_sha256']
            or status['plan_sha256'] != payload['plan_sha256']):
        raise ValueError('Plan inspection requires the exact plan currently awaiting an owner decision')

    next_event = 1
    async for event in handle.fetch_history_events(page_size=100, rpc_timeout=timedelta(seconds=20)):
        if (event.event_id != next_event
                or next_event == 1 and not event.HasField('workflow_execution_started_event_attributes')):
            raise ValueError('Plan inspection requires the original history prefix')
        next_event += 1
        if not event.HasField('activity_task_scheduled_event_attributes'):
            continue
        scheduled = event.activity_task_scheduled_event_attributes
        if scheduled.activity_type.name != submission.input.submit_activity:
            continue
        if len(scheduled.input.payloads) != 1:
            raise ValueError('Original plan history has no single job context')
        values = await converter.decode(scheduled.input.payloads, [dict])
        if len(values) != 1 or not isinstance(values[0], dict):
            raise ValueError('Original plan history has no single job context')
        context = values[0]
        if context.get('stage') != 'plan':
            continue
        if (context['request_sha256'] != spec['request_sha256'] or not submission.input.matches_context(context)):
            raise ValueError('Original plan history differs from the recorded task spec')
        job_id = identifier(context['job_id'])
        break
    else:
        raise ValueError('Original history has no submitted plan job')

    result = _plan_materials(submission, intent, run_id, context, event.event_id, payload['plan_sha256'])
    if 'methods' in payload:
        _require_method_window(status, submission)
        method = plan_methods.addendum(submission.input.document, run_id, result['plan_sha256'], payload['methods'])
        result.update(method_addendum=method, method_addendum_sha256=creation.sha(method),
                      approval_plan_sha256=plan_methods.approval_digest(method))
        creation.check_size(result, 1_048_576, 'Plan inspection with method addendum')
    if 'design_read' in result:
        directory = creation.path('ergora/task-approvals/' + creation.task_id)
        if directory.exists():
            with _source_lock(creation):
                chain = _source_scan(submission)
                if chain is not None:
                    attached = _source_output(creation, chain)
                    for key in ('design_source_read', 'design_source_validation'):
                        result[key] = attached[key]
    return result


def _plan_materials(submission, intent: dict, run_id: str, context: dict,
                    history_event_id: int, plan_sha256: str) -> dict:
    from dev_platform.adapter import identifier

    creation, spec = submission.creation, submission.spec
    job_id = identifier(context['job_id'])
    job_sha = creation.sha(context)
    adapter = creation.file_adapter(submission.input)
    envelope = adapter.read_job(adapter.path('requests', creation.task_id + '/' + job_id + '.json'))
    if creation.sha(envelope) != creation.sha({'schema_version': 1, 'job_id': job_id,
                                             'job_sha256': job_sha, 'context': context}):
        raise ValueError('Plan request envelope differs from its original history context')
    receipt = creation.document(creation.path('receipts/' + creation.task_id + '/' + job_id + '.json'))
    # The native workflow hashes its accepted receipt, not an individual plan text.
    # That digest also binds metadata we do not display or revalidate here.
    if (creation.sha(receipt) != plan_sha256 or receipt['job_id'] != job_id
            or receipt['job_sha256'] != job_sha or receipt['state'] != 'SUCCEEDED'):
        raise ValueError('Plan receipt differs from the exact pending plan or its original job')
    artifacts = {artifact['name']: artifact for artifact in receipt['artifacts']}
    if len(artifacts) != len(receipt['artifacts']):
        raise ValueError('Plan receipt contains duplicate review artifact names')
    materials = []
    names = list(spec['profile']['artifacts_by_stage']['plan'])
    if selected := submission.input.document.get('composition', {}).get('preparation'):
        names.append('preparation-sources')
    if 'design-packet' in artifacts and 'design-packet' not in names:
        names.append('design-packet')
    for name in names:
        if name not in artifacts:
            raise ValueError('Plan receipt is missing a required review artifact: ' + name)
        artifact = artifacts[name]
        raw = creation.adapter.read_raw(creation.path('artifacts/' + artifact['path']), 262_144)
        if hashlib.sha256(raw).hexdigest() != artifact['sha256']:
            raise ValueError('Plan artifact bytes do not match their receipt digest: ' + name)
        materials.append({'name': name, 'sha256': artifact['sha256'], 'bytes': len(raw), 'text': raw.decode('utf-8')})
    result = {'schema_version': 1, 'project': creation.project['id'], 'project_revision': creation.project['revision'],
              'task_id': creation.task_id, 'workflow_id': intent['workflow_id'], 'run_id': run_id,
              'request_sha256': spec['request_sha256'], 'profile_sha256': spec['profile_sha256'],
              'runtime_status': 'queried', 'phase': 'AWAITING_PLAN_APPROVAL', 'plan_sha256': plan_sha256,
              'history_plan_event_id': history_event_id, 'job_sha256': job_sha, 'receipt': receipt,
              'materials': materials, 'artifact_limit_bytes': 262_144, 'read_only': True}
    if selected:
        sources = json.loads(next(item['text'] for item in materials if item['name'] == 'preparation-sources'))
        if (sources['kind'] != 'formal-preparation-sources' or sources['stage'] != 'plan'
                or sources['member'] != selected['plan']['coordinator']
                or sources['request_sha256'] != spec['request_sha256']
                or sources['profile_sha256'] != spec['profile_sha256']
                or sources['admission_sha256'] != submission.input.document['sha256']):
            raise ValueError('Plan preparation sources differ from the original canonical plan')
        outputs = [output for row in sources['members'].values() for output in row['outputs'].values()]
        outputs.extend(sources['inventory']['outputs'].values())
        for output in outputs:
            artifact = output['ref']
            path = creation.safe_path(creation.path('artifacts'), artifact['path'])
            raw = creation.adapter.read_raw(path, 262_144)
            if (hashlib.sha256(raw).hexdigest() != artifact['sha256'] or len(raw) != output['bytes']
                    or output['text'].encode('utf-8') != raw):
                raise ValueError('Preparation source bytes differ from their original artifact: ' + artifact['name'])
    if 'design-packet' in artifacts:
        material = next(item for item in materials if item['name'] == 'design-packet')
        result['design_read'], sources = _read_design(creation, submission.input, context, material)
        materials.extend({'name': 'design-source:' + source['id'], **source} for source in sources)
        creation.check_size(result, result['design_read']['profile']['limits']['inspection_bytes'], 'Design inspection')
    creation.check_size(result, 1_048_576, 'Plan inspection')
    return result


_SOURCE_LIMITS = {'artifact_bytes': 262144, 'inspection_bytes': 1048576, 'operations': 128,
                  'packet_revisions': 32, 'intent_bytes': 16777216, 'journal_bytes': 67108864}
_SOURCE_MEDIA = {'text/plain': 'txt', 'text/markdown': 'md', 'text/html': 'html', 'application/json': 'json'}


def _source_storage(creation, supplied=None, frozen=None):
    contract = json.loads((DATA_ROOT / 'design-profiles/design-source-storage-v1.json').read_text())
    limits = dict(contract['limits']) if frozen is None else dict(frozen['limits'])
    if supplied is not None:
        if set(supplied) - set(limits):
            raise ValueError('Unknown design source storage limit')
        limits.update(supplied)
    if set(limits) != set(_SOURCE_LIMITS):
        raise ValueError('Unsupported design source storage profile fields')
    for name, hard in _SOURCE_LIMITS.items():
        if type(limits[name]) is not int or not 0 < limits[name] <= min(contract['limits'][name], hard):
            raise ValueError('Design source storage limit is invalid: ' + name)
    profile = {**contract, 'limits': limits}
    if frozen is not None and profile != frozen:
        raise ValueError('Design source storage profile is frozen; start a new task instead')
    return contract, profile


def _source_paths(creation, operation_id):
    operation_id = creation.core.slug(operation_id)
    prefix = 'ergora/task-approvals/' + creation.task_id + '/' + operation_id
    return {name: creation.path(prefix + '.' + name + '.json') for name in ('intent', 'result', 'attempt')}


def _source_json(creation, value):
    return creation.adapter.canonical(value) + b'\n'


def _source_confirm(creation, path, expected):
    """Confirm the same existing inode and bytes, then its publication directories."""
    creation.safe_path(creation.root, path.relative_to(creation.root).as_posix())
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or stream.read(len(expected) + 1) != expected:
            raise ValueError('Design source publication differs from its complete intent: ' + str(path))
        os.fsync(stream.fileno())
        for parent in path.parents:
            directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                descriptor = os.fstat(directory_fd)
                actual = parent.stat(follow_symlinks=False)
                if (descriptor.st_dev, descriptor.st_ino) != (actual.st_dev, actual.st_ino):
                    raise ValueError('Design source directory changed during confirmation')
                os.fsync(directory_fd)
                actual = parent.stat(follow_symlinks=False)
                if (descriptor.st_dev, descriptor.st_ino) != (actual.st_dev, actual.st_ino):
                    raise ValueError('Design source directory changed during confirmation')
            finally:
                os.close(directory_fd)
            if parent == creation.root:
                break
        actual = path.stat(follow_symlinks=False)
        if (before.st_dev, before.st_ino) != (actual.st_dev, actual.st_ino):
            raise ValueError('Design source file changed during confirmation')
        stream.seek(0)
        if stream.read(len(expected) + 1) != expected:
            raise ValueError('Design source bytes changed during confirmation')


def _source_publish_body(creation, item):
    path = creation.path('artifacts/' + item['path'])
    raw = item['text'].encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    creation.safe_path(creation.root, path.relative_to(creation.root).as_posix())
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.pending-')
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if creation.adapter.read_raw(path, len(raw)) != raw:
                raise ValueError('Immutable design source body conflicts: ' + item['path'])
        _source_confirm(creation, path, raw)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def _source_lock(creation, *, writing=False, blocking=False):
    import fcntl

    fd = os.open(creation.lock_path, (os.O_RDWR if writing else os.O_RDONLY) | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        actual = creation.lock_path.stat(follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or (before.st_dev, before.st_ino) != (actual.st_dev, actual.st_ino):
            raise ValueError('Original task creation lock is not the same regular file')
        try:
            fcntl.flock(fd, (fcntl.LOCK_EX if writing else fcntl.LOCK_SH) | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError as error:
            code = 'operation_unavailable' if writing else 'read_unavailable'
            raise ValueError('Design source ' + code + ': original task creation lock is busy') from error
        yield
        actual = creation.lock_path.stat(follow_symlinks=False)
        if (before.st_dev, before.st_ino) != (actual.st_dev, actual.st_ino):
            raise ValueError('Original task creation lock changed during source inspection')
    finally:
        os.close(fd)


def _source_seed(submission, preflight):
    creation = submission.creation
    intent, run_id = submission.submitted()
    if preflight['run_id'] != run_id or preflight['phase'] != 'AWAITING_PLAN_APPROVAL':
        raise ValueError('Design source seed must name the inspected original pending plan')
    from dev_platform.adapter import identifier

    job_id = identifier(preflight['receipt']['job_id'])
    adapter = creation.file_adapter(submission.input)
    envelope = adapter.read_job(adapter.path('requests', creation.task_id + '/' + job_id + '.json'))
    context = envelope['context']
    if not submission.input.matches_context(context) or context['stage'] != 'plan':
        raise ValueError('Design source seed differs from its original plan job')
    seed = _plan_materials(submission, intent, run_id, context,
                           preflight['history_plan_event_id'], preflight['plan_sha256'])
    if 'design_read' not in seed:
        raise ValueError('Design source operations require an original design packet')
    for name in ('task_id', 'workflow_id', 'run_id', 'request_sha256', 'profile_sha256', 'plan_sha256', 'job_sha256'):
        if seed[name] != preflight[name]:
            raise ValueError('Original design seed changed after inspection: ' + name)
    if type(preflight['project_revision']) is not int or not 1 <= preflight['project_revision'] <= creation.project['revision']:
        raise ValueError('Design source seed has an invalid original project revision')
    seed['project_revision'] = preflight['project_revision']
    # Saved preflight bodies and schema are reread from original immutable files.
    return seed


def _source_anchor(submission, seed):
    creation = submission.creation
    contract, _ = _source_storage(creation)
    intent, run_id = submission.submitted()
    return {'schema_version': 1, 'kind': 'task-design-source-anchor', 'task_id': creation.task_id,
        'creation_sha256': creation.sha(submission.creation_record), 'submission_sha256': creation.sha(intent),
        'workflow_id': intent['workflow_id'], 'run_id': run_id, 'seed_receipt_sha256': seed['plan_sha256'],
        'seed_job_sha256': seed['job_sha256'], 'seed_packet_sha256': creation.sha(seed['design_read']['packet']),
        'source_storage_contract_sha256': creation.sha(contract)}


def _source_body(creation, text, media_type, limits):
    raw = text.encode('utf-8')
    if media_type not in _SOURCE_MEDIA or not 0 < len(raw) <= limits['artifact_bytes']:
        raise ValueError('Design source body media or complete byte size is unsupported')
    digest = hashlib.sha256(raw).hexdigest()
    return {'path': creation.task_id + '/design/' + digest + '/body.' + _SOURCE_MEDIA[media_type],
            'sha256': digest, 'bytes': len(raw), 'media_type': media_type, 'text': text}


def _source_material(creation, operation, value, packet, responses, seed, recorded_at, recorder, limits):
    from ergora.development.design import inspect_packet

    if operation == 'publish-design':
        proposed = value['packet']
        bindings = ('task_id', 'request_sha256', 'profile_sha256', 'admission_sha256', 'manifest_digest',
                    'seed_plan_job_sha256', 'design_profile_sha256', 'owner_id')
        if any(proposed[key] != seed['design_read']['packet'][key] for key in bindings):
            raise ValueError('Published design must retain its original task/profile/declared owner binding')
        if (type(proposed['revision']) is not int or proposed['revision'] != packet['revision'] + 1
                or proposed['revision'] > limits['packet_revisions']
                or proposed['previous_packet_sha256'] != creation.sha(packet)):
            raise ValueError('Published design must follow the current committed packet revision')
        supplied, seen = {}, set()
        for item in value['bodies']:
            body = _source_body(creation, item['text'], item['media_type'], limits)
            if body != item:
                raise ValueError('Design source body must match its managed path, bytes, SHA and media')
            if body['path'] in supplied and supplied[body['path']] != body:
                raise ValueError('Conflicting design source body path')
            supplied[body['path']] = body
        facts, used = {}, set()
        for record in proposed['source_records']:
            if record['id'] in seen:
                raise ValueError('Duplicate design source ID: ' + record['id'])
            seen.add(record['id'])
            if record['access'] == 'reference_only':
                facts[record['id']] = {'status': 'reference_only'}
                continue
            ref = record['body']
            body = supplied.get(ref['path'])
            if body is None or {key: body[key] for key in ref} != ref:
                raise ValueError('Full design source requires its complete matching body: ' + record['id'])
            used.add(body['path'])
            facts[record['id']] = {'status': 'read', 'sha256': body['sha256'], 'bytes': body['bytes']}
        if used != set(supplied):
            raise ValueError('Design submission contains unreferenced bodies')
        inspection = inspect_packet(proposed, seed['design_read']['profile'], seed['design_read']['expected'],
                                    facts, seed['design_read']['work_unit_ids'])
        if not inspection['content_integrity']['valid']:
            raise ValueError('Design source content integrity failed: ' + json.dumps(inspection['content_integrity']))
        raw = _source_json(creation, proposed)
        if len(raw) > limits['artifact_bytes']:
            raise ValueError('Complete published packet exceeds its artifact limit')
        artifact = {'path': creation.task_id + '/design/' + creation.sha(proposed) + '/packet.json',
                    'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                    'media_type': 'application/json', 'text': raw.decode('utf-8')}
        return {'packet': proposed, 'response': None, 'bodies': [*supplied.values(), artifact]}
    if operation != 'record-response':
        raise ValueError('Unsupported design source operation')
    response = value['response']
    if response['origin'] not in ('agent', 'reported-human'):
        raise ValueError('human_channel_unavailable: trusted owner responses are not supported')
    if response['packet_content_sha256'] != creation.sha(packet) or response['id'] in {item['id'] for item in responses}:
        raise ValueError('Response requires the current packet and a fresh response ID')
    questions = {item['id']: item for item in packet['questions']}
    if (not response['question_ids'] or set(response['question_ids']) - questions.keys()
            or set(response['source_refs']) - {item['id'] for item in packet['source_records']}):
        raise ValueError('Response refers to unknown packet questions or sources')
    choices = {option['id'] for key in response['question_ids'] for option in questions[key]['options']}
    if set(response['choice_ids']) - choices:
        raise ValueError('Response choice must belong to its target questions')
    superseded = response['supersedes_response_id']
    if superseded is not None and not any(item['id'] == superseded
            and item['packet_content_sha256'] == response['packet_content_sha256']
            and set(item['question_ids']) == set(response['question_ids']) for item in responses):
        raise ValueError('Superseded response must name the same packet and questions')
    body = _source_body(creation, value['body']['text'], value['body']['media_type'], limits)
    if body['media_type'] not in ('text/plain', 'text/markdown'):
        raise ValueError('Response text must be plain text or Markdown')
    complete = {**response, 'exact_text_ref': {key: body[key] for key in ('path', 'sha256', 'bytes', 'media_type')},
                'recorded_by': ':'.join(recorder.split(':', 2)[:2]), 'recorded_at': recorded_at}
    return {'packet': None, 'response': complete, 'bodies': [body]}


def _source_result(creation, intent):
    return {'schema_version': 2, 'kind': 'task-design-source-commit', 'operation_id': intent['operation_id'],
            'intent_sha256': creation.sha(intent), 'parent_record_sha256': intent['parent_record_sha256'],
            'material_revision': intent['material_revision']}


def _source_read_bodies(creation, material, limits, *, pending=False, repairing=None):
    missing = []
    for body in material['bodies']:
        path = creation.path('artifacts/' + body['path'])
        if not path.exists() and (pending or repairing is not None and repairing.get(body['path']) == body):
            missing.append(body['path'])
            continue
        if not path.is_file():
            raise ValueError('Design source body is not a regular file: ' + body['path'])
        raw = creation.adapter.read_raw(path, limits['artifact_bytes'])
        if raw != body['text'].encode('utf-8') or len(raw) != body['bytes'] or hashlib.sha256(raw).hexdigest() != body['sha256']:
            raise ValueError('Design source body differs from its complete intent: ' + body['path'])
    return missing


def _approval_journal(creation):
    """Read the bounded task directory shared by owner and source receipts."""
    directory = creation.path('ergora/task-approvals/' + creation.task_id)
    if not directory.exists():
        return {}
    groups, scanned = {}, 0
    with os.scandir(directory) as entries:
        for index, entry in enumerate(entries):
            if index >= 3 * _SOURCE_LIMITS['operations']:
                raise ValueError('Task approval journal exceeds its bounded entry scan')
            if entry.name.startswith('.'):
                continue
            match = re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9_-]{0,79})\.(intent|result|attempt)\.json', entry.name)
            if match is None:
                raise ValueError('Unknown task approval journal entry: ' + entry.name)
            path = creation.path('ergora/task-approvals/' + creation.task_id + '/' + entry.name)
            value = creation.document(path, _SOURCE_LIMITS['intent_bytes'])
            scanned += path.stat().st_size
            if scanned > _SOURCE_LIMITS['journal_bytes']:
                raise ValueError('Task approval journal exceeds its bounded raw-byte scan')
            groups.setdefault(match[1], {})[match[2]] = (value, path.stat().st_size)
    return groups


def _source_scan(submission, repair_id=None):
    creation = submission.creation
    groups = _approval_journal(creation)
    operations = []
    for operation_id, files in groups.items():
        if 'intent' not in files:
            raise ValueError('Task approval journal has no original intent: ' + operation_id)
        intent = files['intent'][0]
        if intent.get('schema_version') == 1 and intent.get('operation') == 'approve':
            if any(item[0].get('schema_version') != 1 for item in files.values()):
                raise ValueError('Conflicting task approval/source operation namespace: ' + operation_id)
            continue
        if intent.get('schema_version') != 2 or intent.get('kind') != 'task-design-source-operation' or 'attempt' in files:
            raise ValueError('Unsupported design source journal format: ' + operation_id)
        if type(intent.get('material_revision')) is not int or intent['material_revision'] < 2:
            raise ValueError('Invalid design source material revision: ' + operation_id)
        operations.append((intent, files))
    if not operations:
        return None
    operations.sort(key=lambda item: item[0]['material_revision'])
    first = operations[0][0]
    seed = _source_seed(submission, first['seed'])
    if creation.sha(seed) != creation.sha(first['seed']):
        raise ValueError('Original design source seed bytes/identity changed')
    anchor = _source_anchor(submission, seed)
    if first['anchor'] != anchor:
        raise ValueError('Design source anchor differs from its original task/submission/seed')
    _, profile = _source_storage(creation, frozen=first['storage_profile'])
    limits = profile['limits']
    if len(operations) > limits['operations']:
        raise ValueError('Design source operation count exceeds its frozen limit')
    if sum(size for _, files in operations for _, size in files.values()) > limits['journal_bytes']:
        raise ValueError('Design source journal exceeds its frozen raw-byte limit')
    packet, responses = seed['design_read']['packet'], []
    parent, records, pending, bodies = creation.sha(anchor), [], [], {}
    repair_required = set()
    repairing = {}
    if repair_id is not None:
        target = next((intent for intent, _ in operations if intent['operation_id'] == repair_id), None)
        if target is not None:
            repairing = {item['path']: item for item in target['material']['bodies']}
    for number, (intent, files) in enumerate(operations, 2):
        if pending or intent['material_revision'] != number or intent['parent_record_sha256'] != parent:
            raise ValueError('Design source journal has a missing parent, fork or pending tail')
        if intent['operation_id'] not in groups or groups[intent['operation_id']] is not files:
            raise ValueError('Design source operation ID differs from its original filename')
        if (intent['anchor'] != anchor or intent['seed'] != seed or intent['storage_profile'] != profile
                or intent['source_storage_profile_sha256'] != creation.sha(profile)):
            raise ValueError('Design source journal changes its frozen seed/storage identity')
        if (set(intent['recorded_actor']) != {'id', 'assurance'} or intent['recorded_actor']['assurance'] != 'local-process-only'
                or not isinstance(intent['recorded_actor']['id'], str)
                or re.fullmatch(r'unix:[0-9]+:.+', intent['recorded_actor']['id'], re.DOTALL) is None):
            raise ValueError('Unsupported saved design source recorder assurance')
        if files['intent'][1] > limits['intent_bytes']:
            raise ValueError('Saved design source intent exceeds its frozen byte limit')
        if (not isinstance(intent['recorded_at'], str)
                or datetime.fromisoformat(intent['recorded_at']).tzinfo is None):
            raise ValueError('Saved design source timestamp must retain its original timezone')
        material = _source_material(creation, intent['operation'], intent['submission'], packet, responses,
                                    seed, intent['recorded_at'], intent['recorded_actor']['id'], limits)
        expected = {**submission.expected, 'schema_version': 2, 'kind': 'task-design-source-operation',
            'operation': intent['operation'], 'project_revision': intent['project_revision'],
            'operation_id': intent['operation_id'], 'submission_sha256': creation.sha(submission.load()),
            'run_id': anchor['run_id'], 'anchor': anchor, 'seed': seed, 'storage_profile': profile,
            'source_storage_profile_sha256': creation.sha(profile), 'parent_record_sha256': parent,
            'material_revision': number, 'recorded_actor': intent['recorded_actor'], 'recorded_at': intent['recorded_at'],
            'submission': intent['submission'], 'material': material}
        if (type(intent['project_revision']) is not int or not 1 <= intent['project_revision'] <= creation.project['revision']
                or creation.sha(intent) != creation.sha(expected)):
            raise ValueError('Saved design source intent differs from its original binding/materials')
        result = _source_result(creation, intent)
        saved_result = files.get('result')
        if saved_result is not None and saved_result[0] != result:
            raise ValueError('Design source commit differs from its original intent')
        missing = _source_read_bodies(creation, material, limits, pending=saved_result is None, repairing=repairing)
        if saved_result is not None:
            repair_required.update(missing)
        if saved_result is None:
            pending.append({'operation_id': intent['operation_id'], 'intent_sha256': creation.sha(intent),
                            'material_revision': number, 'parent_record_sha256': parent})
            continue
        parent = creation.sha(result)
        if material['packet'] is not None:
            packet = material['packet']
        if material['response'] is not None:
            responses.append(material['response'])
        bodies.update({item['path']: item for item in material['bodies']})
        records.append({'operation_id': intent['operation_id'], 'operation': intent['operation'],
            'intent_sha256': creation.sha(intent), 'record_sha256': parent, 'parent_record_sha256': result['parent_record_sha256'],
            'material_revision': number, 'recorded_actor': intent['recorded_actor'], 'recorded_at': intent['recorded_at'],
            'packet': material['packet'], 'response': material['response']})
    view = {'anchor': anchor, 'storage_profile': profile, 'source_storage_profile_sha256': creation.sha(profile), 'status': 'recorded',
        'material_revision': len(records) + 1, 'source_chain_sha256': parent, 'records': records, 'pending': pending,
        'current_packet': packet, 'responses': responses, 'bodies': list(bodies.values()),
        'local_chain_checked': True, 'seed_previous_revision_chain_checked': False}
    intents = {intent['operation_id']: intent for intent, _ in operations}
    return {'seed': seed, 'view': view, 'intents': intents,
            'inventory_sha256': creation.sha({key: creation.sha(value) for key, value in intents.items()}),
            'repair_required': sorted(repair_required),
            'journal_bytes': sum(size for _, files in operations for _, size in files.values())}


def _source_output(creation, chain, *, operation_id=None, durable=None, online=False):
    from ergora.development.native import _design_public_result

    seed, view = chain['seed'], chain['view']
    result = {**seed, 'project_revision': creation.project['revision'],
              'seed_project_revision': seed['project_revision'], 'seed_phase': seed['phase'],
              'runtime_status': 'not_queried', 'design_source_read': view, 'read_only': durable is None,
              'design_source_validation': {'inventory_sha256': chain.get('inventory_sha256'),
                  'repair_required': chain.get('repair_required', []),
                  'inputs': [{'operation_id': item['operation_id'], 'intent_sha256': creation.sha(item),
                              'operation': item['operation'], 'submission': item['submission'],
                              'response': item['material']['response']} for item in chain['intents'].values()]}}
    if online:
        result['runtime_status'] = 'queried'
    else:
        result.pop('phase')
    if operation_id is not None:
        intent = chain['intents'].get(operation_id)
        result.update(operation_id=operation_id, durable=durable)
        if intent is None:
            result['status'] = 'not_recorded'
        else:
            result.update(intent_sha256=creation.sha(intent),
                status='prepared' if any(item['operation_id'] == operation_id for item in view['pending']) else 'committed')
    if chain.get('repair_required'):
        result['status'] = 'prepared'
    public = _design_public_result(result)
    creation.check_size(public, view['storage_profile']['limits']['inspection_bytes'], 'Complete design source inspection')
    return result


def _source_virtual(submission, seed, profile):
    creation = submission.creation
    anchor = _source_anchor(submission, seed)
    view = {'anchor': anchor, 'storage_profile': profile, 'source_storage_profile_sha256': creation.sha(profile), 'status': 'not_recorded',
        'material_revision': 1, 'source_chain_sha256': creation.sha(anchor), 'records': [], 'pending': [],
        'current_packet': seed['design_read']['packet'], 'responses': [], 'bodies': [],
        'local_chain_checked': False, 'seed_previous_revision_chain_checked': False}
    return {'seed': seed, 'view': view, 'intents': {}, 'journal_bytes': 0}


def _source_prospective(creation, chain, intent):
    view, material = chain['view'], intent['material']
    result = _source_result(creation, intent)
    bodies = {item['path']: item for item in view['bodies']}
    bodies.update({item['path']: item for item in material['bodies']})
    record = {'operation_id': intent['operation_id'], 'operation': intent['operation'],
        'intent_sha256': creation.sha(intent), 'record_sha256': creation.sha(result),
        'parent_record_sha256': intent['parent_record_sha256'], 'material_revision': intent['material_revision'],
        'recorded_actor': intent['recorded_actor'], 'recorded_at': intent['recorded_at'],
        'packet': material['packet'], 'response': material['response']}
    prospective = {**chain, 'view': {**view, 'status': 'recorded', 'local_chain_checked': True,
        'material_revision': intent['material_revision'], 'source_chain_sha256': creation.sha(result),
        'records': [*view['records'], record], 'pending': [], 'bodies': list(bodies.values()),
        'current_packet': material['packet'] if material['packet'] is not None else view['current_packet'],
        'responses': view['responses'] + ([material['response']] if material['response'] is not None else [])},
        'intents': {**chain['intents'], intent['operation_id']: intent}}
    limits = view['storage_profile']['limits']
    if len(prospective['view']['records']) > limits['operations']:
        raise ValueError('Design source operation count exceeds its frozen limit')
    raw_intent, raw_result = _source_json(creation, intent), _source_json(creation, result)
    if len(raw_intent) > limits['intent_bytes']:
        raise ValueError('Complete design source intent exceeds its frozen byte limit')
    if chain['journal_bytes'] + len(raw_intent) + len(raw_result) > limits['journal_bytes']:
        raise ValueError('Complete design source journal exceeds its frozen byte limit')
    _source_output(creation, prospective, operation_id=intent['operation_id'], durable=True)


def _source_prepare(submission, payload, chain):
    creation = submission.creation
    operation_id = creation.core.slug(payload['operation_id'])
    paths = _source_paths(creation, operation_id)
    if chain is not None and operation_id in chain['intents']:
        intent = chain['intents'][operation_id]
        if (intent['recorded_actor']['id'] != _Approval.actor() or intent['operation'] != payload['source_operation']
                or intent['submission'] != payload['source'] or intent['parent_record_sha256'] != payload['parent_record_sha256']
                or intent['run_id'] != payload['run_id'] or intent['anchor']['seed_receipt_sha256'] != payload['plan_sha256']):
            raise ValueError('Design source operation ID conflicts with its original submission/actor/binding')
        status = _source_output(creation, chain, operation_id=operation_id)
        status['read_only'] = False
        return {'created': False, 'source': status}
    if any(path.exists() for path in paths.values()):
        raise ValueError('Operation ID already belongs to another task approval journal operation')
    if chain is None:
        seed = _source_seed(submission, payload['preflight'])
        _, profile = _source_storage(creation, payload['source'].get('storage_limits'))
        if seed['design_read']['packet']['revision'] > profile['limits']['packet_revisions']:
            raise ValueError('Design source storage cannot contain its original seed packet')
        if any(item['bytes'] > profile['limits']['artifact_bytes'] for item in seed['materials']):
            raise ValueError('Design source storage cannot contain its original seed materials')
        chain = _source_virtual(submission, seed, profile)
    else:
        _source_storage(creation, payload['source'].get('storage_limits'), chain['view']['storage_profile'])
    view, seed = chain['view'], chain['seed']
    if payload['run_id'] != view['anchor']['run_id'] or payload['plan_sha256'] != view['anchor']['seed_receipt_sha256']:
        raise ValueError('Design source must pin the original seed run and receipt')
    if view['pending']:
        pending = view['pending'][0]
        raise ValueError('Resume pending design source operation ' + pending['operation_id'] + ': ' + pending['intent_sha256'])
    if payload['parent_record_sha256'] != view['source_chain_sha256']:
        raise ValueError('Design source parent changed; inspect the complete chain before submitting again')
    recorded_at = datetime.now(timezone.utc).isoformat()
    actor = {'id': _Approval.actor(), 'assurance': 'local-process-only'}
    material = _source_material(creation, payload['source_operation'], payload['source'], view['current_packet'],
        view['responses'], seed, recorded_at, actor['id'], view['storage_profile']['limits'])
    intent = {**submission.expected, 'schema_version': 2, 'kind': 'task-design-source-operation',
        'operation': payload['source_operation'], 'operation_id': operation_id,
        'submission_sha256': creation.sha(submission.load()), 'run_id': view['anchor']['run_id'],
        'anchor': view['anchor'], 'seed': seed, 'storage_profile': view['storage_profile'],
        'source_storage_profile_sha256': creation.sha(view['storage_profile']),
        'parent_record_sha256': view['source_chain_sha256'], 'material_revision': view['material_revision'] + 1,
        'recorded_actor': actor, 'recorded_at': recorded_at, 'submission': payload['source'], 'material': material}
    _source_prospective(creation, chain, intent)
    creation.adapter.publish(paths['intent'], intent)
    _source_confirm(creation, paths['intent'], _source_json(creation, intent))
    prepared = _source_scan(submission)
    status = _source_output(creation, prepared, operation_id=operation_id)
    status['read_only'] = False
    return {'created': True, 'source': status}


async def _source_operation(payload):
    submission = _Submission(payload)
    submission.submitted()
    creation = submission.creation
    operation = payload['operation']
    if operation == 'source-inspect':
        directory = creation.path('ergora/task-approvals/' + creation.task_id)
        if directory.exists():
            with _source_lock(creation):
                chain = _source_scan(submission)
                if chain is not None:
                    if payload['run_id'] != chain['view']['anchor']['run_id'] or payload['plan_sha256'] != chain['view']['anchor']['seed_receipt_sha256']:
                        raise ValueError('Design source inspection must pin its original seed/run')
                    return _source_output(creation, chain)
        from agent_platform.core import environment
        os.environ.update(environment())
        seed = await _plan(payload)
        if 'design_read' not in seed:
            raise ValueError('Design source operations require an original design packet')
        _, profile = _source_storage(creation)
        return _source_output(creation, _source_virtual(submission, seed, profile), online=True)
    operation_id = creation.core.slug(payload['operation_id'])
    if operation == 'source-status':
        directory = creation.path('ergora/task-approvals/' + creation.task_id)
        if not directory.exists():
            return {'operation_id': operation_id, 'status': 'not_recorded', 'runtime_status': 'not_queried', 'read_only': True}
        with _source_lock(creation):
            chain = _source_scan(submission)
            if chain is None:
                if any(path.exists() for path in _source_paths(creation, operation_id).values()):
                    raise ValueError('Operation ID belongs to a schema1 approval')
                return {'operation_id': operation_id, 'status': 'not_recorded', 'runtime_status': 'not_queried', 'read_only': True}
            return _source_output(creation, chain, operation_id=operation_id)
    preparing = operation in ('source-prepare', 'source-prepare-resume')
    if operation not in ('source-prepare', 'source-prepare-resume', 'source-commit', 'source-resume'):
        raise ValueError('Unsupported design source operation')
    with _source_lock(creation, writing=True, blocking=not preparing):
        chain = _source_scan(submission, repair_id=operation_id if operation != 'source-prepare' else None)
        if operation == 'source-prepare':
            return _source_prepare(submission, payload, chain)
        if chain is None or operation_id not in chain['intents']:
            raise ValueError('Design source recovery requires its original operation intent')
        intent = chain['intents'][operation_id]
        if creation.sha(intent) != payload['intent_sha256'] or intent['recorded_actor']['id'] != _Approval.actor():
            raise ValueError('Design source recovery requires the original intent and recorder')
        if preparing:
            return _source_output(creation, chain, operation_id=operation_id)
        if payload.get('source_inventory_sha256') != chain['inventory_sha256']:
            raise ValueError('Design source journal changed after application schema validation')
        result_path = _source_paths(creation, operation_id)['result']
        result_raw = _source_json(creation, _source_result(creation, intent))
        extra = 0 if result_path.exists() else len(result_raw)
        if chain['journal_bytes'] + extra > chain['view']['storage_profile']['limits']['journal_bytes']:
            raise ValueError('Source recovery commit would exceed its frozen journal limit')
        if result_path.exists() and creation.adapter.read_raw(result_path, len(result_raw)) != result_raw:
            raise ValueError('Source recovery commit conflicts with existing result bytes')
        _source_confirm(creation, _source_paths(creation, operation_id)['intent'], _source_json(creation, intent))
        for body in intent['material']['bodies']:
            _source_publish_body(creation, body)
        path = _source_paths(creation, operation_id)['result']
        result = _source_result(creation, intent)
        creation.adapter.publish(path, result)
        _source_confirm(creation, path, _source_json(creation, result))
        return _source_output(creation, _source_scan(submission), operation_id=operation_id, durable=True)


class _Approval:
    def __init__(self, payload: dict):
        self.payload = payload
        self.submission = _Submission(payload)
        self.creation = self.submission.creation
        self.core, self.sha = self.creation.core, self.creation.sha
        if payload['operation'] != 'list':
            self.select_decision(payload['decision_id'])

    def select_decision(self, decision_id: str) -> None:
        self.decision_id = self.core.slug(decision_id)
        prefix = 'ergora/task-approvals/' + self.creation.task_id + '/' + self.decision_id
        self.intent_path = self.creation.path(prefix + '.intent.json')
        self.attempt_path = self.creation.path(prefix + '.attempt.json')
        self.result_path = self.creation.path(prefix + '.result.json')

    def prepare(self) -> None:
        self.start_intent, self.run_id = self.submission.submitted()
        self.spec = self.submission.spec

    @staticmethod
    def actor() -> str:
        return f'unix:{os.getuid()}:{getpass.getuser()}'

    def record(self, revision: int, plan: str, receipt_id: str, created_at: int, actor: str, method=None) -> dict:
        approval = {'schema_version': 1, 'kind': 'plan-approval', 'task_id': self.creation.task_id,
                    'request_sha256': self.spec['request_sha256'], 'profile_sha256': self.spec['profile_sha256'],
                    'plan_sha256': plan, 'decision': 'approve', 'principal_type': 'human', 'actor_id': actor,
                    'role': 'owner', 'expires_at': created_at + 86400, 'revoked': False}
        if method is not None:
            plan_methods.require_addendum(method, self.submission.input.document, self.run_id,
                                          method['original_plan_sha256'])
            if plan_methods.approval_digest(method) != plan:
                raise ValueError('Approval must bind the exact composite Plan digest')
            approval['method_addendum'] = method
        return {**self.submission.expected, 'operation': 'approve', 'project_revision': revision,
                'submission_sha256': self.sha(self.start_intent), 'run_id': self.run_id,
                'decision_id': self.decision_id, 'plan_sha256': plan, 'receipt_id': receipt_id,
                'created_at': created_at, 'approval': approval}

    def load(self) -> dict | None:
        record = self.creation.optional(self.intent_path)
        if record is None:
            if self.attempt_path.exists() or self.result_path.exists():
                raise ValueError('Approval records have no original intent; reconcile before any decision')
            return None
        if (type(record.get('project_revision')) is not int or record['project_revision'] < 1
                or type(record.get('created_at')) is not int or record['created_at'] < 1
                or not isinstance(record.get('plan_sha256'), str) or not re.fullmatch('[0-9a-f]{64}', record['plan_sha256'])
                or not isinstance(record.get('receipt_id'), str) or not re.fullmatch('owner-[0-9a-f]{32}', record['receipt_id'])):
            raise ValueError('Invalid saved approval intent')
        actor = record['approval']['actor_id']
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError('Saved owner identity is invalid')
        expected = self.record(record['project_revision'], record['plan_sha256'], record['receipt_id'],
                               record['created_at'], actor, record['approval'].get('method_addendum'))
        if self.sha(record) != self.sha(expected):
            raise ValueError('Approval intent conflicts with its original project, submission, run or owner receipt')
        return record

    def approval_path(self, intent: dict):
        return self.creation.path('approvals/' + intent['receipt_id'] + '.json')

    def signal(self, intent: dict) -> dict:
        signal = {'request_sha256': self.spec['request_sha256'], 'plan_sha256': intent['plan_sha256'],
                  'receipt_id': intent['receipt_id']}
        if 'method_addendum' in intent['approval']:
            signal['method_addendum'] = intent['approval']['method_addendum']
        return signal

    def attempt(self, intent: dict) -> dict:
        return {'schema_version': 1, 'intent_sha256': self.sha(intent), 'workflow_id': intent['workflow_id'],
                'run_id': intent['run_id'], 'signal_name': 'approve_plan', 'signal_sha256': self.sha(self.signal(intent)),
                'approval_sha256': self.sha(intent['approval'])}

    def receipt(self, intent: dict, delivery: str, event_id: int | None) -> dict:
        if not ((delivery == 'acknowledged' and event_id is None)
                or (delivery == 'history' and type(event_id) is int and event_id > 0)):
            raise ValueError('Invalid approval signal evidence')
        return {**self.attempt(intent), 'delivery': delivery, 'history_event_id': event_id}

    def status(self, intent: dict | None) -> dict:
        result = {'project': self.creation.project['id'], 'project_revision': self.creation.project['revision'],
                  'task_id': self.creation.task_id, 'decision_id': self.decision_id, 'run_id': self.run_id,
                  'runtime_status': 'not_queried', 'approval_accepted': None, 'execution_success': None}
        if intent is None:
            return {**result, 'status': 'not_recorded'}
        receipt = self.creation.optional(self.result_path)
        attempt = self.creation.optional(self.attempt_path)
        approval = self.creation.optional(self.approval_path(intent))
        if approval is not None and self.sha(approval) != self.sha(intent['approval']):
            raise ValueError('Published owner receipt conflicts with its approval intent')
        if attempt is not None and (approval is None or self.sha(attempt) != self.sha(self.attempt(intent))):
            raise ValueError('Approval attempt has missing or inconsistent owner evidence')
        if receipt is not None and (attempt is None or self.sha(receipt) != self.sha(
                self.receipt(intent, receipt.get('delivery'), receipt.get('history_event_id')))):
            raise ValueError('Approval result conflicts with its original intent or signal checkpoint')
        if method := intent['approval'].get('method_addendum'):
            result.update(original_plan_sha256=method['original_plan_sha256'], method_addendum_sha256=self.sha(method))
        return {**result, 'workflow_id': intent['workflow_id'], 'intent_sha256': self.sha(intent),
                'status': 'requested' if receipt is not None else 'unknown' if attempt is not None else 'prepared',
                'plan_sha256': intent['plan_sha256'], 'owner_receipt_id': intent['receipt_id'],
                'expires_at': intent['approval']['expires_at'], 'owner_receipt_saved': approval is not None,
                'attempt_saved': attempt is not None, 'result_saved': receipt is not None,
                'signal_delivery': receipt['delivery'] if receipt is not None else None}

    def list_records(self) -> dict:
        self.prepare()
        if self.payload['run_id'] != self.run_id:
            raise ValueError('Approval lookup must pin the original submitted run ID')
        records = []
        for decision_id, files in sorted(_approval_journal(self.creation).items()):
            self.select_decision(decision_id)
            if 'intent' in files:
                intent = files['intent'][0]
            else:
                # A concurrent publication can appear partway through scandir.
                intent = self.creation.optional(self.intent_path, _SOURCE_LIMITS['intent_bytes'])
                if intent is None:
                    raise ValueError('Task approval journal has no original intent: ' + decision_id)
            if (intent.get('schema_version') == 2 and intent.get('kind') == 'task-design-source-operation'
                    and 'attempt' not in files):
                continue
            if intent.get('schema_version') != 1 or intent.get('operation') != 'approve':
                raise ValueError('Unrecognized task approval intent: ' + decision_id)
            intent = self.load()
            if intent is None:
                raise ValueError('Original approval intent disappeared during lookup: ' + decision_id)
            records.append(self.status(intent))
        return {'project': self.creation.project['id'], 'task_id': self.creation.task_id,
                'workflow_id': self.start_intent['workflow_id'], 'run_id': self.run_id,
                'runtime_status': 'not_queried', 'records': records}

    async def dispatch(self, intent: dict) -> dict:
        from dev_platform.adapter import publish
        from dev_platform.workflow import DevelopmentWorkflow

        if intent['approval']['actor_id'] != self.actor():
            raise ValueError('Approval owner identity changed; the original decision cannot be impersonated')
        if time.time() >= intent['approval']['expires_at']:
            raise ValueError('Approval expired; inspect the current plan and make a new explicit decision with a new ID')
        handle, _, _ = await self.submission.lookup_run(self.start_intent, intent['run_id'])
        status = await handle.query(DevelopmentWorkflow.status, rpc_timeout=timedelta(seconds=20))
        method = intent['approval'].get('method_addendum')
        original_plan = method['original_plan_sha256'] if method is not None else intent['plan_sha256']
        if (status['phase'] != 'AWAITING_PLAN_APPROVAL' or status['request_sha256'] != self.spec['request_sha256']
                or status['plan_sha256'] != original_plan):
            raise ValueError('Approval must name the exact plan currently awaiting an owner decision')
        if method is not None:
            _require_method_window(status, self.submission)
        publish(self.approval_path(intent), intent['approval'])
        self.core.write(self.attempt_path, self.attempt(intent))
        await handle.signal(DevelopmentWorkflow.approve_plan, self.signal(intent), rpc_timeout=timedelta(seconds=20))
        self.core.write(self.result_path, self.receipt(intent, 'acknowledged', None))
        return self.status(intent)

    async def reconcile(self, intent: dict) -> dict:
        handle, _, converter = await self.submission.lookup_run(self.start_intent, intent['run_id'])
        event_id = await find_signal_event(handle, converter, 'approve_plan', self.signal(intent))
        if event_id is not None:
            self.core.write(self.result_path, self.receipt(intent, 'history', event_id))
            return self.status(intent)
        return {**self.status(intent), 'reconciliation': 'signal_not_found',
                'instruction': 'Delivery remains uncertain; query the original run, do not resend this decision'}

    async def run(self) -> dict:
        operation = self.payload['operation']
        if operation == 'list':
            return self.list_records()
        if operation == 'status':
            self.prepare()
            return self.status(self.load())
        preparing = operation in ('prepare', 'prepare-resume')
        # Preparation runs while the parent reserves the project revision. It
        # must never retain the control DB while waiting for a remote task lock.
        with file_lock(self.creation.lock_path, blocking=not preparing):
            self.prepare()
            intent = self.load()
            if operation == 'prepare':
                if self.payload['run_id'] != self.run_id:
                    raise ValueError('Approval must pin the original submitted run ID')
                method = None
                if 'methods' in self.payload or 'original_plan_sha256' in self.payload:
                    method = plan_methods.addendum(self.submission.input.document, self.run_id,
                        self.payload.get('original_plan_sha256'), self.payload.get('methods'))
                if intent is not None:
                    if (intent['plan_sha256'] != self.payload['plan_sha256']
                            or intent['approval'].get('method_addendum') != method):
                        raise ValueError('Decision ID already names a different plan; inspect its original intent')
                    return {'created': False, 'approval': self.status(intent)}
                intent = self.record(self.creation.project['revision'], self.payload['plan_sha256'],
                                     'owner-' + uuid.uuid4().hex, int(time.time()), self.actor(), method)
                self.core.write(self.intent_path, intent)
                return {'created': True, 'approval': self.status(intent)}
            if intent is None or self.sha(intent) != self.payload['intent_sha256']:
                raise ValueError('Approval recovery requires the exact original decision intent digest')
            status = self.status(intent)
            if operation == 'prepare-resume':
                return status
            if operation not in ('dispatch', 'resume'):
                raise ValueError('Unsupported approval operation')
            if status['status'] == 'requested':
                return status
            if status['attempt_saved']:
                return await self.reconcile(intent) if operation == 'resume' else status
            return await self.dispatch(intent)


def main() -> None:
    """Approval locks only its network phase; plan inspection is read-only."""
    from agent_platform.core import Blocked, environment
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError

    inspecting, source = False, False
    try:
        payload = json.load(sys.stdin)
        source = payload['operation'].startswith('source-')
        inspecting = payload['operation'] == 'inspect-plan' or source
        if not source and payload['operation'] not in ('list', 'status', 'prepare', 'prepare-resume'):
            os.environ.update(environment())
        operation = (_source_operation(payload) if source else
                     _plan(payload) if inspecting else _Approval(payload).run())
        result = asyncio.run(asyncio.wait_for(operation, payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        if source:
            raise SystemExit('BLOCKED: Design source timed out; inspect the original source operation or seed before recovery') from error
        if inspecting:
            raise SystemExit('BLOCKED: Plan inspection timed out; query the original run before inspecting again') from error
        raise SystemExit('BLOCKED: Approval timed out; inspect the original decision ID and resume its saved intent') from error
    except RuntimeNotFound as error:
        if source:
            raise SystemExit('BLOCKED: Original design seed run was not found; preserve its ID and query its status') from error
        if inspecting:
            raise SystemExit('BLOCKED: Original plan run was not found; preserve the run ID and query its status') from error
        raise SystemExit('BLOCKED: Original approval run was not found; preserve this decision and reconcile the original run') from error
    except RPCError as error:
        name = 'Design source seed inspection' if source else 'Plan inspection' if inspecting else 'Approval'
        raise SystemExit('BLOCKED: ' + name + ' RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
