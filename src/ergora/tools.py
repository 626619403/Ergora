"""Tool catalog and project readiness; selection never changes the reference runtime."""

from copy import deepcopy
import importlib.util
from importlib import metadata
import json
import os
import re
import sqlite3
import tempfile
import time
from urllib.parse import urlsplit
from pathlib import Path
import sys

from . import agents, components, kernel, processes, projects
from .agent_runs import output as output, run_agent as run_agent, runs as runs
from .bindings import validate_binding as validate_binding
from .state import State


CATALOG = components.CATALOG


def installation_profiles() -> dict:
    return {"schema_version": 1, **deepcopy(components.INSTALLATION_PROFILES)}


def catalog() -> dict:
    result = {}
    for layer, choices in CATALOG.items():
        result[layer] = []
        for tool in choices:
            component = components.COMPONENTS[tool]
            probe = component["probe"]
            if probe == "local":
                installed = True
            elif probe == "agent":
                installed = agents.available({"tool": tool}, Path.cwd())
            elif probe == "python-module":
                installed = importlib.util.find_spec(component["module"]) is not None
            elif probe in ("binding", "remote", "campaign"):
                installed = None
            else:
                raise ValueError(f"Unsupported component probe: {probe}")
            operations = component["operations"]
            supported = not component["platforms"] or sys.platform in component["platforms"]
            result[layer].append({"tool": tool, "installed": installed if supported else False,
                                  "supported": supported, "platform_note": "" if supported else component["platform_note"],
                                  "authentication": "not_checked",
                                  "operations": operations[layer] if layer in operations else operations["*"],
                                  "capabilities": agents.TOOL_CAPABILITIES.get(tool, []),
                                  "requires": agents.ROLE_CAPABILITIES.get(layer, []),
                                  "configuration": components.configuration(layer, tool, sys.platform),
                                  "note": component["note"], "installation": component["installation"]})
    return deepcopy(result)


def _local_check(binding: dict, repo: Path) -> dict:
    tool = binding["tool"]
    component = components.COMPONENTS[tool]
    supported = not component["platforms"] or sys.platform in component["platforms"]
    check = {"tool": tool, "installed": None, "version": "not_checked",
             "authentication": "not_checked", "connectivity": "not_checked",
             "task_availability": "not_checked", "supported": supported,
             "platform_note": "" if supported else component["platform_note"],
             "remediation": [], "probe_status": "not_requested"}
    if tool in ("manual", "sqlite", "urls"):
        check.update(installed=True, version=sqlite3.sqlite_version if tool == "sqlite" else "not_applicable",
                     authentication="not_required", connectivity="local", task_availability="available")
    elif component["kind"] == "agent":
        check.update(installed=agents.available(binding, repo), runtime="ergora-agent-invocation")
        check["remediation"].append("Run an explicitly budgeted agent invocation to verify the selected model and task; doctor never calls a model.")
        if component["implementation"] == "codex":
            check["remediation"].append("Use codex login, then tools doctor PROJECT --probe; stored credentials do not verify account access or quota.")
        elif component["implementation"] == "claude-code":
            check["remediation"].append("Use claude auth login; authentication is not checked by this driver.")
        elif component["implementation"] == "command":
            check["authentication"] = "external"
            check["remediation"].append("Verify the configured command's credentials and protocol separately; doctor does not execute arbitrary argv.")
    elif tool == "forgekernel":
        check.update(kernel.available(binding), runtime="native ForgeKernel campaign; candidate only")
        check["remediation"].append("Use the pinned Forge installer, verify its task, Claude credentials and GPU, then evaluate the candidate independently.")
    elif tool == "reme":
        check["authentication"] = ("credentials_present" if os.environ.get(binding["token_env"]) else "credentials_missing") if binding.get("token_env") else "external"
        check["remediation"].append("Start the ReMe endpoint and set the named token environment variable if required; run memory sync to verify its protocol and authorization.")
    elif component["probe"] == "python-module":
        check["installed"] = importlib.util.find_spec(component["module"]) is not None
        try:
            check["version"] = metadata.version(component["module"])
        except metadata.PackageNotFoundError:
            pass
        check["remediation"].append(f"Install ergora[{component['installation']['extra']}] in the environment running Ergora.")
        if tool == "temporal":
            check["remediation"].append("Start the selected Temporal service and project worker; a reachable TCP port does not verify namespace, authorization or task queue readiness.")
        else:
            check["remediation"].append("Verify the configured proposer and evaluator with a bounded candidate evaluation; SDK installation alone does not verify optimization.")
    if not supported:
        check.update(installed=False, task_availability="unsupported")
        check["remediation"].append(check["platform_note"])
    elif check["installed"] is False or check["authentication"] == "credentials_missing":
        check["task_availability"] = "blocked"
        check["remediation"].append("Install the selected tool or correct its executable/environment binding before running this operation.")
    if check["version"] == "unsupported":
        check["task_availability"] = "blocked"
    return check


