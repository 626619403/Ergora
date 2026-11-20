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


@pytest.mark.parametrize('mode', ['native-auth', 'native-auth-rejected', 'selected-auth-rejected',
                                 'command-invalid-codex-config', 'command-nontable-codex-config'])
def test_backend_native_authentication_uses_the_original_stage_owners(tmp_path, mode):
    pytest.importorskip('temporalio')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    backend = 'command' if mode.startswith('command-') else 'codex'
    result = subprocess.run([sys.executable, '-B', str(fixture), str(tmp_path), 'repository-governance', backend, mode],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    if backend == 'command':
        assert summary['backend'] == 'command' and summary['candidate_bound'] and len(summary['stages']) == 6
    elif mode == 'native-auth':
        assert summary['native_auth'] and summary['candidate_bound'] and len(summary['stages']) == 6
    else:
        assert summary['rejected'] == mode and summary['state'] == 'FAILED'
        assert summary['backend_authentication_error_preserved'] and summary['original_job_id'].startswith('task-1-')


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


@pytest.mark.skipif(sys.platform != 'linux', reason='Original monitor requires Linux/WSL2')
@pytest.mark.parametrize('case', ['good', 'bad', 'review-reject', 'review-corrupt',
                                 'review-ordinary-missing', 'review-baseline-false', 'review-scope-fail'])
def test_fixed_cpu_oracle_observes_candidate_through_original_stage_owners(tmp_path, case):
    """Deterministic CLI/model doubles; actual registration, Git and CPU scripts."""
    pytest.importorskip('temporalio')
    pytest.importorskip('mcp')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, '-B', str(fixture), str(tmp_path), 'large-change', 'command',
        'composition-work-materials-fixed-' + case], capture_output=True, text=True, timeout=210)
    (tmp_path / 'fixture.stdout.json').write_text(result.stdout)
    (tmp_path / 'fixture.stderr.log').write_text(result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['original_owners']
    if case == 'bad':
        assert summary['fixed_rejected'] and summary['ordinary_passed']
    elif case.startswith('review-'):
        assert summary['review_rejected'] and summary['fixed_accepted']
    else:
        assert summary['candidate'] and summary['review_calls'] == 3
