# Optimization report layout — placeholders only

This is an Ergora-authored structural example, not an experiment or measured result. Replace brackets with supplied evidence in the requested language; remove inapplicable columns/sections with a brief reason. Keep missing required evidence visible. The runtime supplies this entire file as context alongside both report Skills.

## 1. Scope, current state and objective

- Purpose and system: [what it computes and why].
- Objective and acceptance: [metric, unit, threshold; numerical/update/quality obligations].
- Fixed comparison: [algorithm/model structure and size, precision, phase, input/work units, effective batch/update behavior, hardware/ranks].
- Exact baseline and selected/recommended candidate: [source IDs and version/config identities].
- Supported conclusion: [actual result or precise missing result]; decision: [supplied owner/status, or pending].

## 2. Algorithm, dependencies and data flow

[Explain the supplied algorithm and major components, including forward, backward and update dependencies when relevant. Cite the source map and coverage.]

```text
SCHEMATIC PLACEHOLDER — replace with source-backed nodes and edges
[input producer] → [component and tensors] → [consumer/output]
                         ↓
                  [state/update obligation]
```

| Component / tensor | Computation and dependency | Shape / dtype / layout; lifetime and reuse | Source and coverage |
|---|---|---|---|
| [descriptive name] | [producer → consumer; synchronization/communication] | [supplied contract or missing] | [source ID and location] |

| Redundancy candidate | Existing use and suspected repetition | Evidence state and source | Obligations / counterevidence | Next bounded falsification check |
|---|---|---|---|---|
| [computation, component or tensor] | [what may be repeated/unused and why] | [source fact / measured / hypothesis / unverified] | [gradient, state, mask, RNG or other supplied constraint] | [owner and required evidence] |

Static structure does not establish runtime cost, overlap, safe removal or speedup.

## 3. Baseline and measured progression — [one comparable scope]

Measurement contract: [phase, hardware/ranks, precision, useful work, effective batch/update semantics, units and aggregation]. Window: [warmup/exclusions, timing boundary, synchronization, sample count/repeats, uncertainty]. Display order: [measured MFU after-value, declared objective or chronology]. Speed measurements: [uninstrumented window]; diagnostic captures: [separate windows or missing].

The table below contains placeholders only. Use descriptive names; keep internal run codes in reproduction metadata or actual paths.

| Number / name | This item's config; inherited settings | What changes / how it works / why it may help | Throughput | GPU memory | Loss / correctness / quality | MFU, if applicable | Actual experiment location; paired identities; outcome |
|---|---|---|---|---|---|---|---|
| 1. [baseline name] | [full relevant baseline settings/source] | [baseline behavior] | [value + unit/window, or missing] | [allocated/reserved + unit/rank aggregation] | [oracle and actual coverage] | [value + measured/estimated accounting, or inapplicable] | [actual output/task; source identity; evidence status] |
| 2. [candidate name] | [own keys; inherit report item 1; full frozen config/source] | [mechanism; all simultaneous changes] | [paired control → result, unit and uncertainty, or absolute result] | [actual result and definition] | [actual checks and missing quality scope] | [supplied result and accounting] | [actual output/task; exact control/candidate; retain/reject/pending] |

[If item 2 is a combined trial, keep its gain attached to the complete combination. Any repeated metric from that run is the same measured configuration, not an isolated contribution.]

Selected configuration in this scope: [complete enabled chain, defaults/fixes and exact config source; supplied selection owner/status or recommendation]. Repeat this section for different phases/hardware/work, without deriving cross-scope speedup percentages.

## 4. Diagnosis and figures

| Candidate / phase | Requested → actual tool | Capture / readback and diagnostic window | Finding and evidence | Missing / failed / unsupported |
|---|---|---|---|---|
| [exact identities] | [tool and version or unavailable] | [separate statuses, window and original artifact] | [source-bound observation; interpretation labelled] | [actual limitation and next check] |

[Embed authorized original figure bytes when available. Caption: source ID, candidate/control, units and sample window. Repeat relevant numerical values as searchable text/table. If bytes or values are absent, state that limitation and keep the authorized source reference.]

## 5. Decisions, negative results and next bottlenecks

| Candidate / descriptive trial | Supported result | Decision owner / actual status | Reason and original output |
|---|---|---|---|
| [retained, rejected, failed or unknown trial] | [measured / estimated / hypothesis / not validated] | [supplied receipt or pending recommendation] | [including regression/dissent and real experiment source] |

Remaining bottlenecks: [observation versus hypothesis]. Next bounded checks: [question, owner, required measurement and stopping condition]. Missing quality/performance evidence: [precise scope].

## 6. Evidence and limitations

[Source inventory: stable IDs, authorized original references, exact supplied or verified identities, actual read coverage including excerpts/attachments. Record unresolved conflicts, missing originals and inapplicable sections. Both report views carry the same claims, values and limitations.]
