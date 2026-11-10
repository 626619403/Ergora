"""Static, bounded composition; no model calls, scheduler, or execution authorization."""

from copy import deepcopy
import base64
import ctypes
from graphlib import CycleError, TopologicalSorter
import hashlib
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from urllib.parse import urlsplit

from . import agent_definitions, contracts, definition_bundles
from .asset_trees import inventory_tree
from .state import State


_PRESETS = Path(__file__).parent / "data/presets"


def _preset_catalog() -> dict:
    catalog = definition_bundles.read_json(_PRESETS / "presets.json")
    if catalog["schema_version"] != 1:
        raise ValueError("Unsupported bundled preset catalog version")
    return catalog["presets"]


def presets() -> list[dict]:
    """List shipped recipes without creating State or probing execution tools."""
    return [{"id": identity, "description": entry["description"], "runtime": entry["runtime"],
             "root": _reference(inspect_bundle(_PRESETS / "workflows" / entry["root"]), "workflow")}
            for identity, entry in _preset_catalog().items()]


def install_preset(state: State, identity: str) -> dict:
    """Import exact dependency versions; each existing library owns publication.

    This is restartable per-definition installation, not a cross-library
    transaction or execution authorization. It never replaces stored versions.
    """
    catalog = _preset_catalog()
    if identity not in catalog:
        raise ValueError(f"Unknown bundled composition: {identity}")
    entry = catalog[identity]
    imported_agents = [agent_definitions.import_bundle(state, _PRESETS / "agents" / name)
                       for name in entry["agents"]]
    imported_workflows = {name: import_bundle(state, _PRESETS / "workflows" / name)
                          for name in entry["workflows"]}
    return {"id": identity, "runtime": entry["runtime"], "execution_authorized": False,
            "root": _reference(imported_workflows[entry["root"]], "workflow"),
            "agents": [_reference(item, "agent") for item in imported_agents],
            "workflows": [_reference(item, "workflow") for item in imported_workflows.values()]}


def _encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _permissions(value: dict) -> None:
    for access in ("read", "write"):
        for name in value[access]:
            path = definition_bundles.relative_path(name, "Permission")
            if (path.parts[0] not in ("workspace", "definitions") or
                    (access == "write" and path.parts[0] != "workspace")):
                raise ValueError(f"Permission requires a supported logical mount/access: {name}")
            if path.parts[0] == "definitions" and len(path.parts) > 1:
                if len(path.parts) < 4 or path.parts[1] not in ("agent", "workflow"):
                    raise ValueError(f"Permission requires a complete definition kind/ID/version: {name}")
                contracts.validate(path.parts[2], contracts.WORKFLOW_DEFINITION["$defs"]["id"], "Permission definition ID")
                contracts.validate(path.parts[3], contracts.WORKFLOW_DEFINITION["properties"]["version"], "Permission definition version")
    for origin in value["network"]:
        parsed = urlsplit(origin)
        host = parsed.hostname or ""
        try:
            address = ipaddress.ip_address(host)
            host = f"[{address.compressed}]" if address.version == 6 else address.compressed
        except ValueError:
            if len(host) > 253 or re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*", host) is None:
                raise ValueError(f"Network permission requires an exact DNS name or IP address: {origin}")
        port = parsed.port
        authority = host + (f":{port}" if port is not None and port != {"http": 80, "https": 443}.get(parsed.scheme) else "")
        if (parsed.scheme not in ("http", "https") or parsed.username is not None or parsed.password is not None or
                parsed.path or parsed.query or parsed.fragment or port == 0 or "%" in host or
                origin != f"{parsed.scheme}://{authority}"):
            raise ValueError(f"Network permission requires a canonical HTTP(S) origin: {origin}")


def _covered(path: str, scopes: list[str]) -> bool:
    return any(PurePosixPath(path).is_relative_to(PurePosixPath(scope)) for scope in scopes)


