from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from .core import Blocked, CONFIG, PYTHON, ROOT, STATE, environment, project, projects, read, require, slug, task_spec, write


def supervisor(*args: str) -> int:
    return subprocess.call([str(ROOT / ".venv/bin/supervisorctl"), "-c", str(CONFIG / "supervisord.ini"), *args], env=environment())


async def task_action(args) -> dict:
    from dev_platform.connection import connect, task_queue
    from dev_platform.runtime import DevelopmentTransport
    from dev_platform.workflow import DevelopmentWorkflow, workflow_id
    from dev_platform.adapter import publish
    spec = task_spec(args.task_id)
    if args.operation == "start":
        from .doctor import report
        doctor = report()
        require(doctor["ready_for_real_tasks"], "Real execution prerequisites are incomplete; run agentflow doctor")
        p = read(STATE / "tasks" / args.task_id / "project.json")
        from .projects import check_task_type
        check_task_type(p['name'], spec['request']['task_type'])
        missing = set(spec["profile"]["required_checks"]) - {"scope", "baseline-regression"} - set(p["checks"])
        require(not missing, "Configure trusted checks first: " + ", ".join(sorted(missing)))
    client = await connect()
    runtime = DevelopmentTransport(client, task_queue())
    if args.operation == "start":
        from .ingress import claim
        claim(spec)
        return {"workflow_id": workflow_id(spec), "run_id": await runtime.start(spec)}
    handle, description = await runtime.lookup(spec)
    if args.operation == "status":
        return await handle.query(DevelopmentWorkflow.status)
    if args.operation == "result":
        outcome = await handle.result(follow_runs=False)
        from .ingress import release
        release(spec, outcome)
        return outcome
    if args.operation == 'export':
        outcome = await handle.result(follow_runs=False)
        require(outcome['status'] == 'REVIEW_READY', 'Export requires completed verification and independent review')
        from .ingress import release
        release(spec, outcome)
        from .core import git
        p = read(STATE / 'tasks' / args.task_id / 'project.json')
        repo = Path(p['repo'])
        branch = args.branch or 'agent/' + args.task_id
        require(git(repo, 'check-ref-format', '--branch', branch, check=False).returncode == 0 and not branch.startswith('-'), 'Invalid target branch')
        candidate = outcome['candidate_sha']
        existing = git(repo, 'show-ref', '--verify', '--hash', 'refs/heads/' + branch, check=False)
        if existing.returncode == 0:
            require(existing.stdout.strip() == candidate, 'Branch already exists at a different commit; choose another name')
        else:
            git(repo, 'fetch', '--no-tags', str(STATE / 'workspaces' / args.task_id / 'repo.git'), candidate + ':refs/heads/' + branch)
        write(STATE / 'tasks' / args.task_id / 'export.json', {'candidate_sha': candidate, 'repo': str(repo), 'branch': branch})
        return {'repo': str(repo), 'branch': branch, 'candidate_sha': candidate, 'checked_out': False, 'merged': False}
    if args.operation == "cancel":
        await runtime.cancel(spec, description.run_id, args.reason)
        return {"cancel_requested": True, "confirmed": False, "instruction": "Query result for the confirmed external-job state"}
    status = await handle.query(DevelopmentWorkflow.status)
    require(status["phase"] == "AWAITING_PLAN_APPROVAL" and status["plan_sha256"] == args.plan_sha256,
            "Approval must name the exact plan currently awaiting a decision")
    receipt_id = "owner-" + uuid.uuid4().hex
    approval = {"schema_version": 1, "kind": "plan-approval", "task_id": args.task_id,
        "request_sha256": spec["request_sha256"], "profile_sha256": spec["profile_sha256"],
        "plan_sha256": args.plan_sha256, "decision": "approve", "principal_type": "human",
        "actor_id": f"unix:{os.getuid()}:{getpass.getuser()}", "role": "owner", "expires_at": int(time.time()) + 86400, "revoked": False}
    publish(STATE / "approvals" / (receipt_id + ".json"), approval)
    await handle.signal(DevelopmentWorkflow.approve_plan,
        {"request_sha256": spec["request_sha256"], "plan_sha256": args.plan_sha256, "receipt_id": receipt_id})
    return {"approval_submitted": receipt_id, "plan_sha256": args.plan_sha256}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agentflow", description="本地多 agent 开发平台：Codex 实现与独立会话审查")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="初始化 home 配置，保留现有设置")
    sub.add_parser("doctor", help="检查组件、凭据状态与执行条件（不显示密钥）")
    verify = sub.add_parser('verify', help='验证本地 Temporal、A2A 与 MLflow')
    verify.add_argument('--restart-temporal', action='store_true')
    templates = sub.add_parser('templates').add_subparsers(dest='operation', required=True)
    templates.add_parser('install')
    copy_template = templates.add_parser('copy')
    copy_template.add_argument('kind', choices=['repository-governance', 'large-change', 'training-optimization'])
    copy_template.add_argument('destination', type=Path)
    service = sub.add_parser("services").add_subparsers(dest="operation", required=True)
    for operation in ("start", "stop", "status", "restart"):
        service.add_parser(operation)
    logs = service.add_parser("logs"); logs.add_argument("name"); logs.add_argument("--stderr", action="store_true")
    sandbox = sub.add_parser("sandbox").add_subparsers(dest="operation", required=True)
    sandbox.add_parser("probe"); sandbox.add_parser("diagnose")
    execution = sub.add_parser('execution').add_subparsers(dest='operation', required=True)
    enable_execution = execution.add_parser('enable')
    enable_execution.add_argument('--trusted-current-container', action='store_true', required=True)
    execution.add_parser('disable')
    projects = sub.add_parser("project").add_subparsers(dest="operation", required=True)
    add = projects.add_parser("add"); add.add_argument("name"); add.add_argument("--repo", type=Path, required=True)
    add.add_argument("--tracker", choices=["local", "github", "gitlab"], required=True); add.add_argument("--project", required=True)
    add.add_argument("--allowed-path", action="append", required=True); add.add_argument("--checks-json", type=Path)
    projects.add_parser("list")
    task = sub.add_parser("task").add_subparsers(dest="operation", required=True)
    create = task.add_parser("create"); create.add_argument("--project", required=True)
    create.add_argument("--type", choices=["repository-governance", "large-change"], required=True)
    create.add_argument("--id", required=True); create.add_argument("--issue", required=True)
    create.add_argument("--input", type=Path, required=True); create.add_argument("--starting-sha")
    for operation in ("start", "status", "result", "approve", "cancel", 'export'):
        item = task.add_parser(operation); item.add_argument("task_id")
        if operation == "approve": item.add_argument("--plan-sha256", required=True)
        if operation == "cancel": item.add_argument("--reason", required=True)
        if operation == 'export': item.add_argument('--branch')
    search = sub.add_parser("search"); search.add_argument("--project", required=True); search.add_argument("--id", required=True)
    search.add_argument("--goal", required=True); search.add_argument("--limit", type=int, default=3); search.add_argument("--resume", action="store_true")
    symphony = sub.add_parser("symphony").add_subparsers(dest="operation", required=True)
    configure = symphony.add_parser("configure"); configure.add_argument("project"); configure.add_argument("--repo-url", required=True)
    enable = symphony.add_parser("enable"); enable.add_argument("project")
    a2a = sub.add_parser("a2a", help="原生 A2A 准入、客户端与恢复命令")
    a2a.add_argument("arguments", nargs=argparse.REMAINDER)
    demo = sub.add_parser("demo"); demo.add_argument("operation", choices=["prepare"])
    training = sub.add_parser("training", help="训练优化契约与本地 runner")
    training.add_argument("arguments", nargs=argparse.REMAINDER)
    return p


