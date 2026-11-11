# F7c：显式工单回写的协议、恢复边界与首片建议

日期：2026-11-11。研究基线为 `4638c3b9524adcba584a9313b8fd1588b5dde64d`，分支 `refactor/architecture-foundations`。要求来自 [F7 计划](../plans/2026-11-11-project-trackers.md)，接续[准备研究](2026-11-11-project-trackers.md)。本次只新增本文；没有实现回写、修改产品／计划／测试、安装 SDK、运行模型、提交或推送，也没有使用凭据或向 GitHub／GitLab 发送写请求。研究开始时 B1c 所选准入尚未提交且真实模型验收在进行；收尾时主工作流另报已推送 `6a7e9a1`、自己的 CI 在跑。后者由[原片记录](../delivery/2026-11-11-source-task-admission.md)负责，本文不将其验收或新提交当成 F7c 证据。

本文把**事实**、**推断**、**推荐**和**未知**分开写。官方滚动文档、静态源码与实际远端响应的证据边界不同；文末登记本次读取及失败。本文不能证明真实账号写入、自托管版本兼容或恢复实现已经通过验收。

## 建议决策

**推荐 C1 只做一件事：操作者为原已导出的 task／run／candidate，显式发送一条新的关联 comment／note。** 目标必须来自该任务冻结的来源 v7；正文由已核身份生成，保存完整 write intent，发送前保存 attempt，每个 intent 最多执行一次 POST。它不发布 Git branch、不创建 PR／MR、不改 labels／state，也不改变本地批准和任务结果。后续 C2 才做明确拥有的标签操作，C3 再分清已有 branch／PR／MR 的引用与远端创建，F7d 才做 observe／页面。[本地来源与任务合同](../../src/ergora/issue_sources.py)、[v7 封装](../../src/ergora/task_envelopes.py)、[原 export](../../src/ergora/reference_task_export.py)、[F7 范围](../plans/2026-11-11-project-trackers.md)

**事实：本次所读两家 comment／note 创建接口都没有 documented 客户端幂等 key、客户端指定的唯一操作 ID，或按该 ID 查询原创建结果的合同。** GitHub POST 的业务参数只有 `body`；GitLab POST 除 `body` 外有 `internal`、已弃用的 `confidential` 和有权限限制的 `created_at`，都不是请求去重 token。两者资源 ID 均由返回的 comment／note 对象取得。没有找到该能力不能扩写成“任何部署绝不支持”，但足以拒绝承诺本次接口具备它。[GH-COMMENTS]（本次 E1）、[GL-NOTES]（E2）

**推断：唯一 marker、同一 author 和全文匹配只能定位候选资源，不能证明“这个资源由本地那次 attempt 创建”。** 同一账号可以手工复制正文，已发评论也可以编辑／删除；原生创建 ID 不是事先绑定本地 attempt 的 operation ID。因此，完整且匹配的 `201` 响应可记 `acknowledged`；响应丢失后，即使只查到一个匹配，也应保留 `unknown`，另记 `observed_candidate`。查不到更不能证明没发出。没有足够原生因果事实时不自动重发，也不换一个 write ID 绕过未知状态。[GH-COMMENTS]（E1 的创建／更新／删除合同）、[GL-NOTES]（E2）、[GL-DISCUSSIONS]（E5 的编辑权限）

**事实：原生“关联”不一定符合默认不关单。** GitHub 的 linked PR 在合入默认分支时关闭 linked issue。GitLab 文档明确说，即使没有 closing pattern，通过 GraphQL 或 MR 的 Work items widget 建立的这类 link 仍会在 merge 时关闭 issue。因此，准备研究中“无需关闭的关联也有 GraphQL／Work items widget 入口”不能作为安全保证；本文收窄该判断。C1 使用中性评论引用，后续必须按具体 relation 类型声明副作用。[GH-LINK]（E3）、[GL-MANAGE]（E4）

## 已有所有者与本次核到的缺口

以下是基线静态事实。所引文件未在本次修改；B1c 正在修改的 submission／准入工作只按[当前记录](../delivery/2026-11-11-source-task-admission.md)理解，不借其结果证明 F7c。

