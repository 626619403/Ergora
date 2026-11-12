"""Task-scoped fixed resources and actual official SDK stdio connections."""

import asyncio
import base64
import builtins
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ergora import agent_definitions, agent_runs, agents, processes, projects, task_mcp, workflow_definitions as workflows
from ergora.asset_trees import digest_tree
from ergora.cli import main
from ergora.state import State


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
READ = {"read": ["definitions", "workspace"], "write": [], "shell": False, "network": []}
LIMITS = {"depth": 8, "instances": 128, "concurrency": 4, "material_bytes": 262144}


@pytest.fixture
def scoped(tmp_path):
    if sys.platform != "linux" or importlib.util.find_spec("mcp") is None:
        pytest.skip("Creating fixed task MCP scopes requires Linux and the task-mcp extra")
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "state")
    projects.create(state, "demo", repo)
    source = tmp_path / "agent"
    shutil.copytree(EXAMPLES / "agents/architecture-reviewer", source)
    appendix = source / "skills/architecture-evidence/references"
    appendix.mkdir()
    (appendix / "leaf.bin").write_bytes(b"\xff\0Leaf attachment.\r\n")
    (source / "undeclared.txt").write_text("This same-directory file is not a resource.")
    doc = json.loads((source / "agent.json").read_text())
    doc["resources"][-1]["digest"] = digest_tree(source / "skills/architecture-evidence")[0]
    (source / "agent.json").write_text(json.dumps(doc))
    agent = agent_definitions.import_bundle(state, source)
    sibling_source = tmp_path / "sibling"
    shutil.copytree(source, sibling_source)
    doc["id"] = "sibling-reviewer"
    (sibling_source / "agent.json").write_text(json.dumps(doc))
    sibling = agent_definitions.import_bundle(state, sibling_source)

    def ref(document, kind):
        return {"kind": kind, "id": document["definition"]["id"], "version": "1.0.0", "digest": document["digest"]}

    def node(identity, document, kind):
        return {"id": identity, "ref": ref(document, kind), "depends_on": [], "inputs": {"task": {"input": "task"}},
                **({"role": "reviewer", "permissions": deepcopy(READ)} if kind == "agent" else {})}

    def workflow(identity, nodes):
        directory = tmp_path / identity
        skill = directory / "skills" / (identity + "-skill")
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_bytes(f"---\nname: {identity}-skill\ndescription: Scoped ancestor resource\n---\nRead {identity} instructions.\n".encode())
        (skill / "attachment.txt").write_bytes((identity + " ancestor attachment. 资料\r\n").encode())
        (directory / "workflow.json").write_text(json.dumps({"schema_version": 1, "id": identity, "version": "1.0.0",
            "description": "Scoped resource workflow", "permissions": READ, "limits": LIMITS,
            "inputs": ["task"], "outputs": {"result": {"node": nodes[0]["id"], "output": "result"}}, "nodes": nodes,
            "resources": [{"id": identity + "-skill", "kind": "skill", "path": "skills/" + skill.name,
                           "digest": digest_tree(skill)[0]}]}))
        return workflows.import_bundle(state, directory)

    inner = workflow("inner", [node("review", agent, "agent")])
    workflow("outer", [node("inner", inner, "workflow"), node("sibling", sibling, "agent")])
    source = tmp_path / "input"
    workflows.prepare_input(state.root, "outer", "1.0.0", "root/inner/review",
                            {"schema_version": 1, "permissions": READ, "limits": LIMITS}, b"Review the exact input.", source, 30000)
    prepared = workflows.inspect_input(source, material=True)
    scope = task_mcp.freeze(prepared, "a" * 32, tmp_path / "scope.json")
    return state, prepared, scope


