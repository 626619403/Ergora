import json
import os
import re
from pathlib import Path
import subprocess
import shutil
import hashlib
import sys
import time

import pytest

from ergora import agents, kernel, processes, projects, reference, tools
from ergora.state import State


def project(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    projects.create(state, "demo", repo)
    return state, repo


def binding():
    return {"tool": "command", "argv": [sys.executable, str(Path(__file__).parent / "fixtures/stage_agent.py")],
            "protocol": "stage-json-v1", "capabilities": agents.GENERAL_CAPABILITIES}


@pytest.mark.parametrize("kind", reference.TEMPLATES)
def test_template_roles_switch_actual_processes_without_template_edits(tmp_path, kind):
    state, repo = project(tmp_path)
    contract = reference.agent_contract(kind)
    before = json.dumps(contract, sort_keys=True)
    for role in contract["agents"]:
        first = binding()
        projects.bind(state, "demo", role, first, state.project("demo")["revision"])
        run = tools.run_agent(state, "demo", role, "Inspect the same repository", template=kind)
        assert run["status"] == "succeeded"
        result = json.loads(Path(run["result"]).read_text())
        assert set(result["artifacts"]) == set(contract["agents"][role]["artifacts"])
        second = {**first, "argv": [sys.executable, "-c", "import json,sys;r=json.load(sys.stdin);print(json.dumps({'summary':'second','artifacts':{k:'second '+k for k in r['result_schema']['properties']['artifacts']['required']},**({'decision':'approve'} if 'decision' in r['result_schema']['required'] else {})}))"]}
        projects.bind(state, "demo", role, second, state.project("demo")["revision"])
        other = tools.run_agent(state, "demo", role, "Inspect the same repository", template=kind)
        assert other["status"] == "succeeded"
        assert json.loads(Path(other["result"]).read_text())["summary"] == "second"
    assert json.dumps(reference.agent_contract(kind), sort_keys=True) == before
    assert not any(name in before.lower() for name in ("codex", "claude", "forgekernel", "/home/"))


def test_missing_capability_and_malformed_stage_result_are_visible(tmp_path):
    state, repo = project(tmp_path)
    with pytest.raises(ValueError, match="Unsupported|does not support"):
        projects.bind(state, "demo", "reviewer", {"tool": "mini-swe-agent", "model": "provider/model"}, 1)
    with pytest.raises(ValueError, match="lacks capabilities"):
        projects.bind(state, "demo", "planner", {**binding(), "capabilities": []}, 1)
    bad = {**binding(), "argv": [sys.executable, "-c", "print('{}')"]}
    projects.bind(state, "demo", "inspector", bad, 1)
    run = tools.run_agent(state, "demo", "inspector", "Inspect", template="repository-governance")
    assert run["status"] == "failed" and "structured" in run["error"]
    assert tools.runs(State(state.root), "demo")[0]["id"] == run["id"]


@pytest.mark.parametrize("tool", ["codex", "claude-code"])
@pytest.mark.parametrize("effort", [None, "low", "high"])
@pytest.mark.parametrize("mode", ["native", "text-only"])
@pytest.mark.skipif(os.name == "nt", reason="POSIX CLI shebang fixtures; Windows uses structured command fixtures")
def test_native_structured_output_normalization_uses_actual_process(tmp_path, monkeypatch, tool, effort, mode):
    programs = tmp_path / "bin"
    programs.mkdir()
    script = programs / ("codex" if tool == "codex" else "claude")
    script.write_text(f"#!{sys.executable}\nimport json,sys,pathlib\nargs=sys.argv\n" +
        "pathlib.Path('native-argv.json').write_text(json.dumps(args))\n" +
        ("schema=json.loads(pathlib.Path(args[args.index('--output-schema')+1]).read_text())\n" if tool == "codex" else
         "schema=json.loads(args[args.index('--json-schema')+1])\n") +
        "result={'summary':'native fixture','artifacts':{k:'evidence' for k in schema['properties']['artifacts']['required']},'decision':'approve'}\n" +
        ("pathlib.Path(args[args.index('--output-last-message')+1]).write_text(json.dumps(result))\nprint('{}')\n" if tool == "codex" else
         "print(json.dumps({'structured_output':result,'is_error':False}))\n"))
    script.chmod(0o700)
    monkeypatch.setenv("PATH", str(programs) + os.pathsep + os.environ["PATH"])
    selected = {"tool": tool}
    if effort is not None:
        selected["reasoning_effort" if tool == "codex" else "effort"] = effort
    result = agents.invoke(selected, "reviewer", "Review", tmp_path, tmp_path / "output", 5,
                           agents.result_schema(["review-report"], True), mode=mode)
    assert result["status"] == "succeeded"
    assert json.loads(Path(result["result"]).read_text())["decision"] == "approve"
    argv = json.loads((tmp_path / "native-argv.json").read_text())
    if tool == "codex":
        settings = dict(argv[i + 1].split("=", 1) for i, item in enumerate(argv) if item == "-c")
        assert settings.get("model_reasoning_effort") == (json.dumps(effort) if effort is not None else None)
    else:
        assert ("--effort" in argv) == (effort is not None)
        if effort is not None:
            assert argv[argv.index("--effort") + 1] == effort


@pytest.mark.parametrize("effort", [None, "high"])
def test_formal_codex_config_cannot_override_role_sandbox(tmp_path, monkeypatch, effort):
    config = tmp_path / "codex.toml"
    config.write_text('approval_policy = "never"\nsandbox_mode = "danger-full-access"\n'
                      'model = "config-model"\nmodel_reasoning_effort = "low"\n[sandbox_workspace_write]\nnetwork_access = true\n'
                      '[model_providers.fixture]\nbase_url = "https://example.invalid/v1"\n', encoding="utf-8")
    options = ["--skip-git-repo-check"]
    schema = agents.result_schema(["review-report"], True)

    def run(argv, cwd, output, timeout, stdin, env, **kwargs):
        assert argv[0] == "configured-codex" and stdin == "Review exact candidate"
        assert argv[argv.index("--sandbox") + 1] == "read-only"
        assert "--ignore-user-config" in argv and "--ignore-rules" in argv
        assert [argv[i + 1] for i, value in enumerate(argv) if value == "--disable"] == ["plugins", "apps"]
        settings = [argv[i + 1] for i, value in enumerate(argv) if value == "-c"]
        assert settings == ['model="config-model"', 'model_reasoning_effort=' + json.dumps(effort or "low"),
                            'model_providers.fixture.base_url="https://example.invalid/v1"']
        assert argv[argv.index("--model") + 1] == "binding-model"
        output.mkdir()
        Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(
            {"summary": "reviewed", "artifacts": {"review-report": "candidate evidence"}, "decision": "approve"}))
        return {"status": "succeeded", "returncode": 0}

    monkeypatch.setattr(processes, "run", run)
    selected = {"tool": "codex", "model": "binding-model"}
    if effort is not None:
        selected["reasoning_effort"] = effort
    result = agents.invoke(selected, "reviewer", "Review exact candidate",
                           tmp_path, tmp_path / "output", 5, schema, codex_bin="configured-codex",
                           codex_options=options, codex_config=config)
    assert result["status"] == "succeeded" and options == ["--skip-git-repo-check"]


