"""Frozen CPU text observations, independent of application state and executors.

The operator selects all source, cases and expected values before candidate
generation. Programs observe text; only this owner compares their observations.
"""

import hashlib
import base64
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat

from ergora.storage.assets import manifest_digest, inventory_tree
from ergora.storage.git import text_blob
from ergora.training.materials import decode_record, observation_bytes, relative, read_raw


SOURCE_BYTES = 128 * 1024
CANDIDATE_BYTES = 256 * 1024
OBSERVATION_BYTES = 64 * 1024
ARTIFACT_BYTES = 1_000_000
# JSON can escape every byte of an observation; reserve the complete raw text
# plus comparison values before admitting a process, then check actual encoding.
RESULT_RESERVE = 14 * OBSERVATION_BYTES
INTEGER_LIMIT = 2**53 - 1


def sha(value) -> str:
    return hashlib.sha256(observation_bytes(value, 16 * 1_048_576)).hexdigest()


def capacity(value, limit: int, label: str, *, reserve: int = 0, compact: bool = False) -> None:
    encoding = {'separators': (',', ':')} if compact else {'indent': 2}
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, **encoding).encode('utf-8')
    if len(raw) + reserve > limit:
        raise ValueError(label + ' exceeds its complete encoded capacity; nothing was truncated')


def _fields(value, names, label):
    if not isinstance(value, dict) or set(value) != set(names):
        raise ValueError(label + ' has missing or unsupported fields')


def _digest(value):
    if not isinstance(value, str) or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError('Fixed verification requires complete SHA-256 identities')


def _id(value):
    if not isinstance(value, str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value) is None:
        raise ValueError('Fixed verification requires stable check and case IDs')


