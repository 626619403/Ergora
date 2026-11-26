"""Immutable finite training inputs; scheduling and original evidence stay elsewhere."""

import ergora.training.runtime.evidence as execution_evidence
from datetime import datetime, timedelta
from contextlib import ExitStack, contextmanager
import asyncio
import getpass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import shutil
from copy import deepcopy
import tempfile
from time import sleep

import ergora.native.registration as native_registration
import ergora.training.application as training
import ergora.training.execution_protocol as training_execution_protocol
import ergora.configuration.registrations as registrations
from ergora.runtime import budget_clock
from ergora._paths import PACKAGE_ROOT
from ergora.configuration import validation as contracts
from ergora.storage.assets import inventory_tree, is_link, publish_directory
from ergora.definitions.bundles import parse_json
from ergora.training.execution_protocol import _CycleCapacityError, _read_cycle_bytes as _read_bytes
from ergora.storage.state import State, file_lock, now
from ergora.training.materials import relative, require_driver, validate_preparation_intent


MAX_PLAN_BYTES = 10_000_000
MAX_RECORD_BYTES = 1_048_576
_SCHEMA = json.loads((PACKAGE_ROOT / 'data/schemas/training-cycle-v2.json').read_text(encoding='utf-8'))
_COMMON = training_execution_protocol.ROUND_COMMON
_READY_PUBLICATION_PENDING = 'Original admission checks or durable publication are still in progress'
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
    schema = _SCHEMA
    if plan.get('schema_version') == 1:
        schema = deepcopy(_SCHEMA)
        for key in ('request', 'plan'):
            schema['$defs'][key]['properties']['schema_version']['const'] = 1
        schema['$defs']['request']['required'].remove('execution_scope')
        schema['$defs']['request'].pop('allOf', None)
        for name in ('execution_scope', 'search', 'historical_failures', 'profile_policy', 'analyst', 'resources'):
            schema['$defs']['request']['properties'].pop(name, None)
        for name in ('search', 'stage_map', 'stage_admissions', 'preparation_sources', 'analyst', 'material_files'):
            schema['$defs']['plan']['properties'].pop(name, None)
        schema['$defs']['configurationReadback']['properties'].pop('profile', None)
        for operation in schema['$defs']['execution']['oneOf']:
            operation['properties'].pop('profile', None)
    contracts.validate(plan, {'$defs': schema['$defs'], '$ref': '#/$defs/plan'}, 'Training cycle plan')
    request, project = plan['definition'], plan['project']
    _selection(request)
    candidates = request['candidates']
    if len(plan['admissions']) != len(candidates):
        raise ValueError('Training cycle must retain one complete admission for each ordered candidate')
    anchor, baseline_files = None, None
    verification_ids = set()
    try:
        registration = project['registration']
        definition = registration['definition']
        marker_path, _, policy_path, _ = native_registration.registration_paths(project['id'])
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
            inputs = require_driver(manifest, runner)
            if inputs is not None and inputs['kind'] == 'prepared-json':
                for arm in ('baseline', 'candidate'):
                    key = 'state/' + inputs[arm]['path']
                    expected_names.add(key)
                    if files.get(key) != inputs[arm]['sha256']:
                        raise ValueError('Training cycle lacks its original raw configuration inputs')
            material = item.get('cpu_contract_preparation')
            if material is not None:
                for suffix, key in (('.intent.json', 'intent_ref'), ('.cpu-contract-admission.json', 'admission_ref')):
                    path = 'state/ergora/training-preparations/' + selected['experiment_id'] + suffix
                    expected_names.add(path)
                    if files.get(path) != material[key]['sha256']:
                        raise ValueError('Training cycle lacks its complete original CPU admission source inventory')
            if (set(observed['baseline_files']) != {prefix + 'baseline.json'} or set(files) != expected_names
                    or files[registered] != selected['manifest_sha256'] or files[frozen] != selected['manifest_sha256']):
                raise ValueError('Training cycle lacks its complete original source SHA inventory')
            common = {name: manifest.get(name) for name in _COMMON}
            execution = manifest['execution']
            if item.get('execution') != execution:
                raise ValueError('Training cycle operation differs from its original manifest')
            operation_contract = {'operation': execution['operation']}
            if 'cpu_contract' in execution:
                operation_contract['cpu_contract'] = execution['cpu_contract']
            if execution['operation'] == 'training-screen-v1':
                verification = execution['plan']['verification_experiment_id']
                if verification in verification_ids:
                    raise ValueError('Screen choices require distinct frozen verification experiment IDs')
                verification_ids.add(verification)
                operation_contract['plan'] = {key: value for key, value in execution['plan'].items() if key != 'verification_experiment_id'}
            common['operation_contract'] = operation_contract
            if anchor is None:
                anchor, baseline_files = common, observed['baseline_files']
            elif common != anchor or observed['baseline_files'] != baseline_files:
                raise ValueError('Training cycle requires one initial baseline, workload, semantic and measurement contract')
    except (KeyError, TypeError) as error:
        raise ValueError('Training cycle is missing complete original project or admission observations') from error
    if plan['schema_version'] == 2:
        try:
            _validate_scope(plan)
        except (KeyError, TypeError, IndexError, StopIteration) as error:
            raise ValueError('Incomplete original bounded-cycle material; this semantic reader is unavailable') from error
        training_execution_protocol.cpu_contract_roles(plan)
    return plan


def read(directory: Path, *, sha256: str | None = None) -> dict:
    """Verify the complete saved input offline; do not re-admit or authenticate origin."""
    directory = directory.expanduser().absolute()
    if is_link(directory) or not directory.is_dir():
        raise ValueError('Training cycle directory must be ordinary')
    raw = _read_bytes(directory / 'cycle.json', MAX_PLAN_BYTES)
    digest = hashlib.sha256(raw).hexdigest()
    if sha256 is not None and sha256 != digest:
        raise ValueError('Training cycle plan differs from the expected complete SHA256')
    plan = _decode(raw)
    _saved_materials(directory, plan)
    return {'directory': str(directory), 'sha256': digest, 'plan': plan, 'coverage': dict(_COVERAGE)}