@pytest.mark.parametrize("payload", [
    {"is_error": True, "subtype": "success", "structured_output": {
        "summary": "claim", "artifacts": {"review-report": "claim"}, "decision": "approve"}},
    {"is_error": False},
    {"is_error": False, "structured_output": {"summary": "incomplete"}},
])
def test_claude_exit_zero_is_insufficient_for_structured_acceptance(tmp_path, monkeypatch, payload):
    def run(argv, cwd, output, *args, **kwargs):
        output.mkdir()
        (output / "stdout.txt").write_text(json.dumps(payload), encoding="utf-8")
        return {"status": "succeeded", "returncode": 0}

    monkeypatch.setattr(processes, "run", run)
    result = agents.invoke({"tool": "claude-code"}, "reviewer", "Review", tmp_path,
                           tmp_path / "output", 5, agents.result_schema(["review-report"], True))
    assert result["status"] == "failed" and "Invalid structured agent result" in result["error"]
    assert not (tmp_path / "output/result.json").exists()


@pytest.mark.skipif(sys.platform != "linux", reason="mini-swe-agent driver requires Linux/bash")
def test_mini_invocation_keeps_selected_interpreter_and_request(tmp_path, monkeypatch):
    selected = {"tool": "mini-swe-agent", "model": "fixture/model", "python": "selected-python",
                "step_limit": 4, "cost_limit": 1}

    def run(argv, cwd, output, timeout, stdin, env, **kwargs):
        assert argv[0] == "selected-python" and Path(argv[1]).name == "mini.py" and stdin == ""
        request = json.loads(Path(argv[2]).read_text())
        assert request["binding"] == selected and request["cwd"] == str(tmp_path)
        assert request["timeout"] == timeout == 7 and request["prompt"] == "Implement"
        assert Path(request["trajectory"]).parent == Path(argv[2]).parent
        output.mkdir()
        (output / "stdout.txt").write_text('{"summary":"candidate","artifacts":{"change-summary":"evidence"}}')
        return {"status": "succeeded", "returncode": 0}

    monkeypatch.setattr(processes, "run", run)
    result = agents.invoke(selected, "implementer", "Implement", tmp_path, tmp_path / "output", 7,
                           agents.result_schema(["change-summary"]))
    assert result["status"] == "succeeded"


