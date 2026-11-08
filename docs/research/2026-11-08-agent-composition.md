# 按职能与专长组合 Agent：实现和论文对照

日期：2026-11-08。源码观察固定在`b1dbe48a1b14e8e2ec59d4f44e30b2ea367fa1fe`。本轮接续[工具全景](2026-10-28-multi-agent-landscape.md)、[持续演进](2026-10-28-continuous-evolution.md)、[三个模板的 Agent 选型](2026-10-31-template-agents.md)和[DeepSeek 原型研究](2026-11-02-deepseek-agents.md)，定向核对 Agent 定义、成员关系、权限和审查，而非重做一份工具排行榜。

用户希望每个模板组合多个执行者、审查者、监管者；每个具体 Agent 有独立保存的专长、后端、提示词、权限、MCP、Skill 和资料。各职能均可独立选后端，执行者与审查者优先选择不同后端；同类成员也可以分工，例如 kernel 实现与整体架构审查。此需求包含定义、分配和执行三层，不能只将现有 binding 改成数组。

本文的实现结论来自官方文档及固定源码，论文结论来自定向阅读的正文方法、实验及限制；没有运行竞品、复现论文或测得 Ergora 的质量收益。来源和内容身份见[清单](sources/2026-11-08-agent-composition.json)，采用决策见[ADR0004](../architecture/decisions/0004-agent-composition.md)，执行节点见[AC计划](../plans/2026-11-08-agent-composition.md)。

## 1. 当前代码已经做了什么

|事实|实际所有者|含义|
|---|---|---|
|角色与工具有分离入口|[components](../../src/ergora/components.py)、[agents](../../src/ergora/agents.py)|Codex、Claude Code、mini 和 command 可按支持的角色独立绑定，模板无需写死厂商；并非所有后端都支持所有角色。|
|每个角色只有一个有效 binding|[projects](../../src/ergora/projects.py)、[bindings](../../src/ergora/bindings.py)|正式开发快照只冻结 inspector/planner/implementer/reviewer 四项；没有可复用的命名 Agent 包、同角色多成员或专长覆盖策略。|
|正式执行与模型调用分开|[reference_executor](../../src/ergora/reference_executor.py)、[stage_driver](../../src/ergora/stage_driver.py)|原 executor 保留 Git、可信检查、时限和回执，桥接选择角色后端。`agents.invoke` 的多个具体后端分支仍集中在同一所有者。|
|最终审查有候选和独立性门禁|[activities](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/activities.py)|检查精确候选、显式 independent-review pass、actor kind、作者 ID 和会话排除；这些是可信层规则。actor 字符串不是恶意同用户环境下的身份认证。|
|角色文件有职责描述|[治理 roles](../../src/ergora/data/reference/platform/templates/repository-governance/roles.json)、[大型变更 roles](../../src/ergora/data/reference/platform/templates/large-change/roles.json)|capabilities/forbidden_actions/independent_from 表达职责，不能据字段存在推断每条动作都被 OS 或工具拦截。|
|Skill 版本、评价和采用已有用例|[skill_assets](../../src/ergora/skill_assets.py)、[evaluation](../../src/ergora/evaluation.py)、[skills](../../src/ergora/skills.py)|内容定址与活动版本头可复用；正式任务尚未冻结、加载选定 Skill 集合。权限、资源装载和专长评价仍需补齐。|

主代理沿`tasks → reference_task_creation → compiled/task.spec → workflow → reference_executor → stage_driver → agents.invoke → receipt → activities.poll`核对了当前审查流程。编译产物虽保存模板 instructions，阶段 prompt 目前只拼通用指令、任务上下文和依赖材料；不得把保存了文本等同实际加载。Codex reviewer 默认 read-only，但 binding 可以显式覆盖；Claude reviewer 的内建工具限制和空 MCP 也不等同 OS 隔离。两者均需在计划中分别修正或明确展示。

此外，当前逐份截取依赖材料前60000字符的方法不能当作未来通用上下文策略。新增 Skill/专长材料要有预算、来源、截断提示与完整续读入口，不能通过无限堆叠提示词实现“专家”。当前缺陷和全面独立审查的覆盖范围、未验部分见[共享评审](../delivery/2026-11-08-agent-composition-review.md)。

