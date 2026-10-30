from __future__ import annotations

from .core import CONFIG, STATE, git, read, write
from .projects import create_task, register
from dev_platform.contracts import canonical_sha


def prepare() -> dict:
    root = STATE / "demo"
    repo = root / "repository"
    if not repo.exists():
        (repo / "src/app").mkdir(parents=True)
        (repo / "tests").mkdir()
        (repo / 'docs').mkdir()
        (repo / "src/app/__init__.py").write_text("")
        (repo / "src/app/math_utils.py").write_text('def add(left, right):\n    return left + right\n')
        (repo / "tests/test_math.py").write_text('import sys, unittest\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))\nfrom app.math_utils import add\nclass Tests(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n')
        (repo / "README.md").write_text('# Installation demo\nRun tests with `python3 -m unittest discover -s tests`.\n')
        (repo / "AGENTS.md").write_text('Read [README.md](README.md) for the tested command and [ARCHITECTURE.md](ARCHITECTURE.md) for boundaries.\n')
        (repo / "ARCHITECTURE.md").write_text('# Architecture\nThe app package contains deterministic arithmetic. Tests depend on app.\n')
        (repo / 'docs/QUALITY.md').write_text('# Quality\nTests exercise arithmetic behavior; architecture and document checks use the trusted external harness.\n')
        (repo / 'docs/RUNBOOK.md').write_text('# Runbook\nRun `python3 -m unittest discover -s tests` from the repository root.\n')
        git(repo, "init", "--initial-branch=main")
        git(repo, "add", "--all")
        git(repo, "commit", "-m", "Initial installation demo")
    checks = {
        "behavior": ["python3", "-m", "unittest", "discover", "-s", "tests"],
        "architecture": ["python3", "/platform/upstream/platform/harness/harness.py", "check", "--repo", '{repo}',
            "--policy", "/policy/harness.json", "--out", "/out/harness.json"],
        "knowledge": ["python3", "/platform/upstream/platform/harness/harness.py", "check", "--repo", '{repo}',
            "--policy", "/policy/harness.json", "--out", "/out/harness.json"],
    }
    checks_file = root / 'checks-governance.json'
    write(checks_file, checks)
    if not (CONFIG / "projects/install-demo.json").exists():
        register("install-demo", repo, "local", "local/install-demo", ["src", "tests", "README.md", "AGENTS.md", "ARCHITECTURE.md", 'docs'], checks_file)
    write(CONFIG / 'policies/install-demo/execution.json', {'allowed_task_types': ['repository-governance']})
    harness = {"schema_version": 1, "python_roots": ["src"], "layers": {"app": ["app"]},
               "allowed_edges": {'app': []}, 'doc_roots': ['README.md', 'AGENTS.md', 'ARCHITECTURE.md', 'docs'],
               "required_docs": ["README.md", "AGENTS.md", "ARCHITECTURE.md", 'docs/QUALITY.md', 'docs/RUNBOOK.md'],
               "max_file_lines": 300}
    write(CONFIG / "policies/install-demo/harness.json", harness)
    results = []
    for kind in ("repository-governance", "large-change"):
        task_id = "installation-" + ("governance" if kind == "repository-governance" else "large") + "-r1"
        unit = {"id": "arithmetic", "depends_on": [], "paths": ["src/app/math_utils.py", "tests/test_math.py"],
                "instructions": "Add subtract(left, right) alongside add and verify positive, zero and negative values; keep add unchanged."}
        inp = {"goal": "Add a small tested subtraction function for the installation acceptance task.",
               "allowed_paths": unit["paths"], "acceptance": ["Existing addition tests pass.", "Subtraction has correct positive, zero and negative results."],
               "constraints": ["Keep the public add function unchanged."], "risk": "standard" if kind == 'repository-governance' else 'high', "work_units": [unit]}
        input_path = root / (kind + '.' + canonical_sha(inp)[:12] + '.input.json')
        write(input_path, inp)
        if not (STATE / "tasks" / task_id / "compiled.json").exists():
            results.append(create_task("install-demo", kind, task_id, "1", input_path))
    return {"demo_repository": str(repo), "templates": results, "tracker": "local installation fixture; no remote issue exists or is contacted",
            'large_change_fixture': 'compile-only; use a real project with trusted integration, compatibility and rollback checks',
            "model_execution_started": False, "next": "Resolve doctor prerequisites, start the governance task, inspect and approve its exact plan"}