def _within(request: dict, ceiling: dict, path: str) -> None:
    for access in ("read", "write"):
        for name in request[access]:
            if not _covered(name, ceiling[access]):
                raise ValueError(f"Permission exceeds ancestor/project at {path}: {access} {name}")
    if request["shell"] and not ceiling["shell"]:
        raise ValueError(f"Permission exceeds ancestor/project at {path}: shell")
    if not set(request["network"]).issubset(ceiling["network"]):
        raise ValueError(f"Permission exceeds ancestor/project at {path}: network")


def _levels(definition: dict) -> list[list[str]]:
    nodes = {node["id"]: node for node in definition["nodes"]}
    if len(nodes) != len(definition["nodes"]):
        raise ValueError("Duplicate Workflow node ID")
    for node in nodes.values():
        if set(node["depends_on"]) - nodes.keys():
            raise ValueError(f"Unknown Workflow dependency at {node['id']}")
    graph = TopologicalSorter({key: node["depends_on"] for key, node in nodes.items()})
    try:
        graph.prepare()
    except CycleError as error:
        raise ValueError(f"Workflow dependency cycle: {error.args[1]}") from error
    levels = []
    while graph.is_active():
        ready = sorted(graph.get_ready())
        levels.append(ready)
        graph.done(*ready)
    return levels


def inspect_bundle(source: Path, *, material: bool = False) -> dict:
    document = definition_bundles.inspect_bundle(source, "workflow.json", contracts.WORKFLOW_DEFINITIONS,
                                                 "Workflow", material=material)
    definition = document["definition"]
    _permissions(definition["permissions"])
    for node in definition["nodes"]:
        if "permissions" in node:
            _permissions(node["permissions"])
    _levels(definition)
    return document


def library(root: Path) -> definition_bundles.DefinitionLibrary:
    def checked(path, *, material=False):
        document = inspect_bundle(path, material=True)
        definition = document["definition"]
        grant = {"schema_version": 1, "permissions": definition["permissions"], "limits": definition["limits"]}
        _Compilation(root, grant, agent_admission=agent_definitions.validate_admission).compile(document)
        if not material:
            for resource in document["resources"]:
                del resource["text"]
        return document
    return definition_bundles.DefinitionLibrary(root, "workflow", contracts.WORKFLOW_DEFINITION, inspect_bundle,
                                              import_inspector=checked)


def _reference(document: dict, kind: str) -> dict:
    return {"kind": kind, "id": document["definition"]["id"], "version": document["definition"]["version"],
            "digest": document["digest"]}


def _materials(inherited: list[dict], document: dict, kind: str, path: str) -> list[dict]:
    """Merge only the structural chain; preserve every origin even on deduplication."""
    result = deepcopy(inherited)
    logical, skills = {}, {}
    for item in result:
        for identity in item["ids"]:
            logical[identity] = item
        if item["kind"] == "skill":
            skills[item["skill"]["name"]] = item
    reference = _reference(document, kind)
    for resource in document["resources"]:
        digest = resource.get("digest", resource.get("sha256"))
        same = logical.get(resource["id"])
        if same is not None and (same["kind"], same["content_digest"]) != (resource["kind"], digest):
            raise ValueError(f"Inherited resource ID conflict at {path}: {resource['id']}")
        if resource["kind"] == "skill":
            loaded = skills.get(resource["skill"]["name"])
            if loaded is not None and loaded["content_digest"] != digest:
                raise ValueError(f"Inherited Skill loading name conflict at {path}: {resource['skill']['name']}")
            same = loaded or same
        origin = {"instance": path, "definition": reference, "resource_id": resource["id"], "path": resource["path"],
                  "uri": f"definitions/{kind}/{reference['id']}/{reference['version']}/{resource['path']}"}
        if same is None:
            same = {**resource, "ids": [resource["id"]], "content_digest": digest, "sources": [origin]}
            result.append(same)
        else:
            if resource["id"] not in same["ids"]:
                same["ids"].append(resource["id"])
            same["sources"].append(origin)
        logical[resource["id"]] = same
        if resource["kind"] == "skill":
            skills[resource["skill"]["name"]] = same
    return result