def test_forge_native_cpu_campaign_and_scope(tmp_path):
    checkout = os.environ.get("ERGORA_FORGE_TEST_CHECKOUT")
    python = os.environ.get("ERGORA_FORGE_TEST_PYTHON")
    if not checkout or not python:
        pytest.skip("Explicit fixed ForgeKernel checkout and Python required; no GPU/model calls")
    state, _ = project(tmp_path)
    forge = {"tool": "forgekernel", "checkout": checkout, "python": python,
             "task": str(Path(checkout) / "tasks/rmsnorm")}
    projects.bind(state, "demo", "kernel", forge, 1)
    plan = kernel.create(state, "demo", "plan")
    assert plan["status"] == "observed", plan
    assert "budget:" in plan["native"]["plan"]
    prepared = kernel.create(state, "demo", "prepare")
    assert prepared["status"] == "prepared", prepared
    assert prepared["native"]["native_record"]["status"] == "created"
    projects.bind(state, "demo", "kernel", {"tool": "manual"}, 2)
    observed = kernel.operate(State(state.root), "demo", prepared["id"], "status")
    assert observed["campaign"] == prepared["campaign"]
    assert observed["binding"] == forge
    assert observed["native"]["native_record"]["snapshot_sha256"] == prepared["native"]["native_record"]["snapshot_sha256"]
    projects.create(state, "other", Path(state.project("demo")["repo"]))
    with pytest.raises(ValueError, match="Unknown kernel"):
        kernel.operate(state, "other", prepared["id"], "status")
    snapshot = Path(prepared["campaign"]) / "task"
    # Find the actual snapshotted description independently of the upstream directory name.
    description = next(Path(prepared["campaign"]).glob("*/description.md"))
    description.write_text(description.read_text() + "\nchanged")
    failed = kernel.operate(state, "demo", prepared["id"], "status")
    assert failed["status"] == "failed"


@pytest.mark.parametrize("action", ["complete", "timeout", "empty"])
def test_real_mini_sdk_driver_and_action_cancellation(tmp_path, action):
    python = os.environ.get("ERGORA_MINI_TEST_PYTHON")
    if not python:
        pytest.skip("Explicit installed mini-swe-agent Python required; deterministic SDK fixture only")
    from ergora import processes
    driver = Path(agents.__file__).parent / "data/drivers/mini.py"
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"binding": {"model": "openai/gpt-4o-mini", "cost_limit": 3, "step_limit": 3},
        "prompt": "Exercise the real SDK without a remote model", "cwd": str(tmp_path),
        "timeout": 30, "trajectory": str(tmp_path / "trajectory.json")}))
    fixture = Path(__file__).parent / "fixtures/mini_acceptance.py"
    result = processes.run([python, str(fixture), str(driver), str(request), action], tmp_path,
                           tmp_path / "output", 8 if action == "timeout" else 15)
    if action == "complete":
        assert result["status"] == "succeeded", (tmp_path / "output/stderr.txt").read_text()
        agents.validate_result(json.loads((tmp_path / "output/stdout.txt").read_text()), agents.result_schema(["change-summary"]))
        assert (tmp_path / "candidate.txt").read_text() == "fixture candidate"
        trajectory = json.loads((tmp_path / "trajectory.json").read_text())
        assert trajectory["info"]["exit_status"] == "Submitted"
        assert trajectory["info"]["model_stats"]["api_calls"] == 2
        assert trajectory["info"]["config"]["model_type"].endswith("LitellmModel")
    elif action == "timeout":
        assert result["status"] == "timed_out"
        pid = int((tmp_path / "action-ready").read_text())
        time.sleep(0.1)
        stat = Path(f"/proc/{pid}/stat")
        assert not stat.exists() or stat.read_text().rsplit(")", 1)[1].split()[0] == "Z"
        assert not (tmp_path / "late.txt").exists()
    else:
        assert result["status"] == "failed"
        assert not (tmp_path / "output/stdout.txt").read_text().strip()


