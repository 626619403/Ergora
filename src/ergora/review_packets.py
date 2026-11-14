"""State-free local source review material; never formal candidate approval."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

from . import contracts
from .asset_trees import is_link, publish_directory
from .definition_bundles import parse_json, relative_path
from .git_materials import GitMaterials, text_blob


MAX_PACKET_BYTES = 10_000_000
_SCHEMA = json.loads((Path(__file__).parent / "data/schemas/local-review-packet-v1.json").read_text(encoding="utf-8"))
_COVERAGE = {"changed_sources": "complete", "context": "explicit-files-only",
             "instructions": "ancestor-AGENTS.md", "checks": "operator-supplied-unverified",
             "execution_authorized": False, "platform_approval": False}


def _document(path: Path, remaining_bytes: int) -> tuple[dict, int]:
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Review document requires an ordinary file: " + str(path))
    with path.open("rb") as stream:
        raw = stream.read(remaining_bytes + 1)
    if len(raw) > remaining_bytes or b"\0" in raw:
        raise ValueError("Review document exceeds remaining packet byte budget or contains binary content: " + str(path))
    return {"name": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "text": raw.decode("utf-8")}, len(raw)


def _instructions(paths: list[str]) -> list[str]:
    names = {"AGENTS.md"}
    for name in paths:
        names.update((parent / "AGENTS.md").as_posix() for parent in PurePosixPath(name).parents)
    return sorted(names)


def _changes(reader: GitMaterials, before: str, after: str) -> list[dict]:
    raw = reader.read("diff", "--raw", "-z", "--no-abbrev", "--no-renames", "--no-ext-diff",
                      "--no-textconv", "--ignore-submodules=none", "--no-relative", before, after, "--")
    fields, changes = raw.split(b"\0"), []
    for index in range(0, len(fields) - 1, 2):
        old_mode, new_mode, old_oid, new_oid, status = fields[index].decode("ascii").removeprefix(":").split()
        path = fields[index + 1].decode("utf-8")
        relative_path(path, "Review source")
        changes.append({"path": path, "status": status,
            "before": None if old_mode == "000000" else {"mode": old_mode, "git_object": old_oid},
            "after": None if new_mode == "000000" else {"mode": new_mode, "git_object": new_oid}})
    return sorted(changes, key=lambda item: item["path"])


def _check(packet: dict) -> None:
    contracts.validate(packet, _SCHEMA, "Local review packet")
    repository, source = packet["repository"], packet["source"]
    oid_length = {"sha1": 40, "sha256": 64}[repository["object_format"]]
    by_commit = {}
    for label in ("base", "head", "diff_base"):
        if not re.fullmatch("[0-9a-f]{" + str(oid_length) + "}", repository[label]):
            raise ValueError("Review requires full commit IDs for its object format")
        if source[label]["commit"] != repository[label]:
            raise ValueError("Review source commit differs from its repository identity")
        files = source[label]["files"]
        if by_commit.setdefault(repository[label], files) != files:
            raise ValueError("Review source tables for the same commit differ")
    if repository["comparison"] == "base" and repository["base"] != repository["diff_base"]:
        raise ValueError("Direct review comparison differs from base")
    changes, contexts = packet["changes"], packet["context_paths"]
    paths = [item["path"] for item in changes]
    if paths != sorted(set(paths)) or contexts != sorted(set(contexts)):
        raise ValueError("Review paths require a unique sorted inventory")
    instructions = _instructions(paths + contexts)
    scope = sorted(set(paths + contexts + instructions))
    if source["scope"] != scope:
        raise ValueError("Review scope differs from changes, context and ancestor instructions")
    for path in scope:
        relative_path(path, "Review source")
    referenced = set()
    for label in ("base", "diff_base", "head"):
        for path, file in source[label]["files"].items():
            if path not in scope:
                raise ValueError("Review contains a source outside its declared scope: " + path)
            if file["git_object"] not in source["blobs"]:
                raise ValueError("Review source lacks its complete blob: " + path)
            referenced.add(file["git_object"])
    if referenced != source["blobs"].keys():
        raise ValueError("Review blob inventory differs from source references")
    for path in contexts:
        if not any(path in source[label]["files"] for label in ("base", "diff_base", "head")):
            raise ValueError("Review context must name an existing exact file, not a directory: " + path)
    before_files, after_files = source["diff_base"]["files"], source["head"]["files"]
    differences = {path for path in before_files.keys() | after_files.keys()
                   if before_files.get(path) != after_files.get(path)}
    if differences != set(paths):
        raise ValueError("Review change inventory differs from its selected before/after sources")
    for change in changes:
        for side, label in (("before", "diff_base"), ("after", "head")):
            if change[side] != source[label]["files"].get(change["path"]):
                raise ValueError("Review change differs from its exact source: " + change["path"])
        before, after = change["before"], change["after"]
        status = "A" if before is None else "D" if after is None else "M"
        if change["status"] != status or before == after:
            raise ValueError("Review change has inconsistent status or identical sources: " + change["path"])
    total = 0
    for oid, blob in source["blobs"].items():
        content = blob["text"].encode("utf-8")
        actual = hashlib.new(repository["object_format"], b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        if actual != oid or text_blob(content) != blob:
            raise ValueError("Review blob content differs from its Git object or SHA256: " + oid)
        total += len(content) + len(f"{oid} blob {len(content)}") + 2
    if total > packet["limits"]["max_source_bytes"]:
        raise ValueError("Review source exceeds its declared input byte limit")
    diff = source["diff"].encode("utf-8")
    if len(diff) > packet["limits"]["max_source_bytes"]:
        raise ValueError("Review diff exceeds its declared input byte limit")
    if hashlib.sha256(diff).hexdigest() != source["diff_sha256"]:
        raise ValueError("Review diff content differs from its SHA256")
    for document in (packet["requirements"], *packet["evidence"]):
        if "\0" in document["text"] or hashlib.sha256(document["text"].encode("utf-8")).hexdigest() != document["sha256"]:
            raise ValueError("Review document content differs from its SHA256: " + document["name"])
    if not packet["requirements"]["text"].strip():
        raise ValueError("Review requirements must contain the original request")


def _summary(packet: dict, sha256: str) -> dict:
    return {"packet_sha256": sha256, "repository": packet["repository"], "changes": len(packet["changes"]),
            "source_files": {label: len(packet["source"][label]["files"]) for label in ("base", "diff_base", "head")},
            "context_paths": packet["context_paths"], "evidence_documents": len(packet["evidence"]),
            "coverage": packet["coverage"]}


def prepare(repository: Path, *, repository_id: str, base: str, head: str, requirements: Path,
            destination: Path, context_paths: list[str] | None = None, evidence: list[Path] | None = None,
            comparison: str = "merge-base", max_source_bytes: int = 1_000_000) -> dict:
    """Freeze local objects into a new directory without running target code."""
    if not 1 <= max_source_bytes <= MAX_PACKET_BYTES:
        raise ValueError("Review max_source_bytes must be between 1 and 10000000")
    reader = GitMaterials(repository.expanduser().absolute(), max_bytes=max_source_bytes)
    object_format = reader.read("rev-parse", "--show-object-format").decode("ascii").strip()
    oid_length = {"sha1": 40, "sha256": 64}.get(object_format)
    for commit in (base, head):
        if oid_length is None or not re.fullmatch("[0-9a-f]{" + str(oid_length) + "}", commit):
            raise ValueError("Review base and head must be full lowercase commit IDs, not refs or abbreviations")
        if reader.read("cat-file", "-t", commit).strip() != b"commit":
            raise ValueError("Review requires actual local commit objects")
    if comparison == "merge-base":
        bases = reader.read("merge-base", "--all", base, head).decode("ascii").splitlines()
        if len(bases) != 1:
            raise ValueError("Review requires one unique merge-base; select explicit base comparison if appropriate")
        diff_base = bases[0]
    elif comparison == "base":
        diff_base = base
    else:
        raise ValueError("Review comparison must be merge-base or base")
    try:
        changes = _changes(reader, diff_base, head)
    except ValueError as error:
        raise ValueError("Review packet not published; complete change inventory unavailable: " + str(error)) from error
    contexts = sorted(set(context_paths or []))
    selected = [item["path"] for item in changes] + contexts
    scope = sorted(set(selected + _instructions(selected)))
    try:
        if len(scope) > 500:
            raise ValueError("Review scope exceeds 500 selected paths")
        for path in scope:
            relative_path(path, "Review source")
        source = reader.repository_sources({"base": base, "diff_base": diff_base, "head": head}, scope)
        source["diff"] = reader.read("diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--no-relative",
            "--no-color", "--text", "--diff-algorithm=myers", "--no-indent-heuristic", "--unified=3",
            "--src-prefix=a/", "--dst-prefix=b/", "--ignore-submodules=none", "-O", os.devnull,
            diff_base, head, "--").decode("utf-8")
        source["diff_sha256"] = hashlib.sha256(source["diff"].encode("utf-8")).hexdigest()
        if len(evidence or []) > _SCHEMA["properties"]["evidence"]["maxItems"]:
            raise ValueError("Review packet exceeds its evidence document count limit")
        request, used = _document(requirements, MAX_PACKET_BYTES)
        documents = []
        for path in evidence or []:
            document, size = _document(path, MAX_PACKET_BYTES - used)
            used += size
            documents.append(document)
        packet = {"schema_version": 1, "kind": "local-source-review", "repository": {
            "id": repository_id, "object_format": object_format, "base": base, "head": head,
            "diff_base": diff_base, "comparison": comparison}, "changes": changes, "context_paths": contexts,
            "source": source, "requirements": request, "evidence": documents,
            "limits": {"max_source_bytes": max_source_bytes}, "coverage": dict(_COVERAGE)}
        _check(packet)
        encoded = (json.dumps(packet, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(encoded) > MAX_PACKET_BYTES:
            raise ValueError("Complete review packet exceeds 10 MB including JSON, diff and documents")
    except (ValueError, OSError) as error:
        raise ValueError("Review packet not published; no coverage claimed for " + json.dumps(scope, ensure_ascii=False)
                         + ": " + str(error)) from error
    destination = destination.expanduser().absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".review-", dir=destination.parent) as temporary:
        staged = Path(temporary) / "packet"
        staged.mkdir()
        (staged / "packet.json").write_bytes(encoded)
        publish_directory(staged, destination)
    return {"directory": str(destination), **_summary(packet, hashlib.sha256(encoded).hexdigest())}


def read(directory: Path, *, sha256: str | None = None) -> dict:
    """Verify complete material offline; does not authenticate its Git origin."""
    directory = directory.expanduser().absolute()
    if is_link(directory) or not directory.is_dir() or {path.name for path in directory.iterdir()} != {"packet.json"}:
        raise ValueError("Review directory must contain exactly one ordinary packet.json")
    path = directory / "packet.json"
    if is_link(path) or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Review packet requires an ordinary file")
    with path.open("rb") as stream:
        encoded = stream.read(MAX_PACKET_BYTES + 1)
    if len(encoded) > MAX_PACKET_BYTES:
        raise ValueError("Complete review packet exceeds 10 MB")
    actual = hashlib.sha256(encoded).hexdigest()
    if sha256 is not None and sha256 != actual:
        raise ValueError("Review packet differs from expected SHA256")
    packet = parse_json(encoded.decode("utf-8"), "local review packet")
    _check(packet)
    return {"packet_sha256": actual, "packet": packet}


def verify(directory: Path, *, sha256: str | None = None) -> dict:
    material = read(directory, sha256=sha256)
    return _summary(material["packet"], material["packet_sha256"])