def _readable(materials: list[dict], permissions: dict, path: str) -> None:
    for resource in materials:
        for source in resource["sources"]:
            if not _covered(source["uri"], permissions["read"]):
                raise ValueError(f"Required inherited resource is not readable at {path}: {source['uri']}")


class _Compilation:
    """One bounded traversal owns reference, graph, inheritance and budget checks."""

    def __init__(self, root: Path, grant: dict, *, agent_admission=None):
        contracts.validate(grant, contracts.COMPOSITION_GRANT, "Composition preview grant")
        _permissions(grant["permissions"])
        self.root, self.grant = root, grant
        self.agent_admission = agent_admission
        self.documents, self.instances = {}, []
        self.preview_version = 1
        self.total = {"path": "project", "limits": grant["limits"], "depth": 0, "instances": 0, "material_bytes": 0}

    def _resolve(self, reference: dict, *, material: bool = False) -> dict:
        key = (reference["kind"], reference["id"], reference["version"], reference["digest"], material)
        if key not in self.documents:
            source = agent_definitions.library(self.root) if reference["kind"] == "agent" else library(self.root)
            document = source.get(reference["id"], reference["version"], material=material)
            if document["digest"] != reference["digest"]:
                raise ValueError(f"Definition reference digest mismatch: {reference['id']}@{reference['version']}")
            if reference["kind"] == "agent" and self.agent_admission is not None:
                self.agent_admission(document)
            self.documents[key] = document
        return self.documents[key]

    def _links(self, definition: dict) -> None:
        nodes = {node["id"]: node for node in definition["nodes"]}
        ports = {}
        for identity, node in nodes.items():
            if "join" in node or node["ref"]["kind"] == "agent":
                ports[identity] = ["result"]
            else:
                ports[identity] = list(self._resolve(node["ref"])["definition"]["outputs"])
        def binding(value, dependencies):
            if "input" in value:
                if value["input"] not in definition["inputs"]:
                    raise ValueError(f"Unknown Workflow input port: {value['input']}")
            elif (value["node"] not in dependencies or value["node"] not in ports or
                  value["output"] not in ports[value["node"]]):
                raise ValueError(f"Unknown or non-dependent Workflow output port: {value}")
        for node in nodes.values():
            if "join" in node:
                continue
            expected = (["task"] if node["ref"]["kind"] == "agent" else
                        self._resolve(node["ref"])["definition"]["inputs"])
            if set(node["inputs"]) != set(expected):
                raise ValueError(f"Workflow input ports differ at {node['id']}: expected {expected}")
            for value in node["inputs"].values():
                binding(value, node["depends_on"])
        for value in definition["outputs"].values():
            binding(value, nodes)

    @staticmethod
    def _count(scopes: list[dict], path: str) -> None:
        for scope in scopes:
            scope["instances"] += 1
            depth = len(path.split("/")) - scope["depth"]
            for name, actual in (("depth", depth), ("instances", scope["instances"])):
                if actual > scope["limits"][name]:
                    raise ValueError(f"Composition {name} budget exceeded at {path} (scope {scope['path']})")

    @staticmethod
    def _prompt(materials: list[dict]) -> str:
        return "\n\n".join(f"Resource {','.join(item['ids'])} ({item['kind']}); sources: " +
                             json.dumps(item["sources"], sort_keys=True, ensure_ascii=False) + "\n" + item["text"]
                             for item in materials)

    def _workflow(self, document: dict, path: str, inherited: list[dict], ceiling: dict,
                  scopes: list[dict], lineage: tuple, inputs: dict, dependencies: list[str]) -> None:
        definition = document["definition"]
        self.preview_version = max(self.preview_version, definition["schema_version"])
        reference = _reference(document, "workflow")
        identity = (reference["id"], reference["version"], reference["digest"])
        if identity in lineage:
            raise ValueError(f"Workflow reference cycle at {path}")
        permissions = definition["permissions"]
        _within(permissions, ceiling, path)
        scope = {"path": path, "limits": definition["limits"], "depth": len(path.split("/")) - 1,
                 "instances": 0, "material_bytes": 0}
        scopes = [*scopes, scope]
        self._count(scopes, path)
        materials = _materials(inherited, document, "workflow", path)
        _readable(materials, permissions, path)
        self._links(definition)
        levels = _levels(definition)
        instance = {"path": path, "parent": path.rpartition("/")[0] or None, "kind": "workflow", "ref": reference,
                    "permissions": permissions, "inputs": inputs, "outputs": definition["outputs"], "depends_on": dependencies,
                    "levels": [[f"{path}/{name}" for name in level] for level in levels], "limits": definition["limits"]}
        self.instances.append(instance)
        nodes = {node["id"]: node for node in definition["nodes"]}
        for level in levels:
            for name in level:
                node, child_path = nodes[name], f"{path}/{name}"
                dependencies = [f"{path}/{value}" for value in node["depends_on"]]
                if "join" in node:
                    self._count(scopes, child_path)
                    self.instances.append({"path": child_path, "parent": path, "kind": "join", "join": "all",
                                           "depends_on": dependencies, "outputs": ["result"], "permissions": permissions})
                elif node["ref"]["kind"] == "workflow":
                    self._workflow(self._resolve(node["ref"], material=True), child_path, materials, permissions,
                                   scopes, (*lineage, identity), node["inputs"], dependencies)
                else:
                    self._count(scopes, child_path)
                    child = self._resolve(node["ref"], material=True)
                    if node["role"] not in child["definition"]["roles"]:
                        raise ValueError(f"Agent role not supported at {child_path}: {node['role']}")
                    _within(node["permissions"], permissions, child_path)
                    selected = _materials(materials, child, "agent", child_path)
                    _readable(selected, node["permissions"], child_path)
                    prompt = self._prompt(selected)
                    size = len(prompt.encode("utf-8"))
                    for active in scopes:
                        active["material_bytes"] += size
                        if active["material_bytes"] > active["limits"]["material_bytes"]:
                            raise ValueError(f"Composition material_bytes budget exceeded at {child_path} (scope {active['path']})")
                    self.instances.append({"path": child_path, "parent": path, "kind": "agent", "ref": node["ref"],
                                           "role": node["role"], "backend_request": child["definition"]["backend"],
                                           **({"review_requirement": node["review_requirement"]}
                                              if "review_requirement" in node else {}),
                                           "depends_on": dependencies, "inputs": node["inputs"], "outputs": ["result"],
                                           "permissions": node["permissions"], "resources": selected, "prompt": prompt,
                                           "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                                           "material_bytes": size,
                                           "concurrency_scopes": [{"path": active["path"], "limit": active["limits"]["concurrency"]}
                                                                  for active in scopes]})
        instance["usage"] = {key: scope[key] for key in ("instances", "material_bytes")}

    def compile(self, document: dict) -> dict:
        self._workflow(document, "root", [], self.grant["permissions"], [self.total], (),
                       {name: {"input": name} for name in document["definition"]["inputs"]}, [])
        result = {"schema_version": self.preview_version, "kind": "composition-preview", "executable": False,
                  "root": _reference(document, "workflow"), "grant": self.grant, "instances": self.instances,
                  "usage": {key: self.total[key] for key in ("instances", "material_bytes")},
                  "pending": ["project admission and approved manifest", "backend permission and resource enforcement",
                              "runtime port values, complete input capacity and durable execution"]}
        return {**result, "preview_sha256": hashlib.sha256(_encoded(result)).hexdigest()}


