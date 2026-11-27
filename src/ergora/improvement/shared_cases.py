"""Explicit local case lookup and append-only Markdown publication."""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import heapq
import os
from pathlib import Path
import re
import stat
import tempfile
import unicodedata

from ergora.improvement.case_markdown import CASE_ID, MAX_MARKDOWN_BYTES, MAX_REVISION, decode_markdown, validate_id
from ergora.improvement.memory import parse_expiry, validate_source
from ergora.storage.assets import is_link, publish_directory
from ergora.storage.state import file_lock, now


DEFAULT_LIMIT = 5
MAX_RESULTS = 20
MAX_EXCERPT_BYTES = 512
_REVISION = re.compile(r"[1-9][0-9]{0,8}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_WORDS = re.compile(r"[^\W_]+")
_FACTS = ("project", "technology", "environment", "version")
_APPLICABILITY_ORDER = {"matched": 0, "unknown": 1, "incompatible": 2}


@dataclass(frozen=True)
class _Case:
    metadata: dict
    markdown: str
    body: str
    sha256: str
    expiry: datetime | None

    def record(self, observed: datetime) -> dict:
        validity = "valid"
        if self.metadata["status"] == "withdrawn":
            validity = "withdrawn"
        elif self.expiry is not None and observed >= self.expiry:
            validity = "expired"
        return {**self.metadata, "sha256": self.sha256, "validity": validity}


def _text(value, label: str, limit: int) -> None:
    if (not isinstance(value, str) or not value.strip() or value.strip() != value
            or len(value.encode("utf-8")) > limit or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError(f"Shared case {label} requires a nonempty single line of at most {limit} UTF-8 bytes")


def _strings(items, label: str) -> None:
    if not isinstance(items, list) or len(items) > 16:
        raise ValueError(f"Shared case {label} requires an array of up to 16 strings")
    for item in items:
        _text(item, label, MAX_EXCERPT_BYTES)
    if len(set(items)) != len(items):
        raise ValueError(f"Shared case {label} requires unique entries")


def _require_regular(path: Path) -> os.stat_result:
    details = path.lstat()
    if not stat.S_ISREG(details.st_mode) or is_link(path) or details.st_nlink != 1:
        raise ValueError(f"Shared case library requires ordinary files without links: {path.name}")
    return details


def _read_markdown(path: Path) -> bytes:
    original = _require_regular(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        current = os.fstat(stream.fileno())
        if (not stat.S_ISREG(current.st_mode) or current.st_nlink != 1
                or (original.st_dev, original.st_ino) != (current.st_dev, current.st_ino)):
            raise ValueError("Shared case Markdown changed while opening")
        raw = stream.read(MAX_MARKDOWN_BYTES + 1)
    if len(raw) > MAX_MARKDOWN_BYTES:
        raise ValueError(f"Shared case Markdown exceeds {MAX_MARKDOWN_BYTES} UTF-8 bytes")
    return raw


def _validate_applicability(value) -> None:
    if (not isinstance(value, dict) or set(value) - {"project", "technology", "environment", "versions"}
            or not {"environment", "versions"} <= value.keys()
            or not {"project", "technology"} & value.keys()):
        raise ValueError("Shared case applicability requires project or technology, environment and versions")
    for field in ("project", "technology", "environment"):
        if field in value:
            _text(value[field], field, 128)
    _strings(value["versions"], "versions")
    if not value["versions"]:
        raise ValueError("Shared case applicability requires at least one exact version")


def _validate_sources(value) -> None:
    if not isinstance(value, list) or not 1 <= len(value) <= 8:
        raise ValueError("Shared case requires one to eight shareable source references")
    for source in value:
        validate_source(source)
        _text(source["uri"], "source URI", 2_048)
        _text(source["revision"], "source revision", 256)


def _parse(raw: bytes, sha256: str) -> _Case:
    record, markdown, body = decode_markdown(raw)
    if set(record) != {
        "id", "revision", "title", "aliases", "error_signatures", "applicability", "status", "sources", "expires_at",
    }:
        raise ValueError("Shared case front matter requires id, revision, title, aliases, error_signatures, "
                         "applicability, status, sources and expires_at")
    _text(record["title"], "title", 256)
    _strings(record["aliases"], "aliases")
    _strings(record["error_signatures"], "error signatures")
    if not (record["aliases"] or record["error_signatures"]):
        raise ValueError("Shared case requires an alias or error signature")
    _validate_applicability(record["applicability"])
    _validate_sources(record["sources"])
    if record["status"] not in ("verified", "unresolved", "withdrawn"):
        raise ValueError("Shared case status requires verified, unresolved or withdrawn")
    return _Case(record, markdown, body, sha256, parse_expiry(record["expires_at"]))


def _directory(path: Path) -> bool:
    try:
        if is_link(path) or not path.is_dir():
            raise ValueError(f"Shared case library requires a real directory: {path.name}")
    except FileNotFoundError:
        return False
    return True


def _case_root(library: Path) -> Path:
    if library is None:
        raise ValueError("Select an existing local shared case directory with --library")
    root = Path(library).expanduser().absolute()
    if not _directory(root):
        raise ValueError("Select an existing local shared case directory with --library")
    return root / "cases"


def _current(directory: Path) -> _Case | None:
    if not _directory(directory):
        return None
    revision = max((int(path.name) for path in directory.iterdir() if _REVISION.fullmatch(path.name)), default=0)
    if revision == 0:
        return None
    selected = directory / str(revision)
    if not _directory(selected):
        raise ValueError("Shared case revision directory disappeared")
    raw = _read_markdown(selected / "case.md")
    case = _parse(raw, hashlib.sha256(raw).hexdigest())
    if (case.metadata["id"], case.metadata["revision"]) != (directory.name, revision):
        raise ValueError("Shared case Markdown ID or revision differs from its published directory")
    return case


def _normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _matching_facts(applicability: dict, facts: dict) -> dict:
    missing, mismatched = [], []
    for field in _FACTS:
        stored_key = "versions" if field == "version" else field
        if stored_key not in applicability:
            continue
        actual = facts.get(field)
        expected = applicability[stored_key]
        if actual is None:
            missing.append(field)
        elif (actual not in expected if field == "version" else _normalize(actual) != _normalize(expected)):
            mismatched.append(field)
    status = "incompatible" if mismatched else "unknown" if missing else "matched"
    return {"status": status, "missing": missing, "mismatched": mismatched}


def _rank(case: _Case, query: str, words: set[str]) -> tuple[int, str, str] | None:
    data = case.metadata
    if signature := next((value for value in data["error_signatures"] if _normalize(value) in query), None):
        return 0, "error_signature", signature
    lexical = None
    for field, values in (("title", (data["title"],)), ("alias", data["aliases"]),
                          ("error_signature", data["error_signatures"])):
        for value in values:
            normalized = _normalize(value)
            if query in normalized or normalized in query:
                return 1, field, value
            if lexical is None and words and words.issubset(_WORDS.findall(normalized)):
                lexical = 2, field, value
    if lexical is not None:
        return lexical
    for line in case.body.splitlines():
        normalized = _normalize(line)
        if query in normalized or (words and words.issubset(_WORDS.findall(normalized))):
            return 2, "body", line.strip()
    return None


def _excerpt(text: str, query: str, words: set[str]) -> tuple[str, bool]:
    if len(text.encode("utf-8")) <= MAX_EXCERPT_BYTES:
        return text, False
    # Search excerpts may normalize long lines. The exact reader returns the original bytes.
    normalized = _normalize(text)
    start = normalized.find(query)
    if start < 0:
        start = next((word.start() for word in _WORDS.finditer(normalized) if word.group() in words), 0)
    raw = normalized[max(0, start - 64):].encode("utf-8")
    return raw[:MAX_EXCERPT_BYTES].decode("utf-8", errors="ignore"), True


def _candidates(cases: Path, query: str, observed: datetime, facts: dict):
    words = set(_WORDS.findall(query))
    if not _directory(cases):
        return
    for path in cases.iterdir():
        if len(path.name) > 64 or CASE_ID.fullmatch(path.name) is None:
            continue
        validate_id(path.name)
        case = _current(path)
        if case is None:
            continue
        record = case.record(observed)
        if record["validity"] != "valid":
            continue
        rank = _rank(case, query, words)
        if rank is None:
            continue
        priority, field, text = rank
        applicability = _matching_facts(record["applicability"], facts)
        excerpt, truncated = _excerpt(text, query, words)
        result = {**record, "applicability_match": applicability, "match": {
            "field": field, "excerpt": excerpt, "truncated": truncated}}
        yield (priority, _APPLICABILITY_ORDER[applicability["status"]], record["id"]), result


def _provided_facts(facts: dict | None) -> dict:
    if facts is None:
        return {}
    if not isinstance(facts, dict) or facts.keys() - set(_FACTS):
        raise ValueError("Shared case lookup supports project, technology, environment and version facts")
    for name, value in facts.items():
        _text(value, name, MAX_EXCERPT_BYTES if name == "version" else 128)
    return facts


def search(library: Path, query: str, *, limit: int = DEFAULT_LIMIT, facts: dict | None = None) -> dict:
    if not isinstance(query, str) or not query.strip() or len(query.encode("utf-8")) > 1_024:
        raise ValueError("Shared case query requires 1 to 1024 UTF-8 bytes of text")
    if type(limit) is not int or not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"Shared case limit requires an integer from 1 to {MAX_RESULTS}")
    observed_at = now()
    matches = _candidates(_case_root(library), _normalize(query), datetime.fromisoformat(observed_at),
                          _provided_facts(facts))
    results = [result for _, result in heapq.nsmallest(limit, matches, key=lambda item: item[0])]
    return {"scope": "shared", "observed_at": observed_at, "results": results}


def show(library: Path, case_id: str, *, revision: int | None = None, sha256: str | None = None,
         facts: dict | None = None) -> dict:
    if (revision is not None or sha256 is not None) and (
            type(revision) is not int or not 1 <= revision <= MAX_REVISION
            or not isinstance(sha256, str) or _SHA256.fullmatch(sha256) is None):
        raise ValueError("Exact shared case read requires both a positive --revision and a lowercase --sha256 digest")
    case_id = validate_id(case_id)
    cases = _case_root(library)
    case = _current(cases / case_id) if _directory(cases) else None
    if case is None:
        raise ValueError(f"Unknown shared case: {case_id}")
    observed_at = now()
    record = case.record(datetime.fromisoformat(observed_at))
    validity = record["validity"]
    if revision is not None:
        if validity != "valid":
            raise ValueError(f"Shared case {case_id} is {validity}; search again")
        if (record["revision"], record["sha256"]) != (revision, sha256):
            raise ValueError(f"Shared case {case_id} revision or digest changed; search again")
    record["applicability_match"] = _matching_facts(record["applicability"], _provided_facts(facts))
    return {"scope": "shared", "observed_at": observed_at, "record": record,
            "markdown": case.markdown if validity == "valid" else None}


def _sync_directory(directory: Path) -> None:
    if os.name != "nt":
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def publication_lock(library: Path):
    """Keep a publisher from changing a current selection through first admission."""
    cases = _case_root(library)
    if not _directory(cases):
        raise ValueError("Shared case library has no published revisions")
    lock = cases / ".publish.lock"
    _require_regular(lock)
    return file_lock(lock)


def publish(library: Path, draft: Path, expected_revision: int, *, sha256: str) -> dict:
    if type(expected_revision) is not int or not 0 <= expected_revision < MAX_REVISION:
        raise ValueError("Shared case expected revision must be zero for creation or the current revision")
    if not isinstance(sha256, str) or _SHA256.fullmatch(sha256) is None:
        raise ValueError("Shared case publication requires the reviewed Markdown SHA-256")
    cases = _case_root(library)
    raw = _read_markdown(draft)
    if hashlib.sha256(raw).hexdigest() != sha256:
        raise ValueError("Reviewed shared case Markdown digest changed. Review the complete draft again.")
    case = _parse(raw, sha256)
    revision = case.metadata["revision"]
    if revision != expected_revision + 1:
        raise ValueError("Shared case draft revision must be one greater than --expected-revision")
    if not _directory(cases):
        cases.mkdir(mode=0o700, exist_ok=True)
        _directory(cases)
    directory = cases / case.metadata["id"]
    lock = cases / ".publish.lock"
    try:
        _require_regular(lock)
    except FileNotFoundError:
        pass
    with file_lock(lock):
        current = _current(directory)
        current_revision = current.metadata["revision"] if current else 0
        if current_revision != expected_revision:
            raise ValueError(f"Shared case revision changed; expected {expected_revision}, current {current_revision}")
        if current_revision == 0 and case.metadata["status"] == "withdrawn":
            raise ValueError("Shared case withdrawal requires a previously published revision")
        directory.mkdir(mode=0o700, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".pending-", dir=directory) as temporary:
            staged = Path(temporary)
            with (staged / "case.md").open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            _sync_directory(staged)
            publish_directory(staged, directory / str(revision))
        for parent in (directory, cases, cases.parent):
            _sync_directory(parent)
    observed_at = now()
    return {"scope": "shared", "observed_at": observed_at, "record": case.record(datetime.fromisoformat(observed_at))}
