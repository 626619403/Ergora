"""Agent capabilities and native invocations, independent of workflow templates."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from . import processes


ROLE_CAPABILITIES = {
    "inspector": ["repository-read", "baseline-inspection"],
    "planner": ["repository-read", "plan-write"],
    "implementer": ["scoped-code-write", "test-execution"],
    "reviewer": ["independent-candidate-review"],
    "experiment-planner": ["experiment-design"],
    "performance-analyst": ["performance-analysis"],
    "kernel-tuner": ["kernel-generation"],
}
GENERAL_CAPABILITIES = sorted({cap for caps in ROLE_CAPABILITIES.values() for cap in caps})
TOOL_CAPABILITIES = {
    "codex": GENERAL_CAPABILITIES,
    "claude-code": GENERAL_CAPABILITIES,
    "mini-swe-agent": ROLE_CAPABILITIES["implementer"],
}
CHOICES = {role: [tool for tool, caps in TOOL_CAPABILITIES.items() if set(required) <= set(caps)] + ["command"]
           for role, required in ROLE_CAPABILITIES.items()}


def binding_for(project: dict, role: str) -> dict:
    if role not in ROLE_CAPABILITIES:
        raise ValueError(f"Unknown agent role: {role}")
    return project["bindings"].get(role, project["bindings"]["implementer"])


def validate_binding(role: str, binding: dict) -> None:
    tool = binding.get("tool")
    if tool not in CHOICES[role]:
        raise ValueError(f"Agent {tool!r} does not support role {role}; choices: {CHOICES[role]}")
    allowed = {
        "codex": {"tool", "model", "sandbox"},
        "claude-code": {"tool", "model"},
        "mini-swe-agent": {"tool", "model", "python", "cost_limit", "step_limit"},
        "command": {"tool", "argv", "protocol", "capabilities"},
    }[tool]
    if set(binding) - allowed:
        raise ValueError(f"Unknown agent options: {sorted(set(binding) - allowed)}")
    for field in ("model", "python"):
        if field in binding and (not isinstance(binding[field], str) or not binding[field].strip() or "\0" in binding[field]):
            raise ValueError(f"{field} must be a nonempty string")
    if tool == "codex" and binding.get("sandbox", "workspace-write") not in ("workspace-write", "read-only", "current-container"):
        raise ValueError("Codex sandbox must be read-only, workspace-write or explicitly current-container")
    if tool == "mini-swe-agent":
        if not binding.get("model"):
            raise ValueError("mini-swe-agent requires an explicit provider/model ID")
        if type(binding.get("step_limit", 30)) is not int or not 1 <= binding.get("step_limit", 30) <= 1000:
            raise ValueError("mini-swe-agent step_limit must be 1–1000")
        cost = binding.get("cost_limit", 3.0)
        if type(cost) not in (float, int) or not 0 < cost <= 100:
            raise ValueError("mini-swe-agent cost_limit must be >0 and <=100 (upstream reported USD)")
    if tool == "command":
        argv = binding.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(item, str) or not item or "\0" in item for item in argv):
            raise ValueError("command requires a nonempty argv array")
        if "protocol" in binding and binding["protocol"] != "stage-json-v1":
            raise ValueError("Only stage-json-v1 is supported for structured commands")
        caps = binding.get("capabilities", [])
        if not isinstance(caps, list) or any(cap not in GENERAL_CAPABILITIES for cap in caps):
            raise ValueError("Unknown agent capability")
        if "protocol" in binding and not set(ROLE_CAPABILITIES[role]) <= set(caps):
            raise ValueError(f"Command lacks capabilities for {role}: {ROLE_CAPABILITIES[role]}")


def executable(binding: dict) -> str:
    tool = binding["tool"]
    if tool == "command":
        return binding["argv"][0]
    return {"codex": "codex", "claude-code": "claude", "mini-swe-agent": binding.get("python", sys.executable)}[tool]


def available(binding: dict, cwd: Path) -> bool:
    program = executable(binding)
    if "/" in program and not Path(program).is_absolute():
        program = str(cwd / program)
    if shutil.which(program) is None:
        return False
    if binding["tool"] == "mini-swe-agent":
        try:
            result = subprocess.run([program, "-c", "import importlib.util;raise SystemExit(0 if importlib.util.find_spec('minisweagent') else 1)"],
                                    cwd=cwd, capture_output=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0
    return True


def result_schema(names: list[str], review: bool = False) -> dict:
    properties = {"summary": {"type": "string"}, "artifacts": {"type": "object", "properties":
                  {name: {"type": "string"} for name in names}, "required": names, "additionalProperties": False}}
    if review:
        properties["decision"] = {"type": "string", "enum": ["approve", "request-changes"]}
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def validate_result(result: dict, schema: dict) -> dict:
    if not isinstance(result, dict) or set(result) != set(schema["required"]):
        raise ValueError("Agent result does not match the required stage fields")
    if not isinstance(result["summary"], str) or not result["summary"].strip():
        raise ValueError("Agent omitted the stage summary")
    artifacts = result["artifacts"]
    if not isinstance(artifacts, dict) or set(artifacts) != set(schema["properties"]["artifacts"]["required"]):
        raise ValueError("Agent omitted required stage artifacts")
    if any(not isinstance(content, str) or not content.strip() for content in artifacts.values()):
        raise ValueError("Agent returned an empty stage artifact")
    if "decision" in result and result["decision"] not in ("approve", "request-changes"):
        raise ValueError("Agent must explicitly approve or request changes")
    return result


def invoke(binding: dict, role: str, prompt: str, cwd: Path, output: Path, timeout: int,
           schema: dict | None = None, *, env: dict | None = None,
           codex_options: list[str] | None = None, codex_bin: str = "codex", supervised: bool = False) -> dict:
    """A successful process is not evidence acceptance; structured consumers validate separately."""
    validate_binding(role, binding)
    tool = binding["tool"]
    if schema and tool == "command" and binding.get("protocol") != "stage-json-v1":
        raise ValueError("Formal stages require command protocol stage-json-v1 and capabilities")
    protocol = output.with_name(output.name + ".protocol")
    protocol.mkdir(parents=True, exist_ok=False, mode=0o700)
    (protocol / "prompt.txt").write_text(prompt)
    if schema:
        (protocol / "schema.json").write_text(json.dumps(schema))
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
        (protocol / "request.json").write_text(json.dumps(request))
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
                result = json.loads((protocol / "result.json").read_text())
            else:
                result = json.loads((output / "stdout.txt").read_text())
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
