"""Tool catalog and project readiness; selection never changes the reference runtime."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

from . import agents, components, kernel
from .agent_runs import output as output, run_agent as run_agent, runs as runs
from .bindings import validate_binding as validate_binding
from .state import State


CATALOG = components.CATALOG


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


def doctor(state: State, project_id: str) -> dict:
    project = state.project(project_id)
    checks = []
    for layer in CATALOG:
        binding = agents.binding_for(project, layer) if layer in agents.ROLE_CAPABILITIES else project["bindings"].get(layer, {"tool": "manual"})
        validate_binding(layer, binding)
        tool = binding["tool"]
        if layer == "kernel":
            checks.append({"layer": layer, "tool": tool, **kernel.available(binding),
                           "authentication": "not_checked", "runtime": "native ForgeKernel campaign; candidate only"})
            continue
        if layer == "memory":
            checks.append({"layer": layer, "tool": tool, "installed": True if tool == "sqlite" else None,
                           "connectivity": "local" if tool == "sqlite" else "not_checked"})
            continue
        if layer == "optimizer":
            checks.append({"layer": layer, "tool": tool, "installed": tool == "manual" or importlib.util.find_spec("gepa") is not None,
                           "authentication": "not_checked"})
            continue
        if layer in ("research", "scheduler"):
            checks.append({"layer": layer, "tool": tool, "installed": tool != "temporal" or importlib.util.find_spec("temporalio") is not None,
                           "connectivity": "not_checked" if tool == "temporal" else "local"})
            continue
        component = components.COMPONENTS[tool]
        supported = not component["platforms"] or sys.platform in component["platforms"]
        checks.append({"layer": layer, "tool": tool, "installed": agents.available(binding, Path(project["repo"])),
                       "authentication": "not_checked", "runtime": "ergora-agent-invocation",
                       "supported": supported,
                       "platform_note": "" if supported else component["platform_note"]})
    return {"project": project_id, "checks": checks,
            "reference_runtime": "default agentflow unchanged; opt in with ergora reference executor for new tasks" if sys.platform == "linux" else "Formal reference execution requires Linux; use WSL2"}
