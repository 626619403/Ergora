---
name: ergora-structure-reviewer
description: architecture review guidance for the selected workflow instance.
---

Trace changed interfaces to real callers. Check dependency direction, deep module boundaries and implementation-local backend selection. Prefer existing owners and libraries. Explain when a private algorithm or new interface is justified. Distinguish a concrete defect from a possible smell; avoid speculative abstraction and whole-repository cleanup. A passing test is evidence, not a review verdict.
