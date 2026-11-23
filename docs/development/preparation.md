# Prepare a task's frozen composition

English · [Documentation](../README.md) · [简体中文](../zh-CN/development/preparation.md)

## Freeze a review composition for a formal task

The original `schema_version: 1` continues to use four-role bindings and the complete six stages. The new `schema_version: 2` freezes the complete composition bundle and each member's backend, supporting preview, creation, publication recovery, start and original-run status queries. Formal review supports a single read-only reviewer or multiple nested read-only review branches joined through an explicit all-join. Each leaf's input must map directly to the root task through every structural ancestor, with no predecessor dependencies along the path. Other valid static compositions can still be saved and inspected, but unsupported shapes are explicitly rejected before submission. Use the worker and executor managed by this Ergora version; old runners do not support the new envelope.

First prepare a manifest according to the [complete composition bundle instructions](../definitions/workflows/compose.md#save-and-share-a-complete-composition), and use `verify-manifest` to obtain its `digest`. Change `schema_version` to 2 in the original task definition and add the following `composition` field, keeping the other inputs in the original template format:

```json
{
  "manifest": "/absolute/path/to/review-manifest",
  "manifest_digest": "REPLACE_WITH_THE_VERIFIED_DIGEST",
  "review_instance": "root",
  "mode": "task-mcp",
  "backend_overrides": {
    "root/review": {
      "binding": {"tool": "codex"},
      "reason": "Claude不可用，选择已配置的Codex/ChatGPT"
    }
  },
  "diversity": {
    "policy": "prefer-distinct",
    "reason": "当前只有Codex可用，接受执行和审查共享后端"
  }
}
```

This example is for the `structure-review` bundle; use the actual member paths for other bundles. `manifest` is a local path on the machine running the CLI or HTTP service; an absolute path is recommended. The initial supported shape accepts only a review-workflow subtree with one `task` input and no dependencies on unexecuted external nodes. All leaves must be read-only reviewers. `mode` can be `text-only` or `task-mcp`. Saving a capability contract does not prove that the CLI, authentication, SDK or services are available.

For parallel review by three specialties, first import the three specialists and four review workflows in the [example import order](../definitions/workflows/compose.md#run-the-example), then prepare the overall review bundle:

```bash
ergora composition prepare-manifest parallel-review 1.0.0 --grant examples/composition/preview-grant.json --directory ./parallel-review-manifest
ergora composition verify-manifest ./parallel-review-manifest
```

Use that directory and the returned digest in the task's `composition`; `review_instance` remains `root`. The member paths are `root/structure/review` (structure, Codex by default), `root/correctness/review` (correctness, Claude Code by default) and `root/test-value/review` (test/CI value, Codex by default). To override a backend, replace a `backend_overrides` key in the example above with the corresponding path. Multiple members can be overridden together. Each definition retains its own declared Skills and initial instructions and fully inherits materials from the root and its containing subtemplates.

The three reviewers inspect the same exact candidate, original validation report and approved plan, saving separate jobs, workspaces, invocations and receipts. Concurrency is constrained by the shared project and ancestor-template limits. Every branch in this example is a required review. Any request for changes, failure, timeout, missing review, or reuse of the author's or another review session prevents approval. After all pass, the original outcome's `review` is `composition-review-aggregate`, retaining each member's original stage/job/receipt digest. It is not an additional model or human approval. `task evidence` and handoff packets can still read these separate originals. After a worker restart, execution continues from the original history without redispatching the same published job. Cancellation and unknown external jobs still follow the original fence/reconciliation process.

For advisory review, import the [review-requirements example](../definitions/workflows/contracts.md#static-required-and-advisory-review-declarations), then prepare its complete bundle:

```bash
ergora composition prepare-manifest review-requirements 1.0.0 --grant examples/composition/preview-grant.json --directory ./review-requirements-manifest
ergora composition verify-manifest ./review-requirements-manifest
```

Continue using a `schema_version: 2` task definition, replacing the manifest and digest with these results. The member paths are `root/structure` (required) and `root/test-value` (advisory). Responsibilities are declared by node instances in WorkflowDefinition v2, with at least one required reviewer; backend overrides cannot change them. Old v1 review leaves in a mixed tree remain required. Creation saves a formal v3 envelope. This runtime protocol version is managed separately from the user task-definition and workflow-definition versions.

All branches must still finish and enter an explicit all-join. This new responsibility graph must declare a join even with only one reviewer; directly forwarding task or a leaf result as the output is unsupported for formal execution. Old v1 graphs retain their single-leaf behavior. An advisory member's valid `request-changes` retains its original `FAILED` receipt and findings. Trusted aggregation v2 records each member's `review_requirement`, `decision` and original receipt reference. The task reaches `REVIEW_READY` only when every required member approves and the other contracts are satisfied. An advisory member's process failure, candidate mismatch, missing evidence, session reuse, timeout or cancellation still blocks the task and follows the original fence/reconciliation process. Joining does not turn original opinions into approvals.

To run structure review first, followed by parallel correctness and test-value reviews, import [serial-review](../definitions/workflows/contracts.md#data-ports-for-formal-read-only-review), prepare its complete manifest, and add the following to `composition` in the same task definition:

```json
"review_protocol": "dag-v1"
```

Replace the manifest path and digest with these results. Member paths remain `root/structure/review`, `root/correctness/review` and `root/test-value/review`; use those paths for backend overrides too. This explicit selection is saved as a formal v4 envelope; old tasks without the field continue using their original v2/v3. Downstream nodes receive all original predecessor artifacts only after the predecessors finish, while independently ready branches are scheduled within ancestor limits. Configuring depends_on alone without port bindings does not automatically pass predecessor bodies. Skills, MCP and permissions from the three structural parent templates do not inherit across data arrows. The selected review subtree must have one task input and one terminal output, with an explicit all-join at the endpoint providing full transitive coverage. Nested multiple named outputs are supported; all leaves remain read-only reviewers.

Without overrides, the backend specified by the definition is used. Overrides select individual instance paths and record a reason. `prefer-distinct` is the default policy and requires `diversity.reason` when the backend matches the implementer's; `require-distinct` rejects matching backends outright, while `allow-same` permits them. Backend equality compares tool implementations; different tools do not imply independent model errors. Credentials continue to come from environment variables or protected local authentication and are not written into definitions.

Use the [preview/create commands and APIs](tasks.md#preview-and-create-formal-tasks), then follow the [formal task sequence](tasks.md#formal-task-sequence-and-recovery) with `task start/submission/resume-start/status/plan/approve`. The preview's `files.task.spec.json` is an explicitly versioned envelope whose `legacy_spec` retains the unchanged original six-stage projection. `composition.manifest` carries complete file bytes and executable bits. The envelope SHA also binds the static graph, ancestor materials, members, policies and diversity decisions. Removing the source manifest or changing the active library/project bindings after creation does not affect the saved original intent or publication recovery. `runtime_supported` means only that the current runtime bridge supports that static shape; it does not check authentication, models, SDK or service readiness and does not mean execution succeeded.

Composition tasks use separate composition-v2, composition-v3 or composition-v4 queues and request directories according to their formal envelope version. The original owners still handle the six stages, plan approval, candidate verification and receipts. Old workers cannot take over newer versions. During an upgrade, stop the old worker/executor and restart them through this version's `services`, preserving the original history and state directories. Each stage binds the complete original envelope. Status and recovery check the original Temporal input; the same legacy projection cannot substitute for a different manifest. Review invocations save the complete ancestor materials, original template instructions, approved plan and verification artifacts, together with base/candidate source and diff within the shared read scope of the task and leaf. Source, dependency digests, invocations and results all bind to the same candidate. The original monitor continues to own timeout and cancellation. Read-only tool configuration does not provide operating-system isolation. Cancellation of composition tasks also checks the complete original envelope and follows the same `cancel/cancellation/resume-cancel` and original-signal recovery. `requested` still denotes only delivery; external terminal states and leases are checked through the original `external-status/reconcile`, preserving the original outcome after cleanup.

Complete composition bundle exports still support 10 MB/500 files. Formal creation uses the [contract-specific wire/file/aggregate limits](../architecture/contracts/formats.md#supported-task-routes-and-material-limits), including base64 and complete bodies in the graph. Formal material contexts use their original input's [context limit](../architecture/contracts/formats.md#supported-task-routes-and-material-limits); standalone leaf preparation and static resource limits remain separate. Dynamic source, dependency bodies and all ancestor prompts count together, with explicit rejection above the limit. The save and backup scope remains the task's seven contracts, complete intent and result receipt in the registered execution-state directory. A control-database-only backup does not include them. Original v4 read-only DAGs and v5 work compositions inline all original predecessor artifacts in full, so long audit chains may still exceed the budget. `kernel-delivery` still supports only static preview; a manifest does not establish that all nodes have executed.

To assign implementation specialists to the original work units, followed by overall review, select `execution.protocol: work-units-v2` according to the [specialist executor configuration](../definitions/workflows/contracts.md#specialist-writers-and-original-work-units). The user task definition remains schema-v2 and the formal envelope is v6. The page's “Complete manifest · composition execution and review” uses this protocol. v6 passes declared stage artifacts, trusted checks and review comments in full. Execution audits stay in the original receipt/evidence/handoff and continue to be verified individually, avoiding recursive copying of old prompts downstream. Results are also retained for control dependencies without port bindings. Ancestor resources, approval, candidate identity and original recovery gates remain intact. Old `work-units-v1`/v5 tasks do not migrate automatically. New v6 queues require an upgraded worker/executor, and full execution still requires Linux/WSL2 and an explicitly trusted container.

## Select template Agents for inventory and planning

[Complete material configuration](../definitions/workflows/contracts.md#complete-inventory-and-planning-materials) uses current task-definition schema8/formal input12. Each preparation stage selects a workflow subtree plus canonical coordinator. Inventory members are readonly inspectors; plan members are readonly planners. Ready experts run within the original ancestor concurrency limits, and the canonical coordinator consumes complete original predecessor results. Every planner receives the original canonical inventory; only the inventory coordinator owns trusted baseline checks.

The current graphical wizard, CLI and HTTP share this contract. A one-member group uses the same representation. Preparation, work and review exactly cover all leaves. Required Skill attachment reads, trusted source bindings, complete output bytes, original owner plan approval and candidate evidence remain mandatory. See the [18-leaf MoE example](../../examples/composition/optimization-selected-moe/README.md) for a concrete stage-specific optimization tree. This does not execute training or collect profiles.

## Prepare under a single budget authorization

On Linux/WSL2, use [task-definition schema8](../../src/ergora/data/schemas/task-definition-v8.json) with explicit native and preparation-DAG selections to give the original six stages a single authorized total budget. Add `budget`, for example `{"wall_seconds":3600,"cleanup_seconds":60,"model_invocations":16}`. The cleanup reserve is included in the total. The invocation limit covers inventory, plan, each work unit and each reviewer (including advisory reviews), and should at least cover these known slots. It counts model-launch slots, not the backend's internal API requests, tokens or cost.

```bash
ergora task prepare my-project --definition task-definition.json --revision 1
ergora task preparation my-project TASK_ID
ergora task preview my-project --definition task-definition.json --revision 1
ergora task create my-project --definition task-definition.json --revision 1 --prepare-sha256 PREPARE_SHA --preview-sha256 PREVIEW_SHA
```

The first prepare saves the single budget before reading the installation or materials. For repeated calls or a lost receipt, continue reading the original TASK_ID without resetting the start time. Preview and create only after prepare reports `status: prepared`. preview reads the complete frozen results, including the two SHAs to confirm; elapsed time does not change their bodies. create no longer publishes after expiry. A saved intent continues through the original `creation/resume-create` without recompiling materials. Preparation binds the project revision and registered identity; changes cannot turn the old authorization into a new budget.

`authorized` means the budget is saved but the body has not started. `unknown` means the original attempt or cleanup is still unconfirmed. `failed/exhausted` does not publish usable preparation results. Check `budget_status` and the original private output. Failure or uncertainty does not automatically rerun the body; reconcile the original identity first. A new independent authorization needs a new task ID. A single observation exceeding 30 seconds returns unknown and retains the original cleanup process without extending business time. `prepared` proves only that preparation finished. After creation, use the original `task start/submission/resume-start/status/plan/approve`. Upgrade and restart this version's worker/executor to consume the `.composition-v12` queue and `requests-composition-v12` request root, and explicitly start the required stack according to [service management](../operations/services.md#manage-services-explicitly). The budget starts at the first prepare. Material reading, queueing, human approval, retries, waiting for concurrency slots, model/trusted commands, result collection and process cleanup all consume the same authorization; restarting does not extend it. Prepare services and authentication before authorizing the actual task. Existing records retain their original identities. Removed preparation inputs8–11 require their original installation to finish, cancel or reconcile before upgrade; this installation reports them unsupported.

The work deadline is the total minus the cleanup reserve. Once reached, no new work starts and cleanup follows the original fence. If the total is exhausted before stopping is confirmed, the original unknown/CANCEL_UNCONFIRMED remains. A late result with confirmed stopping can only become a failed terminal state; it cannot publish an expired SUCCEEDED. One Agent CLI invocation does not equal one provider API call, and a reserved slot does not establish an actual launch. The input budget and the original outcome's `budget` retain the original identity, deadlines and observed facts; they are neither a bill nor a kernel-level hard real-time guarantee.

A first start that expires before sending creates no new run. If an attempt already exists, `resume-start` only queries the original workflow/run and complete input without resending, even if the new configuration disables execution. During execution, restarting the Executor continues counting OWNED occupancy in the original jobs ledger. Occupied slots for live or unknown original jobs are not refunded when a Future or Temporal run ends. If a formal receipt is linked but the ledger update is lost, the daemon only reconciles the original terminal state without rerunning the body. Unknown occupancy may block the installation-level `max_parallel_jobs`. Preserve the original request, attempt, owner and stop/collection witnesses and investigate. Do not delete the ledger or manually change terminal states to free slots. This limit differs from a single task's ancestor concurrency constraints and does not establish a project-wide quota across tasks.

This current entry point selects one six-stage instance inside an ordinary parent, as described next. Multiple native instances or scheduling arbitrary mixed outer graphs still require later contracts.

The APIs are `POST .../tasks/prepare` (`definition/revision`), `GET .../tasks/TASK_ID/preparation` and the original preview/create. Current create explicitly passes `prepare_sha256`; write requests retain same-origin protection and `X-Ergora-Request: 1`. Backups must retain both `ergora/task-creations` in the registered execution state and `operations/task-preparations` in the control directory. A control-database-only backup does not include all materials. New work refuses recovery across boots/hosts or when UTC and monotonic clocks differ substantially; static contracts remain readable.

## Invoke the six stages as a subtemplate

Task-definition schema8/formal input12 includes `composition.native` in the same budget contract, binding one invocation inside an ordinary parent template to the original six-stage task. The [native-development](../../examples/composition/native-development/workflow.json) example references [prepared-delivery](../../examples/composition/prepared-delivery/workflow.json). First import the preparation, work and review bundles in the [example dependency order](../../examples/composition/README.md), then import the parent bundle and generate a complete manifest.

Keep schema8, its input, budget and mode; use the parent manifest's actual path/digest and select paths inside that instance:

```json
{"native":{"protocol":"six-stage-v1","instance":"root/development"},
 "review_instance":"root/development/review"}
```

Write both fields above inside `composition`; see the [current schema8](../../src/ergora/data/schemas/task-definition-v8.json) for the other required fields. The corresponding `execution.instance` is `root/development/work`, with each unit assigned to its actual Agent leaf. `preparation.inventory/plan` select those workflow subtrees through `{instance, coordinator}` objects; the coordinator paths append `/coordinator`. `backend_overrides` also uses the new complete paths. You must still explicitly choose the trusted writer boundary and follow the execution/review backend-diversity policy.

Follow the same `task prepare → preview → create → start` sequence. create still confirms both prepare and preview digests, followed by approval of the original plan. After upgrading and restarting the worker/executor, use the `.composition-v12` queue and `requests-composition-v12` request root; old-version queues and history remain intact. The original task creation record's `composition.native` saves the exact parent-definition chain. `native_invocation` in the original status and terminal outcome projects the same invocation. Task/run/candidate identity, approval, cancellation, unknown recovery and evidence remain with the original owners.

The initial supported shape requires ancestors to contain only this invocation and directly forward task and result. work and review must be direct subtemplates of the selected six-stage instance; inventory/planning may have their own structural wrappers. Preparation rejects additional parent branches, a second instance, unexecuted external inputs or control dependencies. Internal work/review still supports the existing sequential/parallel DAGs; this does not authorize execution of arbitrary outer graphs. The graphical task wizard can select the native six stages following the [page composition steps](../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page), explicitly authorize preparation, then preview and create schema8/input12. The CLI/HTTP can still submit complete definitions.

## Select project memories and active Skills for a formal task

For the combined sequence from retrospective candidates through separate adoption to freezing a new task, see the [complete improvement journey](../improvement/workflow.md).

On Linux/WSL2, use the same [task-definition schema8](../../src/ergora/data/schemas/task-definition-v8.json)/formal input12 with optional context. First run `ergora memory catalog PROJECT` to inspect the `id`/`revision` of currently valid memories, and `ergora skill list PROJECT` for the `name`/`digest`/`revision` of active heads. Keep `schema_version: 8`, append the following field and replace the example identities:

```json
{
  "context": {
    "root_version": "1.0.1",
    "memories": [{"id": "MEMORY_ID", "revision": 2}],
    "skills": [{"name": "your-skill", "digest": "ACTIVE_SHA256", "revision": 1}]
  }
}
```

At least one of the two lists must be nonempty. Only the project's latest currently valid memory revisions and the exact heads of currently active Skills are accepted. An initially imported baseline can be selected, but that does not establish measured improvement. `root_version` is the new version of the selected manifest's root definition and must differ from the original root. The system retains the same root ID, all member paths, original permissions and limits, adding only source context and complete Skill directories. The derived bundle is frozen with this task and does not change active Skills or the global definition library. Skill attachments require the corresponding instance's `task-mcp`/`workspace-task-mcp` mode. A read scope that does not cover the new root resource URI, conflicting content for a same-name Skill, or insufficient capacity causes explicit rejection. To change permissions, first follow the original parent/child definition revision process, then select a new manifest.

Use the original `task prepare → preview → create → start`; create still explicitly confirms both prepare and preview digests. The preview's `files["task.spec.json"].context` gives the selected identities. `composition.manifest` carries the complete sources and files. `development.envelopes.selected_context` supports offline checks of the original bodies, sources, expiry and Skill attachment identities. Each graph leaf's `material_bytes` and each scope's `usage`/`limits` show static capacity. Dynamic repository content, predecessor results and complete prompts are still checked at the actual stage; static headroom does not guarantee future success.

Old selections cannot be published for the first time after a correction, deletion, expiry or active-head change. Interrupted recovery with a complete saved creation intent uses the original snapshot, including materials that subsequently became invalid. `task creation` checks the original intent; `task resume-create` recovers by its SHA without reselecting materials or extending the budget. Archived input is run evidence. Deleting canonical memories does not remove frozen tasks or independent backups. The new protocol registers the `.composition-v12` queue and `requests-composition-v12` request root; upgrade and restart the worker/executor before using them. The CLI and HTTP share this contract.

In “Formal tasks → Preview and create,” select the native six stages and read the complete manifest. “Material sources for this task” defaults to inheriting only template materials. To add project materials, select “Inherit template and append project materials,” enter the exact new derived-root version, click “Read current material catalog,” then explicitly select memories and active Skills. The page shows complete memory bodies/sources/expiry, unselectable states and exact Skill heads. Expired and deleted records cannot be selected. Refreshing the catalog clears selections; after a failed read, a successful reread is required before use. The catalog is only an observed snapshot; original admission checks it again. Next explicitly authorize preparation, inspect frozen sources and complete files, then confirm creation with both digests. The authorization-input download includes the complete context selection. All existing ancestor materials are still inherited, and the page offers no operation to remove ancestor resources or expand permissions. The lightweight read-only `GET /api/projects/PROJECT_ID/skills/heads` returns only current active heads without invoking tool diagnostics.

## Use the refactoring recipe

`refactoring` delegates behavior-preserving refactoring to the original `large-change` six-stage owner. By default, material inventory, planning and original owner approval run first. After the refactoring implementer finishes `rewrite`, the compatibility specialist performs `compatibility` on a candidate integrating its predecessor. After the original trusted integrate/verify stages, three required reviewers inspect structure, correctness and test value in parallel.

```bash
ergora composition install-preset refactoring
ergora composition prepare-manifest ergora-refactoring-template 1.3.6 \
  --grant examples/composition/refactoring/grant.json \
  --directory ./refactoring-manifest
```

The example is in the repository's [refactoring directory](../../examples/composition/refactoring/README.md). The wheel contains all Agents and subtemplates; examples are unnecessary when using your own grant. Copy [task.example.json](../../examples/composition/refactoring/task.example.json) into a task definition and enter the real issue, task ID, baseline, manifest path/digest and actual project modules/callers. Also check the complete material scope, behavior invariants, migration and isolated rollback checks. Then follow the original `task prepare → preview → create` sequence with two-digest confirmation, followed by start/plan approval. Valid JSON or successful prepare proves only that the contract can be assembled. Actual checks and review evidence support behavior preservation.

The shared module/validation/coordinator inventory and planning groups each contain three real calls. With the two refactoring work units and three independent final reviewers, this default needs 11 model slots. These reusable development Agents use Codex gpt-6.1-sol/max in every role because their Agent-level minimum also covers planning; independent reviewers and pure documentation Agents use at least high. Complete `backend_overrides` must retain model/reasoning_effort values satisfying the definition minimum; writers also explicitly select current-container. Same-backend selection under `prefer-distinct` requires `diversity.reason`; `require-distinct` continues to reject it. The compatibility work unit does not replace final independent review.

The parent directly includes [`ergora-codebase-quality`](../../src/ergora/data/presets/workflows/ergora-refactoring-template/skills/ergora-codebase-quality/SKILL.md). All descendants inherit complete guidance on the target repository conventions, actual callers and testing seams. Original task/budget/candidate identities and recovery owners remain; installation and static preview do not approve a business migration.

The definitions and compositions for the refactoring implementer, structure reviewer, correctness and test-value reviewers, and compatibility validator are maintained in this repository. Engineering guidance draws on [Agent definitions](../definitions/agents.md#built-in-specialists), retaining each source's license. They are independently versionable specialty configurations; Codex/Claude Code are the actual runtime backends. Selecting a backend does not import all of that tool's private prompts, Skills or scheduling framework. Check backend capabilities and complete material reading separately according to the [Agent guide](../agents/backends.md).

To use the Skill only in a standalone project invocation, run the following command from this repository's checkout root after registering the real `my-project`:

```bash
ergora skill import my-project \
  src/ergora/data/presets/workflows/ergora-refactoring-template/skills/ergora-codebase-quality
```

Standalone `agent run --skill ergora-codebase-quality` consumes the project's currently adopted version. This and the template's fixed Skill are two explicit choices. The first same-name import becomes the initial baseline; subsequent candidates still require [evaluation and adoption](../improvement/skills-and-evaluation.md#skill-candidates-evaluation-and-adoption). Importing into a project or editing a host Skill does not change a frozen template. Changing materials for a formal task requires selecting a new version and manifest.

Continue: [Create a formal development task](tasks.md) · [Submit, observe and recover a development task](run-and-recover.md).
