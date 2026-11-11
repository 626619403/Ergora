# F7c-C3b：显式关联已有 PR／MR 的最小合同

日期：2026-11-11。固定提交基线 `93b538fd474120fa05574dcdcf376b7666502c8d`，分支 `refactor/architecture-foundations`。已读取 AGENTS、[PLAN](../PLAN.md)、[C3 原研究](2026-11-11-candidate-publication.md)、[C3a 计划](../plans/2026-11-11-candidate-observation.md)、[当片交付记录](../delivery/2026-11-11-candidate-observation.md)及当前所有者。下文对 C3a 源码的观察属于**未提交候选**，不表示其自身审查、独立审查或精确交付已通过；旧研究也不替代产品验收。

本文只新增此研究文档和忽略目录中的研究原件索引；未修改产品、计划或测试，未安装、运行模型／产品测试、提交或推送。复用原 12 份 body／manifest 重新核算完整性，定向读取官方正文／schema，**新增网络请求为 0**。下文分别标记观察、推导、建议和未核；来源与本轮采集范围见末节。

## 建议：保存一个本地 context 关联

**建议最小行为：** 操作者给定原 task／run／完整 candidate、沿 C3a 明确的 base branch，以及原来源仓库中的一个 PR number／MR iid。用原任务所有者核来源与导出，复用 C3a 的当前本地对象／ref和远端两条 ref 观察，再 GET 指定评审资源。只有原生身份、同仓库／项目、原 export head 名和完整 candidate 均符合本地支持合同时，保存一条不可变的 `operator_asserted_review_context` 记录。CLI 与受保护 HTTP 共用此用例。[当前 tasks](../../src/ergora/tasks.py)、[issues](../../src/ergora/issues.py)、[backend](../../src/ergora/issue_backends.py)

这条记录表示“操作者于此时把这个已观察资源关联到这个原候选”。它不表示 Ergora 创建过资源、原远端 attempt 已发送、head／base 永远不变、PR／MR 已批准／合并或 issue 已完成。现有评论／标签的原 intent／attempt／result／unknown 保持原样；C3b 不通过关联去确认或清除它们，也不引入新的远端发送生命周期。

建议首片支持范围是：**同来源仓库／项目、当前可见且仍存活的原 export head ref、精确原 candidate、明确匹配的 base ref 名**。不支持 fork、跨仓库／项目、任意 URL、搜索／列表自动猜测、只给短 SHA、按标题或 marker 找资源、为关联而修改远端 refs／资源。draft 和 state 实读保存即可，不必额外要求 `draft=true` 或 `state=open`：本地 context 关联本身不授予执行权限。关闭／已合并资源仅在所需当前 refs 仍能精确核对时可首次关联；以后 ref 被删除不会删除已保存的历史关联。

首次保存的明确门槛是：C3a 的 `local_export_ref_matches_candidate=true`、`head_matches_candidate=true`，远端 base ref也已解析；review自己的head名／SHA和base名符合上述合同，repo／source身份完整。false／null不能按“也许相等”通过。只有 `base_matches_task_base` 可以为false，因为它表达原task base与当前base的差异；对应时间点和实际SHA必须保留。

**base 的建议语义：** PR／MR 的实际 base branch 必须等于操作者给定的 `base_branch`；当前 base tip 来自 C3a。原 task base 是否仍等于当前 base 保留为 C3a 的 true／false／null 比较，**不因不相等就隐式换原 base，也不把 false 当成批准失败**。本片记录 context；若未来业务需要“仅允许原 base 完全不变的候选”，由那个消费者另立准入规则。

## 当前所有者与新增接口

