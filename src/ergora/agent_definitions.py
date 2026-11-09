"""Static specialist recipes: verified bundles and an immutable-version library."""

from pathlib import Path

from . import agents, contracts, definition_bundles
from .state import State


def _inspect_bundle(source: Path, *, material: bool = False) -> dict:
    return definition_bundles.inspect_bundle(source, "agent.json", {1: contracts.AGENT_DEFINITION}, "Agent", material=material)


def validate_admission(document: dict) -> None:
    """Apply today's role/backend contract to an already integrity-checked package."""
    definition = document["definition"]
    for role in definition["roles"]:
        if role not in agents.ROLE_CAPABILITIES:
            raise ValueError(f"Unknown agent role: {role}")
        agents.validate_binding(role, definition["backend"])


def inspect_bundle(source: Path, *, material: bool = False) -> dict:
    """Verify content and current admission, without invoking a backend or script."""
    document = _inspect_bundle(source, material=material)
    validate_admission(document)
    return document


def library(root: Path) -> definition_bundles.DefinitionLibrary:
    return definition_bundles.DefinitionLibrary(root, "agent", contracts.AGENT_DEFINITION, _inspect_bundle,
                                              import_inspector=inspect_bundle)


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
