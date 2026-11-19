# Select an optimization specialist

English · [Documentation](../README.md)

## General performance diagnosis

Ergora maintains performance-analysis, experiment-design, kernel-design and measurement-review definitions/compositions; see [integration guide](../improvement/workflow.md) and [Agent definitions](../definitions/agents.md#built-in-specialists). The 19 directions divide specialist responsibilities. Profiling and performance-diagnosis reuse `ergora-performance-analyst@2.3.0`; kernel topics reuse kernel-designer; common experiment design and measurement review remain independent. Citing papers/Skills does not import complete native Agent workflows. Tools such as Forge still require separate adaptation/admission.

```bash
ergora composition install-preset optimization-performance-diagnosis
```

Prepare manifests with the complete `root` reference returned by installation. Root is `ergora-opt-performance-diagnosis-proposal@1.2.1`; `root/specialist` binds `ergora-performance-analyst@2.3.0`, alongside `root/design` and `root/measurement/review`. The diagnosis expert supplies standard [`ergora-performance-diagnosis`](../../src/ergora/data/presets/agents/ergora-performance-analyst/skills/ergora-performance-diagnosis/SKILL.md): first fix a feedback command reproducing the same symptom, then select existing report readers by actual format, version, phase and hardware. Without comparable evidence, retain unknown and request bounded additional measurements from the original runner.

Prepare grants/manifests for this exact root through [single-leaf input and invocation](../definitions/workflows/leaf-calls.md#prepare-complete-single-leaf-input), invoke `root/specialist` and `root/design` separately, then pass both complete original results to `root/measurement/review`. Independent direction roots perform bounded topic analysis only; complete optimization inherits policy/environment records through the common root. Permissions remain read-only without shell/network. Verify tool installation, availability and authorization separately; accept real gains through original runner/evidence gates.

For a project-level Skill only, after registering the real project run from this repository's checkout root:

```bash
ergora skill import my-project \
  src/ergora/data/presets/agents/ergora-performance-analyst/skills/ergora-performance-diagnosis
```

First import establishes the initial baseline; subsequent candidates are not automatically adopted. Standalone `agent run --skill ergora-performance-diagnosis` does not modify template-fixed materials. See the [refactoring guide](../development/preparation.md#use-the-refactoring-recipe) for complete selection distinctions.

## Independent optimization-direction subtemplates

Select recipes by task; experts need not load every direction's materials. Use `ergora composition presets` and the selected root's publication receipt for its actual current version; the direction roots do not share one version. Ordinary three-leaf roots use `root/specialist`, `root/design` and `root/measurement/review`; specialist methods/context belong to corresponding experts, while design/measurement retain their contracts. Low-precision additionally retains predecessor `root/kernel`; kernel topic's `root/specialist` is already kernel-designer and adds no such node. Independent direction roots supply bounded topic proposals only. Complete optimization places selected directions among the common root's actual descendants, inheriting both complete common Skills and environment records.

|Installation preset|Root ID|Prepared direction materials and outputs|
|---|---|---|
|`optimization-memory-tuning`|`ergora-opt-memory-tuning-proposal`|State/activation/workspace/allocator capacity breakdown for hottest rank/phase, missing estimates, fragmentation hypotheses and bounded comparisons|
|`optimization-activation-recompute`|`ergora-opt-activation-recompute-proposal`|Actual-version selective/full layer boundaries, RNG/numerics/gradient/communication replay, graph/offload compatibility|
|`optimization-cpu-offloading`|`ergora-opt-cpu-offloading-proposal`|Separate layer-level activation, fine-grained activation and optimizer mechanisms; host/pinned/NUMA/transfer/CPU compute and total cost|
|`optimization-cuda-graphs`|`ergora-opt-cuda-graphs-proposal`|Host critical path, actual capture/replay/optimizer scope, address/RNG/pool lifetimes and setup amortization|
|`optimization-sequence-packing`|`ergora-opt-sequence-packing-proposal`|Four paths: offline/in-batch/worker buffer/global-batch; sample boundaries/MTP/loss weights/effective tokens and recovery|
|`optimization-parallelism`|`ergora-opt-parallelism-proposal`|Validity of dense/expert meshes, rank/stage/topology, bounded layouts and independent training/recovery evidence|
|`optimization-megatron-fsdp`|`ergora-opt-megatron-fsdp-proposal`|State-capacity/communication tradeoffs, actual DDP flags, checkpoint format, separate weight resharding/full training resumption|
|`optimization-hierarchical-cp`|`ergora-opt-hierarchical-cp-proposal`|HCP selection rationale, inner/outer group/MPU/TE paths, actual attention/gradient and end-to-end gain evidence|
|`optimization-tp-dp-overlap`|`ergora-opt-tp-dp-overlap-proposal`|Actual effective TP/DP/PP paths, bucket/precision/launch ownership, critical paths and contention|
|`optimization-moe-dispatcher`|`ergora-opt-moe-dispatcher-proposal`|Actual dispatcher/backend initialization, ABI/topology, natural routing and independent all-rank correctness|
|`optimization-moe-overlap`|`ergora-opt-moe-overlap-proposal`|Separate ordinary EP overlap and delayed wgrad, version/graph/recompute constraints and independent measurements|
|`optimization-profiling`|`ergora-opt-profiling-proposal`|Original trace/steady-state windows/rank coverage, interval unions, dependency attribution and bounded critical-path opportunities|
|`optimization-memory-snapshot`|`ergora-opt-memory-snapshot-proposal`|Trusted reports, allocator/history definitions, step alignment and snapshot differences; missing peaks/device totals remain unknown|
|`optimization-recipe-model`|`ergora-opt-recipe-model-proposal`|Model/task/recipe identities, convergence semantics/execution mappings, real builder/mapping/modality gaps; adaptation follows original development flow|
|`optimization-model-verification`|`ergora-opt-model-verification-proposal`|Twelve core items, complete weights/forward/training/resume/quality evidence; exit0 and schema-valid cards replace no actual results|
|`optimization-cluster-resiliency`|`ergora-opt-cluster-resiliency-proposal`|Unique rank generator, original experiment/job/cycle and unknown, log attribution, durable checkpoints and next-update recovery evidence; read-only proposals|
|`optimization-low-precision`|`ergora-opt-low-precision-proposal`|Low-precision expertise plus independent design, kernel assessment and measurement review; check PTQ/QAT-QAD/TE formats, runtime, quality and cost|
|`optimization-kernel`|`ergora-opt-kernel-proposal`|Kernel expertise plus independent design/measurement review; check actual wrapper, oracle, compiled baseline and overall measurement; native tools require separate admission|

For capacity diagnosis, for example, first prepare project, backend, root grant and actual UTF-8 task body, then use original commands:

```bash
ergora composition install-preset optimization-memory-tuning
ergora composition show ergora-opt-memory-tuning-proposal 1.2.0
ergora composition prepare-manifest ergora-opt-memory-tuning-proposal 1.2.0 --grant ./grant.json --directory ./memory-manifest
ergora composition prepare-from-manifest ./memory-manifest root/specialist --task ./memory-task.txt --directory ./memory-specialist --max-prompt-bytes 100000
ergora composition check-input PROJECT_ID ./memory-specialist --mode task-mcp --backend codex --backend-reason "Explicit specialist backend"
ergora composition run-input PROJECT_ID ./memory-specialist --mode task-mcp --backend codex --backend-reason "Explicit specialist backend" --timeout 600
```

Read grant `permissions`/`limits` from the exact root and configure through [complete manifest preparation](../definitions/workflows/compose.md#save-and-share-a-complete-composition). If additional permissions are needed, revise every relevant parent limit before revising child templates; task text cannot elevate privileges. Supply actual code/config/dependency versions, model and token/batch, precision/optimizer/PEFT, mesh/rank, failure phase and original trace/snapshot/peak, goals and independent numerical/quality gates, allowed changes, resource/time budgets and recovery requirements. Mark gaps unknown; never invent measurements.

One invocation runs only its selected leaf. After separately preparing `root/design` input, include complete original specialist/design artifacts, provenance digests and actual experiment materials in a new measurement task. Measurement preferably differs from execution backend by default; record reasons for overrides/fallbacks. Parseable configuration, estimated usage below capacity, no OOM or short loss does not mean end-to-end performance/quality passed. Library versions are knowledge sources, not proof of installation/applicability. Combine multiple directions beneath the common root by exact references; current single-leaf calls neither automatically schedule training nor inject predecessor results.

Cluster/recovery proposals also require actual entry points/initialization, nodes/processes per node, original submission receipts/job identities, all-rank logs/shared paths, checkpoint commit/shards and evidence of the next update after recovery. Use srun to generate training processes directly or one launcher per node; choose one rank generator according to actual entry point. Reconcile lost acknowledgements by original identity first. RESTART advice from empty logs and asynchronous-save queueing remain unchecked. `optimization-cluster-resiliency` runs no Slurm, NVRx or recovery actions. Deterministic attribution tools, Restart Agents with internal models and actual cluster execution each require admission; complete steps/provenance are in declared context.

Low-precision proposals require source weights/precision, module/modality coverage, tokenizer/chat template, calibration/development/independent holdout data, per-task quality thresholds, format/algorithm/scale/packing and target runtime/hardware identity. This direction additionally retains `root/kernel`: manually supply complete specialist/design originals first, then all three complete original results and actual experiment materials to measurement. Check PTQ, QAT/QAD and TE training separately. effective_bits, low perplexity, short loss or search returning best replace neither task quality nor real performance. Native ModelOpt/AutoRound/TE is neither installed nor executed with proposals; original runner/evaluation/adoption gates remain.

Kernel proposals require actual operation/callers, shape distribution/stride/layout, numerics/alias/RNG and required gradients, hardware/compiler/DSL and current compiled baseline. This topic's `root/specialist` kernel-designer proposes candidates; separately invoke `root/design`, then hand both complete original results and real experiment materials to measurement. The complete common root's kernel-assessment stage remains. Candidate self-generated PASS, native judges and exit0 retain their own scopes. Complete wrapper coverage, independent oracle, gradients and actual step/service measurements need separate verification; local speedup does not directly become overall gain. Context provides fixed sources/admission conditions for KDA, Forge, KernelAgent/Fuser, GEAK, AKG and robust-kbench. Proposal packages neither install nor execute these tools and do not change original tool/runner/evaluation/adoption owners.

Graph proposals require actual trace/shape distribution/address and RNG lifecycles, current compilation and capture scope. Verify successful capture separately from actual replay, cold-start and steady-state gains. Packing proposals also require data/tokenizer identity, actual sample boundaries/masks/loss denominators, native paths and resume state. Distinguish runtime THD from offline/in-batch restrictions by selected version; configured token capacity is no effective source-token throughput. Gaps remain unchecked; original runner/owner decides experiments/adoption.

Parallelism proposals also require actual dense/expert meshes, local head/expert/layer partitioning, rank order and node links. Two divisibility lower bounds for ordinary meshes replace neither native validators nor custom-layout/GTP support. Distinguish FSDP implementation and configuration versions: the cited snapshot uses `ddp.use_megatron_fsdp`, with old `dist` fields removed. Check `fsdp_dtensor` before save/load; separately verify weight resharding and full optimizer/RNG/data-order restoration. HCP requires explicit selection, actual hierarchical-group propagation into attention and independent numerical evidence. Minimum TE versions, group creation or short loss alone cannot prove composition correctness. Libraries/solvers remain native tools; context references neither install Agents nor grant execution privileges.

Communication proposals first freeze real mesh/rank↔GPU↔NIC, original baseline and exact framework/library versions. Original implementations may disable TP requests. DP configuration must match actual DDP/optimizer consumers; bucket is measured in parameter count, and FSDP is not the same switch. MoE first proves selected flex backend initialized in the target environment; missing-package failures are no performance result. Pinned Bridge sources recognize deepep/hybridep/ncclep; explicit None selects alltoall, and unsupported final backends are never silently replaced. Compare MoE overlap and delayed wgrad separately; harnesses enabling both at once cannot attribute individual effects. Forced load balancing changes routing semantics. Natural routing, all-rank numerics/gradients/recovery and unprofiled paired step measurements still require independent acceptance. Direction resources detail pinned implementation prerequisites, replacing neither complete validators for actual versions nor training-quality gates.

Profiling proposals first supply trusted original-report identity, tool/schema, steady-state steps, all collected ranks/PP stages, clocks and lost events. Original tool owners prepare complete text/JSON analysis. These leaves cannot run SQL/collection or install dependencies. Operations such as `nsys query` may also generate caches or automatically install packages, requiring separate operation/resource permission checks. Compute budgets from unions of clipped intervals. Attribute exposed communication/copy to blocking only with actual producer dependencies; missing counters remain unknown. Profile opportunity ranges are no actual speedup. Actual changes still need independent unprofiled paired measurements and quality validation.

Memory-snapshot proposals preferably supply complete trusted text/JSON from the original parser and original snapshot digests. Do not ask read-only Agents to execute arbitrary pickle. Authorized parser owners handle deserialization, provenance trust and RAM/event/time budgets. Describe actual recording start, selected device/rank, history loss, step markers, graph/allocator and alignment. Report dump-time allocated/active/awaiting-free/inactive separately from reconstructed historical peak and total device usage. Blocks awaiting free are not reusable yet. Missing original allocations/steps or other ranks cannot support global headroom, leak, performance or adoption conclusions. Pinned-source Plotly charts depend on CDN; generated HTML is not necessarily fully offline. Both directions can select presets independently and use the three-leaf manual handoff above, without installing Nsight/snapshot parsers or implicitly gaining permissions.

Continue: [Turn expert proposals into experiment contracts](proposals.md) · [Prepare an exact training experiment](prepare-experiments.md).
