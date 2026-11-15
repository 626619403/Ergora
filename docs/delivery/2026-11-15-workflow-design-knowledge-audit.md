# WA3：设计讨论、必要知识与人类关卡审计

日期：2026-11-15。源码固定为 detached `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`，开始时工作树 clean。本文是[WA3 审计](../plans/2026-11-15-workflow-evidence-and-human-gates.md)的独立只读结果；仅新增本报告及 ignored 检查原件，没有修改产品、模板、测试、CI、其他工作树或全局 Skill，没有提交、推送或外部业务写入。总计划状态由主控整合，本报告不另改其检查点。

**结论：精确计划批准是真实运行关卡；“详细设计、关键问题反复讨论、必要公司资料补齐后才能实施”还没有完整的机器可核对合同。** 当前可以要求模型写出设计与未知条件，再由 owner 阅读并批准精确计划；不能从这次批准、资源全文读取、独立 reviewer 的 approve，或训练候选 release，推出所有关键问题已经回答。应扩展原计划、收据和恢复所有者，先与用户确定必要的产品选择，再实施；不需要另造批准系统或第二调度器，也不应对已经授权的日常开发重新逐操作询问。

本文以“观察”标明直接读到的当前实现，以“历史证据”标明已有交付记载，以“推论”标明从调用关系得出的能力边界，以“建议”标明尚未决定、尚未实施的方案。WA1 负责外部调研采用矩阵，WA2 负责调度、循环和非 Agent 节点全链，本报告只在设计及知识关卡所需处引用其相关 owner。

## 1. 固定来源与定义身份

以下源码链接全部以本报告开头的固定提交为核查基线；版本号不是运行成功或人类已经讨论的证据。

|来源|本次直接核对的内容|
|---|---|
|[六阶段 Workflow](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/workflow.py)、[FileAdapter](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/adapter.py)|`DevelopmentWorkflow.run/approval/approve_plan/request_cancel`，以及 `FileAdapter.authorize/verify_receipt`|
|[组合 Workflow](../../src/ergora/reference_workflows.py)、[实际 Executor](../../src/ergora/reference_executor.py)、[冻结 Executor](../../src/ergora/data/reference/platform/local/agent_platform/executor.py)|原六阶段继承、准备产物传递、模型结果合同、可信命令和批准复核；已读至 `SelectedContextWorkflow` 的 envelope v11，未把早期版本当当前上限|
|[计划读取与批准](../../src/ergora/reference_task_approval.py)、[正式用例](../../src/ergora/tasks.py)、[HTTP](../../src/ergora/web.py)、[批准页面](../../src/ergora/data/console/tasks.js)|完整材料读取、exact run/plan、确认、意图／attempt／回执、unknown 恢复及当前公开操作|
|[模型结果](../../src/ergora/agents.py)、[large-change profile](../../src/ergora/data/reference/platform/upstream/platform/task-types/large-change/profile.json)、[输入 schema](../../src/ergora/data/reference/platform/upstream/platform/task-types/large-change/input.schema.json)|计划产物的真实结构、acceptance 字段及 `knowledge` 等可信检查的意义|
|[静态定义 schema v2](../../src/ergora/data/schemas/workflow-definition-v2.json)、[定义编译](../../src/ergora/workflow_definitions.py)、[任务资料选择](../../src/ergora/task_context.py)、[冻结 context 校验](../../src/ergora/task_envelopes.py)|资源来源／修订／摘要、完整祖先继承、权限上限；没有由资源或 Skill 自动产生的新授权|
|[大型变更说明](../../src/ergora/data/reference/platform/templates/large-change/instructions.md)、[准备叶说明](../../src/ergora/data/presets/agents/ergora-development-preparer/instructions.md)、[重构根说明](../../src/ergora/data/presets/workflows/ergora-refactoring-template/instructions.md)|已有调研、设计、兼容、迁移、回滚及未决条件的提示要求|
|[训练 proposal v3](../../src/ergora/data/presets/workflows/ergora-training-proposal-v3/instructions.md)、[完整根 Skill](../../src/ergora/data/presets/workflows/ergora-training-proposal-v3/skills/ergora-bottleneck-optimization/SKILL.md)、[设计叶 Skill](../../src/ergora/data/presets/agents/ergora-experiment-designer-v2/skills/ergora-experiment-designer/SKILL.md)|固定工作负载／质量合同、缺信息、证据请求与执行／采用边界|
|[训练 release 桥](../../src/ergora/reference_training_release.py)、[原训练 Workflow](../../src/ergora/data/reference/platform/upstream/temporal/perf_temporal/workflow.py)、[原训练 adapter](../../src/ergora/data/reference/platform/local/agent_platform/training.py)|候选 evidence 批准与设计确认的差别|

