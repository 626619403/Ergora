# c1d M1b: schema3 birth and compatibility

2026-11-16. **Storage-only amendment accepted; final design review approve on both axes, open0.** The [fresh design review](../delivery/2026-11-16-training-cycle-v3-birth-design-review.md) closed D1 on revised design `b2edb47f…`; actual native callback and its test obligation below are unchanged. Implementation is starting in its isolated tree; this header is status bookkeeping. Original design baseline: `fa2fd17620192ac1341a72f1050dc37faaee623f`; implementation baseline after reviewed M1a: `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`, branch `refactor/architecture-foundations`. Apply maintainable-project-delivery/ergora-codebase-quality; read PLAN/AGENTS/component protocol. M1a remains a separately reviewed slice.

Authority: [parent](2026-11-16-training-cycle-measurement-and-index.md), [wire](2026-11-16-training-cycle-measurement-wire.md) SHA `ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`, [review](../delivery/2026-11-16-training-cycle-measurement-wire-review.md). PLAN closes c1c. Preserve six stages, old authorization/history, candidate evidence, attempt-before-send, unknown-only reconciliation, one nonrenewable budget. Only new schema3/eventual V2 may execute successors.

## Necessary staging amendment

Dispatch belongs to worker; budget/native branch on authorization. V2 submission now would target an absent class without acceptance/final gates. Amend M1b to **internal explicit schema3 storage birth/read/local intent only**, subject to fresh design review. No runnable V2/class/activities/queues/operation protocol/capability; CLI/HTTP/UI unchanged.

Local ready means local admission, `execution_authorized=false`. Schema3 intent preparation may succeed; live/manual/native execution fails even at ordinal0. Retain all `successor_not_enabled`; no stub/framework/second writer.

## Minimal birth contract

Existing Python API:

```python
authorize_controller(state, project_id, cycle_id, directory, sha256,
                     expected_revision, *, confirm, execute_selected,
                     program_version=1)
```

Exact int1/2, not bool: omitted/1→schema2, 2→schema3; manual authorize→schema1. `_authorize` compares exact requested/saved version instead of boolean consent. No mode/program change; schema3 retry requires explicit2.

Use wire's exact schema3 keys/canonical SHA; preserve actor/confirmation/scope/continuation. V2 protocol/queue=`ergora-training-cycle-v2`, ID prefix=`ergora-training-cycle-v2/`; schema2 prefix stays `ergora-training-cycle/`. Identity={control_home,project,cycle_id,input_sha256}. Intent stays schema1 via CycleAdmission.intent_record; workflow_input={protocol,control_home,project,cycle_id,input_sha256,authorization_sha256}; no workflow_type field.

`measurement_sources`: exact package-relative keys/full lowercase raw SHA256:

- `training_rounds.py`
- `reference_training_evidence.py`
- `data/schemas/training-rounds-v1.json`
- `reference_training_release.py`

Hash package-root bytes via ordinary/no-link bounded readers, never installation/caller paths. Fixed protocol tuple serves cycles capture/strict map validation; private capture stays in cycles. Old 25-key GATE_SOURCES/capability stays exact; no protocol imports of these modules.

Before reserving ID: validate input/project/revision/registration, capture four sources, create one clock, validate authorization. Reuse lock/mkdir/link/fsync publication. Reserved ID remains permanent after failure. Retry loads originals without source/clock recapture or incomplete-record replacement. Input/revision/mode changes refuse. Status validates saved map/SHA; current source drift leaves history readable but blocks schema3 local intent create/recovery within original budget. Execution source/ROOT gates remain M2/M5.

## Exact branch inventory and smallest changes

Baseline lines; no blanket widening.

