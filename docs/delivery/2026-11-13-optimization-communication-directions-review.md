# B2d communication-direction independent review

Date: 2026-11-13. **Final local verdict: Spec passes within the readonly-proposal scope; Standards passes, ST1 closed, no new findings.** The package/material and nine-call handoff evidence is accepted. Ordinary publication and this candidate's own CI remain pending. This does not grant native training, performance, numerical/quality/recovery, GPU/multirank, heterogeneous-backend or adoption acceptance.

The initial r2 review below is preserved with its original finding and pending evidence. The [final r3 re-review](#final-re-review-of-r3) records their disposition and supersedes those local pending items.

## Review identity and boundary

The independent coordinator `/root/communication_directions_review` started with a fresh context. It launched fresh-context, parallel `standards` and `spec` reviewers using `fork_turns: "none"`. Their reports appear separately below; findings are neither merged nor reranked across axes. The implementation conversation and a proposed verdict were not supplied.

Applicable instructions were root [AGENTS.md](../../AGENTS.md), [PLAN](../PLAN.md), the maintainable-project-delivery independent-review brief, code-review and codebase-design skills. Standards also inspected the definition, backend and testing documentation. No applicable repository `CONTRIBUTING.md` or `CODING_STANDARDS.md` was found; frozen upstream templates are not this change's standards.

Raw acceptance sources were the [communication plan](../plans/2026-11-13-optimization-communication-directions.md), [specialist plan](../plans/2026-11-13-specialist-presets.md), especially B2/B3 and common inheritance/backend acceptance, and [R3 research](../research/2026-11-12-optimization-communication-agents.md). The originating requirement is complementary, individually configurable specialists and backends, nested serial/parallel templates, complete ancestor materials, and child authority bounded by ancestors. This slice is specifically three readonly proposal roots; actual communication/training execution remains with the original runner and owners.

The fixed baseline and inspected HEAD are `a9fcc17d17a91d1df54fbfb65ed8921837d3eb1a`, on `refactor/architecture-foundations`. `git rev-parse` resolved the baseline; `git log <baseline>..HEAD --oneline` was empty. Therefore `git diff <baseline>...HEAD` is empty and cannot represent this uncommitted slice. Review instead used the explicit tracked/untracked snapshot under private `.ergora/checks/optimization-communication-directions/`:

- `review-r2/manifest.json`, SHA256 `f5af115d6c0e04ca214441e805eabf6c92d78d64d5a11e6dc4d77ccfef057318`;
- all full contents in `review-r2/files/`, plus `review-r2-tracked.diff`;
- `product-paths.json`, identifying the eleven product/test files.

All seventeen frozen files' sizes and SHA256 values were independently recomputed; live bytes matched at initial inspection. The snapshot contains six changed tracked files (`docs/PLAN.md`, `docs/TEMPLATE_WALKTHROUGHS.md`, `docs/TRAINING.md`, the specialist plan, catalog and existing preset test), the new communication plan and delivery record, and all nine new files under the TP/DP-overlap, MoE-dispatcher and MoE-overlap proposal roots. After review began, the author changed status documentation to address ST1 and record newer call outcomes; those later bytes are outside this frozen initial verdict and require the final snapshot check.

Read-only inspection included the existing catalog installer, CLI/HTTP consumers, manifest/input compilation, resource inheritance, backend admission, shared exact v2 workflows/experts/Skills and neighboring direction roots. Only this review report was written. Reviewers did not install packages, start or stop models, run suites, modify product files, read credential configuration, or commit/push.

## Independently checked evidence at the initial review

Evidence locations below are private relative paths under `.ergora/checks/optimization-communication-directions/`; they are not distributed product resources.

|Evidence|Observed result and limit|
|---|---|
|`install-r1/package-identity.json`, `source-manifest.json`, wheel and installed RECORDs|Coordinator independently compared all 530 live/source/wheel/installed product files byte-for-byte. Wheel SHA256 is `d670881e158a6aa1ed3f2a8bcbdb95e9eac63386fee40a615efafa696442c9d2`; all 538 wheel RECORD rows and 543 installed RECORD rows passed hash/size recomputation. All eleven source overlays match the frozen product/test bytes. This is the existing noneditable Python 3.11.15 installation, not a new reviewer install.|
|`baseline-identity-r1.json`, `reference-r1.stdout.txt`|Independent comparison against the baseline archive found 521 existing product files, only the catalog changed, and nine new data files. All 283 frozen reference files remain byte-equal. Both axes verified preservation of the thirteen old catalog entries. The recorded reference verifier passes without starting its runtime.|
|`install-r1/preset-suite/result.json`, `process/stdout.txt`|Recorded installed preset suite: 23 passed in 96.46 seconds; outer process 98.197 seconds, return code 0. The three new direction parameters passed. Reviewers inspected the command, environment identity and original output but did not rerun pytest.|
|`collection-all-r1/`, `collection-group-{0..5}-r1/`, `collection-audit-r1.json`|Coordinator independently parsed the seven original phase streams' **collected** node IDs: full 1,711; groups 254/250/342/312/254/299; exact union and zero pairwise intersections, no duplicate selected IDs, all return codes 0. These are collect-only invocations of the formal installed-product CI runner, not full-suite or new-candidate CI passes.|
|`research/manifest.json` and six saved originals|Six HTTP-200 retrieval records identify Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0`: four communication Skills, `comm_overlap.py`, and `flex_dispatcher_backend.py`. Both axes and coordinator recomputed the saved original sizes/hashes. Spec compared the new contracts with the pinned implementations; stale Skill descriptions do not override source. No new network request was needed for this review.|
|`self-review-r1-codex.json`, `self-review-audit-r1.json`, `self-review-r1-codex/`|Original installed `ergora-structure-review@1.0.0` call succeeded in 35.6186 seconds and returned `approve`. Coordinator independently checked all eleven complete frozen product/test files (54,212 bytes) occur in the actual 60,445-byte prompt/stdin/protocol, which are byte-equal. Result SHA256 is `be07d524d19be4bcd6e9b7dd158c511409218bed8cd864bb88b9590d599cc3e4`; original and persisted result match. Its verdict covers the supplied structure packet, not independent upstream, suite or hardware acceptance.|
|`real-leaves-r1/tp-dp-overlap/`, `real-leaves-r1/moe-dispatcher/`|Six original calls succeeded. Coordinator independently rechecked original task/prompt/stdin/protocol/result hashes, complete original design/profile transfer to each measurement task, readonly permissions, native receipt hashes, and exact ancestor/own scope files against frozen input assets. All 36 resource occurrences, 63,601 bytes, have continuous complete UTF-8 read pages (TP/DP 18/31,409 bytes; dispatcher 18/32,192 bytes), with only list/read tools and no failed MCP call. Skill tree attachments were checked as individual files rather than confusing the tree digest with the SKILL instruction digest. Both measurements return `request-changes` for missing real experimental evidence.|

The original MoE-overlap design run `37cc585b20e74d9bb496c5e1426a53f8` timed out after 602.224 seconds at the original 600-second bound, CLI exit 1, with no persisted final result. The author's later diagnostics report connection/reconnection errors and preserved original artifacts; this is not a benchmark or a product correctness verdict. The replacement chain under `real-leaves-r2/` is explicitly outside this initial acceptance and will be checked from its own originals when complete. No reviewer restarted or terminated either run.

## Standards

Fresh-context Standards review of baseline `a9fcc17d17a91d1df54fbfb65ed8921837d3eb1a` and all 17 files in `review-r2/manifest.json` (`f5af115d…`). Independently verified snapshot/live hashes and sizes; HEAD equals baseline, so the reviewed change is uncommitted.

**Verdicts:** product maintainability passes within the inspected scope. One P3 documentation-standard violation needs correction. Overall acceptance remains pending the overlap leaf chain and this candidate's publication/CI evidence.

- **ST1 — P3, `docs/PLAN.md:13`: stale self-review status.** The checkpoint says “自身与fresh双轴待做,” but the scoped plan at line 31 and delivery record at lines 11/23 report the completed 35.619-second self-review. `AGENTS.md:9` requires updating PLAN when validation finishes; `docs/PLAN.md:57` likewise requires checkpoint updates. A recovering agent could unnecessarily repeat a completed model review. Minimum correction: distinguish completed self-review from pending independent review and record the current leaf-chain outcome, preserving the original overlap timeout.

No other documented-standard violations found in the inspected hunks. The catalog additions and nine new workflow/resource files follow specialist-plan lines 106–121: independent direction choices, exact shared v2 references, readonly permissions and complete local context. CLI and HTTP continue calling the existing installer; inheritance and permission checks remain in the existing compiler. The handbook additions accurately describe manual predecessor handoff and proposal-only scope.

**Smell judgment:** the repeated `"analysis"`/`"measurement"` workflow shape and instructions are self-contained, immutable configuration packages required by the agreed interface. No actionable duplication, speculative abstraction or new wrapper warrants correction.

The three additions at `tests/test_presets.py:18–20` reuse a meaningful public-interface check: installation, manifest preparation, offline reconstruction after removing source libraries, and complete context/permission preservation. No new assertion, test function or CI layer was introduced. Recorded installed verification is 23 passed in 96.46 seconds. Seven collect-only runs establish 1,711-item disjoint coverage, not regression success.

Performance impact is limited to selected direction materials and three test parameters; no execution algorithm changes. I inspected neighboring installers/compiler and recorded evidence without installing or rerunning suites/models. GPU, multirank, heterogeneous-backend and end-to-end training performance remain unverified, appropriately outside this readonly slice.

## Spec

Spec verdict: no actionable product findings in the frozen 17-file r2 snapshot (manifest SHA256 `f5af115d6c0e04ca214441e805eabf6c92d78d64d5a11e6dc4d77ccfef057318`), reviewed fresh against baseline `a9fcc17d17a91d1df54fbfb65ed8921837d3eb1a`.

- Missing/incorrect implementation: none found within this slice. The requirement “三个可选择的只读配方” (communication plan:7) is implemented through three catalog roots, exact v2 analysis/measurement references, complete declared contexts and readonly permissions.
- Unasked scope: none found. No backend, scheduler, training ledger, native runtime or duplicated MoE Agent was introduced. Manual single-leaf operation matches the scoped contract (specialist plan:98).
- Apparently implemented but wrong: none found. The contexts correctly distinguish requested/effective TP settings, ordinary/emerging optimizer paths, explicit `None=alltoall`, unsupported-backend errors, and plain EP overlap versus delayed wgrad. These agree with the pinned implementations, including graph/TE/recompute constraints.

Checks: independently verified all 17 snapshot hashes/sizes and live equality, six resource hashes, six upstream original hashes/sizes, preservation of all 13 previous catalog entries, and equality of 530 source/installed products. Inspected the complete nine new data files, tracked diff, shared workflows/Skills, permission/inheritance compiler, backend admission, existing parameterized test and original structure-review result/scope. Recorded installed pytest output confirms 23 passed; I did not rerun it.

Limits and remaining acceptance: B2d.3 requires “每方向 design／profile／measurement 真实独立调用” (communication plan:30). The r1 checkpoint records six successful calls, two measurement `request-changes` decisions, then MoE-overlap design timeout at 602.224 seconds without a result. Therefore third-direction runtime acceptance and final chain audit remain pending; this is an evidence limit, not a demonstrated product defect. The isolated r2 retry requires later review. No GPU/multirank, heterogeneous-backend, full-suite, new-candidate CI or publication acceptance is granted. No files were changed or processes controlled.

## Initial disposition and remaining acceptance

At the frozen initial review, ST1 is open. The author reports a subsequent live correction to the checkpoint and related records; final doc bytes and their consistency with completed/failed call evidence still need re-review. This report preserves the finding rather than replacing the frozen initial outcome with an unreviewed claim.

Next acceptance work is to check the complete replacement MoE-overlap three-leaf chain, its full ancestor/Skill files and unmodified original predecessors, all original failure artifacts and process-ownership limits, then verify the final documentation snapshot and close or retain ST1 with evidence. Ordinary publication and this candidate's own required CI are later gates. Prior `9250bf8` CI, text-only calls, fixture mesh/model/backend specifications, a provider availability probe, configuration, rank-zero logs and upstream examples do not establish real initialization, GPU/multirank correctness, training quality, performance or adoption. B3 native experiment acceptance remains with its original manifest/runner/evidence/approval owners.

Initial findings by axis: Standards 1 (worst P3 ST1); Spec 0. Product maintainability/spec findings 0/0 within the inspected scope; full slice acceptance remains pending the evidence and records listed above.

## Final re-review of r3

The same two axis reviewers rechecked fixes and completed evidence within this slice. The final inspected snapshot is `review-r3/manifest.json`, SHA256 `ddb516812bcd4a9e430564fa6b69c40c98d600088a7d833954e0a89d741a7c8a`, against the same baseline/HEAD `a9fcc17d17a91d1df54fbfb65ed8921837d3eb1a`. All nineteen snapshot files' sizes/hashes and live equality were independently recomputed by coordinator and both axes. All eleven product/test files are byte-identical to r2; only status documentation, the public evidence projection and this review record were added or changed. No new product behavior, assertion, test function or CI layer needs another runtime check.

The r3 snapshot includes the initial version of this review report. This final extension is the authorized review output and is the sole post-snapshot change made by the coordinator; it is not claimed to have been included in its own input hash.

### Final original-evidence acceptance

The coordinator independently revalidated all ten original attempts with the installed, read-only `inspect_input` verifier, including the entire frozen input bundles and copied runtime bundles. Their computed input digests, complete task/prompt/stdin/protocol bytes, readonly permissions, structural instructions and all ancestor/own files match. Each successful native final message parses to its persisted original result. Each measurement task contains both complete original predecessor results, with the exact saved digests. Scope listings, native receipts/streams, individual UTF-8 read pages and result hashes match the raw audits.

|Original chain|Calls and complete resource evidence|Outcome|
|---|---|---|
|`real-leaves-r1/tp-dp-overlap/`|3 successful calls; 18 occurrences / 31,409 bytes|Measurement `request-changes`; missing real training evidence preserved|
|`real-leaves-r1/moe-dispatcher/`|3 successful calls; 18 occurrences / 32,192 bytes|Measurement `request-changes`; missing evidence and differing predecessor timing proposals preserved|
|`real-leaves-r2/moe-overlap/`|3 successful calls; 18 occurrences / 32,702 bytes|Measurement `request-changes`; missing evidence, reversed A/B labels and dispatcher alignment requirements preserved|
|Preserved `real-leaves-r1/moe-overlap/` design|1 failed attempt; 6 occurrences / 10,965 bytes, counted separately|`timed_out`, 602.224 seconds, native return code −9; no result or final native-readiness summary|

The nine successful calls contain 173 original native events and 54 resource occurrences totaling 96,303 bytes. Every resource has continuous complete UTF-8 coverage through the last page, and every successful scope exposes only the exact declared ancestor/own files through list/read. The failed attempt has 28 original events, eleven reconnect errors (one response-body/stream error followed by ten waiting-network errors), complete material reads and no successful final result. Its failed status remains intact.

The successful retry's design input digest and prompt are identical to the failed original, including exact prompt bytes. The saved retry driver selects only MoE overlap in a new State and specifies 240 seconds per model call and 290 seconds for the outer subprocess. The original six successes and original 600-second-bound failure were not replaced or rerun. The bounds and elapsed times describe text-model calls, not training budgets or measured performance.

The [public evidence projection](evidence/2026-11-13-optimization-communication-directions.json), SHA256 `320971844b46a8735e8f28de125260e727623a313b047ab48fe21ad475b1fdbf`, matches all three successful raw audits, original failure audit, self-review audit, collection summary, package identity and post-call observation receipt. The coordinator checked its call identities, bindings, predecessor/result/input hashes, counts, byte totals and referenced audit hashes against the originals. The public projection is a faithful summary; it does not replace the raw model replies or experiments that remain absent.

The original structure-review bundle was also reverified with `inspect_input`: its frozen/runtime inputs and digest agree; all three original structural resources match their audit and occur in the actual prompt. The eleven-file 54,212-byte packet, 60,445-byte actual prompt/stdin/protocol, original `approve` result and previously inspected installed 23-pass suite remain bound to the unchanged candidate. The seven formal collection streams still establish the exact 1,711-item disjoint union, not a regression or remote-CI pass.

The original replies substantiate the new delivery statements: dispatcher design proposes five pairs with 20 warmup/100 measured steps, while profile proposes three alternating pairs with 20/50; overlap design and profile reverse baseline/candidate letters and do not yet freeze the same dispatcher. Their independent measurement leaves explicitly require reconciliation. These are useful proposal findings; no executable candidate, correctness pass or optimization gain is inferred from them.

The final process receipt records one post-call observation with no matching processes under its stated root/argument selection. Its saved producer and documentation explicitly limit this to a bounded end observation, without whole-run or detached-descendant sampling. The models GET200 record is only an availability observation; no inference or hardware conclusion is derived from it. Reviewers did not perform a new network request or process observation.

### Standards — final re-review

Standards verdict: **pass within the inspected scope; ST1 closed; no new findings.** This same-slice re-review preserves the initial finding and verdict as historical results.

Inspected baseline `a9fcc17d17a91d1df54fbfb65ed8921837d3eb1a`, the complete r3 tracked diff, and all 19 files in `review-r3/manifest.json` (SHA256 `ddb516812bcd4a9e430564fa6b69c40c98d600088a7d833954e0a89d741a7c8a`). Independently recomputed every snapshot/live size and hash. All eleven product/test files remain byte-identical to r2.

**ST1 disposition:** `docs/PLAN.md:13` now records the completed 35.619-second self-review separately from pending final independent review and publication. The scoped plan, delivery record and specialist checkpoint agree. This satisfies the update requirements in `AGENTS.md:9` and `docs/PLAN.md:57`. The original timeout remains explicitly preserved.

Checks against raw originals confirmed:

- Nine successful calls' prompt/stdin/protocol/result identities, readonly permissions and complete predecessor transfer.
- All 54 resource occurrences, totaling 96,303 bytes, read continuously as UTF-8 through the final page.
- Public call fields, audit hashes, self-review fields, collection summary and post-call observation identity match the corresponding private records.
- The original overlap failure retains `timed_out`, native return code −9, eleven network errors, six complete resources/10,965 bytes, no result and no final native-readiness summary. The retry's input and prompt match the failed call; its script specifies 240-second calls and a 290-second outer bound.

The documentation accurately separates proposal disagreements and three measurement `request-changes` decisions from training evidence. It limits the models GET200 to availability and the final process observation to one bounded observation. Collection coverage is not presented as regression success; publication and this candidate's own CI remain pending.

The initial structure, reuse, test-value and performance assessment stands. Documentation-only corrections warrant no additional model or suite runs. No actionable smell was introduced.

Limits: read-only inspection only; no installations, model/suite runs, process controls or writes. This verdict grants no GPU/multirank, training-performance, heterogeneous-backend, adoption or publication acceptance and does not rerank Spec.

### Spec — final re-review

Spec verdict: pass within the B2d readonly-proposal scope; no new actionable findings. Reviewed r3's 19 files against baseline `a9fcc17d17a91d1df54fbfb65ed8921837d3eb1a`; manifest SHA256 `ddb516812bcd4a9e430564fa6b69c40c98d600088a7d833954e0a89d741a7c8a`.

Findings: none. The eleven product/test files are unchanged from r2. The requirement “每方向 design／profile／measurement 真实独立调用” (communication plan:30) now has nine successful original calls across the two rounds. Complete materials and manual predecessor handoff are supported. Three measurement `request-changes` decisions accurately preserve missing experimental evidence.

The final delivery claims match the original replies: dispatcher predecessors propose different timing schedules; overlap predecessors reverse A/B labels and require agreement on a common dispatcher (delivery:33). The docs retain these as proposal issues requiring resolution, without claiming an executable candidate or measured gain. No missing product requirement, incorrect implementation or unasked scope was found.

Checks: independently verified all 19 snapshot hashes/sizes/live bytes; nine original call/result identities; six complete predecessor-result transfers; prompt/stdin/protocol equality; native receipt hashes; and 54 continuous UTF-8 resource occurrences totaling 96,303 bytes across 173 native events. Public call fields and referenced audit hashes match originals. The retained failure has 28 native events, eleven reconnect errors, no result and no final native summary. Failed/retry prompts are byte-identical. Retry bounds match the saved driver.

Limits: the end-of-run `/proc` observation supports only its stated scope, not whole-run descendant sampling. The original timeout remains a failed attempt. No GPU/multirank initialization, numerical/quality/recovery result, measured optimization benefit or heterogeneous-backend acceptance is established. B3 execution, publication and this candidate's own CI remain pending. No files changed, suites/models/installations run, external calls made or processes controlled.

### Final disposition and remaining gates

ST1 is closed by the checkpoint correction and independent Standards recheck. All local product/material/call-chain and final-record evidence required for this readonly slice has been inspected; no blocking product or documentation finding remains. The seven reviewed public Markdown files had 168 resolving local-link occurrences before this final report extension; the report's added links are checked at handoff.

Ordinary publication, precise remote identity and this candidate's own required CI remain open. B3 still requires a real workload/manifest, compatible initialized runtime, independent all-rank numerical/quality/recovery and paired performance evidence, followed by the original owner's approval; no result here closes that work. The documented next data-only direction is profiling/memory-snapshot, without repeating broad research or changing the existing training/Forge owners.

Final open findings by axis: Standards 0 (historical P3 ST1 closed); Spec 0. The local readonly-proposal acceptance passes; publication and own CI have no pass claim.
