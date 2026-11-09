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
    assert summary["template_instructions_bound"] is True


@pytest.mark.parametrize('mode,detail', [
    ('verify-scope-mismatch', 'Immutable file already exists'),
    ('verify-scope-header', 'Immutable file already exists'),
    ('verify-baseline-drift', 'Trusted check commands changed'),
    ('verify-command-failure', 'Final candidate check failed'),
    ('verify-scope-recovery', 'Candidate scope gate failed'),
])
def test_trusted_verification_preserves_input_and_rejects_unbound_evidence(tmp_path, mode, detail):
    pytest.importorskip('temporalio')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command', mode],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['rejected'] == mode and detail in summary['detail']


@pytest.mark.parametrize("mode,detail", [("instructions-missing", "compiled.json"),
                                        ("instructions-tampered", "Compiled digest mismatch"),
                                        ("instructions-cross-task", "Compiled task differs")])
def test_template_instructions_fail_closed_before_agent_invocation(tmp_path, mode, detail):
    if importlib.util.find_spec("temporalio") is None:
        pytest.skip("Reference activity validation requires the optional Temporal SDK")
    fixture = Path(__file__).parent / "fixtures/reference_acceptance.py"
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), "repository-governance", "command", mode],
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get("skip"):
        pytest.skip(summary["skip"])
    assert summary["rejected"] == mode and detail in summary["detail"]


def test_task_keeps_template_instructions_when_source_package_is_unavailable(tmp_path):
    if importlib.util.find_spec("temporalio") is None:
        pytest.skip("Reference activity validation requires the optional Temporal SDK")
    fixture = Path(__file__).parent / "fixtures/reference_acceptance.py"
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), "large-change", "command", "instructions-frozen-source"],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get("skip"):
        pytest.skip(summary["skip"])
    assert summary["candidate_bound"] and len(summary["stages"]) == 6 and summary["template_instructions_bound"]


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


def test_existing_task_selection_without_effective_view_remains_usable(tmp_path):
    if importlib.util.find_spec("temporalio") is None:
        pytest.skip("Reference activity validation requires the optional Temporal SDK")
    fixture = Path(__file__).parent / "fixtures/reference_acceptance.py"
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), "repository-governance", "command", "legacy-snapshot"],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get("skip"):
        pytest.skip(summary["skip"])
    assert summary["candidate_bound"] is True and len(summary["stages"]) == 6


@pytest.mark.parametrize("kind", ["repository-governance", "large-change"])
@pytest.mark.parametrize("mode", ["unified-registration", "imported-registration"])
def test_unified_registration_drives_six_stages(tmp_path, kind, mode):
    if importlib.util.find_spec("temporalio") is None:
        pytest.skip("Reference activity validation requires the optional Temporal SDK")
    fixture = Path(__file__).parent / "fixtures/reference_acceptance.py"
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), kind, "command", mode],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get("skip"):
        pytest.skip(summary["skip"])
    assert summary["candidate_bound"] and len(summary["stages"]) == 6


@pytest.mark.parametrize("mode,detail", [("unified-pending", "pending"), ("unified-drift", "drift"),
                                         ("unified-wrong-state", "directory mismatch")])
def test_new_task_refuses_incomplete_or_mismatched_registration(tmp_path, mode, detail):
    if importlib.util.find_spec("temporalio") is None:
        pytest.skip("Reference activity validation requires the optional Temporal SDK")
    fixture = Path(__file__).parent / "fixtures/reference_acceptance.py"
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), "repository-governance", "command", mode],
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get("skip"):
        pytest.skip(summary["skip"])
    assert summary["rejected"] == mode and detail in summary["detail"]


@pytest.mark.parametrize("boundary", ["creation", "cleanup"])
def test_first_sigterm_cannot_interrupt_supervised_cleanup(tmp_path, boundary):
    fixture = Path(__file__).parent / "fixtures/signal_windows.py"
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), boundary],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "cancelled"
    assert summary["late_write"] is False
