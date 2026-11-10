"""Verified resource packages and immutable libraries for Agent and Workflow definitions."""

import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat
import tempfile

import yaml

from . import contracts, skill_assets
from .asset_trees import digest_tree, inventory_tree, is_link
from .state import file_lock


def relative_path(value: str, label: str = "Definition") -> Path:
    path = PurePosixPath(value)
    if (not path.parts or path.is_absolute() or PureWindowsPath(value).drive or
            path.as_posix() != value or any(part in (".", "..") for part in path.parts) or
            any(char in value for char in '\\:<>"|?*') or any(ord(char) < 32 for char in value) or
            any(part.endswith((".", " ")) or PureWindowsPath(part).is_reserved() for part in path.parts)):
        raise ValueError(f"{label} resource requires a portable relative path: {value!r}")
    return Path(*path.parts)


def _parse_json(text: str, label: str) -> dict:
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"Duplicate JSON key in {label}: {key}")
            value[key] = item
        return value

    return json.loads(text, object_pairs_hook=unique)


def read_json(path: Path, expected: str | None = None) -> dict:
    encoded = path.read_bytes()
    if expected is not None and hashlib.sha256(encoded).hexdigest() != expected:
        raise ValueError(f"Definition content changed while reading: {path.name}")
    return _parse_json(encoded.decode("utf-8-sig"), path.name)


