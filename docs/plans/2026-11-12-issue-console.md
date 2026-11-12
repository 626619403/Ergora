# F7d-D1：项目工单读取与离线快照页面

实现基线`572c44e3f9621cd85d18447f14b436725df2eb64`，分支`refactor/architecture-foundations`。前片[C3b](2026-11-11-existing-review-association.md)精确28Git、作者SSH远端及自己的CI43068731988双OS必要步骤已经原评审终核通过；本片另验，不借前片结果。接续[F7总计划](2026-11-11-project-trackers.md)。

## 行为与范围

控制台增加逐项目“工单来源”入口。普通本地项目也能按明确number／iid读取当前完整上下文，并明确保存快照；已有快照有界分页、全文离线读回。manual或后来改绑的项目仍可浏览其历史快照，但不能把历史来源假称为当前绑定。来源文字一律按不可信文本展示，保留完整正文和来源／native ID／原响应摘要；列表摘要不代替全文。读取／capture不创建任务、不授权限、不自动发送评论／标签或创建PR／MR。

首片只解决完整可用的来源阅读旅程。来源快照→正式任务v3、原候选观察／回写／review关联的页面承接另片D2；沿原task preview/create、原run/candidate/intent恢复，不在来源页建立第二状态机。稳定事件／Trigger先研究真实consumer再立D3，不先造通用webhook／outbox服务或后台派工。

## 所有权与设计

- 新`console/issues.js`是导航视图，按已有api/ui/state模块消费`issues.show / capture / snapshots / snapshot`对应HTTP。列表保持服务器limit／cursor语义，无浏览器业务存储、provider分派、SDK或新数据库表。
- `console/app.js / index.html`只登记导航和view；项目revision及有效绑定仍由原dashboard／components拥有。刷新页面不隐式请求provider，外部读取必须操作者按按钮。
- 历史列表和全文读取可主动按钮刷新／翻页，不自动轮询。项目切换、tab离开、较晚响应不能覆盖新选择；参考现有任务视图的序号和DOM生命周期，局部实现即可，不为单视图增加全局request框架。
- 当前读取和已保存快照分别标清，不拿旧摘要当新观察。捕获时消费当前明确项目revision，失败不伪造本地记录；捕获成功后只刷新已有历史用例。正文用textContent／pre等现有安全DOM，不执行Markdown/HTML或任意外部URL。
- 不新增生产依赖、CLI或持久合同。可选Web继续可选，基础读取不依赖Temporal／模型。页面用量和截图不是正式六阶段或平台权限验收。

## 可验收节点

|节点|出口|状态|
|---|---|---|
|D0 立片|重核原页面生命周期／原HTTP／权限与现有owner，固定基线／范围及D2/D3依赖|已完成，前片已精确终结|
|D1 视图|导航、当前明确读取、显式capture、历史有界分页／全文离线读；manual／绑定事实准确|已实现，最终r4单列历史／滚动区已验|
|D2 行为验收|安装包真实HTTP＋loopback GH／GL，manual、完整恶意外观文字、revision冲突／失败、旧资料／重开保持、迟到回复／切项目与零意外写|已验：r2后端45项；r3生命周期18项；r4主旅程38项／SP1复验2项；75原快照与拥有资源清理通过，分轮身份保持|
|D3 文档及审查|更新使用／架构及实际截图，必要受影响检查；内置审查模板和新fresh-context独立两轴，检查重复实现／冗余test／guard与实际成本|文档／截图、自身706.84秒approve／五scope完整读取完成；最终19文件静态206链接／6秘密值issue0；完整19文件独立两轴开放0／0、SP1与ST1关闭，本地出口通过|
|D4 精确交付|普通提交／推送、精确Git／remote与本提交自己的双OS必要CI，原失败范围保留|d60a9d8普通提交／推送退出0、19Git／ready及作者SSH Ref原件独立核准；自己的CI43142680273第四run HTML Success、两job七必要步骤通过，原评审11份原body／receipt离线终核通过，精确交付终结；两REST403／前三非终态及lazy404保留|

每节点完成后更新本文件、[本片交付](../delivery/2026-11-12-issue-console.md)与[PLAN](../PLAN.md)。恢复先重读AGENTS／PLAN、Git、当片原件，不以设计文档称实现完成。Linux浏览器只验本地控制台，不从CI推导原生Windows正式执行或真实SaaS兼容。
