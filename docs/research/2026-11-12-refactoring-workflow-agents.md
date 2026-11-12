# 重构、代码治理专家与可复用六阶段流程

调研日期：2026-11-12。R10 对应[专家模板重整计划](../plans/2026-11-12-specialist-template-refresh.md)与[分类说明](2026-11-12-optimization-taxonomy.md)。本地源码核对身份为 `42902bbe1af59059b287a38f0c9efa51a72dca4b`；开始时已有其他研究／计划文档修改，本文不将其算作自己的实现。本文只提供选型与待实现合同，没有安装、调用模型、执行训练或对任何实现片作独立通过判定。

建议先**采用现有六阶段、AgentDefinition 和可信检查所有者，适配专长资料与明确的 refactoring 入口**；编辑工具按项目需要接入，独立审查继续核精确候选。六阶段成为真正可嵌套子模板需要一个沿原运行所有者的 native 调用消费者，单纯增加六个节点或换一个根模板名称不足以完成。不要为重构另建 scheduler、任务账本或聊天式批准机制。

## 1. 当前可用接口与缺口

本轮直接阅读了以下源码及现有 Agent／Workflow 手册、治理／大型变更 preset。早先[模板选型](2026-10-31-template-agents.md)、[Agent 组合](2026-11-08-agent-composition.md)和[嵌套工作流研究](2026-11-08-nested-workflows.md)只作为其当时固定版本的历史设计证据；下表来自当前源码重新核对。