|当前观察|建议增量／理由|
|---|---|
|`tasks.exported_source_candidate` 已把原 C1 私有校验上浮，供 `issue_writebacks` 与 `issues` 共用；检查原 v7 snapshot、creation、run、export 和 candidate，维持旧 task 投影 [源码](../../src/ergora/tasks.py)|C3b 继续消费该公开投影，不复制 source-candidate 规则或直接解析原生 run／export 文件；原 C1/C2 intent 字节和 digest 不变|
|`tasks.inspect_export` 委托原 `reference_task_export` 的只读 inspect；当前候选对 inspect 禁 lazy fetch，并检查所支持的 Git 版本／对象 [源码](../../src/ergora/reference_task_export.py)|复用 C3a 的本地事实，不在新用例运行 Git、重新连接 Temporal或重放 export。缺对象／原 ref 漂移具体拒绝首次关联，保留历史导出收据|
|`issues.remote_candidate` 已拥有当次项目修订、来源、当前本地／远端观察和逐项比较；没有持久化 [源码](../../src/ergora/issues.py)|本地关联用例继续放 `issues`：例如 `link_review(state, project_id, task_id, expected_revision, *, run_id, candidate_sha, base_branch, review_number, reason)`；读取已有记录用独立 offline `review_link` 接口。复用原观察合同，不增加通用 publication／operation manager|
|`IssueBackend.repository_refs` 已由 GH／GL 本族实现；上层没有 provider 分派，传输有完整读取、1 MiB 上限、20 秒 socket timeout、无 redirect／重试 [源码](../../src/ergora/issue_backends.py)|增加一个真实消费者所需的 `read_review_request(repository_identity, review_number)`：GH／GL各自定位并核 native 字段。传入 C3a 已见仓库 native identity，GL直接数字项目路由；HTTP、CLI、用例不各自组装厂商路径|
|`issues.link_task`／`issue_task_links` 是 snapshot→creation 的旧 context 关系，主键没有 run／candidate／review；`issue_writebacks` 则有 send、attempt、result语义 [源码](../../src/ergora/issues.py)、[State](../../src/ergora/state.py)|保持两种旧格式；C3b 不把新记录塞成旧 task link 或未发送 writeback。新持久对象归 `issues` 的 context 领域，只加所需一张本域表，见下节|
|State 拥有 schema migration／短事务／旧 writer fence；backup 通过领域 `validate_storage` 离线验证 [源码](../../src/ergora/state.py)、[backup](../../src/ergora/backups.py)|若立片保存关联，migration、旧连接 fence 与 backup/load 校验同片完成；不建立第二数据库、正式 run 账本、调度器、outbox 或恢复队列|

这组接口同时有保存入口和离线读取入口两个实际消费者。单个 link 操作本身已经是明确的本地写意图，无需借远端 send 的 `--confirm`／attempt 状态。可以先展示只读预览，但首片不为此持久化 prepare 状态；若要确认预览中的精确 repo／review native ID，则将这些实际 ID 作为预期输入重新比较，不能只确认可变 URL／number。

## 第一方 GET 合同与易混身份

官方 GitHub 原文是 “Lists details of a pull request by providing its number.”；GitLab 请求表把 `merge_request_iid` 描述为 “The internal ID of the merge request.”。这两个路由号都不是全局资源 ID，也不是源 issue 的 native ID。[GH-PULL][GH-PULL]、[GL-MR][GL-MR]

|读取与字段|推荐支持合同；不是平台所有部署都保证返回的 required schema|
|---|---|
|GitHub `GET /repos/{owner}/{repo}/pulls/{pull_number}` [GH-PULL]|完整 200 JSON；`number` 等于输入；保存 PR 的正整数 `id`、不透明 `node_id`、原 API `url`、`html_url`、`user.id`、title／body、state／draft／merged、created_at／updated_at。number、PR REST id、GraphQL node_id、来源 issue native ID分别保存，不能相互替换或自行编码 Node ID。不要调用 `/issues/{number}` 后把任意 issue 当 PR|
|GH head／base [GH-PULL]|两端 `repo` 都须为可核对象；`head.repo.id/node_id`、`base.repo.id/node_id` 都等于当前 C3a 仓库身份，完整 namespace 与受支持原 API 目标一致。`head.ref` 必须是原 export branch，`head.sha` 必须是完整原 candidate，并与 C3a 远端 head 观察相等；`base.ref` 等于显式 base branch。`base.sha` 单列为该 PR 响应中的 base OID，不用 `merge_commit_sha`、head.label 或 owner显示名代替|
|GitLab `GET /projects/{numeric_project_id}/merge_requests/{iid}` [GL-MR]|先由 C3a 按冻结 namespace 核 project native ID；后续用数字 ID 路由。核 `iid` 等于输入，保存 MR 正整数 `id`；`project_id` 是容纳 MR 的项目，`source_project_id` 是源项目，`target_project_id` 是目标项目。首片三者都须等于 C3a 的 native project ID，以实际字段拒绝 fork，不能把 iid/global id混用。保存 author.id、title／description、state／draft、时间和 web_url|
|GL head／base [GL-MR]|`source_branch` 等于原 export branch，`sha` 等于完整原 candidate且与 C3a 当前 head相等；`target_branch` 等于显式 base branch。当前 base tip仍取 C3a branch GET的 `commit.id`。`diff_refs` 作为该版 diff 的独立可空事实保存；不能从不存在的 `target_sha` 字段补造值|
|当前源 issue [当前来源合同](../../src/ergora/issue_sources.py)|建议额外一次原 `backend.read(source.issue_id)`，核 number／iid 和 native issue ID 等于原 v7 snapshot，且 source API／namespace未变。这能检测“同路径换了仓库并有同号 issue”的常见替换；不采纳新正文、不换 source snapshot，不增加普通 issue写权限要求|

