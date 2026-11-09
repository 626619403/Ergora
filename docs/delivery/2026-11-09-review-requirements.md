# AC4.2a：版本化审查职责声明

日期：2026-11-09。基线 `f9f4fc01546aa065f2fe32294a28c31387b2cf56`。状态：静态实现、最终包、公开 CLI、自身模板及[新独立两轴审查](2026-11-09-review-requirements-review.md)通过；23文件普通提交 `5580c8ca154af3b58bd546315f0ec4812bd5c4b3`、自己的双OS CI42566831850七必要步骤及独立05:37:09.274699 UTC明确HTTPS远端同SHA均通过。上一片 [AC4.1](2026-11-09-parallel-reviews.md) 已精确终结，不以本片替代。

## 可验收范围

把 `required`／`advisory` 放在工作流对审查 Agent 的**实例引用**上，同一专家定义可在不同模板中承担不同的审查职责，不修改 AgentDefinition 的含义。新增独立的 WorkflowDefinition v2；v1 文件、摘要和预览原字节保持，不给历史模板补字段。v2 的 reviewer 节点必须显式声明 `review_requirement`，其他角色、子工作流引用和 join 不接受该字段。子工作流内部决定每个叶子的职责；改变职责需要保存新的定义版本并更新父引用，不修改在途 manifest。

静态预览在对应叶子保留声明；一旦任何被引用定义为 v2，预览使用版本 2，以免旧执行器把建议成员当作旧必需合同。原定义库、完整树校验、引用摘要、权限/资源/容量解析、导入/导出、备份及固定输入包继续由现有所有者处理；不新建定义库、解析器或数据账本。共享包检查在读取已核 SHA 的 JSON 后选择支持的 schema，Agent v1 和 Workflow v1/v2 使用同一校验入口。

本片只交付定义及其静态消费者。现有正式运行仍限预览 v1，新的 v2 图在正式任务准入和运行形状检查处明确拒绝；不能在这一片宣称建议审查已执行或让旧 envelope 静默降级。AC4.2b 再接独立版本的正式请求、可信审查意见判定、汇合和实际旅程。

## 后续运行合同

建议审查的 `request-changes` 是保留原意见的业务结果，和进程失败、合同破坏、候选不符、证据缺失、会话复用、超时或未确认清理不同。后者继续阻塞并走原 stop/fence/reconcile；不得捕获旧 `StopWork` 后清空全局取消，不把 FAILED/CANCELLED 改成 SUCCEEDED，不解析错误字符串来推定模型意见。原六阶段、精确候选、owner 批准、attempt-before-send 与历史重放保持。

AC4.2b 必须从原可信执行器的结构化模型结果产生可核意见原件，并在原活动所有者核身份/候选/完整产物及会话后消费。建议意见不能成为正式 approve；汇合引用全部必需与建议原收据、保留 findings，且至少有一名必需审查者。各成员仍使用原作业、worktree、monitor、预算和取消所有者，不建第二调度器。

## 实施与证据计划

- 修改现有 `contracts`、`definition_bundles`、`agent_definitions`、`workflow_definitions` 的版本选择与叶子投影，以及 `tasks`／`task_envelopes` 的明确不支持出口；新增一个自包含 v2 JSON Schema，不改 283 个冻结文件。
- 回归覆盖同一 Agent 的两种实例职责、显式字段/版本拒绝、嵌套与重复引用、v1 原预览身份、新包完整冻结/源定义删除后读取与备份恢复，以及正式准入无副作用拒绝。复用既有 fixture 和套件，不建立新 CI 作业。
- 非 editable wheel 核源/wheel/安装身份和冻结身份，运行有针对性的原定义/任务/架构检查；静态核公开手册及命令。静态定义改动不启动无消费者的完整 Temporal 旅程。
- 完整切片使用 Ergora 自身结构审查模板，并交 fresh-context 独立审查者核需求、结构、冗余校验和性能。实现、各次验证、模型审查、独立审查、普通提交/推送及本提交必要 CI 分开记事实。

下一步：完成本片静态版本合同后实施 AC4.2b。串行端口、写执行者分配、三领域默认组合和页面继续按 [AC 计划](../plans/2026-11-08-agent-composition.md) 推进。

## 当前实现与验证

已在原完整树检查中按被核过 SHA 的 JSON 选择 Agent v1／Workflow v1/v2 schema；未知、布尔或非对象版本明确拒绝。库索引继续使用原身份字段，不改储存格式。原编译器只为 v2 reviewer 节点投影 `review_requirement`，递归遇到 v2 即输出预览 v2；全 v1 图不插字段。新增 `review-requirements` 静态示例并同步工作流手册。正式任务准入和原生形状检查各守自己的外部输入出口，均拒绝预览 v2，避免未实现的建议成员进入旧运行。

