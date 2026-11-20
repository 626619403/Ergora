"""Explicit correction proposals and once-only edits of one project document.

The original retrospective/composition readers own frozen model material. This
owner adds the local document lifecycle; a preview never grants file authority.
"""

from contextlib import ExitStack, contextmanager
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import uuid

from ergora._paths import DATA_ROOT
from ergora.agents import native_sources
from ergora.configuration import validation as contracts
from ergora.definitions import bundles, workflows
from ergora.improvement import retrospectives
from ergora.storage.assets import is_link, publish_directory
from ergora.storage.git import GitMaterials, text_blob
from ergora.storage.state import State, file_lock, now


_SCHEMA = json.loads((DATA_ROOT / 'schemas/document-correction-proposal-v1.json').read_bytes())
MAX_MATERIAL_BYTES = 1_048_576
_RECORD_LIMIT = 16_777_216
_SHA = {'type': 'string', 'pattern': '^[a-f0-9]{64}$'}
_TEXT = {'type': 'string', 'minLength': 1, 'maxLength': 65536, 'pattern': r'\S'}
_IDENTITY = {'type': 'array', 'minItems': 2, 'maxItems': 2, 'items': {'type': 'integer', 'minimum': 0}}
_AUTHORITY = {'type': 'object', 'additionalProperties': False,
              'required': ['root', 'root_identity', 'database_identity'],
              'properties': {'root': _TEXT, 'root_identity': _IDENTITY, 'database_identity': _IDENTITY}}
_REQUEST = {'type': 'object', 'additionalProperties': False, 'properties': {
    'schema_version': {'const': 1}, 'format': {'const': 'ergora-document-correction-request'},
    'project': _TEXT, 'revision': {'type': 'integer', 'minimum': 1},
    'proposal_id': {'type': 'string', 'pattern': '^[a-f0-9]{32}$'},
    'authority': _AUTHORITY, 'baseline': {'type': 'object'},
    'correction': {'type': 'object'}, 'parent': {'type': ['object', 'null']},
    'max_material_bytes': {'type': 'integer', 'minimum': 1, 'maximum': MAX_MATERIAL_BYTES},
    'proposal_schema': {'const': _SCHEMA}, 'request_sha256': _SHA,
}}
_REQUEST['required'] = list(_REQUEST['properties'])


class NativePreparationConflict(ValueError):
    """An issued native source cannot be recreated with new input or a new clock."""


def _hash(value) -> str:
    return hashlib.sha256(retrospectives._encoded(value)).hexdigest()


def _identity(details) -> list[int]:
    return [details.st_dev, details.st_ino]


def _authority(root: Path) -> dict:
    root = root.resolve(strict=True)
    database = root / 'ergora.sqlite3'
    if is_link(root) or is_link(database) or not stat.S_ISREG(database.stat().st_mode):
        raise ValueError('Document control authority requires its original directory and database')
    return {'root': str(root), 'root_identity': _identity(root.stat()),
            'database_identity': _identity(database.stat())}


def availability() -> dict:
    supported = sys.platform == 'linux' and all(hasattr(os, name) for name in ('O_DIRECTORY', 'O_NOFOLLOW'))
    return {'available': supported, 'reason': None if supported else
            'Document apply requires local Linux/WSL file replacement and directory synchronization'}


def _sync_directory(path: Path) -> None:
    if os.name != 'nt':
        for directory in (path, *path.parents):
            descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)


