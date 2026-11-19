"""Publish one cross-end development task revision through the existing libraries."""

import argparse
from copy import deepcopy
import json
from pathlib import Path

from ergora import workflow_definitions as workflows
from ergora.state import State


def publish(state: State, example: Path, *, version: str) -> dict:
    installation = workflows.install_preset(state, 'large-change')
    agents = {reference['id']: reference for reference in installation['agents']}
    bases = {'root': installation['root']}
    documents = {}
    # Follow the installed current graph, retaining its actual immutable references.
    for name, child in (('root', 'development'), ('delivery', 'preparation')):
        reference = bases[name]
        documents[name] = workflows.get(state, reference['id'], reference['version'])['definition']
        bases['delivery' if name == 'root' else 'preparation'] = next(
            node['ref'] for node in documents[name]['nodes'] if node['id'] == child)
    reference = bases['preparation']
    documents['preparation'] = workflows.get(state, reference['id'], reference['version'])['definition']
    for name in ('inventory', 'plan'):
        bases[name] = next(node['ref'] for node in documents['preparation']['nodes'] if node['id'] == name)
        reference = bases[name]
        documents[name] = workflows.get(state, reference['id'], reference['version'])['definition']

    selected = (
        ('contract', 'ergora-api-contract-author'),
        ('server', 'ergora-server-implementer'),
        ('client', 'ergora-client-implementer'),
        ('validation', 'ergora-compatibility-validator'),
    )
    receipts, references = {}, {}
    for name, role in (('inventory', 'inspector'), ('plan', 'planner')):
        definition = deepcopy(documents[name])
        definition.update(id='ergora-cross-end-' + name, version=version,
                          description='Selected cross-end ' + name + ' experts and canonical coordinator.')
        experts = []
        for identity, agent in selected:
            after_contract = name == 'plan' and identity in ('server', 'client')
            experts.append({
                'id': identity, 'ref': agents[agent], 'role': role,
                'depends_on': ['contract'] if after_contract else [],
                'inputs': {'task': {'node': 'contract', 'output': 'result'} if after_contract else {'input': 'task'}},
                'permissions': deepcopy(definition['permissions']),
            })
        members = [node['id'] for node in experts]
        coordinator = deepcopy(next(node for node in definition['nodes'] if node['id'] == 'coordinator'))
        coordinator.update(role=role, depends_on=['expert-results'],
                           inputs={'task': {'node': 'expert-results', 'output': 'result'}})
        definition['nodes'] = [
            *experts,
            {'id': 'expert-results', 'join': 'all', 'depends_on': members},
            coordinator,
            {'id': 'done', 'join': 'all', 'depends_on': [*members, 'coordinator']},
        ]
        definition['outputs'] = {'result': {'node': 'done', 'output': 'result'}}
        base = bases[name]
        result = workflows.revise(state, base['id'], base['version'], base['digest'], definition, publish=True)
        receipts[name] = result
        references[name] = {'kind': 'workflow', 'id': result['definition']['id'],
                            'version': result['definition']['version'], 'digest': result['digest']}

    # Publish children first; every parent uses the preceding publication receipt.
    for name, replacements in (
        ('preparation', {'inventory': 'inventory', 'plan': 'plan'}),
        ('delivery', {'preparation': 'preparation'}),
        ('root', {'development': 'delivery'}),
    ):
        definition = deepcopy(documents[name])
        definition.update(id='ergora-cross-end-' + ('template' if name == 'root' else name), version=version)
        for node in definition['nodes']:
            if node['id'] in replacements:
                node['ref'] = references[replacements[node['id']]]
        base = bases[name]
        result = workflows.revise(state, base['id'], base['version'], base['digest'], definition, publish=True)
        receipts[name] = result
        references[name] = {'kind': 'workflow', 'id': result['definition']['id'],
                            'version': result['definition']['version'], 'digest': result['digest']}

    root = references['root']
    grant = json.loads((example / 'grant.json').read_bytes())
    preview = workflows.preview(state.root, root['id'], root['version'], grant)
    manifest = workflows.freeze_manifest(state.root, root['id'], root['version'], grant, preview['preview_sha256'])
    return {'installation': installation, 'bases': bases, 'publications': receipts,
            'references': references, 'root': root, 'preview_sha256': preview['preview_sha256'],
            'manifest': manifest, 'execution_authorized': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, required=True, help='Explicit definition-library home')
    parser.add_argument('--version', required=True, help='Unused task-revision version, for example 1.0.0')
    options = parser.parse_args()
    print(json.dumps(publish(State(options.home), Path(__file__).resolve().parent, version=options.version),
                     ensure_ascii=False))
