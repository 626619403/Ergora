import json
from pathlib import Path
import socket
import subprocess
import sys
import time

import pytest

from ergora import agents, processes, projects, tools
from ergora.state import State


@pytest.fixture
def project(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    projects.create(state, "demo", repo)
    return state, repo


def checks(report):
    return {item["layer"]: item for item in report["checks"]}


def test_default_does_not_run_commands_or_connect_and_rechecks_next_request(project, monkeypatch):
    state, _ = project
    calls = []
    monkeypatch.setattr(agents, "available", lambda binding, repo: calls.append(binding) or True)
    def unexpected(*args, **kwargs):
        pytest.fail("Default doctor must not execute a command or connect")
    monkeypatch.setattr(processes, "run", unexpected)
    monkeypatch.setattr(socket, "create_connection", unexpected)
    before = state.project("demo")
    first = tools.doctor(state, "demo")
    assert len(calls) == len({json.dumps(binding, sort_keys=True) for binding in calls})
    count = len(calls)
    tools.doctor(state, "demo")
    assert len(calls) == 2 * count
    assert state.project("demo") == before
    assert first["project_revision"] == before["revision"] and not first["probe"]["requested"]
    assert checks(first)["memory"]["task_availability"] == "available"
    assert checks(first)["reviewer"]["authentication"] == "not_checked"
    assert checks(first)["reviewer"]["task_availability"] == "not_checked"


def test_arbitrary_command_is_never_executed_even_with_probe(project, monkeypatch):
    state, _ = project
    projects.bind(state, "demo", "implementer", {"tool": "command", "argv": [sys.executable, "-c", "raise SystemExit('must not run')"]}, 1)
    monkeypatch.setattr(agents, "available", lambda binding, repo: binding["tool"] == "command")
    def unexpected(*args, **kwargs):
        pytest.fail("Must not execute arbitrary command or model")
    monkeypatch.setattr(processes, "run", unexpected)
    result = checks(tools.doctor(state, "demo", probe=True))["implementer"]
    assert result["authentication"] == "external" and result["task_availability"] == "not_checked"
    assert result["probe_status"] == "not_applicable" and result["remediation"]


def test_missing_executable_is_blocked_with_guidance(project):
    state, _ = project
    projects.bind(state, "demo", "reviewer", {"tool": "command", "argv": ["missing-ergora-test-program"]}, 1)
    result = checks(tools.doctor(state, "demo"))["reviewer"]
    assert result["installed"] is False and result["task_availability"] == "blocked"
    assert result["remediation"] and result["version"] == "not_checked"


@pytest.mark.parametrize("returncode,expected", [(0, "credentials_present"), (1, "not_confirmed")])
def test_codex_probe_discards_auth_output_and_never_reports_task_acceptance(project, monkeypatch, returncode, expected):
    state, _ = project
    monkeypatch.setattr(agents, "available", lambda *args: True)
    monkeypatch.setattr(processes, "resolve_program", lambda *args: "codex")
    calls = []
    def run(argv, cwd, output, timeout):
        calls.append(argv)
        output.mkdir()
        version = argv[1:] == ["--version"]
        (output / "stdout.txt").write_text("codex-cli 1.2.3 secret-value" if version else "secret-value", encoding="utf-8")
        code = 0 if version else returncode
        return {"status": "succeeded" if code == 0 else "failed", "returncode": code}
    monkeypatch.setattr(processes, "run", run)
    result = tools.doctor(state, "demo", probe=True)
    review = checks(result)["reviewer"]
    assert review["version"] == "1.2.3" and review["authentication"] == expected
    assert review["task_availability"] == "not_checked" and review["connectivity"] == "not_checked"
    assert calls == [["codex", "--version"], ["codex", "login", "status"]]
    assert "secret-value" not in json.dumps(result)


def test_missing_reme_credential_is_distinct_from_tcp_reachable(project, monkeypatch):
    state, _ = project
    monkeypatch.delenv("ERGORA_TEST_REME_TOKEN", raising=False)
    monkeypatch.setattr(agents, "available", lambda *args: False)
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        projects.bind(state, "demo", "memory", {"tool": "reme", "endpoint": f"http://127.0.0.1:{port}", "token_env": "ERGORA_TEST_REME_TOKEN"}, 1)
        result = checks(tools.doctor(state, "demo", probe=True, timeout=5))["memory"]
    assert result["authentication"] == "credentials_missing"
    assert result["connectivity"] == "tcp_reachable" and result["installed"] is None
    assert result["task_availability"] == "blocked"


def test_whole_active_budget_includes_child_timeout(project, monkeypatch):
    state, _ = project
    monkeypatch.setattr(agents, "available", lambda *args: True)
    monkeypatch.setattr(processes, "resolve_program", lambda *args: "codex")
    original = processes.run
    calls = []
    def run(argv, cwd, output, timeout):
        calls.append(argv)
        return original([sys.executable, "-c", "import time; time.sleep(60)"], cwd, output, timeout)
    monkeypatch.setattr(processes, "run", run)
    start = time.monotonic()
    report = tools.doctor(state, "demo", probe=True, timeout=1)
    assert time.monotonic() - start < 6  # Includes native Windows process-tree setup/cleanup.
    review = checks(report)["reviewer"]
    assert review["version"] == "timed_out" and review["authentication"] == "not_checked"
    assert review["probe_status"] == "budget_exhausted" and len(calls) == 1


@pytest.mark.parametrize("timeout", [0, 31, True, 1.5])
def test_probe_budget_is_validated(project, timeout):
    with pytest.raises(ValueError, match="1–30"):
        tools.doctor(project[0], "demo", probe=True, timeout=timeout)


def test_http_probe_requires_local_write_header_and_uses_same_contract(project, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from ergora.web import create_app
    state, _ = project
    monkeypatch.setattr(agents, "available", lambda *args: False)
    client = TestClient(create_app(state.root), base_url="http://127.0.0.1")
    uri = "/api/projects/demo/doctor"
    assert client.post(uri, json={}).status_code == 403
    headers = {"X-Ergora-Request": "1"}
    response = client.post(uri, json={"timeout": 1}, headers=headers)
    assert response.status_code == 200
    assert response.json() == tools.doctor(state, "demo", probe=True, timeout=1)
    assert client.post(uri, json={"timeout": 31}, headers=headers).status_code == 422
