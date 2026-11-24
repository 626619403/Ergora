import json
import os
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

import ergora.improvement.evaluation as evaluation
import ergora.improvement.memory as memory
import ergora.improvement.optimization as optimization
import ergora.configuration.projects as projects
import ergora.improvement.skill_adoption as skills
import ergora.definitions.skills as skill_assets
import ergora.operations.tools as tools
import ergora.agents.runs as agent_runs
from ergora.storage.state import State


@pytest.fixture
def skill_project(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    projects.create(state, "demo", repo)
    projects.create(state, "other", repo)
    source = tmp_path / "source" / "test-skill"
    source.mkdir(parents=True)
    source.joinpath("SKILL.md").write_text("---\nname: test-skill\ndescription: A reproducible test skill\n---\nBASELINE\n")
    evaluator = repo / "evaluate.py"
    evaluator.write_text('''import json,sys,pathlib
request=json.load(sys.stdin)
text=(pathlib.Path(request["skill_dir"])/"SKILL.md").read_text()
score=.9 if "IMPROVED" in text else .5
if "REGRESS" in text and request["case"]["split"]=="holdout": score=.1
print(json.dumps({"score":score,"passed":"INCORRECT" not in text,"cost":0,"feedback":"Measured fixture result"}))
''')
    suite = evaluation.register(state, "demo", {"schema_version": 1, "evaluator_argv": [sys.executable, str(evaluator)],
        "evaluator_files": [str(evaluator)],
        "timeout_seconds": 5, "minimum_gain": .1, "max_reported_cost": 1,
        "cases": [{"id": split, "split": split, "input": {"split": split, "data": "SECRET_HELDOUT_VALUE" if split == "holdout" else "public"}}
                  for split in ("train", "validation", "holdout")]})
    baseline = skill_assets.import_bundle(state, "demo", source)
    return state, repo, source, baseline, suite


def test_candidate_evaluation_adoption_and_rollback(skill_project, tmp_path):
    state, repo, source, baseline, suite = skill_project
    text = (source / "SKILL.md").read_text().replace("BASELINE", "IMPROVED")
    (source / "SKILL.md").write_text(text)
    candidate = skill_assets.import_bundle(state, "demo", source, "Improve held-out fixture score")
    assert candidate["parent"] == baseline["digest"]
    assert "BASELINE" in (Path(baseline["path"]) / "SKILL.md").read_text()
    base_run = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    candidate_run = evaluation.evaluate(state, "demo", candidate["digest"], suite["digest"])
    comparison = evaluation.compare(state, "demo", base_run["id"], candidate_run["id"])
    assert comparison["eligible"] and comparison["averages"]["candidate"]["holdout"] == .9
    skills.adopt(state, "demo", base_run["id"], candidate_run["id"], 1, "Reviewed fixture evidence")
    active = skill_assets.versions(State(state.root), "demo")["active"][0]
    assert active["digest"] == candidate["digest"] and active["revision"] == 2
    projects.bind(state, "demo", "implementer", {"tool": "command", "argv": [sys.executable, "-c", "import sys;print(sys.stdin.read())"]}, 1)
    note = memory.save(state, "demo", "Run the project verification command", {"uri": "manual:project", "revision": "v1"})
    invocation = agent_runs.run_agent(state, "demo", "implementer", "Use selected context", skill_names=["test-skill"], recall="verification")
    assert invocation["context"]["skills"][0]["digest"] == candidate["digest"]
    assert invocation["context"]["memories"][0]["id"] == note["id"]
    assert "IMPROVED" in Path(invocation["output"], "stdin.txt").read_text()
    with pytest.raises(ValueError, match="Active skill changed"):
        skills.adopt(state, "demo", base_run["id"], candidate_run["id"], 1, "stale")
    skill_assets.rollback(state, "demo", "test-skill", baseline["digest"], 2, "Restore previous active skill")
    assert skill_assets.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]
    after_rollback = agent_runs.run_agent(state, "demo", "implementer", "Check restored context", skill_names=["test-skill"])
    assert "BASELINE" in Path(after_rollback["output"], "stdin.txt").read_text()
    target = tmp_path / "export" / "test-skill"
    skill_assets.export(state, "demo", candidate["digest"], target)
    assert skill_assets.digest_tree(target)[0] == candidate["digest"]
    with pytest.raises(ValueError, match="Unknown skill"):
        skill_assets.get(state, "other", candidate["digest"])


def test_holdout_regression_partial_evidence_and_mutation_are_rejected(skill_project):
    state, repo, source, baseline, suite = skill_project
    (source / "SKILL.md").write_text((source / "SKILL.md").read_text().replace("BASELINE", "IMPROVED REGRESS"))
    candidate = skill_assets.import_bundle(state, "demo", source)
    base = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    bad = evaluation.evaluate(state, "demo", candidate["digest"], suite["digest"])
    assert "holdout" in " ".join(evaluation.compare(state, "demo", base["id"], bad["id"])["reasons"])
    with pytest.raises(ValueError, match="not eligible"):
        skills.adopt(state, "demo", base["id"], bad["id"], 1, "must not pass")
    partial = evaluation.evaluate(state, "demo", candidate["digest"], suite["digest"], ["validation"])
    assert not evaluation.compare(state, "demo", base["id"], partial["id"])["eligible"]
    (repo / "evaluate.py").write_text("print('changed scorer')")
    with pytest.raises(ValueError, match="Trusted evaluator changed"):
        evaluation.compare(state, "demo", base["id"], bad["id"])
    (Path(candidate["path"]) / "SKILL.md").write_text("tampered")
    with pytest.raises(ValueError, match="content changed"):
        skill_assets.get(state, "demo", candidate["digest"])


def test_selected_evaluation_archive_omits_unselected_case_material(skill_project):
    state, _, _, baseline, suite = skill_project
    manifest = suite["manifest"]
    digest = suite["digest"]
    full_run = evaluation.evaluate(state, "demo", baseline["digest"], digest)
    full_path = Path(full_run["output"], "suite.json")
    complete_snapshot = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    assert full_run["status"] == "succeeded" and full_path.read_bytes() == complete_snapshot
    holdout = manifest["cases"][-1]
    assert json.loads(Path(full_run["cases"][-1]["output"], "stdin.txt").read_bytes())["case"] == holdout["input"]

    partial = evaluation.evaluate(state, "demo", baseline["digest"], digest, ["validation", "train", "validation"])
    assert partial["status"] == "succeeded" and partial["suite"] == digest
    output = Path(partial["output"])
    raw = (output / "suite.json").read_bytes()
    holdout_id = json.dumps(holdout["id"]).encode("utf-8")
    holdout_value = holdout["input"]["data"].encode("utf-8")
    assert holdout_id not in raw and holdout_value not in raw
    selected = manifest["cases"][:2]
    assert json.loads(raw) == {**manifest, "cases": selected, "partial": True, "suite_digest": digest}
    assert [case["id"] for case in partial["cases"]] == [case["id"] for case in selected]
    for row, case, full_row in zip(partial["cases"], selected, full_run["cases"][:2], strict=True):
        request = json.loads(Path(row["output"], "stdin.txt").read_bytes())
        assert set(request) == {"skill_dir", "case", "budget"}
        assert request["skill_dir"] == baseline["path"] and request["case"] == case["input"]
        assert (row["score"], row["passed"], row["cost"]) == (full_row["score"], full_row["passed"], full_row["cost"])
    for file in output.rglob("*"):
        if file.is_file():
            raw = file.read_bytes()
            assert holdout_id not in raw and holdout_value not in raw, file

    reopened = State(state.root)
    assert evaluation.get(reopened, "demo", partial["id"]) == partial
    assert evaluation.suite(reopened, "demo", digest) == suite and evaluation.manifest_sha256(manifest) == digest
    assert full_path.read_bytes() == complete_snapshot


def test_missing_selected_asset_is_rejected_before_agent_or_evaluator_runs(skill_project):
    state, _, _, baseline, suite = skill_project
    Path(baseline["path"], "SKILL.md").unlink()
    with pytest.raises(ValueError, match="content changed"):
        agent_runs.run_agent(state, "demo", "implementer", "Use selected context", skill_names=["test-skill"])
    with pytest.raises(ValueError, match="content changed"):
        evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    assert agent_runs.runs(state, "demo") == []
    assert evaluation.listing(state, "demo")["runs"] == []


