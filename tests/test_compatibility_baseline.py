"""Pinned pre-refactor identities and synthetic 0.2.0 persisted documents."""

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from ergora import drafts, evaluation, kernel, memory, optimization, projects, reference, research, skills, tools
from ergora.state import State


FIXTURES = Path(__file__).parent / "fixtures/compatibility-v0_2_0"
IDENTITIES = json.loads((FIXTURES / "identities.json").read_text(encoding="utf-8"))


def test_distinct_json_identity_vectors_are_preserved(tmp_path):
    payload = IDENTITIES["payload"]
    assert evaluation.manifest_sha256(payload) == IDENTITIES["evaluation_sha256"]
    environment = dict(os.environ, PYTHONPATH=str(reference.ROOT / "platform/upstream/platform"),
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
    digest, files = skills.digest_tree(tmp_path)
    assert digest == expected["digest"]
    assert files == expected["files"]


@pytest.mark.parametrize("kind", ["repository-governance", "large-change"])
def test_compiled_examples_keep_exact_pre_refactor_identity(tmp_path, kind):
    example = reference.ROOT / "platform/upstream/platform/portable/examples" / kind
    package = reference.ROOT / "platform/upstream/platform/portable/packages" / kind / "manifest.json"
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
    assert skills.get(state, project, digest) == rows["skill_versions"][0]["document"]
    assert skills.versions(state, project)["active"] == rows["skill_heads"]
    assert evaluation.listing(state, project) == {
        "suites": [rows["evaluation_suites"][0]["document"]], "runs": [rows["evaluations"][0]["document"]]}
    assert optimization.listing(state, project) == [rows["optimizations"][0]["document"]]
    assert research.get(state, project, "research-1")["status"] == "cancelled"
    assert "Synthetic source snapshot" in research.proposal(state, project, "proposal-1")["text"]
    campaign = kernel.get(state, project, "kernel-1")
    assert campaign["status"] == "outcome_unknown" and campaign["requires_reconciliation"] is True
    assert tools.runs(state, project)[0]["status"] == "failed"
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
