"""Immutable finite training inputs; scheduling and original evidence stay elsewhere."""

from datetime import datetime, timedelta
import asyncio
import getpass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

from . import budget_clock, contracts, reference, registrations, training, training_execution_protocol
from .asset_trees import is_link, publish_directory
from .definition_bundles import parse_json
from .training_execution_protocol import _CycleCapacityError, _read_cycle_bytes as _read_bytes
from .state import State, file_lock, now


MAX_PLAN_BYTES = 10_000_000
MAX_RECORD_BYTES = 1_048_576
_SCHEMA = json.loads((Path(__file__).parent / 'data/schemas/training-cycle-v1.json').read_text(encoding='utf-8'))
_COMMON = training_execution_protocol.ROUND_COMMON
_COVERAGE = {'records': 'saved-local-admission', 'runtime_status': 'not_queried',
             'origin_authenticated': False, 'execution_authorized': False, 'budget_started': False}


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


def _directory(home: Path, project_id: str, cycle_id: str) -> Path:
    if (re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}', project_id) is None
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', cycle_id) is None):
        raise ValueError('Training authorization requires portable project and cycle IDs')
    directory = home / 'training-cycles' / project_id / cycle_id
    for path in (directory, *directory.parents):
        if path.exists() or path.is_symlink():
            if is_link(path) or not path.is_dir():
                raise ValueError('Training authorization requires ordinary directories in its original control home')
        if path == home:
            break
    return directory


def _document(path: Path, *, limit: int = MAX_RECORD_BYTES) -> dict:
    value = parse_json(_read_bytes(path, limit).decode('utf-8'), 'training cycle record', finite=True)
    if not isinstance(value, dict):
        raise ValueError('Training cycle record must be a JSON object')
    return value


def _origin(home: Path, project: dict, source: dict | None = None) -> dict:
    operation = project['registration']['operation_id']
    if source is None:
        result = _document(home / 'registrations' / project['id'] / (operation + '.result.json'))
        digest = result.get('intent_sha256')
    else:
        if set(source) != {'operation_id', 'intent_sha256'} or source['operation_id'] != operation:
            raise ValueError('Training authorization differs from its original published registration')
        digest = source['intent_sha256']
    published = registrations.published_project(home, project['id'], operation, digest)
    # Later binding revisions are legitimate; the original registration stays fixed.
    if any(_sha(published[name]) != _sha(project[name]) for name in ('id', 'repo', 'created', 'schema_version', 'registration')):
        raise ValueError('Training cycle has no matching published registration in this control home')
    return {'operation_id': operation, 'intent_sha256': digest}


def _authorization(home: Path, project_id: str, cycle_id: str, plan: dict, digest: str, value: dict) -> dict:
    try:
        version = value['schema_version']
        if type(version) is not int or version not in (1, 2, 3, 4):
            raise ValueError('Unsupported original training authorization schema')
        clock = value['clock']
        if not isinstance(clock, dict) or set(clock) != set(budget_clock.FIELDS):
            raise ValueError('Training authorization requires its complete original clock')
        budget_clock.validate(clock, plan['definition']['budget']['wall_seconds'])
        expected = {'schema_version': version, 'kind': 'training-cycle-authorization', 'cycle_id': cycle_id,
                    'control_home': str(home), 'project': project_id, 'project_revision': plan['project']['revision'],
                    'input_sha256': digest, 'registration': _origin(home, plan['project'], value['registration']),
                    'execution': plan['project']['registration']['definition']['execution'], 'clock': clock}
        if version in (2, 3, 4):
            expected['controller'] = _controller(home, project_id, cycle_id, digest, value['controller']['actor_id'], version)
        if version in (3, 4):
            sources = value['measurement_sources']
            if (not isinstance(sources, dict) or set(sources) != set(training_execution_protocol.MEASUREMENT_SOURCES)
                    or any(not isinstance(item, str) or re.fullmatch('[0-9a-f]{64}', item) is None
                           for item in sources.values())):
                raise ValueError('Training authorization requires its complete original measurement source map')
            expected['measurement_sources'] = sources
        if (plan['control_home'] != str(home) or plan['project']['id'] != project_id
                or _sha(value) != _sha({**expected, 'sha256': _sha(expected)})):
            raise ValueError('Training authorization differs from its original input, source or complete canonical SHA256')
    except (KeyError, TypeError) as error:
        raise ValueError('Incomplete original training authorization') from error
    return value


