# Bilingual documentation and branch maintenance: batch 1 independent review

Date: 2026-11-16. Reviewer: fresh-context Codex reviewer `bilingual_docs_batch1_review`. Product/author documents were read-only; this review file is the reviewer's only write. Requirements, frozen changes and relevant implementation were inspected before the author's delivery narrative. No further reviewer was delegated.

## Scope and identity

- Review baseline and observed HEAD: `04af2344239306cb00458e89f81258093235f049`; product baseline: `c540939d3b3f38f3851b0de965c9cd0f969eea77`, on `refactor/architecture-foundations`.
- Frozen patch: `.ergora/checks/bilingual-docs-branch-cleanup/owned-docs.patch`, SHA256 `f7c36f8ac620e63ea52a49312c601af44c13717290599108ceb6f5ebf383710b`.
- Manifest file SHA256: `572e8df98095f1be6cd42b373d6d7f94bf51214a1a1b29f6660c67d4333e6781`. Its internal `scope_sha256` field is `a734d6b178b9c78fb105d6ccdbf9f3ea585dd456a104e9a69367d59e76f844cb`; these are different identities. The coordinator corrected the brief's initial description of that field. Every listed file's bytes, line count and SHA256 matched the manifest, and replaying the patch against the review baseline in memory reproduced all 12 current files.
- Complete reviewed files: `README.md`, `README.zh-CN.md`, `docs/README.md`, `docs/README.zh-CN.md`, `docs/BACKUP_RECOVERY.md`, `docs/zh-CN/BACKUP_RECOVERY.md`, `docs/EVIDENCE_REPORTS.md`, `docs/zh-CN/EVIDENCE_REPORTS.md`, `docs/TESTING.md`, `docs/zh-CN/TESTING.md`, `docs/plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md`, and `docs/delivery/2026-11-16-bilingual-documentation-and-branch-cleanup.md`.
- Other working-tree changes, including the root live plan and neighboring delivery records, are outside this slice. Root instructions and the live checkpoint were read for context. The maintainable-project-delivery independent-review brief and applicable repository-quality guidance governed this review.

## Two-axis result

|Axis|Verdict|Evidence|
|---|---|---|
|Requirement compliance|Approve with one nonblocking P3 correction|Five complete language pairs have reciprocal links and English default paths; commands, limits, recovery and pending capability boundaries agree across languages. Remaining guides, architecture and historical navigation have explicit later batches. No blanket translation/completion claim is made. Local branch cleanup meets the scoped deletion rules.|
|Maintainability|Approve with one nonblocking P3 correction|Existing guide paths and old anchors remain usable. Documentation uses existing CLI/backup/runtime owners and links to original evidence. No source abstraction, test framework, installation, scheduler or frozen-resource change is introduced. One CI timeout statement needs platform qualification.|

There are no blocking findings within the inspected batch. The wider documentation request remains open; this verdict applies only to the frozen batch and recorded local branch cleanup.

## Finding

