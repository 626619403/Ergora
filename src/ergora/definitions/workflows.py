"""Static, bounded composition; no model calls, scheduler, or execution authorization."""

from copy import deepcopy
import base64
from graphlib import CycleError, TopologicalSorter
import hashlib
import ipaddress
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from urllib.parse import urlsplit

import ergora.definitions.agents as agent_definitions
import ergora.definitions.bundles as definition_bundles
from ergora.configuration import validation as contracts
from ergora.storage.assets import inventory_tree, publish_directory
from ergora.storage.state import State, file_lock
from ergora._paths import DATA_ROOT


_PRESETS = DATA_ROOT / "presets"
_IMPACT_SELECTION = {
    "$defs": contracts.WORKFLOW_DEFINITION["$defs"],
    "type": "object", "additionalProperties": False, "required": ["schema_version", "roots"],
    "properties": {
        "schema_version": {"type": "integer", "const": 1},
        "roots": {
            "type": "array", "minItems": 1, "maxItems": 16, "uniqueItems": True,
            "items": {
                "type": "object", "additionalProperties": False, "required": ["ref", "grant"],
                "properties": {
                    "ref": {
                        **contracts.WORKFLOW_DEFINITION["$defs"]["reference"],
                        "properties": {
                            "kind": {"const": "workflow"}, "id": {"$ref": "#/$defs/id"},
                            "version": contracts.WORKFLOW_DEFINITION["properties"]["version"],
                            "digest": {"$ref": "#/$defs/digest"},
                        },
                    },
                    "grant": {"$ref": "#/$defs/grant"},
                },
            },
        },
    },
}


def _preset_catalog() -> dict:
    catalog = definition_bundles.read_json(_PRESETS / "presets.json")
    if catalog["schema_version"] != 1:
        raise ValueError("Unsupported bundled preset catalog version")
    return catalog["presets"]


