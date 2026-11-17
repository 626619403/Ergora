# Experiment evidence contract

This is Ergora-authored synthesis of the fixed research sources below; no upstream prompts, Skill bodies or code are redistributed. URLs are provenance, not evidence that a tool is installed or that a model fetched it.

An optimization action changes a known baseline. Record model/data/token regime, shapes and distribution, dtype, runtime/dependency versions, rank/mesh/device topology, target metric, quality gates, warmup and measurement window. If a required field is missing, name it and describe what it prevents; do not invent hardware or substitute microbenchmarks for the target workload.

A bounded proposal states baseline and candidate identities, permitted variables, resource/wall/trial budget, correctness and quality oracle, stop conditions, repeat/pairing scheme and rollback. A candidate combining two changes is a new candidate. Memory headroom, host bandwidth, network contention, capture lifetime and numerical quality can couple directions. A recommended recipe or solver output has to be checked in the actual runtime.

The original runner owns experiment IDs, artifacts, job/stop/recovery and evidence; the owner separately approves adoption. A journal, study or search tree does not prove stopped workers or restored training state. Missing, failed, no_gain, noisy and unknown outcomes retain their meaning. No claim of token, provider API or financial enforcement follows from a proposal's budget text.

Sources reviewed in Ergora R4/R5/R9/X1/X3 on 2026-11-12: Megatron Bridge 0.8.0 reference snapshot https://github.com/NVIDIA-NeMo/Megatron-Bridge/tree/55694838ce73cd23b00ff95bd00512aefb963ce0; Optuna study/optimization and Ray Tune fault-tolerance code at the fixed revisions recorded in those reports. This package uses their distinctions as design knowledge; it neither imports those libraries nor runs their schedulers.