使用原 `asset_trees.digest_tree` 重新核出的完整包身份如下；不是仅 hash 一份说明文档。

|定义|完整包 digest|
|---|---|
|`ergora-development-preparation@1.0.0`|`3006fcc8b7b93a018952ebe7921514d5cd604434670c2d36caae90e598fc4acd`|
|`ergora-development-preparer@1.0.0`|`c8527fd7dfd8ec9549e285412f907406a880097663412066d664900778f295d3`|
|`ergora-refactoring-template@1.0.0`|`ce26192b22c25031156755290c252823dbd845c199ff7f62f8e874e07076a15d`|
|`ergora-refactoring-template@1.1.0`|`79376039d7794e228c4f4e57e42383927460c26da0948781b9f7d4cc4a62b48e`|
|`ergora-refactoring-delivery@1.0.0`|`8bc02f70dc320aff86736235446b94a0f4065bb63d243a382906be69e947822d`|
|`ergora-training-proposal@3.0.0`|`7532009200221f23d70474e5882c447df4fc65350fd94bed6e79d0566153dd79`|
|`ergora-experiment-designer@2.0.0`|`cd88d273d84b35d1a93c6a537897ba0d8d58a1e9a69ed9a26d2ab0b970de10c3`|

## 2. 已覆盖的真实行为与仅提示部分