def test_skill_import_recovers_unregistered_partial_tree_and_preserves_valid_publication(skill_project):
    state, _, source, _, _ = skill_project
    (source / "reference.txt").write_text("Complete resource\n")
    digest, _ = skill_assets.digest_tree(source)
    destination = state.root / "skills" / "other" / digest / source.name
    destination.mkdir(parents=True)
    shutil.copy2(source / "SKILL.md", destination / "SKILL.md")

    imported = skill_assets.import_bundle(state, "other", source)
    assert skill_assets.get(state, "other", digest) == imported
    assert (destination / "reference.txt").read_bytes() == (source / "reference.txt").read_bytes()
    timestamps = {p.name: p.stat().st_mtime_ns for p in destination.iterdir()}
    assert skill_assets.import_bundle(state, "other", source, "Repeated import") == imported
    assert {p.name: p.stat().st_mtime_ns for p in destination.iterdir()} == timestamps
    stored = skill_assets.versions(state, "other")
    assert len(stored["versions"]) == len(stored["active"]) == len(stored["history"]) == 1


@pytest.mark.parametrize("boundary", ["copy", "publication"])
def test_interrupted_skill_import_retries_without_partial_registration(skill_project, monkeypatch, boundary):
    state, _, source, _, _ = skill_project
    (source / "reference.txt").write_text("Complete resource\n")
    digest, _ = skill_assets.digest_tree(source)
    destination = state.root / "skills" / "other" / digest / source.name
    with monkeypatch.context() as patch:
        if boundary == "copy":
            def interrupted_copy(src, dst, **kwargs):
                Path(dst).mkdir(parents=True)
                shutil.copy2(Path(src) / "SKILL.md", Path(dst) / "SKILL.md")
                raise OSError("Injected copy interruption")
            patch.setattr(shutil, "copytree", interrupted_copy)
        else:
            rename = Path.rename
            def interrupted_publication(path, target):
                result = rename(path, target)
                if Path(target) == destination:
                    raise OSError("Injected publication interruption")
                return result
            patch.setattr(Path, "rename", interrupted_publication)
        with pytest.raises(OSError, match="Injected"):
            skill_assets.import_bundle(state, "other", source)
    assert skill_assets.versions(state, "other") == {"versions": [], "active": [], "history": []}
    assert destination.exists() == (boundary == "publication")
    imported = skill_assets.import_bundle(state, "other", source)
    assert skill_assets.get(state, "other", digest) == imported
    stored = skill_assets.versions(state, "other")
    assert len(stored["versions"]) == len(stored["active"]) == len(stored["history"]) == 1


@pytest.mark.parametrize("damage", ["modified", "missing"])
def test_skill_import_refuses_to_replace_registered_evidence(skill_project, damage):
    state, _, source, baseline, _ = skill_project
    destination = Path(baseline["path"])
    if damage == "modified":
        (destination / "SKILL.md").write_text("Changed evidence\n")
    else:
        shutil.rmtree(destination)
    before = skill_assets.versions(state, "demo")
    with pytest.raises(ValueError, match="content changed"):
        skill_assets.import_bundle(state, "demo", source)
    assert skill_assets.versions(state, "demo") == before
    if damage == "modified":
        assert (destination / "SKILL.md").read_text() == "Changed evidence\n"
    else:
        assert not destination.exists()


def test_concurrent_skill_imports_publish_one_complete_version(skill_project, tmp_path):
    state, _, source, _, _ = skill_project
    (source / "reference.txt").write_text("Complete resource\n" * 10000)
    digest, _ = skill_assets.digest_tree(source)
    start = tmp_path / "start"
    script = """import json,sys,time
from pathlib import Path
import ergora.improvement.skill_adoption as skills
import ergora.definitions.skills as skill_assets
from ergora.storage.state import State
state = State(Path(sys.argv[1]))
Path(sys.argv[3]).touch()
while not Path(sys.argv[4]).exists():
    time.sleep(.01)
print(json.dumps(skill_assets.import_bundle(state, 'other', Path(sys.argv[2]))))
"""
    ready = [tmp_path / f"ready-{i}" for i in range(4)]
    children = []
    try:
        for path in ready:
            children.append(subprocess.Popen([sys.executable, "-c", script, str(state.root), str(source), str(path), str(start)],
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        deadline = time.monotonic() + 15
        while not all(path.exists() for path in ready) and time.monotonic() < deadline:
            time.sleep(.01)
        assert all(path.exists() for path in ready), "Import processes did not become ready"
        start.touch()
        results = []
        for child in children:
            stdout, stderr = child.communicate(timeout=20)
            assert child.returncode == 0, stdout + stderr
            results.append(json.loads(stdout))
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)
    assert all(result == results[0] for result in results)
    assert skill_assets.get(state, "other", digest) == results[0]
    stored = skill_assets.versions(state, "other")
    assert len(stored["versions"]) == len(stored["active"]) == len(stored["history"]) == 1


def test_adoption_rejects_evidence_from_a_different_suite(skill_project):
    state, _, source, baseline, suite = skill_project
    (source / "SKILL.md").write_text((source / "SKILL.md").read_text().replace("BASELINE", "IMPROVED"))
    candidate = skill_assets.import_bundle(state, "demo", source)
    manifest = {key: value for key, value in suite["manifest"].items() if key not in ("file_sha256", "path_bindings")}
    manifest["minimum_gain"] = .2
    other_suite = evaluation.register(state, "demo", manifest)
    base_run = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    candidate_run = evaluation.evaluate(state, "demo", candidate["digest"], other_suite["digest"])
    with pytest.raises(ValueError, match="same frozen evaluation suite"):
        skills.adopt(state, "demo", base_run["id"], candidate_run["id"], 1, "Different evidence")
    assert skill_assets.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]


def test_skill_symlinks_and_malformed_evaluator_output_fail_visibly(skill_project):
    state, repo, source, baseline, suite = skill_project
    source.joinpath("secret-link").symlink_to(repo / "evaluate.py")
    with pytest.raises(ValueError, match="symlinks"):
        skill_assets.import_bundle(state, "demo", source)
    source.joinpath("secret-link").unlink()
    reserved = {k: v for k, v in suite["manifest"].items() if k not in ("file_sha256", "path_bindings")}
    reserved["cases"] = [{**case, "id": "work"} if case["split"] == "train" else case for case in reserved["cases"]]
    reserved_suite = evaluation.register(state, "demo", reserved)
    assert evaluation.evaluate(state, "demo", baseline["digest"], reserved_suite["digest"])["status"] == "succeeded"
    scorer = repo / "malformed.py"
    scorer.write_text("print('[]')")
    manifest = {k: v for k, v in suite["manifest"].items() if k not in ("file_sha256", "path_bindings")}
    manifest["evaluator_argv"] = [sys.executable, str(scorer)]
    manifest["evaluator_files"] = [str(scorer)]
    malformed_suite = evaluation.register(state, "demo", manifest)
    result = evaluation.evaluate(state, "demo", baseline["digest"], malformed_suite["digest"])
    assert result["status"] == "failed"
    assert "Evaluator result at /:" in result["error"] and "type 'object'" in result["error"]
    assert evaluation.get(State(state.root), "demo", result["id"])["status"] == "failed"


