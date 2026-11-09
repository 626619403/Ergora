"""Versioned formal review uses the original six-stage evidence owners."""

import json
from pathlib import Path
import subprocess
import sys

import pytest


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal execution requires Linux / WSL2')


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