**作者与操作者不同：** 现有 PR／MR 可以由别人创建，`user.id`／`author.id` 保存实际作者即可，不要求等于当前 reader，不把它当本地操作者签名。C3b 不需要调用 `/user` 才能保存本地 context，不因此排除原生支持的只读认证方式，也不新造一套 actor 身份系统。认证仍由原绑定和受保护本地入口拥有；凭据存在不证明资源可见。

GH GET 文档实际列出 pull requests(read) **或** contents(read)，公开资源可匿名；这与 list pulls 的权限表不同。C3a 所需 repo metadata／refs读取及额外 source issue读取仍各受原权限约束，不能只看单个 endpoint 的权限就称整个用例可用。GitLab文档允许公开项目读取，私有资源受 token／项目可见性控制；本轮没有新增真实 token 或最小角色实测。[GH-PULL][GH-PULL]、[GH-REPO][GH-REPO]、[GL-PROJECT][GL-PROJECT]、[原 token 研究](2026-11-11-issue-label-writeback.md)

### 空 repo 对象、异步 diff 与不同时间的事实

**观察：** GH 当前文档样例提供 head/base 的 ref／sha／repo对象；缓存完整 GraphQL schema还明确 `headRepository: Repository`、`baseRepository: Repository` 为 nullable，headRefOid／baseRefOid甚至可在 ref删除后保留。GraphQL字段不能冒充REST schema保证，但足以提醒：评审资源中仍有 SHA，不证明当前 branch／repo仍存在。建议REST收到 `head.repo=null`／`base.repo=null`、缺对象、空／短 SHA时拒绝首次关联，不按 label 或 URL猜回仓库；已保存记录仍可离线读。[GH-PULL][GH-PULL]、[GH-SCHEMA][GH-SCHEMA]

**观察：** GitLab 对 `diff_refs` 的原文是 “Corresponds to the latest diff version of the merge request. Empty when the merge request is created, and populates asynchronously.”；`start_sha` 的说明是 “SHA of the target branch commit. The starting point for the diff.”。其 `base_sha` 是 merge-base，`head_sha` 是该版 diff 的 head。[GL-MR][GL-MR]

**建议：** MR.sha 与 C3a 当前 head 均匹配原 candidate、同项目与两条 ref名符合时，允许保存 `diff_refs=null`／空对象的明确异步覆盖，不把它变成 0／空 SHA或自动轮询。非空 diff_refs 的三个 SHA均做完整类型／格式校验，按原生含义保存；若 diff head与 MR.sha不同，显示 `diff_version_head_matches_candidate=false`，不能偷偷用这个值覆盖 `sha`。对于需要完整 diff版本证据的未来消费者，明确“尚不足”；C3b 不通过它批准代码。

GH `base.sha`、GL `diff_refs.start_sha`、C3a当前base tip、原 task base分开存，比较也分别命名。两次值不同可以表示版本／并发漂移；两次相同也不能检测 A→B→A 或删除再同名同 SHA重建的 ABA。不要为了强行凑齐“统一 base SHA”另发 merge、rebase、update-branch、fetch 或改写原candidate。

### Namespace reuse 能核到哪里

**当前源码观察：** v7 snapshot 固定 provider／完整 API base／namespace、源 issue number／iid和 native ID；未保存“任务创建时的 repo native ID”。C3a返回文字已经明确：repository identity 是现在从冻结 namespace观察的事实。[source](../../src/ergora/issue_sources.py)、[C3a 当前观察](../../src/ergora/issues.py)

**建议：** 首次关联将 C3a当前 repo ID与实际 PR／MR源／目标 repo ID绑定，并重核当前 source issue native ID。每个请求记录各自时间／摘要；相关绑定／项目修订变化拒绝。之后任何“重新观察”须比较原记录中的 repo native ID与review native ID，301／namespace变化／同路径新ID均不能透明采用；404只表示未找到或不可见，不删除原关联，也不证明未创建。

