"""Frozen evaluation inputs and candidate-bound evidence, independent of generators."""

import hashlib
import errno
import json
from pathlib import Path
import re
import time
import uuid

from . import contracts, processes, skills
from .state import State, now


def manifest_sha256(value: dict) -> str:
    """Evaluation identity retains spaced sorted UTF-8 JSON; reference uses compact JSON."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def register(state: State, project_id: str, manifest: dict) -> dict:
    project = state.project(project_id)
    contracts.validate(manifest, contracts.EVALUATION_MANIFEST, "Evaluation manifest")
    if manifest["schema_version"] != 1:
        raise ValueError("Evaluation manifest at /schema_version: requires version 1")
    argv = manifest["evaluator_argv"]
    cases = manifest["cases"]
    ids = set()
    for case in cases:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", case["id"]) or case["id"] in ids:
            raise ValueError("Each case requires a unique safe id, split, and input")
        ids.add(case["id"])
    if {case["split"] for case in cases} != {"train", "validation", "holdout"}:
        raise ValueError("Train, validation and holdout splits are required")
    argv = list(argv)
    executable = processes.resolve_program(argv[0], Path(project["repo"]))
    argv[0] = str(Path(executable).resolve())
    declared = manifest["evaluator_files"]
    resolved = {}
    for filename in declared:
        path = (Path(project["repo"]) / filename).resolve(strict=True)
        if not path.is_file():
            raise ValueError("Declared evaluator file is not a regular file")
        resolved[filename] = str(path)
    argv = [resolved.get(argument, argument) for argument in argv]
    fingerprints = {}
    file_arguments = set()
    path_bindings = {}
    for argument in argv[1:]:
        path = Path(project["repo"]) / argument
        try:
            if path.is_file():
                file_arguments.add(str(path.resolve()))
                path_bindings[str(path)] = str(path.resolve())
        except OSError as error:
            if error.errno != errno.ENAMETOOLONG:
                raise
    for filename in {argv[0], *resolved.values(), *file_arguments}:
        with Path(filename).open("rb") as stream:
            fingerprints[filename] = hashlib.file_digest(stream, "sha256").hexdigest()
    frozen = {**manifest, "evaluator_argv": argv, "file_sha256": fingerprints, "path_bindings": path_bindings}
    digest = manifest_sha256(frozen)
    document = {"project": project_id, "digest": digest, "manifest": frozen, "created": now()}
    with state.connect() as db:
        db.execute("INSERT OR IGNORE INTO evaluation_suites VALUES (?, ?, ?)", (project_id, digest, json.dumps(document)))
    return document


def suite(state: State, project_id: str, digest: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM evaluation_suites WHERE project=? AND digest=?", (project_id, digest)).fetchone()
    if row is None:
        raise ValueError("Unknown evaluation suite in this project")
    document = json.loads(row[0])
    for filename, expected_target in document["manifest"]["path_bindings"].items():
        if str(Path(filename).resolve(strict=True)) != expected_target:
            raise ValueError("Trusted evaluator path changed; register and rerun a new suite")
    for filename, expected in document["manifest"]["file_sha256"].items():
        with Path(filename).open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError("Trusted evaluator changed; register and rerun a new suite")
    return document


def listing(state: State, project_id: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        return {"suites": [json.loads(row[0]) for row in db.execute(
                    "SELECT document FROM evaluation_suites WHERE project=? ORDER BY rowid DESC", (project_id,))],
                "runs": [json.loads(row[0]) for row in db.execute(
                    "SELECT document FROM evaluations WHERE project=? ORDER BY rowid DESC", (project_id,))]}


def evaluate(state: State, project_id: str, digest: str, suite_digest: str, case_ids: list[str] | None = None,
             deadline: float | None = None, remaining_cost: float | None = None) -> dict:
    candidate = skills.get(state, project_id, digest)
    specification = suite(state, project_id, suite_digest)["manifest"]
    cost_limit = specification["max_reported_cost"]
    if remaining_cost is not None:
        cost_limit = min(cost_limit, remaining_cost)
    cases = specification["cases"]
    if case_ids is not None:
        if not case_ids or not set(case_ids).issubset({case["id"] for case in cases}):
            raise ValueError("Unknown evaluation case IDs")
        cases = [case for case in cases if case["id"] in case_ids]
    run_id = uuid.uuid4().hex
    directory = state.root / "evaluations" / run_id
    directory.mkdir(parents=True)
    (directory / "suite.json").write_text(json.dumps(specification, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    working = directory / "work"
    working.mkdir()
    document = {"id": run_id, "project": project_id, "skill": digest, "name": candidate["name"],
                "suite": suite_digest, "started": now(), "status": "running", "cases": [], "reported_cost": 0.0,
                "output": str(directory), "cost_limit": cost_limit}
    with state.connect() as db:
        db.execute("INSERT INTO evaluations VALUES (?, ?, ?)", (run_id, project_id, json.dumps(document)))
    document["status"] = "succeeded"
    for case in cases:
        try:
            timeout = specification["timeout_seconds"]
            if deadline is not None:
                timeout = min(timeout, deadline - time.monotonic())
                if timeout <= 0:
                    document["status"] = "timed_out"
                    break
            payload = json.dumps({"skill_dir": candidate["path"], "case": case["input"]})
            outcome = processes.run(specification["evaluator_argv"], working, directory / "cases" / case["id"], timeout, payload)
            row = {"id": case["id"], "split": case["split"], **outcome}
            if outcome["status"] != "succeeded":
                document["cases"].append(row)
                document["status"] = outcome["status"]
                break
            output = Path(outcome["output"]) / "stdout.txt"
            if output.stat().st_size > 1_000_000:
                raise ValueError("Evaluator JSON response exceeded 1 MB")
            result = json.loads(output.read_text(encoding="utf-8"))
            contracts.validate(result, contracts.EVALUATION_RESULT, "Evaluator result")
            cost = result["cost"]
            row.update({key: result[key] for key in ("score", "cost", "passed", "feedback")})
            document["cases"].append(row)
            document["reported_cost"] += cost
            if document["reported_cost"] > cost_limit:
                document["status"] = "budget_exhausted"
                break
        except (ValueError, KeyError, OSError) as error:
            document["status"] = "failed"
            document["error"] = f"Case {case['id']}: {error}"
            break
    try:
        skills.get(state, project_id, digest)
        suite(state, project_id, suite_digest)
    except (ValueError, OSError) as error:
        document.update(status="failed", error=str(error))
    document["finished"] = now()
    with state.connect() as db:
        db.execute("UPDATE evaluations SET document=? WHERE id=?", (json.dumps(document), run_id))
    return document


def get(state: State, project_id: str, run_id: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM evaluations WHERE project=? AND id=?", (project_id, run_id)).fetchone()
    if row is None:
        raise ValueError("Unknown evaluation run in this project")
    return json.loads(row[0])


def compare(state: State, project_id: str, baseline_run: str, candidate_run: str) -> dict:
    baseline, candidate = get(state, project_id, baseline_run), get(state, project_id, candidate_run)
    if baseline["suite"] != candidate["suite"] or baseline["name"] != candidate["name"]:
        raise ValueError("Compare the same skill name against the same frozen evaluation suite")
    specification = suite(state, project_id, candidate["suite"])["manifest"]
    for run in (baseline, candidate):
        skills.get(state, project_id, run["skill"])
    reasons = []
    if baseline["skill"] == candidate["skill"]:
        reasons.append("Candidate content is identical to the baseline")
    expected = {case["id"] for case in specification["cases"]}
    averages = {}
    for label, run in (("baseline", baseline), ("candidate", candidate)):
        if run["status"] != "succeeded" or {case["id"] for case in run["cases"]} != expected:
            reasons.append(f"{label} did not complete the whole evaluation suite")
            continue
        if label == "candidate" and not all(case["passed"] for case in run["cases"]):
            reasons.append("Candidate failed a required correctness check")
        averages[label] = {split: sum(c["score"] for c in run["cases"] if c["split"] == split) /
                          sum(c["split"] == split for c in run["cases"]) for split in ("train", "validation", "holdout")}
    if len(averages) == 2:
        if averages["candidate"]["validation"] < averages["baseline"]["validation"] + specification["minimum_gain"]:
            reasons.append("Candidate does not meet the validation improvement gate")
        if averages["candidate"]["holdout"] < averages["baseline"]["holdout"]:
            reasons.append("Candidate regressed on the holdout split")
    return {"baseline": baseline["skill"], "candidate": candidate["skill"], "suite": candidate["suite"],
            "eligible": not reasons, "reasons": reasons, "averages": averages,
            "reported_cost": baseline["reported_cost"] + candidate["reported_cost"]}
