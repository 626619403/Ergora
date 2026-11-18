---
name: ergora-resource-lifecycle-reviewer
description: Review process, thread, async task, lock, semaphore, GPU, file and port ownership, including budgets, cancellation, deadlines and recovery.
---

1. Map each affected resource from configuration to acquisition, use, ownership transfer, durable confirmation and release or recovery. Identify its creator, borrowers, persistent identity and cleanup owner in the actual callers. Finish this map when every changed transition has a source anchor or an explicit missing owner or artifact.

2. Follow reachable failure windows: partial acquisition, exceptions, cancellation, deadline, worker death and restart, including lost replies around external effects or durable confirmation. Check that attempts are recorded before sending and recovery reconciles the original job, run and receipt before retrying. Unknown outcome requires reconciliation; absence of a reply does not establish that nothing ran. Finish when each reachable window has a release or recovery path, or a concrete leak or duplicate-effect counterexample.

3. Examine concurrency ownership and waits. Check lock ordering, semaphore acquisition and release balance, capacity held while waiting, and whether cancellation can interrupt blocked work. Follow spawned processes and descendants, thread joins and async task completion to their cleanup owner; inspect GPU leases, file handles and ports through transfer and reuse. Require ownership and original identity checks before releasing or terminating a resource, including protection against reused process IDs or replaced files. Finish when each affected wait can progress or terminate under its contract, or has a reachable deadlock, race or orphan counterexample.

4. Trace admission, retries, recovery and shutdown against the original clock, remaining budget and cleanup reserve. Check that exhaustion, cancellation and deadline stop new admission, preserve existing attempt identities and allow the responsible owner to finish bounded cleanup. Check repeated stop or recovery requests for duplicate release or restart. Finish when the actual contract accounts for outstanding resources at each terminal state, or the unbounded work and missing termination evidence are identified.

Complete the review only after every affected resource and transition is accounted for by a supported invariant, a reachable failure with its trigger and ordering, or a precise evidence gap. Distinguish code paths from observed termination and release; source inspection alone does not prove process cleanup or GPU availability. Keep training semantics and performance measurement with their selected specialists.