def test_forge_failed_observation_preserves_crash_reconciliation(tmp_path, monkeypatch):
    checkout, python = os.environ.get("ERGORA_FORGE_TEST_CHECKOUT"), os.environ.get("ERGORA_FORGE_TEST_PYTHON")
    if not checkout or not python:
        pytest.skip("Explicit pinned Forge installation required; CPU only")
    state, _ = project(tmp_path)
    projects.bind(state, "demo", "kernel", {"tool": "forgekernel", "checkout": checkout, "python": python,
        "task": str(Path(checkout) / "tasks/rmsnorm")}, 1)
    prepared = kernel.create(state, "demo", "prepare")
    assert prepared["status"] == "prepared"
    prepared.update(status="running", last_action="run")
    kernel._store(state, "demo", prepared)
    monkeypatch.setenv("FK_DELIVERY", "invalid-for-probe")
    failed = kernel.operate(state, "demo", prepared["id"], "status")
    assert failed["status"] == "failed"
    assert failed["requires_reconciliation"] is True
    monkeypatch.delenv("FK_DELIVERY")
    with pytest.raises(ValueError, match="reconcile reason"):
        kernel.operate(State(state.root), "demo", prepared["id"], "run")


@pytest.mark.parametrize("relative", ["scripts/timeout-run.py", "src/forgekernel/ergora_untracked.py"])
def test_forge_runtime_source_drift_blocks_doctor_and_prepare(tmp_path, monkeypatch, relative):
    source, python = os.environ.get("ERGORA_FORGE_TEST_CHECKOUT"), os.environ.get("ERGORA_FORGE_TEST_PYTHON")
    if not source or not python:
        pytest.skip("Explicit pinned Forge installation required; CPU only")
    checkout = tmp_path / "forge-source"
    subprocess.run(["git", "clone", "--shared", source, str(checkout)], check=True, capture_output=True)
    monkeypatch.setenv("PYTHONPATH", str(checkout / "src"))
    state, _ = project(tmp_path)
    binding = {"tool": "forgekernel", "checkout": str(checkout), "python": python,
               "task": str(checkout / "tasks/rmsnorm")}
    projects.bind(state, "demo", "kernel", binding, 1)
    assert kernel.available(binding)["version"] == "pinned"
    path = checkout / relative
    with path.open("a") as stream:
        stream.write("\n# source identity regression; never executed\n")
    check = next(item for item in tools.doctor(state, "demo")["checks"] if item["layer"] == "kernel")
    assert check["version"] == "unsupported" and check["task_availability"] == "blocked"
    assert check["installed"] and not check["source_clean"]
    refused = kernel.create(state, "demo", "prepare")
    assert refused["status"] == "failed" and "execution scripts" in refused["error"]
    assert "operations" not in refused and "campaign" not in refused
    assert not (state.root / "kernel" / refused["id"] / "native").exists()


def test_forge_config_drift_and_cuda_candidate_identity(tmp_path, monkeypatch):
    source, python = os.environ.get("ERGORA_FORGE_TEST_CHECKOUT"), os.environ.get("ERGORA_FORGE_TEST_PYTHON")
    if not source or not python:
        pytest.skip("Explicit pinned Forge installation required; CPU only")
    checkout = tmp_path / "forge-source"
    subprocess.run(["git", "clone", "--shared", source, str(checkout)], check=True, capture_output=True)
    monkeypatch.setenv("PYTHONPATH", str(checkout / "src"))
    state, _ = project(tmp_path)
    task = tmp_path / "cuda-task"
    shutil.copytree(checkout / "tasks/rmsnorm", task)
    config = task / "task.toml"
    config.write_text(config.read_text().replace('language = "cutedsl"', 'language = "cuda"'))
    projects.bind(state, "demo", "kernel", {"tool": "forgekernel", "checkout": str(checkout), "python": python, "task": str(task)}, 1)
    prepared = kernel.create(state, "demo", "prepare")
    assert prepared["status"] == "prepared", prepared
    campaign = Path(prepared["campaign"])
    best = campaign / "best/kernel.cu"
    best.parent.mkdir()
    best.write_text("// CPU identity fixture, never compiled or executed\n")
    (campaign / "report.md").write_text("CPU candidate fixture only\n")
    observed = kernel.operate(state, "demo", prepared["id"], "status")
    assert observed["status"] == "observed", observed
    assert observed["native"]["artifacts"]["best/kernel.cu"]["sha256"] == hashlib.sha256(best.read_bytes()).hexdigest()
    for name in ("models.toml", "loop.toml"):
        defaults = checkout / "global_config" / name
        original = defaults.read_text()
        changed = original.replace("claude-opus-5-5", "changed-model-id") if name == "models.toml" else re.sub(r"(?m)^(hours\s*=\s*)[0-9.]+", r"\g<1>40", original)
        assert changed != original
        defaults.write_text(changed)
        refused = kernel.operate(state, "demo", prepared["id"], "status")
        assert refused["status"] == "failed"
        assert "frozen campaign identity" in refused["operations"][-1]["stderr_preview"]
        defaults.write_text(original)
        assert kernel.operate(state, "demo", prepared["id"], "status")["status"] == "observed"