def test_real_gepa_engine_uses_bounded_visible_cases_without_adopting(skill_project):
    pytest.importorskip("gepa")
    state, repo, source, baseline, suite = skill_project
    proposer = repo / "propose.py"
    proposer.write_text('''import json,sys,pathlib
request=json.load(sys.stdin)
pathlib.Path("seen-proposer.json").write_text(json.dumps(request))
print(json.dumps({"skill":request["candidate"]["skill"].replace("BASELINE","IMPROVED"),"cost":0}))
''')
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, str(proposer)]}, 1)
    result = optimization.optimize(state, "demo", baseline["digest"], suite["digest"], "Improve fixture score", 4, 1, 20)
    assert result["status"] == "succeeded", result
    assert result["best_candidate"] != baseline["digest"]
    assert result["metric_calls"] <= 4 and result["proposals"] <= 1
    assert skill_assets.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]
    assert "SECRET_HELDOUT_VALUE" not in repo.joinpath("seen-proposer.json").read_text()
    for run_id in result["evaluations"]:
        run = evaluation.get(state, "demo", run_id)
        assert all(c["split"] != "holdout" for c in run["cases"])
        snapshot = json.loads(Path(run["output"], "suite.json").read_bytes())
        assert snapshot["partial"] is True and snapshot["suite_digest"] == run["suite"] == suite["digest"]
        assert [case["id"] for case in snapshot["cases"]] == [case["id"] for case in run["cases"]]
        assert all(case["split"] != "holdout" for case in snapshot["cases"])


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_real_gepa_stops_with_unknown_proposer_cost_when_cost_fields_conflict(skill_project, newline):
    pytest.importorskip("gepa")
    state, repo, _, _, original = skill_project
    source = repo / "cost-skill"
    source.mkdir()
    skill_bytes = b"---\nname: cost-skill\ndescription: Local cost fixture\n---\nBASELINE\n".replace(b"\n", newline)
    (source / "SKILL.md").write_bytes(skill_bytes)
    baseline = skill_assets.import_bundle(state, "demo", source)
    scorer = repo / "cost-scorer.py"
    scorer.write_text('''import json, pathlib, sys
request = json.load(sys.stdin)
text = pathlib.Path(request["skill_dir"], "SKILL.md").read_text()
print(json.dumps({"score": .9 if "IMPROVED" in text else .5, "passed": True, "cost": .125, "feedback": "fixture"}))
''', encoding="utf-8")
    proposer = repo / "ambiguous-proposer.py"
    proposer.write_text('''import json, sys
request = json.load(sys.stdin)
skill = request["candidate"]["skill"].replace("BASELINE", "IMPROVED")
print('{"skill":' + json.dumps(skill) + ',"cost":2,"cost":0}')
''', encoding="utf-8")
    manifest = {key: value for key, value in original["manifest"].items() if key not in ("file_sha256", "path_bindings")}
    manifest.update(evaluator_argv=[sys.executable, str(scorer)], evaluator_files=[str(scorer)])
    suite = evaluation.register(state, "demo", manifest)
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, str(proposer)]}, 1)

    result = optimization.optimize(state, "demo", baseline["digest"], suite["digest"], "Improve fixture score", 4, 1, 20)
    raw = Path(result["output"], "proposal-1", "stdout.txt").read_bytes()
    assert raw.rstrip().endswith(b',"cost":2,"cost":0}')
    assert result["status"] == "failed" and result["reported_cost_complete"] is False, result
    assert "Duplicate JSON key" in result["error"] and "cost" in result["error"]
    children = [evaluation.get(state, "demo", run_id) for run_id in result["evaluations"]]
    assert all(run["skill"] == baseline["digest"] and run["reported_cost_complete"] for run in children)
    assert result["baseline"] == baseline["digest"]
    for run in children:
        for case in run["cases"]:
            request = json.loads(Path(case["output"], "stdin.txt").read_bytes())
            assert request["skill_dir"] == baseline["path"]
            assert Path(request["skill_dir"], "SKILL.md").read_bytes() == skill_bytes
    request = json.loads(Path(result["output"], "proposal-1", "stdin.txt").read_bytes())
    assert request["candidate"]["skill"].encode("utf-8") == skill_bytes
    assert result["reported_cost"] == sum(run["reported_cost"] for run in children) > 0
    assert result["proposals"] == 1 and result["candidates"] == [baseline["digest"]]
    assert optimization.listing(State(state.root), "demo")[0] == result


def test_real_gepa_retains_failed_proposer_and_cost_budget_evidence(skill_project):
    pytest.importorskip("gepa")
    state, repo, source, baseline, suite = skill_project
    proposer = repo / "invalid-proposer.py"
    proposer.write_text("print('{}')")
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, str(proposer)]}, 1)
    result = optimization.optimize(state, "demo", baseline["digest"], suite["digest"], "Reject invalid output", 8, 2, 20)
    assert result["status"] == "failed" and result["error"]
    assert result["proposals"] == 1
    assert optimization.listing(state, "demo")[0]["status"] == "failed"
    scorer = repo / "costly.py"
    scorer.write_text('print(\'{"score":0.5,"cost":2,"passed":true,"feedback":"fixture cost"}\')')
    manifest = {k: v for k, v in suite["manifest"].items() if k not in ("file_sha256", "path_bindings")}
    manifest.update(evaluator_argv=[sys.executable, str(scorer)], evaluator_files=[str(scorer)])
    costly = evaluation.register(state, "demo", manifest)
    evaluation_result = evaluation.evaluate(state, "demo", baseline["digest"], costly["digest"])
    assert evaluation_result["status"] == "budget_exhausted"
    assert len(evaluation_result["cases"]) == 1 and evaluation_result["reported_cost"] == 2


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable mode evidence; Windows content evidence is covered separately")
def test_executable_bits_and_undeclared_scorer_arguments_are_bound(skill_project):
    state, repo, source, baseline, suite = skill_project
    script = source / "run.sh"
    script.write_text("#!/bin/sh\ntrue\n")
    script.chmod(0o600)
    nonexecutable = skill_assets.import_bundle(state, "demo", source)
    script.chmod(0o700)
    executable = skill_assets.import_bundle(state, "demo", source)
    assert executable["digest"] != nonexecutable["digest"]
    Path(executable["path"], "run.sh").chmod(0o600)
    with pytest.raises(ValueError, match="content changed"):
        skill_assets.get(state, "demo", executable["digest"])
    manifest = {k: v for k, v in suite["manifest"].items() if k not in ("file_sha256", "path_bindings")}
    manifest["evaluator_files"] = []
    implicit = evaluation.register(state, "demo", manifest)
    assert str(repo / "evaluate.py") in implicit["manifest"]["file_sha256"]
    (repo / "evaluate.py").write_text("print('mutated')")
    with pytest.raises(ValueError, match="Trusted evaluator changed"):
        evaluation.evaluate(state, "demo", baseline["digest"], implicit["digest"])


def test_real_gepa_cannot_report_success_when_all_evaluators_fail(skill_project):
    pytest.importorskip("gepa")
    state, repo, source, baseline, suite = skill_project
    scorer = repo / "invalid-scorer.py"
    scorer.write_text("print('[]')")
    manifest = {k: v for k, v in suite["manifest"].items() if k not in ("file_sha256", "path_bindings")}
    manifest.update(evaluator_argv=[sys.executable, str(scorer)], evaluator_files=[str(scorer)])
    invalid = evaluation.register(state, "demo", manifest)
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, "-c", "print('{}')"]}, 1)
    result = optimization.optimize(state, "demo", baseline["digest"], invalid["digest"], "Reject broken evaluator", 4, 1, 20)
    assert result["status"] == "failed" and result["error"]
    assert result["proposals"] == 0


def test_real_gepa_passes_remaining_cost_into_each_evaluation_batch(skill_project):
    pytest.importorskip("gepa")
    state, repo, source, baseline, suite = skill_project
    scorer = repo / "batch-cost.py"
    scorer.write_text('''import json,sys,pathlib
request=json.load(sys.stdin)
text=pathlib.Path(request["skill_dir"],"SKILL.md").read_text()
print(json.dumps({"score":.9 if "IMPROVED" in text else .5,"cost":.1,"passed":True,"feedback":"fixture"}))
''')
    proposer = repo / "batch-proposer.py"
    proposer.write_text('''import json,sys
request=json.load(sys.stdin)
print(json.dumps({"skill":request["candidate"]["skill"].replace("BASELINE","IMPROVED"),"cost":0}))
''')
    manifest = {k: v for k, v in suite["manifest"].items() if k not in ("file_sha256", "path_bindings")}
    manifest.update(evaluator_argv=[sys.executable, str(scorer)], evaluator_files=[str(scorer)], max_reported_cost=.45)
    manifest["cases"] = [*manifest["cases"], {"id": "validation-two", "split": "validation", "input": {}}]
    bounded = evaluation.register(state, "demo", manifest)
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, str(proposer)]}, 1)
    result = optimization.optimize(state, "demo", baseline["digest"], bounded["digest"], "Stop after first over-budget case", 8, 1, 20)
    assert result["status"] == "budget_exhausted", result
    assert math.isclose(result["reported_cost"], .5)
    runs = [evaluation.get(state, "demo", rid) for rid in result["evaluations"]]
    assert runs[-1]["status"] == "budget_exhausted" and len(runs[-1]["cases"]) == 1


