# Q4.2b1：原训练提交的前置阻断

日期：2026-11-15。承接[有界循环计划](2026-11-15-bounded-training-cycles.md)和[a2有限选择](2026-11-15-training-cycle-selection.md)。实施基线固定 `1b58e929aaf495c16f448454c78de23718786ae9`，a2自己的CI与原终核现已闭合，不转授本片。修订后的实施前合同已独立两轴通过，当前沿下述边界实施和验证。Kernel专家继续保留在v3路径，不改提案图或283参考文件。

## 要解决的具体问题

当前 `training.cancel` 要求原start回执已经确认run ID；prepared／unknown的start尚不能走这条取消入口。与此同时，原 `_Submission.dispatch` 在最后一次preflight以后才发送RPC，取消一个本地等待进程不能证明远端不会迟到创建workflow。

原 `LocalTrainingAdapter.fence_and_lookup` 已在同一个 `registry_lock` 下核对完整Experiment、查找已有job、不可变写入完整binding fence；`create_job_if_absent` 在同一锁下先拒绝fence。应先把这一**原本已有的阻断能力**接入应用，使操作者可以在尚无run ID时阻止未来本地job创建。它不取消Temporal workflow，也不能证明已经启动的clone、runner、归档、跟踪或其后代停止。

## 本片行为与调用边界

拟增加薄 `training fence-start PROJECT EXPERIMENT --revision REV --manifest-sha256 SHA --confirm` CLI，进入原 `training` 应用及原 `reference_training_submission` 进程；最终字段／退出合同在实施前评审后固定。

1. `--confirm`是操作者对这个精确原Experiment的**本地实验级fence**的明确授权，包含抑制其后续job创建、可能使runner／归档观察到取消，以及阻断尚未创建的release ticket。它不确认run归属／资源已停止，也不撤回已经创建的ticket。必须同时确认项目修订、实验和完整原manifest SHA。沿原 `_TrainingProject` 保留已发布注册、canonical执行目录和control归属检查；本片只支持原Linux／WSL2本地执行上下文，注册已漂移时明确拒绝，不先放宽恢复校验。
2. 如果已有start intent，沿原load／status验证完整原身份，从该intent取原Experiment；首次阻断在观察到prepared／unknown时才可新增fence。已观察到submitted时指向现有精确run取消入口，rejected先对账归属；没有已有匹配fence时两者均拒绝新增。manifest确认必须与原intent一致，不能因当前同名spec变化换绑。状态只是观察快照：在不持有投递锁时，receipt／rejection可以在观察后落盘，本命令不保证全程排斥这些终态，也不认证或接管run。
3. 没有start intent时，沿原records读取已准备实验及其完整binding／spec，并确认所选manifest SHA；不为“阻止提交”创建一个新的start intent，也不调用start preflight来授予准入。原records仍拥有manifest／spec／runner及来源关系，不另写读文件器。
4. 通过原本地adapter的 `fence_and_lookup` 执行阻断，不重写registry锁或创建路径。mutation前沿原 `adapter.safe_file` 核registry lock、本实验job request及fence路径，frozen intent分支也不能跳过。当前控制调用不持有submission远端投递锁：否则可能等在正在进行的RPC后面而无法及时阻断。应用只在本地操作期间保留原项目修订预留，不跨远端RPC持有SQLite事务。
5. 退出0仅表示确认原binding的本地fence已保存或匹配读回，返回完整字节SHA、锁内 `existing_job` 或null、`submission_status_observed`及可有的原intent SHA。`runtime_status=not_queried`、`executor_stop_confirmed=null`、`execution_success=null`；不推断run／父循环归属、ticket是否存在或资源停止。重复同一确认允许读回已有相同binding的fence，即使receipt／rejection后来落盘；这是确认原本地事实，不重发start、不发送signal、不补回执或授予接管权。不同binding或损坏记录拒绝覆盖。

