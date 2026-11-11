# F7：逐项目工单来源、任务映射与显式回写

入片基线 `0252dec5c41be1c1f6f533d86d8f32d30d178ce3`，分支 `refactor/architecture-foundations`。接续[总计划第8节](2026-11-01-all-in-one.md#8-p1低代码更多真实工具与演进闭环)的F7／DS4与[C6d](../delivery/2026-11-11-architecture-platform.md)。C6d已普通提交／推送，独立精确Git与一次官方HTTPS Ref通过，自己的CI42968978850第三样本已终态成功且原独立评审完成精确原件终核；本片可继续本地与交付工作。

## 现有路径与选择

一个业务项目拥有一个仓库／工单命名空间；任务分支隔离代码候选，工单属于仓库或GitLab项目。项目修订、工具选择、有效配置、CLI／HTTP保护沿 `projects / components / bindings / web`；正式任务仍经 `tasks`、原creation／submission和Temporal运行，不增加工单调度器。

冻结Symphony的 `tracker.py` 已有状态／label读取和有限label迁移，但只有单类provider分支，未提供完整工单正文、源版本、第一方项目用例或并发写入CAS。本片保持283冻结文件及旧Symphony配置原样；新的GitHub／GitLab Adapter只负责其原生协议，映射、授权与副作用恢复由第一方用例持有。优先调查官方REST与现成SDK；首片只需单个GET，依赖取舍和官方证据另存调研笔记。

已评估入口准入：当前正式提交在专用进程调用冻结 `task_action`，保持doctor→项目policy／可信checks→connect→ingress.claim→start。其旧doctor额外依赖A2A／MLflow等，不能当成新的工单读取前置。F7a不需要参考安装、模型、A2A或Temporal，直接使用普通项目和只读来源；在F7b出现真实正式派工消费者时再设计版本化Input的窄准入，保持旧入口、policy／claim／candidate与未知恢复，不在Web全局替换doctor，也不另建健康状态机。

## 分片与验收

|节点|实现／复用|可验收出口与状态|
|---|---|---|
|F7a 指定工单读取|项目增加描述驱动tracker绑定，默认manual；GitHub／GitLab本族ABC和局部映射；公共 `issue show` 用例供CLI／HTTP消费|本地出口与28文件ready独立通过；9f01007已精确交付，自己的CI42974715330七必要步骤与原评审终核通过。普通新项目无需参考运行时即可读指定number／iid；命名空间、全局native ID、原更新时间／ETag和响应摘要分别保留，正文仅为上下文。匿名公共读取或外部token_env；无自动列表／接单／写回。固定源、无redirect凭据、1MiB完整读取上限和I/O超时；本地确定性HTTP夹具验证两实现／边界／CLI／HTTP，项目／任务／run不变；实际自身模板、新独立两轴、自己的精确交付|
|F7b 来源到任务的显式映射|[F7b.0](2026-11-11-issue-mapping.md)已精确交付3c4ef39；[B1来源任务](2026-11-11-issue-dispatch.md)及[B1c窄准入](2026-11-11-source-task-admission.md)已精确交付472ff60，自己的CI43007648352双OS七必要步骤与原评审终核通过。一个工单可对应多个task／原creation，新工作修订用新ID，复用原ID／意图／ingress|去重／重放／工单更新不覆写原任务或批准；工单正文不改变权限／可信检查；源不可用与绑定修订有明确恢复。已完成所选依赖准入、原未知恢复反例及真实混合来源六阶段验收，实际范围见B1c记录；不建立第二套正式调度|
|F7c 显式状态／关联回写|复用原候选export与run身份，保存回写意图／attempt-before-send；[C1](2026-11-11-issue-writeback.md)先实现一条固定中性comment／note及原生观察，原生导出衔接、最终r2安装52项及自身聚焦approve已过，完整28文件独立两轴／本地出口通过、开放0／0，b5ee397自己的CI43015595781及原评审终核通过、精确交付终结；[C2a标签](2026-11-11-issue-label-writeback.md)源码67项／安装117项通过，自身approve与最终r2包446／283通过，完整独立及精确26Git通过，93b538f自己的CI43023048173双OS七必要步骤与原评审终核通过，精确交付终结；[C3a只读远端候选](2026-11-11-candidate-observation.md)已实现，r1安装196通过／1跳过，独立两P2修正后r2包446／283、受影响49项与文案断言修正后原回归1项通过；自身首审发现SP3对象replacement，已真实red并最小修正，r3新包446／283及受影响18项通过，聚焦自身164.79秒approve／五scope完整读取通过，完整29文件独立两轴0／0及本地出口通过，SP1–SP3关闭；精确交付继续；GitLab标签严格能力保持unsupported，branch发布／PR／MR后续另片|读后比较仍有竞态；若API无写CAS必须如实说明。人工修改／部分完成／响应丢失可复现，unknown先查原生事实，不能不确定重发；不自动close／merge，不把标签当审批|
|F7d observe与用户旅程|按真实需求增加有界分页／稳定Trigger去重和来源页面；描述驱动Source／Channel；复用原任务页面与记录|先observe预览，机器人／重复事件不重复派工；后续消息只追加上下文。本地模式与原Symphony保持；三域相关旅程、手册／架构与独立收口。真实账号写操作另需明确业务授权，默认只用本地夹具|

F7a不新增持久表、任务合同、调度器、webhook服务、真实账号写操作或GUI专页。现有项目绑定表单可呈现新tracker描述；完整交互页面属于F7d。只读观察不是冻结任务、owner批准或工单处理完成。

### F7a当前验收进度

|出口|实际状态|
|---|---|
|原生读取与项目归属|完成：两Adapter／CLI／HTTP、固定项目快照、完整正文／摘要和边界；source159项通过|
|发行包与兼容|完成：后补r2非editable包442文件、两RECORD／283冻结；安装28项12.79秒及reference verify通过|
|现有绑定页面|完成：manual默认、两种来源保存修订／reload读回；13分段检查／57原HTTP／3本地tracker GET与清理通过；两driver失败保持|
|真实自身模板|完成：228.07秒approve／19附件、五scope完整读取；后补字段／边界与公开材料不在原模型范围|
|完整独立两轴|完成：[新完整fresh-context两轴报告](../delivery/2026-11-11-project-trackers-review.md)，Spec／Standards开放0／0，历史P3／附件计数修正已关闭；后补字节不借原模型判词|
|精确交付|完成：28Git对象／ready及既有SSH远端同完整9f01007；自己的CI42974715330官方run／两job原HTML终态Success，Linux三／Windows四必要步骤成功，原评审终核通过；两REST403及原In progress保持，未取得成功终态REST／全job日志|

## F7a职责、检查与记录

- `issue_backends` 是GitHub／GitLab本族的构造／读取／认证诊断Interface；实现内部保存endpoint、headers和字段映射。`bindings`只委托配置验证，`tools`只消费诊断，`issues`只调用同一读取Interface，不按厂商分派。
- `issues`拥有项目有效配置快照与观察结果；CLI和HTTP是两个实际消费者。`components.json`继续拥有可选工具和配置描述，JSON Schema拥有可交换观察格式；不复制前端表单或另造DSL。manual保留无来源的本地工作方式，旧缺字段项目按原兼容规则解析。
- 验证面向可静默出错的真实合同：GitLab全局id不混作iid、嵌套namespace编码、固定项目快照、完整正文／变更摘要、PR拒绝、无凭据redirect、外部错误与超限拒绝。避免为每个普通参数或普通异常堆叠同构测试；不改既有CI。
- 原件放持久忽略目录，公开记录在[交付记录](../delivery/2026-11-11-project-trackers.md)与本计划；每节点更新[PLAN](../PLAN.md)。保留基线、包身份、实际网络／夹具／模型读取范围与失败；文档、平台和真实服务分别记账。

后续仍按总计划推进F8／F9／F10和G1；第二后端推理、GPU、WSL2和PUB1许可证等原未验／维护者事项不借本片关闭。