首轮源码执行 `tests/test_workflow_definitions.py`、`tests/test_agent_definitions.py`、`tests/test_composition_tasks.py` 与 `tests/test_architecture_boundaries.py`：**191 passed / 1 skipped / 66.53 秒**。该轮发生在静态示例断言及测试清单读取整理之前；六个生产模块随后未变，不把它当作最终测试文件的运行。已覆盖同一 Agent 的必需/建议实例、新旧定义共存、嵌套重复引用、完整包、删除原库后读取、离线备份恢复、七种非法声明，以及正式运行明确拒绝；真实独立叶子调用及建议聚合未在本轮执行。

非 editable wheel 构建/安装成功，SHA `f6c6dc4733185a485847138c96176064e9b82f61d3486bfadcf1b942698fd801`；**370 份源/wheel/安装文件相同，283 冻结保持**。新隔离安装包用 `python -I` 执行上述四组最终测试，**191 passed / 1 skipped / 148.54 秒**；跳过项要求真实 Windows junction，未据此宣称本机 Windows 原生通过。没有新增 CI 作业。

[原包身份与最终检查](evidence/2026-11-09-ac4-requirements-package.json)保留完整相对文件 SHA 与检查日志；[公开 CLI 原观察](evidence/2026-11-09-ac4-requirements-cli.json)保留各操作原输出摘要和新旧预览比较，没有发布私有验收目录。

实际安装后 CLI 完成 **11 个静态操作**：两份 Agent 导入、新示例 check/import/preview、prepare-manifest/verify-manifest、从完整包准备/核验输入，以及旧 v1 示例导入/预览。固定输入保持 `execution_authorized: false`。另直接调用上一片实际安装的旧编译器，同一库的 v1 预览与本片逐项/摘要完全相同；旧读取器明确拒绝新 v2 manifest。此处验证静态消费者，不是正式 Temporal 或建议业务运行。当前静态核 **8 份 Markdown / 137 本地链接与锚点 / 79 条公开命令 parser** 均通过；文档继续收口时再核新增引用。

## 自身模板真实审查

通过最终安装包的 `structure-review` 与 task MCP 实际调用 Codex `gpt-6.1-sol`／high，run `c76a609598184cb0a58b34156490208e`，**129.315 秒 / succeeded / exit 0 / approve**。[精确输入身份](evidence/2026-11-09-ac4-requirements-self-review-identity.json)及[原模型结果](evidence/2026-11-09-ac4-requirements-self-review-result.json)保持。附件包含16份完整源码/schema/测试/相邻所有者与基线 tracked diff，249,350 字节，SHA `6fc61ab5bcab0451541a1269bd714727632369d65db8a086515bd6e2750185cf`；实际读取分页及原调用身份由新独立者另核。原定义库在调用前移除，固定完整包仍能读取。

模型在 Spec／Standards 两轴未提出 finding。它明确没有执行测试，没有收到全部 native 调用者、CI 或包装配置，也未独立核283冻结；原结果中的这些限制保持，不把它当作实际包/CLI验收或独立仓库审查的替代。Claude不可用时使用用户已授权的Codex/ChatGPT回退，不声称模型错误独立、OS隔离或正式审批。

## 独立本地出口

Fresh-context 评审者在完整源码/相邻消费者上独立判定 Spec／Standards 通过，无成立 finding。自行构造13实例/7叶混合树，验证 v1 根两次引用 v2、v2 内嵌 v1、祖先正文、17种角色字段组合及20种非法版本；直接装载 Git 基线模块逐字节比较 v1 预览，并移除当前 catalog 后验证历史包、输入、离线备份与同路径恢复。另绕过应用准入，用原生创建器保存可读的新图历史封装，再调用真实公开 `tasks.start`，在发送前拒绝且没有提交意图/请求/收据；与新增回归合计 **10 passed / 6.48 秒**。这些是独立执行，最终包191项为独立复核原日志而非重跑，两者不混称。

独立者还实际重算370源/wheel/安装及283冻结身份、11项CLI原观察、模型scope/输入/prompt/native审计/原结果与16份完整源码；从实际stdout重组925字节Skill及candidate连续9页至null，249,350字节完整相同。公开结果保留原 result.json 精确字节和原SHA。模型没有得到的证据由此在各自实际范围内补足，未把模型的限制改写成更广的审查结果。

本片修改六个已有生产模块，新增一个独立schema和一个静态示例，扩展两个原测试文件，没有新增调度器、账本、公开函数或CI作业。纯状态及证据导航收口后继续核完整范围/链接，再普通提交并核该提交自己的必要CI及实时远端；尚未预记交付门禁通过。下一片进入 AC4.2b 的可信建议运行。
