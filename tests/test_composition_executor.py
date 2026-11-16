"""Versioned formal review uses the original six-stage evidence owners."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

from test_registrations import design_policy


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal execution requires Linux / WSL2')


@pytest.mark.parametrize('version', [1, 2])
def test_native_legacy_job_obeys_registered_design_policy_before_claim(tmp_path, version):
    pytest.importorskip('temporalio')
    (tmp_path / 'design-policy.json').write_text(json.dumps(design_policy()), encoding='utf-8')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    mode = 'design-policy-legacy-v' + str(version)
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command', mode],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['legacy_request_root']
    if version == 2:
        assert summary['rejected'] == mode and set(summary['starts'].values()) == {0}
        assert summary['registration']['design']['execution_supported'] is False
    else:
        assert summary['allowed'] == mode and summary['frozen_selection']


@pytest.mark.parametrize('problem', ['missing-control', 'repo-mismatch'])
@pytest.mark.parametrize('frozen', [False, True])
def test_native_legacy_control_failure_keeps_receipt_or_frozen_selection(tmp_path, problem, frozen):
    pytest.importorskip('temporalio')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    mode = 'legacy-control-' + ('frozen-' if frozen else '') + problem
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command', mode],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['state'] == ('SUCCEEDED' if frozen else 'FAILED')
    assert summary['poll_received_terminal'] and summary['frozen_selection'] == frozen


@pytest.mark.parametrize('template,mode', [
    ('repository-governance', 'composition'),
    ('large-change', 'composition'),
    ('repository-governance', 'composition-import-shadowing'),
    ('repository-governance', 'composition-replace-object'),
])
def test_published_composition_runs_a_restricted_leaf_through_all_six_stages(tmp_path, template, mode):
    pytest.importorskip('temporalio')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), template, 'command', mode],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['candidate_bound'] and summary['template_instructions_bound'] and len(summary['stages']) == 6


@pytest.mark.parametrize('mode,detail', [
    ('composition-missing-admission', 'complete published admission'),
    ('composition-other-admission', 'complete published admission'),
    ('composition-missing-publication', 'creation is incomplete'),
    ('composition-binding-drift', 'creation is incomplete'),
    ('composition-config-drift', 'configuration drift'),
    ('composition-policy-drift', 'current backend contract'),
    ('composition-multiple', 'explicit all-join'),
])
def test_invalid_composition_is_rejected_before_the_native_constructor(tmp_path, mode, detail):
    pytest.importorskip('temporalio')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command', mode],
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['before_native_side_effects'] and detail in summary['detail']


@pytest.mark.parametrize('mode,detail', [
    ('composition-binary', 'binary content'),
    ('composition-symlink', 'ordinary Git file'),
    ('composition-capacity', 'input byte limit'),
    ('composition-read-scope', 'leaf read scope'),
    ('composition-dependency-drift', 'artifact changed'),
    ('composition-evidence-capacity', 'File exceeds size limit'),
    ('composition-review-reject', 'reviewer requested changes'),
    ('composition-review-timeout', 'agent failed'),
    ('composition-review-cancel', 'agent failed'),
    ('composition-missing-invocation', 'invocation evidence'),
])
def test_incomplete_input_or_unsuccessful_review_never_publishes_a_pass(tmp_path, mode, detail):
    pytest.importorskip('temporalio')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command', mode],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['rejected'] == mode and detail in summary['detail']


def test_recovery_reuses_the_original_native_review_call_and_artifacts(tmp_path):
    pytest.importorskip('temporalio')
    fixture = Path(__file__).parent / 'fixtures/reference_acceptance.py'
    result = subprocess.run([sys.executable, str(fixture), str(tmp_path), 'repository-governance', 'command',
                             'composition-review-recovery'], capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    if summary.get('skip'):
        pytest.skip(summary['skip'])
    assert summary['candidate_bound'] and len(summary['stages']) == 6
