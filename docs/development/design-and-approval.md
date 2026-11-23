# Review design material and approve an exact plan

English · [Documentation](../README.md) · [简体中文](../zh-CN/development/design-and-approval.md)

## Read plan materials awaiting approval

This applies only to tasks created through the unified entry point with their original submission receipt saved, using the same runtime environment as submission. First query the original state with `task status --run-id RUN_ID`, obtain the actual plan SHA from `AWAITING_PLAN_APPROVAL`, then read its materials:

```bash
ergora task status my-project TASK_ID --run-id RUN_ID
ergora task plan my-project TASK_ID --run-id RUN_ID --plan-sha256 PLAN_SHA --timeout 20
```

`plan` checks the original submission run/spec/memo, the current awaiting-approval phase and selected plan SHA. It locates the plan job in the original history and checks the request envelope and accepted receipt. The plan SHA is the canonical JSON digest of the entire receipt, not the execution-plan file digest. `materials` returns complete UTF-8 text and each material's `name/sha256/bytes` according to the frozen profile. Both development templates provide execution-plan, ownership-map and rollback-plan. The response also retains the original run, request, profile, receipt and history-event identities for reviewing work units, scope, risks and rollback measures.

Each material is limited to 256 KiB, and the total JSON response to 1 MiB. Missing materials, digest mismatch, non-UTF-8, unsafe paths or exceeded limits reject the read instead of truncating it into an apparently complete plan. `--timeout` is 1–60 seconds. The parent process provides another 5 seconds for startup/reaping; local prechecks are separate. This operation holds no control-database write lock, creates no decision or owner receipt, and sends no signal. The result is a snapshot at read time; the server checks the original run's current state again before approval.

API: GET `.../tasks/TASK_ID/plan?run_id=RUN_ID&plan_sha256=PLAN_SHA&timeout=20`. The page's “Review plan and approve” uses the same entry point. After a network failure or when the plan is no longer awaiting approval, query status again using the original ID without creating a replacement task.

## Approve per-unit method guidance at the original checkpoint

For a current budgeted native run, the owner can include implementation guidance for named, frozen work units in the initial Plan approval. Use a JSON object such as `{"parse":"Reuse the existing parser before allocating memory."}`, where each key is an original unit ID. Each UTF-8 text value is at most 2,048 bytes and the complete canonical map is at most 8,192 bytes. The guidance shares the original objective, acceptance, checks, assignments, permissions, scopes and budget. Substantive changes to those fields use the linked-successor workflow.

```bash
ergora task plan my-project TASK_ID --run-id RUN_ID --plan-sha256 ORIGINAL_PLAN_SHA \
  --method-addendum methods.json
ergora task approve my-project TASK_ID --decision-id owner-method --revision REVISION --run-id RUN_ID \
  --original-plan-sha256 ORIGINAL_PLAN_SHA --plan-sha256 APPROVAL_PLAN_SHA \
  --method-addendum methods.json --confirm
```

Read the complete original Plan and method preview. Use its `approval_plan_sha256` as `APPROVAL_PLAN_SHA`. The composite digest binds the original Plan receipt and complete canonical addendum, including its exact unit text and original run. The preview is read-only. Preview and approval require a worker with the checkpoint capability. A pending or previously consumed approval, cancellation or expiration closes the method checkpoint. The original worker decides races in original history before work reserves any unit.

Use the same decision ID and `task approval` or `task resume-approve` when delivery is uncertain. Recovery checks the original signal, including the exact method contents. The workflow must verify the owner receipt before dispatch. Work sees its own approved method text and Review sees the complete approved addendum with the original Plan and independent candidate evidence. Use the supported Worker and Executor throughout the run. Status exposes the composite approval digest for method-approved work, including work priority. The evidence index and later amendment checkpoint verify the original owner receipt before reporting the applied composite. A missing or changed receipt leaves the authority audit incomplete.

## Store complete design sources and reported answers

**Published development candidate:** this section describes source `2ae107b` included in verified public commit `9f3e693498834f071cf20d0f25c18555554765f1`. Its own Portability run `43867345323` is terminal 8/8 success, including existing Windows checks; this source-storage slice's publication/CI gate is closed without inheriting e5's result. Source commands still require Linux/WSL2 below; this adds no native Windows source support. An older installation may not provide these commands. This is inspection-only storage, not a new default design/approval workflow.

Use Linux/WSL2 and the project's original registered native interpreter/runtime, matching SDK and original creation/submission/state files. The unified-entry task must already be verifiably submitted, with a real pending plan whose accepted original receipt contains a valid `design-packet` artifact. **No default seed producer was added here**; ordinary template creation alone does not supply one. If the original packet is absent, stop: do not forge an artifact, edit an old receipt or downgrade registration to bypass admission. First inspection/anchor creation checks the actual original online run, history and receipt; callers cannot supply a trusted preflight.

