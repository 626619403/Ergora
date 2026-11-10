"""Specialist bundles preserve exact identities without granting execution."""

from concurrent.futures import ThreadPoolExecutor
import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import agent_definitions as definitions
from ergora import agents, backups, contracts, definition_bundles, projects, skill_assets
from ergora.state import State


EXAMPLES = Path(__file__).resolve().parents[1] / "examples/agents"


@pytest.fixture
def bundle(tmp_path):
    source = tmp_path / "specialist"
    shutil.copytree(EXAMPLES / "kernel-implementer", source)
    return source


def revise(source, change):
    path = source / "agent.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    change(document)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def test_complementary_examples_material_and_filtering_share_backend_without_sharing_identity(tmp_path):
    contracts.StrictValidator.check_schema(contracts.AGENT_DEFINITION)
    state = State(tmp_path / "state")
    sources = [EXAMPLES / name for name in ("architecture-reviewer", "kernel-implementer")]
    imported = [definitions.import_bundle(state, path) for path in sources]
    assert len({item["digest"] for item in imported}) == len(sources)
    assert {item["definition"]["backend"]["tool"] for item in imported} == {"codex"}
    assert [item["id"] for item in definitions.definitions(state, role="reviewer")] == ["architecture-reviewer"]
    assert [item["id"] for item in definitions.definitions(state, specialty="cuda")] == ["kernel-implementer"]
    selected = definitions.get(state, "kernel-implementer", "1.0.0", material=True)
    for resource in selected["resources"]:
        path = Path(selected["path"]) / resource["path"]
        if resource["kind"] == "skill":
            assert skill_assets.digest_tree(path)[0] == resource["digest"]
            path /= "SKILL.md"
        assert resource["text"] == path.read_text(encoding="utf-8")


def test_versions_are_immutable_idempotent_and_export_roundtrips(bundle, tmp_path):
    state = State(tmp_path / "state")
    first = definitions.import_bundle(state, bundle)
    index_path = state.root / "agent-definitions/index.json"
    original_index = index_path.read_bytes()
    assert definitions.import_bundle(state, bundle) == first
    assert index_path.read_bytes() == original_index
    exported = definitions.export(state, "kernel-implementer", "1.0.0", tmp_path / "share")
    other = State(tmp_path / "other")
    assert definitions.import_bundle(other, Path(exported["destination"]))["digest"] == first["digest"]
    revise(bundle, lambda item: item.update(description="Changed recipe"))
    with pytest.raises(ValueError, match="new version"):
        definitions.import_bundle(state, bundle)
    assert index_path.read_bytes() == original_index
    revise(bundle, lambda item: item.update(version="1.0.1"))
    second = definitions.import_bundle(state, bundle)
    assert second["digest"] != first["digest"]
    assert definitions.get(state, "kernel-implementer", "1.0.0") == first
    assert len(definitions.definitions(state)) == 2
    with pytest.raises(ValueError, match="new Agent export"):
        definitions.export(state, "kernel-implementer", "1.0.0", tmp_path / "share")


def test_revision_preserves_complete_package_and_only_publishes_explicitly(bundle, tmp_path):
    skill = bundle / "skills/kernel-measurement"
    (skill / "references/empty").mkdir(parents=True)
    (skill / "references/opaque.bin").write_bytes(b"\x00\xff complete attachment")
    (bundle / "unlisted.bin").write_bytes(b"\xff preserved extra file")
    revise(bundle, lambda item: next(resource for resource in item["resources"] if resource["kind"] == "skill").update(
        digest=skill_assets.digest_tree(skill)[0]))
    (bundle / "agent.json").chmod(0o555)
    state = State(tmp_path / "state")
    original = definitions.import_bundle(state, bundle)
    identity, version = original["definition"]["id"], original["definition"]["version"]
    updated = {**original["definition"], "version": "1.0.1", "description": "Revised specialist request",
               "backend": {"tool": "codex", "model": "test-specialist"}}
    index = state.root / "agent-definitions/index.json"
    before = index.read_bytes()
    checked = definitions.revise(state, identity, version, original["digest"], updated)
    assert checked["published"] is False and "path" not in checked
    assert index.read_bytes() == before
    with pytest.raises(ValueError, match="base digest"):
        definitions.revise(state, identity, version, "0" * 64, updated, publish=True)
    assert index.read_bytes() == before
    published = definitions.revise(state, identity, version, original["digest"], updated, publish=True)
    assert published == {**checked, "published": True}
    assert definitions.revise(state, identity, version, original["digest"], updated, publish=True) == published
    assert definitions.get(state, identity, version) == original
    saved = definitions.get(state, identity, updated["version"])
    assert saved["files"]["agent.json"]["executable_bits"] == original["files"]["agent.json"]["executable_bits"]
    assert {key: value for key, value in saved["files"].items() if key != "agent.json"} == {
        key: value for key, value in original["files"].items() if key != "agent.json"}
    assert (Path(saved["path"]) / "skills/kernel-measurement/references/empty").is_dir()


