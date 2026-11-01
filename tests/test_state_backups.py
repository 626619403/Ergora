"""Offline snapshots bind an unchanged database to the original local file assets."""

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from ergora import backups, contracts, memory, projects, skills
from ergora.state import State


@pytest.fixture
def archive_state(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    projects.create(state, "demo", repo)
    memory.save(state, "demo", "Persistent observation", {"uri": "manual:note", "revision": "one"})
    source = tmp_path / "demo-skill"
    source.mkdir()
    (source / "SKILL.md").write_text("---\nname: demo-skill\ndescription: Test fixture\n---\nKeep evidence.\n", encoding="utf-8")
    (source / "run.py").write_bytes(b"print('fixture')\n")
    if os.name != "nt":
        (source / "run.py").chmod(0o755)
    bundle = skills.import_bundle(state, "demo", source)
    raw = b"Synthetic source snapshot\n"
    digest = hashlib.sha256(raw).hexdigest()
    path = state.root / "sources/demo" / f"{digest}.raw"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    (state.root / "empty directory").mkdir()
    (state.root / "额外 文件.txt").write_text("preserve unknown ordinary files\n", encoding="utf-8")
    with state.connect() as db:
        db.execute("INSERT INTO source_snapshots VALUES (?,?,?,?)", ("demo", "https://example.invalid/source", digest, "{}"))
    return state, bundle, path


def test_full_roundtrip_preserves_canonical_rows_skills_sources_unknown_files_and_empty_dirs(archive_state, tmp_path):
    state, skill, raw = archive_state
    contracts.StrictValidator.check_schema(contracts.STATE_BACKUP)
    with state.connect() as db:
        before = [tuple(row) for row in db.execute("SELECT * FROM memories")]
        original_skill = db.execute("SELECT document FROM skill_versions").fetchone()[0]
    result = backups.create(state.root, tmp_path / "snapshot", offline=True)
    assert result["status"] == "backed_up" and result["skills"] == result["source_snapshots"] == 1
    assert result["database_schema_version"] == 1
    assert backups.verify(tmp_path / "snapshot")["manifest_sha256"] == result["manifest_sha256"]
    state.root.rename(tmp_path / "kept-original")
    restored = backups.restore(state.root, tmp_path / "snapshot", offline=True)
    assert restored["status"] == "restored" and restored["manifest_sha256"] == result["manifest_sha256"]
    reopened = State(state.root)
    assert skills.get(reopened, "demo", skill["digest"]) == skill
    assert (state.root / "empty directory").is_dir()
    assert (state.root / "额外 文件.txt").read_text(encoding="utf-8").startswith("preserve")
    assert raw.read_bytes() == b"Synthetic source snapshot\n"
    with reopened.connect() as db:
        assert [tuple(row) for row in db.execute("SELECT * FROM memories")] == before
        assert db.execute("SELECT document FROM skill_versions").fetchone()[0] == original_skill


def test_legacy_wal_snapshot_is_created_before_upgrade_and_restores_the_original_schema(tmp_path):
    root = tmp_path / "legacy"
    root.mkdir()
    with closing(sqlite3.connect(root / "ergora.sqlite3")) as old:
        old.execute("PRAGMA journal_mode=WAL")
        old.execute("PRAGMA wal_autocheckpoint=0")
        old.execute("CREATE TABLE projects (id TEXT PRIMARY KEY, document TEXT NOT NULL)")
        old.commit()
        old.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        encoded = '{"revision": 3, "original": "字节"}'
        with old:
            old.execute("INSERT INTO projects VALUES (?,?)", ("legacy", encoded))
        assert (root / "ergora.sqlite3-wal").stat().st_size > 0
        result = backups.create(root, tmp_path / "v0-backup", offline=True)
        assert result["database_schema_version"] == 0
        assert old.execute("PRAGMA user_version").fetchone()[0] == 0
        manifest = json.loads((tmp_path / "v0-backup/manifest.json").read_text())
        assert set(manifest["files"]) == {"ergora.sqlite3"}
    root.rename(tmp_path / "kept-v0")
    backups.restore(root, tmp_path / "v0-backup", offline=True)
    with closing(sqlite3.connect(root / "ergora.sqlite3")) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        assert db.execute("SELECT document FROM projects").fetchone()[0] == encoded
    assert State(root).project("legacy") == json.loads(encoded)


@pytest.mark.parametrize("mutation", ["changed", "missing", "extra", "directory", "mode"])
def test_verifier_rejects_asset_changes_before_creating_any_restore_target(archive_state, tmp_path, mutation):
    state, _, raw = archive_state
    target = tmp_path / "backup"
    backups.create(state.root, target, offline=True)
    copied = target / "data" / raw.relative_to(state.root)
    if mutation == "changed":
        copied.write_bytes(b"changed")
    elif mutation == "missing":
        copied.unlink()
    elif mutation == "extra":
        (target / "data/extra-file").write_bytes(b"extra")
    elif mutation == "directory":
        (target / "data/empty directory").rmdir()
    else:
        manifest = json.loads((target / "manifest.json").read_text())
        manifest["files"][copied.relative_to(target / "data").as_posix()]["mode"] ^= 0o100
        (target / "manifest.json").write_text(json.dumps(manifest))
    state.root.rename(tmp_path / "original-kept")
    with pytest.raises(ValueError, match="changed"):
        backups.restore(state.root, target, offline=True)
    assert not state.root.exists()


@pytest.mark.parametrize("mutation", ["version", "unsafe-file", "unsafe-directory", "platform", "database-version"])
def test_manifest_versions_paths_and_platform_are_checked(archive_state, tmp_path, mutation):
    state, _, _ = archive_state
    target = tmp_path / "backup"
    backups.create(state.root, target, offline=True)
    manifest = json.loads((target / "manifest.json").read_text())
    if mutation == "version":
        manifest["schema_version"] = 2
    elif mutation == "unsafe-file":
        manifest["files"]["../outside"] = manifest["files"]["ergora.sqlite3"]
    elif mutation == "unsafe-directory":
        manifest["directories"].append("C:\\outside")
    elif mutation == "platform":
        manifest["platform"] = "other-platform"
    else:
        manifest["database_schema_version"] = 2
    (target / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        backups.verify(target)


def test_database_to_asset_identity_is_checked_even_when_inventory_was_recomputed(archive_state, tmp_path):
    state, skill, _ = archive_state
    target = tmp_path / "backup"
    backups.create(state.root, target, offline=True)
    changed = target / "data" / Path(skill["path"]).relative_to(state.root) / "SKILL.md"
    changed.write_text("changed candidate\n")
    manifest = json.loads((target / "manifest.json").read_text())
    entry = manifest["files"][changed.relative_to(target / "data").as_posix()]
    entry.update(sha256=hashlib.sha256(changed.read_bytes()).hexdigest(), size=changed.stat().st_size)
    (target / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Skill asset identity"):
        backups.verify(target)


def test_inconsistent_source_snapshot_is_not_published_as_a_valid_backup(archive_state, tmp_path):
    state, _, raw = archive_state
    raw.write_bytes(b"does not match the source row")
    with pytest.raises(ValueError, match="Source snapshot identity"):
        backups.create(state.root, tmp_path / "backup", offline=True)
    assert not (tmp_path / "backup").exists()


def test_detected_source_file_mutation_aborts_the_offline_snapshot(archive_state, tmp_path, monkeypatch):
    state, _, raw = archive_state
    original = backups.shutil.copy2

    def change_source(source, target, *args, **kwargs):
        result = original(source, target, *args, **kwargs)
        if Path(source) == raw:
            raw.write_bytes(b"source writer was still active")
        return result

    monkeypatch.setattr(backups.shutil, "copy2", change_source)
    with pytest.raises(ValueError, match="State files changed"):
        backups.create(state.root, tmp_path / "backup", offline=True)
    assert not (tmp_path / "backup").exists()


def test_failed_restore_staging_keeps_the_archive_and_does_not_create_home(archive_state, tmp_path, monkeypatch):
    state, _, _ = archive_state
    target = tmp_path / "backup"
    created = backups.create(state.root, target, offline=True)
    state.root.rename(tmp_path / "original-kept")
    original = backups.shutil.copytree

    def fail_copy(source, destination, *args, **kwargs):
        original(source, destination, *args, **kwargs)
        raise OSError("injected restore copy failure")

    monkeypatch.setattr(backups.shutil, "copytree", fail_copy)
    with pytest.raises(OSError, match="injected restore copy failure"):
        backups.restore(state.root, target, offline=True)
    assert not state.root.exists()
    assert not list(tmp_path.glob(".ergora-restore-*"))
    assert backups.verify(target)["manifest_sha256"] == created["manifest_sha256"]


def test_offline_original_home_and_non_overwrite_are_enforced(archive_state, tmp_path):
    state, _, _ = archive_state
    target = tmp_path / "backup"
    with pytest.raises(ValueError, match="offline"):
        backups.create(state.root, target)
    with pytest.raises(ValueError, match="outside"):
        backups.create(state.root, state.root / "nested-backup", offline=True)
    backups.create(state.root, target, offline=True)
    with pytest.raises(ValueError, match="existing destinations"):
        backups.create(state.root, target, offline=True)
    with pytest.raises(ValueError, match="offline"):
        backups.restore(state.root, target)
    with pytest.raises(ValueError, match="nonexistent home"):
        backups.restore(state.root, target, offline=True)
    with pytest.raises(ValueError, match="original state home"):
        backups.restore(tmp_path / "different-home", target, offline=True)
    assert not (tmp_path / "different-home").exists()


def test_copy_failure_preserves_source_and_does_not_publish_a_partial_backup(archive_state, tmp_path, monkeypatch):
    state, skill, _ = archive_state
    original = backups.shutil.copy2

    def fail_copy(source, target, *args, **kwargs):
        original(source, target, *args, **kwargs)
        raise OSError("injected copy failure")

    monkeypatch.setattr(backups.shutil, "copy2", fail_copy)
    with pytest.raises(OSError, match="injected copy failure"):
        backups.create(state.root, tmp_path / "backup", offline=True)
    assert not (tmp_path / "backup").exists()
    assert not list(tmp_path.glob(".ergora-backup-*"))
    assert skills.get(state, "demo", skill["digest"]) == skill


@pytest.mark.skipif(os.name == "nt", reason="symlink creation needs an extra Windows privilege")
def test_source_and_archive_symlinks_are_rejected(archive_state, tmp_path):
    state, _, _ = archive_state
    external = tmp_path / "outside.txt"
    external.write_bytes(b"outside")
    link = state.root / "link"
    link.symlink_to(external)
    with pytest.raises(ValueError, match="symbolic links"):
        backups.create(state.root, tmp_path / "rejected", offline=True)
    link.unlink()
    backups.create(state.root, tmp_path / "backup", offline=True)
    (tmp_path / "backup/data/link").symlink_to(external)
    with pytest.raises(ValueError, match="symbolic links"):
        backups.verify(tmp_path / "backup")


@pytest.mark.skipif(os.name != "nt", reason="requires a real Windows junction")
def test_windows_junction_is_rejected_before_traversing_external_data(archive_state, tmp_path):
    state, _, _ = archive_state
    external = tmp_path / "external-directory"
    external.mkdir()
    (external / "outside.txt").write_bytes(b"outside")
    link = state.root / "junction"
    result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(external)], capture_output=True)
    assert result.returncode == 0, result.stderr
    try:
        with pytest.raises(ValueError, match="reparse points"):
            backups.create(state.root, tmp_path / "rejected", offline=True)
        assert not (tmp_path / "rejected").exists()
        assert (external / "outside.txt").read_bytes() == b"outside"
    finally:
        link.rmdir()


def test_cli_maintenance_does_not_create_or_migrate_state_implicitly(archive_state, tmp_path):
    state, _, _ = archive_state

    def cli(home, *arguments):
        return subprocess.run([sys.executable, "-m", "ergora", "--home", str(home), "state", *arguments],
                              capture_output=True, text=True, encoding="utf-8", timeout=20)

    absent = tmp_path / "absent"
    assert cli(absent, "info").returncode == 2 and not absent.exists()
    assert json.loads(cli(state.root, "info").stdout)["database_schema_version"] == 1
    assert cli(state.root, "backup", str(tmp_path / "without-flag")).returncode == 2
    assert not (tmp_path / "without-flag").exists()
    assert cli(state.root, "backup", str(tmp_path / "backup"), "--offline").returncode == 0
    assert json.loads(cli(state.root, "verify-backup", str(tmp_path / "backup")).stdout)["status"] == "verified"
    state.root.rename(tmp_path / "original")
    result = cli(state.root, "restore", str(tmp_path / "backup"), "--offline")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "restored"
