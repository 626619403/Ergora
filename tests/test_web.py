import json
import sys
from pathlib import Path
import subprocess

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

from ergora import memory, projects, skills
from ergora.state import State
from ergora.web import create_app
from test_agents import native_session_case


@pytest.fixture
def console(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    projects.create(state, "demo", repo)
    projects.create(state, "other", repo)
    headers = {"Origin": "http://127.0.0.1:8977", "X-Ergora-Request": "1"}
    with TestClient(create_app(state.root), base_url="http://127.0.0.1:8977", headers=headers) as client:
        yield client, state, repo


def test_local_http_boundary_and_packaged_assets(console):
    client, state, repo = console
    index = client.get("/")
    assert index.status_code == 200 and "/assets/app.js" in index.text
    assert "script-src 'self'" in index.headers["content-security-policy"]
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/vendor/cytoscape.min.js").status_code == 200
    payload = {"id": "third", "repo": str(repo)}
    assert client.post("/api/projects", json=payload, headers={"X-Ergora-Request": ""}).status_code == 403
    assert client.post("/api/projects", json=payload, headers={"Origin": "https://attacker.example"}).status_code == 403
    assert client.get("/api/bootstrap", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert client.get("/api/bootstrap", headers={"Host": "attacker.example", "Origin": "http://attacker.example"}).status_code == 400
    assert [item["id"] for item in client.get("/api/bootstrap").json()["projects"]] == ["demo", "other"]


def test_installation_profiles_match_cli_without_rewriting_projects(console):
    client, state, _ = console
    before = state.project("demo")
    observed = client.get("/api/installation-profiles")
    assert observed.status_code == 200
    result = subprocess.run([sys.executable, "-m", "ergora", "tools", "profiles"],
                            capture_output=True, text=True, encoding="utf-8", timeout=10)
    assert result.returncode == 0, result.stderr
    assert observed.json() == json.loads(result.stdout)
    assert state.project("demo") == before


def test_binding_revisions_and_cli_web_share_durable_state(console):
    client, state, repo = console
    path = "/api/projects/demo/bindings/implementer"
    binding = {"tool": "command", "argv": [sys.executable, "-c", "import sys;print(sys.stdin.read())"]}
    assert client.put(path, json={"binding": binding, "revision": 1}).status_code == 200
    assert client.put(path, json={"binding": binding, "revision": 1}).status_code == 400
    assert state.project("demo")["revision"] == 2
    result = client.post("/api/projects/demo/agent-runs", json={"role": "implementer", "prompt": "API fixture", "timeout": 5}).json()
    assert result["status"] == "succeeded"
    assert "API fixture" in Path(result["output"], "stdout.txt").read_text()
    preview = client.get(f"/api/projects/demo/agent-runs/{result['id']}/output").json()
    assert "API fixture" in preview["streams"]["stdout"]["text"]
    assert "native_history" not in preview
    unsupported = client.get(f"/api/projects/demo/agent-runs/{result['id']}/output?native_history=true").json()
    assert unsupported["native_history"]["available"] is False
    Path(result["output"], "stdout.txt").write_text("Z" * 70000)
    bounded = client.get(f"/api/projects/demo/agent-runs/{result['id']}/output").json()["streams"]["stdout"]
    assert len(bounded["text"]) == 65536 and bounded["truncated"]
    assert client.get(f"/api/projects/other/agent-runs/{result['id']}/output").status_code == 400
    assert client.get("/api/projects/other/dashboard").json()["agent_runs"] == []


def test_project_sessions_http_and_cli_preserve_exact_operation_inputs(console, tmp_path, monkeypatch, capsys):
    from ergora import agent_runs, cli

    client, state, _ = console
    calls = []
    root = {"id": "session-root", "project": "demo", "status": "succeeded", "session": {"id": "session-root"}}
    page = {"sessions": [{"id": root["id"], "birth_intent": "birth-once"}], "next_after": None}
    detail = {"id": root["id"], "turns": [root], "next_after": None}
    stopped = {"run_id": "exact-turn", "stop_requested": True, "notification": "unconfirmed", "run": root}

    def start(control, project, role, prompt, timeout, skill_names, recall, template, **options):
        calls.append((control.root, project, role, prompt, timeout, skill_names, recall, template, options))
        return root

    def listing(control, project, **options):
        calls.append((control.root, project, options))
        return page

    def inspect(control, project, session, **options):
        calls.append((control.root, project, session, options))
        return detail

    def followup(control, project, session, parent, prompt, **options):
        calls.append((control.root, project, session, parent, prompt, options))
        return root

    def stop(control, project, session, run, **options):
        calls.append((control.root, project, session, run, options))
        return stopped

    monkeypatch.setattr(agent_runs, "run_agent", start)
    monkeypatch.setattr(agent_runs, "sessions", listing)
    monkeypatch.setattr(agent_runs, "inspect_session", inspect)
    monkeypatch.setattr(agent_runs, "continue_session", followup)
    monkeypatch.setattr(agent_runs, "stop_session", stop)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Continue developing: café\n", encoding="utf-8")
    config = tmp_path / "native options.toml"
    payload = {"role": "implementer", "prompt": prompt.read_text(), "timeout": 71, "skills": ["original-skill"],
               "recall": "original memory", "template": "large-change", "session_intent": "birth-once",
               "expected_revision": 3, "codex_config": str(config)}
    base = "/api/projects/demo"
    assert client.post(base + "/agent-runs", json=payload).json() == root
    initial = calls.pop()
    assert initial == (state.root, "demo", "implementer", prompt.read_text(), 71, ["original-skill"],
                       "original memory", "large-change", {"session_intent": "birth-once", "expected_revision": 3, "codex_config": config})
    prefix = ["--home", str(state.root), "agent"]
    assert cli.main(prefix + ["run", "demo", "implementer", "--prompt", str(prompt), "--timeout", "71",
        "--skill", "original-skill", "--recall", "original memory", "--template", "large-change",
        "--session-intent", "birth-once", "--revision", "3", "--codex-config", str(config)]) == 0
    assert calls.pop() == initial and json.loads(capsys.readouterr().out) == root
    assert client.get(base + "/agent-sessions?after=2&limit=7&intent_id=birth-once").json() == page
    listing_call = calls.pop()
    assert listing_call == (state.root, "demo", {"after": 2, "limit": 7, "intent_id": "birth-once"})
    assert cli.main(prefix + ["sessions", "demo", "--after", "2", "--limit", "7", "--intent", "birth-once"]) == 0
    assert calls.pop() == listing_call and json.loads(capsys.readouterr().out) == page
    url = base + "/agent-sessions/session-root"
    assert client.get(url + "?after=1&limit=4").json() == detail
    inspect_call = calls.pop()
    assert inspect_call == (state.root, "demo", "session-root", {"after": 1, "limit": 4})
    assert cli.main(prefix + ["session", "demo", "session-root", "--after", "1", "--limit", "4"]) == 0
    assert calls.pop() == inspect_call and json.loads(capsys.readouterr().out) == detail
    continuation = {"parent_run_id": "exact-parent", "prompt": prompt.read_text(), "expected_revision": 3,
                    "intent_id": "continue-once", "timeout": 83}
    assert client.post(url + "/continue", json=continuation).json() == root
    followup_call = calls.pop()
    assert followup_call == (state.root, "demo", "session-root", "exact-parent", prompt.read_text(),
                             {"expected_revision": 3, "intent_id": "continue-once", "timeout": 83})
    assert cli.main(prefix + ["continue", "demo", "session-root", "--parent", "exact-parent", "--prompt", str(prompt),
        "--revision", "3", "--intent", "continue-once", "--timeout", "83"]) == 0
    assert calls.pop() == followup_call and json.loads(capsys.readouterr().out) == root
    assert client.post(url + "/stop", json={"run_id": "exact-turn", "intent_id": "stop-once"}).json() == stopped
    stop_call = calls.pop()
    assert stop_call == (state.root, "demo", "session-root", "exact-turn", {"intent_id": "stop-once"})
    assert cli.main(prefix + ["stop", "demo", "session-root", "--run", "exact-turn", "--intent", "stop-once"]) == 0
    assert calls.pop() == stop_call and json.loads(capsys.readouterr().out) == stopped

    # Transport validation cannot add execution authority or silently coerce revision/budget values.
    for change in ({"expected_revision": True}, {"timeout": "83"}, {"cwd": "/elsewhere"}, {"native_uuid": "external"}):
        assert client.post(url + "/continue", json={**continuation, **change}).status_code == 422
    assert client.get(base + "/agent-sessions?after=-1").status_code == 422
    assert client.post(url + "/stop", json={"run_id": "exact-turn", "intent_id": "stop-once"},
                       headers={"X-Ergora-Request": ""}).status_code == 403
    assert client.post(url + "/continue", json=continuation, headers={"Origin": "https://other.example"}).status_code == 403
    assert calls == []


@pytest.mark.skipif(sys.platform != "linux", reason="Persistent native turns use the Linux process owner")
def test_project_native_session_http_and_cli_share_original_development_chain(native_session_case, tmp_path):
    state, repo, config, _ = native_session_case
    revision = state.project("demo")["revision"]
    base = "/api/projects/demo/agent-sessions"
    headers = {"Origin": "http://127.0.0.1:8977", "X-Ergora-Request": "1"}
    with TestClient(create_app(state.root), base_url="http://127.0.0.1:8977", headers=headers) as client:
        rejected = client.post("/api/projects/demo/agent-runs", json={"role": "implementer", "prompt": "stale start",
            "timeout": 10, "session_intent": "rejected-birth", "expected_revision": revision - 1, "codex_config": str(config)})
        assert rejected.status_code == 400
        assert rejected.json() == {"error": "Session start requires the current project revision", "admission_rejected": True,
                                   "native_effect_started": False, "intent_id": "rejected-birth"}
        oversized = client.post("/api/projects/demo/agent-runs", json={"role": "implementer", "prompt": "X" * 1_000_001,
            "session_intent": "oversized-birth", "expected_revision": revision, "codex_config": str(config)})
        assert oversized.status_code == 400 and oversized.json()["admission_rejected"] is True
        assert oversized.json()["intent_id"] == "oversized-birth" and not oversized.json()["native_effect_started"]
        assert client.get(base, params={"intent_id": "rejected-birth"}).json()["sessions"] == []
        assert not (repo / "native-calls.jsonl").exists()
        # Discard the submitted call's reply and recover only by its exact original birth intent.
        response = client.post("/api/projects/demo/agent-runs", json={"role": "implementer", "prompt": "HTTP first change",
            "timeout": 10, "session_intent": "http-birth", "expected_revision": revision, "codex_config": str(config)})
        assert response.status_code == 200
        del response
        observed = client.get(base, params={"intent_id": "http-birth"}).json()
        assert len(observed["sessions"]) == 1 and observed["next_after"] is None
        session = observed["sessions"][0]
        assert session["birth_intent"] == "http-birth" and session["sandbox"] == "workspace-write"
        assert session["can_continue"] and (repo / "turn-1.txt").read_text() == "HTTP first change"
        assert client.get(base, params={"intent_id": "unrelated-birth"}).json()["sessions"] == []
        assert client.get(base.replace("/demo/", "/other/")).status_code == 400
        second = client.post(f"{base}/{session['id']}/continue", json={"parent_run_id": session["latest_run"],
            "prompt": "HTTP second change", "expected_revision": revision, "intent_id": "http-next", "timeout": 10}).json()
        assert second["status"] == "succeeded", second
        assert second["session"]["parent_run"] == session["latest_run"]
        assert second["formal_execution_authorized"] is False
        prompt = tmp_path / "third.md"
        prompt.write_text("CLI third change")
        process = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "agent", "continue", "demo",
            session["id"], "--parent", second["id"], "--prompt", str(prompt), "--revision", str(revision),
            "--intent", "cli-third", "--timeout", "10"], capture_output=True, text=True, timeout=20)
        assert process.returncode == 0, process.stderr
        third = json.loads(process.stdout)
        assert third["status"] == "succeeded", third
        first_page = client.get(f"{base}/{session['id']}?limit=2").json()
        final_page = client.get(f"{base}/{session['id']}?after={first_page['next_after']}&limit=2").json()
        assert [turn["session"]["ordinal"] for turn in first_page["turns"] + final_page["turns"]] == [0, 1, 2]
        assert final_page["next_after"] is None and final_page["latest_run"] == third["id"]
        output = client.get(f"/api/projects/demo/agent-runs/{third['id']}/output").json()
        assert output["result"]["available"] and output["result"]["text"] == "fixture-original turn 3"
        assert output["result"]["sha256"] == third["result_sha256"]
        assert (repo / "turn-2.txt").read_text() == "HTTP second change"
        assert (repo / "turn-3.txt").read_text() == "CLI third change"
        calls = [json.loads(line) for line in (repo / "native-calls.jsonl").read_text().splitlines()]
        assert len(calls) == 3 and len({call["id"] for call in calls}) == 1
        assert len({call["home"] for call in calls}) == 1


