"""Prepare pinned home assets; the existing installer creates the environment."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import tarfile
import tempfile
from urllib.request import urlopen


TEMPORAL_SHA = '09a0326a51db84d02735e53542b9ebd8c4758daf47482a9ab0abce15844e60d5'
SYMPHONY_SHA = '08d7aac26747fdc14022ade870cf7e530a6343ab92a040f39a4294b27a0cd5af'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_bundle(root: Path) -> list[Path]:
    entries = []
    for line in (root / 'BUNDLE-SHA256SUMS').read_text().splitlines():
        checksum, name = line.split('  ', 1)
        relative = PurePosixPath(name)
        require(not relative.is_absolute() and '..' not in relative.parts and '\\' not in name,
                'Unsafe bundle checksum path')
        path = root / name
        require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), 'Bundle symlink is not allowed')
        require(path.is_file() and digest(path) == checksum, 'Bundle checksum mismatch: ' + name)
        entries.append(path)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and p.relative_to(root).as_posix() != 'BUNDLE-SHA256SUMS'}
    expected = {p.relative_to(root).as_posix() for p in entries}
    require(actual == expected, 'Bundle has missing or unlisted files; unpack a clean ZIP directory')
    return entries


def source_plan(bundle: Path, destination: Path, entries: list[Path]) -> list[tuple[Path, Path]]:
    payload = bundle / 'platform'
    plan = []
    for source in entries:
        if not source.is_relative_to(payload):
            continue
        target = destination / source.relative_to(payload)
        require(not target.is_symlink() and target.resolve().is_relative_to(destination.resolve()),
                'Destination path escapes the selected platform directory')
        if target.exists():
            require(target.is_file() and digest(target) == digest(source),
                    'Existing source differs; preserve it and review the upgrade manually: ' + str(target))
        else:
            plan.append((source, target))
    return plan


def prerequisites() -> dict:
    require(platform.system() == 'Linux' and platform.machine() in ('x86_64', 'amd64'),
            'This export pins Linux x86_64 runtimes')
    distribution = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines()
                        if '=' in line and not line.startswith('#'))
    require(distribution.get('ID', '').strip('"') == 'ubuntu' and
            distribution.get('VERSION_ID', '').strip('"') == '24.04',
            'The Linux package script targets Ubuntu 24.04')
    return {'distribution': 'Ubuntu 24.04', 'architecture': 'linux-x86_64',
            'user_tools_installed_by_bootstrap': ['Node.js', 'uv', 'Codex'],
            'accounts_required_for_installation': False}


def atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.pending-', dir=target.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def acquire(target: Path, expected: str, url: str, cache: Path | None, *, check: bool) -> str:
    if target.exists():
        require(not target.is_symlink() and digest(target) == expected, 'Pinned runtime checksum mismatch: ' + str(target))
        return 'present-and-verified'
    if cache is not None and cache.exists():
        require(not cache.is_symlink() and digest(cache) == expected, 'Runtime cache checksum mismatch: ' + str(cache))
        if not check:
            atomic_copy(cache, target)
        return 'verified-cache'
    if check:
        return 'needs-network-download'
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.download-', dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as output, urlopen(url, timeout=30) as response:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                require(total <= 256 * 1024 * 1024, 'Unexpected runtime size')
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        require(digest(temporary) == expected,
                'Downloaded runtime SHA differs. A rolling Symphony nightly may have changed; use the exported cache or reviewed pinned-source build. Do not bypass the checksum.')
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return 'downloaded-and-verified'


def temporal_binary(archive: Path, target: Path, *, check: bool = False) -> None:
    with tarfile.open(archive) as bundle:
        members = [item for item in bundle.getmembers() if Path(item.name).name == 'temporal' and item.isfile()]
        require(len(members) == 1 and members[0].size < 256 * 1024 * 1024, 'Unexpected Temporal archive')
        with bundle.extractfile(members[0]) as stream:
            expected = hashlib.file_digest(stream, 'sha256').hexdigest()
        if target.exists():
            require(not target.is_symlink() and digest(target) == expected, 'Existing Temporal binary checksum mismatch')
            return
        if check:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.extract-', dir=target.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, 'wb') as output, bundle.extractfile(members[0]) as stream:
                shutil.copyfileobj(stream, output)
            temporary.chmod(0o755)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)


def install_user_tools(root: Path, pins: dict) -> None:
    node_version = pins['node']
    node_folder = root / 'toolchains' / ('node-v' + node_version + '-linux-x64')
    if not (node_folder / 'bin/node').exists():
        with tarfile.open(root / 'downloads/node.tar.xz') as archive:
            expected_prefix = node_folder.name + '/'
            require(all(member.name == node_folder.name or member.name.startswith(expected_prefix)
                        for member in archive.getmembers()), 'Unexpected Node archive layout')
            archive.extractall(root / 'toolchains', filter='data')
    link = root / 'toolchains/node'
    if not link.exists():
        link.symlink_to(node_folder.name, target_is_directory=True)
    require(link.resolve() == node_folder.resolve(), 'Existing managed Node path names another version')
    with tarfile.open(root / 'downloads/uv.tar.gz') as archive:
        for name in ('uv', 'uvx'):
            members = [member for member in archive.getmembers() if Path(member.name).name == name and member.isfile()]
            require(len(members) == 1, 'Unexpected uv archive layout')
            target = root / 'bin' / name
            with archive.extractfile(members[0]) as stream:
                raw = stream.read()
            if target.exists():
                require(not target.is_symlink() and target.read_bytes() == raw, 'Existing managed uv binary differs')
            else:
                target.write_bytes(raw)
                target.chmod(0o755)
    env = dict(os.environ)
    env['PATH'] = str(link / 'bin') + ':' + str(root / 'bin') + ':' + env.get('PATH', '')
    subprocess.run([str(link / 'bin/npm'), 'ci', '--prefix', str(root / 'tooling'),
                    '--no-audit', '--no-fund', '--registry', 'https://registry.npmjs.org'], env=env, check=True)
    for name in ('codex',):
        target = root / 'bin' / name
        executable = root / 'tooling/node_modules/.bin' / name
        require(executable.exists(), 'npm did not install the model CLI: ' + name)
        if target.exists() or target.is_symlink():
            require(target.resolve() == executable.resolve(), 'Existing managed CLI path differs: ' + name)
        else:
            target.symlink_to(executable)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--mode', choices=['check', 'install'], required=True)
    parser.add_argument('--runtime-cache', default='')
    args = parser.parse_args()
    bundle, destination = args.bundle.resolve(), args.destination.expanduser().resolve()
    entries = verify_bundle(bundle)
    plan = source_plan(bundle, destination, entries)
    tools = prerequisites()
    check = args.mode == 'check'
    cache = Path(args.runtime_cache).expanduser().resolve() if args.runtime_cache else None
    payload = bundle / 'platform'
    temporal = json.loads((payload / 'downloads/temporal-cli.json').read_text())
    symphony = json.loads((payload / 'upstream/symphony/upstream.lock.json').read_text())
    tool_pins = json.loads((payload / 'bootstrap/report/public-release.json').read_text())['native_tools']
    require(temporal['archive_sha256'] == TEMPORAL_SHA and symphony['binary_sha256'] == SYMPHONY_SHA,
            'Runtime pins differ from the reviewed installer')
    for name in ('install-multi-agent-linux-deps.sh', 'install-multi-agent-platform.sh'):
        target = Path.home() / name
        require(not target.exists() or digest(target) == digest(payload / 'bootstrap' / name),
                'Existing home script differs; review it manually: ' + str(target))
    if not check:
        for source, target in plan:
            atomic_copy(source, target)
    runtime = {}
    for name, relative, expected, url in [
        ('temporal_archive', 'downloads/temporal-cli.tar.gz', TEMPORAL_SHA, temporal['source_url']),
        ('symphony', 'bin/symphony', SYMPHONY_SHA, symphony['binary_url']),
        ('node', 'downloads/node.tar.xz', tool_pins['node_archive_sha256'],
         'https://nodejs.org/dist/v' + tool_pins['node'] + '/node-v' + tool_pins['node'] + '-linux-x64.tar.xz'),
        ('uv', 'downloads/uv.tar.gz', tool_pins['uv_archive_sha256'],
         'https://github.com/astral-sh/uv/releases/download/' + tool_pins['uv'] + '/uv-x86_64-unknown-linux-gnu.tar.gz'),
    ]:
        runtime[name] = acquire(destination / relative, expected, url, cache / relative if cache else None, check=check)
    if (destination / 'downloads/temporal-cli.tar.gz').exists():
        temporal_binary(destination / 'downloads/temporal-cli.tar.gz', destination / 'bin/temporal', check=check)
    if not check:
        (destination / 'bin/symphony').chmod(0o755)
        install_user_tools(destination, tool_pins)
        for name in ('install-multi-agent-linux-deps.sh', 'install-multi-agent-platform.sh'):
            target = Path.home() / name
            source = destination / 'bootstrap' / name
            require(not target.exists() or digest(target) == digest(source),
                    'Existing home script differs; review it manually: ' + str(target))
            if not target.exists():
                atomic_copy(source, target)
                target.chmod(0o755)
    print(json.dumps({'mode': args.mode, 'destination': str(destination), 'new_source_files': len(plan),
                      'prerequisites': tools, 'runtimes': runtime, 'services_started': False,
                      'training_started': False}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        raise SystemExit('Installation stopped: ' + str(error))
