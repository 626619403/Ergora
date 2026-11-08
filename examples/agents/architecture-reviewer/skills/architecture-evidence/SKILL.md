---
name: architecture-evidence
description: Assess module ownership and abstractions in a code change by tracing production consumers and reachable failure cases.
---

Start from the change's entry points and trace its inputs, construction,
execution and persistence. Compare the proposed owner with existing project or
library implementations before recommending a new abstraction.

For a new interface, inspect the behavior hidden from callers and the actual
variation between implementations. Evaluate configuration interfaces by their
role; test-only use does not establish production reuse. Keep a cohesive private
algorithm local when splitting it would expose unnecessary details.

For added checks and fallbacks, identify the reachable failure and which layer
owns it. Retain persisted-input, resource-lifecycle and coordination checks.
Recommend removing repetition only when its removal preserves those contracts.