@pytest.mark.skipif(sys.platform != "linux", reason="Native archive reads admit Linux/WSL2")
def test_native_history_http_and_cli_read_the_same_saved_run_without_mutating_it(console):
    client, state, _ = console
    run_id = "saved-harness-run"
    protocol = state.root / "runs" / (run_id + ".protocol")
    cwd = state.root / "runs" / (run_id + ".cwd")
    home = protocol / "native-home"
    archive = home / "sessions/project/native-session/session.v4.jsonl"
    archive.parent.mkdir(parents=True)
    identity = {"home": str(home), "session_id": "native-session", "profile": "sdk-minimal"}
    (protocol / "native-identity.json").write_text(json.dumps(identity))
    raw = (json.dumps({"version": 4, "id": "native-session", "cwd": str(cwd)}) + "\n" +
           json.dumps({"text": "保存的回复🙂" * 30}, ensure_ascii=False) + "\n").encode()
    archive.write_bytes(raw)
    document = {"id": run_id, "project": "demo", "status": "succeeded", "binding": {"tool": "deepseek-harness"}}
    encoded = json.dumps(document)
    with state.connect() as db:
        db.execute("INSERT INTO agent_runs VALUES (?, ?, ?)", (run_id, "demo", encoded))
    url = f"/api/projects/demo/agent-runs/{run_id}/output"
    first = client.get(url, params={"native_history": True, "history_limit": 255})
    assert first.status_code == 200
    page = first.json()["native_history"]
    assert page["next_offset"] is not None
    args = [sys.executable, "-m", "ergora", "--home", str(state.root), "agent", "output", "demo", run_id,
            "--native-history", "--history-limit", "255"]
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == first.json()
    assert client.get(url, params={"native_history": True, "history_offset": page["next_offset"]}).status_code == 400
    cursor = {"native_history": True, "history_offset": page["next_offset"], "history_limit": 255,
              "history_revision": page["revision"]}
    following = client.get(url, params=cursor)
    assert following.status_code == 200 and following.json()["native_history"]["offset"] == page["next_offset"]
    assert client.get(url.replace("/demo/", "/other/"), params=cursor).status_code == 400
    assert archive.read_bytes() == raw
    with state.connect() as db:
        assert db.execute("SELECT document FROM agent_runs WHERE id=?", (run_id,)).fetchone()[0] == encoded


