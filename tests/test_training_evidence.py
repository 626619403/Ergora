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
from test_training_submission import prepared, service


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
    text = (folder / 'notes.txt').read_bytes().decode('utf-8')
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


def test_round_index_retains_negative_unknown_and_offline_cli_read(experiments, tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    from ergora import training_rounds
    from ergora.cli import main

    state, definition, runtime, _, _ = experiments
    before = {p: p.read_bytes() for root in (runtime, Path(definition['execution']['config_directory']))
              for p in root.rglob('*') if p.is_file()}
    request = {'schema_version': 1, 'rounds': [{'experiment_id': 'alpha', 'change': 'Synthetic rejected candidate',
                'next_bottleneck': 'Unknown; no measured optimization claim'}]}
    source = tmp_path / 'round-request.json'
    source.write_text(json.dumps(request), encoding='utf-8')
    output = io.StringIO()
    first = tmp_path / 'first'
    with redirect_stdout(output):
        assert main(['--home', str(state.root), 'training', 'rounds-create', 'demo', '--definition', str(source),
                     '--directory', str(first)]) == 0
    identity = json.loads(output.getvalue())
    original = (first / 'rounds.json').read_bytes()
    request['rounds'][0].update(experiment_id='beta', change='Independent pending original experiment')
    second = training_rounds.create(state, 'demo', request, tmp_path / 'second',
                                    previous=first, previous_sha256=identity['sha256'])
    report = training_rounds.read(tmp_path / 'second', sha256=second['sha256'])['report']
    negative, pending = report['rounds']
    assert negative['native']['records']['experiment']['recorded_gate']['passed'] is False
    assert negative['native']['records']['experiment']['negative_result']['detail'] == 'Synthetic negative result'
    assert pending['native']['records']['experiment']['recorded_result_state'] is None
    assert all(item['native']['approval'] is None for item in report['rounds'])
    assert report['coverage']['promotion_approved'] is False and report['coverage']['execution_success'] is None
    assert pending['parent_sha256'] == negative['sha256']
    assert (first / 'rounds.json').read_bytes() == original
    assert all(path.read_bytes() == raw for path, raw in before.items())
    with pytest.raises(FileExistsError):
        training_rounds.create(state, 'demo', request, first)
    assert (first / 'rounds.json').read_bytes() == original

    def no_native_observation(*args, **kwargs):
        raise AssertionError('Offline index reading must not observe a project or service')

    monkeypatch.setattr(training, 'inspect', no_native_observation)
    monkeypatch.setattr(training, 'submission', no_native_observation)
    original_find = reference.importlib.util.find_spec
    monkeypatch.setattr(reference.importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original_find(name))
    output = io.StringIO()
    unused_home = tmp_path / 'unused-control-home'
    with redirect_stdout(output):
        assert main(['--home', str(unused_home), 'training', 'rounds-read', str(tmp_path / 'second'),
                     '--sha256', second['sha256']]) == 0
    assert json.loads(output.getvalue())['report'] == report and not unused_home.exists()


def test_round_extension_preserves_accepted_prefix_and_failed_result_after_baseline_drift(archive, tmp_path):
    pytest.importorskip('temporalio')
    from ergora import training_rounds

    state, _, runtime, prefix, write, _, _ = archive
    request = {'schema_version': 1, 'rounds': [{'experiment_id': 'alpha', 'change': 'Synthetic accepted evidence',
                'next_bottleneck': 'No actual training or performance assessment'}]}
    first = training_rounds.create(state, 'demo', request, tmp_path / 'first')
    original = training_rounds.read(tmp_path / 'first')['report']
    beta = json.loads((runtime / 'training/specs/beta.json').read_bytes())
    write(runtime / 'training/jobs/beta/result.json', {'binding': beta['binding'], 'job_id': 'local-perf-beta',
          'state': 'FAILED', 'detail': 'Synthetic runner failed; do not discard this round'})
    write(runtime / 'training/negative-results/beta.json', {'project': 'demo', 'experiment_id': 'beta',
          'binding': beta['binding'], 'state': 'FAILED', 'detail': 'Synthetic runner failed'})
    baseline = json.loads((prefix / 'baseline.json').read_bytes())
    write(prefix / 'baseline.json', {**baseline, 'config_sha256': 'f' * 64})
    request['rounds'][0].update(experiment_id='beta', change='Synthetic failed candidate')
    second = training_rounds.create(state, 'demo', request, tmp_path / 'second',
                                    previous=tmp_path / 'first', previous_sha256=first['sha256'])
    report = training_rounds.read(tmp_path / 'second')['report']
    assert report['rounds'][0] == original['rounds'][0]
    accepted, failed = report['rounds']
    assert accepted['native']['evidence']['archive']['artifact_content_status'] == 'not_read'
    assert accepted['native']['records']['experiment']['baseline_matches'] is True
    assert failed['native']['records']['experiment']['baseline_matches'] is False
    assert failed['native']['records']['experiment']['recorded_result_state'] == 'FAILED'
    assert report['initial_anchor']['base_config_sha256'] == baseline['config_sha256']
    assert report['previous_report']['sha256'] == first['sha256']
    with pytest.raises(ValueError, match='once'):
        training_rounds.create(state, 'demo', request, tmp_path / 'duplicate',
                               previous=tmp_path / 'second', previous_sha256=second['sha256'])
    raw = tmp_path / 'second/rounds.json'
    report['rounds'][1]['parent_sha256'] = '0' * 64
    raw.write_text(json.dumps(report), encoding='utf-8')
    with pytest.raises(ValueError, match='predecessor link'):
        training_rounds.read(raw.parent)
    with pytest.raises(ValueError, match='expected SHA256'):
        training_rounds.read(raw.parent, sha256=second['sha256'])


def test_round_index_keeps_lost_start_acknowledgement_without_query_or_approval(prepared, service, tmp_path, monkeypatch):
    from ergora import training_rounds

    state, _, runtime, _, _, digest = prepared
    select, record = service
    select('lost-ack')
    with pytest.raises(ValueError, match='UNAVAILABLE'):
        training.start(state, 'demo', 'alpha', state.project('demo')['revision'], digest)
    unknown = training.submission(state, 'demo', 'alpha')
    calls = record.read_bytes()
    before = {path: path.read_bytes() for path in runtime.rglob('*') if path.is_file()}

    def no_approval(*args, **kwargs):
        raise AssertionError('An unknown start is not an approved or submitted run')

    monkeypatch.setattr(training, 'approval', no_approval)
    created = training_rounds.create(state, 'demo', {'schema_version': 1, 'rounds': [{
        'experiment_id': 'alpha', 'change': 'Simulated lost service acknowledgement',
        'next_bottleneck': 'Reconcile the original start; do not start another experiment'}]}, tmp_path / 'index')
    saved = training_rounds.read(tmp_path / 'index', sha256=created['sha256'])['report']['rounds'][0]['native']
    assert saved['submission'] == unknown and saved['submission']['status'] == 'unknown'
    assert saved['submission']['run_id'] is None and saved['approval'] is None
    assert record.read_bytes() == calls and all(path.read_bytes() == raw for path, raw in before.items())
