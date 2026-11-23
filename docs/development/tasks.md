# Create a formal development task

English · [Documentation](../README.md) · [简体中文](../zh-CN/development/tasks.md)

## Choose the task entry point

| Goal | Entry point and result |
| --- | --- |
| Check a proposed task's inputs and selected route | Run [task preview](#preview-and-create-formal-tasks), then stop at the digests and static admission result. This uses the registered project and needs no running services. |
| Ask for a one-off diagnosis of supplied material | [Prepare one leaf and call it in a supported read-only mode](../definitions/workflows/leaf-calls.md#call-a-prepared-leaf). Provide the input and any prerequisite evidence directly. The result is the leaf reply and its saved invocation record. |
| Deliver a small, reviewable code change | If the registered `repository-governance` template and project roles cover the change, use [one scoped work unit](#preview-and-create-formal-tasks). Review the exact plan, then read verification and independent review evidence for the exact candidate through the [original six-stage task](#formal-task-sequence-and-recovery). |

Choose a [saved composition](../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page) when the change requires it. Keep the preparation, work and review graph to the roles and dependencies the task needs, and check admission for the selected route. Any formal delivery uses the registered trusted checks and original approval and review gates.

## Current design-workflow availability

A first unified registration can store a schema2 design policy and its effective digests. It reports `execution_supported: false` and `human_channel_unavailable`; schema2 task creation and managed native execution refuse `design_policy_execution_unsupported`. Existing registrations cannot be upgraded, replaced or downgraded through that entry. See [the current registration boundary](../projects/registration.md#current-limits-of-design-policy-registration). These records provide policy storage, without executable design approval. Design source-journal storage and trusted owner/material/gate handling remain under implementation in [PLAN](../PLAN.md); plans and research do not establish delivered support. Existing schema1 task contracts remain in force.

Per-Agent explicit reasoning fields can request a level supported by the selected backend/model. Unified fixed/preset/planner/automatic selection and its configuration/freeze contract remain future work. A requested level does not establish the native level actually used, or authorize a model switch, hidden downgrade or larger budget.

## Formal task sequence and recovery

For first use, follow the [complete template journey](templates.md) and [Project definitions](../projects/registration.md) to prepare a real Git baseline, trusted checks and authenticated roles, then use the sequence below. Formal development requires the registered complete Linux/WSL2 executor. A workflow draft on the page is not yet a created formal task.

```text
project register → select roles/check revision → services start for the selected stack
→ task preview → review digest → task create → task start
→ inventory/plan → status pinned to original run → review actual plan → approve exact plan
→ work/integrate/verify/review → original outcome
→ REVIEW_READY: review exact candidate/checks/review → export local branch and check lease receipt → independent revalidation/human merge
   Defer export: external-status → explicit reconcile (original result/candidate retained)
→ Blocked or canceled: confirm original run is closed → external-status → explicit reconcile → recover using original intent
```

The formal task page also supports [selecting a saved complete composition](../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page): replace only review, or choose execution and review subflows and assign specialist instances and per-leaf backends to each work unit. First read the complete package matching the original preview digest, then preview and explicitly create. Users explicitly choose writable trust and cross-backend policies; failures display the original owner's error.

Retain the task ID, creation/submission intent SHA and original workflow/run IDs. All write commands use the current project revision. Approval also requires a stable decision ID and exact plan SHA; cancellation requires a stable request ID. HTTP 200, CLI 0 or requested is a receipt for the corresponding operation. The original outcome and candidate evidence determine whether the six stages passed. After closing the page or ending the CLI process, continue queries with the same `--home` and registered execution directory. Do not reuse task IDs to bypass old records.

|Interruption point|Read first|Allowed next step|
|---|---|---|
|Task contract publication|`task creation PROJECT TASK`|Run resume-create with the original intent SHA; check conflicting files first|
|Unknown submission result|`task submission PROJECT TASK`|resume-start checks the original spec/memo/run; unknown permits queries only, without resubmission|
|Unknown approval/cancellation delivery|`task approval PROJECT TASK DECISION` / `task cancellation PROJECT TASK REQUEST`|resume-approve/resume-cancel checks the original operation SHA and history; without a matching signal, it remains unknown|
|Closed but externally unconfirmed|`task status --run-id` and `task external-status --run-id`|Retain original result/requests/receipts/artifacts/fence; explicitly reconcile, then resume-reconcile if incomplete|
|Interrupted candidate export|`task export-status PROJECT TASK`|resume-export checks the original result and actual ref; unknown does not refetch or revive deleted branches|

A joint backup must retain the control `ERGORA_HOME`, registered CONFIG/STATE, business Git repositories, Temporal persistent data and actual tool authentication. A control SQLite backup excludes original tasks/history/candidates/leases. `tasks/`, `ergora/task-*`, requests/receipts/artifacts/approvals/fences, workspaces, process records and ledger in execution STATE are all recovery evidence. Stop the relevant writers and check in-flight external jobs first, then follow the [backup instructions](../install/upgrades.md#upgrades-and-persistent-data). See the [Joint backup and recovery guide](../operations/backup-recovery.md) for complete offline steps on the same platform at original paths, and checks before starting.

## Formal task page

After selecting a project registered through the unified entry point, open “Formal tasks” from the left sidebar or “View formal tasks” from the project overview. The list uses bounded cursor pagination; a page with no matches may still have a next page. Unreadable records and invalid contracts appear separately. Task details show the task's own frozen input, role snapshot, work units and local submission receipt. They do not fill in history from the current project bindings or treat an existing contract or submitted state as successful execution.

“Native run” defaults to the original run ID from the saved selection or submission receipt. It connects to the registered Temporal instance only after you click “Read original run.” The result preserves original facts such as REVIEW_READY, BLOCKED, CANCEL_UNCONFIRMED and NEEDS_RECONCILIATION; not_found and query failures appear separately. After you switch tasks/projects, edit the run ID or leave the page, an old response cannot overwrite the current selection. Refreshing or returning to the console in the same browser tab preserves the project, page, task and run selections, while execution status is queried again. Retention after closing the tab depends on the browser's own session recovery.

Click “Preview and create,” select a development template registered for the project, and load the template input or a compatible saved draft. Enter a new task ID, issue number or local identifier, and edit the complete input JSON. You can specify a starting commit; leave it blank to use the registered baseline. The server preview shows the revision, frozen roles, complete files and digests. Changing any field or source immediately invalidates the previous confirmation. After reviewing, click “Confirm creation of frozen contract.” This publishes the contract without automatically submitting a run. Training optimization continues to use its separate entry point.

Before sending a creation request, the browser saves the original task ID as the project's task selection. If the response fails or is lost, the form locks; first use “Read creation record by original ID.” You can also query by ID at the top of the page at any time. If the contract has not been fully published after a reload, the details error still retains the original ID and query entry point. `pending` shows the original intent digest and frozen revision; explicitly confirming recovery publishes the original content. Later project binding changes do not replace the old roles. `published` shows that the frozen contract has been published, `not_recorded` does not take over old tasks, and `conflict` preserves conflicting files without offering an overwrite button. The page does not automatically resend creation, change the ID or start execution.

“Check submission and recovery” in task details rereads the creation and local submission records. If publication is complete and no submission record exists, you can review the frozen contract, roles, current revision and digest, then select “Confirm submission of this frozen task.” `prepared` or `unknown` offers only explicit recovery of the original intent. The backend decides whether to continue a submission that has not been dispatched or query a dispatch whose result is already uncertain. `not_found` remains unknown; the page does not resend start. An ownership `rejected` state provides no override entry point. If the response fails, reread the original record first; this does not justify changing the ID. `submitted` saves the original run selection. Click “View original task and run,” then read the run status separately; a submission receipt does not mean the six stages are complete.

When the original run query returns `AWAITING_PLAN_APPROVAL`, click “Review plan and approve” to read the complete execution-plan, ownership-map and rollback-plan, together with the exact receipt identity. No approval entry point is available if material reading fails. After reviewing, enter a stable “Decision ID (for recovery),” such as `owner-one`, and first select “Read approval record.” “Confirm approval of this plan” is offered only if that ID has no record. Confirmation binds the run/plan SHA of these materials, and the server checks the current state again. Keep this ID; do not use a new ID to bypass unknown delivery.

Task details also provide “Check approval record by original ID,” which does not require the task to still be awaiting a plan. The browser retains the latest decision selection per project/task. If the selection is cleared or you change devices, entering the original ID manually still retrieves the backend record. `prepared` allows “Confirm recovery of original approval intent”; `unknown` allows only “Confirm reconciliation of original approval signal”; `requested` displays delivery facts and offers no further delivery button. If the current materials workspace finds an existing decision, inspect its original record separately; current materials do not overwrite the old decision. If the response fails, reread the original record first. Reloading does not automatically approve anything. Return to the original task and select “Read original run” again to check actual acceptance and execution progress.

While the original run is still running, click “Request cancellation of this run,” enter a stable “Cancellation request ID (for recovery),” and first select “Read cancellation record.” A reason field and “Confirm cancellation request for this run” are offered only if that ID has no record. The server fixes the original run and checks its state again. Task details also provide “Check cancellation record by original ID”: `prepared` explicitly recovers the original cancellation intent, `unknown` only reconciles the original signal, and `requested`/`already_closed` offers no redelivery. Current edits cannot overwrite the original reason or intent. `already_closed` means the original run was closed before sending and no new signal was sent.

Keep the original cancellation request ID. After a lost response, read the original record first. If the browser selection has been cleared, enter the original ID manually to resume querying. Cancellation is a cooperative request; `requested` does not confirm a stop. Return to the original task and select “Read original run” again to check the phase and terminal state. Reconcile external job cleanup and lease release separately.

Once the original run is closed, click “External evidence and reconciliation” for a read-only view of that run's jobs, request/receipt/artifact verification results, fence and original outcome. Reading does not change the execution fence or lease. Even if some jobs already have terminal states, check `external_confirmed`; workflow closure or cancellation delivery does not establish completed cleanup.

Read the original reconciliation record in the same workspace. “Confirm external reconciliation and release original lease” is offered only when the current external evidence read succeeds and the record is `not_recorded`. The operation rechecks the original run, creates or reuses the same fence, and releases the original claim after all external jobs are confirmed. Task details also provide “Check original reconciliation record and recovery,” which reads only local persistent records. `prepared/unknown/confirmed` allows “Confirm recovery of original reconciliation intent,” binding the original intent SHA without replacing it with the currently edited run. `confirmed` has not yet saved a lease-release receipt; only `reconciled` means that the original lease release and receipt have been saved. The latter offers no further write operation.

After a lost response, reload or reselect the original task, then read its original reconciliation record. No new reconciliation ID is needed. Live external evidence and historical reconciliation receipts are read separately. The original `CANCEL_UNCONFIRMED` outcome remains; completed cleanup does not mean development succeeded. Failed external evidence reading prevents a new reconciliation, but an already saved original intent can still be inspected separately and explicitly recovered.

When the original run is closed with a `REVIEW_READY` outcome, click “Export exact candidate.” The page fixes the original run/full candidate SHA for this operation and first reads the original export record. Only `not_recorded` offers a target local branch field and “Confirm export of this candidate to a local branch.” Server-side Git/original-outcome checks decide whether the branch is valid and the original candidate can be exported. The page does not replace existing branches, checkout, merge or push.

Task details also provide “Check original export record and recovery,” which reads only local records without querying Temporal or current Git refs. `prepared` allows “Confirm recovery of original export intent” and may create the saved target for the first time. `unknown` allows “Confirm reconciliation of original export branch” and only checks the original branch; `branch_not_found` remains unknown and does not recreate it. Recovery binds the original intent SHA; repo/run/candidate/branch cannot change. `exported` displays only the historical receipt and original lease-release facts. It does not prove that the current ref is still correct, that development succeeded or that the change was merged. After a lost response, reselect the original task and read the same record without resending the export. Maintainers must still recheck the actual branch and evidence before adoption.

Projects not registered through the unified entry point show registration guidance. Local contracts remain viewable when the service is unavailable. Closing a dialog or page does not revoke an operation already sent, and closing the page does not cancel external tasks. A terminal state does not mean external job cleanup has been confirmed. The browser saves only selections; creation/execution facts are read from the server each time.

## Read formal task contracts

First complete [unified project registration](../projects/registration.md). You can read existing development tasks in the execution directory directly from the main entry point:

```bash
ergora task list my-project --limit 50
ergora task show my-project TASK_ID
```

The same-origin APIs are `GET /api/projects/ID/tasks?limit=50&after=CURSOR` and `GET /api/projects/ID/tasks/TASK_ID`. Each page validates 50 candidate directory entries by default, configurable from 1–100. Pass the returned opaque ASCII cursor `next_after` unchanged to continue until it is null; the cursor is neither a task ID nor a file path. Each page streams all directory names before selecting its candidate window, so enumeration time grows with the number of tasks. `inspected_entries` counts only the entries validated on that page. Other projects or damaged directories may produce empty pages; continue following the cursor. `items` contains only tasks matching the project/Git root/tracker and passing contract structure and digest checks. Entries with confirmed ownership but damaged contracts go into `errors`; entries whose ownership cannot be determined are counted only in `unreadable_count`.

Details return the original spec, frozen project, optional `agent_bindings` and their file SHA256 values. `project_revision` is the current control-project revision; `project_revision` in frozen bindings belongs to the snapshot taken at creation or first execution. `runtime_status: not_queried` means Temporal was not accessed. Existing local files do not mean a task has started, completed or passed acceptance. Contract queries do not install the SDK, start services, submit tasks or write back to old records. Tasks created/submitted through the unified entry point use the explicit [plan approval](design-and-approval.md), [cancellation](run-and-recover.md#request-cancellation-and-recover-unknown-delivery) and [export](evidence-and-export.md#export-an-exact-candidate-and-recover-its-receipt) operations. Tasks from the old entry point continue to be managed according to the [formal execution guide](../agents/backends.md). Linux and Windows can both read locally accessible execution directories; full six-stage execution requires Linux/WSL2.

## Preview and create formal tasks

Projects registered through the unified entry point can compile and save both development templates with a base installation, without Temporal/Web SDKs. First save `task-definition.json`. `input` uses the template's original input format; the original compiler still validates its fields and DAG:

```json
{
  "schema_version": 1,
  "task_id": "example-change",
  "task_type": "repository-governance",
  "issue_id": "1",
  "input": {
    "goal": "检查并整理 src 内的模块边界",
    "allowed_paths": ["src"],
    "acceptance": ["保持已有行为和可信检查"],
    "constraints": [],
    "risk": "standard",
    "work_units": [{"id": "inspect", "depends_on": [], "paths": ["src"], "instructions": "完成边界整理"}]
  }
}
```

Choose `repository-governance` or `large-change`; the template must already be registered for the project. For large development tasks, set the risk and input according to the original template. The optional `starting_sha` is a 40-character lowercase Git commit SHA and defaults to the registered baseline. Replace the revision below with the current value from `project show`:

```bash
ergora task preview my-project --definition task-definition.json --revision 1
# Review the complete spec, trusted policy, frozen project and agent-bindings returned in files.
# Replace PREVIEW_SHA with preview_sha256 from this output:
ergora task create my-project --definition task-definition.json --revision 1 --preview-sha256 PREVIEW_SHA
ergora task creation my-project example-change
# After an interruption, recover with intent_sha256 from creation and the current project revision:
ergora task resume-create my-project example-change --revision 1 --intent-sha256 INTENT_SHA
```

preview invokes the original compiler only in an automatically cleaned temporary directory, without writing to the real task directory. The digest binds the control directory, project revision, registered identity, all compiled contracts and role snapshot. Review a new preview whenever the definition or bindings change. Before publishing any native task file, create saves the complete intent, then publishes seven immutable contracts and finally saves the result receipt. The same request can be retried idempotently. Task IDs are globally unique within an execution-state directory; create and resume-create cannot take over an old task without this tool's intent.

Read `route_admission` in the preview before using the creation digest. A valid graph can be blocked for the chosen route. A blocker identifies the relevant instance and reason. The CLI prints the preview and exits 1 for `route_admission.status: blocked`, and create refuses the selection before saving an intent. Graph-only previews and saved manifests are still available from the definition library. A standalone leaf uses its own admission check and operator-supplied input.

`creation.status` is `not_recorded / pending / published / conflict` and describes only local file publication. `runtime_status: not_queried` and `execution_started_by_operation: false` mean this operation neither queried nor started a workflow; they do not establish the task's actual runtime state. Each contract file is limited to 1 MiB; the intent limit is 16 MiB. Comparison uses native canonical JSON content digests and preserves the bytes of equivalent existing files. Intents and receipts are stored in the registered execution-state directory as `ergora/task-creations/TASK_ID.intent.json` and `.result.json`. Keep them with the original task directory; a backup of the Ergora control database alone does not include the execution-state directory.

After an interruption, query creation first, then explicitly recover using the original intent digest. Recovery does not recompile and retains the original role snapshot even after project bindings change. Conflicting files are preserved and reported as errors; history is not automatically overwritten or recreated. If the project configuration projection or execution directory has drifted, repair the original registration first. Switching execution directories does not automatically migrate old tasks. Write operations serialize while retaining the project revision and acquire a same-ID file lock without blocking. A busy task explicitly returns busy. The budget for one native process is 30 seconds; after a timeout, query the original intent first without automatically retrying.

The corresponding APIs are `POST /api/projects/ID/tasks/preview` (`definition/revision`), `POST /api/projects/ID/tasks` (adding `preview_sha256`), `GET .../tasks/TASK_ID/creation` and `POST .../tasks/TASK_ID/resume-create` (`revision/intent_sha256`). Write requests retain the local same-origin restrictions and `X-Ergora-Request: 1`. Preview and creation support local file contracts on Linux/Windows. Full six-stage execution still uses Linux/WSL2 and the [formal execution guide](../agents/backends.md).

Continue: [Prepare a task's frozen composition](preparation.md) · [Submit, observe and recover a development task](run-and-recover.md).