def test_memory_provenance_search_conflict_and_restore(console):
    client, state, _ = console
    base = "/api/projects/demo/memories"
    payload = {"text": '<img src=x onerror="alert(1)"> observed text', "source": {"uri": "manual:fixture", "revision": "v1"}}
    created = client.post(base, json=payload).json()
    assert memory.records(State(state.root), "demo")[0]["text"] == payload["text"]
    memory.save(state, "demo", "Corrected observation", payload["source"], created["id"], 1)
    assert client.post(base, json={**payload, "id": created["id"], "revision": 1}).status_code == 400
    restored = client.post(f"{base}/{created['id']}/restore", json={"from_revision": 1, "revision": 2}).json()
    assert restored["revision"] == 3 and restored["text"] == payload["text"]
    searched = client.get("/api/projects/demo/memory-search", params={"query": "observed"}).json()
    assert searched["results"][0]["id"] == created["id"]
    assert client.get("/api/projects/other/dashboard").json()["memories"] == []
    assert client.request("DELETE", f"{base}/{created['id']}", json={"revision": 3}).status_code == 200
    expired = client.post(base, json={**payload, "expires_at": "2001-01-01T08:00:00+08:00"}).json()
    assert client.get("/api/projects/demo/dashboard").json()["memories"] == []
    catalog = client.get("/api/projects/demo/memory-catalog").json()
    assert catalog["records"][0] == {"record": expired, "validity": "expired"} and catalog["observed_at"]
    corrected = client.post(base, json={**payload, "id": expired["id"], "revision": 1}).json()
    assert corrected["expires_at"] == expired["expires_at"]
    renewed = client.post(base, json={**payload, "id": expired["id"], "revision": 2, "expires_at": None}).json()
    assert "expires_at" not in renewed
    assert client.get("/api/projects/demo/memory-search", params={"query": "observed"}).json()["results"] == [renewed]


