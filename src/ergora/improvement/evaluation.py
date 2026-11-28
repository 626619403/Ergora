"""Frozen evaluation inputs and candidate-bound evidence, independent of generators."""

from decimal import Decimal
import hashlib
import errno
import json
import math
from pathlib import Path
import re
import time
import uuid

import ergora.definitions.skills as skill_assets
from ergora.agents import native_sources
from ergora.configuration import validation as contracts
from ergora.definitions.bundles import parse_json
from ergora.runtime import processes
from ergora.storage.state import State, now


def manifest_sha256(value: dict) -> str:
    """Evaluation identity retains spaced sorted UTF-8 JSON; reference uses compact JSON."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _normalize_case_input(value):
    """Compare numeric values as serialized JSON while preserving nonnumeric types."""
    if isinstance(value, dict):
        return {key: _normalize_case_input(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_case_input(item) for item in value]
    if type(value) is float and value.is_integer():
        return int(Decimal(str(value)))
    return value


def split_overlap(cases: list[dict]) -> str | None:
    """Return the first shared input or declared lineage across evaluation splits."""
    owners = {}
    for case in cases:
        keys = [("input", manifest_sha256({"input": _normalize_case_input(case["input"])}))]
        if "lineage" in case:
            keys.append(("lineage", case["lineage"]))
        for kind, identity in keys:
            first = owners.setdefault((kind, identity), case)
            if case["split"] != first["split"]:
                return (f"Evaluation split overlap for {kind} between case {first['id']} "
                        f"({first['split']}) and case {case['id']} ({case['split']})")
    return None


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
    if overlap := split_overlap(cases):
        raise ValueError(overlap)
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
    if (not isinstance(document, dict) or document.get("project") != project_id
            or document.get("digest") != digest or not isinstance(document.get("manifest"), dict)
            or manifest_sha256(document["manifest"]) != digest):
        raise ValueError("Saved evaluation suite differs from its registered digest or project")
    manifest = document["manifest"]
    for filename, expected_target in manifest["path_bindings"].items():
        if str(Path(filename).resolve(strict=True)) != expected_target:
            raise ValueError("Trusted evaluator path changed; register and rerun a new suite")
    for filename, expected in manifest["file_sha256"].items():
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


def _suite_snapshot(manifest: dict) -> bytes:
    return json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")


def _read_result(directory: Path, expected_identity: dict | None) -> tuple[dict, dict | None, str]:
    try:
        raw = native_sources.artifact(directory, "stdout.txt", 1_000_000)
    except native_sources.ArtifactCapacityError as error:
        raise ValueError("Evaluator JSON response exceeded 1 MB") from error
    try:
        # The schema checks consumed numbers and leaves scored metadata opaque.
        result = parse_json(raw.decode("utf-8"), "Evaluator result")
    except RecursionError as error:
        raise ValueError("Evaluator JSON response is too deeply nested") from error
    identity = None
    if expected_identity is not None and isinstance(result, dict):
        identity = result.pop("execution_identity", None)
    contracts.validate(result, contracts.EVALUATION_RESULT, "Evaluator result")
    if identity is not None:
        contracts.validate(identity, contracts.EVALUATION_MANIFEST["properties"]["execution_identity"],
                           "Reported evaluator execution identity")
    return result, identity, hashlib.sha256(raw).hexdigest()


def evaluate(state: State, project_id: str, digest: str, suite_digest: str, case_ids: list[str] | None = None,
             deadline: float | None = None, remaining_cost: float | None = None, *,
             unreserved_metric_calls: int | None = None) -> dict:
    candidate = skill_assets.get(state, project_id, digest)
    specification = suite(state, project_id, suite_digest)["manifest"]
    expected_identity = specification.get("execution_identity")
    cost_limit = specification["max_reported_cost"]
    if remaining_cost is not None:
        cost_limit = min(cost_limit, remaining_cost)
    cases = specification["cases"]
    if case_ids is not None:
        if not case_ids or not set(case_ids).issubset({case["id"] for case in cases}):
            raise ValueError("Unknown evaluation case IDs")
        cases = [case for case in cases if case["id"] in case_ids]
    snapshot = specification
    if len(cases) < len(specification["cases"]):
        snapshot = {**specification, "cases": cases, "partial": True, "suite_digest": suite_digest}
    run_id = uuid.uuid4().hex
    directory = state.root / "evaluations" / run_id
    directory.mkdir(parents=True)
    (directory / "suite.json").write_bytes(_suite_snapshot(snapshot))
    working = directory / "work"
    working.mkdir()
    document = {"id": run_id, "project": project_id, "skill": digest, "name": candidate["name"],
                "suite": suite_digest, "started": now(), "status": "running", "cases": [], "reported_cost": 0.0,
                "reported_cost_complete": True, "output": str(directory), "cost_limit": cost_limit}
    if expected_identity is not None:
        document["expected_execution_identity"] = expected_identity
    with state.connect() as db:
        db.execute("INSERT INTO evaluations VALUES (?, ?, ?)", (run_id, project_id, json.dumps(document)))

    def persist():
        with state.connect() as db:
            db.execute("UPDATE evaluations SET document=? WHERE id=?", (json.dumps(document), run_id))

    for index, case in enumerate(cases):
        row = None
        try:
            current = time.monotonic()
            call_deadline = current + specification["timeout_seconds"]
            if deadline is not None:
                call_deadline = min(call_deadline, deadline)
            timeout = call_deadline - current
            if timeout <= 0:
                document["status"] = "timed_out"
                break
            payload = json.dumps({"skill_dir": candidate["path"], "case": case["input"], "budget": {
                "deadline_monotonic": call_deadline, "remaining_seconds": timeout,
                "remaining_reported_cost": max(0.0, cost_limit - document["reported_cost"]),
                "remaining_batch_calls": len(cases) - index,
                "unreserved_metric_calls": unreserved_metric_calls}})
            case_output = directory / "cases" / case["id"]
            row = {"id": case["id"], "split": case["split"], "status": "running", "output": str(case_output),
                   "stdin_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                   "reported_cost_complete": False}
            document["cases"].append(row)
            document["reported_cost_complete"] = False
            persist()
            outcome = processes.run(specification["evaluator_argv"], working, case_output,
                                    timeout, payload, deadline=call_deadline)
            row.update(outcome)
            if outcome["status"] != "succeeded":
                document["status"] = outcome["status"]
                break
            result, observed_identity, result_sha256 = _read_result(Path(outcome["output"]), expected_identity)
            row["stdout_sha256"] = result_sha256
            cost = result["cost"]
            countable_cost = cost
            identity_mismatch = False
            if expected_identity is not None:
                row["execution_identity"] = observed_identity
                identity_mismatch = observed_identity != expected_identity
                if observed_identity is None or observed_identity["cost_unit"] != expected_identity["cost_unit"]:
                    countable_cost = None
            unevaluable = identity_mismatch or result.get("outcome") == "unevaluable"
            row.update(cost=cost, feedback=result["feedback"], reported_cost_complete=countable_cost is not None)
            if identity_mismatch:
                row["error"] = "Reported evaluator execution identity differs from the frozen suite"
            if unevaluable:
                row["outcome"] = "unevaluable"
            else:
                row.update(score=result["score"], passed=result["passed"])
            if countable_cost is not None:
                total = document["reported_cost"] + countable_cost
                if not math.isfinite(total):
                    raise ValueError("Reported cost total is not finite")
                document.update(reported_cost=total, reported_cost_complete=True)
            if document["reported_cost"] > cost_limit:
                document["status"] = "budget_exhausted"
            elif identity_mismatch:
                document.update(status="failed", error=f"Case {case['id']}: {row['error']}")
            elif unevaluable:
                document.update(status="failed", error=f"Case {case['id']}: evaluator returned an unevaluable result")
            persist()
            if document["status"] != "running":
                break
        except (ValueError, KeyError, OSError) as error:
            document["status"] = "failed"
            document["error"] = f"Case {case['id']}: {error}"
            if row is not None:
                row["error"] = str(error)
            break
    else:
        document["status"] = "succeeded"
    try:
        skill_assets.get(state, project_id, digest)
        suite(state, project_id, suite_digest)
    except (ValueError, OSError) as error:
        document.update(status="failed", error=str(error))
    document["finished"] = now()
    persist()
    return document


def get(state: State, project_id: str, run_id: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM evaluations WHERE project=? AND id=?", (project_id, run_id)).fetchone()
    if row is None:
        raise ValueError("Unknown evaluation run in this project")
    return json.loads(row[0])


def _check_evaluation_input(row: dict, directory: Path, skill_path: str, case: dict) -> None:
    expected = {"skill_dir": skill_path, "case": case["input"]}
    # The original request adds a bounded set of per-call budget fields to these inputs.
    limit = len(json.dumps(expected).encode("utf-8")) + 4096
    raw = native_sources.artifact(directory, "stdin.txt", limit)
    if "stdin_sha256" in row and hashlib.sha256(raw).hexdigest() != row["stdin_sha256"]:
        raise ValueError(f"case {case['id']} request differs from its recorded digest")
    observed = parse_json(raw.decode("utf-8"), "Evaluator request")
    if not isinstance(observed, dict) or expected.keys() - observed.keys() or manifest_sha256(
            {name: observed[name] for name in expected}) != manifest_sha256(expected):
        raise ValueError(f"case {case['id']} request differs from the frozen Skill or case input")


def _check_evaluation_archive(run: dict, specification: dict, skill_path: str) -> None:
    cases = specification["cases"]
    expected = [(case["id"], case["split"]) for case in cases]
    if [(case["id"], case["split"]) for case in run["cases"]] != expected:
        raise ValueError("recorded cases or splits differ from the full evaluation suite")
    directory = Path(run["output"])
    if directory.name != run["id"] or directory.parent.name != "evaluations":
        raise ValueError("archive path differs from the original evaluation")
    raw = native_sources.artifact(directory, "suite.json", len(_suite_snapshot(specification)))
    snapshot = parse_json(raw.decode("utf-8"), "Evaluation suite snapshot")
    if manifest_sha256(snapshot) != run["suite"]:
        raise ValueError("archived suite differs from the registered manifest")
    expected_identity = specification.get("execution_identity")
    for row, case in zip(run["cases"], cases):
        case_id = row["id"]
        case_directory = directory / "cases" / case_id
        if (Path(row["output"]) != case_directory or row.get("status") != "succeeded"
                or row.get("returncode") != 0):
            raise ValueError(f"case {case_id} lacks a matching completed output")
        _check_evaluation_input(row, case_directory, skill_path, case)
        result, identity, result_sha = _read_result(case_directory, expected_identity)
        if row.get("stdout_sha256", result_sha) != result_sha:
            raise ValueError(f"case {case_id} output differs from its recorded digest")
        if expected_identity is not None and (identity != expected_identity or row.get("execution_identity") != identity):
            raise ValueError(f"case {case_id} evaluator execution identity differs from the frozen suite")
        if result.get("outcome") == "unevaluable" or any(
                type(row.get(field)) is not type(result[field]) or row[field] != result[field]
                for field in ("score", "passed", "cost", "feedback")):
            raise ValueError(f"case {case_id} summary differs from the original evaluator result")


def compare(state: State, project_id: str, baseline_run: str, candidate_run: str) -> dict:
    baseline, candidate = get(state, project_id, baseline_run), get(state, project_id, candidate_run)
    if baseline["suite"] != candidate["suite"] or baseline["name"] != candidate["name"]:
        raise ValueError("Compare the same skill name against the same frozen evaluation suite")
    specification = suite(state, project_id, candidate["suite"])["manifest"]
    expected_identity = specification.get("execution_identity")
    skill_paths = {run["skill"]: skill_assets.get(state, project_id, run["skill"])["path"]
                   for run in (baseline, candidate)}
    reasons = []
    if overlap := split_overlap(specification["cases"]):
        reasons.append(overlap)
    if baseline["skill"] == candidate["skill"]:
        reasons.append("Candidate content is identical to the baseline")
    averages = {}
    for label, run_id, run in (("baseline", baseline_run, baseline), ("candidate", candidate_run, candidate)):
        if run.get("id") != run_id or run.get("project") != project_id:
            reasons.append(f"{label} evaluation identity differs from the selected run")
            continue
        if run.get("status") != "succeeded":
            reasons.append(f"{label} did not complete the whole evaluation suite")
            continue
        try:
            _check_evaluation_archive(run, specification, skill_paths[run["skill"]])
        except (KeyError, TypeError, ValueError, OSError, RecursionError) as error:
            reasons.append(f"{label} original evaluation evidence could not be verified: {error}")
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
    reported_cost = baseline["reported_cost"] + candidate["reported_cost"]
    if not math.isfinite(reported_cost):
        raise ValueError("Combined reported cost total is not finite")
    return {"baseline": baseline["skill"], "candidate": candidate["skill"], "suite": candidate["suite"],
            "eligible": not reasons, "reasons": reasons, "averages": averages,
            "reported_cost": reported_cost,
            "reported_cost_complete": all(run.get("reported_cost_complete") is True for run in (baseline, candidate)),
            **({"execution_identity": expected_identity} if expected_identity is not None else {})}