def presets() -> list[dict]:
    """List shipped recipes without creating State or probing execution tools."""
    return [{"id": identity, "description": entry["description"], "runtime": entry["runtime"],
             "root": _reference(inspect_bundle(_PRESETS / "workflows" / entry["root"]), "workflow"),
             **({"starter": _reference(inspect_bundle(_PRESETS / "workflows" / entry["starter_root"]), "workflow")}
                if "starter_root" in entry else {})}
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


def _check_bundle(root: Path, path: Path, *, material=False, inspect_revision=None) -> dict:
    document = inspect_bundle(path, material=True)
    definition = document["definition"]
    grant = {"schema_version": 1, "permissions": definition["permissions"], "limits": definition["limits"]}
    if inspect_revision is None:
        _Compilation(root, grant, agent_admission=agent_definitions.validate_admission).compile(document)
    else:
        document["impact"] = inspect_revision(document, grant)
    if not material:
        for resource in document["resources"]:
            del resource["text"]
    return document


def library(root: Path) -> definition_bundles.DefinitionLibrary:
    def checked(path, *, material=False):
        return _check_bundle(root, path, material=material)
    return definition_bundles.DefinitionLibrary(root, "workflow", contracts.WORKFLOW_DEFINITION, inspect_bundle,
                                              import_inspector=checked)


def _reference(document: dict, kind: str) -> dict:
    return {"kind": kind, "id": document["definition"]["id"], "version": document["definition"]["version"],
            "digest": document["digest"]}


def _ref_key(reference: dict) -> tuple[str, ...]:
    return tuple(reference[key] for key in ("kind", "id", "version", "digest"))


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


def _render_resource(item: dict) -> str:
    return (f"Resource {','.join(item['ids'])} ({item['kind']}); sources: " +
            json.dumps(item["sources"], sort_keys=True, ensure_ascii=False) + "\n" + item["text"])


class _MaterialLimitExceeded(ValueError):
    def __init__(self, leaf: dict, scope: dict):
        super().__init__(f"Composition material_bytes budget exceeded at {leaf['path']} (scope {scope['path']})")
        self.leaf, self.scope = leaf, scope


class _ReferenceUnavailable(ValueError):
    def __init__(self, reference: dict, path: str, error: Exception):
        super().__init__(str(error))
        self.reference, self.path = reference, path


class _Compilation:
    """One bounded traversal owns reference, graph, inheritance and budget checks."""

    def __init__(self, root: Path, grant: dict, *, agent_admission=None, measure=False, replacement=None):
        contracts.validate(grant, contracts.COMPOSITION_GRANT, "Composition preview grant")
        _permissions(grant["permissions"])
        self.root, self.grant = root, grant
        self.agent_admission = agent_admission
        self.measure, self.replacement = measure, replacement
        self.documents, self.instances = {}, []
        self.preview_version = 1
        self.total = {"path": "project", "limits": grant["limits"], "depth": 0, "instances": 0, "material_bytes": 0}
        self.scopes = [self.total]
        self.path = "root"
        self.replacements_seen = set()

    def _replaces(self, reference: dict, project: bool) -> bool:
        return project and self.replacement is not None and reference == self.replacement[0]

    def _resolve(self, reference: dict, path: str, *, project=False) -> dict:
        if self._replaces(reference, project):
            self.replacements_seen.add(path)
            return self.replacement[1]
        key = _ref_key(reference)
        if key not in self.documents:
            source = agent_definitions.library(self.root) if reference["kind"] == "agent" else library(self.root)
            try:
                document = source.get(reference["id"], reference["version"], material=True)
                if document["digest"] != reference["digest"]:
                    raise ValueError(f"Definition reference digest mismatch: {reference['id']}@{reference['version']}")
            except (ValueError, OSError) as error:
                if self.measure:
                    raise _ReferenceUnavailable(reference, path, error) from error
                raise
            if reference["kind"] == "agent" and self.agent_admission is not None:
                self.agent_admission(document)
            self.documents[key] = document
        return self.documents[key]

    def _routes(self, definition: dict, path: str, nodes: dict) -> dict:
        choices, controlled = {}, set()
        for identity, node in nodes.items():
            if node.get('operation') != 'choose-agent':
                continue
            self.path = f'{path}/{identity}'
            analyzer, = node['depends_on']
            if (node['inputs'] != {'source': {'node': analyzer, 'output': 'result'}}
                    or nodes.get(analyzer, {}).get('ref', {}).get('kind') != 'agent'):
                raise ValueError(f'Route selector requires the result of its sole sibling Agent dependency: {self.path}')
            if analyzer in choices:
                raise ValueError(f'An analyzer can supply only one route selector: {path}/{analyzer}')
            choices[analyzer] = [*node['branches'], 'none']
            for branch in node['branches']:
                target = nodes.get(branch, {})
                if target.get('ref', {}).get('kind') != 'agent' or identity not in target['depends_on']:
                    raise ValueError(f'Route branch must be a sibling Agent depending directly on its selector: {path}/{branch}')
                if branch in controlled:
                    raise ValueError(f'An Agent can belong to only one route selector: {path}/{branch}')
                controlled.add(branch)
        if controlled:
            for identity, node in nodes.items():
                if 'join' not in node and controlled.intersection(node['depends_on']):
                    self.path = f'{path}/{identity}'
                    raise ValueError(f'Conditional Agent dependencies require an all-join: {self.path}')
            if any(binding.get('node') in controlled for binding in definition['outputs'].values()):
                self.path = path
                raise ValueError(f'Conditional Agent outputs require an all-join: {path}')
        return choices

    def _links(self, definition: dict, path: str, *, project: bool) -> dict:
        nodes = {node["id"]: node for node in definition["nodes"]}
        choices = self._routes(definition, path, nodes)
        ports = {}
        for identity, node in nodes.items():
            self.path = f"{path}/{identity}"
            if "join" in node or "operation" in node or node["ref"]["kind"] == "agent":
                ports[identity] = ["result"]
            else:
                ports[identity] = list(self._resolve(node["ref"], self.path, project=project)["definition"]["outputs"])
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
            self.path = f"{path}/{node['id']}"
            if "operation" in node:
                expected = ["source"]
            elif node["ref"]["kind"] == "agent":
                expected = ["task"]
            else:
                expected = self._resolve(node["ref"], self.path, project=project)["definition"]["inputs"]
            if set(node["inputs"]) != set(expected):
                raise ValueError(f"Workflow input ports differ at {node['id']}: expected {expected}")
            for value in node["inputs"].values():
                binding(value, node["depends_on"])
        self.path = path
        for value in definition["outputs"].values():
            binding(value, nodes)
        return choices

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
        return "\n\n".join(_render_resource(item) for item in materials)

    def _workflow(self, document: dict, path: str, inherited: list[dict], ceiling: dict,
                  scopes: list[dict], lineage: tuple, inputs: dict, dependencies: list[str], *, project: bool) -> None:
        self.path = path
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
        if self.measure:
            scope["ref"] = reference
            self.scopes.append(scope)
        scopes = [*scopes, scope]
        self._count(scopes, path)
        materials = _materials(inherited, document, "workflow", path)
        _readable(materials, permissions, path)
        route_choices = self._links(definition, path, project=project)
        levels = _levels(definition)
        instance = {"path": path, "parent": path.rpartition("/")[0] or None, "kind": "workflow", "ref": reference,
                    "permissions": permissions, "inputs": inputs, "outputs": definition["outputs"], "depends_on": dependencies,
                    "levels": [[f"{path}/{name}" for name in level] for level in levels], "limits": definition["limits"]}
        self.instances.append(instance)
        nodes = {node["id"]: node for node in definition["nodes"]}
        for level in levels:
            for name in level:
                node, child_path = nodes[name], f"{path}/{name}"
                self.path = child_path
                dependencies = [f"{path}/{value}" for value in node["depends_on"]]
                if "join" in node:
                    self._count(scopes, child_path)
                    self.instances.append({"path": child_path, "parent": path, "kind": "join", "join": "all",
                                           "depends_on": dependencies, "outputs": ["result"], "permissions": permissions})
                elif "operation" in node:
                    self._count(scopes, child_path)
                    self.instances.append({"path": child_path, "parent": path, "kind": node["operation"],
                                           "depends_on": dependencies, "inputs": node["inputs"],
                                           "outputs": ["result"], "permissions": permissions,
                                           **({"branches": [f"{path}/{branch}" for branch in node["branches"]]}
                                              if node["operation"] == "choose-agent" else {})})
                elif node["ref"]["kind"] == "workflow":
                    child = self._resolve(node["ref"], child_path, project=project)
                    self._workflow(child, child_path, materials, permissions,
                                   scopes, (*lineage, identity), node["inputs"], dependencies,
                                   project=project and not self._replaces(node["ref"], project))
                else:
                    self._count(scopes, child_path)
                    child = self._resolve(node["ref"], child_path)
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
                            raise _MaterialLimitExceeded({"path": child_path, "ref": node["ref"],
                                "resources": selected, "material_bytes": size}, active)
                    self.instances.append({"path": child_path, "parent": path, "kind": "agent", "ref": node["ref"],
                                           "role": node["role"], "backend_request": child["definition"]["backend"],
                                           **({"invocation_minimum": child["definition"]["invocation_minimum"]}
                                              if "invocation_minimum" in child["definition"] else {}),
                                           **({"review_requirement": node["review_requirement"]}
                                              if "review_requirement" in node else {}),
                                           **({"route_choices": route_choices[name]} if name in route_choices else {}),
                                           "depends_on": dependencies, "inputs": node["inputs"], "outputs": ["result"],
                                           "permissions": node["permissions"], "resources": selected, "prompt": prompt,
                                           "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                                           "material_bytes": size,
                                           "concurrency_scopes": [{"path": active["path"], "limit": active["limits"]["concurrency"]}
                                                                  for active in scopes]})
        instance["usage"] = {key: scope[key] for key in ("instances", "material_bytes")}
        scope["complete"] = True

    def walk(self, document: dict, *, project=False) -> None:
        self._workflow(document, "root", [], self.grant["permissions"], [self.total], (),
                       {name: {"input": name} for name in document["definition"]["inputs"]}, [], project=project)
        self.total["complete"] = True

    def compile(self, document: dict) -> dict:
        self.walk(document)
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
           preview_resources: bool = False, impact: dict | None = None) -> dict:
    if impact is not None:
        if publish:
            raise ValueError("Workflow revision impact requires a read-only revision check")
        return revision_impact(state.root, identity, version, base_digest, definition, selection=impact,
            resource_changes=resource_changes, accepted_candidate=accepted_candidate, preview_resources=preview_resources)
    return library(state.root).revise(identity, version, base_digest, definition, publish=publish,
        resource_changes=resource_changes, accepted_candidate=accepted_candidate, preview_resources=preview_resources)