def test_all_templates_and_formal_dag_constraints(console):
    client, state, _ = console
    for kind in ("repository-governance", "large-change"):
        task_input = client.get(f"/api/templates/{kind}").json()["input"]
        payload = {"id": kind, "kind": kind, "input": task_input, "revision": 0}
        assert client.post("/api/projects/demo/drafts/validate", json=payload).json()["status"] == "PASS"
        saved = client.post("/api/projects/demo/drafts", json=payload).json()
        assert saved["state"] == "draft" and saved["revision"] == 1
        assert client.post("/api/projects/demo/drafts", json=payload).status_code == 400
        units = task_input["work_units"]
        units[0]["depends_on"] = [units[1]["id"]]
        units[1]["depends_on"] = [units[0]["id"]]
        assert client.post("/api/projects/demo/drafts/validate", json=payload).status_code == 400
    task_input = client.get("/api/templates/repository-governance").json()["input"]
    task_input["work_units"][1]["paths"] = task_input["work_units"][0]["paths"]
    assert client.post("/api/projects/demo/drafts", json={"id": "overlap", "kind": "repository-governance", "input": task_input, "revision": 0}).status_code == 400
    training = client.get("/api/templates/training-optimization").json()
    assert {"workload-contract.md", "experiment.json", "baseline.json"} <= set(training["files"])
    assert client.get("/api/projects/other/dashboard").json()["drafts"] == []
    assert len(client.get("/api/projects/demo/dashboard").json()["drafts"]) == 2


