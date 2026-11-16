# Complete bilingual USAGE guide: independent review

2026-11-16. Reviewer: `bilingual_usage_review`, a new independent agent with fresh context. Final requirement-compliance verdict: **approve**. Final maintainability verdict: **approve**. One initial P3 finding was corrected and independently rechecked within this slice; no open findings remain in the inspected scope.

## Requirements and inspected identity

The raw requirement is a complete English-default guide at its existing path and a complete Chinese counterpart, with reciprocal navigation, every original heading target, executable example, recovery/approval/platform restriction and historical evidence preserved. An index or summary is insufficient. The six-stage candidate-bound contract and visible unsupported/unavailable capabilities must remain. Documentation checks do not establish runtime, model, CI or quality acceptance.

Documentation baseline and observed HEAD: `e5a35558f29f11eed62c6dd28450da6d39f232df`, branch `refactor/architecture-foundations`. Product/source identity: `6cec589f404b17f4828a70807d5e33d89fad3fa0`; an independent `git diff` confirmed no `src` changes against that product. The separately reviewed test-only merge `99c85030e35834a751ea6069e2310506a73ccf43` is outside this documentation slice.

The original guide is 1,272 lines / 169,871 bytes, SHA256 `298105ebfba66d25ca67e3aa1cd14dfbd0c8bc219da85564add805e0385093f9`, and independently matches baseline Git bytes. I read and compared the complete original/English chunks covering lines 1–419, 420–854 and 855–1272 in bounded sections, including examples and dense recovery, external-write, UI, lease and retrospective guidance. The original chunks concatenate exactly to the original. Raw requirements, original content and actual changes were inspected before the author's USAGE delivery narrative.

The complete six-file author scope is:

- `docs/USAGE.md`
- `docs/zh-CN/USAGE.md`
- `docs/README.md`
- `docs/README.zh-CN.md`
- `docs/plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md`
- `docs/delivery/2026-11-16-bilingual-usage-guide.md`

Initial tracked/untracked patch SHA256: `8ac6642e16abe80eebe142e9303af95bc4887b2371314603d72a5a599182c1e9`. Corrected complete patch SHA256: `d9d15cf918487c7588e0ee3d89bdd3e0cb6b731c7f0809dea6b82bd8c35fe579`. Their manifests and complete patches remain under `.ergora/checks/bilingual-usage-guide/r1/` and `.ergora/checks/bilingual-usage-guide/comment-fix-r2/`. I independently applied both patches **in memory** to baseline/new-file bytes, verified every manifest hash and confirmed all six corrected outputs equal the inspected files. Final English SHA256 is `4759309af3dd608af22c6ac463b5171f20f267c2dcfce130abd7d95893af5f23`; Chinese is `e44c80178ef3cb68b9e64729aa7830e3f4bcebef1405c923cb807429eb1e6148`. Other dirty checkpoint, handoff, CI and S2 records are excluded.

## Finding and correction

**F1 — P3, resolved: translate two explanatory recovery comments.** The initial English [reconciliation example](../USAGE.md#显式终态对账与工单租约释放) at `docs/USAGE.md:1101` and [export example](../USAGE.md#导出精确候选与恢复回执) at `docs/USAGE.md:1123` retained Chinese-only comments. An English reader following these examples could not read the local instructions about the original intent digest, rereading export status and current revision. This fell short of the complete-English requirement. The minimal correction was to translate those two standalone comments while preserving commands and Chinese content.

The author made exactly that correction. Independent r1-to-r2 comparison found only those two changed public lines; the other five author files are identical. Both comments now preserve the original recovery meaning in English, and no Chinese standalone shell comment remains. Executable-block bytes/order are unchanged after excluding standalone comments. F1 is closed. No further semantic or maintainability findings were identified during the full-guide review.

## Evidence and assessment

Independent read-only, standard-library checks passed on the corrected six-file scope: strict UTF-8 and complete fences; reciprocal guide links; **311** local links/fragments; all **62** original heading targets; all **64** original executable blocks, in order; **692** original inline-code occurrences as a multiset; no private machine paths; and scoped `git diff --check`. Inline-code values/counts are preserved, while natural English may reorder mentions. Original quoted example payloads remain byte-identical. After undoing link relocation/navigation, the Chinese body matches the complete original apart from exactly three documented current-schema corrections and the explicit availability addition.

Full semantic comparison retained the installation/offline/platform restrictions; immutable source/task/run/candidate identities; current-revision and exact-plan confirmation; unknown-operation recovery without resending; independent required/advisory review distinctions; complete evidence/material capacity failures; normal and cancellation outcomes; external-process confirmation versus file receipts; exact lease release; retrospective proposal/evaluation/adoption separation; memory expiry/deletion limits; and frozen reference/resource/manifests. Stable guide ownership and existing navigation are appropriate; no new runtime abstraction, source owner or dependency was introduced. Remaining documentation batches are still explicitly open.

The three current-schema 5→6 corrections match `state.py`'s six ordered migrations. The historical schema-v4 review-link introduction remains historical. I checked new availability claims against the actual registration schema and `registrations.py`, `task_design.py`, `tasks.py`, `reference_executor.py`, `reference_task_approval.py`, `task_envelopes.py`, `agent_backends.py` and component definitions: first-registration schema2 stores policy/effective requirements and digests; status reports execution unsupported and human assurance unavailable; task birth and managed native execution retain refusal; existing registration migration/replacement/downgrade is blocked. The legacy local Unix actor is not presented as a trusted new owner channel. Source journal/trusted material/gate work and unified fixed/preset/planner/automatic selection are not claimed delivered. Explicit backend reasoning fields request native options without proving actual levels or authorizing hidden fallback/budget expansion. Original evidence-reader and handoff limits were also checked against their source constants.

I inspected the author's parser commands, stdout/stderr, checker and initial unsubstituted-placeholder rejection records. The existing joint installed SDK's recorded `-I -B` `parse_args` check accepts **146** fenced argv examples after nominal integer revision substitution and removal of shell redirections. The separate original `ergora workflow --help` example bypasses the application parser in `cli.main`; that dispatch was checked directly in source. These are declaration checks without handler execution. The r2 change affects only comments, so the original parser receipt remains applicable to the identical argv; no parser rerun is claimed.

## Limits and handoff

This review performed no product tests, installation, model/handler/service/browser execution, shell-example execution, remote URL access, platform/network calls, Git-index operation, commit or push. Source inspection and static documentation checks do not certify Windows/WSL2 execution, external-write compatibility, cross-machine runtime recovery, trusted human authority, training or model/business quality. Neither historical product CI nor this candidate's separately monitored CI substitutes for translation acceptance. The earlier failed run and any later run retain their own identities/results.

The only reviewer write is this report. The coordinator owns plan/delivery status updates and any subsequent publication. The corrected complete USAGE documentation slice has no remaining review blocker; later guide/architecture batches and product acceptance remain separate work.
