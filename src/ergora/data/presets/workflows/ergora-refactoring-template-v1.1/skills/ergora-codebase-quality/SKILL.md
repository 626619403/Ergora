---
name: ergora-codebase-quality
description: Ground refactoring, architecture review and test-value review in the target repository's conventions, real callers and failure paths.
---

Read the target repository's applicable instructions and the exact task scope before proposing changes. Use the references for your selected responsibility:

- For code style or maintainability findings, read [repository-style.md](references/repository-style.md). Establish which rules and existing tools actually apply to the changed paths.
- For module or dependency changes, read [module-design.md](references/module-design.md). Follow real callers and move complexity to the owner that can hide it.
- For verification or redundant-test review, read [test-seams.md](references/test-seams.md). Check that the chosen interface can expose the real failure.

Return concrete affected paths, observed evidence, the smallest useful action and its verification. Apply changes only within the selected role's authorization; a review or proposal remains read-only. Use the enclosing workflow's existing approval, candidate, budget and recovery process.
