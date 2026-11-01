"""Offline state snapshots; canonical records and their absolute paths stay intact."""

from contextlib import closing, contextmanager
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import sqlite3
import stat
import sys
import tempfile

from . import contracts, skills
from .state import SCHEMA_VERSION, file_lock, now


_SOURCE_EXCLUSIONS = {".schema.lock", "ergora.sqlite3", "ergora.sqlite3-wal", "ergora.sqlite3-shm", "ergora.sqlite3-journal"}


def _relative(value: str) -> Path:
    path = PurePosixPath(value)
    if (path.is_absolute() or PureWindowsPath(value).drive or path.as_posix() != value or
            not path.parts or any(part in (".", "..") for part in path.parts) or "\\" in value or "\0" in value):
        raise ValueError(f"Unsafe state backup path: {value!r}")
    return Path(*path.parts)


def _is_link(path: Path) -> bool:
    details = path.lstat()
    return stat.S_ISLNK(details.st_mode) or bool(
        getattr(details, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _inventory(root: Path, exclusions=frozenset()) -> tuple[dict, list[str]]:
    if not root.is_dir() or _is_link(root):
        raise ValueError(f"State backup requires a real directory: {root}")
    files, directories = {}, []
    pending = [root]
    while pending:
        # Inspect links / Windows junctions before descending; recursive globbing
        # may traverse a reparse point before its results can be checked.
        for path in pending.pop().iterdir():
            relative = path.relative_to(root).as_posix()
            if relative in exclusions:
                continue
            _relative(relative)
            if _is_link(path):
                raise ValueError(f"State backup does not follow symbolic links or reparse points: {relative}")
            if path.is_dir():
                directories.append(relative)
                pending.append(path)
            elif path.is_file():
                details = path.stat()
                with path.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                files[relative] = {"sha256": digest, "size": details.st_size, "mode": stat.S_IMODE(details.st_mode)}
            else:
                raise ValueError(f"State backup does not copy special files: {relative}")
    return dict(sorted(files.items())), sorted(directories)


@contextmanager
def _database(path: Path, *, writable: bool = False):
    if not path.is_file() or _is_link(path):
        raise ValueError(f"No regular state database at {path}")
    try:
        uri = path.resolve().as_uri() + ("?mode=rw" if writable else "?mode=ro")
        with closing(sqlite3.connect(uri, uri=True, timeout=15)) as db:
            db.row_factory = sqlite3.Row
            yield db
    except sqlite3.Error as error:
        raise ValueError(f"State database operation failed at {path}: {error}") from error


def info(root: Path) -> dict:
    with _database(root / "ergora.sqlite3") as db:
        version = db.execute("PRAGMA user_version").fetchone()[0]
    return {"home": str(root), "database_schema_version": version, "current_schema_version": SCHEMA_VERSION,
            "supported": 0 <= version <= SCHEMA_VERSION, "upgrade_required": 0 <= version < SCHEMA_VERSION}


def _check_assets(db: sqlite3.Connection, data: Path, original_home: Path) -> dict:
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    checked = {"skills": 0, "source_snapshots": 0}
    if "skill_versions" in tables:
        for row in db.execute("SELECT digest,document FROM skill_versions"):
            document = json.loads(row["document"])
            if (not isinstance(document, dict) or not isinstance(document.get("path"), str) or
                    not isinstance(document.get("digest"), str)):
                raise ValueError("Invalid Skill asset record in state backup database")
            try:
                relative = Path(document["path"]).relative_to(original_home).as_posix()
            except ValueError as error:
                raise ValueError("Skill asset path does not belong to the recorded state home") from error
            actual, _ = skills.digest_tree(data / _relative(relative))
            if actual != row["digest"] or document["digest"] != row["digest"]:
                raise ValueError(f"Skill asset identity does not match database: {relative}")
            checked["skills"] += 1
    if "source_snapshots" in tables:
        for row in db.execute("SELECT project,sha FROM source_snapshots"):
            relative = _relative(f"sources/{row['project']}/{row['sha']}.raw")
            with (data / relative).open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != row["sha"]:
                raise ValueError(f"Source snapshot identity does not match database: {relative}")
            checked["source_snapshots"] += 1
    return checked


def verify(backup: Path) -> dict:
    if not backup.is_dir() or _is_link(backup) or _is_link(backup / "manifest.json"):
        raise ValueError("State backup and manifest must not be symbolic links")
    encoded = (backup / "manifest.json").read_bytes()
    manifest = json.loads(encoded.decode("utf-8"))
    contracts.validate(manifest, contracts.STATE_BACKUP, "State backup manifest")
    if manifest["platform"] != sys.platform:
        raise ValueError("State backup verification and restore require the recorded platform")
    original_home = Path(manifest["source_home"])
    if not original_home.is_absolute():
        raise ValueError("State backup source_home must be absolute")
    for value in [*manifest["directories"], *manifest["files"]]:
        _relative(value)
    data = backup / "data"
    files, directories = _inventory(data)
    if files.keys() != manifest["files"].keys():
        raise ValueError("State backup file inventory changed (missing or unexpected files)")
    for name, details in files.items():
        if details != manifest["files"][name]:
            raise ValueError(f"State backup file changed: {name}")
    if directories != manifest["directories"]:
        raise ValueError("State backup directory inventory changed")
    with _database(data / "ergora.sqlite3") as db:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version != manifest["database_schema_version"] or not 0 <= version <= SCHEMA_VERSION:
            raise ValueError("State backup database version is mismatched or unsupported")
        if [row[0] for row in db.execute("PRAGMA integrity_check")] != ["ok"]:
            raise ValueError("State backup database integrity check failed")
        assets = _check_assets(db, data, original_home)
    return {"status": "verified", "backup": str(backup.resolve()), "source_home": str(original_home),
            "platform": manifest["platform"], "database_schema_version": version, "files": len(files),
            "manifest_sha256": hashlib.sha256(encoded).hexdigest(), **assets}


def create(root: Path, destination: Path, *, offline: bool = False) -> dict:
    if not offline:
        raise ValueError("Stop state writers and external work, then explicitly select --offline")
    destination = destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Choose a new backup directory; existing destinations are not replaced")
    destination = destination.resolve()
    if destination.is_relative_to(root):
        raise ValueError("Choose a backup directory outside the state home")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".ergora-backup-", dir=destination.parent) as temporary:
        bundle = Path(temporary) / "bundle"
        data = bundle / "data"
        data.mkdir(parents=True, mode=0o700)
        bundle.chmod(0o700)
        with file_lock(root / ".schema.lock"), _database(root / "ergora.sqlite3", writable=True) as db, db:
            db.execute("BEGIN IMMEDIATE")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if not 0 <= version <= SCHEMA_VERSION:
                raise ValueError(f"Unsupported state database schema {version}")
            files, directories = _inventory(root, _SOURCE_EXCLUSIONS)
            with closing(sqlite3.connect(data / "ergora.sqlite3")) as snapshot:
                with _database(root / "ergora.sqlite3") as reader:
                    reader.backup(snapshot)
                snapshot.execute("PRAGMA journal_mode=DELETE")
            (data / "ergora.sqlite3").chmod(0o600)
            for directory in directories:
                (data / _relative(directory)).mkdir(parents=True, exist_ok=True, mode=0o700)
            for name in files:
                target = data / _relative(name)
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                shutil.copy2(root / _relative(name), target)
            if _inventory(root, _SOURCE_EXCLUSIONS) != (files, directories):
                raise ValueError("State files changed during offline backup; stop writers before retrying")
            copied, copied_directories = _inventory(data)
            for name, details in files.items():
                if copied[name] != details:
                    raise ValueError(f"State file changed while copying: {name}")
            manifest = {"schema_version": 1, "source_home": str(root), "platform": sys.platform,
                        "database_schema_version": version, "created": now(),
                        "directories": copied_directories, "files": copied}
            (bundle / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        result = verify(bundle)
        if destination.exists() or destination.is_symlink():
            raise ValueError("Backup destination appeared during copying; it was not replaced")
        bundle.rename(destination)
    return {**result, "status": "backed_up", "backup": str(destination)}


def restore(root: Path, backup: Path, *, offline: bool = False) -> dict:
    if not offline:
        raise ValueError("Stop state writers and external work, then explicitly select --offline")
    result = verify(backup)
    if Path(result["source_home"]) != root:
        raise ValueError("Restore requires the original state home; absolute record paths are not rewritten")
    if root.exists() or root.is_symlink():
        raise ValueError("Restore requires a nonexistent home; keep the existing home aside before restoring")
    root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".ergora-restore-", dir=root.parent) as temporary:
        bundle = Path(temporary) / "bundle"
        bundle.mkdir(mode=0o700)
        shutil.copy2(backup / "manifest.json", bundle / "manifest.json")
        shutil.copytree(backup / "data", bundle / "data")
        staged = verify(bundle)
        if staged != {**result, "backup": str(bundle.resolve())}:
            raise ValueError("State backup changed while staging restore")
        if root.exists() or root.is_symlink():
            raise ValueError("Restore target appeared during staging; it was not replaced")
        (bundle / "data").rename(root)
    return {**result, "status": "restored", "home": str(root)}
