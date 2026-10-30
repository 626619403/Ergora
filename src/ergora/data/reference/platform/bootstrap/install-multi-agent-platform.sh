#!/usr/bin/env bash
# Repair/recreate the user environment from its persistent home assets.
set -euo pipefail

platform_root="${AGENTFLOW_ROOT:-$HOME/multi-agent-platform}"
export PATH="$HOME/.local/bin:$PATH"
start_services=0
trust_current=0
for option in "$@"; do
  case "$option" in
    --start) start_services=1 ;;
    --trust-current-container) trust_current=1 ;;
    -h|--help)
      printf '%s\n' 'Usage: bash ~/install-multi-agent-platform.sh [--start] [--trust-current-container]'
      printf '%s\n' 'Uses permanent sources, binaries and requirements.lock in ~/multi-agent-platform. Preserves user configuration.'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$option" >&2; exit 2 ;;
  esac
done

if [[ ! -d "$platform_root/bootstrap/local/agent_platform" || ! -f "$platform_root/requirements.lock" ]]; then
  printf 'Persistent installation assets are missing: %s\n' "$platform_root" >&2
  exit 2
fi
bash "$platform_root/bootstrap/install-multi-agent-linux-deps.sh" --install

python3 - "$platform_root" <<'PY'
import hashlib
from pathlib import Path
import shutil, stat, sys, tarfile, zipfile
root = Path(sys.argv[1])
archive = root / 'source/upstream-original.zip'
expected = '65c71bb985138ed55fcde82c7ccf976cce95ec0169a410341bcc865bcd5ee031'
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise SystemExit('Original report ZIP checksum mismatch')
if not (root / 'upstream').exists():
    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            target = root / 'upstream' / info.filename
            if not target.resolve().is_relative_to((root / 'upstream').resolve()) or stat.S_ISLNK(info.external_attr >> 16):
                raise SystemExit('Unsafe ZIP entry')
        source.extractall(root / 'upstream')
destination = root / 'local/agent_platform'
destination.mkdir(parents=True, exist_ok=True)
for source in (root / 'bootstrap/local/agent_platform').glob('*.py'):
    target = destination / source.name
    if not target.exists(): shutil.copy2(source, target)
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
temporal_archive=root/'downloads/temporal-cli.tar.gz'
if sha(temporal_archive) != '09a0326a51db84d02735e53542b9ebd8c4758daf47482a9ab0abce15844e60d5':
    raise SystemExit('Official Temporal archive checksum mismatch')
with tarfile.open(temporal_archive) as source:
    member=next(item for item in source.getmembers() if Path(item.name).name=='temporal' and item.isfile())
    with source.extractfile(member) as stream: expected=hashlib.file_digest(stream,'sha256').hexdigest()
if sha(root/'bin/temporal') != expected: raise SystemExit('Pinned Temporal binary checksum mismatch')
if sha(root/'bin/symphony') != '08d7aac26747fdc14022ade870cf7e530a6343ab92a040f39a4294b27a0cd5af':
    raise SystemExit('Pinned Symphony binary checksum mismatch')
print('Persistent source assets verified')
PY

if [[ -r "$platform_root/env.sh" ]]; then
  # Generated for this user's persistent installation.
  # shellcheck source=/dev/null
  . "$platform_root/env.sh"
fi

if ! command -v uv >/dev/null 2>&1; then
  printf '%s\n' 'uv is required; the current installation uses ~/.local/bin/uv.' >&2
  exit 2
fi
if [[ ! -x "$platform_root/.venv/bin/python" ]]; then uv venv --python 3.12 "$platform_root/.venv"; fi
uv pip sync --python "$platform_root/.venv/bin/python" --require-hashes "$platform_root/requirements.lock"
export PYTHONPATH="$platform_root/local:$platform_root/upstream/platform:$platform_root/upstream/temporal:$platform_root/upstream"
"$platform_root/.venv/bin/python" -m agent_platform.adapt_upstream
"$platform_root/.venv/bin/python" -m agent_platform.cli init
"$platform_root/.venv/bin/python" -m agent_platform.cli templates install
if (( trust_current )); then
  "$platform_root/.venv/bin/python" -m agent_platform.cli execution enable --trusted-current-container
fi
if (( start_services )); then "$platform_root/.venv/bin/python" -m agent_platform.cli services start; fi
"$platform_root/.venv/bin/python" -m agent_platform.cli doctor
