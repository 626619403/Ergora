"""Runs in the optional pinned SDK environment; no Ergora imports or scheduler."""

from contextlib import ExitStack, contextmanager, redirect_stdout
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

    home = path.parent / 'native-home'
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
    native_id = "ergora-" + uuid.uuid4().hex
    (path.parent / "native-identity.json").write_text(json.dumps({"session_id": native_id, "distributions": versions,
        "python": sys.version, "profile": "sdk-minimal", "home": str(home)}), encoding="utf-8")

    def record(notification):
        with (path.parent / "native-events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(notification), ensure_ascii=False) + "\n")

    # The original outer process owner bounds the call and its MCP descendants.
    with redirect_stdout(sys.stderr):
        with DeepSeekHarness(profile="sdk-minimal", dsh_home=str(home), patches=(str(patch_path),),
            cwd=request["cwd"], runtime_cwd=request["cwd"], provider="ergora", model=binding["model"],
            initialize_timeout_seconds=15, request_timeout_seconds=15, shutdown_timeout_seconds=5) as harness:
            result = harness.run(prompt, session_id=native_id, on_notification=record)
            native = {"session_id": result.session_id, "finish_reason": result.finish_reason,
                      "final_response": result.final_response, "events": result.events}
            (path.parent / "native-result.json").write_text(json.dumps(native, ensure_ascii=False), encoding="utf-8")
    print(result.final_response)


if __name__ == "__main__":
    main()
