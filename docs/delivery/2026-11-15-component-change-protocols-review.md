# Q5.1：组件变更协议独立审查

日期：2026-11-15。评审者为 fresh-context Codex reviewer `component_change_protocols_audit`；先读原始要求、适用规范及实际差异，再核邻近源码和私有原件。未参与实现，只写本报告及指定 ignored 审查目录。

**本地需求符合性 approve；结构可维护性 approve。所审范围内实质 finding 0／0，无阻塞修正。** 这是目录协议、文档与静态清单的审查结论；普通发布、固定发布补核和本片自己的适用 CI 仍 pending。

## 固定范围

基线与本次所读 HEAD 均为 `750dd68ff2b1e41f6fe390d6a52e651bf41d5642`。最初 scope-r1 为13作者文件／193,892B；最终 scope-r2 为 **14作者文件／200,131B**，不含本报告。两份快照的全文、逐文件字节／SHA256及 tracked diff 已直接核对，最终作者文件与工作树一致。最终 scope 清单 SHA256 为 `5f072a6c291d45072c8955c90e2dda1cf6e3f90e56eb112067fe920f1710eb55`，tracked diff SHA256 为 `3066e9dd28142b3d64c4aae03650f2c6891adca63d2bd1ca761c6f8ca2fbbca5`。

实际范围为：

- 根 [AGENTS](../../AGENTS.md)，以及 [源码](../../src/ergora/AGENTS.md)、[测试](../../tests/AGENTS.md)、[脚本](../../scripts/AGENTS.md) 三个局部入口。
- [组件工程指南](../architecture/component-change-protocols.md)、[当前架构](../architecture/current.md)与[固定源码清单](evidence/2026-11-15-component-source-inventory.json)。
- [PLAN](../PLAN.md)、[Q总计划](../plans/2026-11-15-domain-review-optimization-quality.md)、[Q5.1计划](../plans/2026-11-15-component-change-protocols.md)和[Q5.1交付](2026-11-15-component-change-protocols.md)。
- Q4.1的[计划](../plans/2026-11-15-training-round-chains.md)、[交付](2026-11-15-training-round-chains.md)与[原独立报告](2026-11-15-training-round-chains-review.md)中的固定发布记账。

r1→r2只补Q5.1实际验收／自身审查事实，以及Q4.1固定750发布和仍在途CI的计划记账；根指针、三个局部入口、组件指南、架构及静态清单逐字保持。未改变Python、schema、定义／模板资源、SDK、依赖、安装器或CI策略。

## 两轴依据

|核查点|直接证据与判断|
|---|---|
|真实选择接口|`agents.invoke`及`agent_runs._admission`消费 `AgentBackend`；其 `for_binding`先从组件元数据取得implementation，再在本族 `_BACKENDS`构造。工单模块级工厂 `issue_backends.for_binding`按本族tool构造 `IssueBackend`，`issues`与`issue_writebacks`消费该接口；动作差异由后者已有action契约持有。指南指向这些现有owner，没有要求上层新增逐实现分派或通用注册总线。|
|配置与原生版本|`components`派生角色能力／可选项，`bindings`验证本族配置，`projects`保留修订与旧缺省语义，`registrations`作单向原配置投影。`WorkflowInput._INPUTS`保留1至11各自构造／队列／请求根和原workflow；指南要求沿原版本与生命周期owner扩展，没有把不同格式版本混成一个版本号或宣称任意静态图均可执行。|
|资源与格式|核 `workflow_definitions._materials/_within/_readable/_Compilation`、`DefinitionLibrary`、严格JSON／YAML转换、`asset_trees`及`task_mcp`。祖先完整材料、子权限上限、同名冲突、容量、不可变版本和不同摘要合同的说明与源码一致。目录AGENTS不成为runtime grant或MCP资源。|
|状态与恢复|核 `State`迁移／旧writer隔离、备份与领域事务；`reference`专用进程按所选注册配置装载，`issue_writebacks.send`先提交attempt再外发。指南保留原ID、完整意图、receipt、unknown先对账及原冻结输入，没有建立第二运行／实验／批准状态。|
|能力与责任|`training_rounds.create/read`仅采集原观察并离线核身份，CLI的read分支不构造State。指南明确保留kernel评估及“无需修改”结果，optimizer／model／dataset／loss／forward局部协议归授权目标项目。固定TorchTitan／Bridge／slime研究只是接口取舍依据；不引入trainer依赖，不把deprecated数据ABC或可选工具的局部分支宣称为统一插件化。|
|指针与检查成本|根只路由，三个目录入口按实际分支触发；详细扩展规则集中在一份指南，操作参数继续指向原手册。核现有Agent、工单／写回、继承、preset、迁移／备份测试接缝及显式CI分组；没有新增测试、断言、fixture或CI job。建议按可达失败与真实状态转换选检查，并区分源码、安装、服务替身和真实外部验收。|