class _DocumentLoader(yaml.SafeLoader):
    """Compose a bounded JSON data tree without aliases or YAML-specific values."""

    _JSON_TAGS = {f"tag:yaml.org,2002:{kind}" for kind in ("map", "seq", "str", "int", "float", "bool", "null")}

    def __init__(self, text):
        self.depth = self.values = 0
        super().__init__(text)

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise ValueError("Definition documents do not accept YAML aliases")
        self.depth += 1
        self.values += 1
        if self.depth > 64 or self.values > 100_000:
            raise ValueError("Definition document exceeds 64 levels / 100000 values")
        try:
            node = super().compose_node(parent, index)
            if node.tag not in self._JSON_TAGS:
                raise ValueError(f"Definition document requires JSON-compatible YAML tags: {node.tag}")
            return node
        finally:
            self.depth -= 1

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ValueError("Definition document mapping keys must be strings")
            if key in result:
                raise ValueError(f"Duplicate YAML key in definition document: {key}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def convert_document(text: str, format: str = "json") -> dict:
    """Convert editor text; library admission and publication remain separate."""
    try:
        if format == "json":
            definition = _parse_json(text.removeprefix("\ufeff"), "definition document")
        elif format == "yaml":
            definition = yaml.load(text, Loader=_DocumentLoader)
        else:
            raise ValueError(f"Unsupported definition document format: {format}")
        if not isinstance(definition, dict):
            raise ValueError("Definition document requires an object root")
        pending, values = [(definition, 1)], 0
        while pending:
            value, depth = pending.pop()
            values += 1
            if depth > 64 or values > 100_000:
                raise ValueError("Definition document exceeds 64 levels / 100000 values")
            if isinstance(value, dict):
                pending.extend((item, depth + 1) for pair in value.items() for item in pair)
            elif isinstance(value, list):
                pending.extend((item, depth + 1) for item in value)
        encoded = json.dumps(definition, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        return {"definition": definition, "json": encoded,
                "yaml": yaml.safe_dump(definition, sort_keys=True, allow_unicode=True)}
    except (yaml.YAMLError, RecursionError) as error:
        raise ValueError(f"Invalid definition document: {error}") from error


def inspect_bundle(source: Path, filename: str, schemas: dict[int, dict], label: str, *, material: bool = False) -> dict:
    """Check the complete tree and declared resources without executing their content."""
    source = source.expanduser().absolute()
    digest, files, directories = inventory_tree(source, label=label, max_directories=500, max_depth=32)
    spellings = {}
    for name in [*directories, *files]:
        parts = relative_path(name, label).parts
        for depth in range(1, len(parts) + 1):
            prefix = "/".join(parts[:depth])
            if spellings.setdefault(prefix.casefold(), prefix) != prefix:
                raise ValueError(f"{label} bundle has case-insensitive path collisions: {name}")
    if filename not in files:
        raise ValueError(f"{label} bundle requires {filename}")
    definition = read_json(source / filename, files[filename]["sha256"])
    version = definition.get("schema_version") if isinstance(definition, dict) else None
    if type(version) is not int or version not in schemas:
        raise ValueError(f"Unsupported {label} definition schema version: {version!r}")
    schema = schemas[version]
    contracts.validate(definition, schema, f"{label} definition")
    resources, identities = [], set()
    for resource in definition["resources"]:
        if resource["id"] in identities:
            raise ValueError(f"Duplicate {label} resource ID: {resource['id']}")
        identities.add(resource["id"])
        relative = relative_path(resource["path"], label)
        path = source / relative
        if resource["kind"] == "skill":
            actual, _ = digest_tree(path)
            if actual != resource["digest"]:
                raise ValueError(f"{label} Skill digest mismatch: {resource['id']}")
            meta = skill_assets.metadata(path)
            if path.name != meta["name"]:
                raise ValueError(f"{label} Skill directory name must match its frontmatter name")
            instruction = path / "SKILL.md"
            details = {"skill": meta, "instruction_sha256": files[instruction.relative_to(source).as_posix()]["sha256"]}
        else:
            if resource["path"] not in files or files[resource["path"]]["sha256"] != resource["sha256"]:
                raise ValueError(f"{label} resource missing or SHA256 mismatch: {resource['id']}")
            instruction, details = path, {}
        encoded = instruction.read_bytes()
        if hashlib.sha256(encoded).hexdigest() != files[instruction.relative_to(source).as_posix()]["sha256"]:
            raise ValueError(f"{label} content changed while reading: {resource['id']}")
        text = encoded.decode("utf-8-sig")
        if not text.strip() or "\0" in text:
            raise ValueError(f"{label} instructions/context must be nonempty UTF-8 text: {resource['id']}")
        resources.append({**resource, **details, **({"text": text} if material else {})})
    return {"digest": digest, "definition": definition, "files": files,
            "resources": resources, "path": str(source)}


class DefinitionLibrary:
    """Verify historical identity; admit imports before publishing immutable objects."""

    def __init__(self, root: Path, kind: str, schema: dict, inspector, *, import_inspector=None):
        self.root, self.kind, self.schema, self.inspect = root, kind, schema, inspector
        self.inspect_import = import_inspector or inspector
        self.label = kind.capitalize()
        self.store = root / f"{kind}-definitions"
        self.index_schema = {
            "type": "object", "additionalProperties": False, "required": ["schema_version", "definitions"],
            "properties": {"schema_version": {"type": "integer", "const": 1}, "definitions": {
                "type": "object", "propertyNames": schema["$defs"]["id"], "additionalProperties": {
                    "type": "object", "minProperties": 1, "propertyNames": schema["properties"]["version"],
                    "additionalProperties": schema["$defs"]["digest"]}}}}

    def _check_store(self) -> None:
        for directory in (self.store, self.store / "objects"):
            if directory.exists() or directory.is_symlink():
                if is_link(directory) or not directory.is_dir():
                    raise ValueError(f"{self.label} definition storage must use real directories")

    def _index(self) -> dict:
        path = self.store / "index.json"
        if is_link(path) or not path.is_file():
            raise ValueError(f"{self.label} definition index must be a regular file")
        index = read_json(path)
        contracts.validate(index, self.index_schema, f"{self.label} definition index")
        return index

    def _get(self, identity: str, version: str, digest: str, *, material: bool = False) -> dict:
        document = self.inspect(self.store / "objects" / digest, material=material)
        if (document["digest"] != digest or document["definition"]["id"] != identity or
                document["definition"]["version"] != version):
            raise ValueError(f"Stored {self.label} definition identity changed: {identity}@{version}")
        return document

    @staticmethod
    def _publish_index(store: Path, index: dict) -> None:
        with tempfile.TemporaryDirectory(prefix=".index-", dir=store) as temporary:
            path = Path(temporary) / "index.json"
            path.write_text(json.dumps(index, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            path.replace(store / "index.json")

    def import_bundle(self, source: Path) -> dict:
        original = self.inspect_import(source)
        with tempfile.TemporaryDirectory(prefix=f".{self.kind}-import-", dir=self.root) as temporary:
            copy = Path(temporary) / "bundle"
            shutil.copytree(original["path"], copy, symlinks=True)
            staged = self.inspect_import(copy)
            if staged["digest"] != original["digest"]:
                raise ValueError(f"{self.label} source changed while importing; retry a stable source")
            definition = staged["definition"]
            identity, version, digest = definition["id"], definition["version"], staged["digest"]
            with file_lock(self.root / f".{self.kind}-definitions.lock"):
                self._check_store()
                if not self.store.exists():
                    # Publish the first object and reference as one complete library.
                    library = Path(temporary) / "library"
                    (library / "objects").mkdir(parents=True, mode=0o700)
                    copy.rename(library / "objects" / digest)
                    self._publish_index(library, {"schema_version": 1, "definitions": {identity: {version: digest}}})
                    library.rename(self.store)
                    return {**staged, "path": str(self.store / "objects" / digest)}
                index = self._index()
                registered = index["definitions"].get(identity, {}).get(version)
                if registered is not None and registered != digest:
                    raise ValueError(f"{self.label} {identity}@{version} already exists with different content; choose a new version")
                destination = self.store / "objects" / digest
                if destination.exists() or destination.is_symlink():
                    self._get(identity, version, digest)
                elif registered is not None:
                    raise ValueError(f"Stored {self.label} definition is missing; refuse to replace registered evidence")
                else:
                    copy.rename(destination)
                if registered is None:
                    index["definitions"].setdefault(identity, {})[version] = digest
                    # Interrupted publication may leave a complete unreferenced object.
                    self._publish_index(self.store, index)
        return {**staged, "path": str(destination)}

    def get(self, identity: str, version: str, *, material: bool = False) -> dict:
        self._check_store()
        if self.store.exists():
            digest = self._index()["definitions"].get(identity, {}).get(version)
            if digest is not None:
                return self._get(identity, version, digest, material=material)
        raise ValueError(f"Unknown {self.label} definition: {identity}@{version}")

    def documents(self) -> list[dict]:
        self._check_store()
        if not self.store.exists():
            return []
        return [self._get(identity, version, digest)
                for identity, versions in sorted(self._index()["definitions"].items())
                for version, digest in sorted(versions.items())]

    def export(self, identity: str, version: str, destination: Path) -> dict:
        document = self.get(identity, version)
        destination = destination.expanduser().absolute()
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"Choose a new {self.label} export directory")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f".{self.kind}-export-", dir=destination.parent) as temporary:
            copy = Path(temporary) / "bundle"
            shutil.copytree(document["path"], copy, symlinks=True)
            staged = self.inspect(copy)
            if staged["digest"] != document["digest"]:
                raise ValueError(f"Stored {self.label} content changed while exporting")
            if destination.exists() or destination.is_symlink():
                raise ValueError(f"{self.label} export destination appeared; it was not replaced")
            copy.rename(destination)
        return {"digest": document["digest"], "destination": str(destination)}

    def revise(self, identity: str, version: str, base_digest: str, definition: dict, *, publish: bool = False) -> dict:
        """Derive a complete candidate from a pinned historical package, without editing it."""
        with tempfile.TemporaryDirectory(prefix=f".{self.kind}-revision-", dir=self.root) as temporary:
            copy = Path(temporary) / "bundle"
            original = self.export(identity, version, copy)
            if original["digest"] != base_digest:
                raise ValueError(f"{self.label} revision base digest does not match {identity}@{version}")
            standard = copy / f"{self.kind}.json"
            standard.chmod(standard.stat().st_mode | stat.S_IWUSR)
            standard.write_text(
                json.dumps(definition, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                encoding="utf-8", newline="\n")
            candidate = self.import_bundle(copy) if publish else self.inspect_import(copy)
            return {**{key: value for key, value in candidate.items() if key != "path"},
                    "base": {"kind": self.kind, "id": identity, "version": version, "digest": base_digest},
                    "published": publish}

    def verify(self) -> int:
        return len(self.documents())