def test_template_roles_and_structured_agent_selection(console):
    from ergora import agents
    client, state, repo = console
    bootstrap = client.get("/api/bootstrap").json()
    assert bootstrap["layers"]["reviewer"]["requires"] == ["independent-candidate-review"]
    command = next(item for item in bootstrap["tools"]["reviewer"] if item["tool"] == "command")
    assert command["configuration"]["properties"]["capabilities"]["default"] == ["independent-candidate-review"]
    assert command["configuration"]["required"] == ["tool", "argv"]
    assert set(bootstrap["agent_contracts"]) == set(bootstrap["templates"])
    for kind, contract in bootstrap["agent_contracts"].items():
        assert client.get(f"/api/templates/{kind}").json()["agents"] == contract
    binding = {"tool": "command", "argv": [sys.executable, str(Path(__file__).parent / "fixtures/stage_agent.py")],
               "protocol": "stage-json-v1", "capabilities": agents.ROLE_CAPABILITIES["experiment-planner"]}
    path = "/api/projects/demo/bindings/experiment-planner"
    assert client.put(path, json={"binding": binding, "revision": 1}).status_code == 200
    response = client.post("/api/projects/demo/agent-runs", json={"role": "experiment-planner", "template": "training-optimization", "prompt": "Propose an experiment"})
    result = response.json()
    assert result["status"] == "succeeded"
    assert set(json.loads(Path(result["result"]).read_text())["artifacts"]) == {"hypothesis", "experiment-proposal"}
    assert client.post("/api/projects/demo/agent-runs", json={"role": "verifier", "prompt": "Bypass trusted checks"}).status_code == 400
    assert client.post("/api/projects/demo/kernel-runs", json={"action": "plan"}).status_code == 400


