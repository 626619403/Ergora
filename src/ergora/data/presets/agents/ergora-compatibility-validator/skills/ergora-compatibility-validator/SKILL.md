---
name: ergora-compatibility-validator
description: Validate an integrated interface migration and its rollback against the approved compatibility contract.
---

1. Bind the checks to the exact candidate, real callers and required old/new behavior. Complete when relevant interface and persistent-format combinations have explicit coverage or a recorded gap.
2. Exercise the meaningful failure and rollback cases with isolated fixtures. Complete when actual results, including failures, identify the candidate and the oracle used.
3. Return the requested artifacts with migration status, rollback evidence and unverified conditions. Complete when independent reviewers can assess behavior and test value without treating a proposal as a passing result.
