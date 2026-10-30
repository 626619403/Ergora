#!/usr/bin/env bash
# Bootstrap a clean Ubuntu environment from the public workflow package.
set -euo pipefail

bundle_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
platform_root="${AGENTFLOW_ROOT:-$HOME/multi-agent-platform}"
export PATH="$HOME/.local/bin:$PATH"
if [[ -r "$platform_root/env.sh" ]]; then
  # shellcheck source=/dev/null
  . "$platform_root/env.sh"
fi
mode=install
runtime_cache=""
repair_options=()
while (( $# )); do
  case "$1" in
    --check) mode=check ;;
    --start) repair_options+=(--start) ;;
    --trust-current-container) repair_options+=(--trust-current-container) ;;
    --runtime-cache)
      if (( $# < 2 )); then printf '%s\n' '--runtime-cache requires an extracted cache directory' >&2; exit 2; fi
      runtime_cache=$2; shift ;;
    -h|--help)
      printf '%s\n' 'Usage: bash install-from-report.sh [--check] [--runtime-cache DIR] [--start] [--trust-current-container]'
      printf '%s\n' 'Run beside the platform/ directory in the extracted report ZIP. Existing differing source files are preserved and installation stops.'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done

if [[ "$mode" == install ]]; then
  bash "$bundle_root/platform/bootstrap/install-multi-agent-linux-deps.sh" --install
fi
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'Python is not installed yet. Run without --check to install the Ubuntu prerequisites.' >&2
  exit 2
fi
python3 "$bundle_root/platform/bootstrap/report/install_from_bundle.py" \
  --bundle "$bundle_root" --destination "$platform_root" \
  --mode "$mode" --runtime-cache "$runtime_cache"
if [[ "$mode" == check ]]; then exit 0; fi
export PATH="$platform_root/toolchains/node/bin:$platform_root/bin:$PATH"
bash "$platform_root/bootstrap/install-multi-agent-platform.sh" "${repair_options[@]}"