def test_all_ancestors_and_skill_attachments_are_fixed_without_exposing_siblings_or_unlisted_files(scoped):
    _, prepared, scope = scoped
    view = task_mcp.ResourceView.load(Path(scope["path"]), scope["sha256"])
    names = [item["uri"] for item in view.list()["files"]]
    for uri in ("definitions/workflow/outer/1.0.0/skills/outer-skill/attachment.txt",
                "definitions/workflow/inner/1.0.0/skills/inner-skill/attachment.txt"):
        assert "ancestor attachment" in view.read(uri)["content"]
    binary = "definitions/agent/architecture-reviewer/1.0.0/skills/architecture-evidence/references/leaf.bin"
    read = view.read(binary)
    assert read["encoding"] == "base64" and base64.b64decode(read["content"]) == b"\xff\0Leaf attachment.\r\n"
    assert all("sibling" not in uri and "undeclared" not in uri and "index.json" not in uri for uri in names)
    assert all(f"Read {identity} instructions." in prepared["prompt"] for identity in ("outer", "inner"))
    assert {source["instance"] for item in view.list()["files"] for source in item["sources"]} == {"root", "root/inner", "root/inner/review"}
    shutil.rmtree(prepared["path"])
    assert view.read(binary) == read


@pytest.mark.parametrize("path", ["../scope.json", "/etc/passwd", "C:/secret", "\\\\server\\share", "definitions/../index.json",
                                  "definitions//agent", "definitions\0private", "workspace/README.md",
                                  "definitions/agent/sibling-reviewer/1.0.0/instructions.md"])
def test_tool_paths_cannot_escape_or_read_other_input_assets(scoped, path):
    _, _, scope = scoped
    view = task_mcp.ResourceView.load(Path(scope["path"]), scope["sha256"])
    for operation in (view.read, view.list):
        with pytest.raises(ValueError):
            operation(path)


def test_pages_reassemble_exact_bytes_and_keep_complete_metadata(scoped):
    _, _, scope = scoped
    view = task_mcp.ResourceView.load(Path(scope["path"]), scope["sha256"])
    page, names, offset = None, [], 0
    while page is None or page["next_offset"] is not None:
        page = view.list(offset=offset, max_entries=1)
        names.extend(item["uri"] for item in page["files"])
        offset = page["next_offset"]
    assert names == sorted(view.contents)
    uri = next(name for name in names if name.endswith("attachment.txt"))
    content, offset = bytearray(), 0
    while offset is not None:
        page = view.read(uri, offset=offset, max_bytes=3)
        content.extend(page["content"].encode("utf-8") if page["encoding"] == "utf-8" else base64.b64decode(page["content"]))
        offset = page["next_offset"]
    assert bytes(content) == view.contents[uri] and hashlib.sha256(content).hexdigest() == page["sha256"]
    for operation, kwargs in ((view.read, {"path": uri, "offset": -1}), (view.read, {"path": uri, "max_bytes": True}),
                              (view.list, {"max_entries": 101})):
        with pytest.raises(ValueError):
            operation(**kwargs)


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_modified_resource_links_and_special_files_are_rejected(scoped, tmp_path, kind):
    _, prepared, _ = scoped
    agent = next(item for item in prepared["composition"]["instances"] if item["path"] == prepared["request"]["instance"])
    ref = agent["ref"]
    file = Path(prepared["path"]) / "assets/agent-definitions/objects" / ref["digest"] / "instructions.md"
    outside = tmp_path / "outside"
    file.rename(outside)
    if kind == "symlink":
        file.symlink_to(outside)
    elif kind == "hardlink":
        os.link(outside, file)
    else:
        os.mkfifo(file)
    with pytest.raises((OSError, ValueError)):
        task_mcp.freeze(prepared, "b" * 32, tmp_path / "refused-scope.json")
    assert not (tmp_path / "refused-scope.json").exists()


def test_replaced_file_between_inventory_and_open_is_not_followed(scoped, tmp_path, monkeypatch):
    _, prepared, _ = scoped
    original = task_mcp._fixed_bytes
    called = False
    def replaced(root, name, expected):
        nonlocal called
        if not called:
            called = True
            target = root / name
            outside = tmp_path / "secret"
            outside.write_text("This must not become a tool response.")
            target.unlink()
            target.symlink_to(outside)
        return original(root, name, expected)
    monkeypatch.setattr(task_mcp, "_fixed_bytes", replaced)
    with pytest.raises(OSError):
        task_mcp.freeze(prepared, "b" * 32, tmp_path / "refused-scope.json")
    assert called and not (tmp_path / "refused-scope.json").exists()