def _measurement_sources() -> dict:
    root = Path(__file__).parent
    return {name: hashlib.sha256(_read_bytes(root / name, MAX_PLAN_BYTES)).hexdigest()
            for name in training_execution_protocol.MEASUREMENT_SOURCES}


def _controller(home: Path, project_id: str, cycle_id: str, digest: str, actor: str, version: int) -> dict:
    if not isinstance(actor, str) or re.fullmatch('unix:[0-9]+:[^\r\n]+', actor) is None:
        raise ValueError('Controller authorization requires its original Unix actor')
    identity = {'control_home': str(home), 'project': project_id, 'cycle_id': cycle_id, 'input_sha256': digest}
    protocol = {2: 'ergora-training-cycle-v1', 3: 'ergora-training-cycle-v2', 4: 'ergora-training-cycle-v3'}[version]
    prefix = {2: 'ergora-training-cycle/', 3: 'ergora-training-cycle-v2/', 4: 'ergora-training-cycle-v3/'}[version]
    return {'protocol': protocol, 'workflow_id': prefix + _sha(identity),
        'task_queue': protocol, 'execution_scope': 'ordered-selected-native-once',
        'continuation': 'accepted-archive-pass', 'actor_id': actor, 'confirmation': True}


def _load(home: Path, project_id: str, cycle_id: str, directory: Path) -> tuple[dict, dict, dict | None]:
    raw = _read_bytes(directory / 'cycle.json', MAX_PLAN_BYTES)
    plan = _decode(raw)
    authorization = _authorization(home, project_id, cycle_id, plan, hashlib.sha256(raw).hexdigest(),
                                   _document(directory / 'authorization.json'))
    ready_path = directory / 'ready.json'
    ready = _document(ready_path) if ready_path.exists() or ready_path.is_symlink() else None
    if ready is not None:
        _validate_ready(plan, authorization, ready)
        if authorization['schema_version'] in (2, 3, 4):
            training_execution_protocol.CycleAdmission(directory, authorization).validate_lock()
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


def _record(path: Path, value: dict, *, limit: int = MAX_RECORD_BYTES) -> None:
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
    _record_bytes(path, raw, limit)


def _status(state: State, plan: dict, authorization: dict, ready: dict | None) -> dict:
    policy = plan['definition']['budget']
    current = state.project(authorization['project'])
    matches = _sha(current) == _sha(plan['project'])
    stopped = None
    if authorization['schema_version'] in (2, 3, 4):
        admission = training_execution_protocol.CycleAdmission(
            _directory(state.root, authorization['project'], authorization['cycle_id']), authorization)
        stopped = admission.observe()
    # All business-file observations consume the same original computation window.
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
    observed = {'cycle_id': authorization['cycle_id'], 'project': authorization['project'],
            'project_revision': authorization['project_revision'], 'current_project_revision': current['revision'],
            'authorization_sha256': authorization['sha256'], 'input_sha256': authorization['input_sha256'],
            'authorization': authorization, 'ready': ready, 'status': status, 'reason': reason,
            'current_project_matches': matches, 'work_remaining_seconds': work, 'total_remaining_seconds': total,
            'coverage': {'records': 'original-local-authorization', 'origin_authenticated': True,
                         'runtime_status': 'not_queried', 'budget_started': True, 'execution_authorized': False}}
    if stopped is not None:
        observed['controller'] = {'consent_recorded': True, 'stop': stopped}
        if stopped['stop_visible'] is not False:
            observed.update(status='stopped' if stopped['identity_matches'] is True else 'unknown',
                reason=stopped['reason'] or 'Controller stop is visible; no new work is authorized')
    return observed


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
    plan, authorization, ready = _load(state.root, authorization['project'], authorization['cycle_id'], directory)
    if authorization['sha256'] != original:
        raise ValueError('Original training authorization changed during ready recovery')
    return _status(state, plan, authorization, ready)


