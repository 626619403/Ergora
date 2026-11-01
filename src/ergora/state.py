"""Durable local state shared by the CLI and control plane."""

from contextlib import closing, contextmanager
from datetime import datetime, timezone
import errno
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid


_TABLES = {
    "projects": "(id TEXT PRIMARY KEY, document TEXT NOT NULL)",
    "agent_runs": "(id TEXT PRIMARY KEY, project TEXT NOT NULL, document TEXT NOT NULL)",
    "memories": "(project TEXT, id TEXT, revision INTEGER, document TEXT NOT NULL, PRIMARY KEY(project, id, revision))",
    "memory_mirrors": "(project TEXT, endpoint TEXT, id TEXT, revision INTEGER, binding TEXT NOT NULL, PRIMARY KEY(project, endpoint, id))",
    "skill_versions": "(project TEXT, digest TEXT, document TEXT, PRIMARY KEY(project,digest))",
    "skill_heads": "(project TEXT, name TEXT, digest TEXT, revision INTEGER, PRIMARY KEY(project,name))",
    "skill_events": "(project TEXT, name TEXT, document TEXT)",
    "evaluation_suites": "(project TEXT, digest TEXT, document TEXT, PRIMARY KEY(project,digest))",
    "evaluations": "(id TEXT PRIMARY KEY, project TEXT, document TEXT)",
    "optimizations": "(id TEXT PRIMARY KEY, project TEXT, document TEXT)",
    "research_runs": "(id TEXT PRIMARY KEY,project TEXT,cancel INTEGER,document TEXT)",
    "source_snapshots": "(project TEXT,url TEXT,sha TEXT,document TEXT,PRIMARY KEY(project,url,sha))",
    "source_heads": "(project TEXT,url TEXT,sha TEXT,PRIMARY KEY(project,url))",
    "research_proposals": "(id TEXT PRIMARY KEY,project TEXT,document TEXT)",
    "drafts": "(project TEXT,id TEXT,document TEXT,PRIMARY KEY(project,id))",
    "kernel_runs": "(id TEXT PRIMARY KEY, project TEXT, document TEXT)",
}


def _schema_v1(db: sqlite3.Connection) -> None:
    with closing(sqlite3.connect(":memory:")) as expected:
        for table, declaration in _TABLES.items():
            expected.execute(f'CREATE TABLE "{table}" {declaration}')
            columns = [tuple(row) for row in db.execute(f'PRAGMA table_xinfo("{table}")')]
            if columns and columns != expected.execute(f'PRAGMA table_xinfo("{table}")').fetchall():
                raise ValueError(f"Unsupported legacy table layout: {table}; original data was not rewritten")
            db.execute(f'CREATE TABLE IF NOT EXISTS "{table}" {declaration}')
            # Old 0.2.0 clients never inspect user_version. Requiring a registered
            # writer function also fences their already-open SQLite connections.
            for operation in ("INSERT", "UPDATE", "DELETE"):
                db.execute(f'''CREATE TRIGGER "ergora_writer_v1_{table}_{operation.lower()}"
                    BEFORE {operation} ON "{table}"
                    WHEN ergora_writer_schema_version() IS NOT 1
                    BEGIN SELECT RAISE(ABORT, 'Incompatible Ergora writer; upgrade before writing'); END''')


_MIGRATIONS = (_schema_v1,)
SCHEMA_VERSION = len(_MIGRATIONS)


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
        with file_lock(self.root / ".schema.lock"), closing(self._open()) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version == SCHEMA_VERSION:
                return
            if not 0 <= version < SCHEMA_VERSION:
                raise ValueError(f"Unsupported database schema {version}; this Ergora supports {SCHEMA_VERSION}. Use a compatible release")
            backup = None
            try:
                with db:
                    db.execute("BEGIN IMMEDIATE")
                    if db.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone():
                        directory = self.root / "backups"
                        directory.mkdir(exist_ok=True, mode=0o700)
                        backup = directory / f"schema-v{version}-{uuid.uuid4().hex}.sqlite3"
                        staging = backup.with_suffix(".sqlite3.part")
                        complete = False
                        try:
                            # A separate reader avoids backup waiting on its own
                            # write transaction; BEGIN IMMEDIATE excludes writers.
                            uri = (self.root / "ergora.sqlite3").as_uri() + "?mode=ro"
                            with closing(sqlite3.connect(uri, uri=True)) as source, closing(sqlite3.connect(staging)) as target:
                                source.backup(target)
                                if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                                    raise ValueError("Pre-migration database backup failed its integrity check")
                            staging.chmod(0o600)
                            staging.replace(backup)
                            complete = True
                        finally:
                            if not complete:
                                staging.unlink(missing_ok=True)
                    for next_version in range(version + 1, SCHEMA_VERSION + 1):
                        _MIGRATIONS[next_version - 1](db)
                        db.execute(f"PRAGMA user_version={next_version}")
            except (OSError, sqlite3.Error, ValueError) as error:
                detail = f"Pre-migration DB backup: {backup}" if backup and backup.exists() else "No complete pre-migration DB backup was created"
                raise ValueError(f"State migration failed; database transaction rolled back. {detail}. {error}") from error

    def _open(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.root / "ergora.sqlite3", timeout=15)
        db.row_factory = sqlite3.Row
        db.create_function("ergora_writer_schema_version", 0, lambda: SCHEMA_VERSION, deterministic=True)
        return db

    @contextmanager
    def connect(self):
        db = self._open()
        try:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version != SCHEMA_VERSION:
                raise ValueError(f"Unsupported database schema {version}; expected {SCHEMA_VERSION}. Reopen with a compatible Ergora release")
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
