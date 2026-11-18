"""Review data projections use the same compiled graph as formal admission."""

from copy import deepcopy
import json
import sys

import pytest

from ergora import agent_definitions, reference_budget, workflow_definitions as workflows
from ergora.review_dags import ReviewDAG, preparation_members, preparation_stages
from test_workflow_definitions import EXAMPLES, base, child, definition, grant, imported, leaf, ref


def compile_graph(base, document):
    state, _, _ = base
    imported(base, document)
    return workflows.preview(state.root, document['id'], document['version'], grant())


def gather(identity, *dependencies):
    return {'id': identity, 'join': 'all', 'depends_on': list(dependencies)}


def test_control_predecessors_are_aggregated_without_becoming_data_or_structure_ancestors(base):
    _, agent, _ = base
    nodes = [leaf('structure', agent), leaf('slow', agent),
             {**leaf('correctness', agent), 'depends_on': ['structure']},
             gather('done', 'correctness', 'slow')]
    graph = compile_graph(base, definition('control-review', nodes))
    dag = ReviewDAG(graph, 'root')
    assert dag.predecessors == {'root/correctness': ('root/structure',), 'root/slow': (), 'root/structure': ()}
    assert dag.input_ports('root/correctness') == {
        'bindings': {'task': 'task'}, 'values': {'task': {'kind': 'task'}}, 'sources': []}
    assert dag.members['root/correctness']['parent'] == 'root'
    assert [item['text'] for item in dag.members['root/correctness']['resources']] == [
        item['text'] for item in dag.members['root/structure']['resources']]


def test_nested_multinamed_outputs_project_original_instances_once_and_wait_for_the_whole_call(base):
    _, agent, _ = base
    sub = definition('specialists', [leaf('correctness', agent), leaf('tests', agent),
                                      gather('both', 'correctness', 'tests')])
    sub['inputs'] = ['draft']
    for node in sub['nodes'][:2]:
        node['inputs']['task'] = {'input': 'draft'}
    sub['outputs'] = {'findings': {'node': 'both', 'output': 'result'}, 'original': {'input': 'draft'}}
    saved = imported(base, sub)
    nodes = [leaf('structure', agent),
        {**child('specialists', ref(saved, 'workflow')), 'depends_on': ['structure'],
         'inputs': {'draft': {'node': 'structure', 'output': 'result'}}},
        gather('gather', 'specialists'),
        {**leaf('audit', agent), 'depends_on': ['gather'],
         'inputs': {'task': {'node': 'gather', 'output': 'result'}}}, gather('done', 'audit')]
    dag = ReviewDAG(compile_graph(base, definition('nested-review', nodes)), 'root')
    assert dag.predecessors['root/audit'] == ('root/specialists/correctness', 'root/specialists/tests', 'root/structure')
    assert dag.input_ports('root/specialists/tests')['sources'] == ['root/structure']
    ports = dag.input_ports('root/audit')
    assert ports['bindings'] == {'task': 'root/gather#result'}
    assert ports['sources'] == ['root/specialists/correctness', 'root/specialists/tests', 'root/structure']
    assert ports['values']['root/gather#result']['outputs'] == {'root/specialists': {
        'findings': 'root/specialists/both#result', 'original': 'root/structure#result'}}
    assert len(ports['values']) == 5


@pytest.mark.parametrize('failure', ['omitted-leaf', 'passthrough', 'multiple-terminal', 'empty-join', 'external'])
def test_admission_rejects_incomplete_terminal_or_unexecuted_external_sources(base, failure):
    _, agent, _ = base
    doc = definition('invalid-review', [leaf('one', agent), leaf('two', agent), gather('done', 'one', 'two')])
    if failure == 'omitted-leaf':
        doc['nodes'][-1]['depends_on'] = ['one']
    elif failure == 'passthrough':
        doc['outputs'] = {'result': {'input': 'task'}}
    elif failure == 'multiple-terminal':
        doc['outputs']['other'] = {'node': 'one', 'output': 'result'}
    elif failure == 'empty-join':
        doc['nodes'][-1]['depends_on'] = []
    else:
        saved = imported(base, doc)
        doc = definition('outer', [leaf('outside', agent), {**child('selected', ref(saved, 'workflow')),
            'depends_on': ['outside'], 'inputs': {'task': {'node': 'outside', 'output': 'result'}}}])
    with pytest.raises(ValueError, match='cover every|explicit all-join|one terminal|nonempty|external|non-empty|not valid under any'):
        graph = compile_graph(base, doc)
        ReviewDAG(graph, 'root/selected' if failure == 'external' else 'root')


