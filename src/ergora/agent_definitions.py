"""Static specialist recipes: verified bundles and an immutable-version library."""

import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import tempfile

from . import agents, contracts, skill_assets
from .asset_trees import digest_tree, inventory_tree, is_link
from .state import State, file_lock


_SCHEMA = contracts.AGENT_DEFINITION
_INDEX_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["schema_version", "definitions"],
    "properties": {"schema_version": {"type": "integer", "const": 1}, "definitions": {
        "type": "object", "propertyNames": _SCHEMA["$defs"]["id"], "additionalProperties": {
            "type": "object", "minProperties": 1, "propertyNames": _SCHEMA["properties"]["version"],
            "additionalProperties": _SCHEMA["$defs"]["digest"]}}}}


def _relative(value: str) -> Path:
    path = PurePosixPath(value)
    if (not path.parts or path.is_absolute() or PureWindowsPath(value).drive or
            path.as_posix() != value or any(part in (".", "..") for part in path.parts) or
            any(char in value for char in '\\:<>"|?*') or any(ord(char) < 32 for char in value) or
            any(part.endswith((".", " ")) or PureWindowsPath(part).is_reserved() for part in path.parts)):
        raise ValueError(f"Agent resource requires a portable relative path: {value!r}")
    return Path(*path.parts)


def _read_json(path: Path, expected: str | None = None) -> dict:
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"Duplicate JSON key in {path.name}: {key}")
            value[key] = item
        return value

    encoded = path.read_bytes()
    if expected is not None and hashlib.sha256(encoded).hexdigest() != expected:
        raise ValueError(f"Agent content changed while reading: {path.name}")
    return json.loads(encoded.decode("utf-8-sig"), object_pairs_hook=unique)


def inspect_bundle(source: Path, *, material: bool = False) -> dict:
    """Read and verify all content, without invoking any backend or bundled script."""
    source = source.expanduser().absolute()
    digest, files, directories = inventory_tree(source, label="Agent", max_directories=500, max_depth=32)
    spellings = {}
    for name in [*directories, *files]:
        parts = _relative(name).parts
        for depth in range(1, len(parts) + 1):
            prefix = "/".join(parts[:depth])
            if spellings.setdefault(prefix.casefold(), prefix) != prefix:
                raise ValueError(f"Agent bundle has case-insensitive path collisions: {name}")
    if "agent.json" not in files:
        raise ValueError("Agent bundle requires agent.json")
    definition = _read_json(source / "agent.json", files["agent.json"]["sha256"])
    contracts.validate(definition, _SCHEMA, "Agent definition")
    for role in definition["roles"]:
        if role not in agents.ROLE_CAPABILITIES:
            raise ValueError(f"Unknown agent role: {role}")
        agents.validate_binding(role, definition["backend"])
    resources, identities = [], set()
    for resource in definition["resources"]:
        if resource["id"] in identities:
            raise ValueError(f"Duplicate Agent resource ID: {resource['id']}")
        identities.add(resource["id"])
        relative = _relative(resource["path"])
        path = source / relative
        if resource["kind"] == "skill":
            actual, _ = digest_tree(path)
            if actual != resource["digest"]:
                raise ValueError(f"Agent Skill digest mismatch: {resource['id']}")
            meta = skill_assets.metadata(path)
            if path.name != meta["name"]:
                raise ValueError("Agent Skill directory name must match its frontmatter name")
            instruction = path / "SKILL.md"
            details = {"skill": meta, "instruction_sha256": files[instruction.relative_to(source).as_posix()]["sha256"]}
        else:
            if resource["path"] not in files or files[resource["path"]]["sha256"] != resource["sha256"]:
                raise ValueError(f"Agent resource missing or SHA256 mismatch: {resource['id']}")
            instruction, details = path, {}
        encoded = instruction.read_bytes()
        if hashlib.sha256(encoded).hexdigest() != files[instruction.relative_to(source).as_posix()]["sha256"]:
            raise ValueError(f"Agent content changed while reading: {resource['id']}")
        text = encoded.decode("utf-8-sig")
        if not text.strip() or "\0" in text:
            raise ValueError(f"Agent instructions/context must be nonempty UTF-8 text: {resource['id']}")
        resources.append({**resource, **details, **({"text": text} if material else {})})
    return {"digest": digest, "definition": definition, "files": files,
            "resources": resources, "path": str(source)}


def _store(root: Path) -> Path:
    store = root / "agent-definitions"
    for directory in (store, store / "objects"):
        if directory.exists() or directory.is_symlink():
            if is_link(directory) or not directory.is_dir():
                raise ValueError("Agent definition storage must use real directories")
    return store


