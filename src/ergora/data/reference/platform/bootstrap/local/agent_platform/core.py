from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "upstream"
CONFIG = Path(os.environ.get("AGENTFLOW_CONFIG_DIR", Path.home() / ".config/multi-agent-platform"))
STATE = Path(os.environ.get("AGENTFLOW_STATE_DIR", Path.home() / ".local/state/multi-agent-platform"))
RUNTIME = STATE / 'runtime'
PYTHON = ROOT / ".venv/bin/python"


class Blocked(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Blocked(message)


def read(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def write(path: str | Path, value: Any, *, replace: bool = False) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".pending-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            try:
                os.link(temporary, path)
            except FileExistsError:
                def canonical(item):
                    return json.dumps(item, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
                require(canonical(read(path)) == canonical(value), f"Immutable file already exists with different content: {path}")
    finally:
        Path(temporary).unlink(missing_ok=True)


def slug(value: str) -> str:
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value) is not None, "Invalid identifier")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def settings() -> dict:
    return read(CONFIG / "platform.json")


def environment() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(map(str, [ROOT / "local", UPSTREAM / "platform", UPSTREAM / "temporal", UPSTREAM]))
    env.update(TEMPORAL_ADDRESS="127.0.0.1:7233", TEMPORAL_NAMESPACE="default", TEMPORAL_LOCAL_DEV="1",
               DEV_TASK_QUEUE="development-tasks", PERF_TASK_QUEUE="perf-experiments-v1",
               DEV_ADAPTER_CONFIG=str(CONFIG / "adapter.json"),
               PERF_CLUSTER_ADAPTER="agent_platform.training:create_adapter", XDG_RUNTIME_DIR=str(RUNTIME),
               MLFLOW_TRACKING_URI="http://127.0.0.1:5000", DO_NOT_TRACK="1", LANGCHAIN_TRACING_V2="false")
    secrets_file = CONFIG / "credentials.json"
    if secrets_file.exists():
        require(secrets_file.stat().st_mode & 0o077 == 0, "credentials.json must have mode 0600")
        for key, value in read(secrets_file).items():
            require(re.fullmatch(r"[A-Z][A-Z0-9_]*", key) is not None and isinstance(value, str), "Invalid credential mapping")
            env.setdefault(key, value)
    return env


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_TERMINAL_PROMPT="0",
               GIT_AUTHOR_NAME="Agent Platform", GIT_AUTHOR_EMAIL="agent-platform@localhost",
               GIT_COMMITTER_NAME="Agent Platform", GIT_COMMITTER_EMAIL="agent-platform@localhost")
    result = subprocess.run(["/usr/bin/git", "-c", "core.hooksPath=/dev/null", "-c", "protocol.file.allow=always",
                             "-C", str(repo), *args], env=env, capture_output=True, text=True, timeout=120)
    if check:
        require(result.returncode == 0, f"git {args[0]} failed: {result.stderr[:1500]}")
    return result


def project(name: str) -> dict:
    return read(CONFIG / "projects" / f"{slug(name)}.json")


def projects() -> list[dict]:
    return [read(path) for path in sorted((CONFIG / "projects").glob("*.json"))
            if not path.name.endswith(".symphony.json")]


def project_for(request: dict) -> dict:
    matches = projects()
    matches = [p for p in matches if p["tracker"] == {k: request["tracker"][k] for k in ("kind", "project")}]
    require(len(matches) == 1, "Register exactly one trusted project matching the task tracker")
    return matches[0]


def task_spec(task_id: str) -> dict:
    return read(STATE / "tasks" / slug(task_id) / "task.spec.json")
