# c1d M1c capacity staging: independent design review

2026-11-16. Reviewer: fresh-context independent agent `cycle_measurement_capacity_design_review`, with no participation in drafting or implementation. Applied `maintainable-project-delivery` and its independent-review brief, plus `ergora-codebase-quality` repository-style/module-design/test-seams guidance. Read root/source/tests AGENTS, PLAN and the component protocols. This report is the only write.

**Requirements: approve the bounded staging amendment; blocking findings 0. Maintainability: approve; blocking findings 0.** One nonblocking factual correction, D1, remains below. This approves proceeding to M1c-T verification and attaching mandatory capacity obligations to the real later consumers. It does **not** close M1c, approve a retention implementation, certify a new observation lifecycle, or open ordinal1. Complete oversized parent-request retention remains an unresolved required contract, explicitly acknowledged by the proposal.

## Inspected identities and authority

| Item | Independently inspected identity |
|---|---|
| [Capacity proposal](../plans/2026-11-16-training-cycle-measurement-capacity.md) | 8,043B; raw SHA256 `3fa65a8804b5061de2a325a3b21c98ef92857d1edcf88de58385fd7957cffa2b` |
| [Approved wire](../plans/2026-11-16-training-cycle-measurement-wire.md) | raw SHA256 `ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`; read its [review and re-review](2026-11-16-training-cycle-measurement-wire-review.md), including the final design approval |
| [Parent measurement/index plan](../plans/2026-11-16-training-cycle-measurement-and-index.md) | raw SHA256 `4575d4f0dae80ea0ab822c002780acfa4decafa41c882b85f1c99509d4abb72d` |
| [Current M1b storage-only plan](../plans/2026-11-16-training-cycle-v3-birth.md) | raw SHA256 `39c2dec92aa185de5c832a216f947c516a637af8b5e878c561f20ff0926d9da0` |
| [M1b design review](2026-11-16-training-cycle-v3-birth-design-review.md) | raw SHA256 `a0f5d6a4515104ffc2f25ed0119b565c318df861471ee886093959f4048d14fd`; storage-only approval and callback precision, not implementation acceptance |
| Assigned source baseline | `bd479050ddd2d9c6b6964f89fe44cfc895273d6b` |
| Main HEAD throughout inspection | `59b74ceb4e3b90c2c875bb5eca56bbf8a102c384`; `git diff --name-only <baseline> HEAD` contains docs only |
| Worker / protocol / rounds | raw SHA256 `7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9` / `bd5f1b2878c533aeadd6e69d2c5b3a830e52b135f808e12d283f9251c8068a09` / `ad9fba3d3f675ec0a91dc07a4224852482e0b75730218b5feaecb3f342abe310` |

The capacity proposal was already untracked at entry. No M1b implementation worktree was inspected or changed. Line references below identify the assigned source, not a post-M1b product candidate.

The raw requirements remain: complete LF-inclusive UTF-8 observation bytes and raw SHA; a single 10,000,000B artifact admission limit; complete 32,768B S/H and actual SDK Payloads boundaries including metadata; 2KiB Memo; complete retained originals on rejection; original once-only opportunities, stop/reaper ownership and nonrenewable BOOT windows. Only complete acceptance, durable prefix, real predecessor/native gates and the real new V2 may authorize a successor. The amendment changes delivery order, not those contracts.

## Staging and ownership judgment

