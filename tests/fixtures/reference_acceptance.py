"""Two backend protocol fixtures through all existing stage/evidence owners; no model calls."""

import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import threading

from ergora import agents, projects, reference
from ergora.state import State


async def main():
    root, kind, backend = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    installation = root / "installation"
    for part in ("local", "upstream/platform"):
        shutil.copytree(reference.ROOT / "platform" / part, installation / part)
    (installation / ".venv").symlink_to(sys.prefix, target_is_directory=True)
    config, runtime = root / "config", root / "runtime"
    config.mkdir()
    runtime.mkdir()
    os.environ.update(AGENTFLOW_CONFIG_DIR=str(config), AGENTFLOW_STATE_DIR=str(runtime), ERGORA_FIXTURE_KEY="not-a-secret")
    sys.path[:0] = [str(installation / "local"), str(installation / "upstream/platform")]
    from agent_platform.core import git, read, write
    from agent_platform.projects import register, create_task
    from agent_platform.sandbox import container_identity
    from dev_platform.adapter import FileAdapter, sha
    from dev_platform.activities import Activities
    from dev_platform.workflow import DevelopmentWorkflow
    identity = container_identity()
    if identity is None:
        print(json.dumps({"skip": "Reference executor requires an acknowledged Docker/Podman boundary"}))
        return
    programs = root / "bin"
    programs.mkdir()
    fixture = Path(__file__).with_name("stage_agent.py")
    codex = programs / "pinned-codex"
    codex.write_text(f"#!{sys.executable}\nimport runpy\nrunpy.run_path({str(fixture)!r},run_name='__main__')\n")
    codex.chmod(0o700)
    wrong_codex = programs / "codex"
    wrong_codex.write_text("#!/bin/sh\nexit 99\n")
    wrong_codex.chmod(0o700)
    os.environ["PATH"] = str(programs) + os.pathsep + os.environ["PATH"]
    write(config / "platform.json", {"current_container_trust_acknowledged": True,
        "container_boundary": identity, "stage_walltime_seconds": 20, "max_parallel_jobs": 2,
        "codex_env_key": "ERGORA_FIXTURE_KEY", "codex_bin": str(codex), "reviewer": "codex"})
    (config / "codex.toml").write_text("")
    adapter_config = {key: str(runtime / key) for key in ("requests", "receipts", "artifacts", "approvals", "fences")}
    adapter_config["trusted_receipts"] = True
    write(config / "adapter.json", adapter_config)
    repo = root / "repo"
    repo.mkdir()
    git(repo, "init")
    (repo / "src").mkdir()
    (repo / "src/base.py").write_text("VALUE = 1\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture baseline")
    check = [sys.executable, "-c", "import ast,pathlib;[ast.parse(p.read_text()) for p in pathlib.Path('{repo}/src').glob('*.py')]"]
    checks = {key: check for key in ("behavior", "architecture", "knowledge", "integration", "compatibility", "migration-rollback")}
    write(root / "checks.json", checks)
    register("demo", repo, "github", "fixtures/demo", ["src"], root / "checks.json")
    task_input = json.loads((reference.ROOT / "platform/templates" / kind / "input.json").read_text())
    task_input.update(goal="Add a fixture module", allowed_paths=["src"],
        work_units=[{"id": "unit", "depends_on": [], "paths": ["src"], "instructions": "Add VALUE = 42 in src/new.py"}])
    write(root / "input.json", task_input)
    create_task("demo", kind, "task-1", "1", root / "input.json")
    state = State(root / "control")
    projects.create(state, "demo", repo)
    binding = {"tool": "codex", "sandbox": "current-container"} if backend == "codex" else {
        "tool": "command", "argv": [sys.executable, str(fixture)], "protocol": "stage-json-v1", "capabilities": agents.GENERAL_CAPABILITIES}
    cancellation = len(sys.argv) > 4 and sys.argv[4] == "cancel-ignore-term"
    if cancellation:
        binding["argv"] += ["--wait-for-cancellation", str(root / "action-ready"), str(root / "late-write")]
    for role in ("inspector", "planner", "implementer", "reviewer"):
        projects.bind(state, "demo", role, binding, state.project("demo")["revision"])
    app = DevelopmentWorkflow()
    app.spec = read(runtime / "tasks/task-1/task.spec.json")
    adapter = FileAdapter(adapter_config)
    activities = Activities(adapter)
    await activities.validate(app.spec)
    records = {}
    starting = app.spec["request"]["repository"]["starting_sha"]
    if cancellation:
        context = app.context("inventory", starting, dependencies={})
        job = await activities.submit(context)
        def cancel():
            limit = time.monotonic() + 15
            while not (root / "action-ready").exists() and time.monotonic() < limit:
                time.sleep(0.02)
            assert (root / "action-ready").exists()
            write(runtime / "fences/task-1.json", {"reason": "cancellation regression"})
        thread = threading.Thread(target=cancel)
        thread.start()
        receipt = reference.executor(installation, state.root, runtime / "requests/task-1" / (context["job_id"] + ".json"))
        thread.join(timeout=2)
        assert await activities.poll(job) == receipt
        assert receipt["state"] == "CANCELLED", receipt
        assert (root / "action-ready").exists()
        time.sleep(2.2)
        assert not (root / "late-write").exists()
        print(json.dumps({"cancelled": True, "no_late_write": True}))
        return
    for stage in ("inventory", "plan", "work:unit", "integrate", "verify", "review"):
        expected = records["integrate"]["candidate_sha"] if stage in ("verify", "review") else None
        dependencies = {key: records[key] for key in records if key in {
            "inventory" if stage == "plan" else "plan" if stage == "work:unit" else "work:unit" if stage == "integrate" else "integrate" if stage == "verify" else "verify"}}
        context = app.context(stage, expected, task_input["work_units"][0] if stage == "work:unit" else None, dependencies)
        job = await activities.submit(context)
        request = runtime / "requests/task-1" / (context["job_id"] + ".json")
        receipt = reference.executor(installation, state.root, request)
        assert receipt["state"] == "SUCCEEDED", receipt
        assert await activities.poll(job) == receipt
        records[stage] = receipt
        app.results[stage] = receipt
        if stage == "inventory":
            # Later project changes must not change the already-frozen task selection.
            projects.bind(state, "demo", "implementer", {"tool": "command", "argv": ["/missing/changed-binding"]}, state.project("demo")["revision"])
        if stage == "plan":
            plan_sha = sha(receipt)
            write(runtime / "approvals/fixture-approval.json", {"schema_version": 1, "kind": "plan-approval",
                "task_id": "task-1", "request_sha256": app.spec["request_sha256"], "profile_sha256": app.spec["profile_sha256"],
                "plan_sha256": plan_sha, "decision": "approve", "principal_type": "human", "actor_id": "fixture-maintainer",
                "role": "maintainer", "expires_at": time.time() + 3600, "revoked": False})
            authorization = await adapter.authorize({"task_id": "task-1", "request_sha256": app.spec["request_sha256"],
                "profile_sha256": app.spec["profile_sha256"], "plan_sha256": plan_sha, "receipt_id": "fixture-approval"})
            app.approved_plan = {"plan_sha256": plan_sha, "receipt": receipt, "approval": authorization}
    time.sleep(1.2)
    assert not list((runtime / "workspaces").rglob("late-review.py"))
    candidate = records["integrate"]["candidate_sha"]
    assert candidate != starting
    assert records["verify"]["candidate_sha"] == records["review"]["candidate_sha"] == candidate
    assert records["review"]["actor"]["session_id"] != records["work:unit"]["actor"]["session_id"]
    assert records["review"]["actor"]["id"] == backend + ":reviewer"
    assert set(app.spec["profile"]["required_checks"]) == {check["id"] for check in records["verify"]["checks"]}
    print(json.dumps({"template": kind, "backend": backend, "stages": list(records), "candidate_bound": True}))


if __name__ == "__main__":
    asyncio.run(main())
