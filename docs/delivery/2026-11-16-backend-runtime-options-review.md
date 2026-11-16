# Backend runtime options: independent semantic review

2026-11-16. Reviewer: fresh-context independent agent `backend_options_semantic_review`. Scope: bilingual research slice A6a only; product, research, and neighboring documentation were read-only. This report does not review or accept A6b–d implementation.

## Candidate and requirements

Documentation review baseline: `04af2344239306cb00458e89f81258093235f049`. Product baseline: `c540939d3b3f38f3851b0de965c9cd0f969eea77`. Branch: `refactor/architecture-foundations`. The branch advanced with separately reviewed work during this review; the baseline is not a claim about current HEAD. Other owners' product/documentation changes are outside this review.

The complete initial reviewed candidate consists of these two untracked files; the corrected accepted hashes are recorded in the re-review below:

|File|SHA256|
|---|---|
|[English research](../research/2026-11-16-backend-runtime-options.md)|`1190b14d27c829dc980a8761910a958a61bf5bb04fcb3fa71af51b132066781d`|
|[Chinese research](../research/2026-11-16-backend-runtime-options.zh-CN.md)|`1eea39aa99e453f343ad3cae104d86fa1df134c22e03c1caa669d2038a0e72fd`|

The complete scoped patch is `.ergora/checks/backend-runtime-options/owned-research.patch`, SHA256 `e471c4b0beb73b90bf78308f64aabc09a6377481bfd999c351e173fc183a3d35`: two new files, 278 added lines. The scope manifest, source manifest, handoff summary, static-check receipt, indexed source captures, and five local help/version receipts were inspected under that same evidence root. No recursive scan of the wider checks tree was performed.

Raw requirements were read from [the reasoning/parallelism plan](../plans/2026-11-16-agent-reasoning-and-parallelism.md): A6a researches Codex, Claude Code and the actual integrated backends, distinguishing native support, current public fields, existing passthrough, missing integration and unverified execution. A6b–d retain four per-instance selection modes, immutable resolution/recovery, original budgets and permissions, and requested/sent/native-observed-or-unknown evidence. Presets, planner selection and framework automatic selection are not implemented in this candidate.

## Initial verdicts

|Axis|Verdict|Reason|
|---|---|---|
|Requirement compliance|**Request changes**|One current-mode limitation of Claude `ultracode` is missing from both languages; F1 below needs a documentation correction.|
|Maintainability|**Approve within the research scope**|The research identifies the existing backend/driver owners, keeps native and framework controls separate, and proposes bounded typed extensions through existing consumers. No separate maintainability finding.|

The research otherwise distinguishes declared capabilities from observed availability, explicit binding requests from native applied values, CLI controls from API parameters, and single-invocation limits from Ergora's recovery/budget owners. It treats ChatGPT through Codex/provider configuration correctly, retains model/account uncertainty, and does not claim that the future selection modes already exist. English and Chinese convey the same substantive findings and limits; F1 is shared by both.

## F1 — P2: state the text-only mode's documented ultracode limitation

