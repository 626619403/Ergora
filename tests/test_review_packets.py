"""Exact local Git material and offline packet integrity, using real objects."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

import ergora.agents.backends as agent_backends
import ergora.agents.runs as agent_runs
import ergora.agents.invocation as agents
import ergora.interfaces.cli as cli
import ergora.configuration.projects as projects
import ergora.development.review.packets as review_packets
import ergora.development.review.requests as review_requests
import ergora.definitions.workflows as workflows
from ergora.runtime import processes
from ergora.storage.state import State
from test_composition_invocations import prepared as restricted_input


def git(repository, *arguments, input=None):
    result = subprocess.run(["git", "-C", str(repository), *arguments], input=input, capture_output=True)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


def commit(repository, message):
    git(repository, "-c", "user.name=Packet Test", "-c", "user.email=packet@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-qm", message)
    return git(repository, "rev-parse", "HEAD").decode().strip()


@pytest.fixture
def source(tmp_path):
    repository = tmp_path / "source"
    repository.mkdir()
    git(repository, "init", "-q", "--initial-branch=main")
    git(repository, "config", "core.autocrlf", "false")
    (repository / "src").mkdir()
    files = {"AGENTS.md": b"Root instructions\r\n", "src/AGENTS.md": b"Source instructions\n",
             "src/train.py": b"VALUE = 1\r\n", "src/old.py": "# 原内容\r\n".encode(),
             "src/deleted.py": b"DELETE = True\n", "caller.py": b"from src.train import VALUE\n",
             "config.toml": b"target = 1\n"}
    for path, raw in files.items():
        (repository / path).write_bytes(raw)
    git(repository, "add", ".")
    anchor = commit(repository, "anchor")
    (repository / "config.toml").write_bytes(b"target = 2\n")
    git(repository, "add", ".")
    base = commit(repository, "target advanced")
    git(repository, "checkout", "-qb", "candidate", anchor)
    (repository / "src/train.py").write_bytes("VALUE = 2  # 新候选\r\n".encode())
    (repository / "src/deleted.py").unlink()
    (repository / "src/old.py").rename(repository / "src/renamed.py")
    git(repository, "add", "-A")
    head = commit(repository, "candidate")
    requirements = tmp_path / "request.md"
    requirements.write_bytes("保留语义并核对调用者。\r\n".encode())
    evidence = tmp_path / "check.txt"
    evidence.write_bytes(b"operator supplied check output\r\n")
    options = {"repository_id": "example/training", "base": base, "head": head,
               "requirements": requirements, "context_paths": ["caller.py", "config.toml"], "evidence": [evidence]}
    return repository, anchor, options


@pytest.fixture
def review_manifest(tmp_path):
    state = State(tmp_path / "review-definitions")

    def build(domain, *, after_general=False):
        if domain == "engineering":
            from test_presets import _selected_engineering_review
            _, document = _selected_engineering_review(state)
        else:
            installed = workflows.install_preset(state, domain + "-review")
            document = workflows.get(state, installed["root"]["id"], installed["root"]["version"])
        root = document["definition"]
        if after_general:
            major, minor, patch = map(int, root["version"].split("."))
            root["version"] = f"{major}.{minor}.{patch + 1}"
            next(node for node in root["nodes"] if node["id"] == "domain")["depends_on"] = ["general"]
            bundle = tmp_path / "serial-domain"
            shutil.copytree(document["path"], bundle)
            (bundle / "workflow.json").write_text(json.dumps(root), encoding="utf-8")
            workflows.import_bundle(state, bundle)
        grant = {"schema_version": 1, "permissions": root["permissions"], "limits": root["limits"]}
        manifest = workflows.prepare_manifest(state.root, root["id"], root["version"], grant, tmp_path / domain)
        return manifest

    return build


@pytest.mark.parametrize("domain", ["pretraining", "posttraining"])
def test_source_bound_domain_input_preserves_complete_material_and_frozen_ancestors(source, review_manifest, tmp_path,
                                                                                  monkeypatch, capsys, domain):
    repository, _, options = source
    packet, destination = tmp_path / "packet", tmp_path / "source-input"
    receipt = review_packets.prepare(repository, destination=packet, **options)
    manifest = review_manifest(domain)
    originals = {str(path): path.read_bytes() for directory in (packet, Path(manifest["path"]))
                 for path in directory.rglob("*") if path.is_file()}
    selected = review_requests.prepare(packet, source_kind="local", source_sha256=receipt["packet_sha256"],
        manifest=Path(manifest["path"]), manifest_digest=manifest["digest"], instance="root/domain/review",
        destination=destination, max_prompt_bytes=1_000_000)
    frozen = workflows.inspect_input(destination, material=True)
    task = json.loads((destination / "task.txt").read_bytes())
    assert task["material"] == review_packets.read(packet, sha256=receipt["packet_sha256"])
    leaf = next(item for item in frozen["composition"]["instances"] if item["path"] == selected["instance"])
    assert leaf["ref"]["id"] == "ergora-" + domain + "-reviewer"
    assert all(resource["text"] in frozen["prompt"] for resource in leaf["resources"])
    assert any(source["instance"] == "root" for resource in leaf["resources"] for source in resource["sources"])
    monkeypatch.setenv("PATH", "")
    unused_home = tmp_path / "unused-home"
    assert cli.main(["--home", str(unused_home), "review", "verify-input", str(packet), "--source-kind", "local",
        "--source-sha256", receipt["packet_sha256"], "--input", str(destination),
        "--input-digest", selected["input_digest"], "--manifest-digest", manifest["digest"]]) == 0
    assert json.loads(capsys.readouterr().out)["input_digest"] == selected["input_digest"] and not unused_home.exists()
    for original in (packet, Path(manifest["path"])):
        with pytest.raises(ValueError, match="inside its immutable source or manifest"):
            review_requests.prepare(packet, source_kind="local", source_sha256=receipt["packet_sha256"],
                manifest=Path(manifest["path"]), manifest_digest=manifest["digest"], instance=selected["instance"],
                destination=original / "unwanted" / "input", max_prompt_bytes=1_000_000)
        assert not (original / "unwanted").exists()
    assert {name: Path(name).read_bytes() for name in originals} == originals
    # A different valid packet for the same commits is still a different original request.
    monkeypatch.undo()
    request = tmp_path / "different-request.md"
    request.write_text("A different original requirement.", encoding="utf-8")
    other = tmp_path / "other-packet"
    other_receipt = review_packets.prepare(repository, destination=other, **{**options, "requirements": request})
    with pytest.raises(ValueError, match="complete selected source or manifest identity"):
        review_requests.verify(destination, input_digest=selected["input_digest"], source=other,
            source_kind="local", source_sha256=other_receipt["packet_sha256"], manifest_digest=manifest["digest"])


@pytest.mark.parametrize("permission", [("read", ["definitions"]), ("shell", True)])
def test_source_bound_inputs_refuse_valid_templates_with_incompatible_permissions(source, restricted_input, tmp_path, permission):
    repository, _, options = source
    state, _, original_input = restricted_input(permission=permission)
    grant = workflows.inspect_input(original_input)["request"]["grant"]
    manifest = workflows.prepare_manifest(state.root, "structure-review", "1.0.0", grant, tmp_path / "restricted-manifest")
    packet = tmp_path / "packet"
    receipt = review_packets.prepare(repository, destination=packet, **options)
    destination = tmp_path / "denied"
    with pytest.raises(ValueError, match="read ceiling|read-only leaf"):
        review_requests.prepare(packet, source_kind="local", source_sha256=receipt["packet_sha256"],
            manifest=Path(manifest["path"]), manifest_digest=manifest["digest"], instance="root/review",
            destination=destination, max_prompt_bytes=1_000_000)
    assert not destination.exists()


def test_source_bound_inputs_refuse_a_different_manifest_used_during_preparation(source, review_manifest, tmp_path, monkeypatch):
    repository, _, options = source
    before, switched = review_manifest("pretraining"), review_manifest("posttraining")
    packet = tmp_path / "packet"
    receipt = review_packets.prepare(repository, destination=packet, **options)
    original = workflows.prepare_input_from_manifest

    def replace_manifest(manifest, *args, **kwargs):
        return original(Path(switched["path"]), *args, **kwargs)

    monkeypatch.setattr(workflows, "prepare_input_from_manifest", replace_manifest)
    destination = tmp_path / "changed-manifest"
    with pytest.raises(ValueError, match="manifest changed while preparing"):
        review_requests.prepare(packet, source_kind="local", source_sha256=receipt["packet_sha256"],
            manifest=Path(before["path"]), manifest_digest=before["digest"], instance="root/domain/review",
            destination=destination, max_prompt_bytes=1_000_000)
    assert not destination.exists()


def test_source_bound_input_does_not_skip_unexecuted_ancestor_dependencies(source, review_manifest, tmp_path):
    repository, _, options = source
    packet = tmp_path / "packet"
    receipt = review_packets.prepare(repository, destination=packet, **options)
    manifest = review_manifest("pretraining", after_general=True)
    destination = tmp_path / "not-executed"
    with pytest.raises(ValueError, match="direct root task"):
        review_requests.prepare(packet, source_kind="local", source_sha256=receipt["packet_sha256"],
            manifest=Path(manifest["path"]), manifest_digest=manifest["digest"], instance="root/domain/review",
            destination=destination, max_prompt_bytes=1_000_000)
    assert not destination.exists()


def test_source_bound_input_exceeding_full_prompt_capacity_is_not_truncated_or_published(source, review_manifest, tmp_path):
    repository, _, options = source
    packet = tmp_path / "packet"
    receipt = review_packets.prepare(repository, destination=packet, **options)
    manifest = review_manifest("pretraining")
    destination = tmp_path / "too-small"
    with pytest.raises(ValueError, match="Complete composition prompt exceeds"):
        review_requests.prepare(packet, source_kind="local", source_sha256=receipt["packet_sha256"],
            manifest=Path(manifest["path"]), manifest_digest=manifest["digest"], instance="root/domain/review",
            destination=destination, max_prompt_bytes=100)
    assert not destination.exists() and not list(tmp_path.glob(".review-input-*"))


@pytest.fixture
def reviewed_source(source, review_manifest, tmp_path, monkeypatch):
    repository, _, options = source
    state = State(tmp_path / "review-runs")
    projects.create(state, "demo", repository)

    def native(argv, cwd, output, timeout, stdin, env, **kwargs):
        run = agent_runs.runs(state, "demo")[0]
        path = run["input_request"]["instance"]
        response = "Original reply for " + path + ":\n````\nUnicode: \u0085\u2028\u2029\r\n" + "完整审查意见。" * 10000
        result = {"summary": path, "artifacts": {"response": response},
                  "decision": decision if path in ("root/domain/review", "root/resource-lifecycle") else "approve"}
        Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(result), encoding="utf-8")
        output.mkdir()
        return {"status": "succeeded", "returncode": 0, "output": str(output)}

    monkeypatch.setattr(processes, "run", native)
    decision = "request-changes"

    def build(domain="pretraining", domain_decision="request-changes"):
        nonlocal decision
        decision = domain_decision
        packet = tmp_path / "report-packet"
        receipt = review_packets.prepare(repository, destination=packet, **options)
        manifest = review_manifest(domain)
        graph = workflows.inspect_manifest(Path(manifest["path"]), material=True)["composition"]
        selections = {}
        for number, leaf in enumerate(item for item in graph["instances"] if item["kind"] == "agent"):
            directory = tmp_path / ("report-input-" + str(number))
            review_requests.prepare(packet, source_kind="local", source_sha256=receipt["packet_sha256"],
                manifest=Path(manifest["path"]), manifest_digest=manifest["digest"], instance=leaf["path"],
                destination=directory, max_prompt_bytes=1_000_000)
            run = agent_runs.run_input(state, "demo", directory, backend="codex", reason="Explicit fixture backend")
            assert run["status"] == "succeeded"
            selections[leaf["path"]] = run["id"]
        return state, packet, {"source_kind": "local", "source_sha256": receipt["packet_sha256"],
            "manifest": Path(manifest["path"]), "manifest_digest": manifest["digest"], "runs": selections}

    return build


@pytest.mark.parametrize("domain,decision", [("pretraining", "request-changes"), ("posttraining", "request-changes"),
                                            ("pretraining", "approve"), ("engineering", "request-changes")])
def test_complete_review_report_retains_each_original_and_minority_without_redispatch(reviewed_source, tmp_path,
                                                                                    monkeypatch, capsys, domain, decision):
    state, packet, options = reviewed_source(domain, decision)
    with state.connect() as db:
        before = list(db.iterdump())
    originals = {str(p): p.read_bytes() for directory in (packet, options["manifest"], state.root / "runs")
                 for p in directory.rglob("*") if p.is_file()}
    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(agent_backends, "for_binding", lambda *a, **k: pytest.fail("Report must not readmit a backend"))
    monkeypatch.setattr(agents, "invoke", lambda *a, **k: pytest.fail("Report must not redispatch"))
    observed = review_requests.report(state, "demo", packet, **options)
    count = len(options["runs"])
    assert observed["coverage"] == {"expected": count, "selected": count, "verified": count, "completed": count, "complete": True}
    assert observed["decision"] == decision and not observed["formal_execution_authorized"]
    opposed = "root/resource-lifecycle" if domain == "engineering" else "root/domain/review"
    assert observed["request_changes"] == ([opposed] if decision == "request-changes" else [])
    for branch in observed["branches"]:
        original = branch["observation"]
        assert original["result"]["bytes"] > 65536 and original["run"]["id"] == options["runs"][branch["instance"]]
        assert original["run"]["binding"]["tool"] == "codex" and branch["agent"]["specialties"]
        assert original["input"]["composition"] == observed["manifest"]["composition"]
        assert original["result"]["document"]["summary"] == branch["instance"]
    mapping = tmp_path / "runs.json"
    mapping.write_text(json.dumps(options["runs"]), encoding="utf-8")
    argv = ["--home", str(state.root), "review", "report", "demo", str(packet), "--source-kind", "local",
            "--source-sha256", options["source_sha256"], "--manifest", str(options["manifest"]),
            "--manifest-digest", options["manifest_digest"], "--runs", str(mapping)]
    assert cli.main(argv) == 0 and json.loads(capsys.readouterr().out) == observed
    assert cli.main(argv + ["--format", "markdown"]) == 0
    rendered = capsys.readouterr().out
    assert "Decision: " + decision in rendered and "    ````" in rendered
    encoded = rendered.split("## Complete source and original observations\n\n", 1)[1]
    recovered = "\n".join(line[4:] for line in encoded.split("\n") if line.startswith("    "))
    assert json.loads(recovered) == observed
    for branch in observed["branches"]:
        response = branch["observation"]["result"]["document"]["artifacts"]["response"]
        assert all("    " + line in rendered for line in response.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
    with state.connect() as db:
        assert list(db.iterdump()) == before
    assert {name: Path(name).read_bytes() for name in originals} == originals


def test_review_report_keeps_original_unfinished_states_separate_from_evidence_and_opinion(reviewed_source):
    state, packet, options = reviewed_source()
    run_id = options["runs"]["root/general/structure/review"]
    for status in ("failed", "running", "preparing", "unknown"):
        with state.connect() as db:
            run = json.loads(db.execute("SELECT document FROM agent_runs WHERE id=?", (run_id,)).fetchone()[0])
            run["status"] = status
            db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(run), run_id))
        observed = review_requests.report(state, "demo", packet, **options)
        branch = next(item for item in observed["branches"] if item["run_id"] == run_id)
        assert branch["verified"] and not branch["completed"] and branch["observation"]["run"] == run
        assert observed["coverage"]["verified"] == 4 and observed["coverage"]["completed"] == 3
        assert observed["decision"] == "incomplete" and observed["request_changes"] == ["root/domain/review"]


@pytest.mark.parametrize("fault", ["missing", "unknown", "invalid-id", "wrong-instance", "bad-result", "nonfinite-result", "nonfinite-record", "nested-result",
                                   "missing-input", "capacity"])
def test_review_report_preserves_other_branches_and_raw_results_when_one_selection_is_unverifiable(reviewed_source, fault):
    state, packet, options = reviewed_source()
    path = "root/general/structure/review"
    run_id = options["runs"][path]
    if fault == "missing":
        del options["runs"][path]
    elif fault == "unknown":
        options["runs"][path] = "not-a-saved-run"
    elif fault == "invalid-id":
        options["runs"][path] = 'not-a-run\n<img src=x onerror=alert(1)>\r<script>alert(1)</script>'
    elif fault == "wrong-instance":
        other = "root/general/correctness/review"
        options["runs"][path], options["runs"][other] = options["runs"][other], run_id
    elif fault == "missing-input":
        (state.root / "runs" / (run_id + ".input") / "task.txt").unlink()
    elif fault == "nonfinite-record":
        with state.connect() as db:
            run = json.loads(db.execute("SELECT document FROM agent_runs WHERE id=?", (run_id,)).fetchone()[0])
            run["reported_detail"] = float("nan")
            db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(run), run_id))
    elif fault in ("bad-result", "nonfinite-result", "nested-result"):
        raw = (b'{"decision":"approve","artifacts":{"response":NaN},"summary":"Non-finite result"}'
               if fault == "nonfinite-result" else
               b'{"extra":' + b'[' * 990 + b'0' + b']' * 990 + b'}' if fault == "nested-result" else
               json.dumps({"decision": "approve", "artifacts": {}, "summary": "No required response"}).encode())
        (state.root / "runs" / run_id / "result.json").write_bytes(raw)
        (state.root / "runs" / (run_id + ".protocol") / "schema.json").write_text("{}", encoding="utf-8")
        with state.connect() as db:
            run = json.loads(db.execute("SELECT document FROM agent_runs WHERE id=?", (run_id,)).fetchone()[0])
            run["result_sha256"] = hashlib.sha256(raw).hexdigest()
            db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(run), run_id))
    else:
        options["max_result_bytes"] = 1
    observed = review_requests.report(state, "demo", packet, **options)
    branch = next(item for item in observed["branches"] if item["instance"] == path)
    assert not branch["verified"] and branch["error"] and observed["decision"] == "incomplete"
    if fault != "capacity":
        domain = next(item for item in observed["branches"] if item["instance"] == "root/domain/review")
        assert domain["completed"] and observed["request_changes"] == ["root/domain/review"]
    if fault in ("wrong-instance", "bad-result", "missing-input"):
        assert branch["observation"]["result"]["available"]
    if fault == "invalid-id":
        rendered = review_requests.markdown(observed)
        assert all(line.startswith("    ") for line in rendered.split("\n") if "<img" in line or "<script" in line)
    if fault in ("nonfinite-result", "nested-result"):
        rendered = review_requests.markdown(observed)
        assert "root/domain/review" in rendered and not branch["observation"]["result"]["available"]


@pytest.mark.parametrize("fault", ["source", "manifest", "duplicate-run", "unknown-instance"])
def test_review_report_rejects_ambiguous_selection_instead_of_silently_changing_scope(source, review_manifest, tmp_path, fault):
    repository, _, original = source
    state = State(tmp_path / "report-state")
    projects.create(state, "demo", repository)
    packet = tmp_path / "report-packet"
    receipt = review_packets.prepare(repository, destination=packet, **original)
    manifest = review_manifest("pretraining")
    options = {"source_kind": "local", "source_sha256": receipt["packet_sha256"],
               "manifest": Path(manifest["path"]), "manifest_digest": manifest["digest"],
               "runs": {"root/domain/review": "domain", "root/general/structure/review": "structure"}}
    if fault == "source":
        options["source_sha256"] = "0" * 64
    elif fault == "manifest":
        options["manifest_digest"] = "0" * 64
    elif fault == "duplicate-run":
        options["runs"]["root/general/structure/review"] = options["runs"]["root/domain/review"]
    else:
        options["runs"]["root/not-declared"] = "not-a-run"
    with pytest.raises(ValueError):
        review_requests.report(state, "demo", packet, **options)


@pytest.mark.parametrize("changed", ["source", "manifest"])
def test_review_report_does_not_attribute_valid_original_runs_to_a_different_valid_source_or_manifest(
        reviewed_source, source, review_manifest, tmp_path, changed):
    state, packet, options = reviewed_source()
    if changed == "source":
        repository, _, original = source
        request = tmp_path / "other-request.md"
        request.write_text("A different complete original requirement", encoding="utf-8")
        packet = tmp_path / "other-source"
        receipt = review_packets.prepare(repository, destination=packet, **{**original, "requirements": request})
        options["source_sha256"] = receipt["packet_sha256"]
    else:
        manifest = review_manifest("posttraining")
        options.update(manifest=Path(manifest["path"]), manifest_digest=manifest["digest"])
    observed = review_requests.report(state, "demo", packet, **options)
    assert observed["decision"] == "incomplete" and observed["coverage"]["verified"] == 0
    assert observed["request_changes"] == []
    for branch in observed["branches"]:
        assert branch["error"] and not branch["verified"]
        assert all(branch["observation"][name]["available"] for name in ("input", "prompt", "result"))


def test_complete_diverged_sources_ignore_worktree_and_survive_repository_removal(source, tmp_path):
    repository, anchor, options = source
    (repository / "src/train.py").write_text("uncommitted content")
    (repository / "AGENTS.md").write_text("uncommitted instructions")
    (repository / "untracked.txt").write_text("untracked")
    destination = tmp_path / "review"
    result = review_packets.prepare(repository, destination=destination, **options)
    material = review_packets.read(destination, sha256=result["packet_sha256"])
    packet = material["packet"]
    assert packet["repository"] == {"id": options["repository_id"], "object_format": "sha1",
        "base": options["base"], "head": options["head"], "diff_base": anchor, "comparison": "merge-base"}
    assert [(item["path"], item["status"]) for item in packet["changes"]] == [
        ("src/deleted.py", "D"), ("src/old.py", "D"), ("src/renamed.py", "A"), ("src/train.py", "M")]
    assert packet["requirements"]["text"].encode() == options["requirements"].read_bytes()
    assert packet["evidence"][0]["text"].encode() == options["evidence"][0].read_bytes()
    source_material = packet["source"]
    for label in ("base", "diff_base", "head"):
        files = source_material[label]["files"]
        assert {"AGENTS.md", "src/AGENTS.md", "caller.py", "config.toml"} <= files.keys()
        for path, file in files.items():
            assert source_material["blobs"][file["git_object"]]["text"].encode() == git(
                repository, "cat-file", "blob", source_material[label]["commit"] + ":" + path)
    old_oid = source_material["diff_base"]["files"]["src/old.py"]["git_object"]
    assert old_oid == source_material["head"]["files"]["src/renamed.py"]["git_object"]
    assert "uncommitted" not in json.dumps(packet) and "untracked.txt" not in source_material["scope"]
    direct = review_packets.prepare(repository, destination=tmp_path / "direct", comparison="base", **options)
    assert direct["repository"]["diff_base"] == options["base"] and direct["changes"] == result["changes"] + 1
    # Git creates read-only loose objects; Windows requires writable files for deletion.
    for object_file in (repository / ".git/objects").rglob("*"):
        if object_file.is_file():
            object_file.chmod(0o600)
    shutil.rmtree(repository)
    assert review_packets.verify(destination, sha256=result["packet_sha256"]) == {key: value for key, value in result.items()
                                                                            if key != "directory"}


def test_cli_is_state_free_and_publication_never_replaces_an_existing_directory(source, tmp_path):
    repository, _, options = source
    destination, home = tmp_path / "packet", tmp_path / "unused-home"
    command = [sys.executable, "-m", "ergora", "--home", str(home), "review"]
    prepared = subprocess.run([*command, "prepare", str(repository), "--base", options["base"], "--head", options["head"],
        "--repository-id", options["repository_id"], "--requirements", str(options["requirements"]),
        "--directory", str(destination), "--context", "caller.py"], capture_output=True, text=True)
    assert prepared.returncode == 0, prepared.stderr
    digest = json.loads(prepared.stdout)["packet_sha256"]
    environment = dict(os.environ, PATH="")
    for operation in ("verify", "read"):
        result = subprocess.run([*command, operation, str(destination), "--sha256", digest],
                                env=environment, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["packet_sha256"] == digest
    assert not home.exists()
    original = (destination / "packet.json").read_bytes()
    with pytest.raises(OSError):
        review_packets.prepare(repository, destination=destination, **options)
    assert (destination / "packet.json").read_bytes() == original
    empty = tmp_path / "already-empty"
    empty.mkdir()
    with pytest.raises(OSError):
        review_packets.prepare(repository, destination=empty, **options)
    assert list(empty.iterdir()) == []
    with pytest.raises(ValueError, match="expected SHA256"):
        review_packets.verify(destination, sha256="0" * 64)


def test_git_environment_replacements_and_executable_repository_configuration_are_ignored(source, tmp_path, monkeypatch):
    repository, anchor, options = source
    marker, helper = tmp_path / "executed", tmp_path / "forbidden.py"
    helper.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n")
    command = f'"{Path(sys.executable).as_posix()}" "{helper.as_posix()}"'
    for key in ("diff.external", "diff.probe.textconv", "filter.probe.clean", "filter.probe.smudge"):
        git(repository, "config", key, command)
    (repository / ".git/info/attributes").write_text("* diff=probe filter=probe\n")
    git(repository, "replace", anchor, options["head"])
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "unrelated"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "diff.external")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", command)
    result = review_packets.prepare(repository, destination=tmp_path / "safe", **options)
    assert result["repository"]["diff_base"] == anchor
    packet = review_packets.read(tmp_path / "safe")["packet"]
    assert "VALUE = 1" in packet["source"]["diff"] and "VALUE = 2" in packet["source"]["diff"]
    assert not marker.exists()


@pytest.mark.parametrize("kind", ["binary", "non-utf8", "lfs", "symlink", "gitlink"])
def test_unsupported_source_rejects_the_whole_packet_with_known_uncovered_paths(source, tmp_path, kind):
    repository, _, options = source
    content = {"binary": b"zero\0byte", "non-utf8": b"\xff", "lfs": (
        b"version https://git-lfs.github.com/spec/v1\n" + b"oid sha256:" + b"0" * 64 + b"\nsize 20\n"),
        "symlink": b"elsewhere"}
    if kind == "gitlink":
        oid, mode = options["head"], "160000"
    else:
        oid = git(repository, "hash-object", "-w", "--stdin", input=content[kind]).decode().strip()
        mode = "120000" if kind == "symlink" else "100644"
    git(repository, "update-index", "--add", "--cacheinfo", mode, oid, "unsupported")
    options["head"] = commit(repository, "unsupported material")
    destination = tmp_path / "unsupported-packet"
    with pytest.raises(ValueError, match="no coverage claimed.*unsupported"):
        review_packets.prepare(repository, destination=destination, **options)
    assert not destination.exists()


def test_missing_promisor_blob_does_not_fetch_even_with_an_available_local_remote(source, tmp_path):
    repository, _, options = source
    remote = tmp_path / "remote.git"
    git(repository, "clone", "-q", "--bare", "--no-hardlinks", str(repository), str(remote))
    git(repository, "config", "remote.origin.url", str(remote))
    git(repository, "config", "remote.origin.promisor", "true")
    git(repository, "config", "remote.origin.partialclonefilter", "blob:none")
    git(repository, "config", "extensions.partialClone", "origin")
    git(repository, "config", "protocol.file.allow", "always")
    oid = git(repository, "rev-parse", options["head"] + ":src/train.py").decode().strip()
    object_file = repository / ".git/objects" / oid[:2] / oid[2:]
    object_file.chmod(0o600)
    object_file.unlink()
    with pytest.raises(ValueError, match="local Git blob"):
        review_packets.prepare(repository, destination=tmp_path / "missing", **options)
    assert not object_file.exists() and not (tmp_path / "missing").exists()


@pytest.mark.parametrize("payload_size", [2048, 8192])
def test_source_limits_follow_the_configured_budget_without_truncating(source, tmp_path, payload_size):
    repository, _, options = source
    (repository / "src/train.py").write_bytes(b"x" * payload_size)
    git(repository, "add", "src/train.py")
    options["head"] = commit(repository, "large candidate")
    first = tmp_path / "full"
    review_packets.prepare(repository, destination=first, **options)
    packet = review_packets.read(first)["packet"]
    total = sum(len(blob["text"].encode()) + len(f'{oid} blob {len(blob["text"].encode())}') + 2
                for oid, blob in packet["source"]["blobs"].items())
    configured = max(total, len(packet["source"]["diff"].encode())) + 512
    review_packets.prepare(repository, destination=tmp_path / "configured", max_source_bytes=configured, **options)
    rejected = tmp_path / "too-small"
    with pytest.raises(ValueError, match="no coverage claimed.*input byte limit"):
        review_packets.prepare(repository, destination=rejected, max_source_bytes=total - 1, **options)
    assert not rejected.exists()


def test_document_budget_stops_aggregate_reads_before_building_an_oversized_packet(source, tmp_path, monkeypatch):
    repository, _, options = source
    evidence = [tmp_path / "large-baseline.txt", tmp_path / "large-candidate.txt"]
    for path in evidence:
        path.write_bytes(b"x" * (review_packets.MAX_PACKET_BYTES * 3 // 5))
    options["evidence"] = evidence
    observed, original = [], Path.open
    documents = {options["requirements"], *evidence}

    class ObservedReader:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def read(self, size):
            raw = self.stream.read(size)
            observed.append(len(raw))
            return raw

        def __exit__(self, *args):
            self.stream.close()

    def opening(path, *args, **kwargs):
        stream = original(path, *args, **kwargs)
        return ObservedReader(stream) if path in documents and args == ("rb",) else stream

    monkeypatch.setattr(Path, "open", opening)
    with pytest.raises(ValueError, match="packet.*byte|10 MB"):
        review_packets.prepare(repository, destination=tmp_path / "over-budget", **options)
    assert sum(observed) <= review_packets.MAX_PACKET_BYTES + 1
    assert not (tmp_path / "over-budget").exists()


@pytest.mark.parametrize("tamper", ["blob", "dangling", "change", "scope", "document", "diff"])
def test_offline_verification_checks_content_and_reference_consistency(source, tmp_path, tamper):
    repository, _, options = source
    destination = tmp_path / "review"
    review_packets.prepare(repository, destination=destination, **options)
    packet = json.loads((destination / "packet.json").read_bytes())
    oid = next(iter(packet["source"]["blobs"]))
    if tamper == "blob":
        packet["source"]["blobs"][oid]["text"] += "modified"
    elif tamper == "dangling":
        del packet["source"]["blobs"][oid]
    elif tamper == "change":
        packet["changes"].pop()
    elif tamper == "scope":
        packet["source"]["scope"].remove("AGENTS.md")
    elif tamper == "document":
        packet["requirements"]["text"] += "modified"
    else:
        packet["source"]["diff"] = "there are no changes"
    (destination / "packet.json").write_bytes(json.dumps(packet).encode())
    with pytest.raises(ValueError):
        review_packets.verify(destination)


def test_one_commit_cannot_have_conflicting_file_tables_in_different_labels(source, tmp_path):
    repository, _, options = source
    destination = tmp_path / "review"
    review_packets.prepare(repository, comparison="base", destination=destination, **options)
    packet = json.loads((destination / "packet.json").read_bytes())
    packet["source"]["base"]["files"]["src/train.py"] = packet["source"]["head"]["files"]["src/train.py"]
    (destination / "packet.json").write_bytes(json.dumps(packet).encode())
    with pytest.raises(ValueError, match="same commit"):
        review_packets.verify(destination)


def test_offline_diff_cannot_exceed_the_collected_material_budget(source, tmp_path):
    repository, _, options = source
    destination = tmp_path / "review"
    review_packets.prepare(repository, destination=destination, **options)
    packet = json.loads((destination / "packet.json").read_bytes())
    packet["source"]["diff"] += "x" * packet["limits"]["max_source_bytes"]
    packet["source"]["diff_sha256"] = hashlib.sha256(packet["source"]["diff"].encode()).hexdigest()
    (destination / "packet.json").write_bytes(json.dumps(packet).encode())
    with pytest.raises(ValueError, match="diff exceeds.*byte limit"):
        review_packets.verify(destination)


def test_ambiguous_merge_base_requires_explicit_direct_comparison(source, tmp_path):
    repository, anchor, options = source
    tree = git(repository, "rev-parse", anchor + "^{tree}").decode().strip()
    def node(parents, message):
        args = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit-tree", tree]
        for parent in parents:
            args.extend(["-p", parent])
        return git(repository, *args, input=message.encode()).decode().strip()
    left, right = node([anchor], "left"), node([anchor], "right")
    options.update(base=node([left, right], "merge-left"), head=node([right, left], "merge-right"))
    with pytest.raises(ValueError, match="unique merge-base"):
        review_packets.prepare(repository, destination=tmp_path / "ambiguous", **options)
    result = review_packets.prepare(repository, comparison="base", destination=tmp_path / "explicit", **options)
    assert result["changes"] == 0 and result["repository"]["diff_base"] == options["base"]


def test_sha256_git_objects_are_verified_without_assuming_sha1_width(tmp_path):
    repository = tmp_path / "sha256"
    repository.mkdir()
    git(repository, "init", "-q", "--initial-branch=main", "--object-format=sha256")
    (repository / "source.txt").write_bytes(b"old\n")
    git(repository, "add", ".")
    base = commit(repository, "base")
    (repository / "source.txt").write_bytes(b"new\r\n")
    git(repository, "add", ".")
    head = commit(repository, "head")
    requirements = tmp_path / "request.md"
    requirements.write_text("Preserve behavior")
    result = review_packets.prepare(repository, repository_id="local/sha256", base=base, head=head,
                                    requirements=requirements, destination=tmp_path / "review")
    assert result["repository"]["object_format"] == "sha256" and len(head) == 64
    assert review_packets.verify(tmp_path / "review")["packet_sha256"] == result["packet_sha256"]
