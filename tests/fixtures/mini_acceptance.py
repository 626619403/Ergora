"""Real SDK/model factory and tool-call parser with a local completion response."""

from contextlib import redirect_stdout
import json
from pathlib import Path
import re
import runpy
import shlex
import sys

with redirect_stdout(sys.stderr):
    import litellm


driver, request_path, action = sys.argv[1:]
request = json.loads(Path(request_path).read_text())
result = {"summary": "native SDK fixture", "artifacts": {"change-summary": "fixture artifact"}}
calls = 0


def completion(**kwargs):
    global calls
    calls += 1
    assert kwargs["tools"][0]["function"]["name"] == "bash"
    rendered = kwargs["messages"][1]["content"]
    assert "mswea_bash_command" not in rendered
    submission = re.search(r"<submission-path>(.*?)</submission-path>", rendered, re.S).group(1)
    finish = re.search(r"<submission-command>(.*?)</submission-command>", rendered, re.S).group(1)
    if action == "complete":
        code = "from pathlib import Path;Path('candidate.txt').write_text('fixture candidate');Path(" + repr(submission) + ").write_text(" + repr(json.dumps(result)) + ")"
        command = shlex.join([sys.executable, "-c", code]) if calls == 1 else finish
    elif action == "empty":
        command = "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"
    else:
        code = "import os,time;from pathlib import Path;Path('action-ready').write_text(str(os.getpid()));time.sleep(30);Path('late.txt').touch()"
        command = shlex.join([sys.executable, "-c", code])
    return litellm.ModelResponse(model="gpt-4o-mini", usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        choices=[{"index": 0, "finish_reason": "tool_calls", "message": {"role": "assistant", "content": "fixture action",
            "tool_calls": [{"id": str(calls), "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": command})}}]}}])


litellm.completion = completion
sys.argv = [driver, request_path]
runpy.run_path(driver, run_name="__main__")