def create(state: State, project_id: str, definition: dict, destination: Path) -> dict:
    """Capture explicitly selected original admissions without starting any budget or run."""
    contracts.validate(definition, _SCHEMA, 'Training cycle request')
    _selection(definition)
    policy = definition['budget']
    project = training._project(state, project_id)
    stages, stage_map, preparation_sources, search, analyst, search_saved, analyst_source = [], [], [], None, None, None, None
    definition = deepcopy(definition)
    if definition['execution_scope'] == training_execution_protocol.D_SCOPE:
        import ergora.training.search as training_search
        import ergora.definitions.workflows as workflow_definitions
        search_saved = training_search.read(Path(definition['search']['directory']), sha256=definition['search']['sha256'])
        training_search.authenticate_preparation(state, project_id, search_saved)
        packet = search_saved['plan']
        if packet['project'] != {'id': project['id'], 'repo': project['repo'], 'revision': project['revision'],
                'registration_sha256': project['registration']['sha256']} or packet['control_home'] != str(state.root):
            raise ValueError('Search package differs from the complete current registered project')
        candidates = []
        for choice in packet['choices']:
            pair, original_preparations = {}, {}
            for stage in ('screen', 'full'):
                selected = choice['stages'][stage]
                digest = hashlib.sha256(selected['native_plan']['files']['training/manifests/' + selected['experiment_id'] + '.json'].encode('utf-8')).hexdigest()
                checked = training.check_start(state, project_id, selected['experiment_id'], digest)
                if not checked['ready_for_new_start']:
                    raise ValueError('Cycle cannot adopt an existing submitted stage')
                prepared = training.preparation(state, project_id, selected['experiment_id'])
                preparation = validate_preparation_intent(prepared['intent'])
                if (prepared['status'] != 'prepared' or prepared['intent_sha256'] != preparation['intent_sha256']
                        or preparation['preview_sha256'] != selected['native_preview_sha256']
                        or preparation['body'] != selected['native_plan']):
                    raise ValueError('Cycle requires the complete actual original native stage preparation')
                intent_path = Path(project['registration']['definition']['execution']['state_directory']) / 'ergora/training-preparations' / (selected['experiment_id'] + '.intent.json')
                intent_raw = _read_bytes(intent_path, 16 * MAX_RECORD_BYTES)
                original_intent = parse_json(intent_raw.decode('utf-8'), 'original preparation intent', finite=True)
                if (validate_preparation_intent(original_intent) != preparation
                        or _sha(original_intent) != prepared['intent_sha256']):
                    raise ValueError('Original native preparation intent changed while freezing the cycle')
                original_preparations[stage] = {'path': str(intent_path), 'sha256': hashlib.sha256(intent_raw).hexdigest(), 'bytes': len(intent_raw)}
                pair[stage] = checked
            stages.append(pair)
            preparation_sources.append(original_preparations)
            stage_map.append({'ordinal': choice['ordinal'], 'variant_id': choice['variant_id'],
                **{stage: {'experiment_id': pair[stage]['experiment_id'],
                    'manifest_sha256': pair[stage]['manifest_sha256'], 'admission_sha256': _sha(pair[stage])}
                   for stage in ('screen', 'full')}})
            candidates.append({'experiment_id': pair['screen']['experiment_id'],
                'manifest_sha256': pair['screen']['manifest_sha256']})
        if [{key: item[key] for key in ('experiment_id', 'manifest_sha256')} for item in definition['candidates']] != candidates:
            raise ValueError('Bounded cycle candidates must exactly select the prepared active screen stages')
        candidates = definition['candidates']
        if definition['profile_policy'] != packet['request']['profile_policy']:
            raise ValueError('Cycle profile policy differs from the original search package')
        selector = definition['analyst']
        analyst_source = Path(selector['manifest']['directory'])
        original = workflow_definitions.inspect_manifest(analyst_source, material=True)
        if original['manifest']['preview_sha256'] != selector['manifest']['preview_sha256']:
            raise ValueError('Analyst selector differs from its complete composition preview')
        root = original['manifest']['root']
        frozen = workflow_definitions.freeze_manifest(state.root, root['id'], root['version'],
            original['manifest']['grant'], original['manifest']['preview_sha256'])
        if frozen['digest'] != original['digest']:
            raise ValueError('Analyst material differs from the current accepted complete composition')
        leaf = next(item for item in original['composition']['instances'] if item['path'] == selector['instance'])
        analyst = {key: value for key, value in original.items() if key != 'path'}
        analyst.update({key: selector[key] for key in ('instance', 'binding', 'maximum_seconds', 'mode')})
        import ergora.configuration.catalog as components
        import ergora.agents.invocation as agents
        import ergora.definitions.agents as agent_definitions
        project_binding = components.resolve_binding(project, leaf['role'])
        effective_binding = {**leaf['backend_request'], **project_binding['binding']}
        agents.validate_binding(leaf['role'], effective_binding, formal=True)
        selected_definition = agent_definitions.library(analyst_source / 'assets').get(leaf['ref']['id'], leaf['ref']['version'])
        components.validate_agent_minimum(effective_binding, selected_definition['definition'].get('invocation_minimum'))
        if selector['binding'] != effective_binding:
            raise ValueError('Analyst binding differs from the actual project and frozen leaf selection')
        analyst['project_binding'] = project_binding
        analyst.update(definition_id=leaf['ref']['id'], definition_version=leaf['ref']['version'],
            definition_digest=leaf['ref']['digest'])
        search = {'sha256': search_saved['sha256'], 'preview_sha256': search_saved['preview_sha256'], 'plan': packet,
            'preparation_materials': search_saved['preparation_materials']}
        admissions = [pair['screen'] for pair in stages]
    else:
        candidates = definition['candidates']
        admissions = []
        for selected in candidates:
            checked = training.check_start(state, project_id, selected['experiment_id'], selected['manifest_sha256'])
            if not checked['ready_for_new_start']:
                raise ValueError('Training cycle cannot adopt an existing submission: ' + selected['experiment_id'])
            admissions.append(checked)
    if state.project(project_id)['revision'] != project['revision']:
        raise ValueError('Project changed while capturing training candidates; no cycle plan was published')
    plan = {'schema_version': 2, 'kind': 'training-cycle-plan', 'control_home': str(state.root),
            'project': project, 'definition': definition, 'admissions': admissions}
    if search is not None:
        material_files = {}
        for label, original_path in (('search', Path(search_saved['directory'])), ('analyst', analyst_source)):
            _, files, _ = inventory_tree(original_path, max_directories=1000, max_depth=48)
            material_files.update({label + '/' + key: value for key, value in files.items()})
        plan.update(search=search, stage_map=stage_map, stage_admissions=stages, preparation_sources=preparation_sources, analyst=analyst, material_files=material_files)
        from ergora.training.materials import cpu_contract

        if any(cpu_contract(item['observation']['experiment']['manifest']) is not None for item in admissions):
            selector = plan['admissions'][0]['observation']['experiment']['manifest']['baseline_reference']
            baseline = training.baseline_reference(state, project_id, selector['experiment_id'],
                evidence_sha256=selector['evidence_sha256'])
            if baseline['reference_sha256'] != selector['reference_sha256']:
                raise ValueError('CPU material collection differs from the original baseline reference')
            if baseline.get('cpu_contract') is not None:
                plan['cpu_contract_baseline'] = baseline['cpu_contract']
    raw = (json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
    _decode(raw)  # The writer and offline reader must accept the same complete input.
    destination = destination.expanduser().absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.training-cycle-', dir=destination.parent) as temporary:
        staged = Path(temporary) / 'plan'
        staged.mkdir()
        (staged / 'cycle.json').write_bytes(raw)
        if search_saved is not None:
            shutil.copytree(Path(search_saved['directory']), staged / 'search')
            shutil.copytree(analyst_source, staged / 'analyst')
        _saved_materials(staged, plan)
        publish_directory(staged, destination)
    return {'directory': str(destination), 'sha256': hashlib.sha256(raw).hexdigest(),
            'project': project_id, 'project_revision': project['revision'], 'candidates': len(candidates),
            'budget': policy, 'coverage': dict(_COVERAGE)}


def _require_current(plan, authorization):
    if authorization['schema_version'] != 5 or plan['schema_version'] != 2:
        raise ValueError('Historical controller records are read-only; original runtime replay is unavailable')
    if plan['definition']['execution_scope'] == training_execution_protocol.FULL_SCOPE and any(
            item['observation']['experiment']['manifest']['execution']['operation'] != 'full-verify'
            for item in plan['admissions']):
        raise ValueError('Full controller scope requires complete original full admissions')


def _validate_scope(plan):
    definition = plan['definition']
    scope = definition['execution_scope']
    if scope == training_execution_protocol.FULL_SCOPE:
        if any(name in definition for name in ('search', 'historical_failures', 'profile_policy', 'analyst', 'resources')):
            raise ValueError('Full controller selection cannot implicitly acquire bounded-search operations')
        return
    if scope != training_execution_protocol.D_SCOPE or definition.get('resources') != {'kind': 'cpu'}:
        raise ValueError('Automatic search supports explicit CPU resources only; managed GPU guard is unsupported')
    from ergora.training.materials import validate_profile_policy
    validate_profile_policy(definition['profile_policy'])
    packet = plan['search']['plan']
    if (plan['search']['sha256'] != definition['search']['sha256'] or
            packet['project'] != {'id': plan['project']['id'], 'repo': plan['project']['repo'],
                'revision': plan['project']['revision'],
                'registration_sha256': plan['project']['registration']['sha256']} or
            packet['request']['profile_policy'] != definition['profile_policy']):
        raise ValueError('Bounded cycle differs from its complete prepared search package')
    choices = packet['choices']
    if not len(plan['admissions']) == len(choices) == len(plan['stage_map']) == len(plan['stage_admissions']) == len(plan['preparation_sources']):
        raise ValueError('Bounded cycle requires all logical trials and both original stage admissions')
    identifiers = set()
    for ordinal, (choice, pair, stage, selected) in enumerate(zip(choices, plan['stage_admissions'],
            plan['stage_map'], plan['admissions'])):
        if stage != {'ordinal': ordinal, 'variant_id': choice['variant_id'], **{name: {
                'experiment_id': pair[name]['experiment_id'], 'manifest_sha256': pair[name]['manifest_sha256'],
                'admission_sha256': _sha(pair[name])} for name in ('screen', 'full')}} or selected != pair['screen']:
            raise ValueError('Bounded cycle changed its original logical stage map or active screen admission')
        for name in ('screen', 'full'):
            admitted = pair[name]
            original = choice['stages'][name]
            manifest = admitted['observation']['experiment']['manifest']
            expected_sha = hashlib.sha256(original['native_plan']['files']['training/manifests/' + original['experiment_id'] + '.json'].encode('utf-8')).hexdigest()
            if (admitted['experiment_id'] != original['experiment_id'] or admitted['manifest_sha256'] != expected_sha
                    or admitted['project_revision'] != plan['project']['revision'] or
                    manifest['candidate_config_sha256'] != choice['configuration']['sha256'] or
                    manifest['performance_policy'] != packet['performance_policy'] or
                    manifest['baseline_reference'] != packet['request']['experiment_template']['baseline_reference'] or
                    manifest['execution'] != original['native_request']['experiment']['execution']):
                raise ValueError('Stage admission changed its prepared source/configuration/reference/P/operation')
            if admitted['experiment_id'] in identifiers:
                raise ValueError('Every prepared screen and full stage requires its own original ID')
            identifiers.add(admitted['experiment_id'])
        full_definition = {'schema_version': 2, 'execution_scope': training_execution_protocol.FULL_SCOPE,
            'candidates': [{'experiment_id': pair['full']['experiment_id'], 'manifest_sha256': pair['full']['manifest_sha256'],
                'change': definition['candidates'][ordinal]['change'], 'next_bottleneck': definition['candidates'][ordinal]['next_bottleneck']}],
            'budget': definition['budget']}
        _decode(json.dumps({'schema_version': 2, 'kind': 'training-cycle-plan', 'control_home': plan['control_home'],
            'project': plan['project'], 'definition': full_definition, 'admissions': [pair['full']]},
            ensure_ascii=False, allow_nan=False).encode('utf-8'))
        left, right = (pair[name]['observation']['experiment']['manifest'] for name in ('screen', 'full'))
        if (left['execution']['plan']['verification_experiment_id'] != right['experiment_id'] or
                left['execution'].get('cpu_contract') != right['execution'].get('cpu_contract') or
                any(left.get(key) != right.get(key) for key in (*_COMMON, 'candidate_commit', 'candidate_config_sha256'))):
            raise ValueError('Prepared full verification does not bind the exact screen candidate and common contract')
    analyst = plan['analyst']
    leaf = next((item for item in analyst['composition']['instances'] if item['path'] == analyst['instance']), None)
    if (leaf is None or leaf['kind'] != 'agent' or leaf['ref']['digest'] != analyst['definition_digest'] or
            leaf['ref']['id'] != analyst['definition_id'] or leaf['ref']['version'] != analyst['definition_version'] or
            any(leaf['permissions'][name] for name in ('write', 'shell', 'network')) or
            type(analyst['maximum_seconds']) is not int or not 1 <= analyst['maximum_seconds'] <= 3600):
        raise ValueError('Bounded cycle requires the exact frozen readonly analyst leaf and finite slot cap')
    import ergora.configuration.catalog as components
    project_binding = components.resolve_binding(plan['project'], leaf['role'])
    if (analyst['project_binding'] != project_binding or
            analyst['binding'] != {**leaf['backend_request'], **project_binding['binding']}):
        raise ValueError('Frozen analyst changed its actual original project binding')
    failures = definition['historical_failures']
    if len({item['ordinal'] for item in failures}) != len(failures) or any(
            type(item['ordinal']) is not int or not 0 <= item['ordinal'] < len(choices) for item in failures):
        raise ValueError('Historical failures must select distinct original logical trials')


def _saved_materials(directory, plan, *, authorized=False):
    names = {'cycle.json'}
    if plan['definition'].get('execution_scope') == training_execution_protocol.D_SCOPE:
        import ergora.training.search as training_search
        import ergora.definitions.workflows as workflow_definitions
        names.update(('search', 'analyst'))
        saved = training_search.read(directory / 'search', sha256=plan['search']['sha256'])
        if ({key: saved[key] for key in ('sha256', 'preview_sha256', 'plan', 'preparation_materials')} != plan['search']):
            raise ValueError('Complete original search material changed inside the saved cycle')
        actual = workflow_definitions.inspect_manifest(directory / 'analyst', material=True)
        if any(actual[key] != plan['analyst'][key] for key in ('digest', 'manifest', 'composition')):
            raise ValueError('Complete original analyst material changed inside the saved cycle')
    actual_names = {item.name for item in directory.iterdir()}
    if authorized:
        names.add('authorization.json')
        if not names <= actual_names or actual_names - names - {'ready.json', 'controller'}:
            raise ValueError('Authorized cycle contains missing or undeclared original material')
    elif actual_names != names:
        raise ValueError('Training cycle contains missing or undeclared original preparation material')


def _live_materials(state, plan, directory):
    if plan['definition']['execution_scope'] != training_execution_protocol.D_SCOPE:
        return
    import ergora.training.search as training_search
    saved = training_search.read(directory / 'search', sha256=plan['search']['sha256'])
    training_search.authenticate_preparation(state, plan['project']['id'], saved)
    for ordinal, pair in enumerate(plan['stage_admissions']):
        for stage in ('screen', 'full'):
            original = plan['search']['plan']['choices'][ordinal]['stages'][stage]
            checked_preparation = training.preparation(state, plan['project']['id'], original['experiment_id'])
            preparation = validate_preparation_intent(checked_preparation['intent'])
            if (checked_preparation['status'] != 'prepared' or checked_preparation['intent_sha256'] != preparation['intent_sha256']
                    or preparation['preview_sha256'] != original['native_preview_sha256']
                    or preparation['body'] != original['native_plan']):
                raise ValueError('Original native stage preparation changed before bounded execution')
        full = pair['full']
        checked = training.check_start(state, plan['project']['id'], full['experiment_id'], full['manifest_sha256'])
        if _sha(checked) != _sha(full):
            raise ValueError('Prepared full-stage admission changed before bounded execution')
    training_execution_protocol._frozen_stage_sources(plan)
    _cpu_reference(state, plan)
    if state.project(plan['project']['id']) != plan['project']:
        raise ValueError('Original project changed while authenticating preparation artifacts')


def _cpu_reference(state, plan):
    from ergora.training.runtime.evidence import validate_cpu_applicability, validate_trial_diagnostics

    selector = plan['admissions'][0]['observation']['experiment']['manifest']['baseline_reference']
    baseline = training.baseline_reference(state, plan['project']['id'], selector['experiment_id'],
        evidence_sha256=selector['evidence_sha256'])
    if baseline['reference_sha256'] != selector['reference_sha256']:
        raise ValueError('Original baseline reference changed before CPU admission')
    validate_trial_diagnostics(baseline.get('diagnostics'), plan['definition']['profile_policy'])
    return validate_cpu_applicability(baseline)


def analysis_authority_remaining(authority):
    """Check all original owners first, then sample the remaining original clocks."""
    operation = authority['operation']
    training_execution_protocol.validate_cycle_operation(operation)
    original = operation['identity']['parent']
    if training_execution_protocol.processes.identity(original['pid']) != original:
        raise ValueError('Analysis lost its complete original supervising parent')
    training_execution_protocol.read_cycle_supervisor(operation, live=True)
    window = training_execution_protocol.read_trial_reference(authority['preparation'])
    snapshot, policy = operation['snapshot'], operation['snapshot']['budget']['policy']
    directory = _directory(Path(operation['identity']['control_home']), operation['identity']['project'], operation['identity']['cycle_id'])
    authorization = training_execution_protocol._cycle_authorization(operation)
    training_execution_protocol.CycleAdmission(directory, authorization).check()
    # No blocking identity/source read may leave a stale positive allowance.
    boot, ticks = budget_clock._clock()
    if boot != window['boot_id'] or ticks < window['started_ns']:
        raise ValueError('Analysis preparation lost its original operation clock')
    remaining = min(float(authority['maximum_seconds']) - (ticks - window['started_ns']) / 1_000_000_000,
        training_execution_protocol.cycle_operation_remaining(operation),
        budget_clock.remaining(snapshot['budget']['clock'], policy['wall_seconds'], policy['cleanup_seconds']))
    if remaining <= 0:
        raise ValueError('Original analysis computation allowance ended')
    return remaining


def validate_analysis_authority(state, project_id, authority, *, prepared):
    """Internal S/H-only admission; an ordinary input never grants this authority."""
    protocol = training_execution_protocol
    protocol._exact(authority, ('schema_version', 'kind', 'operation', 'slot', 'fixed_run_id', 'input_digest',
        'composition_preview_sha256', 'prompt_sha256', 'packet', 'maximum_seconds', 'mode', 'preparation'), 'Analysis authority')
    if authority['schema_version'] != 1 or authority['kind'] != 'training-cycle-analysis-authority':
        raise ValueError('Unsupported analysis authority')
    operation, slot = authority['operation'], authority['slot']
    protocol.validate_cycle_operation(operation)
    identity = operation['identity']
    directory = _directory(state.root, project_id, identity['cycle_id'])
    plan, authorization, ready = _load(state.root, project_id, identity['cycle_id'], directory)
    _require_current(plan, authorization)
    if (plan['definition']['execution_scope'] != protocol.D_SCOPE or ready is None
            or identity['control_home'] != str(state.root) or identity['project'] != project_id
            or state.project(project_id) != plan['project'] or operation['snapshot'] != protocol._cycle_snapshot(directory, plan, authorization)):
        raise ValueError('Analysis authority lost its original current project, scope or complete parent')
    raw_operation = protocol.read_raw(state.root / 'operations/training-cycles' / identity['operation_id'] / 'request.json', 32_768)
    if protocol.decode_record(raw_operation) != operation:
        raise ValueError('Analysis authority differs from its original retained operation request')
    if identity['mode'] not in protocol.CYCLE_MEASUREMENT_MODES:
        raise ValueError('Only the original cycle collection operation may consume an analyst slot')
    protocol._exact(slot, ('authorization_sha256', 'ordinal', 'phase', 'packet_sha256', 'definition_digest', 'binding'), 'Analysis slot')
    analyst = plan['analyst']
    preparation = protocol.read_trial_reference(authority['preparation'])
    expected_preparation = {'schema_version': 1, 'kind': 'training-cycle-analysis-preparation',
        'authorization_sha256': authorization['sha256'], 'ordinal': slot['ordinal'], 'phase': slot['phase'],
        'operation_id': identity['operation_id'], 'boot_id': identity['parent']['boot_id'], 'started_ns': preparation['started_ns']}
    protocol._match(preparation, expected_preparation, 'Original independent analyst preparation anchor')
    if (Path(authority['preparation']['path']) != directory / 'controller/analysis' / (slot['phase'] + '-' + str(slot['ordinal'])) / 'preparation.json'
            or type(preparation['started_ns']) is not int or preparation['started_ns'] < operation['bootstrap']['started_ns']
            or preparation['started_ns'] >= operation['bootstrap']['deadline_ns']):
        raise ValueError('Analysis preparation anchor differs from its original slot and H window')
    if (slot['authorization_sha256'] != authorization['sha256'] or slot['phase'] not in ('baseline', 'screen')
            or slot['ordinal'] != (-1 if slot['phase'] == 'baseline' else identity['ordinal'])
            or slot['definition_digest'] != analyst['definition_digest'] or slot['binding'] != analyst['binding']
            or authority['maximum_seconds'] != analyst['maximum_seconds'] or authority['mode'] != analyst['mode']
            or authority['fixed_run_id'] != _sha(slot)[:32]
            or _sha(authority['packet']) != slot['packet_sha256']):
        raise ValueError('Analysis opportunity changed its fixed slot, packet, definition, binding or run')
    saved_packet = directory / 'controller/analysis' / (slot['phase'] + '-' + str(slot['ordinal'])) / 'packet.json'
    if protocol.decode_record(protocol.read_raw(saved_packet, protocol.ARTIFACT_LIMIT)) != authority['packet']:
        raise ValueError('Analysis packet differs from the complete original durable packet')
    if (prepared['digest'] != authority['input_digest'] or prepared['request']['instance'] != analyst['instance']
            or prepared['request']['preview_sha256'] != analyst['manifest']['preview_sha256']
            or prepared['request']['preview_sha256'] != authority['composition_preview_sha256']
            or prepared['request']['prompt_sha256'] != authority['prompt_sha256']
            or prepared['composition'] != analyst['composition']):
        raise ValueError('Analysis input differs from its complete frozen composition and prompt')
    execution_evidence.authenticate_cycle_binding({'cycle_id': identity['cycle_id'], 'authorization_sha256': authorization['sha256'],
        'task_queue': protocol.BUDGET_TASK_QUEUE, 'controller': operation['start_context']['controller']},
        plan, protocol.CycleAdmission(directory, authorization), ready)
    analysis_authority_remaining(authority)
    return authority


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


@contextmanager
def _existing_shared_lock(path):
    """Observe an existing writer lock without creating or repairing any file."""
    with os.fdopen(training_execution_protocol._fd(path), 'rb') as stream:
        if os.name == 'nt':
            import msvcrt

            os.lseek(stream.fileno(), 0, os.SEEK_SET)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBRLCK, 1)
            try:
                yield
            finally:
                os.lseek(stream.fileno(), 0, os.SEEK_SET)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


