"""Observe original content-addressed training evidence without evaluating or releasing it."""

import ergora.training.execution_protocol as protocol
from ergora.runtime import budget_clock
import hashlib
import json
import math
import os
from pathlib import Path
import sys

from ergora.training.native import _training_records
from ergora.training.materials import decode_record


def _accepted_archive(project, ident, binding, baseline_id, gate, read, *, max_artifacts=None):
    """Verify original accepted metadata for the diagnostic and full-inventory readers."""
    import perfctl
    import ergora.training.execution_protocol as protocol

    evidence_sha = gate['evidence_sha256']
    perfctl.sha(evidence_sha, 'evidence_sha256')
    prefix = f'training/projects/{project.project["id"]}/perf/experiments/{ident}/accepted-evidence/{evidence_sha}/'
    archive = project.adapter.safe_file(project.root, prefix[:-1])

    def document(name):
        raw = read(prefix + name)
        value = decode_record(raw)
        return value, hashlib.sha256(raw).hexdigest()

    archive_gate, _ = document('gate-result.json')
    if project.sha(gate['archive_report']) != project.sha({**archive_gate, 'archive_path': str(archive)}):
        raise ValueError('Archived gate differs from the original job gate report')
    expected = {'status': 'ELIGIBLE_FOR_HUMAN_REVIEW', 'experiment_id': ident,
                'baseline_id': baseline_id, 'candidate_commit': binding['candidate_sha'],
                'manifest_sha256': binding['manifest_sha'], 'evidence_sha256': evidence_sha}
    if any(archive_gate.get(key) != value for key, value in expected.items()):
        raise ValueError('Archived gate belongs to another evidence or experiment')
    evidence, evidence_digest = document('evidence.json')
    if evidence_digest != evidence_sha:
        raise ValueError('Archived evidence bytes differ from their original content address')
    expected.pop('status')
    expected.pop('evidence_sha256')
    if (type(evidence.get('schema_version')) is not int or evidence['schema_version'] != 1
            or any(evidence.get(key) != value for key, value in expected.items())):
        raise ValueError('Archived evidence belongs to another manifest or experiment')
    manifest, manifest_digest = document('_archive_meta/manifest.json')
    execution = manifest.get('execution')
    if execution is not None:
        from ergora.training.materials import _exact, validate_profile_policy
        _exact(execution, ('operation', *(['profile'] if 'profile' in execution else []), *(['cpu_contract'] if 'cpu_contract' in execution else [])), 'Archived full execution')
        if 'cpu_contract' in execution:
            from ergora.training.materials import validate_cpu_execution_contract
            validate_cpu_execution_contract(execution['cpu_contract'])
        if execution['operation'] != 'full-verify':
            raise ValueError('Accepted archive requires original full verification')
        if 'profile' in execution:
            validate_profile_policy(execution['profile'])
    if manifest_digest != binding['manifest_sha']:
        raise ValueError('Archived manifest bytes differ from the original binding')
    baseline, baseline_digest = document('_archive_meta/baseline.json')
    if baseline_digest != archive_gate['baseline_snapshot_sha256']:
        raise ValueError('Archived baseline bytes differ from the original gate snapshot')
    perfctl.baseline_ok(manifest, baseline)
    comparator_sha = hashlib.sha256(read(prefix + '_archive_meta/compare_runs.py')).hexdigest()
    if comparator_sha != manifest['comparison_tool_sha256']:
        raise ValueError('Archived comparator differs from the original manifest')
    artifacts = {}
    if not isinstance(evidence.get('artifacts'), list) or not evidence['artifacts']:
        raise ValueError('Archived evidence has no artifact index')
    if max_artifacts is not None and len(evidence['artifacts']) > max_artifacts:
        raise ValueError(f'capacity_exceeded: archived evidence indexes more than {max_artifacts} artifacts')
    for item in evidence['artifacts']:
        name = item['path']
        perfctl.local_file(archive, name)
        project.adapter.safe_file(project.root, prefix + name)
        perfctl.sha(item['sha256'], 'artifact sha256')
        if name in artifacts:
            raise ValueError('Archived evidence has a duplicate artifact path')
        artifacts[name] = item
    return {'evidence_sha256': evidence_sha, 'path': str(archive), 'evidence': evidence,
            'gate_result': archive_gate, 'manifest': manifest, 'baseline': baseline,
            'comparator_sha256': comparator_sha, 'artifact_content_status': 'not_read'}, artifacts


def _retained_archive(project, experiment, files):
    """Verify the locked executor's saved local gate after an unsuccessful managed job."""
    ident, state = experiment['experiment_id'], experiment['recorded_result_state']
    unavailable = {'status': 'unavailable', 'native_result_state': state}
    if experiment['execution']['operation'] != 'full-verify' or state not in (None, 'FAILED', 'CANCELLED'):
        return {**unavailable, 'reason': 'Original job is outside retained full archive observation'}
    if experiment['job_request'] is None or experiment['started'] is None:
        return {**unavailable, 'reason': 'Original native job request or start is missing'}

    inventory = _Inventory()
    root = project.root
    job = f'training/jobs/{ident}/'
    gate_name, result_name = job + 'gate-report.json', job + 'result.json'

    def read(relative, expected=None, *, optional=False):
        return inventory.read(root, relative, 'archive', expected, evidence=False, optional=optional)

    try:
        chain = protocol.ExecutionRecords(project.project, ident, project.payload['control_home']).load()
        stopped = chain.records['stopped']
        if stopped is None:
            return {**unavailable, 'reason': 'Original managed execution owner has no saved reap record'}
        process = stopped['process']
        if state is None and process['status'] == 'succeeded':
            return {**unavailable, 'reason': 'Missing native result has no unsuccessful original executor observation'}
        request = chain.records['request']
        if request['native_request_sha256'] != files['state/' + job + 'request.json']:
            raise ValueError('Original native request differs from the managed attempt')
        project.registration(inventory)
        for path, raw in chain.originals.items():
            inventory.read(root, path.relative_to(root).as_posix(), 'execution',
                           hashlib.sha256(raw).hexdigest(), 16 * 1_048_576, evidence=False)
        for relative in (job + 'started.json', f'training/manifests/{ident}.json', f'training/specs/{ident}.json',
                         f'training/projects/{project.project["id"]}/perf/experiments/{ident}/manifest.json'):
            read(relative, files['state/' + relative])
        saved_result = read(result_name, files.get('state/' + result_name), optional=True)
        if (saved_result is None) != (state is None):
            raise ValueError('Original native result changed during retained archive observation')
        gate_raw = read(gate_name, files.get('state/' + gate_name))
        gate = decode_record(gate_raw)
        binding = experiment['binding']
        if (gate['passed'] is not True or gate['binding'] != binding
                or gate['manifest_sha256'] != binding['manifest_sha']):
            raise ValueError('No passing local gate matches the original native job')
        archive_output = read(job + 'archive-output/execution.log')
        # The native executor consumes the leading JSON and leaves the trailing log intact.
        archive_report, _ = json.JSONDecoder().raw_decode(archive_output.decode('utf-8').lstrip())
        if project.sha(archive_report) != project.sha(gate['archive_report']):
            raise ValueError('Original native archive output differs from the retained gate report')
        archive, artifacts = _accepted_archive(project, ident, binding, experiment['baseline_id'], gate, read, max_artifacts=256)
        for name, artifact in artifacts.items():
            inventory.read(archive['path'], name, 'archive', artifact['sha256'], 16 * 1_048_576, evidence=False)
        inventory.confirm()
    except (OSError, KeyError, TypeError, ValueError, project.core.Blocked) as error:
        return {**unavailable, 'reason': str(error)}
    return {'status': 'verified', 'native_result_state': state, 'job_id': request['job_id'],
            'run_id': request['run_id'], 'attempt_sha256': chain.sha(chain.records['attempt']),
            'reap_record_sha256': chain.sha(stopped),
            'executor_process': {key: process[key] for key in ('status', 'returncode')},
            'gate_report_sha256': hashlib.sha256(gate_raw).hexdigest(),
            'archive_output_sha256': hashlib.sha256(archive_output).hexdigest(),
            'archive': {**archive, 'artifact_content_status': 'verified'}}


def inspect(payload: dict) -> dict:
    from ergora.training.runtime.context import _TrainingProject
    from ergora.training.materials import read_raw

    project = _TrainingProject(payload)
    project.registration()
    ident = project.core.slug(payload['experiment_id'])
    observed = _training_records({'project': project.project['id'], 'repo': project.project['repo'],
                                  'experiment_id': ident})
    experiment = observed['experiment']
    binding, gate = experiment['binding'], experiment['gate_report']
    files = {**observed['baseline_files'], **experiment['files']}

    def read(relative):
        raw = read_raw(project.adapter.safe_file(project.root, relative))
        files['state/' + relative] = hashlib.sha256(raw).hexdigest()
        return raw

    def document(relative: str) -> dict:
        value = json.loads(read(relative))
        if not isinstance(value, dict):
            raise ValueError('Training evidence record must be a JSON object: ' + relative)
        return value

    result = {'project': project.project['id'], 'project_revision': project.project['revision'],
              'experiment_id': ident, 'binding': binding, 'read_only': True, 'runtime_status': 'not_queried',
              'execution_success': None, 'approval_status': 'not_evaluated', 'integration_verified': None,
              'baseline_matches': experiment['baseline_matches'], 'baseline_error': experiment['baseline_error'],
              'fence_recorded': experiment['fence_recorded'], 'recorded_gate_report': gate,
              'archive_status': 'no_accepted_archive', 'archive': None, 'artifact': None,
              'screen': None, 'screen_status': 'not_recorded',
              'integration_ticket': None, 'files': files,
              'artifact_limit_bytes': 16_777_216, 'response_limit_bytes': 8_388_608,
              'scope': 'Saved native records only; no live phase, statistical re-evaluation, artifact-wide verification, authorization or integration completion claim'}
    if payload.get('retained_archive'):
        result['retained_archive'] = _retained_archive(project, experiment, files)
        result['scope'] = ('Saved native records and bounded retained archive verification; '
                           'no live runtime query, statistical re-evaluation, authorization or integration completion claim')
    if experiment.get('screen_ref') is not None:
        native = experiment['job_request']
        job = {'binding': binding, 'job_id': native['job_id']}
        bundle = _screen_result(project, ident, payload['control_home'], job)
        result.update(screen_status='complete' if bundle['complete'] else 'cleanup_unavailable',
            screen={'result_sha256': bundle['sha256'], 'report': bundle['result'], 'cleanup': bundle['cleanup']})
        if payload['artifact'] is not None:
            if payload.get('evidence_sha256') is not None or payload.get('screen_result_sha256') != bundle['sha256']:
                raise ValueError('Screen artifact read requires the exact screen result SHA-256')
            item = next((item for item in bundle['result']['artifacts'] if item['path'] == payload['artifact']), None)
            if item is None:
                raise ValueError('Selected artifact is absent from the original screen index')
            raw = bundle['inventory'].originals[Path(bundle['output']) / item['path']][0]
            result['artifact'] = _artifact_window(raw, item, payload)
            bundle['inventory'].confirm()
        return result
    if payload.get('screen_result_sha256') is not None:
        raise ValueError('Full archive artifact requires its full evidence SHA-256')
    if gate is None or gate['passed'] is not True:
        if payload['artifact'] is not None:
            raise ValueError('No accepted archive is recorded for the selected artifact')
        return result
    if experiment['recorded_result_state'] != 'SUCCEEDED':
        if payload.get('retained_archive'):
            return result
        raise ValueError('Accepted training evidence has no successful original job result')
    archive, artifacts = _accepted_archive(project, ident, binding, experiment['baseline_id'], gate, read)
    result.update(archive_status='recorded', archive=archive)
    evidence_sha = archive['evidence_sha256']
    prefix = Path(archive['path']).relative_to(project.root).as_posix() + '/'
    if payload['artifact'] is not None:
        if payload['evidence_sha256'] != evidence_sha:
            raise ValueError('Artifact read requires the exact observed evidence SHA-256')
        item = artifacts.get(payload['artifact'])
        if item is None:
            raise ValueError('Selected artifact is absent from the original evidence index')
        raw = read_raw(project.adapter.safe_file(project.root, prefix + item['path']), 16_777_216)
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Artifact bytes differ from the original evidence digest')
        text = raw.decode('utf-8')
        if '\0' in text:
            raise ValueError('Selected artifact contains NUL; only UTF-8 text evidence is supported')
        offset = payload['offset']
        if offset > len(text):
            raise ValueError('Artifact character offset exceeds the original text length')
        stop = min(offset + payload['limit'], len(text))
        result['artifact'] = {'path': item['path'], 'sha256': item['sha256'], 'bytes': len(raw),
                              'characters': len(text), 'offset': offset, 'limit': payload['limit'],
                              'next_offset': stop if stop < len(text) else None, 'text': text[offset:stop]}

    ticket_id = ident + '-' + evidence_sha[:16]
    ticket_path = 'training/integration-tickets/' + ticket_id + '.json'
    try:
        ticket = document(ticket_path)
    except FileNotFoundError:
        ticket = None
    if ticket is not None:
        receipt_id = project.core.slug(ticket['approval_receipt_id'])
        expected_ticket = {'schema_version': 1, 'kind': 'local-integration-revalidation',
                           'project': project.project['id'], 'binding': binding, 'evidence_sha256': evidence_sha,
                           'approval_receipt_id': receipt_id, 'automatic_merge': False}
        if project.sha(ticket) != project.sha(expected_ticket):
            raise ValueError('Integration ticket differs from the original project, binding or evidence')
        result['integration_ticket'] = {'task_id': ticket_id, 'task_url': (project.root / ticket_path).as_uri(),
                                        'record': ticket, 'approval_currently_valid': None}
    return result


def _artifact_window(raw, item, payload):
    text = raw.decode('utf-8')
    if '\0' in text:
        raise ValueError('Selected artifact contains NUL; only UTF-8 text evidence is supported')
    offset = payload['offset']
    if offset > len(text):
        raise ValueError('Artifact character offset exceeds the original text length')
    stop = min(offset + payload['limit'], len(text))
    return {'path': item['path'], 'sha256': item['sha256'], 'bytes': len(raw), 'characters': len(text),
        'offset': offset, 'limit': payload['limit'], 'next_offset': stop if stop < len(text) else None, 'text': text[offset:stop]}


class _Inventory:
    """One complete read, retaining original path/inode/raw identity until its final check."""

    def __init__(self):
        self.originals = {}
        self.absences = set()
        self.presence_guards = set()
        self.total = 0

    def read(self, root, relative, label, expected=None, limit=1_048_576, *, evidence=True, optional=False):
        import ergora.training.execution_protocol as protocol
        from ergora.training.materials import relative as canonical_relative

        path = Path(root) / canonical_relative(relative)
        if optional:
            self.presence_guards.add(path)
        try:
            descriptor = protocol._fd(path)
        except FileNotFoundError:
            if not optional:
                raise
            if path in self.originals:
                raise ValueError('archive_changed: original baseline reference file disappeared')
            self.absences.add(path)
            return None
        existing = self.originals.get(path)
        read_limit = min(limit, 64 * 1_048_576 - self.total) if existing is None else limit
        with os.fdopen(descriptor, 'rb') as stream:
            details = os.fstat(stream.fileno())
            if details.st_size > read_limit:
                raise ValueError('capacity_exceeded: complete baseline reference inventory')
            chunks, length, digest = [], 0, hashlib.sha256()
            while chunk := stream.read(min(65_536, read_limit + 1 - length)):
                chunks.append(chunk)
                length += len(chunk)
                digest.update(chunk)
                if length > read_limit:
                    break
            if length > read_limit:
                raise ValueError('capacity_exceeded: complete baseline reference inventory')
            raw = b''.join(chunks)
        digest = digest.hexdigest()
        if path in self.absences:
            raise ValueError('archive_changed: original baseline reference absence changed')
        if expected is not None and digest != expected:
            raise ValueError('archive_changed: original baseline reference digest differs: ' + relative)
        if existing is not None:
            original, device, inode, record = existing
            if original != raw or (device, inode) != (details.st_dev, details.st_ino):
                raise ValueError('archive_changed: baseline reference path, inode or raw changed during inventory')
            if evidence and record is None:
                self.originals[path] = (original, device, inode,
                    {'root': label, 'path': relative, 'bytes': len(raw), 'sha256': digest})
            return raw
        self.total += len(raw)
        self.originals[path] = (raw, details.st_dev, details.st_ino,
                                {'root': label, 'path': relative, 'bytes': len(raw), 'sha256': digest} if evidence else None)
        return raw

    def confirm(self):
        import ergora.training.execution_protocol as protocol

        # Confirm presence guards only after all ordinary payload reads.
        ordered = sorted(self.originals.items(), key=lambda item: item[0] in self.presence_guards)
        for path, (raw, device, inode, _) in ordered:
            with os.fdopen(protocol._fd(path), 'rb') as stream:
                details = os.fstat(stream.fileno())
                if (details.st_dev, details.st_ino) != (device, inode) or stream.read(len(raw) + 1) != raw:
                    raise ValueError('archive_changed: baseline reference path, inode or raw bytes changed')
                current = path.stat(follow_symlinks=False)
                if (current.st_dev, current.st_ino) != (device, inode):
                    raise ValueError('archive_changed: baseline reference path changed during final read')
        # Check relevant absences last, including late dangling links/FIFOs.
        for path in self.absences:
            try:
                path.lstat()
            except FileNotFoundError:
                continue
            raise ValueError('archive_changed: original baseline reference absence became visible')

    def index(self):
        return sorted((item[3] for item in self.originals.values() if item[3] is not None),
                      key=lambda item: (item['root'], item['path']))


def _cpu_observations(observations):
    """The supported diagnostic source must actually describe a CPU-only workload."""
    proof = {}
    for arm in ('baseline', 'candidate'):
        observed = observations.get(arm) if isinstance(observations, dict) else None
        layout = observed.get('workload', {}).get('layout') if isinstance(observed, dict) else None
        if not isinstance(layout, dict) or layout.get('kind') != 'cpu-single-process':
            raise ValueError('unsupported: diagnostic source has no actual CPU single-process workload observation')
        proof[arm] = {'layout': layout, 'source_sha256': observed.get('source_sha256')}
    return proof


