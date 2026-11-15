# c1：独立训练循环进程与总Workflow

日期：2026-11-15。产品准备基线为b2b本地固定`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`；该片本地两轴已闭合，普通发布及自己的CI另按原门禁。本文细化[已批准具体合同](2026-11-15-training-cycle-controller-contracts.md)第2、4、5节及c1实施节点，不替换其记录／权限／时钟合同。当前仅准备；没有新的controller producer、worker或总Workflow运行结论。kernel专家保留在v3路径。

## 目标与既有边界

顺序消费同一出生授权中至多32个既有候选；由实际Temporal history保存顺序及恢复位置，每轮仍调用原start／resume、显式execution、原accepted archive与rounds索引。只接受完整原测量，不生成实验、不晋升baseline、不批准release、不改变算法／模型／数据。保留原同意、单次attempt／launch、连续clock及独立人工release。

b2b的`stop_live_controller`已经把独立writer／逐owner通知／drain／执行链观察隔离到S-H；本片复用它，不复制进程driver、reader、reaper或停止协议。原`training-budget-worker`的PID／event loop／ExperimentWorkflow注册保持；新的cycle服务拥有另一个PID／event loop，普通活动与stop活动各有自己的Worker和并发配额。全部业务文件、SQLite、锁、fsync及同步原应用调用只能在被监管H内，SDK父loop只作异步监管。

|现有owner|本片可变内容|稳定合同|
|---|---|---|
|training_execution_protocol|总投递原件的共享生成／完整验证；新增普通operation所需完整身份与原clock界|stdlib-only；已有schema／停止封套与GATE_SOURCES key集合保持，不导入State／SDK|
|training_cycles|原Path读取、明确总投递准备和原件观察；按原事务边界冻结意图|不反向导入worker／submission，不持SQLite跨RPC，不保存本地可变current-round|
|reference_training_worker|SDK总投递／对账，普通S-H应用操作，独立cycle入口及确定性总Workflow|原budget入口／serve保持；worker自身仍在现有source pin内；同一原processes.run reaper|
|reference／services|真实cycle argv、独立服务与明确停止；复用现有命令构造及Supervisor|不复制SDK投递／领域状态机，不隐式替旧项目启动自动执行|
|training／training_rounds／evidence／runtime|由H组合原接口；按原完整链和实际phase判定继续|各原件／评分／批准／归档权威保持；原10MB索引超限整体拒绝|

新增函数先沿上述实际caller固定职责；优先复用现有生成／验证函数和库，不增加插件总线或为了行数拆module。若现有pure字段验证需从“读文件”中提取，同片先证明原算法／错误保持，不能另写一份近似validator。

## 实施与验收节点

|节点|完整交付物|必要验收|状态|
|---|---|---|---|
|c1a 总投递原件与SDK对账|完整intent→持久attempt→唯一start→固定run receipt；只读status／reconcile。先核schema2原ready、原revision／clock／stop；共享原controller intent生成／验证|原同意不升级、slot只消耗一次、RPC外无SQLite事务；真SDK编码服务替身上的accepted／lost reply／NOT_FOUND／冲突输入与memo／队列类型；恢复只查同ID，不重发／跟随新run|c1a1／c1a2已本地及固定提交两轴通过；原件准备d1fcfa5、SDK投递／对账f00bfdf，各自普通发布／准确CI排队，见[投递计划](2026-11-15-training-cycle-dispatch.md)|
|c1b 异步普通操作与真实服务边界|在原operation owner中接inspect／start-or-reconcile／request-execution-or-observe／collect-round所需身份；非阻塞cycle入口，独立normal／stop Worker与配额|完整原controller run由SDK activity身份取得并经H核原记录，不接受外部候选列表；真双服务不同PID，普通H锁／fsync阻塞时stop queue仍可运行，取消仍回收实际spawn／后代；无SDK的core观察保持|c1b0一次普通窗口已本地固定3947b1e；接续[跨调用owner生命周期c1b1](2026-11-15-training-cycle-owner-lifecycle.md)设计／实证，再独立cycle服务及配额。自动派发仍关闭|
|c1c 总Workflow与每轮执行|可被标准SDK sandbox重新导入的TrainingCycleWorkflow，确定性顺序／timer／query／stop；所有业务经c1b活动|真实Temporal的原input／memo／固定run；副作用activity maximum_attempts=1；原compute／control timeout导出SDK截止，非正不派发；重启／丢activity回复不重占start／launch|待真实c1b入口及stop配额，不推迟这些边界到公共交互|
|c1d 测量接受／索引／容量|原accepted archive＋durable stopped＋实际Workflow phase＋不可变rounds追加，只有全部原绑定通过才继续|至少两候选的顺序／原baseline保持；前轮release窗口保留；phase／gate／reap交错、索引超限／项目漂移、32KiB封套与history界；只报告真实所验容量|待c1c；不引入第二账本或新的质量／收益评分|
|c2 公共入口与交接|CLI／HTTP／services薄入口，明确authorize／start／status／stop／reconcile；手册／页面使用已验用例|安装后完整操作；Temporal不可用先返回实际本地停止分支，未知不自动重试；旧schema1不启用自动循环|后继片|
|d 可信CPU两轮|公开一键脚本、独立正确性oracle、原runner／gate与完整证据|真实Temporal正常两轮或有证据提前停止；lost reply／进程重启／预算／取消及全部收尾，保留旧负gate例的原范围|后继片；不认证真实GPU／ML质量／性能收益|

