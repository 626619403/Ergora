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


def execution_plan(manifest, runner):
    """Validate the one current operation without importing source or reading history."""
    execution = manifest.get('execution')
    if not isinstance(execution, dict):
        raise ValueError('Current execution requires an explicit operation')
    if execution.get('operation') == 'full-verify':
        _exact(execution, ('operation',), 'Full execution')
        return execution
    _exact(execution, ('operation', 'plan'), 'Screen execution')
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
