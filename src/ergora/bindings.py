"""Validate project layer bindings using their component and domain contracts."""

import re
from urllib.parse import urlsplit

from . import agents, components, contracts, issue_backends, kernel
from .components import CATALOG


def development_snapshot(project: dict, configuration: dict) -> dict:
    """Freeze the four selectable development roles under one effective configuration."""
    roles = ("inspector", "planner", "implementer", "reviewer")
    selection = {"schema_version": 1, "reference_project": project["id"],
                 "project_revision": project["revision"],
                 "bindings": {role: configuration["layers"][role]["binding"] for role in roles},
                 "configuration": configuration}
    for role, binding in selection["bindings"].items():
        agents.validate_binding(role, binding, formal=True)
    return selection


def validate_binding(layer: str, binding: dict) -> None:
    if layer not in CATALOG or not isinstance(binding, dict) or binding.get("tool") not in CATALOG[layer]:
        raise ValueError(f"Unsupported layer/tool: {layer}; choices: {CATALOG.get(layer, [])}")
    tool = binding["tool"]
    if layer in agents.ROLE_CAPABILITIES:
        agents.validate_binding(layer, binding)
        return
    if layer == "kernel":
        kernel.validate_binding(binding)
        return
    if components.COMPONENTS[tool]["kind"] == "issue-tracker":
        issue_backends.for_binding(binding)
        return
    contracts.validate(binding, components.COMPONENTS[tool]["configuration"], f"{layer} binding")
    if tool == "reme":
        endpoint = binding.get("endpoint")
        url = urlsplit(endpoint)
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("ReMe endpoint requires HTTP(S), without credentials, query or fragment")
        if "token_env" in binding and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", binding["token_env"]):
            raise ValueError("token_env must name an environment variable")
