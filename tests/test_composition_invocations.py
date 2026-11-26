"""Independent leaf calls bind complete input and explicit native tool restrictions."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

import ergora.agents.backends as agent_backends
import ergora.definitions.agents as agent_definitions
import ergora.agents.runs as agent_runs
import ergora.agents.native_sources as native_sources
import ergora.agents.invocation as agents
import ergora.configuration.projects as projects
import ergora.definitions.workflows as workflows
from ergora.runtime import processes
from ergora.interfaces.cli import main
from ergora.storage.state import State
from ergora._paths import IMPORT_ROOT


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize("name,effort", [("performance", "high"), ("resource-lifecycle", "medium"),
                                       ("dependency", "medium"), ("security", "medium")])
def test_selected_specialist_floor_rejects_lower_override_before_any_native_call(tmp_path, monkeypatch, name, effort):
    from test_presets import _selected_engineering_review
    state = State(tmp_path / "state")
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", str(repository)], capture_output=True, check=True)
    projects.create(state, "demo", repository)
    installed, selected = _selected_engineering_review(state)
    root = selected["definition"]
    if name in ("dependency", "security"):
        root = json.loads(json.dumps(root))
        root.update(id="selected-" + name, version="1.0.0")
        reference = next(item for item in installed["agents"] if item["id"] == "ergora-" + name + "-reviewer")
        root["nodes"].insert(-1, {"id": name, "ref": reference, "role": "reviewer", "depends_on": [],
            "review_requirement": "required", "permissions": root["permissions"], "inputs": {"task": {"input": "task"}}})
        root["nodes"][-1]["depends_on"].append(name)
        workflows.revise(state, selected["definition"]["id"], selected["definition"]["version"],
                         selected["digest"], root, publish=True)
    grant = {"schema_version": 1, "permissions": root["permissions"], "limits": root["limits"]}
    destination = tmp_path / "input"
    workflows.prepare_input(state.root, root["id"], root["version"], "root/" + name, grant,
                            b"Complete exact review source and original requirements.", destination, 1_000_000)
    monkeypatch.setattr(processes, "run", lambda *args, **kwargs: pytest.fail("Rejected review must not invoke a model"))
    with pytest.raises(ValueError, match="at least"):
        agent_runs.run_input(state, "demo", destination,
            binding_override={"tool": "codex", "model": "gpt-6.2-sol", "reasoning_effort": effort})
    assert agent_runs.runs(state, "demo") == []


@pytest.fixture
def prepared(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    state = State(tmp_path / "state")
    projects.create(state, "demo", repo)

    def build(*, binding=None, permission=None, minimum=None):
        agent_source = tmp_path / "agent"
        shutil.copytree(EXAMPLES / "agents/architecture-reviewer", agent_source)
        doc = json.loads((agent_source / "agent.json").read_text())
        doc["backend"] = binding or {"tool": "codex"}
        if minimum is not None:
            doc["invocation_minimum"] = minimum
        (agent_source / "agent.json").write_text(json.dumps(doc), encoding="utf-8")
        agent = agent_definitions.import_bundle(state, agent_source)
        source = tmp_path / "workflow"
        shutil.copytree(EXAMPLES / "composition/structure-review", source)
        doc = json.loads((source / "workflow.json").read_text())
        doc["nodes"][0]["ref"]["digest"] = agent["digest"]
        if permission:
            key, value = permission
            doc["permissions"][key] = value
            doc["nodes"][0]["permissions"][key] = value
        (source / "workflow.json").write_text(json.dumps(doc), encoding="utf-8")
        workflows.import_bundle(state, source)
        grant = {"schema_version": 1, "permissions": doc["permissions"], "limits": doc["limits"]}
        target = tmp_path / "prepared"
        workflows.prepare_input(state.root, "structure-review", "1.0.0", "root/review", grant,
                                "Review the supplied candidate. 核对结构。\r\n".encode(), target, 30000)
        return state, repo, target
    return build


@pytest.mark.parametrize('case', ['success', 'failed-first', 'result-budget', 'lost-outcome'])
def test_standalone_graph_executes_nested_ports_and_keeps_original_attempts(prepared, tmp_path, monkeypatch, capsys, case):
    from ergora.agents import graphs

    fail_first = case == 'failed-first'
    original_result = {'summary': 'Review', 'artifacts': {'response': 'Verified output'}, 'decision': 'approve'}
    if case == 'result-budget':
        single_result_bytes = len(json.dumps(original_result, sort_keys=True).encode('utf-8'))
        monkeypatch.setattr(graphs, '_RESULT_LIMIT', single_result_bytes + single_result_bytes//2)
    state, _, _ = prepared()
    child = workflows.get(state, 'structure-review', '1.0.0')
    root = child['definition']
    leaf = root['nodes'][0]
    draft = {**root, 'id': 'standalone-review', 'inputs': ['request'], 'outputs': {
        'joined': {'node': 'join', 'output': 'result'}, 'original': {'input': 'request'}}, 'nodes': [
        {'id': 'nested', 'ref': {'kind': 'workflow', 'id': root['id'], 'version': root['version'], 'digest': child['digest']},
         'depends_on': [], 'inputs': {'task': {'input': 'request'}}},
        {**leaf, 'id': 'followup', 'depends_on': ['nested'], 'inputs': {'task': {'node': 'nested', 'output': 'findings'}}},
        {'id': 'join', 'join': 'all', 'depends_on': ['nested', 'followup']},
    ]}
    workflows.revise(state, root['id'], root['version'], child['digest'], draft, publish=True)
    grant = {'schema_version': 1, 'permissions': draft['permissions'], 'limits': draft['limits']}
    manifest = tmp_path / 'manifest'
    selected = workflows.prepare_manifest(state.root, draft['id'], draft['version'], grant, manifest)
    inputs, destination = tmp_path / 'inputs.json', tmp_path / 'graph-run'
    supplied = {'requirement': '保留依赖', 'fail': fail_first}
    inputs.write_text(json.dumps({'request': supplied}), encoding='utf-8')
    if case == 'success':
        grant_path, route_path = tmp_path / 'grant.json', tmp_path / 'admission.json'
        grant_path.write_text(json.dumps(grant), encoding='utf-8')
        route_path.write_text(json.dumps({'route': 'standalone-graph', 'project': 'demo', 'revision': 1,
            'inputs': {'request': supplied}, 'max_prompt_bytes': 50000, 'timeout': 20,
            'manifest': str(manifest), 'manifest_digest': selected['digest']}), encoding='utf-8')
        invocation = ['--home', str(state.root), 'composition', 'preview', draft['id'], draft['version']]
        compiled = []
        compile_input = workflows.compile_input

        def observe(comp, instance, *args, **kwargs):
            compiled.append(instance)
            return compile_input(comp, instance, *args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(workflows, 'compile_input', observe)
            assert main([*invocation, '--grant', str(grant_path), '--admission', str(route_path)]) == 0
        assert compiled == ['root/nested/review']
        inspected = json.loads(capsys.readouterr().out)
        assert inspected['composition'] == workflows.inspect_manifest(manifest, material=True)['composition']
        admission = inspected['route_admission']
        assert admission['capability'] == {'route': 'standalone-graph', 'status': 'admitted'}
        assert admission['manifest_digest'] == selected['digest'] and admission['runtime_status'] == 'not_queried'
        assert {row['instance'] for row in admission['bindings']} == {'root/nested/review', 'root/followup'}
        assert all(row['mode'] == 'text-only' for row in admission['bindings'])
        assert not destination.exists() and agent_runs.runs(state, 'demo') == []
    script, call_log = tmp_path / 'provider.py', tmp_path / 'calls.jsonl'
    script.write_text('''import json, sys
from pathlib import Path
value = json.loads(sys.stdin.read().split('Workflow task port (JSON value):\\n')[-1])
with Path(sys.argv[2]).open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(value) + '\\n')
if value.get('fail'):
    sys.exit(7)
Path(sys.argv[1]).write_text(json.dumps({'summary': 'Review', 'artifacts': {'response': 'Verified output'},
                                       'decision': 'approve'}), encoding='utf-8')
''', encoding='utf-8')
    original = agent_backends.CodexBackend.command

    def command(backend, request):
        argv, prompt = original(backend, request)
        assert argv[argv.index('--sandbox') + 1] == 'read-only'
        return [sys.executable, str(script), argv[argv.index('--output-last-message') + 1], str(call_log)], prompt

    monkeypatch.setattr(agent_backends.CodexBackend, 'command', command)
    monkeypatch.setattr(agent_backends.CodexBackend, 'check_invocation', lambda self: None)
    if case == 'lost-outcome':
        original_run = agent_runs.run_input

        def lose_outcome(*args, **kwargs):
            original_run(*args, **kwargs)
            raise OSError('Original leaf reply was lost')

        monkeypatch.setattr(agent_runs, 'run_input', lose_outcome)
    process_deadlines = []
    native = processes.run

    def observe(*args, **kwargs):
        process_deadlines.append(kwargs['deadline'])
        return native(*args, **kwargs)

    monkeypatch.setattr(processes, 'run', observe)
    argv = ['--home', str(state.root), 'composition', 'run-graph', 'demo', str(manifest),
            '--inputs', str(inputs), '--max-prompt-bytes', '150000', '--timeout', '20', '--directory', str(destination)]
    assert main([*argv, '--manifest-digest', 'f' * 64]) == 2
    assert not destination.exists() and not call_log.exists()
    capsys.readouterr()
    bound = [*argv, '--manifest-digest', selected['digest']]
    assert main(bound) == (0 if case in ('success', 'lost-outcome') else 1)
    receipt = json.loads(capsys.readouterr().out)
    assert json.loads((destination/'run.json').read_bytes()) == receipt
    assert receipt['manifest_digest'] == selected['digest'] and not receipt['formal_execution_authorized']
    assert workflows.inspect_manifest(destination/'manifest')['digest'] == selected['digest']
    calls = [json.loads(line) for line in call_log.read_text(encoding='utf-8').splitlines()]
    assert calls[0] == supplied and len(set(process_deadlines)) == 1
    if fail_first:
        assert receipt['status'] == 'failed' and 'outputs' not in receipt
        assert len(calls) == 1 and receipt['leaves'][0]['status'] == 'failed'
    elif case == 'result-budget':
        assert len(calls) == 2 and 'outputs' not in receipt
        assert receipt['status'] == 'failed' and 'remaining' in receipt['error']
    else:
        assert len(calls) == 2 and calls[1]['artifacts']['response'] == 'Verified output'
        assert receipt['outputs'] == {'joined': {'root/nested': {'findings': calls[1]},
                                                 'root/followup': {'result': calls[1]}}, 'original': supplied}
    assert [leaf['instance'] for leaf in receipt['leaves']] == (
        ['root/nested/review'] if fail_first else ['root/nested/review', 'root/followup'])
    for leaf in receipt['leaves']:
        observed = agent_runs.inspect_run(state, 'demo', leaf['run_id'])
        assert observed['input']['digest'] == leaf['input_digest']
        assert observed['input']['request']['input_origin'] == 'workflow-port'
    assert main(bound) == 2
    assert len(call_log.read_text(encoding='utf-8').splitlines()) == len(calls)


@pytest.mark.skipif(sys.platform != 'linux', reason='Historical direct-child stamps use Linux procfs')
@pytest.mark.parametrize('case', ['success', 'timeout', 'stop', 'missing-proc', 'unreadable-proc'])
def test_cli_observes_the_original_waited_graph_child(prepared, tmp_path, monkeypatch, capsys, case):
    state, _, _ = prepared()
    workflow = workflows.get(state, 'structure-review', '1.0.0')['definition']
    grant = {'schema_version': 1, 'permissions': workflow['permissions'], 'limits': workflow['limits']}
    manifest = tmp_path / 'manifest'
    frozen = workflows.prepare_manifest(state.root, workflow['id'], workflow['version'], grant, manifest)
    source, inputs, witnesses = tmp_path / 'child.py', tmp_path / 'inputs.json', tmp_path / 'witnesses'
    witnesses.mkdir()
    source.write_text('''import json, os, signal, sqlite3, sys, time
from pathlib import Path

result, witnesses, database = map(Path, sys.argv[1:])
task = json.loads(sys.stdin.read().split('Workflow task port (JSON value):\\n')[-1])
run_id = result.parent.name.removesuffix('.protocol')
with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
    row, = connection.execute('SELECT document FROM agent_runs WHERE id=?', (run_id,)).fetchone()
    run = json.loads(row)
assert run['status'] == 'running' and 'finished' not in run
assert 'process_start_receipt' not in run and 'process_start_sha256' not in run
pid = os.getpid()
fields = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
stamp = {'pid': pid, 'start_ticks': fields[19],
         'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
(witnesses / (run_id + '.json')).write_text(json.dumps(stamp), encoding='utf-8')
if task == 'stop':
    os.kill(os.getppid(), signal.SIGTERM)
if task in ('stop', 'timeout'):
    time.sleep(30)
result.write_text(json.dumps({'summary': task, 'artifacts': {'response': 'reviewed'},
                             'decision': 'approve'}), encoding='utf-8')
''', encoding='utf-8')
    original = agent_backends.CodexBackend.command

    def command(backend, request):
        argv, prompt = original(backend, request)
        result = argv[argv.index('--output-last-message') + 1]
        return [sys.executable, str(source), result, str(witnesses), str(state.root / 'ergora.sqlite3')], prompt

    monkeypatch.setattr(agent_backends.CodexBackend, 'command', command)
    monkeypatch.setattr(agent_backends.CodexBackend, 'check_invocation', lambda self: None)
    if case in ('missing-proc', 'unreadable-proc'):
        def fail_sample(_pid):
            error = FileNotFoundError if case == 'missing-proc' else PermissionError
            raise error('Controlled procfs read failure')
        monkeypatch.setattr(processes, '_process_stamp', fail_sample)

    cli = ['--home', str(state.root), 'composition']

    def run(task):
        directory = tmp_path / task
        inputs.write_text(json.dumps({'task': task}), encoding='utf-8')
        assert main([*cli, 'run-graph', 'demo', str(manifest), '--manifest-digest', frozen['digest'],
                     '--inputs', str(inputs), '--directory', str(directory), '--max-prompt-bytes', '30000',
                     '--timeout', '5' if task == 'timeout' else '20']) == (1 if task in ('timeout', 'stop') else 0)
        receipt = json.loads(capsys.readouterr().out)
        leaf, = receipt['leaves']
        return directory, receipt, leaf

    directory, receipt, leaf = run(case)
    run_id = leaf['run_id']
    other = run('different-input')[2] if case == 'success' else None
    original_records = {item['id']: item for item in agent_runs.runs(state, 'demo')}
    assert set(original_records) == ({run_id, other['run_id']} if other is not None else {run_id})
    witnessed = {path.stem: json.loads(path.read_text()) for path in witnesses.iterdir()}
    assert witnessed.keys() == original_records.keys()
    expected_graph = {'timeout': 'timed_out', 'stop': 'cancelled'}.get(case, 'succeeded')
    assert receipt['status'] == expected_graph
    if case == 'timeout':
        assert leaf['status'] in ('timed_out', 'cancelled')
    else:
        assert leaf['status'] == expected_graph
    process = witnessed[run_id]
    try:
        current = processes.identity(process['pid'])
    except (OSError, ValueError):
        pass
    else:
        assert current != process

    def forbidden(*args, **kwargs):
        pytest.fail('Historical inspection must never dispatch or sample a live PID')

    for operation in ('run', 'identity', '_process_stamp'):
        monkeypatch.setattr(processes, operation, forbidden)

    def read_run():
        assert main([*cli, 'inspect-run', 'demo', run_id]) == 0
        return json.loads(capsys.readouterr().out)

    receipt_bytes = (directory / 'run.json').read_bytes()
    observed = read_run()
    names = ('process_start_receipt', 'process_start_sha256')
    run_record = original_records[run_id]
    omitted = {name: value for name, value in run_record.items() if name not in names}
    assert observed['run'] == omitted
    start = observed['process_start']
    expected_start = {'missing-proc': 'missing', 'unreadable-proc': 'unknown'}.get(case, 'available')
    assert start['state'] == expected_start and start['available'] is (expected_start == 'available')
    if start['available']:
        assert start['kind'] == 'historical-direct-child-start' and start['process'] == process
        bound = original_records[run_id]['process_start_receipt']['binding']
        assert bound == {'run_id': run_id, 'project': 'demo', 'project_revision': receipt['project_revision'],
                         'input_digest': leaf['input_digest'], 'instance': leaf['instance'],
                         'preview_sha256': frozen['manifest']['preview_sha256'],
                         'prompt_sha256': observed['prompt']['sha256']}
        assert start['receipt_sha256'] == original_records[run_id]['process_start_sha256']
    assert observed['input']['digest'] == leaf['input_digest'] and observed['prompt']['input_compared']
    assert observed['result']['available'] == (expected_graph == 'succeeded')
    assert main([*cli, 'inspect-graph', 'demo', str(directory), '--manifest-digest', frozen['digest']]) == 0
    graph = json.loads(capsys.readouterr().out)
    assert graph['agent_attempts'][0]['original_run']['process_start'] == start
    assert graph['process_start'] == graph['stop_and_cleanup'] == 'unknown'
    assert read_run() == observed and (directory / 'run.json').read_bytes() == receipt_bytes
    assert {item['id']: item for item in agent_runs.runs(state, 'demo')} == original_records

    if case == 'success':
        other_record = original_records[other['run_id']]
        partial = {**omitted, names[0]: run_record[names[0]]}
        swapped = {**run_record, **{name: other_record[name] for name in names}}
        invalid = json.loads(json.dumps(run_record))
        invalid[names[0]]['observation']['process']['boot_id'] = '0' * 36
        invalid[names[1]] = native_sources.sha(invalid[names[0]])
        escaped_surrogate = json.loads(json.dumps(run_record))
        escaped_surrogate[names[0]]['observation']['process']['boot_id'] = '\ud800'
        for modified, status in ((omitted, 'not_recorded'), (partial, 'missing'),
                                 (swapped, 'mismatch'), (invalid, 'invalid'), (escaped_surrogate, 'invalid')):
            stored = json.dumps(modified)
            with state.connect() as db:
                db.execute('UPDATE agent_runs SET document=? WHERE id=?', (stored, run_id))
            repeated = read_run()
            assert not repeated['process_start']['available'] and repeated['process_start']['state'] == status
            assert repeated['input']['available'] and repeated['prompt']['available']
            assert repeated['result'] == observed['result']
            assert repeated['run'] == omitted
            with state.connect() as db:
                assert db.execute('SELECT document FROM agent_runs WHERE id=?', (run_id,)).fetchone()[0] == stored
        with state.connect() as db:
            db.execute('UPDATE agent_runs SET document=? WHERE id=?', (json.dumps(run_record), run_id))
        saved_task = state.root / 'runs' / (run_id + '.input') / 'task.txt'
        task_bytes = saved_task.read_bytes()
        saved_task.write_bytes(b'changed task')
        repeated = read_run()
        assert not repeated['input']['available'] and not repeated['process_start']['available']
        assert repeated['process_start']['state'] == repeated['input']['state']
        assert repeated['prompt']['available'] and not repeated['prompt']['input_compared']
        assert repeated['result'] == observed['result']
        saved_task.write_bytes(task_bytes)
        prompt_file = state.root / 'runs' / (run_id + '.protocol') / 'prompt.txt'
        prompt_file.unlink()
        repeated = read_run()
        assert repeated['prompt']['state'] == repeated['process_start']['state'] == 'missing'
        assert repeated['result'] == observed['result']
        assert {path.stem: json.loads(path.read_text()) for path in witnesses.iterdir()} == witnessed


@pytest.fixture
def parallel_graph(prepared, tmp_path, monkeypatch):
    from ergora.agents.graphs import run_graph

    state, _, _ = prepared()
    base = workflows.get(state, 'structure-review', '1.0.0')
    definition = base['definition']
    leaf = definition['nodes'][0]
    source, witnesses = tmp_path/'provider.py', tmp_path/'witnesses'
    witnesses.mkdir()
    source.write_text('''import json, os, sys, time
from itertools import count
from pathlib import Path

result, witnesses = map(Path, sys.argv[1:])
task = json.loads(sys.stdin.read().split('Workflow task port (JSON value):\\n')[-1])
name = task.get('name', 'next')

def stamp(event):
    # The providers claim a shared event order even when their clock ticks are equal.
    for position in count():
        try:
            (witnesses.parent / f'event-{position}').touch(exist_ok=False)
        except FileExistsError:
            continue
        break
    path = witnesses / (name + '.' + event)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps([os.getpid(), position]), encoding='utf-8')
    temporary.replace(path)

stamp('started')
if 'wait_for' in task:
    end = time.monotonic() + 15
    while not (witnesses / task['wait_for']).exists():
        if time.monotonic() >= end:
            sys.exit(8)
        time.sleep(.01)
if task.get('trigger') == 'failure':
    sys.exit(7)
if task.get('trigger') == 'cancelled':
    (witnesses / 'stop').touch()
    time.sleep(15)
result.write_text(json.dumps({'summary': name, 'decision': 'approve',
                              'artifacts': {'response': json.dumps(task)}}), encoding='utf-8')
stamp('finished')
''', encoding='utf-8')
    original = agent_backends.CodexBackend.command

    def command(backend, request):
        argv, prompt = original(backend, request)
        return [sys.executable, str(source), argv[argv.index('--output-last-message') + 1], str(witnesses)], prompt

    monkeypatch.setattr(agent_backends.CodexBackend, 'command', command)
    monkeypatch.setattr(agent_backends.CodexBackend, 'check_invocation', lambda self: None)

    def run(project_cap, root_cap, nested_cap, case='success'):
        nested = {**definition, 'id': 'parallel-nested', 'limits': {**definition['limits'], 'concurrency': nested_cap},
                  'inputs': ['a', 'b'], 'outputs': {name: {'node': name, 'output': 'result'} for name in ('a', 'b')},
                  'nodes': [{**leaf, 'id': name, 'inputs': {'task': {'input': name}}} for name in ('a', 'b')]}
        child = workflows.revise(state, definition['id'], definition['version'], base['digest'], nested, publish=True)
        draft = {**definition, 'id': 'parallel-root', 'limits': {**definition['limits'], 'concurrency': root_cap},
                 'inputs': ['a', 'b', 'slow'], 'outputs': {'joined': {'node': 'join', 'output': 'result'}}, 'nodes': [
                     {'id': 'nested', 'ref': {'kind': 'workflow', 'id': nested['id'], 'version': nested['version'],
                                              'digest': child['digest']}, 'depends_on': [],
                      'inputs': {name: {'input': name} for name in nested['inputs']}},
                     {**leaf, 'id': 'slow', 'inputs': {'task': {'input': 'slow'}}},
                     {**leaf, 'id': 'next', 'depends_on': ['nested'],
                      'inputs': {'task': {'node': 'nested', 'output': 'b'}}},
                     {'id': 'join', 'join': 'all', 'depends_on': ['slow', 'next', 'nested']},
                 ]}
        if case == 'over-budget':
            draft['nodes'][1]['depends_on'] = ['nested']
        workflows.revise(state, definition['id'], definition['version'], base['digest'], draft, publish=True)
        grant = {'schema_version': 1, 'permissions': draft['permissions'],
                 'limits': {**draft['limits'], 'concurrency': project_cap}}
        manifest, directory = tmp_path/'manifest', tmp_path/'run'
        selected = workflows.prepare_manifest(state.root, draft['id'], draft['version'], grant, manifest)
        inputs = {name: {'name': name} for name in ('a', 'b', 'slow')}
        if min(project_cap, root_cap) == 2:
            inputs['slow']['wait_for'] = 'next.finished'
            if nested_cap == 2:
                inputs['a']['wait_for'] = 'b.started'
                inputs['b']['wait_for'] = 'a.started'
            else:
                inputs['a']['wait_for'] = 'slow.started'
        if case == 'timed_out':
            inputs['b']['wait_for'] = 'never.started'
        elif case in ('failure', 'cancelled'):
            inputs['b']['trigger'] = case
        elif case.startswith('reservation-'):
            inputs['a']['wait_for'] = 'release-a'
            if case == 'reservation-failure':
                inputs['a']['trigger'] = 'failure'
        receipt = run_graph(state, 'demo', manifest, selected['digest'], inputs, directory, 50_000,
                            5 if case == 'timed_out' else 20, stop_requested=lambda: (witnesses/'stop').exists())
        assert receipt == json.loads((directory/'run.json').read_bytes())
        assert len({leaf['run_id'] for leaf in receipt['leaves']}) == len(receipt['leaves'])
        return receipt, witnesses, state

    return run


@pytest.mark.parametrize('project_cap,root_cap,nested_cap', [(1, 2, 2), (2, 1, 2), (2, 2, 2), (2, 2, 1)])
def test_standalone_graph_runs_ready_leaves_within_every_scope(parallel_graph, project_cap, root_cap, nested_cap):
    receipt, witnesses, _ = parallel_graph(project_cap, root_cap, nested_cap)
    assert receipt['status'] == 'succeeded'
    assert len(receipt['leaves']) == 4
    joined = receipt['outputs']['joined']
    assert list(joined) == ['root/slow', 'root/next', 'root/nested']
    assert json.loads(joined['root/next']['result']['artifacts']['response']) == joined['root/nested']['b']
    positions = {path.name: json.loads(path.read_bytes())[1] for path in witnesses.iterdir()}
    events = sorted((position, 1 if name.endswith('.started') else -1) for name, position in positions.items())
    assert [position for position, _ in events] == list(range(2 * len(receipt['leaves'])))
    active, peak = 0, 0
    for _, change in events:
        active += change
        peak = max(active, peak)
    assert peak == min(project_cap, root_cap)
    assert positions['next.started'] > max(positions['a.finished'], positions['b.finished'])
    if peak == 2:
        assert positions['slow.started'] < positions['next.started'] < positions['slow.finished']
        nested_overlap = max(positions['a.started'], positions['b.started']) < min(positions['a.finished'], positions['b.finished'])
        assert nested_overlap == (nested_cap == 2)


@pytest.mark.parametrize('case', ['failure', 'cancelled', 'timed_out'])
def test_standalone_graph_stops_dispatch_and_drains_owned_leaves(parallel_graph, monkeypatch, case):
    from ergora.agents.graphs import _GraphRun

    original_save = _GraphRun.save

    def save(graph):
        if any(attempt['status'] == 'failed' for attempt in graph.receipt['leaves']):
            assert graph.should_stop()
        original_save(graph)

    monkeypatch.setattr(_GraphRun, 'save', save)
    receipt, witnesses, state = parallel_graph(2, 2, 1, case)
    assert receipt['status'] == ('failed' if case == 'failure' else case)
    assert 'outputs' not in receipt and not (witnesses/'next.started').exists()
    attempts = {leaf['instance'].rsplit('/', 1)[-1]: leaf for leaf in receipt['leaves']}
    assert attempts.keys() == {'a', 'b', 'slow'}
    for name, attempt in attempts.items():
        pid, _ = json.loads((witnesses/(name + '.started')).read_bytes())
        if os.name == 'posix':
            with pytest.raises(ProcessLookupError):
                os.kill(pid, 0)
        observed = agent_runs.inspect_run(state, 'demo', attempt['run_id'])
        assert observed['run']['id'] == attempt['run_id']
        assert observed['run']['status'] == attempt['status']
        assert observed['input']['digest'] == attempt['input_digest']
        if name == 'a':
            assert attempt['status'] == 'succeeded'
            assert observed['result']['sha256'] == attempt['result_sha256']
        elif case == 'failure':
            assert attempt['status'] == ('failed' if name == 'b' else 'cancelled')
        else:
            assert attempt['status'] in ('cancelled', 'timed_out')


@pytest.mark.parametrize('condition,terminal,error', [
    ('failure', 'failed', 'Workflow leaf root/nested/a reported failed'),
    ('stop', 'cancelled', 'Workflow interrupted'),
    ('budget', 'failed', 'Workflow has no remaining result bytes'),
])
def test_standalone_graph_rechecks_admission_after_saving_an_attempt(
        parallel_graph, tmp_path, monkeypatch, condition, terminal, error):
    from ergora.agents import graphs

    if condition == 'budget':
        task = {'name': 'a', 'wait_for': 'release-a'}
        result = {'summary': 'a', 'decision': 'approve', 'artifacts': {'response': json.dumps(task)}}
        monkeypatch.setattr(graphs, '_RESULT_LIMIT', len(json.dumps(result).encode('utf-8')))
    previous_status = {'failure': 'failed', 'stop': 'cancelled', 'budget': 'succeeded'}[condition]
    witnesses = tmp_path/'witnesses'
    original_save = graphs._GraphRun.save
    reservations = []

    def save(graph):
        leaves = graph.receipt['leaves']
        if len(leaves) == 2 and leaves[-1]['instance'] == 'root/nested/b' and not reservations:
            assert len(json.loads((graph.directory/'run.json').read_bytes())['leaves']) == 1
            reservations.append(leaves[-1].copy())
            if condition == 'stop':
                (witnesses/'stop').touch()
            else:
                (witnesses/'release-a').touch()
                first, = graph.running
                assert first.result(timeout=10)['status'] == previous_status
        original_save(graph)

    monkeypatch.setattr(graphs._GraphRun, 'save', save)
    receipt, witnesses, state = parallel_graph(2, 2, 2, 'reservation-' + condition)
    assert receipt['status'] == terminal and receipt['error'] == error
    first, skipped = receipt['leaves']
    reservation, = reservations
    assert reservation['status'] == 'attempted'
    assert skipped == {**reservation, 'status': 'not_dispatched'}
    assert first['status'] == previous_status
    assert {job['id'] for job in agent_runs.runs(state, 'demo')} == {first['run_id']}
    assert not (witnesses/'b.started').exists()


def test_standalone_graph_charges_parallel_results_to_one_budget(parallel_graph, monkeypatch):
    from ergora.agents import graphs

    monkeypatch.setattr(graphs, '_RESULT_LIMIT', 180)
    receipt, witnesses, state = parallel_graph(2, 2, 2, 'over-budget')
    assert receipt['status'] == 'failed' and 'remaining' in receipt['error']
    assert 'outputs' not in receipt
    assert {path.name for path in witnesses.iterdir()} == {'a.started', 'a.finished', 'b.started', 'b.finished'}
    assert [leaf['instance'] for leaf in receipt['leaves']] == ['root/nested/a', 'root/nested/b']
    original_sizes = []
    for attempt in receipt['leaves']:
        original = agent_runs.inspect_run(state, 'demo', attempt['run_id'])['result']
        assert original['sha256'] == attempt['result_sha256']
        original_sizes.append(original['bytes'])
    assert max(original_sizes) <= 180 < sum(original_sizes)


@pytest.mark.skipif(sys.platform != 'linux', reason='Recoverable standalone graphs require Linux/WSL2')
@pytest.mark.parametrize('case', ['resume', 'lost-outcome', 'unknown', 'expired', 'clock', 'project', 'result-budget',
                                  'route-before', 'route-after', 'route-none'])
def test_standalone_graph_resume_retains_the_original_work(prepared, tmp_path, case):
    import signal
    import time

    state, _, _ = prepared()
    base = workflows.get(state, 'structure-review', '1.0.0')
    definition = base['definition']
    choice = {'route-before': 'dependency', 'route-after': 'structure', 'route-none': 'none'}.get(case)
    if choice is not None:
        draft = _conditional_draft(definition)
    else:
        leaf = {**definition['nodes'][0], 'review_requirement': 'required'}
        draft = {**definition, 'schema_version': 2, 'id': 'resume-review', 'inputs': ['task'],
                 'nodes': [{**leaf, 'id': 'first', 'inputs': {'task': {'input': 'task'}}},
                           {**leaf, 'id': 'second', 'depends_on': ['first'],
                            'inputs': {'task': {'node': 'first', 'output': 'result'}}}],
                 'outputs': {'result': {'node': 'second', 'output': 'result'}}}
    workflows.revise(state, definition['id'], definition['version'], base['digest'], draft, publish=True)
    grant = {'schema_version': 1, 'permissions': draft['permissions'], 'limits': draft['limits']}
    manifest, directory = tmp_path / 'manifest', tmp_path / 'graph'
    selected = workflows.prepare_manifest(state.root, draft['id'], draft['version'], grant, manifest)
    inputs, calls, gate = (tmp_path / name for name in ('inputs.json', 'calls.jsonl', 'interrupted'))
    task = ({'choice': choice} if choice is not None else
            {'request': 'Review the exact source and carry the original result to the next review.'})
    inputs.write_text(json.dumps({'task': task}), encoding='utf-8')
    result_limit = 1200 if case == 'result-budget' else None
    timeout = 7 if case == 'expired' else 45

    # Probe only the selected lifecycle boundary. The CLI, graph owner and Agent
    # process are real. No coordinator hook is installed on the resume command.
    coordinator = r'''
import json
import os
from pathlib import Path
import signal
import sys

from ergora.agents import backends, graphs
from ergora.interfaces.cli import main
from ergora.runtime import budget_clock, processes

case, checkpoint, clock_jump, gate, calls = sys.argv[1:6]
gate = Path(gate)
model = r"""
import json
from pathlib import Path
import sys

