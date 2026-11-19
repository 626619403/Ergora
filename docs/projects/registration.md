# Register a project

English · [Documentation](../README.md) · [简体中文](../zh-CN/projects/registration.md)

`project add` creates a lightweight control project for standalone Agents, memory, Skills and research. `project register` registers a business Git root, tool bindings, templates, tracker, execution locations and trusted checks together, then publishes the reference project/policy files required for formal execution. The CLI and local API use the same application use case; a GitHub or GitLab account is not required.

## Unified registration

Install the [current reference prerequisites](../install/linux.md#prepare-the-formal-reference-runtime) first, then complete model authentication, platform settings and trusted execution boundaries. Registration checks the definition and installation identity; it does not install services, invoke models or run checks. The repository must already contain a commit. All three execution directories must be absolute paths outside the business repository. They may use persistent user directories. Windows supports registration and check configuration; formal six-stage execution still requires Linux/WSL2.

Save the following as `project.json`, replacing the paths with actual absolute paths. Checks use argv arrays and run in trusted check processes; `{repo}` expands to the task checkout. These example checks suit only a small Python project. Configure the project's own behavior, architecture and knowledge checks for actual use.

```json
{
  "schema_version": 1,
  "id": "my-project",
  "repo": "/home/USER/projects/my-project",
  "templates": ["repository-governance"],
  "execution": {
    "installation": "/home/USER/multi-agent-platform",
    "config_directory": "/home/USER/.config/multi-agent-platform",
    "state_directory": "/home/USER/.local/state/multi-agent-platform"
  },
  "tracker": {"kind": "local", "project": "local/my-project"},
  "allowed_paths": ["src", "tests"],
  "checks": {
    "behavior": ["python", "-m", "pytest", "{repo}/tests"],
    "architecture": ["python", "{repo}/checks/architecture.py"],
    "knowledge": ["python", "{repo}/checks/knowledge.py"]
  },
  "scope_policy": {
    "schema_version": 1,
    "protected_paths": [".git", ".symphony", ".agent-control", ".agent-platform-private"],
    "max_changed_files": 200,
    "max_changed_lines": 20000
  }
}
```

```bash
ergora project register project.json --revision 0
ergora project config my-project
ergora project registration my-project
```

Use revision0 for a new project. When registering an existing lightweight project, use its current revision from `project show`. An existing project must retain the same Git root; omitted tool bindings remain unchanged. Optional `bindings` use the same format as `project bind`; missing formal role capabilities or the `stage-json-v1` protocol are rejected. Optional `base_sha` pins an existing commit; omission selects HEAD. Unknown fields/versions are rejected, and project definitions do not store API keys.

`large-change` also requires `integration`, `compatibility` and `migration-rollback` checks; the executor provides `scope` and `baseline-regression`. Multiple templates may be registered together, and checks must satisfy every development template. `training-optimization` registers three training roles and execution locations; configure the runner, workload, baseline and experiments through the [reference training flow](../agents/backends.md). Registration does not initialize or accept training.

The configuration directory receives:

- `projects/ID.json`: business repository, tracker, baseline, allowed paths and checks.
- `policies/ID/scope.json` and `execution.json`: scope policy and enabled development templates.
- `ergora/registrations/ID.json`: ownership record for the control directory and definition digest.

The control project document is authoritative for the definition and bindings. These files are one-way, immutable projections; do not edit them in both directions. `project bind` may still revise tool selections. Changes to the baseline, templates or trusted policy require a new configuration directory, retaining the old configuration for existing tasks; conflicting content at the original path is not overwritten. A configuration directory allows only one business project per tracker.

## Current limits of design policy registration

The example above uses registration schema1. Schema2 can save a complete `design_policy` and its profile/policy digests for a genuinely first unified registration. `project registration` returns the effective minimum questions/knowledge requirements and `execution_supported: false`; a configured owner does not authenticate a human. An existing unified registration, including an empty schema1 registration, cannot upgrade to schema2. A schema2 registration cannot be re-registered, replaced or downgraded, and existing native projections are not a first registration. The complete input format is defined by [registration schema2](../../src/ergora/data/schemas/project-registration-v2.json).

Current schema2 projects cannot create or execute legacy task inputs: ordinary/budgeted task birth and managed native execution admission reject them with `design_policy_execution_unsupported` / `human_channel_unavailable`. This is not an executable design approval flow. The source journal, trusted owner decisions and later gates have separate delivery work in the [implementation plan](../PLAN.md). Do not delete a registration, change it to schema1 or switch control directories to bypass refusal. The schema1 example retains its original task and recovery contracts.

## Interrupted publication and recovery

Publication across SQLite and multiple files records the intent, saves a pending project, publishes files, then confirms published status. Registration status and file consistency are reported separately; a published registration with `consistent: false` still needs drift investigation.

```bash
ergora project show my-project
ergora project registration my-project
ergora project resume-registration my-project --revision CURRENT_REVISION
```

Recovery uses only the saved original intent. Identical files may be retried idempotently; conflicting files are retained and reported as errors. A pending project cannot change bindings or start new formal tasks. The recovery record is `registrations/ID/OPERATION.json` under the Ergora control directory and contains the before/after project and source; `.result.json` is its publication receipt. The same resume command can finish a missing completion receipt. Do not delete a pending record and resubmit another definition.

## Formal tasks and API

New tasks use the unified `ergora task` entry point for creation, submission, approval, cancellation and export. Tasks created through the old entry point continue through `agentflow task`. The executor can select the directories saved by a unified project directly:

```bash
ergora reference executor --project my-project
```

Enable the selectable executor only for new tasks, and do not run it alongside the original executor. New tasks verify published status, directories and projections, then freeze their effective configuration; existing tasks retain their original binding snapshots. See the [Agent guide](../agents/backends.md) for complete approval, six-stage and evidence requirements. The unified entry point can [read an existing formal task's contract](../development/tasks.md#read-formal-task-contracts) and frozen bindings. Preview, creation and interrupted recovery use [unified creation](../development/tasks.md#preview-and-create-formal-tasks); `task status` [queries the native run](../development/run-and-recover.md#query-formal-task-run-status). Use [unified submission and recovery](../development/run-and-recover.md#submit-formal-tasks-and-recover-unknown-results), [exact-plan approval](../development/design-and-approval.md#approve-an-exact-plan-and-recover-delivery), [original-run cancellation](../development/run-and-recover.md#request-cancellation-and-recover-unknown-delivery) and [exact-candidate export](../development/evidence-and-export.md#export-an-exact-candidate-and-recover-its-receipt). After closure, [check each external-job evidence item](../development/evidence-and-export.md#check-external-job-evidence-for-a-closed-run) and explicitly [reconcile/recover the exact claim](../development/run-and-recover.md#explicitly-reconcile-terminal-state-and-release-issue-leases) using the current revision. The reference commands can still manage tasks created through the old entry point. The [formal-task page](../development/tasks.md#formal-task-page) exposes the same lifecycle and original-ID recovery; after closure, read evidence/budgets and download a handoff bundle through the [web handoff](../development/evidence-and-export.md#web-evidence-budgets-and-handoff) as needed.

After changing execution configuration directories, old tasks still require their original configuration/state and installation. When restarting the old executor, set its original `AGENTFLOW_CONFIG_DIR` and `AGENTFLOW_STATE_DIR` explicitly and use `--installation`. `--project` selects the currently registered directories; it does not migrate old tasks or services.

Local HTTP entry points retain same-origin and `X-Ergora-Request: 1` protection:

|Method and path|Input/output|
|---|---|
|`POST /api/project-registrations`|`{"definition": {...}, "revision": 0}`, returns the project|
|`GET /api/projects/ID/configuration`|Effective bindings, registration definition, revision and digests|
|`GET /api/projects/ID/registration`|Publication status, per-file consistency and recovery-record location|
|`POST /api/projects/ID/registration/resume`|`{"revision": CURRENT_REVISION}`|

## Explicit import of an existing registration

Existing reference registrations require explicit import; `register` cannot adopt them automatically. First stop registration writers for that configuration directory and retain old tasks and their original runtime directories. Import reads only same-ID `projects/ID.json`, `policies/ID/scope.json` and optional `execution.json`; it does not import model keys or service settings.

Save `import.json` with the existing registration ID, expected Git root, enabled templates and all three absolute execution directories:

```json
{
  "schema_version": 1,
  "id": "my-project",
  "repo": "/home/USER/projects/my-project",
  "templates": ["repository-governance"],
  "execution": {
    "installation": "/home/USER/multi-agent-platform",
    "config_directory": "/home/USER/.config/multi-agent-platform",
    "state_directory": "/home/USER/.local/state/multi-agent-platform"
  }
}
```

Optional `bindings` select roles/support tools. Omission retains existing control-project choices; new projects use defaults. The baseline, tracker, checks, allowed paths and scope come from the old files. A different Git root, unknown fields/versions, insufficient role capabilities or checks are rejected. If an old execution policy exists, its development-template member set must match, and its original member order and JSON formatting are preserved. If absent, the selected development-template allowlist is explicitly generated; this can narrow previously unrestricted task types.

```bash
# Read-only preview by default; revision0 for a new control project, current revision for a lightweight one.
ergora project import-reference import.json --revision 0
# Review definition, changes, files and target control_home, then supply that preview_sha256.
ergora project import-reference import.json --revision 0 --apply --preview-sha256 REVIEWED_SHA256
```

Preview `changes` use JSON Pointer. `files` lists each `adopt/create` action, raw source-byte SHA and expected projection-semantic SHA. `preview_sha256` binds the target control directory, revision, definition and file intent. Apply rereads and verifies the source: even whitespace changes require a new preview. Compatible old files retain their original bytes; only missing policies and ownership records are created. Import does not scan or migrate in-flight tasks.

Import uses the same pending intent and `resume-registration` path. Its recovery record also stores the preview SHA, each source identity and the before/after control project; it is recovery evidence, not a complete backup of the original directory. If another process changes an adopted file after reservation, recovery refuses. Verify and restore the original file first, or retain the pending record for maintenance. Do not overwrite the original configuration to bypass conflicts. A registration already owned by another control directory cannot be adopted again.

|Method and path|Input/output|
|---|---|
|`POST /api/project-registration-imports/preview`|`{"definition": IMPORT_SPEC, "revision": 0}`, returns a read-only preview|
|`POST /api/project-registration-imports`|The same input plus `"preview_sha256": "REVIEWED_SHA256"`, explicitly adopts it|

Continue: [Follow the bundled development templates](../development/templates.md) · [Prepare a task's frozen composition](../development/preparation.md).
