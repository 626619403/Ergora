# 原六阶段轮询的历史大小修正

承接[第二轮重构失败](2026-11-13-refactoring-journey.md)，产品基线`e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`。相邻[stdin修正](2026-11-13-supervised-stdin.md)独立保留；本片不改变task/run、完整输入、原预算、审批、候选或调度归属，不通过提高服务历史上限绕过问题。

## 复现与诊断

原第二轮历史为1,638事件／70,666,291B JSON，SHA256 `2d6798714a8208aa7fe189115218f3b8d0a88e5cf7f7e0d04f30d77d03386866`；末事件由history-service以`Workflow history size exceeds limit.`终止。原task／预算保持，未确认cancel。

原件按SDK活动输入解码后，9次submit共2,029,106B；210次poll共47,991,832B，单次最大229,547B。同一批poll若只传`task_id`、`job_id`、`job_sha256`合计34,650B。该投影仅用于估算输入重复量，未称整体历史已缩至这一大小。完整材料已在原不可变job request中保存，逐次重复并非执行完整读取所必需。

依次检验三个可证伪假设：

1. poll重复完整job是主要增长来源。新真实Temporal检查应在原实现发现poll包含完整context，修正后只记录原身份引用；完整submit和材料仍相同。
2. 活动结果或query是主要增长来源。若如此，压缩poll输入后的同等待历史仍会接近原增长量；比较相同活动数的输入与实际历史。
3. 只有长任务事件数触发限制。若如此，同样次数的小引用轮询也会按原速度接近限制；保留原事件数和服务终止原因，不能把字节大小与事件数量混为一谈。

## 实施边界

复用`reference_workflows`中的原预算workflow和原work-delivery活动；仅v9／v10发送端使用SDK patch marker `ergora-budgeted-poll-reference-v1`，将poll的完整job投影为原身份引用。活动端从自己版本的trusted request namespace加载原不可变envelope，核完整身份与摘要后沿原receipt／review验证路径处理。旧完整job输入继续沿原路径，旧历史重放单独验证；不改283冻结参考文件，不另建材料服务、缓存、预算、任务版本或调度器。

新增代码留在原workflow／activity owner；不引入新的生产Module或抽象。读取原trusted request的必要校验保护替换／损坏的原件，不能从引用获得新的权限、输入或预算。原submit仍记录完整context，离线evidence入口继续以该原事件校核完整envelope。

|节点|验收出口|状态|
|---|---|---|
|H0 反馈循环|真实Temporal原生产workflow轮询重复材料的red；保存原历史输入统计|真实red-r2为1 failed／14.95秒，明确发现额外context；原red-r1因把轮询次数写死为2而先失败，按配置修正测试后再确认产品red，原件保留|
|H1 修正|紧凑引用、同一trusted envelope、原review验证；旧完整输入兼容|原owner两接缝已改；同一真实回归1 passed／14.97秒|
|H2 验证|同一真实回归变绿；预算／停止场景、原历史重放、替换原件拒绝；隔离包身份|源码9项／99.06秒通过（8真实Temporal场景及1原活动材料／回执检查）；原r1的1,253事件、原r2的1,638事件以新源码重放均通过。新包497产品／两RECORD／283及安装9项／103.69秒通过，同安装对两原历史重放亦通过|
|H3 独立审查|本项目自身模板及新fresh-context两轴；原件和最终文档核对|自身原结构模板42.719秒approve／两源码全文内联；新fresh-context两轴及r3／安装／原重放／模型原件补核通过，Spec／Standards开放0／0|
|H4 重构与交付|新独立A2 task／预算真实完整旅程、原ID恢复及清理；普通提交／远端／本候选必要CI|第三轮REVIEW_READY／9 job／7会话、原ID恢复／重放／导出复验／清理已补核，新独立A2评审中；远端与本候选CI仍开放，前两轮失败保持|

本机checks中的`workflow-poll-history/diagnosis-r1.json`保存统计。Windows、跨机器材料存储、无限期任意数量事件不由本片保证；本片解决可定位的重复大输入，不把一次短回归称任意长任务已经验收。

H1只改`reference_workflows.py`，测试沿原`test_budget_workflow.py`扩展：真实SDK历史检查原poll引用与完整admission；活动接缝检查缺receipt、原完整job与新引用的同一失败receipt、原材料被改后的拒绝。独立新task／budget之前的历史恢复不读取或启动模型，不改原TERMINATED或BLOCKED结果。旧历史重放使用原始字节，未以新历史替换它们。

隔离安装从上述基线仅叠加本片两文件及stdin前置片两文件；排除暂存B2a资料和测试。wheel SHA256 `85e20a342361f8fda1233f607dc94679364a0691b0b5452bb6b274648d117ab7`，497产品文件等于隔离源码与安装目录，wheel／安装RECORD及283参考文件已核；源码验证为Python3.11，安装为Python3.12。安装检查9 passed；105.443秒为包含控制进程启动的外部耗时，不借前置片旧包结果授予本片安装成功。

同一安装的原structure-review模板实际Codex会话交付两份产品／测试文件全文41,202B，42.719秒返回approve；原结果SHA256 `85c7a5be3d0252c884160063856503025eaf621ffa982e136857f6f3fc57864a`。输入／协议／stdin与最终原件由新独立评审核验，不把聚焦模型审查扩大为全仓库或Windows运行通过。原第二轮已经由原公开reconcile和原executor完成排队job／fence／claim收尾，记录在[A2交付](2026-11-13-refactoring-journey.md)，没有用本片修正改写旧run。

[独立审查](2026-11-13-workflow-poll-history-review.md)已由新上下文的Spec／Standards两轴完成，并补核r3四文件身份、497三树／两RECORD／283、两原历史重放、模型输入及原结果，开放finding为0／0。该判词关闭H3的代码／证据审查，不关闭新A2实际成功、Windows／候选CI或远端交付。当前源码和包与被审身份相同。

后续[A2第三轮原件](2026-11-13-refactoring-journey.md#第三轮原件补核)记录完整成功历史623事件／6,111,384B，61个poll输入均为三字段引用、合计10,065B，原SDK patch marker存在。该run拥有独立task／预算，与原第二轮时长及轮询次数不同；不把整体历史之比当严格性能对照。七次实际会话及完整材料、原ID重启、精确候选导出复验／handoff、9 owner／7槽与claim收尾已补核，新的独立A2评审继续。代码／安装／自身模板与本片独立审查出口通过；普通提交与精确候选CI另记。
