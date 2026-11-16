# Independent review: bilingual Projects guide

2026-11-16. Fresh-context independent Codex reviewer; sub-batch2a only. The reviewer received the raw language/navigation requirements, exact baseline, six-file scope, complete tracked/untracked patch and actual check artifacts, without an implementation conversation or proposed verdict. Product and candidate documents were read-only; this report is the sole reviewer write.

## Verdicts

- **Requirements: approve.** The English-default guide and complete Chinese counterpart have matching scope, examples, supported behavior and limitations. Original registration, task, recovery and explicit-import coverage is retained. All five original Chinese heading targets remain reachable at the English path. Both indexes link the full pair; the plan and delivery leave USAGE/WINDOWS and the remaining batches open.
- **Maintainability: approve.** The guide keeps operational instructions in the existing guide, links to the schema and current implementation plan for detailed S1 boundaries, and preserves existing command and recovery owners. No source, configuration, dependency, preset, reference, test or CI change was introduced. The bilingual duplication is required by the language contract and remains semantically aligned.

**Findings: none within the inspected scope.** No blocking or nonblocking correction is required for this guide pair.

## Inspected candidate

Documentation baseline and observed HEAD: `7fc42177db11fbfe4c9adb33342ecb5da4ed0434`, branch `refactor/architecture-foundations`. Accepted product: `6cec589f404b17f4828a70807d5e33d89fad3fa0`. The product paths inspected have no diff from that product identity. Concurrent S2 design, handoff, root-plan and publication-status edits were excluded and left intact.

The complete scoped patch is `.ergora/checks/bilingual-projects-guide/r1/complete.patch`, SHA-256 `a1252e6d8ac2291e26b7c76d783e8575864908fc610b423cb4baf30fad53f7a2`. The reviewer verified its hash and reconstructed all six patch results in memory against the baseline, including both new files; each result matched the current bytes and `scope-manifest.json`.

|Reviewed file|SHA-256|
|---|---|
|[English Projects guide](../PROJECTS.md)|`3ca1b8062a3166f3bd50cab0c081cba7508bf251c913fc18d3f669774b1a61e2`|
|[Chinese Projects guide](../zh-CN/PROJECTS.md)|`159c82e79e3ebd920aeb01f0389323199beb1ccf3023ef29240079c04bafaf28`|
|[English documentation index](../README.md)|`a98877b0162ed09fc97d0b3d00eb4323b9dbaa2c45624e03f556d194032e4778`|
|[Chinese documentation index](../README.zh-CN.md)|`110a38e90866c3613abe191e4731957241ca6a4ebf09020485f7c28106464f8e`|
|[Batch plan](../plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md)|`1ccd40dfc69eafe949ac2b11af514e866bcf33bae6ce3050cf5755a3f59db2e6`|
|[Slice delivery](2026-11-16-bilingual-projects-guide.md)|`47442c57bee9a173dcc41d3b239a2864b50615d72cab421720148906408f60ce`|

The original 125-line Chinese guide matches `git show BASELINE:docs/PROJECTS.md` and the saved `original-PROJECTS.md`, SHA-256 `ecc6da1187b4c22c7f35454f440bbd99bb43778401345fcc98b4a4fc84ff3be6`.

## Semantic and implementation inspection

The English guide was compared with the complete original and Chinese counterpart. Both retain lightweight versus unified projects, revision and binding rules, immutable native projections, original execution directories for old tasks, pending publication and saved-intent recovery, formal-task lifecycle links, HTTP entry points, and explicit legacy preview/adoption. Import documentation retains raw source-byte identity, whitespace-sensitive preview renewal, source conflict refusal, original-byte preservation, ownership restrictions and the absence of automatic takeover or in-flight-task migration.

The new S1 section was checked against `project-registration-v1.json`, `project-registration-v2.json`, `registrations.py`, `task_design.py`, `tasks.py` and `reference_executor.py`. It accurately describes complete policy/digest storage only on a first unified registration; refusal to upgrade an existing registration, including an empty v1 registration; refusal to re-register, replace or downgrade v2; and existing native projections disqualifying a first registration. `registrations.status` exposes effective requirements, `execution_supported: false` and unavailable actor assurance. Ordinary and budgeted task birth call the unsupported-policy guard; managed native execution also checks it before claims. The documented refusal codes match that guard. Neither language claims implemented S2, authenticated human decisions or executable design approval.

The retained operational claims were traced through `projects.py`, `registrations.py`, `reference.py`, task creation and native admission. CLI declarations/dispatch and `web.py` routes/payloads match the documented commands, revision inputs, preview digest and API responses. The HTTP middleware retains same-origin checks and the mutation request header. Formal execution remains Linux/WSL2-only; registration does not start services or models.

## Checks and limits

Independent read-only static checks passed for all six UTF-8 files: final newline/whitespace, closed fences, **146** local file/fragment targets, reciprocal language links, **six** matching executable blocks with comments excluded, and **five** preserved original heading targets. The complete original Chinese body is unchanged after excluding the explicit S1 addition and normalizing navigation/link relocation. Scoped `git diff --check` passed. Manifest identities and the complete patch were independently verified as described above.

The author's recorded CLI check was inspected: nine examples parsed through the installed SDK CLI with `-I -B`, stdout `9`, empty stderr, and no handler dispatch. The reviewer checked the relevant parser/handler source and did not rerun installed parsing or product behavior. The recorded static check predates final status-only changes to the plan/delivery; the final manifest and independent checks above cover the current six files.

No installation, product tests, model calls, service/browser runs, Temporal execution, Windows execution, training, human authentication, commit or push was performed by this review. The joint-product CI run `43833234533` is separate evidence and was neither queried nor inherited as translation validation. Coordinator status bookkeeping/publication remains outside this review; USAGE/WINDOWS and later documentation batches remain unfinished.
