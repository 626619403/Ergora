# b2b：独立受监管训练循环停止操作

日期：2026-11-15。本地基线877e1e4f7397731915c36b82f335efeaab3854dd，分支refactor/architecture-foundations。承接[已独立通过的具体监管合同](2026-11-15-training-cycle-stop-supervision.md)和[b2b0只读读取整理](2026-11-15-training-cycle-offline-reader.md)。前两片已固定本地／独立通过，远端仍等待前置43d自己的CI准确终态；限额前不重复查询。

本片完整交付原设计的operation及停止fan-out，仍不创建总Workflow、worker queue或公共CLI／HTTP。kernel专家保留在v3路径。

|原owner|本片责任|稳定边界|
|---|---|---|
|training_execution_protocol|纯stdlib完整operation请求身份及原clock／固定冷观察截止，复用PhaseFrames|不引入State／SDK、新parser或reaper，原budget两帧保持|
|reference_training_worker|异步创建、stdin／stdout／stderr与wait独立task；每个S经原processes.run监督一个H；具体停止操作与fan-out复用原submission／cycles读取|父loop无业务文件／锁／fsync；取消保留spawn handle并实际收尾；匹配stopped后S不再spawn|
|training_cycles|保持原Path只读_load与领域原件，由worker调用生成snapshot及执行停止分支|不创建State、补造记录、重授权、重开clock、查询当前SDK／源码来清理旧owner或统一取消旧测量轮|

先冷inspect，spawn前只计算一次1至60秒BOOT观察截止；返回完整原authorization／policy及有序候选索引才启动效果分支。后续全部使用同一原total；身份／clock未知或已尽不新启动。每个S验证原父进程身份及原截止，H在效果前重读完整原件。停止帧先于最后结果读取；S若在stopped后卡住，父侧按同一冷截止或原total回收S并保留unknown。

每个请求／结果封套上限32 KiB，stopped首帧65,536B；超限拒绝，完整原材料留本次独立operation目录。执行链完整观察保留文件和SHA，响应只给原typed事实与引用。停止可见、持久、父许可排空、精确通知与executor停止分列，不从进程退出、future取消或通知成功推导其他结论。

|节点|验收|状态|
|---|---|---|
|b2b.1 请求与监管|实际stdlib完整身份、两帧顺序、原父watchdog／原clock、异步pipe与取消收尾|已置原worker／protocol；源码r2、core真实inspect、安装相关接缝已验，独立终核待|
|b2b.2 具体停止分支|只读inspect、独立writer／逐owner精确通知／drain与执行链观察；全部效果前原件重核|真实两个原owner并行阻塞及完整原snapshot通过；通知／清理分别观察|
|b2b.3 运行验收|真实两个原owner，writer同步及一目标读取阻塞时另一通知到达；冷stopped后读盘卡住；spawn取消；错误controller／PID；core无SDK；原clock耗尽、原人工release和所有operation收尾|源码r2为22通过，r3归档身份／无当前安装与原manual-release两项通过；安装r1其余30通过，同一产品通知事件修正r2一项通过，原失败保持；38已知actor活匹配0|
|b2b.4 交付|新非editable安装／283／依赖／架构；自身原模板、新fresh-context产品两轴；按前片门禁普通推送与自己的CI|两新安装各652／283／依赖通过；最终自身原模板43.807秒approve；新的fresh-context最终本地两轴approve／开放0／0；普通发布／自己的CI待，不借原设计或前片产品批准|

每步见[交付](../delivery/2026-11-15-training-cycle-stop-operations.md)。完成后接c1总Workflow与独立cycle进程／普通及stop配额，随后c2公开交互与新的真实CPU两轮；实际GPU／业务训练与质量／收益条件保持开放。

## 源码r1后的职责修正

原架构检查实际发现cycles反向导入submission／worker形成环。停止分支调用原_Submission及ExecutionRecords，本来就在原worker边界依赖集合内；因此将本片新snapshot／目标读取／H操作／fan-out整体置于已有worker，继续调用cycles的原Path读者，不新增module／反向导入／注入总线或复制validator。cycles本片保持基线字节，异步父loop仍不碰业务存储。原架构检查保持，修正后的实际检查另存r2；审批与验收不继承r1局部通过。