The decomposition follows the current callers. There is no round-observation writer/ref consumer, collect/reconcile-round implementation or registered V2 class in the inspected product. The existing worker [stop-chain observation](../../src/ergora/reference_training_worker.py#L579) is pretty-encoded `ExecutionRecords.observe`, not the approved full round-observation shape. Converting that legacy file to make a new serialization test pass would change the wrong contract.

M1c-T can verify the existing `_CycleOperation → S → processes.run → H → PhaseFrames → invoke` transport lifecycle without inventing a product diff. M1c-O belongs with the actual H acceptance composition in M2a and collect publication/durability in M3a. M1c-R belongs with `CycleAdmission.bind`, `BudgetedStart.source`, `validate_context`, `Execution.current` and isolated native consumers in M5a. M1c-V belongs with actual dispatch and the registered V2/activities in M6a. The proposal explicitly requires each containing slice's capacity acceptance and keeps the cumulative successor gate closed. This is coherent with storage-only M1b.

Reusing `protocol.ARTIFACT_LIMIT` is correct: M1a already established that constant and `training_rounds.MAX_INDEX_BYTES` aliases it. A second same-valued constant or an unused generic reader would add no responsibility. The private H lifecycle can remain with its one actual owner. No fake collector, test-only future pipeline, archive reader, ledger, service or configurable transport limit is justified.

## D1 — P3, nonblocking: distinguish existing V1 checks from its missing consume recheck

Location: [capacity proposal, line 27](../plans/2026-11-16-training-cycle-measurement-capacity.md#L27).

The row lists V1 `_capacity/status/request_stop/_ordinary/_consume/run` and says complete converter checks exist. Actual calls cover input (`run:1520`), outgoing ordinary/stop requests (`1261/1492`), signal (`1229`) and query/outcome through `status:1223`. **`_consume:1306` does not call `_capacity(value)` on the complete received activity envelope.** Its exact-shape/facts checks and the activity's separate result check are not that Workflow-side recheck.

Consequence: the inventory can mislead a later implementer into treating received-envelope verification as already provided by the V1 consumer. The proposal's future V2 ledger still requires the check, so this does not invalidate the staged design or establish a V1 execution exploit.

Minimal correction: state precisely which V1 checks exist, explicitly record that its `_consume` lacks the final-envelope capacity recheck, and retain that obligation at the real V2 `_consume` boundary. Preserve V1 commands; this factual repair does not require a V1 behavior change, new guard or test.

## Required open contract: oversized parent-request retention

Proposal lines 24/30 correctly leave this incomplete. `_CycleOperation.__init__:79–83` encodes the full request and raises before assigning `self.output`; `_run` has not spawned S. S's exact `request.json` and H's `helper/stdin.txt` therefore cannot retain that rejected payload. The SDK wrapper at `1671–1673` logs exception text. Stop fanout at `1003–1013` creates a fresh UUID in its inline failure, so its record does not preserve the rejected constructor's raw identity. Complete source/input/snapshot originals and the received SDK request remain useful evidence, but do not prove preservation of the exact assembled unsent S/H payload.

This is reachable at an existing seam: `test_cycle_sdk_capacity_failure_finishes_peers_and_keeps_original_bytes[operation-request]` passes an SDK-sized stop request whose snapshot/context expansion makes the stop-writer constructor fail. The check observes peer completion and inline capacity failure; it does **not** assert exact rejected-request retention. The separate launch-material test protects an occupied native start intent and likewise does not close this constructor gap.

The accepted wire requires the complete unsent material; this review grants no waiver. Before full M1c/new-wire transport acceptance, a separately reviewed design must identify a bounded, supervised owner, exact raw payload/operation identity, original deadline/cancellation/reaper behavior, and the result when retention itself fails or is interrupted. A full synchronous log/disk write in the SDK event loop, an unowned thread/process, reconstructed subset, second ledger or new window is not an approved repair. M1c-T may complete a truthful verification record with this contract still open; it cannot report full M1c acceptance. When recording the amendment, retain this as an explicit blocking follow-up under the existing request owner, with a closure gate, rather than allowing it to disappear between the O/R/V slices.

The other frame issue has a different evidence status. `cycle_operation_main.frame:1078` checks the initial full frame and emits a smaller failure without rechecking it. The approved new-wire second check remains a required integration obligation. No ordinary reachable case where that replacement also exceeds capacity was established here; this is not grounds for a new present-product guard or fabricated end-to-end test. Preserve the 65,536B stopped control frame, full stdout and incomplete/unknown behavior if a real new-wire result cannot be sent.

## Probe audit and actual missing acceptance

Read the retained `probe.py`, `argv.json` and `result.json` in ignored `.ergora/checks/cycle-measurement-capacity-design/`; did not execute them. Their raw SHA256 values are respectively `7205f79ce509149138a912b07dd9bb858429a8d154d18bdefbbce4359db932f2`, `e5cfb29cc923dc1de96b2698de48cdd08bcc2fc383bd35a434982f2432a810b0`, and `accc9d4faaa41d15b08bbab82b89c4e0c2bf35dd46800b078fdf3ee234f61fa0`.

The recorded Python 3.11.15/SDK 1.34.0 default-converter observations match the code and proposal: synthetic observation bytes including one LF are M−1/M/M+1; Payloads are 32,767/32,768/32,769B and match the local Workflow wrapper; 32,768 JSON bytes become 32,800 Payloads bytes; 32,768 H stdout bytes become a 33,365B synthetic full result frame. Its failure frame is 700B. This supports neither a reachable oversized failure-frame claim nor arbitrary codec compatibility.

The observation uses empty identity/context/facts/native/execution/evidence placeholders. It is intentionally not a valid production observation and exercises no writer, ref reader, fsync, timeout, SDK invoke or new Workflow. These are design observations only.

Still required, at the actual owners and exact accepted candidates:

- M1c-T: select/reuse candidate-bound existing transport checks, retain their actual commands/results and service-double limits; independently review a demonstrated fix if any. Historical results do not automatically certify a post-M1b candidate.
- M1c-O: a valid full observation lifecycle at M−1/M/M+1 with multibyte UTF-8/LF, legal values above 1MiB through the same writer/readers, aggregate-over-M originals without refs/ready, and partial-write/fsync/deadline/reply-loss behavior in the original S/H window. No helper-only roundtrip substitutes for this.
- M1c-R: explicit `read_raw(path, ARTIFACT_LIMIT)` at real H/budget/context/native use sites, fixed ordinary same-root path, exact bytes/raw SHA and full binding checks; source/stop/clock/old-prefix failures must refuse actual later actions.
- Real H stdout/frame and assembled SDK result boundaries, complete facts/acceptance/operations/outer identity/metadata and all N32 branches including inline unknowns, original stdout hashes and peer cleanup. Existing `cycle_sdk_activity`/`cycle_operation_fault` retain real S/H and ActivityEnvironment with service doubles; legacy N32 is not v3 acceptance.
- M1c-V: full started input/Memo before real claim/send, complete V2 ordinary/stop/inbound/result/consume/signal/query/outcome measurements and installed converter correspondence on the registered program, original once-only effects and continuous BOOT deadlines. Full M1c also requires closure of the parent-retention contract above.

Inspected existing submission/runtime fixtures and their assertions, including metadata, oversized stdout/frame, aggregate failure after peers, constructor failure, occupied launch intent, N32 refs and sandbox signal/query/outcome seams. No suites, probes, replay, services, installation, network, model or training ran; no product/tests/PLAN edits, commit or push. M1b implementation, M2/M3/M5/M6, installed/live two-round acceptance and training quality remain outside this design verdict.

Static report checks: relative links resolve; `git diff --no-index --check /dev/null <report>` emitted no whitespace diagnostics (exit1 denotes the new-file difference, not exit0). The reviewed proposal's SHA remained unchanged. Final shared-tree status also showed another agent's M1b delivery update; this reviewer did not edit that file.

## D1 bounded re-review

2026-11-16. The same independent reviewer read the revised proposal and independently confirmed raw SHA256 `c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`. The original reviewed SHA `3fa65a8804b5061de2a325a3b21c98ef92857d1edcf88de58385fd7957cffa2b` and finding remain historical evidence above.

The V1 inventory now explicitly states that `_consume` does not recheck the complete received envelope, preserves V1 history/commands, and assigns the complete inbound-envelope check to the real V2. The D1 disposition retains both that new check and exact oversized parent-request retention as mandatory, unimplemented gates. The header accurately limits approval to bounded staging/M1c-T and states that full M1c remains open. **D1 closed; no new finding in this correction. Requirements and maintainability remain approve for the bounded staging amendment, open findings 0/0.**

This re-review does not close the parent-retention contract, any M1c integration gate or product acceptance. It only read the correction and appended this section; no source/tests/PLAN or other file was changed, and no probes, suites, services, installation or network ran. The report's whitespace check again emitted no diagnostics (new-file diff exit1).
