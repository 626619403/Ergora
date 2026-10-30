# Ergora work continuity

At the start of work, after context compaction, or after switching machines:

1. Read `docs/PLAN.md`, including the current checkpoint and the active slice.
2. Check the current branch, `git status`, and recent commits. Reconcile these with the checkpoint before editing.
3. Read the active slice's delivery record and relevant implementation. Treat older research as design evidence, not as proof of implemented features.

Update `docs/PLAN.md` when a slice changes state, validation finishes, a decision changes, or work is handed off. Record actual checks and remaining work in that slice's delivery record under `docs/delivery/`. Keep secrets, runtime data, and machine-specific paths outside public documents.

Use a fresh-context independent reviewer for each complete implementation slice. Give the reviewer the raw requirements, baseline, changed files, and actual validation. Resolve findings and record the result before marking a slice complete. Reviews and status bookkeeping do not require recursive reviews.

Keep the existing six-stage development contract and candidate-bound evidence intact while migrating the reference implementation. Optional tool integrations must expose their actual availability and supported operations. Unsupported capabilities must fail visibly.