def _index(store: Path) -> dict:
    path = store / "index.json"
    if is_link(path) or not path.is_file():
        raise ValueError("Agent definition index must be a regular file")
    index = _read_json(path)
    contracts.validate(index, _INDEX_SCHEMA, "Agent definition index")
    return index


def _get(store: Path, identity: str, version: str, digest: str, *, material: bool = False) -> dict:
    document = inspect_bundle(store / "objects" / digest, material=material)
    if (document["digest"] != digest or document["definition"]["id"] != identity or
            document["definition"]["version"] != version):
        raise ValueError(f"Stored Agent definition identity changed: {identity}@{version}")
    return document


def _publish_index(store: Path, index: dict) -> None:
    with tempfile.TemporaryDirectory(prefix=".index-", dir=store) as temporary:
        path = Path(temporary) / "index.json"
        path.write_text(json.dumps(index, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        path.replace(store / "index.json")


def import_bundle(state: State, source: Path) -> dict:
    original = inspect_bundle(source)
    with tempfile.TemporaryDirectory(prefix=".agent-import-", dir=state.root) as temporary:
        copy = Path(temporary) / "bundle"
        shutil.copytree(original["path"], copy, symlinks=True)
        staged = inspect_bundle(copy)
        if staged["digest"] != original["digest"]:
            raise ValueError("Agent source changed while importing; retry a stable source")
        definition = staged["definition"]
        identity, version, digest = definition["id"], definition["version"], staged["digest"]
        with file_lock(state.root / ".agent-definitions.lock"):
            store = _store(state.root)
            if not store.exists():
                # The first reference and object become visible together. A
                # failed first import leaves no half-initialized library.
                library = Path(temporary) / "library"
                (library / "objects").mkdir(parents=True, mode=0o700)
                copy.rename(library / "objects" / digest)
                _publish_index(library, {"schema_version": 1, "definitions": {identity: {version: digest}}})
                library.rename(store)
                return {**staged, "path": str(store / "objects" / digest)}
            # Once published, a missing index is corruption, never an empty
            # library that can silently discard other registered versions.
            index = _index(store)
            registered = index["definitions"].get(identity, {}).get(version)
            if registered is not None and registered != digest:
                raise ValueError(f"Agent {identity}@{version} already exists with different content; choose a new version")
            destination = store / "objects" / digest
            if destination.exists() or destination.is_symlink():
                _get(store, identity, version, digest)
            elif registered is not None:
                raise ValueError("Stored Agent definition is missing; refuse to replace registered evidence")
            else:
                copy.rename(destination)
            if registered is None:
                index["definitions"].setdefault(identity, {})[version] = digest
                # Publish the reference last. A failed index write may leave an
                # intact unreferenced object, which a retry verifies and reuses.
                _publish_index(store, index)
    return {**staged, "path": str(destination)}


def get(state: State, identity: str, version: str, *, material: bool = False) -> dict:
    store = _store(state.root)
    if not store.exists():
        raise ValueError(f"Unknown Agent definition: {identity}@{version}")
    digest = _index(store)["definitions"].get(identity, {}).get(version)
    if digest is None:
        raise ValueError(f"Unknown Agent definition: {identity}@{version}")
    return _get(store, identity, version, digest, material=material)


def definitions(state: State, *, role: str | None = None, specialty: str | None = None) -> list[dict]:
    store = _store(state.root)
    if not store.exists():
        return []
    result = []
    for identity, versions in sorted(_index(store)["definitions"].items()):
        for version, digest in sorted(versions.items()):
            document = _get(store, identity, version, digest)
            definition = document["definition"]
            if (role is None or role in definition["roles"]) and (specialty is None or specialty in definition["specialties"]):
                result.append({**definition, "digest": digest})
    return result


def export(state: State, identity: str, version: str, destination: Path) -> dict:
    document = get(state, identity, version)
    destination = destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Choose a new Agent export directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".agent-export-", dir=destination.parent) as temporary:
        copy = Path(temporary) / "bundle"
        shutil.copytree(document["path"], copy, symlinks=True)
        staged = inspect_bundle(copy)
        if staged["digest"] != document["digest"]:
            raise ValueError("Stored Agent content changed while exporting")
        if destination.exists() or destination.is_symlink():
            raise ValueError("Agent export destination appeared; it was not replaced")
        copy.rename(destination)
    return {"digest": document["digest"], "destination": str(destination)}


def verify_store(root: Path) -> int:
    """Check every registered reference without constructing/migrating State."""
    store = _store(root)
    if not store.exists():
        return 0
    count = 0
    for identity, versions in _index(store)["definitions"].items():
        for version, digest in versions.items():
            _get(store, identity, version, digest)
            count += 1
    return count
