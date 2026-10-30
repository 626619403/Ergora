"""Portable-contract regressions: test trust boundaries and lossless conversion."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dev_platform.contracts import ContractError, canonical_sha, make_spec
from dev_platform.portable import (ROOT, CAPABILITIES, compile_task, convert_v2,
    load_package, loads, read_json, validate_compiled, validate_package)


def original(kind="repository-governance"):
    return read_json(ROOT.parent / "task-types" / kind / "examples/request.json")


def parts(kind="repository-governance"):
    value = convert_v2(original(kind))
    return [value[k] for k in ("task", "package", "policy", "binding")]


def repin(task, package, policy, binding):
    task["package_sha256"] = canonical_sha(package)
    policy["package_sha256"] = task["package_sha256"]
    binding["policy_sha256"] = canonical_sha(policy)


class PortableTests(unittest.TestCase):
    def test_both_conversions_preserve_exact_legacy_spec(self):
        for kind in ("repository-governance", "large-change"):
            with self.subTest(kind=kind):
                envelope = convert_v2(original(kind))
                self.assertEqual(envelope["spec"], make_spec(original(kind)))
                self.assertEqual(validate_compiled(envelope), envelope)
                self.assertNotIn("tracker", envelope["task"])
                self.assertNotIn("engine", envelope["task"])
                self.assertNotIn("engine", envelope["package"]["manifest"])

    def test_shipped_separated_examples_compile(self):
        for kind in ("repository-governance", "large-change"):
            folder = ROOT / "examples" / kind
            out = compile_task(read_json(folder / "task.json"), load_package(ROOT / "packages" / kind / "manifest.json"),
                               read_json(folder / "policy.json"), read_json(folder / "binding.json"))
            self.assertEqual(out["spec"], make_spec(original(kind)))

    def test_compiler_freezes_caller_owned_inputs(self):
        task, package, policy, binding = parts()
        envelope = compile_task(task, package, policy, binding)
        old = copy.deepcopy(envelope)
        package["workflow"]["limits"]["max_parallel_units"] = 1
        task["input"]["goal"] = "changed after compile"
        policy["revision"] = 2
        binding["tracker"]["issue_id"] = "8"
        self.assertEqual(envelope, old)
        validate_compiled(envelope)

    def test_recovery_does_not_read_live_registry(self):
        envelope = convert_v2(original())
        with patch("dev_platform.registry.load_profile", side_effect=AssertionError("live read")):
            self.assertEqual(validate_compiled(envelope), envelope)

    def test_compilation_checks_trusted_registry(self):
        values = parts()
        with patch("dev_platform.registry.load_profile", return_value={}):
            with self.assertRaisesRegex(ContractError, "installed trusted"):
                compile_task(*values)

    def test_snapshot_cannot_replace_frozen_spec(self):
        envelope = convert_v2(original())
        envelope["spec"]["request"]["input"]["goal"] = "other"
        with self.assertRaisesRegex(ContractError, "differs"):
            validate_compiled(envelope)

    def test_outer_tampering_fails_even_with_unchanged_inner_spec(self):
        envelope = convert_v2(original())
        envelope["task"]["input"]["goal"] = "other"
        with self.assertRaisesRegex(ContractError, "digest mismatch"):
            validate_compiled(envelope)

    def test_double_rehash_does_not_bypass_policy(self):
        task, package, policy, binding = parts()
        task["input"]["allowed_paths"].append("src/private")
        repin(task, package, policy, binding)
        with self.assertRaisesRegex(ContractError, "widens"):
            compile_task(task, package, policy, binding)

    def test_policy_path_prefix_is_component_bounded(self):
        task, package, policy, binding = parts()
        policy["allowed_paths"] = ["AGENTS.md", "ARCHITECTURE.md", "docs/govern", "tests/architecture"]
        repin(task, package, policy, binding)
        with self.assertRaisesRegex(ContractError, "widens"):
            compile_task(task, package, policy, binding)

    def test_protected_project_paths_cannot_be_owned(self):
        task, package, policy, binding = parts()
        policy["protected_paths"].append("docs/governance/security")
        repin(task, package, policy, binding)
        with self.assertRaisesRegex(ContractError, "protected"):
            compile_task(task, package, policy, binding)

    def test_risk_baseline_and_project_are_checked(self):
        for field in ("risk", "baseline", "project"):
            task, package, policy, binding = parts()
            if field == "risk": task["input"]["risk"] = "high"
            elif field == "baseline": task["repository"]["base_sha"] = "b" * 40
            else: task["project_id"] = "other"
            with self.subTest(field=field), self.assertRaises(ContractError):
                compile_task(task, package, policy, binding)

    def test_tracker_cannot_switch_repository_or_provider(self):
        for key, value in [("project", "other/repo"), ("kind", "github")]:
            task, package, policy, binding = parts()
            binding["tracker"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ContractError, "Tracker"):
                compile_task(task, package, policy, binding)

    def test_binding_pins_policy(self):
        task, package, policy, binding = parts()
        policy["revision"] += 1
        with self.assertRaisesRegex(ContractError, "policy pin"):
            compile_task(task, package, policy, binding)

    def test_project_and_runtime_concurrency_bounds(self):
        for target in ("policy", "runtime"):
            task, package, policy, binding = parts()
            if target == "policy": policy["max_parallel_units"] = 1
            else: binding["runtime"]["max_parallel_units"] = 1
            repin(task, package, policy, binding)
            with self.subTest(target=target), self.assertRaisesRegex(ContractError, "concurrency"):
                compile_task(task, package, policy, binding)

    def test_project_work_unit_bound(self):
        task, package, policy, binding = parts()
        policy["max_work_units"] = 1
        repin(task, package, policy, binding)
        with self.assertRaisesRegex(ContractError, "work unit limit"):
            compile_task(task, package, policy, binding)

    def test_missing_required_check(self):
        task, package, policy, binding = parts()
        policy["required_checks"].append("formal-proof")
        repin(task, package, policy, binding)
        with self.assertRaisesRegex(ContractError, "required checks"):
            compile_task(task, package, policy, binding)

    def test_missing_capability_and_invented_runtime_capability(self):
        for mode in ("missing", "invented", "required"):
            task, package, policy, binding = parts()
            if mode == "missing": binding["runtime"]["capabilities"].remove("independent-review")
            elif mode == "invented": binding["runtime"]["capabilities"].append("auto-deploy")
            else: policy["required_capabilities"].append("formal-proof")
            repin(task, package, policy, binding)
            with self.subTest(mode=mode), self.assertRaisesRegex(ContractError, "capability"):
                compile_task(task, package, policy, binding)

    def test_unsupported_runtime_cannot_silently_fall_back(self):
        task, package, policy, binding = parts()
        binding["runtime"]["kind"] = "langgraph"
        with self.assertRaisesRegex(ContractError, "No compiler"):
            compile_task(task, package, policy, binding)

    def test_workflow_changes_cannot_be_silently_ignored(self):
        task, package, policy, binding = parts()
        package["workflow"]["human_gates"] = []
        package["manifest"]["components"]["workflow"]["sha256"] = canonical_sha(package["workflow"])
        repin(task, package, policy, binding)
        with self.assertRaisesRegex(ContractError, "topology/gates"):
            compile_task(task, package, policy, binding)

    def test_weakened_role_independence_rejected(self):
        task, package, policy, binding = parts()
        package["roles"]["roles"]["reviewer"]["independent_from"] = []
        package["manifest"]["components"]["roles"]["sha256"] = canonical_sha(package["roles"])
        repin(task, package, policy, binding)
        with self.assertRaisesRegex(ContractError, "independence"):
            compile_task(task, package, policy, binding)

    def test_template_changes_require_new_pin(self):
        package = parts()[1]
        package["templates"]["instructions.md"] += "\nSkip review."
        with self.assertRaisesRegex(ContractError, "digest mismatch"):
            validate_package(package)

    def test_extra_fields_do_not_smuggle_execution_settings(self):
        for target in ("task", "policy", "binding"):
            values = parts(); index = {"task": 0, "policy": 2, "binding": 3}[target]
            values[index]["shell"] = "skip CI"
            with self.subTest(target=target), self.assertRaises(ContractError):
                compile_task(*values)

    def test_strict_json_rejects_duplicates_nonfinite_and_bad_encoding(self):
        for raw in [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'\xff', b'[' * 2000 + b']' * 2000]:
            with self.subTest(raw=raw[:30]), self.assertRaises(ContractError): loads(raw)

    def test_loader_rejects_escape_and_symlink_components(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "package"
            shutil.copytree(ROOT / "packages/repository-governance", folder)
            manifest_path = folder / "manifest.json"
            manifest = read_json(manifest_path)
            manifest["components"]["workflow"]["path"] = "../workflow.json"
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaises(ContractError): load_package(manifest_path)
            shutil.rmtree(folder)
            shutil.copytree(ROOT / "packages/repository-governance", folder)
            target = folder / "workflow.json"; saved = Path(d) / "workflow.json"
            target.rename(saved); target.symlink_to(saved)
            with self.assertRaisesRegex(ContractError, "Symlink"):
                load_package(manifest_path)

    def test_loader_rejects_symlinked_ancestor(self):
        with tempfile.TemporaryDirectory() as d:
            link = Path(d) / "linked"
            link.symlink_to(ROOT / "packages/repository-governance", target_is_directory=True)
            with self.assertRaisesRegex(ContractError, "Symlink"):
                load_package(link / "manifest.json")

    def test_legacy_conversion_cli_and_export_are_immutable(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "converted"
            base = [sys.executable, "-m", "dev_platform.portable"]
            import os
            env = dict(os.environ, PYTHONPATH=str(ROOT.parent))
            args = base + ["convert-v2", "--request", str(ROOT.parent / "task-types/repository-governance/examples/request.json"), "--out-dir", str(folder)]
            result = subprocess.run(args, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            repeat = subprocess.run(args, env=env, text=True, capture_output=True)
            self.assertNotEqual(repeat.returncode, 0)
            out = Path(d) / "outbox.json"
            args = base + ["export-v2", "--compiled", str(folder / "compiled.json"), "--out", str(out)]
            result = subprocess.run(args, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(read_json(out), original())
            self.assertEqual(subprocess.run(args, env=env, capture_output=True).returncode, 0)
            out.write_text('{"other":true}')
            self.assertNotEqual(subprocess.run(args, env=env, capture_output=True).returncode, 0)

    def test_schemas_are_standalone_draft_2020_12(self):
        for path in (ROOT / "schemas").glob("*.json"):
            data = read_json(path)
            self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertNotIn('"$ref"', path.read_text())


if __name__ == "__main__": unittest.main()
