"""Portable evidence bytes and internal identities; no workflow replay or execution."""

from collections.abc import Callable
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import tempfile
import zipfile

from .task_envelopes import outcome_reference_state

MANIFEST_LIMIT = 1_048_576
BLOB_LIMIT = 16_777_216
PAYLOAD_LIMIT = 67_108_864
PACKET_LIMIT = 75_497_472
MEMBER_LIMIT = 4096
_SCHEMA = json.loads((Path(__file__).parent / 'data/schemas/task-handoff-v1.json').read_text(encoding='utf-8'))


def _canonical(value) -> bytes:
    # Match the frozen reference JSON identity; control/Skill identities differ.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _sha(value) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _references(index: dict) -> dict:
    contract = index['contract']
    spec = contract['spec']
    if (contract['spec_sha256'] != _sha(spec)
            or spec['request_sha256'] != _sha(spec['request'])
            or spec['profile_sha256'] != _sha(spec['profile'])
            or index['request_sha256'] != spec['request_sha256']
            or index['profile_sha256'] != spec['profile_sha256']
            or spec['request']['task_id'] != index['task_id']
            or contract['agent_bindings_sha256'] != _sha(contract['agent_bindings'])):
        raise ValueError('Handoff contract identity differs from the indexed frozen bytes')
    outcome = index['original_outcome']
    if (index['original_outcome_sha256'] != (_sha(outcome) if outcome is not None else None)
            or outcome is not None and (outcome.get('task_id') != index['task_id']
                                      or outcome.get('request_sha256') != index['request_sha256'])):
        raise ValueError('Handoff original outcome identity differs from its indexed task')
    identities, artifacts = {}, {}
    for job in index['jobs']:
        if job['job_id'] in identities:
            raise ValueError('Handoff contains duplicate original jobs')
        identities[job['job_id']] = job['job_sha256']
        receipt = job['receipt']
        receipt_bytes = _canonical(receipt)
        if (len(receipt_bytes) > 32_768 or job['receipt_sha256'] != hashlib.sha256(receipt_bytes).hexdigest()
                or receipt['job_id'] != job['job_id']
                or receipt['job_sha256'] != job['job_sha256'] or receipt['state'] != job['receipt_state']):
            raise ValueError('Handoff receipt identity differs from its indexed job')
        reference = outcome_reference_state(outcome, job)
        if job['outcome_reference_state'] != reference:
            raise ValueError('Handoff invents an original outcome receipt reference')
        names = set()
        for artifact in receipt['artifacts']:
            relative = artifact['path']
            path = PurePosixPath(relative)
            if (path.is_absolute() or PureWindowsPath(relative).drive or path.as_posix() != relative
                    or any(part in ('', '.', '..') for part in relative.split('/')) or '\\' in relative or '\0' in relative):
                raise ValueError('Handoff contains an unsafe original artifact path')
            if artifact['name'] in names:
                raise ValueError('Handoff contains duplicate receipt artifact names')
            names.add(artifact['name'])
            artifacts.setdefault(artifact['sha256'], artifact)
        checks = set()
        for check in receipt.get('checks', []):
            if check['id'] in checks or check['artifact'] not in names:
                raise ValueError('Handoff check has a duplicate ID or missing artifact')
            checks.add(check['id'])
    history_jobs = [{'job_id': key, 'job_sha256': value} for key, value in sorted(identities.items())]
    if index['history_jobs_sha256'] != _sha(history_jobs):
        raise ValueError('Handoff original job set differs from its indexed history digest')
    if len(artifacts) + 1 > MEMBER_LIMIT:
        raise ValueError('Handoff exceeds its member limit')
    return artifacts


def create(index: dict, read_artifact: Callable[[dict], bytes], destination: Path) -> dict:
    """Collect an internally verified index, then publish a new complete packet."""
    if index['published_evidence'] != 'verified' or index['unresolved_jobs'] or index['unexpected_jobs']:
        raise ValueError('Handoff requires complete verified original materials')
    artifacts = _references(index)
    destination = destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Choose a new handoff file; existing destinations are not replaced')
    descriptor, name = tempfile.mkstemp(prefix='.ergora-handoff-', dir=destination.parent)
    temporary = Path(name)
    try:
        blobs, total = {}, 0
        with os.fdopen(descriptor, 'w+b') as stream:
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
                for digest, artifact in sorted(artifacts.items()):
                    raw = read_artifact(artifact)
                    if len(raw) > BLOB_LIMIT or hashlib.sha256(raw).hexdigest() != digest:
                        raise ValueError('Handoff artifact bytes exceed the limit or differ from the indexed receipt')
                    total += len(raw)
                    if total > PAYLOAD_LIMIT:
                        raise ValueError('Handoff exceeds its 64 MiB payload limit')
                    archive.writestr(zipfile.ZipInfo('blobs/' + digest), raw)
                    blobs[digest] = {'bytes': len(raw)}
                manifest = {'schema_version': 1, 'format': 'ergora-task-handoff',
                            'index': index, 'index_sha256': _sha(index), 'blobs': blobs}
                encoded = _canonical(manifest)
                if len(encoded) > MANIFEST_LIMIT:
                    raise ValueError('Handoff manifest exceeds 1 MiB')
                archive.writestr(zipfile.ZipInfo('manifest.json'), encoded)
            if stream.tell() > PACKET_LIMIT:
                raise ValueError('Handoff packet exceeds 72 MiB')
            stream.flush()
            os.fsync(stream.fileno())
            stream.seek(0)
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        os.link(temporary, destination)
        return {'schema_version': 1, 'status': 'exported', 'path': str(destination), 'sha256': digest,
                'manifest_sha256': hashlib.sha256(encoded).hexdigest(), 'artifacts': len(blobs),
                'artifact_bytes': total, 'project': index['project'], 'task_id': index['task_id'],
                'run_id': index['run_id'], 'execution_success': None, 'origin_authenticated': False}
    finally:
        temporary.unlink(missing_ok=True)


