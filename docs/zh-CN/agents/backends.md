# 模板角色与可替换 Agent

简体中文 · [English](../../agents/backends.md) · [文档目录](../../README.zh-CN.md)

可分享的专家配方见[专长Agent定义库](../../definitions/agents.md)，完整祖先材料的受限单叶调用见[工作流调用手册](../../definitions/workflows/leaf-calls.md#call-a-prepared-leaf)。项目角色绑定和正式六阶段继续使用本手册的入口。

模板保存目标、角色、能力、产物和验收；项目保存具体工具。`ergora templates copy` 会在原文件之外附带 `agent-contract.json`，不改变冻结参考合同。查看角色：

```bash
ergora templates agents repository-governance
ergora templates agents large-change
ergora templates agents training-optimization
```

治理和大型开发提供 inspector / planner / implementer / reviewer。integrate、verify 和 work 的可信 test-results 仍由执行器负责。训练提供 experiment-planner / performance-analyst / kernel-tuner，分别输出提案、分析及候选说明；原生 kernel 生成工具在独立的 `kernel` 层选择。

Codex / Claude Code 的首次安装、认证和官方入口见 [安装手册](../../agents/configuration.md#install-and-authenticate-agent-clis)。以下步骤假定所选命令已在启动 Ergora 的 shell PATH 中可用。

绑定后可运行 `ergora tools doctor PROJECT`；主动版本/凭据/TCP 检查使用 `--probe --timeout 5`。分项含义、预算和修复入口见[诊断说明](../../operations/services.md#diagnose-and-repair)。Codex 凭据存在与真实模型任务通过分别记录，不据此宣称 Agent 已验收。

Linux 统一注册项目可通过[显式服务入口](../../operations/services.md#manage-services-explicitly)启动所选 `temporal/worker/executor/a2a`。服务只在明确选择后启动；停止需确认且等待真实状态，原运行栈不会自动接管。托管 executor 使用此控制目录中的冻结角色快照。 已有正式开发任务可以通过 `ergora task list PROJECT` / `task show PROJECT TASK_ID` [读取冻结合同](../../development/tasks.md#read-formal-task-contracts)；此查询不推断Temporal实时状态，主入口也支持[预览、创建和恢复](../../development/tasks.md#preview-and-create-formal-tasks)，在创建时冻结角色配置；`task status`提供[原生运行状态查询](../../development/run-and-recover.md#query-formal-task-run-status)，提交使用[统一提交与恢复入口](../../development/run-and-recover.md#submit-formal-tasks-and-recover-unknown-results)，批准使用[精确计划批准入口](../../development/design-and-approval.md#approve-an-exact-plan-and-recover-delivery)，取消使用[原运行取消入口](../../development/run-and-recover.md#request-cancellation-and-recover-unknown-delivery)，导出使用[精确候选出口](../../development/evidence-and-export.md#export-an-exact-candidate-and-recover-its-receipt)；旧入口创建的任务继续使用本手册的参考命令。

`control`、`development`、`research`是控制面SDK的[安装组合](../../install/linux.md#choose-an-installation-profile)，不安装或选择某个Agent。通过 [Agent 配置](configuration.md)配置 Codex/Claude；[mini-swe-agent](#mini-swe-agent) 和 [ForgeKernel](forgekernel.md) 需要各自固定源码的环境。更换组合不修改已有项目绑定。

Windows 原生的安装与认证见 [Windows 手册](../../install/windows.md#install-and-authenticate-agents)。原生角色调用支持 Codex、Claude Code 及明确的程序 / 解释器 `.exe`；`.cmd` / `.bat` launcher 显式拒绝。mini 的 Bash 驱动、ForgeKernel 及正式六阶段桥接要求 WSL2/Linux，正式参考执行器另需可信 Linux 容器。Windows 保持 Codex 原生 sandbox，不能使用 Linux 的 `current-container` 选择。

## 项目选择与独立调用

通过控制台“工具绑定”选择每个角色，也可以使用 JSON：

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

`--template` 要求该角色的真实结构化产物；不指定时保持普通文本调用。两者都不等于正式验收。Codex 默认使用角色对应的 CLI sandbox。若系统不支持该 sandbox，可在已经明确接受当前容器/用户边界后，显式设置 `"sandbox":"current-container"`；不会自动降级。Claude Code 使用自己的认证，其审查/提案角色限制到 Read/Grep/Glob，关闭会话持久化与额外 MCP 配置。默认审查仍为 Codex。

### 为每个 Agent 设置思考强度

Codex 的 binding 可增加 `reasoning_effort`，Claude Code 可增加 `effort`，例如：

```json
{"tool":"codex","model":"YOUR_MODEL_ID","reasoning_effort":"high"}
```

```json
{"tool":"claude-code","model":"YOUR_MODEL_ID","effort":"medium"}
```

项目角色在“工具绑定”表单或 `project bind` 中设置；专长实例在自己的 `agent.json.backend` 或正式任务的 `composition.backend_overrides[实例路径].binding` 中设置。正式任务会冻结这份完整配置；修改项目绑定或发布新的 Agent 版本不会改写已有任务。并行审查分支可分别选择后端、模型和强度，沿原 DAG 与祖先并发配额调度。

Codex 的可选值为 `low/medium/high/xhigh/max/ultra`，显式 binding 覆盖 `--codex-config` 文件中的 `model_reasoning_effort`。Claude 的可选值为 `low/medium/high/xhigh/max/ultracode`，投影为原生 `--effort`。省略字段时保留各 CLI 的原有设置；其他后端没有这两个字段。等级是否可用取决于所选模型、CLI、账户和服务；Ergora 保存明确请求，不估算或承诺各后端使用相同计算量。Claude 的组织策略可能限制实际等级，JSON 模式的相关警告可能只进入原生 debug log，不能仅凭请求值认定实际强度。

参数说明见 [Codex 官方配置](https://developers.openai.com/codex/config-reference/)、[Claude CLI](https://code.claude.com/docs/en/cli-reference#cli-flags) 和 [Claude 模型配置](https://code.claude.com/docs/en/model-config)。不支持的字段在绑定校验时拒绝；已接受字段在模型端能否运行，仍须真实调用验证。

### 当前配置证据与待交付能力

区分三项事实：binding／冻结配置中的请求等级，向原生CLI投影的参数／配置，以及实际观察到的native／模型行为。Codex把 `reasoning_effort` 投影为 `-c model_reasoning_effort=...`，Claude把 `effort` 投影为 `--effort`；参数只证明向CLI提出请求，不证明模型实际采用等级或provider线上请求已核。没有native证据时，实际强度保持未知，不能从进程成功、结构输出或binding被接受推断生效。

目前只实现显式binding值与原默认设置；统一fixed／preset／planner／automatic选择及配置冻结合同仍是后继工作。现有工作流preset和native CLI profile不实现调参preset或自动选择。换模型／强度回退与扩大预算需要各自明确策略，不得暗中执行。Claude text-only加入 `--safe-mode`，文档说明的原生行为会关闭workflows，因此请求 `ultracode` 不能证明启用了ultracode workflow；native优先级／上限及实际采用分别核对，见[后端指南](../../agents/backends.md#set-reasoning-effort-for-each-agent)。

DeepSeek当前的 `context_window`／`max_tokens` 写入SDK模型注册的容量描述，不是已验证的单请求token硬上限；仍按原每次wall-time、报告成本和续接合同处理，不把不同原生控制当作统一预算保证。

选择后端不会开放新设计关卡或训练效果。当前schema2设计policy登记仍[仅存储且拒执行](../../projects/registration.md#current-limits-of-design-policy-registration)；只读[source-journal记录](../../development/design-and-approval.md#store-complete-design-sources-and-reported-answers)不提供可信owner批准；有限训练控制器按其[明确授权合同](../../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization)执行。原schema1任务合同保持原范围。

### 用 Ergora 审查自己的仓库

可以为本仓库或其他代码库登记一个审查项目，并给 reviewer 选择与实际作者不同的可用后端。例如把 `reviewer.json` 写为 `{"tool":"claude-code"}`，然后运行：

```bash
ergora project add self-review --repo /PATH/TO/REPOSITORY
ergora project show self-review
ergora project bind self-review reviewer --binding reviewer.json --revision CURRENT_REVISION
ergora agent run self-review reviewer --prompt review-request.md --template repository-governance --timeout 900
ergora agent runs self-review
ergora agent output self-review RUN_ID
```

`review-request.md`写明原始需求、精确候选SHA；未提交内容另列完整差异、新文件及摘要。提供真实验证命令、结果和未验范围，并指定只读检查范围。需要专长提示时，可从[定义库](../../definitions/agents.md)的`show --material`取得正文，显式加入请求；当前不会自动装载定义或继承资源。后端继续使用自己的登录与环境变量，不在请求中放密钥。

只读范围应允许该后端实际具备的读取方式：Codex通常通过只读shell命令检查源码，Claude可用Read/Grep/Glob。不要同时禁止所有命令又只列出另一后端的专有工具；也可随请求附入新文件全文，并核对输入摘要。切换后端后重新确认材料确实可读，不能把“无法完成检查”的request-changes当成已确认的源码缺陷。

此模板要求`review-report`、`handoff`和明确的`approve/request-changes`。查看运行记录中的原始结构化result及摘要，逐项处理finding；进程成功、结构合格和审查通过分别核对。失败/超时不视为通过，同后端回退保留原因；单次独立调用不产生正式workflow批准或可信验收。

### 自定义命令

普通 `{"tool":"command","argv":["/path/to/program"]}` 继续接收 stdin 文本。正式阶段或 `--template` 调用要求：

```json
{
  "tool": "command",
  "argv": ["/path/to/agent-wrapper"],
  "protocol": "stage-json-v1",
  "capabilities": ["repository-read", "plan-write"]
}
```

stdin 为 `{schema_version, role, prompt, result_schema}`；stdout 必须仅含一个符合 result_schema 的 JSON 对象，诊断写 stderr。schema 要求 summary、所需 artifacts；审查还要求明确的 approve / request-changes。能力列表须覆盖角色要求；它是兼容性声明，不是工具质量或隔离的证明。命令按 argv 执行，模板中不嵌入命令。

### mini-swe-agent

```bash
bash scripts/install-agent.sh mini-swe-agent
```

固定源码和独立 venv 默认保存在 `~/.local/share/ergora-tools/mini-swe-agent/`。将其 Python 绝对路径填入实现角色：

```json
{
  "tool": "mini-swe-agent",
  "python": "/YOUR_HOME/.local/share/ergora-tools/mini-swe-agent/.venv/bin/python",
  "model": "YOUR_PROVIDER/YOUR_MODEL",
  "step_limit": 30,
  "cost_limit": 3.0
}
```

认证由相应 provider 的环境变量提供。mini 支持实现角色，不承担只读独立审查。驱动使用原生 LiteLLM tool-call 模型与一致的 bash 工具提示，保存 trajectory；完成时将最终文本写到运行归档中的提交文件，再用提示中给出的命令提交正文，交给同一结构验证。空 submission 判为失败。shell action 保留在外层监控的进程组，使用整体任务时限；一个 action 可消耗剩余时限。成本沿用上游报告值，单次 API 请求可能超过剩余预算，不是预付费金额上限。安装和 CPU SDK 检查不代表模型效果验收。

### Antigravity CLI 与 DeepSeek CLI

在 Linux/WSL2 上按官方指南安装并配置 [Antigravity CLI](https://antigravity.google/docs/cli/headless) 或 [DeepSeek Harness CLI](https://github.com/deepseek-ai/deepseek-harness/tree/master/apps/cli)。实现角色可绑定 `{"tool":"antigravity-cli"}` 或 `{"tool":"deepseek-cli"}`。服务的 PATH 找不到 `agy` 或 `dsh` 时，通过 `executable` 指定绝对路径。

```bash
ergora project bind PROJECT implementer --binding implementer.json --revision CURRENT_REVISION
ergora tools doctor PROJECT --probe --timeout 5
ergora agent run PROJECT implementer --prompt task.md --timeout 300
```

Antigravity 使用自身登录，可在绑定中选择 `model` 和 `effort`。Ergora 通过 `--sandbox` 请求原生终端沙箱，实际效果取决于 Linux namespace 支持和原生权限。无头模式可以拒绝需要审批的工具操作，随后仍返回成功答复。以实际 Git diff 和测试结果确认实现是否完成。[Antigravity 无头模式权限](https://antigravity.google/docs/cli/headless) · [沙箱要求](https://antigravity.google/docs/sandbox/)

DeepSeek 使用原生配置的默认模型，通过 `headless` profile 和原生 `workspace-write` 权限运行。Ergora 从 stdin 提供任务，并用 CLI 最后加载的配置补丁选择新会话和 JSON 输出。DeepSeek Harness CLI 0.2.2-rc.2 随附的无头配置按启动环境变量、工作目录的 `.env`、`DSH_HOME/.env` 的顺序读取 API key。使用 GUI 管理的密钥或登录状态需要在原生配置中显式启用相应组件。[DeepSeek 无头凭据](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.2/packages/bundle/headless/README.md#credentials)

两者在受信任的工作区执行单次原生实现请求。并行实现时使用独立 worktree。Ergora 核对工作目录、原生标识和成功终态，有阶段 schema 时再验证结构化结果。运行记录保留原生 stdout 和 stderr。`ergora tools doctor PROJECT --probe` 可检查可执行文件版本，认证状态为 `not_checked`。受限只读叶子可继续用 [DeepSeek Harness SDK](deepseek-harness.md)。

## 维护内置组件描述

源码中的 `src/ergora/data/components.json` 是内置角色与工具目录的来源，目录版本为 `schema_version: 1`。角色保存能力要求、显示信息和新项目默认绑定；组件保存已实现的驱动名称、能力、操作、平台、探测方式、配置字段及安装来源。`ergora tools list` 和 Web bootstrap 返回这些描述，绑定表单按字段生成。ForgeKernel 与 mini 的安装器也从此文件读取固定源码和提交。

复用已有 `command` 驱动时，可在随包目录增加一个组件，使用 `implementation: "command"`、对应的 `tool.const` 和既有配置字段；模板及页面不需要增加厂商分支。重新构建并安装软件后生效。普通命令、`stage-json-v1`、角色能力及可信验收规则仍由相同实现检查。实际驱动、资源清理和新的操作语义需要代码适配与合同验收；增加描述不会自动支持新的 SDK。

当前表单支持 string、number、integer、array 和 enum。`x-ergora-*` 字段仅提供表单的枚举标签、平台默认值、项目 task queue 默认值及输入步长。配置描述不注入已保存绑定或运行快照，也不改变 Agent 的运行默认值。核心使用同一配置的 JSON Schema 做结构校验，既有角色、路径、URL 和可信门禁继续由业务所有者负责；具体类型、错误路径及兼容规则见 [合同与身份](../../architecture/contracts/formats.md)。目录不加载用户提供的 Python 插件，配置中也不保存密钥值。

独立组合叶子的默认text-only及可选task-mcp模式见[工作流手册](../../definitions/workflows/leaf-calls.md#read-fixed-attachments-through-task-mcp)。后者只读选中叶子/祖先固定资源，不继承ambient工具；原生工具表、Claude bare认证差异和Linux支持范围均按该模式处理。普通agent run及正式stage不自动采用此模式。

独立组合调用前可用`composition check-input`查看[能力及权限链](../../definitions/workflows/leaf-calls.md#inspect-capabilities-and-permissions-before-invocation)。报告由当前后端合同与原准入共同生成；它不探测认证或启动服务，实际调用会重新准入并保存相同结构的policy。新增受限后端需实现自己的composition_policy，不能只声明模式名称。

## 专长工作实例的可写调用

正式`work-units-v1`将每个原unit映射到冻结的implementer实例，配置和支持范围见[工作流手册](../../definitions/workflows/contracts.md#specialist-writers-and-original-work-units)。workspace-task-mcp使用同一backend Interface、固定资源服务、原生进程监督与调用记录；Codex显式开启workspace shell/file工具，关闭ambient规则、Skill、插件、hook、web和隐式子Agent。推理配置继续仅消费白名单字段。原生工具配置与无OS/网络隔离分别写入policy，不把权限提示词当强制隔离。

调用证据包含原formal-call、完整输入快照与prompt、实际argv/cwd/stdin SHA、MCP原生回执、结构结果与最终原work receipt。提交和确定性检查由可信Executor完成。新workspace模式目前仅支持显式current-container的Codex/Linux/WSL2；Claude仍可使用已支持的只读审查模式，未验证的新可写组合会拒绝。旧独立read-only入口不能通过修改mode取得写权限。
