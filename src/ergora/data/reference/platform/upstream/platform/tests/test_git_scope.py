import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))
from dev_platform.contracts import canonical_sha
from dev_platform.registry import load_profile, make_spec

SCRIPT = PLATFORM / "harness/git_scope.py"
loader = importlib.util.spec_from_file_location("trusted_git_scope", SCRIPT)
scope = importlib.util.module_from_spec(loader)
loader.loader.exec_module(scope)


class GitScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        self.git("init", "--quiet")
        self.git("config", "user.name", "Scope Fixture")
        self.git("config", "user.email", "scope-fixture@example.invalid")
        self.put("src/owned.py", "value = 1\n")
        self.put("outside/legacy.py", "value = 1\n")
        self.base = self.commit("base")
        self.policy = {"schema_version": 1, "protected_paths": [".github", "infra/prod"],
                       "max_changed_files": 20, "max_changed_lines": 100}
        self.spec = self.make_spec(["src"])

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
        result = subprocess.run(["git", "-c", "core.hooksPath=" + os.devnull, "-C", str(self.root), *args],
                                env=env, capture_output=True, check=True)
        return result.stdout.decode().strip()

    def put(self, path, value):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(value.encode() if isinstance(value, str) else value)
        return p

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", message)
        return self.git("rev-parse", "HEAD")

    def make_spec(self, paths):
        profile = load_profile("repository-governance")
        request = {"schema_version": 2, "task_type": "repository-governance", "task_version": 1,
                   "task_id": "scope-fixture-r1", "profile_sha256": canonical_sha(profile),
                   "tracker": {"kind": "github", "project": "team/project", "issue_id": "42"},
                   "repository": {"base_sha": self.base, "starting_sha": self.base},
                   "input": {"goal": "Scoped behavior-preserving cleanup", "allowed_paths": paths,
                             "acceptance": ["Existing behavior passes"], "constraints": [], "risk": "standard",
                             "work_units": [{"id": "cleanup", "depends_on": [], "paths": [paths[0]],
                                             "instructions": "Make the scoped change"}]}}
        return make_spec(request)

    def verify(self, candidate=None):
        return scope.verify(self.root, candidate or self.git("rev-parse", "HEAD"), self.spec, self.policy)

    def codes(self, report):
        return {item["code"] for item in report["violations"]}

    def test_real_diff_passes_with_hash_binding(self):
        self.put("src/owned.py", "value = 2\n")
        candidate = self.commit("in scope")
        report = self.verify(candidate)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["base_sha"], self.base)
        self.assertEqual(report["candidate_sha"], candidate)
        self.assertEqual(report["request_sha256"], self.spec["request_sha256"])
        self.assertEqual(report["policy_sha256"], canonical_sha(self.policy))
        self.assertEqual(report["changed_text_lines"], 2)

    def test_rename_evaluates_both_deleted_and_added_paths(self):
        self.git("mv", "outside/legacy.py", "src/moved.py")
        self.commit("move outside into allowed")
        report = self.verify()
        self.assertEqual({f["path"] for f in report["files"]}, {"outside/legacy.py", "src/moved.py"})
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("outside-scope", self.codes(report))

    def test_outside_deletion_is_not_hidden(self):
        (self.root / "outside/legacy.py").unlink()
        self.commit("delete outside")
        report = self.verify()
        self.assertIn("outside-scope", self.codes(report))

    def test_allowed_deletion_passes(self):
        (self.root / "src/owned.py").unlink()
        self.commit("delete owned")
        self.assertEqual(self.verify()["status"], "PASS")

    def test_project_protected_ci_path_overrides_allowed_scope(self):
        self.spec = self.make_spec(["src", ".github"])
        self.put(".github/workflows/test.yml", "name: changed\n")
        self.commit("change CI")
        report = self.verify()
        self.assertIn("protected-path", self.codes(report))

    def test_nested_reserved_metadata_is_blocked(self):
        self.put("src/.agent-control/policy.json", "{}\n")
        self.commit("nested private metadata")
        self.assertIn("protected-path", self.codes(self.verify()))

    def test_component_prefix_not_string_prefix(self):
        self.put("src-other/file.py", "x = 1\n")
        self.commit("wrong prefix")
        self.assertIn("outside-scope", self.codes(self.verify()))

    def test_abbreviated_missing_or_noncommit_sha_rejected(self):
        for candidate in (self.base[:12], "0" * 40, self.git("rev-parse", "HEAD:src/owned.py")):
            with self.subTest(candidate=candidate), self.assertRaises(scope.ScopeError):
                self.verify(candidate)

    def test_head_must_equal_candidate(self):
        self.put("src/owned.py", "value = 2\n")
        self.commit("new candidate")
        with self.assertRaisesRegex(scope.ScopeError, "HEAD differs"):
            self.verify(self.base)

    def test_unrelated_commit_history_is_rejected(self):
        tree = self.git("rev-parse", "HEAD^{tree}")
        orphan = self.git("commit-tree", tree, "-m", "unrelated candidate")
        self.git("reset", "--hard", orphan)
        with self.assertRaisesRegex(scope.ScopeError, "does not descend"):
            self.verify(orphan)

    def test_dirty_and_untracked_checkouts_blocked(self):
        self.put("src/untracked.py", "x = 1\n")
        with self.assertRaisesRegex(scope.ScopeError, "clean"):
            self.verify()

    def test_file_and_line_limits(self):
        self.put("src/owned.py", "value = 2\n")
        self.put("src/new.py", "other = 3\n")
        self.commit("large change")
        self.policy["max_changed_files"] = 1
        self.policy["max_changed_lines"] = 1
        self.assertTrue({"file-limit", "line-limit"} <= self.codes(self.verify()))

    def test_binary_diff_cannot_pass_a_line_cap(self):
        self.put("src/image.bin", b"\x00\x01binary\x00")
        self.commit("binary")
        report = self.verify()
        self.assertIn("binary-line-count-unknown", self.codes(report))
        self.assertEqual(report["binary_paths"], ["src/image.bin"])
        del self.policy["max_changed_lines"]
        self.assertEqual(self.verify()["status"], "PASS")

    def test_newline_filename_fails_closed(self):
        self.put("src/odd\nname.py", "x = 1\n")
        self.commit("odd path")
        with self.assertRaisesRegex(scope.ScopeError, "unusual Git path"):
            self.verify()

    def test_non_utf8_filename_fails_closed(self):
        name = os.fsencode(self.root / "src") + b"/odd-\xff.py"
        fd = os.open(name, os.O_CREAT | os.O_WRONLY, 0o600)
        os.write(fd, b"x = 1\n")
        os.close(fd)
        self.commit("non UTF-8 path")
        with self.assertRaisesRegex(scope.ScopeError, "Non-UTF-8"):
            self.verify()

    def test_symlink_change_requires_separate_verifier(self):
        (self.root / "src/link").symlink_to("../outside")
        self.commit("symlink")
        self.assertIn("symlink-change-unsupported", self.codes(self.verify()))

    def test_submodule_gitlink_requires_separate_verifier(self):
        self.git("update-index", "--add", "--cacheinfo", "160000," + self.base + ",src/dependency")
        self.git("commit", "--quiet", "-m", "gitlink")
        (self.root / "src/dependency").mkdir()
        with self.assertRaisesRegex(scope.ScopeError, "submodules"):
            self.verify()

    def test_clean_and_process_filters_never_execute(self):
        marker = Path(self.tmp.name) / "filter-executed"
        helper = Path(self.tmp.name) / "filter.sh"
        helper.write_text("#!/bin/sh\ntouch '" + str(marker) + "'\ncat\n")
        helper.chmod(0o700)
        (self.root / ".git/info/attributes").write_text("*.py filter=review\n")
        # Same-size modification triggers Git's clean-filter comparison.
        self.put("src/owned.py", "value = 2\n")
        for setting in ("clean", "process"):
            self.git("config", "filter.review." + setting, str(helper))
            with self.subTest(setting=setting), self.assertRaisesRegex(scope.ScopeError, "clean/process"):
                scope._git(self.root, "status", "--porcelain=v1", "-z")
            self.assertFalse(marker.exists())
            self.git("config", "--unset", "filter.review." + setting)

    def test_assume_unchanged_and_skip_worktree_rejected(self):
        self.git("update-index", "--assume-unchanged", "src/owned.py")
        self.put("src/owned.py", "value = 2\n")
        self.assertEqual(self.git("status", "--porcelain=v1"), "")
        with self.assertRaisesRegex(scope.ScopeError, "assume-unchanged / skip-worktree"):
            self.verify()
        self.git("update-index", "--no-assume-unchanged", "src/owned.py")
        self.git("update-index", "--skip-worktree", "src/owned.py")
        with self.assertRaisesRegex(scope.ScopeError, "assume-unchanged / skip-worktree"):
            self.verify()

    def test_submodule_child_filter_is_never_executed(self):
        child = self.root / "src/dependency"
        child.mkdir()
        subprocess.run(["git", "init", "--quiet", str(child)], check=True)
        def child_git(*args):
            return subprocess.check_output(["git", "-c", "core.hooksPath=" + os.devnull, "-C", str(child), *args], text=True).strip()
        child_git("config", "user.name", "Child Fixture")
        child_git("config", "user.email", "child@example.invalid")
        (child / "file.txt").write_text("a\n")
        child_git("add", "file.txt")
        child_git("commit", "--quiet", "-m", "child")
        child_sha = child_git("rev-parse", "HEAD")
        self.git("update-index", "--add", "--cacheinfo", "160000," + child_sha + ",src/dependency")
        self.git("commit", "--quiet", "-m", "submodule")
        marker = Path(self.tmp.name) / "child-filter-executed"
        helper = Path(self.tmp.name) / "child-filter.sh"
        helper.write_text("#!/bin/sh\ntouch '" + str(marker) + "'\ncat\n")
        helper.chmod(0o700)
        child_git("config", "filter.review.clean", str(helper))
        (child / ".git/info/attributes").write_text("*.txt filter=review\n")
        (child / "file.txt").write_text("b\n")
        with self.assertRaisesRegex(scope.ScopeError, "submodules"):
            self.verify()
        with self.assertRaisesRegex(scope.ScopeError, "Submodule/gitlink"):
            scope._git(self.root, "status", "--porcelain=v1", "--ignore-submodules=none")
        self.assertFalse(marker.exists())

    def test_promisor_clone_cannot_invoke_remote_helper(self):
        base_blob = self.git("rev-parse", self.base + ":src/owned.py")
        self.put("src/owned.py", "value = 2\n")
        self.commit("candidate")
        self.git("config", "remote.origin.url", "review::fixture")
        self.git("config", "remote.origin.promisor", "true")
        self.git("config", "remote.origin.partialclonefilter", "blob:none")
        self.git("config", "protocol.review.allow", "always")
        loose_blob = self.root / ".git/objects" / base_blob[:2] / base_blob[2:]
        loose_blob.unlink()
        helper_dir = Path(self.tmp.name) / "helpers"
        helper_dir.mkdir()
        marker = Path(self.tmp.name) / "remote-helper-executed"
        helper = helper_dir / "git-remote-review"
        helper.write_text("#!/bin/sh\ntouch '" + str(marker) + "'\nexit 1\n")
        helper.chmod(0o700)
        with patch.dict(os.environ, {"PATH": str(helper_dir) + os.pathsep + os.environ["PATH"]}):
            with self.assertRaisesRegex(scope.ScopeError, "Partial/promisor"):
                self.verify()
            with self.assertRaisesRegex(scope.ScopeError, "Partial/promisor"):
                scope._git(self.root, "cat-file", "-p", base_blob)
            # Defense in depth still forbids transport if a future caller omits
            # the preflight. A protocol-specific allow rule cannot run a helper.
            with self.assertRaises(scope.ScopeError):
                scope._run_git(self.root, "cat-file", "-p", base_blob)
        self.assertFalse(marker.exists())

    def test_sparse_checkout_config_is_rejected(self):
        self.git("config", "core.sparseCheckout", "true")
        with self.assertRaisesRegex(scope.ScopeError, "Sparse"):
            self.verify()

    def test_external_diff_and_textconv_are_never_run(self):
        marker = Path(self.tmp.name) / "executed"
        helper = Path(self.tmp.name) / "unsafe-diff.sh"
        helper.write_text("#!/bin/sh\ntouch '" + str(marker) + "'\n")
        helper.chmod(0o700)
        self.git("config", "diff.external", str(helper))
        self.git("config", "diff.unsafe.textconv", str(helper))
        info = self.root / ".git/info/attributes"
        info.write_text("*.py diff=unsafe\n")
        self.put("src/owned.py", "value = 2\n")
        self.commit("candidate")
        self.assertEqual(self.verify()["status"], "PASS")
        self.assertFalse(marker.exists())

    def test_cli_failure_report_and_no_overwrite(self):
        self.put("outside/legacy.py", "value = 2\n")
        candidate = self.commit("outside")
        spec = Path(self.tmp.name) / "spec.json"
        policy = Path(self.tmp.name) / "policy.json"
        output = Path(self.tmp.name) / "report.json"
        spec.write_text(json.dumps(self.spec))
        policy.write_text(json.dumps(self.policy))
        command = [sys.executable, str(SCRIPT), "--repo", str(self.root), "--candidate", candidate,
                   "--spec", str(spec), "--policy", str(policy), "--out", str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        first = output.read_bytes()
        self.assertEqual(json.loads(first)["status"], "FAIL")
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(output.read_bytes(), first)

    def test_invalid_candidate_cli_writes_incomplete_fail_report(self):
        spec = Path(self.tmp.name) / "spec.json"
        policy = Path(self.tmp.name) / "policy.json"
        output = Path(self.tmp.name) / "report.json"
        spec.write_text(json.dumps(self.spec))
        policy.write_text(json.dumps(self.policy))
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.root), "--candidate", "HEAD",
                                 "--spec", str(spec), "--policy", str(policy), "--out", str(output)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(output.read_text())["violations"][0]["code"], "verification-incomplete")


if __name__ == "__main__":
    unittest.main()
