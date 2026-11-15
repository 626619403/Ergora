"""Immutable finite training inputs; scheduling and original evidence stay elsewhere."""

from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

from . import budget_clock, contracts, reference, registrations, training
from .asset_trees import is_link, publish_directory
from .definition_bundles import parse_json
from .state import State, file_lock, now


MAX_PLAN_BYTES = 10_000_000
MAX_RECORD_BYTES = 1_048_576
_SCHEMA = json.loads((Path(__file__).parent / 'data/schemas/training-cycle-v1.json').read_text(encoding='utf-8'))
_COMMON = ('baseline_id', 'baseline_commit', 'base_config_sha256', 'workload_fingerprint',
           'dataset_manifest_sha256', 'initial_checkpoint_sha256', 'environment_fingerprint',
           'validation_contract_sha256', 'comparison_tool_sha256', 'checks_required',
           'quality_required', 'performance_policy')
_COVERAGE = {'records': 'saved-local-admission', 'runtime_status': 'not_queried',
             'origin_authenticated': False, 'execution_authorized': False, 'budget_started': False}


def _read_bytes(path: Path, limit: int) -> bytes:
    for selected in (path, *path.parents):
        if is_link(selected):
            raise ValueError('Training cycle records cannot use symlinks or reparse points')
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Training cycle records require ordinary files')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f'Complete training cycle record exceeds {limit} bytes; nothing was truncated')
    return raw


