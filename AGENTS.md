# Ergora work continuity

At the start of work, after context compaction, or after switching machines:

1. Read `docs/PLAN.md`, including the current checkpoint and the active slice.
2. Check the current branch, `git status`, and recent commits. Reconcile these with the checkpoint before editing.
3. Read the active slice's delivery record and relevant implementation. Treat older research as design evidence, not as proof of implemented features.

Update `docs/PLAN.md` when a slice changes state, validation finishes, a decision changes, or work is handed off. Record actual checks and remaining work in that slice's delivery record under `docs/delivery/`. Keep secrets, runtime data, and machine-specific paths outside public documents.

For development priorities, CI supervision, release qualification, or daily activation, follow the [Ergora development delivery skill](.agents/skills/ergora-development-delivery/SKILL.md).

During routine development, each direction expert performs proportionate self-checks. Do not keep resident reviewer agents or start separate reviews for preparation, environment binding, documentation edits, or each small fix. Use a fresh-context independent reviewer when consolidating a change batch for integration or merge; provide the raw requirements, baseline, complete changes, and actual validation. Resolve findings within that same batch and release the reviewer when the integration review finishes. When the original formal final-review stage already covers the batch, use that gate without adding a duplicate routine review layer. Tests, trusted verification, candidate evidence and original execution contracts remain required. Reviews and status bookkeeping do not require recursive reviews.

Check only what is necessary for the current stage and its current goal. In optimization, prioritize applicable semantic/numerical invariants, reliable profiling and matched measurements, and resource/budget/recovery obligations; code style, abstraction and architectural polish are not independent optimization gates unless they directly affect that goal. Review granularity follows one coherent ready-to-integrate outcome, not individual files, commits or setup steps. Keep one feature's preparation, implementation, tests, binding and small corrections together; split only genuinely independent delivery goals or contracts that need separate integration. The [review guide](docs/review/invoke-and-aggregate.md) owns detailed stage and granularity guidance.

The supervisor owns cross-direction staffing. Each non-supervisor AI agent may create at most one distinct direct helper within its original project/campaign scope; that helper cannot recursively delegate to more agents. Reusing the same helper is not a new creation, but completion, failure, renamed tasks or tool changes do not renew the quota. Route additional staffing needs back to the supervisor under the original total/depth/concurrency/budget limits. This restriction concerns AI-agent delegation, not ordinary tool calls, training ranks, DataLoader workers, or the original executor's frozen workflow fanout; it grants no unavailable spawning capability.

Keep the existing six-stage development contract and candidate-bound evidence intact while migrating the reference implementation. Optional tool integrations must expose their actual availability and supported operations. Unsupported capabilities must fail visibly.

During active development, maintain one current implementation and interface. Update their existing semantic owners directly and remove obsolete adapters, version dispatch and compatibility-only tests; do not add legacy interfaces or duplicate resource trees to preserve earlier development versions. Retain the correctness of candidate binding, budgets, recovery and process cleanup, and preserve original validation evidence without relabeling it.

When changing component implementations or their configuration, read the applicable directory's `AGENTS.md` and [component change protocol](docs/architecture/component-change-protocols.md). It identifies extension owners, stable contracts, data and recovery obligations, and relevant checks.
