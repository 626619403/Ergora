"""Upgrade the independently captured 0.2.0 schema without rewriting its records."""

from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys

import pytest

from ergora import state as storage
from ergora.state import State


LEGACY_SQL = (Path(__file__).parent / "fixtures/compatibility-v0_2_0/schema.sql").read_text(encoding="utf-8")
LEGACY_TABLES = set(re.findall(r"CREATE TABLE (\w+)", LEGACY_SQL))


@pytest.fixture
def old_home(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    document = {"schema_version": 1, "id": "demo", "repo": str(tmp_path), "revision": 3,
                "bindings": {"reviewer": {"tool": "codex"}}}
    with closing(sqlite3.connect(root / "ergora.sqlite3")) as db, db:
        db.executescript(LEGACY_SQL)
        db.execute("INSERT INTO projects VALUES (?,?)", ("demo", json.dumps(document)))
        db.execute("CREATE TABLE custom_extra (value TEXT)")
        db.execute("INSERT INTO custom_extra VALUES ('preserved')")
        db.execute("CREATE INDEX custom_project_index ON projects(document)")
        db.execute("CREATE TRIGGER custom_trigger AFTER INSERT ON custom_extra BEGIN SELECT 1; END")
    asset = root / "sources/demo/synthetic.raw"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"synthetic source, not a real user asset\n")
    return root, document


def test_new_state_has_complete_schema_without_lazy_ddl_or_backup(tmp_path):
    state = State(tmp_path / "new")
    with state.connect() as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        assert {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")} == LEGACY_TABLES
        assert db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0] == 48
        with closing(sqlite3.connect(":memory:")) as legacy:
            legacy.executescript(LEGACY_SQL)
            for table in LEGACY_TABLES:
                assert [tuple(row) for row in db.execute(f'PRAGMA table_xinfo("{table}")')] == legacy.execute(f'PRAGMA table_xinfo("{table}")').fetchall()
    State(state.root)
    assert not (state.root / "backups").exists()


@pytest.mark.parametrize("journal_mode", ["delete", "wal"])
def test_upgrade_preserves_rows_extra_objects_assets_and_restorable_v0_backup(old_home, journal_mode):
    root, document = old_home
    asset = root / "sources/demo/synthetic.raw"
    original_asset = hashlib.sha256(asset.read_bytes()).hexdigest()
    with closing(sqlite3.connect(root / "ergora.sqlite3")) as db:
        assert db.execute(f"PRAGMA journal_mode={journal_mode}").fetchone()[0] == journal_mode
        original = list(db.iterdump())
    state = State(root)
    assert state.project("demo") == document
    backups = list((root / "backups").glob("schema-v0-*.sqlite3"))
    assert len(backups) == 1
    with closing(sqlite3.connect(backups[0])) as backup:
        assert backup.execute("PRAGMA user_version").fetchone()[0] == 0
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert list(backup.iterdump()) == original
        # A pre-migration backup remains writable by an unmodified old client.
        with backup:
            backup.execute("UPDATE projects SET document=document WHERE id='demo'")
    with state.connect() as db:
        assert db.execute("SELECT value FROM custom_extra").fetchone()[0] == "preserved"
        assert {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE name LIKE 'custom_%'")} == {
            "custom_extra", "custom_project_index", "custom_trigger"}
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == original_asset
    assert State(root).project("demo") == document
    assert list((root / "backups").glob("*.sqlite3")) == backups


