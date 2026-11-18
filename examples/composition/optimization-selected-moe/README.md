# Selected MoE optimization proposals

This example publishes an exact revision of the shared training proposal with MoE dispatcher and overlap workflows as real descendants. All eleven leaves inherit both shared optimization Skills and the environment-change record. Topic specialists carry their complete topic methods. The single current resource tree remains in `src/ergora/data/presets`; this directory contains a standard revision document, not a duplicate resource bundle.

The inherited [GPU comparison policy](../../../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#gpu-comparisons-and-pool-validation) guides the authorized execution supervisor's small comparisons, candidate batches and target-scale acceptance through available `igs` pool operations. These readonly proposal calls retain their existing permissions.

Install the three dependency closures in your chosen control home, then check and publish the supplied document. These commands pin the shipped references; a conflicting published version is never overwritten.

```bash
ergora composition install-preset training-optimization
ergora composition install-preset optimization-moe-dispatcher
ergora composition install-preset optimization-moe-overlap
ergora composition revise ergora-training-proposal 4.1.3 --base-digest 29f5a66e650678ea34d1445a4138bca8f7aa84d2777d141f6edbb6990f317a8c --document examples/composition/optimization-selected-moe/root.revision.example.json --check
ergora composition revise ergora-training-proposal 4.1.3 --base-digest 29f5a66e650678ea34d1445a4138bca8f7aa84d2777d141f6edbb6990f317a8c --document examples/composition/optimization-selected-moe/root.revision.example.json
ergora composition preview ergora-training-proposal 4.1.4 --grant examples/composition/optimization-selected-moe/grant.json
```

The base digest in these commands is the exact shipped root. The check resolves every reference and validates the whole graph. Use the returned `preview_sha256` in the existing freeze call, then use its returned complete manifest path:

```bash
ergora composition freeze-manifest ergora-training-proposal 4.1.4 --grant examples/composition/optimization-selected-moe/grant.json --preview-sha256 PREVIEW_SHA256
ergora composition show-manifest PREVIEW_SHA256 --material
ergora composition prepare-from-manifest FROZEN_MANIFEST_PATH root/moe-dispatcher/specialist --task analysis-task.txt --directory dispatcher-input --max-prompt-bytes 1000000
ergora composition prepare-from-manifest FROZEN_MANIFEST_PATH root/moe-overlap/specialist --task analysis-task.txt --directory overlap-input --max-prompt-bytes 1000000
ergora composition check-input PROJECT dispatcher-input --mode task-mcp
ergora composition check-input PROJECT overlap-input --mode task-mcp
ergora composition run-input PROJECT dispatcher-input --mode task-mcp --timeout 120
ergora composition run-input PROJECT overlap-input --mode task-mcp --timeout 120
```

Replace PROJECT with an admitted project; check actual backend authentication and task-MCP availability. Unsupported modes fail visibly. The task file includes the original requirements, exact workload/source/baseline/candidate/environment, the same existing profile and the complete flow/common-analysis result envelopes. These leaf calls do not execute predecessors or fill ports. No new profile, training, installation, adoption or GPU permission follows from preparation.

Run every required leaf in the following groups, preparing each input with the original task and complete preceding artifacts. Within a group the operator may run independent calls concurrently. Readonly specialists first receive the same evidence without sibling conclusions; dependent review receives complete original results.

|Group|Exact leaves|Role / definition|
|---|---|---|
|1|`root/flow/map`|performance-analyst / training-flow-analyst@1.0.1, high|
|2|`root/analysis/design`, `root/analysis/profile`|experiment-planner / experiment-designer@2.0.1, max; performance-analyst / performance-analyst@2.1.0, high|
|3|`root/moe-dispatcher/specialist`, `root/moe-overlap/specialist`|performance-analyst / each opt-…-expert@1.0.0, high|
|3|`root/moe-dispatcher/design`, `root/moe-overlap/design`|experiment-planner / experiment-designer@2.0.1, max|
|4|`root/moe-dispatcher/measurement/review`, `root/moe-overlap/measurement/review`|reviewer / measurement-reviewer@2.0.1, high|
|5|`root/kernel/assess`|kernel-tuner / kernel-designer@2.1.0, max|
|6|`root/measurement/review`|reviewer / measurement-reviewer@2.0.1, high|

All Agent IDs above have prefix `ergora-`; all models are `gpt-6.1-sol`. The manifest contains the complete exact references and minimum efforts. The shared designer owns the whole-workload contract; the two local designers check finite topic tests against it. All use the same baseline, trace and oracle, collected once by their original owner.

Each topic measurement requires both of its complete analysis results. Global kernel requires flow, both common analyses and both complete topic results. Final measurement additionally requires global kernel. Preserve every original input/output identity, counter-evidence, failure, no_gain, noise and unknown. A reasoned no-kernel-change assessment completes assessment; a missing assessment does not.

There are eleven calls. Reserve eleven model-call slots, at most four concurrent model processes, an explicit total wall limit and cleanup reserve within the actual authorization. Independent `run-input` enforces its own timeout; it does not enforce the group's total budget, concurrency, recovery or all-join. The operator records launches, actual overlap, full results and terminal process state. Insufficient budget or incomplete required predecessors stops the handoff. The product's automatic stage fanout remains a separate required runtime delivery.

The grant permits workspace/definition reads, no writes, no shell and no network. Its explicit material ceiling is 500000 bytes; every subtree ceiling still applies. A capacity failure requires a smaller reviewed selection or an explicitly revised valid ceiling, never truncated material or automatic permission expansion.

The nineteen standalone optimization presets remain limited topic entries. They do not acquire this root's shared policies through a link or a separate invocation. When selecting low-precision, preserve its own specialist/design → kernel → measurement sequence and pass its complete kernel result; the global assessment cannot replace it.