def import_bundle(state: State, source: Path) -> dict:
    return library(state.root).import_bundle(source)


def revise(state: State, identity: str, version: str, base_digest: str, definition: dict, *, publish: bool = False,
           resource_changes: dict | None = None, accepted_candidate: dict | None = None,
           preview_resources: bool = False) -> dict:
    return library(state.root).revise(identity, version, base_digest, definition, publish=publish,
        resource_changes=resource_changes, accepted_candidate=accepted_candidate, preview_resources=preview_resources)


def read_file(state: State, identity: str, version: str, base_digest: str, path: str, *, offset: int = 0,
              limit: int = 65_536) -> dict:
    return library(state.root).read_file(identity, version, base_digest, path, offset=offset, limit=limit)


def get(state: State, identity: str, version: str, *, material: bool = False) -> dict:
    return library(state.root).get(identity, version, material=material)


def definitions(state: State) -> list[dict]:
    return [{**item["definition"], "digest": item["digest"]} for item in library(state.root).documents()]


def export(state: State, identity: str, version: str, destination: Path) -> dict:
    return library(state.root).export(identity, version, destination)


def preview(root: Path, identity: str, version: str, grant: dict) -> dict:
    """Read a library without constructing State or changing any project configuration."""
    document = library(root).get(identity, version, material=True)
    return _Compilation(root, grant, agent_admission=agent_definitions.validate_admission).compile(document)


