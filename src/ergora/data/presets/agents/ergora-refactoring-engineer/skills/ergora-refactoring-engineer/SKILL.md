---
name: ergora-refactoring-engineer
description: Implement a scoped module refactor while preserving the approved behavior and caller contract.
---

1. Locate the implementation, interface and real callers in the approved unit. Complete when each affected caller and behavioral invariant is accounted for by source or an explicit gap.
2. Make the planned change and caller migration. Keep the interface small; use the deletion test to explain where complexity now belongs. Complete when the diff stays within scope and the original behavior has relevant evidence.
3. Return the required change artifacts, actual check results, migration status and rollback procedure. Complete when the next validation unit can reproduce the checks and identify every unverified condition.