|所有者|已存在的事实|对 F7c 的推荐边界|
|---|---|---|
|[issue_backends.py](../../src/ergora/issue_backends.py)|`IssueBackend` ABC、GitHub／GitLab 本族实现和模块局部 `_BACKENDS`／`for_binding`；构造校验、认证头、固定 API 来源、拒绝重定向、单次按号 GET、1 MiB 完整读取限制；没有 comment／note 写入、分页、主体核对或通用写请求合同|继续由同一构造／执行 Interface 承担协议，不在 CLI／HTTP／用例按厂商分派；扩展实际需要的窄方法，不能让现有“凭据存在”诊断冒充写权限已核|
|[projects.py](../../src/ergora/projects.py)、[issues.py](../../src/ergora/issues.py)|项目绑定有 `expected_revision`；有效配置有内容摘要；读取带项目修订，capture 保存完整 binding／observation；`issue_task_links` 只是 `operator_asserted_context`，`execution_authorized=false`|准备和发送都固定项目／来源；普通本地 context link 不足以授权发帖。新写入不能改 snapshot、旧 task 或项目 namespace|
|[issue_sources.py](../../src/ergora/issue_sources.py)、[tasks.py](../../src/ergora/tasks.py)、[task_envelopes.py](../../src/ergora/task_envelopes.py)|`tracker_identity` 保留 API base 的 host 与路径；snapshot 内容寻址；正式来源校验项目、provider、API、namespace、路由号；带来源的 envelope 为 v7|C1 从原 creation 中的 v7 source 派生目标，区分 number／iid 与 `native_id`；不得仅用旧 hostless tracker 键定位写请求|
|[reference_task_creation.py](../../src/ergora/reference_task_creation.py)、[tasks.py](../../src/ergora/tasks.py)|creation 验证完整不可变合同；任务 API 持有原 ID、run 和显式 decision／export；`_native_prepare` 只在本地准备阶段保留 DB 修订，长操作在外部执行|复用公开的 creation／export／evidence 用例，不能在回写层重做“任务是否批准／完成”的状态机；读取材料和网络查询均不持有共享 DB 写事务|
|[reference_task_export.py](../../src/ergora/reference_task_export.py)|固定 submission／run／candidate；只接受原完成的 `REVIEW_READY`；保存 intent／attempt／result；以本地 Git ref 查询恢复；`export_status` 不查远端 ref；export 不 push、不建 PR／MR|评论引用原 export 的精确事实，不把本地 branch 称作远端发布。新增只读投影若必要，应由该所有者提供，不导入 `_Export` 私有对象再复制验证|
|[reference_task_approval.py](../../src/ergora/reference_task_approval.py)、[reference_task_reconciliation.py](../../src/ergora/reference_task_reconciliation.py)|批准在 signal 前保存 attempt；未知恢复查原 run 的精确信号历史，查无信号不重发；对账仍拥有原 fence／claim 处理|借鉴“先意图、先 attempt、原事实恢复”的次序。评论服务没有 Temporal 信号历史同等证明，不能照搬 `history` 成功判断；回写不释放 claim、不批准候选|
|[state.py](../../src/ergora/state.py)、[backups.py](../../src/ergora/backups.py)|State 管 SQLite migration、旧 writer fence、迁移前备份和跨进程 `file_lock`；现为 schema v2。backup 离线验证会委托领域校验；没有现成通用 OperationManager／issue-writeback 表|如 C1 需要持久记录，在原 State 内增加一个本域 canonical 记录，不另建数据库／后台 outbox 调度器；migration、writer fence、backup／restore 验证同片补齐，不借新模块名声称这些已存在|

**推荐的归属：** `issue_writebacks` 用例持有显式业务意图、逻辑操作唯一性、前置比较、状态转换与恢复决策；`issue_backends` 只持有原生协议和有界事实；State 持有持久化与锁；原 task／export／evidence 持有候选和批准。回写记录只引用它们的身份／摘要，不能复制一套正式 task、approval、run 或调度账本。原 283 冻结文件保持原字节。依据为上表本地源码与 [F7 计划](../plans/2026-11-11-project-trackers.md)。

## 原生 comment／note 合同

### 创建、读取、编辑、删除与权限

|事项|GitHub issue comments|GitLab issue notes|
|---|---|---|
|创建|`POST /repos/{owner}/{repo}/issues/{issue_number}/comments`，`body` 必填；成功 `201`。会触发通知，快速创建可能触发 secondary rate limit。Issues API 同样覆盖 PR，C1 仍先拒绝 PR|`POST /projects/:id/issues/:issue_iid/notes`，`body` 必填，最多 1,000,000 **characters**；`internal` 默认 false；`created_at` 需要管理员或 project／group owner 权限。C1 只发显式普通 note，不发这些管理参数|
|按原生 ID 读|`GET /repos/{owner}/{repo}/issues/comments/{comment_id}`；路径本身没有 issue number，必须核响应的 `issue_url`，不能只认 comment ID|`GET /projects/:id/issues/:issue_iid/notes/:note_id`；核 project／noteable 身份、`noteable_type=Issue`、`system=false` 和实际 body／author|
|列该 issue 的评论|`GET /repos/{owner}/{repo}/issues/{issue_number}/comments`，按 ID 升序；支持 `since`（最后更新时间之后）、`page`、`per_page`，默认 30、最多 100；它没有 repository-comments 列表的 sort／direction 参数|`GET /projects/:id/issues/:issue_iid/notes`，默认 `order_by=created_at`、`sort=desc`，也支持 updated_at 和 asc；当前文档还有 `activity_filter`。不能假设旧部署也支持该过滤；兼容首片可读默认 notes 并在本地检查 `system` 等字段|
|返回内容|raw Markdown `body`、`user.id`、资源 `id`／`node_id`、时间、`issue_url` 等；raw／text／html／full 是不同表示。marker 比较必须取 raw `body`|`body`、`author.id`、资源 `id`、时间、`project_id`、`noteable_id`／`noteable_iid`／`noteable_type`、`system`、`internal` 等。author 是对象字段，不是本地请求签名|
|修改与删除|`PATCH .../issues/comments/{comment_id}` 修改 body；`DELETE` 删除。两方法都存在，因此正文不是不可变操作收据|`PUT .../notes/:note_id` 可修改 body；`DELETE` 删除。本人可编辑自己的评论，Maintainer／Owner 还可编辑他人的评论|
|读权限|fine-grained token 文档列 Issues(read) 或 Pull requests(read)；公共资源可匿名读取|必须实际有目标 issue／note 的可见性。普通、internal、confidential、锁定讨论的权限并不相同；公开 issue 可读不证明 notes 可匿名读|
|写权限|fine-grained token 文档列 Issues(write) 或 Pull requests(write)，支持 App user、App installation 和 fine-grained PAT；这不是凭据存在即可写成功的保证|当前权限矩阵的普通 “Leave comments” 包括 Guest，Guest 说明也写明可评论 issue；这不等于任意 token、internal／confidential 对象或锁定讨论都可写。API token 还须有相应 API 权限；本次没有核到可移植的最窄 token scope 名称，不能把 read-only scope 宣称成可写|

上表 GitHub 事实均来自 [GH-COMMENTS]（E1），GitLab 路径／参数来自 [GL-NOTES]（E2），普通项目角色来自 [GL-PERMISSIONS]（E10），编辑／讨论语义来自 [GL-DISCUSSIONS]（E5）。本轮还只读复核了前研究已取得的两份官方分页页缓存，原 body hash 与原 metadata 相符，没有再次发起 GET；其具体 continuation 依据见下表 E17。notes 的当前过滤字段不能据此宣称覆盖所有自托管版本。

