"""Optional GEPA search; generated candidates never move the active skill head."""

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import tempfile
import time
import uuid

from . import evaluation, processes, skills
from .state import State, now


def _schema(state: State):
    with state.connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS optimizations (id TEXT PRIMARY KEY, project TEXT, document TEXT)")


def listing(state: State, project_id: str) -> list[dict]:
    state.project(project_id)
    _schema(state)
    with state.connect() as db:
        return [json.loads(row[0]) for row in db.execute(
            "SELECT document FROM optimizations WHERE project=? ORDER BY rowid DESC", (project_id,))]


def optimize(state: State, project_id: str, baseline_digest: str, suite_digest: str, objective: str,
             max_evaluations: int = 20, max_proposals: int = 5, timeout: int = 300) -> dict:
    binding = state.project(project_id)["bindings"].get("optimizer", {"tool": "manual"})
    if binding["tool"] != "gepa":
        raise ValueError("Select the gepa optimizer, or import a manual candidate")
    if importlib.util.find_spec("gepa") is None:
        raise ValueError("Install the optional ergora[gepa] dependency before optimizing")
    if not objective.strip() or not 2 <= max_evaluations <= 200 or not 1 <= max_proposals <= 20 or not 1 <= timeout <= 3600:
        raise ValueError("Require objective, 2–200 metric calls, 1–20 proposals and 1–3600 seconds")
    from gepa import optimize as gepa_optimize
    from gepa.core.adapter import EvaluationBatch
    from gepa.utils.stop_condition import TimeoutStopCondition

    baseline = skills.get(state, project_id, baseline_digest)
    specification = evaluation.suite(state, project_id, suite_digest)["manifest"]
    visible = {case["id"]: case for case in specification["cases"] if case["split"] != "holdout"}
    train = [case["id"] for case in visible.values() if case["split"] == "train"]
    validation = [case["id"] for case in visible.values() if case["split"] == "validation"]
    run_id = uuid.uuid4().hex
    directory = state.root / "optimizations" / run_id
    directory.mkdir(parents=True)
    document = {"id": run_id, "project": project_id, "baseline": baseline_digest, "suite": suite_digest,
                "objective": objective, "binding": binding, "max_evaluations": max_evaluations,
                "max_proposals": max_proposals, "timeout_seconds": timeout, "started": now(), "status": "running",
                "metric_calls": 0, "proposals": 0, "reported_cost": 0.0, "evaluations": [], "candidates": [],
                "output": str(directory)}
    _schema(state)

    def persist():
        with state.connect() as db:
            db.execute("INSERT OR REPLACE INTO optimizations VALUES (?, ?, ?)", (run_id, project_id, json.dumps(document)))

    persist()
    deadline = time.monotonic() + timeout
    parents = {}
    text_versions = {}

    def check_budget(metric_calls=0):
        if document["status"] != "running":
            raise ValueError("Optimization has already terminated")
        if time.monotonic() >= deadline or document["metric_calls"] + metric_calls > max_evaluations:
            document["status"] = "budget_exhausted"
            raise ValueError("Optimization time or metric-call budget exhausted")
        if document["reported_cost"] > specification["max_reported_cost"]:
            document["status"] = "budget_exhausted"
            raise ValueError("Reported cost budget exhausted")

    class Adapter:
        propose_new_texts = None

        def evaluate(self, batch, candidate, capture_traces=False):
            check_budget(len(set(batch)))
            if not set(batch).issubset(visible):
                raise ValueError("Optimizer may only evaluate train and validation IDs")
            document["metric_calls"] += len(set(batch))
            text = candidate["skill"]
            text_sha = hashlib.sha256(text.encode()).hexdigest()
            try:
                with tempfile.TemporaryDirectory(dir=directory) as temporary:
                    bundle = Path(temporary) / baseline["name"]
                    shutil.copytree(baseline["path"], bundle)
                    (bundle / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
                    imported = skills.import_bundle(state, project_id, bundle, f"GEPA search {run_id}", parents.get(text_sha, baseline_digest))
            except (ValueError, OSError) as error:
                outputs = [{"input": visible[case_id]["input"], "feedback": str(error), "score": 0.0} for case_id in batch]
                (directory / f"invalid-{document['metric_calls']}.txt").write_text(text, encoding="utf-8", newline="\n")
            else:
                text_versions[text_sha] = imported["digest"]
                if imported["digest"] not in document["candidates"]:
                    document["candidates"].append(imported["digest"])
                remaining_cost = max(0.0, specification["max_reported_cost"] - document["reported_cost"])
                try:
                    result = evaluation.evaluate(state, project_id, imported["digest"], suite_digest, list(set(batch)), deadline, remaining_cost)
                except (ValueError, OSError) as error:
                    document.update(status="failed", error=str(error))
                    persist()
                    raise
                document["evaluations"].append(result["id"])
                document["reported_cost"] += result["reported_cost"]
                if result["status"] != "succeeded":
                    document.update(status=result["status"], error=result.get("error", "Evaluation did not complete successfully"))
                    persist()
                    raise ValueError(document["error"])
                by_id = {case["id"]: case for case in result["cases"]}
                outputs = [{"input": visible[case_id]["input"], "feedback": by_id.get(case_id, {}).get("feedback", result.get("error", result["status"])),
                            "score": by_id.get(case_id, {}).get("score", 0.0) if result["status"] == "succeeded" else 0.0}
                           for case_id in batch]
            persist()
            check_budget()
            return EvaluationBatch(outputs=outputs, scores=[row["score"] for row in outputs],
                                   trajectories=outputs if capture_traces else None, num_metric_calls=len(set(batch)))

        def make_reflective_dataset(self, candidate, eval_batch, components_to_update):
            return {component: eval_batch.trajectories for component in components_to_update}

    def propose_text(candidate, reflective_dataset, components_to_update):
        check_budget()
        if document["proposals"] >= max_proposals:
            document["status"] = "budget_exhausted"
            raise ValueError("Proposal budget exhausted")
        document["proposals"] += 1
        request = {"candidate": candidate, "feedback": reflective_dataset, "components": components_to_update,
                   "objective": objective, "response": {"skill": "complete SKILL.md text", "cost": "nonnegative reported cost"}}
        remaining = max(1, min(300, int(deadline - time.monotonic())))
        outcome = processes.run(binding["proposer_argv"], Path(state.project(project_id)["repo"]),
                                directory / f"proposal-{document['proposals']}", remaining, json.dumps(request))
        if outcome["status"] != "succeeded":
            document["status"] = outcome["status"]
            persist()
            raise ValueError("Candidate proposer did not complete successfully")
        output = Path(outcome["output"]) / "stdout.txt"
        if output.stat().st_size > 200_000:
            raise ValueError("Proposer response exceeded 200 KB")
        response = json.loads(output.read_text(encoding="utf-8"))
        cost = response["cost"]
        if not isinstance(response["skill"], str) or type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
            raise ValueError("Proposer requires complete skill text and a finite nonnegative cost")
        document["reported_cost"] += cost
        parent_sha = hashlib.sha256(candidate["skill"].encode()).hexdigest()
        parents[hashlib.sha256(response["skill"].encode()).hexdigest()] = text_versions.get(parent_sha, baseline_digest)
        persist()
        check_budget()
        return {"skill": response["skill"]}

    def propose(candidate, reflective_dataset, components_to_update):
        try:
            return propose_text(candidate, reflective_dataset, components_to_update)
        except Exception as error:
            # GEPA can retain proposal errors internally; preserve them as a terminal search outcome.
            if document["status"] == "running":
                document["status"] = "failed"
            document["error"] = str(error)
            persist()
            raise

    class FileLog:
        def log(self, message):
            with (directory / "engine.log").open("a", encoding="utf-8") as stream:
                stream.write(str(message) + "\n")

    try:
        result = gepa_optimize(
            seed_candidate={"skill": (Path(baseline["path"]) / "SKILL.md").read_text(encoding="utf-8")}, trainset=train, valset=validation,
            adapter=Adapter(), custom_candidate_proposer=propose, max_metric_calls=max_evaluations,
            stop_callbacks=[TimeoutStopCondition(timeout), lambda _: document["status"] != "running"], reflection_minibatch_size=1,
            skip_perfect_score=False, run_dir=str(directory / "gepa"), raise_on_exception=True,
            logger=FileLog(),
        )
        text_sha = hashlib.sha256(result.best_candidate["skill"].encode()).hexdigest()
        evaluation.suite(state, project_id, suite_digest)
        document.update(best_candidate=text_versions[text_sha], engine="gepa==0.1.4")
        if document["status"] == "running":
            document["status"] = "succeeded"
    except KeyboardInterrupt:
        document.update(status="cancelled")
    except Exception as error:
        # The external SDK is a job boundary: retain failures, never substitute another optimizer.
        if document["status"] == "running":
            document["status"] = "failed"
        document["error"] = str(error)
    document["finished"] = now()
    persist()
    return document
