---
name: ergora-performance-analyst
description: Diagnose a supplied critical path across traces, memory, ranks, communication and data flow without inventing a profile.
---

1. Inventory supplied traces, tables, memory snapshots and commands with their actual identities, profiler/version, window, rank coverage and collection conditions. Read references/evidence-contract.md. Complete when unavailable or synthetic evidence is clearly separated from original measurements.
2. Trace the slowest relevant dependency path across CPU launch, kernels, collectives, synchronization, memory and data preparation. Treat concurrency and hidden overlap explicitly; do not add overlapping durations. Complete when each bottleneck hypothesis names supporting intervals, competing explanations and the target objective it could affect.
3. Analyze capacity and contention using the right units and definitions: allocated/reserved/peak memory, activation/optimizer/parameter state, host/pinned/NVMe budget, bandwidth and SM use. Complete when rank/window gaps, profiler perturbation, sampling and uncertainty remain visible.
4. Return falsifiable ranked hypotheses and bounded follow-up measurements for the actual runner. Complete when each request says what would support/refute it, how quality and versions remain fixed, and which conclusions are still unknown. Do not present an upper bound as a measured gain.
