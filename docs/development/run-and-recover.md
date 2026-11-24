# Submit, observe and recover a development task

English · [Documentation](../README.md) · [简体中文](../zh-CN/development/run-and-recover.md)

## Query formal task run status

Install the development profile or `ergora[temporal]`, and prepare the registered reference runtime. Use the CLI or `GET /api/projects/ID/tasks/TASK_ID/status?run_id=RUN_ID&timeout=20` for read-only native-run facts:

```bash
ergora task status my-project TASK_ID --timeout 20
# Pin subsequent queries to the native run_id returned by the previous query:
ergora task status my-project TASK_ID --run-id RUN_ID --timeout 20
```

This operation first validates the local task's project ownership and spec, then uses the original DevelopmentTransport in the registered installation to check Temporal's original start input. `runtime_status: queried` includes the native workflow/run ID, phase and status or outcome. If no run ID is supplied, it first resolves the current workflow and returns its concrete run ID, which can be pinned for subsequent queries. Only a native NOT_FOUND returns `runtime_status: not_found`, without an invented phase. Connection, authentication, timeout and original-input collision failures are errors and cannot be treated as “not started.” The query does not submit, approve, cancel or release an issue lease, and does not write task state.

`terminal: true` means only that the Temporal run is closed. Its outcome may still be CANCEL_UNCONFIRMED, or its phase NEEDS_RECONCILIATION; both require reconciliation under the original ID. This entry point uses the registered reference environment's connection rules (currently local 127.0.0.1:7233/default). The project scheduler binding's address/queue is used only for material-research scheduling. A 1–60-second timeout constrains the network query. The child process receives an additional 5 seconds for startup/reaping; local contract prechecks and installation identity checks are separate. Missing SDKs produce an explicit message. They are not installed automatically, and runtime state is not inferred from local COMPILED or service RUNNING states. Full six-stage execution still uses Linux/WSL2.

## Prioritize a pending work unit

During approved implementation, a supervisor can prefer a work unit from the original task. Use a task with a recorded `task start` submission. Query the original run and use its `status.work_priority.pending_work_unit_ids`, `plan_sha256` and project revision. The capability requires the current Linux/WSL2 budgeted preparation workflow and a worker that reports `work_priority.available`. Choose a decision ID unique to this request.

On the formal task page, select “Read original run” and then “Prioritize a pending work unit.” Choose one of the reported pending units, enter a decision ID and check it. Review the original run, approved Plan digest and project revision before confirming. After an uncertain result, use “Read priority decision by original ID” on the same task. You can open that reader after the run closes and enter an ID recorded through the CLI or API.

```bash
ergora task status my-project TASK_ID --run-id RUN_ID
ergora task prioritize-work my-project TASK_ID UNIT_ID --revision REVISION \
  --run-id RUN_ID --plan-sha256 PLAN_SHA --decision-id DECISION_ID --confirm
ergora task work-priority my-project TASK_ID DECISION_ID --run-id RUN_ID
```

The same-origin API uses `POST /api/projects/ID/tasks/TASK_ID/work-priority/DECISION_ID` with `X-Ergora-Request: 1` and a JSON body containing `revision`, `run_id`, `plan_sha256`, `work_unit_id`, `confirm: true` and optional `timeout`. Read the original result with `GET /api/projects/ID/tasks/TASK_ID/work-priority/DECISION_ID?run_id=RUN_ID&timeout=20`.

`applied` means the workflow recorded the preference. The unit takes precedence when its original predecessors have succeeded and the original concurrency limits permit dispatch. Other eligible units can start while it waits. A later decision can replace the preference. Each work unit keeps its original inputs, owner and job ID. The same plan approval, budget cutoff, integration, verification and review apply.

The task saves the exact attempt beside its submission records before sending one Temporal Update to the original run. After a lost response, use the read-only Console action, API or `task work-priority` with the original run and decision IDs. A repeated submission for a saved decision reads its outcome. An unavailable outcome remains `unknown`. A rejection or unavailable worker before the attempt leaves no attempt. An update that races a dispatch, cancellation or cutoff may return a recorded rejection. Use workers that support this Update for all runs on the updated queue throughout execution and recovery.

## Preview a substantive amendment and prepare its successor

Use a new task ID and an edited schema-8 definition for the same registered project, repository and native issue. Include the revised requirements and the new budget policy in that file. Start with a comparison against the exact original budgeted run.

