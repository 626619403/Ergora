"""Finite configuration preparation, using the original native publication owner.

This preparation does not execute candidates or start a budget. Its offline reader verifies
content and links, not execution authority or current native state.
"""

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

from jsonschema.exceptions import SchemaError

from . import contracts, tasks, training
from .asset_trees import inventory_tree, is_link, publish_directory
from .definition_bundles import parse_json
from .state import State
from .training_materials import material_plan, relative, require_driver


MAX_REQUEST_BYTES = 1_048_576
MAX_CONFIG_BYTES = 1_048_576
MAX_PACKAGE_BYTES = 10_000_000
_SCHEMA = json.loads((Path(__file__).parent / 'data/schemas/training-search-v1.json').read_text())
_COVERAGE = {'operation': 'preparation-only', 'origin_authenticated': False,
             'runtime_status': 'not_queried', 'execution_authorized': False,
             'budget_started': False, 'configuration_execution': 'requires-original-managed-full'}
_PACKET_FIELDS = {'schema_version', 'kind', 'control_home', 'project', 'request', 'request_sha256',
                  'candidate_source', 'cardinality', 'family_allocation', 'performance_policy',
                  'performance_policy_sha256', 'baseline_configuration', 'choices', 'coverage'}
_CHOICE_FIELDS = {'ordinal', 'grid_ordinal', 'combination', 'variant_id', 'experiment_id',
                  'configuration', 'native_request', 'native_preview_sha256', 'native_plan'}


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _sha(value):
    return hashlib.sha256(_encode(value)).hexdigest()


def _raw_sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _decode_packet(raw):
    if len(raw) > MAX_PACKAGE_BYTES:
        raise ValueError('Complete search package manifest exceeds 10 MB')
    return parse_json(raw.decode('utf-8'), 'training search packet', finite=True, bounded=True)


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
    if is_link(path) or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('Training search requires ordinary files: ' + str(path))
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Complete training search file exceeds its capacity: ' + path.name)
    return raw


def read_request(path: Path) -> dict:
    """Read one complete strict JSON document; never import a Python recipe."""
    return parse_json(_file(path, MAX_REQUEST_BYTES).decode('utf-8-sig'), 'training search request',
                      finite=True, bounded=True)


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
    value = parse_json(raw.decode(), 'training search request', finite=True, bounded=True)
    contracts.validate(value, _SCHEMA, 'Training search request')
    # JSON Schema patterns use search semantics; '$' may precede a final LF.
    # These identifiers and the decimal policy have a whole-string contract.
    if re.fullmatch(r'0\.[0-9]*[1-9]', value['family_policy']['family_error_budget']) is None:
        raise ValueError('Family error budget must be a canonical decimal string')
    identifiers = [(value['search_id'], 40), (value['runner']['runner_template_id'], 80),
                   (value['experiment_template']['baseline_id'], 80)]
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
    for key in ('source_flow_sha256', 'redundancy_sha256'):
        _digest(value['analysis'][key])
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
    base = parse_json(original.decode('utf-8-sig'), 'baseline configuration', finite=True, bounded=True)
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
    variant = _sha(['training-search-v1', project, _sha(request), ordinal, grid_ordinal, combination, digest])
    ident = request['search_id'] + '-' + f'{ordinal:02d}' + '-' + variant[:16]
    policy = _legacy_performance_policy_v1(request)
    # Original native serialization preserves insertion order. Normalize the
    # request before its first native preview so readback cannot change bytes.
    native = parse_json(_encode({'experiment': {**request['experiment_template'], 'experiment_id': ident,
                 'candidate_config_sha256': digest, 'performance_policy': policy}, **request['runner'],
                 'configuration_materials': {'format': 'json-v1',
                     'baseline': {'utf8': request['baseline_configuration']['utf8'],
                                  'sha256': request['baseline_configuration']['sha256']},
                     'candidate': {'utf8': raw.decode('utf-8'), 'sha256': digest}}}).decode(),
                 'generated native request', finite=True, bounded=True)
    return {'ordinal': ordinal, 'grid_ordinal': grid_ordinal, 'combination': combination, 'variant_id': variant,
            'experiment_id': ident, 'configuration': {'path': 'configs/' + ident + '.json',
                                                    'sha256': digest, 'bytes': len(raw)},
            'native_request': native}, raw