def test_shared_join_dag_is_bounded_by_unique_port_addresses(base):
    _, agent, _ = base
    nodes = [leaf('one', agent), leaf('two', agent)]
    for number in range(80):
        dependencies = (['one', 'two'] if number == 0 else ['one', 'j0'] if number == 1
                        else [f'j{number - 2}', f'j{number - 1}'])
        nodes.append(gather(f'j{number}', *dependencies))
    nodes.extend([{**leaf('audit', agent), 'depends_on': ['j79'],
                   'inputs': {'task': {'node': 'j79', 'output': 'result'}}}, gather('done', 'audit')])
    graph = compile_graph(base, definition('shared-review', nodes))
    dag = ReviewDAG(graph, 'root')
    calls = 0

    def count(frame, event, argument):
        nonlocal calls
        if event == 'call' and frame.f_code.co_filename.endswith('/review_dags.py'):
            calls += 1

    previous = sys.getprofile()
    try:
        sys.setprofile(count)
        ports = dag.input_ports('root/audit')
    finally:
        sys.setprofile(previous)
    assert ports['sources'] == ['root/one', 'root/two'] and len(ports['values']) == 82
    assert len(json.dumps(ports).encode()) < 20_000 and calls < 20 * len(nodes)


def test_unknown_port_and_non_predecessor_data_are_rejected_at_projection(base):
    _, agent, _ = base
    nodes = [leaf('one', agent), {**leaf('two', agent), 'depends_on': ['one'],
        'inputs': {'task': {'node': 'one', 'output': 'result'}}}, gather('done', 'two')]
    graph = compile_graph(base, definition('ports-review', nodes))
    for failure in ('port', 'control'):
        damaged = deepcopy(graph)
        item = next(item for item in damaged['instances'] if item['path'] == 'root/two')
        if failure == 'port':
            item['inputs']['task']['output'] = 'absent'
        else:
            item['depends_on'] = []
            next(item for item in damaged['instances'] if item['kind'] == 'join')['depends_on'].append('root/one')
        dag = ReviewDAG(damaged, 'root')
        with pytest.raises(ValueError, match='unknown output port|unfinished review producer'):
            dag.input_ports('root/two')


@pytest.fixture(params=[0, 2])
def preparation_graph(base, request):
    state, _, _ = base
    agent = agent_definitions.import_bundle(state, EXAMPLES / 'composition/agents/development-preparer')
    stages = {}
    for stage, role in (('inventory', 'inspector'), ('plan', 'planner')):
        nodes = [{**leaf('expert-' + str(index), ref(agent, 'agent')), 'role': role}
                 for index in range(request.param)]
        experts = [node['id'] for node in nodes]
        if experts:
            nodes.append(gather('analyses', *experts))
        nodes.append({**leaf('coordinator', ref(agent, 'agent')), 'role': role,
            'depends_on': ['analyses'] if experts else [],
            'inputs': {'task': {'node': 'analyses', 'output': 'result'} if experts else {'input': 'task'}}})
        nodes.append(gather('done', 'coordinator'))
        stages[stage] = imported(base, definition(stage + '-group', nodes))
    document = definition('preparation-groups', [child(stage, ref(saved, 'workflow'))
                                               for stage, saved in stages.items()])
    graph = compile_graph(base, document)
    selection = {'protocol': 'preparation-dag-v1', 'mode': 'text-only', 'repository_paths': ['src'],
        **{stage: {'instance': 'root/' + stage, 'coordinator': 'root/' + stage + '/coordinator'} for stage in stages}}
    return graph, selection


