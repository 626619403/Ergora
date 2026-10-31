"""Versioned project ownership and tool choices."""

import json
from pathlib import Path
import re
import sqlite3
import subprocess

from .state import State, now
from .tools import validate_binding


def create(state: State, project_id: str, repo: Path) -> dict:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", project_id):
        raise ValueError("Project ID must use 1–64 letters, digits, underscores or hyphens")
    repo = repo.expanduser().resolve(strict=True)
    result = subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise ValueError("Project root must be an existing Git repository")
    if Path(result.stdout.strip()).resolve() != repo:
        raise ValueError("Choose the Git repository root")
    document = {"schema_version": 1, "id": project_id, "repo": str(repo), "created": now(),
                "revision": 1, "bindings": {**{role: {"tool": "codex"} for role in (
                    "inspector", "planner", "implementer", "reviewer", "experiment-planner", "performance-analyst", "kernel-tuner")},
                                           "memory": {"tool": "sqlite"}, "optimizer": {"tool": "manual"},
                                           "research": {"tool": "urls"}, "scheduler": {"tool": "manual"}, "kernel": {"tool": "manual"}}}
    try:
        with state.connect() as db:
            db.execute("INSERT INTO projects VALUES (?, ?)", (project_id, json.dumps(document)))
    except sqlite3.IntegrityError as error:
        raise ValueError(f"Project already exists: {project_id}") from error
    return document


def list_projects(state: State) -> list[dict]:
    with state.connect() as db:
        return [json.loads(row[0]) for row in db.execute("SELECT document FROM projects ORDER BY id")]


def bind(state: State, project_id: str, layer: str, binding: dict, expected_revision: int) -> dict:
    validate_binding(layer, binding)
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT document FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown project: {project_id}")
        document = json.loads(row[0])
        if document["revision"] != expected_revision:
            raise ValueError("Project revision changed; reload before saving")
        document["bindings"][layer] = binding
        document["revision"] += 1
        db.execute("UPDATE projects SET document=? WHERE id=?", (json.dumps(document), project_id))
    return document