## 2. 成熟实现怎样划分职责

以下 SHA 为本轮公开 HEAD 解析后固定的源码。只比较已读接口，不宣称各系统拥有相同安全或交付保证。变化中的官网有时滞后于源码：例如本轮 AgentScope 教程仍展示 ReActAgent，固定 HEAD 已使用 Agent；Google 旧 multi-agents 地址重定向 workflows；CrewAI 文档仍列 code execution 参数，固定源码已标记弃用。接入时必须锁定组合，不能拼接不同版本的示例。

|对象与固定源码|观察到的设计|适合借鉴 / 接入范围|
|---|---|---|
|[OpenAI Agents SDK](https://github.com/openai/openai-agents-python/blob/27c75c5f9c5fd957d28c04fb7e9eeacaad4630a9/src/agents/agent.py)|Agent 保存 instructions、model、tools、MCP、handoffs 和输出配置；运行上下文及 Runner 另有责任。MCP 连接/清理是需要明确管理的生命周期。|采用定义与运行分离；区分 agent-as-tool 与 handoff，不把二者都画成一条“协作线”。guardrail 不替代本项目可信候选门禁。参见[官方定义文档](https://openai.github.io/openai-agents-python/agents/)。|
|[Google ADK](https://github.com/google/adk-python/blob/1cb926d5b8d702261ec82a26d3f1c4296e0db7d7/src/google/adk/agents/llm_agent.py)、[BaseAgent](https://github.com/google/adk-python/blob/1cb926d5b8d702261ec82a26d3f1c4296e0db7d7/src/google/adk/agents/base_agent.py)|LlmAgent 配置模型、instruction 和 tools；BaseAgent 管 sub_agents/parent。子实例有单一父关系，ParallelAgent另管并发。|可复用定义、每次构造运行实例；不能将共享一个配置文件误实现为共享一个有状态子实例。[并行实现](https://github.com/google/adk-python/blob/1cb926d5b8d702261ec82a26d3f1c4296e0db7d7/src/google/adk/agents/parallel_agent.py)不自动解决共享 checkout 写冲突。|
|[LangGraph](https://github.com/langchain-ai/langgraph/blob/e5e37b5d70dbfd93c7006bd90a658c6179a95946/libs/langgraph/langgraph/graph/state.py)|StateGraph 的节点读状态、返回部分更新；reducer处理共享字段。builder须compile，运行上下文和状态schema有分别。|借鉴显式数据流、聚合与状态所有权。Ergora已有Temporal，不再新增第二套顶层持久调度；未来可把既有图作为一个有界候选生成adapter。[官方图说明](https://docs.langchain.com/oss/python/langgraph/graph-api)。|
|[AutoGen AssistantAgent](https://github.com/microsoft/autogen/blob/d07c667a3239ea4ab7af62a53b0f4ff205a1f23d/python/packages/autogen-agentchat/src/autogen_agentchat/agents/_assistant_agent.py)、[Team](https://github.com/microsoft/autogen/blob/d07c667a3239ea4ab7af62a53b0f4ff205a1f23d/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_base_group_chat.py)|Agent 的模型、工具、系统消息与Team的参与者、终止条件、max_turns分别配置；Team要求成员名唯一。|借鉴运行成员ID、显式结束和预算；“聊天结束”仍须映射成真实结果，不能直接作软件验收通过。|
|[CrewAI](https://github.com/crewAIInc/crewAI/blob/2fba413623a60d7a2f24a7d21685bbcd8dd45a4f/lib/crewai/src/crewai/agent/core.py)|角色、目标、背景、模型、提示模板、工具/MCP和运行限制可配置；具体执行器仍另有实现。|借鉴便于填写的 Agent 卡片和[配置文档](https://docs.crewai.com/en/concepts/agents)。描述性 backstory 不证明专业能力，专长标签不直接授予权限。|
|[AgentScope Agent](https://github.com/agentscope-ai/agentscope/blob/782bd43f9f61788a1901fcc4e5486758491d387f/src/agentscope/agent/_agent.py)、[TeamPipeline](https://github.com/agentscope-ai/agentscope/blob/782bd43f9f61788a1901fcc4e5486758491d387f/src/agentscope/pipeline/_team_pipeline.py)|Agent将system_prompt、model、toolkit、middleware、state和分组配置分别注入；TeamMember是Agent+分派说明。Team把成员结果交回leader，同成员分派串行，跨成员可并行。|借鉴配置组合与成员上下文分开；middleware/toolkit负责真实运行行为，不能只输出权限标签。本轮未运行其权限、MCP或恢复。|
|[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness/tree/ce7073d51254c26cd63b22a60835b8f948deb447)、[Super-agent原型](https://github.com/deepseek-ai/dsh-superagent-prototype/tree/6337fc823ce20251c8de8085948165c81aaa701e)|既有固定源码研究区分Agent接口/loop、领域对象、事件、授权、会话与外部执行。原型明确不是正式产品或文章的完整实现。|借鉴跨任务交互与单任务执行分开、原生回执与持久副作用意图；保留既有[50文件证据](sources/2026-11-02-deepseek-agents.json)，本轮没有换成新HEAD或直接整包依赖。|

[OpenHands与ForgeKernel的先前定向研究](2026-10-31-template-agents.md)仍有效作为固定版本证据：前者是可选执行adapter候选，后者已接入受限的候选生成流程。Forge的内置judge、模型认证与GPU依赖不因命名为“kernel专家”而消失；KDA/KernelWiki等知识资料可进入独立Agent包，但须分别处理许可、来源和实际加载。

共同模式是定义、成员分配、状态与执行策略分离。没有证据表明必须照搬其中任意一套类继承树，或需要一种全新的跨厂商DSL。

## 3. 相关论文及可用结论

阅读范围精确到下列章节；并未逐页复核所有附录、证明或外部数据。这里将作者结论、实验条件和本项目建议分别说明，研究收益不迁移成Ergora承诺。

|论文 / 正文阅读范围|研究内容及限制|对Ergora的判断|
|---|---|---|
|[Why Do Multi-Agent LLM Systems Fail? / MAST，v3](https://arxiv.org/html/2503.13657v3)，§3–5、附录A/G/H|对多系统轨迹归纳规格/系统设计、Agent间对齐、验证与终止三类失败；人工标注与LLM标注有分别，分类非穷尽。个别提示或拓扑干预有收益，也有不显著结果。|先明确职责、交接、停止条件、覆盖缺口和可信验证；复盘可使用失败分类，不能只加更多审查者或用“通过率”隐藏验证不足。|
|[Cut the Crap / AgentPrune，v1](https://arxiv.org/html/2410.02506v1)，§2–4|将空间/跨轮通信分开，优化掩码再剪枝；使用有评分的任务。正文说明简单chain/direct-output不适用该模块，优化本身也有成本。|默认显式、稀疏的证据交接；先测通信开销和质量再考虑剪枝。不能删除可信验收边，也不按论文数字承诺省token。|
|[AFlow，v4](https://arxiv.org/html/2410.10762v4)，§3–5、附录A的算子/代码映射及G|搜索代码表示的完整工作流，以执行反馈和MCTS式经验迭代；核心实验依赖数值评分、验证/测试划分及多次执行。添加review节点也出现负收益。|组合与Skill优化只生成候选，在固定评价、预算和采用流程中比较；先复用GEPA入口，不为“自进化”马上重写搜索器或可信workflow。|
|[Multi-Agent Collaboration via Evolving Orchestration，v2](https://arxiv.org/html/2505.19591v2)，§2–3、附录B–D|中心策略按状态选择Agent，用最终质量/token奖励优化序列；明确仍假设固定Agent/工具集合，中间反馈和错误协同有局限。|保留将来可替换选择策略，但先实现确定的成员分配。不能把论文中的在线策略训练说成现有RSI，亦不允许学习策略修改验收/权限。|
|[Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena，v4](https://arxiv.org/html/2306.05685v4)，§3.1–3.4、§4设置|研究偏好评分的顺序、冗长和推理能力问题；作者对self-enhancement因果判断保持保留。主要场景是聊天偏好，不是仓库验收。|多后端审查是降低共同盲点的策略，不是误差独立或质量最优的证明。要求可核对finding、候选与检查；不要用篇幅、票数或换模型替代证据。|
|[A Programming Paradigm for Spatiotemporal Composability / Cordis，v1](https://arxiv.org/pdf/2608.25512v1)，§1、§5.1.1、§5.2热重载段、§6.1–6.5|把可撤销副作用、依赖激活和清理放在同一context范式；逆操作正确性仍由实现者承担。明确外发副作用不自动回滚、语言内依赖限制不是不可信代码沙箱。|借鉴资源取得与清理相邻、依赖声明和adapter生命周期。继续用事务/意图/对账管理外部写入；不以热重载为由替换运行中已批准Agent或整套引入Cordis。|

“多成员互补”应表现为不同的可核对职责、资源与覆盖。例如kernel执行者交付候选和测量材料，架构审查者检查模块interface、修改局部性与兼容性，正确性审查者核对需求和边界。是否提升结果，要用相同任务、基线、真实预算和可信检查比较，保留负面结果；不把每个专长都自动变成一个必跑节点。

## 4. DeepSeek文章的读取边界与参考价值

用户提供的[知乎链接](https://zhuanlan.zhihu.com/p/2099987320443237060)本轮返回403；[公众号原文](https://mp.weixin.qq.com/s/zoS7GlReWPhfCjENGxXCdg)也未取得。已阅读[可访问转载](https://offloop.org/zh-CN/learn/exploring-deepseek-super-agent-design)的设计、实验条件和开放问题，但未独立验证转载与原文逐字一致。架构建议以此为辅助，并以[官方原型说明](https://github.com/deepseek-ai/dsh-superagent-prototype)及前轮固定源码交叉核对；不把转载当新官方产品规格。Cordis是另一篇形式化论文，不能和这篇工程文章混称为同一套实证结论。

本文对文章的有限摘要是：跨任务Router与单任务Worker分工，事件路由、按需上下文、异步交互、计算/状态/环境分开和外部Watchdog构成其讨论重点；文中初步实验使用合成消息及简化执行，不证明真实代码质量或最优模型组织。以下为Ergora自己的取舍：

|取舍|落点与理由|
|---|---|
|保留|已有六阶段、Temporal、精确计划/候选、原生回执及REVIEW_READY出口；Router不应再实现一套可信验收。|
|微调|F7先做确定性Source/Thread归属和去重，有需要再使用语义路由；用户面对任务和待办，不必手动管理底层所有会话。|
|增加|AgentDefinition和成员分配；F10以有来源的引用、摘要、续读和预算装配上下文；监管者先观察进展并提出有界恢复建议。|
|限制|事件上下文不等于行动授权；Watchdog不自授权限、不改可信策略或自动采用自身修改；原服务管理器管进程存活，模型可选判断任务进展，责任分开。|
|暂缓|投机外部写入、动态拓扑学习、运行中热换Agent、整个Super-agent迁入，以及为所有项目维护一个全局业务工单仓库。|

## 5. 推荐的产品方向

Ergora继续定位为可组合的软件交付与实验控制面：为已有Agent/harness组织专长、任务、权限和证据，让同一模板可选择工具实现。Agent库提供可版本化的专家配置，模板提供职责搭配与验收；已有CLI/Web/逐项目仓库入口保持。

优先顺序为：修复当前可达缺陷 → 将真实后端差异放进局部adapter → 独立Agent包及冻结资源/有效权限 → 多成员分配和多审查策略 → 图形配置 → tracker/新harness/实验/持续改进。为任意聊天拓扑制造通用引擎不是此轮前置。

执行者和审查者优先不同后端的规则应在实际后端解析后比较，不能只比较Agent名称。Codex与Claude Code是不同harness；底层模型/提供方是否也不同要另记，未知不能宣称不同。每成员有自己的时限和预算；偏好无法满足时显示原因，不能在已开始任务中静默切换。具体设计与验收只在[ADR0004](../architecture/decisions/0004-agent-composition.md)和[AC计划](../plans/2026-11-08-agent-composition.md)维护。
