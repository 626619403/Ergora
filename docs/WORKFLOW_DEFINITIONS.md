<a id="可组合工作流定义"></a>
# Composable workflow definitions

[English](WORKFLOW_DEFINITIONS.md) · [简体中文](zh-CN/WORKFLOW_DEFINITIONS.md)

Workflow packages compose exact versions of specialists or subworkflows into a bounded DAG. A structure-review template can stand alone, or structure, correctness and test-value templates can run in parallel and be chained with an execution template. The structural parent chain determines inheritance; work dependencies pass data only through named ports.

`composition` provides static checks, an immutable version library, complete previews, portable static composition bundles and explicit single-leaf calls. Previews do not call models; `run-input` can pass prepared input to the selected backend. Formal development follows the [six-stage process](USAGE.md#正式任务的操作顺序与恢复); its review stage supports nested read-only serial/parallel branches with explicit all-join barriers. See [formal review compositions](USAGE.md#为正式任务冻结审查组合) for configuration, [the formal DAG protocol](#正式只读审查的数据端口) for read-only review ports, and [the work-units-v2 protocol](#专长执行者与原工作单元) below for specialist writer assignments.

The Web console's “Agent and composition library” reuses the same version library, import and preview use cases without requiring project registration. Select an exact workflow version, inspect the static ceilings initialized from its root declaration, and explicitly preview it to see every instance's structural parent chain, predecessor dependencies, named ports, complete resource provenance and assembled prompt; see [page operations](USAGE.md#在页面浏览与预览定义). Static ceilings do not authorize a project, and backend fields are requests. Downloaded definition JSON and preview JSON support reading and comparison; share complete resources and exact dependencies through `export`, `prepare-manifest` below or [freeze the current preview](#固定当前预览到持久控制目录). [Explicitly revise](#在页面修订工作流) the standard document on the page; see the [follow-up plan](plans/2026-11-09-composition-console.md) for the nested canvas and formal handoff.

Current availability: import, preview and manifest freezing do not execute or adopt a graph, approve a candidate or establish backend/SDK readiness. General Repeat and arbitrary mixed-node graph execution remain unimplemented. Registered design policies currently store requirements only and visibly refuse unsupported execution; the trusted human channel is unavailable, and the isolated source-journal draft is unreleased. All schema3 training effects remain explicitly closed. See the [current plan](PLAN.md), [design-policy execution guard](../src/ergora/task_design.py) and [training-controller guard](../src/ergora/training_cycles.py).

<a id="使用内置领域组合"></a>
## Use bundled domain compositions

Installing the wheel is enough to import the default specialists and all their subworkflows; no repository examples download, model call or service startup is required:

```bash
ergora composition presets
ergora composition install-preset repository-governance
ergora composition install-preset large-change
ergora composition install-preset training-optimization
ergora composition install-preset refactoring
ergora composition install-preset optimization-performance-diagnosis
ergora composition install-preset training-flow-map
ergora composition install-preset evidence-report
ergora composition install-preset optimization-report
ergora composition install-preset pretraining-review
ergora composition install-preset posttraining-review
ergora composition install-preset engineering-review
ergora composition show ergora-large-change-template 1.1.0 --material
ergora agent definition show ergora-server-implementer 2.0.0 --material
```

[Pretraining/posttraining review](TRAINING_REVIEW.md) adds domain specialists to the general three-way review and describes independent leaf calls separately from formal all-join review.

The [evidence-report author](EVIDENCE_REPORTS.md) provides an independent read-only `root/author` that produces Markdown and a static self-contained HTML reading view from complete supplied materials. It reuses the manifest, single-leaf input and original-run reader below; it does not collect evidence, execute predecessors or grant approval.

`presets` reads shipped content without creating State. `install-preset` imports exact versions in dependency order; repetition retains the same identity and refuses different content at an existing ID/version. Each definition is published atomically, but the whole installation is not a cross-library transaction; retry after interruption. Installation changes no project binding or permission, does not install/authenticate an Agent CLI, and grants no execution or approval authority. The authoritative resources for the new default library are in [data/presets](../src/ergora/data/presets/presets.json); replace specialists and subtemplates through the existing export/new-version/import process. Previously published objects and frozen examples retain their original identities; current source revisions publish new versions.

|Composition|Root ID/version|Default relationships and supported use|
|---|---|---|
|repository-governance|`ergora-governance-template@1.1.0`|Shared module/validation/coordinator inventory and planning → parallel knowledge-mapping and architecture-regression work → trusted integrate/verify and three reviews; 11 model slots|
|large-change|`ergora-large-change-template@1.1.0`|Shared module/validation/coordinator inventory and planning → current contract → parallel server/client work → integration validation → trusted integrate/verify and three reviews; 13 model slots|
|training-optimization|`ergora-training-proposal@4.2.2`|Shared flow/design/diagnosis → retained kernel assessment → measurement proposal. Select relevant topic workflows as real descendants in an exact root revision; each leaf inherits the complete common methods and environment record. Explicit leaf calls only.|
|refactoring|`ergora-refactoring-template@1.3.0`|Shared module/validation/coordinator inventory and planning → serial rewrite/compatibility work → trusted integrate/verify and three reviews; 11 model slots, large-change formal task type, definition8/input12|
|optimization-performance-diagnosis|`ergora-opt-performance-diagnosis-proposal@1.2.1`|Limited symptom/compatible-reader specialist plus local test design and measurement proposal; actual profile collection stays with its original owner|
|training-flow-map|`ergora-training-flow-map`|Read-only `root/map` separately produces algorithm/execution dependency maps, state lifecycles and falsifiable redundancy hypotheses; no automatic downstream specialist or training execution|
|evidence-report|`ergora-evidence-report`|Read-only `root/author` produces Markdown/static HTML reports bound to sources; preserves original evidence, run records and independent review/release|
|optimization-report|`ergora-evidence-report@2.0.1`|Same read-only author interface, with dedicated optimization Skill and full template context: source flow/redundancy → comparable results → diagnosis/decisions; explicitly supplied evidence only|
|pretraining-review|`ergora-pretraining-review` 1.1.0|Original general three-way review alongside a pretraining specialist, required/all-join; all four leaves inherit shared backend guidance; the domain leaf can be called independently|
|posttraining-review|`ergora-posttraining-review` 1.1.0|Original general three-way review alongside a posttraining specialist, required/all-join; all four leaves inherit shared backend guidance; the domain leaf can be called independently|

The `engineering-review` catalog imports `ergora-delivery-review@1.2.0` plus optional performance/resource-lifecycle/dependency/security/measurement reviewers. Its default remains three core branches. The [five-member revision example](../examples/composition/pr-review-selected/README.md) selects performance and resource lifecycle before freeze, keeps every selected member required and documents full source inputs, readonly permissions, model floors and supervisor follow-up handoff. Independent source calls run one leaf each; the source report requires all declared leaves. Formal development uses its existing ReviewDAG, candidate, fixed call slots, original clock and cleanup owners. All training-root domain/general leaves inherit their own outer root reporting contract; full response compliance is read separately from schema/decision coverage.

Development compositions share `ergora-delivery-review`, which references three independently usable subtemplates for structure, correctness and test value. Each specialist has separate initial instructions, expertise and Skills, loading complete materials along its own structural parent chain. Bundled specialists default to Codex gpt-6.1-sol and enforce the [definition minimum](AGENT_DEFINITIONS.md); per-instance overrides must satisfy it. Invocation admission still checks availability and authentication; same-backend selection follows the diversity policy and records its reason.

The three development presets share one preparation default: `ergora-refactoring-engineer` as module specialist, `ergora-compatibility-validator` as validation specialist, and the canonical coordinator in each group. Each group has three actual model leaves. Their Agent-level planning minimum is `gpt-6.1-sol/max`, also applying to work invocations of those reusable Agents. Task-specific expert selection uses an explicit revision before freezing; a task-type name does not switch the shared graph. The [development specialist example](../examples/composition/development-specialists/README.md) publishes a cross-end revision through real receipts, with 5 inventory + 5 plan + 4 work + 3 review = 17 slots. Added required or advisory review leaves increase the finite budget by their actual count.

With an explicit preview grant, run `prepare-manifest` as described in [complete composition sharing](#保存和分享完整组合), substituting a root ID/version above. Formal development selection uses [work-units-v2](#专长执行者与原工作单元), with `root/development/work` and `root/development/review` inside the selected native instance; a unit ID maps directly to the same-named leaf, for example `contract`→`root/development/work/contract`. Domain inputs obtained through `templates copy` contain the corresponding unit IDs, paths and dependencies; when changing those unit relationships, revise the corresponding work subtemplate too. Workspace write calls still require every writer to explicitly select trusted current-container; importing a composition does not select this boundary automatically.

`refactoring` uses [native six-stage selection](USAGE.md#使用重构配方): its instance is `root/development`, containing work/review, with preparation also handled by independent specialist sessions. Its [complete task example](../examples/composition/refactoring/task.example.json) supplies definition8, unit assignments, a budget and explicit writer trust; replace its baseline, callers, scope, acceptance criteria and manifest with real values. Its parent Skill supplies repository conventions, real callers and testing seams; original task types remain. The catalog's `development-v5` is the existing page's development-category label; the task definition selects the actual execution contract, and this label does not downgrade new tasks to input5. The graphical task wizard can select native six stages, preparation and budgets as described below, producing input12 through definition8.

The training composition's `root/analysis/design`, `root/analysis/profile`, `root/kernel/assess` and `root/measurement/review` support [single-leaf calls](#调用一个准备好的叶子); the operator must supply the complete workload, baseline and relevant predecessor outputs in the task file. Independent `run-input` does not execute graph predecessors. Generated proposals/code text and model reviews are neither experiment results nor adoption approval. Actual CPU/GPU work, Forge candidates and measurements still use the original trusted runner/gate described in the [training guide](TRAINING.md). The catalog's `runtime` describes the supported use of this distribution; it does not establish backend, service or hardware readiness.

The current training root includes source flow, cross-domain planning/diagnosis, kernel implementation assessment, independent measurement review and library/environment selection. Leaves are read-only with shell=false and network=[]. Calls using Skill attachments require supported task-MCP. Operators supply the complete original task and predecessor materials; missing evidence is reported. Proposals establish neither heterogeneous validation, environment compatibility nor measured gains.

The nineteen `optimization-*` direction presets select scoped specialists at `root/specialist`, alongside `root/design` and `root/measurement/review`. Profiling and performance-diagnosis reuse one evidence-analysis expert with different topic instructions; kernel reuses the kernel designer. Other directions use their own expert definitions and complete methods. Low-precision retains `root/kernel` between analysis and measurement, and measurement requires that complete result.

A bare direction root is a limited topic proposal. The [selected MoE example](../examples/composition/optimization-selected-moe/README.md) uses a fixed 18-leaf native tree with automatic stage fanout/join on the original six-stage owner. Its current revision bases and complete resource file bindings are pinned explicitly. Every leaf inherits the two common Skills and environment record from one development ancestor, without another policy source tree. Independent `run-input` still executes only its selected leaf and requires complete caller-supplied predecessors.

The shared optimization Skill also defines staged GPU validation: the authorized supervisor compares on 2 GPUs (4 when necessary), batches measured improvements for matched acceptance at each target 8-GPU or larger cross-node scale, and uses available `igs` pool operations within the agreed budget. See its [GPU comparison policy](../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#gpu-comparisons-and-pool-validation) for the fixed first-round model contract, original full acceptance gate and unknown-submission reconciliation. This guidance adds no training permission to readonly leaves and implements no automatic experiment loop or iGS backend.

<a id="运行示例"></a>
## Run the example

Install basic Ergora first using the [usage guide](USAGE.md); these commands require no model credentials, Web, issue or Temporal service. Example files are in the repository's [examples/composition](../examples/composition/README.md). From the repository root, import dependencies before the workflows that reference them:

```bash
ergora agent definition import examples/agents/kernel-implementer
ergora agent definition import examples/agents/architecture-reviewer
ergora agent definition import examples/composition/agents/correctness-reviewer
ergora agent definition import examples/composition/agents/test-value-reviewer
ergora composition check examples/composition/parallel-review --material
ergora composition import examples/composition/structure-review
ergora composition import examples/composition/correctness-review
ergora composition import examples/composition/test-value-review
ergora composition import examples/composition/parallel-review
ergora composition import examples/composition/kernel-delivery
ergora composition list
ergora composition show kernel-delivery 1.0.0 --material
ergora composition preview kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json
ergora composition export kernel-delivery 1.0.0 ./shared-kernel-delivery
```

`check` validates one package's schema, resources, paths and local graph without resolving library dependencies or creating State. `import` also resolves the entire dependency tree and checks ports, inheritance, permissions and this definition's budgets; missing references or digest drift fail. `preview` additionally applies explicitly supplied project authorization ceilings, reading the library without creating or migrating State. `show` displays this package's materials; leaf `resources` and `prompt` in the preview contain the complete static materials from the entire ancestor chain.

The example expands to 10 instances: a root, an implementation Agent, an overall review workflow, three review subworkflows, three reviewer Agents and an all-join. `root/implement` precedes `root/review`; the three ready branches inside the overall review can run in parallel, and `root/review/gather` waits for all three. Repeated references to the same subworkflow create instances with distinct paths.

The example Agents use Codex and Claude Code. Preview shows only the requested backend, without checking installation or authentication or promising model quality or independent errors. To change a backend persistently, create a new Agent version and update references along the chain; single-leaf calls also support an explicitly recorded per-call override. See [Agent entry points](AGENT_BACKENDS.md) for project-role calls.

<a id="保存和分享完整组合"></a>
## Save and share a complete composition

After importing the examples, save the root workflow together with every recursive dependency:

```bash
ergora composition prepare-manifest kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json --directory ./kernel-delivery-manifest
ergora composition verify-manifest ./kernel-delivery-manifest
ergora composition verify-manifest ./kernel-delivery-manifest --material
```

Share the entire output directory. A recipient with basic Ergora installed can run `verify-manifest` without first importing the same definitions, creating a project or starting services. The bundle's `manifest.json` records the exact root version, supplied grant and complete graph digest; `composition.json` preserves all stable instances, named ports, dependency/join relationships, ancestor resource provenance, complete static prompts, permissions and budgets; `assets/` carries every exactly referenced definition, Skill directory and context. Repeated references copy a definition once, while instance state remains distinct by path.

Verification rebuilds the complete graph from bundled resources and checks identity byte for byte, refusing missing, modified or extra files and unreferenced definitions; it does not depend on the original library location or current backend catalog. New preparation still checks current definition admission and does not overwrite an existing directory. It shares complete asset/capacity checks and atomic publication with single-leaf inputs, explicitly refusing complete bundles exceeding 10 MB or 500 files.

To use a leaf, prepare a UTF-8 task file and generate its input directly from the complete bundle:

```bash
ergora composition prepare-from-manifest ./kernel-delivery-manifest root/review/structure/review --task ./review-task.txt --directory ./prepared-review --max-prompt-bytes 30000
```

This rechecks current definition admission and the entire graph identity; a verifiable old bundle is not necessarily callable today. Use the generated input through `check-input`/`run-input` below. It neither executes graph predecessors or ports nor creates State or depends on the recipient's original definition library.

These are complete **static** materials with `execution_authorized` false; they contain no operator task body, future parent results, candidate approval or runtime session. Formal tasks still require creation, original-owner approval and runtime admission; see [formal review compositions](USAGE.md#为正式任务冻结审查组合) for currently supported shapes. To include this bundle in a complete State backup, put the output directory inside your State data directory; otherwise save/copy the entire bundle separately, rather than retaining only `manifest.json`. `--material` returns every leaf's complete static materials; omitting it returns only identities and inventories.

<a id="固定当前预览到持久控制目录"></a>
### Freeze the current preview into the persistent control directory

In the page's “Agent and composition library”, preview the exact workflow and explicit ceilings, then click “Save current preview as complete manifest”. This saves the currently selected root, excluding editor buffers and the comparison target. Success returns the complete bundle's absolute path, `digest` and original `preview_sha256`; formal task definitions use this `path` and `digest`. The page's “Download composition-preview.json” remains a reading aid and cannot replace the complete directory.

The CLI uses the same use case and requires explicitly submitting the reviewed preview digest:

```bash
ergora composition preview kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json
# Insert the actual preview_sha256 returned above; do not create a task with the example placeholder.
ergora composition freeze-manifest kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json --preview-sha256 PREVIEW_SHA256
ergora composition show-manifest PREVIEW_SHA256 --material
```

The complete bundle lives at `composition-manifests/PREVIEW_SHA256/` under the current control directory, following `--home`/`ERGORA_HOME` and the platform's default persistent directory; a complete control-directory backup includes it. The first save reruns original admission and checks the preview digest; changes to ceilings or definition identity require another review. Retrying the same digest verifies the original complete bundle without overwriting an existing directory; file/definition/material identity that fails complete verification is explicitly refused. Empty directories are copied and retained but excluded from the digest under the existing contract; stable additions/removals of empty directories do not change identity.

If the save response is lost, retain the original digest and query “Read saved bundle by current digest” or `show-manifest`; after a refresh, preview the same exact version and ceilings again before reading. Reading requires neither the source library nor a currently available backend; independently use `show-manifest` or `verify-manifest`, without equating historical readability with current executability. HTTP uses `POST /api/composition/manifests` (the original preview request plus `preview_sha256`) and `GET /api/composition/manifests/PREVIEW_SHA256?material=true`; writes still require local same-origin access and the original request headers. Saving creates no project, task, approval or Agent call.

<a id="在正式任务页面选择组合"></a>
## Select a composition on the formal-task page

Complete [project registration](PROJECTS.md), then open “Formal tasks” → “Preview and create”. The original “Project roles” entry continues using project bindings without automatically applying library compositions.

1. Load a registered development template or compatible draft and fill in the task ID, issue and complete input. Choose “Agent source for this task”: composition review only, composition execution and review, or native six stages (Linux/WSL2). Training optimization retains its separate entry point.
2. Paste the saved bundle's `manifest.preview_sha256` returned above and click “Read complete manifest”. This is not the manifest directory digest; the page reads and verifies the original complete bundle from the current control directory, then displays its root identity and manifest digest. Reading a historical bundle does not admit a formal call today.
3. Select the review subtree by full instance path. Execution-and-review compositions also require an execution subtree; click “Load work units from current input” and select the implementation Agent for each unit. Bundled development compositions usually use `root/work` and `root/review`; unit IDs correspond to same-named work leaves. Reload assignments after changing the work subtree; a failed load retains the previous input and assignments, and the original task preview checks every unit and dependency.
4. Reviewers may retain their exact definition's backend request; to override it, select a backend, configure model and other fields, and state a reason. Explicitly override each writer. Under the existing backend contract, writable mode requires a trusted Linux binding; currently, select Codex's “Execution boundary” → “Trusted current container / user”. The page does not infer this trust from a static definition. External tool configuration still provides authentication; do not enter credentials here. The server explicitly refuses other backends or unsupported modes.
5. Different execution/review backends are preferred by default; same-backend fallback requires a policy explanation. You can explicitly require distinct backends or allow the same backend under the existing diversity contract. Different names or model choices alone do not prove independent error probabilities.
6. Native six stages also require selecting the six-stage invocation inside the ordinary parent template, the inventory and planning Agents, preparation mode, repository-relative paths (one per line), and total time/reserved cleanup time/model-call count. Preparation members also support per-instance backend overrides. For bundled `refactoring`, select `root/development`, `root/development/preparation/inventory` and `root/development/preparation/plan`; execution/review are at `root/development/work` and `root/development/review`. Adapt the [complete example](../examples/composition/refactoring/task.example.json) to the actual input and work units. Under “Materials for this task”, optionally add [exact project memories and active Skills](USAGE.md#为正式任务选择项目记忆与活动-skill): explicitly read the catalog, enter a new root version and select entries; the default inherits all ancestor materials without automatic recall. Click “Prepare native six stages”, check the complete input and explicitly “Confirm preparation authorization (start budget clock)”; preview is available only after `prepared`. The budget has already started; reads and previews do not extend it, and changing authorized input requires a new task ID. Before authorization, “Download complete authorization input” is available, and preparation or unknown results also offer this download. Closing or refreshing the page releases the form; ID queries read status without reloading the original form. Continue with the downloaded file using the original CLI's `task preview --definition ... --revision ...` and dual-digest `task create`. If a response is lost, first “Read original preparation record” or reopen “Read preparation record by ID”; do not automatically resend authorization.
7. Click “Preview frozen contract”, review the server's complete frozen files and all preparation/execution/review members, the six-stage parent chain and original budget deadline, then “Confirm creation of frozen contract”. The page retains both original preparation and preview digests; an optional source snapshot and six-stage composition can be used together. Creation publishes the contract without starting, approving or executing it. Follow the [formal operating sequence](USAGE.md#正式任务的操作顺序与恢复) to start and approve the original plan. Earlier review-only/execution compositions do not require preparation authorization.

Field changes invalidate the previous task preview; late manifest or preview responses cannot restore old selections. Read/preview failures retain input; issuing creation locks the original contract. If its response is lost, query the original creation record read-only using the task ID retained on the page before deciding how to recover; do not resend under a different ID. Composition, backend overrides and reasons belong only to this frozen task and change no template or project defaults; original owners still verify all ancestor materials, permissions and candidate/approval evidence. The form is released when its dialog closes; save task input first. The complete manifest in the definition library remains persistent.

<a id="定义和数据流"></a>
## Definitions and data flow

The package entry point is `workflow.json`; see [schema v1](../src/ergora/data/schemas/workflow-definition-v1.json) and [schema v2](../src/ergora/data/schemas/workflow-definition-v2.json). Only JSON is accepted, with an optional UTF-8 BOM; duplicate JSON keys and unknown fields are refused. Package trees and resources follow the [Agent package](AGENT_DEFINITIONS.md#资源和存储边界) contract for digests, paths, sizes, directory limits and same-platform recovery.

|Field|Consumer and meaning|
|---|---|
|`schema_version`, `id`, `version`, `description`|Version-library and CLI display; format version is strictly integer 1 or 2, IDs use lowercase kebab case, versions have three exact numeric parts, with no implicit latest.|
|`resources`|Ordered local instructions/context/Skills; may be empty. Reuses Agent resource formats and complete digest checks.|
|`inputs`|Array of input-port names; mappings are checked statically, and formal `dag-v1` projects the root task or completed predecessors' named outputs using frozen bindings.|
|`outputs`|Output port → source binding, from this workflow's inputs or local nodes' outputs.|
|`nodes`|Agent references, Workflow references and all-join; determine structural instances and the local graph.|
|`permissions`|This workflow's request/child ceilings; checked along the complete structural ancestor chain and against the project grant.|
|`limits`|This subtree's depth, instance, concurrency and complete static-material ceilings; root/project totals cover every subtree.|

Agent/Workflow references require `kind`, `id`, `version` and `digest`. `digest` identifies the entire package tree and is available from `check/import/show`; it is not a single JSON file's SHA. Each node has a unique local `id` and explicit `depends_on`. Agent nodes also have `role`, `permissions` and exactly one `task` input; their result port is fixed as `result`, and the target Agent must support the role. Workflow-node inputs/outputs are declared by the exact target version.

Bindings can only be `{"input":"task"}` or `{"node":"implement","output":"result"}`. A node referencing another node's result must list it as a direct dependency; references do not implicitly add dependencies. There are no Python expressions, arbitrary scripts or loops. Port values are opaque data consumed at execution time; static checks do not establish trust in a candidate, review decision or domain artifact.

`{"id":"gather","join":"all","depends_on":["structure","correctness","test-value"]}` declares a join whose intended `result` output is a map of every dependency branch's complete named outputs. A join is a data barrier waiting for all listed branches. Formal read-only parallel review requires the root output to point to an explicit all-join covering every leaf; the original trusted runner checks each required branch's candidate, session and receipt before producing an aggregate reference. Static all-join alone is neither majority voting nor human approval.

<a id="必需与建议审查的静态声明"></a>
## Static required and advisory review declarations

WorkflowDefinition v2 requires every Agent node with `role: reviewer` to explicitly declare `review_requirement: required` or `advisory`. This is a workflow-instance responsibility; the same specialist may have different responsibilities at different nodes. AgentDefinition remains v1. Other roles, subworkflow references and joins do not accept this field. To change a nested review leaf's responsibility, save a new child-definition version and update exact references along the parent chain. Permission, Skill and context inheritance rules remain unchanged.

For example, [review-requirements](../examples/composition/review-requirements/workflow.json) makes structure review required and test-value review advisory:

```bash
ergora composition check examples/composition/review-requirements
ergora composition import examples/composition/review-requirements
ergora composition preview review-requirements 1.0.0 --grant examples/composition/preview-grant.json
ergora composition prepare-manifest review-requirements 1.0.0 --grant examples/composition/preview-grant.json --directory ./review-requirements-manifest
```

First import the structure reviewer and test-value reviewer from the beginning of this guide. Preview displays each leaf's declaration; any recursively referenced v2 definition makes `composition-preview.schema_version` 2, and complete bundles/backups preserve the original identity. All-v1 compositions retain their preview version and bytes; active templates do not downgrade historical members.

Formal development supports this composition; see [freeze a review composition](USAGE.md#为正式任务冻结审查组合). It must contain at least one required reviewer, and every required and advisory branch must finish. In the new responsibility graph, the selected output must point to an explicit all-join covering every member, even a single member; old v1 single-leaf graphs retain their runtime contract. Only after checking the same candidate, independent sessions, complete artifacts and actual model opinions does the trusted runner allow an advisory `request-changes` into the join with its original findings. Its original receipt remains `FAILED`, and the join records responsibility and opinion. Required requests for changes, runtime failure, missing output, timeout, contract violations and unconfirmed cleanup still block progress. Independent `run-input` calls only the selected leaf; it neither aggregates the workflow nor produces formal approval.

<a id="正式只读审查的数据端口"></a>
## Data ports for formal read-only review

[serial-review](../examples/composition/serial-review/workflow.json) reuses three independent subtemplates: structure review finishes first, then correctness and test-value reviews run in parallel, followed by explicit all-join. After importing the specialists and three subtemplates at the beginning of this guide:

```bash
ergora composition import examples/composition/serial-review
ergora composition prepare-manifest serial-review 1.0.0 --grant examples/composition/preview-grant.json --directory ./serial-review-manifest
ergora composition verify-manifest ./serial-review-manifest
```

Within the user task definition v2's `composition`, explicitly set `review_protocol: "dag-v1"` and provide this manifest's path and digest, then [preview, create, start and approve the plan](USAGE.md#正式任务的操作顺序与恢复). The saved formal envelope is v4, with a separate queue/request-root; tasks without this field retain their v2/v3 contract without automatic upgrades. This remains review within the original six stages, without additional inventory, planning or verify execution. All members are read-only reviewers, at least one required; writer assignment is outside this entry point.

The structural parent determines ancestor resources and permissions; `depends_on` controls order alone, and `inputs/outputs` select data sources. Reviews connected only by control dependencies still enter the final aggregate but do not automatically become downstream prompts or Skills. A nested Workflow publishes named outputs only after all its nodes finish and may have multiple outputs. The selected review subtree has one terminal output; its projection chain must end at explicit all-join, and the transitive closure of completion dependencies must cover every reviewer, including serial upstream reviewers.

Each input uses `bindings` to map to `task` or a stable `实例路径#端口` (instance path#port); the `values` table stores unique values. A join value references all named outputs of each direct dependency, and repeated template instances retain distinct paths. In the actual model input, `review_inputs.results` provides original stages, receipts and digests, and every original artifact's complete body for all bound review sources. Original request/context/receipt/claim, candidate and actual read SHA are checked before invocation. Advisory request-changes can flow downstream with their FAILED originals retained; runtime failures cannot supply valid port values.

Dynamic ports and complete predecessor bodies are inlined into the actual prompt. Task-mcp still exposes only this leaf's and its structural ancestors' fixed resources, without automatically opening siblings' or predecessors' host files. All ancestor materials and original predecessor artifacts count toward the 1,000,000-byte complete-input limit. A shared table avoids recursive expansion of the same join value, but bodies inside different audit artifacts may still repeat, so long audit chains can exceed the limit early; execution then stops explicitly without truncation or omission. Original runtime owners retain cross-member session isolation, ancestor concurrency limits, cancellation, unknown-result reconciliation and history recovery.

<a id="专长执行者与原工作单元"></a>
## Specialist writers and original work units

[specialist-work](../examples/composition/specialist-work/workflow.json) assigns implementation and validation to two independent specialist definitions, passing original artifacts from the former to the latter after completion; [specialist-delivery](../examples/composition/specialist-delivery/workflow.json) connects the work join to three parallel reviews. These reuse the original six stages: inventory, plan and owner approval happen once, followed by the original work units, integrate, trusted verify and review.

Import the three reviewer specialists and subtemplates from the beginning of this guide, then the implementation specialists and new compositions:

```bash
ergora agent definition import examples/agents/kernel-implementer
ergora agent definition import examples/agents/validation-implementer
ergora composition import examples/composition/specialist-work
ergora composition import examples/composition/specialist-delivery
ergora composition prepare-manifest specialist-delivery 1.0.0 --grant examples/composition/preview-grant.json --directory ./specialist-delivery-manifest
ergora composition verify-manifest ./specialist-delivery-manifest
```

Use task-definition-v2 and add this to the existing `composition` option:

```json
{
  "review_protocol": "dag-v1",
  "review_instance": "root/review",
  "mode": "task-mcp",
  "execution": {
    "protocol": "work-units-v2",
    "instance": "root/work",
    "assignments": {
      "implementation": "root/work/implementation",
      "validation": "root/work/validation"
    },
    "mode": "workspace-task-mcp"
  }
}
```

Retain the actual `manifest` path and `manifest_digest`. Keys in `assignments` must correspond one-to-one to the original `input.work_units[].id`; this example's validation unit must depend on implementation. Each selected work leaf maps to one unit; reuse a specialist through distinct instance paths. The static graph and original units must have identical transitive ordering. The two subtrees must be disjoint and cover every Agent in the graph; the work subtree also needs an explicit nonempty all-join covering every leaf. Missing members or an additional execution order are refused.

`backend_overrides` selects backends, models and reasons separately for all actual writers and reviewers. The initial workspace mode supports Codex on Linux/WSL2 and requires explicitly selecting `{"tool":"codex","sandbox":"current-container"}` for every writer; the outer project must also confirm the current container through [trusted execution configuration](AGENT_BACKENDS.md#可选的正式六阶段执行桥接). Example Agent definitions retain ordinary Codex bindings; isolation requirements are not lowered automatically without this explicit choice. The new workspace mode does not support Claude/arbitrary commands/mini-swe-agent and refuses them before execution; their existing modes remain unchanged. Review can select another backend; `prefer-distinct` requires an explicit fallback reason for the same backend. Diversity compares all actual writers rather than the project's default implementer.

Work inherits and narrows the complete permission chain; every path in each original unit must fall wholly within its effective write scope (logical prefix `workspace/`). The Executor still owns independent checkouts, dependency-commit merging, path gates, deterministic checks, cancellation fences and trusted commits. Agents cannot commit or move HEAD; invalid results do not reach successors. Every writer simultaneously obeys original unit concurrency, executor capacity and all structural ancestor limits.

`work-units-v2` publishes formal envelope v6 using a separate `composition-v6` queue and request root; new execution compositions created on the page select this protocol. Task JSON may still explicitly select `work-units-v1`, publishing the original v5 contract. Existing tasks retain their versions through tool upgrades. `composition check-input/run-input` remain read-only; preparing an input bundle cannot authorize a writable call. Native workspace tools can access the current user's files; prompts and the final Git gate constrain permission paths, without enforcing isolation of every in-flight file access or network egress. Fixed task MCP still provides only this leaf's and its ancestors' declared materials. Use a separately supported execution environment for strong isolation or external MCP; this mode does not supply those capabilities. Existing Windows installation, definitions and compatible readers remain; use WSL2 for the new write path.

Actual work input contains all ancestor instructions, context, Skill bodies/attachment entry points and the approved plan. In v6, `stage-artifacts-v1` passes every declared stage artifact and trusted check/opinion: the profile's `artifacts_by_stage`, work's trusted `test-results`, verify's trusted `check-results`, every checks reference in the receipt, and review's trusted `composition-review-decision`. These bodies are fully inlined; model summaries are not the artifacts promised by this contract. Complete originals such as logs, previous prompts and MCP audits remain in original receipt indexes, `task evidence` and offline handoff, without recursively copying them again as downstream results. Retaining an index does not establish that downstream models read the complete audit.

In v6, `work_inputs.results` stores the union of port sources and direct work dependencies by instance path; `dependencies` maps unit IDs to instance paths. Each source is delivered once. Control dependencies without bound data ports still deliver their declared artifacts/trusted checks; control edges add no ancestor Skills. Review still receives the original plan/verification and bound sources. v2–v5 retain their complete artifact-inlining contract, where long audit chains can still exceed budgets; choose the v2 protocol for new tasks rather than altering old tasks to erase failure records.

Original request/context/admission, actual binding/session, claim, formal-call/invocation/selection, every byte of receipt artifacts and Git ancestry are still checked; v6 audits omitted from inlining must also remain intact. Work ports are not review opinions, and trusted readers still validate review opinions. Integrate/verify, the final candidate and original approved plan remain mandatory before review. v5/v6 reference fully saved admission by digest, preserving the original manifest and complete ancestor resources. The complete-input ceiling stays at 1,000,000 bytes; genuinely oversized declared artifacts or ancestor materials are refused before invocation without truncation.

Original attempt/monitor/unknown and cancellation-recovery rules remain. Recovery after the original call and commit finish but before receipt publication reuses the same job/context and monitor artifacts. If HEAD has changed, verify the complete invocation evidence saved by the original Executor after its first HEAD gate; missing or mismatched evidence is refused and requires reconciliation. Without reliable external results, retain unknown status rather than redispatching a writer or changing IDs. After a run, use `agent runs` and formal `task evidence` to read original calls/artifacts, and export offline handoff for the original task.

<a id="盘点与规划的完整材料"></a>
## Complete inventory and planning materials

Use current [task-definition schema8](../src/ergora/data/schemas/task-definition-v8.json), producing formal input12. Inventory and plan each select a readonly workflow subtree and a canonical coordinator. The original six-stage owner runs ready experts within the frozen ancestor concurrency limits, passes complete predecessor originals to the coordinator, waits for owner approval of the canonical plan, and retains trusted checks, candidate identity and cleanup.

After the specialist-work and parallel-review dependencies, import the preparation Agent, both current groups, their wrapper and native parent:

```bash
ergora agent definition import examples/composition/agents/development-preparer
ergora composition import examples/composition/preparation-inventory
ergora composition import examples/composition/preparation-plan
ergora composition import examples/composition/preparation-guide
ergora composition import examples/composition/prepared-delivery
ergora composition import examples/composition/native-development
ergora composition prepare-manifest native-development 1.1.0 --grant examples/composition/preview-grant.json --directory ./native-development-manifest
```

The complete schema8 definition includes `budget`, original work/review selections and a single native invocation. Its preparation selection is:

```json
{
  "native": {"protocol": "six-stage-v1", "instance": "root/development"},
  "preparation": {
    "protocol": "preparation-dag-v1",
    "inventory": {"instance": "root/development/preparation/inventory", "coordinator": "root/development/preparation/inventory/coordinator"},
    "plan": {"instance": "root/development/preparation/plan", "coordinator": "root/development/preparation/plan/coordinator"},
    "mode": "task-mcp",
    "repository_paths": ["src"]
  }
}
```

These are fields inside `composition`. Every inventory leaf explicitly selects role `inspector`; every plan leaf selects `planner`. The coordinator consumes every other member, and a terminal all-join covers the entire group. A one-member group uses the same shape. Multi-role Agent references declare their actual role; backend overrides address actual leaf paths and must satisfy the definition's model floor. Preparation, work and review together cover every Agent leaf exactly once.

To select different specialists, start with the actual installed definition receipts and revise inventory and plan first. In each group, `expert-results` explicitly joins every selected expert; coordinator depends on and consumes its complete result; `done` explicitly joins every expert and coordinator, with the group result pointing to `done`. For a cross-end change, inventory selects contract/server/client/validation independently; plan starts contract and validation independently, and server/client wait for the complete contract port. The original Executor still supplies canonical inventory to every planner; inventory and plan retain independent root-task inputs in the preparation wrapper. Validation obligations and interface proposals must be reconciled by the coordinator before owner approval.

Publish the revised preparation references next, then the selected delivery's preparation reference, and finally its sole native parent reference. At each level use exact version/digest values returned by the preceding publication, preserve unchanged resources, permission ceilings and work/review references, and use unoccupied task-revision versions. Preview and freeze the final native parent, and save all actual base/publication and manifest receipts. [The executable example](../examples/composition/development-specialists/publish.py) uses the standard `workflow_definitions.revise` and `freeze_manifest` APIs for this sequence; its task demonstrates sole ownership of shared contract fixtures, separate server/client paths, and integration depending on both. The same sequence can select governance-specific experts or a one-member preparation group. Such selection creates immutable task revisions, without changing the frozen graph during execution.

`repository_paths` contains relative prefixes from the original starting commit and covers every work-unit path. `['.']` selects the entire repository. Include required build/model configuration; the trusted reader includes applicable ancestor `AGENTS.md`. Every file remains within each leaf's read ceiling. Binary/special Git objects and oversized complete material fail visibly. Skills, instructions and context accumulate along the structural ancestor chain without granting shell, network or experiment permission.

Non-coordinator inventory specialists use supplied source and existing evidence. Only the inventory coordinator runs the original trusted baseline commands and publishes canonical behavior-baseline. Every planner receives the same canonical inventory. Stage ports retain complete strict UTF-8 output bytes and their original request, receipt, claim/session, selected backend and invocation identities; the trusted `preparation-sources` artifact binds all members. The original plan reader verifies and presents those originals before approval. Work and final review consume that same approved plan; model prose cannot replace the trusted source table.

Required non-inlined Skill attachments use task-MCP's original complete-read coverage checks. Complete inlined bodies need no duplicate read. Coverage proves byte delivery, not model understanding. The complete context/prompt ceiling remains 1,000,000 bytes, with the original plan-material item limit; overflow rejects before the successor model.

Run [budgeted prepare → preview → dual-digest create](USAGE.md#一次授权的预算准备), then the original start/approval/cancellation/recovery operations. The one birth clock covers compilation, queues, human waiting, every finite member slot and cleanup. Current workers consume `.composition-v12` / `requests-composition-v12`. Optional issue sources and selected project context stay on this same schema8/input12 contract. Existing frozen records retain their original identities; this current installation does not execute removed preparation inputs8–11. Finish, cancel or reconcile them with their original installation before upgrading.

The [formal selected-MoE example](../examples/composition/optimization-selected-moe/README.md) fixes source/profile/topic inventory experts, experiment/topic/kernel planning and four final reviews in one 18-leaf native tree. Its common policy snapshot is inherited from one development ancestor. The nineteen independent topic presets retain their explicit readonly proposal interface; selecting a topic root does not automatically execute training.

<a id="完整继承与冲突"></a>
## Complete inheritance and conflicts

Each leaf assembles every ancestor's Skill instructions/context and each level's initial instructions in root→parent→self order. Composition templates add no model calls themselves. Preview provides each complete body, content identity, every source, complete assembled body and SHA; a Skill's required body is `SKILL.md`, while scripts and other directory attachments remain resources read as needed.

A logical resource ID with different content or kinds is refused. Same-named Skills are checked by their actual frontmatter loading name; different trees are refused. Matching names/trees may be merged while preserving every logical ID/source and verifying every source is readable. Last-writer-wins does not replace ancestors. Sibling/predecessor Skills are not inherited; predecessors supply only port data. Repeated references do not share mutable sessions.

A preview of complete static-material delivery does not establish model understanding, compliance or actual reading. Actual calls fix the original instance and current task body, check complete input capacity and retain loading evidence; insufficient capacity is refused without silent truncation. Formal `dag-v1` adds explicitly bound predecessor artifacts according to its frozen version (v6 uses the declared artifacts and trusted checks/opinions above); independent `run-input` still calls one leaf only.

<a id="权限路径和预算"></a>
## Permission paths and budgets

The preview grant file uses the schema's `$defs/grant`: `schema_version: 1` with complete `permissions` and `limits`. [preview-grant.json](../examples/composition/preview-grant.json) is illustrative; operators should narrow it to their projects. It is currently an explicit static input, unconnected to project configuration or formal approval.

|Permission field|Exact semantics|
|---|---|
|`read`|Array of readable logical subtrees, such as `workspace/src` and `definitions/agent/architecture-reviewer/1.0.0`; `definitions` represents the entire definition asset library.|
|`write`|Array of writable workspace subtrees, such as `workspace/src`; definition-library writes cannot be declared, and write permission does not implicitly grant reads.|
|`shell`|Whether subprocess execution is requested; a Skill script's presence does not grant this permission.|
|`network`|Array of exact canonical HTTP(S) origins, such as `https://api.example.com`; hosts must be lowercase ASCII DNS names (punycode for international domains) or IP literals, IPv6 must be compressed, and default ports omitted. Paths, credentials, queries, fragments, whitespace and wildcards are refused.|

Paths use `/` and case-sensitive path-segment containment; `workspace/src` cannot grant `workspace/src-other`. `..`, host absolute paths and globs are refused. Logical `workspace` is reserved for the project workspace at execution time; `definitions/{agent,workflow}/ID/VERSION/path` represents exact package resources. These are not current OS mount points and preview neither creates nor enforces them automatically.

The root request must fit within the grant; subworkflow requests must fit within their parents, and Agent nodes within their owning workflow. Every level is checked, transitively satisfying every ancestor. Every origin path of each required resource must fit the current instance's read scope; Skills require their entire directory to be readable. Narrowing that excludes ancestor materials fails rather than dropping materials or silently elevating privileges. Preview's `backend_request.sandbox` is only a backend request; it cannot override this chain or prove OS isolation. See [pre-call capability checks](#调用前查看能力与权限) for the actual `enforced/advisory/unsupported` loading matrix.

All four `limits` fields are required; booleans, floats and values outside supported ranges are refused:

|Field|Counting and supported ceiling|
|---|---|
|`depth`|Root depth is 1, increasing by 1 per structural node; each subtree counts its local depth from 1 while every ancestor/project depth is checked simultaneously. Maximum 16.|
|`instances`|Includes the root, every Workflow reference, every Agent and all-join; repeated references count separately. Constrained per subtree and globally. Maximum 512.|
|`concurrency`|Shared quotas per structural scope; leaf previews list every scope. Formal parallel review obeys project and all ancestor-scope ceilings together; a branch waiting on a narrow subtree does not occupy ancestor capacity. Maximum 64; independent leaf calls do not schedule the graph.|
|`material_bytes`|Total UTF-8 bytes of all leaves' complete static prompts, including source markers; repeated calls count separately. Constrained per subtree and globally. Maximum 1,000,000; future port values are excluded.|

These are hard ceilings of the bounded static format; they promise neither performance, model capacity nor execution at arbitrary concurrency. Smaller project/subtree limits can refuse oversized compositions during compilation.

Independent branches can select different backends, models and [reasoning levels](AGENT_BACKENDS.md#为每个-agent-设置思考强度). For example, set these separately in a formal task's `composition.backend_overrides`:

```json
{
  "root/structure/review": {
    "binding": {"tool":"codex","reasoning_effort":"high"},
    "reason": "结构设计审查采用较高推理强度"
  },
  "root/correctness/review": {
    "binding": {"tool":"claude-code","effort":"medium"},
    "reason": "正确性审查使用独立后端"
  }
}
```

Paths must identify actual leaves in this manifest, and every backend must pass the selected mode's capability check; the task page's composition configuration can generate the same binding. Formal review and work-unit runners start branches as dependencies become ready and shared quotas permit. Execution/review backend diversity still follows the original `diversity` configuration. `composition run-input` calls only one leaf; arbitrary mixed-node graphs and general Repeat execution remain covered by implementation plans.

These explicit per-Agent levels are retained in exact definitions and frozen task bindings. A requested value, its projection into native CLI arguments/configuration, and an actually observed native value are separate facts; without native evidence, actual application remains unknown. Unified fixed/preset/planner/automatic tuning selection remains future work; existing workflow presets do not implement tuning presets. No level/model fallback or budget increase is implicit. See the [backend guide](AGENT_BACKENDS.md#为每个-agent-设置思考强度) for mode-specific limits.

<a id="修订分享与恢复"></a>
## Revision, sharing and recovery

To change only the standard workflow document, use `show` to obtain the exact original version's `digest` and `definition`, save `definition` alone as `new-workflow.json`, and change its version, nodes or dependency references. Replace `BASE_DIGEST` with the original package digest:

```bash
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --check
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json
```

`--check` does not publish a version; omitting it publishes through the existing library. Both copy the complete original package; without resource arguments, only `workflow.json` is rewritten as UTF-8 with sorted keys, two-space indentation and a final newline. Responses include candidate identity, fixed `base` and `published`. Instructions, context, complete Skill trees, undeclared files and empty directories are retained. Change resources through resource revision below or export/edit/check/import. This entry accepts a complete JSON document or YAML with `--format yaml`; page operations follow below.

Unlike single-package `composition check`, `revise --check` resolves complete recursive dependencies using the current library and checks backend/role admission, inheritance, permissions, resources, ports and budgets. Dependencies must already be published with exactly matching digests. It uses no project grant and does not approve execution; preview the entire chain with an explicit grant after publication. Original-digest mismatch or current admission failure is refused; different content cannot be published at the same version, and the original remains unchanged. Checking reserves no version, so concurrent version conflicts may prevent publication; identical publication can be retried.

HTTP `POST /api/workflow-definitions/{id}/{version}/revisions/check` and `/api/workflow-definitions/{id}/{version}/revisions` check and publish respectively, with JSON `{"base_digest": "原包的64位小写摘要", "definition": {完整的新正文}}` (the original package's 64-character lowercase digest and complete new document). CLI and HTTP share candidate digests and existing validation; neither starts models, services or tasks.

Resource operations follow the same contract as [Agent resource revision](AGENT_DEFINITIONS.md#修订完整资源文件). Prepare `resource-changes/changes.json`, `files/<包相对路径>` (package-relative path), and complete `new-workflow.json` (with valid placeholder digests for new declarations). Preview first, review and save the suggested response document as `new-workflow.json`, then explicitly accept, check and publish:

```bash
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --preview-resources > resource-preview.json
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --accept-candidate ./resource-preview.json --check
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --accept-candidate ./resource-preview.json
ergora composition file kernel-delivery 1.0.0 instructions.md --base-digest BASE_DIGEST --offset 0 --limit 65536
```

Explicit operations derive binary attachments, complete Skill trees, executable bits and empty directories within the same package; unchanged content is retained. Take filenames from the original package's `show` response `files`; windows are returned as base64, and you must follow `next_offset` and combine every byte. HTTP uses `POST /api/workflow-definitions/{id}/{version}/revisions/preview-resources` and `/files/read`; requests and final `resource_changes/accepted_candidate` fields match Agents. Preview, checking and publication all perform complete recursive admission; historical file reads do not require a currently available backend. Complete candidate acceptance binds ordinary attachments and every directory; changing documents or operations requires a new preview. Preview neither elevates permissions nor approves execution. The page's “Resource and attachment editing” can read/upload complete files, stage operations and explicitly accept resource digests; use the CLI or full export/edit for larger changes. See [revise workflow resources on the page](#在页面修订工作流资源).

Parents/children can jointly plan permission increases or additional resources: create new child-definition versions, update parent references/permissions level by level, publish a new root, then check the whole chain with the new project grant. Changing children alone fails, as does a root still exceeding project ceilings. Single-definition import publishes a complete object and index atomically; exact recursive references fix the complete root revision. This provides neither a cross-definition transaction nor project adoption. Old roots and versions retain their original content rather than substituting new active heads.

Joint revision is not a cross-library atomic transaction. Interruption or parent-check failure leaves earlier independent child versions visible; old roots, frozen manifests, task inputs and approvals keep their exact references. After repair, continue from the unfinished parent instead of automatically substituting the “latest version”.

<a id="沿完整依赖链发布资源修订"></a>
### Publish resource revisions through the complete dependency chain

For the governance composition's structure reviewer, publication order is Agent `ergora-structure-reviewer` → `ergora-structure-review` → `ergora-delivery-review` → `ergora-governance-delivery` → root `ergora-governance-template@1.1.0`. Large changes use the same inner definitions through `ergora-large-change-delivery` → root `ergora-large-change-template@1.1.0`; the training proposal's measurement chain is Agent `ergora-measurement-reviewer` → `ergora-measurement-review` → `ergora-training-proposal`. At every level, update the parent reference with the exact version and digest from the dependency's publication receipt.

1. Save a complete manifest and required leaf inputs from the old root, retaining the original version as a comparison. Preserve existing `resources` when adding materials at each level; Skills must include their entry point, all referenced files and necessary empty directories. Ordinary undeclared attachments may also remain in the package.
2. Starting with the Agent, raise each changed package's version and follow resource preview, explicit acceptance, checking and publication above. In the parent, set `nodes[].ref` to the newly published child's complete `kind/id/version/digest`, then publish the parent, root last. Checks refuse unpublished new dependencies or mismatched digests; do not invent predicted digests or edit old indexes.
3. Fully `export` each package; import frozen dependencies into the receiving library before their parents. Copying a root package alone does not provide a complete composition. For one-step sharing, run `prepare-manifest` with the new root and share the entire directory.
4. Preview the new root with an explicit grant. Check the target leaf's complete ancestor provenance, original/additional materials, permission chain and budgets, then prepare new input from the new manifest. Old frozen input still points to old materials; publishing a new root does not update it.

Resource revision does not automatically adopt definitions for projects, elevate permissions or execute anything. Training templates retain their proposal/material-review entry points; real training and adoption must pass their own experiment gates.

<a id="联合修订父子权限"></a>
### Jointly revise parent and child permissions

Permission declarations belong to Workflows and their Agent nodes. The governance composition's structure-review leaf requires checking four levels: `root` → `root/review` → `root/review/structure` → `root/review/structure/review`. Large changes use the same review chain, while training proposals' measurement chain has one fewer level. Raising only the innermost Agent-node request is still refused by its owning Workflow; merely publishing a child workflow and replacing the parent reference still leaves the parent refusing an out-of-bounds child.

|Operation order|Explicit changes required in the new revision|
|---|---|
|Innermost Workflow|Raise the selected Agent node's request and this Workflow's ceilings, check, then publish a new version.|
|Each parent Workflow|Reference the newly published child's exact version/digest and raise this parent's ceilings; check and publish, root last.|
|New-root preview|Supply an explicit grant covering the new root; the old grant still refuses it. Check unselected branches, all ancestor materials, budgets and ports.|
|Actual invocation|Prepare input from the new manifest, then use `check-input` for the selected mode/backend; static declarations add no backend capabilities.|

For example, the reserved domain `https://joint-revision.example.invalid` can check complete containment of `network` sets; this validates declarations only, so do not request the domain. Current public `text-only` and `task-mcp` calls support no tool network requests. Even when the new root/grant pass static checks, these modes' `check-input` and `run-input` still refuse before registering a run or calling a model. Other execution capabilities require a specifically supported execution entry point and project authorization.

<a id="重复实例职责和后端选择"></a>
### Repeated instances, responsibilities and backend selection

To reuse a subtemplate, in the parent's `nodes`, reference the same complete ref with different `id` values, connecting every branch requiring a join to explicit `all`. For example, `structure` and `structure-extra` can reference the same structure-review version, producing leaves at `root/review/structure/review` and `root/review/structure-extra/review`. Frozen assets save one copy of the same definition; each reference still counts instances, complete-material bytes and scope budgets separately, with its own structural provenance paths.

Two instances of the same exact subtemplate have identical internal responsibility declarations. To make one advisory, publish a new subtemplate version with its Agent node's `review_requirement` changed to `advisory`, then reference it from the parent; Workflow-reference nodes have no responsibility-override field. Independent Agent definitions and per-leaf call backend overrides own backend selection; responsibility changes cannot switch models. Run `check-input --backend codex` or `--backend claude-code` for each leaf to check current configuration/mode admission. This checks neither authentication, actual reasoning nor independence of model errors.

The library lives in State's `workflow-definitions/index.json` and `objects/<digest>/`, separate from the Agent library but sharing `definition_bundles` code. Existing `ERGORA_HOME`, `--home` and platform defaults still apply, with no new DB table. `export` exports only the current package; complete composition sharing also requires sharing/importing each referenced package in dependency order. A single root is not a self-contained distribution.

The original [complete offline backup](USAGE.md#升级与持久数据) saves both libraries. Verification checks indexes and objects plus recursive workflow references, resources, graphs and static contracts; recovery still requires the original platform, original State path and stopped writers. Library corruption is not automatically overwritten as new evidence. Explicit task definition v2 can [freeze a complete review composition](USAGE.md#为正式任务冻结审查组合), running read-only reviewers or nested serial/parallel review through the original six stages with required/advisory responsibilities. Old v2/v3 review requires every leaf to map directly to the root task through its structural ancestors without predecessor dependencies. Explicit dag-v1 v4 uses [named ports](#正式只读审查的数据端口); v5 with work-units-v1 and v6 with work-units-v2 use [specialist writer assignments](#专长执行者与原工作单元). Original owners retain formal approval and candidate evidence. A listed runtime_supported value describes static shape support only, without proving backend/service availability.

Historical `show/list/export` and backup/recovery do not require referenced backends to remain in the current catalog; they still check complete static structure and content. New `import` (including repeated import of identical content) and `preview` additionally check every Agent definition's current role/backend contract rather than skipping admission because a version was imported previously. Single-package `check` still checks local graphs/resources without accessing dependency libraries. See the [Agent guide](AGENT_DEFINITIONS.md#历史资产与当前准入) for historical readability versus current availability.

<a id="在页面修订工作流"></a>
## Revise workflows on the page

Select an exact workflow version in “Agent and composition library”. The field form supports a new version, description, root inputs/outputs, permissions and budgets; “Edit instance” selects an Agent, subworkflow or all-join to change exact references, roles, review responsibilities, predecessor dependencies, input bindings and instance permissions. Modify an Agent's backend request in its independent definition, then update this reference to the published new version/digest. Old v1 is not automatically upgraded to v2; complex documents can still be explicitly edited in JSON/YAML.

After adding an instance, select it and complete its actual ports, dependencies and permissions. Renaming synchronizes dependencies/named bindings; deletion requires fixing remaining port references. Intermediate documents may temporarily violate execution contracts, with the raw-document entry still available for repairs. The original library's “Check definition candidate” and publication checks determine complete-graph validity, ancestor permissions, resource conflicts and budgets.

Use “Apply field text” or apply JSON/YAML → “Check definition candidate” → “Publish new definition version”. The three editor buffers, raw-text synchronization confirmation, bounded history, recovery and download rules match the [Agent editor](AGENT_DEFINITIONS.md#在页面编辑专长-agent). The page provides no cross-library transaction: publish Agents/subworkflows first, then update/publish parents and finally the new root. A failed parent does not undo published child versions, change old roots or alter in-flight tasks.

The library page holds no project grant; saving root permissions is not approval. After publication, preview and freeze tasks with an explicit grant. See the [plan](plans/2026-11-09-composition-console.md) for formal-task handoff implementation scope.

<a id="查看已发布嵌套关系图"></a>
### View published nested relationships

Select an exact workflow version, confirm “Static preview ceilings JSON” and click “Preview complete composition”. Nested boxes represent structural parents/children, dashed arrows predecessor dependencies, and blue solid lines/named input-output ports data bindings. Data edges neither pass Skills nor grant permissions; the graph does not indicate that Agents have run. Repeated references to a subtemplate still appear at distinct full instance paths.

Click a graph instance or a keyboard-accessible button in the instance table to inspect complete permissions, budget/usage, ports, responsibilities and backend requests. Agent details include every ancestor resource and complete prompt body; expertise comes only from that exact Agent version. Click “Open selected exact definition” to modify its independent definition; edit instance permissions, dependencies and bindings through “Open structural parent definition”, which also owns join edits. Navigation preserves original editor buffers without automatically publishing or adopting newer versions.

The graph always comes from the labeled **published version and preview digest**; it excludes unpublished document/resource drafts. Dragging, zooming, “Locate selected instance” and “Rearrange composition graph” change display only. The tab retains layout by control directory and exact root version, and refresh rearranges it. Changing the grant clears the old graph and requires explicit preview again. If the graph component fails to load, the instance table and complete details remain available; “Dependency and named data relationships” provides a text table. Download complete data as `composition-preview.json`.

Click “Collapse FULL_PATH” in the instance table, or select a subworkflow and “Collapse selected subworkflow”. Each instance collapses independently; other instances of the same ref are unaffected, and the root stays expanded. Collapse/expand rearranges the view using the original hierarchy, hiding internal nodes/edges while retaining complete instance/relationship tables. Cross-group edges are labeled “Summary”, retaining original types/named bindings; click an edge or relationship-table ID to inspect complete original endpoints. A collapsed box introduces no execution or inheritance relationship. “Expand all subworkflows” clears all collapsed states.

“Find instances (path, responsibility, expertise, backend)” matches literal case-insensitive terms, requiring every term to match. For example, `reviewer codex` finds reviewer instances using Codex. Expertise/declared roles come only from Agent-index entries matching complete ID/version/digest; missing metadata is reported without selecting latest. Search highlights matches while retaining unmatched structure/relationships; matches inside collapsed groups are marked on their boxes. “Expand ancestors and locate”, previous/next match buttons and “Locate selected instance” expand structural ancestors and locate the original instance; selecting a hidden leaf in the instance table opens complete details without expanding it. Query, collapsed state, selection and layout live only in this page session, isolated by control directory/complete root ref and reset on refresh.

<a id="比较两个已发布组合"></a>
### Compare two published compositions

1. Under “Exact subworkflow version”, select the original root version. Draft edits do not participate in comparison.
2. Under “Preview entire nested composition”, check “Static preview ceilings JSON”, then select “Comparison target (published exact version)”. The target can be another workflow in the library; the list explicitly shows ID, version and digest without using latest.
3. Click “Compare two published versions”. Each exact version passes through the original preview entry using the same explicit grant. Either version exceeding permissions, missing references or failing compatibility displays the original refusal, without widening permissions or generating a partially successful diff. If greater permissions are needed, inspect and explicitly change the shared ceilings before retrying.
4. Under “Exact comparison of two published compositions”, inspect counts and per-path results for added, removed, changed and identical instances. Click a full path to compare permissions, responsibilities, backends, budgets, dependencies, named ports and other facts field by field, and expand both complete original instances to read all resources, provenance and assembled prompts; table buttons also support keyboard use.
5. Download before/after preview JSON separately to retain complete originals. Comparison neither publishes definitions, applies drafts nor changes the editing baseline. Switching roots or control directories clears the current comparison. Changing the target or grant requires another explicit comparison; late responses cannot restore previous results.

Object-key order creates no differences; arrays retain order, without inferring equivalence from reordered permission/dependency declarations. Comparison pairs by full instance path and retains every repeated instance of an exact Agent/workflow. Renaming appears as deletion of an old path/addition of a new one, without guessing renames. Resource content identity/order, provenance/declarations and assembled-prompt identity are displayed separately. A source-definition version change alone can alter prompt digest/byte usage without establishing changed Skill bodies. Digests reflect only compiled facts in the original preview; open exact definitions to verify non-preview fields such as Agent descriptions/expertise. See [task-page selection](#在正式任务页面选择组合) for formal execution handoff and the [C5 plan](plans/2026-11-10-composition-handoff.md) for acceptance progress.

<a id="准备完整的单叶输入"></a>
## Prepare complete single-leaf input

Use an exact instance path to prepare an independently verifiable input bundle. Complete the definition imports above, create your own UTF-8 task file `review-task.txt`, then run:

```bash
ergora composition prepare kernel-delivery 1.0.0 root/review/structure/review --grant examples/composition/preview-grant.json --task review-task.txt --directory ./prepared-review --max-prompt-bytes 30000
ergora composition verify-input ./prepared-review
ergora composition verify-input ./prepared-review --material
```

Preparation still checks current Agent admission. It neither calls models, executes predecessors/ports nor approves workflows. Operators explicitly supply the task; to send execution results to a reviewer, for example, supply the corresponding task materials yourself rather than treating this bundle as verified automatic data flow.

Input contains `request.json`, complete `composition.json`, original `task.txt`, complete `prompt.txt` and every exactly referenced package in `assets/`. Skill-directory scripts/attachments are saved together; complete resource bodies still load root→leaf. `verify-input --material` recompiles the bundled static composition and checks the complete user prompt. It remains usable after source State deletion, without depending on the current backend catalog. Verification executes neither Skills nor backends.

`max-prompt-bytes` must be 1–1,000,000, counting UTF-8 bytes of the complete user prompt; excess is refused without truncation. This does not establish model-token capacity or room for additional backend system prompts. The complete input bundle allows at most 10MB/500 files, 1000 directories and 48 levels, checked during copying too; failure publishes no partial bundle. Save only to a new directory outside immutable definition libraries. Atomic no-overwrite publication supports Linux (requiring renameat2) and Windows, failing explicitly when unsupported. Whole-tree consistency is checked before/after verification; keep input directories stable, as this does not isolate processes belonging to the same user. The input digest covers task, composition, prompt and every asset; it establishes content consistency without authenticating authors or granting execution. Definition-package limits on cross-platform executable bits and same-platform byte preservation also apply.

Input metadata uses [composition-input v1](../src/ergora/data/schemas/composition-input-v1.json), retaining referenced Agent v1 and Workflow v1/v2 formats inside the bundle. Actual calls pass admission again through the separate entry below.

<a id="调用一个准备好的叶子"></a>
## Call a prepared leaf

First [register the project](PROJECTS.md) and install/authenticate the selected [Agent CLI](USAGE.md#安装与认证-agent-cli). `prepared-review` is the complete input bundle prepared above:

```bash
ergora composition run-input my-project ./prepared-review --timeout 300
ergora composition run-input my-project ./prepared-review --backend codex --backend-reason "Selected Codex for this call" --codex-config /PATH/TO/codex.toml --timeout 300
ergora composition run-input my-project ./prepared-review --backend claude-code --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

The exact leaf definition supplies the default backend; `--backend` and `--model` override this call only. Choose a model again when switching backends rather than retaining another backend's model name. Prefer different execution/review backends; when Claude is unavailable, explicitly select Codex/ChatGPT and record why with `--backend-reason`. Failure does not silently retry another backend. Timeout is 1–3600 seconds; exit 0 means success, 1 means model failure/timeout/startup configuration or structural error, and 2 means input-bundle or mode-admission error.

Alternatively, configure the [DeepSeek Harness read-only backend](AGENT_BACKENDS.md#deepseek-harness-只读叶后端) in the exact leaf definition, retaining the full interpreter, model, API service and credential-variable reference; avoid an incomplete `--backend` override. It supports the two read-only modes in this section. Native workspace execution and formal-task recovery remain unsupported; an explicitly enabled new standalone task-MCP source supports [one explicit read-only continuation](AGENT_BACKENDS.md#显式续接一次只读会话), with the original source and its single durable continuation slot preserved.

The default mode is `text-only`. Complete ancestor instructions, context, Skill `SKILL.md` bodies and the original task enter the model. Skill attachments remain in the snapshot, but this mode has no file/command/Web/MCP tools and cannot read other materials by path or edit the project. Include candidate code and required evidence in the task body for review. Leaves requesting write, shell or tool-network permissions are refused before invocation; the example implementation leaf, for instance, cannot run through this mode. Native structured-response or interactive tools may remain.

Runs use a new empty cwd, native CLI rule/tool-disabling options and independent sessions. These constrain model tools without providing OS/network isolation; they do not isolate user processes or model-service communication itself. Backends lacking required options fail explicitly. Codex can receive explicit reasoning configuration through `--codex-config`: only model/provider/reasoning effort/service tier and provider fields such as URL and credential environment-variable references are consumed. Tool, MCP, Skill, approval and sandbox settings there do not override this mode. Omit the file when using native Codex login; Claude uses native authentication or corresponding environment variables. Do not put credentials in definitions or task bodies.

Each run saves a completely verified input copy, a new empty working directory, complete prompt, actual argv, stdout/stderr and structured results under State's `runs/`, reusing existing Agent run lists/output and complete backups. Records bind input digest, project revision, requested/actual binding and override reasons. Run lists include only resource identities/provenance; inspect complete bodies as needed against the returned `input_path` with `composition verify-input --material`. Read the returned `result` file for `summary` and `artifacts.response`; reviewers additionally provide `approve/request-changes`. Process success and review approval are evaluated separately.

Operators supply single-leaf tasks; graph predecessors and ports do not execute. The original input remains `execution_authorized: false`, and this call creates no formal candidate/approval. Formal serial/parallel scheduling, candidates and approvals use the [formal review](#正式只读审查的数据端口) and [work-unit](#专长执行者与原工作单元) entries above.

<a id="按精确-id-读取原组合运行"></a>
## Read an original composition run by exact ID

`agent runs` lists only the latest 100 records; `agent output` provides bounded stdout/stderr. To obtain an original composition run's complete input and structured result, use its exact ID:

```bash
ergora composition inspect-run my-project RUN_ID > ./original-run.json
ergora --home /path/to/control-directory composition inspect-run my-project RUN_ID \
  --max-result-bytes 16777216 > ./original-run.json
```

This reads the original record by project/ID and the complete input, invocation prompt and result in its original `runs/` slot under the current control directory. It requires no source repository, backend program, authentication or network. After copying the complete control directory, historical metadata's absolute paths remain unchanged, while reading uses the original slot under the new directory. Do not copy only the database and discard run files. Ordinary old `agent run` still uses `agent output`; this complete reader targets original composition runs such as `composition run-input`.

Returned `run` preserves original status and actual backend/reason. `input.available` verifies complete input against its original digest/request/prompt identity; `prompt.available` independently verifies the original invocation prompt's SHA/byte count against its record. When input is also verifiable, the frozen prompt is compared byte for byte and `prompt.input_compared: true` is set. Unverifiable input leaves this false without preventing preservation of invocation-prompt identity that still matches its record. `result.available` verifies the complete original result SHA and reads its JSON, placing the body in `result.document` without truncating it to a stdout preview. Default result capacity is 8,388,608B; excess explicitly reports unverifiable and can be reread with a larger positive integer capacity. Original saved content remains unchanged.

Each missing item, identity mismatch or excess gets its corresponding `error`; other verifiable materials and the original run status remain visible. Successful observation reads return 0; scripts must inspect each `available` and `run.status`, rather than treating exit 0 as completed review. This reader neither reruns current backend/schema admission nor upgrades historical results to formal approval; downstream reports interpret advice through the trusted reviewer contract.

Original invocation prompts come from shared backend storage at `protocol/prompt.txt`. Actual transport may use stdin or backend request files, so this observation cannot certify stdin delivery for every backend. Read original native history through the [backend guide](AGENT_BACKENDS.md). Preserve and reconcile failures/unknowns first rather than automatically resending model calls.


<a id="在页面修订工作流资源"></a>
## Revise workflow resources on the page

Select an exact subworkflow version in “Agent and composition library” and use “Resource and attachment editing”. Complete reads/binary uploads, explicit write/delete/mkdir, diff previews and digest acceptance share the [Agent resource steps](AGENT_DEFINITIONS.md#在页面编辑资源与附件) session contract. Apply the document with a higher version and resource declarations first, then stage file operations, preview/accept, check and explicitly publish. Continue later additions from the complete accepted operation set; original packages and old manifests remain unchanged.

Document, operations and acceptance identity undo/redo together; unapplied drafts remain separate. Unapplied content or stale digest acceptance prevents publishing an old snapshot. Recheck after refreshing; damaged/quota-exceeding buffers can download complete working bytes, excluding unedited original packages. HTTP's total limit including base64 is 4,000,000 bytes; use CLI `composition revise --resources` for larger changes. This creates no separate server draft store or automatic upload session. The current page revises only the selected definition; joint parent/child permission increases and new-root references still require explicit new versions. Adding Skills/context expands no execution permissions.

<a id="调用前查看能力与权限"></a>
## Inspect capabilities and permissions before invocation

Before actually invoking a model, check the same input, backend and mode:

```bash
ergora composition check-input my-project ./prepared-review
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend codex
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend codex --codex-config /PATH/TO/codex.toml
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend claude-code --backend-reason "Independent review backend"
```

This command shares current admission with `run-input`. The result's `policy.permission_ceilings` lists the complete structural permission chain from supplied grant through root to leaf; `requested_permissions` is the leaf request, and `context.resources` retains every ancestor/self resource source. Read paths are permission ceilings; listing workspace does not automatically supply project-file tools. Support for complete inline materials and fixed attachments is displayed separately; text-only does not claim readable attachments.

`policy.capabilities` divides support into `enforced` (mechanisms implemented by trusted CLI/task-URI services), `advisory` (requests/prompts without enforcement guarantees) and `unsupported` (no corresponding capability). Codex actually sends a read-only request without claiming host isolation; Claude disables native tools without additionally requesting an OS sandbox. Task MCP provides only list/read for fixed declared materials; live workspace access, writes, shell, tool-network origins and external MCP remain unsupported. Infrastructure inference HTTP, stdio processes and log/state writes still exist.

This is an implementation contract and current admission report; it starts no server/model, creates no run and checks neither CLI version nor authentication. With Codex's `--codex-config`, check/run share reasoning-field parsing; unreadable files, invalid TOML, invalid provider tables or unencodable fields are refused before run creation. It does not verify provider acceptance, model availability or adequate capacity; Claude ignores this Codex-specific option. Task-mcp checks only Linux and top-level SDK presence; actual SDK compatibility/connection is preflighted at runtime. A successful check is not formal approval, and `formal_execution_authorized` remains false. Actual execution reruns admission and saves the same `policy` structure rather than treating an earlier check as an authorization token.

<a id="通过任务-mcp-读取固定附件"></a>
## Read fixed attachments through task MCP

On Linux/WSL2, install the optional dependency in the same Python environment that runs Ergora. From the repository root:

```bash
python -m pip install '.[task-mcp]'
ergora composition run-input my-project ./prepared-review --mode task-mcp --backend codex --codex-config /PATH/TO/codex.toml --timeout 300
ergora composition run-input my-project ./prepared-review --mode task-mcp --backend claude-code --timeout 300
```

This mode retains complete inlining of ancestor instructions, context and Skill guidance, additionally providing the model with the `ergora_task` service's `list` and `read` tools. Use `list` to inspect virtual URIs, then `read` for this leaf's and all structural ancestors' declared materials/Skill attachments. Ordinary bodies expose only declared files; Skills expose their complete frozen directories. Sibling templates, undeclared neighboring files, the entire input asset library and live project files remain unavailable. Materials do not execute as programs; write, shell and tool-network requests are still refused before invocation.

Each call produces a separate [task-mcp-scope v1](../src/ergora/data/schemas/task-mcp-scope-v1.json), retaining original bytes, digests and provenance. Limits are 10MB/500 files and 16MB for the complete serialized scope; excess is refused. After verifying scope, the service queries memory only and never treats model-supplied URIs as host paths. Fixed-resource reads on Linux use non-link-following file descriptors at every level, refusing symlinks/hardlinks/special files. On Windows, this new mode currently gives Linux/WSL2 guidance; existing Windows features remain available.

`list(path="",offset=0,max_entries=100)` pages authorized URIs, with up to about 64KiB of entry metadata per page; `read(path,offset=0,max_bytes=65536)` pages bytes. Responses include file size, SHA256 and `next_offset`; decodable chunks use UTF-8, while binary chunks or encoding-boundary splits explicitly use base64. Follow `next_offset` for complete content instead of treating one tool response as a whole directory or file.

<a id="核验完整附件读取"></a>
### Verify complete attachment reads

When a task requires complete inspection at every level, explicitly require it in the task file: page through every URI, then read each from offset 0 to `next_offset:null`, including all ancestor instructions/context, every Skill's `SKILL.md` and every referenced attachment. If a UTF-8 window splits a multibyte character and returns base64, reread the same offset with smaller `max_bytes`, then advance through successful text pages. Handle actual binary attachments as complete base64 bytes without executing them. Empty directories remain in the complete bundle without becoming readable files; ordinary undeclared attachments do not automatically enter task scope.

Neither successful execution nor final `approve` proves complete attachment reading. Compare frozen input, `task_mcp.scope` URI/size/SHA/provenance and actual list/read responses in this call's native events. Successful pages for every file should continuously cover original bytes; retain failed/repeated windows. Scope records available materials; native read records show which bytes the model actually requested in this call. Prepared input remains usable after the source library moves; verify and retain both source library and complete input first to avoid deleting the only copy.

MCP configuration is generated for this call only. Codex selects only this server's two tools; native MCP resource discovery/response or interactive entries may remain. The service registers no additional resources/templates/prompts. Claude uses `--bare --restricted`, empty native tools and strict explicit MCP; bare mode uses only its supported API-environment authentication without reading ordinary OAuth/keychain credentials. Users requiring OAuth login can continue using text-only or set backend-supported API environment variables for this mode; credentials need not enter definitions, scope or chat. Backends do not automatically share model names or authentication.

The run record's `task_mcp` contains frozen scope identity, preflight results and this call's native connection receipt. Preflight and native receipts are separate; the latter requires an actual SDK-successful `tools/list` for this scope with exactly list/read tools. Old handshakes and newer handshake-free requests record their actual protocol and `handshake_observed` separately. Missing actual service receipts fail the run even when final model JSON succeeds. Scope/receipts follow complete State backups, while run lists retain only summaries; this provides no OS isolation or expanded template/project authorization.

Execution also checks task-MCP transport errors already reported by this native backend. Even if the model later reconnects and returns a valid result, this run remains failed with original stdout retained. Server-side domain refusals such as unknown resources or invalid URIs allow correction and continuation; they do not equal connection failure. In this mode, Claude saves original stream-json events and extracts the final structured result; ordinary native/text-only output handling remains unchanged. This check provides no continuous heartbeat and cannot detect silent disconnection without later calls or native error events.