def validate_cpu_applicability(baseline, *, observations=None, screen=None):
    """Consume authenticated original CPU facts; configuration alone grants no GPU work."""
    from ergora.training.materials import observation_sha256

    reference = baseline.get('reference') if isinstance(baseline, dict) else None
    receipt = reference.get('receipt') if isinstance(reference, dict) else None
    environment = receipt.get('environment') if isinstance(receipt, dict) else None
    observed = environment.get('observed') if isinstance(environment, dict) else None
    layout = receipt.get('baseline', {}).get('workload', {}).get('layout') if isinstance(receipt, dict) else None
    if (not isinstance(observed, dict) or observed.get('device') != 'CPU' or observed.get('ranks') != [0]
            or observed.get('layout') != 'single-process' or not environment.get('report_ref')
            or not isinstance(layout, dict) or layout.get('kind') != 'cpu-single-process'):
        raise ValueError('unsupported: original baseline has no applicable actual CPU environment/workload evidence; managed GPU guard is unavailable')
    proof = {'kind': 'training-cpu-applicability', 'baseline_reference_sha256': baseline.get('reference_sha256'),
             'environment': observed, 'environment_report_ref': environment['report_ref'], 'layout': layout}
    if observations is not None:
        proof['source_observations'] = _cpu_observations(observations)
    if screen is not None:
        result = screen.get('source_report', screen.get('result', screen)) if isinstance(screen, dict) else None
        scope = result.get('workload', {}).get('scope') if isinstance(result, dict) else None
        actual = scope.get('environment') if isinstance(scope, dict) else None
        if (not isinstance(scope, dict) or scope.get('device') != 'CPU' or not isinstance(actual, dict)
                or actual.get('device') != 'CPU' or actual.get('ranks') != [0] or actual.get('layout') != 'single-process'):
            raise ValueError('unsupported: actual screen has no applicable CPU environment/workload evidence')
        proof['screen_environment'] = actual
    return {**proof, 'sha256': observation_sha256(proof)}



def _cpu_window_contract(proof, request):
    contract = request['execution'].get('cpu_contract')
    if (contract is None or proof.get('contract_sha256') != contract['sha256']
            or proof.get('preparation') != request.get('cpu_contract_preparation')):
        raise ValueError('Core CPU window differs from its original typed contract/acceptance')


def cpu_contract_evidence(output, request, manifest, *, inventory=None, require_complete=False, expected_owner=None):
    """Original C/A and locally owned lineage, with no following archived host refs."""
    import ergora.training.materials as materials
    import ergora.training.execution_protocol as protocol
    contract = materials.cpu_contract(manifest)
    if contract is None:
        return None
    output = Path(output)
    inventory = _Inventory() if inventory is None else inventory
    def raw(name, limit=16 * 1_048_576):
        return inventory.read(output, name, 'cpu-materials', limit=limit)
    intent_raw, admission_raw = raw('cpu-contract-preparation-intent.json'), raw('cpu-contract-admission.json')
    intent, admission = materials.decode_record(intent_raw), materials.decode_record(admission_raw)
    body = materials.preparation_preview_body(intent)
    runner = body['sources']['runner']['document']
    manifest_raw = body['files']['training/manifests/' + manifest['experiment_id'] + '.json'].encode('utf-8')
    if materials.decode_record(manifest_raw) != manifest or hashlib.sha256(manifest_raw).hexdigest() != request['binding']['manifest_sha']:
        raise ValueError('Original CPU material manifest differs from its admitted native binding')
    materials.validate_cpu_preparation_admission(admission, intent, manifest_raw, runner)
    if body['execution'] != request['context']['intent']['execution']:
        raise ValueError('Archived CPU preparation execution differs from original managed source')
    checked = materials.validate_preparation_intent(intent)
    envelope = materials.cpu_preparation_observation({'contract': contract, 'contract_sha256': contract['sha256'],
        'intent_raw': intent_raw, 'admission_raw': admission_raw,
        'preview_sha256': checked['preview_sha256'], 'intent_sha256': checked['intent_sha256']}, manifest['experiment_id'], output=True)
    if request.get('cpu_contract_preparation') != {key: envelope[key] for key in ('intent_ref', 'admission_ref')}:
        raise ValueError('CPU execution request lost its original complete acceptance material')
    metadata = materials.decode_record(raw('cpu-execution-materials.json'))
    materials._exact(metadata, ('schema_version', 'kind', 'contract_sha256', 'budget_context', 'sources',
        'native_ref', 'native_parent_ref', 'managed_records', 'process_records', 'lineage_reason'), 'Original CPU execution material inventory')
    if metadata['schema_version'] != 1 or metadata['kind'] != 'training-cpu-execution-materials' or metadata['contract_sha256'] != contract['sha256']:
        raise ValueError('CPU execution materials differ from their original contract')
    indexed = {}
    for item in metadata['sources']:
        materials._exact(item, ('original_path', 'original_sha256', 'original_bytes', 'artifact_ref'), 'Original archived CPU context source')
        ref = item['artifact_ref']
        original = inventory.read(output, ref['path'], 'cpu-materials', ref['sha256'], 10 * 1_048_576)
        if len(original) != ref['bytes'] or len(original) != item['original_bytes'] or hashlib.sha256(original).hexdigest() != item['original_sha256']:
            raise ValueError('Archived CPU context source differs from its complete original raw reference')
        key = (item['original_path'], item['original_sha256'], item['original_bytes'])
        if key in indexed:
            raise ValueError('Archived CPU source inventory is ambiguous')
        indexed[key] = original
    def archived(ref):
        original = indexed.get((ref['path'], ref['sha256'], ref['bytes']))
        if original is None:
            raise ValueError('CPU context refers outside its complete archived source inventory')
        return materials.decode_record(original)
    context = request['context']
    if context.get('cpu_context') != metadata['budget_context']:
        raise ValueError('Archived CPU budget context differs from its original managed context')
    budget_stable = protocol.validate_cpu_budget_context(context, expected_budget=expected_owner,
        require_complete=require_complete, reader=archived)
    binding = {'intent_sha256': materials.observation_sha256(context['intent']),
               'authorization_sha256': context['authorization']['sha256']}
    def artifact(ref):
        original = inventory.read(output, ref['path'], 'cpu-materials', ref['sha256'], 10 * 1_048_576)
        if len(original) != ref['bytes']:
            raise ValueError('CPU lineage artifact length changed')
        return materials.decode_record(original)
    native = artifact(metadata['native_ref'])
    relation = artifact(metadata['native_parent_ref'])
    materials._exact(metadata['managed_records'], ('request', 'launch', 'attempt', 'ack'), 'Original CPU managed record references')
    managed = {name: artifact(metadata['managed_records'][name]) for name in ('request', 'launch', 'attempt', 'ack')}
    if any(materials.observation_sha256(record) != request['managed'][name + '_sha256'] for name, record in managed.items()):
        raise ValueError('CPU native material differs from its original normal managed record binding')
    if (managed['attempt']['request_sha256'] != request['managed']['request_sha256']
            or managed['attempt']['launch_sha256'] != request['managed']['launch_sha256']
            or managed['ack']['attempt_sha256'] != request['managed']['attempt_sha256']
            or managed['ack']['executor'] != managed['attempt']['executor']):
        raise ValueError('CPU native material lost its original normal managed attempt/ack chain')
    native_stable = materials.validate_cpu_context_observation(native, contract=contract, role='native', binding=binding,
        expected_subject=managed['attempt']['executor'], require_complete=require_complete)
    materials._exact(relation, ('kind', 'binding', 'supervisor', 'supervisor_parent_pid', 'budget'), 'Original CPU native parent relation')
    if (relation['kind'] != 'training-cpu-native-parent' or relation['binding'] != binding
            or relation['supervisor'] != managed['attempt']['supervisor']
            or native['subject']['parent_pid'] != relation['supervisor']['pid']
            or relation['supervisor_parent_pid'] != relation['budget']['pid']):
        raise ValueError('CPU native context lost its actual original supervisor/budget relationship')
    if require_complete and budget_stable != native_stable:
        raise ValueError('unsupported: original CPU placement changed from budget to native executor')
    if expected_owner is not None:
        expected = dict(expected_owner)
        if str(expected.get('start_ticks')) != str(relation['budget']['start_ticks']) or any(expected.get(key) != relation['budget'][key] for key in ('pid', 'boot_id')):
            raise ValueError('CPU native parent differs from its original normal managed owner')
    wrapped = []
    for name in ('cpu-wrapper-context.json', 'cpu-wrapper-prepared-context.json'):
        frame = materials.decode_record(raw(name, 10 * 1_048_576))
        wrapped.append((frame, materials.validate_cpu_context_observation(frame, contract=contract, role='wrapper',
            binding=binding, require_complete=require_complete)))
    if any(item[0]['subject'] != wrapped[0][0]['subject'] for item in wrapped[1:]):
        raise ValueError('Source construction changed its original wrapper/thread subject')
    if metadata['process_records'] is None:
        if not isinstance(metadata['lineage_reason'], str) or not metadata['lineage_reason']:
            raise ValueError('Unavailable CPU process lineage requires its actual reason')
        if require_complete:
            raise ValueError(metadata['lineage_reason'])
    else:
        if metadata['lineage_reason'] is not None:
            raise ValueError('Complete CPU lineage cannot also claim unavailability')
        original_request_raw = raw('cpu-contract-configuration-request.json')
        original_request = materials.decode_record(original_request_raw)
        if (original_request != {key: value for key, value in request.items() if key != '_raw_sha256'}
                or '_raw_sha256' in request and hashlib.sha256(original_request_raw).hexdigest() != request['_raw_sha256']):
            raise ValueError('Archived CPU configuration request differs from its original complete binding')
        core = materials.decode_record(raw('cpu-core-sources.json'))
        materials._exact(core, ('package_directory', 'sources', 'contract_sha256'), 'Original archived CPU core source map')
        package = Path(core['package_directory'])
        state = Path(body['execution']['state_directory'])
        if (not package.is_absolute() or str(package) != core['package_directory'] or package.name != 'ergora'
                or not state.is_absolute() or str(state) != body['execution']['state_directory']
                or core['contract_sha256'] != contract['sha256']
                or materials.observation_sha256(core['sources']) != contract['implementation']['core_sources_sha256']
                or request['cpu_contract_core'] != {'package_directory': str(package),
                    'sources_sha256': contract['implementation']['core_sources_sha256']}
                or 'training/configuration.py' not in core['sources']):
            raise ValueError('Archived CPU command lacks its original admitted core source map')
        job = state / 'training/jobs' / manifest['experiment_id']
        expected_command = [runner['command'][0], str(package / 'training/configuration.py'), str(job / 'configuration-request.json')]
        records = {name: artifact(metadata['process_records'][name]) for name in ('request', 'started', 'pid')}
        process = materials.decode_record(raw('cpu-process-context.json', 10 * 1_048_576))
        process_stable = materials.validate_cpu_context_observation(process, contract=contract, role='process', binding=binding,
            expected_subject={'pid': records['started']['monitor_pid']}, require_complete=require_complete)
        if (process['subject']['parent_pid'] != native['subject']['pid']
                or wrapped[0][0]['subject']['parent_pid'] != records['pid']['pid']
                or records['request']['output'] != request['output']
                or request['output'] != str(job / 'run-output')
                or records['request']['command'] != expected_command or records['started']['command'] != expected_command):
            raise ValueError('CPU source wrapper lost its actual fixed process_job/timeout/native relation')
        if require_complete and any(value != native_stable for value in (process_stable, *[item[1] for item in wrapped])):
            raise ValueError('unsupported: original CPU placement changed across its owned native/source handoff')
    inventory.confirm()
    return envelope



def cpu_reuse_identity(baseline, screen):
    """Read independently bound original physical/placement facts for negative reuse."""
    from ergora.training.materials import validate_cpu_window_identity

    reference = baseline.get('reference') if isinstance(baseline, dict) else None
    receipt = reference.get('receipt') if isinstance(reference, dict) else None
    result = screen.get('result') if isinstance(screen, dict) else None
    if not isinstance(receipt, dict) or not isinstance(result, dict):
        raise ValueError('unsupported: CPU reuse lacks original baseline/screen evidence')
    original_contract = baseline.get('cpu_contract')
    screen_contract = screen.get('cpu_contract')
    if (not isinstance(original_contract, dict) or not isinstance(screen_contract, dict)
            or original_contract['contract_sha256'] != screen_contract['contract_sha256']):
        raise ValueError('unsupported: original baseline/screen lacks its original typed CPU contract/acceptance')
    if baseline.get('cpu_owner') is None or screen.get('cpu_owner') is None:
        raise ValueError('unsupported: original CPU material lacks its normal managed owner')
    for observed in (baseline, screen):
        source = observed['cpu_materials']
        cpu_contract_evidence(Path(source['output']), source['request'], source['manifest'], require_complete=True,
                              expected_owner=observed['cpu_owner'])
    measurements = receipt.get('measurement', [])
    windows = result.get('windows', [])
    if not measurements or not windows:
        raise ValueError('unsupported: CPU reuse lacks original unprofiled windows')
    subjects = [(receipt, receipt['baseline'].get('core_cpu_execution'), 'baseline',
        [item['provenance'] for item in measurements]),
        (result, result['workload']['scope'].get('core_cpu_execution'), 'screen',
         [item['provenance'] for item in windows])]
    from ergora.training.materials import read_raw
    def original_core(proof, observed):
        if not isinstance(proof, dict):
            raise ValueError('unsupported: original core-owned CPU window proof is missing')
        envelope = observed['cpu_contract']
        if (proof.get('contract_sha256') != envelope['contract_sha256']
                or proof.get('preparation') != {key: envelope[key] for key in ('intent_ref', 'admission_ref')}):
            raise ValueError('Original CPU window lost its typed contract/acceptance binding')
        wrapper = decode_record(read_raw(Path(observed['cpu_materials']['output']) / 'cpu-wrapper-prepared-context.json', 10 * 1_048_576))
        for snapshot in (proof.get('before'), proof.get('after')):
            raw = snapshot.get('raw') if isinstance(snapshot, dict) else None
            provenance = raw.get('allocation_provenance') if isinstance(raw, dict) else None
            actual_subject = provenance.get('subject') if isinstance(provenance, dict) else None
            if not isinstance(actual_subject, dict):
                raise ValueError('unsupported: original core-owned CPU window subject proof is unavailable')
            if any(actual_subject.get(key) != value for key, value in wrapper['subject'].items()):
                raise ValueError('Original CPU measured thread is not its actual admitted wrapper subject')
    identities = []
    unprofiled_ids = {item[key] for _, _, _, values in subjects for item in values for key in ('run_id', 'window_id')}
    for owner, proof, phase, provenance in subjects:
        observed_material = baseline if phase == 'baseline' else screen
        original_core(proof, observed_material)
        execution_phases = {item['execution_phase_id'] for item in provenance}
        if len(execution_phases) != 1:
            raise ValueError('CPU reuse changed its original unprofiled execution phase')
        selected = [{key: item[key] for key in ('run_id', 'window_id')} for item in provenance]
        unprofiled_ids.update(value for item in selected for value in item.values())
        identities.append(validate_cpu_window_identity(proof, binding=owner['binding'],
            native_request_sha256=owner['native_request_sha256'], managed=owner['managed'], source=owner['source'],
            execution_phase_id=next(iter(execution_phases)), phase=phase, operation='unprofiled', windows=selected))
        diagnostics = baseline.get('diagnostics') if phase == 'baseline' else screen.get('diagnostics')
        if not isinstance(diagnostics, dict) or diagnostics.get('status') != 'complete' or not diagnostics.get('raw'):
            raise ValueError('unsupported: CPU reuse requires the original actual profile hardware/window proof')
        for entry in diagnostics['raw']:
            capture = entry['capture']
            actual, selection = capture['actual'], capture['selection']
            if selection['phase'] != phase or any(selection[key] in unprofiled_ids for key in ('run_id', 'window_id')):
                raise ValueError('CPU reuse mixes original profile and unprofiled windows')
            if (any(capture[key] != owner[key] for key in ('binding', 'managed'))
                    or {key: value for key, value in capture['source'].items() if key != 'repo'}
                       != {key: value for key, value in owner['source'].items() if key != 'repo'}):
                raise ValueError('CPU profile hardware observation changed its original binding')
            original_core(actual['hardware'].get('core_cpu_execution'), observed_material)
            identities.append(validate_cpu_window_identity(actual['hardware'].get('core_cpu_execution'),
                binding=owner['binding'], native_request_sha256=owner['native_request_sha256'],
                managed=owner['managed'], source=owner['source'], execution_phase_id=next(iter(execution_phases)),
                phase=phase, operation='profiled', windows=[{key: selection[key] for key in ('run_id', 'window_id')}]))
    if any(identity != identities[0] for identity in identities[1:]):
        raise ValueError('unsupported: original baseline/screen/profile CPU hardware or placement differs')
    return identities[0]


def _profile_report(raw):
    """Fixed data-only reader for finite cProfile JSON; never load marshal/pickle/source."""
    from ergora.training.materials import _exact, observation_bytes

    capture = decode_record(raw)
    _exact(capture, ('schema_version', 'kind', 'tool', 'reader', 'source', 'binding', 'managed',
                     'configuration_request_sha256', 'selection', 'actual', 'elapsed_seconds', 'functions'), 'Profile capture')
    if type(capture['schema_version']) is not int or capture['schema_version'] != 1 or capture['kind'] != 'training-cprofile-json' or capture['reader'] != 'cprofile-json-v1':
        raise ValueError('Unsupported profile capture or fixed reader')
    tool = capture['tool']
    _exact(tool, ('name', 'version', 'build'), 'Profile tool')
    if tool['name'] != 'cprofile-json' or not all(isinstance(tool[key], str) and tool[key] for key in ('version', 'build')):
        raise ValueError('Profile capture lacks actual tool identity')
    if type(capture['elapsed_seconds']) not in (int, float) or not math.isfinite(capture['elapsed_seconds']) or capture['elapsed_seconds'] < 0:
        raise ValueError('Profile capture has invalid actual duration')
    functions = capture['functions']
    if not isinstance(functions, list) or not functions or len(functions) > 100_000:
        raise ValueError('Profile capture has no complete bounded function table')
    lines = ['cProfile CPU diagnostic; profiled values are excluded from throughput.',
             'calls recursive inline_seconds total_seconds function']
    identities = set()
    for entry in functions:
        _exact(entry, ('function', 'calls', 'recursive_calls', 'inline_seconds', 'total_seconds', 'callees'), 'Profile function')
        if not isinstance(entry['function'], str) or not entry['function'] or entry['function'] in identities:
            raise ValueError('Profile capture contains duplicate or invalid function identities')
        identities.add(entry['function'])
        for key in ('calls', 'recursive_calls'):
            if type(entry[key]) is not int or entry[key] < 0:
                raise ValueError('Profile counts must be nonnegative integers')
        for key in ('inline_seconds', 'total_seconds'):
            if type(entry[key]) not in (int, float) or not math.isfinite(entry[key]) or entry[key] < 0:
                raise ValueError('Profile timings must be finite nonnegative numbers')
        if not isinstance(entry['callees'], list) or not all(isinstance(callee, str) and callee for callee in entry['callees']):
            raise ValueError('Profile edges require complete function identities')
        lines.append(f"{entry['calls']} {entry['recursive_calls']} {entry['inline_seconds']:.9g} {entry['total_seconds']:.9g} {json.dumps(entry['function'], ensure_ascii=False)}")
    if any(callee not in identities for entry in functions for callee in entry['callees']):
        raise ValueError('Profile edge points outside the complete function table')
    observation_bytes(capture, 16 * 1_048_576)
    return capture, '\n'.join(lines) + '\n'


