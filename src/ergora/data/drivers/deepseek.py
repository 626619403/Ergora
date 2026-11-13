"""Runs in the optional pinned SDK environment; no Ergora imports or scheduler."""

from contextlib import ExitStack, contextmanager, nullcontext, redirect_stdout
import codecs
from dataclasses import asdict
from importlib.metadata import version
import hashlib
from itertools import islice
import json
import os
from pathlib import Path
import stat
import sys
import uuid


CALL_METADATA_LIMITS = {"request.json": 8_000_000, "native-patch.yml": 65_536,
    "native-prompt.txt": 2_000_000, "schema.json": 65_536, "native-identity.json": 16_384,
    "native-call-contract.json": 65_536}
MAX_CONTINUATION_HISTORY = 64 * 1024 * 1024


@contextmanager
def call_directory(path: Path):
    """Keep a saved call's complete directory chain open and unchanged."""
    with ExitStack() as stack:
        opened = []
        parent = None
        for name in (path.anchor, *path.parts[1:]):
            descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            stack.callback(os.close, descriptor)
            opened.append((parent, name, descriptor))
            parent = descriptor
        yield parent
        for parent, name, descriptor in opened:
            current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            original = os.fstat(descriptor)
            if (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino):
                raise ValueError("Saved call directory moved while reading")