**F1 — P3: qualify the CI job deadline by platform.** [English testing guide](../TESTING.md#maintain-tests-and-interpret-ci-evidence), line 22, says each matrix group has a 20-minute job limit; the preserved [Chinese counterpart](../zh-CN/TESTING.md#测试维护), line 20, has the same statement. The actual [workflow](../../.github/workflows/portability.yml), lines 34–46, includes Windows `group: all` in that matrix and sets Windows to 30 minutes, Linux to 20. A maintainer interpreting a Windows run or estimating timeout headroom from this guide receives an inaccurate deadline. Smallest correction: state “Linux groups: 20 minutes; Windows job: 30 minutes” in both language versions. This is a documentation correction; no workflow or test change is needed. Recheck bilingual/static parity after correction and update the Chinese-body-preservation claim to account for this explicit current-fact correction while retaining the baseline evidence.

## Checks and evidence

- Independently recomputed strict UTF-8/newline/whitespace and fenced-block checks for all 12 files; all 260 local relative file/directory links and Markdown fragments resolved. All five language pairs have reciprocal links and matching executable Bash/PowerShell/JSON blocks after excluding comments/blank lines. Manual prose review found matching scope, qualifications and recovery instructions.
- All original heading targets remain available: 19 in the root README, four each in backup/recovery and evidence reports, and one in testing. Compared the three relocated Chinese guide bodies directly with `git show` at the baseline, normalizing only navigation/relative link relocation; all three retain their complete original body. Scoped `git diff --check` exited 0.
- Parsed 43 distinct documented `ergora` invocations using the current source `ergora.cli.parser()` with placeholder revisions replaced by integers. All parsed successfully; no handler was dispatched. This establishes parameter syntax only. Source metadata confirms 33 presets and the documented `control`, `development`, `research` extras.
- Inspected the backup create/verify/restore owner, source CLI dispatch, evidence-report root/author/grant, restricted backend contracts, installer/profile metadata, installed-wheel CI runner/observation plugin and workflow. The README's schema3 disabled-effect boundary matches the explicit guard in `reference_training_worker.py`. The report guide accurately treats inner model JSON/HTML as prompt output with separate validation, rather than trusted runtime certification.
- Read the original branch inventory, deletion receipts and before/after refs. Saved inventory has 40 local refs and eight remote-tracking refs; the saved delta contains exactly the three documented local deletions and no other ref/OID changes. All receipts used ordinary `git branch -d` and exited 0. Independently checked each deleted OID is an ancestor of saved public `eba86805e5d50824eefb5e69edd0faab099cbf42` with zero unique commits. Each local ref is absent and its original OID remains referenced by the corresponding remote-tracking ref. None was attached to a worktree before or now; all 38 original worktree paths remain present.
- Read the author's 13 help/catalog/profile receipts and their stated limitations. They remain source/interface evidence, without transferring historical product/model/service/CI acceptance to this batch. Remote suggestions remain explicitly provisional; no remote operation was performed by this reviewer.

## Limits and handoff

No model, service, browser, installation, product suite, training workload, remote URL or network operation was run. No source, git index, ref, commit or push was changed. Static Markdown parsing does not certify rendered browser layout; parser success does not certify formal task execution or recovery. Existing product runtime/CI evidence retains its original candidate identity. HTML views were optional and were not produced or accepted in this batch.

The coordinator should record F1's correction or evidenced disposition and the affected recheck before marking batch 1 complete. Publication and all queued bilingual/historical batches keep their own acceptance work.

## F1 correction re-review — 2026-11-16

Read-only follow-up inspected the corrected English sentence at `docs/TESTING.md:22`, its Chinese counterpart at `docs/zh-CN/TESTING.md:20`, and `.github/workflows/portability.yml:46`. Both versions now explicitly state Linux jobs have a 20-minute limit and the Windows `all` job has a 30-minute limit, matching `timeout-minutes: ${{ matrix.os == 'windows-latest' && 30 || 20 }}`. Their meanings agree. **F1 is resolved; requirement compliance: approve; maintainability: approve; zero open findings within this batch.**

|Corrected file|Current SHA256|
|---|---|
|`docs/TESTING.md`|`5c5da4faf83afec5ea1f4208261b878f7bae1f8d072780c5d99615e9c1886d8d`|
|`docs/zh-CN/TESTING.md`|`b3274302acea8ef1f9e4572fc445f143a779dcba1c68d534968b05ecf93a4b13`|

The original freeze identifies the initial review; the two hashes above identify this correction. This follow-up checked only the two sentences against their existing workflow owner. No parser/link suite, model, service, installation, browser, CI or network check was rerun, and no other file was edited by the reviewer. The wider untranslated scope and original runtime/publication limits remain as recorded above. The coordinator owns the corrected delivery/status records and final artifact manifest.
