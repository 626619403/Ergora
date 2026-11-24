# Formal development execution and recovery

English · [Documentation](../../README.md)

This page describes the actual current execution owners. The [supported definition/input sets and limits](../contracts/formats.md#supported-task-routes-and-material-limits) are authoritative; current prepared recipes use definition8/Input12. Supported earlier inputs retain their own original behavior and identity. Removed8–11 inputs have no current execution route, and old records are not upgraded by changing a label.

## Formal development path

`development.application` prepares and creates exact inputs through dedicated native operations; `development.inputs.PreparationDAGInput` selects `PreparationDAGWorkflow` and its adapter/activities. Current development presets freeze preparation/work/review graphs under one native six-stage instance. This retains inventory → plan → work → integrate → verify → review, original trusted checks, exact-plan approval and candidate-bound independent reviews.

```mermaid
flowchart LR
  Definitions[exact definitions / ancestor resources / explicit grant] --> Prepare[original budgeted preparation]
  Prepare --> Creation[preview / dual-digest creation / Input12]
  Creation --> Submission[original task and run submission]
  Submission --> Inventory[inventory experts and coordinator]
  Inventory --> Plan[plan experts and coordinator]
  Plan --> Approval[original owner approves exact plan]
  Approval --> Work[original work units / dependency integration]
  Work --> Verify[trusted integrate and verify]
  Verify --> Review[required and advisory candidate-bound review]
  Review --> Outcome[original outcome / evidence / explicit export]
```

Structural inheritance supplies all ancestor resources; control dependencies order work; named ports carry declared producer outputs. Work-unit paths/dependencies, complete leaf coverage, explicit all-joins and required/advisory review duties are checked through the original DAG and envelope owners. A static graph does not authorize arbitrary roles, generalized Repeat or another scheduler. Exact issue sources remain context and do not grant execution permissions.

## Execution materials and recovery

`development.runtime.executor` binds stage requests, original jobs, claims, receipts, invocations and exact Git baseline/candidate objects. Material v2/`stage-artifacts-v1` passes complete declared artifacts, trusted checks and opinions without recursively copying predecessor prompts. Current12 retains complete selected structural resources and preparation expert results. Required Skill attachments must have continuous actual MCP read coverage; inline complete bodies need no duplicate read.

`agents.runs` owns invocation records, and `agents.mcp` delivers only fixed declared resources. Backend loading/capability requests, resource delivery and actual model reading/quality remain distinct facts. Capacity is checked using the original contract's [scoped limits](../contracts/formats.md#supported-task-routes-and-material-limits); no complete material is silently truncated. Current bindings, clocks or active library heads do not replace saved task selections during recovery.

External actions retain attempt-before-send. A lost reply remains unknown until the original ID/history/receipt is reconciled; a restart creates no new authorization. Cancellation delivery, local fences, process stopping, terminal outcomes and applicable lease release are separate observations. [Operational recovery](../../development/run-and-recover.md) and [evidence/export](../../development/evidence-and-export.md) use the original records.

## Complete preparation materials

Definition8 freezes the actual inventory and plan DAGs, explicit coordinators, every selected leaf/backend/mode, source paths and complete graph coverage. `development.envelopes` owns pure frozen reads; current input12 uses its own queue/request namespace through `PreparationDAGInput`. Preparation branches are scheduled by the original Workflow rather than a separate generic graph runtime.

Inventory/plan use exact starting Git objects and required ancestor instructions. Coordinators receive complete verified expert-results, and plan input binds the original inventory artifacts. Handoff checks retain original request, receipt, claim, invocation and artifact identities. Static completeness is not proof of understanding or business acceptance. See [preparation contracts](../../definitions/workflows/contracts.md#complete-inventory-and-planning-materials).

## Shared end-to-end budget

`development.budget` owns standard-library policy/instance/known-slot contracts. The first prepare saves authorization and a unique attempt before installation/material work; original supervised workers compile and collect within the same deadline, reap their owned trees and clean scratch before publishing results/witnesses. Preview reads those frozen results; creation confirms prepare and preview SHAs. Recovery does not compile again, renew the clock or refund a consumed slot.

Current12's dispatch/start methods check original remaining time and bound RPC timeout; `BudgetedJob` and `development.runtime.jobs` retain original owner, slot and finalization checks. Waiting, retries, model work, collection and cleanup share the nonrenewable budget. Reservations are not proof of provider spending. Original OWNED jobs retain occupancy across restarts; receipt/ledger uncertainty requires reconciliation. Terminal publication requires actual owned-process stopping and complete collection/budget checks, with one reaper/finalizer.

## Single-instance native six stages

`development.six_stage` checks one explicitly selected native instance, at the root or within a supported parent, with exact structural ancestors and work/review selections. `PreparationDAGWorkflow` retains that selection as a read-only `native_invocation` projection. Its original run also owns approval and receipts. Extra instances, external prerequisites or unsupported mixed shapes fail original preparation. See [native selection](../../development/preparation.md#invoke-the-six-stages-as-a-subtemplate).

## Explicit project sources

The current definition8 can select exact valid memory revisions and active Skill head revision/digest. `development.context` derives a same-id new root only in original supervised scratch, using the existing definition library, complete resources, permissions and capacity checks. Before first intent, original reservation/publication locking checks canonical sources; drift rejects the selection. `development.envelopes.selected_context` verifies saved selection, root differences and complete attachments using standard-library code.

`PreparationDAGInput.stage_material` carries optional selected context through the original stage interface. Recovery uses archived source bytes; later expiry, corrections, deletion, rollback or library revisions do not silently swap in new materials. Context freezing adds no second memory/resource library, mutable state ledger or execution grant. [Explicit material selection](../../development/preparation.md#select-project-memories-and-active-skills-for-a-formal-task) explains the current operator steps.