def status(state: State, project_id: str, cycle_id: str, *, authorization_sha256: str | None = None) -> dict:
    """Observe original records and flush an existing ready entry; never re-admit or dispatch."""
    directory = _directory(state.root, project_id, cycle_id)
    plan, authorization, ready = _load(state.root, project_id, cycle_id, directory)
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


def start(state: State, project_id: str, cycle_id: str, experiment_id: str,
          authorization_sha256: str, expected_revision: int) -> dict:
    """Bind a selected candidate through the original native start and its single slot."""
    plan, authorization, _ = _load(state.root, project_id, cycle_id, _directory(state.root, project_id, cycle_id))
    if authorization['sha256'] != authorization_sha256:
        raise ValueError('Training start requires the exact original authorization SHA256')
    selected = next((item for item in plan['definition']['candidates'] if item['experiment_id'] == experiment_id), None)
    if selected is None:
        raise ValueError('Experiment is outside the original finite training selection')
    return training.start(state, project_id, experiment_id, expected_revision, selected['manifest_sha256'],
                          timeout=plan['definition']['budget']['control_timeout_seconds'],
                          budget={'cycle_id': cycle_id, 'authorization_sha256': authorization_sha256})


def prepare_controller(state: State, project_id: str, cycle_id: str,
                       authorization_sha256: str, expected_revision: int) -> dict:
    """Freeze the original controller intent, without consuming its start attempt.

    A prepared intent is not a dispatch permit. The final cycle observation may
    already be exhausted; dispatch must use its own original last-action gates.
    """
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Expected project revision must be a positive integer')
    # Only local immutable preparation holds this reservation, never an RPC.
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        observed = status(state, project_id, cycle_id)
        if authorization_sha256 != observed['authorization_sha256']:
            raise ValueError('Controller preparation requires the exact original authorization SHA256')
        if observed['current_project_revision'] != expected_revision:
            raise ValueError('Project revision changed; reload before preparing the controller')
        directory = _directory(state.root, project_id, cycle_id)
        admission = training_execution_protocol.CycleAdmission(directory, observed['authorization'])
        if observed['status'] != 'ready':
            raise ValueError(observed['reason'] or 'Controller preparation requires the original durable ready record')
        with admission.permission():
            if (observed['authorization']['schema_version'] in (3, 4)
                    and _measurement_sources() != observed['authorization']['measurement_sources']):
                raise ValueError('Original measurement sources changed; controller intent cannot be prepared or recovered')
            intent = admission.controller_intent()
            created = intent is None
            if created:
                _record(admission.folder / 'intent.json', admission.intent_record())
            else:
                # Recover a lost reply or failed directory fsync without replacing
                # the original bytes, inode, authorization or computation clock.
                _sync_directory(admission.folder)
            intent = admission.controller_intent()
            admission.check()
            observed = status(state, project_id, cycle_id, authorization_sha256=authorization_sha256)
            return {'created': created, 'intent': intent, 'intent_sha256': _sha(intent), 'cycle': observed}


def _controller_ready(state: State, admission) -> None:
    original = admission.authorization
    observed = status(state, original['project'], original['cycle_id'], authorization_sha256=original['sha256'])
    if observed['status'] != 'ready':
        raise ValueError(observed['reason'] or 'Controller dispatch requires its original durable ready record')
    admission.check()


def _claim_controller(state: State, admission) -> bool:
    """Reserve the single start slot locally; no transaction may cover its RPC."""
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        saved = admission.submission()
        if saved['attempt_saved'] or saved['status'] == 'rejected':
            return False
        if saved['intent'] is None:
            raise ValueError('Prepare the complete original controller intent before dispatch')
        _controller_ready(state, admission)
        _record(admission.folder / 'attempt.json', admission.attempt_record(saved['intent']))
        return True


