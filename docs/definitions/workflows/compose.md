# Compose and freeze a workflow

English · [Documentation](../../README.md) · [简体中文](../../zh-CN/definitions/workflows/compose.md)

Workflow packages compose exact versions of specialists or subworkflows into a bounded DAG. A structure-review template can stand alone, or structure, correctness and test-value templates can run in parallel and be chained with an execution template. The structural parent chain determines inheritance; work dependencies pass data only through named ports.

`composition` provides static checks, an immutable version library, complete previews, portable static composition bundles and explicit single-leaf calls. Previews do not call models; `run-input` can pass prepared input to the selected backend. Formal development follows the [six-stage process](../../development/tasks.md#formal-task-sequence-and-recovery); its review stage supports nested read-only serial/parallel branches with explicit all-join barriers. See [formal review compositions](../../development/preparation.md#freeze-a-review-composition-for-a-formal-task) for configuration, [the formal DAG protocol](contracts.md#data-ports-for-formal-read-only-review) for read-only review ports, and [the work-units-v2 protocol](contracts.md#specialist-writers-and-original-work-units) for specialist writer assignments.

The Web console's “Agent and composition library” reuses the same version library, import and preview use cases without requiring project registration. Select an exact workflow version, inspect the static ceilings initialized from its root declaration, and explicitly preview it to see every instance's structural parent chain, predecessor dependencies, named ports, complete resource provenance and assembled prompt; see [page operations](#browse-and-preview-definitions-in-the-page). Static ceilings do not authorize a project, and backend fields are requests. Downloaded definition JSON and preview JSON support reading and comparison; share complete resources and exact dependencies through `export`, `prepare-manifest` below or [freeze the current preview](#freeze-the-current-preview-into-the-persistent-control-directory). [Explicitly revise](revisions.md#revise-workflows-on-the-page) the standard document on the page; see the [workflow guide](revisions.md#view-published-nested-relationships) for the nested canvas and formal handoff.

Import, preview and manifest freezing provide static graph artifacts. The [standalone graph command](#run-a-standalone-workflow-graph) explicitly runs supported read-only graphs. General Repeat and arbitrary mixed-node graph execution remain unimplemented. Registered design policies currently store requirements only and visibly refuse unsupported execution; the trusted human channel is unavailable. Inspection-only [source-journal records](../../development/design-and-approval.md#store-complete-design-sources-and-reported-answers) do not grant execution; finite training controllers require [explicit authorization](../../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization). See the [current plan](../../PLAN.md), [design-policy execution guard](../../../src/ergora/development/design.py) and [training-controller guard](../../../src/ergora/training/cycles.py).

## Run a standalone workflow graph

Create an ordinary local project and use a complete manifest plus its digest. Supply a JSON object with exactly the root input port names. A root declaring `task` can use `{"task":"Read the supplied structure and summarize the dependencies."}`.

```bash
ergora composition run-graph my-project ./complete-manifest --manifest-digest MANIFEST_DIGEST \
  --inputs ./graph-inputs.json --directory ./original-graph-run --max-prompt-bytes 150000 --timeout 300
```

The command schedules read-only, text-only Agent leaves when their declared dependencies are satisfied and the frozen project, root and ancestor concurrency limits allow another call. With a free slot, a successor can start while an unrelated branch is still running. Nested workflows pass data through their declared ports. Each Agent leaf supplies its complete structured reply as `result`, and an all-join maps the outputs of all its declared predecessors by exact instance path.

The graph coordinator records each original Agent attempt and run ID in `run.json` before launch, then checks the current stop, completed calls and result capacity again. An attempt stopped before the Agent runner starts is recorded as `not_dispatched`. One deadline covers the whole graph. On failure, cancellation or timeout, the coordinator stops dispatch and waits for the original process owners to stop and collect active calls. Ctrl+C requests cancellation through those owners. On Linux/WSL2, SIGTERM uses the same path.

Read `run.json` in the selected directory for the original manifest, inputs, attempted Agent run IDs and named outputs. Use `composition inspect-run` to read each original leaf, including completed leaves from a failed or interrupted graph. The graph retains up to 8 MiB of complete verified leaf results and caps its final output at 8 MiB. Exceeding either limit fails the graph with the original leaf records available. `run-graph` takes an unused directory and returns a nonzero status when the graph ends without complete success.

### Observe an original graph run

After an interrupted run or a lost reply, use the original control home, project, run directory and manifest digest. The command opens the existing control database read-only. SQLite can create or update WAL coordination sidecars during a shared read. The command issues no writes to project records or the graph receipt and does not migrate the database.

```bash
ergora --home ROOT composition inspect-graph PROJECT DIRECTORY --manifest-digest SHA256
```

The reader verifies the frozen manifest and reports its root, the saved `run.json` status and digest, the recorded output port names and Agent attempts in reservation order. Each attempt includes the reserved input identity and separate observations of the original Agent run, input, prompt and result. For example, a saved `attempted` entry can have an observed `succeeded` Agent run while the graph receipt still reads `incomplete`. Use the original Agent run ID for complete result content. [Read an original leaf by ID](leaf-calls.md#read-an-original-composition-run-by-exact-id)

In `route_decisions`, a `corroborated` choice matches the frozen branch list and the original analyzer's verified result. For `verify-evidence`, the report shows the graph-recorded locator and evidence status with the original native receipt marked `not_queried`. Per-leaf `original_run.process_start` shows the original Agent run's historical direct-child observation. The graph-level `process_start` and `stop_and_cleanup` report `unknown`. Inspection is for observation only. Repeat the read with the same identifiers when more evidence becomes available.

For a recoverable run, `recovery.authorization.state: corroborated` means that the saved authority matches the selected graph, original directory, control home and lock file identity. The `recovery` section also reports the original and current project revisions, clock and stop observations, and any saved terminal status. `recovery.clock.state` reports `invalid` for invalid saved clock data and `unknown` when the current boot comparison is unavailable. Valid saved evidence remains readable when that comparison is unavailable, after expiry or after completion.

`recovery.fixed_check` checks local attempt and completion witness identities and reports the saved `read_cutoff`. Its `recorded_complete` state can accompany captured `attempted` progress if the coordinator advances between the reader's unlocked observations. The original native receipt is `not_queried`, and `recovery.owner_activity` stays `unknown`. `resume-graph` checks admission under the original lock. [Resume an interrupted graph](#resume-an-interrupted-graph)

### Resume an interrupted graph

On Linux/WSL2, select `--recoverable` at the first launch. This mode supports read-only, text-only Agent leaves, nested Workflows, all-joins, typed `choose-agent` routing and the [fixed-check review graph](#resume-a-fixed-check-gated-review). Use the manifest's backend bindings and omit `--codex-config`. The first launch saves the original graph inputs, manifest and same-boot budget, and holds a coordinator lock.

```bash
ergora composition run-graph PROJECT ./complete-manifest --manifest-digest MANIFEST_DIGEST \
  --inputs ./graph-inputs.json --directory ./original-graph-run --max-prompt-bytes 150000 \
  --timeout 300 --recoverable
```

If the coordinator is interrupted and leaves the run `incomplete`, inspect the original directory first. Continue with the same control home, project, directory and manifest digest. [Graph readback](#observe-an-original-graph-run)

```bash
ergora composition resume-graph PROJECT ./original-graph-run --manifest-digest MANIFEST_DIGEST
```

Resumption acquires the original coordinator lock and verifies the control home before opening State for writes. It checks the saved project revision, manifest, inputs, remaining budget and original leaf evidence, and corroborates each reservation with its durable pre-send record. It reconstructs the declared outputs of verified successful leaves from their original attempts and Agent run IDs. Only previously unreserved leaves can start. The original deadline and result limits still apply.

For `choose-agent`, recovery derives the selected branch or `none` from the analyzer's verified original result. It checks any saved decision against that result and the frozen branches. A mismatch blocks resumption. If the coordinator was interrupted after the analyzer succeeded and before saving the decision, recovery records that same decision before preparing or dispatching the selected branch. A missing decision blocks recovery when dependent work was already prepared or reserved. A conditional branch can start only if selected and previously unreserved. All-joins retain the skipped states of unselected branches. [Conditional routing contract](contracts.md#conditional-agent-routing)

The command refuses an active coordinator, a terminal or explicitly stopped graph, an expired or invalid original clock, or any reserved leaf with unresolved or inconsistent evidence. Keep the original directory and IDs for readback.

### Read original fixed verification evidence

For a Workflow v2 graph with a `verify-evidence` node, run the same command with the registered project. Supply the original fixed-verify locator through the declared root input. Use the original verify job's activity scheduling event ID, candidate SHA and receipt SHA256. This input example assumes the graph declares `source`. [Read original job receipts](../../development/run-and-recover.md#read-original-job-receipts-and-text-evidence)

```json
{
  "source": {
    "task_id": "TASK_ID",
    "run_id": "RUN_ID",
    "event_id": 42,
    "candidate_sha": "CANDIDATE_SHA",
    "receipt_sha256": "RECEIPT_SHA256"
  }
}
```

Replace the placeholders and example event ID with values from the original run. The read requires the project's original Linux/WSL2 reference installation, Temporal history and job files. It runs synchronously in the graph coordinator and can delay independent dispatch and observation of other Agent results. Active Agent calls retain their original deadline and stop handling. A successful node returns the verified evidence identity on its `result` port. The graph receipt records each original locator and the read outcome in `verification_reads`. Formal verification, approval and candidate release continue through their original owners. [Node and port contract](contracts.md#original-fixed-verification-evidence)

### Gate an advisory review on a completed fixed check

On Linux/WSL2, create a Workflow v2 root with a `verify-fixed-check` gate and exactly one shipped `ergora-correctness-review@1.0.2` child. The child depends on the gate and forwards the root `task` unchanged. Add this fragment to the root definition with its own identity, description, resources, read-only permissions and limits. The `engineering-review` preset installs the pinned child. [Freeze the exact graph manifest](#save-and-share-a-complete-composition)

```json
{
  "schema_version": 2,
  "inputs": ["task", "check"],
  "outputs": {
    "proof": {"node": "verify", "output": "result"},
    "result": {"node": "correctness", "output": "result"}
  },
  "nodes": [
    {"id": "verify", "operation": "verify-fixed-check", "depends_on": [],
     "inputs": {"source": {"input": "check"}}},
    {"id": "correctness", "ref": {
       "kind": "workflow", "id": "ergora-correctness-review", "version": "1.0.2",
       "digest": "f7b5e13770fd64d54b9fe8380e8c70f49b2f6ce140168f2a6eb5cf9e0f4d0ae7"
     }, "depends_on": ["verify"], "inputs": {"task": {"input": "task"}}}
  ]
}
```

Authorize the fixed check with this gated manifest's exact path and digest, the leaf `root/correctness/review` and the local review packet for the exported candidate. Use `task candidate-check` and the registered executor to run it separately. Prepare the graph task from the same packet and manifest, then read the original check status by operation ID. [Authorize, execute and read back a fixed check](../../development/run-and-recover.md#run-registered-fixed-checks-on-an-exported-candidate)

```bash
ergora review prepare-graph-task ./review-packet --source-sha256 PACKET_SHA256 \
  --manifest ./gated-review-manifest --manifest-digest MANIFEST_DIGEST > ./review-task.json
ergora task candidate-check-status PROJECT OPERATION_ID > ./fixed-check-status.json
```

Create `graph-inputs.json` with exactly two fields. Copy the returned `task` object unchanged into `task`. In `check`, copy the original `operation_id`, `request_file_sha256`, `job_sha256` and `candidate_sha` from the check status. For an already completed check, require `succeeded`, `cleanup_confirmed: true` and `stop_requested: false`. Add its exact `receipt_sha256` and `fixed_results_sha256`.

For an already authorized check in `queued` or `attempted` state, use the waiting form of the same `check` object. It takes an integer `wait_seconds` from 1 to 3600 in place of the two terminal digests.

```json
{
  "operation_id": "OPERATION_ID",
  "request_file_sha256": "REQUEST_FILE_SHA256",
  "job_sha256": "JOB_SHA256",
  "candidate_sha": "CANDIDATE_SHA",
  "wait_seconds": 120
}
```

The registered executor watcher runs the original Job. The gate observes it until the earlier of the original graph deadline and the requested wait window. The Job retains its original authorization, attempt and clock. To stop that Job, explicitly use `task candidate-check-stop` with its original operation ID, Job digest and `--confirm`.

```bash
ergora composition run-graph PROJECT ./gated-review-manifest --manifest-digest MANIFEST_DIGEST \
  --inputs ./graph-inputs.json --directory ./gated-review-run --max-prompt-bytes 1000000 --timeout 300
```

The gate validates the original terminal proof against the exact candidate, receipt, authorized project revision, manifest, leaf and task reconstructed from the saved packet. Timeout, stop, unknown outcomes and missing or mismatched evidence block the reviewer. The graph's `proof` output records the verified receipt and fixed-results digests along with the review-input identities. The separate `result` output carries the single advisory review of the unchanged task. Inspect its saved Agent evidence with `composition inspect-run`. Check launch and recovery authority stay with the original check owner. [Observe the graph readback](#observe-an-original-graph-run)

#### Resume a fixed-check-gated review

Use the exact gated manifest above and launch with `--recoverable`. Supply either the completed `check` object with both terminal digests or the wait locator for an already authorized Job. If the coordinator is lost, resume in the same control home and run directory under the conditions below.

```bash
ergora composition resume-graph PROJECT ./gated-review-run --manifest-digest MANIFEST_DIGEST
```

When passing proof is saved, recovery rechecks it through the original native reader under the cutoff recorded for the first gate observation and the original graph deadline. It verifies the original Job, receipt, report, confirmed cleanup and their binding to the authorized project revision, candidate, packet, manifest and reviewer task. The unreserved reviewer can then start under the remaining original graph budget. A previously reserved reviewer requires its verified successful original result.

If that proof came from a wait, recovery uses a completed lookup of the same Job, pinned to the receipt and report digests captured in the proof. The graph keeps the original wait locator and the saved `proof` value.

A native proof reader can outlive the coordinator and keep the original graph lock. Resume can be refused until that reader exits, and the original cutoff still applies. If graph progress still says `attempted`, recovery can reconcile it from a matching durable completion witness only when no prepared dependent input or reservation exists.

An unfinished wait can continue once `resume-graph` acquires the original lock. The original durable wait attempt must match the saved `attempted` progress, and the directory must have no completion record, prepared dependent input or reservation. Resume observes the same authorized Job read-only under the first observation cutoff and the original graph deadline. It durably records passing proof before preparing the reviewer. A missing or mismatched attempt, partial or mismatched proof, stop or expired cutoff blocks resumption.

The original executor retains the fixed-check Job's execution, stop and cleanup authority. Formal `verify-evidence` uses ordinary standalone execution. [Observe the original graph](#observe-an-original-graph-run)

### Choose a follow-up Agent

Use the fragment in a Workflow v2 `workflow.json` with ID `conditional-review` and version `1.0.0`. Keep the usual root description, resources, read-only permissions and limits. Replace each example `ref` with an imported Agent's exact ID, version and bundle digest. Give the analyzer instructions for choosing `structure`, `dependency` or `none` in `artifacts.route`. Both reviewers take the root task as input. [Agent definitions](../agents.md#create-and-modify-definitions) · [Routing contract](contracts.md#conditional-agent-routing)

```json
{
  "schema_version": 2,
  "inputs": ["task"],
  "outputs": {"findings": {"node": "gather", "output": "result"}},
  "nodes": [
    {
      "id": "analyze", "depends_on": [],
      "ref": {"kind": "agent", "id": "route-analyzer", "version": "1.0.0", "digest": "ANALYZER_DIGEST"},
      "role": "inspector", "permissions": {"read": ["definitions"], "write": [], "shell": false, "network": []},
      "inputs": {"task": {"input": "task"}}
    },
    {
      "id": "select", "operation": "choose-agent", "depends_on": ["analyze"],
      "inputs": {"source": {"node": "analyze", "output": "result"}},
      "branches": ["structure", "dependency"]
    },
    {
      "id": "structure", "depends_on": ["select"],
      "ref": {"kind": "agent", "id": "structure-reviewer", "version": "1.0.0", "digest": "STRUCTURE_DIGEST"},
      "role": "reviewer", "review_requirement": "required",
      "permissions": {"read": ["definitions"], "write": [], "shell": false, "network": []},
      "inputs": {"task": {"input": "task"}}
    },
    {
      "id": "dependency", "depends_on": ["select"],
      "ref": {"kind": "agent", "id": "dependency-reviewer", "version": "1.0.0", "digest": "DEPENDENCY_DIGEST"},
      "role": "reviewer", "review_requirement": "required",
      "permissions": {"read": ["definitions"], "write": [], "shell": false, "network": []},
      "inputs": {"task": {"input": "task"}}
    },
    {"id": "gather", "join": "all", "depends_on": ["structure", "dependency"]}
  ]
}
```

With a preview grant in `./preview-grant.json`, import and preview the exact definition, then freeze the complete manifest. Use the `digest` returned by `verify-manifest` as `MANIFEST_DIGEST`. Put the task text under `"task"` in `./graph-inputs.json`.

```bash
ergora composition import ./conditional-review
ergora composition preview conditional-review 1.0.0 --grant ./preview-grant.json
ergora composition prepare-manifest conditional-review 1.0.0 --grant ./preview-grant.json --directory ./conditional-review-manifest
ergora composition verify-manifest ./conditional-review-manifest
ergora composition run-graph my-project ./conditional-review-manifest --manifest-digest MANIFEST_DIGEST \
  --inputs ./graph-inputs.json --directory ./conditional-review-run --max-prompt-bytes 150000 --timeout 300
```

Read `route_decisions` and the joined `findings` in the original `run.json`. A `none` decision marks both branches skipped. Use the standalone graph route for this operation. [Routing and evidence contract](contracts.md#conditional-agent-routing)

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
ergora composition show ergora-large-change-template 1.1.9 --material
ergora agent definition show ergora-server-implementer 2.0.2 --material
```

[Pretraining/posttraining review](../../review/training.md) adds domain specialists to the general three-way review and describes independent leaf calls separately from formal all-join review.

The [evidence-report author](../../review/evidence-reports.md) provides an independent read-only `root/author` that produces Markdown and a static self-contained HTML reading view from complete supplied materials. It reuses the manifest and the [single-leaf input/original-run readers](leaf-calls.md); it does not collect evidence, execute predecessors or grant approval.

`presets` reads shipped content without creating State. `install-preset` imports exact versions in dependency order; repetition retains the same identity and refuses different content at an existing ID/version. Each definition is published atomically, but the whole installation is not a cross-library transaction; retry after interruption. Installation changes no project binding or permission, does not install/authenticate an Agent CLI, and grants no execution or approval authority. The authoritative resources for the new default library are in [data/presets](../../../src/ergora/data/presets/presets.json); replace specialists and subtemplates through the existing export/new-version/import process. Previously published objects and frozen examples retain their original identities; current source revisions publish new versions.

|Composition|Root ID/version|Default relationships and supported use|
|---|---|---|
|repository-governance|`ergora-governance-template@1.1.7`|Shared module/validation/coordinator inventory and planning → parallel knowledge-mapping and architecture-regression work → trusted integrate/verify and three reviews; 11 model slots|
|large-change|`ergora-large-change-template@1.1.9`|Shared module/validation/coordinator inventory and planning → current contract → parallel server/client work → integration validation → trusted integrate/verify and three reviews; 13 model slots|
|training-optimization|`ergora-training-proposal@4.2.10`|Shared flow/design/diagnosis → retained kernel assessment → measurement proposal. Select relevant topic workflows as real descendants in an exact root revision; each leaf inherits the complete common methods and environment record. Explicit leaf calls only.|
|refactoring|`ergora-refactoring-template@1.3.7`|Shared module/validation/coordinator inventory and planning → serial rewrite/compatibility work → trusted integrate/verify and three reviews; 11 model slots, large-change formal task type, definition8/input12|
|optimization-performance-diagnosis|`ergora-opt-performance-diagnosis-proposal@1.2.2`|Limited symptom/compatible-reader specialist plus local test design and measurement proposal; actual profile collection stays with its original owner|
|training-flow-map|`ergora-training-flow-map`|Read-only `root/map` separately produces algorithm/execution dependency maps, state lifecycles and falsifiable redundancy hypotheses; no automatic downstream specialist or training execution|
|evidence-report|`ergora-evidence-report`|Read-only `root/author` produces Markdown/static HTML reports bound to sources; preserves original evidence, run records and independent review/release|
|optimization-report|`ergora-evidence-report@2.0.2`|Same read-only author interface, with dedicated optimization Skill and full template context: source flow/redundancy → comparable results → diagnosis/decisions; explicitly supplied evidence only|
|pretraining-review|`ergora-pretraining-review` 1.1.6|Original general three-way review alongside a pretraining specialist, required/all-join; all four leaves inherit shared backend guidance; the domain leaf can be called independently|
|posttraining-review|`ergora-posttraining-review` 1.1.6|Original general three-way review alongside a posttraining specialist, required/all-join; all four leaves inherit shared backend guidance; the domain leaf can be called independently|

The `engineering-review` catalog imports `ergora-delivery-review@1.2.6` plus optional performance/resource-lifecycle/dependency/security/measurement reviewers. Its default remains three core branches. The [five-member revision example](../../../examples/composition/pr-review-selected/README.md) selects performance and resource lifecycle before freeze, keeps every selected member required and documents full source inputs, readonly permissions, model floors and supervisor follow-up handoff. Independent source calls run one leaf each; the source report requires all declared leaves. Formal development uses its existing ReviewDAG, candidate, fixed call slots, original clock and cleanup owners. All training-root domain/general leaves inherit their own outer root reporting contract; full response compliance is read separately from schema/decision coverage.

The supervisor dispatches, coordinates resources, verifies evidence and reports. Assign a named executor to every experiment, fix or commit and retain one expert per direction. When an expert finishes or encounters a blocker, record the outcome and next step in the durable task list. Recheck readiness immediately, dispatch authorized work, refill vacant needed directions and advance independent tasks. Aim for 4–8 experts actively doing assigned work in distinct directions, based on the latest trusted profile for optimization and current task evidence for development or review. Report the actual count and blocker when the graph, tools, resources or caps allow fewer. Select members and dependencies before freezing. Keep the original candidate, budgets, deadlines, cancellation and cleanup. The task list records state, executor, related files, blocker, next ready work and original backend/job or run IDs. Independently managed external Jobs may continue across session loss. On resume, read the list and reconcile original state before acting on that job. See the [shared optimization policy](../../../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#specialist-execution-and-supervision) and [review contract](../../../src/ergora/data/presets/workflows/ergora-delivery-review/instructions.md).

The [AI helper delegation limit](../../../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#ai-helper-delegation-limit) preserves the original supervisor's relevant parallel expert roster. Every other AI agent gets at most one distinct direct helper over its original campaign lifetime, and that helper creates no AI child. Same-helper continuation consumes the original budgets; new task IDs, aliases, retries or completed helpers do not reset the limit. Further needs go back to the supervisor. This governs AI-initiated delegation, not OS/training processes or trusted scheduling of the already-frozen graph, and it exposes no new spawn capability or runtime enforcement.

Use the [stage/goal and review-granularity guide](../../review/invoke-and-aggregate.md#choose-review-scope-and-granularity): routine experts self-check what the current goal needs, and independent code-quality review covers a coherent integration/merge batch. Preparation, environment binding, documentation and small fixes do not each get a resident or separate reviewer. The selected original FinalReviewDAG is that batch's review arrangement; avoid another same-axis layer, retain actual required tests/evidence/gates, resolve findings in the same batch and release reviewers afterwards.

Development compositions share `ergora-delivery-review`, which references three independently usable subtemplates for structure, correctness and test value. Each specialist has separate initial instructions, expertise and Skills, loading complete materials along its own structural parent chain. Bundled specialists default to Codex gpt-6.2-sol and enforce the [definition minimum](../agents.md); per-instance overrides must satisfy it. Invocation admission still checks availability and authentication; same-backend selection follows the diversity policy and records its reason.

The delivery ancestors carry development rules for semantic ownership, current interfaces, failure-revealing checks, minimal submission scope and candidate-bound evidence; each writer also checks its assigned change before returning. The three development presets share one preparation default: `ergora-refactoring-engineer` as module specialist, `ergora-compatibility-validator` as validation specialist, and the canonical coordinator in each group. Each group has three actual model leaves. Their Agent-level planning minimum is `gpt-6.2-sol/max`, also applying to work invocations of those reusable Agents. Task-specific expert selection uses an explicit revision before freezing; a task-type name does not switch the shared graph. The [development specialist example](../../../examples/composition/development-specialists/README.md) publishes a cross-end revision through real receipts, with 5 inventory + 5 plan + 4 work + 3 review = 17 slots. Added required or advisory review leaves increase the finite budget by their actual count.

With an explicit preview grant, run `prepare-manifest` as described in [complete composition sharing](#save-and-share-a-complete-composition), substituting a root ID/version above. Formal development selection uses [work-units-v2](contracts.md#specialist-writers-and-original-work-units), with `root/development/work` and `root/development/review` inside the selected native instance; a unit ID maps directly to the same-named leaf, for example `contract`→`root/development/work/contract`. Domain inputs obtained through `templates copy` contain the corresponding unit IDs, paths and dependencies; when changing those unit relationships, revise the corresponding work subtemplate too. Workspace write calls still require every writer to explicitly select trusted current-container; importing a composition does not select this boundary automatically.

`refactoring` uses [native six-stage selection](../../development/preparation.md#use-the-refactoring-recipe): its instance is `root/development`, containing work/review, with preparation also handled by independent specialist sessions. Its [complete task example](../../../examples/composition/refactoring/task.example.json) supplies definition8, unit assignments, a budget and explicit writer trust; replace its baseline, callers, scope, acceptance criteria and manifest with real values. Its parent Skill supplies repository conventions, real callers and testing seams; original task types remain. The catalog's `development-v5` is the existing page's development-category label; the task definition selects the actual execution contract, and this label does not downgrade new tasks to input5. The graphical task wizard can select native six stages, [preparation and budgets](../../development/preparation.md), producing input12 through definition8.

The training composition's `root/analysis/design`, `root/analysis/profile`, `root/kernel/assess` and `root/measurement/review` support [single-leaf calls](leaf-calls.md#call-a-prepared-leaf); the operator must supply the complete workload, baseline and relevant predecessor outputs in the task file. Independent `run-input` does not execute graph predecessors. Generated proposals/code text and model reviews are neither experiment results nor adoption approval. Actual CPU/GPU work, Forge candidates and measurements still use the original trusted runner/gate described in the [training guide](../../training/overview.md). The catalog's `runtime` describes the supported use of this distribution; it does not establish backend, service or hardware readiness.

The current training root includes source flow, cross-domain planning/diagnosis, kernel implementation assessment, independent measurement review and library/environment selection. Leaves are read-only with shell=false and network=[]. Calls using Skill attachments require supported task-MCP. Operators supply the complete original task and predecessor materials; missing evidence is reported. Proposals establish neither heterogeneous validation, environment compatibility nor measured gains.

The nineteen `optimization-*` method presets for the [sixteen optimization directions and three support roles](../../../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#sixteen-optimization-directions-and-three-support-roles) select scoped specialists at `root/specialist`, alongside `root/design` and `root/measurement/review`. Profiling and performance-diagnosis reuse one evidence-analysis expert with different topic instructions; kernel reuses the kernel designer. Other directions use their own expert definitions and complete methods. Low-precision retains `root/kernel` between analysis and measurement, and measurement requires that complete result.

A bare direction root is a limited topic proposal. The [selected MoE example](../../../examples/composition/optimization-selected-moe/README.md) uses a fixed 18-leaf native tree with automatic stage fanout/join on the original six-stage owner. Its current revision bases and complete resource file bindings are pinned explicitly. Every leaf inherits the two common Skills and environment record from one development ancestor, without another policy source tree. Independent `run-input` still executes only its selected leaf and requires complete caller-supplied predecessors.

The shared optimization Skill defines [specialist execution and supervision](../../../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#specialist-execution-and-supervision) within assigned resources, budgets and actual tool grants, alongside [GPU comparison guidance](../../../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#gpu-comparisons-and-pool-validation). Readonly leaves retain their declared capabilities. The recipe supplies instructions and explicit handoffs; automatic experiment scheduling and an iGS backend are not implemented.

## Run the example

Install basic Ergora first using the [installation guide](../../install/linux.md); these commands require no model credentials, Web, issue or Temporal service. Example files are in the repository's [examples/composition](../../../examples/composition/README.md). From the repository root, import dependencies before the workflows that reference them:

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

The example Agents use Codex and Claude Code. Preview shows only the requested backend, without checking installation or authentication or promising model quality or independent errors. To change a backend persistently, create a new Agent version and update references along the chain; single-leaf calls also support an explicitly recorded per-call override. See [Agent entry points](../../agents/backends.md) for project-role calls.

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

This rechecks current definition admission and the entire graph identity; a verifiable old bundle is not necessarily callable today. Use the generated input through [explicit check-input/run-input](leaf-calls.md#call-a-prepared-leaf). It neither executes graph predecessors or ports nor creates State or depends on the recipient's original definition library.

These are complete **static** materials with `execution_authorized` false; they contain no operator task body, future parent results, candidate approval or runtime session. Formal tasks still require creation, original-owner approval and runtime admission; see [formal review compositions](../../development/preparation.md#freeze-a-review-composition-for-a-formal-task) for currently supported shapes. To include this bundle in a complete State backup, put the output directory inside your State data directory; otherwise save/copy the entire bundle separately, rather than retaining only `manifest.json`. `--material` returns every leaf's complete static materials; omitting it returns only identities and inventories.

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

## Select a composition on the formal-task page

Complete [project registration](../../projects/registration.md), then open “Formal tasks” → “Preview and create”. The original “Project roles” entry continues using project bindings without automatically applying library compositions.

1. Load a registered development template or compatible draft and fill in the task ID, issue and complete input. Choose “Agent source for this task”: composition review only, composition execution and review, or native six stages (Linux/WSL2). Training optimization retains its separate entry point.
2. Paste the saved bundle's `manifest.preview_sha256` returned above and click “Read complete manifest”. This is not the manifest directory digest; the page reads and verifies the original complete bundle from the current control directory, then displays its root identity and manifest digest. Reading a historical bundle does not admit a formal call today.
3. Select the review subtree by full instance path. Execution-and-review compositions also require an execution subtree; click “Load work units from current input” and select the implementation Agent for each unit. Bundled development compositions usually use `root/work` and `root/review`; unit IDs correspond to same-named work leaves. Reload assignments after changing the work subtree; a failed load retains the previous input and assignments, and the original task preview checks every unit and dependency.
4. Reviewers may retain their exact definition's backend request; to override it, select a backend, configure model and other fields, and state a reason. Explicitly override each writer. Under the existing backend contract, writable mode requires a trusted Linux binding; currently, select Codex's “Execution boundary” → “Trusted current container / user”. The page does not infer this trust from a static definition. External tool configuration still provides authentication; do not enter credentials here. The server explicitly refuses other backends or unsupported modes.
5. Different execution/review backends are preferred by default; same-backend fallback requires a policy explanation. You can explicitly require distinct backends or allow the same backend under the existing diversity contract. Different names or model choices alone do not prove independent error probabilities.
6. For native six stages, select the root workflow or a nested six-stage call, then select the inventory and planning Agents, preparation mode, repository-relative paths (one per line), and total time/reserved cleanup time/model-call count. Preparation members also support per-instance backend overrides. For bundled `refactoring`, select `root/development`, `root/development/preparation/inventory` and `root/development/preparation/plan`; execution/review are at `root/development/work` and `root/development/review`. Adapt the [complete example](../../../examples/composition/refactoring/task.example.json) to the actual input and work units. Under “Materials for this task”, optionally add [exact project memories and active Skills](../../development/preparation.md#select-project-memories-and-active-skills-for-a-formal-task): explicitly read the catalog, enter a new root version and select entries; the default inherits all ancestor materials without automatic recall. Click “Prepare native six stages”, check the complete input and explicitly “Confirm preparation authorization (start budget clock)”; preview is available only after `prepared`. The budget has already started; reads and previews do not extend it, and changing authorized input requires a new task ID. Before authorization, “Download complete authorization input” is available, and preparation or unknown results also offer this download. Closing or refreshing the page releases the form; ID queries read status without reloading the original form. Continue with the downloaded file using the original CLI's `task preview --definition ... --revision ...` and dual-digest `task create`. If a response is lost, first “Read original preparation record” or reopen “Read preparation record by ID”; do not automatically resend authorization.
7. Click “Preview frozen contract”, review the server's complete frozen files and all preparation/execution/review members, the six-stage parent chain and original budget deadline, then “Confirm creation of frozen contract”. The page retains both original preparation and preview digests; an optional source snapshot and six-stage composition can be used together. Creation publishes the contract without starting, approving or executing it. Follow the [formal operating sequence](../../development/tasks.md#formal-task-sequence-and-recovery) to start and approve the original plan. Earlier review-only/execution compositions do not require preparation authorization.

Field changes invalidate the previous task preview; late manifest or preview responses cannot restore old selections. Read/preview failures retain input; issuing creation locks the original contract. If its response is lost, query the original creation record read-only using the task ID retained on the page before deciding how to recover; do not resend under a different ID. Composition, backend overrides and reasons belong only to this frozen task and change no template or project defaults; original owners still verify all ancestor materials, permissions and candidate/approval evidence. The form is released when its dialog closes; save task input first. The complete manifest in the definition library remains persistent.

## Nested workflow definitions

The basic installation uses `ergora composition` to inspect, import, share and preview versioned Agent/subworkflow DAGs. A leaf preview includes all ancestor static materials, permission chains, named ports and global budgets. See [workflow composition](#compose-and-freeze-a-workflow) for examples, operation sequence and scope. Static preview starts no Agent; formal execution retains the original six-stage approval workflow.

### Browse and preview definitions in the page

Start `ergora serve` and open “Agent and composition library” without first registering a project. These libraries belong to the current persistent control directory; switching projects does not change them.

1. Explicitly import a desired composition under “Built-in domain compositions”. Reimporting the same version retains the same identity. Governance, large development and training proposals can be imported independently.
2. Select an exact version in the Agent/subworkflow list. Details display the standard definition, complete own resources, package-file identities and default-backend request. Share complete Skill-attachment packages with CLI `export`; the page's downloaded “Definition JSON” contains only the definition body and cannot replace a complete package.
3. After selecting a workflow, inspect “Static preview limits JSON”, then “Preview complete composition”. Initial values come from the root definition; edits affect this static validation only and grant no project permissions. Errors appear on the page while edited text remains available.
4. Select an instance in the published nested graph, or use the instance-table buttons by keyboard, to inspect complete ancestor resources, sources, permissions, ports, budgets and assembly hints. Nested boxes, dashed dependencies and blue named data represent three relationships. Full paths distinguish repeated references. “Open selected exact definition” and “Open structural parent definition” return to the corresponding editor. Download exact preview JSON for inspection/comparison.
5. After review, “Save current preview as complete manifest” saves this root and every definition/Skill attachment to persistent control storage. Returned `path` and `digest` can be formal-task definition inputs. Saving creates or starts no task. On a lost reply, first “Read saved package by current digest”. If the source library is unavailable, independently verify with `ergora composition show-manifest PREVIEW_SHA256`; see the [complete steps](#freeze-the-current-preview-into-the-persistent-control-directory).

Import does not install/authenticate backends or start tasks/services. Preview backend fields are requests; actual calls still require capability admission and authentication. After choosing an exact version, edit fields or JSON/YAML in “Edit definition and derive new version”, then explicitly apply, check and publish a revision. Original attachments and old versions remain. See [Agent editing](../agents.md#edit-a-specialist-agent-in-the-console) and [workflow revisions](revisions.md#revise-workflows-on-the-page) for complete steps and browser-buffer limits. The graph shows published versions; drafts do not enter automatically. Collapse subworkflows independently, search by responsibility/specialty/backend and expand ancestors to locate results. Summary edges trace back to complete original endpoints. Layout/collapse/search are separate from contracts and reset on refresh; the table remains available if graphical components are missing. See the [relationship graph](revisions.md#view-published-nested-relationships). With a comparison target selected, [compare two published compositions](revisions.md#compare-two-published-compositions) using the same explicit limits, checking reference/permission/material differences per path and downloading both complete previews. Save a complete manifest here, then [select it on the task page](#select-a-composition-on-the-formal-task-page) to read the original digest, assign work units and set per-instance backends. The native six-stage entry also configures inventory/planning Agents and budget; explicitly authorize preparation before previewing and creating. Original project-role entry points remain available.

Use [CLI resource revisions](../resources.md#revise-complete-resource-files) to modify instructions/context, complete Skill directories and ordinary attachments: pin the original package, preview complete differences and suggested digest, explicitly accept that same candidate, then check/publish a version. Both definition kinds share this contract. Binary files, executable bits and empty directories remain explicit; historical files support byte-window reads. The page's “Resource and attachment editing” can also read/upload complete files, stage operations, preview differences and explicitly accept the digest before check/publish; see the [page resource steps](../resources.md#edit-resources-and-attachments-in-the-console). Bodies, operations and accepted identity enter history together. Unapplied bytes remain separate; a downloaded editing buffer excludes unedited original package content.

When changing nested compositions, follow the [dependency-chain steps](revisions.md#publish-resource-revisions-through-the-complete-dependency-chain): publish specialists/subworkflows before the new root. Prepare new input from that root; old snapshots retain old materials. To establish that attachments actually reached the model, check this invocation's original list/read evidence through [complete-read verification](leaf-calls.md#verify-complete-attachment-reads).

## Import domain-specialist compositions

The basic installation includes default specialist/subworkflow packages for governance, large development and training proposals. Run `ergora composition presets` to inspect actual scope and `ergora composition install-preset large-change` to import every exact dependency. See [built-in domain compositions](#use-bundled-domain-compositions) for details, node relationships, independent backend selection and sharing. Static import chooses no trusted container, starts no services and approves no task. Formal development follows the [original task sequence](../../development/tasks.md#formal-task-sequence-and-recovery); training proposals and [trusted experiment execution](../../training/overview.md) remain separate.

For parent/child permission changes, follow [joint revisions](revisions.md#jointly-revise-parent-and-child-permissions), publishing versions from inner definitions to root, then provide an explicit grant and check actual invocation capabilities. Parallel instances of the same specialist need distinct node IDs and a complete all-join. Different review responsibilities require a new subtemplate version; see [repeated instances and backend selection](revisions.md#repeated-instances-responsibilities-and-backend-selection).

### Import a complete workflow directory in the page

In “Agent and composition library”, select “Import workflow directory”. Enter the directory on the console machine containing `workflow.json` and all own resources; a retrospective export directory from the next section is suitable. Check the displayed control directory and explicitly submit. The library is shared in this control directory without depending on the current project. The receipt contains original ID/version/digest, definition and resource-file identities. Retain it, close the window, “Refresh definition library” on this page, then select the receipt's exact version. The global “Refresh” at the top does not reread the definition list.

Identical content/version retains the same identity. Different content at the same version is refused; select a new version. Import publishes only this root package, so import Agent/subworkflow dependencies beforehand. Original import/preview checks complete references, ancestor resources and permissions. After selecting a new version, preview under the original limits above and explicitly save a new manifest. To roll back, select the original version/manifest again; old tasks retain original materials. Import does not automatically select a new version, preview, save or execute.

An abnormal request may have executed. First refresh the library and select original ID/version to check its digest, or read its original package with `ergora composition show WORKFLOW_ID VERSION --material`. Do not delete original records to force retries. After closing the window or leaving its source page, late replies do not manipulate subsequent windows. Reopening requires checking original records again. The HTTP equivalent is `POST /api/workflow-definitions/import` with `{"directory":"/path/to/workflow-bundle"}`, retaining same-origin protection and `X-Ergora-Request: 1`.

Continue: [Workflow data and execution contracts](contracts.md) · [Inherited resources, permissions and static budgets](permissions.md) · [Invoke and inspect one frozen workflow leaf](leaf-calls.md).
