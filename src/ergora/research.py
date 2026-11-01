"""Bounded source observations. Web content is evidence, never executable instructions."""

from contextlib import nullcontext
import ctypes
import hashlib
from html.parser import HTMLParser
import ipaddress
import json
import multiprocessing
import os
from pathlib import Path
import re
import signal
import socket
import time
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid

from .state import State, file_lock, now


def _fetch_source(url, allow_private, max_bytes, filename, sender, deadline, controller_pid, gate=None):
    """A network-only child; the parent owns the wall deadline and persistent state."""
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    def expire(signum, frame):
        raise TimeoutError("Research time budget exhausted")

    try:
        if os.name == "nt":
            # Also bound the pre-assignment window if the parent exits before assigning us.
            if not gate.wait(max(.001, deadline - time.monotonic())):
                raise TimeoutError("Research time budget exhausted before job assignment")
        else:
            # Linux sends SIGKILL if the controller dies, including abrupt exits.
            if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL, 0, 0, 0):
                raise OSError(ctypes.get_errno(), "Cannot bind network child lifetime to controller")
            if os.getppid() != controller_pid:
                return
            signal.signal(signal.SIGALRM, expire)
            signal.setitimer(signal.ITIMER_REAL, max(.001, deadline - time.monotonic()))
        opener = build_opener(NoRedirect())
        target = url
        for _ in range(6):
            validate_url(target, allow_private)
            try:
                response = opener.open(Request(target, headers={"User-Agent": "Ergora/0.1 source-observer"}), timeout=15)
            except HTTPError as error:
                if error.code not in (301, 302, 303, 307, 308):
                    raise
                location = error.headers.get("Location")
                error.close()
                if not location:
                    raise ValueError("Redirect has no Location")
                target = urljoin(target, location)
                continue
            with response, Path(filename).open("wb") as output:
                content_type = response.headers.get_content_type()
                if content_type not in ("text/html", "text/plain", "text/markdown", "application/json", "application/xml", "text/xml", "application/rss+xml"):
                    raise ValueError(f"Unsupported source content type: {content_type}")
                size = 0
                while chunk := response.read1(min(65536, max_bytes - size + 1)):
                    output.write(chunk)
                    output.flush()
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError("Research byte budget exhausted")
                if response.length not in (None, 0):
                    raise ValueError("Incomplete source response body")
            sender.send({"status": "succeeded", "content_type": content_type, "final_url": response.url})
            return
        raise ValueError("Too many source redirects")
    except Exception as error:
        # Network/protocol failures cross this process boundary as explicit failed outcomes.
        sender.send({"status": "failed", "error": str(error), "error_type": type(error).__name__})
    finally:
        if os.name != "nt":
            signal.setitimer(signal.ITIMER_REAL, 0)
        sender.close()


def _download(url, allow_private, max_bytes, filename, check, progress, deadline):
    context = multiprocessing.get_context("spawn")
    gate = context.Event() if os.name == "nt" else None
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_fetch_source, args=(url, allow_private, max_bytes, str(filename), sender, deadline, os.getpid(), gate), daemon=True)
    if os.name == "nt":
        from .windows_job import Job
        lifetime = Job()
    else:
        lifetime = nullcontext()
    with lifetime as job:
        process.start()
        try:
            if job is not None:
                job.assign(process.pid)
                gate.set()
            while process.is_alive():
                progress()
                check()
                process.join(timeout=.05)
            progress()
            check()
            if not receiver.poll(.1):
                raise ValueError("Source fetch process ended without a result")
            try:
                result = receiver.recv()
            except EOFError as error:
                raise ValueError("Source fetch process ended without a result") from error
            if result["status"] != "succeeded":
                if result["error_type"] == "TimeoutError":
                    raise TimeoutError(result["error"])
                raise ValueError(result["error"])
            return result
        finally:
            sender.close()
            if process.is_alive():
                process.kill()
            process.join()
            progress()
            receiver.close()


def validate_url(url: str, allow_private: bool = False):
    parsed = urlsplit(url)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password
            or parsed.fragment or len(url) > 4096):
        raise ValueError("Source requires an HTTP(S) URL without credentials or fragment")
    if not allow_private:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
            raise ValueError("Private source addresses require explicit allow_private")