def _profile_contents(output, policy, *, request=None, inventory=None, receipt_raw=None):
    """The collector can validate pending receipt bytes before immutable publication."""
    from ergora.training.materials import _exact, validate_profile_policy, observation_sha256

    validate_profile_policy(policy)
    output = Path(output)
    inventory = _Inventory() if inventory is None else inventory
    if receipt_raw is None:
        receipt_raw = inventory.read(output, 'profile-receipt.json', 'profile')
    receipt = decode_record(receipt_raw)
    _exact(receipt, ('schema_version', 'kind', 'policy', 'policy_sha256', 'binding', 'managed', 'source',
                     'configuration_request_sha256', 'phase', 'tool', 'reader', 'source_operation', 'status',
                     'reason', 'captures', 'attempts', 'raw_bytes', 'derived_bytes', 'readback'), 'Profile receipt')
    if (type(receipt['schema_version']) is not int or receipt['schema_version'] != 1 or receipt['kind'] != 'training-profile-receipt'
            or receipt['policy'] != policy or receipt['policy_sha256'] != observation_sha256(policy)
            or receipt['tool'] != policy['tool'] or receipt['reader'] != policy['reader']
            or receipt['source_operation'] != policy['source_operation']
            or receipt['phase'] not in policy['phases']):
        raise ValueError('Profile receipt differs from the frozen diagnostic policy')
    if request is not None:
        for key, expected in {'binding': request['binding'], 'managed': request['managed'],
                'source': request['configuration_readback']['source'],
                'configuration_request_sha256': request['_raw_sha256'],
                'phase': 'screen' if request['execution']['operation'] == 'training-screen-v1' else 'baseline'}.items():
            if receipt[key] != expected:
                raise ValueError('Profile receipt differs from its original managed ' + key)
    if (receipt['status'] not in ('complete', 'unavailable', 'not_run', 'failed')
            or not isinstance(receipt['captures'], list) or not isinstance(receipt['attempts'], list)):
        raise ValueError('Profile receipt has unknown capture actuality')
    maximum = policy['captures'] * len(policy['ranks'])
    if len(receipt['captures']) > maximum or len(receipt['attempts']) > maximum:
        raise ValueError('Profile receipt exceeds its frozen opportunity count')
    attempts = set()
    for attempt in receipt['attempts']:
        _exact(attempt, ('selection', 'capture', 'readback', 'reason'), 'Profile attempt')
        selected = attempt['selection']
        if (not isinstance(selected, dict) or type(selected.get('rank')) is not int
                or type(selected.get('capture_index')) is not int):
            raise ValueError('Profile attempt lacks its original typed selection')
        key = (selected['rank'], selected['capture_index'])
        if key in attempts or selected['rank'] not in policy['ranks'] or type(selected['capture_index']) is not int or not 0 <= selected['capture_index'] < policy['captures']:
            raise ValueError('Profile receipt repeats or changes an attempted opportunity')
        attempts.add(key)
        if attempt['capture'] not in ('complete', 'failed') or attempt['readback'] not in ('complete', 'not_run', 'failed'):
            raise ValueError('Profile attempt remains unknown')
    if receipt['status'] == 'complete':
        if (receipt['reason'] is not None or receipt['readback'] != 'complete' or len(receipt['captures']) != maximum
                or len(receipt['attempts']) != maximum or any(item['capture'] != 'complete' or item['readback'] != 'complete' or item['reason'] is not None for item in receipt['attempts'])):
            raise ValueError('Profile capture/readback is incomplete')
    elif not isinstance(receipt['reason'], str) or not receipt['reason']:
        raise ValueError('Unavailable/failed profile requires its actual reason')
    if receipt['status'] in ('unavailable', 'not_run'):
        if receipt['captures'] or receipt['attempts'] or receipt['readback'] != 'not_run' or receipt['raw_bytes'] != 0 or receipt['derived_bytes'] != 0:
            raise ValueError('Unavailable profile cannot claim a capture/readback opportunity')
        for rank in policy['ranks']:
            for ordinal in range(policy['captures']):
                for suffix in ('.json', '.txt'):
                    if inventory.read(output, f"profile/{receipt['phase']}-{rank}-{ordinal}{suffix}",
                            'profile', optional=True) is not None:
                        raise ValueError('Unavailable diagnostic already has an original capture opportunity')
    elif receipt['status'] == 'failed' and receipt['readback'] not in ('failed', 'not_run'):
        raise ValueError('Failed diagnostic cannot claim complete readback')
    raw_items, derived_items = [], []
    if receipt['captures']:
        if policy['tool'] != 'cprofile-json' or policy['reader'] != 'cprofile-json-v1' or policy['source_operation'] != 'cpu-diagnostic-v1' or policy['ranks'] != [0]:
            raise ValueError('Profile receipt claims an unsupported actual operation')
        raw_items, derived_items, total_raw, total_derived, elapsed, selections = [], [], 0, 0, 0, set()
        for item in receipt['captures']:
            _exact(item, ('raw_ref', 'derived_ref', 'selection'), 'Profile capture index')
            selection = item['selection']
            _exact(selection, ('phase', 'rank', 'capture_index', 'window_id', 'run_id', 'window', 'source_operation'), 'Profile selection')
            ordinal = selection['capture_index']
            if (selection['phase'] != receipt['phase'] or type(selection['rank']) is not int or selection['rank'] not in policy['ranks']
                    or type(ordinal) is not int or not 0 <= ordinal < policy['captures']
                    or selection['window'] != policy['window'] or selection['source_operation'] != policy['source_operation']
                    or (selection['rank'], ordinal) in selections):
                raise ValueError('Profile capture selection differs from its frozen rank/window/count')
            selections.add((selection['rank'], ordinal))
            if not any(attempt['selection'] == selection and attempt['capture'] == 'complete' for attempt in receipt['attempts']):
                raise ValueError('Profile raw capture lacks its original durable opportunity')
            identity = observation_sha256({'request': receipt['configuration_request_sha256'],
                'phase': receipt['phase'], 'rank': selection['rank'], 'capture': ordinal})
            if selection['window_id'] != 'profile-window-' + identity[:24] or selection['run_id'] != 'profile-run-' + identity[:24]:
                raise ValueError('Profile IDs differ from the original separate diagnostic window')
            for key, suffix in (('raw_ref', '.json'), ('derived_ref', '.txt')):
                ref = item[key]
                _exact(ref, ('path', 'sha256', 'bytes'), 'Profile raw reference')
                expected_path = f"profile/{receipt['phase']}-{selection['rank']}-{ordinal}{suffix}"
                if ref['path'] != expected_path or type(ref['bytes']) is not int or ref['bytes'] < 0:
                    raise ValueError('Profile reference differs from its fixed original capture path')
            raw = inventory.read(output, item['raw_ref']['path'], 'profile', item['raw_ref']['sha256'], policy['max_raw_bytes'])
            derived = inventory.read(output, item['derived_ref']['path'], 'profile', item['derived_ref']['sha256'], policy['max_derived_bytes'])
            if len(raw) != item['raw_ref']['bytes'] or len(derived) != item['derived_ref']['bytes']:
                raise ValueError('Profile original raw/derived bytes differ from their complete receipt')
            capture, text = _profile_report(raw)
            if derived != text.encode('utf-8'):
                raise ValueError('Profile fixed-reader readback differs from exact derived text')
            for key in ('source', 'binding', 'managed', 'configuration_request_sha256'):
                if capture[key] != receipt[key]:
                    raise ValueError('Profile raw capture differs from its managed receipt')
            actual = capture['actual']
            _exact(actual, ('phase', 'rank', 'window_id', 'run_id', 'window', 'input_identity', 'hardware', 'work_completed', 'warmup_work_completed', 'measurement_mode'), 'Source profile observation')
            if (capture['selection'] != selection or any(actual[key] != selection[key] for key in ('phase', 'rank', 'window_id', 'run_id', 'window'))
                    or type(actual['rank']) is not int or actual['measurement_mode'] != 'profiled' or not isinstance(actual['input_identity'], dict) or not actual['input_identity']
                    or not isinstance(actual['hardware'], dict)
                    or {key: actual['hardware'].get(key) for key in ('device', 'ranks', 'layout')} != {'device': 'CPU', 'ranks': [0], 'layout': 'single-process'}
                    or type(actual['work_completed']) is not int or type(actual['warmup_work_completed']) is not int
                    or actual['work_completed'] != policy['window']['work'] or actual['warmup_work_completed'] != policy['window']['warmup_work']):
                raise ValueError('Profile raw source observation differs from its separate actual window')
            hardware = actual['hardware']
            _exact(hardware, ('device', 'ranks', 'layout', *(['cpu_execution'] if 'cpu_execution' in hardware else []), *(['core_cpu_execution'] if 'core_cpu_execution' in hardware else [])), 'Profile CPU hardware observation')
            if 'cpu_execution' in hardware:
                from ergora.training.materials import validate_cpu_window_identity
                proof = hardware['cpu_execution']
                validate_cpu_window_identity(proof, binding=receipt['binding'],
                    native_request_sha256=request['native_request_sha256'] if request is not None else proof['native_request_sha256'],
                    managed=receipt['managed'], source=receipt['source'],
                    execution_phase_id=request['execution_phase_id'] if request is not None else proof['execution_phase_id'],
                    phase=receipt['phase'], operation='profiled',
                    windows=[{key: selection[key] for key in ('run_id', 'window_id')}], require_complete=False)
            if 'core_cpu_execution' in hardware:
                proof = hardware['core_cpu_execution']
                if request is not None:
                    _cpu_window_contract(proof, request)
                from ergora.training.materials import validate_cpu_window_identity
                validate_cpu_window_identity(proof, binding=receipt['binding'],
                    native_request_sha256=request['native_request_sha256'] if request else proof['native_request_sha256'],
                    managed=receipt['managed'], source=receipt['source'],
                    execution_phase_id=request['execution_phase_id'] if request else proof['execution_phase_id'],
                    phase=receipt['phase'], operation='profiled', windows=[{key: selection[key] for key in ('run_id', 'window_id')}], require_complete=False)
            total_raw += len(raw)
            total_derived += len(derived)
            elapsed += capture['elapsed_seconds']
            raw_items.append({'ref': item['raw_ref'], 'capture': capture})
            derived_items.append({'ref': item['derived_ref'], 'text': text})
        if (total_raw != receipt['raw_bytes'] or total_derived != receipt['derived_bytes']
                or total_raw > policy['max_raw_bytes'] or total_derived > policy['max_derived_bytes']
                or receipt['status'] == 'complete' and elapsed > policy['maximum_seconds']):
            raise ValueError('capacity_exceeded: complete profile raw/derived evidence')
    if not receipt['captures'] and (receipt['raw_bytes'] != 0 or receipt['derived_bytes'] != 0):
        raise ValueError('Profile receipt claims bytes without original captured files')
    inventory.confirm()
    return {'receipt': receipt, 'receipt_ref': {'path': 'profile-receipt.json', 'sha256': hashlib.sha256(receipt_raw).hexdigest(), 'bytes': len(receipt_raw)},
            'raw': raw_items, 'derived': derived_items, 'status': receipt['status'],
            'required_satisfied': receipt['status'] == 'complete',
            'gaps': [] if receipt['status'] == 'complete' else [{'code': receipt['status'], 'reason': receipt['reason']}], 'inventory': inventory}


def profile_bundle(output, policy, *, request=None, inventory=None):
    """Authenticate the original durable receipt and exact finite raw/derived files."""
    return _profile_contents(output, policy, request=request, inventory=inventory)


def validate_trial_diagnostics(bundle, policy):
    """D continuation requires complete actual readback or explicit optional absence."""
    from ergora.training.materials import validate_profile_policy, observation_sha256

    validate_profile_policy(policy)
    if bundle is None or not isinstance(bundle, dict) or not isinstance(bundle.get('receipt'), dict):
        raise ValueError('blocked: diagnostic receipt is missing or unknown')
    receipt = bundle['receipt']
    if receipt.get('policy') != policy or receipt.get('policy_sha256') != observation_sha256(policy):
        raise ValueError('blocked: diagnostic policy differs from the original selection')
    if receipt.get('status') == 'failed' or receipt.get('status') not in ('complete', 'unavailable', 'not_run'):
        raise ValueError('blocked: diagnostic capture/readback failed or remains unknown')
    if receipt['status'] != 'complete' and (policy['required'] or not receipt.get('reason')):
        raise ValueError('blocked: required diagnostic was not captured and read back')
    if receipt['status'] == 'complete' and (receipt.get('readback') != 'complete' or not bundle.get('raw') or not bundle.get('derived')):
        raise ValueError('blocked: diagnostic capture/readback is incomplete')
    return {'profile_sha256': bundle['receipt_ref']['sha256'], 'policy_sha256': observation_sha256(policy),
            'status': receipt['status'], 'required_satisfied': receipt['status'] == 'complete', 'gaps': bundle['gaps']}