def _measure_leaf(leaf: dict) -> dict:
    resources = [{
        "ids": item["ids"], "kind": item["kind"], "content_digest": item["content_digest"],
        "sources": item["sources"], "inline_bytes": len(item["text"].encode("utf-8")),
        "rendered_bytes": len(_render_resource(item).encode("utf-8")) + (2 if index else 0),
    } for index, item in enumerate(leaf["resources"])]
    return {"path": leaf["path"], "ref": leaf["ref"], "material_bytes": leaf["material_bytes"], "resources": resources}


def _measure(root: Path, grant: dict, *, document=None, reference=None,
             replacement=None) -> tuple[dict, list[dict], list[str]]:
    """Use original compiler stops, including the first failed material charge."""
    try:
        compilation = _Compilation(root, grant, agent_admission=agent_definitions.validate_admission,
                                   measure=True, replacement=replacement)
    except ValueError as error:
        return {"status": "blocked", "scopes": [], "leaves": [],
                "blocker": {"path": "root", "reason": str(error)}}, [], []
    result = {"status": "checked"}
    try:
        if document is None:
            document = compilation._resolve(reference, "root", project=True)
        compilation.walk(document, project=replacement is not None and reference != replacement[0])
    except _MaterialLimitExceeded as error:
        result.update(status="blocked", blocker={
            "path": error.leaf["path"], "scope": error.scope["path"], "reason": str(error),
            "observed_material_bytes": error.scope["material_bytes"],
            "limit": error.scope["limits"]["material_bytes"], "attempted_leaf": _measure_leaf(error.leaf),
        })
    except _ReferenceUnavailable as error:
        result.update(status="unverified", blocker={"path": error.path, "reference": error.reference, "reason": str(error)})
    except (ValueError, OSError) as error:
        result.update(status="blocked", blocker={"path": compilation.path, "reason": str(error)})
    result["scopes"] = [{
        "path": item["path"], "ref": item.get("ref"), "complete": item.get("complete", False),
        "material_bytes": item["material_bytes"], "limit": item["limits"]["material_bytes"],
        "remaining_bytes": item["limits"]["material_bytes"] - item["material_bytes"],
    } for item in compilation.scopes]
    result["leaves"] = [_measure_leaf(item) for item in compilation.instances if item["kind"] == "agent"]
    reached_replacements = [item["path"] for item in compilation.instances
                            if item["kind"] == "workflow" and item["path"] in compilation.replacements_seen]
    return result, compilation.instances, reached_replacements


