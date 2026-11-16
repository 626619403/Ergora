# WA5-S2：设计来源 journal 存取实施

2026-11-16。当前隔离树7路径已形成首稿：native来源journal持久化、tasks／reference source APIs与CLI声明已有实现；r4当时首稿的局部源码检查2 passed（pytest41.26秒／JUnit41.240秒，runner43.530秒），覆盖原真实native／no-jsonschema reader与新增两轮完整来源／离线答复happy path。中断恢复、并发、坏链、GET无写、容量、准入、新source native依赖、真实CLI、新安装、fresh实现独审和自己的CI仍待验。未合入或发布，不是公开产品可用性或ready结论。前两次setup错误与r3缺API的早期失败继续保留；e5官方8/8 CI不认证本隔离草稿。设计执行、可信人类批准及F/J/G继续关闭。

## 合同与准确基线

[完整 S2 proposal](../plans/2026-11-16-design-source-journal-s2.md)规定：沿原 approval journal 保存两轮完整设计／报告与原答复；按原 operation ID 读回和恢复；原 `task plan` 与最小 `task design inspect` 返回完整来源链和全文。所有结果只供讨论与检查，`local-process-only` 和 `reported-human` 不能成为有权 owner 的决定，不产生 resolution、seal 或执行权。既有 schema1 approve／cancel、原 receipt／signal、原任务绑定、六阶段和 candidate 证据合同保留。

受审原 proposal 共197行，SHA256 `fdf2c8a8bebac116a0b1a56556a4fcc1f3493e3fd93c2b2c1f3f87d65c185c0e`。[新的 fresh 独立设计审](2026-11-16-design-source-journal-s2-design-review.md)需求 approve、维护性 approve、开放 findings 0，另核最终 S1 与原 v1 source／creation／submission 路径兼容。原件和设计报告冻结于 `.ergora/checks/design-source-journal-s2/design-review-r1/`；proposal 后续首行／检查框及追加状态不改变该原件身份。设计审不替代实现验收。

|身份|本片实际状态|
|---|---|
|隔离实施分支|`feat/design-source-journal-s2-r1`，从 `7fc42177db11fbfe4c9adb33342ecb5da4ed0434` 建立。|
|已接纳产品基线|`6cec589f404b17f4828a70807d5e33d89fad3fa0`；起点 src/tests 与该联合产品相同，包含最终 S1 `b28cd316` 与容量片 `919a380`。文档提交不改变其产品身份。|
|隔离树与原始证据|实施树 `.ergora/worktrees/design-source-journal-s2-r1`。此为忽略的本地工作树，不能当作已发布文件或跨机器证据；新源码和验证证据的最终冻结身份待实际产生后记录。|
|初始源码交接|源码 owner 已读实际 approval／submission／creation／reference／tasks owner 和已审 proposal；交接时未改 S2 源码、未运行本片测试。|

本记录只维护 docs，不代替源码 owner 修改实现、配置、测试或运行 home。后继每项结果必须固定实际 candidate／diff、配置、调用入口与原件，不从联合产品已通过的安装或 CI 转授给 S2。

## 待实现与验收

实现沿已审原 owner：应用层负责结构校验与短 revision reservation，`reference` 负责实际所选 native 进程及公共结果校验，approval owner 负责原件身份、唯一 source 链、安全正文发布、pending 尾部与同 ID 恢复。容量资源只约束存取，首条操作冻结可收紧的有效限额，不导入 design policy 或增加第二状态库／调度器。

|阶段|所需可观察证据|当前结果|
|---|---|---|
|源码实施|完整 packet／response／正文及准确身份，唯一 committed 链与 pending 尾部；原 schema1 合同不变。|7路径首稿：reference_task_approval／reference／tasks／cli、原测试与2资源；native持久化、source APIs／CLI已有初稿，未完成验收或独审。|
|源码验证|真实 CLI／tasks／reference／native 两轮全文读回；删除原 body-file 后同 ID 恢复；正文后 result 前真实进程退出；并发 pending、旧 ID 冲突、坏链拒绝；GET 全文件快照无写；有效非默认容量与 aggregate 零增量拒绝；公共入口应用校验、持久确认失败和旧批准恢复。|r4局部源码2过：原native／no-jsonschema reader＋完整两轮／离线答复；pytest41.26秒、JUnit41.240秒／runner43.530秒。中断恢复／并发／坏链／GET无写／容量／准入／新source native依赖／真实CLI仍待验。|
|新安装|准确新非 editable 包、完整文件／执行位／实际导入／参考／依赖身份，同一新候选走真实 CLI 和所选 native。|未构建或验证。|
|原模板与实现独审|保存完整模板输入／实际后端／原回复；新的 fresh 实现 reviewer 获得原始要求、完整 tracked/untracked 差异及实际验证，分别审需求与可维护性。|未开始；设计 approve 不转授。|
|集成与发布|源码／安装／独审等本片门槛满足后普通合入、必要联合验证、普通推送及自己的适用 CI。|未开始。|

