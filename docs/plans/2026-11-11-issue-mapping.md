# F7b.0：工单上下文快照与显式任务关联

基线`9f010079126f374c01272ecf2f0ec85284e4e2cc`，分支`refactor/architecture-foundations`。承接[F7分片](2026-11-11-project-trackers.md)，F7a已普通提交／推送并独立核精确28Git对象与一次既有SSH远端SHA；一次官方HTTPS Ref及首次CI REST均限流403，原件保留；官方run／两job原HTML已终态Success、七必要步骤经原评审独立终核通过；原REST403与In progress保留，前片精确交付已终结。

## 明确范围

普通项目可显式capture当前工单，保存完整不可变上下文快照；按明确快照SHA与已发布原task creation意图SHA建立操作者声明的上下文关联。一个工单／快照可以关联多个task及其不可变创建版本，重复同语义操作返回原记录。工单更新只生成新快照，不覆写旧任务、批准或关联。旧task／登记不含API host，本片不证明原生工单与旧task同一来源，关联不是接单去重、派工、授权或任务通过；F7b.1先解决版本化来源／窄准入设计与反例后才允许派工。

不改283冻结参考文件、正式v1–v6、doctor／policy／ingress／memo／attempt恢复，不增加调度器、外网写入、自动轮询或GUI专页。旧入口保持，F7c／F7d仍分别实现回写／observe和页面。

## 所有者与存储决策

- `issues`持有capture／snapshot／关联用例，复用F7a原读取与固定项目快照；CLI和HTTP共用，无上层厂商分支。已有`tasks.creation`核目标published状态、原intent／compiled SHA及created_revision，不复制参考创建验证。
- 为快照和关联增加专属SQLite表，采用原`State`的显式v2迁移、备份、事务与跨平台文件锁；不借用研究／记忆表，不建立另一套文件索引或关系数据库。保留v1历史布局，并将所有表的writer fence升级，拒绝已打开旧writer。原`backups`已按当前schema与整库身份工作，不新写备份器。
- 快照的稳定payload固定完整F7a观察（除本次observed_at）和当时tracker绑定；凭据仍只保存变量名。内容SHA与首次观察时间分开：重复同payload返回原快照／first_observed_at，本次GET时间留在capture回执。读取已保存内容不要求当前凭据、binding或参考服务可用。
- 关联绑定同控制项目、快照SHA、task ID和原creation意图SHA，保存原compiled SHA／created_revision、原因与首次关联时间。明确`context_only`／操作者声明性质，不对缺host旧任务推断原生归属。GET后只持有短事务；capture在GET前核预期修订，期间改变绑定仍保存明确标注原修订／绑定的完整观察；新关联在保存前再核当前修订，原快照／关联不被覆盖。

## 可验收节点

|节点|验收与状态|
|---|---|
|B0.1 设计与迁移|源码完成，存储33项通过／1项平台跳过：显式schema v2、固定历史v1夹具／v0升级、54 writer fences与旧连接拒绝；旧行／资产／备份、故障和进程中断回滚通过。完整独立两轴通过|
|B0.2 用例与入口|本地通过：源码受影响152通过／1平台跳过；重复／并发capture和link、更新／换绑定、离线读／多对多、精确creation反例、分页及原字节保持；完整独立两轴通过|
|B0.3 安装与旅程|完成：r1／r2各57通过／1平台跳过及真实13项旅程保留原包身份；最终r3新非editable包442／两RECORD／283及11映射回归通过；完整原home备份恢复／任务字节保持，首个driver失败保持，无正式start|
|B0.4 审查与交付|本地出口完成：自身首审request-changes／194.63秒与聚焦approve／80.09秒、两次五scope完整读取；后补并发／投影由新的完整28文件独立两轴覆盖，SP1／ST1关闭、开放0／0。最终静态／ready／普通提交推送与本候选精确CI继续|

最小CLI／HTTP先沿现有issue命名空间；本地列表有界，完整快照单独显式读取，列表不批量返回所有正文。只有真实静默错误才增回归，版本敏感的既有迁移／备份测试按SCHEMA_VERSION调整，不用新增同构CI。每完成节点更新[交付记录](../delivery/2026-11-11-issue-mapping.md)及[PLAN](../PLAN.md)。