**仍不可承诺：** 上述 GET不是共同事务。GH `/pulls/{number}` 仍按可变名字路由，额外 issue／repo读取可能发生在不同路由时刻；GL数字项目ID减少后续namespace再解析，却不补足创建任务时缺失的repo身份。当前source issue ID相同也不构成历史路径未转移／未重用的证明，移转／redirect内部细节未在本轮核成合同。若业务要求严格的“原历史repo身份”，应为未来任务由其 source owner增加有版本的原生repo身份冻结，不能回填旧v7并称原来就有。C3b只保存这些明确时间点的关联事实。

## 完整读取、正文与预算

建议沿现有 transport：每个外部 GET必须读尽预期的200响应、满足声明长度和1 MiB总字节预算，JSON必须为预期对象；404、redirect、认证／限流、坏JSON、截断和超限都可见拒绝本次保存。304若没有可验证的完整原表示，不是本次完整读取，首片无需引入条件GET缓存。默认无列表／分页／后台轮询；正常路径约为 C3a三次GET＋指定review一次＋原source issue一次，共五次有界读取。不能把20秒socket timeout叫作整个五请求操作的20秒deadline。[现有 transport](../../src/ergora/issue_backends.py)

title／原 `body`／`description` 是不受信任的 context。推荐保存原字符串全文；原生 null如被支持，应保持null，不与空串、缺字段混淆。明确使用 GH raw JSON表示和GL默认原description字段，不请求diff／patch／HTML渲染，不抓comments、commits或任意正文URL。内容不进入工具权限、可信检查、正式任务输入／审批，也不因含 `/close`／“approved”而改变任何状态。外部内容需要展示时按普通文本处理，不把native HTML当可信页面。[GH媒体类型][GH-PULL]、[GL参数][GL-MR]

完整读取不等于保存整个原始JSON：持久化只有所需白名单、raw正文及原字节摘要／时间。GH repo GET可能返回敏感 `temp_clone_token`，不能复制到本地关联、错误或报告。[GH-REPO][GH-REPO] 总JSON响应在1MiB内仍须对最终canonical关联文档做独立字节预算（建议同为1MiB）；若正文加候选事实后超限，明确拒绝、不截断正文后保存“完整关联”。GL的有效description可按字符计达到1,048,576，UTF-8加元数据可能超过本工具字节预算；这属于可见支持上限，不是远端资源无效。[GL-MR][GL-MR]

**GET副作用的准确表述：** GH官方明确 “When you get, create, or edit a pull request, GitHub creates a merge commit to test whether the pull request can be automatically merged…”；这个测试commit不加入head或base branch。GitLab也说明GET时mergeability可异步检查。因此产品可承诺“只向provider发送GET、不请求业务资源变更”，不能承诺provider内部没有任何计算／派生对象写入。也不应为获得mergeable结果额外轮询或将其作为本地approval。[GH-PULL][GH-PULL]、[GL-MR][GL-MR]

## 保存、去重与 backup／load 的最小设计

**建议记录**包含：版本和kind；project／首次保存修订；原 source snapshot摘要及原provider/API/namespace/native issue身份；原task/creation/compiled/run/candidate/export摘要；固定review的provider／repo native ID／route number／review native ID；实际作者、state／draft／merged等原生状态；head/base原生事实、C3a三项比较和逐点时间／响应摘要；完整title／正文、操作者短reason与linked_at。固定 `relationship=operator_asserted_review_context`、`context_only=true`、`execution_authorized=false`、`proves_original_attempt=false`，不产生created-by-Ergora／acknowledged／approved等字段。

保存的是关联当时事实；原task／candidate／approval／claim仍只引用既有所有者身份，不复制一套运行／审批账本。无需把包含本地路径、无关repo设置或临时凭据的整个C3a／repo响应复制进来：可以持久化所需完整事实投影，投影摘要与原HTTP响应摘要分别命名，不冒称保存了未保存的原文。