def _record_controller(state: State, admission, *, run_id: str | None, reason: str | None = None) -> dict:
    """Publish one same-identity terminal fact, never act on a stale pre-claim lookup."""
    with state.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        original = admission.authorization
        _, authorization, ready = _load(state.root, original['project'], original['cycle_id'], admission.directory)
        if authorization['sha256'] != original['sha256'] or ready is None:
            raise ValueError('Controller terminal fact requires its complete original authorization and ready record')
        saved = admission.submission()
        intent = saved['intent']
        if intent is None:
            raise ValueError('Controller delivery facts require the prepared original intent')
        name = 'receipt' if reason is None else 'rejection'
        value = admission.receipt_record(intent, run_id) if reason is None else admission.rejection_record(intent, reason, run_id)
        if saved['status'] in ('submitted', 'rejected'):
            current = _document(admission.folder / (('receipt' if saved['result_saved'] else 'rejection') + '.json'))
            if (name == 'receipt') == saved['result_saved'] and _sha(current) != _sha(value):
                raise ValueError('Controller terminal fact differs from its original immutable record')
            _sync_directory(admission.folder)
            return admission.submission()
        # A late no-attempt lookup can have observed another claimant's legal run.
        if reason in ('preexisting_run', 'lookup_rejected') and saved['attempt_saved']:
            return saved
        if not saved['attempt_saved'] and (reason is None or reason == 'start_conflict'):
            raise ValueError('Controller result has no original consumed start attempt')
        _record(admission.folder / (name + '.json'), value)
        return admission.submission()


def authorize(state: State, project_id: str, cycle_id: str, directory: Path, sha256: str,
              expected_revision: int, *, confirm: bool) -> dict:
    """Persist one clock before all live checks; retries retain its full input and deadline."""
    return _authorize(state, project_id, cycle_id, directory, sha256, expected_revision, confirm=confirm, version=1)


def authorize_controller(state: State, project_id: str, cycle_id: str, directory: Path, sha256: str,
                         expected_revision: int, *, confirm: bool, execute_selected: bool,
                         program_version: int = 1) -> dict:
    """Record birth-time consent for the original ordered selection, never upgrade it."""
    if execute_selected is not True:
        raise ValueError('Explicitly confirm execution of the complete ordered training selection')
    if type(program_version) is not int or program_version not in (1, 2, 3):
        raise ValueError('Controller program version must be integer 1, 2 or 3')
    return _authorize(state, project_id, cycle_id, directory, sha256, expected_revision,
                      confirm=confirm, version=program_version + 1)


