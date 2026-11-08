"""Complete static graphs travel independently of their source catalog or runtime."""

import hashlib
import json
import shutil

import pytest

from ergora import agent_definitions, agents, backups, contracts, workflow_definitions as workflows
from ergora.asset_trees import digest_tree
from ergora.cli import main
from test_workflow_definitions import EXAMPLES, base, child, definition, grant, imported, leaf, ref, write_bundle


def test_manifest_preserves_all_instances_inherited_assets_and_backup_without_live_catalog(base, monkeypatch, capsys):
    contracts.StrictValidator.check_schema(contracts.COMPOSITION_MANIFEST)
    state, agent, directory = base
    sub = imported(base, definition("sub", [leaf("review", agent)]), "Child instructions. 子材料。\n")
    source = write_bundle(directory / "root-source",
        definition("outer", [child("alpha", ref(sub, "workflow")), child("beta", ref(sub, "workflow"))]),
        "Root instructions. 祖先材料。\n")
    skill = source / "skills/kernel-measurement"
    shutil.copytree(EXAMPLES / "agents/kernel-implementer/skills/kernel-measurement", skill)
    doc = json.loads((source / "workflow.json").read_text())
    doc["resources"].append({"id": "inherited-measurement", "kind": "skill", "path": "skills/kernel-measurement",
                             "digest": digest_tree(skill)[0]})
    (source / "workflow.json").write_text(json.dumps(doc), encoding="utf-8")
    workflows.import_bundle(state, source)
    target = state.root / "manifests/frozen"
    original = workflows.preview(state.root, "outer", "1.0.0", grant())
    saved = workflows.prepare_manifest(state.root, "outer", "1.0.0", grant(), target)
    checked = workflows.inspect_manifest(target, material=True)
    assert checked["digest"] == saved["digest"] and checked["composition"] == original
    assert checked["manifest"]["execution_authorized"] is False and "request" not in checked and "prompt" not in checked
    assert not (target / "task.txt").exists() and not (target / "prompt.txt").exists()
    leaves = [item for item in checked["composition"]["instances"] if item["kind"] == "agent"]
    assert {item["path"] for item in leaves} == {"root/alpha/review", "root/beta/review"}
    for item in leaves:
        assert item["prompt"].index("Root instructions.") < item["prompt"].index("Child instructions.")
        assert (skill / "SKILL.md").read_text() in item["prompt"]
        assert all(origin["instance"] in ("root", item["parent"], item["path"])
                   for resource in item["resources"] for origin in resource["sources"])
    assert len(list((target / "assets/workflow-definitions/objects").iterdir())) == 2
    assert len(list((target / "assets/agent-definitions/objects").iterdir())) == 1
    backups.create(state.root, directory / "backup", offline=True)
    shutil.rmtree(state.root)
    backups.restore(state.root, directory / "backup", offline=True)
    assert workflows.inspect_manifest(target, material=True) == checked

    def reject(*args, **kwargs):
        raise ValueError("Current backend policy rejected")

    monkeypatch.setattr(agents, "validate_binding", reject)
    assert workflows.inspect_manifest(target)["digest"] == saved["digest"]
    with pytest.raises(ValueError, match="Current backend policy"):
        workflows.prepare_manifest(state.root, "outer", "1.0.0", grant(), directory / "denied")
    with pytest.raises(ValueError, match="Current backend policy"):
        workflows.prepare_input_from_manifest(target, "root/alpha/review", b"Review.", directory / "denied-input", 30000)
    assert not (directory / "denied-input").exists()
    monkeypatch.undo()
    shared = directory / "shared"
    shutil.copytree(target, shared)
    shutil.rmtree(state.root)
    assert main(["--home", str(state.root), "composition", "verify-manifest", str(shared), "--material"]) == 0
    exported = json.loads(capsys.readouterr().out)
    assert exported["digest"] == saved["digest"] and exported["composition"] == original
    assert not state.root.exists()
    task = directory / "task.txt"
    task.write_bytes("Review the supplied candidate. 核对候选。\r\n".encode())
    input_path = directory / "prepared-from-manifest"
    assert main(["--home", str(state.root), "composition", "prepare-from-manifest", str(shared), "root/alpha/review",
                 "--task", str(task), "--directory", str(input_path), "--max-prompt-bytes", "30000"]) == 0
    prepared = json.loads(capsys.readouterr().out)
    assert prepared["request"]["root"] == saved["manifest"]["root"]
    assert prepared["request"]["preview_sha256"] == original["preview_sha256"]
    assert workflows.inspect_input(input_path, material=True)["prompt"].endswith(task.read_bytes().decode())
    assert not state.root.exists()