@pytest.mark.parametrize("mutation", ["attachment", "executable", "directory", "document"])
def test_resource_acceptance_binds_the_entire_candidate(bundle, tmp_path, mutation):
    if mutation == "executable" and sys.platform == "win32":
        pytest.skip("Windows cannot set POSIX executable bits")
    state = State(tmp_path / "state")
    original = definitions.import_bundle(state, bundle)
    definition = {**original["definition"], "version": "1.0.1"}
    changes = {"schema_version": 1, "operations": [
        {"op": "write", "path": "opaque.bin", "content_base64": base64.b64encode(b"\xff\x00 accepted attachment").decode()}]}
    args = (state, definition["id"], "1.0.0", original["digest"])
    preview = definitions.revise(*args, definition, resource_changes=changes, preview_resources=True)
    index = state.root / "agent-definitions/index.json"
    before = index.read_bytes()
    changed = deepcopy(changes)
    definition = deepcopy(preview["definition"])
    if mutation == "attachment":
        changed["operations"][0]["content_base64"] = base64.b64encode(b"\xff\x00 unaccepted attachment").decode()
    elif mutation == "executable":
        changed["operations"][0]["executable_bits"] = 0o100
    elif mutation == "directory":
        changed["operations"].append({"op": "mkdir", "path": "new/nested/empty"})
    else:
        definition["description"] += " Changed after acceptance"
    for publish in (False, True):
        with pytest.raises(ValueError, match="candidate changed"):
            definitions.revise(*args, definition, resource_changes=changed,
                               accepted_candidate=preview["candidate"], publish=publish)
    assert index.read_bytes() == before
    assert definitions.get(state, definition["id"], "1.0.0") == original


@pytest.mark.parametrize("unreferenced", [False, True])
def test_resource_publication_rejects_same_digest_with_different_empty_directories(bundle, tmp_path, unreferenced):
    state = State(tmp_path / "state")
    original = definitions.import_bundle(state, bundle)
    definition = {**original["definition"], "version": "1.0.1"}
    args = (state, definition["id"], "1.0.0", original["digest"], definition)
    changes = {"schema_version": 1, "operations": [{"op": "mkdir", "path": "new/a/empty"}]}
    first = definitions.revise(*args, resource_changes=changes, preview_resources=True)
    published = definitions.revise(*args, resource_changes=changes, accepted_candidate=first["candidate"], publish=True)
    assert definitions.revise(*args, resource_changes=changes, accepted_candidate=first["candidate"], publish=True) == published
    index = state.root / "agent-definitions/index.json"
    if unreferenced:
        document = json.loads(index.read_bytes())
        del document["definitions"][definition["id"]]["1.0.1"]
        index.write_text(json.dumps(document))
    before = index.read_bytes()
    changed = {"schema_version": 1, "operations": [{"op": "mkdir", "path": "new/b/empty"}]}
    second = definitions.revise(*args, resource_changes=changed, preview_resources=True)
    assert second["digest"] == first["digest"]
    assert second["candidate"]["directories"] != first["candidate"]["directories"]
    with pytest.raises(ValueError, match="different directories"):
        definitions.revise(*args, resource_changes=changed, accepted_candidate=second["candidate"], publish=True)
    assert index.read_bytes() == before
    stored = state.root / "agent-definitions/objects" / first["digest"]
    assert (stored / "new/a/empty").is_dir() and not (stored / "new/b").exists()