def test_real_gepa_evaluator_receives_shrinking_budgets_without_future_call_grants(skill_project, monkeypatch):
    pytest.importorskip("gepa")
    state, repo, source, baseline, suite = skill_project
    scorer = repo / "budget-scorer.py"
    scorer.write_text('''import json,sys,pathlib
request=json.load(sys.stdin)
text=pathlib.Path(request["skill_dir"],"SKILL.md").read_text()
print(json.dumps({"score":.9 if "IMPROVED" in text else .5,"cost":.1,"passed":True,"feedback":json.dumps(request["budget"])}))
''')
    proposer = repo / "budget-proposer.py"
    proposer.write_text('''import json,sys
request=json.load(sys.stdin)
print(json.dumps({"skill":request["candidate"]["skill"].replace("BASELINE","IMPROVED"),"cost":0}))
''')
    manifest = {k: v for k, v in suite["manifest"].items() if k not in ("file_sha256", "path_bindings")}
    manifest.update(evaluator_argv=[sys.executable, str(scorer)], evaluator_files=[str(scorer)], timeout_seconds=60)
    manifest["cases"].append({"id": "validation-two", "split": "validation", "input": {}})
    bounded = evaluation.register(state, "demo", manifest)
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, str(proposer)]}, 1)
    # The Windows child admission gate reads the system monotonic clock.
    clock = [time.monotonic()]
    started = clock[0]
    for owner in (optimization, evaluation, optimization.processes):
        monkeypatch.setattr(owner, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    run = optimization.processes.run
    budgets = []

    def advance(argv, cwd, output, timeout, stdin="", **kwargs):
        if output.parent.name == "cases":
            budgets.append(json.loads(stdin)["budget"])
        outcome = run(argv, cwd, output, timeout, stdin, **kwargs)
        clock[0] += 1
        return outcome

    monkeypatch.setattr(optimization.processes, "run", advance)
    result = optimization.optimize(state, "demo", baseline["digest"], bounded["digest"], "Expose effective limits", 6, 1, 20)
    assert result["status"] == "succeeded", result
    assert result["metric_calls"] == 6 and result["proposals"] == 1
    runs = [evaluation.get(state, "demo", run_id) for run_id in result["evaluations"]]
    received = [json.loads(case["feedback"]) for record in runs for case in record["cases"]]
    assert received == budgets
    assert all(budget["deadline_monotonic"] == started + 20 for budget in budgets)
    assert [budget["remaining_seconds"] for budget in budgets] == pytest.approx(
        [20, 19, 18, 16, 15, 14], rel=0, abs=math.ulp(started + 20))
    assert [budget["remaining_batch_calls"] for budget in budgets] == [2, 1, 1, 1, 2, 1]
    assert [budget["unreserved_metric_calls"] for budget in budgets] == [4, 4, 3, 2, 0, 0]
    assert all(math.isclose(budget["remaining_reported_cost"], 1 - index * .1) for index, budget in enumerate(budgets))
    assert skill_assets.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]


def test_real_gepa_retains_batch_reservation_when_setup_exhausts_deadline(skill_project, monkeypatch):
    pytest.importorskip("gepa")
    state, repo, source, baseline, suite = skill_project
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, "-c", "print('{}')"]}, 1)
    manifest = {k: v for k, v in suite["manifest"].items() if k not in ("file_sha256", "path_bindings")}
    manifest["cases"].append({"id": "validation-two", "split": "validation", "input": {}})
    bounded = evaluation.register(state, "demo", manifest)
    clock = [time.monotonic()]
    for owner in (optimization, evaluation, optimization.processes):
        monkeypatch.setattr(owner, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    write = Path.write_text

    def expire(path, *args, **kwargs):
        result = write(path, *args, **kwargs)
        if path.name == "stdin.txt":
            clock[0] += 20
        return result

    monkeypatch.setattr(Path, "write_text", expire)
    monkeypatch.setattr(optimization.processes.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Expired evaluator was dispatched"))
    result = optimization.optimize(state, "demo", baseline["digest"], bounded["digest"], "Keep reserved attempts consumed", 6, 1, 20)
    assert result["status"] == "timed_out", result
    assert result["metric_calls"] == 2 and result["proposals"] == 0
    record = evaluation.get(State(state.root), "demo", result["evaluations"][0])
    assert record["status"] == "timed_out" and len(record["cases"]) == 1
    assert record["cases"][0]["returncode"] is None
    assert optimization.listing(state, "demo")[0]["metric_calls"] == 2


@pytest.mark.parametrize("expire_during_setup", [False, True])
def test_real_gepa_proposer_keeps_fractional_remaining_time(skill_project, monkeypatch, expire_during_setup):
    pytest.importorskip("gepa")
    state, repo, source, baseline, suite = skill_project
    proposer = repo / "fractional-proposer.py"
    proposer.write_text('''import json,sys,pathlib
request=json.load(sys.stdin)
pathlib.Path("proposal-dispatched").touch()
print(json.dumps({"skill":request["candidate"]["skill"].replace("BASELINE","IMPROVED"),"cost":0}))
''')
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, str(proposer)]}, 1)
    clock = [time.monotonic()]
    started = clock[0]
    for owner in (optimization, evaluation, optimization.processes):
        monkeypatch.setattr(owner, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    run = optimization.processes.run
    proposals = []
    evaluated = 0
    write = Path.write_text

    def expire(path, *args, **kwargs):
        result = write(path, *args, **kwargs)
        if expire_during_setup and path.name == "stdin.txt" and path.parent.name.startswith("proposal-"):
            clock[0] = started + 20
        return result

    monkeypatch.setattr(Path, "write_text", expire)

    def advance(argv, cwd, output, timeout, stdin="", **kwargs):
        nonlocal evaluated
        if output.name.startswith("proposal-"):
            proposals.append((timeout, kwargs.get("deadline")))
        outcome = run(argv, cwd, output, timeout, stdin, **kwargs)
        if output.parent.name == "cases":
            evaluated += 1
            if evaluated == 2:
                clock[0] = started + 19.75
        return outcome

    monkeypatch.setattr(optimization.processes, "run", advance)
    result = optimization.optimize(state, "demo", baseline["digest"], suite["digest"], "Keep fractional tail", 4, 1, 20)
    assert result["status"] == ("timed_out" if expire_during_setup else "succeeded"), result
    assert proposals == [(.25, started + 20)]
    assert (repo / "proposal-dispatched").exists() is not expire_during_setup
    assert result["metric_calls"] == (2 if expire_during_setup else 4) and result["proposals"] == 1


def test_undeclared_scorer_symlink_retarget_invalidates_suite(skill_project):
    state, repo, source, baseline, suite = skill_project
    link = repo / "score-link.py"
    link.symlink_to(repo / "evaluate.py")
    manifest = {k: v for k, v in suite["manifest"].items() if k not in ("file_sha256", "path_bindings")}
    manifest.update(evaluator_argv=[sys.executable, str(link)], evaluator_files=[])
    frozen = evaluation.register(state, "demo", manifest)
    assert evaluation.evaluate(state, "demo", baseline["digest"], frozen["digest"])["status"] == "succeeded"
    replacement = repo / "replacement.py"
    replacement.write_text('print(\'{"score":1,"passed":true,"cost":0,"feedback":"changed"}\')')
    link.unlink()
    link.symlink_to(replacement)
    with pytest.raises(ValueError, match="path changed"):
        evaluation.evaluate(state, "demo", baseline["digest"], frozen["digest"])


def test_real_gepa_scorer_change_during_proposal_is_terminal(skill_project):
    pytest.importorskip("gepa")
    state, repo, source, baseline, suite = skill_project
    proposer = repo / "mutate-scorer.py"
    proposer.write_text('''import json,sys,pathlib
request=json.load(sys.stdin)
pathlib.Path("evaluate.py").write_text("print('mutated scorer')")
print(json.dumps({"skill":request["candidate"]["skill"].replace("BASELINE","IMPROVED"),"cost":0}))
''')
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, str(proposer)]}, 1)
    result = optimization.optimize(state, "demo", baseline["digest"], suite["digest"], "Preserve trusted scorer", 3, 1, 20)
    assert result["status"] == "failed" and "evaluator changed" in result["error"]
    assert skill_assets.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]


def _reported_outcome(output, raw, *, status="succeeded"):
    output.mkdir(parents=True)
    (output / "stdout.txt").write_text(raw, encoding="utf-8")
    return {"status": status, "returncode": 0 if status == "succeeded" else 2, "output": str(output)}


