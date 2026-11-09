"""Structured native agent runner inside the reference's existing process monitor."""

import json
import os
from pathlib import Path
import shutil
import sys
import signal

from . import agent_runs, agents, processes
from .state import State


def _cancel(_signal, _frame):
    # Leave cleanup uninterrupted, even when the first TERM arrives inside it.
    processes.cancel_supervised()


def main() -> int:
    signal.signal(signal.SIGTERM, _cancel)
    request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    env = dict(os.environ)
    credentials = Path(request["credentials"])
    if credentials.exists():
        if credentials.stat().st_mode & 0o077:
            raise ValueError("Reference credentials must have mode 0600")
        for key, value in json.loads(credentials.read_text(encoding="utf-8")).items():
            env.setdefault(key, value)
    if 'composition' in request:
        call = request['composition']
        options = dict(codex_config=Path(request['codex_config']), result_schema=request['schema'], env=env,
                       codex_bin=request.get('codex_bin') or 'codex', supervised=True)
        if 'workspace_call' in call:
            document = agent_runs.run_workspace(State(Path(call['home'])), call['project'], Path(call['input']),
                Path(request['cwd']), json.loads(Path(call['workspace_call']).read_bytes()), request['timeout'],
                binding=request['binding'], **options)
        else:
            document = agent_runs.run_input(State(Path(call['home'])), call['project'], Path(call['input']), request['timeout'],
                binding_override=request['binding'], reason=call['backend_reason'], mode=call['mode'], **options)
        output = Path(request['output'])
        output.mkdir(mode=0o700)
        (output / 'invocation.json').write_text(json.dumps(document), encoding='utf-8')
        for stream in ('stdout.txt', 'stderr.txt', 'result.json'):
            source = Path(document.get('output', '')) / stream
            if 'output' in document and source.is_file():
                shutil.copyfile(source, output / stream)
    else:
        document = agents.invoke(request["binding"], request["role"], request["prompt"], Path(request["cwd"]),
                                 Path(request["output"]), request["timeout"], request["schema"],
                                 env=env, codex_config=request["codex_config"],
                                 codex_bin=request.get("codex_bin") or "codex", supervised=True)
    print(json.dumps(document))
    return 0 if document["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