**推荐的严格响应合同及其依据：** “完整”首先表示 HTTP body 无截断、未超字节预算且 JSON 为预期对象／数组；然后核下列实际消费者需要的字段。新增可选字段可以保留，不因平台增加字段而失效；缺必要字段必须明确不支持／unknown。下面的要求是 C1 应验收的本地合同，不把文档样例的所有字段都冒充服务端 required schema。

|消费点|本次取得的字段依据|C1 推荐校验|
|---|---|---|
|GitHub POST 的 `201`|E1 创建样例含 `id`、`node_id`、`url`、`html_url`、`body`、`user.id`、`created_at`、`updated_at`、`issue_url`、`author_association`，还有当前可选 `pin/minimized`|正整数 `id`；raw `body` 精确相等；`user.id` 等于当前已核 actor；`issue_url` 是冻结 API base 下目标 repo／number 的 issue 路径；`url` 是同源该 comment ID 的资源路径；时间字段有效，node／web URL 等作元数据。`html_url` 不作带凭据请求目标；`author_association` 不当 author 身份。响应**没有 issue 全局 native ID**，只能结合前置 issue GET 比较，不能伪造原子 ID 前置条件|
|GitLab POST 的 `201`|E2 的创建段没有独立 `201` 示例／响应 schema。E8 通用规则是 POST 成功201并返回新资源 JSON；E2 的 issue-notes 列表样例提供 `id/body/author.id/project_id/noteable_id/noteable_iid/noteable_type/system/internal/created_at/updated_at`|C1 声明只支持能返回并核实必要身份字段的普通 note：native `id` 正整数、exact body、`author.id` 与 actor 一致、`noteable_type=Issue`、`noteable_id` 等于冻结 issue `native_id`、`noteable_iid` 等于路由 iid、`system=false`、普通 note 的 `internal=false`。请求固定在冻结 namespace 的 issue notes 路径，结合全局 native issue ID 核所属 issue。`project_id` 若返回作为原生元数据保存，不在没有期望值时伪造比较。缺必要字段不算确认成功；该严格201合同仍待夹具及未来有授权目标验证|
|GitLab issue→project 事实|原 issue GET 的全量原生响应有 project_id；前研究公开 GET 实际记下 project_id=278964。现有 F7a `issue()` 投影只保留 issue `native_id`，**不保留 project_id**|C1 使用已有冻结全局 native issue ID＋iid＋受控请求 namespace 即可，无须只为 project_id 扩展快照。以后若出现必须比 project ID 的真实消费者，再由 backend 复用原 issue GET 提供窄事实投影；不能从 namespace 猜 ID，也不能假称 snapshot 已含该字段 [原投影](../../src/ergora/issue_backends.py)、[原实测](2026-11-11-project-trackers.md)|
|GitHub 单页 continuation|E1 issue-comments 参数有 page／per_page；缓存 [GH-PAGE] 明确 `Link` 的 `rel="next"` 是下一页，可能缺 first／last，单页可无 Link|返回明确 next cursor，绑定 provider／API／target／表示／过滤和本轮范围；不凭总数或“本页少于请求项数”推导未发送。Link 的同源 canonical 路径也必须能证明等价目标，无法核实的 alias 保持 incomplete，不能对任意 Link 发带凭据请求|
|GitLab 单页 continuation|缓存 [GL-REST] 的 offset 段明确 page 默认1、per_page 默认20／最多100；还直接以 issue notes 为例给 `Link rel="next"`、`x-next-page`，并说明 GitLab.com 可能不返部分头／大集合省略 totals|优先核 Link 的 next；支持的 x-next-page 作为一致性依据，冲突／目标变化拒绝，缺总数不影响按有效 next 读取。没有足够 continuation 证据时标不完整；一次页链结束仅表示本轮可见遍历结束，不声称稳定快照。缺页、限额、坏 Link 都不能默默变成“全部查完”|

`GET /user` 所需的共同主体字段就是原生正整数 `id`，login／username／name 只作展示，不读私有 email 等不相关字段。GitLab E7 current-user 示例明确有 `id`；GitHub E6 是 authenticated-user 合同，comment `user.id` 样例在 E1。两者对比属于应实现的身份校验；本次没有真实 token 身份回执。

**事实与限度：** GitHub comments 文档列出创建 `201/403/404/410/422`，单条 GET `200/404`，issue 列表 `200/404/410`，PATCH `200/422`，DELETE `204`。它不是穷尽所有网关／认证／限流错误。GitLab notes 页没有为每个 issue-note 操作列完整状态码矩阵；通用文档说明 POST 通常 `201`、GET／PUT `200`、删除 `204` 或异步 `202`，并解释 `400/401/403/404/405/409/412/422/429/5xx`。不能把一般说明写成每个 note endpoint 已验证支持全部代码，尤其不能由通用 `409/412` 推导写 CAS。[GH-COMMENTS]（E1）、[GL-ERRORS]（E8）

**推荐：** 完整保存成功响应的资源身份、精确正文、作者及摘要；错误只保存经清理的状态／必要头／错误类别与摘要，不原样输出凭据或任意服务端报错。发送后的 timeout、断连、5xx、重定向、截断／超限／无效 JSON、成功状态但缺字段或目标／作者不符均不算成功。`4xx` 可记录为 `rejected_response` 的事实和原因；C1 也不据此自动重发。`404` 可能是无权限而非删除，`401` 也可能包含权限不足，`429` 尊重 Retry-After 的读取节奏；限流建议不授权重发未知 POST。[GL-ERRORS]（E8）、[GH-COMMENTS]（E1）、前研究的 [GH-BEST]；这些映射仍须本地夹具验证。

