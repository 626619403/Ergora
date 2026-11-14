"""Source-bound proposals; original inputs, memory, versions and adoption stay authoritative."""

from copy import deepcopy
from contextlib import contextmanager
import base64
import hashlib
import json
from pathlib import Path
import tempfile

from . import agents, contracts, definition_bundles, handoff, memory, skill_assets, workflow_definitions
from .asset_trees import digest_tree, inventory_tree, manifest_digest, publish_directory
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
_MEMORY_SCHEMA = json.loads((Path(__file__).parent / 'data/schemas/retrospective-memory-proposal-v1.json').read_bytes())
_MEMORY_REQUEST = deepcopy(_REQUEST)
_MEMORY_REQUEST['properties'].update({
    'format': {'const': 'ergora-memory-retrospective-request'}, 'proposal_schema': {'const': _MEMORY_SCHEMA},
    'baseline': {
        'type': 'object', 'additionalProperties': False, 'required': ['record', 'digest', 'observed_at'],
        'properties': {
            'digest': {'$ref': '#/$defs/digest'}, 'observed_at': {'type': 'string', 'minLength': 1},
            'record': {'oneOf': [{'type': 'null'}, {
                'type': 'object', 'additionalProperties': False,
                'required': ['project', 'id', 'revision', 'text', 'source', 'observed', 'status'],
                'properties': {
                    'project': {'type': 'string', 'minLength': 1}, 'id': {'type': 'string', 'minLength': 1},
                    'revision': {'type': 'integer', 'minimum': 1}, 'text': {'$ref': '#/$defs/memory_text'},
                    'source': {'type': 'object', 'additionalProperties': False, 'required': ['uri', 'revision'],
                               'properties': {key: {'type': 'string', 'pattern': '\\S'} for key in ('uri', 'revision')}},
                    'observed': {'type': 'string', 'minLength': 1}, 'status': {'const': 'active'},
                    'expires_at': {'type': 'string', 'minLength': 1},
                },
            }]},
        },
    },
})
_MEMORY_REQUEST['$defs'] = _MEMORY_SCHEMA['$defs']
_MEMORY_REQUEST['properties']['evidence']['required'].append('packet_sha256')
_MEMORY_REQUEST['properties']['evidence']['properties']['packet_sha256'] = {'$ref': '#/$defs/digest'}

_WORKFLOW_SCHEMA = json.loads((Path(__file__).parent / 'data/schemas/retrospective-workflow-proposal-v1.json').read_bytes())
_WORKFLOW_REQUEST = deepcopy(_MEMORY_REQUEST)
_WORKFLOW_REQUEST['$defs'] = _WORKFLOW_SCHEMA['$defs']
_WORKFLOW_REQUEST['properties'].update({
    'format': {'const': 'ergora-workflow-retrospective-request'}, 'proposal_schema': {'const': _WORKFLOW_SCHEMA},
    'baseline': {
        'type': 'object', 'additionalProperties': False,
        'required': ['digest', 'manifest_digest', 'directories', 'definition', 'next_version', 'files'],
        'properties': {
            'digest': {'$ref': '#/$defs/digest'}, 'definition': {'type': 'object'},
            'manifest_digest': {'$ref': '#/$defs/digest'},
            'directories': {'type': 'array', 'maxItems': 1000, 'uniqueItems': True,
                            'items': {'type': 'string', 'minLength': 1, 'maxLength': 4096}},
            'next_version': contracts.WORKFLOW_DEFINITION['properties']['version'],
            'files': {key: value for key, value in _CANDIDATE['properties']['files'].items() if key != 'required'},
        },
    },
})


