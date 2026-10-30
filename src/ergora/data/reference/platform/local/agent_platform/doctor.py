from __future__ import annotations

import importlib.metadata
import tomllib
import os
from pathlib import Path
import shutil
import socket

from .core import CONFIG, ROOT, STATE, environment, projects, settings, write
from .sandbox import Sandbox


def report() -> dict:
    env = environment()
    config = settings()
    checks = {}
    for package in ("temporalio", "a2a-sdk", "mlflow", "langgraph", "supervisor"):
        checks[package] = {"status": "ready", "version": importlib.metadata.version(package)}
    for name in ("temporal", "symphony"):
        checks[name] = {"status": "ready" if (ROOT / "bin" / name).is_file() else "missing"}
    for name in ("git", "node", "codex"):
        checks[name] = {"status": "ready" if shutil.which(name) else "missing"}
    model_settings = tomllib.loads((CONFIG / "codex.toml").read_text())
    checks["model-configuration"] = {"status": "ready" if model_settings.get("model") not in
                                    (None, "", "CONFIGURE_MODEL_BEFORE_USE") else "needs-configuration"}
    checks["codex-auth"] = {"status": "ready" if env.get(config["codex_env_key"]) else "needs-configuration",
                            "variable": config["codex_env_key"]}
    checks["reviewer"] = {"status": "ready" if config.get("reviewer") == "codex" else "needs-configuration",
                          "provider": config.get("reviewer"), "session": "independent"}
    sandbox = Sandbox().probe()
    checks["execution-boundary"] = {"status": "ready" if sandbox["available"] else "blocked", **sandbox}
    checks['automatic-executor'] = {'status': 'enabled' if config.get('execution_enabled') is True else 'disabled'}
    rejected = list((STATE / 'rejected-envelopes').glob('*.json'))
    checks['rejected-stage-envelopes'] = {'status': 'requires-reconciliation' if rejected else 'clear', 'count': len(rejected)}
    for name, port in (("temporal-service", 7233), ("temporal-ui", 8233), ("mlflow-service", 5000), ("a2a-service", 8765)):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                checks[name] = {"status": "listening", "port": port}
        except OSError:
            checks[name] = {"status": "stopped", "port": port}
    registered = projects()
    checks['projects'] = {'status': 'configured' if registered else 'needs-configuration', 'count': len(registered)}
    symphony_projects = list((CONFIG / 'projects').glob('*.symphony.json'))
    checks["symphony-project"] = {"status": "configured" if symphony_projects else "needs-real-tracker", "count": len(symphony_projects)}
    result = {"installation": str(ROOT), "config": str(CONFIG), "state": str(STATE), "checks": checks,
              "ready_for_real_tasks": all(checks[k]["status"] == "ready" for k in
                 ('model-configuration', 'git', 'codex', 'codex-auth', 'reviewer', 'execution-boundary')) and bool(registered)
                 and config.get('execution_enabled') is True
                 and all(checks[k]['status'] == 'listening' for k in ('temporal-service', 'a2a-service'))}
    write(STATE / "doctor.json", result, replace=True)
    return result
