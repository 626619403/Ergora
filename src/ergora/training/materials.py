"""Frozen raw configuration inputs, shared without application state or native SDKs."""

import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

from ergora.storage.assets import is_link


LIMIT = 1_048_576


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(label + ' has unsupported or missing fields')


def decode_record(raw: bytes) -> dict:
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('Duplicate execution record key: ' + key)
            value[key] = item
        return value

    def number(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError('Execution records require finite JSON numbers')
        return value

    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=number, parse_float=number)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Execution record is not complete UTF-8 JSON') from error
    if not isinstance(value, dict):
        raise ValueError('Execution record must be a JSON object')
    return value


def observation_sha256(value):
    return hashlib.sha256(observation_bytes(value)).hexdigest()


def observation_bytes(value, limit=LIMIT):
    # Bound the complete observation, including arbitrary nested adapter values.
    pending, count = [(value, 0)], 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if depth > 64 or count > 100_000:
            raise ValueError('Configuration observation exceeds its complete bounds')
        if isinstance(item, dict):
            if not all(isinstance(key, str) for key in item):
                raise ValueError('Configuration observation keys must be strings')
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
        elif item is not None and type(item) not in (str, bool, int, float):
            raise ValueError('Configuration observations must be finite JSON values')
    try:
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError('Configuration observations must be finite bounded JSON') from error
    if len(raw) > limit:
        raise ValueError('Configuration observation exceeds its complete read capacity')
    return raw


def relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or '\x00' in value
            or PurePosixPath(value).is_absolute() or str(PurePosixPath(value)) != value
            or any(part in ('.', '..') for part in value.split('/'))):
        raise ValueError('Configuration input paths must be ordinary relative paths')
    return value


def _sha(value):
    if not isinstance(value, str) or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError('Configuration inputs require complete raw SHA256 identities')


def json_configuration(raw):
    """Validate data only; preserve its original UTF-8 bytes, including a signature."""
    if not 0 < len(raw) <= LIMIT:
        raise ValueError('Complete configuration input exceeds its 1 MiB capacity')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Configuration JSON has duplicate object keys')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('Configuration JSON requires finite values')

    try:
        value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs, parse_constant=constant)
        if not isinstance(value, dict):
            raise ValueError('Complete configuration input must be a JSON object')
        pending, count = [(value, 0)], 0
        while pending:
            item, depth = pending.pop()
            count += 1
            if depth > 64 or count > 100_000:
                raise ValueError('Complete configuration input exceeds its JSON bounds')
            if isinstance(item, dict):
                pending.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in item)
            elif isinstance(item, float) and not math.isfinite(item):
                raise ValueError('Configuration JSON requires finite values')
        json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Configuration input requires bounded valid UTF-8 JSON') from error
    return value


