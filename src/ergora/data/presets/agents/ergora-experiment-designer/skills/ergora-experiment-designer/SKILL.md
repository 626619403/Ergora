---
name: ergora-experiment-designer
description: Design bounded cross-domain optimization experiments from a fixed workload, baseline and quality contract.
---

1. Establish the measurement contract: workload/config/code identity, objective and units, quality/correctness gates, hardware and matched dependency versions, baseline evidence and permitted changes. Read references/evidence-contract.md. Complete when every asserted fact has a supplied source and every missing prerequisite is explicit.
2. Choose the smallest bounded action set that can distinguish the current hypotheses. Consider parallelism, memory/recompute/offload, overlap, graph/data scheduling, precision, kernel and model/runtime architecture together. Do not infer a bottleneck from a category name. Complete when each candidate has a mechanism, changed variables, comparison, resource/time budget and stop condition.
3. Plan interactions and attribution: use baseline/A/B/A+B when interaction matters, keep paired comparison conditions, and identify invalidated captures, checkpoints or numerical gates. Complete when local speedups are not multiplied or treated as measured end-to-end gains.
4. Return a reproducible proposal and explicit handoff to the original runner: exact inputs/candidates, commands to be supplied or verified, oracle/gates, repetitions, evidence locations and rollback. Complete when the owner can freeze a real experiment without accepting invented values or granting this leaf execution authority.
