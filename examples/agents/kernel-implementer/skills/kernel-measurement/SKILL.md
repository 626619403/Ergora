---
name: kernel-measurement
description: Compare CUDA or Triton kernel candidates against a reference using the project's numerical contract and target hardware.
---

Reproduce the reference result and timing on the target device before changing
the kernel. Reuse the project's harness when it measures the actual workload.

Validate each candidate across the requested input domain, including boundary
shapes, layout and dtype constraints. Synchronize device timing, distinguish
compilation from steady-state latency, and use the same measurement conditions
for candidate and baseline. Report variability alongside the comparison.

Keep a failing candidate's result and diagnosis. Select improvements only from
candidates that meet the project's correctness and measurement criteria.
