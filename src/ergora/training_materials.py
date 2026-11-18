"""Frozen raw configuration inputs, shared without application state or native SDKs."""

import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

from .asset_trees import is_link


LIMIT = 1_048_576


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(label + ' has unsupported or missing fields')


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
    return value


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