def material_plan(ident, materials):
    """Return native fixed-path descriptors and exact bytes, without effects."""
    if not isinstance(ident, str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', ident) is None:
        raise ValueError('Configuration materials require the original experiment ID')
    _exact(materials, ('format', 'baseline', 'candidate'), 'Configuration materials')
    if materials['format'] != 'json-v1':
        raise ValueError('Configuration execution unavailable for this material format')
    descriptor, files = {'kind': 'prepared-json', 'format': 'json-v1'}, {}
    for arm in ('baseline', 'candidate'):
        item = materials[arm]
        _exact(item, ('utf8', 'sha256'), 'Configuration material')
        _sha(item['sha256'])
        if not isinstance(item['utf8'], str):
            raise ValueError('Configuration material requires complete UTF-8 data')
        raw = item['utf8'].encode('utf-8')
        json_configuration(raw)
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Configuration material raw bytes differ from their SHA256')
        path = 'training/configurations/' + ident + '/' + arm + '.json'
        files[path] = raw
        descriptor[arm] = {'path': path, 'sha256': item['sha256'], 'bytes': len(raw)}
    return descriptor, files


def input_descriptor(manifest):
    """The manifest alone selects the input source; absent means ordinary full."""
    value = manifest.get('configuration_inputs')
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError('Configuration inputs require an exact descriptor')
    if value.get('kind') == 'git-source':
        _exact(value, ('kind', 'path'), 'Git configuration inputs')
        relative(value['path'])
        return value
    _exact(value, ('kind', 'format', 'baseline', 'candidate'), 'Prepared configuration inputs')
    if value['kind'] != 'prepared-json' or value['format'] != 'json-v1':
        raise ValueError('Configuration execution unavailable for this input source or format')
    ident = manifest['experiment_id']
    if not isinstance(ident, str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', ident) is None:
        raise ValueError('Configuration input descriptor requires the original experiment ID')
    for arm, key in (('baseline', 'base_config_sha256'), ('candidate', 'candidate_config_sha256')):
        item = value[arm]
        _exact(item, ('path', 'sha256', 'bytes'), 'Prepared configuration input')
        if item['path'] != 'training/configurations/' + ident + '/' + arm + '.json':
            raise ValueError('Prepared configuration input differs from its original native path')
        _sha(item['sha256'])
        if (item['sha256'] != manifest[key] or type(item['bytes']) is not int
                or not 0 < item['bytes'] <= LIMIT):
            raise ValueError('Prepared configuration input differs from its manifest raw identity')
    return value


def require_driver(manifest, runner):
    """Check declared support without importing or constructing the driver."""
    value = input_descriptor(manifest)
    capability = runner['configuration_readback']
    selector = baseline_selector(manifest)
    if selector is not None and (capability is None or capability['baseline_reference_protocol'] != 'baseline-reference-v1'):
        raise ValueError('Baseline reference unavailable: trusted driver does not declare baseline-reference-v1')
    if (value is None) != (capability is None):
        raise ValueError('Configuration execution unavailable: runner and input descriptor disagree')
    if value is not None and value['kind'] == 'prepared-json' and capability.get('prepared_json_format') != value['format']:
        raise ValueError('Configuration execution unavailable: trusted driver does not declare json-v1 support')
    execution_plan(manifest, runner)
    return value



def validate_profile_policy(policy, capability=None):
    """Validate the explicit finite diagnostic selection; never infer a capture."""
    _exact(policy, ('protocol', 'tool', 'reader', 'source_operation', 'phases', 'ranks', 'window',
                    'captures', 'maximum_seconds', 'max_raw_bytes', 'max_derived_bytes', 'required'), 'Profile policy')
    if (policy['protocol'] != 'training-profile-v1' or not isinstance(policy['tool'], str) or not policy['tool']
            or not isinstance(policy['reader'], str) or not policy['reader']
            or not isinstance(policy['source_operation'], str) or not policy['source_operation']):
        raise ValueError('Profile policy requires explicit protocol, tool, reader and source operation')
    if (not isinstance(policy['phases'], list) or not policy['phases']
            or any(phase not in ('baseline', 'screen') for phase in policy['phases'])
            or len(set(policy['phases'])) != len(policy['phases'])
            or not isinstance(policy['ranks'], list) or not policy['ranks']
            or any(type(rank) is not int or rank < 0 for rank in policy['ranks'])
            or len(set(policy['ranks'])) != len(policy['ranks']) or len(policy['ranks']) > 1024):
        raise ValueError('Profile policy requires unique phases and actual nonnegative ranks')
    window = policy['window']
    _exact(window, ('unit', 'work', 'warmup_work'), 'Profile window')
    if (window['unit'] not in ('source_samples', 'source_tokens')
            or type(window['work']) is not int or not 0 < window['work'] <= 10_000_000
            or type(window['warmup_work']) is not int or not 0 <= window['warmup_work'] <= 10_000_000
            or type(policy['captures']) is not int or not 1 <= policy['captures'] <= 32
            or type(policy['maximum_seconds']) not in (int, float)
            or not math.isfinite(policy['maximum_seconds']) or not 0 < policy['maximum_seconds'] <= 86400
            or type(policy['max_raw_bytes']) is not int or not 0 < policy['max_raw_bytes'] <= 16 * LIMIT
            or type(policy['max_derived_bytes']) is not int or not 0 < policy['max_derived_bytes'] <= LIMIT
            or type(policy['required']) is not bool):
        raise ValueError('Profile policy requires finite actual window, count, time and complete byte capacities')
    if capability is not None:
        _exact(capability, ('protocol', 'operations'), 'Profile capability')
        if (capability['protocol'] != 'training-profile-v1' or not isinstance(capability['operations'], list)
                or not capability['operations']
                or any(not isinstance(operation, str) or not operation for operation in capability['operations'])
                or len(set(capability['operations'])) != len(capability['operations'])):
            raise ValueError('Profile capability requires explicit supported source operations')
    return policy


def profile_policy(manifest, runner):
    """Read only the selected manifest policy; absent historical/manual fields stay absent."""
    policy = manifest['execution'].get('profile')
    if policy is not None:
        if not isinstance(runner.get('configuration_readback'), dict):
            raise ValueError('Profile diagnostic unavailable: no trusted source configuration wrapper')
        validate_profile_policy(policy, runner['configuration_readback'].get('profile'))
        phase = 'screen' if manifest['execution']['operation'] == 'training-screen-v1' else 'baseline'
        if phase not in policy['phases']:
            raise ValueError('Profile policy does not select the actual execution phase')
    return policy


def execution_plan(manifest, runner):
    """Validate the one current operation without importing source or reading history."""
    execution = manifest.get('execution')
    if not isinstance(execution, dict):
        raise ValueError('Current execution requires an explicit operation')
    if execution.get('operation') == 'full-verify':
        _exact(execution, ('operation', *(['profile'] if 'profile' in execution else []), *(['cpu_contract'] if 'cpu_contract' in execution else [])), 'Full execution')
        if 'cpu_contract' in execution:
            validate_cpu_execution_contract(execution['cpu_contract'], runner=runner)
        profile_policy(manifest, runner)
        return execution
    _exact(execution, ('operation', 'plan', *(['profile'] if 'profile' in execution else []), *(['cpu_contract'] if 'cpu_contract' in execution else [])), 'Screen execution')
    if 'cpu_contract' in execution:
        validate_cpu_execution_contract(execution['cpu_contract'], runner=runner)
    profile_policy(manifest, runner)
    if execution['operation'] != 'training-screen-v1':
        raise ValueError('Execution operation unavailable')
    plan = execution['plan']
    _exact(plan, ('scheme', 'requested_tier', 'verification_experiment_id', 'input_plan', 'window',
                  'checks', 'resources', 'screening'), 'Screen plan')
    capability = runner['configuration_readback']
    screen = capability.get('screen') if isinstance(capability, dict) else None
    if (not isinstance(screen, dict) or screen != {'protocol': 'training-screen-v1', 'scheme': plan['scheme']}
            or capability.get('baseline_reference_protocol') != 'baseline-reference-v1'
            or baseline_selector(manifest) is None or input_descriptor(manifest) is None):
        raise ValueError('Screen execution unavailable: declared source, scheme or baseline reference is missing')
    if (not isinstance(plan['scheme'], str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', plan['scheme']) is None
            or plan['requested_tier'] != 'screened'
            or not isinstance(plan['verification_experiment_id'], str)
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', plan['verification_experiment_id']) is None
            or plan['verification_experiment_id'] == manifest['experiment_id']):
        raise ValueError('Screen plan requires its fixed scheme, tier and distinct verification experiment')
    _exact(plan['input_plan'], ('scheme', 'sha256'), 'Screen input plan')
    _sha(plan['input_plan']['sha256'])
    if not isinstance(plan['input_plan']['scheme'], str) or not plan['input_plan']['scheme']:
        raise ValueError('Screen input plan requires an explicit source scheme')
    window = plan['window']
    _exact(window, ('unit', 'minimum_work', 'maximum_work', 'warmup_maximum_work', 'maximum_windows', 'maximum_seconds'), 'Screen window')
    if (window['unit'] not in ('source_samples', 'source_tokens')
            or any(type(window[key]) is not int for key in ('minimum_work', 'maximum_work', 'warmup_maximum_work', 'maximum_windows'))
            or not 0 < window['minimum_work'] <= window['maximum_work'] or window['warmup_maximum_work'] < 0
            or window['maximum_windows'] <= 0 or type(window['maximum_seconds']) not in (int, float)
            or not math.isfinite(window['maximum_seconds']) or not 1 <= window['maximum_seconds'] <= 86400):
        raise ValueError('Screen window requires supported work bounds and walltime 1..86400 seconds')
    if not isinstance(plan['checks'], list) or not 1 <= len(plan['checks']) <= 64:
        raise ValueError('Screen requires a complete bounded check plan')
    checks = set()
    for check in plan['checks']:
        _exact(check, ('id', 'kind', 'contract_sha256', 'source_entrypoint'), 'Screen check')
        if not isinstance(check['id'], str) or not check['id'] or check['id'] in checks or check['kind'] not in ('finite', 'behavior'):
            raise ValueError('Screen checks require unique IDs and supported kinds')
        checks.add(check['id'])
        _sha(check['contract_sha256'])
        relative(check['source_entrypoint'])
    if {check['kind'] for check in plan['checks']} != {'finite', 'behavior'}:
        raise ValueError('Screen requires finite and independent behavior checks')
    if not isinstance(plan['resources'], list) or len(plan['resources']) > 32:
        raise ValueError('Screen resource plan exceeds its complete bound')
    metrics = set()
    for metric in plan['resources']:
        _exact(metric, ('metric', 'unit', 'scope', 'aggregation', 'required', 'limit'), 'Screen resource')
        if (any(not isinstance(metric[key], str) or not metric[key].strip() for key in ('metric', 'unit', 'aggregation'))
                or not (isinstance(metric['scope'], str) and metric['scope'].strip() or isinstance(metric['scope'], dict) and metric['scope'])
                or metric['metric'] in metrics or type(metric['required']) is not bool
                or metric['limit'] is not None and (type(metric['limit']) not in (int, float)
                    or not math.isfinite(metric['limit']) or metric['limit'] < 0)):
            raise ValueError('Screen resources require unique typed observations and finite limits')
        metrics.add(metric['metric'])
    screening = plan['screening']
    _exact(screening, ('target', 'minimum_improvement_fraction', 'noise_fraction', 'comparison_scheme'), 'Screening policy')
    if (screening['target'] not in {'throughput', *metrics}
            or not isinstance(screening['comparison_scheme'], str) or not screening['comparison_scheme']
            or any(type(screening[key]) not in (int, float) or not math.isfinite(screening[key]) or screening[key] < 0
                   for key in ('minimum_improvement_fraction', 'noise_fraction'))):
        raise ValueError('Screening requires a declared target and finite exploration thresholds')
    return execution


def baseline_selector(manifest):
    """Validate the immutable same-project archive selection, without observing it."""
    value = manifest.get('baseline_reference')
    if value is None:
        return None
    _exact(value, ('experiment_id', 'evidence_sha256', 'reference_sha256'), 'Baseline reference selector')
    if not isinstance(value['experiment_id'], str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value['experiment_id']) is None:
        raise ValueError('Baseline reference requires an exact original experiment ID')
    for key in ('evidence_sha256', 'reference_sha256'):
        _sha(value[key])
    return value


def _path(path, root):
    path, root = Path(path), Path(root)
    relative(path.relative_to(root).as_posix())
    for selected in (path, *path.parents):
        try:
            linked = is_link(selected)
        except FileNotFoundError:
            continue
        if linked:
            raise ValueError('Configuration input publications cannot use symlinks or reparse points')
    return path


def read_raw(path, limit=LIMIT):
    """Read an ordinary bounded file without waiting on a FIFO or following links."""
    path = Path(path)
    _path(path, path.parent)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Configuration inputs require ordinary files')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Complete configuration publication exceeds its read capacity')
    return raw


def read_materials(root, manifest):
    """Read and verify the exact native data that enters original source inventories."""
    value, result = input_descriptor(manifest), {}
    if value is not None and value['kind'] == 'prepared-json':
        for arm in ('baseline', 'candidate'):
            item = value[arm]
            raw = read_raw(_path(Path(root) / item['path'], root))
            if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
                raise ValueError('Configuration material bytes differ from the original manifest: ' + arm)
            json_configuration(raw)
            result[arm] = raw
    return result


def confirm_file(path, raw, root):
    """Confirm the same inode/raw bytes durably, including all new pathname links."""
    path, root = _path(path, root), Path(root)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or stream.read(len(raw) + 1) != raw:
            raise ValueError('Original configuration publication bytes changed before synchronization')
        os.fsync(stream.fileno())
        for directory in (path.parent, *path.parent.parents):
            fd = os.open(directory, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0))
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            if directory == root:
                break
        else:
            raise ValueError('Configuration publication escaped its original root')
        reader = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(reader, 'rb') as readback:
            current = os.fstat(readback.fileno())
            if (current.st_dev, current.st_ino) != (before.st_dev, before.st_ino) or readback.read(len(raw) + 1) != raw:
                raise ValueError('Original configuration publication changed during durable readback')
            final = path.stat(follow_symlinks=False)
            if (final.st_dev, final.st_ino) != (current.st_dev, current.st_ino):
                raise ValueError('Original configuration publication changed during durable readback')


def publish_material(path, raw, root):
    """Publish exact raw data once; equal visible retries still confirm durability."""
    path = _path(path, root)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix='.configuration-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if read_raw(path, len(raw)) != raw:
                raise ValueError('Immutable configuration input conflicts with its original raw bytes')
        confirm_file(path, raw, root)
    finally:
        Path(temporary).unlink(missing_ok=True)

CPU_CONFORMANCE = {'prepare': 'construct-and-describe-only', 'compute_subject': 'same-wrapper-calling-thread',
                   'compute_workers': 'none', 'placement': 'inherit-current-container-no-mutation',
                   'placement_inputs': 'frozen-domain-only-not-pid-job-id'}
_PREPARATION_FIELDS = ('schema_version', 'operation', 'control_home', 'project', 'repo', 'execution',
                       'registration_sha256', 'experiment_id', 'project_revision', 'request', 'sources', 'files')


def _cpu_domain(schema, value=None, *, check=False):
    """The supported CPU parameter domain is a complete primitive-object schema."""
    _exact(schema, ('type', 'properties', 'required', 'additionalProperties'), 'CPU input domain')
    if (schema['type'] != 'object' or schema['additionalProperties'] is not False
            or not isinstance(schema['properties'], dict) or not isinstance(schema['required'], list)
            or any(not isinstance(key, str) or not key for key in schema['properties'])
            or any(not isinstance(key, str) for key in schema['required'])
            or len(set(schema['required'])) != len(schema['required']) or not set(schema['required']) <= set(schema['properties'])):
        raise ValueError('Unsupported CPU input domain')
    if check and (not isinstance(value, dict) or not set(schema['required']) <= set(value)
                  or not set(value) <= set(schema['properties'])):
        raise ValueError('CPU configuration is outside its admitted complete input domain')
    types = {'integer': lambda item: type(item) is int, 'number': lambda item: type(item) in (int, float),
             'string': lambda item: isinstance(item, str), 'boolean': lambda item: type(item) is bool,
             'null': lambda item: item is None}
    def equal(left, right):
        # JSON booleans are distinct from numbers, including true versus 1.
        return left == right and (type(left) is bool) == (type(right) is bool)
    for key, rule in schema['properties'].items():
        if (not isinstance(rule, dict) or 'type' not in rule or not set(rule) <= {'type', 'enum', 'const', 'minimum', 'maximum'}
                or rule['type'] not in types):
            raise ValueError('Unsupported CPU parameter constraint')
        if 'enum' in rule and (not isinstance(rule['enum'], list) or not rule['enum']):
            raise ValueError('CPU enum requires its complete nonempty values')
        for bound in ('minimum', 'maximum'):
            if bound in rule and (type(rule[bound]) not in (int, float) or not math.isfinite(rule[bound])):
                raise ValueError('CPU domain bounds require finite numbers')
        if not check or key not in value:
            continue
        item = value[key]
        if (not types[rule['type']](item) or 'enum' in rule and not any(equal(item, allowed) for allowed in rule['enum'])
                or 'const' in rule and not equal(item, rule['const'])
                or any(bound in rule and (type(item) not in (int, float)
                    or (item < rule[bound] if bound == 'minimum' else item > rule[bound])) for bound in ('minimum', 'maximum'))):
            raise ValueError('CPU configuration is outside its admitted input domain: ' + key)


def validate_cpu_execution_contract(value, *, runner=None):
    """Read the original admitted operation declaration; no hardware/authority inference."""
    _exact(value, ('schema_version', 'kind', 'operation', 'implementation', 'conformance', 'input_domain', 'sha256'), 'CPU execution contract')
    if (type(value['schema_version']) is not int or value['schema_version'] != 1
            or value['kind'] != 'training-cpu-execution-contract' or value['operation'] != 'cpu-diagnostic-v1'
            or value['conformance'] != CPU_CONFORMANCE):
        raise ValueError('Unsupported admitted CPU operation conformance')
    implementation = value['implementation']
    _exact(implementation, ('source', 'driver_protocol', 'observation_scheme', 'runner_sha256', 'wrapper_entry', 'core_sources_sha256'), 'CPU implementation')
    source = implementation['source']
    _exact(source, ('repo', 'commit', 'inventory_sha256', 'entrypoint', 'entrypoint_sha256'), 'Admitted CPU source')
    relative(source['entrypoint'])
    if (not isinstance(source['repo'], str) or not Path(source['repo']).is_absolute()
            or not isinstance(source['commit'], str) or re.fullmatch('[a-f0-9]{40}', source['commit']) is None
            or implementation['driver_protocol'] != 'training-configuration-driver-v1'
            or implementation['wrapper_entry'] != 'ergora.training.configuration:main'
            or not isinstance(implementation['observation_scheme'], str) or not implementation['observation_scheme']):
        raise ValueError('CPU contract requires its exact source ABI and fixed wrapper')
    for digest in (source['inventory_sha256'], source['entrypoint_sha256'], implementation['runner_sha256'],
                   implementation['core_sources_sha256'], value['sha256']):
        _sha(digest)
    _cpu_domain(value['input_domain'])
    if observation_sha256({key: item for key, item in value.items() if key != 'sha256'}) != value['sha256']:
        raise ValueError('CPU contract differs from its complete canonical content')
    if runner is not None:
        capability = runner.get('configuration_readback')
        if (not isinstance(capability, dict) or capability['source'] != {key: item for key, item in source.items() if key != 'entrypoint_sha256'}
                or implementation['runner_sha256'] != observation_sha256(runner)
                or implementation['observation_scheme'] != capability['observation_scheme']
                or implementation['driver_protocol'] != capability['protocol']):
            raise ValueError('CPU contract differs from its original registered runner/source')
    return value


def cpu_contract(value):
    """Only absence is ordinary scope; a present malformed contract never is."""
    if not isinstance(value, dict):
        raise ValueError('CPU contract field reader requires an original object')
    if value.get('kind') == 'training-cpu-execution-contract':
        return validate_cpu_execution_contract(value)
    execution = value.get('execution')
    if not isinstance(execution, dict) or 'cpu_contract' not in execution:
        return None
    return validate_cpu_execution_contract(execution['cpu_contract'])


def validate_cpu_contract_configuration(contract, raw):
    validate_cpu_execution_contract(contract)
    value = json_configuration(raw)
    _cpu_domain(contract['input_domain'], value, check=True)
    return value


def _preparation_sha(value):
    return hashlib.sha256(observation_bytes(value, 16 * LIMIT)).hexdigest()


def preparation_preview_body(intent):
    return validate_preparation_intent(intent)['body']


def validate_preparation_intent(intent):
    """Keep original preview, immutable confirmation and saved-intent identities distinct."""
    if not isinstance(intent, dict):
        raise ValueError('Preparation intent must be an original object')
    if intent.get('schema_version') == 1 and type(intent.get('schema_version')) is int:
        _exact(intent, _PREPARATION_FIELDS, 'Historical preparation data')
        return {'body': intent, 'preview_sha256': _preparation_sha(intent),
                'intent_sha256': _preparation_sha(intent), 'confirmation': None}
    _exact(intent, (*_PREPARATION_FIELDS, 'confirmed_preview_sha256', 'confirmation'), 'Current preparation intent')
    if type(intent['schema_version']) is not int or intent['schema_version'] != 2:
        raise ValueError('Unsupported preparation intent data shape')
    body = {key: intent[key] for key in _PREPARATION_FIELDS}
    confirmation = intent['confirmation']
    _exact(confirmation, ('kind', 'actor_id', 'project_revision', 'request_sha256'), 'Preparation confirmation')
    if (confirmation['kind'] != 'training-preparation-confirmation' or not isinstance(confirmation['actor_id'], str)
            or re.fullmatch(r'unix:[0-9]+:[^\r\n]+', confirmation['actor_id']) is None
            or type(confirmation['project_revision']) is not int or confirmation['project_revision'] != body['project_revision']
            or confirmation['request_sha256'] != _preparation_sha(body['request'])
            or intent['confirmed_preview_sha256'] != _preparation_sha(body)):
        raise ValueError('Preparation confirmation differs from its original exact preview/request/revision')
    return {'body': body, 'preview_sha256': intent['confirmed_preview_sha256'],
            'intent_sha256': _preparation_sha(intent), 'confirmation': confirmation}


def make_cpu_preparation_admission(intent):
    checked = validate_preparation_intent(intent)
    body = checked['body']
    manifest_path = 'training/manifests/' + body['experiment_id'] + '.json'
    manifest_raw = body['files'][manifest_path].encode('utf-8')
    manifest = decode_record(manifest_raw)
    contract = cpu_contract(manifest)
    if contract is None:
        return None
    if checked['confirmation'] is None or body['schema_version'] != 2:
        raise ValueError('unsupported: historical preparation has no original CPU contract confirmation')
    runner = body['sources']['runner']['document']
    if (body['operation'] != 'prepare-training' or manifest.get('experiment_id') != body['experiment_id']
            or manifest.get('local_project') != body['project']
            or body['request']['experiment'].get('experiment_id') != body['experiment_id']
            or runner.get('project') != body['project'] or runner.get('repo') != body['repo']):
        raise ValueError('CPU acceptance intent/source/manifest original identity changed')
    validate_cpu_execution_contract(contract, runner=runner)
    if body['request']['experiment']['execution'].get('cpu_contract') != contract:
        raise ValueError('Original CPU manifest differs from the confirmed source request')
    return {'schema_version': 1, 'kind': 'training-cpu-contract-admission', 'project': body['project'],
        'registration_sha256': body['registration_sha256'], 'project_revision': body['project_revision'],
        'experiment_id': body['experiment_id'], 'contract_sha256': contract['sha256'],
        'manifest_sha256': hashlib.sha256(manifest_raw).hexdigest(),
        'preparation_intent_sha256': checked['intent_sha256'], 'confirmed_preview_sha256': checked['preview_sha256'],
        'request_sha256': _preparation_sha(body['request']), 'runner_sha256': contract['implementation']['runner_sha256'],
        'source_sha256': _preparation_sha(contract['implementation']['source']),
        'core_sources_sha256': contract['implementation']['core_sources_sha256'], 'confirmation': checked['confirmation']}


def validate_cpu_preparation_admission(admission, intent, manifest_raw, runner):
    expected = make_cpu_preparation_admission(intent)
    if expected is None or admission != expected:
        raise ValueError('CPU contract admission differs from its original confirmation-bearing intent')
    body = preparation_preview_body(intent)
    if (hashlib.sha256(manifest_raw).hexdigest() != expected['manifest_sha256']
            or body['files']['training/manifests/' + body['experiment_id'] + '.json'].encode('utf-8') != manifest_raw):
        raise ValueError('CPU contract admission belongs to another original manifest')
    contract = cpu_contract(decode_record(manifest_raw))
    validate_cpu_execution_contract(contract, runner=runner)
    return contract


CPU_IDENTITY_PROTOCOL = 'training-cpu-execution-identity-v1'
CPU_IDENTITY_SCOPE = 'linux-x86_64-visible-cgroup2-local-boot'
_CPU_MODEL_FIELDS = ('vendor_id', 'cpu family', 'model', 'model name', 'stepping', 'microcode',
                     'flags', 'cache size', 'clflush size', 'cache_alignment', 'address sizes')
_CPU_LIMIT_FILES = ('cpu.max', 'cpu.max.burst', 'cpu.weight', 'cpu.idle', 'cpu.uclamp.min', 'cpu.uclamp.max',
                    'cpuset.cpus.effective', 'cpuset.mems.effective')


_CPU_PROOF_FILES = (*_CPU_LIMIT_FILES, 'cgroup.controllers', 'cgroup.subtree_control', 'cgroup.type')
_CPU_KERNEL_CONTRACT = 'linux-cgroup-init-fd-v1'
_PROC_MAGIC, _NSFS_MAGIC, _CGROUP2_MAGIC = 0x9fa0, 0x6e736673, 0x63677270
_INITIAL_CGROUP_INODE, _CGROUP_NS_TYPE = 0xeffffffb, 0x02000000



def _cpu_endpoint_ancestry(root_path, group, *, opened, metadata, control):
    """Reopen the current path tree; pinned old nodes cannot prove this endpoint."""
    flags = getattr(os, 'O_PATH', os.O_RDONLY) | os.O_DIRECTORY | os.O_NOFOLLOW
    root = opened(root_path, flags)
    root_meta = metadata(root)
    nodes, current, selected = [], root, '/'
    for part in ('', *PurePosixPath(group).parts[1:]):
        if part:
            current = opened(part, flags, current)
            selected = (PurePosixPath(selected) / part).as_posix()
        node_meta = metadata(current)
        if (node_meta['filesystem'] != _CGROUP2_MAGIC or node_meta['mount_id'] != root_meta['mount_id']
                or node_meta['device'] != root_meta['device']):
            raise ValueError('unsupported: current CPU ancestor path is overmounted')
        values = {name: control(current, name) for name in _CPU_PROOF_FILES}
        nodes.append({'relative': selected, 'node': node_meta,
            'files': {name: item[0] for name, item in values.items()},
            'file_identities': {name: item[1] for name, item in values.items()}})
    return root_meta, nodes


def _cpu_fd_scope():
    """Context manager for genuine own-proc/nsfs and opened namespace-visible tree."""
    from contextlib import contextmanager, ExitStack
    import ctypes
    import fcntl
    import threading

    @contextmanager
    def scope():
        if os.uname().machine != 'x86_64' or ctypes.sizeof(ctypes.c_long) != 8:
            raise ValueError('unsupported: CPU FD observer ABI is not Linux x86_64')
        libc = ctypes.CDLL(None, use_errno=True)
        libc.fstatfs.argtypes = (ctypes.c_int, ctypes.c_void_p)
        libc.fstatfs.restype = ctypes.c_int
        if getattr(libc, 'syscall', None) is None:
            raise ValueError('unsupported: kernel FD statx syscall entry is unavailable')
        libc.syscall.restype = ctypes.c_long
        with ExitStack() as stack:
            def opened(path, flags, parent=None):
                fd = os.open(path, flags | getattr(os, 'O_CLOEXEC', 0), dir_fd=parent)
                stack.callback(os.close, fd)
                return fd
            def magic(fd):
                buffer = ctypes.create_string_buffer(256)
                if libc.fstatfs(fd, buffer) != 0:
                    raise OSError(ctypes.get_errno(), 'fstatfs failed for original CPU proof FD')
                return ctypes.c_long.from_buffer(buffer).value & 0xffffffff
            def text_fd(fd, limit=LIMIT):
                raw = bytearray()
                while len(raw) <= limit:
                    chunk = os.read(fd, min(65536, limit + 1 - len(raw)))
                    if not chunk:
                        break
                    raw.extend(chunk)
                if len(raw) > limit:
                    raise ValueError('CPU FD observation exceeds its complete read capacity')
                return bytes(raw).decode('utf-8')
            flags = getattr(os, 'O_PATH', os.O_RDONLY) | os.O_DIRECTORY
            proc = opened('/proc', flags | os.O_NOFOLLOW)
            if magic(proc) != _PROC_MAGIC:
                raise ValueError('unsupported: CPU subject route is not genuine procfs')
            thread = opened('thread-self', flags, proc)
            leader = opened('self', flags, proc)
            if magic(thread) != _PROC_MAGIC or magic(leader) != _PROC_MAGIC:
                raise ValueError('unsupported: CPU subject directory is not genuine procfs')
            def mount_id(fd):
                # x86_64 statx UAPI: AT_EMPTY_PATH, STATX_MNT_ID (Linux 5.8+).
                # Read the opened descriptor directly; proc fdinfo can itself be overmounted.
                buffer = ctypes.create_string_buffer(256)
                result = libc.syscall(ctypes.c_long(332), ctypes.c_int(fd), ctypes.c_char_p(b''),
                    ctypes.c_int(0x1100), ctypes.c_uint(0x1000), ctypes.byref(buffer))
                if result != 0:
                    raise ValueError('unsupported: kernel FD statx mount identity is unavailable: ' + str(ctypes.get_errno()))
                if not ctypes.c_uint32.from_buffer(buffer).value & 0x1000:
                    raise ValueError('unsupported: kernel FD statx did not provide STATX_MNT_ID')
                return ctypes.c_uint64.from_buffer(buffer, 0x90).value
            def metadata(fd):
                value = os.fstat(fd)
                return {'device': value.st_dev, 'inode': value.st_ino, 'mode': value.st_mode,
                        'filesystem': magic(fd), 'mount_id': mount_id(fd)}
            proc_meta, thread_meta, leader_meta = metadata(proc), metadata(thread), metadata(leader)
            if any(item['mount_id'] != proc_meta['mount_id'] or item['device'] != proc_meta['device'] for item in (thread_meta, leader_meta)):
                raise ValueError('unsupported: own subject proc directory has a different mount')
            proc_files = {}
            def proc_text(name, parent=thread, limit=LIMIT):
                fd = opened(name, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, 'O_NONBLOCK', 0), parent)
                observed = metadata(fd)
                if (observed['filesystem'] != _PROC_MAGIC or observed['mount_id'] != proc_meta['mount_id']
                        or observed['device'] != proc_meta['device'] or not stat.S_ISREG(observed['mode'])):
                    raise ValueError('unsupported: CPU proc file has a different actual mount or was overmounted')
                raw = text_fd(fd, limit)
                route = {thread: 'thread', leader: 'leader', proc: 'proc'}[parent] + '/' + name
                encoded = raw.encode('utf-8')
                proc_files.setdefault(route, []).append({'identity': observed,
                    'sha256': hashlib.sha256(encoded).hexdigest(), 'bytes': len(encoded)})
                return raw
            last_subject_raw = {}
            def subject():
                raw = proc_text('stat')
                parts = raw.rsplit(')', 1)[1].split()
                status_raw = proc_text('status')
                status = dict(line.split(':', 1) for line in status_raw.splitlines() if ':' in line)
                leader_raw = proc_text('stat', leader)
                leader_stat = leader_raw.rsplit(')', 1)[1].split()
                last_subject_raw.clear()
                last_subject_raw.update(thread_stat=raw, thread_status=status_raw, leader_stat=leader_raw,
                    observed_pid=os.getpid(), observed_tid=threading.get_native_id())
                if int(status['Tgid']) != os.getpid() or int(status['Pid']) != threading.get_native_id():
                    raise ValueError('unsupported: proc subject is not the actual calling process/thread')
                return {'pid': os.getpid(), 'tid': threading.get_native_id(), 'start_ticks': int(leader_stat[19]),
                        'thread_start_ticks': int(parts[19]), 'parent_pid': int(leader_stat[1]),
                        'boot_id': proc_text('sys/kernel/random/boot_id', proc).strip()}
            ns_dir = opened('ns', flags | os.O_NOFOLLOW, thread)
            entry = opened('cgroup', getattr(os, 'O_PATH', os.O_RDONLY) | os.O_NOFOLLOW, ns_dir)
            entry_meta = metadata(entry)
            if (magic(ns_dir) != _PROC_MAGIC or metadata(ns_dir)['mount_id'] != proc_meta['mount_id']
                    or entry_meta['filesystem'] != _PROC_MAGIC or entry_meta['mount_id'] != proc_meta['mount_id']
                    or not stat.S_ISLNK(entry_meta['mode'])):
                raise ValueError('unsupported: namespace entry is not the original procfs magic link')
            target = opened('cgroup', os.O_RDONLY, ns_dir)
            target_meta = metadata(target)
            ns_type = fcntl.ioctl(target, 0xb703)
            if target_meta['filesystem'] != _NSFS_MAGIC or ns_type != _CGROUP_NS_TYPE:
                raise ValueError('unsupported: CPU namespace FD is not a genuine cgroup namespace')
            membership, mountinfo = proc_text('cgroup'), proc_text('mountinfo')
            if len(membership.strip().splitlines()) != 1 or not membership.startswith('0::/'):
                raise ValueError('unsupported: CPU has no unambiguous unified cgroup membership')
            group = membership.strip()[3:]
            if str(PurePosixPath(group)) != group or '..' in PurePosixPath(group).parts or len(PurePosixPath(group).parts) > 64:
                raise ValueError('unsupported: CPU membership path is not canonical/bounded')
            candidates = []
            for record in mountinfo.splitlines():
                split = record.split(' - ')
                if len(split) == 2 and split[1].startswith('cgroup2 '):
                    before = split[0].split()
                    if len(before) >= 6 and before[3] == '/':
                        candidates.append((before[4], record, before))
            selected = None
            for _, record, fields in sorted(candidates):
                point = re.sub(r'\\([0-7]{3})', lambda item: chr(int(item.group(1), 8)), fields[4])
                root = opened(point, flags | os.O_NOFOLLOW)
                root_meta = metadata(root)
                if root_meta['filesystem'] == _CGROUP2_MAGIC and root_meta['mount_id'] == int(fields[0]):
                    selected = (root, root_meta, record, point)
                    break
            if selected is None:
                raise ValueError('unsupported: no genuine selected cgroup2 full-root FD')
            root, root_meta, selected_record, selected_point = selected
            def control(node, name):
                try:
                    fd = opened(name, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, 'O_NONBLOCK', 0), node)
                except FileNotFoundError:
                    return None, None
                meta = metadata(fd)
                if (meta['filesystem'] != _CGROUP2_MAGIC or meta['mount_id'] != root_meta['mount_id']
                        or meta['device'] != root_meta['device'] or not stat.S_ISREG(meta['mode'])):
                    raise ValueError('unsupported: CPU control file is outside its selected opened tree')
                return text_fd(fd, 4096), meta
            nodes, current, relative_path = [], root, '/'
            for part in ('', *PurePosixPath(group).parts[1:]):
                if part:
                    current = opened(part, flags | os.O_NOFOLLOW, current)
                    relative_path = (PurePosixPath(relative_path) / part).as_posix()
                node_meta = metadata(current)
                if node_meta['filesystem'] != _CGROUP2_MAGIC or node_meta['mount_id'] != root_meta['mount_id'] or node_meta['device'] != root_meta['device']:
                    raise ValueError('unsupported: CPU ancestor directory is hidden by another mount')
                values = {name: control(current, name) for name in _CPU_PROOF_FILES}
                nodes.append((current, {'relative': relative_path, 'node': node_meta,
                    'files': {name: value[0] for name, value in values.items()},
                    'file_identities': {name: value[1] for name, value in values.items()}}))
            first_subject = subject()
            value = {'contract': _CPU_KERNEL_CONTRACT, 'kernel': dict(zip(('sysname', 'nodename', 'release', 'version', 'machine'), os.uname())),
                'proc_root': proc_meta, 'thread_directory': thread_meta, 'leader_directory': leader_meta,
                'proc_files': proc_files, 'namespace_entry': entry_meta,
                'namespace_target': target_meta, 'namespace_type': ns_type, 'namespace_link': os.readlink('cgroup', dir_fd=ns_dir),
                'subject': first_subject, 'subject_raw': dict(last_subject_raw), 'membership': membership, 'mountinfo': mountinfo, 'selected_mount': selected_record,
                'root': root_meta, 'ancestors': [row for _, row in nodes]}
            def finish():
                value['subject_after'] = subject()
                value['subject_raw_after'] = dict(last_subject_raw)
                value['membership_after'] = proc_text('cgroup')
                value['mountinfo_after'] = proc_text('mountinfo')
                fresh_target = opened('cgroup', os.O_RDONLY, ns_dir)
                value['namespace_target_after'] = metadata(fresh_target)
                value['namespace_entry_after'] = metadata(opened('cgroup', getattr(os, 'O_PATH', os.O_RDONLY) | os.O_NOFOLLOW, ns_dir))
                after_membership = value['membership_after'].strip().splitlines()
                if len(after_membership) != 1 or not after_membership[0].startswith('0::/'):
                    raise ValueError('unsupported: current CPU membership is not unified')
                after_group = after_membership[0][3:]
                if (str(PurePosixPath(after_group)) != after_group or '..' in PurePosixPath(after_group).parts
                        or len(PurePosixPath(after_group).parts) > 64):
                    raise ValueError('unsupported: current CPU membership is not canonical/bounded')
                value['root_after'], value['ancestors_after'] = _cpu_endpoint_ancestry(
                    selected_point, after_group, opened=opened, metadata=metadata, control=control)
            yield value, finish
    return scope()


