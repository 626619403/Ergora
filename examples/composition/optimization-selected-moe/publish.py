"""Publish this fixed offline example through the existing immutable libraries."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import tempfile

from ergora import agent_definitions, workflow_definitions as workflows
from ergora.state import State


def publish(state: State, example: Path) -> dict:
    specification = json.loads((example / 'publication.json').read_bytes())
    for name in ('large-change', 'training-optimization', 'optimization-moe-dispatcher', 'optimization-moe-overlap'):
        workflows.install_preset(state, name)
    # The current ordinary parent is the revision base; no older source tree is required.
    composition = example.parent
    for folder in sorted((composition / 'agents').iterdir()):
        agent_definitions.import_bundle(state, folder)
    for name in ('kernel-implementer', 'validation-implementer', 'architecture-reviewer'):
        agent_definitions.import_bundle(state, composition.parent / 'agents' / name)
    for name in ('structure-review', 'correctness-review', 'test-value-review', 'parallel-review',
                 'specialist-work', 'specialist-delivery', 'preparation-inventory', 'preparation-plan',
                 'preparation-guide', 'prepared-delivery', 'native-development'):
        workflows.import_bundle(state, composition / name)
    source = specification['policy_source']
    original = workflows.get(state, source['id'], source['version'])
    if original['digest'] != source['digest']:
        raise ValueError('The exact current optimization policy source is unavailable')
    with tempfile.TemporaryDirectory(prefix='ergora-moe-policy-') as temporary:
        exported = Path(temporary) / 'source'
        workflows.export(state, source['id'], source['version'], exported)
        changes = {'schema_version': 1, 'operations': []}
        for name, details in specification['policy_files'].items():
            path = exported / name
            raw = path.read_bytes()
            if (hashlib.sha256(raw).hexdigest() != details['sha256'] or len(raw) != details['bytes']
                    or path.stat().st_mode & 0o111 != details['executable_bits']):
                raise ValueError('Optimization policy file differs from its pinned original: ' + name)
            changes['operations'].append({'op': 'write', 'path': name,
                'content_base64': base64.b64encode(raw).decode('ascii'),
                'executable_bits': details['executable_bits']})
        for name in ('inventory', 'plan', 'preparation', 'review', 'delivery', 'root'):
            base = specification['bases'][name]
            definition = json.loads((example / (name + '.revision.example.json')).read_bytes())
            arguments = {}
            if name == 'delivery':
                preview = workflows.revise(state, base['id'], base['version'], base['digest'], definition,
                                           resource_changes=changes, preview_resources=True)
                definition = preview['definition']
                arguments = {'resource_changes': changes, 'accepted_candidate': preview['candidate']}
            result = workflows.revise(state, base['id'], base['version'], base['digest'], definition,
                                      publish=True, **arguments)
            actual = {'kind': 'workflow', 'id': result['definition']['id'],
                      'version': result['definition']['version'], 'digest': result['digest']}
            if actual != specification['published'][name]:
                raise ValueError('Published example differs from its pinned reference: ' + name)
    root = specification['published']['root']
    grant = json.loads((example / 'grant.json').read_bytes())
    preview = workflows.preview(state.root, root['id'], root['version'], grant)
    manifest = workflows.freeze_manifest(state.root, root['id'], root['version'], grant, preview['preview_sha256'])
    return {'root': root, 'manifest': manifest, 'execution_authorized': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, required=True, help='Explicit definition-library home')
    options = parser.parse_args()
    print(json.dumps(publish(State(options.home), Path(__file__).resolve().parent), ensure_ascii=False))