@pytest.fixture
def native_session_case(tmp_path, monkeypatch):
    from ergora import agent_runs
    state, repo = project(tmp_path)
    programs = tmp_path / 'session-bin'
    programs.mkdir()
    script = programs / 'codex'
    script.write_text(f'#!{sys.executable}\n' + r'''
import json, os, pathlib, subprocess, sys, time, uuid
args = sys.argv[1:]
if args == ['--version']:
    print('codex-cli 0.167.1-fixture')
    raise SystemExit(0)
prompt = sys.stdin.read()
home = pathlib.Path(os.environ['CODEX_HOME'])
saved = home / 'thread.json'
if 'resume' in args:
    native = json.loads(saved.read_text())
    assert args[args.index('resume') + 1] == native['id']
else:
    assert not saved.exists()
    native = {'id': str(uuid.uuid4()), 'turns': 0, 'nonce': 'fixture-original'}
native['turns'] += 1
saved.write_text(json.dumps(native))
repo = pathlib.Path.cwd()
with (repo / 'native-calls.jsonl').open('a') as stream:
    stream.write(json.dumps({'argv': args, 'home': str(home), 'id': native['id'], 'prompt': prompt}) + '\n')
print(json.dumps({'type': 'thread.started', 'thread_id': native['id']}), flush=True)
if prompt.startswith('SLEEP'):
    code = 'import time;time.sleep(40)'
    child = subprocess.Popen([sys.executable, '-c', code], start_new_session=True)
    (repo / 'escape-pid').write_text(str(child.pid))
    (repo / 'native-ready').touch()
    time.sleep(40)
if prompt.startswith('PAUSE'):
    time.sleep(.4)
(repo / ('turn-' + str(native['turns']) + '.txt')).write_text(prompt)
result_path = pathlib.Path(args[args.index('--output-last-message') + 1])
if '--output-schema' in args:
    schema = json.loads(pathlib.Path(args[args.index('--output-schema') + 1]).read_text())
    result = {'summary': native['nonce'], 'artifacts': {k: 'fixture evidence' for k in schema['properties']['artifacts']['required']}}
    if 'decision' in schema['required']:
        result['decision'] = 'approve'
    result_path.write_text(json.dumps(result))
else:
    result_path.write_text(native['nonce'] + ' turn ' + str(native['turns']))
print(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 1, 'output_tokens': 1}}), flush=True)
''')
    script.chmod(0o700)
    monkeypatch.setenv('PATH', str(programs) + os.pathsep + os.environ['PATH'])
    selected = {'tool': 'codex', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'xhigh'}
    projects.bind(state, 'demo', 'implementer', selected, state.project('demo')['revision'])
    config = tmp_path / 'session.toml'
    config.write_text('model = "gpt-6.1-sol"\nmodel_reasoning_effort = "xhigh"\n')
    return state, repo, config, agent_runs