def _publish(destination: Path, value: dict) -> None:
    """Durably publish one immutable lifecycle record; never repair an old one."""
    raw = retrospectives._encoded({'record': value, 'sha256': _hash(value)})
    if len(raw) > _RECORD_LIMIT:
        raise ValueError('Complete document record exceeds 16 MiB')
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staged = Path(tempfile.mkdtemp(prefix='.document-record-', dir=destination.parent))
    try:
        with (staged / 'record.json').open('xb') as stream:
            os.chmod(stream.name, 0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _sync_directory(staged)
        publish_directory(staged, destination)
        _sync_directory(destination.parent)
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def _record(directory: Path, *, confirm_durable: bool = False) -> dict:
    path = directory / 'record.json'
    if is_link(directory) or is_link(path) or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('Document history requires original ordinary records')
    if confirm_durable:
        raw = native_sources.artifact(directory, 'record.json', _RECORD_LIMIT, confirm_durable=True)
    else:
        with path.open('rb') as stream:
            raw = stream.read(_RECORD_LIMIT + 1)
    if len(raw) > _RECORD_LIMIT:
        raise ValueError('Complete document record exceeds 16 MiB')
    value = bundles.parse_json(raw.decode('utf-8'), 'Document record', finite=True, bounded=True)
    contracts.validate(value, {'type': 'object', 'additionalProperties': False, 'required': ['record', 'sha256'],
        'properties': {'record': {'type': 'object'}, 'sha256': _SHA}}, 'Document record')
    if value['sha256'] != _hash(value['record']):
        raise ValueError('Document history differs from its immutable record')
    return value['record']


def read_preview(path: Path) -> dict:
    with path.open('rb') as stream:
        raw = stream.read(_RECORD_LIMIT + 1)
    if len(raw) > _RECORD_LIMIT:
        raise ValueError('Complete document preview exceeds 16 MiB')
    value = bundles.parse_json(raw.decode('utf-8'), 'Document preview', finite=True, bounded=True)
    _validate_preview(value)
    return value


def get_preview(state: State, project_id: str, proposal_id: str) -> dict:
    """Read an existing original candidate; never prepare or recreate its history."""
    state.project(project_id)
    slot = _slot(state.root, project_id, proposal_id)
    task = _record(slot)
    _original(state, task)
    with file_lock(slot / '.lock'):
        value = _record(slot / 'candidate')
        _actionable(state, project_id, value)
    return value


def inspect_proposal(state: State, project_id: str, proposal_id: str, *, include_preview: bool = False) -> dict:
    """Read small original-slot references; full immutable text is explicit."""
    project = state.project(project_id)
    slot = _slot(state.root, project_id, proposal_id)
    base = {'project': project_id, 'proposal_id': proposal_id, 'preview': None,
            'candidate_digest': None, 'reason': None, 'can_apply': False, 'apply': availability()}
    with file_lock(slot / '.lock'):
        reference = _record(slot / 'request-reference')
        if (reference['project'] != project_id or reference['proposal_id'] != proposal_id
                or reference['authority'] != _authority(state.root)):
            raise ValueError('Document reference belongs to another original control authority')
        original = slot / 'record.json'
        if is_link(original) or not stat.S_ISREG(original.stat().st_mode):
            raise ValueError('Original document request is unavailable; never recreate it')
        if reference['source_kind'] == 'native-session':
            if not (slot / 'native-outcome').exists():
                return {**base, 'status': 'unknown' if (slot / 'native-completion').exists() else 'prepared',
                        'reason': 'Original native suggestion completion is unconfirmed'}
            outcome = _record(slot / 'native-outcome')
            completion = _record(slot / 'native-completion')
            if outcome.get('completion_sha256') != _hash(completion):
                raise ValueError('Native suggestion outcome differs from its original completion')
            if outcome['status'] != 'ready':
                return {**base, 'status': outcome['status'], 'reason': outcome.get('reason')}
            if not (slot / 'native-eligibility').exists():
                return {**base, 'status': 'unknown',
                        'reason': 'Original native final eligibility is unconfirmed; no retry or application'}
        if not (slot / 'candidate-reference').exists():
            return {**base, 'status': 'prepared', 'reason': 'No completed immutable candidate reference'}
        candidate = _record(slot / 'candidate-reference')
        if (candidate['request_sha256'] != reference['request_sha256']
                or candidate['project'] != project_id or candidate['proposal_id'] != proposal_id):
            raise ValueError('Candidate reference differs from its original request')
        try:
            observed = _phase(slot, candidate)
        except OSError as error:
            if candidate['source'].get('kind') != 'native-session':
                raise
            return {**base, 'status': 'unknown',
                    'reason': 'Original native suggestion evidence lacks durable confirmation: ' + str(error)}
        evidence_present = (candidate['source'].get('kind') != 'native-session'
                            or native_sources.records_present(state, candidate['source']['run_id']))
        candidate_path = slot / 'candidate' / 'record.json'
        candidate_present = not is_link(candidate_path) and candidate_path.is_file()
        # This is an action affordance, not a cached source-current verdict.
        # Exact apply always reloads full source/preview and rechecks live data.
        result = {**base, **observed, 'candidate_digest': candidate['candidate_digest'],
            'scope_sha256': candidate['scope_sha256'], 'base_sha256': candidate['base_sha256'],
            'revision': reference['revision'], 'source_validation': 'rechecked by full preview and exact apply',
            'reason': None if evidence_present and candidate_present else 'Original candidate/native records are unavailable',
            'can_apply': observed['status'] == 'ready' and availability()['available']
                and project['revision'] == reference['revision'] and evidence_present and candidate_present}
    if include_preview:
        result['preview'] = get_preview(state, project_id, proposal_id)
    return result


def _request_reference(slot: Path, task: dict) -> None:
    """Immutable display reference, never a cached live authority decision."""
    _publish(slot / 'request-reference', {'project': task['project'], 'proposal_id': task['proposal_id'],
        'authority': task['authority'], 'request_sha256': task['request_sha256'], 'revision': task['revision'],
        'source_kind': 'native-session' if task['correction'].get('native') else 'composition'})



def _validate_request(task: dict) -> None:
    contracts.validate(task, _REQUEST, 'Document correction request')
    if task['request_sha256'] != _hash({key: value for key, value in task.items() if key != 'request_sha256'}):
        raise ValueError('Document request differs from its complete original bytes')


def _validate_preview(preview: dict) -> None:
    contracts.validate(preview, {'type': 'object', 'required': ['format', 'request', 'candidate_digest'],
        'properties': {'format': {'const': 'ergora-document-correction-preview'},
                       'request': _REQUEST, 'candidate_digest': _SHA}}, 'Document preview')
    _validate_request(preview['request'])
    if preview['candidate_digest'] != _hash({key: value for key, value in preview.items() if key != 'candidate_digest'}):
        raise ValueError('Document preview changed; inspect a fresh exact candidate')


def _slot(root: Path, project: str, proposal: str) -> Path:
    contracts.validate(project, {'type': 'string', 'pattern': '^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$'}, 'Project ID')
    contracts.validate(proposal, _REQUEST['properties']['proposal_id'], 'Document proposal ID')
    return root / 'retrospectives' / 'documents' / project / proposal


def _original(state: State, task: dict) -> Path:
    _validate_request(task)
    if _authority(state.root) != task['authority']:
        raise ValueError('Document control authority changed; observe the original home and proposal: '
                         + task['authority']['root'] + ' / ' + task['proposal_id'])
    slot = _slot(state.root, task['project'], task['proposal_id'])
    if _record(slot) != task:
        raise ValueError('Original document proposal slot differs; missing history cannot be recreated')
    return slot


@contextmanager
def _parent_fd(repo: Path, path: Path):
    descriptor = os.open(repo, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


def _file(repo: Path, name: str, limit: int) -> dict:
    relative = bundles.relative_path(name, 'Project document')
    if '.git' in relative.parts:
        raise ValueError('Document scope cannot enter .git')
    if os.name == 'nt':
        path = repo
        for part in relative.parts:
            path /= part
            if is_link(path):
                raise ValueError('Document paths cannot contain links or reparse points')
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError('Document targets and rules must be ordinary files')
        with path.open('rb') as stream:
            details = os.fstat(stream.fileno())
            raw = stream.read(limit + 1)
    else:
        with _parent_fd(repo, relative) as parent:
            descriptor = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(descriptor, 'rb') as stream:
                details = os.fstat(stream.fileno())
                if not stat.S_ISREG(details.st_mode):
                    raise ValueError('Document targets and rules must be ordinary files')
                raw = stream.read(limit + 1)
    if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
        raise ValueError('Document targets and rules must be ordinary files without hard links')
    if len(raw) > limit:
        raise ValueError('Complete correction/document material exceeds its byte limit')
    return {'path': name, **text_blob(raw), 'mode': stat.S_IMODE(details.st_mode), 'identity': _identity(details)}


def _snapshot(project: dict, name: str, limit: int) -> dict:
    relative = bundles.relative_path(name, 'Project document')
    if relative.suffix.lower() != '.md':
        raise ValueError('Select one existing Markdown project document')
    repo = Path(project['repo'])
    if is_link(repo) or repo.resolve(strict=True) != repo:
        raise ValueError('Project repository identity or canonical path changed')
    reader = GitMaterials(repo)
    head = reader.read('rev-parse', '--verify', 'HEAD^{commit}', limit=256).decode('ascii').strip()
    common = Path(reader.read('rev-parse', '--path-format=absolute', '--git-common-dir', limit=4096).decode().strip()).resolve(strict=True)
    target = _file(repo, name, limit)
    remaining = limit - len(target['text'].encode('utf-8'))
    rules = []
    for parent in [Path(), *reversed(relative.parent.parents), relative.parent]:
        rule = (parent / 'AGENTS.md').as_posix()
        if rule == name or any(item['path'] == rule for item in rules):
            continue
        try:
            item = _file(repo, rule, remaining)
        except FileNotFoundError:
            item = {'path': rule, 'missing': True}
        else:
            remaining -= len(item['text'].encode('utf-8'))
        rules.append(item)
    return {'repo': str(repo), 'repo_identity': _identity(repo.stat()), 'head': head,
            'git_common_dir': str(common), 'git_common_identity': _identity(common.stat()),
            'file': target, 'rules': rules}


def _consumption(slot: Path, preview: dict) -> dict:
    value = _record(slot / 'consumption')
    contracts.validate(value, {'type': 'object', 'additionalProperties': False,
        'required': ['candidate_digest', 'decision_sha256'], 'properties': {
            'candidate_digest': _SHA, 'decision_sha256': {'anyOf': [_SHA, {'type': 'null'}]}}},
        'Original document consumption state')
    if value['candidate_digest'] != preview['candidate_digest']:
        raise ValueError('Document consumption state differs from its original candidate')
    return value


def _consume(slot: Path, preview: dict, decision: dict) -> None:
    """Reserve the original slot durably before publishing any issued decision."""
    if _consumption(slot, preview)['decision_sha256'] is not None:
        raise ValueError('Original document candidate is already consumed')
    value = {'candidate_digest': preview['candidate_digest'], 'decision_sha256': _hash(decision)}
    folder = slot / 'consumption'
    descriptor, temporary = tempfile.mkstemp(prefix='.consume-', dir=folder)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(retrospectives._encoded({'record': value, 'sha256': _hash(value)}))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, folder / 'record.json')
        _sync_directory(folder)
        if _record(folder) != value:
            raise ValueError('Original consumption state changed after durable reservation')
    finally:
        Path(temporary).unlink(missing_ok=True)


def _phase(slot: Path, preview: dict) -> dict:
    _native_ready(slot, preview)
    consumption = _consumption(slot, preview)
    decision = _record(slot / 'decision') if (slot / 'decision').exists() else None
    attempt = _record(slot / 'attempt') if (slot / 'attempt').exists() else None
    receipt = _record(slot / 'receipt') if (slot / 'receipt').exists() else None
    if consumption['decision_sha256'] is None:
        if decision or attempt or receipt:
            raise ValueError('Issued document history conflicts with its unconsumed footprint')
        return {'status': 'ready', 'consumption': consumption, 'decision': None, 'attempt': None, 'receipt': None}
    if decision is None:
        return {'status': 'unknown', 'consumption': consumption, 'decision': None, 'attempt': attempt,
                'receipt': receipt, 'history_incomplete': 'Original reserved decision is missing; never redispatch'}
    if _hash(decision) != consumption['decision_sha256']:
        raise ValueError('Document decision differs from its original durable consumption state')
    if decision and decision.get('candidate_digest') != preview['candidate_digest']:
        raise ValueError('Document decision differs from the sealed candidate')
    if attempt and (not decision or attempt.get('decision_sha256') != _hash(decision)):
        raise ValueError('Document attempt has no matching original decision')
    if receipt and (not attempt or receipt.get('attempt_sha256') != _hash(attempt)):
        raise ValueError('Document receipt has no matching original attempt')
    status = ('applied' if receipt else 'withdrawn' if decision and decision['action'] == 'withdraw'
              else 'unknown' if decision or attempt else 'ready')
    return {'status': status, 'consumption': consumption, 'decision': decision, 'attempt': attempt, 'receipt': receipt}


def _actionable(state: State, project: str, preview: dict) -> Path:
    _validate_preview(preview)
    task = preview['request']
    if project != task['project']:
        raise ValueError('Document preview belongs to a different project')
    slot = _original(state, task)
    if _record(slot / 'candidate') != preview:
        raise ValueError('Document preview differs from its original sealed candidate')
    _consumption(slot, preview)
    _native_ready(slot, preview)
    return slot


def _native_ready(slot: Path, preview: dict) -> None:
    if preview['source'].get('kind') == 'native-session':
        completion = _record(slot / 'native-completion')
        outcome = _record(slot / 'native-outcome')
        # A published name alone is not a durable completion witness. Confirm
        # the same existing bytes/object/chain; never replace or recreate it.
        eligibility = _record(slot / 'native-eligibility', confirm_durable=True)
        binding = _record(slot / 'input')
        if (outcome.get('completion_sha256') != _hash(completion)
                or completion.get('input_sha256') != _hash(_record(slot / 'input'))
                or outcome.get('status') != 'ready'
                or outcome.get('candidate_digest') != preview['candidate_digest']
                or eligibility.get('completion_sha256') != _hash(completion)
                or eligibility.get('outcome_sha256') != _hash(outcome)
                or eligibility.get('input_sha256') != _hash(binding)
                or eligibility.get('candidate_digest') != preview['candidate_digest']
                or eligibility.get('document_request_sha256') != binding['request_sha256']
                or eligibility.get('native_request_sha256') != binding['input_digest']
                or eligibility.get('native_prompt_sha256') != binding['prompt_sha256']
                or eligibility.get('native_result_sha256') != preview['source']['native_result_sha256']
                or type(eligibility.get('remaining_seconds')) not in (int, float)
                or eligibility['remaining_seconds'] <= 0):
            raise ValueError('Original native suggestion completion is not actionable')


@contextmanager
def _parent_lock(reference: dict | None):
    with ExitStack() as locks:
        if reference is not None:
            try:
                root = Path(reference['authority']['root'])
                if _authority(root) == reference['authority']:
                    slot = _slot(root, reference['project'], reference['proposal_id'])
                    _record(slot)
                    locks.enter_context(file_lock(slot / '.lock'))
            except (FileNotFoundError, PermissionError):
                pass
        yield


def _parent_observation(reference: dict) -> dict:
    observed = {key: reference[key] for key in ('authority', 'project', 'proposal_id', 'candidate_digest')}
    observed.update(outcome='unknown', observation_sha256=None)
    try:
        root = Path(reference['authority']['root'])
        if _authority(root) != reference['authority']:
            return observed
        slot = _slot(root, reference['project'], reference['proposal_id'])
        task, value = _record(slot), _record(slot / 'candidate')
        _validate_preview(value)
        if value['request'] != task or value['candidate_digest'] != reference['candidate_digest']:
            raise ValueError('Superseded document record differs from its original candidate')
        phase = _phase(slot, value)
        observed.update(outcome=phase['status'], observation_sha256=_hash(phase))
    except (FileNotFoundError, PermissionError):
        pass
    return observed


def _parent_reference(preview: dict | None, project: str, path: str, baseline: dict) -> dict | None:
    if preview is None:
        return None
    _validate_preview(preview)
    task = preview['request']
    if (task['project'] != project or task['baseline']['file']['path'] != path
            or any(task['baseline'][key] != baseline[key] for key in ('repo', 'repo_identity'))):
        raise ValueError('Superseded document proposal belongs to another project or path')
    reference = {'authority': task['authority'], 'project': project, 'proposal_id': task['proposal_id'],
                 'candidate_digest': preview['candidate_digest']}
    with _parent_lock(reference):
        return _parent_observation(reference)


def prepare(state: State, project_id: str, path: str, correction: bytes, *, source: str, revision: int,
            manifest: Path, instance: str, destination: Path, max_prompt_bytes: int,
            max_material_bytes: int = MAX_MATERIAL_BYTES, parent_preview: dict | None = None) -> dict:
    """Issue an original authority-owned slot and freeze one complete readonly input."""
    contracts.validate(source, _TEXT, 'Correction source description')
    contracts.validate(revision, _REQUEST['properties']['revision'], 'Project revision')
    contracts.validate(max_material_bytes, _REQUEST['properties']['max_material_bytes'], 'Material byte limit')
    text = text_blob(correction)
    if not text['text'].strip() or len(correction) >= max_material_bytes:
        raise ValueError('Correction must be complete nonempty UTF-8 within the material byte limit')
    project = state.project(project_id)
    if project['revision'] != revision:
        raise ValueError('Project revision changed; prepare a fresh document correction')
    baseline = _snapshot(project, path, max_material_bytes - len(correction))
    task = {'schema_version': 1, 'format': 'ergora-document-correction-request',
            'project': project_id, 'revision': revision, 'proposal_id': uuid.uuid4().hex,
            'authority': _authority(state.root), 'baseline': baseline,
            'correction': {**text, 'source': source, 'origin': 'operator-submitted'},
            'parent': _parent_reference(parent_preview, project_id, path, baseline),
            'max_material_bytes': max_material_bytes, 'proposal_schema': _SCHEMA}
    task['request_sha256'] = _hash(task)
    slot = _slot(state.root, project_id, task['proposal_id'])
    _publish(slot, task)
    prepared = workflows.prepare_input_from_manifest(manifest, instance, retrospectives._encoded(task), destination, max_prompt_bytes)
    frozen = workflows.inspect_input(Path(prepared['path']), material=True)
    leaf = next(item for item in frozen['composition']['instances'] if item['path'] == instance)
    if leaf['permissions']['write'] or leaf['permissions']['network'] or leaf['permissions']['shell']:
        raise ValueError('Document proposer must be a readonly leaf without shell or network')
    _publish(slot / 'input', {'input_digest': prepared['digest'], 'request_sha256': task['request_sha256']})
    _request_reference(slot, task)
    return {**prepared, 'proposal_id': task['proposal_id'], 'authority': task['authority'], 'apply': availability()}


def prepare_native(state: State, project_id: str, run_id: str, session: dict, submitted: dict,
                   revision: int, clock: dict, *, path: str = 'AGENTS.md',
                   max_material_bytes: int = MAX_MATERIAL_BYTES) -> dict:
    """Freeze D once before native P/N, without importing the native executor."""
    native_sources.session_id(run_id, 'Native run ID')
    contracts.validate(max_material_bytes, _REQUEST['properties']['max_material_bytes'], 'Material byte limit')
    raw = submitted['prompt'].encode('utf-8')
    text = text_blob(raw)
    if not text['text'].strip() or len(raw) >= max_material_bytes:
        raise ValueError('Complete correction exceeds the native suggestion material allowance')
    authority = _authority(state.root)
    proposal_id = uuid.uuid5(uuid.NAMESPACE_URL, 'ergora:native-document-correction:' +
        _hash({'authority': authority, 'project': project_id, 'run_id': run_id})).hex
    source = {'session_id': session['id'], 'run_id': run_id, 'parent_run_id': session['parent_run'],
        'ordinal': session['ordinal'], 'intent_id': submitted['intent_id'], 'project_revision': revision,
        'raw_prompt_sha256': hashlib.sha256(raw).hexdigest(),
        'submitted_sha256': native_sources.sha(submitted), 'clock': clock}
    slot = _slot(state.root, project_id, proposal_id)
    if slot.exists():
        task = _record(slot)
        _original(state, task)
        if (task['correction'].get('native') != source or task['correction']['text'] != text['text']
                or task['baseline']['file']['path'] != path or task['revision'] != revision):
            raise NativePreparationConflict('Native correction intent already has original frozen input/clock; observe it')
        reference = _record(slot / 'request-reference')
        if reference['request_sha256'] != task['request_sha256']:
            raise NativePreparationConflict('Original native request reference changed')
        return task
    project = state.project(project_id)
    if project['revision'] != revision:
        raise NativePreparationConflict('Native project revision changed before correction preparation')
    baseline = _snapshot(project, path, max_material_bytes - len(raw))
    parent = None
    if session['parent_run'] is not None:
        previous = native_sources.request(state, project_id, session['parent_run'])['request']
        previous_id = previous.get('correction_suggestion', {}).get('proposal_id')
        if previous_id is not None:
            previous_slot = _slot(state.root, project_id, previous_id)
            if (previous_slot / 'candidate').exists():
                parent = _parent_reference(get_preview(state, project_id, previous_id), project_id, path, baseline)
            elif (previous_slot / 'native-outcome').exists():
                if _record(previous_slot / 'native-outcome')['status'] == 'ready':
                    raise ValueError('Prior native correction candidate history is unavailable; observe it before superseding')
    task = {'schema_version': 1, 'format': 'ergora-document-correction-request',
        'project': project_id, 'revision': revision, 'proposal_id': proposal_id, 'authority': authority,
        'baseline': baseline, 'correction': {**text, 'source': 'Original Ergora native operator submission',
            'origin': 'native-session-operator-submitted', 'native': source},
        'parent': parent, 'max_material_bytes': max_material_bytes, 'proposal_schema': _SCHEMA}
    task['request_sha256'] = _hash(task)
    _publish(slot, task)
    _request_reference(slot, task)
    return task


def native_prompt(task: dict) -> str:
    """Add bounded proposal material, never an apply capability or consent claim."""
    _validate_request(task)
    digest = task['request_sha256']
    return ('Project correction suggestions: finish the requested task normally. Consider only the latest '
        'operator submission as correction evidence, not quoted agent/reviewer output. Task-only guidance '
        'needs no persistent rule. For a reusable project lesson, propose one complete replacement for '
        'the frozen target; do not apply learned rules or claim operator consent. No learning apply tool '
        'is provided. Ordinary task-authorized document development remains separate.\n'
        'ERGORA_DOCUMENT_REQUEST\n' + retrospectives._encoded(task).decode('utf-8') +
        '\nEND_ERGORA_DOCUMENT_REQUEST\n'
        'Optionally append exactly one JSON proposal using the supplied proposal_schema, or candidate:null, '
        'between these exact lines; keep the ordinary native reply intact:\n'
        'ERGORA_DOCUMENT_PROPOSAL ' + digest + '\n'
        '<one JSON object; request_sha256 must equal the frozen document request SHA>\n'
        'END_ERGORA_DOCUMENT_PROPOSAL ' + digest)


def _native_input(state: State, task: dict, run_id: str) -> dict:
    source = native_sources.request(state, task['project'], run_id)
    original = source['request']
    native = task['correction']['native']
    expected = {'session_id': original['session']['id'], 'run_id': run_id,
        'parent_run_id': original['session']['parent_run'], 'ordinal': original['session']['ordinal'],
        'intent_id': original['submitted']['intent_id'], 'project_revision': source['document']['project_revision'],
        'raw_prompt_sha256': hashlib.sha256(original['submitted']['prompt'].encode('utf-8')).hexdigest(),
        'submitted_sha256': native_sources.sha(original['submitted']), 'clock': original['clock']}
    ref = original.get('correction_suggestion', {})
    if (native != expected or task['correction']['text'] != original['submitted']['prompt']
            or ref.get('proposal_id') != task['proposal_id']
            or ref.get('request_sha256') != task['request_sha256']
            or not original['prompt'].endswith('\n\n' + native_prompt(task))):
        raise ValueError('Native correction source/material differs from original submission and effective prompt')
    return {'kind': 'native-session', 'run_id': run_id, 'input_digest': source['request_sha256'],
            'prompt_sha256': source['prompt_sha256'], 'request_sha256': task['request_sha256']}


def bind_native(state: State, project_id: str, proposal_id: str, run_id: str) -> None:
    """Bind late native N/P outside frozen D before the original native attempt."""
    slot = _slot(state.root, project_id, proposal_id)
    task = _record(slot)
    _original(state, task)
    value = _native_input(state, task, run_id)
    if (slot / 'input').exists():
        if _record(slot / 'input') != value:
            raise NativePreparationConflict('Native suggestion has another original input binding')
    else:
        _publish(slot / 'input', value)


def _native_segment(raw: bytes, digest: str) -> tuple[dict | None, str | None]:
    opening = ('ERGORA_DOCUMENT_PROPOSAL ' + digest).encode('ascii')
    lines = raw.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.rstrip(b'\r\n') == opening]
    any_starts = [line for line in lines if line.startswith(b'ERGORA_DOCUMENT_PROPOSAL ')]
    if not any_starts:
        return None, None
    if len(starts) != 1 or len(any_starts) != 1:
        raise ValueError('Native correction has duplicate or mismatched proposal segments')
    tail = b''.join(lines[starts[0] + 1:])
    # The original complete native reader owns the 8 MiB result bound. The
    # existing proposal schema and request own text/replacement limits.
    text = tail.decode('utf-8').lstrip()
    _, end = json.JSONDecoder().raw_decode(text)
    closing = 'END_ERGORA_DOCUMENT_PROPOSAL ' + digest
    remainder = text[end:].lstrip()
    if remainder.strip() != closing:
        raise ValueError('Native correction segment has no exact closing identity')
    proposal_text = text[:end]
    proposal = bundles.parse_json(proposal_text, 'Native document proposal', finite=True, bounded=True)
    contracts.validate(proposal, _SCHEMA, 'Native document proposal')
    return proposal, hashlib.sha256(proposal_text.encode('utf-8')).hexdigest()