def test_skill_evidence_and_adoption_use_existing_business_gate(console, tmp_path):
    client, state, repo = console
    directory = tmp_path / "api-skill"
    directory.mkdir()
    baseline_text = "---\nname: api-skill\ndescription: API fixture\n---\nBASELINE\n"
    directory.joinpath("SKILL.md").write_text(baseline_text)
    baseline = client.post("/api/projects/demo/skills/import", json={"directory": str(directory)}).json()
    directory.joinpath("SKILL.md").write_text(baseline_text.replace("BASELINE", "IMPROVED"))
    candidate = client.post("/api/projects/demo/skills/import", json={"directory": str(directory), "hypothesis": "Measured fixture gain"}).json()
    diff = client.get("/api/projects/demo/skills/diff", params={"baseline": baseline["digest"], "candidate": candidate["digest"]}).json()
    assert "+IMPROVED" in diff["diff"] and diff["changed_files"] == ["SKILL.md"]
    evaluator = repo / "evaluate.py"
    evaluator.write_text('import json,sys,pathlib\nr=json.load(sys.stdin)\ns=.9 if "IMPROVED" in pathlib.Path(r["skill_dir"],"SKILL.md").read_text() else .5\nprint(json.dumps({"score":s,"passed":True,"cost":0,"feedback":"fixture"}))\n')
    manifest = {"schema_version": 1, "evaluator_argv": [sys.executable, str(evaluator)], "evaluator_files": [str(evaluator)], "timeout_seconds": 5, "minimum_gain": .1, "max_reported_cost": 1, "cases": [{"id": split, "split": split, "input": {}} for split in ("train", "validation", "holdout")]}
    suite = client.post("/api/projects/demo/evaluations/suites", json=manifest).json()
    runs = [client.post("/api/projects/demo/evaluations/run", json={"digest": digest, "suite": suite["digest"]}).json() for digest in (baseline["digest"], candidate["digest"])]
    comparison = client.get("/api/projects/demo/evaluations/compare", params={"baseline": runs[0]["id"], "candidate": runs[1]["id"]}).json()
    assert comparison["eligible"]
    payload = {"baseline_run": runs[0]["id"], "candidate_run": runs[1]["id"], "revision": 1, "reason": "Reviewed API fixture evidence"}
    assert client.post("/api/projects/demo/skills/adopt", json=payload).status_code == 200
    assert skills.versions(State(state.root), "demo")["active"][0]["digest"] == candidate["digest"]
    assert client.post("/api/projects/demo/skills/adopt", json=payload).status_code == 400


@pytest.mark.skipif(sys.platform != "linux", reason="mini driver explicitly requires Linux/bash")
def test_slow_optional_mini_probe_keeps_dashboard_repairable(console, tmp_path):
    client, state, _ = console
    slow = tmp_path / "slow-python"
    slow.write_text(f"#!{sys.executable}\nimport time;time.sleep(8)\n")
    slow.chmod(0o700)
    path = "/api/projects/demo/bindings/implementer"
    binding = {"tool": "mini-swe-agent", "model": "provider/model", "python": str(slow)}
    assert client.put(path, json={"binding": binding, "revision": 1}).status_code == 200
    response = client.get("/api/projects/demo/dashboard")
    assert response.status_code == 200
    check = next(item for item in response.json()["tools"]["checks"] if item["layer"] == "implementer")
    assert check["installed"] is False
    assert client.put(path, json={"binding": {"tool": "codex"}, "revision": 2}).status_code == 200
