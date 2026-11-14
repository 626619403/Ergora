from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

from . import __version__
from . import reference
from . import agent_definitions, agent_runs, agents, contracts, definition_bundles, evaluation, issues, issue_writebacks, kernel, memory, optimization, projects, registrations, research, services, tasks, skill_assets, skills, tools, training, workflow_definitions
from .state import State, resolve_home


def _definition_edit_parsers(operations) -> None:
    revision = operations.add_parser("revise", help="Derive an immutable version from a pinned complete package")
    revision.add_argument("id")
    revision.add_argument("version", help="Exact base version")
    revision.add_argument("--base-digest", required=True)
    revision.add_argument("--document", type=Path, required=True, help="Complete new standard definition document")
    revision.add_argument("--format", choices=("json", "yaml"), default="json", help="Document representation; stored packages remain JSON")
    revision.add_argument("--check", action="store_true", help="Validate without publishing a version")
    revision.add_argument("--resources", type=Path, help="Local changes.json and files/<package path> directory")
    revision.add_argument("--preview-resources", action="store_true", help="Suggest resource hashes and candidate identity without publishing")
    revision.add_argument("--accept-candidate", type=Path, help="Saved resource preview response explicitly accepted for this candidate")
    file = operations.add_parser("file", help="Read a bounded byte window of a pinned package file")
    file.add_argument("id")
    file.add_argument("version")
    file.add_argument("path")
    file.add_argument("--base-digest", required=True)
    file.add_argument("--offset", type=int, default=0)
    file.add_argument("--limit", type=int, default=65_536)