本片完成的是可定位、可按族使用的变更协议。它没有实施全仓重构，也没有宣称全部可变量已经充分解耦；Q5.2实证重构、自动循环及目标训练项目的实际组件协议仍由各自后续范围负责。

## 实际复核

独立从固定750的Git对象重算：**76顶层第一方Python模块、312条去重本地AST导入边、无环、28第一方console JS**。公开清单的76个源码SHA和28个JS SHA逐项一致；函数内导入计入，vendor、驱动、动态装载、SDK与子进程运行不在该图内。架构新增的本地Git包／Git读取与多轮索引调用方向对应实际owner。旧506cc57与更早清单保持原身份，静态无环没有升级成运行、恢复或性能证明。

固定Git的 **640产品文件＝当前产品源文件＝原记录清单＝新r1 wheel＝原750 wheel＝原r1非editable安装**，均逐字一致；源码包根额外只有repo-only `AGENTS.md`。沿未改的 `pyproject.toml`包选择，新wheel没有包含它。新wheel SHA256 为 `e6eadd281a65801d280261e9dddc9399d52b4c179bb3ab506c4ed6a9e5e758d4`，原750 wheel仍为 `368f534a0497a12d00c89ad5f2e835343ed4e773c88048ab457a2b6f381bb558`；两者产品相同，wheel本身身份不同。283冻结参考逐项匹配原manifest。此处是文档／打包排除核验，没有重装相同产品或声称新的runtime验收。最初输出重定向因目录缺失而在build启动前exit1，原件保留；build-r2日志和实际wheel对应后续构建成功，无产品修正。

独立复核原自身审查：run `01bdb0678c554fa89b9d10cda04c2bf9`，succeeded／exit0／25.034234秒／approve。22个完整文件／348,582B逐项匹配原packet-index，全部文件块、原task及三项继承resource均连续出现在prompt／实际stdin中；prepared与sealed input树身份相同。input为 `5c1fbb5d21012ddc7d205f28e1a685502fab82ea42683770b93b72e4df4dbcf9`，result SHA256为 `7c934fd9343ec2cf5ef6f6ec6c89028a072cd1c474e1f30bbf892b291cff31de`。这只是所给完整文本的原模板审查，不代替本次私有原件核验，也不认证产品、CI或异后端成功。

原r1的12份Markdown／259本地链接及fragment零错；最终作者r2的 **13份Markdown／262条**另行复核零错。本报告的本地链接另核。现有tracked diff的 `git diff --check 750dd68…` 通过；新增文件另核尾随空白。最终暂存后的完整diff及固定发布身份仍须在发布补核，未把tracked-only检查称为完整暂存验收。

私有独立原件保存在本片 `reviewer-r1/`：`scope-audit-r1.json`、`package-audit-r1.json`、`inventory-audit-r1.json`、`self-review-audit-r1.json`及最终scope／链接审计。首轮清单探针误将vendor JS计入，已按公开清单明确的第一方范围修正并保留探针更正记录；它不是产品finding。

## 未覆盖与交付门禁

本次没有安装依赖、重跑产品测试／模型／服务／训练／GPU、执行目标业务代码、写Git或修改实现。现有测试只核接缝位置与含义；固定外部研究未重新认证当前上游兼容性。未验证数值／梯度／分布式、真实训练质量或收益、自动循环／采用、完整Forge及跨机器恢复，原开放条件保持。

Q4.1固定750的原独立发布审查属于前片；其自己的CI `43629303623`在本次冻结范围中仍pending。本片普通提交／推送与自己的适用CI亦pending。新目录AGENTS不在当前push忽略项内，不能因本片是文档就跳过实际触发的CI；前片CI终态及原独立闭合前继续保留后继push门禁。后续须核本片精确发布文件／远端Ref与自己的适用CI，任何前片或后继结果均不替代。
