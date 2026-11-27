"""State-independent shared case CLI and original publication boundaries."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Barrier

import pytest

import ergora
from ergora.configuration import projects
from ergora.improvement import memory, shared_cases
from ergora.storage.state import State


_FIXTURE = Path(__file__).parent / "fixtures" / "shared-task-mcp-missing.md"
_ID = "task-mcp-missing-sdk"
_SIGNATURE = "Task MCP requires the optional dependency"
_MATCH = {"technology": "ergora-task-mcp", "environment": "linux", "version": "0.2.0"}


@pytest.fixture
def library(tmp_path):
    path = tmp_path / "explicit library"
    path.mkdir()
    return path


def _draft(path, *, body=None, **metadata):
    _, header, original = _FIXTURE.read_bytes().split(b"---\n", 2)
    if body is None:
        body = original.decode("utf-8")
    data = {**json.loads(header), **metadata}
    path.write_bytes(f"---\n{json.dumps(data, ensure_ascii=False)}\n---\n{body}".encode("utf-8"))
    return path


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _publish(library, draft, expected_revision):
    return shared_cases.publish(library, draft, expected_revision, sha256=_digest(draft))


def _environment():
    return {**os.environ, "PYTHONPATH": str(Path(ergora.__file__).resolve().parents[1]), "PYTHONIOENCODING": "utf-8"}


def _cli(library, *args, cwd=None, home=None):
    env = _environment()
    if home is not None:
        env["ERGORA_HOME"] = str(home)
    return subprocess.run([sys.executable, "-m", "ergora", "memory", "shared", *args,
                           "--library", str(library)], env=env, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", timeout=30)


def test_shared_cli_matches_exact_case_in_two_workspaces(library, tmp_path):
    first, second = tmp_path / "workspace-a", tmp_path / "workspace-b"
    first.mkdir()
    second.mkdir()
    home = tmp_path / "absent state"
    assert _cli(library, "search", _SIGNATURE, cwd=first, home=home).returncode == 0
    assert list(library.iterdir()) == []
    sha256 = _digest(_FIXTURE)
    published = _cli(library, "publish", str(_FIXTURE), "--expected-revision", "0", "--sha256", sha256,
                     cwd=first, home=home)
    assert published.returncode == 0, published.stderr
    receipt = json.loads(published.stdout)
    assert receipt["record"]["sha256"] == sha256

    options = [item for name, value in _MATCH.items() for item in ("--" + name, value)]
    for workspace, query in ((first, "任务 MCP 启动失败"), (second, "ERROR: " + _SIGNATURE + ": pip install ...")):
        search = _cli(library, "search", query, *options, cwd=workspace, home=home)
        assert search.returncode == 0, search.stderr
        result, = json.loads(search.stdout)["results"]
        assert (result["id"], result["revision"], result["sha256"]) == (_ID, 1, sha256)
        assert result["applicability_match"] == {"status": "matched", "missing": [], "mismatched": []}
        assert "markdown" not in result
        show = _cli(library, "show", _ID, "--revision", "1", "--sha256", sha256, *options, cwd=workspace, home=home)
        assert show.returncode == 0, show.stderr
        assert json.loads(show.stdout)["markdown"].encode("utf-8") == _FIXTURE.read_bytes()
    assert not home.exists()


def test_shared_ranking_distinguishes_wrong_scope_unknown_and_unresolved(library, tmp_path):
    _publish(library, _FIXTURE, 0)
    alternative = _draft(
        tmp_path / "alternate.md", id="task-mcp-pending-triage", status="unresolved",
        title=_SIGNATURE, error_signatures=[], aliases=["任务 MCP 启动失败"],
        applicability={"technology": "ergora-task-mcp", "environment": "windows", "versions": ["0.2.1"]},
        body="# Controlled alternative\nThe cause is unconfirmed. Verify the mode's platform admission first.\n")
    _publish(library, alternative, 0)

    verified, unresolved = shared_cases.search(library, _SIGNATURE, facts=_MATCH)["results"]
    assert (verified["id"], verified["status"], verified["match"]["field"]) == (_ID, "verified", "error_signature")
    assert verified["applicability_match"]["status"] == "matched"
    assert (unresolved["status"], unresolved["applicability_match"]) == (
        "unresolved", {"status": "incompatible", "missing": [], "mismatched": ["environment", "version"]})
    wrong = shared_cases.show(library, _ID, facts={**_MATCH, "environment": "windows", "version": "0.2.1"})
    assert wrong["record"]["applicability_match"]["mismatched"] == ["environment", "version"]
    assert shared_cases.search(library, _SIGNATURE)["results"][0]["applicability_match"]["status"] == "unknown"
    assert shared_cases.search(library, "unrelated observation")["results"] == []


def test_shared_and_project_search_use_distinct_sources(library, tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "state")
    projects.create(state, "alpha", repo)
    private = memory.save(state, "alpha", _SIGNATURE + " private observation", {"uri": "manual:private", "revision": "r1"})
    _publish(library, _FIXTURE, 0)

    shared = _cli(library, "search", _SIGNATURE, cwd=repo, home=state.root)
    assert shared.returncode == 0, shared.stderr
    assert [result["id"] for result in json.loads(shared.stdout)["results"]] == [_ID]
    assert private["text"] not in shared.stdout
    assert memory.search(state, "alpha", _SIGNATURE)["results"] == [private]
    assert memory.search(state, "alpha", "启动失败")["results"] == []


def test_publish_rejects_an_edited_reviewed_draft_without_creating_library_files(library, tmp_path):
    path = _draft(tmp_path / "reviewed.md", title="Reviewed draft")
    reviewed = _digest(path)
    _draft(path, title="Different draft at the same path")
    refused = _cli(library, "publish", str(path), "--expected-revision", "0", "--sha256", reviewed)
    assert refused.returncode == 2 and not refused.stdout
    assert "Reviewed shared case Markdown digest changed" in refused.stderr
    assert list(library.iterdir()) == []


def test_shared_case_preserves_opaque_bounded_source_references(library, tmp_path):
    revision = "3bd4779a0a6fa303e528d285e82b41668812b8db"
    sources = [
        {"uri": "git:docs/definitions/workflows/leaf-calls.md", "revision": revision},
        {"uri": f"https://github.com/626619403/Ergora/blob/{revision}/pyproject.toml?plain=1", "revision": revision},
    ]
    draft = _draft(tmp_path / "references.md", sources=sources)
    receipt = _publish(library, draft, 0)["record"]
    shown = shared_cases.show(library, _ID, revision=1, sha256=receipt["sha256"])
    assert receipt["sources"] == shown["record"]["sources"] == sources
    assert shown["markdown"].encode("utf-8") == draft.read_bytes()


def test_only_one_concurrent_publisher_can_advance_the_same_revision(library, tmp_path):
    _publish(library, _FIXTURE, 0)
    first = _draft(tmp_path / "first.md", revision=2, title="First editor")
    second = _draft(tmp_path / "second.md", revision=2, title="Second editor")
    ready = Barrier(2)

    def submit(draft):
        ready.wait(timeout=5)
        return _cli(library, "publish", str(draft), "--expected-revision", "1", "--sha256", _digest(draft))

    with ThreadPoolExecutor(max_workers=2) as pool:
        attempts = list(pool.map(submit, (first, second)))
    assert sorted(result.returncode for result in attempts) == [0, 2]
    winner = next(json.loads(item.stdout)["record"] for item in attempts if item.returncode == 0)
    rejected = next(item.stderr for item in attempts if item.returncode == 2)
    assert "revision changed; expected 1, current 2" in rejected
    current, = shared_cases.search(library, _SIGNATURE)["results"]
    assert current["revision"] == 2 and current["sha256"] == winner["sha256"]
    assert {path.name for path in (library / "cases" / _ID).iterdir() if path.name.isdecimal()} == {"1", "2"}
    markdown = (first if winner["title"] == "First editor" else second).read_bytes()
    assert shared_cases.show(library, _ID, revision=2, sha256=winner["sha256"])["markdown"].encode("utf-8") == markdown


def test_publish_interruption_before_exposure_keeps_the_previous_revision(library, tmp_path):
    _publish(library, _FIXTURE, 0)
    second = _draft(tmp_path / "second.md", revision=2, title="Updated title")
    witness = """from pathlib import Path
