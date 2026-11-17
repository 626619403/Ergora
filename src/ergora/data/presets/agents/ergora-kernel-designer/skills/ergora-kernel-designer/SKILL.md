---
name: ergora-kernel-designer
description: Design a kernel candidate together with its numerical, layout, wrapper and end-to-end integration contract.
---

1. Freeze the real operation and wrapper contract, exact baseline/candidate identity and supported input set. Read references/evidence-contract.md. Complete when shape/stride/layout, dtype/accumulation, alias/lifetime, RNG and derivative/distributed requirements are explicit or identified as missing.
2. Connect the proposed change to actual hardware and critical-path evidence. Consider precision, vectorization/layout, tiling, fusion, graph capture, memory traffic and communication together. Complete when prerequisites, unsupported cases and the expected mechanism are stated without invented measured speedups.
3. Design the candidate and an independent correctness oracle over representative and adversarial valid cases. Preserve failure behavior and quality gates; separate kernel, wrapper and full-step/service tests. Complete when candidate text is not represented as compiled or validated code.
4. Return a reproducible evaluation/integration plan with exact compiler/runtime versions, warmup, synchronization, repetitions, isolation, candidate bytes and rollback. Complete when original runner and independent reviewers can evaluate it without using this agent's self-report as adoption approval.
