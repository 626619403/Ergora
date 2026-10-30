#!/usr/bin/env python3
"""Paired-run performance screening. Standard library only; never quality approval.

Usage: python compare_runs.py comparison.json [--output result.json]
       python compare_runs.py --self-test
Input contract and limitations are documented in measurement.md.
"""

import argparse
import copy
import hashlib
import json
import math
import random
import re
import statistics
import sys
import unittest
from pathlib import Path


def finite_number(value, name, *, positive=False, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: expected a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{name}: expected a finite number")
    if positive and value <= 0:
        raise ValueError(f"{name}: must be positive")
    if nonnegative and value < 0:
        raise ValueError(f"{name}: must be nonnegative")
    return float(value)


def positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name}: expected a positive integer")
    return value


def quantile(sorted_values, probability):
    position = (len(sorted_values) - 1) * probability
    left = math.floor(position)
    right = math.ceil(position)
    return sorted_values[left] + (sorted_values[right] - sorted_values[left]) * (position - left)


def summarize(rows, normalization):
    # Each row is one matched, independent replicate. Each arm is a complete
    # global completion window, not one rank and not one per-update sample.
    b_seconds = sum(row[0] for row in rows)
    c_seconds = sum(row[1] for row in rows)
    samples = sum(row[2] for row in rows)
    return {
        "baseline_source_samples_per_second": samples / b_seconds,
        "candidate_source_samples_per_second": samples / c_seconds,
        "baseline_seconds_at_normalization": normalization * b_seconds / samples,
        "candidate_seconds_at_normalization": normalization * c_seconds / samples,
        "saved_seconds_at_normalization": normalization * (b_seconds - c_seconds) / samples,
        "speedup_ratio": b_seconds / c_seconds,
        "speedup_percent": 100.0 * (b_seconds / c_seconds - 1.0),
        "time_reduction_percent": 100.0 * (1.0 - c_seconds / b_seconds),
    }


