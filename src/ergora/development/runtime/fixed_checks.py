"""Run and validate fixed candidate observations inside an admitted native job."""

import hashlib
import json
import os
from pathlib import Path
import re

from agent_platform import executor as original
from agent_platform.core import CONFIG, ROOT, STATE, read, require, write
from dev_platform.adapter import FileAdapter, identifier, safe_file
from dev_platform.contracts import canonical_sha

from ergora.development import envelopes, verification
from ergora.runtime import budget_clock
from ergora.storage.assets import inventory_tree
from ergora.training.materials import decode_record, read_raw as read_fixed_raw


KIND = envelopes.FIXED_CANDIDATE_CHECK
FIELDS = {'task_id', 'run_id', 'candidate_sha', 'export_intent_sha256', 'verification_sha256',
          'packet', 'packet_sha256', 'manifest', 'manifest_digest', 'instance',
          'wall_seconds', 'cleanup_seconds'}


def check_adapter() -> FileAdapter:
    config = read(CONFIG / 'adapter.json')
    roots = {name: str(STATE / name) for name in ('requests', 'receipts', 'artifacts', 'fences', 'approvals')}
    require(all(config.get(key) == value for key, value in roots.items()), 'Candidate check adapter roots drifted')
    return FileAdapter({**config, **{key: str(Path(value) / KIND) for key, value in roots.items()}})


def decode_check_request(text: str, digest: str) -> dict:
    require(isinstance(text, str), 'Candidate check requires the original confirmed request text')
    raw = text.encode('utf-8')
    require(len(raw) <= 65_536 and hashlib.sha256(raw).hexdigest() == digest,
            'Candidate check request bytes differ from the confirmed digest')
    return _check_request(decode_record(raw))


