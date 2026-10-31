import importlib.util
import json
import sys
from pathlib import Path
import subprocess

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Formal reference execution requires Linux / WSL2")


@pytest.mark.parametrize("kind", ["repository-governance", "large-change"])
@pytest.mark.parametrize("backend", ["command", "codex"])
def test_existing_six_stage_contract_consumes_selectable_agent_evidence(tmp_path, kind, backend):
    if importlib.util.find_spec("temporalio") is None:
        pytest.skip("Reference activity validation requires the optional Temporal SDK")
    fixture = Path(__file__).parent / "fixtures/reference_acceptance.py"
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), kind, backend],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get("skip"):
        pytest.skip(summary["skip"])
    assert summary["candidate_bound"] is True
    assert len(summary["stages"]) == 6


def test_cancellation_reaps_same_group_children_ignoring_sigterm(tmp_path):
    if importlib.util.find_spec("temporalio") is None:
        pytest.skip("Reference activity validation requires the optional Temporal SDK")
    fixture = Path(__file__).parent / "fixtures/reference_acceptance.py"
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), "repository-governance", "command", "cancel-ignore-term"],
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get("skip"):
        pytest.skip(summary["skip"])
    assert summary["cancelled"] and summary["no_late_write"]


@pytest.mark.parametrize("boundary", ["creation", "cleanup"])
def test_first_sigterm_cannot_interrupt_supervised_cleanup(tmp_path, boundary):
    fixture = Path(__file__).parent / "fixtures/signal_windows.py"
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), boundary],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "cancelled"
    assert summary["late_write"] is False
