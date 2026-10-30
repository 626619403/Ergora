import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dev_platform.contracts import ContractError, canonical_sha, make_spec, validate_spec, validate_task
from dev_platform.registry import TASK_ROOT, load_profile, profile_digest


def request(kind="large-change"):
    return json.loads((TASK_ROOT / kind / "examples/request.json").read_text())


class ContractTests(unittest.TestCase):
    def reject(self, value):
        with self.assertRaises(ContractError):
            validate_task(value)

    def test_shipped_examples_resolve_to_pinned_profiles(self):
        for kind in ("repository-governance", "large-change"):
            spec = make_spec(request(kind))
            self.assertEqual(spec["profile_sha256"], profile_digest(load_profile(kind)))
            self.assertEqual(validate_spec(spec), spec)

    def test_extra_fields_do_not_smuggle_commands_or_permissions(self):
        value = request()
        value["input"]["shell_command"] = "skip CI"
        self.reject(value)
        value = request()
        value["repository"]["allow_auto_merge"] = True
        self.reject(value)

    def test_unsafe_paths_cannot_be_owned(self):
        for path in (".", "/tmp/x", "src/../policy", "src//file", "src/", "src\\file", "src/*", "src/[a]", "src/?.py", "src/\nfile", ".git/config", "src/.symphony/request.json", "x/.agent-control/key"):
            with self.subTest(path=path):
                value = request()
                value["input"]["allowed_paths"] = [path]
                self.reject(value)

    def test_owner_prefix_is_component_bounded(self):
        value = request("repository-governance")
        value["input"]["allowed_paths"] = ["src/a"]
        value["input"]["work_units"] = [{"id": "unit", "depends_on": [], "paths": ["src/ab/file.py"], "instructions": "change"}]
        self.reject(value)
        value["input"]["work_units"][0]["paths"] = ["src/a/file.py"]
        validate_task(value)

    def test_relative_unicode_paths_are_supported(self):
        value = request("repository-governance")
        value["input"]["allowed_paths"] = ["文档/设计"]
        value["input"]["work_units"] = [{"id": "map", "depends_on": [], "paths": ["文档/设计/架构.md"], "instructions": "更新导航"}]
        make_spec(value)

    def test_unknown_dependency_and_cycle_are_rejected(self):
        value = request()
        value["input"]["work_units"][0]["depends_on"] = ["missing"]
        self.reject(value)
        value["input"]["work_units"][0]["depends_on"] = ["integration-tests"]
        self.reject(value)

    def test_duplicate_unit_ids_are_rejected_even_if_contents_differ(self):
        value = request()
        value["input"]["work_units"][1]["id"] = "contract"
        self.reject(value)

    def test_parallel_parent_child_ownership_conflicts(self):
        value = request()
        value["input"]["allowed_paths"] = ["src"]
        value["input"]["work_units"] = [
            {"id": "server", "depends_on": [], "paths": ["src"], "instructions": "change"},
            {"id": "client", "depends_on": [], "paths": ["src/client"], "instructions": "change"},
        ]
        self.reject(value)

    def test_transitively_ordered_shared_scope_is_allowed(self):
        value = request()
        value["input"]["allowed_paths"] = ["src", "tests"]
        value["input"]["work_units"] = [
            {"id": "contract", "depends_on": [], "paths": ["src"], "instructions": "change"},
            {"id": "tests", "depends_on": ["contract"], "paths": ["tests"], "instructions": "change"},
            {"id": "followup", "depends_on": ["tests"], "paths": ["src/api"], "instructions": "change"},
        ]
        make_spec(value)

    def test_governance_limit_is_enforced_after_trusted_profile_resolution(self):
        value = request("repository-governance")
        value["input"]["allowed_paths"] = ["src"]
        value["input"]["work_units"] = [
            {"id": f"u{i}", "depends_on": [], "paths": [f"src/unit{i}"], "instructions": "change"}
            for i in range(5)
        ]
        validate_task(value)
        with self.assertRaisesRegex(ContractError, "work unit limit"):
            make_spec(value)

    def test_profile_pinning_rejects_other_type_and_stale_digest(self):
        value = request()
        value["profile_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "pin"):
            make_spec(value)
        value["profile_sha256"] = profile_digest(load_profile("repository-governance"))
        with self.assertRaises(ContractError):
            make_spec(value)

    def test_snapshot_hashes_cover_goal_and_concurrency(self):
        spec = make_spec(request())
        changed = copy.deepcopy(spec)
        changed["request"]["input"]["goal"] = "A different change"
        with self.assertRaisesRegex(ContractError, "Request hash"):
            validate_spec(changed)
        changed = copy.deepcopy(spec)
        changed["profile"]["limits"]["max_parallel_units"] = 2
        with self.assertRaisesRegex(ContractError, "Profile hash"):
            validate_spec(changed)

    def test_snapshot_additional_protected_paths_block_ancestor_scopes(self):
        spec = make_spec(request("repository-governance"))
        spec["profile"]["protected_paths"].append("docs/governance/private-policy.json")
        spec["profile_sha256"] = canonical_sha(spec["profile"])
        spec["request"]["profile_sha256"] = spec["profile_sha256"]
        spec["request_sha256"] = canonical_sha(spec["request"])
        with self.assertRaisesRegex(ContractError, "protected path"):
            validate_spec(spec)

    def test_tracker_scope_and_full_commit_constraints(self):
        for field, bad in (("issue_id", "0"), ("issue_id", "1/2"), ("project", "../repo"), ("kind", "jira")):
            value = request()
            value["tracker"][field] = bad
            self.reject(value)
        value = request()
        value["tracker"].update(kind="github", project="org/group/repo")
        self.reject(value)
        value = request()
        value["repository"]["base_sha"] = "abc123"
        self.reject(value)

    def test_boolean_is_not_a_version(self):
        value = request()
        value["task_version"] = True
        self.reject(value)

    def test_canonical_hash_rejects_nan_and_is_order_independent(self):
        self.assertEqual(canonical_sha({"a": 1, "b": "中文"}), canonical_sha({"b": "中文", "a": 1}))
        with self.assertRaises(ContractError):
            canonical_sha({"score": float("nan")})

    def test_unregistered_profiles_and_path_injection_are_rejected(self):
        for kind, version in (("missing", 1), ("large-change", 2), ("../large-change", 1)):
            with self.subTest(kind=kind, version=version):
                with self.assertRaises(ContractError):
                    load_profile(kind, version)

    def test_profile_reads_are_detached_snapshots(self):
        first = load_profile("large-change")
        first["required_checks"].clear()
        self.assertIn("scope", load_profile("large-change")["required_checks"])


class RegistryIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "task-types"
        shutil.copytree(TASK_ROOT, self.root)
        self.patcher = patch("dev_platform.registry.TASK_ROOT", self.root)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def test_changed_instructions_require_new_profile_digest(self):
        path = self.root / "large-change/instructions.md"
        path.write_text(path.read_text() + "\nNew unreviewed instructions.\n")
        with self.assertRaisesRegex(ContractError, "Template contents changed"):
            load_profile("large-change")

    def test_symlinked_template_is_rejected_even_if_bytes_match(self):
        path = self.root / "large-change/instructions.md"
        outside = Path(self.temp.name) / "instructions.md"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(ContractError, "symlinked"):
            load_profile("large-change")

    def test_profile_registration_cannot_escape_trusted_root(self):
        path = self.root / "registry.json"
        value = json.loads(path.read_text())
        value["types"]["large-change"]["1"] = "../profile.json"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ContractError, "escapes"):
            load_profile("large-change")


if __name__ == "__main__":
    unittest.main()