|持久化事项|建议合同|
|---|---|
|一张本域表|例如 `candidate_review_links(project, scope, sha, document)`，`PRIMARY KEY(project,scope)`、`UNIQUE(project,sha)`。document包含全部必要原生事实，sha为其canonical内容摘要；不另加attempt、result、observation表、status队列或未来未消费字段|
|稳定scope|从project＋原task/creation/run/candidate/export identity派生“评审context关联”语义槽。review number/native ID、base、reason、actor、时间、新snapshot摘要是固定operand／证据，不作为换一个值就能另建关联的逃生口。source原身份仍须相符；同一候选首片只固定一个review|
|重复与冲突|同scope、同请求目标重复调用返回原记录／原sha，不因新观察时间或body编辑插入第二份；返回明确是saved历史事实，不能称fresh读。另一个number、repo/native ID或原候选不符具体冲突，不silent update／upsert覆盖。历史替换／supersede若真有需求，另片显式定义，C3b不猜|
|数据库边界|先核当前expected_revision并查已有scope；没有记录才做有界外部读。GET期间不持SQLite写事务；准备写入时短 `BEGIN IMMEDIATE` 重核当前revision／相关binding和scope，唯一约束决定并发赢家。两份不同目标同时到达只能一份保存；失败方不能覆写赢家|
|本地崩溃恢复|DB commit前崩溃没有关联；重做显式只读采集后再保存即可。commit后本地响应丢失，用原scope／sha读取唯一记录，重复调用返回原记录。这里不需要伪造“远端unknown”，也不能拿本地关联去清除C1/C2真实发送unknown|
|未来创建动作|C3b没有创建PR／MR。以后若立C3d，须显式消费已固定的context槽并拒绝绕过原目标／unknown；不能因新动作kind不同就悄悄再建一个远端资源。当前本地唯一约束仍不保证他人／别的系统未建其他PR／MR|

当前State schema是v3。若实现上表，建议沿现有迁移机制新增版本和这一张表：预迁移备份、事务失败回滚、所有旧表与新表的writer fence一起更新，覆盖迁移前已打开的v3连接；不要仅给新表装trigger而让旧客户端继续写旧表。旧v1–v3备份依原版本读取，不能因为新表尚不存在而误报损坏。[State现有迁移](../../src/ergora/state.py)

`issues`拥有同一个canonical load校验函数，供save、offline show和`issues.validate_storage`共用。至少核schema/kind/flags、全文预算、document sha、scope重算、SQL列与payload目标一致、正整数ID与完整SHA、source snapshot的本域存在性／内容身份及project所属、同repo／原candidate约束。新增记录不能只“JSON能解析”就通过。backup继续调用原`issues.validate_storage`，无须为此增加新的领域导入；离线校验不得发网络、启动reference子进程、读取当前Git或要求远端PR仍可见。[现有领域校验](../../src/ergora/issues.py)、[backup委托](../../src/ergora/backups.py)

离线校验只能验证已保存证据内部和本域引用的一致性，不能证明外部原task／export文件现状或review仍未改变。HTTP／CLI的读已存记录入口始终离线；未来再观察远端时返回新的当前事实／drift，不覆盖原文、原时间或原native ID。首片无需为了支持saved读取而持久化一条不断刷新的latest status。

## 可验收的故障旅程

以下为下一实现片的建议，不是本轮已执行测试。默认使用localfixture和本地Git；不需要安装SDK、模型或真实账号写入。

1. **真实衔接与身份。** 原v7creation／原run／真实本地export→C3a观察→GH number与GL iid分别GET→保存→新CLI进程及HTTP离线读原sha。source issue native ID、PR／MR全局ID、number/iid、repo ID各自核对；同号普通issue、错误iid/global id、wrong repo、fork、null repo、错误head branch或head SHA都拒绝且不写表。
2. **版本事实与漂移。** 当前base前进仍按事实保存C3a false；显式base名与review不符拒绝。GL空diff_refs正常保留“版本未就绪”，非空start/base/head分别保留，不把merge-base当target tip。GET之间移动head、改target、A→B→A、删除同名ref后重建，分别呈现可见差异与不能检测的历史窗口；不输出CAS或可批准结论。
3. **本地唯一性与中断。** 同scope并发相同／不同review、reason变化、响应丢失后重试都只留一个不可变记录；commit前／后退出分开复现。另选review／native repo替换不能借新digest绕过旧slot。既有评论／标签的unknown、result与原task/claim前后保持。
4. **传输与预算。** 200但缺必要字段、截断、非法JSON、字节超限、有效超长Unicode正文、304无原表示、301/302、401/403/404/429与socket失败均拒绝本次新保存；错误不泄漏token／temp_clone_token／服务端任意正文。接收端明确只见有界GET，无create/update/merge/reopen/branch操作、分页或隐式轮询。
5. **历史与可见性。** 首次存下真实draft/state/author，不把作者等同操作者；后来编辑／ready／关闭重开／删除、repo转移／namespace重用、404不可见时，offline记录／原sha仍可读。新读取不得自动接纳同号新native ID或修改原正文；不能称关联证明了远端原attempt。
6. **迁移、load与backup。** 新版迁移成功／失败回滚和旧打开连接fence；旧备份继续校验；新记录sha/scope、ID、candidate、flags、来源snapshot／project等关键字节被改时，普通load与backup使用同一校验拒绝。valid关联的离线backup／restore不访问外网或原Git对象；原issue context／writeback／283冻结资料保持。

