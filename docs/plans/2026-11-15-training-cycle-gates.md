# Q4.2c0.2b：原执行门禁与独立停止通知

日期：2026-11-15。承接[控制器具体合同](2026-11-15-training-cycle-controller-contracts.md)与[c0.2a](2026-11-15-training-cycle-admission.md)。产品基线固定 `07cbae2227d60c849df6ac96b4f96d3f71d80d43`；其自身CI仍待恢复读取和原reviewer终核。当前仅做源码调查与设计，不开放后继产品路径。kernel专家保留在v3总优化路径。

目标是让父停止真正约束原来的四个动作，并能独立通知原owner；保留原start slot、原launch、原clock、唯一reaper与人工release。c1才创建总Workflow和独立cycle worker，c2才提供公共CLI／HTTP。此处的完整binding支持不等于已经提供自动循环。

## 源码调查与所有者

|实际接缝|本片动作与调用者|保留的算法|
|---|---|---|
|`training_execution_protocol.CycleAdmission`；`BudgetedStart.source`与`validate_context`|在现有stdlib owner核完整controller三件套、run和ordinal；两个原消费边界共同复用。应用侧继续核State／project，native侧不导入它们|原authorization／ready、cycle raw SHA、五key context和source key集合|
|`reference_training_runtime`的Experiment专用`lookup`|增加独立的controller固定run读取用例，供submission、worker、Execution三个真实异步消费者使用；不能把总Workflow套成Experiment|原Experiment／Outcome读取合同|
|`_Submission.dispatch.CheckpointedClient.start_workflow`|父共享许可覆盖原完整投递期间；原attempt发布和最终RPC前分别核stop；完整父run history在原异步操作中核|原preflight、唯一attempt、memo、RPC和丢回复只对账|
|`BudgetAdapter.create_job_if_absent`及锁内`lookup_job`|父共享许可在进入原create前取得，直到原registry调用返回；锁内lookup再核stop／完整来源；ContextVar保存当前创建的原上下文|原registry lock、lookup及真正创建代码|
|`Execution.check/request/admit/current`|父run history及原actor；父许可覆盖原execution.lock下request／launch发布，最后再核stop|原显式完整确认、不可返还launch及等待原窗口|
|`training_execution_protocol.native_main`|外层共享许可覆盖原process；admission callback在原executor lock内，于attempt／ack发布前后再核stop|原process、原native venv、原executor lock与原reaper|
|`training_cycles`、`processes`及既有预算phase接缝|独立writer、各候选的原owner精确通知、排空及原执行链观察；所有业务I/O隔离在各自操作进程中|原pidfd通知、原supervised reap，不新写第二个reaper或live owner循环|

以上是真实源码接缝，不是任意后端／插件注册表。新增方法优先留在这些owner；顶层入口只负责编排。283冻结文件、native delta、依赖和CI矩阵保持。

## 完整binding及两类验证

保留原三字段手工binding。自动binding只额外包含controller，严格字段为protocol、workflow_id、run_id、intent_sha256、ordinal；ordinal是0至所选列表长度减一的整数，布尔值、负值和越界均拒绝。schema1不得带controller，schema2不得使用手工binding。重复prepare比较整个原selector，不能漏掉controller后接管已有手工start。

在原CycleAdmission内核本地controller intent／attempt／receipt：完整expected intent沿a片的原算法；attempt核完整input SHA和intent SHA；receipt只增加原非空run ID。binding必须与三件套及authorization完全匹配，原ordinal必须指向同一个experiment和完整原admission observation。不存在、部分文件、额外字段和任何身份漂移均拒绝，不补造总记录。普通历史读取不要求当前controller或SDK可用，不回写原链。

本地记录匹配不能证明远端归属。三个异步动作在自己的受监管上下文中另核父级固定run：describe与first started event的完整input、workflow type=`TrainingCycleWorkflow`、原task queue及独立memo `ergora.training_cycle_sha256`必须相同；必须观察为RUNNING才准入新动作。NOT_FOUND、不可达、run改变或memo／input漂移均拒绝新动作，不重发。这里不读取新的“current run”，也不在旧Experiment lookup中加特例。

远端检查不得进入原prepare的SQLite reservation：`prepare_binding`只核本地，submission在事务结束后的dispatch核父run；worker在`super().create_job_if_absent`前核远端，registry锁内lookup只核本地最后gate；执行在`Execution.check`核远端，随后才进execution.lock。native原executor锁内没有SDK查询。

native hook只能核原完整本地三件套／binding、父stop、原owner与clock，不导入SDK或声称远端实时查询。它消费已经经上游远端核验、冻结到原owner context的同一binding；原父cancellation的本地stop和原clock仍是执行撤销接缝。服务terminate或cycle worker缺席不保证即时回收，沿原合同保留实际限制。

## 许可的范围与锁顺序

沿a片非阻塞共享许可，取得后最后检查；不加新计时器。submission原锁可在父许可外，但任何父drain都不得拿submission锁。worker和native遵循父共享许可→原registry／executor；request和launch遵循父共享许可→execution.lock。父writer不等待任何这些锁；排空仅拿父排他许可。

原最后gate必须在会阻塞的来源检查／fsync之后复核stop。父锁保留至对应实际动作返回；不能把一次早期permission检查当作覆盖后续await／RPC或原registry调用。RPC在stop可见前已进入服务时可能晚到；worker锁内gate仍拒绝新create，已持有动作不返还start机会。request／launch／attempt／ack在停止交错后即使已部分落盘也不擦除、不重发；原owner沿原清理路径处理。