def validate_request(urls: list[str], max_bytes: int, timeout: int):
    if not 1 <= len(urls) <= 10 or len(set(urls)) != len(urls) or not 1 <= max_bytes <= 10_000_000 or not 1 <= timeout <= 300:
        raise ValueError("Require 1–10 unique URLs, 1–10000000 total bytes and 1–300 seconds")


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def text_content(raw: bytes, content_type: str) -> str:
    text = raw.decode("utf-8", errors="replace")
    if "html" in content_type:
        parser = _Text()
        parser.feed(text)
        text = "\n".join(parser.parts)
    return text


def get(state: State, project_id: str, run_id: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM research_runs WHERE project=? AND id=?", (project_id, run_id)).fetchone()
    if row is None:
        raise ValueError("Unknown research run in this project")
    return json.loads(row[0])


def listing(state: State, project_id: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        return {"runs": [json.loads(row[0]) for row in db.execute("SELECT document FROM research_runs WHERE project=? ORDER BY rowid DESC", (project_id,))],
                "proposals": [json.loads(row[0]) for row in db.execute("SELECT document FROM research_proposals WHERE project=? ORDER BY rowid DESC", (project_id,))]}


def cancel(state: State, project_id: str, run_id: str) -> dict:
    document = get(state, project_id, run_id)
    with state.connect() as db:
        db.execute("UPDATE research_runs SET cancel=1 WHERE project=? AND id=?", (project_id, run_id))
    return {"id": run_id, "cancel_requested": True, "status": document["status"]}


def proposal(state: State, project_id: str, proposal_id: str) -> dict:
    state.project(project_id)
    with state.connect() as db:
        row = db.execute("SELECT document FROM research_proposals WHERE project=? AND id=?", (project_id, proposal_id)).fetchone()
    if row is None:
        raise ValueError("Unknown research proposal in this project")
    document = json.loads(row[0])
    raw = (state.root / "sources" / project_id / f"{document['sha']}.raw").read_bytes()
    if hashlib.sha256(raw).hexdigest() != document["sha"]:
        raise ValueError("Source snapshot changed")
    return {**document, "text": text_content(raw, document["content_type"])}


def review(state: State, project_id: str, proposal_id: str, status: str, expected_revision: int, reason: str) -> dict:
    if status not in ("reviewed", "dismissed") or not reason.strip():
        raise ValueError("Choose reviewed/dismissed and provide a reason")
    with state.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT document FROM research_proposals WHERE project=? AND id=?", (project_id, proposal_id)).fetchone()
        if row is None:
            raise ValueError("Unknown research proposal in this project")
        document = json.loads(row[0])
        if document["revision"] != expected_revision:
            raise ValueError("Proposal revision changed; reload before saving")
        document.update(status=status, revision=expected_revision + 1, reason=reason, reviewed=now())
        db.execute("UPDATE research_proposals SET document=? WHERE id=?", (json.dumps(document), proposal_id))
    return document


def run(state: State, project_id: str, urls: list[str], max_bytes: int = 1_000_000,
        timeout: int = 30, allow_private: bool = False, run_id: str | None = None) -> dict:
    project = state.project(project_id)
    if project["bindings"].get("research", {"tool": "urls"})["tool"] != "urls":
        raise ValueError("Research binding does not support URL observations")
    validate_request(urls, max_bytes, timeout)
    request = {"urls": urls, "max_bytes": max_bytes, "timeout_seconds": timeout, "allow_private": allow_private}
    run_id = run_id or uuid.uuid4().hex
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", run_id):
        raise ValueError("Invalid research run ID")
    locks = state.root / "locks"
    locks.mkdir(exist_ok=True)
    with file_lock(locks / f"research-{run_id}.lock", blocking=False):
        with state.connect() as db:
            row = db.execute("SELECT project,document FROM research_runs WHERE id=?", (run_id,)).fetchone()
            if row:
                document = json.loads(row["document"])
                if row["project"] != project_id or document["request"] != request:
                    raise ValueError("Research ID already belongs to a different frozen request")
                if document["status"] != "running":
                    return document
            else:
                document = {"id": run_id, "project": project_id, "request": request, "started": now(),
                            "status": "running", "bytes": 0, "results": []}
                db.execute("INSERT INTO research_runs VALUES (?, ?, 0, ?)", (run_id, project_id, json.dumps(document)))
        session_started = time.monotonic()
        elapsed_before = document.get("elapsed_seconds", 0.0)
        if document.get("inflight") and document.get("checkpoint_epoch"):
            # An interrupted controller cannot prove when its network child stopped.
            # Charge that uncertain interval conservatively, up to the total budget.
            elapsed_before += min(max(0, time.time() - document["checkpoint_epoch"]), max(0, timeout - elapsed_before))
        deadline = session_started + timeout - elapsed_before

        def checkpoint():
            document["elapsed_seconds"] = elapsed_before + time.monotonic() - session_started
            document["checkpoint_epoch"] = time.time()
            with state.connect() as db:
                db.execute("UPDATE research_runs SET document=? WHERE id=?", (json.dumps(document), run_id))

        def check():
            with state.connect() as db:
                cancelled = db.execute("SELECT cancel FROM research_runs WHERE id=?", (run_id,)).fetchone()[0]
            if cancelled:
                raise InterruptedError("Research cancellation acknowledged")
            if time.monotonic() >= deadline:
                raise TimeoutError("Research time budget exhausted")

        download_dir = state.root / "research-downloads" / run_id
        download_dir.mkdir(parents=True, exist_ok=True)
        if document.get("inflight"):
            partial = download_dir / document["inflight"]["filename"]
            size = partial.stat().st_size if partial.exists() else 0
            document["bytes"] += max(0, size - document["inflight"]["counted"])
            if not document["inflight"].get("finished"):
                # A file stat cannot establish how many bytes an interrupted
                # child consumed. Do not spend the same transfer allowance twice.
                document["reserved_bytes"] = max(0, max_bytes - document["bytes"])
            document.pop("inflight")
            checkpoint()
        completed = {result["url"] for result in document["results"]}
        try:
            for url in urls:
                if url in completed:
                    continue
                check()
                document["active_url"] = url
                remaining = max_bytes - document["bytes"] - document.get("reserved_bytes", 0)
                if remaining <= 0:
                    raise ValueError("Research byte budget exhausted (unconfirmed interrupted transfers reserve their remaining allowance)")
                partial = download_dir / (uuid.uuid4().hex + ".part")
                document["inflight"] = {"filename": partial.name, "counted": 0}
                checkpoint()
                last_checkpoint = time.monotonic()

                def progress():
                    nonlocal last_checkpoint
                    size = partial.stat().st_size if partial.exists() else 0
                    delta = max(0, size - document["inflight"]["counted"])
                    document["bytes"] += delta
                    document["inflight"]["counted"] = size
                    if delta or time.monotonic() - last_checkpoint >= 1:
                        checkpoint()
                        last_checkpoint = time.monotonic()

                fetched = _download(url, allow_private, remaining, partial, check, progress, deadline)
                document["inflight"]["finished"] = True
                checkpoint()
                content_type, final_url = fetched["content_type"], fetched["final_url"]
                check()
                sha = hashlib.sha256(partial.read_bytes()).hexdigest()
                destination = state.root / "sources" / project_id / f"{sha}.raw"
                destination.parent.mkdir(parents=True, exist_ok=True)
                partial.replace(destination)
                document.pop("inflight")
                observation = {"url": url, "final_url": final_url, "sha": sha, "content_type": content_type, "observed": now()}
                proposal_id = uuid.uuid5(uuid.NAMESPACE_URL, f"{project_id}/{run_id}/{url}/{sha}").hex
                with state.connect() as db:
                    db.execute("BEGIN IMMEDIATE")
                    previous = db.execute("SELECT sha FROM source_heads WHERE project=? AND url=?", (project_id, url)).fetchone()
                    previous_sha = previous[0] if previous else None
                    existing = db.execute("SELECT document FROM research_proposals WHERE id=?", (proposal_id,)).fetchone()
                    changed = previous_sha != sha or existing is not None
                    db.execute("INSERT OR IGNORE INTO source_snapshots VALUES (?, ?, ?, ?)", (project_id, url, sha, json.dumps(observation)))
                    db.execute("INSERT OR REPLACE INTO source_heads VALUES (?, ?, ?)", (project_id, url, sha))
                    if changed:
                        proposal_doc = {**observation, "id": proposal_id, "project": project_id, "run": run_id,
                                        "previous_sha": previous_sha, "status": "pending", "revision": 1}
                        db.execute("INSERT OR IGNORE INTO research_proposals VALUES (?, ?, ?)", (proposal_id, project_id, json.dumps(proposal_doc)))
                document["results"].append({**observation, "changed": changed, "proposal": proposal_id if changed else None})
                checkpoint()
            check()
            document["status"] = "succeeded"
            document.pop("active_url", None)
        except (KeyboardInterrupt, InterruptedError):
            document["status"] = "cancelled"
        except TimeoutError as error:
            document.update(status="timed_out", error=str(error))
        except (ValueError, OSError) as error:
            document.update(status="failed", error=str(error))
        document["finished"] = now()
        checkpoint()
    return document
