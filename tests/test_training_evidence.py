"""Saved training evidence, selected content and local tickets are distinct facts."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import reference, training
from test_training import experiments, registration
from test_training_runtime import installation


@pytest.fixture
def archive(experiments):
    state, definition, runtime, prefix, write = experiments
    upstream = Path(definition['execution']['installation']) / 'upstream'
    process = subprocess.run([sys.executable, '-P', str(Path(__file__).parent / 'fixtures/training_evidence_archive.py')],
        input=json.dumps({'runtime': str(runtime), 'prefix': str(prefix)}), text=True, encoding='utf-8', capture_output=True,
        env={**os.environ, 'PYTHONPATH': str(upstream)}, timeout=30)
    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)['archive']
    return state, definition, runtime, prefix, write, Path(report['archive_path']), report


def test_original_archive_and_unicode_window_preserve_records_without_sdk_or_services(archive, monkeypatch):
    state, definition, runtime, prefix, write, folder, report = archive
    before = {path: path.read_bytes() for root in (runtime, Path(definition['execution']['config_directory']))
              for path in root.rglob('*') if path.is_file()}
    original = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
    result = training.evidence(state, 'demo', 'alpha')
    assert result['archive']['evidence_sha256'] == report['evidence_sha256']
    assert result['archive']['evidence'] == json.loads((folder / 'evidence.json').read_bytes())
    assert result['runtime_status'] == 'not_queried' and result['approval_status'] == 'not_evaluated'
    assert result['execution_success'] is result['integration_verified'] is None
    assert result['archive']['artifact_content_status'] == 'not_read' and result['integration_ticket'] is None
    window = training.evidence(state, 'demo', 'alpha', artifact='notes.txt', evidence_sha256=report['evidence_sha256'], offset=2, limit=4)['artifact']
    text = (folder / 'notes.txt').read_text(encoding='utf-8')
    assert window['text'] == text[2:6] and window['next_offset'] == 6 and window['characters'] == len(text)
    assert all(path.read_bytes() == raw for path, raw in before.items())
    assert not (runtime / 'ergora').exists()
    baseline = json.loads((prefix / 'baseline.json').read_bytes())
    write(prefix / 'baseline.json', {**baseline, 'baseline_id': 'new-baseline'})
    assert training.evidence(state, 'demo', 'alpha')['baseline_matches'] is False


@pytest.mark.parametrize('relative,error', [
    ('evidence.json', 'content address'), ('gate-result.json', 'Archived gate differs'),
    ('_archive_meta/manifest.json', 'Archived manifest bytes'), ('_archive_meta/baseline.json', 'Archived baseline bytes'),
    ('_archive_meta/compare_runs.py', 'Archived comparator differs'), ('notes.txt', 'Artifact bytes differ'),
])
def test_changed_original_content_is_not_returned_as_verified(archive, relative, error):
    state, _, _, _, _, folder, report = archive
    path = folder / relative
    if relative == 'gate-result.json':
        gate = json.loads(path.read_bytes())
        path.write_text(json.dumps({**gate, 'status': 'CHANGED'}), encoding='utf-8')
    else:
        path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(ValueError, match=error):
        training.evidence(state, 'demo', 'alpha', artifact='notes.txt', evidence_sha256=report['evidence_sha256'])


def test_archive_location_symlink_and_foreign_ticket_are_not_accepted(archive):
    state, _, runtime, _, write, folder, report = archive
    gate_path = runtime / 'training/jobs/alpha/gate-report.json'
    gate = json.loads(gate_path.read_bytes())
    gate['archive_report']['archive_path'] = str(runtime / 'training/projects/another/perf')
    gate_sha = write(gate_path, gate)
    result_path = gate_path.with_name('result.json')
    result = json.loads(result_path.read_bytes())
    result['gate']['report_sha256'] = gate_sha
    write(result_path, result)
    with pytest.raises(ValueError, match='Archived gate differs'):
        training.evidence(state, 'demo', 'alpha')
    gate['archive_report'] = report
    result['gate']['report_sha256'] = write(gate_path, gate)
    write(result_path, result)
    ticket = {'schema_version': 1, 'kind': 'local-integration-revalidation', 'project': 'demo',
              'binding': gate['binding'], 'evidence_sha256': report['evidence_sha256'],
              'approval_receipt_id': 'owner-synthetic', 'automatic_merge': False}
    ticket_path = runtime / ('training/integration-tickets/alpha-' + report['evidence_sha256'][:16] + '.json')
    write(ticket_path, ticket)
    observed = training.evidence(state, 'demo', 'alpha')['integration_ticket']
    assert observed['record'] == ticket and observed['approval_currently_valid'] is None
    write(ticket_path, {**ticket, 'project': 'another'})
    with pytest.raises(ValueError, match='Integration ticket differs'):
        training.evidence(state, 'demo', 'alpha')
    write(ticket_path, ticket)
    notes = folder / 'notes.txt'
    notes.rename(folder / 'original-notes.txt')
    try:
        notes.symlink_to(folder / 'original-notes.txt')
    except OSError:
        pytest.skip('This platform requires unavailable permission to create symlinks')
    with pytest.raises(ValueError, match='Symlinks'):
        training.evidence(state, 'demo', 'alpha')


def test_selected_text_requires_exact_index_digest_and_capacity(archive):
    state, _, _, _, _, folder, report = archive
    for options, error in [({'artifact': 'notes.txt', 'evidence_sha256': 'f' * 64}, 'exact observed evidence'),
                           ({'artifact': '../baseline.json'}, 'absent from the original'),
                           ({'artifact': 'trace.bin'}, 'contains NUL'),
                           ({'artifact': 'notes.txt', 'offset': 1_000}, 'offset exceeds')]:
        options = {'evidence_sha256': report['evidence_sha256'], **options}
        with pytest.raises(ValueError, match=error):
            training.evidence(state, 'demo', 'alpha', **options)
    notes = folder / 'notes.txt'
    with notes.open('wb') as stream:
        stream.truncate(16_777_217)
    with pytest.raises(ValueError, match='size limit'):
        training.evidence(state, 'demo', 'alpha', artifact='notes.txt', evidence_sha256=report['evidence_sha256'])


def test_no_archive_and_cli_http_share_the_observation(experiments):
    state = experiments[0]
    assert training.evidence(state, 'demo', 'alpha')['archive_status'] == 'no_accepted_archive'
    assert training.evidence(state, 'demo', 'beta')['recorded_gate_report'] is None
    from ergora.cli import main
    output = io.StringIO()
    with redirect_stdout(output):
        assert main(['--home', str(state.root), 'training', 'evidence', 'demo', 'alpha']) == 0
    assert json.loads(output.getvalue()) == training.evidence(state, 'demo', 'alpha')
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.web import create_app
    headers = {'Origin': 'http://127.0.0.1:8977', 'X-Ergora-Request': '1'}
    with TestClient(create_app(state.root), base_url=headers['Origin'], headers=headers) as client:
        response = client.get('/api/projects/demo/training/alpha/evidence')
        assert response.status_code == 200 and response.json() == json.loads(output.getvalue())
        assert client.get('/api/projects/demo/training/alpha/evidence', params={'artifact': 'notes.txt'}).status_code == 400