def test_actual_official_sdk_stdio_roundtrip_and_missing_server(scoped, tmp_path):
    _, _, scope = scoped
    audit = tmp_path / "preflight.jsonl"
    result = asyncio.run(task_mcp.probe(task_mcp.launch(scope, audit), tmp_path / "probe.stderr"))
    assert result["initialized"] and result["tools"] == ["list", "read"]
    assert task_mcp.verify_native(audit, scope["sha256"])["ready"]
    events = [json.loads(line) for line in audit.read_text().splitlines()]
    start = next(event for event in events if event.get("event") == "started")
    assert not any("KEY" in key or "TOKEN" in key or key == "PYTHONPATH" for key in start["environment_keys"])
    assert any(event.get("event") == "closed" for event in events)
    with pytest.raises(ValueError, match="preflight failed"):
        asyncio.run(task_mcp.probe({"command": str(tmp_path / "missing"), "args": []}, tmp_path / "failed.stderr"))


def test_attachment_delivery_requires_continuous_actual_read_ranges(scoped, tmp_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    _, _, scope = scoped
    audit = tmp_path / 'resource-ranges.jsonl'
    document = json.loads(Path(scope['path']).read_bytes())
    attachments = [uri for uri in document['files'] if uri.endswith(('attachment.txt', 'leaf.bin'))]

    async def exercise():
        async with stdio_client(StdioServerParameters(**task_mcp.launch(scope, audit))) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                await session.list_tools()
                for uri in attachments:
                    # Overlapping responses do not fill the missing byte at 3.
                    for offset, size in ((0, 3), (0, 3), (4, 65536)):
                        response = await session.call_tool('read', {'path': uri, 'offset': offset, 'max_bytes': size})
                        assert not response.is_error
                with pytest.raises(ValueError, match='not completely read'):
                    task_mcp.verify_reads(document, audit.read_bytes())
                for uri in attachments:
                    response = await session.call_tool('read', {'path': uri, 'offset': 3, 'max_bytes': 1})
                    assert not response.is_error
        return task_mcp.verify_reads(document, audit.read_bytes())

    coverage = asyncio.run(exercise())['attachments']
    assert coverage.keys() == set(attachments)
    assert all(item['size'] == item['covered_bytes'] for item in coverage.values())


def test_successful_model_cannot_substitute_for_missing_native_mcp_connection(scoped, monkeypatch, capsys):
    state, prepared, _ = scoped
    async def preflight(*args):
        return {"initialized": True, "tools": ["list", "read"], "read_only_probe": "succeeded"}
    def model(*args, **kwargs):
        return {"status": "succeeded", "returncode": 0}
    monkeypatch.setattr(task_mcp, "probe", preflight)
    monkeypatch.setattr(agents, "invoke", model)
    assert main(["--home", str(state.root), "composition", "run-input", "demo", prepared["path"], "--mode", "task-mcp"]) == 1
    run = json.loads(capsys.readouterr().out)
    assert run["status"] == "failed" and run["finished"] and "receipt is missing" in run["error"]
    assert run == agent_runs.runs(State(state.root), "demo")[0]


def test_task_mcp_reports_missing_dependency_or_platform_before_a_model_call(monkeypatch):
    if sys.platform == "linux":
        monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
        expected = "optional dependency"
    else:
        expected = "requires Linux"
    with pytest.raises(ValueError, match=expected):
        task_mcp.check_available()


@pytest.mark.parametrize("backend", ["codex", "claude-code"])
@pytest.mark.parametrize("transport_failure", [True, False])
def test_native_transport_failure_cannot_be_hidden_by_a_valid_result_but_resource_rejection_can_recover(
        scoped, monkeypatch, capsys, backend, transport_failure):
    state, prepared, _ = scoped
    result = {"summary": "Review completed", "artifacts": {"response": "Evidence"}, "decision": "approve"}

    async def preflight(*args):
        return {"initialized": True, "tools": ["list", "read"], "read_only_probe": "succeeded"}

    def native(argv, cwd, output, *args, **kwargs):
        running = agent_runs.runs(state, "demo")[0]
        digest = running["task_mcp"]["scope"]["sha256"]
        audit = state.root / "runs" / (running["id"] + ".mcp-native.jsonl")
        audit.write_text(json.dumps({"scope_sha256": digest, "method": "tools/list", "success": True,
                                     "tools": ["list", "read"]}) + "\n", encoding="utf-8")
        # Shapes captured from the actual CLIs: both final results are valid.
        if backend == "codex":
            Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(result), encoding="utf-8")
            events = [{"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "ergora_task",
                "tool": "read", "status": "failed", "result": None if transport_failure else {
                    "content": [{"type": "text", "text": "Error executing tool read"}]},
                "error": {"message": "Transport closed"} if transport_failure else None}}]
        else:
            events = [
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "call_1",
                    "name": "mcp__ergora_task__read", "input": {"path": "../forbidden"}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "call_1",
                    "is_error": True, "content": "Connection closed" if transport_failure else "Error executing tool read"}]},
                 "tool_use_result": "Error: Connection closed" if transport_failure else {
                     "content": "Error: Error executing tool read", "_meta": {
                         "io.modelcontextprotocol/serverInfo": {"name": "ergora-task", "version": "1"}}}},
                {"type": "result", "is_error": False, "structured_output": result}]
        output.mkdir()
        (output / "stdout.txt").write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        return {"status": "succeeded", "returncode": 0, "output": str(output)}

    monkeypatch.setattr(task_mcp, "probe", preflight)
    monkeypatch.setattr(processes, "run", native)
    code = main(["--home", str(state.root), "composition", "run-input", "demo", prepared["path"],
                 "--mode", "task-mcp", "--backend", backend])
    run = json.loads(capsys.readouterr().out)
    assert code == (1 if transport_failure else 0)
    assert run["status"] == ("failed" if transport_failure else "succeeded") and run["finished"]
    if transport_failure:
        assert "transport" in run["error"].lower() and not (Path(run["output"]) / "result.json").exists()
    else:
        assert json.loads(Path(run["result"]).read_text()) == result
    assert run == agent_runs.runs(State(state.root), "demo")[0]