@pytest.mark.parametrize("cost,returncode,expected_status", [
    (0, 0, "failed"), (.25, 0, "failed"), (None, 0, "failed"), (2, 0, "budget_exhausted"), (.25, 2, "failed"),
])
def test_unevaluable_local_process_keeps_report_and_blocks_adoption(skill_project, cost, returncode, expected_status):
    state, repo, source, baseline, original = skill_project
    skill_file = source / "SKILL.md"
    skill_file.write_text(skill_file.read_text().replace("BASELINE", "IMPROVED"))
    candidate = skill_assets.import_bundle(state, "demo", source)
    response = {"outcome": "unevaluable", "cost": cost, "feedback": "Missing usable answer"}
    scored_response = ('{"score":0,"passed":false,"cost":0.125,"feedback":"Scored wrong answer",'
                       '"upstream_metadata":{"raw_number":1e400}}')
    scorer = repo / "unevaluable.py"
    scorer.write_text(f'''import json, sys
from pathlib import Path
request = json.load(sys.stdin)
if request["case"]["split"] == "validation" and "IMPROVED" in Path(request["skill_dir"], "SKILL.md").read_text():
    print({json.dumps(response)!r})
    print("Original evaluator diagnostic", file=sys.stderr)
    sys.exit({returncode})
print({scored_response!r})
''', encoding="utf-8")
    manifest = {key: value for key, value in original["manifest"].items() if key not in ("file_sha256", "path_bindings")}
    manifest.update(evaluator_argv=[sys.executable, str(scorer)], evaluator_files=[str(scorer)])
    suite = evaluation.register(state, "demo", manifest)
    base_run = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    result = evaluation.evaluate(state, "demo", candidate["digest"], suite["digest"])
    assert base_run["status"] == "succeeded"
    assert result["status"] == expected_status and evaluation.get(State(state.root), "demo", result["id"]) == result
    assert [row["id"] for row in result["cases"]] == ["train", "validation"]
    assert not Path(result["output"], "cases", "holdout").exists()
    first, row = result["cases"]
    assert first["score"] == 0 and first["passed"] is False and first["reported_cost_complete"] is True
    assert "upstream_metadata" not in first and Path(first["output"], "stdout.txt").read_text() == scored_response + "\n"
    assert row["status"] == ("failed" if returncode else "succeeded") and row["returncode"] == returncode
    assert json.loads(Path(row["output"], "stdout.txt").read_text()) == response
    assert Path(row["output"], "stderr.txt").read_text() == "Original evaluator diagnostic\n"
    assert {"score", "passed"}.isdisjoint(row)
    if returncode:
        assert {"outcome", "cost", "feedback"}.isdisjoint(row)
    else:
        assert {key: row[key] for key in response} == response
    complete = returncode == 0 and cost is not None
    assert row["reported_cost_complete"] is result["reported_cost_complete"] is complete
    subtotal = .125 + (cost if complete else 0)
    assert result["reported_cost"] == subtotal
    comparison = evaluation.compare(state, "demo", base_run["id"], result["id"])
    assert comparison["reasons"] == ["candidate did not complete the whole evaluation suite"]
    assert not comparison["eligible"] and "candidate" not in comparison["averages"]
    assert comparison["reported_cost"] == .375 + subtotal and comparison["reported_cost_complete"] is complete
    with pytest.raises(ValueError, match="not eligible"):
        skills.adopt(state, "demo", base_run["id"], result["id"], 1, "Cannot adopt unevaluable candidate")
    assert skill_assets.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]


@pytest.mark.parametrize("failure", ["nonzero", "timed-out", "killed", "malformed", "missing-cost", "invalid-cost",
                                     "overflowing-cost", "duplicate-outcome", "oversized", "exception", "interrupt"])
def test_reported_cost_evaluator_failure_retains_unknown_subtotal_and_case(skill_project, monkeypatch, failure):
    state, _, _, baseline, suite = skill_project
    calls = []
    rejected = {
        "nonzero": '{"score":1,"passed":true,"cost":99,"feedback":"not an accepted report"}',
        "timed-out": '{"outcome":"unevaluable","cost":99,"feedback":"untrusted timed-out output"}',
        "killed": '{"outcome":"unevaluable","cost":99,"feedback":"untrusted killed output"}',
        "malformed": '{"cost":99',
        "missing-cost": '{"score":1,"passed":true,"feedback":"no cost"}',
        "invalid-cost": '{"score":1,"passed":true,"cost":NaN,"feedback":"invalid cost"}',
        "overflowing-cost": '{"outcome":"unevaluable","cost":1e400,"feedback":"unrepresentable cost"}',
        "duplicate-outcome": '{"outcome":"unknown","outcome":"unevaluable","cost":99,"feedback":"ambiguous"}',
        "oversized": "x" * 1_000_001,
    }
    process_status, returncode = {"nonzero": ("failed", 2), "timed-out": ("timed_out", 0), "killed": ("failed", -9)}.get(
        failure, ("succeeded", 0))

    def process(argv, cwd, output, timeout, stdin, **options):
        pending = evaluation.listing(State(state.root), "demo")["runs"][0]
        assert pending["status"] == "running" and pending["reported_cost_complete"] is False
        assert pending["reported_cost"] == (0 if not calls else .125)
        row = pending["cases"][-1]
        assert row["id"] == json.loads(stdin)["case"]["split"] and row["output"] == str(output)
        assert row["reported_cost_complete"] is False and "score" not in row and "cost" not in row
        if calls:
            assert pending["cases"][0]["cost"] == .125 and pending["cases"][0]["reported_cost_complete"] is True
        calls.append(output)
        assert len(calls) <= 2, "Incomplete reports must halt subsequent cases"
        if len(calls) == 1:
            return _reported_outcome(output, '{"score":0,"passed":false,"cost":0.125,"feedback":"wrong answer, valid cost"}')
        if failure == "interrupt":
            raise KeyboardInterrupt()
        if failure == "exception":
            raise OSError("Lost evaluator return")
        return {**_reported_outcome(output, rejected[failure], status=process_status), "returncode": returncode}

    monkeypatch.setattr(evaluation.processes, "run", process)
    if failure == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
        result = evaluation.listing(State(state.root), "demo")["runs"][0]
        assert result["status"] == "running" and "finished" not in result
    else:
        result = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
        assert result["status"] == ("timed_out" if failure == "timed-out" else "failed")
        assert evaluation.get(State(state.root), "demo", result["id"]) == result
    assert len(calls) == 2 and result["reported_cost"] == .125 and result["reported_cost_complete"] is False
    assert len(result["cases"]) == 2 and result["cases"][-1]["reported_cost_complete"] is False
    assert {"score", "passed", "cost", "outcome"}.isdisjoint(result["cases"][-1])
    expected_outcome = "running" if failure in ("exception", "interrupt") else process_status
    assert result["cases"][-1]["status"] == expected_outcome
    if failure in rejected:
        assert (calls[-1] / "stdout.txt").read_text() == rejected[failure]
        assert result["cases"][-1]["returncode"] == returncode


@pytest.mark.parametrize("cost,expected_calls,expected_status", [(0, 3, "succeeded"), (2, 1, "budget_exhausted")])
def test_reported_cost_complete_coverage_keeps_wrong_scores_and_full_overshoot(skill_project, monkeypatch,
                                                                           cost, expected_calls, expected_status):
    state, _, _, baseline, suite = skill_project
    calls = []

    def process(argv, cwd, output, timeout, stdin, **options):
        calls.append(output)
        return _reported_outcome(output, json.dumps({"score": 0, "passed": False, "cost": cost, "feedback": "wrong answer"}))

    monkeypatch.setattr(evaluation.processes, "run", process)
    result = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    assert len(calls) == expected_calls and result["status"] == expected_status
    assert result["reported_cost"] == cost * expected_calls and result["reported_cost_complete"] is True
    assert all(row["reported_cost_complete"] and row["score"] == 0 and not row["passed"] for row in result["cases"])


def test_reported_cost_before_entry_and_after_material_failure_have_distinct_coverage(skill_project, monkeypatch):
    state, _, _, baseline, suite = skill_project
    monkeypatch.setattr(evaluation.processes, "run", lambda *a, **k: pytest.fail("Expired case cannot enter evaluator"))
    expired = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"], deadline=0)
    assert expired["status"] == "timed_out" and expired["cases"] == []
    assert expired["reported_cost"] == 0 and expired["reported_cost_complete"] is True
    calls = []

    def process(argv, cwd, output, timeout, stdin, **options):
        calls.append(output)
        if len(calls) == 3:
            (Path(baseline["path"]) / "SKILL.md").write_text("Changed after reports")
        return _reported_outcome(output, '{"score":1,"passed":true,"cost":0.125,"feedback":"valid report"}')

    monkeypatch.setattr(evaluation.processes, "run", process)
    failed = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    assert failed["status"] == "failed" and "Stored skill content changed" in failed["error"]
    assert failed["reported_cost"] == .375 and failed["reported_cost_complete"] is True


@pytest.mark.parametrize("unevaluable", [False, True])
def test_reported_cost_overflow_never_persists_complete_infinity(skill_project, monkeypatch, unevaluable):
    state, _, _, baseline, original = skill_project
    manifest = {key: value for key, value in original["manifest"].items() if key not in ("file_sha256", "path_bindings")}
    manifest["max_reported_cost"] = 1e308
    suite = evaluation.register(state, "demo", manifest)
    def process(argv, cwd, output, *args, **kwargs):
        response = {"cost": 1e308, "feedback": "Finite individual report"}
        if unevaluable and output.name == "validation":
            response["outcome"] = "unevaluable"
        else:
            response.update(score=1, passed=True)
        return _reported_outcome(output, json.dumps(response))

    monkeypatch.setattr(evaluation.processes, "run", process)
    result = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    assert result["status"] == "failed" and "total is not finite" in result["error"]
    assert result["reported_cost"] == 1e308 and result["reported_cost_complete"] is False
    assert len(result["cases"]) == 2 and result["cases"][-1]["cost"] == 1e308
    assert result["cases"][-1]["status"] == "succeeded"
    if unevaluable:
        assert result["cases"][-1]["outcome"] == "unevaluable" and "score" not in result["cases"][-1]
    assert "Infinity" not in json.dumps(evaluation.get(State(state.root), "demo", result["id"]), allow_nan=False)
    with pytest.raises(ValueError, match="Combined reported cost total is not finite"):
        evaluation.compare(state, "demo", result["id"], result["id"])


