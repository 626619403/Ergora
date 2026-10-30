import os
from pathlib import Path
import subprocess
import sys


def test_installer_upgrades_symlinked_directories_and_preserves_foreign_command(tmp_path):
    """Run the real shell entry point; only venv/package installation is substituted."""
    real_install = tmp_path / "physical-install"
    real_bin = tmp_path / "physical-bin"
    real_install.mkdir()
    real_bin.mkdir()
    install_link, bin_link = tmp_path / "install", tmp_path / "bin"
    install_link.symlink_to(real_install, target_is_directory=True)
    bin_link.symlink_to(real_bin, target_is_directory=True)
    python = tmp_path / "package-installer"
    python.write_text(f"#!{sys.executable}\n" + '''
from pathlib import Path
import sys
if sys.argv[1:3] == ["-m", "venv"]:
    directory = Path(sys.argv[3]) / "bin"
    directory.mkdir(parents=True, exist_ok=True)
    for name in ["python", "ergora"]:
        command = directory / name
        command.write_text("#!/bin/sh\\nexit 0\\n")
        command.chmod(0o755)
''')
    python.chmod(0o755)
    env = dict(os.environ, ERGORA_PYTHON=str(python), ERGORA_INSTALL_ROOT=str(install_link),
               ERGORA_BIN_DIR=str(bin_link))
    installer = Path(__file__).resolve().parents[1] / "scripts/install.sh"
    for _ in range(2):
        result = subprocess.run(["bash", str(installer)], env=env, capture_output=True, text=True,
                                timeout=10)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (bin_link / "ergora").resolve() == real_install / "venv/bin/ergora"

    entry = bin_link / "ergora"
    entry.unlink()
    entry.write_text("another application's command\n")
    result = subprocess.run(["bash", str(installer)], env=env, capture_output=True, text=True,
                            timeout=10)
    assert result.returncode == 1
    assert "belongs to another installation" in result.stderr
    assert entry.read_text() == "another application's command\n"