def check_native(state: State, project_id: str, proposal_id: str, run_id: str) -> dict:
    """Verify the actual original native source/result and compute a readonly diff."""
    slot = _slot(state.root, project_id, proposal_id)
    task = _record(slot)
    _original(state, task)
    binding = _native_input(state, task, run_id)
    if _record(slot / 'input') != binding:
        raise ValueError('Native correction input differs from its original binding')
    source = native_sources.result(state, project_id, run_id)
    proposal, span_sha = _native_segment(source['result'], task['request_sha256'])
    if proposal is None:
        proposal = {'schema_version': 1, 'request_sha256': task['request_sha256'], 'candidate': None}
    ref = {'kind': 'native-session', 'session_id': task['correction']['native']['session_id'], 'run_id': run_id,
        'native_request_sha256': source['request_sha256'], 'native_prompt_sha256': source['prompt_sha256'],
        'native_result_sha256': source['result_sha256'], 'document_request_sha256': task['request_sha256'],
        'proposal_span_sha256': span_sha}
    return _preview_value(task, proposal, input_digest=source['request_sha256'],
        result_sha256=source['result_sha256'], agent_result={'kind': 'native-session-result',
            'run_id': run_id, 'result_sha256': source['result_sha256']}, source_ref=ref)


def complete_native(state: State, project_id: str, proposal_id: str, run_id: str, *, remaining) -> dict:
    """One original completion may seal a preview; observers never finish it."""
    slot = _slot(state.root, project_id, proposal_id)
    task = _record(slot)
    _original(state, task)
    with file_lock(slot / '.lock'):
        if not (slot / 'native-completion').exists():
            _publish(slot / 'native-completion', {'run_id': run_id, 'request_sha256': task['request_sha256'],
                'input_sha256': _hash(_record(slot / 'input'))})
            value = None
            try:
                if remaining() <= 0:
                    raise ValueError('Original native deadline ended before suggestion completion')
                value = check_native(state, project_id, proposal_id, run_id)
                project = state.project(project_id)
                if project['revision'] != task['revision'] or project.get('correction_suggestions_enabled', True) is not True:
                    raise ValueError('Project correction preference/revision changed during the native turn')
                with state.connect() as db:
                    _current(state, db, task)
                if remaining() <= 0:
                    raise ValueError('Original native deadline ended before suggestion publication')
                if value['candidate_digest'] is None:
                    outcome = {'status': 'none', 'reason': 'No reusable project-document change was proposed'}
                elif value['change']['after']['sha256'] == value['change']['before']['sha256']:
                    outcome = {'status': 'none', 'reason': 'Proposed project document is unchanged'}
                else:
                    _seal_candidate(slot, value)
                    outcome = {'status': 'ready', 'candidate_digest': value['candidate_digest'], 'reason': None}
                if remaining() <= 0:
                    outcome = {'status': 'unavailable', 'reason': 'Original native deadline ended during suggestion publication'}
            except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
                outcome = {'status': 'unavailable', 'reason': str(error)}
            outcome['completion_sha256'] = _hash(_record(slot / 'native-completion'))
            _publish(slot / 'native-outcome', outcome)
            if outcome['status'] == 'ready':
                try:
                    if remaining() <= 0:
                        raise ValueError('Original native allowance ended before final eligibility')
                    # This final positive admission comes after all provisional
                    # candidate/outcome I/O. It does not modify frozen D, N or R.
                    _original(state, task)
                    project = state.project(project_id)
                    if project.get('correction_suggestions_enabled', True) is not True:
                        raise ValueError('Project correction suggestions changed before final eligibility')
                    with state.connect() as db:
                        _current(state, db, task)
                    allowance = remaining()
                    if allowance <= 0:
                        raise ValueError('Original native deadline/stop denied final eligibility')
                    binding = _record(slot / 'input')
                    _publish(slot / 'native-eligibility', {
                        'completion_sha256': outcome['completion_sha256'], 'outcome_sha256': _hash(outcome),
                        'input_sha256': _hash(binding), 'candidate_digest': value['candidate_digest'],
                        'document_request_sha256': task['request_sha256'],
                        'native_request_sha256': binding['input_digest'],
                        'native_prompt_sha256': binding['prompt_sha256'],
                        'native_result_sha256': value['source']['native_result_sha256'],
                        'remaining_seconds': allowance})
                except (OSError, ValueError, KeyError, TypeError):
                    # Absence of the positive witness is the fail-closed state.
                    # No best-effort negative marker can grant or revoke it.
                    pass
    return inspect_proposal(state, project_id, proposal_id)