def validate_readback_source(source: dict) -> dict:
    """Validate an exact original-run locator before any native read."""
    _fields(source, ('task_id', 'run_id', 'event_id', 'candidate_sha', 'receipt_sha256'), 'Verification source')
    task_id, run_id, event_id, candidate = (source[key] for key in ('task_id', 'run_id', 'event_id', 'candidate_sha'))
    if not isinstance(task_id, str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', task_id) is None:
        raise ValueError('Invalid original verification task ID')
    if not isinstance(run_id, str) or not 1 <= len(run_id) <= 128 or run_id.strip() != run_id:
        raise ValueError('Invalid original verification run ID')
    if type(event_id) is not int or not 1 <= event_id <= 10_000:
        raise ValueError('Verification scheduling event ID must be 1–10000')
    if not isinstance(candidate, str) or re.fullmatch('(?:[a-f0-9]{40}|[a-f0-9]{64})', candidate) is None:
        raise ValueError('Verification source requires a full candidate commit ID')
    _digest(source['receipt_sha256'])
    return source


def validate_fixed_check_source(source: dict) -> dict:
    """Validate a completed receipt locator or a bounded wait for the original Job."""
    fields = ('operation_id', 'request_file_sha256', 'job_sha256', 'candidate_sha')
    waiting = isinstance(source, dict) and 'wait_seconds' in source
    outputs = ('receipt_sha256', 'fixed_results_sha256')
    _fields(source, fields + (('wait_seconds',) if waiting else outputs), 'Fixed check source')
    identifier, candidate = source['operation_id'], source['candidate_sha']
    if not isinstance(identifier, str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', identifier) is None:
        raise ValueError('Invalid original fixed check operation ID')
    if not isinstance(candidate, str) or re.fullmatch('[a-f0-9]{40}', candidate) is None:
        raise ValueError('Fixed check source requires a full SHA-1 candidate commit')
    if waiting:
        seconds = source['wait_seconds']
        if type(seconds) is not int or not 1 <= seconds <= 3600:
            raise ValueError('Fixed check wait must be 1–3600 integer seconds')
    for key in ('request_file_sha256', 'job_sha256') + (() if waiting else outputs):
        _digest(source[key])
    return source


def value_bytes(value) -> bytes:
    """One exact JSON domain: bool is distinct from int, and floats are absent."""
    raw = observation_bytes(value, SOURCE_BYTES)
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
        elif type(item) is int:
            if not -INTEGER_LIMIT <= item <= INTEGER_LIMIT:
                raise ValueError('Fixed verification integers exceed the exact JSON domain')
        elif item is not None and type(item) not in (str, bool):
            raise ValueError('Fixed verification values do not support floats or non-JSON types')
    return raw


def runtime_identity(executable: Path) -> dict:
    executable = Path(executable)
    if not executable.is_absolute() or str(executable) != os.path.normpath(str(executable)):
        raise ValueError('Fixed verification runtime must be the selected absolute installation Python')
    target = executable.resolve(strict=True)
    with target.open('rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Fixed verification runtime must resolve to an ordinary executable')
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if not os.access(target, os.X_OK):
        raise ValueError('Fixed verification runtime is not executable')
    return {'executable': str(executable), 'resolved': str(target), 'sha256': digest}


def validate_checks(checks: dict, *, installation: Path | None = None, live: bool = False) -> dict:
    if not isinstance(checks, dict) or not 1 <= len(checks) <= 4:
        raise ValueError('Fixed verification requires 1–4 mandatory checks')
    total, cases_count = 0, 0
    for ident, check in checks.items():
        _id(ident)
        _fields(check, ('format', 'coverage', 'entrypoint', 'source', 'runtime', 'candidate_paths', 'cases', 'wall_seconds'), 'Fixed check')
        if check['format'] != 'fixed-text-observations-v1':
            raise ValueError('Unsupported fixed verification format')
        if not isinstance(check['coverage'], str) or not check['coverage'].strip() or len(check['coverage']) > 4096:
            raise ValueError('Fixed verification requires an explicit bounded coverage obligation')
        if type(check['wall_seconds']) is not int or not 1 <= check['wall_seconds'] <= 60:
            raise ValueError('Fixed verification wall cap must be 1–60 seconds')
        source = check['source']
        _fields(source, ('files', 'digest'), 'Fixed source')
        if not isinstance(source['files'], dict) or not 1 <= len(source['files']) <= 64:
            raise ValueError('Fixed verification source requires 1–64 ordinary files')
        inventory = {}
        for name, item in source['files'].items():
            relative(name)
            if '.git' in PurePosixPath(name).parts or any(parent.as_posix() in source['files'] for parent in PurePosixPath(name).parents):
                raise ValueError('Fixed source paths conflict or contain .git')
            _fields(item, ('text', 'sha256', 'executable_bits'), 'Fixed source file')
            if not isinstance(item['text'], str):
                raise ValueError('Fixed source must retain complete UTF-8 text')
            raw = item['text'].encode('utf-8')
            total += len(raw)
            if (hashlib.sha256(raw).hexdigest() != item['sha256'] or type(item['executable_bits']) is not int
                    or item['executable_bits'] & ~0o111):
                raise ValueError('Fixed source bytes or executable bits differ from their identity')
            inventory[name] = {key: item[key] for key in ('sha256', 'executable_bits')}
        if source['digest'] != manifest_digest(inventory):
            raise ValueError('Fixed source inventory digest mismatch')
        if relative(check['entrypoint']) not in source['files'] or not check['entrypoint'].endswith('.py'):
            raise ValueError('Fixed verification requires one frozen Python entrypoint')
        runtime = check['runtime']
        _fields(runtime, ('executable', 'resolved', 'sha256'), 'Fixed runtime')
        _digest(runtime['sha256'])
        for key in ('executable', 'resolved'):
            value = runtime[key]
            if not isinstance(value, str) or '\0' in value:
                raise ValueError('Fixed runtime paths must be canonical absolute paths')
            posix, windows = PurePosixPath(value), PureWindowsPath(value)
            if not ((posix.is_absolute() and str(posix) == value and '..' not in posix.parts)
                    or (windows.is_absolute() and str(windows) == value and '..' not in windows.parts)):
                raise ValueError('Fixed runtime paths must be canonical absolute paths')
        if installation is not None and runtime['executable'] != str(installation / '.venv/bin/python'):
            raise ValueError('Fixed runtime differs from the selected installation Python')
        if live and runtime_identity(Path(runtime['executable'])) != runtime:
            raise ValueError('Fixed verification runtime identity changed')
        paths = check['candidate_paths']
        if (not isinstance(paths, list) or not 1 <= len(paths) <= 64
                or not all(isinstance(name, str) for name in paths) or len(set(paths)) != len(paths)):
            raise ValueError('Fixed verification requires unique exact candidate paths')
        for name in paths:
            relative(name)
        cases = check['cases']
        if not isinstance(cases, list) or not cases:
            raise ValueError('Fixed verification requires named cases')
        ids = set()
        for case in cases:
            _fields(case, ('id', 'input', 'expected'), 'Fixed case')
            _id(case['id'])
            if case['id'] in ids:
                raise ValueError('Duplicate fixed verification case')
            ids.add(case['id'])
            total += len(value_bytes(case['input'])) + len(value_bytes(case['expected']))
        cases_count += len(cases)
    if total > SOURCE_BYTES or cases_count > 32:
        raise ValueError('Fixed verification exceeds aggregate source/case bytes or 32 cases')
    capacity(checks, ARTIFACT_BYTES, 'Fixed verification declaration', reserve=RESULT_RESERVE)
    return checks


def snapshot(project: dict, *, revision: int | None = None) -> dict | None:
    registration = project.get('registration')
    if registration is None or 'trusted_checks' not in registration['definition']:
        return None
    checks = validate_checks(registration['definition']['trusted_checks'])
    value = {'format': 'fixed-text-verification-v1', 'project': project['id'],
             'project_revision': project['revision'] if revision is None else revision,
             'registration_sha256': registration['sha256'], 'checks': checks}
    return {**value, 'sha256': sha(value)}


def validate_snapshot(value: dict, *, owner: dict | None = None) -> dict:
    _fields(value, ('format', 'project', 'project_revision', 'registration_sha256', 'checks', 'sha256'), 'Fixed verification snapshot')
    _id(value['project'])
    _digest(value['registration_sha256'])
    if (value['format'] != 'fixed-text-verification-v1' or type(value['project_revision']) is not int
            or value['project_revision'] < 1 or value['sha256'] != sha({key: item for key, item in value.items() if key != 'sha256'})):
        raise ValueError('Fixed verification snapshot identity mismatch')
    validate_checks(value['checks'])
    if owner is not None and any(value[key] != owner[key] for key in
                                 ('project', 'project_revision', 'registration_sha256')):
        raise ValueError('Fixed verification owner differs from its original budget scope')
    return value


def require_route(project: dict, version: int) -> dict | None:
    value = snapshot(project)
    if value is not None and version != 8:
        raise ValueError('Fixed verification requires current Definition8/Input12 formal task creation')
    return value


def require_admission(project: dict, document: dict, *, revision: int | None = None) -> None:
    expected = snapshot(project, revision=revision)
    if (sha(document.get('verification')) != sha(expected)
            or ('verification' in document) != (expected is not None)
            or (expected is not None and document.get('schema_version') != 12)):
        raise ValueError('Task verification differs from its original registered fixed checks')


def subject(document: dict, job_id: str, job_sha256: str, candidate: str, creation_sha256: str) -> dict:
    verification = validate_snapshot(document['verification'])
    return {'task_id': document['legacy_spec']['request']['task_id'], 'job_id': job_id,
            'job_sha256': job_sha256, 'admission_sha256': document['sha256'],
            'creation_sha256': creation_sha256, 'verification_sha256': verification['sha256'],
            'registration_sha256': verification['registration_sha256'], 'candidate_sha': candidate}


def script_input(check_id: str, check: dict, expected_subject: dict, repository: dict) -> dict:
    value = {'format': 'fixed-text-input-v1', 'subject': {**expected_subject, 'check_id': check_id, 'check_sha256': sha(check)},
             'repository': repository, 'cases': [{'id': case['id'], 'input': case['input']} for case in check['cases']]}
    validate_input(value, check_id, check, expected_subject)
    return value


def validate_input(value: dict, ident: str, check: dict, expected_subject: dict) -> None:
    _fields(value, ('format', 'subject', 'repository', 'cases'), 'Fixed script input')
    if (value['format'] != 'fixed-text-input-v1'
            or value['subject'] != {**expected_subject, 'check_id': ident, 'check_sha256': sha(check)}
            or sha(value['cases']) != sha([{'id': case['id'], 'input': case['input']} for case in check['cases']])):
        raise ValueError('Fixed script input belongs to another check, subject or case set')
    for case in value['cases']:
        value_bytes(case['input'])
    repository = value['repository']
    _fields(repository, ('candidate', 'blobs', 'scope'), 'Fixed candidate material')
    candidate = repository['candidate']
    _fields(candidate, ('commit', 'files'), 'Fixed candidate')
    if (candidate['commit'] != expected_subject['candidate_sha'] or set(candidate['files']) != set(check['candidate_paths'])
            or repository['scope'] != check['candidate_paths']):
        raise ValueError('Fixed candidate material must contain every declared exact file and no expansion')
    objects, total = set(), 0
    for name, item in candidate['files'].items():
        _fields(item, ('git_object', 'mode'), 'Fixed Git file')
        if item['mode'] not in ('100644', '100755') or re.fullmatch('[a-f0-9]{40}', item['git_object']) is None:
            raise ValueError('Fixed candidate material requires ordinary full Git blob identities')
        objects.add(item['git_object'])
    if set(repository['blobs']) != objects:
        raise ValueError('Fixed candidate blob set differs from its exact file inventory')
    for oid, item in repository['blobs'].items():
        _fields(item, ('sha256', 'text'), 'Fixed Git blob')
        raw = item['text'].encode('utf-8')
        total += len(raw)
        if (text_blob(raw) != item or hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest() != oid):
            raise ValueError('Fixed candidate text identity mismatch')
    if total > CANDIDATE_BYTES:
        raise ValueError('Fixed candidate material exceeds its complete text capacity')


def observations(check: dict, raw: bytes | None, returncode: int) -> dict:
    """Keep complete raw evidence even for known malformed or failed output."""
    if raw is not None and len(raw) > OBSERVATION_BYTES:
        raise ValueError('Fixed observations exceed their complete raw capacity')
    result = {'raw_base64': base64.b64encode(raw).decode('ascii') if raw is not None else None,
              'raw_sha256': hashlib.sha256(raw).hexdigest() if raw is not None else None,
              'comparisons': [], 'failure': None, 'passed': False}
    if returncode != 0:
        result['failure'] = 'Fixed process exited with code ' + str(returncode)
        return result
    try:
        if raw is None:
            raise ValueError('Confirmed terminal has no observations')
        value = decode_record(raw)
        _fields(value, ('observations',), 'Fixed observations')
        items = value['observations']
        if not isinstance(items, list):
            raise ValueError('Fixed observations must be a complete array')
        found = {}
        for item in items:
            _fields(item, ('case_id', 'value'), 'Fixed observation')
            _id(item['case_id'])
            value_bytes(item['value'])
            if item['case_id'] in found:
                raise ValueError('Duplicate fixed observation case')
            found[item['case_id']] = item['value']
        if set(found) != {case['id'] for case in check['cases']}:
            raise ValueError('Fixed observations omit or add required cases')
        result['comparisons'] = [{'case_id': case['id'], 'expected': case['expected'], 'observed': found[case['id']],
                                  'matches': value_bytes(case['expected']) == value_bytes(found[case['id']])}
                                 for case in check['cases']]
        result['passed'] = all(item['matches'] for item in result['comparisons'])
        if not result['passed']:
            result['failure'] = 'Fixed observations differ from the frozen expected values'
    except (ValueError, TypeError, KeyError, UnicodeError) as error:
        result['comparisons'] = []
        result['passed'] = False
        result['failure'] = str(error)
    return result


def process_binding(input_value: dict) -> dict:
    return {'kind': 'fixed-text-verification-process-v1', 'subject': input_value['subject'], 'input_sha256': sha(input_value)}


def process_name(binding: dict) -> str:
    job_sha256 = binding['subject']['job_sha256']
    _digest(job_sha256)
    return 'af-oracle-' + job_sha256 + '-' + sha(binding)


def _ordinary_report(report: dict, verification: dict, expected_subject: dict, state: Path, require_pass: bool) -> None:
    """Join original scope/baseline evidence without re-executing its checks."""
    _fields(report, ('candidate_sha', 'scope', 'commands', 'baseline_commands', 'baseline_regression', 'verification'),
            'Complete check-results')
    task_id, job_id = expected_subject['task_id'], expected_subject['job_id']
    record = decode_record(read_raw(state / 'ergora/task-creations' / (task_id + '.intent.json'), 16 * 1_048_576))
    document = record['files']['task.spec.json']
    if (sha(record) != expected_subject['creation_sha256'] or document['sha256'] != expected_subject['admission_sha256']
            or sha(document['verification']) != sha(verification)):
        raise ValueError('Check-results differ from the original creation/admission')
    spec = record['files']['compiled.json']['spec']
    base = state / 'workspaces' / task_id / 'jobs' / job_id
    scope = report['scope']
    _fields(scope, ('schema_version', 'check', 'status', 'task_id', 'request_sha256', 'profile_sha256',
        'spec_sha256', 'policy_sha256', 'base_sha', 'candidate_sha', 'allowed_paths', 'protected_paths',
        'changed_files', 'changed_text_lines', 'binary_paths', 'files', 'violations', 'coverage'), 'Original scope result')
    if (sha(scope) != sha(decode_record(read_raw(base / 'output/scope.json')))
            or type(scope['schema_version']) is not int or scope['schema_version'] != 1 or scope['check'] != 'scope'
            or scope['task_id'] != task_id or scope['candidate_sha'] != expected_subject['candidate_sha']
            or scope['request_sha256'] != spec['request_sha256'] or scope['profile_sha256'] != spec['profile_sha256']
            or scope['spec_sha256'] != sha(spec) or scope['base_sha'] != spec['request']['repository']['base_sha']
            or scope['allowed_paths'] != spec['request']['input']['allowed_paths']
            or not isinstance(scope['violations'], list) or scope['status'] != ('FAIL' if scope['violations'] else 'PASS')):
        raise ValueError('Scope result differs from its original candidate/spec or outcome')
    baseline = decode_record(read_raw(state / 'tasks' / task_id / 'baseline-checks.json'))
    if sha(report['baseline_commands']) != sha(baseline):
        raise ValueError('Check-results differ from the original baseline commands')
    selected = {}
    for ident in spec['profile']['required_checks']:
        if ident in ('scope', 'baseline-regression'):
            continue
        template = record['files']['project.json']['checks'][ident]
        # This is the original commands() template key, not executable-source
        # provenance. Inventory and verify legitimately map different repos.
        key = hashlib.sha256(json.dumps(template).encode()).hexdigest()[:16]
        selected.setdefault(key, {'template': template, 'checks': []})['checks'].append(ident)
    inventory_id = task_id + '-' + sha({'stage': 'inventory'})[:24]
    for label, checkout in (('commands', base / 'checkout'),
                            ('baseline_commands', state / 'workspaces' / task_id / 'jobs' / inventory_id / 'checkout')):
        commands = report[label]
        if not isinstance(commands, dict) or set(commands) != set(selected):
            raise ValueError('Ordinary check commands differ from the frozen required profile')
        for key, command in commands.items():
            _fields(command, ('command', 'exit_code', 'log', 'checks'), 'Ordinary command result')
            expected = [arg.replace('{repo}', str(checkout)) for arg in selected[key]['template']]
            if (command['command'] != expected or command['checks'] != selected[key]['checks']
                    or type(command['exit_code']) is not int or not isinstance(command['log'], str)):
                raise ValueError('Ordinary command result differs from its frozen template or checks')
    ordinary_passed = all(item['exit_code'] == 0 for item in report['commands'].values())
    if type(report['baseline_regression']) is not bool or report['baseline_regression'] != ordinary_passed:
        raise ValueError('Baseline regression flag contradicts the candidate command outcomes')
    if require_pass and (scope['status'] != 'PASS' or not ordinary_passed):
        raise ValueError('Required original scope or ordinary checks did not pass')


def validate_report(report: dict, verification: dict, expected_subject: dict, *, process_root: Path, require_pass: bool = True) -> dict:
    """Consume actual trusted artifacts and original process records at every join."""
    validate_snapshot(verification)
    capacity(report, ARTIFACT_BYTES, 'Complete check-results', compact=True)
    _ordinary_report(report, verification, expected_subject, process_root.parent, require_pass)
    if report['candidate_sha'] != expected_subject['candidate_sha']:
        raise ValueError('Fixed results differ from the required checks or original subject')
    state = process_root.parent
    base = state / 'workspaces' / expected_subject['task_id'] / 'jobs' / expected_subject['job_id']
    fence = state / 'fences' / (expected_subject['task_id'] + '.json')
    _validate_fixed_results(report['verification'], verification, expected_subject, process_root, base, fence, require_pass)
    return report


def validate_fixed_report(report: dict, verification: dict, expected_subject: dict, *,
                          process_root: Path, workspace: Path, fence: Path, require_pass: bool = True) -> dict:
    """Validate a report whose receipt covers only the authorized fixed checks."""
    _fields(report, ('schema_version', 'kind', 'candidate_sha', 'verification'), 'Independent fixed check results')
    if (type(report['schema_version']) is not int or report['schema_version'] != 1
            or report['kind'] != 'fixed-candidate-check-results'
            or report['candidate_sha'] != expected_subject['candidate_sha']):
        raise ValueError('Independent fixed results differ from the exact candidate')
    validate_snapshot(verification)
    # The original immutable JSON publisher includes a trailing newline.
    capacity(report, ARTIFACT_BYTES, 'Independent fixed check results', reserve=1, compact=True)
    _validate_fixed_results(report['verification'], verification, expected_subject, process_root, workspace, fence, require_pass)
    return report


def _validate_fixed_results(fixed, verification, expected_subject, process_root, base, fence, require_pass):
    _fields(fixed, ('subject', 'required_checks', 'checks', 'passed'), 'Fixed verification results')
    if (fixed['subject'] != expected_subject
            or fixed['required_checks'] != sorted(verification['checks']) or set(fixed['checks']) != set(verification['checks'])):
        raise ValueError('Fixed results differ from the required checks or original subject')
    total = 0
    for ident, check in verification['checks'].items():
        item = fixed['checks'][ident]
        _fields(item, ('input', 'input_sha256', 'process', 'observations'), 'Fixed check result')
        validate_input(item['input'], ident, check, expected_subject)
        if sha(item['input']) != item['input_sha256']:
            raise ValueError('Fixed result input identity mismatch')
        binding = process_binding(item['input'])
        process = item['process']
        _fields(process, ('name', 'request', 'started', 'terminal'), 'Fixed process evidence')
        name = process_name(binding)
        if process['name'] != name:
            raise ValueError('Fixed process name differs from its full subject digest')
        for record_name in ('request', 'started', 'terminal'):
            original = decode_record(read_raw(process_root / name / (record_name + '.json')))
            if sha(original) != sha(process[record_name]):
                raise ValueError('Fixed process evidence differs from its original ' + record_name)
        request, started, terminal = (process[key] for key in ('request', 'started', 'terminal'))
        if (request['binding'] != binding or started['binding'] != binding or terminal['binding'] != binding
                or request['name'] != name or started['name'] != name or terminal['name'] != name
                or started['request_sha256'] != sha(request) or terminal['request_sha256'] != sha(request)
                or request['writable'] is not False or request['model'] is not None
                or type(terminal['returncode']) is not int
                or type(request['timeout']) not in (int, float) or not 1 <= request['timeout'] <= check['wall_seconds']):
            raise ValueError('Fixed process lost its original request/input binding')
        output = Path(request['output'])
        if (output != base / 'output' / name or Path(request['checkout']) != base / 'checkout'
                or request['fence'] != str(fence)):
            raise ValueError('Fixed process moved outside its original verify Job')
        owner = decode_record(read_raw(base / 'budget/owner.json'))
        if (request['deadline'] != owner['verification_deadline']
                or any(owner[key] != expected_subject[key] for key in ('job_id', 'job_sha256', 'admission_sha256'))):
            raise ValueError('Fixed process cutoff differs from its original Job owner')
        command = [check['runtime']['executable'], '-I', '-S', str(output / 'source' / check['entrypoint']),
                   str(output / 'input.json'), str(output / 'observations.json')]
        if request['command'] != command or started['command'] != command:
            raise ValueError('Fixed process command differs from the frozen isolated entrypoint')
        if (sha(decode_record(read_raw(output / 'input.json'))) != item['input_sha256']
                or inventory_tree(output / 'source', label='Fixed source')[0] != check['source']['digest']):
            raise ValueError('Fixed process source or input differs from its frozen contract')
        raw = item['observations']['raw_base64']
        raw = base64.b64decode(raw, validate=True) if raw is not None else None
        try:
            original_raw = read_raw(output / 'observations.json', OBSERVATION_BYTES)
        except FileNotFoundError:
            original_raw = None
        if original_raw != raw:
            raise ValueError('Fixed result differs from its complete original output bytes')
        total += len(raw) if raw is not None else 0
        if sha(item['observations']) != sha(observations(check, raw, terminal['returncode'])):
            raise ValueError('Fixed result comparison differs from the complete original observations')
    if total > OBSERVATION_BYTES:
        raise ValueError('Fixed observations exceed aggregate raw capacity')
    passed = all(item['observations']['passed'] for item in fixed['checks'].values())
    if type(fixed['passed']) is not bool or fixed['passed'] != passed or (require_pass and not passed):
        raise ValueError('Required fixed verification did not pass')


def job_subject(document: dict, job: dict, state: Path) -> dict:
    """Join the original creation bytes; no live registration or State lookup."""
    task_id = document['legacy_spec']['request']['task_id']
    if not isinstance(task_id, str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', task_id) is None:
        raise ValueError('Invalid original fixed verification task ID')
    record = decode_record(read_raw(state / 'ergora/task-creations' / (task_id + '.intent.json'), 16 * 1_048_576))
    fixed = validate_snapshot(document['verification'])
    if (record['schema_version'] != 8 or record['project'] != fixed['project']
            or record['project_revision'] != fixed['project_revision']
            or record['registration_sha256'] != fixed['registration_sha256']
            or sha(record['files']['task.spec.json']) != sha(document)
            or sha(record['files']['project.json']['trusted_checks']) != sha(fixed['checks'])):
        raise ValueError('Fixed verification differs from the complete original creation')
    return subject(document, job['job_id'], job['job_sha256'], job['context']['expected_candidate_sha'], sha(record))


def read_report(raw: bytes, verification: dict, expected_subject: dict, *, process_root: Path, require_pass: bool = True) -> dict:
    if len(raw) > ARTIFACT_BYTES:
        raise ValueError('Complete check-results exceed their encoded capacity')
    return validate_report(decode_record(raw), verification, expected_subject, process_root=process_root, require_pass=require_pass)