def call_files(protocol: Path, limits: dict[str, int]) -> dict[str, bytes]:
    """Read only known call metadata, with bounded IO and no followed links."""
    result = {}
    def stamp(value):
        return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns
    with call_directory(protocol) as directory:
        for name, maximum in limits.items():
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(descriptor, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    raise ValueError("Saved call metadata requires ordinary files without hard links")
                raw = stream.read(maximum + 1)
                current = os.stat(name, dir_fd=directory, follow_symlinks=False)
                if len(raw) > maximum or stamp(before) != stamp(os.fstat(stream.fileno())) or stamp(before) != stamp(current):
                    raise ValueError("Saved call metadata changed or exceeds its byte limit")
                result[name] = raw
    return result


@contextmanager
def native_directories(protocol: Path, cwd: Path, *, expected: dict | None = None):
    """Pin both native directories for the entire observation or SDK operation."""
    with ExitStack() as stack:
        identities = {}
        for name, path in (("cwd", cwd), ("home", protocol / "native-home")):
            descriptor = stack.enter_context(call_directory(path))
            details = os.fstat(descriptor)
            identities[name + "_identity"] = [details.st_dev, details.st_ino]
        if expected is not None and any(expected.get(key) != value for key, value in identities.items()):
            raise ValueError("Native home or cwd differs from its frozen directory")
        yield identities


def native_history_page(protocol: Path, *, cwd: Path, offset: int,
                        limit: int, revision: str | None) -> dict:
    if sys.platform != "linux":
        return {"available": False, "reason": "Native archive reads currently require Linux/WSL2"}
    with ExitStack() as stack:
        directories, files, layouts = [], [], []

        def stamp(value):
            return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns

        def directory(parent, name):
            descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            stack.callback(os.close, descriptor)
            directories.append((parent, name, descriptor))
            return descriptor

        def ordinary(parent, name):
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            stream = stack.enter_context(os.fdopen(descriptor, "rb"))
            details = os.fstat(descriptor)
            if not stat.S_ISREG(details.st_mode):
                raise ValueError("Native archives require ordinary files")
            files.append((parent, name, stream, details))
            return stream

        def listing(descriptor, maximum):
            with os.scandir(descriptor) as entries:
                names = [entry.name for entry in islice(entries, maximum)]
            layouts.append((descriptor, maximum, set(names)))
            return names

        try:
            protocol_fd = stack.enter_context(call_directory(protocol))
            native = directory(protocol_fd, "native-home")
        except FileNotFoundError:
            return {"available": False, "reason": "No native archive was saved for this call"}
        identity_file = ordinary(protocol_fd, "native-identity.json")
        raw_identity = identity_file.read(16_385)
        if len(raw_identity) > 16_384:
            raise ValueError("Native archive identity exceeds 16 KiB")
        identity = json.loads(raw_identity)
        if (not isinstance(identity, dict) or identity.get("home") != str(protocol / "native-home") or
                identity.get("profile") != "sdk-minimal"):
            raise ValueError("Native archive home/profile differs from the saved call")
        sessions = directory(native, "sessions")
        projects = listing(sessions, 2)
        if len(projects) != 1:
            raise ValueError("Native archive requires one original session namespace")
        namespace = directory(sessions, projects[0])
        names = listing(namespace, 2)
        if names != [identity.get("session_id")]:
            raise ValueError("Native archive session differs from the saved call")
        session = directory(namespace, names[0])
        names = set(listing(session, 3))
        if "session.v4.jsonl" not in names or names - {"session.lock", "session.v4.jsonl"}:
            raise ValueError("Only the original uncompressed v4 session archive is supported")
        stream = ordinary(session, "session.v4.jsonl")
        line = stream.readline(16_385)
        if len(line) > 16_384 or not line.endswith(b"\n"):
            raise ValueError("Native archive header is missing or exceeds 16 KiB")
        header = json.loads(line)
        if (not isinstance(header, dict) or type(header.get("version")) is not int or header["version"] != 4 or
                header.get("id") != identity["session_id"] or header.get("cwd") != str(cwd)):
            raise ValueError("Native archive header differs from the saved session/cwd")
        details = files[-1][3]
        source = f"native-home/sessions/{projects[0]}/{identity['session_id']}/session.v4.jsonl"
        observed = hashlib.sha256(json.dumps({"run": protocol.name, "source": source, "session": identity["session_id"],
            "identity": hashlib.sha256(raw_identity).hexdigest(), "stat": stamp(details)}, sort_keys=True).encode()).hexdigest()
        if revision is not None and revision != observed:
            raise ValueError("Native archive changed; restart at offset 0 without the old revision")
        if offset > details.st_size:
            raise ValueError("Native archive offset exceeds the observed file")
        stream.seek(offset)
        raw = stream.read(min(limit, details.st_size - offset))
        decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
        text = decoder.decode(raw, final=offset + len(raw) == details.st_size)
        count = len(raw) - len(decoder.getstate()[0])
        for parent, name, descriptor in directories:
            current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            opened = os.fstat(descriptor)
            if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
                raise ValueError("Native archive directory moved while reading")
        for parent, name, opened, before in files:
            if stamp(os.fstat(opened.fileno())) != stamp(before) or stamp(os.stat(name, dir_fd=parent, follow_symlinks=False)) != stamp(before):
                raise ValueError("Native archive changed while reading")
        for descriptor, maximum, before in layouts:
            with os.scandir(descriptor) as entries:
                current = {entry.name for entry in islice(entries, maximum)}
            if current != before:
                raise ValueError("Native archive directory changed while reading")
        return {"available": True, "kind": "native-jsonl-archive", "session_id": identity["session_id"],
            "source": source,
            "revision": observed, "revision_basis": "local file observation; not a full content SHA",
            "writer_state": "unconfirmed", "size_bytes": details.st_size, "offset": offset,
            "bytes_read": count, "next_offset": offset + count if offset + count < details.st_size else None,
            "encoding": "utf-8", "content": text,
            "complete": offset == 0 and count == details.st_size}


def installed_versions():
    versions = {name: version(name) for name in ("deepseek-harness-sdk", "deepseek-harness-runtime-bin")}
    if any(value != "0.2.2rc2" for value in versions.values()):
        raise ValueError("This adapter requires deepseek-harness-sdk/runtime-bin==0.2.2rc2")
    return versions


def _json_file(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _history(protocol, cwd):
    chunks = []
    offset, revision, first = 0, None, None
    while True:
        page = native_history_page(protocol, cwd=cwd, offset=offset, limit=65_536, revision=revision)
        if not page["available"] or page["size_bytes"] > MAX_CONTINUATION_HISTORY:
            raise ValueError("Continuation requires an available native archive of at most 64 MiB")
        first = first or page
        chunks.append(page["content"].encode("utf-8"))
        if page["next_offset"] is None:
            break
        revision, offset = page["revision"], page["next_offset"]
    raw = b"".join(chunks)
    if not raw.endswith(b"\n"):
        raise ValueError("Continuation history has an incomplete tail")
    lines = raw.splitlines()
    if any(len(line) > 8_000_000 for line in lines):
        raise ValueError("Continuation history exceeds the 8 MB event limit")
    header, *events = (json.loads(line) for line in lines)
    if header.get("type") != "session":
        raise ValueError("Continuation requires the original session header")
    return raw, events, {"source": first["source"], "size_bytes": len(raw), "sha256": _sha(raw)}


def _completed_input(events, prompt):
    """The supported single-input shape; not a general inbox/surface restorer."""
    inbox = [event for event in events if event.get("type") == "agent/inbox/spliced"]
    if len(inbox) != 2:
        raise ValueError("Continuation requires one unambiguous inserted and consumed input")
    queued, consumed = (event["data"] for event in inbox)
    messages = queued.get("inserted", [])
    if (queued.get("target") != "next-turn" or queued.get("start") != 0 or len(messages) != 1
            or consumed != {"target": "next-turn", "start": 0, "removedCount": 1, "inserted": []}):
        raise ValueError("Native input has additional or pending inbox activity")
    message = messages[0]
    expected = {"role": "user", "source": {"kind": "user"}, "content": [{"type": "text", "text": prompt}]}
    if not message.get("id") or any(message.get(key) != value for key, value in expected.items()):
        raise ValueError("Native receipt differs from this complete prompt")
    surface = [event for event in events if event.get("type") == "user/message"
               and event["data"].get("source", {}).get("kind") == "user"]
    turns = [event for event in events if event.get("type") == "turn/end"]
    if (len(surface) != 1 or surface[0]["data"] != message or len(turns) != 1
            or turns[0]["data"].get("reason", {}).get("kind") != "completed"
            or not inbox[0]["seq"] < inbox[1]["seq"] < surface[0]["seq"] < turns[0]["seq"]):
        raise ValueError("Native input lacks its own consumed message and completed turn")
    return message["id"]


def _same_patch(original, current):
    """Only the three call-owned MCP scope/audit arguments may differ."""
    normalized = []
    for patch in (original, current):
        copied = json.loads(json.dumps(patch))
        plugin = copied[-1]["insert"][0]
        args = plugin["config"]["args"]
        if plugin["id"] != "mcp-ergora-task" or len(args) != 6 or args[:3] != ["-I", "-m", "ergora.task_mcp"]:
            raise ValueError("Continuation requires the fixed per-call task MCP transport")
        args[3:] = ["scope", "scope-sha256", "audit"]
        normalized.append(copied)
    if normalized[0] != normalized[1]:
        raise ValueError("Native continuation patch changed outside its per-call scope/audit")


def main():
    versions = installed_versions()
    if sys.argv[1] == "--check":
        print(json.dumps({"distributions": versions, "python": sys.version}))
        return
    path = Path(sys.argv[1])
    request = json.loads(path.read_text(encoding="utf-8"))
    binding = request["binding"]
    credential = binding["api_key_env"]
    # Remove ambient DSH configuration and unrelated credentials before importing
    # or spawning the SDK. Retaining HOME does not imply host isolation.
    environment = {key: value for key, value in os.environ.items() if key in (
        "PATH", "HOME", "LANG", "LC_ALL", "PYTHONUTF8", "PYTHONIOENCODING", "TMPDIR",
        "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
        "http_proxy", "https_proxy", "all_proxy", "no_proxy", credential)}
    os.environ.clear()
    os.environ.update(environment)
    with redirect_stdout(sys.stderr):
        from deepseek_harness import DeepSeekHarness

    continuation = request.get("continuation")
    resuming = continuation is not None and continuation["kind"] == "resume"
    source = continuation["source"] if resuming else None
    root = Path(source["protocol"]) if resuming else path.parent
    home = root / "native-home"
    if not resuming:
        home.mkdir(mode=0o700)
    patch = [{"id": name, "disabled": True} for name in (
        "persistent-bash", "persistent-pwsh", "tool-fs", "tool-working-directory", "mcp-resources", "llm-deepseek")]
    patch.append({"insert": [{"id": "llm-ergora", "name": "@deepseek-ai/dsh-llm-pi-ai", "config": {"providers": {
        "ergora": {"apiKeyEnv": credential, "api": binding.get("api", "openai-completions"), "baseURL": binding["base_url"],
                   "models": [{"id": binding["model"], "contextWindow": binding.get("context_window", 131072),
                               "maxTokens": binding.get("max_tokens", 4096)}],
                   "retryPolicy": {"mode": "normal", "maxRetries": 0}}}}}]})
    if request["task_mcp"] is not None:
        patch.append({"insert": [{"id": "mcp-ergora-task", "name": "@deepseek-ai/dsh-mcp-client", "config": {
            "serverName": "ergora_task", "transport": "stdio", **request["task_mcp"], "cwd": request["cwd"],
            "startupTimeoutMs": 15000, "toolCallTimeoutMs": 15000, "closeTimeoutMs": 5000,
            "failOnStartupError": True, "reconnect": {"enabled": False}}}]})
    patch_path = path.parent / "native-patch.yml"
    patch_path.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
    prompt = request["prompt"]
    if request["schema"] is not None:
        prompt += "\n\nReturn exactly one JSON object matching this schema, without fences or explanation:\n" + json.dumps(request["schema"])
    (path.parent / "native-prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    native_id = source["session_id"] if resuming else "ergora-" + uuid.uuid4().hex
    (path.parent / "native-identity.json").write_text(json.dumps({"session_id": native_id, "distributions": versions,
        "python": sys.version, "profile": "sdk-minimal", "home": str(home)}), encoding="utf-8")

    notices = []
    def record(notification):
        if continuation is not None:
            notices.append(asdict(notification))
        with (path.parent / "native-events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(notification), ensure_ascii=False) + "\n")

    operation = native_directories(root, Path(request["cwd"])) if continuation is not None else nullcontext({})
    with operation as directories:
        frozen = None
        if continuation is not None:
            if prompt.lstrip().startswith("/") or request["mode"] != "task-mcp" or request["schema"] is None:
                raise ValueError("Continuation accepts only complete prepared task-MCP prompts")
            initial = call_files(path.parent, {name: limit for name, limit in CALL_METADATA_LIMITS.items()
                                               if name != "native-call-contract.json"})
            frozen = {"schema_version": 1, "session_id": native_id, **directories,
                "distributions": versions, "python_executable": os.path.realpath(sys.executable),
                "driver_sha256": _sha(Path(__file__).read_bytes()),
                "authority_sha256": _sha(json.dumps(continuation["authority"], ensure_ascii=False, sort_keys=True).encode()),
                "files": {name: _sha(raw) for name, raw in initial.items()}}
            _json_file(path.parent / "native-call-contract.json", frozen)
        b0 = b1 = None
        if resuming:
            old = call_files(root, {"native-source-seal.json": 65_536, **CALL_METADATA_LIMITS})
            seal = json.loads(old["native-source-seal.json"])
            previous = json.loads(old["request.json"])
            if (source["seal_sha256"] != _sha(old["native-source-seal.json"])
                    or seal["files"] != {name: _sha(raw) for name, raw in old.items() if name != "native-source-seal.json"}
                    or previous["continuation"]["kind"] != "source"
                    or previous["continuation"]["authority"] != continuation["authority"]
                    or previous["binding"] != binding or previous["schema"] != request["schema"]
                    or previous["cwd"] != request["cwd"] or source["cwd"] != request["cwd"]
                    or any(seal[key] != frozen[key] for key in ("cwd_identity", "home_identity", "distributions", "python_executable", "driver_sha256", "authority_sha256"))):
                raise ValueError("Native source runtime or frozen authorization changed")
            _same_patch(json.loads(old["native-patch.yml"]), patch)
            b0, original_events, history = _history(root, Path(request["cwd"]))
            if history != source["history"] or history != seal["history"]:
                raise ValueError("Native source no longer has its exact sealed history")
            _completed_input(original_events, old["native-prompt.txt"].decode("utf-8"))

        # The existing outer Ergora process owner bounds the whole call, including
        # notifications and MCP descendants; the SDK request timeout does not.
        with redirect_stdout(sys.stderr):
            with DeepSeekHarness(profile="sdk-minimal", dsh_home=str(home), patches=(str(patch_path),),
                cwd=request["cwd"], runtime_cwd=request["cwd"], provider="ergora", model=binding["model"],
                initialize_timeout_seconds=15, request_timeout_seconds=15, shutdown_timeout_seconds=5) as harness:
                if resuming:
                    session = harness.resume_session(native_id)
                    b1, _, restored = _history(root, Path(request["cwd"]))
                    suffix = b1[len(b0):]
                    _json_file(path.parent / "native-restore.json", {"source": source["history"],
                        "restored": restored, "restore_sha256": _sha(suffix), "prefix_preserved": b1.startswith(b0)})
                    if session.get_working_directory() != request["cwd"]:
                        raise ValueError("Restored native cwd differs from the frozen source")
                    added = [json.loads(line) for line in suffix.splitlines()]
                    if not b1.startswith(b0) or len(added) > 1 or any(event.get("type") != "session/end-seed" for event in added):
                        raise ValueError("Native resume changed more than the supported end-seed suffix; input was not sent")
                    with native_directories(root, Path(request["cwd"]), expected=directories):
                        _json_file(path.parent / "native-send-intent.json", {"session_id": native_id,
                            "prompt_sha256": _sha(prompt.encode()), "source_seal_sha256": source["seal_sha256"]})
                        result = session.run(prompt, on_notification=record)
                else:
                    operation = native_directories(root, Path(request["cwd"]), expected=directories) if continuation is not None else nullcontext()
                    with operation:
                        result = harness.run(prompt, session_id=native_id, on_notification=record)
                native = {"session_id": result.session_id, "finish_reason": result.finish_reason,
                          "final_response": result.final_response, "events": result.events}
                (path.parent / "native-result.json").write_text(json.dumps(native, ensure_ascii=False), encoding="utf-8")
        if continuation is not None:
            if result.session_id != native_id or result.finish_reason != "completed":
                raise ValueError("Continuation input did not complete in its original session")
            receipt_id = _completed_input(result.events, prompt)
            idle = any(item["method"] == "session.status" and item["payload"].get("sessionId") == native_id
                       and item["payload"].get("status") == "idle" for item in notices)
            if not idle:
                raise ValueError("Native input lacks its matching root idle notification")
            # SDK idle is not a persistence barrier. Capture only after normal close.
            final, events, history = _history(root, Path(request["cwd"]))
            actual = call_files(path.parent, CALL_METADATA_LIMITS)
            metadata = {name: _sha(raw) for name, raw in actual.items()}
            if frozen["files"] != {name: digest for name, digest in metadata.items() if name != "native-call-contract.json"}:
                raise ValueError("Call metadata changed after its pre-input freeze")
            if resuming:
                if not final.startswith(b1) or _completed_input([event for event in events if event["seq"] >= result.events[0]["seq"]], prompt) != receipt_id:
                    raise ValueError("Continuation archive lacks its original prefix or this exact completed input")
                projected = json.dumps(json.loads(result.final_response), ensure_ascii=False, sort_keys=True).encode()
                _json_file(path.parent / "native-continuation.json", {"schema_version": 1, "session_id": native_id,
                    "source_seal_sha256": source["seal_sha256"], "restored_bytes": len(b1), "final_bytes": len(final),
                    "restore_sha256": _sha(b1[len(b0):]), "activity_sha256": _sha(final[len(b1):]),
                    "receipt_id": receipt_id, "root_idle": True, "history": history, "files": metadata,
                    "result_sha256": _sha(projected)})
            else:
                if _completed_input(events, prompt) != receipt_id:
                    raise ValueError("Source archive differs from its own completed input")
                _json_file(path.parent / "native-source-seal.json", {**frozen, "files": metadata,
                    "history": history, "receipt_id": receipt_id, "root_idle": True})
        print(result.final_response)


if __name__ == "__main__":
    main()
