"""Static specialist recipes: verified bundles and an immutable-version library."""

from pathlib import Path

from . import agents, contracts, definition_bundles
from .state import State


def inspect_bundle(source: Path, *, material: bool = False) -> dict:
    """Read and verify all content, without invoking any backend or bundled script."""
    document = definition_bundles.inspect_bundle(source, "agent.json", contracts.AGENT_DEFINITION, "Agent", material=material)
    definition = document["definition"]
    for role in definition["roles"]:
        if role not in agents.ROLE_CAPABILITIES:
            raise ValueError(f"Unknown agent role: {role}")
        agents.validate_binding(role, definition["backend"])
    return document


def library(root: Path) -> definition_bundles.DefinitionLibrary:
    return definition_bundles.DefinitionLibrary(root, "agent", contracts.AGENT_DEFINITION, inspect_bundle)


def import_bundle(state: State, source: Path) -> dict:
    return library(state.root).import_bundle(source)


def get(state: State, identity: str, version: str, *, material: bool = False) -> dict:
    return library(state.root).get(identity, version, material=material)


def definitions(state: State, *, role: str | None = None, specialty: str | None = None) -> list[dict]:
    return [{**item["definition"], "digest": item["digest"]} for item in library(state.root).documents()
            if (role is None or role in item["definition"]["roles"]) and
            (specialty is None or specialty in item["definition"]["specialties"])]


def export(state: State, identity: str, version: str, destination: Path) -> dict:
    return library(state.root).export(identity, version, destination)


def verify_store(root: Path) -> int:
    """Check every registered reference without constructing/migrating State."""
    return library(root).verify()
