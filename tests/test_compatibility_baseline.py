"""Persisted identity contracts and synthetic stored documents."""

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

import ergora.native.resources as native_resources
import ergora.development.drafts as drafts
import ergora.improvement.evaluation as evaluation
import ergora.improvement.kernel as kernel
import ergora.improvement.memory as memory
import ergora.improvement.optimization as optimization
import ergora.configuration.projects as projects
import ergora.improvement.research as research
import ergora.definitions.skills as skill_assets
import ergora.operations.tools as tools
import ergora.agents.runs as agent_runs
from ergora.storage.state import State


FIXTURES = Path(__file__).parent / "fixtures/compatibility-v0_2_0"
IDENTITIES = json.loads((FIXTURES / "identities.json").read_text(encoding="utf-8"))






def test_distinct_json_identity_vectors_are_preserved(tmp_path):
    payload = IDENTITIES["payload"]
    assert evaluation.manifest_sha256(payload) == IDENTITIES["evaluation_sha256"]
    environment = dict(os.environ, PYTHONPATH=str(native_resources.ROOT / "platform/upstream/platform"),
                       PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    result = subprocess.run(
        [sys.executable, "-P", "-S", "-c",
         "import json,sys;from dev_platform.contracts import canonical_sha;"
         "from dev_platform.adapter import sha;v=json.load(sys.stdin);print(canonical_sha(v));print(sha(v))"],
        input=json.dumps(payload), cwd=tmp_path, env=environment,
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    assert result.stdout.splitlines() == [IDENTITIES["compact_sha256"]] * 2
    assert IDENTITIES["compact_sha256"] != IDENTITIES["evaluation_sha256"]


@pytest.mark.parametrize("executable", [False, True])
def test_skill_tree_identity_includes_original_exec_bits(tmp_path, executable):
    if executable and os.name == "nt":
        pytest.skip("POSIX executable-bit identity; Windows verifies the plain content vector")
    for relative, text in IDENTITIES["skill_content"].items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
        target.chmod(0o755 if executable and relative == "scripts/check.py" else 0o644)
    expected = IDENTITIES["skill_identity"]["executable" if executable else "plain"]
    digest, files = skill_assets.digest_tree(tmp_path)
    assert digest == expected["digest"]
    assert files == expected["files"]


@pytest.mark.parametrize("kind", ["repository-governance"])
def test_compiled_examples_keep_exact_pre_refactor_identity(tmp_path, kind):
    example = native_resources.ROOT / "platform/upstream/platform/portable/examples" / kind
    package = native_resources.ROOT / "platform/upstream/platform/portable/packages" / kind / "manifest.json"
    target = tmp_path / "compiled.json"
    subprocess.run(
        [sys.executable, "-m", "ergora", "workflow", "compile", "--task", str(example / "task.json"),
         "--package", str(package), "--policy", str(example / "policy.json"),
         "--binding", str(example / "binding.json"), "--out", str(target)],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    compiled = json.loads(target.read_text(encoding="utf-8"))
    encoded = json.dumps(compiled, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    expected = IDENTITIES["compiled"][kind]
    assert hashlib.sha256(encoded).hexdigest() == expected["canonical_sha256"]
    assert compiled["spec"]["request_sha256"] == expected["request_sha256"]
    assert compiled["spec"]["profile_sha256"] == expected["profile_sha256"]


def test_current_large_change_cli_compilation_and_conversion_keep_the_complete_contract(tmp_path):
    platform = native_resources.ROOT / "platform/upstream/platform"
    example = platform / "portable/examples/large-change"
    package = platform / "portable/packages/large-change"
    task_type = platform / "task-types/large-change"
    request = json.loads((task_type / "examples/request.json").read_text(encoding="utf-8"))
    parts = {name: json.loads((example / (name + ".json")).read_text(encoding="utf-8"))
             for name in ("task", "policy", "binding")}
    target, spec_target = tmp_path / "compiled.json", tmp_path / "task.spec.json"
    subprocess.run(
        [sys.executable, "-m", "ergora", "workflow", "compile", "--task", str(example / "task.json"),
         "--package", str(package / "manifest.json"), "--policy", str(example / "policy.json"),
         "--binding", str(example / "binding.json"), "--out", str(target), "--spec-out", str(spec_target)],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", check=True, timeout=30,
    )
    compiled = json.loads(target.read_text(encoding="utf-8"))
    converted_directory = tmp_path / "converted current request"
    subprocess.run(
        [sys.executable, "-m", "ergora", "workflow", "convert-v2", "--request", str(task_type / "examples/request.json"),
         "--project-id", parts["task"]["project_id"], "--out-dir", str(converted_directory)],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", check=True, timeout=30,
    )
    converted = json.loads((converted_directory / "compiled.json").read_text(encoding="utf-8"))
    environment = dict(os.environ, PYTHONPATH=str(platform), PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    original = subprocess.run(
        [sys.executable, "-P", "-S", "-c",
         "import json,sys;from dev_platform.registry import make_spec;print(json.dumps(make_spec(json.load(sys.stdin))))"],
        input=json.dumps(request), cwd=tmp_path, env=environment,
        capture_output=True, text=True, encoding="utf-8", check=True, timeout=30,
    )
    assert compiled["spec"] == converted["spec"] == json.loads(original.stdout)
    assert json.loads(spec_target.read_text(encoding="utf-8")) == compiled["spec"]
    assert json.loads((converted_directory / "task.spec.json").read_text(encoding="utf-8")) == converted["spec"]
    assert compiled["spec"]["request"] == request
    assert parts["task"]["input"] == converted["task"]["input"] == request["input"]
    assert request["input"] == native_resources.template_details("large-change")["input"]
    for name, value in parts.items():
        assert compiled[name] == value
        assert json.loads((converted_directory / (name + ".json")).read_text(encoding="utf-8")) == converted[name]
    for envelope in (compiled, converted):
        assert envelope["task"]["package_sha256"] == envelope["policy"]["package_sha256"] == envelope["digests"]["package"]
        assert envelope["binding"]["policy_sha256"] == envelope["digests"]["policy"]
        assert envelope["spec"]["request"]["profile_sha256"] == envelope["package"]["manifest"]["legacy_profile_sha256"]
        assert envelope["spec"]["profile_sha256"] == request["profile_sha256"]
        for name in ("README.md", "instructions.md"):
            assert envelope["package"]["templates"][name] == (package / name).read_text(encoding="utf-8")
            assert envelope["package"]["templates"][name] == (task_type / name).read_text(encoding="utf-8")


@pytest.fixture
def legacy_state(tmp_path):
    root, repo = tmp_path / "data", tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)

    def relocate(value):
        if isinstance(value, str):
            return value.replace("@HOME@", root.as_posix()).replace("@REPO@", repo.as_posix())
        if isinstance(value, dict):
            return {key: relocate(item) for key, item in value.items()}
        if isinstance(value, list):
            return [relocate(item) for item in value]
        return value

    fixture = relocate(json.loads((FIXTURES / "state.json").read_text(encoding="utf-8")))
    # Build the old DB independently of the current initialization/migration code.
    with sqlite3.connect(root / "ergora.sqlite3") as db:
        db.executescript((FIXTURES / "schema.sql").read_text(encoding="utf-8"))
        assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        for table, rows in fixture["rows"].items():
            for row in rows:
                values = [json.dumps(value) if isinstance(value, dict) else value for value in row.values()]
                db.execute(f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", values)
    for relative, text in fixture["assets"].items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
        target.chmod(0o644)
    return State(root), fixture


def test_old_state_documents_survive_reopen_and_keep_domain_statuses(legacy_state):
    state, fixture = legacy_state
    project = fixture["project"]
    rows = fixture["rows"]
    assert State(state.root).project(project) == rows["projects"][0]["document"]
    process = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "project", "show", project],
                             capture_output=True, text=True, encoding="utf-8", check=True)
    assert json.loads(process.stdout) == state.project(project)
    assert drafts.listing(state, project) == [rows["drafts"][0]["document"]]
    assert memory.history(state, project, "memory-1") == [row["document"] for row in rows["memories"]]
    assert memory.records(state, project) == [rows["memories"][-1]["document"]]
    digest = rows["skill_heads"][0]["digest"]
    assert skill_assets.get(state, project, digest) == rows["skill_versions"][0]["document"]
    assert skill_assets.versions(state, project)["active"] == rows["skill_heads"]
    assert evaluation.listing(state, project) == {
        "suites": [rows["evaluation_suites"][0]["document"]], "runs": [rows["evaluations"][0]["document"]]}
    assert optimization.listing(state, project) == [rows["optimizations"][0]["document"]]
    assert research.get(state, project, "research-1")["status"] == "cancelled"
    assert "Synthetic source snapshot" in research.proposal(state, project, "proposal-1")["text"]
    campaign = kernel.get(state, project, "kernel-1")
    assert campaign["status"] == "outcome_unknown" and campaign["requires_reconciliation"] is True
    assert agent_runs.runs(state, project)[0]["status"] == "failed"
    with state.connect() as db:
        for table, expected in rows.items():
            stored = [dict(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            for row in stored:
                for column in ("document", "binding"):
                    if column in row:
                        row[column] = json.loads(row[column])
            assert stored == expected, table


def test_old_project_draft_and_memory_reject_stale_revisions(legacy_state):
    state, fixture = legacy_state
    project = fixture["project"]
    with pytest.raises(ValueError, match="revision changed"):
        projects.bind(state, project, "reviewer", {"tool": "codex"}, expected_revision=2)
    with pytest.raises(ValueError, match="revision changed"):
        drafts.save(state, project, "draft-1", "repository-governance",
                    fixture["rows"]["drafts"][0]["document"]["input"], expected_revision=1)
    with pytest.raises(ValueError, match="revision changed"):
        memory.save(state, project, "stale overwrite", {"uri": "manual:synthetic", "revision": "3"},
                    memory_id="memory-1", expected_revision=1)
    assert state.project(project)["revision"] == 3
    assert drafts.listing(state, project)[0]["revision"] == 2
    assert memory.records(state, project)[0]["revision"] == 2
