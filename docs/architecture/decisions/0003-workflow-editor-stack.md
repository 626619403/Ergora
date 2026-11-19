# ADR 0003: Graphs and forms in the workflow editor

English · [Documentation](../../README.md)

Date: 2026-11-05. This ADR records the frontend selection context; see the [architecture](../interfaces.md#graphical-pages-and-low-code) and [workflow guide](../../definitions/workflows/revisions.md#view-published-nested-relationships) for the current pages and formal handoff.

## Decision

Retain the current Cytoscape, native ES modules, and existing Python distribution. The next slice will unify the semantic editing state of the graph, property form, and JSON within the existing `workflow.js` owner, progressively adding bounded editing commands, undo/redo, protection for unsaved changes, and revision conflict handling. Field descriptions cover only input types actually used; they do not create a second configuration DSL or a general form framework. Position/viewport state is separate from semantic input; the server continues to own contract validation, digests, revisions, and formal task facts.

Keep React Flow as a reproducible developer candidate; JSON Forms does not become a default dependency. This is not a general verdict on the two libraries. The complete React Flow entry was smaller than the Cytoscape entry in this comparison, and both template journeys passed for all three adjusted alternatives. The existing stack was chosen because it can already implement the current features, no measured bottleneck requires a framework migration, and React Flow does not replace the editing/saving semantics this project must own.

JSON Forms' default Ajv compilation actually conflicts with the existing CSP. Official NoValidation rendering together with explicit validation by the existing backend completed this journey, but provides no client-side Schema error messages, and its complete entry is approximately twice the size of the native alternative. The default distribution currently lacks enough dynamic form demand to justify introducing this stack; do not relax CSP or describe it as precompiled validation.

## Boundaries and reevaluation

Graph edges currently represent only work-unit dependencies; the original role/tool bindings still own Agent implementation selection. Role responsibilities, artifact flow, permissions, and execution stages must not be conflated into a single connection. The six stages and trusted integrate/verify/review cannot be arbitrarily removed or changed by the canvas.

The framework manages projections and interactions; it does not own template compilation, Agent execution, issues, review authorization, or candidate evidence. Editor state remains with its actual lifecycle owner. Do not create a default plugin system for experimental adapters or copy the experimental UI directly into production.

When actual port interactions, custom nodes, node keyboard requirements, or F6.3 capacity results demonstrate that the current alternative is insufficient, rerun the same journeys and relevant loads before deciding on a React Flow migration. Evaluate JSON Forms/precompiled Ajv separately when dynamic schemas/complex rules and client-side error messages offer a clear benefit. Reevaluation must preserve the original CSP, domain contracts, and actual distribution costs; the current single loopback timing and unmeasured large graphs cannot serve as performance conclusions.

F6.1 changed no production code, default dependencies, or package resources. Reverting this slice removes only the developer examples and selection notes; subsequent production features each have independent acceptance, review, and delivery records.