def _seal_candidate(slot: Path, value: dict) -> None:
    """Caller holds the original slot lock; retain its consumption witness."""
    if (slot / 'candidate').exists():
        if _record(slot / 'candidate') != value:
            raise ValueError('Original slot already sealed a different candidate; prepare a fresh proposal')
        _consumption(slot, value)
    else:
        if (slot / 'consumption').exists():
            raise ValueError('Original candidate history is incomplete; never reconstruct its slot')
        _publish(slot / 'consumption', {'candidate_digest': value['candidate_digest'], 'decision_sha256': None})
        _publish(slot / 'candidate', value)
        _publish(slot / 'candidate-reference', {'project': value['request']['project'],
            'proposal_id': value['request']['proposal_id'], 'request_sha256': value['request']['request_sha256'],
            'candidate_digest': value['candidate_digest'], 'source': value['source'],
            'scope_sha256': value['scope_sha256'], 'base_sha256': value['change']['before']['sha256']})


def _preview_value(task: dict, proposal: dict, *, input_digest: str, result_sha256: str,
                   agent_result: dict, source_ref: dict) -> dict:
    """One complete proposal/diff contract for actual composition and native sources."""
    contracts.validate(proposal, _SCHEMA, 'Document correction proposal')
    _validate_request(task)
    if proposal['request_sha256'] != task['request_sha256']:
        raise ValueError('Document response differs from the original request')
    if proposal['candidate'] is None:
        return {'candidate_digest': None, 'request': task, 'input_digest': input_digest,
                'result_sha256': result_sha256, 'agent_result': agent_result, 'adoption_authorized': False}
    replacement = proposal['candidate']['replacement_text'].encode('utf-8')
    text_blob(replacement)
    if len(replacement) > task['max_material_bytes']:
        raise ValueError('Complete replacement exceeds the supplied material byte limit')
    before = task['baseline']['file']
    after = {'text': replacement.decode('utf-8'), 'sha256': hashlib.sha256(replacement).hexdigest(), 'mode': before['mode']}
    diff = ''.join(line if line.endswith(('\n', '\r')) else line + '\n\\ No newline at end of file\n'
                   for line in difflib.unified_diff(before['text'].splitlines(True), after['text'].splitlines(True),
                                                   fromfile=before['path'], tofile=before['path']))
    scope = {'project': task['project'], 'revision': task['revision'], 'authority': task['authority'],
             'proposal_id': task['proposal_id'], 'repo': task['baseline']['repo'],
             'head': task['baseline']['head'], 'path': before['path'], 'base_sha256': before['sha256'],
             'after_sha256': after['sha256'], 'mode': before['mode']}
    preview = {'schema_version': 1, 'format': 'ergora-document-correction-preview', 'request': task,
               'input_digest': input_digest, 'result_sha256': result_sha256,
               'source': source_ref,
               'change': {'path': before['path'], 'before': before, 'after': after, 'diff': diff},
               'lesson': proposal['candidate']['lesson'], 'applicability': proposal['candidate']['applicability'],
               'scope': scope, 'scope_sha256': _hash(scope), 'agent_result': agent_result,
               'origin_authenticated': False, 'adoption_authorized': False, 'apply': availability()}
    preview['candidate_digest'] = _hash(preview)
    return preview