### 主体核对与 marker 的证明能力

**事实：** GitHub `GET /user` 的 fine-grained token 类型列 App user token 和 fine-grained PAT，没有 App installation token；该 endpoint 不要求 fine-grained permissions。经典 PAT／OAuth 缺私有用户 scope 仍会以 token owner 身份返回 public-user 表示，取 `id` 不应要求无关私有字段。GitLab `GET /user` 返回当前用户；其错误指南特别说明，有些有效 fine-grained token 因没有读用户权限也可能返回 `403`，CI/CD job token 不能用这项诊断。[GH-USER]（E6）、[GL-USER]（E7）、[GL-ERRORS]（E8）

**推荐 C1 明示支持范围：** 仅支持能通过同一凭据取得明确 native actor ID 的认证模式，发送前重新核对。GitHub installation token 的 comments 能力在文档中存在，但 C1 若尚无经过核对的 installation／app→bot 主体解析，就显示该写认证模式 unsupported；不能偷偷把 `/user` 当所有 token 的共同前置。GitLab 同理，不把 `/user` 的 `403` 一概叫 token 无效，不支持 sudo／代用户参数。每次显式操作开始时仅在 adapter 内存固定一次凭据值，current-actor 与 POST 使用同一短期请求上下文；不能两次重新读取 env 而在中途悄悄换主体，值不得返回用例／日志／DB。下一次显式操作重新取凭据、重新比 native actor。主体核对仍不能保证服务端随后没有撤销权限。

**推荐 marker 构造：** 用本地不透明 write ID 加随机 nonce，并可附不含 marker 的语义 payload 摘要。把它作为普通文本保存在精确正文中；不依赖 HTML 注释一定原样保留或可见。最终 intent 摘要在完整正文生成后计算，避免“正文含自身 intent hash”的循环。marker 不是秘密、签名或服务端幂等 key；服务端不负责唯一约束。以下都必须有反例验收：[创建／更新合同][GH-COMMENTS]（E1）、[GL-NOTES]（E2）、[GL-DISCUSSIONS]（E5）

|恢复看到的情况|推荐保存的事实与结果|
|---|---|
|完整匹配的原 `201` 已保存，知道 native comment／note ID|该 attempt 可记 `acknowledged`；之后按 ID GET 是当前内容核对，保留原收据。后来的编辑／删除记 drift，不能擦除原已确认发送事实，也不补发|
|响应丢失，只有一个 marker＋同 actor ID＋精确全文匹配|保存该资源当前事实及 `observed_candidate`；同账号仍可手工复制，缺原生 operation ID 时 delivery 保持 `unknown`，不自动接纳为本次已发送|
|marker 被别的作者复制／导入／系统 note 携带|不是本次发送证明；分别记录实际 author／system／import 字段，不靠显示名、`author_association` 或后缀猜机器人|
|同作者复制出两条或更多完全匹配项|记录多匹配／歧义及已覆盖范围；不任意取最早／最新／最小 ID，不删重复、不再发|
|正文或 marker 被人工编辑，或原 ID 已删／返回 404|保存 drift／不可见事实。已确认收据仍是历史事实；原 unknown 继续 unknown，查不到不转成 failed／未发送|
|达到页数／字节／时间预算，缺页／JSON 不完整／返回错 issue|记录 incomplete coverage，结果 unknown；不把截断页当完整空列表，也不凭单条候选省略未覆盖范围|
|完整遍历当前分页没有 marker|只表示本轮可见页没有匹配。删除、并发编辑／分页移动、权限或不可见 note 仍可能影响结果；不是稳定 snapshot，更不是不存在的证明|
|token_env 的值换成了另一主体|同 env 名不等于同 author。未发送 intent 在 dispatch 前阻断；已 attempt 只读对账，另记读取主体／可见性，不借新主体认领旧操作或重发。相同主体换 token 也不证明 scope 相同|
|项目修订、provider、API base／版本、namespace、issue native ID 改变|未发送时返回 stale／conflict，不能 retarget 已保存意图；已有 attempt 只在冻结原来源做有授权的只读对账。新绑定不是旧 operation 的恢复地点；不能跟随 Location 携带凭据迁移|

**未知：** 本次没有原生写 API 可供指定 operation ID 并在丢响应后查询其执行结果的证据。HTTP 请求相关 ID（若返回）可以记为诊断，不能当成 documented 可查询操作收据。人工明确采纳某条匹配资源可另记 operator resolution，但不能改写成服务端证明；C1 不必提供这一状态提升入口。

## 一套构造／执行 Interface 与恢复所有权

下面是推荐形状，不是已实现 API。沿原 `for_binding(binding)` 构造同族 backend，由它统一保留认证、来源和字段映射；capabilities 只暴露确实实现并受支持的操作。manual／未支持认证或方法必须明确失败。

```python
backend = issue_backends.for_binding(frozen_binding)
backend.capabilities()                       # actual supported operations/auth modes
backend.read(issue_number_or_iid)             # existing issue observation
backend.current_actor()                       # native ID + observed auth mode
backend.create_comment(issue_id, exact_body)   # one native POST, no retry
backend.get_comment(issue_id, native_id)       # verify native target and raw body
backend.list_comments(issue_id, cursor, budget) # explicit bounded page, no get_all
```

**推荐实现界线：** GitHub／GitLab 各自把 comments／notes 路径映射到共同 `CommentObservation`／`CommentPage`／`WriteResponse`。观察保留 native ID、native author ID、目标 issue 身份、raw body、时间、实际 system／internal 属性、响应摘要和来源；分页保留本轮请求范围、耗时、下一页及是否完整取得这一页，不伪造服务端稳定 snapshot。`WriteResponse` 不替用例决定“能否重试”。HTTP helper 只收敛已有超时／完整读取／固定来源／错误处理，不扩成通用 Git 平台框架，不把 SDK 对象暴露上层。[现有 ABC](../../src/ergora/issue_backends.py)、[两原生合同][GH-COMMENTS]／[GL-NOTES]

