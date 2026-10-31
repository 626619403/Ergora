"""Durable local state shared by the CLI and control plane."""

from contextlib import contextmanager
from datetime import datetime, timezone
import errno
import json
import os
from pathlib import Path
import sqlite3
import time


@contextmanager
def file_lock(path: Path, *, blocking: bool = True):
    """Cross-process mutex; keep the file open for the whole remote operation."""
    with path.open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            # Byte-range locks may extend beyond EOF; never rewrite a locked byte.
            while True:
                lock.seek(0)
                try:
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as error:
                    if error.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                        raise
                    if not blocking:
                        raise BlockingIOError("File is locked by another operation") from error
                    time.sleep(.05)
            try:
                yield lock
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            yield lock


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class State:
    def __init__(self, root: Path | None = None):
        if os.name == "nt":
            default = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Ergora/data"
        else:
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