def check(source: Path, result: Path, *, result_sha256: str, input_digest: str) -> dict:
    """Compute a full offline preview; only original-authority publication seals it."""
    prepared, task, outer, proposal, observed = retrospectives._read_proposal(
        source, result, result_sha256, _REQUEST, _SCHEMA, input_digest=input_digest)
    return _preview_value(task, proposal, input_digest=prepared['digest'], result_sha256=observed,
        agent_result=outer, source_ref={'input': str(source.expanduser().resolve()),
                                     'result': str(result.expanduser().resolve())})



def preview(state: State, project_id: str, source: Path, result: Path, *, revision: int,
            result_sha256: str, input_digest: str) -> dict:
    value = check(source, result, result_sha256=result_sha256, input_digest=input_digest)
    task = value['request']
    if task['project'] != project_id or task['revision'] != revision or state.project(project_id)['revision'] != revision:
        raise ValueError('Document preview project/revision changed')
    slot = _original(state, task)
    if _record(slot / 'input') != {'input_digest': input_digest, 'request_sha256': task['request_sha256']}:
        raise ValueError('Document input differs from its original prepared slot')
    if value['candidate_digest'] is not None:
        with file_lock(slot / '.lock'):
            _seal_candidate(slot, value)
    return value


def status(state: State, project_id: str, value: dict) -> dict:
    slot = _actionable(state, project_id, value)
    with file_lock(slot / '.lock'):
        observed = _phase(slot, value)
    try:
        current = _file(Path(value['request']['baseline']['repo']), value['change']['path'], _RECORD_LIMIT)
        current = {key: current[key] for key in ('path', 'sha256', 'mode', 'identity')}
    except (OSError, ValueError) as error:
        current = {'available': False, 'error': str(error)}
    return {**observed, 'project': project_id, 'proposal_id': value['request']['proposal_id'],
            'candidate_digest': value['candidate_digest'], 'current': current, 'apply': availability()}