@pytest.mark.parametrize("operations", [
    [{"op": "write", "path": "agent.json", "content_base64": "e30="}],
    [{"op": "write", "path": "new.bin", "content_base64": "YQ=="},
     {"op": "write", "path": "new.bin", "content_base64": "Yg=="}],
    [{"op": "mkdir", "path": "new"}, {"op": "write", "path": "new/file", "content_base64": "YQ=="}],
])
def test_resource_operations_cannot_silently_override_each_other_or_the_document(bundle, tmp_path, operations):
    state = State(tmp_path / "state")
    original = definitions.import_bundle(state, bundle)
    before = (state.root / "agent-definitions/index.json").read_bytes()
    with pytest.raises(ValueError, match="document input|repeat or overlap"):
        definitions.revise(state, original["definition"]["id"], "1.0.0", original["digest"],
                           {**original["definition"], "version": "1.0.1"},
                           resource_changes={"schema_version": 1, "operations": operations}, preview_resources=True)
    assert (state.root / "agent-definitions/index.json").read_bytes() == before
    assert definitions.get(state, original["definition"]["id"], "1.0.0") == original


def test_cli_resource_transport_bounds_repeated_write_payloads(tmp_path):
    # A small source tree can otherwise expand into an arbitrarily large transport.
    (tmp_path / "files").mkdir()
    (tmp_path / "files/attachment.bin").write_bytes(b"x" * 8192)
    changes = {"schema_version": 1, "operations": [{"op": "write", "path": "attachment.bin"}] * 1500}
    (tmp_path / "changes.json").write_text(json.dumps(changes))
    with pytest.raises(ValueError):
        definition_bundles.resource_changes_from_directory(tmp_path)


@pytest.mark.parametrize("scenario", ["depth", "count", "file-boundary"])
def test_resource_directory_budget_precedes_filesystem_allocation(bundle, tmp_path, monkeypatch, scenario):
    state = State(tmp_path / "state")
    original = definitions.import_bundle(state, bundle)
    if scenario == "count":
        operations = [{"op": "mkdir", "path": f"flood-{number}"} for number in range(501)]
    else:
        path = "/".join(["flood", *[f"level-{number}" for number in range(32)]])
        operations = [{"op": "mkdir", "path": path}] if scenario == "depth" else [
            {"op": "write", "path": path, "content_base64": "YQ=="}]
    mkdir = Path.mkdir

    def prevent_allocation(path, *args, **kwargs):
        if any(part.startswith("flood") for part in path.parts):
            pytest.fail("Over-budget resource directories reached filesystem allocation")
        return mkdir(path, *args, **kwargs)

    if scenario != "file-boundary":
        monkeypatch.setattr(Path, "mkdir", prevent_allocation)
    args = (state, original["definition"]["id"], "1.0.0", original["digest"],
            {**original["definition"], "version": "1.0.1"})
    changes = {"schema_version": 1, "operations": operations}
    if scenario == "file-boundary":
        preview = definitions.revise(*args, resource_changes=changes, preview_resources=True)
        assert operations[0]["path"] in preview["files"]
    else:
        with pytest.raises(ValueError, match="directory count or depth"):
            definitions.revise(*args, resource_changes=changes, preview_resources=True)


@pytest.mark.parametrize("mutation", ["schema", "bool-version", "missing-hash", "bad-hash", "missing-file", "duplicate-id",
                                      "unknown-role", "incompatible-backend", "unknown-backend-field", "permission-field",
                                      "bad-skill-hash", "missing-skill-hash", "no-instructions", "two-instructions", "invalid-frontmatter"])
