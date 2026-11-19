# Read original evidence and export a candidate

English · [Documentation](../README.md) · [简体中文](../zh-CN/development/evidence-and-export.md)

## Read the evidence index of a closed run

For tasks created through the unified entry point with their original submission receipt saved, read evidence references together after the original run is closed with no successor run:

```bash
ergora task evidence my-project TASK_ID --run-id RUN_ID --timeout 20
```

API: `GET /api/projects/PROJECT_ID/tasks/TASK_ID/evidence?run_id=RUN_ID&timeout=20`. Use the registered complete Linux/WSL2 runtime. The query budget is 1–60 seconds, with another 5 seconds from the parent process; local contract prechecks are separate. Timeout, oversized responses or wrong ownership cause explicit failure rather than returning a partial index presented as complete.

`contract` fixes the original creation/submission digests, spec and Agent-binding snapshot. `original_outcome` and its digest preserve the original result. `jobs` lists original scheduled-event IDs, context digests, request/receipt states and complete checked receipts. Receipts include the actor, candidate, checks and material name/path/SHA, without material bodies. For bodies, use the [original-job reading entry point](run-and-recover.md#read-original-job-receipts-and-text-evidence) with the listed scheduled event.

`published_evidence: verified` means only that all original requests/published receipts and artifact bytes in this check match completely. It does not mean checks passed, independent review approved or the task can be merged; `execution_success` remains null. Only verification/review receipts explicitly saved in the original outcome are compared individually with their corresponding jobs, with `outcome_reference_state` showing `matches/differs/unavailable`. Other stages show `not_recorded`; existing files do not establish acceptance. Missing or damaged receipts/artifacts make `published_evidence` `incomplete`. Wrong requests, fences, roots or history are explicitly rejected. External cleanup is described separately by `external_confirmed/fence/unresolved_jobs`. A normal task can have complete materials without a fence; a cancelled task still retains its original CANCEL_UNCONFIRMED.

The index response is limited to 1 MiB, but still scans the complete original history and uses FileAdapter to read and check every artifact (up to 16 MiB each). It does not limit total I/O or total memory to 1 MiB. Results describe current material observations; later reads must verify again. Evaluation sets, Skills, memories and source-adoption snapshots in `context_snapshots` are `not_recorded` if the original task did not record them. Current configuration does not fill in history. The query does not start services, execute models, write fences, release leases or change Git refs.

The `budget` field still projects the same frozen profile's `limits`, stage waits, human-approval wait and polling interval, with the original profile SHA and `workflow_admission_and_waiting` scope. `max_parallel_units` constrains work-unit scheduling; it is not a global concurrency limit for all external processes. Stage deadlines are established after the original dev_submit returns and checked after polls with empty receipts. They do not guarantee hard external-process deadlines and are not total task-duration or cost limits. The historical executor's separate walltime cannot be reconstructed from current configuration. v9's unified authorization is separately stored in `contract.original_input.budget`, and runtime observations in `original_outcome.budget`. Do not treat the old profile projection as that persistent authorization or as actual model-invocation billing.

`usage` lists event counts from the complete original history: activity schedules, actually recorded activity-starts, signals, dev_submit events and distinct jobs. It also gives the number of work units in the frozen request. The SDK merges some retry history, so these counts cannot establish all retries, model invocations or billing. `workflow_span` calculates seconds from the original first/final event Timestamps and includes event references. It includes queueing, human waits, concurrency and service downtime; it is neither model runtime nor the sum of job durations. Missing timestamps produce `not_recorded`; reversed timestamps produce `invalid_timestamps` with a null value. Only a real zero span yields 0. Without structured usage sources verified against original jobs, `model_calls/tokens/cost` are all `not_recorded/value: null`, and cost currency and source are also null. They are not automatically estimated from material text or current pricing.

## Collect and verify handoff packets offline

When the original run is closed and the index above has complete materials, explicitly collect them into a new local file. Use the registered complete Linux/WSL2 runtime without starting a worker or rerunning an agent:

```bash
ergora task handoff my-project TASK_ID --run-id RUN_ID --output ./task-handoff.zip --timeout 20
```

Collection reads only artifacts referenced by the original index and receipts. It does not scan the environment, credentials, arbitrary user directories or the whole repository. Missing/damaged materials or additional jobs cause collection to be rejected. Original business failure or cancellation does not prevent handing off complete materials and is not rewritten as success. A temporary file in the same directory is completed and then published with create-only semantics, refusing to overwrite an existing target; a local filesystem supporting hard links is required. Ordinary exceptions clean up temporary files. After forced process termination, first inspect the target and `.ergora-handoff-*` remnants in the same directory, and confirm that no collection process is still running before handling them. The query budget is 1–60 seconds, plus 5 seconds from the parent process. A timeout does not guarantee that the file has not been published. Check an existing target first rather than blindly overwriting it.

Recipients need only the base `ergora` installation and can run on native Windows or Linux without a control database, SDK or online services:

```bash
ergora handoff verify ./task-handoff.zip
ergora handoff verify ./task-handoff.zip --sha256 EXPECTED_PACKET_SHA256
```

The optional `--sha256` accepts an independently obtained 64-character lowercase hexadecimal digest of the complete packet. A match gives `external_sha256: matches`; omitting it gives `not_recorded`. Success outputs `status: verified`, packet/manifest digests, project/original-run/candidate references and the original outcome. `verification_scope: packet_bytes_and_declared_internal_identities` proves only that the packet's bytes, digests and declared spec/request/profile/binding, job/receipt/material relationships match. `origin_authenticated: false` and `execution_success: null` remain unchanged. The packet does not carry complete creation/submission intents, service history, context or Git objects; their SHAs are only references. Offline verification cannot authenticate the original executor, verify history counts or review independence, replay execution or recheck candidate code. An external SHA does not itself constitute a signature or source authentication.

v1 uses standard ZIP_STORED, UTF-8 JSON, SHA256 and a public [versioned schema](../../src/ergora/data/schemas/task-handoff-v1.json), containing only `manifest.json` and digest-deduplicated `blobs/SHA256`. [Version-scoped manifest limits](../architecture/contracts/formats.md#supported-task-routes-and-material-limits) are 4 MiB for verified current12 input and 1 MiB for other supported inputs; the unchanged remaining caps are 16 MiB per blob, 64 MiB total deduplicated materials, 4096 members and 72 MiB per packet. Duplicate, extra, missing, noncanonical-path, linked, encrypted or compressed members are explicitly rejected. Verification reads members directly without extracting or executing them. These limits do not constrain ZIP-library peak memory or the original index's complete-history/per-artifact reading costs to 1 MiB. Handoff packets support material review; they do not replace a combined backup of the original execution directory, Git and lease database. Operators separately choose local output paths and transmission.

HTTP clients can explicitly `POST /api/projects/PROJECT_ID/tasks/TASK_ID/handoff` with JSON body `{"run_id":"RUN_ID","timeout":20}`. Same-origin protection and `X-Ergora-Request: 1` still apply. Additional fields such as server source/output paths are not accepted. Success returns `application/zip` with the fixed attachment name `ergora-handoff.zip`; `X-Ergora-Handoff-SHA256` is the whole-packet digest of this response's bytes. The server invokes the same collection use case in a private temporary directory, reads the packet back within limits and checks its SHA, cleans the temporary directory, then sends the response. Ordinary failures also clean up, without starting services or changing the original task. The client chooses the download location and must avoid overwriting local files that need to be kept. This entry point buffers up to 72 MiB of packet bytes and has additional memory costs; it is not a streaming download. Remnants from forced process termination are handled operationally. The response digest supports comparison of this download and is not a signature. Obtain any independently expected SHA through a separate trusted channel.

## Web evidence, budgets and handoff

For a formal task, first “Read original run”, then select “Evidence, budget and handoff” on the closed original run. Opening the window does not request an index or materials. “Read evidence index” checks original materials together and displays the original outcome, completeness, external-protocol confirmation and lease facts. Budget and usage retain original sources and units. Unrecorded model calls, tokens and costs remain unknown; an actual zero remains zero. Frozen waiting limits are not process or cost limits. Missing context relationships are not backfilled from current configuration.

The original job directory displays 20 entries per page. “Original job receipts and materials” reuses the original receipt window; select and explicitly read text there. Indexes, complete contracts and material content are displayed as text. Failed rereading retains the previous observation and marks failure. Closing and reopening starts empty, without automatic polling, retries or body prefetching.

“Collect and download handoff package” needs no prior index read. The page calls the [handoff collection interface](#collect-and-verify-handoff-packets-offline), checks actual response bytes and digest headers, then gives the bytes to the browser for saving. A success message does not prove a file reached disk; check browser downloads and the save location. The page displays full-package SHA, bytes and an `ergora handoff verify` command. Independently verify provenance, original outcome and candidate. Both server and browser buffer package bytes; download is not streaming. Failure does not trigger this download; any older download information describes only a previous operation.

Closing/replacing the window, editing the run or switching task/project prevents late indexes from updating the page and late packages from triggering a download. It does not revoke a read-only collection the server has already sent. A busy window prevents concurrent reads/downloads. These operations do not automatically start services, workers or models, publish a fence, release a lease, approve a candidate or rewrite the original cancellation result.

## Check external-job evidence for a closed run

For a task created through the unified entry point with its original submission receipt saved, use the fixed original run to read complete history, original job requests, trusted terminal receipts and an existing fence:

```bash
ergora task external-status my-project TASK_ID --run-id RUN_ID --timeout 20
```

API: `GET /api/projects/PROJECT_ID/tasks/TASK_ID/external-status?run_id=RUN_ID&timeout=20`. The original run must be closed and still the latest run of that workflow ID; continued-as-new and other subsequent runs are unsupported. Use the registered complete Linux/WSL2 runtime. The budget is 1–60 seconds, with another 5 seconds for the parent process and separate local contract preflight.

`original_outcome` retains the original workflow outcome; it is null when a failed, cancelled, terminated or timed-out Temporal run has no result. `jobs` lists original-history jobs with request/receipt status and digests. `unresolved_jobs` includes missing requests, missing or damaged receipts, extra requests and orphan receipts. Wrong roots, conflicting requests, wrong fences or incomplete history are explicitly refused. Only the requests/receipts/artifacts/approvals/fences layout inside the registered execution-state directory is supported.

`external_confirmed` is true only when every request and trusted terminal receipt matches complete history, no extra job exists and the correct fence is already present. Both requests and receipts job directories are checked. An orphan receipt that cannot bind to original history cannot be confirmed. FAILED/CANCELLED receipts also establish external-job termination; they do not establish successful development. This is a current snapshot of a trusted-file protocol, relying on the executor to publish receipts and honor fences under the original protocol. It does not replace OS process checks. A missing directory cannot turn known historical jobs into a zero-job pass.

The query saves no tool-run record, publishes no fence and releases no lease: `lease_released_by_operation: false`, `execution_success: null`. CLI exit 0 means only that the query succeeded; inspect external_confirmed and unresolved entries. If unconfirmed, retain the original task, run directory and lease, and complete evidence using the original IDs first.

## Export an exact candidate and recover its receipt

This applies only to unified-entry tasks with saved submission receipts. First use `task status --run-id RUN_ID` to confirm the original run finished with outcome `REVIEW_READY`. Review its exact candidate and trusted-check/independent-review evidence, then explicitly specify a local target branch:

```bash
ergora task export my-project TASK_ID --revision 1 --run-id RUN_ID --candidate-sha CANDIDATE_SHA --branch agent/TASK_ID --confirm --timeout 20
ergora task export-status my-project TASK_ID
# After interruption, read export-status first; resume with original intent_sha256 and current project revision:
ergora task resume-export my-project TASK_ID --revision 1 --intent-sha256 EXPORT_SHA --confirm --timeout 20
```

One task saves one immutable export target. Repeated export returns its original record, without changing run, candidate or branch. `prepared` means no write-ahead checkpoint exists; explicit resume can continue. `unknown` means the original result digest was saved; recovery only checks the original run/outcome and actual branch, without refetching or creating it. A missing branch returns `unknown/branch_not_found`, avoiding resurrection of a manually deleted branch. Retain the original record and reconcile manually. An existing branch pointing elsewhere, changed original result or conflicting record is explicitly refused.

Git fetches objects without writing FETCH_HEAD, checking out, merging or pushing. A Git conditional transaction creates the target branch. An existing exact-candidate branch is accepted; other branches and symbolic refs remain unchanged. After confirming the branch, release applicable issue leases through the original rules and save the original `tasks/TASK_ID/export.json` format and this tool's receipt. `exported` means that export fact has been saved, with `checked_out: false`, `merged: false`; later review and integration follow project policy. Reading a repeated terminal result does not live-check subsequent manual branch edits.

`export-status` reads only local records, without connecting to Temporal or releasing leases. Intent, write-ahead checkpoint and receipt live at `ergora/task-exports/TASK_ID.{intent,attempt,result}.json` in execution state. Back them up together with original creation, submission, task, workspace and lease records; a control database alone is insufficient. Preparation strictly checks current revision/confirm and acquires the original task lock nonblockingly. Network/Git phases release the control-database write lock. Each stage has 1–60 seconds, another 5 for the parent and separate preflight. After timeout, read records first and reconcile actual writes through original branches/checkpoints. Linux/WSL2 uses the registered complete runtime; exports through the old entry point are not implicitly taken over.

API: GET/POST `.../tasks/TASK_ID/export`; POST body is `revision/run_id/candidate_sha/branch/confirm/timeout`. POST `/resume` under that same path uses `revision/intent_sha256/confirm/timeout`. Mutations retain same-origin protection and `X-Ergora-Request: 1`; confirm must be true. A mutating CLI returns 0 only for exported; HTTP success also requires checking status.

Continue: [Write reports from original evidence](../review/evidence-reports.md) · [Carry a retrospective into the next task](../improvement/workflow.md).