@contextmanager
def _cpu_preparation_locks(plan):
    """Serialize the first typed clock with the original preparation publisher."""
    roles = training_execution_protocol.cpu_contract_roles(plan)
    if not roles:
        yield roles
        return
    state_root = Path(plan['project']['registration']['definition']['execution']['state_directory'])
    selected = sorted({role['experiment_id'] for role in roles if role['ordinal'] >= 0})
    with ExitStack() as locks:
        for ident in selected:
            locks.enter_context(_existing_shared_lock(state_root / 'ergora/training-preparations' / (ident + '.lock')))
        yield roles


def assert_preparation_unconsumed(control_home, project_id, experiment_id, manifest_sha256):
    """Refuse late A creation using original immutable authorization records only.

    The caller holds the existing preparation writer lock through publication;
    new typed authorizations share that lock before their first clock.
    """
    home = Path(control_home)
    if (not home.is_absolute() or '..' in home.parts
            or not isinstance(experiment_id, str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', experiment_id) is None
            or not isinstance(manifest_sha256, str) or re.fullmatch('[a-f0-9]{64}', manifest_sha256) is None):
        raise ValueError('CPU preparation opportunity check requires its original home/stage/manifest identity')
    catalog = _directory(home, project_id, 'cpu-preparation-check').parent
    if not catalog.exists():
        return

    def names():
        result = []
        with os.scandir(catalog) as entries:
            for entry in entries:
                result.append(entry.name)
                if len(result) > 2000:
                    raise ValueError('unsupported: complete original cycle catalog exceeds 1000 directories')
        return set(result)

    original = names()
    cycles = sorted(name for name in original if not name.startswith('.'))
    if len(cycles) > 1000:
        raise ValueError('unsupported: complete original cycle catalog exceeds 1000 directories')
    if original != set(cycles) | {'.' + name + '.lock' for name in cycles}:
        raise ValueError('CPU preparation has an incomplete original authorization/clock catalog; reconcile it first')
    for cycle_id in cycles:
        directory = _directory(home, project_id, cycle_id)
        try:
            with _existing_shared_lock(catalog / ('.' + cycle_id + '.lock')):
                plan, _, _ = _load(home, project_id, cycle_id, directory)
        except (OSError, ValueError) as error:
            raise ValueError('CPU preparation cannot prove original authorization/clock absence; reconcile its original records') from error
        selected = {item['experiment_id'] for item in plan['definition']['candidates']}
        for pair in plan.get('stage_admissions', []):
            selected.update(item['experiment_id'] for item in pair.values())
        for item in plan['admissions']:
            reference = item['observation']['experiment']['manifest'].get('baseline_reference')
            if reference is not None:
                selected.add(reference['experiment_id'])
        if experiment_id in selected:
            raise ValueError('CPU admission cannot be created after an original stage authorization/clock opportunity')
    if names() != original:
        raise ValueError('CPU preparation authorization catalog changed during its absence check')


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
        if type(version) is not int or version not in (1, 2, 3, 4, 5):
            raise ValueError('Unsupported original training authorization schema')
        clock = value['clock']
        if not isinstance(clock, dict) or set(clock) != set(budget_clock.FIELDS):
            raise ValueError('Training authorization requires its complete original clock')
        budget_clock.validate(clock, plan['definition']['budget']['wall_seconds'])
        expected = {'schema_version': version, 'kind': 'training-cycle-authorization', 'cycle_id': cycle_id,
                    'control_home': str(home), 'project': project_id, 'project_revision': plan['project']['revision'],
                    'input_sha256': digest, 'registration': _origin(home, plan['project'], value['registration']),
                    'execution': plan['project']['registration']['definition']['execution'], 'clock': clock}
        if version in (2, 3, 4, 5):
            expected['controller'] = _controller(home, project_id, cycle_id, digest, value['controller']['actor_id'], version,
                plan['definition'].get('execution_scope', training_execution_protocol.FULL_SCOPE))
        if version in (3, 4, 5):
            sources = value['measurement_sources']
            if (not isinstance(sources, dict)
                    or (set(sources) != set(training_execution_protocol.MEASUREMENT_SOURCES) if version == 5 else len(sources) != 4)
                    or any(not isinstance(item, str) or re.fullmatch('[0-9a-f]{64}', item) is None
                           for item in sources.values())):
                raise ValueError('Training authorization requires its complete original measurement source map')
            for name in sources:
                relative(name)
            expected['measurement_sources'] = sources
        roles = training_execution_protocol.cpu_contract_roles(plan)
        if roles:
            admitted = value['cpu_contracts']
            if (not isinstance(admitted['actor_id'], str) or not admitted['actor_id'].startswith('unix:')
                    or version == 5 and admitted['actor_id'] != value['controller']['actor_id']):
                raise ValueError('CPU role admission lacks its original producer actor provenance')
            expected['cpu_contracts'] = {'actor_id': admitted['actor_id'], 'roles': roles}
        if (plan['control_home'] != str(home) or plan['project']['id'] != project_id
                or _sha(value) != _sha({**expected, 'sha256': _sha(expected)})):
            raise ValueError('Training authorization differs from its original input, source or complete canonical SHA256')
    except (KeyError, TypeError) as error:
        raise ValueError('Incomplete original training authorization') from error
    return value


def _measurement_sources() -> dict:
    return {name: hashlib.sha256(_read_bytes(PACKAGE_ROOT / name, MAX_PLAN_BYTES)).hexdigest()
            for name in training_execution_protocol.MEASUREMENT_SOURCES}


def _require_current_measurement_sources(authorization: dict) -> None:
    if (authorization['schema_version'] == 5
            and _measurement_sources() != authorization['measurement_sources']):
        raise ValueError('Original measurement sources changed; current controller work is unavailable')


def _controller(home: Path, project_id: str, cycle_id: str, digest: str, actor: str, version: int, scope: str) -> dict:
    if not isinstance(actor, str) or re.fullmatch('unix:[0-9]+:[^\r\n]+', actor) is None:
        raise ValueError('Controller authorization requires its original Unix actor')
    identity = {'control_home': str(home), 'project': project_id, 'cycle_id': cycle_id, 'input_sha256': digest}
    protocol = {2: 'ergora-training-cycle-v1', 3: 'ergora-training-cycle-v2', 4: 'ergora-training-cycle-v3', 5: 'ergora-training-cycle-v3'}[version]
    prefix = {2: 'ergora-training-cycle/', 3: 'ergora-training-cycle-v2/', 4: 'ergora-training-cycle-v3/', 5: 'ergora-training-cycle-v3/'}[version]
    return {'protocol': protocol, 'workflow_id': prefix + _sha(identity),
        'task_queue': protocol, 'execution_scope': scope,
        'continuation': 'typed-trial-completion' if scope == training_execution_protocol.D_SCOPE else 'accepted-archive-pass', 'actor_id': actor, 'confirmation': True}


def _load(home: Path, project_id: str, cycle_id: str, directory: Path) -> tuple[dict, dict, dict | None]:
    raw = _read_bytes(directory / 'cycle.json', MAX_PLAN_BYTES)
    plan = _decode(raw)
    authorization = _authorization(home, project_id, cycle_id, plan, hashlib.sha256(raw).hexdigest(),
                                   _document(directory / 'authorization.json'))
    ready_path = directory / 'ready.json'
    ready = _document(ready_path) if ready_path.exists() or ready_path.is_symlink() else None
    if ready is not None:
        _validate_ready(plan, authorization, ready)
        if authorization['schema_version'] == 5:
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
    if authorization['schema_version'] == 5:
        admission = training_execution_protocol.CycleAdmission(
            _directory(state.root, authorization['project'], authorization['cycle_id']), authorization)
        bounded = plan['definition'].get('execution_scope') == training_execution_protocol.D_SCOPE
        stopped = admission.observe(synchronize=bounded, drain=bounded)
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
    if authorization['schema_version'] in (2, 3, 4):
        observed.update(status='historical-read-only', reason='Original runtime replay is unavailable; no current effects are authorized')
    if authorization['schema_version'] == 5 and plan['definition']['execution_scope'] == training_execution_protocol.D_SCOPE:
        progress = training_execution_protocol.read_trial_progress(plan, authorization,
            _directory(state.root, authorization['project'], authorization['cycle_id']))
        directory = _directory(state.root, authorization['project'], authorization['cycle_id'])
        effects = training_execution_protocol.remaining_trial_effects(plan, authorization, directory,
            progress['sequence_trials'], ready=ready is not None)
        progress['local_effects'] = effects
        progress['local_stop'] = {key: stopped.get(key) for key in
            ('stop_visible', 'identity_matches', 'stop_durable', 'admission_drained')}
        budget_cutoff = work is not None and work <= 0
        confirmed_stop = (stopped['stop_visible'] is True and stopped['identity_matches'] is True
            and stopped['stop_durable'] is True and (stopped['admission_drained'] is True
                or effects['admission_state'] == 'not_admitted'))
        progress['termination'] = 'budget' if budget_cutoff else 'stop' if stopped['stop_visible'] is True else None
        progress['coverage'].update(remote_controller_status='not_queried', controller_cancellation_confirmed=None,
            executor_stop_confirmed=(True if effects['state'] == 'quiescent' and progress['executed_trials'] else None))
        # A known cutoff is distinct from a pending/unknown original effect.
        # Neither local fact establishes remote controller cancellation.
        if progress['status'] == 'needs_reconciliation' or effects['state'] != 'quiescent':
            progress.update(status='needs_reconciliation', reason=progress['reason'] or observed['reason'] or
                'An original uncompleted opportunity or record remains unresolved')
        elif progress['status'] != 'screen_search_completed':
            if (stopped['stop_visible'] is not False and not confirmed_stop
                    or observed['status'] in ('unknown', 'project-changed')):
                progress.update(status='needs_reconciliation', reason=observed['reason'] or 'The original local cutoff is unconfirmed')
            elif budget_cutoff or confirmed_stop:
                progress.update(status='partial', reason='Known original budget/stop cutoff; confirmed local prefix retained')
        observed['search'] = progress
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
            observed['reason'] = _READY_PUBLICATION_PENDING
        return observed


def start(state: State, project_id: str, cycle_id: str, experiment_id: str,
          authorization_sha256: str, expected_revision: int) -> dict:
    """Bind a selected candidate through the original native start and its single slot."""
    plan, authorization, _ = _load(state.root, project_id, cycle_id, _directory(state.root, project_id, cycle_id))
    if authorization['sha256'] != authorization_sha256:
        raise ValueError('Training start requires the exact original authorization SHA256')
    if authorization['schema_version'] != 1:
        raise ValueError('Controller birth requires the fixed controller/run path')
    selected = next((item for item in plan['definition']['candidates'] if item['experiment_id'] == experiment_id), None)
    if selected is None:
        raise ValueError('Experiment is outside the original finite training selection')
    return training.start(state, project_id, experiment_id, expected_revision, selected['manifest_sha256'],
                          timeout=plan['definition']['budget']['control_timeout_seconds'],
                          budget={'cycle_id': cycle_id, 'authorization_sha256': authorization_sha256})


class _ControllerNotReady(ValueError):
    def __init__(self, observed: dict, reason: str):
        super().__init__(observed['reason'] or reason)
        self.observed = observed

    @property
    def publication_pending(self) -> bool:
        return self.observed['status'] == 'pending' and self.observed['reason'] == _READY_PUBLICATION_PENDING


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
        plan, _, _ = _load(state.root, project_id, cycle_id, directory)
        _require_current(plan, observed['authorization'])
        _live_materials(state, plan, directory)
        admission = training_execution_protocol.CycleAdmission(directory, observed['authorization'])
        if observed['status'] != 'ready':
            raise _ControllerNotReady(observed, 'Controller preparation requires the original durable ready record')
        with admission.permission():
            _require_current_measurement_sources(observed['authorization'])
            training_execution_protocol.admit_cycle_capacity(plan, str(state.root), project_id, cycle_id,
                len(_read_bytes(directory / 'cycle.json', MAX_PLAN_BYTES)))
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
    _require_current_measurement_sources(original)
    observed = status(state, original['project'], original['cycle_id'], authorization_sha256=original['sha256'])
    if observed['status'] != 'ready':
        raise _ControllerNotReady(observed, 'Controller dispatch requires its original durable ready record')
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
    return _authorize(state, project_id, cycle_id, directory, sha256, expected_revision, confirm=confirm, controller=False)


def authorize_controller(state: State, project_id: str, cycle_id: str, directory: Path, sha256: str,
                         expected_revision: int, *, confirm: bool, execute_selected: bool) -> dict:
    """Persist one explicit current birth; the selected scope can never be upgraded."""
    if execute_selected is not True:
        raise ValueError('Explicitly confirm execution of the complete ordered training selection')
    return _authorize(state, project_id, cycle_id, directory, sha256, expected_revision,
                      confirm=confirm, controller=True)


def _authorize(state: State, project_id: str, cycle_id: str, directory: Path, sha256: str,
               expected_revision: int, *, confirm: bool, controller: bool) -> dict:
    version = 5 if controller else 1
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
            original = read(directory, sha256=sha256)
            raw = _read_bytes(directory / 'cycle.json', MAX_PLAN_BYTES)
            if hashlib.sha256(raw).hexdigest() != sha256:
                raise ValueError('Training cycle plan differs from the expected complete SHA256')
            plan = _decode(raw)
            if plan['schema_version'] != 2:
                raise ValueError('Historical cycle data has no current execution authority')
            if plan['control_home'] != str(state.root) or _sha(plan['project']) != _sha(project):
                raise ValueError('Training authorization requires the original control home and complete current project')
            with _cpu_preparation_locks(plan) as roles:
                sources = _measurement_sources() if version == 5 else None
                if controller:
                    training_execution_protocol.admit_cycle_capacity(plan, str(state.root), project_id, cycle_id, len(raw))
                value = {'schema_version': version, 'kind': 'training-cycle-authorization', 'cycle_id': cycle_id,
                         'control_home': str(state.root), 'project': project_id, 'project_revision': expected_revision,
                         'input_sha256': sha256, 'registration': _origin(state.root, project),
                         'execution': project['registration']['definition']['execution'],
                         'clock': budget_clock.authorize(plan['definition']['budget']['wall_seconds'])}
                if controller:
                    value['controller'] = _controller(state.root, project_id, cycle_id, sha256,
                        f'unix:{os.getuid()}:{getpass.getuser()}', version, plan['definition']['execution_scope'])
                if controller:
                    value['measurement_sources'] = sources
                if roles:
                    value['cpu_contracts'] = {'actor_id': f'unix:{os.getuid()}:{getpass.getuser()}', 'roles': roles}
                authorization = {**value, 'sha256': _sha(value)}
                if version == 5:
                    _require_current(plan, authorization)
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
        if plan['definition']['execution_scope'] == training_execution_protocol.D_SCOPE:
            # Publish each existing complete input tree atomically. A failed
            # first copy retains the same authorization and can resume only the
            # exact original material, never another input or clock.
            for name in ('search', 'analyst'):
                target = destination / name
                if not target.exists() and not target.is_symlink():
                    original = read(directory.expanduser().absolute(), sha256=sha256)
                    if original['plan'] != plan:
                        raise ValueError('Material recovery differs from the original complete cycle input')
                    with tempfile.TemporaryDirectory(prefix='.cycle-material-', dir=destination) as temporary:
                        staged = Path(temporary) / name
                        shutil.copytree(directory.expanduser().absolute() / name, staged)
                        expected_files = {key[len(name) + 1:]: value for key, value in plan['material_files'].items() if key.startswith(name + '/')}
                        if inventory_tree(staged, max_directories=1000, max_depth=48)[1] != expected_files:
                            raise ValueError('Original complete cycle material changed during recovery')
                        publish_directory(staged, target)
                if all((destination / part).exists() for part in ('search', 'analyst')):
                    training_execution_protocol._frozen_cycle_materials(plan, destination)
                observed = _status(state, plan, authorization, None)
                if observed['status'] != 'pending':
                    return observed
            _saved_materials(destination, plan, authorized=True)
            _live_materials(state, plan, destination)
            observed = _status(state, plan, authorization, None)
            if observed['status'] != 'pending':
                return observed
        _require_current_measurement_sources(authorization)
        if controller:
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
               expected_revision: int | None = None, reason: str | None = None,
               wait_ready: bool = False) -> dict:
    """Control the original parent through its existing local and S/H owners."""
    if action not in ('status', 'prepare', 'submit', 'reconcile', 'stop'):
        raise ValueError('Unsupported training controller action')
    if wait_ready and action != 'submit':
        raise ValueError('Waiting for readiness requires controller submission')
    directory = _directory(state.root, project_id, cycle_id)
    plan, authorization, _ = _load(state.root, project_id, cycle_id, directory)
    if authorization['sha256'] != authorization_sha256:
        raise ValueError('Controller operation requires its exact original authorization SHA256')
    if authorization['schema_version'] in (2, 3, 4):
        if action != 'status':
            _require_current(plan, authorization)
        return {'authorization_sha256': authorization_sha256, 'status': 'historical-read-only',
            'read_only': True, 'runtime_status': 'not_queried', 'execution_authorized': False,
            'records': {item.name: _document(item) for item in (directory / 'controller').glob('*.json')}}
    admission = training_execution_protocol.CycleAdmission(directory, authorization)
    if action == 'status':
        observed = {**admission.submission(), 'authorization_sha256': authorization_sha256,
                'read_only': True, 'runtime_status': 'not_queried', 'execution_authorized': False}
        if plan['definition']['execution_scope'] == training_execution_protocol.D_SCOPE:
            observed['search'] = status(state, project_id, cycle_id, authorization_sha256=authorization_sha256)['search']
        return observed
    _require_current(plan, authorization)
    if action == 'prepare':
        return prepare_controller(state, project_id, cycle_id, authorization_sha256, expected_revision)
    if action == 'stop':
        return stop_controller(state, project_id, cycle_id, authorization_sha256, reason=reason)
    if wait_ready:
        while True:
            saved = admission.submission()
            if saved['attempt_saved'] or saved['status'] == 'rejected':
                action = 'reconcile'
                break
            observed = status(state, project_id, cycle_id, authorization_sha256=authorization_sha256)
            if observed['status'] == 'ready':
                try:
                    prepared = prepare_controller(state, project_id, cycle_id, authorization_sha256,
                                                  authorization['project_revision'])
                except _ControllerNotReady as error:
                    observed = error.observed
                except BlockingIOError:
                    observed = status(state, project_id, cycle_id, authorization_sha256=authorization_sha256)
                except ValueError:
                    observed = status(state, project_id, cycle_id, authorization_sha256=authorization_sha256)
                    if observed['status'] in ('ready', 'pending'):
                        raise
                else:
                    observed = prepared['cycle']
                    if observed['status'] == 'ready':
                        break
            if observed['status'] not in ('ready', 'pending'):
                saved = admission.submission()
                if saved['attempt_saved'] or saved['status'] == 'rejected':
                    action = 'reconcile'
                    break
                result = {key: value for key, value in saved.items() if key != 'intent'}
                result.update(status=observed['status'], reason=observed['reason'],
                              authorization_sha256=authorization_sha256, runtime_status='not_queried')
                if observed['status'] == 'stopped':
                    result['stop'] = observed['controller']['stop']
                return result
            sleep(min(1, observed['work_remaining_seconds']))
    mode = 'submit-controller' if action == 'submit' else 'reconcile-controller'
    operation = training_execution_protocol._CycleOperation(state.root, project_id, cycle_id, authorization_sha256, mode,
        snapshot=training_execution_protocol._cycle_snapshot(directory, plan, authorization),
        inspection_timeout=plan['definition']['budget']['control_timeout_seconds'])
    return asyncio.run(operation.run())
