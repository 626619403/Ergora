# Workflow data and execution contracts

English · [Documentation](../../README.md) · [简体中文](../../zh-CN/definitions/workflows/contracts.md)

## Structural inheritance, control dependencies and named data

Template “parent/child” relationships are versioned data relationships, and specialist Agents are independent complete definition packages; no Python subclass is needed per expert. The same exact definition can be instantiated multiple times; complete instance paths distinguish permissions, material sources, concurrency counts, backend selection and sessions.

|Relationship|Meaning|Existing rules|
|---|---|---|
|Structural parent/child|Workflow nests Workflow or Agent instances|Each leaf accumulates declared Skills / instructions / context from all structural ancestors, then its own materials; it does not read private materials of siblings or control predecessors|
|Control dependency|`depends_on` determines runnable order; explicit all-join waits for listed branches|Static bounded DAG rejects cycles; formal stages execute only supported projections, without canvas rescheduling|
|Named data|Inputs bind to parent inputs or outputs of declared dependencies|Ports create neither inheritance nor permissions; actual values are delivered after original producer receipt and declared-artifact verification|

Each Workflow's permissions are constrained by its structural parent and the operator's explicit grant; each Agent node is further constrained by its Workflow. Writes are permitted only within declared workspace scope. If a narrower read scope makes inherited material unreadable, compilation refuses rather than dropping ancestors' material and continuing. Identical material bytes may be deduplicated, but all logical IDs and sources remain; identical IDs with different content, or identical Skill load names with different trees, are rejected.

Adding resources still requires access along the complete parent chain; permission elevation requires publishing new exact versions of the necessary parents and children and updating references, root last, without bypassing parents. Ordinary package attachments do not enter scope merely by being packaged. Limits include each ancestor instance's material budget and concurrency quota; overflow is explicitly rejected rather than truncated and called complete inheritance. Complete definitions / admission and actual page-by-page model reading are different evidence; the latter requires original `list/read` replies.

## Definitions and data flow

