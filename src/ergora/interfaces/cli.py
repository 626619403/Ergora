from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

from ergora import __version__
import ergora.native.commands as native_commands
import ergora.native.compiler as native_compiler
import ergora.native.resources as native_resources
import ergora.training.application as training
import ergora.definitions.agents as agent_definitions
import ergora.agents.runs as agent_runs
import ergora.agents.invocation as agents
import ergora.definitions.bundles as definition_bundles
import ergora.improvement.evaluation as evaluation
import ergora.issues.application as issues
import ergora.issues.writebacks as issue_writebacks
import ergora.improvement.kernel as kernel
import ergora.improvement.memory as memory
import ergora.improvement.optimization as optimization
import ergora.configuration.projects as projects
import ergora.configuration.registrations as registrations
import ergora.improvement.research as research
import ergora.operations.services as services
import ergora.development.application as tasks
import ergora.definitions.skills as skill_assets
import ergora.improvement.skill_adoption as skills
import ergora.operations.tools as tools
import ergora.definitions.workflows as workflow_definitions
from ergora.configuration import validation as contracts
from ergora.storage.state import State, resolve_home


def _definition_edit_parsers(operations, *, workflow=False) -> None:
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
    if workflow:
        revision.add_argument("--impact", type=Path, help="Measure this draft against explicit root references and grants in JSON")
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
    review = commands.add_parser("review", help="Collect exact review material and report explicit original runs without redispatch")
    operations = review.add_subparsers(dest="operation", required=True)
    preparing = operations.add_parser("prepare", help="Read full local Git objects; never checkout, fetch or execute target code")
    preparing.add_argument("repository", type=Path)
    preparing.add_argument("--repository-id", required=True, help="Operator-asserted repository identity; not authenticated")
    preparing.add_argument("--base", required=True, help="Full target commit ID")
    preparing.add_argument("--head", required=True, help="Full candidate commit ID")
    preparing.add_argument("--comparison", choices=("merge-base", "base"), default="merge-base")
    preparing.add_argument("--requirements", type=Path, required=True)
    preparing.add_argument("--context", action="append", default=[], help="Exact repository-relative caller/config file; repeatable")
    preparing.add_argument("--evidence", action="append", type=Path, default=[], help="Operator-supplied UTF-8 check output; repeatable, not trusted automatically")
    preparing.add_argument("--max-source-bytes", type=int, default=1_000_000, help="Full Git material limit, up to 10000000; no truncation")
    preparing.add_argument("--directory", type=Path, required=True, help="New directory; never overwrites an existing packet")
    collecting = operations.add_parser("collect", help="Read one same-repository PR/MR and local exact objects; provider GET only")
    collecting.add_argument("repository", type=Path)
    collecting.add_argument("--binding", type=Path, required=True, help="GitHub/GitLab binding JSON; credentials only through token_env")
    collecting.add_argument("--number", required=True, help="Repository PR number or project MR iid")
    collecting.add_argument("--requirements", type=Path, required=True)
    collecting.add_argument("--context", action="append", default=[], help="Exact repository-relative caller/config file; repeatable")
    collecting.add_argument("--evidence", action="append", type=Path, default=[], help="Operator-supplied UTF-8 checks; repeatable, unverified")
    collecting.add_argument("--max-source-bytes", type=int, default=1_000_000, help="Complete Git material limit, up to 10000000")
    collecting.add_argument("--directory", type=Path, required=True, help="New source directory; never replaces an existing one")
    source_read = operations.add_parser("read-source", help="Read and verify a complete saved PR/MR source offline")
    source_read.add_argument("directory", type=Path)
    source_read.add_argument("--sha256", help="Independently obtained source.json SHA256")
    for name in ("prepare-input", "verify-input"):
        operation = operations.add_parser(name, help="Bind a complete review source to one original read-only leaf input")
        operation.add_argument("source", type=Path)
        operation.add_argument("--source-kind", choices=("local", "external"), required=True)
        operation.add_argument("--source-sha256", required=True)
        operation.add_argument("--manifest-digest", required=True)
        if name == "prepare-input":
            operation.add_argument("--manifest", type=Path, required=True)
            operation.add_argument("--instance", required=True)
            operation.add_argument("--max-prompt-bytes", type=int, required=True)
            operation.add_argument("--directory", type=Path, required=True)
        else:
            operation.add_argument("--input", type=Path, required=True)
            operation.add_argument("--input-digest", required=True)
    for name in ("verify", "read"):
        operation = operations.add_parser(name, help="Offline integrity check; does not authenticate Git origin or checks")
        operation.add_argument("directory", type=Path)
        operation.add_argument("--sha256", help="Independently obtained packet.json SHA256")
    reporting = operations.add_parser("report", help="Read every declared reviewer against explicit source, manifest and original run IDs")
    reporting.add_argument("project")
    reporting.add_argument("source", type=Path)
    reporting.add_argument("--source-kind", choices=("local", "external"), required=True)
    reporting.add_argument("--source-sha256", required=True)
    reporting.add_argument("--manifest", type=Path, required=True)
    reporting.add_argument("--manifest-digest", required=True)
    reporting.add_argument("--runs", type=Path, required=True, help="JSON object mapping exact instance paths to original run IDs; omitted members stay incomplete")
    reporting.add_argument("--max-result-bytes", type=int, default=8_388_608)
    reporting.add_argument("--format", choices=("json", "markdown"), default="json")
    handoff = commands.add_parser("handoff", help="Verify portable evidence without services or local state")
    operations = handoff.add_subparsers(dest="operation", required=True)
    for name in ("verify", "read"):
        operation = operations.add_parser(name)
        operation.add_argument("path", type=Path)
        operation.add_argument("--sha256", help="Independently obtained whole-packet SHA256")
        if name == "read":
            operation.add_argument("--selection", type=Path, help="JSON array of exact job_id/name pairs; omitted reads the complete index")
    retrospective = commands.add_parser("retrospective", help="Propose improvements; explicitly confirm exact project-document edits separately")
    operations = retrospective.add_subparsers(dest="operation", required=True)
    document = operations.add_parser("prepare-document", help="Freeze an explicit correction and one existing project Markdown document")
    document.add_argument("project")
    document.add_argument("--document", required=True, help="Exact project-relative existing Markdown path")
    document.add_argument("--correction", type=Path, required=True, help="Complete operator-submitted UTF-8 correction")
    document.add_argument("--source", required=True, help="Source description; imported text is not authenticated human consent")
    document.add_argument("--revision", type=int, required=True)
    document.add_argument("--manifest", type=Path, required=True)
    document.add_argument("--instance", required=True)
    document.add_argument("--directory", type=Path, required=True)
    document.add_argument("--max-prompt-bytes", type=int, required=True)
    document.add_argument("--max-material-bytes", type=int, default=1_048_576)
    document.add_argument("--parent-preview", type=Path, help="Original preview when editing or superseding a prior proposal")
    for name in ("check-document", "preview-document"):
        document = operations.add_parser(name, help="Inspect full document diff offline" if name == "check-document" else
                                         "Seal one exact candidate at its original control authority; no document write")
        if name == "preview-document":
            document.add_argument("project")
            document.add_argument("--revision", type=int, required=True)
        document.add_argument("input", type=Path)
        document.add_argument("result", type=Path)
        document.add_argument("--input-digest", required=True)
        document.add_argument("--result-sha256", required=True)
    for name in ("apply-document", "withdraw-document", "document-status"):
        document = operations.add_parser(name, help="Use the original authority-owned document candidate; never recreate a missing slot")
        document.add_argument("project")
        document.add_argument("preview", type=Path, help="Saved complete sealed preview")
        if name == "withdraw-document":
            document.add_argument("--reason", required=True)
        if name == "apply-document":
            document.add_argument("--revision", type=int, required=True)
            document.add_argument("--candidate-digest", required=True)
            document.add_argument("--base-sha256", required=True)
            document.add_argument("--scope-sha256", required=True)
            document.add_argument("--confirm", action="store_true", help="Explicit decision for these exact bytes/scope; not general task agreement")
    for name in ("prepare", "prepare-memory", "prepare-workflow"):
        preparing = operations.add_parser(name, help="Freeze complete evidence and the selected baseline for a proposal-producing leaf")
        preparing.add_argument("project")
        preparing.add_argument("packet", type=Path)
        preparing.add_argument("--selection", type=Path, required=True)
        preparing.add_argument("--packet-sha256", required=True)
        if name == "prepare":
            preparing.add_argument("--skill", required=True)
            preparing.add_argument("--digest", required=True)
            preparing.add_argument("--head-revision", type=int, required=True)
        elif name == "prepare-memory":
            target = preparing.add_mutually_exclusive_group(required=True)
            target.add_argument("--new-memory", action="store_true")
            target.add_argument("--memory-id")
            preparing.add_argument("--revision", type=int, default=0, help="Exact current memory revision; zero for explicit creation")
        else:
            preparing.add_argument("--target-manifest", type=Path, required=True)
            preparing.add_argument("--target-digest", required=True, help="Exact complete target manifest digest")
            preparing.add_argument("--next-version", required=True, help="Explicit new immutable root version")
        preparing.add_argument("--objective", type=Path, required=True)
        preparing.add_argument("--manifest", type=Path, required=True)
        preparing.add_argument("--instance", required=True)
        preparing.add_argument("--directory", type=Path, required=True)
        preparing.add_argument("--max-prompt-bytes", type=int, required=True)
    for name in ("check", "check-memory", "check-workflow"):
        checking = operations.add_parser(name, help="Check a structured result (up to 8 MiB) against its frozen input, offline")
        checking.add_argument("input", type=Path)
        checking.add_argument("result", type=Path)
        checking.add_argument("--result-sha256")
    for name in ("export", "export-memory", "export-workflow"):
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
    legacy = commands.add_parser("reference", help="Inspect the reference or prepare versioned native training source")
    legacy.add_argument("operation", choices=["info", "verify", "executor", "prepare-training"])
    legacy.add_argument("--installation", type=Path, help="Existing v2.2 reference installation (executor only)")
    legacy.add_argument("--request", type=Path, help="Execute one envelope instead of watching the reference queue")
    legacy.add_argument("--project", help="Use a unified project's saved execution directories")
    legacy.add_argument("--protocol", choices=native_resources.TRAINING_PROTOCOLS, help="Exact native source protocol (prepare-training only)")
    legacy.add_argument("--directory", type=Path, help="New native source directory (prepare-training only)")
    templates = commands.add_parser("templates", help="List or copy a reference workflow template")
    operations = templates.add_subparsers(dest="operation", required=True)
    operations.add_parser("list")
    copy = operations.add_parser("copy")
    copy.add_argument("kind", choices=native_resources.TEMPLATES)
    copy.add_argument("destination", type=Path)
    contract = operations.add_parser("agents")
    contract.add_argument("kind", choices=native_resources.TEMPLATES)
    workflow = commands.add_parser("workflow", add_help=False, help="Run the existing portable-contract compiler")
    workflow.add_argument("arguments", nargs=argparse.REMAINDER)
    composition = commands.add_parser("composition", help="Check nested definitions, prepare inputs or explicitly invoke a leaf")
    operations = composition.add_subparsers(dest="operation", required=True)
    _definition_edit_parsers(operations, workflow=True)
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
    inspection = operations.add_parser("inspect-run", help="Read an exact original composition run, complete input and result offline")
    inspection.add_argument("project")
    inspection.add_argument("id")
    inspection.add_argument("--max-result-bytes", type=int, default=8_388_608, help="Complete result capacity; excess is reported without truncation")
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
    suggestions = operations.add_parser("correction-suggestions", help="Set suggestions for new native sessions; changes the project revision")
    suggestions.add_argument("id")
    suggestions.add_argument("--enabled", choices=("true", "false"), required=True)
    suggestions.add_argument("--revision", type=int, required=True)
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
    amendment = operations.add_parser("preview-amendment", help="Compare a revised successor with the original task and closure evidence")
    amendment.add_argument("project")
    amendment.add_argument("task_id")
    amendment.add_argument("--run-id", required=True)
    amendment.add_argument("--definition", type=Path, required=True)
    amendment.add_argument("--revision", type=int, required=True)
    amendment.add_argument("--change", required=True)
    amendment.add_argument("--timeout", type=int, default=20)
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
    design_source = operations.add_parser("design", help="Store/read complete inspection-only design sources; grants no approval")
    source_operations = design_source.add_subparsers(dest="source_operation", required=True)
    for name in ("inspect", "publish", "respond", "operation", "resume"):
        command = source_operations.add_parser(name)
        command.add_argument("project")
        command.add_argument("task_id")
        command.add_argument("--timeout", type=int, default=20)
        if name in ("inspect", "publish", "respond"):
            command.add_argument("--run-id", required=True)
            command.add_argument("--plan-sha256", required=True)
        if name in ("publish", "respond"):
            command.add_argument("--operation-id", required=True)
            command.add_argument("--parent-record-sha256", required=True)
            command.add_argument("--body-file", type=Path, required=True)
        if name in ("publish", "respond", "resume"):
            command.add_argument("--revision", type=int, required=True)
        if name in ("operation", "resume"):
            command.add_argument("operation_id")
        if name == "resume":
            command.add_argument("--intent-sha256", required=True)
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
    prioritize = operations.add_parser("prioritize-work", help="Prioritize one pending unit in the original approved work queue")
    prioritize.add_argument("project")
    prioritize.add_argument("task_id")
    prioritize.add_argument("work_unit_id")
    prioritize.add_argument("--revision", type=int, required=True)
    prioritize.add_argument("--run-id", required=True)
    prioritize.add_argument("--plan-sha256", required=True)
    prioritize.add_argument("--decision-id", required=True)
    prioritize.add_argument("--confirm", action="store_true", required=True)
    prioritize.add_argument("--timeout", type=int, default=20)
    priority_status = operations.add_parser("work-priority", help="Read the original work priority outcome without another send")
    priority_status.add_argument("project")
    priority_status.add_argument("task_id")
    priority_status.add_argument("decision_id")
    priority_status.add_argument("--run-id", required=True)
    priority_status.add_argument("--timeout", type=int, default=20)
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
    run.add_argument("--template", choices=native_resources.TEMPLATES, help="Require the selected template role's structured artifacts (not formal acceptance)")
    run.add_argument("--session-intent", help="Save a native session under this stable intent; requires --revision")
    run.add_argument("--revision", type=int, help="Current project revision for a new persistent session")
    run.add_argument("--codex-config", type=Path, help="Trusted native configuration to freeze once when starting a session")
    for name in ("sessions", "session"):
        listing = operations.add_parser(name, help="Read original project sessions without invoking an Agent")
        listing.add_argument("project")
        if name == "session":
            listing.add_argument("id")
        else:
            listing.add_argument("--intent", help="Observe the exact original birth intent without invoking an Agent")
        listing.add_argument("--after", type=int, default=0)
        listing.add_argument("--limit", type=int, default=20)
    continuation = operations.add_parser("continue", help="Continue an exact project session with a new prompt")
    continuation.add_argument("project")
    continuation.add_argument("id")
    continuation.add_argument("--parent", required=True, help="Latest original run selected from session history")
    continuation.add_argument("--prompt", type=Path, required=True)
    continuation.add_argument("--revision", type=int, required=True)
    continuation.add_argument("--intent", required=True, help="Stable intent; a lost reply must be observed before any new work")
    continuation.add_argument("--timeout", type=int, default=300)
    stop = operations.add_parser("stop", help="Request stop of one exact session turn, then inspect its original record")
    stop.add_argument("project")
    stop.add_argument("id")
    stop.add_argument("--run", required=True)
    stop.add_argument("--intent", required=True)
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
    for name in ("search-preview", "search-prepare"):
        search = operations.add_parser(name, help="Preview or prepare finite configuration candidates; never execute training")
        search.add_argument("project")
        search.add_argument("--request", type=Path, required=True)
        if name == "search-prepare":
            search.add_argument("--revision", type=int, required=True)
            search.add_argument("--preview-sha256", required=True)
            search.add_argument("--directory", type=Path, required=True)
    reading = operations.add_parser("search-read", help="Verify a saved search preparation offline; never query or execute training")
    reading.add_argument("directory", type=Path)
    reading.add_argument("--sha256", help="Pin the saved search.json raw SHA256")
    rounds = operations.add_parser("rounds-create", help="Freeze selected original experiment observations in a new advisory index")
    rounds.add_argument("project")
    rounds.add_argument("--definition", type=Path, required=True)
    rounds.add_argument("--directory", type=Path, required=True)
    rounds.add_argument("--previous", type=Path, help="Extend this frozen index without observing its old rounds again")
    rounds.add_argument("--previous-sha256", help="Required exact SHA256 of the previous index")
    reading = operations.add_parser("rounds-read", help="Verify and read an index offline; never query, execute or approve")
    reading.add_argument("directory", type=Path)
    reading.add_argument("--sha256", help="Pin the expected complete index SHA256")
    cycle = operations.add_parser("cycle-create", help="Freeze a finite selection and budget policy; never dispatch training")
    cycle.add_argument("project")
    cycle.add_argument("--definition", type=Path, required=True)
    cycle.add_argument("--directory", type=Path, required=True)
    cycle = operations.add_parser("cycle-read", help="Read a complete saved selection offline; never re-admit or start a budget")
    cycle.add_argument("directory", type=Path)
    cycle.add_argument("--sha256", help="Pin the complete saved cycle SHA256")
    cycle = operations.add_parser("cycle-authorize", help="Start one immutable local training budget, then check admissions; never dispatch")
    cycle.add_argument("project")
    cycle.add_argument("cycle_id")
    cycle.add_argument("--directory", type=Path, required=True, help="Original input directory; retries use the saved complete input")
    cycle.add_argument("--sha256", required=True, help="Exact complete input SHA256")
    cycle.add_argument("--revision", type=int, required=True)
    cycle.add_argument("--confirm", action="store_true", help="Confirm starting the nonrenewable budget before live checks")
    cycle = operations.add_parser("cycle-authorize-controller", help="Confirm one finite ordered controller and its nonrenewable budget")
    cycle.add_argument("project")
    cycle.add_argument("cycle_id")
    cycle.add_argument("--directory", type=Path, required=True)
    cycle.add_argument("--sha256", required=True)
    cycle.add_argument("--revision", type=int, required=True)
    cycle.add_argument("--confirm", action="store_true")
    cycle.add_argument("--execute-selected", action="store_true", help="Explicitly consent to executing the exact selected candidates")
    for action, description in (
            ('status', 'Read saved parent intent/attempt/receipt without querying or dispatching'),
            ('prepare', 'Freeze the original parent intent without dispatch'),
            ('submit', 'Submit the prepared parent once, preserving an uncertain original attempt'),
            ('reconcile', 'Observe only the original parent after a lost reply; never resend'),
            ('stop', 'Publish the local stop veto; this does not certify executor subtree termination')):
        cycle = operations.add_parser('cycle-controller-' + action, help=description)
        cycle.add_argument('project')
        cycle.add_argument('cycle_id')
        cycle.add_argument('--authorization-sha256', required=True)
        if action == 'prepare':
            cycle.add_argument('--revision', type=int, required=True)
        elif action == 'stop':
            cycle.add_argument('--reason', required=True)
    cycle = operations.add_parser("cycle-status", help="Read the original local authorization and deadline; never re-admit or dispatch")
    cycle.add_argument("project")
    cycle.add_argument("cycle_id")
    cycle.add_argument("--authorization-sha256", help="Pin the original authorization canonical SHA256")
    cycle = operations.add_parser("cycle-start", help="Bind one selected experiment to its original budget and native start")
    cycle.add_argument("project")
    cycle.add_argument("cycle_id")
    cycle.add_argument("experiment_id")
    cycle.add_argument("--authorization-sha256", required=True)
    cycle.add_argument("--revision", type=int, required=True)
    operation = operations.add_parser('execution', help='Read saved execution and stop records offline; never launch or restart')
    operation.add_argument('project')
    operation.add_argument('experiment_id')
    operation = operations.add_parser('execute', help='Confirm one submitted job for its original capable budget owner')
    operation.add_argument('project')
    operation.add_argument('experiment_id')
    operation.add_argument('--revision', type=int, required=True)
    operation.add_argument('--intent-sha256', required=True)
    operation.add_argument('--run-id', required=True)
    operation.add_argument('--request-sha256', required=True, help='SHA256 of the complete original native request bytes')
    operation.add_argument('--confirm', action='store_true', required=True)
    operation.add_argument('--timeout', type=int, default=20)
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
    evidence.add_argument("--screen-result-sha256", help="Exact observed screen result digest; use with a screen artifact")
    evidence.add_argument("--offset", type=int, default=0, help="Unicode character offset in the selected text artifact")
    evidence.add_argument("--limit", type=int, default=12_000, help="Text window size, at most 65,536 characters")
    live = operations.add_parser("status", help="Query the original workflow; never start, cancel or approve an experiment")
    live.add_argument("project")
    live.add_argument("experiment_id")
    live.add_argument("--run-id", help="Pin the query to an existing native run ID")
    live.add_argument("--timeout", type=int, default=20)
    recovery_operations = []
    for name in ("submission", "check-start", "start", "resume-start"):
        operation = operations.add_parser(name)
        if name in ("submission", "resume-start"):
            recovery_operations.append(operation)
        operation.add_argument("project")
        operation.add_argument("experiment_id")
        if name == "check-start":
            operation.add_argument("--manifest-sha256", required=True)
        elif name != "submission":
            operation.add_argument("--revision", type=int, required=True)
            operation.add_argument("--manifest-sha256" if name == "start" else "--intent-sha256", required=True)
            operation.add_argument("--timeout", type=int, default=20)
    fence = operations.add_parser("fence-start", help="Confirm a local experiment fence: suppress future jobs/release and possibly runner/archive; never certify run ownership or stop")
    fence.add_argument("project")
    fence.add_argument("experiment_id")
    fence.add_argument("--revision", type=int, required=True)
    fence.add_argument("--manifest-sha256", required=True)
    fence.add_argument("--confirm", action="store_true", required=True)
    fence.add_argument("--timeout", type=int, default=20)
    recovery_operations.append(fence)
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
        recovery_operations.append(operation)
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
    for operation in recovery_operations:
        operation.add_argument("--original-registration", help="Original operation ID from this control home's registration journal")
        operation.add_argument("--registration-intent-sha256", help="Exact canonical intent SHA from that operation's published result")
        if operation is not fence:
            operation.add_argument("--confirm", action="store_true", help="Confirm recovery in the selected original registration")
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
    pool = commands.add_parser("gpu-pool", help="Local cooperating GPU resource decisions; does not authorize execution")
    pool_operations = pool.add_subparsers(dest="operation", required=True)
    for name in ("inspect", "request", "cancel", "release", "reconcile", "close"):
        operation = pool_operations.add_parser(name)
        operation.add_argument("--config", required=True)
        if name == "request":
            operation.add_argument("--request", required=True)
        if name == "cancel":
            operation.add_argument("--request-id", required=True)
            operation.add_argument("--origin", required=True)
        if name in ("release", "reconcile"):
            operation.add_argument("--lease-id", required=True)
        if name == "release":
            operation.add_argument("--proof", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    if os.name == "nt":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["workflow"]:
        return native_compiler.workflow(argv[1:])
    args = parser().parse_args(argv)
    try:
        if args.command == "gpu-pool":
            from ergora.runtime import gpu_pool as local_gpu_pool

            def document(path):
                return local_gpu_pool._decode(local_gpu_pool._read(Path(path), local_gpu_pool.FRAME_LIMIT))

            pool = local_gpu_pool.LocalGpuPool.connect(document(args.config))
            if args.operation == "request":
                output = pool.request(document(args.request))
            elif args.operation == "cancel":
                output = pool.cancel(args.request_id, document(args.origin))
            elif args.operation == "release":
                output = pool.release(args.lease_id, document(args.proof))
            elif args.operation == "reconcile":
                output = pool.reconcile(args.lease_id)
            else:
                output = getattr(pool, args.operation)()
        elif args.command == "review":
            import ergora.development.review.packets as review_packets

            if args.operation in ("prepare-input", "verify-input", "report"):
                import ergora.development.review.requests as review_requests

                if args.operation == "prepare-input":
                    output = review_requests.prepare(args.source, source_kind=args.source_kind, source_sha256=args.source_sha256,
                        manifest=args.manifest, manifest_digest=args.manifest_digest, instance=args.instance,
                        destination=args.directory, max_prompt_bytes=args.max_prompt_bytes)
                elif args.operation == "verify-input":
                    output = review_requests.verify(args.input, input_digest=args.input_digest, source=args.source,
                        source_kind=args.source_kind, source_sha256=args.source_sha256, manifest_digest=args.manifest_digest)
                else:
                    output = review_requests.report(State(args.home), args.project, args.source,
                        source_kind=args.source_kind, source_sha256=args.source_sha256, manifest=args.manifest,
                        manifest_digest=args.manifest_digest, runs=definition_bundles.read_json(args.runs),
                        max_result_bytes=args.max_result_bytes)
                    if args.format == "markdown":
                        print(review_requests.markdown(output), end="")
                        return 0
            elif args.operation in ("collect", "read-source"):
                import ergora.development.review.sources as review_sources

                if args.operation == "collect":
                    output = review_sources.collect(definition_bundles.read_json(args.binding), args.number, args.repository,
                        requirements=args.requirements, destination=args.directory, context_paths=args.context,
                        evidence=args.evidence, max_source_bytes=args.max_source_bytes)
                else:
                    output = review_sources.read(args.directory, sha256=args.sha256)
            elif args.operation == "prepare":
                output = review_packets.prepare(args.repository, repository_id=args.repository_id, base=args.base,
                    head=args.head, requirements=args.requirements, destination=args.directory,
                    context_paths=args.context, evidence=args.evidence, comparison=args.comparison,
                    max_source_bytes=args.max_source_bytes)
            else:
                operation = review_packets.read if args.operation == "read" else review_packets.verify
                output = operation(args.directory, sha256=args.sha256)
        elif args.command == "handoff":
            import ergora.development.handoff as handoff

            output = (handoff.verify(args.path, sha256=args.sha256) if args.operation == "verify" else
                      handoff.evidence(args.path, definition_bundles.read_json(args.selection) if args.selection else None,
                                       sha256=args.sha256))
        elif args.command == "retrospective":
            import ergora.improvement.retrospectives as retrospectives

            if args.operation in ("prepare-document", "check-document", "preview-document", "apply-document",
                                  "withdraw-document", "document-status"):
                import ergora.improvement.document_corrections as corrections

                if args.operation == "prepare-document":
                    with args.correction.open('rb') as stream:
                        raw = stream.read(min(max(args.max_material_bytes, 0), corrections.MAX_MATERIAL_BYTES) + 1)
                    output = corrections.prepare(State(args.home), args.project, args.document, raw,
                        source=args.source, revision=args.revision, manifest=args.manifest, instance=args.instance,
                        destination=args.directory, max_prompt_bytes=args.max_prompt_bytes,
                        max_material_bytes=args.max_material_bytes,
                        parent_preview=corrections.read_preview(args.parent_preview) if args.parent_preview else None)
                elif args.operation == "check-document":
                    output = corrections.check(args.input, args.result, result_sha256=args.result_sha256,
                                               input_digest=args.input_digest)
                elif args.operation == "preview-document":
                    output = corrections.preview(State(args.home), args.project, args.input, args.result,
                        revision=args.revision, result_sha256=args.result_sha256, input_digest=args.input_digest)
                else:
                    state, value = State(args.home), corrections.read_preview(args.preview)
                    if args.operation == "apply-document":
                        output = corrections.apply(state, args.project, value, revision=args.revision,
                            candidate_digest=args.candidate_digest, base_sha256=args.base_sha256,
                            scope_sha256=args.scope_sha256, confirm=args.confirm)
                    elif args.operation == "withdraw-document":
                        output = corrections.withdraw(state, args.project, value, reason=args.reason)
                    else:
                        output = corrections.status(state, args.project, value)
            elif args.operation == "check":
                output = retrospectives.check(args.input, args.result, result_sha256=args.result_sha256)
            elif args.operation == "check-memory":
                output = retrospectives.check_memory(args.input, args.result, result_sha256=args.result_sha256)
            elif args.operation == "check-workflow":
                output = retrospectives.check_workflow(args.input, args.result, result_sha256=args.result_sha256)
            elif args.operation == "export":
                output = retrospectives.export(args.input, args.result, args.destination,
                    result_sha256=args.result_sha256, candidate_digest=args.candidate_digest)
            elif args.operation == "export-memory":
                output = retrospectives.export_memory(args.input, args.result, args.destination,
                    result_sha256=args.result_sha256, candidate_digest=args.candidate_digest)
            elif args.operation == "export-workflow":
                output = retrospectives.export_workflow(args.input, args.result, args.destination,
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
                elif args.operation == "prepare-workflow":
                    output = retrospectives.prepare_workflow(State(args.home), args.project, args.packet,
                        definition_bundles.read_json(args.selection), target_manifest=args.target_manifest,
                        target_digest=args.target_digest, next_version=args.next_version, **options)
                else:
                    output = retrospectives.prepare(State(args.home), args.project, args.packet,
                        definition_bundles.read_json(args.selection), name=args.skill, digest=args.digest,
                        head_revision=args.head_revision, **options)
        elif args.command == "state":
            import ergora.operations.backups as backups

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
            if args.operation == "prepare-training":
                if not args.protocol or args.directory is None:
                    raise ValueError("Source preparation requires --protocol and a new --directory")
                output = native_resources.prepare_training(args.directory, protocol=args.protocol)
            elif args.operation == "executor":
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
                output = native_commands.executor(args.installation, State(args.home).root, args.request)
            else:
                output = native_resources.verify() if args.operation == "verify" else native_resources.info()
        elif args.command == "serve":
            try:
                import uvicorn
                from ergora.interfaces.web import create_app
            except ModuleNotFoundError as error:
                raise ValueError("Install ergora[web] to start the graphical console") from error
            uvicorn.run(create_app(args.home), host="127.0.0.1", port=args.port, proxy_headers=False)
            return 0
        elif args.command == "templates":
            if args.operation == "list":
                output = {"templates": list(native_resources.TEMPLATES)}
            elif args.operation == "agents":
                output = native_resources.agent_contract(args.kind)
            else:
                output = native_resources.copy_template(args.kind, args.destination)
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
            elif args.operation == "correction-suggestions":
                output = projects.set_correction_suggestions(state, args.id, args.enabled == "true", args.revision)
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
            elif args.operation == "preview-amendment":
                definition = json.loads(args.definition.read_text(encoding="utf-8-sig"))
                output = tasks.preview_amendment(state, args.project, args.task_id, definition, args.revision,
                    run_id=args.run_id, change=args.change, timeout=args.timeout)
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output['status'] == 'ready' else 1
            elif args.operation == "design":
                if args.source_operation == "inspect":
                    output = tasks.design(state, args.project, args.task_id, run_id=args.run_id,
                                          plan_sha256=args.plan_sha256, timeout=args.timeout)
                elif args.source_operation in ("publish", "respond"):
                    with args.body_file.open('rb') as stream:
                        raw = stream.read(16 * 1024 * 1024 + 1)
                    if len(raw) > 16 * 1024 * 1024:
                        raise ValueError('Design source body-file exceeds its complete intent boundary')
                    body = json.loads(raw.decode('utf-8-sig'))
                    writer = tasks.publish_design if args.source_operation == "publish" else tasks.record_design_response
                    output = writer(state, args.project, args.task_id, args.operation_id, args.revision, body,
                        parent_record_sha256=args.parent_record_sha256, run_id=args.run_id,
                        plan_sha256=args.plan_sha256, timeout=args.timeout)
                elif args.source_operation == "operation":
                    output = tasks.design_operation(state, args.project, args.task_id, args.operation_id, timeout=args.timeout)
                else:
                    output = tasks.resume_design_operation(state, args.project, args.task_id, args.operation_id,
                        args.revision, args.intent_sha256, timeout=args.timeout)
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
            elif args.operation == "prioritize-work":
                output = tasks.prioritize_work_unit(state, args.project, args.task_id, args.work_unit_id, args.revision,
                    run_id=args.run_id, plan_sha256=args.plan_sha256, decision_id=args.decision_id,
                    confirm=args.confirm, timeout=args.timeout)
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["status"] == "applied" else 1
            elif args.operation == "work-priority":
                output = tasks.work_priority(state, args.project, args.task_id, args.decision_id,
                                             run_id=args.run_id, timeout=args.timeout)
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
                    print(json.dumps(output, ensure_ascii=False, indent=2))
                    return 1 if output["route_admission"]["status"] == "blocked" else 0
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
            elif args.operation == "revise" and args.impact:
                options = _definition_revision_options(args)
                if options.pop("publish"):
                    raise ValueError("--impact requires --check or --preview-resources")
                output = workflow_definitions.revision_impact(resolve_home(args.home), args.id, args.version,
                    args.base_digest, selection=definition_bundles.read_json(args.impact), **options)
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 0 if output["impact"]["status"] == "checked" else 1
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
                    backend=args.backend, model=args.model, reason=args.backend_reason, codex_config=args.codex_config, mode=args.mode)
            elif args.operation == "inspect-run":
                output = agent_runs.inspect_run(State(args.home), args.project, args.id, max_result_bytes=args.max_result_bytes)
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
                elif args.operation == "sessions":
                    output = agent_runs.sessions(state, args.project, after=args.after, limit=args.limit, intent_id=args.intent)
                elif args.operation == "session":
                    output = agent_runs.inspect_session(state, args.project, args.id, after=args.after, limit=args.limit)
                elif args.operation == "continue":
                    output = agent_runs.continue_session(state, args.project, args.id, args.parent,
                        args.prompt.read_text(encoding="utf-8-sig"), expected_revision=args.revision,
                        intent_id=args.intent, timeout=args.timeout)
                elif args.operation == "stop":
                    output = agent_runs.stop_session(state, args.project, args.id, args.run, intent_id=args.intent)
                elif args.operation == "runs":
                    output = agent_runs.runs(state, args.project)
                elif args.operation == "output":
                    output = agent_runs.output(state, args.project, args.id, native_history=args.native_history,
                                              offset=args.history_offset, limit=args.history_limit,
                                              revision=args.history_revision)
                else:
                    output = agent_runs.run_agent(state, args.project, args.role, args.prompt.read_text(encoding="utf-8-sig"), args.timeout, args.skill, args.recall, args.template,
                        session_intent=args.session_intent, expected_revision=args.revision, codex_config=args.codex_config)
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0 if args.operation not in ("run", "continue") or output["status"] == "succeeded" else 1
        elif args.command == "training":
            original_operation = getattr(args, "original_registration", None)
            registration_digest = getattr(args, "registration_intent_sha256", None)
            recovery = None
            if (original_operation is not None or registration_digest is not None
                    or (args.operation != "fence-start" and hasattr(args, "original_registration") and args.confirm)):
                recovery = {"operation_id": original_operation, "intent_sha256": registration_digest, "confirm": args.confirm}
            if args.operation in ("search-preview", "search-prepare", "search-read"):
                import ergora.training.search as training_search

                if args.operation == "search-read":
                    output = training_search.read(args.directory, sha256=args.sha256)
                else:
                    document = training_search.read_request(args.request)
                    if args.operation == "search-preview":
                        output = training_search.preview(State(args.home), args.project, document)
                    else:
                        output = training_search.prepare(State(args.home), args.project, document, args.revision,
                                                         args.preview_sha256, args.directory)
            elif args.operation in ("baseline-preview", "init-baseline", "runner-preview", "register-runner", "experiment-preview", "prepare", "rounds-create", "cycle-create"):
                document_path = (args.definition if args.operation in ("rounds-create", "cycle-create") else
                                 args.experiment if args.operation in ("experiment-preview", "prepare") else args.document)
                with document_path.open("rb") as stream:
                    raw = stream.read(1_048_577)
                if len(raw) > 1_048_576:
                    raise ValueError("Training setup source file exceeds 1 MiB")
                if args.operation in ("rounds-create", "cycle-create"):
                    cycle_request = args.operation == "cycle-create"
                    document = definition_bundles.parse_json(raw.decode('utf-8-sig'),
                        'training cycle request' if cycle_request else 'training round request',
                        finite=cycle_request, bounded=cycle_request)
                else:
                    document = json.loads(raw)
                if args.operation == "cycle-create":
                    import ergora.training.cycles as training_cycles

                    output = training_cycles.create(State(args.home), args.project, document, args.directory)
                elif args.operation == "rounds-create":
                    import ergora.training.rounds as training_rounds

                    output = training_rounds.create(State(args.home), args.project, document, args.directory,
                                                   previous=args.previous, previous_sha256=args.previous_sha256)
                elif args.operation in ("experiment-preview", "prepare"):
                    operation = training.preview_experiment if args.operation == "experiment-preview" else training.prepare_experiment
                    confirmation = () if args.operation == "experiment-preview" else (args.revision, args.preview_sha256)
                    output = operation(State(args.home), args.project, document, args.runner, *confirmation,
                                       max_run_seconds=args.max_run_seconds)
                else:
                    operation = {"baseline-preview": training.preview_baseline, "init-baseline": training.initialize_baseline,
                                 "runner-preview": training.preview_runner, "register-runner": training.register_runner}[args.operation]
                    confirmation = () if args.operation in ("baseline-preview", "runner-preview") else (args.revision, args.document_sha256)
                    output = operation(State(args.home), args.project, document, *confirmation)
            elif args.operation == "cycle-read":
                import ergora.training.cycles as training_cycles

                output = training_cycles.read(args.directory, sha256=args.sha256)
            elif args.operation == "cycle-authorize":
                import ergora.training.cycles as training_cycles

                output = training_cycles.authorize(State(args.home), args.project, args.cycle_id, args.directory,
                                                   args.sha256, args.revision, confirm=args.confirm)
            elif args.operation == 'cycle-authorize-controller':
                import ergora.training.cycles as training_cycles

                output = training_cycles.authorize_controller(State(args.home), args.project, args.cycle_id, args.directory,
                    args.sha256, args.revision, confirm=args.confirm, execute_selected=args.execute_selected)
            elif args.operation.startswith('cycle-controller-'):
                import ergora.training.cycles as training_cycles

                action = args.operation.removeprefix('cycle-controller-')
                selected = ({'expected_revision': args.revision} if action == 'prepare' else
                            {'reason': args.reason} if action == 'stop' else {})
                output = training_cycles.controller(State(args.home), args.project, args.cycle_id,
                    args.authorization_sha256, action, **selected)
            elif args.operation == "cycle-status":
                import ergora.training.cycles as training_cycles

                output = training_cycles.status(State(args.home), args.project, args.cycle_id,
                                                authorization_sha256=args.authorization_sha256)
            elif args.operation == "cycle-start":
                import ergora.training.cycles as training_cycles

                output = training_cycles.start(State(args.home), args.project, args.cycle_id, args.experiment_id,
                                               args.authorization_sha256, args.revision)
            elif args.operation == "rounds-read":
                import ergora.training.rounds as training_rounds

                output = training_rounds.read(args.directory, sha256=args.sha256)
            elif args.operation == "preparation":
                output = training.preparation(State(args.home), args.project, args.experiment_id)
            elif args.operation == "resume-prepare":
                output = training.resume_prepare(State(args.home), args.project, args.experiment_id, args.revision, args.intent_sha256)
            elif args.operation == "status":
                output = training.status(State(args.home), args.project, args.experiment_id, run_id=args.run_id, timeout=args.timeout)
            elif args.operation == "evidence":
                output = training.evidence(State(args.home), args.project, args.experiment_id, artifact=args.artifact,
                                           evidence_sha256=args.evidence_sha256, screen_result_sha256=args.screen_result_sha256, offset=args.offset, limit=args.limit)
            elif args.operation == "submission":
                output = training.submission(State(args.home), args.project, args.experiment_id, original_registration=recovery)
            elif args.operation == "check-start":
                output = training.check_start(State(args.home), args.project, args.experiment_id, args.manifest_sha256)
            elif args.operation == "fence-start":
                output = training.fence_start(State(args.home), args.project, args.experiment_id, args.revision,
                                              args.manifest_sha256, confirm=args.confirm, timeout=args.timeout,
                                              original_registration=recovery)
            elif args.operation == "start":
                output = training.start(State(args.home), args.project, args.experiment_id, args.revision,
                                        args.manifest_sha256, timeout=args.timeout)
            elif args.operation == 'execution':
                output = training.execution(State(args.home), args.project, args.experiment_id)
            elif args.operation == 'execute':
                output = training.execute(State(args.home), args.project, args.experiment_id, args.revision,
                    args.intent_sha256, args.run_id, args.request_sha256, confirm=args.confirm, timeout=args.timeout)
            elif args.operation == "resume-start":
                output = training.resume_start(State(args.home), args.project, args.experiment_id, args.revision,
                                               args.intent_sha256, timeout=args.timeout, original_registration=recovery)
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
                output = training.cancellation(State(args.home), args.project, args.experiment_id, args.request_id,
                                                original_registration=recovery)
            elif args.operation == "cancel":
                output = training.cancel(State(args.home), args.project, args.experiment_id, args.request_id, args.revision,
                                         run_id=args.run_id, reason=args.reason, timeout=args.timeout, original_registration=recovery)
            elif args.operation == "resume-cancel":
                output = training.resume_cancel(State(args.home), args.project, args.experiment_id, args.request_id,
                                                args.revision, args.intent_sha256, timeout=args.timeout, original_registration=recovery)
            elif args.operation == "stop-status":
                output = training.stop_status(State(args.home), args.project, args.experiment_id, timeout=args.timeout,
                                               original_registration=recovery)
            else:
                output = training.inspect(State(args.home), args.project, getattr(args, "experiment_id", None),
                                          limit=getattr(args, "limit", 50), after=getattr(args, "after", None))
            print(json.dumps(output, ensure_ascii=False, indent=2))
            if args.operation == "check-start":
                return 0 if output["ready_for_new_start"] else 1
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
                    import ergora.improvement.scheduling as scheduling
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
            return native_compiler.workflow(args.arguments)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        if args.command == "gpu-pool" and output["status"] in ("unavailable", "rejected", "unknown"):
            return 1
        if args.command == "reference" and args.operation == "executor" and output and output["state"] != "SUCCEEDED":
            return 1
        if args.command == "services" and output.get("outcome") in ("unconfirmed", "failed"):
            return 1
        if args.command == "composition" and args.operation == "run-input" and output["status"] != "succeeded":
            return 1
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