def test_invalid_definitions_are_rejected_before_publication(bundle, tmp_path, mutation):
    def change(item):
        if mutation == "schema":
            item["schema_version"] = 99
        elif mutation == "bool-version":
            item["schema_version"] = True
        elif mutation == "missing-hash":
            del item["resources"][0]["sha256"]
        elif mutation == "bad-hash":
            item["resources"][0]["sha256"] = "0" * 64
        elif mutation == "missing-file":
            item["resources"][0]["path"] = "absent.md"
        elif mutation == "duplicate-id":
            item["resources"][1]["id"] = item["resources"][0]["id"]
        elif mutation == "unknown-role":
            item["roles"] = ["nonexistent"]
        elif mutation == "incompatible-backend":
            item["roles"], item["backend"] = ["reviewer"], {"tool": "mini-swe-agent", "model": "provider/model"}
        elif mutation == "unknown-backend-field":
            item["backend"]["not-supported"] = True
        elif mutation == "permission-field":
            item["permissions"] = {"write": True}
        elif mutation == "bad-skill-hash":
            item["resources"][2]["digest"] = "0" * 64
        elif mutation == "missing-skill-hash":
            del item["resources"][2]["digest"]
        elif mutation == "no-instructions":
            item["resources"][0]["kind"] = "context"
        elif mutation == "two-instructions":
            item["resources"][1]["kind"] = "instructions"
        else:
            (bundle / "skills/kernel-measurement/SKILL.md").write_text("Missing frontmatter", encoding="utf-8")
            item["resources"][2]["digest"] = skill_assets.digest_tree(bundle / "skills/kernel-measurement")[0]
    revise(bundle, change)
    state = State(tmp_path / "state")
    with pytest.raises(ValueError):
        definitions.import_bundle(state, bundle)
    assert definitions.definitions(state) == []


@pytest.mark.parametrize("path", ["../outside.md", "/etc/passwd", "C:/outside.md", "context\\outside.md", "context/../instructions.md",
                                 "./instructions.md", "context//measurement.md", "context/measurement.md:secret", "NUL.md"])
def test_resource_paths_cannot_escape_or_change_meaning_across_platforms(bundle, path):
    revise(bundle, lambda item: item["resources"][0].update(path=path))
    with pytest.raises(ValueError, match="portable relative path"):
        definitions.inspect_bundle(bundle)


def test_import_does_not_execute_command_or_skill_script(bundle, tmp_path):
    marker = tmp_path / "executed"
    program = f"from pathlib import Path; Path({str(marker)!r}).touch()"
    (bundle / "skills/kernel-measurement/execute.py").write_text(program, encoding="utf-8")
    def change(item):
        item["roles"] = ["implementer"]
        item["backend"] = {"tool": "command", "argv": [sys.executable, "-c", program]}
        item["resources"][2]["digest"] = skill_assets.digest_tree(bundle / "skills/kernel-measurement")[0]
    revise(bundle, change)
    state = State(tmp_path / "state")
    imported = definitions.import_bundle(state, bundle)
    definitions.get(state, imported["definition"]["id"], "1.0.0", material=True)
    with state.connect() as db:
        assert db.execute("SELECT count(*) FROM agent_runs").fetchone()[0] == 0
    assert not marker.exists()


def test_copy_failure_and_failed_reference_publication_can_retry_without_partial_versions(bundle, tmp_path, monkeypatch):
    state = State(tmp_path / "state")
    def fail_copy(source, destination, *args, **kwargs):
        Path(destination).mkdir()
        (Path(destination) / "agent.json").write_text("{}", encoding="utf-8")
        raise OSError("interrupted copy")
    with monkeypatch.context() as patch:
        patch.setattr(definition_bundles.shutil, "copytree", fail_copy)
        with pytest.raises(OSError, match="interrupted"):
            definitions.import_bundle(state, bundle)
    assert not (state.root / "agent-definitions/index.json").exists()
    assert not (state.root / "agent-definitions").exists()
    assert definitions.definitions(state) == []
    assert backups.create(state.root, tmp_path / "after-copy-failure", offline=True)["agent_definitions"] == 0
    original_replace = Path.replace
    def fail_index(path, target):
        if Path(target).name == "index.json":
            raise OSError("interrupted index")
        return original_replace(path, target)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", fail_index)
        with pytest.raises(OSError, match="interrupted index"):
            definitions.import_bundle(state, bundle)
    assert not (state.root / "agent-definitions/index.json").exists()
    assert definitions.definitions(state) == []
    assert backups.create(state.root, tmp_path / "after-index-failure", offline=True)["agent_definitions"] == 0
    published = definitions.import_bundle(state, bundle)
    assert definitions.get(state, "kernel-implementer", "1.0.0") == published
    assert len(list((state.root / "agent-definitions/objects").iterdir())) == 1
    original_index = (state.root / "agent-definitions/index.json").read_bytes()
    revise(bundle, lambda item: item.update(version="1.0.1", description="New version"))
    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", fail_index)
        with pytest.raises(OSError, match="interrupted index"):
            definitions.import_bundle(state, bundle)
    assert (state.root / "agent-definitions/index.json").read_bytes() == original_index
    assert definitions.get(state, "kernel-implementer", "1.0.0") == published
    assert len(definitions.definitions(state)) == 1
    assert backups.create(state.root, tmp_path / "after-incremental-failure", offline=True)["agent_definitions"] == 1
    definitions.import_bundle(state, bundle)
    assert len(definitions.definitions(state)) == 2
    assert len(list((state.root / "agent-definitions/objects").iterdir())) == 2


