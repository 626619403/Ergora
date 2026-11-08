"""Per-call MCP projection of fixed declared resources; no workspace or host-path tools."""

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

from . import contracts, definition_bundles
from .asset_trees import inventory_tree


MAX_SCOPE_BYTES = 16_000_000
TOOLS = ["list", "read"]
_SCHEMA = json.loads((Path(__file__).parent / "data/schemas/task-mcp-scope-v1.json").read_text(encoding="utf-8"))


def check_available() -> None:
    if sys.platform != "linux":
        raise ValueError("Task MCP scope creation currently requires Linux no-follow file descriptors; use WSL2")
    if importlib.util.find_spec("mcp") is None:
        raise ValueError("Task MCP requires the optional dependency: pip install 'ergora[task-mcp]'")


def _fixed_bytes(root: Path, name: str, expected: str, limit: int = 10_000_000) -> bytes:
    """Never follow a replaced component or read a special/hard-linked file."""
    parts = definition_bundles.relative_path(name, "Task MCP").parts
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        file = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        with os.fdopen(file, "rb") as stream:
            details = os.fstat(stream.fileno())
            if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
                raise ValueError("Task MCP resources must be ordinary files without hard links")
            content = stream.read(limit + 1)
        if len(content) > limit or hashlib.sha256(content).hexdigest() != expected:
            raise ValueError(f"Task MCP resource identity changed: {name}")
        return content
    finally:
        os.close(descriptor)


def freeze(prepared: dict, run_id: str, destination: Path) -> dict:
    """Consume an already-verified input and freeze only the selected structural chain."""
    check_available()
    leaf = next(item for item in prepared["composition"]["instances"] if item["path"] == prepared["request"]["instance"])
    bundles, entries = {}, {}
    assets = Path(prepared["path"]) / "assets"
    for resource in leaf["resources"]:
        for origin in resource["sources"]:
            ref = origin["definition"]
            key = (ref["kind"], ref["digest"])
            if key not in bundles:
                bundle = assets / (ref["kind"] + "-definitions") / "objects" / ref["digest"]
                digest, files, _ = inventory_tree(bundle, label="Task MCP resource", max_directories=500, max_depth=32)
                if digest != ref["digest"]:
                    raise ValueError("Task MCP definition identity changed")
                bundles[key] = bundle, files
            bundle, files = bundles[key]
            names = [name for name in files if name.startswith(origin["path"] + "/")] if resource["kind"] == "skill" else [origin["path"]]
            for name in names:
                suffix = name[len(origin["path"]):]
                uri = origin["uri"] + suffix
                definition_bundles.relative_path(uri, "Task MCP")
                if uri not in entries:
                    content = _fixed_bytes(bundle, name, files[name]["sha256"])
                    entries[uri] = {"sha256": files[name]["sha256"], "size": len(content),
                                    "content_base64": base64.b64encode(content).decode("ascii"), "sources": []}
                if origin not in entries[uri]["sources"]:
                    entries[uri]["sources"].append(origin)
    document = {"schema_version": 1, "kind": "task-mcp-scope", "run_id": run_id,
                "input_digest": prepared["digest"], "instance": leaf["path"], "tools": TOOLS,
                "files": dict(sorted(entries.items()))}
    ResourceView(document)
    encoded = json.dumps(document, sort_keys=True, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_SCOPE_BYTES:
        raise ValueError("Complete task MCP scope exceeds 16 MB; resources were not truncated")
    with destination.open("xb") as stream:
        stream.write(encoded)
    destination.chmod(0o600)
    return {"path": str(destination), "sha256": hashlib.sha256(encoded).hexdigest(),
            "files": len(entries), "input_digest": prepared["digest"], "instance": leaf["path"]}


class ResourceView:
    """A bounded, verified in-memory URI table. Tool arguments never address host files."""

    def __init__(self, document: dict):
        contracts.validate(document, _SCHEMA, "Task MCP scope")
        self.document, self.contents = document, {}
        total = 0
        for uri, details in document["files"].items():
            definition_bundles.relative_path(uri, "Task MCP")
            content = base64.b64decode(details["content_base64"], validate=True)
            total += len(content)
            if total > 10_000_000 or len(content) != details["size"] or hashlib.sha256(content).hexdigest() != details["sha256"]:
                raise ValueError("Task MCP scope content is oversized or differs from its identity")
            self.contents[uri] = content

    @classmethod
    def load(cls, path: Path, expected: str):
        encoded = _fixed_bytes(path.parent, path.name, expected, MAX_SCOPE_BYTES)
        return cls(json.loads(encoded))

    def list(self, path: str = "", offset: int = 0, max_entries: int = 100) -> dict:
        if path:
            definition_bundles.relative_path(path, "Task MCP")
        contracts.validate(offset, {"type": "integer", "minimum": 0}, "List offset")
        contracts.validate(max_entries, {"type": "integer", "minimum": 1, "maximum": 100}, "List page size")
        names = [name for name in sorted(self.contents) if not path or name.startswith(path + "/")]
        if path and not names:
            raise ValueError("Unknown task resource directory")
        if offset > len(names):
            raise ValueError("List offset exceeds the selected directory")
        selected, size = [], 0
        for name in names[offset:offset + max_entries]:
            details = {key: value for key, value in self.document["files"][name].items() if key != "content_base64"}
            size += len(json.dumps({"uri": name, **details}, ensure_ascii=False).encode("utf-8"))
            if size > 65536:
                if not selected:
                    raise ValueError("Task resource metadata exceeds the 64 KiB list page limit")
                break
            selected.append(name)
        return {"files": [{"uri": name, **{key: value for key, value in self.document["files"][name].items()
                                          if key != "content_base64"}} for name in selected],
                "next_offset": offset + len(selected) if offset + len(selected) < len(names) else None}

    def read(self, path: str, offset: int = 0, max_bytes: int = 65536) -> dict:
        definition_bundles.relative_path(path, "Task MCP")
        if path not in self.contents:
            raise ValueError("Unknown task resource")
        content = self.contents[path]
        contracts.validate(offset, {"type": "integer", "minimum": 0, "maximum": len(content)}, "Read offset")
        contracts.validate(max_bytes, {"type": "integer", "minimum": 1, "maximum": 65536}, "Read page size")
        chunk = content[offset:offset + max_bytes]
        try:
            text, encoding = chunk.decode("utf-8"), "utf-8"
        except UnicodeDecodeError:
            text, encoding = base64.b64encode(chunk).decode("ascii"), "base64"
        return {"uri": path, "sha256": self.document["files"][path]["sha256"], "size": len(content),
                "offset": offset, "encoding": encoding, "content": text,
                "next_offset": offset + len(chunk) if offset + len(chunk) < len(content) else None}


def launch(scope: dict, audit: Path) -> dict:
    return {"command": sys.executable, "args": ["-I", "-m", "ergora.task_mcp", scope["path"], scope["sha256"], str(audit)]}


def serve(path: Path, digest: str, audit: Path) -> None:
    # -I ignores Python path/user-site injection before module execution. This
    # service has no credentials and never passes inference environment to MCP.
    environment = {key: value for key, value in os.environ.items() if key in (
        "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "LANG", "LC_ALL", "PYTHONUTF8", "PYTHONIOENCODING")}
    os.environ.clear()
    os.environ.update(environment)
    from mcp.server import MCPServer
    from mcp.types import ToolAnnotations

    view = ResourceView.load(path, digest)
    def record(**fields):
        with audit.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"pid": os.getpid(), "scope_sha256": digest, **fields}) + "\n")

    async def observe(context, call_next):
        result = await call_next(context)
        if context.method in ("initialize", "tools/list", "tools/call"):
            payload = result.model_dump(mode="json", by_alias=True) if hasattr(result, "model_dump") else result
            fields = {"method": context.method, "protocol_version": context.protocol_version,
                      "success": not payload.get("isError", False)}
            if context.method == "tools/list":
                fields["tools"] = sorted(tool["name"] for tool in payload["tools"])
            if context.method == "tools/call":
                fields["tool"] = context.params.get("name")
            record(**fields)
        return result

    server = MCPServer("ergora-task", version="1", middleware=[observe], log_level="ERROR")
    annotations = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    @server.tool(name="list", annotations=annotations)
    def list_resources(path: str = "", offset: int = 0, max_entries: int = 100) -> dict:
        """List only this call's declared fixed resources; paginate with next_offset."""
        return view.list(path, offset, max_entries)

    @server.tool(name="read", annotations=annotations)
    def read_resource(path: str, offset: int = 0, max_bytes: int = 65536) -> dict:
        """Read a declared resource by virtual URI, at most 64 KiB; no host paths."""
        return view.read(path, offset, max_bytes)

    record(event="started", environment_keys=sorted(os.environ))
    try:
        server.run(transport="stdio")
    finally:
        record(event="closed")


