"""Source-bound Skill proposals; original inputs, versions and adoption stay authoritative."""

import hashlib
import json
from pathlib import Path

from . import agents, contracts, definition_bundles, handoff, skill_assets, workflow_definitions
from .asset_trees import manifest_digest
from .state import State

BASELINE_LIMIT = 1_048_576
RESULT_LIMIT = 8_388_608

_SCHEMA = json.loads((Path(__file__).parent / 'data/schemas/retrospective-proposal-v1.json').read_bytes())
_CANDIDATE = _SCHEMA['properties']['candidate']['oneOf'][1]
_REQUEST = {
    'type': 'object', 'additionalProperties': False,
    'required': ['schema_version', 'format', 'project', 'objective', 'evidence', 'baseline', 'proposal_schema'],
    'properties': {
        'schema_version': {'const': 1},
        'format': {'const': 'ergora-skill-retrospective-request'},
        'project': {'type': 'string', 'minLength': 1},
        'objective': {'$ref': '#/$defs/text'},
        'proposal_schema': {'const': _SCHEMA},
        'baseline': {
            'type': 'object', 'additionalProperties': False,
            'required': ['name', 'digest', 'head_revision', 'files'],
            'properties': {
                'name': _CANDIDATE['properties']['name'], 'digest': {'$ref': '#/$defs/digest'},
                'head_revision': _SCHEMA['properties']['head_revision'], 'files': _CANDIDATE['properties']['files'],
            },
        },
        'evidence': {
            'type': 'object', 'required': ['sha256', 'artifacts'],
            'properties': {
                'sha256': {'$ref': '#/$defs/digest'},
                'artifacts': {
                    'type': 'array', 'maxItems': 32,
                    'items': {
                        'type': 'object', 'required': ['job_id', 'artifact'],
                        'properties': {
                            'job_id': {'type': 'string'},
                            'artifact': {
                                'type': 'object', 'required': ['name', 'sha256'],
                                'properties': {'name': {'type': 'string'}, 'sha256': {'$ref': '#/$defs/digest'}},
                            },
                        },
                    },
                },
            },
        },
    },
    '$defs': _SCHEMA['$defs'],
}


