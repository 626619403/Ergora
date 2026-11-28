"""Saved training evidence, selected content and local tickets are distinct facts."""

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from ergora._paths import IMPORT_ROOT
import importlib
import ergora.native.registration as native_registration
import ergora.native.resources as native_resources
import ergora.training.application as training
from test_training import experiments, registration
from test_training_runtime import installation
from test_training_submission import prepared, service
from test_training_runner import configuration_source
from test_training_search import (search_request, search_input, search_execution,
                                  _prepare_cpu_screens, _execute_search)


@pytest.mark.parametrize('case, outcome', [('bound', 'bound_run_observed'), ('foreign', 'foreign_run'),
    ('multiple', 'multiple_manifest_matches'), ('other_run', 'selected_run_mismatch'), ('deleted', 'run_inactive')])
def test_training_tracking_observation_reads_effects_only_for_the_original_run(monkeypatch, case, outcome):
    from ergora.training.runtime import tracking

    run_id, other = 'a' * 32, 'b' * 32
    binding = {'manifest_sha': '1' * 64, 'experiment_id': 'alpha', 'baseline_sha': '2' * 40, 'candidate_sha': '3' * 40}
    job_id = 'local-perf-alpha'
    tags = {**binding, 'runner_job_id': 'foreign' if case == 'foreign' else job_id,
            'purpose': 'paired-comparison', 'trust_model': 'trusted-current-container'}
    ids = [run_id, other] if case == 'multiple' else [other if case == 'other_run' else run_id]
    responses = {'experiments/get-by-name': {'experiment': {'name': 'training-demo', 'experiment_id': '7'}},
        'runs/search': {'runs': [{'info': {'run_id': ident}} for ident in ids]},
        'runs/get': {'run': {'info': {'run_id': run_id, 'experiment_id': '7', 'status': 'FINISHED',
            'lifecycle_stage': 'deleted' if case == 'deleted' else 'active',
            'artifact_uri': f'mlflow-artifacts:/7/{run_id}/artifacts'},
            'data': {'tags': [{'key': key, 'value': value} for key, value in tags.items()]}}},
        'metrics/get-history': {'metrics': [
            {'key': 'gate_passed', 'step': 0, 'timestamp': 3, 'value': 1, 'dataset_name': 'other'},
            {'key': 'gate_passed', 'step': 0, 'timestamp': 2, 'value': 1},
            {'key': 'gate_passed', 'step': 0, 'timestamp': 1, 'value': 1}]}}

    def read_document(endpoint, *, query=None, search=None):
        if endpoint == 'runs/search':
            assert search == {'experiment_ids': ['7'], 'max_results': 2, 'run_view_type': 'ALL',
                              'filter': f"tags.manifest_sha = '{binding['manifest_sha']}'"}
        if endpoint in ('runs/get', 'metrics/get-history'):
            assert query['run_id'] == run_id
        assert case == 'bound' or endpoint != 'metrics/get-history'
        return responses[endpoint]

    def read_artifact(path, limit):
        assert case == 'bound' and limit == 16 * 1_048_576
        assert path == f'/api/2.0/mlflow-artifacts/artifacts/7/{run_id}/artifacts/immutable-evidence/my%20score'
        return b'original bytes'

    monkeypatch.setattr(tracking, '_document', read_document)
    monkeypatch.setattr(tracking, '_read', read_artifact)
    sha = hashlib.sha256(b'original bytes').hexdigest()
    result = tracking.observe('demo', binding, job_id, run_id, 'gate_passed', 1,
                              {'path': 'my score', 'sha256': sha})
    assert result['status'] == outcome
    if case != 'bound':
        assert result['metric'] is result['artifact'] is None
    else:
        metric, artifact = result['metric'], result['artifact']
        assert metric['row_count'] == 3 and metric['matching_row_count'] == 2
        assert [row['timestamp'] for row in metric['rows']] == [1, 2, 3]
        assert artifact['status'] == 'matching_bytes' and artifact['observed_sha256'] == sha


def test_training_tracking_observation_refuses_partial_metric_history(monkeypatch):
    from ergora.training.runtime import tracking

    def paged_history(endpoint, *, query):
        assert endpoint == 'metrics/get-history' and query['max_results'] == 257
        return {'next_page_token': 'more'}

    monkeypatch.setattr(tracking, '_document', paged_history)
    with pytest.raises(ValueError, match='capacity_exceeded: original MLflow metric history'):
        tracking._metric_history('a' * 32, 'gate_passed', 1)


def test_training_tracking_observation_refuses_duplicate_run_identity_before_effects(monkeypatch):
    from ergora.training.runtime import tracking

    run_id, other = 'a' * 32, 'b' * 32
    binding = {'manifest_sha': '1' * 64, 'experiment_id': 'alpha', 'baseline_sha': '2' * 40, 'candidate_sha': '3' * 40}
    info = {'run_id': run_id, 'experiment_id': '7', 'status': 'RUNNING', 'lifecycle_stage': 'active',
            'artifact_uri': f'mlflow-artifacts:/7/{run_id}/artifacts'}
    tags = {**binding, 'runner_job_id': 'local-perf-alpha', 'purpose': 'paired-comparison',
            'trust_model': 'trusted-current-container'}
    run = {'run': {'info': info, 'data': {'tags': [{'key': key, 'value': value} for key, value in tags.items()]}}}
    duplicate = json.dumps(run).replace(f'"run_id": "{run_id}"', f'"run_id": "{other}", "run_id": "{run_id}"', 1)
    itinerary = iter((
        ('experiments/get-by-name', json.dumps({'experiment': {'name': 'training-demo', 'experiment_id': '7'}})),
        ('runs/search', json.dumps({'runs': [{'info': info}]})),
        ('runs/get', duplicate),
    ))

    def read_response(path, limit, *, query=None, search=None):
        endpoint, raw = next(itinerary)
        assert path == '/api/2.0/mlflow/' + endpoint
        return raw.encode()

    monkeypatch.setattr(tracking, '_read', read_response)
    with pytest.raises(ValueError, match='Duplicate execution record key: run_id'):
        tracking.observe('demo', binding, 'local-perf-alpha', run_id, 'gate_passed', 1,
                         {'path': 'notes.txt', 'sha256': '4' * 64})
    assert next(itinerary, None) is None


@pytest.fixture
def saved_source_subject(tmp_path, request):
    """Declaration-only source data; no archived implementation or executable fixture."""
    import ergora.training.execution_protocol as protocol

    member, count = getattr(request, 'param', ('saved/protocol.py', 30))
    names = (list(protocol.GATE_SOURCES) if count == 'current' else
             [member, 'data/reference-manifest.json', *(f'saved/member_{index}.py' for index in range(count - 2))])
    raw = (f'PROTOCOL = {protocol.PROTOCOL!r}\nGATE_SOURCES = {tuple(names)!r}\n').encode()
    sources = {name: hashlib.sha256(('saved source data: ' + name).encode()).hexdigest() for name in names}
    sources[member] = hashlib.sha256(raw).hexdigest()
    descriptor = json.dumps({'protocol_id': native_resources.TRAINING_PROTOCOL,
        'reference_manifest_sha256': sources['data/reference-manifest.json']}).encode()
    installation = tmp_path / 'absent-original-installation'
    capability = {'protocol': protocol.PROTOCOL, 'admission_protocol': native_resources.TRAINING_PROTOCOL,
        'descriptor_sha256': hashlib.sha256(descriptor).hexdigest(), 'installation': str(installation),
        'native_python': str(installation / '.venv/bin/python'), 'cycle_ready_sha256': '4' * 64, 'gate_sources': sources}
    manifest = {'schema_version': 1, 'kind': 'training-execution-source-manifest',
        'capability_sha256': protocol.CycleAdmission._sha(capability), 'gate_sources': deepcopy(sources),
        'protocol_source_ref': {'path': 'baseline-reference-protocol-source.py.txt',
            'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)},
        'native_descriptor_ref': {'path': 'baseline-reference-native-descriptor.json',
            'sha256': hashlib.sha256(descriptor).hexdigest(), 'bytes': len(descriptor)}}
    return capability, manifest, raw, descriptor, member


@pytest.mark.parametrize('saved_source_subject', [
    ('training_execution_protocol.py', 30), ('training/execution_protocol.py', 'current'), ('saved/protocol.py', 30)], indirect=True)
def test_saved_source_association_uses_the_exact_subject_and_supplied_raw(saved_source_subject, monkeypatch):
    import ergora.training.execution_protocol as protocol

    capability, manifest, raw, descriptor, _ = saved_source_subject
    before = deepcopy((capability, manifest))
    monkeypatch.setattr(protocol, 'read_raw', lambda *args: pytest.fail('Saved association cannot search current or archived files'))
    monkeypatch.setattr(protocol.native_resources, 'validate_installation', lambda *args, **kwargs:
        pytest.fail('Saved association cannot require a current installation'))
    observed = protocol.observe_source_manifest(capability, manifest, raw, descriptor)
    assert observed == {'state': 'verified', 'capability_sha256': protocol.CycleAdmission._sha(capability),
        'declared_gate_sources_sha256': protocol.CycleAdmission._sha(capability['gate_sources']), 'reasons': []}
    assert (capability, manifest) == before
    if set(capability['gate_sources']) != set(protocol.GATE_SOURCES):
        with pytest.raises(ValueError, match='Current execution source coverage'):
            protocol._current_capability(capability)
    else:
        # Complete current names still cannot turn synthetic saved bytes into current effects.
        monkeypatch.setattr(protocol, 'read_raw', lambda *args: b'actual different current bytes')
        with pytest.raises(ValueError, match='execution gate source changed'):
            protocol.validate_sources(capability)


@pytest.mark.parametrize('missing', ['subject', 'manifest', 'protocol', 'descriptor', 'protocol_ref', 'descriptor_ref', 'subject_ref'])
def test_saved_source_missing_association_is_visibly_unavailable(saved_source_subject, missing):
    import ergora.training.execution_protocol as protocol

    capability, manifest, raw, descriptor, _ = saved_source_subject
    if missing == 'subject':
        capability = None
    elif missing == 'manifest':
        manifest = None
    elif missing == 'protocol':
        raw = None
    elif missing == 'descriptor':
        descriptor = None
    else:
        manifest.pop({'protocol_ref': 'protocol_source_ref', 'descriptor_ref': 'native_descriptor_ref',
                      'subject_ref': 'capability_sha256'}[missing])
    observed = protocol.observe_source_manifest(capability, manifest, raw, descriptor)
    assert observed['state'] == 'unavailable' and observed['reasons'] == ['source_manifest_unavailable']


@pytest.mark.parametrize('fault', ['subject', 'missing_ref_conflict', 'map', 'protocol_bytes', 'descriptor_bytes', 'path', 'size',
                                  'zero_matches', 'multiple_matches', 'protocol_literal', 'member_literal', 'descriptor_binding'])
def test_saved_source_rejects_conflicts_and_refuses_ambiguous_association(saved_source_subject, fault):
    import ergora.training.execution_protocol as protocol

    capability, manifest, raw, descriptor, member = saved_source_subject
    if fault in ('subject', 'missing_ref_conflict'):
        manifest['capability_sha256'] = '0' * 64
        if fault == 'missing_ref_conflict':
            manifest.pop('protocol_source_ref')
    elif fault == 'map':
        manifest['gate_sources'].pop(member)
    elif fault == 'protocol_bytes':
        raw += b'\n'
    elif fault == 'descriptor_bytes':
        descriptor += b'\n'
    elif fault == 'path':
        manifest['protocol_source_ref']['path'] = 'other-source.py.txt'
    elif fault == 'size':
        manifest['protocol_source_ref']['bytes'] += 1
    else:
        if fault == 'zero_matches':
            capability['gate_sources'][member] = '0' * 64
        elif fault == 'multiple_matches':
            capability['gate_sources']['saved/member_0.py'] = capability['gate_sources'][member]
        elif fault in ('protocol_literal', 'member_literal'):
            raw = raw.replace(protocol.PROTOCOL.encode(), b'another-protocol') if fault == 'protocol_literal' else raw.replace(
                b'saved/member_0.py', b'saved/different.py')
            capability['gate_sources'][member] = hashlib.sha256(raw).hexdigest()
            manifest['protocol_source_ref'].update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        else:
            value = json.loads(descriptor)
            value['reference_manifest_sha256'] = '0' * 64
            descriptor = json.dumps(value).encode()
            capability['descriptor_sha256'] = hashlib.sha256(descriptor).hexdigest()
            manifest['native_descriptor_ref'].update(sha256=hashlib.sha256(descriptor).hexdigest(), bytes=len(descriptor))
        manifest['gate_sources'] = deepcopy(capability['gate_sources'])
        manifest['capability_sha256'] = protocol.CycleAdmission._sha(capability)
    if fault in ('zero_matches', 'multiple_matches'):
        observed = protocol.observe_source_manifest(capability, manifest, raw, descriptor)
        assert observed['state'] == 'unavailable' and observed['reasons'] == ['reader_unsupported']
    else:
        with pytest.raises(ValueError):
            protocol.observe_source_manifest(capability, manifest, raw, descriptor)


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{'baseline_reference_support': True, 'screen_support': True}], indirect=True)
def test_screen_opaque_check_artifacts_keep_raw_identity_and_capacity(search_execution):
    item = _prepare_cpu_screens(search_execution, [{'fault': 'screen-opaque-artifacts'}])
    result, = _execute_search(item, wait_completion=True)
    state, ident = item['state'], result['experiment_id']
    output = result['job'] / 'run-output'
    report = json.loads((output / 'screen-result.json').read_bytes())
    assert json.loads((result['job'] / 'result.json').read_bytes())['state'] == 'SCREEN_COMPLETED'
    inputs = (output / 'screen/check-inputs.bin').read_bytes()
    expected = (output / 'screen/check-expected.bin').read_bytes()
    assert b'\0' in inputs
    with pytest.raises(UnicodeDecodeError):
        inputs.decode('utf-8')
    assert 1_048_576 < len(expected) <= 16_777_216
    actual = json.loads((output / 'screen/actual-output.txt').read_bytes())
    assert [int.from_bytes(expected[index:index + 24_000], 'big')
            for index in range(0, len(expected), 24_000)] == actual
    assert all(check['status'] == 'PASS' for check in report['checks'])
    assert report['windows'][0]['input_ref']['path'] == 'screen/inputs.json'
    observed = training.evidence(state, 'demo', ident)
    assert observed['screen_status'] == 'complete' and observed['screen']['report'] == report
    originals = {path: path.read_bytes() for path in output.rglob('*') if path.is_file()}
    for path, replacement, error in (
            (output / 'screen/check-inputs.bin', inputs + b'drift', 'digest differs'),
            (output / 'screen/check-expected.bin', b'\0' * 16_777_217, 'capacity_exceeded')):
        try:
            path.write_bytes(replacement)
            with pytest.raises(ValueError, match=error):
                training.evidence(state, 'demo', ident)
        finally:
            path.write_bytes(originals[path])
    assert training.evidence(state, 'demo', ident)['screen_status'] == 'complete'
    assert {path: path.read_bytes() for path in output.rglob('*') if path.is_file()} == originals
    with pytest.raises(ValueError, match='full-verify'):
        training.approve(state, 'demo', ident, state.project('demo')['revision'],
            run_id=result['submission']['run_id'], evidence_sha256='a' * 64, confirm=True)
    assert not (item['runtime'] / 'training/approvals').exists()


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
    original = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original(name))
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
    with pytest.raises(ValueError, match='outside retained full archive observation'):
        training.evidence(state, 'demo', 'alpha', retained_archive=True,
                          artifact='notes.txt', evidence_sha256=report['evidence_sha256'])
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
    with pytest.raises(ValueError, match='size limit|capacity'):
        training.evidence(state, 'demo', 'alpha', artifact='notes.txt', evidence_sha256=report['evidence_sha256'])