**推荐 canonical 记录：** 可在原 State 内增加一个 `issue_writebacks` 本域表，键为 project＋write ID；记录内容校验归用例，迁移／writer fence／backup 校验归原所有者。只存一份不可变 intent、至多一次 attempt 与响应／后续只读观察，避免同时在 DB 和 reference 目录维护两份权威回写账。至少绑定：

- 原 creation／compiled／source snapshot 身份、原 submission／run ID、精确 candidate SHA、原 export intent／result 身份；相关任务批准／证据由原用例核验，不由评论或 label 推断。
- 项目修订和 effective configuration 摘要、完整冻结 tracker binding、API base 含路径与版本、namespace、路由 number／iid 和 issue `native_id`；credential 只存 env 名，主体另存已核 native actor ID，不存 token 值或其派生指纹。
- 一个明确 `candidate_association` 动作、生成模板版本、精确正文及 UTF-8 摘要、marker、操作者显式授权与准备时看到的原生前置事实；正文不复制工单中的任意指令、quick actions 或 mentions。
- attempt 的精确 intent 摘要、请求 method／受控目标／payload 摘要和保存时间；result 保留实际状态、完整性、native ID／author／body 校验事实。只读恢复观察独立追加，不覆盖原 attempt 或原响应。

**推荐唯一性：** C1 每个原 creation＋run＋export intent 的 `candidate_association` 只有一个逻辑动作。相同 write ID 只接受相同 intent；不同 write ID 也不能绕过该动作已有的 attempt／unknown／acknowledged 去再发一条。尚未 attempt 的意图如需改来源或内容，应明确撤回本地 prepared 记录再重新审查；已 attempt 不提供“清空重试”通道。这样仍允许同一 issue 对应多个明确 task／run，不产生第二套派工去重规则。[现有多任务映射](../../src/ergora/issues.py)、[原决策身份模式](../../src/ergora/tasks.py)

建议执行顺序：

1. **准备可审查意图。** 读取原 creation／来源 v7／export／必要 evidence，经其既有用例核身份。网络预检在 DB 事务外取得当前 issue 与 actor；本地短事务再次核项目修订，再保存完整 intent。区分任务冻结来源与准备时新看到的 issue 事实，不能把新内容覆写进旧任务。
2. **发送前核对。** 在 State 的既有 `file_lock` 机制下串行化该逻辑动作；重新核项目绑定、原 export 记录、当前 actor 和 issue 身份／准备时选定的比较字段。已发生人工变化则返回 conflict／not_attempted，供重新审查。比较后仍有远端竞态，不能称 CAS，也不能在共享 DB 写事务里等远端锁／HTTP。
3. **先保存 attempt 再发送。** 短事务提交后才允许唯一一次 POST；transport、SDK、HTTP 层均不得自动重试 unsafe 请求或跟随重定向。只有完整、目标／作者／精确 body 均匹配的原 `201` 可保存 acknowledged。进程在 attempt 提交后、实际发送前崩溃也应成为 unknown：安全代价是可能没发出的操作也不能自动补发。
4. **status 与恢复分开。** status 只查本地记录；send 见已有 attempt 就返回原状态。resume／reconcile 只读冻结来源：已知 ID 先 GET 原 ID；未知 ID 再有限 list 找候选；缺少因果证明始终 unknown。读取失败、权限变化或任务运行时不可用都不能触发重新 POST，也不需要重新做模型准入。

这沿用原 [export](../../src/ergora/reference_task_export.py)／[approval](../../src/ergora/reference_task_approval.py) 的准备、锁、attempt 与原事实恢复原则；comments 的资源 ID 证明能力较弱，所以结果提升条件必须独立定义。C1 可暂用每次恢复最多 2 页、每页最多 100 项、单响应 1 MiB、总响应 2 MiB 和显式总期限；这是待实测的起始预算，不是平台限制。超过预算保留可继续的读取范围，不自动启动全库扫描；页码／Link 只用于同一已核 API origin 和目标，不跟随任意外部 URL。[GH-COMMENTS]（E1）、[原读取边界](../../src/ergora/issue_backends.py)、前研究的 [GH-PAGE]／[GL-REST]

## 不关单的关联范围与后续切分