def test_preparation_groups_bind_all_original_ports_and_finite_stage_ids(preparation_graph):
    graph, selection = preparation_graph
    groups = preparation_members(graph, selection)
    members = {}
    for stage, group in groups.items():
        dag, coordinator = group['dag'], group['coordinator']
        others = dag.members.keys() - {coordinator}
        assert set(dag.predecessors[coordinator]) == set(dag.input_ports(coordinator)['sources']) == others
        ports = dag.input_ports(coordinator)
        assert {value['kind'] for value in ports['values'].values()
                if value.get('instance') in others} <= {stage + '-result'}
        assert all(not dag.input_ports(path)['sources'] for path in others)
        members.update(dag.members)
    frozen = {**selection, 'members': members}
    stages = preparation_stages(frozen)
    assert set(stages.values()) == members.keys() and len(stages) == len(members)
    for stage in groups:
        assert stages[stage] == groups[stage]['coordinator']
        assert {key for key, value in stages.items() if value in groups[stage]['dag'].members} == {
            stage if path == groups[stage]['coordinator'] else stage + ':' + path
            for path in groups[stage]['dag'].members}
    composition = {'preparation': frozen, 'execution': {'assignments': {'unit': 'root/work/one'}},
                   'members': {'root/review/one': {}}}
    assert reference_budget.call_slots(composition) == {
        **stages, 'work:unit': 'root/work/one', 'review:root/review/one': 'root/review/one'}


@pytest.mark.parametrize('failure', ['data', 'late-member', 'wrong-role', 'write', 'read-ceiling', 'terminal'])
@pytest.mark.parametrize('preparation_graph', [2], indirect=True)
def test_preparation_cannot_hide_or_bypass_required_producers(preparation_graph, failure):
    graph, selection = preparation_graph
    graph = deepcopy(graph)
    nodes = {node['path']: node for node in graph['instances']}
    coordinator = nodes[selection['inventory']['coordinator']]
    if failure == 'data':
        coordinator['inputs'] = {'task': {'input': 'task'}}
    elif failure == 'late-member':
        extra = {**deepcopy(coordinator), 'path': 'root/inventory/late', 'depends_on': [],
                 'inputs': {'task': {'input': 'task'}}}
        graph['instances'].append(extra)
        nodes['root/inventory/done']['depends_on'].append(extra['path'])
    elif failure == 'wrong-role':
        coordinator['role'] = 'planner'
    elif failure == 'write':
        coordinator['permissions']['shell'] = True
    elif failure == 'read-ceiling':
        coordinator['permissions']['read'] = ['definitions']
    else:
        nodes['root/inventory']['outputs'] = {'result': {'node': 'coordinator', 'output': 'result'}}
    with pytest.raises(ValueError, match='coordinator|wrong role|read-only|read ceiling|explicit all-join'):
        preparation_members(graph, selection)


@pytest.mark.parametrize('failure', ['outside', 'overlap', 'coordinator'])
def test_preparation_stage_ids_never_drop_or_alias_a_frozen_member(preparation_graph, failure):
    graph, selection = preparation_graph
    groups = preparation_members(graph, selection)
    frozen = deepcopy(selection)
    frozen['members'] = {path: leaf for group in groups.values() for path, leaf in group['dag'].members.items()}
    if failure == 'outside':
        frozen['members']['root/hidden'] = {}
    elif failure == 'overlap':
        frozen['inventory']['instance'] = 'root'
    else:
        frozen['plan']['coordinator'] = 'root/not-selected'
    with pytest.raises(ValueError, match='disjoint|coordinator|exactly'):
        preparation_stages(frozen)


@pytest.mark.parametrize('preparation_graph', [2], indirect=True)
def test_preparation_terminal_cannot_hide_coordinator_behind_a_workflow_output(base, preparation_graph):
    _, selection = preparation_graph
    state, _, _ = base
    body = deepcopy(workflows.get(state, 'inventory-group', '1.0.0')['definition'])
    body.update(id='early-inventory-output', outputs={'result': {'node': 'analyses', 'output': 'result'}})
    hidden = imported(base, body)
    wrapper = imported(base, definition('inventory-output-wrapper', [
        child('body', ref(hidden, 'workflow')), gather('done', 'body')]))
    plan = workflows.get(state, 'plan-group', '1.0.0')
    document = definition('wrapped-preparation', [child('inventory', ref(wrapper, 'workflow')),
                                                child('plan', ref(plan, 'workflow'))])
    actual = compile_graph(base, document)
    selection = deepcopy(selection)
    selection['inventory']['coordinator'] = 'root/inventory/body/coordinator'
    # The wrapper is complete only after all children, including coordinator,
    # but its declared result carries only the earlier experts' outputs.
    with pytest.raises(ValueError, match='terminal|all-join'):
        preparation_members(actual, selection)
