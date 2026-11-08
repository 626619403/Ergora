"""Composition contracts through the public package, library and preview interfaces."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import agent_definitions, backups, contracts, skill_assets, workflow_definitions as workflows
from ergora.asset_trees import digest_tree
from ergora.state import State


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
READ = {"read": ["workspace", "definitions"], "write": [], "shell": False, "network": []}
LIMITS = {"depth": 8, "instances": 128, "concurrency": 4, "material_bytes": 262144}


def ref(document, kind):
    return {"kind": kind, "id": document["definition"]["id"], "version": document["definition"]["version"],
            "digest": document["digest"]}


def write_bundle(path, definition, text=None):
    path.mkdir(parents=True, exist_ok=True)
    if text is not None:
        (path / "instructions.md").write_bytes(text.encode("utf-8"))
        definition["resources"] = [{"id": definition["id"] + "-instructions", "kind": "instructions",
                                     "path": "instructions.md", "sha256": hashlib.sha256(text.encode()).hexdigest()}]
    (path / "workflow.json").write_text(json.dumps(definition, indent=2) + "\n", encoding="utf-8")
    return path


def definition(identity, nodes):
    return {"schema_version": 1, "id": identity, "version": "1.0.0", "description": "Test workflow contract",
            "resources": [], "permissions": deepcopy(READ), "limits": deepcopy(LIMITS), "inputs": ["task"],
            "outputs": {"result": {"node": nodes[-1]["id"], "output": "result"}}, "nodes": deepcopy(nodes)}


def leaf(identity, agent):
    return {"id": identity, "ref": agent, "role": "reviewer", "depends_on": [],
            "inputs": {"task": {"input": "task"}}, "permissions": deepcopy(READ)}


def child(identity, workflow):
    return {"id": identity, "ref": workflow, "depends_on": [], "inputs": {"task": {"input": "task"}}}


def grant(**limits):
    return {"schema_version": 1, "permissions": deepcopy(READ), "limits": {**LIMITS, **limits}}


@pytest.fixture
def base(tmp_path):
    state = State(tmp_path / "state")
    agent = agent_definitions.import_bundle(state, EXAMPLES / "agents/architecture-reviewer")
    return state, ref(agent, "agent"), tmp_path


def imported(base, document, text=None):
    state, _, directory = base
    source = write_bundle(directory / (document["id"] + "-" + document["version"]), document, text)
    return workflows.import_bundle(state, source)


def test_examples_expand_serial_and_parallel_all_join_without_dependency_inheritance(tmp_path):
    contracts.StrictValidator.check_schema(contracts.WORKFLOW_DEFINITION)
    contracts.StrictValidator.check_schema(contracts.COMPOSITION_GRANT)
    state = State(tmp_path / "state")
    for source in sorted((EXAMPLES / "agents").iterdir()):
        agent_definitions.import_bundle(state, source)
    for source in sorted((EXAMPLES / "composition/agents").iterdir()):
        agent_definitions.import_bundle(state, source)
    for name in ("structure-review", "correctness-review", "test-value-review", "parallel-review", "kernel-delivery"):
        workflows.import_bundle(state, EXAMPLES / "composition" / name)
    permissions = json.loads((EXAMPLES / "composition/preview-grant.json").read_text())
    result = workflows.preview(state.root, "kernel-delivery", "1.0.0", permissions)
    assert result["executable"] is False and result["usage"]["instances"] == 10
    items = {item["path"]: item for item in result["instances"]}
    assert items["root"]["levels"] == [["root/implement"], ["root/review"]]
    assert len(items["root/review"]["levels"][0]) == 3
    assert set(items["root/review/gather"]["depends_on"]) == {
        "root/review/structure", "root/review/correctness", "root/review/test-value"}
    assert items["root/review"]["depends_on"] == ["root/implement"]
    assert len({item["path"] for item in result["instances"]}) == 10
    for item in items.values():
        if item["kind"] == "agent" and item["role"] == "reviewer":
            ids = [identity for resource in item["resources"] for identity in resource["ids"]]
            assert "kernel-measurement" not in ids and "kernel-delivery-instructions" in ids
            assert "parallel-review-instructions" in ids
            for resource in item["resources"]:
                assert resource["text"] in item["prompt"]
    assert workflows.preview(state.root, "kernel-delivery", "1.0.0", permissions) == result


def test_repeated_references_are_distinct_instances_and_preserve_ancestor_sources(base):
    state, agent, _ = base
    sub = imported(base, definition("sub", [leaf("review", agent)]), "Sub instructions.\n")
    outer = imported(base, definition("outer", [child("first", ref(sub, "workflow")), child("second", ref(sub, "workflow"))]),
                     "Root instructions.\n")
    result = workflows.preview(state.root, "outer", "1.0.0", grant(concurrency=1))
    agents = [item for item in result["instances"] if item["kind"] == "agent"]
    assert [item["path"] for item in agents] == ["root/first/review", "root/second/review"]
    for item in agents:
        assert item["prompt"].index("Root instructions.") < item["prompt"].index("Sub instructions.")
        assert [scope["limit"] for scope in item["concurrency_scopes"]] == [1, 4, 4]
        assert all(source["instance"] in ("root", item["parent"], item["path"])
                   for material in item["resources"] for source in material["sources"])
    assert agents[0]["prompt_sha256"] != agents[1]["prompt_sha256"]
    assert outer["definition"]["nodes"][0]["ref"] == outer["definition"]["nodes"][1]["ref"]


@pytest.mark.parametrize("failure", ["missing-ref", "digest", "role", "input", "output", "not-dependent", "child-input"])
def test_unresolvable_references_and_port_bindings_never_publish(base, failure):
    state, agent, directory = base
    doc = definition("broken", [leaf("first", agent), leaf("second", agent)])
    if failure == "missing-ref":
        doc["nodes"][0]["ref"] = {**agent, "id": "absent"}
    elif failure == "digest":
        doc["nodes"][0]["ref"] = {**agent, "digest": "0" * 64}
    elif failure == "role":
        doc["nodes"][0]["role"] = "implementer"
    elif failure == "input":
        doc["nodes"][0]["inputs"]["task"] = {"input": "absent"}
    elif failure == "output":
        doc["outputs"]["result"]["output"] = "absent"
    elif failure == "not-dependent":
        doc["nodes"][1]["inputs"]["task"] = {"node": "first", "output": "result"}
    else:
        del doc["nodes"][0]["inputs"]["task"]
    with pytest.raises(ValueError):
        workflows.import_bundle(state, write_bundle(directory / "broken", doc))
    assert workflows.definitions(state) == [] and not (state.root / "workflow-definitions").exists()


@pytest.mark.parametrize("failure", ["cycle", "duplicate", "unknown", "join-empty", "version", "limit-bool", "unknown-field"])
def test_local_graph_and_schema_are_checked_without_library_access(base, failure):
    _, agent, directory = base
    doc = definition("broken", [leaf("first", agent), leaf("second", agent)])
    if failure == "cycle":
        doc["nodes"][0]["depends_on"] = ["second"]
        doc["nodes"][1]["depends_on"] = ["first"]
    elif failure == "duplicate":
        doc["nodes"][1]["id"] = "first"
    elif failure == "unknown":
        doc["nodes"][0]["depends_on"] = ["absent"]
    elif failure == "join-empty":
        doc["nodes"] = [{"id": "first", "join": "all", "depends_on": []}]
    elif failure == "version":
        doc["schema_version"] = True
    elif failure == "limit-bool":
        doc["limits"]["instances"] = True
    else:
        doc["python_expression"] = "arbitrary()"
    with pytest.raises(ValueError):
        workflows.inspect_bundle(write_bundle(directory / "broken", doc))


@pytest.mark.parametrize("access,value", [("read", ["workspace-private"]), ("write", ["workspace"]),
                                         ("shell", True), ("network", ["https://api.example.com"])])
def test_descendants_cannot_broaden_any_permission(base, access, value):
    _, agent, _ = base
    doc = definition("escalation", [leaf("review", agent)])
    doc["nodes"][0]["permissions"][access] = value
    with pytest.raises(ValueError, match="Permission"):
        imported(base, doc)


@pytest.mark.parametrize("access,value", [("read", ["workspace-other"]), ("write", ["definitions"]),
                                         ("read", ["workspace/../private"]), ("network", ["https://user@api.example.com"]),
                                         ("network", ["https://api.example.com/path"]), ("network", ["https://api.example.com:99999"])])
def test_permission_mounts_paths_and_network_origins_have_unambiguous_meaning(base, access, value):
    _, agent, directory = base
    doc = definition("bad-permissions", [leaf("review", agent)])
    doc["permissions"][access] = value
    with pytest.raises(ValueError):
        workflows.inspect_bundle(write_bundle(directory / "bad-permissions", doc))


@pytest.mark.parametrize("access,value", [
    ("read", ["definitions/agent"]), ("read", ["definitions/agent/architecture-reviewer"]),
    ("read", ["definitions/workflow/Bad-ID/1.0.0"]), ("read", ["definitions/agent/architecture-reviewer/latest"]),
    ("network", ["https://*.example.com"]), ("network", ["https://api example.com"]),
    ("network", ["https://api.example.com:"]), ("network", ["https://api.example.com:443"]),
])
def test_illegal_definition_scopes_and_network_origins_rejected_for_definition_and_explicit_grant(base, access, value):
    state, agent, directory = base
    doc = definition("strict", [leaf("review", agent)])
    imported(base, doc)
    invalid_grant = grant()
    invalid_grant["permissions"][access] = value
    with pytest.raises(ValueError, match="Permission|Network"):
        workflows.preview(state.root, "strict", "1.0.0", invalid_grant)
    doc["permissions"][access] = value
    doc["nodes"][0]["permissions"][access] = value
    with pytest.raises(ValueError, match="Permission|Network"):
        workflows.import_bundle(state, write_bundle(directory / "invalid", doc))
    assert len(workflows.definitions(state)) == 1


def test_exact_version_scopes_dns_and_ip_origins_remain_supported(base):
    state, agent, _ = base
    doc = definition("strict", [leaf("review", agent)])
    permissions = {**READ, "read": ["workspace/src", "definitions/agent/architecture-reviewer/1.0.0"],
                   "network": ["https://api.example.com", "http://localhost:8765", "http://127.0.0.1", "https://[::1]:8443"]}
    doc["permissions"] = deepcopy(permissions)
    doc["nodes"][0]["permissions"] = deepcopy(permissions)
    imported(base, doc)
    actual = workflows.preview(state.root, "strict", "1.0.0", {**grant(), "permissions": permissions})
    assert actual["instances"][-1]["permissions"] == permissions


def test_narrowing_read_cannot_remove_required_inherited_material_even_when_agent_itself_is_readable(base):
    _, agent, _ = base
    doc = definition("inherited", [leaf("review", agent)])
    doc["nodes"][0]["permissions"]["read"] = ["definitions/agent/architecture-reviewer/1.0.0"]
    with pytest.raises(ValueError, match="Required inherited resource is not readable"):
        imported(base, doc, "Mandatory inherited material.\n")


@pytest.mark.parametrize("collision", ["id", "skill-name", "identical-skill"])
def test_resource_identity_and_real_skill_loading_name_conflicts(base, collision):
    state, agent, directory = base
    doc = definition("resources", [leaf("review", agent)])
    source = write_bundle(directory / "resources", doc)
    if collision == "id":
        (source / "other.md").write_text("Different instructions.\n")
        doc["resources"] = [{"id": "initial-instructions", "kind": "instructions", "path": "other.md",
                             "sha256": hashlib.sha256((source / "other.md").read_bytes()).hexdigest()}]
    else:
        skill = source / "skills/architecture-evidence"
        shutil.copytree(EXAMPLES / "agents/architecture-reviewer/skills/architecture-evidence", skill)
        if collision == "skill-name":
            with (skill / "SKILL.md").open("a", encoding="utf-8") as stream:
                stream.write("\nExtra instructions.\n")
        doc["resources"] = [{"id": "other-logical-id", "kind": "skill", "path": "skills/architecture-evidence",
                             "digest": skill_assets.digest_tree(skill)[0]}]
    write_bundle(source, doc)
    if collision != "identical-skill":
        with pytest.raises(ValueError, match="conflict"):
            workflows.import_bundle(state, source)
    else:
        workflows.import_bundle(state, source)
        result = workflows.preview(state.root, "resources", "1.0.0", grant())
        materials = result["instances"][-1]["resources"]
        skills = [item for item in materials if item["kind"] == "skill"]
        assert len(skills) == 1 and skills[0]["ids"] == ["other-logical-id", "architecture-evidence"]
        assert len(skills[0]["sources"]) == 2


def test_every_ancestor_and_the_project_bound_expansion_and_static_prompt_bytes(base):
    state, agent, _ = base
    sub = imported(base, definition("sub", [leaf("review", agent)]))
    imported(base, definition("outer", [child("one", ref(sub, "workflow")), child("two", ref(sub, "workflow"))]))
    result = workflows.preview(state.root, "outer", "1.0.0", grant())
    assert result["usage"]["instances"] == 5
    size = result["usage"]["material_bytes"]
    assert workflows.preview(state.root, "outer", "1.0.0", grant(material_bytes=size))["usage"] == result["usage"]
    for small in ({"depth": 2}, {"instances": 4}, {"material_bytes": size - 1}):
        with pytest.raises(ValueError, match="budget exceeded"):
            workflows.preview(state.root, "outer", "1.0.0", grant(**small))
    too_small = definition("local-limit", [leaf("review", agent)])
    too_small["limits"]["instances"] = 1
    with pytest.raises(ValueError, match="budget exceeded"):
        imported(base, too_small)


def test_new_parent_and_child_revision_can_raise_permissions_together_without_changing_old_root(base):
    state, agent, _ = base
    subdoc = definition("sub", [leaf("review", agent)])
    sub = imported(base, subdoc)
    rootdoc = definition("outer", [child("review", ref(sub, "workflow"))])
    imported(base, rootdoc)
    old = workflows.preview(state.root, "outer", "1.0.0", grant())
    subdoc["version"] = "1.0.1"
    for permissions in (subdoc["permissions"], subdoc["nodes"][0]["permissions"]):
        permissions["write"] = ["workspace/src"]
    newer_sub = imported(base, subdoc)
    rootdoc["version"] = "1.0.1"
    rootdoc["nodes"][0]["ref"] = ref(newer_sub, "workflow")
    with pytest.raises(ValueError, match="Permission exceeds"):
        imported(base, rootdoc)
    rootdoc["permissions"]["write"] = ["workspace/src"]
    imported(base, rootdoc)
    with pytest.raises(ValueError, match="Permission exceeds"):
        workflows.preview(state.root, "outer", "1.0.1", grant())
    updated_grant = grant()
    updated_grant["permissions"]["write"] = ["workspace/src"]
    new = workflows.preview(state.root, "outer", "1.0.1", updated_grant)
    assert new["instances"][-1]["permissions"]["write"] == ["workspace/src"]
    assert workflows.preview(state.root, "outer", "1.0.0", grant()) == old
    assert new["preview_sha256"] != old["preview_sha256"]


def test_workflow_versions_export_and_offline_backup_preserve_the_complete_reference_tree(base):
    state, agent, directory = base
    bundle = imported(base, definition("review", [leaf("review", agent)]), "Persistent instructions.\n")
    expected = workflows.preview(state.root, "review", "1.0.0", grant())
    exported = workflows.export(state, "review", "1.0.0", directory / "export")
    assert exported["digest"] == bundle["digest"]
    assert workflows.import_bundle(state, Path(exported["destination"])) == bundle
    changed = deepcopy(bundle["definition"])
    changed["description"] = "Different same-version content"
    with pytest.raises(ValueError, match="new version"):
        imported(base, changed)
    archive = directory / "backup"
    assert backups.create(state.root, archive, offline=True)["workflow_definitions"] == 1
    shutil.rmtree(state.root)
    backups.restore(state.root, archive, offline=True)
    assert workflows.preview(state.root, "review", "1.0.0", grant()) == expected
    # Even a self-consistent local object/index cannot mask a broken cross-library reference.
    object_path = Path(bundle["path"])
    definition_path = object_path / "workflow.json"
    corrupted = json.loads(definition_path.read_text())
    corrupted["nodes"][0]["ref"]["digest"] = "0" * 64
    definition_path.write_text(json.dumps(corrupted))
    new_digest = digest_tree(object_path)[0]
    object_path.rename(object_path.with_name(new_digest))
    index = state.root / "workflow-definitions/index.json"
    document = json.loads(index.read_text())
    document["definitions"]["review"]["1.0.0"] = new_digest
    index.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="reference digest mismatch"):
        backups.create(state.root, directory / "corrupt-backup", offline=True)


def test_failed_first_workflow_publication_leaves_no_library_and_can_retry(base, monkeypatch):
    state, agent, directory = base
    source = write_bundle(directory / "review", definition("review", [leaf("review", agent)]))
    original = Path.replace
    def interrupted(path, destination):
        if Path(destination).name == "index.json":
            raise OSError("interrupted reference publication")
        return original(path, destination)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", interrupted)
        with pytest.raises(OSError, match="interrupted"):
            workflows.import_bundle(state, source)
    assert not (state.root / "workflow-definitions").exists()
    assert backups.create(state.root, directory / "after-interruption", offline=True)["workflow_definitions"] == 0
    first = workflows.import_bundle(state, source)
    assert workflows.import_bundle(state, source) == first


def test_cli_check_and_failed_preview_do_not_create_state(tmp_path):
    absent = tmp_path / "absent"
    def cli(*arguments):
        return subprocess.run([sys.executable, "-m", "ergora", "--home", str(absent), "composition", *arguments],
                              capture_output=True, text=True, encoding="utf-8", timeout=30)
    checked = cli("check", str(EXAMPLES / "composition/parallel-review"), "--material")
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["resources"][0]["text"] and not absent.exists()
    missing = cli("preview", "parallel-review", "1.0.0", "--grant", str(EXAMPLES / "composition/preview-grant.json"))
    assert missing.returncode == 2 and "Unknown Workflow definition" in missing.stderr and not absent.exists()