def test_missing_existing_index_is_corruption_and_cannot_drop_other_registered_versions(bundle, tmp_path):
    state = State(tmp_path / "state")
    definitions.import_bundle(state, bundle)
    definitions.import_bundle(state, EXAMPLES / "architecture-reviewer")
    index = state.root / "agent-definitions/index.json"
    index.unlink()
    objects = sorted(path.name for path in (state.root / "agent-definitions/objects").iterdir())
    with pytest.raises(OSError):
        definitions.import_bundle(state, bundle)
    assert not index.exists()
    assert sorted(path.name for path in (state.root / "agent-definitions/objects").iterdir()) == objects
    with pytest.raises(OSError):
        definitions.definitions(state)


def test_source_change_during_copy_does_not_publish_a_different_recipe(bundle, tmp_path, monkeypatch):
    state = State(tmp_path / "state")
    original = shutil.copytree
    def change_copy(source, target, *args, **kwargs):
        result = original(source, target, *args, **kwargs)
        if Path(source) == bundle:
            revise(Path(target), lambda item: item.update(description="Different copy"))
        return result
    monkeypatch.setattr(definition_bundles.shutil, "copytree", change_copy)
    with pytest.raises(ValueError, match="source changed"):
        definitions.import_bundle(state, bundle)
    assert not (state.root / "agent-definitions/index.json").exists()


def test_concurrent_imports_publish_one_complete_reference(bundle, tmp_path):
    state = State(tmp_path / "state")
    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(lambda _: definitions.import_bundle(state, bundle), range(4)))
    assert all(result == results[0] for result in results)
    assert len(definitions.definitions(state)) == 1


@pytest.mark.parametrize("damage", ["resource", "object-missing", "reference"])
def test_registered_content_cannot_be_silently_repaired_or_backed_up(bundle, tmp_path, damage):
    state = State(tmp_path / "state")
    imported = definitions.import_bundle(state, bundle)
    if damage == "resource":
        (Path(imported["path"]) / "instructions.md").write_text("changed", encoding="utf-8")
    elif damage == "object-missing":
        shutil.rmtree(imported["path"])
    else:
        index = state.root / "agent-definitions/index.json"
        value = json.loads(index.read_text(encoding="utf-8"))
        value["definitions"]["other-agent"] = value["definitions"].pop("kernel-implementer")
        index.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises((ValueError, OSError)):
        definitions.get(state, "other-agent" if damage == "reference" else "kernel-implementer", "1.0.0")
    if damage != "reference":
        with pytest.raises((ValueError, OSError)):
            definitions.import_bundle(state, bundle)
    with pytest.raises((ValueError, OSError)):
        backups.create(state.root, tmp_path / "bad-backup", offline=True)
    assert not (tmp_path / "bad-backup").exists()