```bash
ergora task preview-amendment my-project ORIGINAL_TASK --run-id ORIGINAL_RUN \
  --revision REVISION --definition revised.json --change 'Describe the revised work' > amendment.json
```

The read-only preview shows changed requirements, work membership, instructions, scope, assignments and dependencies, plus the observed state of original jobs and Plan. During a live run, a unit absent from the visible history is `not_observed`. An unconfirmed checkpoint returns `status: blocked` and a null `successor_definition`. Check the original submission, request cancellation if needed, and reconcile closure through the existing commands. The successor requires evidence of stopped jobs and a matched release in the original ingress ledger. An interrupted reconciliation with only `confirmed` state needs recovery using its original intent. An active SQLite WAL, rollback journal or changing ledger leaves the preview unconfirmed until it can read a stable checkpoint.

When the preview returns `status: ready`, save the complete `successor_definition` object. `jq` is one way to extract it.

```bash
jq -e '.successor_definition | select(. != null)' amendment.json > successor.json
ergora task prepare my-project --revision REVISION --definition successor.json
```

The ordinary `prepare` command verifies the exact original closed run, matching fence and terminal job evidence, and the durable release in the original ingress ledger before it authorizes the successor. It recomputes the substantive difference from the original definition. A new ID or budget alone leaves the work definition unchanged. Run the preview again after editing the proposed work or changing the project revision. Continue with the ordinary `task preview`, `create` and `start`, then inspect and approve the successor's own exact Plan. `task creation` includes its pinned amendment link. The successor has its own clock, model slots and six-stage evidence. Earlier work remains readable by its original identity. An intervening task may still own the issue when the successor tries to start.

## Read original-run events in pages

For a task created through the unified entry point with its original submission receipt saved, pin that receipt's run ID and read event metadata:

```bash
ergora task events my-project TASK_ID --run-id RUN_ID --limit 20 --timeout 20
# Only when continuing, pass the previously returned next_after unchanged:
ergora task events my-project TASK_ID --run-id RUN_ID --limit 20 --after CURSOR --timeout 20
```

The same-origin read-only API is `GET /api/projects/ID/tasks/TASK_ID/events?run_id=RUN_ID&limit=20&after=CURSOR&timeout=20`; omit after on the first call. This entry point uses the Linux/WSL2 reference runtime and original submission/spec/memo validation described above, without following another run. It returns event IDs, types, timestamps and applicable activity/scheduled_event/signal association fields, without original input, prompts, results or payloads. Event projection does not decode payloads, although original-identity validation still needs to decode the start spec. `read_only: true` and `execution_success: null` make clear that this is only a fragment of facts. If the native run does not exist, it returns `runtime_status: not_found`. Connection, timeout, wrong-ownership and cursor errors fail explicitly without automatic retries or task resubmission.

After original-identity validation, each call reads one physical SDK event page and returns at most limit entries (1–100, default 20); it does not guarantee filling the limit. The overall request also describes the original run and reads its start prefix, so it is not a single RPC. Temporal's physical page size is advisory and may exceed the requested count. The cursor retains the unread position in that page, and the next call first continues through its remaining entries. `next_after` is read-only navigation bound to the original submission/run, not authorization or proof of complete history, and cannot be used across runs. The display limit can change; the SDK page size retains the original cursor's value. The total JSON response is limited to 1 MiB; that response limit does not constrain network memory used by SDK physical-page reception. timeout is a 1–60-second wall-clock budget. The parent process provides another 5 seconds for startup/reaping; prechecks are separate.

`has_more` means unread content is known to remain; `at_current_end` means only that reading has reached the currently visible end. A RUNNING run retains next_after even when no new events are currently available, so the user can explicitly read later. Only a terminal run read through its end returns null. Event fragments do not prove six-stage completion, candidate acceptance or stopped external processes; verify those facts through the original status/outcome and external reconciliation.

On the formal task page, first select “Read original run,” then “Read original-run events.” Opening reads the first batch; each subsequent click reads at most 20 entries, without automatic polling or retry. The page shows the cumulative read count and the latest 200 entries. Association fields exceeding 256 Unicode characters show an ellipsis; read complete metadata through the CLI/API. At the current end of a running run, you can still manually select “Read new events.” The button is disabled after a terminal run has been fully read. A failed read preserves the fragments already read in this session and the original position; continuing requires an explicit retry click. Closing and reopening starts from the first batch. Switching project, task or run invalidates old responses. Displayed records are only this session's observations, not persistent evidence or proof of complete history.

