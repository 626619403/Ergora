"""Immutable links between original training observations; never a new gate."""

import hashlib
import json
from pathlib import Path
import stat
import tempfile

from . import contracts, training
from .asset_trees import is_link, publish_directory
from .definition_bundles import parse_json
from .state import State


MAX_INDEX_BYTES = 10_000_000
_SCHEMA = json.loads((Path(__file__).parent / 'data/schemas/training-rounds-v1.json').read_text(encoding='utf-8'))
_COVERAGE = {'records': 'saved-observations', 'artifacts': 'index-only', 'runtime_status': 'not_queried',
             'authorization_status': 'not_evaluated', 'origin_authenticated': False,
             'execution_success': None, 'promotion_approved': False}


def _encoded(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def _sha(value: dict) -> str:
    return hashlib.sha256(_encoded(value)).hexdigest()


def _comparison(records: dict) -> dict:
    experiment = records['experiment']
    manifest = experiment['manifest']
    return {'baseline_id': manifest['baseline_id'], 'baseline_commit': manifest['baseline_commit'],
            'base_config_sha256': manifest['base_config_sha256'],
            'workload_fingerprint': manifest['workload_fingerprint'],
            'candidate_commit': manifest['candidate_commit'],
            'candidate_config_sha256': manifest['candidate_config_sha256'],
            'manifest_sha256': experiment['binding']['manifest_sha']}


def _anchor(comparison: dict) -> dict:
    return {key: comparison[key] for key in ('baseline_id', 'baseline_commit',
                                             'base_config_sha256', 'workload_fingerprint')}


def _check(report: dict) -> None:
    contracts.validate(report, {'$defs': _SCHEMA['$defs'], '$ref': '#/$defs/report'}, 'Training round index')
    if report['coverage'] != _COVERAGE:
        raise ValueError('Training round index cannot grant execution, authorization or promotion')
    parent, seen = None, set()
    for item in report['rounds']:
        content = {key: value for key, value in item.items() if key != 'sha256'}
        if item['parent_sha256'] != parent or item['sha256'] != _sha(content):
            raise ValueError('Training round content or predecessor link differs from its SHA256')
        parent = item['sha256']
        if item['experiment_id'] in seen:
            raise ValueError('Training round index contains the same original experiment twice')
        seen.add(item['experiment_id'])
        native = item['native']
        records, evidence, submission, approval = (native[key] for key in ('records', 'evidence', 'submission', 'approval'))
        experiment = records['experiment']
        binding = experiment['binding']
        revision = records['project_revision']
        for view in (records, evidence, submission, *([approval] if approval is not None else [])):
            if view['project'] != report['project']['id'] or view['project_revision'] != revision:
                raise ValueError('Training round observations belong to different projects or revisions')
        if (experiment['experiment_id'] != item['experiment_id'] or binding['experiment_id'] != item['experiment_id']
                or any(view['experiment_id'] != item['experiment_id'] for view in (evidence, submission))
                or evidence['binding'] != binding or evidence['recorded_gate_report'] != experiment['gate_report']):
            raise ValueError('Training round observations have different original experiment bindings or gates')
        files = {**records['baseline_files'], **experiment['files']}
        if any(evidence['files'].get(name) != digest for name, digest in files.items()):
            raise ValueError('Training sources changed between the original record and evidence observations')
        if (item['comparison'] != _comparison(records)
                or item['comparison']['candidate_commit'] != binding['candidate_sha']
                or item['comparison']['baseline_commit'] != binding['baseline_sha']):
            raise ValueError('Training round comparison differs from its original manifest')
        if _anchor(item['comparison']) != report['initial_anchor']:
            raise ValueError('Training round index requires one reviewed initial baseline; baseline migration is separate')
        if submission['status'] in ('prepared', 'unknown', 'submitted') and (
                submission['manifest_sha256'] != binding['manifest_sha']
                or submission['confirmation']['binding'] != binding):
            raise ValueError('Training round submission names a different original manifest')
        if submission['status'] == 'submitted':
            if (approval is None or approval['experiment_id'] != item['experiment_id']
                    or approval['run_id'] != submission['run_id']):
                raise ValueError('Training round approval must observe the original submitted run')
        elif approval is not None:
            raise ValueError('Training round approval is not evaluated for an unresolved or unsubmitted ingress')
    previous = report['previous_report']
    if previous is not None and (not 1 <= previous['rounds'] < len(report['rounds'])
            or previous['last_round_sha256'] != report['rounds'][previous['rounds'] - 1]['sha256']):
        raise ValueError('Training round extension does not retain its declared original prefix')


def read(directory: Path, *, sha256: str | None = None) -> dict:
    """Verify frozen values and links offline; do not authenticate native origin."""
    directory = directory.expanduser().absolute()
    if is_link(directory) or not directory.is_dir() or {path.name for path in directory.iterdir()} != {'rounds.json'}:
        raise ValueError('Training round directory must contain exactly one ordinary rounds.json')
    path = directory / 'rounds.json'
    if is_link(path) or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('Training round index requires an ordinary file')
    with path.open('rb') as stream:
        raw = stream.read(MAX_INDEX_BYTES + 1)
    if len(raw) > MAX_INDEX_BYTES:
        raise ValueError('Complete training round index exceeds 10 MB')
    digest = hashlib.sha256(raw).hexdigest()
    if sha256 is not None and sha256 != digest:
        raise ValueError('Training round index differs from the expected SHA256')
    report = parse_json(raw.decode('utf-8'), 'training round index')
    _check(report)
    return {'directory': str(directory), 'sha256': digest, 'report': report}


def create(state: State, project_id: str, definition: dict, destination: Path, *,
           previous: Path | None = None, previous_sha256: str | None = None) -> dict:
    """Capture selected original records, preserving an explicitly pinned prefix."""
    contracts.validate(definition, _SCHEMA, 'Training round request')
    if (previous is None) != (previous_sha256 is None):
        raise ValueError('Training round extension requires both the previous directory and its exact SHA256')
    project = training._project(state, project_id)
    identity = {'id': project_id, 'repo': project['repo'], 'registration_sha256': project['registration']['sha256']}
    original = read(previous, sha256=previous_sha256) if previous is not None else None
    if original is not None and original['report']['project'] != identity:
        raise ValueError('Training round extension belongs to another registered project or repository')
    rounds = list(original['report']['rounds']) if original else []
    selected = [item['experiment_id'] for item in rounds] + [item['experiment_id'] for item in definition['rounds']]
    if len(selected) != len(set(selected)):
        raise ValueError('Select each original training experiment once')
    if len(selected) > _SCHEMA['$defs']['report']['properties']['rounds']['maxItems']:
        raise ValueError('Training round index exceeds its 32-round capacity')
    for requested in definition['rounds']:
        ident = requested['experiment_id']
        records = training.inspect(state, project_id, ident)
        evidence = training.evidence(state, project_id, ident)
        submission = training.submission(state, project_id, ident)
        approval = training.approval(state, project_id, ident) if submission['status'] == 'submitted' else None
        content = {'experiment_id': ident, 'parent_sha256': rounds[-1]['sha256'] if rounds else None,
                   'annotation': {key: requested[key] for key in ('change', 'next_bottleneck')},
                   'comparison': _comparison(records),
                   'native': {'records': records, 'evidence': evidence, 'submission': submission, 'approval': approval}}
        rounds.append({**content, 'sha256': _sha(content)})
    if state.project(project_id)['revision'] != project['revision']:
        raise ValueError('Project changed while capturing training observations; no index was published')
    report = {'schema_version': 1, 'kind': 'training-round-index', 'project': identity,
              'initial_anchor': original['report']['initial_anchor'] if original else _anchor(rounds[0]['comparison']),
              'previous_report': {'sha256': original['sha256'], 'rounds': len(original['report']['rounds']),
                                  'last_round_sha256': original['report']['rounds'][-1]['sha256']} if original else None,
              'rounds': rounds, 'coverage': dict(_COVERAGE)}
    _check(report)
    raw = _encoded(report)
    if len(raw) > MAX_INDEX_BYTES:
        raise ValueError('Complete training round index exceeds 10 MB; nothing was truncated or published')
    destination = destination.expanduser().absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.training-rounds-', dir=destination.parent) as temporary:
        staged = Path(temporary) / 'index'
        staged.mkdir()
        (staged / 'rounds.json').write_bytes(raw)
        publish_directory(staged, destination)
    return {'directory': str(destination), 'sha256': hashlib.sha256(raw).hexdigest(),
            'rounds': len(rounds), 'initial_anchor': report['initial_anchor'], 'coverage': report['coverage']}