Locations: [English research, line 56](../research/2026-11-16-backend-runtime-options.md#claude-code-candidates-and-current-behavior), and [Chinese research, line 56](../research/2026-11-16-backend-runtime-options.zh-CN.md#claude-code候选选项与当前行为). The preceding adapter description at line 50 in each language also omits `--safe-mode` for text-only calls.

The current binding schema accepts `effort: ultracode`. In the reachable Claude text-only path, [the adapter](../../src/ergora/agent_backends.py) adds `--safe-mode` at line 269 and still sends `--effort ultracode` at line 275. The fetched [official CLI reference](https://code.claude.com/docs/en/cli-reference) says safe mode disables workflows. The fetched [official model configuration](https://code.claude.com/docs/en/model-config) says ultracode is unavailable when workflows are off; in that case the flag starts with ultracode off and an allowed effort level up to `xhigh`.

Consequently, model/account eligibility and caps are not the only current restrictions: this existing Ergora mode itself disables the special workflow behavior. The current table describes the flag as requesting `xhigh` plus ultracode behavior and lists generic eligibility/precedence caveats, but never connects the native limitation to its actual text-only consumer. A later per-mode selector or acceptance plan based on this research could treat schema/CLI acceptance as support for ultracode workflows in text-only mode and miss the documented change in behavior. This is a source-and-documentation conclusion, not a measured model-call result.

Exact saved evidence: `.ergora/checks/backend-runtime-options/sources/claude-cli-reference.html` (A1), the `--safe-mode` row, lists workflows among the customizations that do not load. `.ergora/checks/backend-runtime-options/sources/claude-model-config.html` (A2), immediately after the ultracode flag/version explanation, says “Ultracode is unavailable when: Workflows are turned off” and describes the flag starting with ultracode off, at the highest model/cap-permitted level up to `xhigh`. The corresponding `.txt` captures preserve the same clauses.

Minimal correction: add `--safe-mode` to both adapter descriptions and explicitly state in both ultracode rows that the current text-only path disables workflows, so the documented native outcome has ultracode off with effort up to `xhigh` subject to native precedence/caps. Keep requested, sent, and native-observed/unknown separate; do not change product code or infer task-MCP behavior without its own evidence. Verify the corrected bilingual rows against the same A1/A2/E1 sources and recheck only the affected documentation.

Suggested English addition: “Text-only also adds `--safe-mode`, which disables workflows. In that current mode, the documented `--effort ultracode` behavior has ultracode off and effort up to `xhigh`, subject to native precedence and caps; actual application was not tested.” Suggested Chinese addition: “text-only 另加 `--safe-mode`，关闭 workflows。因此在该现有模式下，文档规定 `--effort ultracode` 的 ultracode 行为关闭，effort 至多为 `xhigh`，仍受原生优先级及 cap 约束；未验证真实应用值。” These can be split between lines 50 and 56.

## Checks and limits

- Read root instructions, the current checkpoint, active requirements/delivery, component change protocol, the independent-review brief and repository-quality guidance. Inspected the complete two-file research candidate and relevant current consumers in `agent_backends`, `agents`, `agent_runs`, component metadata and the DeepSeek/mini/Forge drivers and kernel owner.
- Confirmed all eight cited Ergora source files exist at the product pin and their current contents have no diff against that baseline. Checked the relevant official/pinned source sections for Codex filtering and controls, Claude precedence/caps/ultracode/limits, DeepSeek initialization versus registry metadata, mini query limits and dropped parameters, and Forge campaign/config identity.
- Independently verified the research/patch hashes and all 31 source-capture file hashes/sizes in the source manifest. Every native/upstream citation maps to a successful source receipt; failed fetch records were not used as evidence. The five recorded local version/help commands all exited zero. Their observed versions are Codex `0.167.1` and Claude Code `2.1.312`.
- Both files decode as strict UTF-8, contain 139 lines, 28 source definitions and 112 citation uses, and have no undefined source references or broken relative links. Citation order, inline control names/values, table shapes and heading counts match across languages. Scoped no-index whitespace checks produced no diagnostics; their exit status 1 denotes the new-file differences.
- Applied OpenAI Docs guidance to the fetched C1–C3 official pages. The exposed web-search connector returned “not available to the model” when invoked; the preserved official-page receipts were inspected directly. No new network fetch was needed.

No model, authentication, environment/config snapshot, installation, service, billing/performance test, product test or remote write was performed. Source documentation cannot certify actual provider/account availability, applied effort, native caps, fallback, compaction, cancellation or recovery. Those remain later candidate-specific acceptance work. Only this review report was written.

Initial disposition: F1 open pending bilingual correction and scoped re-review. A6b–d and product runtime acceptance remain separate.

## Same-slice F1 re-review — closed

2026-11-16. The original reviewer rechecked the minimal bilingual correction. The current candidate is:

|File|Accepted SHA256|
|---|---|
|[English research](../research/2026-11-16-backend-runtime-options.md)|`619e06132008f6a0695128a3bebb57c101d6225554397587ce0cc6d0cd524be2`|
|[Chinese research](../research/2026-11-16-backend-runtime-options.zh-CN.md)|`9ae13021b9dfb5b69755d480f8acb004b611ea48248bd5ff6bdd8bdc6d43a951`|

The correction receipt is `.ergora/checks/backend-runtime-options/f1-correction-r1/changes.json`. Independently reconstructed the initial files from the original complete patch and confirmed their original hashes. Compared those contents to the corrected files: exactly lines 50 and 56 changed in each language, with both files remaining 139 lines. Verified the corrected hashes against the receipt. The branch moved during review; the hash-capture command observed HEAD `6cec589f404b17f4828a70807d5e33d89fad3fa0`. That HEAD is contextual only; the two research hashes above identify the accepted candidate.

Both adapter descriptions now state that text-only adds `--safe-mode` and disables workflows, citing A1/E1. Both ultracode rows connect that current mode to the documented ultracode-off behavior and effort up to `xhigh`, retain native precedence/caps and requested/resolved/native-observed separation, and explicitly say actual application was not tested. The English and Chinese corrections have equivalent meaning. Rechecked the unchanged saved A1/A2 HTML/TXT capture hashes and unchanged adapter against the product baseline. The correction resolves F1 without extending a product capability or claiming a runtime observation.

|Axis|Final verdict|Open findings|
|---|---|---|
|Requirement compliance|**Approve within A6a research scope**|0 — F1 closed|
|Maintainability|**Approve within A6a research scope**|0|

No new finding arose from the correction. No unchanged static suite, product tests, model calls, installations, source changes or remote operations were run for this re-review. A6a semantic review is complete for these exact hashes. Configuration/freeze design, fixed/preset/planner/automatic implementation and native runtime acceptance remain A6b–d work.
