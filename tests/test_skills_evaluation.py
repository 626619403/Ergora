import json
import os
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from ergora import evaluation, memory, optimization, projects, skills, tools
from ergora.state import State


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
    baseline = skills.import_bundle(state, "demo", source)
    return state, repo, source, baseline, suite


def test_candidate_evaluation_adoption_and_rollback(skill_project, tmp_path):
    state, repo, source, baseline, suite = skill_project
    text = (source / "SKILL.md").read_text().replace("BASELINE", "IMPROVED")
    (source / "SKILL.md").write_text(text)
    candidate = skills.import_bundle(state, "demo", source, "Improve held-out fixture score")
    assert candidate["parent"] == baseline["digest"]
    assert "BASELINE" in (Path(baseline["path"]) / "SKILL.md").read_text()
    base_run = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    candidate_run = evaluation.evaluate(state, "demo", candidate["digest"], suite["digest"])
    comparison = evaluation.compare(state, "demo", base_run["id"], candidate_run["id"])
    assert comparison["eligible"] and comparison["averages"]["candidate"]["holdout"] == .9
    skills.adopt(state, "demo", base_run["id"], candidate_run["id"], 1, "Reviewed fixture evidence")
    active = skills.versions(State(state.root), "demo")["active"][0]
    assert active["digest"] == candidate["digest"] and active["revision"] == 2
    projects.bind(state, "demo", "implementer", {"tool": "command", "argv": [sys.executable, "-c", "import sys;print(sys.stdin.read())"]}, 1)
    note = memory.save(state, "demo", "Run the project verification command", {"uri": "manual:project", "revision": "v1"})
    invocation = tools.run_agent(state, "demo", "implementer", "Use selected context", skill_names=["test-skill"], recall="verification")
    assert invocation["context"]["skills"][0]["digest"] == candidate["digest"]
    assert invocation["context"]["memories"][0]["id"] == note["id"]
    assert "IMPROVED" in Path(invocation["output"], "stdin.txt").read_text()
    with pytest.raises(ValueError, match="Active skill changed"):
        skills.adopt(state, "demo", base_run["id"], candidate_run["id"], 1, "stale")
    skills.rollback(state, "demo", "test-skill", baseline["digest"], 2, "Restore previous active skill")
    assert skills.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]
    after_rollback = tools.run_agent(state, "demo", "implementer", "Check restored context", skill_names=["test-skill"])
    assert "BASELINE" in Path(after_rollback["output"], "stdin.txt").read_text()
    target = tmp_path / "export" / "test-skill"
    skills.export(state, "demo", candidate["digest"], target)
    assert skills.digest_tree(target)[0] == candidate["digest"]
    with pytest.raises(ValueError, match="Unknown skill"):
        skills.get(state, "other", candidate["digest"])


def test_holdout_regression_partial_evidence_and_mutation_are_rejected(skill_project):
    state, repo, source, baseline, suite = skill_project
    (source / "SKILL.md").write_text((source / "SKILL.md").read_text().replace("BASELINE", "IMPROVED REGRESS"))
    candidate = skills.import_bundle(state, "demo", source)
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
        skills.get(state, "demo", candidate["digest"])


def test_missing_selected_asset_is_rejected_before_agent_or_evaluator_runs(skill_project):
    state, _, _, baseline, suite = skill_project
    Path(baseline["path"], "SKILL.md").unlink()
    with pytest.raises(ValueError, match="content changed"):
        tools.run_agent(state, "demo", "implementer", "Use selected context", skill_names=["test-skill"])
    with pytest.raises(ValueError, match="content changed"):
        evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    assert tools.runs(state, "demo") == []
    assert evaluation.listing(state, "demo")["runs"] == []


def test_skill_import_recovers_unregistered_partial_tree_and_preserves_valid_publication(skill_project):
    state, _, source, _, _ = skill_project
    (source / "reference.txt").write_text("Complete resource\n")
    digest, _ = skills.digest_tree(source)
    destination = state.root / "skills" / "other" / digest / source.name
    destination.mkdir(parents=True)
    shutil.copy2(source / "SKILL.md", destination / "SKILL.md")

    imported = skills.import_bundle(state, "other", source)
    assert skills.get(state, "other", digest) == imported
    assert (destination / "reference.txt").read_bytes() == (source / "reference.txt").read_bytes()
    timestamps = {p.name: p.stat().st_mtime_ns for p in destination.iterdir()}
    assert skills.import_bundle(state, "other", source, "Repeated import") == imported
    assert {p.name: p.stat().st_mtime_ns for p in destination.iterdir()} == timestamps
    stored = skills.versions(state, "other")
    assert len(stored["versions"]) == len(stored["active"]) == len(stored["history"]) == 1


@pytest.mark.parametrize("boundary", ["copy", "publication"])
def test_interrupted_skill_import_retries_without_partial_registration(skill_project, monkeypatch, boundary):
    state, _, source, _, _ = skill_project
    (source / "reference.txt").write_text("Complete resource\n")
    digest, _ = skills.digest_tree(source)
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
            skills.import_bundle(state, "other", source)
    assert skills.versions(state, "other") == {"versions": [], "active": [], "history": []}
    assert destination.exists() == (boundary == "publication")
    imported = skills.import_bundle(state, "other", source)
    assert skills.get(state, "other", digest) == imported
    stored = skills.versions(state, "other")
    assert len(stored["versions"]) == len(stored["active"]) == len(stored["history"]) == 1


