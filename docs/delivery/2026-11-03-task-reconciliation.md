# F3.4b：终态后外部 fence 对账的实施前调查

日期：2026-11-03。本节点尚未开始生产实现；当前活动仍为[F3.4a最终验收](2026-11-03-task-export.md)，不是本节点已通过的声明。范围沿[F3.4总设计](2026-11-03-formal-task-acceptance.md)：明确写操作核原任务/run与实际外部事实，不改原workflow终态，不删除ledger，不以取消请求或空目录推断外部进程已停。

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