|候选动作|官方事实／限制|推荐分片|
|---|---|---|
|在 issue 写中性评论，列精确 task／run／candidate|普通评论创建与修改 issue state 是不同原生操作；GitLab 评论支持 quick actions，`/close` 也可写在 comment 中。任意工单正文或模型输出不能直接作为 note 发送|C1 固定生成文本，只含经验证的 ID／SHA 和 marker；原 export branch 保存在意图证据中，未验证远端 ref 时不声称分支已发布。明确拒绝任意 quick-action 文本，默认不修改已有评论 [GL-DISCUSSIONS]（E5）、[GL-MANAGE]（E4）、[GH-COMMENTS]（E1）|
|在评论中引用已存在的 branch／PR／MR URL|文本引用不等于 closing relation，也不证明该远端 branch 指向本地 candidate。GitLab 官方例子 `Related to #5` 表示 related 且不自动关闭，而 `Closes #4` 会关闭；自托管 closing pattern 可定制|C3 可先只读核原生目标／head SHA／项目后发中性引用，保存 relation=`comment_reference`。普通文本、原生 Development／Work items link、closing relation 分别表达；不承诺第三方自动化没有其他效果 [GL-MANAGE]（E4）、[GH-LINK]（E3）|
|原生 linked branch 或 linked PR|GitHub 支持手动关联 branch／PR；linked PR 合入默认分支会关闭 issue。分支关联也不能继承成“一切后续 PR 都无关闭语义”的保证|不在 C1 建立；C3 分别核具体原生关系与权限。默认不创建带 closing 语义的链接，不以“未调用 close endpoint”掩盖未来 merge 的关闭副作用 [GH-LINK]（E3）；分支细节沿前研究的 [GH-BRANCH]，本轮未重读|
|GitLab GraphQL／Work items widget 的 issue↔MR link|官方明写无需 closing pattern 也会在 merge 时关闭；权限在建链接时检查，之后失去 issue 项目权限仍保留 link 的关闭效果|默认不采用为无关闭关联；若未来需求明确要求此类 relation，需另立具有该副作用的动作，不偷渡到 comment reference [GL-MANAGE]（E4）|
|创建远端 branch／PR／MR|当前 export 是本地条件 ref 创建。远端发布、head／base 身份、创建响应丢失、并发同名分支、PR／MR 已存在等属于新的实际消费者；PR／MR 描述和 commit closing pattern 可在后续 merge／默认分支 push 时关单|C3 再调查具体 create／lookup／恢复合同；只提供现有对象引用不等于已实现创建。不得调用 close／merge 或自动启用 merge；不根据 SDK 可调用方法直接开放 [原 export](../../src/ergora/reference_task_export.py)、[GH-LINK]（E3）、[GL-MANAGE]（E4）|
|标签 add／remove|既有准备研究已核：GitHub POST 加、DELETE 指定名称；PUT／issue PATCH labels 为整套替换；GitLab add_labels／remove_labels 为局部操作，但 add 不存在名称可能建标签。没有 documented issue 写 CAS|C2 独立显式动作和逐子步骤 attempt；不整套覆写，不补偿删除人的标签；不把 label 当批准。前置读不能消除人恰好在读后修改的竞态。单个 add 成功、remove 丢响应时 stop／unknown；读到目标集合只能证明当前状态，不能证明每步由谁完成。不得自动重发未知步骤 [准备研究](2026-11-11-project-trackers.md) 的 [GH-LABELS]／[GL-ISSUES]／[GH-BEST]|

**推断与未知：** append-only 评论避免覆盖 issue 正文或整套 labels，但仍不能保证“若任何人刚改 issue 就一定拒绝”：读与 POST 之间没有本次已核的原子前置条件。中性文本不改变本地批准；外部 webhook／机器人对评论的反应也不是本次可保证的范围。自托管 closing pattern、特定服务器字段／权限及将来 PR／MR 创建合同仍待实际需求和目标版本核验。

## 窄 HTTP 与现库：按 C1 消费面计算

**事实：** 前研究已从维护者 PyPI 发行物静态核过 PyGithub 2.10.0 与 python-gitlab 8.6.0 的依赖、Issue／HTTP／保存／分页实现及 wheel SHA。本次只读复核原两个 wheel 的同一 SHA，并定向静态读了新 comment／note 消费者及写重试实现；没有重新下载、安装、导入或运行 SDK。不能将“SDK 有接口”当服务端幂等／CAS／服务器版本兼容。当前 Ergora 基础依赖只有 PyYAML 和 jsonschema，Python >=3.11。[准备研究](2026-11-11-project-trackers.md)、[pyproject.toml](../../pyproject.toml)、文末 E15／E16

|方案|C1 实际需要适配的消费者合同|节省与仍由 Ergora 承担的部分|
|---|---|---|
|现有 stdlib backend|已有 read 继续复用；各 provider 增 current actor、create comment、按 ID get、单页 list，共四种新原生操作。CLI／HTTP 共用一个 writeback 用例，不各造一套 HTTP|可复用现有构造、来源／认证头／响应上限。新增公共传输结果与分页边界有真实消费者；意图、主体核对、一次发送、未知恢复、语义唯一性和关系分类仍须自己实现。不扩成仓库全功能 SDK|
|可选 PyGithub|E15 实读 `Issue.create_comment` 的单次 requester POST，以及 `get_comment`／`get_comments` 的 lazy 对象／PaginatedList 入口；authenticated user 和共同结果仍需封装|可省对象映射／资源导航，但默认 `Github.default_retry=GithubRetry()`，其 allowed_methods **包含 POST**，status_forcelist 含403／5xx。客户端说明 `retry=None` 可关闭重试，仍须用故障夹具核“最多1 POST”、redirect／lazy／字节边界。前研究所核 pynacl、requests、pyjwt[crypto]、typing-extensions、urllib3 扩大依赖面 [PYGH-ISSUE]／[PYGH-MAIN]／[PYGH-RETRY]|
|可选 python-gitlab|E16 实读 `ProjectIssueNoteManager` 的 CRUDMixin、`/projects/{project_id}/issues/{issue_iid}/notes`、parent iid 映射与 body create 参数；current user 和共同结果仍需封装|可省路径／常见错误／分页代码，但 HTTP 默认 `obey_rate_limit=True`、`max_retries=10`，429 重试循环不区分 POST；transient retry 默认 false。C1 写调用至少需 `max_retries=0`、禁止 transient retry 并验证底层 transport；不能只关 transient 就称单次发送。requests／requests-toolbelt 是前研究已核依赖 [PYGL-NOTES]／[PYGL-CLIENT]／[PYGL-UTILS]|

**推荐：** C1 继续 stdlib，四种新原生操作集中在原 backend 后面；保留可选替换空间，不为首个评论消费者引入两套客户端。真实需求扩大到仓库／refs／PR／MR 多资源且出现重复协议维护时，再以当片具体操作数、代码／测试成本、可控制的单次发送、包依赖和服务器范围评估一个或两个可选 SDK。上表只静态核了所列发行源码；没有运行 SDK 的成功／故障／跨版本验证。

## C1 最小可验收出口

以下是待实现的可反证验收建议，**本次均未执行**。默认只用本地确定性 HTTP／故障夹具，不向真实账号发评论。