def _sha(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def _selection(definition: dict) -> None:
    if definition['budget']['cleanup_seconds'] >= definition['budget']['wall_seconds']:
        raise ValueError('Training cycle cleanup reserve must be inside the total wall allowance')
    candidates = definition['candidates']
    if len({item['experiment_id'] for item in candidates}) != len(candidates):
        raise ValueError('Select each original training experiment once')


def _decode(raw: bytes) -> dict:
    if len(raw) > MAX_PLAN_BYTES:
        raise ValueError('Complete training cycle plan exceeds 10 MB; nothing was truncated')
    plan = parse_json(raw.decode('utf-8'), 'training cycle plan', finite=True, bounded=True)
    contracts.validate(plan, {'$defs': _SCHEMA['$defs'], '$ref': '#/$defs/plan'}, 'Training cycle plan')
    request, project = plan['definition'], plan['project']
    _selection(request)
    candidates = request['candidates']
    if len(plan['admissions']) != len(candidates):
        raise ValueError('Training cycle must retain one complete admission for each ordered candidate')
    anchor, baseline_files = None, None
    try:
        registration = project['registration']
        definition = registration['definition']
        marker_path, _, policy_path, _ = reference.registration_paths(project['id'])
        marker = registration['files'][marker_path]
        # Registration v1 hashes this envelope; its definition omits id/repo.
        identity = json.dumps({'id': project['id'], 'repo': project['repo'], 'definition': definition},
                              sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        if (registration['status'] != 'published' or marker['id'] != project['id']
                or marker['control_home'] != plan['control_home']
                or marker['definition_sha256'] != registration['sha256']
                or registration['sha256'] != hashlib.sha256(identity).hexdigest()
                or 'training-optimization' not in definition['templates']):
            raise ValueError('Training cycle must retain its original published project and control directory')
        expected_files = registrations.publication_files(project, definition, plan['control_home'], registration['sha256'])
        # Imported execution policies may retain an equivalent list order.
        policy = registration['files'][policy_path]
        normalized = {**registration['files'], policy_path: {**policy, 'allowed_task_types': sorted(policy['allowed_task_types'])}}
        if normalized != expected_files:
            raise ValueError('Training cycle must retain all original registration documents and their definition')
        manifest_root = PurePosixPath(definition['execution']['state_directory']) / 'training/manifests'
        prefix = 'state/training/projects/' + project['id'] + '/perf/'
        for selected, checked in zip(candidates, plan['admissions']):
            if (checked['project'] != project['id'] or checked['project_revision'] != project['revision']
                    or checked['experiment_id'] != selected['experiment_id']
                    or checked['manifest_sha256'] != selected['manifest_sha256']):
                raise ValueError('Training cycle admission differs from its selected project, revision or unsubmitted candidate')
            observed = checked['observation']
            item = observed['experiment']
            manifest, binding, spec, runner = (item[name] for name in ('manifest', 'binding', 'spec', 'current_runner'))
            if (item['experiment_id'] != selected['experiment_id']
                    or binding['experiment_id'] != selected['experiment_id']
                    or binding['manifest_sha'] != selected['manifest_sha256']
                    or binding != item['spec']['binding']
                    or item['spec']['manifest_uri'] != (manifest_root / (selected['experiment_id'] + '.json')).as_uri()
                    or manifest['experiment_id'] != selected['experiment_id']
                    or manifest['candidate_commit'] != binding['candidate_sha']
                    or manifest['baseline_commit'] != binding['baseline_sha']
                    or manifest['candidate_sha'] != binding['candidate_sha']
                    or manifest['baseline_sha'] != binding['baseline_sha']
                    or manifest['local_project'] != project['id']
                    or runner['project'] != project['id'] or runner['repo'] != project['repo']
                    or runner['runner_template_id'] != manifest['runner_template_id']
                    or not 1 <= runner['timeout_seconds'] <= min(82800, spec['max_run_seconds'])
                    or item['max_run_seconds'] != manifest['max_run_seconds'] or item['max_run_seconds'] != spec['max_run_seconds']):
                raise ValueError('Training cycle contains conflicting original experiment or runner identities')
            baseline = observed['baseline']
            if (any(manifest[left] != baseline[right] for left, right in (
                    ('baseline_id', 'baseline_id'), ('baseline_commit', 'commit'),
                    ('base_config_sha256', 'config_sha256'), ('workload_fingerprint', 'workload_fingerprint')))
                    or item['baseline_id'] != manifest['baseline_id']
                    or item['workload_fingerprint'] != manifest['workload_fingerprint']
                    or item['track'] != manifest['track']):
                raise ValueError('Training cycle manifest differs from its saved baseline or observation')
            files = item['files']
            registered = prefix + 'experiments/' + selected['experiment_id'] + '/manifest.json'
            frozen = 'state/training/manifests/' + selected['experiment_id'] + '.json'
            expected_names = {registered, frozen, 'state/training/specs/' + selected['experiment_id'] + '.json',
                              'config/training-runners/' + runner['runner_template_id'] + '.json'}
            if (set(observed['baseline_files']) != {prefix + 'baseline.json'} or set(files) != expected_names
                    or files[registered] != selected['manifest_sha256'] or files[frozen] != selected['manifest_sha256']):
                raise ValueError('Training cycle lacks its complete original source SHA inventory')
            common = {name: manifest[name] for name in _COMMON}
            if anchor is None:
                anchor, baseline_files = common, observed['baseline_files']
            elif common != anchor or observed['baseline_files'] != baseline_files:
                raise ValueError('Training cycle requires one initial baseline, workload, semantic and measurement contract')
    except (KeyError, TypeError) as error:
        raise ValueError('Training cycle is missing complete original project or admission observations') from error
    return plan


def read(directory: Path, *, sha256: str | None = None) -> dict:
    """Verify the complete saved input offline; do not re-admit or authenticate origin."""
    directory = directory.expanduser().absolute()
    if is_link(directory) or not directory.is_dir() or {p.name for p in directory.iterdir()} != {'cycle.json'}:
        raise ValueError('Training cycle directory must contain exactly one ordinary cycle.json')
    raw = _read_bytes(directory / 'cycle.json', MAX_PLAN_BYTES)
    digest = hashlib.sha256(raw).hexdigest()
    if sha256 is not None and sha256 != digest:
        raise ValueError('Training cycle plan differs from the expected complete SHA256')
    return {'directory': str(directory), 'sha256': digest, 'plan': _decode(raw), 'coverage': dict(_COVERAGE)}


def create(state: State, project_id: str, definition: dict, destination: Path) -> dict:
    """Capture explicitly selected original admissions without starting any budget or run."""
    contracts.validate(definition, _SCHEMA, 'Training cycle request')
    _selection(definition)
    policy, candidates = definition['budget'], definition['candidates']
    project = training._project(state, project_id)
    admissions = []
    for selected in candidates:
        checked = training.check_start(state, project_id, selected['experiment_id'], selected['manifest_sha256'])
        if not checked['ready_for_new_start']:
            raise ValueError('Training cycle cannot adopt an existing submission: ' + selected['experiment_id'])
        admissions.append(checked)
    if state.project(project_id)['revision'] != project['revision']:
        raise ValueError('Project changed while capturing training candidates; no cycle plan was published')
    plan = {'schema_version': 1, 'kind': 'training-cycle-plan', 'control_home': str(state.root),
            'project': project, 'definition': definition, 'admissions': admissions}
    raw = (json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
    _decode(raw)  # The writer and offline reader must accept the same complete input.
    destination = destination.expanduser().absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.training-cycle-', dir=destination.parent) as temporary:
        staged = Path(temporary) / 'plan'
        staged.mkdir()
        (staged / 'cycle.json').write_bytes(raw)
        publish_directory(staged, destination)
    return {'directory': str(destination), 'sha256': hashlib.sha256(raw).hexdigest(),
            'project': project_id, 'project_revision': project['revision'], 'candidates': len(candidates),
            'budget': policy, 'coverage': dict(_COVERAGE)}


def _directory(state: State, project_id: str, cycle_id: str) -> Path:
    if (re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}', project_id) is None
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', cycle_id) is None):
        raise ValueError('Training authorization requires portable project and cycle IDs')
    directory = state.root / 'training-cycles' / project_id / cycle_id
    for path in (directory, *directory.parents):
        if path.exists() or path.is_symlink():
            if is_link(path) or not path.is_dir():
                raise ValueError('Training authorization requires ordinary directories in its original control home')
        if path == state.root:
            break
    return directory


def _document(path: Path) -> dict:
    value = parse_json(_read_bytes(path, MAX_RECORD_BYTES).decode('utf-8'), 'training cycle record', finite=True)
    if not isinstance(value, dict):
        raise ValueError('Training cycle record must be a JSON object')
    return value


def _origin(state: State, project: dict, source: dict | None = None) -> dict:
    operation = project['registration']['operation_id']
    if source is None:
        result = _document(state.root / 'registrations' / project['id'] / (operation + '.result.json'))
        digest = result.get('intent_sha256')
    else:
        if set(source) != {'operation_id', 'intent_sha256'} or source['operation_id'] != operation:
            raise ValueError('Training authorization differs from its original published registration')
        digest = source['intent_sha256']
    published = registrations.published_project(state.root, project['id'], operation, digest)
    # Later binding revisions are legitimate; the original registration stays fixed.
    if any(_sha(published[name]) != _sha(project[name]) for name in ('id', 'repo', 'created', 'schema_version', 'registration')):
        raise ValueError('Training cycle has no matching published registration in this control home')
    return {'operation_id': operation, 'intent_sha256': digest}


def _authorization(state: State, project_id: str, cycle_id: str, plan: dict, digest: str, value: dict) -> dict:
    try:
        clock = value['clock']
        if not isinstance(clock, dict) or set(clock) != set(budget_clock.FIELDS):
            raise ValueError('Training authorization requires its complete original clock')
        budget_clock.validate(clock, plan['definition']['budget']['wall_seconds'])
        expected = {'schema_version': 1, 'kind': 'training-cycle-authorization', 'cycle_id': cycle_id,
                    'control_home': str(state.root), 'project': project_id, 'project_revision': plan['project']['revision'],
                    'input_sha256': digest, 'registration': _origin(state, plan['project'], value['registration']),
                    'execution': plan['project']['registration']['definition']['execution'], 'clock': clock}
        if (plan['control_home'] != str(state.root) or plan['project']['id'] != project_id
                or _sha(value) != _sha({**expected, 'sha256': _sha(expected)})):
            raise ValueError('Training authorization differs from its original input, source or complete canonical SHA256')
    except (KeyError, TypeError) as error:
        raise ValueError('Incomplete original training authorization') from error
    return value


def _load(state: State, project_id: str, cycle_id: str, directory: Path) -> tuple[dict, dict, dict | None]:
    raw = _read_bytes(directory / 'cycle.json', MAX_PLAN_BYTES)
    plan = _decode(raw)
    authorization = _authorization(state, project_id, cycle_id, plan, hashlib.sha256(raw).hexdigest(),
                                   _document(directory / 'authorization.json'))
    ready_path = directory / 'ready.json'
    ready = _document(ready_path) if ready_path.exists() or ready_path.is_symlink() else None
    if ready is not None:
        _validate_ready(plan, authorization, ready)
    return plan, authorization, ready


def _validate_ready(plan: dict, authorization: dict, ready: dict) -> None:
    expected = {'schema_version': 1, 'kind': 'training-cycle-ready',
                'authorization_sha256': authorization['sha256'],
                'admissions_sha256': _sha(plan['admissions']), 'project_revision': authorization['project_revision'],
                'checked_at': ready.get('checked_at')}
    try:
        checked = datetime.fromisoformat(ready.get('checked_at'))
        clock, policy = authorization['clock'], plan['definition']['budget']
        if (checked.utcoffset() != timedelta(0) or checked.isoformat() != ready['checked_at']
                or checked < datetime.fromisoformat(clock['authorized_at'])
                or checked >= datetime.fromisoformat(clock['deadline_at']) - timedelta(seconds=policy['cleanup_seconds'])
                or _sha(ready) != _sha(expected)):
            raise ValueError('Training ready record differs from its original authorization, admissions or computation window')
    except (TypeError, OverflowError) as error:
        raise ValueError('Invalid training ready completion time') from error


def _sync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _record_bytes(path: Path, raw: bytes, limit: int) -> None:
    if len(raw) > limit:
        raise ValueError(f'Complete training cycle record exceeds {limit} bytes; nothing was truncated')
    descriptor, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        _sync_directory(path.parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _record(path: Path, value: dict) -> None:
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
    _record_bytes(path, raw, MAX_RECORD_BYTES)


def _status(state: State, plan: dict, authorization: dict, ready: dict | None) -> dict:
    policy = plan['definition']['budget']
    current = state.project(authorization['project'])
    matches = _sha(current) == _sha(plan['project'])
    status, reason, work, total = 'pending' if ready is None else 'ready', None, None, None
    try:
        total = budget_clock.remaining(authorization['clock'], policy['wall_seconds'])
        work = total - policy['cleanup_seconds']
        if work <= 0:
            status, reason = 'exhausted', 'Original computation deadline has passed; authorization cannot be renewed'
        elif not matches:
            status, reason = 'project-changed', 'Current project differs from the original confirmed revision; no new work is authorized'
    except (OSError, ValueError) as error:
        status, reason = 'unknown', str(error)
    return {'cycle_id': authorization['cycle_id'], 'project': authorization['project'],
            'project_revision': authorization['project_revision'], 'current_project_revision': current['revision'],
            'authorization_sha256': authorization['sha256'], 'input_sha256': authorization['input_sha256'],
            'authorization': authorization, 'ready': ready, 'status': status, 'reason': reason,
            'current_project_matches': matches, 'work_remaining_seconds': work, 'total_remaining_seconds': total,
            'coverage': {'records': 'original-local-authorization', 'origin_authenticated': True,
                         'runtime_status': 'not_queried', 'budget_started': True, 'execution_authorized': False}}


def _durable_status(state: State, plan: dict, authorization: dict, ready: dict, directory: Path) -> dict:
    # A previous publisher may have lost its reply or failed after linking ready.
    # Complete that same directory entry, without changing bytes or its clock.
    try:
        _sync_directory(directory)
    except OSError as error:
        observed = _status(state, plan, authorization, None)
        observed.update(status='unknown', reason='Original ready record durability is unconfirmed: ' + str(error))
        return observed
    original = authorization['sha256']
    plan, authorization, ready = _load(state, authorization['project'], authorization['cycle_id'], directory)
    if authorization['sha256'] != original:
        raise ValueError('Original training authorization changed during ready recovery')
    return _status(state, plan, authorization, ready)


def status(state: State, project_id: str, cycle_id: str, *, authorization_sha256: str | None = None) -> dict:
    """Observe original records and flush an existing ready entry; never re-admit or dispatch."""
    directory = _directory(state, project_id, cycle_id)
    plan, authorization, ready = _load(state, project_id, cycle_id, directory)
    if authorization_sha256 is not None and authorization_sha256 != authorization['sha256']:
        raise ValueError('Training authorization differs from the expected complete canonical SHA256')
    lock = directory.parent / ('.' + cycle_id + '.lock')
    if is_link(lock) or not stat.S_ISREG(lock.stat().st_mode):
        raise ValueError('Training authorization requires its ordinary original lock file')
    try:
        with file_lock(lock, blocking=False):
            return (_status(state, plan, authorization, None) if ready is None else
                    _durable_status(state, plan, authorization, ready, directory))
    except BlockingIOError:
        # A visible ready link is not completion while its publisher is still fsyncing.
        observed = _status(state, plan, authorization, None)
        if observed['status'] == 'pending':
            observed['reason'] = 'Original admission checks or durable publication are still in progress'
        return observed


def authorize(state: State, project_id: str, cycle_id: str, directory: Path, sha256: str,
              expected_revision: int, *, confirm: bool) -> dict:
    """Persist one clock before all live checks; retries retain its full input and deadline."""
    if confirm is not True or type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Explicitly confirm the current project revision and one nonrenewable training budget')
    if not isinstance(sha256, str) or re.fullmatch('[0-9a-f]{64}', sha256) is None:
        raise ValueError('Training authorization requires the complete original input SHA256')
    destination = _directory(state, project_id, cycle_id)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = destination.parent / ('.' + cycle_id + '.lock')
    if lock.exists() or lock.is_symlink():
        if is_link(lock) or not stat.S_ISREG(lock.stat().st_mode):
            raise ValueError('Training authorization requires its ordinary original lock file')
    with file_lock(lock):
        project = training._project(state, project_id)
        if project['revision'] != expected_revision:
            raise ValueError('Project revision changed; reload before authorizing training')
        if not destination.exists():
            directory = directory.expanduser().absolute()
            if is_link(directory) or not directory.is_dir() or {p.name for p in directory.iterdir()} != {'cycle.json'}:
                raise ValueError('Select one complete original cycle input directory')
            raw = _read_bytes(directory / 'cycle.json', MAX_PLAN_BYTES)
            if hashlib.sha256(raw).hexdigest() != sha256:
                raise ValueError('Training cycle plan differs from the expected complete SHA256')
            plan = _decode(raw)
            if plan['control_home'] != str(state.root) or _sha(plan['project']) != _sha(project):
                raise ValueError('Training authorization requires the original control home and complete current project')
            value = {'schema_version': 1, 'kind': 'training-cycle-authorization', 'cycle_id': cycle_id,
                     'control_home': str(state.root), 'project': project_id, 'project_revision': expected_revision,
                     'input_sha256': sha256, 'registration': _origin(state, project),
                     'execution': project['registration']['definition']['execution'],
                     'clock': budget_clock.authorize(plan['definition']['budget']['wall_seconds'])}
            authorization = {**value, 'sha256': _sha(value)}
            _authorization(state, project_id, cycle_id, plan, sha256, authorization)
            # Reserve the ID permanently before persistence can fail. Incomplete
            # originals are retained and cannot be replaced by another clock.
            destination.mkdir(mode=0o700)
            _sync_directory(state.root)
            _sync_directory(destination.parent.parent)
            _sync_directory(destination.parent)
            _record(destination / 'authorization.json', authorization)
            _record_bytes(destination / 'cycle.json', raw, MAX_PLAN_BYTES)
        # An interrupted publication or observer always loads the original bytes first.
        plan, authorization, ready = _load(state, project_id, cycle_id, destination)
        if sha256 != authorization['input_sha256']:
            raise ValueError('Cycle ID is already bound to a different complete input; original authorization is retained')
        if _sha(project) != _sha(plan['project']):
            raise ValueError('Project differs from the original training authorization; it cannot be renewed')
        observed = (_status(state, plan, authorization, None) if ready is None else
                    _durable_status(state, plan, authorization, ready, destination))
        if ready is not None or observed['status'] != 'pending':
            return observed
        for selected, expected in zip(plan['definition']['candidates'], plan['admissions']):
            checked = training.check_start(state, project_id, selected['experiment_id'], selected['manifest_sha256'])
            observed = _status(state, plan, authorization, None)
            if observed['status'] != 'pending':
                return observed
            if _sha(checked) != _sha(expected):
                raise ValueError('Current complete training admission differs from the original finite selection')
        ready = {'schema_version': 1, 'kind': 'training-cycle-ready', 'authorization_sha256': authorization['sha256'],
                 'admissions_sha256': _sha(plan['admissions']), 'project_revision': expected_revision, 'checked_at': now()}
        observed = _status(state, plan, authorization, None)
        if observed['status'] != 'pending':
            return observed
        _validate_ready(plan, authorization, ready)
        _record(destination / 'ready.json', ready)
        # File/directory fsync and revision changes consume this authorization too.
        plan, authorization, ready = _load(state, project_id, cycle_id, destination)
        return _status(state, plan, authorization, ready)