| Baseline owner/site | Required change or deliberate closure |
|---|---|
| cycles `_authorization`226/236, `_controller`246 | Exact versions1/2/3; schema3 controller/map strict; old expected objects unchanged. Consumed by load/status/budget. |
| cycles `_load`264, `_status`319 | Include schema3 for original lock and local stop observation only. |
| cycles `_authorize`527/547 | Explicit birth selection/exact mode collision; reuse storage/clock/ready algorithm. |
| protocol CycleAdmission constructor552 | Accept schema3 storage identity; reuse intent_record/stop/submission and original record SHA algorithms. |
| cycles prepare_controller / _controller_ready | Prepare schema3 with source check; `_controller_ready` rejects it before direct `_claim_controller` publishes attempt. |
| protocol validate_cycle_operation308 | Keep schema2-only snapshots and operation-v1/SDK contracts. Cold inspect returns before this check; another closure is necessary. |
| worker `_cycle_operation`486 | After load/exact authorization check, reject schema3 before activity binding, SDK lookup, prepare/candidate/stop branches, including cold H. Local stop remains stop_controller. |
| budget BudgetedStart.source263 | Reject schema3 before admission/binding selection; omitted controller must not fall through manual path. Submission and BudgetAdapter create/lookup consume this. |
| protocol validate_context994 | Reject schema3 before manual/controller dispatch, including Execution.current/check and isolated direct-native entry. No SDK/State import. |
| protocol native actor1050 / outer permission1084; execution.check actor30 | Leave schema2 branches. Schema3 skips native_main's outer parent permission; actual refusal is the executor's `admit` callback into validate_context before started/attempt/ack/runner effects. Source/context refusal closes training effects; it does not make the outer schema2 branch run for schema3. |
| protocol validate_owner450/452/456 | Unrelated owner schemas1/2: tuple/capability unchanged, as are request/launch/attempt/ack/stopped and controller intent versions. |

One closed protocol→type function serves runtime `_controller_history`78 and worker dispatch description915/start949: v1→`TrainingCycleWorkflow`, v2→`TrainingCycleWorkflowV2`, unknown fails. V2 dispatch stays closed. Preserve fixed first/original run, attempt1, full input/memo/queue, no reset/continue-as-new. `reference_training_submission.py` already calls budget source/history; no version branch/parent producer or required edit there/context.

## Verification scope for implementation

Reuse submission cycle_selection/controller_admission/historical_execution, controller service/dispatch and runtime replay fixtures; no new file/CI group.

1. Retain schema1 CLI publication/lost-reply, schema2 preparation/dispatch, owner1/2 SDK-free history. Compare complete raw cycle/auth/ready/intent/attempt/receipt across read/retry; controller defaults stay schema2.
2. New version2 ID: birth, remove external input, explicit retry; same hashes/auth/clock/ready, no capture/admission again. Reuse authorization-publication/ready-directory-fsync fault seams: one clock, original bytes, incomplete ID never repaired. Substitute source-read seam (do not mutate repository): current drift blocks local intent, retains readable history, never re-freezes on retry; saved-map tampering fails read.
3. Same ID manual/v1/v2 both directions and input/revision collision preserve originals; reject bool version.
4. Prepare schema3 twice: identical six-field input/intent bytes, no attempt. Exercise direct `_claim_controller`, cold H and manual-binding BudgetedStart.source: visible failure, no attempt/SDK start/job/request/launch; observe existing fixture logs. For direct native, use the existing executor fixture's actual `admit` callback path into validate_context and verify refusal before started/attempt/ack/runner, rather than testing the helper alone or claiming the outer parent-permission branch ran. Keep old ordinal1 SDK refusals.
5. Existing controller fixture's actual SDK codec tests type/input/queue/memo/fixed run; keep v1 defaults and add bounded v2 read-only authentication plus mismatched-v1-type refusal. No V2 execution/replay claim. Replay retained c1c success/cancel/failure history via unchanged v1 class, including cancellation/eviction harness; locate exact artifacts via c1c delivery, do not regenerate as V2. Record actual results only after running.

Deferred: M1c complete encoding/capacity; M2 source/ROOT/four facts; M3 collect/durability; M5 final predecessor/native gates; M6 real V2/activities/registration/continuous budget. Only then may new-version successors open. M7/M8 own installed/live two-round/history evidence; CPU/control does not certify training quality.

The design task wrote only this page, with no tests/services/install/network/source/test edits/commit/push. Root accepted the source-grounded storage-only amendment and D1 was rechecked before code. Implementation/checks belong to [delivery](../delivery/2026-11-16-training-cycle-v3-birth.md) and PLAN, with a fresh implementation review still required. No further user decision is required for this bounded internal slice.
