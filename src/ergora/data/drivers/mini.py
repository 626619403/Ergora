"""Runs in the optional mini-swe-agent environment; no Ergora imports required."""

from contextlib import redirect_stdout
import json
from pathlib import Path
import sys
import os
import shlex
import subprocess

with redirect_stdout(sys.stderr):
    from minisweagent.agents.default import DefaultAgent
    from minisweagent.environments.local import LocalEnvironment
    from minisweagent.models import get_model


class ManagedLocalEnvironment(LocalEnvironment):
    """Keep actions in the outer supervisor's process group for whole-run cancellation."""

    def execute(self, action: dict, cwd: str = "", *, timeout=None):
        completed = subprocess.run(action.get("command", ""), shell=True, cwd=cwd or self.config.cwd or os.getcwd(),
                                   env=os.environ | self.config.env, text=True, encoding="utf-8", errors="replace",
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = {"output": completed.stdout, "returncode": completed.returncode, "exception_info": ""}
        self._check_finished(output)
        return output


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    binding = request["binding"]
    submission = Path(request["trajectory"]).with_name("submission.txt")
    command = shlex.join([sys.executable, "-c",
        "from pathlib import Path;import sys;print('COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT');print(Path(sys.argv[1]).read_text())",
        str(submission)])
    config = {
        "system_template": "You implement the assigned repository task. Use the bash tool with a command argument for actions. "
                           "Respect the approved paths and task constraints. The final submission must contain the requested result.",
        "instance_template": """{{task}}

Use bash tool calls to inspect, edit, and verify. Each command runs in a new subshell.
When done, write the complete final response to this output file outside the repository:
<submission-path>{{submission_path}}</submission-path>
For a structured result contract, this file must contain exactly the required JSON object.
Then execute this exact command using the bash tool; its stdout submits your response:
<submission-command>{{submission_command}}</submission-command>
Do not submit an empty response or a marker-only command. The submission ends the task.
""",
        "step_limit": binding.get("step_limit", 30), "cost_limit": binding.get("cost_limit", 3.0),
        "wall_time_limit_seconds": request["timeout"], "output_path": Path(request["trajectory"]),
    }
    with redirect_stdout(sys.stderr):
        model = get_model(config={"model_name": binding["model"], "model_class": "litellm",
                                  "model_kwargs": {"drop_params": True},
                                  "format_error_template": "{{error}} Use the bash tool with a command argument. "
                                                           "For final submission, follow the output-file command in the task."})
        agent = DefaultAgent(model, ManagedLocalEnvironment(cwd=request["cwd"]), **config)
        result = agent.run(request["prompt"], submission_path=str(submission), submission_command=command)
    if result.get("exit_status") != "Submitted" or not result.get("submission", "").strip():
        print(json.dumps(result), file=sys.stderr)
        return 1
    print(result["submission"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