def _authorize(state: State, project_id: str, cycle_id: str, directory: Path, sha256: str,
               expected_revision: int, *, confirm: bool, version: int) -> dict:
    if confirm is not True or type(expected_revision) is not int or expected_revision < 1:
        raise ValueError('Explicitly confirm the current project revision and one nonrenewable training budget')
    if not isinstance(sha256, str) or re.fullmatch('[0-9a-f]{64}', sha256) is None:
        raise ValueError('Training authorization requires the complete original input SHA256')
    destination = _directory(state.root, project_id, cycle_id)
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
            sources = _measurement_sources() if version in (3, 4) else None
            value = {'schema_version': version, 'kind': 'training-cycle-authorization', 'cycle_id': cycle_id,
                     'control_home': str(state.root), 'project': project_id, 'project_revision': expected_revision,
                     'input_sha256': sha256, 'registration': _origin(state.root, project),
                     'execution': project['registration']['definition']['execution'],
                     'clock': budget_clock.authorize(plan['definition']['budget']['wall_seconds'])}
            if version in (2, 3, 4):
                value['controller'] = _controller(state.root, project_id, cycle_id, sha256,
                    f'unix:{os.getuid()}:{getpass.getuser()}', version)
            if version in (3, 4):
                value['measurement_sources'] = sources
            authorization = {**value, 'sha256': _sha(value)}
            _authorization(state.root, project_id, cycle_id, plan, sha256, authorization)
            # Reserve the ID permanently before persistence can fail. Incomplete
            # originals are retained and cannot be replaced by another clock.
            destination.mkdir(mode=0o700)
            _sync_directory(state.root)
            _sync_directory(destination.parent.parent)
            _sync_directory(destination.parent)
            _record(destination / 'authorization.json', authorization)
            _record_bytes(destination / 'cycle.json', raw, MAX_PLAN_BYTES)
        # An interrupted publication or observer always loads the original bytes first.
        plan, authorization, ready = _load(state.root, project_id, cycle_id, destination)
        if authorization['schema_version'] != version:
            raise ValueError('Cycle ID retains its original consent mode; it cannot be upgraded or downgraded')
        if sha256 != authorization['input_sha256']:
            raise ValueError('Cycle ID is already bound to a different complete input; original authorization is retained')
        if _sha(project) != _sha(plan['project']):
            raise ValueError('Project differs from the original training authorization; it cannot be renewed')
        observed = (_status(state, plan, authorization, None) if ready is None else
                    _durable_status(state, plan, authorization, ready, destination))
        if ready is not None or observed['status'] != 'pending':
            return observed
        if version in (2, 3, 4):
            admission = training_execution_protocol.CycleAdmission(destination, authorization)
            if admission.folder.exists() or admission.folder.is_symlink():
                if is_link(admission.folder) or not admission.folder.is_dir():
                    raise ValueError('Controller admission requires an ordinary original directory')
            admission.folder.mkdir(exist_ok=True, mode=0o700)
            try:
                admission.lock.lstat()
            except FileNotFoundError:
                _record_bytes(admission.lock, b'', MAX_RECORD_BYTES)
            admission.validate_lock(synchronize=True)
            # Publishing and flushing the lock consume the same original budget.
            observed = _status(state, plan, authorization, None)
            if observed['status'] != 'pending':
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
        plan, authorization, ready = _load(state.root, project_id, cycle_id, destination)
        return _status(state, plan, authorization, ready)


def stop_controller(state: State, project_id: str, cycle_id: str, authorization_sha256: str, *, reason: str) -> dict:
    """Storage-only stop; a live controller must supervise writer and notifications separately."""
    directory = _directory(state.root, project_id, cycle_id)
    _, authorization, _ = _load(state.root, project_id, cycle_id, directory)
    if authorization['sha256'] != authorization_sha256:
        raise ValueError('Controller stop requires the exact original authorization SHA256')
    return training_execution_protocol.CycleAdmission(directory, authorization).request_stop(reason)


def controller(state: State, project_id: str, cycle_id: str, authorization_sha256: str, action: str, *,
               expected_revision: int | None = None, reason: str | None = None) -> dict:
    """Control the original parent through its existing local and S/H owners."""
    if action not in ('status', 'prepare', 'submit', 'reconcile', 'stop'):
        raise ValueError('Unsupported training controller action')
    directory = _directory(state.root, project_id, cycle_id)
    plan, authorization, _ = _load(state.root, project_id, cycle_id, directory)
    if authorization['sha256'] != authorization_sha256:
        raise ValueError('Controller operation requires its exact original authorization SHA256')
    admission = training_execution_protocol.CycleAdmission(directory, authorization)
    if action == 'status':
        return {**admission.submission(), 'authorization_sha256': authorization_sha256,
                'read_only': True, 'runtime_status': 'not_queried', 'execution_authorized': False}
    if action == 'prepare':
        return prepare_controller(state, project_id, cycle_id, authorization_sha256, expected_revision)
    if action == 'stop':
        return stop_controller(state, project_id, cycle_id, authorization_sha256, reason=reason)
    from .reference_training_worker import _CycleOperation, _cycle_snapshot

    mode = 'submit-controller' if action == 'submit' else 'reconcile-controller'
    operation = _CycleOperation(state.root, project_id, cycle_id, authorization_sha256, mode,
        snapshot=_cycle_snapshot(plan, authorization),
        inspection_timeout=plan['definition']['budget']['control_timeout_seconds'])
    return asyncio.run(operation.run())