```bash
ergora task design inspect my-project TASK_ID --run-id RUN_ID --plan-sha256 SEED_PLAN_SHA --timeout 20 > design-current.json
ergora project show my-project
```

`SEED_PLAN_SHA` remains the original plan receipt's canonical SHA, not a report-file or later packet SHA. Read the complete `design.source_journal`: its `source_chain_sha256` is the next `PARENT_SHA`, and `current_packet` is the complete packet to copy into a separate local next-revision draft. Preserve every unspecified field and the original task/request/profile/admission/manifest/seed-job/design-profile/declared-owner bindings and work-unit mapping. A publish needs packet revision+1 and `previous_packet_sha256` equal to the current packet's canonical SHA. This guide supplies no abbreviated packet template; use the full [packet schema](../../src/ergora/data/schemas/task-design-v1.json) and [source submission schema](../../src/ergora/data/schemas/task-design-source-v1.json).

Create `publish-round-1.json` with `schema_version:1`, the **whole** next `packet` object and `bodies`, containing a complete descriptor for every `access:full` source. Each descriptor has `path`, `sha256`, `bytes`, `media_type`, `text`; SHA/bytes describe `text` encoded as exact UTF-8, without trimming or newline/BOM normalization. JSON paths are relative to artifacts: `TASK_ID/design/RAW_BODY_SHA/body.SUFFIX`, with plain text→`txt`, Markdown→`md`, HTML→`html`, JSON→`json`. The server publishes them beneath the execution state's `artifacts/`; arbitrary host paths are refused. Every packet body reference must match its descriptor; reference-only sources have no body and are not fetched. `report_ref` names a complete full Markdown report, and a declared `html_ref` names a complete HTML report. Include all full bodies, not summaries or local filenames; publish permits at most32 body entries and rejects duplicate source IDs or unreferenced bodies. The body-file is the closed submission shape, not a native envelope, saved intent or recorder metadata.

```bash
ergora task design publish my-project TASK_ID --run-id RUN_ID --plan-sha256 SEED_PLAN_SHA --operation-id design-round-1 --parent-record-sha256 PARENT_SHA --revision CURRENT_PROJECT_REVISION --body-file publish-round-1.json --timeout 20
```

Reread inspection and the current project revision before the next operation. For `respond`, fill this complete outer shape from the **current** packet's actual IDs and your exact answer; the uppercase SHA/ID/text values below are user placeholders:

```json
{"schema_version":1,"response":{"id":"RESPONSE_ID","question_ids":["QUESTION_ID"],"packet_content_sha256":"CURRENT_PACKET_SHA","choice_ids":[],"source_refs":[],"authored_by":"REPORTED_AUTHOR_ID","origin":"reported-human","supersedes_response_id":null},"body":{"media_type":"text/plain","text":"FULL_EXACT_ANSWER"}}
```

`origin` is only `agent` or `reported-human`; `authored_by` is reported metadata. Choose valid question/choice/source IDs from that current packet. The packet SHA hashes UTF-8 JSON with Unicode unescaped (`ensure_ascii=False`), sorted keys, `separators=(',', ':')`, `allow_nan=False` and no trailing newline; it is not the indented file's byte SHA or the seed packet SHA after revision advances. Do not submit owner-channel, recorder, actor, role, attestation or server-time fields: trusted human assurance is unavailable and the server records only its local process identity. Response bodies allow plain text/Markdown. Save the filled object as `answer-round-1.json`:

```bash
ergora task design respond my-project TASK_ID --run-id RUN_ID --plan-sha256 SEED_PLAN_SHA --operation-id answer-round-1 --parent-record-sha256 CURRENT_PARENT_SHA --revision CURRENT_PROJECT_REVISION --body-file answer-round-1.json --timeout 20
ergora task design operation my-project TASK_ID answer-round-1 --timeout 20
ergora task design resume my-project TASK_ID answer-round-1 --revision CURRENT_PROJECT_REVISION --intent-sha256 ORIGINAL_INTENT_SHA --timeout 20
```

`resume` is only for explicit recovery after inspecting the saved original operation; a successful write does not need another resume. Keep task/run/operation ID, original intent SHA and recorder identity. On timeout/lost reply, inspect before recovering that same ID; do not choose another ID, change submitted content or resend an unknown operation. Resume reads complete saved intent/body bytes and needs no original body-file. A pending tail blocks new IDs until the exact pending operation is recovered. Existing schema1 approval and source operations share the same ID namespace. Missing managed bodies can be restored only by explicit recovery; conflicting bytes/bad chains block, and GET never repairs them.