def verify_store(root: Path) -> int:
    documents = library(root).documents()
    for document in documents:
        definition = document["definition"]
        grant = {"schema_version": 1, "permissions": definition["permissions"], "limits": definition["limits"]}
        _Compilation(root, grant).compile(library(root).get(definition["id"], definition["version"], material=True))
    return len(documents)


def _input_fields(composition: dict, instance: str, task: bytes, max_prompt_bytes: int) -> tuple[dict, bytes]:
    contracts.validate(max_prompt_bytes, contracts.COMPOSITION_INPUT["properties"]["max_prompt_bytes"], "Input byte limit")
    if len(task) > contracts.COMPOSITION_INPUT["properties"]["max_prompt_bytes"]["maximum"]:
        raise ValueError("Composition task exceeds the supported input byte limit")
    text = task.decode("utf-8-sig")
    if not text.strip() or "\0" in text:
        raise ValueError("Composition task must be nonempty UTF-8 text without NUL")
    selected = next((item for item in composition["instances"] if item["path"] == instance and item["kind"] == "agent"), None)
    if selected is None:
        raise ValueError(f"Select an Agent leaf instance: {instance}")
    prompt = (selected["prompt"] + "\n\nOperator supplied task (workflow ports have not been executed):\n" + text).encode("utf-8")
    if len(prompt) > max_prompt_bytes:
        raise ValueError(f"Complete composition prompt exceeds the input byte limit: {len(prompt)} > {max_prompt_bytes}")
    document = {"schema_version": 1, "kind": "composition-input", "execution_authorized": False,
                "root": composition["root"], "instance": instance, "grant": composition["grant"],
                "input_origin": "operator-supplied", "task_sha256": hashlib.sha256(task).hexdigest(),
                "preview_sha256": composition["preview_sha256"], "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
                "prompt_bytes": len(prompt), "max_prompt_bytes": max_prompt_bytes}
    contracts.validate(document, contracts.COMPOSITION_INPUT, "Composition input")
    return document, prompt


def _manifest_fields(composition: dict) -> dict:
    return {"schema_version": 1, "kind": "composition-manifest", "execution_authorized": False,
            "root": composition["root"], "grant": composition["grant"], "preview_sha256": composition["preview_sha256"]}