def _collect_parent_updates(root: dict, instances: list[dict], paths: list[str], updates: dict,
                            base: dict, replacement: dict) -> None:
    by_path = {item["path"]: item for item in instances}
    for path in paths:
        item = by_path[path]
        while item["parent"] is not None:
            parent = by_path[item["parent"]]
            plan = updates.setdefault(_ref_key(parent["ref"]), {"ref": parent["ref"], "references": []})
            site = {"root": root, "path": item["path"], "node": item["path"].rsplit("/", 1)[-1],
                    "before": item["ref"], "replacement": replacement if item["ref"] == base else None}
            if site not in plan["references"]:
                plan["references"].append(site)
            item = parent


def _observed_leaves(phase: dict) -> dict[str, str]:
    observed = {item["path"]: "measured" for item in phase["leaves"]}
    attempt = phase.get("blocker", {}).get("attempted_leaf")
    if attempt is not None:
        observed[attempt["path"]] = "attempted"
    return observed


def _leaf_coverage(paths: list[str], before: dict, after: dict | None, standalone: dict) -> list[dict]:
    old = _observed_leaves(before)
    new = _observed_leaves(after) if after is not None else {}
    expected = {path + leaf.removeprefix("root") for path in paths for leaf in _observed_leaves(standalone)}
    rows = []
    for leaf in sorted(old.keys() | new.keys() | expected):
        if not any(leaf.startswith(path + "/") for path in paths):
            continue
        if after is not None and after["status"] == "checked":
            projected = "absent"
        else:
            projected = "unreached" if after is not None and leaf in expected else "unverified"
        rows.append({"path": leaf, "baseline": old.get(leaf, "absent" if before["status"] == "checked" else "unverified"),
                     "projection": new.get(leaf, projected)})
    return rows


