"""Native Agent adapters; the local mapping selects execution, not public schemas."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
import uuid
from urllib.parse import unquote

from ergora.agents import native_sources
from ergora.configuration import catalog as components
from ergora.configuration import validation as contracts
from ergora.definitions.bundles import parse_json
from ergora.runtime import processes
from ergora.data.drivers.deepseek import native_history_page
from ergora._paths import DATA_ROOT


def _events(output: Path):
    with (output / "stdout.txt").open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def _headless_turn(events: Iterable[object], event_key: str, opening_name: str, terminal_name: str) -> tuple[dict, dict]:
    opening = None
    terminal = None
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Headless output contains an invalid event")
        kind = event.get(event_key)
        if kind == opening_name:
            if opening is not None or terminal is not None:
                raise ValueError("Headless output contains more than one invocation")
            opening = event
        elif kind == terminal_name:
            if opening is None or terminal is not None:
                raise ValueError("Headless output contains an unexpected terminal event")
            terminal = event
    if opening is None or terminal is None:
        raise ValueError("Headless output has no complete invocation and terminal event")
    return opening, terminal


def _check_headless_cwd(observed: object, request_cwd: Path) -> None:
    if not isinstance(observed, str) or Path(observed) != request_cwd.resolve():
        raise ValueError("Headless output does not report the original working directory")


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
    session: dict | None = None


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

    def validate_native_completion(self, output: Path, request: Invocation) -> None:
        """Check any backend-specific completion evidence for a plain invocation."""

    def native_usage(self, protocol: Path, mode: str, *, expected_sha256: str | None = None) -> dict | None:
        """Observe supported usage from the original invocation artifacts."""
        return None

    def archived_history(self, protocol: Path, *, cwd: Path, offset: int,
                         limit: int, revision: str | None) -> dict:
        """Observe saved native bytes without starting an interpreter or SDK."""
        return {"available": False, "reason": "This backend has no native archive reader"}

    def session_configuration(self, cwd: Path) -> dict:
        raise ValueError(f"{self.binding['tool']} does not support persistent native sessions")

    def validate_session_configuration(self, configuration: dict, cwd: Path, *, verify_executable: bool = True) -> None:
        raise ValueError(f"{self.binding['tool']} does not support persistent native sessions")

    def session_result(self, output: Path, request: Invocation, *, completed: bool = True) -> dict:
        raise ValueError(f"{self.binding['tool']} does not support persistent native sessions")

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

    def check_mode(self, mode: str) -> None:
        super().check_mode(mode)
        if mode != 'native':
            self._options(mode)

    def _options(self, mode: str, task_mcp: dict | None = None) -> list[str]:
        """Parse the same inference options for model-free admission and command construction."""
        options = list(self.options.get("arguments") or [])
        config = {}
        if self.options.get("config") is not None:
            options += ["--ignore-user-config", "--ignore-rules", "--disable", "plugins", "--disable", "apps"]
            config = (json.loads(json.dumps(self.options['parsed_config'])) if 'parsed_config' in self.options
                      else tomllib.loads(Path(self.options["config"]).read_text(encoding="utf-8")))
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

        if "reasoning_effort" in self.binding:
            config["model_reasoning_effort"] = self.binding["reasoning_effort"]

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

    @staticmethod
    def _output_schema(schema: dict) -> dict:
        """Conjoin the demonstrated array-ref bound without changing the canonical contract."""
        scope_keys = {'$id', '$anchor', '$dynamicAnchor', '$dynamicRef', '$schema', '$vocabulary'}

        def walk(node, pointer='', scoped=False):
            if not isinstance(node, dict):
                return
            scoped = scoped or bool(scope_keys & node.keys())
            yield node, pointer, scoped
            for key in ('$defs', 'properties', 'patternProperties', 'dependentSchemas'):
                if isinstance(node.get(key), dict):
                    for name, child in node[key].items():
                        escaped = name.replace('~', '~0').replace('/', '~1')
                        yield from walk(child, pointer + '/' + key + '/' + escaped, scoped)
            for key in ('allOf', 'anyOf', 'oneOf', 'prefixItems'):
                if isinstance(node.get(key), list):
                    for index, child in enumerate(node[key]):
                        yield from walk(child, pointer + '/' + key + '/' + str(index), scoped)
            for key in ('items', 'contains', 'additionalProperties', 'unevaluatedProperties',
                        'unevaluatedItems', 'propertyNames', 'not', 'if', 'then', 'else', 'contentSchema'):
                yield from walk(node.get(key), pointer + '/' + key, scoped)

        if not any('$ref' in node and 'minItems' in node for node, _, _ in walk(schema)):
            return schema
        converted = deepcopy(schema)
        definitions = schema.get('$defs', {})
        for node, pointer, scoped in list(walk(converted)):
            if '$ref' not in node or 'minItems' not in node:
                continue

            def unsupported(reason):
                raise ValueError(f"Codex schema conversion unsupported at {pointer or '/'}: "
                                 f"$ref={node['$ref']!r}, keywords={sorted(node)}; {reason}")

            def resolve(reference):
                if not isinstance(reference, str) or not reference.startswith('#'):
                    unsupported('only local root $defs references can be expanded')
                try:
                    parts = unquote(reference[1:], errors='strict').split('/')
                except UnicodeDecodeError:
                    unsupported('the local reference has invalid UTF-8 fragment encoding')
                if (len(parts) != 3 or parts[:2] != ['', '$defs']
                        or '~' in parts[2].replace('~0', '').replace('~1', '')):
                    unsupported('only local root $defs references can be expanded')
                name = parts[2].replace('~1', '/').replace('~0', '~')
                if not isinstance(definitions, dict) or not isinstance(definitions.get(name), dict):
                    unsupported('the referenced definition is missing or is not a concrete schema')
                return name, definitions[name]

            if scoped or set(node) != {'$ref', 'minItems'}:
                unsupported('conversion requires a scope-free reference with only a minItems sibling')
            name, target = resolve(node['$ref'])
            if target.get('type') != 'array' or '$ref' in target:
                unsupported('the referenced definition is not a concrete bounded array')
            if any(type(value) is not int or value < 0 for value in (
                    node['minItems'], target.get('minItems', 0), target.get('maxItems'))):
                unsupported('conversion requires nonnegative integer bounds and an explicit maxItems')

            # Copying a reference closure requires unchanged reference scope and
            # no recursive or nested expansion. Pure refs outside it stay native.
            pending, active, checked = [(name, False)], set(), set()
            while pending:
                current, finished = pending.pop()
                if finished:
                    active.remove(current)
                    checked.add(current)
                    continue
                if current in active:
                    unsupported('the replacement reference closure is recursive')
                if current in checked:
                    continue
                active.add(current)
                pending.append((current, True))
                for child, _, child_scoped in walk(definitions[current], scoped=bool(scope_keys & schema.keys())):
                    if child_scoped:
                        unsupported('the replacement reference closure changes schema scope or dialect')
                    if '$ref' in child:
                        if 'minItems' in child:
                            unsupported('the replacement closure itself requires array-reference conversion')
                        child_name, _ = resolve(child['$ref'])
                        pending.append((child_name, False))
            minimum = max(target.get('minItems', 0), node['minItems'])
            node.clear()
            node.update(deepcopy(target))
            node['minItems'] = minimum
        return converted

    def command(self, request: Invocation) -> tuple[list[str], str]:
        if request.mode == "workspace-task-mcp":
            self.composition_policy(request.mode)
        options = (list(request.session['configuration']['arguments']) if request.session is not None
                   else self._options(request.mode, request.task_mcp))
        sandbox = "read-only" if request.mode not in ("native", "workspace-task-mcp") else self.binding.get(
            "sandbox", "read-only" if request.role != "implementer" else "workspace-write")
        sandbox = "danger-full-access" if sandbox == "current-container" else sandbox
        executable = request.session['configuration']['executable'] if request.session is not None else self.executable()
        prefix = request.session['configuration']['prefix_arguments'] if request.session is not None else []
        argv = [executable, *prefix, "exec", *([] if request.session is not None else ["--ephemeral"]),
                "--sandbox", sandbox, "--json", *options]
        if "model" in self.binding:
            argv += ["--model", self.binding["model"]]
        if request.schema:
            schema_path = request.protocol / "schema.json"
            native_schema = self._output_schema(request.schema)
            if native_schema is not request.schema:
                schema_path = request.protocol / "codex-schema.json"
                schema_path.write_text(json.dumps(native_schema), encoding="utf-8", newline="\n")
            argv += ["--output-schema", str(schema_path),
                     "--output-last-message", str(request.protocol / "result.json")]
        elif request.session is not None:
            argv += ["--output-last-message", str(request.protocol / "result.txt")]
        if request.session is not None and request.session.get('native_id') is not None:
            argv += ['resume', request.session['native_id']]
        return [*argv, "-"], request.prompt

    def session_configuration(self, cwd: Path) -> dict:
        if sys.platform != 'linux':
            raise ValueError('Persistent native sessions require Linux/WSL2 process ownership')
        source = Path(self.options.get('config') or Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'config.toml')
        if not source.is_file():
            raise ValueError('Persistent Codex sessions require an explicit or existing trusted Codex configuration')
        raw = source.read_bytes()
        config = tomllib.loads(raw.decode('utf-8'))
        # The existing native option owner accepts inference settings. Persistent
        # sessions cannot retain literal credentials or ambient tool/profile state.
        allowed = {'model', 'model_provider', 'model_reasoning_effort', 'service_tier', 'model_providers',
                   'approval_policy', 'sandbox_mode', 'sandbox_workspace_write'}
        unsupported = set(config) - allowed
        if unsupported:
            raise ValueError('Persistent Codex configuration has unsupported settings: ' + ', '.join(sorted(unsupported)))
        for provider in config.get('model_providers', {}).values():
            if not isinstance(provider, dict) or set(provider) - {
                    'name', 'base_url', 'env_key', 'wire_api', 'requires_openai_auth', 'env_http_headers'}:
                raise ValueError('Persistent Codex provider settings support credential environment references only')
            from urllib.parse import urlsplit
            url = urlsplit(provider.get('base_url', ''))
            if url.username or url.password or url.query or url.fragment:
                raise ValueError('Persistent Codex provider URL cannot contain credentials, query or fragment')
            for name in [provider.get('env_key'), *provider.get('env_http_headers', {}).values()]:
                if name is not None and (not isinstance(name, str) or not name.isidentifier()):
                    raise ValueError('Codex credentials require environment variable names')
        effective = dict(self.binding)
        for key in ('model', 'model_reasoning_effort'):
            target = 'reasoning_effort' if key == 'model_reasoning_effort' else key
            if target not in effective and key in config:
                effective[target] = config[key]
        if not effective.get('model') or not effective.get('reasoning_effort'):
            raise ValueError('Persistent Codex sessions require an explicit model and reasoning effort')
        adapter = CodexBackend(effective, {**self.options, 'config': str(source), 'parsed_config': config})
        arguments = adapter._options('native')
        if source.read_bytes() != raw:
            raise ValueError('Codex configuration changed while freezing options')
        executable = str(Path(processes.resolve_program(self.executable(), cwd)).resolve())
        selected_files = [Path(executable)]
        if Path(executable).name == 'codex.js':
            import platform
            package = Path(executable).parent.parent
            target = {'x86_64': ('linux-x64', 'x86_64-unknown-linux-musl'),
                      'aarch64': ('linux-arm64', 'aarch64-unknown-linux-musl')}.get(platform.machine())
            if target is None:
                raise ValueError('Cannot establish native Codex binary for this architecture')
            candidates = [package / 'node_modules' / '@openai' / ('codex-' + target[0]) / 'vendor' / target[1] / 'bin' / 'codex',
                          package / 'vendor' / target[1] / 'bin' / 'codex']
            binary = next((candidate for candidate in candidates if candidate.is_file()), None)
            if binary is None:
                raise ValueError('Cannot establish the selected npm Codex native binary')
            selected_files += [package / 'package.json', binary]
        fingerprints = {}
        for path in selected_files:
            with path.open('rb') as stream:
                fingerprints[str(path.resolve())] = hashlib.file_digest(stream, 'sha256').hexdigest()
        version = subprocess.run([executable, '--version'], cwd=cwd, capture_output=True, text=True, timeout=5)
        if version.returncode or not version.stdout.startswith('codex-cli '):
            raise ValueError('Cannot establish selected Codex CLI version')
        return {'arguments': arguments, 'prefix_arguments': ['--no-daemon'],
                'binding': effective, 'executable': executable,
                'executable_files': fingerprints, 'version': version.stdout.strip(),
                'sandbox': effective.get('sandbox', 'workspace-write' if self.options.get('role') == 'implementer' else 'read-only'),
                'source_sha256': hashlib.sha256(raw).hexdigest()}

    def validate_session_configuration(self, configuration: dict, cwd: Path, *, verify_executable: bool = True) -> None:
        if self.binding != configuration['binding']:
            raise ValueError('Session binding differs from its frozen native configuration')
        if verify_executable:
            for filename, expected in configuration['executable_files'].items():
                with Path(filename).open('rb') as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
                        raise ValueError('Selected native executable changed; start a new session')
        self.check_mode('native')

    def session_result(self, output: Path, request: Invocation, *, completed: bool = True) -> dict:
        thread, terminal = [], []
        for event in _events(output):
            if event.get('type') == 'thread.started':
                thread.append(str(uuid.UUID(event['thread_id'])))
            if event.get('type') in ('turn.completed', 'turn.failed', 'error'):
                terminal.append(event)
        if not completed and not thread and request.session.get('native_id') is not None:
            return {'id': request.session['native_id'], 'completed': False, 'observed_in_turn': False}
        if len(thread) != 1 or (completed and (len(terminal) != 1 or terminal[0]['type'] != 'turn.completed')):
            raise ValueError('Native session lacks one matching thread and completed turn')
        if request.session.get('native_id') not in (None, thread[0]):
            raise ValueError('Native resume returned a different session UUID')
        return {'id': thread[0], 'completed': len(terminal) == 1 and terminal[0]['type'] == 'turn.completed',
                'observed_in_turn': True, 'usage': terminal[0].get('usage') if terminal else None}

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
        if "effort" in self.binding:
            argv += ["--effort", self.binding["effort"]]
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
        return [self.executable(), str(DATA_ROOT / "drivers/mini.py"), str(path)], ""

    def probe_commands(self, cwd: Path) -> list[tuple[str, list[str]]]:
        return [("version", [self.executable(), "-c",
                "from importlib.metadata import version; print(version('mini-swe-agent'))"])]


class DeepSeekHarnessBackend(AgentBackend):
    """Optional SDK environment, admitted only for fixed-resource read-only calls."""

    invocation_modes = ("text-only", "task-mcp")
    guidance = ("Install the pinned DeepSeek SDK/runtime in a separate Python environment and select its interpreter.",
                "Configure the OpenAI-compatible base_url, model and api_key_env; native/workspace calls are unsupported.")

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
                             str(DATA_ROOT / "drivers/deepseek.py"), "--check"])]

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
        path = request.protocol / "request.json"
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8", newline="\n")
        return [self.executable(), "-I", str(DATA_ROOT / "drivers/deepseek.py"), str(path)], ""

    def read_result(self, output: Path, request: Invocation) -> dict:
        native = json.loads((request.protocol / "native-result.json").read_text(encoding="utf-8"))
        if native["finish_reason"] != "completed":
            raise ValueError("DeepSeek Harness input did not complete")
        if any(event.get("type") == "tool/result" and event["data"]["message"].get("isError")
               for event in native["events"]):
            raise ValueError("DeepSeek Harness reported a tool error; see native-events.jsonl")
        return json.loads(native["final_response"])

    def native_usage(self, protocol: Path, mode: str, *, expected_sha256: str | None = None) -> dict | None:
        if mode != "text-only" or self.binding.get("api", "openai-completions") != "openai-completions":
            return None
        raw = native_sources.artifact(protocol, "native-result.json", 8_388_608)
        digest = hashlib.sha256(raw).hexdigest()
        if expected_sha256 is not None and digest != expected_sha256:
            raise native_sources.ArtifactIdentityError("DeepSeek Harness native result differs from its recorded SHA256")
        try:
            native = parse_json(raw.decode("utf-8"), "DeepSeek Harness native result", finite=True, bounded=True)
        except (ValueError, RecursionError):
            return {"available": False, "state": "invalid", "source_sha256": digest,
                    "error": "Malformed DeepSeek Harness native result JSON"}
        if (not isinstance(native, dict) or not isinstance(native.get("finish_reason"), str)
                or not isinstance(native.get("events"), list)):
            raise ValueError("Invalid DeepSeek Harness native result for usage observation")
        if native["finish_reason"] != "completed":
            return {"available": False, "state": "incomplete", "source_sha256": digest}
        assistant_events = [(index, event) for index, event in enumerate(native["events"])
                            if isinstance(event, dict) and event.get("type") == "assistant/message"]
        if len(assistant_events) != 1 or not isinstance(assistant_events[0][1].get("data"), dict):
            raise ValueError("DeepSeek Harness usage requires one completed native assistant message")
        index, event = assistant_events[0]
        source = {"source_sha256": digest, "event_index": index}
        usage = event["data"].get("usage")
        if usage is None:
            return {"available": False, "state": "unreported", **source}
        required = ("inputTokens", "outputTokens", "totalTokens")
        optional = ("cacheReadTokens", "cacheWriteTokens")
        if not isinstance(usage, dict) or not set(required) <= usage.keys():
            raise ValueError("DeepSeek Harness native usage lacks required token counters")
        tokens = {field: usage[field] for field in (*required, *optional) if field in usage}
        if any(type(value) is not int or value < 0 for value in tokens.values()):
            raise ValueError("DeepSeek Harness native usage has invalid token counters")
        if not any(tokens.values()):
            # This SDK emits the same all-zero counters when the provider omitted usage.
            return {"available": False, "state": "zero_or_unreported", **source}
        return {"available": True, "state": "observed", **source, "sdk_tokens": tokens}

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


class _HeadlessCliBackend(AgentBackend):
    default_executable: str

    def executable(self) -> str:
        return self.binding.get("executable", self.default_executable)

    def check_invocation(self) -> None:
        if sys.platform != "linux":
            raise ValueError(f"{self.binding['tool']} native invocation requires Linux or WSL2")

    def probe_commands(self, cwd: Path) -> list[tuple[str, list[str]]]:
        return [("version", [processes.resolve_program(self.executable(), cwd), "--version"])]


class AntigravityBackend(_HeadlessCliBackend):
    default_executable = "agy"
    guidance = ("Sign in interactively with agy before a headless call.",
                "The native sandbox is requested and requires host namespace support. Check actual edits and test results.")

    def command(self, request: Invocation) -> tuple[list[str], str]:
        argv = [self.executable(), "--input-format", "stream-json", "--output-format", "stream-json", "--sandbox"]
        for field in ("model", "effort"):
            if field in self.binding:
                argv.extend((f"--{field}", self.binding[field]))
        if request.schema is not None:
            argv.extend(("--json-schema", json.dumps(request.schema)))
        message = {"event": "user", "message": {"content": request.prompt}}
        return argv, json.dumps(message, ensure_ascii=False) + "\n"

    @staticmethod
    def _terminal(output: Path, request: Invocation) -> dict:
        opening, terminal = _headless_turn(_events(output), "event", "init", "result")
        init = opening.get("init")
        _check_headless_cwd(init.get("cwd") if isinstance(init, dict) else None, request.cwd)
        result = terminal.get("result")
        identity = opening.get("conversation_id")
        if not isinstance(identity, str) or not identity or not isinstance(result, dict) or result.get("conversation_id") != identity:
            raise ValueError("Antigravity result belongs to an unknown conversation")
        if result.get("status") != "SUCCESS":
            raise ValueError("Antigravity did not report a successful turn; see native stdout and stderr")
        turns = result.get("num_turns")
        if type(turns) is not int or turns != 1:
            raise ValueError("Antigravity did not report exactly one user turn")
        return result

    def read_result(self, output: Path, request: Invocation) -> dict:
        return self._terminal(output, request).get("structured_output")

    def validate_native_completion(self, output: Path, request: Invocation) -> None:
        response = self._terminal(output, request).get("response")
        if not isinstance(response, str) or not response.strip():
            raise ValueError("Antigravity final response is empty")


class DeepSeekCliBackend(_HeadlessCliBackend):
    default_executable = "dsh"
    guidance = ("Configure the default model and headless credentials in DeepSeek Harness.",
                "The headless profile runs with workspace-write and uses the native approval policy.")

    def command(self, request: Invocation) -> tuple[list[str], str]:
        prompt = request.prompt
        if request.schema is not None:
            prompt += ("\n\nReturn only the final JSON object, without Markdown, matching this JSON Schema:\n"
                       + json.dumps(request.schema, ensure_ascii=False))
        # User profile layers can replace the runner's entire config row. Restore the original
        # startup links in the final CLI overlay, keeping the other deployment rows selected.
        overlay = request.protocol.resolve() / "dsh-headless.patch.yml"
        overlay.write_text(
            "- id: headless-runner\n"
            "  inject: [headlessStartup]\n"
            "  config:\n"
            "    task: !!js ctx.headlessStartup.task\n"
            "    sessionId: !!js ctx.headlessStartup.sessionId\n"
            "    json: !!js ctx.headlessStartup.json\n",
            encoding="utf-8", newline="\n",
        )
        return [self.executable(), "--profile", "headless", "--patch", str(overlay),
                "--permission-mode", "workspace-write", "--json", "-"], prompt

    @staticmethod
    def _stream(output: Path) -> Iterator[object]:
        session_opened = False
        observed_turns: set[int] = set()
        active_turn = None
        last_reason = None
        finished = False
        for event in _events(output):
            if not isinstance(event, dict):
                raise ValueError("Headless output contains an invalid event")
            kind = event.get("type")
            if kind == "error":
                raise ValueError("DeepSeek CLI reported a fatal error; see native stdout and stderr")
            if finished:
                raise ValueError("DeepSeek CLI reported data after the final event")
            if kind == "session":
                session_opened = True
            elif kind == "status":
                if not session_opened:
                    raise ValueError("DeepSeek CLI reported status before opening the native session")
                phase, turn = event.get("phase"), event.get("turn")
                if phase == "turn_start":
                    if active_turn is not None or type(turn) is not int or turn in observed_turns:
                        raise ValueError("DeepSeek CLI reported an unexpected turn start")
                    observed_turns.add(turn)
                    active_turn = turn
                elif phase == "turn_end":
                    if active_turn is None or type(turn) is not int or turn != active_turn:
                        raise ValueError("DeepSeek CLI reported an unexpected turn end")
                    active_turn = None
                    last_reason = event.get("reason")
            elif kind == "final":
                if active_turn is not None or not isinstance(last_reason, dict) or event.get("reason") != last_reason:
                    raise ValueError("DeepSeek CLI final reason disagrees with the last completed native turn")
                finished = True
            yield event

    @staticmethod
    def _answer(output: Path, request: Invocation) -> str:
        opening, terminal = _headless_turn(DeepSeekCliBackend._stream(output), "type", "session", "final")
        _check_headless_cwd(opening.get("cwd"), request.cwd)
        identity = opening.get("sessionId")
        if not isinstance(identity, str) or not identity or terminal.get("sessionId") != identity:
            raise ValueError("DeepSeek CLI result belongs to an unknown session")
        reason = terminal.get("reason")
        if not isinstance(reason, dict) or reason.get("kind") != "completed":
            raise ValueError("DeepSeek CLI did not report a completed turn; see native stdout and stderr")
        answer = terminal.get("text")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("DeepSeek CLI final response is empty")
        return answer

    def read_result(self, output: Path, request: Invocation) -> dict:
        return parse_json(self._answer(output, request), "DeepSeek CLI final response", finite=True, bounded=True)

    def validate_native_completion(self, output: Path, request: Invocation) -> None:
        self._answer(output, request)


_BACKENDS = {"codex": CodexBackend, "claude-code": ClaudeCodeBackend,
             "mini-swe-agent": MiniSweBackend, "deepseek-harness": DeepSeekHarnessBackend, "command": CommandBackend,
             "antigravity-cli": AntigravityBackend, "deepseek-cli": DeepSeekCliBackend}


def supports_mode(tool: str, mode: str) -> bool:
    """Read the registered backend's mode declaration without constructing it."""
    implementation = components.COMPONENTS[tool]["implementation"]
    return mode in _BACKENDS[implementation].invocation_modes


def for_binding(binding: dict, configurations: dict | None = None) -> AgentBackend:
    implementation = components.COMPONENTS[binding["tool"]]["implementation"]
    return _BACKENDS[implementation](binding, (configurations or {}).get(implementation, {}))