|要求|观察与实际消费者|判定及缺口|
|---|---|---|
|实施前盘点与计划|原 `DevelopmentWorkflow.run` 依次完成 inventory、plan，再 `await approval()`，之后才 `units()`；组合 Workflow 继承此路径。`reference_executor._preparation_results` 核同一原 inventory 的 job、receipt、candidate、调用身份及完整产物，再交 plan。|**真实顺序与材料关卡**，不是静态 DAG 图上画六个节点。尚无可声明的独立 research／design-discussion 阶段。|
|详细修改方案、边界、顺序和回滚|大型变更 planner 要求行为／消费者／持久化／部署依赖、兼容合同、验收证据、DAG、共享文件 owner、迁移与回滚；preparer 和重构根要求真实 caller、baseline、保持行为及未知项。|**已采用的操作知识／提示约定**。计划目前强制 `execution-plan`、`ownership-map`、`rollback-plan` 三个非空字符串，没有逐项验证设计内容完整的 typed 对象。|
|工程风格与模块选择|重构根 1.1.0 实际增加[仓库质量 Skill](../../src/ergora/data/presets/workflows/ergora-refactoring-template-v1.1/skills/ergora-codebase-quality/SKILL.md)，链接仓库规范、实际 caller／owner、测试接缝；随包 [catalog](../../src/ergora/data/presets/presets.json) 通过 `refactoring-quality` 选择它。|**随包的版本化资料**，比只留研究报告更进一步；它没有自动把争议风格选择交由人类决定的状态机。运行前应选择精确版本，不能把旧 1.0.0 旅程算成 1.1.0 行为验收。|
|客观验收与可信测试|`input.acceptance` 是非空字符串数组；profile 要求 `behavior/architecture/knowledge/integration/compatibility/migration-rollback` 等。冻结 Executor `commands` 为各检查寻找受信任项目 argv，缺命令会失败，同命令只执行一次；baseline、work、verify 的实际退出码可阻断。|**可信检查执行是真关卡**；但 acceptance 文本没有 requirement→oracle／阈值→检查／证据的强制映射。检查名 `knowledge` 不等于“必要公司知识已补齐”，其能力取决于该项目真正配置的命令。|
|人类审阅精确计划|`reference_task_approval._plan` 在同一原 run 的 pending plan 上核 history、job、receipt SHA 和每项要求的完整文本字节；页面 `approvalDialog` 取得材料后才显示批准入口。|**存在完整可审材料路径**。CLI/API `approve` 不要求已保存的“读取／讨论完成”证据；网页取到文本也不证明人的理解。|
|批准前禁止实施|原 `approval()` 真实等待 owner receipt；`approve_plan` 拒绝错误 phase／request／plan／复用 receipt。`FileAdapter.authorize` 核 human、owner/maintainer、expiry、revoked=false；后续 Executor 又核批准摘要和撤回状态。|**真实精确批准关卡**，应保留。它验证的是对这个计划 receipt 的批准，不验证有哪些问题、谁回答、答案是否完整或内部约束是否已经提供。|
|反复讨论与逐轮决定|大型变更说明要求 versioned execution plan、暴露 unresolved decisions，合同变化时停止并请求 revised plan。|**提示约定**。当前 plan 模型一次生成后等待 approve；没有 question/answer/decision event、设计修订轮次、逐问题负责人、待决清单或 revise-and-reapprove 消费者。|
|缺必要资料时请求开发者|preparer 要明确未知；experiment-designer 要缺失先决条件、固定质量合同及 evidence request。训练提案根要求保留 insufficient/unknown。|**能提示和写缺口**，但没有统一“必要资料缺失→等待提问→答复绑定→恢复原关卡”合同。公司文档、人的设想、会议决定、权限不足及冲突来源未被一等建模。|
|已有资料的可靠引用|`task_context._sources` 核显式所选 memory revision、当前 validity 与 adopted Skill digest/revision；首次 intent 前复核，冻结来源随完整根装配。|**已有来源身份与准入关卡**。它只验证“选中的资料”，不能保证“决策必需资料已经选齐”，也不替人裁定哪份会议决定更权威。|
|训练优化前的设计|proposal v3 固定 flow→analysis→kernel assessment→measurement 的方法；设计叶给出工作负载、目标、质量 oracle、允许变化、预算、配对测量、交互和回退要求。[工作负载卡](../../src/ergora/data/reference/platform/templates/training-optimization/workload-contract.md)也包含资源授权与发布 owner。|**具体提案方法已进入完整 Skill**；该根明确是只读静态提案，操作者显式供给前驱，不是自动实验或人类设计讨论执行器。|
|训练候选采用|原训练 Workflow 先 trusted gate，之后 `AWAITING_RELEASE`；adapter 复核 binding、evidence、当前 gate、baseline、owner receipt、expiry／revocation／fence，再写 `automatic_merge:false` 的集成复验票据。|**真实候选 release 关卡**，时点在实验 gate 后。它不是实施前的设计确认，不能填补前述问答缺口，也不授权 merge／部署。|

这些边界与[当前架构](../architecture/current.md)、[组合 ADR](../architecture/decisions/0005-composable-workflows.md)一致：原 Temporal 六阶段保持执行事实；静态 WorkflowDefinition v2 只有 Agent／Workflow ref 和 all-join，没有可配置的通用 human／question 节点。没有使用 LangGraph 来实现本审计所需的人类讨论。

### 可达的最小结构反例

本次离线抽取当前 `agents.result_schema`，用 profile 的三个 plan 名称生成真实 schema，再用实际 `jsonschema.Draft202012Validator` 验证如下结果：**结构通过**。

```json
{
  "summary": "Open design questions remain.",
  "artifacts": {
    "execution-plan": "BLOCKED: Q1 is unanswered; the internal meeting decision is unavailable.",
    "ownership-map": "TBD: awaiting owner answer.",
    "rollback-plan": "TBD: awaiting required internal material."
  }
}
```

观察：schema 只要求非空字符串。沿 `reference_executor.model`，结果通过结构验证后按原 artifact 发布，plan 本身没有依据这些正文建立必答事项清单。推论：不能把结构成功解释为讨论闭合；目前要靠人工阅读后拒绝批准。**这里没有运行模型、启动任务、发出批准或证明真实工作流被绕过**；人类批准关卡依然存在。本反例只把“语义未闭合可表现为结构合法计划”变为可复核事实。

## 3. 拒绝、失联、撤回、变更和恢复

