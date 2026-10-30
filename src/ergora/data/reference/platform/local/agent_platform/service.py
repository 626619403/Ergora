from __future__ import annotations

import os
import socket
import sys
import time

from .core import CONFIG, PYTHON, ROOT, STATE, environment


def main() -> None:
    name = sys.argv[1]
    commands = {
        "temporal": [str(ROOT / "bin/temporal"), "server", "start-dev", "--ip", "127.0.0.1", "--port", "7233",
                     "--ui-ip", "127.0.0.1", "--ui-port", "8233", "--db-filename", str(STATE / "temporal.sqlite3")],
        "mlflow": [str(ROOT / ".venv/bin/mlflow"), "server", "--host", "127.0.0.1", "--port", "5000",
                   "--backend-store-uri", "sqlite:///" + str(STATE / "tracking/mlflow.sqlite3"),
                   "--artifacts-destination", str(STATE / "tracking/artifacts"), "--serve-artifacts"],
        "worker": [str(PYTHON), "-m", "dev_platform.worker"],
        "executor": [str(PYTHON), "-m", "agent_platform.executor"],
        "a2a": [str(PYTHON), "-m", "dev_platform.a2a_gateway", "serve", "--config", str(CONFIG / "a2a.json")],
        "training-worker": [str(PYTHON), "-m", "perf_temporal.worker"],
    }
    if name in {"worker", "a2a", "training-worker"}:
        for attempt in range(60):
            try:
                with socket.create_connection(("127.0.0.1", 7233), timeout=1):
                    break
            except OSError:
                if attempt == 59:
                    raise RuntimeError("Temporal is unavailable after 60 seconds")
                time.sleep(1)
    if name.startswith("symphony-") or name.startswith("bridge-"):
        from .symphony import service_command
        command = service_command(name)
    else:
        command = commands[name]
    env = environment()
    if name.startswith("symphony-"):
        env = {key: value for key, value in env.items() if not key.startswith("TEMPORAL_")}
    os.execve(command[0], command, env)


if __name__ == "__main__":
    main()
