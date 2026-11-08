"""Static, bounded composition; no model calls, scheduler, or execution authorization."""

from copy import deepcopy
from graphlib import CycleError, TopologicalSorter
import hashlib
import ipaddress
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit

from . import agent_definitions, contracts, definition_bundles
from .state import State


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
    document = definition_bundles.inspect_bundle(source, "workflow.json", contracts.WORKFLOW_DEFINITION,
                                                 "Workflow", material=material)
    definition = document["definition"]
    _permissions(definition["permissions"])
    for node in definition["nodes"]:
        if "permissions" in node:
            _permissions(node["permissions"])
    _levels(definition)
    return document


def library(root: Path) -> definition_bundles.DefinitionLibrary:
    return definition_bundles.DefinitionLibrary(root, "workflow", contracts.WORKFLOW_DEFINITION, inspect_bundle)


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

    def __init__(self, root: Path, grant: dict):
        contracts.validate(grant, contracts.COMPOSITION_GRANT, "Composition preview grant")
        _permissions(grant["permissions"])
        self.root, self.grant = root, grant
        self.documents, self.instances = {}, []
        self.total = {"path": "project", "limits": grant["limits"], "depth": 0, "instances": 0, "material_bytes": 0}

    def _resolve(self, reference: dict, *, material: bool = False) -> dict:
        key = (reference["kind"], reference["id"], reference["version"], reference["digest"], material)
        if key not in self.documents:
            source = agent_definitions.library(self.root) if reference["kind"] == "agent" else library(self.root)
            document = source.get(reference["id"], reference["version"], material=material)
            if document["digest"] != reference["digest"]:
                raise ValueError(f"Definition reference digest mismatch: {reference['id']}@{reference['version']}")
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
        result = {"schema_version": 1, "kind": "composition-preview", "executable": False,
                  "root": _reference(document, "workflow"), "grant": self.grant, "instances": self.instances,
                  "usage": {key: self.total[key] for key in ("instances", "material_bytes")},
                  "pending": ["project admission and approved manifest", "backend permission and resource enforcement",
                              "runtime port values, complete input capacity and durable execution"]}
        return {**result, "preview_sha256": hashlib.sha256(_encoded(result)).hexdigest()}


def import_bundle(state: State, source: Path) -> dict:
    def checked(path, *, material=False):
        document = inspect_bundle(path, material=True)
        definition = document["definition"]
        grant = {"schema_version": 1, "permissions": definition["permissions"], "limits": definition["limits"]}
        _Compilation(state.root, grant).compile(document)
        if not material:
            for resource in document["resources"]:
                del resource["text"]
        return document
    return definition_bundles.DefinitionLibrary(state.root, "workflow", contracts.WORKFLOW_DEFINITION, checked).import_bundle(source)


def get(state: State, identity: str, version: str, *, material: bool = False) -> dict:
    return library(state.root).get(identity, version, material=material)


def definitions(state: State) -> list[dict]:
    return [{**item["definition"], "digest": item["digest"]} for item in library(state.root).documents()]


def export(state: State, identity: str, version: str, destination: Path) -> dict:
    return library(state.root).export(identity, version, destination)


def preview(root: Path, identity: str, version: str, grant: dict) -> dict:
    """Read a library without constructing State or changing any project configuration."""
    document = library(root).get(identity, version, material=True)
    return _Compilation(root, grant).compile(document)


def verify_store(root: Path) -> int:
    documents = library(root).documents()
    for document in documents:
        definition = document["definition"]
        preview(root, definition["id"], definition["version"],
                {"schema_version": 1, "permissions": definition["permissions"], "limits": definition["limits"]})
    return len(documents)