|情形|当前事实|与本次需求的差距|
|---|---|---|
|人明确拒绝设计／要求修改|公开 task 用例、CLI 和 HTTP 提供 approve/status/resume-approve 及独立 cancel；原 `approve_plan` 只接批准。授权器的 `ApprovalRejected` 是不合规收据被拒绝，reviewer 的 request-changes 是另一阶段意见。|缺带理由、问题与精确设计版本的人类 reject／request-revision 事件；不能把“无批准”或“收据拒绝”冒称已保存产品反对意见。|
|不答、离线、关闭页面|`approval()` 固定原 deadline 等待，超时 `StopWork("Human plan approval expired")`；随后 fencing，按确认结果为 BLOCKED／CANCEL_UNCONFIRMED／NEEDS_RECONCILIATION。关闭页面不会撤销操作。|**沉默不会批准**已覆盖；但没有讨论轮次／提醒／等待答复对象，也没有“保留同一设计待用户继续”与“终止并重建”的专门产品选择。|
|错版本或旧批准|pending request／plan receipt digest 必须相等；同 decision ID 不可改计划，不自动续期。过期 prepared intent 要重新审阅并显式新决定；attempt 后只核原 run 的精确信号。|**旧 SHA 不能批准新 SHA**已覆盖。缺从旧设计修订到新设计的关联、各决定受何修改影响、哪些题目需重答的机制。|
|撤回已批准决定|授权器要求 revoked=false；冻结 Executor 在 work/integrate/verify/review 初始化再读原收据，摘要变化或 revoked 可阻断后继准入。|不能说“完全没有撤回校验”。但当前公开入口没有 append-only withdrawal／revoke 操作；已开始的 stage 不因讨论中的撤回文本立即停止。撤回与取消/fence应如何接合仍需具体设计，不能靠直接改旧收据制造历史。|
|实施中重要合同改变|大型变更说明要求停受影响工作并请求 revised plan；批准材料按摘要固定，原任务和根 manifest 不随活动库更新。|没有机器定义的“重大变更”字段集或可运行的修订／批准失效流程。仅在外部新文件出现变化，不会自动成为已批准计划的新事实。|
|公司资料缺失或访问被拒|编译会拒绝不可读的已声明祖先资源；task_context 拒绝被选中资料的漂移／过期；训练设计叶会被提示报告 missing prerequisite。|没有 `required_source`、denied／conflicting／stale 状态和补齐责任；未声明所需资料不会仅凭 schema 自动阻断。缺权限应保留缺口并向开发者要授权内材料，不能擅自扩访问范围。|
|批准信号丢应答／重启|`_Approval` 有稳定 decision ID、不可变 intent、receipt、attempt、result；attempt 前显式恢复重核原 phase／SHA／owner／expiry，attempt 后只匹配原 history 完整 payload，不补发。`requested` 明确不是批准采纳／执行成功。|**副作用恢复已有可靠 owner**。新设计／问答合同应接在此处，不能另加“讨论已完成”的第二权威或在恢复时重新摘要当前文件替换原批准材料。|

身份边界也必须保留：[原 adapter 声明](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/adapter.py)明确文件 ACL 才是权限权威，JSON identity 本身不是认证；`reference_task_approval.actor()` 使用操作者 Unix 身份，`confirm:true` 是显式调用参数。它们能记录被授权操作者的批准事实，不能单凭 `principal_type:human` 证明某个具体自然人读过文档或亲自答完问题。未来若需要多人／组织身份，须明确可信输入渠道和角色来源，不能从 Agent 填的一段文字生成可信人类决定。

## 4. 实际运行与决定记录能证明什么

本次直接读取以下固定公开记录及投影，没有重跑其模型、训练或私有历史。它们保留当时版本；与当前源码一致的机制是来源核查，不能代替当前完整运行验收。

