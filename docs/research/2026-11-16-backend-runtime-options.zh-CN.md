# 后端运行选项：原生控制与 Ergora 暴露范围

[English（默认）](2026-11-16-backend-runtime-options.md) · 简体中文

只读调研，2026-11-16。产品基线：`c540939d3b3f38f3851b0de965c9cd0f969eea77`；核对时文档 HEAD：`04af2344239306cb00458e89f81258093235f049`。本文提出配置工作的建议，不新增或认证产品功能。

## 结论

模型／思考强度之外，确有值得配置的选项。首批候选为 Codex 服务等级与回复详略、Claude 有限轮数／估算费用上限，以及 DeepSeek SDK 的明确思考强度／输出上限合同。上下文／压缩、provider 重试与会话变化影响保留材料、费用或恢复，需要分别处理。保留后端各自的语义，并核验实际所选模型／客户端。([C1]、[A1]、[D1]、[E1])

用户要求的四种选择模式为 **fixed / preset / planner / automatic**。Ergora 当前支持显式 binding 值与既有缺省值；可复用调参预设、planner 提议和自动按任务选择均属后续工作。仓库工作流 preset 与原生 CLI profile 不等于已经实现这几种模式，设计归属[思考强度／并行计划](../plans/2026-11-16-agent-reasoning-and-parallelism.md)。通过 Codex／provider 配置访问 ChatGPT 不构成另一个已注册的 `AgentBackend`。([E1]、[E2])

## 证据与术语

本机程序报告版本为 `codex-cli 0.167.1` 与 `Claude Code 2.1.312`，仅执行了 `--version`、`--help` 和 `codex exec --help`。官方页面在本次调研日获取；公开上游源码使用 Ergora 已声明的精确固定提交。文档、本地帮助、源码构造和真实模型调用分别证明不同范围。帮助中没有某参数不自动表示不支持：Claude 官方 CLI 手册明确说明帮助并未列出全部参数。本研究未调用模型、登录、安装，也未读取私人配置或凭据／环境快照。([A1]、[E2])

Ergora 的 `native` 模式仍启动**非交互子进程**：`codex exec` 或 `claude --print`，不是交互终端会话。`text-only` 与 `task-mcp` 是受限组合模式，后者只暴露固定授权资源。`workspace-task-mcp` 是明确授权的可信 Linux Codex 工作区模式。正式任务执行还有冻结输入、原 executor／Temporal 生命周期及绑定候选的检查；原生 CLI 的单项功能不能直接实现这份合同。([E1]、[E3]、[E4])

|后端|当前暴露的配置|准入入口与相关边界|
|---|---|---|
|Codex|`model`、`reasoning_effort`、`sandbox`|Native、受限文本／MCP，以及可信 workspace-MCP。内部／参考 `codex_config` 是另一条路径，组合调用对其严格过滤|
|Claude Code|`model`、`effort`|Native 与受限文本／MCP；受限轮数当前由 adapter 固定。没有 workspace-MCP 实现|
|DeepSeek Harness|`python`、`model`、`base_url`、`api_key_env`、`api`、`context_window`、`max_tokens`|固定 SDK／runtime `0.2.2rc2`；Linux 只读文本／MCP 叶。没有 native／workspace 模式；一次明确授权的 standalone MCP 续接另有冻结来源合同|
|mini-swe-agent|`python`、`model`、`step_limit`、`cost_limit`|固定版本的 Linux／native 实现角色驱动，没有受限组合模式|
|ForgeKernel|`checkout`、`python`、`task`|Kernel 支持层 campaign，不属于 AgentBackend。仅本地 delivery；原生任务／全局配置仍独立提供选项|
|结构化 `command`|`argv`、可选 `stage-json-v1` 和声明的 `capabilities`|Native 子进程；结构化正式阶段要求该协议及角色能力。任意 argv 不构成受限模式准入|

本表依据当前组件 schema、adapter 模式列表与实际驱动，不从上游宣传推断。这些 binding schema 拒绝未知属性。([E1]、[E2]、[E5]、[E6]、[E7]、[E8])

## Codex：候选选项与当前行为

Codex 官方支持 config override 与原生 profile。Ergora 参考路径可在内部传入 TOML 文件。受限模式下，`_options` 仅保留 `model`、`model_provider`、`model_reasoning_effort`、`service_tier` 和很小一组 provider 传输／凭据引用字段，再强制自己的工具／资源限制；这些模式拒绝额外 native argv。普通项目／定义 binding 没有任意 config 字典入口。([C1]、[C2]、[E1]、[E3])

