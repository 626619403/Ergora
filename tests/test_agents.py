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

from ergora import agents, kernel, projects, reference, tools
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
@pytest.mark.skipif(os.name == "nt", reason="POSIX CLI shebang fixtures; Windows uses structured command fixtures")
def test_native_structured_output_normalization_uses_actual_process(tmp_path, monkeypatch, tool):
    programs = tmp_path / "bin"
    programs.mkdir()
    script = programs / ("codex" if tool == "codex" else "claude")
    script.write_text(f"#!{sys.executable}\nimport json,sys,pathlib\nargs=sys.argv\n" +
        ("schema=json.loads(pathlib.Path(args[args.index('--output-schema')+1]).read_text())\n" if tool == "codex" else
         "schema=json.loads(args[args.index('--json-schema')+1])\n") +
        "result={'summary':'native fixture','artifacts':{k:'evidence' for k in schema['properties']['artifacts']['required']},'decision':'approve'}\n" +
        ("pathlib.Path(args[args.index('--output-last-message')+1]).write_text(json.dumps(result))\nprint('{}')\n" if tool == "codex" else
         "print(json.dumps({'structured_output':result,'is_error':False}))\n"))
    script.chmod(0o700)
    monkeypatch.setenv("PATH", str(programs) + os.pathsep + os.environ["PATH"])
    result = agents.invoke({"tool": tool}, "reviewer", "Review", tmp_path, tmp_path / "output", 5,
                           agents.result_schema(["review-report"], True))
    assert result["status"] == "succeeded"
    assert json.loads(Path(result["result"]).read_text())["decision"] == "approve"


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
