"""Agent capabilities and native invocations, independent of workflow templates."""

import hashlib
import json
from pathlib import Path

from . import agent_backends, components, contracts, processes
from .components import CHOICES, GENERAL_CAPABILITIES, ROLE_CAPABILITIES, TOOL_CAPABILITIES


def binding_for(project: dict, role: str) -> dict:
    if role not in ROLE_CAPABILITIES:
        raise ValueError(f"Unknown agent role: {role}")
    return components.resolve_binding(project, role)["binding"]


def validate_binding(role: str, binding: dict, *, formal: bool = False) -> None:
    tool = binding.get("tool")
    if tool not in CHOICES[role]:
        raise ValueError(f"Agent {tool!r} does not support role {role}; choices: {CHOICES[role]}")
    agent_backends.for_binding(binding).validate_binding(role, formal=formal)


def executable(binding: dict) -> str:
    return agent_backends.for_binding(binding).executable()


def available(binding: dict, cwd: Path) -> bool:
    return agent_backends.for_binding(binding).available(cwd)


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
           codex_options: list[str] | None = None, codex_bin: str = "codex", supervised: bool = False,
           codex_config: str | Path | None = None, mode: str = "native", task_mcp: dict | None = None) -> dict:
    """A successful process is not evidence acceptance; structured consumers validate separately."""
    validate_binding(role, binding, formal=bool(schema))
    backend = agent_backends.for_binding(binding, {"codex": {
        "arguments": codex_options, "executable": codex_bin, "config": codex_config}})
    backend.check_invocation()
    backend.check_mode(mode)
    if (mode in ("task-mcp", "workspace-task-mcp")) != (task_mcp is not None):
        raise ValueError("Task MCP mode requires its explicit per-call server configuration")
    protocol = output.with_name(output.name + ".protocol")
    protocol.mkdir(parents=True, exist_ok=False, mode=0o700)
    (protocol / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    if schema:
        (protocol / "schema.json").write_text(json.dumps(schema), encoding="utf-8", newline="\n")
    request = agent_backends.Invocation(role, prompt, cwd, protocol, timeout, schema, mode, task_mcp)
    argv, stdin = backend.command(request)
    document = processes.run(argv, cwd, output, timeout, stdin, env, supervised=supervised,
                             command_record=protocol / "command.json" if mode != "native" else None)
    if document["status"] == "succeeded" and schema:
        try:
            result = backend.read_result(output, request)
            validate_result(result, schema)
            content = json.dumps(result, ensure_ascii=False, sort_keys=True).encode()
            (output / "result.json").write_bytes(content)
            document.update(result=str(output / "result.json"), result_sha256=hashlib.sha256(content).hexdigest())
        except (OSError, ValueError, TypeError, AttributeError, KeyError, RecursionError) as error:
            document.update(status="failed", error=f"Invalid structured agent result: {error}")
    return document