def compare(document, input_sha256=None):
    if document.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if document.get("independent_unit") != "paired_run":
        raise ValueError("independent_unit must be paired_run; correlated windows are not IID runs")
    if not document.get("workload_fingerprint"):
        raise ValueError("workload_fingerprint is required")
    if not isinstance(document.get("experiment_id"), str) or not document["experiment_id"]:
        raise ValueError("experiment_id is required")
    if not re.fullmatch(r"[0-9a-f]{64}", document.get("manifest_sha256", "")):
        raise ValueError("manifest_sha256 must be the lowercase SHA256 of the experiment manifest")
    normalization = positive_int(document.get("normalization_source_samples", 1), "normalization_source_samples")
    settings = document.get("statistics", {})
    min_pairs = positive_int(settings.get("min_pairs", 8), "statistics.min_pairs")
    if min_pairs < 4:
        raise ValueError("min_pairs must be at least 4; this floor is a screening policy, not a precision guarantee")
    resamples = positive_int(settings.get("bootstrap_resamples", 10000), "statistics.bootstrap_resamples")
    if resamples < 1000:
        raise ValueError("bootstrap_resamples must be at least 1000")
    confidence = finite_number(settings.get("confidence", 0.95), "statistics.confidence")
    if not 0.5 < confidence < 1.0:
        raise ValueError("confidence must be between 0.5 and 1")
    seed = settings.get("seed", 20261026)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("statistics.seed must be an integer")
    thresholds = document.get("thresholds", {})
    absolute = thresholds.get("min_saved_seconds_at_normalization", 0.0)
    relative = thresholds.get("min_speedup_percent", None)
    absolute = None if absolute is None else finite_number(absolute, "absolute threshold", nonnegative=True)
    relative = None if relative is None else finite_number(relative, "relative threshold", nonnegative=True)
    if absolute is None and relative is None:
        raise ValueError("at least one practical threshold must be enabled")
    if absolute is not None and relative is not None and "mode" not in thresholds:
        raise ValueError("thresholds.mode must explicitly specify all or any when both thresholds are enabled")
    rule = thresholds.get("mode", "all")
    if rule not in ("all", "any"):
        raise ValueError("thresholds.mode must be all or any")

    pairs = document.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("pairs must contain one or more paired runs")
    rows, pair_ids, run_ids, orders = [], set(), set(), set()
    pair_fingerprints = []
    fingerprint_fields = ("matched_input_fingerprint", "environment_fingerprint", "initial_checkpoint_sha256")
    code_hashes = {"baseline": set(), "candidate": set()}
    for index, pair in enumerate(pairs):
        pair_id = pair.get("pair_id")
        if not isinstance(pair_id, str) or not pair_id or pair_id in pair_ids:
            raise ValueError(f"pair {index}: missing or duplicated pair_id")
        pair_ids.add(pair_id)
        if pair.get("order") not in ("AB", "BA"):
            raise ValueError(f"{pair_id}: order must be AB or BA")
        orders.add(pair["order"])
        arms = []
        fingerprints = {}
        for side in ("baseline", "candidate"):
            arm = pair.get(side, {})
            run_id = arm.get("run_id")
            if not isinstance(run_id, str) or not run_id or run_id in run_ids:
                raise ValueError(f"{pair_id}/{side}: missing or reused run_id")
            run_ids.add(run_id)
            code_sha = arm.get("code_sha", "")
            if not isinstance(code_sha, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", code_sha):
                raise ValueError(f"{pair_id}/{side}: code_sha must be a full Git SHA or source bundle SHA256")
            code_hashes[side].add(code_sha)
            fingerprints[side] = {}
            for field in fingerprint_fields:
                value = arm.get(field, "")
                if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                    raise ValueError(f"{pair_id}/{side}/{field}: expected a lowercase SHA256 fingerprint")
                fingerprints[side][field] = value
            if arm.get("measurement_mode") != "unprofiled":
                raise ValueError(f"{pair_id}/{side}: measured run must be unprofiled")
            if arm.get("aggregation") != "global_completion_window":
                raise ValueError(f"{pair_id}/{side}: expected global_completion_window")
            elapsed = finite_number(arm.get("elapsed_seconds"), f"{pair_id}/{side}/elapsed_seconds", positive=True)
            samples = positive_int(arm.get("source_samples"), f"{pair_id}/{side}/source_samples")
            arms.append((elapsed, samples))
        if arms[0][1] != arms[1][1]:
            raise ValueError(f"{pair_id}: baseline/candidate must process the same number of source samples")
        if fingerprints["baseline"] != fingerprints["candidate"]:
            raise ValueError(f"{pair_id}: baseline/candidate input, environment and initial-checkpoint fingerprints must match")
        pair_fingerprints.append({"pair_id": pair_id, **fingerprints["baseline"]})
        rows.append((arms[0][0], arms[1][0], arms[0][1]))
    if any(len(hashes) != 1 for hashes in code_hashes.values()):
        raise ValueError("Each arm must use one fixed code hash across all pairs")

    point = summarize(rows, normalization)
    output = {
        "schema_version": 1,
        "comparison_id": document.get("comparison_id"),
        "experiment_id": document["experiment_id"],
        "input_sha256": input_sha256,
        "manifest_sha256": document["manifest_sha256"],
        "code_hashes": {side: next(iter(hashes)) for side, hashes in code_hashes.items()},
        "matched_pair_fingerprints": pair_fingerprints,
        "workload_fingerprint": document["workload_fingerprint"],
        "independent_pairs": len(rows),
        "n_pairs": len(rows),
        "status": "INCONCLUSIVE",
        "estimated_saving_ms": point["saved_seconds_at_normalization"] * 1000.0,
        "estimated_speedup_percent": point["speedup_percent"],
        "saving_ms_ci": None,
        "speedup_percent_ci": None,
        "normalization_source_samples": normalization,
        "point_estimates": point,
        "paired_savings_seconds_at_normalization": [normalization * (b-c)/n for b,c,n in rows],
        "median_paired_saving_seconds_at_normalization": statistics.median(normalization * (b-c)/n for b,c,n in rows),
        "confidence_intervals": None,
        "thresholds": {"min_saved_seconds_at_normalization": absolute, "min_speedup_percent": relative, "mode": rule},
        "performance_screen": "INCONCLUSIVE",
        "p99_assessment": {"status": "INSUFFICIENT_EVIDENCE", "certified": False,
                           "reason": "Run aggregates cannot identify update-latency P99 or throughput lower tails."},
        "quality_assessment": "NOT_EVALUATED",
        "promotion_approved": False,
        "warnings": [
            "Independence, matching inputs, hardware isolation and manifest provenance are caller obligations; this program cannot establish them.",
            "Percentile paired bootstrap is an approximate fixed-sample screen, not a formal guarantee or a valid optional-stopping/multiple-search correction.",
            "Repeated windows from one training job must be aggregated into one run; do not reuse a baseline run across supposedly independent pairs.",
            "No correctness, quality, memory, long-run reliability or P99 gate is approved by this result.",
        ],
    }
    if len(rows) < min_pairs:
        output["reason"] = f"Only {len(rows)} independent pairs; configured minimum is {min_pairs}. Descriptive results only."
        return output
    if len(orders) < 2:
        output["reason"] = "Only one execution order is represented; AB and BA confirmation pairs are required by this screening policy."
        return output

    rng = random.Random(seed)
    keys = ("saved_seconds_at_normalization", "speedup_percent", "time_reduction_percent")
    distributions = {key: [] for key in keys}
    for _ in range(resamples):
        replicate = summarize([rows[rng.randrange(len(rows))] for _ in rows], normalization)
        for key in keys:
            distributions[key].append(replicate[key])
    tail = (1.0 - confidence) / 2.0
    intervals = {}
    for key in keys:
        values = sorted(distributions[key])
        intervals[key] = {"low": quantile(values, tail), "high": quantile(values, 1.0-tail)}
    output["confidence_intervals"] = {"method": "paired_run_percentile_bootstrap", "confidence": confidence,
                                      "resamples": resamples, "seed": seed, "metrics": intervals}
    output["saving_ms_ci"] = [intervals["saved_seconds_at_normalization"][key] * 1000 for key in ("low", "high")]
    output["speedup_percent_ci"] = [intervals["speedup_percent"][key] for key in ("low", "high")]
    enabled = []
    if absolute is not None:
        enabled.append(("saved_seconds_at_normalization", absolute))
    if relative is not None:
        enabled.append(("speedup_percent", relative))
    combine = all if rule == "all" else any
    # Strict inequality also ensures positive evidence when threshold is zero.
    lower_pass = combine(intervals[key]["low"] > limit for key, limit in enabled)
    upper_could_pass = combine(intervals[key]["high"] > limit for key, limit in enabled)
    if lower_pass:
        output["performance_screen"] = "PERFORMANCE_SCREEN_PASS"
        output["status"] = "PASS"
        output["reason"] = "Lower interval bounds exceed the configured practical thresholds; other gates remain pending."
    elif not upper_could_pass:
        output["performance_screen"] = "PERFORMANCE_SCREEN_REJECT"
        output["status"] = "FAIL"
        output["reason"] = "Even upper interval bounds do not exceed the configured practical thresholds."
    else:
        output["reason"] = "Intervals overlap at least one required threshold; collect a preplanned independent confirmation set or stop."
    return output


def example(pair_count=8, factor=0.9):
    pairs = []
    for i in range(pair_count):
        baseline = 100.0 + (i % 4)
        common = {"source_samples": 1000, "measurement_mode": "unprofiled", "aggregation": "global_completion_window",
                  "matched_input_fingerprint": "1"*64, "environment_fingerprint": "2"*64,
                  "initial_checkpoint_sha256": "3"*64}
        pairs.append({"pair_id": str(i), "order": "AB" if i % 2 == 0 else "BA", "baseline": {**common, "run_id": f"b{i}", "code_sha": "a"*40, "elapsed_seconds": baseline},
                      "candidate": {**common, "run_id": f"c{i}", "code_sha": "b"*40, "elapsed_seconds": baseline*factor}})
    return {"schema_version": 1, "experiment_id": "synthetic-example-not-a-real-experiment", "manifest_sha256": "0"*64,
            "comparison_id": "synthetic-example", "workload_fingerprint": "example",
            "independent_unit": "paired_run", "normalization_source_samples": 1000,
            "statistics": {"min_pairs": 8, "bootstrap_resamples": 1000, "seed": 17},
            "thresholds": {"min_saved_seconds_at_normalization": 1.0, "min_speedup_percent": 1.0, "mode": "all"}, "pairs": pairs}


class ComparisonTests(unittest.TestCase):
    def test_known_speedup_and_no_quality_approval(self):
        result = compare(example())
        self.assertEqual(result["performance_screen"], "PERFORMANCE_SCREEN_PASS")
        self.assertAlmostEqual(result["point_estimates"]["speedup_percent"], 100/9)
        self.assertAlmostEqual(result["point_estimates"]["time_reduction_percent"], 10)
        self.assertFalse(result["promotion_approved"])
        self.assertFalse(result["p99_assessment"]["certified"])

    def test_one_pair_is_inconclusive(self):
        result = compare(example(1))
        self.assertEqual(result["performance_screen"], "INCONCLUSIVE")
        self.assertIsNone(result["confidence_intervals"])

    def test_regression_and_identical_are_rejected(self):
        for factor in (1.2, 1.0):
            self.assertEqual(compare(example(factor=factor))["performance_screen"], "PERFORMANCE_SCREEN_REJECT")

    def test_reused_run_and_different_work_are_invalid(self):
        data = example()
        data["pairs"][1]["baseline"]["run_id"] = "b0"
        with self.assertRaises(ValueError):
            compare(data)
        data = example()
        data["pairs"][0]["candidate"]["source_samples"] += 1
        with self.assertRaises(ValueError):
            compare(data)

    def test_nonfinite_and_profiler_are_invalid(self):
        for field, value in (("elapsed_seconds", float("nan")), ("elapsed_seconds", -1), ("source_samples", True), ("measurement_mode", "ncu")):
            data = example()
            data["pairs"][0]["candidate"][field] = value
            with self.assertRaises(ValueError):
                compare(data)

    def test_normalization_and_bootstrap_reproducible(self):
        data = example()
        result = compare(data)
        self.assertEqual(result, compare(copy.deepcopy(data)))
        data["normalization_source_samples"] = 100
        changed = compare(data)
        self.assertAlmostEqual(changed["point_estimates"]["saved_seconds_at_normalization"], result["point_estimates"]["saved_seconds_at_normalization"]/10)

    def test_any_and_all_threshold_policy(self):
        data = example()
        data["thresholds"]["min_speedup_percent"] = 20
        self.assertEqual(compare(data)["performance_screen"], "PERFORMANCE_SCREEN_REJECT")
        data["thresholds"]["mode"] = "any"
        self.assertEqual(compare(data)["performance_screen"], "PERFORMANCE_SCREEN_PASS")

    def test_order_and_explicit_mode(self):
        data = example()
        for pair in data["pairs"]:
            pair["order"] = "AB"
        self.assertEqual(compare(data)["status"], "INCONCLUSIVE")
        data = example()
        del data["thresholds"]["mode"]
        with self.assertRaises(ValueError):
            compare(data)

    def test_pair_fingerprints_must_match_and_exist(self):
        for field in ("matched_input_fingerprint", "environment_fingerprint", "initial_checkpoint_sha256"):
            data = example()
            data["pairs"][0]["candidate"][field] = "f"*64
            with self.assertRaises(ValueError):
                compare(data)
            data = example()
            del data["pairs"][0]["candidate"][field]
            with self.assertRaises(ValueError):
                compare(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--example", action="store_true", help="print an explicitly synthetic valid input")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ComparisonTests))
        return 0 if result.wasSuccessful() else 1
    if args.example:
        print(json.dumps(example(), indent=2))
        return 0
    if args.input is None:
        parser.error("provide an input JSON file, --example, or --self-test")
    try:
        raw = args.input.read_bytes()
        result = compare(json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest())
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(json.dumps({"error": str(error), "promotion_approved": False}), file=sys.stderr)
        return 2
    output = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