def _definition_revision_options(args) -> dict:
    accepted = None
    if args.accept_candidate:
        response = definition_bundles.read_json(args.accept_candidate)
        if not isinstance(response, dict) or not isinstance(response.get("candidate"), dict):
            raise ValueError("--accept-candidate requires a saved resource preview response with candidate")
        accepted = response["candidate"]
    return {"definition": definition_bundles.convert_document(
                args.document.read_text(encoding="utf-8-sig"), args.format)["definition"],
            "publish": not (args.check or args.preview_resources), "preview_resources": args.preview_resources,
            "resource_changes": definition_bundles.resource_changes_from_directory(args.resources) if args.resources else None,
            "accepted_candidate": accepted}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="ergora", description="Project collaboration and continuous improvement")
    result.add_argument("--version", action="version", version=__version__)
    result.add_argument("--home", type=Path, help="Persistent state directory (default: ERGORA_HOME, LocalAppData on Windows, or XDG data)")
    commands = result.add_subparsers(dest="command", required=True)
    handoff = commands.add_parser("handoff", help="Verify portable evidence without services or local state")
    operations = handoff.add_subparsers(dest="operation", required=True)
    for name in ("verify", "read"):
        operation = operations.add_parser(name)
        operation.add_argument("path", type=Path)
        operation.add_argument("--sha256", help="Independently obtained whole-packet SHA256")
        if name == "read":
            operation.add_argument("--selection", type=Path, help="JSON array of exact job_id/name pairs; omitted reads the complete index")
    retrospective = commands.add_parser("retrospective", help="Prepare, check or export source-bound Skill and memory proposals; never adopt")
    operations = retrospective.add_subparsers(dest="operation", required=True)
    for name in ("prepare", "prepare-memory"):
        preparing = operations.add_parser(name, help="Freeze complete evidence and the selected baseline for a proposal-producing leaf")
        preparing.add_argument("project")
        preparing.add_argument("packet", type=Path)
        preparing.add_argument("--selection", type=Path, required=True)
        preparing.add_argument("--packet-sha256", required=True)
        if name == "prepare":
            preparing.add_argument("--skill", required=True)
            preparing.add_argument("--digest", required=True)
            preparing.add_argument("--head-revision", type=int, required=True)
        else:
            target = preparing.add_mutually_exclusive_group(required=True)
            target.add_argument("--new-memory", action="store_true")
            target.add_argument("--memory-id")
            preparing.add_argument("--revision", type=int, default=0, help="Exact current memory revision; zero for explicit creation")
        preparing.add_argument("--objective", type=Path, required=True)
        preparing.add_argument("--manifest", type=Path, required=True)
        preparing.add_argument("--instance", required=True)
        preparing.add_argument("--directory", type=Path, required=True)
        preparing.add_argument("--max-prompt-bytes", type=int, required=True)
    for name in ("check", "check-memory"):
        checking = operations.add_parser(name, help="Check a structured result (up to 8 MiB) against its frozen input, offline")
        checking.add_argument("input", type=Path)
        checking.add_argument("result", type=Path)
        checking.add_argument("--result-sha256")
    for name in ("export", "export-memory"):
        exporting = operations.add_parser(name, help="Explicitly save one checked complete candidate to a new directory; never adopt")
        exporting.add_argument("input", type=Path)
        exporting.add_argument("result", type=Path)
        exporting.add_argument("destination", type=Path)
        exporting.add_argument("--result-sha256", required=True)
        exporting.add_argument("--candidate-digest", required=True)
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
    composition = commands.add_parser("composition", help="Check nested definitions, prepare inputs or explicitly invoke a leaf")
    operations = composition.add_subparsers(dest="operation", required=True)
    _definition_edit_parsers(operations)
    operations.add_parser("presets", help="List bundled domain recipes and their actual execution scope")
    preset = operations.add_parser("install-preset", help="Import a bundled recipe's exact dependencies; does not authorize execution")
    preset.add_argument("id", help="Bundled recipe ID from composition presets")
    for name in ("check", "import"):
        operation = operations.add_parser(name)
        operation.add_argument("directory", type=Path)
        if name == "check":
            operation.add_argument("--material", action="store_true")
    operations.add_parser("list")
    for name in ("show", "export", "preview", "prepare", "prepare-manifest", "freeze-manifest"):
        operation = operations.add_parser(name)
        operation.add_argument("id")
        operation.add_argument("version")
        if name == "show":
            operation.add_argument("--material", action="store_true")
        elif name == "export":
            operation.add_argument("directory", type=Path)
        else:
            operation.add_argument("--grant", type=Path, required=True, help="Explicit JSON preview permissions and global limits")
            if name == "prepare":
                operation.add_argument("instance", help="Exact Agent leaf path from composition preview")
                operation.add_argument("--task", type=Path, required=True, help="Operator-supplied UTF-8 task; does not execute workflow ports")
                operation.add_argument("--directory", type=Path, required=True, help="New complete input bundle directory")
                operation.add_argument("--max-prompt-bytes", type=int, required=True, help="Complete user prompt limit; not a model token guarantee")
            elif name == "prepare-manifest":
                operation.add_argument("--directory", type=Path, required=True, help="New complete static composition directory")
            elif name == "freeze-manifest":
                operation.add_argument("--preview-sha256", required=True, help="Accepted exact preview; persists a complete package in the control directory")
    frozen = operations.add_parser("show-manifest", help="Verify an original saved package by preview SHA256; no live admission")
    frozen.add_argument("preview_sha256")
    frozen.add_argument("--material", action="store_true")
    for name in ("verify-input", "verify-manifest"):
        operation = operations.add_parser(name)
        operation.add_argument("directory", type=Path)
        operation.add_argument("--material", action="store_true")
    from_manifest = operations.add_parser("prepare-from-manifest", help="Prepare an independent leaf input from a verified static package")
    from_manifest.add_argument("manifest", type=Path)
    from_manifest.add_argument("instance", help="Exact Agent leaf path from the static composition")
    from_manifest.add_argument("--task", type=Path, required=True, help="Operator-supplied UTF-8 task; workflow ports remain unexecuted")
    from_manifest.add_argument("--directory", type=Path, required=True, help="New complete input bundle directory")
    from_manifest.add_argument("--max-prompt-bytes", type=int, required=True, help="Complete user prompt limit; not a model token guarantee")
    for name in ("check-input", "run-input"):
        operation = operations.add_parser(name, help="Check current leaf capabilities" if name == "check-input" else
                                         "Independent restricted leaf call; no workflow ports or formal approval")
        operation.add_argument("project")
        operation.add_argument("directory", type=Path)
        operation.add_argument("--mode", choices=("text-only", "task-mcp"), default="text-only")
        operation.add_argument("--backend", choices=sorted({tool for choices in agents.CHOICES.values() for tool in choices}),
                               help="Registered Agent backend; unsupported role/mode/configuration fails admission")
        operation.add_argument("--model")
        operation.add_argument("--backend-reason")
        operation.add_argument("--codex-config", type=Path, help="Inference settings only; native tool and permission settings are ignored")
        if name == "run-input":
            operation.add_argument("--timeout", type=int, default=300)
            operation.add_argument("--allow-one-continuation", action="store_true",
                                   help="Enable one explicit follow-up for a new standalone task-MCP source; unsupported backends fail")
    continuation = operations.add_parser("continue-input", help="Send one explicit new prepared input to an enabled native source")
    continuation.add_argument("project")
    continuation.add_argument("source_run")
    continuation.add_argument("directory", type=Path)
    continuation.add_argument("--intent", required=True, help="Stable input identity; repeats return the original saved attempt")
    continuation.add_argument("--timeout", type=int, default=300)
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
    issue = commands.add_parser("issue", help="Read tracker context and explicitly confirm candidate association comments")
    operations = issue.add_subparsers(dest="operation", required=True)
    show_issue = operations.add_parser("show", help="Read one GitHub number or GitLab iid using the selected tracker")
    show_issue.add_argument("project")
    show_issue.add_argument("issue_id")
    capture_issue = operations.add_parser("capture", help="Save a complete immutable issue context snapshot")
    capture_issue.add_argument("project")
    capture_issue.add_argument("issue_id")
    capture_issue.add_argument("--revision", type=int, required=True)
    saved_issue = operations.add_parser("snapshot", help="Read one complete saved snapshot offline")
    saved_issue.add_argument("project")
    saved_issue.add_argument("sha256")
    saved_issues = operations.add_parser("snapshots", help="List bounded saved snapshot metadata offline")
    saved_issues.add_argument("project")
    saved_issues.add_argument("--limit", type=int, default=50)
    saved_issues.add_argument("--after")
    link_issue = operations.add_parser("link-task", help="Associate context with an exact published creation; does not start execution")
    link_issue.add_argument("project")
    link_issue.add_argument("snapshot_sha256")
    link_issue.add_argument("task_id")
    link_issue.add_argument("--creation-sha256", required=True)
    link_issue.add_argument("--revision", type=int, required=True)
    link_issue.add_argument("--reason", required=True)
    issue_links = operations.add_parser("links", help="Read saved task context associations offline")
    issue_links.add_argument("project")
    issue_links.add_argument("--snapshot", dest="snapshot_sha256")
    issue_links.add_argument("--task", dest="task_id")
    issue_links.add_argument("--limit", type=int, default=50)
    issue_links.add_argument("--after")
    for name in ("writeback-prepare", "writeback-label-prepare"):
        writing = operations.add_parser(name, help={
            'writeback-prepare': 'Prepare a fixed comment for an exact exported v7 candidate; sends no comment',
            'writeback-label-prepare': 'Prepare one existing GitHub label by native ID; sends no mutation'}[name])
        writing.add_argument("project")
        writing.add_argument("task_id")
        writing.add_argument("--revision", type=int, required=True)
        writing.add_argument("--run-id", required=True)
        writing.add_argument("--candidate-sha", required=True)
        if name == 'writeback-label-prepare':
            writing.add_argument("--label-name", required=True)
    candidate = operations.add_parser("candidate-observe", help="Compare original exported content with current local and remote refs; read only")
    candidate.add_argument("project")
    candidate.add_argument("task_id")
    candidate.add_argument("--revision", type=int, required=True)
    candidate.add_argument("--run-id", required=True)
    candidate.add_argument("--candidate-sha", required=True)
    candidate.add_argument("--base-branch", required=True, help="Explicit remote base branch; never inferred from its current default")
    review = operations.add_parser("review-link", help="Save an explicit existing PR/MR as immutable candidate context; provider GET only")
    review.add_argument("project")
    review.add_argument("task_id")
    review.add_argument("--revision", type=int, required=True)
    review.add_argument("--run-id", required=True)
    review.add_argument("--candidate-sha", required=True)
    review.add_argument("--base-branch", required=True)
    review.add_argument("--review-number", required=True, help="Repository PR number or project MR iid, not a global ID or URL")
    review.add_argument("--reason", required=True)
    saved_review = operations.add_parser("review-link-show", help="Read saved candidate review context offline by content identity")
    saved_review.add_argument("project")
    saved_review.add_argument("sha256")
    for name in ("writeback-status", "writeback-send", "writeback-observe"):
        writing = operations.add_parser(name, help={
            'writeback-status': 'Read the saved writeback offline',
            'writeback-send': 'Confirm one saved intent; an existing attempt is never resent',
            'writeback-observe': 'Read one current resource or comment page without acknowledging an unknown attempt'}[name])
        writing.add_argument("project")
        writing.add_argument("intent_sha256")
        if name == 'writeback-send':
            writing.add_argument("--revision", type=int, required=True)
            writing.add_argument("--confirm", action="store_true", required=True)
        elif name == 'writeback-observe':
            writing.add_argument("--comment-id")
            writing.add_argument("--page", type=int, default=1)
            writing.add_argument("--cursor", help="Read one current label page using its opaque GraphQL cursor")
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
    for name in ("prepare", "preview", "create"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("--definition", type=Path, required=True)
        operation.add_argument("--revision", type=int, required=True)
        if name == "create":
            operation.add_argument("--preview-sha256", required=True)
            operation.add_argument("--prepare-sha256", help="Required for a budgeted v5–v7 task's original authorization")
    for name in ("preparation", "creation", "resume-create"):
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
    evidence = operations.add_parser("evidence", help="Index original contracts, published receipts and artifact references")
    evidence.add_argument("project")
    evidence.add_argument("task_id")
    evidence.add_argument("--run-id", required=True)
    evidence.add_argument("--timeout", type=int, default=20)
    handoff = operations.add_parser("handoff", help="Collect a closed original run's published evidence into a new ZIP")
    handoff.add_argument("project")
    handoff.add_argument("task_id")
    handoff.add_argument("--run-id", required=True)
    handoff.add_argument("--output", type=Path, required=True)
    handoff.add_argument("--timeout", type=int, default=20)
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
    definition = operations.add_parser("definition", help="Check and share static specialist recipes; importing never executes them")
    definitions = definition.add_subparsers(dest="definition_operation", required=True)
    _definition_edit_parsers(definitions)
    for name in ("check", "import"):
        operation = definitions.add_parser(name)
        operation.add_argument("directory", type=Path)
        if name == "check":
            operation.add_argument("--material", action="store_true", help="Include full instruction, context and SKILL.md text")
    listing = definitions.add_parser("list")
    listing.add_argument("--role", help="Filter stored role labels, including roles no longer available for execution")
    listing.add_argument("--specialty")
    for name in ("show", "export"):
        operation = definitions.add_parser(name)
        operation.add_argument("id")
        operation.add_argument("version")
        if name == "export":
            operation.add_argument("directory", type=Path)
        else:
            operation.add_argument("--material", action="store_true")
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
    preview.add_argument("--native-history", action="store_true", help="Read a page of saved native history without starting the backend")
    preview.add_argument("--history-offset", type=int, default=0, help="Byte offset returned by the previous history page")
    preview.add_argument("--history-limit", type=int, default=65536, help="UTF-8 byte window, 4–65536 bytes")
    preview.add_argument("--history-revision", help="Observation revision required after the first history page")
    experiments = commands.add_parser("training", help="Observe native experiments; explicitly submit, cancel or reconcile original operations")
    operations = experiments.add_subparsers(dest="operation", required=True)
    for name in ("baseline-preview", "init-baseline", "runner-preview", "register-runner"):
        operation = operations.add_parser(name, help="Preview or explicitly publish native baseline/runner configuration; never execute training")
        operation.add_argument("project")
        runner = name in ("runner-preview", "register-runner")
        operation.add_argument("--runner" if runner else "--baseline", dest="document", type=Path, required=True)
        if name in ("init-baseline", "register-runner"):
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--runner-sha256" if runner else "--baseline-sha256", dest="document_sha256", required=True,
                                   help="Content SHA-256 returned by the corresponding preview")
    for name in ("experiment-preview", "prepare"):
        operation = operations.add_parser(name, help="Preview or explicitly prepare the original immutable experiment files; never start training")
        operation.add_argument("project")
        operation.add_argument("--experiment", type=Path, required=True)
        operation.add_argument("--runner", required=True, help="Already registered project runner ID")
        operation.add_argument("--max-run-seconds", type=int, help="Native queue-plus-run window; omitted uses the original default")
        if name == "prepare":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--preview-sha256", required=True)
    for name in ("preparation", "resume-prepare"):
        operation = operations.add_parser(name, help="Read or explicitly recover the same original preparation intent")
        operation.add_argument("project")
        operation.add_argument("experiment_id")
        if name == "resume-prepare":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--intent-sha256", required=True)
    for name in ("list", "show"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        if name == "show":
            operation.add_argument("experiment_id")
        else:
            operation.add_argument("--limit", type=int, default=50)
            operation.add_argument("--after", help="Directory cursor from the previous page")
    evidence = operations.add_parser("evidence", help="Read original archived evidence and an optional fully hashed text window; never approve")
    evidence.add_argument("project")
    evidence.add_argument("experiment_id")
    evidence.add_argument("--artifact", help="Relative path listed by the original evidence bundle")
    evidence.add_argument("--evidence-sha256", help="Exact observed content address; required with --artifact")
    evidence.add_argument("--offset", type=int, default=0, help="Unicode character offset in the selected text artifact")
    evidence.add_argument("--limit", type=int, default=12_000, help="Text window size, at most 65,536 characters")
    live = operations.add_parser("status", help="Query the original workflow; never start, cancel or approve an experiment")
    live.add_argument("project")
    live.add_argument("experiment_id")
    live.add_argument("--run-id", help="Pin the query to an existing native run ID")
    live.add_argument("--timeout", type=int, default=20)
    for name in ("submission", "start", "resume-start"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("experiment_id")
        if name != "submission":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--manifest-sha256" if name == "start" else "--intent-sha256", required=True)
            operation.add_argument("--timeout", type=int, default=20)
    for name in ("approval", "approve", "resume-approve"):
        operation = operations.add_parser(name, help="Read or explicitly confirm the original owner decision; delivery is not authorization")
        operation.add_argument("project")
        operation.add_argument("experiment_id")
        if name != "approval":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--confirm", action="store_true", required=True)
            operation.add_argument("--timeout", type=int, default=20)
            if name == "approve":
                operation.add_argument("--run-id", required=True)
                operation.add_argument("--evidence-sha256", required=True)
            else:
                operation.add_argument("--intent-sha256", required=True)
    for name in ("cancellation", "cancel", "resume-cancel", "stop-status"):
        operation = operations.add_parser(name)
        operation.add_argument("project")
        operation.add_argument("experiment_id")
        if name != "stop-status":
            operation.add_argument("request_id", help="Stable cancellation request ID; reuse it for recovery")
        if name in ("cancel", "resume-cancel"):
            operation.add_argument("--revision", type=int, required=True)
            if name == "cancel":
                operation.add_argument("--run-id", required=True)
                operation.add_argument("--reason", required=True)
            else:
                operation.add_argument("--intent-sha256", required=True)
        if name != "cancellation":
            operation.add_argument("--timeout", type=int, default=20)
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
    for name in ("list", "catalog", "sync", "search", "save", "history", "delete", "restore"):
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
            expiry = operation.add_mutually_exclusive_group()
            expiry.add_argument("--expires-at", default=argparse.SUPPRESS,
                                help="ISO 8601 timestamp with timezone; omitted corrections preserve the previous limit")
            expiry.add_argument("--no-expiry", dest="expires_at", action="store_const", const=None,
                                default=argparse.SUPPRESS, help="Explicitly remove an expiry limit")
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
        if args.command == "handoff":
            from . import handoff

            output = (handoff.verify(args.path, sha256=args.sha256) if args.operation == "verify" else
                      handoff.evidence(args.path, definition_bundles.read_json(args.selection) if args.selection else None,
                                       sha256=args.sha256))
        elif args.command == "retrospective":
            from . import retrospectives

            if args.operation == "check":
                output = retrospectives.check(args.input, args.result, result_sha256=args.result_sha256)
            elif args.operation == "check-memory":
                output = retrospectives.check_memory(args.input, args.result, result_sha256=args.result_sha256)
            elif args.operation == "export":
                output = retrospectives.export(args.input, args.result, args.destination,
                    result_sha256=args.result_sha256, candidate_digest=args.candidate_digest)
            elif args.operation == "export-memory":
                output = retrospectives.export_memory(args.input, args.result, args.destination,
                    result_sha256=args.result_sha256, candidate_digest=args.candidate_digest)
            else:
                with args.objective.open('rb') as stream:
                    raw = stream.read(262145)
                if len(raw) > 262144:
                    raise ValueError('Retrospective objective exceeds 256 KiB')
                options = {'packet_sha256': args.packet_sha256, 'objective': raw.decode('utf-8-sig'),
                           'manifest': args.manifest, 'instance': args.instance,
                           'destination': args.directory, 'max_prompt_bytes': args.max_prompt_bytes}
                if args.operation == "prepare-memory":
                    output = retrospectives.prepare_memory(State(args.home), args.project, args.packet,
                        definition_bundles.read_json(args.selection), memory_id=args.memory_id,
                        revision=args.revision, **options)
                else:
                    output = retrospectives.prepare(State(args.home), args.project, args.packet,
                        definition_bundles.read_json(args.selection), name=args.skill, digest=args.digest,
                        head_revision=args.head_revision, **options)
        elif args.command == "state":
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
        elif args.command == "issue":
            state = State(args.home)
            if args.operation == "show":
                output = issues.show(state, args.project, args.issue_id)
            elif args.operation == "capture":
                output = issues.capture(state, args.project, args.issue_id, args.revision)
            elif args.operation == "snapshot":
                output = issues.snapshot(state, args.project, args.sha256)
            elif args.operation == "snapshots":
                output = issues.snapshots(state, args.project, limit=args.limit, after=args.after)
            elif args.operation == "link-task":
                output = issues.link_task(state, args.project, args.snapshot_sha256, args.task_id,
                                          args.creation_sha256, args.revision, args.reason)
            elif args.operation == 'links':
                output = issues.links(state, args.project, snapshot_sha256=args.snapshot_sha256,
                                      task_id=args.task_id, limit=args.limit, after=args.after)
            elif args.operation == 'writeback-prepare':
                output = issue_writebacks.prepare(state, args.project, args.task_id, args.revision,
                                                  run_id=args.run_id, candidate_sha=args.candidate_sha)
            elif args.operation == 'writeback-label-prepare':
                output = issue_writebacks.prepare_label(state, args.project, args.task_id, args.revision,
                    run_id=args.run_id, candidate_sha=args.candidate_sha, label_name=args.label_name)
            elif args.operation == 'candidate-observe':
                output = issues.remote_candidate(state, args.project, args.task_id, args.revision,
                    run_id=args.run_id, candidate_sha=args.candidate_sha, base_branch=args.base_branch)
            elif args.operation == 'review-link':
                output = issues.link_review(state, args.project, args.task_id, args.revision,
                    run_id=args.run_id, candidate_sha=args.candidate_sha, base_branch=args.base_branch,
                    review_number=args.review_number, reason=args.reason)
            elif args.operation == 'review-link-show':
                output = issues.review_link(state, args.project, args.sha256)
            elif args.operation == 'writeback-status':
                output = issue_writebacks.status(state, args.project, args.intent_sha256)
            elif args.operation == 'writeback-send':
                output = issue_writebacks.send(state, args.project, args.intent_sha256, args.revision, confirm=args.confirm)
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output['status'] == 'acknowledged' else 1
            elif args.operation == 'writeback-observe':
                output = issue_writebacks.observe(state, args.project, args.intent_sha256,
                    comment_id=args.comment_id, page=args.page, cursor=args.cursor)
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
            elif args.operation == "preparation":
                output = tasks.preparation(state, args.project, args.task_id)
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
            elif args.operation == "evidence":
                output = tasks.evidence(state, args.project, args.task_id, run_id=args.run_id, timeout=args.timeout)
            elif args.operation == "handoff":
                output = tasks.handoff(state, args.project, args.task_id, run_id=args.run_id,
                                       output=args.output, timeout=args.timeout)
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
                if args.operation == "prepare":
                    output = tasks.prepare(state, args.project, definition, args.revision)
                    print(json.dumps(output, ensure_ascii=False, indent=2))
                    return 0 if output['status'] == 'prepared' else 1
                elif args.operation == "preview":
                    output = tasks.preview(state, args.project, definition, args.revision)
                else:
                    output = tasks.create(state, args.project, definition, args.revision, args.preview_sha256,
                                          prepare_sha256=args.prepare_sha256)
        elif args.command == "services":
            state = State(args.home)
            if args.operation == "status":
                output = services.status(state, args.project)
            elif args.operation == "logs":
                output = services.logs(state, args.project, args.name, offset=args.offset, limit=args.bytes, stderr=args.stderr)
            else:
                output = services.control(state, args.project, args.operation, getattr(args, "names", []), args.revision,
                                          confirm=getattr(args, "confirm", False), timeout=args.timeout)
        elif args.command == "composition":
            if args.operation == "presets":
                output = workflow_definitions.presets()
            elif args.operation == "install-preset":
                output = workflow_definitions.install_preset(State(args.home), args.id)
            elif args.operation == "check":
                output = workflow_definitions.inspect_bundle(args.directory, material=args.material)
            elif args.operation == "preview":
                output = workflow_definitions.preview(resolve_home(args.home), args.id, args.version,
                                                       definition_bundles.read_json(args.grant))
            elif args.operation == "prepare-manifest":
                output = workflow_definitions.prepare_manifest(resolve_home(args.home), args.id, args.version,
                    definition_bundles.read_json(args.grant), args.directory)
            elif args.operation == "freeze-manifest":
                output = workflow_definitions.freeze_manifest(resolve_home(args.home), args.id, args.version,
                    definition_bundles.read_json(args.grant), args.preview_sha256)
            elif args.operation == "show-manifest":
                output = workflow_definitions.frozen_manifest(resolve_home(args.home), args.preview_sha256, material=args.material)
            elif args.operation in ("prepare", "prepare-from-manifest"):
                with args.task.open("rb") as source:
                    task = source.read(contracts.COMPOSITION_INPUT["properties"]["max_prompt_bytes"]["maximum"] + 1)
                output = (workflow_definitions.prepare_input(resolve_home(args.home), args.id, args.version, args.instance,
                    definition_bundles.read_json(args.grant), task, args.directory, args.max_prompt_bytes)
                    if args.operation == "prepare" else workflow_definitions.prepare_input_from_manifest(
                        args.manifest, args.instance, task, args.directory, args.max_prompt_bytes))
            elif args.operation == "verify-input":
                output = workflow_definitions.inspect_input(args.directory, material=args.material)
            elif args.operation == "verify-manifest":
                output = workflow_definitions.inspect_manifest(args.directory, material=args.material)
            elif args.operation == "check-input":
                output = agent_runs.check_input(State(args.home), args.project, args.directory,
                    backend=args.backend, model=args.model, reason=args.backend_reason, mode=args.mode, codex_config=args.codex_config)
            elif args.operation == "run-input":
                output = agent_runs.run_input(State(args.home), args.project, args.directory, args.timeout,
                    backend=args.backend, model=args.model, reason=args.backend_reason, codex_config=args.codex_config, mode=args.mode,
                    allow_one_continuation=args.allow_one_continuation)
            elif args.operation == "continue-input":
                output = agent_runs.continue_input(State(args.home), args.project, args.source_run, args.directory,
                    intent_id=args.intent, timeout=args.timeout)
            else:
                state = State(args.home)
                if args.operation == "import":
                    output = workflow_definitions.import_bundle(state, args.directory)
                elif args.operation == "revise":
                    output = workflow_definitions.revise(state, args.id, args.version, args.base_digest,
                        **_definition_revision_options(args))
                elif args.operation == "file":
                    output = workflow_definitions.read_file(state, args.id, args.version, args.base_digest, args.path,
                                                           offset=args.offset, limit=args.limit)
                elif args.operation == "list":
                    output = workflow_definitions.definitions(state)
                elif args.operation == "show":
                    output = workflow_definitions.get(state, args.id, args.version, material=args.material)
                else:
                    output = workflow_definitions.export(state, args.id, args.version, args.directory)
        elif args.command == "agent":
            if args.operation == "definition" and args.definition_operation == "check":
                output = agent_definitions.inspect_bundle(args.directory, material=args.material)
            else:
                state = State(args.home)
                if args.operation == "definition":
                    if args.definition_operation == "import":
                        output = agent_definitions.import_bundle(state, args.directory)
                    elif args.definition_operation == "revise":
                        output = agent_definitions.revise(state, args.id, args.version, args.base_digest,
                            **_definition_revision_options(args))
                    elif args.definition_operation == "file":
                        output = agent_definitions.read_file(state, args.id, args.version, args.base_digest, args.path,
                                                            offset=args.offset, limit=args.limit)
                    elif args.definition_operation == "list":
                        output = agent_definitions.definitions(state, role=args.role, specialty=args.specialty)
                    elif args.definition_operation == "show":
                        output = agent_definitions.get(state, args.id, args.version, material=args.material)
                    else:
                        output = agent_definitions.export(state, args.id, args.version, args.directory)
                elif args.operation == "runs":
                    output = agent_runs.runs(state, args.project)
                elif args.operation == "output":
                    output = agent_runs.output(state, args.project, args.id, native_history=args.native_history,
                                              offset=args.history_offset, limit=args.history_limit,
                                              revision=args.history_revision)
                else:
                    output = agent_runs.run_agent(state, args.project, args.role, args.prompt.read_text(encoding="utf-8-sig"), args.timeout, args.skill, args.recall, args.template)
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0 if args.operation != "run" or output["status"] == "succeeded" else 1
        elif args.command == "training":
            if args.operation in ("baseline-preview", "init-baseline", "runner-preview", "register-runner", "experiment-preview", "prepare"):
                document_path = args.experiment if args.operation in ("experiment-preview", "prepare") else args.document
                with document_path.open("rb") as stream:
                    raw = stream.read(1_048_577)
                if len(raw) > 1_048_576:
                    raise ValueError("Training setup source file exceeds 1 MiB")
                document = json.loads(raw)
                if args.operation in ("experiment-preview", "prepare"):
                    operation = training.preview_experiment if args.operation == "experiment-preview" else training.prepare_experiment
                    confirmation = () if args.operation == "experiment-preview" else (args.revision, args.preview_sha256)
                    output = operation(State(args.home), args.project, document, args.runner, *confirmation,
                                       max_run_seconds=args.max_run_seconds)
                else:
                    operation = {"baseline-preview": training.preview_baseline, "init-baseline": training.initialize_baseline,
                                 "runner-preview": training.preview_runner, "register-runner": training.register_runner}[args.operation]
                    confirmation = () if args.operation in ("baseline-preview", "runner-preview") else (args.revision, args.document_sha256)
                    output = operation(State(args.home), args.project, document, *confirmation)
            elif args.operation == "preparation":
                output = training.preparation(State(args.home), args.project, args.experiment_id)
            elif args.operation == "resume-prepare":
                output = training.resume_prepare(State(args.home), args.project, args.experiment_id, args.revision, args.intent_sha256)
            elif args.operation == "status":
                output = training.status(State(args.home), args.project, args.experiment_id, run_id=args.run_id, timeout=args.timeout)
            elif args.operation == "evidence":
                output = training.evidence(State(args.home), args.project, args.experiment_id, artifact=args.artifact,
                                           evidence_sha256=args.evidence_sha256, offset=args.offset, limit=args.limit)
            elif args.operation == "submission":
                output = training.submission(State(args.home), args.project, args.experiment_id)
            elif args.operation == "start":
                output = training.start(State(args.home), args.project, args.experiment_id, args.revision,
                                        args.manifest_sha256, timeout=args.timeout)
            elif args.operation == "resume-start":
                output = training.resume_start(State(args.home), args.project, args.experiment_id, args.revision,
                                               args.intent_sha256, timeout=args.timeout)
            elif args.operation == "approval":
                output = training.approval(State(args.home), args.project, args.experiment_id)
            elif args.operation == "approve":
                output = training.approve(State(args.home), args.project, args.experiment_id, args.revision,
                                           run_id=args.run_id, evidence_sha256=args.evidence_sha256,
                                           confirm=args.confirm, timeout=args.timeout)
            elif args.operation == "resume-approve":
                output = training.resume_approve(State(args.home), args.project, args.experiment_id, args.revision,
                                                  args.intent_sha256, confirm=args.confirm, timeout=args.timeout)
            elif args.operation == "cancellation":
                output = training.cancellation(State(args.home), args.project, args.experiment_id, args.request_id)
            elif args.operation == "cancel":
                output = training.cancel(State(args.home), args.project, args.experiment_id, args.request_id, args.revision,
                                         run_id=args.run_id, reason=args.reason, timeout=args.timeout)
            elif args.operation == "resume-cancel":
                output = training.resume_cancel(State(args.home), args.project, args.experiment_id, args.request_id,
                                                args.revision, args.intent_sha256, timeout=args.timeout)
            elif args.operation == "stop-status":
                output = training.stop_status(State(args.home), args.project, args.experiment_id, timeout=args.timeout)
            else:
                output = training.inspect(State(args.home), args.project, getattr(args, "experiment_id", None),
                                          limit=getattr(args, "limit", 50), after=getattr(args, "after", None))
            print(json.dumps(output, ensure_ascii=False, indent=2))
            if args.operation in ("start", "resume-start"):
                return 0 if output["status"] == "submitted" else 1
            if args.operation in ("approve", "resume-approve"):
                return 0 if output["status"] == "requested" else 1
            if args.operation in ("cancel", "resume-cancel"):
                return 0 if output["status"] in ("requested", "already_closed") else 1
            return 0
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
            elif args.operation == "catalog":
                output = memory.catalog(state, args.project)
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
                output = memory.save(state, args.project, args.text.read_bytes().decode("utf-8"),
                                     {"uri": args.source, "revision": args.source_revision}, args.id, args.revision,
                                     **({"expires_at": args.expires_at} if hasattr(args, "expires_at") else {}))
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
        if args.command == "composition" and args.operation in ("run-input", "continue-input") and output["status"] != "succeeded":
            return 1
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
