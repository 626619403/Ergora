# F7d-D3b：已有 PR／MR 的明确关联与离线读回

基线 `cae1dbb7f35ae76d9290b6e5c86f8445fd5f5ae5`，工作分支 `refactor/architecture-foundations`。前片[D3a候选观察](2026-11-12-candidate-observation-console.md)已精确交付，自己的CI43150719942双OS七必要步骤与原评审终核通过；不借给本片。

## 行为与所有权

原v7来源任务的导出记录为exported时，增加“关联已有PR／MR”入口。固定原任务、run、candidate、export分支和当前项目修订；操作者明确填写base分支、同来源仓库PR number／项目MR iid和关联原因，确认后沿既有受保护POST candidate-review-links保存一份不可变本地上下文。后端 `issues.link_review / _review_link` 继续拥有原来源／任务／导出／当前Git／原生review身份及修订校验，五次provider GET、原槽幂等与冲突、canonical记录大小及持久化；页面不复制这些逻辑，不执行远端业务写入。

结果显示完整记录SHA、原候选、原任务base／当前base／PR响应base／GitLab diff版本各自事实、全文标题与正文及完整安全JSON。already_saved／fresh_observations按原返回区分，不把已有历史记录称作新观察；并发首次请求可能已各自读取平台，不能据fresh_observations=false断言本次零读取。上下文不是批准、原发送成功证明或由工具创建PR／MR的证明。

首次请求发出后固定原字段；保存回复失败／丢失时保留原请求，提供明确“恢复原关联请求”。这仍是原幂等POST：入口已查到原记录时离线返回它；尚无记录时可能重新读取平台并首次保存本地记录，不能称作只读status。没有自动重发或把新number／base替换原请求。关闭后可按原字段重新明确恢复；已存原槽拒绝不同目标，不另建浏览器账本。

另提供按已知记录SHA的显式离线GET，使用原candidate-review-links/{digest}，不依赖token、原执行目录、Git或当前tracker绑定。该入口在正式任务页可直接打开，不要求当前任务仍可读；必须保留本项目隔离。SHA编辑、关闭重开、换任务／项目／视图后迟到读取不得覆盖当前选择；全量正文安全文本显示，不能成为指令、Skill、MCP或权限。

## 结构、范围与验收

专用 `candidate-review.js` 内聚保存／恢复与独立SHA读取；只有原tasks一个生产调用者，基于完整交互的职责拆分，不虚构复用。复用原api/ui与任务存活上下文；不新建后端／schema／table、调度、缓存账本、依赖、CI或永久测试框架。三模板、六阶段及283参考文件保持。评论／标签发送留给D3c，PR／MR创建、远端push、稳定Trigger另片。

|节点|出口|状态|
|---|---|---|
|R0 立片|核既有link_review／离线GET、原槽恢复语义与调用者生命周期，记录范围／基线|已完成|
|R1 页面|原导出入口；明确保存、原字段恢复、完整记录与事实区分；任务页独立SHA离线读；迟到隔离|已实现，安装／页面验收见R2|
|R2 实际验收|新非editable包／RECORD／283及必要原suite；两provider原生v7／Git页面保存、丢失回复同槽恢复、离线读取、冲突／修订／迟到反例，原合同／来源／导出保持、零provider业务写／零新执行、拥有资源清理|已验：r1安装74／两种子，r2包450／两RECORD／283；主39项后驱动谓词超时、续28／顺序补5／视口3及清理通过，原失败与45秒自动释放范围保留；151HTTP／后续9GET／88runtime与原记录保持|
|R3 文档与审查|使用／架构／截图；实际内置审查模板；新的fresh-context完整Spec／Standards／结构／冗余guard与成本审查|已完成；自身首审request-changes／聚焦approve；完整19件独立Spec／Standards及本地出口通过，开放0／0、SP1关闭|
|R4 精确交付|普通提交／推送、精确Git／Ref和本提交自己的双OS必要CI，更新PLAN和交付记录|已完成；18585dc精确19Git／ready／包及作者完整Ref通过，自己的CI43155880413第五run双OS七必要步骤与原评审终核通过；REST403／前四In progress保持|

验证中的Temporal SDK若受控、REVIEW_READY若合成须明确，不冒称新真实六阶段／SaaS／原生Windows正式运行。原D3a封存验收状态不再修改；另建原生种子及服务。每个节点同步[PLAN](../PLAN.md)与[交付记录](../delivery/2026-11-12-review-context-console.md)。
