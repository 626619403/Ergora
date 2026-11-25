# Ergora documentation

English · [简体中文](README.zh-CN.md) · [Project README](../README.md)

Choose the task you are performing. English is the primary current documentation; explicitly labelled Chinese links select translations or frozen source material. The [current plan](PLAN.md) separates delivered behavior from work awaiting implementation or acceptance. Pin the complete source commit when reproducing a result.

## Install and operate

|Task|Guide|
|---|---|
|Install the control plane and prepare offline wheels|[Linux/WSL2](install/linux.md) · [Windows/PowerShell](install/windows.md)|
|Set up backend login, tools and effective bindings|[Agent configuration](agents/configuration.md)|
|Register repository, tracker, roles and trusted checks|[Project registration](projects/registration.md)|
|Upgrade or rebuild while retaining persistent data|[Upgrades](install/upgrades.md)|
|Use local pages and edit work-unit drafts|[Console](operations/console.md)|
|Diagnose, start, stop and recover selected services|[Services](operations/services.md)|
|Create a coordinated offline recovery point|[Backup and recovery](operations/backup-recovery.md)|

Installation does not authenticate an Agent, start services or authorize a task. Control-home backups do not include execution data stored elsewhere.

## Run a formal development task

Follow [template journeys](development/templates.md) for governance, large changes and refactoring, then use the relevant operation:

1. [Prepare its composition, budget and context](development/preparation.md) for the selected recipe.
2. [Preview and create the task](development/tasks.md) from those exact inputs.
3. [Submit and observe the original run](development/run-and-recover.md).
4. When it awaits approval, [read design material and approve the exact plan](development/design-and-approval.md).
5. [Read original evidence, verify a handoff and export the exact candidate](development/evidence-and-export.md).

[Issue context](projects/issues.md) freezes explicit source observations. [Candidate actions](projects/candidate-actions.md) cover original-candidate observations, explicit comments/labels and existing PR/MR associations. These do not merge or approve remote changes.

## Define Agents and workflows

|Task|Guide|
|---|---|
|Select a backend and inspect actual role/mode support|[Backend selection](agents/backends.md)|
|Use an optional native integration|[DeepSeek Harness](agents/deepseek-harness.md) · [formal six-stage bridge](agents/formal-execution.md) · [ForgeKernel](agents/forgekernel.md)|
|Create or derive immutable specialist definitions|[Agent definitions](definitions/agents.md)|
|Revise/read complete resources and attachments|[Shared definition resources](definitions/resources.md)|
|Import, compose, preview and freeze a workflow|[Composition](definitions/workflows/compose.md)|
|Understand data ports, work units and review responsibilities|[Workflow contracts](definitions/workflows/contracts.md)|
|Check ancestor resources, permissions and static budgets|[Inheritance and permissions](definitions/workflows/permissions.md)|
|Publish exact new versions and share dependencies|[Workflow revisions](definitions/workflows/revisions.md)|
|Explicitly invoke/inspect one supported leaf and fixed MCP resources|[Leaf calls](definitions/workflows/leaf-calls.md)|

A static preview or installed preset does not execute a graph. Per-binding reasoning fields request a supported level; they do not establish the level actually used.

## Review and explain original evidence

Start with [exact local/PR/MR material](review/materials.md), then [invoke and aggregate frozen reviewers](review/invoke-and-aggregate.md). [Training code review](review/training.md) selects pretraining/posttraining specialists. [Evidence reports](review/evidence-reports.md) turn original materials into readable Markdown/HTML with explicit coverage limits.

## Train and measure

Start with the [training overview and CPU contract demo](training/overview.md). Continue to [experiment preparation](training/prepare-experiments.md), [original execution and recovery](training/execution.md), [finite controller authorization](training/controllers.md), or [evidence/rounds/exact approval](training/evidence-and-approval.md). Verify an unsuccessful experiment’s saved local archive through the [retained archive reader](training/evidence-and-approval.md#read-a-retained-local-archive-after-unsuccessful-execution).

[Expert proposals](training/proposals.md) map source flow and bottleneck analysis into experiment contracts; [optimization specialists](training/specialists.md) select a focused direction. Proposal leaves and synthetic CPU checks do not certify real GPU quality or performance.

## Improve the next task

Use the campaign guide to save an exact local operator plan, stop it through the Worker on its original queue, or observe an authorized fixed check. When Workflow state is unavailable, online status can verify saved observation receipts and a passing opt-in Activity completion from original Temporal History. [Campaign operator guide](improvement/campaigns.md) · [Stop the original campaign](improvement/campaigns.md#stop-the-original-campaign-plan) · [Timed readback](improvement/campaigns.md#allow-one-timed-readback-of-a-waiting-check)

The [improvement workflow](improvement/workflow.md) connects [source-bound retrospective candidates](improvement/retrospectives.md), [project memory and optional ReMe](improvement/memory.md), [trusted Skill evaluation/adoption](improvement/skills-and-evaluation.md), and [bounded research/scheduling](improvement/research-and-schedules.md). Generation, evaluation, adoption and a new task's frozen context are separate operations.

## Understand and change the implementation

Start with the [whole-framework implementation tour](architecture/framework-tour.md), then read the [architecture overview](architecture/current.md), [source ownership map](architecture/module-map.md), [component change protocols](architecture/component-change-protocols.md) and [domain glossary](../CONTEXT.md).

|Reference|Purpose|
|---|---|
|[Structured formats](architecture/contracts/formats.md) · [content identities](architecture/contracts/identities.md)|Versioned records and distinct encoding/digest contracts|
|[Development execution](architecture/execution/development.md) · [training execution](architecture/execution/training.md)|Original state, budgets, recovery and process ownership|
|[CLI/HTTP/console](architecture/interfaces.md)|Transport and asynchronous view ownership|
|[Native reference access](architecture/reference-boundary.md)|Fixed source, native processes and migration responsibilities|
|[Database migration](architecture/state-migrations.md) · [testing](architecture/testing.md)|Persistent data recovery and evidence-aware checks|
|[Architecture decisions](architecture/decisions/)|Dated decisions, with current owners linked separately|

Follow root [cooperation rules](../AGENTS.md) and the active [plan](PLAN.md) before repository changes. The [editor comparison](../examples/editor-comparison/README.md) is an independent prototype. The [frozen v2.2 distribution (Chinese)](distribution/multi-agent-development-platform.html) and packaged reference manuals retain their original scope; they are source artifacts, not translated current guides.

[Third-party notices](../THIRD_PARTY_NOTICES.md)