def build_analysis_packet(*, baseline, screen, source_materials, policy):
    """Freeze complete existing evidence for the fixed readonly analyst opportunity."""
    from ergora.training.materials import observation_bytes

    if not isinstance(baseline, dict) or not isinstance(baseline.get('reference'), dict):
        raise ValueError('Analysis packet requires the complete fixed baseline reference')
    if not isinstance(source_materials, dict) or not source_materials:
        raise ValueError('Analysis packet requires complete original source graph/materials')
    baseline_validation = validate_trial_diagnostics(baseline.get('diagnostics'), policy)
    diagnostics = baseline.get('diagnostics') if screen is None else screen.get('diagnostics')
    validation = baseline_validation if screen is None else validate_trial_diagnostics(diagnostics, policy)
    def plain(bundle):
        return {key: value for key, value in bundle.items() if key != 'inventory'}
    packet = {'schema_version': 1, 'kind': 'training-round-analysis-packet', 'policy': policy,
              'baseline_reference': {key: value for key, value in baseline.items() if key not in ('inventory', 'diagnostics')},
              'unprofiled_screen': None if screen is None else {key: value for key, value in screen.items() if key not in ('inventory', 'diagnostics', 'raw')},
              'profile': plain(diagnostics), 'baseline_profile': None if screen is None else plain(baseline['diagnostics']),
              'source_materials': source_materials, 'gaps': baseline_validation['gaps'] + ([] if screen is None else validation['gaps'])}
    raw = observation_bytes(packet, 10_000_000)
    return {'packet': decode_record(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def _reason(code, field, expected=None, observed=None, source_ref=None):
    return {'code': code, 'field': field, 'expected': expected, 'observed': observed, 'source_ref': source_ref}


def _artifact_refs(value, artifacts):
    """Every explicit receipt reference must resolve to the original complete index."""
    if isinstance(value, dict):
        if 'path' in value and ('sha256' in value or 'bytes' in value):
            if set(value) != {'path', 'sha256', 'bytes'}:
                raise ValueError('Baseline receipt requires exact artifact reference identities')
            if artifacts.get(value['path']) != value:
                raise ValueError('Baseline receipt references an unindexed or mismatched artifact')
        else:
            for child in value.values():
                _artifact_refs(child, artifacts)
    elif isinstance(value, list):
        for child in value:
            _artifact_refs(child, artifacts)


def _resource_coverage(resources, artifacts, read_artifact):
    """Classify measured resource data; a soft limit does not replace the full gate."""
    import ergora.training.execution_protocol as protocol

    if not isinstance(resources, list):
        raise ValueError('Resources must list measured metrics or remain empty')
    _artifact_refs(resources, artifacts)
    resource_reasons = []
    resource_invalid = False
    for metric in resources:
        protocol._exact(metric, ('metric', 'unit', 'aggregation', 'scope', 'observed', 'limit', 'report_ref'), 'Baseline resource metric')
        if any(not isinstance(metric[key], str) or not metric[key].strip() for key in ('metric', 'unit', 'aggregation')):
            raise ValueError('Resource metric, unit and aggregation must be nonblank text')
        scope = metric['scope']
        if not (isinstance(scope, str) and scope.strip() or isinstance(scope, dict) and scope):
            raise ValueError('Resource scope must be nonblank text or a nonempty bounded JSON object')
        if (type(metric['observed']) not in (int, float) or metric['observed'] < 0
                or type(metric['observed']) is float and not math.isfinite(metric['observed'])):
            raise ValueError('Baseline resource metrics require measured finite nonnegative values with explicit units')
        if metric['limit'] is not None and (type(metric['limit']) not in (int, float) or metric['limit'] < 0
                or type(metric['limit']) is float and not math.isfinite(metric['limit'])):
            raise ValueError('Baseline resource limits require finite nonnegative values')
        if read_artifact(metric['report_ref']).get('metric') != {key: value for key, value in metric.items() if key != 'report_ref'}:
            raise ValueError('Baseline resource report differs from its receipt')
        if metric['unit'] not in ('bytes', 'seconds', 'samples', 'tokens', 'updates', 'percent'):
            resource_reasons.append(_reason('reader_unsupported', 'resources.' + str(metric['metric']) + '.unit', observed=metric['unit']))
            continue
        # A measured soft-limit violation belongs to this dimension; it does
        # not invalidate the archive or its separate quality/timing evidence.
        if metric['limit'] is not None and metric['observed'] > metric['limit']:
            resource_invalid = True
            resource_reasons.append(_reason('resource_limit_exceeded', 'resources.' + str(metric['metric']) + '.limit',
                                           metric['limit'], metric['observed'], metric['report_ref']))
    return {'state': 'invalid' if resource_invalid else 'observed' if resources and not resource_reasons else 'unavailable',
            'metrics': resources, 'reasons': resource_reasons if resources else [_reason('resource_not_measured', 'resources')]}


def _receipt_coverage(receipt, configuration, configuration_request, manifest, binding, artifacts, read_artifact, chain):
    """Bind source-owned baseline facts to original work; generic checks grant no quality."""
    import ergora.training.execution_protocol as protocol

    reasons = []
    if receipt is None:
        return [_reason('missing_baseline_receipt', 'receipt')], False
    protocol._exact(receipt, ('schema_version', 'kind', 'binding', 'native_request_sha256', 'runner_sha256',
        'managed', 'configuration_receipt_sha256', 'source', 'baseline_observation_sha256',
        'baseline', 'oracle', 'environment', 'measurement', 'resources'), 'Baseline reference receipt')
    if type(receipt['schema_version']) is not int or receipt['schema_version'] != 1 or receipt['kind'] != 'baseline-reference-receipt':
        raise ValueError('Unsupported baseline reference receipt')
    _artifact_refs(receipt, artifacts)
    if configuration is None or configuration_request is None or chain is None or chain.records['ack'] is None:
        return [_reason('missing_baseline_receipt', 'configuration_binding')], False
    expected = {'binding': binding, 'native_request_sha256': configuration_request['native_request_sha256'],
                'runner_sha256': configuration_request['runner_sha256'], 'managed': configuration_request['managed'],
                'configuration_receipt_sha256': artifacts['configuration-receipt.json']['sha256'],
                'source': configuration_request['configuration_readback']['source'],
                'baseline_observation_sha256': chain.sha(configuration['observations']['baseline'])}
    if any(receipt[key] != value for key, value in expected.items()):
        raise ValueError('Baseline reference receipt differs from its original configuration or execution')
    if (configuration['binding'] != binding or configuration['native_request_sha256'] != chain.records['request']['native_request_sha256']
            or configuration['source'] != expected['source'] or configuration['managed'] != expected['managed']
            or expected['managed'] != {name + '_sha256': chain.sha(chain.records[name]) for name in ('request', 'launch', 'attempt', 'ack')}
            or configuration_request['configuration_readback'] != chain.native['runner']['configuration_readback']
            or configuration['runner_sha256'] != chain.sha(chain.native['runner'])
            or configuration['request_sha256'] != hashlib.sha256(chain.originals[chain.folder.parent / 'configuration-request.json']).hexdigest()
            or configuration_request['binding'] != binding
            or chain.sha(configuration_request['context']) != chain.owner['context_sha256']):
        raise ValueError('Baseline configuration receipt is not bound to its original managed execution')
    baseline, oracle, environment = (receipt[key] for key in ('baseline', 'oracle', 'environment'))
    if isinstance(baseline, dict) and 'core_cpu_execution' in baseline:
        _cpu_window_contract(baseline['core_cpu_execution'], configuration_request)
        from ergora.training.materials import validate_cpu_window_identity
        validate_cpu_window_identity(baseline['core_cpu_execution'], binding=binding,
            native_request_sha256=configuration_request['native_request_sha256'], managed=configuration_request['managed'],
            source=configuration_request['configuration_readback']['source'], execution_phase_id=configuration_request['execution_phase_id'],
            phase='baseline', operation='unprofiled',
            windows=[{key: item['provenance'][key] for key in ('run_id', 'window_id')} for item in receipt['measurement']], require_complete=False)
    if isinstance(baseline, dict) and 'cpu_execution' in baseline:
        from ergora.training.materials import validate_cpu_window_identity
        validate_cpu_window_identity(baseline['cpu_execution'], binding=binding,
            native_request_sha256=configuration_request['native_request_sha256'], managed=configuration_request['managed'],
            source=configuration_request['configuration_readback']['source'], execution_phase_id=configuration_request['execution_phase_id'],
            phase='baseline', operation='unprofiled',
            windows=[{key: item['provenance'][key] for key in ('run_id', 'window_id')} for item in receipt['measurement']], require_complete=False)
    if not isinstance(baseline, dict) or not baseline:
        reasons.append(_reason('missing_actual_workload', 'baseline'))
    else:
        if (baseline.get('commit') != manifest['baseline_commit'] or baseline.get('config_sha256') != manifest['base_config_sha256']
                or baseline.get('invariants') != configuration['observations']['baseline']['invariants']):
            raise ValueError('Baseline actual subject differs from the original baseline or observation')
        for key in ('initialization', 'inputs', 'workload', 'output_refs', 'run_ids'):
            if not baseline.get(key):
                reasons.append(_reason('missing_actual_workload', 'baseline.' + key))
        configuration_ref = baseline.get('configuration_ref')
        if configuration_ref is None:
            reasons.append(_reason('missing_actual_workload', 'baseline.configuration_ref'))
        elif configuration_ref.get('sha256') != manifest['base_config_sha256']:
            raise ValueError('Baseline actual raw configuration differs from its original base_config_sha256')
        workload = baseline.get('workload')
        if isinstance(workload, dict):
            for key in ('global_batch', 'microbatch', 'accumulation'):
                if (type(workload.get(key)) is not int or workload[key] <= 0
                        or workload[key] != configuration['observations']['baseline']['workload'].get(key)):
                    raise ValueError('Baseline actual workload count differs from its constructed configuration: ' + key)
            for key in ('source_samples_per_window', 'source_tokens_per_window', 'optimizer_updates', 'group_count'):
                if key in workload and workload[key] is not None and (type(workload[key]) is not int or workload[key] < 0):
                    raise ValueError('Baseline actual counts require nonnegative integers in their own units')
    if not isinstance(environment, dict) or not environment.get('report_ref'):
        reasons.append(_reason('missing_environment', 'environment'))
    elif read_artifact(environment['report_ref']).get('environment') != environment.get('observed'):
        raise ValueError('Baseline environment report differs from its actual observation')
    if not isinstance(receipt['measurement'], list) or not receipt['measurement']:
        reasons.append(_reason('missing_actual_workload', 'baseline.actual_windows'))
    if not isinstance(oracle, dict) or not oracle:
        reasons.append(_reason('missing_baseline_oracle', 'oracle'))
    else:
        protocol._exact(oracle, ('scheme', 'source_entrypoint', 'validation_contract_sha256', 'subject',
            'coverage', 'status', 'report_ref', 'input_refs', 'expected_refs'), 'Baseline oracle')
        if oracle['status'] not in ('PASS', 'FAIL', 'NOT_RUN'):
            raise ValueError('Baseline oracle has unsupported status')
        if oracle['status'] != 'PASS':
            reasons.append(_reason('oracle_not_run' if oracle['status'] == 'NOT_RUN' else 'oracle_failed', 'oracle.status', 'PASS', oracle['status']))
        else:
            source = receipt['source']
            if (oracle['source_entrypoint'] != source['entrypoint']
                    or oracle['validation_contract_sha256'] != manifest['validation_contract_sha256']):
                raise ValueError('Baseline oracle source or validation contract differs from its trusted source')
            subject = oracle['subject']
            if (not isinstance(subject, dict) or subject.get('arm') != 'baseline'
                    or subject.get('commit') != manifest['baseline_commit']
                    or subject.get('config_sha256') != manifest['base_config_sha256']
                    or subject.get('observation_sha256') != receipt['baseline_observation_sha256']
                    or subject.get('run_ids') != baseline.get('run_ids')
                    or subject.get('windows') != [window['provenance'] for window in receipt['measurement']]):
                raise ValueError('oracle_subject_mismatch: baseline oracle does not describe original baseline work')
            if not oracle['input_refs'] or not oracle['expected_refs'] or not oracle['report_ref']:
                raise ValueError('Baseline PASS oracle requires independent raw input, expected and report artifacts')
            report = read_artifact(oracle['report_ref'])
            if (report.get('kind') != 'baseline-output-oracle' or report.get('status') != 'PASS'
                    or report.get('subject') != subject or report.get('scheme') != oracle['scheme']
                    or report.get('coverage') != oracle['coverage']
                    or report.get('actual_refs') != baseline.get('output_refs')
                    or report.get('input_refs') != oracle['input_refs'] or report.get('expected_refs') != oracle['expected_refs']):
                raise ValueError('Baseline-specific actual oracle report differs from its receipt')
    return reasons, not reasons


def _measurement(receipt, evidence, manifest, artifacts, read_artifact, chain):
    """An archived window is historical; every current full pair still needs current raw work."""
    if receipt is None or not isinstance(receipt.get('measurement'), list) or not receipt['measurement'] or chain is None or chain.records['launch'] is None:
        return [_reason('historical_timing_only', 'measurement', observed='unavailable')]
    comparison = read_artifact(artifacts[evidence['comparison']['input']])
    windows, seen = [], set()
    for pair in comparison['pairs']:
        for arm in ('baseline', 'candidate'):
            item = pair[arm]
            ref = item.get('raw_ref')
            if not isinstance(ref, dict) or artifacts.get(ref.get('path')) != ref:
                raise ValueError('Full comparison requires indexed actual raw windows')
            raw = read_artifact(ref)
            provenance = raw.get('provenance')
            if (not isinstance(provenance, dict) or provenance.get('native_request_sha256') != chain.records['request']['native_request_sha256']
                    or provenance.get('launch_sha256') != chain.sha(chain.records['launch'])
                    or provenance.get('execution_phase_id') != chain.records['launch']['execution_phase_id']
                    or provenance.get('run_id') != item['run_id'] or not provenance.get('window_id')
                    or provenance['window_id'] in seen or raw.get('arm') != arm
                    or raw.get('elapsed_seconds') != item['elapsed_seconds'] or type(raw.get('source_samples')) is not int
                    or raw['source_samples'] != item['source_samples']
                    or raw.get('matched_input_fingerprint') != item['matched_input_fingerprint']
                    or raw.get('measurement_mode') != 'unprofiled' or raw.get('aggregation') != 'global_completion_window'):
                raise ValueError('Full comparison window is not actual work from this managed execution')
            seen.add(provenance['window_id'])
            if arm == 'baseline':
                windows.append({'pair_id': pair['pair_id'], 'order': pair['order'], 'run_id': item['run_id'],
                    'raw_ref': ref, 'provenance': provenance, 'elapsed_seconds': item['elapsed_seconds'],
                    'source_samples': item['source_samples'], 'unit': 'seconds',
                    'measurement_mode': 'unprofiled', 'aggregation': 'global_completion_window'})
    if receipt['measurement'] != windows or receipt['baseline'].get('run_ids') != [item['run_id'] for item in windows]:
        raise ValueError('Baseline measurement receipt differs from the original full pair windows')
    workload = receipt['baseline'].get('workload', {})
    samples = workload.get('source_samples_per_window')
    if samples is not None and (type(samples) is not int or samples <= 0 or any(item['source_samples'] != samples for item in windows)):
        raise ValueError('Baseline actual source samples differ from its measured windows')
    return []


def _reference_projection(projection, selected, request, request_sha256, observations, manifest):
    """The source declares its oracle relation; core keeps quality and timing separate."""
    import ergora.training.execution_protocol as protocol
    import ergora.training.materials as materials

    projection = decode_record(materials.observation_bytes(projection))
    materials._exact(projection, ('scheme', 'baseline_observation_sha256', 'candidate_observation_sha256', 'invariants',
                        'relations', 'allowed_deltas', 'oracle_applicability'), 'Baseline reference projection')
    reference = selected['reference']
    anchor = reference['anchor']
    if (anchor['baseline_commit'] != request['binding']['baseline_sha']
            or anchor['base_config_sha256'] != manifest['base_config_sha256']
            or anchor['workload_fingerprint'] != manifest['workload_fingerprint']
            or anchor['baseline_id'] != manifest['baseline_id']):
        raise ValueError('Baseline reference anchor differs from the current baseline')
    if (not isinstance(projection['scheme'], str) or not projection['scheme']
            or projection['baseline_observation_sha256'] != materials.observation_sha256(observations['baseline'])
            or projection['candidate_observation_sha256'] != materials.observation_sha256(observations['candidate'])
            or projection['invariants'] != observations['baseline']['invariants']):
        raise ValueError('Baseline reference projection differs from the actual configuration observations')
    relations, deltas = projection['relations'], projection['allowed_deltas']
    if not isinstance(relations, list) or not isinstance(deltas, list) or not all(isinstance(key, str) for key in deltas):
        raise ValueError('Baseline reference requires explicit field relations and allowed deltas')
    fields, different, unsupported_units = set(), set(), []
    for relation in relations:
        materials._exact(relation, ('field', 'relation', 'reference', 'current', 'unit'), 'Baseline reference field relation')
        if (not isinstance(relation['field'], str) or not relation['field'] or relation['field'] in fields
                or relation['relation'] not in ('matched', 'different', 'unknown', 'not_applicable')
                or not isinstance(relation['unit'], str) or not relation['unit']):
            raise ValueError('Baseline reference has an unsupported field relation')
        if relation['unit'] not in ('samples', 'tokens', 'updates', 'groups', 'bytes', 'identity', 'not_applicable'):
            unsupported_units.append(relation['field'])
        fields.add(relation['field'])
        if relation['unit'] in ('samples', 'tokens', 'updates', 'groups', 'bytes'):
            if any(value is not None and (type(value) is not int or value < 0)
                   for value in (relation['reference'], relation['current'])):
                raise ValueError('Baseline reference counts must be nonnegative integers in declared units')
        if relation['relation'] == 'matched' and relation['reference'] != relation['current']:
            raise ValueError('Baseline reference claims unequal field values match')
        if relation['relation'] == 'different':
            different.add(relation['field'])
    if len(deltas) != len(set(deltas)) or not set(deltas) <= different:
        raise ValueError('Baseline reference allowed deltas must name actual different fields')
    applicability = projection['oracle_applicability']
    materials._exact(applicability, ('state', 'scheme', 'coverage', 'reasons'), 'Baseline oracle applicability')
    if applicability['state'] not in ('supported', 'unavailable', 'invalid') or not isinstance(applicability['reasons'], list):
        raise ValueError('Unsupported baseline oracle applicability')
    receipt, quality = reference['receipt'], reference['coverage']['quality']
    if receipt is not None and receipt.get('baseline') and receipt['baseline'].get('invariants') != projection['invariants']:
        raise ValueError('Baseline reference changes fixed model, precision or objective invariants')
    if quality.get('state') == 'invalid' or applicability['state'] == 'invalid':
        raise ValueError('Baseline reference is invalid for this target oracle')
    reusable = quality['baseline_scope_verified'] and applicability['state'] == 'supported' and not unsupported_units
    if reusable and (receipt['oracle']['scheme'] != applicability['scheme'] or receipt['oracle']['coverage'] != applicability['coverage']):
        raise ValueError('Baseline reference applicability does not match its actual baseline oracle scope')
    reasons = list(quality['reasons'])
    if unsupported_units:
        reasons.append(_reason('reader_unsupported', 'projection.relation_units', observed=unsupported_units))
    if not reusable:
        reasons.append(_reason('oracle_relation_unsupported', 'projection.oracle_applicability', observed=applicability['state']))
    return {'schema_version': 1, 'kind': 'baseline-reference-read', 'request_sha256': request_sha256,
            'binding': request['binding'], 'selector': request['baseline_reference'],
            'reference_sha256': selected['reference_sha256'], 'anchor_sha256': selected['anchor_sha256'],
            'inventory_sha256': reference['inventory']['sha256'],
            'candidate_observation_sha256': materials.observation_sha256(observations['candidate']), 'projection': projection,
            'quality': {'state': 'reusable' if reusable else 'unavailable', 'coverage': applicability['coverage'] if reusable else None,
                        'reasons': reasons},
            'timing': reference['coverage']['timing'], 'resources': reference['coverage']['resources'],
            'candidate_quality': 'not_evaluated', 'baseline_work_skipped': False,
            'independent_pair_supplied': False, 'promotion_approved': False}


def _baseline_reference(project, control_home, selector, *, inventory=None):
    """Inventory a fixed accepted archive with the same reader in public and managed processes."""
    from dataclasses import asdict
    from perf_temporal.models import Binding, Experiment
    import perfctl
    import ergora.training.execution_protocol as protocol
    from ergora.training.materials import relative, input_descriptor, json_configuration

    inventory = _Inventory() if inventory is None else inventory
    reference_entries = {}

    def read_inventory(root, relative_path, label, expected=None, limit=1_048_576, *, evidence=True, optional=False):
        original = inventory.read(root, relative_path, label, expected, limit, evidence=evidence, optional=optional)
        if original is not None and evidence:
            reference_entries.setdefault(Path(root) / relative_path,
                {'root': label, 'path': relative_path, 'bytes': len(original), 'sha256': hashlib.sha256(original).hexdigest()})
        return original

    project.registration(inventory)
    ident = project.core.slug(selector['experiment_id'])
    protocol._digest(selector['evidence_sha256'])
    prefix = f'training/projects/{project.project["id"]}/perf/experiments/{ident}/'
    archive_prefix = prefix + 'accepted-evidence/' + selector['evidence_sha256'] + '/'

    def read(relative):
        return read_inventory(project.root, relative, 'archive' if relative.startswith(archive_prefix) else 'job')

    def document(relative):
        return decode_record(read(relative))

    manifest_path = prefix + 'manifest.json'
    manifest_raw = read(manifest_path)
    manifest = decode_record(manifest_raw)
    perfctl.validate(manifest)
    if manifest['experiment_id'] != ident or manifest['local_project'] != project.project['id']:
        raise ValueError('Experiment does not belong to this project and native directory')
    manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
    binding = asdict(Binding(ident, manifest_sha, manifest['candidate_commit'], manifest['baseline_commit']))
    frozen_path = 'training/manifests/' + ident + '.json'
    frozen_raw = read(frozen_path)
    if hashlib.sha256(frozen_raw).hexdigest() != manifest_sha:
        raise ValueError('Frozen manifest bytes differ from the project registry')
    frozen = decode_record(frozen_raw)
    if frozen['candidate_sha'] != binding['candidate_sha'] or frozen['baseline_sha'] != binding['baseline_sha']:
        raise ValueError('Manifest commit aliases differ from the original binding')
    spec = document('training/specs/' + ident + '.json')
    experiment = Experiment(**{**spec, 'binding': Binding(**spec['binding'])})
    experiment.validate()
    if (asdict(experiment.binding) != binding or experiment.manifest_uri != (project.root / frozen_path).as_uri()
            or experiment.max_run_seconds != manifest['max_run_seconds']):
        raise ValueError('Experiment spec differs from its frozen manifest binding')
    job_prefix = 'training/jobs/' + ident + '/'
    native = document(job_prefix + 'request.json')
    protocol._exact(native, ('schema_version', 'job_id', 'experiment', 'runner'), 'Native request')
    if (type(native['schema_version']) is not int or native['schema_version'] != 1
            or native['experiment'] != spec or native['job_id'] != 'local-perf-' + ident):
        raise ValueError('Native job request differs from the original experiment')
    runner = native['runner']
    if (runner['runner_template_id'] != manifest['runner_template_id'] or runner['project'] != project.project['id']
            or runner['repo'] != project.project['repo']):
        raise ValueError('Original runner does not belong to the selected project and Git repository')
    try:
        started = document(job_prefix + 'started.json')
    except FileNotFoundError:
        started = None
    result = document(job_prefix + 'result.json')
    for value in (started, result):
        if value is not None and (value['binding'] != binding or value['job_id'] != native['job_id']):
            raise ValueError('Training job result differs from its original request or binding')
    if result['state'] != 'SUCCEEDED' or result.get('gate') is None:
        raise ValueError('Baseline reference requires a successful original accepted job result')
    gate_ref = result['gate']
    gate_path = job_prefix + 'gate-report.json'
    if gate_ref['report'] != str(project.root / gate_path):
        raise ValueError('Gate report is outside the original experiment job')
    gate_raw = read(gate_path)
    if hashlib.sha256(gate_raw).hexdigest() != gate_ref['report_sha256']:
        raise ValueError('Gate report bytes differ from the original result SHA')
    gate = decode_record(gate_raw)
    if gate['binding'] != binding or gate['manifest_sha256'] != manifest_sha:
        raise ValueError('Gate report belongs to another experiment manifest')
    if gate['passed'] is not True or gate['evidence_sha256'] != selector['evidence_sha256']:
        raise ValueError('Baseline reference requires the exact accepted original evidence SHA-256')
    archive, _ = _accepted_archive(project, ident, binding, manifest['baseline_id'], gate, read)
    folder = Path(archive['path'])
    inputs = input_descriptor(manifest)
    if inputs is not None and inputs['kind'] == 'prepared-json':
        for arm in ('baseline', 'candidate'):
            item = inputs[arm]
            raw = read_inventory(project.root, item['path'], 'job', item['sha256'])
            if len(raw) != item['bytes']:
                raise ValueError('Configuration material bytes differ from the original manifest: ' + arm)
            json_configuration(raw)
    fence_raw = read_inventory(project.root, 'training/fences/' + ident + '.json', 'execution', optional=True)
    fence = None if fence_raw is None else decode_record(fence_raw)
    if fence is not None and fence['binding'] != binding:
        raise ValueError('Training fence belongs to another immutable binding')
    artifacts = archive['evidence']['artifacts']
    if len(artifacts) > 256:
        raise ValueError('capacity_exceeded: baseline archive contains more than 256 artifacts')
    indexed = {}
    total = inventory.total
    for item in artifacts:
        # Inspect all ordinary file sizes before consuming the complete index.
        path = folder / relative(item['path'])
        descriptor = protocol._fd(path)
        try:
            size = os.fstat(descriptor).st_size
        finally:
            os.close(descriptor)
        total += 0 if path in inventory.originals else size
        if size > 16 * 1_048_576 or total > 64 * 1_048_576:
            raise ValueError('capacity_exceeded: complete baseline reference archive')
    for item in artifacts:
        protocol._exact(item, ('path', 'sha256'), 'Original artifact index')
        relative(item['path'])
        protocol._digest(item['sha256'])
        raw = read_inventory(folder, item['path'], 'archive', item['sha256'], 16 * 1_048_576)
        indexed[item['path']] = {**item, 'bytes': len(raw)}

    def artifact(ref):
        if indexed.get(ref.get('path')) != ref:
            raise ValueError('Baseline reference has an unindexed transitive artifact')
        raw = inventory.originals[folder / ref['path']][0]
        if len(raw) > 1_048_576:
            raise ValueError('capacity_exceeded: baseline JSON metadata exceeds 1 MiB')
        return decode_record(raw)

    saved = protocol.ExecutionRecords(project.project, ident, control_home)
    required = [*(saved.folder / (name + '.json') for name in ('request', 'launch', 'attempt', 'ack')),
                saved.budget / 'owner.json', *(saved.budget.parent / (ident + suffix) for suffix in ('.intent.json', '.attempt.json', '.result.json'))]
    context_missing = []
    for path in (*required, saved.folder / 'stopped.json'):
        try:
            original = read_inventory(project.root, path.relative_to(project.root).as_posix(),
                'execution' if path.is_relative_to(saved.folder) else 'budget', limit=16 * 1_048_576)
            value = decode_record(original)
            if path == saved.budget / 'owner.json':
                protocol.owner_record(value)
        except FileNotFoundError:
            if path in required:
                context_missing.append(path.relative_to(project.root).as_posix())
    chain = saved.load() if not context_missing else None
    stop = (chain.observe(durable=True) if chain is not None else
            {'reap_record_observed': None, 'executor_stop_confirmed': None, 'durable_stop_confirmed': None})
    if chain is not None:
        for path, raw in chain.originals.items():
            label = 'execution' if path.is_relative_to(chain.folder) else 'budget' if path.is_relative_to(chain.budget.parent) else 'job'
            read_inventory(project.root, path.relative_to(project.root).as_posix(),
                           label, hashlib.sha256(raw).hexdigest(), 16 * 1_048_576)
    configuration_request = None
    try:
        raw = read_inventory(saved.folder.parent, 'configuration-request.json', 'job', limit=16 * 1_048_576)
        if chain is not None:
            chain.originals[chain.folder.parent / 'configuration-request.json'] = raw
        configuration_request = decode_record(raw)
    except FileNotFoundError:
        pass
    # Cycle paths are derived from the original intent; never follow receipt URIs.
    if chain is not None and chain.intent is not None and chain.intent.get('budget') is not None:
        cycle_id = project.core.slug(chain.intent['budget']['cycle_id'])
        cycle = Path(control_home) / 'training-cycles' / project.project['id'] / cycle_id
        for name in ('cycle.json', 'authorization.json', 'ready.json'):
            relative_path = (cycle / name).relative_to(control_home).as_posix()
            try:
                decode_record(read_inventory(Path(control_home), relative_path, 'budget', limit=16 * 1_048_576))
            except FileNotFoundError:
                context_missing.append(relative_path)
        if not context_missing:
            authorization = decode_record(inventory.originals[cycle / 'authorization.json'][0])
            ready = decode_record(inventory.originals[cycle / 'ready.json'][0])
            if (authorization['sha256'] != chain.owner['authorization_sha256']
                    or chain.sha({key: value for key, value in authorization.items() if key != 'sha256'}) != authorization['sha256']
                    or hashlib.sha256(inventory.originals[cycle / 'cycle.json'][0]).hexdigest() != authorization['input_sha256']
                    or chain.sha(ready) != chain.owner['execution_capability']['cycle_ready_sha256']
                    or ready['authorization_sha256'] != authorization['sha256']):
                raise ValueError('Baseline reference cycle authorization or ready binding changed')
    configuration = artifact(indexed['configuration-receipt.json']) if 'configuration-receipt.json' in indexed else None
    receipt = artifact(indexed['baseline-reference-receipt.json']) if 'baseline-reference-receipt.json' in indexed else None
    source_name = 'baseline-reference-execution-sources.json'
    source_manifest = artifact(indexed[source_name]) if source_name in indexed else None
    source_raw = lambda name: inventory.originals[folder / name][0] if name in indexed else None
    capability = chain.owner.get('execution_capability') if chain is not None and chain.owner else None
    source = (protocol.observe_source_manifest(capability, source_manifest,
        source_raw('baseline-reference-protocol-source.py.txt'), source_raw('baseline-reference-native-descriptor.json'))
        if capability else {'state': 'unavailable', 'reasons': ['source_manifest_unavailable']})
    source['reasons'] = [_reason(code, 'execution_source') for code in source['reasons']]
    if source_manifest is not None:
        _artifact_refs(source_manifest, indexed)
    source['manifest_ref'] = indexed.get(source_name)
    quality_reasons, baseline_verified = _receipt_coverage(receipt, configuration, configuration_request, archive['manifest'],
        binding, indexed, artifact, chain)
    if receipt is not None:
        inventory_ref = indexed.get('baseline-reference-source-inventory.raw')
        if inventory_ref is None or inventory_ref['sha256'] != receipt['source']['inventory_sha256']:
            raise ValueError('Baseline trusted driver source inventory is missing or mismatched')
        records = inventory.originals[folder / inventory_ref['path']][0].split(b'\0')
        paths = []
        for record in filter(None, records):
            metadata, name = record.split(b'\t', 1)
            mode, kind, blob = metadata.split(b' ')
            relative(name.decode('utf-8'))
            if mode not in (b'100644', b'100755') or kind != b'blob' or len(blob) != 40:
                raise ValueError('Baseline source inventory contains unsupported tracked objects')
            paths.append(name.decode('utf-8'))
        if receipt['source']['entrypoint'] not in paths or len(paths) != len(set(paths)):
            raise ValueError('Baseline oracle source is absent from its complete inventory')
    facts = {key: stop[key] for key in ('reap_record_observed', 'executor_stop_confirmed', 'durable_stop_confirmed')}
    stopped = chain.records['stopped'] if chain is not None else None
    cleanup_verified = (source['state'] == 'verified' and all(value is True for value in facts.values())
                        and stopped is not None and stopped['process']['status'] == 'succeeded'
                        and stopped['process']['returncode'] == 0 and fence is None and not context_missing)
    if context_missing:
        quality_reasons.append(_reason('reader_unsupported', 'execution_context', 'complete original context', context_missing))
    if source['state'] != 'verified':
        quality_reasons.append(_reason('source_manifest_unavailable', 'execution_source'))
    if not cleanup_verified:
        quality_reasons.append(_reason('cleanup_unconfirmed', 'cleanup', observed=facts))
    timing_reasons = _measurement(receipt, archive['evidence'], archive['manifest'], indexed, artifact, chain)
    if not cleanup_verified:
        timing_reasons.append(_reason('cleanup_unconfirmed', 'cleanup'))
    if receipt is None or not receipt.get('environment'):
        timing_reasons.append(_reason('missing_environment', 'environment'))
    resources = _resource_coverage([] if receipt is None else receipt['resources'], indexed, artifact)
    baseline = archive['baseline']
    anchor = {'baseline_snapshot_sha256': archive['gate_result']['baseline_snapshot_sha256'],
              'baseline_id': baseline['baseline_id'], 'baseline_commit': baseline['commit'],
              'base_config_sha256': baseline['config_sha256'], 'workload_fingerprint': baseline['workload_fingerprint']}
    inventory.confirm()
    entries = sorted(reference_entries.values(), key=lambda item: (item['root'], item['path']))
    if receipt is not None:
        # Locations remain in the authenticated raw receipt/report inventory.
        # The reference exposes their code/build identity without making the
        # original checkout or interpreter pathname part of its projection.
        receipt = {**receipt, 'source': {key: value for key, value in receipt['source'].items() if key != 'repo'}}
        environment = receipt.get('environment')
        if isinstance(environment, dict) and isinstance(environment.get('observed'), dict):
            receipt['environment'] = {**environment, 'observed': {
                key: value for key, value in environment['observed'].items() if key != 'executable'}}
    reference = {'schema_version': 1, 'kind': 'baseline-reference',
        'source': {'project': project.project['id'], 'registration_sha256': project.project['registration']['sha256'],
                   'experiment_id': ident, 'binding': binding, 'evidence_sha256': selector['evidence_sha256'],
                   'gate_report_sha256': hashlib.sha256(gate_raw).hexdigest(),
                   'archive_gate_sha256': hashlib.sha256(inventory.originals[folder / 'gate-result.json'][0]).hexdigest()},
        'anchor': anchor, 'inventory': {'entries': entries, 'sha256': project.sha(entries)}, 'receipt': receipt,
        'coverage': {'inventory': 'complete', 'applicability': 'not_requested', 'execution_source': source,
            'cleanup': {'state': 'verified' if cleanup_verified else 'unavailable', 'original_stop_facts': facts,
                        'stopped_record_present': saved.folder / 'stopped.json' in inventory.originals,
                        'reasons': [] if cleanup_verified else [_reason('cleanup_unconfirmed', 'cleanup')]},
            'quality': {'state': 'invalid' if any(reason['code'] == 'oracle_failed' for reason in quality_reasons) else 'unavailable',
                        'baseline_scope_verified': baseline_verified and not quality_reasons,
                        'reasons': quality_reasons},
            'timing': {'state': 'unavailable' if timing_reasons else 'historical_only', 'reasons': timing_reasons},
            'resources': resources}}
    result = {'reference': reference, 'reference_sha256': project.sha(reference), 'anchor_sha256': project.sha(anchor),
              'read_only': True, 'runtime_status': 'not_queried'}
    # Diagnostics are read only from the original immutable archive. Absence
    # retains the old reference bytes/identity and never triggers recollection.
    if 'profile-receipt.json' in indexed:
        policy = manifest['execution'].get('profile')
        if policy is None or configuration_request is None or chain is None:
            raise ValueError('Baseline diagnostic receipt lacks its original explicit policy/request')
        diagnostics = profile_bundle(folder, policy, request={**configuration_request,
            '_raw_sha256': hashlib.sha256(chain.originals[chain.folder.parent / 'configuration-request.json']).hexdigest()}, inventory=inventory)
        result['diagnostics'] = {key: value for key, value in diagnostics.items() if key != 'inventory'}
    if manifest.get('execution', {}).get('cpu_contract') is not None:
        if configuration_request is None or chain is None:
            raise ValueError('Original CPU contract material has no complete managed configuration context')
        result['cpu_contract'] = cpu_contract_evidence(folder, configuration_request, manifest, inventory=inventory)
        result['cpu_owner'] = {key: chain.owner[key] for key in ('pid', 'start_ticks', 'boot_id')}
        result['cpu_materials'] = {'output': str(folder), 'request': configuration_request, 'manifest': manifest}
    inventory.confirm()
    return result


def baseline_reference(payload):
    from ergora.training.runtime.context import _TrainingProject

    if payload['project'].get('_original_registration') is not None:
        raise ValueError('Baseline reference does not support registration recovery')
    project = _TrainingProject(payload)
    return _baseline_reference(project, payload['control_home'], payload)


def _screen_data(data, request, manifest, read, first_failure):
    """Validate actual source observations and derive only the frozen exploratory result."""
    import ergora.training.execution_protocol as protocol
    from ergora.training.materials import execution_plan

    protocol._exact(data, ('workload', 'windows', 'checks', 'checks_not_run', 'resources', 'artifacts', 'reasons'), 'Screen source report')
    plan = execution_plan(manifest, {'configuration_readback': request['configuration_readback']})['plan']
    workload = data['workload']
    protocol._exact(workload, ('input_plan', 'warmup_work', 'scope'), 'Screen workload')
    protocol._match(workload['input_plan'], plan['input_plan'], 'Screen actual input plan')
    if (type(workload['warmup_work']) is not int or not 0 <= workload['warmup_work'] <= plan['window']['warmup_maximum_work']
            or not isinstance(workload['scope'], dict) or not workload['scope']):
        raise ValueError('Screen workload lacks actual bounded warmup or scope')
    if not isinstance(data['reasons'], list):
        raise ValueError('Screen reasons must be a complete list')
    windows = data['windows']
    if not isinstance(windows, list) or not 1 <= len(windows) <= plan['window']['maximum_windows']:
        raise ValueError('Screen has no complete bounded candidate windows')
    by_window, runs, underwork = {}, set(), False
    for window in windows:
        protocol._exact(window, ('provenance', 'input_ref', 'unit', 'effective_work', 'updates', 'measurement_mode',
                                'aggregation', 'rank_coverage', 'elapsed_seconds', 'raw_ref'), 'Screen window')
        provenance = window['provenance']
        protocol._exact(provenance, ('native_request_sha256', 'launch_sha256', 'execution_phase_id', 'run_id', 'window_id'), 'Screen window provenance')
        if (any(provenance[key] != value for key, value in {'native_request_sha256': request['native_request_sha256'],
                'launch_sha256': request['managed']['launch_sha256'], 'execution_phase_id': request['execution_phase_id']}.items())
                or any(not isinstance(provenance[key], str) or not provenance[key] for key in ('run_id', 'window_id'))
                or provenance['run_id'] in runs or provenance['window_id'] in by_window):
            raise ValueError('Screen window does not belong to this original execution')
        work, elapsed = window['effective_work'], window['elapsed_seconds']
        if (type(work) is not int or not 0 <= work <= plan['window']['maximum_work']
                or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0
                or work > 0 and elapsed <= 0 or window['unit'] != plan['window']['unit']
                or window['measurement_mode'] != 'unprofiled' or window['aggregation'] != 'global_completion_window'
                or not (type(window['updates']) is int and window['updates'] >= 0 or window['updates'] == 'not-applicable')):
            raise ValueError('Screen window has unsupported work, timing or measurement semantics')
        coverage = window['rank_coverage']
        protocol._exact(coverage, ('expected', 'completed'), 'Screen rank coverage')
        if (not isinstance(coverage['expected'], list) or not coverage['expected']
                or any(type(rank) is not int or rank < 0 for rank in coverage['expected'])
                or len(set(coverage['expected'])) != len(coverage['expected'])
                or protocol.CycleAdmission._sha(coverage['completed']) != protocol.CycleAdmission._sha(coverage['expected'])):
            raise ValueError('Screen window lacks global rank completion')
        raw = read(window['raw_ref'])
        protocol._match({key: raw.get(key) for key in window if key != 'raw_ref'},
                        {key: value for key, value in window.items() if key != 'raw_ref'}, 'Screen actual raw window')
        raw_input = read(window['input_ref'])
        protocol._match(raw_input.get('input_plan'), plan['input_plan'], 'Screen raw input identity')
        if type(raw_input.get('effective_work')) is not int or raw_input['effective_work'] != work:
            raise ValueError('Screen raw input effective work differs from its window')
        by_window[provenance['window_id']] = window
        runs.add(provenance['run_id'])
        underwork |= work < plan['window']['minimum_work'] or elapsed <= 0
    if sum(window['elapsed_seconds'] for window in windows) > plan['window']['maximum_seconds']:
        raise ValueError('Screen measured windows exceed their frozen execution walltime')
    expected_checks = {check['id']: check for check in plan['checks']}
    seen, failures = set(), []
    if not isinstance(data['checks'], list) or not isinstance(data['checks_not_run'], list):
        raise ValueError('Screen check coverage is incomplete')
    for check in data['checks']:
        protocol._exact(check, ('id', 'kind', 'contract_sha256', 'subject', 'status', 'report_ref', 'input_refs', 'expected_refs', 'coverage'), 'Screen check result')
        expected = expected_checks.get(check['id'])
        if (expected is None or any(check[key] != expected[key] for key in ('kind', 'contract_sha256'))
                or check['status'] not in ('PASS', 'FAIL') or not isinstance(check['coverage'], dict) or not check['coverage']):
            raise ValueError('Screen check differs from its trusted oracle contract')
        subject = check['subject']
        protocol._exact(subject, ('window_id', 'rank'), 'Screen check subject')
        window = by_window.get(subject['window_id'])
        if window is None or type(subject['rank']) is not int or subject['rank'] not in window['rank_coverage']['completed']:
            raise ValueError('Screen check has no actual candidate window/rank')
        check_key = (check['id'], subject['window_id'], subject['rank'])
        if check_key in seen:
            raise ValueError('Duplicate screen check for the same window and rank')
        if (not isinstance(check['input_refs'], list) or not check['input_refs'] or not isinstance(check['expected_refs'], list)
                or check['kind'] == 'behavior' and not check['expected_refs']):
            raise ValueError('Screen check lacks actual inputs or independent expected outputs')
        for ref in (*check['input_refs'], *check['expected_refs']):
            read(ref, metadata=False)
        report = read(check['report_ref'])
        expected_report = {'kind': 'screen-check', 'check_id': check['id'], 'check_kind': check['kind'],
            **{key: check[key] for key in ('contract_sha256', 'subject', 'status', 'input_refs', 'expected_refs', 'coverage')}}
        protocol._match({key: report.get(key) for key in expected_report}, expected_report, 'Screen original oracle report')
        seen.add(check_key)
        if check['status'] == 'FAIL':
            failures.append(check)
    not_run = data['checks_not_run']
    last_window = windows[-1]['provenance']['window_id']
    last_seen = {key[0] for key in seen if key[1] == last_window}
    if (not all(isinstance(key, str) for key in not_run) or len(set(not_run)) != len(not_run)
            or last_seen & set(not_run) or last_seen | set(not_run) != set(expected_checks)):
        raise ValueError('Screen check coverage omits or duplicates a frozen required check')
    for window in windows[:-1] if failures else windows:
        if window['effective_work'] < plan['window']['minimum_work'] or window['elapsed_seconds'] <= 0:
            raise ValueError('Screen completed window lacks required work before a later failure')
        if any((key, window['provenance']['window_id'], rank) not in seen
               for key in expected_checks for rank in window['rank_coverage']['completed']):
            raise ValueError('Screen required checks do not cover every completed candidate window/rank')
    if failures:
        if first_failure is None:
            raise ValueError('first_failure_unknown: source did not durably record its first failed check')
        failure = first_failure['failure']
        matching = [check for check in failures if check['id'] == failure['check_id'] and
                    check['subject'] == {'window_id': failure['window_id'], 'rank': failure['rank']}]
        if not matching or failure['window_id'] != windows[-1]['provenance']['window_id']:
            raise ValueError('Screen continued candidate windows after its first observed failure')
        for ref in failure['diagnostic_refs']:
            read(ref, metadata=False)
    elif first_failure is not None or underwork or not_run:
        raise ValueError('Screen required work or checks are missing without an observed failure')
    if 'core_cpu_execution' in workload['scope']:
        _cpu_window_contract(workload['scope']['core_cpu_execution'], request)
        from ergora.training.materials import validate_cpu_window_identity
        validate_cpu_window_identity(workload['scope']['core_cpu_execution'], binding=request['binding'],
            native_request_sha256=request['native_request_sha256'], managed=request['managed'],
            source=request['configuration_readback']['source'], execution_phase_id=request['execution_phase_id'],
            phase='screen', operation='unprofiled',
            windows=[{key: item['provenance'][key] for key in ('run_id', 'window_id')} for item in windows], require_complete=False)
    if 'cpu_execution' in workload['scope']:
        from ergora.training.materials import validate_cpu_window_identity
        validate_cpu_window_identity(workload['scope']['cpu_execution'], binding=request['binding'],
            native_request_sha256=request['native_request_sha256'], managed=request['managed'],
            source=request['configuration_readback']['source'], execution_phase_id=request['execution_phase_id'],
            phase='screen', operation='unprofiled',
            windows=[{key: item['provenance'][key] for key in ('run_id', 'window_id')} for item in windows], require_complete=False)
    resources, resource_failure = [], False
    supplied = {}
    if not isinstance(data['resources'], list):
        raise ValueError('Screen resources must be a bounded observation list')
    for metric in data['resources']:
        protocol._exact(metric, ('metric', 'unit', 'scope', 'aggregation', 'state', 'observed', 'report_ref'), 'Screen resource observation')
        if metric['metric'] in supplied:
            raise ValueError('Duplicate screen resource observation')
        supplied[metric['metric']] = metric
    for expected in plan['resources']:
        metric = supplied.pop(expected['metric'], {'metric': expected['metric'], 'unit': expected['unit'], 'scope': expected['scope'],
            'aggregation': expected['aggregation'], 'state': 'NOT_RUN', 'observed': None, 'report_ref': None})
        protocol._match({key: metric[key] for key in ('metric', 'unit', 'scope', 'aggregation')},
                        {key: expected[key] for key in ('metric', 'unit', 'scope', 'aggregation')}, 'Screen resource scope')
        if metric['state'] == 'NOT_RUN':
            if metric['observed'] is not None or metric['report_ref'] is not None or expected['required']:
                raise ValueError('blocked: current required screen resource was not measured')
        elif (metric['state'] != 'OBSERVED' or type(metric['observed']) not in (int, float)
                or not math.isfinite(metric['observed']) or metric['observed'] < 0):
            raise ValueError('Screen resource is not an actual finite measurement')
        else:
            protocol._match(read(metric['report_ref']).get('metric'),
                            {key: value for key, value in metric.items() if key != 'report_ref'}, 'Screen raw resource report')
            resource_failure |= expected['required'] and expected['limit'] is not None and metric['observed'] > expected['limit']
        resources.append({**metric, 'required': expected['required'], 'limit': expected['limit']})
    if supplied:
        raise ValueError('Screen source reported an undeclared resource')
    receipt = read({'path': 'baseline-reference-read.json'})
    projection = read({'path': 'baseline-reference-projection.json'})
    reference = projection['reference']
    protocol._match(projection['reference_sha256'], request['baseline_reference']['reference_sha256'], 'Screen reference selector')
    protocol._match(reference, reference, 'Screen reference')
    if (protocol.CycleAdmission._sha(reference) != projection['reference_sha256']
            or receipt['selector'] != request['baseline_reference'] or receipt['binding'] != request['binding']
            or receipt['reference_sha256'] != projection['reference_sha256']
            or receipt['anchor_sha256'] != projection['anchor_sha256']
            or receipt['request_sha256'] != request['_raw_sha256']):
        raise ValueError('Screen reference read differs from the actual same-context request')
    policy = plan['screening']
    relation = receipt['projection']
    allowed = set(relation['allowed_deltas'])
    comparable = (receipt['quality']['state'] == 'reusable' and receipt['timing']['state'] == 'historical_only'
        and relation['scheme'] == policy['comparison_scheme']
        and all(item['relation'] in ('matched', 'not_applicable') or item['relation'] == 'different' and item['field'] in allowed
                for item in relation['relations']))
    historical = reference.get('receipt')
    environment = historical.get('environment') if isinstance(historical, dict) else None
    comparable &= bool(environment and protocol.CycleAdmission._sha(workload['scope'].get('environment')) == protocol.CycleAdmission._sha(environment.get('observed')))
    rate = (sum(window['effective_work'] for window in windows) / sum(window['elapsed_seconds'] for window in windows)
            if not underwork else None)
    change = None
    if comparable and not failures and not resource_failure:
        if policy['target'] == 'throughput':
            measured = historical.get('measurement', [])
            if measured and all(item['elapsed_seconds'] > 0 for item in measured):
                baseline_rate = sum(item['source_samples'] for item in measured) / sum(item['elapsed_seconds'] for item in measured)
                if plan['window']['unit'] == 'source_samples' and baseline_rate > 0:
                    change = rate / baseline_rate - 1
        else:
            actual = next(item for item in resources if item['metric'] == policy['target'])
            old = next((item for item in receipt['resources']['metrics'] if item['metric'] == policy['target']
                        and all(item[key] == actual[key] for key in ('unit', 'scope', 'aggregation'))), None)
            if receipt['resources']['state'] == 'observed' and old and old['observed'] > 0 and actual['state'] == 'OBSERVED':
                change = 1 - actual['observed'] / old['observed']
    rejected = bool(failures or resource_failure)
    if rejected:
        performance, decision = 'unavailable', 'rejected'
    elif change is None:
        performance, decision = 'unavailable', 'inconclusive'
    elif change <= policy['minimum_improvement_fraction']:
        performance, decision = 'no_gain', 'stop_direction'
    elif change <= policy['minimum_improvement_fraction'] + policy['noise_fraction']:
        performance, decision = 'below_noise', 'stop_direction'
    else:
        performance, decision = 'promising', 'promising'
    return {'requested_tier': 'screened', 'achieved_quality_tier': 'none' if rejected else 'screened',
        'workload': workload, 'windows': windows, 'checks': data['checks'], 'checks_not_run': not_run,
        'resources': resources, 'reference': {key: receipt[key] for key in
            ('selector', 'reference_sha256', 'anchor_sha256', 'inventory_sha256', 'quality', 'timing', 'resources')},
        'performance_state': performance, 'decision': decision, 'throughput': rate, 'change_fraction': change,
        'reasons': data['reasons'] + ([] if comparable else [_reason('comparison_unavailable', 'performance')])}


def _screen_bundle(output, request, manifest, *, inventory=None):
    """Read the same immutable typed content for executor and complete historical readers."""
    import ergora.training.execution_protocol as protocol
    from ergora.training.materials import observation_bytes

    output = Path(output)
    inventory = _Inventory() if inventory is None else inventory
    raw = inventory.read(output, 'screen-result.json', 'screen')
    result = decode_record(raw)
    protocol._match(request['execution'], manifest['execution'], 'Screen request operation')
    protocol._exact(result, ('schema_version', 'kind', 'binding', 'native_request_sha256', 'configuration_request_sha256',
        'runner_sha256', 'managed', 'source', 'execution_plan_sha256', 'configuration_receipt_ref', 'baseline_reference_read_ref',
        'requested_tier', 'achieved_quality_tier', 'workload', 'windows', 'checks', 'checks_not_run', 'first_failure_ref',
        'resources', 'reference', 'performance_state', 'decision', 'throughput', 'change_fraction', 'artifacts', 'reasons'), 'Screen result')
    expected = {'schema_version': 1, 'kind': 'training-screen-result', 'binding': request['binding'],
        'native_request_sha256': request['native_request_sha256'], 'configuration_request_sha256': request['_raw_sha256'],
        'runner_sha256': request['runner_sha256'], 'managed': request['managed'], 'source': request['configuration_readback']['source'],
        'execution_plan_sha256': protocol.CycleAdmission._sha(request['execution']['plan'])}
    protocol._match({key: result[key] for key in expected}, expected, 'Screen result envelope')
    indexed = {}
    if not isinstance(result['artifacts'], list) or not 0 < len(result['artifacts']) <= 256:
        raise ValueError('capacity_exceeded: screen artifact index')
    for item in result['artifacts']:
        protocol._exact(item, ('path', 'sha256', 'bytes'), 'Screen artifact')
        if item['path'] == 'screen-result.json' or item['path'] in indexed or type(item['bytes']) is not int or not 0 <= item['bytes'] <= 16 * 1_048_576:
            raise ValueError('Screen artifact index is duplicate, recursive or exceeds capacity')
        original = inventory.read(output, item['path'], 'screen', item['sha256'], 16 * 1_048_576)
        if len(original) != item['bytes']:
            raise ValueError('Screen artifact length differs from its raw index')
        indexed[item['path']] = item

    projection_path = output / 'baseline-reference-projection.json'
    if projection_path not in inventory.originals:
        raise ValueError('Screen reference projection is missing')
    projected = decode_record(inventory.originals[projection_path][0])
    protocol._exact(projected, ('reference', 'reference_sha256', 'anchor_sha256', 'read_only', 'runtime_status',
        *(['diagnostics'] if 'diagnostics' in projected else []),
        *(['cpu_contract', 'cpu_owner', 'cpu_materials'] if 'cpu_contract' in projected else [])), 'Saved baseline reference projection')
    historical_index = {}
    for entry in projected['reference']['inventory']['entries']:
        if entry['root'] == 'archive':
            item = {key: entry[key] for key in ('path', 'sha256', 'bytes')}
            if item['path'] in historical_index and historical_index[item['path']] != item:
                raise ValueError('Historical baseline reference index is ambiguous')
            historical_index[item['path']] = item
    _artifact_refs(projected['reference']['receipt'], historical_index)
    _artifact_refs(projected['reference']['coverage'], historical_index)

    def read(ref, metadata=True):
        item = indexed.get(ref.get('path'))
        if item is None or len(ref) != 1 and ref != item:
            raise ValueError('Screen report has an unindexed transitive raw reference')
        original = inventory.originals[output / item['path']][0]
        if not metadata:
            return original
        if len(original) > (8 * 1_048_576 if item['path'] == 'baseline-reference-projection.json' else 1_048_576):
            raise ValueError('capacity_exceeded: screen JSON metadata')
        value = decode_record(original)
        if item['path'] == 'baseline-reference-read.json':
            _artifact_refs({key: value[key] for key in ('quality', 'timing', 'resources')}, historical_index)
        elif item['path'] not in ('configuration-receipt.json', 'baseline-reference-projection.json'):
            _artifact_refs(value, indexed)
        return value

    if result['configuration_receipt_ref'] != indexed.get('configuration-receipt.json'):
        raise ValueError('Screen configuration receipt differs from its fixed original path')
    configuration = read(result['configuration_receipt_ref'])
    protocol._match(configuration['request_sha256'], request['_raw_sha256'], 'Screen configuration receipt request')
    for key in ('binding', 'native_request_sha256', 'runner_sha256', 'managed'):
        protocol._match(configuration[key], request[key], 'Screen configuration receipt ' + key)
    for key, value in {'source': request['configuration_readback']['source'],
            'environment_fingerprint': manifest['environment_fingerprint'],
            'execution_plan_sha256': protocol.CycleAdmission._sha(request['execution']['plan']),
            'configurations': request['configurations']}.items():
        protocol._match(configuration[key], value, 'Screen configuration receipt ' + key)
    if result['baseline_reference_read_ref'] != indexed.get('baseline-reference-read.json'):
        raise ValueError('Screen baseline read receipt reference differs from its fixed path')
    reference_read = read(result['baseline_reference_read_ref'])
    projection = read({'path': 'baseline-reference-projection.json'})
    expected_read = _reference_projection(reference_read['projection'], projection, request,
        request['_raw_sha256'], configuration['observations'], manifest)
    protocol._match(reference_read, expected_read, 'Screen same-context baseline read receipt')
    if indexed.get('screen-source-inventory.raw', {}).get('sha256') != request['configuration_readback']['source']['inventory_sha256']:
        raise ValueError('Screen trusted source inventory is missing or changed')
    for index, check in enumerate(request['execution']['plan']['checks']):
        if indexed.get('screen-oracles/' + str(index) + '.raw', {}).get('sha256') != check['contract_sha256']:
            raise ValueError('Screen oracle raw is missing or changed')
    for arm in ('baseline', 'candidate'):
        if indexed.get('screen-configuration-inputs/' + arm + '.raw', {}).get('sha256') != request['configurations'][arm]['source_sha256']:
            raise ValueError('Screen actual configuration raw is missing or changed')
    first = read(result['first_failure_ref']) if result['first_failure_ref'] is not None else None
    if first is not None:
        for key, value in {'kind': 'training-screen-first-failure', 'binding': request['binding'],
                'configuration_request_sha256': request['_raw_sha256'], 'source': request['configuration_readback']['source']}.items():
            protocol._match(first[key], value, 'Screen first failure ' + key)
    data = read({'path': 'screen-source-report.json'})
    _artifact_refs(data, indexed)
    derived = _screen_data(data, request, manifest, read, first)
    protocol._match({key: result[key] for key in derived}, derived, 'Screen derived result')
    observation_bytes(result)
    inventory.confirm()
    bundle = {'result': result, 'raw': raw, 'sha256': hashlib.sha256(raw).hexdigest(),
        'state': 'SCREEN_REJECTED' if result['decision'] == 'rejected' else 'SCREEN_COMPLETED',
        'first_failure': first, 'source_report': data, 'inventory': inventory}
    if request['execution'].get('profile') is not None:
        diagnostics = profile_bundle(output, request['execution']['profile'], request=request, inventory=inventory)
        if diagnostics['receipt_ref'] != indexed.get('profile-receipt.json'):
            raise ValueError('Screen diagnostic receipt is not in its complete original artifact inventory')
        for item in diagnostics['receipt']['captures']:
            if any(indexed.get(item[key]['path']) != item[key] for key in ('raw_ref', 'derived_ref')):
                raise ValueError('Screen diagnostic raw/derived is outside its original artifact inventory')
        bundle['diagnostics'] = {key: value for key, value in diagnostics.items() if key != 'inventory'}
    if request['execution'].get('cpu_contract') is not None:
        bundle['cpu_contract'] = cpu_contract_evidence(output, request, manifest, inventory=inventory)
        bundle['cpu_materials'] = {'output': str(output), 'request': request, 'manifest': manifest}
    inventory.confirm()
    return bundle


def _screen_result(project, ident, control_home, job):
    """Combine typed content with the original managed records and real durable stop."""
    import ergora.training.execution_protocol as protocol

    guards = _Inventory()
    saved = protocol.ExecutionRecords(project.project, ident, control_home)
    for path in (*(saved.folder / (name + '.json') for name in ('request', 'launch', 'attempt', 'ack', 'stopped')),
                 saved.budget / 'owner.json'):
        guards.read(path.parent, path.name, 'execution', limit=16 * 1_048_576, optional=path.name == 'stopped.json')
    chain = saved.load()
    stop = chain.observe(durable=True)
    complete = all(stop[key] is True for key in ('durable_stop_confirmed', 'executor_stop_confirmed', 'reap_record_observed'))
    stopped_process = chain.records['stopped']['process'] if chain.records['stopped'] is not None else None
    complete &= bool(stopped_process and stopped_process['status'] == 'succeeded' and stopped_process['returncode'] == 0)
    def read_guard(path, limit=16 * 1_048_576):
        return guards.read(path.parent, path.name, 'execution', limit=limit)
    native_result = decode_record(read_guard(chain.folder.parent / 'result.json'))
    if native_result['job_id'] != job['job_id'] or native_result['binding'] != job['binding'] or native_result.get('gate') is not None:
        raise ValueError('Screen native result binding or gate is invalid')
    request_raw = read_guard(chain.folder.parent / 'configuration-request.json')
    request = decode_record(request_raw)
    request['_raw_sha256'] = hashlib.sha256(request_raw).hexdigest()
    manifest_raw = read_guard(chain.root / ('training/manifests/' + ident + '.json'))
    if hashlib.sha256(manifest_raw).hexdigest() != job['binding']['manifest_sha']:
        raise ValueError('Screen original manifest raw changed')
    protocol._match(request['binding'], job['binding'], 'Screen original configuration binding')
    protocol._match(request['managed'], {name + '_sha256': chain.sha(chain.records[name]) for name in ('request', 'launch', 'attempt', 'ack')}, 'Screen original managed chain')
    if request['native_request_sha256'] != chain.records['request']['native_request_sha256'] or request['runner_sha256'] != chain.sha(chain.native['runner']):
        raise ValueError('Screen original native request or runner changed')
    bundle = _screen_bundle(chain.folder.parent / 'run-output', request, decode_record(manifest_raw), inventory=guards)
    ref = native_result.get('screen')
    expected = {'report': str(chain.folder.parent / 'run-output/screen-result.json'), 'report_sha256': bundle['sha256']}
    if ref != expected or native_result['state'] != bundle['state']:
        raise ValueError('Screen native result does not pin its original typed content')
    sources = bundle['result']['artifacts']
    indexed = {item['path']: item for item in sources}
    output = chain.folder.parent / 'run-output'
    source_manifest = decode_record(protocol.read_raw(output / 'screen-execution-sources.json'))
    _artifact_refs(source_manifest, indexed)
    observed = protocol.observe_source_manifest(chain.owner['execution_capability'], source_manifest,
        protocol.read_raw(output / 'baseline-reference-protocol-source.py.txt'), protocol.read_raw(output / 'baseline-reference-native-descriptor.json'))
    if observed['state'] != 'verified' or any(item not in indexed for item in
            ('screen-execution-sources.json', 'baseline-reference-protocol-source.py.txt', 'baseline-reference-native-descriptor.json')):
        raise ValueError('Screen original execution source manifest is unavailable or invalid')
    for path, original in chain.originals.items():
        if read_guard(path) != original:
            raise ValueError('Screen original execution chain changed during collection')
    selected = _baseline_reference(project, control_home, request['baseline_reference'], inventory=guards)
    projection_raw = guards.originals[output / 'baseline-reference-projection.json'][0]
    protocol._match(selected, decode_record(projection_raw), 'Screen original baseline inventory after collection')
    guards.confirm()
    if bundle.get('cpu_contract') is not None:
        bundle['cpu_owner'] = {key: chain.owner[key] for key in ('pid', 'start_ticks', 'boot_id')}
    bundle.update(complete=complete, cleanup={**{key: stop[key] for key in ('durable_stop_confirmed', 'executor_stop_confirmed', 'reap_record_observed')},
        'process': stopped_process}, output=str(output))
    return bundle


def _native_screen_read(payload):
    """Fixed no-spawn child body; native parents transmit only their Job and core paths."""
    import ergora.training.execution_protocol as protocol
    from ergora.training.runtime.context import _TrainingProject
    from ergora.training.materials import relative

    root, config = Path(payload['state_directory']), Path(payload['config_directory'])
    if root.resolve() != root or config.resolve() != config:
        raise ValueError('Native reader requires original canonical core paths')
    job = payload['job']
    ident = job['binding']['experiment_id']
    if relative(ident) != ident or '/' in ident:
        raise ValueError('Native reader requires one exact experiment ID')
    folder = root / 'training/jobs' / ident
    native = decode_record(protocol.read_raw(folder / 'request.json', 16 * 1_048_576))
    if native['job_id'] != job['job_id'] or native['experiment']['binding'] != job['binding']:
        raise ValueError('Native reader Job differs from its original request')
    try:
        result = decode_record(protocol.read_raw(folder / 'result.json'))
    except FileNotFoundError:
        result = None
    if result is None:
        return {'job': job, 'state': 'RUNNING' if (folder / 'started.json').exists() else 'QUEUED', 'detail': ''}
    if result['job_id'] != job['job_id'] or result['binding'] != job['binding']:
        raise ValueError('Native result binding changed')
    if payload['operation'] == 'native-poll' and result['state'] not in ('SCREEN_COMPLETED', 'SCREEN_REJECTED'):
        return {'job': job, 'state': result['state'], 'detail': result['detail']}
    request = decode_record(protocol.read_raw(folder / 'configuration-request.json', 16 * 1_048_576))
    context = request['context']
    project = _TrainingProject({'project': context['project'], 'control_home': context['intent']['control_home']})
    if project.root != root or project.config != config or request['binding'] != job['binding']:
        raise ValueError('Native screen reader context differs from its original core paths')
    project.registration()
    if payload['operation'] == 'native-poll':
        chain = protocol.ExecutionRecords(project.project, ident, context['intent']['control_home']).load()
        stopped = chain.observe(durable=True)
        if not all(stopped[key] is True for key in ('durable_stop_confirmed', 'executor_stop_confirmed', 'reap_record_observed')):
            return {'job': job, 'state': 'RUNNING', 'detail': 'screen_result_recorded; cleanup_pending'}
        process = chain.records['stopped']['process']
        if process['status'] != 'succeeded' or process['returncode'] != 0:
            return {'job': job, 'state': 'FAILED', 'detail': 'screen_result_recorded; original executor process failed'}
        return {'job': job, 'state': result['state'], 'detail': result['detail']}
    bundle = _screen_result(project, ident, context['intent']['control_home'], job)
    if not bundle['complete']:
        raise ValueError('Screen cleanup_pending: original durable stop is incomplete')
    return {'job': job, 'state': bundle['state'], 'result_sha256': bundle['sha256'],
        'report_uri': (folder / 'run-output/screen-result.json').as_uri(), 'summary': bundle['result']['decision']}


def main() -> None:
    from agent_platform.core import Blocked
    from ergora.training.runtime.context import _native_bytes

    try:
        raw = sys.stdin.buffer.read(16 * 1_048_576 + 1)
        if len(raw) > 16 * 1_048_576:
            raise ValueError('capacity_exceeded: complete training reader request')
        payload = decode_record(raw)
        if payload['operation'] not in ('inspect', 'baseline-reference', 'native-poll', 'collect-screen'):
            raise ValueError('Unsupported training evidence operation')
        if payload['operation'] in ('native-poll', 'collect-screen'):
            result = _native_screen_read(payload)
        else:
            result = inspect(payload) if payload['operation'] == 'inspect' else baseline_reference(payload)
        sys.stdout.write(_native_bytes(result, 'Training evidence response', 8_388_608).decode('utf-8'))
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error)) from error