|历史证据|已覆盖|本报告不由它推出的结论|
|---|---|---|
|[F3 精确批准交付](2026-11-03-task-approval.md)及[原设计](2026-11-03-task-decisions.md)|固定 run／plan、decision ID、24h expiry、意图／attempt／signal 原件；原 fixture 包含旧 plan、过期、revoked、phase 竞争及 unknown 恢复；记录明确区分受控 SDK 与真实服务。|这是批准与恢复合同，不是关键设计问答产品。原 expired/revoked 收据负例不等于有公开撤回操作或设计修订流程。|
|[治理六阶段真实旅程](2026-11-13-six-stage-native-journey.md)及[公开投影](evidence/2026-11-13-six-stage-native-journey.json)|真实 CLI 计划读取／精确 owner 批准、7 模型会话、9 job、REVIEW_READY、同 ID／history 重放与交接恢复。该旅程未在 v10 注入到期／取消故障，文档明确保留此限制。|不能把完整资源读取当作讨论／理解，不能把 REVIEW_READY 当作 merge，也不能替新讨论状态验证拒绝／失联／撤回。|
|[重构第三轮](2026-11-13-refactoring-journey.md)及[投影](evidence/2026-11-13-refactoring-journey-r3.json)|`ergora-refactoring-template@1.0.0` 的真实串行 rewrite→compatibility；run `01a1d3ba-600c-7c5f-b4e2-0e52c156d305`，owner 读取后批准 plan `113e5cd337aedb013237fa3d5634478e1dcb098298bce5b031050d9a07d4a9e1`，候选 `63004b35f123e0efa49f3746627247d9036d1de8`；投影索引保留 owner-plan-assessment 与 owner-approve 原件 SHA。前两轮 BLOCKED／TERMINATED、收尾与预算身份保持。|本次只读到公开原件索引，没有重读私有 owner assessment 全文。公开投影不含逐轮人类问题／答案／选择，也未宣称这些存在；不能据“owner assessment”文件名推定已实现讨论协议。|
|[瓶颈提案 v3 交付](2026-11-15-training-bottleneck-path.md)|两个任务共十次真实只读调用；完整前驱由操作者提供；kernel 可选择无需修改；两 measurement 均 request-changes 保留缺候选、正确性和成对测量证据。|这是方法进入 Skill 后的真实提案使用，不能当作实验 gate、人类设计批准、自动循环或 GPU 收益。request-changes 是模型意见，不是人类拒绝事件。|
|[训练控制旅程](2026-11-14-training-control-journey.md)及[投影](evidence/2026-11-14-training-control-journey.json)|已有 evidence 观察、精确 owner release、恢复和集成票据路径；记录注明部分证据／attestation 为 synthetic。|不能借 synthetic 候选证明真实训练有效，更不能由候选 release 推出实验前的人类设计讨论已闭合。|

[重构研究 R10](../research/2026-11-12-refactoring-workflow-agents.md)曾提出沿既有六阶段、caller／Interface／迁移／rollback 与原批准 owner 适配；这些要求确实进入了重构根、准备者及质量 Skill。本文没有重新开展市场调研或新读上游网页；更广泛的一手来源→方法→消费者采用矩阵归 WA1，外部文章中的完整“人类决定方向”不能仅凭引用就计作当前运行能力。

## 5. 最小 typed 合同建议，尚待用户决定

建议先把已有计划的可审材料补齐为一个版本化包，再由原批准 owner 引用其摘要。以下是领域数据职责，不是已存在 API、schema 名称或已经批准的新产品决定。

|对象|最小必需字段与用途|优先复用的 owner|
|---|---|---|
|设计包 `DesignPacket`|设计 ID／revision／前版摘要；原 task/request/profile、baseline、精确 manifest；研究来源及适用范围；问题／方案／取舍；明确方向、非目标、风格规范与证据；Interface／持久格式／迁移／回滚；工作单元／顺序；验收合同；批准材料摘要。报告 Markdown/HTML 与机器对象绑定同一摘要。|现有 plan artifacts、不可变定义与 task envelope；不改旧 frozen profile 的含义，新增显式版本。|
|必要资料 `KnowledgeRequirement`|稳定 ID；缺什么及阻止哪项决定／验收；必要性来自哪条用户要求／规范／已记录决定；请求对象；授权内来源引用；提供者、来源版本／时间、内容摘要；`missing / supplied / denied / conflicting / stale` 等互斥状态及关联答复。|现有 resources／memory source/revision／task_context；新字段只表达决策依赖，不授检索权限。|
|问题与逐轮答复 `Question`／`Response`|问题 ID、所针对设计摘要、问题正文、依据／缺口、可比较选项及代价、必答依据／决策人、影响范围；每轮原答复的 actor／时间／内容摘要、引用来源、选择与理由、替代哪条旧答复、未决项。明确拒答和请求补资料，保留原文。|原计划材料与追加记录；不要把聊天摘要覆盖成唯一历史，也不要把模型代拟答案当作 human event。|
|决定 `DesignDecision`|稳定 decision ID、精确设计包／问题集／验收摘要、可信 actor／role、`approve / request-revision / reject / withdraw`、原因、已解决与未决 ID、授权 scope、有效条件及 supersedes。与原 intent／attempt／result 关联，投递与被采纳分开。|原 `reference_task_approval`、授权 adapter、固定 run history；批准的继续权仍由原 Workflow 持有。|
|验收项 `AcceptanceCriterion`|稳定 requirement／check ID；输入与环境身份；可执行的 oracle／算法版本、比较方式和数值阈值或确定性预期；受信任 check 引用、证据格式／身份；权限／预算／取消 owner。不能机器裁定的方向／风格选择明确引用人类决定。|原项目 checks／profile、Executor 和候选证据；不要让设计模型自改 oracle、阈值或可信 runner。|

