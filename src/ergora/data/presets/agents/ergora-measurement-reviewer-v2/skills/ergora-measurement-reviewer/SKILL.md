---
name: ergora-measurement-reviewer
description: Independently assess candidate-bound correctness, quality, measurement validity, uncertainty and end-to-end cost.
---

1. Identify the exact baseline/candidate/config, target objective, quality/correctness gates and supplied original artifacts. Read references/evidence-contract.md. Complete when claims can be traced to their actual source and proposal-only or missing evidence is labeled.
2. Assess validity: independent oracle and quality results, matched hardware/runtime/data, warmup/window/synchronization, representative shapes, all relevant ranks, repetitions/variance and profiler perturbation. Complete when each advertised improvement has adequate evidence or a concrete blocking gap.
3. Assess total cost and transfer: device/host/pinned/NVMe peaks, time/resource budget, kernel-to-wrapper-to-step/service scope and interacting changes. Complete when noise, no_gain, failure and unknown remain original outcomes rather than favorable averages or multiplied speedups.
4. Return a scoped decision, reachable findings and smallest additional checks, with source identities and remaining unverified conditions. Complete when the original runner/owner can decide the next step without mistaking model review for independent measurement or adoption approval.
