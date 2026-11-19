"""Immutable links between original training observations; never a new gate."""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
import stat
import tempfile

import ergora.training.application as training
import ergora.training.execution_protocol as execution
from ergora.configuration import validation as contracts
from ergora.storage.assets import is_link, publish_directory
from ergora.definitions.bundles import parse_json
from ergora.storage.state import State
from ergora._paths import DATA_ROOT


MAX_INDEX_BYTES = execution.ARTIFACT_LIMIT
_SCHEMA = json.loads((DATA_ROOT / 'schemas/training-rounds-v1.json').read_text(encoding='utf-8'))
def _check(report: dict) -> None:
    contracts.validate(report, {'$defs': _SCHEMA['$defs'], '$ref': '#/$defs/report'}, 'Training round index')
    execution.validate_round_content(report)


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
           previous: Path | None = None, previous_sha256: str | None = None,
           on_reader_return: Callable[[str, dict], None] | None = None) -> dict:
    """Capture original records; an optional observer runs before the next read."""
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
        if on_reader_return is not None:
            on_reader_return('inspect', records)
        evidence = training.evidence(state, project_id, ident)
        if on_reader_return is not None:
            on_reader_return('evidence', evidence)
        submission = training.submission(state, project_id, ident)
        if on_reader_return is not None:
            on_reader_return('submission', submission)
        approval = None
        if submission['status'] == 'submitted':
            approval = training.approval(state, project_id, ident)
            if on_reader_return is not None:
                on_reader_return('approval', approval)
        content = {'experiment_id': ident, 'parent_sha256': rounds[-1]['sha256'] if rounds else None,
                   'annotation': {key: requested[key] for key in ('change', 'next_bottleneck')},
                   'comparison': execution.round_comparison(records),
                   'native': {'records': records, 'evidence': evidence, 'submission': submission, 'approval': approval}}
        rounds.append({**content, 'sha256': execution.round_content_sha(content)})
    if state.project(project_id)['revision'] != project['revision']:
        raise ValueError('Project changed while capturing training observations; no index was published')
    report = {'schema_version': 1, 'kind': 'training-round-index', 'project': identity,
              'initial_anchor': original['report']['initial_anchor'] if original else execution.round_anchor(rounds[0]['comparison']),
              'previous_report': {'sha256': original['sha256'], 'rounds': len(original['report']['rounds']),
                                  'last_round_sha256': original['report']['rounds'][-1]['sha256']} if original else None,
              'rounds': rounds, 'coverage': dict(execution.ROUND_COVERAGE)}
    _check(report)
    raw = execution.encode_round_content(report)
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
