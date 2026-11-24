"""Dedicated native task clients and validated design handoffs."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from .._paths import IMPORT_ROOT
from ..native.files import _read_windows_contract
from ..native.resources import DATA, ROOT


FIXED_CHECK_PROOF_TIMEOUT = 20


def task_files(project: dict, *, task_id: str | None = None, limit: int = 50,
               after: str | None = None) -> dict:
    """Read native task files in a dedicated process; no optional SDK is loaded."""
    execution = project['registration']['definition']['execution']
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=execution['state_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        IMPORT_ROOT, ROOT / 'platform/local', ROOT / 'platform/upstream/platform')))
    try:
        result = subprocess.run([sys.executable, '-P', '-S', '-c',
                                 'from ergora.development.native import _task_files_main;_task_files_main()'],
                                input=json.dumps({'project': project['id'], 'repo': project['repo'],
                                                  'tracker': project['registration']['definition']['tracker'],
                                                  'task_id': task_id, 'limit': limit, 'after': after}),
                                capture_output=True, text=True, encoding='utf-8', env=environment, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise ValueError('Task contract reader timed out; inspect the selected execution storage before retrying') from error
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        raise ValueError(lines[-1] if lines else f'Task contract reader exited with status {result.returncode}')
    return json.loads(result.stdout)


def task_runtime_status(project: dict, spec: dict, *, run_id: str | None, timeout: int) -> dict:
    """Query the installed native transport without loading its globals into Web/CLI."""
    if importlib.util.find_spec('temporalio') is None:
        raise ValueError('Task runtime queries require the optional Temporal SDK; install ergora[temporal] in this environment')
    execution = project['registration']['definition']['execution']
    installation = Path(execution['installation'])
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=execution['state_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        IMPORT_ROOT, installation / 'local', installation / 'upstream/platform')))
    try:
        result = subprocess.run([sys.executable, '-P', '-c',
                                 'from ergora.development.runtime.status import main;main()'],
                                input=json.dumps({'spec': spec, 'run_id': run_id, 'timeout': timeout}, allow_nan=False),
                                capture_output=True, text=True, encoding='utf-8', env=environment, timeout=timeout + 5)
    except subprocess.TimeoutExpired as error:
        raise ValueError('Task runtime query process timed out; execution state remains unknown') from error
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        raise ValueError(lines[-1] if lines else f'Task runtime query process exited with status {result.returncode}')
    return json.loads(result.stdout)


def task_submission(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Use the registered full runtime for native admission and its local journal."""
    return _task_operation(project, home, 'submission', operation, payload, timeout)


