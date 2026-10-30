#!/usr/bin/env bash
set -euo pipefail

mode=install
source_build=0
with_podman=0
for option in "$@"; do
  case "$option" in
    --install) mode=install ;;
    --check) mode=check ;;
    --dry-run) mode=dry-run ;;
    --symphony-source) source_build=1 ;;
    --with-podman) with_podman=1 ;;
    -h|--help)
      printf '%s\n' 'Usage: bash install-multi-agent-linux-deps.sh [--install|--check|--dry-run] [--symphony-source] [--with-podman]'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$option" >&2; exit 2 ;;
  esac
done

if [[ ! -r /etc/os-release ]]; then
  printf '%s\n' 'Cannot identify this Linux distribution.' >&2
  exit 2
fi
# shellcheck source=/dev/null
. /etc/os-release
if [[ "${ID:-}" != ubuntu || "${VERSION_ID:-}" != 24.04 ]]; then
  printf 'This package manifest targets Ubuntu 24.04; detected %s %s.\n' "${ID:-unknown}" "${VERSION_ID:-unknown}" >&2
  exit 2
fi

packages=(
  ca-certificates curl git openssh-client unzip zip tar xz-utils jq ripgrep tmux
  python3.12 python3.12-venv sqlite3 bubblewrap
  procps psmisc iproute2 lsof util-linux shellcheck
)
if (( with_podman )); then packages+=(podman uidmap fuse-overlayfs slirp4netns passt); fi
if (( source_build )); then
  packages+=(build-essential pkg-config libssl-dev libncurses-dev zlib1g-dev autoconf m4)
fi

missing=()
for package in "${packages[@]}"; do
  status=$(dpkg-query -W -f='${Status}' "$package" 2>/dev/null || true)
  if [[ "$status" != 'install ok installed' ]]; then missing+=("$package"); fi
done
if (( ${#missing[@]} == 0 )); then
  printf '%s\n' 'All selected Linux support packages are installed. Runtime isolation support is checked separately by agentflow doctor.'
  exit 0
fi
printf 'Missing packages:'
printf ' %s' "${missing[@]}"
printf '\n'
if [[ "$mode" == check ]]; then exit 1; fi
if [[ "$mode" == dry-run ]]; then
  printf 'Command: '
  printf '%q ' sudo apt-get install --no-install-recommends "${missing[@]}"
  printf '\n'
  exit 0
fi

elevate=()
if (( EUID != 0 )); then elevate=(sudo); fi
"${elevate[@]}" apt-get update
"${elevate[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing[@]}"
printf '%s\n' 'Linux packages installed. Run agentflow doctor after installing the user environment.'
