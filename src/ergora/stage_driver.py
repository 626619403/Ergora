"""Structured native agent runner inside the reference's existing process monitor."""

import json
import os
from pathlib import Path
import sys
import signal

from . import agents, processes


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
    document = agents.invoke(request["binding"], request["role"], request["prompt"], Path(request["cwd"]),
                             Path(request["output"]), request["timeout"], request["schema"],
                             env=env, codex_config=request["codex_config"],
                             codex_bin=request.get("codex_bin") or "codex", supervised=True)
    print(json.dumps(document))
    return 0 if document["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
