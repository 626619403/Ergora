# 模板角色与可替换 Agent

可分享的专家配方见[专长Agent定义库](AGENT_DEFINITIONS.md)，完整祖先材料的受限单叶调用见[工作流调用手册](WORKFLOW_DEFINITIONS.md#调用一个准备好的叶子)。项目角色绑定和正式六阶段继续使用本手册的入口。

模板保存目标、角色、能力、产物和验收；项目保存具体工具。`ergora templates copy` 会在原文件之外附带 `agent-contract.json`，不改变冻结参考合同。查看角色：

```bash
ergora templates agents repository-governance
ergora templates agents large-change
ergora templates agents training-optimization
```

治理和大型开发提供 inspector / planner / implementer / reviewer。integrate、verify 和 work 的可信 test-results 仍由执行器负责。训练提供 experiment-planner / performance-analyst / kernel-tuner，分别输出提案、分析及候选说明；原生 kernel 生成工具在独立的 `kernel` 层选择。

Codex / Claude Code 的首次安装、认证和官方入口见 [安装手册](USAGE.md#安装与认证-agent-cli)。以下步骤假定所选命令已在启动 Ergora 的 shell PATH 中可用。

绑定后可运行 `ergora tools doctor PROJECT`；主动版本/凭据/TCP 检查使用 `--probe --timeout 5`。分项含义、预算和修复入口见[诊断说明](USAGE.md#诊断与修复)。Codex 凭据存在与真实模型任务通过分别记录，不据此宣称 Agent 已验收。

Linux 统一注册项目可通过[显式服务入口](USAGE.md#显式服务管理)启动所选 `temporal/worker/executor/a2a`。服务只在明确选择后启动；停止需确认且等待真实状态，原运行栈不会自动接管。托管 executor 使用此控制目录中的冻结角色快照。 已有正式开发任务可以通过 `ergora task list PROJECT` / `task show PROJECT TASK_ID` [读取冻结合同](USAGE.md#读取正式任务合同)；此查询不推断Temporal实时状态，主入口也支持[预览、创建和恢复](USAGE.md#预览与创建正式任务)，在创建时冻结角色配置；`task status`提供[原生运行状态查询](USAGE.md#查询正式任务运行状态)，提交使用[统一提交与恢复入口](USAGE.md#提交正式任务与恢复未知结果)，批准使用[精确计划批准入口](USAGE.md#批准精确计划与恢复投递)，取消使用[原运行取消入口](USAGE.md#请求取消与恢复未知投递)，导出使用[精确候选出口](USAGE.md#导出精确候选与恢复回执)；旧入口创建的任务继续使用本手册的参考命令。

`control`、`development`、`research`是控制面SDK的[安装组合](USAGE.md#选择安装组合)，不安装或选择某个Agent。Codex/Claude仍按本手册配置；mini-swe-agent和ForgeKernel继续用下文固定源码安装器。更换组合不修改已有项目绑定。

Windows 原生的安装与认证见 [Windows 手册](WINDOWS.md#agent-安装与认证)。原生角色调用支持 Codex、Claude Code 及明确的程序 / 解释器 `.exe`；`.cmd` / `.bat` launcher 显式拒绝。mini 的 Bash 驱动、ForgeKernel 及正式六阶段桥接要求 WSL2/Linux，正式参考执行器另需可信 Linux 容器。Windows 保持 Codex 原生 sandbox，不能使用 Linux 的 `current-container` 选择。

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

`review-request.md`写明原始需求、精确候选SHA；未提交内容另列完整差异、新文件及摘要。提供真实验证命令、结果和未验范围，并指定只读检查范围。需要专长提示时，可从[定义库](AGENT_DEFINITIONS.md)的`show --material`取得正文，显式加入请求；当前不会自动装载定义或继承资源。后端继续使用自己的登录与环境变量，不在请求中放密钥。

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

### DeepSeek Harness 只读叶后端

可选适配固定为 SDK／runtime-bin `0.2.2rc2`，使用独立环境；基础 Ergora 不依赖它。目前只支持 Linux/WSL2 的 `composition check-input/run-input`，模式为 `text-only` 或 `task-mcp`，角色为 reviewer、experiment-planner、performance-analyst、kernel-tuner。后两类产物仍是文本提案，不是实际测量或 kernel 执行。`agent run` 的原生调用、workspace 写入、交互会话和恢复尚不支持；OpenHands SDK 暂未注册。

安装器已提供 uv 后，可在持久目录单独安装：

```bash
ERGORA_DSH_ENV="$HOME/.local/share/ergora-tools/deepseek-harness/0.2.2rc2/.venv"
uv venv --python 3.12 "$ERGORA_DSH_ENV"
uv pip install --python "$ERGORA_DSH_ENV/bin/python" \
  'deepseek-harness-sdk==0.2.2rc2' 'deepseek-harness-runtime-bin==0.2.2rc2'
```

在所选[Agent定义的新版本](AGENT_DEFINITIONS.md#从固定原包派生新版本)中设置完整 `backend`；解释器替换为上一步实际绝对路径，模型与URL替换为自己服务的值：

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

`api` 显式选择 `openai-responses` 或 `openai-completions`；省略时保持 Chat Completions。选择服务实际提供的入口，平台不会因失败自动切换协议；task-MCP 还须兼容所选协议的工具调用及 SSE。环境变量由启动 Ergora 的 shell 提供，不把密钥填入JSON。`context_window`和`max_tokens`按实际模型配置，默认值不证明服务支持相同容量。包版本诊断不调用模型，也不证明认证、网关或模型质量通过。

发布新的 Agent 版本并沿父引用准备新输入，保留完整祖先资料及权限上限，然后调用：

```bash
ergora composition check-input my-project ./prepared-review --mode task-mcp
ergora composition run-input my-project ./prepared-review --mode task-mcp --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

这里采用叶定义的完整后端配置。单独 `--backend deepseek-harness` 不会填充必需的解释器、服务和认证变量名。只含内联资料时可显式选择text-only；有Skill附件时用task-mcp，按[全文读取说明](WORKFLOW_DEFINITIONS.md#核验完整附件读取)检查原回执。

每次调用使用新原生home／session、固定最小profile与生成的patch；无原生shell、文件、工作目录及额外MCP工具。task-mcp只提供原scope的list/read。适配保存原生身份、完整prompt、事件和终值到本次`.protocol`目录，整体时限／停止仍由原进程owner负责。这不提供OS隔离。

必须同时核对完成状态、严格JSON／原结果schema和原MCP连接回执；任一原生工具错误使本次调用失败，不隐式重试或续接会话。上游可能在插件失败或断连后仍返回completed，因此最终文本本身不能代表成功。失败或结果不明先按原run ID查看证据，不创建另一次调用冒充恢复。固定发行包与loopback／停止探针见[H1交付](delivery/2026-11-12-harness-probes.md)；显式Responses的真实禁工具调用及同模板专家叶task-MCP全文验收见[H2交付](delivery/2026-11-14-harness-real-model.md)。这两次只读成功不证明正式六阶段、持久会话或其他平台已经准入。

## 可选的正式六阶段执行桥接

默认`agentflow`执行器保持v2.2行为。要使项目的角色选择作用于正式任务，先按参考手册安装、配置模型和可信执行边界，再用[统一项目注册](PROJECTS.md)一次登记Git根、角色、模板与可信检查，并运行`ergora reference executor --project PROJECT_ID`。旧的两次注册方式继续兼容，两个同名项目必须指向相同Git根。只对新任务启用；不要中途切换已开始的参考任务。

已有reference项目可用`ergora project import-reference import.json --revision N`预览，审阅差异和文件身份后加`--apply --preview-sha256 SHA`显式采用。它保持兼容旧文件原字节，保存前后项目与来源记录；不搬迁在途任务或导入模型密钥。详细spec和恢复命令见[项目定义手册](PROJECTS.md#显式导入旧注册)。

先停止原 executor，保留 Temporal、worker 等服务：

```bash
"$HOME/multi-agent-platform/.venv/bin/supervisorctl" \
  -c "$HOME/.config/multi-agent-platform/supervisord.ini" stop executor
ergora reference executor --installation "$HOME/multi-agent-platform"
```

该命令在前台监听原 FileAdapter 队列，使用同一 executor 锁，保留原任务创建、审批、取消、恢复和导出命令。也可加 `--request /ABSOLUTE/PATH/envelope.json` 精确处理一个已发布信封。执行器校验参考 Python 源码身份，拒绝未经适配的版本。

新任务首次处理时将角色工具与项目修订写入原任务持久目录的 `agent-bindings.json`；恢复继续用这份选择。实现者和审查者使用不同角色身份、新会话、精确候选提交及原有工作区变化检测。正式阶段结束前清理并回收其派生进程，再执行原监控的只读变化检查；精确使用参考配置的 Codex 可执行路径。未知外部进程结果继续由参考监控对账；缺少能力、结果结构错误、命令失败或只读阶段改动都不能通过。Agent 的 `model-log` 和 `agent-selection` 附在原回执证据中。

桥接的模型阶段会核验本任务保存的 `compiled.json` 与stage合同，从该快照加载完整模板说明，并将说明摘要记入 `agent-selection`。快照缺失、被改或属于另一任务时明确失败；不会改用活动包。已有任务不因源包删除而换说明，安装profile本身漂移仍按原规则拒绝。此行为属于Ergora桥接；直接 `agentflow` 入口保留原v2.2行为。

统一入口的[外部证据查询](USAGE.md#核对闭合运行的外部作业证据)将原run完整历史中的dev_submit与可信FileAdapter请求/回执逐项对应。每个已知job即使请求丢失仍保留为未决；没有正确fence、存在额外请求/孤立回执、无效回执或产物摘要错误时不会报告外部已确认。只读查询不修改原outcome、不发布fence、不释放租约，外部终止证据和六阶段质量结果分别保留。 正常REVIEW_READY也不会因workflow闭合自动释放租约：导出沿原规则处理，暂不导出时使用[正常任务关闭流程](USAGE.md#正常任务完成后的关闭)。需要写入fence和释放精确原claim时，显式使用[reconcile/reconciliation/resume-reconcile](USAGE.md#显式终态对账与工单租约释放)；它保存原outcome与独立清理evidence，原CANCEL_UNCONFIRMED保持，缺证据不释放。

原v7来源任务导出精确候选后，可按[候选评论说明](USAGE.md#为已导出的候选发布工单评论)准备并确认GitHub／GitLab中性评论；该操作单独保存意图及原生收据，复用原任务身份，不改变Agent后端、批准或导出结果。GitHub的[原生ID标签追加](USAGE.md#为已导出的候选追加-github-标签)复用同一回写生命周期；GitLab标签动作明确unsupported，选择tracker不会隐式改变Agent授权。

新记录还保存`configuration`有效绑定视图，含每层来源、校验结果、项目修订和内容摘要；`ergora project config PROJECT_ID`可查看当前值。旧任务没有此附加字段时仍使用原绑定快照，不重建历史配置。视图范围与独立调用的上下文区别见[有效绑定与运行快照](USAGE.md#有效绑定与运行快照)。

统一注册项目需要长期运行时，优先用`ergora services start PROJECT temporal worker executor a2a --revision N`管理所选栈，不必手改ini。以下仅适用于保留原Supervisor的旧部署：在 `~/.config/multi-agent-platform/supervisor.d/executor.ini` 中把该 program 的 `command` 改为 Ergora 可执行文件绝对路径、`reference executor --installation ...`，保留 stopasgroup/killasgroup。再用 supervisorctl `reread` / `update`。初始化参考发行可能重新生成该文件，升级后应核对。不要同时运行新旧两个 executor。

桥接沿用参考配置中的 Codex TOML 和 API 变量。参考监控的凭据白名单不会传递任意 shell 变量；其他 provider 可使用工具自己的持久登录，或参考 `credentials.json` 的 0600 凭据映射。模板、项目绑定与仓库中只保存凭据变量名/元数据。独立调用的活动 Skill/记忆选项不会自动改写正式任务的上下文。

## ForgeKernel 原生候选

```bash
bash scripts/install-agent.sh forgekernel
```

默认源码为 `~/.local/share/ergora-tools/forgekernel`，安装固定版本，不安装 CUDA/PyTorch、不登录 Claude、不启动 GPU。依据 [官方说明](https://github.com/OpenBMB/ForgeKernel/tree/5030503d3ff71851aa34c14b9caf13ebfa9d9a78) 填写原生任务和本地设备配置后绑定：

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

同样操作位于“工作流设计 → 训练优化实验 → 原生 Kernel 候选”。`plan` 检查并展示原生计划；`prepare` 只创建并冻结原生 campaign；`run` 才执行模型/GPU，显式调用也用于继续同一个 campaign；`status` 核对原生状态。Ergora ID 与原生目录映射持久保存，改变当前项目绑定不会改变已有 campaign。

固定版本仅支持 Claude backend；Codex 登录不能替代它。首版适配仅支持 local delivery，SSH delivery 显式拒绝。超时/中断可能留下原生子作业，记录为 `outcome_unknown`，不声称远端或 GPU 已取消。先核对原生目录和旧作业是否停止；需要继续时，提供 `--reconcile-reason '实际核对依据'`，页面也有对应字段。创建结果不明时先 status 从该 ID 的原生目录对账，不能直接创建另一个 campaign 替代。

固定版本检查同时覆盖 `src/forgekernel` 和实际使用的 `scripts`：相对 Git HEAD 的修改、删除或未跟踪文件会使 doctor 显示 `version=unsupported`，并在启动 native driver 前拒绝操作。需要自定义包装脚本时放在 checkout 之外；固定源码检查不保证外部 Python 依赖、CLI 二进制、环境或 OS 隔离。

除原生任务快照，campaign 还固定 models.toml、loop.toml、backends.toml 的 SHA；后续配置漂移会明确拒绝，须恢复对应配置。运行中不要修改共享默认配置；备份与换机须同时保留工具源码、这些配置及 campaign。报告与实际 best/kernel.py 或 best/kernel.cu 的身份会保存；`native_finished` 只描述生成器的完成，`native_failed` 保留上游失败。选择候选提交后，继续用训练模板的 manifest、可信 runner、正确性/质量与配对性能证据，并按 evidence SHA 人工放行。ForgeKernel 的内部 judge、target_met 或报告文字不能直接成为 perfctl PASS。实际验证范围及未测的 GPU/模型效果见 [S8 记录](delivery/2026-10-31-s8-agents.md)。

完整选型与未接入工具见 [三模板调研](research/2026-10-31-template-agents.md)。

新增后端的代码入口是`agent_backends.py`的共有`AgentBackend`合同及本地映射；命令、结果提取、后端专用配置和诊断归各实现，公开配置schema与能力仍只在`components.json`声明。`agents`、正式阶段和doctor复用这些实现，进程监控与取消由`processes`管理。接入步骤和调用关系见[当前架构](architecture/current.md#agent后端接入)。新增专长定义、模板成员和嵌套资源继承仍按[AC计划](plans/2026-11-08-agent-composition.md)实施。

## 维护内置组件描述

源码中的 `src/ergora/data/components.json` 是内置角色与工具目录的来源，目录版本为 `schema_version: 1`。角色保存能力要求、显示信息和新项目默认绑定；组件保存已实现的驱动名称、能力、操作、平台、探测方式、配置字段及安装来源。`ergora tools list` 和 Web bootstrap 返回这些描述，绑定表单按字段生成。ForgeKernel 与 mini 的安装器也从此文件读取固定源码和提交。

复用已有 `command` 驱动时，可在随包目录增加一个组件，使用 `implementation: "command"`、对应的 `tool.const` 和既有配置字段；模板及页面不需要增加厂商分支。重新构建并安装软件后生效。普通命令、`stage-json-v1`、角色能力及可信验收规则仍由相同实现检查。实际驱动、资源清理和新的操作语义需要代码适配与合同验收；增加描述不会自动支持新的 SDK。

当前表单支持 string、number、integer、array 和 enum。`x-ergora-*` 字段仅提供表单的枚举标签、平台默认值、项目 task queue 默认值及输入步长。配置描述不注入已保存绑定或运行快照，也不改变 Agent 的运行默认值。核心使用同一配置的 JSON Schema 做结构校验，既有角色、路径、URL 和可信门禁继续由业务所有者负责；具体类型、错误路径及兼容规则见 [合同与身份](architecture/contracts-and-identities.md)。目录不加载用户提供的 Python 插件，配置中也不保存密钥值。

独立组合叶子的默认text-only及可选task-mcp模式见[工作流手册](WORKFLOW_DEFINITIONS.md#通过任务-mcp-读取固定附件)。后者只读选中叶子/祖先固定资源，不继承ambient工具；原生工具表、Claude bare认证差异和Linux支持范围均按该模式处理。普通agent run及正式stage不自动采用此模式。

独立组合调用前可用`composition check-input`查看[能力及权限链](WORKFLOW_DEFINITIONS.md#调用前查看能力与权限)。报告由当前后端合同与原准入共同生成；它不探测认证或启动服务，实际调用会重新准入并保存相同结构的policy。新增受限后端需实现自己的composition_policy，不能只声明模式名称。


## 专长工作实例的可写调用

正式`work-units-v1`将每个原unit映射到冻结的implementer实例，配置和支持范围见[工作流手册](WORKFLOW_DEFINITIONS.md#专长执行者与原工作单元)。workspace-task-mcp使用同一backend Interface、固定资源服务、原生进程监督与调用记录；Codex显式开启workspace shell/file工具，关闭ambient规则、Skill、插件、hook、web和隐式子Agent。推理配置继续仅消费白名单字段。原生工具配置与无OS/网络隔离分别写入policy，不把权限提示词当强制隔离。

调用证据包含原formal-call、完整输入快照与prompt、实际argv/cwd/stdin SHA、MCP原生回执、结构结果与最终原work receipt。提交和确定性检查由可信Executor完成。新workspace模式目前仅支持显式current-container的Codex/Linux/WSL2；Claude仍可使用已支持的只读审查模式，未验证的新可写组合会拒绝。旧独立read-only入口不能通过修改mode取得写权限。
