"""Exact local Git material and offline packet integrity, using real objects."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import review_packets


def git(repository, *arguments, input=None):
    result = subprocess.run(["git", "-C", str(repository), *arguments], input=input, capture_output=True)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


def commit(repository, message):
    git(repository, "-c", "user.name=Packet Test", "-c", "user.email=packet@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-qm", message)
    return git(repository, "rev-parse", "HEAD").decode().strip()


@pytest.fixture
def source(tmp_path):
    repository = tmp_path / "source"
    repository.mkdir()
    git(repository, "init", "-q", "--initial-branch=main")
    git(repository, "config", "core.autocrlf", "false")
    (repository / "src").mkdir()
    files = {"AGENTS.md": b"Root instructions\r\n", "src/AGENTS.md": b"Source instructions\n",
             "src/train.py": b"VALUE = 1\r\n", "src/old.py": "# 原内容\r\n".encode(),
             "src/deleted.py": b"DELETE = True\n", "caller.py": b"from src.train import VALUE\n",
             "config.toml": b"target = 1\n"}
    for path, raw in files.items():
        (repository / path).write_bytes(raw)
    git(repository, "add", ".")
    anchor = commit(repository, "anchor")
    (repository / "config.toml").write_bytes(b"target = 2\n")
    git(repository, "add", ".")
    base = commit(repository, "target advanced")
    git(repository, "checkout", "-qb", "candidate", anchor)
    (repository / "src/train.py").write_bytes("VALUE = 2  # 新候选\r\n".encode())
    (repository / "src/deleted.py").unlink()
    (repository / "src/old.py").rename(repository / "src/renamed.py")
    git(repository, "add", "-A")
    head = commit(repository, "candidate")
    requirements = tmp_path / "request.md"
    requirements.write_bytes("保留语义并核对调用者。\r\n".encode())
    evidence = tmp_path / "check.txt"
    evidence.write_bytes(b"operator supplied check output\r\n")
    options = {"repository_id": "example/training", "base": base, "head": head,
               "requirements": requirements, "context_paths": ["caller.py", "config.toml"], "evidence": [evidence]}
    return repository, anchor, options


def test_complete_diverged_sources_ignore_worktree_and_survive_repository_removal(source, tmp_path):
    repository, anchor, options = source
    (repository / "src/train.py").write_text("uncommitted content")
    (repository / "AGENTS.md").write_text("uncommitted instructions")
    (repository / "untracked.txt").write_text("untracked")
    destination = tmp_path / "review"
    result = review_packets.prepare(repository, destination=destination, **options)
    material = review_packets.read(destination, sha256=result["packet_sha256"])
    packet = material["packet"]
    assert packet["repository"] == {"id": options["repository_id"], "object_format": "sha1",
        "base": options["base"], "head": options["head"], "diff_base": anchor, "comparison": "merge-base"}
    assert [(item["path"], item["status"]) for item in packet["changes"]] == [
        ("src/deleted.py", "D"), ("src/old.py", "D"), ("src/renamed.py", "A"), ("src/train.py", "M")]
    assert packet["requirements"]["text"].encode() == options["requirements"].read_bytes()
    assert packet["evidence"][0]["text"].encode() == options["evidence"][0].read_bytes()
    source_material = packet["source"]
    for label in ("base", "diff_base", "head"):
        files = source_material[label]["files"]
        assert {"AGENTS.md", "src/AGENTS.md", "caller.py", "config.toml"} <= files.keys()
        for path, file in files.items():
            assert source_material["blobs"][file["git_object"]]["text"].encode() == git(
                repository, "cat-file", "blob", source_material[label]["commit"] + ":" + path)
    old_oid = source_material["diff_base"]["files"]["src/old.py"]["git_object"]
    assert old_oid == source_material["head"]["files"]["src/renamed.py"]["git_object"]
    assert "uncommitted" not in json.dumps(packet) and "untracked.txt" not in source_material["scope"]
    direct = review_packets.prepare(repository, destination=tmp_path / "direct", comparison="base", **options)
    assert direct["repository"]["diff_base"] == options["base"] and direct["changes"] == result["changes"] + 1
    # Git creates read-only loose objects; Windows requires writable files for deletion.
    for object_file in (repository / ".git/objects").rglob("*"):
        if object_file.is_file():
            object_file.chmod(0o600)
    shutil.rmtree(repository)
    assert review_packets.verify(destination, sha256=result["packet_sha256"]) == {key: value for key, value in result.items()
                                                                            if key != "directory"}


def test_cli_is_state_free_and_publication_never_replaces_an_existing_directory(source, tmp_path):
    repository, _, options = source
    destination, home = tmp_path / "packet", tmp_path / "unused-home"
    command = [sys.executable, "-m", "ergora", "--home", str(home), "review"]
    prepared = subprocess.run([*command, "prepare", str(repository), "--base", options["base"], "--head", options["head"],
        "--repository-id", options["repository_id"], "--requirements", str(options["requirements"]),
        "--directory", str(destination), "--context", "caller.py"], capture_output=True, text=True)
    assert prepared.returncode == 0, prepared.stderr
    digest = json.loads(prepared.stdout)["packet_sha256"]
    environment = dict(os.environ, PATH="")
    for operation in ("verify", "read"):
        result = subprocess.run([*command, operation, str(destination), "--sha256", digest],
                                env=environment, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["packet_sha256"] == digest
    assert not home.exists()
    original = (destination / "packet.json").read_bytes()
    with pytest.raises(OSError):
        review_packets.prepare(repository, destination=destination, **options)
    assert (destination / "packet.json").read_bytes() == original
    empty = tmp_path / "already-empty"
    empty.mkdir()
    with pytest.raises(OSError):
        review_packets.prepare(repository, destination=empty, **options)
    assert list(empty.iterdir()) == []
    with pytest.raises(ValueError, match="expected SHA256"):
        review_packets.verify(destination, sha256="0" * 64)


def test_git_environment_replacements_and_executable_repository_configuration_are_ignored(source, tmp_path, monkeypatch):
    repository, anchor, options = source
    marker, helper = tmp_path / "executed", tmp_path / "forbidden.py"
    helper.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n")
    command = f'"{Path(sys.executable).as_posix()}" "{helper.as_posix()}"'
    for key in ("diff.external", "diff.probe.textconv", "filter.probe.clean", "filter.probe.smudge"):
        git(repository, "config", key, command)
    (repository / ".git/info/attributes").write_text("* diff=probe filter=probe\n")
    git(repository, "replace", anchor, options["head"])
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "unrelated"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "diff.external")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", command)
    result = review_packets.prepare(repository, destination=tmp_path / "safe", **options)
    assert result["repository"]["diff_base"] == anchor
    packet = review_packets.read(tmp_path / "safe")["packet"]
    assert "VALUE = 1" in packet["source"]["diff"] and "VALUE = 2" in packet["source"]["diff"]
    assert not marker.exists()


@pytest.mark.parametrize("kind", ["binary", "non-utf8", "lfs", "symlink", "gitlink"])
def test_unsupported_source_rejects_the_whole_packet_with_known_uncovered_paths(source, tmp_path, kind):
    repository, _, options = source
    content = {"binary": b"zero\0byte", "non-utf8": b"\xff", "lfs": (
        b"version https://git-lfs.github.com/spec/v1\n" + b"oid sha256:" + b"0" * 64 + b"\nsize 20\n"),
        "symlink": b"elsewhere"}
    if kind == "gitlink":
        oid, mode = options["head"], "160000"
    else:
        oid = git(repository, "hash-object", "-w", "--stdin", input=content[kind]).decode().strip()
        mode = "120000" if kind == "symlink" else "100644"
    git(repository, "update-index", "--add", "--cacheinfo", mode, oid, "unsupported")
    options["head"] = commit(repository, "unsupported material")
    destination = tmp_path / "unsupported-packet"
    with pytest.raises(ValueError, match="no coverage claimed.*unsupported"):
        review_packets.prepare(repository, destination=destination, **options)
    assert not destination.exists()


def test_missing_promisor_blob_does_not_fetch_even_with_an_available_local_remote(source, tmp_path):
    repository, _, options = source
    remote = tmp_path / "remote.git"
    git(repository, "clone", "-q", "--bare", "--no-hardlinks", str(repository), str(remote))
    git(repository, "config", "remote.origin.url", str(remote))
    git(repository, "config", "remote.origin.promisor", "true")
    git(repository, "config", "remote.origin.partialclonefilter", "blob:none")
    git(repository, "config", "extensions.partialClone", "origin")
    git(repository, "config", "protocol.file.allow", "always")
    oid = git(repository, "rev-parse", options["head"] + ":src/train.py").decode().strip()
    object_file = repository / ".git/objects" / oid[:2] / oid[2:]
    object_file.chmod(0o600)
    object_file.unlink()
    with pytest.raises(ValueError, match="local Git blob"):
        review_packets.prepare(repository, destination=tmp_path / "missing", **options)
    assert not object_file.exists() and not (tmp_path / "missing").exists()


@pytest.mark.parametrize("payload_size", [2048, 8192])
def test_source_limits_follow_the_configured_budget_without_truncating(source, tmp_path, payload_size):
    repository, _, options = source
    (repository / "src/train.py").write_bytes(b"x" * payload_size)
    git(repository, "add", "src/train.py")
    options["head"] = commit(repository, "large candidate")
    first = tmp_path / "full"
    review_packets.prepare(repository, destination=first, **options)
    packet = review_packets.read(first)["packet"]
    total = sum(len(blob["text"].encode()) + len(f'{oid} blob {len(blob["text"].encode())}') + 2
                for oid, blob in packet["source"]["blobs"].items())
    configured = max(total, len(packet["source"]["diff"].encode())) + 512
    review_packets.prepare(repository, destination=tmp_path / "configured", max_source_bytes=configured, **options)
    rejected = tmp_path / "too-small"
    with pytest.raises(ValueError, match="no coverage claimed.*input byte limit"):
        review_packets.prepare(repository, destination=rejected, max_source_bytes=total - 1, **options)
    assert not rejected.exists()


def test_document_budget_stops_aggregate_reads_before_building_an_oversized_packet(source, tmp_path, monkeypatch):
    repository, _, options = source
    evidence = [tmp_path / "large-baseline.txt", tmp_path / "large-candidate.txt"]
    for path in evidence:
        path.write_bytes(b"x" * (review_packets.MAX_PACKET_BYTES * 3 // 5))
    options["evidence"] = evidence
    observed, original = [], Path.open
    documents = {options["requirements"], *evidence}

    class ObservedReader:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def read(self, size):
            raw = self.stream.read(size)
            observed.append(len(raw))
            return raw

        def __exit__(self, *args):
            self.stream.close()

    def opening(path, *args, **kwargs):
        stream = original(path, *args, **kwargs)
        return ObservedReader(stream) if path in documents and args == ("rb",) else stream

    monkeypatch.setattr(Path, "open", opening)
    with pytest.raises(ValueError, match="packet.*byte|10 MB"):
        review_packets.prepare(repository, destination=tmp_path / "over-budget", **options)
    assert sum(observed) <= review_packets.MAX_PACKET_BYTES + 1
    assert not (tmp_path / "over-budget").exists()


@pytest.mark.parametrize("tamper", ["blob", "dangling", "change", "scope", "document", "diff"])
def test_offline_verification_checks_content_and_reference_consistency(source, tmp_path, tamper):
    repository, _, options = source
    destination = tmp_path / "review"
    review_packets.prepare(repository, destination=destination, **options)
    packet = json.loads((destination / "packet.json").read_bytes())
    oid = next(iter(packet["source"]["blobs"]))
    if tamper == "blob":
        packet["source"]["blobs"][oid]["text"] += "modified"
    elif tamper == "dangling":
        del packet["source"]["blobs"][oid]
    elif tamper == "change":
        packet["changes"].pop()
    elif tamper == "scope":
        packet["source"]["scope"].remove("AGENTS.md")
    elif tamper == "document":
        packet["requirements"]["text"] += "modified"
    else:
        packet["source"]["diff"] = "there are no changes"
    (destination / "packet.json").write_bytes(json.dumps(packet).encode())
    with pytest.raises(ValueError):
        review_packets.verify(destination)


def test_one_commit_cannot_have_conflicting_file_tables_in_different_labels(source, tmp_path):
    repository, _, options = source
    destination = tmp_path / "review"
    review_packets.prepare(repository, comparison="base", destination=destination, **options)
    packet = json.loads((destination / "packet.json").read_bytes())
    packet["source"]["base"]["files"]["src/train.py"] = packet["source"]["head"]["files"]["src/train.py"]
    (destination / "packet.json").write_bytes(json.dumps(packet).encode())
    with pytest.raises(ValueError, match="same commit"):
        review_packets.verify(destination)


def test_offline_diff_cannot_exceed_the_collected_material_budget(source, tmp_path):
    repository, _, options = source
    destination = tmp_path / "review"
    review_packets.prepare(repository, destination=destination, **options)
    packet = json.loads((destination / "packet.json").read_bytes())
    packet["source"]["diff"] += "x" * packet["limits"]["max_source_bytes"]
    packet["source"]["diff_sha256"] = hashlib.sha256(packet["source"]["diff"].encode()).hexdigest()
    (destination / "packet.json").write_bytes(json.dumps(packet).encode())
    with pytest.raises(ValueError, match="diff exceeds.*byte limit"):
        review_packets.verify(destination)


def test_ambiguous_merge_base_requires_explicit_direct_comparison(source, tmp_path):
    repository, anchor, options = source
    tree = git(repository, "rev-parse", anchor + "^{tree}").decode().strip()
    def node(parents, message):
        args = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit-tree", tree]
        for parent in parents:
            args.extend(["-p", parent])
        return git(repository, *args, input=message.encode()).decode().strip()
    left, right = node([anchor], "left"), node([anchor], "right")
    options.update(base=node([left, right], "merge-left"), head=node([right, left], "merge-right"))
    with pytest.raises(ValueError, match="unique merge-base"):
        review_packets.prepare(repository, destination=tmp_path / "ambiguous", **options)
    result = review_packets.prepare(repository, comparison="base", destination=tmp_path / "explicit", **options)
    assert result["changes"] == 0 and result["repository"]["diff_base"] == options["base"]


def test_sha256_git_objects_are_verified_without_assuming_sha1_width(tmp_path):
    repository = tmp_path / "sha256"
    repository.mkdir()
    git(repository, "init", "-q", "--initial-branch=main", "--object-format=sha256")
    (repository / "source.txt").write_bytes(b"old\n")
    git(repository, "add", ".")
    base = commit(repository, "base")
    (repository / "source.txt").write_bytes(b"new\r\n")
    git(repository, "add", ".")
    head = commit(repository, "head")
    requirements = tmp_path / "request.md"
    requirements.write_text("Preserve behavior")
    result = review_packets.prepare(repository, repository_id="local/sha256", base=base, head=head,
                                    requirements=requirements, destination=tmp_path / "review")
    assert result["repository"]["object_format"] == "sha256" and len(head) == 64
    assert review_packets.verify(tmp_path / "review")["packet_sha256"] == result["packet_sha256"]
