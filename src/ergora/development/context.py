"""Explicit current project sources, carried by the original root resource tree."""

import base64
from contextlib import contextmanager, nullcontext
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import ergora.improvement.memory as memory
from ergora.improvement import shared_cases
import ergora.definitions.skills as skill_assets
from ergora.development import envelopes as task_envelopes
from ergora.storage.assets import digest_tree
from ergora.storage.state import State


def _sources(state: State, project_id: str, selection: dict) -> tuple[dict, list[Path]]:
    skills, paths, names = [], [], set()
    heads = ({head['name']: head for head in skill_assets.versions(state, project_id, heads_only=True)['active']}
             if selection['skills'] else {})
    for selected in selection['skills']:
        name = selected['name']
        if name in names:
            raise ValueError('Selected Skill names must be unique')
        names.add(name)
        head = heads.get(name)
        if head is None or {key: head[key] for key in ('name', 'digest', 'revision')} != selected:
            raise ValueError('Selected Skill head changed; select its current adopted digest and revision: ' + name)
        version = skill_assets.get(state, project_id, selected['digest'])
        if version['name'] != name:
            raise ValueError('Selected Skill digest belongs to another name')
        skills.append({**selected, 'provenance': {key: value for key, value in version.items()
                      if key not in ('path', 'project', 'name', 'digest')}})
        paths.append(Path(version['path']))
    # Skill hashing can be slow. Observe memory validity after that I/O, at the
    # final admission decision, rather than carry an earlier validity snapshot.
    catalog = memory.catalog(state, project_id)
    records = {item['record']['id']: item for item in catalog['records']}
    memories, ids = [], set()
    for selected in selection['memories']:
        identity = selected['id']
        current = records.get(identity)
        if identity in ids:
            raise ValueError('Selected memory IDs must be unique')
        ids.add(identity)
        if (current is None or current['validity'] != 'valid'
                or current['record']['revision'] != selected['revision']):
            raise ValueError('Selected memory changed, expired or was deleted; select a current valid revision: ' + identity)
        memories.append(current['record'])
    return {'observed_at': catalog['observed_at'], 'memories': memories, 'skills': skills}, paths


def _shared_library(request: dict) -> Path:
    library = Path(request['library']).expanduser()
    if not library.is_absolute():
        raise ValueError('Selected shared case requires an absolute host library path')
    return library


def _read_shared_case(request: dict) -> bytes:
    result = shared_cases.show(_shared_library(request), request['id'],
                               revision=request['revision'], sha256=request['sha256'])
    return result['markdown'].encode('utf-8')


def _private_version(library, original: dict, reserved: str | None) -> str:
    used = {item['definition']['version'] for item in library.documents()
            if item['definition']['id'] == original['id']}
    major, minor, patch = original['version'].split('.')
    version = int(patch) + 1
    while f'{major}.{minor}.{version}' in used or f'{major}.{minor}.{version}' == reserved:
        version += 1
    return f'{major}.{minor}.{version}'


def _case_base_certificate(document: dict, kind: str) -> dict:
    filename = kind + '.json'
    raw = (Path(document['path']) / filename).read_bytes()
    if hashlib.sha256(raw).hexdigest() != document['files'][filename]['sha256']:
        raise ValueError('Shared case base definition changed while recording its identity')
    return {'definition_base64': base64.b64encode(raw).decode('ascii'), 'files': document['files']}


def _derive_shared_case(root: Path, workflow_library, graph: dict, definition: dict,
                        base_root: dict, request: dict, markdown: bytes) -> tuple[dict, dict]:
    """Revise just the selected Agent and the references on its ancestor path."""
    import ergora.definitions.agents as agent_definitions

    instance = request['instance']
    parts = instance.split('/')
    path = ['/'.join(parts[:depth + 1]) for depth in range(1, len(parts))]
    instances = {item['path']: item for item in graph['instances']}
    target = instances.get(instance)
    if parts[0] != 'root' or not path or target is None or target['kind'] != 'agent':
        raise ValueError('Select one Agent instance for shared case context')
    permissions = target['permissions']
    if permissions['write'] or permissions['shell'] or permissions['network']:
        raise ValueError('Shared case requires a restricted read-only Agent instance')
    selection = task_envelopes.shared_case_selection(request)
    attachment = task_envelopes.shared_case_resource(selection)
    branch = []
    for depth, member in reversed(list(enumerate(path))):
        original_ref = instances[member]['ref']
        kind = original_ref['kind']
        library = agent_definitions.library(root) if kind == 'agent' else workflow_library
        document = library.get(original_ref['id'], original_ref['version'])
        if document['digest'] != original_ref['digest']:
            raise ValueError('Shared case branch definition changed during selection')
        old = document['definition']
        reserved = definition['version'] if kind == 'workflow' and old['id'] == definition['id'] else None
        updated = {**old, 'version': _private_version(library, old, reserved)}
        options = {}
        if kind == 'agent':
            if (attachment['path'] in document['files']
                    or any(resource['id'] == attachment['id'] for resource in old['resources'])):
                raise ValueError('Selected Agent already uses the reserved shared case resource')
            updated['resources'] = old['resources'] + [attachment]
            changes = {'schema_version': 1, 'operations': [{'op': 'write', 'path': attachment['path'],
                        'content_base64': base64.b64encode(markdown).decode('ascii')}]}
            preview = library.revise(old['id'], old['version'], document['digest'], updated,
                                     resource_changes=changes, preview_resources=True)
            options = {'resource_changes': changes, 'accepted_candidate': preview['candidate']}
        else:
            updated, _ = task_envelopes.replace_context_child(updated, parts[depth + 2], derived)
        saved = library.revise(old['id'], old['version'], document['digest'], updated, publish=True, **options)
        derived = {'kind': kind, 'id': updated['id'], 'version': updated['version'], 'digest': saved['digest']}
        branch.append(_case_base_certificate(document, kind))
    updated_root, _ = task_envelopes.replace_context_child(definition, parts[1], derived)
    branch.append(_case_base_certificate(base_root, 'workflow'))
    return updated_root, {'selection': selection, 'base_definitions': list(reversed(branch))}


