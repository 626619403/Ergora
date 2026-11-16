---
name: ergora-optimization-report
description: Organize supplied optimization evidence into a progressive report with source flow, redundancy hypotheses, comparable baseline and candidate tables, measured outcomes and traceable decisions.
---

# Optimization reports

Apply the complete companion `ergora-evidence-report` Skill for evidence boundaries, safe static HTML and the existing response convention. This specialization organizes supplied material; it grants no collection, profiling, experiment or adoption authority. Use the requested language. Its [template](assets/optimization-report-template.md) is also supplied as full context so that frozen leaf inputs contain the layout without network access or later file reads. Adapt its columns and length; placeholders are instructions, never results.

## Establish the comparison

Read the original objective, constraints, complete supplied flow-map/algorithm analysis, baseline, candidate configurations and original results. Inventory what was actually supplied and read, including attachments and predecessor envelopes. Complete the inventory when every requested component and retained trial is either covered by a source or explicitly missing. Preserve the original raw artifacts outside the derived report.

Open with the purpose, current state, target metric and acceptance conditions, the strongest supported result and its limits. Identify fixed algorithm/model structure, size, precision, training phase, hardware/ranks, data/work unit, effective batch/update behavior, baseline and candidate versions. State any changes to these conditions before presenting gains. Split different phases, hardware, precision or effective work into separate comparison scopes; a cross-scope number is descriptive, not a speedup comparison.

## Present the system before the interventions

Use supplied source-anchored analysis to explain the complete relevant algorithm, computation dependencies and data flow before listing optimizations. Cover major components, forward/backward/update dependencies where relevant, tensor shape/dtype/layout, producers/consumers, reuse/lifetime, synchronization/communication and state obligations. Explain unfamiliar terms by role. Include a compact labelled diagram and a text/table equivalent, with source references on nodes or edges. Label schematic or incomplete maps. A source dependency establishes structure; observed timing, overlap and bottlenecks require their own runtime evidence.

Make a redundancy inventory for computation, components and tensors. For each item record the current producer/consumer, suspected repetition or unused value, supplied evidence, and obligations that could make removal unsafe (for example gradients, RNG, masks, normalization, communication or recovery). Use explicit states: source fact, measured observation, hypothesis, or unverified. Describe the bounded check needed to falsify each hypothesis. Keep unsupported items visible; do not turn a plausible removal into a measured gain.

## Make progression comparable and self-contained

State common hardware, workload, units, warmup, timing boundaries, repetitions/sample count, sample window, synchronization, aggregation and uncertainty immediately above each results table. Keep profiler-instrumented diagnosis windows separate from uninstrumented speed measurements. Missing baseline or quality evidence narrows the conclusion; keep that limitation beside the relevant result.

Use descriptive numbered row names. Show the baseline and retained sequence so the reader can reconstruct each complete configuration. Prefer these columns for training reports: **number/name → this item's configuration → what/how/why → throughput → GPU memory → loss/correctness → MFU → actual experiment/task location**. Add paired control/candidate identities and outcome where needed. Omit inapplicable metrics with an explanation instead of forcing empty columns. For other workloads choose the metric matching the objective; MFU is optional, not an acceptance gate.

- Give each row its own configuration keys and the mechanism connecting the change to expected behavior. Identify inherited settings by backward references to numbered rows; retain the complete enabled combination, defaults and fixes in the selected result, plus its exact full-configuration source. Explain shared changes on first use so no external summary is required to understand them.
- A matched single-change trial may show control → result and its measured delta. A combined trial must list the simultaneous changes and attach the gain to the entire combination. Repeated full-configuration values refer to the same run; they are not isolated per-item gains. Unmatched ablations cannot be added to manufacture a total gain.
- Within a comparable scope, show measured progression from lower to higher after-value MFU when that metric is supplied and meaningful. Keep equal values adjacent. Otherwise follow the declared objective or validation chronology and name that order. Retain actual predecessor/control identities when display order differs from execution order. Put correctness repairs or defaults without performance measurements before measured rows.
- State measured, estimated, hypothesis and not validated explicitly. A short finite run, a profile or a speed result establishes only its actual scope; loss, numerical/gradient parity and training quality remain separate evidence. Preserve regressions, failures, unknowns, dissent and unsuccessful trials, with real output locations and rejection reasons.
- Use the actual experiment output directory or platform task URL in each result row. Make code/configuration/environment, command, raw samples, figures and oracle coverage recoverable there. A repository root or another summary is not a substitute. If the original output is absent, name that missing evidence once and cite the narrower supplied record.

Report units and denominators explicitly: per-device versus global throughput, useful work versus padding/repeats, wall time versus kernel time, allocated/reserved memory and rank aggregation. MFU (model FLOPs utilization) needs its supplied useful-FLOPs accounting, precision convention, hardware peak and timing denominator. Preserve estimates and their assumptions as estimates; do not infer MFU from an unrelated utilization percentage. Recounting after a model/input/precision change belongs to that changed scope.

## Show diagnosis, decisions and remaining work

For each supplied profile, identify candidate/phase, requested and actual tool, capture and readback coverage, instrumented window, original artifact and source-bound finding. Distinguish availability, successful capture, successful readback and unsupported operations. Keep tool failures and permissions limits visible. A previous candidate's trace remains evidence for that candidate.

Embed relevant original figures when supplied and authorized, with source ID, scope, units/window and searchable numerical text or an adjacent table. In HTML use safe inline data images under the companion Skill's static-output rules. When image bytes are absent, keep the source reference and say the original was not embedded. Captions and screenshots do not establish unseen values or authenticate provenance. Qualitative maps can be drawn from supplied structure and visibly labelled as such.

End with candidate decisions, their actual decision owner/status and the supported reason, followed by remaining bottlenecks, missing evidence and the next bounded check. A report recommendation is not an adoption receipt. State one reproducible selected result per scope only when selection is supplied; otherwise call it a recommendation or pending decision.

Before returning, apply a one-pass reader check: can a newcomer explain the component flow, each intervention and retained combination, the measured comparison and its limits, the rejected trials, and locate the original experiment? Reconcile row references after sorting, headline/table/figure numbers, sources and limitations across both Markdown and HTML. Return the companion Skill's original `markdown`, `html`, `sources`, `limitations` JSON payload inside the existing response string.