1. 原来源 v7＋精确 creation／run／candidate／export 经现有所有者读回。普通 context-only link、另一项目／API／native issue、非原 run、非导出候选、unsupported 认证模式具体拒绝；不触发 task start／approve／export／claim 修改或模型调用。
2. 同一用例服务 CLI 和受保护 HTTP；输入是显式原身份和可审查正文摘要，不能从工单内容授权。两 native 请求只含受支持 create 参数；包含 `/close`／标签指令／mentions 的原工单仍不会进入生成正文。原 issue／任务／批准保持原身份。
3. 服务端实际接收唯一 POST 之前，本地 intent 和 attempt 已可读取；在 attempt 后、发送前杀进程，重启仍 unknown 且 POST 计数为 0。服务端已创建再丢响应／崩溃，重启 reconcile 只 GET，POST 计数为 1；即使找到唯一同作者全文也不自动确认或补发。
4. 成功完整 `201` 的 native target／author／body／ID 全核后保存 acknowledged；成功响应截断、超限、字段不全、错误 issue／PR、错误 actor、无效 JSON、重定向、timeout／5xx 有独立失败事实，不能当空结果或成功。result 保存失败保留 attempt，不自动再发。
5. 同 write ID 不同 payload、不同 ID 但相同逻辑动作、source／binding／API 修订及 token 主体变化均不能绕过原意图。发前人工更新可检出；比较之后再人工修改的夹具明确显示剩余竞态，不宣称 CAS。
6. 复制 marker（他人和同作者）、多匹配、原评论编辑／删除、404 权限隐藏、分页中的并发编辑／删除、超页／字节／期限预算、缺完整响应都返回准确覆盖和 unknown。已确认资源后来的 drift 不删除历史收据；无匹配不证明未发送。
7. State migration／旧 writer fence／离线 backup／restore 校验包含新 canonical 记录和对既有 project／source 的引用；原记录与 283 冻结字节保持。包检查只覆盖实际受影响面；新的完整实现片再按 AGENTS 做独立审查与真实自身模板，不借本文或 B1c 判词关闭 F7c。

C2 的加删标签部分完成、C3 的远端 ref 并发／PR／MR 创建与关闭关系，须各自提供真实子步骤故障反例。C1 的单条评论出口不能替它们提前验收。真实账号写入、平台权限和目标部署版本需要未来明确业务授权与对应原件；本次只完成定向研究。

## 本次实际读取证据与限制

本轮在 **2026-11-11 10:12:38–10:18:29 UTC** 发起 **18 次无凭据 GET**，没有其他 HTTP 方法。每次文档读取上限 3,000,000 字节、timeout 15 秒、拒绝重定向；两次公开 API 列表预算各 1 页／1 项、1 MiB／15 秒，失败后没有继续单条 GET。命令没有读取／输出凭据。

可核结果为 **13 次 HTTP 200、1 次 403、1 次 401、1 次 404、1 次读取超时**；另 1 次首轮 GitHub 关联页的工具输出被截断，未保留该次状态／hash，不将它算成功。初轮大输出还使 GitLab notes 的段落不完整，后用定向段落重新取得同 hash；用户／token 页的再次读取仅为定位所需段落，没有扩大 API 扫描。本次只在本文保存可核元数据、所读关键合同及少量原文，未另存 HTML／API body 原件。

