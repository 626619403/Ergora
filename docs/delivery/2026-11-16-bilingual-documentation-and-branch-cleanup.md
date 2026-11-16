# Bilingual documentation and branch maintenance: batch 1

Status: all four complete batch3 guide pairs passed their own checks and fresh reviews with all findings closed, and their commits46017e1/31ce9a3/d73de13 plus earlier backend227 are now included in exact verified public9f3e693498834f071cf20d0f25c18555554765f1. SourceS2's own9f3/run43867345323 is terminal8/8 success; it has separate scope and documentation reviews do not confer runtime support. New batch4 authoring remains stopped until root follows up; batches4–7 remain open. Date: 2026-11-16.

[Plan and full remaining scope](../plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md) · [English documentation](../README.md) · [中文文档](../README.zh-CN.md)

## Request and baseline

The user requested cleanup of obsolete branches, documentation, READMEs and reports, with complete English/Chinese documents, reciprocal language links and English as the default. HTML reports are permitted. Batch 1 covers the entry points and three complete operational guides; the remaining living user/extension/architecture guides are explicitly queued in the plan.

Source baseline: `c540939d3b3f38f3851b0de965c9cd0f969eea77` on `refactor/architecture-foundations`. Initial remote-tracking development OID: `eba86805e5d50824eefb5e69edd0faab099cbf42`. Default `main`: `cab3a724e421d0a7d9ff6f03dfcbd3225361e2f1`. The package version alone does not identify the same features. Other active work and its untracked reports are outside this slice.

During the slice, the coordinator published documentation-only `04af2344239306cb00458e89f81258093235f049`, retaining the `c540939` product. The original branch-deletion proof uses the older saved public development OID and remains valid. This slice did not perform that publication.

## Documentation changes

|Complete language pair|Change and evidence boundary|
|---|---|
|`README.md` / `README.zh-CN.md`|Complete matching overview, installation, formal task journey, tools, training, improvement, operations and extension guidance. English is the default; original Chinese heading anchors remain available in the English default path. Clearly identifies development versus default `main`, frozen HTML scope, model/runtime prerequisites, explicit reasoning selection and disabled/pending features|
|`docs/README.md` / `docs/README.zh-CN.md`|Complete paired navigation for every top-level guide, living architecture guidance, live plan and dated evidence. Marks untranslated guides accurately and preserves original historical paths rather than presenting research or plans as delivered capabilities|
|`docs/BACKUP_RECOVERY.md` / `docs/zh-CN/BACKUP_RECOVERY.md`|Full English translation and preserved complete Chinese recipe, with correct relocated links. Keeps control-only versus whole-stack backups, stopped writers, original-path/platform requirements, external ownership and partial tar recovery limits|
|`docs/EVIDENCE_REPORTS.md` / `docs/zh-CN/EVIDENCE_REPORTS.md`|Full English translation and preserved complete Chinese author/manifest/export guide. Keeps read-only scope, source/coverage identity, all commands, untrusted inner model JSON and static HTML limits|
|`docs/TESTING.md` / `docs/zh-CN/TESTING.md`|Full English translation and preserved complete Chinese maintenance guide. Keeps installed-wheel scope, collection versus test success, explicit grouping, original phase evidence and interruption limits|

The remaining changed files are this delivery record and its plan: 12 owned Markdown files in total, four modified tracked files and eight new files at handoff. The original Chinese guide bodies are retained in full with language navigation and adjusted relative links. Historical reports, frozen reference/preset content and the single-file distribution retain their original bytes.

The wider request remains open. The complete1272-line USAGE pair passed whole-guide static/parser checks and a new fresh two-axis review; one P3 was corrected/rechecked and no findings remain. Its exact seven-file scope is committed as `73b7d61c9b1f775ea14535483a773901e5ec6124`, not yet pushed. All four third-batch guide pairs are now complete and independently reviewed; their exact publication states remain separate. Five top-level guides still need full language pairs in batch4: TRAINING, TRAINING_REVIEW, LOCAL_REVIEW, IMPROVEMENT_WORKFLOW and INTEGRATIONS. The separately reviewed [Projects sub-batch](2026-11-16-bilingual-projects-guide.md) has a complete pair committed as `82c1c84` and published through e5. Five living architecture guides and the domain glossary, remaining maintained example/extension entry points, and topic/candidate historical indexing have separate accepted batches in the plan. No placeholder counterpart or index counts as a completed guide.

