# CPU preparation proposal exercise

This authored example checks proposal routing and complete handoffs. It is not a real training workload, measured bottleneck or speedup benchmark. Use readonly proposal calls; fixed inherited-resource list/read is allowed, but execute no supplied code. The exact source below and this whole task are the selected material. No separate repository/commit, runtime trace, dataset, checkpoint, trainer, model or quality result is supplied.

The fixed objective is the list of weighted sums, in input batch order. The layout JSON string is immutable during one call. Every batch and every value must still contribute; sample reuse, changed weights and skipped batches are disallowed. Prefer investigating repeated preparation and its lifetime before introducing implementation-specific acceleration. No GPU or CUDA operation is present. Preserve the original source as the reference; propose the smallest change and independent checks, without making an actual gain or adoption claim.

Complete selected `schedule.py`:

```python
import json


def prepare_layout(layout_json):
    return tuple(json.loads(layout_json)["weights"])


def evaluate_batches(batches, layout_json):
    result = []
    for batch in batches:
        weights = prepare_layout(layout_json)
        result.append(sum(value * weight for value, weight in zip(batch, weights)))
    return result
```

One valid configuration is `batches=[[1, 2], [3, 4]]`, `layout_json='{"weights": [2, 3]}'`; the hand-derived outputs are `[8, 18]`. Valid cases may use other finite numeric weights, batch values and counts. Preserve Python `zip`'s current behavior on unequal lengths unless a separately approved semantic change is requested. The immutable layout may be reusable; the actual batch contents are fresh inputs. Parsing failures, iterator consumption and exception timing are observable behavior to examine before hoisting work. No measured cost or caching benefit is given.

Produce algorithm/execution maps and lifetimes, then bounded design/profile hypotheses. The kernel expert must be called and may conclude that no kernel modification is appropriate. Report the scope and evidence for that conclusion. The measurement reviewer must distinguish a coherent proposal from missing actual timing, correctness execution, restoration and task-quality evidence. Supply complete predecessor result envelopes on each later call; do not replace this source or task with a model summary.