|证据|实际读取及结果|可用范围|
|---|---|---|
|E1|[GH-COMMENTS]，10:12:38，200，464190 B；SHA256 `42b36236ceba2f805580aa71238ce122a7b320da76704d5ceff6e06fa0dd84cc`|实读 issue comments create／get／list／update／delete 的参数、权限、状态和 raw 表示；所读业务参数无 idempotency key。REST 文档 query 为 2026-03-10；不改变产品默认版本|
|E2|[GL-NOTES]，10:12:38 与10:14:07 两次200，180840 B，同 SHA256 `480e4236cb27bd8a270f43dbfc8859d5fe8160005eb4af72639c412c782ad013`|第二次完整核 issue notes 五操作、参数和样例字段。`created_at` 是可指定时间而非 CAS／operation ID。没有取得真实 note 对象|
|E3|[GH-LINK]，首轮输出截断未核状态；10:14:07 再取200，174925 B；SHA256 `0ed6b8bc5f44fd0c22402cfdff1dd348ec6fc085414e76a6c79ddfe4dc91b1bf`|实读 “When you merge a linked pull request into the default branch … its linked issue is automatically closed.” 及 keyword／手工链接段落|
|E4|[GL-MANAGE]，10:12:38，200，115196 B；SHA256 `4d189b29de43d58f7d6a599fddfa0eaf6d93af9f275a9d72a88228a8433ed24e`|实读 closing pattern、`Related to #5` 例子及原文 “For links created either way … The link persists, so the issue still closes on merge …”；还核 `/close` 可在 comment 中使用|
|E5|[GL-DISCUSSIONS]，10:14:07，200，64032 B；SHA256 `c92cf65c1dd013d6882d8c12fccf696be712750a184507713ddfcd6240a3daa4`|实读 comments 支持 Markdown／quick actions，以及本人和 Maintainer／Owner 编辑权限；不借 thread resolve 的角色要求代替普通 comment 权限|
|E6|[GH-USER]，10:15:19 与10:16:59 两次200，404110 B，同 SHA256 `7599da2dbba10cd5fe8b8d27198057e0d0d3c80b4bcfeab8d245de7e47b1fa12`|第二次实读 authenticated user 的 public／private 表示与 token 类型／权限／状态；没有实际带 token 调用 `/user`|
|E7|[GL-USER]，10:15:19，200，252777 B；SHA256 `fae8bbedc08323944440eccfe111cc716a4574a662fcf98bd8bbe478f5b690e7`|实读 current user 的 `GET /user`／native `id`；没有调用管理员 sudo 或真实主体查询|
|E8|[GL-ERRORS]，10:15:19，200，54129 B；SHA256 `eaf5bba7af80955f4c0750c80f102d0a8e16ae0bf121eb21655848a41a0d1cdf`|实读通用状态、401 的认证／授权区别、`/user` 诊断限制、429；不是 note 专属写入实测|
|E9|[GL-PAT]，10:15:19 与10:16:59 两次200，81326 B，同 SHA256 `f44572678e4ab8f870637f5f48de3c226756b0e379514e6ce2e93c743898101f`|实读 token 使用／替代方式的相关段落；该读取没有核到本片所需的最窄 note-write scope，不能据页面标题补结论|
|E10|[GL-PERMISSIONS]，10:15:19，200，144332 B；SHA256 `4f2e2df83c09b04ece35ca319055b4fd530d1cfa16792490fc67ec2e430cda78`|实读 Guest 说明与项目 “Leave comments”／编辑他人评论权限；目标对象仍需可见且未被其他规则限制|
|E11|[GL-QUICK]，10:14:07，15秒读取 TimeoutError|未取得完整正文／hash；quick actions 的本次事实只引用成功的 E4／E5，不声称此页已读|
|E12|`GET https://api.github.com/repos/octocat/Hello-World/issues/1/comments?per_page=1&page=1`，10:15:45，403，异常原因为 rate limit exceeded|未保存 body／响应头／hash，没有取得 comment ID，没有继续单条 GET；该样例 issue1 在前研究属于 PR，也不是本片普通 issue 验收|
|E13|`GET https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab/issues/1/notes?per_page=1&page=1&sort=asc&order_by=created_at`，10:15:45，401 Unauthorized|未保存 body／响应头／hash，没有取得 note ID，没有继续单条 GET；不能因 issue 公开读取曾成功就宣称 notes 匿名可用，也不能由401推断目标不存在|
|E14|`GET https://docs.gitlab.com/auth/tokens/`，10:18:29，404 Not Found|这是定位 token scope 文档时的失败地址，不是 notes API 失败；没有据它推断 scope／权限|
|E15|只读原 PyGithub 2.10.0 wheel，455554 B；重新算 SHA256 `192ada2a76e4afc7d6b37e500c9bfeba1731e6506697445a5ba1c4af8bf0b924`，与前研究一致|静态读取 Issue.py create_comment／get_comment／get_comments，MainClass.py default_retry／retry 配置，GithubRetry.py allowed_methods／status_forcelist，Requester.py retry 传递。未导入／运行；固定源码链接供复核，不称本次网络取源码成功|
|E16|只读原 python-gitlab 8.6.0 wheel，159654 B；重新算 SHA256 `34fee7e5576cf01982c4bfa98f94d50e24733edb66beba3cb8ef286287723019`，与前研究一致|静态读取 notes.py 的 ProjectIssueNoteManager、client.py 的 HTTP retry loop／单页 get_next=False 路径，utils.py 的429／transient重试条件。没有创建 SDK client 或实际请求|
|E17|只读前研究原官方文档缓存：[GH-PAGE]，354174 B，SHA256 `385332dbe172cfdde8382006f10f6b78f84924de54ec9c52a0c89f415e07dcc2`；[GL-REST]，74504 B，SHA256 `1bd38c8370a0ab2f9a030ab263c802c0c0ee69937523cf6e123ac7a9085b0bc4`|均与原 metadata 相符，原 GET 时间05:54 UTC、本次不重取。实读 Link next／per_page；GitLab notes 分页实例及 x-next-page／缺 totals 范围。文档示例不是实际 notes API响应|

前研究的 43 GET、单 issue 条件 GET，以及 issue／labels 无 documented 写 CAS 的事实按其原范围引用，没有重跑全部网络请求；两份旧 wheel 和两份分页页缓存按 E15–E17 定向复核。GitHub 的条件读取 ETag、GitLab 通用412或一次 list 结束都不是写 CAS／稳定 snapshot。最新 GitLab 页面带有多个新版本字段；本次没有查询部署版本、运行 SDK 或构造真实编辑／删除／丢响应实验。[准备研究](2026-11-11-project-trackers.md)

## 第一方来源

[GH-COMMENTS]: https://docs.github.com/en/rest/issues/comments?apiVersion=2026-03-10
[GH-USER]: https://docs.github.com/en/rest/users/users?apiVersion=2026-03-10#get-the-authenticated-user
[GH-LINK]: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue
[GL-NOTES]: https://docs.gitlab.com/api/notes/
[GL-MANAGE]: https://docs.gitlab.com/user/project/issues/managing_issues/
[GL-DISCUSSIONS]: https://docs.gitlab.com/user/discussions/
[GL-USER]: https://docs.gitlab.com/api/users/#retrieve-the-current-user
[GL-ERRORS]: https://docs.gitlab.com/api/rest/troubleshooting/
[GL-PAT]: https://docs.gitlab.com/user/profile/personal_access_tokens/
[GL-PERMISSIONS]: https://docs.gitlab.com/user/permissions/
[GL-QUICK]: https://docs.gitlab.com/user/project/quick_actions/
[GH-BEST]: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
[GH-PAGE]: https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api
[GH-BRANCH]: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-a-branch-for-an-issue
[GL-REST]: https://docs.gitlab.com/api/rest/
[GH-LABELS]: https://docs.github.com/en/rest/issues/labels?apiVersion=2026-03-10
[GL-ISSUES]: https://docs.gitlab.com/api/issues/
[PYGH-ISSUE]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/Issue.py
[PYGH-MAIN]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/MainClass.py
[PYGH-RETRY]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/GithubRetry.py
[PYGL-NOTES]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/v4/objects/notes.py
[PYGL-CLIENT]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/client.py
[PYGL-UTILS]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/utils.py
