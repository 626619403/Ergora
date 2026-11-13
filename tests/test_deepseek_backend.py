"""A completed SDK turn must not silently bypass restricted call acceptance."""

import json
from pathlib import Path
import sys

import pytest

from ergora import agent_backends, agents, processes


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
    original_decoder = agent_backends.codecs.getincrementaldecoder

    def mutate_after_listing(encoding):
        if addition == "generation":
            archive.with_name("session.v4.1.jsonl").write_bytes(b"future generation\n")
        else:
            (archive.parent.parent / "another-session").mkdir()
        return original_decoder(encoding)

    monkeypatch.setattr(agent_backends.codecs, "getincrementaldecoder", mutate_after_listing)
    with pytest.raises(ValueError, match="directory changed"):
        adapter.archived_history(protocol, cwd=cwd, offset=0, limit=4093, revision=None)