## Read original job receipts and text evidence

From the original events above, for Activity type `dev_submit`, select an `ACTIVITY_TASK_SCHEDULED` event ID (not an activity ID or completed-event ID), then read the job catalog first. 42 below is only an example; use the actual ID:

```bash
ergora task job my-project TASK_ID --run-id RUN_ID --event-id 42 --timeout 20
# Select a name from the returned receipt.artifacts and retain this receipt_sha256; do not pass a local path
ergora task job my-project TASK_ID --run-id RUN_ID --event-id 42 --artifact model-log --receipt-sha256 RECEIPT_SHA --offset 0 --limit 8192 --timeout 20
```

The API is `GET /api/projects/ID/tasks/TASK_ID/jobs/42?run_id=RUN_ID&timeout=20`. Add `artifact=model-log&receipt_sha256=RECEIPT_SHA&offset=0&limit=8192` for a text window. Continue manually with the returned `artifact.next_offset`; null marks the end of that text. offset/limit count Unicode characters, not UTF-8 bytes. A window defaults to 8192 characters and allows at most 16384, retaining the SHA, byte count and character count of the complete original text. A changed receipt or changed artifact bytes causes an explicit failure, preventing fragments from being combined as one log. Artifact names match only entries in the selected original job receipt; user-supplied paths are not parsed.

This read still pins the unified task's original submission/run/spec/memo. It checks a contiguous history prefix through the selected scheduled event, decodes only that event's original context, then checks the original request envelope and receipt published in the trusted directory. Event IDs 1–10000 are supported. Later events are explicitly rejected; this does not establish that no job exists. Both RUNNING and closed original runs can be read. `runtime_status: not_found` means the original history is currently unknown; `receipt_status: missing` means there is no verifiable published receipt yet. Without a receipt, no log is offered, and an existing request directory is not treated as completed execution.

`receipt_status: published` means only that the original job's currently published receipt passes checks through the local trusted file adapter. `workflow_receipt_accepted: null` and `execution_success: null` preserve uncertainty. Even if the receipt state is SUCCEEDED, use original-run status/outcome, candidate checks and external reconciliation to verify actual acceptance, development results and cleanup facts. This feature does not change original intents, receipts, claims or Git refs, and does not submit, resend or automatically retry.

The native adapter allows at most 16 MiB per artifact. It checks the complete digest first, strictly decodes the selected full UTF-8 text and rejects NUL, then returns the window. Missing, damaged, non-UTF-8, NUL-containing, oversized or unsafe-path artifacts fail explicitly. Each receipt check rereads the digests of all its artifacts; the selected text also requires a complete read/decode. The window and 1 MiB JSON response limits do not limit SDK physical pages or total file reading/memory, and there is no hidden cache. timeout is 1–60 seconds. Network operations inside the coroutine are constrained by a 20-second RPC limit and the request budget; synchronous file reads are finally reaped by the parent process at timeout+5 seconds. This entry point uses the existing Linux/WSL2 reference runtime. The base Web application itself does not require the Temporal SDK, but native queries need the registered complete execution environment and its SDK. If the environment is incomplete, configure it according to the tool-diagnostics page; nothing is installed and no services are started automatically.

On the page, first read the original run and its events, then click “Original job evidence” on a scheduled-event row whose Activity is `dev_submit`. The dialog reads that original run/event's job catalog and shows the original receipt, candidate and digests. Missing or failed reads can be retried manually. Selecting a material from the receipt does not issue a text request. Only clicking “Read first segment of selected material” reads an 8192-character window; read the next segment manually. Each read pins the first receipt SHA, and the page retains only the current window and full artifact digest. Material errors or an unknown original run preserve the read window and original offset, allowing “Retry original position.” If the receipt changes, close the dialog and recheck the catalog; old windows cannot be stitched together. Switching materials clears the window and resets the offset to zero; reading stops at the end. Closing and reopening restores no text and performs no background polling. Editing the run, switching task/project, replacing the dialog or leaving the page invalidates late responses from previous requests.

## Submit formal tasks and recover unknown results