def _inspect_snapshot(source: Path, *, leaf_input: bool, material: bool) -> dict:
    """One complete-tree verifier for a static graph and its prepared leaf inputs."""
    source = source.expanduser().absolute()
    before = inventory_tree(source, label="Composition bundle", max_directories=1000, max_depth=48)
    digest, files, _ = before
    filename = "request.json" if leaf_input else "manifest.json"
    required = {filename, "composition.json", *(["task.txt", "prompt.txt"] if leaf_input else [])}
    if not required.issubset(files):
        raise ValueError("Composition bundle requires " + ", ".join(sorted(required)))
    request = definition_bundles.read_json(source / filename, files[filename]["sha256"])
    contracts.validate(request, contracts.COMPOSITION_INPUT if leaf_input else contracts.COMPOSITION_MANIFEST, "Composition bundle")
    assets = source / "assets"
    root = request["root"]
    document = library(assets).get(root["id"], root["version"], material=True)
    composition = _Compilation(assets, request["grant"]).compile(document)
    stored = definition_bundles.read_json(source / "composition.json", files["composition.json"]["sha256"])
    expected, prompt = (_input_fields(composition, request["instance"], (source / "task.txt").read_bytes(), request["max_prompt_bytes"])
                        if leaf_input else (_manifest_fields(composition), None))
    if (_encoded(stored) != _encoded(composition) or _encoded(request) != _encoded(expected) or
            (leaf_input and (source / "prompt.txt").read_bytes() != prompt)):
        raise ValueError("Composition bundle differs from its complete stored material, task or prompt")
    wanted = {(item["ref"]["kind"], item["ref"]["id"], item["ref"]["version"], item["ref"]["digest"])
              for item in composition["instances"] if "ref" in item}
    actual = set()
    for store in (agent_definitions.library(assets), library(assets)):
        required.add((store.store / "index.json").relative_to(source).as_posix())
        for item in store.documents():
            actual.add((store.kind, item["definition"]["id"], item["definition"]["version"], item["digest"]))
            for name, details in item["files"].items():
                path = (Path(item["path"]) / name).relative_to(source).as_posix()
                if files.get(path) != details:
                    raise ValueError(f"Composition bundle asset changed during verification: {path}")
                required.add(path)
    if actual != wanted or set(files) != required:
        raise ValueError("Composition bundle contains unreferenced assets or undeclared files")
    for name, data in ((("task.txt", (source / "task.txt").read_bytes()), ("prompt.txt", prompt)) if leaf_input else []):
        if hashlib.sha256(data).hexdigest() != files[name]["sha256"]:
            raise ValueError(f"Composition bundle changed during verification: {name}")
    if inventory_tree(source, label="Composition bundle", max_directories=1000, max_depth=48) != before:
        raise ValueError("Composition bundle changed during verification; retry a stable directory")
    return {"digest": digest, "request" if leaf_input else "manifest": request, "path": str(source),
            **({"composition": composition} if material else {}),
            **({"prompt": prompt.decode("utf-8")} if material and leaf_input else {})}


def inspect_input(source: Path, *, material: bool = False) -> dict:
    """Verify a saved input and all its assets without today's backend admission."""
    return _inspect_snapshot(source, leaf_input=True, material=material)


def inspect_manifest(source: Path, *, material: bool = False) -> dict:
    """Verify a complete static graph; no current admission, model or authorization."""
    return _inspect_snapshot(source, leaf_input=False, material=material)


def restore_manifest(snapshot: dict, destination: Path) -> dict:
    """Publish a carried complete manifest atomically; never expose a partial tree."""
    destination = destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        checked = inspect_manifest(destination, material=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.composition-restore-', dir=destination.parent) as temporary:
            staged = Path(temporary) / 'manifest'
            staged.mkdir(mode=0o700)
            for name, item in snapshot['files'].items():
                path = staged / definition_bundles.relative_path(name, 'Frozen composition')
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(base64.b64decode(item['content_base64'], validate=True))
                path.chmod(0o600 | item['executable_bits'])
            checked = inspect_manifest(staged, material=True)
            if checked['digest'] != snapshot['digest']:
                raise ValueError('Frozen composition manifest changed')
            _publish_bundle(staged, destination)
    if checked['digest'] != snapshot['digest']:
        raise ValueError('Frozen composition manifest changed')
    return {**checked, 'path': str(destination)}


def _publish_bundle(staged: Path, destination: Path) -> None:
    """Publish once without replacing even a concurrently created empty directory."""
    if os.name == "nt":
        staged.rename(destination)
    elif sys.platform == "linux":
        rename = getattr(ctypes.CDLL(None, use_errno=True), "renameat2", None)
        if rename is None:
            raise ValueError("Atomic composition publication requires Linux renameat2 or Windows")
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        if rename(-100, os.fsencode(staged), -100, os.fsencode(destination), 1) != 0:  # AT_FDCWD, RENAME_NOREPLACE
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code), str(destination))
    else:
        raise ValueError("Atomic composition publication is supported on Linux and Windows")