|选项|原生语义|当前 Ergora 暴露范围与影响|
|---|---|---|
|模型与强度|`model`、`model_reasoning_effort`；强度名称取决于实际模型／客户端|已有显式 binding 字段。Binding 的强度覆盖传入参考 TOML 中的同名设置；省略时沿用既有缺省。Schema 接受不证明 provider 接受。([C1]、[E1])|
|服务等级|`service_tier`；`fast` 对应请求等级 `priority`，其他可声明等级依模型而定|受限调用已保留内部／参考配置中的该字段，但无 binding／UI 字段。适合作为明确可选字段。可用性、延迟及价格需 provider／账户证据，且与思考强度独立。([C1]、[E1])|
|回复详略|支持时 `model_verbosity` 使用 `low/medium/high`；配置参考将其描述为 Responses 模型的详略控制|无 binding 字段，受限 config 过滤会移除；native／参考配置可携带。它表达希望的回复详略，不是硬 token／费用上限。按模型准入，不套用到全部 provider。([C1]、[E1])|
|思考摘要|`model_reasoning_summary` 控制摘要展示|Binding 未暴露，受限 config 也不保留。它独立于思考深度，不是完整内部推理逐字稿。([C1]、[E1])|
|上下文与压缩|`model_context_window`、`model_auto_compact_token_limit` 及其 scope 控制容量描述／压缩时点|属于 native config，受限调用过滤移除。写入一个数字不会扩大 provider 的实际上下文；压缩会改变后续模型可见历史，若接入须保留原冻结材料并记录策略。([C1]、[E1])|
|工具输出界限|`tool_output_token_limit` 及逐 MCP 工具输出上限约束工具结果|不是最终回答 token 总上限。受限 MCP 仍有原固定传输／工具合同，不能将这些字段改称回复长度。([C1]、[E1])|
|Provider 重试／流空闲超时|逐 provider 的 `request_max_retries`、`stream_max_retries`、`stream_idle_timeout_ms`|受限 provider 白名单不保留。修改会影响延迟／尝试次数，总时长仍归原外层 wall budget；推理重试不授权重新发送 task／job start。([C1]、[E1]、[E3])|
|并行|原生 Agent thread 控制与工作流 DAG 并行度相互独立|受限调用关闭 native multi-agent，不可用 thread 设置绕过工作流并行／资源权限。([C1]、[E1])|
|Profile 与会话|原生 `--profile` 提供配置层，`resume/fork` 管理原生会话身份|Ergora 使用 `--ephemeral`，原生 session resume 不是正式任务恢复 API。CLI profile 可含远超调参范围的内容，不等于 Ergora 已冻结的调参 preset。([C2]、[C3]、[E1])|

所读 CLI／config 参考未建立通用 Codex CLI `temperature`、`top_p`、单次美元上限或一般最大 Agent 轮数参数。不能从名字相似的 Responses API 参数推断它们存在。当前 wall timeout 与正式预算属于既有 Ergora 控制，不是原生美元／轮数上限。([C1]、[C2]、[E3])

## Claude Code：候选选项与当前行为

Adapter 始终使用 `--print` 与 `--no-session-persistence`。text-only 另加 `--safe-mode`，关闭 workflows。([A1]、[E1])受限调用关闭 user／project／local setting sources，选择明确工具与严格 MCP 配置，并为 text-only 固定使用 `--max-turns 3`，task MCP 固定为 `24`。MCP 模式另使用 `--bare`，其认证／运行条件不同于普通交互登录。当前没有通用 Claude 参数／settings 透传入口。([A7]、[E1])