from hashlib import sha256
import os
import sys
from ergora.improvement import shared_cases

shared_cases.publish_directory = lambda staged, destination: os._exit(93)
draft = Path(sys.argv[2])
shared_cases.publish(Path(sys.argv[1]), draft, 1, sha256=sha256(draft.read_bytes()).hexdigest())
"""
    interrupted = subprocess.run([sys.executable, "-c", witness, str(library), str(second)],
                                 env=_environment(), capture_output=True, timeout=30)
    assert interrupted.returncode == 93, interrupted.stderr
    staged, = (library / "cases" / _ID).glob(".pending-*")
    assert (staged / "case.md").read_bytes() == second.read_bytes()
    current, = shared_cases.search(library, _SIGNATURE)["results"]
    assert current["revision"] == 1
    assert shared_cases.show(library, _ID)["markdown"].encode("utf-8") == _FIXTURE.read_bytes()
    assert _publish(library, second, 1)["record"]["revision"] == 2
    assert shared_cases.show(library, _ID)["markdown"].encode("utf-8") == second.read_bytes()


def test_exact_read_distinguishes_drift_withdrawal_and_archive(library, tmp_path):
    original = _publish(library, _FIXTURE, 0)["record"]
    exact = shared_cases.show(library, _ID, revision=1, sha256=original["sha256"])
    second = _draft(tmp_path / "correction.md", revision=2, title="Corrected title")
    _publish(library, second, 1)
    with pytest.raises(ValueError, match="revision or digest changed"):
        shared_cases.show(library, _ID, revision=1, sha256=original["sha256"])
    withdrawn = _draft(tmp_path / "withdrawal.md", revision=3, status="withdrawn", body="Retired case.\n")
    _publish(library, withdrawn, 2)
    assert shared_cases.search(library, _SIGNATURE)["results"] == []
    metadata = shared_cases.show(library, _ID)
    assert (metadata["record"]["revision"], metadata["record"]["validity"], metadata["markdown"]) == (3, "withdrawn", None)
    rejected = _cli(library, "show", _ID, "--revision", "1", "--sha256", original["sha256"])
    assert rejected.returncode == 2 and "is withdrawn" in rejected.stderr and not rejected.stdout

    restored = tmp_path / "restored library"
    shutil.copytree(library, restored)
    assert shared_cases.show(restored, _ID)["record"] == metadata["record"]
    archived = restored / "cases" / _ID / "1" / "case.md"
    assert archived.read_bytes() == exact["markdown"].encode("utf-8")
    assert hashlib.sha256(archived.read_bytes()).hexdigest() == original["sha256"]


def test_expiry_of_latest_revision_never_reselects_an_older_revision(library, tmp_path, monkeypatch):
    decision = {"time": "2027-06-23T23:59:59+00:00"}
    monkeypatch.setattr(shared_cases, "now", lambda: decision["time"])
    _publish(library, _FIXTURE, 0)
    expiring = _draft(tmp_path / "expiry.md", revision=2, expires_at="2027-06-24T08:00:00+08:00")
    current = _publish(library, expiring, 1)["record"]
    assert shared_cases.search(library, _SIGNATURE)["results"][0]["revision"] == 2
    decision["time"] = "2027-06-24T00:00:00+00:00"
    assert shared_cases.search(library, _SIGNATURE)["results"] == []
    expired = shared_cases.show(library, _ID)
    assert expired["record"]["validity"] == "expired" and expired["markdown"] is None
    with pytest.raises(ValueError, match="is expired"):
        shared_cases.show(library, _ID, revision=2, sha256=current["sha256"])


def test_read_bounds_never_truncate_the_selected_markdown(library, tmp_path):
    query = "日志见证"
    complete = _draft(tmp_path / "complete.md", body="证据" * 1_000 + query)
    _publish(library, complete, 0)
    for index in range(6):
        alternate = _draft(tmp_path / f"{index}.md", id=f"alternate-{index}", body=query)
        _publish(library, alternate, 0)
    records = shared_cases.search(library, query)["results"]
    assert len(records) == 5
    wide, = [result for result in shared_cases.search(library, query, limit=7)["results"] if result["id"] == _ID]
    assert wide["match"]["truncated"]
    assert query in wide["match"]["excerpt"]
    assert len(wide["match"]["excerpt"].encode("utf-8")) <= shared_cases.MAX_EXCERPT_BYTES
    assert shared_cases.show(library, _ID, revision=1, sha256=wide["sha256"])["markdown"].encode("utf-8") == complete.read_bytes()
    with pytest.raises(ValueError, match="limit"):
        shared_cases.search(library, query, limit=21)

    # Simulate an off-contract edit so the reader's cap is tested independently of publish.
    stored = library / "cases" / _ID / "1" / "case.md"
    stored.write_bytes(b"x" * (shared_cases.MAX_MARKDOWN_BYTES + 1))
    with pytest.raises(ValueError, match="Markdown exceeds"):
        shared_cases.show(library, _ID)
    with pytest.raises(ValueError, match="Markdown exceeds"):
        _publish(library, stored, 1)


@pytest.mark.parametrize(("change", "error"), [
    ({"id": "../private"}, "portable"),
    ({"applicability": {"technology": "ergora-task-mcp", "versions": ["0.2.0"]}}, "environment and versions"),
    ({"status": "draft"}, "status requires"),
    ({"expires_at": "2027-06-24T08:00:00"}, "with timezone"),
    ({"sources": [{"uri": "", "revision": "r1"}]}, "nonempty uri and revision"),
])
def test_invalid_case_draft_is_rejected_before_library_mutation(library, tmp_path, change, error):
    draft = _draft(tmp_path / "case.md", **change)
    with pytest.raises(ValueError, match=error):
        _publish(library, draft, 0)
    assert list(library.iterdir()) == []
