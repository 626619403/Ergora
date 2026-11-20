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

import ergora.native.resources as native_resources
import ergora.agents.invocation as agents
import ergora.improvement.kernel as kernel
import ergora.configuration.projects as projects
import ergora.operations.tools as tools
import ergora.agents.runs as agent_runs
from ergora.runtime import processes
from ergora.storage.state import State
from ergora._paths import DATA_ROOT


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


@pytest.mark.skipif(sys.platform != 'linux', reason='Original supervised Linux subtree owner')
@pytest.mark.parametrize('stop', [False, True])
def test_parent_analysis_monitor_and_original_reaper_record_actual_model_and_escaped_child(tmp_path, stop):
    model = tmp_path / 'model.py'
    model.write_text("import json,pathlib,subprocess,sys,time\n"
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)\n"
        "pathlib.Path('escaped-pid').write_text(str(child.pid))\n"
        "print(json.dumps({'summary':'controlled model','artifacts':{'response':'actual process tree'}}),flush=True)\n"
        + ('time.sleep(60)\n' if stop else ''))
    worker = r'''
import json,os,sys,time
from pathlib import Path
import ergora.agents.invocation as agents
from ergora.runtime import processes
root=Path(sys.argv[1]);started=time.monotonic()
binding={'tool':'command','argv':[sys.executable,str(root/'model.py')],
         'protocol':'stage-json-v1','capabilities':agents.GENERAL_CAPABILITIES}
try:
    result=agents.invoke(binding,'inspector','fixed packet',root,root/'output',30,
        agents.result_schema(['response']),supervised=True,record_lifecycle=True,
        stop_requested=lambda:sys.argv[2]=='True' and time.monotonic()-started>.3)
    print(json.dumps(result))
finally:
    processes._reap_children()
'''
    completed = subprocess.run([sys.executable, '-c', worker, str(tmp_path), str(stop)],
                               capture_output=True, text=True, timeout=10)
    assert completed.returncode == 0, completed.stderr
    observed = json.loads(completed.stdout)
    cleanup = json.loads((tmp_path / 'output/process-cleanup.json').read_bytes())
    escaped = int((tmp_path / 'escaped-pid').read_text())
    assert observed['status'] == ('cancelled' if stop else 'succeeded')
    assert cleanup['owner']['pid'] != os.getpid() and cleanup['model']['pid'] != cleanup['owner']['pid']
    assert cleanup['model_waited'] is True and cleanup['remaining_children'] == []
    child = next(value for value in cleanup['descendants'] if value['process']['pid'] == escaped)
    assert child['wait_pid'] == escaped and type(child['wait_status']) is int
    assert not Path('/proc/' + str(escaped)).exists()


def test_parent_stop_at_final_command_boundary_prevents_native_spawn(tmp_path, monkeypatch):
    checks = []

    def stopped():
        checks.append(True)
        return True

    monkeypatch.setattr(processes, 'run', lambda *a, **k: pytest.fail('Stopped analysis must not spawn'))
    result = agents.invoke(binding(), 'inspector', 'packet', tmp_path, tmp_path / 'output', 10,
                           agents.result_schema(['response']), stop_requested=stopped)
    assert result['status'] == 'cancelled' and checks and not (tmp_path / 'output').exists()


@pytest.mark.parametrize("kind", native_resources.TEMPLATES)
def test_template_roles_switch_actual_processes_without_template_edits(tmp_path, kind):
    state, repo = project(tmp_path)
    contract = native_resources.agent_contract(kind)
    before = json.dumps(contract, sort_keys=True)
    for role in contract["agents"]:
        first = binding()
        projects.bind(state, "demo", role, first, state.project("demo")["revision"])
        run = agent_runs.run_agent(state, "demo", role, "Inspect the same repository", template=kind)
        assert run["status"] == "succeeded"
        result = json.loads(Path(run["result"]).read_text())
        assert set(result["artifacts"]) == set(contract["agents"][role]["artifacts"])
        second = {**first, "argv": [sys.executable, "-c", "import json,sys;r=json.load(sys.stdin);print(json.dumps({'summary':'second','artifacts':{k:'second '+k for k in r['result_schema']['properties']['artifacts']['required']},**({'decision':'approve'} if 'decision' in r['result_schema']['required'] else {})}))"]}
        projects.bind(state, "demo", role, second, state.project("demo")["revision"])
        other = agent_runs.run_agent(state, "demo", role, "Inspect the same repository", template=kind)
        assert other["status"] == "succeeded"
        assert json.loads(Path(other["result"]).read_text())["summary"] == "second"
    assert json.dumps(native_resources.agent_contract(kind), sort_keys=True) == before
    assert not any(name in before.lower() for name in ("codex", "claude", "forgekernel", "/home/"))


def test_missing_capability_and_malformed_stage_result_are_visible(tmp_path):
    state, repo = project(tmp_path)
    with pytest.raises(ValueError, match="Unsupported|does not support"):
        projects.bind(state, "demo", "reviewer", {"tool": "mini-swe-agent", "model": "provider/model"}, 1)
    with pytest.raises(ValueError, match="lacks capabilities"):
        projects.bind(state, "demo", "planner", {**binding(), "capabilities": []}, 1)
    bad = {**binding(), "argv": [sys.executable, "-c", "print('{}')"]}
    projects.bind(state, "demo", "inspector", bad, 1)
    run = agent_runs.run_agent(state, "demo", "inspector", "Inspect", template="repository-governance")
    assert run["status"] == "failed" and "structured" in run["error"]
    assert agent_runs.runs(State(state.root), "demo")[0]["id"] == run["id"]


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


@pytest.fixture
def codex_schema_process(tmp_path):
    """A native-process substitute with the observed provider's reference restriction."""
    def create(payload):
        script = tmp_path / "codex-schema"
        script.write_text(f"#!{sys.executable}\n" +
            "import json,pathlib,sys\nfrom jsonschema import Draft202012Validator\n" +
            "args=sys.argv\n" +
            "schema=json.loads(pathlib.Path(args[args.index('--output-schema')+1]).read_text())\n" +
            "bounded=schema['properties'].get('bounded', {})\n" +
            "if '$ref' in bounded and 'minItems' in bounded:\n" +
            "    print('invalid_json_schema: $ref cannot have sibling minItems', file=sys.stderr)\n" +
            "    raise SystemExit(31)\n" +
            f"payload=json.loads({json.dumps(payload)!r})\n" +
            "pathlib.Path('transport-valid.json').write_text(json.dumps(Draft202012Validator(schema).is_valid(payload)))\n" +
            "pathlib.Path('transport-schema.json').write_text(json.dumps(schema))\n" +
            "pathlib.Path(args[args.index('--output-last-message')+1]).write_text(json.dumps(payload))\n" +
            "print('{}')\n")
        script.chmod(0o700)
        return str(script)
    return create


