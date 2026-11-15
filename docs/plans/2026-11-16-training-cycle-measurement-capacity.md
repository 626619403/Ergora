# c1d M1c: capacity at real production boundaries

2026-11-16. **Bounded staging accepted by fresh review; D1 wording correction recorded below; no product acceptance.** Baseline `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`. [Wire](2026-11-16-training-cycle-measurement-wire.md) SHA256 `ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337` and its [accepted review](../delivery/2026-11-16-training-cycle-measurement-wire-review.md) remain authoritative. [M1b](2026-11-16-training-cycle-v3-birth.md) implements storage-only schema3 separately. Applied maintainable-project-delivery/ergora-codebase-quality; read AGENTS/PLAN/component protocol and original fixtures. [Design review](../delivery/2026-11-16-training-cycle-measurement-capacity-design-review.md) approves the bounded staging on both axes, with no blocker to M1c-T; full M1c remains open.

## Necessary staging amendment

No collect mode, full round-observation writer/ref consumer, v3 activity or V2 Workflow exists. M1b keeps schema3 H/dispatch/native closed. A standalone reader/serialization utility would have no production caller. Existing `helper/observation.json` at worker `_cycle_operation:579` is a legacy pretty-encoded stop-chain observation with a different result shape; preserve it.

Propose splitting M1c obligations by their actual owner, retaining the dependency gates:

1. **M1c-T, next bounded verification slice:** verify existing transport callers on the fixed post-M1b candidate; reuse its exact checks already run. No source change presumed. Independently review any demonstrated bounded fix at its existing owner.
2. **M1c-O with M2a/M3a:** implement/check the full observation encoding when H actually assembles the four original observations; M2 remains read-only acceptance, M3 owns index publication/durability. Complete the relevant capacity gate before each containing slice is accepted.
3. **M1c-R with M5a; M1c-V with M6a:** wire the real predecessor/native readers and real V2/SDK boundaries when those consumers exist. No successor opening before all M1c gates, acceptance, durable prefix, final native gates and V2 checks close.

This amends “all M1c implemented before M2” into staging at real consumers. No wire obligation is waived; transport tests alone cannot close M1c. Root records disposition and obtains fresh review before code.

## Source-established owners and gaps

Baseline line numbers; resolve again after M1b integration.

| Production boundary | Existing behavior / smallest responsibility |
|---|---|
| [protocol](../../src/ergora/training_execution_protocol.py):27; [rounds](../../src/ergora/training_rounds.py):15/22/42 | M1a already owns `ARTIFACT_LIMIT=10_000_000`; `MAX_INDEX_BYTES` aliases it; cycle reader uses it explicitly. Reuse this constant, not a duplicate `CYCLE_ARTIFACT_BYTES`. Preserve rounds' pretty encoding and content SHA. |
| [worker](../../src/ergora/reference_training_worker.py) `_CycleOperation:49/79`, `cycle_operation_main:1031` | Parent checks whole compact request before spawn; S/H each read limit+1. S saves exact request; `processes.run` retains H stdin/stdout. Oversized constructor payload has no operation directory; wrapper logs only exception text. Exact unsent-request retention is therefore unproved. |
| worker `cycle_operation_main.frame:1078`; protocol `PhaseFrames:214` | Whole identity/event/result JSON includes `_stdout_ref`; LF is delimiter. Overflow becomes capacity failure without replacement recheck; reader rejects oversized frames. No reachable oversized replacement with valid ordinary paths established: do not invent a pipeline test. Apply wire's second check with actual new-wire integration; no-fit means no result, retained stopped/stdout, incomplete unknown. Stopped stays 65,536B. |
| worker `_cycle_capacity:1177`, `create_cycle_activities.invoke:1573/1661` | Actual client DataConverter/complete `Payloads.ByteSize()` guard inbound request before S/H and assembled result after peer cleanup, metadata included. Existing full-envelope logger does not prove oversized constructor retention. Extend assembly for v3, no second converter helper. |
| worker V1 `_capacity/status/request_stop/_ordinary/run`; `_consume` | The listed sending/result paths have complete converter checks; `_consume` currently does not recheck the complete received envelope. Preserve V1 history/commands. Complete inbound-envelope validation remains required in the real V2 class, alongside its sending/result checks. |
| worker `_dispatch_controller:867/945` | Full started input/Memo gates absent; V2 dispatch closed. Add full converter `Payloads`/Memo checks when real, before claim/send; no retry opportunity. |

