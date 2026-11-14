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

## 固定普通发布补核（2026-11-15）

同一独立评审者已直接核对普通发布 `705cbe428dce73ff222dbdaec3c67329a310c06d`，唯一父为 `750dd68ff2b1e41f6fe390d6a52e651bf41d5642`，tree为 `9516f1710d131f7c70acd7d657a79fd66d7cdbbf`。本节覆盖上文待普通发布／固定发布身份状态：**固定发布需求符合性 approve／结构可维护性 approve，新增实质 finding 0／0；本片自己的适用CI仍pending，未认证成功。**

固定Git的变化集合恰为 **15个文件**，逐项blob ID、字节数与SHA256全部匹配 `staged-r1.json`、`local-commit-r1.json`和`publication-r1.json`，无额外或缺失文件。相对已审scope-r2，协议、根及三个目录入口、架构与清单均逐字相同；仅四份计划／交付文档补记实际本地独立通过，并加入本报告原 **8,342B／SHA256 `11b0513445d571064cd7b2634ed4225c7f71810c64c3016c15c70001d7c0ff9d`** 的版本。原报告与本次追加前的工作树全文一致；上述前缀保持，原本地结论和证据未改写。

|发布原件|独立重算SHA256|
|---|---|
|`staged-r1.json`|`e4ede396f36165a9c5546f2f1515b27b63b0e247d6027b23f2e3a7aae909f95b`|
|`local-commit-r1.json`|`fb6041672b8f8abf12025eee917c48f4e391f77105d660f4c6676add22786807`|
|`publication-r1.json`|`a045e3e88d2a40c56e4a09d42f70d1a6087fa4d895568166029ad5272c007372`|
|`remote-r1.txt`|`0fceec26b7791831739f7ee0ad43afa9af2cdb18f730d84b75a4f1269a341ee7`|

独立执行只读 `git ls-remote --refs origin refs/heads/refactor/architecture-foundations`，实时完整Ref与保存原件均为上述705发布SHA。原本地提交记录中的“尚未push”保留当时身份，后续publication和实时Ref提供实际普通发布事实。

只读固定705对象，排除repo-only `src/ergora/AGENTS.md`后的 **640产品＝原750产品＝原记录清单＝本片r1 wheel＝原750 wheel＝原r1非editable安装**；两wheel各自的SHA保持上文身份，283参考逐项匹配原manifest。没有使用后继工作树源码认证本片。固定发布的 **14份Markdown／277个本地链接及fragment零错误**；原13份／262条保持原范围，新增本地终核报告入口及本报告链接按发布内容另核。基线→固定发布的完整 `git diff --check` 通过，已包含全部新增文件。

前片Q4.1的原reviewer已在其原报告追加自己的CI `43629303623`终态两轴approve／开放0／0，前片push门禁已解除；该终核仍只属于固定750，不认证本片CI。本次只核其原终核报告及所引用独立结果身份，未重复解析前片全部官方CI页面。

私有补核原件为本片 `reviewer-r1/publication-r1.json`、`publication-live-remote-r1.txt`、`publication-docs-r1.json`与原报告前缀快照。本次无产品测试／模型／训练／安装、Git写入或平台写入，仅固定对象／既有原件的只读核对及报告追加。剩余验收为本片完整候选自己的适用CI终态及同片补核；原真实训练、质量、性能、自动循环、完整Forge和目标项目协议的开放条件保持。

## 自有CI终态补核（2026-11-15）

