# Ownership and dependencies

Trace representative production calls, configuration ownership and state lifetime before choosing an interface. Explain what callers must currently know and what the proposed owner would hide. Judge a refactor by changed-call locality and preserved behavior, rather than file length or the number of classes.

Classify a dependency by how it can actually be exercised: local computation, a local substitutable dependency, an owned remote system, or an external service. Use the existing library or project interface when adequate. Introduce injection or an interchangeable contract where a real caller or meaningful test needs variation; keep single-use orchestration with its current owner. Historical immutable bundles are versions, not evidence that runtime code needs another abstraction.

For an adapter, include construction, configuration, execution and resource lifetime in the contract. Select implementations at their existing factory; upper callers should use that contract. Check caller migration order, persisted data and restore compatibility. Show how to reverse the change using the original candidate and lifecycle owner.

Use a deletion thought experiment: identify which caller obligations would reappear if an abstraction disappeared. If none would, consider simplifying locally. Preserve checks whose owners protect external inputs, persistent identity, concurrency or resource cleanup; replace redundant checks only when their real failure remains covered at the responsible interface.