On Linux/WSL2, install the reference runtime's required dependencies and initialize the registered configuration. Admission uses that runtime's `.venv/bin/python`. The control plane need not install all execution dependencies. v1–v6 use the original installation-level doctor; v7 source tasks check actual dependencies according to the [frozen selection](../projects/issues.md#create-a-source-task-from-an-issue-snapshot). Actual submission still checks trusted checks, policies and issue occupancy; selected services and models must be ready. This entry point accepts only tasks fully created through the unified entry point and retains their original spec and role snapshot.

```bash
# CREATION_SHA comes from task creation's intent_sha256; obtain the revision from project show.
ergora task start my-project TASK_ID --revision 1 --creation-sha256 CREATION_SHA --timeout 20
ergora task submission my-project TASK_ID
# After an interruption, read submission first, then explicitly recover with its original intent_sha256 and the current project revision:
ergora task resume-start my-project TASK_ID --revision 1 --intent-sha256 SUBMISSION_SHA --timeout 20
```

On the formal task page, enter the original task ID to see its submission and next action. The initial view and `task submission` read local evidence without connecting to Temporal. They show the task and workflow IDs, a run ID when verified by the saved submission receipt, and canonical JSON SHA256 digests for each verified intent, attempt, result and rejection record. A null digest means that record was absent in the local read.

| Submission status | Next action |
| --- | --- |
| `not_recorded` | Review the frozen task. To submit it for the first time, use the current project revision and `creation_sha256` with `task start`. |
| `prepared` | Use `task resume-start` with the original `intent_sha256` to continue admission for the first dispatch. |
| `unknown` | Use `task resume-start` with the original `intent_sha256` to check the original workflow for its matching input and submission memo. Preserve the original identity and attempt if the lookup fails or returns `not_found`. |
| `rejected` | Inspect the original rejection digest and conflict reason. A reported conflicting run belongs to the conflict record. |
| `submitted` | Read progress with `task status --run-id RUN_ID` using the saved run ID. If closed, check [external evidence and reconciliation](#explicitly-reconcile-terminal-state-and-release-issue-leases) for cleanup. |

A mutation command reports CLI success only for `submitted`. The receipt records delivery. Execution and cleanup have their own observations.

The immutable intent is saved first, followed by original admission/claim. An attempt is saved before the actual start, and the native receipt is saved last. prepared can repeat admission through an explicit resume while reusing the same lease. unknown can only query original input under the original workflow ID and fill in the receipt; even NOT_FOUND does not permit resending. A crash after writing the checkpoint but before the actual RPC also retains unknown and requires manual reconciliation. An existing run is rejected rather than taken over; later disappearance of its history does not automatically restart it. The original start associates this submission-intent digest in Temporal memo, and unknown recovery also checks that marker. Missing or different markers prevent adoption as this submission. An AlreadyStarted response from a submission race is persistently rejected without adopting another entry point's run. Original input is compared exactly by canonical JSON digest, distinguishing true/1/1.0. Original-input mismatch, RPC failure and contract/registration drift all cause explicit errors. Do not change the task ID to bypass an unknown state, and do not release the lease. Repeated operations with an already saved receipt continue returning the original run ID.

The intent, dispatch checkpoint, receipt and any applicable ownership-rejection record are stored in the execution-state directory at `ergora/task-submissions/TASK_ID.{intent,attempt,result,rejection}.json`. Keep them with creation records, the task directory and original run state. The preparation stage retains the current project revision and acquires the original same-ID lock without blocking, saving only the intent. It then releases the control-database write lock; the network stage holds only the original task lock. The 1–60-second timeout applies separately to preparation and network stages. The parent process provides each with another 5 seconds for startup/reaping; prechecks are separate. A timeout reaps only the submission client. The persistent executor owns actual Agents, so a client timeout does not establish a stop. An incomplete environment fails explicitly without automatically starting services or changing execution permissions.

APIs: `POST .../tasks/TASK_ID/start` with body `revision/creation_sha256/timeout`, `GET .../tasks/TASK_ID/submission`, and `POST .../tasks/TASK_ID/resume-start` with body `revision/intent_sha256/timeout`. Write requests retain same-origin protection and `X-Ergora-Request: 1`. Concurrent preparation or creation/resume-create for the same task returns busy promptly when its task lock is active. Concurrent reads may observe prepared/unknown snapshots without waiting for the other request to finish. After the operation, read submission and the current project revision before deciding whether to explicitly resume. Repeating start does not implicitly retry undispatched admission, and unknown does not resend. Other projects do not have the control-database write lock continuously occupied by this network wait. Even an HTTP success response requires checking status; unknown/rejected cannot be treated as successful submission.

## Fixed verification evidence and recovery

For projects declaring [fixed CPU text checks](../projects/registration.md#fixed-cpu-text-checks), the original verify Job runs the frozen scripts and publishes complete observations/comparisons in `check-results`. Poll and review independently read that artifact against the original admission, creation, candidate and process records. A passing result proves only the declared cases/material obligations; the reviewer may still request changes.

Each check's wall allowance is the minimum of its declared cap, the original verification stage cutoff and the original task work budget. The job owner freezes the stage cutoff before constructing the executor; setup, materialization, Git reading, parsing and publication consume it. The native monitor checks that same cutoff immediately before launch and during execution, including fractional remaining time. Recovery retains the saved cutoff. Cancellation or cutoff prevents the next admission; the existing budget owner and supervised process tree retain cleanup responsibility. A process terminal alone does not prove whole-tree cleanup.

An original process request/started record without a confirmed terminal remains unknown, even after the outer owner confirms that its descendants were reaped. The original job retains occupancy and cannot rerun a script to fill missing evidence. An unrelated unfinished process publication does not block this job's recovery. Recovery may collect complete saved pending evidence when collection has never been attempted; an uncertain collection remains unknown. Keep original process records, output/source/input bytes, scope and baseline evidence, and the complete check artifact with the task's existing budget and creation records. Do not replace missing output, renew a clock or change IDs to obtain a passing result.

## Run registered fixed checks on an exported candidate

On Linux/WSL2, use the registered reference runtime and the same control home throughout. Read `task export-status PROJECT SOURCE_TASK_ID` to obtain the saved `exported` receipt, source run ID, full SHA-1 candidate and export intent digest. Prepare a local review packet with that same candidate as its head, and retain `packet_sha256`. Obtain the current `revision` and `verification.snapshot_sha256` from `project registration PROJECT`. [Export a candidate](evidence-and-export.md#export-an-exact-candidate-and-recover-its-receipt) · [Prepare a local review packet](../review/materials.md#prepare-materials)

Freeze a complete review manifest and retain its `digest`. Select a read-only reviewer leaf directly beneath the pinned `ergora-correctness-review@1.0.2` subworkflow. The bundled `engineering-review` preset provides `root/correctness/review` in `ergora-delivery-review@1.2.6`. The leaf must receive the root task directly and have read scope for the packet's paths. [Freeze an exact manifest](../definitions/workflows/compose.md#save-and-share-a-complete-composition)

Save the following fields in `candidate-check.json`, replacing placeholders with the original values and absolute packet and manifest directory paths. Set integer allowances with `1 <= cleanup_seconds < wall_seconds <= 3600`. Cleanup is reserved within the wall allowance.

```json
{
  "task_id": "SOURCE_TASK_ID",
  "run_id": "SOURCE_RUN_ID",
  "candidate_sha": "CANDIDATE_SHA",
  "export_intent_sha256": "EXPORT_INTENT_SHA256",
  "verification_sha256": "VERIFICATION_SHA256",
  "packet": "/absolute/path/to/review-packet",
  "packet_sha256": "PACKET_SHA256",
  "manifest": "/absolute/path/to/review-manifest",
  "manifest_digest": "MANIFEST_DIGEST",
  "instance": "root/correctness/review",
  "wall_seconds": 300,
  "cleanup_seconds": 20
}
```

Review the exact request bytes. Hash that file and explicitly confirm one stable operation ID.

```bash
REQUEST_SHA256=$(sha256sum ./candidate-check.json | cut -d ' ' -f 1)
ergora task candidate-check PROJECT OPERATION_ID --request ./candidate-check.json \
  --request-sha256 "$REQUEST_SHA256" --revision CURRENT_REVISION --confirm
ergora task candidate-check-status PROJECT OPERATION_ID
```

The registered executor watcher can consume the saved request. Direct execution uses the same executor lock. For single-request mode, set `JOB_ID` to the returned `job_id` and `EXECUTION_STATE` to `registration.definition.execution.state_directory` from `project show PROJECT`. Use the saved envelope in place.

```bash
ergora reference executor --project PROJECT \
  --request "$EXECUTION_STATE/requests/fixed-candidate-check/${JOB_ID%-*}/$JOB_ID.json"
```

After a lost reply, use `candidate-check-status` with the same operation ID to read its original Job. Supply its returned SHA256 to pin subsequent reads or request a stop.

```bash
ergora task candidate-check-status PROJECT OPERATION_ID --job-sha256 JOB_SHA256
ergora task candidate-check-stop PROJECT OPERATION_ID --job-sha256 JOB_SHA256 --confirm
```

A stop fences only that check Job. `stop_requested` records the fence. The final checker launch and successful terminal publication use the same scoped admission gate. When the original clock is unusable before work, a durable `body_started: false` observation supports finalizing that original refusal without resubmitting a checker or claiming descendant cleanup. If an original checker terminal is missing, the Job can remain `unknown` even with `outer_cleanup_confirmed: true`. Repeating an existing operation ID with the identical authorization only reads the original records, including `request_not_observed` if its saved permit has no visible request. The original attempt and clock still apply.

A verified terminal receipt supplies `receipt_sha256`. When present, `fixed_results_sha256` identifies the report of registered fixed checks, observations and comparisons for the candidate. The separate Job covers fixed checks only. The source task's formal verification, review and candidate release retain their original evidence and authority.

## Request cancellation and recover unknown delivery

Tasks created through the unified entry point with their original submission receipt saved can request cooperative cancellation pinned to the original run. As with approval, use the current project revision, a stable request ID and explicit confirmation. The reason must be nonempty and at most 1000 characters:

```bash
ergora task cancel my-project TASK_ID --request-id stop-one --revision 1 --run-id RUN_ID --reason 'Owner requested stop' --confirm --timeout 20
ergora task cancellation my-project TASK_ID stop-one
# After an interruption, read cancellation first and recover the same request with its original intent_sha256:
ergora task resume-cancel my-project TASK_ID stop-one --revision 1 --intent-sha256 CANCELLATION_SHA --confirm --timeout 20
ergora task status my-project TASK_ID --run-id RUN_ID --timeout 20
```

`cancellation` checks only local records without connecting to Temporal. `prepared` has no dispatch checkpoint yet, so explicit recovery can continue the original cancel. `unknown` has a checkpoint but unconfirmed delivery; it can only check the complete signal containing this operation's SHA in the original run history. It cannot claim another request merely because the reason matches, and does not resend. Repeating the same ID retains the original reason/actor without generating a second request. Do not change the ID to bypass uncertainty; first check original-run and external-job facts.

`requested` and `cancel_requested: true` mean only that the signal was acknowledged or the original history has a corresponding event. `already_closed` means the original run was closed when checked for this operation; `cancel_requested: false` and `signal_delivery: not_sent` explicitly mean no new signal was sent. Repeated reads return saved facts rather than a new live query. CLI mutations return 0 for either state, but the status fields must still be checked. `cancellation_confirmed: null` and `execution_success: null` do not establish stopped execution. Use `task status --run-id` to check the original phase/outcome. Continue reconciling CANCEL_UNCONFIRMED/NEEDS_RECONCILIATION with the original fence and external jobs; do not delete the ledger, terminate, or automatically release unconfirmed leases.

Intent/attempt/result records are stored in the execution-state directory at `ergora/task-cancellations/TASK_ID/REQUEST_ID.*.json`. Keep them with the original task, creation and submission records. Preparation acquires the original task lock without blocking under the current revision. The remote stage releases the control-database write lock. Each stage has a 1–60-second budget, with another 5 seconds from the parent process for each; local prechecks are separate. Windows uses the registered complete Linux/WSL2 runtime. This local entry point is not a team permissions system.

The API is GET/POST `.../tasks/TASK_ID/cancellations/REQUEST_ID`. The POST body is `revision/run_id/reason/confirm/timeout`; POST to the same path's `/resume` uses `revision/intent_sha256/confirm/timeout`. Strict confirmation must be true. Write requests retain same-origin protection and `X-Ergora-Request: 1`. Tasks from the old entry point remain managed by the original CLI.

## Close after normal task completion

`REVIEW_READY` means the original candidate passed the workflow's required validation and review. Closing a workflow does not automatically release an issue lease. To adopt the candidate, explicitly [export it](evidence-and-export.md#export-an-exact-candidate-and-recover-its-receipt) and check the receipt; that entry releases applicable leases under the original rules. If not exporting yet or only ending this task, first check evidence and explicitly reconcile:

```bash
ergora task external-status my-project TASK_ID --run-id RUN_ID --timeout 20
ergora task reconcile my-project TASK_ID --revision CURRENT_REVISION --run-id RUN_ID --confirm --timeout 20
ergora task reconciliation my-project TASK_ID
```

First confirm that the original run is closed, original jobs and trusted terminal receipts/artifacts are complete, and no extra or unresolved job remains. Without the correct fence, an initial read-only external_confirmed check may still be false; it publishes no fence and releases no lease. Only explicit reconcile establishes the original execution fence, rechecks facts and releases the exact claim. Missing evidence remains unknown. Verify stopped external processes through the actual executor; trusted-file receipts cannot replace OS checks.

Reconciliation retains normal REVIEW_READY and the exact candidate, without merging or deleting branches. The same candidate can still be exported explicitly afterward. Only reconciled means this lease release and receipt have been saved; recover interruptions through the original intent below. Downloading a handoff package, closing browser/HTTP or stopping services does not release a lease. Before stopping a shared stack, check its projects' in-flight tasks and external jobs individually, then [manage services](../operations/services.md#manage-services-explicitly) to exit and back up persistent directories.

## Explicitly reconcile terminal state and release issue leases

After the original run closes, use the current project revision and fixed original run to explicitly authorize the fence and external-cleanup checks:

```bash
ergora task reconcile my-project TASK_ID --revision 1 --run-id RUN_ID --confirm --timeout 20
ergora task reconciliation my-project TASK_ID
# After interruption or completing original trusted receipts, resume with the original intent_sha256 returned above:
ergora task resume-reconcile my-project TASK_ID --revision 1 --intent-sha256 RECONCILIATION_SHA --confirm --timeout 20
```

This only takes responsibility for tasks created through this control directory's unified entry point, with original submission receipts and original `local-cli` issue ownership retained. Before and after reconciliation, verify the original run is still current, complete original history and the registered adapter directory. Extra requests/orphan receipts block taking over that scope. After publishing the original immutable fence, confirm every historical job's original request, trusted terminal receipt and hashed artifacts. Missing/damaged evidence remains unknown and retains the lease. Trusted executors must still honor fences and independent walltime. This file-protocol evidence does not replace a system process scan. All coordinators must keep task IDs nonreusable and must not start a new run for the same task outside the protocol.

`reconciliation` reads only local records, without querying remotely, publishing a fence or releasing a lease. `prepared` has no saved write-ahead checkpoint. `unknown` has saved original outcome/history identities but incomplete cleanup evidence. `confirmed` has saved cleanup evidence but no saved release receipt. Only `reconciled` means the lease was released for the exact original claim and its receipt saved. Recovery revalidates original facts and advances idempotently with the same fence/evidence digests. Repeating reconcile returns saved state; only explicit resume-reconcile continues an unfinished operation. A completed receipt is historical fact; use external-status for live external state.

`original_outcome` retains the actual original result. Even if it was CANCEL_UNCONFIRMED, confirmed cleanup does not change it to BLOCKED or successful development. `execution_success: null` makes no claim about candidate acceptance. Preserve the original outcome digest when native release applies; other closed-run cleanup uses a separate cleanup-evidence digest. Do not manually edit owners/ledgers or delete evidence to bypass conflicts. A mutating CLI returns 0 only for reconciled; HTTP success also requires checking status.

API: GET `.../tasks/TASK_ID/reconciliation`, POST `.../tasks/TASK_ID/reconcile` (`revision/run_id/confirm/timeout`), POST `.../tasks/TASK_ID/resume-reconcile` (`revision/intent_sha256/confirm/timeout`). confirm must be exactly true. Mutations retain same-origin protection and `X-Ergora-Request: 1`. Linux/WSL2 uses the registered complete runtime. Each stage allows 1–60 seconds, with another 5 for the parent and separate local preflight. The original task lock protects that task; remote phases hold no control-database write lock.

Back up execution-state files `ergora/task-reconciliations/TASK_ID.{intent,attempt,evidence,result}.json` together with the original task/creation/submission, requests/receipts/artifacts/fence and `ingress/leases.sqlite3`. Missing evidence or a database retains unknown state; a new ledger must not reconstruct ownership.

Continue: [Review design material and approve an exact plan](design-and-approval.md) · [Read original evidence and export a candidate](evidence-and-export.md).
