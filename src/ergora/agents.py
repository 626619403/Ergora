"""Agent capabilities and native invocations, independent of workflow templates."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from . import components, contracts, processes
from .components import CHOICES, GENERAL_CAPABILITIES, ROLE_CAPABILITIES, TOOL_CAPABILITIES


def binding_for(project: dict, role: str) -> dict:
    if role not in ROLE_CAPABILITIES:
        raise ValueError(f"Unknown agent role: {role}")
    return project["bindings"].get(role, project["bindings"]["implementer"])


def validate_binding(role: str, binding: dict) -> None:
    tool = binding.get("tool")
    if tool not in CHOICES[role]:
        raise ValueError(f"Agent {tool!r} does not support role {role}; choices: {CHOICES[role]}")
    contracts.validate(binding, components.COMPONENTS[tool]["configuration"], f"{role} binding")
    implementation = components.COMPONENTS[tool]["implementation"]
    if (implementation == "command" and "protocol" in binding and
            not set(ROLE_CAPABILITIES[role]) <= set(binding.get("capabilities", []))):
        raise ValueError(f"Command lacks capabilities for {role}: {ROLE_CAPABILITIES[role]}")


def executable(binding: dict) -> str:
    tool = components.COMPONENTS[binding["tool"]]["implementation"]
    if tool == "command":
        return binding["argv"][0]
    return {"codex": "codex", "claude-code": "claude", "mini-swe-agent": binding.get("python", sys.executable)}[tool]


def available(binding: dict, cwd: Path) -> bool:
    implementation = components.COMPONENTS[binding["tool"]]["implementation"]
    if implementation == "mini-swe-agent" and sys.platform != "linux":
        return False
    try:
        program = processes.resolve_program(executable(binding), cwd)
    except (OSError, ValueError):
        return False
    if implementation == "mini-swe-agent":
        try:
            result = subprocess.run([program, "-c", "import importlib.util;raise SystemExit(0 if importlib.util.find_spec('minisweagent') else 1)"],
                                    cwd=cwd, capture_output=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0
    return True


def result_schema(names: list[str], review: bool = False) -> dict:
    properties = {"summary": {"type": "string", "pattern": r"\S"}, "artifacts": {"type": "object", "properties":
                  {name: {"type": "string", "pattern": r"\S"} for name in names}, "required": names, "additionalProperties": False}}
    if review:
        properties["decision"] = {"type": "string", "enum": ["approve", "request-changes"]}
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def validate_result(result: dict, schema: dict) -> dict:
    contracts.validate(result, schema, "Agent result")
    return result


def invoke(binding: dict, role: str, prompt: str, cwd: Path, output: Path, timeout: int,
           schema: dict | None = None, *, env: dict | None = None,
           codex_options: list[str] | None = None, codex_bin: str = "codex", supervised: bool = False) -> dict:
    """A successful process is not evidence acceptance; structured consumers validate separately."""
    validate_binding(role, binding)
    tool = components.COMPONENTS[binding["tool"]]["implementation"]
    if tool == "mini-swe-agent" and sys.platform != "linux":
        raise ValueError("This mini-swe-agent driver requires Linux/bash; use WSL2")
    if sys.platform != "linux" and tool == "codex" and binding.get("sandbox") == "current-container":
        raise ValueError("current-container requires the trusted Linux container configuration; use the native Codex sandbox on Windows")
    if schema and tool == "command" and binding.get("protocol") != "stage-json-v1":
        raise ValueError("Formal stages require command protocol stage-json-v1 and capabilities")
    protocol = output.with_name(output.name + ".protocol")
    protocol.mkdir(parents=True, exist_ok=False, mode=0o700)
    (protocol / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    if schema:
        (protocol / "schema.json").write_text(json.dumps(schema), encoding="utf-8", newline="\n")
    stdin = prompt
    if tool == "codex":
        sandbox = binding.get("sandbox", "read-only" if role != "implementer" else "workspace-write")
        sandbox = "danger-full-access" if sandbox == "current-container" else sandbox
        argv = [codex_bin, "exec", "--ephemeral", "--sandbox", sandbox, "--json", *(codex_options or [])]
        if "model" in binding:
            argv += ["--model", binding["model"]]
        if schema:
            argv += ["--output-schema", str(protocol / "schema.json"), "--output-last-message", str(protocol / "result.json")]
        argv += ["-"]
    elif tool == "claude-code":
        argv = ["claude", "--print", "--output-format", "json", "--no-session-persistence"]
        if role != "implementer":
            argv += ["--tools", "Read,Grep,Glob", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
        if "model" in binding:
            argv += ["--model", binding["model"]]
        if schema:
            argv += ["--json-schema", json.dumps(schema)]
    elif tool == "mini-swe-agent":
        request = {"binding": binding, "prompt": prompt, "cwd": str(cwd),
                   "timeout": timeout, "trajectory": str(protocol / "trajectory.json")}
        (protocol / "request.json").write_text(json.dumps(request), encoding="utf-8", newline="\n")
        argv = [binding.get("python", sys.executable), str(Path(__file__).parent / "data/drivers/mini.py"), str(protocol / "request.json")]
        stdin = ""
    else:
        argv = binding["argv"]
        if binding.get("protocol") == "stage-json-v1":
            stdin = json.dumps({"schema_version": 1, "role": role, "prompt": prompt, "result_schema": schema}, ensure_ascii=False)
    document = processes.run(argv, cwd, output, timeout, stdin, env, supervised=supervised)
    if document["status"] == "succeeded" and schema:
        try:
            if tool == "codex":
                result = json.loads((protocol / "result.json").read_text(encoding="utf-8"))
            else:
                result = json.loads((output / "stdout.txt").read_text(encoding="utf-8"))
                if tool == "claude-code":
                    if result.get("is_error"):
                        raise ValueError("Claude Code reported an error")
                    result = result.get("structured_output")
            validate_result(result, schema)
            content = json.dumps(result, ensure_ascii=False, sort_keys=True).encode()
            (output / "result.json").write_bytes(content)
            document.update(result=str(output / "result.json"), result_sha256=hashlib.sha256(content).hexdigest())
        except (OSError, ValueError, TypeError, AttributeError) as error:
            document.update(status="failed", error=f"Invalid structured agent result: {error}")
    return document