def _check_native(packet, choice):
    plan, request = choice['native_plan'], choice['native_request']
    fields = {'schema_version', 'operation', 'control_home', 'project', 'repo', 'execution', 'registration_sha256',
              'experiment_id', 'project_revision', 'request', 'sources', 'files'}
    _exact(plan, fields, 'original native preparation plan')
    project, ident = packet['project'], choice['experiment_id']
    if (type(plan['schema_version']) is not int or plan['schema_version'] != 1 or plan['operation'] != 'prepare-training'
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
    _exact(capability, {'protocol', 'source', 'prepared_json_format', 'manifest_configuration_role', 'observation_scheme', 'baseline_reference_protocol'},
           'frozen configuration readback')
    if (capability['baseline_reference_protocol'] not in (None, 'baseline-reference-v1')
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
    manifest = parse_json(raw.decode(), 'frozen native manifest', finite=True, bounded=True)
    expected = {**request['experiment'], 'candidate_sha': request['experiment']['candidate_commit'],
                'baseline_sha': request['experiment']['baseline_commit'], 'runner_template_id': request['runner_template_id'],
                'max_run_seconds': request['max_run_seconds'], 'local_project': project['id'], 'configuration_inputs': inputs}
    require_driver(manifest, runner)
    if not _identical(manifest, expected):
        raise ValueError('Original native manifest changes the frozen candidate or performance policy')
    spec_raw = plan['files'][targets[2]].encode('utf-8')
    if len(spec_raw) > MAX_CONFIG_BYTES:
        raise ValueError('Original native spec exceeds its read capacity')
    spec = parse_json(spec_raw.decode(), 'frozen native spec', finite=True, bounded=True)
    expected_spec = {'binding': {'experiment_id': ident, 'manifest_sha': _raw_sha(raw),
                                'candidate_sha': template['candidate_commit'], 'baseline_sha': template['baseline_commit']},
                     'manifest_uri': (PurePosixPath(plan['execution']['state_directory']) / targets[0]).as_uri(),
                     'poll_seconds': 30, 'max_run_seconds': request['max_run_seconds'],
                     'release_wait_seconds': 86400, 'cancel_wait_seconds': 60}
    if not _identical(spec, expected_spec):
        raise ValueError('Original native spec differs from its manifest bytes or immutable binding')


def _packet(packet, files):
    _exact(packet, _PACKET_FIELDS, 'training search packet')
    if (type(packet['schema_version']) is not int or packet['schema_version'] != 1
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
    expected_files, seen_ids, seen_configs, sources = {'baseline-config.json'}, set(), set(), None
    for ordinal, (choice, (grid_ordinal, combination)) in enumerate(zip(packet['choices'], selected)):
        _exact(choice, _CHOICE_FIELDS, 'frozen search choice')
        expected, config_raw = _choice(request, packet['project'], ordinal, grid_ordinal, combination)
        if any(not _identical(choice[key], item) for key, item in expected.items()):
            raise ValueError('Frozen search choice changes its original order, configuration or native request')
        ident, path = choice['experiment_id'], choice['configuration']['path']
        if ident in seen_ids or choice['configuration']['sha256'] in seen_configs:
            raise ValueError('Duplicate generated experiment ID or complete configuration')
        if files.get(path) != config_raw:
            raise ValueError('Generated configuration bytes differ from their frozen identity')
        expected_files.add(path)
        seen_ids.add(ident)
        seen_configs.add(choice['configuration']['sha256'])
        _check_native(packet, choice)
        if sources is not None and sources != choice['native_plan']['sources']:
            raise ValueError('Frozen candidates do not share the same original baseline and runner sources')
        sources = choice['native_plan']['sources']
    if set(files) != expected_files:
        raise ValueError('Training search packet contains missing or additional configuration files')


def _check_project(state, project_id, packet):
    project = training._project(state, project_id)
    if _binding(project) != packet['project'] or str(state.root) != packet['control_home']:
        raise ValueError('Search project revision or registration changed; retain the original packet')
    return project


def _check_sources(state, project, packet):
    if not _identical(_capture_source(state, project, packet['request']), packet['candidate_source']):
        raise ValueError('Original candidate creation or export source changed')
    execution = project['registration']['definition']['execution']
    plan = packet['choices'][0]['native_plan']
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
                or not _identical(parse_json(raw.decode(), 'original ' + name, finite=True), source['document'])):
            raise ValueError('Original preparation baseline or runner source changed: ' + name)


def preview(state: State, project_id: str, request: dict) -> dict:
    """Build a complete finite packet through original native previews, without publication."""
    request, _, cardinality = _request(request)
    project = training._project(state, project_id)
    binding = _binding(project)
    policy = _legacy_performance_policy_v1(request)
    packet = {'schema_version': 1, 'kind': 'training-search-preparation', 'control_home': str(state.root),
              'project': binding, 'request': request, 'request_sha256': _sha(request),
              'candidate_source': _capture_source(state, project, request), 'cardinality': cardinality,
              'family_allocation': {'max_trials': request['selection']['max_trials'],
                    'enabled_thresholds': sum(value is not None for key, value in policy['thresholds'].items() if key != 'mode')},
              'performance_policy': policy, 'performance_policy_sha256': _sha(policy),
              'baseline_configuration': {'path': 'baseline-config.json', 'sha256': request['baseline_configuration']['sha256'],
                                         'bytes': len(request['baseline_configuration']['utf8'].encode('utf-8'))},
              'choices': [], 'coverage': dict(_COVERAGE)}
    files = {'baseline-config.json': request['baseline_configuration']['utf8'].encode('utf-8')}
    observations = []
    for ordinal, (grid, combination) in enumerate(_selected_v1(request)):
        choice, raw = _choice(request, binding, ordinal, grid, combination)
        checked = training.preview_experiment(state, project_id, **choice['native_request'])
        choice.update(native_preview_sha256=checked['preview_sha256'], native_plan=checked['plan'])
        observed = checked['preparation']
        if observed['status'] != 'not_recorded' and (observed.get('intent') is None
                or _sha(observed['intent']) != checked['preview_sha256']):
            raise ValueError('Generated experiment ID is already occupied outside its original preparation')
        packet['choices'].append(choice)
        files[choice['configuration']['path']] = raw
        observations.append(observed)
        _check_project(state, project_id, packet)
    raw = _config_bytes(packet)
    if len(raw) + sum(map(len, files.values())) > MAX_PACKAGE_BYTES:
        raise ValueError('Complete search package exceeds 10 MB; nothing was published')
    # Request limits do not imply that the wrapped packet (including all
    # native plans) fits the reader's aggregate depth and value limits.
    packet = _decode_packet(raw)
    try:
        _packet(packet, files)
    except (KeyError, TypeError, AttributeError, OverflowError) as error:
        raise ValueError('Frozen search packet has malformed original records or configuration data') from error
    _check_sources(state, project, packet)
    return {'project': project_id, 'project_revision': project['revision'], 'preview_sha256': _sha(packet),
            'plan': packet, 'preparation': observations, 'coverage': dict(_COVERAGE)}


def read(directory: Path, *, sha256: str | None = None) -> dict:
    """Verify a complete original packet offline, including original selected configurations."""
    directory = Path(directory).expanduser().absolute()
    _, inventory, directories = inventory_tree(directory, label='Training search', max_directories=1, max_depth=1)
    if directories != ['configs'] or 'search.json' not in inventory or len(inventory) > 34:
        raise ValueError('Training search requires exactly its manifest, baseline and chosen configurations')
    raw = _file(directory / 'search.json', MAX_PACKAGE_BYTES)
    digest = _raw_sha(raw)
    if sha256 is not None and sha256 != digest:
        raise ValueError('Training search packet differs from the expected raw SHA256')
    packet = _decode_packet(raw)
    files = {name: _file(directory / name, MAX_CONFIG_BYTES) for name in inventory if name != 'search.json'}
    try:
        _packet(packet, files)
    except (KeyError, TypeError, AttributeError, OverflowError) as error:
        raise ValueError('Frozen search packet has malformed original records or configuration data') from error
    return {'directory': str(directory), 'sha256': digest, 'preview_sha256': _sha(packet), 'plan': packet,
            'native_preparation_status': 'not_queried', 'coverage': dict(_COVERAGE)}


def _durable_packet(directory, expected_sha256):
    """Complete local input durability before the original owner creates an intent."""
    _, inventory, _ = inventory_tree(directory, label='Training search', max_directories=1, max_depth=1)
    for name in inventory:
        with (directory / name).open('rb') as stream:
            os.fsync(stream.fileno())
    # The caller may have just created several destination ancestors. Sync
    # every pathname link, including on retry after an earlier sync failure.
    for path in (directory / 'configs', directory, *directory.parents):
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return read(directory, sha256=expected_sha256)


def prepare(state: State, project_id: str, request: dict, expected_revision: int,
            preview_sha256: str, destination: Path) -> dict:
    """Publish input once, then prepare or resume each exact original native intent."""
    request, _, _ = _request(request)
    project = training._project(state, project_id)
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
            (staged / 'search.json').write_bytes(_config_bytes(packet))
            (staged / 'baseline-config.json').write_bytes(request['baseline_configuration']['utf8'].encode('utf-8'))
            for choice in packet['choices']:
                _, raw = _choice(request, packet['project'], choice['ordinal'], choice['grid_ordinal'], choice['combination'])
                (staged / choice['configuration']['path']).write_bytes(raw)
            read(staged)
            _check_project(state, project_id, packet)
            _check_sources(state, project, packet)
            publish_directory(staged, destination)
        saved = read(destination)
    # A visible rename or a previous lost reply is not a durability receipt.
    # Existing packets use the same files and IDs, then sync and read them back.
    saved = _durable_packet(destination, saved['sha256'])
    packet = saved['plan']
    _check_project(state, project_id, packet)
    _check_sources(state, project, packet)
    results = []
    for choice in packet['choices']:
        ident = choice['experiment_id']
        try:
            _check_project(state, project_id, packet)
            _check_sources(state, project, packet)
            observed = training.preparation(state, project_id, ident)
            if observed['status'] == 'not_recorded':
                observed = training.prepare_experiment(state, project_id, expected_revision=expected_revision,
                    preview_sha256=choice['native_preview_sha256'], **choice['native_request'])
            elif observed['status'] in ('intent_saved', 'partially_prepared', 'prepared'):
                if not _identical(observed.get('intent'), choice['native_plan']) or observed.get('intent_sha256') != choice['native_preview_sha256']:
                    raise ValueError('Native preparation belongs to a different original intent')
                if observed['status'] != 'prepared':
                    observed = training.resume_prepare(state, project_id, ident, expected_revision, observed['intent_sha256'])
            else:
                raise ValueError('Original native preparation cannot be resumed from ' + observed['status'])
            if observed['status'] != 'prepared' or not _identical(observed.get('intent'), choice['native_plan']):
                raise ValueError('Original native preparation did not return its exact completed plan')
            _check_project(state, project_id, packet)
            _check_sources(state, project, packet)
            manifest = choice['native_plan']['files']['training/manifests/' + ident + '.json'].encode('utf-8')
            results.append({'experiment_id': ident, 'status': observed['status'],
                            'intent_sha256': observed['intent_sha256'], 'manifest_sha256': _raw_sha(manifest)})
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ValueError('Search packet ' + saved['sha256'] + ' stopped at original experiment ' + ident + ': ' + str(error)) from error
    return {'directory': str(destination), 'sha256': saved['sha256'], 'project': project_id,
            'project_revision': expected_revision, 'status': 'prepared', 'experiments': results,
            'coverage': dict(_COVERAGE)}