`_CycleOperation` construction runs synchronously in the SDK async parent. Large writes/full-payload logging could block stop/cleanup; S does not yet exist. Do not add unsupervised retention, ledger, transport size or window. Keep authoritative input/snapshot/source materials at original owners; H-generated full values stay under original S supervision/window. Exact oversized parent request raw retention requires a separately designed bounded supervised path before claiming completion. A reconstructed subset or stop branch's replacement operation ID does not prove raw identity.

D1 disposition: corrected the V1 `_consume` overstatement from the reviewed proposal. No V1 behavior changes. The real V2 complete inbound check and exact oversized parent-request retention are still mandatory, unimplemented gates; the staging review does not certify either.

## Next diff and verification seams

M1c-T has **no planned product diff**. Original `tests/test_training_submission.py` fixtures `cycle_sdk_activity`, `cycle_operation_fault`, and `tests/fixtures/training_cycle_operations.py` retain actual S/H/reaper and SDK ActivityEnvironment. Tests cover request/stdout/frame overflow, aggregate failure after peers, occupied launch intent and 66 N32 stop refs. `tests/test_training_runtime.py` covers metadata and real sandbox signal/query/outcome. Select exact-candidate checks; no new test file/CI group or helper test. Separate service-double from installed/live scope; legacy N32 does not certify v3.

M1c-O's first product diff stays private in the actual H acceptance/collect owner. Reuse full runtime/native/ExecutionRecords/evidence values, no duplicate archive reader. Use wire's compact UTF-8/sorted keys/finite numbers/one LF; bytes/raw SHA include LF. Save complete raw `xb`; over M is diagnostic only, no ref/acceptance/ready. Write/deadline failure preserves available originals and returns unknown. In-limit ref requires same-file fsync, directory chain sync and same-inode/raw reread inside original window; encoding/reply failure never advances prefix/ordinal.

Real H/budget/context/native consumers explicitly call `read_raw(path, ARTIFACT_LIMIT)`, not its 1MiB default; validate fixed same-root path, ref bytes/raw SHA and strict semantics. No unused generic reader, reencoding for raw SHA, attachments, truncation or renewed clock/opportunity.

## Boundary acceptance ledger, still pending

- Observation M−1/M/M+1 includes multibyte UTF-8 and final LF. Real H writer/reader must accept legal >1MiB. Original readers may succeed while their sum exceeds M: retain complete diagnostics/chains, no ref/acceptance/ready. Partial write, fsync/deadline and reply loss never reset effects.
- H stdout at 32,767/32,768/32,769B counts LF; whole result-frame boundaries count complete identity and `_stdout_ref`, excluding only delimiter LF. A legal stdout can overflow its frame. Verify rejection through original S/H fixture and exact retained stdout hash; do not reduce identity/reason.
- SDK whole `Payloads` at 32,767/32,768/32,769B, plus individually small facts/operations/acceptance that overflow together. Exercise actual invoke assembly, not just `_cycle_capacity`. N32 stop retains every branch/ref, including unknown inline failures; no shortened successful envelope.
- Real V2 input/Memo, ordinary/stop request, inbound/result, signal/query/outcome need final converter/protobuf checks, original BOOT deadlines and once-only effects on the registered program.

## Design probe only

Ignored `.ergora/checks/cycle-measurement-capacity-design/{probe.py,argv.json,result.json}` retain exact code/argv/results. Root `.venv-dev`, Python3.11.15/SDK1.34.0: synthetic LF-inclusive observation sizes M−1/M/M+1 roundtrip; actual default Payloads 32,767/32,768/32,769B match Workflow wrapper. JSON32,768B becomes Payloads32,800B; H stdout32,768B becomes frame33,365B. No production writer/reader/activity ran. Only this public plan written; no source/tests/PLAN/install/services/network/commit/push. All implementation acceptance remains pending.
