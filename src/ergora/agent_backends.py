"""Native Agent adapters; the local mapping selects execution, not public schemas."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
import tomllib

from . import components, contracts, processes


@dataclass(frozen=True)
class Invocation:
    role: str
    prompt: str
    cwd: Path
    protocol: Path
    timeout: int
    schema: dict | None


class AgentBackend(ABC):
    authentication = "not_checked"
    guidance: tuple[str, ...] = ()

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

    @abstractmethod
    def command(self, request: Invocation) -> tuple[list[str], str]:
        """Prepare the native command and stdin in an existing protocol directory."""

    def read_result(self, output: Path, protocol: Path) -> dict:
        return json.loads((output / "stdout.txt").read_text(encoding="utf-8"))

    def diagnostics(self) -> dict:
        return {"authentication": self.authentication, "remediation": [
            "Run an explicitly budgeted agent invocation to verify the selected model and task; doctor never calls a model.",
            *self.guidance]}

    def probe_commands(self, cwd: Path) -> list[tuple[str, list[str]]]:
        """Only fixed local diagnostics; arbitrary bindings never execute here."""
        return []


class CodexBackend(AgentBackend):
    guidance = ("Use codex login, then tools doctor PROJECT --probe; stored credentials do not verify account access or quota.",)

    def executable(self) -> str:
        return "codex"

    def check_invocation(self) -> None:
        if sys.platform != "linux" and self.binding.get("sandbox") == "current-container":
            raise ValueError("current-container requires the trusted Linux container configuration; use the native Codex sandbox on Windows")

    def command(self, request: Invocation) -> tuple[list[str], str]:
        options = list(self.options.get("arguments") or [])
        if self.options.get("config") is not None:
            options += ["--ignore-user-config", "--ignore-rules", "--disable", "plugins", "--disable", "apps"]
            config = tomllib.loads(Path(self.options["config"]).read_text(encoding="utf-8"))

            def add(table, prefix=""):
                for key, value in table.items():
                    name = prefix + key
                    if isinstance(value, dict):
                        add(value, name + ".")
                    elif name != "approval_policy" and not name.startswith("sandbox_"):
                        options.extend(["-c", name + "=" + json.dumps(value)])

            add(config)
        sandbox = self.binding.get("sandbox", "read-only" if request.role != "implementer" else "workspace-write")
        sandbox = "danger-full-access" if sandbox == "current-container" else sandbox
        argv = [self.options.get("executable", "codex"), "exec", "--ephemeral", "--sandbox", sandbox, "--json", *options]
        if "model" in self.binding:
            argv += ["--model", self.binding["model"]]
        if request.schema:
            argv += ["--output-schema", str(request.protocol / "schema.json"),
                     "--output-last-message", str(request.protocol / "result.json")]
        return [*argv, "-"], request.prompt

    def read_result(self, output: Path, protocol: Path) -> dict:
        return json.loads((protocol / "result.json").read_text(encoding="utf-8"))

    def probe_commands(self, cwd: Path) -> list[tuple[str, list[str]]]:
        program = processes.resolve_program(self.executable(), cwd)
        return [("version", [program, "--version"]), ("authentication", [program, "login", "status"])]


class ClaudeCodeBackend(AgentBackend):
    guidance = ("Use claude auth login; authentication is not checked by this driver.",)

    def executable(self) -> str:
        return "claude"

    def command(self, request: Invocation) -> tuple[list[str], str]:
        argv = ["claude", "--print", "--output-format", "json", "--no-session-persistence"]
        if request.role != "implementer":
            argv += ["--tools", "Read,Grep,Glob", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
        if "model" in self.binding:
            argv += ["--model", self.binding["model"]]
        if request.schema:
            argv += ["--json-schema", json.dumps(request.schema)]
        return argv, request.prompt

    def read_result(self, output: Path, protocol: Path) -> dict:
        result = super().read_result(output, protocol)
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