def _probe_check(check: dict, binding: dict, repo: Path, deadline: float) -> None:
    tool = binding["tool"]
    implementation = components.COMPONENTS[tool]["implementation"]
    commands = []
    if check["installed"] and check["supported"] and implementation in ("codex", "claude-code"):
        try:
            program = processes.resolve_program(agents.executable(binding), repo)
        except (OSError, ValueError):
            check.update(installed=False, probe_status="failed", task_availability="blocked")
            return
        commands.append(("version", [program, "--version"]))
        if implementation == "codex":
            commands.append(("authentication", [program, "login", "status"]))
    elif check["installed"] and implementation == "mini-swe-agent":
        commands.append(("version", [binding.get("python", sys.executable), "-c",
            "from importlib.metadata import version; print(version('mini-swe-agent'))"]))
    elif tool in ("reme", "temporal"):
        try:
            address = binding["endpoint"] if tool == "reme" else binding["address"]
            endpoint = urlsplit(address if "://" in address else "//" + address)
            if endpoint.scheme not in ("", "http", "https"):
                raise ValueError("Unsupported endpoint scheme")
            port = endpoint.port
            if port is None:
                # Temporal's SDK supplies http:// for a bare address; URL defaults still apply.
                port = 443 if endpoint.scheme == "https" else 80
            if not endpoint.hostname or not port:
                raise ValueError("Missing endpoint host/port")
        except ValueError:
            check.update(connectivity="invalid_endpoint", probe_status="failed", task_availability="blocked")
            return
        # DNS and TCP both run in the bounded child; no credentials or application data are sent.
        commands.append(("connectivity", [sys.executable, "-c",
            "import socket,sys; socket.create_connection((sys.argv[1],int(sys.argv[2])),timeout=30).close()",
            endpoint.hostname, str(port)]))
    if not commands:
        check["probe_status"] = "unsupported" if not check["supported"] else "not_applicable"
        return
    with tempfile.TemporaryDirectory(prefix="ergora-doctor-") as temporary:
        for index, (dimension, argv) in enumerate(commands):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                check["probe_status"] = "budget_exhausted"
                return
            try:
                output = Path(temporary) / str(index)
                result = processes.run(argv, repo, output, remaining)
                check["probe_status"] = result["status"]
                if result["status"] != "succeeded":
                    check[dimension] = "timed_out" if result["status"] == "timed_out" else "not_confirmed"
                    continue
                if dimension == "version":
                    with (output / "stdout.txt").open("rb") as stream:
                        content = stream.read(4096).decode("utf-8", errors="replace")
                    match = re.search(r"\b[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?\b", content)
                    check[dimension] = match.group() if match else "not_confirmed"
                else:
                    check[dimension] = "credentials_present" if dimension == "authentication" else "tcp_reachable"
            except (OSError, ValueError):
                check.update(probe_status="failed")
                check[dimension] = "not_confirmed"


def doctor(state: State, project_id: str, *, project: dict | None = None,
           probe: bool = False, timeout: int = 5) -> dict:
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 30:
        raise ValueError("Doctor active probe timeout must be 1–30 seconds")
    project = state.project(project_id) if project is None else project
    configuration = projects.effective_configuration(project)
    checks = []
    local_results = {}
    for layer in CATALOG:
        resolved = configuration["layers"][layer]
        binding = resolved["binding"]
        if not resolved["validation"]["valid"]:
            checks.append({"layer": layer, "tool": binding["tool"], "installed": None,
                           "configuration_valid": False, "error": resolved["validation"]["error"],
                           "version": "not_checked", "authentication": "not_checked", "connectivity": "not_checked",
                           "task_availability": "blocked", "probe_status": "not_requested",
                           "remediation": ["Save an explicit compatible binding for this layer; inspect project config for its source."]})
            continue
        key = json.dumps(binding, sort_keys=True)
        if key not in local_results:
            local_results[key] = _local_check(binding, Path(project["repo"]))
        checks.append({"layer": layer, "configuration_valid": True, "source": resolved["source"],
                       **deepcopy(local_results[key])})
    if probe:
        deadline = time.monotonic() + timeout
        active_results = {}
        for check in checks:
            if not check["configuration_valid"]:
                continue
            binding = configuration["layers"][check["layer"]]["binding"]
            key = json.dumps(binding, sort_keys=True)
            if key not in active_results:
                result = deepcopy(local_results[key])
                _probe_check(result, binding, Path(project["repo"]), deadline)
                active_results[key] = result
            check.update(deepcopy(active_results[key]))
    return {"schema_version": 1, "project": project_id, "project_revision": project["revision"],
            "configuration_sha256": configuration["sha256"], "checks": checks,
            "probe": {"requested": probe, "active_budget_seconds": timeout,
                      "scope": "local version/credential status and TCP only; no model, service protocol or task acceptance"},
            "reference_runtime": "default agentflow unchanged; opt in with ergora reference executor for new tasks" if sys.platform == "linux" else "Formal reference execution requires Linux; use WSL2"}