def test_offline_restore_preserves_definitions_resources_and_exact_references(bundle, tmp_path):
    state = State(tmp_path / "state")
    first = definitions.import_bundle(state, bundle)
    definitions.import_bundle(state, EXAMPLES / "architecture-reviewer")
    before = definitions.get(state, "kernel-implementer", "1.0.0", material=True)
    snapshot = backups.create(state.root, tmp_path / "backup", offline=True)
    assert snapshot["agent_definitions"] == 2 and snapshot["database_schema_version"] == 1
    state.root.rename(tmp_path / "kept-original")
    backups.restore(state.root, tmp_path / "backup", offline=True)
    restored = State(state.root)
    assert definitions.get(restored, "kernel-implementer", "1.0.0", material=True) == before
    assert definitions.verify_store(restored.root) == 2
    assert definitions.get(restored, "kernel-implementer", "1.0.0")["digest"] == first["digest"]


@pytest.mark.parametrize("policy_change", ["removed-role", "removed-backend", "stricter-binding"])
def test_historical_assets_survive_current_admission_changes(bundle, tmp_path, monkeypatch, capsys, policy_change):
    from ergora.cli import main

    state = State(tmp_path / "state")
    original = definitions.import_bundle(state, bundle)
    expected = definitions.get(state, "kernel-implementer", "1.0.0", material=True)
    listing = definitions.definitions(state)
    index = (state.root / "agent-definitions/index.json").read_bytes()
    if policy_change == "removed-role":
        monkeypatch.setattr(agents, "ROLE_CAPABILITIES", {key: value for key, value in agents.ROLE_CAPABILITIES.items()
                                                       if key != "implementer"})
    elif policy_change == "removed-backend":
        monkeypatch.setattr(agents, "CHOICES", {**agents.CHOICES, "implementer": ["command"]})
    else:
        def reject(role, binding, **kwargs):
            raise ValueError("Current policy rejects this binding")
        monkeypatch.setattr(agents, "validate_binding", reject)
    assert definitions.get(state, "kernel-implementer", "1.0.0", material=True) == expected
    assert definitions.definitions(state) == listing and definitions.verify_store(state.root) == 1
    assert main(["--home", str(state.root), "agent", "definition", "list", "--role", "implementer"]) == 0
    assert json.loads(capsys.readouterr().out) == listing
    exported = tmp_path / "export"
    assert definitions.export(state, "kernel-implementer", "1.0.0", exported)["digest"] == original["digest"]
    assert skill_assets.digest_tree(exported)[0] == original["digest"]
    # Public checks and both import entry points still apply current policy, even for identical content.
    for operation in (lambda: definitions.inspect_bundle(bundle),
                      lambda: definitions.import_bundle(state, bundle),
                      lambda: definitions.library(state.root).import_bundle(exported)):
        with pytest.raises(ValueError):
            operation()
    assert (state.root / "agent-definitions/index.json").read_bytes() == index
    archive = tmp_path / "backup"
    snapshot = backups.create(state.root, archive, offline=True)
    assert backups.verify(archive)["manifest_sha256"] == snapshot["manifest_sha256"]
    state.root.rename(tmp_path / "kept-original")
    backups.restore(state.root, archive, offline=True)
    assert definitions.get(state, "kernel-implementer", "1.0.0", material=True) == expected
    assert (state.root / "agent-definitions/index.json").read_bytes() == index


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlinks and FIFO; Windows junction covered separately")
@pytest.mark.parametrize("unsafe", ["link", "root-link", "fifo", "git"])
def test_unsafe_trees_rejected_before_reading_or_traversing_external_content(bundle, tmp_path, unsafe):
    external = tmp_path / "outside"
    external.mkdir()
    if unsafe == "root-link":
        linked = tmp_path / "linked"
        linked.symlink_to(bundle, target_is_directory=True)
        bundle = linked
    elif unsafe == "link":
        (bundle / "outside").symlink_to(external, target_is_directory=True)
    elif unsafe == "fifo":
        os.mkfifo(bundle / "pipe")
    else:
        (bundle / ".git").mkdir()
    with pytest.raises(ValueError, match="symlinks|special files|.git"):
        definitions.inspect_bundle(bundle)


