"""Durable local state shared by the CLI and control plane."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class State:
    def __init__(self, root: Path | None = None):
        default = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "ergora"
        self.root = Path(root or os.environ.get("ERGORA_HOME", default)).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, document TEXT NOT NULL)")
            db.execute("""CREATE TABLE IF NOT EXISTS agent_runs (
                id TEXT PRIMARY KEY, project TEXT NOT NULL, document TEXT NOT NULL)""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.root / "ergora.sqlite3", timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def project(self, project_id: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT document FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown project: {project_id}")
        return json.loads(row[0])