def _revision_report(root: Path, base: dict, document: dict, grant: dict, selection: dict) -> dict:
    proposed = _reference(document, "workflow")
    standalone, _, _ = _measure(root, grant, document=document)
    results, updates = [], {}
    for chosen in selection["roots"]:
        reference, root_grant = chosen["ref"], chosen["grant"]
        before, instances, _ = _measure(root, root_grant, reference=reference)
        paths = [item["path"] for item in instances if item.get("ref") == base]
        row = {**chosen, "baseline": before, "projection": None, "status": before["status"],
               "affected_paths": paths, "affected_leaves": [], "leaf_coverage": [], "comparison_complete": False}
        results.append(row)
        _collect_parent_updates(reference, instances, paths, updates, base, proposed)
        after = None
        if before["status"] == "checked" and not paths:
            row["status"] = "unaffected"
        elif before["status"] == "checked" or "attempted_leaf" in before.get("blocker", {}):
            after, projected, replacements = _measure(root, root_grant, reference=reference, replacement=(base, document))
            row.update(status=after["status"], projection=after,
                       comparison_complete=before["status"] == after["status"] == "checked")
            # The reached sites were resolved from the original exact pins.
            original_sites = [{**item, "ref": base} if item["path"] in replacements else item for item in projected]
            _collect_parent_updates(reference, original_sites, replacements, updates, base, proposed)
            row["affected_paths"] = list(dict.fromkeys([*paths, *replacements]))
        coverage = _leaf_coverage(row["affected_paths"], before, after, standalone)
        row["leaf_coverage"] = coverage
        row["affected_leaves"] = [item["path"] for item in coverage]
    order = TopologicalSorter({
        owner: sorted({_ref_key(site["before"]) for site in plan["references"]} & updates.keys())
        for owner, plan in updates.items()
    })
    statuses = {standalone["status"], *(item["status"] for item in results)}
    status = "blocked" if "blocked" in statuses else "unverified" if "unverified" in statuses else "checked"
    return {"schema_version": 1, "status": status, "executable": False, "coverage": "selected-roots",
            "base": base, "candidate": {"ref": proposed, "standalone": standalone}, "roots": results,
            "required_parent_revisions": [updates[key] for key in order.static_order()]}


