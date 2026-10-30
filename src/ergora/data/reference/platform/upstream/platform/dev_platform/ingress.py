"""Single-host issue ownership shared by trusted ingress adapters.

This is an ownership ledger, not an expiring lock. A caller may release a claim
only after its own durable state records confirmed cleanup or REVIEW_READY.
All coordinators must use the same private local database and OS identity.
Do not place SQLite on NFS or expose this module to untrusted agents.
"""
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time

from .contracts import canonical_sha


class OwnershipError(ValueError):
    """A conflicting or missing durable claim requires reconciliation."""


def _need(condition, message):
    if not condition:
        raise OwnershipError(message)


def _key(tracker):
    _need(type(tracker) is dict and set(tracker) == {"kind", "project", "issue_id"}, "Invalid tracker identity")
    _need(tracker["kind"] in ("local", "github", "gitlab"), "Unsupported tracker kind")
    _need(type(tracker["project"]) is str and len(tracker["project"]) <= 300 and
          re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+", tracker["project"]), "Invalid tracker project")
    _need(all(part not in (".", "..") for part in tracker["project"].split("/")), "Invalid tracker project component")
    _need(type(tracker["issue_id"]) is str and re.fullmatch(r"[1-9][0-9]{0,19}", tracker["issue_id"]), "Invalid issue ID")
    # Conservative case folding prevents alternate casing from bypassing a
    # GitHub claim. Separate hosts with identical project paths share a claim.
    return json.dumps({**tracker, "project": tracker["project"].casefold()}, sort_keys=True, separators=(",", ":"))


def _identity(tracker, owner, task_id, spec_sha256):
    resource = _key(tracker)
    _need(type(owner) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,199}", owner), "Invalid ingress owner")
    _need(type(task_id) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", task_id), "Invalid task ID")
    _need(type(spec_sha256) is str and re.fullmatch(r"[a-f0-9]{64}", spec_sha256), "Full canonical spec SHA256 required")
    claim_id = canonical_sha({"resource": resource, "owner": owner, "task_id": task_id})
    return resource, claim_id


class IngressLeases:
    def __init__(self, path):
        self.path = Path(path)
        _need(self.path.is_absolute() and ".." not in self.path.parts, "Shared ingress database must use an absolute canonical path")
        for item in (self.path, *self.path.parents):
            _need(not item.is_symlink(), "Shared ingress path cannot contain symlinks")
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        parent = self.path.parent.stat()
        _need(parent.st_uid == os.getuid() and not parent.st_mode & 0o022,
              "Shared ingress parent must be owned by the coordinator and not group/world writable")
        if self.path.exists():
            info = self.path.stat()
            _need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid()
                  and not info.st_mode & 0o077, "Shared ingress database must be a private regular file")
        else:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            os.close(fd)
        # The parent is a trusted private directory; agents cannot replace the
        # database, journal, or WAL between validation and SQLite's open.
        self.db = sqlite3.connect(self.path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY, resource TEXT NOT NULL, owner TEXT NOT NULL,
            task_id TEXT NOT NULL, spec_sha256 TEXT NOT NULL, acquired_at REAL NOT NULL,
            released_at REAL, evidence_digest TEXT)""")
        self.db.execute("CREATE TABLE IF NOT EXISTS active (resource TEXT PRIMARY KEY, claim_id TEXT UNIQUE NOT NULL)")
        self.db.commit()

    def close(self):
        self.db.close()

    def acquire(self, tracker, owner, task_id, spec_sha256):
        resource, claim_id = _identity(tracker, owner, task_id, spec_sha256)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            claim = self.db.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
            active = self.db.execute("SELECT claim_id FROM active WHERE resource=?", (resource,)).fetchone()
            if claim is not None:
                _need(claim["spec_sha256"] == spec_sha256, "Immutable ingress claim hash differs")
                _need(claim["released_at"] is None, "Released ingress claim cannot reopen; use a new task revision")
                _need(active is not None and active["claim_id"] == claim_id, "Ingress claim is missing from active ledger; reconcile")
            else:
                _need(active is None, "Another ingress task owns this issue; confirmed release is required")
                self.db.execute("INSERT INTO claims VALUES (?,?,?,?,?,?,NULL,NULL)",
                                (claim_id, resource, owner, task_id, spec_sha256, time.time()))
                self.db.execute("INSERT INTO active VALUES (?,?)", (resource, claim_id))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    def assert_held(self, tracker, owner, task_id, spec_sha256):
        resource, claim_id = _identity(tracker, owner, task_id, spec_sha256)
        row = self.db.execute("""SELECT c.* FROM active a JOIN claims c ON c.claim_id=a.claim_id
                               WHERE a.resource=?""", (resource,)).fetchone()
        _need(row is not None and row["claim_id"] == claim_id and row["spec_sha256"] == spec_sha256
              and row["released_at"] is None, "Exact ingress ownership is missing; reconcile before further runtime operations")

    def release(self, tracker, owner, task_id, spec_sha256, evidence_digest):
        resource, claim_id = _identity(tracker, owner, task_id, spec_sha256)
        _need(type(evidence_digest) is str and re.fullmatch(r"[a-f0-9]{64}", evidence_digest), "Release evidence digest required")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            claim = self.db.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
            _need(claim is not None and claim["spec_sha256"] == spec_sha256, "Release must match the original ingress claim")
            if claim["released_at"] is not None:
                _need(claim["evidence_digest"] == evidence_digest, "Immutable release evidence differs")
            else:
                self.assert_held(tracker, owner, task_id, spec_sha256)
                self.db.execute("UPDATE claims SET released_at=?,evidence_digest=? WHERE claim_id=?",
                                (time.time(), evidence_digest, claim_id))
                self.db.execute("DELETE FROM active WHERE resource=? AND claim_id=?", (resource, claim_id))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