def _prepare_bundle(root: Path, composition: dict, destination: Path, documents: dict[str, bytes], inspector) -> dict:
    """Publish precisely the graph's referenced assets and format-specific materials once."""
    destination = destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Choose a new composition bundle directory")
    for store in (agent_definitions.library(root), library(root)):
        if destination.resolve().is_relative_to(store.store.resolve()):
            raise ValueError("Composition bundle cannot be written inside an immutable definition library")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".composition-bundle-", dir=destination.parent) as temporary:
        staged = Path(temporary) / "bundle"
        assets = staged / "assets"
        assets.mkdir(parents=True, mode=0o700)
        for name, content in {"composition.json": _encoded(composition), **documents}.items():
            (staged / name).write_bytes(content)
        # Agents first, then children before parents. Repeated instances keep their own paths in composition.json.
        instances = [item for item in composition["instances"] if item["kind"] == "agent"]
        instances += [item for item in reversed(composition["instances"]) if item["kind"] == "workflow"]
        copied = set()
        for item in instances:
            reference = item["ref"]
            key = (reference["kind"], reference["id"], reference["version"], reference["digest"])
            if key in copied:
                continue
            source = agent_definitions.library(root) if reference["kind"] == "agent" else library(root)
            target = agent_definitions.library(assets) if reference["kind"] == "agent" else library(assets)
            original = source.get(reference["id"], reference["version"])
            if original["digest"] != reference["digest"]:
                raise ValueError("Composition definition changed while preparing its input")
            imported = target.import_bundle(Path(original["path"]))
            if imported["digest"] != reference["digest"]:
                raise ValueError("Composition definition changed while copying its input")
            copied.add(key)
            # This private staging library has one writer; locks are not published input assets.
            (assets / f".{target.kind}-definitions.lock").unlink()
            inventory_tree(staged, label="Composition bundle", max_directories=1000, max_depth=48)
        verified = inspector(staged)
        if destination.exists() or destination.is_symlink():
            raise ValueError("Composition bundle destination appeared; it was not replaced")
        _publish_bundle(staged, destination)
    return {**verified, "path": str(destination)}


def prepare_input(root: Path, identity: str, version: str, instance: str, grant: dict, task: bytes,
                  destination: Path, max_prompt_bytes: int) -> dict:
    """Atomically export a complete, bounded, operator-supplied leaf input; never run it."""
    composition = preview(root, identity, version, grant)
    request, prompt = _input_fields(composition, instance, task, max_prompt_bytes)
    return _prepare_bundle(root, composition, destination,
        {"request.json": _encoded(request), "task.txt": task, "prompt.txt": prompt}, inspect_input)


def prepare_manifest(root: Path, identity: str, version: str, grant: dict, destination: Path) -> dict:
    """Freeze the complete static composition without inventing future input/port values."""
    composition = preview(root, identity, version, grant)
    return _prepare_bundle(root, composition, destination, {"manifest.json": _encoded(_manifest_fields(composition))}, inspect_manifest)


def prepare_input_from_manifest(source: Path, instance: str, task: bytes, destination: Path, max_prompt_bytes: int) -> dict:
    """Use a complete static package only after fresh admission of its original graph."""
    checked = inspect_manifest(source, material=True)
    if destination.expanduser().resolve().is_relative_to(Path(checked["path"]).resolve()):
        raise ValueError("Composition input cannot be written inside its source manifest")
    root = Path(checked["path"]) / "assets"
    reference = checked["manifest"]["root"]
    composition = preview(root, reference["id"], reference["version"], checked["manifest"]["grant"])
    if _encoded(composition) != _encoded(checked["composition"]):
        raise ValueError("Composition manifest changed before input admission")
    request, prompt = _input_fields(composition, instance, task, max_prompt_bytes)
    return _prepare_bundle(root, composition, destination,
        {"request.json": _encoded(request), "task.txt": task, "prompt.txt": prompt}, inspect_input)