|选项|原生语义／版本证据|当前 Ergora 暴露范围与影响|
|---|---|---|
|模型与强度|`--model`、`--effort`；文档集合包括 `low/medium/high/xhigh/max/ultracode`，受模型／账户限制|已有显式 binding 字段。本机帮助列出普通等级，但未穷尽所有文档特殊值；仅凭帮助不能证明该值的真实可用性。([A1]、[A2]、[E1]、[E2])|
|有效强度与 cap|`CLAUDE_CODE_EFFORT_LEVEL` 高于 `--effort`，`maxEffortLevel` 再施加上限；逐模型 cap 需 v2.1.267+|请求的 binding 值可能不等于实际强度。JSON／stream-JSON 运行中，超 cap 警告进入 debug log，当前结构化结果自身不能证明实际强度。未读取本机环境值。([A2]、[A3]、[A6])|
|`ultracode`|此 flag 请求 `xhigh` 加 ultracode 行为；需 v2.1.203+ 及模型／账户资格|不能放进跨后端通用数值阶梯，也不能翻译成 Codex `ultra`。在当前 text-only 模式下，文档规定原生 `--effort ultracode` 的 ultracode 行为关闭，effort 至多为 `xhigh`，仍受原生优先级及 cap 约束；未验证真实应用值。应分别记录请求／解析／原生观察。([A1]、[A2]、[E1])|
|Fast mode|`fastMode`／`--settings` 和 `/fast` 为合资格模型／账户提供原生速度／费用行为；文档规定 print 支持自 v2.1.205 起|Adapter 未暴露。后续可考虑明确 typed fast-mode 选项；任意 settings 还会带入无关行为。它不等于换个名字的 Codex service-tier 字符串。([A4]、[E1])|
|最大轮数|`--max-turns` 限制 print 模式的 agentic turns，原生不指定时无上限；stream-JSON 排队输入可开始新一轮并重新计限|受限模式当前固定为 3／24，用户不可配；native 模式不加该参数。用户上限须保留模式／资源完整性和外层任务预算，触顶不能当成有效完成的审查。([A1]、[E1])|
|估算 API 费用|仅 print 的 `--max-budget-usd`；文档中的 subagent enforcement 需 v2.1.217+|未暴露。客户端估算可与账单不同，也可能超过 cap；恢复的旧 run 费用不计入新 invocation cap。可作为附加界限，不能充当跨恢复权威总预算。([A1]、[A5])|
|输出 token|`CLAUDE_CODE_MAX_OUTPUT_TOKENS` 限制多数请求；模型 cap 可能降低请求值，并影响上下文余量|没有显式 binding 字段；进程可能继承操作者环境，这不构成已核的逐调用冻结／观察。后续 adapter 字段需记录 requested／capped／unknown，同时不收集秘密环境快照。([A3]、[E3])|
|Thinking-token 预算|`MAX_THINKING_TOKENS` 对应较早的固定预算思考行为；adaptive 模型在文档条件下忽略正数预算|不是通用 effort 替代，也不是独立增加的推理额度。宜保留为逐模型高级选项，不做通用滑块。([A2]、[A3]、[A5])|
|压缩|`--autocompact`、`autoCompactWindow`、逐模型设置和 `CLAUDE_CODE_AUTO_COMPACT_WINDOW` 各有优先级；CLI flag 需 v2.1.221+|未暴露。须表示模型／上下文限制及环境优先级，压缩变化会影响历史与复现。([A1]、[A2]、[A3])|
|超时|`API_TIMEOUT_MS` 限制单次响应头／请求等待；Bash timeout 变量限制工具命令|不等于完整模型 invocation 的 wall budget，也不证明后代进程已停。保留原进程 owner 及正式取消／恢复。([A3]、[E3])|
|Fallback 模型|`--fallback-model` 可在过载／不可用时选择其他模型|Ergora 未添加该选项。它改变真实模型身份及可能的费用／质量，接入前需要明确冻结的 fallback policy 与回执语义。不能对未知强度／模型静默降档。([A1]、[A2]、[E1])|
|Output style、并行 Agent 与 resume|原生 settings／flags 可改变角色指令、subagent 行为、工具或会话身份|这些不是回复长度调参。当前 adapter 保留指定 schema／工具控制及禁用会话持久化，正式恢复归原任务 owner。([A1]、[A6]、[E1]、[E3])|

所读 Claude CLI 资料未建立通用 CLI `temperature`／`top_p` 调参能力。API／SDK 请求参数不会自动成为 `claude --print` 选项；操作者的 ambient 原生配置也不等于明确冻结的 Ergora 字段。([A1]、[A3]、[E1])

## 其他已接入工具

