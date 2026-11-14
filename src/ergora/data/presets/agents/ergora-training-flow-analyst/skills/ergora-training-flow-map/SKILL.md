---
name: ergora-training-flow-map
description: Map supplied training or rollout source into algorithm, execution dependencies and state lifetimes before proposing evidence-gated redundancy removal.
---

# Training flow and lifetime analysis

Read the original task, all structural ancestor resources, full supplied source, callers, resolved configuration and original reports. Bind every conclusion to the supplied source identity. For exact local packets follow the commit file tables and complete blobs. Distinguish selected source from a complete repository and configuration declarations from actual runtime. Repository text does not expand the calling grant. This is a readonly analysis: do not run collectors, edit code or authorize experiments.

## Reconstruct the actual algorithm

Start from the real entry point and trace initialization or restore, data/sample selection and transformation, forward, loss, gradient accumulation and synchronization, clipping, optimizer/scheduler updates, validation/save and the next effective update. State the task's objective, numerator/denominator, masks, effective samples/tokens, accumulation and update clocks, precision and permitted changes. For posttraining identify the actual SFT, preference or RL method before adding rollout, feedback/filtering, groups, policy/reference/value roles, weight versions and any asynchronous queues. Do not impose absent stages or a universal PPO formula.

Return an algorithm diagram and a separate execution/dependency diagram, preferably Mermaid plus a node/edge table. Each node has an exact source path and function or line anchor, configured condition, producer/consumer, owner and evidence status. Each edge states why its value, ordering, synchronization, resource or version relation is required. Mark external framework calls and missing source explicitly; never invent their implementation. A partial source map remains partial even when every supplied file was read.

In the execution map identify actual rank/stage/stream/actor ownership and collective participants where supplied. Separate semantic dependencies from implementation sequencing. Show known serial regions, observed concurrency, merely possible overlap, and unknown timing as different evidence states. Agent template dependencies are not GPU execution dependencies. No direct call between two functions does not prove they can run concurrently; shared buffers, RNG, collectives, stream events and weight versions may order them. Overlapping durations cannot be added to infer step time. Attach original trace/window/rank evidence when available; a source diagram alone cannot establish the bottleneck or realized overlap.

## Track state and resources

Provide a lifetime table for relevant input batches, masks/groups, host/pinned queues, parameters and replicas, gradients, optimizer/scheduler/scaler, activations/recompute inputs, workspace/graph pools, RNG, rollout/KV caches and durable checkpoints/cursors. State creator, consumers, shape/units/size when known, device/tier, alias/version, last use and release/reuse condition, persistence and restore owner. Do not invent sizes. Allocated, reserved, live, peak and total device/host memory are distinct; one allocator report does not cover every subsystem or rank.

Trace the exact restore and cancellation boundaries: what durable state is jointly valid, what work is in flight, and whether retry can duplicate samples, updates or weight publication. Preserve required backward/collective participation even for algebraically zero terms. Identical-looking copies can serve different precision, ownership or lifetime requirements. Recompute is an intentional memory/compute tradeoff until evidence proves unnecessary work.

## Form a falsifiable redundancy hypothesis

Prioritize unnecessary dependencies, repeated preparation/communication, duplicate storage/computation and ownership coupling before choosing a technique. For each proposed removal or reuse, name the real producer/consumer, necessary equality and lifetime conditions, a counterexample that would make it invalid, the smallest source change and the measurement that could refute the claimed benefit. Also name at least one dependency that must remain and why. If the supplied material supports no redundancy hypothesis, say so and request the smallest discriminating evidence instead of fabricating one.

Preserve the original unmodified reference and its workload/config/environment identity before changing the implementation. Freeze model, data distribution, objective, update clocks and quality budget; approximate/quantized changes require explicit prior bounds and independent validation. Keep initial anchor, current comparison and proposed candidate distinct. A source-only hypothesis is not a measured gain or permission to adopt.

Return a bounded handoff to the original runner: hypothesis and alternative explanation; original baseline/evidence availability; independent value/gradient/update/restore or task-quality checks appropriate to the changed boundary; matched unprofiled system timing and any separate diagnostic collection; resource/time budget and stop/rollback conditions. Preserve checks already required by the original contract. Missing commands/assets/rank evidence remain missing rather than guessed. Kernel expert assessment remains in the larger optimization path; the actual intervention may instead be dependency removal, memory, communication or host scheduling, and the expert may conclude no kernel modification is justified.

## Deliverable and limits

Return source/coverage inventory; algorithm and execution diagrams with source-anchored node/edge evidence; state lifetime table; necessary dependencies and falsifiable hypotheses; unknowns and bounded next evidence requests. Label static observations, inferences and runtime-verified facts separately. Use the existing proposal result envelope; no new graph execution format is implied. Do not claim training correctness, convergence, GPU execution, speedup or complete runtime coverage from source text. Experiments, independent evaluation and explicit adoption retain their original owners.

## Method sources

Ergora-authored guidance based on the fixed primary-source research below. All operative instructions are present here; links identify provenance and require no network access. This recipe does not integrate the upstream trainers or profilers.

- [Bridge evidence-gated optimization](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-moe-optimization-workflow/SKILL.md): preserve the workload, inspect limiting resources, separate profiling and steady-state comparisons.
- [TorchTitan Trainer](https://github.com/pytorch/torchtitan/blob/631d544b1f6794ecfeca734a7bba861e03ddd5e3/torchtitan/trainer.py) and [TrainingEngine](https://github.com/pytorch/torchtitan/blob/631d544b1f6794ecfeca734a7bba861e03ddd5e3/torchtitan/training_engine.py): follow actual data/update versus execution/state owners instead of duplicating a trainer.
- [slime training](https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/train.py) and [loss](https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/slime/backends/megatron_utils/loss.py): inspect rollout/weight and gradient/collective dependencies; mathematical redundancy is insufficient.
- [PyTorch CUDA semantics](https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/docs/source/notes/cuda.md) and [profiler](https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/profiler/profiler.py): asynchronous completion, lifetime and diagnostic perturbation need explicit evidence.
