# Main branch integration

Preparation checkpoint (2026-11-19): branch content and history are consolidated and the integration branch has been ordinarily pushed. Documentation/archive/source-identity checks have passed; final independent review and the integration Portability gate are in progress. The final `main` update and ancestry-gated remote branch cleanup follow those gates.

## Scope and source

The source baseline is `ace1deade97ac39182e0d34c1a5777afc0663b3e`, with source tree `dc4c231e4f7f51227ca1adf66d6693e338db49a9`. Source, tests, scripts, runtime resources and required dependency declarations retain their exact baseline identities. The old remote `main`, `cab3a724e421d0a7d9ff6f03dfcbd3225361e2f1`, is an ancestor of that baseline.

All 23 observed remote heads are ancestors of the integration candidate. The configuration and template-identity branch commits have stable patch IDs equal to already delivered ancestors. The cycle-overlap fixture's two complete changed functions are byte-identical to their delivered counterparts and current consumers. Their histories are retained without restoring earlier interfaces. The process-supervision branch changes only four explicitly temporary experiment documents; its original commit and bytes are preserved without adopting it as product behavior.

Current user guides point installation and source ZIPs to `main`, use the actual current preset IDs, and describe explicit finite frozen-candidate training controllers. Adaptive generation and automatic per-round profiling remain separate work. The current six-stage workflow, candidate binding, original budgets, unknown reconciliation and unique reaper are unchanged.

Old plans, delivery logs, research, handoffs and history documents are excluded from the final documentation tree after every archived file's bytes and digest were read back. Original Git commits remain intact. Unneeded remote heads are removed only after the final main includes their exact commits; local development branches and active worktrees are retained. The current plan and this active record satisfy the repository's continuity rules.

## Actual validation and remaining work

- Remote head OIDs were fetched and independently compared; all 23 ancestry relationships were checked after history integration.
- The retained 77 root, guide and example Markdown files passed relative-file and Markdown-anchor checks with no missing targets. `git diff --check`, current preset-catalog checks, all archived-file byte/digest/mode checks and source/test/script/dependency identity comparisons passed.
- A fresh-context independent reviewer has independently checked branch content equivalence, current resource references and preserved source/test/script identities. Final complete-document review is pending.
- No new runtime, model, GPU or installation acceptance is claimed for this documentation-only delta. The published integration ref has its own Portability run in progress; the final normal `main` push waits for its actual result and complete independent review.

The [current plan](../PLAN.md) tracks the next action and remaining implementation boundaries. Historical results retain their original source and scope.
