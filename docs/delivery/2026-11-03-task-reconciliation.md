# F3.4b：终态后外部 fence 对账的实施前调查

日期：2026-11-03。F3.4a已独立验收完成；本节点进入b1只读证据接口的准备实施，尚无本节点生产实现或验收结论。范围沿[F3.4总设计](2026-11-03-formal-task-acceptance.md)：明确写操作核原任务/run与实际外部事实，不改原workflow终态，不删除ledger，不以取消请求或空目录推断外部进程已停。

## 已核实的原生接口

`_Submission.submitted/lookup_run`可继续复用原创建、七合同、原始spec、固定run及submission memo校验。原`DevelopmentTransport.poll`只读返回原终态outcome；COMPLETED不等于成功，CANCEL_UNCONFIRMED/NEEDS_RECONCILIATION应保持原值。其他Temporal闭合状态未必有可成功读取的outcome，需与真实description分开表达。

`FileAdapter.fence(context)`以task_id/request_sha256不可变发布fence，然后仅枚举当前requests目录，对每个原job调用poll；缺失或无效receipt保留unresolved。该函数不读完整Temporal history，也不是系统进程或所有外部作业的扫描器。`IngressLeases.release`要求原tracker/owner/task/spec和证据摘要，保持单向释放且证据不可变。`agent_platform.ingress.release`便利函数仅接受REVIEW_READY或BLOCKED+confirmed；不能通过把原CANCEL_UNCONFIRMED临时改成BLOCKED来绕过它。

## 隔离反例及设计影响

原始证据`.ergora/checks/f3-task-reconciliation/adapter-fence-probe.py/json/log`：冻结FileAdapter、合法原spec的单个隔离stage envelope、无receipt时fence为confirmed=false；把adapter切到另一套空根，或仅删除该隔离envelope，fence都返回confirmed=true。探针未使用Temporal服务/真实作业，没有释放租约、修改生产实现或用户已有状态。

这证明不能把“当前目录未发现未决job”扩大为“原run全部可能提交的job已确认结束”。统一出口至少要核对原adapter根与登记的执行目录，并以固定原run的权威历史/已有job身份对照实际请求及可信终态receipt；已知原job的envelope/receipt丢失或配置根漂移不能当作零作业成功。仍需核SDK真实history结构、原活动取消与发布的竞争，再选择最小的原接口组合。不能为完成入口而复制第二套进程监控或从数据库删未知claim。

## 下一实施前检查

1. 核原闭合run中dev_submit的上下文、重试与活动身份，以及原envelope/job_sha/spec如何逐一对应；先用隔离反例证明历史job缺失、错误根、冲突回执仍保持未知。
2. 明确仅在原run已闭合后允许本操作；准备仍用当前revision/严格confirm和原task非阻塞锁，退出共享DB后才查询/发布fence，GET保持只读。
3. 若证据充分，保存真实原workflow结果与本次外部核对事实两份身份，以原IngressLeases合同决定释放；不伪造新的workflow状态。先调查现有可复用持久记录，再决定最小的意图/检查点/回执，未知恢复依原fence的不可变幂等语义处理。
4. 本节点须独立源码/异常/资源/最终发行审查；新两模板真实六阶段和worker重启仍分别由F3.4c/d/e验收，不因这项adapter探针通过而接管。


## SDK与目录来源补核

已安装Temporalio1.34.0的真实protobuf/默认converter离线往返通过（history-shape-probe.py/json/log）：dev_submit对应activity_task_scheduled_event_attributes、activity_type.name、activity_id及单个context输入payload，规范context摘要保持。原workflow.call以单个dict调用活动，context包含原spec/request/profile/stage，job_id由task+stage摘要稳定生成。该探针没有查询真实服务history；实现应使用lookup_run返回的实际SDK converter，而非硬编码默认codec，并对分页/完整历史及任务身份另验。

原setup.initialize默认将五类adapter根置于STATE子目录；已有adapter.json不覆写。原doctor检查模型、边界和端口等，但不证明adapter根与登记STATE一致。因此不能把doctor曾通过当作根归属证据。准备限定受支持的参考目录布局并校验原job证据，对其他根显式拒绝/保留未知；不自动猜根或把丢失请求视为未启动。还需考虑task级fence对后续不同run的作用范围；原run已闭合并不能授权停止同workflow ID的另一在途run，实施前应核当前run归属或明确拒绝这种情况。


## 最小实施子节点

