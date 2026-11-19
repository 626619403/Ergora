# Start a training optimization trial

English · [Documentation](../README.md)

Training templates freeze the workload, experiment inputs, correctness requirements, baseline and candidate evidence. The selected tools and project environment perform actual training, kernel generation and device access. Ergora project memory, Skill candidates and source observations can be used independently first; they do not mean model training or performance has improved.

Follow the [three-template walkthrough](../development/templates.md) for installing expert compositions, preparing read-only leaves, selecting backends and handing off development work. Real experiments use a [trusted runner](prepare-experiments.md#preview-and-register-a-trusted-runner) and [exact evidence approval](evidence-and-approval.md#exact-owner-approval-and-delivery-recovery).

Training compositions still provide read-only proposal leaves; the operator supplies workload and predecessor materials. Development tasks' `work-units-v2` does not automatically schedule training experiments or approve candidates. All ancestor Skills/context must still be delivered in full. Real device execution and result adoption continue through this guide's runner/gate.

|Current goal|Entry point|
|---|---|
|Understand algorithms, execution dependencies and state residency first|[Source-anchored flow maps](proposals.md#source-anchored-flow-maps)|
|Combine mapping, analysis, kernel assessment and measurement review|[Organize a complete proposal around the bottleneck](proposals.md#organize-complete-proposals-around-bottlenecks), with explicit handoffs between leaves under the common root|
|Analyze existing code, traces or memory reports first|[General performance diagnosis](specialists.md#general-performance-diagnosis) or [specialized direction templates](specialists.md#independent-optimization-direction-subtemplates)|
|Turn expert proposals into executable experiments|[Map proposals to the original experiment contract](proposals.md#map-expert-proposals-into-the-original-experiment-contract), then preview/confirm the baseline, runner and experiment|
|Check measurement contracts and the original gates on CPU first|[Offline paired-measurement demo](#offline-paired-measurement-demo), requiring no model, key or training service|
|Retain each round's original results, failures and unknowns for offline review|[Multi-round evidence index](evidence-and-approval.md#multi-round-evidence-index), explicitly selecting original experiments and appending in a new directory|
|Start and stop the original control workflow|[Submission and reconciliation by original ID](execution.md#submit-prepared-experiments-and-reconcile-by-original-id), [cancellation and stop facts](execution.md#cancel-original-runs-and-observe-stop-facts-separately)|
|Execute a submitted experiment within its original budget and confirm its subtree stopped|[Explicit managed execution and offline stop observation](execution.md#explicit-managed-execution-and-offline-stop-observation)|
|Screen bounded candidates before deciding on separate full verification|[Choose full or lightweight screen](prepare-experiments.md#choose-full-or-lightweight-screen)|
|Continue handling old runs after registration or configuration changes|[Original-registration recovery](execution.md#recover-in-the-original-registration-context), explicitly selecting and confirming the original published record|
|Review actual results and authorize subsequent integration|[Archived evidence](evidence-and-approval.md#read-archived-evidence-and-original-integration-tickets), [exact owner approval](evidence-and-approval.md#exact-owner-approval-and-delivery-recovery)|
|Apply experience to the next task|[Complete improvement journey](../improvement/workflow.md), adopting candidates separately before explicitly freezing them|

For actual computation, explicitly select `training execute` under the same budget through [explicit managed execution](execution.md#explicit-managed-execution-and-offline-stop-observation); ordinary full runs can also use trusted `run-local` after per-experiment manifest confirmation. Finite V2/V3 controllers execute frozen candidates through [explicit authorization and submission](controllers.md#start-a-local-training-budget-and-recover-original-authorization). Successful control operations, CPU lifecycle acceptance and real GPU correctness/quality/performance gains each require their own evidence.

Native Windows supports training-template design, ordinary proposal-role calls and memory / Skill management. Composition leaves with complete Skill attachments use Linux task-MCP and must run under WSL2/Linux. ForgeKernel, the mini driver and full reference experiment execution also use WSL2/Linux; the trusted reference executor additionally requires a Linux container. Native installation does not configure CUDA, GPUs or these reference services; see the [Windows guide](../install/windows.md).

## Preparation

```bash
ergora templates copy training-optimization ./training-task
ergora project add my-project --repo "$HOME/projects/my-project"
```

Alternatively, select “训练优化实验” under “工作流设计” in the console to preview and download files. The template includes `workload-contract.md`, `baseline.json`, `experiment.json`, runner examples, hypothesis, result, evidence, attestation and negative-result records. Replace placeholders with real configuration before approving the contract and exact experiment.

Freeze the model / code version, data identity, random seeds, numerical precision, parallel layout, devices, timing intervals, repetitions and correctness thresholds. The project supplies the training environment and data; installing the console does not install CUDA or PyTorch or request GPUs. Comparing performance candidates is meaningful only after they satisfy both project correctness and quality constraints.

## Offline paired-measurement demo

After installing Ergora on Linux/WSL2, run the bundled original CPU contract demo in a persistent directory that does not yet exist. These Bash commands operate only on the demo directory, without connecting to real projects, services or devices:

```bash
ERGORA_MEASUREMENT_TOOLS="$(python -c 'from ergora.native.resources import ROOT; print(ROOT / "platform/upstream")')"
python -B "$ERGORA_MEASUREMENT_TOOLS/demo.py" \
  --out "$HOME/ergora-examples/paired-measurement"
```

It generates synthetic baseline/experiment inputs, eight AB/BA run pairs, example files in the independent-check format, comparison inputs/outputs and the original content-addressed archive. Every elapsed value and check PASS is constructed to demonstrate formats and binding; no actual training or quality evaluation occurs. It stops if the new directory already exists, preserving originals. Choose another new directory to repeat the demo, without overwriting records.

Recompute the original comparison and pass the original gate again:

```bash
python -B "$ERGORA_MEASUREMENT_TOOLS/compare_runs.py" \
  "$HOME/ergora-examples/paired-measurement/bundle/comparison-input.json" \
  --output "$HOME/ergora-examples/paired-measurement/recomputed-comparison.json"
cmp "$HOME/ergora-examples/paired-measurement/recomputed-comparison.json" \
  "$HOME/ergora-examples/paired-measurement/bundle/comparison-report.json"
python -B "$ERGORA_MEASUREMENT_TOOLS/perfctl.py" \
  --root "$HOME/ergora-examples/paired-measurement/state" gate synthetic-demo \
  --bundle "$HOME/ergora-examples/paired-measurement/bundle/evidence.json"
```

Comparator `PASS` only means paired performance screening passed for the fixed samples; `quality_assessment` remains `NOT_EVALUATED`, `p99_assessment.certified` is false and `promotion_approved` is false. The gate returns at most `ELIGIBLE_FOR_HUMAN_REVIEW`. File digests, distinct reviewer strings and self-reported sampling windows check internal consistency only; they cannot authenticate executor identity, independence, real inputs/hardware, completion boundaries or training quality. Do not transplant the demo's `contract_approved: true` into real projects.

Real projects still freeze semantics, allowed changes, quality and statistical thresholds using the [original contract field table](proposals.md#map-expert-proposals-into-the-original-experiment-contract). Each pair must consist of comparable complete runs restarted independently; the trusted runner must substantiate deduplicated global work across ranks, completion windows and the configuration/initial state actually used. Collect profiles separately from steady-state timing; multiple windows cannot count as multiple independent pairs. Retain `INCONCLUSIVE` when samples or order swaps are insufficient, or confidence intervals cannot distinguish the preset threshold. Under the preset all/any rule, record `FAIL` only when even the interval upper bound cannot strictly exceed the threshold. A point estimate below the threshold alone does not establish failure; neither result passes the original performance gate. Never silently replace the original reference. The relation between the initial multi-round anchor and current reference belongs to the subsequent cycle contract.

## Reference experiment execution

The complete reference distribution provides `agentflow training`, a trusted runner and perfctl gates. Use the parameters in the [complete training optimization reference guide (Chinese source)](../../src/ergora/data/reference/platform/docs/TRAINING.md):

```text
init / runner-add → prepare → worker-start → start
→ explicitly select execute within the same budget, or the old per-experiment run-local
→ trusted evidence and statistical revalidation → human approval of evidence SHA
→ integration / revalidation task for that project
```

`run-local` explicitly executes one experiment at a time; there is no resident training-queue consumer. Approval, results, cancellation and recovery retain the original experiment identity. Unknown results require reconciliation, rather than rerunning with a new ID. Candidate-model or Agent reports cannot replace trusted-runner validation; retain experiment failures and negative results too.

Continue: [Prepare an exact training experiment](prepare-experiments.md) · [Select an optimization specialist](specialists.md).
