"""Source-pinned configuration construction and explicit operations in one managed runner."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import runpy
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ergora._paths import IMPORT_ROOT, PACKAGE_ROOT


PROTOCOL = 'training-configuration-driver-v1'
INVARIANTS = ('model_algorithm', 'model_structure', 'model_size', 'precision_policy', 'objective')
WORKLOAD = ('dataset', 'initial_checkpoint', 'window', 'global_batch', 'microbatch',
            'accumulation', 'normalization', 'optimizer', 'schedule', 'layout')
LIMIT = 1_048_576


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(label + ' has unsupported or missing fields')


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
                        'observation_scheme', 'baseline_reference_protocol', 'screen',
                        *(name for name in ('profile', 'local_gpu_pool') if name in capability)), 'Configuration readback')
    if 'local_gpu_pool' in capability:
        from ergora.runtime import gpu_pool

        selected = capability['local_gpu_pool']
        gpu_pool.validate_lease_selection(selected)
        if selected['runtime_sha256'] != gpu_pool.runtime_source_sha256():
            raise ValueError('Local GPU runtime sources differ from the reviewed runner')
    if 'profile' in capability and capability['profile'] is not None:
        from ergora.training.materials import _exact as exact_profile
        declared = capability['profile']
        exact_profile(declared, ('protocol', 'operations'), 'Profile capability')
        if (declared['protocol'] != 'training-profile-v1' or not isinstance(declared['operations'], list)
                or not declared['operations'] or any(not isinstance(item, str) or not item for item in declared['operations'])
                or len(set(declared['operations'])) != len(declared['operations'])):
            raise ValueError('Profile source capability requires explicit unique operations')
    if capability['baseline_reference_protocol'] not in (None, 'baseline-reference-v1'):
        raise ValueError('Unsupported baseline reference protocol')
    screen = capability['screen']
    if screen is not None:
        _exact(screen, ('protocol', 'scheme'), 'Screen capability')
        if (screen['protocol'] != 'training-screen-v1' or not isinstance(screen['scheme'], str)
                or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', screen['scheme']) is None
                or capability['baseline_reference_protocol'] != 'baseline-reference-v1'):
            raise ValueError('Unsupported declared screen capability')
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


def cpu_contract_sources():
    """The admitted operation uses this one current wrapper/native implementation."""
    from ergora.training.materials import read_raw
    package = PACKAGE_ROOT
    names = tuple(sorted(path.relative_to(package).as_posix() for path in package.rglob('*.py')
                         if path.relative_to(package).parts[0] != 'data')) + (
             'data/components.json',
             'data/native-runtime/training-executor-admission-v3.json',
             'data/reference-manifest.json',
             'data/reference/platform/local/agent_platform/process_job.py',
             'data/reference/platform/local/agent_platform/sandbox.py',
             'data/reference/platform/local/agent_platform/training.py',
             'data/reference/platform/local/agent_platform/training_executor.py',
             'data/schemas/agent-definition-v1.json',
             'data/schemas/candidate-review-context-v1.json',
             'data/schemas/composition-input-v1.json',
             'data/schemas/composition-manifest-v1.json',
             'data/schemas/document-correction-proposal-v1.json',
             'data/schemas/evaluation-manifest-v1.json',
             'data/schemas/evaluation-result-v1.json',
             'data/schemas/issue-observation-v1.json',
             'data/schemas/project-registration-v1.json',
             'data/schemas/project-registration-v2.json',
             'data/schemas/retrospective-memory-proposal-v1.json',
             'data/schemas/retrospective-proposal-v1.json',
             'data/schemas/retrospective-workflow-proposal-v1.json',
             'data/schemas/state-backup-v1.json',
             'data/schemas/task-definition-v1.json',
             'data/schemas/task-definition-v2.json',
             'data/schemas/task-definition-v3.json',
             'data/schemas/task-definition-v8.json',
             'data/schemas/task-handoff-v1.json',
             'data/schemas/task-mcp-scope-v1.json',
             'data/schemas/training-cycle-v2.json',
             'data/schemas/training-rounds-v1.json',
             'data/schemas/training-search-v2.json',
             'data/schemas/workflow-definition-v1.json',
             'data/schemas/workflow-definition-v2.json',
             )

    return {name: hashlib.sha256(read_raw(package / name, 16 * LIMIT)).hexdigest() for name in names}


def bind_cpu_execution_contract(value, runner):
    """Compile explicit conformance against actual sources before native preview."""
    import ergora.training.materials as materials
    if value is None:
        raise ValueError('Present CPU declaration/contract cannot be null')
    validate_runner(runner)
    capability = runner['configuration_readback']
    if not isinstance(capability, dict):
        raise ValueError('CPU contract requires its trusted configuration source ABI')
    source = capability['source']
    actual = source_reference(Path(source['repo']), source['commit'], source['entrypoint'])
    if actual != source:
        raise ValueError('CPU contract source changed before preparation')
    original = _git(Path(source['repo']), 'show', source['commit'] + ':' + source['entrypoint'])
    implementation = {'source': {**source, 'entrypoint_sha256': hashlib.sha256(original).hexdigest()},
        'driver_protocol': capability['protocol'], 'observation_scheme': capability['observation_scheme'],
        'runner_sha256': materials.observation_sha256(runner), 'wrapper_entry': 'ergora.training.configuration:main',
        'core_sources_sha256': materials.observation_sha256(cpu_contract_sources())}
    if isinstance(value, dict) and value.get('kind') == 'training-cpu-execution-declaration':
        materials._exact(value, ('kind', 'operation', 'conformance', 'input_domain'), 'Explicit CPU declaration')
        result = {'schema_version': 1, 'kind': 'training-cpu-execution-contract',
                  **{key: value[key] for key in ('operation', 'conformance', 'input_domain')}, 'implementation': implementation}
        result['sha256'] = materials.observation_sha256(result)
    else:
        result = value
        materials.validate_cpu_execution_contract(result, runner=runner)
        if result['implementation'] != implementation:
            raise ValueError('Admitted CPU source/wrapper differs from the exact original implementation')
    materials.validate_cpu_execution_contract(result, runner=runner)
    return materials.decode_record(materials.observation_bytes(result))






def _checkout(repo, commit):
    repo = Path(repo)
    if _git(repo, 'rev-parse', 'HEAD').decode().strip() != commit:
        raise ValueError('Configuration checkout differs from its original commit')
    if _git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Configuration checkout contains changed or untracked source')


def validate_execution_sources(manifest, runner):
    """Observe current trusted oracle bytes before an operation can be reserved."""
    from ergora.training.materials import execution_plan

    execution = execution_plan(manifest, runner)
    if execution.get('cpu_contract') is not None:
        bind_cpu_execution_contract(execution['cpu_contract'], runner)
    if execution['operation'] == 'full-verify':
        return
    source = runner['configuration_readback']['source']
    if source_reference(Path(source['repo']), source['commit'], source['entrypoint']) != source:
        raise ValueError('Screen trusted source inventory changed')
    for check in execution['plan']['checks']:
        raw = _git(Path(source['repo']), 'show', source['commit'] + ':' + check['source_entrypoint'])
        if not raw or len(raw) > 10 * LIMIT or hashlib.sha256(raw).hexdigest() != check['contract_sha256']:
            raise ValueError('Screen oracle source differs from its frozen contract')
        metadata = _git(Path(source['repo']), 'ls-tree', source['commit'], '--', check['source_entrypoint'])
        if not metadata.startswith((b'100644 blob ', b'100755 blob ')):
            raise ValueError('Screen oracle requires an ordinary tracked source file')


def _source_bytes(repo, commit, relative):
    from ergora.training.execution_protocol import read_raw

    _checkout(repo, commit)
    path = _file(repo, relative)
    raw = read_raw(path, 10 * LIMIT)
    if raw != _git(repo, 'show', commit + ':' + relative):
        raise ValueError('Configuration source bytes differ from their original Git object')
    return path, hashlib.sha256(raw).hexdigest()


def _chain(request):
    import ergora.training.execution_protocol as protocol
    from ergora.training.runtime.evidence import validate_context

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
    validate_context(context, chain)
    protocol.require_not_skipped(intent['execution'], chain.ident)
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
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials

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
               'execution': materials.execution_plan(manifest, runner),
               'baseline_reference': materials.baseline_selector(manifest),
               'execution_phase_id': chain.records['launch']['execution_phase_id'],
               'configurations': configurations, 'trusted_repo': str(trusted),
               'manifest': str(folder.parent.parent / 'manifests' / (intent['experiment_id'] + '.json')),
               'output': str(folder / 'run-output'), 'context': context,
               'managed': {name + '_sha256': chain.sha(chain.records[name])
                           for name in ('request', 'launch', 'attempt', 'ack')}}
    cpu_preparation = _cpu_copy_stage(folder, chain, manifest, runner, context, active)
    if cpu_preparation is not None:
        request['cpu_contract_preparation'] = cpu_preparation
        request['cpu_contract_core'] = {'package_directory': str(PACKAGE_ROOT),
            'sources_sha256': request['execution']['cpu_contract']['implementation']['core_sources_sha256']}
    path = folder / 'configuration-request.json'
    materials.observation_bytes(request, 16 * LIMIT - 1)
    protocol.publish(path, request, chain.root)
    _chain(request)
    active()
    return {'configuration_driver': str(Path(__file__).resolve()), 'configuration_request': str(path)}


def _cpu_binding(request):
    from ergora.training.materials import observation_sha256
    context = request['context']
    return {'intent_sha256': observation_sha256(context['intent']),
            'authorization_sha256': context['authorization']['sha256']}


def cpu_process_context(command, output):
    """Original process_job consumes only the actual fixed managed wrapper entry."""
    from ergora.training.runtime.evidence import read_cpu_preparation_admission
    import ergora.training.materials as materials
    import ergora.training.execution_protocol as protocol
    if len(command) != 3 or Path(command[1]).resolve() != Path(__file__).resolve():
        return None
    raw = materials.read_raw(Path(command[2]), 16 * LIMIT)
    request = materials.decode_record(raw)
    chain, manifest = _inputs(request, raw)
    contract = materials.cpu_contract(manifest)
    if contract is None:
        return None
    if Path(output) != Path(request['output']):
        raise ValueError('CPU process command output differs from its original managed wrapper')
    read_cpu_preparation_admission(chain.root, chain.ident, manifest, chain.native['runner'])
    protocol.validate_cpu_budget_context(request['context'], require_complete=False)
    frame = materials.cpu_context_observation(contract, 'process', _cpu_binding(request))
    materials.publish_material(Path(output) / 'cpu-process-context.json', materials.observation_bytes(frame, 10 * LIMIT), chain.root)
    _inputs(request, raw)
    return request, raw


def cpu_process_last_admission(owned):
    if owned is None:
        return
    request, original_raw = owned
    _inputs(request, original_raw)


def _cpu_copy_stage(folder, chain, manifest, runner, context, active):
    from ergora.training.runtime.evidence import read_cpu_preparation_admission
    import ergora.training.materials as materials
    import ergora.training.execution_protocol as protocol
    accepted = read_cpu_preparation_admission(chain.root, chain.ident, manifest, runner)
    if accepted is None:
        return None
    output = Path(folder) / 'run-output'
    result = materials.cpu_preparation_observation(accepted, chain.ident, output=True)
    for name in ('intent', 'admission'):
        active()
        materials.publish_material(output / result[name + '_ref']['path'], accepted[name + '_raw'], chain.root)
        active()
    protocol.validate_cpu_budget_context(context, require_complete=False)
    source_map = cpu_contract_sources()
    if materials.observation_sha256(source_map) != accepted['contract']['implementation']['core_sources_sha256']:
        raise ValueError('CPU original fixed wrapper source closure changed before staging')
    core = {'package_directory': str(PACKAGE_ROOT), 'sources': source_map,
            'contract_sha256': accepted['contract_sha256']}
    materials.publish_material(output / 'cpu-core-sources.json', materials.observation_bytes(core), chain.root)
    active()
    return {name: result[name] for name in ('intent_ref', 'admission_ref')}


def _cpu_window_snapshots(request, raw):
    import ergora.training.materials as materials
    if request['execution'].get('cpu_contract') is None:
        return None
    _inputs(request, raw)
    try:
        snapshot = materials.cpu_execution_identity()
    except (OSError, ValueError) as error:
        snapshot = {'unsupported_reason': str(error)}
    _inputs(request, raw)
    return snapshot


def _cpu_core_window(request, phase, operation, windows, before, after):
    import ergora.training.materials as materials
    if request['execution'].get('cpu_contract') is None:
        return None
    value = materials.cpu_window_identity(request, phase, operation, windows, before, after)
    value.update(contract_sha256=request['execution']['cpu_contract']['sha256'],
                 preparation=request['cpu_contract_preparation'])
    return value


def _cpu_wrapper_context(request, raw, name):
    import ergora.training.materials as materials
    contract = request['execution'].get('cpu_contract')
    if contract is None:
        return None
    chain, _ = _inputs(request, raw)
    frame = materials.cpu_context_observation(contract, 'wrapper', _cpu_binding(request))
    path = Path(request['output']) / name
    original = materials.observation_bytes(frame, 10 * LIMIT)
    materials.publish_material(path, original, chain.root)
    _inputs(request, raw)
    return frame


def _cpu_complete_materials(request, raw):
    """Freeze complete original context sources before the first measured window."""
    import ergora.training.materials as materials
    import ergora.training.execution_protocol as protocol
    contract = request['execution'].get('cpu_contract')
    if contract is None:
        return {}
    chain, manifest = _inputs(request, raw)
    output = Path(request['output'])
    originals, copied = {}, []
    def copy(original, target, *, source_ref=None):
        path = output / target
        materials.publish_material(path, original, chain.root)
        originals[path] = original
        ref = {'path': target, 'sha256': hashlib.sha256(original).hexdigest(), 'bytes': len(original)}
        if source_ref is not None:
            copied.append({'original_path': source_ref['path'], 'original_sha256': source_ref['sha256'],
                           'original_bytes': source_ref['bytes'], 'artifact_ref': ref})
        return ref
    budget = request['context'].get('cpu_context')
    protocol.validate_cpu_budget_context(request['context'], require_complete=False)
    refs = [budget['parent'], budget['budget']]
    if budget['cycle'] is not None:
        refs.append(budget['cycle'])
        cycle = protocol.read_trial_reference(budget['cycle'])
        refs.extend([cycle['request_ref'], cycle['supervisor_ref'], *cycle['frames'].values()])
    seen = set()
    for ref in refs:
        key = (ref['path'], ref['sha256'], ref['bytes'])
        if key in seen:
            continue
        seen.add(key)
        _inputs(request, raw)
        value = protocol.read_raw(Path(ref['path']), 10 * LIMIT)
        if len(value) != ref['bytes'] or hashlib.sha256(value).hexdigest() != ref['sha256']:
            raise ValueError('Original CPU context source changed before archival')
        copy(value, 'cpu-context-sources/' + str(len(copied)) + '.raw', source_ref=ref)
        _inputs(request, raw)
    native = copy(protocol.read_raw(chain.folder / 'cpu-native.json', 10 * LIMIT), 'cpu-native-context.json')
    relation = copy(protocol.read_raw(chain.folder / 'cpu-native-parent.json'), 'cpu-native-parent.json')
    managed = {name: copy(chain.originals[chain.folder / (name + '.json')], 'cpu-managed-' + name + '.json')
               for name in ('request', 'launch', 'attempt', 'ack')}
    process_root = chain.root / 'processes' / ('af-perf-' + chain.ident + '-run')
    process, lineage_reason = {}, None
    try:
        for name in ('request', 'started', 'pid'):
            process[name] = copy(materials.read_raw(process_root / (name + '.json'), 10 * LIMIT), 'cpu-process-' + name + '.json')
        originals[output / 'cpu-process-context.json'] = materials.read_raw(output / 'cpu-process-context.json', 10 * LIMIT)
    except FileNotFoundError:
        process = None
        lineage_reason = 'unsupported: original process_job context/owned records are unavailable'
    for name in ('cpu-wrapper-context.json', 'cpu-wrapper-prepared-context.json', 'cpu-core-sources.json'):
        originals[output / name] = materials.read_raw(output / name, 10 * LIMIT)
    for name in ('intent_ref', 'admission_ref'):
        ref = request['cpu_contract_preparation'][name]
        original = materials.read_raw(output / ref['path'], 16 * LIMIT)
        if len(original) != ref['bytes'] or hashlib.sha256(original).hexdigest() != ref['sha256']:
            raise ValueError('Original CPU preparation artifact changed before source work')
        originals[output / ref['path']] = original
    copy(raw, 'cpu-contract-configuration-request.json')
    metadata = {'schema_version': 1, 'kind': 'training-cpu-execution-materials', 'contract_sha256': contract['sha256'],
                'budget_context': budget, 'sources': copied, 'native_ref': native, 'native_parent_ref': relation,
                'managed_records': managed, 'process_records': process, 'lineage_reason': lineage_reason}
    path = output / 'cpu-execution-materials.json'
    originals[path] = materials.observation_bytes(metadata)
    materials.publish_material(path, originals[path], chain.root)
    from ergora.training.runtime.evidence import cpu_contract_evidence
    cpu_contract_evidence(output, request, manifest)
    _inputs(request, raw)
    return originals


def _observations(value, request):
    import ergora.training.materials as materials

    materials.observation_bytes(value)
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
        result[arm] = {**item, 'snapshot_sha256': materials.observation_sha256(item['snapshot'])}
    if result['baseline']['invariants'] != result['candidate']['invariants']:
        raise ValueError('Configuration changes fixed model, precision or objective invariants')
    return result


def _inputs(request, original_raw):
    from ergora.training.runtime.evidence import read_cpu_preparation_admission
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials

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
    accepted = read_cpu_preparation_admission(chain.root, chain.ident, manifest, runner)
    if accepted is not None:
        expected_cpu = materials.cpu_preparation_observation(accepted, chain.ident, output=True)
        if request.get('cpu_contract_core') != {'package_directory': str(PACKAGE_ROOT),
                'sources_sha256': accepted['contract']['implementation']['core_sources_sha256']}:
            raise ValueError('CPU wrapper request differs from its original actual fixed core entry')
        if request.get('cpu_contract_preparation') != {key: expected_cpu[key] for key in ('intent_ref', 'admission_ref')}:
            raise ValueError('CPU wrapper request lost its original preparation acceptance')
    elif 'cpu_contract_preparation' in request:
        raise ValueError('Ordinary source request cannot acquire CPU preparation authority')
    if request['execution'] != materials.execution_plan(manifest, runner):
        raise ValueError('Configuration operation changed from its original manifest')
    if request['execution']['operation'] == 'training-screen-v1':
        for check in request['execution']['plan']['checks']:
            _, digest = _source_bytes(trusted, source['commit'], check['source_entrypoint'])
            if digest != check['contract_sha256']:
                raise ValueError('Screen oracle bytes changed from their original trusted source')
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
        if accepted is not None:
            materials.validate_cpu_contract_configuration(accepted['contract'], materials.read_raw(path))
    if protocol.read_raw(chain.folder.parent / 'configuration-request.json', 16 * LIMIT) != original_raw:
        raise ValueError('Configuration driver request bytes changed before training work')
    return _chain(request), manifest


def _publish_receipt(path, value, chain, *, limit=LIMIT):
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials

    materials.observation_bytes(value, limit - 1)
    raw = chain.adapter.canonical(value) + b'\n'
    protocol.publish(path, value, chain.root)
    materials.confirm_file(path, raw, chain.root)
    return raw


def _reference_read(projection, selected, request, request_raw, observations):
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials
    from ergora.training.runtime.evidence import _reference_projection

    _chain(request)
    manifest = materials.decode_record(protocol.read_raw(Path(request['manifest'])))
    return _reference_projection(projection, selected, request, hashlib.sha256(request_raw).hexdigest(), observations, manifest)


def _record_reference(driver, context, request, output, observations, configuration_raw, request_raw, manifest, *, frozen=None, cpu_window=None):
    """Collect already executed source facts under the original full job and clock."""
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials
    from ergora.training.runtime.evidence import _receipt_coverage, _measurement, _resource_coverage

    chain, _ = _inputs(request, request_raw)
    evidence_path = output / 'evidence.json'
    evidence_raw = protocol.read_raw(evidence_path)
    evidence = materials.decode_record(evidence_raw)
    originals, artifacts = {}, {}
    for item in evidence['artifacts']:
        _exact(item, ('path', 'sha256'), 'Full evidence artifact')
        path = output / materials.relative(item['path'])
        original = materials.read_raw(path, 16 * LIMIT)
        if item['path'] in artifacts or hashlib.sha256(original).hexdigest() != item['sha256']:
            raise ValueError('Full evidence has duplicate or changed original artifacts')
        originals[path] = original
        artifacts[item['path']] = {**item, 'bytes': len(original)}
    for cpu_path, cpu_raw in (frozen or {}).items():
        originals[cpu_path] = cpu_raw
        relative = cpu_path.relative_to(output).as_posix()
        artifacts[relative] = {'path': relative, 'sha256': hashlib.sha256(cpu_raw).hexdigest(), 'bytes': len(cpu_raw)}
    data = materials.decode_record(materials.observation_bytes(driver['baseline_reference_record'](context, request, output)))
    _exact(data, ('baseline', 'oracle', 'environment', 'measurement', 'resources'), 'Source baseline record')
    if 'core_cpu_execution' in data['baseline']:
        raise ValueError('Source cannot supply a core-owned CPU window proof')
    if cpu_window is not None and request['execution'].get('cpu_contract') is not None:
        data['baseline']['core_cpu_execution'] = _cpu_core_window(request, 'baseline', 'unprofiled',
            [{key: item['provenance'][key] for key in ('run_id', 'window_id')} for item in data['measurement']], *cpu_window)
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
            or hashlib.sha256(source_originals['baseline-reference-protocol-source.py.txt']).hexdigest() != capability['gate_sources']['training/execution_protocol.py']
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
        return materials.decode_record(original)

    chain.originals[chain.folder.parent / 'configuration-request.json'] = request_raw
    _receipt_coverage(receipt, materials.decode_record(configuration_raw), request, manifest, request['binding'], artifacts, artifact, chain)
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


def _record_profile(driver, context, request, output, request_raw, *, first_failure=None, guards=None):
    """Run a separate source-owned diagnostic inside the original managed wrapper/cap."""
    import cProfile
    import platform
    import signal
    import time
    import ergora.training.materials as materials
    from ergora.training.runtime.evidence import _Inventory, _profile_report, _profile_contents, profile_bundle

    policy = request['execution'].get('profile')
    if policy is None:
        return {}
    materials.validate_profile_policy(policy, request['configuration_readback'].get('profile'))
    chain, _ = _inputs(request, request_raw)
    guards = _Inventory() if guards is None else guards
    guards.confirm()
    phase = 'screen' if request['execution']['operation'] == 'training-screen-v1' else 'baseline'
    capability = request['configuration_readback'].get('profile')
    reason = None
    if phase not in policy['phases']:
        raise ValueError('Profile policy does not select the actual execution phase')
    if first_failure is not None:
        status, reason = 'not_run', 'first_failure: no further diagnostic training window is authorized'
    elif (policy['tool'] != 'cprofile-json' or policy['reader'] != 'cprofile-json-v1'
            or policy['source_operation'] != 'cpu-diagnostic-v1'):
        status, reason = 'unavailable', 'requested tool/reader/source operation has no supported capture operation'
    elif not capability or capability['protocol'] != 'training-profile-v1' or policy['source_operation'] not in capability['operations']:
        status, reason = 'unavailable', 'trusted source does not declare the requested diagnostic operation'
    elif not hasattr(signal, 'SIGALRM') or not hasattr(signal, 'setitimer'):
        status, reason = 'unavailable', 'this platform has no supported in-process diagnostic sub-cap enforcement'
    elif policy['ranks'] != [0]:
        status, reason = 'unavailable', 'CPU diagnostic operation supports actual local rank zero only'
    elif not callable(driver.get('profile')):
        status, reason = 'unavailable', 'trusted source has no callable profile operation'
    else:
        status = 'complete'
    receipt = {'schema_version': 1, 'kind': 'training-profile-receipt', 'policy': policy,
        'policy_sha256': materials.observation_sha256(policy), 'binding': request['binding'], 'managed': request['managed'],
        'source': request['configuration_readback']['source'], 'configuration_request_sha256': hashlib.sha256(request_raw).hexdigest(),
        'phase': phase, 'tool': policy['tool'], 'reader': policy['reader'], 'source_operation': policy['source_operation'],
        'status': status, 'reason': reason, 'captures': [], 'attempts': [], 'raw_bytes': 0, 'derived_bytes': 0,
        'readback': 'complete' if status == 'complete' else 'not_run'}
    originals = {}
    started = time.monotonic()

    def ref(path, raw):
        return {'path': path.relative_to(output).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

    def expired(signum, frame):
        raise TimeoutError('Profile diagnostic exhausted its original selected sub-cap')

    if status == 'complete':
        try:
            for ordinal in range(policy['captures']):
                chain, _ = _inputs(request, request_raw)
                guards.confirm()
                remaining = policy['maximum_seconds'] - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError('Profile diagnostic exhausted its original selected sub-cap')
                identity = materials.observation_sha256({'request': hashlib.sha256(request_raw).hexdigest(),
                    'phase': phase, 'rank': 0, 'capture': ordinal})
                selection = {'phase': phase, 'rank': 0, 'capture_index': ordinal,
                    'window_id': 'profile-window-' + identity[:24], 'run_id': 'profile-run-' + identity[:24],
                    'window': policy['window'], 'source_operation': policy['source_operation']}
                receipt['attempts'].append({'selection': selection, 'capture': 'attempted', 'readback': 'not_run', 'reason': None})
                profiler = cProfile.Profile()
                previous_handler = signal.getsignal(signal.SIGALRM)
                previous_timer = signal.getitimer(signal.ITIMER_REAL)
                signal.signal(signal.SIGALRM, expired)
                signal.setitimer(signal.ITIMER_REAL, min(remaining, previous_timer[0]) if previous_timer[0] > 0 else remaining)
                capture_started = time.monotonic()
                try:
                    cpu_before = _cpu_window_snapshots(request, request_raw)
                    actual = profiler.runcall(driver['profile'], context, request, output,
                        selection=materials.decode_record(materials.observation_bytes(selection)))
                    cpu_after = _cpu_window_snapshots(request, request_raw)
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, previous_handler)
                    if previous_timer[0] > 0:
                        signal.setitimer(signal.ITIMER_REAL, max(0.000001, previous_timer[0] - (time.monotonic() - capture_started)), previous_timer[1])
                _inputs(request, request_raw)
                actual = materials.decode_record(materials.observation_bytes(actual))
                if 'core_cpu_execution' in actual['hardware']:
                    raise ValueError('Source cannot supply a core-owned CPU window proof')
                if request['execution'].get('cpu_contract') is not None:
                    actual['hardware']['core_cpu_execution'] = _cpu_core_window(request, phase, 'profiled',
                        [{key: selection[key] for key in ('run_id', 'window_id')}], cpu_before, cpu_after)
                entries = profiler.getstats()
                def identity_for(code):
                    return code if isinstance(code, str) else f'{code.co_filename}:{code.co_firstlineno}:{code.co_name}'
                functions = [{'function': identity_for(entry.code), 'calls': entry.callcount,
                    'recursive_calls': entry.reccallcount, 'inline_seconds': entry.inlinetime,
                    'total_seconds': entry.totaltime,
                    'callees': sorted(identity_for(call.code) for call in (entry.calls or []))} for entry in entries]
                capture = {'schema_version': 1, 'kind': 'training-cprofile-json',
                    'tool': {'name': 'cprofile-json', 'version': platform.python_version(), 'build': platform.python_implementation() + ' ' + ' '.join(platform.python_build())},
                    'reader': policy['reader'], 'source': request['configuration_readback']['source'],
                    'binding': request['binding'], 'managed': request['managed'],
                    'configuration_request_sha256': hashlib.sha256(request_raw).hexdigest(), 'selection': selection, 'actual': actual,
                    'elapsed_seconds': time.monotonic() - capture_started,
                    'functions': sorted(functions, key=lambda entry: entry['function'])}
                raw = materials.observation_bytes(capture, policy['max_raw_bytes']) + b'\n'
                _, text = _profile_report(raw)
                derived = text.encode('utf-8')
                if receipt['raw_bytes'] + len(raw) > policy['max_raw_bytes'] or receipt['derived_bytes'] + len(derived) > policy['max_derived_bytes']:
                    raise ValueError('capacity_exceeded: complete profile raw/derived evidence')
                capture_path = output / f'profile/{phase}-0-{ordinal}.json'
                derived_path = capture_path.with_suffix('.txt')
                for path, original in ((capture_path, raw), (derived_path, derived)):
                    _inputs(request, request_raw)
                    materials.publish_material(path, original, chain.root)
                    originals[path] = original
                    guards.read(output, path.relative_to(output).as_posix(), 'profile', hashlib.sha256(original).hexdigest(), 16 * LIMIT)
                    _inputs(request, request_raw)
                receipt['captures'].append({'raw_ref': ref(capture_path, raw), 'derived_ref': ref(derived_path, derived), 'selection': selection})
                receipt['raw_bytes'] += len(raw)
                receipt['derived_bytes'] += len(derived)
                receipt['attempts'][-1].update(capture='complete', readback='complete')
                guards.confirm()
                _inputs(request, request_raw)
            _profile_contents(output, policy, request={**request, '_raw_sha256': hashlib.sha256(request_raw).hexdigest()},
                inventory=guards, receipt_raw=materials.observation_bytes(receipt) + b'\n')
            _inputs(request, request_raw)
            if time.monotonic() - started > policy['maximum_seconds']:
                raise TimeoutError('Profile diagnostic exhausted its original selected sub-cap during readback')
        except (OSError, ValueError, RuntimeError, TimeoutError) as error:
            # A failed partial capture is never treated as optional unavailable.
            # Preserve any raw files in place; no retry or replacement window.
            receipt.update(status='failed', reason=type(error).__name__ + ': ' + str(error), readback='failed')
            if receipt['attempts']:
                receipt['attempts'][-1].update(reason=receipt['reason'])
                if receipt['attempts'][-1]['capture'] != 'complete':
                    receipt['attempts'][-1].update(capture='failed', readback='not_run')
                else:
                    receipt['attempts'][-1]['readback'] = 'failed'
    _inputs(request, request_raw)
    path = output / 'profile-receipt.json'
    originals[path] = _publish_receipt(path, receipt, chain)
    guards.read(output, path.name, 'profile', hashlib.sha256(originals[path]).hexdigest())
    guards.confirm()
    _inputs(request, request_raw)
    # Read the exact original finite JSON back with the fixed reader. Continuation
    # admission remains the protocol/packet owner's job, including requiredness.
    profile_bundle(output, policy, request={**request, '_raw_sha256': hashlib.sha256(request_raw).hexdigest()}, inventory=guards)
    _inputs(request, request_raw)
    if receipt['status'] == 'complete' and time.monotonic() - started > policy['maximum_seconds']:
        raise TimeoutError('Profile original selected sub-cap exhausted during durable receipt/readback')
    return originals


def _record_screen(driver, context, request, output, observations, frozen, raw, manifest, guards, reference_project):
    """Publish actual candidate-only observations inside the existing managed job."""
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials
    from ergora.training.runtime.evidence import _screen_data, _screen_bundle, _baseline_reference

    chain, _ = _inputs(request, raw)
    first = None

    def record_first_failure(failure):
        nonlocal first
        materials.observation_bytes(failure)
        _exact(failure, ('check_id', 'rank', 'phase', 'window_id', 'work_index', 'observation_order', 'diagnostic_refs'), 'Screen first failure')
        if (first is not None or failure['check_id'] not in {item['id'] for item in request['execution']['plan']['checks']}
                or any(type(failure[key]) is not int or failure[key] < 0 for key in ('rank', 'work_index', 'observation_order'))
                or any(not isinstance(failure[key], str) or not failure[key] for key in ('phase', 'window_id'))
                or not isinstance(failure['diagnostic_refs'], list)):
            raise ValueError('Screen first failure is duplicate or has no actual check/observation identity')
        # The final report does not exist yet. Authenticate each existing raw
        # diagnostic now, then bind it again to the final complete index.
        for ref in failure['diagnostic_refs']:
            _exact(ref, ('path', 'sha256', 'bytes'), 'Screen failure diagnostic')
            original = guards.read(output, ref['path'], 'screen', ref['sha256'], 16 * LIMIT)
            if type(ref['bytes']) is not int or len(original) != ref['bytes'] or hashlib.sha256(original).hexdigest() != ref['sha256']:
                raise ValueError('Screen first failure diagnostic differs from its original raw bytes')
            materials.confirm_file(output / ref['path'], original, chain.root)
        first = {'schema_version': 1, 'kind': 'training-screen-first-failure', 'binding': request['binding'],
            'configuration_request_sha256': hashlib.sha256(raw).hexdigest(), 'source': request['configuration_readback']['source'],
            'failure': materials.decode_record(materials.observation_bytes(failure))}
        path = output / 'screen-first-failure.json'
        frozen[path] = _publish_receipt(path, first, chain)
        guards.read(output, path.name, 'screen', hashlib.sha256(frozen[path]).hexdigest())
        guards.confirm()
        _inputs(request, raw)

    # No work follows a last source/read/receipt return without this admission.
    chain, _ = _inputs(request, raw)
    guards.confirm()
    chain, _ = _inputs(request, raw)
    if protocol.budget_clock.remaining(request['context']['authorization']['clock'], request['context']['policy']['wall_seconds'],
            request['context']['policy']['cleanup_seconds']) < 1:
        raise ValueError('blocked: remaining original work allowance is below supported screen walltime')
    cpu_before = _cpu_window_snapshots(request, raw)
    data = materials.decode_record(materials.observation_bytes(driver['screen'](context, request, output, record_first_failure=record_first_failure)))
    cpu_after = _cpu_window_snapshots(request, raw)
    if 'core_cpu_execution' in data['workload']['scope']:
        raise ValueError('Source cannot supply a core-owned CPU window proof')
    if request['execution'].get('cpu_contract') is not None:
        data['workload']['scope']['core_cpu_execution'] = _cpu_core_window(request, 'screen', 'unprofiled',
            [{key: item['provenance'][key] for key in ('run_id', 'window_id')} for item in data['windows']], cpu_before, cpu_after)
    if request['execution'].get('profile') is not None:
        from ergora.training.runtime.evidence import validate_cpu_applicability
        selected = _baseline_reference(reference_project, request['context']['intent']['control_home'], request['baseline_reference'], inventory=guards)
        validate_cpu_applicability(selected, observations=observations, screen=data)
    _inputs(request, raw)
    _exact(data, ('workload', 'windows', 'checks', 'checks_not_run', 'resources', 'artifacts', 'reasons'), 'Screen source report')
    path = output / 'screen-source-report.json'
    frozen[path] = _publish_receipt(path, data, chain)
    frozen.update(_record_profile(driver, context, request, output, raw, first_failure=first, guards=guards))
    source = request['configuration_readback']['source']
    capability = chain.owner['execution_capability']
    core_raw = {
        'screen-source-inventory.raw': _git(Path(request['trusted_repo']), 'ls-tree', '-r', '-z', '--full-tree', source['commit']),
        'baseline-reference-protocol-source.py.txt': protocol.read_raw(Path(protocol.__file__)),
        'baseline-reference-native-descriptor.json': protocol.read_raw(Path(capability['installation']) / 'ergora-native-runtime.json')}
    if (hashlib.sha256(core_raw['screen-source-inventory.raw']).hexdigest() != source['inventory_sha256']
            or hashlib.sha256(core_raw['baseline-reference-protocol-source.py.txt']).hexdigest() != capability['gate_sources']['training/execution_protocol.py']
            or hashlib.sha256(core_raw['baseline-reference-native-descriptor.json']).hexdigest() != capability['descriptor_sha256']):
        raise ValueError('Screen source bytes differ from original admitted source closure')
    for index, check in enumerate(request['execution']['plan']['checks']):
        original = protocol.read_raw(_file(request['trusted_repo'], check['source_entrypoint']), 10 * LIMIT)
        if hashlib.sha256(original).hexdigest() != check['contract_sha256']:
            raise ValueError('Screen oracle changed during actual candidate work')
        core_raw['screen-oracles/' + str(index) + '.raw'] = original
    for arm in ('baseline', 'candidate'):
        original = materials.read_raw(Path(request['configurations'][arm]['path']), 10 * LIMIT)
        if hashlib.sha256(original).hexdigest() != request['configurations'][arm]['source_sha256']:
            raise ValueError('Screen configuration input changed during actual work')
        core_raw['screen-configuration-inputs/' + arm + '.raw'] = original
    for name, original in core_raw.items():
        path = output / name
        materials.publish_material(path, original, chain.root)
        frozen[path] = original

    def ref(path, original):
        return {'path': path.relative_to(output).as_posix(), 'sha256': hashlib.sha256(original).hexdigest(), 'bytes': len(original)}

    source_manifest = {'schema_version': 1, 'kind': 'training-execution-source-manifest',
        'capability_sha256': chain.sha(capability), 'gate_sources': capability['gate_sources'],
        'protocol_source_ref': ref(output / 'baseline-reference-protocol-source.py.txt', core_raw['baseline-reference-protocol-source.py.txt']),
        'native_descriptor_ref': ref(output / 'baseline-reference-native-descriptor.json', core_raw['baseline-reference-native-descriptor.json'])}
    path = output / 'screen-execution-sources.json'
    frozen[path] = _publish_receipt(path, source_manifest, chain)
    originals = dict(frozen)
    if not isinstance(data['artifacts'], list) or len(data['artifacts']) > 256:
        raise ValueError('capacity_exceeded: screen source artifact index')
    for item in data['artifacts']:
        _exact(item, ('path', 'sha256', 'bytes'), 'Screen source artifact')
        path = output / materials.relative(item['path'])
        original = guards.read(output, item['path'], 'screen', item['sha256'], 16 * LIMIT)
        if hashlib.sha256(original).hexdigest() != item['sha256'] or type(item['bytes']) is not int or len(original) != item['bytes']:
            raise ValueError('Screen source artifact differs from its actual raw output')
        if path in originals and originals[path] != original:
            raise ValueError('Screen source changed a core receipt or raw input')
        originals[path] = original
    artifacts = [ref(path, original) for path, original in sorted(originals.items())]
    if len(artifacts) > 256 or sum(item['bytes'] for item in artifacts) > 64 * LIMIT:
        raise ValueError('capacity_exceeded: complete screen raw inventory')
    indexed = {item['path']: item for item in artifacts}

    def read(item, metadata=True):
        entry = indexed.get(item.get('path'))
        if entry is None or len(item) != 1 and item != entry:
            raise ValueError('Screen report references unindexed raw data')
        original = originals[output / entry['path']]
        if not metadata:
            return original
        if len(original) > (8 * LIMIT if entry['path'] == 'baseline-reference-projection.json' else LIMIT):
            raise ValueError('capacity_exceeded: screen metadata')
        return materials.decode_record(original)

    checked_request = {**request, '_raw_sha256': hashlib.sha256(raw).hexdigest()}
    derived = _screen_data(data, checked_request, manifest, read, first)
    result = {'schema_version': 1, 'kind': 'training-screen-result', 'binding': request['binding'],
        'native_request_sha256': request['native_request_sha256'], 'configuration_request_sha256': hashlib.sha256(raw).hexdigest(),
        'runner_sha256': request['runner_sha256'], 'managed': request['managed'], 'source': source,
        'execution_plan_sha256': chain.sha(request['execution']['plan']),
        'configuration_receipt_ref': indexed['configuration-receipt.json'], 'baseline_reference_read_ref': indexed['baseline-reference-read.json'],
        'first_failure_ref': indexed.get('screen-first-failure.json'), **derived, 'artifacts': artifacts}
    for path, original in originals.items():
        materials.confirm_file(path, original, chain.root)
    guards.confirm()
    _inputs(request, raw)
    path = output / 'screen-result.json'
    _publish_receipt(path, result, chain)
    _screen_bundle(output, checked_request, manifest, inventory=guards)
    selected = _baseline_reference(reference_project, request['context']['intent']['control_home'],
        request['baseline_reference'], inventory=guards)
    if materials.observation_bytes(selected, 8 * LIMIT) != materials.observation_bytes(read({'path': 'baseline-reference-projection.json'}), 8 * LIMIT):
        raise ValueError('Original baseline reference changed during candidate screen work')
    guards.confirm()
    _inputs(request, raw)


def _run_local_gpu(driver, context, request, original_raw, output):
    """Give one reviewed full runner its original owner-checked guarded child."""
    from copy import deepcopy
    import signal

    from ergora.runtime import gpu_guard, gpu_pool, processes
    from ergora.training import execution_protocol as protocol

    selected = request['configuration_readback']['local_gpu_pool']
    chain, _ = _inputs(request, original_raw)
    lease_path = chain.folder / 'gpu-lease.json'
    if lease_path.exists() or lease_path.is_symlink():
        raise ValueError('Original training GPU lease opportunity was already observed')
    original = request['context']
    intent, authorization, policy = (original[name] for name in ('intent', 'authorization', 'policy'))
    auth_path = Path(chain.home) / 'training-cycles' / intent['project'] / intent['budget']['cycle_id'] / 'authorization.json'
    attempt_path = chain.folder / 'attempt.json'
    attempt_raw = chain.originals[attempt_path]
    runner_path = chain.folder.parent / 'request.json'
    trusted = Path(request['trusted_repo'])
    trusted_source = _file(trusted, request['configuration_readback']['source']['entrypoint'])

    def reference(path):
        return {'root': str(path.parent), 'relative_path': path.name,
                'raw_sha256': hashlib.sha256(protocol.read_raw(path)).hexdigest(), 'semantic_sha256': None}

    source_refs = [reference(Path(__file__).resolve()), reference(trusted_source)]
    config_ref = reference(runner_path)
    origin = {'kind': 'supervised-command-v1',
              'operation_id': chain.records['launch']['execution_phase_id'],
              'attempt_ref': reference(attempt_path), 'authorization_ref': reference(auth_path),
              'source_sha256': chain.sha(source_refs), 'config_sha256': config_ref['raw_sha256'],
              'clock': authorization['clock'], 'wall_seconds': policy['wall_seconds'],
              'cleanup_reserve_seconds': policy['cleanup_seconds'], 'owner_identity': processes.identity(os.getpid())}

    stopped = False
    used = False
    outcome = None

    def stop_requested(_signum, _frame):
        nonlocal stopped
        stopped = True

    def authorize(expected):
        current, _ = _inputs(request, original_raw)
        if (stopped or expected != origin or current.originals.get(attempt_path) != attempt_raw
                or current.records['ack'] != chain.records['ack']
                or selected['runtime_sha256'] != gpu_pool.runtime_source_sha256()):
            raise ValueError('Original managed training stopped or its GPU attempt changed')
        processes.require_ancestor(os.getpid(), chain.records['attempt']['executor'])

    def run_guarded(argv, *, cwd=None, env=None):
        nonlocal used, outcome
        if used:
            raise ValueError('Original training GPU lease permits one guarded invocation')
        if stopped:
            raise ValueError('Original managed training stopped before GPU guard creation')
        used = True
        active, _ = _inputs(request, original_raw)
        if active.originals.get(attempt_path) != attempt_raw:
            raise ValueError('Original managed GPU attempt changed before guard creation')
        pool = gpu_pool.LocalGpuPool.connect(selected['configuration'], session_id=selected['session_id'])
        pool.verify_runtime(selected['runtime_sha256'])

        publication_error = None

        def before_request(resource_request, lease_id, guard_identity):
            nonlocal publication_error
            try:
                pool.verify_runtime(selected['runtime_sha256'])
                binding = chain.gpu_lease_record(selected, resource_request['request_id'],
                                                 chain.sha(resource_request), lease_id, guard_identity)
                protocol.publish(lease_path, binding, chain.root)
                protocol.confirm_gpu_guard(binding, chain.records['attempt']['supervisor'],
                                           lambda: gpu_pool._remaining(origin), lambda: stopped)
            except Exception as error:
                publication_error = error
                raise

        outcome = gpu_guard.run_owned_guard(pool, origin, argv, trusted if cwd is None else Path(cwd),
            dict(os.environ) if env is None else env, device_uuids=selected['ordered_device_uuids'],
            source_refs=source_refs, config_ref=config_ref,
            guard_source_refs=[reference(Path(module.__file__).resolve()) for module in (gpu_guard, processes)],
            authorize=authorize, stop_requested=lambda: stopped, before_request=before_request)
        if publication_error is not None:
            raise publication_error
        return deepcopy(outcome)

    previous_term = signal.signal(signal.SIGTERM, stop_requested)
    previous_int = signal.signal(signal.SIGINT, stop_requested)
    try:
        driver['run'](context, request, output, run_guarded=run_guarded)
    finally:
        signal.signal(signal.SIGINT, previous_int)
        signal.signal(signal.SIGTERM, previous_term)
    if stopped or not outcome or (outcome['process_result'] or {}).get('status') != 'succeeded':
        raise ValueError('Original training GPU runner has no confirmed successful guarded child result')


def main(request_path):
    """Construct, observe, freeze and run the same source-owned configuration objects."""
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials

    raw = protocol.read_raw(Path(request_path), 16 * LIMIT)
    request = materials.decode_record(raw)
    _exact(request, ('schema_version', 'kind', 'binding', 'native_request_sha256', 'runner_sha256',
                     'configuration_readback', 'baseline_reference', 'execution', 'execution_phase_id', 'configurations', 'trusted_repo', 'manifest', 'output', 'context', 'managed',
                     *(['cpu_contract_preparation', 'cpu_contract_core'] if 'cpu_contract_preparation' in request else [])),
           'Configuration driver request')
    if type(request['schema_version']) is not int or request['schema_version'] != 1 or request['kind'] != 'training-configuration-driver-request':
        raise ValueError('Unsupported configuration driver request')
    materials.observation_bytes(request, 16 * LIMIT)
    execution = request['context']['intent']['execution']
    from ergora.native.resources import validate_installation

    installation = validate_installation(Path(execution['installation']), training=True)
    if str(installation) != execution['installation']:
        raise ValueError('Configuration driver requires its original canonical native installation')
    paths = [str(installation / part) for part in ('local', 'upstream/platform', 'upstream/temporal', 'upstream')]
    sys.path[:0] = paths
    os.environ.update(AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                      AGENTFLOW_STATE_DIR=execution['state_directory'],
                      PYTHONPATH=os.pathsep.join([str(IMPORT_ROOT), *paths]))
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
    _cpu_wrapper_context(request, raw, 'cpu-wrapper-context.json')
    driver = runpy.run_path(str(_file(trusted, request['configuration_readback']['source']['entrypoint'])))
    screen_operation = request['execution']['operation'] == 'training-screen-v1'
    for operation in ('prepare', 'describe', 'screen' if screen_operation else 'run'):
        if not callable(driver.get(operation)):
            raise ValueError('Configuration driver does not support ' + operation)
    supports_reference = request['configuration_readback']['baseline_reference_protocol'] == 'baseline-reference-v1'
    if supports_reference:
        for operation in (('baseline_reference_read',) if screen_operation else ('baseline_reference_read', 'baseline_reference_record')):
            if not callable(driver.get(operation)):
                raise ValueError('Configuration driver does not support ' + operation)
    _inputs(request, raw)
    context = driver['prepare'](request)
    observations = _observations(driver['describe'](context), request)
    # Copy the observation now: describe must not retain mutable aliases into it.
    observations = materials.decode_record(materials.observation_bytes(observations))
    receipt = {'schema_version': 1, 'kind': 'training-configuration-receipt',
               'request_sha256': hashlib.sha256(raw).hexdigest(), 'binding': request['binding'],
               'native_request_sha256': request['native_request_sha256'], 'runner_sha256': request['runner_sha256'],
               'managed': request['managed'], 'source': request['configuration_readback']['source'],
               'environment_fingerprint': manifest['environment_fingerprint'], 'observations': observations,
               'configuration_inputs': materials.input_descriptor(manifest), 'configurations': request['configurations'],
               'execution_plan_sha256': chain.sha(request['execution'].get('plan'))}
    materials.observation_bytes(receipt, LIMIT - 1)
    receipt_raw = chain.adapter.canonical(receipt) + b'\n'
    protocol.publish(receipt_path, receipt, chain.root)
    materials.confirm_file(receipt_path, receipt_raw, chain.root)
    frozen = {receipt_path: receipt_raw}
    guards = None
    if screen_operation:
        from ergora.training.runtime.evidence import _Inventory
        guards = _Inventory()
        guards.read(output, receipt_path.name, 'screen', hashlib.sha256(receipt_raw).hexdigest())
    reference_project = None
    if request['baseline_reference'] is not None:
        from ergora.training.runtime.evidence import _baseline_reference
        from ergora.training.runtime.context import _TrainingProject

        project = _TrainingProject({'project': request['context']['project'], 'control_home': request['context']['intent']['control_home']})
        reference_project = project
        selected = _baseline_reference(project, request['context']['intent']['control_home'], request['baseline_reference'], inventory=guards)
        if screen_operation and request['execution'].get('profile') is not None:
            from ergora.training.runtime.evidence import validate_cpu_applicability
            validate_cpu_applicability(selected, observations=observations)
        if screen_operation and request['execution'].get('profile') is not None:
            from ergora.training.runtime.evidence import validate_trial_diagnostics
            validate_trial_diagnostics(selected.get('diagnostics'), request['execution']['profile'])
        if selected['reference_sha256'] != request['baseline_reference']['reference_sha256']:
            raise ValueError('Baseline reference content differs from the frozen selector')
        reference = selected['reference']
        before_reference = materials.observation_bytes(reference, 8 * LIMIT)
        projection = driver['baseline_reference_read'](context, request, reference)
        if materials.observation_bytes(reference, 8 * LIMIT) != before_reference:
            raise ValueError('Baseline reference changed during its source-owned read callback')
        read = _reference_read(projection, selected, request, raw, observations)
        read_path = output / 'baseline-reference-read.json'
        frozen[read_path] = _publish_receipt(read_path, read, chain)
        if guards is not None:
            guards.read(output, read_path.name, 'screen', hashlib.sha256(frozen[read_path]).hexdigest())
        if screen_operation:
            projection_path = output / 'baseline-reference-projection.json'
            frozen[projection_path] = _publish_receipt(projection_path, selected, chain, limit=8 * LIMIT)
            guards.read(output, projection_path.name, 'screen', hashlib.sha256(frozen[projection_path]).hexdigest())
        # Re-read the same full immutable inventory after the callback and the
        # durable receipt; then the existing last admission follows all I/O.
        again = _baseline_reference(project, request['context']['intent']['control_home'], request['baseline_reference'], inventory=guards)
        if materials.observation_bytes(again['reference'], 8 * LIMIT) != before_reference:
            raise ValueError('Baseline reference changed before current full work')
    if request['execution'].get('profile') is not None:
        from ergora.training.runtime.evidence import _cpu_observations
        _cpu_observations(observations)
    if materials.observation_bytes(_observations(driver['describe'](context), request)) != materials.observation_bytes(observations):
        raise ValueError('Configuration changed after observation and before training work')
    _inputs(request, raw)
    _cpu_wrapper_context(request, raw, 'cpu-wrapper-prepared-context.json')
    frozen.update(_cpu_complete_materials(request, raw))
    if screen_operation:
        for cpu_path, cpu_raw in frozen.items():
            guards.read(output, cpu_path.relative_to(output).as_posix(), 'screen', hashlib.sha256(cpu_raw).hexdigest(), 16 * LIMIT)
        _record_screen(driver, context, request, output, observations, frozen, raw, manifest, guards, reference_project)
        return
    cpu_before = _cpu_window_snapshots(request, raw)
    if 'local_gpu_pool' in request['configuration_readback']:
        _run_local_gpu(driver, context, request, raw, output)
    else:
        driver['run'](context, request, output)
    cpu_after = _cpu_window_snapshots(request, raw)
    _inputs(request, raw)
    frozen.update(_record_profile(driver, context, request, output, raw))
    if supports_reference:
        frozen.update(_record_reference(driver, context, request, output, observations, receipt_raw, raw, manifest, frozen=frozen, cpu_window=(cpu_before, cpu_after)))
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
        evidence = materials.decode_record(protocol.read_raw(evidence_path))
        for artifact in artifacts:
            existing = [item for item in evidence['artifacts'] if item['path'] == artifact['path']]
            if existing and existing != [artifact]:
                raise ValueError('Full evidence contains a conflicting configuration input or receipt')
            if not existing:
                evidence['artifacts'].append(artifact)
        # This is the runner-owned unfinished output, not an immutable archive.
        evidence_path.write_bytes(materials.observation_bytes(evidence, LIMIT - 1) + b'\n')
    _inputs(request, raw)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Expected the original managed configuration request path')
    main(Path(sys.argv[1]))
