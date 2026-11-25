# Source modules and ownership

English · [Documentation](../README.md)

Use this map to find the implementation that owns a change. Read its directory `AGENTS.md` and the [component change protocol](component-change-protocols.md) before editing. The [architecture overview](current.md) explains the product contract; [development](execution/development.md) and [training execution](execution/training.md) describe their original state and recovery obligations.

## Modules and dependencies

The package groups existing owners by responsibility. Package initializers provide no forwarding exports or SDK initialization. Python entry points remain `ergora.__init__` and `ergora.__main__`; the standard-library `_paths` owner resolves the single packaged data tree.

```text
src/ergora/
  _paths.py
  configuration/       catalog, bindings, projects, registrations, validation
  storage/             SQLite, immutable assets, complete local Git objects
  agents/              standalone graphs, runs and sessions, backend invocation, MCP
  definitions/         Agent/Workflow packages, bundles, Skill assets
  issues/              identity, backends, observations, use cases, writebacks
  development/         task contracts, context, review material, native client
    runtime/           original six-stage process owners
    review/            exact packets, external PR/MR sources, review inputs
  training/            materials, configuration, protocol, rounds/cycles/search
    runtime/           original experiment and controller process owners
  campaigns/           local operator plan, original Temporal run and receipts
  improvement/         memory, evaluation, optimization, research, retrospectives
  runtime/             process/reaper, budget clock, local GPU ownership
  native/              resources, compiler, registration, files, history, commands
  operations/          diagnostics, backups, selected service control
  interfaces/          CLI and HTTP/console transport
  data/                one existing schema/preset/console/reference tree
```

