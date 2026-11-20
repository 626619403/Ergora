from __future__ import annotations

import json
import hashlib
import math
import os
from pathlib import Path
import re
import subprocess
import time
import tomllib

from .core import Blocked, CONFIG, PYTHON, STATE, environment, read, require, settings, write


def container_identity() -> dict | None:
    marker = Path('/run/systemd/container')
    kind = marker.read_text().strip() if marker.is_file() else None
    if Path('/.dockerenv').exists(): kind = 'docker'
    if Path('/run/.containerenv').exists(): kind = 'podman'
    if kind not in {'docker', 'podman'}: return None
    return {'kind': kind, 'pid_namespace': os.readlink('/proc/self/ns/pid'),
            'mount_namespace': os.readlink('/proc/self/ns/mnt'),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def process_deadline(deadline: dict | None, binding: dict | None = None) -> float | None:
    if binding is not None:
        require(isinstance(binding, dict) and binding.get('kind') == 'fixed-text-verification-process-v1',
                'Unsupported native process binding')
        require(deadline is not None, 'Fixed verification requires its original process deadline')
    if deadline is None:
        return None
    require(isinstance(deadline, dict) and set(deadline) == {'monotonic', 'boot_id'},
            'Invalid original process deadline')
    cutoff = deadline['monotonic']
    require(type(cutoff) is float and math.isfinite(cutoff) and cutoff > 0,
            'Invalid original process deadline cutoff')
    require(deadline['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'Original process deadline belongs to another boot; execution cannot be renewed')
    return cutoff


class Sandbox:
    """Trusted native processes inside the operator's existing Docker container."""

    def __init__(self):
        self.env = environment()

    def probe(self) -> dict:
        config = settings()
        identity = container_identity()
        container = identity is not None
        accepted = config.get('current_container_trust_acknowledged') is True
        matched = container and config.get('container_boundary') == identity
        return {'available': container and accepted and matched, 'backend': 'current-container',
                'container_detected': container, 'trust_acknowledged': accepted,
                'container_boundary_matches': matched,
                'filesystem_isolation_between_agents': False,
                'detail': 'Trusted projects only; agents run as the current Unix user. The existing container is the security boundary.'}

    def request(self, name: str, checkout: Path, output: Path, command: list[str], *, writable: bool,
                fence: Path | None = None, timeout: int = 1800, model: str | None = None,
                protocol: Path | None = None, policy: Path | None = None, binding: dict | None = None,
                deadline: dict | None = None) -> dict:
        """Construct the original complete frame for capacity admission and execution."""
        require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,159}', name), 'Invalid process job name')
        require(1 <= timeout <= 86400, 'Invalid process walltime')
        process_deadline(deadline, binding)
        request = {'schema_version': 1, 'name': name, 'checkout': str(checkout.resolve()),
                   'output': str(output.resolve()), 'command': command, 'writable': writable,
                   'fence': str(fence) if fence else None, 'timeout': timeout, 'model': model,
                   'protocol': str(protocol) if protocol else None, 'policy': str(policy) if policy else None}
        if binding is not None:
            request['binding'] = binding
        if deadline is not None:
            request['deadline'] = deadline
        return request

    def run(self, name: str, checkout: Path, output: Path, command: list[str], *, writable: bool,
            fence: Path | None = None, timeout: int = 1800, model: str | None = None,
            protocol: Path | None = None, policy: Path | None = None, gitdir: Path | None = None,
            binding: dict | None = None, deadline: dict | None = None) -> int:
        require(self.probe()['available'], 'Current-container execution requires a detected container and acknowledgment bound to its current namespaces')
        request = self.request(name, checkout, output, command, writable=writable, fence=fence,
            timeout=timeout, model=model, protocol=protocol, policy=policy, binding=binding, deadline=deadline)
        folder = STATE / 'processes' / name
        write(folder / 'request.json', request)
        terminal = folder / 'terminal.json'
        launcher = None
        def launch():
            with (folder / 'runner.log').open('ab') as log:
                return subprocess.Popen([str(PYTHON), '-m', 'agent_platform.process_job', str(folder)],
                                        env=self.env, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                        start_new_session=True, close_fds=True)
        wait_deadline = process_deadline(deadline) + 30 if deadline is not None else time.monotonic() + timeout + 30
        last_launch = 0.0
        while not terminal.exists():
            require(not (not terminal.exists() and (folder / 'started.json').exists()
                         and (launcher is None or launcher.poll() is not None)),
                    f'Original process started without a confirmed terminal; outcome unknown. Inspect {folder}')
            if deadline is not None and time.monotonic() >= wait_deadline:
                raise Blocked(f'Process outcome unknown; inspect {folder}. It will not be resubmitted automatically.')
            if (launcher is None or launcher.poll() is not None) and time.monotonic() - last_launch > 2:
                launcher = launch()
                last_launch = time.monotonic()
            if time.monotonic() >= wait_deadline:
                raise Blocked(f'Process outcome unknown; inspect {folder}. It will not be resubmitted automatically.')
            time.sleep(0.25)
        result = read(terminal)
        require(result['name'] == name, 'Process terminal record names another job')
        if binding is not None:
            digest = hashlib.sha256(json.dumps(request, ensure_ascii=False, sort_keys=True,
                separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
            require(result['binding'] == binding and result['request_sha256'] == digest,
                    'Process terminal differs from its original bound request')
        if launcher is not None:
            launcher.wait(timeout=5)
        return result['returncode']


def model_protocol(folder: Path, prompt: str, schema: dict, model: str, config: dict) -> list[str]:
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    prompt_path = folder / 'prompt.txt'
    schema_path = folder / 'schema.json'
    for path, content in [(prompt_path, prompt), (schema_path, json.dumps(schema))]:
        if path.exists():
            require(path.read_text() == content, 'Immutable model input changed: ' + str(path))
        else:
            path.write_text(content)
    require(model == 'codex', 'Only the Codex model runner is supported')
    args = [config['codex_bin'], '--no-daemon', '-a', 'never', 'exec', '--json', '--ephemeral',
            '--ignore-user-config', '--ignore-rules', '--skip-git-repo-check',
            '--sandbox', 'danger-full-access', '--disable', 'plugins', '--disable', 'apps']
    data = tomllib.loads((CONFIG / 'codex.toml').read_text())
    def add(table: dict, prefix: str = '') -> None:
        for key, value in table.items():
            name = prefix + key
            if isinstance(value, dict):
                add(value, name + '.')
            elif name not in {'approval_policy'} and not name.startswith('sandbox_'):
                args.extend(['-c', name + '=' + json.dumps(value)])
    add(data)
    return [*args, '--output-schema', str(schema_path), '--output-last-message', '/out/result.json', '-']
