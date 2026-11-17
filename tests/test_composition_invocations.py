"""Independent leaf calls bind complete input and explicit native tool restrictions."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import agent_backends, agent_definitions, agent_runs, agents, processes, projects, workflow_definitions as workflows
from ergora.cli import main
from ergora.state import State


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


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


@pytest.mark.parametrize("floor,effort", [("medium", "medium"), ("high", "xhigh"), ("xhigh", "max"), ("max", "ultra")])
def test_explicit_minimum_reaches_native_command_without_replacing_provider(prepared, tmp_path, monkeypatch, floor, effort):
    requested = {"tool": "codex", "model": "gpt-6.1-sol", "reasoning_effort": floor}
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
    {"tool": "codex", "model": "gpt-6-sol", "reasoning_effort": "ultra"},
    {"tool": "codex", "model": "gpt-6.1-sol"},
    {"tool": "codex", "model": "gpt-6.1-sol", "reasoning_effort": "medium"},
    {"tool": "claude-code", "model": "gpt-6.1-sol", "effort": "high"},
])
def test_actual_binding_below_minimum_is_rejected_before_run(prepared, monkeypatch, binding):
    requested = {"tool": "codex", "model": "gpt-6.1-sol", "reasoning_effort": "high"}
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
