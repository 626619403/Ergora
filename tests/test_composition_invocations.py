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