真实 Temporal、自然人认证、F/J 的权威 materials／seal／withdraw、G1/G2、可执行 v12、业务质量与训练效果仍是各自后继验收。当前只有局部源码happy-path通过，尚无公开S2可用性或完整验收结论；下一步由源码owner继续补齐上述故障／容量／CLI接缝，冻结准确源码后新安装与fresh实现独审。

源码owner早期交接为clean于7fc4217、已核实际owner／预检／schema／native IO；后继仅改测试草稿，不能沿用该早期clean描述为当前状态。实际runner与fixture结果分别如下，原件根 `.ergora/checks/design-source-journal-s2/impl-r1/`：

|运行标签|实际结果与范围|
|---|---|
|red-first／r1|2 setup errors／1.08秒：basetemp父目录缺失；未执行产品feature，不是功能反例。原stdout保留。|
|red-source-r2|1 passed、1 setup error／15.40秒：共享模块安装的`.venv`被首个测试转换，后继setup失效；不是新功能反例。完整argv／环境身份／hash／raw／JUnit与自有PID终核保留。|
|red-source-r3|fixture按function teardown恢复其自己原`.venv` symlink后，原真实native／no-jsonschema reader1 passed，新两轮用例1 failed：`AttributeError: tasks.design`缺失。JUnit14.02秒／runner14.969秒，无setup错误。|

真实native入口和no-jsonschema约束保留；fixture改动仅用于该测试自身恢复。不得把setup错误说成已观察的S2存取拒绝／恢复行为，也不得把旧联合安装或相邻CI修正转授S2通过。r3已观察到拟议API缺失。之后仅加入两份草稿JSON资源 `data/design-profiles/design-source-storage-v1.json`／`data/schemas/task-design-source-v1.json`，并在 `reference_task_approval.py`／`reference.py` 作共享本地材料及结果检查提取；加上测试共5路径。r3的旧reader通过发生在这些草稿之前，不认证后继factor／资源；该5路径阶段当时尚无source APIs／CLI／journal持久化；后继r4首稿见下节。原件保留 `red-source-r3.*`，含完整argv／源码hash／raw／JUnit和自有PID start ticks／boot／wait后absent。这个早期r3结果不作为后继首稿的通过或ready证明。


## 首轮源码 happy path：source-first-r4

源码owner已在同一隔离分支形成7路径草稿：`reference_task_approval.py`、`reference.py`、`tasks.py`、`cli.py`、`tests/test_task_plan.py`及两份新JSON资源。native来源记录持久化、source APIs和CLI声明已有初稿；公开主分支仍为原6cec源码加已审测试平台修正，未包含这些S2草稿。

`source-first-r4.*`保存准确argv、before源码身份、stdout／stderr／JUnit、自有PID/start ticks/boot及wait后absent。实际2节点：`test_application_task_plan_uses_selected_native_python_without_jsonschema`与`test_source_journal_preserves_two_complete_rounds_and_offline_answers`；pytest **2 passed／41.26秒**，JUnit2 tests／0 failures／0 errors／0 skipped／41.240秒，runner43.529603秒（显示43.530秒）。这证明r4当时首稿的原reader和完整两轮／离线答复happy path，不证明中断恢复、并发、坏链、只读／容量／准入或真实CLI，原reader的依赖检查也不替代新source路径的专项native依赖验证。

首稿未完成、未冻结接纳、未独审、未新安装、未合入或发布；S2自己的后继CI仍待。联合主分支e5/run43840394544的8/8成功保持其准确候选身份，不能转授本首稿，更不能开放设计批准或执行。

r4之后源码owner继续调整schema／validation草稿；这些后继字节未由上述r4结果验证，当前验收状态仍为实现WIP。实际源码身份随各label保存，不把r4的2过转授后继修改，更不继承e5公开CI。
