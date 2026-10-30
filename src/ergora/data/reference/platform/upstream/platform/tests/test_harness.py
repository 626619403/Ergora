import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HARNESS = Path(__file__).resolve().parents[1] / "harness" / "harness.py"
spec = importlib.util.spec_from_file_location("repository_harness", HARNESS)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        self.policy = {
            "schema_version": 1,
            "required_docs": ["AGENTS.md", "docs/index.md"],
            "doc_roots": ["AGENTS.md", "docs"],
            "python_roots": ["src"],
            "layers": {"domain": ["app.domain"], "service": ["app.service"]},
            "allowed_edges": {"domain": [], "service": ["domain"]},
            "max_file_lines": 100,
        }
        self.put("AGENTS.md", "[Docs](docs/index.md)\n")
        self.put("docs/index.md", "[Map](../AGENTS.md)\n")
        self.put("src/app/domain/model.py", "VALUE = 1\n")
        self.put("src/app/service/use.py", "from app.domain import model\n")

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def scan(self):
        return h.scan(self.root, self.policy)

    def rules(self):
        return {f["rule"] for f in self.scan()["findings"]}

    def test_stage_is_new_directory_only(self):
        target = Path(self.tmp.name) / "staging"
        h.bootstrap(target)
        original = (target / "AGENTS.md").read_bytes()
        with self.assertRaises(h.HarnessError):
            h.bootstrap(target)
        self.assertEqual((target / "AGENTS.md").read_bytes(), original)
        self.assertTrue((target / "docs/exec-plans/PLAN_TEMPLATE.md").is_file())

    def test_staged_document_map_has_no_broken_local_links(self):
        target = Path(self.tmp.name) / "staging"
        h.bootstrap(target)
        code = target / "src/app/domain/model.py"
        code.parent.mkdir(parents=True)
        code.write_text("VALUE = 1\n")
        report = h.scan(target, h.load_policy(target / "harness-policy.json"))
        self.assertEqual(report["findings"], [])

    def test_valid_scan_has_explicit_coverage(self):
        report = self.scan()
        self.assertEqual(h.evaluate(report)["status"], "PASS")
        self.assertEqual(report["coverage"]["python_files"], 2)
        self.assertEqual(report["coverage"]["internal_import_edges"], 1)
        self.assertIn("Markdown heading anchors", report["coverage"]["excludes"])

    def test_forbidden_edge_blocked(self):
        self.put("src/app/domain/model.py", "from app.service import use\n")
        self.assertIn("forbidden-dependency", self.rules())
        self.assertEqual(h.evaluate(self.scan())["status"], "BLOCKED")

    def test_relative_import_cannot_bypass_layer_check(self):
        self.put("src/app/domain/model.py", "from ..service import use\n")
        self.assertIn("forbidden-dependency", self.rules())

    def test_existing_debt_accepted_but_new_debt_not_offset(self):
        self.put("docs/index.md", "[old](missing-old.md)\n")
        baseline = h.make_baseline(self.scan())
        self.assertEqual(h.evaluate(self.scan(), baseline)["status"], "PASS")
        self.put("docs/index.md", "[new](missing-new.md)\n")
        gate = h.evaluate(self.scan(), baseline)
        self.assertEqual(gate["status"], "BLOCKED")
        self.assertEqual(len(gate["resolved_debt"]), 1)
        self.assertEqual(len(gate["new_findings"]), 1)

    def test_old_long_file_growth_is_regression(self):
        self.put("src/app/domain/model.py", "# old\n" * 120)
        baseline = h.make_baseline(self.scan())
        self.put("src/app/domain/model.py", "# old\n" * 119)
        self.assertEqual(h.evaluate(self.scan(), baseline)["status"], "PASS")
        self.put("src/app/domain/model.py", "# old\n" * 121)
        self.assertEqual(h.evaluate(self.scan(), baseline)["status"], "BLOCKED")

    def test_incomplete_scan_cannot_be_baselined(self):
        self.put("src/app/domain/model.py", "def !!!\n")
        self.assertIn("python-parse-error", self.rules())
        with self.assertRaises(h.HarnessError):
            h.make_baseline(self.scan())

    def test_changed_policy_does_not_silently_rebaseline(self):
        baseline = h.make_baseline(self.scan())
        self.policy["max_file_lines"] = 500
        with self.assertRaises(h.HarnessError):
            h.evaluate(self.scan(), baseline)

    def test_dynamic_import_is_not_claimed_as_covered(self):
        self.put("src/app/domain/model.py", "import importlib\nx = importlib.import_module('app.service.use')\n")
        self.assertIn("dynamic-import-unsupported", self.rules())
        with self.assertRaises(h.HarnessError):
            h.make_baseline(self.scan())

    def test_document_links_and_code_examples(self):
        self.put("docs/index.md", "[ok](../AGENTS.md)\n```md\n[x](not-real.md)\n```\n[ref][local]\n[local]: gone.md\n")
        report = self.scan()
        broken = [f for f in report["findings"] if f["rule"] == "doc-link-broken"]
        self.assertEqual([f["key"] for f in broken], ["gone.md"])

    def test_document_path_escape_is_hard_error(self):
        self.put("docs/index.md", "[outside](../../outside.md)\n")
        self.assertIn("doc-link-escape", self.rules())

    def test_symlink_file_is_hard_error(self):
        (self.root / "src/app/domain/link.py").symlink_to(self.root / "src/app/domain/model.py")
        self.assertIn("symlink-unsupported", self.rules())

    def test_symlink_scan_root_is_hard_error(self):
        (self.root / "linked-src").symlink_to(self.root / "src", target_is_directory=True)
        self.policy["python_roots"] = ["linked-src"]
        self.assertIn("scan-root-unsafe", self.rules())

    def test_missing_and_empty_roots_do_not_pass(self):
        self.policy["python_roots"] = ["nonexistent"]
        self.assertIn("scan-root-missing", self.rules())
        (self.root / "empty").mkdir()
        self.policy["python_roots"] = ["empty"]
        self.assertIn("python-coverage-empty", self.rules())

    def test_unassigned_module_blocks(self):
        self.put("src/app/unowned.py", "VALUE = 1\n")
        self.assertIn("python-layer-unassigned", self.rules())

    def test_output_is_create_only(self):
        out = Path(self.tmp.name) / "out.json"
        h.write_new(out, {"first": 1})
        with self.assertRaises(FileExistsError):
            h.write_new(out, {"second": 2})
        self.assertEqual(json.loads(out.read_text()), {"first": 1})

    def test_cli_rejects_wrong_trusted_baseline_hash(self):
        policy = Path(self.tmp.name) / "policy.json"
        baseline = Path(self.tmp.name) / "baseline.json"
        out = Path(self.tmp.name) / "out.json"
        h.write_new(policy, self.policy)
        h.write_new(baseline, h.make_baseline(self.scan()))
        result = subprocess.run([sys.executable, str(HARNESS), "check", "--repo", str(self.root), "--policy", str(policy), "--baseline", str(baseline), "--baseline-sha256", "0" * 64, "--out", str(out)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("trusted CI hash", result.stderr)
        self.assertFalse(out.exists())

    def test_cli_correct_baseline_completes(self):
        policy = Path(self.tmp.name) / "policy.json"
        baseline = Path(self.tmp.name) / "baseline.json"
        out = Path(self.tmp.name) / "out.json"
        h.write_new(policy, self.policy)
        h.write_new(baseline, h.make_baseline(self.scan()))
        result = subprocess.run([sys.executable, str(HARNESS), "check", "--repo", str(self.root), "--policy", str(policy), "--baseline", str(baseline), "--baseline-sha256", h.digest(baseline.read_bytes()), "--out", str(out)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(out.read_text())["gate"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