## 本轮实际采集范围与未核

**0次新GET；0次provider写入或GraphQL。** 原12份body逐一与 `requests.jsonl` 的bytes／SHA256重算相符，其中原11次200、1次301未跟随，仍属于**前研究**的网络记录。本轮没有把缓存读取算成新网络成功。定向从body 03–08重新生成六份正文文本，另从09完整schema读取所需字段；保存10处官方原文摘录、缓存完整性索引和空的新请求manifest于本片持久忽略原件目录。以下列本文主要复用的原件身份；原完整12行账本保留在[C3研究](2026-11-11-candidate-publication.md)。

|第一方原件|原GET开始UTC／status／bytes／SHA256|本轮实读范围|
|---|---|---|
|[GH-PULL]|2026-11-11 12:39:26／200／892408；`55d8396db608b89f40a42de3164de83c076669eca9de79a30540f3db9dc4eb8d`|get-pull路径、原200对象例子、ID／head/base、media type、权限、test merge及mutable字段|
|[GL-MR]|2026-11-11 12:39:28／200／724730；`d76abdc831450458ea16e5e8cf74c6ed690ff77a3011ccb8ae045b50875d7b18`|retrieve MR完整请求／响应字段表、project/source/target ID、sha、diff_refs语义与异步空值、状态／正文预算／mergeability|
|[GH-REPO]|2026-11-11 12:39:51／200／1414655；`dda154373bc705b6b26f3120f2e477ce8a4ec24e6e4b74bde7f9410093c66d8b`|repository native identity、301、权限与temp_clone_token敏感说明|
|[GL-PROJECT]|2026-11-11 12:39:52／200／572057；`9c971cee3d026cd3aa46ce22727661dcc94b061b3127a718b23151912e032b05`|数字ID／namespace路由、path_with_namespace、原生ID与字段可见性|
|[GL-BRANCH]|2026-11-11 12:40:04／200／104794；`1e5920dfb5f3669086b8fdac43c44b05621da8fe12d07dfd03ae47c61a523010`|当前branch commit.id与C3a语义，未实际访问branch API|
|[GH-REF]|2026-11-11 12:40:05／200／347595；`8bad8465449b941bb2f9905c6a065d466bf45e2e71039346c2e34e3099d9e556`|精确ref／matching差别和当前OID，未实际访问ref API|
|[GH-SCHEMA]|2026-11-11 12:40:44／200／1584905；`46f1d455d72ab784c6cb2b86e9b023df195dcfd2ed92099108b0faa5faa5d1fc`|PullRequest headRepository／baseRepository nullable和ref删除后保留OID的描述；未用此替REST schema|

前次GitLab drafts／GitHub创建指南301和其他旧源码只做缓存hash核对，不作为本轮新增读取成功或新增事实。新请求manifest为空，因此没有新原URL／最终URL／时间／状态／body可报告；原manifest没有单列final URL字段，本文不补造。所有引用均指第一方官方来源；滚动REST文档版本与目标部署仍不同，GH参考query是2026-03-10，产品当前默认版本仍由binding拥有。

未核：真实账号权限、完整真实PR／MR与null／redacted字段返回、namespace转移／iid历史复用内部机制、所有Self-Managed/GHES版本、GL最新schema、GET派生对象的完整内部副作用、真实并发ABA、provider历史event因果能力，以及新持久表／migration／backup实现。本文没有创建或关联真实资源，也没有完成产品验收。推荐的是可独立立片的本地context关联；严格历史repo证明、远端创建、CAS和原unknown自动恢复仍不可承诺。

[GH-PULL]: https://docs.github.com/en/rest/pulls/pulls?apiVersion=2026-03-10
[GL-MR]: https://docs.gitlab.com/api/merge_requests/
[GH-REPO]: https://docs.github.com/en/rest/repos/repos?apiVersion=2026-03-10
[GL-PROJECT]: https://docs.gitlab.com/api/projects/
[GL-BRANCH]: https://docs.gitlab.com/api/branches/
[GH-REF]: https://docs.github.com/en/rest/git/refs?apiVersion=2026-03-10
[GH-SCHEMA]: https://docs.github.com/public/fpt/schema.docs.graphql