|当前所有者与 Interface|已实现的能力|对 R10 的约束|
|---|---|---|
|[AgentDefinition](../../src/ergora/agent_definitions.py)：`inspect_bundle`、`validate_admission`、精确 `get/revise/export`|同一定义可有多个 `roles`、`specialties`；职能逐项检查后端准入，定义按版本／摘要固定。|复用这些多对多关系，不按“重构、测试、架构”各造一个基类；专长和描述不授予工具权限。|
|[WorkflowDefinition](../../src/ergora/workflow_definitions.py)：`_Compilation`、`_materials`、`compile_input`|嵌套 Agent／Workflow 与 all-join；沿结构祖先累加完整正文，去重保留全部来源，同名资源／Skill 冲突拒绝；权限与预算逐层核。|这是静态组合及受支持阶段的输入基础。`compile()` 明确 `executable: false`；[v2 schema](../../src/ergora/data/schemas/workflow-definition-v2.json)没有 native 外部流程调用节点。|
|[Agent runs](../../src/ergora/agent_runs.py)：`check_input/run_input`、内部 `run_workspace`|前两者只准入／调用选中只读叶；`run_workspace` 仅由原 Executor 的正式调用授权，复用快照、MCP、进程与结果所有者。|`run_input` 不执行前驱或端口。不能先独立调用几次叶子，再宣称运行过完整图；workspace 也不是通用 CLI 写入模式。|
|[StageDAG／WorkDelivery](../../src/ergora/review_dags.py)|投影原 work/review 的控制前驱、端口与祖先并发上限；work 单叶与原 work unit 一对一，依赖闭包必须一致；review 只读。|不是任意混合职能图运行器；六阶段、native campaign 或额外 planner 不能直接塞进这些叶子。|
|[WorkflowInput](../../src/ergora/reference_inputs.py)：版本路由、`start`、`worker`、`stage_material`；[reference workflows](../../src/ergora/reference_workflows.py)|v1–v7 各自选择原六阶段的 workflow、adapter、queue 与 request-root；正式工作／审查沿原 Temporal 和 receipt 执行。|这是六阶段复用的现有 seam。新行为用显式版本化入口，保留旧输入、在途任务与冻结源码；不能把静态 WorkflowDefinition 直接传给 `start`。|
|[正式任务用例](../../src/ergora/tasks.py)及[手册](../USAGE.md#正式任务的操作顺序与恢复)|已有 preview/create/start/status/approval/cancel/reconcile/evidence，提交和信号有原意图／恢复规则。|native 包装必须调用这些原所有者，不能平行维护“已批准／已成功”。`submitted`、`requested`、Temporal terminal、`REVIEW_READY`与最终采用分别表达。|
|[Forge native 所有者](../../src/ergora/kernel.py)：`create(plan/prepare)`、`operate(run/status)`|绑定固定源码／配置、原 campaign ID、进程原件；不确定 prepare/run 保留 `outcome_unknown` 并要求对账。|可借鉴 native 身份与 unknown 处理；当前没有通用 native 模板消费、父级材料注入、完整取消接口或六阶段嵌套接口，不能按已有名字推导出来。|

现有 [preset catalog](../../src/ergora/data/presets/presets.json)只有 `repository-governance`、`large-change`、`training-optimization`。前两者配置 work/review；训练是 proposal-leaves。治理 work 的两名专家承担知识地图与架构回归，尚无明确“行为保持的代码重构”旅程；[任务定义](../../src/ergora/data/schemas/task-definition-v2.json)也只接受前两个 `task_type`。这同时是入口与运行能力的差距，不能用一份新说明抹平。

## 2. 少量值得接入或借鉴的真实实现

以下是本轮通过官方仓库 HTML 解析 `currentOid` 后读取的固定源码，不声称是最新稳定发行版。GitHub REST HEAD 请求均遇到未认证限流 403；没有切换凭据。Aider 与 AI Hero 的本次可见 HEAD 和早期固定身份相同；这是重读该身份，不证明其间没有其他分支或发行。

|对象、固定版本与许可|真实 Interface／分工|判断与局限|
|---|---|---|
|Aider：`5dc9490bb35f9729ef2c95d00a19ccd30c26339c`；源码 `0.86.3.dev`，Python ≥3.10,<3.15；Apache-2.0。[版本][aider-version]、[环境][aider-project]、[许可][aider-license]、[参数][aider-args]|`--architect`／`--chat-mode architect`、`--model`、`--editor-model`、`--message-file`；architect 提建议，再由 editor 生成编辑；支持只读附加文件、lint/test 设置。[实现][aider-architect]、[说明][aider-modes]|**借鉴分工，暂缓默认后端接入**。两模型调用增加成本，editor 可与 architect 相同，不是独立审查。自动提交／dirty 提交默认开启；若接入需显式关闭，Git 和可信检查仍归 Executor。stock 文本与本地 lint/test 不是 Ergora stage receipt；当前 workspace 合同也不支持把任意 Aider 命令当 Codex writer。|
|PR-Agent：原 Qodo 社区项目现迁至 `The-PR-Agent/pr-agent`；`41a7ead86d3ede31d2ec7e54b5a7673a0b9acee5`，pyproject `0.49.0`、Python ≥3.12，MIT。[身份][pr-readme]、[许可][pr-license]、[元数据][pr-project]|本地 `pr-agent --diff-file change.patch --output review.md --json-output review.json review` 或 `--stdin`；[CLI][pr-cli]将其路由到 `PlainDiffGitProvider`，写 stdout／文件，不要求发布托管平台评论。当前 `/improve` 是 `/review` 的别名，不能算第二名独立专家。[命令表][pr-registry]、[provider][pr-plain]|**适配为可选建议性审查**，先于接 SaaS／Action。raw diff 无可信 head SHA，provider 明确缺 head-staleness／CI 等能力；需外层绑定原候选、完整文件、实际模型与覆盖。大 diff 有过滤、压缩、分块、失败分块和 findings 数上限，[源码][pr-reviewer]不支持“零意见＝全面通过”。源码注释含“since 0.51”，不能仅凭 pyproject 版本推断接口。|
|Serena：`6e5c3776d4e67befaab7c290bc29b0279c98d1ed`；`2.1.1.dev0`，Python ≥3.11,<3.15；应用 GPL-3.0-or-later，SolidLSP MIT，组合发行遵循 GPL。[元数据][serena-project]、[许可][serena-license]|MCP 工具，包括 `find_symbol`、`find_referencing_symbols`、诊断，以及 `replace_symbol_body`、`rename_symbol`；LSP 提供实际语言语义。[工具源码][serena-symbols]、[文件工具][serena-files]|**按需适配工具，不充当重构 Agent**。语言服务器、项目初始化与客户端均有依赖；不能保证找全动态导入／反射。读取与编辑工具应按任务权限分配，不能把整个 MCP server 默认给 reviewer。当前 Ergora task-mcp 只暴露原 scope 的 list/read；Serena 不会因配置文件存在而自动成为受支持工具。|
|AI Hero／mattpocock skills：`4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`；本地索引登记 1.3.2，MIT。[目录][hero-readme]、[许可][hero-license]|`improve-codebase-architecture` 先按变化热点和术语调查，给 deepening 候选；`codebase-design` 定义 module/interface/seam/adapter；`code-review` 固定 diff 后分 Standards／Spec 两轴。[架构][hero-architecture]、[设计][hero-design]、[审查][hero-review]|**适配资料与职责，不能整套当引擎导入**。这些是由宿主执行的 Skill 指令，没有自己的持久运行、权限或恢复。只把有证据的 smell 当判断线索；repo 规则优先，不重复 lint 已覆盖事项。本轮按研究任务读取，没有触发其实现／发布 tracker 或实际并行审查流程。|
|Agentless：`5ce5888b9f149beaace393957a55ea8ee46c9f71`，README 的 1.5 系列研究流程，MIT。[源码入口][agentless-readme]|脚本分别进行层次定位、采样 patch、回归／复现测试与候选排序；不是长期对话 agent。[定位][agentless-localize]、[修补][agentless-repair]、[测试][agentless-test]|**借鉴有界定位—候选—验证流程，暂缓整套接入**。面向 SWE-bench 和特定运行依赖，缺 Ergora owner／权限合同；已有脚本和论文结果不能证明适合结构重构或完整产品交付。|

本轮没有找到可以直接替换项目合同、同时保证架构改进、行为等价和测试价值的成熟“全能重构 Agent”。Aider 是编辑候选生成器，Serena 是工具，PR-Agent 是审查实现，Skill 是操作知识；四者可组合，责任不能互相冒名。

## 3. 编辑、检查和测试价值各用什么

对本项目的 Python 源码，优先复用小而明确的确定性工具，而不是让模型自己宣称迁移成功。以下源码／许可已读，没有安装或运行。

|工具与固定身份|可接的真实 Interface|可以证明的范围与局限|
|---|---|---|
|LibCST：`d9a255843b5cdbecc6834684d233bce1f2987f9d`，动态版本，以提交固定；Python ≥3.9。主体 MIT，部分派生文件另有 PSF／Apache-2.0 声明。[许可][libcst-license]、[元数据][libcst-project]|`libcst.codemod.transform_module`、`CodemodCommand`、`python -m libcst.tool codemod ...`；支持 diff 而非直接应用、成功／失败／跳过与 warnings。[文档][libcst-codemods]|**适配为批量机械编辑器**。保留格式的语法变换适合 import／调用迁移，但语法合法不保证动态行为、持久数据或跨进程协议等价。对本来几行的手改，不先造通用 codemod 框架。|
|Import Linter：`398c1fbbd974d6dc5e2d2fc47e36d6c8a4c5656b`，2.16，Python ≥3.11；BSD-2-Clause。[元数据][imports-project]、[许可][imports-license]|`lint-imports`／`import-linter lint` 读取项目配置；内置 forbidden、layers 等合同，使用真实 import 图、返回退出状态。[CLI][imports-cli]、[forbidden][imports-forbidden]、[layers][imports-layers]|**按需采用架构约束工具**。适合机器可表达的依赖方向；不是 module 深度评分器，不能代替真实调用／所有者分析。动态导入、行为和数据所有权要另核；有现成精确架构测试时不为相同条件重复加一层。|
|mutmut：`6837b3c3ab0cfa4f5488f68adbd1bb26f68b8eb8`，3.8.1，Python ≥3.10；BSD-3-Clause。[元数据][mutmut-project]、[许可][mutmut-license]|`mutmut run`，可按 module／function glob 限定；保存增量结果并提供人工检查／应用 mutant 的工具。[说明][mutmut-readme]、[CLI][mutmut-cli]|**适配为有界测试价值证据**。用存活变异暴露断言缺口；需要 pytest 与 POSIX fork，Windows 需相应 Linux 环境。成本、等价变异、超时／不稳定必须分类；分数不是需求正确性的证明，禁止自动 apply surviving mutant 或按分数删测试。|

分工建议：模型解释改动意图、决定 module/interface 与迁移；Serena/LSP 做定位和有权限的语义编辑，LibCST 做可复查的重复变换；可信 Executor 运行项目既有 build、lint、合同／集成检查并绑定候选；测试价值 reviewer 判断每条断言要防什么真实失败。模型生成的测试、候选和测试报告不能自己提升为可信检查结果。

测试价值审查应给出“需求或失败模式 → 现有断言 → 缺口／重叠 → 最小替代 → 实测成本”。保留有不同故障含义的序列化、持久状态、消息／进程、取消／unknown 与跨版本检查；不要因形状相似就删掉。覆盖率是定位信号；有界 mutation 可以补断言证据；纯文本或低影响可逆修改不默认增加与实现同形的测试。修改真实合同或 native 生命周期时才补针对失败面的检查，不强制每片全套变异与全量测试。

## 4. 一手论文可支持的做法

下表按公开全文方法／实验与限制阅读；未复现论文，不使用其排名或历史价格作当前选型依据。

|论文与阅读范围|可用结论|不能迁移的承诺|
|---|---|---|
|[SWE-agent，2405.15793v3][paper-swe]，§2–5 的 ACI、编辑器／lint、实验与消融|工具 Interface、反馈和编辑失败恢复会影响 Agent 行为；将导航／编辑与即时可检查反馈放到清楚的 seam，往往比只扩提示更有用。|主要任务是 Python issue 修复；拒绝 lint 错误不证明行为保持、并发或持久状态正确。无需为采用这个原则再接一整套 SWE-agent runtime；现有 mini 后端也不能借其论文直接声称等效。|
|[Agentless，2407.01489v2][paper-agentless]，§3 的定位／patch／测试选择、§6–7 数据与威胁|有界定位、多个候选和真实测试反馈是可复用模块，不必让所有阶段变成会话 Agent。|生成复现测试本身可能错误；其回归筛选、复现失败回退和多数排序不是本项目可信策略。数据集偏差、潜在训练污染和任务泛化限制存在；不可让生成器删除项目必要检查。|
|[Meta TestGen-LLM，2402.09171v1][paper-testgen]，§2、§3.2.1、§4–5|将生成与 build、稳定通过、增量覆盖过滤分开，再由工程人员审阅，是可用的工具／审查分工。论文也记录覆盖增加但没有断言的测试被人工拒绝。|未公开两个模型的具体身份，研究场景为 Kotlin 工程／Meta 基础设施；覆盖提升不保证 bug detection。论文为回归增强而丢弃首轮失败测试，这不适合作为通用 bug 修复规则；原始失败要保留分类。|

多 reviewer 仍会共享训练数据、默认假设、遗漏的输入及错误 oracle。不同后端和独立新会话是减少共同盲点的策略，不能证明统计独立；共同 approve 不是 owner 批准或运行通过。现有 [Standards／Spec 两轴的历史对照](2026-11-08-agent-composition.md#3-相关论文及可用结论)也只提供设计证据，不能把聊天偏好研究当代码验收实验。

## 5. Bridge 开发技能只借研究原则

已读取官方索引中五份开发技能，属于当前 `latest` 网页快照，内容摘要保存在私有原件中；不是自主 Agent，也不把整个 Bridge 开发约定导入 Ergora。

|技能|可借鉴|不随参考自动导入|
|---|---|---|
|[Build and Dependency][bridge-build]|固定可再现环境、区分宿主／容器、记录包与源码身份。|NVIDIA 容器、Bridge 的目录／安装命令和硬件依赖。|
|[Bump Dependency][bridge-bump]|依赖 pin 与锁文件协同；小范围验证 API／ABI／行为变化，保留原失败。|任意升级现有 Ergora 依赖、自动操作子模块或沿用上游版本选择。|
|[Testing][bridge-testing]|按风险、代表性、成本与重叠分层；记录功能／硬件范围和不稳定样本。|照搬 L0/L1/L2 名称、GPU 数量或平台覆盖；Ergora 按自己的当前 CI 合同验收。|
|[CI/CD][bridge-cicd]|明确可信触发、精确提交与实际 job 状态，区分排队、执行和成功。|NVIDIA 身份、机器人命令、runner／权限与仓库审批规则。|
|[Review PR][bridge-review]|先读原工件；定范围、按轮核正确性／测试／可维护性；工具检查与人工判断分开。|其仓库专用禁改目录和命令。本文研究任务不执行其中的 review 流程，也不据其默认分工推翻用户授权。|

## 6. 六阶段模板与 refactoring 入口的最小迁移

### 6.1 先改善现有正式消费者，不伪称完成嵌套

发布新的 refactoring preset／任务准备入口，显式声明“行为保持的 module 重构”，输入包括基线、允许路径、行为不变量、拟改变的 interface、迁移／兼容策略和成功证据。内部先生成既有任务定义：小范围治理映射 `repository-governance`，涉及调用方／兼容迁移映射 `large-change`。preset 名称与 `task_type` 分开；不在原冻结模板或 schema 中偷偷增加第三个正式类型。

工作阶段可复用并修订现有 mapper／architecture-test-author／compatibility-validator 等精确定义：定位痛点与真实调用方 → 在批准计划内完成重构 → 交独立兼容验证单元。只在确有前驱数据需求时串行，独立写单元使用原隔离与依赖提交，不并发改同一 checkout。继续满足 WorkDelivery 对 unit／writer 一对一、依赖和写路径的合同。资料与定义改版后，须由内到外发布引用它的新子模板／根版本；旧任务保持原摘要。

六阶段仍是 `inventory → plan → work → integrate → verify → review`：

|阶段|重构任务应新增的具体责任|既有权威保持|
|---|---|---|
|inventory|基线行为、变化热点、实际调用方／序列化与持久协议、测试与依赖地图；每项结论有代码来源。|inspector 不授权迁移；未知行为和缺证据单列。|
|plan|比较至少实际需要的 interface 方案；用 module 深度、locality、deletion test 解释收益，列迁移顺序、失败面与适当检查。|planner 不批准自身计划，原 owner 批准精确计划。|
|work|依批准 scope 做小步候选；确定性批量编辑按需用 LibCST／符号工具；验证单元检查行为／兼容。|原 Executor 控制工作区、Git、test-results；Agent 不改可信规则。|
|integrate|按原依赖整合候选与冲突，核最终 diff 和允许路径。|原 integrate 所有者，不能被“重构专家”取代。|
|verify|对整合后的同一候选运行原必要检查；按改动选有价值的合同／生命周期／跨平台检查。|可信 check-results；原失败与未覆盖平台保持。|
|review|结构 reviewer 核真实 interface／所有者，正确性 reviewer 核需求与失败语义，测试价值 reviewer 核 oracle／成本。|required／advisory 含义保持；独立会话、候选和报告可核；owner 决定不来自票数。|

一份 Agent 可兼具多项专长并在不同模板中担任不同支持的职能；审查尽量选择实际 writer 之外的后端，记录实际 harness／模型而非显示名称。不可用时用户已授权 Codex 回退，可保存明确回退理由后继续，不再重复索取泛化确认；回退不满足“已经跨后端验证”的声明。

### 6.2 首个 D1：一个真正消费六阶段子模板的 native 调用

**建议首个 D1 的真实消费者选 `reference-development`，把一个精确六阶段模板作为结构子节点调用；先支持一条有界串行路径。** 子流程内部仍运行其原 work/review 组合。Forge 的现有 native 所有者用于对照，而不同时扩出任意第三方混合图运行器。下表是待实现的语义合同，不是现存 schema、命令或已通过能力。

|最小 Interface|必要输入／输出|沿用的当前所有者与必须补足之处|
|---|---|---|
|离线准备调用|输入：父 manifest／实例路径／精确子模板 ref、原任务定义与基线、项目 revision、有效 grant、后端选择；输出：不可变调用包和摘要。|复用 WorkflowDefinition 的精确引用、完整树和祖先检查；新增明确的 native 执行描述及消费者。不能以普通 `workflow` ref 解析成功冒充运行支持。|
|启动一次|输入：调用包摘要与原授权；输出：原 task／workflow／run ID 及提交回执，或者明确拒绝／unknown。|复用原 create/start 的意图与幂等／恢复用例、`WorkflowInput` 路由和原 Temporal。若用 Temporal child-workflow，则原启动所有者须唯一，不能同时再走一次独立 start；具体方案在 D1 定稿。|
|观察／收集|输入：原 native ID；输出：来源化的 native phase／outcome、候选提交、原 receipt／evidence 引用与完整性。|原状态/history、candidate、evidence 为权威，父节点只投影；进程退出0或 native terminal 不映射成 adoption。端口消费必须等待规定的真实终态且核同一候选。|
|取消／恢复／对账|输入：原 ID、原意图及必要的显式恢复理由；输出：取消投递与停止确认分别记录，unknown 保持。|原 cancel/reconcile/monitor 负责副作用；父级失败不能只取消本地 await 后假称子进程已停。未知提交／执行禁止自动重提新 run。|

首片可以限制为一个父模板中的一个六阶段 native 子实例，以及有真实消费者需要的串行依赖和结果投影。原 Temporal 承担调度，原提交／审批／证据目录承担记录；控制面仅索引关联，不能建与其竞争的新状态机。静态 preview、单叶 run-input 和 WorkDelivery 保持原语义；无法消费的 native 节点在准入前明确拒绝。多个并行 native 子实例、跨服务远端运行和任意混合角色调度留待真实消费者与预算证据。

父流程若本身已有六阶段，调用内层完整六阶段必须显式选择其隔离工作区和结果整合策略：内层返回候选／证据，外层按自己的批准计划整合并重新 verify；不能让内层在外层当前 checkout 上提交，不能借内层 approve 跳过外层检查。首片可直接拒绝这类共享 workspace 的递归调用；depth／实例／并发和预算沿全部结构祖先约束，不能靠 native 黑盒隐藏子调用。

### 6.3 native 子模板的四个不可省门槛

1. **父资源真实进入每个实际会话。** 冻结全部结构祖先及子模板的 instructions/context/Skill 完整树，保留去重来源、正文与附件可读入口。注入不只覆盖 work/review，还要覆盖原六阶段的 inventory、plan 及 native 内部模型子会话；可信 integrate/verify 读取相应合同。仅把 manifest 路径放入 config、把 Skill 名称列在页面、或上游只给 editor 转发 architect 摘要均不足。预算超限拒绝，不静默截断；执行证据能核实际输入和读取范围。
2. **权限与资源不越任一父级。** 子流程所有实际工具／工作区／网络／子 Agent 都须满足有效上限；声明相交之外还要有实际执行控制。审核只读 scope 不能启动可写 native；native 若不能施加父上限就拒绝该模式。模型传输的配置与任务工具权限分别核，不因换后端扩权；后端不可用／降级明确记录。
3. **原生身份、状态与未知保持。** 固定上游源码／配置与内部模型策略；关联原 native ID、task/run、candidate 和实际子会话，不强改上游内部 teacher/editor/judge 语义。若 native 没有可核状态、取消或恢复，准确暴露不支持范围；不能把 `native_finished` 或模型 judge 变成可信 PASS。
4. **批准与评价仍在原合同。** 子计划需要原规则认可的 owner 回执，父授权不能代替子计划批准；内层评审结果只是相应精确候选的原件。父级接纳还核需求、原必要检查、同一候选与未知状态；不同后端也可能共同误判。

这些门槛也适用于未来 Forge/Aider/Agentless 整体子流程。当前 `kernel.py` 固定了 Forge native 身份和 unknown，但没有证明完整祖先资料实际注入其 teacher/student、全部父权限可施加或 native 子节点可运行，因此暂不能把现成 campaign 接口标为合格嵌套模板。

## 7. D0 决策与依赖顺序

|次序与决策|采用／适配／借鉴／暂缓|出口|
|---|---|---|
|P0 原所有者与合同|**采用**现有六阶段、AgentDefinition／WorkflowDefinition、可信 integrate/verify、候选／owner／unknown 语义。|不新增第二 scheduler／ledger，不改283冻结文件，不搬迁在途运行。|
|P1 专家资料与新入口|**适配** AI Hero 的深 module、两轴审查、故障导向测试价值；发布 refactoring preset，映射既有 task_type。|有可审阅任务例子、精确定义、完整资源和后端／回退说明；只声称现有正式消费者支持的执行范围。|
|P2 首个运行补足|**自建**上述有真实消费者的 native 六阶段调用 seam；只补准备、单次启动、状态／结果和原恢复联动。|用一个嵌套实例验收完整祖先材料、父权限、原 task/run／计划批准／候选、超时／取消／unknown；同时证明旧输入与冻结文件未变。|
|P3 项目需要的工具|**按需接** LibCST、Import Linter；Serena 经实际 MCP／权限适配后选用；mutmut 限定高价值路径与预算。|每项有可重复命令、实际 availability／supported operations、原输出与失败；不要求为简单改动安装整套工具。|
|P4 可替换审查／编辑|**适配** PR-Agent 本地 diff 的建议性输出；**借鉴** Aider architect/editor 与 Agentless 定位／候选选择。|先验完整输入、候选／覆盖／预算／停止与结果规范，再决定是否扩 required reviewer 或 writer 后端；未验前不自动设默认。|
|P5 更大原生流程|**暂缓**整套 Agentless、Aider 多模型原生子流程、任意框架图与大规模并发。|只有实际项目需要、P2 资源／权限／恢复合同满足且独立评价有证据后再接；不因项目有 agent 名称就增加插件层。|

D1 的最小验收应围绕真实失效：同一准备包重试不重复启动；超时后仍可查原 run；子流程不能在父级只读／小 scope 下写；所有祖先材料实际进入每个模型会话；超限完整拒绝；子候选／回执不一致拒绝；取消未确认和 unknown 保持；子流程通过不跳过外层 verify／owner。仅解析新字段、生成静态图或跑合成“approve”不能完成这些验收。研究报告本身不替代该实现片的 fresh-context 独立审查。

## 8. 证据范围

公开仓库 HTML、固定源码／许可、论文 HTML／提取文本、Bridge 五份网页，以及请求清单、字节摘要和失败原件均保存在本片私有研究目录。GitHub API 限流、猜测路径404和不可用的网页工具原样保留，后续以可访问的官方仓库／固定 raw 文件收敛；没有通过认证回避限流。网页 `latest` 是读取日快照，SHA 固定源码是对应身份的证据，两者不混称。

本轮仅做公开来源读取、当前源码核对和本文的格式／本地链接及来源文件身份检查。未安装第三方包，未调用模型／MCP服务器／GPU，未跑测试或CI，未读凭据、外部业务写、修改源码／计划、提交或推送。没有验证任何工具的当前账号权限、隔离强度、质量提升或六阶段 native 嵌套能力。

[aider-version]: https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/__init__.py
[aider-project]: https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/pyproject.toml
[aider-license]: https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/LICENSE.txt
[aider-args]: https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py
[aider-architect]: https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/architect_coder.py
[aider-modes]: https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/usage/modes.md
[pr-readme]: https://github.com/The-PR-Agent/pr-agent/blob/41a7ead86d3ede31d2ec7e54b5a7673a0b9acee5/README.md
[pr-license]: https://github.com/The-PR-Agent/pr-agent/blob/41a7ead86d3ede31d2ec7e54b5a7673a0b9acee5/LICENSE
[pr-project]: https://github.com/The-PR-Agent/pr-agent/blob/41a7ead86d3ede31d2ec7e54b5a7673a0b9acee5/pyproject.toml
[pr-cli]: https://github.com/The-PR-Agent/pr-agent/blob/41a7ead86d3ede31d2ec7e54b5a7673a0b9acee5/pr_agent/cli.py
[pr-registry]: https://github.com/The-PR-Agent/pr-agent/blob/41a7ead86d3ede31d2ec7e54b5a7673a0b9acee5/pr_agent/agent/command_registry.py
[pr-plain]: https://github.com/The-PR-Agent/pr-agent/blob/41a7ead86d3ede31d2ec7e54b5a7673a0b9acee5/pr_agent/git_providers/plain_diff_provider.py
[pr-reviewer]: https://github.com/The-PR-Agent/pr-agent/blob/41a7ead86d3ede31d2ec7e54b5a7673a0b9acee5/pr_agent/commands/pr_reviewer.py
[serena-project]: https://github.com/oraios/serena/blob/6e5c3776d4e67befaab7c290bc29b0279c98d1ed/pyproject.toml
[serena-license]: https://github.com/oraios/serena/blob/6e5c3776d4e67befaab7c290bc29b0279c98d1ed/LICENSE
[serena-symbols]: https://github.com/oraios/serena/blob/6e5c3776d4e67befaab7c290bc29b0279c98d1ed/src/serena/tools/symbol_tools.py
[serena-files]: https://github.com/oraios/serena/blob/6e5c3776d4e67befaab7c290bc29b0279c98d1ed/src/serena/tools/file_tools.py
[hero-readme]: https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/README.md
[hero-license]: https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/LICENSE
[hero-architecture]: https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/improve-codebase-architecture/SKILL.md
[hero-design]: https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/codebase-design/SKILL.md
[hero-review]: https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/code-review/SKILL.md
[agentless-readme]: https://github.com/OpenAutoCoder/Agentless/blob/5ce5888b9f149beaace393957a55ea8ee46c9f71/README.md
[agentless-localize]: https://github.com/OpenAutoCoder/Agentless/blob/5ce5888b9f149beaace393957a55ea8ee46c9f71/agentless/fl/localize.py
[agentless-repair]: https://github.com/OpenAutoCoder/Agentless/blob/5ce5888b9f149beaace393957a55ea8ee46c9f71/agentless/repair/repair.py
[agentless-test]: https://github.com/OpenAutoCoder/Agentless/blob/5ce5888b9f149beaace393957a55ea8ee46c9f71/agentless/test/run_regression_tests.py
[libcst-license]: https://github.com/Instagram/LibCST/blob/d9a255843b5cdbecc6834684d233bce1f2987f9d/LICENSE
[libcst-project]: https://github.com/Instagram/LibCST/blob/d9a255843b5cdbecc6834684d233bce1f2987f9d/pyproject.toml
[libcst-codemods]: https://github.com/Instagram/LibCST/blob/d9a255843b5cdbecc6834684d233bce1f2987f9d/docs/source/codemods.rst
[imports-project]: https://github.com/seddonym/import-linter/blob/398c1fbbd974d6dc5e2d2fc47e36d6c8a4c5656b/pyproject.toml
[imports-license]: https://github.com/seddonym/import-linter/blob/398c1fbbd974d6dc5e2d2fc47e36d6c8a4c5656b/LICENSE
[imports-cli]: https://github.com/seddonym/import-linter/blob/398c1fbbd974d6dc5e2d2fc47e36d6c8a4c5656b/src/importlinter/cli.py
[imports-forbidden]: https://github.com/seddonym/import-linter/blob/398c1fbbd974d6dc5e2d2fc47e36d6c8a4c5656b/src/importlinter/contracts/forbidden.py
[imports-layers]: https://github.com/seddonym/import-linter/blob/398c1fbbd974d6dc5e2d2fc47e36d6c8a4c5656b/src/importlinter/contracts/layers.py
[mutmut-project]: https://github.com/boxed/mutmut/blob/6837b3c3ab0cfa4f5488f68adbd1bb26f68b8eb8/pyproject.toml
[mutmut-license]: https://github.com/boxed/mutmut/blob/6837b3c3ab0cfa4f5488f68adbd1bb26f68b8eb8/LICENSE
[mutmut-readme]: https://github.com/boxed/mutmut/blob/6837b3c3ab0cfa4f5488f68adbd1bb26f68b8eb8/README.rst
[mutmut-cli]: https://github.com/boxed/mutmut/blob/6837b3c3ab0cfa4f5488f68adbd1bb26f68b8eb8/src/mutmut/__main__.py
[paper-swe]: https://arxiv.org/html/2405.15793v3
[paper-agentless]: https://arxiv.org/html/2407.01489v2
[paper-testgen]: https://arxiv.org/html/2402.09171v1
[bridge-build]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/build-and-dependency/SKILL.html
[bridge-bump]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/bump-dependency/SKILL.html
[bridge-testing]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/testing/SKILL.html
[bridge-cicd]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/cicd/SKILL.html
[bridge-review]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/review-pr/SKILL.html
