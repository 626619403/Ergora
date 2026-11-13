# Select a reader from the evidence

First identify the original artifact and its producer/version, units, time window, rank/device coverage and collection conditions. Record which of these are absent. Tool names below are optional candidates; use the project's available compatible reader and verify its actual input contract before execution.

| Supplied evidence | Candidate route | Limit to retain |
| --- | --- | --- |
| Training Nsight Systems report or exported tables | Existing profiling direction and a version-matched Systems reader | Verify table layout, units, ranks and dependencies. Use interval unions for overlap; missing events are not zero cost. |
| Inference Chrome trace requiring forward/layer interpretation | An available inference trace reader or matching AI-Infra profiler member | Establish model, phase and layer cadence first. Training-to-inference or one-rank-to-all-ranks conclusions require additional evidence. |
| A trace needing a derived layer guide | A compatible layer-track tool, retaining the original artifact | Generated lanes are an interpretation, not CUDA stream counts or independent measured durations. |
| A selected CUDA kernel's resource counters | Hardware-matched Nsight Compute reader; kernel architecture references when designing candidates | Check supported counters and collection permission. Replay may change concurrent behavior; use a separate matched unprofiled workload to judge gains. |
| PyTorch CUDA allocator snapshots | Existing memory-snapshot direction and a compatible trusted-input reader | Validate allocator/version, rank, step and markers. Allocator state does not account for every device allocation. Deserialize only trusted artifacts. |
| Only a slowdown description, or a report from a different phase/stack | Request a reproducible baseline/candidate feedback command and the missing identity | Keep performance and causal attribution unknown. An unrelated trace may suggest a hypothesis but cannot measure this workload. |

Request the smallest collection that distinguishes the competing explanations, with a bounded window and the original runner's budget. If a tool is unavailable, name the missing evidence or a compatible existing alternative. Preserve original reports and failures. Treat profiler output, synthetic summaries and model arithmetic according to their actual scope; a proposed speedup is not a measured improvement.