def main() -> None:
    args = parser().parse_args()
    try:
        result = None
        if args.command == "init":
            from .setup import initialize
            initialize(); result = {"initialized": str(ROOT)}
        elif args.command == "doctor":
            from .doctor import report
            result = report()
        elif args.command == 'verify':
            from .acceptance import services
            result = asyncio.run(services(restart_temporal=args.restart_temporal))
        elif args.command == 'templates':
            from .templates import install, copy
            result = install() if args.operation == 'install' else copy(args.kind, args.destination)
        elif args.command == "services":
            if args.operation == "start":
                status = subprocess.run([str(ROOT / ".venv/bin/supervisorctl"), "-c", str(CONFIG / "supervisord.ini"), "pid"],
                    capture_output=True, text=True, env=environment())
                if status.returncode:
                    subprocess.run([str(ROOT / ".venv/bin/supervisord"), "-c", str(CONFIG / "supervisord.ini")], check=True, env=environment())
                else:
                    from .core import settings
                    names = ['temporal', 'mlflow', 'worker', 'a2a']
                    if settings().get('execution_enabled') is True: names.append('executor')
                    for name in names:
                        supervisor("start", name)
                result = {"started": True, "logs": str(STATE / "logs")}
            elif args.operation == "stop":
                sys.exit(supervisor("shutdown"))
            elif args.operation == "status":
                sys.exit(supervisor("status"))
            elif args.operation == "restart":
                from .core import settings
                names = ['temporal', 'mlflow', 'worker', 'a2a']
                if settings().get('execution_enabled') is True: names.append('executor')
                sys.exit(supervisor('restart', *names))
            else:
                slug(args.name)
                path = STATE / "logs" / (args.name + (".err.log" if args.stderr else ".log"))
                print(path.read_text()[-30000:])
        elif args.command == "sandbox":
            from .sandbox import Sandbox
            result = Sandbox().probe()
            if args.operation == 'diagnose':
                from .diagnostics import isolation_report
                result['inner_sandbox_tests'] = isolation_report()
        elif args.command == 'execution':
            from .core import settings
            from .setup import supervisor_config
            config = settings()
            config.update(execution_enabled=args.operation == 'enable')
            if args.operation == 'enable':
                from .sandbox import container_identity
                boundary = container_identity()
                require(boundary is not None, 'No supported container marker detected; native execution stays disabled')
                config.update(execution_backend='current-container', current_container_trust_acknowledged=True,
                              container_boundary=boundary)
            write(CONFIG / 'platform.json', config, replace=True)
            supervisor_config()
            status = subprocess.run([str(ROOT / '.venv/bin/supervisorctl'), '-c', str(CONFIG / 'supervisord.ini'), 'pid'],
                                    capture_output=True, env=environment())
            if status.returncode == 0:
                supervisor('reread'); supervisor('update')
                if args.operation == 'disable': supervisor('stop', 'executor')
            result = {'execution_enabled': config['execution_enabled'], 'backend': config['execution_backend']}
        elif args.command == "project":
            from .projects import register
            if args.operation == "list": result = projects()
            else: result = register(args.name, args.repo, args.tracker, args.project, args.allowed_path, args.checks_json)
        elif args.command == "task":
            if args.operation == "create":
                from .projects import create_task
                result = create_task(args.project, args.type, args.id, args.issue, args.input, args.starting_sha)
            else: result = asyncio.run(task_action(args))
        elif args.command == "search":
            from .search import run
            result = run(args.project, args.id, args.goal, args.limit, args.resume)
        elif args.command == "symphony":
            from .symphony import configure, enable
            result = configure(args.project, args.repo_url) if args.operation == "configure" else enable(args.project)
        elif args.command == "a2a":
            sys.exit(subprocess.call([str(PYTHON), "-m", "dev_platform.a2a_gateway", *args.arguments], env=environment()))
        elif args.command == "demo":
            from .demo import prepare
            result = prepare()
        else:
            from .training import cli
            result = cli(args.arguments)
        if result is not None:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (Blocked, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
