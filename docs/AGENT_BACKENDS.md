<a id="模板角色与可替换-agent"></a>
# Template roles and interchangeable Agents

English · [简体中文](zh-CN/AGENT_BACKENDS.md)

See the [specialist Agent definition library](AGENT_DEFINITIONS.md) for shareable specialist recipes and the [workflow invocation guide](WORKFLOW_DEFINITIONS.md#调用一个准备好的叶子) for restricted single-leaf calls with complete ancestor materials. Project-role bindings and formal six-stage execution retain this guide's entry points.

Templates save objectives, roles, capabilities, artifacts and acceptance requirements; projects save concrete tools. `ergora templates copy` adds `agent-contract.json` alongside the original files without changing frozen reference contracts. Inspect roles:

```bash
ergora templates agents repository-governance
ergora templates agents large-change
ergora templates agents training-optimization
```

Governance and large development provide inspector / planner / implementer / reviewer roles. The executor still owns integrate, verify and trusted work test-results. Training provides experiment-planner / performance-analyst / kernel-tuner, producing proposals, analysis and candidate descriptions respectively. Select native kernel-generation tools in the separate `kernel` layer.

See [Agent CLI installation](USAGE.md#安装与认证-agent-cli) for initial Codex / Claude Code installation, authentication and official entry points. These steps assume the selected command is available on the PATH of the shell starting Ergora.

After binding, run `ergora tools doctor PROJECT`. Explicit version/credential/TCP probes use `--probe --timeout 5`; see [diagnostics](USAGE.md#诊断与修复) for each result, budgets and repair entry points. Existing Codex credentials and a successful actual model task are separate facts, neither automatically granting Agent acceptance.

A Linux unified project can explicitly start selected `temporal/worker/executor/a2a` services through [service management](USAGE.md#显式服务管理). Services start only when selected. Stopping requires confirmation and actual status observation; the original running stack is not taken over automatically. The managed executor uses frozen role snapshots in this control directory. Use `ergora task list PROJECT` / `task show PROJECT TASK_ID` to [read existing formal tasks' frozen contracts](USAGE.md#读取正式任务合同), without inferring live Temporal state. The primary entry also [previews, creates and recovers tasks](USAGE.md#预览与创建正式任务), freezing role configuration at creation. `task status` provides [native runtime observations](USAGE.md#查询正式任务运行状态). Use the [unified submission/recovery entry](USAGE.md#提交正式任务与恢复未知结果), [exact-plan approval](USAGE.md#批准精确计划与恢复投递), [original-run cancellation](USAGE.md#请求取消与恢复未知投递) and [exact-candidate export](USAGE.md#导出精确候选与恢复回执). Tasks born through the legacy entry retain this guide's reference commands.

`control`, `development` and `research` are control-plane SDK [installation profiles](USAGE.md#选择安装组合), without installing or selecting a particular Agent. Configure Codex/Claude as below; mini-swe-agent and ForgeKernel retain the pinned-source installers below. Changing profile does not modify existing project bindings.

See the [Windows guide](WINDOWS.md#agent-安装与认证) for native installation/authentication. Native role calls support Codex, Claude Code and explicit program/interpreter `.exe` files; `.cmd` / `.bat` launchers are explicitly refused. The mini Bash driver, ForgeKernel and formal six-stage bridge require WSL2/Linux; the formal reference executor additionally needs a trusted Linux container. Keep Codex's native sandbox on Windows; the Linux `current-container` selection is unavailable there.

<a id="项目选择与独立调用"></a>
## Project selection and standalone calls

Select a tool for each role in the console's “Tool bindings”, or use JSON:

```json
{"tool":"codex","model":"YOUR_MODEL_ID"}
```

```bash
ergora project show my-project
ergora project bind my-project planner --binding planner.json --revision CURRENT_REVISION
ergora agent run my-project planner --prompt plan-request.md --template repository-governance
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

`--template` requires the role's actual structured artifacts; omitting it retains ordinary text invocation. Neither grants formal acceptance. Codex uses the role's default CLI sandbox. If the system cannot provide that sandbox, explicitly set `"sandbox":"current-container"` only after accepting the current container/user boundary. There is no automatic downgrade. Claude Code owns its authentication; its review/proposal roles use Read/Grep/Glob with session persistence and extra MCP configuration disabled. Codex remains the default reviewer.

<a id="为每个-agent-设置思考强度"></a>
### Set reasoning effort for each Agent

Add `reasoning_effort` to a Codex binding or `effort` to a Claude Code binding, for example:

```json
{"tool":"codex","model":"YOUR_MODEL_ID","reasoning_effort":"high"}
```

```json
{"tool":"claude-code","model":"YOUR_MODEL_ID","effort":"medium"}
```

Set project roles in “Tool bindings” or `project bind`; set specialist instances in their `agent.json.backend` or the formal task's `composition.backend_overrides[实例路径].binding`. Formal tasks freeze the complete configuration. Changing project bindings or publishing an Agent version does not rewrite existing tasks. Parallel review branches can select separate backends, models and effort, following the original DAG and ancestor concurrency quotas.

Codex choices are `low/medium/high/xhigh/max/ultra`; an explicit binding overrides `model_reasoning_effort` from `--codex-config`. Claude choices are `low/medium/high/xhigh/max/ultracode`, projected as native `--effort`. Omitting a field retains the CLI's existing settings; other backends do not expose these fields. Availability depends on the selected model, CLI, account and service. Ergora records explicit requests without estimating or promising equal computation across backends. Claude organization policies may cap effective effort; in JSON mode, relevant warnings may appear only in native debug logs. Requested effort alone does not establish applied effort.

See [official Codex configuration](https://developers.openai.com/codex/config-reference/), [Claude CLI flags](https://code.claude.com/docs/en/cli-reference#cli-flags) and [Claude model configuration](https://code.claude.com/docs/en/model-config). Binding validation refuses unsupported fields. Whether an accepted field works at the model still needs an actual invocation.

### Current configuration evidence and pending capabilities

Keep three facts separate: the requested level in a binding/frozen configuration; the arguments/configuration projected to the native CLI; and native/model behavior actually observed. Codex projects `reasoning_effort` to `-c model_reasoning_effort=...`; Claude projects `effort` to `--effort`. Those arguments establish a CLI request, not an applied model level or a verified provider request. Without native evidence, applied effort remains unknown. Do not infer it from process success, structured output or an accepted binding.

Only explicit binding values and existing defaults are implemented. Unified fixed/preset/planner/automatic selection and its configuration/freeze contract remain future work. Existing workflow presets and native CLI profiles do not implement tuning presets or automatic selection. Model/effort fallback and larger budgets require their own explicit policy; do not silently change them. Claude text-only adds `--safe-mode`; the documented native behavior disables workflows, so an `ultracode` request does not establish an active ultracode workflow. Native precedence/caps and actual application remain separate. See the [backend guide](AGENT_BACKENDS.md#为每个-agent-设置思考强度).

DeepSeek's current `context_window`/`max_tokens` populate SDK model-registry capacity descriptions; this is not a verified per-request hard token cap. Retain the original per-call wall-time, reported-cost and continuation semantics rather than treating different native controls as a common budget guarantee.

Backend selection does not enable new design gates or training effects. Current schema2 design-policy registration remains [storage-only with execution unsupported](PROJECTS.md#current-limits-of-design-policy-registration). The isolated source-journal draft is not released, trusted owner/material/gate handling remains pending, and schema3 training effects stay disabled. Existing schema1 task contracts retain their original scope.

<a id="用-ergora-审查自己的仓库"></a>
### Review a repository using Ergora

Register this or another repository as a review project and select an available reviewer backend different from the actual author's. For example, write `reviewer.json` as `{"tool":"claude-code"}`, then run:

```bash
ergora project add self-review --repo /PATH/TO/REPOSITORY
ergora project show self-review
ergora project bind self-review reviewer --binding reviewer.json --revision CURRENT_REVISION
ergora agent run self-review reviewer --prompt review-request.md --template repository-governance --timeout 900
ergora agent runs self-review
ergora agent output self-review RUN_ID
```

In `review-request.md`, give original requirements and the exact candidate SHA. For uncommitted work, separately list complete changes, new files and digests. Supply actual validation commands/results and unverified scope, and specify read-only inspection boundaries. If specialist instructions are needed, obtain them with `show --material` in the [definition library](AGENT_DEFINITIONS.md) and explicitly include them. Definitions/inherited resources are not loaded automatically here. Backends retain their own login/environment; do not include keys in the request.

Allow read methods the selected backend actually has. Codex typically inspects source with read-only shell commands; Claude can use Read/Grep/Glob. Do not forbid all commands while listing only another backend's proprietary tools. Alternatively attach complete new-file contents and check input digests. Recheck material readability after changing backend. A request-changes result caused by inability to inspect is not a confirmed source defect.

This template requires `review-report`, `handoff` and explicit `approve/request-changes`. Inspect original structured results/digests in run records and resolve each finding. Process success, structural validity and review approval need separate checks. Failure/timeout is not a pass. Retain reasons for same-backend fallback. A standalone independent call produces no formal workflow approval or trusted acceptance.

<a id="自定义命令"></a>
### Custom commands

An ordinary `{"tool":"command","argv":["/path/to/program"]}` continues receiving plain stdin text. Formal stages or `--template` calls require:

```json
{
  "tool": "command",
  "argv": ["/path/to/agent-wrapper"],
  "protocol": "stage-json-v1",
  "capabilities": ["repository-read", "plan-write"]
}
```

stdin is `{schema_version, role, prompt, result_schema}`. stdout must contain only one JSON object matching result_schema; write diagnostics to stderr. The schema requires summary and required artifacts, plus explicit approve / request-changes for review. Declared capabilities must cover the role's requirements. They declare compatibility, without proving tool quality or isolation. Execute commands through argv; templates embed no commands.

### mini-swe-agent

```bash
bash scripts/install-agent.sh mini-swe-agent
```

Pinned source and its independent venv default to `~/.local/share/ergora-tools/mini-swe-agent/`. Put that Python's absolute path in the implementation-role binding:

```json
{
  "tool": "mini-swe-agent",
  "python": "/YOUR_HOME/.local/share/ergora-tools/mini-swe-agent/.venv/bin/python",
  "model": "YOUR_PROVIDER/YOUR_MODEL",
  "step_limit": 30,
  "cost_limit": 3.0
}
```

The provider's environment variables supply authentication. mini supports implementation, without serving as a read-only independent reviewer. Its driver uses native LiteLLM tool-call models and consistent Bash tool instructions, retaining the trajectory. On completion it writes final text to the submission file in the run archive, then uses the prompted command to submit the body to the same structural validation. Empty submission fails. Shell actions remain in the outer monitor's process group under the overall task timeout; one action can consume all remaining time. Costs use upstream reports. One API request may exceed the remaining budget; this is not a prepaid-spend ceiling. Installation and CPU SDK checks do not establish model quality.

<a id="deepseek-harness-只读叶后端"></a>
### DeepSeek Harness read-only leaf backend

The optional adapter pins SDK/runtime-bin `0.2.2rc2` in a separate environment; basic Ergora does not depend on it. Supported Linux/WSL2 entry points are `composition check-input/run-input` in `text-only` or `task-mcp` mode for reviewer, experiment-planner, performance-analyst and kernel-tuner roles. The last two produce textual proposals, not measurements or kernel execution. This backend supports independent restricted calls and saved-history observation. Persistent native development sessions, native `agent run`, workspace writes and formal-task recovery remain unsupported. OpenHands SDK is not registered.

After the installer provides uv, install separately in persistent storage:

```bash
ERGORA_DSH_ENV="$HOME/.local/share/ergora-tools/deepseek-harness/0.2.2rc2/.venv"
uv venv --python 3.12 "$ERGORA_DSH_ENV"
uv pip install --python "$ERGORA_DSH_ENV/bin/python" \
  'deepseek-harness-sdk==0.2.2rc2' 'deepseek-harness-runtime-bin==0.2.2rc2'
```

Set the complete `backend` in a [new version of the selected Agent definition](AGENT_DEFINITIONS.md#从固定原包派生新版本). Replace the interpreter with the actual absolute path above and the model/URL with values for your service:

```json
{
  "tool": "deepseek-harness",
  "python": "/YOUR_HOME/.local/share/ergora-tools/deepseek-harness/0.2.2rc2/.venv/bin/python",
  "model": "YOUR_MODEL_ID",
  "base_url": "https://YOUR_PROVIDER/v1",
  "api_key_env": "LINGZHI_API_KEY",
  "api": "openai-responses",
  "context_window": 131072,
  "max_tokens": 4096
}
```

`api` explicitly selects `openai-responses` or `openai-completions`; omission retains Chat Completions. Choose an interface the service actually provides. The platform does not switch protocols automatically after failure. Task MCP additionally requires compatible tool calls and SSE on that protocol. The shell starting Ergora supplies environment variables; do not put keys in JSON. Configure `context_window` and `max_tokens` for the actual model; defaults do not prove service capacity. Package-version diagnostics call no model and establish neither authentication, gateway nor model quality.

Publish the new Agent version and prepare new input through parent references, retaining complete ancestor materials and permission ceilings, then invoke:

```bash
ergora composition check-input my-project ./prepared-review --mode task-mcp
ergora composition run-input my-project ./prepared-review --mode task-mcp --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

This uses the leaf definition's complete backend configuration. `--backend deepseek-harness` alone does not supply the required interpreter, service or credential-variable name. Explicit text-only mode suits inline-only materials. Use task-mcp for Skill attachments and inspect original receipts through [complete-read verification](WORKFLOW_DEFINITIONS.md#核验完整附件读取).

Default calls use a fresh native home/session, fixed minimal profile and generated patch, without native shell, file, working-directory or extra MCP tools. Task MCP exposes only the original scope's list/read. The adapter saves native identities, complete prompt, events and terminal value in this call's `.protocol` directory. The original process owner retains overall timeout/stop responsibilities. This provides no OS isolation.

Check completion status, strict JSON/original result schema and the original MCP connection receipt together. Any native tool error fails the call, without implicit retry or session continuation. Upstream may return completed after plugin failure/disconnection, so final text alone is not success. On failure or an unknown result, inspect evidence by original run ID before proceeding. Do not create another call as purported recovery. Formal six-stage execution, persistent sessions and other platforms require their own supported backend contract and acceptance.

<a id="查看已保存的原生历史"></a>
#### Read saved native history

On Linux/WSL2, select “Read native history” on the original invocation record and page through saved inputs, tool results and model replies. Reading accesses only that run's archive, without starting the SDK, invoking models or restoring a session. Other backends report unsupported. Original stdout/stderr viewing remains available.

```bash
ergora agent output my-project RUN_ID --native-history
# Next page: use next_offset and revision from the previous response.
ergora agent output my-project RUN_ID --native-history \
  --history-offset NEXT_OFFSET --history-revision REVISION
```

Each page defaults to at most 65,536B; choose 4–65,536B with `--history-limit`. Cursors use bytes and preserve UTF-8 boundaries. The page displays only the current window. For a complete export, save successive `native_history.content` values until `next_offset` is null. Observed revision binds current file identity and time/size, not a complete content SHA or proof the writer stopped. A changed file refuses an old page. “Read from start” or restart at zero without the old revision. Only the original saved uncompressed v4 single-session archive is supported. Missing archives, mismatched IDs/directories or future storage generations are not empty history. Archive EOF does not mean successful completion; original call status and result receipts remain separate checks.

<a id="项目原生开发会话"></a>
#### Project native development sessions

The ordinary `agent run` path can save a project session with an explicit birth intent and project revision. Select its original history and continue with a new prompt through `agent continue` or the project overview's “项目会话 / 运行 Agent” dialog. Role, template artifacts, selected Skills, memory and native configuration freeze at session creation; later turns use the same native workspace permissions. This is separate from formal-task execution and approval. The Codex session command uses `--no-daemon`; only the turn's owned process subtree is covered by its cleanup evidence. A stopped turn with a confirmed final cleanup and usable native reference can receive a new explicit prompt; an unknown outcome cannot be replayed.

See [project-session operations](USAGE.md#project-native-sessions) for the current CLI/HTTP inputs, exact-intent observation after a lost reply and per-turn stop. The persistent interface selects Codex on Linux/WSL2; it does not enable other backends' persistent capabilities. Existing single-use composition results and native archives remain observable through their original run/output records.

<a id="可选的正式六阶段执行桥接"></a>
## Optional formal six-stage execution bridge

The default `agentflow` executor retains v2.2 behavior. To apply project-role selections to formal tasks, first install the reference runtime and configure models/trusted execution boundaries. Then [register a unified project](PROJECTS.md) with Git root, roles, templates and trusted checks together, and run `ergora reference executor --project PROJECT_ID`. The old two-registration approach remains compatible; identically named projects must use the same Git root. Enable this only for new tasks, without switching an already-started reference task midway.

Preview an existing reference project with `ergora project import-reference import.json --revision N`, review differences/file identities, then explicitly adopt with `--apply --preview-sha256 SHA`. Compatible old files retain original bytes, with before/after project and provenance records saved. It neither migrates in-flight tasks nor imports model keys. See [project definitions](PROJECTS.md#显式导入旧注册) for the complete spec and recovery commands.

Stop the original executor first, retaining Temporal, worker and other services:

```bash
"$HOME/multi-agent-platform/.venv/bin/supervisorctl" \
  -c "$HOME/.config/multi-agent-platform/supervisord.ini" stop executor
ergora reference executor --installation "$HOME/multi-agent-platform"
```

The command listens in the foreground to the original FileAdapter queue under the same executor lock, preserving original task creation, approval, cancellation, recovery and export commands. Add `--request /ABSOLUTE/PATH/envelope.json` to process exactly one published envelope. The executor verifies reference Python source identities and refuses unadapted versions.

When first processing a new task, save selected role tools/project revision in `agent-bindings.json` inside the original persistent task directory. Recovery retains that selection. Implementer and reviewer use distinct role identities, fresh sessions, exact candidate commits and original workspace-change checks. Before a formal stage ends, clean up/reap descendants, then execute the original monitor's read-only change checks using the exact configured reference Codex executable path. The reference monitor still reconciles unknown external-process outcomes. Missing capabilities, invalid result structure, command failure or read-only-stage changes cannot pass. Agent `model-log` and `agent-selection` accompany original receipt evidence.

Bridge model stages verify this task's saved `compiled.json` and stage contract, load complete template instructions from that snapshot and record their digest in `agent-selection`. Missing, changed or other-task snapshots explicitly fail, without substituting the active package. Deleting source packages does not change existing tasks' instructions; installation-profile drift is still refused under original rules. This is Ergora bridge behavior; direct `agentflow` retains original v2.2 behavior.

The unified entry's [external-evidence query](USAGE.md#核对闭合运行的外部作业证据) matches dev_submit entries in complete original-run history against trusted FileAdapter requests/receipts individually. Every known job remains unresolved even with a missing request. External confirmation is refused when the correct fence is missing, extra requests/orphan receipts exist, receipts are invalid or artifact digests are wrong. A read-only query changes no original outcome, publishes no fence and releases no lease. External termination evidence and six-stage quality outcomes remain separate. A normal REVIEW_READY also does not automatically release an issue lease when its workflow closes: export follows the original rules, or use [normal task closure](USAGE.md#正常任务完成后的关闭) when not exporting yet. To write a fence and release the exact original claim, explicitly use [reconcile/reconciliation/resume-reconcile](USAGE.md#显式终态对账与工单租约释放). It saves original outcome and independent cleanup evidence, retains original CANCEL_UNCONFIRMED and refuses release with missing evidence.

After an original v7 provenance task exports its exact candidate, follow [candidate comments](USAGE.md#为已导出的候选发布工单评论) to prepare/confirm a neutral GitHub/GitLab comment. That action separately saves intent/native receipt and reuses original task identity without changing backend, approval or export results. GitHub [native-ID label addition](USAGE.md#为已导出的候选追加-github-标签) reuses that writeback lifecycle. GitLab labels explicitly report unsupported. Selecting a tracker does not implicitly alter Agent authorization.

New records also save the effective `configuration` view, including each layer's source, validation, project revision and content digest. Read current values through `ergora project config PROJECT_ID`. Older tasks without this extra field retain their original binding snapshot, without reconstructing historical configuration. See [effective bindings and run snapshots](USAGE.md#有效绑定与运行快照) for its scope versus standalone-call context.

For long-running unified projects, prefer `ergora services start PROJECT temporal worker executor a2a --revision N` to manage the selected stack without hand-editing ini. The following applies only to legacy deployments retaining original Supervisor: in `~/.config/multi-agent-platform/supervisor.d/executor.ini`, change the program's `command` to the absolute Ergora executable plus `reference executor --installation ...`, retaining stopasgroup/killasgroup. Run supervisorctl `reread` / `update`. Reference-distribution initialization may regenerate this file; check after upgrading. Do not run old and new executors together.

The bridge retains Codex TOML/API variables from reference configuration. The reference monitor's credential whitelist does not forward arbitrary shell variables. Other providers may use their own persistent login or the reference `credentials.json` 0600 credential mapping. Templates, bindings and repositories store only credential-variable names/metadata. Standalone active-Skill/memory options do not automatically rewrite formal-task context.

<a id="forgekernel-原生候选"></a>
## ForgeKernel native candidates

```bash
bash scripts/install-agent.sh forgekernel
```

Default source is `~/.local/share/ergora-tools/forgekernel`. Installation pins its version without installing CUDA/PyTorch, logging into Claude or starting GPU work. Configure native tasks/local devices using the [official instructions](https://github.com/OpenBMB/ForgeKernel/tree/5030503d3ff71851aa34c14b9caf13ebfa9d9a78), then bind:

```json
{
  "tool": "forgekernel",
  "checkout": "/YOUR_HOME/.local/share/ergora-tools/forgekernel",
  "python": "/YOUR_HOME/.local/share/ergora-tools/forgekernel/.venv/bin/python",
  "task": "/YOUR_HOME/projects/my-project/kernel-task"
}
```

```bash
ergora project bind my-project kernel --binding kernel.json --revision CURRENT_REVISION
ergora kernel plan my-project
ergora kernel prepare my-project
ergora kernel list my-project
ergora kernel status my-project CAMPAIGN_ID
ergora kernel run my-project CAMPAIGN_ID --timeout 3600
```

The same operations appear in “Workflow design → Training optimization experiments → Native kernel candidates”. `plan` checks/displays the native plan; `prepare` only creates/freezes a native campaign. `run` invokes models/GPU and explicitly continues that same campaign; `status` checks native state. The Ergora-ID/native-directory mapping is persistent. Changing current project bindings does not alter existing campaigns.

The pinned version supports only Claude backend; Codex login cannot substitute for it. This adapter version supports local delivery only and explicitly refuses SSH delivery. Timeout/interruption may leave native child jobs; record `outcome_unknown` without claiming remote/GPU cancellation. Check native directories and stopped old jobs first. To continue, supply `--reconcile-reason '实际核对依据'`, also available in the page. With uncertain creation, first use status to reconcile that ID's native directory rather than creating a replacement campaign.

Pinned-source checks cover both `src/forgekernel` and actually used `scripts`. Modified, deleted or untracked files relative to Git HEAD make doctor report `version=unsupported` and refuse operations before starting the native driver. Put custom wrappers outside the checkout. Pinned-source checks do not guarantee external Python dependencies, CLI binaries, environment or OS isolation.

In addition to native task snapshots, campaigns freeze SHAs for models.toml, loop.toml and backends.toml. Later configuration drift explicitly refuses execution; restore matching configuration. Do not edit shared defaults during a run. Backups/machine moves must retain tool source, these configurations and campaigns together. Reports and actual best/kernel.py or best/kernel.cu identities are saved. `native_finished` describes generator completion only; `native_failed` retains upstream failure. After selecting a candidate commit, continue with training-template manifests, trusted runners, correctness/quality and paired performance evidence, then manual release bound to evidence SHA. ForgeKernel's internal judge, target_met or report prose is not perfctl PASS. GPU/model quality requires independent workload acceptance.

Backend extensions use the shared `AgentBackend` contract and local mapping in `agent_backends.py`. Each implementation owns its commands, result extraction, specialized configuration and diagnostics. Public configuration schemas/capabilities remain declared only in `components.json`. `agents`, formal stages and doctor reuse those implementations; `processes` owns process monitoring/cancellation. See [current architecture](architecture/current.md#agent后端接入) for integration/call paths. New specialist definitions, template members and nested resource inheritance follow the [workflow guide](WORKFLOW_DEFINITIONS.md#完整继承与冲突).

<a id="维护内置组件描述"></a>
## Maintain built-in component descriptions

`src/ergora/data/components.json` supplies built-in roles/tool descriptions at catalog `schema_version: 1`. Roles save capability requirements, display information and recommended bindings for new projects. Components save implemented driver names, capabilities, operations, platforms, probe methods, configuration fields and installation sources. `ergora tools list` and Web bootstrap return these descriptions; binding forms are generated from their fields. ForgeKernel/mini installers also read pinned sources/commits from this file.

To reuse the existing `command` driver, add a packaged component with `implementation: "command"`, matching `tool.const` and existing configuration fields. Templates/pages need no vendor-specific branch. Rebuild/install to apply the change. The same implementation still checks ordinary commands, `stage-json-v1`, role capabilities and trusted acceptance. Actual drivers, cleanup and new operation semantics require code adaptation/contract acceptance; adding a description does not support a new SDK automatically.

Forms currently support string, number, integer, array and enum. `x-ergora-*` fields supply only form enum labels, platform defaults, project task-queue defaults and input steps. Descriptions are not injected into saved bindings/run snapshots and do not change Agent runtime defaults. Core structural validation uses the same configuration JSON Schema; business owners retain role, path, URL and trusted-gate checks. See [contracts and identities](architecture/contracts-and-identities.md) for types, error paths and compatibility. The catalog loads no user Python plugins or key values.

See [fixed attachment reads through task MCP](WORKFLOW_DEFINITIONS.md#通过任务-mcp-读取固定附件) for independent composition leaves' default text-only and optional task-mcp modes. The latter reads only selected leaf/ancestor fixed resources, without ambient tools. Native tool lists, Claude bare-authentication differences and Linux support follow that mode's contract. Ordinary agent run/formal stages do not adopt it automatically.

Before independent composition calls, use `composition check-input` to inspect [capabilities and permission chains](WORKFLOW_DEFINITIONS.md#调用前查看能力与权限). The report combines current backend contracts with original admission. It probes no authentication and starts no services. An actual call repeats admission and saves a policy with the same structure. A new restricted backend must implement composition_policy rather than merely declare a mode name.

<a id="专长工作实例的可写调用"></a>
## Writable calls for specialist work instances

Formal `work-units-v1` maps each original unit to a frozen implementer instance; see [specialist executors and original work units](WORKFLOW_DEFINITIONS.md#专长执行者与原工作单元) for configuration/support. workspace-task-mcp reuses the same backend Interface, fixed resource service, native process supervision and call records. Codex explicitly enables workspace shell/file tools while disabling ambient rules, Skills, plugins, hooks, web and implicit sub-Agents. Reasoning configuration still consumes only whitelisted fields. Policy separately records native tool configuration and the absence of OS/network isolation; permission instructions are not enforced isolation.

Invocation evidence includes original formal-call, complete input snapshot/prompt, actual argv/cwd/stdin SHA, native MCP receipts, structured result and final original work receipt. The trusted Executor owns commits/deterministic checks. This workspace mode currently supports only explicitly selected current-container Codex/Linux/WSL2. Claude retains supported read-only review modes; unverified new writable compositions are refused. Changing mode on an old independent read-only entry cannot grant write authority.