def test_broken_optional_sdk_import_is_a_finished_failure_before_model_call(scoped, monkeypatch, capsys):
    state, prepared, _ = scoped
    original = builtins.__import__

    def imported(name, *args, **kwargs):
        if name == "mcp.client.stdio":
            raise ModuleNotFoundError("Injected missing SDK submodule")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", imported)
    monkeypatch.setattr(processes, "run", lambda *a, **k: pytest.fail("Broken SDK must not call the model"))
    assert main(["--home", str(state.root), "composition", "run-input", "demo", prepared["path"],
                 "--mode", "task-mcp"]) == 1
    run = json.loads(capsys.readouterr().out)
    assert run["status"] == "failed" and run["finished"] and "working mcp 2.3.0" in run["error"]
    assert run == agent_runs.runs(State(state.root), "demo")[0]


@pytest.mark.parametrize("event", [
    {"type": "assistant", "message": {}},
    {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "mcp__ergora_task__read"}]}},
])
def test_malformed_native_stream_finishes_durably(scoped, monkeypatch, capsys, event):
    state, prepared, _ = scoped

    async def preflight(*args):
        return {"initialized": True, "tools": ["list", "read"]}

    def native(argv, cwd, output, *args, **kwargs):
        output.mkdir()
        result = {"type": "result", "is_error": False, "structured_output": {
            "summary": "claim", "artifacts": {"response": "claim"}, "decision": "approve"}}
        (output / "stdout.txt").write_text(json.dumps(event) + "\n" + json.dumps(result) + "\n", encoding="utf-8")
        return {"status": "succeeded", "returncode": 0, "output": str(output)}

    monkeypatch.setattr(task_mcp, "probe", preflight)
    monkeypatch.setattr(processes, "run", native)
    assert main(["--home", str(state.root), "composition", "run-input", "demo", prepared["path"],
                 "--mode", "task-mcp", "--backend", "claude-code"]) == 1
    run = json.loads(capsys.readouterr().out)
    assert run["status"] == "failed" and run["finished"] and "Invalid structured" in run["error"]
    assert not (Path(run["output"]) / "result.json").exists()
    assert run == agent_runs.runs(State(state.root), "demo")[0]


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_replaced_scope_links_and_fifo_fail_without_blocking(scoped, tmp_path, kind):
    _, _, scope = scoped
    target = Path(scope["path"])
    original = tmp_path / "original-scope.json"
    target.rename(original)
    if kind == "symlink":
        target.symlink_to(original)
    elif kind == "hardlink":
        os.link(original, target)
    else:
        os.mkfifo(target)
    # A process deadline also catches the old blocking FIFO open. The native
    # service uses this same installed module under isolated Python execution.
    program = ("from pathlib import Path;import sys;from ergora.task_mcp import ResourceView\n"
               "try: ResourceView.load(Path(sys.argv[1]),sys.argv[2])\n"
               "except (OSError,ValueError): print('refused')\n"
               "else: print('accepted')\n")
    result = subprocess.run([sys.executable, "-I", "-c", program, str(target), scope["sha256"]],
                            capture_output=True, text=True, timeout=5)
    assert result.returncode == 0 and result.stdout.strip() == "refused", result.stderr