@contextmanager
def selected_manifest(state: State, project_id: str, option: dict, selection: dict, working_directory: Path):
    """Derive the selected root in the caller's private preparation or inspection tree."""
    import ergora.definitions.workflows as workflow_definitions

    source = Path(option['manifest']).expanduser().absolute()
    original = workflow_definitions.inspect_manifest(source)
    if original['digest'] != option['manifest_digest']:
        raise ValueError('Selected composition manifest digest changed')
    case_request = selection.get('shared_case')
    project_selection = {key: value for key, value in selection.items() if key != 'shared_case'}
    sources, paths = _sources(state, project_id, project_selection)
    working_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix='.task-context-', dir=working_directory) as temporary:
        work = Path(temporary)
        copied = work / 'base'
        shutil.copytree(source, copied, symlinks=True)
        checked = workflow_definitions.inspect_manifest(copied, material=case_request is not None)
        if checked['digest'] != original['digest']:
            raise ValueError('Composition manifest changed while selecting task context')
        root = checked['manifest']['root']
        library = workflow_definitions.library(copied / 'assets')
        document = library.get(root['id'], root['version'])
        if document['digest'] != root['digest']:
            raise ValueError('Task context base root differs from its original manifest')
        if selection['root_version'] == root['version']:
            raise ValueError('Selected task context requires a new root_version')
        if (any(name == 'selected-context' or name.startswith('selected-context/') for name in document['files'])
                or any(item['id'].startswith('ergora-selected-') for item in document['definition']['resources'])):
            raise ValueError('Task context base already uses the reserved selected-context resource namespace')
        snapshot = {'schema_version': 1, 'project': project_id, 'base_manifest_digest': checked['digest'],
                    'base_root': root, 'base_definition': document['definition'], 'selection': project_selection, **sources}
        encoded = (json.dumps(snapshot, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        resource_sha256 = hashlib.sha256(encoded).hexdigest()
        additions = [{'id': 'ergora-selected-context', 'kind': 'context', 'path': 'selected-context/selection.json',
                      'sha256': resource_sha256}]
        operations = [{'op': 'write', 'path': additions[0]['path'], 'content_base64': base64.b64encode(encoded).decode('ascii')}]
        for index, (skill, path) in enumerate(zip(sources['skills'], paths)):
            prefix = 'selected-context/skills/' + skill['name']
            additions.append({'id': 'ergora-selected-skill-' + str(index), 'kind': 'skill',
                              'path': prefix, 'digest': skill['digest']})
            digest, files = digest_tree(path)
            if digest != skill['digest'] or files != skill['provenance']['files']:
                raise ValueError('Selected Skill changed while preparing its complete resources')
            for name, details in files.items():
                raw = (path / name).read_bytes()
                if hashlib.sha256(raw).hexdigest() != details['sha256']:
                    raise ValueError('Selected Skill file changed while copying: ' + name)
                operations.append({'op': 'write', 'path': prefix + '/' + name,
                    'content_base64': base64.b64encode(raw).decode('ascii'), 'executable_bits': details['executable_bits']})
        definition = deepcopy(document['definition'])
        definition['version'] = selection['root_version']
        definition['resources'].extend(additions)
        case_receipt = None
        if case_request is not None:
            definition, case_receipt = _derive_shared_case(
                copied / 'assets', library, checked['composition'], definition, document,
                case_request, _read_shared_case(case_request))
        changes = {'schema_version': 1, 'operations': operations}
        preview = library.revise(root['id'], root['version'], root['digest'], definition,
                                 resource_changes=changes, preview_resources=True)
        library.revise(root['id'], root['version'], root['digest'], definition, publish=True,
                       resource_changes=changes, accepted_candidate=preview['candidate'])
        manifest = workflow_definitions.prepare_manifest(copied / 'assets', root['id'], definition['version'],
                                                        checked['manifest']['grant'], work / 'selected')
        context = {'project': project_id, 'base_manifest_digest': checked['digest'],
                   'selection': project_selection, 'resource_sha256': resource_sha256}
        if case_receipt is not None:
            context['shared_case'] = case_receipt
        yield {**option, 'manifest': manifest['path'], 'manifest_digest': manifest['digest']}, context


def reserve_shared_case(selection: dict):
    request = selection.get('shared_case')
    if request is None or not request['require_current']:
        return nullcontext()
    return shared_cases.publication_lock(_shared_library(request))


def require_current(state: State, project_id: str, document: dict, selection: dict) -> None:
    """Check just before first intent; recovery of an existing intent keeps its bytes."""
    frozen = task_envelopes.selected_context(document)
    if frozen['project'] != project_id:
        raise ValueError('Selected task context belongs to another project')
    current, _ = _sources(state, project_id, frozen['selection'])
    if any(current[key] != frozen[key] for key in ('memories', 'skills')):
        raise ValueError('Selected task context content changed; prepare a fresh explicit selection')
    request = selection.get('shared_case')
    if task_envelopes.shared_case_selection(request) != frozen.get('shared_case'):
        raise ValueError('Selected shared case differs from its original host declaration')
    if request is not None and request['require_current']:
        _read_shared_case(request)