def _validate_cpu_fd_provenance(value, raw, *, require_complete=True):
    """Only original genuine-FD observations qualify; namespace strings never do."""
    if not isinstance(value, dict):
        raise ValueError('unsupported: CPU observations have no independent trusted proof of complete allocation ancestry')
    fields = ('contract', 'kernel', 'proc_root', 'thread_directory', 'leader_directory', 'proc_files', 'namespace_entry', 'namespace_target', 'namespace_type',
              'namespace_link', 'subject', 'membership', 'mountinfo', 'selected_mount', 'root', 'ancestors',
              'subject_raw', 'subject_after', 'subject_raw_after', 'membership_after', 'mountinfo_after', 'namespace_target_after', 'namespace_entry_after', 'root_after', 'ancestors_after')
    _exact(value, fields, 'Original CPU allocation FD proof')
    def meta(item, fs):
        _exact(item, ('device', 'inode', 'mode', 'filesystem', 'mount_id'), 'Original CPU FD identity')
        if any(type(item[key]) is not int or item[key] < 0 for key in item) or item['filesystem'] != fs:
            raise ValueError('unsupported: CPU FD filesystem/type identity is not applicable')
    if value['contract'] != _CPU_KERNEL_CONTRACT or value['kernel'].get('sysname') != 'Linux' or value['kernel'].get('machine') != 'x86_64':
        raise ValueError('unsupported: CPU kernel conformance contract is not applicable')
    for key in ('proc_root', 'thread_directory', 'leader_directory', 'namespace_entry'):
        meta(value[key], _PROC_MAGIC)
        if (value[key]['mount_id'] != value['proc_root']['mount_id'] or value[key]['device'] != value['proc_root']['device']):
            raise ValueError('unsupported: CPU namespace is associated with another proc mount')
    if any(not stat.S_ISDIR(value[key]['mode']) for key in ('proc_root', 'thread_directory', 'leader_directory')):
        raise ValueError('CPU proc route is not an original subject directory')
    if not stat.S_ISLNK(value['namespace_entry']['mode']):
        raise ValueError('unsupported: CPU namespace entry is not an original proc magic link')
    meta(value['namespace_target'], _NSFS_MAGIC)
    if (value['namespace_type'] != _CGROUP_NS_TYPE
            or value['namespace_link'] != 'cgroup:[' + str(value['namespace_target']['inode']) + ']'):
        raise ValueError('CPU namespace target is not the original cgroup namespace FD')
    subject = value['subject']
    _exact(subject, ('pid', 'tid', 'start_ticks', 'thread_start_ticks', 'parent_pid', 'boot_id'), 'Original CPU subject')
    if (any(type(subject[key]) is not int or subject[key] < (1 if key in ('pid', 'tid') else 0) for key in subject if key != 'boot_id')
            or subject['boot_id'] != raw['boot_id'].strip() or subject != value['subject_after']):
        raise ValueError('unsupported: CPU observation changed its actual process/thread subject')
    for key, observed in (('subject_raw', subject), ('subject_raw_after', value['subject_after'])):
        recorded = value[key]
        _exact(recorded, ('thread_stat', 'thread_status', 'leader_stat', 'observed_pid', 'observed_tid'), 'CPU original subject raw facts')
        status = dict(line.split(':', 1) for line in recorded['thread_status'].splitlines() if ':' in line)
        leader_fields = recorded['leader_stat'].rsplit(')', 1)[1].split()
        thread_fields = recorded['thread_stat'].rsplit(')', 1)[1].split()
        if (int(status['Tgid']) != observed['pid'] or int(status['Pid']) != observed['tid']
                or recorded['observed_pid'] != observed['pid'] or recorded['observed_tid'] != observed['tid']
                or int(recorded['leader_stat'].split(' ', 1)[0]) != observed['pid']
                or int(recorded['thread_stat'].split(' ', 1)[0]) != observed['tid']
                or int(leader_fields[19]) != observed['start_ticks'] or int(thread_fields[19]) != observed['thread_start_ticks']
                or int(leader_fields[1]) != observed['parent_pid']):
            raise ValueError('CPU calling subject differs from its original genuine proc raw facts')
    originals = {'thread/stat': [value[key]['thread_stat'] for key in ('subject_raw', 'subject_raw_after')],
        'thread/status': [value[key]['thread_status'] for key in ('subject_raw', 'subject_raw_after')],
        'leader/stat': [value[key]['leader_stat'] for key in ('subject_raw', 'subject_raw_after')],
        'thread/cgroup': [value[key] for key in ('membership', 'membership_after')],
        'thread/mountinfo': [value[key] for key in ('mountinfo', 'mountinfo_after')],
        'proc/sys/kernel/random/boot_id': [raw['boot_id'], raw['boot_id']]}
    _exact(value['proc_files'], originals, 'Original CPU proc file descriptor provenance')
    for route, contents in originals.items():
        records = value['proc_files'][route]
        if not isinstance(records, list) or len(records) != 2:
            raise ValueError('CPU proc file lacks both original descriptor observations')
        for record, content in zip(records, contents):
            _exact(record, ('identity', 'sha256', 'bytes'), 'Original CPU proc file observation')
            identity = record['identity']
            meta(identity, _PROC_MAGIC)
            encoded = content.encode('utf-8')
            if (identity['mount_id'] != value['proc_root']['mount_id'] or identity['device'] != value['proc_root']['device']
                    or not stat.S_ISREG(identity['mode']) or record['bytes'] != len(encoded)
                    or record['sha256'] != hashlib.sha256(encoded).hexdigest()):
                raise ValueError('CPU proc file differs from its actual subject mount/raw observation')
        if records[0]['identity'] != records[1]['identity']:
            raise ValueError('CPU proc file descriptor object changed during observation')
    if (value['namespace_link'] != raw['cgroup_namespace'] or value['membership'] != raw['cgroup_membership']
            or value['selected_mount'] != raw['cgroup_mount']):
        raise ValueError('CPU visible facts differ from their original FD provenance')
    if not require_complete:
        return value
    if value['namespace_target']['inode'] != _INITIAL_CGROUP_INODE:
        raise ValueError('unsupported: actual calling subject is not in the initial cgroup namespace')
    if (value['membership'] != raw['cgroup_membership'] or value['selected_mount'] != raw['cgroup_mount']
            or value['membership'] != value['membership_after'] or value['mountinfo'] != value['mountinfo_after']
            or value['namespace_target'] != value['namespace_target_after'] or value['namespace_entry'] != value['namespace_entry_after']
            or value['root'] != value['root_after'] or value['ancestors'] != value['ancestors_after']):
        raise ValueError('unsupported: CPU namespace/membership/control state changed during observation')
    record = value['selected_mount'].split(' - ')
    if len(record) != 2 or not record[1].startswith('cgroup2 ') or record[0].split()[3] != '/':
        raise ValueError('unsupported: CPU selected mount is not the actual full cgroup2 root')
    meta(value['root'], _CGROUP2_MAGIC)
    if (value['root']['mount_id'] != int(record[0].split()[0]) or value['selected_mount'] not in value['mountinfo'].splitlines()
            or not stat.S_ISDIR(value['root']['mode'])
            or record[0].split()[2] != str(os.major(value['root']['device'])) + ':' + str(os.minor(value['root']['device']))):
        raise ValueError('unsupported: CPU opened root differs from its original selected mount record')
    if len(value['ancestors']) != len(raw['limits']):
        raise ValueError('unsupported: CPU actual subject ancestor walk is incomplete')
    for index, (item, limit) in enumerate(zip(value['ancestors'], raw['limits'])):
        _exact(item, ('relative', 'node', 'files', 'file_identities'), 'Original CPU ancestor FD record')
        _exact(item['files'], _CPU_PROOF_FILES, 'Original CPU controller files')
        _exact(item['file_identities'], _CPU_PROOF_FILES, 'Original CPU controller FD identities')
        meta(item['node'], _CGROUP2_MAGIC)
        if (item['relative'] != limit['relative'] or item['node']['mount_id'] != value['root']['mount_id']
                or item['node']['device'] != value['root']['device']
                or {key: item['files'][key] for key in _CPU_LIMIT_FILES} != limit['files']):
            raise ValueError('unsupported: CPU ancestor is outside its original selected tree')
        if index and (item['files']['cgroup.type'] is None or item['files']['cgroup.type'].strip() != 'domain'):
            raise ValueError('unsupported: CPU matching requires a domain cgroup hierarchy')
        if index == 0 and item['files']['cgroup.type'] is not None:
            raise ValueError('unsupported: opened full root claims a non-root cgroup.type interface')
        controllers = (item['files']['cgroup.controllers'] or '').split()
        if index == 0 and (item['files']['cpu.max'] is not None or item['files']['cpu.weight'] is not None):
            raise ValueError('unsupported: opened initial full root has inconsistent non-root CPU control files')
        if index == 0 and not {'cpu', 'cpuset'} <= set(controllers):
            raise ValueError('unsupported: CPU/cpuset controller applicability is unknown or bound outside v2')
        if index and not {'cpu', 'cpuset'} <= set((value['ancestors'][index - 1]['files']['cgroup.subtree_control'] or '').split()):
            raise ValueError('unsupported: CPU/cpuset hierarchy is not delegated in the supported scope')
        for name, content in item['files'].items():
            identity = item['file_identities'][name]
            if content is None:
                if identity is not None:
                    raise ValueError('CPU missing controller file claims a descriptor identity')
                continue
            if not isinstance(content, str):
                raise ValueError('CPU controller facts require complete original text')
            meta(identity, _CGROUP2_MAGIC)
            if identity['device'] != value['root']['device'] or identity['mount_id'] != value['root']['mount_id'] or not stat.S_ISREG(identity['mode']):
                raise ValueError('unsupported: CPU control descriptor is not in its selected actual tree')
    if value['ancestors'][0]['node'] != value['root']:
        raise ValueError('unsupported: CPU walk does not end at the opened full root')
    return value