@pytest.mark.parametrize("case,target_minimum,accepted", [
    ("valid", 0, True), ("minimum", 0, True), ("maximum", 0, True),
    ("empty", 0, False), ("duplicate", 0, False),
    ("overflow", 0, False), ("wrong-item", 0, False),
    ("extra-property", 0, False), ("missing-property", 0, False),
    ("wrong-literal", 0, False), ("wrong-enum", 0, False),
    ("stronger-target", 2, False), ("valid", 2, True),
])
@pytest.mark.skipif(os.name == "nt", reason="POSIX native CLI substitute; no provider calls")
def test_codex_array_reference_contract_survives_native_transport(tmp_path, codex_schema_process,
                                                                  case, target_minimum, accepted):
    maximum = 3
    schema = {"type": "object", "additionalProperties": False,
        "required": ["bounded", "shared", "details", "literal", "literal_enum"],
        "properties": {
            "bounded": {"$ref": "#/$defs/ids~1bounded~0", "minItems": 1},
            "shared": {"$ref": "#/$defs/ids~1bounded~0"},
            "details": {"type": "object", "properties": {"owner": {"type": "string"}},
                        "required": ["owner"], "additionalProperties": False},
            "literal": {"const": {"$ref": "data, not a schema reference", "minItems": 0}},
            "literal_enum": {"enum": [{"$ref": "enum data", "minItems": 0}]}},
        "$defs": {
            "ids/bounded~": {"type": "array", "minItems": target_minimum, "maxItems": maximum,
                             "items": {"$ref": "#/$defs/id"}, "uniqueItems": True},
            "id": {"type": "string", "pattern": "^[a-z]+$"}}}
    original = json.dumps(schema)
    payload = {"bounded": ["a", "b"], "shared": ["a", "b"] if target_minimum else [],
               "details": {"owner": "owner"}, "literal": schema["properties"]["literal"]["const"],
               "literal_enum": schema["properties"]["literal_enum"]["enum"][0]}
    if case == "minimum":
        payload["bounded"] = ["a"]
    elif case == "maximum":
        payload["bounded"] = list("abcdef"[:maximum])
    elif case == "empty":
        payload["bounded"] = []
    elif case == "duplicate":
        payload["bounded"] = ["a", "a"]
    elif case == "overflow":
        payload["bounded"] = list("abcdef"[:maximum + 1])
    elif case == "wrong-item":
        payload["bounded"] = ["invalid ID"]
    elif case == "extra-property":
        payload["details"]["extra"] = "forbidden"
    elif case == "missing-property":
        del payload["details"]["owner"]
    elif case == "wrong-literal":
        payload["literal"] = {"$ref": "different data", "minItems": 0}
    elif case == "wrong-enum":
        payload["literal_enum"] = {"$ref": "different data", "minItems": 0}
    elif case == "stronger-target":
        payload["bounded"] = ["a"]
    result = agents.invoke({"tool": "codex"}, "planner", "Return the supplied contract", tmp_path,
                           tmp_path / "output", 5, schema, codex_bin=codex_schema_process(payload))
    assert result["status"] == ("succeeded" if accepted else "failed"), result
    assert json.loads((tmp_path / "transport-valid.json").read_text()) is accepted
    assert json.dumps(schema) == original
    assert (tmp_path / "output.protocol/schema.json").read_text() == original
    if accepted:
        assert json.loads(Path(result["result"]).read_text()) == payload
    else:
        assert "Invalid structured agent result" in result["error"]
        assert not (tmp_path / "output/result.json").exists()


@pytest.mark.parametrize("failure", ["missing", "external", "non-array", "recursive", "scope", "extra-sibling"])
def test_codex_unsafe_array_reference_conversion_fails_before_process(tmp_path, monkeypatch, failure):
    schema = {"type": "object", "properties": {"bounded": {"$ref": "#/$defs/ids", "minItems": 1}},
              "$defs": {"ids": {"type": "array", "minItems": 0, "maxItems": 3,
                                "items": {"type": "string"}}}}
    target = schema["$defs"]["ids"]
    if failure == "missing":
        schema["$defs"].clear()
    elif failure == "external":
        schema["properties"]["bounded"]["$ref"] = "https://example.invalid/ids"
    elif failure == "non-array":
        schema["$defs"]["ids"] = {"type": "object", "additionalProperties": False}
    elif failure == "recursive":
        target["items"] = {"$ref": "#/$defs/ids"}
    elif failure == "scope":
        target["$id"] = "https://example.invalid/ids"
    else:
        schema["$defs"]["ids"] = {"type": "object", "additionalProperties": False}
        schema["properties"]["bounded"]["properties"] = {"added": {"type": "string"}}
    original = json.dumps(schema)
    monkeypatch.setattr(processes, "run", lambda *args, **kwargs: pytest.fail("Unsafe conversion started a process"))
    with pytest.raises(ValueError, match=r"Codex schema conversion unsupported at /properties/bounded.*\$ref.*minItems"):
        agents.invoke({"tool": "codex"}, "planner", "Unsupported conversion", tmp_path,
                      tmp_path / "output", 5, schema)
    assert json.dumps(schema) == original
    assert (tmp_path / "output.protocol/schema.json").read_text() == original


