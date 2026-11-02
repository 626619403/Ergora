"""Effective choices describe actual legacy execution and remain frozen per invocation."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from ergora import agent_runs, agents, components, memory, projects, tools
from ergora.state import State


@pytest.fixture
def legacy_project(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    state = State(tmp_path / "data")
    project = projects.create(state, "demo", repo)
    project["bindings"] = {"implementer": {"tool": "command", "argv": [sys.executable, "-c", "print('legacy')"]}}
    with state.connect() as db:
        db.execute("UPDATE projects SET document=? WHERE id=?", (json.dumps(project), "demo"))
    return state, project


def test_effective_sources_keep_legacy_choices_without_writing_defaults(legacy_project, monkeypatch):
    state, project = legacy_project
    before = deepcopy(project)
    configuration = projects.effective_configuration(project)
    assert configuration["scope"] == "project-bindings"
    assert configuration["project"] == {key: project[key] for key in ("id", "repo", "revision")}
    for role in agents.ROLE_CAPABILITIES:
        resolved = configuration["layers"][role]
        assert resolved["binding"] == project["bindings"]["implementer"]
        assert resolved["source"] == {"kind": "project" if role == "implementer" else "inherited", "path": "bindings.implementer"}
        assert resolved["validation"] == {"valid": True}
    expected = {"memory": "sqlite", "research": "urls", "scheduler": "manual", "optimizer": "manual", "kernel": "manual"}
    for layer, tool in expected.items():
        assert configuration["layers"][layer] == {
            "binding": {"tool": tool},
            "source": {"kind": "legacy-default", "path": f"legacy-missing-bindings-v1.{layer}"},
            "validation": {"valid": True},
        }
    for layer in components.LAYERS:
        monkeypatch.setitem(components.DEFAULT_BINDINGS, layer, {"tool": "changed-recommendation"})
        monkeypatch.setitem(components.LAYERS[layer], "default_binding", {"tool": "changed-recommendation"})
    assert projects.effective_configuration(project) == configuration
    assert project == before == State(state.root).project("demo")
    content = {key: value for key, value in configuration.items() if key != "sha256"}
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest() == configuration["sha256"]
    configuration["layers"]["reviewer"]["binding"]["argv"].append("changed")
    assert project == before


def test_doctor_and_memory_use_the_same_missing_support_choices(legacy_project):
    state, project = legacy_project
    checks = {check["layer"]: check for check in tools.doctor(state, "demo")["checks"]}
    assert checks["memory"]["tool"] == "sqlite" and checks["memory"]["connectivity"] == "local"
    assert checks["research"]["tool"] == "urls"
    saved = memory.save(state, "demo", "Legacy execution keeps local SQLite", {"uri": "manual:fixture", "revision": "1"})
    assert memory.search(state, "demo", "SQLite")["results"] == [saved]
    assert agent_runs.run_agent(state, "demo", "reviewer", "legacy role")["status"] == "succeeded"
    assert State(state.root).project("demo") == project


def test_incompatible_inherited_role_is_visible_and_does_not_block_other_roles(legacy_project):
    state, project = legacy_project
    projects.bind(state, "demo", "implementer", {"tool": "mini-swe-agent", "model": "provider/model"}, 1)
    configuration = projects.effective_configuration(state.project("demo"))
    assert configuration["layers"]["implementer"]["validation"]["valid"] is True
    review = configuration["layers"]["reviewer"]
    assert review["source"]["kind"] == "inherited"
    assert review["validation"]["valid"] is False
    check = next(item for item in tools.doctor(state, "demo")["checks"] if item["layer"] == "reviewer")
    assert check["configuration_valid"] is False and check["installed"] is None
    assert "reviewer" in check["error"]
    with pytest.raises(ValueError, match="Unsupported|does not support"):
        agent_runs.run_agent(state, "demo", "reviewer", "incompatible review")
    assert agent_runs.runs(state, "demo") == []
    projects.bind(state, "demo", "reviewer", project["bindings"]["implementer"], 2)
    run = agent_runs.run_agent(state, "demo", "reviewer", "valid role despite unrelated invalid inheritance")
    assert run["status"] == "succeeded"
    assert run["configuration"]["layers"]["planner"]["validation"]["valid"] is False


def test_invocation_saves_effective_snapshot_before_tool_and_keeps_it_after_revision_change(legacy_project, monkeypatch):
    state, project = legacy_project
    configuration = projects.effective_configuration(project)
    original_invoke = agents.invoke

    def invoke(binding, role, *args, **kwargs):
        running = agent_runs.runs(State(state.root), "demo")[0]
        assert running["status"] == "running" and running["configuration"] == configuration
        projects.bind(state, "demo", "implementer", {"tool": "command", "argv": ["/missing/new-choice"]}, 1)
        return original_invoke(binding, role, *args, **kwargs)

    monkeypatch.setattr(agents, "invoke", invoke)
    run = agent_runs.run_agent(state, "demo", "reviewer", "freeze before invocation")
    assert run["status"] == "succeeded"
    assert run["binding"] == project["bindings"]["implementer"]
    assert run["project_revision"] == 1 and run["configuration"] == configuration
    assert projects.effective_configuration(state.project("demo"))["sha256"] != configuration["sha256"]
    assert agent_runs.runs(State(state.root), "demo")[0] == run
    assert "legacy" in Path(run["output"], "stdout.txt").read_text(encoding="utf-8")


def test_recall_keeps_initial_sqlite_choice_when_project_changes_before_search(legacy_project, monkeypatch):
    state, project = legacy_project
    saved = memory.save(state, "demo", "Keep this SQLite observation", {"uri": "manual:fixture", "revision": "1"})
    configuration = projects.effective_configuration(project)
    original_search = memory.search

    def search(*args, **kwargs):
        projects.bind(state, "demo", "memory", {"tool": "reme", "endpoint": "http://127.0.0.1:1"}, 1)
        return original_search(*args, **kwargs)

    def unexpected_remote(*args, **kwargs):
        pytest.fail("A SQLite recall must not contact a newly configured ReMe backend")

    monkeypatch.setattr(memory, "search", search)
    monkeypatch.setattr(memory, "_job", unexpected_remote)
    run = agent_runs.run_agent(state, "demo", "reviewer", "recall a project observation", recall="SQLite")
    assert run["status"] == "succeeded"
    assert run["context"]["memories"] == [saved]
    assert run["configuration"] == configuration and run["project_revision"] == 1
    assert state.project("demo")["revision"] == 2
    assert agent_runs.runs(State(state.root), "demo")[0] == run


def test_recall_search_and_sync_keep_initial_reme_endpoint_when_project_changes(legacy_project, monkeypatch):
    state, _ = legacy_project
    original_binding = {"tool": "reme", "endpoint": "http://127.0.0.1:1"}
    project = projects.bind(state, "demo", "memory", original_binding, 1)
    configuration = projects.effective_configuration(project)
    saved = memory.save(state, "demo", "Keep the selected ReMe endpoint", {"uri": "manual:fixture", "revision": "1"})
    original_sync = memory.sync
    remote_calls = []

    def sync(*args, **kwargs):
        projects.bind(state, "demo", "memory", {"tool": "reme", "endpoint": "http://127.0.0.1:2"}, 2)
        return original_sync(*args, **kwargs)

    def job(binding, operation, payload):
        remote_calls.append((deepcopy(binding), operation))
        results = [{"path": f"digest/ergora/demo/{saved['id']}.md"}] if operation == "search" else []
        return {"success": True, "metadata": {"results": results}}

    monkeypatch.setattr(memory, "sync", sync)
    monkeypatch.setattr(memory, "_job", job)
    run = agent_runs.run_agent(state, "demo", "reviewer", "recall a project observation", recall="endpoint")
    assert run["status"] == "succeeded"
    assert remote_calls == [(original_binding, "write"), (original_binding, "search")]
    assert run["context"]["memories"] == [saved]
    assert run["configuration"] == configuration and run["project_revision"] == 2
    assert state.project("demo")["revision"] == 3
    assert agent_runs.runs(State(state.root), "demo")[0] == run


def test_cli_and_api_return_the_same_readonly_effective_configuration(legacy_project):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from ergora.web import create_app

    state, project = legacy_project
    result = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "project", "config", "demo"],
                            capture_output=True, text=True, encoding="utf-8", check=True)
    configuration = json.loads(result.stdout)
    with TestClient(create_app(state.root), base_url="http://127.0.0.1:8977") as client:
        response = client.get("/api/projects/demo/configuration")
        assert response.status_code == 200 and response.json() == configuration
        dashboard = client.get("/api/projects/demo/dashboard")
        assert dashboard.status_code == 200 and dashboard.json()["configuration"] == configuration
        assert client.get("/api/projects/unknown/configuration").status_code == 400
    assert State(state.root).project("demo") == project
