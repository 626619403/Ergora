"""Structured native agent runner inside the reference's existing process monitor."""

import json
import os
from pathlib import Path
import sys
import signal
import tomllib

from . import agents, processes


def _cancel(_signal, _frame):
    # Leave cleanup uninterrupted, even when the first TERM arrives inside it.
    processes.cancel_supervised()


def main() -> int:
    signal.signal(signal.SIGTERM, _cancel)
    request = json.loads(Path(sys.argv[1]).read_text())
    env = dict(os.environ)
    credentials = Path(request["credentials"])
    if credentials.exists():
        if credentials.stat().st_mode & 0o077:
            raise ValueError("Reference credentials must have mode 0600")
        for key, value in json.loads(credentials.read_text()).items():
            env.setdefault(key, value)
    options = []
    if request["binding"]["tool"] == "codex":
        options += ["--ignore-user-config", "--ignore-rules", "--disable", "plugins", "--disable", "apps"]
        config = tomllib.loads(Path(request["codex_config"]).read_text())
        def add(table, prefix=""):
            for key, value in table.items():
                name = prefix + key
                if isinstance(value, dict):
                    add(value, name + ".")
                elif name != "approval_policy" and not name.startswith("sandbox_"):
                    options.extend(["-c", name + "=" + json.dumps(value)])
        add(config)
    document = agents.invoke(request["binding"], request["role"], request["prompt"], Path(request["cwd"]),
                             Path(request["output"]), request["timeout"], request["schema"],
                             env=env, codex_options=options, codex_bin=request.get("codex_bin") or "codex", supervised=True)
    print(json.dumps(document))
    return 0 if document["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