For a second complete round, inspect again, copy the whole current packet, increment its revision/previous SHA, supply all full bodies, then publish/respond with fresh IDs and the latest parent. Each commit increments `material_revision`; a response does not increment packet revision. Packet, material and project revisions are different. Old packets, reports and superseded answer text remain readable. Once anchored, source-history reads/recovery are local and return `runtime_status:not_queried`; they still need the original selected installation and files, and do not prove the old run is still pending. Query task status separately when live state is needed.

The [storage profile](../../src/ergora/data/design-profiles/design-source-storage-v1.json) defaults to artifact/packet262144B, complete inspection1048576B,64 operations (including pending),32 packet revisions, intent4194304B and raw journal16777216B. Optional first-submission `storage_limits` may only tighten these values; the full effective profile is frozen and cannot later grow/change. Actual complete intent, history and final encoded public result must fit; defaults do not guarantee that all64 operations or32 packet revisions will fit. Complete committed views/results are not truncated or presented as complete after a partial read. Validation/capacity rejection before intent publication creates no new source intent; later I/O/fsync/confirmation failure may leave a pending intent or visible result whose durability this call did not confirm. Inspect the original operation and explicitly recover the same ID/intent SHA, even when result bytes are visible; never delete, overwrite or replace it with a new ID. An insufficient frozen budget requires a new legitimately seeded task. CLI body-file reading also has a16MiB boundary.

Q/K owner resolution, seal/withdraw, trusted design approval and execution are not implemented by these records: readiness/capabilities remain false and supplied knowledge is not an owner decision. Old schema1 `task approve` stays independent and does **not** consume the new discussion or propagate it into old work. Source publication/answers do not authorize execution, change frozen task fields, open schema3 effects or establish real-service/human/GPU acceptance.

## Approve an exact plan and recover delivery

First read and review the complete materials as described above, then explicitly approve using the current project revision, original run ID and that plan SHA:

```bash
ergora task approve my-project TASK_ID --decision-id owner-one --revision 1 --run-id RUN_ID --plan-sha256 PLAN_SHA --confirm --timeout 20
ergora task approval my-project TASK_ID owner-one
# After an interruption, read approval first, then recover with the original intent_sha256 and current project revision:
ergora task resume-approve my-project TASK_ID owner-one --revision 1 --intent-sha256 APPROVAL_SHA --confirm --timeout 20
```

The decision ID is the stable identifier for this owner decision. Repeating the same ID only reads the original record; it does not resend, change the plan or extend the 24-hour validity period. After a plan update, expiry or revocation of the original decision, review the current plan and explicitly make a new decision with a new decision ID. Project binding changes do not alter the original role snapshot. This local entry point uses the current Linux user as the owner actor and does not provide team authentication.

`approval` reads only local records without connecting to Temporal. States are `not_recorded / prepared / unknown / requested`. prepared has no signal checkpoint yet and can be explicitly recovered. unknown has a saved attempt; recovery can only check the exact request/plan/receipt in the original run's paginated history without resending. If the signal is not found or the original run is unavailable, the result remains unknown; continue reconciliation under the original ID. Revoking or changing the owner receipt makes the original intent no longer dispatchable.

`requested` means only that the SDK acknowledged the signal or that the original history contains a corresponding event. `approval_accepted: null` and `execution_success: null` do not mean approval was accepted or the six stages succeeded. The workflow still checks owner/expiry/revocation/exact plan under the original authorization rules. Use `task status --run-id RUN_ID` to check actual progress. CLI mutations return 0 only for requested; even HTTP success responses require checking status.

Approval operation records are stored in the execution-state directory at `ergora/task-approvals/TASK_ID/DECISION_ID.{intent,attempt,result}.json`; the original owner receipt is at `approvals/owner-UUID.json`. Keep them with the original task, creation and submission records. Intent preparation retains the project revision and acquires the original task lock without blocking. The network stage releases the control-database write lock and holds only the same-task lock. Preparation and network each have a 1–60-second budget. The parent process adds 5 seconds for each; local prechecks are separate. After a timeout, read the records before deciding whether to recover.

API: GET/POST `.../tasks/TASK_ID/approvals/DECISION_ID`. The POST body is `revision/run_id/plan_sha256/confirm/timeout`; POST to the same path's `/resume` uses `revision/intent_sha256/confirm/timeout`. `confirm` must be true. Write requests retain same-origin protection and `X-Ergora-Request: 1`. Tasks created/started through the old reference entry point remain managed by the original CLI; this entry point does not adopt old runs.

Continue: [Submit, observe and recover a development task](run-and-recover.md) · [Read original evidence and export a candidate](evidence-and-export.md).