def test_interrupt_during_preflight_is_a_durable_cancelled_run(scoped, monkeypatch, capsys):
    state, prepared, _ = scoped

    async def interrupted(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(task_mcp, "probe", interrupted)
    monkeypatch.setattr(processes, "run", lambda *a, **k: pytest.fail("Interrupted preflight must not call the model"))
    assert main(["--home", str(state.root), "composition", "run-input", "demo", prepared["path"],
                 "--mode", "task-mcp"]) == 1
    run = json.loads(capsys.readouterr().out)
    assert run["status"] == "cancelled" and run["finished"]
    assert run == agent_runs.runs(State(state.root), "demo")[0]


@pytest.mark.parametrize("backend", ["codex", "claude-code"])
@pytest.mark.parametrize("mode", ["text-only", "task-mcp"])
def test_capability_check_has_complete_ceilings_and_resources_without_starting_a_run(scoped, monkeypatch, capsys, backend, mode):
    state, prepared, _ = scoped
    revision = state.project("demo")["revision"]

    def not_called(*args, **kwargs):
        pytest.fail("Admission must not freeze scope, probe servers or invoke a model")

    monkeypatch.setattr(task_mcp, "freeze", not_called)
    monkeypatch.setattr(task_mcp, "probe", not_called)
    monkeypatch.setattr(agents, "invoke", not_called)
    assert main(["--home", str(state.root), "composition", "check-input", "demo", prepared["path"],
                 "--mode", mode, "--backend", backend, "--model", "selected-model", "--backend-reason", "Review diversity"]) == 0
    admission = json.loads(capsys.readouterr().out)
    policy = admission["policy"]
    assert admission["kind"] == "composition-admission" and admission["formal_execution_authorized"] is False
    assert admission["binding"] == {"tool": backend, "model": "selected-model"} and admission["backend_reason"] == "Review diversity"
    assert policy["requested_permissions"] == READ
    assert [item["path"] for item in policy["permission_ceilings"]] == ["supplied-grant", "root", "root/inner", "root/inner/review"]
    assert all(item["permissions"] == READ for item in policy["permission_ceilings"])
    capabilities = policy["capabilities"]
    assert capabilities["fixed_resource_read"]["status"] == ("enforced" if mode == "task-mcp" else "unsupported")
    assert capabilities["task_mcp"]["tools"] == (["list", "read"] if mode == "task-mcp" else [])
    assert all(capabilities[name]["status"] == "unsupported" for name in (
        "workspace_read", "write", "shell", "tool_network_origins", "external_mcp", "host_isolation"))
    if backend == "claude-code" and mode == "task-mcp":
        assert "OAuth/keychain are not read" in policy["authentication"]
    assert capabilities["backend_sandbox"]["status"] == ("advisory" if backend == "codex" else "unsupported")
    assert {source["instance"] for resource in admission["context"]["resources"] for source in resource["sources"]} == {
        "root", "root/inner", "root/inner/review"}
    assert all("text" not in resource for resource in admission["context"]["resources"])
    assert agent_runs.runs(state, "demo") == [] and not (state.root / "runs").exists()
    assert state.project("demo")["revision"] == revision