最小执行顺序建议是“授权内资料盘点→设计包与待答事项→反复答复／修订→机器核对就绪条件→原精确计划批准→原 work／verify／review”。机器能客观核对的是**声明的必答项已经有对应有效决定、必要资料有可校验来源、批准引用同一材料**；它不能保证模型识别了公司里所有未说出的事实，更不能自动判断人的设想已经被理解。未识别缺口仍需人类与独立评审承担。

就绪判定应返回精确缺项列表，至少要求引用身份一致、声明必答事项无未决、必要资料符合已选时效／权限策略、验收项均可映射至可信检查或明确人类决定。对可暂缓的问题，必须由有权决策人明确接受带边界的假设并形成版本化决定；“没有答复”不能被转换为接受。谁能标记必答／可暂缓以及允许哪些假设，是下节待决产品问题，不应由实现 Agent 自行选定。

批准失效应采用可计算规则，例如对已声明的 baseline、Interface／持久格式、目标／oracle／阈值、必要资料、权限／预算、工作拆分／顺序等材料计算批准摘要；其中任一被改变则新摘要没有旧批准。哪些字段属于此集合、纯展示编辑是否排除需用户选择。避免让 Agent 凭主观判断一句“不是重大变更”延续旧授权。恢复必须沿已存摘要与原决定，不临时读活动 head 重建成新的批准对象。

授权边界仍是本次用户要求：读取 Skill、继承祖先上下文、收到会议资料或下游结果都不扩大路径／shell／network／资源权限。已有授权内的调研、只读操作和可逆日常开发继续进行；关卡只控制本次新设计的进入实施，以及以后经明确规则认定失效的受影响工作。

## 6. 未来实施的客观验收，不在本审计新增测试

下表是 WA4 方案应纳入的可操作行为验收，需在方案确认后由相应 owner 的现有测试入口验证；不能只做 schema 解析或 prompt 文字断言。

|场景|可观察的通过标准|
|---|---|
|关键问题未答／必要公司资料缺失|提交一份结构合法设计，保留某声明必答项或必要来源为 missing；批准／工作投递被拒绝，返回精确 ID、缺少内容和恢复入口；既有工作／信号计数不增加。|
|补资料与反复讨论|连续两轮问题／原答复／设计修订均可离线读回；第二轮明确引用第一轮和新来源；只解决一个问题时其他未决仍阻断；不能因写出“已讨论”文本通过。|
|来源权限／时效／冲突|denied、摘要变化、已声明失效来源、相互冲突的必要资料分别保留原状态；不发额外授权请求或擅自联网；仅有权人的明确冲突处理或补齐合格来源后就绪。|
|人拒绝／要求修改／拒答／不答|每类事件可区分、绑定同一设计版本并保留原因；后继未投递。不答到期依据确认的策略进入等待或停止，始终不产生 approve。|
|设计变更后的批准失效|对批准材料字段集逐项改变 baseline、接口、oracle／阈值、必要资料、权限和工作顺序；旧决定无法启用新材料。已确认不影响批准的展示编辑按明确规则处理，不靠 Agent 文本判定“重大”。|
|批准／撤回与并发|绑定旧版本的迟到批准不能覆盖新版本；若撤回先被接受，受影响后继不启动；若实际副作用已经发生，记录原事实并走原取消／fence，不能把 UI 的撤回成功等同进程已停。|
|崩溃、重复与恢复|问题、答复、决定写前后及批准 attempt 前后中断；原 IDs、材料摘要、期限和记录不变。unknown 只核原 history，不重发、不刷新预算或生成新批准者；并发决定不形成两个继续权。|
|可核对验收|每个 requirement 有检查／人类决定引用；固定输入的失败、unknown、缺原件或错候选不能被模型 verdict 转成 pass；可信检查在原 owner 执行，原日志／退出码／数值与最终候选相符。|
|不增加无关确认|已批准设计与原授权 scope 内的重复只读、恢复、检查及可逆工作沿原用例继续；仅新设计／批准材料变更触发相应设计决定，不逐工具调用弹确认。|

