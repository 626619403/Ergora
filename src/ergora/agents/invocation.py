"""Agent capabilities and native invocations, independent of workflow templates."""

import hashlib
import json
from pathlib import Path

import ergora.agents.backends as agent_backends
from ergora.configuration import catalog as components
from ergora.configuration import validation as contracts
from ergora.runtime import processes
from ergora.configuration.catalog import CHOICES, GENERAL_CAPABILITIES, ROLE_CAPABILITIES, TOOL_CAPABILITIES


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
           codex_config: str | Path | None = None, mode: str = "native", task_mcp: dict | None = None,
           lock_fd: int | None = None,
           session: dict | None = None, stop_requested=None, record_lifecycle: bool = False,
           deadline: float | None = None, on_start=None, observe_direct_child_start: bool = False) -> dict:
    """A successful process is not evidence acceptance; structured consumers validate separately."""
    validate_binding(role, binding, formal=bool(schema))
    backend = agent_backends.for_binding(binding, {"codex": {
        "arguments": codex_options, "executable": codex_bin, "config": codex_config}})
    if session is None:
        backend.check_invocation()
    else:
        backend.validate_session_configuration(session['configuration'], cwd)
    backend.check_mode(mode)
    if (mode in ("task-mcp", "workspace-task-mcp")) != (task_mcp is not None):
        raise ValueError("Task MCP mode requires its explicit per-call server configuration")
    protocol = output.with_name(output.name + ".protocol")
    protocol.mkdir(parents=True, exist_ok=False, mode=0o700)
    (protocol / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    if schema:
        (protocol / "schema.json").write_text(json.dumps(schema), encoding="utf-8", newline="\n")
    request = agent_backends.Invocation(role, prompt, cwd, protocol, timeout, schema, mode, task_mcp, session)
    argv, stdin = backend.command(request)
    if stop_requested is not None and stop_requested():
        return {'status': 'cancelled', 'returncode': None, 'error': 'Parent stopped before native spawn'}
    document = processes.run(argv, cwd, output, timeout, stdin, env, supervised=supervised,
                             command_record=protocol / "command.json" if mode != "native" or session is not None else None,
                             **({'deadline': deadline} if deadline is not None else {}),
                             **({'on_start': on_start} if on_start is not None else {}),
                             **({'observe_direct_child_start': True} if observe_direct_child_start else {}),
                             **({"stop_requested": stop_requested} if stop_requested is not None else {}),
                             **({'record_lifecycle': True} if record_lifecycle else {}),
                             **({"lock_fd": lock_fd} if lock_fd is not None else {}))
    if document["status"] == "succeeded" and schema:
        try:
            if stop_requested is not None and stop_requested():
                raise ValueError('Parent stopped before structured result synchronization')
            result = backend.read_result(output, request)
            validate_result(result, schema)
            content = json.dumps(result, ensure_ascii=False, sort_keys=True).encode()
            (output / "result.json").write_bytes(content)
            if stop_requested is not None and stop_requested():
                raise ValueError('Parent stopped during structured result synchronization')
            document.update(result=str(output / "result.json"), result_sha256=hashlib.sha256(content).hexdigest())
        except (OSError, ValueError, TypeError, AttributeError, KeyError, RecursionError) as error:
            document.update(status="failed", error=f"Invalid structured agent result: {error}")
    if session is not None:
        try:
            document['native_session'] = backend.session_result(output, request, completed=document['status'] == 'succeeded')
            if document['status'] == 'succeeded' and schema is None:
                raw = (protocol / 'result.txt').read_bytes()
                if not raw.strip() or len(raw) > 8_388_608:
                    raise ValueError('Native session final message is empty or exceeds 8 MiB')
                raw.decode('utf-8')
                (output / 'result.txt').write_bytes(raw)
                document.update(result=str(output / 'result.txt'), result_sha256=hashlib.sha256(raw).hexdigest())
        except (OSError, ValueError, TypeError, KeyError) as error:
            document['native_observation_error'] = str(error)
            if document['status'] == 'succeeded':
                document.update(status='failed', error=f'Invalid native session result: {error}')
    return document
