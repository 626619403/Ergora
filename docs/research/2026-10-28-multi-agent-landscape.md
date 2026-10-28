# 多 agent 工具调研与 Ergora 产品方案

调研日期：2026-10-28。本文是设计建议，当前可运行能力以 [README](../../README.md) 及其 v2.2 参考分发为准。本文没有为现有程序增加后端、配置格式或图形界面。

## 1. 建议结论

**推荐集成成熟项目，把 Ergora 做成统一使用入口、内部按职责组合的工具。** 用户安装一套工具、打开一个项目、查看一个任务；执行、工单、模型、通信和实验记录通过明确的绑定选择。

建议产品定位：**面向代码开发与训练优化的协作交付工具，以项目合同、人工决策和可复查证据管理多 agent 工作。** 工具编排、角色聊天、可视化连线、持久恢复和多模型支持都已有成熟实现，不能单独构成 Ergora 的定位优势。

关系表示优先复用 **JSON + JSON Schema**，可增加受约束的 YAML 编辑入口；另外评估 **Oracle Agent Spec** 的受支持子集，用作跨框架描述与交换。保留 Ergora 已有的任务、工作流包、策略、绑定及证据语义，不在第一版设计完整的新通用 agent 语言。[Agent Spec 官方项目](https://github.com/oracle/agent-spec)、[JSON Schema](https://json-schema.org/draft/2020-12/json-schema-core)。

首版继续采用现有 Codex、Temporal、Git worktree 和三模板；优先验证一个真实的第二执行后端，再扩展插件清单和界面。各后端的取消、恢复、权限与证据能力必须经过兼容性验收，界面中的可选项应反映这个状态。

## 2. 调研方法与边界

本轮读取了 **36 个工具项目的官方 README**，并补查官方 SDK、商业产品、关系描述规范和通信协议文档。下面比较 40 个代表性工具或产品家族；Agent Spec、OASF 和基础标准另列。范围覆盖通用框架、编码协作、可视化平台、持久工作流和通信层，未穷尽所有长尾项目。

事实依据为已取得的官方文档与部分架构、示例、接口说明；这是架构与产品调研，没有安装这些候选项目或对它们做统一业务任务测试。文档未描述某能力，不作为该项目绝对不支持它的证明。公开宣称的性能、规模和安全属性没有转写成独立验证结果。

[来源索引](2026-10-28-sources.json) 记录获取地址、重定向、日期、内容摘要和失败请求。`HEAD`、`latest` 代表访问时的文档快照，不是固定发布版本；没有将网页内容摘要冒充上游 commit。两个文档入口只取得跳转页面，相关判断改用对应官方 README。许可证获取不完整的候选也保留了缺口。

## 3. 市场与实现分类

### 3.1 通用 agent 与工作流框架

|工具|定位与主要实现方式|对 Ergora 的意义|
|---|---|---|
|[LangGraph](https://github.com/langchain-ai/langgraph)|底层状态图，checkpointer、interrupt、恢复和子图；可自行定义多 agent 控制流|已有候选搜索可继续复用；持久性和人工介入本身已有成熟参照|
|[Microsoft Agent Framework](https://github.com/microsoft/agent-framework)|多语言 agent SDK 与类型化工作流，含并行、交接、checkpoint、人工交互、DevUI|可作为大型团队的框架或后端候选，需明确运行时职责|
|[AutoGen](https://github.com/microsoft/autogen)|消息驱动、多 agent Team、GroupChat 与历史上的 Studio|当前 README 已标明归档并推荐 MAF；适合作为架构历史参照|
|[CrewAI](https://github.com/crewAIInc/crewAI)|Agent / Task / Crew 组织分工，Flow 编排状态、事件和控制流|现成团队抽象与配置方式；应比较其 Flow 与 Ergora 任务合同的边界|
|[OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk)|代码定义 agent、工具、handoff、审批及 tracing，由应用管理部署和存储|适合封装局部专家任务；handoff 与“agent 作为工具”有不同控制权语义|
|[Google ADK](https://github.com/google/adk-python)|当前 README 为 ADK 2.0，提供图式 Workflow Runtime、Task API 和模块化多 agent|应按当前图与任务 API 评估，不能只沿用旧版顺序/并行 agent 的印象|
|[Pydantic AI](https://github.com/pydantic/pydantic-ai)|类型化 agent SDK、可组合能力、Harness；提供多种持久执行引擎接入|“同一 agent 接不同运行环境”已经有直接实践，值得优先研究接口与恢复边界|
|[Strands Agents](https://github.com/strands-agents/sdk-python)|进程内 agent loop，提供 agents-as-tools、Graph、Swarm、Workflow 和 A2A 等模式|不同关系不宜压成同一种连线；可复用其局部协作能力|
|[Agno](https://github.com/agno-agi/agno)|SDK、AgentOS 与控制台分层；当前支持 Agno、Claude Agent、Codex SDK，含持久服务和审批|是工具可调、统一服务面的直接参照，相关能力不宜再宣称为独有|
|[Mastra](https://github.com/mastra-ai/mastra)|TypeScript agent、图式工作流、暂停恢复与 Studio，便于接 Web 应用|若未来前端与业务偏 TypeScript，可评估；当前 Python 控制面无需立即迁栈|
|[AgentScope](https://github.com/agentscope-ai/agentscope)|agent 应用与 pipeline，当前包含 leader 分派工作的 TeamPipeline|可参考团队分工与 agent 应用部署方式|
|[CAMEL](https://github.com/camel-ai/camel)|多 agent 研究、工具协作、合成数据及环境交互|适合研究与候选生成，项目交付门禁仍需具体定义|
|[LlamaIndex Agent Workflows](https://github.com/run-llama/workflows-py)|异步步骤发出和消费事件，支持分支、并行、持久状态与恢复，强调文档工作流|适合资料和知识处理子任务；需区分事件工作流与仓库验收合同|
|[Haystack](https://github.com/deepset-ai/haystack)|模块化 pipeline 与 agent，显式管理检索、路由、记忆和生成|适合检索/RAG 子系统，属于可接入能力层|
|[smolagents](https://github.com/huggingface/smolagents)|CodeAgent、ToolCallingAgent、层级多 agent 与执行环境选择|轻量专家或实验工具候选；代码执行语义要由具体后端承担|
|[Agency Swarm](https://github.com/VRSEN/agency-swarm)|基于 Agents SDK 扩展，以定向 `communication_flows` 约束 agent 通信|直接证明“显式关系图”已有实现；通信许可与任务完成依赖仍需分开|
|[BeeAI Framework](https://github.com/i-am-bee/beeai-framework)|Python/TypeScript agent、工具、工作流与多 agent 组合|可借鉴可组合部件和协议接入，采用前需核对所选语言版本|
|[GitHub Copilot SDK](https://github.com/github/copilot-sdk)|将 Copilot CLI 的 agent runtime 嵌入应用，暴露工具和权限处理能力|是一种可调用的执行后端；模型配置和完整 coding harness 不能混为一层|

这些框架已有审批、恢复或观测能力。例如 CrewAI 明确建议 Flow 管理生产控制、用 `@persist` 保存状态；Pydantic AI 当前文档列出多种 durable engine。因此 Ergora 的比较重点应是**项目所需规则是否已落实、是否可独立复验**。[CrewAI 生产架构](https://docs.crewai.com/en/concepts/production-architecture)、[Pydantic AI 持久执行](https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/)。

### 3.2 编码执行器、协作平台与仓库自动化

|工具|定位与主要实现方式|对 Ergora 的意义|
|---|---|---|
|[Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents)|编码 harness，可用专门配置和独立上下文组织子 agent|当前默认执行器与审查工具；外层合同负责项目范围和验收|
|[Claude Code / Agent SDK](https://code.claude.com/docs/en/agent-sdk/subagents)|SDK 支持 subagents；CLI agent teams 另有团队协调、共享任务列表与通信模式|适合第二执行工具候选；SDK 子 agent 与 CLI team 应分别接入、核对能力|
|[OpenHands Software Agent SDK](https://github.com/OpenHands/software-agent-sdk)|Agent、Conversation、Workspace、Agent Server 与类型化客户端；可本地或远端执行|优先验证的执行后端候选；已有 SDK/服务器可减少自建执行基础设施|
|[SWE-agent](https://github.com/SWE-agent/SWE-agent) / [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)|面向软件问题求解的执行与研究工具；官方已将主要开发转向更简洁的 mini-swe-agent，并推荐今后优先使用后者|新后端候选优先评估 mini-swe-agent；完整项目生命周期与取消恢复语义仍需外层接入和验收|
|[Agent Orchestrator / Orchestrator.inc](https://github.com/ComposioHQ/agent-orchestrator)|多编码 agent、独立 worktree、任务看板、reviewer、CI/评论反馈；现有架构含 Go daemon 和桌面 UI|与拟议 all-in-one 最接近，应先评估整体接入和已有 API|
|[Gas Town](https://github.com/steveyegge/gastown)|多 coding agent 工作区，分工角色、Git 持久工作、Beads、TOML formula/molecule|恢复、任务分工、工具切换已有工程化实现，值得比较真实操作成本|
|[Beads](https://github.com/steveyegge/beads)|面向 agent 的依赖任务、持久工作记忆和工作上下文|可作为项目任务入口候选；与现有 tracker 归属及任务 ID 需明确映射|
|[Vibe Kanban](https://github.com/BloopAI/vibe-kanban)|看板、分支/workspace、多编码工具切换、diff 审阅和 PR|可参考产品体验；当前 README 有 sunsetting 公告，不能直接假定持续厂商维护|
|[OpenCode](https://github.com/anomalyco/opencode)|可配置编码 agent；内置 build、plan 和 general subagent 等角色入口|另一实际 coding harness 候选，工具权限与模型配置需一起检查|
|[Ruflo / Claude Flow](https://github.com/ruvnet/ruflo)|围绕 agent 团队、记忆、编排和插件/控制台组织协作|插件体验和团队控制的参照；本文未独立验证其规模或性能宣传|
|[MetaGPT](https://github.com/FoundationAgents/MetaGPT)|以产品、架构、工程等角色和 SOP 组织软件协作|角色分工和 SOP 已有先例；现有仓库接入与证据要求仍需单独比较|
|[ChatDev 2.0 / DevAll](https://github.com/OpenBMB/ChatDev)|当前已发展为配置式、零代码多 agent 平台，经典软件公司版本在独立分支|不能只按早期“虚拟软件公司”评价；是关系配置体验的参照|
|[Open SWE](https://github.com/langchain-ai/open-swe)|围绕 coding agent、GitHub/Slack 和审阅的工程应用，当前直接部署依赖 Managed Deep Agents|可研究完整开发产品如何组合既有执行器；自主部署需核对该依赖|
|[GitHub Agentic Workflows](https://github.com/github/gh-aw)|Markdown + YAML frontmatter 编译为 GitHub Actions；多 agent engine 与受控 safe outputs|与“协作协议 + 编译 + 工程控制”高度相关，适合 GitHub 专用接入与设计复用|

Agent Orchestrator 的官方矩阵区分 Terminal、Chat、Reviewer 支持，能力注册也不代表本机已可用；其架构已经处理独立会话进程、事实持久化和恢复。这些能力应先评估接入，避免低估成熟执行管理的工作量。[Agent adapters](https://docs.orchestrator.inc/plugins/agents/)、[架构文档](https://github.com/ComposioHQ/agent-orchestrator/blob/HEAD/docs/architecture.md)。

GitHub Agentic Workflows 的 agent job、编译器和后续输出作业承担不同权限；safe outputs 对配置的外部写入进行校验与分阶段应用。其安全属性有具体 runner、隔离和凭据前提，不能通过复制 YAML 配置在共享用户容器里自动获得同等保证。[官方安全架构](https://github.github.com/gh-aw/introduction/architecture/)。

### 3.3 可视化平台、个人 agent 与商业产品

|工具|主要定位|接入建议|
|---|---|---|
|[Dify](https://github.com/langgenius/dify)|可视化 LLM 应用、RAG、工作流、agent、模型与工具管理|可用作业务应用或外部能力服务；许可证含附加条件，采用前按实际用途核对|
|[Langflow](https://github.com/langflow-ai/langflow)|可视化 agent/flow，提供 API 与 MCP 服务|可作为子流程作者工具，需明确导出内容和运行时依赖|
|[Flowise](https://github.com/FlowiseAI/Flowise)|可视化构建 agent 与 LLM 应用|可研究表单、节点配置和服务化体验|
|[n8n](https://github.com/n8n-io/n8n)|可视化自动化、外部系统连接与 AI 流程|适合接消息和业务自动化；采用 fair-code 许可，不应默认当作无额外限制的开源依赖|
|[Goose](https://github.com/block/goose)|本地桌面、CLI 与 API 的通用 agent 工具|可作为执行或桌面交互候选，具体多 agent 能力需另行对接验收|
|[OpenClaw](https://github.com/openclaw/openclaw)|个人 agent / Gateway、通信渠道、工具与 harness 插件|更接近个人助理和渠道入口，可作为外围接入；与仓库交付职责分开|
|[Cursor](https://cursor.com/docs/agent/projects)|商业编码产品；Projects 协调多个 agent、维护长期上下文并使用 Cloud Agents|统一入口和长期项目体验的直接参照，当前不是可直接迁入的开源核心|
|[Devin](https://docs.devin.ai/get-started/devin-intro)|商业软件开发 agent，强调任务分派、并行和 PR 工作方式|对照端到端交付体验；本文未购买、调用或测试其服务|

“源码可见”“OSI 意义的开源”“商业托管产品”在上表中分别处理。Mastra 当前 README 也区分 Apache-2.0 核心与 `ee/` 企业许可部分，代码复用应按具体文件核对。[Mastra 许可说明](https://github.com/mastra-ai/mastra#license)。

## 4. 关系表示应复用哪些格式

**建议自定义少量领域语义，复用现有语法、校验与协议。** 本项目术语见 [领域词汇表](../../CONTEXT.md)。

|规范或格式|实际负责的内容|在 Ergora 中的位置|
|---|---|---|
|[JSON Schema](https://json-schema.org/draft/2020-12/json-schema-core)|描述与校验 JSON 文档结构|任务包、策略、绑定、回执及证据的机器可读结构；DAG、权限和版本兼容仍由编译器校验|
|[YAML 1.2](https://yaml.org/spec/1.2.2/)|适合人工编辑的数据语法|可选作者入口，加载后形成同一种受校验对象；首版继续接受现有 JSON 即可|
|[Agent Spec](https://github.com/oracle/agent-spec)|agent、工具、模型、Flow 及多 agent 组合的可移植描述；提供 PyAgentSpec 和运行时适配器|优先评估受支持的导入/导出子集；不预设不同框架的执行与审批语义完全相同|
|[OASF](https://github.com/agntcy/oasf)|agent 能力、skills、domains、关系与发现元数据|需要跨组织目录时再接入；当前 Agent Card 可先承担服务发现|
|[A2A](https://a2a-protocol.org/latest/specification/)|独立 agent 服务之间发现、消息、任务状态与产物交互|继续作为跨服务适配；项目策略、精确计划审批和验收含义由 Ergora 约定|
|[MCP](https://modelcontextprotocol.io/specification/2026-07-28)|应用与工具、资源、提示等能力的连接与协商|提供 agent 可调用能力；不会自动定义整个项目的交付合同|
|[Agent Client Protocol](https://agentclientprotocol.com/protocol/v1/overview)|编辑器/客户端与 coding agent 的会话、请求、通知和权限交互|适合统一部分编码工具的交互接入，按能力协商使用|
|[AG-UI](https://docs.ag-ui.com/introduction)|前端与 agent 后端之间的事件、状态与用户交互|可以承载控制台的运行事件；审批仍由后端验证与记录|
|[CloudEvents](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md)|跨服务事件的通用信封与上下文属性|出现实际事件总线需求时复用，业务状态语义和去重规则仍归项目定义|
|[CNCF Serverless Workflow](https://github.com/serverlessworkflow/specification)|通用工作流 DSL、控制流、事件和函数调用等|可评估互操作映射；当前六阶段不需要先实现完整通用 DSL|
|[BPMN](https://www.omg.org/spec/BPMN/2.0.2/About-BPMN)|业务流程模型与表示规范|复杂人工作业或企业流程需要时再评估；完整引擎接入成本较高|

此处 ACP 特指 **Agent Client Protocol**。选用任何协议都应记录协议名、版本与能力，避免同名缩写被当作同一接口。

Agent Spec 已覆盖构件、图连接和跨框架描述，值得实际做转换样例。其通用模型与 Ergora 的项目保护路径、训练统计证据、精确人工审批之间，仍需要明确映射或扩展；未表达、无法保留的规则必须拒绝转换。本文没有证明 Agent Spec 无法表达这些规则，也没有证明现成适配器已经实现它们。[Agent Spec 语言规范示例版本](https://oracle.github.io/agent-spec/26.3.1/agentspec/language_spec_25_4_1.html)。

### 4.1 把四类关系分别表达

|关系|例子|需要表达的约束|
|---|---|---|
|工作依赖与控制流|集成等待两个实现单元完成|先后、并行、失败传播、资源与循环边界|
|委派与通信许可|协调者可向研究者提问|谁可调用谁、调用预算、交接后谁拥有控制权|
|资料与证据流|审查者读取候选 diff、检查结果和必要项目资料|输入/输出类型、版本、可见范围和产物身份|
|审查与决策权|独立审查后仍需维护者决定采用|上下文分离、角色权限、精确材料、批准人及有效期|

一条无类型的 `A → B` 无法同时准确表达这四种关系。图形页面应提供不同类型的边及其约束。通信许可本身不表示前置任务已完成；能读取产物也不等于有权批准它。

当前已支持的是六阶段下的**工作单元依赖与路径所有权**。例如以下 `work_units` 片段表达两个可并行修改的单元，不改变六阶段拓扑：

```json
{
  "work_units": [
    {
      "id": "api-change",
      "depends_on": [],
      "paths": ["src/api"],
      "instructions": "按已批准的接口合同修改 API。"
    },
    {
      "id": "client-change",
      "depends_on": [],
      "paths": ["src/client"],
      "instructions": "按同一接口合同修改客户端。"
    }
  ]
}
```

这是输入字段的节选，完整任务仍需 `goal`、`allowed_paths`、`acceptance` 等必填内容与可信检查。两个单元完成后由固定的 integrate 阶段集成；若修改范围重叠，必须调整依赖或拆分路径。

### 4.2 延续现有四类合同

|现有对象|继续拥有的职责|
|---|---|
|`package`|阶段、角色、输入输出与证据要求的可复用版本|
|`task`|某次任务的目标、输入、基线、工作单元与身份|
|`policy`|维护者规定的路径、检查、权限、审批和上限|
|`binding`|项目 tracker、运行环境、执行协议与能力的对应关系|

这些对象在现有 `portable.py` 和示例中已有实现。第一步可扩充 binding 的明确工具映射；模型提出的任务输入不能自行改写维护者策略。当前共享用户执行边界并不提供强制隔离的策略存储，新后端需要按其实际权限边界验收。

人工编辑如采用 YAML，应限定到 JSON 可表达的值、使用安全加载、拒绝重复键及不支持的标签，再交给同一编译器。保存图形布局等纯视图信息时，可使用单独文件，避免移动节点位置就改变任务语义摘要。

现有摘要函数必须保持版本语义。跨语言时可评估 [RFC 8785 JCS](https://www.rfc-editor.org/info/rfc8785/)，但当前排序 JSON 不等同完整 JCS；改变规范化会影响现有包、计划和证据摘要，需要新的版本与迁移，不能直接重解释在途任务。

## 5. 各层真实工具如何可调

**可以做到，但应逐层定义兼容边界。** 模型、agent harness、工作流引擎、工单系统和通信协议是不同选择；它们的替换成本及验收要求不同。

|层|当前可运行组合|后续可选方向|替换时要保留什么|
|---|---|---|---|
|模型服务|Codex adapter 的 Responses API 配置|相应 harness 支持的其他模型或 provider|工具能力、输出约束、凭据与预算；选择模型不等于更换 harness|
|实现与审查|Codex，不同会话|OpenHands、Claude Agent SDK、Copilot SDK、ACP agent|固定候选、工作目录、会话身份、结果查询、取消与审查变化检测|
|开发控制流|Temporal 六阶段|先保留；以后评估其他持久引擎|审批等待、恢复、幂等、版本、超时和外部作业对账|
|候选搜索|LangGraph + SQLite|其他生成或搜索实现|项目范围、候选数量、检查点及负面结果；仅生成提案|
|工单|本地关联，Symphony 的项目 tracker 接入|GitHub/GitLab 原生 API、Beads、其他项目系统|项目/工单归属、去重、准入和状态映射|
|服务通信|CLI、本地可信文件、A2A|HTTP、事件总线等按需求接入|请求身份、原始合同、状态/产物绑定与协议能力|
|工具与资料|执行后端本身的工具配置|MCP、项目已有工具服务|授权范围、输入输出、失败语义与审计|
|产物与证据|文件归档与固定证据校验|对象存储等|内容身份、可读取原始材料、版本与保留规则|
|实验观测|MLflow|其他实验记录服务|关联任务/实验身份及观测字段；正式验收不依赖观测页面自报|
|训练执行|逐实验手动可信 runner|Slurm、Kubernetes、已有训练服务|资源预算、精确作业查询、去重、停止确认、同一合同证据|
|本地服务管理|Supervisor|平台对应的部署方式|配置、日志、生命周期与持久目录；它属于部署层|

Temporal、Prefect 与 Argo 都能运行工作，但运行模型不同。例如 Argo 以 Kubernetes CRD 和容器任务组织 DAG；将 Temporal 改成 Argo 需要迁移执行与恢复语义。[Temporal Workflow Execution](https://docs.temporal.io/workflow-execution)、[Prefect Flow](https://www.prefect.io/docs/v3/concepts/flows)、[Argo Workflows](https://argo-workflows.readthedocs.io/en/latest/)。

**下方仅为新 binding 的概念草案，当前 CLI 不接受它，字段名也尚未定版：**

```yaml
api_version: ergora.design/v0
kind: ProjectBindings
project_id: my-project
workflow_ref: development-v1
executors:
  implementer:
    adapter: codex-cli
    config_ref: coding-default
  reviewer:
    adapter: codex-cli
    config_ref: independent-review
runtime:
  adapter: temporal
  config_ref: local-control
tracker:
  adapter: gitlab
  config_ref: project-issues
observability:
  adapter: mlflow
  config_ref: project-experiments
```

`config_ref` 指向受维护的配置与凭据引用，公开定义不包含密钥。改用另一个 reviewer 需要该适配器通过所需能力检查；当前分发只实现 Codex 审查。工具与模型选择在编译/审批前解析并冻结，在途执行沿用原绑定，新选择形成新的修订。

第一版适配器接口应复用现有 `submit / poll / authorize / fence` 等真实边界，按实际消费者拆分职责。仅替换内部函数名无法解决外部进程失联、重复提交或取消未知的问题。不支持的必需能力应在执行前明确报错，不能自动降低审批或验证要求。

## 6. 直接集成、适配、借鉴与暂缓清单

|候选|建议方式|原因与首个验收点|
|---|---|---|
|Temporal|继续直接依赖|已有控制流，先迁入并复验恢复/取消；保持正式任务状态的归属|
|LangGraph|继续局部复用|保持有界候选搜索；需要内部子流程时再扩展，明确外层任务与内层状态|
|MLflow|继续直接依赖，逐步做可选配置|复用成熟实验记录；门禁证据由任务合同和归档负责|
|Codex|保持默认执行工具|保护当前可运行路径，把现有耦合逐步提到配置和适配器|
|OpenHands SDK / Agent Server|优先做第二执行后端验证|官方有客户端与 workspace 边界；先验证精确候选、恢复、取消、产物和变更检测|
|Claude Agent SDK / Copilot SDK / ACP|按真实需求增加适配器|可复用完整 harness；各自会话、权限、认证和终态映射需要验证|
|Agent Spec / PyAgentSpec|优先做小规模描述转换验证|检验所选版本和子集是否保留当前合同；首版不强制所有安装者引入整套 runtime|
|Agent Orchestrator|评估整体接入或 API 桥接，同时借鉴已实现的执行管理|先验证能否保留 Ergora 任务/作业 ID、候选与证据身份，再决定是否采用其 UI/执行管理|
|GitHub Agentic Workflows|GitHub 场景评估导出/调用；复用其分阶段写入思路|需要 GitHub Actions 执行上下文；转换只接受能保留语义的子集|
|Symphony|继续按项目 tracker 适配|保留工单入口与执行准入的区分；接入其他 tracker 时统一归属|
|A2A / MCP / AG-UI|分别在对应边界复用协议和 SDK|跨服务、工具、前端承担不同任务，避免重复定义相同通信机制|
|React Flow 等画布组件|有编辑需求时复用界面组件|布局、节点交互与图语义分开，输出仍经过后端合同编译；[官方组件文档](https://reactflow.dev/learn)|
|Dify / Langflow / Flowise / n8n|先作为外部子流程或渠道接入|保留其独立产品能力；整包嵌入会引入重复用户、状态和依赖管理|
|CAMEL / MetaGPT / ChatDev 等整套框架|按具体子任务选择，暂不全部纳入默认安装|首版以当前工作流和第二后端的完整验收控制接入规模|

OpenHands SDK 的官方仓库已经区分 SDK/Agent Server、客户端、Agent Canvas 与自动化服务的归属，适合参考这种组件复用方式。Agent Orchestrator 是完整产品，当前能力按 daemon 构建注册；不能仅凭“有插件分类”假设可以把任意内部 Go 组件直接作为 Python 库导入。[OpenHands 仓库边界](https://github.com/OpenHands/software-agent-sdk#repository-boundaries)、[Agent Orchestrator 能力文档](https://docs.orchestrator.inc/plugins/agents/)。

### 6.1 采用源码时的具体边界

优先使用公开 SDK、CLI 或服务接口，并固定支持版本。需要迁入具体源码时记录来源 commit、文件、修改范围、许可证和上游同步方式。只有文档或模式借鉴时，无需复制其整套实现。

本轮已取得 OpenHands SDK、GitHub Agentic Workflows 的 MIT 许可文件，以及 Agent Orchestrator 的 Apache-2.0 许可文件。Agent Spec README 声明 Apache-2.0 / UPL-1.0 可选双许可，但本轮尝试的根目录许可文件地址返回 404，GitHub 目录 API 又遇到限流；实际采用前仍要取得固定版本的完整授权文件。此缺口不影响对其公开描述格式的调研，也不等于该项目没有许可证。[Agent Spec README](https://github.com/oracle/agent-spec#license)。

采用候选组件的许可不会自动确定 Ergora 自身许可证。本轮没有引入这些新依赖，也没有把候选项目的产品、托管服务或企业功能归入本项目授权范围。

## 7. Ergora 可以形成什么定位优势

以下是**适合投入验证的差异方向**，不是已经证明领先竞品的结论。

1. **项目交付合同作为核心交付物。** 用户可以把任务、可信检查、权限、计划决策和验收规则带到自己的仓库；更换执行工具时仍可检查这些规则是否成立。
2. **代码开发与训练实验共用交付框架。** 保留三模板，并把 baseline、数值/质量约束、成对测量、原始证据和集成复验连接起来。训练收益必须在真实 workload 上重新测量。
3. **把外部作业的未知结果显式交给对账流程。** 重启后恢复执行身份，区分请求取消与实际停止；替换工具时用统一的失败场景验收，减少依赖某个 UI 的隐含状态。
4. **工具选择有可查询的兼容等级。** 区分“已安装”“认证可用”“声明支持”“通过本项目合同验收”，配置选择能显示缺失能力及影响。
5. **一套容易开始的产品入口。** 默认完成一个本地项目任务，用户随后按需求接入工单、实验、训练和其他 agent；把现有安装包的完整流程变成稳定体验。

这些能力与其他产品仍有重叠。仅需多 agent 看板与分支管理的用户已经可以评估 Agent Orchestrator；需要通用 agent 开发与多 runtime 的团队可以评估 Pydantic AI、Agno 或 MAF。Ergora 更适合以**可带入具体项目的验收工作流与证据管理**切入，再根据真实用户决定平台规模。

当前仍欠缺：独立模块发布与公开 CI、广泛后端兼容性、团队身份和执行隔离、真实项目比较数据、图形入口，以及项目许可与贡献流程。源码与配置存在的耦合应先整理，不能把组合已有工具自动等同成熟平台。

建议用同一组真实任务比较配置耗时、首次任务成功率、人工审阅时间、重启后恢复情况、重复副作用、错误候选拒绝率、模型成本和证据可复验性。训练另比较固定质量下的时间、数值容差和成对重复结果。没有这组数据前，优势应表述为定位与已落实规则。

## 8. All-in-one 的产品形态

推荐做到**统一入口与运行视图，内部保留清楚的组件归属**。

用户只需安装 Ergora、接入自己的项目、选择一套默认配置，随后在同一处发起任务、查看进度、阅读计划、批准、审阅证据和导出分支。项目仍拥有自己的业务仓库与工单；控制台可以聚合视图。

### 8.1 按使用阶段启用能力

|使用组合|建议启用的能力|进入条件|
|---|---|---|
|本地开发默认组合|CLI、当前控制流、Codex、Git、文件产物与服务管理|一个真实仓库、可信检查、模型凭据、明确执行边界|
|项目工单组合|默认组合 + GitHub/GitLab tracker 与相应接入服务|按项目配置工单身份、映射和准入|
|实验研究组合|默认组合 + LangGraph、MLflow 与训练控制功能|有 workload、基线、runner、资源预算和证据格式|
|跨服务组合|按需增加 A2A、MCP 或其他接口|对端能力、认证、协议版本与恢复行为已核对|

上表是建议的未来安装配置。当前 v2.2 安装与服务命令仍按 README 使用，尚无这些新的 profile 选项。真实训练继续由操作员确认明确实验，不因启用研究界面就自动扫描并运行队列。

### 8.2 图形页面的实施顺序

1. **先观察与决策。** 展示任务、当前阶段、工作单元、候选提交、检查与证据、待批准计划、预算和异常对账。先解决用户最频繁的交接。
2. **再配置。** 根据组件 Schema 生成表单，选择角色绑定、模型、工具、tracker、观测和执行环境，显示兼容检查结果和配置差异。
3. **最后关系编辑。** 用现成画布组件编辑工作单元、依赖和资料流，并预览可执行合同；CLI 与 GUI 走同一个编译器。当前六阶段不开放任意改变，扩展拓扑需新的协议版本与验收。

界面布局与样式属于视图，审批、权限和执行决定属于后端。需要跨产品实时交互时可接 AG-UI；已有 REST/SSE 能满足首版时，不必先引入另一套复杂交互层。[AG-UI 规范定位](https://docs.ag-ui.com/introduction)。

## 9. 推荐的首版仓库实施顺序

### 第一步：把当前工作流迁为可维护的参考发行

先迁入实际源码、模板、合同、锁文件和安装器，记录来源及许可。保留一个 Python 主包，复用现有纯合同与编译边界；安装路径、服务地址、凭据引用和项目绑定从核心逻辑中逐步提取。明确默认使用的 Temporal 版本和现有六阶段语义。

使用最小真实项目验收：注册 → 创建 → 盘点 → 精确计划批准 → 实现 → 集成 → 检查 → 独立审查 → 导出；另验取消与重启恢复。将安装、配置与首次任务串成一个可复验的路径。

### 第二步：证明真实工具可替换

从 OpenHands SDK / Agent Server 开始做一个有明确范围的后端验证；如果 Agent Orchestrator 的公开接口更好地满足所需合同，也可以选择其桥接方案。默认 Codex 路径保持可用。用同一任务合同检查两个后端，再决定扩展更多工具。

适配器验收至少包括：相同作业身份的重复提交、控制面重启、后端结果未知、精确候选取证、超时、取消竞态、审查修改检测、缺少必需能力、凭据不可用和错误证据拒绝。验证实际行为后再向用户显示为兼容。

同时用一个简单 Agent Spec 样例验证导入、导出与不支持结构的拒绝。记录保留了哪些语义，不能仅凭 JSON 能解析就宣称跨框架可移植。

### 第三步：统一安装、配置和观察入口

把默认开发、工单、实验和跨服务依赖组织成可选安装组合；提供组件探测和清楚的错误指引。新增控制台先消费正式任务状态和归档证据，后续增加同一 Schema 的配置表单与受约束图编辑。

继续保持一个正式生命周期拥有者；外部 orchestrator、agent session、训练调度器各自的状态通过映射对账。采用新的整个工作流引擎、完整 UI 产品或安全边界时，单独验证状态归属与恢复语义。

## 10. 本轮交付与未实施项

已完成官方资料核查、分类比较、现有合同对照和上述产品/集成建议，并保存来源索引与术语表。未安装候选项目、引入新依赖、实现 Agent Spec 转换、新 YAML binding、插件系统、安装 profile、GUI 或新执行后端。公开源码迁入与具体实现应按上述可验收切片继续推进。
