# Ergora framework tour

English · [Documentation](../README.md) · [Architecture contract](current.md)

Ergora is a control plane for project-bound specialist Agents, workflow composition, formal software delivery, training experiments and reusable improvements. Definitions describe reusable behavior. Each operation freezes its own inputs, checks its execution authority and produces evidence under its original identity.

This tour uses candidate runtime revision `fe69a67b2a0d5b463f3c55efe3878e229233eacc` and its `src` tree `635e18a73096b951d45b7500b178778fa6b7e519` as the exact source reference. Packages, installed applications and local definition libraries have separate identities. The [current plan](../PLAN.md) and its delivery records track review, CI and installation status.

## The whole system

The template library offers exact bundled and saved starter graphs. An operator can preview and freeze a template before choosing its execution route.

```mermaid
flowchart TB
  Entry["CLI and web Console"] --> Select["Select an execution route"]
  Entry --> Freeze["Static preview and freeze<br/>Exact manifest and selections"]
  Assets["Starter library<br/>Default six-stage or another exact graph"] --> Freeze
  Freeze -. "selected material" .-> Select
  Config["Project revision, bindings and grants"] --> Select

  Select --> Check["Fixed-check CLI<br/>Separate authorization"]
  Select --> Graph["Standalone graph CLI<br/>Ready Agents and typed operations"]
  Select --> Session["Prepared leaf or native project session<br/>agents.runs"]
  Select --> Dev["Formal task<br/>Explicit native root or nested invocation"]
  Select --> Train["Training experiments and finite controllers<br/>training.application"]
  Select --> Improve["Retrospectives and Skill evaluation<br/>improvement"]

  Check --> CheckJob["Registered executor<br/>Original fixed-check Job"]
  Graph --> GraphProof["Graph and original Agent evidence<br/>Historical leaf starts via inspect-graph"]
  Graph --> Gate["verify-fixed-check<br/>Receipt gate before advisory review"]
  CheckJob -. "receipt or bounded wait" .-> Gate
  Gate --> GraphProof
  Graph -. "Agent graph, saved proof or interrupted wait" .-> Resume["Opt-in resume-graph<br/>Original boot, directory, cutoffs and lock"]
  Resume --> GraphProof
  Session --> Turn["Original leaf result or Codex turn receipts"]
  Dev --> Six["Original Temporal six stages<br/>Exact approval and candidate evidence"]
  Train --> Runner["Original training executor<br/>Runner and experiment archive"]
  Improve --> Eval["Trusted evaluation<br/>Explicit adoption"]

  GraphProof -.-> Recover["Read original IDs, receipts and outcomes"]
  CheckJob -.-> Recover
  Turn -.-> Recover
  Six -.-> Recover
  Runner -.-> Recover
  Eval -.-> Recover
```

Development's [workflow extensions](../../src/ergora/development/runtime/workflows.py) and [executor](../../src/ergora/development/runtime/executor.py) extend the bundled reference. Training's [native entry point](../../src/ergora/training/runtime/execution.py) enters the bundled training executor. Dedicated processes select the installation, configuration and state before importing the reference. [Reference boundary](reference-boundary.md)

## Definitions and execution routes

`DefinitionLibrary` stores immutable Agent and Workflow versions with their complete ordinary-file bundles. The compiler resolves exact ID/version/digest references, ancestor instructions and Skills, permissions, capacity, dependencies and named ports. Structural ancestry supplies instructions and resources. Dependencies order work. Ports carry declared outputs. Inherited material stays within the original grants. Preview and freeze are static operations. Execution binds the selected manifest or session context to the project revision and admitted inputs. [Workflow compiler](../../src/ergora/definitions/workflows.py)

