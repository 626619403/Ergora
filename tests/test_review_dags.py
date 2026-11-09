"""Review data projections use the same compiled graph as formal admission."""

from copy import deepcopy
import json
import sys

import pytest

from ergora import workflow_definitions as workflows
from ergora.review_dags import ReviewDAG
from test_workflow_definitions import base, child, definition, grant, imported, leaf, ref


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
