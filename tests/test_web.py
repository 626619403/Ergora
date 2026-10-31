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
    Path(result["output"], "stdout.txt").write_text("Z" * 70000)
    bounded = client.get(f"/api/projects/demo/agent-runs/{result['id']}/output").json()["streams"]["stdout"]
    assert len(bounded["text"]) == 65536 and bounded["truncated"]
    assert client.get(f"/api/projects/other/agent-runs/{result['id']}/output").status_code == 400
    assert client.get("/api/projects/other/dashboard").json()["agent_runs"] == []


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