“New template” preselects the bundled six-stage graph. Other bundled graphs and exact saved versions are peer choices. The selected starter opens an editable draft under its own destination ID and version. Formal task admission separately checks the published graph and explicitly selected route. [Choose a starter and save a template](../definitions/workflows/revisions.md#revise-workflows-on-the-page)

### Standalone graph

`ergora composition run-graph` selects a complete manifest by digest, the exact root inputs and a new run directory. Read-only, text-only Agent leaves start when their dependencies are satisfied and project, root and ancestor concurrency limits have room. A ready successor can run while an unrelated branch is still active. The graph coordinator reserves each original attempt before dispatch. Failure, stop or deadline ends new dispatch and drains the original owned calls. Nested workflows pass declared ports, and all-joins collect outputs by exact instance path. [Graph commands and limits](../definitions/workflows/compose.md#run-a-standalone-workflow-graph) · [Graph runner](../../src/ergora/agents/graphs.py)

- `choose-agent` reads the verified analyzer result and records the decision before any follow-up dispatch. Its typed route selects one declared sibling Agent or `none`. The all-join carries the selected branch's original result and explicit skipped states for untaken branches. [Routing contract](../definitions/workflows/contracts.md#conditional-agent-routing)
- `verify-evidence` takes an exact original fixed-verify locator from a declared root input. The native reader uses the registered reference installation, original Temporal history and Job artifacts to validate the candidate, receipt, complete check results and process records. This synchronous read can delay other dispatch. The formal executor owns execution of that verify Job. [Verification readback](../definitions/workflows/compose.md#read-original-fixed-verification-evidence)
- `verify-fixed-check` reads a separately authorized fixed-check Job. Given a queued or attempted Job, it can wait until the earlier of the original graph deadline and the requested observation window. The original executor owns check execution, stop and cleanup. The gate requires a passing receipt and confirmed cleanup bound to the exact candidate, review packet, frozen manifest and prepared task before the pinned correctness reviewer starts. The graph publishes the verified receipt and report identities in `proof` alongside the separate advisory result. [Gated advisory review](../definitions/workflows/compose.md#gate-an-advisory-review-on-a-completed-fixed-check)

After an interrupted run, `composition inspect-graph` uses the original directory and manifest digest and opens the existing control database read-only. It reports the saved graph status and attempts alongside the observed original Agent input, prompt and result identities. A corroborated route matches the frozen branches and original analyzer evidence. Saved verification references show native receipts as `not_queried`. [Graph observation](../definitions/workflows/compose.md#observe-an-original-graph-run)

For a collected text-only graph leaf on Linux/WSL2, `original_run.process_start` can show the historical direct local child's PID, boot ID and start ticks. The original process owner samples the child at launch and returns the sample after its wait. The leaf reader verifies the sample's binding to the original run, frozen input and prompt. The graph-level `process_start` and `stop_and_cleanup` fields remain `unknown`. Use `composition inspect-run` on the exact original leaf run ID for complete result content. [Original leaf readback](../definitions/workflows/leaf-calls.md#read-an-original-composition-run-by-exact-id)

On Linux/WSL2, graphs with read-only, text-only Agent leaves, nested Workflows, all-joins and `choose-agent` can opt into recovery at launch with `run-graph --recoverable`. `resume-graph` opens the same directory and control home on the original boot under the saved coordinator lock and deadline. It verifies original reservations and successful Agent results to reconstruct the graph's ports. Saved typed choices must match the original analyzer result. If a choice is missing and its dependent work has yet to be prepared or reserved, the coordinator records the same branch or `none` before proceeding. Only previously unreserved, ready Agent leaves can start. An active, stopped, terminal or expired graph, or any unproven original Agent attempt, blocks resume. [Standalone recovery](../definitions/workflows/compose.md#resume-an-interrupted-graph)

The pinned correctness-review graph can opt in with a completed locator or a bounded wait on its separately authorized fixed-check Job. When passing proof is already durable, resume revalidates it within the first gate read's saved cutoff and the graph deadline. For proof from an initial wait, the native reader uses the captured receipt and report digests for a completed lookup of the same Job. The graph keeps the original wait locator and proof.

A surviving reader can hold the original lock after coordinator loss. Once resume acquires the lock, it can continue an unfinished wait whose durable attempt matches the saved `attempted` progress, with no completion record or dependent work. The native reader observes the same authorized Job under the original cutoff and graph deadline. The graph durably records passing proof before preparing the reviewer. The original executor retains ownership of the Job. Formal `verify-evidence` uses ordinary standalone execution. [Fixed-check-gated recovery](../definitions/workflows/compose.md#resume-a-fixed-check-gated-review)

### Separately authorized fixed checks

On Linux/WSL2, `task candidate-check` authorizes one fixed-check Job for an already exported Git candidate using an exact request SHA256 and a stable operation ID. The registered reference executor runs `CandidateCheckJob` under the original clock, owns checker launch and cleanup, and publishes the scoped receipt. `task candidate-check-status` reads that original Job and `task candidate-check-stop` fences it. The checker Job's execution authority stays with its original permit and executor. [Fixed-check CLI and recovery](../development/run-and-recover.md#run-registered-fixed-checks-on-an-exported-candidate) · [Native operation](../../src/ergora/development/runtime/candidate_checks.py) · [Job owner](../../src/ergora/development/runtime/jobs.py)

### One leaf or a native project session

`composition run-input` explicitly runs one admitted leaf. Supply its prerequisite evidence with the prepared input. The backend validates the requested mode; fixed task MCP, when used, exposes the frozen resource table and records resource reads. Backend admission, delivered bytes, actual reading and model quality are separate observations. [Leaf calls](../definitions/workflows/leaf-calls.md)

An ordinary native project session uses the role's original workspace grants. It freezes the role, repository, selected backend configuration and context at session start. The current persistent native session route uses Codex on Linux/WSL2. Continuation selects the latest stopped parent with its saved native session identity and a stable turn intent. The CLI and Console read the same receipt by original session, parent and intent. [Project sessions](../operations/services.md#project-native-sessions)

|Receipt evidence|What it establishes|
|---|---|
|`dispatch`| `reserved` records the request. `attempted` records the original dispatch before launching supervision. `accepted` records that the original supervision process acquired the inherited session lock and accepted the request. `unrecorded` can mean the read raced publication. Damaged or missing required evidence is `incomplete`.|
|`native_start`|The supervision process records the actual child after obtaining its process handle. `running` checks the saved PID, boot ID and process start ticks at readback. `started` preserves verified historical launch evidence. `unrecorded` includes older turns without the receipt. `incomplete` reports a failed publication or invalid evidence.|
|`run` and cleanup|The original run can show a live supervision process, a verified final record or an unknown outcome. Stop request and notification are separate from `execution_stopped`, which confirms the original owner has no remaining execution to reap. Use the same original intent for readback after a lost response.|

The start receipt's metadata writer runs in a separate thread from the native child's sole reaper, so storage publication can stay pending while cancellation and cleanup proceed. The owner bounds any wait for that writer by the original stop and deadline. A missing receipt leaves the independent dispatch and outcome readable. These records concern the local Agent process. Provider receipt and external training execution have their own evidence. [Continuation reader and session owner](../../src/ergora/agents/runs.py) · [Process owner](../../src/ergora/runtime/processes.py)

## From a development request to a reviewable candidate

Choose the formal task route when delivery requires an approved plan, an exact Git candidate and trusted checks. In Definition8, `composition.native` can explicitly select one six-stage instance at `root` or under a supported parent that forwards its task and result. `development.application` checks the registered repository, baseline, permissions, budget and optional issue, memory and Skill snapshots, then prepares and creates the frozen task. Explicit submission uses Input12 and `PreparationDAGWorkflow`. The original Temporal run owns these stages. [Formal route selection](../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page)

1. **`inventory`** inspects the exact starting Git objects. Frozen inventory specialists supply declared results to their coordinator; the canonical inventory records the trusted sources.
2. **`plan`** uses that inventory and the selected planning DAG. The original workflow computes the plan receipt digest and waits for **the original owner's approval of that exact request and plan**. `development.application.approve` delivers this decision through the native approval owner. A proposed plan alone grants no work execution.
3. **`work`** runs approved work units (`work:<unit-id>`), respecting dependency commits, path scopes and concurrency limits. Isolated worktrees and original receipts bind each output to its producer; declared ports supply predecessor artifacts.
4. **`integrate`** combines the work through the trusted executor and establishes the candidate Git SHA. An Agent's text cannot substitute for this integration result.
5. **`verify`** runs trusted checks against that candidate. Registered fixed verification freezes its check declaration at task creation and validates the complete check-results report, source binding and process evidence. A model's claim that tests passed is insufficient.
6. **`review`** collects candidate-bound independent sessions, required/advisory duties and verification material. Success returns `REVIEW_READY` with original evidence. Explicit export obtains the exact candidate for human merge review; merge, push and deployment are separate actions.

The [workflow contract](../definitions/workflows/contracts.md) owns detailed graph rules. [Formal recovery](../development/run-and-recover.md) follows the original task and run IDs.

PR/MR review also works without creating a formal development task. `development.review.packets.prepare` captures exact local base/head Git material and requirements; `review.sources.collect` binds supported same-repository platform observations; `review.requests.prepare` freezes reviewer inputs and `report` aggregates actual results. Issue snapshots are optional context. External comments/labels and candidate associations have explicit writeback owners; collecting a review does not approve or merge a remote request.

## Training experiments and evaluation

**Training optimization.** `training.application` previews/registers baselines and runners, prepares experiment manifests, submits original runs, explicitly requests managed execution, reads archives and delivers exact-evidence approval. `training.native` uses dedicated operations/readers; `training.runtime.execution.Execution` checks the original queued run and publishes a single request/launch chain before the native executor enters its existing lock, sandbox, runner and archive path. `training.execution_protocol` owns cross-process records, source/context bindings and offline lifecycle reads. Target models, optimizers, datasets, gradients and numerical quality remain the target training project's responsibility.

`training.search` freezes a finite candidate package. `training.cycles` authorizes a bounded controller; `training.runtime.worker` executes its supported protocol using the original submission, budget and stop owners. Current consent distinguishes full-accepted execution from bounded screen/profile/no-effect-skip. `training.rounds` links original observations; its index neither executes candidates nor advances the baseline. Resource grants, specialist proposals, experiment execution and evidence approval stay separate. A template's GPU topology or optimization suggestion is not a GPU measurement.

**Improvement, memory and RSI.** `improvement.retrospectives` turns source-bound handoff material into checked Skill, memory or Workflow candidates. `memory` owns revisions, validity, deletion/restore and optional ReMe mirroring. `evaluation` freezes trusted evaluator files and train/validation/holdout cases, then binds results to exact Skill content. Optional GEPA search in `optimization` starts from the registered Skill's exact seed bytes, proposes revisions and evaluates visible cases under call, time and reported-cost bounds. Ambiguous proposer cost ends the search with incomplete cost coverage. `skill_adoption.adopt` compares full-suite runs and explicitly moves a revision-checked head. Rollback and later task-context freezing have their own operations. Project-document correction suggestions have their own exact-preview consent/apply owner. Research scheduling and native kernel campaigns retain separate domain lifecycles and capability checks. [Evaluation and adoption](../improvement/skills-and-evaluation.md)

## Where each responsibility lives

|Responsibility|Code entry points and contract|
|---|---|
|Transport and pages|[cli.main](../../src/ergora/interfaces/cli.py), [web.create_app](../../src/ergora/interfaces/web.py), [console assets](../../src/ergora/data/console). Parse requests and render domain results; pages own no scheduler.|
|Configuration|[catalog](../../src/ergora/configuration/catalog.py), [bindings](../../src/ergora/configuration/bindings.py), [projects](../../src/ergora/configuration/projects.py), [registrations](../../src/ergora/configuration/registrations.py). Effective choices, project revisions and one-way native publication.|
|Reusable assets|[agents](../../src/ergora/definitions/agents.py), [workflows](../../src/ergora/definitions/workflows.py), [bundles](../../src/ergora/definitions/bundles.py), [skills](../../src/ergora/definitions/skills.py). Admission, compilation, immutable content and active Skill heads.|
|Graph and Agent calls|[graphs](../../src/ergora/agents/graphs.py), [runs](../../src/ergora/agents/runs.py), [native record readers](../../src/ergora/agents/native_sources.py), [invocation](../../src/ergora/agents/invocation.py), [backends](../../src/ergora/agents/backends.py), [MCP](../../src/ergora/agents/mcp.py). Standalone scheduling, route decisions and inspection, original leaf and session records, backend selection and fixed resources.|
|Development and review|[application](../../src/ergora/development/application.py), [native](../../src/ergora/development/native.py), [runtime](../../src/ergora/development/runtime), [review](../../src/ergora/development/review), [verification](../../src/ergora/development/verification.py). Exact task/candidate decisions and trusted evidence.|
|External sources|[issue backends](../../src/ergora/issues/backends.py), [snapshots](../../src/ergora/issues/snapshots.py), [writebacks](../../src/ergora/issues/writebacks.py). Platform identity, frozen context and attempted external effects.|
|Training|[application](../../src/ergora/training/application.py), [execution protocol](../../src/ergora/training/execution_protocol.py), [runtime](../../src/ergora/training/runtime), [cycles](../../src/ergora/training/cycles.py), [rounds](../../src/ergora/training/rounds.py). Original experiments, finite controllers and observation links.|
|Improvement|[retrospectives](../../src/ergora/improvement/retrospectives.py), [memory](../../src/ergora/improvement/memory.py), [evaluation](../../src/ergora/improvement/evaluation.py), [optimization](../../src/ergora/improvement/optimization.py), [adoption](../../src/ergora/improvement/skill_adoption.py). Generation, evaluation and explicit reuse.|
|Persistence and live resources|[State](../../src/ergora/storage/state.py), [assets](../../src/ergora/storage/assets.py), [Git material](../../src/ergora/storage/git.py), [processes](../../src/ergora/runtime/processes.py), [budget clock](../../src/ergora/runtime/budget_clock.py), [GPU pool](../../src/ergora/runtime/gpu_pool.py). Durable control records, complete material and owned lifetimes.|
|Native integration and operations|[resources](../../src/ergora/native/resources.py), [compiler](../../src/ergora/native/compiler.py), [registration](../../src/ergora/native/registration.py), [operations](../../src/ergora/operations). Source identity, isolated integration, diagnostics, services and coordinated backups.|

## Evidence, recovery and current limits

Control-plane SQLite is not the execution ledger: native task/training directories retain original jobs, claims, receipts, archives and runtime history. Exact Git objects, bundle digests, raw-file hashes and record digests have [distinct identity contracts](contracts/identities.md). A changed registration or library head affects new selections; recovery reads the original frozen materials.

External effects record an attempt before sending. A lost reply remains **unknown** until reconciliation of the original ID/history/receipt; restarting cannot authorize duplicate execution. Budgets retain their original clock and consumed slots across recovery. Cancellation delivery, fences, actual process stopping, durable cleanup, terminal outcome and lease release are separate facts. Each supervised subtree has one reaper; its stopped record follows actual collection, and it cannot spawn after stopping. See [development](execution/development.md) and [training recovery](execution/training.md) before changing these owners.

General Repeat, arbitrary mixed-stage graphs, multiple native six-stage instances and the protected human design-approval channel remain outside the current execution scope. Optional backend modes, ReMe, GEPA, research and ForgeKernel depend on actual integration support and availability. Model quality and GPU gains require corresponding run evidence. Full native development and persistent Codex sessions use Linux/WSL2. Windows has its own control-plane and backend support. Local containers run in the trusted current-user boundary. [Supported scope](current.md) · [Windows guide](../install/windows.md) · [Current plan](../PLAN.md)

## A short source-reading route

1. Start at `interfaces.cli.main` or `interfaces.web.create_app`; follow one domain call.
2. Read `configuration.catalog`, `bindings` and `registrations` for effective authority and publication.
3. Follow `definitions.workflows.preview` into `_Compilation` and `DefinitionLibrary`, then `agents.graphs.run_graph` and `inspect_graph` for standalone execution and evidence readback.
4. Trace `development.application` → `development.native` → `PreparationDAGWorkflow` → bundled `DevelopmentWorkflow.run`.
5. Read `development.runtime.executor.Executor`, `jobs` and `verification`, then `agents.invocation.invoke` and `AgentBackend`.
6. Compare `training.application.execute`, `runtime.execution.Execution` and `execution_protocol`; follow the native runner and controller separately.
7. Trace `retrospectives` → candidate import/evaluation → `skill_adoption.adopt` → `development.context` for the next task.
8. Finish with `storage.state`, `runtime.processes` and `budget_clock`; inspect the relevant recovery guide and [component protocol](component-change-protocols.md) before editing.

Keep this tour focused on relationships and boundaries. Update affected source links and explanations when ownership changes; keep detailed schemas, operational commands and changing acceptance status in their existing owners.