def test_native_development_session_restores_exact_uuid_across_application_processes(native_session_case):
    state, repo, config, runs = native_session_case
    revision = state.project('demo')['revision']
    first = runs.run_agent(state, 'demo', 'implementer', 'first change', timeout=10,
                           session_intent='development', expected_revision=revision, codex_config=config)
    assert first['status'] == 'succeeded', first
    assert first['execution_stopped'] is True and first['formal_execution_authorized'] is False
    assert (repo / 'turn-1.txt').read_text() == 'first change'
    assert runs.sessions(state, 'demo')['sessions'][0]['sandbox'] == 'workspace-write'
    request = {'home': str(state.root), 'session': first['id'], 'parent': first['id'], 'revision': revision}
    code = ('import json,sys;from pathlib import Path;from ergora import agent_runs;from ergora.state import State;'
            'q=json.loads(sys.argv[1]);r=agent_runs.continue_session(State(Path(q["home"])),"demo",q["session"],q["parent"],'
            '"second change",expected_revision=q["revision"],intent_id="second",timeout=10);print(json.dumps(r))')
    fresh = subprocess.run([sys.executable, '-c', code, json.dumps(request)], capture_output=True, text=True, timeout=20)
    assert fresh.returncode == 0, fresh.stderr
    second = json.loads(fresh.stdout)
    assert second['status'] == 'succeeded', second
    third = runs.continue_session(State(state.root), 'demo', first['id'], second['id'], 'third change',
                                  expected_revision=revision, intent_id='third', timeout=10)
    assert third['status'] == 'succeeded', third
    calls = [json.loads(line) for line in (repo / 'native-calls.jsonl').read_text().splitlines()]
    assert len(calls) == 3 and len({call['id'] for call in calls}) == 1 and len({call['home'] for call in calls}) == 1
    assert '--ephemeral' not in calls[0]['argv'] and calls[0]['argv'][calls[0]['argv'].index('--sandbox') + 1] == 'workspace-write'
    assert calls[1]['argv'][calls[1]['argv'].index('resume') + 1] == first['native_session']['id']
    assert Path(third['result']).read_text() == 'fixture-original turn 3'
    observed = runs.inspect_session(state, 'demo', first['id'])
    assert observed['can_continue'] and [t['session']['ordinal'] for t in observed['turns']] == [0, 1, 2]
    precise = runs.sessions(state, 'demo', intent_id='development')['sessions']
    assert len(precise) == 1 and precise[0]['birth_intent'] == 'development' and precise[0]['id'] == first['id']
    assert runs.sessions(state, 'demo', intent_id='not-recorded')['sessions'] == []
    assert runs.run_agent(state, 'demo', 'implementer', 'first change', timeout=10,
                          session_intent='development', expected_revision=revision, codex_config=config)['id'] == first['id']
    assert runs.continue_session(state, 'demo', first['id'], second['id'], 'third change',
                                  expected_revision=revision, intent_id='third', timeout=10)['id'] == third['id']
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 3


def test_session_keeps_template_context_and_configuration_after_source_changes(native_session_case):
    state, repo, config, runs = native_session_case
    first = runs.run_agent(state, 'demo', 'implementer', 'first', timeout=10, template='repository-governance',
                          session_intent='template', expected_revision=state.project('demo')['revision'], codex_config=config)
    assert first['status'] == 'succeeded', first
    config.write_text('model = "different-model"\nmodel_reasoning_effort = "low"\n')
    second = runs.continue_session(state, 'demo', first['id'], first['id'], 'second',
                                  expected_revision=state.project('demo')['revision'], intent_id='second', timeout=10)
    assert second['status'] == 'succeeded' and second['binding']['model'] == 'gpt-6.1-sol'
    assert json.loads(Path(second['result']).read_text())['summary'] == 'fixture-original'
    calls = [json.loads(line) for line in (repo / 'native-calls.jsonl').read_text().splitlines()]
    assert 'Template role requirements' in calls[0]['prompt'] and 'Template role requirements' in calls[1]['prompt']
    assert calls[1]['argv'][calls[1]['argv'].index('--model') + 1] == 'gpt-6.1-sol'
    assert all('different-model' not in argument for argument in calls[1]['argv'])


def test_session_rejects_stale_parent_cross_project_and_changed_authority(native_session_case):
    state, repo, config, runs = native_session_case
    revision = state.project('demo')['revision']
    first = runs.run_agent(state, 'demo', 'implementer', 'first', timeout=10,
                          session_intent='authority', expected_revision=revision, codex_config=config)
    assert first['status'] == 'succeeded', first
    projects.create(state, 'other-session-project', repo)
    with pytest.raises(ValueError, match='Unknown session'):
        runs.inspect_session(state, 'other-session-project', first['id'])
    second = runs.continue_session(state, 'demo', first['id'], first['id'], 'second',
                                  expected_revision=revision, intent_id='second', timeout=10)
    with pytest.raises(ValueError, match='latest stopped'):
        runs.continue_session(state, 'demo', first['id'], first['id'], 'stale',
                              expected_revision=revision, intent_id='stale')
    projects.bind(state, 'demo', 'implementer', {'tool': 'codex', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'high'}, revision)
    with pytest.raises(ValueError, match='revision'):
        runs.continue_session(state, 'demo', first['id'], second['id'], 'changed authority',
                              expected_revision=revision, intent_id='drift')
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 2
    assert runs.inspect_session(state, 'demo', first['id'])['can_continue'] is False


def test_session_concurrent_parent_has_one_real_effect(native_session_case):
    from concurrent.futures import ThreadPoolExecutor
    state, repo, config, runs = native_session_case
    revision = state.project('demo')['revision']
    first = runs.run_agent(state, 'demo', 'implementer', 'first', timeout=10,
                          session_intent='concurrent', expected_revision=revision, codex_config=config)
    def call(intent):
        try:
            return runs.continue_session(State(state.root), 'demo', first['id'], first['id'], 'PAUSE next',
                                          expected_revision=revision, intent_id=intent, timeout=10)
        except (ValueError, BlockingIOError) as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(call, ['one', 'two']))
    assert sum(isinstance(value, dict) and value['status'] == 'succeeded' for value in outcomes) == 1, outcomes
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 2


