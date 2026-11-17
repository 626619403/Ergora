# Tests at the relevant interface

Start from the observable behavior or reported symptom. Identify the calls and state transitions needed to expose it: multiple callers, repeated execution, partial failure, restart, cancellation or migration may matter. Select the smallest interface that still contains that sequence. A passing isolated helper does not protect a failure requiring the complete caller or recovery path.

Use an existing suitable fixture and test entry. Substitute dependencies whose behavior is irrelevant to the defect, while retaining the calls, state and failure that make it observable. Test a real adapter separately when its external protocol is itself the risk. State which checks are local, simulated or dependent on a live system.

For a bug, keep the original reproducer and a smaller failing case if useful. Confirm the chosen check observes the original failure, then rerun the original scenario after the fix. For a behavior-preserving refactor, retain the necessary interface and compatibility coverage. Remove a shallow duplicate only after identifying where its distinct protection now lives; a cleaner implementation alone is not a reason to delete recovery or contract tests.

Derive expected relationships from the supplied valid configuration. Prefer assertions that reveal plausible silent errors. Report what a check cannot establish and its material runtime cost; avoid tests that merely restate source wording or repeat a failure already exposed by ordinary execution.
