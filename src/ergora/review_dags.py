"""Bounded review dependencies and port projections from the original static graph.

This module computes data. Temporal still schedules jobs, and the original
executor and receipt owners establish runtime authority and artifact identity.
"""

from graphlib import CycleError, TopologicalSorter
import json
from pathlib import PurePosixPath


def require_root_task(instances: dict, leaf: dict) -> None:
    """A direct stage leaf consumes no unexecuted sibling data or control edge."""
    node, port, visited = leaf, 'task', set()
    while True:
        if (node['path'] in visited or set(node['inputs']) != {port} or node['depends_on']
                or 'input' not in node['inputs'][port]):
            raise ValueError('Composition leaf requires a direct root task input')
        visited.add(node['path'])
        port = node['inputs'][port]['input']
        if node['parent'] is None:
            if port != 'task':
                raise ValueError('Composition leaf must resolve to the root task input')
            return
        node = instances[node['parent']]


def preparation_members(graph: dict, selection: dict) -> dict:
    """Project the two original preparation calls, without a mixed-role schedule."""
    paths = selection['repository_paths']
    if (not isinstance(paths, list) or not 1 <= len(paths) <= 128
            or any(not isinstance(name, str) or not name or len(name) > 4096
                   or name != PurePosixPath(name).as_posix() or PurePosixPath(name).is_absolute()
                   or '..' in PurePosixPath(name).parts or any(char in name for char in ('\\', ':', '\0', '\n', '\r'))
                   for name in paths) or len(set(paths)) != len(paths)):
        raise ValueError('Preparation requires distinct canonical relative repository paths')
    instances = {item['path']: item for item in graph['instances']}
    members = {}
    for stage, role in (('inventory', 'inspector'), ('plan', 'planner')):
        leaf = instances.get(selection[stage])
        if leaf is None or leaf['kind'] != 'agent' or leaf['role'] != role:
            raise ValueError('Preparation must select an ' + role + ' Agent leaf')
        if leaf['permissions']['write'] or leaf['permissions']['shell'] or leaf['permissions']['network']:
            raise ValueError('Preparation requires read-only leaves without shell or network')
        for name in paths:
            wanted = 'workspace' if name == '.' else 'workspace/' + name
            if not any(wanted == prefix or wanted.startswith(prefix + '/') for prefix in leaf['permissions']['read']):
                raise ValueError('Preparation repository paths exceed the leaf read ceiling: ' + name)
        require_root_task(instances, leaf)
        members[stage] = leaf
    return members


class StageDAG:
    """Derive one selected subtree without persisting a second execution graph."""

    def __init__(self, graph: dict, selected: str, *, role='reviewer', external=None):
        self._instances = {item['path']: item for item in graph['instances']}
        self._selected = selected
        self._aliases = {}
        self._external = external
        self._result_kind = 'review-result' if role == 'reviewer' else 'work-result'
        if selected not in self._instances:
            raise ValueError('Unknown selected stage subtree: ' + selected)
        root = self._instances[selected]
        if root['kind'] != 'workflow' or set(root['inputs']) != {'task'} or len(root['outputs']) != 1:
            raise ValueError('Review DAG requires one task input and one terminal output')
        self.members = {path: item for path, item in sorted(self._instances.items())
                        if item['kind'] == 'agent' and path.startswith(selected + '/')}
        if not self.members:
            raise ValueError('Review DAG requires reviewer leaves')
        for leaf in self.members.values():
            if leaf['role'] != role:
                raise ValueError('Stage DAG leaf has the wrong role: ' + leaf['path'])
            if role == 'reviewer' and (leaf['permissions']['write']
                    or leaf['permissions']['shell'] or leaf['permissions']['network']):
                raise ValueError('Review DAG requires read-only reviewers without shell or network')
            if role == 'implementer' and (not leaf['permissions']['write']
                    or not leaf['permissions']['shell'] or leaf['permissions']['network']):
                raise ValueError('Work DAG requires writable shell-enabled leaves without network origins')
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
            if set(node['depends_on']) - ({external._selected} if external else set()):
                raise ValueError('Selected review DAG cannot depend on unexecuted external nodes')
            if 'input' not in origin:
                address = self._resolve(node['path'], port, 'input')
                if external is None or address != external.terminal:
                    raise ValueError('Stage input must project the selected work terminal or root task')
                break
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
                if dependency not in nodes:
                    raise ValueError('Stage control dependencies must stay inside its selected subtree')
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
        self.terminal = terminal
        if terminal == 'task' or self._instances[terminal.rsplit('#', 1)[0]]['kind'] != 'join':
            raise ValueError('Review DAG terminal output must project an explicit all-join')
        origin = root['outputs'][output]
        if ('node' not in origin
                or completed[selected + '/' + origin['node']] != self.members.keys()):
            raise ValueError('Review DAG all-join must cover every reviewer, including serial predecessors')

    def _inside(self, path):
        if path != self._selected and not path.startswith(self._selected + '/'):
            if self._external is not None:
                return self._external._inside(path)
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
                    external = self._external is not None and path in self._external.members
                    value = {'kind': 'work-result' if external else self._result_kind, 'instance': path}
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
        allowed = set(self.predecessors[member]) | (set(self._external.members) if self._external else set())
        if not sources <= allowed:
            raise ValueError('Review DAG input requires an unfinished review producer')
        return {'bindings': bindings, 'values': dict(sorted(values.items())), 'sources': sorted(sources)}


