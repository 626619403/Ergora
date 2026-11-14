# Conditional kernel design proposal exercise

This authored example checks the kernel-design route and complete handoffs. It supplies a **stipulated diagnostic hypothesis**, not an observed GPU trace, training run or measured benefit. Use readonly proposal calls; fixed inherited-resource list/read is allowed, but execute no supplied code, allocate no device, or fetch external code or models. This whole task and the exact source below are selected material; no real project/commit, compiler version, device report, baseline timings, dataset, checkpoint or quality results are supplied.

Complete selected `affine.py`:

```python
import torch


def affine(x, scale, bias):
    product = torch.mul(x, scale)
    return torch.add(product, bias)
```

Design contract for a possible candidate: `x` is a contiguous CUDA float32 vector of 4096 finite values; `scale` and `bias` are finite, zero-dimensional CUDA float32 tensors on the same device. The reference is the two operations above, producing a new output without modifying inputs. Preserve float32 multiply rounding before add; disable contraction if needed and state the exact compiler option or primitive required. Bounds, alignment, alias/lifetime and nonfinite/overflow behavior require explicit independent checks. This example does not authorize changing precision, math, tolerance, input distribution or training quality requirements. Unknown valid cases remain unsupported or require a separate contract; do not silently constrain a real project's configuration to this fixture.

For this **routing exercise only**, assume investigation has identified these two operations and their intermediate storage on the exposed critical path. Treat that assumption as unverified outside this example. A bounded fusion candidate is a hypothesis worth designing; generated source or a design must still be independently compiled, checked and measured. Report what would falsify the hypothesis, including wrapper cost, loss of overlap or an unchanged end-to-end bottleneck. Do not invent elapsed values, an actual speedup, hardware support, a trace or successful tests.

Produce algorithm/execution maps and state lifetimes; then design/profile proposals that retain the diagnostic assumption's status. The kernel expert must assess the boundary and can give a conditional candidate plus its independent wrapper/numerical/gradient/lifetime evaluation plan. If a prerequisite is missing, retain it as a blocking gap instead of reporting verified output. The measurement reviewer must retain the absence of real independent correctness, quality and paired system timing; model approval of proposal completeness is not gate eligibility or adoption. Supply the original task/source and complete predecessor result envelopes to every later leaf.
