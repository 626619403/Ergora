# Ergora documentation

English · [简体中文](README.zh-CN.md) · [Project README](../README.md)

Start with the [project overview and quick start](../README.md#quick-start), then choose a guide below. Current feature guidance follows `refactor/architecture-foundations`; the default `main` branch and frozen v2.2 reference distribution have different scopes. Pin the full source commit when reproducing a recorded result.

English is the default for completed language pairs. The table explicitly marks guides still written in Chinese while their complete English counterparts are prepared under the [bilingual maintenance plan](plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md). Existing guide paths remain stable. An English counterpart must preserve the complete commands, limits and recovery behavior before its row is marked bilingual.

## Install and operate

|Guide|Use it for|Language status|
|---|---|---|
|[Installation and daily use](USAGE.md)|Installation profiles/offline wheels, Agent authentication, formal task operations, issue sources, services and recovery|Chinese; full pair queued in batch 2|
|[Windows](WINDOWS.md)|Native control plane, PowerShell installation, handoff verification and WSL2 execution boundaries|[English](WINDOWS.md) / [中文](zh-CN/WINDOWS.md)|
|[Projects](PROJECTS.md)|Unified registration, revisions, effective bindings and explicit adoption of a reference registration|[English](PROJECTS.md) / [中文](zh-CN/PROJECTS.md)|
|[Backup and recovery](BACKUP_RECOVERY.md) · [中文](zh-CN/BACKUP_RECOVERY.md)|Coordinated offline control/execution/Temporal/Git snapshots and same-path restoration|English and Chinese|
|[Testing](TESTING.md) · [中文](zh-CN/TESTING.md)|Installed-wheel checks, CI selection, collection coverage and original failure logs|English and Chinese|

Control-plane installation does not start services, authenticate a model or enable the trusted reference executor. A control-home backup does not include execution data stored elsewhere. Keep credentials and local runtime data outside public documents.

## Define Agents and workflows

|Guide|Use it for|Language status|
|---|---|---|
|[Template walkthroughs](TEMPLATE_WALKTHROUGHS.md)|Complete governance/refactoring/training-proposal journeys and manifests|Chinese; full pair queued in batch 3|
|[Agent definitions](AGENT_DEFINITIONS.md)|Independent specialist definitions, resources and immutable versions|Chinese; full pair queued in batch 3|
|[Agent backends](AGENT_BACKENDS.md)|Actual role/mode support, backend configuration, formal execution and session recovery|Chinese; full pair queued in batch 3|
|[Workflow definitions](WORKFLOW_DEFINITIONS.md)|Nested references, resource inheritance, permissions, graph compilation, manifests and explicit leaf calls|Chinese; full pair queued in batch 3|

A valid definition, preset installation or preview does not execute a graph. Formal development retains the supported six-stage runtime. Per-binding reasoning settings request a level supported by the selected backend/model; they do not prove the model used that level. Automatic task-based level selection remains planned.

## Review, train, report and improve

|Guide|Use it for|Language status|
|---|---|---|
|[Local review](LOCAL_REVIEW.md)|Exact Git/requirements/context packets, offline verification and explicit source collection|Chinese; full pair queued in batch 4|
|[Pretraining and posttraining review](TRAINING_REVIEW.md)|Domain reviewers and CPU contract examples|Chinese; full pair queued in batch 4|
|[Training](TRAINING.md)|Workloads/baselines/runners, experiments, evidence, approval, managed execution and optimization proposals|Chinese; full pair queued in batch 4|
|[Improvement workflow](IMPROVEMENT_WORKFLOW.md)|Source-bound memory/Skill/Workflow candidates, evaluation, explicit adoption and next-task freeze|Chinese; full pair queued in batch 4|
|[Integrations](INTEGRATIONS.md)|Tool bindings, memory projections, GEPA, bounded research and scheduling|Chinese; full pair queued in batch 4|
|[Evidence reports](EVIDENCE_REPORTS.md) · [中文](zh-CN/EVIDENCE_REPORTS.md)|A read-only report author, original source/coverage records and self-contained HTML exports|English and Chinese|

Training proposals and evidence indexes do not authorize experiments or establish GPU quality/performance. New versioned training-cycle schema3 controller effects remain disabled; future loop/gate/Repeat work is tracked in the live plan. External issue comments/labels, candidate adoption and publication retain their own explicit action/approval paths.

## Understand and extend the implementation

These living guides remain in Chinese and are assigned complete language pairs in batch 5. Dated inventories inside them establish only the recorded source revision; consult the live plan and original deliveries for later changes.

|Guide|Owner and purpose|
|---|---|
|[Current architecture](architecture/current.md)|Module/caller/data boundaries and supported extension points|
|[Component change protocols](architecture/component-change-protocols.md)|Construction/configuration, ownership, lifecycle, recovery and relevant verification before changing a component|
|[Contracts and identities](architecture/contracts-and-identities.md)|Versioned schemas, complete resource identities and distinct digest contracts|
|[Reference boundary](architecture/reference-boundary.md)|Frozen runtime access and gradual migration responsibilities|
|[State migrations](architecture/state-migrations.md)|Database compatibility, backups and rollback|
|[Domain glossary](../CONTEXT.md)|Project terminology and original domain owners|

Read the root [cooperation rules](../AGENTS.md) and current plan before changing repository code. The [editor comparison example](../examples/editor-comparison/README.md) is a separate design experiment with its own build requirements. Frozen preset/reference instructions and third-party materials are product/source artifacts, not targets for blanket documentation translation.

## Current work and historical evidence

|Record|How to interpret it|
|---|---|
|[Live plan](PLAN.md)|Current checkpoint, active candidates, owner decisions and remaining acceptance; currently Chinese|
|[Implementation plans](plans/)|Dated scope and acceptance criteria; planned capability is not implemented support|
|[Delivery records](delivery/)|Original candidate-bound checks, review findings, failures, corrections and unverified scope; supporting files are under [delivery/evidence](delivery/evidence/)|
|[Research](research/)|Dated source comparisons, design evidence and adoption recommendations; not product acceptance|
|[Architecture decisions](architecture/decisions/)|Recorded decisions and their original context|
|[Frozen reference HTML](distribution/multi-agent-development-platform.html)|Self-contained v2.2 Linux distribution with its original embedded deployment/training manuals|

Historical checkpoint archives: [November 9](PLAN-history-2026-11-09.md), [10](PLAN-history-2026-11-10.md), [14](PLAN-history-2026-11-14.md), [15](PLAN-history-2026-11-15.md), [16](PLAN-history-2026-11-16.md). “Current”, “pending” and “in progress” in these files refer to the date and candidate recorded there.

Earlier architecture evidence remains at its original paths: [November 1 baseline](architecture/2026-11-01-baseline.md), [audit](architecture/2026-11-01-audit.md), [compatibility](architecture/2026-11-01-compatibility.md), [November 2 runtime contracts](architecture/2026-11-02-runtime-contracts.md), [November 11 architecture history](architecture/current-history-2026-11-11.md), and [November 14 Harness seam](architecture/2026-11-14-harness-session-seam.md)/[continuation alternatives](architecture/2026-11-14-harness-continuation-options.md).

Historical records keep their original language, results and source identities. The bilingual cleanup adds navigation first, then topic/candidate indexes in its planned historical batch; it does not delete or silently rewrite evidence. New HTML reading views are optional, must remain self-contained and must link to the preserved original sources.

[Language migration plan](plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md) · [Batch delivery and branch cleanup](delivery/2026-11-16-bilingual-documentation-and-branch-cleanup.md) · [Third-party notices](../THIRD_PARTY_NOTICES.md)
