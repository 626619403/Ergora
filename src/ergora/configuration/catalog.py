"""Built-in component descriptions, shared by configuration consumers."""

from copy import deepcopy
import json
from pathlib import Path
from ergora._paths import DATA_ROOT


_manifest = json.loads((DATA_ROOT / "components.json").read_text(encoding="utf-8"))
if _manifest["schema_version"] != 1:
    raise ValueError("Unsupported built-in component catalog version")
LAYERS = _manifest["layers"]
COMPONENTS = _manifest["components"]
INSTALLATION_PROFILES = _manifest["installation_profiles"]
ROLE_CAPABILITIES = {layer: definition["requires"] for layer, definition in LAYERS.items()
                     if definition["kind"] == "agent"}
GENERAL_CAPABILITIES = sorted({capability for required in ROLE_CAPABILITIES.values() for capability in required})
TOOL_CAPABILITIES = {tool: definition["capabilities"] for tool, definition in COMPONENTS.items()
                     if definition["kind"] == "agent" and not definition.get("declared_capabilities")}
DEFAULT_BINDINGS = {layer: definition["default_binding"] for layer, definition in LAYERS.items()}

# Missing fields in schema-v1 projects keep their original execution semantics.
_LEGACY_SUPPORT_BINDINGS = {
    "memory": {"tool": "sqlite"}, "optimizer": {"tool": "manual"},
    "research": {"tool": "urls"}, "scheduler": {"tool": "manual"},
    "kernel": {"tool": "manual"},
    "tracker": {"tool": "manual"},
}


def resolve_binding(project: dict, layer: str) -> dict:
    if layer not in LAYERS:
        raise ValueError(f"Unknown project layer: {layer}")
    if layer in project["bindings"]:
        binding = project["bindings"][layer]
        source = {"kind": "project", "path": f"bindings.{layer}"}
    elif LAYERS[layer]["kind"] == "agent":
        binding = project["bindings"]["implementer"]
        source = {"kind": "inherited", "path": "bindings.implementer"}
    else:
        binding = _LEGACY_SUPPORT_BINDINGS[layer]
        source = {"kind": "legacy-default", "path": f"legacy-missing-bindings-v1.{layer}"}
    return {"binding": deepcopy(binding), "source": source}


def _choices(layer: str) -> list[str]:
    definition = LAYERS[layer]
    if definition["kind"] == "agent":
        return [tool for tool, component in COMPONENTS.items() if component["kind"] == "agent"
                and (component.get("declared_capabilities") or
                     set(definition["requires"]) <= set(component["capabilities"]))]
    return [tool for tool, component in COMPONENTS.items() if layer in component["layers"]]


CATALOG = {layer: _choices(layer) for layer in LAYERS}
CHOICES = {role: CATALOG[role] for role in ROLE_CAPABILITIES}


def validate_agent_minimum(binding: dict, minimum: dict | None) -> None:
    """Check a definition's explicit floor without probing or substituting a model."""
    if minimum is None:
        return
    efforts = ("low", "medium", "high", "xhigh", "max", "ultra")
    if (not isinstance(minimum, dict) or set(minimum) != {"model", "reasoning_effort"}
            or not isinstance(minimum["model"], str) or not minimum["model"].strip() or "\0" in minimum["model"]
            or minimum["reasoning_effort"] not in efforts[1:]):
        raise ValueError("Invalid Agent invocation minimum")
    if not isinstance(binding, dict) or binding.get("tool") != "codex" or binding.get("model") != minimum["model"]:
        raise ValueError("Agent invocation minimum requires explicit Codex model " + minimum["model"])
    effort = binding.get("reasoning_effort")
    if effort not in efforts or efforts.index(effort) < efforts.index(minimum["reasoning_effort"]):
        raise ValueError("Agent invocation requires reasoning_effort at least " + minimum["reasoning_effort"])


def configuration(layer: str, tool: str, platform: str) -> dict:
    """Copy the binding structure and resolve display-only defaults for this view."""
    component = COMPONENTS[tool]
    schema = deepcopy(component["configuration"])
    for name, field in schema["properties"].items():
        platform_defaults = field.pop("x-ergora-platform-defaults", {})
        if platform in platform_defaults:
            field["default"] = platform_defaults[platform]
        enum_platforms = field.pop("x-ergora-enum-platforms", {})
        if enum_platforms:
            field["enum"] = [value for value in field["enum"]
                             if value not in enum_platforms or platform in enum_platforms[value]]
        if name == "capabilities" and component.get("declared_capabilities"):
            field["default"] = list(ROLE_CAPABILITIES[layer])
    return schema