def _check_request(value: dict) -> dict:
    require(isinstance(value, dict) and value.keys() == FIELDS, 'Candidate check requires the exact authorization fields')
    task_id, run_id, candidate = (value[key] for key in ('task_id', 'run_id', 'candidate_sha'))
    require(isinstance(task_id, str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', task_id),
            'Invalid original task ID')
    require(isinstance(run_id, str) and 1 <= len(run_id) <= 128 and run_id.strip() == run_id, 'Invalid original run ID')
    require(isinstance(candidate, str) and re.fullmatch('[a-f0-9]{40}', candidate),
            'Fixed candidate checks require a full SHA-1 Git commit')
    for key in ('verification_sha256', 'export_intent_sha256', 'packet_sha256', 'manifest_digest'):
        require(isinstance(value[key], str) and re.fullmatch('[a-f0-9]{64}', value[key]), 'Invalid ' + key)
    for key in ('packet', 'manifest'):
        require(isinstance(value[key], str) and len(value[key]) <= 4096 and Path(value[key]).is_absolute(), 'Invalid ' + key)
    require(isinstance(value['instance'], str) and value['instance'].startswith('root/') and len(value['instance']) <= 1024,
            'Select the exact correctness-review instance')
    wall, cleanup = value['wall_seconds'], value['cleanup_seconds']
    require(type(wall) is int and type(cleanup) is int and 1 <= cleanup < wall <= 3600, 'Invalid check and cleanup allowance')
    return value


def operation_scope(project: str, operation_id: str) -> str:
    require(isinstance(operation_id, str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', operation_id),
            'Invalid candidate check operation ID')
    return 'check-' + canonical_sha({'project': project, 'operation_id': operation_id})[:40]


def check_context(admission: dict) -> dict:
    task_id = operation_scope(admission['project'], admission['operation_id'])
    return {'kind': KIND, 'task_id': task_id, 'stage': KIND, 'request_sha256': admission['sha256'],
            'job_id': task_id + '-' + canonical_sha({'stage': KIND})[:24], 'admission': admission}


def check_workspace(context: dict) -> Path:
    return safe_file(STATE, 'workspaces/' + KIND + '/' + identifier(context['task_id']) + '/jobs/' + identifier(context['job_id']))


def read_record(path: Path, limit: int = 1_048_576) -> dict:
    return decode_record(read_fixed_raw(path, limit))


def work_remaining(admission: dict, *, cleanup=False) -> float:
    request = admission['request']
    return budget_clock.remaining(admission['budget'], request['wall_seconds'],
                                  0 if cleanup else request['cleanup_seconds'])


def check_project(project: dict, home: Path, admission: dict) -> None:
    from ergora.development.design import require_execution_support

    require_execution_support(project)
    registered = project['registration']
    execution = registered['definition']['execution']
    require(registered['status'] == 'published' and registered['sha256'] == admission['registration_sha256'],
            'Candidate check requires its original published registration')
    require(project['revision'] == admission['project_revision'] and project['repo'] == admission['repo'],
            'Candidate check project or revision changed')
    require(execution == admission['execution'] and all(Path(execution[key]) == actual for key, actual in (
        ('installation', ROOT), ('config_directory', CONFIG), ('state_directory', STATE))),
        'Candidate check execution directories differ from its authorization')
    require(home == Path(admission['control_home']) and home.resolve() == home, 'Candidate check control directory changed')
    require(verification.snapshot(project) == admission['verification'], 'Candidate check declaration changed')
    for relative, expected in registered['files'].items():
        require(canonical_sha(read_record(safe_file(CONFIG, relative))) == canonical_sha(expected), 'Candidate check registration files drifted')
    verification.validate_checks(admission['verification']['checks'], installation=ROOT, live=True)


def authorized(adapter: FileAdapter, envelope: dict) -> dict:
    context = envelope['context']
    admission = context['admission']
    require(admission.keys() == {'schema_version', 'kind', 'project', 'project_revision', 'registration_sha256',
                                'execution', 'repo', 'control_home', 'operation_id', 'actor_id', 'request',
                                'request_text', 'request_file_sha256', 'verification', 'export_receipt_sha256', 'budget', 'sha256'},
            'Candidate check authorization has unsupported or missing fields')
    source = decode_check_request(admission['request_text'], admission['request_file_sha256'])
    require(source == admission['request'], 'Candidate check request differs from its confirmed input bytes')
    fixed = verification.validate_snapshot(admission['verification'])
    identity = {key: value for key, value in admission.items() if key != 'sha256'}
    require(type(admission['schema_version']) is int and admission['schema_version'] == 1 and admission['kind'] == KIND
            and admission['sha256'] == canonical_sha(identity), 'Candidate check authorization digest changed')
    require(source['verification_sha256'] == fixed['sha256'] and all(
        fixed[key] == admission[key] for key in ('project', 'project_revision', 'registration_sha256')),
        'Candidate check authorization differs from its frozen declaration')
    budget = admission['budget']
    budget_clock.validate(budget, source['wall_seconds'])
    require(budget.keys() == {*budget_clock.FIELDS, 'sha256'}
            and budget['sha256'] == canonical_sha({key: budget[key] for key in budget_clock.FIELDS}),
            'Candidate check budget identity changed')
    expected = check_context(admission)
    require(envelope == {'schema_version': 1, 'job_id': expected['job_id'],
                         'job_sha256': canonical_sha(expected), 'context': expected},
            'Candidate check request envelope differs from its authorization')
    saved = read_record(adapter.path('approvals', expected['task_id'] + '.json'))
    require(saved == admission, 'Candidate check has no matching operator authorization')
    return admission


def check_subject(envelope: dict) -> dict:
    context = envelope['context']
    admission = context['admission']
    return {'task_id': context['task_id'], 'job_id': envelope['job_id'], 'job_sha256': envelope['job_sha256'],
            'admission_sha256': admission['sha256'], 'authorization_sha256': admission['sha256'],
            'verification_sha256': admission['verification']['sha256'], 'registration_sha256': admission['registration_sha256'],
            'candidate_sha': admission['request']['candidate_sha']}


def validate_receipt(adapter: FileAdapter, envelope: dict, receipt: dict) -> dict | None:
    admission = authorized(adapter, envelope)
    subject = check_subject(envelope)
    expected_actor = {'id': 'local-ci', 'kind': 'ci', 'role': 'fixed-checker'}
    require(receipt['candidate_sha'] == subject['candidate_sha']
            and all(receipt['actor'][key] == value for key, value in expected_actor.items()),
            'Candidate check receipt differs from its authorized candidate or verifier')
    if not receipt['artifacts']:
        require(receipt['state'] != 'SUCCEEDED' and not receipt['checks'], 'Candidate check outcome lacks its scoped report')
        return None
    require(len(receipt['artifacts']) == 1 and receipt['state'] in ('SUCCEEDED', 'FAILED'), 'Invalid scoped check artifacts')
    artifact = receipt['artifacts'][0]
    relative = f"{subject['task_id']}/{subject['job_id']}/fixed-check-results.json"
    require(artifact['path'] == relative and artifact['name'] == 'fixed-check-results', 'Invalid scoped check report identity')
    raw = read_fixed_raw(adapter.path('artifacts', relative), verification.ARTIFACT_BYTES)
    require(hashlib.sha256(raw).hexdigest() == artifact['sha256'], 'Scoped check report bytes changed')
    report = verification.validate_fixed_report(decode_record(raw), admission['verification'], subject,
        process_root=STATE / 'processes', workspace=check_workspace(envelope['context']),
        fence=adapter.path('fences', subject['task_id'] + '.json'), require_pass=receipt['state'] == 'SUCCEEDED')
    checks = report['verification']['checks']
    require(receipt['state'] == ('SUCCEEDED' if report['verification']['passed'] else 'FAILED')
            and receipt['checks'] == check_rows(checks), 'Receipt checks differ from the complete scoped report')
    return report


def check_rows(checks: dict) -> list[dict]:
    return [{'id': ident, 'status': 'pass' if item['observations']['passed'] else 'fail',
             'artifact': 'fixed-check-results'} for ident, item in sorted(checks.items())]


def run_fixed_checks(fixed, subject, ordinary, *, checkout, scratch, materials, sandbox,
                     fence, mirror, deadline, require_remaining):
    """Execute one already authorized, owned fixed-observation bundle."""
    candidate = subject['candidate_sha']
    verification.validate_checks(fixed['checks'], installation=ROOT, live=True)
    require(original.git(checkout, 'rev-parse', 'HEAD').stdout.strip() == candidate,
            'Fixed verification checkout differs from the exact expected candidate')
    before = original.git(checkout, 'status', '--porcelain=v1', '-z', '--untracked-files=all').stdout
    require(not before, 'Fixed verification requires an unchanged candidate checkout')
    result = {'subject': subject, 'required_checks': sorted(fixed['checks']), 'checks': {}, 'passed': False}
    inputs, candidate_files, requests = {}, {}, {}
    for ident, check in sorted(fixed['checks'].items()):
        require_remaining()
        repository = materials.repository_sources({'candidate': candidate}, check['candidate_paths'])
        inputs[ident] = verification.script_input(ident, check, subject, repository)
        binding = verification.process_binding(inputs[ident])
        name = verification.process_name(binding)
        output = safe_file(scratch, name)
        command = [check['runtime']['executable'], '-I', '-S', str(output / 'source' / check['entrypoint']),
                   str(output / 'input.json'), str(output / 'observations.json')]
        requests[ident] = sandbox.request(name, checkout, output, command,
            writable=False, fence=fence, timeout=check['wall_seconds'], binding=binding, deadline=deadline)
        for name, item in repository['candidate']['files'].items():
            candidate_files[name] = repository['blobs'][item['git_object']]['text']
    require(sum(len(text.encode('utf-8')) for text in candidate_files.values()) <= verification.CANDIDATE_BYTES,
            'Fixed candidate text exceeds aggregate capacity')
    # All exact inputs are known before the first process request. Include
    # ordinary logs and reserve the maximum escaped observation/comparison
    # contribution; the actual complete report is checked again below.
    verification.capacity({'ordinary': ordinary, 'verification': fixed, 'inputs': inputs, 'requests': requests},
        verification.ARTIFACT_BYTES, 'Fixed verification execution', reserve=verification.RESULT_RESERVE, compact=True)
    raw_total = 0
    for ident, check in sorted(fixed['checks'].items()):
        require_remaining()
        input_value = inputs[ident]
        binding = verification.process_binding(input_value)
        name = verification.process_name(binding)
        output = safe_file(scratch, name)
        source = safe_file(output, 'source')
        process_folder = STATE / 'processes' / name
        require(not (output / 'observations.json').exists() or (process_folder / 'terminal.json').exists(),
                'Fixed observations exist without their original completed process')
        source.mkdir(parents=True, exist_ok=True, mode=0o700)
        for relative, item in check['source']['files'].items():
            path = safe_file(source, relative)
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            raw = item['text'].encode('utf-8')
            if not path.exists():
                with path.open('xb') as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                path.chmod(0o600 | item['executable_bits'])
            require(read_fixed_raw(path, verification.SOURCE_BYTES) == raw, 'Frozen fixed source bytes changed')
        require(inventory_tree(source, label='Fixed source')[0] == check['source']['digest'],
                'Materialized fixed source inventory changed')
        write(output / 'input.json', input_value)
        require(verification.sha(json.loads(read_fixed_raw(output / 'input.json'))) == verification.sha(input_value),
                'Materialized fixed script input changed')
        verification.validate_checks({ident: check}, installation=ROOT, live=True)
        require_remaining()
        timeout, original_deadline = check['wall_seconds'], deadline
        if (process_folder / 'request.json').exists():
            saved = read(process_folder / 'request.json')
            timeout, original_deadline = saved['timeout'], saved['deadline']
            require(original_deadline == deadline, 'Original fixed process cutoff differs from its Job owner')
        command = [check['runtime']['executable'], '-I', '-S', str(source / check['entrypoint']),
                   str(output / 'input.json'), str(output / 'observations.json')]
        code = sandbox.run(name, checkout, output, command, writable=False, fence=fence,
            timeout=timeout, gitdir=mirror, binding=binding, deadline=original_deadline)
        process = {'name': name, **{key: json.loads(read_fixed_raw(process_folder / (key + '.json')))
                                  for key in ('request', 'started', 'terminal')}}
        try:
            raw = read_fixed_raw(output / 'observations.json', verification.OBSERVATION_BYTES - raw_total)
        except FileNotFoundError:
            raw = None
        raw_total += len(raw) if raw is not None else 0
        observed = verification.observations(check, raw, code)
        result['checks'][ident] = {'input': input_value, 'input_sha256': verification.sha(input_value),
                                  'process': process, 'observations': observed}
        require(inventory_tree(source, label='Fixed source')[0] == check['source']['digest']
                and verification.sha(json.loads(read_fixed_raw(output / 'input.json'))) == verification.sha(input_value),
                'Fixed source or input drifted during execution')
        verification.validate_checks({ident: check}, installation=ROOT, live=True)
    require(original.git(checkout, 'rev-parse', 'HEAD').stdout.strip() == candidate
            and original.git(checkout, 'status', '--porcelain=v1', '-z', '--untracked-files=all').stdout == before,
            'Fixed verification changed its candidate checkout')
    result['passed'] = all(item['observations']['passed'] for item in result['checks'].values())
    verification.capacity({**ordinary, 'verification': result}, verification.ARTIFACT_BYTES,
        'Complete check-results', compact=True)
    return result