target, calls, case = sys.argv[1:]
task = json.loads(sys.stdin.read().split('Workflow task port (JSON value):\n')[-1])
label = 'first' if 'request' in task or 'choice' in task else 'second'
result = {'summary': label, 'decision': 'approve',
          'artifacts': {'response': 'x' * 700 if case == 'result-budget' else 'Review fixture'}}
if 'choice' in task:
    result['artifacts']['route'] = task['choice']
with Path(calls).open('a', encoding='utf-8') as stream:
    stream.write(json.dumps({'task': task, 'result': result}) + '\n')
Path(target).write_text(json.dumps(result), encoding='utf-8')
"""
command = backends.CodexBackend.command
def controlled(backend, request):
    argv, prompt = command(backend, request)
    assert argv[argv.index('--sandbox') + 1] == 'read-only'
    return [sys.executable, '-c', model, argv[argv.index('--output-last-message') + 1], calls, case], prompt

backends.CodexBackend.command = controlled
backends.CodexBackend.check_invocation = lambda self: None
if case == 'result-budget':
    graphs._RESULT_LIMIT = 1200
if clock_jump == 'jump':
    current_clock = budget_clock._clock
    def discontinuity():
        boot, ticks = current_clock()
        return boot, ticks + 120_000_000_000
    budget_clock._clock = discontinuity

def hold(phase):
    ready = gate.with_suffix('.pending')
    witness = {'phase': phase, 'owner': processes.identity(os.getpid())}
    ready.write_text(json.dumps(witness), encoding='utf-8')
    ready.replace(gate)
    signal.pause()
    raise AssertionError('Fixture should terminate its original coordinator')

if checkpoint == 'successor':
    dispatch = graphs._GraphRun.dispatch_leaf
    def before_successor(self, executor, node, task):
        if node['path'] == 'root/second':
            assert self.receipt['leaves'][0]['status'] == 'succeeded'
            hold('successor')
        return dispatch(self, executor, node, task)
    graphs._GraphRun.dispatch_leaf = before_successor
elif checkpoint == 'reserved':
    save = graphs._GraphRun.save
    def retain_prior_progress(self):
        if self.receipt['leaves']:
            previous = (self.directory / 'run.json').read_bytes()
            gate.with_name('stale-run.json').write_bytes(previous)
        return save(self)
    graphs._GraphRun.save = retain_prior_progress
    admit = graphs._GraphRun.check_leaf_admission
    def before_submit(self):
        settled = admit(self)
        if self.receipt['leaves'] and self.receipt['leaves'][0]['status'] == 'attempted':
            hold('reserved')
        return settled
    graphs._GraphRun.check_leaf_admission = before_submit
elif checkpoint == 'lost':
    collect = graphs._GraphRun.collect_finished
    def before_receipt(self):
        if self.running and any(future.done() and future.result()['status'] == 'succeeded'
                                for future in self.running):
            hold('lost')
        return collect(self)
    graphs._GraphRun.collect_finished = before_receipt
elif checkpoint in ('before-choice', 'after-choice'):
    choose = graphs._GraphRun.choose_agent
    def around_choice(self, node, source):
        assert self.receipt['leaves'][0]['status'] == 'succeeded'
        if checkpoint == 'before-choice':
            hold(checkpoint)
        result = choose(self, node, source)
        hold(checkpoint)
        return result
    graphs._GraphRun.choose_agent = around_choice

raise SystemExit(main(sys.argv[6:]))
'''
    env = dict(os.environ, PYTHONPATH=str(IMPORT_ROOT), PYTHONDONTWRITEBYTECODE='1')
    checkpoint = {'unknown': 'reserved', 'lost-outcome': 'lost', 'route-before': 'before-choice',
                  'route-after': 'after-choice', 'route-none': 'after-choice'}.get(case, 'successor')

    def command(operation, *args, hook='none', clock='actual', home=None):
        return [sys.executable, '-P', '-c', coordinator, case, hook, clock, str(gate), str(calls),
                '--home', str(state.root if home is None else home), 'composition', operation, *args]

    common = ['demo', str(directory), '--manifest-digest', selected['digest']]
    original_cli = command('run-graph', 'demo', str(manifest), '--manifest-digest', selected['digest'],
        '--inputs', str(inputs), '--max-prompt-bytes', '50000', '--timeout', str(timeout),
        '--directory', str(directory), '--recoverable', hook=checkpoint)

    def resume(*, clock='actual', home=None):
        return subprocess.run(command('resume-graph', *common, clock=clock, home=home), env=env,
                              capture_output=True, text=True, timeout=15)

    receipt_path, recovery = directory / 'run.json', directory / 'recovery.json'
    original = subprocess.Popen(original_cli, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        cutoff = time.monotonic() + 12
        while not gate.exists() and original.poll() is None and time.monotonic() < cutoff:
            time.sleep(.01)
        if not gate.exists():
            if original.poll() is None:
                original.kill()
            stdout, stderr = original.communicate(timeout=5)
            pytest.fail(f'Coordinator missed its interruption point: {(stdout, stderr)!r}')
        witness = json.loads(gate.read_bytes())
        assert witness == {'phase': checkpoint, 'owner': processes.identity(original.pid)}
        original_receipt, original_budget = receipt_path.read_bytes(), recovery.read_bytes()
        saved = json.loads(original_receipt)
        first, = saved['leaves']
        assert saved['status'] == 'incomplete' and first['instance'] == ('root/analyze' if choice is not None else 'root/first')
        assert not (directory / 'input-2').exists()
        assert first['status'] == ('attempted' if checkpoint in ('reserved', 'lost') else 'succeeded')
        assert len(saved.get('route_decisions', [])) == (1 if checkpoint == 'after-choice' else 0)
        if case == 'unknown':
            assert not calls.exists() and agent_runs.runs(state, 'demo') == []
        else:
            original_run = agent_runs.inspect_run(state, 'demo', first['run_id'])
            assert original_run['run']['status'] == 'succeeded'
            assert original_run['input']['digest'] == first['input_digest']
            assert len(calls.read_text(encoding='utf-8').splitlines()) == 1
        if case == 'resume':
            active = resume()
            assert active.returncode == 2 and 'original graph coordinator is still active' in active.stderr
            assert original.poll() is None and receipt_path.read_bytes() == original_receipt
            assert recovery.read_bytes() == original_budget
            assert not (directory / 'input-2').exists()
            assert len(calls.read_text(encoding='utf-8').splitlines()) == 1
    finally:
        if original.poll() is None:
            original.kill()
        original.communicate(timeout=5)
    assert original.returncode == -signal.SIGKILL

    def unchanged():
        assert receipt_path.read_bytes() == original_receipt
        assert recovery.read_bytes() == original_budget
        assert not (directory / 'input-2').exists()
        assert len(agent_runs.runs(state, 'demo')) == (0 if case == 'unknown' else 1)

    if case == 'resume':
        missing_home, existing_home = (tmp_path / name for name in ('missing-home', 'other-home'))
        existing_home.mkdir()
        marker = existing_home / 'original-marker'
        marker.write_bytes(b'Other State home fixture')
        for home in (missing_home, existing_home):
            refused = resume(home=home)
            assert refused.returncode == 2 and 'State home' in refused.stderr
            unchanged()
        assert not missing_home.exists()
        assert list(existing_home.iterdir()) == [marker] and marker.read_bytes() == b'Other State home fixture'

        # A verified input slot alone must not make an omitted native attempt eligible.
        try:
            receipt_path.write_text(json.dumps({**saved, 'leaves': []}), encoding='utf-8')
            omitted = resume()
            assert omitted.returncode == 2 and 'reservation witnesses differ from graph progress' in omitted.stderr
            assert len(calls.read_text(encoding='utf-8').splitlines()) == 1
        finally:
            receipt_path.write_bytes(original_receipt)
        unchanged()
        result_file = state.root / 'runs' / first['run_id'] / 'result.json'
        original_result = result_file.read_bytes()
        try:
            result_file.write_bytes(original_result + b' ')
            refused = resume()
            assert refused.returncode == 2 and 'matching original Agent input, prompt and result evidence' in refused.stderr
            unchanged()
        finally:
            result_file.write_bytes(original_result)
    elif case == 'route-after':
        # A coherent choice of the other branch still contradicts the original analyzer.
        recorded, = saved['route_decisions']
        different = {**recorded, 'choice': 'dependency', 'selected': 'root/dependency', 'skipped': ['root/structure']}
        altered = json.dumps({**saved, 'route_decisions': [different]}).encode('utf-8')
        try:
            receipt_path.write_bytes(altered)
            refused = resume()
            assert refused.returncode == 2 and 'route decision differs from its original analyzer result' in refused.stderr, refused.stderr
            assert receipt_path.read_bytes() == altered and recovery.read_bytes() == original_budget
            assert len(calls.read_text(encoding='utf-8').splitlines()) == 1
            assert len(agent_runs.runs(state, 'demo')) == 1 and not (directory / 'input-2').exists()
        finally:
            receipt_path.write_bytes(original_receipt)
        unchanged()
    elif case == 'project':
        project = state.project('demo')
        projects.set_correction_suggestions(state, 'demo', False, project['revision'])
    elif case == 'expired':
        deadline_ns = json.loads(original_budget)['deadline_monotonic_ns']
        deadline = deadline_ns / 1_000_000_000
        time.sleep(max(0, deadline - time.monotonic()) + .05)
        inspected = subprocess.run(command('inspect-graph', *common), env=env,
                                   capture_output=True, text=True, timeout=15)
        assert inspected.returncode == 0, inspected.stdout + inspected.stderr
        (tmp_path / 'expired-inspection.json').write_text(inspected.stdout, encoding='utf-8')
        observation = json.loads(inspected.stdout)
        assert observation['graph_receipt']['status'] == 'incomplete'
        assert observation['graph_receipt']['sha256'] == hashlib.sha256(original_receipt).hexdigest()
        assert observation['recovery']['authorization']['state'] == 'corroborated'
        assert observation['recovery']['clock']['state'] == 'expired'
        assert observation['recovery']['clock']['deadline_monotonic_ns'] == deadline_ns
        assert observation['recovery']['fixed_check']['state'] == 'not_applicable'
        observed, = observation['agent_attempts']
        assert observed['run_id'] == first['run_id']
        assert observed['original_run']['result']['sha256'] == first['result_sha256']
        unchanged()

    resumed = resume(clock='jump' if case == 'clock' else 'actual')
    diagnostics = {'unknown': 'Unknown agent run', 'clock': 'clock discontinuity',
                   'project': 'Project revision differs', 'expired': 'original workflow deadline expired'}
    if case in diagnostics:
        assert resumed.returncode == 2 and diagnostics[case] in resumed.stderr, resumed.stderr
        unchanged()
        if case == 'unknown':
            witness = directory / 'reservation-1.json'
            witnessed = witness.read_bytes()
            expected = {'schema_version': 1, 'sequence': 1, 'recovery_sha256': saved['recovery_sha256'],
                        **{key: first[key] for key in ('instance', 'run_id', 'input_digest')}}
            assert json.loads(witnessed) == expected
            original_input = workflows.inspect_input(directory / 'input-1')['digest']
            assert original_input == first['input_digest']
            stale = gate.with_name('stale-run.json').read_bytes()
            assert json.loads(stale) == {**saved, 'leaves': []}
            try:
                receipt_path.write_bytes(stale)
                omitted = resume()
                assert omitted.returncode == 2 and 'reservation witnesses differ from graph progress' in omitted.stderr
                assert receipt_path.read_bytes() == stale and witness.read_bytes() == witnessed
                assert recovery.read_bytes() == original_budget
                assert workflows.inspect_input(directory / 'input-1')['digest'] == original_input
                assert not calls.exists() and agent_runs.runs(state, 'demo') == []
            finally:
                receipt_path.write_bytes(original_receipt)
            unchanged()
        return
    assert resumed.returncode == (1 if case == 'result-budget' else 0), (resumed.stdout, resumed.stderr)
    settled = json.loads(resumed.stdout)
    assert settled == json.loads(receipt_path.read_bytes()) and recovery.read_bytes() == original_budget
    first_result = original_run['result']
    recovered, *new_leaves = settled['leaves']
    assert recovered['instance'] == first['instance'] and recovered['run_id'] == first['run_id']
    assert recovered['input_digest'] == first['input_digest'] and recovered['result_sha256'] == first_result['sha256']
    repeated = agent_runs.inspect_run(state, 'demo', first['run_id'])
    assert repeated['input'] == original_run['input'] and repeated['result'] == first_result
    observed = [json.loads(line) for line in calls.read_text(encoding='utf-8').splitlines()]
    if choice is not None:
        _assert_resumed_route(settled, saved, choice, original_run, repeated, observed, task, new_leaves, state)
        return
    next_leaf, = new_leaves
    assert next_leaf['instance'] == 'root/second' and next_leaf['run_id'] != first['run_id']
    assert [row['task'] for row in observed] == [task, first_result['document']]
    if case == 'result-budget':
        assert settled['status'] == 'failed' and 'remaining' in settled['error'] and 'outputs' not in settled
        next_result = agent_runs.inspect_run(state, 'demo', next_leaf['run_id'])['result']
        sizes = first_result['bytes'], next_result['bytes']
        assert max(sizes) <= result_limit < sum(sizes)
    else:
        assert settled['status'] == 'succeeded' and settled['outputs']['result'] == observed[1]['result']
        assert len(agent_runs.runs(state, 'demo')) == 2
        if case == 'resume':
            finished = receipt_path.read_bytes()
            refused = resume()
            assert refused.returncode == 2 and 'terminal or explicitly stopped graph' in refused.stderr
            assert receipt_path.read_bytes() == finished and recovery.read_bytes() == original_budget
            assert len(calls.read_text(encoding='utf-8').splitlines()) == 2


def _assert_resumed_route(settled, saved, choice, original, repeated, calls, task, new_leaves, state):
    selected = None if choice == 'none' else 'root/' + choice
    eligible = ['root/structure', 'root/dependency']
    first = saved['leaves'][0]
    assert settled['status'] == 'succeeded' and settled['leaves'][0] == first
    assert repeated['run'] == original['run'] and calls[0]['task'] == task
    record, = settled['route_decisions']
    assert record == {'instance': 'root/choose', 'choice': choice, 'eligible': eligible, 'selected': selected,
                      'skipped': [path for path in eligible if path != selected],
                      'source': {key: first[key] for key in ('instance', 'run_id', 'input_digest', 'result_sha256')}}
    if saved.get('route_decisions'):
        assert settled['route_decisions'] == saved['route_decisions']
    followups = {path: {'status': 'skipped'} for path in eligible}
    if selected is None:
        assert len(calls) == 1 and not new_leaves
    else:
        successor, = new_leaves
        assert successor['instance'] == selected and successor['run_id'] != first['run_id']
        assert len(calls) == 2 and calls[1]['task'] == original['result']['document']
        followups[selected] = {'result': calls[1]['result']}
    assert settled['outputs'] == {'selection': {'choice': choice}, 'followups': followups}
    assert {row['id'] for row in agent_runs.runs(state, 'demo')} == {leaf['run_id'] for leaf in settled['leaves']}


@pytest.mark.skipif(not all(hasattr(os, flag) for flag in ('O_NOFOLLOW', 'O_NONBLOCK', 'O_ACCMODE')),
                    reason='POSIX read-only descriptor flags are unavailable')
def test_nondurable_artifact_read_opens_an_ordinary_file_with_guarded_flags(tmp_path, monkeypatch):
    witness = tmp_path / 'recovery.json'
    original = b'{"schema_version": 2}\n'
    witness.write_bytes(original)
    open_descriptor = os.open
    opened = []

    def observe_open(path, flags, *args, **kwargs):
        if Path(path) == witness:
            opened.append(flags)
        return open_descriptor(path, flags, *args, **kwargs)

    def forbidden_sync(*args, **kwargs):
        pytest.fail('Local observation attempted durable confirmation')

    monkeypatch.setattr(os, 'open', observe_open)
    monkeypatch.setattr(os, 'fsync', forbidden_sync)
    assert native_sources.artifact(tmp_path, witness.name, len(original)) == original
    assert len(opened) == 1
    guarded = os.O_NOFOLLOW | os.O_NONBLOCK
    assert opened[0] & guarded == guarded and opened[0] & os.O_ACCMODE == os.O_RDONLY


def test_inspect_graph_joins_original_attempts_after_a_lost_reply(parallel_graph, tmp_path, monkeypatch, capsys):
    receipt, witnesses, state = parallel_graph(2, 2, 1)
    directory = tmp_path / 'run'
    receipt_path = directory / 'run.json'
    raw = receipt_path.read_bytes()
    attempts = receipt['leaves']
    argv = ['--home', str(state.root), 'composition', 'inspect-graph', 'demo', str(directory),
            '--manifest-digest', receipt['manifest_digest']]
    witness_bytes = {path.name: path.read_bytes() for path in witnesses.iterdir()}

    def forbidden(*args, **kwargs):
        pytest.fail('Inspection must not perform an execution or admission operation')

    monkeypatch.setattr(agent_runs, 'run_input', forbidden)
    monkeypatch.setattr(processes, 'run', forbidden)
    monkeypatch.setattr(agent_backends.CodexBackend, 'check_invocation', forbidden)
    assert main([*argv[:-1], 'f' * 64]) == 2
    assert 'selected project or manifest digest' in capsys.readouterr().err
    wrong_project = argv.copy()
    wrong_project[4] = 'other'
    assert main(wrong_project) == 2
    assert 'selected project or manifest digest' in capsys.readouterr().err
    assert main([argv[0], str(tmp_path / 'absent-home'), *argv[2:]]) == 2
    assert not (tmp_path / 'absent-home').exists()
    capsys.readouterr()

    # Observe one exact receipt if the coordinator replaces it between stat and open.
    before_publication = {name: value for name, value in receipt.items() if name != 'outputs'}
    before_publication.update(status='incomplete', leaves=[])
    receipt_path.write_text(json.dumps(before_publication), encoding='utf-8')
    staged_receipt = receipt_path.with_name('staged.json')
    staged_receipt.write_bytes(raw)
    open_owner = os if os.name == 'posix' else Path
    open_path = open_owner.open

    def open_after_publication(path, *args, **kwargs):
        if path == receipt_path and staged_receipt.exists():
            staged_receipt.replace(receipt_path)
        return open_path(path, *args, **kwargs)

    with monkeypatch.context() as replacing:
        replacing.setattr(open_owner, 'open', open_after_publication)
        assert main(argv) == 0
    observed = json.loads(capsys.readouterr().out)
    assert observed['graph_receipt']['sha256'] == hashlib.sha256(raw).hexdigest()
    assert observed['graph_receipt']['status'] == 'succeeded'
    assert observed['graph_receipt']['recorded_output_ports'] == ['joined']
    assert observed['process_start'] == observed['stop_and_cleanup'] == 'unknown'
    assert observed['formal_execution_authorized'] is False
    assert [item['run_id'] for item in observed['agent_attempts']] == [item['run_id'] for item in attempts]
    assert [item['sequence'] for item in observed['agent_attempts']] == [1, 2, 3, 4]
    assert observed['ordering'] == {'nodes': 'frozen_manifest_order',
                                    'agent_attempts': 'graph_receipt_reservation_order',
                                    'verification_reads': 'graph_receipt_read_order',
                                    'route_decisions': 'graph_receipt_decision_order'}
    for attempt, item in zip(attempts, observed['agent_attempts'], strict=True):
        assert item['reserved_input']['state'] == 'available'
        assert item['reserved_input']['digest'] == attempt['input_digest']
        original = item['original_run']
        assert original['state'] == 'available'
        assert original['input']['digest'] == attempt['input_digest']
        assert original['result']['sha256'] == attempt['result_sha256']
        assert original['graph_outcome_agreement'] == 'matching'
        assert original['record_created'] and original['record_finished']
        assert 'document' not in original['result']

    for key, label in (('project_revision', 'Receipt project revision'), ('max_prompt_bytes', 'Receipt input byte limit'),
                       ('timeout', 'Receipt workflow timeout')):
        receipt_path.write_text(json.dumps({**receipt, key: float(receipt[key])}), encoding='utf-8')
        assert main(argv) == 2
        assert label in capsys.readouterr().err
    receipt_path.write_bytes(raw)

    # Retain the original attempt but model a crash before the coordinator saved its outcome.
    receipt['status'] = 'incomplete'
    receipt.pop('outputs')
    attempts[0].pop('result_sha256')
    attempts[0]['status'] = 'attempted'
    receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
    shutil.rmtree(directory / 'input-2')
    files = state.root / 'runs'
    (files / attempts[1]['run_id'] / 'result.json').write_text('{}', encoding='utf-8')
    (files / attempts[2]['run_id'] / 'result.json').unlink()
    with state.connect() as db:
        db.execute('DELETE FROM agent_runs WHERE id=?', (attempts[3]['run_id'],))
    before = [path.read_bytes() for path in (receipt_path, state.root / 'ergora.sqlite3')]

    assert main(argv) == 0
    observed = json.loads(capsys.readouterr().out)
    recovered, changed, missing_result, missing_run = observed['agent_attempts']
    assert observed['graph_receipt']['status'] == 'incomplete'
    assert recovered['status'] == 'attempted'
    assert recovered['original_run']['status'] == 'succeeded'
    assert recovered['original_run']['graph_outcome_agreement'] == 'not_recorded'
    assert changed['reserved_input']['state'] == 'missing'
    assert changed['original_run']['result']['state'] == 'mismatch'
    assert missing_result['original_run']['result']['state'] == 'missing'
    assert missing_run['original_run']['state'] == 'missing'
    assert {path.name: path.read_bytes() for path in witnesses.iterdir()} == witness_bytes
    assert before == [path.read_bytes() for path in (receipt_path, state.root / 'ergora.sqlite3')]

    # A run with a different frozen input identity cannot corroborate the selected leaf.
    first_id = attempts[0]['run_id']
    with state.connect() as db:
        row = json.loads(db.execute('SELECT document FROM agent_runs WHERE id=?', (first_id,)).fetchone()[0])
    request = row['input_request']
    limits = request['grant']['limits']
    changed_grant = {**request['grant'], 'limits': {**limits, 'concurrency': float(limits['concurrency'])}}
    changed_rows = [
        {**row, 'input_digest': 'a' * 64},
        {**row, 'project_revision': float(row['project_revision'])},
        {**row, 'input_request': {**request, 'max_prompt_bytes': float(request['max_prompt_bytes'])}},
        {**row, 'input_request': {**request, 'grant': changed_grant}},
    ]
    for changed_row in changed_rows:
        with state.connect() as db:
            db.execute('UPDATE agent_runs SET document=? WHERE id=?', (json.dumps(changed_row), first_id))
        assert main(argv) == 0
        observed = json.loads(capsys.readouterr().out)
        assert observed['agent_attempts'][0]['original_run']['state'] == 'mismatch'

    # Independently read the original saved input when only its prompt byte-count type has changed.
    altered_request = {**request, 'prompt_bytes': float(request['prompt_bytes'])}
    with state.connect() as db:
        db.execute('UPDATE agent_runs SET document=? WHERE id=?',
                   (json.dumps({**row, 'input_request': altered_request}), first_id))
    assert main(argv) == 0
    observed = json.loads(capsys.readouterr().out)
    original = observed['agent_attempts'][0]['original_run']
    assert original['input']['state'] == 'mismatch'
    assert original['prompt']['state'] == 'invalid'

    (directory / 'manifest' / 'surprise.txt').write_text('unexpected', encoding='utf-8')
    assert main(argv) == 2
    assert 'undeclared files' in capsys.readouterr().err


def test_standalone_graph_rejects_writable_leaf_before_reserving_any_effect(prepared, tmp_path):
    from ergora.agents.graphs import run_graph
    from ergora.development.route_errors import RouteBlocked
    from ergora.interfaces import composition_preview

    state, _, _ = prepared(permission=('write', ['workspace']))
    definition = workflows.get(state, 'structure-review', '1.0.0')['definition']
    grant = {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}
    manifest, destination = tmp_path/'manifest', tmp_path/'graph-run'
    selected = workflows.prepare_manifest(state.root, definition['id'], definition['version'], grant, manifest)
    inspection = composition_preview.preview(state.root, definition['id'], definition['version'], grant,
        {'route': 'standalone-graph', 'project': 'demo', 'inputs': {'task': 'test'}, 'max_prompt_bytes': 50000})
    with pytest.raises(RouteBlocked, match='requires a read-only leaf') as failure:
        run_graph(state, 'demo', manifest, selected['digest'], {'task': 'test'}, destination, 50_000, 20)
    expected = failure.value
    assert inspection['route_admission']['capability'] == {'route': 'standalone-graph', 'status': 'blocked',
                                                           'instance': expected.instance, 'reason': expected.reason}
    assert not destination.exists() and agent_runs.runs(state, 'demo') == []


def test_leaf_route_preview_binds_the_same_prepared_input_and_policy(prepared):
    from ergora.interfaces import composition_preview

    state, _, bundle = prepared()
    original = workflows.inspect_input(bundle, material=True)
    request = original['request']
    details = {'route': 'single-leaf', 'project': 'demo', 'directory': str(bundle), 'input_digest': original['digest']}
    root = request['root']
    report = composition_preview.preview(state.root, root['id'], root['version'], request['grant'], details)
    admission = agent_runs.check_input(state, 'demo', bundle, input_digest=original['digest'])
    assert report['composition'] == original['composition']
    assert report['route_admission']['input_digest'] == admission['input_digest']
    assert report['route_admission']['policy'] == admission['policy']
    assert report['route_admission']['runtime_status'] == 'not_queried'
    different = composition_preview.preview(state.root, root['id'], root['version'], request['grant'],
                                            {**details, 'input_digest': '0' * 64})
    assert different['route_admission']['capability']['status'] == 'blocked'
    assert different['route_admission']['capability']['instance'] == request['instance']
    assert agent_runs.runs(state, 'demo') == []


@pytest.mark.parametrize('failure', ['leaf-prompt-capacity', 'codex-config', 'codex-provider-table'])
def test_graph_preview_and_dispatch_share_known_leaf_blockers(prepared, tmp_path, failure):
    from ergora.agents import graphs
    from ergora.development.route_errors import RouteBlocked
    from ergora.interfaces import composition_preview

    state, _, _ = prepared()
    definition = workflows.get(state, 'structure-review', '1.0.0')['definition']
    grant = {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}
    manifest, destination = tmp_path / 'manifest', tmp_path / 'destination'
    frozen = workflows.prepare_manifest(state.root, definition['id'], definition['version'], grant, manifest)
    limit = 100 if failure == 'leaf-prompt-capacity' else 50000
    config = tmp_path / 'bad.toml' if failure != 'leaf-prompt-capacity' else None
    if config is not None:
        content = 'invalid.toml-config = [' if failure == 'codex-config' else 'model_providers = "invalid"'
        config.write_text(content, encoding='utf-8')
    inputs = {'task': 'check'}
    report = composition_preview.preview(state.root, definition['id'], definition['version'], grant, {
        'route': 'standalone-graph', 'project': 'demo', 'inputs': inputs, 'max_prompt_bytes': limit,
        'manifest': str(manifest), 'manifest_digest': frozen['digest'],
        **({'codex_config': str(config)} if config is not None else {})})['route_admission']
    with pytest.raises(RouteBlocked) as refused:
        graphs.run_graph(state, 'demo', manifest, frozen['digest'], inputs, destination, limit, 20, codex_config=config)
    assert report['capability'] == {'route': 'standalone-graph', 'status': 'blocked', 'instance': 'root/review',
                                    'reason': refused.value.reason}
    reasons = {'leaf-prompt-capacity': 'Complete composition prompt exceeds the input byte limit',
               'codex-config': 'Invalid', 'codex-provider-table': 'Codex inference providers must be TOML tables'}
    reason = reasons[failure]
    assert reason in refused.value.reason
    assert refused.value.instance == 'root/review'
    assert not destination.exists() and agent_runs.runs(state, 'demo') == []


def test_graph_route_preview_and_cli_dispatch_share_the_decoded_tree_bound(prepared, tmp_path, capsys):
    state, _, _ = prepared()
    root = workflows.get(state, 'structure-review', '1.0.0')['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    manifest, destination = tmp_path / 'manifest', tmp_path / 'destination'
    frozen = workflows.prepare_manifest(state.root, root['id'], root['version'], grant, manifest)
    task = 'leaf'
    for _ in range(64):
        task = [task]
    inputs = {'task': task}
    execution = {'route': 'standalone-graph', 'project': 'demo', 'manifest': str(manifest),
                 'manifest_digest': frozen['digest'], 'inputs': inputs, 'max_prompt_bytes': 50000}
    grant_path, execution_path, inputs_path = (tmp_path / name for name in ('grant.json', 'execution.json', 'inputs.json'))
    for path, data in ((grant_path, grant), (execution_path, execution), (inputs_path, inputs)):
        path.write_text(json.dumps(data), encoding='utf-8')
    cli = ['--home', str(state.root), 'composition']
    assert main([*cli, 'preview', root['id'], root['version'], '--grant', str(grant_path),
                 '--admission', str(execution_path)]) == 0
    admission = json.loads(capsys.readouterr().out)['route_admission']
    assert admission['capability']['status'] == 'blocked'
    reason = admission['capability']['reason']
    assert reason == 'Workflow inputs exceeds 64 levels / 100000 values'
    assert main([*cli, 'run-graph', 'demo', str(manifest), '--manifest-digest', frozen['digest'],
                 '--inputs', str(inputs_path), '--directory', str(destination), '--max-prompt-bytes', '50000']) == 2
    assert reason in capsys.readouterr().err
    assert not destination.exists() and agent_runs.runs(state, 'demo') == []


def _conditional_draft(root):
    agent = {**root['nodes'][0], 'review_requirement': 'required'}
    return {**root, 'schema_version': 2, 'id': 'bounded-route', 'outputs': {
        'selection': {'node': 'choose', 'output': 'result'}, 'followups': {'node': 'gather', 'output': 'result'}},
        'nodes': [
            {**agent, 'id': 'analyze'},
            {'id': 'choose', 'operation': 'choose-agent', 'depends_on': ['analyze'],
             'inputs': {'source': {'node': 'analyze', 'output': 'result'}}, 'branches': ['structure', 'dependency']},
            *[{**agent, 'id': name, 'depends_on': ['choose', 'analyze'],
               'inputs': {'task': {'node': 'analyze', 'output': 'result'}}} for name in ('structure', 'dependency')],
            {'id': 'gather', 'join': 'all', 'depends_on': ['dependency', 'structure']},
        ]}


@pytest.fixture
def conditional_definition(prepared, tmp_path):
    state, _, _ = prepared()
    base = workflows.get(state, 'structure-review', '1.0.0')
    draft = _conditional_draft(base['definition'])

    def publish(definition):
        source = tmp_path / 'conditional-definition'
        shutil.copytree(EXAMPLES / 'composition/structure-review', source)
        (source / 'workflow.json').write_text(json.dumps(definition), encoding='utf-8')
        return workflows.import_bundle(state, source)

    return state, base, draft, publish


@pytest.mark.skipif(sys.platform != 'linux', reason='Recoverable standalone graphs require Linux/WSL2')
@pytest.mark.parametrize('case', ['follow-up', 'finish', 'lost-before-publish', 'conflicting-publication',
                                  'lost-decision', 'lost-progress', 'expired', 'stopped', 'none'])
def test_supervised_route_keeps_the_original_graph(conditional_definition, tmp_path, monkeypatch, capsys, case):
    import time

    from ergora.agents import graphs

    state, _, draft, publish = conditional_definition
    publish(draft)
    grant = {'schema_version': 1, 'permissions': draft['permissions'], 'limits': draft['limits']}
    manifest, directory = tmp_path / 'manifest', tmp_path / 'graph'
    selected = workflows.prepare_manifest(state.root, draft['id'], draft['version'], grant, manifest)
    inputs, calls = tmp_path / 'inputs.json', tmp_path / 'calls.jsonl'
    recommendation = 'none' if case == 'none' else 'dependency'
    inputs.write_text(json.dumps({'task': {'recommendation': recommendation}}), encoding='utf-8')
    model = r'''
import json
from pathlib import Path
import sys

output, calls = map(Path, sys.argv[1:])
task = json.loads(sys.stdin.read().rsplit('Workflow task port (JSON value):\n', 1)[1])
artifacts = {'response': 'Original packaging evidence'}
if 'recommendation' in task:
    artifacts['route'] = task['recommendation']
with calls.open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(task) + '\n')
output.write_text(json.dumps({'summary': 'Review', 'decision': 'approve', 'artifacts': artifacts}), encoding='utf-8')
'''
    command = agent_backends.CodexBackend.command

    def controlled(backend, request):
        argv, prompt = command(backend, request)
        return [sys.executable, '-c', model, argv[argv.index('--output-last-message') + 1], str(calls)], prompt

    monkeypatch.setattr(agent_backends.CodexBackend, 'command', controlled)
    monkeypatch.setattr(agent_backends.CodexBackend, 'check_invocation', lambda self: None)
    cli = ['--home', str(state.root), 'composition']
    common = ['demo', str(directory), '--manifest-digest', selected['digest']]

    def invoke(arguments, code=0, diagnostic=None):
        assert main(cli + arguments) == code
        captured = capsys.readouterr()
        if diagnostic is not None:
            assert diagnostic in captured.err
        return json.loads(captured.out) if captured.out else None

    timeout = 7 if case == 'expired' else 45
    launch = ['run-graph', 'demo', str(manifest), '--manifest-digest', selected['digest'], '--inputs', str(inputs),
              '--directory', str(directory), '--max-prompt-bytes', '50000', '--timeout', str(timeout),
              '--pause-before-route', 'root/choose']
    if case == 'follow-up':
        invoke(launch, 2, 'requires an original recoverable graph')
        assert not directory.exists() and not calls.exists()
    paused = invoke(launch + ['--recoverable'])
    analyzer, = paused['leaves']
    assert analyzer['instance'] == 'root/analyze' and analyzer['status'] == 'succeeded'
    assert not (directory / 'input-2').exists()
    assert len(calls.read_text(encoding='utf-8').splitlines()) == 1
    inspect = ['inspect-graph', *common]
    resume = ['resume-graph', *common]
    observed = invoke(inspect)
    checkpoint = observed['recovery']['route_checkpoint']
    if case == 'none':
        assert paused['status'] == 'succeeded' and paused['outputs']['selection'] == {'choice': 'none'}
        assert checkpoint['state'] == 'not_recorded'
        assert observed['route_decisions'][0]['state'] == 'corroborated'
        return
    assert paused['status'] == 'awaiting_route_decision'
    assert observed['route_decisions'] == [] and checkpoint['state'] == 'awaiting'
    assert checkpoint['recommendation']['selected'] == 'root/dependency'
    assert checkpoint['recommendation']['source']['result_sha256'] == analyzer['result_sha256']
    checkpoint_sha = checkpoint['sha256']
    recovery = directory / 'recovery.json'
    decision = directory / 'route-operator-decision.json'
    clock_bytes = recovery.read_bytes()
    original_receipt = (directory / 'run.json').read_bytes()

    def decide(action, digest=checkpoint_sha):
        return [*resume, '--route-checkpoint', digest, '--route-action', action]

    assert invoke(resume) == paused
    assert (directory / 'run.json').read_bytes() == original_receipt
    invoke(decide('follow-up', 'a' * 64), 2, 'Select the exact original route checkpoint')
    assert not decision.exists()
    if case == 'expired':
        time.sleep(max(0, json.loads(clock_bytes)['deadline_monotonic_ns'] / 1_000_000_000 - time.monotonic()) + .05)
        invoke(decide('follow-up'), 2, 'original workflow deadline expired')
        assert invoke(inspect)['recovery']['route_checkpoint']['state'] == 'closed'
    elif case == 'stopped':
        with pytest.raises(KeyboardInterrupt):
            graphs.resume_graph(state.root, 'demo', directory, selected['digest'], route_checkpoint=checkpoint_sha,
                                route_action='follow-up', stop_requested=lambda: True)
        invoke(decide('follow-up'), 2, 'explicitly stopped graph cannot resume')
        assert invoke(inspect)['recovery']['route_checkpoint']['state'] == 'closed'
    if case in ('expired', 'stopped'):
        assert not decision.exists() and not (directory / 'input-2').exists()
        assert recovery.read_bytes() == clock_bytes and (directory / 'run.json').read_bytes() == original_receipt
        assert len(agent_runs.runs(state, 'demo')) == 1
        return

    action = 'finish' if case == 'finish' else 'follow-up'
    if case in ('lost-before-publish', 'conflicting-publication'):
        link = os.link

        def interrupt_publication(source, destination, **options):
            if destination == decision:
                assert not decision.exists()
                staged = json.loads(source.read_bytes())
                assert staged['checkpoint_sha256'] == checkpoint_sha and staged['action'] == action
                if case == 'lost-before-publish':
                    raise OSError('Fixture interrupted the decision before publication')
                decision.write_bytes(b'Existing decision evidence')
            link(source, destination, **options)

        with monkeypatch.context() as patch:
            patch.setattr(os, 'link', interrupt_publication)
            invoke(decide(action), 2, 'before publication' if case == 'lost-before-publish' else 'File exists')
        assert (directory / 'run.json').read_bytes() == original_receipt
        assert recovery.read_bytes() == clock_bytes and not (directory / 'input-2').exists()
        assert len(agent_runs.runs(state, 'demo')) == 1
        if case == 'conflicting-publication':
            assert decision.read_bytes() == b'Existing decision evidence'
            return
        assert not decision.exists()
        assert invoke(inspect)['recovery']['route_checkpoint']['state'] == 'awaiting'
    if case == 'lost-decision':
        publish = graphs._GraphRun.publish_route_decision

        def lose_ack(graph, record):
            publish(graph, record)
            raise OSError('Fixture lost the decision reply after publication')

        with monkeypatch.context() as patch:
            patch.setattr(graphs._GraphRun, 'publish_route_decision', lose_ack)
            invoke(decide(action), 2, 'lost the decision reply')
        assert (directory / 'run.json').read_bytes() == original_receipt
        published = decision.read_bytes()
        decided = invoke(inspect)['recovery']['route_checkpoint']
        assert decided['state'] == 'decided' and decided['decision']['action'] == action
        invoke(decide('finish'), 2, 'already has a different decision')
        assert decision.read_bytes() == published and not (directory / 'input-2').exists()
    if case == 'lost-progress':
        save = graphs._GraphRun.save

        def lose_progress(graph):
            save(graph)
            if graph.receipt['status'] == 'incomplete' and 'route_checkpoint' in graph.receipt:
                raise OSError('Fixture lost the coordinator after saving resume progress')

        with monkeypatch.context() as patch:
            patch.setattr(graphs._GraphRun, 'save', lose_progress)
            invoke(decide(action), 2, 'lost the coordinator')
        published = decision.read_bytes()
        decision.unlink()
        invoke(resume, 2, 'missing the original operator decision')
        assert invoke(inspect)['recovery']['route_checkpoint']['state'] == 'missing'
        assert not (directory / 'input-2').exists()
        decision.write_bytes(published)

    completed = invoke(decide(action))
    assert completed['status'] == 'succeeded'
    assert completed['leaves'][0] == analyzer and recovery.read_bytes() == clock_bytes
    observed = invoke(inspect)
    route, = observed['route_decisions']
    assert route['state'] == 'corroborated'
    assert route['operator_decision_sha256'] == observed['recovery']['route_checkpoint']['decision_sha256']
    assert route['selected'] == ('root/dependency' if action == 'follow-up' else None)
    assert observed['recovery']['route_checkpoint']['recommendation']['selected'] == 'root/dependency'
    published = decision.read_bytes()
    invoke(decide(action), 2, 'terminal or explicitly stopped graph cannot resume')
    assert decision.read_bytes() == published
    assert len(calls.read_text(encoding='utf-8').splitlines()) == (2 if action == 'follow-up' else 1)
    assert len(agent_runs.runs(state, 'demo')) == (2 if action == 'follow-up' else 1)


@pytest.mark.parametrize('case', ['structure', 'dependency', 'none', 'missing', 'unknown', 'changed-result', 'stopped'])
def test_standalone_graph_routes_only_the_typed_choice(conditional_definition, tmp_path, monkeypatch, capsys, case):
    from ergora.agents import graphs
    from ergora.development import application
    from ergora.development.route_errors import RouteBlocked

    state, base, draft, publish = conditional_definition
    imported = publish(draft)
    prefix = 'root'
    if case == 'dependency':
        root = base['definition']
        wrapper = {**root, 'id': 'outer-route', 'outputs': {
            name: {'node': 'nested', 'output': name} for name in draft['outputs']}, 'nodes': [
                {'id': 'nested', 'ref': {'kind': 'workflow', 'id': draft['id'], 'version': draft['version'],
                                         'digest': imported['digest']}, 'depends_on': [],
                 'inputs': {'task': {'input': 'task'}}},
            ]}
        workflows.revise(state, root['id'], root['version'], base['digest'], wrapper, publish=True)
        draft, prefix = wrapper, 'root/nested'

    grant = {'schema_version': 1, 'permissions': draft['permissions'], 'limits': draft['limits']}
    manifest, directory = tmp_path/'manifest', tmp_path/'graph-run'
    pinned = workflows.prepare_manifest(state.root, draft['id'], draft['version'], grant, manifest)
    compiled = workflows.inspect_manifest(manifest, material=True)['composition']
    nodes = {node['path']: node for node in compiled['instances']}
    analyzer, selector = f'{prefix}/analyze', f'{prefix}/choose'
    eligible = [f'{prefix}/structure', f'{prefix}/dependency']
    assert nodes[analyzer]['route_choices'] == ['structure', 'dependency', 'none']
    assert nodes[selector]['branches'] == eligible
    with pytest.raises(RouteBlocked, match='Conditional Agent selection requires standalone graph execution') as error:
        application._composition_selection(compiled, {}, {})
    assert error.value.instance == selector

    script, calls = tmp_path/'provider.py', tmp_path/'calls.jsonl'
    script.write_text('''import json, sys
from pathlib import Path
result, calls = map(Path, sys.argv[1:3])
task = json.loads(sys.stdin.read().rsplit('Workflow task port (JSON value):\\n', 1)[1])
analyzer = sys.argv[3] == 'analyzer'
with calls.open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(task) + '\\n')
output = {'summary': 'Review', 'decision': 'approve', 'artifacts': {'response': 'Free-form: choose dependency.'}}
if analyzer and task['choice'] is not None:
    output['artifacts']['route'] = task['choice']
result.write_text(json.dumps(output), encoding='utf-8')
''', encoding='utf-8')
    original = agent_backends.CodexBackend.command
    schemas = []

    def command(backend, request):
        argv, prompt = original(backend, request)
        artifacts = request.schema['properties']['artifacts']
        schemas.append(artifacts)
        analyzing = 'route' in artifacts['required']
        if not analyzing:
            decisions = json.loads((directory/'run.json').read_bytes())['route_decisions']
            decision, = decisions
            assert decision['instance'] == selector and decision['selected'] == f'{prefix}/{case}'
        return [sys.executable, str(script), argv[argv.index('--output-last-message') + 1], str(calls),
                'analyzer' if analyzing else 'follow-up'], prompt

    monkeypatch.setattr(agent_backends.CodexBackend, 'command', command)
    monkeypatch.setattr(agent_backends.CodexBackend, 'check_invocation', lambda self: None)
    if case == 'changed-result':
        original_run = agent_runs.run_input

        def swap_result(*args, **kwargs):
            job = original_run(*args, **kwargs)
            if 'result_schema' in kwargs:
                path = Path(job['result'])
                changed = json.loads(path.read_bytes())
                changed['artifacts']['route'] = 'dependency'
                path.write_text(json.dumps(changed), encoding='utf-8')
            return job

        monkeypatch.setattr(agent_runs, 'run_input', swap_result)

    choice = {'missing': None, 'unknown': 'undeclared', 'changed-result': 'structure', 'stopped': 'structure'}.get(case, case)
    inputs = {'task': {'choice': choice}}
    failure = case in ('missing', 'unknown', 'changed-result')
    if case == 'stopped':
        original_save = graphs._GraphRun.save
        stopped = []

        def stop_after_decision(graph):
            original_save(graph)
            if graph.receipt.get('route_decisions'):
                stopped.append(True)

        monkeypatch.setattr(graphs._GraphRun, 'save', stop_after_decision)
        receipt = graphs.run_graph(state, 'demo', manifest, pinned['digest'], inputs, directory, 50_000, 20,
                                   stop_requested=lambda: bool(stopped))
    else:
        supplied = tmp_path/'inputs.json'
        supplied.write_text(json.dumps(inputs), encoding='utf-8')
        assert main(['--home', str(state.root), 'composition', 'run-graph', 'demo', str(manifest),
                     '--manifest-digest', pinned['digest'], '--inputs', str(supplied), '--directory', str(directory),
                     '--max-prompt-bytes', '50000', '--timeout', '20']) == (1 if failure else 0)
        receipt = json.loads(capsys.readouterr().out)

    assert receipt == json.loads((directory/'run.json').read_bytes())
    assert receipt['manifest_digest'] == pinned['digest']
    assert schemas[0]['required'] == ['response', 'route']
    assert schemas[0]['properties']['route'] == {'type': 'string', 'enum': ['structure', 'dependency', 'none']}
    executed = [json.loads(line) for line in calls.read_text(encoding='utf-8').splitlines()]
    assert executed[0] == inputs['task']
    before, *followups = receipt['leaves']
    assert before['instance'] == analyzer
    original = agent_runs.inspect_run(state, 'demo', before['run_id'])
    assert original['input']['digest'] == before['input_digest']
    assert {job['id'] for job in agent_runs.runs(state, 'demo')} == {leaf['run_id'] for leaf in receipt['leaves']}
    observe_argv = ['--home', str(state.root), 'composition', 'inspect-graph', 'demo', str(directory),
                    '--manifest-digest', pinned['digest']]
    call_bytes = calls.read_bytes()

    def observe():
        assert main(observe_argv) == 0
        assert calls.read_bytes() == call_bytes
        return json.loads(capsys.readouterr().out)

    observation = observe()
    node_records = {node['instance']: node['graph_record'] for node in observation['nodes']}
    if failure:
        assert receipt['status'] == 'failed' and 'route_decisions' not in receipt and 'outputs' not in receipt
        assert not followups and len(executed) == 1
        assert observation['route_decisions'] == [] and node_records[selector] == 'not_recorded'
        assert not original['result']['available']
        if case == 'changed-result':
            assert 'SHA256' in original['result']['error']
        else:
            assert 'Invalid structured agent result' in original['run']['error']
        return

    selected = None if choice == 'none' else f'{prefix}/{choice}'
    decision, = receipt['route_decisions']
    assert decision == {'instance': selector, 'choice': choice, 'eligible': eligible, 'selected': selected,
                        'skipped': [path for path in eligible if path != selected],
                        'source': {'instance': analyzer, 'run_id': before['run_id'], 'input_digest': before['input_digest'],
                                   'result_sha256': original['result']['sha256']}}
    assert observation['route_decisions'] == [
        {**decision, 'sequence': 1, 'source_instance': analyzer, 'state': 'corroborated'}]
    assert node_records[selector] == 'recorded'
    assert all(node_records[path] == 'not_recorded' for path in decision['skipped'])
    if case == 'structure':
        receipt_path = directory / 'run.json'
        saved = receipt_path.read_bytes()
        decision.update(choice='unverified-content', selected='unverified-target')
        receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
        changed, = observe()['route_decisions']
        assert changed['state'] == 'mismatch' and changed['proof'] == 'route_decision'
        assert not {'choice', 'selected', 'skipped'}.intersection(changed)
        receipt_path.write_bytes(saved)
        decision.update(choice=choice, selected=selected)
        result_path = Path(original['run']['result'])
        original_bytes = result_path.read_bytes()
        result_path.write_text('{}', encoding='utf-8')
        changed, = observe()['route_decisions']
        assert changed['state'] == 'mismatch' and changed['proof'] == 'result'
        assert not {'choice', 'selected', 'skipped'}.intersection(changed)
        result_path.unlink()
        missing, = observe()['route_decisions']
        assert missing['state'] == 'missing' and missing['proof'] == 'result'
        result_path.write_bytes(original_bytes)
    if case == 'stopped':
        assert receipt['status'] == 'cancelled' and not followups and len(executed) == 1 and 'outputs' not in receipt
        assert node_records[selected] == 'not_recorded'
        return
    assert receipt['status'] == 'succeeded' and receipt['outputs']['selection'] == {'choice': choice}
    joined = receipt['outputs']['followups']
    assert list(joined) == eligible[::-1]
    assert all(joined[branch] == {'status': 'skipped'} for branch in decision['skipped'])
    if selected is None:
        assert not followups and len(executed) == 1
    else:
        branch, = followups
        assert branch['instance'] == selected and schemas[1]['required'] == ['response']
        observed = agent_runs.inspect_run(state, 'demo', branch['run_id'])
        assert executed[1:] == [original['result']['document']]
        assert joined[selected] == {'result': observed['result']['document']}


@pytest.mark.parametrize('case,diagnostic', [
    ('reserved', 'Workflow definition at /nodes/1'), ('too-many', 'Workflow definition at /nodes/1'),
    ('duplicate', 'Workflow definition at /nodes/1'), ('root-source', 'sole sibling Agent dependency'),
    ('unknown-source', 'Unknown Workflow dependency at choose'),
    ('missing-branch', 'sibling Agent depending directly'), ('indirect-branch', 'sibling Agent depending directly'),
    ('two-owners', 'only one route selector'), ('two-selectors', 'only one route selector'),
    ('ordinary-dependent', 'Conditional Agent dependencies require an all-join'),
    ('output-binding', 'Conditional Agent outputs require an all-join'),
    ('conditional-analyzer', 'Conditional Agent dependencies require an all-join'),
])
def test_choose_agent_rejects_invalid_conditional_graphs(conditional_definition, case, diagnostic):
    state, _, draft, publish = conditional_definition
    analyzer, selector, structure, dependency, join = draft['nodes']
    if case == 'reserved':
        selector['branches'] = ['none']
    elif case == 'too-many':
        selector['branches'] = [f'branch-{index}' for index in range(9)]
    elif case == 'duplicate':
        selector['branches'] = ['structure', 'structure']
    elif case == 'root-source':
        selector['inputs'] = {'source': {'input': 'task'}}
    elif case == 'unknown-source':
        selector['depends_on'] = ['foreign-source']
        selector['inputs'] = {'source': {'node': 'foreign-source', 'output': 'result'}}
    elif case == 'missing-branch':
        selector['branches'] = ['foreign-branch']
    elif case == 'indirect-branch':
        structure['depends_on'] = ['analyze']
    elif case == 'two-owners':
        draft['nodes'] += [
            {**analyzer, 'id': 'other-analyzer'},
            {**selector, 'id': 'other-choose', 'depends_on': ['other-analyzer'], 'branches': ['structure'],
             'inputs': {'source': {'node': 'other-analyzer', 'output': 'result'}}},
        ]
        structure['depends_on'].append('other-choose')
    elif case == 'two-selectors':
        draft['nodes'].append({**selector, 'id': 'other-choose', 'branches': ['dependency']})
        dependency['depends_on'].append('other-choose')
    elif case == 'ordinary-dependent':
        draft['nodes'].append({**analyzer, 'id': 'ordinary', 'depends_on': ['structure'],
                               'inputs': {'task': {'node': 'structure', 'output': 'result'}}})
    elif case == 'output-binding':
        draft['outputs']['conditional'] = {'node': 'structure', 'output': 'result'}
    else:
        draft['nodes'] += [{**analyzer, 'id': 'other-branch', 'depends_on': ['other-choose']},
                           {**selector, 'id': 'other-choose', 'depends_on': ['structure'], 'branches': ['other-branch'],
                            'inputs': {'source': {'node': 'structure', 'output': 'result'}}}]
        join['depends_on'].append('other-branch')
    with pytest.raises(ValueError, match=diagnostic):
        publish(draft)
    assert agent_runs.runs(state, 'demo') == []


@pytest.mark.parametrize('case', ['validated', 'invalid-evidence', 'cancelled', 'invalid-source', 'agent-source'])
def test_workflow_verification_read_binds_an_operator_source_before_analysis(prepared, tmp_path, monkeypatch, capsys, case):
    from ergora.development import application
    from ergora.development.route_errors import RouteBlocked

    state, _, _ = prepared()
    base = workflows.get(state, 'structure-review', '1.0.0')
    definition = base['definition']
    verify = {**definition, 'schema_version': 2, 'id': 'verify-original', 'inputs': ['source'],
              'outputs': {'evidence': {'node': 'verify', 'output': 'result'}}, 'nodes': [
                  {'id': 'verify', 'operation': 'verify-evidence', 'depends_on': [],
                   'inputs': {'source': {'input': 'source'}}}]}
    child = workflows.revise(state, definition['id'], definition['version'], base['digest'], verify, publish=True)
    analyze = definition['nodes'][0]
    nested = {'id': 'nested', 'ref': {'kind': 'workflow', 'id': verify['id'], 'version': verify['version'],
                                     'digest': child['digest']}, 'depends_on': [],
              'inputs': {'source': {'input': 'locator'}}}
    draft = {**definition, 'id': 'verified-analysis', 'inputs': ['locator'],
             'outputs': {'analysis': {'node': 'review', 'output': 'result'}}, 'nodes': [nested, {
                 **analyze, 'depends_on': ['nested'], 'inputs': {'task': {'node': 'nested', 'output': 'evidence'}}}]}
    if case == 'agent-source':
        nested.update(depends_on=['find'], inputs={'source': {'node': 'find', 'output': 'result'}})
        draft['nodes'].append({**analyze, 'id': 'find', 'inputs': {'task': {'input': 'locator'}}})
    workflows.revise(state, definition['id'], definition['version'], base['digest'], draft, publish=True)
    grant = {'schema_version': 1, 'permissions': draft['permissions'], 'limits': draft['limits']}
    manifest = tmp_path / 'evidence-manifest'
    selected = workflows.prepare_manifest(state.root, draft['id'], draft['version'], grant, manifest)
    graph = workflows.inspect_manifest(manifest, material=True)['composition']
    operation = next(item for item in graph['instances'] if item['path'] == 'root/nested/verify')
    assert operation['kind'] == 'verify-evidence'
    with pytest.raises(RouteBlocked, match='standalone graph execution') as error:
        application._composition_selection(graph, {}, {})
    assert error.value.instance == 'root/nested/verify'

    source = {'task_id': 'demo-task', 'run_id': '00000000-0000-4000-8000-000000000001',
              'event_id': 12, 'candidate_sha': 'a' * 40, 'receipt_sha256': 'b' * 64}
    if case == 'invalid-source':
        source.pop('candidate_sha')
    project_revision = state.project('demo')['revision']
    evidence = {**source, 'project': 'demo', 'project_revision': project_revision,
                'check_results_sha256': 'c' * 64, 'fixed_check_ids': ['config-check'], 'status': 'validated'}
    reads, deadlines = [], []

    def read(observed_state, project_id, observed, *, expected_revision, deadline, stop_requested):
        assert observed_state.root == state.root and project_id == 'demo' and expected_revision == project_revision
        assert observed == source and not stop_requested()
        reads.append(observed)
        deadlines.append(deadline)
        if case == 'invalid-evidence':
            raise ValueError('Original verify receipt differs')
        if case == 'cancelled':
            raise KeyboardInterrupt
        return evidence

    monkeypatch.setattr(application, 'read_candidate_verification', read)
    script, received = tmp_path / 'analysis.py', tmp_path / 'received.json'
    script.write_text('''import json, sys
from pathlib import Path
evidence = json.loads(sys.stdin.read().split('Workflow task port (JSON value):\\n')[-1])
Path(sys.argv[2]).write_text(json.dumps(evidence), encoding='utf-8')
Path(sys.argv[1]).write_text(json.dumps({'summary':'Review', 'artifacts':{'response':'Ready'},
                                       'decision':'approve'}), encoding='utf-8')
''', encoding='utf-8')
    original = agent_backends.CodexBackend.command

    def command(backend, request):
        argv, prompt = original(backend, request)
        return [sys.executable, str(script), argv[argv.index('--output-last-message') + 1], str(received)], prompt

    monkeypatch.setattr(agent_backends.CodexBackend, 'command', command)
    monkeypatch.setattr(agent_backends.CodexBackend, 'check_invocation', lambda self: None)
    native = processes.run

    def observe(*args, **kwargs):
        deadlines.append(kwargs['deadline'])
        return native(*args, **kwargs)

    monkeypatch.setattr(processes, 'run', observe)
    supplied, directory = tmp_path / 'evidence-input.json', tmp_path / 'evidence-run'
    supplied.write_text(json.dumps({'locator': source}), encoding='utf-8')
    status = main(['--home', str(state.root), 'composition', 'run-graph', 'demo', str(manifest),
                   '--manifest-digest', selected['digest'], '--inputs', str(supplied), '--directory', str(directory),
                   '--max-prompt-bytes', '30000'])
    captured = capsys.readouterr()
    if case in ('agent-source', 'invalid-source'):
        assert status == 2 and not directory.exists() and not reads and not received.exists()
        if case == 'agent-source':
            assert 'must come from a workflow root input' in captured.err
            assert 'root/nested/verify' in captured.err
        return
    receipt = json.loads(captured.out)
    assert receipt == json.loads((directory / 'run.json').read_bytes())
    assert reads == [source] and receipt['formal_execution_authorized'] is False
    record, = receipt['verification_reads']
    assert record['instance'] == 'root/nested/verify' and record['source'] == source
    if case == 'validated':
        assert status == 0 and record['evidence'] == evidence
        assert json.loads(received.read_bytes()) == evidence
        assert len(deadlines) == 2 and deadlines[0] == deadlines[1]
    else:
        assert status == 1 and not received.exists() and receipt['leaves'] == []
        assert record['status'] == receipt['status'] == ('cancelled' if case == 'cancelled' else 'failed')
    # Reconstruct the graph-recorded verification reference without opening its original native reader.
    observation_argv = ['--home', str(state.root), 'composition', 'inspect-graph', 'demo', str(directory),
                        '--manifest-digest', selected['digest']]
    assert main(observation_argv) == 0
    observation = json.loads(capsys.readouterr().out)
    verification, = observation['verification_reads']
    assert verification['locator'] == source
    assert verification['status'] == record['status']
    assert verification['original_receipt'] == {'state': 'not_queried'}
    assert verification['recorded_evidence']['state'] == ('recorded' if case == 'validated' else 'not_recorded')
    nodes = {node['instance']: node['graph_record'] for node in observation['nodes']}
    assert nodes['root/review'] == ('recorded' if case == 'validated' else 'not_recorded')
    if case == 'validated':
        for field, value in (('receipt_sha256', 'd' * 64), ('event_id', float(source['event_id']))):
            original_value = record['evidence'][field]
            record['evidence'][field] = value
            (directory / 'run.json').write_text(json.dumps(receipt), encoding='utf-8')
            assert main(observation_argv) == 0
            observation = json.loads(capsys.readouterr().out)
            assert observation['verification_reads'][0]['recorded_evidence']['state'] == 'mismatch'
            record['evidence'][field] = original_value

        record['source']['event_id'] = float(source['event_id'])
        (directory / 'run.json').write_text(json.dumps(receipt), encoding='utf-8')
        assert main(observation_argv) == 0
        observation = json.loads(capsys.readouterr().out)
        assert observation['verification_reads'][0]['locator_state'] == 'mismatch'
        assert 'locator' not in observation['verification_reads'][0]
    assert reads == [source]


@pytest.mark.skipif(sys.platform != 'linux', reason='Candidate verification uses registered native Linux readers')
@pytest.mark.parametrize('end', ['complete', 'stop', 'deadline'])
def test_pending_verification_allows_a_disjoint_branch_and_keeps_its_original_reader(prepared, tmp_path, monkeypatch, end):
    from ergora.agents import graphs
    from ergora.development import application

    state, _, _ = prepared()
    base = workflows.get(state, 'structure-review', '1.0.0')
    definition = base['definition']
    review = {**definition['nodes'][0], 'review_requirement': 'required'}
    draft = {**definition, 'id': 'overlapping-verification', 'schema_version': 2, 'inputs': ['locator', 'task'],
             'outputs': {'analysis': {'node': 'review', 'output': 'result'}}, 'nodes': [
                 {'id': 'evidence', 'operation': 'verify-evidence', 'depends_on': [],
                  'inputs': {'source': {'input': 'locator'}}},
                 {**review, 'id': 'independent'},
                 {**review, 'depends_on': ['evidence'], 'inputs': {'task': {'node': 'evidence', 'output': 'result'}}}]}
    workflows.revise(state, definition['id'], definition['version'], base['digest'], draft, publish=True)
    grant = {'schema_version': 1, 'permissions': draft['permissions'], 'limits': {**draft['limits'], 'concurrency': 1}}
    manifest = tmp_path / 'manifest'
    selected = workflows.prepare_manifest(state.root, draft['id'], draft['version'], grant, manifest)
    source = {'task_id': 'demo-task', 'run_id': '00000000-0000-4000-8000-000000000001',
              'event_id': 12, 'candidate_sha': 'a' * 40, 'receipt_sha256': 'b' * 64}
    project = state.project('demo')
    evidence = {**source, 'project': 'demo', 'project_revision': project['revision'],
                'check_results_sha256': 'c' * 64, 'fixed_check_ids': ['config-check'], 'status': 'validated'}

    installation = tmp_path / 'installation'
    interpreter = installation / '.venv/bin/python'
    interpreter.parent.mkdir(parents=True)
    interpreter.symlink_to(sys.executable)
    monkeypatch.setattr(application, '_project', lambda state, project_id: {**state.project(project_id),
        'registration': {'definition': {'execution': {'installation': str(installation),
            'config_directory': str(tmp_path), 'state_directory': str(tmp_path)}}}})

    reader_pid, independent, dependent = (tmp_path / name for name in ('reader.pid', 'independent', 'dependent'))
    reader = '''import json, os, sys, time
from pathlib import Path
pid, independent, end, evidence = sys.argv[1:]
request = json.load(sys.stdin)
assert request['source'] == {key: json.loads(evidence)[key] for key in request['source']}
assert request['operation'] == 'read-candidate-verification'
Path(pid).write_text(str(os.getpid()))
while end != 'complete' or not Path(independent).exists():
    time.sleep(.02)
print(evidence)
'''
    analysis = '''import json, os, sys, time
from pathlib import Path
pid, independent, dependent, output = map(Path, sys.argv[1:])
task = json.loads(sys.stdin.read().split('Workflow task port (JSON value):\\n')[-1])
if task == 'independent work':
    while not pid.exists() or not pid.read_text():
        time.sleep(.02)
    os.kill(int(pid.read_text()), 0)
    independent.touch()
else:
    dependent.write_text(json.dumps(task))
output.write_text(json.dumps({'summary': 'Review', 'artifacts': {'response': 'Ready'}, 'decision': 'approve'}))
'''
    deadlines, reads = {}, []
    original_run = processes.run

    def run(argv, *args, **kwargs):
        if argv[-1] == 'from ergora.development.runtime.evidence import main;main()':
            reads.append(kwargs['deadline'])
            argv = [sys.executable, '-c', reader, str(reader_pid), str(independent), end, json.dumps(evidence)]
        else:
            deadlines.setdefault('analysis', kwargs['deadline'])
        return original_run(argv, *args, **kwargs)

    monkeypatch.setattr(processes, 'run', run)
    original_command = agent_backends.CodexBackend.command

    def command(backend, request):
        argv, prompt = original_command(backend, request)
        output = argv[argv.index('--output-last-message') + 1]
        return [sys.executable, '-c', analysis, str(reader_pid), str(independent), str(dependent), output], prompt

    monkeypatch.setattr(agent_backends.CodexBackend, 'command', command)
    monkeypatch.setattr(agent_backends.CodexBackend, 'check_invocation', lambda self: None)
    directory = tmp_path / 'run'
    receipt = graphs.run_graph(state, 'demo', manifest, selected['digest'], {'locator': source, 'task': 'independent work'},
        directory, 30_000, 5, stop_requested=lambda: end == 'stop' and independent.exists())

    assert independent.exists(), 'A ready disjoint Agent must start while the original evidence reader is pending'
    assert not Path('/proc', reader_pid.read_text()).exists(), 'The original reader must be reaped before returning'
    record, = receipt['verification_reads']
    assert record['source'] == source and record['instance'] == 'root/evidence'
    assert receipt == json.loads((directory / 'run.json').read_bytes())
    if end == 'complete':
        assert receipt['status'] == 'succeeded'
        assert record['status'] == 'validated' and record['evidence'] == evidence
        assert json.loads(dependent.read_bytes()) == evidence
        assert [leaf['instance'] for leaf in receipt['leaves']] == ['root/independent', 'root/review']
    else:
        status = 'cancelled' if end == 'stop' else 'timed_out'
        assert receipt['status'] == record['status'] == status
        assert [leaf['instance'] for leaf in receipt['leaves']] == ['root/independent']
        assert not dependent.exists() and 'outputs' not in receipt
    observation = graphs.inspect_graph(state, 'demo', directory, selected['digest'])
    observed, = observation['verification_reads']
    assert observed['locator'] == source and observed['status'] == record['status']
    assert observed['original_receipt'] == {'state': 'not_queried'}
    assert reads == [deadlines['analysis']]


def test_standalone_graph_rechecks_selected_manifest_at_each_leaf(prepared, tmp_path, monkeypatch):
    from ergora.agents.graphs import run_graph

    state, _, _ = prepared()
    original = workflows.get(state, 'structure-review', '1.0.0')
    root = original['definition']
    grant = {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}
    manifest, alternate, destination = (tmp_path/name for name in ('manifest', 'alternate', 'graph-run'))
    selected = workflows.prepare_manifest(state.root, root['id'], root['version'], grant, manifest)
    workflows.revise(state, root['id'], root['version'], original['digest'], {**root, 'id': 'different-graph'}, publish=True)
    workflows.prepare_manifest(state.root, 'different-graph', root['version'], grant, alternate)
    original_prepare = workflows.prepare_input_from_manifest

    def replaced(source, *args, **kwargs):
        shutil.rmtree(source)
        shutil.copytree(alternate, source)
        return original_prepare(source, *args, **kwargs)

    monkeypatch.setattr(workflows, 'prepare_input_from_manifest', replaced)
    receipt = run_graph(state, 'demo', manifest, selected['digest'], {'task': 'test'}, destination, 50_000, 20)
    assert receipt['status'] == 'failed' and 'explicitly selected digest' in receipt['error']
    assert receipt['leaves'] == agent_runs.runs(state, 'demo') == []


@pytest.fixture
def cycle_analysis_case(prepared, tmp_path, monkeypatch):
    if sys.platform != 'linux':
        pytest.skip('Original cycle analysis requires Linux/WSL2 budget clocks, durable records and process identity')
    from ergora.runtime import budget_clock
    import ergora.training.cycles as training_cycles
    state, _, original = prepared(binding={'tool': 'codex', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'max'})
    source = tmp_path / 'analysis-input'
    packet = {'schema_version': 1, 'kind': 'training-round-analysis-packet', 'gaps': [], 'profile': 'controlled packet'}
    raw = json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    request = workflows.inspect_input(original)['request']
    workflows.prepare_input(state.root, 'structure-review', '1.0.0', 'root/review', request['grant'], raw, source, 30000)
    saved = workflows.inspect_input(source, material=True)
    leaf = next(item for item in saved['composition']['instances'] if item['path'] == saved['request']['instance'])
    slot = {'authorization_sha256': 'a' * 64, 'ordinal': 0, 'phase': 'screen',
            'packet_sha256': hashlib.sha256(raw).hexdigest(), 'definition_digest': leaf['ref']['digest'],
            'binding': leaf['backend_request']}
    slot_raw = json.dumps(slot, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    native_state = tmp_path / 'native-state'
    (native_state / 'ergora/training-submissions').mkdir(parents=True)
    boot, ticks = budget_clock._clock()
    preparation = {'schema_version': 1, 'kind': 'training-cycle-analysis-preparation',
                   'authorization_sha256': slot['authorization_sha256'], 'ordinal': slot['ordinal'], 'phase': slot['phase'],
                   'operation_id': 'e' * 32, 'boot_id': boot, 'started_ns': ticks}
    prep_path = tmp_path / 'preparation.json'
    prep_raw = json.dumps(preparation, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    prep_path.write_bytes(prep_raw)
    authority = {'schema_version': 1, 'kind': 'training-cycle-analysis-authority',
        'operation': {'identity': {'operation_id': 'e' * 32},
                      'bootstrap': {'boot_id': boot, 'started_ns': ticks, 'deadline_ns': ticks + 30_000_000_000},
                      'snapshot': {'candidate_count': 32}}, 'slot': slot,
        'fixed_run_id': hashlib.sha256(slot_raw).hexdigest()[:32],
        'input_digest': saved['digest'], 'composition_preview_sha256': request['preview_sha256'],
        'prompt_sha256': saved['request']['prompt_sha256'], 'packet': packet, 'maximum_seconds': 30, 'mode': 'text-only',
        'preparation': {'path': str(prep_path), 'sha256': hashlib.sha256(prep_raw).hexdigest(), 'bytes': len(prep_raw)}}
    calls = []

    def validate(selected_state, project, value, *, prepared):
        assert selected_state.root == state.root and project == 'demo'
        assert value == authority and prepared['digest'] == saved['digest']
        calls.append('authority')
        return value

    import ergora.training.execution_protocol as training_execution_protocol
    monkeypatch.setattr(training_execution_protocol, 'resolve_cycle_snapshot', lambda operation: (
        {'definition': {'candidates': [{'experiment_id': 'screen-' + str(number)} for number in range(32)]}},
        {'execution': {'state_directory': str(native_state)}}))
    monkeypatch.setattr(training_cycles, 'validate_analysis_authority', validate, raising=False)
    monkeypatch.setattr(training_cycles, 'analysis_authority_remaining',
        lambda selected: 30 - (budget_clock._clock()[1] - ticks) / 1_000_000_000, raising=False)
    # This fixture substitutes the native model/process port in the test runner;
    # the actual dedicated subtree owner is exercised in test_agents.
    monkeypatch.setattr(processes, 'prepare_supervised', lambda: None)
    monkeypatch.setattr(processes, '_reap_children', lambda: [])

    def model(argv, cwd, output, timeout, stdin, env, **options):
        calls.append('model')
        assert options['supervised'] and options['record_lifecycle'] and not options['stop_requested']()
        folder = agent_runs.cycle_analysis_path(state.root, slot['authorization_sha256'], slot['ordinal'], slot['phase'])
        assert (folder / 'intent.json').is_file() and (folder / 'attempt.json').is_file()
        assert timeout <= authority['maximum_seconds'] and stdin == saved['prompt']
        output.mkdir()
        owner = processes.identity(os.getpid())
        cleanup = {'schema_version': 1, 'kind': 'supervised-process-cleanup', 'owner': owner,
                   'model': {'pid': 123456789, 'start_ticks': '1', 'boot_id': owner['boot_id']},
                   'model_waited': True, 'returncode': 0, 'descendants': [], 'remaining_children': []}
        (output / 'process-cleanup.json').write_text(json.dumps(cleanup))
        (output / 'stdout.txt').write_text('{}\n')
        Path(argv[argv.index('--output-last-message') + 1]).write_text(json.dumps(
            {'summary': 'Fixed packet analysis', 'artifacts': {'response': 'Bounded feedback'}, 'decision': 'approve'}))
        return {'status': 'succeeded', 'returncode': 0, 'output': str(output)}

    monkeypatch.setattr(processes, 'run', model)
    return state, source, authority, calls


@pytest.mark.parametrize('ordinal', [-1, 0, 31])
def test_cycle_analysis_consumes_one_durable_fixed_run_and_lost_reply_only_inspects(cycle_analysis_case, monkeypatch, ordinal):
    import ergora.training.cycles as training_cycles
    state, source, authority, calls = cycle_analysis_case
    authority['slot'].update(ordinal=ordinal, phase='baseline' if ordinal == -1 else 'screen')
    prep_path = Path(authority['preparation']['path'])
    preparation = json.loads(prep_path.read_bytes())
    preparation.update(ordinal=ordinal, phase=authority['slot']['phase'])
    prep_raw = json.dumps(preparation, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    prep_path.write_bytes(prep_raw)
    authority['preparation'].update(sha256=hashlib.sha256(prep_raw).hexdigest(), bytes=len(prep_raw))
    raw = json.dumps(authority['slot'], sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    authority['fixed_run_id'] = hashlib.sha256(raw).hexdigest()[:32]
    first = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert first['outcome'] == 'provisional' and first['cleanup']['model']['state'] == 'reaped'
    assert first['cleanup']['MCP']['state'] == 'not_requested' and first['receipt_sha256']
    assert calls.count('model') == 1
    shutil.rmtree(source)
    monkeypatch.setattr(training_cycles, 'validate_analysis_authority', lambda *a, **k: pytest.fail('No current readmission after attempt'))
    monkeypatch.setattr(agents, 'invoke', lambda *a, **k: pytest.fail('No repeat model'))
    repeated = agent_runs.run_cycle_analysis(State(state.root), 'demo', source, authority, stop_requested=lambda: True)
    assert repeated == first and calls.count('model') == 1


def test_cycle_analysis_pending_attempt_and_changed_packet_never_buy_another_opportunity(cycle_analysis_case, monkeypatch):
    state, source, authority, calls = cycle_analysis_case

    class LostReply(BaseException):
        pass

    def lose(*args, **kwargs):
        raise LostReply()

    monkeypatch.setattr(agent_runs, '_run_prepared', lose)
    with pytest.raises(LostReply):
        agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    folder = agent_runs.cycle_analysis_path(state.root, authority['slot']['authorization_sha256'], 0)
    original = (folder / 'attempt.json').read_bytes()
    repeated = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert repeated['outcome'] == 'needs_reconciliation' and calls.count('model') == 0
    changed = {**authority, 'packet': {'different': 'packet'}, 'fixed_run_id': 'analysis-' + 'b' * 48}
    observed = agent_runs.run_cycle_analysis(state, 'demo', source, changed, stop_requested=lambda: False)
    assert observed['outcome'] == 'needs_reconciliation' and (folder / 'attempt.json').read_bytes() == original
    assert len(list((state.root / 'runs').glob('.cycle-analysis-*'))) == 2  # original packet and original lock


@pytest.mark.parametrize('changed', ['result', 'cleanup', 'cleanup-inode'])
def test_cycle_analysis_late_artifacts_cannot_replace_original_terminal_receipt(cycle_analysis_case, monkeypatch, changed):
    state, source, authority, calls = cycle_analysis_case
    first = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    run_id = authority['fixed_run_id']
    target = state.root / 'runs' / run_id / ('result.json' if changed == 'result' else 'process-cleanup.json')
    if changed == 'result':
        target.write_text('{"summary":"late"}')
    elif changed == 'cleanup':
        value = json.loads(target.read_text())
        value['remaining_children'] = ['123']
        target.write_text(json.dumps(value))
    else:
        original_sync = native_sources.sync_directory_chain

        def replace(directory):
            original_sync(directory)
            if directory == target.parent:
                other = target.with_suffix('.late')
                other.write_bytes(target.read_bytes())
                other.replace(target)

        monkeypatch.setattr(native_sources, 'sync_directory_chain', replace)
    observed = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert first['outcome'] == 'provisional' and observed['outcome'] == 'needs_reconciliation'
    assert calls.count('model') == 1


def test_cycle_analysis_stop_during_input_preparation_consumes_attempt_without_model(cycle_analysis_case, monkeypatch):
    state, source, authority, calls = cycle_analysis_case
    original = shutil.copy2
    stopped = False

    def copy(*args, **kwargs):
        nonlocal stopped
        result = original(*args, **kwargs)
        stopped = True
        return result

    monkeypatch.setattr(shutil, 'copy2', copy)
    observed = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: stopped)
    assert observed['outcome'] == 'failed' and calls.count('model') == 0
    assert observed['cleanup']['model']['state'] == 'not_started'
    repeated = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert repeated == observed and calls.count('model') == 0


def test_cycle_analysis_stop_during_final_sync_keeps_original_opportunity_unknown(cycle_analysis_case, monkeypatch):
    state, source, authority, calls = cycle_analysis_case
    original = agent_runs._publish_session_packet
    stopped = False

    def publish(destination, values):
        nonlocal stopped
        original(destination, values)
        if destination.name == 'final':
            stopped = True

    monkeypatch.setattr(agent_runs, '_publish_session_packet', publish)
    first = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: stopped)
    assert first['outcome'] == 'needs_reconciliation' and calls.count('model') == 1
    repeated = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert repeated['outcome'] == 'needs_reconciliation' and calls.count('model') == 1


@pytest.mark.parametrize('boundary', ['final', 'confirmation-stop', 'confirmation-readback', 'confirmation-eviction'])
def test_cycle_analysis_original_terminal_confirmation_never_repaired_after_interrupted_publication(
        cycle_analysis_case, monkeypatch, boundary):
    state, source, authority, calls = cycle_analysis_case
    original = agent_runs._publish_session_packet
    stopped = False

    class LostReply(BaseException):
        pass

    def publish(destination, values):
        nonlocal stopped
        original(destination, values)
        if destination.name == 'final' and boundary == 'final':
            raise LostReply()
        if destination.name == 'confirmation':
            if boundary == 'confirmation-readback':
                raise ValueError('Original confirmation readback is unconfirmed')
            stopped = True
            if boundary == 'confirmation-eviction':
                raise LostReply()

    monkeypatch.setattr(agent_runs, '_publish_session_packet', publish)
    if boundary in ('final', 'confirmation-eviction'):
        with pytest.raises(LostReply):
            agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: stopped)
    else:
        first = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: stopped)
        assert first['outcome'] == 'needs_reconciliation'
    repeated = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert repeated['outcome'] == ('provisional' if boundary == 'confirmation-eviction' else 'needs_reconciliation')
    assert calls.count('model') == 1
    folder = agent_runs.cycle_analysis_path(state.root, authority['slot']['authorization_sha256'], 0)
    assert (folder / 'final').is_dir()
    if boundary == 'final':
        assert not (folder / 'confirmation').exists()
    elif boundary == 'confirmation-eviction':
        assert (folder / 'confirmation').is_dir() and not (folder / 'interrupted').exists()
        # H's visible evidence is provisional. Only the original S's normal
        # H wait/exit + complete operation proof can authorize continuation.
        operation = authority['operation']['identity']['operation_id']
        assert not (state.root / 'operations/training-cycles' / operation / 'completion.json').exists()
    else:
        assert (folder / 'confirmation').is_dir() and (folder / 'interrupted').is_dir()


@pytest.mark.parametrize('changed', ['missing', 'unwaited', 'owner', 'MCP'])
def test_cycle_analysis_model_success_needs_original_process_and_mcp_cleanup(cycle_analysis_case, monkeypatch, changed):
    import ergora.agents.mcp as task_mcp
    state, source, authority, calls = cycle_analysis_case
    original = processes.run
    if changed == 'MCP':
        authority['mode'] = 'task-mcp'
        monkeypatch.setattr(task_mcp, 'check_available', lambda: None)
        monkeypatch.setattr(task_mcp, 'freeze', lambda *a, **k: {'sha256': 'f' * 64})
        monkeypatch.setattr(task_mcp, 'launch', lambda *a, **k: {'command': 'fixed-resources-only'})

        async def preflight(*args, **kwargs):
            assert not kwargs['stop_requested']() and kwargs['remaining']() <= authority['maximum_seconds']
            return {'initialized': True}

        monkeypatch.setattr(task_mcp, 'probe', preflight)
        monkeypatch.setattr(task_mcp, 'verify_native', lambda *a, **k: {'ready': True})

    def model(*args, **kwargs):
        result = original(*args, **kwargs)
        path = args[2] / 'process-cleanup.json'
        if changed == 'missing':
            path.unlink()
        elif changed != 'MCP':
            value = json.loads(path.read_text())
            if changed == 'unwaited':
                value['descendants'] = [{'process': {'pid': 123}, 'wait_pid': None, 'wait_status': None}]
            else:
                value['owner']['start_ticks'] = 'different-owner'
            path.write_text(json.dumps(value))
        return result

    monkeypatch.setattr(processes, 'run', model)
    observed = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert calls.count('model') == 1 and observed['outcome'] == 'needs_reconciliation'
    assert observed['cleanup']['model']['state'] == 'unknown'


def test_cycle_analysis_mcp_preparation_consumes_original_stop_and_never_spawns_model(cycle_analysis_case, monkeypatch):
    import ergora.agents.mcp as task_mcp
    state, source, authority, calls = cycle_analysis_case
    authority['mode'] = 'task-mcp'
    stopped = False
    monkeypatch.setattr(task_mcp, 'check_available', lambda: None)
    monkeypatch.setattr(task_mcp, 'freeze', lambda *a, **k: {'sha256': 'f' * 64})
    monkeypatch.setattr(task_mcp, 'launch', lambda *a, **k: {'command': 'fixed-resources-only'})

    async def preflight(*args, **kwargs):
        nonlocal stopped
        assert kwargs['remaining']() <= authority['maximum_seconds']
        stopped = True
        assert kwargs['stop_requested']()
        raise ValueError('Parent stopped in MCP preparation')

    monkeypatch.setattr(task_mcp, 'probe', preflight)
    observed = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: stopped)
    assert observed['outcome'] == 'needs_reconciliation' and calls.count('model') == 0
    repeated = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert repeated == observed


@pytest.mark.parametrize('boundary', ['boot', 'ticks', 'operation'])
def test_cycle_analysis_never_renews_original_parent_or_slot_allowance(cycle_analysis_case, monkeypatch, boundary):
    from ergora.runtime import budget_clock
    import ergora.training.cycles as training_cycles
    state, source, authority, calls = cycle_analysis_case
    original_clock = budget_clock._clock
    original_publish = agent_runs._publish_session_packet
    consumed = False

    def publish(destination, values):
        nonlocal consumed
        original_publish(destination, values)
        if 'attempt.json' in values:
            consumed = True

    def clock():
        boot, ticks = original_clock()
        if consumed:
            if boundary == 'boot':
                boot = 'different-original-boot'
            elif boundary == 'ticks':
                ticks += 31_000_000_000
        return boot, ticks

    monkeypatch.setattr(agent_runs, '_publish_session_packet', publish)
    monkeypatch.setattr(budget_clock, '_clock', clock)
    monkeypatch.setattr(budget_clock, 'authorize', lambda *a: pytest.fail('Analysis cannot authorize any new clock'))
    monkeypatch.setattr(training_cycles, 'analysis_authority_remaining',
                        lambda value: 0 if consumed and boundary == 'operation' else 30)
    observed = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert observed['outcome'] == 'needs_reconciliation' and calls.count('model') == 0
    assert agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False) == observed


def test_cycle_analysis_skip_first_vetoes_durable_attempt_under_original_submission_lock(cycle_analysis_case):
    import ergora.training.execution_protocol as training_execution_protocol
    state, source, authority, calls = cycle_analysis_case
    _, authorization = training_execution_protocol.resolve_cycle_snapshot(authority['operation'])
    path = training_execution_protocol.skip_decision_path(authorization['execution'], 'screen-0')
    path.write_bytes(b'Unresolved original skip is still an irreversible veto')
    with pytest.raises(ValueError, match='skip|Skip'):
        agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    folder = agent_runs.cycle_analysis_path(state.root, authority['slot']['authorization_sha256'], 0)
    assert not folder.exists() and calls.count('model') == 0


@pytest.mark.skipif(sys.platform != 'linux', reason='Original task MCP process identity requires Linux/WSL2')
def test_task_mcp_closed_audit_cannot_certify_a_still_live_original_process():
    import ergora.agents.mcp as task_mcp
    identity = processes.identity(os.getpid())
    events = [{'event': 'started', 'scope_sha256': 'd' * 64, 'pid': os.getpid(), 'identity': identity},
              {'event': 'closed', 'scope_sha256': 'd' * 64, 'pid': os.getpid()}]
    raw = ('\n'.join(json.dumps(event) for event in events) + '\n').encode()
    with pytest.raises(ValueError, match='still alive'):
        task_mcp.verify_cleanup(raw, 'd' * 64)
    with pytest.raises(ValueError, match='closed lifecycle'):
        task_mcp.verify_cleanup(raw.splitlines()[0], 'd' * 64)


@pytest.mark.parametrize('stop', [False, True])
def test_candidate_source_task_mcp_closes_its_actual_original_process(cycle_analysis_case, tmp_path, monkeypatch, stop):
    import asyncio
    import importlib.util
    import ergora.agents.mcp as task_mcp

    if sys.platform != 'linux' or importlib.util.find_spec('mcp') is None:
        pytest.skip('Explicit Linux source stdio MCP fixture requires task-mcp extra')
    _, source, _, _ = cycle_analysis_case
    scope = task_mcp.freeze(workflows.inspect_input(source, material=True), 'f' * 32, tmp_path / 'source-scope.json')
    audit = tmp_path / 'source-audit.jsonl'
    # Production launch deliberately uses -I and the installed package. This
    # controlled source child checks these changed server bytes independently.
    source_root = str(IMPORT_ROOT)
    configuration = {'command': sys.executable, 'args': ['-P', '-c',
        'import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import ergora.agents.mcp as task_mcp;'
        "assert Path(task_mcp.__file__).resolve()==Path(sys.argv[1])/'ergora/agents/mcp.py';"
        'task_mcp.serve(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]))', source_root, scope['path'], scope['sha256'], str(audit)]}

    def stopped():
        return stop and audit.exists() and bool(audit.read_bytes())

    if stop:
        with pytest.raises(ValueError, match='Parent stopped'):
            asyncio.run(task_mcp.probe(configuration, tmp_path / 'source-stderr.txt',
                                      stop_requested=stopped, remaining=lambda: 5))
    else:
        result = asyncio.run(task_mcp.probe(configuration, tmp_path / 'source-stderr.txt',
                                          stop_requested=stopped, remaining=lambda: 5))
        assert result['read_only_probe'] == 'succeeded'
    cleanup = task_mcp.verify_cleanup(audit.read_bytes(), scope['sha256'])
    assert cleanup['state'] == 'closed' and cleanup['process']['pid'] != os.getpid()


def test_cycle_analysis_fixed_task_mcp_confirms_both_actual_source_lifecycles_once(cycle_analysis_case, tmp_path, monkeypatch):
    import asyncio
    import importlib.util
    import ergora.agents.mcp as task_mcp

    if sys.platform != 'linux' or importlib.util.find_spec('mcp') is None:
        pytest.skip('Explicit Linux source stdio MCP fixture requires task-mcp extra')
    state, source, authority, calls = cycle_analysis_case
    authority['mode'] = 'task-mcp'
    native = None
    launches = []

    def launch(scope, audit):
        nonlocal native
        native = {'command': sys.executable, 'args': ['-P', '-c',
            'import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import ergora.agents.mcp as task_mcp;'
            "assert Path(task_mcp.__file__).resolve()==Path(sys.argv[1])/'ergora/agents/mcp.py';"
            'task_mcp.serve(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]))',
            str(IMPORT_ROOT), scope['path'], scope['sha256'], str(audit)]}
        launches.append(audit)
        return native

    model_port = processes.run

    def model(*args, **kwargs):
        result = asyncio.run(task_mcp.probe(native, tmp_path / 'source-native-stderr.txt',
            stop_requested=kwargs['stop_requested'], remaining=lambda: args[3]))
        assert result['read_only_probe'] == 'succeeded'
        return model_port(*args, **kwargs)

    monkeypatch.setattr(task_mcp, 'launch', launch)
    monkeypatch.setattr(processes, 'run', model)
    observed = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert observed['outcome'] == 'provisional' and observed['cleanup']['MCP']['state'] == 'closed'
    preflight, native_process = (observed['cleanup']['MCP'][key]['process'] for key in ('preflight', 'native'))
    assert preflight != native_process and preflight['pid'] != os.getpid() and native_process['pid'] != os.getpid()
    assert len(launches) == 2 and calls.count('model') == 1
    assert agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False) == observed
    assert len(launches) == 2 and calls.count('model') == 1


def test_provisional_analysis_cannot_satisfy_default_native_reader_without_original_s_completion(cycle_analysis_case):
    import ergora.training.execution_protocol as protocol
    state, source, authority, calls = cycle_analysis_case
    observed = agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False)
    assert observed['outcome'] == 'provisional'
    raw = Path(observed['receipt']['path']).read_bytes()
    ref = {**observed['receipt'], 'bytes': len(raw)}
    material = workflows.inspect_input(source, material=True)
    plan = {'analyst': {'definition_digest': authority['slot']['definition_digest'],
                       'binding': authority['slot']['binding'], 'instance': material['request']['instance'],
                       'composition': material['composition']}}
    authorization = {'sha256': authority['slot']['authorization_sha256'], 'project': 'demo', 'control_home': str(state.root)}
    arguments = (ref, plan, authorization, 0, 'screen', authority['slot']['packet_sha256'])
    own = protocol._analysis_receipt(*arguments, provisional_operation_id=authority['operation']['identity']['operation_id'])
    assert own['outcome'] == 'provisional'
    with pytest.raises(FileNotFoundError, match='completion.json'):
        protocol._analysis_receipt(*arguments)
    assert agent_runs.run_cycle_analysis(state, 'demo', source, authority, stop_requested=lambda: False) == observed
    assert calls.count('model') == 1


@pytest.mark.parametrize("floor,effort", [("medium", "medium"), ("high", "xhigh"), ("xhigh", "max"), ("max", "ultra")])
def test_explicit_minimum_reaches_native_command_without_replacing_provider(prepared, tmp_path, monkeypatch, floor, effort):
    requested = {"tool": "codex", "model": "gpt-6.2-sol", "reasoning_effort": floor}
    state, _, source = prepared(binding=requested,
        minimum={"model": requested["model"], "reasoning_effort": floor})
    config = tmp_path / "inference.toml"
    config.write_text('model="operator-default"\nmodel_reasoning_effort="low"\nmodel_provider="fixture"\n'
        '[model_providers.fixture]\nname="Fixture"\nbase_url="https://example.invalid/v1"\n'
        'env_key="ERGORA_TEST_KEY"\nwire_api="responses"\n', encoding="utf-8")
    actual = {**requested, "reasoning_effort": effort}
    assert agent_runs.check_input(state, "demo", source, backend="codex", codex_config=config)['binding'] == requested
    calls = []

    def native(argv, cwd, output, timeout, stdin, env, **kwargs):
        calls.append(argv)
        assert argv[argv.index("--model") + 1] == actual["model"]
        settings = dict(argv[i + 1].split("=", 1) for i, item in enumerate(argv) if item == "-c")
        assert settings["model_reasoning_effort"] == json.dumps(effort)
        assert settings["model_provider"] == '"fixture"'
        assert settings["model_providers.fixture.env_key"] == '"ERGORA_TEST_KEY"'
        assert settings["model_providers.fixture.base_url"] == '"https://example.invalid/v1"'
        Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(
            {"summary": "Review", "artifacts": {"response": "Evidence"}, "decision": "approve"}))
        output.mkdir()
        return {"status": "succeeded", "returncode": 0, "output": str(output)}

    monkeypatch.setattr(processes, "run", native)
    run = agent_runs.run_input(state, "demo", source, codex_config=config, binding_override=actual)
    assert run["status"] == "succeeded" and run["binding"] == actual and run["requested_binding"] == requested
    assert len(calls) == 1
    assert agent_runs.inspect_run(state, "demo", run['id'])['input']['available']
    run['binding'] = {**actual, 'reasoning_effort': 'low'}
    with state.connect() as db:
        db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(run), run['id']))
    observed = agent_runs.inspect_run(state, "demo", run['id'])
    assert not observed['input']['available'] and 'at least' in observed['input']['error']
    assert observed['run'] == run and len(calls) == 1


@pytest.mark.parametrize("binding", [
    {"tool": "codex", "reasoning_effort": "high"},
    {"tool": "codex", "model": "gpt-6.1-sol", "reasoning_effort": "ultra"},
    {"tool": "codex", "model": "gpt-6.2-sol"},
    {"tool": "codex", "model": "gpt-6.2-sol", "reasoning_effort": "medium"},
    {"tool": "claude-code", "model": "gpt-6.2-sol", "effort": "high"},
])
def test_actual_binding_below_minimum_is_rejected_before_run(prepared, monkeypatch, binding):
    requested = {"tool": "codex", "model": "gpt-6.2-sol", "reasoning_effort": "high"}
    state, _, source = prepared(binding=requested,
        minimum={"model": requested["model"], "reasoning_effort": requested["reasoning_effort"]})
    monkeypatch.setattr(processes, "run", lambda *args, **kwargs: pytest.fail("Rejected calls must not run"))
    with pytest.raises(ValueError, match="requires"):
        agent_runs.run_input(state, "demo", source, binding_override=binding)
    assert agent_runs.runs(state, "demo") == []


@pytest.fixture
def recorded_run(prepared, monkeypatch):
    state, repo, source = prepared()
    result = {"summary": "Complete original review", "artifacts": {"response": "原始完整回复。" * 12000}, "decision": "approve"}

    def native(argv, cwd, output, timeout, stdin, env, **kwargs):
        Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(result), encoding="utf-8")
        output.mkdir()
        return {"status": "succeeded", "returncode": 0, "output": str(output)}

    monkeypatch.setattr(processes, "run", native)
    run = agent_runs.run_input(state, "demo", source)
    assert run["status"] == "succeeded"
    monkeypatch.setattr(agents, "invoke", lambda *args, **kwargs: pytest.fail("Inspection must never redispatch"))
    return state, repo, run, result


def test_exact_run_inspection_survives_history_limit_and_relocation_without_current_backend(recorded_run, tmp_path,
                                                                                           monkeypatch, capsys):
    state, repo, run, result = recorded_run
    projects.create(state, "other", repo)
    with pytest.raises(ValueError, match="Unknown agent run in this project"):
        agent_runs.inspect_run(state, "other", run["id"])
    with state.connect() as db:
        db.executemany("INSERT INTO agent_runs VALUES (?, ?, ?)",
            [(f"later-{number}", "demo", json.dumps({**run, "id": f"later-{number}"})) for number in range(100)])
    assert run["id"] not in [item["id"] for item in agent_runs.runs(state, "demo")]
    moved = tmp_path / "relocated-state"
    shutil.copytree(state.root, moved)
    shutil.rmtree(state.root)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(agent_backends, "for_binding", lambda *args, **kwargs: pytest.fail("Historical read has no live admission"))
    state = State(moved)
    with state.connect() as db:
        before = list(db.iterdump())
    assert main(["--home", str(moved), "composition", "inspect-run", "demo", run["id"]]) == 0
    observed = json.loads(capsys.readouterr().out)
    assert observed["run"] == run and observed["input"]["digest"] == run["input_digest"]
    assert observed["input"]["request"] == run["input_request"] and observed["prompt"]["available"]
    assert observed["result"]["document"] == result and observed["result"]["bytes"] > 65536
    assert observed["result"]["sha256"] == run["result_sha256"]
    assert agent_runs.inspect_run(state, "demo", run["id"], max_result_bytes=10**30)["result"] == observed["result"]
    with state.connect() as db:
        assert list(db.iterdump()) == before


@pytest.mark.skipif(sys.platform != "linux", reason="DeepSeek Harness adapter requires Linux/WSL2")
@pytest.mark.parametrize("malformed", [False, True], ids=["valid", "duplicate-surrogate-key"])
def test_original_deepseek_usage_is_bound_to_its_run_artifact(prepared, tmp_path, monkeypatch, capsys, malformed):
    state, _, source = prepared()
    binding = {"tool": "deepseek-harness", "python": str(tmp_path / "unavailable-python"), "model": "test",
               "base_url": "http://127.0.0.1:1/v1", "api_key_env": "FIXTURE_MODEL_KEY"}
    result = {"summary": "Review complete", "artifacts": {"response": "Verified"}, "decision": "approve"}
    tokens = {"inputTokens": 30, "outputTokens": 11, "totalTokens": 48, "cacheReadTokens": 7}
    native = {"finish_reason": "completed", "final_response": json.dumps(result),
              "events": [{"type": "assistant/message", "data": {"usage": tokens}}]}
    raw = json.dumps(native).encode()
    if malformed:
        raw = raw.replace(b'"cacheReadTokens": 7}', rb'"cacheReadTokens": 7, "\ud800": 1, "\ud800": 2}', 1)

    def finish(argv, cwd, output, *args, **kwargs):
        output.mkdir()
        Path(argv[-1]).with_name("native-result.json").write_bytes(raw)
        return {"status": "succeeded", "returncode": 0, "output": str(output)}

    monkeypatch.setattr(processes, "run", finish)
    run = agent_runs.run_input(state, "demo", source, binding_override=binding)
    assert run["status"] == "succeeded"
    monkeypatch.setattr(processes, "run", lambda *args, **kwargs: pytest.fail("Usage inspection must not invoke a backend"))
    moved = tmp_path / "relocated"
    state.root.rename(moved)
    assert main(["--home", str(moved), "composition", "inspect-run", "demo", run["id"]]) == 0
    observed = json.loads(capsys.readouterr().out)
    assert observed["native_usage"] == run["native_usage"] and observed["result"]["document"] == result
    usage = observed["native_usage"]
    assert usage["source_sha256"] == hashlib.sha256(raw).hexdigest()
    if malformed:
        assert usage["state"] == "invalid" and usage["available"] is False and "sdk_tokens" not in usage
        assert usage["error"] == "Malformed DeepSeek Harness native result JSON"
    else:
        assert usage["available"] is True and usage["sdk_tokens"] == tokens

    artifact = moved / "runs" / (run["id"] + ".protocol") / "native-result.json"
    assert artifact.read_bytes() == raw
    artifact.write_bytes(raw + b"\n")
    changed = agent_runs.inspect_run(State(moved), "demo", run["id"])
    assert changed["native_usage"]["state"] == "mismatch" and changed["native_usage"]["available"] is False
    assert changed["result"] == observed["result"]
    artifact.unlink()
    missing = agent_runs.inspect_run(State(moved), "demo", run["id"])
    assert missing["native_usage"]["state"] == "missing" and missing["native_usage"]["available"] is False
    assert missing["result"] == observed["result"]


@pytest.mark.parametrize("changed", ["input", "recursive-input", "prompt", "result", "recursive-result", "nonfinite-result", "overflow-result",
                                     "missing-result", "unrecorded-result", "capacity"])
def test_run_inspection_retains_original_state_and_other_material_when_one_artifact_is_unverifiable(recorded_run, changed):
    state, _, run, result = recorded_run
    storage, run_id = state.root / "runs", run["id"]
    if changed == "input":
        (storage / (run_id + ".input") / "task.txt").write_text("A different task", encoding="utf-8")
    elif changed in ("recursive-input", "recursive-result"):
        depth = 20 * sys.getrecursionlimit()
        raw = ("[" * depth + "0" + "]" * depth).encode()
        if changed == "recursive-input":
            (storage / (run_id + ".input") / "request.json").write_bytes(raw)
        else:
            (storage / run_id / "result.json").write_bytes(raw)
            run = {**run, "result_sha256": hashlib.sha256(raw).hexdigest()}
            with state.connect() as db:
                db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(run), run_id))
    elif changed in ("nonfinite-result", "overflow-result"):
        raw = b'{"original_value":' + (b'NaN' if changed == "nonfinite-result" else b'1e309') + b'}'
        (storage / run_id / "result.json").write_bytes(raw)
        run = {**run, "result_sha256": hashlib.sha256(raw).hexdigest()}
        with state.connect() as db:
            db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(run), run_id))
    elif changed == "prompt":
        (storage / (run_id + ".protocol") / "prompt.txt").write_text("A different prompt", encoding="utf-8")
    elif changed == "result":
        (storage / run_id / "result.json").write_text(json.dumps({**result, "decision": "request-changes"}), encoding="utf-8")
    elif changed == "missing-result":
        (storage / run_id / "result.json").unlink()
    elif changed == "unrecorded-result":
        run = {key: value for key, value in run.items() if key not in ("result", "result_sha256")}
        run.update(status="failed", error="No final receipt was recorded")
        with state.connect() as db:
            db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(run), run_id))
    observed = agent_runs.inspect_run(state, "demo", run_id, max_result_bytes=100 if changed == "capacity" else 8_388_608)
    unavailable = "input" if changed in ("input", "recursive-input") else "prompt" if changed == "prompt" else "result"
    assert observed["run"] == run and not observed[unavailable]["available"] and observed[unavailable]["error"]
    if unavailable != "input":
        assert observed["input"]["available"]
    if unavailable != "result":
        assert observed["result"]["document"] == result
    if unavailable != "prompt":
        assert observed["prompt"]["available"]
        assert observed["prompt"]["input_compared"] == observed["input"]["available"]
        assert observed["prompt"]["sha256"] == run["prompt_sha256"]
    with state.connect() as db:
        assert json.loads(db.execute("SELECT document FROM agent_runs WHERE id=?", (run_id,)).fetchone()[0]) == run


@pytest.mark.parametrize("depth,available", [(62, True), (80, False)])
def test_original_custom_schema_results_obey_observation_tree_capacity(prepared, monkeypatch, depth, available):
    state, _, source = prepared()
    raw = b'{"extra":' + b'[' * depth + b'0' + b']' * depth + b'}'

    def native(argv, cwd, output, *args, **kwargs):
        Path(argv[argv.index("--output-last-message") + 1]).write_bytes(raw)
        output.mkdir()
        return {"status": "succeeded", "returncode": 0}

    monkeypatch.setattr(processes, "run", native)
    run = agent_runs.run_input(state, "demo", source, result_schema={"type": "object"})
    assert run["status"] == "succeeded"
    original = Path(run["result"]).read_bytes()
    observed = agent_runs.inspect_run(state, "demo", run["id"])
    assert observed["result"]["available"] == available and observed["input"]["available"] and observed["prompt"]["available"]
    if available:
        assert observed["result"]["document"] == json.loads(raw)
    else:
        assert "64 levels" in observed["result"]["error"]
    assert Path(run["result"]).read_bytes() == original


@pytest.mark.parametrize("backend", ["codex", "claude-code"])
def test_call_persists_complete_snapshot_and_explicit_backend_without_ambient_tools(prepared, tmp_path, monkeypatch, capsys, backend):
    state, repo, source = prepared()
    original = workflows.inspect_input(source, material=True)
    admitted = agent_runs.check_input(state, "demo", source, backend=backend, model="fixture-model", reason="Explicit test selection",
                                     input_digest=original["digest"])
    config = tmp_path / "native.toml"
    config.write_text('model_provider="fixture"\napproval_policy="never"\nsandbox_mode="danger-full-access"\n'
        '[features]\nshell_tool=true\n[model_providers.fixture]\nname="Fixture"\n'
        'base_url="http://127.0.0.1:1/v1"\nenv_key="ERGORA_TEST_KEY"\nwire_api="responses"\n'
        '[mcp_servers.ambient]\ncommand="must-not-run"\n', encoding="utf-8")
    result = {"summary": "Reviewed supplied input", "artifacts": {"response": "Evidence"}, "decision": "approve"}
    def native(argv, cwd, output, timeout, stdin, env, **kwargs):
        running = agent_runs.runs(State(state.root), "demo")[0]
        assert running["status"] == "running" and running["binding"]["tool"] == backend
        assert workflows.inspect_input(Path(running["input_path"]))["digest"] == original["digest"]
        assert cwd != repo and cwd != source and not list(cwd.iterdir())
        assert stdin.encode() == (source / "prompt.txt").read_bytes() and timeout == 15
        assert "must-not-run" not in str(argv) and "danger-full-access" not in argv
        if backend == "codex":
            settings = dict(argv[i + 1].split("=", 1) for i, item in enumerate(argv) if item == "-c")
            assert settings['features.shell_tool'] == 'false' and settings['features.plugins'] == 'false'
            assert settings['model_providers.fixture.env_key'] == '"ERGORA_TEST_KEY"'
            assert "--ignore-user-config" in argv and "--ignore-rules" in argv
            Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(result), encoding="utf-8")
            payload = "{}"
        else:
            assert argv[argv.index("--tools") + 1] == "" and argv[argv.index("--setting-sources") + 1] == ""
            assert "--restricted" in argv and "--safe-mode" in argv and "--strict-mcp-config" in argv
            payload = json.dumps({"is_error": False, "structured_output": result})
        output.mkdir()
        (output / "stdout.txt").write_text(payload, encoding="utf-8")
        return {"status": "succeeded", "returncode": 0, "output": str(output)}
    monkeypatch.setattr(processes, "run", native)
    assert main(["--home", str(state.root), "composition", "run-input", "demo", str(source), "--backend", backend,
                 "--model", "fixture-model", "--backend-reason", "Explicit test selection", "--timeout", "15",
                 "--codex-config", str(config)]) == 0
    run = json.loads(capsys.readouterr().out)
    assert run["status"] == "succeeded" and run["requested_binding"] == {"tool": "codex"}
    assert run["backend_reason"] == "Explicit test selection" and run["formal_execution_authorized"] is False
    assert run["policy"] == admitted["policy"] and run["binding"] == admitted["binding"]
    assert all("text" not in resource and resource["sources"] for resource in run["context"]["resources"])
    assert json.loads(Path(run["result"]).read_text()) == result
    assert workflows.inspect_input(source)["digest"] == original["digest"]
    shutil.rmtree(source)
    saved = workflows.inspect_input(Path(run["input_path"]), material=True)
    assert saved["prompt"] == original["prompt"] and saved["request"]["execution_authorized"] is False
    protocol = Path(run["output"]).with_name(run["id"] + ".protocol")
    assert hashlib.sha256((protocol / "prompt.txt").read_bytes()).hexdigest() == run["prompt_sha256"]
    assert agent_runs.runs(State(state.root), "demo")[0] == run
    assert agent_runs.output(State(state.root), "demo", run["id"])["streams"]["stdout"]["available"]


def test_selected_digest_rejects_a_different_valid_input_before_run_or_model(prepared, tmp_path, monkeypatch):
    state, _, source = prepared()
    original = workflows.inspect_input(source)
    replacement = tmp_path / "replacement"
    workflows.prepare_input(state.root, "structure-review", "1.0.0", "root/review", original["request"]["grant"],
                            b"Review a different candidate.", replacement, 30000)
    selected = workflows.inspect_input(replacement)
    assert selected["digest"] != original["digest"]
    assert agent_runs.check_input(state, "demo", replacement, input_digest=selected["digest"])["input_digest"] == selected["digest"]
    monkeypatch.setattr(processes, "run", lambda *a, **k: pytest.fail("A changed selection must not call the model"))
    for operation in (agent_runs.check_input, agent_runs.run_input):
        with pytest.raises(ValueError, match="explicitly selected digest"):
            operation(state, "demo", replacement, input_digest=original["digest"])
    assert agent_runs.runs(state, "demo") == [] and not (state.root / "runs").exists()


@pytest.mark.parametrize("permission", [("write", ["workspace"]), ("shell", True), ("network", ["https://example.com"])])
def test_text_only_refuses_unsupported_permissions_before_creating_a_run(prepared, permission):
    state, _, source = prepared(permission=permission)
    for operation in (agent_runs.check_input, agent_runs.run_input):
        with pytest.raises(ValueError, match="Text-only"):
            operation(state, "demo", source)
    assert agent_runs.runs(state, "demo") == [] and not (state.root / "runs").exists()


def test_command_cannot_claim_text_only_capability(prepared):
    state, _, source = prepared(binding={"tool": "command", "argv": ["must-not-run"], "protocol": "stage-json-v1",
                                         "capabilities": agents.GENERAL_CAPABILITIES})
    for operation in (agent_runs.check_input, agent_runs.run_input):
        with pytest.raises(ValueError, match="does not support text-only"):
            operation(state, "demo", source)
    assert agent_runs.runs(state, "demo") == []


def test_historical_input_does_not_bypass_current_admission_when_overriding_backend(prepared, monkeypatch):
    state, _, source = prepared()
    def reject(*args, **kwargs):
        raise ValueError("Current policy rejects this definition")
    monkeypatch.setattr(agents, "validate_binding", reject)
    assert workflows.inspect_input(source)["request"]["execution_authorized"] is False
    for operation in (agent_runs.check_input, agent_runs.run_input):
        with pytest.raises(ValueError, match="Current policy"):
            operation(state, "demo", source, backend="claude-code")
    assert agent_runs.runs(state, "demo") == []


def test_declared_sandbox_is_visible_but_cannot_expand_restricted_call_tools(prepared, tmp_path, monkeypatch):
    state, _, source = prepared(binding={"tool": "codex", "sandbox": "workspace-write"})
    admitted = agent_runs.check_input(state, "demo", source)
    sandbox = admitted["policy"]["capabilities"]["backend_sandbox"]
    assert sandbox["requested"] == "workspace-write" and sandbox["effective"] == "read-only" and sandbox["status"] == "advisory"
    result = {"summary": "Reviewed", "artifacts": {"response": "Evidence"}, "decision": "approve"}

    def native(argv, cwd, output, *args, **kwargs):
        assert argv[argv.index("--sandbox") + 1] == "read-only"
        settings = dict(argv[i + 1].split("=", 1) for i, item in enumerate(argv) if item == "-c")
        assert settings["features.shell_tool"] == "false"
        Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(result), encoding="utf-8")
        output.mkdir()
        return {"status": "succeeded", "returncode": 0, "output": str(output)}

    monkeypatch.setattr(processes, "run", native)
    run = agent_runs.run_input(state, "demo", source)
    assert run["status"] == "succeeded" and run["policy"] == admitted["policy"]


@pytest.mark.parametrize("mode", ["text-only", "task-mcp"])
@pytest.mark.parametrize("content,error", [("model_providers=[]\n", "TOML tables"), ("model=2026-11-09\n", "JSON-compatible"),
                                         ("model=nan\n", "JSON-compatible"), ("model=inf\n", "JSON-compatible"),
                                         ("model=-inf\n", "JSON-compatible")])
def test_invalid_inference_config_rejects_check_and_run_before_side_effects(prepared, tmp_path, monkeypatch, content, error, mode):
    state, _, source = prepared()
    config = tmp_path / "invalid.toml"
    config.write_text(content, encoding="utf-8")
    monkeypatch.setattr(processes, "run", lambda *a, **k: pytest.fail("Invalid inference config must not call model"))
    for operation in (agent_runs.check_input, agent_runs.run_input):
        with pytest.raises(ValueError, match=error):
            operation(state, "demo", source, codex_config=config, mode=mode)
    assert agent_runs.runs(State(state.root), "demo") == [] and not (state.root / "runs").exists()


def test_native_stdin_matches_saved_prompt_bytes_with_unicode_and_mixed_newlines(tmp_path):
    prompt = "Ancestor instructions.\n资料与任务。\r\nChild instructions.\rFinal line.\n"
    output = tmp_path / "output"
    result = processes.run([sys.executable, "-c", "import hashlib,sys;sys.stdout.write(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())"],
                           tmp_path, output, 10, prompt)
    assert result["status"] == "succeeded"
    raw = prompt.encode("utf-8")
    assert (output / "stdin.txt").read_bytes() == raw
    assert (output / "stdout.txt").read_bytes() == hashlib.sha256(raw).hexdigest().encode("ascii")


def test_native_command_record_matches_selected_executable_and_arguments(tmp_path):
    program = Path(sys.executable).name if os.name == "nt" else sys.executable
    argv = [program, "-c", "import sys;print(sys.executable);print(sys.argv[1])", "资料与参数"]
    record = tmp_path / "command.json"
    output = tmp_path / "output"
    result = processes.run(argv, tmp_path, output, 10, command_record=record)
    assert result["status"] == "succeeded"
    saved = json.loads(record.read_text(encoding="utf-8"))
    assert saved == [processes.resolve_program(program, tmp_path) if os.name == "nt" else program, *argv[1:]]
    executable, argument = (output / "stdout.txt").read_text(encoding="utf-8").splitlines()
    assert os.path.samefile(saved[0], executable) and argument == argv[-1]


def test_changed_snapshot_fails_before_model_call_and_keeps_durable_failure(prepared, monkeypatch):
    state, _, source = prepared()
    original = shutil.copytree
    def changed(source, target, *args, **kwargs):
        result = original(source, target, *args, **kwargs)
        if Path(target).name.endswith(".input"):
            (Path(target) / "prompt.txt").write_bytes(b"Ancestor material removed")
        return result
    monkeypatch.setattr(shutil, "copytree", changed)
    monkeypatch.setattr(processes, "run", lambda *a, **k: pytest.fail("Snapshot mismatch must not call the model"))
    run = agent_runs.run_input(state, "demo", source)
    assert run["status"] == "failed" and run["finished"] and "differs" in run["error"]
    assert agent_runs.runs(State(state.root), "demo")[0] == run
    assert not (state.root / "runs" / (run["id"] + ".protocol")).exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Original supervised cleanup requires Linux')
def test_independent_call_stop_during_snapshot_confirms_preparation_cleanup(prepared, monkeypatch):
    state, _, source = prepared()
    copy = shutil.copy2
    stopped = False

    def stop_copy(*args, **kwargs):
        nonlocal stopped
        result = copy(*args, **kwargs)
        stopped = True
        return result

    monkeypatch.setattr(shutil, 'copy2', stop_copy)
    monkeypatch.setattr(processes, 'prepare_supervised', lambda: None)
    monkeypatch.setattr(processes, '_reap_children', lambda: [])
    monkeypatch.setattr(agents, 'invoke', lambda *a, **k: pytest.fail('Stopped snapshot cannot invoke'))
    run = agent_runs.run_input(state, 'demo', source, supervised=True, record_lifecycle=True,
                              stop_requested=lambda: stopped)
    assert run['status'] == 'failed' and 'parent stopped' in run['error']
    cleanup = state.root / 'runs' / (run['id'] + '.preparation-cleanup') / 'record.json'
    assert json.loads(cleanup.read_bytes())['kind'] == 'composition-preparation-cleanup'
    assert agent_runs.runs(State(state.root), 'demo')[0] == run


@pytest.mark.skipif(sys.platform != 'linux', reason='Task MCP fixed-resource descriptors require Linux')
def test_independent_call_mcp_preparation_stop_fences_native(prepared, monkeypatch):
    import ergora.agents.mcp as task_mcp
    state, _, source = prepared()
    stopped = False
    monkeypatch.setattr(task_mcp, 'check_available', lambda: None)

    async def stop_probe(*args, **kwargs):
        nonlocal stopped
        assert kwargs['remaining']() == .125
        stopped = True
        assert kwargs['stop_requested']()
        raise ValueError('Original parent stopped inside MCP preflight')

    monkeypatch.setattr(task_mcp, 'probe', stop_probe)
    monkeypatch.setattr(agents, 'invoke', lambda *a, **k: pytest.fail('Stopped MCP cannot invoke'))
    run = agent_runs.run_input(state, 'demo', source, mode='task-mcp',
                              stop_requested=lambda: stopped, remaining=lambda: .125)
    assert run['status'] == 'failed' and 'inside MCP' in run['error']
    assert not (state.root / 'runs' / (run['id'] + '.protocol')).exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='Original supervised cleanup requires Linux')
def test_independent_call_fractional_allowance_reaches_original_process_lifecycle(prepared, monkeypatch):
    state, _, source = prepared()
    monkeypatch.setattr(processes, 'prepare_supervised', lambda: None)
    monkeypatch.setattr(processes, '_reap_children', lambda: pytest.fail('Native lifecycle already returned'))
    calls = []

    def native(argv, cwd, output, timeout, stdin, env, **options):
        calls.append(timeout)
        assert options['supervised'] and options['record_lifecycle'] and not options['stop_requested']()
        output.mkdir()
        (output / 'process-cleanup.json').write_text('{}')
        Path(argv[argv.index('--output-last-message') + 1]).write_text(json.dumps(
            {'summary': 'Review', 'artifacts': {'response': 'Evidence'}, 'decision': 'approve'}))
        return {'status': 'succeeded', 'returncode': 0, 'output': str(output)}

    monkeypatch.setattr(processes, 'run', native)
    run = agent_runs.run_input(state, 'demo', source, timeout=7, supervised=True, record_lifecycle=True,
                              stop_requested=lambda: False, remaining=lambda: .125)
    assert run['status'] == 'succeeded' and calls == [.125]
    assert not (state.root / 'runs' / (run['id'] + '.preparation-cleanup')).exists()


@pytest.mark.parametrize('boundary', ['command', 'result'])
def test_independent_call_original_stop_fences_final_spawn_and_result(prepared, monkeypatch, boundary):
    state, _, source = prepared()
    stopped, calls = False, []
    method = 'command' if boundary == 'command' else 'read_result'
    original = getattr(agent_backends.CodexBackend, method)

    def stop_boundary(*args, **kwargs):
        nonlocal stopped
        result = original(*args, **kwargs)
        stopped = True
        return result

    def native(argv, cwd, output, *args, **kwargs):
        calls.append(argv)
        output.mkdir()
        Path(argv[argv.index('--output-last-message') + 1]).write_text(json.dumps(
            {'summary': 'Review', 'artifacts': {'response': 'Evidence'}, 'decision': 'approve'}))
        return {'status': 'succeeded', 'returncode': 0, 'output': str(output)}

    monkeypatch.setattr(agent_backends.CodexBackend, method, stop_boundary)
    monkeypatch.setattr(processes, 'run', native)
    run = agent_runs.run_input(state, 'demo', source, stop_requested=lambda: stopped)
    assert run['status'] == 'failed' and 'result' not in run
    assert len(calls) == (0 if boundary == 'command' else 1)
    assert agent_runs.runs(State(state.root), 'demo')[0] == run


@pytest.mark.parametrize("failure", ["timed_out", "invalid-result", "deep-json"])
def test_unsuccessful_calls_are_visible_in_cli_and_durable_record(prepared, monkeypatch, capsys, failure):
    state, _, source = prepared()
    def unsuccessful(argv, cwd, output, *args, **kwargs):
        output.mkdir()
        if failure != "timed_out":
            content = "[" * 10000 + "0" + "]" * 10000 if failure == "deep-json" else "{}"
            Path(argv[argv.index("--output-last-message") + 1]).write_text(content, encoding="utf-8")
        return {"status": "timed_out" if failure == "timed_out" else "succeeded", "returncode": 0}
    monkeypatch.setattr(processes, "run", unsuccessful)
    assert main(["--home", str(state.root), "composition", "run-input", "demo", str(source)]) == 1
    run = json.loads(capsys.readouterr().out)
    assert run["status"] == ("timed_out" if failure == "timed_out" else "failed")
    assert run == agent_runs.runs(State(state.root), "demo")[0] and run["finished"]
    if failure == "deep-json":
        assert "Invalid structured agent result" in run["error"] and "recursion" in run["error"].lower()


@pytest.mark.parametrize('case', ['success', 'missing', 'omitted', 'null-response', 'baseline', 'source',
                                  'lone-surrogate', 'identity-newline', 'source-newline',
                                  'oversize', 'oversize-prompt', 'resume-success', 'resume-blocked'])
def test_training_proposal_binds_its_original_flow_map_or_keeps_independent_design(
        prepared, tmp_path, monkeypatch, case):
    from ergora.agents import graphs

    state, _, _ = prepared()
    selected = workflows.install_preset(state, 'training-optimization')['root']
    definition = workflows.get(state, selected['id'], selected['version'])['definition']
    grant = {'schema_version': 1, 'permissions': definition['permissions'], 'limits': definition['limits']}
    manifest = tmp_path / 'proposal-manifest'
    frozen = workflows.prepare_manifest(state.root, selected['id'], selected['version'], grant, manifest)
    compiled = workflows.inspect_manifest(manifest, material=True)['composition']
    profile = next(node for node in compiled['instances'] if node['path'] == 'root/analysis/profile')
    prompt_bytes = len(profile['prompt'].encode('utf-8'))
    assert 4000 < prompt_bytes < 500000
    prompt_only_map_bytes = 500000 - prompt_bytes // 2
    destination = tmp_path / 'proposal-run'
    task = {'request': 'Map the exact trainer source and give a read-only proposal.',
            'baseline': {'raw_sha256': hashlib.sha256(b'fixed baseline').hexdigest()},
            'source': {'source_sha256': hashlib.sha256(b'fixed source').hexdigest()}}
    if case == 'identity-newline':
        task['baseline']['raw_sha256'] += '\n'
    if case == 'source-newline':
        task['source']['source_sha256'] += '\n'
    backend = tmp_path / 'proposal_backend.py'
    log = tmp_path / 'calls.jsonl'
    started = tmp_path / 'design-started'
    resume_design = tmp_path / 'resume-design'
    backend.write_text('''
from pathlib import Path
import json, sys, time

output, log, stage, case, started, resume, prompt_only_map_bytes = sys.argv[1:]
task = json.loads(sys.stdin.read().split('Workflow task port (JSON value):\\n')[-1])
with Path(log).open('a') as file:
    file.write(json.dumps({'stage': stage, 'task': task}) + '\\n')
value = {'summary': stage, 'artifacts': {'response': 'original '+stage+' result'}}
if stage == 'flow' and case in ('omitted', 'resume-blocked'):
    value['artifacts'] = {}
elif stage == 'flow' and case == 'null-response':
    value['artifacts']['response'] = None
elif stage == 'flow' and case != 'missing':
    flow_map = {'schema_version':1, 'kind':'training-flow-map', 'map':'train.py:1 loss -> backward',
                'baseline_sha256':task['baseline']['raw_sha256'],
                'source_sha256':task['source']['source_sha256']}
    if case in ('baseline', 'source'):
        flow_map[case+'_sha256'] = 'f' * 64
    if case == 'oversize':
        flow_map['map'] = 'x' * 510000
    if case == 'oversize-prompt':
        flow_map['map'] = 'x' * int(prompt_only_map_bytes)
    if case == 'lone-surrogate':
        flow_map['map'] = chr(0xd800)
    if case == 'success':
        flow_map['map'] = 'train.py:1 损失 → 梯度 🧪'
    value['artifacts']['response'] = json.dumps(flow_map)
elif stage == 'design':
    Path(started).touch()
    deadline = time.monotonic() + 6
    while not Path(resume).exists() and time.monotonic() < deadline:
        time.sleep(.02)
    if not Path(resume).exists():
        raise SystemExit(9)
elif stage == 'measurement':
    value['decision'] = 'request-changes'
Path(output).write_text(json.dumps(value))
''', encoding='utf-8')
    original_command = agent_backends.CodexBackend.command

    def command(adapter, request):
        argv, prompt = original_command(adapter, request)
        assert argv[argv.index('--sandbox') + 1] == 'read-only'
        stage = {'experiment-planner': 'design', 'kernel-tuner': 'kernel', 'reviewer': 'measurement'}.get(request.role)
        if stage is None:
            stage = 'flow' if 'Map the exact supplied training source before' in prompt else 'profile'
        return [sys.executable, str(backend), argv[argv.index('--output-last-message') + 1],
                str(log), stage, case, str(started), str(resume_design), str(prompt_only_map_bytes)], prompt

    monkeypatch.setattr(agent_backends.CodexBackend, 'command', command)
    monkeypatch.setattr(agent_backends.CodexBackend, 'check_invocation', lambda self: None)
    direct = not case.startswith('resume')
    reasons = {**dict.fromkeys(('missing', 'omitted', 'null-response', 'resume-blocked'), 'missing-flow-map'),
               'baseline': 'baseline-mismatch', 'source': 'source-mismatch',
               **dict.fromkeys(('lone-surrogate', 'identity-newline', 'source-newline'), 'invalid-flow-map'),
               **dict.fromkeys(('oversize', 'oversize-prompt'), 'oversize-flow-map')}
    reason = reasons.get(case)
    agent_task = graphs._GraphRun.agent_task
    record_block = graphs._GraphRun.record_flow_map_block
    blocked_while_design_running = []

    def task_after_original_design_starts(run, node, opened):
        if node['path'] == 'root/analysis/profile' and reason and not started.exists():
            import time

            until = time.monotonic() + 6
            while not started.exists() and time.monotonic() < until:
                time.sleep(.01)
            assert started.exists(), 'Independent design subprocess must have started before its sibling is blocked'
        return agent_task(run, node, opened)

    def unblock_independent_design(run, path, error, *, original=None):
        record_block(run, path, error, original=original)
        blocked_while_design_running.append(any(not future.done() and row['instance']=='root/analysis/design'
                                                for future, row in run.running.items()))
        resume_design.touch()

    if reason:
        monkeypatch.setattr(graphs._GraphRun, 'agent_task', task_after_original_design_starts)
        monkeypatch.setattr(graphs._GraphRun, 'record_flow_map_block', unblock_independent_design)
    else:
        resume_design.touch()

    if case == 'resume-success':
        structural = graphs._GraphRun.open_structure

        def stop_before_analysis(run, node, opened):
            if node['path'] == 'root/analysis':
                raise RuntimeError('Controlled coordinator loss before analysis')
            return structural(run, node, opened)

        with monkeypatch.context() as fault:
            fault.setattr(graphs._GraphRun, 'open_structure', stop_before_analysis)
            with pytest.raises(RuntimeError, match='coordinator loss'):
                graphs.run_graph(state, 'demo', manifest, frozen['digest'], {'task':task}, destination, 500000, 45,
                                 recoverable=True)
    if case == 'resume-blocked':
        save = graphs._GraphRun.save

        def stop_after_local_block(run):
            if run.receipt.get('flow_map_blocks'):
                while run.running:
                    run.wait_for_work()
                    run.collect_finished()
                save(run)
                raise RuntimeError('Controlled coordinator loss after the dependent block')
            save(run)

        with monkeypatch.context() as fault:
            fault.setattr(graphs._GraphRun, 'save', stop_after_local_block)
            with pytest.raises(RuntimeError, match='coordinator loss'):
                graphs.run_graph(state, 'demo', manifest, frozen['digest'], {'task':task}, destination, 500000, 45,
                                 recoverable=True)

    if direct:
        receipt = graphs.run_graph(state, 'demo', manifest, frozen['digest'], {'task':task}, destination, 500000, 45)
    else:
        original = json.loads((destination/'run.json').read_bytes())
        receipt = graphs.resume_graph(state.root, 'demo', destination, frozen['digest'])
        assert receipt['recovery_sha256'] == original['recovery_sha256']
        assert receipt['leaves'][:len(original['leaves'])] == original['leaves']

    observed = graphs.inspect_graph(state,'demo',destination,frozen['digest'])
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert [row['task'] for row in calls if row['stage'] == 'design'] == [task]
    assert sum(row['stage']=='flow' for row in calls)==1
    leaves = {row['instance']:row for row in receipt['leaves']}
    original_flow = {name: leaves['root/flow/map'][name]
                     for name in ('instance','run_id','input_digest','result_sha256')}
    assert leaves['root/analysis/design']['status']=='succeeded'
    protocol = state.root/'runs'/(original_flow['run_id']+'.protocol')
    native_schema = json.loads((protocol/'schema.json').read_bytes())
    artifact_schema = native_schema['properties']['artifacts']
    assert artifact_schema['required'] == ['response']
    assert artifact_schema['properties']['response']['type'] == ['string', 'null']
    if reason is None:
        assert receipt['status']=='succeeded'
        profile, = [row['task'] for row in calls if row['stage']=='profile']
        expected_map = 'train.py:1 损失 → 梯度 🧪' if case == 'success' else 'train.py:1 loss -> backward'
        assert profile['task']==task and profile['flow_map']['map']==expected_map
        assert profile['flow_map_producer']==original_flow
    else:
        assert receipt['status']=='failed' and 'outputs' not in receipt
        assert receipt['error']=='Required training FlowMap evidence blocked a dependent Agent'
        assert blocked_while_design_running[0]
        assert list(leaves)==['root/flow/map','root/analysis/design']
        expected = {'instance':'root/analysis/profile','reason':reason,'producer':original_flow}
        assert receipt['flow_map_blocks']==[expected]
        assert observed['flow_map_blocks']==[{**expected, 'reason_state':'corroborated'}]
        if case in ('lone-surrogate', 'identity-newline', 'source-newline'):
            raw = (state.root/'runs'/original_flow['run_id']/'result.json').read_bytes()
            assert hashlib.sha256(raw).hexdigest() == original_flow['result_sha256']
            original_map = json.loads(json.loads(raw)['artifacts']['response'])
            assert original_map['map'] == (chr(0xd800) if case == 'lone-surrogate' else 'train.py:1 loss -> backward')
            assert original_map['baseline_sha256'] == task['baseline']['raw_sha256']
            assert original_map['source_sha256'] == task['source']['source_sha256']
        if case == 'oversize-prompt':
            flow = agent_runs.inspect_run(state, 'demo', original_flow['run_id'])['result']['document']
            combined = {'task':task, 'flow_map':json.loads(flow['artifacts']['response']),
                        'flow_map_producer':original_flow}
            data = json.dumps(combined, ensure_ascii=False, separators=(',', ':')).encode()
            assert len(data) < 500000 < len(data) + prompt_bytes

    if case == 'missing':
        path = destination/'run.json'
        raw = path.read_bytes()
        changed = json.loads(raw)
        changed['flow_map_blocks'][0]['reason'] = 'source-mismatch'
        try:
            path.write_text(json.dumps(changed))
            with pytest.raises(ValueError, match='original producer evidence'):
                graphs.inspect_graph(state, 'demo', destination, frozen['digest'])
        finally:
            path.write_bytes(raw)
        artifact = state.root/'runs'/original_flow['run_id']/'result.json'
        hidden = artifact.with_suffix('.hidden')
        artifact.rename(hidden)
        try:
            limited = graphs.inspect_graph(state, 'demo', destination, frozen['digest'])
            assert limited['flow_map_blocks']==[{**expected, 'reason_state':'receipt-reported'}]
        finally:
            hidden.rename(artifact)

    if case in ('omitted', 'null-response'):
        producer = agent_runs.inspect_run(state, 'demo', original_flow['run_id'])
        actual_artifacts = {} if case == 'omitted' else {'response': None}
        assert producer['result']['document']['artifacts'] == actual_artifacts
        # The separately selected FlowMap root keeps its ordinary Agent result schema.
        independent = workflows.install_preset(state, 'training-flow-map')['root']
        separate = tmp_path/'standalone-map-manifest'
        pinned = workflows.prepare_manifest(state.root, independent['id'], independent['version'], grant, separate)
        failed = graphs.run_graph(state, 'demo', separate, pinned['digest'], {'task':task},
                                  tmp_path/'standalone-map-graph', 500000, 45)
        assert failed['status']=='failed'
        assert [row['status'] for row in failed['leaves']] == ['failed']
        assert 'flow_map_blocks' not in failed
        separate_run, = failed['leaves']
        separate_protocol = state.root/'runs'/(separate_run['run_id']+'.protocol')
        separate_schema = json.loads((separate_protocol/'schema.json').read_bytes())
        assert separate_schema['properties']['artifacts']['required'] == ['response']
        assert separate_schema['properties']['artifacts']['properties']['response']['type'] == 'string'


def test_freeze_rejects_unknown_required_flow_map_port(prepared):
    from copy import deepcopy

    state, _, _ = prepared()
    workflows.install_preset(state, 'training-optimization')
    original = workflows.get(state, 'ergora-training-analysis', '2.2.3')
    draft = deepcopy(original['definition'])
    draft['version'] = '2.2.4'
    next(node for node in draft['nodes'] if node['id'] == 'profile')['required_flow_map'] = 'misspelled'
    with pytest.raises(ValueError, match='Unknown required FlowMap input port'):
        workflows.revise(state, draft['id'], original['definition']['version'], original['digest'], draft,
                         publish=True)
