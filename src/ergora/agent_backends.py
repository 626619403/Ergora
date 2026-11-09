"""Native Agent adapters; the local mapping selects execution, not public schemas."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
import tomllib

from . import components, contracts, processes


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
        return "codex"

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
        argv = [self.options.get("executable", "codex"), "exec", "--ephemeral", "--sandbox", sandbox, "--json", *options]
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
             "mini-swe-agent": MiniSweBackend, "command": CommandBackend}


def for_binding(binding: dict, configurations: dict | None = None) -> AgentBackend:
    implementation = components.COMPONENTS[binding["tool"]]["implementation"]
    return _BACKENDS[implementation](binding, (configurations or {}).get(implementation, {}))
