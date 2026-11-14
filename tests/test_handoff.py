"""Portable packets prove bytes and declared links, without an execution service."""

from copy import deepcopy
import hashlib
import json
import os
import stat
import subprocess
import sys
import zipfile

import pytest

from ergora import cli, handoff


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


@pytest.fixture
def evidence():
    binary = b'\x00\xff\x80\nportable bytes'
    digest = hashlib.sha256(binary).hexdigest()
    request = {'task_id': 'task-one', 'goal': '复查材料'}
    profile = {'limits': {'max_parallel_units': 2}}
    spec = {'request': request, 'profile': profile, 'request_sha256': sha(request), 'profile_sha256': sha(profile)}
    receipt = {'schema_version': 1, 'job_id': 'job-one', 'job_sha256': 'b' * 64, 'state': 'SUCCEEDED',
        'actor': {'id': 'reviewer', 'session_id': 'session-one', 'role': 'verifier', 'kind': 'ci'},
        'candidate_sha': 'a' * 40, 'artifacts': [
            {'name': 'record', 'path': 'task-one/result.bin', 'sha256': digest},
            {'name': 'same-bytes', 'path': 'task-one/copy.bin', 'sha256': digest}],
        'checks': [{'id': 'check-one', 'status': 'pass', 'artifact': 'record'}]}
    outcome = {'status': 'REVIEW_READY', 'task_id': 'task-one', 'request_sha256': spec['request_sha256'],
               'candidate_sha': 'a' * 40, 'verification': deepcopy(receipt)}
    index = {'schema_version': 1, 'project': 'demo', 'task_id': 'task-one', 'workflow_id': 'dev-task/task-one',
        'run_id': 'original-run', 'read_only': True, 'terminal': True, 'temporal_status': 'COMPLETED',
        'lease_released_by_operation': False, 'execution_success': None, 'published_evidence': 'verified',
        'unresolved_jobs': [], 'unexpected_jobs': [], 'request_sha256': spec['request_sha256'],
        'profile_sha256': spec['profile_sha256'],
        'history_jobs_sha256': sha([{'job_id': 'job-one', 'job_sha256': 'b' * 64}]),
        'contract': {'spec': spec, 'spec_sha256': sha(spec), 'creation_sha256': 'c' * 64,
                     'submission_sha256': 'd' * 64, 'agent_bindings': {'reviewer': 'codex'},
                     'agent_bindings_sha256': sha({'reviewer': 'codex'})},
        'original_outcome': outcome, 'original_outcome_sha256': sha(outcome),
        'jobs': [{'job_id': 'job-one', 'job_sha256': 'b' * 64, 'stage': 'verify', 'request_state': 'matches',
                  'receipt_state': 'SUCCEEDED', 'receipt_sha256': sha(receipt), 'receipt': receipt,
                  'history_event_ids': [2, 9], 'outcome_reference_state': 'matches'}],
        'usage': {'cost': {'state': 'not_recorded', 'value': None}}}
    return index, binary


def collect(evidence, tmp_path):
    index, binary = evidence
    path = tmp_path / 'handoff.zip'
    result = handoff.create(index, lambda artifact: binary, path)
    return path, result


def rewrite(path, change):
    with zipfile.ZipFile(path) as archive:
        members = [(entry, archive.read(entry)) for entry in archive.infolist()]
    members = change(members)
    with zipfile.ZipFile(path, 'w') as archive:
        for entry, raw in members:
            archive.writestr(entry, raw)


def change_manifest(path, change):
    def update(members):
        result = []
        for entry, raw in members:
            if entry.filename == 'manifest.json':
                manifest = json.loads(raw)
                change(manifest)
                raw = canonical(manifest)
            result.append((entry, raw))
        return result
    rewrite(path, update)