if __name__ == '__main__':
    main()


def _failure_actual_identities(actual, plan, ordinal, *, current_context=None, authorization=None):
    """Compare original execution proofs with a separately observed current CPU.

    Original timings/window data establish the old negative's applicability;
    they are never presented as observations of the new unexecuted choice.
    """
    import ergora.training.materials as materials
    from ergora.training.runtime.context import _TrainingProject

    admitted = plan['admissions'][ordinal]['observation']['experiment']
    selector = admitted['manifest']['baseline_reference']
    project = _TrainingProject({'project': plan['project'], 'control_home': plan['control_home']})
    baseline = _baseline_reference(project, plan['control_home'], selector)
    validate_cpu_applicability(baseline, screen=actual)
    # This reader consumes only the original, source-owned raw window proofs.
    # Generic old CPU labels cannot be backfilled by a successful current read.
    original_cpu = cpu_reuse_identity(baseline, actual)
    original_typed = baseline.get('cpu_contract')
    if original_typed is None:
        raise ValueError('unsupported: original baseline has no admitted CPU operation contract')
    state_root = Path(plan['project']['registration']['definition']['execution']['state_directory'])
    current_typed = read_cpu_preparation_admission(state_root, admitted['manifest']['experiment_id'],
        admitted['manifest'], admitted['current_runner'])
    if current_typed is None or current_context is None:
        raise ValueError('unsupported: current CPU admission lacks its original C/A and P/S/H observations')
    current_cpu = protocol.read_cycle_cpu_context(current_context, contract=current_typed['contract'])
    current_material = protocol.read_trial_reference(current_context)
    context_identity = current_material['operation']
    context_plan = decode_record(protocol.read_raw(Path(context_identity['control_home']) / 'training-cycles'
        / context_identity['project'] / context_identity['cycle_id'] / 'cycle.json', protocol.ARTIFACT_LIMIT))
    if (context_plan != plan or context_identity['ordinal'] != ordinal
            or authorization is not None and any(context_identity[key] != authorization[key]
                for key in ('control_home', 'project', 'cycle_id', 'input_sha256', 'authorization_sha256') if key in authorization)):
        raise ValueError('Current CPU context differs from this exact selected birth/ordinal')
    if authorization is not None and context_identity['authorization_sha256'] != authorization['sha256']:
        raise ValueError('Current CPU context differs from its original normal authorization')
    current_environment = current_material['environment']
    original_environment = baseline['reference']['receipt']['environment']['observed']
    protocol._match(actual['result']['workload']['scope']['environment'], original_environment,
        'Original screen and baseline environment')
    if original_environment.get('dependencies') != 'Python standard library':
        raise ValueError('unsupported: historical CPU dependency scope is not the supported stdlib execution')
    output = Path(actual['output'])
    configuration = decode_record(protocol.read_raw(output / 'configuration-receipt.json', protocol.ARTIFACT_LIMIT))
    original_request = decode_record(protocol.read_raw(output.parent / 'configuration-request.json', 16 * protocol.LIMIT))
    reference_read = decode_record(protocol.read_raw(output / 'baseline-reference-read.json', protocol.ARTIFACT_LIMIT))
    observations = configuration['observations']
    validate_cpu_applicability(baseline, observations=observations, screen=actual)
    original_sources = {arm: observations[arm]['source_sha256'] for arm in ('baseline', 'candidate')}
    inputs = materials.require_driver(admitted['manifest'], admitted['current_runner'])
    if inputs is None or inputs['kind'] != 'prepared-json':
        raise ValueError('unsupported: current reuse needs its original complete prepared configuration bytes')
    current_sources = {}
    for arm in ('baseline', 'candidate'):
        raw = protocol.read_raw(state_root / materials.relative(inputs[arm]['path']), protocol.LIMIT)
        materials.json_configuration(raw)
        current_sources[arm] = hashlib.sha256(raw).hexdigest()
        if len(raw) != inputs[arm]['bytes'] or current_sources[arm] != inputs[arm]['sha256']:
            raise ValueError('Current original configuration input changed before known-negative reuse')
    projection = reference_read['projection']
    allowed = set(projection['allowed_deltas'])
    if any(item['relation'] not in ('matched', 'not_applicable') and not (
            item['relation'] == 'different' and item['field'] in allowed) for item in projection['relations']):
        raise ValueError('Historical input/initialization/effective projection is not comparable')
    original = baseline['reference']['receipt']
    if (not original['measurement'] or any(item['measurement_mode'] != 'unprofiled' or
            item['elapsed_seconds'] <= 0 or item['source_samples'] <= 0 for item in original['measurement'])):
        raise ValueError('Historical noise/range lacks actual original unprofiled reference windows')
    if actual['diagnostics']['status'] != 'complete':
        raise ValueError('unsupported: historical reuse has no actual capture/readback window proof')
    original_contract = {key: value for key, value in original_request['execution']['plan'].items()
        if key != 'verification_experiment_id'}
    current_contract = {key: value for key, value in admitted['manifest']['execution']['plan'].items()
        if key != 'verification_experiment_id'}
    # Each side has its own source: original measured request/configuration and
    # window proofs versus current frozen inputs plus fresh physical placement.
    historical = {'cpu_execution': original_cpu, 'environment': original_environment,
        'cpu_contract_sha256': original_typed['contract_sha256'],
        'configuration_sources': original_sources, 'execution_contract': original_contract,
        'baseline_reference_sha256': actual['result']['reference']['reference_sha256']}
    current = {'cpu_execution': current_cpu, 'environment': current_environment,
        'cpu_contract_sha256': current_typed['contract_sha256'],
        'configuration_sources': current_sources, 'execution_contract': current_contract,
        'baseline_reference_sha256': selector['reference_sha256']}
    return current, historical