def test_partial_legacy_database_gains_missing_tables_without_rewriting_existing_rows(tmp_path):
    root = tmp_path / "partial"
    root.mkdir()
    with closing(sqlite3.connect(root / "ergora.sqlite3")) as db, db:
        db.execute("CREATE TABLE projects (id TEXT PRIMARY KEY, document TEXT NOT NULL)")
        db.execute("INSERT INTO projects VALUES ('partial', '{\"revision\":1}')")
    state = State(root)
    assert state.project("partial") == {"revision": 1}
    with state.connect() as db:
        assert {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")} == LEGACY_TABLES
    backup = next((root / "backups").glob("*.sqlite3"))
    with closing(sqlite3.connect(backup)) as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [("projects",)]
        assert db.execute("SELECT document FROM projects").fetchone()[0] == '{"revision":1}'


def test_already_open_legacy_client_cannot_write_any_of_the_16_tables(old_home):
    root, document = old_home
    with closing(sqlite3.connect(root / "ergora.sqlite3")) as old:
        old.execute("SELECT * FROM projects").fetchall()
        state = State(root)
        for table in LEGACY_TABLES:
            column = old.execute(f'PRAGMA table_info("{table}")').fetchone()[1]
            for sql in (f'INSERT INTO "{table}" DEFAULT VALUES', f'UPDATE "{table}" SET "{column}"="{column}"',
                        f'DELETE FROM "{table}"'):
                with pytest.raises(sqlite3.OperationalError, match="ergora_writer_schema_version"):
                    with old:
                        old.execute(sql)
        assert json.loads(old.execute("SELECT document FROM projects").fetchone()[0]) == document
        for version in (0, 2, None):
            old.create_function("ergora_writer_schema_version", 0, lambda: version)
            with pytest.raises(sqlite3.IntegrityError, match="Incompatible Ergora writer"):
                with old:
                    old.execute("UPDATE projects SET document=document")
    with state.connect() as db:
        db.execute("UPDATE projects SET document=document WHERE id='demo'")
    assert state.project("demo") == document


def test_failed_migration_rolls_back_ddl_version_and_writer_guards(old_home, monkeypatch):
    root, document = old_home
    migrate = storage._MIGRATIONS[0]

    def interrupted(db):
        migrate(db)
        db.execute("CREATE TABLE interrupted_marker (value TEXT)")
        raise RuntimeError("injected migration interruption")

    with monkeypatch.context() as patch:
        patch.setattr(storage, "_MIGRATIONS", (interrupted,))
        with pytest.raises(RuntimeError, match="injected migration interruption"):
            State(root)
    with closing(sqlite3.connect(root / "ergora.sqlite3")) as db, db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        assert db.execute("SELECT name FROM sqlite_master WHERE name='interrupted_marker'").fetchone() is None
        assert db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name LIKE 'ergora_writer_%'").fetchone()[0] == 0
        db.execute("UPDATE projects SET document=document")
    assert len(list((root / "backups").glob("*.sqlite3"))) == 1
    assert State(root).project("demo") == document


def test_abrupt_process_exit_during_migration_recovers_the_old_transaction(old_home):
    root, document = old_home
    code = '''import os,sys
from pathlib import Path
from ergora import state
original=state._MIGRATIONS[0]
def crash(db):
 original(db)
 os._exit(19)
state._MIGRATIONS=(crash,)
state.State(Path(sys.argv[1]))
'''
    child = subprocess.run([sys.executable, "-c", code, str(root)], capture_output=True, text=True, timeout=20)
    assert child.returncode == 19, child.stderr
    with closing(sqlite3.connect(root / "ergora.sqlite3")) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name LIKE 'ergora_writer_%'").fetchone()[0] == 0
    assert State(root).project("demo") == document


def test_backup_failure_prevents_any_migration(old_home, monkeypatch):
    root, document = old_home
    connect = sqlite3.connect

    def fail_backup(path, *args, **kwargs):
        if Path(str(path)).parent == root / "backups":
            Path(path).write_bytes(b"incomplete backup")
            raise sqlite3.OperationalError("injected backup storage failure")
        return connect(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(storage.sqlite3, "connect", fail_backup)
        with pytest.raises(ValueError, match="No complete pre-migration DB backup.*injected backup storage failure"):
            State(root)
    with closing(sqlite3.connect(root / "ergora.sqlite3")) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        assert json.loads(db.execute("SELECT document FROM projects").fetchone()[0]) == document
    assert not list((root / "backups").iterdir())


def test_unknown_layout_and_newer_versions_are_rejected_without_rewriting(tmp_path):
    invalid = tmp_path / "invalid"
    invalid.mkdir()
    with closing(sqlite3.connect(invalid / "ergora.sqlite3")) as db:
        db.execute("CREATE TABLE projects (id TEXT)")
    with pytest.raises(ValueError, match="Unsupported legacy table layout: projects"):
        State(invalid)
    with closing(sqlite3.connect(invalid / "ergora.sqlite3")) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        assert len(db.execute("PRAGMA table_info(projects)").fetchall()) == 1
    state = State(tmp_path / "future")
    with state.connect() as db:
        db.execute("PRAGMA user_version=2")
    original = (state.root / "ergora.sqlite3").read_bytes()
    with pytest.raises(ValueError, match="Unsupported database schema 2"):
        State(state.root)
    with pytest.raises(ValueError, match="Unsupported database schema 2"):
        with state.connect():
            pytest.fail("A stale State instance must not open the newer schema")
    assert (state.root / "ergora.sqlite3").read_bytes() == original
    assert not (state.root / "backups").exists()


def test_parallel_upgrade_and_project_revision_conflict_are_serialized(old_home):
    root, document = old_home
    code = '''import sys
from pathlib import Path
from ergora import projects
from ergora.state import State
state=State(Path(sys.argv[1]))
try:
 projects.bind(state,"demo","reviewer",{"tool":"codex","model":sys.argv[2]},3)
except ValueError as error:
 if "revision changed" not in str(error): raise
 print("conflict")
else: print("saved")
'''
    children = [subprocess.Popen([sys.executable, "-c", code, str(root), model], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True) for model in ("model-a", "model-b")]
    try:
        outcomes = [child.communicate(timeout=30) for child in children]
        assert all(child.returncode == 0 for child in children), outcomes
        assert sorted(output.strip() for output, _ in outcomes) == ["conflict", "saved"]
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=5)
    current = State(root).project("demo")
    assert current["revision"] == document["revision"] + 1
    assert len(list((root / "backups").glob("*.sqlite3"))) == 1
