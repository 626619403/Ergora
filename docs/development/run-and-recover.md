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

`submission` checks only the local submission record without connecting to Temporal. `status: submitted` means the original workflow/run ID receipt is saved; `execution_success: null` does not mean the six stages succeeded. Query progress with `task status --run-id RUN_ID`. Repeated start returns only the original local record without resubmitting. `not_recorded` means no submission intent exists. `prepared` means an intent exists but no dispatch checkpoint has been saved. `unknown` means the checkpoint is saved but the original call's result is unknown. `rejected` means an existing run not belonging to this submission was found and the rejection record preserved. A mutation command reports CLI success only for submitted.

The immutable intent is saved first, followed by original admission/claim. An attempt is saved before the actual start, and the native receipt is saved last. prepared can repeat admission through an explicit resume while reusing the same lease. unknown can only query original input under the original workflow ID and fill in the receipt; even NOT_FOUND does not permit resending. A crash after writing the checkpoint but before the actual RPC also retains unknown and requires manual reconciliation. An existing run is rejected rather than taken over; later disappearance of its history does not automatically restart it. The original start associates this submission-intent digest in Temporal memo, and unknown recovery also checks that marker. Missing or different markers prevent adoption as this submission. An AlreadyStarted response from a submission race is persistently rejected without adopting another entry point's run. Original input is compared exactly by canonical JSON digest, distinguishing true/1/1.0. Original-input mismatch, RPC failure and contract/registration drift all cause explicit errors. Do not change the task ID to bypass an unknown state, and do not release the lease. Repeated operations with an already saved receipt continue returning the original run ID.

The intent, dispatch checkpoint, receipt and any applicable ownership-rejection record are stored in the execution-state directory at `ergora/task-submissions/TASK_ID.{intent,attempt,result,rejection}.json`. Keep them with creation records, the task directory and original run state. The preparation stage retains the current project revision and acquires the original same-ID lock without blocking, saving only the intent. It then releases the control-database write lock; the network stage holds only the original task lock. The 1–60-second timeout applies separately to preparation and network stages. The parent process provides each with another 5 seconds for startup/reaping; prechecks are separate. A timeout reaps only the submission client. The persistent executor owns actual Agents, so a client timeout does not establish a stop. An incomplete environment fails explicitly without automatically starting services or changing execution permissions.

APIs: `POST .../tasks/TASK_ID/start` with body `revision/creation_sha256/timeout`, `GET .../tasks/TASK_ID/submission`, and `POST .../tasks/TASK_ID/resume-start` with body `revision/intent_sha256/timeout`. Write requests retain same-origin protection and `X-Ergora-Request: 1`. Concurrent preparation or creation/resume-create for the same task returns busy promptly when its task lock is active. Concurrent reads may observe prepared/unknown snapshots without waiting for the other request to finish. After the operation, read submission and the current project revision before deciding whether to explicitly resume. Repeating start does not implicitly retry undispatched admission, and unknown does not resend. Other projects do not have the control-database write lock continuously occupied by this network wait. Even an HTTP success response requires checking status; unknown/rejected cannot be treated as successful submission.

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