def withdraw(state: State, project_id: str, value: dict, *, reason: str) -> dict:
    contracts.validate(reason, _TEXT, 'Withdrawal reason')
    slot = _actionable(state, project_id, value)
    with file_lock(slot / '.lock'):
        observed = _phase(slot, value)
        if observed['status'] == 'ready':
            decision = {'action': 'withdraw', 'candidate_digest': value['candidate_digest'], 'reason': reason, 'at': now()}
            _consume(slot, value, decision)
            _publish(slot / 'decision', decision)
    return status(state, project_id, value)


def _current(state: State, db, task: dict) -> None:
    _original(state, task)
    if task['parent'] is not None and _parent_observation(task['parent']) != task['parent']:
        raise ValueError('Parent document lineage changed; prepare a fresh full preview and consent')
    row = db.execute('SELECT document FROM projects WHERE id=?', (task['project'],)).fetchone()
    project = json.loads(row[0]) if row else None
    if project is None or project['revision'] != task['revision']:
        raise ValueError('Project revision changed; prepare a fresh preview and consent')
    limit = task['max_material_bytes'] - len(task['correction']['text'].encode('utf-8'))
    if _snapshot(project, task['baseline']['file']['path'], limit) != task['baseline']:
        raise ValueError('Document source/HEAD/rules/mode/path changed; prepare a fresh full diff and consent')


