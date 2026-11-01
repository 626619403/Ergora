import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from ergora import agents, projects, tools
from ergora.state import State


@pytest.fixture
def state_project(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    projects.create(state, "demo", repo)
    return state, repo


def test_project_scope_and_binding_revision_survive_new_process(state_project):
    state, repo = state_project
    binding = {"tool": "command", "argv": [sys.executable, "-c", "print('ready')"]}
    updated = projects.bind(state, "demo", "reviewer", binding, expected_revision=1)
    assert updated["revision"] == 2
    restored = State(state.root).project("demo")
    assert restored["bindings"]["reviewer"] == binding
    assert restored["repo"] == str(repo)
    with pytest.raises(ValueError, match="revision changed"):
        projects.bind(state, "demo", "reviewer", binding, expected_revision=1)
    with pytest.raises(ValueError, match="Unknown project"):
        state.project("other")
    with pytest.raises(ValueError, match="already exists"):
        projects.create(state, "demo", repo)


def test_unsupported_bindings_fail_instead_of_falling_back(state_project):
    state, _ = state_project
    for layer, binding in [("reviewer", {"tool": "unknown"}), ("scheduler", {"tool": "codex"}),
                           ("implementer", {"tool": "command", "argv": "echo x"}),
                           ("implementer", {"tool": "command", "argv": ["bad\0argument"]}),
                           ("implementer", {"tool": "codex", "api_key": "not-a-key"})]:
        with pytest.raises(ValueError):
            projects.bind(state, "demo", layer, binding, expected_revision=1)
    assert state.project("demo")["revision"] == 1


def test_agent_uses_configured_argv_and_keeps_failures(state_project):
    state, repo = state_project
    code = "import sys,pathlib;print(pathlib.Path.cwd());print(sys.stdin.read());sys.exit(7)"
    projects.bind(state, "demo", "reviewer", {"tool": "command", "argv": [sys.executable, "-c", code]}, 1)
    result = tools.run_agent(state, "demo", "reviewer", "literal $HOME; no shell")
    assert result["status"] == "failed" and result["returncode"] == 7
    output = Path(result["output"]) / "stdout.txt"
    assert str(repo) in output.read_text()
    assert "literal $HOME; no shell" in output.read_text()
    assert tools.runs(State(state.root), "demo")[0] == result


def test_agent_timeout_is_recorded_and_missing_executable_is_visible(state_project):
    state, _ = state_project
    binding = {"tool": "command", "argv": [sys.executable, "-c", "import time;time.sleep(20)"]}
    projects.bind(state, "demo", "implementer", binding, 1)
    assert tools.run_agent(state, "demo", "implementer", "bounded", timeout=1)["status"] == "timed_out"
    projects.bind(state, "demo", "implementer", {"tool": "command", "argv": ["/missing/tool"]}, 2)
    result = tools.run_agent(state, "demo", "implementer", "test")
    assert result["status"] == "failed" and "error" in result


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable / fork / SIGINT fixture; native lifecycle has portable coverage")
def test_doctor_resolves_relative_executable_in_project(state_project):
    state, repo = state_project
    tool = repo / "local-tool"
    tool.write_text("#!/bin/sh\ncat\n")
    tool.chmod(0o700)
    projects.bind(state, "demo", "reviewer", {"tool": "command", "argv": ["./local-tool"]}, 1)
    check = next(c for c in tools.doctor(state, "demo")["checks"] if c["layer"] == "reviewer")
    assert check["installed"] is True
    assert tools.run_agent(state, "demo", "reviewer", "relative path")["status"] == "succeeded"


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable / fork / SIGINT fixture; native lifecycle has portable coverage")
def test_normal_exit_also_cleans_up_same_group_descendants(state_project):
    state, repo = state_project
    code = "import os,time,pathlib; child=os.fork(); time.sleep(.5) if child==0 else None; pathlib.Path('late-write').touch() if child==0 else None"
    projects.bind(state, "demo", "implementer", {"tool": "command", "argv": [sys.executable, "-c", code]}, 1)
    result = tools.run_agent(state, "demo", "implementer", "test")
    assert result["status"] == "succeeded"
    time.sleep(.7)
    assert not (repo / "late-write").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable / fork / SIGINT fixture; native lifecycle has portable coverage")
def test_sigint_leaves_a_terminal_run(state_project):
    state, repo = state_project
    code = "import pathlib,time;pathlib.Path('ready').touch();time.sleep(20)"
    projects.bind(state, "demo", "implementer", {"tool": "command", "argv": [sys.executable, "-c", code]}, 1)
    prompt = repo / "prompt.txt"
    prompt.write_text("interrupt me")
    process = subprocess.Popen([sys.executable, "-m", "ergora", "--home", str(state.root), "agent", "run", "demo",
                                "implementer", "--prompt", str(prompt)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(100):
            if (repo / "ready").exists():
                break
            time.sleep(.05)
        assert (repo / "ready").exists()
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 1, stderr
        assert json.loads(stdout)["status"] == "cancelled"
        assert tools.runs(state, "demo")[0]["status"] == "cancelled"
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


@pytest.mark.parametrize("tool", ["codex", "claude-code"])
def test_native_reviewer_starts_a_fresh_restricted_invocation(state_project, monkeypatch, tool):
    state, repo = state_project
    projects.bind(state, "demo", "reviewer", {"tool": tool}, 1)
    observed = []

    def invoke(argv, cwd, output, timeout, stdin, env=None, **kwargs):
        observed.extend(argv)
        return {"status": "succeeded", "returncode": 0}

    monkeypatch.setattr(agents.processes, "run", invoke)
    tools.run_agent(state, "demo", "reviewer", "review request")
    assert "resume" not in observed
    if tool == "codex":
        assert "--ephemeral" in observed and observed[observed.index("--sandbox") + 1] == "read-only"
    else:
        assert "--no-session-persistence" in observed
        assert observed[observed.index("--tools") + 1] == "Read,Grep,Glob"
        assert "--strict-mcp-config" in observed
        assert json.loads(observed[observed.index("--mcp-config") + 1]) == {"mcpServers": {}}