def revision_impact(root: Path, identity: str, version: str, base_digest: str, definition: dict, *,
                    selection: dict, resource_changes: dict | None = None, accepted_candidate: dict | None = None,
                    preview_resources: bool = False) -> dict:
    """Check an exact draft and project its substitution into explicitly selected roots."""
    contracts.validate(selection, _IMPACT_SELECTION, "Workflow revision impact selection")
    base = {"kind": "workflow", "id": identity, "version": version, "digest": base_digest}

    def inspect_revision(document, grant):
        return _revision_report(root, base, document, grant, selection)

    def inspect_check(path):
        return _check_bundle(root, path, inspect_revision=inspect_revision)

    result = library(root).revise(identity, version, base_digest, definition, resource_changes=resource_changes,
        accepted_candidate=accepted_candidate, preview_resources=preview_resources, inspect_check=inspect_check)
    if result["impact"]["candidate"]["standalone"]["status"] != "checked":
        result.pop("candidate", None)
    return result


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


def compile_input(composition: dict, instance: str, task: bytes, max_prompt_bytes: int, *,
                  input_origin: str = "operator-supplied") -> tuple[dict, bytes]:
    """Compile complete leaf prompt bytes without writing or authorizing a call."""
    contracts.validate(max_prompt_bytes, contracts.COMPOSITION_INPUT["properties"]["max_prompt_bytes"], "Input byte limit")
    contracts.validate(input_origin, contracts.COMPOSITION_INPUT["properties"]["input_origin"], "Input origin")
    if len(task) > contracts.COMPOSITION_INPUT["properties"]["max_prompt_bytes"]["maximum"]:
        raise ValueError("Composition task exceeds the supported input byte limit")
    text = task.decode("utf-8-sig")
    if not text.strip() or "\0" in text:
        raise ValueError("Composition task must be nonempty UTF-8 text without NUL")
    selected = next((item for item in composition["instances"] if item["path"] == instance and item["kind"] == "agent"), None)
    if selected is None:
        raise ValueError(f"Select an Agent leaf instance: {instance}")
    label = {"operator-supplied": "Operator supplied task (workflow ports have not been executed):",
             "workflow-port": "Workflow task port (JSON value):"}[input_origin]
    prompt = (selected["prompt"] + "\n\n" + label + "\n" + text).encode("utf-8")
    if len(prompt) > max_prompt_bytes:
        raise ValueError(f"Complete composition prompt exceeds the input byte limit: {len(prompt)} > {max_prompt_bytes}")
    document = {"schema_version": 1, "kind": "composition-input", "execution_authorized": False,
                "root": composition["root"], "instance": instance, "grant": composition["grant"],
                "input_origin": input_origin, "task_sha256": hashlib.sha256(task).hexdigest(),
                "preview_sha256": composition["preview_sha256"], "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
                "prompt_bytes": len(prompt), "max_prompt_bytes": max_prompt_bytes}
    contracts.validate(document, contracts.COMPOSITION_INPUT, "Composition input")
    return document, prompt


def _manifest_fields(composition: dict) -> dict:
    return {"schema_version": 1, "kind": "composition-manifest", "execution_authorized": False,
            "root": composition["root"], "grant": composition["grant"], "preview_sha256": composition["preview_sha256"]}


def _inspect_snapshot(source: Path, *, leaf_input: bool, material: bool, include_inventory: bool = False) -> dict:
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
    expected, prompt = (compile_input(composition, request["instance"], (source / "task.txt").read_bytes(),
                                      request["max_prompt_bytes"], input_origin=request["input_origin"])
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
            **({"inventory": files} if include_inventory else {}),
            **({"prompt": prompt.decode("utf-8")} if material and leaf_input else {})}


def inspect_input(source: Path, *, material: bool = False) -> dict:
    """Verify a saved input and all its assets without today's backend admission."""
    return _inspect_snapshot(source, leaf_input=True, material=material)