同一独立评审者已直接重解析本片 [Portability 43631156705](https://github.com/626619403/Ergora/actions/runs/43631156705) 保存的官方原件，绑定固定提交 `705cbe428dce73ff222dbdaec3c67329a310c06d`。本节覆盖上文待CI状态：**需求符合性 approve／结构可维护性 approve，开放实质 finding 0／0，Q5.1片内剩余验收0。**

终态原件为 `ci/observation-terminal-r6.json`、`job-groups-terminal-r6.json`、`run-terminal-r6.html`及八份 `job-*-terminal-r6.html`，共11件，观察时间 `2026-11-14T19:37:17.015067+00:00`。原run页状态为 **Success**，pushed commit链接包含上述完整SHA；原导航指向自己的run及 `job_groups_batch?attempt=1`。完整分页 **totalCount=8／hasMore=false**，八个唯一job与固定705的workflow及六组Linux配置相符。

|Job|原job ID|必要步骤成功数|
|---|---|---|
|plan|132557838639|1／1|
|Ubuntu 3.11 group 0|132557901121|4／4|
|Ubuntu 3.11 group 1|132557901138|4／4|
|Ubuntu 3.11 group 2|132557901097|4／4|
|Ubuntu 3.11 group 3|132557901163|4／4|
|Ubuntu 3.11 group 4|132557901140|4／4|
|Ubuntu 3.11 group 5|132557901183|4／4|
|Windows 3.12 group all|132557901126|5／5|

终态分页的八job均为 completed／success，各job页的selected job ID、run导航与 `check-steps`完成状态逐项相符。独立从原HTML的 `check-step`重解析 **30／30必要步骤success**：plan读取分组，七个native job的Python准备、wheel构建安装、参考身份与应用回归，以及Windows PowerShell 5.1安装升级。每一步均有原完成标记、起止时间和log URL；URL中的完整commit、job ID和step number全部匹配。步骤按顺序完成，开始不晚于完成、完成不晚于观察时间，native必要步骤不早于plan完成；重解析字段与保存观察逐项一致。这里认证官方步骤结论与日志身份，没有取得并虚构逐测试日志或额外测试总数。

此前七组捕获均保持中间态：`observation-r1`为22／30；`observation-r2`及`terminal-r1`至`terminal-r4`为28／30；`terminal-r5`虽为30／30，原Windows job仍in_progress、run仍In progress，不能当作终态。仅 `terminal-r6`具备八job和全部必要步骤的共同成功。八组各11件、合计 **88份官方捕获**的原长度／SHA256、分页、job与必要步骤均已直接核对，旧null结论和空完成／log字段保留原值。

顺序采集有一处可见进展边界：`observation-r2`的group 5在先读的job-groups原JSON中仍in_progress，随后保存的该job HTML已completed；两次读取各自状态已分开记录，没有拼成原子快照。当时Windows和run仍在途，终态r6的分页、job页及步骤则严格一致。首轮审查探针因假设该中间状态完全相同而停止，修正探针后保留上述差异；未改原捕获、重跑CI或修改产品。

另从固定705的Git对象复核原 **15个发布blob**、唯一父750／原tree及暂存／本地提交／发布清单，再核排除repo-only目录AGENTS后的 **640产品＝原记录清单＝两wheel产品＝原r1非editable安装**，**283参考**逐项保持。没有读取后继Q1.2产品源码作705的验收依据，也没有借前片CI认证本片。

独立解析脚本 `reviewer-r1/ci-terminal-r1.py` SHA256为 `b6206e90ba89a9a4e2dc3947fd021ec895954deceac1f208bca3f09961b38eba`，结果 `ci-terminal-r1.json` SHA256为 `82e5db53f90a69a6b6a701f8c1877e91cd8b61b2756c56f0f9218d9373b3adde`。追加前报告 **11,420B／SHA256 `a47ffb8e8cb1b8f71bcf449e129e200fd8d94439d63b820d8523888bd880cdac`** 的前缀逐字保持，原全文另存 `ci-terminal-report-prefix-r1.md`。

本次没有测试／模型／训练／安装、Git或平台写入，仅追加同一固定片的CI与身份终核。Q5.1目录协议、静态清单及其本地／固定发布／自有CI合同已闭合；目标训练项目实际协议、Q5.2实证重构、真实训练／GPU／质量／性能、自动循环及完整Forge等原开放范围继续由各自分片验收。