## Local branch cleanup

Before cleanup, all 40 local refs, 8 remote-tracking refs, OIDs, upstreams, merge relationships, worktree bindings and local status were saved under ignored `.ergora/checks/bilingual-docs-branch-cleanup/`. No fetch was performed. The saved public development snapshot is the ancestry boundary; worktrees and active design/training/reasoning/review branches are protected even if merged locally.

The following branches were rechecked at their original OID, proved ancestors of the saved public development snapshot with zero unique commits, found unused by worktrees, and deleted with ordinary `git branch -d` (all exit 0):

|Deleted local branch|Recoverable original OID|Reason|
|---|---|---|
|`feat/evolution-console`|`4c7426a4ce5b733bb32b32fc6fa2fe8438e05e9d`|Old console feature fully merged into public development; no worktree|
|`feat/windows-support`|`01d134492c557ec1458de44248a6cb3c5954ca9c`|Old Windows feature fully merged into public development; no worktree|
|`research/multi-agent-evolution-20261028`|`3b52365fe56d79c7b467a73e369b5a42c2b5afc9`|Old research branch fully merged into public development; no worktree|

The other 37 initial local branches and all 38 worktrees were retained. The full before/after ref lists and exact command receipts are retained privately. A deleted local branch can be recreated with `git branch BRANCH ORIGINAL_OID` while its retained commit exists. The corresponding remote-tracking refs were left intact, so these commits also remained referenced locally after cleanup.

## Remote suggestions: no mutation

Remote branches have not been fetched, deleted or pushed. The coordinator must re-read the live remote OID, current activity and merge relation before any separate remote action. The initial local tracking snapshot proposes only these old branch names for further review:

|Remote branch|Exact local remote-tracking OID|Observation|
|---|---|---|
|`origin/feat/evolution-console`|`4c7426a4ce5b733bb32b32fc6fa2fe8438e05e9d`|Fully merged into saved public development; local obsolete branch removed|
|`origin/feat/windows-support`|`01d134492c557ec1458de44248a6cb3c5954ca9c`|Fully merged into saved public development; local obsolete branch removed|
|`origin/research/multi-agent-evolution-20261028`|`3b52365fe56d79c7b467a73e369b5a42c2b5afc9`|Fully merged into saved public development; local obsolete branch removed|

`origin/main` and `origin/refactor/architecture-foundations` are protected. The prototype and both cycle-stop/review-related remote refs remain because they correspond to retained work/evidence; there is no blanket remote deletion recommendation.

## Verification and handoff

- Read the root cooperation rules, current plan, component protocol and applicable delivery/quality skills. No agent-instruction file was changed.
- Inspected current installation profile metadata, CLI parser/help, preset ownership, schema3 disabled-effect guard, backup owner and installed-product CI runner. CLI help/profile reads used the source checkout; they do not certify a new installation or runtime.
- All 12 owned Markdown files pass strict UTF-8, 260 relative-file/directory links and Markdown fragments, fenced-block closure, reciprocal language links for all five pairs, matching executable fenced blocks, every original translated heading anchor, portable-path and whitespace checks, plus scoped `git diff --check`. All three Chinese guide bodies match the preserved originals after removing navigation and normalizing link paths. The one-off checker/evidence live only under ignored `.ergora/checks/bilingual-docs-branch-cleanup/`; no product test or CI framework was added.
- Thirteen read-only source CLI help/catalog/profile reads succeeded. They verify the documented entry names/options and preset/profile facts without installation, models or services.
- Exact scoped contents, hashes and tracked/untracked diff are handed to the coordinator through private `scope-manifest.json` and `owned-docs.patch`. Independent semantic/maintenance review and publication are pending; this document does not claim either passed.
- Remote URLs, browser rendering, a new installation, product/service/model execution, training quality/performance and a new candidate's CI were not checked by this documentation slice. Original product evidence keeps its own candidate identity.
- No source/test/CI/resource edits, installation, model call, service start, training run, remote write, git-index mutation or commit was performed by this slice. Existing product runtime and CI results remain attached to their own candidates.
## Coordinator review and handoff