|工具|固定上游实际提供什么|当前集成与最小相关 owner|
|---|---|---|
|DeepSeek Harness|SDK 初始化除 provider／model 外，接受可选的路由自有 `reasoning_effort` 与逐请求 `max_tokens`；不支持的强度在 prompt 前拒绝，request timeout 不限制随后 activity|当前 binding 暴露 `context_window`／`max_tokens`，但 driver 将它们写成模型 registry 的 `contextWindow`／`maxTokens`，没有传 SDK 可选初始化控制。宣称硬逐请求 cap 前，先核清 registry 容量与请求 cap 语义。候选归 DeepSeek binding／driver 及原冻结 call／continuation 合同。([D1]、[D2]、[D3]、[E2]、[E5])|
|DeepSeek provider 路由|固定 pi-ai adapter 声明逐模型思考等级、兼容及重试行为；`off` 可能省略 wire 参数，仍沿用网关默认。SDK profile／home／patch 还会选择工具和持久化|Ergora 固定 `sdk-minimal`，移除原生 shell／file 工具，在所选路由禁用重试／reconnect，需要时只允许固定 task MCP。不要开放任意 profile／patch，或将 headless／完整 SDK 功能当成当前 adapter 已支持。服务优先级／采样兼容需精确路由证据。([D1]、[D2]、[D4]、[E5])|
|mini-swe-agent|固定 `AgentConfig` 有 step／cost／wall-time 上限；LiteLLM model 有逐 provider 的 `model_kwargs`、cost tracking 和重试|Ergora 已暴露步数（默认 30）与报告 USD 费用（默认 3）；下次模型查询前才核 cost，单次查询可超出余额。Driver 传外层 timeout 作为 wall time，`model_kwargs` 固定为 `drop_params=True`。没有用户采样／effort 透传。后续 typed provider 控制归该 driver／schema；静默丢弃不支持参数会使“实际应用”主张失效。([M1]、[M2]、[E2]、[E6])|
|ForgeKernel|固定提交的原生 task／global TOML 配置 teacher／student 的 backend／provider／model／effort／turn timeout、loop hours、最大 meta rounds 及 reference 生成时长|这些已是原生任务文件选项，不是新增项目 Agent 字段。Ergora 绑定路径、核精确源码，并逐 campaign 保存三个全局配置文件摘要。新选项须绑定原生 campaign／config 身份和原恢复；原生 judge 仍属候选生成证据。Owner 为 `kernel` 与既有 Forge driver。([F1]、[F2]、[F3]、[E7]、[E8])|
|`command`|Argv 可选择实际可执行程序的参数，没有通用模型／provider 合同|已有可配 argv；按需使用 plain text 或 `stage-json-v1` stdin／结构化 output。新语义由真实命令定义，保留 `Invocation` timeout／schema／capabilities；不能借此绕过受限后端准入。([E1]、[E3])|

Mini 与 Forge 源码分别固定于 `04d809ceab9df28f9adaed044884180159172930`、`5030503d3ff71851aa34c14b9caf13ebfa9d9a78`；DeepSeek 使用 `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb`，对应现有 `0.2.2rc2` 集成。更新上游功能不能继承本次准入。([E2]、[M3])

## 建议顺序

|优先级|可独立审查的候选|宣称产品支持前的验收边界|
|---|---|---|
|P0|已有模型／effort 的 requested／resolved／native-observed 记录，附后端／客户端／模型支持证据|区分省略／默认，记录优先级／cap／unknown，派发前冻结具体请求，恢复保留原输入／结果。实际值仅来自明确原生来源，不能从 argv 或外层 JSON 成功推断|
|P1|明确可选 Codex 服务等级，再补 verbosity／summary 展示|复用 `CodexBackend._options` 与 binding 元数据；逐模式 allowlist、真实所选模型接受及原输出／schema／取消检查；不扩大为通用 config|
|P1|明确 Claude 轮数与估算费用 cap|复用 adapter 的 print flags；原模式 ceiling／完整性在另行准入前保留，触顶／截断按失败报告，证明跨任务／恢复预算仍归原 owner|
|P1|DeepSeek 路由思考强度与输出上限语义|复用固定 SDK 初始化合同；核精确路由的支持等级／cap，保留冻结 patch／source／continuation 兼容，不能仅凭 registry 元数据宣称逐请求上限|
|P2|Claude fast mode／输出 token 界限，及逐后端上下文／压缩／推理重试|版本／模型／账户证据；明确环境／setting 优先级且不捕获秘密；有界总时长／费用和完整原来源材料|
|P3|Fallback 模型、原生 subagent／会话持久化、任意 provider kwargs 或跨后端采样|独立身份／资源／恢复设计和准入，不能顺手作为调参字段带入|

