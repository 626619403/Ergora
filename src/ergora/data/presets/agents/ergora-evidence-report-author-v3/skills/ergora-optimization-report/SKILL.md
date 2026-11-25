---
name: ergora-optimization-report
description: Write the selected concise optimization log from supplied evidence, with retained measured improvements, screened trials, deferred work and source-linked metrics in six sections.
---

# Concise optimization reports

Use this layout when the user selects the concise optimization-report mode. The existing detailed optimization and generic evidence-report presets keep their layouts. Apply the complete companion `ergora-evidence-report` Skill for evidence boundaries, safe static HTML and the original response convention. This specialization changes presentation, not collection, experiment, quality, adoption or release authority. Use the requested language. The [template](assets/optimization-report-template.md) is also full context in frozen leaf inputs; its placeholders carry no results.

## Establish the evidence and comparison

Read the original objective and acceptance conditions, current supplied report, complete retained trial records, configurations, measurements and analysis. Inventory the source IDs, original outputs/task locations, supplied or verified identities and actual read coverage. Preserve raw records and other contributors' entries. A summary or an external reference is context with provenance, not fresh proof of an experiment.

Keep the single original baseline and its measured metrics only in **初始状态**. Give it a stable reference for later rows without copying it into result tables. State the original code/configuration identity, model/algorithm structure and size, precision, phase, hardware/ranks, input/useful work, effective batch/update semantics, and the objective's units and thresholds. Link supplied flow maps or detailed analysis here when relevant; the compact report need not repeat them as narrative chapters.

Define comparison groups before interpreting changes. Different batch/input/effective work, model, precision, phase or hardware is a separate workload/scope. A capacity result under a changed workload may meet its declared target, but is not a same-workload code speedup. Preserve each actual paired control identity; the report's one original baseline does not turn every later control into that baseline.

## Classify every trial once

Use these six sections, translating their titles only for the requested language: **初始状态、实验总表、已筛除、暂缓、待迁机Kernel、填写规则**. Keep empty sections brief and state when no corresponding records were supplied.

| Section | Entry condition and retained evidence |
|---|---|
| 实验总表 | Retained, actually measured positive results for the declared performance objective, or an actually measured capacity target achieved under its identified workload and applicable constraints. Keep absolute values, paired reference, uncertainty, complete configuration, memory, quality/checks, decision and original output. |
| 已筛除 | Known no-benefit/regression, observed failed trials, or explicitly rejected candidates. Preserve positive-but-rejected measurements and their actual trade-off/decision; arithmetic positivity alone does not restore a rejected candidate to the main table. |
| 暂缓 | Untested, inconclusive or dependency-blocked candidates, including claimed performance gains without a comparable reference. Keep partial metrics, the precise evidence/dependency gap, actual tool availability where relevant, and the condition to resume. Unknown benefit is not no benefit; a separately scoped measured capacity success remains eligible for the main table. |
| 待迁机Kernel | Kernel tasks specifically awaiting a required machine/capability. Keep the task/configuration identity, supplied artifacts, requested versus available tools, capture/readback status, missing capability and next bounded check. These are deferred tasks, not measured successes. |

A promising performance-screened result can enter the main table with its actual validation scope, even when convergence or final acceptance is pending. Keep the original quality tier/checks and decision verbatim in meaning: measured improvement does not itself confer `verified_gain`, correctness, convergence, adoption or approval. A supplied failed quality/acceptance decision belongs in 已筛除; missing checks remain visible as pending evidence. An observed collection/tool failure establishes that operation's failure, not an unmeasured candidate regression.

For performance rows, show the actual improvement under a named comparable measurement and preserve supplied uncertainty/acceptance rules. If uncertainty is absent, mark that gap and keep a retained positive screen at its actual scope; do not invent a confidence threshold or new gate. A result whose direction or comparison is unresolved remains in 暂缓. For capacity rows, state the capacity target and actual achieved work/memory alongside throughput/latency and any regression; a slower result may still meet an explicitly capacity-focused objective and any supplied performance floor. A larger batch alone is not a measured gain.

Give each trial one canonical row. When supplied, carry the stable hypothesis ID alongside its experiment ID. Use existing evidence and decision cells for the evidence that changed the decision, its scope and the next action or stop condition. Mark missing evidence or identity in the row. A kernel task awaiting migration belongs in the kernel section; a cross-reference in 暂缓 may point there without duplicating metrics or explanation. When evidence or decisions change, move the row to its appropriate section, preserving the experiment identity and decision history in original artifacts. Renumber displayed rows and inherited-setting references together, including references across sections.

## Keep the report compact and reproducible

Use tables for trial records. In each relevant table, put the intervention's configuration and **one or two sentences** explaining what changed, how it may help and a material trade-off only in **本次改动**. Refer back to that cell for reused mechanisms; keep result, rejection and deferral cells about observations and decisions. Avoid additional mechanism, capacity-exploration or external-reference narrative chapters.

Each row carries its own configuration keys and verified inherited-setting references plus the exact complete configuration source. For a combined trial, list simultaneous changes in that cell and attach the result to the complete combination; repeated metrics from one run are not isolated contributions. Use descriptive numbered names, with internal run codes in source/reproduction metadata. Follow the requested order, or a named measured progression within each comparable group; repair row references after sorting or moving.

Keep available throughput/latency, memory and loss/correctness/quality metrics even for screened or deferred rows. Define units, useful-work denominators, per-device/global scope and memory type/rank aggregation; retain host memory if relevant. MFU is optional and needs its supplied FLOPs/precision/hardware-peak/timing accounting. Shared warmup, scoring/consumed windows, synchronization, repetitions and uncertainty may appear once per group in 填写规则 or directly above the table. Keep instrumented diagnosis and uninstrumented speed windows distinct.

Put actual experiment outputs or platform task locations and paired source IDs beside each row. Code/patch, complete configuration, environment, command, raw samples, figures and oracle coverage must be recoverable from the supplied originals; name missing evidence precisely. Preserve supplied versus independently verified provenance. Place any relevant authorized original figure in its row with searchable values and source/window; absent image bytes remain absent. Apply the companion Skill's static HTML rules. Source flow or a profile does not by itself establish speedup, safe removal or quality.

Use the final section for the report's applicable measurement conventions, concise source inventory/read coverage and unresolved limits. Use original timestamps to report latency from proposal to first usable decision. Use original occupancy receipts to report occupied eight-GPU group time per distinct usable decision. Include supported rejections and name missing coverage for each measure. It is part of the report, not a copy of this entire Skill. Keep profile findings with their candidate row and kernel-tool gaps with their task; detailed source artifacts remain linked rather than repeated. Both Markdown and HTML keep the same six sections, substantive claims, values, status and limitations.

Before returning, reconcile every supplied trial with its canonical row or an explicit source gap; check main-table eligibility, the unique baseline location, preserved screened/deferred metrics and decisions, and all row/source references. Return the companion Skill's unchanged `markdown`, `html`, `sources`, `limitations` JSON payload in the existing response string.