def test_reported_cost_comparison_preserves_unrecorded_history_and_quality_gate(skill_project, monkeypatch):
    state, _, source, baseline, suite = skill_project
    (source / "SKILL.md").write_text((source / "SKILL.md").read_text().replace("BASELINE", "IMPROVED"))
    candidate = skill_assets.import_bundle(state, "demo", source)

    def process(argv, cwd, output, timeout, stdin, **options):
        request = json.loads(stdin)
        score = .9 if request["skill_dir"] == candidate["path"] else .5
        return _reported_outcome(output, json.dumps({"score": score, "passed": True, "cost": .125, "feedback": "report"}))

    monkeypatch.setattr(evaluation.processes, "run", process)
    base_run, candidate_run = [evaluation.evaluate(state, "demo", item["digest"], suite["digest"])
                               for item in (baseline, candidate)]
    complete = evaluation.compare(state, "demo", base_run["id"], candidate_run["id"])
    assert complete["eligible"] and complete["reported_cost_complete"] is True and complete["reported_cost"] == .75
    candidate_run.pop("reported_cost_complete")
    with state.connect() as db:
        db.execute("UPDATE evaluations SET document=? WHERE id=?", (json.dumps(candidate_run), candidate_run["id"]))
    assert evaluation.get(State(state.root), "demo", candidate_run["id"]) == candidate_run
    unrecorded = evaluation.compare(state, "demo", base_run["id"], candidate_run["id"])
    assert unrecorded["eligible"] and unrecorded["reported_cost_complete"] is False
    assert unrecorded["reported_cost"] == complete["reported_cost"]
    assert evaluation.get(State(state.root), "demo", candidate_run["id"]) == candidate_run


@pytest.mark.parametrize("failure,expected_subtotal,complete,expected_status", [
    ("nonzero", .375, False, "failed"), ("unknown", .375, False, "failed"),
    ("known", .625, True, "failed"), ("overshoot", 2.375, True, "budget_exhausted"),
])
def test_reported_cost_optimization_halts_after_partial_evaluator_report(skill_project, monkeypatch, failure,
                                                                       expected_subtotal, complete, expected_status):
    gepa = pytest.importorskip("gepa")
    state, _, _, baseline, suite = skill_project
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, "unused-proposer"]}, 1)
    calls = []

    def process(argv, cwd, output, timeout, stdin, **options):
        pending = optimization.listing(State(state.root), "demo")[0]
        assert pending["reported_cost_complete"] is False
        assert pending["reported_cost"] == (0 if not calls else .25)
        calls.append(output)
        if len(calls) == 3:
            if failure == "nonzero":
                return _reported_outcome(output, '{"score":1,"passed":true,"cost":99,"feedback":"failed output"}',
                                         status="failed")
            cost = {"unknown": None, "known": .25, "overshoot": 2}[failure]
            return _reported_outcome(output, json.dumps({"outcome": "unevaluable", "cost": cost, "feedback": "No score"}))
        return _reported_outcome(output, json.dumps({"score": .5, "passed": True, "cost": .25 if len(calls) == 1 else .125,
                                                    "feedback": "accepted report"}))

    def engine(**request):
        adapter, seed = request["adapter"], request["seed_candidate"]
        adapter.evaluate([request["trainset"][0]], seed)
        saved = optimization.listing(State(state.root), "demo")[0]
        assert saved["reported_cost_complete"] and saved["reported_cost"] == .25
        with pytest.raises(ValueError):
            adapter.evaluate([request["trainset"][0], request["valset"][0]], seed)
        for repeat in (lambda: adapter.evaluate([request["trainset"][0]], seed),
                       lambda: request["custom_candidate_proposer"](seed, {}, ["skill"])):
            with pytest.raises(ValueError, match="already terminated"):
                repeat()
        return SimpleNamespace(best_candidate=seed)

    monkeypatch.setattr(gepa, "optimize", engine)
    monkeypatch.setattr(optimization.processes, "run", process)
    result = optimization.optimize(state, "demo", baseline["digest"], suite["digest"], "Retain incomplete reports", 6, 2, 20)
    assert result["status"] == expected_status and result["reported_cost"] == expected_subtotal
    assert result["reported_cost_complete"] is complete
    assert len(calls) == 3 and result["metric_calls"] == 3 and result["proposals"] == 0
    assert len(result["evaluations"]) == 2 and optimization.listing(State(state.root), "demo")[0] == result
    last_evaluation = evaluation.get(State(state.root), "demo", result["evaluations"][-1])
    assert {"score", "passed"}.isdisjoint(last_evaluation["cases"][-1])


@pytest.mark.parametrize("failure", ["nonzero", "malformed", "invalid-cost", "interrupt", "overshoot", "overflow"])
def test_reported_cost_proposer_retains_prefix_and_unknown_on_failure(skill_project, monkeypatch, failure):
    gepa = pytest.importorskip("gepa")
    state, _, _, baseline, original = skill_project
    manifest = {key: value for key, value in original["manifest"].items() if key not in ("file_sha256", "path_bindings")}
    prefix = 1e308 if failure == "overflow" else .25
    manifest["max_reported_cost"] = 1e308 if failure == "overflow" else 1
    suite = evaluation.register(state, "demo", manifest)
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, "unused-proposer"]}, 1)
    calls = []

    def process(argv, cwd, output, timeout, stdin, **options):
        pending = optimization.listing(State(state.root), "demo")[0]
        assert pending["reported_cost_complete"] is False
        calls.append(output)
        if len(calls) == 1:
            return _reported_outcome(output, json.dumps({"score": .5, "passed": True, "cost": prefix, "feedback": "known prefix"}))
        assert len(calls) == 2 and pending["reported_cost"] == prefix and pending["proposals"] == 1
        if failure == "interrupt":
            raise KeyboardInterrupt()
        if failure == "malformed":
            raw = "{}"
        else:
            raw = json.dumps({"skill": json.loads(stdin)["candidate"]["skill"],
                              "cost": float("nan") if failure == "invalid-cost" else 1e308 if failure == "overflow" else 2})
        return _reported_outcome(output, raw, status="failed" if failure == "nonzero" else "succeeded")

    def engine(**request):
        seed = request["seed_candidate"]
        request["adapter"].evaluate([request["trainset"][0]], seed)
        with pytest.raises(ValueError):
            request["custom_candidate_proposer"](seed, {}, ["skill"])
        with pytest.raises(ValueError, match="already terminated"):
            request["adapter"].evaluate([request["trainset"][0]], seed)
        return SimpleNamespace(best_candidate=seed)

    monkeypatch.setattr(gepa, "optimize", engine)
    monkeypatch.setattr(optimization.processes, "run", process)
    result = optimization.optimize(state, "demo", baseline["digest"], suite["digest"], "Retain proposer uncertainty", 6, 2, 20)
    assert len(calls) == 2 and result["proposals"] == 1 and result["metric_calls"] == 1
    assert result["status"] == ("cancelled" if failure == "interrupt" else "budget_exhausted" if failure == "overshoot" else "failed")
    assert result["reported_cost"] == (prefix + 2 if failure == "overshoot" else prefix)
    assert result["reported_cost_complete"] is (failure == "overshoot")
    assert optimization.listing(State(state.root), "demo")[0] == result


def test_reported_cost_evaluation_subtotals_cannot_overflow_search_total(skill_project, monkeypatch):
    gepa = pytest.importorskip("gepa")
    state, _, _, baseline, original = skill_project
    manifest = {key: value for key, value in original["manifest"].items() if key not in ("file_sha256", "path_bindings")}
    manifest["max_reported_cost"] = 1e308
    suite = evaluation.register(state, "demo", manifest)
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, "unused-proposer"]}, 1)
    calls = []

    def process(argv, cwd, output, *args, **kwargs):
        calls.append(output)
        assert len(calls) <= 2
        return _reported_outcome(output, '{"score":1,"passed":true,"cost":1e308,"feedback":"finite batch cost"}')

    def engine(**request):
        seed = request["seed_candidate"]
        request["adapter"].evaluate([request["trainset"][0]], seed)
        with pytest.raises(ValueError, match="total is not finite"):
            request["adapter"].evaluate([request["valset"][0]], seed)
        with pytest.raises(ValueError, match="already terminated"):
            request["adapter"].evaluate([request["trainset"][0]], seed)
        return SimpleNamespace(best_candidate=seed)

    monkeypatch.setattr(gepa, "optimize", engine)
    monkeypatch.setattr(optimization.processes, "run", process)
    result = optimization.optimize(state, "demo", baseline["digest"], suite["digest"], "Preserve finite search total", 4, 1, 20)
    assert result["status"] == "failed" and "total is not finite" in result["error"]
    assert result["reported_cost"] == 1e308 and result["reported_cost_complete"] is False
    assert len(calls) == len(result["evaluations"]) == 2 and result["proposals"] == 0
    assert "Infinity" not in json.dumps(optimization.listing(State(state.root), "demo"), allow_nan=False)


