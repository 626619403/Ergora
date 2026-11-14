"""Explicit current project sources, carried by the original root resource tree."""

import base64
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from . import memory, skill_assets, task_envelopes
from .asset_trees import digest_tree
from .state import State


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


@contextmanager
def selected_manifest(state: State, project_id: str, option: dict, selection: dict, working_directory: Path):
    """Derive a new root only inside the supervised original preparation tree."""
    from . import workflow_definitions

    source = Path(option['manifest']).expanduser().absolute()
    original = workflow_definitions.inspect_manifest(source)
    if original['digest'] != option['manifest_digest']:
        raise ValueError('Selected composition manifest digest changed')
    sources, paths = _sources(state, project_id, selection)
    working_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix='.task-context-', dir=working_directory) as temporary:
        work = Path(temporary)
        copied = work / 'base'
        shutil.copytree(source, copied, symlinks=True)
        checked = workflow_definitions.inspect_manifest(copied)
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
                    'base_root': root, 'base_definition': document['definition'], 'selection': selection, **sources}
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
        changes = {'schema_version': 1, 'operations': operations}
        preview = library.revise(root['id'], root['version'], root['digest'], definition,
                                 resource_changes=changes, preview_resources=True)
        library.revise(root['id'], root['version'], root['digest'], definition, publish=True,
                       resource_changes=changes, accepted_candidate=preview['candidate'])
        manifest = workflow_definitions.prepare_manifest(copied / 'assets', root['id'], definition['version'],
                                                        checked['manifest']['grant'], work / 'selected')
        context = {'project': project_id, 'base_manifest_digest': checked['digest'],
                   'selection': selection, 'resource_sha256': resource_sha256}
        yield {**option, 'manifest': manifest['path'], 'manifest_digest': manifest['digest']}, context


def require_current(state: State, project_id: str, document: dict) -> None:
    """Check just before first intent; recovery of an existing intent keeps its bytes."""
    frozen = task_envelopes.selected_context(document)
    if frozen['project'] != project_id:
        raise ValueError('Selected task context belongs to another project')
    current, _ = _sources(state, project_id, frozen['selection'])
    if any(current[key] != frozen[key] for key in ('memories', 'skills')):
        raise ValueError('Selected task context content changed; prepare a fresh explicit selection')
