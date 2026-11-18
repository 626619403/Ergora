"""Observe original content-addressed training evidence without evaluating or releasing it."""

import hashlib
import json
import math
import os
from pathlib import Path
import sys

from .reference import _training_records


def _accepted_archive(project, ident, binding, baseline_id, gate, read):
    """Verify original accepted metadata for the diagnostic and full-inventory readers."""
    import perfctl
    from . import training_execution_protocol as protocol

    evidence_sha = gate['evidence_sha256']
    perfctl.sha(evidence_sha, 'evidence_sha256')
    prefix = f'training/projects/{project.project["id"]}/perf/experiments/{ident}/accepted-evidence/{evidence_sha}/'
    archive = project.adapter.safe_file(project.root, prefix[:-1])

    def document(name):
        raw = read(prefix + name)
        value = protocol.decode(raw)
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
    from .reference_training_context import _TrainingProject
    from .training_materials import read_raw

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
              'integration_ticket': None, 'files': files,
              'artifact_limit_bytes': 16_777_216, 'response_limit_bytes': 8_388_608,
              'scope': 'Saved native records only; no live phase, statistical re-evaluation, artifact-wide verification, authorization or integration completion claim'}
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


class _Inventory:
    """One complete read, retaining original path/inode/raw identity until its final check."""

    def __init__(self):
        self.originals = {}
        self.absences = set()
        self.presence_guards = set()
        self.total = 0

    def read(self, root, relative, label, expected=None, limit=1_048_576, *, evidence=True, optional=False):
        from . import training_execution_protocol as protocol
        from .training_materials import relative as canonical_relative

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
        from . import training_execution_protocol as protocol

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
    from . import training_execution_protocol as protocol

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
    from . import training_execution_protocol as protocol

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


def _baseline_reference(project, control_home, selector):
    """Inventory a fixed accepted archive with the same reader in public and managed processes."""
    from dataclasses import asdict
    from perf_temporal.models import Binding, Experiment
    import perfctl
    from . import training_execution_protocol as protocol
    from .training_materials import relative, input_descriptor, json_configuration

    inventory = _Inventory()
    project.registration(inventory)
    ident = project.core.slug(selector['experiment_id'])
    protocol._digest(selector['evidence_sha256'])
    prefix = f'training/projects/{project.project["id"]}/perf/experiments/{ident}/'
    archive_prefix = prefix + 'accepted-evidence/' + selector['evidence_sha256'] + '/'

    def read(relative):
        return inventory.read(project.root, relative, 'archive' if relative.startswith(archive_prefix) else 'job')

    def document(relative):
        return protocol.decode(read(relative))

    manifest_path = prefix + 'manifest.json'
    manifest_raw = read(manifest_path)
    manifest = protocol.decode(manifest_raw)
    perfctl.validate(manifest)
    if manifest['experiment_id'] != ident or manifest['local_project'] != project.project['id']:
        raise ValueError('Experiment does not belong to this project and native directory')
    manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
    binding = asdict(Binding(ident, manifest_sha, manifest['candidate_commit'], manifest['baseline_commit']))
    frozen_path = 'training/manifests/' + ident + '.json'
    frozen_raw = read(frozen_path)
    if hashlib.sha256(frozen_raw).hexdigest() != manifest_sha:
        raise ValueError('Frozen manifest bytes differ from the project registry')
    frozen = protocol.decode(frozen_raw)
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
    gate = protocol.decode(gate_raw)
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
            raw = inventory.read(project.root, item['path'], 'job', item['sha256'])
            if len(raw) != item['bytes']:
                raise ValueError('Configuration material bytes differ from the original manifest: ' + arm)
            json_configuration(raw)
    fence_raw = inventory.read(project.root, 'training/fences/' + ident + '.json', 'execution', optional=True)
    fence = None if fence_raw is None else protocol.decode(fence_raw)
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
        total += size
        if size > 16 * 1_048_576 or total > 64 * 1_048_576:
            raise ValueError('capacity_exceeded: complete baseline reference archive')
    for item in artifacts:
        protocol._exact(item, ('path', 'sha256'), 'Original artifact index')
        relative(item['path'])
        protocol._digest(item['sha256'])
        raw = inventory.read(folder, item['path'], 'archive', item['sha256'], 16 * 1_048_576)
        indexed[item['path']] = {**item, 'bytes': len(raw)}

    def artifact(ref):
        if indexed.get(ref.get('path')) != ref:
            raise ValueError('Baseline reference has an unindexed transitive artifact')
        raw = inventory.originals[folder / ref['path']][0]
        if len(raw) > 1_048_576:
            raise ValueError('capacity_exceeded: baseline JSON metadata exceeds 1 MiB')
        return protocol.decode(raw)

    saved = protocol.ExecutionRecords(project.project, ident, control_home)
    required = [*(saved.folder / (name + '.json') for name in ('request', 'launch', 'attempt', 'ack')),
                saved.budget / 'owner.json', *(saved.budget.parent / (ident + suffix) for suffix in ('.intent.json', '.attempt.json', '.result.json'))]
    context_missing = []
    for path in (*required, saved.folder / 'stopped.json'):
        try:
            original = inventory.read(project.root, path.relative_to(project.root).as_posix(),
                'execution' if path.is_relative_to(saved.folder) else 'budget', limit=16 * 1_048_576)
            value = protocol.decode(original)
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
            inventory.read(project.root, path.relative_to(project.root).as_posix(),
                           label, hashlib.sha256(raw).hexdigest(), 16 * 1_048_576)
    configuration_request = None
    try:
        raw = inventory.read(saved.folder.parent, 'configuration-request.json', 'job', limit=16 * 1_048_576)
        if chain is not None:
            chain.originals[chain.folder.parent / 'configuration-request.json'] = raw
        configuration_request = protocol.decode(raw)
    except FileNotFoundError:
        pass
    # Cycle paths are derived from the original intent; never follow receipt URIs.
    if chain is not None and chain.intent is not None and chain.intent.get('budget') is not None:
        cycle_id = project.core.slug(chain.intent['budget']['cycle_id'])
        cycle = Path(control_home) / 'training-cycles' / project.project['id'] / cycle_id
        for name in ('cycle.json', 'authorization.json', 'ready.json'):
            relative_path = (cycle / name).relative_to(control_home).as_posix()
            try:
                protocol.decode(inventory.read(Path(control_home), relative_path, 'budget', limit=16 * 1_048_576))
            except FileNotFoundError:
                context_missing.append(relative_path)
        if not context_missing:
            authorization = protocol.decode(inventory.originals[cycle / 'authorization.json'][0])
            ready = protocol.decode(inventory.originals[cycle / 'ready.json'][0])
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
    entries = inventory.index()
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
    from .reference_training_context import _TrainingProject

    if payload['project'].get('_original_registration') is not None:
        raise ValueError('Baseline reference does not support registration recovery')
    project = _TrainingProject(payload)
    return _baseline_reference(project, payload['control_home'], payload)


def main() -> None:
    from agent_platform.core import Blocked
    from .reference_training_context import _native_bytes

    try:
        payload = json.load(sys.stdin)
        if payload['operation'] not in ('inspect', 'baseline-reference'):
            raise ValueError('Unsupported training evidence operation')
        result = inspect(payload) if payload['operation'] == 'inspect' else baseline_reference(payload)
        sys.stdout.write(_native_bytes(result, 'Training evidence response', 8_388_608).decode('utf-8'))
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error)) from error


if __name__ == '__main__':
    main()
