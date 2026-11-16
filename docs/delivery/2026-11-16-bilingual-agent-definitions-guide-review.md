# Independent review: bilingual Agent definitions guide

2026-11-16. Reviewer: `bilingual_agent_definitions_review`, a new context independent of the guide author and coordinator. This review read the raw requirements, original guide and actual patch before the author narrative. It follows the repository continuity rules and `maintainable-project-delivery` independent-review brief. Only this report is written by the reviewer.

## Verdicts

- **Requirement compliance: approve** on corrected candidate r3. The complete translation, preserved Chinese guide, examples, navigation and runtime boundaries satisfy the inspected requirements. The initial r2 verdict was request changes for F1/P3, now corrected and rechecked below.
- **Maintainability: approve**, with no maintainability findings in this documentation-only scope. The pair uses existing guide paths, source owners and navigation; no new abstraction, product path or execution mechanism is introduced.

F1 was an inherited factual discrepancy retained in both guides, not a translation-induced product regression. Its small bilingual correction is closed. **No open findings remain within the inspected scope.** No source change was requested or made.

## Exact candidate and scope

The inspected branch is `refactor/architecture-foundations`, with documentation baseline and local HEAD `2273a50ddd0a1f3474e502b151cf12da0d0d3b22`. Public product source is unchanged from `6cec589f404b17f4828a70807d5e33d89fad3fa0`. Other modified/untracked workflow, handoff, plan and delivery files in the shared worktree are excluded.

The initial coordinator six-file candidate was `.ergora/checks/bilingual-agent-definitions-guide/coordinator-review-r2/complete.patch`, SHA256 `f879a2c0c02e66cec5d32ff5683ec88af3102d46b15fdcee3ec407c3882722d7`, with its adjacent `scope-manifest.json`. The reviewer independently applied every hunk in memory against the baseline, including both new files, and verified the resulting bytes against all six files and manifest hashes at initial review:

|File|SHA256|
|---|---|
|`docs/AGENT_DEFINITIONS.md`|`ce67b6386c693179d8f3fe7271c636dae20a1cf622447dfef1b2609c43cce35b`|
|`docs/zh-CN/AGENT_DEFINITIONS.md`|`296688036bf956718a057f2cdbde0e7bc958a8b74897c2b236c14c72c1cc711e`|
|`docs/README.md`|`e50e206ef63bc7aee987a3487143aee222493898b653ff730ca68f7861c9e2c1`|
|`docs/README.zh-CN.md`|`aaac227fc80f0abfd2c457749aff6eb923e78ee378db8e739d71be02e2c5f44c`|
|`docs/plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md`|`9e7dbca2477e33470a6bfb2737e2764925179803e542f14cc3a82be9ff0dfe5f`|
|`docs/delivery/2026-11-16-bilingual-agent-definitions-guide.md`|`200f37325ecdf55dd9815b3524abea525c474586138d19ed1379e27f9e0f3248`|

The original Chinese guide has 212 lines / 25,006 bytes, SHA256 `6552a58a0f9a2097b193e615ec1c8a4f4b7c9af0d745ffa31f8a193aa5570c2e`; its saved private copy independently matches `git show` at the baseline. The original three-author-file freeze remains separately identified by `author-freeze-r1/complete.patch`, SHA256 `21c9cc5a2ba3de8e8a7efb54ca935fe47fad377a67af3ee08db2cd0fe5e6781a`. Both guide hashes matched that author freeze at initial review; the corrected r3 has its own identity. Coordinator navigation and delivery bookkeeping do not inherit three-file validation automatically.

The **approved corrected six-file candidate** is `.ergora/checks/bilingual-agent-definitions-guide/history-fix-r3/complete.patch`, SHA256 `ae2dd6377d655d492c70541e815549d13012978bcb54c69881361fa49b96e59d`, with adjacent `scope-manifest.json` and `static-checks.json`. The reviewer independently reconstructed that full patch and verified every current file/hash again. Only the following three files differ from r2; both indexes and the batch plan retain the exact hashes in the initial table:

|Corrected file|SHA256|
|---|---|
|`docs/AGENT_DEFINITIONS.md`|`91fa3d60aa17c0482a5aead23e9cc40ed9791cbc1c54976d99eb2ea13f47bd84`|
|`docs/zh-CN/AGENT_DEFINITIONS.md`|`2cf5fcf78e7bd5e4deec74df6855b9d648bbcc3b47ee6adf570046da633ab739`|
|`docs/delivery/2026-11-16-bilingual-agent-definitions-guide.md`|`2c38d642b039c49d7e14c925e9cd45afdb9ce265fa85991f6be37e0b7c876cf9`|

## Finding