class ReviewDAG(StageDAG):
    """The unchanged v4 read-only, root-task-only stage contract."""


class WorkDelivery:
    """Project the original units onto two disjoint stages, never schedule them."""

    def __init__(self, graph: dict, execution: dict, review_instance: str, units: list[dict], *, preparation=None):
        self.work = StageDAG(graph, execution['instance'], role='implementer')
        self.review = StageDAG(graph, review_instance, external=self.work)
        self.preparation = preparation_members(graph, preparation) if preparation is not None else {}
        work_paths, review_paths = set(self.work.members), set(self.review.members)
        preparation_paths = {leaf['path'] for leaf in self.preparation.values()}
        agents = {item['path'] for item in graph['instances'] if item['kind'] == 'agent'}
        if (work_paths & review_paths or preparation_paths & (work_paths | review_paths)
                or work_paths | review_paths | preparation_paths != agents):
            raise ValueError('Work and review must cover exactly all Agent leaves without overlap')
        self.assignments = execution['assignments']
        original = {unit['id']: unit for unit in units}
        if preparation is not None:
            for unit in units:
                for name in unit['paths']:
                    if not any(prefix == '.' or name == prefix or name.startswith(prefix + '/')
                               for prefix in preparation['repository_paths']):
                        raise ValueError('Preparation repository paths must cover the original work unit paths')
        if (set(self.assignments) != original.keys() or set(self.assignments.values()) != work_paths
                or len(self.assignments) != len(work_paths)):
            raise ValueError('Work assignments require exactly one distinct implementer instance per original unit')
        self.units = {path: identity for identity, path in self.assignments.items()}
        try:
            order = tuple(TopologicalSorter({key: set(unit['depends_on']) for key, unit in original.items()}).static_order())
        except CycleError as error:
            raise ValueError('Original work units contain a cycle') from error
        predecessors = {}
        for key in order:
            if key not in original:
                raise ValueError('Original unit refers to an unknown dependency')
            predecessors[key] = set(original[key]['depends_on'])
            for parent in original[key]['depends_on']:
                predecessors[key].update(predecessors[parent])
            path = self.assignments[key]
            if {self.assignments[parent] for parent in predecessors[key]} != set(self.work.predecessors[path]):
                raise ValueError('Static work order differs from original work-unit transitive dependencies')
            permissions = self.work.members[path]['permissions']
            for name in original[key]['paths']:
                wanted = 'workspace/' + name
                if not any(wanted == prefix or wanted.startswith(prefix + '/') for prefix in permissions['write']):
                    raise ValueError('Complete original unit paths exceed its effective Agent write ceiling: ' + key)
            self.work.input_ports(path)
        for path in self.review.members:
            self.review.input_ports(path)