本地adapter的导入链经过原 `perf_temporal.client`，因此首版需要 `temporal` extra；新operation加入原进程SDK要求集合，但不连接Temporal服务，不调用会加载credentials的 `core.environment()`，不读取API key、不启动模型或runner。缺SDK可见报出原依赖要求，不能声称SDK-free。本片不根据当前 `PERF_CLUSTER_ADAPTER` 偷换成本地之外的未验证实现；外部scheduler的fence语义另验后再开放。

**未被本次显式fence的已完成前轮**保留人工release窗口；所选实验的原fence会抑制其未来release并可能被executor观察到。已经创建的ticket保持，本命令不回滚它。父循环将来只能对其当前未完成且明确拥有的活动轮调用停止，不能遍历并fence全部旧轮；本片仅手工确认，没有父循环授权，自动控制不得调用它来接管人的原运行。

## 验收节点

|步骤|可观察结果|当前状态|
|---|---|---|
|B1 合同与原owner|核原registry fence／create锁顺序、start最后preflight、取消需run ID、注册及依赖链，确定CLI与回传边界|r2独立需求／维护两轴approve，开放设计项0／0；R1／R2设计关闭，未认证实现|
|B2 应用接入|薄CLI及原training／submission进程调用原adapter，不新增状态表、调度／训练／批准或通用插件框架|r2已实现，frozen job ID P2已最小修正；只用原本地factory，无投递锁／服务连接／密钥加载|
|B3 最小接缝|无intent、prepared、unknown的精确阻断；错误manifest／修订／binding不换绑；已观察submitted／rejected且无fence时拒绝新增；status后落回执／rejection或fence后丢回复再落回执时，重复读回原fence与事实，原记录及RPC次数保持|修后源码18项及后补R1红绿保持；最终r2七suite131通过／674.59秒，含全部本片和原恢复接缝|
|B4 竞态与事实|真实原registry上fence→create拒绝新增、create→fence回同job；最后preflight后的晚到RPC可以创建workflow／receipt，不能创建被fence的新native request，已有job仍可lookup；fence→ticket拒绝新增、ticket→fence保留原ticket，未选中成功实验无fence|源码接缝通过；真实registry／原release owner＋跨进程SDK服务替身，不冒称真实Temporal或停止|
|B5 安装与审查|新非editable包和283参考身份；安装原接缝、实际SDK环境CLI，无服务可执行本地阻断；自身模板、新fresh-context独立两轴及精确普通发布／自己的CI|r2两安装645逐字／283、安装131项、实际六CLI／48原文件和DB、自身35.450秒approve通过；原独立最终本地两轴approve／R1关闭／开放0／0，185原件核；普通发布／自己的CI待|

本片只补当前必要的本地阻断接缝。测试应直接观察原adapter／registry与原记录的关系，不新建仅检查提示文字或helper字典的suite；原RPC丢回复和完整cancel流程保留原保护。超时／中断可能发生在fence已保存之后，错误不能声称没有副作用；沿同一原binding读回或幂等重试，回传该次实际观察，不重发start。

## b1之后仍必须完成

- **Q4.2b2冻结上下文恢复。** 明确授权身份及原intent归属，在当前注册变化后仍能观察／停止旧运行，同时拒绝新派发；不能删掉registration检查或只传旧revision。b1拒绝漂移不关闭此项。
- **Q4.2b3不可续期预算与完整executor。** 真正提交边界验证原始work deadline；处理取消早于intent／run、最后preflight后晚到start、unknown历史对账和跨恢复试次，覆盖clone／worktree、runner、archive、MLflow及后代资源。原本地process owner可以承载监督，但杀worker future／调用进程不证明已脱离的runner停止。预算不足／服务不可达须给cleanup未确认。
- **Q4.2c／d。** Temporal控制工作流及其worker／实际run-local owner、双向输入／输出／异常与history容量、每轮完整结果保存及超限停止、真实CPU旅程、预设可信门禁分类与独立release。未经上述验收，不开放自动派发。

这些是后继独立片，不因本地fence调用成功而提前完成。实际训练、GPU、质量与加速收益仍沿B3资产／命令／oracle和设备条件另验；本开发会话不改目标业务仓库。