@pytest.mark.parametrize("damage", ["authority", "identity", "graph", "asset", "foreign-file", "foreign-definition"])
def test_manifest_reconstructs_graph_and_exact_assets_instead_of_accepting_claimed_digests(base, damage):
    state, agent, directory = base
    imported(base, definition("review", [leaf("review", agent)]), "Required parent instructions.\n")
    target = directory / "manifest"
    workflows.prepare_manifest(state.root, "review", "1.0.0", grant(), target)
    if damage in ("authority", "identity"):
        path = target / "manifest.json"
        document = json.loads(path.read_text())
        document["execution_authorized" if damage == "authority" else "preview_sha256"] = True if damage == "authority" else "0" * 64
        path.write_text(json.dumps(document), encoding="utf-8")
    elif damage == "graph":
        path = target / "composition.json"
        document = json.loads(path.read_text())
        document["instances"][-1]["prompt"] = "Ancestor instructions silently removed."
        document["instances"][-1]["prompt_sha256"] = hashlib.sha256(document["instances"][-1]["prompt"].encode()).hexdigest()
        path.write_text(json.dumps(document), encoding="utf-8")
    elif damage == "asset":
        next((target / "assets/agent-definitions/objects").glob("*/instructions.md")).write_bytes(b"Different instructions.")
    elif damage == "foreign-file":
        (target / "undeclared.txt").write_bytes(b"Unreferenced material.")
    else:
        foreign = write_bundle(directory / "foreign", definition("foreign", [leaf("review", agent)]))
        workflows.library(target / "assets").import_bundle(foreign)
        (target / "assets/.workflow-definitions.lock").unlink()
    with pytest.raises(ValueError):
        workflows.inspect_manifest(target)


def test_manifest_copy_loss_leaves_no_destination_and_source_stays_readable(base, monkeypatch):
    state, agent, directory = base
    imported(base, definition("review", [leaf("review", agent)]))
    original = agent_definitions.library(state.root).__class__.import_bundle

    def interrupted(store, source):
        result = original(store, source)
        if store.kind == "workflow":
            raise OSError("lost manifest publication")
        return result

    monkeypatch.setattr(agent_definitions.library(state.root).__class__, "import_bundle", interrupted)
    with pytest.raises(OSError, match="lost manifest publication"):
        workflows.prepare_manifest(state.root, "review", "1.0.0", grant(), directory / "manifest")
    assert not (directory / "manifest").exists() and not list(directory.glob(".composition-bundle-*"))
    assert workflows.preview(state.root, "review", "1.0.0", grant())["usage"]["instances"] == 2


@pytest.mark.parametrize("relative", ["review-input", "nested/review-input"])
def test_preparing_leaf_inside_manifest_is_rejected_without_changing_its_tree(base, relative):
    state, agent, directory = base
    imported(base, definition("review", [leaf("review", agent)]))
    source = directory / "manifest"
    saved = workflows.prepare_manifest(state.root, "review", "1.0.0", grant(), source)
    with pytest.raises(ValueError, match="inside its source manifest"):
        workflows.prepare_input_from_manifest(source, "root/review", b"Review.", source / relative, 30000)
    assert workflows.inspect_manifest(source)["digest"] == saved["digest"]
    assert not (source / relative.split("/")[0]).exists()
