# F7c：显式候选评论与原生事实观察

实现基线 `472ff60a6d27c91ef5d5285f959e61d3b935341d`，分支 `refactor/architecture-foundations`。承接[逐项目工单计划](2026-11-11-project-trackers.md)；前片B1c修正已精确交付，自己的CI43007648352及原评审终核通过，原6a7e9a1夹具失败记录保持。当前C1最终r2包446／两RECORD／283与受影响52项安装检查通过，原生v7导出后新CLI衔接已验；自身首审request-changes两P2已修、聚焦103.93秒approve。最终28文件独立两轴及本地出口通过，Spec／Standards开放0／0，SP1–SP4／ST1／ST2关闭；本片精确Git／远端／自己的CI待核，不继承前片CI结论。

## C1行为与既有所有者

首片只为已经由原六阶段导出的精确候选，在其冻结工单来源发布一条中性评论（GitHub comment／GitLab issue note）。先prepare并展示完整正文、来源、actor、原task／creation／run／candidate／export身份，再由操作者按精确intent摘要明确send。正文使用固定格式，不复制工单中的指令、标题或模型文本；描述本地导出事实，不推断远端分支、PR/MR、合并或业务完成。默认不向真实账号写入，验收使用loopback夹具。

只支持原Input v7携带的完整来源；不替旧任务推测API host或工单归属。原 `tasks.creation / show / export_status` 拥有原文件、发布与导出身份，`issue_snapshots`／`issue_sources`拥有来源，`projects`拥有修订与绑定；本片消费这些Interface，不再解析原生run文件或创建任务调度。`IssueBackend`族及本地registry拥有两种原生协议；上层不按provider分派。

|节点|实现／复用|可验收出口|状态|
|---|---|---|---|
|W1 原生评论协议|扩展原IssueBackend：固定认证上下文、current actor、单次create、按ID读取及单页有界列表；复用无redirect／完整响应／超时读取|两协议路径、GitLab iid与全局ID、完整201／正文／author／issue所属核对；无SDK默认POST重试，无redirect凭据传播；分页只返回实际续页信息|源码实现通过原读取＋回写协议检查，含最新99项／1跳过；446新包与两RECORD／283已核，尚非完整C1交付|
|W2 显式意图与不确定性|独立且内聚的issue writeback用例由CLI与HTTP共同消费；沿原State保存canonical intent、attempt、result和最后观察；复用原迁移、writer fence、backup校验|只准原v7已导出精确候选；关键点核当前expected revision，tracker绑定／actor漂移拒绝发送；同source/task/run/candidate操作唯一；事务内保存attempt并提交后才单POST；重启／并发／丢响应不重发|源码实现及首轮99项／55.78秒通过；该99项原task读取受控；后补真实原v7／Git导出衔接1项已通过，最终r2含此集成的回写／架构52项通过|
|W3 可用入口与恢复|prepare／status／send／observe入口、去环境化使用说明；保存原生观察，原ID与原意图不变|CLI和受保护HTTP使用相同用例；原生v7导出后新CLI1项／13.10秒通过；status不访问网络。observe可按ID或一页列表核marker／全文／author，始终只说明当前可见事实，不将匹配、空列表、编辑或删除推断为原attempt成功／未发送|源码入口及原生v7导出后新CLI衔接已通过，r2安装52项覆盖当前入口|
|W4 安装、审查与精确交付|固定非editable包、两RECORD／283原冻结、相应回归和本地协议旅程；实际自身审查模板及新fresh-context完整两轴|正常201与已导出原候选关联；响应丢失／部分响应／重试／并发／人工编辑与来源变更证据；更新计划和交付，普通提交／推送、同提交自己的必要双OS CI终核|446新包／两RECORD／283身份通过；r1安装188／1跳过保持；自身首审两P2已修，r2包446／两RECORD／283及52项定向通过；聚焦自身103.93秒approve／五scope全文核过；完整28文件独立两轴／本地出口通过，开放0／0；精确交付待核|

定向[协议研究](../research/2026-11-11-issue-writeback.md)已完成，固定SDK源码的默认POST重试及原生关联副作用已有第一方依据。

准备与发送各使用当次内存中固定的认证headers，凭据只从外部 `token_env` 读取，不落入意图／错误／日志。发送前重新读取当前actor和目标工单身份；不能用“凭据存在”代替身份核验。正文或来源的任何变化需要新业务候选，不能通过更换request ID绕过原操作的unknown状态。项目修订在持久化关键点按操作者当前expected revision重核；其他Agent配置变化不阻断同一冻结候选的回写，原tracker绑定、来源、creation及export仍需完全相等；不会为网络GET／POST长期持有项目数据库写锁。

只有单次POST收到完整、身份／正文／作者均符合支持合同的201，且原result成功持久化，才为`acknowledged`。attempt已保存而缺result则为`unknown`，包括进程在实际发送前退出；不自动重试、不据marker推断exactly-once。后续观察即使找到唯一、全文和author相同的评论，也只保存观察候选，不能证明原attempt；列表分页有人工编辑、删除、权限和顺序竞态，不证明历史不存在。GitLab返回字段严格检查是本工具支持合同，仍需实际服务兼容验证。

`State`只增加工单回写本域记录，复用现有锁／事务／迁移／备份；不建立通用副作用框架、第二账本、调度器或新的恢复队列。检查集中在外部响应、冻结身份与持久化边界；不为每个普通参数堆叠同构断言和测试。原六阶段、candidate／approval／claim／旧attempt与未知恢复保持。

## 后续依赖与界限

标签需要单独设计人工修改与非CAS写入冲突；分支推送／PR／MR创建是另一种远端副作用，另片定义意图、权限和部分完成。GitLab部分原生issue关联会在merge时自动关闭，不能用作默认中性关联。C1不创建／更新／删除评论、不自动close／merge、不以标签代替批准；F7d再组织observe页面与来源旅程。F8、F9、F10和PUB1保持原状态。

原件放home下忽略的本片checks；公开证据去除私有路径及凭据。每节点更新[交付记录](../delivery/2026-11-11-issue-writeback.md)和[PLAN](../PLAN.md)，保留前片自己的CI和本片当前验证的不同身份。