@pytest.mark.parametrize('selected_installation', ('missing', 'descriptor-mismatch'))
def test_public_reference_inventory_runs_without_site_packages_or_selected_native_installation(
        archive, monkeypatch, selected_installation, tmp_path):
    state, definition, runtime, _, _, folder, report = archive
    native = Path(definition['execution']['installation'])
    descriptor = native / 'ergora-native-runtime.json'
    original_descriptor = descriptor.read_bytes()
    moved = native.with_name(native.name + '-temporarily-unavailable')
    before = {path: path.read_bytes() for path in runtime.rglob('*') if path.is_file()}
    original_popen = subprocess.Popen
    calls_path = tmp_path / 'actual-reader-operations.jsonl'
    guard = '''import sys
class DenyApplicationImports:
    def find_spec(self, fullname, *args):
        if fullname in ('ergora.storage.state', 'jsonschema', 'temporalio') or fullname.startswith(('jsonschema.', 'temporalio.')):
            raise AssertionError('Forbidden reader import: ' + fullname)
sys.meta_path.insert(0, DenyApplicationImports())
'''
    guard += f'''import json
from pathlib import Path
import ergora.training.runtime.evidence as evidence
calls_path=Path({str(calls_path)!r})
def observe(action):
    def call(payload):
        with calls_path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(payload['operation'])+'\\n')
        return action(payload)
    return call
evidence.inspect=observe(evidence.inspect)
evidence.baseline_reference=observe(evidence.baseline_reference)
'''
    def guarded(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.training.runtime.evidence import main;main()':
            assert '-S' in argv and '-P' in argv
            argv = [*argv[:-1], guard + argv[-1]]
        return original_popen(argv, *args, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', guarded)
    try:
        if selected_installation == 'missing':
            native.rename(moved)
        else:
            descriptor.write_text(json.dumps({**json.loads(original_descriptor), 'unavailable_fixture_descriptor': True}))
        ordinary = training.evidence(state, 'demo', 'alpha', artifact='notes.txt', evidence_sha256=report['evidence_sha256'])
        assert ordinary['artifact']['text'] == (folder / 'notes.txt').read_bytes().decode('utf-8')
        saved = training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256'])
        reference_document = saved['reference']
        assert saved['read_only'] is True and saved['runtime_status'] == 'not_queried'
        assert reference_document['coverage']['inventory'] == 'complete'
        assert reference_document['coverage']['applicability'] == 'not_requested'
        assert reference_document['receipt'] is None
        assert reference_document['coverage']['quality']['state'] == 'unavailable'
        assert reference_document['coverage']['execution_source']['state'] == 'unavailable'
        assert reference_document['coverage']['cleanup']['state'] == 'unavailable'
        indexed = {entry['path']: entry for entry in reference_document['inventory']['entries'] if entry['root'] == 'archive'}
        evidence = json.loads((folder / 'evidence.json').read_bytes())
        for artifact in evidence['artifacts']:
            raw = (folder / artifact['path']).read_bytes()
            assert indexed[artifact['path']]['sha256'] == artifact['sha256']
            assert indexed[artifact['path']]['bytes'] == len(raw)
        assert [json.loads(line) for line in calls_path.read_text().splitlines()] == ['inspect', 'baseline-reference']
        assert {path: path.read_bytes() for path in runtime.rglob('*') if path.is_file()} == before
    finally:
        if selected_installation == 'missing':
            moved.rename(native)
        else:
            descriptor.write_bytes(original_descriptor)


@pytest.mark.parametrize('mutation', ('raw', 'symlink', 'fifo', 'capacity'))
def test_reference_inventory_checks_every_indexed_artifact_without_blocking_on_fifo(archive, mutation):
    state, _, _, _, _, folder, report = archive
    path = folder / 'trace.bin'
    if mutation == 'raw':
        path.write_bytes(path.read_bytes() + b'drift')
    elif mutation == 'capacity':
        with path.open('wb') as stream:
            stream.truncate(16_777_217)
    else:
        if mutation == 'fifo' and not hasattr(os, 'mkfifo'):
            pytest.skip('FIFO requires POSIX')
        path.unlink()
        if mutation == 'symlink':
            try:
                path.symlink_to(folder / 'notes.txt')
            except OSError:
                pytest.skip('Symlinks require unavailable platform permission')
        else:
            os.mkfifo(path)
    # Ordinary inspect does not read this non-selected artifact; complete inventory must reject it.
    if mutation in ('raw', 'capacity'):
        assert training.evidence(state, 'demo', 'alpha')['archive']['artifact_content_status'] == 'not_read'
    with pytest.raises(ValueError):
        training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256'])


def test_inventory_enforces_remaining_capacity_after_stat(tmp_path, monkeypatch):
    from ergora.training.runtime.evidence import _Inventory

    inventory = _Inventory()
    capacity = 64 * 1_048_576
    # Model the bytes already committed by unaffected earlier inventory entries.
    inventory.total = capacity - 1
    bound = tmp_path / 'last-byte'
    empty = tmp_path / 'empty'
    growing = tmp_path / 'growing'
    bound.write_bytes(b'x')
    empty.touch()
    growing.touch()
    assert inventory.read(tmp_path, bound.name, 'archive') == b'x'
    assert inventory.total == capacity
    assert inventory.read(tmp_path, bound.name, 'archive') == b'x'
    assert inventory.read(tmp_path, empty.name, 'archive') == b''
    assert inventory.total == capacity

    stat = os.fstat
    inode = growing.stat().st_ino
    stats = 0

    def grow_after_stat(fd):
        nonlocal stats
        observed = stat(fd)
        if observed.st_ino == inode:
            stats += 1
            if stats == 2:  # _fd has already checked the descriptor type.
                assert observed.st_size == 0
                growing.write_bytes(b'y')
        return observed

    with monkeypatch.context() as patch:
        patch.setattr(os, 'fstat', grow_after_stat)
        with pytest.raises(ValueError, match='capacity_exceeded'):
            inventory.read(tmp_path, growing.name, 'archive')
    assert stats == 2 and growing.read_bytes() == b'y'
    assert inventory.total == capacity and growing not in inventory.originals
    inventory.confirm()


def test_inventory_keeps_the_first_file_identity_across_repeated_reads(tmp_path):
    from ergora.training.runtime.evidence import _Inventory

    path = tmp_path / 'original.json'
    raw = b'{"saved":"original"}\n'
    sha = hashlib.sha256(raw).hexdigest()
    path.write_bytes(raw)
    original = path.stat()
    inventory = _Inventory()
    assert inventory.read(tmp_path, path.name, 'job', sha) == raw
    replacement = tmp_path / 'replacement.json'
    replacement.write_bytes(raw)
    replacement.replace(path)
    changed = path.stat()
    assert path.read_bytes() == raw
    assert (original.st_dev, original.st_ino) != (changed.st_dev, changed.st_ino)
    observed = {'path': str(path), 'sha256': sha, 'raw_unchanged': True,
                'first_identity': [original.st_dev, original.st_ino],
                'replacement_identity': [changed.st_dev, changed.st_ino],
                'second_read_started': False, 'second_read_returned': False, 'confirm_returned': False}
    try:
        with pytest.raises(ValueError, match='archive_changed: baseline reference'):
            observed['second_read_started'] = True
            assert inventory.read(tmp_path, path.name, 'execution', sha) == raw
            observed['second_read_returned'] = True
            inventory.confirm()
            observed['confirm_returned'] = True
    finally:
        (tmp_path / 'inventory-duplicate-read.json').write_text(json.dumps(observed, indent=2) + '\n')


@pytest.mark.parametrize('mutation', ('remove', 'same-raw-inode', 'dangling-link', 'stable'))
def test_inventory_confirms_initially_present_fence_after_later_files(tmp_path, monkeypatch, mutation):
    import ergora.training.runtime.evidence as evidence
    import ergora.training.execution_protocol as protocol

    if mutation == 'dangling-link':
        probe = tmp_path / 'symlink-permission-probe'
        try:
            probe.symlink_to(tmp_path / 'missing-symlink-permission-target')
        except OSError:
            pytest.skip('Symlinks require unavailable platform permission')
        probe.unlink()
    fence, later = tmp_path / 'fence.json', tmp_path / 'later.json'
    binding = {'experiment_id': 'owned-fence', 'manifest_sha': 'a' * 64,
               'candidate_sha': 'b' * 40, 'baseline_sha': 'c' * 40}
    raw = (json.dumps({'binding': binding}) + '\n').encode()
    fence.write_bytes(raw)
    later.write_bytes(b'{"artifact":"later-confirmation"}\n')
    original = fence.stat()
    inventory = evidence._Inventory()
    assert inventory.read(tmp_path, fence.name, 'job', hashlib.sha256(raw).hexdigest(), optional=True) == raw
    assert inventory.read(tmp_path, later.name, 'archive') == later.read_bytes()
    assert json.loads(fence.read_bytes())['binding'] == binding
    original_fd = protocol._fd
    trace, later_seen, outcome, reason = [], False, 'not-returned', None
    def change_during_later_confirmation(path):
        nonlocal later_seen
        path = Path(path)
        trace.append('confirm-open:' + path.name)
        if path == later and not later_seen:
            later_seen = True
            if mutation == 'remove':
                fence.unlink()
            elif mutation == 'same-raw-inode':
                replacement = tmp_path / 'replacement.json'
                replacement.write_bytes(raw)
                replacement.replace(fence)
                assert fence.read_bytes() == raw and fence.stat().st_ino != original.st_ino
            elif mutation == 'dangling-link':
                fence.unlink()
                fence.symlink_to(tmp_path / 'missing-controlled-fence-target')
            trace.append('later-action-completed:' + mutation)
        return original_fd(path)
    monkeypatch.setattr(protocol, '_fd', change_during_later_confirmation)
    try:
        if mutation == 'stable':
            inventory.confirm()
            outcome = 'accepted'
        else:
            with pytest.raises((ValueError, OSError)) as error:
                inventory.confirm()
                outcome = 'accepted'
            outcome, reason = 'rejected', str(error.value)
    finally:
        assert later_seen and 'later-action-completed:' + mutation in trace
        if mutation in ('same-raw-inode', 'stable'):
            assert fence.read_bytes() == raw and json.loads(fence.read_bytes())['binding'] == binding
            final_inode = fence.stat().st_ino
            assert (final_inode != original.st_ino) is (mutation == 'same-raw-inode')
            final_kind = 'ordinary'
        else:
            final_inode = fence.lstat().st_ino if fence.is_symlink() else None
            final_kind = 'dangling-link' if fence.is_symlink() else 'absent'
        (tmp_path / 'present-fence-confirmation.json').write_text(json.dumps({
            'mutation': mutation, 'initial_present': True, 'initial_binding': binding,
            'initial_sha256': hashlib.sha256(raw).hexdigest(), 'first_inode': original.st_ino,
            'final_inode': final_inode, 'final_kind': final_kind, 'later_seen': later_seen,
            'trace': trace, 'outcome': outcome, 'reason': reason}, indent=2) + '\n')


def test_complete_reference_rechecks_same_inode_after_all_artifacts_are_read(archive, monkeypatch, tmp_path):
    state, _, _, _, _, folder, report = archive
    marker = tmp_path / 'actual-archive-inode-exchange.json'
    original_popen = subprocess.Popen
    program = f'''import json
from pathlib import Path
import ergora.training.runtime.evidence as evidence
target=Path({str(folder / 'trace.bin')!r})
marker=Path({str(marker)!r})
original=evidence._Inventory.confirm
def exchange_after_inventory(inventory):
    raw=target.read_bytes()
    before=target.stat().st_ino
    replacement=target.with_suffix('.replacement')
    replacement.write_bytes(raw)
    replacement.replace(target)
    marker.write_text(json.dumps({{'before':before,'after':target.stat().st_ino}}))
    return original(inventory)
evidence._Inventory.confirm=exchange_after_inventory
'''
    def invoke(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.training.runtime.evidence import main;main()':
            argv = [*argv[:-1], program + argv[-1]]
        return original_popen(argv, *args, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', invoke)
    with pytest.raises(ValueError):
        training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256'])
    exchanged = json.loads(marker.read_text())
    assert exchanged['before'] != exchanged['after']


@pytest.mark.parametrize('mutation', ('registered-manifest-lf', 'registration-lf', 'registration-inode',
                                     'late-fence', 'late-dangling-fence'))
def test_reference_rechecks_original_and_registration_guards_and_fence_absence(archive, monkeypatch, tmp_path, mutation):
    state, definition, runtime, prefix, _, _, report = archive
    if mutation == 'late-dangling-fence':
        probe = tmp_path / 'symlink-permission-probe'
        try:
            probe.symlink_to(tmp_path / 'missing-symlink-permission-target')
        except OSError:
            pytest.skip('Symlinks require unavailable platform permission')
        probe.unlink()
    saved = training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256'])
    if mutation == 'registered-manifest-lf':
        target = prefix / 'experiments/alpha/manifest.json'
    elif mutation.startswith('registration-'):
        target = Path(definition['execution']['config_directory']) / native_registration.registration_paths('demo')[0]
    else:
        target = runtime / 'training/fences/alpha.json'
    original_raw = target.read_bytes() if target.exists() else None
    marker = tmp_path / 'actual-reference-guard-change.json'
    program = f'''import hashlib,json
from pathlib import Path
import ergora.training.runtime.evidence as evidence
target=Path({str(target)!r})
marker=Path({str(marker)!r})
mutation={mutation!r}
original=evidence._Inventory.confirm
def change_after_first_reads(inventory):
    before=target.read_bytes() if target.exists() else None
    before_inode=target.stat().st_ino if before is not None else None
    enrolled=target in inventory.originals
    target.parent.mkdir(parents=True,exist_ok=True)
    if mutation.endswith('-lf'):
        target.write_bytes(before+b'\\n')
    elif mutation=='registration-inode':
        replacement=target.with_suffix('.replacement')
        replacement.write_bytes(before)
        replacement.replace(target)
    elif mutation=='late-fence':
        target.write_text(json.dumps({{'binding':{saved['reference']['source']['binding']!r}}}))
    else:
        target.symlink_to(target.with_name('missing-controlled-fence-target'))
    after=target.read_bytes() if target.exists() else None
    marker.write_text(json.dumps({{'mutation':mutation,'target':str(target),'enrolled':enrolled,
        'before_sha256':hashlib.sha256(before).hexdigest() if before is not None else None,
        'after_sha256':hashlib.sha256(after).hexdigest() if after is not None else None,
        'same_json':json.loads(before)==json.loads(after) if before is not None and after is not None else None,
        'same_raw':before==after,'before_inode':before_inode,'after_inode':target.lstat().st_ino,
        'visible_at_final_confirm':True,'dangling':target.is_symlink() and not target.exists()}}))
    return original(inventory)
evidence._Inventory.confirm=change_after_first_reads
'''
    original_popen = subprocess.Popen
    def inject(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.training.runtime.evidence import main;main()':
            assert '-S' in argv and '-P' in argv
            argv = [*argv[:-1], program + argv[-1]]
        return original_popen(argv, *args, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', inject)
    try:
        with pytest.raises(ValueError, match='archive_changed'):
            training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256'])
    finally:
        if original_raw is None:
            if target.exists() or target.is_symlink():
                target.unlink()
        else:
            target.write_bytes(original_raw)
        assert marker.is_file(), 'The controlled change must actually occur at final confirmation'
        changed = json.loads(marker.read_bytes())
        if mutation.endswith('-lf'):
            assert changed['same_json'] is True and changed['before_sha256'] != changed['after_sha256']
        elif mutation == 'registration-inode':
            assert changed['same_raw'] is True and changed['before_inode'] != changed['after_inode']
        else:
            assert changed['before_inode'] is None and changed['visible_at_final_confirm'] is True
            assert changed['dangling'] is (mutation == 'late-dangling-fence')


def test_reference_is_independent_of_mutable_heads_and_registration_formatting(archive, monkeypatch, tmp_path):
    state, definition, runtime, prefix, write, folder, report = archive
    saved = training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256'])
    head = prefix / 'baseline.json'
    config = Path(definition['execution']['config_directory'])
    guard = config / native_registration.registration_paths('demo')[0]
    head_raw, guard_raw = head.read_bytes(), guard.read_bytes()
    try:
        write(head, {**json.loads(head_raw), 'baseline_id': 'different-current-head'})
        guard.write_bytes(guard_raw + b'\n')
        assert training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256']) == saved
        ignored = [head, config / 'training-runners/trusted.json',
                   runtime / ('training/integration-tickets/alpha-' + report['evidence_sha256'][:16] + '.json'),
                   runtime / 'training/negative-results/alpha.json']
        marker = tmp_path / 'actual-mutable-head-read-guard.txt'
        program = f'''from pathlib import Path
import ergora.training.materials as materials; import ergora.training.execution_protocol as protocol
ignored={{Path(value) for value in {[str(path) for path in ignored]!r}}}
marker=Path({str(marker)!r})
original_raw,original_fd=materials.read_raw,protocol._fd
def checked_raw(path,*args,**kwargs):
    assert Path(path) not in ignored,'unrelated mutable reference read: '+str(path)
    marker.write_text('actual guarded material read')
    return original_raw(path,*args,**kwargs)
def checked_fd(path,*args,**kwargs):
    assert Path(path) not in ignored,'unrelated mutable reference read: '+str(path)
    marker.write_text('actual guarded inventory read')
    return original_fd(path,*args,**kwargs)
materials.read_raw=checked_raw
protocol._fd=checked_fd
'''
        original_popen = subprocess.Popen
        def inject(argv, *args, **kwargs):
            if argv[-1] == 'from ergora.training.runtime.evidence import main;main()':
                argv = [*argv[:-1], program + argv[-1]]
            return original_popen(argv, *args, **kwargs)
        monkeypatch.setattr(subprocess, 'Popen', inject)
        assert training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256']) == saved
        assert marker.is_file(), 'The mutable-head read guard must run inside the actual reader'
    finally:
        head.write_bytes(head_raw)
        guard.write_bytes(guard_raw)


@pytest.mark.parametrize('updates,expected_state', [
    pytest.param({'metric': True}, None, id='metric-bool'),
    pytest.param({'unit': True}, None, id='unit-bool'),
    pytest.param({'unit': []}, None, id='unit-list'),
    pytest.param({'unit': ''}, None, id='unit-empty'),
    pytest.param({'aggregation': {'kind': 'peak'}}, None, id='aggregation-object'),
    pytest.param({'scope': True}, None, id='scope-bool'),
    pytest.param({'scope': []}, None, id='scope-list'),
    pytest.param({'scope': {}}, None, id='scope-empty-object'),
    pytest.param({'scope': '  '}, None, id='scope-blank'),
    pytest.param({'scope': {'process': 'runner', 'ranks': [0]}}, 'observed', id='structured-scope-data'),
    pytest.param({'unit': 'unrecognized-pages', 'limit': 0}, 'unavailable', id='unknown-unit-no-comparison'),
])
def test_resource_metric_metadata_types_are_distinct_from_measurements(updates, expected_state):
    """Resource metadata only: no process memory observation or accepted full is synthesized."""
    from ergora.training.runtime.evidence import _resource_coverage

    metric = {'metric': 'peak_memory', 'unit': 'bytes', 'aggregation': 'peak',
              'scope': 'whole_runner_process', 'observed': 7, 'limit': 8, **updates}
    raw = (json.dumps({'metric': metric}, allow_nan=False) + '\n').encode()
    resource_ref = {'path': 'resource-report.json', 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    selected = {**metric, 'report_ref': resource_ref}
    artifacts = {resource_ref['path']: resource_ref}
    def read_artifact(value):
        assert artifacts[value['path']] == value
        assert hashlib.sha256(raw).hexdigest() == value['sha256'] and len(raw) == value['bytes']
        return json.loads(raw)
    if expected_state is None:
        with pytest.raises(ValueError, match='[Rr]esource'):
            _resource_coverage([selected], artifacts, read_artifact)
    else:
        result = _resource_coverage([selected], artifacts, read_artifact)
        assert result['state'] == expected_state and result['metrics'] == [selected]
        assert not any(reason['code'] == 'resource_limit_exceeded' for reason in result['reasons'])


def test_no_archive_and_cli_http_share_the_observation(experiments):
    state = experiments[0]
    assert training.evidence(state, 'demo', 'alpha')['archive_status'] == 'no_accepted_archive'
    assert training.evidence(state, 'demo', 'beta')['recorded_gate_report'] is None
    from ergora.interfaces.cli import main
    output = io.StringIO()
    with redirect_stdout(output):
        assert main(['--home', str(state.root), 'training', 'evidence', 'demo', 'alpha']) == 0
    assert json.loads(output.getvalue()) == training.evidence(state, 'demo', 'alpha')
    pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    from ergora.interfaces.web import create_app
    headers = {'Origin': 'http://127.0.0.1:8977', 'X-Ergora-Request': '1'}
    with TestClient(create_app(state.root), base_url=headers['Origin'], headers=headers) as client:
        response = client.get('/api/projects/demo/training/alpha/evidence')
        assert response.status_code == 200 and response.json() == json.loads(output.getvalue())
        assert 'retained_archive' not in response.json()
        retained = client.get('/api/projects/demo/training/alpha/evidence', params={'retained_archive': True})
        assert retained.status_code == 200
        assert retained.json() == training.evidence(state, 'demo', 'alpha', retained_archive=True)
        assert retained.json()['retained_archive']['status'] == 'unavailable'
        assert client.get('/api/projects/demo/training/alpha/evidence', params={'artifact': 'notes.txt'}).status_code == 400
        assert client.get('/api/projects/demo/training/alpha/evidence', params={
            'retained_archive': True, 'artifact': 'notes.txt', 'evidence_sha256': '0' * 64}).status_code == 400


def test_round_index_retains_negative_unknown_and_offline_cli_read(experiments, tmp_path, monkeypatch):
    pytest.importorskip('temporalio')
    import ergora.training.rounds as training_rounds
    from ergora.interfaces.cli import main

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
    original_find = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: None if name == 'temporalio' else original_find(name))
    output = io.StringIO()
    unused_home = tmp_path / 'unused-control-home'
    with redirect_stdout(output):
        assert main(['--home', str(unused_home), 'training', 'rounds-read', str(tmp_path / 'second'),
                     '--sha256', second['sha256']]) == 0
    assert json.loads(output.getvalue())['report'] == report and not unused_home.exists()


def test_round_extension_preserves_accepted_prefix_and_failed_result_after_baseline_drift(archive, tmp_path):
    pytest.importorskip('temporalio')
    import ergora.training.rounds as training_rounds

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
    import ergora.training.rounds as training_rounds

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


def test_round_content_validates_original_bindings_without_site_packages(experiments, tmp_path):
    import ergora.training.rounds as training_rounds

    created = training_rounds.create(experiments[0], 'demo', {'schema_version': 1, 'rounds': [{
        'experiment_id': 'alpha', 'change': '保留原始观察 🌱',
        'next_bottleneck': 'No measured optimization claim'}]}, tmp_path / 'index')
    isolated = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', '''import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from ergora.training.execution_protocol import encode_round_content,round_content_sha,validate_round_content
raw=Path(sys.argv[2]).read_bytes()
report=json.loads(raw)
validate_round_content(report)
assert encode_round_content(report)==raw
assert hashlib.sha256(raw).hexdigest()==sys.argv[3]
assert report['rounds'][0]['annotation']['change']=='保留原始观察 🌱'
item=report['rounds'][0]
item['native']['evidence']['project_revision']+=1
item['sha256']=round_content_sha({key:value for key,value in item.items() if key!='sha256'})
try:
    validate_round_content(report)
except ValueError as error:
    assert 'different projects or revisions' in str(error)
else:
    raise AssertionError('A self-consistent content hash cannot replace original observation bindings')
assert not any(name in sys.modules for name in ('yaml','jsonschema','temporalio','dev_platform','ergora.storage.state','ergora.training.application'))
''', str(IMPORT_ROOT), str(tmp_path / 'index/rounds.json'), created['sha256']],
        capture_output=True, text=True, encoding='utf-8', timeout=10)
    assert isolated.returncode == 0, isolated.stderr


@pytest.fixture
def cpu_profile_capture(tmp_path, monkeypatch):
    """Real cProfile/source callback and durable files; managed-chain admission is a leaf."""
    if sys.platform != 'linux':
        pytest.skip('Profile capture requires Linux durable publication and SIGALRM sub-caps')
    import runpy
    from types import SimpleNamespace
    import ergora.training.configuration as wrapper
    import ergora.training.materials as materials
    from ergora.training.execution_protocol import ExecutionRecords

    policy = {'protocol': 'training-profile-v1', 'tool': 'cprofile-json', 'reader': 'cprofile-json-v1',
        'source_operation': 'cpu-diagnostic-v1', 'phases': ['baseline', 'screen'], 'ranks': [0],
        'window': {'unit': 'source_samples', 'work': 17, 'warmup_work': 3}, 'captures': 2,
        'maximum_seconds': 3, 'max_raw_bytes': 524_288, 'max_derived_bytes': 131_072, 'required': True}
    output = tmp_path / 'job/run-output'
    output.mkdir(parents=True)
    markers = tmp_path / 'markers'
    monkeypatch.setenv('ERGORA_TEST_CONFIGURATION_MARKERS', str(markers))
    source = {'repo': str(tmp_path), 'commit': '1' * 40, 'inventory_sha256': '2' * 64, 'entrypoint': 'driver.py'}
    request = {'binding': {'experiment_id': 'candidate-screen'}, 'managed': {'request_sha256': '3' * 64},
        'native_request_sha256': '4' * 64, 'execution_phase_id': 'unit-cpu-phase',
        'configuration_readback': {'source': source, 'profile': {'protocol': 'training-profile-v1', 'operations': ['cpu-diagnostic-v1']}},
        'execution': {'operation': 'training-screen-v1', 'profile': policy}}
    raw = materials.observation_bytes(request)
    context = {'configurations': {arm: {'global_batch': 6, 'microbatch': 3, 'accumulation': 2,
        'strategy': 'closed-form', 'fault': None} for arm in ('baseline', 'candidate')}, 'identity': 'same-source-context'}
    driver = runpy.run_path(str(Path(__file__).parent / 'fixtures/training_configuration_driver.py'))
    checks = []
    chain = ExecutionRecords.__new__(ExecutionRecords)
    chain.root = tmp_path
    chain.folder = output.parent / 'managed-execution'
    chain.records = {'ack': {}}
    chain.originals = {chain.folder / 'attempt.json': b'original CPU profile fixture attempt'}

    def active(current, original):
        assert current == request and original == raw
        checks.append('original-chain-admission')
        return chain, {}
    monkeypatch.setattr(wrapper, '_inputs', active)
    def publish(path, value, chain):
        original = materials.observation_bytes(value) + b'\n'
        materials.publish_material(path, original, chain.root)
        return original
    monkeypatch.setattr(wrapper, '_publish_receipt', publish)
    def capture(*, first_failure=None):
        return wrapper._record_profile(driver, context, request, output, raw, first_failure=first_failure)
    return SimpleNamespace(policy=policy, output=output, request=request, raw=raw, context=context,
        capture=capture, driver=driver, markers=markers, checks=checks)


def test_independent_cpu_profile_captures_are_actual_finite_json_and_fixed_readback(cpu_profile_capture):
    import ergora.training.runtime.evidence as evidence
    item = cpu_profile_capture
    originals = item.capture()
    bundle = evidence.profile_bundle(item.output, item.policy, request={**item.request, '_raw_sha256': hashlib.sha256(item.raw).hexdigest()})
    assert evidence.validate_trial_diagnostics(bundle, item.policy)['required_satisfied'] is True
    assert len(bundle['raw']) == len(bundle['derived']) == 2
    actual = [json.loads(line) for line in (item.markers / 'profile.jsonl').read_text().splitlines()]
    assert all(entry['identity'] == 'same-source-context' and entry['source_samples'] == 17 for entry in actual)
    assert len({entry['window_id'] for entry in actual}) == len({entry['run_id'] for entry in actual}) == 2
    assert all(capture['capture']['actual']['measurement_mode'] == 'profiled' for capture in bundle['raw'])
    assert all('calculate' in derived['text'] for derived in bundle['derived'])
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert not list(item.output.rglob('*.prof')) and not (item.output / 'screen-result.json').exists()
    baseline = {'reference': {'kind': 'baseline-reference', 'inventory': {'entries': []}}, 'diagnostics': bundle}
    packet = evidence.build_analysis_packet(baseline=baseline, screen=None,
        source_materials={'flow_map': {'nodes': ['actual-source'], 'edges': []}}, policy=item.policy)
    assert packet['packet']['profile']['receipt_ref'] == bundle['receipt_ref']
    assert packet['packet']['profile']['raw'] == bundle['raw']
    assert packet['packet']['unprofiled_screen'] is None
    assert len(item.checks) > 2


@pytest.mark.parametrize('condition,status', [('first-failure', 'not_run'), ('unsupported-tool', 'unavailable'), ('missing-source-operation', 'unavailable')])
def test_optional_unavailable_or_first_failure_never_opens_profile_window(cpu_profile_capture, condition, status):
    import ergora.training.runtime.evidence as evidence
    item = cpu_profile_capture
    item.policy['required'] = False
    if condition == 'unsupported-tool':
        item.policy['tool'] = 'ncu'
    elif condition == 'missing-source-operation':
        item.request['configuration_readback']['profile'] = None
    item.capture(first_failure={'check_id': 'finite'} if condition == 'first-failure' else None)
    bundle = evidence.profile_bundle(item.output, item.policy)
    assert bundle['status'] == status and bundle['receipt']['reason']
    assert bundle['raw'] == bundle['derived'] == []
    assert not (item.markers / 'profile.jsonl').exists() and not (item.output / 'profile').exists()
    assert evidence.validate_trial_diagnostics(bundle, item.policy)['required_satisfied'] is False
    item.policy['required'] = True
    bundle['receipt']['policy_sha256'] = __import__('ergora.training.materials', fromlist=['observation_sha256']).observation_sha256(item.policy)
    with pytest.raises(ValueError, match='policy differs'):
        evidence.validate_trial_diagnostics(bundle, item.policy)


@pytest.mark.parametrize('fault', ['profile-exception', 'profile-timeout'])
def test_profile_callback_failure_or_subcap_is_never_optional_success(cpu_profile_capture, fault):
    import ergora.training.runtime.evidence as evidence
    item = cpu_profile_capture
    item.context['configurations']['candidate']['fault'] = fault
    item.policy['required'] = False
    item.policy['maximum_seconds'] = 0.04
    item.capture()
    bundle = evidence.profile_bundle(item.output, item.policy)
    assert bundle['status'] == 'failed' and bundle['receipt']['reason']
    with pytest.raises(ValueError, match='failed or remains unknown'):
        evidence.validate_trial_diagnostics(bundle, item.policy)
    assert not (item.markers / 'profile.jsonl').exists()


def test_profile_reader_rejects_tampering_inode_symlink_and_capacity(cpu_profile_capture):
    import ergora.training.runtime.evidence as evidence
    item = cpu_profile_capture
    item.capture()
    bundle = evidence.profile_bundle(item.output, item.policy)
    raw_path = item.output / bundle['raw'][0]['ref']['path']
    original = raw_path.read_bytes()
    raw_path.write_bytes(original + b'\n')
    with pytest.raises(ValueError, match='digest differs'):
        evidence.profile_bundle(item.output, item.policy)
    raw_path.write_bytes(original)
    inventory = evidence.profile_bundle(item.output, item.policy)['inventory']
    replacement = raw_path.with_suffix('.replacement')
    replacement.write_bytes(original)
    replacement.replace(raw_path)
    with pytest.raises(ValueError, match='inode or raw'):
        inventory.confirm()
    raw_path.rename(replacement)
    raw_path.symlink_to(replacement)
    with pytest.raises(ValueError, match='Symlinks|symlink'):
        evidence.profile_bundle(item.output, item.policy)
    raw_path.unlink()
    replacement.rename(raw_path)
    raw_path.write_bytes(b' ' * (item.policy['max_raw_bytes'] + 1))
    with pytest.raises(ValueError, match='capacity_exceeded'):
        evidence.profile_bundle(item.output, item.policy)


def test_missing_original_baseline_diagnostics_blocks_without_recollection():
    from ergora.training.runtime.evidence import build_analysis_packet
    from ergora.training.materials import validate_profile_policy
    policy = {'protocol': 'training-profile-v1', 'tool': 'cprofile-json', 'reader': 'cprofile-json-v1',
        'source_operation': 'cpu-diagnostic-v1', 'phases': ['baseline', 'screen'], 'ranks': [0],
        'window': {'unit': 'source_samples', 'work': 1, 'warmup_work': 0}, 'captures': 1,
        'maximum_seconds': 1, 'max_raw_bytes': 1024, 'max_derived_bytes': 1024, 'required': True}
    validate_profile_policy(policy)
    with pytest.raises(ValueError, match='receipt is missing or unknown'):
        build_analysis_packet(baseline={'reference': {'kind': 'baseline-reference'}}, screen=None,
            source_materials={'flow_map': {'nodes': ['source']}}, policy=policy)


def test_required_first_failure_blocks_and_late_capture_is_not_absence(cpu_profile_capture):
    import ergora.training.runtime.evidence as evidence
    item = cpu_profile_capture
    item.capture(first_failure={'check_id': 'finite'})
    bundle = evidence.profile_bundle(item.output, item.policy)
    with pytest.raises(ValueError, match='required diagnostic'):
        evidence.validate_trial_diagnostics(bundle, item.policy)
    assert not (item.markers / 'profile.jsonl').exists()
    late = item.output / 'profile/screen-0-0.json'
    late.parent.mkdir()
    late.write_bytes(b'{}')
    with pytest.raises(ValueError, match='absence became visible'):
        bundle['inventory'].confirm()
    with pytest.raises(ValueError, match='already has an original capture opportunity'):
        evidence.profile_bundle(item.output, item.policy)


def test_profile_reader_failure_and_complete_capacity_do_not_become_optional_absence(cpu_profile_capture, monkeypatch):
    import ergora.training.runtime.evidence as evidence
    item = cpu_profile_capture
    item.policy['required'] = False
    item.policy['max_raw_bytes'] = 16
    item.capture()
    bundle = evidence.profile_bundle(item.output, item.policy)
    assert bundle['status'] == 'failed' and bundle['receipt']['readback'] == 'failed'
    with pytest.raises(ValueError, match='failed or remains unknown'):
        evidence.validate_trial_diagnostics(bundle, item.policy)


def test_profile_offline_reader_denies_state_sdk_and_historical_source_execution(cpu_profile_capture):
    item = cpu_profile_capture
    item.capture()
    source = IMPORT_ROOT
    code = '''import json,sys
from pathlib import Path
class DenyApplication:
    def find_spec(self,name,*args):
        if name in ('ergora.storage.state','jsonschema','temporalio','perf_temporal','dev_platform') or name.startswith(('jsonschema.','temporalio.','perf_temporal.','dev_platform.')):
            raise AssertionError('Offline profile reader imported application/native SDK: '+name)
sys.meta_path.insert(0,DenyApplication())
sys.path.insert(0,sys.argv[1])
from ergora.training.runtime.evidence import profile_bundle
receipt=json.loads((Path(sys.argv[2])/'profile-receipt.json').read_bytes())
bundle=profile_bundle(Path(sys.argv[2]),receipt['policy'])
assert bundle['status']=='complete' and len(bundle['raw'])==2
'''
    result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code, str(source), str(item.output)],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_later_profile_failure_preserves_actual_prior_capture(cpu_profile_capture):
    import ergora.training.runtime.evidence as evidence
    item = cpu_profile_capture
    original = item.driver['profile']
    def second_fails(*args, selection, **kwargs):
        if selection['capture_index'] == 1:
            raise ValueError('Second independent diagnostic failed after first complete capture')
        return original(*args, selection=selection, **kwargs)
    item.driver['profile'] = second_fails
    item.capture()
    bundle = evidence.profile_bundle(item.output, item.policy)
    assert bundle['status'] == 'failed'
    assert len(bundle['raw']) == len(bundle['derived']) == 1
    assert [entry['capture'] for entry in bundle['receipt']['attempts']] == ['complete', 'failed']
    assert bundle['receipt']['raw_bytes'] == bundle['raw'][0]['ref']['bytes']
    with pytest.raises(ValueError, match='failed or remains unknown'):
        evidence.validate_trial_diagnostics(bundle, item.policy)


def test_complete_analysis_packet_preserves_large_material_and_rejects_overflow(cpu_profile_capture):
    import ergora.training.runtime.evidence as evidence
    item = cpu_profile_capture
    item.capture()
    bundle = evidence.profile_bundle(item.output, item.policy)
    baseline = {'reference': {'kind': 'baseline-reference'}, 'diagnostics': bundle}
    material = {'flow_map': {'complete_utf8': 'x' * 1_100_000}}
    packet = evidence.build_analysis_packet(baseline=baseline, screen=None, source_materials=material, policy=item.policy)
    assert packet['packet']['source_materials'] == material and packet['bytes'] > 1_100_000
    with pytest.raises(ValueError, match='complete read capacity'):
        evidence.build_analysis_packet(baseline=baseline, screen=None,
            source_materials={'flow_map': {'complete_utf8': 'x' * 10_000_000}}, policy=item.policy)


@pytest.mark.parametrize('actual', ['CPU', 'CUDA', None])
def test_cpu_profile_admission_consumes_actual_baseline_environment(actual):
    from ergora.training.runtime.evidence import validate_cpu_applicability
    baseline = {'reference_sha256': 'a' * 64, 'reference': {'receipt': {
        'environment': {'observed': {'device': actual, 'ranks': [0], 'layout': 'single-process'},
                        'report_ref': {'path': 'baseline-environment.json', 'sha256': 'b' * 64, 'bytes': 42}},
        'baseline': {'workload': {'layout': {'kind': 'cpu-single-process'}}}}}}
    if actual == 'CPU':
        proof = validate_cpu_applicability(baseline)
        assert proof['environment']['device'] == 'CPU' and proof['baseline_reference_sha256'] == 'a' * 64
        with pytest.raises(ValueError, match='actual CPU single-process'):
            validate_cpu_applicability(baseline, observations={arm: {'workload': {'layout': {'kind': 'gpu'}}}
                                                            for arm in ('baseline', 'candidate')})
    else:
        with pytest.raises(ValueError, match='unsupported: original baseline'):
            validate_cpu_applicability(baseline)


@pytest.mark.parametrize('installation', ['managed'], indirect=True)
@pytest.mark.parametrize('search_execution', [{
    'baseline_reference_support': True, 'screen_support': True, 'profile_support': True,
    'profile_policy': {'protocol': 'training-profile-v1', 'tool': 'cprofile-json', 'reader': 'cprofile-json-v1',
        'source_operation': 'cpu-diagnostic-v1', 'phases': ['baseline', 'screen'], 'ranks': [0],
        'window': {'unit': 'source_samples', 'work': 13, 'warmup_work': 2}, 'captures': 1,
        'maximum_seconds': 5, 'max_raw_bytes': 1_048_576, 'max_derived_bytes': 65_536, 'required': True}}], indirect=True)
def test_managed_cpu_wrapper_freezes_one_baseline_and_independent_screen_profiles(search_execution):
    from ergora.training.runtime.evidence import profile_bundle, validate_trial_diagnostics, validate_cpu_applicability
    item = _prepare_cpu_screens(search_execution, [{'global_batch': 24}, {'global_batch': 48}])
    policy = item['profile_policy']
    baseline = item['reference_saved']
    validate_cpu_applicability(baseline)
    validate_trial_diagnostics(baseline['diagnostics'], policy)
    baseline_job = item['reference_source']['job']
    baseline_originals = {path: path.read_bytes() for path in baseline_job.rglob('*') if path.is_file()}
    baseline_receipt = baseline['diagnostics']['receipt']
    assert baseline_receipt['phase'] == 'baseline' and baseline_receipt['status'] == 'complete'
    results = _execute_search(item, wait_completion=True)
    all_window_ids = {entry['selection']['window_id'] for entry in baseline_receipt['captures']}
    for result in results:
        output = result['job'] / 'run-output'
        typed = json.loads((output / 'screen-result.json').read_bytes())
        assert json.loads((result['job'] / 'result.json').read_bytes())['state'] == 'SCREEN_COMPLETED'
        assert all(window['measurement_mode'] == 'unprofiled' for window in typed['windows'])
        diagnostics = profile_bundle(output, policy)
        validate_trial_diagnostics(diagnostics, policy)
        assert diagnostics['receipt']['phase'] == 'screen'
        for entry in diagnostics['receipt']['captures']:
            assert entry['selection']['window_id'] not in all_window_ids
            assert entry['selection']['window_id'] not in {window['provenance']['window_id'] for window in typed['windows']}
            all_window_ids.add(entry['selection']['window_id'])
        assert all(result['execution'][key] is True for key in ('durable_stop_confirmed', 'executor_stop_confirmed'))
        observed = training.evidence(item['state'], 'demo', result['experiment_id'])
        assert observed['screen_status'] == 'complete'
    screen = results[0]
    output = screen['job'] / 'run-output'
    managed = screen['job'] / 'managed-execution'
    original_receipt = output / 'profile-receipt.json'
    original_raw = original_receipt.read_bytes()
    raw_capture = output / 'profile/screen-0-0.json'
    selection = {'profile_attempt_sha256': hashlib.sha256((managed / 'attempt.json').read_bytes()).hexdigest(),
                 'profile_capture_sha256': hashlib.sha256(raw_capture.read_bytes()).hexdigest()}
    profile = training.evidence(item['state'], 'demo', screen['experiment_id'], **selection)['profile_recovery']
    assert profile['original_profile_receipt']['sha256'] == hashlib.sha256(original_raw).hexdigest()
    assert profile['native_result_state'] == 'SCREEN_COMPLETED'
    assert profile['derived']['text'] == (output / 'profile/screen-0-0.txt').read_text()
    original_receipt.write_bytes(original_raw + b'\n')
    try:
        with pytest.raises(ValueError, match='digest differs'):
            training.evidence(item['state'], 'demo', screen['experiment_id'], **selection)
    finally:
        original_receipt.write_bytes(original_raw)
    hidden = original_receipt.with_suffix('.hidden')
    original_receipt.rename(hidden)
    try:
        with pytest.raises(ValueError):
            training.evidence(item['state'], 'demo', screen['experiment_id'], **selection)
    finally:
        hidden.rename(original_receipt)
    markers = [json.loads(line) for line in (item['markers'] / 'profile.jsonl').read_text().splitlines()]
    assert [entry['phase'] for entry in markers] == ['baseline', 'screen', 'screen']
    assert len({entry['run_id'] for entry in markers}) == 3
    assert all(path.read_bytes() == raw for path, raw in baseline_originals.items())


def test_original_stop_after_profile_callback_prevents_next_capture_and_receipt(cpu_profile_capture, monkeypatch):
    import ergora.training.configuration as wrapper
    item = cpu_profile_capture
    admitted = wrapper._inputs
    def stop_after_original_callback(request, original):
        if (item.markers / 'profile.jsonl').exists():
            raise ValueError('Original stop became visible during the source callback')
        return admitted(request, original)
    monkeypatch.setattr(wrapper, '_inputs', stop_after_original_callback)
    with pytest.raises(ValueError, match='Original stop became visible'):
        item.capture()
    markers = (item.markers / 'profile.jsonl').read_text().splitlines()
    assert len(markers) == 1
    assert not (item.output / 'profile-receipt.json').exists()
    assert not list(item.output.rglob('*.json'))


@pytest.fixture
def f1_cpu_snapshot():
    """Data-only original OS frames for the explicitly supported narrow CPU scope."""
    import ergora.training.materials as materials
    model = {'vendor_id': 'GenuineIntel', 'cpu family': '6', 'model': '85', 'model name': 'Original CPU model',
        'stepping': '7', 'microcode': '0x5003605', 'flags': 'fpu sse sse2 avx avx2', 'cache size': '1024 KB',
        'clflush size': '64', 'cache_alignment': '64', 'address sizes': '46 bits physical, 48 bits virtual'}
    root_files = {name: None for name in materials._CPU_LIMIT_FILES}
    root_files.update({'cpuset.cpus.effective': '0-1\n', 'cpuset.mems.effective': '0\n'})
    child_files = {**root_files, 'cpu.max': '100000 100000\n', 'cpu.weight': '100\n',
                   'cpu.max.burst': '0\n', 'cpu.idle': '0\n', 'cpu.uclamp.min': '0.00\n', 'cpu.uclamp.max': 'max\n'}
    raw = {'boot_id': '12345678-1234-1234-1234-123456789abc\n', 'architecture': 'x86_64',
        'online': '0-1\n', 'affinity': [0, 1], 'models': [model],
        'cpus': [{'cpu': cpu, 'model_index': 0, 'package_id': '0\n', 'core_id': '0\n', 'thread_siblings': '0-1\n'} for cpu in (0, 1)],
        'frequency': [{'related_cpus': '0 1\n', 'driver': 'intel_pstate\n', 'governor': 'performance\n',
            'minimum_khz': '1000000\n', 'maximum_khz': '3000000\n',
            'hardware_minimum_khz': '800000\n', 'hardware_maximum_khz': '3500000\n'}],
        'cgroup_membership': '0::/jobs/run\n',
        'cgroup_mount': '27 23 0:25 / /sys/fs/cgroup rw,nosuid,nodev,noexec - cgroup2 cgroup rw',
        'cgroup_namespace': 'cgroup:[4026531835]',
        'limits': [{'relative': '/', 'files': root_files}, {'relative': '/jobs', 'files': dict(child_files)},
                   {'relative': '/jobs/run', 'files': dict(child_files)}],
        'scheduler': {'policy': 0, 'priority': 0, 'nice': 0, 'uclamp_min': '0', 'uclamp_max': '1024'}}
    def snapshot(value):
        identity = materials._cpu_identity_from_raw(value)
        return {'protocol': materials.CPU_IDENTITY_PROTOCOL, 'scope': materials.CPU_IDENTITY_SCOPE,
                'raw': value, 'identity': identity, 'raw_sha256': materials.observation_sha256(value),
                'identity_sha256': materials.observation_sha256(identity)}
    return raw, snapshot


@pytest.mark.parametrize('change', ['model', 'topology', 'affinity', 'cpuset', 'quota', 'frequency', 'scheduler', 'boot'])
def test_f1_independent_current_cpu_facts_change_observations_without_reuse_grant(f1_cpu_snapshot, change):
    from copy import deepcopy
    import ergora.training.materials as materials
    original_raw, snapshot = f1_cpu_snapshot
    current_raw = deepcopy(original_raw)
    if change == 'model':
        current_raw['models'][0]['model name'] = 'Different physical CPU model'
    elif change == 'topology':
        current_raw['cpus'][1]['core_id'] = '1\n'
        current_raw['cpus'][0]['thread_siblings'] = '0\n'
        current_raw['cpus'][1]['thread_siblings'] = '1\n'
    elif change == 'affinity':
        current_raw['affinity'] = [0]
        current_raw['cpus'] = current_raw['cpus'][:1]
    elif change == 'cpuset':
        current_raw['online'] = '0-2\n'
        for item in current_raw['limits']:
            item['files']['cpuset.cpus.effective'] = '0-2\n'
    elif change == 'quota':
        current_raw['limits'][-1]['files']['cpu.max'] = '50000 100000\n'
    elif change == 'frequency':
        current_raw['frequency'][0]['maximum_khz'] = '2000000\n'
    elif change == 'scheduler':
        current_raw['scheduler']['nice'] = 5
    else:
        current_raw['boot_id'] = '12345678-1234-1234-1234-123456789abd\n'
    historical = materials._read_cpu_execution_identity(snapshot(original_raw))
    current = materials._read_cpu_execution_identity(snapshot(current_raw))
    assert set(historical) == {'protocol', 'scope', 'hardware', 'placement'}
    assert current != historical
    assert materials.observation_sha256(current) != materials.observation_sha256(historical)
    for facts in (original_raw, current_raw):
        with pytest.raises(ValueError, match='independent.*complete allocation ancestry'):
            materials.validate_cpu_execution_identity(snapshot(facts))


def test_f1_cpu_reader_rejects_undeclared_identity_and_hidden_allocation(f1_cpu_snapshot):
    from copy import deepcopy
    import ergora.training.materials as materials
    original_raw, snapshot = f1_cpu_snapshot
    saved = snapshot(original_raw)
    saved['identity']['hardware']['architecture'] = 'A changed derived assertion'
    with pytest.raises(ValueError, match='differs from its original raw facts'):
        materials.validate_cpu_execution_identity(saved)
    clipped = deepcopy(original_raw)
    clipped['limits'][0]['files']['cpu.max'] = '200000 100000\n'
    visible = snapshot(clipped)
    assert materials._read_cpu_execution_identity(visible)['placement']['cgroup']['allocations'][0]['files']['cpu.max']
    with pytest.raises(ValueError, match='independent.*complete allocation ancestry'):
        materials.validate_cpu_execution_identity(visible)


def test_f1_source_window_binding_and_changes_do_not_backfill_old_facts(f1_cpu_snapshot):
    from copy import deepcopy
    import ergora.training.materials as materials
    raw, snapshot = f1_cpu_snapshot
    request = {'binding': {'experiment_id': 'original-screen'}, 'native_request_sha256': 'a' * 64,
        'managed': {'request_sha256': 'b' * 64}, 'execution_phase_id': 'original-phase',
        'configuration_readback': {'source': {'repo': '/original-source', 'commit': 'c' * 40,
            'entrypoint': 'driver.py', 'inventory_sha256': 'd' * 64}}}
    windows = [{'run_id': 'original-run', 'window_id': 'original-window'}]
    kwargs = {'binding': request['binding'], 'native_request_sha256': request['native_request_sha256'],
        'managed': request['managed'], 'source': request['configuration_readback']['source'],
        'execution_phase_id': request['execution_phase_id'], 'phase': 'screen', 'operation': 'unprofiled', 'windows': windows}
    proof = materials.cpu_window_identity(request, 'screen', 'unprofiled', windows, snapshot(raw), snapshot(deepcopy(raw)))
    assert proof['state'] == 'unsupported'
    assert materials.validate_cpu_window_identity(proof, **kwargs, require_complete=False) is None
    with pytest.raises(ValueError, match='independent.*complete allocation ancestry'):
        materials.validate_cpu_window_identity(proof, **kwargs)
    # An old raw assertion of completeness stays data-readable, not authoritative.
    old_assertion = deepcopy(proof)
    old_assertion.update(state='complete', reason=None)
    assert materials.validate_cpu_window_identity(old_assertion, **kwargs, require_complete=False) is None
    with pytest.raises(ValueError, match='independent.*complete allocation ancestry'):
        materials.validate_cpu_window_identity(old_assertion, **kwargs)
    with pytest.raises(ValueError, match='original source/binding/window'):
        materials.validate_cpu_window_identity(proof, **{**kwargs, 'windows': [{'run_id': 'other', 'window_id': 'other'}]})
    moved = deepcopy(raw)
    moved['limits'][-1]['files']['cpu.max'] = '50000 100000\n'
    changed = materials.cpu_window_identity(request, 'screen', 'unprofiled', windows, snapshot(raw), snapshot(moved))
    assert changed['state'] == 'unsupported'
    with pytest.raises(ValueError, match='original CPU hardware/placement scope is unavailable'):
        materials.validate_cpu_window_identity(changed, **kwargs)
    assert materials.validate_cpu_window_identity(changed, **kwargs, require_complete=False) is None
    with pytest.raises(ValueError, match='original CPU hardware/placement window evidence is missing'):
        materials.validate_cpu_window_identity(None, **kwargs)


def test_f1_static_os_collection_is_inprocess_and_explicitly_scoped(monkeypatch):
    import ergora.training.materials as materials
    def no_subprocess(*args, **kwargs):
        raise AssertionError('Static CPU identity must not spawn a probe or measurement')
    monkeypatch.setattr(subprocess, 'Popen', no_subprocess)
    try:
        saved = materials.cpu_execution_identity()
    except ValueError as error:
        assert str(error).startswith('unsupported:')
    else:
        value = materials._read_cpu_execution_identity(saved)
        try:
            materials.validate_cpu_execution_identity(saved)
        except ValueError as error:
            assert str(error).startswith('unsupported:')
        assert value['placement']['affinity'] == sorted(os.sched_getaffinity(0))
        assert value['scope'] == 'linux-x86_64-visible-cgroup2-local-boot'


def test_f1_reuse_reads_each_original_window_proof_without_current_backfill(f1_cpu_snapshot, monkeypatch):
    from copy import deepcopy
    import ergora.training.materials as materials
    from ergora.training.runtime.evidence import cpu_reuse_identity
    raw, snapshot = f1_cpu_snapshot
    def live_read_forbidden():
        raise AssertionError('An original CPU proof reader must never backfill current host facts')
    monkeypatch.setattr(materials, 'cpu_execution_identity', live_read_forbidden)
    source = {'repo': '/original-source', 'commit': 'a' * 40, 'inventory_sha256': 'b' * 64, 'entrypoint': 'driver.py'}
    baseline, screen = {}, {}
    for phase, target in (('baseline', baseline), ('screen', screen)):
        request = {'binding': {'experiment_id': 'original-' + phase}, 'native_request_sha256': 'c' * 64,
            'managed': {'launch_sha256': phase + '-original-launch'}, 'execution_phase_id': phase + '-phase',
            'configuration_readback': {'source': source}}
        provenance = {'run_id': phase + '-unprofiled-run', 'window_id': phase + '-unprofiled-window',
                      'execution_phase_id': request['execution_phase_id']}
        selected = [{key: provenance[key] for key in ('run_id', 'window_id')}]
        original = materials.cpu_window_identity(request, phase, 'unprofiled', selected, snapshot(deepcopy(raw)), snapshot(deepcopy(raw)))
        owner = {key: request[key] for key in ('binding', 'native_request_sha256', 'managed')}
        owner['source'] = source
        profile_selection = {'phase': phase, 'run_id': phase + '-profile-run', 'window_id': phase + '-profile-window'}
        profile_proof = materials.cpu_window_identity(request, phase, 'profiled',
            [{key: profile_selection[key] for key in ('run_id', 'window_id')}], snapshot(deepcopy(raw)), snapshot(deepcopy(raw)))
        target['diagnostics'] = {'status': 'complete', 'raw': [{'capture': {
            'binding': request['binding'], 'managed': request['managed'], 'source': source, 'selection': profile_selection,
            'actual': {'hardware': {'cpu_execution': profile_proof}}}}]}
        if phase == 'baseline':
            owner.update(baseline={'cpu_execution': original}, measurement=[{'provenance': provenance}])
            target['reference'] = {'receipt': owner}
        else:
            owner.update(workload={'scope': {'cpu_execution': original}}, windows=[{'provenance': provenance}])
            target['result'] = owner
    with pytest.raises(ValueError, match='original typed CPU contract/acceptance'):
        cpu_reuse_identity(baseline, screen)
    moved = deepcopy(raw)
    moved['models'][0]['model name'] = 'Different original profile CPU'
    changed = deepcopy(screen)
    proof = changed['diagnostics']['raw'][0]['capture']['actual']['hardware']['cpu_execution']
    proof['before'] = snapshot(deepcopy(moved))
    proof['after'] = snapshot(deepcopy(moved))
    with pytest.raises(ValueError, match='original typed CPU contract/acceptance'):
        cpu_reuse_identity(baseline, changed)
    old_without_proof = deepcopy(baseline)
    del old_without_proof['reference']['receipt']['baseline']['cpu_execution']
    with pytest.raises(ValueError, match='original typed CPU contract/acceptance'):
        cpu_reuse_identity(old_without_proof, screen)


def test_f1_cpuset_only_namespace_does_not_authenticate_full_ancestry(f1_cpu_snapshot):
    from copy import deepcopy
    import ergora.training.materials as materials
    raw, snapshot = f1_cpu_snapshot
    cropped = deepcopy(raw)
    cropped['cgroup_membership'] = '0::/\n'
    cropped['cgroup_namespace'] = 'cgroup:[4026539999]'
    cropped['limits'] = [deepcopy(raw['limits'][0])]
    assert cropped['limits'][0]['files']['cpu.max'] is None
    assert cropped['limits'][0]['files']['cpu.weight'] is None
    assert cropped['limits'][0]['files']['cpuset.cpus.effective'] == '0-1\n'
    # A hidden parent's quota is absent from these namespace-relative facts.
    # File absence and syntactic namespace inode cannot prove a global root.
    with pytest.raises(ValueError, match='independent.*complete allocation ancestry'):
        materials.validate_cpu_execution_identity(snapshot(cropped))


@pytest.fixture
def positive_mock_fd_snapshot(f1_cpu_snapshot):
    """Mock recorded FD facts only, not a real qualified namespace/window."""
    import stat
    from copy import deepcopy
    import ergora.training.materials as m
    original, snapshot = f1_cpu_snapshot
    raw = deepcopy(original)
    # Saved Linux dev_t values: major zero, minors 25 (cgroup), 4 (nsfs), 5 (proc).
    def meta(fs, inode, mode, mount=27, device=None):
        return {'device': 25 if device is None else device, 'inode': inode,
                'mode': mode, 'filesystem': fs, 'mount_id': mount}
    root = meta(m._CGROUP2_MAGIC, 1, stat.S_IFDIR | 0o755)
    subject = {'pid': 100, 'tid': 101, 'start_ticks': 10, 'thread_start_ticks': 12,
               'parent_pid': 50, 'boot_id': raw['boot_id'].strip()}
    def subject_raw(value):
        def line(pid, ticks):
            fields = ['0'] * 20
            fields[0], fields[1], fields[19] = 'S', str(value['parent_pid']), str(ticks)
            return str(pid) + ' (pure-unit) ' + ' '.join(fields)
        return {'thread_stat': line(value['tid'], value['thread_start_ticks']),
                'leader_stat': line(value['pid'], value['start_ticks']),
                'thread_status': 'Tgid:\t' + str(value['pid']) + '\nPid:\t' + str(value['tid']) + '\n',
                'observed_pid': value['pid'], 'observed_tid': value['tid']}
    rows = []
    for index, item in enumerate(raw['limits']):
        files = {**item['files'], 'cgroup.controllers': 'cpu cpuset\n', 'cgroup.subtree_control': 'cpu cpuset\n', 'cgroup.type': 'domain\n' if index else None}
        rows.append({'relative': item['relative'], 'node': {**root, 'inode': index + 1}, 'files': files,
            'file_identities': {name: None if value is None else meta(m._CGROUP2_MAGIC, 1000 + index * 20 + ordinal, stat.S_IFREG | 0o644)
                                for ordinal, (name, value) in enumerate(files.items())}})
    target = meta(m._NSFS_MAGIC, m._INITIAL_CGROUP_INODE, stat.S_IFREG | 0o444, 2, 4)
    entry = meta(m._PROC_MAGIC, 5, stat.S_IFLNK | 0o777, 1, 5)
    proof = {'contract': m._CPU_KERNEL_CONTRACT, 'kernel': {'sysname': 'Linux', 'nodename': 'mock', 'release': '5.15-pure', 'version': '#pure', 'machine': 'x86_64'},
        'proc_root': meta(m._PROC_MAGIC, 1, stat.S_IFDIR | 0o555, 1, 5),
        'thread_directory': meta(m._PROC_MAGIC, 3, stat.S_IFDIR | 0o555, 1, 5),
        'leader_directory': meta(m._PROC_MAGIC, 2, stat.S_IFDIR | 0o555, 1, 5),
        'namespace_entry': entry, 'namespace_target': target, 'namespace_type': m._CGROUP_NS_TYPE,
        'namespace_link': 'cgroup:[' + str(m._INITIAL_CGROUP_INODE) + ']', 'subject': subject, 'subject_raw': subject_raw(subject),
        'membership': raw['cgroup_membership'], 'mountinfo': raw['cgroup_mount'], 'selected_mount': raw['cgroup_mount'],
        'root': root, 'ancestors': rows, 'subject_after': deepcopy(subject), 'subject_raw_after': subject_raw(subject),
        'membership_after': raw['cgroup_membership'], 'mountinfo_after': raw['cgroup_mount'],
        'namespace_target_after': deepcopy(target), 'namespace_entry_after': deepcopy(entry),
        'root_after': deepcopy(root), 'ancestors_after': deepcopy(rows)}
    contents = {'thread/stat': proof['subject_raw']['thread_stat'], 'thread/status': proof['subject_raw']['thread_status'],
        'leader/stat': proof['subject_raw']['leader_stat'], 'thread/cgroup': proof['membership'],
        'thread/mountinfo': proof['mountinfo'], 'proc/sys/kernel/random/boot_id': raw['boot_id']}
    proof['proc_files'] = {key: [{'identity': meta(m._PROC_MAGIC, 50 + index, stat.S_IFREG | 0o444, 1, 5),
        'sha256': hashlib.sha256(value.encode()).hexdigest(), 'bytes': len(value.encode())} for _ in range(2)]
        for index, (key, value) in enumerate(contents.items())}
    raw['allocation_provenance'] = proof
    return raw, snapshot, subject_raw


def test_positive_mock_fd_proof_excludes_pid_provenance_from_stable_identity(positive_mock_fd_snapshot):
    from copy import deepcopy
    import ergora.training.materials as m
    raw, snapshot, subject_raw = positive_mock_fd_snapshot
    first = snapshot(deepcopy(raw))
    changed = deepcopy(raw)
    subject = {**changed['allocation_provenance']['subject'], 'pid': 200, 'tid': 201, 'start_ticks': 30, 'thread_start_ticks': 31}
    proof = changed['allocation_provenance']
    proof.update(subject=subject, subject_after=deepcopy(subject), subject_raw=subject_raw(subject), subject_raw_after=subject_raw(subject))
    for route, key in (('thread/stat', 'thread_stat'), ('thread/status', 'thread_status'), ('leader/stat', 'leader_stat')):
        encoded = proof['subject_raw'][key].encode()
        for record in proof['proc_files'][route]:
            record.update(sha256=hashlib.sha256(encoded).hexdigest(), bytes=len(encoded))
    second = snapshot(changed)
    assert first['raw_sha256'] != second['raw_sha256']
    assert m.validate_cpu_execution_identity(first) == m.validate_cpu_execution_identity(second)


def test_positive_initial_root_omits_nonroot_cgroup_type(positive_mock_fd_snapshot):
    from copy import deepcopy
    import ergora.training.materials as m
    raw, snapshot, _ = positive_mock_fd_snapshot
    raw = deepcopy(raw)
    for key in ('ancestors', 'ancestors_after'):
        raw['allocation_provenance'][key][0]['files']['cgroup.type'] = None
        raw['allocation_provenance'][key][0]['file_identities']['cgroup.type'] = None
    assert m.validate_cpu_execution_identity(snapshot(raw))['allocation_objects'][0]['relative'] == '/'


def test_positive_saved_linux_device_numbers_preserve_mount_binding_and_bounds(positive_mock_fd_snapshot):
    import ergora.training.materials as m
    original, snapshot, _ = positive_mock_fd_snapshot
    def saved(device, numbers):
        raw = deepcopy(original)
        proof = raw['allocation_provenance']
        for key in ('root', 'root_after'):
            proof[key]['device'] = device
        for key in ('ancestors', 'ancestors_after'):
            for row in proof[key]:
                row['node']['device'] = device
                for identity in row['file_identities'].values():
                    if identity is not None:
                        identity['device'] = device
        mount = raw['cgroup_mount'].replace('0:25', numbers)
        raw['cgroup_mount'] = mount
        for key in ('selected_mount', 'mountinfo', 'mountinfo_after'):
            proof[key] = mount
        for record in proof['proc_files']['thread/mountinfo']:
            record.update(sha256=hashlib.sha256(mount.encode()).hexdigest(), bytes=len(mount.encode()))
        return raw
    # Original Linux helper results, including each UINT32_MAX sentinel; no host helper is required.
    for device, numbers in ((17592187092992, '4096:256'), (18446726481524555520, '-1:0'),
                            (17592184996095, '0:-1'), (18446744073709551615, '-1:-1')):
        observed = m.validate_cpu_execution_identity(snapshot(saved(device, numbers)))
        assert all(item['device'] == device for item in observed['allocation_objects'])
        different = numbers.replace('-1', '4294967295') if '-1' in numbers else '4096:257'
        with pytest.raises(ValueError, match='opened root differs'):
            m.validate_cpu_execution_identity(snapshot(saved(device, different)))
    for device in (True, -1, 25.0, '25'):
        with pytest.raises(ValueError, match='FD filesystem/type identity'):
            m.validate_cpu_execution_identity(snapshot(saved(device, '0:25')))
    overflow = saved(1 << 64, '0:25')
    assert m._validate_cpu_fd_provenance(overflow['allocation_provenance'], overflow, require_complete=False)
    with pytest.raises(OverflowError, match='int too big to convert'):
        m.validate_cpu_execution_identity(snapshot(overflow))


@pytest.mark.parametrize('corruption', ['noninitial', 'wrong-proc', 'wrong-ioctl', 'overmount', 'persistent-path-object', 'subject'])
def test_positive_mock_fd_reader_refuses_incomplete_or_wrong_subject_facts(positive_mock_fd_snapshot, corruption):
    from copy import deepcopy
    import ergora.training.materials as m
    raw, snapshot, _ = positive_mock_fd_snapshot
    raw = deepcopy(raw)
    proof = raw['allocation_provenance']
    if corruption == 'noninitial':
        proof['namespace_target']['inode'] = proof['namespace_target_after']['inode'] = 4026549999
        proof['namespace_link'] = 'cgroup:[4026549999]'
        raw['cgroup_namespace'] = proof['namespace_link']
    elif corruption == 'wrong-proc':
        proof['namespace_entry']['mount_id'] += 1
    elif corruption == 'wrong-ioctl':
        proof['namespace_type'] = 0x20000
    elif corruption == 'overmount':
        proof['ancestors'][-1]['node']['mount_id'] += 1
        proof['ancestors_after'] = deepcopy(proof['ancestors'])
    elif corruption == 'persistent-path-object':
        proof['ancestors_after'][-1]['node']['inode'] += 1
    else:
        proof['subject_raw']['observed_tid'] += 1
    with pytest.raises(ValueError):
        m.validate_cpu_execution_identity(snapshot(raw))


@pytest.mark.parametrize('change', ['replaced-allocation', 'missing-after-proof'])
def test_positive_window_qualifies_both_original_endpoints(positive_mock_fd_snapshot, change):
    from copy import deepcopy
    import ergora.training.materials as m
    raw, snapshot, _ = positive_mock_fd_snapshot
    before = snapshot(deepcopy(raw))
    moved = deepcopy(raw)
    if change == 'replaced-allocation':
        for key in ('ancestors', 'ancestors_after'):
            moved['allocation_provenance'][key][-1]['node']['inode'] += 1
    else:
        del moved['allocation_provenance']
    after = snapshot(moved)
    request = {'binding': {'experiment_id': 'mock-original'}, 'native_request_sha256': 'a' * 64,
        'managed': {'attempt_sha256': 'b' * 64}, 'execution_phase_id': 'original-phase',
        'configuration_readback': {'source': {'repo': '/original', 'commit': 'c' * 40}}}
    windows = [{'run_id': 'original-run', 'window_id': 'original-window'}]
    value = m.cpu_window_identity(request, 'baseline', 'unprofiled', windows, before, after)
    assert value['state'] == 'unsupported'
    kwargs = {key: request[key] for key in ('binding', 'native_request_sha256', 'managed', 'execution_phase_id')}
    kwargs.update(source=request['configuration_readback']['source'], phase='baseline', operation='unprofiled', windows=windows)
    # A saved record cannot bypass the strict second endpoint by claiming complete.
    value.update(state='complete', reason=None)
    with pytest.raises(ValueError, match='allocation objects changed|complete allocation ancestry'):
        m.validate_cpu_window_identity(value, **kwargs)


@pytest.mark.skipif(sys.platform != 'linux', reason='Current cgroup path reopening uses Linux O_DIRECTORY/O_NOFOLLOW')
def test_positive_endpoint_reopens_current_path_instead_of_pinned_old_nodes():
    """Pure fake kernfs: same membership text, deleted old leaf held open, new leaf."""
    import stat
    import ergora.training.materials as m
    current = {'/': 1, '/job': 2, '/job/worker': 3}
    opened_paths = []
    def opened(path, flags, parent=None):
        selected = '/' if parent is None else (Path(parent['path']) / path).as_posix()
        opened_paths.append(selected)
        return {'path': selected, 'inode': current[selected]}
    def metadata(node):
        return {'device': 25, 'inode': node['inode'], 'mode': stat.S_IFDIR | 0o755,
                'filesystem': m._CGROUP2_MAGIC, 'mount_id': 27}
    def control(node, name):
        return None, None
    before_root, before = m._cpu_endpoint_ancestry('/cg', '/job/worker', opened=opened, metadata=metadata, control=control)
    pinned_old_leaf = {'path': '/job/worker', 'inode': 3}
    current['/job/worker'] = 4
    after_root, after = m._cpu_endpoint_ancestry('/cg', '/job/worker', opened=opened, metadata=metadata, control=control)
    assert before_root == after_root and before[-1]['relative'] == after[-1]['relative']
    assert metadata(pinned_old_leaf)['inode'] == before[-1]['node']['inode'] == 3
    assert after[-1]['node']['inode'] == 4 and before != after
    assert opened_paths.count('/') == 2


@pytest.mark.parametrize('overmount', ['cgroup', 'mountinfo', 'stat', 'status', 'leader-stat', 'fdinfo', 'statx-error', 'statx-missing-mask'])
@pytest.mark.skipif(sys.platform != 'linux', reason='Original proc FD mount probes use Linux fcntl/nsfs/statx')
def test_positive_proc_files_bind_actual_kernel_mount_before_read(monkeypatch, overmount):
    """Pure genuine-proc bind-mount model; forged fdinfo cannot bless another file."""
    import ctypes
    import fcntl
    import stat
    import threading
    from types import SimpleNamespace
    import ergora.training.materials as m
    entries, positions, next_fd = {}, {}, [10]
    proc_dev, group_dev = os.makedev(0, 5), os.makedev(0, 25)
    def stat_line(pid, ticks):
        fields = ['0'] * 20
        fields[0], fields[1], fields[19] = 'S', '50', str(ticks)
        return str(pid) + ' (unit) ' + ' '.join(fields)
    text = {'/proc/thread-self/stat': stat_line(101, 12), '/proc/self/stat': stat_line(100, 10),
        '/proc/thread-self/status': 'Tgid:\t100\nPid:\t101\n', '/proc/thread-self/cgroup': '0::/work\n',
        '/proc/thread-self/mountinfo': '27 1 0:25 / /fake-cgroup rw - cgroup2 cgroup rw\n',
        '/proc/sys/kernel/random/boot_id': '12345678-1234-1234-1234-123456789abc\n'}
    selected = '/proc/self/stat' if overmount == 'leader-stat' else '/proc/thread-self/' + overmount
    def opened(path, flags, *, dir_fd=None):
        key = str(path) if dir_fd is None else entries[dir_fd]['path'] + '/' + str(path)
        fs, mount, device, mode = m._PROC_MAGIC, 1, proc_dev, stat.S_IFREG | 0o444
        content = text.get(key, '')
        if key in ('/proc', '/proc/self', '/proc/thread-self', '/proc/thread-self/ns'):
            mode = stat.S_IFDIR | 0o555
        elif key == '/proc/thread-self/ns/cgroup':
            if flags & os.O_NOFOLLOW:
                mode = stat.S_IFLNK | 0o777
            else:
                fs, mount, device = m._NSFS_MAGIC, 2, os.makedev(0, 4)
        elif '/fdinfo/' in key:
            target = entries[int(key.rsplit('/', 1)[1])]
            content = 'mnt_id:\t' + str(1 if target['path'] == selected else target['mount']) + '\n'
            if overmount == 'fdinfo': mount = 9
        elif key.startswith('/fake-cgroup'):
            fs, mount, device = m._CGROUP2_MAGIC, 27, group_dev
            if key in ('/fake-cgroup', '/fake-cgroup/work'):
                mode = stat.S_IFDIR | 0o755
            else:
                name = key.rsplit('/', 1)[1]
                values = {'cgroup.controllers': 'cpu cpuset\n', 'cgroup.subtree_control': 'cpu cpuset\n',
                    'cgroup.type': 'domain\n', 'cpu.max': 'max 100000\n', 'cpu.weight': '100\n',
                    'cpuset.cpus.effective': '0-1\n', 'cpuset.mems.effective': '0\n'}
                if name not in values: raise FileNotFoundError(key)
                content = values[name]
        if key == selected: mount = 9
        fd = next_fd[0]; next_fd[0] += 1
        entries[fd] = {'path': key, 'fs': fs, 'mount': mount, 'dev': device, 'mode': mode,
            'inode': m._INITIAL_CGROUP_INODE if fs == m._NSFS_MAGIC else abs(hash(key)) % 100000 + 1,
            'content': content.encode()}
        return fd
    def read(fd, size):
        position = positions.get(fd, 0); positions[fd] = position + size
        return entries[fd]['content'][position:position + size]
    class Call:
        def __init__(self, function): self.function = function
        def __call__(self, *args): return self.function(*args)
    def fstatfs(fd, buffer):
        ctypes.c_long.from_buffer(buffer).value = entries[fd]['fs']
        return 0
    def syscall(number, fd, path, flags, mask, buffer):
        assert number.value == 332 and path.value == b''
        if overmount == 'statx-error':
            ctypes.set_errno(38)
            return -1
        target = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte * 256)).contents
        ctypes.c_uint32.from_buffer(target).value = 0 if overmount == 'statx-missing-mask' else 0x1000
        ctypes.c_uint64.from_buffer(target, 0x90).value = entries[fd.value]['mount']
        return 0
    libc = SimpleNamespace(fstatfs=Call(fstatfs), syscall=Call(syscall))
    monkeypatch.setattr(ctypes, 'CDLL', lambda *a, **kw: libc)
    monkeypatch.setattr(m.os, 'open', opened)
    monkeypatch.setattr(m.os, 'close', lambda fd: None)
    monkeypatch.setattr(m.os, 'read', read)
    original_fstat = m.os.fstat
    monkeypatch.setattr(m.os, 'fstat', lambda fd: SimpleNamespace(st_dev=entries[fd]['dev'], st_ino=entries[fd]['inode'], st_mode=entries[fd]['mode']) if fd in entries else original_fstat(fd))
    monkeypatch.setattr(m.os, 'readlink', lambda *a, **kw: 'cgroup:[' + str(m._INITIAL_CGROUP_INODE) + ']')
    monkeypatch.setattr(m.os, 'getpid', lambda: 100)
    monkeypatch.setattr(threading, 'get_native_id', lambda: 101)
    monkeypatch.setattr(fcntl, 'ioctl', lambda *a: m._CGROUP_NS_TYPE)
    if overmount == 'fdinfo':
        # The fixed observer must not consult any fdinfo path at all.
        with m._cpu_fd_scope() as (proof, finish):
            finish()
        assert not any('/fdinfo/' in value['path'] for value in entries.values())
    else:
        with pytest.raises(ValueError, match='proc.*mount|proc.*overmount|statx'):
            with m._cpu_fd_scope(): pass
