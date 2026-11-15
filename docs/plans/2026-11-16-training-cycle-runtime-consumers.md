# c1b2b／c1c：训练循环的后续真实消费者

日期：2026-11-16。状态：源码调查与实施细化；[具体r2设计](2026-11-16-training-cycle-execution-consumer.md)已独立两轴通过，**尚未实现**。承接[已批准控制器合同](2026-11-15-training-cycle-controller-contracts.md)与[c1实施顺序](2026-11-15-training-cycle-workflow.md)。c1b2a服务正在处置独立审查并做真实验收；本页不越过其终核门槛，也不实施等待用户讨论的WA通用设计关卡／Repeat。

## 当前消费者缺口

现有四活动为inspect／start／reconcile／stop；服务本身不注册正式TrainingCycleWorkflow。它们保留完整H原件引用，但引用中的snapshot不能由确定性Workflow读取。当前SDK封套的observation只有原total剩余与时钟观察，不能据此派生compute∩control截止；candidate父侧结果也不能用一个observed状态冒充已提交／已执行／已接受。

原`Execution.request`已经拥有完整revision／start intent／固定run／native request SHA确认、原QUEUED phase核对、父共享许可及不可覆盖request。原预算根的`Execution.admit`消费一次launch并驱动原executor。后继应接这两个原owner，不能另建launch路径或让Workflow持训练进程。原`training.status`／`ExecutionRecords.observe`分别拥有真实Workflow phase与durable stopped；两者不互相替代。原evidence／rounds继续是接受与索引权威。

## 最小实施顺序与验收

|节点|实施责任与范围|验收门槛|
|---|---|---|
|b2b.0 具体活动结果合同|在原protocol／worker中明确Workflow真正需要的小型调度事实：原compute／total剩余、control上限、当前ordinal及精确submission／execution观察。完整原件仍引用，不把snapshot或另一个候选列表传进history|原六字段身份、来源认证、32KiB含metadata不变；假阳性observed不能成为execute或后继许可；合同经fresh设计两轴核对后才实施|
|b2b.1 request-execution-or-observe|H从同一controller／ordinal的原intent、receipt、owner、native request重建原确认，调用同一Execution.request；已有request／launch只观察；SDK父loop不读业务文件|真实原run QUEUED正常一次request；丢completion、重投、并发、坏原件、stop／clock／项目漂移不补request／launch；原slot与reaper保持|
|b2b.2 有界原运行观察|H复用原runtime lookup／phase与ExecutionRecords，向Workflow提供足够的typed事实及原件身份；不在此提前接受测量|phase未知／漂移、结果先于reap、reap先于phase、RPC失败分别可辨；正常观察不通知已交接root、不产生执行机会|
|c1c.0 可选SDK与标准sandbox|沿原被pin的worker owner固定可重新导入的正式decorated类；core导入不要求SDK；使用SDK建议的明确pass-through导入边界|真实SDK默认sandbox重新导入／Worker注册，不用关闭sandbox或线程代替；原budget进程／queue不变|
|c1c.1 确定性首轮与恢复|总Workflow只消费原六字段；history记录inspect→start-or-reconcile→request-execution-or-observe→原状态，普通截止从原compute∩control观察导出；无本地clock／文件读取|真实Temporal首候选完整生命周期；重启／丢reply／取消／未知只对账，无重复start或launch；后继ordinal仍关闭|
|c1c.2 独立停止与取消|signal／cancellation进入已验stop queue；完整stop事实与Workflow关闭分别保存；server terminate不称回收完成|normal忙／worker重启时停止可恢复；已接受旧轮不统一cancel；total尽／服务不可用显式unknown并提供本地对账路径|
|c1d 接受与后继|精确原phase、accepted archive、durable stopped、完整rounds追加全部闭合后才继续原下一ordinal|两候选保持同一baseline；任一否定／未知／容量／索引失败不派发下一轮；真实训练与CPU合同验收分列|

## 设计复核前还需固定的细节

1. 首次冷inspect尚不知道原预算。必须明确其固定BOOT观察与SDK调度截止如何衔接；后续不能借轮询刷新同一次compute窗口。SDK timer只帮助调度，最后H／native gate仍核原BOOT时钟。
2. 活动结果必须能让Workflow在历史中分辨“原start已确认”“仅未知对账”“原execution已请求／launch占用”“实际phase与durable stopped”。先定义真实消费者所需字段与版本，再扩展原封套，不根据H文件路径猜状态。
3. cancellation／fatal期间SDK timeout与实际资源cleanup是不同事实。规定停止调度的剩余时间及失败时返回的unknown，不能以SDK取消完成替原S/H收尾；不能在original total尽后重授一个效果窗口。
4. 自动execution的actor沿schema2出生同意，从原记录重建，不由业务请求自述confirm或run。重读来源与最后gate保护不同时间点，不能为了减少重复字段检查删除持久身份验证。

每个节点分别更新PLAN／交付、保存准确源码／新安装／真实服务证据，并使用Ergora自身模板与fresh独立两轴。服务片的包、回归或测试Workflow不作为这些新消费者已存在的证据。