c1a–d各自可细分为行为保持整理和完整行为片；每个实现片分别记录实际source／wheel／安装身份、适用原接缝、Ergora自身审查模板与新的fresh-context独立两轴审查，修实证问题后才固定提交。前片本地验收、新独立两轴与固定提交闭合后，后继可先在本地实施／验收；若前置CI发现实际修正，先接续并重核基线。普通推送仍逐片等待前置准确CI及相应独立终核，不借另一候选的成功。

## c1a需要先固定的投递细节

原`CycleAdmission.controller_intent()`已经负责完整intent字段，`bind()`核原attempt／receipt；生产者须共用该生成／验证责任。具体字段沿原合同，不新增随机workflow ID。原attempt在真实start前无覆盖发布并同步，拒绝重复与冲突复用；有attempt而无receipt时，只查同ID的完整started input／describe与started memo、类型／queue，NOT_FOUND保持unknown。服务明确拒绝与不确定网络错误分开，部分／损坏原件不修复。

总Workflow可能先于客户端receipt落盘开始执行；必须在首次子start前闭合这个竞态。可由原唯一attempt及已认证的固定run在一次只读对账中补同一receipt，不能把“尚无receipt”解释为重新start或允许未绑定子操作。对已经关闭的总run，status／reconcile仍应读取原完整history／memo；现有`lookup_controller`强制RUNNING是四个最后动作的执行gate，不能放宽它来迁就历史观察。只读总投递查询与该最后gate分别持有相应状态语义，完整input验证尽量复用原runtime owner。

## SDK／进程的实际接缝

标准Temporal SDK sandbox会在新上下文中按workflow类的module和name重新导入，并要求该类仍有完整decorator定义。core导入worker又必须不要求可选SDK。因此不能只在serve局部造一个未导出的装饰类，也不以关闭sandbox、改用线程或扩大同一loop配额替代真实边界。先用实际已安装SDK验证可选装载、重新导入和Worker注册方式，再在既有被pin的owner中固定最小实现；若现有owner无法内聚承载，明确记录证据并复审源码身份方案，不暗加未被pin的新执行依赖。

新的普通请求必须绑定原controller workflow／run、intent SHA和ordinal，结果只传完整typed事实及原件引用。初始化inspect仍只有只读固定观察截止，拿到完整原clock后不重开窗口；普通动作使用原compute与control timeout较小值，停止使用原total。取消总Workflow时通过独立stop queue执行同一b2b用例；已接受旧轮不统一Temporal cancel。server terminate不保证cleanup，手册保留本地停止／原run对账流程。

实际源码依据包括原`reference.training_submission`／`_training_process`的解释器边界、`training._submission`的事务范围、`Execution.request`的完整显式确认、`training_rounds.create`的完整嵌入和10MB拒绝、`services._prepare`与原worker命令构造。实现前逐个重核实际caller，不把本表当作功能已经存在。每步更新[交付记录](../delivery/2026-11-15-training-cycle-workflow.md)。

## 进入c1b／c1c的明确门槛

c1b不能把现b2已知mode的原total监管直接当作普通操作截止。普通请求在spawn前固定一次BOOT操作截止，约束为原compute remaining与原control timeout的较小值；父侧pipe／wait、S的实际stop_requested、H最后动作及post-stopped结果读取均消费该同一窗口，并每次沿原clock保守校验。poll、取消、内部重试或恢复不能重置这个operation窗口；原授权／compute／total不续期。冷inspect与停止模式继续保持b2自己的既有截止。

c1c先实现首轮生命周期及可恢复停止；在c1d完整原archive／实际phase／durable stopped及rounds追加全部核过之前，绝不能派发后继候选。未取得任何一项即保留needs_reconciliation或原明确终止事实，不设置“暂时接受”分支。只有c1d闭合才开放有限顺序继续。实际标准SDK sandbox装载／Worker注册及独立双服务的验证也必须早于自动派发；准备探针不转授这些产品结论。
