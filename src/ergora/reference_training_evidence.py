"""Observe original content-addressed training evidence without evaluating or releasing it."""

import hashlib
import json
import sys

from .reference import _training_records
from .reference_training_context import _native_bytes, _TrainingProject


def inspect(payload: dict) -> dict:
    import perfctl

    project = _TrainingProject(payload)
    project.registration()
    ident = project.core.slug(payload['experiment_id'])
    observed = _training_records({'project': project.project['id'], 'repo': project.project['repo'],
                                  'experiment_id': ident})
    experiment = observed['experiment']
    binding, gate = experiment['binding'], experiment['gate_report']
    files = {**observed['baseline_files'], **experiment['files']}

    def document(relative: str) -> dict:
        raw = project.adapter.read_raw(project.adapter.safe_file(project.root, relative))
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('Training evidence record must be a JSON object: ' + relative)
        files['state/' + relative] = hashlib.sha256(raw).hexdigest()
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
    evidence_sha = gate['evidence_sha256']
    perfctl.sha(evidence_sha, 'evidence_sha256')
    prefix = f'training/projects/{project.project["id"]}/perf/experiments/{ident}/accepted-evidence/{evidence_sha}/'
    archive = project.adapter.safe_file(project.root, prefix[:-1])
    archive_gate = document(prefix + 'gate-result.json')
    if project.sha(gate['archive_report']) != project.sha({**archive_gate, 'archive_path': str(archive)}):
        raise ValueError('Archived gate differs from the original job gate report')
    expected = {'status': 'ELIGIBLE_FOR_HUMAN_REVIEW', 'experiment_id': ident,
                'baseline_id': experiment['baseline_id'], 'candidate_commit': binding['candidate_sha'],
                'manifest_sha256': binding['manifest_sha'], 'evidence_sha256': evidence_sha}
    if any(archive_gate.get(key) != value for key, value in expected.items()):
        raise ValueError('Archived gate belongs to another evidence or experiment')
    evidence = document(prefix + 'evidence.json')
    if files['state/' + prefix + 'evidence.json'] != evidence_sha:
        raise ValueError('Archived evidence bytes differ from their original content address')
    expected.pop('status')
    expected.pop('evidence_sha256')
    if (type(evidence.get('schema_version')) is not int or evidence['schema_version'] != 1
            or any(evidence.get(key) != value for key, value in expected.items())):
        raise ValueError('Archived evidence belongs to another manifest or experiment')
    manifest = document(prefix + '_archive_meta/manifest.json')
    if files['state/' + prefix + '_archive_meta/manifest.json'] != binding['manifest_sha']:
        raise ValueError('Archived manifest bytes differ from the original binding')
    baseline = document(prefix + '_archive_meta/baseline.json')
    if files['state/' + prefix + '_archive_meta/baseline.json'] != archive_gate['baseline_snapshot_sha256']:
        raise ValueError('Archived baseline bytes differ from the original gate snapshot')
    perfctl.baseline_ok(manifest, baseline)
    comparator = project.adapter.read_raw(project.adapter.safe_file(project.root, prefix + '_archive_meta/compare_runs.py'))
    comparator_sha = hashlib.sha256(comparator).hexdigest()
    if comparator_sha != manifest['comparison_tool_sha256']:
        raise ValueError('Archived comparator differs from the original manifest')
    files['state/' + prefix + '_archive_meta/compare_runs.py'] = comparator_sha

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
    result.update(archive_status='recorded', archive={'evidence_sha256': evidence_sha, 'path': str(archive),
                  'evidence': evidence, 'gate_result': archive_gate, 'manifest': manifest, 'baseline': baseline,
                  'comparator_sha256': comparator_sha, 'artifact_content_status': 'not_read'})
    if payload['artifact'] is not None:
        if payload['evidence_sha256'] != evidence_sha:
            raise ValueError('Artifact read requires the exact observed evidence SHA-256')
        item = artifacts.get(payload['artifact'])
        if item is None:
            raise ValueError('Selected artifact is absent from the original evidence index')
        raw = project.adapter.read_raw(project.adapter.safe_file(project.root, prefix + item['path']), 16_777_216)
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


def main() -> None:
    from agent_platform.core import Blocked

    try:
        result = inspect(json.load(sys.stdin))
        sys.stdout.write(_native_bytes(result, 'Training evidence response', 8_388_608).decode('utf-8'))
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error)) from error


if __name__ == '__main__':
    main()