@pytest.mark.parametrize('outcome', ['normal', 'cancelled', 'failed', 'optional-checks'])
def test_roundtrip_preserves_bytes_original_result_and_limited_proof(evidence, tmp_path, outcome):
    index, binary = evidence
    if outcome == 'cancelled':
        index['original_outcome']['status'] = 'CANCEL_UNCONFIRMED'
    elif outcome == 'failed':
        index.update(temporal_status='FAILED', original_outcome=None)
        index['jobs'][0]['outcome_reference_state'] = 'not_recorded'
    elif outcome == 'optional-checks':
        receipt = index['jobs'][0]['receipt']
        receipt.pop('checks')
        index['jobs'][0]['receipt_sha256'] = sha(receipt)
        index['original_outcome']['verification'] = deepcopy(receipt)
    index['original_outcome_sha256'] = sha(index['original_outcome']) if index['original_outcome'] else None
    before = deepcopy(index)
    reads = []
    path = tmp_path / 'handoff.zip'
    result = handoff.create(index, lambda artifact: (reads.append(artifact) or binary), path)
    verified = handoff.verify(path, sha256=result['sha256'])
    assert index == before and len(reads) == 1
    assert verified['status'] == 'verified' and verified['external_sha256'] == 'matches'
    assert verified['execution_success'] is None and verified['origin_authenticated'] is False
    assert verified['original_outcome'] == index['original_outcome']
    assert verified['artifacts'] == 1 and verified['artifact_bytes'] == len(binary)
    assert verified['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        assert set(archive.namelist()) == {'manifest.json', 'blobs/' + hashlib.sha256(binary).hexdigest()}
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['index'] == index and manifest['index_sha256'] == sha(index)
        assert archive.read('blobs/' + hashlib.sha256(binary).hexdigest()) == binary
    selected = handoff.evidence(path, sha256=result['sha256'])
    assert selected['index'] == index and selected['artifacts'] == []
    assert selected['execution_success'] is None and selected['origin_authenticated'] is False


def text_evidence(evidence, texts):
    index, _ = evidence
    original = index['jobs'][0]
    blobs = {}
    for number, text in enumerate(texts, 1):
        raw = text if isinstance(text, bytes) else text.encode('utf-8')
        digest = hashlib.sha256(raw).hexdigest()
        blobs[digest] = raw
        job = deepcopy(original)
        job.update(job_id=f'job-{number}', job_sha256=str(number) * 64,
                   outcome_reference_state='not_recorded')
        job['receipt'].update(job_id=job['job_id'], job_sha256=job['job_sha256'], state='FAILED', artifacts=[
            {'name': 'record', 'path': f'task-one/{number}.txt', 'sha256': digest}])
        job['receipt']['checks'] = [{'id': 'check-one', 'status': 'fail', 'artifact': 'record'}]
        job.update(receipt_state='FAILED', receipt_sha256=sha(job['receipt']))
        if number == 1:
            index['jobs'] = []
        index['jobs'].append(job)
    index.update(temporal_status='FAILED', original_outcome=None, original_outcome_sha256=None)
    index['history_jobs_sha256'] = sha([{'job_id': job['job_id'], 'job_sha256': job['job_sha256']}
                                      for job in index['jobs']])
    return index, blobs


def test_selected_text_keeps_exact_job_receipt_full_body_and_negative_evidence(evidence, tmp_path, monkeypatch, capsys):
    texts = ['完整负结果与原成本未知。\n' * 800, 'Distinct job, same artifact name.\n']
    index, blobs = text_evidence(evidence, texts)
    path = tmp_path / 'text.zip'
    collected = handoff.create(index, lambda artifact: blobs[artifact['sha256']], path)
    selection = [{'job_id': 'job-2', 'name': 'record'}, {'job_id': 'job-1', 'name': 'record'}]
    response = handoff.evidence(path, selection, sha256=collected['sha256'])
    assert response['index'] == index and response['index']['usage']['cost']['state'] == 'not_recorded'
    assert response['execution_success'] is None and response['origin_authenticated'] is False
    assert response['packet_sha256'] == collected['sha256'] and response['index_sha256'] == sha(index)
    assert response['sha256'] == sha({key: value for key, value in response.items() if key != 'sha256'})
    for selected, number in zip(response['artifacts'], (2, 1)):
        job = index['jobs'][number - 1]
        assert selected['job_id'] == job['job_id'] and selected['job_sha256'] == job['job_sha256']
        assert selected['receipt_sha256'] == job['receipt_sha256']
        assert selected['artifact'] == job['receipt']['artifacts'][0]
        assert selected['text'] == texts[number - 1] and selected['bytes'] == len(texts[number - 1].encode())
    selected_file = tmp_path / 'selection.json'
    selected_file.write_text(json.dumps(selection))
    def forbidden(*args, **kwargs):
        raise AssertionError('Offline evidence reading cannot initialize State')
    monkeypatch.setattr(cli, 'State', forbidden)
    root = tmp_path / 'unused-state'
    assert cli.main(['--home', str(root), 'handoff', 'read', str(path), '--selection', str(selected_file),
                     '--sha256', collected['sha256']]) == 0
    assert json.loads(capsys.readouterr().out) == response and not root.exists()


def test_evidence_reader_uses_verified_bytes_when_original_path_changes(evidence, tmp_path, monkeypatch):
    index, blobs = text_evidence(evidence, ['Original complete evidence.'])
    path = tmp_path / 'text.zip'
    collected = handoff.create(index, lambda artifact: blobs[artifact['sha256']], path)
    original = handoff._verified_packet
    def replace_after_verification(*args, **kwargs):
        packet = original(*args, **kwargs)
        path.write_bytes(b'Replaced after the verified read')
        return packet
    monkeypatch.setattr(handoff, '_verified_packet', replace_after_verification)
    response = handoff.evidence(path, [{'job_id': 'job-1', 'name': 'record'}], sha256=collected['sha256'])
    assert response['artifacts'][0]['text'] == 'Original complete evidence.'
    assert response['packet_sha256'] == collected['sha256']
    assert hashlib.sha256(path.read_bytes()).hexdigest() != response['packet_sha256']


def test_aliases_cannot_amplify_text_before_the_selection_size_check(evidence, tmp_path, monkeypatch):
    body = 'Complete source bytes. ' * 14000
    index, blobs = text_evidence(evidence, [body])
    job = index['jobs'][0]
    artifact = job['receipt']['artifacts'][0]
    job['receipt']['artifacts'] = [{**artifact, 'name': f'record-{number}'} for number in range(32)]
    job['receipt']['checks'][0]['artifact'] = 'record-0'
    job['receipt_sha256'] = sha(job['receipt'])
    path = tmp_path / 'aliases.zip'
    handoff.create(index, lambda item: blobs[item['sha256']], path)
    original = handoff.zipfile.ZipFile.read
    reads = []
    allowance = handoff.MANIFEST_LIMIT // len(body.encode())
    def bounded_read(archive, name, *args, **kwargs):
        filename = name.filename if isinstance(name, zipfile.ZipInfo) else name
        if filename.startswith('blobs/'):
            reads.append(filename)
            # One full verifier read, followed only by bodies within the budget.
            if len(reads) > 1 + allowance:
                raise AssertionError('Over-budget alias body was read before rejection')
        return original(archive, name, *args, **kwargs)
    monkeypatch.setattr(handoff.zipfile.ZipFile, 'read', bounded_read)
    with pytest.raises(ValueError, match='Complete handoff selection exceeds'):
        handoff.evidence(path, [{'job_id': job['job_id'], 'name': item['name']} for item in job['receipt']['artifacts']])
    assert len(reads) <= 1 + allowance


@pytest.mark.parametrize('body', [b'\xff\x80', b'embedded\0text', '完整资料' * 100_000])
def test_unreadable_or_over_capacity_evidence_does_not_emit_partial_output(evidence, tmp_path, body, capsys):
    index, blobs = text_evidence(evidence, ['First complete artifact.', body])
    path = tmp_path / 'text.zip'
    handoff.create(index, lambda artifact: blobs[artifact['sha256']], path)
    selected_file = tmp_path / 'selection.json'
    selected_file.write_text(json.dumps([{'job_id': f'job-{number}', 'name': 'record'} for number in (1, 2)]))
    assert cli.main(['handoff', 'read', str(path), '--selection', str(selected_file)]) == 2
    captured = capsys.readouterr()
    assert captured.out == '' and 'handoff' in captured.err.lower()


@pytest.mark.parametrize('change', ['incomplete', 'contract', 'request', 'outcome', 'receipt', 'history',
                                  'reference', 'duplicate-job', 'unsafe-path', 'check'])
def test_inconsistent_declared_links_cannot_be_collected(evidence, tmp_path, change):
    index, binary = evidence
    if change == 'incomplete': index['published_evidence'] = 'incomplete'
    elif change == 'contract': index['contract']['spec']['profile']['limits']['max_parallel_units'] = 3
    elif change == 'request': index['request_sha256'] = 'e' * 64
    elif change == 'outcome': index['original_outcome']['task_id'] = 'other-task'
    elif change == 'receipt': index['jobs'][0]['receipt']['candidate_sha'] = 'e' * 40
    elif change == 'history': index['history_jobs_sha256'] = 'e' * 64
    elif change == 'reference': index['jobs'][0]['outcome_reference_state'] = 'not_recorded'
    elif change == 'duplicate-job': index['jobs'].append(deepcopy(index['jobs'][0]))
    else:
        receipt = index['jobs'][0]['receipt']
        if change == 'unsafe-path': receipt['artifacts'][0]['path'] = '../outside'
        else: receipt['checks'][0]['artifact'] = 'missing'
        index['jobs'][0]['receipt_sha256'] = sha(receipt)
        index['jobs'][0]['outcome_reference_state'] = 'differs'
    with pytest.raises(ValueError):
        handoff.create(index, lambda artifact: binary, tmp_path / 'bad.zip')
    assert list(tmp_path.iterdir()) == []


def test_create_only_publication_and_failure_cleanup(evidence, tmp_path):
    index, binary = evidence
    destination = tmp_path / 'existing.zip'
    destination.write_bytes(b'original')
    with pytest.raises(ValueError, match='existing destinations'):
        handoff.create(index, lambda artifact: binary, destination)
    assert destination.read_bytes() == b'original'
    destination.unlink()
    with pytest.raises(ValueError, match='artifact bytes'):
        handoff.create(index, lambda artifact: b'changed', destination)
    assert list(tmp_path.iterdir()) == []

    def racing_reader(artifact):
        destination.write_bytes(b'concurrent file')
        return binary
    with pytest.raises(FileExistsError):
        handoff.create(index, racing_reader, destination)
    assert destination.read_bytes() == b'concurrent file' and list(tmp_path.iterdir()) == [destination]


@pytest.mark.parametrize('changed', ['stage', 'job_id', 'job_sha256', 'receipt_sha256'])
def test_parallel_review_receipts_keep_their_own_original_outcome_references(evidence, tmp_path, changed):
    index, binary = evidence
    aggregate = {'schema_version': 1, 'kind': 'composition-review-aggregate', 'decision': 'approve',
                 'candidate_sha': 'a' * 40, 'admission_sha256': 'e' * 64, 'review_instance': 'root', 'members': {}}
    for number, path in enumerate(('root/structure/review', 'root/correctness/review'), 2):
        job = deepcopy(index['jobs'][0])
        receipt = job['receipt']
        job.update(job_id='job-' + str(number), job_sha256=str(number) * 64, stage='review:' + path)
        receipt.update(job_id=job['job_id'], job_sha256=job['job_sha256'])
        receipt['actor'].update(kind='agent', role='reviewer', session_id='review-' + str(number))
        job['receipt_sha256'] = sha(receipt)
        index['jobs'].append(job)
        aggregate['members'][path] = {'stage': job['stage'], 'job_id': job['job_id'],
            'job_sha256': job['job_sha256'], 'receipt_sha256': job['receipt_sha256']}
    index['original_outcome']['review'] = aggregate
    index['original_outcome_sha256'] = sha(index['original_outcome'])
    index['history_jobs_sha256'] = sha([{'job_id': job['job_id'], 'job_sha256': job['job_sha256']}
                                       for job in sorted(index['jobs'], key=lambda item: item['job_id'])])
    result = handoff.create(index, lambda artifact: binary, tmp_path / 'parallel.zip')
    assert handoff.verify(tmp_path / 'parallel.zip', sha256=result['sha256'])['original_outcome']['review'] == aggregate
    aggregate['members']['root/structure/review'][changed] = 'f' * 64
    index['original_outcome_sha256'] = sha(index['original_outcome'])
    with pytest.raises(ValueError, match='outcome receipt reference'):
        handoff.create(index, lambda artifact: binary, tmp_path / 'changed.zip')


@pytest.mark.parametrize('kind', ['bytes', 'missing', 'extra', 'duplicate', 'compression', 'symlink', 'directory'])
def test_archive_mutations_fail_without_extracting(evidence, tmp_path, kind):
    path, _ = collect(evidence, tmp_path)
    def mutate(members):
        entry, raw = members[0]
        if kind == 'bytes': members[0] = (entry, b'corrupt')
        elif kind == 'missing': members.pop(0)
        elif kind == 'extra': members.append((zipfile.ZipInfo('../outside'), b'never extract'))
        elif kind == 'duplicate': members.append(members[0])
        elif kind == 'compression': entry.compress_type = zipfile.ZIP_DEFLATED
        elif kind == 'symlink': entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        elif kind == 'directory': members.append((zipfile.ZipInfo('directory/'), b''))
        return members
    if kind == 'duplicate':
        with pytest.warns(UserWarning, match='Duplicate name'):
            rewrite(path, mutate)
    else:
        rewrite(path, mutate)
    with pytest.raises(ValueError):
        handoff.verify(path)
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize('kind', ['index-sha', 'blob-size', 'json-keys', 'identity'])
def test_manifest_mutations_are_checked_in_addition_to_archive_crc(evidence, tmp_path, kind):
    path, _ = collect(evidence, tmp_path)
    if kind == 'json-keys':
        rewrite(path, lambda members: [(entry, raw.replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1', 1)
                                      if entry.filename == 'manifest.json' else raw) for entry, raw in members])
    else:
        def mutate(manifest):
            if kind == 'index-sha': manifest['index_sha256'] = 'e' * 64
            elif kind == 'blob-size': next(iter(manifest['blobs'].values()))['bytes'] += 1
            else:
                manifest['index']['profile_sha256'] = 'e' * 64
                manifest['index_sha256'] = sha(manifest['index'])
        change_manifest(path, mutate)
    with pytest.raises(ValueError):
        handoff.verify(path)


@pytest.mark.parametrize('kind', ['check-id', 'job-id', 'job-digest', 'candidate', 'completed-null', 'failed-outcome'])
def test_self_consistent_hashes_do_not_validate_malformed_receipts_or_terminal_claims(evidence, tmp_path, kind):
    path, _ = collect(evidence, tmp_path)
    def mutate(manifest):
        index = manifest['index']
        job = index['jobs'][0]
        receipt = job['receipt']
        if kind == 'check-id': receipt['checks'][0]['id'] = ' \n'
        elif kind == 'job-id':
            job['job_id'] += '\n'
            receipt['job_id'] = job['job_id']
        elif kind == 'job-digest':
            job['job_sha256'] += '\n'
            receipt['job_sha256'] = job['job_sha256']
        elif kind == 'candidate': receipt['candidate_sha'] += '\n'
        elif kind == 'completed-null':
            index['original_outcome'] = None
            job['outcome_reference_state'] = 'not_recorded'
        else: index['temporal_status'] = 'FAILED'
        job['receipt_sha256'] = sha(receipt)
        if index['original_outcome'] is not None:
            index['original_outcome']['verification'] = deepcopy(receipt)
            index['original_outcome_sha256'] = sha(index['original_outcome'])
        else:
            index['original_outcome_sha256'] = None
        index['history_jobs_sha256'] = sha([{'job_id': row['job_id'], 'job_sha256': row['job_sha256']}
                                          for row in sorted(index['jobs'], key=lambda row: row['job_id'])])
        manifest['index_sha256'] = sha(index)
    change_manifest(path, mutate)
    with pytest.raises(ValueError, match='Handoff manifest'):
        handoff.verify(path)


@pytest.mark.parametrize('limit', ['MANIFEST_LIMIT', 'BLOB_LIMIT', 'PAYLOAD_LIMIT', 'PACKET_LIMIT', 'MEMBER_LIMIT'])
def test_verifier_enforces_each_resource_boundary(evidence, tmp_path, monkeypatch, limit):
    path, _ = collect(evidence, tmp_path)
    monkeypatch.setattr(handoff, limit, 1)
    with pytest.raises(ValueError):
        handoff.verify(path)


@pytest.mark.parametrize('limit', ['MANIFEST_LIMIT', 'BLOB_LIMIT', 'PAYLOAD_LIMIT', 'PACKET_LIMIT', 'MEMBER_LIMIT'])
def test_collector_enforces_limits_without_partial_publication(evidence, tmp_path, monkeypatch, limit):
    monkeypatch.setattr(handoff, limit, 1)
    with pytest.raises(ValueError):
        collect(evidence, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_offline_cli_never_initializes_control_state(evidence, tmp_path, monkeypatch, capsys):
    path, result = collect(evidence, tmp_path)
    root = tmp_path / 'unused-control-state'
    def forbidden(*args, **kwargs):
        raise AssertionError('Offline handoff verification cannot initialize State')
    monkeypatch.setattr(cli, 'State', forbidden)
    assert cli.main(['--home', str(root), 'handoff', 'verify', str(path), '--sha256', result['sha256']]) == 0
    assert json.loads(capsys.readouterr().out)['execution_success'] is None
    assert not root.exists()
    assert cli.main(['--home', str(root), 'handoff', 'verify', str(path), '--sha256', '0' * 64]) == 2
    assert 'external expected SHA256' in capsys.readouterr().err
    assert cli.main(['handoff', 'verify', str(path), '--sha256', 'invalid']) == 2
    assert '64 lowercase hex' in capsys.readouterr().err
    assert not root.exists()


def test_native_collector_does_not_load_control_environment_schema_dependencies(evidence, tmp_path):
    index, binary = evidence
    path = tmp_path / 'native.zip'
    code = '''
import importlib.abc, json, sys
from pathlib import Path
class NoControlDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('jsonschema', 'rpds'):
            raise ImportError('Control dependencies are unavailable in this native interpreter')
sys.meta_path.insert(0, NoControlDependencies())
from ergora import handoff
data = json.load(sys.stdin)
result = handoff.create(data['index'], lambda artifact: bytes.fromhex(data['bytes']), Path(sys.argv[1]))
assert 'jsonschema' not in sys.modules and 'rpds' not in sys.modules
print(json.dumps(result))
'''
    result = subprocess.run([sys.executable, '-c', code, str(path)],
                            input=json.dumps({'index': index, 'bytes': binary.hex()}), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    exported = json.loads(result.stdout)
    assert handoff.verify(path, sha256=exported['sha256'])['artifact_bytes'] == len(binary)


def test_non_archive_and_directory_are_rejected(tmp_path):
    path = tmp_path / 'not-a-zip'
    path.write_bytes(b'no archive')
    with pytest.raises(ValueError, match='Invalid handoff packet'):
        handoff.verify(path)
    with pytest.raises(ValueError, match='regular file'):
        handoff.verify(tmp_path)


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux link/FIFO input boundary')
def test_links_and_fifo_are_rejected_before_opening(evidence, tmp_path, monkeypatch):
    path, _ = collect(evidence, tmp_path)
    link = tmp_path / 'link.zip'
    link.symlink_to(path)
    fifo = tmp_path / 'pipe'
    os.mkfifo(fifo)
    def forbidden(*args, **kwargs):
        raise AssertionError('Do not open a link or block on a FIFO')
    monkeypatch.setattr(handoff.os, 'open', forbidden)
    for selected in (link, fifo):
        with pytest.raises(ValueError, match='regular file'):
            handoff.verify(selected)
