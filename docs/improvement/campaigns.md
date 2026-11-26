# Record a finite optimization campaign

English · [Documentation](../README.md)

The local Unix operator can record the goal, acceptance criteria, baseline commit, evidence format and absolute expiry of a campaign. The original Temporal workflow records the passage of that deadline. Ordinary plans are record-only. An explicit Codex recipient on the timed-readback task can authorize one continuation of an existing native session.

Use an existing published project and explicitly bind its scheduler to the selected trusted Temporal service. Install the existing `ergora[temporal]` extra for `create`, `worker`, `stop`, `observe-check`, `rollover` and online `status`. The operation uses the protected control home's owner and the CLI process's effective UID. This is local-process assurance. The current scheduler uses the configured address and namespace and relies on the selected service's access controls. [Project registration](../projects/registration.md) · [Configure Temporal](research-and-schedules.md)

Save a UTF-8 JSON file with these fields. Set `baseline_commit` to the full Git object ID you intend to use and replace `expires_at` with a future integer UTC Unix second.

```json
{
  "schema_version": 1,
  "goal": "Compare the candidate against the recorded baseline",
  "acceptance": "Record the exact candidate and matching verification result",
  "baseline_commit": "0123456789abcdef0123456789abcdef01234567",
  "evidence_format": "Candidate digest and original verification receipt",
  "limits": {"expires_at": 1795590000}
}
```

Run the create command with the current published project's revision and the SHA-256 of the exact approved file bytes. The response reports the original Workflow and first Run, the plan SHA-256 and the saved scheduler. Use the same `--home` for all campaign commands.

```bash
ergora campaign create my-project first-plan campaign.json \
  --revision PROJECT_REVISION --plan-sha256 PLAN_FILE_SHA256 --confirm

ergora campaign worker my-project first-plan
```

The worker runs in the foreground on the campaign's dedicated queue. It follows a verified opted-in rollover on that queue and exits when the Campaign closes. If you interrupt it, run the worker command again to process the original workflow. When Temporal accepts the start before a worker is ready, the first worker processes the original deadline. It can also close an original run after the deadline has passed.

```bash
ergora campaign status my-project first-plan
ergora campaign status my-project first-plan --online
```

Offline status reads the saved start, stop and task attempts without the SDK. Saved task entries include their local Run and Update IDs and report `status: not_requested`. Online status verifies the original start History and reports the Temporal run and any observed workflow state separately. A running workflow may have state unavailable while its worker is offline. The expiry phase is reported when the original completion can be verified.

After an uncertain start, read `status --online` and repeat `create` with the same project, campaign, exact plan bytes, revision and digest to save the verified original start. Once the dispatch attempt is saved, repeated `create` observes the same original start even if the current project scheduler changed. An unavailable service or missing original History leaves that attempt uncertain.

## Manage one Campaign Worker

On Linux/WSL2, use the Supervisor from the Campaign's original registered reference installation. After `campaign create` saves and verifies the original Run, manage its Worker through the same control home.

```bash
ergora campaign worker-service my-project first-plan start
ergora campaign worker-service my-project first-plan status
ergora campaign worker-service my-project first-plan stop --confirm
```

The service owns one Worker on the saved Campaign queue. It remains active after the launcher exits. Supervisor replaces a Worker that exits unexpectedly after successful startup. The same Campaign and process ownership checks govern each replacement. A competing foreground call is refused while the managed daemon owns this queue.

`worker` reports Supervisor's process state. `queue` reads the original Workflow Task Queue from the original scheduler. Temporal can retain recently exited pollers. `queue.managed_poller_report` matches the cached report to the observed managed generation. `queue.managed_polling: observed` also requires a bounded query of the original Run and the same live process generation across the read. A suspended process can have a reported poller while its readiness is `suspended`. The queue also reports unavailable or unknown evidence and a verified original closure.

`worker-service stop --confirm` shuts down that Campaign's Supervisor and drains its local Worker. A later explicit start can resume polling an open original Run. To finish the Campaign, deliver the original [Campaign STOP](#stop-the-original-campaign-plan) while its Worker is available. Workflow closure lets the Worker exit. Use `worker-service stop` to release the remaining service owner. View the original Workflow, native execution and resource receipts for their respective outcomes.