def test_session_missing_final_is_unknown_and_never_replays(native_session_case):
    state, repo, config, runs = native_session_case
    revision = state.project('demo')['revision']
    first = runs.run_agent(state, 'demo', 'implementer', 'first', timeout=10,
                          session_intent='unknown', expected_revision=revision, codex_config=config)
    final = state.root / 'runs' / (first['id'] + '.session-turn') / 'final'
    final.rename(final.with_name('saved-final'))
    observed = runs.inspect_session(state, 'demo', first['id'])
    assert observed['status'] == 'unknown' and observed['can_continue'] is False
    again = runs.run_agent(state, 'demo', 'implementer', 'first', timeout=10,
                           session_intent='unknown', expected_revision=revision, codex_config=config)
    assert again['status'] == 'unknown'
    with pytest.raises(ValueError, match='latest stopped'):
        runs.continue_session(state, 'demo', first['id'], first['id'], 'not authorized replay',
                              expected_revision=revision, intent_id='new')
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1


def test_session_reservation_survives_attempt_publication_failure_without_dispatch(native_session_case, monkeypatch):
    state, repo, config, runs = native_session_case
    publish = runs._publish_session_packet
    def fail_attempt(path, values):
        if path.name == 'attempt':
            raise OSError('fixture attempt fsync failure')
        return publish(path, values)
    monkeypatch.setattr(runs, '_publish_session_packet', fail_attempt)
    with pytest.raises(OSError, match='fsync'):
        runs.run_agent(state, 'demo', 'implementer', 'first', timeout=10,
                       session_intent='reserved', expected_revision=state.project('demo')['revision'], codex_config=config)
    again = runs.run_agent(state, 'demo', 'implementer', 'first', timeout=10,
                           session_intent='reserved', expected_revision=state.project('demo')['revision'], codex_config=config)
    assert again['status'] == 'unknown' and not (repo / 'native-calls.jsonl').exists()


@pytest.mark.parametrize('end', ['deadline', 'stop'])
def test_session_original_reaper_stops_escape_child_and_does_not_reopen_turn(native_session_case, end):
    from concurrent.futures import ThreadPoolExecutor
    state, repo, config, runs = native_session_case
    revision = state.project('demo')['revision']
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(runs.run_agent, state, 'demo', 'implementer', 'SLEEP original turn', 1 if end == 'deadline' else 10,
                             session_intent='cleanup', expected_revision=revision, codex_config=config)
        limit = time.monotonic() + 10
        while not (repo / 'native-ready').exists() and not future.done() and time.monotonic() < limit:
            time.sleep(.02)
        assert (repo / 'native-ready').exists()
        if end == 'stop':
            session = runs.sessions(State(state.root), 'demo')['sessions'][0]
            stopped = runs.stop_session(State(state.root), 'demo', session['id'], session['latest_run'], intent_id='explicit-stop')
            assert stopped['stop_requested']
            assert stopped['run']['stop_request']['intent_id'] == 'explicit-stop'
        result = future.result(timeout=15)
    assert result['status'] in ('timed_out', 'cancelled'), result
    assert result['execution_stopped'] is True
    escaped = int((repo / 'escape-pid').read_text())
    assert not Path('/proc', str(escaped)).exists(), 'The original subreaper must reap even a new-session child'
    again = runs.run_agent(state, 'demo', 'implementer', 'SLEEP original turn', 1 if end == 'deadline' else 10,
                           session_intent='cleanup', expected_revision=revision, codex_config=config)
    assert again['id'] == result['id'] and len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    continued = runs.continue_session(state, 'demo', result['session']['id'], result['id'], 'new explicit work',
                                      expected_revision=revision, intent_id='after-stop', timeout=10)
    assert continued['status'] == 'succeeded', continued
    assert continued['native_session']['id'] == result['native_session']['id']
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 2


