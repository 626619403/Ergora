# F7d-D3c：工单评论／标签的明确操作页面

基线 `18585dccf067c28e1c444df0c8daaa040b038568`，分支 `refactor/architecture-foundations`。前片[D3b已有PR／MR关联](2026-11-12-review-context-console.md)自己的CI43155880413双OS七必要步骤及原评审终核通过，已精确交付；不能借其验收替代本片。

## 行为与所有权

原v7来源任务的exported记录增加“准备工单回写”入口。固定task／run／candidate／项目修订，操作者明确选择中性评论或一个已存在的GitHub标签；准备只读取身份并保存本地意图。标签原样保留空格、标点及Unicode。GitLab标签沿原owner可见unsupported，不降级为按名称写入。

复用 `issue_writebacks.prepare / prepare_label / status / send / observe` 及既有受保护HTTP入口。原owner继续拥有来源／导出／actor／binding／revision／原生ID核验、每动作唯一槽、attempt-before-send、不可变正文／operand及收据。并发准备可能先读取再返回原意图，不从返回值推断零读取。页面不再实现生命周期、provider调度或账本。

第一次准备后锁定原字段。回复丢失可明确恢复相同prepare请求：已有原槽时返回它，尚未保存时可能首次读取／保存，但不发布评论或标签。不自动prepare、send或observe。完整显示intent SHA、来源、actor、原task／run／candidate／export、固定评论全文或标签原生目标与完整operation；外部文字使用安全文本。

发送是单独的明确确认，只在已读到prepared时提供，并展示本页面项目修订。只发送精确已保存意图。HTTP200仍按业务status显示：acknowledged为原单次响应已核且保存，unknown没有发送按钮；任何发送回复失败先明确GET原意图状态，不重复send。关闭窗口不撤销已发操作。页面不把当前观察、相同正文／作者／marker、空页或标签存在升级为原发送确认，不开放重试槽。

任务页提供独立SHA读回，在无登记、原task文件不可读、token缺失／当前tracker改绑或provider离线时仍可读取本项目原记录。GET不访问provider；后续send／observe仍遵循原owner的真实依赖。评论观察显式选择原生comment ID或一个1–10000页码；标签观察显式传原不透明cursor。每次只读一资源／页，展示完整latest observation与next_page／page_info，下一页由用户明确输入／操作，无自动翻页或轮询。

SHA、观察输入编辑，窗口关闭／替换及任务／run／项目／视图切换均使旧回复失效；旧结果不能恢复发送入口或覆盖当前结果。同一记录工作区忙时不允许并行读／发送／观察。状态重新读取前移除原动作；操作失败不得继续使用旧prepared视图发送。

## 结构与验收

`issue-writeback.js` 内聚准备／原字段恢复、状态与明确发送／观察，只有原tasks一个生产调用者；按完整交互职责拆分，不造通用协议或假复用。复用api／ui／tasks的生命周期，按需复用记录换行样式。无后端、schema、table、依赖、永久test或CI变更，保留三模板、六阶段及283参考身份。真实账号业务写入仍需具体业务授权；本片只用loopback provider。

|节点|可验收出口|状态|
|---|---|---|
|W0 立片|核原prepare／status／send／observe与两动作差异、当前调用者和unknown语义，记录固定基线／范围|已完成|
|W1 页面|原导出准备；完整意图与独立SHA状态；prepared单独确认发送、unknown禁补发；手动有界观察、迟到隔离|已实现并修复两P2，原owner不变|
|W2 实际验收|新非editable包／两RECORD／283；必要原writeback／Web／架构suite；原生v7／Git两provider页面评论、GitHub标签、GitLab拒绝、丢失回复／unknown与观察不升级、离线读／修订／迟到；原合同／导出保持与拥有资源清理|已验：r1安装76项，r3包451／两RECORD／283；主56／续20／离线3／最终7，段失败保持；143HTTP／原88runtime与3记录及所属资源清理通过|
|W3 文档与审查|使用／架构与两视口；实际自身审查模板；新的fresh-context完整Spec／Standards／结构、冗余guard/test/CI与成本检查|自身首审request-changes／聚焦approve，完整19件新独立Spec／Standards及本地出口通过，开放0／0、SP1／SP2关闭|
|W4 精确交付|普通提交／推送、精确Git／Ref和本提交自身双OS必要CI，计划及交付同步|784da65精确19Git／包与独立Ref、普通推送和自己的CI43159652748双OS七必要步骤／原评审终核通过，精确交付终结|

种子若控制Temporal SDK、合成REVIEW_READY，须按实际标记；不冒称新模型六阶段、SaaS或原生Windows运行。CLI／HTTP的既有后端回归与实际页面各有范围，不为文案或状态记账重复全套。每个节点同步[PLAN](../PLAN.md)及[交付记录](../delivery/2026-11-12-issue-writeback-console.md)。稳定Trigger、PR／MR创建、远端push及F8–F10另片。
