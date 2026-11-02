from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

from . import __version__
from . import reference
from . import agent_runs, agents, evaluation, kernel, memory, optimization, projects, research, skill_assets, skills, tools
from .state import State, resolve_home


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="ergora", description="Project collaboration and continuous improvement")
    result.add_argument("--version", action="version", version=__version__)
    result.add_argument("--home", type=Path, help="Persistent state directory (default: ERGORA_HOME, LocalAppData on Windows, or XDG data)")
    commands = result.add_subparsers(dest="command", required=True)
    maintenance = commands.add_parser("state", help="Inspect, back up, verify or restore offline local state")
    operations = maintenance.add_subparsers(dest="operation", required=True)
    operations.add_parser("info")
    for name in ("backup", "verify-backup", "restore"):
        operation = operations.add_parser(name)
        operation.add_argument("directory", type=Path)
        if name != "verify-backup":
            operation.add_argument("--offline", action="store_true", required=True,
                                   help="Confirm state writers and external work have stopped")
    web = commands.add_parser("serve", help="Start the local graphical console (requires ergora[web])")
    web.add_argument("--port", type=int, default=8977)
    legacy = commands.add_parser("reference", help="Inspect the bundled v2.2 reference implementation")
    legacy.add_argument("operation", choices=["info", "verify", "executor"])
    legacy.add_argument("--installation", type=Path, help="Existing v2.2 reference installation (executor only)")
    legacy.add_argument("--request", type=Path, help="Execute one envelope instead of watching the reference queue")
    templates = commands.add_parser("templates", help="List or copy a reference workflow template")
    operations = templates.add_subparsers(dest="operation", required=True)
    operations.add_parser("list")
    copy = operations.add_parser("copy")
    copy.add_argument("kind", choices=reference.TEMPLATES)
    copy.add_argument("destination", type=Path)
    contract = operations.add_parser("agents")
    contract.add_argument("kind", choices=reference.TEMPLATES)
    workflow = commands.add_parser("workflow", add_help=False, help="Run the existing portable-contract compiler")
    workflow.add_argument("arguments", nargs=argparse.REMAINDER)
    project = commands.add_parser("project", help="Register a project and choose layer tools")
    operations = project.add_subparsers(dest="operation", required=True)
    create = operations.add_parser("add")
    create.add_argument("id")
    create.add_argument("--repo", type=Path, required=True)
    operations.add_parser("list")
    show = operations.add_parser("show")
    show.add_argument("id")
    bind = operations.add_parser("bind")
    bind.add_argument("id")
    bind.add_argument("layer")
    bind.add_argument("--binding", type=Path, required=True, help="JSON tool binding")
    bind.add_argument("--revision", type=int, required=True)
    tool = commands.add_parser("tools", help="List supported tools or check project availability")
    operations = tool.add_subparsers(dest="operation", required=True)
    operations.add_parser("list")
    doctor = operations.add_parser("doctor")
    doctor.add_argument("project")
    agent = commands.add_parser("agent", help="Invoke a configured tool, independently of formal workflow acceptance")
    operations = agent.add_subparsers(dest="operation", required=True)
    run = operations.add_parser("run")
    run.add_argument("project")
    run.add_argument("role", choices=list(agents.ROLE_CAPABILITIES))
    run.add_argument("--prompt", type=Path, required=True)
    run.add_argument("--timeout", type=int, default=300)
    run.add_argument("--skill", action="append", help="Include the current adopted version of this skill")
    run.add_argument("--recall", help="Recall project memories with this query before invoking the tool")
    run.add_argument("--template", choices=reference.TEMPLATES, help="Require the selected template role's structured artifacts (not formal acceptance)")
    listing = operations.add_parser("runs")
    listing.add_argument("project")
    preview = operations.add_parser("output")
    preview.add_argument("project")
    preview.add_argument("id")
    kernels = commands.add_parser("kernel", help="Native ForgeKernel campaigns; independent project validation still required")
    operations = kernels.add_subparsers(dest="operation", required=True)
    for name in ("plan", "prepare", "list", "run", "status"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        if name in ("run", "status"):
            operation.add_argument("id")
        if name == "run":
            operation.add_argument("--reconcile-reason", help="Required to continue an uncertain native outcome after checking old jobs have stopped")
        if name != "list":
            operation.add_argument("--timeout", type=int, default=30 if name != "run" else 3600)
    memories = commands.add_parser("memory", help="Project-scoped memories, provenance and revisions")
    operations = memories.add_subparsers(dest="operation", required=True)
    for name in ("list", "sync", "search", "save", "history", "delete", "restore"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        if name in ("history", "delete", "restore"):
            operation.add_argument("id")
        if name == "search":
            operation.add_argument("query")
            operation.add_argument("--limit", type=int, default=10)
        if name == "sync":
            operation.add_argument("--rebuild", action="store_true", help="Rewrite active projections after restoring a ReMe workspace")
        if name == "save":
            operation.add_argument("--text", type=Path, required=True)
            operation.add_argument("--source", required=True)
            operation.add_argument("--source-revision", required=True)
            operation.add_argument("--id")
        if name in ("save", "delete", "restore"):
            operation.add_argument("--revision", type=int, default=0 if name == "save" else None, required=name != "save")
        if name == "restore":
            operation.add_argument("--from-revision", type=int, required=True)
    skill = commands.add_parser("skill", help="Import, evaluate, adopt and roll back Agent Skills")
    operations = skill.add_subparsers(dest="operation", required=True)
    for name in ("import", "list", "export", "adopt", "rollback", "optimize", "optimizations"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        if name == "import":
            operation.add_argument("directory", type=Path)
            operation.add_argument("--hypothesis", default="Imported candidate")
        if name in ("export", "rollback"):
            if name == "rollback":
                operation.add_argument("name")
            operation.add_argument("digest")
        if name == "export":
            operation.add_argument("destination", type=Path)
        if name == "adopt":
            operation.add_argument("--baseline-run", required=True)
            operation.add_argument("--candidate-run", required=True)
        if name in ("adopt", "rollback"):
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--reason", required=True)
        if name == "optimize":
            operation.add_argument("--baseline", required=True)
            operation.add_argument("--suite", required=True)
            operation.add_argument("--objective", required=True)
            operation.add_argument("--max-evaluations", type=int, default=20)
            operation.add_argument("--max-proposals", type=int, default=5)
            operation.add_argument("--timeout", type=int, default=300)
    evaluations = commands.add_parser("evaluation", help="Frozen inputs, trusted evaluators and evidence")
    operations = evaluations.add_subparsers(dest="operation", required=True)
    for name in ("register", "run", "list", "show", "compare"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        if name == "register":
            operation.add_argument("manifest", type=Path)
        if name == "run":
            operation.add_argument("digest")
            operation.add_argument("--suite", required=True)
        if name == "show":
            operation.add_argument("id")
        if name == "compare":
            operation.add_argument("baseline_run")
            operation.add_argument("candidate_run")
    sources = commands.add_parser("research", help="Bounded source snapshots and optional Temporal schedules")
    operations = sources.add_subparsers(dest="operation", required=True)
    for name in ("run", "list", "show", "cancel", "proposal", "review", "schedule", "worker"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        if name == "run":
            operation.add_argument("urls", nargs="+")
            operation.add_argument("--id")
        if name in ("show", "cancel", "proposal", "review"):
            operation.add_argument("id")
        if name == "review":
            operation.add_argument("--status", choices=["reviewed", "dismissed"], required=True)
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--reason", required=True)
        if name == "schedule":
            operation.add_argument("action", choices=["create", "status", "pause", "resume", "trigger", "delete"])
            operation.add_argument("name")
            operation.add_argument("--url", action="append")
            operation.add_argument("--interval", type=int, default=86400)
        if name in ("run", "schedule"):
            operation.add_argument("--max-bytes", type=int, default=1_000_000)
            operation.add_argument("--timeout", type=int, default=30)
            operation.add_argument("--allow-private", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    if os.name == "nt":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["workflow"]:
        return reference.workflow(argv[1:])
    args = parser().parse_args(argv)
    try:
        if args.command == "state":
            from . import backups

            root = resolve_home(args.home)
            if args.operation == "info":
                output = backups.info(root)
            elif args.operation == "backup":
                output = backups.create(root, args.directory, offline=args.offline)
            elif args.operation == "verify-backup":
                output = backups.verify(args.directory)
            else:
                output = backups.restore(root, args.directory, offline=args.offline)
        elif args.command == "reference":
            if args.operation == "executor":
                if not args.installation:
                    raise ValueError("The selectable executor requires --installation and an explicitly configured reference runtime")
                output = reference.executor(args.installation, State(args.home).root, args.request)
            else:
                output = reference.verify() if args.operation == "verify" else reference.info()
        elif args.command == "serve":
            try:
                import uvicorn
                from .web import create_app
            except ModuleNotFoundError as error:
                raise ValueError("Install ergora[web] to start the graphical console") from error
            uvicorn.run(create_app(args.home), host="127.0.0.1", port=args.port, proxy_headers=False)
            return 0
        elif args.command == "templates":
            if args.operation == "list":
                output = {"templates": list(reference.TEMPLATES)}
            elif args.operation == "agents":
                output = reference.agent_contract(args.kind)
            else:
                output = reference.copy_template(args.kind, args.destination)
        elif args.command == "project":
            state = State(args.home)
            if args.operation == "add":
                output = projects.create(state, args.id, args.repo)
            elif args.operation == "list":
                output = projects.list_projects(state)
            elif args.operation == "show":
                output = state.project(args.id)
            else:
                output = projects.bind(state, args.id, args.layer, json.loads(args.binding.read_text(encoding="utf-8-sig")), args.revision)
        elif args.command == "tools":
            output = tools.catalog() if args.operation == "list" else tools.doctor(State(args.home), args.project)
        elif args.command == "agent":
            state = State(args.home)
            if args.operation == "runs":
                output = agent_runs.runs(state, args.project)
            elif args.operation == "output":
                output = agent_runs.output(state, args.project, args.id)
            else:
                output = agent_runs.run_agent(state, args.project, args.role, args.prompt.read_text(encoding="utf-8-sig"), args.timeout, args.skill, args.recall, args.template)
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0 if args.operation != "run" or output["status"] == "succeeded" else 1
        elif args.command == "kernel":
            state = State(args.home)
            if args.operation == "list":
                output = kernel.listing(state, args.project)
            elif args.operation in ("plan", "prepare"):
                output = kernel.create(state, args.project, args.operation, args.timeout)
            else:
                output = kernel.operate(state, args.project, args.id, args.operation, args.timeout, getattr(args, "reconcile_reason", None))
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 1 if isinstance(output, dict) and output["status"] in ("failed", "outcome_unknown", "timed_out", "cancelled", "native_failed") else 0
        elif args.command == "memory":
            state = State(args.home)
            if args.operation == "list":
                output = memory.records(state, args.project)
            elif args.operation == "search":
                output = memory.search(state, args.project, args.query, args.limit)
            elif args.operation == "sync":
                output = memory.sync(state, args.project, args.rebuild)
            elif args.operation == "history":
                output = memory.history(state, args.project, args.id)
            elif args.operation == "delete":
                output = memory.delete(state, args.project, args.id, args.revision)
            elif args.operation == "restore":
                output = memory.restore(state, args.project, args.id, args.from_revision, args.revision)
            else:
                output = memory.save(state, args.project, args.text.read_text(encoding="utf-8-sig"),
                                     {"uri": args.source, "revision": args.source_revision}, args.id, args.revision)
        elif args.command == "skill":
            state = State(args.home)
            if args.operation == "import":
                output = skill_assets.import_bundle(state, args.project, args.directory, args.hypothesis)
            elif args.operation == "list":
                output = skill_assets.versions(state, args.project)
            elif args.operation == "export":
                output = skill_assets.export(state, args.project, args.digest, args.destination)
            elif args.operation == "adopt":
                output = skills.adopt(state, args.project, args.baseline_run, args.candidate_run, args.revision, args.reason)
            elif args.operation == "rollback":
                output = skill_assets.rollback(state, args.project, args.name, args.digest, args.revision, args.reason)
            elif args.operation == "optimizations":
                output = optimization.listing(state, args.project)
            else:
                output = optimization.optimize(state, args.project, args.baseline, args.suite, args.objective,
                                               args.max_evaluations, args.max_proposals, args.timeout)
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["status"] == "succeeded" else 1
        elif args.command == "evaluation":
            state = State(args.home)
            if args.operation == "register":
                output = evaluation.register(state, args.project, json.loads(args.manifest.read_text(encoding="utf-8-sig")))
            elif args.operation == "list":
                output = evaluation.listing(state, args.project)
            elif args.operation == "show":
                output = evaluation.get(state, args.project, args.id)
            elif args.operation == "compare":
                output = evaluation.compare(state, args.project, args.baseline_run, args.candidate_run)
            else:
                output = evaluation.evaluate(state, args.project, args.digest, args.suite)
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["status"] == "succeeded" else 1
        elif args.command == "research":
            state = State(args.home)
            if args.operation == "run":
                output = research.run(state, args.project, args.urls, args.max_bytes, args.timeout, args.allow_private, args.id)
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["status"] == "succeeded" else 1
            elif args.operation == "list":
                output = research.listing(state, args.project)
            elif args.operation == "show":
                output = research.get(state, args.project, args.id)
            elif args.operation == "cancel":
                output = research.cancel(state, args.project, args.id)
            elif args.operation == "proposal":
                output = research.proposal(state, args.project, args.id)
            elif args.operation == "review":
                output = research.review(state, args.project, args.id, args.status, args.revision, args.reason)
            else:
                try:
                    from . import scheduling
                except ModuleNotFoundError as error:
                    if error.name.startswith("temporalio"):
                        raise ValueError("Install ergora[temporal] before using persistent schedules") from error
                    raise
                if args.operation == "worker":
                    asyncio.run(scheduling.serve(state, args.project))
                    return 0
                if args.action == "create":
                    if not args.url:
                        raise ValueError("Schedule creation requires --url")
                    output = asyncio.run(scheduling.create(state, args.project, args.name, args.url, args.interval,
                                                          args.max_bytes, args.timeout, args.allow_private))
                else:
                    output = asyncio.run(scheduling.control(state, args.project, args.name, args.action))
        else:
            return reference.workflow(args.arguments)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        if args.command == "reference" and args.operation == "executor" and output and output["state"] != "SUCCEEDED":
            return 1
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