@pytest.mark.parametrize("interrupted", [False, True])
def test_reported_cost_lost_evaluation_return_stays_unresolved(skill_project, monkeypatch, interrupted):
    gepa = pytest.importorskip("gepa")
    state, _, _, baseline, suite = skill_project
    projects.bind(state, "demo", "optimizer", {"tool": "gepa", "proposer_argv": [sys.executable, "unused-proposer"]}, 1)

    def evaluation_entry(*args, **kwargs):
        pending = optimization.listing(State(state.root), "demo")[0]
        assert pending["reported_cost_complete"] is False and pending["metric_calls"] == 1
        if interrupted:
            raise KeyboardInterrupt()
        raise OSError("Lost evaluation return")

    def engine(**request):
        request["adapter"].evaluate([request["trainset"][0]], request["seed_candidate"])

    monkeypatch.setattr(gepa, "optimize", engine)
    monkeypatch.setattr(evaluation, "evaluate", evaluation_entry)
    monkeypatch.setattr(optimization.processes, "run", lambda *a, **k: pytest.fail("Lost report must not dispatch a proposal"))
    result = optimization.optimize(state, "demo", baseline["digest"], suite["digest"], "Retain lost return", 4, 1, 20)
    assert result["status"] == ("cancelled" if interrupted else "failed")
    assert result["reported_cost"] == 0 and result["reported_cost_complete"] is False
    assert result["proposals"] == 0 and optimization.listing(State(state.root), "demo")[0] == result


@pytest.fixture
def retrospective_case(tmp_path):
    import ergora.development.handoff as handoff
    import ergora.definitions.skills as skill_assets
    import ergora.definitions.workflows as workflows
    from test_handoff import evidence, text_evidence

    repo = tmp_path / 'repo'
    subprocess.run(['git', 'init', str(repo)], check=True, capture_output=True)
    state = State(tmp_path / 'control')
    projects.create(state, 'demo', repo)
    source = tmp_path / 'source/retrospective-skill'
    source.mkdir(parents=True)
    (source / 'SKILL.md').write_bytes(b'---\nname: retrospective-skill\ndescription: Verify complete evidence\n---\nRetain uncertainty.\n')
    (source / 'references').mkdir()
    (source / 'references/evidence.md').write_bytes(('完整保留观察与未知成本。\n' * 400).encode('utf-8'))
    baseline = skill_assets.import_bundle(state, 'demo', source)
    index, blobs = text_evidence(evidence.__wrapped__(), ['Original failed observation; cost unknown.\n'])
    packet = tmp_path / 'source.zip'
    collected = handoff.create(index, lambda artifact: blobs[artifact['sha256']], packet)
    installed = workflows.install_preset(state, 'retrospective')
    root = workflows.get(state, installed['root']['id'], installed['root']['version'])['definition']
    manifest = workflows.prepare_manifest(state.root, root['id'], root['version'],
        {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}, tmp_path / 'manifest')
    return state, packet, source, baseline, {
        'packet_sha256': collected['sha256'], 'name': baseline['name'], 'digest': baseline['digest'],
        'head_revision': 1, 'objective': 'Improve evidence applicability without inventing measurements.',
        'manifest': Path(manifest['path']), 'instance': 'root/propose', 'destination': tmp_path / 'input',
        'max_prompt_bytes': 200000}


def retrospective_result(input_path, result_path):
    from copy import deepcopy

    task = json.loads((input_path / 'task.txt').read_bytes())
    artifact = task['evidence']['artifacts'][0]
    files = deepcopy(task['baseline']['files'])
    files['SKILL.md']['text'] += 'State whether each source observation generalizes to the requested task.\n'
    proposal = {'schema_version': 1, 'evidence_sha256': task['evidence']['sha256'],
        'baseline_digest': task['baseline']['digest'], 'head_revision': task['baseline']['head_revision'],
        'observations': [{'claim': 'The source records an unsuccessful observation.', 'uncertainty': 'General applicability needs evaluation.',
            'citations': [{'job_id': artifact['job_id'], 'name': artifact['artifact']['name'], 'sha256': artifact['artifact']['sha256']}]}],
        'negative_results': ['Original failed outcome retained.'], 'cost_and_uncertainty': 'Original cost is not recorded; benefit unknown.',
        'candidate': {'name': task['baseline']['name'], 'hypothesis': 'Explicit applicability reduces overgeneralization.',
            'applicability': 'Source-bound retrospectives.', 'evaluation_plan': 'Compare the same trusted suite and holdout.', 'files': files}}
    result_path.write_text(json.dumps({'summary': 'Bounded proposed improvement.', 'artifacts': {'response': json.dumps(proposal)}}))
    return proposal


def test_retrospective_freezes_full_baseline_and_rechecks_without_live_sources(retrospective_case, tmp_path):
    import ergora.improvement.retrospectives as retrospectives
    import ergora.definitions.skills as skill_assets
    import ergora.definitions.workflows as workflows

    state, packet, source, baseline, options = retrospective_case
    before = skill_assets.versions(state, 'demo')
    prepared = retrospectives.prepare(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    task = json.loads((options['destination'] / 'task.txt').read_bytes())
    frozen = workflows.inspect_input(options['destination'], material=True)
    assert prepared['digest'] == frozen['digest']
    assert task['baseline']['files']['references/evidence.md']['text'].encode('utf-8') == (source / 'references/evidence.md').read_bytes()
    assert task['evidence']['index']['temporal_status'] == 'FAILED'
    assert task['evidence']['index']['usage']['cost'] == {'state': 'not_recorded', 'value': None}
    for leaf in (item for item in frozen['composition']['instances'] if item['kind'] == 'agent'):
        assert all(resource['text'] in leaf['prompt'] for resource in leaf['resources'])
        assert not leaf['permissions']['write'] and not leaf['permissions']['shell'] and not leaf['permissions']['network']
    result_path = tmp_path / 'result.json'
    proposal = retrospective_result(options['destination'], result_path)
    packet.unlink()
    shutil.rmtree(baseline['path'])
    readback = retrospectives.inspect_input(options['destination'], project_id='demo')
    assert readback['digest'] == prepared['digest'] and readback['retrospective_request'] == task
    with pytest.raises(ValueError, match='different project'):
        retrospectives.inspect_input(options['destination'], project_id='another-project')
    checked = retrospectives.check(options['destination'], result_path)
    assert checked['request'] == task and checked['input_digest'] == prepared['digest']
    assert retrospectives.check(options['destination'], result_path, project_id='demo', input_digest=prepared['digest']) == checked
    assert checked['quality_evaluated'] is checked['adoption_authorized'] is False
    assert skill_assets.versions(state, 'demo') == before
    changed = workflows.prepare_input_from_manifest(options['manifest'], options['instance'],
        json.dumps({**task, 'objective': 'Review the same evidence for a different objective.'}).encode(),
        tmp_path / 'other-input', options['max_prompt_bytes'])
    changed_source = Path(changed['path'])
    assert retrospectives.check(changed_source, result_path)['candidate_digest'] == checked['candidate_digest']
    blocked = tmp_path / 'blocked' / baseline['name']
    for project_id, input_digest, reason in [('another-project', changed['digest'], 'different project'),
                                            ('demo', prepared['digest'], 'input differs')]:
        with pytest.raises(ValueError, match=reason):
            retrospectives.check(changed_source, result_path, project_id=project_id, input_digest=input_digest)
        with pytest.raises(ValueError, match=reason):
            retrospectives.export(changed_source, result_path, blocked, result_sha256=checked['result_sha256'],
                candidate_digest=checked['candidate_digest'], project_id=project_id, input_digest=input_digest)
        assert not blocked.exists()
    candidate_dir = tmp_path / 'candidate' / baseline['name']
    for name, file in proposal['candidate']['files'].items():
        path = candidate_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file['text'].encode('utf-8'))
        path.chmod(0o600 | file['executable_bits'])
    assert skill_assets.digest_tree(candidate_dir)[0] == checked['candidate_digest']


