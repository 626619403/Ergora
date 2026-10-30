#!/usr/bin/env bash
# Optional native agents stay in their own environments, outside the application.
set -euo pipefail

ergora_agent="${1:---help}"
ergora_tools_root="${ERGORA_TOOLS_ROOT:-$HOME/.local/share/ergora-tools}"
ergora_python="${ERGORA_PYTHON:-python3}"
case "$ergora_agent" in
  forgekernel)
    ergora_repository="https://github.com/OpenBMB/ForgeKernel.git"
    ergora_commit="5030503d3ff71851aa34c14b9caf13ebfa9d9a78" ;;
  mini-swe-agent)
    ergora_repository="https://github.com/SWE-agent/mini-swe-agent.git"
    ergora_commit="04d809ceab9df28f9adaed044884180159172930" ;;
  --help|-h)
    echo 'Usage: bash scripts/install-agent.sh {forgekernel|mini-swe-agent}'
    echo 'Installs a pinned source and isolated venv under ~/.local/share/ergora-tools/.'
    echo 'Overrides: ERGORA_TOOLS_ROOT, ERGORA_PYTHON. Does not log in or run models/GPU jobs.'
    exit 0 ;;
  *) echo "Unknown optional agent: $ergora_agent" >&2; exit 2 ;;
esac
"$ergora_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Python 3.11+ is required")'
mkdir -p -- "$ergora_tools_root"
ergora_checkout="$ergora_tools_root/$ergora_agent"
if [[ ! -d "$ergora_checkout" ]]; then
  git init "$ergora_checkout"
  git -C "$ergora_checkout" remote add origin "$ergora_repository"
  git -C "$ergora_checkout" fetch --depth 1 origin "$ergora_commit"
  git -C "$ergora_checkout" checkout --detach FETCH_HEAD
fi
if [[ "$(git -C "$ergora_checkout" rev-parse HEAD)" != "$ergora_commit" ]]; then
  echo "Existing checkout has another commit; preserve it and choose ERGORA_TOOLS_ROOT." >&2
  exit 1
fi
git -C "$ergora_checkout" diff --exit-code HEAD -- src pyproject.toml
"$ergora_python" -m venv "$ergora_checkout/.venv"
"$ergora_checkout/.venv/bin/python" -m pip install -e "$ergora_checkout"
printf '\nCheckout: %s\nPython: %s/.venv/bin/python\nCommit: %s\n' "$ergora_checkout" "$ergora_checkout" "$ergora_commit"