def apply(state: State, project_id: str, value: dict, *, revision: int, candidate_digest: str,
          base_sha256: str, scope_sha256: str, confirm: bool = False) -> dict:
    """Consume exact local operator consent once; recovery only observes records."""
    if not availability()['available']:
        raise ValueError(availability()['reason'])
    slot = _actionable(state, project_id, value)
    task = value['request']
    if (confirm is not True or revision != task['revision'] or candidate_digest != value['candidate_digest']
            or base_sha256 != value['change']['before']['sha256'] or scope_sha256 != value['scope_sha256']):
        raise ValueError('Document apply requires explicit confirmation of the exact candidate, base, scope and project revision')
    repo = Path(task['baseline']['repo'])
    common = Path(task['baseline']['git_common_dir'])
    if _identity(common.stat()) != task['baseline']['git_common_identity'] or is_link(common):
        raise ValueError('Original Git common-directory identity changed')
    with file_lock(common / 'ergora-document-corrections.lock'), file_lock(slot / '.lock'):
        observed = _phase(slot, value)
        if observed['status'] != 'ready':
            return {**observed, 'candidate_digest': value['candidate_digest'], 'redispatched': False}
        if value['source'].get('kind') == 'native-session':
            checked = check_native(state, project_id, task['proposal_id'], value['source']['run_id'])
        else:
            checked = check(Path(value['source']['input']), Path(value['source']['result']),
                            result_sha256=value['result_sha256'], input_digest=value['input_digest'])
        if checked != value:
            raise ValueError('Original document input/result/candidate changed; inspect a fresh proposal')
        with _parent_lock(task['parent']), state.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            _current(state, db, task)
            relative = bundles.relative_path(value['change']['path'], 'Project document')
            with _parent_fd(repo, relative) as parent:
                staged = '.ergora-document-' + uuid.uuid4().hex
                descriptor = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
                stage_identity = _identity(os.fstat(descriptor))
                try:
                    with os.fdopen(descriptor, 'wb') as stream:
                        stream.write(value['change']['after']['text'].encode('utf-8'))
                        stream.flush()
                        os.fchmod(stream.fileno(), value['change']['before']['mode'])
                        os.fsync(stream.fileno())
                    _current(state, db, task)
                    decision = {'action': 'apply', 'candidate_digest': candidate_digest, 'base_sha256': base_sha256,
                                'scope_sha256': scope_sha256, 'revision': revision, 'at': now(),
                                'staged': staged, 'stage_identity': stage_identity}
                    _consume(slot, value, decision)
                    _publish(slot / 'decision', decision)
                    attempt = {'decision_sha256': _hash(decision), 'candidate_digest': candidate_digest, 'at': now()}
                    _publish(slot / 'attempt', attempt)
                    _current(state, db, task)
                    os.replace(staged, relative.name, src_dir_fd=parent, dst_dir_fd=parent)
                    os.fsync(parent)
                    actual = _file(repo, relative.as_posix(), task['max_material_bytes'])
                    if any(actual[key] != value['change']['after'][key] for key in ('sha256', 'mode', 'text')):
                        raise ValueError('Replaced document does not match the exact candidate; original attempt remains unknown')
                    _publish(slot / 'receipt', {'attempt_sha256': _hash(attempt), 'candidate_digest': candidate_digest,
                        'after_sha256': actual['sha256'], 'file_identity': actual['identity'], 'at': now()})
                finally:
                    try:
                        if _identity(os.stat(staged, dir_fd=parent, follow_symlinks=False)) == stage_identity:
                            os.unlink(staged, dir_fd=parent)
                    except FileNotFoundError:
                        pass
    return status(state, project_id, value)
