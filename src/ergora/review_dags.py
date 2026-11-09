"""Bounded review dependencies and port projections from the original static graph.

This module computes data. Temporal still schedules jobs, and the original
executor and receipt owners establish runtime authority and artifact identity.
"""

from graphlib import CycleError, TopologicalSorter
import json


class ReviewDAG:
    """Derive one selected subtree without persisting a second execution graph."""

    def __init__(self, graph: dict, selected: str):
        self._instances = {item['path']: item for item in graph['instances']}
        self._selected = selected
        self._aliases = {}
        root = self._instances[selected]
        if root['kind'] != 'workflow' or set(root['inputs']) != {'task'} or len(root['outputs']) != 1:
            raise ValueError('Review DAG requires one task input and one terminal output')
        self.members = {path: item for path, item in sorted(self._instances.items())
                        if item['kind'] == 'agent' and path.startswith(selected + '/')}
        if not self.members:
            raise ValueError('Review DAG requires reviewer leaves')
        for leaf in self.members.values():
            if (leaf['role'] != 'reviewer' or leaf['permissions']['write']
                    or leaf['permissions']['shell'] or leaf['permissions']['network']):
                raise ValueError('Review DAG requires read-only reviewers without shell or network')
        scopes = {}
        for leaf in self.members.values():
            for scope in leaf['concurrency_scopes']:
                if (not isinstance(scope['path'], str) or type(scope['limit']) is not int or scope['limit'] < 1
                        or scopes.setdefault(scope['path'], scope['limit']) != scope['limit']):
                    raise ValueError('Review DAG concurrency scopes must have consistent positive limits')
        # Ancestors outside the selected subtree supply only the original task;
        # their other children are not part of this formal review stage.
        node, port = root, 'task'
        while True:
            origin = node['inputs'][port]
            if node['depends_on'] or 'input' not in origin:
                raise ValueError('Selected review DAG cannot depend on unexecuted external nodes')
            port = origin['input']
            if node['parent'] is None:
                if port != 'task':
                    raise ValueError('Selected review DAG must resolve to the root task')
                break
            node = self._instances[node['parent']]

        nodes = {path: item for path, item in self._instances.items()
                 if path == selected or path.startswith(selected + '/')}
        children = {path: set() for path in nodes}
        for path, node in nodes.items():
            if path != selected:
                children[node['parent']].add(path)
        dependencies = {}
        for path, node in nodes.items():
            if node['kind'] == 'join' and (node['join'] != 'all' or not node['depends_on']):
                raise ValueError('Review DAG requires nonempty all-joins')
            dependencies[path] = self._activation(path) | (children[path] if node['kind'] == 'workflow' else set())
            for dependency in dependencies[path]:
                self._inside(dependency)
        try:
            order = tuple(TopologicalSorter(dependencies).static_order())
        except CycleError as error:
            raise ValueError('Review DAG contains a dependency cycle') from error
        completed = {}
        for path in order:
            leaves = {path} if nodes[path]['kind'] == 'agent' else set()
            for dependency in dependencies[path]:
                leaves.update(completed[dependency])
            completed[path] = frozenset(leaves)
        self.predecessors = {path: tuple(sorted(completed[path] - {path})) for path in self.members}
        output = next(iter(root['outputs']))
        terminal = self._resolve(selected, output, 'output')
        if terminal == 'task' or self._instances[terminal.rsplit('#', 1)[0]]['kind'] != 'join':
            raise ValueError('Review DAG terminal output must project an explicit all-join')
        origin = root['outputs'][output]
        if ('node' not in origin
                or completed[selected + '/' + origin['node']] != self.members.keys()):
            raise ValueError('Review DAG all-join must cover every reviewer, including serial predecessors')

    def _inside(self, path):
        if path != self._selected and not path.startswith(self._selected + '/'):
            raise ValueError('Review DAG port or dependency refers outside the selected subtree')
        if path not in self._instances:
            raise ValueError('Review DAG refers to an unknown instance')
        return self._instances[path]

    def _activation(self, path):
        """A leaf also waits for dependencies of each enclosing workflow call."""
        dependencies = set()
        while path != self._selected:
            node = self._inside(path)
            dependencies.update(node['depends_on'])
            path = node['parent']
        return dependencies

    def _resolve(self, path, port, direction):
        """Follow aliases iteratively; valid long DAGs must not use Python recursion."""
        visited = set()
        key = direction, path, port
        while key not in self._aliases:
            if key in visited:
                raise ValueError('Review DAG contains a port alias cycle')
            visited.add(key)
            direction, path, port = key
            node = self._inside(path) if direction == 'output' else self._instances[path]
            if port not in node[direction + 's']:
                raise ValueError('Review DAG refers to an unknown ' + direction + ' port')
            if direction == 'output' and node['kind'] != 'workflow':
                value = path + '#' + port
                break
            origin = node[direction + 's'][port]
            if direction == 'output':
                key = (('input', path, origin['input']) if 'input' in origin
                       else ('output', path + '/' + origin['node'], origin['output']))
            elif 'input' not in origin:
                key = 'output', node['parent'] + '/' + origin['node'], origin['output']
            elif node['parent'] is None:
                value = 'task'
                break
            else:
                key = 'input', node['parent'], origin['input']
        else:
            value = self._aliases[key]
        for alias in visited:
            self._aliases[alias] = value
        return value

    def input_ports(self, member: str) -> dict:
        """Return a shared value table and the exact required review producers.

        Values contain original instance addresses, never model-supplied paths
        or recursively expanded audit text. Runtime owners add verified bytes.
        """
        leaf = self.members[member]
        bindings = {port: self._resolve(member, port, 'input') for port in leaf['inputs']}
        values, sources, pending, used = {}, set(), list(bindings.values()), 0
        while pending:
            address = pending.pop()
            if address in values:
                continue
            if address == 'task':
                value = {'kind': 'task'}
            else:
                path, port = address.rsplit('#', 1)
                node = self._inside(path)
                if node['kind'] == 'agent':
                    value = {'kind': 'review-result', 'instance': path}
                    sources.add(path)
                else:
                    outputs = {dependency: {name: self._resolve(dependency, name, 'output')
                                             for name in self._instances[dependency]['outputs']}
                               for dependency in node['depends_on']}
                    value = {'kind': 'all-join', 'instance': path, 'outputs': outputs}
                    pending.extend(source for ports in outputs.values() for source in ports.values())
            used += len(json.dumps({address: value}, ensure_ascii=False, allow_nan=False).encode('utf-8'))
            if used > 1_000_000:
                raise ValueError('Complete review port table exceeds 1,000,000 bytes')
            values[address] = value
        if not sources <= set(self.predecessors[member]):
            raise ValueError('Review DAG input requires an unfinished review producer')
        return {'bindings': bindings, 'values': dict(sorted(values.items())), 'sources': sorted(sources)}
