"""A completed SDK turn must not silently bypass restricted call acceptance."""

import json
from pathlib import Path
import sys

import pytest

from ergora import agents, processes


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