def _historical_failure(historical: dict, plan: dict, ordinal: int, *, current_context=None, authorization=None) -> str:
    """Authenticate old typed evidence and durable cleanup through their original owners."""
    protocol._exact(historical, ('observation', 'diagnostics', 'cleanup'), 'Historical failure sources')
    observed = protocol.read_trial_reference(historical['observation'])
    diagnostics = protocol.read_trial_reference(historical['diagnostics'])
    protocol._exact(diagnostics, ('profile', 'packet', 'analysis', 'baseline_analysis'), 'Historical complete trial diagnostics')
    cleanup = protocol.read_trial_reference(historical['cleanup'])
    if observed.get('kind') != 'training-cycle-trial-observation':
        raise ValueError('Historical failure requires its complete original typed trial observation')
    experiment = observed['experiment']
    ident = experiment['experiment_id']
    chain = protocol.ExecutionRecords(plan['project'], ident, plan['control_home']).load()
    actual_cleanup = chain.observe(durable=True)
    protocol._match({key: actual_cleanup[key] for key in ('owner', 'records', 'record_sha256', 'raw_sha256')},
        {key: cleanup[key] for key in ('owner', 'records', 'record_sha256', 'raw_sha256')}, 'Historical actual managed cleanup')
    if not all(cleanup.get(key) is True for key in
            ('durable_stop_confirmed', 'executor_stop_confirmed', 'reap_record_observed')):
        raise ValueError('Historical failure cleanup is unknown')
    from ergora.training.runtime.context import _TrainingProject

    project = _TrainingProject({'project': plan['project'], 'control_home': plan['control_home']})
    job = {'job_id': chain.records['request']['job_id'], 'binding': chain.native['experiment']['binding']}
    actual = _screen_result(project, ident, plan['control_home'], job)
    if (not actual['complete'] or actual['result'] != observed['screen'] or
            actual['state'] not in ('SCREEN_COMPLETED', 'SCREEN_REJECTED')):
        raise ValueError('Historical typed screen evidence changed or is incomplete')
    screen = actual['result']
    if actual['state'] == 'SCREEN_COMPLETED' and screen['performance_state'] not in ('no_gain', 'below_noise'):
        raise ValueError('Historical result is not a reusable known negative')
    policy = plan['definition']['profile_policy']
    bundle = profile_bundle(Path(actual['output']), policy)
    checked = validate_trial_diagnostics(bundle, policy)
    protocol._match(checked, protocol.read_trial_reference(diagnostics['profile']), 'Historical actual diagnostic receipt')
    original_cycle = Path(chain.intent['control_home']) / 'training-cycles' / chain.intent['project'] / chain.intent['budget']['cycle_id']
    original_authorization = decode_record(protocol.read_raw(original_cycle / 'authorization.json'))
    original_raw = protocol.read_raw(original_cycle / 'cycle.json', protocol.ARTIFACT_LIMIT)
    original_plan = decode_record(original_raw)
    original_ordinal = chain.intent['budget']['controller']['ordinal']
    if (original_authorization['schema_version'] != 5 or original_plan['definition']['execution_scope'] != protocol.D_SCOPE or
            hashlib.sha256(original_raw).hexdigest() != original_authorization['input_sha256'] or
            protocol.CycleAdmission._sha({key: item for key, item in original_authorization.items() if key != 'sha256'}) != original_authorization['sha256'] or
            chain.intent['budget']['authorization_sha256'] != original_authorization['sha256']):
        raise ValueError('Historical failure lacks its original bounded trial birth and immutable plan')
    protocol._frozen_cycle_materials(original_plan, original_cycle)
    protocol._analysis_receipt(diagnostics['analysis'], original_plan, original_authorization, original_ordinal, 'screen',
        protocol.CycleAdmission._sha(protocol.read_trial_reference(diagnostics['packet'])))
    baseline_diagnostics = diagnostics['baseline_analysis']
    protocol._exact(baseline_diagnostics, ('packet', 'analysis'), 'Historical baseline diagnostics')
    protocol._analysis_receipt(baseline_diagnostics['analysis'], original_plan, original_authorization, -1, 'baseline',
        protocol.CycleAdmission._sha(protocol.read_trial_reference(baseline_diagnostics['packet'])))
    original_report = decode_record(protocol.read_raw(original_cycle / 'controller/trials' / str(original_ordinal) / 'trials.json', protocol.ARTIFACT_LIMIT))
    old_trial = original_report['trials'][original_ordinal]
    protocol.validate_trial_entry(old_trial)
    if (old_trial['kind'] != 'executed' or old_trial['observation'] != historical['observation'] or
            old_trial['sources']['cleanup'] != historical['cleanup'] or old_trial['diagnostics'] != diagnostics or
            old_trial['sources']['intent_sha256'] != protocol.CycleAdmission._sha(chain.intent)):
        raise ValueError('Historical negative diagnostics differ from the original completed trial and fixed slot')
    admitted = plan['admissions'][ordinal]['observation']['experiment']
    current_identity, original_identity = _failure_actual_identities(actual, plan, ordinal,
        current_context=current_context, authorization=authorization)
    current = protocol.trial_failure_fingerprint(admitted['manifest'], admitted['current_runner'],
        plan['search']['plan']['request']['screen_policy'], actual_identity=current_identity)
    previous = protocol.trial_failure_fingerprint(experiment['manifest'], experiment['current_runner'],
        observed['screen_policy'], actual_identity=original_identity)
    if current != previous:
        raise ValueError('Historical failure fingerprint differs from the current effective contract')
    return current



