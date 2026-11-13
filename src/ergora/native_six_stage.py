"""Bind one ordinary template call to the existing six-stage task owner.

This is a frozen graph projection, never a graph runner or another run ledger.
Admission and original-input readers use the same supported-shape contract.
"""


def invocation(graph: dict, selection: dict, task_type: str) -> dict:
    """Return the exact parent chain for a single direct six-stage call."""
    native = selection['native']
    if (not isinstance(native, dict) or set(native) != {'protocol', 'instance'}
            or native['protocol'] != 'six-stage-v1' or not isinstance(native['instance'], str)):
        raise ValueError('Native six-stage selection requires its protocol and instance')
    instances = {item['path']: item for item in graph['instances']}
    position = native['instance']
    selected = instances.get(position)
    if selected is None or selected['kind'] != 'workflow' or selected['parent'] is None:
        raise ValueError('Native six-stage invocation requires an instance inside an ordinary parent template')
    stages = [selection['preparation'][stage] for stage in ('inventory', 'plan')]
    work, review = selection['execution']['instance'], selection['review_instance']
    if any(not path.startswith(position + '/') for path in [*stages, work, review]):
        raise ValueError('Every selected stage must belong to the native six-stage instance')
    if any(instances[path]['parent'] != position for path in (work, review)):
        raise ValueError('Native six-stage work and review must be direct child templates')
    review_outputs = instances[review]['outputs']
    if (len(selected['outputs']) != 1 or len(review_outputs) != 1
            or next(iter(selected['outputs'].values())) != {
                'node': review.rsplit('/', 1)[1], 'output': next(iter(review_outputs))}):
        raise ValueError('Native six-stage output must forward its selected review result')

    # Preparation wrappers carry inherited resources, but cannot hide another
    # branch. Work/review subgraphs retain their own original DAG validation.
    covered = {position}
    for path in stages:
        while path != position:
            covered.add(path)
            path = instances[path]['parent']
    covered.update(path for path in instances if any(path == root or path.startswith(root + '/')
                                                   for root in (work, review)))
    descendants = {path for path in instances if path == position or path.startswith(position + '/')}
    if covered != descendants:
        raise ValueError('Native six-stage instance contains an unselected branch')

    lineage = []
    child = None
    node = selected
    while True:
        path = node['path']
        if (node['kind'] != 'workflow' or node['inputs'] != {'task': {'input': 'task'}}
                or node['depends_on']):
            raise ValueError('Native six-stage ancestors must forward the root task without external dependencies')
        if child is not None:
            children = {item['path'] for item in instances.values() if item['parent'] == path}
            if (children != {child['path']} or len(node['outputs']) != 1
                    or next(iter(node['outputs'].values())) != {
                        'node': child['path'].rsplit('/', 1)[1], 'output': next(iter(child['outputs']))}):
                raise ValueError('Native six-stage parent must contain only its selected call and forward its result')
        lineage.append({'instance': path, 'definition': node['ref']})
        if node['parent'] is None:
            break
        child, node = node, instances[node['parent']]
    return {**native, 'task_type': task_type, 'lineage': list(reversed(lineage))}
