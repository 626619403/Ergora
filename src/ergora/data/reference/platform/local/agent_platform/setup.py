from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import shlex
import shutil
import tomllib

from .core import CONFIG, PYTHON, ROOT, RUNTIME, STATE, UPSTREAM, require, write


def initialize() -> None:
    for path in [CONFIG, STATE, RUNTIME, CONFIG / "projects", CONFIG / "policies", CONFIG / "supervisor.d",
                 STATE / "logs", STATE / "tasks", STATE / "workspaces", STATE / "tracking", STATE / "search",
                 *[STATE / name for name in ("requests", "receipts", "artifacts", "approvals", "fences", "ingress", "a2a")]]:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
    provider_id = "api"
    provider = {"name": "Responses API", "base_url": "https://api.openai.com/v1",
                "env_key": "OPENAI_API_KEY", "wire_api": "responses"}
    source = {"model": "CONFIGURE_MODEL_BEFORE_USE", "model_provider": provider_id,
              "model_providers": {provider_id: provider}, "model_reasoning_effort": "high"}
    node = shutil.which("node")
    require(node is not None, "Node is required")
    config = {
        "schema_version": 1, "codex_bin": shutil.which("codex"),
        "node_root": str(Path(node).parent.parent), "codex_env_key": provider["env_key"],
        "sandbox_image": "localhost/agentflow:0.1.0", "max_parallel_jobs": 4, "stage_walltime_seconds": 1800,
        "execution_enabled": False, "execution_backend": "current-container",
        "current_container_trust_acknowledged": False,
        "entry": "symphony", "reviewer": "codex", "tracking": "mlflow", "candidate_search": "langgraph",
    }
    if not (CONFIG / "platform.json").exists():
        write(CONFIG / "platform.json", config)
    codex_file = CONFIG / "codex.toml"
    if not codex_file.exists():
        fields = {"model": source["model"], "model_provider": provider_id,
                  "model_reasoning_effort": source.get("model_reasoning_effort", "high")}
        text = "\n".join(f"{key} = {json.dumps(value)}" for key, value in fields.items())
        text += "\napproval_policy = \"never\"\n[sandbox_workspace_write]\nnetwork_access = true\n"
        text += f"\n[model_providers.{provider_id}]\n"
        for key in ("name", "base_url", "env_key", "wire_api", "requires_openai_auth", "supports_websockets"):
            if key in provider:
                text += f"{key} = {json.dumps(provider[key])}\n"
        codex_file.write_text(text)
        codex_file.chmod(0o600)
    if not (CONFIG / "credentials.json").exists():
        write(CONFIG / "credentials.json", {"A2A_LOCAL_TOKEN": secrets.token_urlsafe(40)})
    if not (CONFIG / "adapter.json").exists():
        write(CONFIG / "adapter.json", {**{name: str(STATE / name) for name in
              ("requests", "receipts", "artifacts", "approvals", "fences")}, "trusted_receipts": True})
    if not (CONFIG / "a2a.json").exists():
        write(CONFIG / "a2a.json", {"schema_version": 1, "ledger": str(STATE / "a2a/ledger.sqlite3"),
              "shared_ingress_db": str(STATE / "ingress/leases.sqlite3"), "public_url": "http://127.0.0.1:8765",
              "host": "127.0.0.1", "port": 8765, "principals": {"local-operator": "A2A_LOCAL_TOKEN"}})
    supervisor_config()
    install_commands()


def install_commands() -> None:
    from .core import settings
    config = settings()
    local_bin = ROOT / 'bin'
    local_bin.mkdir(parents=True, exist_ok=True)
    wrapper = local_bin / 'agentflow'
    text = f'''#!/usr/bin/env bash
# Managed by multi-agent-platform
set -euo pipefail
platform_root={shlex.quote(str(ROOT))}
export PATH={shlex.quote(config['node_root'] + '/bin')}:{shlex.quote(str(ROOT / 'bin'))}:"$PATH"
export PYTHONPATH="$platform_root/local:$platform_root/upstream/platform:$platform_root/upstream/temporal:$platform_root/upstream"
exec "$platform_root/.venv/bin/python" -m agent_platform.cli "$@"
'''
    if wrapper.exists():
        require('agent_platform.cli' in wrapper.read_text(), 'Existing agentflow command is not owned by this installation')
    wrapper.write_text(text); wrapper.chmod(0o755)
    user_entry = Path.home() / '.local/bin/agentflow'
    user_entry.parent.mkdir(parents=True, exist_ok=True)
    if not user_entry.exists() and not user_entry.is_symlink(): user_entry.symlink_to(wrapper)
    path = ':'.join([str(local_bin), str(Path.home() / '.local/bin'), config['node_root'] + '/bin'])
    (ROOT / 'env.sh').write_text('export PATH=' + shlex.quote(path) + ':"$PATH"\nexport MLFLOW_TRACKING_URI="http://127.0.0.1:5000"\n')


def supervisor_config() -> None:
    text = f"""[unix_http_server]
file={STATE}/supervisor.sock
chmod=0700
[supervisord]
logfile={STATE}/logs/supervisord.log
pidfile={STATE}/supervisord.pid
childlogdir={STATE}/logs
logfile_maxbytes=10MB
[rpcinterface:supervisor]
supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface
[supervisorctl]
serverurl=unix://{STATE}/supervisor.sock
[include]
files={CONFIG}/supervisor.d/*.ini
"""
    (CONFIG / "supervisord.ini").write_text(text)
    from .core import settings
    enabled = settings().get('execution_enabled') is True
    for name, priority in [("temporal", 10), ("mlflow", 20), ("worker", 20), ("executor", 30), ("a2a", 30)]:
        service_config(name, priority=priority, autostart=name != "executor" or enabled)
    service_config('training-worker', priority=20, autostart=False)


def service_config(name: str, *, priority: int = 30, extra: str = "", autostart: bool = True) -> None:
    text = f"""[program:{name}]
command={PYTHON} -m agent_platform.service {name} {extra}
directory={ROOT}
environment=PYTHONPATH="{ROOT}/local:{UPSTREAM}/platform:{UPSTREAM}/temporal:{UPSTREAM}"
autostart={'true' if autostart else 'false'}
autorestart=unexpected
startsecs=3
startretries=3
priority={priority}
stopasgroup=true
killasgroup=true
stopwaitsecs=15
stdout_logfile={STATE}/logs/{name}.log
stderr_logfile={STATE}/logs/{name}.err.log
stdout_logfile_maxbytes=10MB
stderr_logfile_maxbytes=10MB
stdout_logfile_backups=3
stderr_logfile_backups=3
"""
    (CONFIG / "supervisor.d" / f"{name}.ini").write_text(text)