def _encoded(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _file_manifest(files: dict, name: str) -> dict:
    """Validate proposed ordinary-file content without writing or executing it."""
    manifest = {}
    paths = []
    for path, value in files.items():
        portable = definition_bundles.relative_path(path, 'Retrospective Skill')
        if '.git' in portable.parts or '\0' in value['text']:
            raise ValueError('Retrospective Skills require ordinary UTF-8 files without .git or NUL')
        manifest[path] = {'sha256': hashlib.sha256(value['text'].encode('utf-8')).hexdigest(),
                          'executable_bits': value['executable_bits']}
        paths.append((tuple(part.casefold() for part in portable.parts), portable.parts))
    paths.sort()
    for (before, spelling), (after, next_spelling) in zip(paths, paths[1:]):
        if after[:len(before)] == before:
            raise ValueError('Retrospective Skill paths have a case collision or file/directory conflict')
        for offset, (left, right) in enumerate(zip(before, after)):
            if left != right:
                break
            if spelling[offset] != next_spelling[offset]:
                raise ValueError('Retrospective Skill directory prefixes require consistent portable spelling')
    if skill_assets.parse_metadata(files['SKILL.md']['text'])['name'] != name:
        raise ValueError('Candidate Skill metadata must preserve the selected name')
    return manifest


def prepare(state: State, project_id: str, packet: Path, selection: list[dict], *, packet_sha256: str,
            name: str, digest: str, head_revision: int, objective: str, manifest: Path, instance: str,
            destination: Path, max_prompt_bytes: int) -> dict:
    """Freeze selected evidence and the current complete baseline into an original leaf input."""
    state.project(project_id)
    contracts.validate(objective, _SCHEMA['$defs']['text'], 'Retrospective objective')
    evidence = handoff.evidence(packet, selection, sha256=packet_sha256)
    if evidence['index']['project'] != project_id:
        raise ValueError('Retrospective evidence belongs to a different project')
    baseline = skill_assets.get(state, project_id, digest)
    if baseline['name'] != name:
        raise ValueError('Retrospective baseline belongs to a different Skill')
    files, remaining = {}, BASELINE_LIMIT
    for path, details in baseline['files'].items():
        with (Path(baseline['path']) / path).open('rb') as stream:
            raw = stream.read(remaining + 1)
        remaining -= len(raw)
        if remaining < 0:
            raise ValueError('Complete retrospective baseline exceeds 1 MiB; choose a smaller Skill')
        if hashlib.sha256(raw).hexdigest() != details['sha256']:
            raise ValueError('Retrospective baseline changed during reading')
        files[path] = {'text': raw.decode('utf-8'), 'executable_bits': details['executable_bits']}
    if manifest_digest(_file_manifest(files, name)) != digest:
        raise ValueError('Retrospective baseline differs from the original Skill identity')
    skill_assets.get(state, project_id, digest)
    # Observe the head after complete source I/O; an earlier preview is not a lease.
    head = next((item for item in skill_assets.versions(state, project_id, heads_only=True)['active']
                 if item['name'] == name), None)
    if head is None or head['digest'] != digest or head['revision'] != head_revision:
        raise ValueError('Active Skill changed; select its current digest and head revision')
    task = {'schema_version': 1, 'format': 'ergora-skill-retrospective-request', 'project': project_id,
            'objective': objective, 'evidence': evidence,
            'baseline': {'name': name, 'digest': digest, 'head_revision': head_revision, 'files': files},
            'proposal_schema': _SCHEMA}
    return workflow_definitions.prepare_input_from_manifest(manifest, instance, _encoded(task),
                                                             destination, max_prompt_bytes)


def check(source: Path, result: Path, *, result_sha256: str | None = None) -> dict:
    """Check declared links against frozen bytes; never import, score or adopt a proposal."""
    prepared = workflow_definitions.inspect_input(source, material=True)
    task = definition_bundles.read_json(Path(prepared['path']) / 'task.txt', prepared['request']['task_sha256'])
    contracts.validate(task, _REQUEST, 'Frozen retrospective request')
    with result.open('rb') as stream:
        raw = stream.read(RESULT_LIMIT + 1)
    if len(raw) > RESULT_LIMIT:
        raise ValueError('Retrospective result exceeds 8 MiB')
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if result_sha256 is not None and result_sha256 != observed_sha256:
        raise ValueError('Retrospective result differs from the expected original bytes')
    outer = definition_bundles.parse_json(raw.decode('utf-8-sig'), 'Retrospective result')
    leaf = next(item for item in prepared['composition']['instances'] if item['path'] == prepared['request']['instance'])
    agents.validate_result(outer, agents.result_schema(['response'], leaf['role'] == 'reviewer'))
    proposal = definition_bundles.parse_json(outer['artifacts']['response'], 'Retrospective proposal')
    contracts.validate(proposal, _SCHEMA, 'Retrospective proposal')
    baseline, evidence = task['baseline'], task['evidence']
    if hashlib.sha256(_encoded({key: value for key, value in evidence.items() if key != 'sha256'})).hexdigest() != evidence['sha256']:
        raise ValueError('Frozen retrospective evidence differs from its declared selection identity')
    if manifest_digest(_file_manifest(baseline['files'], baseline['name'])) != baseline['digest']:
        raise ValueError('Frozen retrospective baseline differs from its declared Skill identity')
    if (proposal['evidence_sha256'] != evidence['sha256'] or proposal['baseline_digest'] != baseline['digest']
            or proposal['head_revision'] != baseline['head_revision']):
        raise ValueError('Retrospective proposal differs from its frozen source or baseline')
    selected = {(item['job_id'], item['artifact']['name'], item['artifact']['sha256']) for item in evidence['artifacts']}
    for observation in proposal['observations']:
        if any((ref['job_id'], ref['name'], ref['sha256']) not in selected for ref in observation['citations']):
            raise ValueError('Retrospective citation is absent from the complete selected evidence')
    candidate = proposal['candidate']
    candidate_digest = None
    if candidate is not None:
        if candidate['name'] != baseline['name']:
            raise ValueError('Candidate Skill must preserve its selected baseline name')
        if not proposal['observations']:
            raise ValueError('A retrospective candidate requires source-cited observations')
        candidate_digest = manifest_digest(_file_manifest(candidate['files'], candidate['name']))
    return {'schema_version': 1, 'format': 'ergora-skill-retrospective-check',
            'input_digest': prepared['digest'], 'result_sha256': observed_sha256,
            'candidate_digest': candidate_digest, 'content_changed': candidate_digest not in (None, baseline['digest']),
            'quality_evaluated': False, 'adoption_authorized': False, 'origin_authenticated': False,
            'verification_scope': 'frozen_input_and_declared_candidate_links',
            'request': task, 'agent_result': outer}
