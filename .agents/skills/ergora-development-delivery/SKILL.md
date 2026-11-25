---
name: ergora-development-delivery
description: Move Ergora development from a requirement to verified use. Use when choosing development slices, coordinating CI or reviews, or staging a release or daily installation.
---

# Develop and deliver Ergora

## Choose work by the decision it unlocks

Read the current checkpoint and active work in [PLAN.md](../../../docs/PLAN.md). For each change, name the operator or other caller, the decision they need to make, and the smallest evidence that can settle it. Separate a controlled proof, a published capability, the daily installation, and use by a real consumer.

If real use is blocked, record the concrete dependency, who owns it, and the observation that will unblock it. Pursue that dependency and continue independent authorized work. Add another fixture or inspection feature when it answers a remaining question for a known consumer. Keep filesystem and credential isolation, original Job ownership, and actual resource release in the real-use acceptance scope where they apply.

## Integrate and qualify coherent changes

- Review one coherent behavior with its actual failure and recovery cases. Follow the existing [review scope and granularity](../../../docs/review/invoke-and-aggregate.md#choose-review-scope-and-granularity). Keep the independent check that can catch a real contract failure. Group related source changes and associated guide or diagram refreshes when they serve the same delivery.
- Track development integration, release qualification, and daily activation separately. Reuse an already verified wheel or check when the covered bytes, dependencies, test inputs and behavior match. Rerun checks affected by later changes or required by the selected release policy. Bind CI evidence to the exact head and attempt, and live postflight to the actual activation.
- For CI and other long waits, assign one observer to the original run or owner. Prefer notifications or a bounded deterministic watcher that reports a terminal result, changed blocker, or timeout. Advance independent work while waiting. When a later push would cancel a required check in the same concurrency group, schedule it so the chosen release still gets its required evidence.

## Update the daily installation during idle windows

Stage candidates and keep developing as checks complete. Keep the daily installation on the qualified usable version across intermediate merges, CI runs, and minor increments. After a major update is complete, a single idle-window activation can include its related changes. Use the change in actual user-facing capability, compatibility, or reliability to judge whether an update is major.

Choose a window when the protected state has no conflicting owner or writer and the upgrade will not interrupt active use. If the window is busy, keep the exact qualified candidate staged and record the condition for the next check. Follow any explicit user instruction about rollout timing. Use the existing [upgrade and recovery procedure](../../../docs/install/upgrades.md#upgrades-and-persistent-data). Verify the actual version, protected state, and service after activation.

## Keep the next action easy to resume

Keep one current status per outcome in [PLAN.md](../../../docs/PLAN.md), with links to original delivery evidence. When timestamps are available, distinguish requirement to first usable evidence, evidence to qualified release, and release to actual use. Attribute waiting to a named dependency and preserve the source of each status. After compaction or handoff, use the checkpoint and original receipts to resume the next authorized action.