这些是建议，不是机械实现的字段清单。每个实现的配置和 argv／SDK 映射留在原 backend／driver，复用组件元数据、既有 binding／definition／manifest 冻结、公共 `Invocation` 和进程／runtime owner。只有真实消费者需要时才增加共享行为，不在调度器里新增按后端名分派的树。([E1]、[E2]、[E3]、[E4])

## Fixed、preset、planner 与 automatic

后三种未来模式可以选择具体配置，同时保留同一执行合同。**Fixed** 请求明确支持值；省略时沿用既有缺省。**Preset** 应解析一个带版本的后端／模型具体选项集合。**Planner** 可在批准／冻结边界前提出受支持的值并给理由。**Automatic** 需要明确有界策略、可观察输入与持久记录的具体结果。任何一种模式都不授予工具、网络、shell、更多并行或更大父预算。

区分用户请求、policy／preset revision、解析后的 backend／model／options、原生实际观察，以及 unknown／unavailable 原因。不要静默重解释未知原生值、将 `ultracode` 映射成通用排名、替换模型或降低 effort 以启动运行。原生环境／组织优先级仍可能改变应用结果；无法观察时报告 unknown。已有任务保持原冻结选择，恢复时不重新求值更新后的 preset／policy。这是设计建议，不表示上述字段或四模式已经存在。([A2]、[A3]、[E1]、[E3]、[E4])

## 验证与限制

共获取二十份官方文档／公开上游源码页面及一份限定官方域名的搜索响应，五次本地版本／帮助读取成功。私人原始来源／CLI 捕获、完整 SHA256 清单与读取错误保存在忽略的 `.ergora/checks/backend-runtime-options/`。搜索连接器不可用，改用 HTTPS 官方域名搜索／页面获取；失败的 raw 路径及 Markdown 简写均以成功的权威页面替换，不作为证据。

两份文件通过严格 UTF-8、互链／相对链接、围栏闭合、空白及限定范围的 `git diff --check`。每种语言的 28 份来源定义、112 次引用、行内配置名／值、表格结构和标题数量一致。每个官方／上游引用都对应成功获取的来源，固定 Ergora 文件均存在于所记提交。此前 12 文件文档批次仍逐字节冻结。这些结构检查不能替代独立语义审查，后者待接续。

本研究仅核源码映射与已获取文档。没有读取真实账户、配额、秘密、环境值或私人配置，没有运行模型、安装依赖、启动服务、测试计费／性能、实际执行原生 cap／fallback／压缩、验证 provider 接受，也未修改产品或 git index。后续每个候选仍需真实调用、受支持模型发现与独立实现审查。两份双语研究不替代当前 [Agent 手册](../AGENT_BACKENDS.md)或原产品验收。

## 来源索引

C1–C3 为 `developers.openai.com` 文档实际重定向后的官方页面；A1–A7 为 Claude Code 官方页面；D／M／F 为不可变公开上游文件；E 固定本次核对的 Ergora 产品。各表在主张处引用对应 owner 的来源。

[C1]: https://learn.chatgpt.com/docs/config-file/config-reference
[C2]: https://learn.chatgpt.com/docs/developer-commands?surface=cli
[C3]: https://learn.chatgpt.com/docs/non-interactive-mode
[A1]: https://code.claude.com/docs/en/cli-reference
[A2]: https://code.claude.com/docs/en/model-config
[A3]: https://code.claude.com/docs/en/env-vars
[A4]: https://code.claude.com/docs/en/fast-mode
[A5]: https://code.claude.com/docs/en/costs
[A6]: https://code.claude.com/docs/en/settings-reference
[A7]: https://code.claude.com/docs/en/settings
[D1]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/README.md
[D2]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/llm/llm-pi-ai/README.md
[D3]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/api.py
[D4]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/bundle/headless/README.md
[M1]: https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py
[M2]: https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/models/litellm_model.py
[M3]: https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/README.md
[F1]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/README.md
[F2]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/task.py
[F3]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/launch.py
[E1]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/agent_backends.py
[E2]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/data/components.json
[E3]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/agents.py
[E4]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/agent_runs.py
[E5]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/data/drivers/deepseek.py
[E6]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/data/drivers/mini.py
[E7]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/kernel.py
[E8]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/data/drivers/forge.py
