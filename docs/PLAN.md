# Current implementation and delivery

The current implementation comes from `ace1deade97ac39182e0d34c1a5777afc0663b3e`. Its source, tests, scripts, runtime resources and required dependencies are preserved while the existing remote branches are consolidated into `main`. Start with the [README](../README.md), [usage guide](USAGE.md) and [component change protocols](architecture/component-change-protocols.md).

## Active slice

[Main branch integration](delivery/2026-11-19-main-branch-integration.md) records the exact branch coverage, current checks and remaining delivery work. The 23 observed remote heads are ancestors of the integration candidate. Equivalent commits retain their original history; the process-supervision experiment remains an experiment.

The candidate keeps the current six-stage development workflow, candidate-bound evidence, original budgets, unknown-result reconciliation and existing process cleanup. Current installation guides use `main` and the actual bundled preset IDs. Working plans, diaries, research and old check artifacts remain available in their original Git commits and in a verified private archive.

Delivery checkpoint (2026-11-19): content review approves `a174bdbba3441d43d39d052a8824d232cb1b1bc6` on both requirements and maintainability, with no open blocking findings. [Portability 44494319222](https://github.com/626619403/Ergora/actions/runs/44494319222) succeeds in 28m36s for exact head `792b7cf003dfef842e9540af5265b23cbecf40a0`: all 12 jobs and 11 Native regression groups pass, including Windows and PowerShell 5.1 installation/upgrade. Source, tests, scripts, required dependencies and workflow identities are identical in the reviewed documentation successor. This slice meets the main delivery gates; the exact current remote state is authoritative in Git. Status-only documentation does not relabel or rerun the original CI evidence.

## Remaining implementation boundaries

- Adaptive candidate generation and automatic per-round profiling are separate from the supported finite frozen training selection.
- Design and knowledge gates, trusted non-Agent verification nodes, general bounded Repeat and mixed workflow canvases remain staged work.
- Real Temporal service recovery, GPU admission/execution and workload quality/performance require their own measured acceptance.
- Backend availability, supported operations, authentication and execution are reported separately; unsupported operations fail visibly.

Update this page and the active delivery record when this slice changes state. Keep credentials, runtime data and machine-specific paths outside public documents.