原`admission.lock`在ready后不可在线替换；helper退出仅关闭自己的fd，不unlink或重建锁。现有联合恢复要求所有writer／外部工作已停且原home不存在，不支持活holder期间原地恢复。若以后支持在线锁替换，须另行定义锁代际／排空证明，本片不把同用户任意换盘纳入当前合同。

自动执行的actor来自原schema2 authorization；手工执行保留当前明确操作者校验。该差异在现有request构造和native callback中按原授权模式处理，不静默改变schema1请求或历史记录。

## 独立停止与进程监管

停止编排只消费完整原cycle身份，不创建可变current-round账本。writer、每个候选的通知／原件观察、drain分别监管；文件读取、身份查找或fsync阻塞不能卡住peer通知。已有`CycleAdmission.request_stop`是存储用例而非live停止入口，不能直接作为一个同步串行总stop。

通知helper只认本cycle完整binding的原budget owner，沿`processes.notify_identity`发精确SIGTERM，由原owner完成fence／cleanup／reap。没有owner、身份未知、已退出或不属本controller均如实返回，不按裸PID发信号，不对所有选定实验统一发送Temporal cancel。此前已测量接受的轮次保留其人工release窗口；原owner的completion优先逻辑保持。父停止响应分别列各分支结果、stop可见／持久、父许可排空及原c2链的executor stop，不用一项推导另一项。

这里需要复用原`processes.run(supervised=True)`的唯一reaper，但同步run本身不能在总driver中按候选串行调用。实施b2前先固定最小共用监管接口：真实budget phase和cycle operation是两个生产消费者；保持budget现有两帧身份、stopped先于持久观察及不再spawn的顺序。若需要抽出非阻塞管道监管，则独立做行为保持的b2a，保留原budget回归后再接b2b；不为cycle伪造BudgetedStart／operation对象，不复制selector／reap状态机。该接口的具体差异必须先回写本页并审查，再改产品。

等待a片CI期间的[具体监管接口草案](2026-11-15-training-cycle-stop-supervision.md)选择stdlib asyncio父侧、原唯一reaper与必要的两帧codec共用，而非抽取一套selector。它仍待新的设计审查及b1实施后的前提复核，不继承b0通过。

原immutable输入本身不可读时无法证明目标身份；报告unknown，不承诺绕过同一可信存储故障通知尚未识别的owner。已获得目标身份后各通知不受writer／其他目标业务I/O牵连。所有操作使用原total remaining，耗尽仍收尾实际操作子树，不借新请求续期。

## 子节点与验收

|节点|完整交付范围|必要证据|当前状态|
|---|---|---|---|
|b0具体设计|本页调用、binding、锁顺序、native／远端边界及停止监管选择|源码／链接核对、新fresh-context设计两轴；不加纯设计测试|新的独立设计两轴approve／开放0／0；b2接口仍需另审|
|b1原最后gate|本地完整binding、三异步远端核验及四动作父许可；无总Workflow producer|原三字段兼容；完整binding错run／ordinal／input拒绝；真实晚RPC、registry／executor锁、stop在最终fsync／attempt／ack交错；原actor；SDK-free历史链|本地闭合：原r1完整127、r2较广32、最终r3相关19分别通过；最终安装／自身模板及新独立两轴approve、开放0／0；R1含深层JSON关闭，普通发布／自己的CI待|
|b2a必要监管整理|先固定实际共用接口，若现接口足够则省略；行为保持，独立记录|原预算phase真实子树／TERM／final与容量回归，无新停止语义混入|接口设计待b1后的实证|
|b2b停止fan-out|独立writer、各原owner通知与drain，供后继cycle用例消费|真实writer fsync及某目标读取阻塞，其他owner仍被精确通知；各子进程收尾；前轮release保留；Temporal不可达的本地真实结果|待监管接口，未实现|
|b3完整交付|每个产品片独立安装／自身模板／新fresh reviewer／普通发布／自己的CI；随后才接c1|实际安装来源及283、必要回归、精确发布与各自终态；不借a片结论|待b1、b2|

检查沿原`tests/test_training_submission.py`、已有SDK服务替身／实际native fixtures及进程接缝，Linux用例在fixture前skip。必要新增只是可揭示身份、并发、恢复和回收风险的检查，不复制全矩阵。安装和真实服务分列，CPU合同不认证业务训练、GPU、质量或性能收益。

逐步状态和原件见[本片交付](../delivery/2026-11-15-training-cycle-gates.md)。下一步先独立设计审查并闭合a片自己的CI；产品b1、b2各自完整审查发布。c1独立cycle进程／loop与queue、总Workflow、轮次索引和容量、c2公开交互、新CPU两轮、Q5.2据证重构、Q6及真实训练条件继续开放。

## b0独立设计结果

[新的fresh-context审查](../delivery/2026-11-15-training-cycle-gates-plan-review.md)需求／维护性两轴approve，开放0／0。核原12文件与tracked状态差异、十owner及原registry／executor、备份恢复约束；允许b1作为消费gate片，不把b2共用接口或c1 producer当作已交付。上述RPC位置和原锁不替换的约束由该源码审查明确补记。08:23 UTCa片自己的CI已可读，run43693023635／attempt1仍in_progress；产品实施门禁继续待终态与原reviewer续核。

a片自己的CI及原终核现已精确闭合；b1开始。另行的b2监管草案r3已新独立设计两轴approve／开放0／0，R1冷inspect截止仅设计关闭，接口在b1后仍需实证核对。完整父attempt使用`workflow_input_sha256`保存完整workflow input canonical SHA；原cycle raw input SHA不复用该字段。
