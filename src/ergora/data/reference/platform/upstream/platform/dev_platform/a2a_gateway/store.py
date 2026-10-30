"""Private, durable admission and ownership ledger, for one gateway process.

Only the trusted operator writes admissions. A task may never replace its frozen
input or owner. The SQLite directory must be on local durable storage, outside
agent workspaces; OS permissions, not hashes, establish this trust boundary.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import stat
import time
import uuid

from ..contracts import canonical_sha, need, SLUG, SHA256

MAX_COMPILED_BYTES = 1024 * 1024


def utc_text(seconds=None):
    return datetime.fromtimestamp(time.time() if seconds is None else seconds, timezone.utc).isoformat().replace('+00:00', 'Z')


def strict_loads(text):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('Duplicate JSON key: ' + key)
            out[key] = value
        return out
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))


def validate_envelope(value):
    from ..portable import validate_compiled
    validate_compiled(value)
    need(len(json.dumps(value, ensure_ascii=False).encode()) <= MAX_COMPILED_BYTES, 'Compiled task exceeds 1 MiB')
    return value


class Store:
    def __init__(self, path):
        self.path = Path(path).absolute()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        for node in [self.path, *self.path.parents]:
            need(not node.is_symlink(), 'Ledger path cannot contain symlinks')
        need(self.path.parent.stat().st_uid == os.getuid() and self.path.parent.stat().st_mode & 0o077 == 0, 'Ledger parent must be private (0700) and owned by the coordinator')
        if self.path.exists():
            need(self.path.is_file() and self.path.stat().st_uid == os.getuid() and self.path.stat().st_nlink == 1 and self.path.stat().st_mode & 0o077 == 0, 'Ledger must be a private regular file owned by the coordinator')
        self.db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        os.chmod(self.path, 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS admissions (
              domain_id TEXT PRIMARY KEY, principal TEXT NOT NULL, digest TEXT NOT NULL,
              compiled TEXT NOT NULL, expires REAL NOT NULL, admitted_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks (
              id TEXT PRIMARY KEY, context_id TEXT NOT NULL, domain_id TEXT NOT NULL UNIQUE,
              principal TEXT NOT NULL, digest TEXT NOT NULL, issue_key TEXT NOT NULL,
              phase TEXT NOT NULL, run_id TEXT, snapshot TEXT, cancel_requested INTEGER NOT NULL DEFAULT 0,
              safe_terminal INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL, updated REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS messages (
              principal TEXT NOT NULL, message_id TEXT NOT NULL, digest TEXT NOT NULL, task_id TEXT NOT NULL,
              PRIMARY KEY(principal,message_id));
        ''')
        self.db.execute("INSERT OR IGNORE INTO metadata VALUES('ledger_uuid',?)", (str(uuid.uuid4()),))
        identity = self.db.execute("SELECT value FROM metadata WHERE key='ledger_uuid'").fetchone()['value']
        need(str(uuid.UUID(identity)) == identity, 'Invalid ledger identity')
        self.ledger_identity = canonical_sha({'uuid': identity, 'path': str(self.path)})[:32]
        self._lock_fd = None

    def lease_owner(self, principal):
        return 'a2a:' + self.ledger_identity + ':' + principal

    def close(self):
        self.db.close()
        if self._lock_fd is not None:
            os.close(self._lock_fd)
            self._lock_fd = None

    def acquire_server_lock(self):
        path = self.path.with_suffix(self.path.suffix + '.server.lock')
        self._lock_fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self._lock_fd); self._lock_fd = None
            raise ValueError('Only one gateway server process may own this ledger') from None

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def admit(self, compiled, principal, expires_at):
        validate_envelope(compiled)
        need(type(principal) is str and SLUG.fullmatch(principal), 'Invalid principal')
        if isinstance(expires_at, str):
            expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            need(expiry.tzinfo is not None, 'Expiry must include a timezone')
            expires_at = expiry.timestamp()
        need(type(expires_at) in (int, float) and time.time() < expires_at <= time.time() + 7 * 86400,
             'Admission expiry must be within the next seven days')
        domain_id = compiled['spec']['request']['task_id']; digest = canonical_sha(compiled)
        encoded = json.dumps(compiled, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
        with self.transaction():
            old = self.db.execute('SELECT * FROM admissions WHERE domain_id=?', (domain_id,)).fetchone()
            if old:
                need(old['principal'] == principal and old['digest'] == digest and old['compiled'] == encoded,
                     'Task ID already admitted with different content or owner')
                need(old['expires'] == expires_at, 'Admission is immutable; create a new task revision to change expiry')
            else:
                from ..portable import compile_task
                current = compile_task(compiled['task'], compiled['package'], compiled['policy'], compiled['binding'])
                need(current == compiled, 'Admission differs from the currently installed trusted registry')
                self.db.execute('INSERT INTO admissions VALUES(?,?,?,?,?,?)',
                                (domain_id, principal, digest, encoded, expires_at, utc_text()))
        return {'task_id': domain_id, 'compiled_sha256': digest}

    def compiled(self, row):
        admission = self.db.execute('SELECT * FROM admissions WHERE domain_id=?', (row['domain_id'],)).fetchone()
        need(admission is not None and admission['digest'] == row['digest'] and admission['principal'] == row['principal'],
             'Ledger admission binding mismatch')
        compiled = strict_loads(admission['compiled'])
        validate_envelope(compiled)
        need(canonical_sha(compiled) == row['digest'], 'Frozen input digest mismatch')
        return compiled

    def owned(self, task_id, principal):
        row = self.db.execute('SELECT * FROM tasks WHERE id=? AND principal=?', (task_id, principal)).fetchone()
        return dict(row) if row else None

    def claim(self, ref, principal, message_id, context_id='', a2a_task_id=''):
        need(type(ref) is dict and set(ref) == {'task_id', 'compiled_sha256'}, 'Expected exact admitted task reference')
        need(type(ref['task_id']) is str and SLUG.fullmatch(ref['task_id']), 'Invalid domain task ID')
        need(type(ref['compiled_sha256']) is str and SHA256.fullmatch(ref['compiled_sha256']), 'Invalid compiled digest')
        need(type(message_id) is str and 0 < len(message_id) <= 200, 'Message ID required (at most 200 characters)')
        request_digest = canonical_sha({'ref': ref, 'context_id': context_id, 'a2a_task_id': a2a_task_id})
        with self.transaction():
            admission = self.db.execute('SELECT * FROM admissions WHERE domain_id=? AND principal=?', (ref['task_id'], principal)).fetchone()
            need(admission is not None and admission['digest'] == ref['compiled_sha256'], 'Task is not admitted for this principal and digest')
            old_message = self.db.execute('SELECT * FROM messages WHERE principal=? AND message_id=?', (principal, message_id)).fetchone()
            if old_message:
                need(old_message['digest'] == request_digest, 'Message ID reused with different input')
                return self.owned(old_message['task_id'], principal), False
            old_task = self.db.execute('SELECT * FROM tasks WHERE domain_id=?', (ref['task_id'],)).fetchone()
            if old_task:
                need(old_task['principal'] == principal and old_task['digest'] == ref['compiled_sha256'], 'Task ownership/content conflict')
                need(not context_id or context_id == old_task['context_id'], 'Context ID differs from admitted task')
                need(not a2a_task_id or a2a_task_id == old_task['id'], 'A2A task ID differs from admitted task')
                row = dict(old_task); created = False
            else:
                need(admission['expires'] > time.time(), 'Admission expired before submission')
                need(not context_id and not a2a_task_id, 'New tasks require server-assigned task/context IDs')
                compiled = strict_loads(admission['compiled']); validate_envelope(compiled)
                need(canonical_sha(compiled) == admission['digest'], 'Frozen input digest mismatch')
                tracker = compiled['spec']['request']['tracker']
                issue_key = canonical_sha(tracker)
                busy = self.db.execute('SELECT id FROM tasks WHERE issue_key=? AND safe_terminal=0', (issue_key,)).fetchone()
                need(busy is None, 'Another task still owns this issue; reconcile or complete it first')
                now = time.time(); tid = str(uuid.uuid4()); cid = str(uuid.uuid4())
                self.db.execute('INSERT INTO tasks(id,context_id,domain_id,principal,digest,issue_key,phase,created,updated) VALUES(?,?,?,?,?,?,?,?,?)',
                                (tid, cid, ref['task_id'], principal, ref['compiled_sha256'], issue_key, 'NEW', now, now))
                row = self.owned(tid, principal); created = True
            self.db.execute('INSERT INTO messages VALUES(?,?,?,?)', (principal, message_id, request_digest, row['id']))
            return row, created

    def update(self, task_id, **values):
        need(set(values) <= {'phase', 'run_id', 'snapshot', 'cancel_requested', 'safe_terminal'}, 'Invalid mutable task fields')
        if 'snapshot' in values:
            values['snapshot'] = json.dumps(values['snapshot'], sort_keys=True, separators=(',', ':'), allow_nan=False)
        values['updated'] = time.time()
        keys = list(values)
        self.db.execute('UPDATE tasks SET ' + ','.join(k + '=?' for k in keys) + ' WHERE id=?', [values[k] for k in keys] + [task_id])

    def owned_rows(self, principal):
        return [dict(row) for row in self.db.execute('SELECT * FROM tasks WHERE principal=? ORDER BY created DESC,id DESC', (principal,))]

    def active_rows(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM tasks WHERE safe_terminal=0 OR phase='TERMINAL' ORDER BY created")]

    def admission_expired(self, row):
        grant = self.db.execute('SELECT expires FROM admissions WHERE domain_id=?', (row['domain_id'],)).fetchone()
        return grant is None or grant['expires'] <= time.time()
