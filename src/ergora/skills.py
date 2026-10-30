"""Agent Skills assets, immutable candidates and explicit adoption history."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import tempfile

import yaml

from .state import State, now


def digest_tree(directory: Path) -> tuple[str, dict]:
    files = {}
    total = 0
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or ".git" in path.relative_to(directory).parts:
            raise ValueError("Skill bundles cannot contain symlinks or .git")
        if path.is_file():
            total += path.stat().st_size
            if total > 10_000_000 or len(files) >= 500:
                raise ValueError("Skill bundle exceeds 10 MB / 500 files")
            files[path.relative_to(directory).as_posix()] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "executable_bits": stat.S_IMODE(path.stat().st_mode) & 0o111,
            }
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return digest, files


def metadata(directory: Path) -> dict:
    text = (directory / "SKILL.md").read_text()
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("SKILL.md requires YAML frontmatter")
    try:
        frontmatter = yaml.safe_load(text[4:].split("\n---\n", 1)[0])
    except yaml.YAMLError as error:
        raise ValueError("Invalid skill YAML frontmatter") from error
    if not isinstance(frontmatter, dict):
        raise ValueError("Skill frontmatter must be a mapping")
    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
            or len(name) > 64 or not isinstance(description, str) or not 1 <= len(description) <= 1024):
        raise ValueError("Agent Skills requires a lowercase kebab name (1–64) and description (1–1024)")
    return {"name": name, "description": description}


def _schema(state: State):
    with state.connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS skill_versions (project TEXT, digest TEXT, document TEXT, PRIMARY KEY(project,digest))")
        db.execute("CREATE TABLE IF NOT EXISTS skill_heads (project TEXT, name TEXT, digest TEXT, revision INTEGER, PRIMARY KEY(project,name))")
        db.execute("CREATE TABLE IF NOT EXISTS skill_events (project TEXT, name TEXT, document TEXT)")


def versions(state: State, project_id: str) -> dict:
    state.project(project_id)
    _schema(state)
    with state.connect() as db:
        return {"versions": [json.loads(row[0]) for row in db.execute(
                    "SELECT document FROM skill_versions WHERE project=? ORDER BY rowid DESC", (project_id,))],
                "active": [dict(row) for row in db.execute("SELECT * FROM skill_heads WHERE project=?", (project_id,))],
                "history": [json.loads(row[0]) for row in db.execute(
                    "SELECT document FROM skill_events WHERE project=? ORDER BY rowid DESC", (project_id,))]}


def get(state: State, project_id: str, digest: str) -> dict:
    state.project(project_id)
    _schema(state)
    with state.connect() as db:
        row = db.execute("SELECT document FROM skill_versions WHERE project=? AND digest=?", (project_id, digest)).fetchone()
    if row is None:
        raise ValueError("Unknown skill version in this project")
    document = json.loads(row[0])
    actual, _ = digest_tree(Path(document["path"]))
    if actual != digest:
        raise ValueError("Stored skill content changed; refuse to use modified evidence")
    return document


def import_bundle(state: State, project_id: str, source: Path, hypothesis: str = "Imported candidate",
                  parent: str | None = None) -> dict:
    state.project(project_id)
    _schema(state)
    source = source.expanduser().resolve(strict=True)
    original_digest, _ = digest_tree(source)
    staging = state.root / "imports"
    staging.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=staging) as temporary:
        copy = Path(temporary) / "bundle"
        shutil.copytree(source, copy, symlinks=True)
        digest, files = digest_tree(copy)
        if digest != original_digest:
            raise ValueError("Skill source changed while importing; retry a stable source")
        meta = metadata(copy)
        if source.name != meta["name"]:
            raise ValueError("Source directory name must match the skill name")
        if parent is not None and get(state, project_id, parent)["name"] != meta["name"]:
            raise ValueError("Candidate parent belongs to a different skill")
        destination = state.root / "skills" / project_id / digest / meta["name"]
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(copy, destination)
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT digest FROM skill_heads WHERE project=? AND name=?", (project_id, meta["name"])).fetchone()
        existing = db.execute("SELECT document FROM skill_versions WHERE project=? AND digest=?", (project_id, digest)).fetchone()
        if existing:
            return json.loads(existing[0])
        document = {**meta, "project": project_id, "digest": digest, "path": str(destination), "files": files,
                    "parent": parent or (previous[0] if previous else None), "hypothesis": hypothesis,
                    "source": str(source), "created": now()}
        db.execute("INSERT INTO skill_versions VALUES (?, ?, ?)", (project_id, digest, json.dumps(document)))
        if previous is None:
            db.execute("INSERT INTO skill_heads VALUES (?, ?, ?, 1)", (project_id, meta["name"], digest))
            event = {"action": "baseline", "to": digest, "reason": "Initial imported baseline; not a measured improvement", "at": now()}
            db.execute("INSERT INTO skill_events VALUES (?, ?, ?)", (project_id, meta["name"], json.dumps(event)))
    return document


def export(state: State, project_id: str, digest: str, destination: Path) -> dict:
    document = get(state, project_id, digest)
    if destination.exists():
        raise ValueError("Choose a new export directory")
    if destination.name != document["name"]:
        raise ValueError("Export directory name must match the skill name")
    shutil.copytree(document["path"], destination)
    return {"digest": digest, "destination": str(destination.resolve())}


def adopt(state: State, project_id: str, baseline_run: str, candidate_run: str, expected_revision: int, reason: str) -> dict:
    from .evaluation import compare

    comparison = compare(state, project_id, baseline_run, candidate_run)
    if not comparison["eligible"]:
        raise ValueError("Candidate is not eligible: " + "; ".join(comparison["reasons"]))
    candidate = get(state, project_id, comparison["candidate"])
    return _move_head(state, project_id, candidate["name"], comparison["candidate"], expected_revision,
                      "adopt", reason, expected_digest=comparison["baseline"], evidence=[baseline_run, candidate_run])


def rollback(state: State, project_id: str, name: str, digest: str, expected_revision: int, reason: str) -> dict:
    target = get(state, project_id, digest)
    if target["name"] != name:
        raise ValueError("Rollback target is a different skill")
    history = versions(state, project_id)["history"]
    if not any(event["to"] == digest for event in history):
        raise ValueError("Rollback target was never an active version")
    return _move_head(state, project_id, name, digest, expected_revision, "rollback", reason)


def _move_head(state: State, project_id: str, name: str, digest: str, expected_revision: int,
               action: str, reason: str, expected_digest: str | None = None, evidence: list | None = None) -> dict:
    if not reason.strip():
        raise ValueError("A reason is required for adoption or rollback")
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        head = db.execute("SELECT digest,revision FROM skill_heads WHERE project=? AND name=?", (project_id, name)).fetchone()
        if head is None or head["revision"] != expected_revision or (expected_digest and head["digest"] != expected_digest):
            raise ValueError("Active skill changed; reload and evaluate the current baseline")
        event = {"action": action, "from": head["digest"], "to": digest, "revision": expected_revision + 1,
                 "evidence": evidence or [], "reason": reason, "at": now()}
        db.execute("UPDATE skill_heads SET digest=?,revision=? WHERE project=? AND name=?",
                   (digest, expected_revision + 1, project_id, name))
        db.execute("INSERT INTO skill_events VALUES (?, ?, ?)", (project_id, name, json.dumps(event)))
    return event
