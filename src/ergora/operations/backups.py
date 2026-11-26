"""Offline state snapshots; canonical records and their absolute paths stay intact."""

from contextlib import closing, contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import sqlite3
import stat
import sys
import tempfile

import ergora.definitions.agents as agent_definitions
from ergora.definitions.bundles import parse_json
import ergora.issues.application as issues
import ergora.issues.writebacks as issue_writebacks
import ergora.definitions.skills as skill_assets
import ergora.definitions.workflows as workflow_definitions
from ergora.configuration import validation as contracts
from ergora.storage.assets import is_link as _is_link
from ergora.storage.state import SCHEMA_VERSION, State, file_lock, now, resolve_home


_SOURCE_EXCLUSIONS = {".schema.lock", "ergora.sqlite3", "ergora.sqlite3-wal", "ergora.sqlite3-shm", "ergora.sqlite3-journal"}


def _relative(value: str) -> Path:
    path = PurePosixPath(value)
    if (path.is_absolute() or PureWindowsPath(value).drive or path.as_posix() != value or
            not path.parts or any(part in (".", "..") for part in path.parts) or "\\" in value or "\0" in value):
        raise ValueError(f"Unsafe state backup path: {value!r}")
    return Path(*path.parts)


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


@contextmanager
def _recovery_file(path: Path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError(f"Recovery scope requires an ordinary file: {path}")
        yield stream


def _file_identity(details: os.stat_result) -> tuple:
    return (details.st_dev, details.st_ino, details.st_mode, details.st_size,
            details.st_mtime_ns, details.st_ctime_ns)


def _control_catalog_inputs(root: Path) -> dict[str, tuple]:
    if os.path.lexists(root / "ergora.sqlite3-journal"):
        raise ValueError("Original control database has a rollback journal; recover that offline state before checking the scope")
    snapshot = {}
    for name in ("ergora.sqlite3", "ergora.sqlite3-wal"):
        try:
            details = (root / name).lstat()
        except FileNotFoundError:
            if name == "ergora.sqlite3":
                raise ValueError("No existing Ergora state database in the selected home") from None
            continue
        if not stat.S_ISREG(details.st_mode):
            raise ValueError(f"Control database and sidecars must be ordinary files: {root / name}")
        snapshot[name] = _file_identity(details)
    return snapshot


@contextmanager
def _offline_control_catalog(root: Path):
    # SQLite can write WAL or SHM even with mode=ro. Read retained WAL frames
    # and rebuild SHM in private staging without connecting to the original.
    temporary_base = Path("/tmp").resolve()
    if temporary_base.is_relative_to(root):
        raise ValueError("Control catalog staging requires a temporary directory outside the original control home")
    inputs = _control_catalog_inputs(root)
    with tempfile.TemporaryDirectory(prefix="ergora-recovery-scope-", dir=temporary_base) as temporary:
        staged = Path(temporary)
        changed = "Control database changed while staging recovery scope; stop writers before retrying"
        for name, identity in inputs.items():
            try:
                with _recovery_file(root / name) as reader, (staged / name).open("xb") as writer:
                    if _file_identity(os.fstat(reader.fileno())) != identity:
                        raise ValueError(changed)
                    shutil.copyfileobj(reader, writer)
            except FileNotFoundError as error:
                raise ValueError(changed) from error
        if _control_catalog_inputs(root) != inputs:
            raise ValueError(changed)
        with _database(staged / "ergora.sqlite3") as db:
            if [row[0] for row in db.execute("PRAGMA quick_check")] != ["ok"]:
                raise ValueError("Staged control database integrity check failed")
        yield State(staged, read_only=True)


def _recovery_directory(path: Path, name: str) -> Path:
    if not path.is_absolute() or not path.is_dir() or path.resolve() != path:
        raise ValueError(f"Missing or redirected original {name} directory: {path}")
    return path


def _temporal_file(entry: Path, *, database: bool = False) -> dict:
    target = entry
    try:
        link = os.readlink(entry) if entry.is_symlink() else None
        if link is not None:
            # Keep a direct symlink's exact text and every location tar must cover.
            # A multi-hop link or noncanonical intermediate directory needs manual inventory.
            target = Path(os.path.abspath(entry.parent / link))
            if link != os.path.normpath(link) or entry.resolve(strict=True) != target:
                raise ValueError(f"Recovery scope requires a direct Temporal SQLite link: {entry}")
        with _recovery_file(target) as stream:
            if database:
                if stream.read(16) != b"SQLite format 3\0":
                    raise ValueError(f"Original local Temporal database is not SQLite: {target}")
                stream.seek(0)
            size = os.fstat(stream.fileno()).st_size
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        return {"path": str(entry), "link": link, "payload_path": str(target),
                "size": size, "sha256": digest}
    except FileNotFoundError as error:
        raise ValueError(f"Missing original local Temporal SQLite dependency: {target} (from {entry})") from error


def recovery_scope(root: Path, project_id: str, *, task_id: str | None = None,
                   expected: Path | None = None) -> dict:
    """Observe one registered local stack while its execution writers are stopped."""
    from ergora.configuration import registrations
    from ergora.development import native
    from ergora.operations import services
    from ergora.storage.git import GitMaterials

    if sys.platform != "linux":
        raise ValueError("Registered local recovery scope requires Linux; use WSL2")
    control_home = resolve_home(root)
    with _offline_control_catalog(control_home) as catalog:
        project, database = services.local_temporal_recovery(catalog, project_id)
        observed = registrations.status(catalog, project_id)
    publication = registrations.publication_identity(control_home, project)
    if (not observed["consistent"] or observed["sha256"] != publication["sha256"]
            or observed["revision"] != project["revision"]):
        raise ValueError("Original project registration differs from its local publication")
    execution = project["registration"]["definition"]["execution"]
    directories = {"control_home": control_home, "repository": Path(project["repo"]),
                   **{name: Path(value) for name, value in execution.items()}}
    roots = {name: str(_recovery_directory(path, name)) for name, path in directories.items()}
    temporal_database = _temporal_file(database, database=True)
    locations = dict.fromkeys((database, Path(temporal_database["payload_path"])))
    sidecars = [str(location) + suffix for location in locations for suffix in ("-journal", "-wal", "-shm")]
    temporal = {"storage": "local-supervisor-sqlite", "database": temporal_database,
                "sidecars": [_temporal_file(Path(path)) for path in sidecars if os.path.lexists(path)]}

    repository = directories["repository"]
    git = GitMaterials(repository)
    if Path(os.fsdecode(git.read("rev-parse", "--show-toplevel", limit=4096).removesuffix(b"\n"))) != repository:
        raise ValueError("Original registered path is not the restored Git worktree")
    git_paths = {}
    for name, argument in (("directory", "--absolute-git-dir"), ("common_directory", "--git-common-dir")):
        value = git.read("rev-parse", "--path-format=absolute", argument, limit=4096).removesuffix(b"\n")
        git_paths[name] = str(_recovery_directory(Path(os.fsdecode(value)).resolve(), f"Git {name}"))
    git_paths["head"] = git.read("rev-parse", "--verify", "HEAD^{commit}", limit=128).decode("ascii").strip()

    submission = None
    if task_id is not None:
        original = native.task_submission(project, control_home, "status", {"task_id": task_id}, timeout=20)
        submission = {key: original[key] for key in ("task_id", "workflow_id", "run_id", "status",
                      "creation_sha256", "intent_sha256", "attempt_sha256", "result_sha256", "rejection_sha256")}
    inventory = {"schema_version": 1, "scope": "registered-project-local-recovery",
                 "project": {"id": project_id, "revision": project["revision"], **publication},
                 "roots": roots, "temporal": temporal, "git": git_paths, "submission": submission}
    if expected is None:
        return {"status": "observed", "inventory": inventory}
    with _recovery_file(expected) as stream:
        encoded = stream.read(65_537)
    if len(encoded) > 65_536:
        raise ValueError("Expected recovery scope exceeds 64 KiB")
    record = parse_json(encoded.decode("utf-8"), "expected recovery scope", finite=True, bounded=True)
    if (not isinstance(record, dict) or record.keys() != {"status", "inventory"}
            or record["status"] != "observed" or not isinstance(record["inventory"], dict)
            or record["inventory"].keys() != inventory.keys()):
        raise ValueError("Expected recovery scope must be the original discovery output")
    for section, actual in inventory.items():
        if json.dumps(record["inventory"][section], sort_keys=True) != json.dumps(actual, sort_keys=True):
            raise ValueError(f"Restored {section} differs from the recorded recovery scope")
    return {"status": "verified", "inventory": inventory}


def _check_assets(db: sqlite3.Connection, data: Path, original_home: Path) -> dict:
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    checked = {"skills": 0, "source_snapshots": 0, "agent_definitions": agent_definitions.verify_store(data),
               "workflow_definitions": workflow_definitions.verify_store(data)}
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
            actual, _ = skill_assets.digest_tree(data / _relative(relative))
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
    return {**checked, **issues.validate_storage(db), **issue_writebacks.validate_storage(db)}


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
