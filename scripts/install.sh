#!/usr/bin/env bash
# Install the local control plane. External agent CLIs and services stay optional.
set -euo pipefail

ergora_source_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ergora_install_root="${ERGORA_INSTALL_ROOT:-$HOME/.local/share/ergora-app}"
ergora_bin_dir="${ERGORA_BIN_DIR:-$HOME/.local/bin}"
ergora_python="${ERGORA_PYTHON:-python3}"
ergora_extras="web"

while (($#)); do
  case "$1" in
    --with-gepa) ergora_extras+=",gepa" ;;
    --with-temporal) ergora_extras+=",temporal" ;;
    --help|-h)
      cat <<'EOF'
Usage: bash scripts/install.sh [--with-gepa] [--with-temporal]

Installs the CLI and local console into ~/.local/share/ergora-app/venv.
Creates ~/.local/bin/ergora. Requires Python 3.11+ with venv and pip.
Optional extras install SDKs; they do not start services or invoke models.

Overrides: ERGORA_INSTALL_ROOT, ERGORA_BIN_DIR, ERGORA_PYTHON.
Persistent project state uses ERGORA_HOME, independently of this install path.
EOF
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

"$ergora_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Python 3.11+ is required")'
mkdir -p -- "$ergora_install_root" "$ergora_bin_dir"
ergora_install_root="$(CDPATH= cd -- "$ergora_install_root" && pwd -P)"
ergora_bin_dir="$(CDPATH= cd -- "$ergora_bin_dir" && pwd -P)"
ergora_target="$ergora_install_root/venv/bin/ergora"
if [[ -e "$ergora_bin_dir/ergora" || -L "$ergora_bin_dir/ergora" ]]; then
  if [[ "$(readlink -f -- "$ergora_bin_dir/ergora")" != "$ergora_target" ]]; then
    echo "Existing $ergora_bin_dir/ergora belongs to another installation. Choose ERGORA_BIN_DIR." >&2
    exit 1
  fi
fi
"$ergora_python" -m venv "$ergora_install_root/venv"
"$ergora_install_root/venv/bin/python" -m pip install "$ergora_source_root[$ergora_extras]"
ln -sfn -- "$ergora_target" "$ergora_bin_dir/ergora"
"$ergora_target" reference verify
printf '\nInstalled: %s\nStart console: %s serve\n' "$ergora_bin_dir/ergora" "$ergora_bin_dir/ergora"
printf 'Add to your shell PATH if needed: export PATH="%s:$PATH"\n' "$ergora_bin_dir"
