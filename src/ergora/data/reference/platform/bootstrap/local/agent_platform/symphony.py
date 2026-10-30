from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from .core import CONFIG, PYTHON, ROOT, STATE, UPSTREAM, environment, git, project, read, require, settings, slug, write
from .sandbox import Sandbox
from .process_job import child_environment
from .setup import service_config


def configure(name: str, repo_url: str) -> dict:
    p = project(name)
    require(p['tracker']['kind'] in {'github', 'gitlab'}, 'Symphony requires a real GitHub/GitLab issue tracker; use local CLI/A2A for local Git tasks')
    require(repo_url and not any(c.isspace() for c in repo_url), "Use one repository URL")
    if repo_url.startswith("https://"):
        from urllib.parse import urlsplit
        u = urlsplit(repo_url)
        require(not u.username and not u.password and not u.query, "Keep repository credentials out of URLs")
    else:
        require(repo_url.startswith("git@"), "Use an HTTPS or git@ SSH repository URL")
    base = STATE / "symphony" / name
    for child in ("workspaces", "outbox", "receipts", "admissions", "bridge", "logs"):
        (base / child).mkdir(parents=True, exist_ok=True, mode=0o700)
    config = {"schema_version": 1, "provider": p["tracker"]["kind"], "project": p["tracker"]["project"],
        "api_url": "https://api.github.com" if p["tracker"]["kind"] == "github" else "https://gitlab.com/api/v4",
        "token_env": "GITHUB_TOKEN" if p["tracker"]["kind"] == "github" else "GITLAB_PAT", "repo_url": repo_url,
        "workspace_root": str(base / "workspaces"), "outbox": str(base / "outbox"), "receipts": str(base / "receipts"),
        "approvals": str(base / "admissions"), "state_dir": str(base / "bridge"),
        "shared_ingress_db": str(STATE / "ingress/leases.sqlite3"), "ready_label": "agent-ready", "max_concurrent_agents": 2,
        "codex_bin": settings()["codex_bin"], "symphony_bin": str(ROOT / "bin/symphony"),
        "dashboard_port": 4000 + len(list((CONFIG / "projects").glob("*.symphony.json"))),
        "enabled_task_types": ["repository-governance", "large-change"],
        "repository_state_file": str(CONFIG / "policies" / name / "repository-state.json")}
    path = CONFIG / "projects" / (name + ".symphony.json")
    write(path, config)
    write(config["repository_state_file"], {"project": config["project"], "base_sha": p["base_sha"], "policy_revision": "local-r1"})
    rendered = subprocess.run([str(PYTHON), str(UPSTREAM / "symphony/configure.py"), "--config", str(path),
        "--output", str(base / "WORKFLOW.generated.md")], capture_output=True, text=True, env=environment())
    require(rendered.returncode == 0, "Symphony configuration rejected: " + rendered.stderr[-2000:])
    text = (base / "WORKFLOW.generated.md").read_text()
    _, frontmatter, prompt = text.split("---", 2)
    native = json.loads(frontmatter)
    native["codex"]["command"] = shlex.join([str(PYTHON), "-m", "agent_platform.symphony", "app-server"])
    native['codex']['thread_sandbox'] = 'danger-full-access'
    native['codex']['turn_sandbox_policy'] = {'type': 'dangerFullAccess'}
    (base / "WORKFLOW.md").write_text("---\n" + json.dumps(native, ensure_ascii=False, indent=2) + "\n---" + prompt)
    for kind in ("symphony", "bridge"):
        service_config(kind + "-" + name, autostart=False)
    return {"configured": name, "workflow": str(base / "WORKFLOW.md"), "token_variable": config["token_env"],
            "started": False, "instruction": "Edit api_url for a private GitLab instance; then run agentflow symphony enable NAME"}


def enable(name: str) -> dict:
    slug(name)
    config = read(CONFIG / "projects" / (name + ".symphony.json"))
    require(bool(environment().get(config["token_env"])), "Tracker credential missing: " + config["token_env"])
    require(Sandbox().probe()["available"], "Configure the execution boundary before enabling automatic issue processing")
    from .cli import supervisor
    supervisor("reread"); supervisor("update")
    require(supervisor("start", "bridge-" + name, "symphony-" + name) == 0, "Symphony service did not start")
    return {"enabled": name, "dashboard": "http://127.0.0.1:" + str(config["dashboard_port"])}


def service_command(service: str) -> list[str]:
    kind, name = service.split("-", 1)
    slug(name)
    config = CONFIG / "projects" / (name + ".symphony.json")
    if kind == "bridge":
        return [str(PYTHON), str(UPSTREAM / "symphony/bridge.py"), "--config", str(config), "run"]
    return [str(PYTHON), str(UPSTREAM / "symphony/launch.py"), "--config", str(config), "--workflow",
            str(STATE / "symphony" / name / "WORKFLOW.md"), "--logs-root", str(STATE / "symphony" / name / "logs")]


def app_server() -> None:
    config = settings()
    runner = Sandbox()
    cwd = Path.cwd().resolve()
    allowed = (STATE / "symphony").resolve()
    require(cwd.is_relative_to(allowed) and "/workspaces/" in str(cwd), "Symphony app-server must run in its managed workspace")
    require(runner.probe()['available'], 'Current-container boundary is not acknowledged')
    import tomllib
    args = ['/usr/bin/timeout', '--kill-after=5', str(config['stage_walltime_seconds']),
            config['codex_bin'], '-c', 'sandbox_mode="danger-full-access"', '-c', 'approval_policy="never"',
            '--disable', 'plugins', '--disable', 'apps']
    def add(table, prefix=''):
        for key, value in table.items():
            name = prefix + key
            if isinstance(value, dict): add(value, name + '.')
            elif name != 'approval_policy' and not name.startswith('sandbox_'):
                args.extend(['-c', name + '=' + json.dumps(value)])
    add(tomllib.loads((CONFIG / 'codex.toml').read_text()))
    args += ['app-server', '--stdio']
    os.execve(args[0], args, child_environment('codex'))


if __name__ == "__main__":
    require(sys.argv[1:] == ["app-server"], "Only the managed app-server entry is supported")
    app_server()
