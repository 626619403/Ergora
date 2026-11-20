"""Finite configuration preparation, using the original native publication owner.

This preparation does not execute candidates or start a budget. Its offline reader verifies
content and links, not execution authority or current native state.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import hashlib
import itertools
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import TYPE_CHECKING

from jsonschema.exceptions import SchemaError

from ergora._paths import DATA_ROOT

import ergora.configuration.validation as contracts
import ergora.development.handoff as handoff
from ergora.storage.assets import inventory_tree, is_link, publish_directory
if TYPE_CHECKING:
    from ergora.storage.state import State
from ergora.training.materials import decode_record, material_plan, relative, require_driver, validate_profile_policy, preparation_preview_body


MAX_REQUEST_BYTES = 1_048_576
MAX_CONFIG_BYTES = 1_048_576
MAX_PACKAGE_BYTES = 10_000_000
_SCHEMA = json.loads((DATA_ROOT / 'schemas/training-search-v2.json').read_text())
_COVERAGE = {'operation': 'preparation-only', 'origin_authenticated': False,
             'runtime_status': 'not_queried', 'execution_authorized': False,
             'budget_started': False, 'configuration_execution': 'requires-original-managed-execution'}
_PACKET_FIELDS = {'schema_version', 'kind', 'control_home', 'project', 'request', 'request_sha256',
                  'candidate_source', 'cardinality', 'family_allocation', 'performance_policy',
                  'performance_policy_sha256', 'baseline_configuration', 'preparation_materials', 'choices', 'coverage'}
_CHOICE_FIELDS = {'ordinal', 'grid_ordinal', 'combination', 'variant_id', 'configuration', 'stages'}
_STAGE_FIELDS = {'experiment_id', 'native_request', 'native_preview_sha256', 'native_plan'}
_MATERIAL_PATH = 'materials/preparation.zip'


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _sha(value):
    return hashlib.sha256(_encode(value)).hexdigest()


def _raw_sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _document(text, label):
    try:
        value = decode_record(text.encode('utf-8'))
        pending, count = [(value, 1)], 0
        while pending:
            item, depth = pending.pop()
            count += 1
            if depth > 64 or count > 100_000:
                raise ValueError('Complete JSON exceeds 64 levels / 100000 values')
            if isinstance(item, dict):
                pending.extend((child, depth + 1) for pair in item.items() for child in pair)
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in item)
    except (ValueError, RecursionError) as error:
        raise ValueError(label + ': ' + str(error)) from error
    return value


def _decode_packet(raw):
    if len(raw) > MAX_PACKAGE_BYTES:
        raise ValueError('Complete search package manifest exceeds 10 MB')
    return _document(raw.decode('utf-8'), 'training search packet')


def _config_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError('Invalid ' + label + ' fields')


def _digest(value):
    if not isinstance(value, str) or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError('Training search identities require complete lowercase SHA256 values')


def _file(path, limit):
    path = Path(path)
    before = path.lstat()
    if is_link(path) or not stat.S_ISREG(before.st_mode):
        raise ValueError('Training search requires ordinary files: ' + str(path))
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or not os.path.samestat(before, opened):
            raise ValueError('Training search file changed before its complete read')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if len(raw) > limit:
        raise ValueError('Complete training search file exceeds its capacity: ' + path.name)
    if (not os.path.samestat(opened, path.lstat()) or is_link(path)
            or (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns)
               != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
        raise ValueError('Training search file changed during its complete read')
    return raw


def read_request(path: Path) -> dict:
    """Read one complete strict JSON document; never import a Python recipe."""
    return _document(_file(path, MAX_REQUEST_BYTES).decode('utf-8-sig'), 'training search request')


def _same(left, right):
    # JSON booleans and numbers are different kinds, even though True == 1 in Python.
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(_same(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


def _identical(left, right):
    # Frozen record identities use canonical JSON, unlike scalar duplicate
    # detection: 6 and 6.0 cannot share a claimed canonical content SHA.
    return _encode(left) == _encode(right)


def _at(value, path):
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise ValueError('Configuration dimensions require existing object-key paths')
        value = value[key]
    if isinstance(value, (dict, list)):
        raise ValueError('Configuration dimensions may replace scalar leaves only')
    return value


def _differences(left, right, path=()):
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            raise ValueError('Candidate configuration must preserve baseline object keys')
        for key in left:
            yield from _differences(left[key], right[key], (*path, key))
    elif not _same(left, right):
        yield path


def _request(value):
    try:
        raw = _encode(value)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError('Training search accepts finite JSON data only') from error
    if len(raw) > MAX_REQUEST_BYTES:
        raise ValueError('Complete training search request exceeds 1 MiB')
    value = _document(raw.decode(), 'training search request')
    contracts.validate(value, _SCHEMA, 'Training search request')
    # JSON Schema patterns use search semantics; '$' may precede a final LF.
    # These identifiers and the decimal policy have a whole-string contract.
    if re.fullmatch(r'0\.[0-9]*[1-9]', value['family_policy']['family_error_budget']) is None:
        raise ValueError('Family error budget must be a canonical decimal string')
    identifiers = [(value['search_id'], 40), (value['runner']['runner_template_id'], 80),
                   (value['experiment_template']['baseline_id'], 80),
                   (value['preparation_materials']['task_id'], 80)]
    identifiers.extend((item['name'], 64) for item in value['dimensions'])
    if value['candidate_source']['kind'] == 'exported_six_stage_v1':
        identifiers.append((value['candidate_source']['task_id'], 80))
    if any(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,' + str(limit - 1) + '}', name) is None
           for name, limit in identifiers):
        raise ValueError('Training search requires complete portable identifiers')
    for key, item in value['experiment_template'].items():
        if key.endswith(('_sha256', '_fingerprint')):
            _digest(item)
    for key in ('baseline_commit', 'candidate_commit'):
        if re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}', value['experiment_template'][key]) is None:
            raise ValueError('Training search requires complete original Git commit IDs')
    materials = value['preparation_materials']
    _digest(materials['packet']['sha256'])
    if not PurePosixPath(materials['packet']['path']).is_absolute():
        raise ValueError('Select the original complete preparation handoff by absolute path')
    validate_profile_policy(value['profile_policy'])
    for key, item in value['candidate_source'].items():
        if key.endswith('_sha256'):
            _digest(item)
    selection = value['selection']
    if ((selection['algorithm'] == 'ordered_grid_v1' and selection['seed'] is not None)
            or (selection['algorithm'] == 'seeded_without_replacement_v1' and type(selection['seed']) is not int)):
        raise ValueError('Search order requires its exact explicit seed contract')
    if value['budget']['cleanup_seconds'] >= value['budget']['wall_seconds']:
        raise ValueError('Search cleanup reserve must be inside its planned wall allowance')
    baseline = value['baseline_configuration']
    original = baseline['utf8'].encode('utf-8')
    if len(original) > MAX_CONFIG_BYTES or _raw_sha(original) != baseline['sha256']:
        raise ValueError('Baseline configuration raw bytes differ from their declared SHA256 or capacity')
    if baseline['sha256'] != value['experiment_template']['base_config_sha256']:
        raise ValueError('Baseline configuration does not bind the original base_config_sha256')
    # A UTF-8 signature is ignored only while decoding, never in the raw identity.
    base = _document(original.decode('utf-8-sig'), 'baseline configuration')
    if not isinstance(base, dict):
        raise ValueError('Baseline configuration must be a complete JSON object')
    config = value['configuration']
    pending = [config['schema']]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if {'$ref', '$dynamicRef', '$id'} & set(item):
                raise ValueError('Configuration schema references and resolvers are unsupported')
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    try:
        contracts.StrictValidator.check_schema(config['schema'])
    except SchemaError as error:
        raise ValueError('Invalid configuration schema: ' + error.message) from error
    contracts.validate(config['template'], config['schema'], 'Complete candidate configuration')
    paths = set()
    for mutable in config['mutable']:
        path = tuple(mutable['path'])
        if (path in paths or any(path[:len(other)] == other or other[:len(path)] == path for other in paths)):
            raise ValueError('Mutable configuration paths must be unique and non-overlapping')
        if mutable['allowed_change'] not in value['experiment_template']['allowed_changes']:
            raise ValueError('Mutable configuration path has no exact approved allowed_changes scope')
        _at(base, path)
        _at(config['template'], path)
        paths.add(path)
    if any(path not in paths for path in _differences(base, config['template'])):
        raise ValueError('Candidate template changes a fixed configuration field outside mutable scope')
    names, dimension_paths = set(), set()
    cardinality = 1
    for dimension in value['dimensions']:
        path = tuple(dimension['path'])
        if dimension['name'] in names or path in dimension_paths or path not in paths:
            raise ValueError('Search dimensions require unique names and declared mutable paths')
        names.add(dimension['name'])
        dimension_paths.add(path)
        cardinality *= len(dimension['values'])
        if cardinality > 4096:
            raise ValueError('Training search full-space cardinality exceeds 4096')
        for index, item in enumerate(dimension['values']):
            if any(_same(item, previous) for previous in dimension['values'][:index]):
                raise ValueError('Duplicate scalar values in a search dimension')
    _legacy_performance_policy_v1(value)
    return value, base, cardinality


def _legacy_performance_policy_v1(request):
    """Project the frozen family allocation into the original three-key ABI."""
    measurement = request['measurement']
    thresholds = {}
    for key in ('min_saved_seconds_at_normalization', 'min_speedup_percent'):
        number = measurement['thresholds'][key]
        if number is not None:
            number = float(number)
            if not math.isfinite(number) or number < 0:
                raise ValueError('Performance thresholds require finite nonnegative values')
            number = 0.0 if number == 0 else number
        thresholds[key] = number
    thresholds['mode'] = measurement['thresholds']['mode']
    count = sum(thresholds[key] is not None for key in ('min_saved_seconds_at_normalization', 'min_speedup_percent'))
    if not count:
        raise ValueError('Enable at least one declared performance threshold')
    # Decimal construction is exact and avoids Python's decimal-string-to-int
    # digit ceiling. The sole binary64 rounding is the final float conversion.
    alpha = Fraction(Decimal(request['family_policy']['family_error_budget']))
    confidence = float(1 - alpha / (request['selection']['max_trials'] * count))
    if not .5 < confidence < 1:
        raise ValueError('Projected confidence is outside the original open (0.5, 1) interval')
    return {'normalization_source_samples': measurement['normalization_source_samples'],
            'statistics': {**measurement['statistics'], 'confidence': confidence}, 'thresholds': thresholds}


def _selected_v1(request):
    dimensions = request['dimensions']
    values = itertools.product(*(dimension['values'] for dimension in dimensions))
    combinations = [(index, [[dimension['name'], item] for dimension, item in zip(dimensions, chosen)])
                    for index, chosen in enumerate(values)]
    if request['selection']['algorithm'] == 'seeded_without_replacement_v1':
        seed = request['selection']['seed']
        combinations.sort(key=lambda item: (_sha(['seeded_without_replacement_v1', seed, item[1]]), item[0]))
    return combinations[:request['selection']['max_trials']]


def _binding(project):
    return {'id': project['id'], 'repo': project['repo'], 'revision': project['revision'],
            'registration_sha256': project['registration']['sha256']}


def _source(request, project, records):
    source = request['candidate_source']
    if source['kind'] == 'unchanged_baseline_v1':
        if records is not None or request['experiment_template']['candidate_commit'] != request['experiment_template']['baseline_commit']:
            raise ValueError('Unchanged source must retain the exact baseline implementation')
        return
    _exact(records, {'creation', 'task', 'export'}, 'original six-stage source records')
    created, task, exported = records['creation'], records['task'], records['export']
    if (created.get('status') != 'published' or created.get('project') != project['id']
            or created.get('task_id') != source['task_id'] or created.get('intent_sha256') != source['creation_sha256']
            or not created.get('compiled_sha256') or task.get('task_id') != source['task_id']
            or task.get('request_sha256') != source['request_sha256']
            or task.get('profile_sha256') != source['profile_sha256']
            or exported.get('status') != 'exported' or exported.get('run_id') != source['run_id']
            or exported.get('candidate_sha') != request['experiment_template']['candidate_commit']
            or exported.get('repo') != project['repo'] or exported.get('intent_sha256') != source['export_intent_sha256']
            or exported.get('lease_released') is not True):
        raise ValueError('Candidate source requires its original published task and completed exact export receipt')
    _digest(created['compiled_sha256'])


def _capture_source(state, project, request):
    import ergora.development.application as tasks

    source = request['candidate_source']
    records = None
    if source['kind'] == 'exported_six_stage_v1':
        records = {'creation': tasks.creation(state, project['id'], source['task_id']),
                   'task': tasks.show(state, project['id'], source['task_id']),
                   'export': tasks.export_status(state, project['id'], source['task_id'])}
    _source(request, _binding(project), records)
    return {'kind': source['kind'], 'records': records}


def _choice(request, project, ordinal, grid_ordinal, combination):
    config = deepcopy(request['configuration']['template'])
    for dimension, (_, value) in zip(request['dimensions'], combination):
        node = config
        for key in dimension['path'][:-1]:
            node = node[key]
        node[dimension['path'][-1]] = value
    contracts.validate(config, request['configuration']['schema'], 'Complete generated candidate configuration')
    raw = _config_bytes(config)
    if len(raw) > MAX_CONFIG_BYTES:
        raise ValueError('Complete generated candidate configuration exceeds 1 MiB')
    digest = _raw_sha(raw)
    variant = _sha(['training-search-v2', project, _sha(request), ordinal, grid_ordinal, combination, digest])
    stem = request['search_id'] + '-' + f'{ordinal:02d}' + '-' + variant[:16]
    full_id = stem + '-full'
    policy = _legacy_performance_policy_v1(request)
    stages = {}
    for stage in ('screen', 'full'):
        ident = stem + '-' + stage
        execution = {'operation': 'full-verify'} if stage == 'full' else {
            'operation': 'training-screen-v1',
            'plan': {**request['screen_policy'], 'verification_experiment_id': full_id},
            'profile': request['profile_policy']}
        if request.get('cpu_execution_contract') is not None:
            execution['cpu_contract'] = request['cpu_execution_contract']
        # Normalize before the first native preview, preserving original native bytes.
        native = _document(_encode({'experiment': {**request['experiment_template'], 'experiment_id': ident,
                     'candidate_config_sha256': digest, 'performance_policy': policy, 'execution': execution},
                     **request['runner'], 'configuration_materials': {'format': 'json-v1',
                         'baseline': {'utf8': request['baseline_configuration']['utf8'],
                                      'sha256': request['baseline_configuration']['sha256']},
                         'candidate': {'utf8': raw.decode('utf-8'), 'sha256': digest}}}).decode(),
                     'generated native request')
        stages[stage] = {'experiment_id': ident, 'native_request': native}
    return {'ordinal': ordinal, 'grid_ordinal': grid_ordinal, 'combination': combination, 'variant_id': variant,
            'configuration': {'path': 'configs/' + stem + '.json', 'sha256': digest, 'bytes': len(raw)},
            'stages': stages}, raw


def _material_selection(request, directory=None):
    selector = request['preparation_materials']
    path = Path(selector['packet']['path']) if directory is None else Path(directory) / _MATERIAL_PATH
    roles = selector['artifacts']
    read = handoff.evidence(path, sha256=selector['packet']['sha256'])
    index = read['index']
    original = index['contract'].get('original_input')
    if (index['task_id'] != selector['task_id'] or index['run_id'] != selector['run_id']
            or original is None or index['temporal_status'] != 'COMPLETED'):
        raise ValueError('Search preparation requires its complete original input and closed task run')
    jobs = {job['job_id']: job for job in index['jobs']}
    composition = original.get('composition', {})
    profile = index['contract']['spec']['profile']
    required = {}
    for role, selected in roles.items():
        job = jobs[selected['job_id']]
        stage = job['stage'].split(':', 1)[0]
        if (job['receipt_state'] != 'SUCCEEDED' or stage not in
                (('inventory', 'plan') if role == 'flow_map' else (role,))):
            raise ValueError('Preparation material has the wrong original stage or incomplete receipt: ' + role)
        declared = profile.get('artifacts_by_stage', {}).get(stage)
        if (not isinstance(declared, list) or not declared
                or any(not isinstance(name, str) or not name for name in declared)
                or len(set(declared)) != len(declared)):
            raise ValueError('Preparation material lacks its complete original declared output contract')
        # The original source owner omits the trusted behavior baseline from
        # inspector specialist outputs; canonical inventory retains it.
        if composition.get('preparation') and stage == 'inventory' and job['stage'] != 'inventory':
            declared = [name for name in declared if name != 'behavior-baseline']
        if selected['name'] not in declared:
            raise ValueError('Preparation selector is outside its original declared outputs: ' + role)
        for name in declared:
            required[(job['job_id'], name)] = {'job_id': job['job_id'], 'name': name}
    # A selector locates its original producer. Analysis consumes every required
    # output of that producer, including bodies beyond the selected anchor.
    unique = list(required.values())
    read = handoff.evidence(path, unique, sha256=selector['packet']['sha256'])
    if composition.get('preparation'):
        plan_job = jobs[roles['plan']['job_id']]
        selected = {'job_id': plan_job['job_id'], 'name': 'preparation-sources'}
        if selected not in unique:
            read = handoff.evidence(path, [*unique, selected], sha256=selector['packet']['sha256'])
        artifact = next(item for item in read['artifacts'] if item['job_id'] == plan_job['job_id']
                        and item['artifact']['name'] == 'preparation-sources')
        sources = _document(artifact['text'], 'original preparation sources')
        spec = index['contract']['spec']
        if (sources['kind'] != 'formal-preparation-sources' or sources['stage'] != 'plan'
                or sources['member'] != composition['preparation']['plan']['coordinator']
                or sources['request_sha256'] != spec['request_sha256']
                or sources['profile_sha256'] != spec['profile_sha256']
                or sources['admission_sha256'] != original['sha256']):
            raise ValueError('Preparation source chain differs from its complete original scope')
        artifacts = {(item['path'], item['sha256']) for job in index['jobs'] for item in job['receipt']['artifacts']}
        outputs = [output for row in sources['members'].values() for output in row['outputs'].values()]
        outputs.extend(sources['inventory']['outputs'].values())
        for output in outputs:
            ref, raw = output['ref'], output['text'].encode('utf-8')
            if ((ref['path'], ref['sha256']) not in artifacts or _raw_sha(raw) != ref['sha256']
                    or len(raw) != output['bytes']):
                raise ValueError('Preparation source output differs from its original complete artifact')
    return read


def _check_material_scope(request, project, materials):
    index = materials['index']
    template = request['experiment_template']
    original = index['contract']['spec']['request']
    outcome = index['original_outcome']
    if (index['project'] != project['id'] or original.get('repository', {}).get('starting_sha') != template['baseline_commit']
            or outcome.get('base_sha') != template['baseline_commit']
            or outcome.get('candidate_sha') != template['candidate_commit']):
        raise ValueError('Preparation materials differ from the original project or reviewed source scope')


def _authenticate_materials(state, project, request, materials):
    import ergora.development.application as tasks

    _check_material_scope(request, project, materials)
    selected = request['preparation_materials']
    observed = tasks.evidence(state, project['id'], selected['task_id'], run_id=selected['run_id'])
    if not _identical(observed, materials['index']):
        raise ValueError('Preparation handoff differs from its complete original task evidence')


def _capture_materials(state, project, request):
    try:
        materials = _material_selection(request)
        _authenticate_materials(state, project, request, materials)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('Preparation source lacks its complete original material scope') from error
    path = Path(request['preparation_materials']['packet']['path'])
    raw = _file(path, MAX_PACKAGE_BYTES)
    if _raw_sha(raw) != request['preparation_materials']['packet']['sha256']:
        raise ValueError('Original preparation packet changed during its complete read')
    return materials, raw


def _check_native(packet, choice):
    plan, request = choice['native_plan'], choice['native_request']
    fields = {'schema_version', 'operation', 'control_home', 'project', 'repo', 'execution', 'registration_sha256',
              'experiment_id', 'project_revision', 'request', 'sources', 'files'}
    _exact(plan, fields, 'original native preparation plan')
    project, ident = packet['project'], choice['experiment_id']
    if (type(plan['schema_version']) is not int or plan['schema_version'] not in (1, 2) or plan['operation'] != 'prepare-training'
            or any(plan[key] != packet[key] for key in ('control_home',))
            or plan['project'] != project['id'] or plan['repo'] != project['repo']
            or type(plan['project_revision']) is not int or plan['project_revision'] != project['revision']
            or plan['registration_sha256'] != project['registration_sha256']
            or plan['experiment_id'] != ident or not _identical(plan['request'], request)
            or choice['native_preview_sha256'] != _sha(plan)):
        raise ValueError('Frozen native preview differs from its original project, request or identity')
    _exact(plan['sources'], {'baseline', 'runner'}, 'native preparation sources')
    for record in plan['sources'].values():
        _exact(record, {'document', 'file_sha256'}, 'native source record')
        if not isinstance(record['document'], dict):
            raise ValueError('Invalid frozen native source identity')
        _digest(record['file_sha256'])
    baseline, runner = (plan['sources'][name]['document'] for name in ('baseline', 'runner'))
    _exact(runner, {'schema_version', 'runner_template_id', 'project', 'repo', 'command', 'timeout_seconds', 'configuration_readback'},
           'original runner template')
    capability = runner['configuration_readback']
    _exact(capability, {'protocol', 'source', 'prepared_json_format', 'manifest_configuration_role', 'observation_scheme', 'baseline_reference_protocol', 'screen', *({'profile'} if 'profile' in capability else set())},
           'frozen configuration readback')
    if (capability['screen'] is not None and (not isinstance(capability['screen'], dict)
            or set(capability['screen']) != {'protocol', 'scheme'}
            or capability['screen']['protocol'] != 'training-screen-v1'
            or not isinstance(capability['screen']['scheme'], str))
            or capability['baseline_reference_protocol'] not in (None, 'baseline-reference-v1')
            or capability['protocol'] != 'training-configuration-driver-v1'
            or capability['manifest_configuration_role'] != 'source-bytes'
            or capability['prepared_json_format'] != 'json-v1'
            or not isinstance(capability['observation_scheme'], str)
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', capability['observation_scheme']) is None):
        raise ValueError('Frozen configuration execution declaration is unavailable or unsupported')
    source = capability['source']
    _exact(source, {'repo', 'commit', 'inventory_sha256', 'entrypoint'}, 'frozen configuration source')
    _digest(source['inventory_sha256'])
    relative(source['entrypoint'])
    if (not isinstance(source['repo'], str) or not PurePosixPath(source['repo']).is_absolute()
            or not isinstance(source['commit'], str) or re.fullmatch('[a-f0-9]{40}', source['commit']) is None
            or len(runner['command']) != 3 or not isinstance(runner['command'][0], str)
            or not PurePosixPath(runner['command'][0]).is_absolute()
            or runner['command'][1:] != ['{configuration_driver}', '{configuration_request}']):
        raise ValueError('Frozen configuration driver source or command differs from its current contract')
    _exact(plan['execution'], {'installation', 'config_directory', 'state_directory'}, 'native execution paths')
    if (any(not isinstance(value, str) or not PurePosixPath(value).is_absolute()
            for value in plan['execution'].values())
            or not isinstance(runner['command'], list) or not runner['command']
            or any(not isinstance(arg, str) or not arg for arg in runner['command'])):
        raise ValueError('Original runner requires literal argv and explicit native execution paths')
    template = packet['request']['experiment_template']
    if any(template[key] != baseline[baseline_key] for key, baseline_key in (
            ('baseline_id', 'baseline_id'), ('baseline_commit', 'commit'), ('base_config_sha256', 'config_sha256'),
            ('workload_fingerprint', 'workload_fingerprint'))):
        raise ValueError('Original baseline anchor differs from its registered snapshot')
    if (runner['schema_version'] != 2 or type(runner['schema_version']) is not int
            or runner['project'] != project['id'] or runner['repo'] != project['repo']
            or runner['runner_template_id'] != request['runner_template_id']
            or type(runner['timeout_seconds']) is not int
            or not 1 <= runner['timeout_seconds'] <= request['max_run_seconds']):
        raise ValueError('Original runner differs from the selected project or window')
    inputs, raw_materials = material_plan(ident, request['configuration_materials'])
    targets = ('training/manifests/' + ident + '.json',
               'training/projects/' + project['id'] + '/perf/experiments/' + ident + '/manifest.json',
               'training/specs/' + ident + '.json', *raw_materials)
    _exact(plan['files'], targets, 'original native publication files')
    if any(not isinstance(value, str) for value in plan['files'].values()):
        raise ValueError('Original native publication files must contain complete UTF-8 text')
    raw = plan['files'][targets[0]].encode('utf-8')
    if len(raw) > MAX_CONFIG_BYTES or plan['files'][targets[1]].encode('utf-8') != raw:
        raise ValueError('Original native manifests have inconsistent complete bytes')
    for name, raw_material in raw_materials.items():
        if plan['files'][name].encode('utf-8') != raw_material:
            raise ValueError('Original native preparation changes frozen raw configuration material')
    manifest = _document(raw.decode(), 'frozen native manifest')
    expected = {**request['experiment'], 'candidate_sha': request['experiment']['candidate_commit'],
                'baseline_sha': request['experiment']['baseline_commit'], 'runner_template_id': request['runner_template_id'],
                'max_run_seconds': request['max_run_seconds'], 'local_project': project['id'], 'configuration_inputs': inputs}
    require_driver(manifest, runner)
    if not _identical(manifest, expected):
        raise ValueError('Original native manifest changes the frozen candidate or performance policy')
    spec_raw = plan['files'][targets[2]].encode('utf-8')
    if len(spec_raw) > MAX_CONFIG_BYTES:
        raise ValueError('Original native spec exceeds its read capacity')
    spec = _document(spec_raw.decode(), 'frozen native spec')
    expected_spec = {'binding': {'experiment_id': ident, 'manifest_sha': _raw_sha(raw),
                                'candidate_sha': template['candidate_commit'], 'baseline_sha': template['baseline_commit']},
                     'manifest_uri': (PurePosixPath(plan['execution']['state_directory']) / targets[0]).as_uri(),
                     'poll_seconds': 30, 'max_run_seconds': request['max_run_seconds'],
                     'release_wait_seconds': 86400, 'cancel_wait_seconds': 60}
    if not _identical(spec, expected_spec):
        raise ValueError('Original native spec differs from its manifest bytes or immutable binding')


def _packet(packet, files, materials):
    _exact(packet, _PACKET_FIELDS, 'training search packet')
    if (type(packet['schema_version']) is not int or packet['schema_version'] != 2
            or packet['kind'] != 'training-search-preparation' or not _identical(packet['coverage'], _COVERAGE)):
        raise ValueError('Unsupported training search preparation version or coverage')
    request, _, cardinality = _request(packet['request'])
    if (_sha(request) != packet['request_sha256'] or type(packet['cardinality']) is not int
            or packet['cardinality'] != cardinality):
        raise ValueError('Frozen search request identity or cardinality differs')
    _exact(packet['project'], {'id', 'repo', 'revision', 'registration_sha256'}, 'search project binding')
    project = packet['project']
    if (not isinstance(project['id'], str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}', project['id']) is None
            or not isinstance(project['repo'], str) or not PurePosixPath(project['repo']).is_absolute()
            or type(project['revision']) is not int or project['revision'] < 1
            or not isinstance(packet['control_home'], str) or not PurePosixPath(packet['control_home']).is_absolute()):
        raise ValueError('Invalid frozen search project or control-directory identity')
    _digest(project['registration_sha256'])
    _exact(packet['candidate_source'], {'kind', 'records'}, 'frozen candidate source')
    if packet['candidate_source']['kind'] != request['candidate_source']['kind']:
        raise ValueError('Frozen candidate source protocol differs')
    _source(request, packet['project'], packet['candidate_source']['records'])
    _check_material_scope(request, project, materials)
    original_materials = {'path': _MATERIAL_PATH, 'sha256': materials['packet_sha256'],
                          'bytes': len(files[_MATERIAL_PATH]), 'index_sha256': materials['index_sha256'],
                          'selection_sha256': materials['sha256']}
    if (not _identical(packet['preparation_materials'], original_materials)
            or _raw_sha(files[_MATERIAL_PATH]) != materials['packet_sha256']):
        raise ValueError('Frozen preparation materials differ from their complete original packet')
    policy = _legacy_performance_policy_v1(request)
    allocation = {'max_trials': request['selection']['max_trials'],
                  'enabled_thresholds': sum(value is not None for key, value in policy['thresholds'].items() if key != 'mode')}
    _exact(packet['family_allocation'], allocation, 'family allocation')
    if (not _identical(packet['performance_policy'], policy)
            or packet['performance_policy_sha256'] != _sha(packet['performance_policy'])
            or any(type(value) is not int for value in packet['family_allocation'].values())
            or packet['family_allocation'] != allocation):
        raise ValueError('Frozen family allocation or three-key performance policy differs')
    raw = request['baseline_configuration']['utf8'].encode('utf-8')
    baseline = {'path': 'baseline-config.json', 'sha256': _raw_sha(raw), 'bytes': len(raw)}
    if not _identical(packet['baseline_configuration'], baseline) or files.get(baseline['path']) != raw:
        raise ValueError('Frozen baseline configuration does not preserve its original raw bytes')
    selected = _selected_v1(request)  # Verify this frozen algorithm; never replace saved choices.
    if not isinstance(packet['choices'], list) or len(packet['choices']) != len(selected):
        raise ValueError('Frozen search must retain the exact complete selected sequence')
    expected_files, seen_ids, seen_configs, sources = {'baseline-config.json', _MATERIAL_PATH}, set(), set(), None
    for ordinal, (choice, (grid_ordinal, combination)) in enumerate(zip(packet['choices'], selected)):
        _exact(choice, _CHOICE_FIELDS, 'frozen search choice')
        expected, config_raw = _choice(request, packet['project'], ordinal, grid_ordinal, combination)
        if any(not _identical(choice[key], expected[key]) for key in expected if key != 'stages'):
            raise ValueError('Frozen search choice changes its original order or configuration')
        path = choice['configuration']['path']
        if choice['configuration']['sha256'] in seen_configs:
            raise ValueError('Duplicate generated complete configuration')
        if files.get(path) != config_raw:
            raise ValueError('Generated configuration bytes differ from their frozen identity')
        expected_files.add(path)
        seen_configs.add(choice['configuration']['sha256'])
        _exact(choice['stages'], {'screen', 'full'}, 'frozen search stages')
        for name in ('screen', 'full'):
            stage = choice['stages'][name]
            _exact(stage, _STAGE_FIELDS, 'frozen native stage')
            if any(not _identical(stage[key], item) for key, item in expected['stages'][name].items()):
                raise ValueError('Frozen native stage changes its original ID, source, configuration, reference or policy')
            if stage['experiment_id'] in seen_ids:
                raise ValueError('Duplicate generated stage experiment ID')
            seen_ids.add(stage['experiment_id'])
            _check_native(packet, stage)
            if sources is not None and sources != stage['native_plan']['sources']:
                raise ValueError('Frozen stages do not share the same original baseline and runner sources')
            sources = stage['native_plan']['sources']
    if set(files) != expected_files:
        raise ValueError('Training search packet contains missing or additional configuration files')


def _check_project(state, project_id, packet):
    import ergora.training.application as training

    project = training._project(state, project_id)
    if _binding(project) != packet['project'] or str(state.root) != packet['control_home']:
        raise ValueError('Search project revision or registration changed; retain the original packet')
    return project


def _check_sources(state, project, packet, materials):
    if not _identical(_capture_source(state, project, packet['request']), packet['candidate_source']):
        raise ValueError('Original candidate creation or export source changed')
    execution = project['registration']['definition']['execution']
    _authenticate_materials(state, project, packet['request'], materials)
    if materials['sha256'] != packet['preparation_materials']['selection_sha256']:
        raise ValueError('Original complete preparation source materials changed')
    plan = packet['choices'][0]['stages']['screen']['native_plan']
    if plan['execution'] != execution:
        raise ValueError('Search native execution directories changed')
    # These are the original preparation owner's two immutable source paths,
    # read only for drift. Publication and recovery still belong to that owner.
    paths = {'baseline': Path(execution['state_directory']) / 'training/projects' / project['id'] / 'perf/baseline.json',
             'runner': Path(execution['config_directory']) / 'training-runners' /
                       (packet['request']['runner']['runner_template_id'] + '.json')}
    for name, path in paths.items():
        raw = _file(path, MAX_CONFIG_BYTES)
        source = plan['sources'][name]
        if (_raw_sha(raw) != source['file_sha256']
                or not _identical(_document(raw.decode(), 'original ' + name), source['document'])):
            raise ValueError('Original preparation baseline or runner source changed: ' + name)


def authenticate_preparation(state: State, project_id: str, saved: dict) -> None:
    """Reconcile the complete saved package with its original project and task sources."""
    checked = read(Path(saved['directory']), sha256=saved['sha256'])
    packet = checked['plan']
    if (saved['preview_sha256'] != checked['preview_sha256'] or not _identical(saved['plan'], packet)
            or not _identical(saved['preparation_materials'], checked['preparation_materials'])):
        raise ValueError('Search preparation differs from its complete frozen packet')
    project = _check_project(state, project_id, packet)
    _check_sources(state, project, packet, checked['preparation_materials'])



def _cpu_request(project, request):
    if request.get('cpu_execution_contract') is None:
        return request
    from ergora.training.configuration import bind_cpu_execution_contract
    execution = project['registration']['definition']['execution']
    path = Path(execution['config_directory']) / 'training-runners' / (request['runner']['runner_template_id'] + '.json')
    runner = _document(_file(path, MAX_CONFIG_BYTES).decode('utf-8'), 'original CPU runner')
    return {**request, 'cpu_execution_contract': bind_cpu_execution_contract(request['cpu_execution_contract'], runner)}


def preview(state: State, project_id: str, request: dict) -> dict:
    """Build a complete finite packet through original native previews, without publication."""
    import ergora.training.application as training

    request, _, cardinality = _request(request)

    project = training._project(state, project_id)
    request = _cpu_request(project, request)
    binding = _binding(project)
    policy = _legacy_performance_policy_v1(request)
    materials, material_raw = _capture_materials(state, project, request)
    packet = {'schema_version': 2, 'kind': 'training-search-preparation', 'control_home': str(state.root),
              'project': binding, 'request': request, 'request_sha256': _sha(request),
              'candidate_source': _capture_source(state, project, request), 'cardinality': cardinality,
              'family_allocation': {'max_trials': request['selection']['max_trials'],
                    'enabled_thresholds': sum(value is not None for key, value in policy['thresholds'].items() if key != 'mode')},
              'performance_policy': policy, 'performance_policy_sha256': _sha(policy),
              'baseline_configuration': {'path': 'baseline-config.json', 'sha256': request['baseline_configuration']['sha256'],
                                         'bytes': len(request['baseline_configuration']['utf8'].encode('utf-8'))},
              'preparation_materials': {'path': _MATERIAL_PATH, 'sha256': materials['packet_sha256'],
                  'bytes': len(material_raw), 'index_sha256': materials['index_sha256'],
                  'selection_sha256': materials['sha256']},
              'choices': [], 'coverage': dict(_COVERAGE)}
    files = {'baseline-config.json': request['baseline_configuration']['utf8'].encode('utf-8'),
             _MATERIAL_PATH: material_raw}
    observations = []
    for ordinal, (grid, combination) in enumerate(_selected_v1(request)):
        choice, raw = _choice(request, binding, ordinal, grid, combination)
        stage_observations = {}
        for name, stage in choice['stages'].items():
            checked = training.preview_experiment(state, project_id, **stage['native_request'])
            stage.update(native_preview_sha256=checked['preview_sha256'], native_plan=checked['plan'])
            observed = checked['preparation']
            if observed['status'] != 'not_recorded' and (observed.get('intent') is None
                    or _sha(preparation_preview_body(observed['intent'])) != checked['preview_sha256']):
                raise ValueError('Generated stage ID is already occupied outside its original preparation')
            stage_observations[name] = observed
        packet['choices'].append(choice)
        files[choice['configuration']['path']] = raw
        observations.append(stage_observations)
        _check_project(state, project_id, packet)
    raw = _config_bytes(packet)
    if len(raw) + sum(map(len, files.values())) > MAX_PACKAGE_BYTES:
        raise ValueError('Complete search package exceeds 10 MB; nothing was published')
    # Request limits do not imply that the wrapped packet (including all
    # native plans) fits the reader's aggregate depth and value limits.
    packet = _decode_packet(raw)
    try:
        _packet(packet, files, materials)
    except (KeyError, TypeError, AttributeError, OverflowError) as error:
        raise ValueError('Frozen search packet has malformed original records or configuration data') from error
    _check_sources(state, project, packet, materials)
    return {'project': project_id, 'project_revision': project['revision'], 'preview_sha256': _sha(packet),
            'plan': packet, 'preparation': observations, 'coverage': dict(_COVERAGE)}


def read(directory: Path, *, sha256: str | None = None) -> dict:
    """Verify a complete original packet offline, including original selected configurations."""
    directory = Path(directory).expanduser().absolute()
    initial_digest, inventory, directories = inventory_tree(directory, label='Training search', max_directories=2, max_depth=1)
    nodes = [directory, *(directory / name for name in [*inventory, *directories])]
    identities = {path: path.lstat() for path in nodes}
    if directories != ['configs', 'materials'] or 'search.json' not in inventory or len(inventory) > 35:
        raise ValueError('Training search requires exactly its manifest, baseline and chosen configurations')
    raw = _file(directory / 'search.json', MAX_PACKAGE_BYTES)
    digest = _raw_sha(raw)
    if sha256 is not None and sha256 != digest:
        raise ValueError('Training search packet differs from the expected raw SHA256')
    packet = _decode_packet(raw)
    files = {name: _file(directory / name, MAX_PACKAGE_BYTES if name == _MATERIAL_PATH else MAX_CONFIG_BYTES)
             for name in inventory if name != 'search.json'}
    if len(raw) + sum(map(len, files.values())) > MAX_PACKAGE_BYTES:
        raise ValueError('Complete search package exceeds 10 MB')
    _request(packet.get('request'))
    try:
        materials = _material_selection(packet['request'], directory)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('Frozen preparation source lacks complete original records') from error
    if any(_raw_sha((raw if name == 'search.json' else files[name])) != item['sha256']
           for name, item in inventory.items()):
        raise ValueError('Training search files changed during complete inventory read')
    try:
        _packet(packet, files, materials)
    except (KeyError, TypeError, AttributeError, OverflowError) as error:
        raise ValueError('Frozen search packet has malformed original records or configuration data') from error
    if (inventory_tree(directory, label='Training search', max_directories=2, max_depth=1)[0] != initial_digest
            or any(not os.path.samestat(details, path.lstat()) or is_link(path)
                   or (details.st_size, details.st_mtime_ns, details.st_ctime_ns)
                      != (path.lstat().st_size, path.lstat().st_mtime_ns, path.lstat().st_ctime_ns)
                   for path, details in identities.items())):
        raise ValueError('Training search package changed during complete offline read')
    return {'directory': str(directory), 'sha256': digest, 'preview_sha256': _sha(packet), 'plan': packet,
            'native_preparation_status': 'not_queried', 'preparation_materials': materials, 'coverage': dict(_COVERAGE)}


def _durable_packet(directory, expected_sha256):
    """Complete local input durability before the original owner creates an intent."""
    _, inventory, _ = inventory_tree(directory, label='Training search', max_directories=2, max_depth=1)
    for name in inventory:
        with (directory / name).open('rb') as stream:
            os.fsync(stream.fileno())
    # The caller may have just created several destination ancestors. Sync
    # every pathname link, including on retry after an earlier sync failure.
    for path in (directory / 'configs', directory / 'materials', directory, *directory.parents):
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return read(directory, sha256=expected_sha256)


def prepare(state: State, project_id: str, request: dict, expected_revision: int,
            preview_sha256: str, destination: Path) -> dict:
    """Publish input once, then prepare or resume each exact original native intent."""
    import ergora.training.application as training

    request, _, _ = _request(request)

    project = training._project(state, project_id)
    request = _cpu_request(project, request)
    if type(expected_revision) is not int or expected_revision != project['revision']:
        raise ValueError('Project revision changed; preview search preparation again')
    destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        saved = read(destination)
        packet = saved['plan']
        if saved['preview_sha256'] != preview_sha256 or not _identical(packet['request'], request):
            raise ValueError('Search destination belongs to a different original preview or request')
    else:
        checked = preview(state, project_id, request)
        if checked['preview_sha256'] != preview_sha256:
            raise ValueError('Confirm the exact original search preparation preview SHA256')
        packet = checked['plan']
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.training-search-', dir=destination.parent) as temporary:
            staged = Path(temporary) / 'packet'
            (staged / 'configs').mkdir(parents=True)
            (staged / 'materials').mkdir()
            _, materials_raw = _capture_materials(state, project, request)
            (staged / _MATERIAL_PATH).write_bytes(materials_raw)
            (staged / 'search.json').write_bytes(_config_bytes(packet))
            (staged / 'baseline-config.json').write_bytes(request['baseline_configuration']['utf8'].encode('utf-8'))
            for choice in packet['choices']:
                _, raw = _choice(request, packet['project'], choice['ordinal'], choice['grid_ordinal'], choice['combination'])
                (staged / choice['configuration']['path']).write_bytes(raw)
            saved = read(staged)
            _check_project(state, project_id, packet)
            _check_sources(state, project, packet, saved['preparation_materials'])
            publish_directory(staged, destination)
        saved = read(destination)
    # A visible rename or a previous lost reply is not a durability receipt.
    # Existing packets use the same files and IDs, then sync and read them back.
    saved = _durable_packet(destination, saved['sha256'])
    packet = saved['plan']
    _check_project(state, project_id, packet)
    _check_sources(state, project, packet, saved['preparation_materials'])
    results = []
    for logical_choice in packet['choices']:
        for name in ('screen', 'full'):
            choice = logical_choice['stages'][name]
            ident = choice['experiment_id']
            try:
                authenticate_preparation(state, project_id, saved)
                observed = training.preparation(state, project_id, ident)
                if observed['status'] == 'not_recorded':
                    observed = training.prepare_experiment(state, project_id, expected_revision=expected_revision,
                        preview_sha256=choice['native_preview_sha256'], **choice['native_request'])
                elif observed['status'] in ('intent_saved', 'partially_prepared', 'prepared'):
                    from ergora.training.materials import validate_preparation_intent
                    checked_intent = validate_preparation_intent(observed['intent'])
                    if not _identical(checked_intent['body'], choice['native_plan']) or checked_intent['preview_sha256'] != choice['native_preview_sha256']:
                        raise ValueError('Native preparation belongs to a different original intent')
                    if observed['status'] != 'prepared':
                        observed = training.resume_prepare(state, project_id, ident, expected_revision, observed['intent_sha256'])
                else:
                    raise ValueError('Original native preparation cannot be resumed from ' + observed['status'])
                if observed['status'] != 'prepared' or not _identical(preparation_preview_body(observed['intent']), choice['native_plan']):
                    raise ValueError('Original native preparation did not return its exact completed plan')
                authenticate_preparation(state, project_id, saved)
                manifest = choice['native_plan']['files']['training/manifests/' + ident + '.json'].encode('utf-8')
                results.append({'ordinal': logical_choice['ordinal'], 'stage': name, 'experiment_id': ident, 'status': observed['status'],
                                'intent_sha256': observed['intent_sha256'], 'confirmed_preview_sha256': observed['confirmed_preview_sha256'], 'manifest_sha256': _raw_sha(manifest)})
            except (OSError, ValueError, KeyError, TypeError) as error:
                raise ValueError('Search packet ' + saved['sha256'] + ' stopped at original experiment ' + ident + ': ' + str(error)) from error
    return {'directory': str(destination), 'sha256': saved['sha256'], 'project': project_id,
            'project_revision': expected_revision, 'status': 'prepared', 'experiments': results,
            'coverage': dict(_COVERAGE)}
