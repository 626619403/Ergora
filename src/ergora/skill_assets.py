"""Agent Skills assets, content identities and atomic version-head history."""

import difflib
import json
from pathlib import Path
import re
import shutil
import tempfile

import yaml

from .state import State, file_lock, now
from .asset_trees import digest_tree


def metadata(directory: Path) -> dict:
    text = (directory / "SKILL.md").read_text(encoding="utf-8-sig")
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


def versions(state: State, project_id: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        return {"versions": [json.loads(row[0]) for row in db.execute(
                    "SELECT document FROM skill_versions WHERE project=? ORDER BY rowid DESC", (project_id,))],
                "active": [dict(row) for row in db.execute("SELECT * FROM skill_heads WHERE project=?", (project_id,))],
                "history": [json.loads(row[0]) for row in db.execute(
                    "SELECT document FROM skill_events WHERE project=? ORDER BY rowid DESC", (project_id,))]}


def get(state: State, project_id: str, digest: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM skill_versions WHERE project=? AND digest=?", (project_id, digest)).fetchone()
    if row is None:
        raise ValueError("Unknown skill version in this project")
    document = json.loads(row[0])
    actual, _ = digest_tree(Path(document["path"]))
    if actual != digest:
        raise ValueError("Stored skill content changed; refuse to use modified evidence")
    return document


def diff(state: State, project_id: str, baseline: str, candidate: str) -> dict:
    before, after = get(state, project_id, baseline), get(state, project_id, candidate)
    before_text = (Path(before["path"]) / "SKILL.md").read_text(encoding="utf-8")
    after_text = (Path(after["path"]) / "SKILL.md").read_text(encoding="utf-8")
    changed = [name for name in sorted(set(before["files"]) | set(after["files"])) if before["files"].get(name) != after["files"].get(name)]
    return {"diff": "".join(difflib.unified_diff(before_text.splitlines(True), after_text.splitlines(True), fromfile=baseline[:12], tofile=candidate[:12])),
            "changed_files": changed, "baseline": before, "candidate": after}


def import_bundle(state: State, project_id: str, source: Path, hypothesis: str = "Imported candidate",
                  parent: str | None = None) -> dict:
    state.project(project_id)
    source = source.expanduser().resolve(strict=True)
    original_digest, _ = digest_tree(source)
    publication = state.root / "skills" / project_id / original_digest
    publication.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".import-", dir=publication) as temporary:
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
        destination = publication / meta["name"]
        with file_lock(publication / ".import.lock"), state.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT document FROM skill_versions WHERE project=? AND digest=?", (project_id, digest)).fetchone()
            actual = digest_tree(destination)[0] if destination.exists() else None
            if actual != digest:
                if existing:
                    raise ValueError("Stored skill content changed; refuse to replace registered evidence")
                # Only an unregistered orphan can be replaced. The verified copy
                # shares its parent filesystem so readers never see a partial tree.
                if destination.exists():
                    shutil.rmtree(destination)
                copy.rename(destination)
            if existing:
                return json.loads(existing[0])
            previous = db.execute("SELECT digest FROM skill_heads WHERE project=? AND name=?", (project_id, meta["name"])).fetchone()
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


def rollback(state: State, project_id: str, name: str, digest: str, expected_revision: int, reason: str) -> dict:
    target = get(state, project_id, digest)
    if target["name"] != name:
        raise ValueError("Rollback target is a different skill")
    history = versions(state, project_id)["history"]
    if not any(event["to"] == digest for event in history):
        raise ValueError("Rollback target was never an active version")
    return move_head(state, project_id, name, digest, expected_revision, "rollback", reason)


def move_head(state: State, project_id: str, name: str, digest: str, expected_revision: int,
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
