"""Native Agent adapters; the local mapping selects execution, not public schemas."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

from . import components, contracts, processes
from .data.drivers.deepseek import (CALL_METADATA_LIMITS, MAX_CONTINUATION_HISTORY,
    call_files as _call_files, native_directories as _native_directories, native_history_page)


def _events(output: Path):
    with (output / "stdout.txt").open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def _restricted_policy(mode: str, native_tools: list[str], credentials: str, sandbox: dict) -> dict:
    task = mode == "task-mcp"
    return {"mode": mode,
        "basis": "Backend implementation contract; installed CLI, authentication and provider capacity have not been probed",
        "model_tools": ("explicit task MCP list/read; " if task else "no file, shell, web or MCP tools; ") +
                       "native response/interaction tools may remain",
        "native_companion_tools": native_tools,
        "resources": "complete inline instructions/context; declared fixed resources via MCP" if task else
                     "complete inline instructions/context; Skill attachments unavailable to this mode",
        "ambient_configuration": "disabled by native CLI options",
        "authentication": credentials, "host_isolation": "not provided",
        "capabilities": {
            "inline_material": {"status": "enforced", "effective": "complete inherited instructions/context and operator prompt",
                                "scope": "byte delivery, not model understanding or a provider context-window guarantee"},
            "fixed_resource_read": {"status": "enforced" if task else "unsupported",
                                    "effective": "selected structural chain's declared fixed resources" if task else []},
            "workspace_read": {"status": "unsupported", "effective": []},
            "write": {"status": "unsupported", "effective": []},
            "shell": {"status": "unsupported", "effective": False},
            "tool_network_origins": {"status": "unsupported", "effective": []},
            "task_mcp": {"status": "enforced" if task else "unsupported", "tools": ["list", "read"] if task else []},
            "external_mcp": {"status": "unsupported", "effective": []},
            "backend_sandbox": sandbox,
            "host_isolation": {"status": "unsupported", "effective": "trusted user/process boundary"}},
        "infrastructure": "Inference HTTP, stdio subprocesses, logs and State writes remain trusted infrastructure"}


@dataclass(frozen=True)
class Invocation:
    role: str
    prompt: str
    cwd: Path
    protocol: Path
    timeout: int
    schema: dict | None
    mode: str = "native"
    task_mcp: dict | None = None
    continuation: dict | None = None


class AgentBackend(ABC):
    authentication = "not_checked"
    guidance: tuple[str, ...] = ()
    invocation_modes = ("native",)

    def __init__(self, binding: dict, options: dict):
        self.binding = binding
        self.options = options

    def validate_binding(self, role: str, *, formal: bool = False) -> None:
        contracts.validate(self.binding, components.COMPONENTS[self.binding["tool"]]["configuration"], f"{role} binding")

    @abstractmethod
    def executable(self) -> str:
        """Return the executable selected by this binding."""

    def available(self, cwd: Path) -> bool:
        try:
            processes.resolve_program(self.executable(), cwd)
        except (OSError, ValueError):
            return False
        return True

    def check_invocation(self) -> None:
        """Reject unsupported runtime modes before creating protocol files."""

    def check_mode(self, mode: str) -> None:
        if mode not in self.invocation_modes:
            raise ValueError(f"{self.binding['tool']} does not support {mode} composition calls")

    def composition_policy(self, mode: str) -> dict:
        """Describe an admitted restricted mode; declaring its name is insufficient."""
        raise ValueError(f"{self.binding['tool']} has no composition capability contract for {mode}")

    @abstractmethod
    def command(self, request: Invocation) -> tuple[list[str], str]:
        """Prepare the native command and stdin in an existing protocol directory."""

    def read_result(self, output: Path, request: Invocation) -> dict:
        return json.loads((output / "stdout.txt").read_text(encoding="utf-8"))

    def archived_history(self, protocol: Path, *, cwd: Path, offset: int,
                         limit: int, revision: str | None) -> dict:
        """Observe saved native bytes without starting an interpreter or SDK."""
        return {"available": False, "reason": "This backend has no native archive reader"}

    def check_continuation(self, mode: str) -> None:
        raise ValueError(f"{self.binding['tool']} does not support explicit session continuation")

    def continuation_source(self, protocol: Path, *, cwd: Path) -> dict:
        raise ValueError(f"{self.binding['tool']} does not support explicit session continuation")

    def continuation_result(self, protocol: Path, *, source: dict) -> dict:
        raise ValueError(f"{self.binding['tool']} does not support explicit session continuation")

    def diagnostics(self) -> dict:
        return {"authentication": self.authentication, "remediation": [
            "Run an explicitly budgeted agent invocation to verify the selected model and task; doctor never calls a model.",
            *self.guidance]}

    def probe_commands(self, cwd: Path) -> list[tuple[str, list[str]]]:
        """Only fixed local diagnostics; arbitrary bindings never execute here."""
        return []


class CodexBackend(AgentBackend):
    invocation_modes = ("native", "text-only", "task-mcp", "workspace-task-mcp")
    guidance = ("Use codex login, then tools doctor PROJECT --probe; stored credentials do not verify account access or quota.",)

    def executable(self) -> str:
        return self.options.get("executable") or "codex"

    def composition_policy(self, mode: str) -> dict:
        self._options(mode)
        if mode == "workspace-task-mcp":
            if self.binding.get("sandbox") != "current-container" or sys.platform != "linux":
                raise ValueError("Workspace task MCP requires an explicit trusted Linux current-container binding (WSL2 uses Linux)")
            policy = _restricted_policy("task-mcp", ["command_execution", "apply_patch", "request_user_input"],
                "Codex inference provider environment credentials; not checked",
                {"status": "advisory", "requested": "current-container", "effective": "current-container",
                 "scope": "Explicit trusted current-user execution; no inter-agent OS isolation"})
            policy.update(mode=mode, model_tools="explicit workspace shell/file tools and fixed task MCP list/read",
                resources="complete inherited material and fixed Skill resources; original approved workspace checkout")
            policy['capabilities'].update(
                workspace_read={"status": "advisory", "effective": "declared read ceilings; current user can access other files"},
                write={"status": "advisory", "effective": "unit paths; trusted executor gates final Git changes before/after checks"},
                shell={"status": "enforced", "effective": True},
                tool_network_origins={"status": "advisory", "effective": "no model network origins authorized; shell egress is not isolated"})
            return policy
        native = ["request_user_input"]
        if mode == "task-mcp":
            native += ["list_mcp_resources", "list_mcp_resource_templates", "read_mcp_resource"]
        return _restricted_policy(mode, native,
            "Codex login or explicit inference provider environment credential references; not checked",
            {"status": "advisory", "requested": self.binding.get("sandbox"), "effective": "read-only",
             "scope": "Codex CLI request; does not establish host isolation"})

    def check_invocation(self) -> None:
        if sys.platform != "linux" and self.binding.get("sandbox") == "current-container":
            raise ValueError("current-container requires the trusted Linux container configuration; use the native Codex sandbox on Windows")
        self._options("native")

    def _options(self, mode: str, task_mcp: dict | None = None) -> list[str]:
        """Parse the same inference options for model-free admission and command construction."""
        options = list(self.options.get("arguments") or [])
        config = {}
        if self.options.get("config") is not None:
            options += ["--ignore-user-config", "--ignore-rules", "--disable", "plugins", "--disable", "apps"]
            config = tomllib.loads(Path(self.options["config"]).read_text(encoding="utf-8"))
        if mode != "native":
            if self.options.get("arguments"):
                raise ValueError("Restricted composition calls do not accept additional native arguments")
            options = ["--ignore-user-config", "--ignore-rules", "--strict-config", "--skip-git-repo-check"]
            config = {key: value for key, value in config.items() if key in (
                "model", "model_provider", "model_reasoning_effort", "service_tier", "model_providers")}
            if "model_providers" in config:
                if not isinstance(config["model_providers"], dict) or any(
                        not isinstance(provider, dict) for provider in config["model_providers"].values()):
                    raise ValueError("Codex inference providers must be TOML tables")
                config["model_providers"] = {name: {key: value for key, value in provider.items() if key in (
                    "name", "base_url", "env_key", "wire_api", "requires_openai_auth", "env_http_headers")}
                    for name, provider in config["model_providers"].items()}
            config.update({"features.shell_tool": mode == "workspace-task-mcp", "features.goals": False, "features.hooks": False,
                "features.view_image": False, "features.multi_agent": False, "features.apps": False,
                "features.plugins": False, "features.memories": False, "features.skill_mcp_dependency_install": False,
                "skills.include_instructions": False, "skills.bundled.enabled": False,
                "web_search": "disabled", "project_doc_max_bytes": 0})
            if task_mcp is not None:
                config["mcp_servers"] = {"ergora_task": {**task_mcp,
                    "enabled_tools": ["list", "read"], "required": True,
                    "startup_timeout_sec": 15, "tool_timeout_sec": 15}}

        def add(table, prefix=""):
            for key, value in table.items():
                name = prefix + key
                if isinstance(value, dict):
                    add(value, name + ".")
                elif name != "approval_policy" and not name.startswith("sandbox_"):
                    try:
                        encoded = json.dumps(value, allow_nan=False)
                    except (TypeError, ValueError) as error:
                        raise ValueError(f"Codex configuration field is not JSON-compatible: {name}") from error
                    options.extend(["-c", name + "=" + encoded])

        add(config)
        return options

    def command(self, request: Invocation) -> tuple[list[str], str]:
        if request.mode == "workspace-task-mcp":
            self.composition_policy(request.mode)
        options = self._options(request.mode, request.task_mcp)
        sandbox = "read-only" if request.mode not in ("native", "workspace-task-mcp") else self.binding.get(
            "sandbox", "read-only" if request.role != "implementer" else "workspace-write")
        sandbox = "danger-full-access" if sandbox == "current-container" else sandbox
        argv = [self.executable(), "exec", "--ephemeral", "--sandbox", sandbox, "--json", *options]
        if "model" in self.binding:
            argv += ["--model", self.binding["model"]]
        if request.schema:
            argv += ["--output-schema", str(request.protocol / "schema.json"),
                     "--output-last-message", str(request.protocol / "result.json")]
        return [*argv, "-"], request.prompt

    def read_result(self, output: Path, request: Invocation) -> dict:
        if request.mode in ("task-mcp", "workspace-task-mcp"):
            for event in _events(output):
                item = event.get("item", {})
                if (event.get("type") == "item.completed" and item.get("type") == "mcp_tool_call"
                        and item.get("server") == "ergora_task" and item.get("error") is not None):
                    raise ValueError("Required task MCP transport failed; see native stdout.txt")
        return json.loads((request.protocol / "result.json").read_text(encoding="utf-8"))

    def probe_commands(self, cwd: Path) -> list[tuple[str, list[str]]]:
        program = processes.resolve_program(self.executable(), cwd)
        return [("version", [program, "--version"]), ("authentication", [program, "login", "status"])]


class ClaudeCodeBackend(AgentBackend):
    invocation_modes = ("native", "text-only", "task-mcp")
    guidance = ("Use claude auth login; authentication is not checked by this driver.",
                "Task MCP uses --bare: configure its supported API environment credentials; stored OAuth/keychain credentials are not read.")

    def executable(self) -> str:
        return "claude"

    def composition_policy(self, mode: str) -> dict:
        credentials = ("Bare mode API environment credentials; stored OAuth/keychain are not read" if mode == "task-mcp" else
                       "Native Claude authentication or its supported environment credentials; not checked")
        return _restricted_policy(mode, ["StructuredOutput"], credentials,
            {"status": "unsupported", "requested": None, "effective": None,
             "scope": "Native tools are disabled; this mode does not request an OS sandbox"})

    def command(self, request: Invocation) -> tuple[list[str], str]:
        argv = ["claude", "--print", "--output-format", "json", "--no-session-persistence"]
        if request.mode != "native":
            servers = {} if request.task_mcp is None else {"ergora_task": {"type": "stdio", **request.task_mcp}}
            argv += ["--setting-sources", "", "--restricted", "--tools", "", "--strict-mcp-config",
                     "--mcp-config", json.dumps({"mcpServers": servers}), "--max-turns", "24" if servers else "3"]
            if servers:
                argv[argv.index("--output-format") + 1] = "stream-json"
                argv += ["--verbose", "--bare", "--allowedTools", "mcp__ergora_task__list", "mcp__ergora_task__read"]
            else:
                argv += ["--safe-mode"]
        elif request.role != "implementer":
            argv += ["--tools", "Read,Grep,Glob", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
        if "model" in self.binding:
            argv += ["--model", self.binding["model"]]
        if request.schema:
            argv += ["--json-schema", json.dumps(request.schema)]
        return argv, request.prompt

    def read_result(self, output: Path, request: Invocation) -> dict:
        if request.mode == "task-mcp":
            calls, result = set(), None
            for event in _events(output):
                if event.get("type") in ("assistant", "user"):
                    for block in event["message"]["content"]:
                        if block.get("type") == "tool_use" and block.get("name") in (
                                "mcp__ergora_task__list", "mcp__ergora_task__read"):
                            calls.add(block["id"])
                        if (block.get("type") == "tool_result" and block.get("tool_use_id") in calls
                                and block.get("is_error") and not isinstance(event.get("tool_use_result"), dict)):
                            # Server CallToolResult errors remain recoverable; native
                            # connection failures have no server result payload.
                            raise ValueError("Required task MCP transport failed; see native stdout.txt")
                elif event.get("type") == "result":
                    result = event
            if result is None:
                raise ValueError("Claude Code stream has no terminal result")
        else:
            result = super().read_result(output, request)
        if result.get("is_error"):
            raise ValueError("Claude Code reported an error")
        return result.get("structured_output")

    def probe_commands(self, cwd: Path) -> list[tuple[str, list[str]]]:
        return [("version", [processes.resolve_program(self.executable(), cwd), "--version"])]


class MiniSweBackend(AgentBackend):
    def executable(self) -> str:
        return self.binding.get("python", sys.executable)

    def check_invocation(self) -> None:
        if sys.platform != "linux":
            raise ValueError("This mini-swe-agent driver requires Linux/bash; use WSL2")

    def available(self, cwd: Path) -> bool:
        if sys.platform != "linux":
            return False
        try:
            program = processes.resolve_program(self.executable(), cwd)
            result = subprocess.run([program, "-c", "import importlib.util;raise SystemExit(0 if importlib.util.find_spec('minisweagent') else 1)"],
                                    cwd=cwd, capture_output=True, timeout=5)
        except (OSError, ValueError, subprocess.SubprocessError):
            return False
        return result.returncode == 0

    def command(self, request: Invocation) -> tuple[list[str], str]:
        document = {"binding": self.binding, "prompt": request.prompt, "cwd": str(request.cwd),
                    "timeout": request.timeout, "trajectory": str(request.protocol / "trajectory.json")}
        path = request.protocol / "request.json"
        path.write_text(json.dumps(document), encoding="utf-8", newline="\n")
        return [self.executable(), str(Path(__file__).parent / "data/drivers/mini.py"), str(path)], ""

    def probe_commands(self, cwd: Path) -> list[tuple[str, list[str]]]:
        return [("version", [self.executable(), "-c",
                "from importlib.metadata import version; print(version('mini-swe-agent'))"])]


class DeepSeekHarnessBackend(AgentBackend):
    """Optional SDK environment, admitted only for fixed-resource read-only calls."""

    invocation_modes = ("text-only", "task-mcp")
    guidance = ("Install the pinned DeepSeek SDK/runtime in a separate Python environment and select its interpreter.",
                "Configure the OpenAI-compatible base_url, model and api_key_env; native/workspace calls are unsupported.",
                "Session continuation requires an explicitly enabled new standalone task-MCP source and its frozen contract.")

    def executable(self) -> str:
        return self.binding["python"]

    def validate_binding(self, role: str, *, formal: bool = False) -> None:
        super().validate_binding(role, formal=formal)
        from urllib.parse import urlsplit

        url = urlsplit(self.binding["base_url"])
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("DeepSeek base_url requires HTTP(S), without credentials, query or fragment")

    def check_invocation(self) -> None:
        if sys.platform != "linux":
            raise ValueError("This DeepSeek Harness adapter currently requires Linux; use WSL2")

    def probe_commands(self, cwd: Path) -> list[tuple[str, list[str]]]:
        return [("version", [processes.resolve_program(self.executable(), cwd), "-I",
                             str(Path(__file__).parent / "data/drivers/deepseek.py"), "--check"])]

    def available(self, cwd: Path) -> bool:
        if sys.platform != "linux":
            return False
        try:
            result = subprocess.run(self.probe_commands(cwd)[0][1], cwd=cwd, capture_output=True, timeout=5)
        except (OSError, ValueError, subprocess.SubprocessError):
            return False
        return result.returncode == 0

    def composition_policy(self, mode: str) -> dict:
        policy = _restricted_policy(mode, [], "Only the named API environment credential; not checked",
            {"status": "unsupported", "requested": None, "effective": None,
             "scope": "Fixed model tools; no OS sandbox is requested"})
        policy.update(ambient_configuration="fresh explicit SDK home and fixed sdk-minimal invocation patch",
            model_tools="only fixed task MCP list/read" if mode == "task-mcp" else "no model tools",
            native_errors="Any native tool error rejects this call; no implicit retry or session resume")
        return policy

    def command(self, request: Invocation) -> tuple[list[str], str]:
        document = {"binding": self.binding, "prompt": request.prompt, "cwd": str(request.cwd),
                    "schema": request.schema, "mode": request.mode, "task_mcp": request.task_mcp}
        if request.continuation is not None:
            document["continuation"] = request.continuation
        path = request.protocol / "request.json"
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8", newline="\n")
        return [self.executable(), "-I", str(Path(__file__).parent / "data/drivers/deepseek.py"), str(path)], ""

    def read_result(self, output: Path, request: Invocation) -> dict:
        native = json.loads((request.protocol / "native-result.json").read_text(encoding="utf-8"))
        if native["finish_reason"] != "completed":
            raise ValueError("DeepSeek Harness input did not complete")
        if any(event.get("type") == "tool/result" and event["data"]["message"].get("isError")
               for event in native["events"]):
            raise ValueError("DeepSeek Harness reported a tool error; see native-events.jsonl")
        return json.loads(native["final_response"])

    def check_continuation(self, mode: str) -> None:
        self.check_invocation()
        if mode != "task-mcp":
            raise ValueError("Explicit continuation requires a standalone task-MCP call")

    def continuation_source(self, protocol: Path, *, cwd: Path) -> dict:
        self.check_continuation("task-mcp")
        material = _call_files(protocol, {"native-source-seal.json": 65_536, **CALL_METADATA_LIMITS})
        seal = json.loads(material["native-source-seal.json"])
        request = json.loads(material["request.json"])
        identity = json.loads(material["native-identity.json"])
        frozen = json.loads(material["native-call-contract.json"])
        for value in (seal, request, identity, frozen):
            contracts.validate(value, {"type": "object"}, "Saved continuation metadata")
        metadata = {name: hashlib.sha256(raw).hexdigest() for name, raw in material.items() if name != "native-source-seal.json"}
        if (type(seal.get("schema_version")) is not int or seal["schema_version"] != 1
                or not isinstance(request.get("continuation"), dict) or request["continuation"].get("kind") != "source"
                or not isinstance(request["continuation"].get("authority"), dict)
                or request.get("binding") != self.binding or request.get("cwd") != str(cwd)
                or request.get("mode") != "task-mcp" or not isinstance(request.get("schema"), dict)
                or request["schema"] != json.loads(material["schema.json"])
                or not isinstance(identity.get("session_id"), str) or seal.get("session_id") != identity["session_id"]
                or seal.get("root_idle") is not True or not seal.get("receipt_id")
                or frozen.get("files") != {name: digest for name, digest in metadata.items() if name != "native-call-contract.json"}
                or any(seal.get(key) != value for key, value in frozen.items() if key != "files")
                or seal.get("files") != {name: hashlib.sha256(raw).hexdigest() for name, raw in material.items()
                                         if name != "native-source-seal.json"}):
            raise ValueError("Native source differs from its frozen call contract")
        with _native_directories(protocol, cwd, expected=seal):
            history, _ = self._history_snapshot(protocol, cwd)
        if seal.get("history") != history:
            raise ValueError("Native source history changed after its sealed completion")
        return {"protocol": str(protocol), "cwd": str(cwd), "session_id": identity["session_id"],
                "seal_sha256": hashlib.sha256(material["native-source-seal.json"]).hexdigest(),
                "authority": request["continuation"]["authority"], "history": history}

    def _history_snapshot(self, protocol: Path, cwd: Path, ranges: tuple = ()) -> tuple[dict, list[str]]:
        digest = hashlib.sha256()
        intervals = [hashlib.sha256() for _ in ranges]
        offset, revision, first = 0, None, None
        while True:
            page = self.archived_history(protocol, cwd=cwd, offset=offset, limit=65_536, revision=revision)
            if not page["available"] or page["size_bytes"] > MAX_CONTINUATION_HISTORY:
                raise ValueError("Continuation requires an available native archive of at most 64 MiB")
            first = first or page
            raw = page["content"].encode("utf-8")
            digest.update(raw)
            for (start, end), hasher in zip(ranges, intervals):
                left, right = max(start, offset), min(end, offset + len(raw))
                if left < right:
                    hasher.update(raw[left - offset:right - offset])
            if page["next_offset"] is None:
                break
            revision, offset = page["revision"], page["next_offset"]
        history = {"source": first["source"], "size_bytes": first["size_bytes"], "sha256": digest.hexdigest()}
        return history, [hasher.hexdigest() for hasher in intervals]

    def continuation_result(self, protocol: Path, *, source: dict) -> dict:
        """Observe stopped-call bytes even when no completed input receipt exists."""
        root, cwd = Path(source["protocol"]), Path(source["cwd"])
        sealed = _call_files(root, {"native-source-seal.json": 65_536})["native-source-seal.json"]
        if hashlib.sha256(sealed).hexdigest() != source["seal_sha256"]:
            raise ValueError("Native source seal changed during continuation")
        seal = json.loads(sealed)
        try:
            restoration = json.loads(_call_files(protocol, {"native-restore.json": 65_536})["native-restore.json"])
        except FileNotFoundError:
            restoration = None
        b0 = source["history"]["size_bytes"]
        b1 = restoration["restored"]["size_bytes"] if restoration is not None else None
        if b1 is not None and (type(b1) is not int or not b0 <= b1 <= MAX_CONTINUATION_HISTORY):
            raise ValueError("Native restore observation has an invalid byte interval")
        with _native_directories(root, cwd, expected=seal):
            history, hashes = self._history_snapshot(root, cwd,
                ((0, b0), (b0, b1 or b0), (b1 or b0, MAX_CONTINUATION_HISTORY), (0, b1 or b0)))
        observed = {"completed": False, "session_id": source["session_id"], "source_bytes": b0,
            "restored_bytes": b1, "final_bytes": history["size_bytes"], "history": history,
            "source_prefix_preserved": history["size_bytes"] >= b0 and hashes[0] == source["history"]["sha256"],
            "restore_sha256": hashes[1] if b1 is not None else None,
            "activity_sha256": hashes[2] if b1 is not None else None,
            "post_source_sha256": hashes[2] if b1 is None else None}
        if restoration is not None and (restoration.get("source") != source["history"]
                or restoration.get("prefix_preserved") is not True
                or restoration["restored"] != {**history, "size_bytes": b1, "sha256": hashes[3]}
                or restoration.get("restore_sha256") != hashes[1]):
            raise ValueError("Native restore interval differs from its saved observation")
        try:
            material = _call_files(protocol, {"native-continuation.json": 65_536, **CALL_METADATA_LIMITS})
        except FileNotFoundError:
            return observed
        receipt = json.loads(material["native-continuation.json"])
        request = json.loads(material["request.json"])
        contracts.validate(receipt, {"type": "object", "required": ["result_sha256"], "properties": {
            "result_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}}, "Native continuation receipt")
        contracts.validate(request, {"type": "object"}, "Native continuation request")
        b2 = receipt.get("final_bytes")
        if (receipt.get("schema_version") != 1 or receipt.get("session_id") != source["session_id"]
                or receipt.get("source_seal_sha256") != source["seal_sha256"]
                or not isinstance(request.get("continuation"), dict) or request["continuation"].get("source") != source
                or receipt.get("root_idle") is not True or not receipt.get("receipt_id")
                or type(b1) is not int or type(b2) is not int or not b0 <= b1 < b2 <= MAX_CONTINUATION_HISTORY
                or receipt.get("restored_bytes") != b1
                or receipt.get("files") != {name: hashlib.sha256(raw).hexdigest() for name, raw in material.items()
                                         if name != "native-continuation.json"}):
            raise ValueError("Native continuation lacks its matching input, identity or completed receipt")
        if (history != receipt.get("history") or history["size_bytes"] != b2 or hashes[0] != source["history"]["sha256"]
                or receipt.get("restore_sha256") != hashes[1] or receipt.get("activity_sha256") != hashes[2]):
            raise ValueError("Native continuation history differs from its original prefix or saved intervals")
        return {**observed, "completed": True, "receipt_id": receipt["receipt_id"],
            "receipt_sha256": hashlib.sha256(material["native-continuation.json"]).hexdigest(),
            "result_sha256": receipt["result_sha256"], "root_idle": True}

    def archived_history(self, protocol: Path, *, cwd: Path, offset: int,
                         limit: int, revision: str | None) -> dict:
        return native_history_page(protocol, cwd=cwd, offset=offset, limit=limit, revision=revision)


class CommandBackend(AgentBackend):
    authentication = "external"
    guidance = ("Verify the configured command's credentials and protocol separately; doctor does not execute arbitrary argv.",)

    def validate_binding(self, role: str, *, formal: bool = False) -> None:
        super().validate_binding(role, formal=formal)
        if ("protocol" in self.binding and not set(components.ROLE_CAPABILITIES[role]) <=
                set(self.binding.get("capabilities", []))):
            raise ValueError(f"Command lacks capabilities for {role}: {components.ROLE_CAPABILITIES[role]}")
        if formal and self.binding.get("protocol") != "stage-json-v1":
            raise ValueError("Formal stages require command protocol stage-json-v1 and capabilities")

    def executable(self) -> str:
        return self.binding["argv"][0]

    def command(self, request: Invocation) -> tuple[list[str], str]:
        stdin = request.prompt
        if self.binding.get("protocol") == "stage-json-v1":
            stdin = json.dumps({"schema_version": 1, "role": request.role, "prompt": request.prompt,
                                "result_schema": request.schema}, ensure_ascii=False)
        return self.binding["argv"], stdin


_BACKENDS = {"codex": CodexBackend, "claude-code": ClaudeCodeBackend,
             "mini-swe-agent": MiniSweBackend, "deepseek-harness": DeepSeekHarnessBackend, "command": CommandBackend}


def for_binding(binding: dict, configurations: dict | None = None) -> AgentBackend:
    implementation = components.COMPONENTS[binding["tool"]]["implementation"]
    return _BACKENDS[implementation](binding, (configurations or {}).get(implementation, {}))