def task_approval(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Use the same native lifecycle for exact owner decisions and signal recovery."""
    if operation.startswith('source-'):
        return task_design_source(project, home, operation, payload, timeout=timeout)
    if operation == 'inspect-plan':
        return task_plan(project, home, payload, timeout=timeout)
    return _task_operation(project, home, 'approval', operation, payload, timeout)


def task_plan(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Inspect the pending plan through the existing native approval boundary."""
    result = _task_operation(project, home, 'approval', 'inspect-plan', payload, timeout)
    return _checked_design_result(result)


def _checked_design_result(result: dict) -> dict:
    if 'design_read' not in result:
        if 'design_source_read' in result or 'design_source_validation' in result:
            raise ValueError('Design source handoff has no complete original design binding')
        return result
    # The registered native interpreter owns SDK/file reads, while the
    # application owns jsonschema. Never expose an unvalidated native handoff.
    from ..configuration.validation import validate

    read = result.pop('design_read')
    schema = json.loads((DATA / 'schemas/task-design-v1.json').read_text(encoding='utf-8'))
    profile, packet = read['profile'], read['packet']
    validate(profile, {'$defs': schema['$defs'], '$ref': '#/$defs/profile'}, 'Design inspection profile')
    limits = profile['limits']
    _validate_design_packet(packet, profile, schema)
    maximum = limits['inspection_bytes']
    if 'design_source_read' in result:
        _validate_source_read(result, schema, profile)
        maximum = result['design_source_read']['storage_profile']['limits']['inspection_bytes']
    result = _design_public_result({**result, 'design_read': read})
    raw = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if len(raw) > maximum:
        raise ValueError('Design inspection exceeds its creation read limit')
    return result


def _validate_design_packet(packet, profile, schema):
    from ..configuration.validation import validate

    limits = profile['limits']
    properties = {**schema['properties'], **{name: {**schema['properties'][name], 'maxItems': limits[name]}
                  for name in ('source_records', 'questions', 'knowledge_requirements')},
                  'revision': {**schema['properties']['revision'], 'maximum': limits['revisions']}}
    validate(packet, {**schema, 'properties': properties}, 'Design packet')


def validate_design_source_submission(value, operation, design_schema=None, profile=None):
    from ..configuration.validation import validate

    design_schema = design_schema or json.loads((DATA / 'schemas/task-design-v1.json').read_text())
    profile = profile or json.loads((DATA / 'design-profiles/framework-development-v1.json').read_text())
    source_schema = json.loads((DATA / 'schemas/task-design-source-v1.json').read_text())
    definitions = {**design_schema['$defs'], **source_schema['$defs']}
    if isinstance(value, dict) and set(value) & {'recorded_by', 'recorded_at', 'actor', 'recorded_actor', 'principal_type', 'role', 'attestation'}:
        raise ValueError('human_channel_unavailable: source submissions cannot provide recorder/owner evidence')
    if isinstance(value, dict) and isinstance(value.get('response'), dict):
        response = value['response']
        if response.get('origin') == 'owner-channel' or set(response) & {'recorded_by', 'recorded_at', 'actor', 'principal_type', 'role', 'attestation'}:
            raise ValueError('human_channel_unavailable: source responses cannot supply trusted/recorded actor evidence')
    branch = {'publish-design': 'publish', 'record-response': 'respond'}.get(operation)
    if branch is None:
        raise ValueError('Unsupported design source submission operation')
    validate(value, {'$defs': definitions, '$ref': '#/$defs/' + branch}, 'Design source submission')
    storage = json.loads((DATA / 'design-profiles/design-source-storage-v1.json').read_text())
    for name, limit in value.get('storage_limits', {}).items():
        if limit > storage['limits'][name]:
            raise ValueError('Design source storage limits may only tighten the built-in profile')
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if len(raw) > storage['limits']['intent_bytes']:
        raise ValueError('Complete source submission exceeds its source intent limit')
    if branch == 'publish':
        _validate_design_packet(value['packet'], profile, design_schema)
        for body in value['bodies']:
            validate({key: body[key] for key in ('path', 'sha256', 'bytes', 'media_type')},
                     {'$defs': design_schema['$defs'], '$ref': '#/$defs/body_ref'}, 'Design source body')
            encoded = body['text'].encode('utf-8')
            if len(encoded) != body['bytes'] or hashlib.sha256(encoded).hexdigest() != body['sha256']:
                raise ValueError('Design source body bytes/SHA differ from its original text')


def _validate_source_read(result, schema, profile):
    from ..configuration.validation import validate

    view, validation = result['design_source_read'], result['design_source_validation']
    source_schema = json.loads((DATA / 'schemas/task-design-source-v1.json').read_text())
    definitions = {**schema['$defs'], **source_schema['$defs']}
    validate(view, {'$defs': definitions, '$ref': '#/$defs/journal_view'}, 'Complete design source view')
    validate(validation, {'$defs': definitions, '$ref': '#/$defs/validation_handoff'}, 'Design source validation handoff')
    storage = json.loads((DATA / 'design-profiles/design-source-storage-v1.json').read_text())
    saved = view['storage_profile']
    from .envelopes import identity

    if view['source_storage_profile_sha256'] != identity(saved):
        raise ValueError('Saved design source storage profile digest differs from its complete object')
    if set(saved) != set(storage) or any(saved[key] != storage[key] for key in ('schema_version', 'kind', 'id')):
        raise ValueError('Unsupported saved design source storage profile')
    if set(saved['limits']) != set(storage['limits']):
        raise ValueError('Unsupported saved design source storage limit fields')
    for name, value in saved['limits'].items():
        if type(value) is not int or not 0 < value <= storage['limits'][name]:
            raise ValueError('Invalid saved design source storage limit: ' + name)
    if (type(view['material_revision']) is not int or view['material_revision'] < 1
            or not isinstance(view['records'], list) or not isinstance(view['pending'], list)
            or len(view['records']) + len(view['pending']) > saved['limits']['operations']):
        raise ValueError('Invalid complete source journal sequence/count')
    identifiers = [item['operation_id'] for item in validation['inputs']]
    if len(set(identifiers)) != len(identifiers) or len(identifiers) != len(view['records']) + len(view['pending']):
        raise ValueError('Incomplete or duplicate source validation records')
    for record in validation['inputs']:
        validate_design_source_submission(record['submission'], record['operation'], schema, profile)
        if record['response'] is not None:
            if record['response']['origin'] not in ('agent', 'reported-human'):
                raise ValueError('human_channel_unavailable: saved source response cannot authenticate an owner')
            validate(record['response'], {'$defs': schema['$defs'], '$ref': '#/$defs/response'}, 'Saved design response')
    _validate_design_packet(view['current_packet'], profile, schema)
    for record in view['records']:
        if record['packet'] is not None:
            _validate_design_packet(record['packet'], profile, schema)
        if record['response'] is not None:
            validate(record['response'], {'$defs': schema['$defs'], '$ref': '#/$defs/response'}, 'Saved design response')
    for body in view['bodies']:
        validate({key: body[key] for key in ('path', 'sha256', 'bytes', 'media_type')},
                 {'$defs': schema['$defs'], '$ref': '#/$defs/body_ref'}, 'Saved source body')
        encoded = body['text'].encode('utf-8')
        if len(encoded) != body['bytes'] or hashlib.sha256(encoded).hexdigest() != body['sha256']:
            raise ValueError('Saved source text differs from its raw-byte identity')


def _source_request_payload(operation: str, payload: dict, *, local_prepare: bool = False) -> None:
    from ..configuration.validation import validate

    common = {'task_id': {'type': 'string', 'pattern': '^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$'},
        'operation_id': {'type': 'string', 'pattern': '^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$'},
        'run_id': {'type': 'string', 'minLength': 1, 'maxLength': 128},
        **{name: {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
           for name in ('plan_sha256', 'parent_record_sha256', 'intent_sha256')},
        'source_operation': {'enum': ['publish-design', 'record-response']},
        'source': {'type': 'object'}, 'preflight': {'type': 'object'}}
    fields = {'source-inspect': ('task_id', 'run_id', 'plan_sha256'),
        'source-status': ('task_id', 'operation_id'),
        'source-prepare': ('task_id', 'operation_id', 'source_operation', 'source',
                           'parent_record_sha256', 'run_id', 'plan_sha256'),
        'source-prepare-resume': ('task_id', 'operation_id', 'intent_sha256'),
        'source-commit': ('task_id', 'operation_id', 'intent_sha256'),
        'source-resume': ('task_id', 'operation_id', 'intent_sha256')}.get(operation)
    if fields is None:
        raise ValueError('Unsupported design source operation')
    if local_prepare and operation == 'source-prepare':
        fields = (*fields, 'preflight')
    validate(payload, {'type': 'object', 'additionalProperties': False, 'required': list(fields),
                       'properties': {key: common[key] for key in fields}}, 'Design source operation payload')
    if 'run_id' in payload and payload['run_id'].strip() != payload['run_id']:
        raise ValueError('Design source run ID must retain its original bytes')


def _prepare_design_source(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Local revision-reservation phase; only checked tasks orchestration supplies preflight."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Design source timeout must be 1–60 seconds')
    if operation not in ('source-prepare', 'source-prepare-resume'):
        raise ValueError('Unsupported local source preparation')
    _source_request_payload(operation, payload, local_prepare=True)
    if operation == 'source-prepare':
        validate_design_source_submission(payload['source'], payload['source_operation'])
    result = _task_operation(project, home, 'approval', operation, payload, timeout)
    if operation == 'source-prepare':
        return {**result, 'source': _checked_design_result(result['source'])}
    return _checked_design_result(result)


def task_design_source(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Public source operations own their observation and cannot replace transport headers."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Design source timeout must be 1–60 seconds')
    _source_request_payload(operation, payload)
    if operation == 'source-prepare':
        validate_design_source_submission(payload['source'], payload['source_operation'])
        preflight = task_design_source(project, home, 'source-inspect',
            {key: payload[key] for key in ('task_id', 'run_id', 'plan_sha256')}, timeout=timeout)
        return _prepare_design_source(project, home, operation, {**payload, 'preflight': preflight}, timeout=timeout)
    if operation in ('source-commit', 'source-resume'):
        prepared = _task_operation(project, home, 'approval', 'source-prepare-resume', payload, timeout)
        inventory = prepared['design_source_validation']['inventory_sha256']
        _checked_design_result(prepared)
        payload = {**payload, 'source_inventory_sha256': inventory}
    result = _task_operation(project, home, 'approval', operation, payload, timeout)
    return _checked_design_result(result)


def _design_view(read: dict, plan_sha256: str, source=None) -> dict:
    from .design import inspect_packet
    from .envelopes import identity

    profile, packet = read['profile'], read['packet']
    inspection = inspect_packet(packet, profile, read['expected'], read['sources'], read['work_unit_ids'])
    snapshot = {'seed_plan_sha256': plan_sha256, 'packet_content_sha256': identity(packet),
                'design_profile_sha256': identity(profile), 'sources': inspection['sources']}
    design = {**snapshot, 'inspection_sha256': identity(snapshot), 'packet': packet,
        **inspection, 'inspection_only': True, 'runtime_enforced': False,
        'profile': {'source': 'built-in-companion-profile', 'frozen_for_task': False, 'document': profile},
        'binding_assurance': {'checked_original_fields': list(read['expected']),
                              'manifest_bound': 'manifest_digest' in read['expected'],
                              'work_unit_mapping_checked': read['work_unit_ids'] is not None,
                              'previous_revision_chain_checked': False,
                              'freshness_basis': 'packet-declared-observation'},
        'actor_assurance': {'status': 'unavailable', 'owner_binding': 'not_frozen_in_original_admission'},
        'capabilities': {'approve_design': False, 'resolve_questions': False, 'execute': False}}
    if source is not None:
        facts = dict(read['sources'])
        bodies = {item['path']: item for item in source['bodies']}
        for record in source['current_packet']['source_records']:
            if record['access'] == 'reference_only':
                facts[record['id']] = {'status': 'reference_only'}
            elif record['body']['path'] in bodies:
                body = bodies[record['body']['path']]
                facts[record['id']] = {'status': 'read', 'sha256': body['sha256'], 'bytes': body['bytes']}
        design['source_journal'] = {**source, 'current_inspection': inspect_packet(source['current_packet'],
            profile, read['expected'], facts, read['work_unit_ids'])}
    return design


def _design_public_result(result: dict) -> dict:
    repair = result.get('design_source_validation', {}).get('repair_required', [])
    if repair:
        return {key: value for key, value in {**result, 'source_repair_required': repair,
            'inspection_only': True, 'runtime_enforced': False}.items()
            if key not in ('design_read', 'design_source_read', 'design_source_validation', 'materials', 'receipt')}
    public = {key: value for key, value in result.items()
              if key not in ('design_read', 'design_source_read', 'design_source_validation')}
    if 'design_read' in result:
        public['design'] = _design_view(result['design_read'], result['plan_sha256'], result.get('design_source_read'))
    return public


def task_events(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Read bounded original-run metadata through its native query entry."""
    return _task_operation(project, home, 'events', 'inspect-events', payload, timeout)


def task_job(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Read the original scheduled job's trusted receipt and bounded text evidence."""
    return _task_operation(project, home, 'evidence', 'inspect-job', payload, timeout)


def task_candidate_verification(project: dict, home: Path, source: dict, *, deadline: float,
                                stop_requested=None) -> dict:
    """Read the pinned verification under the calling graph's original deadline."""
    from ergora.development.verification import validate_readback_source

    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError('Candidate verification requires an absolute monotonic deadline')
    return _task_operation(project, home, 'evidence', 'read-candidate-verification',
                           {'source': validate_readback_source(source)}, 20, deadline=deadline,
                           stop_requested=stop_requested)


def task_fixed_candidate_check(project: dict, home: Path, operation: str, payload: dict) -> dict:
    """Use the registered native runtime for one independent fixed-check operation."""
    return _task_operation(project, home, 'candidate_checks', operation, payload, 20)


def task_fixed_check_proof(project: dict, home: Path, source: dict, review: dict, *, deadline: float,
                           stop_requested=None, lock_fd: int | None = None, original_wait_seconds: int | None = None) -> dict:
    """Read an original fixed check under the standalone graph's deadline."""
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError('Fixed check proof requires an absolute monotonic deadline')
    timeout = source.get('wait_seconds', FIXED_CHECK_PROOF_TIMEOUT)
    if original_wait_seconds is not None:
        if (lock_fd is None or 'wait_seconds' in source or type(original_wait_seconds) is not int
                or not 1 <= original_wait_seconds <= 3600):
            raise ValueError('Original wait allowance requires a locked completed fixed-check reread')
        # Retain the saved transport cutoff even if it is later than a fresh completed read's limit.
        timeout = original_wait_seconds
    elif 'wait_seconds' in source:
        deadline = min(deadline, time.monotonic() + timeout)
    return _task_operation(project, home, 'candidate_checks', 'prove-fixed-check',
                           {'source': source, 'operation_id': source['operation_id'], 'job_sha256': source['job_sha256'],
                            'review': review}, timeout, deadline=deadline, stop_requested=stop_requested,
                           **({'lock_fd': lock_fd} if lock_fd is not None else {}))


def task_cancellation(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Use the native cancellation guard and preserve signal delivery uncertainty."""
    return _task_operation(project, home, 'cancellation', operation, payload, timeout)


def task_work_priority(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    return _task_operation(project, home, 'work_priority', operation, payload, timeout)


def task_export(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Export the original run's candidate through its recoverable native boundary."""
    return _task_operation(project, home, 'export', operation, payload, timeout)


def task_external_status(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Inspect original-run external evidence through the registered native process."""
    return _task_operation(project, home, 'reconciliation', 'inspect', payload, timeout)


def task_evidence(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Index the closed original run's contracts and verified published evidence."""
    return _task_operation(project, home, 'reconciliation', 'inspect-index', payload, timeout)


def task_handoff(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Collect original published evidence into the explicitly selected new file."""
    return _task_operation(project, home, 'reconciliation', 'export-handoff', payload, timeout)


def task_reconciliation(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Reconcile the original closed run through its durable native boundary."""
    return _task_operation(project, home, 'reconciliation', operation, payload, timeout)


def _bounded_task_read(command, home, request, environment, timeout, deadline, stop_requested, *, lock_fd=None):
    from ergora.runtime import processes

    with tempfile.TemporaryDirectory(prefix='ergora-task-read-') as temporary:
        output = Path(temporary) / 'reader'
        result = processes.run(command, home, output, timeout, request, environment,
                               deadline=deadline, stop_requested=stop_requested,
                               **({'lock_fd': lock_fd} if lock_fd is not None else {}))
        if result['status'] == 'cancelled':
            raise KeyboardInterrupt
        if result['status'] == 'timed_out' or time.monotonic() >= deadline:
            raise TimeoutError('Candidate verification evidence read reached its deadline')
        with (output / 'stdout.txt').open('rb') as stream:
            stdout = stream.read(1_048_577)
        with (output / 'stderr.txt').open('rb') as stream:
            stderr = stream.read(8192)
        if len(stdout) > 1_048_576:
            raise ValueError('Candidate verification response exceeds 1 MiB')
        return subprocess.CompletedProcess(command, result['returncode'], stdout.decode('utf-8'),
                                           stderr.decode('utf-8', errors='replace'))


def _task_operation(project: dict, home: Path, component: str, operation: str, payload: dict, timeout: int, *,
                    deadline: float | None = None, stop_requested=None, lock_fd: int | None = None) -> dict:
    inspection = {'inspect-plan': 'Plan', 'inspect-events': 'Task event', 'inspect-job': 'Job evidence',
                  'read-candidate-verification': 'Candidate verification evidence',
                  'inspect-index': 'Task evidence index', 'inspect-amendment': 'Amendment checkpoint',
                  'inspect-amendment-release': 'Amendment release',
                  'export-handoff': 'Task handoff'}.get(operation)
    if sys.platform != 'linux':
        raise ValueError(f'Formal task {component} requires Linux; use the registered Linux runtime in WSL2')
    execution = project['registration']['definition']['execution']
    installation = Path(execution['installation'])
    interpreter = installation / '.venv/bin/python'
    if not interpreter.is_file():
        raise ValueError(f'Selected reference runtime is incomplete; install its full Linux environment before task {component}')
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=execution['state_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        IMPORT_ROOT, installation / 'local', installation / 'upstream/platform')))
    command = [str(interpreter), '-P', '-c', f'from ergora.development.runtime.{component} import main;main()']
    request = {**payload, 'project': project, 'control_home': str(home), 'operation': operation, 'timeout': timeout}
    try:
        if deadline is None:
            result = subprocess.run(command, input=json.dumps(request, allow_nan=False), capture_output=True,
                                    text=True, encoding='utf-8', env=environment, timeout=timeout + 5)
        else:
            deadline = min(deadline, time.monotonic() + timeout)
            request['deadline'] = deadline
            result = _bounded_task_read(command, home, json.dumps(request, allow_nan=False), environment,
                                        timeout, deadline, stop_requested,
                                        **({'lock_fd': lock_fd} if lock_fd is not None else {}))
    except subprocess.TimeoutExpired as error:
        if operation.startswith('source-'):
            raise ValueError('Design source process timed out; inspect saved source state before recovering this operation') from error
        if operation == 'export-handoff':
            raise ValueError('Task handoff process timed out; inspect the output file before collecting again') from error
        if inspection:
            raise ValueError(inspection + ' inspection process timed out; query the original run before inspecting again') from error
        if component == 'work_priority':
            raise ValueError('Work priority process timed out; inspect the original decision with task work-priority') from error
        if component == 'candidate_checks':
            raise ValueError('Candidate check response timed out; inspect its original operation with task candidate-check-status') from error
        raise ValueError(f'Task {component} process timed out; inspect task {component} and resume its original intent') from error
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        detail = lines[-1] if lines else f'Native {component} process exited with status {result.returncode}'
        if operation.startswith('source-'):
            raise ValueError(detail + '; inspect task design operation before recovering its original intent')
        if inspection:
            raise ValueError(detail)
        if component in ('work_priority', 'candidate_checks'):
            raise ValueError(detail)
        raise ValueError(detail + f'; inspect task {component} before any recovery')
    decoded = json.loads(result.stdout)
    if deadline is not None:
        if stop_requested is not None and stop_requested():
            raise KeyboardInterrupt
        if time.monotonic() >= deadline:
            raise TimeoutError('Candidate verification evidence read reached its deadline')
    return decoded


def _task_files_main():
    import base64
    import heapq
    from agent_platform.core import STATE, Blocked, slug
    from dev_platform import adapter
    from dev_platform.contracts import validate_spec
    from . import envelopes as task_envelopes

    try:
        payload = json.load(sys.stdin)
        slug(payload['project'])
        if payload['task_id'] is not None:
            slug(payload['task_id'])
        after = payload['after']
        if after is not None:
            if not isinstance(after, str) or len(after) > 2048:
                raise ValueError('Invalid task directory cursor')
            try:
                after = os.fsdecode(base64.b64decode(after.encode('ascii'), altchars=b'-_', validate=True))
            except ValueError as error:
                raise ValueError('Invalid task directory cursor') from error
        if os.name == 'nt':
            adapter.read_raw = _read_windows_contract
        root = STATE.resolve()
        directory = adapter.safe_file(root, 'tasks')

        def document(task_id, filename):
            path = adapter.safe_file(root, 'tasks/' + slug(task_id) + '/' + filename)
            if not path.is_file():
                raise ValueError('Task contract must be an existing regular file: ' + filename)
            raw = adapter.read_raw(path, task_envelopes.WIRE_LIMIT if filename == 'task.spec.json' else 1_048_576)
            try:
                value = json.loads(raw.decode('utf-8'))
            except ValueError as error:
                if len(raw) > 1_048_576:
                    raise ValueError('Task contract exceeds size limit: ' + filename) from error
                raise ValueError('Invalid task JSON: ' + filename) from error
            if not isinstance(value, dict):
                raise ValueError('Task JSON must be an object: ' + filename)
            if filename == 'task.spec.json' and len(raw) > task_envelopes.wire_limit(value):
                raise ValueError('Task admission exceeds its wire byte limit')
            if filename == 'project.json' and not all(isinstance(value.get(key), str) and value[key]
                                                      for key in ('name', 'repo')):
                raise ValueError('Task project ownership fields are missing or invalid')
            return value, hashlib.sha256(raw).hexdigest()

        def owns(project):
            return (project.get('name') == payload['project']
                    and project.get('repo') == payload['repo'])

        def inspect(task_id, project, *, detail=False):
            if not owns(project):
                raise ValueError('Task does not belong to the selected project and Git repository')
            spec, file_sha = document(task_id, 'task.spec.json')
            envelope = spec
            spec, composition = task_envelopes.unwrap(envelope)
            validate_spec(spec)
            request = spec['request']
            if request['task_id'] != task_id:
                raise ValueError('Task ID differs from its native directory')
            if (project.get('tracker') != payload['tracker']
                    or {key: request['tracker'][key] for key in ('kind', 'project')} != payload['tracker']):
                raise ValueError('Task tracker differs from the selected project')
            if request['repository']['base_sha'] != project.get('base_sha'):
                raise ValueError('Task baseline differs from its frozen project')
            item = {'task_id': task_id, 'task_type': request['task_type'],
                    'goal': request['input']['goal'][:200], 'tracker': request['tracker'],
                    'request_sha256': spec['request_sha256'], 'profile_sha256': spec['profile_sha256'],
                    'spec_file_sha256': file_sha, 'runtime_status': 'not_queried'}
            if composition is not None:
                item['composition'] = task_envelopes.summary(envelope)
            if detail:
                snapshot = adapter.safe_file(root, 'tasks/' + task_id + '/agent-bindings.json')
                bindings, bindings_sha = document(task_id, 'agent-bindings.json') if snapshot.exists() else (None, None)
                if bindings is not None and bindings.get('reference_project') != payload['project']:
                    raise ValueError('Frozen agent snapshot project mismatch')
                item.update(spec=spec, frozen_project=project, agent_bindings=bindings,
                            agent_bindings_file_sha256=bindings_sha)
                if composition is not None:
                    item['admission_envelope'] = envelope
            return item

        if payload['task_id'] is not None:
            project, _ = document(payload['task_id'], 'project.json')
            result = inspect(payload['task_id'], project, detail=True)
        else:
            # Bound both resident candidate names and per-page file reads. A cursor
            # advances across scanned entries even when they belong to other projects.
            if directory.exists():
                with os.scandir(directory) as entries:
                    names = heapq.nsmallest(payload['limit'] + 1, (entry.name for entry in entries
                        if not entry.name.startswith('.') and (after is None or entry.name > after)))
            else:
                names = []
            result = {'items': [], 'errors': [], 'unreadable_count': 0, 'inspected_entries': min(len(names), payload['limit']),
                      'next_after': base64.urlsafe_b64encode(os.fsencode(names[payload['limit'] - 1])).decode('ascii') if len(names) > payload['limit'] else None,
                      'runtime_status': 'not_queried'}
            for name in names[:payload['limit']]:
                try:
                    project, _ = document(name, 'project.json')
                except (OSError, ValueError, Blocked):
                    result['unreadable_count'] += 1
                    continue
                if not owns(project):
                    continue
                try:
                    result['items'].append(inspect(name, project))
                except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
                    result['errors'].append({'task_id': name, 'error': str(error)})
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