def _encoded(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _read_files(directory: Path, files: dict) -> dict:
    """Read complete bounded UTF-8 material against an original tree inventory."""
    selected, remaining = {}, BASELINE_LIMIT
    for name, details in files.items():
        with (directory / name).open('rb') as stream:
            raw = stream.read(remaining + 1)
        remaining -= len(raw)
        if remaining < 0:
            raise ValueError('Complete retrospective baseline exceeds 1 MiB; select a smaller target')
        if hashlib.sha256(raw).hexdigest() != details['sha256']:
            raise ValueError('Retrospective baseline changed during reading')
        if b'\0' in raw:
            raise ValueError('Retrospective baselines require UTF-8 text without NUL')
        selected[name] = {'text': raw.decode('utf-8'), 'executable_bits': details['executable_bits']}
    return selected


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
    files = _read_files(Path(baseline['path']), baseline['files'])
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


def _read_proposal(source: Path, result: Path, result_sha256: str | None,
                   request_schema: dict, proposal_schema: dict) -> tuple[dict, dict, dict, dict, str]:
    """Read one bounded original result and its complete frozen request for either target."""
    prepared = workflow_definitions.inspect_input(source, material=True)
    task = definition_bundles.read_json(Path(prepared['path']) / 'task.txt', prepared['request']['task_sha256'])
    contracts.validate(task, request_schema, 'Frozen retrospective request')
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
    contracts.validate(proposal, proposal_schema, 'Retrospective proposal')
    return prepared, task, outer, proposal, observed_sha256


def _check_sources(task: dict, proposal: dict) -> None:
    """Check complete evidence identities and the proposal's exact selected citations."""
    baseline, evidence = task['baseline'], task['evidence']
    if hashlib.sha256(_encoded({key: value for key, value in evidence.items() if key != 'sha256'})).hexdigest() != evidence['sha256']:
        raise ValueError('Frozen retrospective evidence differs from its declared selection identity')
    if proposal['evidence_sha256'] != evidence['sha256'] or proposal['baseline_digest'] != baseline['digest']:
        raise ValueError('Retrospective proposal differs from its frozen source or baseline')
    selected = {(item['job_id'], item['artifact']['name'], item['artifact']['sha256']) for item in evidence['artifacts']}
    for observation in proposal['observations']:
        if any((ref['job_id'], ref['name'], ref['sha256']) not in selected for ref in observation['citations']):
            raise ValueError('Retrospective citation is absent from the complete selected evidence')
    if proposal['candidate'] is not None and not proposal['observations']:
        raise ValueError('A retrospective candidate requires source-cited observations')


def _checked_proposal(source: Path, result: Path, result_sha256: str | None) -> tuple[dict, dict]:
    """Validate once and retain the parsed Skill proposal for either inspection or export."""
    prepared, task, outer, proposal, observed_sha256 = _read_proposal(source, result, result_sha256, _REQUEST, _SCHEMA)
    _check_sources(task, proposal)
    baseline = task['baseline']
    if manifest_digest(_file_manifest(baseline['files'], baseline['name'])) != baseline['digest']:
        raise ValueError('Frozen retrospective baseline differs from its declared Skill identity')
    if proposal['head_revision'] != baseline['head_revision']:
        raise ValueError('Retrospective proposal differs from its frozen source or baseline')
    candidate = proposal['candidate']
    candidate_digest = None
    if candidate is not None:
        if candidate['name'] != baseline['name']:
            raise ValueError('Candidate Skill must preserve its selected baseline name')
        candidate_digest = manifest_digest(_file_manifest(candidate['files'], candidate['name']))
    checked = {'schema_version': 1, 'format': 'ergora-skill-retrospective-check',
            'input_digest': prepared['digest'], 'result_sha256': observed_sha256,
            'candidate_digest': candidate_digest, 'content_changed': candidate_digest not in (None, baseline['digest']),
            'quality_evaluated': False, 'adoption_authorized': False, 'origin_authenticated': False,
            'verification_scope': 'frozen_input_and_declared_candidate_links',
            'request': task, 'agent_result': outer}
    return checked, proposal


def check(source: Path, result: Path, *, result_sha256: str | None = None) -> dict:
    """Check declared links against frozen bytes; never import, score or adopt a proposal."""
    return _checked_proposal(source, result, result_sha256)[0]


def _export_location(source: Path, destination: Path) -> Path:
    destination = destination.expanduser().absolute()
    if destination.resolve().is_relative_to(source.expanduser().resolve()):
        raise ValueError('Retrospective export cannot change its frozen input directory')
    if destination.exists() or destination.is_symlink():
        raise ValueError('Choose a new retrospective export directory')
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def export(source: Path, result: Path, destination: Path, *, result_sha256: str, candidate_digest: str) -> dict:
    """Explicitly export a selected complete candidate; original owners still evaluate and adopt."""
    checked, proposal = _checked_proposal(source, result, result_sha256)
    candidate = proposal['candidate']
    if candidate is None:
        raise ValueError('Retrospective has no Skill candidate to export')
    if checked['candidate_digest'] != candidate_digest:
        raise ValueError('Retrospective candidate differs from the explicitly selected digest')
    destination = destination.expanduser().absolute()
    if destination.name != candidate['name']:
        raise ValueError('Export directory name must match the Skill name')
    destination = _export_location(source, destination)
    with tempfile.TemporaryDirectory(prefix='.retrospective-skill-', dir=destination.parent) as temporary:
        staged = Path(temporary) / candidate['name']
        staged.mkdir(mode=0o700)
        for name, file in candidate['files'].items():
            path = staged / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(file['text'].encode('utf-8'))
            path.chmod(0o600 | file['executable_bits'])
        if digest_tree(staged)[0] != candidate_digest:
            raise ValueError('Exported Skill cannot preserve the selected complete content and execution bits')
        publish_directory(staged, destination)
    return {'schema_version': 1, 'format': 'ergora-skill-retrospective-export',
            'input_digest': checked['input_digest'], 'result_sha256': checked['result_sha256'],
            'baseline': {key: checked['request']['baseline'][key] for key in ('name', 'digest', 'head_revision')},
            'candidate_digest': candidate_digest, 'destination': str(destination),
            'quality_evaluated': False, 'adoption_authorized': False, 'origin_authenticated': False}


def prepare_memory(state: State, project_id: str, packet: Path, selection: list[dict], *, packet_sha256: str,
                   memory_id: str | None, revision: int, objective: str, manifest: Path, instance: str,
                   destination: Path, max_prompt_bytes: int) -> dict:
    """Freeze a complete current valid memory or an explicit new-record baseline."""
    contracts.validate(objective, _SCHEMA['$defs']['text'], 'Retrospective objective')
    evidence = handoff.evidence(packet, selection, sha256=packet_sha256)
    if evidence['index']['project'] != project_id:
        raise ValueError('Retrospective evidence belongs to a different project')
    # Observe after source I/O. This snapshot is not a lease on future validity.
    catalog = memory.catalog(state, project_id)
    record = None
    if memory_id is not None:
        selected = next((item for item in catalog['records'] if item['record']['id'] == memory_id), None)
        if selected is None or selected['validity'] != 'valid' or selected['record']['revision'] != revision:
            raise ValueError('Selected memory changed, expired or was deleted; select a current valid revision')
        record = selected['record']
    elif revision != 0:
        raise ValueError('A new memory retrospective requires revision zero')
    baseline = {'record': record, 'observed_at': catalog['observed_at'],
                'digest': hashlib.sha256(_encoded({'project': project_id, 'record': record})).hexdigest()}
    task = {'schema_version': 1, 'format': 'ergora-memory-retrospective-request', 'project': project_id,
            'objective': objective, 'evidence': evidence, 'baseline': baseline, 'proposal_schema': _MEMORY_SCHEMA}
    return workflow_definitions.prepare_input_from_manifest(manifest, instance, _encoded(task), destination, max_prompt_bytes)


def _checked_memory(source: Path, result: Path, result_sha256: str | None) -> tuple[dict, dict]:
    prepared, task, outer, proposal, observed_sha256 = _read_proposal(
        source, result, result_sha256, _MEMORY_REQUEST, _MEMORY_SCHEMA)
    _check_sources(task, proposal)
    baseline, evidence = task['baseline'], task['evidence']
    record = baseline['record']
    if (hashlib.sha256(_encoded({'project': task['project'], 'record': record})).hexdigest() != baseline['digest']
            or (record is not None and record['project'] != task['project'])
            or evidence['index']['project'] != task['project']):
        raise ValueError('Frozen retrospective memory differs from its declared project or baseline identity')
    candidate = proposal['candidate']
    save, candidate_digest = None, None
    if candidate is not None:
        save = {'text': candidate['text'],
                'source': {'uri': 'ergora-handoff:sha256:' + evidence['packet_sha256'], 'revision': evidence['sha256']},
                'memory_id': record['id'] if record else None, 'expected_revision': record['revision'] if record else 0}
        candidate_digest = hashlib.sha256(_encoded({'baseline_digest': baseline['digest'], 'save': save})).hexdigest()
    return {'schema_version': 1, 'format': 'ergora-memory-retrospective-check',
            'input_digest': prepared['digest'], 'result_sha256': observed_sha256, 'candidate_digest': candidate_digest,
            'content_changed': candidate is not None and (record is None or candidate['text'] != record['text']),
            'save': save, 'quality_evaluated': False, 'adoption_authorized': False, 'origin_authenticated': False,
            'verification_scope': 'frozen_input_and_declared_candidate_links', 'request': task, 'agent_result': outer}, proposal


def check_memory(source: Path, result: Path, *, result_sha256: str | None = None) -> dict:
    """Verify declared memory proposal links offline, independently of current State."""
    return _checked_memory(source, result, result_sha256)[0]


def export_memory(source: Path, result: Path, destination: Path, *, result_sha256: str, candidate_digest: str) -> dict:
    """Export text and exact original-save coordinates, without saving or renewing memory."""
    checked, proposal = _checked_memory(source, result, result_sha256)
    if proposal['candidate'] is None:
        raise ValueError('Retrospective has no memory candidate to export')
    if checked['candidate_digest'] != candidate_digest:
        raise ValueError('Retrospective candidate differs from the explicitly selected digest')
    destination = _export_location(source, destination)
    text = checked['save']['text'].encode('utf-8')
    receipt = {'schema_version': 1, 'format': 'ergora-memory-retrospective-export',
               'project': checked['request']['project'], 'input_digest': checked['input_digest'],
               'result_sha256': checked['result_sha256'], 'candidate_digest': candidate_digest,
               'baseline': checked['request']['baseline'], 'destination': str(destination),
               'save': {key: value for key, value in checked['save'].items() if key != 'text'},
               'text_file': 'memory.txt', 'text_sha256': hashlib.sha256(text).hexdigest(),
               'expiry_policy': 'original_save_default_preserves_previous_limit',
               'quality_evaluated': False, 'adoption_authorized': False, 'origin_authenticated': False}
    with tempfile.TemporaryDirectory(prefix='.retrospective-memory-', dir=destination.parent) as temporary:
        staged = Path(temporary) / 'candidate'
        staged.mkdir(mode=0o700)
        for name, raw in {'memory.txt': text, 'receipt.json': _encoded(receipt)}.items():
            path = staged / name
            path.write_bytes(raw)
            path.chmod(0o600)
        publish_directory(staged, destination)
    return receipt


def prepare_workflow(state: State, project_id: str, packet: Path, selection: list[dict], *, packet_sha256: str,
                     target_manifest: Path, target_digest: str, next_version: str, objective: str,
                     manifest: Path, instance: str, destination: Path, max_prompt_bytes: int) -> dict:
    """Freeze an operator-selected complete target graph for a bounded root revision."""
    state.project(project_id)
    contracts.validate(objective, _SCHEMA['$defs']['text'], 'Retrospective objective')
    contracts.validate(next_version, contracts.WORKFLOW_DEFINITION['properties']['version'], 'Next workflow version')
    evidence = handoff.evidence(packet, selection, sha256=packet_sha256)
    if evidence['index']['project'] != project_id:
        raise ValueError('Retrospective evidence belongs to a different project')
    checked = workflow_definitions.inspect_manifest(target_manifest, material=True)
    if checked['digest'] != target_digest:
        raise ValueError('Retrospective target differs from the explicitly selected manifest digest')
    root = checked['manifest']['root']
    definition = workflow_definitions.library(Path(checked['path']) / 'assets').get(root['id'], root['version'])['definition']
    if next_version == definition['version']:
        raise ValueError('Select a new immutable workflow version')
    before = inventory_tree(Path(checked['path']), label='Retrospective manifest', max_directories=1000, max_depth=48)
    _, files, directories = before
    frozen = _read_files(Path(checked['path']), files)
    if (manifest_digest(files) != target_digest or
            workflow_definitions.inspect_manifest(target_manifest)['digest'] != target_digest or
            inventory_tree(Path(checked['path']), label='Retrospective manifest', max_directories=1000, max_depth=48) != before):
        raise ValueError('Retrospective target manifest changed during reading')
    task = {'schema_version': 1, 'format': 'ergora-workflow-retrospective-request', 'project': project_id,
            'objective': objective, 'evidence': evidence, 'proposal_schema': _WORKFLOW_SCHEMA,
            'baseline': {'digest': hashlib.sha256(_encoded({'manifest_digest': target_digest, 'directories': directories})).hexdigest(),
                         'manifest_digest': target_digest, 'directories': directories,
                         'definition': definition, 'next_version': next_version, 'files': frozen}}
    return workflow_definitions.prepare_input_from_manifest(manifest, instance, _encoded(task), destination, max_prompt_bytes)


def _workflow_scope(baseline: dict, definition: dict) -> None:
    """Keep authority, ports, implementations and existing ordering gates fixed."""
    original = baseline['definition']
    contracts.validate(definition, contracts.WORKFLOW_DEFINITIONS[original['schema_version']], 'Candidate workflow')
    allowed = {'version', 'description', 'resources', 'nodes'}
    if (definition['version'] != baseline['next_version'] or
            {key: value for key, value in definition.items() if key not in allowed} !=
            {key: value for key, value in original.items() if key not in allowed}):
        raise ValueError('Workflow proposal must preserve the selected authority, ports and version')
    declarations = lambda items: [{key: value for key, value in item.items() if key not in ('sha256', 'digest')} for item in items]
    if declarations(definition['resources']) != declarations(original['resources']):
        raise ValueError('Workflow proposal must preserve root resource declarations')
    nodes = definition['nodes']
    if (len(nodes) != len(original['nodes']) or any(
            {key: value for key, value in node.items() if key != 'depends_on'} !=
            {key: value for key, value in before.items() if key != 'depends_on'} or
            not set(before['depends_on']).issubset(node['depends_on'])
            for before, node in zip(original['nodes'], nodes))):
        raise ValueError('Workflow proposal must preserve every node and existing dependency')


@contextmanager
def _workflow_proposal(source: Path, result: Path, result_sha256: str | None):
    """Original restore/revise/compiler own all scratch material and graph validation."""
    prepared, task, outer, proposal, observed_sha256 = _read_proposal(
        source, result, result_sha256, _WORKFLOW_REQUEST, _WORKFLOW_SCHEMA)
    _check_sources(task, proposal)
    baseline = task['baseline']
    if task['evidence']['index']['project'] != task['project']:
        raise ValueError('Frozen retrospective evidence belongs to a different project')
    files, total = {}, 0
    for name, item in baseline['files'].items():
        raw = item['text'].encode('utf-8')
        total += len(raw)
        if total > BASELINE_LIMIT:
            raise ValueError('Complete retrospective baseline exceeds 1 MiB')
        if b'\0' in raw:
            raise ValueError('Retrospective baselines require UTF-8 text without NUL')
        files[name] = {'content_base64': base64.b64encode(raw).decode('ascii'), 'executable_bits': item['executable_bits']}
    if hashlib.sha256(_encoded({key: baseline[key] for key in ('manifest_digest', 'directories')})).hexdigest() != baseline['digest']:
        raise ValueError('Frozen workflow files and directories differ from the baseline identity')
    snapshot = {'digest': baseline['manifest_digest'], 'files': files}
    with tempfile.TemporaryDirectory(prefix='.retrospective-workflow-') as temporary:
        restored = workflow_definitions.restore_manifest(snapshot, Path(temporary) / 'manifest')
        for name in baseline['directories']:
            (Path(restored['path']) / definition_bundles.relative_path(name, 'Retrospective directory')).mkdir(parents=True, exist_ok=True)
        if inventory_tree(Path(restored['path']), label='Retrospective manifest', max_directories=1000, max_depth=48)[2] != baseline['directories']:
            raise ValueError('Frozen workflow directory inventory is incomplete or noncanonical')
        restored = workflow_definitions.inspect_manifest(Path(restored['path']), material=True)
        root = restored['manifest']['root']
        library = workflow_definitions.library(Path(restored['path']) / 'assets')
        original = library.get(root['id'], root['version'])
        if baseline['definition'] != original['definition'] or baseline['next_version'] == root['version']:
            raise ValueError('Frozen retrospective root differs from its complete manifest or selected new version')
        candidate, revision, compiled = proposal['candidate'], None, None
        if candidate is not None:
            _workflow_scope(baseline, candidate['definition'])
            args = (root['id'], root['version'], root['digest'], candidate['definition'])
            changes = candidate['resource_changes']
            revision = library.revise(*args, resource_changes=changes, preview_resources=True)
            for operation in changes['operations']:
                if operation['op'] == 'write':
                    raw = base64.b64decode(operation['content_base64'], validate=True)
                    raw.decode('utf-8')
                    if b'\0' in raw:
                        raise ValueError('Workflow retrospective writes require UTF-8 text without NUL')
                path = operation['path']
                if not any(path == resource['path'] or
                           (resource['kind'] == 'skill' and path.startswith(resource['path'] + '/'))
                           for resource in original['definition']['resources']):
                    raise ValueError('Workflow resource changes must stay within declared root resources')
            library.revise(root['id'], root['version'], root['digest'], revision['definition'],
                           resource_changes=changes, accepted_candidate=revision['candidate'], publish=True)
            compiled = workflow_definitions.preview(library.root, root['id'], baseline['next_version'], restored['manifest']['grant'])
        checked = {'schema_version': 1, 'format': 'ergora-workflow-retrospective-check',
                   'input_digest': prepared['digest'], 'result_sha256': observed_sha256,
                   'candidate_digest': revision['digest'] if revision else None, 'revision_preview': revision,
                   'candidate_preview_sha256': compiled['preview_sha256'] if compiled else None,
                   'quality_evaluated': False, 'adoption_authorized': False, 'origin_authenticated': False,
                   'verification_scope': 'frozen_input_and_original_scratch_revision_with_frozen_grant',
                   'request': task, 'agent_result': outer}
        yield checked, library


def check_workflow(source: Path, result: Path, *, result_sha256: str | None = None) -> dict:
    """Check offline using private temporary files; never publish into a user's library."""
    with _workflow_proposal(source, result, result_sha256) as (checked, _):
        return checked


def export_workflow(source: Path, result: Path, destination: Path, *, result_sha256: str, candidate_digest: str) -> dict:
    """Export a complete selected root bundle for the original explicit import/selection."""
    with _workflow_proposal(source, result, result_sha256) as (checked, library):
        if checked['candidate_digest'] is None:
            raise ValueError('Retrospective has no workflow candidate to export')
        if checked['candidate_digest'] != candidate_digest:
            raise ValueError('Retrospective candidate differs from the explicitly selected digest')
        destination = _export_location(source, destination)
        baseline = checked['request']['baseline']
        with tempfile.TemporaryDirectory(prefix='.retrospective-workflow-export-', dir=destination.parent) as temporary:
            staged = Path(temporary) / 'bundle'
            library.export(baseline['definition']['id'], baseline['next_version'], staged)
            publish_directory(staged, destination)
        return {'schema_version': 1, 'format': 'ergora-workflow-retrospective-export',
                'input_digest': checked['input_digest'], 'result_sha256': checked['result_sha256'],
                'baseline_digest': baseline['digest'], 'candidate_digest': candidate_digest,
                'baseline_manifest_digest': baseline['manifest_digest'], 'baseline_directories': baseline['directories'],
                'candidate_directories': checked['revision_preview']['candidate']['directories'],
                'definition': checked['revision_preview']['definition'], 'destination': str(destination),
                'candidate_preview_sha256': checked['candidate_preview_sha256'],
                'quality_evaluated': False, 'adoption_authorized': False, 'origin_authenticated': False}
