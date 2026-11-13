"""A completed SDK turn must not silently bypass restricted call acceptance."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from ergora import agent_backends, agent_definitions, agent_runs, agents, processes, projects, task_mcp, workflow_definitions as workflows
from ergora.data.drivers import deepseek
from ergora.cli import main
from ergora.state import State


def binding():
    return {"tool": "deepseek-harness", "python": sys.executable, "model": "fixture-model",
            "base_url": "http://127.0.0.1:1/v1", "api_key_env": "FIXTURE_MODEL_KEY"}


@pytest.mark.skipif(sys.platform != "linux", reason="Read-only SDK adapter currently admits Linux/WSL2")
@pytest.mark.parametrize("case", ["complete", "unfinished", "tool-error", "fenced-json", "wrong-schema"])
def test_native_completion_and_result_are_independent_acceptance_checks(tmp_path, monkeypatch, case):
    expected = {"summary": "Supplied evidence reviewed", "artifacts": {"response": "Coverage"}, "decision": "approve"}
    native = {"session_id": "fixed-session", "finish_reason": "completed", "events": [], "final_response": json.dumps(expected)}
    if case == "unfinished":
        native["finish_reason"] = "max_tokens"
    elif case == "tool-error":
        native["events"] = [{"type": "tool/result", "data": {"message": {"isError": True}}}]
    elif case == "fenced-json":
        native["final_response"] = "```json\n" + native["final_response"] + "\n```"
    elif case == "wrong-schema":
        native["final_response"] = json.dumps({**expected, "decision": "accept"})

    def run(argv, cwd, output, timeout, stdin, env, **kwargs):
        assert argv[:2] == [sys.executable, "-I"]
        request_path = Path(argv[3])
        request = json.loads(request_path.read_text(encoding="utf-8"))
        assert request["binding"] == binding() and request["mode"] == "text-only" and request["task_mcp"] is None
        assert request["prompt"] == "Review supplied material" and request["schema"] == agents.result_schema(["response"], True)
        (request_path.parent / "native-result.json").write_text(json.dumps(native), encoding="utf-8")
        output.mkdir()
        # Even a valid stdout cannot mask a failed native receipt.
        (output / "stdout.txt").write_text(json.dumps(expected), encoding="utf-8")
        return {"status": "succeeded", "returncode": 0, "output": str(output)}

    monkeypatch.setattr(processes, "run", run)
    result = agents.invoke(binding(), "reviewer", "Review supplied material", tmp_path, tmp_path / "output", 12,
                           agents.result_schema(["response"], True), mode="text-only")
    if case == "complete":
        assert result["status"] == "succeeded" and json.loads(Path(result["result"]).read_text()) == expected
    else:
        assert result["status"] == "failed" and "Invalid structured agent result" in result["error"]
        assert not (tmp_path / "output/result.json").exists()


@pytest.mark.skipif(sys.platform != "linux", reason="Read-only SDK adapter currently admits Linux/WSL2")
@pytest.mark.parametrize("mode", ["native", "workspace-task-mcp"])
def test_unadmitted_modes_fail_before_creating_protocol_or_running_model(tmp_path, monkeypatch, mode):
    monkeypatch.setattr(processes, "run", lambda *args, **kwargs: pytest.fail("Unsupported call reached process owner"))
    with pytest.raises(ValueError, match="does not support"):
        agents.invoke(binding(), "reviewer", "Review", tmp_path, tmp_path / "output", 12, mode=mode)
    assert list(tmp_path.iterdir()) == []


@pytest.fixture
def native_archive(tmp_path):
    protocol = tmp_path / "run.protocol"
    cwd = tmp_path / "run.cwd"
    home = protocol / "native-home"
    archive = home / "sessions/project/fixed-session/session.v4.jsonl"
    archive.parent.mkdir(parents=True)
    identity = protocol / "native-identity.json"
    identity.write_text(json.dumps({"session_id": "fixed-session", "home": str(home), "profile": "sdk-minimal"}))
    header = {"version": 4, "id": "fixed-session", "cwd": str(cwd)}
    raw = (json.dumps(header) + "\n" + json.dumps({"type": "text", "text": "历史🙂" * 9001}, ensure_ascii=False) + "\n").encode()
    archive.write_bytes(raw)
    adapter = agent_backends.for_binding(binding())
    return adapter, protocol, cwd, identity, archive, raw


@pytest.mark.skipif(sys.platform != "linux", reason="Native archive reads admit Linux/WSL2")
@pytest.mark.parametrize("limit", [4093, 65536])
def test_archived_history_reconstructs_multibyte_bytes_without_starting_backend(native_archive, monkeypatch, limit):
    adapter, protocol, cwd, _, archive, original = native_archive
    monkeypatch.setattr(processes, "run", lambda *args, **kwargs: pytest.fail("Archive read started a process"))
    monkeypatch.setattr(adapter, "executable", lambda: pytest.fail("Archive read inspected the interpreter"))
    offset, revision, reconstructed = 0, None, bytearray()
    while True:
        page = adapter.archived_history(protocol, cwd=cwd, offset=offset, limit=limit, revision=revision)
        chunk = page["content"].encode()
        assert page["available"] and 0 < len(chunk) == page["bytes_read"] <= limit
        assert page["offset"] == offset and page["size_bytes"] == len(original)
        assert not page["complete"] and page["writer_state"] == "unconfirmed"
        assert revision is None or page["revision"] == revision
        reconstructed.extend(chunk)
        if page["next_offset"] is None:
            break
        revision, offset = page["revision"], page["next_offset"]
        assert offset == len(reconstructed)
    assert reconstructed == original == archive.read_bytes()


@pytest.mark.skipif(sys.platform != "linux", reason="Native archive reads admit Linux/WSL2")
@pytest.mark.parametrize("change", ["append", "replace"])
def test_archived_history_rejects_old_revision_after_file_changes(native_archive, change):
    adapter, protocol, cwd, _, archive, original = native_archive
    first = adapter.archived_history(protocol, cwd=cwd, offset=0, limit=4093, revision=None)
    if change == "append":
        with archive.open("ab") as stream:
            stream.write(b'{"type":"session/end-seed"}\n')
    else:
        replacement = archive.with_suffix(".replacement")
        replacement.write_bytes(original)
        replacement.replace(archive)
    with pytest.raises(ValueError, match="changed; restart"):
        adapter.archived_history(protocol, cwd=cwd, offset=first["next_offset"], limit=4093, revision=first["revision"])
    fresh = adapter.archived_history(protocol, cwd=cwd, offset=0, limit=4093, revision=None)
    assert fresh["revision"] != first["revision"]


@pytest.mark.skipif(sys.platform != "linux", reason="Native archive reads admit Linux/WSL2")
@pytest.mark.parametrize("change", ["home", "session", "cwd", "generation", "symlink", "fifo"])
def test_archived_history_refuses_unrelated_or_unsupported_storage(native_archive, change):
    import os

    adapter, protocol, cwd, identity, archive, original = native_archive
    if change in ("home", "session"):
        document = json.loads(identity.read_bytes())
        document["home" if change == "home" else "session_id"] = "other"
        identity.write_text(json.dumps(document))
    elif change == "cwd":
        archive.write_bytes(original.replace(str(cwd).encode(), str(cwd.with_name("other.cwd")).encode(), 1))
    elif change == "generation":
        archive.with_name("session.v4.1.jsonl").write_bytes(b"future generation\n")
    else:
        archive.unlink()
        if change == "symlink":
            outside = protocol.parent / "unrelated.txt"
            outside.write_bytes(original)
            archive.symlink_to(outside)
        else:
            os.mkfifo(archive)
    with pytest.raises((OSError, ValueError)):
        adapter.archived_history(protocol, cwd=cwd, offset=0, limit=4093, revision=None)


@pytest.mark.skipif(sys.platform != "linux", reason="Native archive reads admit Linux/WSL2")
def test_archived_history_refuses_intermediate_ancestor_symlink(native_archive, tmp_path):
    adapter, protocol, cwd, _, _, _ = native_archive
    real = tmp_path / "real" / "runs"
    real.mkdir(parents=True)
    protocol.rename(real / protocol.name)
    alias = tmp_path / "alias"
    alias.symlink_to(real.parent, target_is_directory=True)
    protocol = alias / "runs" / protocol.name
    identity = protocol / "native-identity.json"
    document = json.loads(identity.read_bytes())
    document["home"] = str(protocol / "native-home")
    identity.write_text(json.dumps(document))
    with pytest.raises(OSError):
        adapter.archived_history(protocol, cwd=cwd, offset=0, limit=4093, revision=None)


@pytest.mark.skipif(sys.platform != "linux", reason="Native archive reads admit Linux/WSL2")
@pytest.mark.parametrize("addition", ["generation", "session"])
def test_archived_history_refuses_layout_changes_during_a_page(native_archive, monkeypatch, addition):
    adapter, protocol, cwd, _, archive, _ = native_archive
    original_decoder = deepseek.codecs.getincrementaldecoder

    def mutate_after_listing(encoding):
        if addition == "generation":
            archive.with_name("session.v4.1.jsonl").write_bytes(b"future generation\n")
        else:
            (archive.parent.parent / "another-session").mkdir()
        return original_decoder(encoding)

    monkeypatch.setattr(deepseek.codecs, "getincrementaldecoder", mutate_after_listing)
    with pytest.raises(ValueError, match="directory changed"):
        adapter.archived_history(protocol, cwd=cwd, offset=0, limit=4093, revision=None)


@pytest.fixture
def continuation(tmp_path, monkeypatch):
    """Exercise the product driver with a deterministic single-input SDK double.

    The double delays persistence until close, as the real SDK can. Actual SDK,
    transport, timeout and cancellation acceptance runs separately on loopback.
    """
    if sys.platform != "linux":
        pytest.skip("Native continuation currently admits Linux/WSL2")
    pytest.importorskip("mcp")
    examples = Path(__file__).resolve().parents[1] / "examples"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    state = State(tmp_path / "control")
    projects.create(state, "demo", repo)
    agent_source = tmp_path / "agent"
    shutil.copytree(examples / "agents/architecture-reviewer", agent_source)
    definition = json.loads((agent_source / "agent.json").read_bytes())
    definition["backend"] = binding()
    (agent_source / "agent.json").write_text(json.dumps(definition))
    agent = agent_definitions.import_bundle(state, agent_source)
    workflow_source = tmp_path / "workflow"
    shutil.copytree(examples / "composition/structure-review", workflow_source)
    workflow = json.loads((workflow_source / "workflow.json").read_bytes())
    workflow["nodes"][0]["ref"]["digest"] = agent["digest"]
    (workflow_source / "workflow.json").write_text(json.dumps(workflow))
    workflows.import_bundle(state, workflow_source)
    grant = {"schema_version": 1, "permissions": workflow["permissions"], "limits": workflow["limits"]}

    def prepare(name, task):
        source = tmp_path / name
        workflows.prepare_input(state.root, "structure-review", "1.0.0", "root/review", grant, task, source, 30000)
        return source

    source = prepare("source", b"Remember SOURCE_MEMORY. Read all inherited attachments.")
    followup = prepare("followup", b"Recall SOURCE_MEMORY and read all inherited attachments again.")
    calls, options = [], {}
    answer = {"summary": "Reviewed", "artifacts": {"response": "Source response"}, "decision": "approve"}

    class Harness:
        def __init__(self, **configuration):
            self.configuration = configuration
            self.pending = b""

        def __enter__(self):
            return self

        def __exit__(self, *args):
            if self.pending:
                with self.archive.open("ab") as stream:
                    stream.write(self.pending)
            if options.get("replace-home-on-close"):
                home = Path(self.configuration["dsh_home"])
                saved = home.with_name("original-home")
                home.rename(saved)
                shutil.copytree(saved, home)

        def resume_session(self, session_id):
            self.archive = Path(self.configuration["dsh_home"]) / "sessions/project" / session_id / "session.v4.jsonl"
            self.previous = self.archive.read_bytes()
            with self.archive.open("ab") as stream:
                stream.write(json.dumps({"type": "session/end-seed", "seq": 10}).encode() + b"\n")
            def cwd():
                if options.get("restore-disconnect"):
                    raise OSError("Synthetic restore cwd RPC disconnected")
                return self.configuration["cwd"]
            return SimpleNamespace(get_working_directory=cwd,
                                   run=lambda prompt, **kwargs: self.run(prompt, session_id=session_id, **kwargs))

        def run(self, prompt, *, session_id, on_notification):
            path = Path(self.configuration["patches"][0])
            request = json.loads((path.parent / "request.json").read_bytes())
            calls.append(request)
            if options.get("during_run"):
                options["during_run"](request)
            if options.get("interrupted"):
                raise KeyboardInterrupt
            if options.get("disconnect"):
                raise OSError("Synthetic connection lost after prompt submission")
            self.archive = Path(self.configuration["dsh_home"]) / "sessions/project" / session_id / "session.v4.jsonl"
            self.archive.parent.mkdir(parents=True, exist_ok=True)
            if not self.archive.exists():
                self.archive.write_bytes(json.dumps({"type": "session", "version": 4, "id": session_id,
                    "cwd": self.configuration["cwd"]}).encode() + b"\n")
            patch = json.loads(path.read_bytes())
            transport = patch[-1]["insert"][0]["config"]["args"]
            view = task_mcp.ResourceView.load(Path(transport[3]), transport[4])
            events = [{"scope_sha256": transport[4], "method": "tools/list", "success": True,
                       "tools": task_mcp.TOOLS, "protocol_version": "fixture"}]
            for uri, details in view.document["files"].items():
                events.append({"scope_sha256": transport[4], "method": "tools/call", "success": True,
                    "tool": "read", "read": {"uri": uri, "sha256": details["sha256"], "size": details["size"],
                                                "offset": 0, "bytes": details["size"]}})
            Path(transport[5]).write_text("".join(json.dumps(event) + "\n" for event in events))
            resumed = request["continuation"]["kind"] == "resume"
            message = {"id": "followup-message" if resumed else "source-message", "role": "user",
                       "source": {"kind": "user"}, "content": [{"type": "text", "text": prompt}]}
            base = 20 if resumed else 1
            events = [{"seq": base, "type": "agent/inbox/spliced", "data": {
                "target": "next-turn", "start": 0, "removedCount": 0, "inserted": [message]}},
                {"seq": base + 1, "type": "agent/inbox/spliced", "data": {
                    "target": "next-turn", "start": 0, "removedCount": 1, "inserted": []}},
                {"seq": base + 2, "type": "user/message", "data": message},
                {"seq": base + 3, "type": "turn/end", "data": {"turn": 1, "reason": {"kind": "completed"}}}]
            from dataclasses import make_dataclass

            notification = make_dataclass("Notification", ["method", "payload"])
            on_notification(notification("session.status", {"sessionId": session_id, "status": "idle"}))
            self.pending = b"".join(json.dumps(event, ensure_ascii=False).encode() + b"\n" for event in events)
            return SimpleNamespace(session_id=session_id, finish_reason="completed", events=events,
                final_response=json.dumps({**answer, "artifacts": {"response": "Followup response"}}) if resumed else json.dumps(answer))

    def dispatch(argv, cwd, output, timeout, stdin, env, **kwargs):
        import contextlib
        import io

        output.mkdir()
        stdout = io.StringIO()
        environment = dict(os.environ)
        try:
            monkeypatch.setattr(sys, "argv", argv[2:])
            with contextlib.redirect_stdout(stdout):
                deepseek.main()
            status, code, error = "succeeded", 0, ""
        except (OSError, ValueError) as failure:
            status, code, error = "failed", 1, str(failure)
        finally:
            os.environ.clear()
            os.environ.update(environment)
            (output / "stdout.txt").write_text(stdout.getvalue())
        (output / "stderr.txt").write_text(error)
        return {"status": status, "returncode": code, "output": str(output)}

    monkeypatch.setitem(sys.modules, "deepseek_harness", SimpleNamespace(DeepSeekHarness=Harness))
    monkeypatch.setattr(deepseek, "installed_versions", lambda: {
        name: "0.2.2rc2" for name in ("deepseek-harness-sdk", "deepseek-harness-runtime-bin")})
    monkeypatch.setattr(processes, "run", dispatch)
    return SimpleNamespace(state=state, repo=repo, source=source, followup=followup, calls=calls, options=options, prepare=prepare)


def test_continuation_keeps_original_session_and_results_with_one_durable_intent(continuation, capsys):
    case = continuation
    original = agent_runs.run_input(case.state, "demo", case.source, mode="task-mcp", allow_one_continuation=True)
    assert original["status"] == "succeeded", original
    saved_original = json.dumps(original, sort_keys=True)
    native = original["continuation"]["native"]
    old_page = agent_runs.output(case.state, "demo", original["id"], native_history=True)["native_history"]

    def concurrent(_):
        with pytest.raises(BlockingIOError):
            agent_runs.continue_input(case.state, "demo", original["id"], case.followup, intent_id="followup-one")

    case.options["during_run"] = concurrent
    assert main(["--home", str(case.state.root), "composition", "continue-input", "demo", original["id"],
                 str(case.followup), "--intent", "followup-one"]) == 0
    followup = json.loads(capsys.readouterr().out)
    assert followup["status"] == "succeeded", followup
    assert followup["continuation"]["state"] == "completed" and len(case.calls) == 2
    assert json.loads(Path(original["result"]).read_bytes())["artifacts"]["response"] == "Source response"
    assert json.loads(Path(followup["result"]).read_bytes())["artifacts"]["response"] == "Followup response"
    assert case.calls[1]["cwd"] == case.calls[0]["cwd"] == native["cwd"]
    assert followup["task_mcp"]["scope"]["sha256"] != original["task_mcp"]["scope"]["sha256"]
    assert followup["task_mcp"]["reads"]["attachments"] == original["task_mcp"]["reads"]["attachments"]
    assert agent_runs.continue_input(case.state, "demo", original["id"], case.followup, intent_id="followup-one") == followup
    with pytest.raises(ValueError, match="already claimed"):
        agent_runs.continue_input(case.state, "demo", original["id"], case.followup, intent_id="conflicting-intent")
    with pytest.raises(ValueError, match="already claimed"):
        agent_runs.continue_input(case.state, "demo", original["id"], case.followup, intent_id="followup-one", timeout=30)
    with pytest.raises(ValueError, match="standalone source"):
        agent_runs.continue_input(case.state, "demo", followup["id"], case.followup, intent_id="third")
    assert len(case.calls) == 2
    assert json.dumps(next(run for run in agent_runs.runs(case.state, "demo") if run["id"] == original["id"]), sort_keys=True) == saved_original
    history = agent_runs.output(case.state, "demo", followup["id"], native_history=True)
    assert history["native_history"]["source_run"] == original["id"]
    assert history["native_history"]["content"].startswith(old_page["content"])
    assert history["native_history"]["revision"] != old_page["revision"]


@pytest.mark.parametrize("drift", ["project", "repository", "cwd", "home", "history", "schema", "binding", "material"])
def test_continuation_refuses_changed_authority_or_native_evidence_before_new_input(continuation, drift, tmp_path):
    case = continuation
    original = agent_runs.run_input(case.state, "demo", case.source, mode="task-mcp", allow_one_continuation=True)
    assert original["status"] == "succeeded", original
    protocol = Path(original["continuation"]["native"]["protocol"])
    if drift == "project":
        projects.bind(case.state, "demo", "reviewer", {"tool": "codex"}, 1)
    elif drift in ("repository", "cwd"):
        path = case.repo if drift == "repository" else Path(original["continuation"]["native"]["cwd"])
        path.rename(tmp_path / "old-directory")
        path.mkdir()
    elif drift == "home":
        path = protocol / "native-home"
        original_home = tmp_path / "original-home"
        path.rename(original_home)
        shutil.copytree(original_home, path)
    elif drift == "history":
        archive = next((protocol / "native-home/sessions").glob("*/*/session.v4.jsonl"))
        with archive.open("ab") as stream:
            stream.write(b'{"type":"session/end-seed"}\n')
    elif drift == "schema":
        (protocol / "schema.json").write_text('{"type":"string"}')
    elif drift == "binding":
        request = json.loads((protocol / "request.json").read_bytes())
        request["binding"]["model"] = "other-model"
        (protocol / "request.json").write_text(json.dumps(request))
    else:
        # The prepared input verifier owns all resource digests.
        path = next((case.followup / "assets").rglob("instructions.md"))
        path.write_text("Changed material")
    with pytest.raises(ValueError):
        agent_runs.continue_input(case.state, "demo", original["id"], case.followup, intent_id="followup-one")
    assert len(case.calls) == 1
    assert len(agent_runs.runs(case.state, "demo")) == 1


@pytest.mark.parametrize("failure", ["disconnect", "interrupted", "restore-disconnect", "replace-home-on-close"])
def test_uncertain_or_interrupted_continuation_is_not_resent(continuation, failure):
    case = continuation
    original = agent_runs.run_input(case.state, "demo", case.source, mode="task-mcp", allow_one_continuation=True)
    assert original["status"] == "succeeded", original
    case.options[failure] = True
    followup = agent_runs.continue_input(case.state, "demo", original["id"], case.followup, intent_id="once")
    assert followup["status"] in ("failed", "cancelled") and followup["continuation"]["state"] == "unknown"
    expected_calls = 1 if failure == "restore-disconnect" else 2
    assert len(case.calls) == expected_calls
    if failure != "replace-home-on-close":
        native = followup["continuation"]["native"]
        assert not native["completed"] and native["source_prefix_preserved"]
        assert native["final_bytes"] >= native["restored_bytes"] > native["source_bytes"]
    else:
        assert "observation_error" in followup["continuation"]
    case.options.clear()
    assert agent_runs.continue_input(State(case.state.root), "demo", original["id"], case.followup, intent_id="once") == followup
    assert len(case.calls) == expected_calls


def test_source_requires_explicit_standalone_opt_in_on_a_supported_backend(continuation):
    case = continuation
    for options in ({"supervised": True}, {"result_schema": agents.result_schema(["custom"])}, {"backend": "codex"}):
        with pytest.raises(ValueError):
            agent_runs.run_input(case.state, "demo", case.source, mode="task-mcp", allow_one_continuation=True, **options)
    assert agent_runs.runs(case.state, "demo") == [] and case.calls == []

    original = agent_runs.run_input(case.state, "demo", case.source, mode="task-mcp", allow_one_continuation=True)
    assert original["status"] == "succeeded", original
    with case.state.connect() as db:
        legacy = dict(original)
        del legacy["continuation"]
        db.execute("UPDATE agent_runs SET document=? WHERE id=?", (json.dumps(legacy), original["id"]))
    with pytest.raises(ValueError, match="explicitly enabled"):
        agent_runs.continue_input(case.state, "demo", original["id"], case.followup, intent_id="old-source")
    assert len(case.calls) == 1


def test_preflight_cannot_reset_continuation_wall_budget_or_its_reserved_slot(continuation, monkeypatch):
    import asyncio

    case = continuation
    original = agent_runs.run_input(case.state, "demo", case.source, mode="task-mcp", allow_one_continuation=True)
    assert original["status"] == "succeeded", original

    async def stalled_probe(*args):
        await asyncio.sleep(10)

    monkeypatch.setattr(task_mcp, "probe", stalled_probe)
    followup = agent_runs.continue_input(case.state, "demo", original["id"], case.followup, intent_id="short", timeout=1)
    assert followup["status"] == "failed" and followup["continuation"]["state"] == "reserved"
    assert len(case.calls) == 1
    assert agent_runs.continue_input(case.state, "demo", original["id"], case.followup, intent_id="short", timeout=1) == followup
    assert len(case.calls) == 1