**F1 / P3 — closed: describe the applied-history budget as a target with a retained-current-snapshot exception.** The initial [English guide](../AGENT_DEFINITIONS.md#edit-a-specialist-agent-in-the-console), line 191, and [Chinese guide](../zh-CN/AGENT_DEFINITIONS.md#在页面编辑专长-agent), line 183, said browser history contains at most 50 entries totaling 4 MiB. In `src/ergora/data/console/definitions.js:134`, `editorSnapshot` counts custom applied JSON/YAML and complete resource-operation bytes; at line 247, eviction runs only while `history.length > 1`. The newest snapshot is therefore retained even when it alone exceeds 4 MiB.

A reachable source-level example is separately applying about 2.2 MB of valid JSON formatting and YAML comments for the same definition. Each conversion request fits the 4,000,000-byte HTTP limit, unchanged semantics preserve both custom representations, and their combined snapshot exceeds 4 MiB. Large retained resource operations provide another reason the newest snapshot can be large. The initial candidate presented a hard memory/history cap that the console does not enforce.

Requested correction: state in both languages that older snapshots are evicted toward the 4 MiB retention budget, at most 50 entries are kept, and the current snapshot is retained even if it alone exceeds that budget. Preserve the separate browser-storage quota warning and 4,000,000-byte request limit. This finding comes from static source inspection; no browser or product scenario was run.

**Same-slice recheck:** r3 makes exactly one prose-line correction in each guide, with matching 50-entry/4 MiB target/newest-snapshot wording. The delivery explicitly records the correction to original line 173 and retains the old author receipts under their original identity. The correction agrees with the existing eviction loop and leaves the separate quota/request boundaries intact. The reviewer repeated all six hash/patch, UTF-8/fence, 190-link, 11-old-target, 9-literal-block, 123-ordered-inline-literal and scoped whitespace checks. Reversing only the disclosed one-line fact correction in addition to navigation/availability changes restores the full Chinese guide byte for byte to the original. Product source remains unchanged. No parser, handler, browser or model run was repeated. F1 is resolved without broadening the slice.

## Checks performed and evidence boundaries

- Read the complete original, English and Chinese guides, including all literal examples and the resource editing, undo/redo, buffer restoration, storage and historical-admission tails. Compared the full English prose against the original requirements and original sections; this is a complete guide, with no summary replacement or omitted tail.
- Independently verified strict UTF-8 and closed fences across the six files; reciprocal guide links; all **190 local links/fragments**; all **11 original heading targets** at the English-default path; all **9 original fenced blocks byte for byte**, including Python; and all **123 original inline-code occurrences in order**. At r2, removing only the disclosed availability section/navigation and reversing relative-link relocation restores the Chinese guide to the exact original bytes; r3 also reverses the disclosed one-line history-budget correction, as checked above. Scoped tracked `git diff --check` passes.
- Verified every one of the **23 immutable author receipt hashes**, the author patch hash, and all **21 recorded source-owner hashes** against current files. Compared the **14 original fenced Ergora argv lists** independently with the frozen parser input. The author's recorded `-I -B` installed-SDK `parse_args` invocation reports 14 examples, zero errors and no handler dispatch; the reviewer did **not** rerun it or execute the examples. Placeholders remain literal.
- Inspected `agent_definitions.py`, `agent-definition-v1.json`, `definition_bundles.py`, `asset_trees.py` and `skill_assets.py` for current admission versus historical integrity, exact identity, resource completeness, executable-bit identity, immutable publication, accepted resource candidates, retries and bounded file reads. Inspected `backups.py` for the original platform/path and stopped-writer recovery boundary.
- Inspected `workflow_definitions.py`, workflow schemas, `agents.py`, `agent_backends.py`, `components.json`, `tasks.py`, `task_envelopes.py` and `reference_executor.py` for ancestor material accumulation, permission narrowing, exact references, static manifest status, explicit effort fields, formal mode/member admission and frozen recovery. The guide distinguishes supported six-stage review/work-unit execution from arbitrary topology/general Repeat, and explicit requests from the unimplemented unified selector.
- Inspected `web.py`, CLI declarations, `definitions.js`, `composition-graph.js` and `composition-comparison.js` for shared revision/read owners, exact-version browsing, full-window assembly and SHA verification, pending-edit invalidation, resource budgets, same-origin/request limits, buffer restoration, graph search and comparison. F1 is the only substantiated discrepancy found in this inspected scope.
- Confirmed public `task_design.py` rejects unsupported registered design-policy execution and `training_execution_protocol.py` rejects schema3 controller execution. The isolated S2 draft remains unreleased evidence; it supplies no delivered capability or acceptance to this translation. The plans and delivery correctly keep this review and publication pending and the remaining documentation batches open.

No install, model/backend call, credential/environment snapshot, service, browser, network operation, example handler, product test, CI run, staging, commit or push was performed. Static inspection and recorded parser declarations do not certify native option behavior, authentication, model quality or runtime recovery. Existing e5 CI and private S2 results retain their original candidates and do not validate this documentation slice. Remote publication verification is owned by the root coordinator and was not queried by this reviewer.
