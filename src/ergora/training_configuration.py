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
    _exact(capability, ('protocol', 'source', 'configuration_path', 'manifest_configuration_role',
                        'observation_scheme'), 'Configuration readback')
    if capability['protocol'] != PROTOCOL or capability['manifest_configuration_role'] != 'source-bytes':
        raise ValueError('Unsupported configuration driver protocol or manifest configuration role')
    if (not isinstance(capability['observation_scheme'], str)
            or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', capability['observation_scheme']) is None):
        raise ValueError('Configuration driver requires a versioned observation scheme')
    _relative(capability['configuration_path'])
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
    from agent_platform.core import git
    from ergora import training_execution_protocol as protocol

    active()
    runner = record['runner']
    validate_runner(runner)
    capability = runner['configuration_readback']
    source = capability['source']
    folder = Path(folder)
    trusted = folder / 'configuration-driver'
    if not trusted.exists():
        git(folder, 'clone', '--no-checkout', '--no-local', source['repo'], str(trusted))
        git(trusted, 'checkout', '--detach', source['commit'])
    _checkout(trusted, source['commit'])
    if source_reference(trusted, source['commit'], source['entrypoint']) != {**source, 'repo': str(trusted)}:
        raise ValueError('Configuration driver checkout inventory changed')
    configurations = {}
    for arm, commit_key, hash_key in (('baseline', 'baseline_sha', 'base_config_sha256'),
                                      ('candidate', 'candidate_sha', 'candidate_config_sha256')):
        commit = record['experiment']['binding'][commit_key]
        path, digest = _source_bytes(checkouts[arm], commit, capability['configuration_path'])
        if digest != manifest[hash_key]:
            raise ValueError('Configuration source raw SHA differs from manifest ' + hash_key)
        configurations[arm] = {'repo': str(checkouts[arm]), 'commit': commit, 'path': str(path), 'source_sha256': digest}
    intent = context['intent']
    chain = protocol.ExecutionRecords(context['project'], intent['experiment_id'], intent['control_home']).load()
    request = {'schema_version': 1, 'kind': 'training-configuration-driver-request',
               'binding': record['experiment']['binding'],
               'native_request_sha256': chain.records['request']['native_request_sha256'],
               'runner_sha256': chain.sha(runner), 'configuration_readback': capability,
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
    from ergora import training_execution_protocol as protocol

    chain = _chain(request)
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
    for arm, commit_key, hash_key in (('baseline', 'baseline_sha', 'base_config_sha256'),
                                      ('candidate', 'candidate_sha', 'candidate_config_sha256')):
        repo = chain.folder.parent / arm
        commit = request['binding'][commit_key]
        path, digest = _source_bytes(repo, commit, capability['configuration_path'])
        if request['configurations'][arm] != {'repo': str(repo), 'commit': commit, 'path': str(path), 'source_sha256': digest}:
            raise ValueError('Configuration driver input differs from the original checkout')
        if digest != manifest[hash_key]:
            raise ValueError('Configuration source raw SHA differs from manifest ' + hash_key)
    if protocol.read_raw(chain.folder.parent / 'configuration-request.json', 16 * LIMIT) != original_raw:
        raise ValueError('Configuration driver request bytes changed before training work')
    return _chain(request), manifest


def main(request_path):
    """Construct, observe, freeze and run the same source-owned configuration objects."""
    from ergora import training_execution_protocol as protocol

    raw = protocol.read_raw(Path(request_path), 16 * LIMIT)
    request = protocol.decode(raw)
    _exact(request, ('schema_version', 'kind', 'binding', 'native_request_sha256', 'runner_sha256',
                     'configuration_readback', 'configurations', 'trusted_repo', 'manifest', 'output', 'context', 'managed'),
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
    _inputs(request, raw)
    context = driver['prepare'](request)
    observations = _observations(driver['describe'](context), request)
    # Copy the observation now: describe must not retain mutable aliases into it.
    observations = protocol.decode(_bytes(observations))
    receipt = {'schema_version': 1, 'kind': 'training-configuration-receipt',
               'request_sha256': hashlib.sha256(raw).hexdigest(), 'binding': request['binding'],
               'native_request_sha256': request['native_request_sha256'], 'runner_sha256': request['runner_sha256'],
               'managed': request['managed'], 'source': request['configuration_readback']['source'],
               'environment_fingerprint': manifest['environment_fingerprint'], 'observations': observations}
    _bytes(receipt, LIMIT - 1)
    protocol.publish(receipt_path, receipt, chain.root)
    saved = protocol.decode(protocol.read_raw(receipt_path))
    if saved != receipt:
        raise ValueError('Configuration receipt differs after durable readback')
    if _bytes(_observations(driver['describe'](context), request)) != _bytes(observations):
        raise ValueError('Configuration changed after observation and before training work')
    _inputs(request, raw)
    driver['run'](context, request, output)
    # Preserve the readback as an ordinary hashed artifact in the original full
    # evidence bundle. The original archive and quality gate remain its owners.
    receipt_raw = protocol.read_raw(receipt_path)
    if protocol.decode(receipt_raw) != saved:
        raise ValueError('Configuration receipt changed during training work')
    evidence_path = output / 'evidence.json'
    if evidence_path.is_file():
        evidence = protocol.decode(protocol.read_raw(evidence_path))
        artifact = {'path': 'configuration-receipt.json', 'sha256': hashlib.sha256(receipt_raw).hexdigest()}
        existing = [item for item in evidence['artifacts'] if item['path'] == artifact['path']]
        if existing and existing != [artifact]:
            raise ValueError('Full evidence contains a conflicting configuration receipt')
        if not existing:
            evidence['artifacts'].append(artifact)
            # This is the runner-owned unfinished output, not an immutable archive.
            evidence_path.write_bytes(_bytes(evidence, LIMIT - 1) + b'\n')


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    if len(sys.argv) != 2:
        raise SystemExit('Expected the original managed configuration request path')
    main(Path(sys.argv[1]))
