"""Source-pinned configuration construction inside one managed full runner."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import runpy
import subprocess
import sys


PROTOCOL = 'training-configuration-driver-v1'
INVARIANTS = ('model_algorithm', 'model_structure', 'model_size', 'precision_policy', 'objective')
WORKLOAD = ('dataset', 'initial_checkpoint', 'window', 'global_batch', 'microbatch',
            'accumulation', 'normalization', 'optimizer', 'schedule', 'layout')
LIMIT = 1_048_576


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(label + ' has unsupported or missing fields')


def _sha(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _bytes(value, limit=LIMIT):
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


def _digest(value, label):
    if not isinstance(value, str) or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError(label + ' requires a complete SHA-256')


def _relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or '\x00' in value
            or PurePosixPath(value).is_absolute() or str(PurePosixPath(value)) != value
            or any(part in ('.', '..') for part in value.split('/'))):
        raise ValueError('Configuration source paths must be ordinary relative paths')
    return value


def _file(root, relative):
    root = Path(root)
    path = root / _relative(relative)
    for selected in (path, *path.parents):
        if selected.is_symlink():
            raise ValueError('Configuration sources cannot use symlinks')
    if not path.is_file():
        raise ValueError('Configuration source is not an ordinary file: ' + str(path))
    return path


def _git(repo, *arguments):
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull, '-C', str(repo), *arguments],
                            env=environment, capture_output=True, timeout=120)
    if result.returncode:
        raise ValueError('Configuration source Git operation failed: ' + arguments[0])
    return result.stdout


def source_reference(repo: Path, commit: str, entrypoint: str) -> dict:
    """Observe exact tracked driver source without importing or executing it."""
    repo = Path(repo).expanduser().resolve(strict=True)
    if Path(_git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != repo:
        raise ValueError('Configuration driver must name a Git repository root')
    if not isinstance(commit, str) or re.fullmatch('[a-f0-9]{40}', commit) is None:
        raise ValueError('Configuration driver requires a complete source commit')
    _relative(entrypoint)
    if _git(repo, 'rev-parse', commit + '^{commit}').decode().strip() != commit:
        raise ValueError('Configuration driver commit differs from its source')
    inventory = _git(repo, 'ls-tree', '-r', '-z', '--full-tree', commit)
    found = False
    for record in inventory.split(b'\0'):
        if not record:
            continue
        metadata, name = record.split(b'\t', 1)
        mode, kind, _ = metadata.split(b' ')
        if mode not in (b'100644', b'100755') or kind != b'blob':
            raise ValueError('Configuration driver inventory requires ordinary tracked files')
        if name.decode('utf-8') == entrypoint:
            found = True
    if not found:
        raise ValueError('Configuration driver entrypoint is absent from its source inventory')
    return {'repo': str(repo), 'commit': commit,
            'inventory_sha256': hashlib.sha256(inventory).hexdigest(), 'entrypoint': entrypoint}


def validate_runner(runner: dict) -> None:
    """Validate the versioned contract shared by registration and admission."""
    fields = ('schema_version', 'runner_template_id', 'project', 'repo', 'command', 'timeout_seconds',
              'configuration_readback')
    version = runner.get('schema_version') if isinstance(runner, dict) else None
    if type(version) is not int or version != 2:
        raise ValueError('Unsupported runner schema_version; it must be an integer')
    _exact(runner, fields, 'Runner')
    if (not isinstance(runner['command'], list) or not runner['command']
            or not all(isinstance(arg, str) and arg for arg in runner['command'])
            or type(runner['timeout_seconds']) is not int or not 1 <= runner['timeout_seconds'] <= 82800):
        raise ValueError('Trusted runner command or execution walltime is invalid')
    capability = runner['configuration_readback']
    if capability is None:
        return
    _exact(capability, ('protocol', 'source', 'prepared_json_format', 'manifest_configuration_role',
                        'observation_scheme', 'baseline_reference_protocol'), 'Configuration readback')
    if capability['baseline_reference_protocol'] not in (None, 'baseline-reference-v1'):
        raise ValueError('Unsupported baseline reference protocol')
    if capability['protocol'] != PROTOCOL or capability['manifest_configuration_role'] != 'source-bytes':
        raise ValueError('Unsupported configuration driver protocol or manifest configuration role')
    if (not isinstance(capability['observation_scheme'], str)
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', capability['observation_scheme']) is None):
        raise ValueError('Configuration driver requires a versioned observation scheme')
    if capability['prepared_json_format'] not in (None, 'json-v1'):
        raise ValueError('Unsupported declared prepared JSON format')
    source = capability['source']
    _exact(source, ('repo', 'commit', 'inventory_sha256', 'entrypoint'), 'Configuration driver source')
    if source_reference(Path(source['repo']), source['commit'], source['entrypoint']) != source:
        raise ValueError('Configuration driver source inventory differs from its frozen reference')
    if (len(runner['command']) != 3 or not Path(runner['command'][0]).is_absolute()
            or runner['command'][1:] != ['{configuration_driver}', '{configuration_request}']):
        raise ValueError('Configuration driver command requires the fixed core wrapper ABI')


def _checkout(repo, commit):
    repo = Path(repo)
    if _git(repo, 'rev-parse', 'HEAD').decode().strip() != commit:
        raise ValueError('Configuration checkout differs from its original commit')
    if _git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Configuration checkout contains changed or untracked source')


def _source_bytes(repo, commit, relative):
    from ergora.training_execution_protocol import read_raw

    _checkout(repo, commit)
    path = _file(repo, relative)
    raw = read_raw(path, 10 * LIMIT)
    if raw != _git(repo, 'show', commit + ':' + relative):
        raise ValueError('Configuration source bytes differ from their original Git object')
    return path, hashlib.sha256(raw).hexdigest()


def _chain(request):
    from ergora import training_execution_protocol as protocol

    context = request['context']
    intent = context['intent']
    chain = protocol.ExecutionRecords(context['project'], intent['experiment_id'], intent['control_home']).load()
    if (chain.owner is None
            or any(chain.records[name] is None for name in ('request', 'launch', 'attempt', 'ack'))
            or chain.owner['context_sha256'] != chain.sha(context)
            or chain.records['launch']['owner_sha256'] != chain.sha(chain.owner)
            or chain.records['stopped'] is not None):
        raise ValueError('Configuration driver has no active original managed execution chain')
    expected = {name + '_sha256': chain.sha(chain.records[name]) for name in ('request', 'launch', 'attempt', 'ack')}
    if expected != request['managed'] or chain.records['request']['native_request_sha256'] != request['native_request_sha256']:
        raise ValueError('Configuration driver request differs from its original execution')
    if chain.sha(chain.native['runner']) != request['runner_sha256'] or chain.native['experiment']['binding'] != request['binding']:
        raise ValueError('Configuration driver runner or binding changed')
    protocol.validate_context(context, chain)
    # Source and parent reads consume the original allowance. Check again after
    # their final return, including the native fence visible to this child.
    fence = chain.root / ('training/fences/' + chain.ident + '.json')
    if (fence.exists() or fence.is_symlink()
            or not protocol.owner_active(chain.budget / 'owner.json', chain.owner)
            or protocol.budget_clock.remaining(context['authorization']['clock'], context['policy']['wall_seconds'],
                                               context['policy']['cleanup_seconds']) <= 0):
        raise ValueError('Original execution fence, owner or computation deadline forbids configuration work')
    return chain


def stage_request(folder, record, checkouts, manifest, context, active):
    """Prepare only after original attempt/ack, under the native executor lock."""
    from ergora import training_execution_protocol as protocol, training_materials as materials

    active()
    runner = record['runner']
    validate_runner(runner)
    capability = runner['configuration_readback']
    source = capability['source']
    folder = Path(folder)
    trusted = folder / 'configuration-driver'
    if not trusted.exists():
        _git(folder, 'clone', '--no-checkout', '--no-local', source['repo'], str(trusted))
        _git(trusted, 'checkout', '--detach', source['commit'])
    _checkout(trusted, source['commit'])
    if source_reference(trusted, source['commit'], source['entrypoint']) != {**source, 'repo': str(trusted)}:
        raise ValueError('Configuration driver checkout inventory changed')
    descriptor = materials.require_driver(manifest, runner)
    raw_materials = materials.read_materials(Path(context['intent']['execution']['state_directory']), manifest)
    configurations = {}
    for arm, commit_key, hash_key in (('baseline', 'baseline_sha', 'base_config_sha256'),
                                      ('candidate', 'candidate_sha', 'candidate_config_sha256')):
        commit = record['experiment']['binding'][commit_key]
        if descriptor['kind'] == 'git-source':
            path, digest = _source_bytes(checkouts[arm], commit, descriptor['path'])
        else:
            _checkout(checkouts[arm], commit)
            path = folder / 'run-output/configuration-inputs' / (arm + '.json')
            materials.publish_material(path, raw_materials[arm], Path(context['intent']['execution']['state_directory']))
            digest = hashlib.sha256(raw_materials[arm]).hexdigest()
        if digest != manifest[hash_key]:
            raise ValueError('Configuration source raw SHA differs from manifest ' + hash_key)
        configurations[arm] = {'repo': str(checkouts[arm]), 'commit': commit, 'path': str(path), 'source_sha256': digest}
    intent = context['intent']
    chain = protocol.ExecutionRecords(context['project'], intent['experiment_id'], intent['control_home']).load()
    request = {'schema_version': 1, 'kind': 'training-configuration-driver-request',
               'binding': record['experiment']['binding'],
               'native_request_sha256': chain.records['request']['native_request_sha256'],
               'runner_sha256': chain.sha(runner), 'configuration_readback': capability,
               'baseline_reference': materials.baseline_selector(manifest),
               'execution_phase_id': chain.records['launch']['execution_phase_id'],
               'configurations': configurations, 'trusted_repo': str(trusted),
               'manifest': str(folder.parent.parent / 'manifests' / (intent['experiment_id'] + '.json')),
               'output': str(folder / 'run-output'), 'context': context,
               'managed': {name + '_sha256': chain.sha(chain.records[name])
                           for name in ('request', 'launch', 'attempt', 'ack')}}
    path = folder / 'configuration-request.json'
    _bytes(request, 16 * LIMIT - 1)
    protocol.publish(path, request, chain.root)
    _chain(request)
    active()
    return {'configuration_driver': str(Path(__file__).resolve()), 'configuration_request': str(path)}


def _observations(value, request):
    _bytes(value)
    _exact(value, ('baseline', 'candidate'), 'Configuration observations')
    result = {}
    for arm in ('baseline', 'candidate'):
        item = value[arm]
        _exact(item, ('observation_scheme', 'source_sha256', 'snapshot', 'semantic_identity', 'invariants', 'workload'),
               'Configuration observation')
        if item['observation_scheme'] != request['configuration_readback']['observation_scheme']:
            raise ValueError('Configuration observation scheme differs from the reviewed driver')
        if item['source_sha256'] != request['configurations'][arm]['source_sha256']:
            raise ValueError('Observed configuration source SHA differs from its input')
        if not isinstance(item['snapshot'], dict) or not item['snapshot']:
            raise ValueError('Configuration driver requires a complete snapshot object')
        identity = item['semantic_identity']
        _exact(identity, ('scheme', 'sha256'), 'Configuration semantic identity')
        if not isinstance(identity['scheme'], str) or not 1 <= len(identity['scheme']) <= 128:
            raise ValueError('Configuration semantic identity requires its versioned scheme')
        _digest(identity['sha256'], 'Configuration semantic identity')
        _exact(item['invariants'], INVARIANTS, 'Configuration invariants')
        if any(not isinstance(token, str) or not 1 <= len(token) <= 256 for token in item['invariants'].values()):
            raise ValueError('Configuration invariants require source-derived identity tokens')
        _exact(item['workload'], WORKLOAD, 'Configuration workload')
        if any(field is None for field in item['workload'].values()):
            raise ValueError('Configuration workload observations must be explicit')
        result[arm] = {**item, 'snapshot_sha256': _sha(item['snapshot'])}
    if result['baseline']['invariants'] != result['candidate']['invariants']:
        raise ValueError('Configuration changes fixed model, precision or objective invariants')
    return result


def _inputs(request, original_raw):
    from ergora import training_execution_protocol as protocol, training_materials as materials

    chain = _chain(request)
    if request['execution_phase_id'] != chain.records['launch']['execution_phase_id']:
        raise ValueError('Configuration request differs from its original execution phase')
    runner = chain.native['runner']
    if request['configuration_readback'] != runner['configuration_readback']:
        raise ValueError('Configuration driver capability differs from the original runner')
    capability = runner['configuration_readback']
    source, trusted = capability['source'], Path(request['trusted_repo'])
    if trusted != chain.folder.parent / 'configuration-driver':
        raise ValueError('Configuration driver source is outside its original job')
    _checkout(trusted, source['commit'])
    if source_reference(trusted, source['commit'], source['entrypoint']) != {**source, 'repo': str(trusted)}:
        raise ValueError('Configuration driver source inventory changed')
    expected_manifest = chain.root / ('training/manifests/' + chain.ident + '.json')
    if request['manifest'] != str(expected_manifest) or request['output'] != str(chain.folder.parent / 'run-output'):
        raise ValueError('Configuration driver paths differ from the original full job')
    manifest_raw = chain.originals.get(expected_manifest) or protocol.read_raw(expected_manifest, 16 * LIMIT)
    if hashlib.sha256(manifest_raw).hexdigest() != request['binding']['manifest_sha']:
        raise ValueError('Configuration driver manifest bytes changed')
    manifest = json.loads(manifest_raw)
    descriptor = materials.require_driver(manifest, runner)
    if request['baseline_reference'] != materials.baseline_selector(manifest):
        raise ValueError('Baseline reference selection differs from the original manifest')
    raw_materials = materials.read_materials(chain.root, manifest)
    for arm, commit_key, hash_key in (('baseline', 'baseline_sha', 'base_config_sha256'),
                                      ('candidate', 'candidate_sha', 'candidate_config_sha256')):
        repo = chain.folder.parent / arm
        commit = request['binding'][commit_key]
        if descriptor['kind'] == 'git-source':
            path, digest = _source_bytes(repo, commit, descriptor['path'])
        else:
            _checkout(repo, commit)
            path = chain.folder.parent / 'run-output/configuration-inputs' / (arm + '.json')
            raw_input = materials.read_raw(path)
            if raw_input != raw_materials[arm]:
                raise ValueError('Configuration driver input differs from its original prepared raw bytes')
            digest = hashlib.sha256(raw_input).hexdigest()
        if request['configurations'][arm] != {'repo': str(repo), 'commit': commit, 'path': str(path), 'source_sha256': digest}:
            raise ValueError('Configuration driver input differs from the original checkout')
        if digest != manifest[hash_key]:
            raise ValueError('Configuration source raw SHA differs from manifest ' + hash_key)
    if protocol.read_raw(chain.folder.parent / 'configuration-request.json', 16 * LIMIT) != original_raw:
        raise ValueError('Configuration driver request bytes changed before training work')
    return _chain(request), manifest


def _publish_receipt(path, value, chain):
    from ergora import training_execution_protocol as protocol, training_materials as materials

    _bytes(value, LIMIT - 1)
    raw = chain.adapter.canonical(value) + b'\n'
    protocol.publish(path, value, chain.root)
    materials.confirm_file(path, raw, chain.root)
    return raw


def _reference_read(projection, selected, request, request_raw, observations):
    """The source declares its oracle relation; core keeps quality and timing separate."""
    from ergora import training_execution_protocol as protocol
    from ergora.reference_training_evidence import _reason

    projection = protocol.decode(_bytes(projection))
    _exact(projection, ('scheme', 'baseline_observation_sha256', 'candidate_observation_sha256', 'invariants',
                        'relations', 'allowed_deltas', 'oracle_applicability'), 'Baseline reference projection')
    reference = selected['reference']
    anchor = reference['anchor']
    chain = _chain(request)
    manifest = protocol.decode(protocol.read_raw(Path(request['manifest'])))
    if (anchor['baseline_commit'] != request['binding']['baseline_sha']
            or anchor['base_config_sha256'] != manifest['base_config_sha256']
            or anchor['workload_fingerprint'] != manifest['workload_fingerprint']
            or anchor['baseline_id'] != manifest['baseline_id']):
        raise ValueError('Baseline reference anchor differs from the current baseline')
    if (not isinstance(projection['scheme'], str) or not projection['scheme']
            or projection['baseline_observation_sha256'] != chain.sha(observations['baseline'])
            or projection['candidate_observation_sha256'] != chain.sha(observations['candidate'])
            or projection['invariants'] != observations['baseline']['invariants']):
        raise ValueError('Baseline reference projection differs from the actual configuration observations')
    relations, deltas = projection['relations'], projection['allowed_deltas']
    if not isinstance(relations, list) or not isinstance(deltas, list) or not all(isinstance(key, str) for key in deltas):
        raise ValueError('Baseline reference requires explicit field relations and allowed deltas')
    fields, different, unsupported_units = set(), set(), []
    for relation in relations:
        _exact(relation, ('field', 'relation', 'reference', 'current', 'unit'), 'Baseline reference field relation')
        if (not isinstance(relation['field'], str) or not relation['field'] or relation['field'] in fields
                or relation['relation'] not in ('matched', 'different', 'unknown', 'not_applicable')
                or not isinstance(relation['unit'], str) or not relation['unit']):
            raise ValueError('Baseline reference has an unsupported field relation')
        if relation['unit'] not in ('samples', 'tokens', 'updates', 'groups', 'bytes', 'identity', 'not_applicable'):
            unsupported_units.append(relation['field'])
        fields.add(relation['field'])
        if relation['unit'] in ('samples', 'tokens', 'updates', 'groups', 'bytes'):
            if any(value is not None and (type(value) is not int or value < 0)
                   for value in (relation['reference'], relation['current'])):
                raise ValueError('Baseline reference counts must be nonnegative integers in declared units')
        if relation['relation'] == 'matched' and relation['reference'] != relation['current']:
            raise ValueError('Baseline reference claims unequal field values match')
        if relation['relation'] == 'different':
            different.add(relation['field'])
    if len(deltas) != len(set(deltas)) or not set(deltas) <= different:
        raise ValueError('Baseline reference allowed deltas must name actual different fields')
    applicability = projection['oracle_applicability']
    _exact(applicability, ('state', 'scheme', 'coverage', 'reasons'), 'Baseline oracle applicability')
    if applicability['state'] not in ('supported', 'unavailable', 'invalid') or not isinstance(applicability['reasons'], list):
        raise ValueError('Unsupported baseline oracle applicability')
    receipt, quality = reference['receipt'], reference['coverage']['quality']
    if receipt is not None and receipt.get('baseline') and receipt['baseline'].get('invariants') != projection['invariants']:
        raise ValueError('Baseline reference changes fixed model, precision or objective invariants')
    if quality.get('state') == 'invalid' or applicability['state'] == 'invalid':
        raise ValueError('Baseline reference is invalid for this target oracle')
    reusable = quality['baseline_scope_verified'] and applicability['state'] == 'supported' and not unsupported_units
    if reusable and (receipt['oracle']['scheme'] != applicability['scheme'] or receipt['oracle']['coverage'] != applicability['coverage']):
        raise ValueError('Baseline reference applicability does not match its actual baseline oracle scope')
    reasons = list(quality['reasons'])
    if unsupported_units:
        reasons.append(_reason('reader_unsupported', 'projection.relation_units', observed=unsupported_units))
    if not reusable:
        reasons.append(_reason('oracle_relation_unsupported', 'projection.oracle_applicability', observed=applicability['state']))
    return {'schema_version': 1, 'kind': 'baseline-reference-read', 'request_sha256': hashlib.sha256(request_raw).hexdigest(),
            'binding': request['binding'], 'selector': request['baseline_reference'],
            'reference_sha256': selected['reference_sha256'], 'anchor_sha256': selected['anchor_sha256'],
            'inventory_sha256': reference['inventory']['sha256'],
            'candidate_observation_sha256': chain.sha(observations['candidate']), 'projection': projection,
            'quality': {'state': 'reusable' if reusable else 'unavailable', 'coverage': applicability['coverage'] if reusable else None,
                        'reasons': reasons},
            'timing': reference['coverage']['timing'], 'resources': reference['coverage']['resources'],
            'candidate_quality': 'not_evaluated', 'baseline_work_skipped': False,
            'independent_pair_supplied': False, 'promotion_approved': False}


def _record_reference(driver, context, request, output, observations, configuration_raw, request_raw, manifest):
    """Collect already executed source facts under the original full job and clock."""
    from ergora import training_execution_protocol as protocol, training_materials as materials
    from ergora.reference_training_evidence import _receipt_coverage, _measurement, _resource_coverage

    chain, _ = _inputs(request, request_raw)
    evidence_path = output / 'evidence.json'
    evidence_raw = protocol.read_raw(evidence_path)
    evidence = protocol.decode(evidence_raw)
    originals, artifacts = {}, {}
    for item in evidence['artifacts']:
        _exact(item, ('path', 'sha256'), 'Full evidence artifact')
        path = output / materials.relative(item['path'])
        original = materials.read_raw(path, 16 * LIMIT)
        if item['path'] in artifacts or hashlib.sha256(original).hexdigest() != item['sha256']:
            raise ValueError('Full evidence has duplicate or changed original artifacts')
        originals[path] = original
        artifacts[item['path']] = {**item, 'bytes': len(original)}
    data = protocol.decode(_bytes(driver['baseline_reference_record'](context, request, output)))
    _exact(data, ('baseline', 'oracle', 'environment', 'measurement', 'resources'), 'Source baseline record')
    if protocol.read_raw(evidence_path) != evidence_raw:
        raise ValueError('Baseline collection changed original unfinished evidence bytes')
    for path, original in originals.items():
        if materials.read_raw(path, 16 * LIMIT) != original:
            raise ValueError('Baseline collection changed original raw work or reports')
    # Core owns the complete source and execution provenance. These are data
    # artifacts, never an alternate runnable source tree or a live admission.
    capability = chain.owner['execution_capability']
    source_originals = {
        'baseline-reference-source-inventory.raw': _git(Path(request['trusted_repo']), 'ls-tree', '-r', '-z', '--full-tree', request['configuration_readback']['source']['commit']),
        'baseline-reference-protocol-source.py.txt': protocol.read_raw(Path(protocol.__file__)),
        'baseline-reference-native-descriptor.json': protocol.read_raw(Path(capability['installation']) / 'ergora-native-runtime.json')}
    descriptor = materials.input_descriptor(manifest)
    configuration_refs = {}
    for arm in ('baseline', 'candidate'):
        original = materials.read_raw(Path(request['configurations'][arm]['path']), 10 * LIMIT)
        if hashlib.sha256(original).hexdigest() != request['configurations'][arm]['source_sha256']:
            raise ValueError('Baseline source configuration bytes changed after actual work')
        name = ('baseline-reference-configuration-inputs/' + arm + '.raw' if descriptor['kind'] == 'git-source'
                else 'configuration-inputs/' + arm + '.json')
        if descriptor['kind'] == 'git-source':
            source_originals[name] = original
        configuration_refs[arm] = {'path': name, 'sha256': hashlib.sha256(original).hexdigest(), 'bytes': len(original)}
    if isinstance(data['baseline'], dict):
        existing = data['baseline'].get('configuration_ref')
        if existing is not None and existing != configuration_refs['baseline']:
            raise ValueError('Source baseline configuration reference differs from actual core raw input')
        data['baseline']['configuration_ref'] = configuration_refs['baseline']
    if (hashlib.sha256(source_originals['baseline-reference-source-inventory.raw']).hexdigest() != request['configuration_readback']['source']['inventory_sha256']
            or hashlib.sha256(source_originals['baseline-reference-protocol-source.py.txt']).hexdigest() != capability['gate_sources']['training_execution_protocol.py']
            or hashlib.sha256(source_originals['baseline-reference-native-descriptor.json']).hexdigest() != capability['descriptor_sha256']):
        raise ValueError('Baseline source bytes differ from the actual current admitted execution')
    result = {}
    for name, original in source_originals.items():
        path = output / name
        materials.publish_material(path, original, chain.root)
        result[path] = original
        artifacts[name] = {'path': name, 'sha256': hashlib.sha256(original).hexdigest(), 'bytes': len(original)}
    for ref in configuration_refs.values():
        if ref['path'] in artifacts and artifacts[ref['path']] != ref:
            raise ValueError('Full evidence raw configuration differs from its original input')
        artifacts[ref['path']] = ref
    source_manifest = {'schema_version': 1, 'kind': 'training-execution-source-manifest',
        'capability_sha256': chain.sha(capability), 'gate_sources': capability['gate_sources'],
        'protocol_source_ref': artifacts['baseline-reference-protocol-source.py.txt'],
        'native_descriptor_ref': artifacts['baseline-reference-native-descriptor.json']}
    path = output / 'baseline-reference-execution-sources.json'
    result[path] = _publish_receipt(path, source_manifest, chain)
    path = output / 'configuration-receipt.json'
    artifacts[path.name] = {'path': path.name, 'sha256': hashlib.sha256(configuration_raw).hexdigest(), 'bytes': len(configuration_raw)}
    receipt = {'schema_version': 1, 'kind': 'baseline-reference-receipt', 'binding': request['binding'],
        'native_request_sha256': request['native_request_sha256'], 'runner_sha256': request['runner_sha256'],
        'managed': request['managed'], 'configuration_receipt_sha256': artifacts['configuration-receipt.json']['sha256'],
        'source': request['configuration_readback']['source'],
        'baseline_observation_sha256': chain.sha(observations['baseline']), **data}

    def artifact(ref):
        if artifacts.get(ref.get('path')) != ref:
            raise ValueError('Baseline receipt references an unindexed current artifact')
        path = output / ref['path']
        original = materials.read_raw(path)
        if hashlib.sha256(original).hexdigest() != ref['sha256'] or len(original) != ref['bytes']:
            raise ValueError('Baseline receipt raw report bytes changed')
        return protocol.decode(original)

    chain.originals[chain.folder.parent / 'configuration-request.json'] = request_raw
    _receipt_coverage(receipt, protocol.decode(configuration_raw), request, manifest, request['binding'], artifacts, artifact, chain)
    _measurement(receipt, evidence, manifest, artifacts, artifact, chain)
    _resource_coverage(receipt['resources'], artifacts, artifact)
    path = output / 'baseline-reference-receipt.json'
    result[path] = _publish_receipt(path, receipt, chain)
    _inputs(request, request_raw)
    # Preserve the complete source evidence and all original work across the
    # callback and all source I/O, not just their decoded JSON values.
    for path, original in {**originals, **result, evidence_path: evidence_raw}.items():
        if materials.read_raw(path, 16 * LIMIT) != original:
            raise ValueError('Baseline source collection changed exact original bytes')
    _inputs(request, request_raw)
    return result


def main(request_path):
    """Construct, observe, freeze and run the same source-owned configuration objects."""
    from ergora import training_execution_protocol as protocol, training_materials as materials

    raw = protocol.read_raw(Path(request_path), 16 * LIMIT)
    request = protocol.decode(raw)
    _exact(request, ('schema_version', 'kind', 'binding', 'native_request_sha256', 'runner_sha256',
                     'configuration_readback', 'baseline_reference', 'execution_phase_id', 'configurations', 'trusted_repo', 'manifest', 'output', 'context', 'managed'),
           'Configuration driver request')
    if type(request['schema_version']) is not int or request['schema_version'] != 1 or request['kind'] != 'training-configuration-driver-request':
        raise ValueError('Unsupported configuration driver request')
    _bytes(request, 16 * LIMIT)
    execution = request['context']['intent']['execution']
    installation = protocol.reference.validate_installation(Path(execution['installation']), training=True)
    if str(installation) != execution['installation']:
        raise ValueError('Configuration driver requires its original canonical native installation')
    paths = [str(installation / part) for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
    sys.path[:0] = paths
    os.environ.update(AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                      AGENTFLOW_STATE_DIR=execution['state_directory'],
                      PYTHONPATH=os.pathsep.join([str(Path(__file__).resolve().parent.parent), *paths]))
    chain, manifest = _inputs(request, raw)
    expected_path = chain.folder.parent / 'configuration-request.json'
    if Path(request_path) != expected_path:
        raise ValueError('Configuration driver request is outside the original job')
    output = Path(request['output'])
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = output / 'configuration-receipt.json'
    if receipt_path.exists() or receipt_path.is_symlink():
        raise ValueError('Configuration construction was already consumed; reconcile the original execution')
    trusted = Path(request['trusted_repo'])
    os.chdir(trusted)
    # Resolve driver imports from its own checkout and the selected interpreter,
    # never from the candidate cwd or an inherited relative PYTHONPATH entry.
    arms = [Path(item['repo']) for item in request['configurations'].values()]
    sys.path[:] = [str(trusted), *[entry for entry in sys.path if entry and Path(entry).is_absolute()
                                  and not any(Path(entry).is_relative_to(arm) for arm in arms)]]
    driver = runpy.run_path(str(_file(trusted, request['configuration_readback']['source']['entrypoint'])))
    for operation in ('prepare', 'describe', 'run'):
        if not callable(driver.get(operation)):
            raise ValueError('Configuration driver does not support ' + operation)
    supports_reference = request['configuration_readback']['baseline_reference_protocol'] == 'baseline-reference-v1'
    if supports_reference:
        for operation in ('baseline_reference_read', 'baseline_reference_record'):
            if not callable(driver.get(operation)):
                raise ValueError('Configuration driver does not support ' + operation)
    _inputs(request, raw)
    context = driver['prepare'](request)
    observations = _observations(driver['describe'](context), request)
    # Copy the observation now: describe must not retain mutable aliases into it.
    observations = protocol.decode(_bytes(observations))
    receipt = {'schema_version': 1, 'kind': 'training-configuration-receipt',
               'request_sha256': hashlib.sha256(raw).hexdigest(), 'binding': request['binding'],
               'native_request_sha256': request['native_request_sha256'], 'runner_sha256': request['runner_sha256'],
               'managed': request['managed'], 'source': request['configuration_readback']['source'],
               'environment_fingerprint': manifest['environment_fingerprint'], 'observations': observations,
               'configuration_inputs': materials.input_descriptor(manifest), 'configurations': request['configurations']}
    _bytes(receipt, LIMIT - 1)
    receipt_raw = chain.adapter.canonical(receipt) + b'\n'
    protocol.publish(receipt_path, receipt, chain.root)
    materials.confirm_file(receipt_path, receipt_raw, chain.root)
    frozen = {receipt_path: receipt_raw}
    if request['baseline_reference'] is not None:
        from ergora.reference_training_evidence import _baseline_reference
        from ergora.reference_training_context import _TrainingProject

        project = _TrainingProject({'project': request['context']['project'], 'control_home': request['context']['intent']['control_home']})
        selected = _baseline_reference(project, request['context']['intent']['control_home'], request['baseline_reference'])
        if selected['reference_sha256'] != request['baseline_reference']['reference_sha256']:
            raise ValueError('Baseline reference content differs from the frozen selector')
        reference = selected['reference']
        before_reference = _bytes(reference, 8 * LIMIT)
        projection = driver['baseline_reference_read'](context, request, reference)
        if _bytes(reference, 8 * LIMIT) != before_reference:
            raise ValueError('Baseline reference changed during its source-owned read callback')
        read = _reference_read(projection, selected, request, raw, observations)
        read_path = output / 'baseline-reference-read.json'
        frozen[read_path] = _publish_receipt(read_path, read, chain)
        # Re-read the same full immutable inventory after the callback and the
        # durable receipt; then the existing last admission follows all I/O.
        again = _baseline_reference(project, request['context']['intent']['control_home'], request['baseline_reference'])
        if _bytes(again['reference'], 8 * LIMIT) != before_reference:
            raise ValueError('Baseline reference changed before current full work')
    if _bytes(_observations(driver['describe'](context), request)) != _bytes(observations):
        raise ValueError('Configuration changed after observation and before training work')
    _inputs(request, raw)
    driver['run'](context, request, output)
    _inputs(request, raw)
    if supports_reference:
        frozen.update(_record_reference(driver, context, request, output, observations, receipt_raw, raw, manifest))
    # Preserve the readback as an ordinary hashed artifact in the original full
    # evidence bundle. The original archive and quality gate remain its owners.
    artifacts = []
    for path, original in frozen.items():
        if protocol.read_raw(path, 16 * LIMIT) != original:
            raise ValueError('Configuration or baseline reference receipt changed during training work')
        artifacts.append({'path': path.relative_to(output).as_posix(), 'sha256': hashlib.sha256(original).hexdigest()})
    for arm, original in materials.read_materials(chain.root, manifest).items():
        path = Path(request['configurations'][arm]['path'])
        if materials.read_raw(path) != original:
            raise ValueError('Actual configuration input changed during training work')
        artifacts.append({'path': path.relative_to(output).as_posix(), 'sha256': hashlib.sha256(original).hexdigest()})
    evidence_path = output / 'evidence.json'
    if evidence_path.is_file():
        evidence = protocol.decode(protocol.read_raw(evidence_path))
        for artifact in artifacts:
            existing = [item for item in evidence['artifacts'] if item['path'] == artifact['path']]
            if existing and existing != [artifact]:
                raise ValueError('Full evidence contains a conflicting configuration input or receipt')
            if not existing:
                evidence['artifacts'].append(artifact)
        # This is the runner-owned unfinished output, not an immutable archive.
        evidence_path.write_bytes(_bytes(evidence, LIMIT - 1) + b'\n')
    _inputs(request, raw)


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    if len(sys.argv) != 2:
        raise SystemExit('Expected the original managed configuration request path')
    main(Path(sys.argv[1]))
