import json
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import reference


def test_public_reference_identity():
    assert reference.verify()["files"] == 283


def test_template_copy_preserves_files_and_existing_destination(tmp_path):
    for kind in reference.TEMPLATES:
        destination = tmp_path / kind
        reference.copy_template(kind, destination)
        source = reference.ROOT / "platform/templates" / kind
        assert (destination / "agent-contract.json").is_file()
        for file in source.rglob("*"):
            if file.is_file():
                assert file.read_bytes() == (destination / file.relative_to(source)).read_bytes()
        with pytest.raises(ValueError, match="preserve"):
            reference.copy_template(kind, destination)


def test_installed_compiler_runs_outside_repository(tmp_path):
    shadow = tmp_path / "dev_platform"
    shadow.mkdir()
    (shadow / "__init__.py").write_text("")
    (shadow / "portable.py").write_text("raise RuntimeError('project must not replace the compiler')")
    example = reference.ROOT / "platform/upstream/platform/portable/examples/repository-governance"
    package = reference.ROOT / "platform/upstream/platform/portable/packages/repository-governance/manifest.json"
    result = subprocess.run(
        [sys.executable, "-m", "ergora", "workflow", "compile", "--task", str(example / "task.json"),
         "--package", str(package), "--policy", str(example / "policy.json"),
         "--binding", str(example / "binding.json"), "--out", str(tmp_path / "compiled.json")],
        cwd=tmp_path, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    compiled = json.loads((tmp_path / "compiled.json").read_text())
    assert compiled["spec"]["request"]["task_type"] == "repository-governance"


def test_workflow_help_is_forwarded(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "ergora", "workflow", "--help"],
        cwd=tmp_path, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "compile" in result.stdout
