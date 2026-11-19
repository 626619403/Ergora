<a id="模板入门旅程"></a>
# Template walkthroughs

English · [简体中文](zh-CN/TEMPLATE_WALKTHROUGHS.md)

This guide connects installation, specialist compositions, formal development and training experiments. Start with [installation and daily use](USAGE.md), or the [Windows guide](WINDOWS.md). The basic control plane includes CLI, SQLite and local pages. Complete six-stage execution additionally needs a Linux/WSL2 reference environment, selected services and authenticated Agents. A development/research installation profile adds SDKs; prepare services, models, project checks and GPUs separately as needed.

Follow [source-branch selection](USAGE.md#从空环境安装) to install the current main branch or pinned commit. An identical package version does not guarantee the preset/composition commands below.

|Template/preset|Current bundled root identity|Specialist relationships and entry points|
|---|---|---|
|repository-governance|`ergora-governance-template@1.1.0`|Parallel knowledge-map/boundary-test, then trusted integration/verification and structure, correctness and test-value reviews|
|large-change|`ergora-large-change-template@1.1.0`|contract→parallel server/client→integration-tests, then trusted integration/verification and three reviews|
|training-optimization|`ergora-training-proposal@4.2.2`|Source flow→planning/diagnosis→kernel implementation planning→measurement review; all five leaves inherit library/environment guidance, with actual experiments owned by trusted runners.|
|optimization-memory-tuning|`ergora-opt-memory-tuning-proposal@1.2.0`|Capacity/allocator materials plus shared design/diagnosis specialists, followed by independent measurement-evidence review|
|optimization-activation-recompute|`ergora-opt-activation-recompute-proposal@1.2.0`|Recompute boundaries, numerical and graph/offload constraints; read-only subtemplate reusing v2 specialists|
|optimization-cpu-offloading|`ergora-opt-cpu-offloading-proposal@1.2.0`|Separates three offload interfaces and host/transfer/compute costs; reuses v2 specialists|
|optimization-tp-dp-overlap|`ergora-opt-tp-dp-overlap-proposal@1.2.0`|Actual TP/DP/PP overlap paths, critical paths and independent measurement; read-only proposals|
|optimization-moe-dispatcher|`ergora-opt-moe-dispatcher-proposal@1.2.0`|Pinned backend/ABI/topology, routing and all-rank evidence; read-only proposals|
|optimization-moe-overlap|`ergora-opt-moe-overlap-proposal@1.2.0`|Separately attributes ordinary EP overlap/delayed wgrad, reusing the same v2 specialists|
|optimization-profiling|`ergora-opt-profiling-proposal@1.2.1`|Steady-state traces/ranks/interval unions and actual dependency evidence; shared design/diagnosis followed by independent measurement review|
|optimization-memory-snapshot|`ergora-opt-memory-snapshot-proposal@1.2.0`|Allocator/history/step differences from trusted summaries; parsing/collection remain with original owners|
|optimization-recipe-model|`ergora-opt-recipe-model-proposal@1.2.0`|Task/model/recipe matching, semantic invariants and missing framework adaptation; shared v2 specialists' read-only proposals|
|optimization-model-verification|`ergora-opt-model-verification-proposal@1.2.0`|Checks conversion/forward/training/recovery/quality claims individually using original metrics beyond exit0; execution stays with original owners|
|optimization-cluster-resiliency|`ergora-opt-cluster-resiliency-proposal@1.2.0`|Launch/original-job identity, logs and checkpoint/recovery evidence; three reused v2 read-only specialists, with cluster actions owned by the original executor|
|optimization-low-precision|`ergora-opt-low-precision-proposal@1.2.0`|Read-only low-precision design/profile→kernel→measurement proposals; original experiment and quality/performance gates retained|
|optimization-kernel|`ergora-opt-kernel-proposal@1.2.0`|Operator/wrapper and independent-validation design/profile→kernel→measurement proposals; native execution and actual measurements remain separate|
|refactoring|`ergora-refactoring-template@1.3.0`|Preparation→rewrite→compatibility→original trusted integration/verification→three reviews; ordinary parent references one native large-change six-stage instance|
|optimization-performance-diagnosis|`ergora-opt-performance-diagnosis-proposal@1.2.1`|Same-symptom feedback commands and report-specific tool selection; read-only design/profile→measurement proposals|

Each Agent is an independently versioned package with its own specialties, initial instructions, Skills and backend. The structural parent chain accumulates complete materials and constrains child permissions. Dependency edges order execution; named ports carry results. Expand these three relationships in “Agent and composition library”. See [definition format and inheritance](WORKFLOW_DEFINITIONS.md).

Refactoring uses the [native six-stage instructions](USAGE.md#使用重构配方) and [complete example](../examples/composition/refactoring/README.md). The two-domain page steps below include independent inventory/planning and the original work/review contract. For refactoring, select “Complete manifest · Native six stages” in the same form, configure preparation leaves/native instance/work and review subgraphs/budget, explicitly authorize preparation, then preview/create. Before choosing the recipe, pin actual callers, behavior to preserve, migration order and rollback checks. It uses original task/run/candidate identities and approval. To include project memory or active Skills, freeze exact current sources through [material selection](USAGE.md#为正式任务选择项目记忆与活动-skill).

Ergora maintains these engineering roles, initial instructions and compositions; see [Agent definitions](AGENT_DEFINITIONS.md#内置专家). They are versioned/selected separately from concrete Codex/Claude Code backends. See the [training guide](TRAINING.md#独立的优化方向子模板) for the complete optimization-direction table; templates do not each import an upstream native Agent directly.

## Current execution boundaries

Presets and static graphs do not implement generalized Repeat, a mixed-graph scheduler or unified fixed/preset/planner/automatic reasoning selection. Current explicit backend fields request supported model options, without proving actual applied effort. Complete ancestor materials and narrowing permissions remain frozen into supported task/leaf inputs. [Current backend limits](AGENT_BACKENDS.md#current-configuration-evidence-and-pending-capabilities) describe these boundaries.

Schema2 design-policy registration remains storage-only with execution unsupported. Inspection-only [source-journal storage](USAGE.md#保存完整设计来源与原答复) is Linux/WSL2-only and requires a legitimate original design-packet. Trusted human assurance and F/J/G remain unavailable. Finite training controllers use a separate [explicit authorization and submission flow](TRAINING.md#起算本地训练预算与恢复原授权). Importing definitions or saving a manifest does not authorize these effects.

<a id="1-准备模板与完整组合"></a>
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
ergora composition show ergora-governance-template 1.1.0 --material > "$WALKTHROUGH_HOME/root.json"
python3 - "$WALKTHROUGH_HOME" <<'PY'
import json, pathlib, sys
directory = pathlib.Path(sys.argv[1])
definition = json.loads((directory / "root.json").read_text())["definition"]
grant = {"schema_version": 1, "permissions": definition["permissions"], "limits": definition["limits"]}
(directory / "grant.json").write_text(json.dumps(grant, indent=2) + "\n")
PY
ergora composition preview ergora-governance-template 1.1.0 --grant "$WALKTHROUGH_HOME/grant.json"
```

Review the complete preview's instances, ancestor materials and authorization limits. Use the actual returned `preview_sha256` for `PREVIEW_SHA256` below:

```bash
ergora composition freeze-manifest ergora-governance-template 1.1.0 --grant "$WALKTHROUGH_HOME/grant.json" --preview-sha256 PREVIEW_SHA256
```

Retain returned complete-package `path`, package `digest` and `manifest.preview_sha256`, then run `ergora composition verify-manifest FULL_MANIFEST_DIRECTORY`. When changing domain, use its root ID above and obtain/review that root's grant again; training roots request neither shell nor write permission. The page can also preview and “Save current preview as complete manifest”. Downloaded preview JSON is for reading; sharing/backups need the complete directory. See [complete bundles](WORKFLOW_DEFINITIONS.md#保存和分享完整组合).

<a id="2-登记自己的项目"></a>
## 2. Register your project

Each business project uses its own Git repository/tracker. First create an actual Git commit. Configure absolute execution paths, allowed changes and actual trusted checks through [project definitions](PROJECTS.md), then run `ergora project register project.json --revision 0`. GitHub/GitLab repositories are not prerequisites: local trackers work, with a separate local branch exported per task. Code branches and issue records have distinct identities; one shared business repository need not hold every project.

Formal development compositions and training task-mcp leaves require Linux/WSL2 and the optional `task-mcp` dependency. control/development/research installation profiles do not add this extra automatically. Static import/preview/freeze and contract creation do not require it, so successful creation still needs runtime preparation. From the installed version's repository root, install in the same Python environment running Ergora and its executor. For the default Bash installer:

```bash
"$HOME/.local/share/ergora-app/venv/bin/python" -m pip install '.[task-mcp]'
```

Use your own Ergora interpreter for custom environments/install locations; installing into another Python does not satisfy the executor dependency. Native Windows can first use the console, definitions and text-only capabilities. Fixed-task MCP reads and complete development execution use Linux/WSL2. Complete selected-Agent [installation/authentication](USAGE.md#安装与认证-agent-cli) and provide its authentication/inference configuration to the environment actually starting Ergora/executor. Other backends apply to custom definitions without this model minimum; Claude task-mcp bare mode requires its supported API-environment authentication. Keep credential values out of tasks/definitions. Check services, roles and project checks separately; a version/authentication probe does not replace an actual task.

Governance requires behavior/architecture/knowledge checks; large changes additionally require integration/compatibility/migration-rollback. These are executable project acceptance checks using the project's actual commands. Prepare complete runtime/services/model authentication through the [deployment steps](USAGE.md#三个模板与正式任务). `doctor`, service RUNNING and successful creation each establish only their own state.

<a id="3-页面创建开发任务"></a>
## 3. Create development tasks in the page

Run `ergora serve` and open local `http://127.0.0.1:8977`. Under “Formal tasks”:

1. Open “Preview and create”, select a registered template and “Load selected template”. Wait for “Template input loaded” before entering task ID, issue and actual input. Changing template invalidates the old preview.
2. Select “Complete manifest · Composition execution and review”, enter step 1's `manifest.preview_sha256` and “Read complete manifest”. Use `root/review` for review and `root/work` for execution. Under “Inventory and planning”, select `root/preparation/inventory` and `root/preparation/plan`, with repository read paths covering the work units. Both preparation specialists default to gpt-6.1-sol max.
3. “Load work units from current input”, assigning every unit to its complete path. Governance uses `knowledge-map`, `boundary-test`; large changes use `contract`, `server`, `client`, `integration-tests`, at `root/work/UNIT_ID`.
4. Explicitly choose a supported backend, execution boundary and override reason for every writer. Current writable compositions prefill the template model/effort for Codex; explicitly choose “Trusted current container/user”, still requiring trusted Linux. This permits access to current-user files; permission-path checks do not provide OS isolation for individual file accesses.
5. Keep gpt-6.1-sol high for review; overrides must meet the definition minimum. Record the reason for separate sessions on the same backend and select that diversity policy. Configure authentication in the environment starting Ergora, keeping keys in external environment/tool-authentication configuration.
6. “Preview frozen contract”, checking complete assignments, backends/policies, ancestor materials, paths and input, then “Confirm creation of frozen contract”. The page freezes inventory, planning, work and review members together; omitting preparation fails visibly. Creation publishes a contract without starting a model or task.

A template can contain multiple same-responsibility specialist instances. Before adding/replacing specialists, publish separate Agents and exact workflow versions along the parent chain, then preview/freeze a new task. The graph shows published versions; dragging layout does not revise contracts. See [work-unit protocol](WORKFLOW_DEFINITIONS.md#专长执行者与原工作单元) for complete CLI configuration.

<a id="4-运行批准验收与恢复"></a>
## 4. Execute, approve, accept and recover

Start selected services and submit the original task using the [formal task sequence](USAGE.md#正式任务的操作顺序与恢复). Retain task ID, creation/submission intent SHAs and original workflow/run IDs. After plan, read the actual plan and explicitly approve its exact SHA with a stable decision ID, then continue work→integrate→verify→review.

`REVIEW_READY` identifies an exact candidate for maintainer inspection. Check candidate, actual checks, every required review and original artifacts, then export a per-task local branch, independently verify again and follow the project's own MR/integration process. Model approval, process exit0 and issue closure each cannot replace that workflow.

If a new task uses issue provenance v7, [check the candidate remotely](USAGE.md#核对候选与当前远端分支) after export to compare local/remote head/base. This only observes current facts, without pushing, linking a PR or replacing human review. Tasks without provenance retain original export/project-publication workflows.

On a lost reply, query original IDs: `task creation` for creation, `task submission` for submission, `task approval` for approval and `task export-status` for export. Use each returned original intent in the corresponding resume command. Reconcile unknown state before proceeding; do not change IDs and resend. After closure, check external jobs/leases. Back up control home, execution CONFIG/STATE, Git repositories and Temporal persistent data together; see the [recovery table](USAGE.md#正式任务的操作顺序与恢复) and [coordinated backup](BACKUP_RECOVERY.md).

<a id="5-训练提案与实际实验"></a>
## 5. Training proposals and actual experiments

Prepare an actual workload, baseline, exact experiment manifest and correctness criteria first. For specialist proposals alone, a lightweight `ergora project add PROJECT_ID --repo ABSOLUTE_REPO` project suffices. Save the complete training manifest through step 1 and prepare UTF-8 task text containing every predecessor material required by the selected leaf.

Complete [step 2's shared runtime preparation](#2-登记自己的项目): Linux/WSL2, task-mcp in the same Ergora interpreter and selected backend authentication.

Complete authentication supported by the chosen backend. Codex can also receive `--codex-config ABSOLUTE_CONFIG_PATH`, whose configuration references external credential variables. Claude bare mode needs supported API-environment authentication. In the task, require complete fixed-task MCP reading of the leaf's own and all structural ancestors' Skills/context, paging long UTF-8 attachments continuously to `next_offset: null`. After dependencies, authentication and task text are ready:

```bash
ergora composition prepare-from-manifest TRAINING_MANIFEST_DIRECTORY root/analysis/design --task experiment-task.txt --directory ./prepared-design --max-prompt-bytes 50000
ergora composition check-input PROJECT_ID ./prepared-design --mode task-mcp --backend codex --backend-reason "Explicit experiment-design backend"
ergora composition run-input PROJECT_ID ./prepared-design --mode task-mcp --backend codex --backend-reason "Explicit experiment-design backend" --timeout 300
```

`check-input` checks capabilities/input without invoking a model. See [single-leaf calls and reading verification](WORKFLOW_DEFINITIONS.md#调用一个准备好的叶子) for the complete workflow.

Other leaves are `root/analysis/profile`, `root/kernel/assess` and `root/measurement/review`. Single-leaf calls do not execute predecessors automatically; explicitly include complete provenance and predecessor replies in new task text. Bundled leaf overrides must satisfy their model minimum; review uses a separate session. After failure, retain the original run without automatic backend switching or downgrades. Other-backend fallback examples apply only to custom definitions without this minimum. Successful authentication still needs a real small invocation to establish inference availability. Broader tool permissions cannot establish repair of an upstream API error.

For specialized knowledge, choose an available direction in the [independent optimization table](TRAINING.md#独立的优化方向子模板). Each reads complete direction-specific context and reuses v2 specialists. Most retain design/profile/measurement leaves, with both complete original preceding results manually supplied to measurement. Low-precision/kernel directions also include a kernel leaf that receives both complete analyses, then all three complete results go to measurement. Installing proposal bundles does not install GPU tools, enable native search or execute the complete graph.

Proposals/model reviews help operators prepare experiments. Actual execution is pinned workload/baseline/experiment→trusted runner→independent correctness/performance verification→human approval of the original evidence SHA→integration verification in that project's development task. Optional ForgeKernel generation has separate version/model/device requirements; generator completion is not performance acceptance or adoption. Install CPU/GPU/data/ML dependencies per project. The console does not configure CUDA or request devices. See [training](TRAINING.md) for runners, negative results, cancellation and adoption.

The complete Linux reference distribution retains two detailed manuals: [deployment/daily use](../src/ergora/data/reference/platform/README.zh-CN.md) and [training optimization](../src/ergora/data/reference/platform/docs/TRAINING.md). They describe the frozen v2.2 reference layer. Current linked guides govern console and composition usage. The single-file HTML embeds the old reference package/manuals; new control-plane features need a separate installation of the current repository.