The [fresh batch-1 review](2026-11-16-bilingual-documentation-batch1-review.md) approved both axes. It independently checked the 12 frozen files, 260 links/anchors, five complete language pairs, 28 old anchors, three preserved Chinese bodies, 43 distinct source-parser examples and the three local branch deletions with all 38 original worktrees retained. One P3 corrected the testing guide's CI limit to Linux 20 minutes / Windows `all` 30 minutes in both languages; the same reviewer rechecked and closed it. No open batch-1 findings remain. The original author freeze and checks retain their original identity; the two corrected sentences and later status notes are coordinator follow-up, not part of that initial freeze.

Publication remains pending at this handoff. Batches 2–7 are still queued. The same author's separate backend-options research is written and statically checked, with its independent semantic review pending; it is not a new implemented feature. No model, service, installation or browser result is claimed for this documentation slice.

Coordinator continuation: all frozen batch files remain identical except the two independently rechecked P3 sentences and status-only plan/delivery changes. The exact 13-file scope (12 owned files plus its independent review) was explicitly staged and committed as `eb14df13a101681043fc8e94084ee3e409518b5b`. Other unreviewed research and unrelated working-tree documents were excluded. Remote publication is still pending; no remote branch was deleted.

The reviewed guide batch is included in the ordinary `7fc42177db11fbfe4c9adb33342ecb5da4ed0434` development-branch push; the complete remote OID was verified. Runtime/CI conclusions belong to the [joint product delivery](2026-11-16-design-capacity-integration.md), not the documentation static checks. Remaining guide batches and remote branch decisions are unchanged.

Sub-batch 2a now supplies the complete English-default Projects guide, full preserved Chinese counterpart and updated language indexes. Its scoped static checks and [fresh two-axis independent review](2026-11-16-bilingual-projects-guide-review.md) passed with no findings. Its original six-file review freeze retains baseline `7fc4217` and patch SHA-256 `a1252e6d8ac2291e26b7c76d783e8575864908fc610b423cb4baf30fad53f7a2`; later status bookkeeping is recorded separately. The exact seven files are committed as `82c1c84` and published through e5. The Windows pair passed scoped static/parser checks and a new fresh two-axis review with no findings; its exact seven files are committed as `13ea479`, published through e5; USAGE and batches 3–7 remain queued; no remote branch action or product/runtime result is claimed.

Installation batch 2 now has three complete, independently reviewed language pairs. Projects 82c and Windows 13ea are published through e5; USAGE's exact seven files are committed as 73b7d61c9b1f775ea14535483a773901e5ec6124, with publication pending. The e5 product's own official CI run43840394544 is terminal 8/8 success including Windows; it does not replace translation review or certify S2. Batches 3–7, their complete guide pairs and original evidence remain open.

Batch3 review handoff is closed for all four complete guides: backend, Agent definitions, workflow definitions and template walkthroughs. Each has a separate fresh reviewer/report; the three P3 findings (official-source attribution, soft history budget and delegated-actor attribution) were minimally corrected and rechecked. The walkthrough had no finding. Remaining staged publication uses each exact seven-file scope; no runtime/model/CI result is transferred. No batch4 authoring is started without root follow-up.

Publication continuation: root ordinary-pushed9f3e693498834f071cf20d0f25c18555554765f1 and verified its full remote OID. All four batch3 guide scopes and their own review records are now published, alongside the separately reviewed S2 source/howto. Its ownCI43867345323 is terminal8/8 success, not an inherited e5pass; no documentation result authorizes real-service/human/GPU or design/schema3 effects. No new batch4 authoring is started.