def test_session_prebirth_rejection_is_distinct_from_consumed_attempt_failure(native_session_case, monkeypatch):
    state, repo, config, runs = native_session_case
    revision = state.project('demo')['revision']
    with pytest.raises(runs.SessionRejected) as rejected:
        runs.run_agent(state, 'demo', 'implementer', 'bad\0prompt', session_intent='rejected',
                       expected_revision=revision, codex_config=config)
    assert rejected.value.intent_id == 'rejected' and runs.sessions(state, 'demo', intent_id='rejected')['sessions'] == []
    original = subprocess.Popen
    def refuse_helper(argv, *args, **kwargs):
        if len(argv) > 2 and argv[1] == '-c' and 'session_main' in argv[2]:
            raise OSError('fixture helper creation failed after durable attempt')
        return original(argv, *args, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', refuse_helper)
    attempted = runs.run_agent(state, 'demo', 'implementer', 'no effect', session_intent='consumed-popen',
                               expected_revision=revision, codex_config=config)
    assert attempted['status'] == 'failed' and attempted['execution_stopped'] is True
    assert (state.root / 'runs' / (attempted['id'] + '.session-turn') / 'attempt').is_dir()
    assert not (repo / 'native-calls.jsonl').exists()
    assert runs.run_agent(state, 'demo', 'implementer', 'no effect', session_intent='consumed-popen',
                          expected_revision=revision, codex_config=config)['id'] == attempted['id']


def test_session_skill_context_is_frozen_internally_and_complete_result_is_readable(native_session_case):
    from ergora import skills
    state, repo, config, runs = native_session_case
    skill = repo.parent / 'session-evidence'
    skill.mkdir()
    (skill / 'SKILL.md').write_text('---\nname: session-evidence\ndescription: frozen selected evidence\n---\nORIGINAL RESOURCE\n')
    (skill / 'attachment.txt').write_text('complete attachment bytes')
    imported = skills.import_bundle(state, 'demo', skill)
    first = runs.run_agent(state, 'demo', 'implementer', 'first', 10, ['session-evidence'],
                          session_intent='resource', expected_revision=state.project('demo')['revision'], codex_config=config)
    assert first['status'] == 'succeeded', first
    actual = skills.get(state, 'demo', imported['digest'])
    Path(actual['path'], 'SKILL.md').write_text('CURRENT SOURCE CHANGED')
    second = runs.continue_session(state, 'demo', first['id'], first['id'], 'second',
                                  expected_revision=state.project('demo')['revision'], intent_id='second', timeout=10)
    assert second['status'] == 'succeeded', second
    calls = [json.loads(line) for line in (repo / 'native-calls.jsonl').read_text().splitlines()]
    assert all('ORIGINAL RESOURCE' in call['prompt'] and 'CURRENT SOURCE CHANGED' not in call['prompt'] for call in calls)
    context = state.root / 'runs' / (first['id'] + '.session') / 'context'
    assert (context / 'skills/session-evidence/attachment.txt').read_text() == 'complete attachment bytes'
    observed = runs.output(state, 'demo', second['id'])['result']
    assert observed['available'] and observed['text'] == 'fixture-original turn 2'
    assert observed['sha256'] == second['result_sha256']


def test_session_result_fsync_failure_keeps_stopped_execution_and_unknown_outcome(native_session_case, monkeypatch):
    state, repo, config, runs = native_session_case
    original = subprocess.Popen
    code = '''import os
from ergora.agent_runs import session_main
real = os.fsync
def fail_result(descriptor):
    if os.readlink('/proc/self/fd/' + str(descriptor)).endswith('/result.txt'):
        raise OSError('fixture result fsync failure')
    return real(descriptor)
os.fsync = fail_result
session_main()
'''
    def inject_in_helper(argv, *args, **kwargs):
        if len(argv) > 2 and argv[1] == '-c' and 'session_main' in argv[2]:
            argv = [*argv[:2], code, *argv[3:]]
        return original(argv, *args, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', inject_in_helper)
    result = runs.run_agent(state, 'demo', 'implementer', 'one effect', 10,
                           session_intent='result-fsync', expected_revision=state.project('demo')['revision'], codex_config=config)
    assert result['status'] == 'unknown' and result['execution_stopped'] is True
    assert 'durable confirmation' in result['error'] and (repo / 'turn-1.txt').exists()
    observed = runs.inspect_session(state, 'demo', result['session']['id'])
    assert observed['can_continue'] is False and 'fsync' in observed['reason']
    again = runs.run_agent(state, 'demo', 'implementer', 'one effect', 10,
                          session_intent='result-fsync', expected_revision=state.project('demo')['revision'], codex_config=config)
    assert again['id'] == result['id'] and len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    with pytest.raises(ValueError, match='unknown parents'):
        runs.continue_session(state, 'demo', result['session']['id'], result['id'], 'do not repeat the unknown effect',
                              expected_revision=state.project('demo')['revision'], intent_id='blocked')