@pytest.mark.skipif(os.name != "nt", reason="requires a real Windows junction")
def test_windows_junction_rejected_before_descent(bundle, tmp_path):
    external = tmp_path / "external"
    external.mkdir()
    link = bundle / "junction"
    result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(external)], capture_output=True)
    assert result.returncode == 0, result.stderr
    try:
        with pytest.raises(ValueError, match="reparse points"):
            definitions.inspect_bundle(bundle)
    finally:
        link.rmdir()


def test_tree_identity_matches_original_skill_algorithm(bundle):
    files = {}
    for path in sorted(bundle.rglob("*")):
        if path.is_file():
            files[path.relative_to(bundle).as_posix()] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "executable_bits": path.stat().st_mode & 0o111}
    assert definitions.inspect_bundle(bundle)["digest"] == hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


@pytest.mark.parametrize("bound", ["files", "bytes", "directories", "depth"])
def test_tree_limits_reject_oversized_or_empty_directory_floods(bundle, bound):
    if bound == "files":
        for number in range(501):
            (bundle / f"file-{number}").touch()
    elif bound == "bytes":
        (bundle / "large.bin").write_bytes(b"x" * 10_000_001)
    elif bound == "directories":
        for number in range(501):
            (bundle / f"dir-{number}").mkdir()
    else:
        path = bundle / "deep"
        for _ in range(33):
            path.mkdir()
            path /= "x"
    with pytest.raises(ValueError, match="exceeds"):
        definitions.inspect_bundle(bundle)


def test_duplicate_json_keys_are_rejected_instead_of_silently_overriding_recipe(bundle):
    path = bundle / "agent.json"
    path.write_text(path.read_text(encoding="utf-8").replace('"schema_version": 1,', '"schema_version": 99, "schema_version": 1,'),
                    encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        definitions.inspect_bundle(bundle)


@pytest.mark.skipif(os.name == "nt", reason="case-insensitive filesystem cannot create these ambiguous sources")
@pytest.mark.parametrize("scenario", ["parents", "empty-case", "empty-reserved", "empty-file"])
def test_empty_and_nonempty_directory_paths_rejected_for_portable_bundles(bundle, scenario):
    if scenario == "empty-reserved":
        (bundle / "NUL").mkdir()
    else:
        (bundle / "Upper").mkdir()
        if scenario == "empty-file":
            (bundle / "upper").touch()
        else:
            (bundle / "upper").mkdir()
            if scenario == "parents":
                (bundle / "Upper/one").touch()
                (bundle / "upper/two").touch()
    with pytest.raises(ValueError, match="case-insensitive path collisions|portable relative path"):
        definitions.inspect_bundle(bundle)


def test_existing_skill_assets_with_many_or_deep_empty_directories_still_read_and_back_up(tmp_path):
    state = State(tmp_path / "state")
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    projects.create(state, "demo", repo)
    source = tmp_path / "old-skill"
    source.mkdir()
    (source / "SKILL.md").write_text("---\nname: old-skill\ndescription: Legacy asset\n---\nOriginal instructions.\n", encoding="utf-8")
    original = skill_assets.import_bundle(state, "demo", source)
    stored = Path(original["path"])
    for number in range(501):
        (stored / f"empty-{number}").mkdir()
    deep = stored / "deep"
    for _ in range(33):
        deep.mkdir()
        deep /= "x"
    assert skill_assets.get(state, "demo", original["digest"]) == original
    assert backups.create(state.root, tmp_path / "legacy-skill-backup", offline=True)["skills"] == 1


def test_cli_checks_without_creating_state_then_imports_shows_filters_and_exports(bundle, tmp_path):
    state = tmp_path / "not-created-by-check"
    def cli(*args):
        result = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state), "agent", "definition", *args],
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)
    checked = cli("check", str(bundle), "--material")
    assert not state.exists() and all(item["text"] for item in checked["resources"])
    assert cli("import", str(bundle))["digest"] == checked["digest"]
    assert cli("list", "--role", "reviewer") == []
    assert len(cli("list", "--specialty", "cuda")) == 1
    shown = cli("show", "kernel-implementer", "1.0.0", "--material")
    assert shown["definition"] == checked["definition"] and shown["resources"] == checked["resources"]
    assert cli("export", "kernel-implementer", "1.0.0", str(tmp_path / "export"))["digest"] == shown["digest"]