def validate_skip_decision(value: dict, *, plan=None, authorization=None, ordinal=None) -> dict:
    protocol._exact(value, ('schema_version', 'kind', 'protocol', 'control_home', 'project', 'cycle_id',
        'authorization_sha256', 'input_sha256', 'ordinal', 'variant_id', 'stage_map_sha256',
        'experiment_id', 'manifest_sha256', 'current_sources_sha256', 'fingerprint_sha256',
        'historical', 'absence_sha256', 'sha256', *(('current_context',) if 'current_context' in value else ())),
        'Known failure skip decision')
    if (value['schema_version'] != 1 or type(value['schema_version']) is not int or
            value['kind'] != 'training-known-failure-skip' or value['protocol'] != protocol.TRIAL_PROTOCOL
            or type(value['ordinal']) is not int or not 0 <= value['ordinal'] < 32):
        raise ValueError('Unsupported known failure skip decision')
    for key in ('authorization_sha256', 'input_sha256', 'stage_map_sha256', 'manifest_sha256',
                'current_sources_sha256', 'fingerprint_sha256', 'absence_sha256', 'sha256'):
        protocol._digest(value[key])
    if value['sha256'] != protocol.CycleAdmission._sha({key: item for key, item in value.items() if key != 'sha256'}):
        raise ValueError('Skip decision differs from its complete canonical SHA256')
    protocol._exact(value['historical'], ('observation', 'diagnostics', 'cleanup'), 'Historical failure sources')
    if plan is None or authorization is None:
        directory = Path(value['control_home']) / 'training-cycles' / value['project'] / value['cycle_id']
        authorization = decode_record(protocol.read_raw(directory / 'authorization.json'))
        raw = protocol.read_raw(directory / 'cycle.json', protocol.ARTIFACT_LIMIT)
        if hashlib.sha256(raw).hexdigest() != value['input_sha256']:
            raise ValueError('Skip decision lost its original complete cycle input')
        plan = decode_record(raw)
    ordinal = value['ordinal'] if ordinal is None else ordinal
    if (authorization['schema_version'] != 5 or authorization['sha256'] != value['authorization_sha256']
            or plan['definition']['execution_scope'] != protocol.D_SCOPE or ordinal != value['ordinal']):
        raise ValueError('Skip decision requires its current bounded screen birth')
    selected = plan['admissions'][ordinal]
    stage = plan['stage_map'][ordinal]
    expected = {'control_home': authorization['control_home'], 'project': authorization['project'],
        'cycle_id': authorization['cycle_id'], 'input_sha256': authorization['input_sha256'],
        'variant_id': stage['variant_id'], 'stage_map_sha256': protocol.CycleAdmission._sha(plan['stage_map']),
        'experiment_id': selected['experiment_id'], 'manifest_sha256': selected['manifest_sha256'],
        'current_sources_sha256': protocol.CycleAdmission._sha(authorization['measurement_sources'])}
    if any(value[name] != item for name, item in expected.items()):
        raise ValueError('Skip decision changed its original stage, source, parent or selection')
    if value['fingerprint_sha256'] != _historical_failure(value['historical'], plan, ordinal,
            current_context=value.get('current_context'), authorization=authorization):
        raise ValueError('Known failure fingerprint was not recomputed from original raw evidence')
    return value



def make_skip_decision(plan, authorization, ordinal, historical, *, absence_sha256, current_context=None):
    selected, stage = plan['admissions'][ordinal], plan['stage_map'][ordinal]
    value = {'schema_version': 1, 'kind': 'training-known-failure-skip', 'protocol': protocol.TRIAL_PROTOCOL,
        **{key: authorization[key] for key in ('control_home', 'project', 'cycle_id',
            'input_sha256')}, 'authorization_sha256': authorization['sha256'], 'ordinal': ordinal,
        'variant_id': stage['variant_id'], 'stage_map_sha256': protocol.CycleAdmission._sha(plan['stage_map']),
        'experiment_id': selected['experiment_id'], 'manifest_sha256': selected['manifest_sha256'],
        'current_sources_sha256': protocol.CycleAdmission._sha(authorization['measurement_sources']),
        'fingerprint_sha256': _historical_failure(historical, plan, ordinal,
            current_context=current_context, authorization=authorization),
        'historical': historical, 'absence_sha256': absence_sha256}
    if current_context is not None:
        value['current_context'] = current_context
    return validate_skip_decision({**value, 'sha256': protocol.CycleAdmission._sha(value)},
        plan=plan, authorization=authorization, ordinal=ordinal)