def _cpu_list(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError('unsupported: CPU allocation has no complete processor list')
    values = set()
    for part in re.split(r'[\s,]+', raw.strip()):
        if re.fullmatch(r'[0-9]+(?:-[0-9]+)?', part) is None:
            raise ValueError('Unsupported CPU list syntax')
        ends = [int(item) for item in part.split('-')]
        low, high = ends[0], ends[-1]
        if not 0 <= low <= high <= 65535 or high - low > 4096:
            raise ValueError('CPU list exceeds its complete bounds')
        values.update(range(low, high + 1))
        if len(values) > 4096:
            raise ValueError('CPU identity exceeds its complete processor capacity')
    return sorted(values)


def _cpu_identity_from_raw(raw):
    """Fixed data-only decoder of the original selected static OS observations."""
    _exact(raw, ('boot_id', 'architecture', 'online', 'affinity', 'models', 'cpus', 'frequency',
                 'cgroup_membership', 'cgroup_mount', 'cgroup_namespace', 'limits', 'scheduler',
                 *(['allocation_provenance'] if 'allocation_provenance' in raw else [])), 'CPU identity raw facts')
    boot = raw['boot_id'].strip() if isinstance(raw['boot_id'], str) else ''
    if re.fullmatch('[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}', boot) is None or raw['architecture'] != 'x86_64':
        raise ValueError('unsupported: CPU reuse requires original local-boot x86_64 identity')
    online = _cpu_list(raw['online'])
    affinity = raw['affinity']
    if (not isinstance(affinity, list) or not affinity or any(type(cpu) is not int for cpu in affinity)
            or affinity != sorted(set(affinity)) or not set(affinity) <= set(online)):
        raise ValueError('CPU identity has no complete actual process affinity')
    models = raw['models']
    if not isinstance(models, list) or not 1 <= len(models) <= len(affinity):
        raise ValueError('CPU identity requires its observed processor models')
    for model in models:
        _exact(model, _CPU_MODEL_FIELDS, 'CPU model observation')
        if any(not isinstance(model[key], str) or not model[key].strip()
               for key in ('vendor_id', 'cpu family', 'model', 'model name', 'stepping', 'flags')):
            raise ValueError('unsupported: original CPU model/features are unavailable')
        if any(model[key] is not None and not isinstance(model[key], str) for key in model):
            raise ValueError('CPU model facts require original textual values')
    cpus = raw['cpus']
    if not isinstance(cpus, list) or len(cpus) != len(affinity):
        raise ValueError('CPU identity omits allocated topology')
    topology = []
    for item in cpus:
        _exact(item, ('cpu', 'model_index', 'package_id', 'core_id', 'thread_siblings'), 'CPU topology observation')
        if (type(item['cpu']) is not int or type(item['model_index']) is not int
                or not 0 <= item['model_index'] < len(models)
                or any(not isinstance(item[key], str) or re.fullmatch(r'[0-9]+\s*', item[key]) is None for key in ('package_id', 'core_id'))):
            raise ValueError('unsupported: CPU topology is unknown')
        siblings = _cpu_list(item['thread_siblings'])
        if item['cpu'] not in siblings or not set(siblings) <= set(online):
            raise ValueError('CPU thread topology differs from original online processors')
        topology.append({'cpu': item['cpu'], 'model_index': item['model_index'],
            'package_id': int(item['package_id']), 'core_id': int(item['core_id']), 'thread_siblings': siblings})
    if [item['cpu'] for item in topology] != affinity:
        raise ValueError('CPU topology does not cover the exact actual affinity')
    by_cpu = {item['cpu']: item for item in topology}
    for item in topology:
        for sibling in set(item['thread_siblings']) & set(affinity):
            other = by_cpu[sibling]
            if any(other[key] != item[key] for key in ('package_id', 'core_id', 'thread_siblings')):
                raise ValueError('CPU topology has inconsistent original physical-core siblings')
    frequency, covered = [], set()
    if not isinstance(raw['frequency'], list) or not 1 <= len(raw['frequency']) <= 4096:
        raise ValueError('unsupported: actual CPU frequency allocation policy is unavailable')
    for item in raw['frequency']:
        _exact(item, ('related_cpus', 'driver', 'governor', 'minimum_khz', 'maximum_khz', 'hardware_minimum_khz', 'hardware_maximum_khz'), 'CPU frequency policy')
        selected = _cpu_list(item['related_cpus'])
        if covered & set(selected) or not set(selected) & set(affinity):
            raise ValueError('CPU frequency policies overlap or have no actual allocated CPU')
        covered.update(selected)
        if any(not isinstance(item[key], str) or not item[key].strip() for key in ('driver', 'governor')):
            raise ValueError('unsupported: CPU frequency policy identity is unavailable')
        limits = {}
        for key in ('minimum_khz', 'maximum_khz', 'hardware_minimum_khz', 'hardware_maximum_khz'):
            if not isinstance(item[key], str) or re.fullmatch(r'[0-9]+\s*', item[key]) is None or int(item[key]) <= 0:
                raise ValueError('unsupported: CPU frequency allocation bounds are unavailable')
            limits[key] = int(item[key])
        if not limits['hardware_minimum_khz'] <= limits['minimum_khz'] <= limits['maximum_khz'] <= limits['hardware_maximum_khz']:
            raise ValueError('CPU frequency allocation bounds are inconsistent')
        frequency.append({'cpus': selected, 'driver': item['driver'].strip(), 'governor': item['governor'].strip(), **limits})
    if not set(affinity) <= covered:
        raise ValueError('unsupported: CPU frequency policy omits allocated processors')
    membership = raw['cgroup_membership'].strip().splitlines() if isinstance(raw['cgroup_membership'], str) else []
    if len(membership) != 1 or not membership[0].startswith('0::/'):
        raise ValueError('unsupported: CPU allocation requires one complete unified cgroup2 hierarchy')
    group = membership[0][3:]
    if (str(PurePosixPath(group)) != group or '..' in PurePosixPath(group).parts
            or not group.startswith('/') or '//' in group or not isinstance(raw['cgroup_namespace'], str)
            or re.fullmatch(r'cgroup:\[[0-9]+\]', raw['cgroup_namespace']) is None):
        raise ValueError('unsupported: CPU allocation namespace is not canonical')
    mount = raw['cgroup_mount'].split(' - ') if isinstance(raw['cgroup_mount'], str) else []
    if len(mount) != 2 or not mount[1].startswith('cgroup2 ') or len(mount[0].split()) < 6 or mount[0].split()[3] != '/':
        raise ValueError('unsupported: CPU cgroup ancestry is not fully visible')
    expected = ['/']
    for part in PurePosixPath(group).parts[1:]:
        expected.append((PurePosixPath(expected[-1]) / part).as_posix())
    allocations = raw['limits']
    if not isinstance(allocations, list) or not len(allocations) == len(expected) <= 64:
        raise ValueError('unsupported: CPU allocation omits original ancestor limits')
    for ordinal, item in enumerate(allocations):
        _exact(item, ('relative', 'files'), 'CPU ancestor allocation')
        _exact(item['files'], _CPU_LIMIT_FILES, 'CPU ancestor limit files')
        if item['relative'] != expected[ordinal] or any(value is not None and not isinstance(value, str) for value in item['files'].values()):
            raise ValueError('CPU allocation changed its original hierarchy')
        # These are namespace-visible observations only. Neither present nor
        # absent controller interfaces establish that no hidden ancestor exists.
        if ordinal > 0:
            weight = item['files']['cpu.weight']
            if not isinstance(weight, str) or re.fullmatch(r'[0-9]+\s*', weight) is None or not 1 <= int(weight) <= 10000:
                raise ValueError('unsupported: CPU fair-share allocation is unavailable')
            quota = item['files']['cpu.max']
            if not isinstance(quota, str) or re.fullmatch(r'(?:max|[1-9][0-9]*) [1-9][0-9]*\s*', quota) is None:
                raise ValueError('unsupported: CPU bandwidth allocation is unavailable')
        for name in ('cpuset.cpus.effective', 'cpuset.mems.effective'):
            selected = _cpu_list(item['files'][name])
            if name == 'cpuset.cpus.effective' and not set(affinity) <= set(selected):
                raise ValueError('CPU affinity escapes original effective cpuset allocation')
    scheduler = raw['scheduler']
    _exact(scheduler, ('policy', 'priority', 'nice', 'uclamp_min', 'uclamp_max'), 'CPU scheduler allocation')
    if (any(type(scheduler[key]) is not int for key in ('policy', 'priority', 'nice'))
            or scheduler['policy'] != 0 or scheduler['priority'] != 0 or not -20 <= scheduler['nice'] <= 19
            or any(not isinstance(scheduler[key], str) or re.fullmatch(r'[0-9]+\s*', scheduler[key]) is None for key in ('uclamp_min', 'uclamp_max'))
            or not 0 <= int(scheduler['uclamp_min']) <= int(scheduler['uclamp_max']) <= 1024):
        raise ValueError('unsupported: actual CPU scheduler allocation is unavailable')
    return {'protocol': CPU_IDENTITY_PROTOCOL, 'scope': CPU_IDENTITY_SCOPE,
        'hardware': {'boot_id': boot, 'architecture': raw['architecture'], 'online_cpus': online,
            'models': [dict(model) for model in models], 'topology': topology},
        'placement': {'affinity': affinity, 'cgroup': {'namespace': raw['cgroup_namespace'], 'path': group,
            'allocations': [{'relative': item['relative'], 'files': dict(item['files'])} for item in allocations]}, 'frequency': sorted(frequency, key=lambda item: item['cpus']),
            'scheduler': {**scheduler, 'uclamp_min': int(scheduler['uclamp_min']), 'uclamp_max': int(scheduler['uclamp_max'])}}}


def _read_cpu_execution_identity(value):
    """Read saved visible CPU observations; this establishes no allocation authority."""
    _exact(value, ('protocol', 'scope', 'raw', 'identity', 'raw_sha256', 'identity_sha256'), 'CPU execution identity')
    if value['protocol'] != CPU_IDENTITY_PROTOCOL or value['scope'] != CPU_IDENTITY_SCOPE:
        raise ValueError('unsupported: CPU execution identity has no fixed reader')
    identity = _cpu_identity_from_raw(value['raw'])
    if 'allocation_provenance' in value['raw']:
        _validate_cpu_fd_provenance(value['raw']['allocation_provenance'], value['raw'], require_complete=False)
    if (value['identity'] != identity or value['raw_sha256'] != observation_sha256(value['raw'])
            or value['identity_sha256'] != observation_sha256(identity)):
        raise ValueError('CPU execution identity differs from its original raw facts')
    return identity



def validate_cpu_execution_identity(value):
    """Qualify only genuine original own-subject FD and complete allocation proof."""
    identity = _read_cpu_execution_identity(value)
    proof = _validate_cpu_fd_provenance(value['raw'].get('allocation_provenance'), value['raw'])
    return {**identity, 'kernel_contract': proof['contract'],
        'kernel': {key: proof['kernel'][key] for key in ('sysname', 'release', 'version', 'machine')},
        'allocation_objects': [{'relative': row['relative'], 'device': row['node']['device'],
                               'inode': row['node']['inode']} for row in proof['ancestors']]}


def _collect_cpu_execution_identity():
    """Read only this process's effective CPU scope and necessary allocation facts."""
    if os.name != 'posix' or not hasattr(os, 'sched_getaffinity') or os.uname().sysname != 'Linux' or os.uname().machine != 'x86_64':
        raise ValueError('unsupported: CPU reuse has no applicable static OS reader')
    def text(path, *, optional=False, limit=LIMIT):
        try:
            fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
            with os.fdopen(fd, 'rb') as stream:
                raw = stream.read(limit + 1)
            if len(raw) > limit:
                raise ValueError('CPU static facts exceed their complete read capacity')
            return raw.decode('utf-8')
        except FileNotFoundError:
            if optional:
                return None
            raise ValueError('unsupported: CPU static OS fact is unavailable: ' + str(path)) from None
        except (OSError, UnicodeError) as error:
            raise ValueError('unsupported: CPU static OS fact cannot be read: ' + str(path)) from error
    affinity = sorted(os.sched_getaffinity(0))
    scope = _cpu_fd_scope()
    proof, finish = scope.__enter__()
    try:
        membership = proof['membership']
        mounts = [proof['selected_mount']]
        ancestors = [{'relative': row['relative'], 'files': {name: row['files'][name] for name in _CPU_LIMIT_FILES}}
                     for row in proof['ancestors']]
        records = {}
        for block in text('/proc/cpuinfo', limit=16 * LIMIT).strip().split('\n\n'):
            record = dict(line.split(':', 1) for line in block.splitlines() if ':' in line)
            record = {key.strip(): value.strip() for key, value in record.items()}
            if record.get('processor', '').isdigit() and int(record['processor']) in affinity:
                records[int(record['processor'])] = record
        cpu_root, models, cpus = Path('/sys/devices/system/cpu'), [], []
        for cpu in affinity:
            if cpu not in records:
                raise ValueError('unsupported: allocated CPU has no original model observation')
            model = {key: records[cpu].get(key) for key in _CPU_MODEL_FIELDS}
            if model not in models:
                models.append(model)
            topology = cpu_root / ('cpu' + str(cpu)) / 'topology'
            cpus.append({'cpu': cpu, 'model_index': models.index(model),
                'package_id': text(topology / 'physical_package_id', limit=4096),
                'core_id': text(topology / 'core_id', limit=4096),
                'thread_siblings': text(topology / 'thread_siblings_list', limit=4096)})
        frequency, policies = [], set()
        for cpu in affinity:
            try:
                directory = (cpu_root / ('cpu' + str(cpu)) / 'cpufreq').resolve(strict=True)
            except OSError as error:
                raise ValueError('unsupported: allocated CPU has no visible frequency allocation policy') from error
            if directory.parent != cpu_root / 'cpufreq' or re.fullmatch('policy[0-9]+', directory.name) is None:
                raise ValueError('unsupported: allocated CPU frequency policy is not canonical')
            policies.add(directory)
        for directory in sorted(policies):
            related = text(directory / 'related_cpus', limit=65536)
            if not set(_cpu_list(related)) & set(affinity):
                continue
            names = {'driver': 'scaling_driver', 'governor': 'scaling_governor', 'minimum_khz': 'scaling_min_freq',
                     'maximum_khz': 'scaling_max_freq', 'hardware_minimum_khz': 'cpuinfo_min_freq', 'hardware_maximum_khz': 'cpuinfo_max_freq'}
            frequency.append({'related_cpus': related, **{key: text(directory / name, limit=4096) for key, name in names.items()}})
        sched = dict(line.split(':', 1) for line in text('/proc/thread-self/sched').splitlines() if ':' in line)
        sched = {key.strip(): value.strip() for key, value in sched.items()}
        raw = {'boot_id': text('/proc/sys/kernel/random/boot_id', limit=4096), 'architecture': os.uname().machine,
            'online': text(cpu_root / 'online', limit=65536), 'affinity': affinity, 'models': models, 'cpus': cpus,
            'frequency': frequency, 'cgroup_membership': membership, 'cgroup_mount': mounts[0],
            'cgroup_namespace': proof['namespace_link'], 'limits': ancestors, 'allocation_provenance': proof,
            'scheduler': {'policy': os.sched_getscheduler(0), 'priority': os.sched_getparam(0).sched_priority,
                'nice': os.getpriority(os.PRIO_PROCESS, 0), 'uclamp_min': sched.get('effective uclamp.min'), 'uclamp_max': sched.get('effective uclamp.max')}}
        finish()
        if affinity != sorted(os.sched_getaffinity(0)) or membership != text('/proc/thread-self/cgroup'):
            raise ValueError('unsupported: CPU placement changed while static facts were collected')
        identity = _cpu_identity_from_raw(raw)
        return {'protocol': CPU_IDENTITY_PROTOCOL, 'scope': CPU_IDENTITY_SCOPE, 'raw': raw, 'identity': identity,
                'raw_sha256': observation_sha256(raw), 'identity_sha256': observation_sha256(identity)}

    finally:
        scope.__exit__(None, None, None)



def cpu_execution_identity():
    """Observe visible static facts in place, without certifying allocation ancestry."""
    try:
        return _collect_cpu_execution_identity()
    except (OSError, ValueError) as error:
        if str(error).startswith('unsupported:'):
            raise
        raise ValueError('unsupported: actual CPU hardware/placement facts cannot be fully observed: ' + str(error)) from error


def cpu_window_identity(request, phase, operation, windows, before, after):
    """Bind source-owned observations to the original measured window, not a new clock."""
    value = {'protocol': 'training-cpu-window-identity-v1', 'binding': request['binding'],
        'execution_phase_id': request['execution_phase_id'],
        'native_request_sha256': request['native_request_sha256'], 'managed': request['managed'],
        'source': request['configuration_readback']['source'], 'phase': phase, 'operation': operation,
        'windows': windows, 'before': before, 'after': after, 'state': 'complete', 'reason': None}
    try:
        for observed in (before, after):
            if isinstance(observed, dict) and set(observed) == {'unsupported_reason'}:
                raise ValueError(observed['unsupported_reason'])
        if _read_cpu_execution_identity(before) != _read_cpu_execution_identity(after):
            raise ValueError('unsupported: CPU hardware/placement changed across the original window')
        if validate_cpu_execution_identity(before) != validate_cpu_execution_identity(after):
            raise ValueError('unsupported: CPU allocation objects changed across the original window')
    except (ValueError, TypeError) as error:
        value.update(state='unsupported', reason=str(error))
    return value


def validate_cpu_window_identity(value, *, binding, native_request_sha256, managed, source, execution_phase_id, phase, operation, windows, require_complete=True):
    """Read original bound observations only; missing old evidence never reads this host."""
    if value is None:
        raise ValueError('unsupported: original CPU hardware/placement window evidence is missing')
    _exact(value, ('protocol', 'binding', 'native_request_sha256', 'managed', 'source', 'execution_phase_id', 'phase', 'operation', 'windows',
                   'before', 'after', 'state', 'reason',
                   *(['contract_sha256', 'preparation'] if 'contract_sha256' in value else [])), 'CPU window identity')
    if (phase not in ('baseline', 'screen') or operation not in ('unprofiled', 'profiled')
            or not isinstance(windows, list) or not 1 <= len(windows) <= 4096
            or any(not isinstance(item, dict) or set(item) != {'run_id', 'window_id'}
                   or any(not isinstance(item[key], str) or not item[key] for key in item) for item in windows)
            or len({(item['run_id'], item['window_id']) for item in windows}) != len(windows)
            or not isinstance(value['source'], dict) or not isinstance(source, dict)):
        raise ValueError('CPU window evidence lacks its actual source/window identity')
    if (value['protocol'] != 'training-cpu-window-identity-v1' or value['binding'] != binding
            or value['native_request_sha256'] != native_request_sha256 or value['managed'] != managed
            or {key: item for key, item in value['source'].items() if key != 'repo'} != {key: item for key, item in source.items() if key != 'repo'}
            or value['execution_phase_id'] != execution_phase_id
            or value['phase'] != phase or value['operation'] != operation or value['windows'] != windows):
        raise ValueError('CPU window evidence differs from its original source/binding/window')
    if 'contract_sha256' in value:
        _sha(value['contract_sha256'])
        _exact(value['preparation'], ('intent_ref', 'admission_ref'), 'Original CPU window preparation')
        for reference in value['preparation'].values():
            _exact(reference, ('path', 'sha256', 'bytes'), 'Original CPU preparation artifact')
            relative(reference['path'])
            _sha(reference['sha256'])
            if type(reference['bytes']) is not int or reference['bytes'] <= 0:
                raise ValueError('CPU preparation artifact requires its complete original byte count')
    if value['state'] == 'unsupported':
        for observed in (value['before'], value['after']):
            if isinstance(observed, dict) and observed.get('protocol') == CPU_IDENTITY_PROTOCOL:
                _read_cpu_execution_identity(observed)
        if not isinstance(value['reason'], str) or not value['reason']:
            raise ValueError('Unsupported CPU window evidence requires its actual missing-proof reason')
        if require_complete:
            raise ValueError('unsupported: original CPU hardware/placement scope is unavailable: ' + value['reason'])
        return None
    if value['state'] != 'complete' or value['reason'] is not None:
        raise ValueError('CPU window hardware/placement observation is unknown')
    original = _read_cpu_execution_identity(value['before'])
    if original != _read_cpu_execution_identity(value['after']):
        raise ValueError('CPU hardware/placement changed across the original window')
    before_proof = value['before']['raw'].get('allocation_provenance')
    after_proof = value['after']['raw'].get('allocation_provenance')
    if before_proof is not None and after_proof is not None and before_proof['subject'] != after_proof['subject']:
        raise ValueError('CPU window changed its actual calling subject/thread')
    if require_complete:
        qualified = validate_cpu_execution_identity(value['before'])
        if qualified != validate_cpu_execution_identity(value['after']):
            raise ValueError('unsupported: CPU allocation objects changed across the original window')
        return qualified
    return None


def _cpu_context_subject():
    import threading
    process = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': os.getpid(), 'tid': threading.get_native_id(), 'start_ticks': int(process[19]),
            'parent_pid': int(process[1]), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def cpu_context_observation(contract, role, binding):
    """Original producer observes itself; a caller cannot supply a subject/FD."""
    validate_cpu_execution_contract(contract)
    if role not in ('parent', 'supervisor', 'helper', 'budget', 'native', 'process', 'wrapper') or not isinstance(binding, dict):
        raise ValueError('CPU context requires its original owner role and binding')
    observation_bytes(binding)
    subject, snapshot, state, reason = _cpu_context_subject(), None, 'complete', None
    try:
        snapshot = cpu_execution_identity()
        proof = snapshot['raw'].get('allocation_provenance')
        if proof is not None:
            subject = {key: proof['subject'][key] for key in ('pid', 'tid', 'start_ticks', 'parent_pid', 'boot_id')}
        validate_cpu_execution_identity(snapshot)
    except (OSError, ValueError) as error:
        state, reason = 'unsupported', str(error)
    return {'protocol': 'training-cpu-context-v1', 'contract_sha256': contract['sha256'], 'role': role,
            'binding': decode_record(observation_bytes(binding)), 'subject': subject,
            'snapshot': snapshot, 'state': state, 'reason': reason}


def validate_cpu_context_observation(frame, *, contract, role, binding, expected_subject=None, require_complete=True):
    """Read saved owner facts; ordinary execution does not require allocation eligibility."""
    validate_cpu_execution_contract(contract)
    _exact(frame, ('protocol', 'contract_sha256', 'role', 'binding', 'subject', 'snapshot', 'state', 'reason'), 'CPU owner context')
    if (frame['protocol'] != 'training-cpu-context-v1' or frame['contract_sha256'] != contract['sha256']
            or frame['role'] != role or frame['binding'] != binding):
        raise ValueError('CPU owner context changed its original contract/role/binding')
    subject = frame['subject']
    if expected_subject is not None:
        expected_subject = dict(expected_subject)
        ticks = expected_subject.get('start_ticks')
        if isinstance(ticks, str):
            if not ticks.isdigit():
                raise ValueError('CPU expected process start ticks are not an original numeric identity')
            expected_subject['start_ticks'] = int(ticks)
    _exact(subject, ('pid', 'tid', 'start_ticks', 'parent_pid', 'boot_id'), 'CPU owner subject')
    if (any(type(subject[key]) is not int or subject[key] < (1 if key in ('pid', 'tid') else 0) for key in subject if key != 'boot_id')
            or not isinstance(subject['boot_id'], str) or not subject['boot_id']
            or expected_subject is not None and any(subject.get(key) != value for key, value in expected_subject.items())):
        raise ValueError('CPU owner context is not the original actual process/thread subject')
    if frame['snapshot'] is not None:
        _read_cpu_execution_identity(frame['snapshot'])
        proof = frame['snapshot']['raw'].get('allocation_provenance')
        if proof is not None and any(proof['subject'][key] != subject[key] for key in subject):
            raise ValueError('CPU owner subject differs from its original FD observation')
    if frame['state'] == 'unsupported':
        if not isinstance(frame['reason'], str) or not frame['reason']:
            raise ValueError('Unsupported CPU context requires its actual reason')
        if require_complete:
            raise ValueError('unsupported: CPU context allocation eligibility is unavailable: ' + frame['reason'])
        return None
    if frame['state'] != 'complete' or frame['reason'] is not None or frame['snapshot'] is None:
        raise ValueError('CPU context has unknown original observation status')
    if require_complete:
        return validate_cpu_execution_identity(frame['snapshot'])
    return None


def cpu_preparation_observation(value, ident, *, output=False):
    """One complete JSON observation envelope for original stage/baseline consumers."""
    if value is None:
        return None
    prefix = '' if output else 'state/ergora/training-preparations/' + ident
    paths = {'intent': 'cpu-contract-preparation-intent.json' if output else prefix + '.intent.json',
             'admission': 'cpu-contract-admission.json' if output else prefix + '.cpu-contract-admission.json'}
    result = {key: value[key] for key in ('contract', 'contract_sha256', 'preview_sha256', 'intent_sha256')}
    for name in ('intent', 'admission'):
        raw = value[name + '_raw']
        result[name + '_utf8'] = raw.decode('utf-8')
        result[name + '_ref'] = {'path': paths[name], 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    return result