|子节点|范围|验收及依赖|
|---|---|---|
|b1 原run外部证据只读视图|CLI `task external-status PROJECT TASK --run-id RUN --timeout 20`及同源GET external-status；原提交/spec/memo/run/闭合history，按原FileAdapter校验请求/可信终态回执和既有fence，明确缺失/冲突/未知；不发布fence、不释放租约、不另存运行状态|真实目录/原history身份反例、根漂移、已知job丢失、未知/损坏receipt、重复/截断history、并发读取、CLI/API一致、缺SDK环境；独立结构/性能/最终发行审查|
|b2 明确终态外部对账|复用b1证据边界；当前revision/confirm/原task锁，短DB准备后不可变意图/检查点，显式原fence与真实外部证据，沿原IngressLeases适用释放；原workflow结果保持|未知不虚假释放，正确幂等与中断恢复、额外run/错误scope拒绝、实际进程/原ID验收；独立新审查。b1完成后实施|

b1仅新增读取接口；完整F3.4b仍等待b2，不以GET已能读证据代替显式对账闭环。当前[b1实现与验收](2026-11-03-task-external-status.md)已接CLI/API和专用原生证据读取，连续历史/可信文件反例及P1孤立回执修正独立复审通过；a2349e8最终包59项/27CLI、精确两OS CI41597961138与独立最终审计均通过，b1已完成；本调查记录不替代该子节点的当前证据。

## b2原租约合同补核与实施顺序

在b1最终CI等待期间，只读核对原`agent_platform.ingress.release`及`dev_platform.ingress.IngressLeases`：前者仅允许REVIEW_READY或BLOCKED且原fence.confirmed；后者的合同允许协调者先保存自己的持久“已确认清理”证据再释放。release严格匹配tracker/owner/task/spec和证据SHA，重复释放必须使用原证据SHA，已释放claim不可重新打开。由此，b2不必改写原CANCEL_UNCONFIRMED为BLOCKED，也不需要复制SQL或新建租约库。

下一切片先落实以下闭环，再补c/d真实服务旅程：

1. CLI/API的明确对账/本地状态/按原意图恢复，复用既有revision/confirm、原task非阻塞锁及短准备事务；固定原创建/提交/run和本地owner，不发新workflow/signal，不重跑Agent或质量检查。
2. 组合b1的完整历史与两类job目录证据。原run须闭合且仍为当前run，根和scope冲突须在fence前拒绝；写前保存绑定原history job集合及原outcome的检查点。
3. 复用原FileAdapter的不可变fence发布，不采纳其空目录confirmed作为完整确认；发布后按b1的已知job、额外请求/孤立回执和可信回执/产物重新核对。缺失或损坏证据不释放租约。
4. 证据完整后先持久保存真实原outcome与本次独立外部清理事实两份身份，再沿原IngressLeases合同释放。原native release本就适用时保留其证据SHA和幂等规则；其他闭合清理使用本工具已保存证据。验证原cli-ingress归属，不能通过删owner/ledger或伪造结果规避。
5. 恢复必须核原run/history/outcome、原fence和已保存检查点，严格处理发布前后、证据保存前后、SQLite提交前后及丢父响应；明确原不可变fence的幂等范围和人工修改冲突，不能凭本地prepared/requested宣称外部已停。GET本地状态及external-status均保持只读。

b2尚未实施；需独立记录具体字段/恢复合同与有意义的中断、错误scope、其他run、缺失/孤立证据及跨项目并发反例。此处是原接口可复用性调查，不把b1的包/fixture或旧L0结果转作b2实际通过。

## 后续所有者与调用边界补核（V2/V3审查等待期间，仅调查）

实际`reference._task_operation`已经为reconciliation组件发送`operation='inspect'`，并统一负责登记Linux解释器、环境、严格JSON输入、超时及原生错误传播；b2可以沿同一组件扩展明确准备/调度/恢复操作，无需新建shell/进程执行器。`tasks._native_prepare`继续拥有短DB准备事务，远程阶段应在其返回后执行。

`_Inspection`实例已经持有原submission/creation/spec/adapter，`run()`返回原outcome、history job集合摘要及逐job文件事实；原FileAdapter.fence只需要原task_id/request_sha256。b2可组合这个实际所有者并在发布后重验，不必另抄history/receipt算法、暴露新通用插件层或为了发布fence重复构造另一套上下文。持久读取/路径/尺寸和task锁应复用`_Creation`已有接口；是否新增私有协调类只按本操作的完整恢复算法所有权决定，不虚构第二调用者。

原fence按task/request发布，不含run ID；本地task锁只串行遵循本协议的控制路径，不能声称原子占有远端workflow ID。实施仍须保留“原已提交闭合run且没有已知后继”的前置检查、发布后复核及冲突保持未知/不释放，并明确原task ID不可被绕过本协议的其他客户端重用。这里没有实施b2、修改冻结文件或验证新的外部清理结果；具体公共字段和恢复检查点仍由下一功能切片固定。

上述为实施前调查快照；当前 [b2实现与验收记录](2026-11-03-task-reconciliation-write.md)已固定公共接口和四份恢复记录，并进入实现/发行审查，不继承调查探针的验收结论。