def read_skip_decision(execution, experiment_id, *, plan=None, authorization=None, ordinal=None):
    try:
        raw = protocol.read_raw(protocol.skip_decision_path(execution, experiment_id), protocol.ARTIFACT_LIMIT)
    except FileNotFoundError:
        return None
    value = validate_skip_decision(decode_record(raw), plan=plan,
        authorization=authorization, ordinal=ordinal)
    if value['experiment_id'] != experiment_id:
        raise ValueError('Skip decision belongs to a different original experiment')
    if authorization is not None and execution != authorization['execution']:
        raise ValueError('Skip decision belongs to a different original native execution root')
    from ergora.training.materials import confirm_file
    confirm_file(protocol.skip_decision_path(execution, experiment_id), raw, Path(execution['state_directory']))
    if protocol.read_raw(protocol.skip_decision_path(execution, experiment_id), protocol.ARTIFACT_LIMIT) != raw:
        raise ValueError('Original skip decision changed after durable readback')
    return value



def _trial_entry_sources(value, plan, admission, ready, active, *, provisional_operation_id=None):
    authorization, sha = admission.authorization, protocol.CycleAdmission._sha
    ordinal = value['ordinal']
    stage = plan['stage_map'][ordinal]
    if value['variant_id'] != stage['variant_id'] or value['stage_map_sha256'] != sha(plan['stage_map']):
        raise ValueError('Bounded trial changed the complete original stage map')
    if value['kind'] == 'skipped_known_failure':
        decision = protocol.read_trial_reference(value['sources']['decision'])
        validate_skip_decision(decision, plan=plan, authorization=authorization, ordinal=ordinal)
        if value['sources']['historical'] != decision['historical']:
            raise ValueError('Skipped trial changed its historical raw sources')
        actual = read_skip_decision(authorization['execution'], decision['experiment_id'],
            plan=plan, authorization=authorization, ordinal=ordinal)
        protocol._match(actual, decision, 'Original authoritative skip decision')
        active()
        return None
    from ergora.training.runtime.context import _TrainingProject
    observation = protocol.read_trial_reference(value['observation'])
    source = protocol.read_trial_reference(value['sources']['operation'])
    protocol.validate_cycle_operation(source)
    original_plan, original_authorization = protocol.resolve_cycle_snapshot(source)
    selected = plan['admissions'][ordinal]
    chain = protocol.ExecutionRecords(plan['project'], selected['experiment_id'], authorization['control_home']).load()
    intent = chain.intent
    protocol._round_candidate_intent(intent, plan, admission, ordinal)
    protocol._round_sources(authorization, ready, chain.owner)
    execution = chain.observe(durable=True)
    cleanup = protocol.read_trial_reference(value['sources']['cleanup'])
    if (any(execution[key] != cleanup[key] for key in ('owner', 'records', 'record_sha256', 'raw_sha256')) or not all(execution.get(key) is True for key in
            ('durable_stop_confirmed', 'executor_stop_confirmed', 'reap_record_observed'))
            or value['sources']['managed'] != execution['record_sha256'] or
            value['sources']['intent_sha256'] != sha(intent) or
            value['sources']['workflow_id'] != chain.records['request']['workflow_id'] or
            value['sources']['run_id'] != chain.records['request']['run_id'] or
            value['sources']['job_id'] != chain.records['request']['job_id'] or
            value['sources']['native_binding'] != chain.native['experiment']['binding'] or
            source['identity']['ordinal'] != ordinal or original_authorization != authorization or original_plan != plan or
            source['start_context']['controller'] != intent['budget']['controller']):
        raise ValueError('Executed trial lost its fixed source, run, native job or complete real cleanup')
    project = _TrainingProject({'project': plan['project'], 'control_home': authorization['control_home']})
    bundle = _screen_result(project, chain.ident, authorization['control_home'],
        {'job_id': chain.records['request']['job_id'], 'binding': chain.native['experiment']['binding']})
    if (not bundle['complete'] or bundle['state'] not in ('SCREEN_COMPLETED', 'SCREEN_REJECTED') or
            observation['screen'] != bundle['result'] or observation['experiment'] != intent['observation']['experiment']):
        raise ValueError('Executed trial typed result or original input is partial or changed')
    if bundle['state'] == 'SCREEN_COMPLETED' and bundle['result']['performance_state'] not in (
            'promising', 'no_gain', 'below_noise', 'unavailable'):
        raise ValueError('Executed screen is outside the complete continuation allowlist')
    profile = protocol.read_trial_reference(value['diagnostics']['profile'])
    checked = validate_trial_diagnostics(bundle['diagnostics'], plan['definition']['profile_policy'])
    protocol._match(profile, checked, 'Original actual profile/readback receipt')
    packet = protocol.read_trial_reference(value['diagnostics']['packet'])
    original_baseline = _baseline_reference(project, plan['control_home'],
        selected['observation']['experiment']['manifest']['baseline_reference'])
    validate_cpu_applicability(original_baseline, screen=bundle)
    expected_packet = build_analysis_packet(baseline=original_baseline, screen=bundle,
        source_materials=plan['search']['preparation_materials'], policy=plan['definition']['profile_policy'])['packet']
    protocol._match(packet, expected_packet, 'Complete original current screen analysis packet')
    protocol._analysis_receipt(value['diagnostics']['analysis'], plan, authorization, ordinal, 'screen', sha(packet),
        provisional_operation_id=provisional_operation_id)
    baseline = value['diagnostics']['baseline_analysis']
    protocol._exact(baseline, ('packet', 'analysis'), 'Original baseline analyst links')
    protocol._analysis_receipt(baseline['analysis'], plan, authorization, -1, 'baseline',
        sha(protocol.read_trial_reference(baseline['packet'])), provisional_operation_id=provisional_operation_id)
    active()
    return observation, intent, execution



def _trial_predecessors(plan, admission, ready, controller, active, *, provisional_operation_id=None):
    ordinal, predecessor = controller['ordinal'], controller['predecessor']
    if ordinal == 0:
        if predecessor is not None:
            raise ValueError('First bounded trial has no predecessor')
        return []
    protocol.validate_round_predecessor(predecessor, ordinal)
    pin = predecessor['prefix']
    protocol.validate_trial_prefix(pin)
    expected_path = admission.folder / 'trials' / str(ordinal - 1) / 'trials.json'
    if pin['path'] != str(expected_path):
        raise ValueError('Bounded prefix moved outside its original logical ordinal')
    report = protocol.read_trial_reference({key: pin[key] for key in ('path', 'sha256', 'bytes')})
    protocol._exact(report, ('schema_version', 'kind', 'authorization_sha256', 'stage_map_sha256', 'source_operation_id', 'baseline_analysis', 'trials'), 'Bounded trial report')
    if (type(report['schema_version']) is not int or report['schema_version'] != 1 or report['kind'] != 'training-cycle-trial-prefix' or
            report['authorization_sha256'] != admission.authorization['sha256'] or
            report['stage_map_sha256'] != protocol.CycleAdmission._sha(plan['stage_map']) or len(report['trials']) != ordinal):
        raise ValueError('Bounded prefix lost its complete birth, package or logical count')
    raw = protocol.read_raw(expected_path, protocol.ARTIFACT_LIMIT)
    if protocol.trial_pin(expected_path, raw, report) != pin or report['trials'][-1] != predecessor['acceptance']:
        raise ValueError('Bounded prefix differs from its complete raw pin and final trial')
    baseline = report['baseline_analysis']
    protocol._exact(baseline, ('packet', 'analysis'), 'Original baseline analyst links')
    from ergora.training.runtime.context import _TrainingProject
    project = _TrainingProject({'project': plan['project'], 'control_home': plan['control_home']})
    selector = plan['admissions'][0]['observation']['experiment']['manifest']['baseline_reference']
    original_baseline = _baseline_reference(project, plan['control_home'], selector)
    validate_cpu_applicability(original_baseline)
    expected_packet = build_analysis_packet(baseline=original_baseline, screen=None,
        source_materials=plan['search']['preparation_materials'], policy=plan['definition']['profile_policy'])['packet']
    protocol._match(protocol.read_trial_reference(baseline['packet']), expected_packet, 'Complete original baseline analysis packet')
    protocol._analysis_receipt(baseline['analysis'], plan, admission.authorization, -1, 'baseline',
        protocol.CycleAdmission._sha(protocol.read_trial_reference(baseline['packet'])), provisional_operation_id=provisional_operation_id)
    prior, result = None, []
    for index, item in enumerate(report['trials']):
        protocol.validate_trial_entry(item)
        if item['ordinal'] != index or item['predecessor_sha256'] != prior:
            raise ValueError('Bounded prefix omits or changes a logical predecessor')
        snapshot_path = admission.folder / 'trials' / str(index) / 'trials.json'
        snapshot_raw = protocol.read_raw(snapshot_path, protocol.ARTIFACT_LIMIT)
        snapshot = decode_record(snapshot_raw)
        protocol._match(snapshot['trials'], report['trials'][:index + 1], 'Original complete trial snapshot prefix')
        if snapshot['source_operation_id'] != provisional_operation_id:
            proof = protocol.validate_cycle_operation_completion(snapshot['source_operation_id'], admission.authorization)
            protocol._match(proof['prefix'], protocol.trial_pin(snapshot_path, snapshot_raw, snapshot), 'Original S-bound trial snapshot')
        result.append(_trial_entry_sources(item, plan, admission, ready, active, provisional_operation_id=provisional_operation_id))
        prior = item['sha256']
    if protocol.read_raw(expected_path, protocol.ARTIFACT_LIMIT) != raw:
        raise ValueError('Bounded prefix changed during its complete source authentication')
    return result



def authenticate_cycle_binding(binding: dict, plan: dict, admission: protocol.CycleAdmission, ready: dict) -> list:
    """Authenticate a real selected binding without inventing a future intent."""
    authorization, project = admission.authorization, plan['project']
    raw_plan, active = protocol._round_authority(plan, admission, ready)
    _, selected = admission._bound_selection(binding, plan)
    current = protocol.ExecutionRecords(project, selected['experiment_id'], authorization['control_home'])
    for name, expected in project['registration']['files'].items():
        protocol._match(current.document(current.adapter.safe_file(current.config, name)), expected, 'Original registered document')
    protocol._round_sources(authorization, ready, None)
    result = (_trial_predecessors(plan, admission, ready, binding['controller'], active)
        if plan['definition']['execution_scope'] == protocol.D_SCOPE else
        protocol._round_predecessors(plan, admission, ready, binding['controller'], active))
    admission._bound_selection(binding, plan)
    protocol._match(decode_record(protocol.read_raw(admission.directory / 'ready.json')), ready, 'Original cycle ready')
    if protocol.read_raw(admission.directory / 'cycle.json', protocol.ARTIFACT_LIMIT) != raw_plan:
        raise ValueError('Original complete cycle input changed during authentication')
    protocol._round_sources(authorization, ready, None)
    active()
    return result



def authenticate_cycle_candidate(intent: dict, plan: dict, admission: protocol.CycleAdmission, ready: dict) -> list:
    """Authenticate the complete current intent, owner and all predecessors.

    The H additionally checks live archive and runtime eligibility. This pure
    boundary remains independent of State, schemas and the SDK.
    """
    authorization, sha, project = admission.authorization, admission._sha, plan['project']
    raw_plan, active = protocol._round_authority(plan, admission, ready)
    protocol.validate_budget_binding(intent['budget'])
    admission.bind(intent, plan)
    controller = intent['budget']['controller']
    ordinal = controller['ordinal']
    protocol._round_candidate_intent(intent, plan, admission, ordinal)
    current = protocol.ExecutionRecords(project, intent['experiment_id'], authorization['control_home'])
    current_owner = current.document(current.budget / 'owner.json', optional=True)
    intent_path = current.budget.parent / (current.ident + '.intent.json')
    actual_intent = current.document(intent_path, optional=current_owner is None, limit=16 * protocol.LIMIT)
    if actual_intent is not None:
        protocol._match(actual_intent, intent, 'Complete original current candidate intent')
    if current_owner is not None:
        protocol.owner_record(current_owner)
        if (current_owner['intent_sha256'] != sha(intent)
                or current_owner['authorization_sha256'] != authorization['sha256']):
            raise ValueError('Round candidate owner differs from its original intent or authorization')
    for name, expected in project['registration']['files'].items():
        protocol._match(current.document(current.adapter.safe_file(current.config, name)), expected, 'Original registered document')

    active()
    protocol._round_sources(authorization, ready, current_owner)
    result = (_trial_predecessors(plan, admission, ready, controller, active)
        if plan['definition']['execution_scope'] == protocol.D_SCOPE else
        protocol._round_predecessors(plan, admission, ready, controller, active))
    protocol._match(current.document(current.budget / 'owner.json', optional=True), current_owner, 'Original round candidate owner')
    protocol._match(decode_record(protocol.read_raw(admission.directory / 'ready.json')), ready, 'Original cycle ready')
    if protocol.read_raw(admission.directory / 'cycle.json', protocol.ARTIFACT_LIMIT) != raw_plan:
        raise ValueError('Original complete cycle input changed during authentication')
    protocol._round_sources(authorization, ready, current_owner)
    protocol._match(current.document(intent_path, optional=actual_intent is None, limit=16 * protocol.LIMIT), actual_intent,
           'Complete original current candidate intent')
    active()
    return result



def validate_context(context: dict, chain: protocol.ExecutionRecords, *, live=True) -> protocol.CycleAdmission | None:
    """Rebind the complete birth context and its original sources, without State."""
    protocol._exact(context, ('intent', 'authorization', 'policy', 'project', 'published_project',
        *(('cpu_context',) if 'cpu_context' in context else ())), 'Cached execution context')
    owner = chain.owner
    protocol._match(context['intent'], chain.intent, 'Complete cached intent')
    protocol.validate_owner_context(context, owner)
    authorization, policy, intent = (context[name] for name in ('authorization', 'policy', 'intent'))
    if (authorization['sha256'] != chain.sha({key: value for key, value in authorization.items() if key != 'sha256'})
            or authorization['sha256'] != owner['authorization_sha256']):
        raise ValueError('Execution authorization differs from its original complete SHA256')
    cycle = Path(intent['control_home']) / 'training-cycles' / intent['project'] / intent['budget']['cycle_id']
    protocol._match(decode_record(protocol.read_raw(cycle / 'authorization.json')), authorization, 'Original cycle authorization')
    raw = protocol.read_raw(cycle / 'cycle.json', protocol.ARTIFACT_LIMIT)
    if hashlib.sha256(raw).hexdigest() != authorization['input_sha256']:
        raise ValueError('Original complete cycle input changed')
    plan = decode_record(raw)
    protocol.validate_cpu_contract_authority(plan, authorization, intent['experiment_id'])
    protocol.validate_cpu_budget_context(context, expected_budget={name: owner[name] for name in ('pid', 'start_ticks', 'boot_id')})
    protocol.validate_budget_binding(intent['budget'])
    if type(authorization['schema_version']) is not int or authorization['schema_version'] not in (1, 5):
        raise ValueError('Unsupported original execution authorization schema')
    parent = None
    if authorization['schema_version'] == 5:
        parent = protocol.CycleAdmission(cycle, authorization)
        authenticate_cycle_candidate(intent, plan, parent, decode_record(protocol.read_raw(cycle / 'ready.json')))
    elif 'controller' in intent['budget']:
        raise ValueError('Manual authorization cannot acquire a controller binding')
    protocol._match(plan['definition']['budget'], policy, 'Original complete computation policy')
    protocol._match(plan['project'], context['project'], 'Original cycle project')
    ready = decode_record(protocol.read_raw(cycle / 'ready.json'))
    if (chain.sha(ready) != owner['execution_capability']['cycle_ready_sha256']
            or ready['authorization_sha256'] != authorization['sha256']):
        raise ValueError('Original cycle ready record changed')
    budget_clock.validate(authorization['clock'], policy['wall_seconds'])
    registration = context['published_project']['registration']
    for name, expected in registration['files'].items():
        protocol._match(chain.document(chain.adapter.safe_file(chain.config, name)), expected, 'Original registered document')
    observed = intent['observation']
    for name, expected in {**observed['baseline_files'], **observed['experiment']['files']}.items():
        prefix, relative = name.split('/', 1)
        root = chain.root if prefix == 'state' else chain.config if prefix == 'config' else None
        if root is None or hashlib.sha256(protocol.read_raw(chain.adapter.safe_file(root, relative))).hexdigest() != expected:
            raise ValueError('Original experiment source changed: ' + name)
    protocol.validate_sources(owner['execution_capability'])
    if live and (not protocol.owner_active(chain.budget / 'owner.json', owner)
            or budget_clock.remaining(authorization['clock'], policy['wall_seconds'], policy['cleanup_seconds']) <= 0):
        raise ValueError('Original execution owner or computation budget is no longer active')
    if live and parent is not None:
        parent.check()
    return parent



def read_cpu_preparation_admission(root, ident, manifest, runner):
    """Read original fixed I/A, without application State, SDK or live observation."""
    import re
    import ergora.training.materials as materials
    if materials.cpu_contract(manifest) is None:
        return None
    if not isinstance(ident, str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', ident) is None:
        raise ValueError('CPU admission requires its original experiment ID')
    if manifest.get('experiment_id') != ident:
        raise ValueError('CPU original admission path differs from its experiment binding')
    root, inventory = Path(root), _Inventory()
    prefix = 'ergora/training-preparations/' + ident
    intent_raw = inventory.read(root, prefix + '.intent.json', 'cpu-preparation', limit=16 * 1_048_576)
    admission_raw = inventory.read(root, prefix + '.cpu-contract-admission.json', 'cpu-preparation', limit=1_048_576)
    manifest_raw = inventory.read(root, 'training/manifests/' + ident + '.json', 'cpu-preparation', limit=16 * 1_048_576)
    if materials.decode_record(manifest_raw) != manifest:
        raise ValueError('CPU preparation manifest changed from its original observation')
    intent, admission = materials.decode_record(intent_raw), materials.decode_record(admission_raw)
    contract = materials.validate_cpu_preparation_admission(admission, intent, manifest_raw, runner)
    original_body = materials.preparation_preview_body(intent)
    if original_body['execution'].get('state_directory') != str(root):
        raise ValueError('CPU original preparation execution root differs from native storage')
    checked = materials.validate_preparation_intent(intent)
    for name, original in ((prefix + '.intent.json', intent_raw),
                           (prefix + '.cpu-contract-admission.json', admission_raw),
                           ('training/manifests/' + ident + '.json', manifest_raw)):
        materials.confirm_file(root / name, original, root)
    inventory.confirm()
    return {'contract': contract, 'contract_sha256': contract['sha256'], 'intent': intent, 'intent_raw': intent_raw,
            'admission': admission, 'admission_raw': admission_raw,
            'preview_sha256': checked['preview_sha256'], 'intent_sha256': checked['intent_sha256']}

