import os
import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.skipif(os.name == "nt", reason="Optional SDK installer requires Linux/bash; native app installation is separate")
@pytest.mark.parametrize("agent,repository,commit", [
    ("forgekernel", "https://github.com/OpenBMB/ForgeKernel.git", "5030503d3ff71851aa34c14b9caf13ebfa9d9a78"),
    ("mini-swe-agent", "https://github.com/SWE-agent/mini-swe-agent.git", "04d809ceab9df28f9adaed044884180159172930"),
])
def test_optional_installer_consumes_pinned_recipe_without_network(tmp_path, agent, repository, commit):
    commands = tmp_path / "bin"
    commands.mkdir()
    git = commands / "git"
    git.write_text(f"#!{sys.executable}\n" + '''
import json, os, pathlib, sys
args = sys.argv[1:]
with open(os.environ['ERGORA_TEST_INSTALL_LOG'], 'a') as log:
    log.write(json.dumps(args) + '\\n')
if args[0] == 'init':
    pathlib.Path(args[1]).mkdir()
if args[-2:] == ['rev-parse', 'HEAD']:
    print(os.environ['ERGORA_TEST_INSTALL_COMMIT'])
''')
    git.chmod(0o755)
    python = commands / "install-python"
    python.write_text(f"#!{sys.executable}\n" + '''
import pathlib, subprocess, sys
if sys.argv[1:3] == ['-m', 'venv']:
    command = pathlib.Path(sys.argv[3]) / 'bin/python'
    command.parent.mkdir(parents=True)
    command.write_text('#!/bin/sh\\nexit 0\\n')
    command.chmod(0o755)
else:
    raise SystemExit(subprocess.call([sys.executable, *sys.argv[1:]]))
''')
    python.chmod(0o755)
    log = tmp_path / "git.jsonl"
    checkout = tmp_path / "tools" / agent
    installer = Path(__file__).resolve().parents[1] / "scripts/install-agent.sh"
    env = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ['PATH'],
               ERGORA_PYTHON=str(python), ERGORA_TOOLS_ROOT=str(checkout.parent),
               ERGORA_TEST_INSTALL_LOG=str(log), ERGORA_TEST_INSTALL_COMMIT=commit)
    result = subprocess.run(["bash", str(installer), agent], env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert ["-C", str(checkout), "remote", "add", "origin", repository] in calls
    assert ["-C", str(checkout), "fetch", "--depth", "1", "origin", commit] in calls
    assert commit in result.stdout and (checkout / ".venv/bin/python").is_file()
    rejected = subprocess.run(["bash", str(installer), "codex"], env=env, capture_output=True, text=True, timeout=10)
    assert rejected.returncode == 2 and "Unknown optional agent" in rejected.stderr


@pytest.mark.skipif(os.name == "nt", reason="Bash installer; native PowerShell installer has a Windows CI check")
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