最小接续片建议：先在 WA4 固定上述范围和字段／状态选择；再用新版本设计材料及就绪验证接原 plan owner；随后接问题／决定／撤回的追加记录与原停止／恢复；最后补 CLI／网页完整呈现和真实小型旅程。任意图的人类节点与通用 Hook 是 WA2 的另一个范围，不应成为本次最小设计闭环的隐含依赖。以上顺序是建议，不等于用户已选定的新产品方向。

## 7. 需要与用户讨论的少数产品选择

原需求已经确定“实施前讨论清楚、缺必要知识要问、不答不算批准”，无需再次询问是否需要这些原则。剩余选择应由主控在具体方案／示例齐备后提出：

|待决事项|可比较选项与取舍|
|---|---|
|第一片覆盖范围与关卡位置|A：先增强框架开发／重构的原 plan 关卡，原 owner 与生命周期最少变化；B：同时为训练优化增加独立实验前设计批准，覆盖更广，但需另固定 proposal→原实验准备的接缝及预算／权限含义。两者都保留原候选 release。|
|必答项与可暂缓假设由谁确定|A：项目／模板显式 policy 加任务 owner 选择，机器易核且可维护；B：所有提出的问题都要明确处理，遗漏更显眼但会增加低价值问答。必要资料访问被拒时是否允许缩小范围另立设计，必须是人的决定。|
|批准失效绑定范围|A：完整 typed 设计材料任一变化都重批，规则简单但小改也可能触发；B：人先确认批准材料字段集，纯展示修改可排除，减少打断但增加字段分类／迁移责任。都不采用 Agent 主观评估“重大”。|
|决策人与拒绝／撤回／失联策略|A：沿现有单 owner，拒绝／撤回接原 cancel/fence、到期保持原停止语义，接线最少；B：允许按议题指定多位决策人、讨论停放与恢复，需要明确冲突规则、等待期限／预算和谁有继续权。都须保留已授权日常工作的边界，不能将失联转为默许。|

这些选择不由本报告代答。公司资料应检索哪些已授权来源、哪些必须请开发者提供，可作为具体设计示例中的资料清单一起确认，而不是先要求访问所有公司系统。

## 8. 本次检查、限制与交接

实际检查：核 full HEAD／detached／初始 clean、最近提交；阅读适用 AGENTS、总计划与 WA 计划、相关架构及 maintainable-project-delivery／ergora-codebase-quality／writing-for-agents；沿上述源码与模板静态追踪；用原资产身份算法重算七包；完成一次 plan schema 的离线结构反例；检查本报告链接／引用与完整改动范围。ignored 原件登记在本工作树 `.ergora/checks/workflow-design-knowledge-audit/`，其中 `audit-observations.json` 含源码基线、原始反例／schema 与逐文件包摘要；公开报告不包含凭据或本机绝对路径。

没有运行模型、Temporal、训练／GPU、完整工作流或产品测试，没有新增测试／CI或安装依赖；没有查询组织资料系统，不能声称当前用户拥有其权限。未重读历史私有 owner assessment／history 原件，历史结论仅按本报告明列的公开记录范围引用。静态反例不证明真实批准被绕过，schema／摘要通过不证明设计质量或人的理解。

本片是独立审计及报告，不对新产品行为作验收通过；审计／状态文档按既有规则不触发递归的“审查审查”。下一责任为 WA4：合并 WA1 来源采用矩阵、WA2 实际执行／停止边界和本报告，形成可审方案与明确问题，记录用户的真实决定和设计版本后再进入 WA5。