|Responsibility|Actual owners and consumers|
|---|---|
|Configuration|[catalog](../../src/ergora/configuration/catalog.py), [bindings](../../src/ergora/configuration/bindings.py), [projects](../../src/ergora/configuration/projects.py), [registrations](../../src/ergora/configuration/registrations.py), [validation](../../src/ergora/configuration/validation.py). Domain use cases consume normalized configuration and project revisions; metadata does not implement a backend.|
|Durable storage|[State](../../src/ergora/storage/state.py), [asset trees](../../src/ergora/storage/assets.py), [bounded Git material](../../src/ergora/storage/git.py). Definitions, review collection, backups and runtime evidence reuse these existing owners.|
|Agents|[standalone graphs](../../src/ergora/agents/graphs.py), [backend contract/factory](../../src/ergora/agents/backends.py), [invocation](../../src/ergora/agents/invocation.py), [runs/sessions](../../src/ergora/agents/runs.py), [original source readers](../../src/ergora/agents/native_sources.py), [fixed MCP](../../src/ergora/agents/mcp.py), [stage entry](../../src/ergora/agents/stage_driver.py). Standalone graphs dispatch through the same leaf-run owner as independent calls.|
|Definitions|[Agent admission](../../src/ergora/definitions/agents.py), [Workflow compilation](../../src/ergora/definitions/workflows.py), [complete bundles](../../src/ergora/definitions/bundles.py), [Skill assets](../../src/ergora/definitions/skills.py). Agent calls, task preparation and review consume exact immutable versions.|
|Issue sources|[identity](../../src/ergora/issues/identity.py), [backend contract/factory](../../src/ergora/issues/backends.py), [snapshots](../../src/ergora/issues/snapshots.py), [use cases](../../src/ergora/issues/application.py), [writebacks](../../src/ergora/issues/writebacks.py). Native observations, local context and external attempts retain distinct records.|
|Development|[task use cases](../../src/ergora/development/application.py), [envelopes](../../src/ergora/development/envelopes.py), [input interfaces](../../src/ergora/development/inputs.py), [context](../../src/ergora/development/context.py), [native client](../../src/ergora/development/native.py), [runtime](../../src/ergora/development/runtime), [review material](../../src/ergora/development/review). These own task preparation, original operations and candidate-bound evidence.|
|Training|[use cases](../../src/ergora/training/application.py), [materials](../../src/ergora/training/materials.py), [saved execution protocol](../../src/ergora/training/execution_protocol.py), [native client](../../src/ergora/training/native.py), [rounds](../../src/ergora/training/rounds.py), [cycles](../../src/ergora/training/cycles.py), [runtime](../../src/ergora/training/runtime). [Retained archive readback](../training/evidence-and-approval.md#read-a-retained-local-archive-after-unsuccessful-execution) verifies saved evidence after an unsuccessful execution. Exact acceptance uses the original accepted archive.|
|Campaign operator records|[Use cases](../../src/ergora/campaigns/application.py), [local records](../../src/ergora/campaigns/records.py), [Temporal Workflow](../../src/ergora/campaigns/workflow.py) and [guarded reader](../../src/ergora/campaigns/readback.py). The Workflow owns task readiness, receipts, the original deadline and opt-in readback scheduling. The guarded reader reads the original fixed-check Job status. Online status verifies saved observation Updates and the recorded Activity completion through original History when Workflow state is unavailable. [Campaign guide](../improvement/campaigns.md)|
|Improvement|[memory](../../src/ergora/improvement/memory.py), [evaluation](../../src/ergora/improvement/evaluation.py), [Skill adoption](../../src/ergora/improvement/skill_adoption.py), [retrospectives](../../src/ergora/improvement/retrospectives.py), [project-document corrections](../../src/ergora/improvement/document_corrections.py), [optimization](../../src/ergora/improvement/optimization.py), [research](../../src/ergora/improvement/research.py), [scheduling](../../src/ergora/improvement/scheduling.py), [kernel campaigns](../../src/ergora/improvement/kernel.py). Each owns its actual selection, availability and lifecycle.|
|Live resources|[processes/reaper](../../src/ergora/runtime/processes.py), [Windows jobs](../../src/ergora/runtime/windows_job.py), [budget clock](../../src/ergora/runtime/budget_clock.py), [GPU pool](../../src/ergora/runtime/gpu_pool.py), [guardian](../../src/ergora/runtime/gpu_guard.py). Domain execution owners reuse these resources without taking over another owner's work.|
|Native integration|[resources](../../src/ergora/native/resources.py), [compiler](../../src/ergora/native/compiler.py), [registration projection](../../src/ergora/native/registration.py), [bounded files](../../src/ergora/native/files.py), [history](../../src/ergora/native/history.py), [worker commands](../../src/ergora/native/commands.py). Task/training clients remain with their domains.|
|Operations|[tools/doctor](../../src/ergora/operations/tools.py), [backups](../../src/ergora/operations/backups.py), [services](../../src/ergora/operations/services.py) compose existing domain owners.|
|Transport|[CLI](../../src/ergora/interfaces/cli.py) and [HTTP](../../src/ergora/interfaces/web.py) parse transport input and call the same use cases. Console assets remain under `data/console`.|

The acyclic constraint applies to the fully qualified **module** graph. A package can contain both leaf contracts and use cases, so the package names alone are not a dependency-layer ordering. Domain modules do not import CLI/HTTP implementations. Static checks traverse first-party modules recursively and exclude packaged data from the import graph. Current resource identity is verified separately; integration import sites inside the packaged reference follow their actual current manifest.

## Invocation and data ownership

Transport parses input; domain use cases own identity, permission, revision and lifecycle decisions. A page does not become a second scheduler or state machine. The console's [asynchronous view contract](interfaces.md) keeps project, control directory and selection generation attached to each response.

Formal development goes through `development.application` → `development.native` → the selected dedicated operation process and original Temporal workflow. [Execution details](execution/development.md) cover complete materials, preparation, one budget and the sole finalizer. Work/review data comes from declared producers and original receipts; a dependency edge grants no extra resource access.

### Graphs, independent calls, improvement and training

`agents.graphs` schedules dependency-ready Agent leaves within the frozen concurrency limits and publishes the standalone graph's operation record. `agents.runs` owns original leaf runs and native session continuations. `agents.invocation` owns backend invocation and results. `agents.native_sources` reads original bounded records and retains native packet serialization for the runner and document-correction owner. Definitions supply complete frozen ancestor resources through the admitted mode. [Standalone graph execution](../definitions/workflows/compose.md#run-a-standalone-workflow-graph) · [Execution routes and continuation receipts](framework-tour.md#definitions-and-execution-routes)

Improvement generation, trusted evaluation, adoption/rollback and new-task material freezing are separate use cases. `training.application` uses its own native client and original runtime processes; an evidence index or proposal neither launches an experiment nor advances a baseline. Read [training execution](execution/training.md) before changing its authorization, clock, stop or recovery behavior.

## Agent backend integration

Extend `AgentBackend` through `agents.backends._BACKENDS` and `for_binding`; keep backend-specific configuration, initialization and actual modes in that implementation. Invocation, task scheduling and transport call the shared interface. `IssueBackend` owns its own factory and native platform protocol. Similar names across these families do not create one universal plugin registry.

GEPA, ReMe, research scheduling and kernel tools retain their real domain integration points. Report declarations, installation, native identity, authentication, supported operations and actual execution separately. Optional capabilities fail visibly when unavailable; adding metadata does not implement them.

## Configuration, data and evidence ownership

|Persisted material|Authority|
|---|---|
|Projects, memory revisions, evaluation and local records|State connections plus the owning domain transaction; [migration rules](state-migrations.md) remain explicit.|
|Agent/Workflow/Skill objects and indexes|The existing definition library and [complete ordinary-file resource contract](../definitions/resources.md); exact content identities include original bytes and executable bits.|
|Registration intent, publication and recovery|`configuration.registrations` plus `native.registration`; the control record does not replace external configuration/state backups.|
|Task runs, approvals, candidates, claims and external jobs|Original development operation, Temporal, executor and evidence owners; [task recovery](../development/run-and-recover.md) retains original IDs and unknown results.|
|Training source, manifests, baseline/runner, execution and archives|Training material/protocol and per-operation runtime owners; [exact evidence approval](../training/evidence-and-approval.md) is separate from execution and measurement acceptance.|
|Process lifetime and budgets|Original domain owner plus shared process/clock resources; descendant stopping and cleanup are observed separately from signal delivery.|

Python relocation does not rename SQLite tables, stored directories, schema IDs, activity/queue names, artifact names or existing evidence keys. Distinct [digest contracts](contracts/identities.md) remain distinct. Historical observations keep their actual identity; changed code does not inherit an older candidate's checks or restart an original budget.

## Change impacts and integration

Follow the actual configuration → construction → invocation → result → recovery path before editing. Keep interchangeable implementations behind their family's existing interface; introduce a new seam only for real variation. Domain input/identity validation remains with its owner, not a duplicated guard in the UI or scheduler.

Changing a target training framework's model, optimizer, dataset or forward function requires that project's own directory protocol and authorization. Ergora's proposal templates do not own those implementations. [Component protocols](component-change-protocols.md) identify data, gradient, parallelism, resource and recovery obligations to inspect.

## Native reference responsibilities

The bundled reference remains the implementation of the existing formal runtime. `native.resources`, `native.compiler`, `native.registration`, `native.files`, `native.history` and `native.commands` own their integration responsibilities; task and training operations use `development.native` and `training.native`. There is no root `reference.py` facade or old-module reexport.

Dedicated native processes preserve each selected installation's ROOT/CONFIG/STATE and original import precedence. Ordinary HTTP/CLI imports do not initialize a selected native platform or optional SDK loop. [Reference access](reference-boundary.md) explains the exact process and reader responsibilities; source refactoring alone does not upgrade a registered installation or certify live recovery.
