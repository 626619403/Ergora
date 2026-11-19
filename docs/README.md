# Ergora documentation

English · [简体中文](README.zh-CN.md) · [Project README](../README.md)

Start with the [project overview and quick start](../README.md#quick-start), then choose a guide below. Current feature guidance follows `main`; the frozen v2.2 reference distribution retains its documented scope. Pin the full source commit when reproducing a recorded result.

English is the default for completed language pairs. The table identifies each guide's available language; current commands and recovery obligations remain owned by the linked guides.

## Install and operate

|Guide|Use it for|Language status|
|---|---|---|
|[Installation and daily use](USAGE.md)|Installation profiles/offline wheels, Agent authentication, formal task operations, issue sources, services and recovery|[English](USAGE.md) / [中文](zh-CN/USAGE.md)|
|[Windows](WINDOWS.md)|Native control plane, PowerShell installation, handoff verification and WSL2 execution boundaries|[English](WINDOWS.md) / [中文](zh-CN/WINDOWS.md)|
|[Projects](PROJECTS.md)|Unified registration, revisions, effective bindings and explicit adoption of a reference registration|[English](PROJECTS.md) / [中文](zh-CN/PROJECTS.md)|
|[Backup and recovery](BACKUP_RECOVERY.md) · [中文](zh-CN/BACKUP_RECOVERY.md)|Coordinated offline control/execution/Temporal/Git snapshots and same-path restoration|English and Chinese|
|[Testing](TESTING.md) · [中文](zh-CN/TESTING.md)|Installed-wheel checks, CI selection, collection coverage and original failure logs|English and Chinese|

Control-plane installation does not start services, authenticate a model or enable the trusted reference executor. A control-home backup does not include execution data stored elsewhere. Keep credentials and local runtime data outside public documents.

## Define Agents and workflows

|Guide|Use it for|Language status|
|---|---|---|
|[Template walkthroughs](TEMPLATE_WALKTHROUGHS.md)|Complete governance/refactoring/training-proposal journeys and manifests|[English](TEMPLATE_WALKTHROUGHS.md) / [中文](zh-CN/TEMPLATE_WALKTHROUGHS.md)|
|[Agent definitions](AGENT_DEFINITIONS.md)|Independent specialist definitions, resources and immutable versions|[English](AGENT_DEFINITIONS.md) / [中文](zh-CN/AGENT_DEFINITIONS.md)|
|[Agent backends](AGENT_BACKENDS.md)|Actual role/mode support, backend configuration, formal execution and session recovery|[English](AGENT_BACKENDS.md) / [中文](zh-CN/AGENT_BACKENDS.md)|
|[Workflow definitions](WORKFLOW_DEFINITIONS.md)|Nested references, resource inheritance, permissions, graph compilation, manifests and explicit leaf calls|[English](WORKFLOW_DEFINITIONS.md) / [中文](zh-CN/WORKFLOW_DEFINITIONS.md)|

A valid definition, preset installation or preview does not execute a graph. Formal development retains the supported six-stage runtime. Per-binding reasoning settings request a level supported by the selected backend/model; they do not prove the model used that level. Automatic task-based level selection remains planned.

## Review, train, report and improve

|Guide|Use it for|Language status|
|---|---|---|
|[Local review](LOCAL_REVIEW.md)|Exact Git/requirements/context packets, offline verification and explicit source collection|Chinese|
|[Pretraining and posttraining review](TRAINING_REVIEW.md)|Domain reviewers and CPU contract examples|Chinese|
|[Training](TRAINING.md)|Workloads/baselines/runners, experiments, evidence, approval, managed execution and optimization proposals|Chinese|
|[Improvement workflow](IMPROVEMENT_WORKFLOW.md)|Source-bound memory/Skill/Workflow candidates, evaluation, explicit adoption and next-task freeze|Chinese|
|[Integrations](INTEGRATIONS.md)|Tool bindings, memory projections, GEPA, bounded research and scheduling|Chinese|
|[Evidence reports](EVIDENCE_REPORTS.md) · [中文](zh-CN/EVIDENCE_REPORTS.md)|A read-only report author, original source/coverage records and self-contained HTML exports|English and Chinese|

Training proposals and evidence indexes do not authorize experiments or establish GPU quality/performance. Explicitly authorized training controllers execute a finite frozen candidate selection under one original budget; adaptive search, design gates and general Repeat remain tracked in the live plan. External issue comments/labels, candidate adoption and publication retain their own explicit action/approval paths.

## Understand and extend the implementation

These architecture guides describe the current semantic owners and contracts. The live plan records current validation and remaining work.

|Guide|Owner and purpose|
|---|---|
|[Current architecture](architecture/current.md)|Module/caller/data boundaries and supported extension points|
|[Component change protocols](architecture/component-change-protocols.md)|Construction/configuration, ownership, lifecycle, recovery and relevant verification before changing a component|
|[Contracts and identities](architecture/contracts-and-identities.md)|Versioned schemas, complete resource identities and distinct digest contracts|
|[Reference boundary](architecture/reference-boundary.md)|Frozen runtime access and gradual migration responsibilities|
|[State migrations](architecture/state-migrations.md)|Database compatibility, backups and rollback|
|[Domain glossary](../CONTEXT.md)|Project terminology and original domain owners|

Read the root [cooperation rules](../AGENTS.md) and current plan before changing repository code. The [editor comparison example](../examples/editor-comparison/README.md) is a separate design experiment with its own build requirements. Frozen preset/reference instructions and third-party materials are product/source artifacts, not targets for blanket documentation translation.

## Current work

The [current plan](PLAN.md) and [active delivery](delivery/2026-11-19-main-branch-integration.md) record current checks and remaining work. [Architecture decisions](architecture/decisions/) retain their dated design context. The [frozen reference HTML](distribution/multi-agent-development-platform.html) remains the self-contained v2.2 Linux distribution with its own original deployment and training manuals.

[Third-party notices](../THIRD_PARTY_NOTICES.md)
