# ADR 0001: Foundational refactoring boundaries

English · [Documentation](../../README.md)

Date: 2026-11-01. This ADR records the foundational refactoring constraints; see the [architecture](../current.md), [migration contract](../state-migrations.md), and [reference boundary](../reference-boundary.md) for the current implementation.

Implementation check (2026-11-02): R1–R7 were completed according to this decision. See the [current architecture](../current.md) for current owners, retained/removed items, and compatibility exit conditions. The following text preserves the motivations and constraints at decision time; see [ADR 0002](0002-static-boundaries.md) for static boundary choices and R8 protection. Actual acceptance is governed by the respective delivery records.

## Component descriptions and execution

R1 uses one built-in component description distributed with the package to store layers/roles, capabilities, configuration fields, platforms, defaults, and installation recipe identities; agents/tools/projects, Web catalogs/forms, and SDK installers consume it. The description uses JSON, with only the standard library for runtime reads; it does not dynamically import arbitrary plugins through strings. Configuration option descriptions are separate from probes, protocol execution, and authorization; installation status/authentication/service connectivity/task acceptance are reported separately.

This replaces the existing multiple Python/JS/script tool field definitions without adding a general plugin container or Agent base class. Execution still reuses actual owners such as agents/kernel and their SDKs; new tools require corresponding adapters, capability/cancellation acceptance, and documentation. Data declarations cannot create capabilities that the implementation lacks. Registration is limited to explicitly built-in implementations; third-party discovery/hot loading awaits actual consumers.

The component description is the shared configuration interface for the current 7 Agent roles and 5 support layers, with value derived from existing consumers. No callers were constructed for future tools. Forms interpret only supported fields; configuration cannot remove trusted integrate/verify or change approval authority.

## Schema and validation dependencies

R2 adopts JSON Schema Draft 2020-12 for shared structures and chooses `jsonschema==4.24.0` for core structural validation; dependencies will be changed separately at that point, validating wheel/CLI and error paths on both OSes. A2 does not install it or change existing validation. The version choice rests on readable release metadata and standard interfaces; it is not claimed to be the latest or to have passed target-environment acceptance.

|Alternative|Suitability and cost|Decision|
|---|---|---|
|Continue handwritten dict validation throughout|Existing simple rules may remain; driving shared forms/schemas simultaneously requires maintaining a second set of structural rules|Not the overall approach for new shared structures|
|Pydantic as a core dependency|Already used by Web, with convenient DTOs; brings the optional Web stack into every CLI; default coercion/object dumps may change old inputs/digests|Retain for transport DTOs; do not recalculate old contracts from its dumps|
|jsonschema + native JSON dict|Standard data reusable by forms/docs; no model classes required; adds attrs/specifications/referencing/rpds dependencies, with a native wheel in rpds|Adopt; R2 validates package distribution and strict type policy|

Local distribution metadata comparison: jsonschema 4.24.0 is MIT / Python ≥3.9; its own files and the four installed dependencies above total approximately 1.67 MB (excluding tests/bytecode/extra format dependencies). Pydantic 2.11.5 plus pydantic-core totals approximately 6.76 MB, also excluding its other dependencies. These are only installed file bytes on the current Linux system, **not wheel download sizes, Windows measurements, or a performance comparison**. Sources: [jsonschema 4.24.0](https://pypi.org/project/jsonschema/4.24.0/), [Pydantic 2.11.5](https://pypi.org/project/pydantic/2.11.5/), [Draft 2020-12](https://json-schema.org/draft/2020-12).

A structural library does not replace business rules: revision, finite budgets, exact candidates, trusted scoring, and approval remain at their responsibility boundaries. R2 must fix the actual semantics of Python strict-int / bool / finite number, extra fields, unknown versions, and null values, preventing JSON Schema's integer definition for `1.0` or DTO coercion from silently changing contracts. First record existing inconsistencies in an input matrix; do not conceal them by changing golden fixtures. Existing compilation, Skill, and evaluation digests each retain their original encoding; do not let a new schema inject defaults before recalculating old approvals.

A self-built complete schema validator, private DSL, or placing all rules in transport DTOs was not adopted. If target-platform wheel/dependency compatibility fails, retain existing validation and reevaluate the approach rather than automatically switching formats; no runtime compatibility layer was introduced in this round.

## State authority and migration

Continue domain ownership of facts: control-plane projects/assets, Temporal history, reference job ledgers/evidence, Forge native state, and MLflow observations remain separate. Formal task queries are projections with provenance, not a second page state machine; command success, native_finished, and acceptance passing cannot map to the same success.

R3 places control-plane DDL and ordered version migrations at the storage initialization boundary, while business modules retain SQL transactions and specific queries; no ORM/universal repository is introduced. The old format is SQLite user_version=0, 16 tables, and JSON documents; synthetic fixtures cover these tables and file assets. Before changes, R3 must also implement backups, transaction failure recovery, rejection of newer versions, and isolation of old clients from new databases. **The old 0.2.0 binary itself has no version check; setting user_version alone cannot justify claiming it will reject writes.** This is an explicit R3 acceptance item; A2 did not implement migration.

ReMe is a rebuildable retrieval projection; deletion/revision propagation still requires checks. Atomic Skill head updates, research budgets/cancellation, and reconciliation of unknown Forge state must survive storage centralization. CLI/Web share complete use cases; move orchestration upward rather than coordinating business behavior through mutual asset/scoring imports.

## Reference and lifecycle

The 283 frozen files and old HTML retain their original bytes; the 21 local/bootstrap mirror pairs have distribution consumers. R6 first integrates through versioned adaptation and new task snapshots, without editing frozen source in place or switching engines for in-flight tasks. Reuse DevelopmentRuntime, DevelopmentAdapter, and the training ClusterAdapter; do not add a competing scheduler or a giant Backend covering all domains.

Retain the actual framework hooks of Executor/mini environment. POSIX process groups, the dedicated stage_driver subreaper, Windows Job, and research fetch monitoring each implement their real lifecycle; a Job is not access isolation. Research/cancellation intent differs from termination confirmation; unknown submission requires reconciliation, without automatic resubmission as a fallback.

Training prepare does not start execution; the control worker only queues, and run-local requires operator confirmation of the manifest SHA. If F9 adds an automatic runner, execution authorization/lifecycle requires separate acceptance; the existing worker cannot be described as already supporting it. Rollback follows normal per-node commits and corresponding data backups; code revert cannot replace a database downgrade that has already occurred.