@pytest.mark.parametrize(('change', 'reason'), [
    ('source', 'frozen source or baseline'),
    ('baseline', 'frozen source or baseline'),
    ('citation', 'citation is absent'),
    ('path', 'portable relative path'),
    ('file-parent', 'file/directory conflict'),
    ('case-parent', 'file/directory conflict'),
    ('directory-case', 'prefixes require consistent'),
])
def test_retrospective_rejects_misbound_or_unsafe_candidate_without_partial_cli_output(retrospective_case, tmp_path, capsys, change, reason):
    import ergora.interfaces.cli as cli
    import ergora.improvement.retrospectives as retrospectives

    state, packet, source, baseline, options = retrospective_case
    retrospectives.prepare(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result_path = tmp_path / 'result.json'
    proposal = retrospective_result(options['destination'], result_path)
    if change == 'source':
        proposal['evidence_sha256'] = '0' * 64
    elif change == 'baseline':
        proposal['baseline_digest'] = '0' * 64
    elif change == 'citation':
        proposal['observations'][0]['citations'][0]['job_id'] = 'another-job'
    elif change == 'path':
        proposal['candidate']['files']['../escape'] = {'text': 'untrusted', 'executable_bits': 0}
    elif change == 'directory-case':
        proposal['candidate']['files']['References/new.txt'] = {'text': 'Conflicts with the original directory spelling.', 'executable_bits': 0}
    else:
        path = ('SKILL.md' if change == 'file-parent' else 'skill.MD') + '/child.txt'
        proposal['candidate']['files'][path] = {'text': 'Conflicts with the existing Skill file.', 'executable_bits': 0}
    result_path.write_text(json.dumps({'summary': 'Proposed.', 'artifacts': {'response': json.dumps(proposal)}}))
    unused = tmp_path / 'unused-state'
    assert cli.main(['--home', str(unused), 'retrospective', 'check', str(options['destination']), str(result_path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == '' and reason in captured.err and not unused.exists()


def test_retrospective_current_head_conflict_and_no_change_proposal(retrospective_case, tmp_path):
    import ergora.improvement.retrospectives as retrospectives
    import ergora.definitions.skills as skill_assets

    state, packet, source, baseline, options = retrospective_case
    skill_assets.rollback(state, 'demo', baseline['name'], baseline['digest'], 1, 'Explicit retained baseline revision')
    with pytest.raises(ValueError, match='Active Skill changed'):
        retrospectives.prepare(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    assert not options['destination'].exists()
    options['head_revision'] = 2
    retrospectives.prepare(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result_path = tmp_path / 'result.json'
    proposal = retrospective_result(options['destination'], result_path)
    proposal['candidate'] = None
    result_path.write_text(json.dumps({'summary': 'No justified change.', 'artifacts': {'response': json.dumps(proposal)}}))
    checked = retrospectives.check(options['destination'], result_path)
    assert checked['candidate_digest'] is None and not checked['content_changed']


def test_retrospective_accepts_crlf_metadata_without_changing_frozen_file_bytes(retrospective_case, tmp_path):
    import ergora.improvement.retrospectives as retrospectives
    import ergora.definitions.skills as skill_assets

    old_state, packet, source, old_baseline, options = retrospective_case
    for path in source.rglob('*'):
        if path.is_file():
            path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
    state = State(tmp_path / 'crlf-control')
    projects.create(state, 'demo', Path(old_state.project('demo')['repo']))
    baseline = skill_assets.import_bundle(state, 'demo', source)
    options['digest'] = baseline['digest']
    retrospectives.prepare(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    task = json.loads((options['destination'] / 'task.txt').read_bytes())
    for name, file in task['baseline']['files'].items():
        assert file['text'].encode('utf-8') == (source / name).read_bytes()
    result = tmp_path / 'result.json'
    retrospective_result(options['destination'], result)
    assert retrospectives.check(options['destination'], result)['content_changed']


def test_retrospective_checks_complete_candidate_with_nested_json_larger_than_input(retrospective_case, tmp_path):
    import ergora.improvement.retrospectives as retrospectives
    import ergora.definitions.skills as skill_assets

    old_state, packet, source, old_baseline, options = retrospective_case
    reference = '{"key":"value"}\n' * 35000
    (source / 'references/evidence.md').write_bytes(reference.encode('utf-8'))
    state = State(tmp_path / 'large-control')
    projects.create(state, 'demo', Path(old_state.project('demo')['repo']))
    baseline = skill_assets.import_bundle(state, 'demo', source)
    options.update(digest=baseline['digest'], max_prompt_bytes=1000000)
    retrospectives.prepare(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result = tmp_path / 'result.json'
    proposal = retrospective_result(options['destination'], result)
    assert result.stat().st_size > 1_048_576
    checked = retrospectives.check(options['destination'], result)
    assert checked['request']['baseline']['files']['references/evidence.md']['text'] == reference
    assert checked['agent_result']['artifacts']['response'] == json.dumps(proposal)
    assert checked['content_changed'] and not checked['quality_evaluated']


@pytest.mark.parametrize('crlf', [False, True])
def test_retrospective_exports_complete_skill_for_original_import_without_adoption(retrospective_case, tmp_path, crlf):
    import hashlib
    import ergora.improvement.retrospectives as retrospectives
    import ergora.definitions.skills as skill_assets
    import ergora.definitions.workflows as workflows

    state, packet, source, baseline, options = retrospective_case
    prepared = retrospectives.prepare(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result = tmp_path / 'result.json'
    proposal = retrospective_result(options['destination'], result)
    proposal['candidate']['files']['scripts/check.py'] = {'text': 'print("Keep this complete resource.")\n',
                                                        'executable_bits': 0 if os.name == 'nt' else 0o100}
    if crlf:
        for file in proposal['candidate']['files'].values():
            file['text'] = file['text'].replace('\n', '\r\n')
    result.write_bytes(json.dumps({'summary': 'Proposed.', 'artifacts': {'response': json.dumps(proposal)}}).encode('utf-8'))
    sha = hashlib.sha256(result.read_bytes()).hexdigest()
    checked = retrospectives.check(options['destination'], result, result_sha256=sha)
    before = skill_assets.versions(state, 'demo')
    target = tmp_path / 'export' / baseline['name']
    exported = retrospectives.export(options['destination'], result, target, result_sha256=sha,
                                     candidate_digest=checked['candidate_digest'], project_id='demo', input_digest=prepared['digest'])
    assert skill_assets.digest_tree(target)[0] == checked['candidate_digest']
    for name, file in proposal['candidate']['files'].items():
        assert (target / name).read_bytes() == file['text'].encode('utf-8')
    assert exported['result_sha256'] == sha and exported['input_digest'] == prepared['digest']
    assert exported['quality_evaluated'] is exported['adoption_authorized'] is exported['origin_authenticated'] is False
    assert skill_assets.versions(state, 'demo') == before
    imported = skill_assets.import_bundle(state, 'demo', target, 'Explicitly imported retrospective proposal')
    assert imported['digest'] == checked['candidate_digest'] and imported['parent'] == baseline['digest']
    assert skill_assets.versions(state, 'demo')['active'] == before['active']
    assert workflows.inspect_input(options['destination'])['digest'] == prepared['digest']
    assert not list(target.parent.glob('.retrospective-skill-*'))


@pytest.mark.parametrize(('case', 'reason'), [
    ('selection', 'explicitly selected digest'), ('null', 'no Skill candidate'),
    ('existing', 'new retrospective export directory'), ('input', 'frozen input directory'),
])
def test_retrospective_export_rejects_before_partial_output_or_changing_existing_files(retrospective_case, tmp_path, capsys, case, reason):
    import hashlib
    import ergora.interfaces.cli as cli
    import ergora.improvement.retrospectives as retrospectives
    import ergora.definitions.workflows as workflows

    state, packet, source, baseline, options = retrospective_case
    prepared = retrospectives.prepare(state, 'demo', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result = tmp_path / 'result.json'
    proposal = retrospective_result(options['destination'], result)
    if case == 'null':
        proposal['candidate'] = None
        result.write_bytes(json.dumps({'summary': 'No change.', 'artifacts': {'response': json.dumps(proposal)}}).encode('utf-8'))
    checked = retrospectives.check(options['destination'], result)
    target = (options['destination'] if case == 'input' else tmp_path / 'export') / baseline['name']
    if case == 'existing':
        target.mkdir(parents=True)
        (target / 'sentinel').write_bytes(b'Keep existing bytes.')
    digest = checked['candidate_digest'] if case not in ('selection', 'null') else '0' * 64
    unused = tmp_path / 'unused-state'
    assert cli.main(['--home', str(unused), 'retrospective', 'export', str(options['destination']), str(result), str(target),
        '--result-sha256', hashlib.sha256(result.read_bytes()).hexdigest(), '--candidate-digest', digest]) == 2
    captured = capsys.readouterr()
    assert captured.out == '' and reason in captured.err and not unused.exists()
    if case == 'existing':
        assert list(target.iterdir()) == [target / 'sentinel'] and (target / 'sentinel').read_bytes() == b'Keep existing bytes.'
    else:
        assert not target.exists()
    assert workflows.inspect_input(options['destination'])['digest'] == prepared['digest']
    assert not list(target.parent.glob('.retrospective-skill-*'))
