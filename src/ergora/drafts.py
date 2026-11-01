"""Editable input drafts; formal task freezing remains in the reference compiler."""

import json
import re

from . import reference
from .state import State, now


def listing(state: State, project_id: str) -> list[dict]:
    state.project(project_id)
    with state.connect() as db:
        return [json.loads(row[0]) for row in db.execute("SELECT document FROM drafts WHERE project=? ORDER BY id", (project_id,))]


def save(state: State, project_id: str, name: str, kind: str, task_input: dict, expected_revision: int) -> dict:
    state.project(project_id)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
        raise ValueError("Draft ID must use letters, digits, underscores or hyphens")
    validation = reference.validate_input(kind, task_input)
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT document FROM drafts WHERE project=? AND id=?", (project_id, name)).fetchone()
        revision = json.loads(previous[0])["revision"] if previous else 0
        if revision != expected_revision:
            raise ValueError("Draft revision changed; reload before saving")
        document = {"schema_version": 1, "project": project_id, "id": name, "kind": kind,
                    "revision": revision + 1, "input": task_input, "validation": validation,
                    "updated": now(), "state": "draft"}
        db.execute("INSERT OR REPLACE INTO drafts VALUES (?, ?, ?)", (project_id, name, json.dumps(document)))
    return document
