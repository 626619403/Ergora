"""Built-in component descriptions, shared by configuration consumers."""

from copy import deepcopy
import json
from pathlib import Path


_manifest = json.loads((Path(__file__).parent / "data/components.json").read_text(encoding="utf-8"))
if _manifest["schema_version"] != 1:
    raise ValueError("Unsupported built-in component catalog version")
LAYERS = _manifest["layers"]
COMPONENTS = _manifest["components"]
ROLE_CAPABILITIES = {layer: definition["requires"] for layer, definition in LAYERS.items()
                     if definition["kind"] == "agent"}
GENERAL_CAPABILITIES = sorted({capability for required in ROLE_CAPABILITIES.values() for capability in required})
TOOL_CAPABILITIES = {tool: definition["capabilities"] for tool, definition in COMPONENTS.items()
                     if definition["kind"] == "agent" and not definition.get("declared_capabilities")}
DEFAULT_BINDINGS = {layer: definition["default_binding"] for layer, definition in LAYERS.items()}


def _choices(layer: str) -> list[str]:
    definition = LAYERS[layer]
    if definition["kind"] == "agent":
        return [tool for tool, component in COMPONENTS.items() if component["kind"] == "agent"
                and (component.get("declared_capabilities") or
                     set(definition["requires"]) <= set(component["capabilities"]))]
    return [tool for tool, component in COMPONENTS.items() if layer in component["layers"]]


CATALOG = {layer: _choices(layer) for layer in LAYERS}
CHOICES = {role: CATALOG[role] for role in ROLE_CAPABILITIES}


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
