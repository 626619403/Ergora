# Submit, execute and recover a training experiment

English · [Documentation](../README.md)

Use an [already prepared experiment](prepare-experiments.md) and its original registered context. Read existing records before recovering an uncertain submission; create no new experiment ID to bypass that uncertainty.

## View original experiments in the console

First use `project register` as described in [project registration](../projects/registration.md) to register an existing Git project, select `training-optimization`, and specify native reference installation, configuration and execution-state directories. Existing original experiments retain their directories and identities; no second experiment database needs importing. Base-installation list/details require no running Temporal, MLflow or GPU. Configure [current native sources](prepare-experiments.md#prepare-versioned-native-sources) first; live queries and explicit execution use their separate operations on this page.

```bash
ergora training list my-project --limit 20
ergora training list my-project --limit 20 --after CURSOR_FROM_PREVIOUS_PAGE
ergora training show my-project EXPERIMENT_ID
```

Open “训练实验” in the console to view the current baseline, paginated original experiments, complete manifests/specs, current runner and frozen job requests, execution results, gate-report summaries, cancellation fences, negative results and existing MLflow run IDs. Complete originals include file SHAs; current-baseline mismatches are explicit. The page also lists this project's existing Forge candidate records; native candidate actions remain in the workflow designer's training template.

CLI, page and `GET /api/projects/{project}/training[/{experiment_id}]` share one read-only query. List `limit` is the number of entries actually inspected per page. Bad entries have separate errors and advance the cursor so later experiments are not hidden. Each JSON file is read up to 1 MiB; out-of-bounds paths and symlinks are rejected. Files being published may temporarily be missing or inconsistent; reread to check. Queries never repair originals.

At least one of the frozen runner in the original job request or the current runner must remain to verify project and Git-root ownership. If both are missing, unverifiable ownership is reported explicitly. Configuration and state directories may share a folder; their two source roles remain separately labeled.

These offline lists/details retain `runtime_status: not_queried`. A start file does not establish that a job is still running, and a missing result does not establish failure. `recorded_result_state: SUCCEEDED` describes only the original execution result; its gate may still fail. Gate summaries check the report SHA referenced by the original result and manifest/job binding, without rerunning statistics, correctness or quality evaluation. Cancellation requires explicit confirmation in the separate panel below. Exact evidence SHA approval still follows original `agentflow training`.

### Explicitly query original runtime status

Install the `temporal` extra in the environment running Ergora (`python -m pip install ".[web,temporal]"` when installing from the repository), then start the same native Temporal service and training-control worker using the complete reference guide. Existing experiments need no resubmission; connection settings follow the registered reference installation.

```bash
ergora training status my-project EXPERIMENT_ID --timeout 20
ergora training status my-project EXPERIMENT_ID --run-id ORIGINAL_RUN_ID
```

Select an experiment on the page, then click “查询原运行状态”. `GET /api/projects/{project}/training/{experiment_id}/status` has the same semantics, with optional `run_id` and 1–60 second `timeout`. There is no automatic polling. Queries first check original manifest/spec and repository ownership, then the complete Experiment input in the original workflow's first history event. They pin the actual run ID to read original Status or Outcome. The SDK and newly used native sources must match supported versions.

`runtime_status: queried` proves only that this query obtained bound original runtime facts. `not_found` comes only from an explicit original-runtime response that the run does not exist. Missing history, input/binding mismatch, network errors and timeouts fail directly; they never fall back to local “运行成功” or automatic resubmission. Original outcomes such as `GATE_FAILED` and `CANCEL_UNCONFIRMED` remain intact. A finished control workflow does not mean the external job stopped; an integration ticket does not mean automatic merge. Saved evidence in list/details remains separate. Live queries do not recompute gates, approve or modify training originals.

### Submit prepared experiments and reconcile by original ID

First freeze a real experiment using original `init / runner-add / prepare`, and start the same native Temporal/training-control worker. `ergora training show` returns current `project_revision` and `experiment.binding.manifest_sha`. After confirming the complete original manifest and trusted runner, submit their exact identities:

```bash
ergora training submission my-project EXPERIMENT_ID
ergora training check-start my-project EXPERIMENT_ID --manifest-sha256 EXACT_MANIFEST_SHA256
ergora training start my-project EXPERIMENT_ID --revision REVISION --manifest-sha256 EXACT_MANIFEST_SHA256
ergora training submission my-project EXPERIMENT_ID
# 已有意图：使用上一步返回的完整 intent_sha256
ergora training resume-start my-project EXPERIMENT_ID --revision REVISION --intent-sha256 ORIGINAL_INTENT_SHA256
```

`check-start` read-only reuses original Linux/WSL2 startup preflight, checking current baseline, runner/time limits, Git root and complete commit, comparator and original job/fence records. It requires no Temporal SDK/service or keys, writes no submission intent and starts no training. With no original intent and passing local checks, `ready_for_new_start=true`/exit0; with an existing prepared/unknown/submitted/rejected intent it is false/exit1, `submission` retains original state and `observation` is null, without readmission or resend. Wrong SHAs or original admission failures follow error exit2. This is neither a reservation nor execution authorization, nor proof the service has no old run; actual subsequent start still queries the service by original identity and repeats original checks.

The console reads only local submission records in experiment details. First submission requires pasting the full manifest SHA; continuation/reconciliation requires the original intent SHA. Reread after project revision changes. HTTP shares the application entry point: `GET .../training/{experiment}/submission`, `POST .../start` (`revision / manifest_sha256 / timeout`) and `POST .../resume-start` (`revision / intent_sha256 / timeout`). Live-operation timeout is 1–60 seconds. Default navigation performs no start, polling or automatic retry.

CLI `start`/`resume-start` exits 0 only for `submitted`; `prepared`/`unknown`/`rejected` exits 1 and prints original JSON, which cannot authorize proceeding with training. `submission` is read-only observation and exits 0 on a successful read; its exit code does not mean submission succeeded. `submitted` only means the original control workflow confirmed receipt, not that training ran or passed.

Submission preflight requires a prepared contract, currently matching baseline, trusted runner from the same repository, existing original Git commit and original comparator. It rejects existing job/execution/fence records. The intent saves the original contract, baseline/runner and file digests under `ergora/training-submissions/` in registered original execution state. It is only an operational checkpoint; experiment, job, statistics, approval and scheduling remain with their original owners. Do not delete these records to bypass unknown state.

|Local submission state|Meaning and next action|
|---|---|
|`not_recorded`|No control-plane intent exists. Submit only after confirming the exact manifest; existing native runs are not claimed.|
|`prepared`|Intent saved with no send attempt. Explicit `resume-start` may continue the original submission once, rechecking original sources before sending.|
|`unknown`|Attempt persisted without receipt. `resume-start` only looks up the original workflow ID, pins the actual run and checks complete input and intent memo. Even explicit NOT_FOUND does not clear the attempt or resend.|
|`submitted`|Original start returned a run ID, or original history/memo verified and restored its run receipt. It does not mean training executed, gates passed or adoption occurred.|
|`rejected`|A run exists without this intent, or the original client rejected same-ID competition. Conflict records remain; no claiming or resending.|

After a lost reply, timeout or process stop, first read `submission`. Do not change experiment IDs, repeat `prepare` or call original start directly to bypass records. Post-attempt reconciliation follows the intent's original spec; subsequent baseline/runner changes do not reinterpret it as new send permission. Input/memo conflicts, missing history and RPC errors retain unknown and fail explicitly. If registration/execution directories change, explicitly select the original published record through [original-registration recovery](#recover-in-the-original-registration-context); do not move old records into a new home to claim them.

Submission only queues the original control workflow. Actual runners execute explicitly through managed execute below or old `agentflow training run-local EXPERIMENT_ID --confirm-manifest-sha ...`. Original evidence SHA approval and integration tickets continue through the original training protocol; `ergora task` manages development Tasks only.

### Explicit managed execution and offline stop observation

Use the [current native sources](prepare-experiments.md#prepare-versioned-native-sources), their separate complete dependencies and a trusted Linux container. Configure explicit trusted execution for the [separately provisioned current installation](../install/linux.md#prepare-the-formal-reference-runtime); a frozen original installer or source-preparation receipt does not establish that environment. This allows same-user Agents access to current-user files; it provides no OS isolation between Agents. Start original `temporal`, `training-budget-worker` and required `mlflow` services. After the separate [original budget authorization and start](controllers.md#start-a-local-training-budget-and-recover-original-authorization), wait until the original run is `QUEUED` and same-job `request.json` exists. The owner freezes current `ergora-training-execution-v1` capability, complete sources and context at creation. Missing/drifted sources reject execution; sources cannot be resampled or the owner restarted/renewed for takeover.

```bash
ergora training execute my-project trial-a --revision REVISION \
  --intent-sha256 EXACT_START_INTENT_SHA256 --run-id EXACT_ORIGINAL_RUN_ID \
  --request-sha256 EXACT_NATIVE_REQUEST_BYTES_SHA256 --confirm
ergora training execution my-project trial-a
```

`run-id` and start intent SHA come from original `submission`. Request SHA is the complete file byte SHA of `training/jobs/trial-a/request.json` under registered native state, obtainable with `sha256sum`; manifest SHA or canonical content SHA cannot replace it. The command checks complete initial history/memo for the same run, same-job state, current original sources and remaining compute, then saves one explicit request. `requested` only means that request was saved. Ordinary start, status, resume-start, execution and worker restarts never create it.

The original live owner consumes launch only once, then writes attempt/ack inside the same original `executor.lock` before entering original Git, runner, archive and track handling. Existing/partial launch, lost replies, Popen failure or hook interruption never returns that opportunity. For unknown, first read `execution` and original service logs, retaining request/launch/attempt/ack. Do not delete records, change cycle or bypass with manual run-local. Reconfirming identical requests at most observes existing records; it cannot authorize relaunch.

Compute expiry or explicit original cancel notifies the execution subtree to stop while independently handling original fence/control cancellation. Registry or fence-sync waits do not block execution reaping. Each execution S uses the original subreaper to reap new-session descendants, then sends a matching stopped frame before the same S directly publishes stopped durably. It creates no further subprocesses afterward. Safety cleanup may exceed total time; retain overrun. Without matching stopped, result, PID disappearance or ended control flow alone cannot establish stop.

|`execution` field|Meaning|
|---|---|
|`status=not_requested`|No explicit request; reading does not create one.|
|`status=pending`|Request/partial chain exists without complete stop; retain unknown and grant no rerun.|
|`reap_record_observed=true`|A stopped record matching the complete identity is readable; durability still needs confirmation.|
|`executor_stop_confirmed=true`|The same complete chain synced existing files/directories and reread them unchanged, confirming durable stop of that execution subtree.|
|`execution_success=null`|Stop observation judges neither training, quality, gains nor adoption; read original result, gate and approval records separately.|
|`current_sources`|Whether current native installation/gate still matches; independent of historical reading, without retroactive execution authority.|

`execution` uses a bundled independent stdlib reader, needing no Temporal SDK/service, GPU or continued existence of the selected native installation. It only reads existing original chains and confirms durability of the same originals; it creates no records or changes to file contents. Sync failure remains unknown; the same originals can be observed again later. Current-source checks have independent limits; installation loss or upgrade drift is displayed separately. This reader neither selects nor executes candidates. Finite controllers require [separate explicit authorization](controllers.md#start-a-local-training-budget-and-recover-original-authorization). Real training quality and performance still need the original evidence flow; kernel experts remain in the proposal path.

### Read an original local GPU release after pool closure

Use the original pool configuration, session ID and lease ID to read a release after the pool closes and relinquishes its sentinel. The command checks the accepted release, the exact stopped proof and the assigned device observations. You can also read it when a successor session uses the same coordination directory and sentinel path with a different set of devices.

```bash
ergora gpu-pool inspect --config POOL_CONFIG --session-id ORIGINAL_SESSION_ID --lease-id ORIGINAL_LEASE_ID
```

The response includes the original attempt digest and release reference. Use the current resource owner for present device availability and new admission. Read experiment outcomes through the training evidence commands.

### Explicitly fence a local experiment without a run ID

When original start remains `prepared`/`unknown` without a complete cancellable run ID, or an experiment is prepared but not submitted, confirm its original local fence. This requires Linux/WSL2, the `temporal` extra and undrifted original registration. It requires no running Temporal service, reads no keys and starts no runner:

```bash
ergora training fence-start my-project EXPERIMENT_ID --revision REVISION --manifest-sha256 EXACT_MANIFEST_SHA256 --confirm
```

Before confirmation, check `training submission` and the original manifest. If a start intent exists, use its complete manifest SHA; a changed same-named current spec does not rebind it. Without an intent, verify identity through original preparation records without fabricating a start intent. `--confirm` authorizes the selected experiment's original local fence: blocking new local jobs, potentially exposing cancellation to runner/archive, and preventing release tickets not yet created. Existing tickets remain; this command does not handle human release for other completed experiments. This is no reversible pause; do not delete fences or change experiment IDs to bypass original records.

Exit 0 only confirms the same binding's local fence was saved/matched on readback. The result contains original binding, `fence.path / sha256` and locked `existing_job`; `runtime_status=not_queried`, with `executor_stop_confirmed` and `execution_success` both null. No job does not mean no workflow or descendants; an existing job does not mean it stopped. `submission_status_observed` is only an observation snapshot; receipts/rejection records may persist after reading. If `submitted` or `rejected` is observed without a fence, creating one is rejected; use exact-run cancellation or ownership reconciliation respectively. An existing same-binding fence can still be matched/read after those terminal states, without start/signal or run-ownership authentication.

A timeout, interruption or lost reply may occur after fence persistence. Retain original confirmation information and idempotently read back with the same command. Errors mean neither “未阻断” nor “已停止”. This entry point rejects registration/execution-directory drift. Old-context recovery, whole-cycle stop and automatic cycles are provided separately. Currently this is CLI-only.

### Cancel original runs and observe stop facts separately

First confirm `training submission` returns `submitted` and the complete original `run_id`. Unknown starts must first recover as described above. Actual cancellation and original-executor observation require Linux/WSL2, the `temporal` extra and the same original service/training-control worker. Cancellation requests use stable IDs; retain the ID and continue querying or recovering the same request after failure.

```bash
ergora training cancellation my-project EXPERIMENT_ID stop-one
ergora training cancel my-project EXPERIMENT_ID stop-one --revision REVISION --run-id ORIGINAL_RUN_ID --reason '停止本次实验'
ergora training cancellation my-project EXPERIMENT_ID stop-one
# 使用取消记录中的原 intent_sha256；不要使用 start 的意图 SHA
ergora training resume-cancel my-project EXPERIMENT_ID stop-one --revision REVISION --intent-sha256 ORIGINAL_CANCEL_INTENT_SHA256
ergora training stop-status my-project EXPERIMENT_ID --timeout 20
```

The page first reads the original submission receipt. Enter a request ID and click “读取本地取消记录”. First cancellation requires the complete original run ID and reason; existing intents require the original cancellation SHA. Cancellation and “读取停止事实” are explicit operations without automatic polling. Existing submissions/cancellations still recover from frozen original input when current manifest/baseline/runner/spec is missing. Failed detail reads do not hide these actions.

|Cancellation-record state|Meaning and next action|
|---|---|
|`not_recorded`|No intent exists for this request ID; create after confirming original run and reason.|
|`prepared`|Intent saved without send record; `resume-cancel` may explicitly continue the original request once.|
|`unknown`|Pre-send attempt saved, delivery unconfirmed. Recovery only checks complete signal history of the pinned original run without resending. Missing events, NOT_FOUND or RPC errors never clear the original attempt.|
|`requested`|Original signal has a send receipt, or history matches complete binding/reason/independent operation SHA. This proves delivery only.|
|`already_closed`|Original control workflow ended, recording `signal_delivery: not_sent`. No cancellation was sent; this does not establish stop.|

Local `cancellation` reads require no SDK or running service and exit 0 on success. `cancel`/`resume-cancel` exits 0 only for `requested`/`already_closed`; other record states exit 1. This exit code is no proof of external stop. The original client checks binding before signaling. Records pin original start intent, run, reason and operator; the same request cannot change reason or impersonate an operator. Intent, send attempt and receipt reside in original execution state at `ergora/training-cancellations/EXPERIMENT/REQUEST_ID.*.json`, retained with `ergora/training-submissions/`, original job/fence and Temporal history. Do not change IDs or delete checkpoints to bypass unknown delivery.

`stop-status` is one read-only observation returning `control` (original Status/Outcome), `executor_observation` (original adapter job observation) and `fence_recorded` separately; successful reads exit 0. Original `CANCEL_UNCONFIRMED` and later local `CANCELLED` may coexist and appear separately. `QUEUED`/`RUNNING`, missing jobs, unread fences or ended control workflows cannot be combined into “已经停止”. This query sends no signals, writes no fence, runs no runner and neither reevaluates nor approves candidates. Operators must still verify actual devices/remote jobs.

HTTP uses the same entry point: `GET .../training/{experiment}/cancellations/{request_id}`; `POST .../cancel` (`revision / request_id / run_id / reason / timeout`); `POST .../resume-cancel` (`revision / request_id / intent_sha256 / timeout`); `GET .../stop-status?timeout=20`. Actual-operation timeout is 1–60 seconds. Native Windows only reads local cancellation records; actual cancellation and executor observation use registered Linux/WSL2 environments.

### Recover in the original registration context

If project registration or its four configuration files later change, CLI can explicitly select **the original registration successfully published in the same control home** to read, reconcile, cancel or fence in the original execution directory. The current project must still exist; default commands continue checking current registration. Preserve old directories, reference installation, original start intent and checkpoints. Selecting an old record neither migrates runs to new directories nor rewrites current projects or original journals.

Find `CONTROL_HOME/registrations/PROJECT/OPERATION_ID.json` using `registration.operation_id` in the original receipt or `recovery_record` in original `project registration` output. Same-directory `OPERATION_ID.result.json` must exist with `status` `published`; select its complete `intent_sha256`. This is the complete original journal's **canonical content digest**, not the original file's `sha256sum` byte digest or a cycle digest. First check the journal's `after` project, repository, execution directory and four published configurations. Missing result/original installation fails explicitly; records are never fabricated.

Read current revision using `project show`. The operation and SHA below come from that original published result; explicitly confirm them with every recovery command:

```bash
ergora project show my-project
ERGORA_ORIGINAL_OPERATION=REPLACE_WITH_ORIGINAL_32_HEX_OPERATION_ID
ERGORA_REGISTRATION_INTENT=REPLACE_WITH_ORIGINAL_64_HEX_INTENT_SHA256
ergora training submission my-project EXPERIMENT_ID \
  --original-registration "$ERGORA_ORIGINAL_OPERATION" \
  --registration-intent-sha256 "$ERGORA_REGISTRATION_INTENT" --confirm
ergora training resume-start my-project EXPERIMENT_ID \
  --revision CURRENT_REVISION --intent-sha256 ORIGINAL_START_INTENT_SHA256 \
  --original-registration "$ERGORA_ORIGINAL_OPERATION" \
  --registration-intent-sha256 "$ERGORA_REGISTRATION_INTENT" --confirm
ergora training cancel my-project EXPERIMENT_ID stop-original \
  --revision CURRENT_REVISION --run-id ORIGINAL_RUN_ID --reason '停止原运行' \
  --original-registration "$ERGORA_ORIGINAL_OPERATION" \
  --registration-intent-sha256 "$ERGORA_REGISTRATION_INTENT" --confirm
```

The same options apply to `cancellation`, `resume-cancel`, `stop-status` and `fence-start`, retaining each command's request ID, manifest/intent SHA and current revision confirmation. Result `project_revision` is the current revision at this selection; `original_registration.registration_project_revision` is the original registration revision; `submitted_revision` or fence `intent_project_revision` is the original start's frozen revision. Post-registration binding changes may make all three differ. Original registration digest and directories are separately listed.

Recovery mode requires an existing matching original start intent. `prepared` can be read or explicitly fenced; `resume-start` requires an existing attempt and only queries complete original input, memo and history. NOT_FOUND or unreachable services remain unknown without resending. `cancel` still freezes one cancellation request for the exact original run; after a lost reply reconcile with same-ID `resume-cancel`. Do not create another request ID to bypass unknown. Old-context mode provides no new start/check/prepare, runner or approval/release; corresponding CLI commands lack these old-registration options and pages never enter recovery mode automatically.

The parent checks original sources before selecting the old execution directory, and the original training process checks again. Journals are limited to 32MiB and published results to 1MiB, strictly parsed with links/reparse points, duplicate keys, missing or conflicting sources rejected. Oversized records are never truncated. Equivalent execution-allowlist order preserved by successful imports remains readable. This retains the current user's management boundary for a trusted control home; a digest set is no cross-user, cross-machine or external-import provenance authentication.

Local `submission / cancellation` requires no SDK/service. Actual reconciliation, cancellation, fencing and executor observation require the `temporal` extra; actual execution entry points still require Linux/WSL2. Connections follow the supported original local runtime fixed at `127.0.0.1:7233`, namespace `default`; another service cannot substitute for original history. Before native-adapter record reads, `stop-status` checks request/started/result/fence paths, job ID and binding. Its control-plane, adapter and fence results remain separate observations, proving no OS/descendant stop.

Continue: [Authorize and supervise a finite training controller](controllers.md) · [Read training evidence and approve exact results](evidence-and-approval.md).