@pytest.mark.parametrize("damage", ["modified", "missing"])
def test_skill_import_refuses_to_replace_registered_evidence(skill_project, damage):
    state, _, source, baseline, _ = skill_project
    destination = Path(baseline["path"])
    if damage == "modified":
        (destination / "SKILL.md").write_text("Changed evidence\n")
    else:
        shutil.rmtree(destination)
    before = skills.versions(state, "demo")
    with pytest.raises(ValueError, match="content changed"):
        skills.import_bundle(state, "demo", source)
    assert skills.versions(state, "demo") == before
    if damage == "modified":
        assert (destination / "SKILL.md").read_text() == "Changed evidence\n"
    else:
        assert not destination.exists()


def test_concurrent_skill_imports_publish_one_complete_version(skill_project, tmp_path):
    state, _, source, _, _ = skill_project
    (source / "reference.txt").write_text("Complete resource\n" * 10000)
    digest, _ = skills.digest_tree(source)
    start = tmp_path / "start"
    script = """import json,sys,time
from pathlib import Path
from ergora import skills
from ergora.state import State
state = State(Path(sys.argv[1]))
Path(sys.argv[3]).touch()
while not Path(sys.argv[4]).exists():
    time.sleep(.01)
print(json.dumps(skills.import_bundle(state, 'other', Path(sys.argv[2]))))
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
    assert skills.get(state, "other", digest) == results[0]
    stored = skills.versions(state, "other")
    assert len(stored["versions"]) == len(stored["active"]) == len(stored["history"]) == 1


def test_adoption_rejects_evidence_from_a_different_suite(skill_project):
    state, _, source, baseline, suite = skill_project
    (source / "SKILL.md").write_text((source / "SKILL.md").read_text().replace("BASELINE", "IMPROVED"))
    candidate = skills.import_bundle(state, "demo", source)
    manifest = {key: value for key, value in suite["manifest"].items() if key not in ("file_sha256", "path_bindings")}
    manifest["minimum_gain"] = .2
    other_suite = evaluation.register(state, "demo", manifest)
    base_run = evaluation.evaluate(state, "demo", baseline["digest"], suite["digest"])
    candidate_run = evaluation.evaluate(state, "demo", candidate["digest"], other_suite["digest"])
    with pytest.raises(ValueError, match="same frozen evaluation suite"):
        skills.adopt(state, "demo", base_run["id"], candidate_run["id"], 1, "Different evidence")
    assert skills.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]


def test_skill_symlinks_and_malformed_evaluator_output_fail_visibly(skill_project):
    state, repo, source, baseline, suite = skill_project
    source.joinpath("secret-link").symlink_to(repo / "evaluate.py")
    with pytest.raises(ValueError, match="symlinks"):
        skills.import_bundle(state, "demo", source)
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
    assert skills.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]
    assert "SECRET_HELDOUT_VALUE" not in repo.joinpath("seen-proposer.json").read_text()
    for run_id in result["evaluations"]:
        assert all(c["split"] != "holdout" for c in evaluation.get(state, "demo", run_id)["cases"])


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
    nonexecutable = skills.import_bundle(state, "demo", source)
    script.chmod(0o700)
    executable = skills.import_bundle(state, "demo", source)
    assert executable["digest"] != nonexecutable["digest"]
    Path(executable["path"], "run.sh").chmod(0o600)
    with pytest.raises(ValueError, match="content changed"):
        skills.get(state, "demo", executable["digest"])
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
    assert skills.versions(state, "demo")["active"][0]["digest"] == baseline["digest"]


@pytest.fixture
def retrospective_case(tmp_path):
    from ergora import handoff, skill_assets, workflow_definitions as workflows
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
    from ergora import retrospectives, skill_assets, workflow_definitions as workflows

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
    checked = retrospectives.check(options['destination'], result_path)
    assert checked['request'] == task and checked['input_digest'] == prepared['digest']
    assert checked['quality_evaluated'] is checked['adoption_authorized'] is False
    assert skill_assets.versions(state, 'demo') == before
    candidate_dir = tmp_path / 'candidate' / baseline['name']
    for name, file in proposal['candidate']['files'].items():
        path = candidate_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file['text'].encode('utf-8'))
        path.chmod(0o600 | file['executable_bits'])
    assert skills.digest_tree(candidate_dir)[0] == checked['candidate_digest']


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
    from ergora import cli, retrospectives

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
    from ergora import retrospectives, skill_assets

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
    from ergora import retrospectives, skill_assets

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
    from ergora import retrospectives, skill_assets

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
    from ergora import retrospectives, skill_assets, workflow_definitions as workflows

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
                                     candidate_digest=checked['candidate_digest'])
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
    from ergora import cli, retrospectives, workflow_definitions as workflows

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