async def probe(configuration: dict, stderr: Path) -> dict:
    try:
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        import anyio
        from mcp.shared.exceptions import MCPError
    except ImportError as error:
        raise ValueError("Task MCP requires a working mcp 2.3.0 installation; reinstall 'ergora[task-mcp]'") from error

    try:
        with stderr.open("w", encoding="utf-8") as errors:
            with anyio.fail_after(15):
                async with stdio_client(StdioServerParameters(**configuration), errlog=errors) as (reader, writer):
                    async with ClientSession(reader, writer, read_timeout_seconds=5) as session:
                        await session.initialize()
                        tools = await session.list_tools()
                        if sorted(tool.name for tool in tools.tools) != TOOLS:
                            raise ValueError("Task MCP did not expose exactly list/read")
                        result = await session.call_tool("list", {})
                        if result.is_error:
                            raise ValueError("Task MCP resource probe failed")
                        return {"initialized": True, "tools": TOOLS, "read_only_probe": "succeeded"}
    except (OSError, ValueError, TimeoutError, ExceptionGroup, MCPError) as error:
        raise ValueError(f"Task MCP preflight failed; see {stderr.name}: {error}") from error


def verify_native(audit: Path, scope_sha256: str) -> dict:
    if not audit.is_file() or audit.stat().st_size > 1_000_000:
        raise ValueError("Required native task MCP connection receipt is missing or oversized")
    events = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    ready = next((event for event in events if event.get("method") == "tools/list" and event.get("success")
                  and event.get("tools") == TOOLS), None)
    if (not events or any(event.get("scope_sha256") != scope_sha256 for event in events)
            or ready is None):
        raise ValueError("Required native task MCP tools/list did not succeed")
    # SDK v2 also accepts protocol-valid stateless requests without initialize.
    # Its successful tools/list response is readiness evidence for both eras.
    return {"ready": True, "handshake_observed": any(event.get("method") == "initialize" and event.get("success") for event in events),
            "protocol_version": ready.get("protocol_version"), "tools": TOOLS, "receipt": str(audit),
            "receipt_sha256": hashlib.sha256(audit.read_bytes()).hexdigest()}


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m ergora.task_mcp SCOPE SHA256 AUDIT")
    serve(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
