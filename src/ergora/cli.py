from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

from . import __version__
from . import reference
from . import agent_runs, agents, evaluation, kernel, memory, optimization, projects, registrations, research, services, tasks, skill_assets, skills, tools
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
    legacy.add_argument("--project", help="Use a unified project's saved execution directories")
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
    configuration = operations.add_parser("config", help="Show effective bindings, sources and project revision")
    configuration.add_argument("id")
    registration = operations.add_parser("register", help="Register a complete project and publish reference configuration")
    registration.add_argument("definition", type=Path)
    registration.add_argument("--revision", type=int, required=True, help="0 for a new project, otherwise its current revision")
    registration = operations.add_parser("registration", help="Inspect publication and file consistency")
    registration.add_argument("id")
    registration = operations.add_parser("resume-registration", help="Resume the saved publication intent")
    registration.add_argument("id")
    registration.add_argument("--revision", type=int, required=True)
    importing = operations.add_parser("import-reference", help="Preview legacy adoption; applying requires the preview digest")
    importing.add_argument("specification", type=Path)
    importing.add_argument("--revision", type=int, required=True)
    importing.add_argument("--apply", action="store_true")
    importing.add_argument("--preview-sha256", help="Required with --apply; from the reviewed dry-run")
    bind = operations.add_parser("bind")
    bind.add_argument("id")
    bind.add_argument("layer")
    bind.add_argument("--binding", type=Path, required=True, help="JSON tool binding")
    bind.add_argument("--revision", type=int, required=True)
    tool = commands.add_parser("tools", help="List supported tools or check project availability")
    operations = tool.add_subparsers(dest="operation", required=True)
    operations.add_parser("list")
    operations.add_parser("profiles", help="Describe SDK installation combinations and their external requirements")
    doctor = operations.add_parser("doctor")
    doctor.add_argument("project")
    doctor.add_argument("--probe", action="store_true", help="Explicit local version/credential status and TCP probes; never calls a model")
    doctor.add_argument("--timeout", type=int, default=5, help="Total active probe budget in seconds (1–30)")
    task = commands.add_parser("task", help="Preview, create, recover and read formal development task contracts")
    operations = task.add_subparsers(dest="operation", required=True)
    listing = operations.add_parser("list")
    listing.add_argument("project")
    listing.add_argument("--limit", type=int, default=50)
    listing.add_argument("--after", help="Continue using the returned opaque directory cursor")
    show_task = operations.add_parser("show")
    show_task.add_argument("project")
    show_task.add_argument("task_id")
    status_task = operations.add_parser("status", help="Query original Temporal facts without starting or changing execution")
    status_task.add_argument("project")
    status_task.add_argument("task_id")
    status_task.add_argument("--run-id", help="Pin a previously observed native run ID")
    status_task.add_argument("--timeout", type=int, default=20)
    events = operations.add_parser("events", help="Read bounded original-run event metadata without raw payloads")
    events.add_argument("project")
    events.add_argument("task_id")
    events.add_argument("--run-id", required=True)
    events.add_argument("--limit", type=int, default=20)
    events.add_argument("--after", help="Continue using the returned original-run event cursor")
    events.add_argument("--timeout", type=int, default=20)
    job = operations.add_parser("job", help="Read an original scheduled job's receipt and UTF-8 artifact window")
    job.add_argument("project")
    job.add_argument("task_id")
    job.add_argument("--run-id", required=True)
    job.add_argument("--event-id", type=int, required=True)
    job.add_argument("--artifact", help="Select an artifact name from the original job receipt")
    job.add_argument("--receipt-sha256", help="Pin the receipt observed before reading an artifact")
    job.add_argument("--offset", type=int, default=0, help="Unicode character offset in the original text")
    job.add_argument("--limit", type=int, default=8192, help="Maximum Unicode characters in one window (1–16384)")
    job.add_argument("--timeout", type=int, default=20)
    for name in ("preview", "create"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("--definition", type=Path, required=True)
        operation.add_argument("--revision", type=int, required=True)
        if name == "create":
            operation.add_argument("--preview-sha256", required=True)
    for name in ("creation", "resume-create"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("task_id")
        if name == "resume-create":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--intent-sha256", required=True)
    for name in ("start", "submission", "resume-start"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("task_id")
        if name != "submission":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--timeout", type=int, default=20)
            operation.add_argument("--creation-sha256" if name == "start" else "--intent-sha256", required=True)
    plan = operations.add_parser("plan", help="Read bounded materials for an exact pending plan without approving it")
    plan.add_argument("project")
    plan.add_argument("task_id")
    plan.add_argument("--run-id", required=True)
    plan.add_argument("--plan-sha256", required=True)
    plan.add_argument("--timeout", type=int, default=20)
    approving = operations.add_parser("approve", help="Record an explicit owner decision for the exact native run and plan")
    approving.add_argument("project")
    approving.add_argument("task_id")
    approving.add_argument("--decision-id", required=True)
    approving.add_argument("--revision", type=int, required=True)
    approving.add_argument("--run-id", required=True)
    approving.add_argument("--plan-sha256", required=True)
    approving.add_argument("--confirm", action="store_true", required=True)
    approving.add_argument("--timeout", type=int, default=20)
    for name in ("approval", "resume-approve"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("task_id")
        operation.add_argument("decision_id")
        if name == "resume-approve":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--intent-sha256", required=True)
            operation.add_argument("--confirm", action="store_true", required=True)
            operation.add_argument("--timeout", type=int, default=20)
    cancelling = operations.add_parser("cancel", help="Request cooperative cancellation for the original native run")
    cancelling.add_argument("project")
    cancelling.add_argument("task_id")
    cancelling.add_argument("--request-id", required=True)
    cancelling.add_argument("--revision", type=int, required=True)
    cancelling.add_argument("--run-id", required=True)
    cancelling.add_argument("--reason", required=True)
    cancelling.add_argument("--confirm", action="store_true", required=True)
    cancelling.add_argument("--timeout", type=int, default=20)
    for name in ("cancellation", "resume-cancel"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("task_id")
        operation.add_argument("request_id")
        if name == "resume-cancel":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--intent-sha256", required=True)
            operation.add_argument("--confirm", action="store_true", required=True)
            operation.add_argument("--timeout", type=int, default=20)
    external = operations.add_parser("external-status", help="Inspect a closed original run's external job evidence")
    external.add_argument("project")
    external.add_argument("task_id")
    external.add_argument("--run-id", required=True)
    external.add_argument("--timeout", type=int, default=20)
    reconciling = operations.add_parser("reconcile", help="Confirm a closed original run's external cleanup and ingress release")
    reconciling.add_argument("project")
    reconciling.add_argument("task_id")
    reconciling.add_argument("--revision", type=int, required=True)
    reconciling.add_argument("--run-id", required=True)
    reconciling.add_argument("--confirm", action="store_true", required=True)
    reconciling.add_argument("--timeout", type=int, default=20)
    for name in ("reconciliation", "resume-reconcile"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("task_id")
        if name == "resume-reconcile":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--intent-sha256", required=True)
            operation.add_argument("--confirm", action="store_true", required=True)
            operation.add_argument("--timeout", type=int, default=20)
    exporting = operations.add_parser("export", help="Export an exact reviewed candidate to a local branch")
    exporting.add_argument("project")
    exporting.add_argument("task_id")
    exporting.add_argument("--revision", type=int, required=True)
    exporting.add_argument("--run-id", required=True)
    exporting.add_argument("--candidate-sha", required=True)
    exporting.add_argument("--branch", required=True)
    exporting.add_argument("--confirm", action="store_true", required=True)
    exporting.add_argument("--timeout", type=int, default=20)
    for name in ("export-status", "resume-export"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("task_id")
        if name == "resume-export":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--intent-sha256", required=True)
            operation.add_argument("--confirm", action="store_true", required=True)
            operation.add_argument("--timeout", type=int, default=20)
    service = commands.add_parser("services", help="Explicit selected-service Supervisor operations (Linux/WSL2)")
    operations = service.add_subparsers(dest="operation", required=True)
    status = operations.add_parser("status")
    status.add_argument("project")
    for name in ("start", "stop", "shutdown"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        if name != "shutdown":
            operation.add_argument("names", nargs="+", choices=services.NAMES)
        operation.add_argument("--revision", type=int, required=True)
        operation.add_argument("--timeout", type=int, default=30)
        if name != "start":
            operation.add_argument("--confirm", action="store_true", required=True)
    logs = operations.add_parser("logs")
    logs.add_argument("project")
    logs.add_argument("name", choices=services.NAMES)
    logs.add_argument("--offset", type=int, default=0)
    logs.add_argument("--bytes", type=int, default=8192)
    logs.add_argument("--stderr", action="store_true")
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
                if args.project:
                    if args.installation:
                        raise ValueError("Choose --project or --installation")
                    saved = State(args.home).project(args.project)
                    if "registration" not in saved or saved["registration"]["status"] != "published":
                        raise ValueError("The project needs a published unified registration")
                    execution = saved["registration"]["definition"]["execution"]
                    args.installation = Path(execution["installation"])
                    os.environ.update(AGENTFLOW_CONFIG_DIR=execution["config_directory"], AGENTFLOW_STATE_DIR=execution["state_directory"])
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
            elif args.operation == "config":
                output = projects.effective_configuration(state.project(args.id))
            elif args.operation == "register":
                output = registrations.register(state, json.loads(args.definition.read_text(encoding="utf-8-sig")), args.revision)
            elif args.operation == "registration":
                output = registrations.status(state, args.id)
            elif args.operation == "resume-registration":
                output = registrations.resume(state, args.id, args.revision)
            elif args.operation == "import-reference":
                specification = json.loads(args.specification.read_text(encoding="utf-8-sig"))
                if args.apply:
                    if not args.preview_sha256:
                        raise ValueError("Applying a legacy import requires --preview-sha256 from a reviewed preview")
                    output = registrations.apply_import(state, specification, args.revision, args.preview_sha256)
                else:
                    if args.preview_sha256:
                        raise ValueError("--preview-sha256 requires --apply")
                    output = registrations.preview_import(state, specification, args.revision)
            else:
                output = projects.bind(state, args.id, args.layer, json.loads(args.binding.read_text(encoding="utf-8-sig")), args.revision)
        elif args.command == "tools":
            if args.operation == "profiles":
                output = tools.installation_profiles()
            else:
                output = tools.catalog() if args.operation == "list" else tools.doctor(State(args.home), args.project, probe=args.probe, timeout=args.timeout)
        elif args.command == "task":
            state = State(args.home)
            if args.operation == "list":
                output = tasks.listing(state, args.project, limit=args.limit, after=args.after)
            elif args.operation == "show":
                output = tasks.show(state, args.project, args.task_id)
            elif args.operation == "status":
                output = tasks.status(state, args.project, args.task_id, run_id=args.run_id, timeout=args.timeout)
            elif args.operation == "events":
                output = tasks.events(state, args.project, args.task_id, run_id=args.run_id,
                                      limit=args.limit, after=args.after, timeout=args.timeout)
            elif args.operation == "job":
                output = tasks.job(state, args.project, args.task_id, run_id=args.run_id, event_id=args.event_id,
                                   artifact=args.artifact, receipt_sha256=args.receipt_sha256,
                                   offset=args.offset, limit=args.limit, timeout=args.timeout)
            elif args.operation == "plan":
                output = tasks.plan(state, args.project, args.task_id, run_id=args.run_id,
                                    plan_sha256=args.plan_sha256, timeout=args.timeout)
            elif args.operation == "creation":
                output = tasks.creation(state, args.project, args.task_id)
            elif args.operation == "resume-create":
                output = tasks.resume_create(state, args.project, args.task_id, args.revision, args.intent_sha256)
            elif args.operation == "submission":
                output = tasks.submission(state, args.project, args.task_id)
            elif args.operation in ("start", "resume-start"):
                output = (tasks.start(state, args.project, args.task_id, args.revision, args.creation_sha256, timeout=args.timeout)
                          if args.operation == "start" else
                          tasks.resume_start(state, args.project, args.task_id, args.revision, args.intent_sha256, timeout=args.timeout))
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["status"] == "submitted" else 1
            elif args.operation == "external-status":
                output = tasks.external_status(state, args.project, args.task_id, run_id=args.run_id, timeout=args.timeout)
            elif args.operation == "reconciliation":
                output = tasks.reconciliation(state, args.project, args.task_id)
            elif args.operation in ("reconcile", "resume-reconcile"):
                output = (tasks.reconcile(state, args.project, args.task_id, args.revision,
                                          run_id=args.run_id, confirm=args.confirm, timeout=args.timeout)
                          if args.operation == "reconcile" else
                          tasks.resume_reconcile(state, args.project, args.task_id, args.revision,
                                                 args.intent_sha256, confirm=args.confirm, timeout=args.timeout))
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["status"] == "reconciled" else 1
            elif args.operation == "export-status":
                output = tasks.export_status(state, args.project, args.task_id)
            elif args.operation in ("export", "resume-export"):
                output = (tasks.export(state, args.project, args.task_id, args.revision,
                                       run_id=args.run_id, candidate_sha=args.candidate_sha, branch=args.branch,
                                       confirm=args.confirm, timeout=args.timeout)
                          if args.operation == "export" else
                          tasks.resume_export(state, args.project, args.task_id, args.revision,
                                              args.intent_sha256, confirm=args.confirm, timeout=args.timeout))
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["status"] == "exported" else 1
            elif args.operation == "approval":
                output = tasks.approval(state, args.project, args.task_id, args.decision_id)
            elif args.operation in ("approve", "resume-approve"):
                output = (tasks.approve(state, args.project, args.task_id, args.decision_id, args.revision,
                                        run_id=args.run_id, plan_sha256=args.plan_sha256, confirm=args.confirm, timeout=args.timeout)
                          if args.operation == "approve" else
                          tasks.resume_approve(state, args.project, args.task_id, args.decision_id, args.revision,
                                               args.intent_sha256, confirm=args.confirm, timeout=args.timeout))
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["status"] == "requested" else 1
            elif args.operation == "cancellation":
                output = tasks.cancellation(state, args.project, args.task_id, args.request_id)
            elif args.operation in ("cancel", "resume-cancel"):
                output = (tasks.cancel(state, args.project, args.task_id, args.request_id, args.revision,
                                       run_id=args.run_id, reason=args.reason, confirm=args.confirm, timeout=args.timeout)
                          if args.operation == "cancel" else
                          tasks.resume_cancel(state, args.project, args.task_id, args.request_id, args.revision,
                                              args.intent_sha256, confirm=args.confirm, timeout=args.timeout))
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["status"] in ("requested", "already_closed") else 1
            else:
                definition = json.loads(args.definition.read_text(encoding="utf-8-sig"))
                output = (tasks.preview(state, args.project, definition, args.revision) if args.operation == "preview"
                          else tasks.create(state, args.project, definition, args.revision, args.preview_sha256))
        elif args.command == "services":
            state = State(args.home)
            if args.operation == "status":
                output = services.status(state, args.project)
            elif args.operation == "logs":
                output = services.logs(state, args.project, args.name, offset=args.offset, limit=args.bytes, stderr=args.stderr)
            else:
                output = services.control(state, args.project, args.operation, getattr(args, "names", []), args.revision,
                                          confirm=getattr(args, "confirm", False), timeout=args.timeout)
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
        if args.command == "services" and output.get("outcome") in ("unconfirmed", "failed"):
            return 1
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
