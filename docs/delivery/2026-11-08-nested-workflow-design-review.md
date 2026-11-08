# AC0b：嵌套工作流设计独立评审

日期：2026-11-08。评审者为本片新建的 fresh-context 独立代理，收到原始连续需求、基线和差异后自行读取设计、相邻实现与固定一手来源；未继承实施对话，也未以旧评审替代本次判断。基线及 HEAD 均为 `b01a59493709e3f49b92596e65500da831612703`，分支 `refactor/architecture-foundations`。

## 范围与身份

原始范围是交接时的 10 份 Markdown，含 3 份未跟踪新文档。逐文件身份见忽略目录 `.ergora/checks/nested-workflow-design/independent-review-inputs/review-scope.json`，SHA256 `9c7368576456ee0d4ad218f6f86decbd5821f3cc83f229d9cc5acbe275c4826f`；对应 `review-tracked.diff` 的 SHA256 为 `dfc304a5040593a6f45dbeb52ecab23d8b963dcb79cab721d3acba31524c95c9`。开始检查时均与工作树一致，副本保留原身份。

完整读取新[研究](../research/2026-11-08-nested-workflows.md)、[ADR0005](../architecture/decisions/0005-composable-workflows.md)、[AC计划](../plans/2026-11-08-agent-composition.md)与[交付记录](2026-11-08-nested-workflow-design.md)，检查 README、总计划、当前架构和 ADR0004 的实际差异。研究为 36,678 字节，SHA256 `f008fda852df1785b08c0c93124e1d7545577e45c2d917733a2db882dac1cf47`。

评审期间另读 AC1.2 原评审者的终结追加，以及主代理对 AC1交付、总计划、AC计划、共享回应和 AC0b 状态的归档差异；这些变更没有改本片设计。AC1.2 评审报告原 11,323 字节前缀逐字保留。本报告不重新认证该片 CI，也不将其通过当作嵌套功能证据。末轮文件身份及检查结果另存 `.ergora/checks/nested-workflow-design/independent-review-evidence.json`。

## 分别结论

|评审轴|结论|
|---|---|
|需求符合性|通过本片研究、设计和计划范围；未发现需修正的需求遗漏或与已读实现冲突的能力声明。新嵌套功能仍未实现。|
|可维护性|通过本片设计范围；未发现需阻塞后续切片的重复所有者、无实际需求的抽象或不必要控制流。具体接口与实现仍须在各后续切片审查。|

**本次所列范围内无 finding，无未解决设计阻塞项。** 结论依据如下：

- ADR0005 第 15–22 行区分 AgentDefinition、WorkflowDefinition、引用产生的实例、稳定调用路径及 manifest；结构祖先决定继承，DAG 前驱通过具名端口传数据。重复引用不共享可变会话，复合模板不为“阅读”虚增模型调用，符合可复用模板与叶子独立职能、资源和后端的需求。
- 第 29–47 行及研究第 5 节要求全部结构祖先声明的 Skill 指令和上下文完整进入每次叶子调用，无 optional inheritance、目录代替正文或静默截断。资源累加不授予 MCP、脚本、文件或网络权限；冲突、不支持的必需能力、继承资源与收窄权限不相容均拒绝。父子共同变更以自洽新修订保存，重核完整链和项目上限，在途身份不变。静态 manifest 与尚未生成的父材料明确分开；子调用快照固定原实例和产物，装载证据不冒充理解保证。
- 第 69–79 行及研究第 6–8 节保留三审查模板单用、并行 all-join 与执行串接、mandatory 全通过和全部原 finding；同候选、实际作者/session/委派来源、单 checkout 单写者、全根预算、层级取消及 unknown 对账均有约束。版本化组合回执不能伪装成旧单 actor；新执行在原 work/review 内渐入，原批准、可信集成/验证和 REVIEW_READY 保留，不重复嵌套完整旧六阶段。
- 继续由 Temporal 拥有持久执行，复用原 submit/poll/fence、准入、资源资产和后端调用 seam；未引入并列持久调度器或每种专长一类。AC3d → AC3b/c → AC4a/b → AC4d → AC4c → AC5/6 的依赖及各自可观察出口清楚。定义/schema、实际装载、递归冻结和执行恢复分别交付，避免以成员列表或画布代替运行能力。新文件为有明确消费者的设计记录；本片没有新增生产函数、测试、断言或分支，不能据此要求删除旧测试，也未发现虚构性能收益。

## 独立核查与限制

只读核 `drafts.save → reference.validate_input`、两开发输入 schema、portable 固定 workflow schema、`DevelopmentWorkflow.units/run/authors/context/stop`、`Activities.poll`，以及 `reference_task_creation`、实际 `reference_executor.model → stage_driver → agents.invoke` 和 `agent_runs`。现有实现确为六阶段内工作单元 DAG、单角色 binding 和固定模板说明加载，没有通用嵌套或祖先强继承；原 stage 派生 job ID、作者集合及单 actor 回执需要后续新版本桥接，研究已明确揭示此限制。

复核来源清单的全部 50 份缓存字节/摘要，无不符；清单 SHA256 `2b666270a7c484a8aba7f81a4f1c8424c75a161db695ad1d1b49f7e0a0292093`。定向抽查固定 LangGraph `e5e37b5…` 的 builder/compile、列表式 add_edge/barrier、LastValue 并发拒绝与子图 namespace，以及官方控制流页；核 ADK `1cb926…` 的弃用、共享 session state、单父与无界循环说明；核 Temporal SDK `a4c2bb…` 的 child start/execute、父关闭/取消默认及 README 的确定性和 handle 取消区别。高影响结论与原文一致；未把 Python builder 宣称为官方 JSON 标准，也未把框架状态隔离当成授权隔离。取得/核摘要不等于审计所有来源全文。

独立检查本地链接/锚点、研究的 26 项外部引用解析、30 条 README parser 命令及 `git diff --check`，均通过。另核生产、测试、依赖及 CI 相对 b01 无差异；读取作者 352 包文件/283 冻结身份记录，没有重跑其完整包比对或行为矩阵。一次输入身份检查遇到并发状态归档而拒绝，随后逐项对照新旧差异确认仅状态变更；这不是设计或产品失败，也未修改既有证据。

未安装或运行 LangGraph/ADK，未启动模型、服务、嵌套 workflow、浏览器或重型矩阵；未验 MCP 认证、真实权限强制、完整材料容量、嵌套故障恢复、原生 Windows 新流程或模型质量/性能。AC3d/3b/3c/4d 等必须以真实消费者和高价值边界行为分别验收，不能继承本文的设计结论。

本片普通交付尚需主代理记录评审处置、刷新包含本报告和状态归档的最终范围/静态身份，普通提交推送并核精确候选及实际必要 CI/远端事实。本轮只新增本报告和本人的忽略证据，无实现、测试、依赖、CI、他人文档、提交或推送写入。
