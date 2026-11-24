from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
import tomllib

from .core import CONFIG, STATE, UPSTREAM, environment, git, read, require, write


def child_environment(model: str | None) -> dict[str, str]:
    require(model in {None, 'codex'}, 'Unsupported model runner')
    source = environment()
    names = {'PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'TZ', 'TMPDIR', 'TERM',
             'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
             'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}
    if model == 'codex':
        names.add('CODEX_HOME')
        config_path = CONFIG / 'codex.toml'
        try:
            config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
        except tomllib.TOMLDecodeError:
            # Selected agents share this monitor; Codex validates its own configuration.
            config = {}
        providers = config.get('model_providers', {})
        provider_id = config.get('model_provider')
        provider = providers.get(provider_id) if isinstance(providers, dict) and isinstance(provider_id, str) else None
        if isinstance(provider, dict):
            credential = provider.get('env_key')
            if provider.get('requires_openai_auth') is not True and isinstance(credential, str):
                names.add(credential)
            headers = provider.get('env_http_headers', {})
            if isinstance(headers, dict):
                names.update(name for name in headers.values() if isinstance(name, str))
    else:
        names.update({'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'LD_LIBRARY_PATH',
                      'OMP_NUM_THREADS', 'MLFLOW_TRACKING_URI'})
        names.update(k for k in source if k.startswith(('NCCL_', 'TORCH_')))
    env = {k: v for k, v in source.items() if k in names or k.startswith('LC_')}
    env.update(PYTHONDONTWRITEBYTECODE='1', DO_NOT_TRACK='1')
    return env


def mapped_command(request: dict) -> list[str]:
    mappings = {'/out': request['output'], '/protocol': request['protocol'],
                '/policy': request['policy'], '/platform/upstream': str(UPSTREAM)}
    command = []
    for item in request['command']:
        for prefix, target in mappings.items():
            if item == prefix or item.startswith(prefix + '/'):
                require(target is not None, 'Missing path mapping: ' + prefix)
                item = target + item[len(prefix):]
                break
        command.append(item)
    return command


def snapshot(checkout: Path) -> tuple[str, str, str]:
    content = hashlib.sha256(git(checkout, 'diff', '--binary', 'HEAD', '--').stdout.encode())
    for relative in git(checkout, 'ls-files', '--others', '--exclude-standard', '-z').stdout.split('\0'):
        if not relative: continue
        path = checkout / relative
        content.update(relative.encode())
        if path.is_symlink(): content.update(os.readlink(path).encode())
        else:
            with path.open('rb') as stream: content.update(hashlib.file_digest(stream, 'sha256').digest())
    return (git(checkout, 'rev-parse', 'HEAD').stdout.strip(),
            git(checkout, 'status', '--porcelain=v1', '-z', '--untracked-files=all').stdout,
            content.hexdigest())


def stop(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def _cpu_read_raw(path, limit=16 * 1_048_576):
    """Bound and confirm one original bootstrap file without following links or FIFOs."""
    path = Path(path)
    require(path.is_absolute() and str(path) == os.path.normpath(str(path)) and len(path.parts) <= 64,
            'CPU bootstrap requires an ordinary absolute original path')
    with contextlib.ExitStack() as resources:
        def opened(name, flags, parent=None):
            fd = os.open(name, flags | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            resources.callback(os.close, fd)
            return fd
        def route():
            parent = opened(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
            parents = [os.fstat(parent)]
            for part in path.parts[1:-1]:
                parent = opened(part, os.O_RDONLY | os.O_DIRECTORY, parent)
                parents.append(os.fstat(parent))
            return opened(path.name, os.O_RDONLY, parent), [(row.st_dev, row.st_ino) for row in parents]
        fd, parents = route()
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit,
                'CPU bootstrap material must be an ordinary bounded file')
        raw = bytearray()
        while len(raw) <= limit:
            chunk = os.read(fd, min(65536, limit + 1 - len(raw)))
            if not chunk: break
            raw.extend(chunk)
        again, current_parents = route()
        def identity(row):
            return (row.st_dev, row.st_ino, row.st_mode, row.st_size, row.st_mtime_ns, row.st_ctime_ns)
        require(len(raw) <= limit and len(raw) == before.st_size and parents == current_parents
                and identity(before) == identity(os.fstat(fd)) == identity(os.fstat(again)),
                'CPU bootstrap material changed during its complete bounded descriptor read')
        return bytes(raw)


def _cpu_training_module(command, output, process_folder, process_request):
    """Bootstrap only the original admitted fixed core, never ambient ergora."""
    import importlib.util
    from .core import ROOT

    def sha(value):
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    def document(path, limit=16 * 1_048_576):
        def unique(items):
            value = {}
            for key, item in items:
                require(key not in value, 'Duplicate original CPU bootstrap JSON key')
                value[key] = item
            return value
        raw = _cpu_read_raw(path, limit)
        value = json.loads(raw, object_pairs_hook=unique)
        require(isinstance(value, dict), 'CPU bootstrap original JSON must be a complete object')
        return value, raw
    def optional(path, limit=16 * 1_048_576):
        try:
            return document(path, limit)[0]
        except FileNotFoundError:
            return None
    def directory_present(path):
        try:
            metadata = os.stat(path, follow_symlinks=False)
        except FileNotFoundError:
            return False
        require(stat.S_ISDIR(metadata.st_mode), 'Original execution opportunity is not an ordinary directory')
        return True
    process_folder = Path(process_folder)
    require(process_folder.parent == STATE / 'processes' and process_request['name'] == process_folder.name,
            'CPU bootstrap process request lost its original registry owner')
    selected = re.fullmatch(r'af-perf-([A-Za-z0-9][A-Za-z0-9_-]{0,79})-run', process_folder.name)
    if selected is None:
        return None
    ident = selected.group(1)
    require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', ident) is not None, 'Invalid CPU original experiment ID')
    job = STATE / 'training/jobs' / ident
    native, native_raw = document(job / 'request.json')
    manifest, manifest_raw = document(STATE / 'training/manifests' / (ident + '.json'))
    binding = native['experiment']['binding']
    require(binding['experiment_id'] == ident and hashlib.sha256(manifest_raw).hexdigest() == binding['manifest_sha'],
            'CPU bootstrap original native manifest binding changed')
    execution = manifest.get('execution', {})
    require(isinstance(execution, dict), 'CPU bootstrap original execution is malformed')
    # Mode absence is meaningful only after independently saved original bindings.
    # The current native/manifest pair may be coherently restored together.
    managed_path = job / 'managed-execution'
    submission_path = STATE / 'ergora/training-submissions'
    budget_path = submission_path / (ident + '.budget')
    managed = optional(managed_path / 'request.json', 1_048_576)
    configuration = optional(job / 'configuration-request.json')
    owner = optional(budget_path / 'owner.json', 1_048_576)
    start_intent = optional(submission_path / (ident + '.intent.json'))
    preparation_path = STATE / 'ergora/training-preparations'
    intent = optional(preparation_path / (ident + '.intent.json'))
    admission = optional(preparation_path / (ident + '.cpu-contract-admission.json'))
    if start_intent is not None:
        original = start_intent['observation']['experiment']
        require(type(start_intent['schema_version']) is int and start_intent['schema_version'] == 1
            and start_intent['operation'] == 'start' and start_intent['experiment_id'] == ident
            and start_intent['workflow_id'] == 'perf-experiment/' + ident
            and start_intent['project'] == native['runner']['project'] and start_intent['repo'] == native['runner']['repo']
            and original['experiment_id'] == ident and original['spec'] == native['experiment']
            and original['binding'] == binding and original['manifest'] == manifest
            and original['current_runner'] == native['runner']
            and Path(start_intent['execution']['state_directory']) == STATE,
            'CPU bootstrap differs from its original admitted start experiment/source')
    normal = (any(value is not None for value in (managed, configuration, owner, admission))
              or start_intent is not None and 'budget' in start_intent or 'cpu_contract' in execution
              or directory_present(managed_path) or directory_present(budget_path))
    if normal:
        require(all(value is not None for value in (managed, owner, start_intent)),
                'Original managed execution lineage is incomplete; CPU absence cannot select ordinary execution')
        require(managed['kind'] == 'training-execution-request' and managed['experiment_id'] == ident
            and managed['native_request_sha256'] == hashlib.sha256(native_raw).hexdigest()
            and managed['owner_sha256'] == sha(owner) and managed['start_intent_sha256'] == sha(start_intent)
            and owner['intent_sha256'] == sha(start_intent)
            and managed['authorization_sha256'] == owner['authorization_sha256'] == start_intent['budget']['authorization_sha256'],
            'CPU bootstrap differs from its independently saved original managed native request/owner')
        if native['runner'].get('configuration_readback') is not None or 'cpu_contract' in execution:
            require(configuration is not None, 'Original configuration execution request is unavailable')
        if configuration is not None:
            require(configuration['binding'] == binding
                and configuration['native_request_sha256'] == managed['native_request_sha256']
                and configuration['managed']['request_sha256'] == sha(managed)
                and configuration['context']['intent'] == start_intent
                and configuration['context']['authorization']['sha256'] == managed['authorization_sha256']
                and owner['context_sha256'] == sha(configuration['context']),
                'CPU bootstrap original configuration/context/managed binding changed')
    if intent is not None:
        require(intent['experiment_id'] == ident
            and intent['files']['training/manifests/' + ident + '.json'].encode('utf-8') == manifest_raw,
            'CPU bootstrap differs from its independently saved original preparation')
        if intent['schema_version'] == 2:
            require(sha({key: value for key, value in intent.items() if key not in ('confirmation', 'confirmed_preview_sha256')})
                    == intent['confirmed_preview_sha256']
                and intent['confirmation']['request_sha256'] == sha(intent['request'])
                and intent['confirmation']['project_revision'] == intent['project_revision'],
                'CPU bootstrap original preparation confirmation changed')
    if admission is not None:
        require(intent is not None and admission['preparation_intent_sha256'] == sha(intent)
            and admission['manifest_sha256'] == hashlib.sha256(manifest_raw).hexdigest(),
            'CPU bootstrap original CPU admission lost its confirmed preparation')
    if 'cpu_contract' not in execution:
        return None
    contract = execution['cpu_contract']
    require(isinstance(contract, dict), 'CPU bootstrap original typed CPU contract is malformed')
    require(normal and configuration is not None and intent is not None and admission is not None,
            'Typed CPU bootstrap requires its complete original managed execution and preparation')
    require(len(command) == 3 and Path(command[2]) == job / 'configuration-request.json'
        and Path(configuration['output']) == output and output == job / 'run-output',
        'CPU bootstrap moved outside its original managed job or fixed command')
    require(hashlib.sha256(manifest_raw).hexdigest() == configuration['binding']['manifest_sha'], 'CPU bootstrap manifest binding changed')
    require(hashlib.sha256(native_raw).hexdigest() == configuration['native_request_sha256']
        and native['experiment']['binding'] == configuration['binding'], 'CPU bootstrap native request changed')
    capability = owner['execution_capability']
    original_intent = configuration['context']['intent']
    original_experiment = original_intent['observation']['experiment']
    require(original_intent['experiment_id'] == ident and original_experiment['binding'] == configuration['binding']
        and original_experiment['manifest'] == manifest
        and Path(original_intent['execution']['state_directory']) == STATE
        and configuration['runner_sha256'] == sha(native['runner'])
        and contract['implementation']['runner_sha256'] == sha(native['runner'])
        and contract['kind'] == 'training-cpu-execution-contract'
        and contract['implementation']['wrapper_entry'] == 'ergora.training.configuration:main'
        and sha({key: value for key, value in contract.items() if key != 'sha256'}) == contract['sha256'],
        'CPU bootstrap contract is not the original managed source/entry')
    require(owner['context_sha256'] == sha(configuration['context']) and Path(capability['installation']) == ROOT,
            'CPU bootstrap is not bound to its original execution owner/context')
    require(hashlib.sha256(_cpu_read_raw(ROOT / 'ergora-native-runtime.json')).hexdigest() == capability['descriptor_sha256'],
            'CPU bootstrap native installation descriptor changed')
    admission_raw = _cpu_read_raw(preparation_path / (ident + '.cpu-contract-admission.json'))
    require(_cpu_read_raw(output / 'cpu-contract-admission.json') == admission_raw,
            'CPU bootstrap staged acceptance differs from its original admission')
    require(admission['manifest_sha256'] == configuration['binding']['manifest_sha'] and admission['contract_sha256'] == contract['sha256']
        and admission['preparation_intent_sha256'] == sha(intent)
        and admission['confirmed_preview_sha256'] == intent['confirmed_preview_sha256']
        and admission['confirmation'] == intent['confirmation']
        and sha({key: value for key, value in intent.items() if key not in ('confirmation', 'confirmed_preview_sha256')}) == intent['confirmed_preview_sha256']
        and intent['files']['training/manifests/' + ident + '.json'].encode('utf-8') == manifest_raw,
        'CPU bootstrap lacks its original exact contract acceptance')
    core, _ = document(output / 'cpu-core-sources.json')
    package = Path(core['package_directory'])
    require(configuration['cpu_contract_core'] == {'package_directory': str(package),
        'sources_sha256': contract['implementation']['core_sources_sha256']}
        and core['contract_sha256'] == contract['sha256'] and sha(core['sources']) == contract['implementation']['core_sources_sha256'],
        'CPU bootstrap core sources are not the original admitted source closure')
    require(package.is_absolute() and package.resolve() == package and package.name == 'ergora'
        and command == [native['runner']['command'][0], str(package / 'training/configuration.py'), str(job / 'configuration-request.json')],
        'CPU bootstrap has no original fixed wrapper command/package association')
    require({path.relative_to(package).as_posix() for path in package.rglob('*.py')
             if path.relative_to(package).parts[0] != 'data'}
            == {name for name in core['sources'] if name.endswith('.py') and not name.startswith('data/')},
            'CPU bootstrap package inventory changed')
    for name, expected in core['sources'].items():
        require(isinstance(name, str) and not Path(name).is_absolute() and '..' not in Path(name).parts,
                'Invalid CPU core source relative path')
        path = package / name
        require(not any(node.is_symlink() for node in (path, *path.parents))
            and hashlib.sha256(_cpu_read_raw(path)).hexdigest() == expected, 'Original CPU core source bytes changed: ' + name)
    require(hashlib.sha256(_cpu_read_raw(Path(__file__))).hexdigest()
        == core['sources']['data/reference/platform/local/agent_platform/process_job.py'],
        'CPU bootstrap process owner differs from its original native source')
    if 'ergora' in sys.modules:
        require(Path(sys.modules['ergora'].__file__).resolve() == package / '__init__.py', 'Ambient CPU core is not the original selected core')
    else:
        spec = importlib.util.spec_from_file_location('ergora', package / '__init__.py', submodule_search_locations=[str(package)])
        module = importlib.util.module_from_spec(spec)
        sys.modules['ergora'] = module
        spec.loader.exec_module(module)
    import ergora.training.configuration as training_configuration
    require(Path(training_configuration.__file__).resolve() == Path(command[1]), 'CPU helper import did not select original current wrapper')
    return training_configuration



@contextlib.contextmanager
def candidate_check_gate(fence: Path):
    """Serialize a scoped stop with checker admission and terminal publication."""
    require(fence is not None and fence.parent == STATE / 'fences/fixed-candidate-check'
            and re.fullmatch(r'check-[a-f0-9]{40}\.json', fence.name), 'Invalid candidate check fence scope')
    fence.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    gate = fence.with_suffix('.lock')
    descriptor = os.open(gate, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as lock:
        require(stat.S_ISREG(os.fstat(lock.fileno()).st_mode), 'Invalid candidate check gate')
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def run(folder: Path) -> None:
    require(folder.resolve().is_relative_to((STATE / 'processes').resolve()), 'Job is outside the process registry')
    with (folder / 'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        if (folder / 'terminal.json').exists():
            return
        request = read(folder / 'request.json')
        # A lost monitor is an observation gap, not a new process outcome.
        # Leave the original started record and missing terminal intact.
        require(not (folder / 'started.json').exists(),
                'Previous process submission has an unknown outcome. No automatic re-execution; reconcile its recorded PID and output.')
        binding = ({'binding': request['binding'], 'request_sha256': hashlib.sha256(json.dumps(request,
            ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()}
            if 'binding' in request else {})
        output = Path(request['output'])
        output.mkdir(parents=True, exist_ok=True, mode=0o700)
        code = 125
        detail = ''
        process = None
        started = time.time()
        log_path = output / 'execution.log'
        try:
            cutoff = None
            if request.get('deadline') is not None or request.get('binding') is not None:
                from .sandbox import process_deadline
                cutoff = process_deadline(request.get('deadline'), request.get('binding'))
            fence = Path(request['fence']) if request['fence'] else None
            require(fence is None or not fence.exists(), 'Cancelled before process start')
            checkout = Path(request['checkout'])
            before = snapshot(checkout) if not request['writable'] else None
            require(cutoff is None or time.monotonic() < cutoff,
                    'Original process deadline expired during checkout snapshot')
            command = mapped_command(request)
            cpu_module = _cpu_training_module(command, output, folder, request)
            cpu_owned = cpu_module.cpu_process_context(command, output) if cpu_module is not None else None
            write(folder / 'started.json', {'time': started, 'name': request['name'], 'command': command,
                                          'monitor_pid': os.getpid(), **binding})
            with contextlib.ExitStack() as resources:
                log = resources.enter_context(log_path.open('ab'))
                stdin = subprocess.DEVNULL
                if request['model']:
                    stdin = resources.enter_context((Path(request['protocol']) / 'prompt.txt').open('rb'))
                stdout = log
                child_env = child_environment(request['model'])
                if cpu_module is not None:
                    cpu_module.cpu_process_last_admission(cpu_owned)
                scoped = fence is not None and fence.parent == STATE / 'fences/fixed-candidate-check'
                with (candidate_check_gate(fence) if scoped else contextlib.nullcontext()):
                    require(fence is None or not fence.exists(), 'Cancelled at original last process admission')
                    if cutoff is not None:
                        cutoff = process_deadline(request['deadline'])
                    remaining = request['timeout'] if cutoff is None else min(request['timeout'], cutoff - time.monotonic())
                    require(remaining > 0, 'Original process deadline expired at last process admission')
                    process = subprocess.Popen(['/usr/bin/timeout', '--signal=TERM', '--kill-after=5',
                                                str(remaining), *command], cwd=checkout,
                                               stdin=stdin, stdout=stdout, stderr=log,
                                               env=child_env, start_new_session=True,
                                               pass_fds=(lock.fileno(),))
                stat = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()
                write(folder / 'pid.json', {'pid': process.pid, 'start_ticks': stat[19],
                                          'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
                deadline = time.monotonic() + request['timeout'] + 5 if cutoff is None else min(cutoff, time.monotonic() + remaining)
                while process.poll() is None:
                    if (fence and fence.exists()) or time.monotonic() >= deadline:
                        detail = 'Cancellation fence observed' if fence and fence.exists() else 'Process walltime exceeded'
                        stop(process)
                        break
                    time.sleep(.2 if cutoff is None else min(.2, max(0, deadline - time.monotonic())))
                code = process.wait()
            if before is not None and snapshot(checkout) != before:
                code = 126
                detail = 'A stage declared read-only changed the checkout or HEAD; inspect its diff'
        except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
            if process is not None and process.poll() is None:
                stop(process)
            detail = f'{type(error).__name__}: {error}'
            code = 125
        with log_path.open('a') as log:
            log.write('\n' + json.dumps({'returncode': code, 'detail': detail}) + '\n')
        write(folder / 'terminal.json', {'name': request['name'], 'returncode': code,
                                         'detail': detail, 'started_at': started, 'finished_at': time.time(), **binding})


if __name__ == '__main__':
    require(len(sys.argv) == 2, 'Expected a process registry directory')
    run(Path(sys.argv[1]))