Maintenance keeps the Worker while the original Campaign command holds its lock or a saved STOP still needs the Worker. An unconfirmed stop reports `campaign_control_busy` or `campaign_stop_unresolved`. Read the original STOP and Run again, then retry maintenance after closure. After a lost Campaign STOP reply, the original command reconciles the same Update ID. If the entire managed service disappears during an unresolved STOP, reconcile the original owner and History before restoring polling. An unresolved Update keeps its original attempt identity.

Service control uses a 1–60 second wait after preflight. `control_outcome` reports the local effect and a confirmed start also requires original queue readiness. A concurrent start or stop that encounters the original control lock reports `worker_control_busy` with an unconfirmed outcome. Read the original service status before retrying. The original Campaign owner checks closure and saved STOP again before starting the Worker. The Campaign's deadline keeps running. The managed Unix socket and logs are under `campaigns/PROJECT/CAMPAIGN/svc` in the control home. Keep this path within the Unix socket limit.

## Continue one Campaign with a pending fixed check

Before creation, set `"rollover": true` in a record-only plan with exactly one pending fixed-check task. Use manual `observe-check` for this task. Plans that configure a timed readback or recipient cannot opt in. Use the [pending fixed-check instructions](#observe-an-original-check-that-is-still-pending) to freeze the original Job and record its waiting receipt. The Job's own executor and authorization continue to govern it.

While the Campaign is open, the same local operator can commit a single Continue-As-New on the original queue.

```bash
ergora campaign rollover my-project first-plan --confirm
ergora campaign status my-project first-plan --online --task-id verify-candidate
```

The rollover keeps the original goal, absolute deadline, waiting receipt and native Job locator. Online status retains the immutable first `run_id`. It exposes `current_run_id` and `rollover.status: verified` after checking both Temporal Run histories and the original waiting and rollover Update decisions. A verified continuation can be observed while the Worker is unavailable. Restart the foreground Worker or its existing service owner to continue processing the same queue.

If the rollover reply is lost, repeat the same command to reconcile its saved Update ID. An unresolved rollover fences new Campaign observations and STOP until the original attempt can be verified. Missing or conflicting predecessor evidence prevents new effects. An earlier saved STOP or a saved terminal task attempt also prevents new rollover. The original Job stays with its executor during all of these reads.

After verification, use `observe-check` again to record the same Job's terminal receipt, and the usual `stop --confirm` to stop the current Campaign Run. The task timeline reports the original Run ID for each accepted Update. The waiting Update remains in the first Run, and the new terminal observation and STOP bind to the verified successor.

## Stop the original campaign plan

Use the same local Unix operator and control home. The confirmed stop binds one request to the saved scheduler and original first Run or its verified opted-in successor.

Run the current `ergora campaign worker` on the original campaign queue to deliver STOP to Temporal. If an older worker lacks the STOP handler, shut it down normally before starting the current worker. With an authorized Codex recipient and a pinned first Run, the confirmed operation also saves the local native STOP fence even when Temporal or its Worker cannot receive the Update.

```bash
ergora campaign stop my-project first-plan --confirm
ergora campaign status my-project first-plan --online
```

An unavailable Worker check returns exit 1 with `stop.remote_status: worker_unavailable` and `stop.retryable: true`. A record-only Campaign leaves the stop intent unrecorded. An opted-in native recipient can show `stop.local_fence_saved: true` with a prepared intent and no Update attempt. Retry the same command once the current Worker is running to send that original intent.

After a lost reply, read online status and repeat the same stop command to reconcile the saved attempt and save its verified decision. Once an attempt exists, `stop.retryable` is `false` and the command observes the original `stop.update_id`. An unavailable service or missing decision leaves that attempt uncertain. An already closed Run at preflight returns its original terminal status.

Read `stop.status` for progress and `stop.receipt.decision` for the verified Update outcome. `accepted` records the original Workflow's decision to stop, and `expired` records that the original deadline took effect. The command can return exit 0 for an accepted receipt before closure is verified. Use online `temporal_status` and `workflow_state.phase` to check the original terminal outcome. For the selected native recipient, its own `recipient.native_receipt.run.execution_stopped` records confirmed process cleanup. The original Job and resource owners supply their own stop and release evidence.

## Record an original fixed check for a task

Before creation, a plan can include one to eight tasks in `tasks`. A fixed-check task declares a unique `task_id`, a list of distinct task IDs in `depends_on` and an exact fixed-check `source`. Dependencies stay within the frozen plan and form an acyclic graph.

For this example, start with a `campaign.json` that has a future expiry. Save the `task candidate-check-status` JSON for two original Jobs under the same project and protected control home as `baseline-check.json` and `candidate-check.json`. Use already authorized, successful checks with confirmed cleanup and `stop_requested: false`. The source retains the original Job's `project_revision`, which can differ from the campaign's project revision. [Original fixed-check status](../development/run-and-recover.md#run-registered-fixed-checks-on-an-exported-candidate)

```bash
python3 - <<'PY'
import json
from pathlib import Path

fields = (
    "operation_id", "request_file_sha256", "job_sha256", "candidate_sha",
    "receipt_sha256", "fixed_results_sha256", "project_revision", "job_id",
    "authorization_sha256", "verification_sha256",
)

def source(path):
    status = json.loads(Path(path).read_text(encoding="utf-8"))
    return {field: status[field] for field in fields}

plan = json.loads(Path("campaign.json").read_text(encoding="utf-8"))
plan["tasks"] = [
    {"task_id": "verify-baseline", "depends_on": [], "source": source("baseline-check.json")},
    {"task_id": "verify-candidate", "depends_on": ["verify-baseline"], "source": source("candidate-check.json")},
]
with Path("campaign-with-checks.json").open("x", encoding="utf-8") as output:
    json.dump(plan, output, indent=2)
    output.write("\n")
PY
```

Use the create command above with the new campaign ID `fixed-check-plan`, the current project revision and the SHA-256 of the exact `campaign-with-checks.json` bytes. Run the current worker on that campaign's original queue.

```bash
ergora campaign observe-check my-project fixed-check-plan verify-baseline --confirm
ergora campaign status my-project fixed-check-plan --online
```

Online status reports `tasks` by ID. Confirm `verify-baseline` is `observed` and `verify-candidate` has `status: ready` and `eligible: true` before submitting the dependent observation.

```bash
ergora campaign observe-check my-project fixed-check-plan verify-candidate --confirm
```

`observe-check` verifies the original passing Job, cleanup and source identities before recording the observation. Its result reports `campaign_project_revision` and `job_project_revision` separately. After an uncertain reply, read online status and look up the saved `update_id`. When task state is available, a saved unresolved attempt shows `attempt_status: unknown` and `eligible: false`. STOP and expiry close admission for new observations. The original receipts remain readable, including by reconciliation of a saved attempt. The fixed-check executor retains Job ownership and authority.

When live task state is unavailable, `status --online` reports saved attempts in `task_observation_history` by task ID and stage (`waiting` or `terminal`). A `verified` entry includes the receipt and its matching accepted and completed Update event IDs on the original Run. A `failed` entry includes the two event IDs when the accepted Update completed with a failure. It carries no observation receipt. `unresolved` means readable History did not establish a completed outcome for that attempt. `unavailable` means the original History could not be read. Each entry retains its original Run and Update IDs. Use this view to recover a lost reply without submitting an observation. Task eligibility requires current Workflow state.

To check the Update and the original Job together after a lost reply, select the frozen task explicitly.

```bash
ergora campaign status my-project fixed-check-plan --online --task-id verify-baseline
```

`task_observation_history` identifies the original Update and any verified completion. `task_evidence.native_job` carries the original Job status, result and cleanup fields on the saved registration. Its `native_observation_sha256` hashes the complete current payload. `correlation: matched` requires that digest to equal the verified terminal Update receipt's `observation_sha256`, with the original Job identity and terminal fields in agreement. `different_observation` means those fields agree and the complete payload digest differs. `pending` means the Job is readable and agreement is still unconfirmed. `unavailable` means the original Job evidence is missing or unknown. `contradictory` means the original owner rejected the exact Job digest or the original identity or terminal fields differ.

If the original task History reader refuses an inconsistent event, `task_observation_history_status: contradictory` reports the failure and the saved Run and Update IDs remain visible. The command still reads the independently owned Job status. A contradictory History, or `unavailable`, `contradictory` or `different_observation` Job correlation, yields exit 1. Omitting `--online` reads the Job and saved local Update identities without consulting Temporal. Both forms are read-only and remain available after Campaign expiry or STOP while the original evidence is readable. Use the original owner for actual process liveness or resource release.

If the current application reports an unsupported reference runtime identity, the separately verified History remains readable. For a retained older run, select its exact original Ergora application and registered reference installation from the release or retirement inventory. From that application, use the same protected control home and run `task candidate-check-status PROJECT OPERATION_ID --job-sha256 JOB_SHA256`. Take `operation_id` and `job_sha256` from `task_evidence.source`. If the original pair is unavailable, native correlation remains unavailable. [Retain the original application and data](../install/upgrades.md#upgrades-and-persistent-data)

### Observe an original check that is still pending

Before freezing the plan, read the already authorized Job with `task candidate-check-status` under the same project and protected control home. Use the source fields from the example above, set `source.pending` to `true` and omit `receipt_sha256` and `fixed_results_sha256`. Copy the other eight fields exactly. If you need to configure the campaign scheduler, do so before authorizing a Job that has yet to launch. Preserve the original Job's project revision through launch.

Use the same confirmed `observe-check` command once the task's dependencies are observed. A verified `queued` or `attempted` Job yields `status: waiting_job`. An original executor rejection blocks this observation, even when the historical Job status still reports `queued` or `attempted`. Dependent tasks wait for `observed`. Repeat the command to check again. While the Job is still pending, the command returns its saved waiting receipt and `update_id`. A passing original Job with confirmed cleanup yields `status: observed` in a terminal Update. Its `receipt.job` contains the original `receipt_sha256` and `fixed_results_sha256`, plus `waiting_receipt_sha256` when a waiting receipt preceded it. A Job that has already passed at first observation can go directly to `observed`. Online task status retains the first `waiting_receipt` alongside any terminal `receipt`.

After an uncertain reply, use online campaign status to read the saved stage. A confirmed command can advance a verified waiting task in the live Workflow by reading the original Job again. A fresh Job status read is bounded by the campaign's original deadline. A locally saved, accepted STOP or operator cancellation interrupts and reaps the local status reader. STOP and the original deadline close admission for new waiting and terminal observations. Use `task candidate-check-status` for the original Job's later outcome and cleanup. The original executor retains Job control. Any resource release requires evidence from the original resource owner.

### Allow one timed readback of a waiting check

To opt in, add `"readback": {"due_at": DUE, "deadline_at": DEADLINE}` to one task in the frozen plan with `"pending": true` in its `source`. Use positive integer Unix seconds with `due_at < deadline_at <= limits.expires_at`. Run the current Linux campaign Worker on the original queue and control home. The first accepted `waiting_job` receipt arms one read of that exact Job. If `due_at` is still in the future, one Timer waits for it. When `due_at` has arrived and the original window still leaves time for cleanup, the Workflow schedules the Activity immediately without starting a Timer. Worker replacement preserves the original window and single attempt. A direct terminal observation leaves the timer unarmed.

Online status reports `readback_observation` for the opted-in task. It starts at `not_armed`. `armed` identifies a bound waiting receipt and `scheduled` identifies an Activity request. `available` links `activity_id` and `waiting_receipt_sha256` to the original `receipt_sha256`, `fixed_results_sha256`, `observation_sha256` and `reader_cleanup_sha256`. `unknown` gives the reason, such as an unavailable or still-pending original read, a closed campaign or an already observed task.

When the Worker cannot return Workflow state, `status --online` can show `readback_completion` for a passing Activity recorded in the original Temporal History. This includes the original schedule and completion event IDs, the accepted waiting receipt digest and the readback proof digests. Current Workflow state remains unavailable until the Worker can return it.

Use a confirmed `observe-check` to verify the original Job, record its passing terminal receipt and make dependents eligible. Reader cleanup covers the local status reader. Read any late Job outcome through the original fixed-check status and obtain resource release evidence from the original resource owner.

### Authorize one local Codex recipient

Add `recipient` to the one task with a timed readback. Select an existing persistent native Codex session in the same published project and revision. Use its latest stopped turn as `parent_run_id` and choose a new stable `intent_id`. The existing native session supplies the approved role, settings and workspace policy. This entry uses the selected installed Linux Codex ELF and the same protected local control home. A session whose installed executable cannot be pinned to that payload is refused at Campaign creation.

```json
{
  "session_id": "SESSION_ID",
  "parent_run_id": "LATEST_STOPPED_RUN_ID",
  "intent_id": "read-original-check",
  "prompt": "Use the original verification result to summarize this candidate.",
  "timeout_seconds": 60
}
```

Supply those fields as the `recipient` object's value and confirm the exact plan bytes with the existing `campaign create` command. The opening freezes the native recipient and original prompt. The normal `campaign worker` schedules one authorized continuation after one successful original timed readback. The launch helper verifies the installed binary under a Linux read lease and keeps its ordinary installed pathname through exec. An attempted write that breaks the lease terminates the inert helper. The launch gate observes the original native clock and the Campaign expiry while waiting for its lock and before exec. The original native session lock and process owner retain reservation and cleanup. Local STOP publication is serialized with the protected exec handoff. The running native owner observes a saved STOP or the original cutoff and reaps its process tree.

Read `recipient` in Campaign status for local attempt evidence, optional exact wake History, and the native continuation receipt. A verified pre-reservation rejection can report a blocker such as `stale_parent` or `session_slot_timeout`. `native_start` advances only when the original process owner observes the selected Codex payload. Use `run.native_session` for the separately verified native thread and outcome. If the Activity reply or native launch evidence is incomplete, retain the original intent and read status again. Worker replacement processes the pinned Run. An uncertain original dispatch stays bound to the same attempt and receives no replacement authorization.

When online status verifies the original wake History, `recipient.history.timing` shows the event IDs and Temporal timestamps for readback readiness, scheduling, Worker start and delivery termination. Intervals use nanoseconds from the same History clock. Missing or reversed timestamps leave the affected interval null. Use the original native receipt for actual payload start and cleanup.

### Admit the guarded result or a confirmed observation

Set `"wake_on_observe": true` on the one task with the frozen recipient and timed readback to use either source for the same task and native continuation. First record the original pending Job with `observe-check --confirm`. A later confirmed passing observation binds the accepted wait and can supply the wake at the original due time. The guarded Activity can also supply the original passing result and make the task's dependents eligible. Both routes use the original readback window, recipient, STOP and Campaign deadline. A passing observation before the original waiting receipt can be recorded without arming a wake.

When the guarded result arrives first, the opted-in task is `observed` with its Activity proof and a null terminal Update receipt. While the Campaign can report live task state, a subsequent `observe-check` can return that original Activity completion. A manual wake records its terminal Update and identifies it in `recipient.history.intent.source`. A manual result accepted while a guarded read is running can drive the continuation before the reader finishes. The Activity keeps its original deadline and cleanup owner.

After the Campaign closes or when the Worker is unavailable, use online status to read the original History.

```bash
ergora campaign status my-project fixed-check-plan --online --task-id verify-baseline
```

Read a verified guarded result in `readback_completion`. If an identical manual Update lost the race, its terminal entry in `task_observation_history` retains the original Run and Update IDs, the accepted and completed event IDs, `status: failed`, `reason: readback_already_admitted` and `receipt: null`. The Activity still supplies the original result. Neither a status read nor a repeated observation delivers a second continuation.

### Read one managed training full result

A record-only plan can include one root task whose source is `{"kind":"training_full_result","locator":{...}}` and whose readback specifies `due_at` and `deadline_at`. The locator requires `experiment_id`, `workflow_id`, `run_id`, `job_id`, `native_request_sha256` and `attempt_sha256` from the same project's original managed full verification. Bind Temporal before authorizing that training attempt so its registration and project revision match the Campaign.

The original Run arms the one guarded read from the confirmed plan. The exact successful native result and archive evidence make the root task observed. The readback records the result digest and the original resource owner's independent lease observation. A fixed-check task can depend on that result and still requires its own original authorization and confirmed observation.

To authorize one native continuation when this exact result is observed, add the existing `recipient` declaration to the training root task. The same registered project and revision supply the already stopped native Codex parent and its approved prompt. Result evidence and lease observation stay in the Campaign receipt. The original verified Activity result triggers that one continuation.

Use `campaign status PROJECT CAMPAIGN --online --task-id TASK` for the original verified result, Activity and any recipient evidence, including after the Worker exits. The Campaign STOP and read cutoff bound this reader. The original training executor and resource owner keep control of their operations.

### Read one managed training screen decision

Use `{"kind":"training_screen_result","locator":{...}}` for a root task that reads an original managed screen. Supply the same six locator fields and the original `due_at` and `deadline_at` window. An optional `recipient` uses the existing frozen session, parent and prompt to wake one authorized expert.

For the selected task, `campaign status PROJECT CAMPAIGN --online --task-id TASK` returns the original `SCREEN_COMPLETED` or `SCREEN_REJECTED` state, its literal decision, diagnostic references and a separate lease observation. A verified rejection is decision evidence and can wake the selected recipient. Any later full comparison uses its own prepared experiment and original execution grant.
