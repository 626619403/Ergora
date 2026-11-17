# [Optimization log title] — placeholders only

This is an Ergora-authored layout, not an experiment or measured result. Fill it from supplied evidence in the requested language. Keep these six sections; adapt columns to the actual metrics and state when a section has no supplied entries. The runtime supplies this entire template alongside both report Skills.

## 初始状态

[Purpose and supported result boundary; original objective, performance or capacity target and applicable acceptance conditions. Fixed model/algorithm, precision, phase, hardware/ranks, input/useful work and update semantics. Define comparison groups; identify changed workloads separately. Link relevant supplied source-flow analysis without repeating it.]

| Original baseline reference | Exact code / complete configuration | Measured results / units / window | Memory / checks / quality coverage | Original output and provenance |
|---|---|---|---|---|
| [Single original baseline; stable reference used later] | [Source identities; full relevant settings] | [Actual throughput/latency; samples and uncertainty, or precise gap] | [Memory type and rank scope; actual oracle/checks] | [Original experiment/task; source ID; supplied or verified identity/read coverage] |

[External references, if supplied: concise context and original source. They are not measured optimization rows.]

## 实验总表

[Retained measured improvements only. Identify comparison groups and named references. A promising screened result retains its actual quality/validation status; capacity success states its target and changed workload, including slower performance when observed.]

| Number / experiment / owner | Workload / comparable group | 本次改动 | Measured result / named paired reference | Memory | Window / checks / decision | Code / configuration / original experiment |
|---|---|---|---|---|---|---|
| [Descriptive retained trial] | [Exact workload and objective] | [Own keys; inherited-row references; one or two sentences for change/mechanism/trade-off; all simultaneous changes] | [Absolute metric, unit, supported delta and uncertainty; or achieved capacity target plus performance] | [Actual values/type/rank scope] | [Sample window; actual correctness/quality coverage and missing checks; supplied decision/tier] | [Exact candidate/control identities; full configuration and real output/task; source IDs] |

## 已筛除

| Number / trial | Workload / 本次改动 | Actual metrics / observed failure | Rejection reason / actual decision | Original experiment and source |
|---|---|---|---|---|
| [Known no-benefit, failed or rejected trial] | [Group; own configuration/inheritance; one or two sentences for change/mechanism/trade-off] | [Available throughput/latency, memory, quality/window; retain any positive-but-rejected measurement and named reference] | [Observed result and supplied decision, including trade-off] | [Exact identity; real raw output/task and full configuration; source IDs] |

## 暂缓

| Number / candidate | Workload / 本次改动 | Available metrics / evidence gap | Resumption condition / next bounded check | Original record / task |
|---|---|---|---|---|
| [Untested, inconclusive or blocked candidate] | [Group; own configuration/inheritance; one or two sentences for change/mechanism/trade-off] | [Partial actual metrics/checks; unknown benefit remains unknown; concrete missing evidence/dependency or unestablished performance comparison] | [Required evidence/capability and owner when supplied] | [Exact identity; real source/configuration/task; source IDs] |

[Kernel tasks waiting specifically for migration have their canonical row below; use an ID cross-reference here only if useful.]

## 待迁机Kernel

| Number / task | Workload / 本次改动 | Existing evidence / requested and available tools | Required machine/capability / resumption check | Original task package |
|---|---|---|---|---|
| [Supplied task awaiting migration] | [Exact scope/configuration; one or two sentences for change/mechanism/trade-off, or no intervention specified] | [Actual metrics if supplied; tool version/availability, capture/readback and unsupported scope] | [Concrete missing capability; next bounded check and owner if supplied] | [Source/task IDs; original artifacts and full configuration] |

## 填写规则

[Report-specific conventions: units/useful work; comparison-group definitions; warmup/scored/consumed windows, synchronization, repetitions and uncertainty; memory definitions; optional MFU accounting. Keep diagnosis windows distinct.]

[Compact source inventory: stable IDs, original references, exact supplied/verified identities, actual read coverage and missing originals/figures/checks. State unresolved limits and actual decision scope once.]

[Appending rule for this log: retained measured improvements in the main table; known failures/no benefit/rejections in screened; unknown/dependency gaps in deferred; machine-dependent kernel tasks in their section. Keep the single baseline above, mechanism in change cells, full configurations and original metrics/decisions traceable; move/renumber rows and inherited references together.]