def inspect_manifest(source: Path, *, material: bool = False, include_inventory: bool = False) -> dict:
    """Verify a complete static graph and optionally return its verified file inventory."""
    return _inspect_snapshot(source, leaf_input=False, material=material, include_inventory=include_inventory)


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
            publish_directory(staged, destination)
    if checked['digest'] != snapshot['digest']:
        raise ValueError('Frozen composition manifest changed')
    return {**checked, 'path': str(destination)}


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
        publish_directory(staged, destination)
    return {**verified, "path": str(destination)}


def prepare_input(root: Path, identity: str, version: str, instance: str, grant: dict, task: bytes,
                  destination: Path, max_prompt_bytes: int) -> dict:
    """Atomically export a complete, bounded, operator-supplied leaf input; never run it."""
    composition = preview(root, identity, version, grant)
    request, prompt = compile_input(composition, instance, task, max_prompt_bytes)
    return _prepare_bundle(root, composition, destination,
        {"request.json": _encoded(request), "task.txt": task, "prompt.txt": prompt}, inspect_input)


def prepare_manifest(root: Path, identity: str, version: str, grant: dict, destination: Path) -> dict:
    """Freeze the complete static composition without inventing future input/port values."""
    composition = preview(root, identity, version, grant)
    return _prepare_bundle(root, composition, destination, {"manifest.json": _encoded(_manifest_fields(composition))}, inspect_manifest)


def frozen_manifest(root: Path, preview_sha256: str, *, material: bool = False) -> dict:
    """Read an original complete package by its accepted preview, without live admission."""
    contracts.validate(preview_sha256, contracts.COMPOSITION_MANIFEST["$defs"]["digest"], "Preview SHA256")
    checked = inspect_manifest(root / "composition-manifests" / preview_sha256, material=material)
    if checked["manifest"]["preview_sha256"] != preview_sha256:
        raise ValueError("Frozen composition does not match its preview location")
    return checked


def freeze_manifest(root: Path, identity: str, version: str, grant: dict, preview_sha256: str) -> dict:
    """Persist only the accepted current preview; retries verify rather than replace."""
    contracts.validate(preview_sha256, contracts.COMPOSITION_MANIFEST["$defs"]["digest"], "Preview SHA256")
    composition = preview(root, identity, version, grant)
    if composition["preview_sha256"] != preview_sha256:
        raise ValueError("Composition preview changed; review the current preview before freezing")
    destination = root / "composition-manifests" / preview_sha256
    with file_lock(root / ".composition-manifests.lock"):
        if destination.exists() or destination.is_symlink():
            return frozen_manifest(root, preview_sha256)
        return _prepare_bundle(root, composition, destination,
            {"manifest.json": _encoded(_manifest_fields(composition))}, inspect_manifest)


def prepare_input_from_manifest(source: Path, instance: str, task: bytes, destination: Path, max_prompt_bytes: int, *,
                                input_origin: str = "operator-supplied", manifest_digest: str | None = None) -> dict:
    """Use a complete static package only after fresh admission of its original graph."""
    checked = inspect_manifest(source, material=True)
    if manifest_digest is not None and checked["digest"] != manifest_digest:
        raise ValueError("Composition manifest differs from the explicitly selected digest")
    if destination.expanduser().resolve().is_relative_to(Path(checked["path"]).resolve()):
        raise ValueError("Composition input cannot be written inside its source manifest")
    root = Path(checked["path"]) / "assets"
    reference = checked["manifest"]["root"]
    composition = preview(root, reference["id"], reference["version"], checked["manifest"]["grant"])
    if _encoded(composition) != _encoded(checked["composition"]):
        raise ValueError("Composition manifest changed before input admission")
    request, prompt = compile_input(composition, instance, task, max_prompt_bytes, input_origin=input_origin)
    return _prepare_bundle(root, composition, destination,
        {"request.json": _encoded(request), "task.txt": task, "prompt.txt": prompt}, inspect_input)