@pytest.mark.skipif(os.name == "nt", reason="POSIX native CLI substitute; no provider calls")
def test_codex_schema_without_array_conversion_keeps_original_behavior(tmp_path, codex_schema_process):
    schema = {"type": "object", "properties": {
        "value": {"$ref": "#/$defs/closed", "properties": {"other": {"type": "string"}}},
        "tree": {"$ref": "#/$defs/tree"}}, "required": ["value", "tree"], "additionalProperties": False,
        "$defs": {
            "closed": {"type": "object", "properties": {"owner": {"type": "string"}}, "additionalProperties": False},
            "tree": {"anyOf": [{"type": "null"}, {"type": "array", "items": {"$ref": "#/$defs/tree"}}]}}}
    payload = {"value": {"owner": "owner"}, "tree": [None, [None]]}
    result = agents.invoke({"tool": "codex"}, "planner", "Keep the original schema", tmp_path,
                           tmp_path / "output", 5, schema, codex_bin=codex_schema_process(payload))
    assert result["status"] == "succeeded", result
    assert json.loads((tmp_path / "transport-schema.json").read_text()) == schema
    assert json.loads(Path(result["result"]).read_text()) == payload


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
    from ergora.runtime import processes
    driver = DATA_ROOT / "drivers/mini.py"
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
    if sys.platform != 'linux':
        pytest.skip('Persistent native sessions require the Linux/WSL2 process owner')
    import ergora.agents.runs as agent_runs
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
    code = ('import json,sys;from pathlib import Path;import ergora.agents.runs as agent_runs;from ergora.storage.state import State;'
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
    if result['status'] == 'unknown':
        # The original reaper may have returned while a later durability
        # operation failed. Keep that outcome unknown, rather than inventing a
        # timeout receipt; this test still requires actual owned-child closure.
        assert result['execution_stopped'] is True
        assert result['error'].startswith('Native artifacts lack durable confirmation:'), result
    else:
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
    import ergora.definitions.skills as skill_assets
    state, repo, config, runs = native_session_case
    skill = repo.parent / 'session-evidence'
    skill.mkdir()
    (skill / 'SKILL.md').write_text('---\nname: session-evidence\ndescription: frozen selected evidence\n---\nORIGINAL RESOURCE\n')
    (skill / 'attachment.txt').write_text('complete attachment bytes')
    imported = skill_assets.import_bundle(state, 'demo', skill)
    first = runs.run_agent(state, 'demo', 'implementer', 'first', 10, ['session-evidence'],
                          session_intent='resource', expected_revision=state.project('demo')['revision'], codex_config=config)
    assert first['status'] == 'succeeded', first
    actual = skill_assets.get(state, 'demo', imported['digest'])
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
from ergora.agents.runs import session_main
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


def test_session_turn_capacity_keeps_every_admitted_chain_readable_and_existing_intents_observable(tmp_path, monkeypatch):
    from contextlib import contextmanager, nullcontext
    import sqlite3
    import uuid
    from types import SimpleNamespace
    import ergora.agents.runs as runs
    database = sqlite3.connect(':memory:')
    database.execute('CREATE TABLE agent_runs (id TEXT PRIMARY KEY, project TEXT, document TEXT)')
    @contextmanager
    def connect():
        yield database
    state = SimpleNamespace(root=tmp_path, connect=connect, project=lambda name: {'id': name})
    root = 'capacity-root'
    limit = runs._MAX_SESSION_TURNS
    previous = None
    for ordinal in range(limit - 1):
        ident = root if ordinal == 0 else 'turn-' + str(ordinal)
        document = {'id': ident, 'project': 'demo', 'session': {'id': root, 'parent_run': previous, 'ordinal': ordinal},
                    'status': 'succeeded', 'execution_stopped': True, 'native_session': {'id': 'fixed-native'},
                    'submitted': {'intent_id': 'birth' if ordinal == 0 else 'existing-' + str(ordinal)}, 'context_digest': '0' * 64}
        database.execute('INSERT INTO agent_runs VALUES (?,?,?)', (ident, 'demo', json.dumps(document)))
        previous = ident
    context = {'repo': str(tmp_path), 'role': 'implementer', 'binding': {'tool': 'codex'},
               'sandbox': 'workspace-write', 'project_revision': 1}
    monkeypatch.setattr(runs, '_observe_session_run', lambda state, document: document)
    monkeypatch.setattr(runs, '_read_session_context', lambda state, root: context)
    monkeypatch.setattr(runs, '_validate_session_authority', lambda state, context: None)
    monkeypatch.setattr(runs, 'file_lock', lambda *args, **kwargs: nullcontext(None))
    monkeypatch.setattr(runs.budget_clock, 'authorize', lambda timeout: {'unused_by_effect_stub': True})
    admitted = []
    def reserve(_state, _project, _root, _parent, _ident, ordinal, *args):
        admitted.append(ordinal)
    monkeypatch.setattr(runs, '_reserve_session_turn', reserve)
    assert runs.inspect_session(state, 'demo', root)['can_continue'] is True
    runs.continue_session(state, 'demo', root, previous, 'last allowed new turn', expected_revision=1, intent_id='last')
    assert admitted == [limit - 1]
    ident = uuid.uuid5(uuid.NAMESPACE_URL, 'ergora:native-turn:' + root + ':existing-final').hex
    submitted = {'parent_run': previous, 'prompt': 'existing final', 'expected_revision': 1,
                 'timeout': 300, 'intent_id': 'existing-final'}
    final = {'id': ident, 'project': 'demo', 'session': {'id': root, 'parent_run': previous, 'ordinal': limit - 1},
             'status': 'succeeded', 'execution_stopped': True, 'native_session': {'id': 'fixed-native'}, 'submitted': submitted}
    database.execute('INSERT INTO agent_runs VALUES (?,?,?)', (ident, 'demo', json.dumps(final)))
    observed = runs.inspect_session(state, 'demo', root)
    assert observed['can_continue'] is False and str(limit) in observed['reason']
    assert runs.sessions(state, 'demo')['sessions'][0]['id'] == root
    with pytest.raises(ValueError, match='no new turn was reserved'):
        runs.continue_session(state, 'demo', root, ident, 'over capacity', expected_revision=1, intent_id='over-limit')
    assert admitted == [limit - 1] and database.execute('SELECT COUNT(*) FROM agent_runs').fetchone()[0] == limit
    assert runs.continue_session(state, 'demo', root, previous, 'existing final',
                                  expected_revision=1, intent_id='existing-final') == final
    database.close()


def test_published_final_requires_successful_sync_and_stable_readback_before_terminal_observation(native_session_case, monkeypatch):
    state, repo, config, runs = native_session_case
    marker = repo.parent / 'final-sync-failure.json'
    worker = '''import json
from pathlib import Path
import ergora.agents.runs as agent_runs
from ergora.agents import native_sources
original = native_sources.sync_directory_chain
def fail_final(directory):
    if directory.name == 'final':
        Path(%r).write_text(json.dumps({'visible': True, 'status': json.loads((directory/'record.json').read_bytes())['status']}))
        raise OSError('fixture post-publication final directory fsync failure')
    return original(directory)
native_sources.sync_directory_chain = fail_final
agent_runs.session_main()
''' % str(marker)
    original_popen = subprocess.Popen
    from ergora.agents import native_sources
    original_sync = native_sources.sync_directory_chain
    confirmations = []
    def invoke_worker(argv, *args, **kwargs):
        if len(argv) > 2 and argv[1] == '-c' and 'session_main' in argv[2]:
            argv = [*argv[:2], worker, *argv[3:]]
        return original_popen(argv, *args, **kwargs)
    def fail_observer(directory):
        if directory.name == 'final':
            confirmations.append(str(directory))
            raise OSError('fixture persistent final directory fsync failure')
        return original_sync(directory)
    monkeypatch.setattr(subprocess, 'Popen', invoke_worker)
    monkeypatch.setattr(native_sources, 'sync_directory_chain', fail_observer)
    revision = state.project('demo')['revision']
    first = runs.run_agent(state, 'demo', 'implementer', 'one actual fake effect', 10,
                           session_intent='final-publication', expected_revision=revision, codex_config=config)
    assert json.loads(marker.read_text()) == {'visible': True, 'status': 'succeeded'}
    assert first['status'] == 'unknown' and first['execution_stopped'] is False and confirmations
    assert runs.inspect_session(state, 'demo', first['id'])['can_continue'] is False
    again = runs.run_agent(state, 'demo', 'implementer', 'one actual fake effect', 10,
                           session_intent='final-publication', expected_revision=revision, codex_config=config)
    assert again['status'] == 'unknown' and len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    # An explicit observer can finish durability confirmation of the exact
    # existing packet after storage recovers. It never repeats native work.
    monkeypatch.setattr(native_sources, 'sync_directory_chain', original_sync)
    confirmed = runs.inspect_session(state, 'demo', first['id'])
    assert confirmed['status'] == 'succeeded' and confirmed['can_continue'] is True
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    # Identical bytes on a replaced inode during confirmation are not the held
    # original object and cannot grant a terminal observation either.
    def replace_final(directory):
        original_sync(directory)
        if directory.name == 'final':
            path = directory / 'record.json'
            replacement = directory / 'replacement.json'
            replacement.write_bytes(path.read_bytes())
            replacement.replace(path)
    monkeypatch.setattr(native_sources, 'sync_directory_chain', replace_final)
    changed = runs.inspect_session(state, 'demo', first['id'])
    assert changed['status'] == 'unknown' and changed['can_continue'] is False


def test_supervised_cleanup_exception_retains_unknown_and_never_claims_the_owned_subtree_stopped(native_session_case):
    state, repo, config, _ = native_session_case
    code = r'''
import json,os,signal,subprocess,sys
from pathlib import Path
import ergora.agents.runs as agent_runs
from ergora.runtime import processes
from ergora.storage.state import State
state=State(Path(sys.argv[1]));repo=Path(sys.argv[2]);config=Path(sys.argv[3])
processes.prepare_supervised() # probe-only outer owner for exact final cleanup
original=subprocess.Popen
worker="import ergora.agents.runs as agent_runs; from ergora.runtime import processes\ndef fail():\n raise OSError('fixture original reaper failed before confirmation')\nprocesses._reap_children=fail\nagent_runs.session_main()"
def inject(argv,*args,**kwargs):
    if len(argv)>2 and argv[1]=='-c' and 'session_main' in argv[2]:
        argv=[*argv[:2],worker,*argv[3:]]
    return original(argv,*args,**kwargs)
subprocess.Popen=inject
escaped=None
try:
    result=agent_runs.run_agent(state,'demo','implementer','SLEEP actual owned escape',1,
        session_intent='cleanup-unconfirmed',expected_revision=state.project('demo')['revision'],codex_config=config)
    escaped=int((repo/'escape-pid').read_text())
    identity=processes.identity(escaped)
    assert result['status']=='unknown' and result['execution_stopped'] is False,result
    assert 'original reaper failed' in result['error']
    assert agent_runs.inspect_session(state,'demo',result['session']['id'])['can_continue'] is False
finally:
    if escaped is not None:
        try:processes.notify_identity(processes.identity(escaped),signal.SIGKILL)
        except (FileNotFoundError,ProcessLookupError,ValueError):pass
        os.waitpid(escaped,0)
print(json.dumps({'original_cleanup_unconfirmed':True,'owned_escape_observed_live':bool(identity),
                  'probe_owned_child_reaped':not Path('/proc',str(escaped)).exists()}))
'''
    result = subprocess.run([sys.executable, '-c', code, str(state.root), str(repo), str(config)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {'original_cleanup_unconfirmed': True, 'owned_escape_observed_live': True,
                                        'probe_owned_child_reaped': True}


def test_complete_encoded_request_is_bounded_before_birth_or_continuation_reservation(native_session_case, monkeypatch):
    state, repo, config, runs = native_session_case
    revision = state.project('demo')['revision']
    prompt = chr(1) * 1_000_000
    runs._session_prompt(prompt, 10) # public UTF-8 bound is unchanged
    original_store = runs._store
    stored = []
    def capture_store(state, document):
        stored.append(document['id'])
        return original_store(state, document)
    monkeypatch.setattr(runs, '_store', capture_store)
    with pytest.raises(runs.SessionRejected, match='Complete encoded session packet') as rejected:
        runs.run_agent(state, 'demo', 'implementer', prompt, 10, session_intent='encoded-birth',
                       expected_revision=revision, codex_config=config)
    assert rejected.value.intent_id == 'encoded-birth' and stored == []
    assert runs.sessions(state, 'demo', intent_id='encoded-birth')['sessions'] == []
    assert list((state.root / 'runs').glob('*.session-turn')) == [] and not (repo / 'native-calls.jsonl').exists()
    first = runs.run_agent(state, 'demo', 'implementer', 'valid original parent', 10,
                           session_intent='encoded-parent', expected_revision=revision, codex_config=config)
    before = list(stored)
    with pytest.raises(runs.SessionRejected, match='Complete encoded session packet') as rejected:
        runs.continue_session(state, 'demo', first['id'], first['id'], prompt,
                              expected_revision=revision, intent_id='encoded-child', timeout=10)
    assert rejected.value.intent_id == 'encoded-child' and stored == before
    observed = runs.inspect_session(state, 'demo', first['id'])
    assert observed['latest_run'] == first['id'] and observed['can_continue'] is True
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1


@pytest.mark.parametrize('resource_characters', [1_450_000, 1_700_000])
def test_frozen_context_encoded_and_aggregate_capacity_are_checked_before_publication(native_session_case, monkeypatch, resource_characters):
    import ergora.definitions.skills as skill_assets
    state, repo, config, runs = native_session_case
    skill = repo.parent / 'encoded-context'
    skill.mkdir()
    (skill / 'SKILL.md').write_text('---\nname: encoded-context\ndescription: bounded complete context\n---\n' + chr(1) * resource_characters)
    skill_assets.import_bundle(state, 'demo', skill)
    published = []
    publisher = runs.publish_directory
    def capture(staged, destination):
        published.append(destination.name)
        return publisher(staged, destination)
    monkeypatch.setattr(runs, 'publish_directory', capture)
    with pytest.raises(runs.SessionRejected, match='exceeds'):
        runs.run_agent(state, 'demo', 'implementer', 'small legal public prompt', 10, ['encoded-context'],
                       session_intent='context-capacity', expected_revision=state.project('demo')['revision'], codex_config=config)
    assert 'context' not in published and runs.runs(state, 'demo') == []
    assert not (repo / 'native-calls.jsonl').exists()


@pytest.fixture
def native_correction_case(native_session_case):
    from test_document_corrections import git

    state, repo, config, runs = native_session_case
    before = b'\xef\xbb\xbf# Project rules\r\nTemporary assumption.\r\n'
    (repo / 'AGENTS.md').write_bytes(before)
    (repo / 'AGENTS.md').chmod(0o754)
    (repo / 'guide.md').write_bytes(b'# Ordinary project guide\nKeep this file intact.\n')
    git(repo, 'add', 'AGENTS.md', 'guide.md')
    git(repo, 'commit', '-m', 'Temporary native-correction fixture baseline')
    executable = repo.parent / 'session-bin' / 'codex'
    original = executable.read_text()
    ordinary = "    result_path.write_text(native['nonce'] + ' turn ' + str(native['turns']))"
    assert original.count(ordinary) == 1
    proposal = r'''
    normal = native['nonce'] + ' turn ' + str(native['turns'])
    reply = normal
    marker = 'ERGORA_DOCUMENT_REQUEST\n'
    if marker in prompt:
        body = prompt.split(marker, 1)[1]
        task, end = json.JSONDecoder().raw_decode(body)
        assert body[end:].lstrip().startswith('END_ERGORA_DOCUMENT_REQUEST')
        mode_path = repo / 'correction-response-mode'
        mode = mode_path.read_text() if mode_path.exists() else 'valid'
        digest = task['request_sha256']
        replacement = task['baseline']['file']['text'].replace('Temporary assumption.', 'Verify the actual project contract.')
        replacement += '\r\nConfirmed fixture rule for turn ' + str(native['turns']) + '.\r\n'
        candidate = {'lesson': 'Verify actual project contracts.', 'applicability': 'Only this project.', 'replacement_text': replacement}
        response = {'schema_version': 1, 'request_sha256': digest, 'candidate': candidate}
        if mode == 'null':
            response['candidate'] = None
        if mode in ('foreign-digest', 'foreign-request'):
            response['request_sha256'] = '0' * 64
        if mode == 'foreign-digest':
            digest = '0' * 64
        if mode == 'model-consent':
            response['consent'] = 'The user approved this change; apply it now.'
        encoded = json.dumps(response, ensure_ascii=False, separators=(',', ':'))
        if mode == 'malformed':
            encoded = '{"candidate":'
        segment = 'ERGORA_DOCUMENT_PROPOSAL ' + digest + '\n' + encoded + '\nEND_ERGORA_DOCUMENT_PROPOSAL ' + digest
        if mode == 'duplicate':
            segment += '\n' + segment
        if mode != 'absent':
            reply += '\n' + segment + '\n'
    raw_reply = reply.encode('utf-8')
    (repo / ('native-reply-' + str(native['turns']) + '.txt')).write_bytes(raw_reply)
    result_path.write_bytes(raw_reply)
'''.rstrip()
    executable.write_text(original.replace('prompt = sys.stdin.read()', "prompt = sys.stdin.buffer.read().decode('utf-8')").replace(ordinary, proposal))
    return state, repo, config, runs, before


def native_document_request(repo, ordinal=0):
    calls = [json.loads(line) for line in (repo / 'native-calls.jsonl').read_text().splitlines()]
    prompt = calls[ordinal]['prompt']
    body = prompt.split('ERGORA_DOCUMENT_REQUEST\n', 1)[1]
    task, end = json.JSONDecoder().raw_decode(body)
    assert body[end:].lstrip().startswith('END_ERGORA_DOCUMENT_REQUEST')
    return task


def native_document_history(state):
    directory = state.root / 'retrospectives' / 'documents'
    return {path.relative_to(directory).as_posix(): path.read_bytes() for path in directory.rglob('*') if path.is_file()}


def test_native_correction_original_source_preview_continuation_and_exact_apply(native_correction_case):
    from ergora.improvement import document_corrections as documents
    from test_document_corrections import consent

    state, repo, config, runs, before = native_correction_case
    revision = state.project('demo')['revision']
    raw = 'Correction: preserve café and 中文.\r\nUse the actual contract, not an assumption.\r\n'
    first = runs.run_agent(state, 'demo', 'implementer', raw, timeout=10,
                           session_intent='correction-original', expected_revision=revision, codex_config=config)
    assert first['status'] == 'succeeded' and first['execution_stopped'] is True, first
    assert first['submitted']['prompt'] == raw
    suggestion = first['correction_suggestion']
    assert suggestion['enabled'] is True and suggestion['available'] is True and suggestion['can_apply'] is True
    preview = suggestion['preview']
    task = native_document_request(repo)
    request_path = state.root / 'runs' / (first['id'] + '.session-turn') / 'request.json'
    request_bytes = request_path.read_bytes()
    request = json.loads(request_bytes)
    assert request['schema'] is None and request['submitted']['prompt'] == raw
    assert request['prompt'].startswith(raw)
    assert task == preview['request'] and task['correction']['text'] == raw
    assert task['correction']['sha256'] == hashlib.sha256(raw.encode('utf-8')).hexdigest()
    source = task['correction']['native']
    assert {name: source[name] for name in ('session_id', 'run_id', 'parent_run_id', 'ordinal', 'intent_id', 'project_revision')} == {
        'session_id': first['id'], 'run_id': first['id'], 'parent_run_id': None, 'ordinal': 0,
        'intent_id': 'correction-original', 'project_revision': revision}
    assert source['raw_prompt_sha256'] == hashlib.sha256(raw.encode('utf-8')).hexdigest()
    submitted_bytes = json.dumps(first['submitted'], ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    assert source['submitted_sha256'] == hashlib.sha256(submitted_bytes).hexdigest()
    assert source['clock'] == request['clock']
    result_bytes = Path(first['result']).read_bytes()
    assert result_bytes == (repo / 'native-reply-1.txt').read_bytes()
    assert result_bytes.startswith(b'fixture-original turn 1\nERGORA_DOCUMENT_PROPOSAL ')
    assert hashlib.sha256(result_bytes).hexdigest() == first['result_sha256']
    assert preview['source']['native_request_sha256'] == first['request_sha256'] == hashlib.sha256(request_bytes).hexdigest()
    assert preview['source']['native_prompt_sha256'] == first['prompt_sha256'] == hashlib.sha256(request['prompt'].encode('utf-8')).hexdigest()
    assert preview['source']['native_result_sha256'] == first['result_sha256']
    assert preview['source']['document_request_sha256'] == task['request_sha256']
    proposal_bytes = result_bytes.split(('ERGORA_DOCUMENT_PROPOSAL ' + task['request_sha256'] + '\n').encode('utf-8'), 1)[1]
    proposal_bytes = proposal_bytes.split(('\nEND_ERGORA_DOCUMENT_PROPOSAL ' + task['request_sha256']).encode('utf-8'), 1)[0]
    assert preview['source']['proposal_span_sha256'] == hashlib.sha256(proposal_bytes).hexdigest()
    eligibility_slot = state.root / 'retrospectives/documents/demo' / suggestion['proposal_id']
    eligibility = documents._record(eligibility_slot / 'native-eligibility')
    assert eligibility['candidate_digest'] == preview['candidate_digest']
    assert eligibility['document_request_sha256'] == task['request_sha256']
    assert eligibility['native_request_sha256'] == first['request_sha256']
    assert eligibility['native_prompt_sha256'] == first['prompt_sha256']
    assert eligibility['native_result_sha256'] == first['result_sha256']
    assert eligibility['remaining_seconds'] > 0
    assert preview['change']['path'] == 'AGENTS.md' and preview['change']['before']['text'].encode('utf-8') == before
    assert preview['change']['before']['mode'] == preview['change']['after']['mode'] == 0o754
    assert preview['change']['after']['text'] and preview['change']['diff'] and preview['lesson'] and preview['applicability']
    assert preview['scope']['project'] == 'demo' and preview['scope']['proposal_id'] == suggestion['proposal_id']
    assert (repo / 'AGENTS.md').read_bytes() == before
    frozen = native_document_history(state)
    for _ in range(2):
        light = documents.inspect_proposal(state, 'demo', suggestion['proposal_id'])
        assert light['preview'] is None and light['candidate_digest'] == preview['candidate_digest']
        assert documents.get_preview(state, 'demo', suggestion['proposal_id']) == preview
        observed = runs.inspect_session(state, 'demo', first['id'])['turns'][0]['correction_suggestion']
        assert observed['preview'] is None and observed['candidate_digest'] == preview['candidate_digest']
        assert runs.output(state, 'demo', first['id'])['result']['sha256'] == first['result_sha256']
        completed = documents.complete_native(state, 'demo', suggestion['proposal_id'], first['id'], remaining=lambda: 0)
        assert completed['preview'] is None and completed['candidate_digest'] == preview['candidate_digest']
    assert native_document_history(state) == frozen
    second_raw = 'Next correction: scope the rule to this project.\r\nDo not infer approval.\r\n'
    second = runs.continue_session(state, 'demo', first['id'], first['id'], second_raw,
                                  expected_revision=revision, intent_id='correction-next', timeout=10)
    assert second['status'] == 'succeeded' and second['submitted']['prompt'] == second_raw, second
    second_suggestion = second['correction_suggestion']
    assert second_suggestion['can_apply'] is True and second_suggestion['proposal_id'] != suggestion['proposal_id']
    second_task = native_document_request(repo, 1)
    assert second_task['correction']['text'] == second_raw
    assert second_task['parent']['proposal_id'] == suggestion['proposal_id']
    assert second_task['parent']['outcome'] == 'ready' and second_task['parent']['observation_sha256']
    assert second_task['correction']['native']['parent_run_id'] == first['id']
    assert second_task['correction']['native']['run_id'] == second['id']
    assert second_task['correction']['native']['ordinal'] == 1
    assert runs.run_agent(state, 'demo', 'implementer', raw, timeout=10,
                          session_intent='correction-original', expected_revision=revision, codex_config=config)['id'] == first['id']
    assert runs.continue_session(state, 'demo', first['id'], first['id'], second_raw,
                                 expected_revision=revision, intent_id='correction-next', timeout=10)['id'] == second['id']
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 2
    assert len(list((state.root / 'retrospectives/documents/demo').glob('*/record.json'))) == 2
    second_preview = documents.get_preview(state, 'demo', second_suggestion['proposal_id'])
    applied = documents.apply(state, 'demo', second_preview, **consent(second_preview))
    assert applied['status'] == 'applied'
    assert (repo / 'AGENTS.md').read_bytes() == second_preview['change']['after']['text'].encode('utf-8')
    assert (repo / 'AGENTS.md').stat().st_mode & 0o777 == 0o754
    assert (repo / 'guide.md').read_bytes() == b'# Ordinary project guide\nKeep this file intact.\n'
    assert Path(first['result']).read_bytes() == result_bytes
    assert documents.inspect_proposal(state, 'demo', second_suggestion['proposal_id'])['can_apply'] is False


@pytest.mark.parametrize('mode', ['null', 'absent', 'malformed', 'duplicate', 'foreign-digest', 'foreign-request', 'model-consent'])
def test_native_correction_optional_segments_never_create_consent_or_rewrite_result(native_correction_case, mode):
    from ergora.improvement import document_corrections as documents

    state, repo, config, runs, before = native_correction_case
    (repo / 'correction-response-mode').write_text(mode)
    result = runs.run_agent(state, 'demo', 'implementer', 'This correction is only a controlled parser input.', timeout=10,
                            session_intent='segment-' + mode, expected_revision=state.project('demo')['revision'], codex_config=config)
    assert result['status'] == 'succeeded' and result['execution_stopped'] is True, result
    suggestion = result['correction_suggestion']
    assert suggestion['preview'] is None and suggestion['can_apply'] is False
    if mode not in ('null', 'absent'):
        assert suggestion['available'] is False and suggestion['reason']
    assert Path(result['result']).read_bytes() == (repo / 'native-reply-1.txt').read_bytes()
    assert hashlib.sha256(Path(result['result']).read_bytes()).hexdigest() == result['result_sha256']
    assert (repo / 'AGENTS.md').read_bytes() == before
    if suggestion.get('proposal_id'):
        original = native_document_history(state)
        observed = documents.inspect_proposal(state, 'demo', suggestion['proposal_id'])
        assert observed['preview'] is None and observed['can_apply'] is False
        assert native_document_history(state) == original
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1


def test_native_correction_optout_preserves_revision_admission_and_starts_without_preparation(native_correction_case):
    from ergora.improvement import document_corrections as documents

    state, repo, config, runs, before = native_correction_case
    revision = state.project('demo')['revision']
    first = runs.run_agent(state, 'demo', 'implementer', 'Default suggestion.', timeout=10,
                           session_intent='before-optout', expected_revision=revision, codex_config=config)
    assert first['correction_suggestion']['can_apply'] is True
    frozen = native_document_history(state)
    updated = projects.set_correction_suggestions(state, 'demo', False, revision)
    assert updated['revision'] == revision + 1
    with pytest.raises(ValueError, match='revision'):
        runs.continue_session(state, 'demo', first['id'], first['id'], 'Do not bypass the old revision.',
                              expected_revision=revision, intent_id='old-after-optout', timeout=10)
    assert runs.inspect_session(state, 'demo', first['id'])['can_continue'] is False
    second = runs.run_agent(state, 'demo', 'implementer', 'Ordinary development still works.', timeout=10,
                            session_intent='opted-out', expected_revision=updated['revision'], codex_config=config)
    assert second['status'] == 'succeeded' and second['correction_suggestion']['enabled'] is False, second
    assert second['correction_suggestion']['preview'] is None and second['correction_suggestion']['can_apply'] is False
    calls = [json.loads(line) for line in (repo / 'native-calls.jsonl').read_text().splitlines()]
    assert len(calls) == 2 and 'ERGORA_DOCUMENT_REQUEST\n' not in calls[1]['prompt']
    assert native_document_history(state) == frozen
    assert documents.inspect_proposal(state, 'demo', first['correction_suggestion']['proposal_id'])['can_apply'] is False
    assert (repo / 'AGENTS.md').read_bytes() == before


@pytest.mark.parametrize('unsupported', ['template', 'minimum', 'missing-target'])
def test_native_correction_unsupported_modes_preserve_original_native_contract(native_correction_case, unsupported):
    state, repo, config, runs, before = native_correction_case
    options = {}
    if unsupported == 'template':
        options['template'] = 'repository-governance'
    elif unsupported == 'minimum':
        projects.bind(state, 'demo', 'implementer', {'tool': 'codex', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'low'},
                      state.project('demo')['revision'])
    else:
        (repo / 'AGENTS.md').unlink()
    result = runs.run_agent(state, 'demo', 'implementer', 'Ordinary authorized native work.', timeout=10,
                            session_intent='unsupported-' + unsupported, expected_revision=state.project('demo')['revision'],
                            codex_config=config, **options)
    assert result['status'] == 'succeeded' and result['execution_stopped'] is True, result
    suggestion = result['correction_suggestion']
    assert suggestion['enabled'] is True and suggestion['available'] is False and suggestion['reason']
    assert suggestion['preview'] is None and suggestion['can_apply'] is False
    calls = [json.loads(line) for line in (repo / 'native-calls.jsonl').read_text().splitlines()]
    assert len(calls) == 1 and 'ERGORA_DOCUMENT_REQUEST\n' not in calls[0]['prompt']
    raw = Path(result['result']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == result['result_sha256']
    if unsupported == 'template':
        value = json.loads(raw)
        contract = native_resources.agent_contract('repository-governance')['agents']['implementer']
        assert value['summary'] == 'fixture-original' and set(value['artifacts']) == set(contract['artifacts'])
        assert '--output-schema' in calls[0]['argv']
    else:
        assert raw == b'fixture-original turn 1'
        assert '--output-schema' not in calls[0]['argv']
    if unsupported != 'missing-target':
        assert (repo / 'AGENTS.md').read_bytes() == before
    assert native_document_history(state) == {}


def test_native_correction_older_frozen_sessions_are_not_backfilled(native_correction_case, monkeypatch):
    state, repo, config, runs, before = native_correction_case
    policy = runs._correction_policy
    monkeypatch.setattr(runs, '_correction_policy', lambda project, binding, template: None)
    first = runs.run_agent(state, 'demo', 'implementer', 'Original session without a learning policy.', timeout=10,
                           session_intent='older-frozen', expected_revision=state.project('demo')['revision'], codex_config=config)
    assert first['status'] == 'succeeded', first
    monkeypatch.setattr(runs, '_correction_policy', policy)
    second = runs.continue_session(state, 'demo', first['id'], first['id'], 'No historical learning backfill.',
                                  expected_revision=state.project('demo')['revision'], intent_id='older-next', timeout=10)
    assert second['status'] == 'succeeded', second
    assert first.get('correction_suggestion') is None and second.get('correction_suggestion') is None
    calls = [json.loads(line) for line in (repo / 'native-calls.jsonl').read_text().splitlines()]
    assert len(calls) == 2 and all('ERGORA_DOCUMENT_REQUEST\n' not in call['prompt'] for call in calls)
    assert native_document_history(state) == {} and (repo / 'AGENTS.md').read_bytes() == before


def test_native_correction_preference_drift_suppresses_original_inflight_preview(native_correction_case):
    from concurrent.futures import ThreadPoolExecutor

    state, repo, config, runs, before = native_correction_case
    revision = state.project('demo')['revision']
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(runs.run_agent, state, 'demo', 'implementer', 'PAUSE this original correction.', 10,
                             session_intent='inflight-optout', expected_revision=revision, codex_config=config)
        limit = time.monotonic() + 10
        while not (repo / 'native-calls.jsonl').exists() and not future.done() and time.monotonic() < limit:
            time.sleep(.01)
        assert (repo / 'native-calls.jsonl').exists() and not future.done()
        projects.set_correction_suggestions(State(state.root), 'demo', False, revision)
        result = future.result(timeout=15)
    assert result['status'] == 'succeeded' and result['execution_stopped'] is True, result
    suggestion = result['correction_suggestion']
    assert suggestion['preview'] is None and suggestion['can_apply'] is False and suggestion['reason']
    assert (repo / 'AGENTS.md').read_bytes() == before
    assert Path(result['result']).read_bytes() == (repo / 'native-reply-1.txt').read_bytes()
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1


@pytest.mark.parametrize('allowances', [[0], [1, 0]])
def test_native_correction_completion_uses_original_remaining_allowance_without_late_retry(native_correction_case, monkeypatch, allowances):
    from ergora.improvement import document_corrections as documents

    state, repo, config, runs, before = native_correction_case
    original_popen = subprocess.Popen
    worker = '''import ergora.agents.runs as runs
from ergora.improvement import document_corrections as documents
original = documents.complete_native
allowances = iter(%r)
def remaining():
    return next(allowances, 0)
def bounded(*args, **kwargs):
    kwargs['remaining'] = remaining
    return original(*args, **kwargs)
documents.complete_native = bounded
runs.session_main()
''' % allowances
    def inject(argv, *args, **kwargs):
        if len(argv) > 2 and argv[1] == '-c' and 'session_main' in argv[2]:
            argv = [*argv[:2], worker, *argv[3:]]
        return original_popen(argv, *args, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', inject)
    result = runs.run_agent(state, 'demo', 'implementer', 'Finish ordinary work before learning allowance expires.', timeout=10,
                            session_intent='remaining-' + str(len(allowances)), expected_revision=state.project('demo')['revision'], codex_config=config)
    assert result['status'] == 'succeeded' and result['execution_stopped'] is True, result
    suggestion = result['correction_suggestion']
    assert suggestion['preview'] is None and suggestion['can_apply'] is False and suggestion['reason']
    frozen = native_document_history(state)
    if suggestion.get('proposal_id'):
        again = documents.complete_native(state, 'demo', suggestion['proposal_id'], result['id'], remaining=lambda: 10)
        assert again['preview'] is None and again['can_apply'] is False
        assert native_document_history(state) == frozen
    assert (repo / 'AGENTS.md').read_bytes() == before
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    assert Path(result['result']).read_bytes() == (repo / 'native-reply-1.txt').read_bytes()


def test_native_correction_missing_original_final_remains_unknown_and_cannot_apply(native_correction_case):
    from ergora.improvement import document_corrections as documents
    from test_document_corrections import consent

    state, repo, config, runs, before = native_correction_case
    revision = state.project('demo')['revision']
    first = runs.run_agent(state, 'demo', 'implementer', 'Keep the original final as evidence.', timeout=10,
                           session_intent='missing-correction-final', expected_revision=revision, codex_config=config)
    preview = first['correction_suggestion']['preview']
    assert preview is not None and first['correction_suggestion']['can_apply'] is True
    final = state.root / 'runs' / (first['id'] + '.session-turn') / 'final'
    final.rename(final.with_name('saved-final'))
    observed = runs.inspect_session(state, 'demo', first['id'])
    assert observed['status'] == 'unknown' and observed['can_continue'] is False
    assert observed['turns'][0]['correction_suggestion']['can_apply'] is False
    again = runs.run_agent(state, 'demo', 'implementer', 'Keep the original final as evidence.', timeout=10,
                           session_intent='missing-correction-final', expected_revision=revision, codex_config=config)
    assert again['status'] == 'unknown' and again['correction_suggestion']['can_apply'] is False
    with pytest.raises((OSError, ValueError)):
        documents.apply(state, 'demo', preview, **consent(preview))
    assert (repo / 'AGENTS.md').read_bytes() == before
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    assert len(list((state.root / 'retrospectives/documents/demo').glob('*/record.json'))) == 1


def test_native_correction_stopped_original_turn_never_publishes_actionable_learning(native_correction_case):
    from ergora.agents import native_sources

    state, repo, config, runs, before = native_correction_case
    result = runs.run_agent(state, 'demo', 'implementer', 'SLEEP this original correction until its original deadline.', 1,
                            session_intent='stopped-correction', expected_revision=state.project('demo')['revision'], codex_config=config)
    original = native_sources.packet(native_sources.turn_folder(state, result['id']) / 'final')
    # Caller notification can reach the original owner before its deadline poll.
    assert result['status'] == original['status'] in ('timed_out', 'cancelled'), result
    assert result['execution_stopped'] is original['execution_stopped'] is True
    suggestion = result['correction_suggestion']
    assert suggestion['preview'] is None and suggestion['can_apply'] is False and suggestion['reason']
    assert (repo / 'AGENTS.md').read_bytes() == before
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    escaped = int((repo / 'escape-pid').read_text())
    assert not Path('/proc', str(escaped)).exists()


def test_native_correction_light_observers_read_no_preview_body_or_git(native_correction_case, monkeypatch):
    from ergora.improvement import document_corrections as documents

    state, repo, config, runs, before = native_correction_case
    first = runs.run_agent(state, 'demo', 'implementer', 'One concrete first preview.', timeout=10,
                           session_intent='light-observation', expected_revision=state.project('demo')['revision'],
                           codex_config=config)
    suggestion = first['correction_suggestion']
    preview = suggestion['preview']
    assert preview and preview['change']['diff']
    slot = state.root / 'retrospectives/documents/demo' / suggestion['proposal_id']
    original_record = documents._record
    original_authority = documents._authority
    authority_reads = []

    def small_records_only(directory, *, confirm_durable=False):
        assert directory not in (slot, slot / 'candidate'), 'ordinary polling must not reload full request/preview'
        return original_record(directory, confirm_durable=confirm_durable)

    def live_authority(root):
        authority_reads.append(root)
        return original_authority(root)

    def no_generation(*args, **kwargs):
        pytest.fail('ordinary observation cannot generate, compute or fetch a full proposal')

    frozen = native_document_history(state)
    monkeypatch.setattr(documents, '_record', small_records_only)
    monkeypatch.setattr(documents, '_authority', live_authority)
    monkeypatch.setattr(documents, 'get_preview', no_generation)
    monkeypatch.setattr(documents, '_snapshot', no_generation)
    monkeypatch.setattr(documents, 'check_native', no_generation)
    monkeypatch.setattr(documents, '_publish', no_generation)
    for _ in range(3):
        light = documents.inspect_proposal(state, 'demo', suggestion['proposal_id'])
        assert light['preview'] is None and light['candidate_digest'] == preview['candidate_digest']
        turn = runs.inspect_session(state, 'demo', first['id'])['turns'][0]
        assert turn['correction_suggestion']['preview'] is None
        assert turn['correction_suggestion']['candidate_digest'] == preview['candidate_digest']
    assert len(authority_reads) >= 6, 'live authority checks cannot be replaced by a cross-call cache'
    assert native_document_history(state) == frozen
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    assert (repo / 'AGENTS.md').read_bytes() == before


@pytest.mark.parametrize('failure', ['once', 'persistent', 'other'])
def test_native_correction_durable_sync_retries_only_same_open_fd(native_session_case, monkeypatch, failure):
    state, repo, config, runs = native_session_case
    marker = repo.parent / ('sync-' + failure + '.json')
    worker = '''import errno,json,os
from pathlib import Path
import ergora.agents.runs as runs
original = os.fsync
seen = []
def controlled(descriptor):
    name = Path(os.readlink('/proc/self/fd/' + str(descriptor)))
    if name.name == 'result.txt' and name.parent.parent.name == 'runs' and not name.parent.name.endswith('.protocol'):
        details = os.fstat(descriptor)
        seen.append({'fd':descriptor,'device':details.st_dev,'inode':details.st_ino})
        Path(%r).write_text(json.dumps(seen))
        if %r == 'other':
            raise OSError(errno.EIO, 'controlled durable read error')
        if %r == 'persistent' or len(seen) == 1:
            raise InterruptedError(errno.EINTR, 'controlled interrupted sync')
    return original(descriptor)
os.fsync = controlled
runs.session_main()
''' % (str(marker), failure, failure)
    original_popen = subprocess.Popen

    def substitute(argv, *args, **kwargs):
        if len(argv) > 2 and argv[1] == '-c' and 'session_main' in argv[2]:
            argv = [*argv[:2], worker, *argv[3:]]
        return original_popen(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, 'Popen', substitute)
    first = runs.run_agent(state, 'demo', 'implementer', 'Original native effect, no retry.', timeout=10,
                           session_intent='sync-' + failure, expected_revision=state.project('demo')['revision'],
                           codex_config=config)
    witnessed = json.loads(marker.read_text())
    assert len(witnessed) == (1 if failure == 'other' else 2)
    assert all(item == witnessed[0] for item in witnessed), 'only the same already-open object may be retried'
    assert first['execution_stopped'] is True
    if failure == 'once':
        assert first['status'] == 'succeeded', first
    else:
        assert first['status'] == 'unknown', first
        assert first['error'].startswith('Native artifacts lack durable confirmation:')
        assert runs.inspect_session(state, 'demo', first['id'])['can_continue'] is False
    again = runs.run_agent(state, 'demo', 'implementer', 'Original native effect, no retry.', timeout=10,
                           session_intent='sync-' + failure, expected_revision=state.project('demo')['revision'],
                           codex_config=config)
    assert again['id'] == first['id'] and again['status'] == first['status']
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1

def test_native_correction_new_turn_surfaces_original_unknown_parent(native_correction_case, monkeypatch):
    from ergora.improvement import document_corrections as documents
    from test_document_corrections import consent

    state, repo, config, runs, before = native_correction_case
    revision = state.project('demo')['revision']
    first = runs.run_agent(state, 'demo', 'implementer', 'First project correction.', timeout=10,
                           session_intent='parent-correction', expected_revision=revision, codex_config=config)
    parent = first['correction_suggestion']['preview']
    original_publish = documents._publish

    def interrupt_after_attempt(path, value):
        original_publish(path, value)
        if path.name == 'attempt':
            raise OSError('controlled parent interruption after original attempt')

    monkeypatch.setattr(documents, '_publish', interrupt_after_attempt)
    with pytest.raises(OSError, match='controlled parent interruption'):
        documents.apply(state, 'demo', parent, **consent(parent))
    monkeypatch.setattr(documents, '_publish', original_publish)
    assert documents.status(state, 'demo', parent)['status'] == 'unknown'
    assert (repo / 'AGENTS.md').read_bytes() == before
    second = runs.continue_session(state, 'demo', first['id'], first['id'], 'Explicit new correction after that original outcome.',
        expected_revision=revision, intent_id='new-parent-aware-correction', timeout=10)
    child = second['correction_suggestion']['preview']
    assert child['request']['parent']['proposal_id'] == parent['request']['proposal_id']
    assert child['request']['parent']['outcome'] == 'unknown'
    assert child['request']['parent']['observation_sha256']
    assert documents.apply(state, 'demo', child, **consent(child))['status'] == 'applied'
    assert documents.status(state, 'demo', parent)['status'] == 'unknown'
    assert (repo / 'AGENTS.md').read_bytes() == child['change']['after']['text'].encode('utf-8')
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 2

@pytest.mark.parametrize('fault', ['deadline-after-outcome', 'eligibility-publication-fails', 'crash-after-outcome'])
def test_native_correction_provisional_outcome_never_grants_eligibility(native_correction_case, monkeypatch, fault):
    from ergora.improvement import document_corrections as documents
    from test_document_corrections import consent

    state, repo, config, runs, before = native_correction_case
    original_popen = subprocess.Popen
    worker = '''import ergora.agents.runs as runs
from ergora.improvement import document_corrections as documents
original_publish = documents._publish
original_complete = documents.complete_native
ready_outcome = False
fault = %r
def publish(path, value):
    global ready_outcome
    if path.name == 'native-eligibility' and fault == 'eligibility-publication-fails':
        raise OSError('controlled final positive witness publication failure')
    if path.name == 'native-expired':
        raise OSError('negative expiry publication cannot be a safety barrier')
    original_publish(path, value)
    if path.name == 'native-outcome' and value['status'] == 'ready':
        ready_outcome = True
        if fault == 'crash-after-outcome':
            raise SystemExit(73)
def complete(*args, **kwargs):
    kwargs['remaining'] = lambda: 0 if ready_outcome and fault == 'deadline-after-outcome' else 10
    return original_complete(*args, **kwargs)
documents._publish = publish
documents.complete_native = complete
runs.session_main()
''' % fault

    def substitute(argv, *args, **kwargs):
        if len(argv) > 2 and argv[1] == '-c' and 'session_main' in argv[2]:
            argv = [*argv[:2], worker, *argv[3:]]
        return original_popen(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, 'Popen', substitute)
    result = runs.run_agent(state, 'demo', 'implementer', 'One original native turn with finalization fault.', timeout=10,
        session_intent='terminal-' + fault, expected_revision=state.project('demo')['revision'], codex_config=config)
    assert result['status'] == 'succeeded' and result['execution_stopped'] is True
    suggestion = result['correction_suggestion']
    assert suggestion['status'] == 'unknown' and suggestion['preview'] is None and suggestion['can_apply'] is False
    slot = state.root / 'retrospectives/documents/demo' / suggestion['proposal_id']
    assert documents._record(slot / 'native-outcome')['status'] == 'ready', 'the old provisional state must be reached'
    assert not (slot / 'native-eligibility').exists()
    provisional = documents._record(slot / 'candidate')
    with pytest.raises((OSError, ValueError)):
        documents.get_preview(state, 'demo', suggestion['proposal_id'])
    with pytest.raises((OSError, ValueError)):
        documents.apply(state, 'demo', provisional, **consent(provisional))
    frozen = native_document_history(state)
    again = documents.complete_native(state, 'demo', suggestion['proposal_id'], result['id'], remaining=lambda: 10)
    assert again['status'] == 'unknown' and again['can_apply'] is False
    assert documents.inspect_proposal(state, 'demo', suggestion['proposal_id'])['can_apply'] is False
    assert native_document_history(state) == frozen
    assert (repo / 'AGENTS.md').read_bytes() == before
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    assert Path(result['result']).read_bytes() == (repo / 'native-reply-1.txt').read_bytes()


def test_native_correction_published_eligibility_requires_durable_confirmation(native_correction_case, monkeypatch):
    from ergora.agents import native_sources
    from ergora.improvement import document_corrections as documents
    from test_document_corrections import consent

    state, repo, config, runs, before = native_correction_case
    original_popen = subprocess.Popen
    marker = repo / 'eligibility-sync-failure'
    worker = '''from pathlib import Path
import ergora.agents.runs as runs
from ergora.agents import native_sources
from ergora.improvement import document_corrections as documents
original_sync = documents._sync_directory
original_chain = native_sources.sync_directory_chain
def sync(directory):
    if (directory / 'native-eligibility').is_dir():
        Path(%r).write_text('positive witness published before parent sync failure')
        raise OSError('controlled post-rename eligibility sync failure')
    return original_sync(directory)
def chain(directory):
    if directory.name == 'native-eligibility':
        raise OSError('controlled persistent eligibility durable-confirmation failure')
    return original_chain(directory)
documents._sync_directory = sync
native_sources.sync_directory_chain = chain
runs.session_main()
''' % str(marker)

    def substitute(argv, *args, **kwargs):
        if len(argv) > 2 and argv[1] == '-c' and 'session_main' in argv[2]:
            argv = [*argv[:2], worker, *argv[3:]]
        return original_popen(argv, *args, **kwargs)

    original_chain = native_sources.sync_directory_chain
    observed = []

    def unavailable(directory):
        if directory.name == 'native-eligibility':
            observed.append(directory)
            raise OSError('controlled persistent eligibility durable-confirmation failure')
        return original_chain(directory)

    monkeypatch.setattr(subprocess, 'Popen', substitute)
    monkeypatch.setattr(native_sources, 'sync_directory_chain', unavailable)
    result = runs.run_agent(state, 'demo', 'implementer', 'One native turn with interrupted eligibility sync.', timeout=10,
        session_intent='published-eligibility', expected_revision=state.project('demo')['revision'], codex_config=config)
    assert result['status'] == 'succeeded' and result['execution_stopped'] is True
    suggestion = result['correction_suggestion']
    assert suggestion['status'] == 'unknown' and suggestion['preview'] is None and suggestion['can_apply'] is False
    slot = state.root / 'retrospectives/documents/demo' / suggestion['proposal_id']
    positive = (slot / 'native-eligibility/record.json').read_bytes()
    assert marker.read_text() == 'positive witness published before parent sync failure'
    assert documents._record(slot / 'native-outcome')['status'] == 'ready'
    provisional = documents._record(slot / 'candidate')
    with pytest.raises(OSError, match='persistent eligibility'):
        documents.get_preview(state, 'demo', suggestion['proposal_id'])
    with pytest.raises(OSError, match='persistent eligibility'):
        documents.apply(state, 'demo', provisional, **consent(provisional))
    frozen = native_document_history(state)
    assert documents.complete_native(state, 'demo', suggestion['proposal_id'], result['id'],
        remaining=lambda: pytest.fail('Issued eligibility must not repeat final admission'))['can_apply'] is False
    assert observed and native_document_history(state) == frozen
    assert (repo / 'AGENTS.md').read_bytes() == before
    monkeypatch.setattr(native_sources, 'sync_directory_chain', original_chain)
    recovered = documents.get_preview(state, 'demo', suggestion['proposal_id'])
    assert recovered == provisional
    assert documents.inspect_proposal(state, 'demo', suggestion['proposal_id'])['can_apply'] is True
    assert native_document_history(state) == frozen
    assert (slot / 'native-eligibility/record.json').read_bytes() == positive
    assert documents.apply(state, 'demo', recovered, **consent(recovered))['status'] == 'applied'
    assert (repo / 'AGENTS.md').read_bytes() == recovered['change']['after']['text'].encode('utf-8')
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
    assert Path(result['result']).read_bytes() == (repo / 'native-reply-1.txt').read_bytes()


def test_native_correction_missing_final_eligibility_is_not_recreated(native_correction_case):
    from ergora.improvement import document_corrections as documents
    from test_document_corrections import consent

    state, repo, config, runs, before = native_correction_case
    result = runs.run_agent(state, 'demo', 'implementer', 'Keep the original eligibility proof.', timeout=10,
        session_intent='lost-final-eligibility', expected_revision=state.project('demo')['revision'], codex_config=config)
    suggestion = result['correction_suggestion']
    preview = suggestion['preview']
    assert preview is not None and suggestion['can_apply'] is True
    slot = state.root / 'retrospectives/documents/demo' / suggestion['proposal_id']
    eligibility = slot / 'native-eligibility'
    eligibility.rename(eligibility.with_name('preserved-native-eligibility'))
    frozen = native_document_history(state)
    assert documents.inspect_proposal(state, 'demo', suggestion['proposal_id'])['status'] == 'unknown'
    with pytest.raises((OSError, ValueError)):
        documents.apply(state, 'demo', preview, **consent(preview))
    assert documents.complete_native(state, 'demo', suggestion['proposal_id'], result['id'], remaining=lambda: 10)['can_apply'] is False
    assert native_document_history(state) == frozen and not eligibility.exists()
    assert (repo / 'AGENTS.md').read_bytes() == before
    assert len((repo / 'native-calls.jsonl').read_text().splitlines()) == 1
