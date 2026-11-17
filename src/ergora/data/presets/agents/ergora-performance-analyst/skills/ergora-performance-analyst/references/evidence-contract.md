# Profiling and diagnosis evidence

Ergora-authored synthesis, not redistributed upstream Skill text. Read actual supplied data; source links are provenance and confer no tool, filesystem or network permission.

A useful trace has exact code/config, device/rank and mesh, warmup/steady-state selection, tool and dependency versions, timestamps/units, collection flags and loss/quality context. Preserve truncation, dropped events and missing ranks. A trace collected with extra synchronization or shape/stack/memory recording can perturb runtime. Async launch duration, summed kernel time, GPU busy time and end-to-end step time answer different questions.

Follow dependencies before assigning a bottleneck. A collective can be delayed by an earlier rank, data preparation can starve launch, and an overlap intervention can consume SM/HBM resources needed by compute. Rank means hide stragglers. Compare matched windows and state the number of samples. Do not claim all-rank peaks from one rank or allocator totals from a device estimate.

Memory snapshots distinguish live allocations, allocator reserve, fragmentation and transient peaks. A snapshot comparison needs matched steps, rank, model, allocator behavior and instrumentation. CPU offload also spends host/pinned memory and transfer bandwidth; released GPU memory alone does not prove throughput benefit.

Primary fixed knowledge source: Megatron Bridge https://github.com/NVIDIA-NeMo/Megatron-Bridge/tree/55694838ce73cd23b00ff95bd00512aefb963ce0, including skills/nemo-mbridge-perf-nsys-analysis and nemo-mbridge-memory-snapshot-analysis; R7 recorded their original scripts, pitfalls and Nsight/PyTorch tool boundaries on 2026-11-12. No Nsight, torch profiler or MCP execution is bundled by this definition. Request missing reports rather than synthesizing them.
