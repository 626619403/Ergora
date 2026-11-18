"""Saved training evidence, selected content and local tickets are distinct facts."""

from contextlib import redirect_stdout
import hashlib
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
    with pytest.raises(ValueError, match='size limit|capacity'):
        training.evidence(state, 'demo', 'alpha', artifact='notes.txt', evidence_sha256=report['evidence_sha256'])


@pytest.mark.parametrize('selected_installation', ('missing', 'descriptor-mismatch'))
def test_public_reference_inventory_runs_without_site_packages_or_selected_native_installation(
        archive, monkeypatch, selected_installation):
    state, definition, runtime, _, _, folder, report = archive
    native = Path(definition['execution']['installation'])
    descriptor = native / 'ergora-native-runtime.json'
    original_descriptor = descriptor.read_bytes()
    moved = native.with_name(native.name + '-temporarily-unavailable')
    before = {path: path.read_bytes() for path in runtime.rglob('*') if path.is_file()}
    original_run = reference.subprocess.run
    calls = []
    guard = '''import sys
class DenyApplicationImports:
    def find_spec(self, fullname, *args):
        if fullname in ('ergora.state', 'jsonschema', 'temporalio') or fullname.startswith(('jsonschema.', 'temporalio.')):
            raise AssertionError('Forbidden reader import: ' + fullname)
sys.meta_path.insert(0, DenyApplicationImports())
'''
    def guarded(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.reference_training_evidence import main;main()':
            assert '-S' in argv and '-P' in argv
            calls.append(json.loads(kwargs['input'])['operation'])
            argv = [*argv[:-1], guard + argv[-1]]
        return original_run(argv, *args, **kwargs)
    monkeypatch.setattr(reference.subprocess, 'run', guarded)
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
        assert calls == ['inspect', 'baseline-reference']
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


def test_inventory_keeps_the_first_file_identity_across_repeated_reads(tmp_path):
    from ergora.reference_training_evidence import _Inventory

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
    from ergora import reference_training_evidence as evidence, training_execution_protocol as protocol

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
    original_run = reference.subprocess.run
    program = f'''import json
from pathlib import Path
from ergora import reference_training_evidence as evidence
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
        if argv[-1] == 'from ergora.reference_training_evidence import main;main()':
            argv = [*argv[:-1], program + argv[-1]]
        return original_run(argv, *args, **kwargs)
    monkeypatch.setattr(reference.subprocess, 'run', invoke)
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
        target = Path(definition['execution']['config_directory']) / reference.registration_paths('demo')[0]
    else:
        target = runtime / 'training/fences/alpha.json'
    original_raw = target.read_bytes() if target.exists() else None
    marker = tmp_path / 'actual-reference-guard-change.json'
    program = f'''import hashlib,json
from pathlib import Path
from ergora import reference_training_evidence as evidence
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
    original_run = reference.subprocess.run
    def inject(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.reference_training_evidence import main;main()':
            assert '-S' in argv and '-P' in argv
            argv = [*argv[:-1], program + argv[-1]]
        return original_run(argv, *args, **kwargs)
    monkeypatch.setattr(reference.subprocess, 'run', inject)
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


def test_reference_is_independent_of_mutable_heads_and_registration_formatting(archive, monkeypatch):
    state, definition, runtime, prefix, write, folder, report = archive
    saved = training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256'])
    head = prefix / 'baseline.json'
    config = Path(definition['execution']['config_directory'])
    guard = config / reference.registration_paths('demo')[0]
    head_raw, guard_raw = head.read_bytes(), guard.read_bytes()
    try:
        write(head, {**json.loads(head_raw), 'baseline_id': 'different-current-head'})
        guard.write_bytes(guard_raw + b'\n')
        assert training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256']) == saved
        ignored = [head, config / 'training-runners/trusted.json',
                   runtime / ('training/integration-tickets/alpha-' + report['evidence_sha256'][:16] + '.json'),
                   runtime / 'training/negative-results/alpha.json']
        program = f'''from pathlib import Path
from ergora import training_materials as materials,training_execution_protocol as protocol
ignored={{Path(value) for value in {[str(path) for path in ignored]!r}}}
original_raw,original_fd=materials.read_raw,protocol._fd
def checked_raw(path,*args,**kwargs):
    assert Path(path) not in ignored,'unrelated mutable reference read: '+str(path)
    return original_raw(path,*args,**kwargs)
def checked_fd(path,*args,**kwargs):
    assert Path(path) not in ignored,'unrelated mutable reference read: '+str(path)
    return original_fd(path,*args,**kwargs)
materials.read_raw=checked_raw
protocol._fd=checked_fd
'''
        original_run = reference.subprocess.run
        def inject(argv, *args, **kwargs):
            if argv[-1] == 'from ergora.reference_training_evidence import main;main()':
                argv = [*argv[:-1], program + argv[-1]]
            return original_run(argv, *args, **kwargs)
        monkeypatch.setattr(reference.subprocess, 'run', inject)
        assert training.baseline_reference(state, 'demo', 'alpha', evidence_sha256=report['evidence_sha256']) == saved
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
    from ergora.reference_training_evidence import _resource_coverage

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


def test_round_content_validates_original_bindings_without_site_packages(experiments, tmp_path):
    from ergora import training_rounds

    created = training_rounds.create(experiments[0], 'demo', {'schema_version': 1, 'rounds': [{
        'experiment_id': 'alpha', 'change': '保留原始观察 🌱',
        'next_bottleneck': 'No measured optimization claim'}]}, tmp_path / 'index')
    isolated = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', '''import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from ergora.training_execution_protocol import encode_round_content,round_content_sha,validate_round_content
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
assert not any(name in sys.modules for name in ('yaml','jsonschema','temporalio','dev_platform','ergora.state','ergora.training'))
''', str(Path(reference.__file__).parent.parent), str(tmp_path / 'index/rounds.json'), created['sha256']],
        capture_output=True, text=True, encoding='utf-8', timeout=10)
    assert isolated.returncode == 0, isolated.stderr
