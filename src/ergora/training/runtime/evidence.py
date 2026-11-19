"""Observe original content-addressed training evidence without evaluating or releasing it."""

import hashlib
import json
import math
import os
from pathlib import Path
import sys

from ergora.training.native import _training_records
from ergora.training.materials import decode_record


def _accepted_archive(project, ident, binding, baseline_id, gate, read):
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
    if manifest.get('execution') not in (None, {'operation': 'full-verify'}):
        raise ValueError('Accepted archive requires original full verification')
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
        with os.fdopen(descriptor, 'rb') as stream:
            details = os.fstat(stream.fileno())
            if details.st_size > limit or self.total + (0 if path in self.originals else details.st_size) > 64 * 1_048_576:
                raise ValueError('capacity_exceeded: complete baseline reference inventory')
            chunks, length, digest = [], 0, hashlib.sha256()
            while chunk := stream.read(min(65_536, limit + 1 - length)):
                chunks.append(chunk)
                length += len(chunk)
                digest.update(chunk)
                if length > limit:
                    break
            raw = b''.join(chunks)
            if len(raw) > limit:
                raise ValueError('capacity_exceeded: complete baseline reference artifact')
        digest = digest.hexdigest()
        if path in self.absences:
            raise ValueError('archive_changed: original baseline reference absence changed')
        if expected is not None and digest != expected:
            raise ValueError('archive_changed: original baseline reference digest differs: ' + relative)
        if path in self.originals:
            original, device, inode, record = self.originals[path]
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
    from ergora.training import materials

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
    return {'reference': reference, 'reference_sha256': project.sha(reference), 'anchor_sha256': project.sha(anchor),
            'read_only': True, 'runtime_status': 'not_queried'}


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
    protocol._exact(projected, ('reference', 'reference_sha256', 'anchor_sha256', 'read_only', 'runtime_status'), 'Saved baseline reference projection')
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
        if len(original) > 1_048_576:
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
    return {'result': result, 'raw': raw, 'sha256': hashlib.sha256(raw).hexdigest(),
        'state': 'SCREEN_REJECTED' if result['decision'] == 'rejected' else 'SCREEN_COMPLETED', 'inventory': inventory}


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
