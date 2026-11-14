"""Immutable finite training inputs; scheduling and original evidence stay elsewhere."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import tempfile

from . import contracts, reference, registrations, training
from .asset_trees import is_link, publish_directory
from .definition_bundles import parse_json
from .state import State


MAX_PLAN_BYTES = 10_000_000
_SCHEMA = json.loads((Path(__file__).parent / 'data/schemas/training-cycle-v1.json').read_text(encoding='utf-8'))
_COMMON = ('baseline_id', 'baseline_commit', 'base_config_sha256', 'workload_fingerprint',
           'dataset_manifest_sha256', 'initial_checkpoint_sha256', 'environment_fingerprint',
           'validation_contract_sha256', 'comparison_tool_sha256', 'checks_required',
           'quality_required', 'performance_policy')
_COVERAGE = {'records': 'saved-local-admission', 'runtime_status': 'not_queried',
             'origin_authenticated': False, 'execution_authorized': False, 'budget_started': False}


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
    path = directory / 'cycle.json'
    if is_link(path) or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('Training cycle plan requires an ordinary file')
    with path.open('rb') as stream:
        raw = stream.read(MAX_PLAN_BYTES + 1)
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