def verify(path: Path, *, sha256: str | None = None) -> dict:
    """Check the selected packet without extraction, execution, state or services."""
    from . import contracts

    if sha256 is not None and not re.fullmatch('[0-9a-f]{64}', sha256):
        raise ValueError('Expected handoff SHA256 must be 64 lowercase hex characters')
    path = path.expanduser()
    details = path.lstat()
    if (not stat.S_ISREG(details.st_mode) or getattr(details, 'st_file_attributes', 0) & 0x400):
        raise ValueError('Handoff packet must be a regular file, without links or reparse points')
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Handoff packet must be a regular file')
        raw = stream.read(PACKET_LIMIT + 1)
    if len(raw) > PACKET_LIMIT:
        raise ValueError('Handoff packet exceeds 72 MiB')
    digest = hashlib.sha256(raw).hexdigest()
    if sha256 is not None and sha256 != digest:
        raise ValueError('Handoff packet differs from the external expected SHA256')

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Handoff manifest contains duplicate JSON keys')
            result[key] = value
        return result

    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            if len(entries) > MEMBER_LIMIT or len({entry.filename for entry in entries}) != len(entries):
                raise ValueError('Handoff has too many or duplicate ZIP members')
            for entry in entries:
                mode = stat.S_IFMT(entry.external_attr >> 16)
                if (entry.filename != entry.orig_filename or entry.is_dir() or mode not in (0, stat.S_IFREG)
                        or entry.flag_bits & 1 or entry.compress_type != zipfile.ZIP_STORED
                        or entry.file_size > (MANIFEST_LIMIT if entry.filename == 'manifest.json' else BLOB_LIMIT)):
                    raise ValueError('Handoff has an unsupported or oversized ZIP member')
            encoded = archive.read('manifest.json')
            if len(encoded) > MANIFEST_LIMIT:
                raise ValueError('Handoff manifest exceeds 1 MiB')
            manifest = json.loads(encoded.decode('utf-8'), object_pairs_hook=unique_object)
            contracts.validate(manifest, _SCHEMA, 'Handoff manifest')
            index = manifest['index']
            artifacts = _references(index)
            if manifest['index_sha256'] != _sha(index) or set(manifest['blobs']) != set(artifacts):
                raise ValueError('Handoff manifest differs from its indexed evidence references')
            expected = {'manifest.json', *('blobs/' + key for key in artifacts)}
            if {entry.filename for entry in entries} != expected:
                raise ValueError('Handoff ZIP has missing or unexpected members')
            total = sum(value['bytes'] for value in manifest['blobs'].values())
            if total > PAYLOAD_LIMIT:
                raise ValueError('Handoff exceeds its 64 MiB payload limit')
            for key, value in manifest['blobs'].items():
                entry = archive.getinfo('blobs/' + key)
                if entry.file_size != value['bytes']:
                    raise ValueError('Handoff artifact size differs from its manifest')
                if hashlib.sha256(archive.read(entry)).hexdigest() != key:
                    raise ValueError('Handoff artifact bytes differ from the indexed receipt')
    except (zipfile.BadZipFile, KeyError, UnicodeError, RecursionError) as error:
        raise ValueError('Invalid handoff packet: ' + str(error)) from error
    outcome = index['original_outcome']
    return {'schema_version': 1, 'status': 'verified', 'sha256': digest,
            'manifest_sha256': hashlib.sha256(encoded).hexdigest(), 'artifacts': len(artifacts),
            'artifact_bytes': total, 'project': index['project'], 'task_id': index['task_id'],
            'run_id': index['run_id'], 'candidate_sha': outcome.get('candidate_sha') if outcome else None,
            'original_outcome': outcome, 'execution_success': None, 'origin_authenticated': False,
            'external_sha256': 'matches' if sha256 is not None else 'not_recorded',
            'verification_scope': 'packet_bytes_and_declared_internal_identities'}