The package entry point is `workflow.json`; see [schema v1](../../../src/ergora/data/schemas/workflow-definition-v1.json) and [schema v2](../../../src/ergora/data/schemas/workflow-definition-v2.json). Only JSON is accepted, with an optional UTF-8 BOM; duplicate JSON keys and unknown fields are refused. Package trees and resources follow the [Agent package](../resources.md#resource-and-storage-boundaries) contract for digests, paths, sizes, directory limits and same-platform recovery.

|Field|Consumer and meaning|
|---|---|
|`schema_version`, `id`, `version`, `description`|Version-library and CLI display; format version is strictly integer 1 or 2, IDs use lowercase kebab case, versions have three exact numeric parts, with no implicit latest.|
|`resources`|Ordered local instructions/context/Skills; may be empty. Reuses Agent resource formats and complete digest checks.|
|`inputs`|Array of input-port names; mappings are checked statically, and formal `dag-v1` projects the root task or completed predecessors' named outputs using frozen bindings.|
|`outputs`|Output port → source binding, from this workflow's inputs or local nodes' outputs.|
|`nodes`|Agent references, Workflow references, all-join and the Workflow v2 `verify-evidence` and `choose-agent` operations determine instances and the local graph.|
|`permissions`|This workflow's request/child ceilings; checked along the complete structural ancestor chain and against the project grant.|
|`limits`|This subtree's depth, instance, concurrency and complete static-material ceilings; root/project totals cover every subtree.|

Agent/Workflow references require `kind`, `id`, `version` and `digest`. `digest` identifies the entire package tree and is available from `check/import/show`; it is not a single JSON file's SHA. Each node has a unique local `id` and explicit `depends_on`. Agent nodes also have `role`, `permissions` and exactly one `task` input; their result port is fixed as `result`, and the target Agent must support the role. Workflow-node inputs/outputs are declared by the exact target version.

Bindings can only be `{"input":"task"}` or `{"node":"implement","output":"result"}`. A node referencing another node's result must list it as a direct dependency; references do not implicitly add dependencies. There are no Python expressions, arbitrary scripts or loops. Port values are opaque data consumed at execution time; static checks do not establish trust in a candidate, review decision or domain artifact.

`{"id":"gather","join":"all","depends_on":["structure","correctness","test-value"]}` declares a join whose intended `result` output is a map of every dependency branch's complete named outputs. A join is a data barrier waiting for all listed branches. Formal read-only parallel review requires the root output to point to an explicit all-join covering every leaf; the original trusted runner checks each required branch's candidate, session and receipt before producing an aggregate reference. Static all-join alone is neither majority voting nor human approval.

## Original fixed verification evidence

Use `operation: "verify-evidence"` in a Workflow v2 definition and execute it through the standalone graph route. The compiler records the instance as kind `verify-evidence`. Its `source` binding must trace through Workflow input ports to an explicitly supplied root input. This applies to nested workflows as well as the root. The fragment below exposes the operation's fixed `result` port as a Workflow output.

```json
{
  "schema_version": 2,
  "inputs": ["source"],
  "outputs": {"evidence": {"node": "verify", "output": "result"}},
  "nodes": [
    {
      "id": "verify",
      "depends_on": [],
      "operation": "verify-evidence",
      "inputs": {"source": {"input": "source"}}
    }
  ]
}
```

The locator binds the original `task_id`, `run_id`, `event_id`, `candidate_sha` and `receipt_sha256`. The native reader revalidates the exact successful fixed-verify job against the original history and complete check-results and process records. Missing or mismatched evidence fails the node. A successful read returns the locator, original project and project revision, `check_results_sha256`, `fixed_check_ids` and `status: validated`. The read leaves check execution, approval, release and changes to the original task with their existing formal owners. [Standalone graph input and runtime requirements](compose.md#read-original-fixed-verification-evidence)

## Conditional Agent routing

A Workflow v2 `choose-agent` node takes its `source` from the `result` of its sole dependency, a sibling analyzer Agent. Declare one to eight distinct sibling Agent IDs in `branches`, in order. Each branch depends directly on the selector and can use unconditional inputs. Each analyzer supplies one selector, and each branch belongs to one selector. The original analyzer reply includes required `artifacts.route`, a string enum of those local IDs plus the reserved `none` for an explicit no-follow-up decision. The existing Agent runner validates and saves the original result. A missing or invalid route fails the graph before any branch dispatch.

The selector's `result` contains the chosen local ID or `none`, for example `{"choice":"structure"}`. Use an all-join to depend on a conditional branch or expose its output. The join maps each skipped branch's full instance path to `{"status":"skipped"}` and each executed branch's path to its usual `{"result":...}` wrapper. A conditional branch cannot feed another branch or act as another selector’s analyzer. Formal task admission rejects `choose-agent`. [Define and run a conditional workflow](compose.md#choose-a-follow-up-agent)

Each `run.json` entry in `route_decisions` binds the selector decision to the analyzer's exact source instance, original run ID, input digest and result digest. It records eligible and skipped full instance paths in declaration order and the chosen path or null. Use the saved analyzer run ID with `composition inspect-run` to read the original input and reply.

## Static required and advisory review declarations

WorkflowDefinition v2 requires every Agent node with `role: reviewer` to explicitly declare `review_requirement: required` or `advisory`. This is a workflow-instance responsibility; the same specialist may have different responsibilities at different nodes. AgentDefinition remains v1. Other roles, subworkflow references and joins do not accept this field. To change a nested review leaf's responsibility, save a new child-definition version and update exact references along the parent chain. Permission, Skill and context inheritance rules remain unchanged.

For example, [review-requirements](../../../examples/composition/review-requirements/workflow.json) makes structure review required and test-value review advisory:

```bash
ergora composition check examples/composition/review-requirements
ergora composition import examples/composition/review-requirements
ergora composition preview review-requirements 1.0.0 --grant examples/composition/preview-grant.json
ergora composition prepare-manifest review-requirements 1.0.0 --grant examples/composition/preview-grant.json --directory ./review-requirements-manifest
```

First import the structure reviewer and test-value reviewer from the beginning of this guide. Preview displays each leaf's declaration; any recursively referenced v2 definition makes `composition-preview.schema_version` 2, and complete bundles/backups preserve the original identity. All-v1 compositions retain their preview version and bytes; active templates do not downgrade historical members.

Formal development supports this composition; see [freeze a review composition](../../development/preparation.md#freeze-a-review-composition-for-a-formal-task). It must contain at least one required reviewer, and every required and advisory branch must finish. In the new responsibility graph, the selected output must point to an explicit all-join covering every member, even a single member; old v1 single-leaf graphs retain their runtime contract. Only after checking the same candidate, independent sessions, complete artifacts and actual model opinions does the trusted runner allow an advisory `request-changes` into the join with its original findings. Its original receipt remains `FAILED`, and the join records responsibility and opinion. Required requests for changes, runtime failure, missing output, timeout, contract violations and unconfirmed cleanup still block progress. Independent `run-input` calls only the selected leaf; it neither aggregates the workflow nor produces formal approval.

## Data ports for formal read-only review

[serial-review](../../../examples/composition/serial-review/workflow.json) reuses three independent subtemplates: structure review finishes first, then correctness and test-value reviews run in parallel, followed by explicit all-join. After importing the specialists and three subtemplates at the beginning of this guide:

```bash
ergora composition import examples/composition/serial-review
ergora composition prepare-manifest serial-review 1.0.0 --grant examples/composition/preview-grant.json --directory ./serial-review-manifest
ergora composition verify-manifest ./serial-review-manifest
```

Within the user task definition v2's `composition`, explicitly set `review_protocol: "dag-v1"` and provide this manifest's path and digest, then [preview, create, start and approve the plan](../../development/tasks.md#formal-task-sequence-and-recovery). The saved formal envelope is v4, with a separate queue/request-root; tasks without this field retain their v2/v3 contract without automatic upgrades. This remains review within the original six stages, without additional inventory, planning or verify execution. All members are read-only reviewers, at least one required; writer assignment is outside this entry point.

The structural parent determines ancestor resources and permissions; `depends_on` controls order alone, and `inputs/outputs` select data sources. Reviews connected only by control dependencies still enter the final aggregate but do not automatically become downstream prompts or Skills. A nested Workflow publishes named outputs only after all its nodes finish and may have multiple outputs. The selected review subtree has one terminal output; its projection chain must end at explicit all-join, and the transitive closure of completion dependencies must cover every reviewer, including serial upstream reviewers.

Each input uses `bindings` to map to `task` or a stable `实例路径#端口` (instance path#port); the `values` table stores unique values. A join value references all named outputs of each direct dependency, and repeated template instances retain distinct paths. In the actual model input, `review_inputs.results` provides original stages, receipts and digests, and every original artifact's complete body for all bound review sources. Original request/context/receipt/claim, candidate and actual read SHA are checked before invocation. Advisory request-changes can flow downstream with their FAILED originals retained; runtime failures cannot supply valid port values.

Dynamic ports and complete predecessor bodies are inlined into the actual prompt. Task-mcp still exposes only this leaf's and its structural ancestors' fixed resources, without automatically opening siblings' or predecessors' host files. All ancestor materials and original predecessor artifacts count toward the 1,000,000-byte complete-input limit. A shared table avoids recursive expansion of the same join value, but bodies inside different audit artifacts may still repeat, so long audit chains can exceed the limit early; execution then stops explicitly without truncation or omission. Original runtime owners retain cross-member session isolation, ancestor concurrency limits, cancellation, unknown-result reconciliation and history recovery.

## Specialist writers and original work units

[specialist-work](../../../examples/composition/specialist-work/workflow.json) assigns implementation and validation to two independent specialist definitions, passing original artifacts from the former to the latter after completion; [specialist-delivery](../../../examples/composition/specialist-delivery/workflow.json) connects the work join to three parallel reviews. These reuse the original six stages: inventory, plan and owner approval happen once, followed by the original work units, integrate, trusted verify and review.

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

`backend_overrides` selects backends, models and reasons separately for all actual writers and reviewers. The initial workspace mode supports Codex on Linux/WSL2 and requires explicitly selecting `{"tool":"codex","sandbox":"current-container"}` for every writer; the outer project must also confirm the current container through [trusted execution configuration](../../agents/formal-execution.md#optional-formal-six-stage-execution-bridge). Example Agent definitions retain ordinary Codex bindings; isolation requirements are not lowered automatically without this explicit choice. The new workspace mode does not support Claude/arbitrary commands/mini-swe-agent and refuses them before execution; their existing modes remain unchanged. Review can select another backend; `prefer-distinct` requires an explicit fallback reason for the same backend. Diversity compares all actual writers rather than the project's default implementer.

Work inherits and narrows the complete permission chain; every path in each original unit must fall wholly within its effective write scope (logical prefix `workspace/`). The Executor still owns independent checkouts, dependency-commit merging, path gates, deterministic checks, cancellation fences and trusted commits. Agents cannot commit or move HEAD; invalid results do not reach successors. Every writer simultaneously obeys original unit concurrency, executor capacity and all structural ancestor limits.

`work-units-v2` publishes formal envelope v6 using a separate `composition-v6` queue and request root; new execution compositions created on the page select this protocol. Task JSON may still explicitly select `work-units-v1`, publishing the original v5 contract. Existing tasks retain their versions through tool upgrades. `composition check-input/run-input` remain read-only; preparing an input bundle cannot authorize a writable call. Native workspace tools can access the current user's files; prompts and the final Git gate constrain permission paths, without enforcing isolation of every in-flight file access or network egress. Fixed task MCP still provides only this leaf's and its ancestors' declared materials. Use a separately supported execution environment for strong isolation or external MCP; this mode does not supply those capabilities. Existing Windows installation, definitions and compatible readers remain; use WSL2 for the new write path.

Actual work input contains all ancestor instructions, context, Skill bodies/attachment entry points and the approved plan. In v6, `stage-artifacts-v1` passes every declared stage artifact and trusted check/opinion: the profile's `artifacts_by_stage`, work's trusted `test-results`, verify's trusted `check-results`, every checks reference in the receipt, and review's trusted `composition-review-decision`. These bodies are fully inlined; model summaries are not the artifacts promised by this contract. Complete originals such as logs, previous prompts and MCP audits remain in original receipt indexes, `task evidence` and offline handoff, without recursively copying them again as downstream results. Retaining an index does not establish that downstream models read the complete audit.

In v6, `work_inputs.results` stores the union of port sources and direct work dependencies by instance path; `dependencies` maps unit IDs to instance paths. Each source is delivered once. Control dependencies without bound data ports still deliver their declared artifacts/trusted checks; control edges add no ancestor Skills. Review still receives the original plan/verification and bound sources. v2–v5 retain their complete artifact-inlining contract, where long audit chains can still exceed budgets; choose the v2 protocol for new tasks rather than altering old tasks to erase failure records.

Original request/context/admission, actual binding/session, claim, formal-call/invocation/selection, every byte of receipt artifacts and Git ancestry are still checked; v6 audits omitted from inlining must also remain intact. Work ports are not review opinions, and trusted readers still validate review opinions. Integrate/verify, the final candidate and original approved plan remain mandatory before review. v5/v6 reference fully saved admission by digest, preserving the original manifest and complete ancestor resources. The complete-input ceiling stays at 1,000,000 bytes; genuinely oversized declared artifacts or ancestor materials are refused before invocation without truncation.

Original attempt/monitor/unknown and cancellation-recovery rules remain. Recovery after the original call and commit finish but before receipt publication reuses the same job/context and monitor artifacts. If HEAD has changed, verify the complete invocation evidence saved by the original Executor after its first HEAD gate; missing or mismatched evidence is refused and requires reconciliation. Without reliable external results, retain unknown status rather than redispatching a writer or changing IDs. After a run, use `agent runs` and formal `task evidence` to read original calls/artifacts, and export offline handoff for the original task.

## Complete inventory and planning materials

Use current [task-definition schema8](../../../src/ergora/data/schemas/task-definition-v8.json), producing formal input12. Inventory and plan each select a readonly workflow subtree and a canonical coordinator. The original six-stage owner runs ready experts within the frozen ancestor concurrency limits, passes complete predecessor originals to the coordinator, waits for owner approval of the canonical plan, and retains trusted checks, candidate identity and cleanup.

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

Publish the revised preparation references next, then the selected delivery's preparation reference, and finally its sole native parent reference. At each level use exact version/digest values returned by the preceding publication, preserve unchanged resources, permission ceilings and work/review references, and use unoccupied task-revision versions. Preview and freeze the final native parent, and save all actual base/publication and manifest receipts. [The executable example](../../../examples/composition/development-specialists/publish.py) uses the standard `definitions.workflows.revise` and `freeze_manifest` APIs for this sequence; its task demonstrates sole ownership of shared contract fixtures, separate server/client paths, and integration depending on both. The same sequence can select governance-specific experts or a one-member preparation group. Such selection creates immutable task revisions, without changing the frozen graph during execution.

`repository_paths` contains relative prefixes from the original starting commit and covers every work-unit path. `['.']` selects the entire repository. Include required build/model configuration; the trusted reader includes applicable ancestor `AGENTS.md`. Every file remains within each leaf's read ceiling. Binary/special Git objects and oversized complete material fail visibly. Skills, instructions and context accumulate along the structural ancestor chain without granting shell, network or experiment permission.

Non-coordinator inventory specialists use supplied source and existing evidence. Only the inventory coordinator runs the original trusted baseline commands and publishes canonical behavior-baseline. Every planner receives the same canonical inventory. Stage ports retain complete strict UTF-8 output bytes and their original request, receipt, claim/session, selected backend and invocation identities; the trusted `preparation-sources` artifact binds all members. The original plan reader verifies and presents those originals before approval. Work and final review consume that same approved plan; model prose cannot replace the trusted source table.

Required non-inlined Skill attachments use task-MCP's original complete-read coverage checks. Complete inlined bodies need no duplicate read. Coverage proves byte delivery, not model understanding. The complete context/prompt ceiling remains 1,000,000 bytes, with the original plan-material item limit; overflow rejects before the successor model.

Run [budgeted prepare → preview → dual-digest create](../../development/preparation.md#prepare-under-a-single-budget-authorization), then the original start/approval/cancellation/recovery operations. The one birth clock covers compilation, queues, human waiting, every finite member slot and cleanup. Current workers consume `.composition-v12` / `requests-composition-v12`. Optional issue sources and selected project context stay on this same schema8/input12 contract. Existing frozen records retain their original identities; this current installation does not execute removed preparation inputs8–11. Finish, cancel or reconcile them with their original installation before upgrading.

The [formal selected-MoE example](../../../examples/composition/optimization-selected-moe/README.md) fixes source/profile/topic inventory experts, experiment/topic/kernel planning and four final reviews in one 18-leaf native tree. Its common policy snapshot is inherited from one development ancestor. The nineteen independent topic presets retain their explicit readonly proposal interface; selecting a topic root does not automatically execute training.

Continue: [Inherited resources, permissions and static budgets](permissions.md) · [Prepare a task's frozen composition](../../development/preparation.md).
