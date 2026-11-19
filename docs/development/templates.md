# Follow the bundled development templates

English · [Documentation](../README.md) · [简体中文](../zh-CN/development/templates.md)

This guide connects installation, specialist compositions, formal development and training experiments. Start with [installation](../install/linux.md), or the [Windows guide](../install/windows.md). The basic control plane includes CLI, SQLite and local pages. Complete six-stage execution additionally needs a Linux/WSL2 reference environment, selected services and authenticated Agents. A development/research installation profile adds SDKs; prepare services, models, project checks and GPUs separately as needed.

Follow [source-branch selection](../install/linux.md#install-in-a-clean-environment) to install the current main branch or pinned commit. An identical package version does not guarantee the preset/composition commands below.

|Template/preset|Current bundled root identity|Specialist relationships and entry points|
|---|---|---|
|repository-governance|`ergora-governance-template@1.1.1`|Parallel knowledge-map/boundary-test, then trusted integration/verification and structure, correctness and test-value reviews|
|large-change|`ergora-large-change-template@1.1.1`|contract→parallel server/client→integration-tests, then trusted integration/verification and three reviews|
|training-optimization|`ergora-training-proposal@4.2.2`|Source flow→planning/diagnosis→kernel implementation planning→measurement review; all five leaves inherit library/environment guidance, with actual experiments owned by trusted runners.|
|refactoring|`ergora-refactoring-template@1.3.1`|Preparation→rewrite→compatibility→original trusted integration/verification→three reviews; ordinary parent references one native large-change six-stage instance|

Select a focused training direction through the [optimization specialist guide](../training/specialists.md). Use `ergora composition presets` for the complete installed catalog and exact current identities; the [shipped catalog](../../src/ergora/data/presets/presets.json) owns those versions.

Each Agent is an independently versioned package with its own specialties, initial instructions, Skills and backend. The structural parent chain accumulates complete materials and constrains child permissions. Dependency edges order execution; named ports carry results. Expand these three relationships in “Agent and composition library”. See [definition format and inheritance](../definitions/workflows/compose.md).

Refactoring uses the [native six-stage instructions](preparation.md#use-the-refactoring-recipe) and [complete example](../../examples/composition/refactoring/README.md). The two-domain page steps below include independent inventory/planning and the original work/review contract. For refactoring, select “Complete manifest · Native six stages” in the same form, configure preparation leaves/native instance/work and review subgraphs/budget, explicitly authorize preparation, then preview/create. Before choosing the recipe, pin actual callers, behavior to preserve, migration order and rollback checks. It uses original task/run/candidate identities and approval. To include project memory or active Skills, freeze exact current sources through [material selection](preparation.md#select-project-memories-and-active-skills-for-a-formal-task).

Ergora maintains these engineering roles, initial instructions and compositions; see [Agent definitions](../definitions/agents.md#built-in-specialists). They are versioned/selected separately from concrete Codex/Claude Code backends. See the [training guide](../training/specialists.md#independent-optimization-direction-subtemplates) for the complete optimization-direction table; templates do not each import an upstream native Agent directly.

## Current execution boundaries

Presets and static graphs do not implement generalized Repeat, a mixed-graph scheduler or unified fixed/preset/planner/automatic reasoning selection. Current explicit backend fields request supported model options, without proving actual applied effort. Complete ancestor materials and narrowing permissions remain frozen into supported task/leaf inputs. [Current backend limits](../agents/backends.md#current-configuration-evidence-and-pending-capabilities) describe these boundaries.

Schema2 design-policy registration remains storage-only with execution unsupported. Inspection-only [source-journal storage](design-and-approval.md#store-complete-design-sources-and-reported-answers) is Linux/WSL2-only and requires a legitimate original design-packet. Trusted human assurance and F/J/G remain unavailable. Finite training controllers use a separate [explicit authorization and submission flow](../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization). Importing definitions or saving a manifest does not authorize these effects.

## 1. Prepare templates and complete compositions

These commands use an installed CLI, without models or background services. Keep business repositories, control data and complete manifests in persistent user directories or volumes, avoiding temporary directories.

```bash
export PATH="$HOME/.local/bin:$PATH"
export ERGORA_HOME="${ERGORA_HOME:-$HOME/.local/share/ergora}"
WALKTHROUGH_HOME="$HOME/.local/share/ergora-walkthrough"
mkdir -p "$WALKTHROUGH_HOME"
ergora composition presets
ergora composition install-preset repository-governance
ergora composition install-preset large-change
ergora composition install-preset training-optimization
ergora templates copy repository-governance "$WALKTHROUGH_HOME/governance-template"
ergora templates copy large-change "$WALKTHROUGH_HOME/development-template"
ergora templates copy training-optimization "$WALKTHROUGH_HOME/training-template"
```

Copy destinations must be new. Reimporting a preset with identical identity retains its version. Template copying and preset import prepare domain inputs and specialist definitions respectively, without granting model, filesystem-write or approval authority.

For governance, read the original root declaration first and save explicitly reviewed permissions/budget as a grant:

```bash
ergora composition show ergora-governance-template 1.1.1 --material > "$WALKTHROUGH_HOME/root.json"
python3 - "$WALKTHROUGH_HOME" <<'PY'
import json, pathlib, sys
directory = pathlib.Path(sys.argv[1])
definition = json.loads((directory / "root.json").read_text())["definition"]
grant = {"schema_version": 1, "permissions": definition["permissions"], "limits": definition["limits"]}
(directory / "grant.json").write_text(json.dumps(grant, indent=2) + "\n")
PY
ergora composition preview ergora-governance-template 1.1.1 --grant "$WALKTHROUGH_HOME/grant.json"
```

Review the complete preview's instances, ancestor materials and authorization limits. Use the actual returned `preview_sha256` for `PREVIEW_SHA256` below:

```bash
ergora composition freeze-manifest ergora-governance-template 1.1.1 --grant "$WALKTHROUGH_HOME/grant.json" --preview-sha256 PREVIEW_SHA256
```

Retain returned complete-package `path`, package `digest` and `manifest.preview_sha256`, then run `ergora composition verify-manifest FULL_MANIFEST_DIRECTORY`. When changing domain, use its root ID above and obtain/review that root's grant again; training roots request neither shell nor write permission. The page can also preview and “Save current preview as complete manifest”. Downloaded preview JSON is for reading; sharing/backups need the complete directory. See [complete bundles](../definitions/workflows/compose.md#save-and-share-a-complete-composition).

## 2. Register your project

Each business project uses its own Git repository/tracker. First create an actual Git commit. Configure absolute execution paths, allowed changes and actual trusted checks through [project definitions](../projects/registration.md), then run `ergora project register project.json --revision 0`. GitHub/GitLab repositories are not prerequisites: local trackers work, with a separate local branch exported per task. Code branches and issue records have distinct identities; one shared business repository need not hold every project.

Formal development compositions and training task-mcp leaves require Linux/WSL2 and the optional `task-mcp` dependency. control/development/research installation profiles do not add this extra automatically. Static import/preview/freeze and contract creation do not require it, so successful creation still needs runtime preparation. From the installed version's repository root, install in the same Python environment running Ergora and its executor. For the default Bash installer:

```bash
"$HOME/.local/share/ergora-app/venv/bin/python" -m pip install '.[task-mcp]'
```

Use your own Ergora interpreter for custom environments/install locations; installing into another Python does not satisfy the executor dependency. Native Windows can first use the console, definitions and text-only capabilities. Fixed-task MCP reads and complete development execution use Linux/WSL2. Complete selected-Agent [installation/authentication](../agents/configuration.md#install-and-authenticate-agent-clis) and provide its authentication/inference configuration to the environment actually starting Ergora/executor. Other backends apply to custom definitions without this model minimum; Claude task-mcp bare mode requires its supported API-environment authentication. Keep credential values out of tasks/definitions. Check services, roles and project checks separately; a version/authentication probe does not replace an actual task.

Governance requires behavior/architecture/knowledge checks; large changes additionally require integration/compatibility/migration-rollback. These are executable project acceptance checks using the project's actual commands. Prepare complete runtime/services/model authentication through the [deployment steps](#the-three-templates-and-formal-tasks). `doctor`, service RUNNING and successful creation each establish only their own state.

## 3. Create development tasks in the page

Run `ergora serve` and open local `http://127.0.0.1:8977`. Under “Formal tasks”:

1. Open “Preview and create”, select a registered template and “Load selected template”. Wait for “Template input loaded” before entering task ID, issue and actual input. Changing template invalidates the old preview.
2. Select “Complete manifest · Composition execution and review”, enter step 1's `manifest.preview_sha256` and “Read complete manifest”. Use `root/review` for review and `root/work` for execution. Under “Inventory and planning”, select `root/preparation/inventory` and `root/preparation/plan`, with repository read paths covering the work units. Both preparation specialists default to gpt-6.1-sol max.
3. “Load work units from current input”, assigning every unit to its complete path. Governance uses `knowledge-map`, `boundary-test`; large changes use `contract`, `server`, `client`, `integration-tests`, at `root/work/UNIT_ID`.
4. Explicitly choose a supported backend, execution boundary and override reason for every writer. Current writable compositions prefill the template model/effort for Codex; explicitly choose “Trusted current container/user”, still requiring trusted Linux. This permits access to current-user files; permission-path checks do not provide OS isolation for individual file accesses.
5. Keep gpt-6.1-sol high for review; overrides must meet the definition minimum. Record the reason for separate sessions on the same backend and select that diversity policy. Configure authentication in the environment starting Ergora, keeping keys in external environment/tool-authentication configuration.
6. “Preview frozen contract”, checking complete assignments, backends/policies, ancestor materials, paths and input, then “Confirm creation of frozen contract”. The page freezes inventory, planning, work and review members together; omitting preparation fails visibly. Creation publishes a contract without starting a model or task.

A template can contain multiple same-responsibility specialist instances. Before adding/replacing specialists, publish separate Agents and exact workflow versions along the parent chain, then preview/freeze a new task. The graph shows published versions; dragging layout does not revise contracts. See [work-unit protocol](../definitions/workflows/contracts.md#specialist-writers-and-original-work-units) for complete CLI configuration.

## 4. Execute, approve, accept and recover

Start selected services and submit the original task using the [formal task sequence](tasks.md#formal-task-sequence-and-recovery). Retain task ID, creation/submission intent SHAs and original workflow/run IDs. After plan, read the actual plan and explicitly approve its exact SHA with a stable decision ID, then continue work→integrate→verify→review.

`REVIEW_READY` identifies an exact candidate for maintainer inspection. Check candidate, actual checks, every required review and original artifacts, then export a per-task local branch, independently verify again and follow the project's own MR/integration process. Model approval, process exit0 and issue closure each cannot replace that workflow.

If a new task uses issue provenance v7, [check the candidate remotely](../projects/candidate-actions.md#check-the-candidate-and-current-remote-branches) after export to compare local/remote head/base. This only observes current facts, without pushing, linking a PR or replacing human review. Tasks without provenance retain original export/project-publication workflows.

On a lost reply, query original IDs: `task creation` for creation, `task submission` for submission, `task approval` for approval and `task export-status` for export. Use each returned original intent in the corresponding resume command. Reconcile unknown state before proceeding; do not change IDs and resend. After closure, check external jobs/leases. Back up control home, execution CONFIG/STATE, Git repositories and Temporal persistent data together; see the [recovery table](tasks.md#formal-task-sequence-and-recovery) and [coordinated backup](../operations/backup-recovery.md).

## 5. Training proposals and actual experiments

Prepare an actual workload, baseline, exact experiment manifest and correctness criteria first. For specialist proposals alone, a lightweight `ergora project add PROJECT_ID --repo ABSOLUTE_REPO` project suffices. Save the complete training manifest through step 1 and prepare UTF-8 task text containing every predecessor material required by the selected leaf.

Complete [step 2's shared runtime preparation](#2-register-your-project): Linux/WSL2, task-mcp in the same Ergora interpreter and selected backend authentication.

Complete authentication supported by the chosen backend. Codex can also receive `--codex-config ABSOLUTE_CONFIG_PATH`, whose configuration references external credential variables. Claude bare mode needs supported API-environment authentication. In the task, require complete fixed-task MCP reading of the leaf's own and all structural ancestors' Skills/context, paging long UTF-8 attachments continuously to `next_offset: null`. After dependencies, authentication and task text are ready:

```bash
ergora composition prepare-from-manifest TRAINING_MANIFEST_DIRECTORY root/analysis/design --task experiment-task.txt --directory ./prepared-design --max-prompt-bytes 50000
ergora composition check-input PROJECT_ID ./prepared-design --mode task-mcp --backend codex --backend-reason "Explicit experiment-design backend"
ergora composition run-input PROJECT_ID ./prepared-design --mode task-mcp --backend codex --backend-reason "Explicit experiment-design backend" --timeout 300
```

`check-input` checks capabilities/input without invoking a model. See [single-leaf calls and reading verification](../definitions/workflows/leaf-calls.md#call-a-prepared-leaf) for the complete workflow.

Other leaves are `root/analysis/profile`, `root/kernel/assess` and `root/measurement/review`. Single-leaf calls do not execute predecessors automatically; explicitly include complete provenance and predecessor replies in new task text. Bundled leaf overrides must satisfy their model minimum; review uses a separate session. After failure, retain the original run without automatic backend switching or downgrades. Other-backend fallback examples apply only to custom definitions without this minimum. Successful authentication still needs a real small invocation to establish inference availability. Broader tool permissions cannot establish repair of an upstream API error.

For specialized knowledge, choose an available direction in the [independent optimization table](../training/specialists.md#independent-optimization-direction-subtemplates). Each reads complete direction-specific context and reuses v2 specialists. Most retain design/profile/measurement leaves, with both complete original preceding results manually supplied to measurement. Low-precision/kernel directions also include a kernel leaf that receives both complete analyses, then all three complete results go to measurement. Installing proposal bundles does not install GPU tools, enable native search or execute the complete graph.

Proposals/model reviews help operators prepare experiments. Actual execution is pinned workload/baseline/experiment→trusted runner→independent correctness/performance verification→human approval of the original evidence SHA→integration verification in that project's development task. Optional ForgeKernel generation has separate version/model/device requirements; generator completion is not performance acceptance or adoption. Install CPU/GPU/data/ML dependencies per project. The console does not configure CUDA or request devices. See [training](../training/overview.md) for runners, negative results, cancellation and adoption.

The complete Linux reference distribution retains two detailed manuals: [deployment/daily use (Chinese source)](../../src/ergora/data/reference/platform/README.zh-CN.md) and [training optimization (Chinese source)](../../src/ergora/data/reference/platform/docs/TRAINING.md). They describe the frozen v2.2 reference layer. Current linked guides govern console and composition usage. The single-file HTML embeds the old reference package/manuals; new control-plane features need a separate installation of the current repository.

## The three templates and formal tasks

```bash
ergora templates list
ergora templates copy repository-governance ./governance-task
ergora templates copy large-change ./development-task
ergora templates copy training-optimization ./training-task
ergora workflow --help
ergora reference verify
ergora reference info
```

The copy destination must be new. Templates define task and evidence requirements. Example PASS values, SHAs and metrics are not actual results. Governance and large development retain `inventory → plan → work → integrate → verify → review`; the complete reference runtime still owns plan approval and final evidence.

For Temporal, MLflow, Symphony, A2A, Supervisor and the complete executor, use the [single-file installation distribution](../distribution/multi-agent-development-platform.html) or installer supplied through packaged reference entry points. The HTML embeds complete install scripts, source ZIP, three templates and two complete reference manuals. It targets Ubuntu 24.04 / Linux x86_64; installation requires network access and package-manager privileges inside the target system.

- [Complete deployment and daily-use reference (Chinese source)](../../src/ergora/data/reference/platform/README.zh-CN.md)
- [Complete training-optimization reference (Chinese source)](../../src/ergora/data/reference/platform/docs/TRAINING.md)
- [Training through the new entry point](../training/overview.md)

These frozen reference files retain v2.2 content identity for verification. This guide and the integration guide describe new control-plane capabilities; they do not rewrite the old HTML's embedded package. Configure Temporal in the current shell before using the local reference-task CLI; see [a first development task](tasks.md).

Continue: [Prepare a task's frozen composition](preparation.md) · [Create a formal development task](tasks.md).
