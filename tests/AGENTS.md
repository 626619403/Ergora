# Test change entry point

Before adding, adjusting, or deleting tests, read the [scripts and checks protocol](../docs/architecture/component-change-protocols.md#scripts-and-checks), then find existing fixtures and actual state transitions for the behavior. Tests protect against reachable risks, and expected relationships come from valid configuration; record original failures separately from runs after corrections.

Update explicit CI groups only when a new test file has an independent necessity. Pure documentation changes add no tests; removing duplicate tests requires explaining which seam now covers their unique risks. Label source, installation, service substitutes, actual external calls, and business acceptance separately.
