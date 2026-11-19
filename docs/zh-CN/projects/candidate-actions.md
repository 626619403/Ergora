# 为已导出的候选发布工单评论

简体中文 · [English](../../projects/candidate-actions.md) · [文档目录](../../README.zh-CN.md)

来源任务到达`REVIEW_READY`后，先按[候选导出](../development/evidence-and-export.md#导出精确候选与恢复回执)导出精确run和candidate。然后读取当前项目revision，准备一条固定的中性评论。tracker绑定须包含外部`token_env`，其账号须能读取`/user`、目标工单并创建GitHub issue comment或GitLab issue note；凭据值只放启动CLI／Web的环境中。无需新增SDK。

```bash
ergora project show PROJECT
ergora issue writeback-prepare PROJECT TASK --revision REVISION --run-id RUN_ID --candidate-sha CANDIDATE_SHA
# 检查返回的完整intent：来源、actor_id、原task/run/candidate/export、body和intent_sha256。
ergora issue writeback-send PROJECT INTENT_SHA --revision REVISION --confirm
ergora issue writeback-status PROJECT INTENT_SHA
```

prepare只做身份读取和本地保存，不发布评论。send只发送保存的正文，不能临时改写；固定正文包含候选和本地导出分支，不复制工单指令、不声称远端分支或合并已完成。同一来源／任务／run／候选操作只有一个意图，重新prepare返回原记录，不能用新请求ID绕过它。其他Agent配置修订后可填写当前revision，原tracker绑定、来源及导出身份仍须保持；绑定或发送账号变化会拒绝未发送意图。发送期间项目修订变化会使最后保存确认失败，原attempt继续保持unknown；即使使用新revision再次send也不会补发。

`acknowledged`表示单次POST的完整201中正文、作者和原生目标已核对，且结果保存成功。send仅在此状态返回退出码0；HTTP也须检查业务status。`prepared`表示尚未保存attempt。attempt在POST前提交，随后任何丢失／不完整响应或中断都会留下`unknown`，包括实际尚未发送的中断窗口；再次send不会补发。status只读本地，不访问tracker。

不知道远端结果时，显式观察当前评论或一页列表：

```bash
ergora issue writeback-observe PROJECT INTENT_SHA --comment-id COMMENT_ID
ergora issue writeback-observe PROJECT INTENT_SHA --page 1
```

列表每页最多100条；沿返回的`next_page`手动继续，每次最多一页。匹配marker、全文和作者只能说明当前可见事实，复制、编辑、删除或空页均不能证明原请求成功或未发送。观察不把unknown升级为acknowledged，不修改旧收据，也不开放重试槽。需要人工处理时先核远端事实，保留原unknown记录；不要另建任务来伪装同次请求重试。

CLI与HTTP共用同一用例；POST沿用Origin及`X-Ergora-Request: 1`保护：

|操作|HTTP入口／正文|
|---|---|
|准备|`POST /api/projects/PROJECT/issue-writebacks`，`{"revision":2,"task_id":"TASK","run_id":"RUN_ID","candidate_sha":"…"}`|
|离线状态|`GET /api/projects/PROJECT/issue-writebacks/INTENT_SHA`|
|发送|`POST .../issue-writebacks/INTENT_SHA/send`，`{"revision":2,"confirm":true}`|
|观察|`POST .../issue-writebacks/INTENT_SHA/observe`，`{"comment_id":"71"}`或`{"page":1}`|

每个HTTP请求20秒socket I/O超时、完整响应上限1MiB，不跟随redirect、无自动写重试；prepare和send还各做actor及目标身份读取，总操作可能超过20秒。GitLab支持普通issue note，成功响应必须明确包含布尔`system`和`internal`，不兼容响应保留unknown。真实服务版本／代理兼容须在自己的测试项目核验。意图、attempt、收据和观察纳入原控制面离线备份；正式任务与导出目录仍另行保存。本入口只创建一条中性评论；GitHub标签见下一节，PR/MR及工单专页按后续片交付。

## 为已导出的候选追加 GitHub 标签

同一个原v7来源任务导出后，可以单独准备一个仓库中已存在的标签。先在自己的GitHub项目建立合适的普通标签，例如`candidate-exported`，并让tracker的外部`token_env`账号具备对应读取／标签写权限。准备只读取和保存，不发送mutation；凭据存在或actor可读不证明标签写权限。

```bash
ergora issue writeback-label-prepare PROJECT TASK --revision REVISION --run-id RUN_ID --candidate-sha CANDIDATE_SHA --label-name candidate-exported
# 检查返回的label_name、native_target、完整operation和intent_sha256，再确认这个摘要。
ergora issue writeback-send PROJECT INTENT_SHA --revision REVISION --confirm
ergora issue writeback-status PROJECT INTENT_SHA
ergora issue writeback-observe PROJECT INTENT_SHA
# 需要下一页时，显式使用上一页page_info.end_cursor；一次仅取一页。
ergora issue writeback-observe PROJECT INTENT_SHA --cursor OPAQUE_CURSOR
```

原REST读取将冻结工单number／native ID、仓库及标签映射为服务返回的GraphQL ID；发送只含一个`labelIds`和原`labelableId`，不按名称写入，不创建标签，不发送整套labels、不移除或替换其他标签。名称包含空格、逗号、引号或Unicode时原样保存，不自行拆分／归一化。GitHub.com使用同源`/graphql`，Enterprise REST `/api/v3`对应同源`/api/graphql`；未知路径、schema／权限不兼容会可见失败，不退回名称REST写入。该路径推导不表示任意Enterprise版本已经实测。

一个来源／creation／run／导出候选只有一个标签追加槽。第一次准备后operand已冻结；重新准备相同名称返回原意图，改名称会拒绝，不能绕过已存在的attempt。标签动作与评论动作各有其原意图，二者复用同一持久生命周期。发送前重核原task／export、当前actor、绑定与原生目标；改名、删除重建或绑定变化会拒绝尚未发送的意图。无关Agent修订允许填当前revision，结果保存仍核同一原attempt和当前expected revision。预检不是服务端CAS，读后目标元数据仍可能变化。

只有单次mutation的完整原200、无GraphQL errors、回显匹配、原Issue／repository匹配，且**原响应所选的一页实际含原label ID、名称和所属仓库**，并保存result后才为`acknowledged`。`clientMutationId`只核回显，不是服务端幂等键。首100项未见目标、nullable／partial data、data与errors并存、丢失／截断响应或结果保存失败都保留`unknown`；已保存attempt后不补发。原响应命中目标可确认，不要求把其他标签翻完，也不表示本次首次新增。

observe通过只读GraphQL query读取当前原Issue的一页，`membership_in_page`只说明该页`present`或`not_seen`；未见不表示标签不存在。即使当前有唯一匹配，或人工已移除、查询空页，也不会确认／重发原attempt。`--comment-id`和非默认`--page`用于评论，不用于标签；标签翻页用不透明cursor。

HTTP准备入口为`POST /api/projects/PROJECT/issue-label-writebacks`，正文是评论prepare的`revision/task_id/run_id/candidate_sha`再加`label_name`。status／send／observe沿上一节的共同`issue-writebacks/INTENT_SHA`入口；标签observe传`{}`或`{"cursor":"…"}`。继续要求同源和`X-Ergora-Request: 1`。标签prepare和首次send各有actor加issue／repo／label三个读取；首次send之后至多一个mutation，status离线，observe是actor加一个query，不后台扫描。每请求仍为1MiB完整响应上限和20秒socket I/O超时，总墙钟不承诺20秒。

当前GitLab标签动作明确不支持，普通工单评论可用；缺少完整目标部署／返回合同及scoped rename并发保证时，不自动改用`add_labels`。标签操作可能产生平台事件、通知和外部自动化，不承诺静默；标签不授批准权，不代表远端发布、合并或工单完成。真实服务版本和账号写权限需在自己的测试项目验证，默认验收只用loopback夹具。

## 在页面准备、发送与观察工单回写

打开“正式任务”，在原v7来源任务的导出记录中选择“准备工单回写”，选择中性评论或一个已存在的GitHub标签，再点击“确认准备本地回写意图”。页面固定原task／run／candidate和当前修订，准备后锁定动作与字段；标签名称原样保存。此时只读取身份并保存本地意图，不发布工单动作。准备回复丢失时，可明确“恢复原准备请求”：已有槽返回原意图，尚无记录时可能首次读取／保存；不要用不同标签或任务绕过原槽。

核对返回的意图SHA、目标工单、账号、候选，以及完整固定评论或标签原生请求。只有`prepared`显示独立的发送确认；勾选核对框后再确认向原工单发送评论或追加标签。发送使用页面显示的项目修订，修订过期需刷新项目后按原SHA重读，不能更换原意图。HTTP成功仍看业务状态；`unknown`不提供补发，`acknowledged`只表示原回执已核且保存。发送回复失败时先“离线读取原意图状态”，关闭窗口不会撤销操作。

“正式任务”顶部的“按SHA读取工单回写”无需项目已登记或原任务文件仍可读。输入原意图SHA后，只读取本项目已保存的intent／attempt／result和最近观察；无需平台在线、token或当前tracker绑定仍相同。读取不会发送或自动观察。发送／观察则仍需要原owner核验的实际依赖；准备返回的已有记录不保证本次没有身份读取，也不保证附带最近观察。

在读回的记录中明确选择观察范围：评论按一个原生ID或一个列表页，标签按一个不透明cursor（留空第一页）。每次只取一资源／页，并保存当前观察；完整结果保留`next_page`或`page_info.end_cursor`供手动下一页。匹配、空页、删除或标签存在均不确认原attempt，不把`unknown`升级或开放重试。查询条件编辑会标记旧观察并移除原发送确认；需明确观察或离线重读，再核对新返回的完整记录。SHA编辑、关闭／替换窗口、换任务／run／项目／视图后，迟到回复不能恢复旧发送入口。所有正文与原记录使用安全文本展示。

## 核对候选与当前远端分支

原v7来源任务已导出后，可读取原来源仓库的当前head与base分支。head名称固定为原export分支，base必须显式指定；工具不会把当前默认分支推断为原任务基线。

```bash
ergora issue candidate-observe PROJECT TASK --revision REVISION --run-id RUN_ID --candidate-sha CANDIDATE_SHA --base-branch main
```

输出分别列出原导出收据、当前本地ref／完整candidate与base commit，以及远端仓库原生ID和两条精确ref。`comparisons`中的`local_export_ref_matches_candidate`、`head_matches_candidate`、`base_matches_task_base`分别表示这三个比较。当前本地分支被移动或远端base已前进时，原收据和冻结base保持不变，比较返回false；本地分支已删除时本地比较为null；远端ref返回404时相应比较为null，`resolution`是`not_found_or_not_visible`。404不能区分不存在与权限不可见，不能据此自动创建。

本地Git读取沿原Linux／WSL2正式执行环境，本入口要求Git 2.43或更新版本并强制`GIT_NO_LAZY_FETCH=1`、`GIT_NO_REPLACE_OBJECTS=1`，未知／更老版本明确拒绝；必须仍有原任务、提交、导出记录和candidate／base commit原对象，不能以`refs/replace`的替代对象通过检查。读取不要求Temporal在线，缺失promisor对象直接报错，不隐式fetch对象、不更新ref或释放claim；原显式导出fetch不受这些只读选项影响。GitHub读取repo及单数`git/ref/heads/...`的精确ref；GitLab先读项目原生ID，再按数字ID读两条分支，完整编码含斜线的分支名。三个平台请求均为GET、无redirect或重试，每个完整响应上限1MiB，socket I/O超时20秒；三次读取和本地操作总墙钟不承诺20秒。原来源binding变化会拒绝；无关Agent设置可使用当前revision。读取期间项目修订变化则拒绝返回旧选择结果，观察不持久保存。

这是分别取得的当前事实，不能发现两次读取之间的ABA，也不能证明谁推送过、原attempt成功或执行瞬间head／base未变化。仓库原生ID是在原来源命名空间下本次读到的身份，原工单快照没有冻结创建时的仓库native ID；命名空间被删除重用等历史不能由本观察排除。不根据本地origin或返回URL改换目标，repo响应仅保留必要白名单字段，不返回临时clone token。

同一查询的HTTP入口为`POST /api/projects/PROJECT/candidate-observations`，正文`revision/task_id/run_id/candidate_sha/base_branch`，继续要求同源及`X-Ergora-Request: 1`。这里POST是本地查询入口；provider只收到GET。该命令不推送分支、不创建或关联PR／MR、不写评论／标签、不批准或合并，`execution_authorized`及`proves_original_attempt`始终为false。确认当前内容相等后，仍按项目自己的发布和人工审查流程操作。

在控制台选择原正式任务，点击“检查原导出记录与恢复”；原v7来源任务的记录为`exported`时，可进入“观察当前候选分支”。页面固定原任务／run／candidate／导出分支及本次项目修订。填写“远端目标分支（base）”，点击“明确查询当前分支”后才调用上述查询；打开和编辑不访问平台。结果分列原目标值、当前读取值、三态比较和各次远端响应的时间／摘要，完整JSON按安全文本展开。

修改目标分支立即使旧观察失效；在途旧回复不会覆盖新选择、关闭重开的窗口或其他项目／任务。失败清楚显示本次错误；再次查询须明确点击，没有轮询或自动重试。读取不要求Temporal在线，仍需要上一节的原执行环境／Git和来源凭据；历史导出保持不变。已有PR／MR关联及评论／标签继续使用各自CLI入口。

## 关联已有 PR／MR 与候选

在自己的项目平台中已建好PR／MR后，可把其明确的仓库PR number／项目MR iid与原v7任务的完整已导出candidate关联。首次关联要求原本地export ref、远端head ref及review head均仍指向该candidate，head名为原export分支，base名为显式输入。仅支持同来源仓库／项目；fork、跨仓库、搜索猜测和任意URL不支持。沿上一节Linux／WSL2 Git检查，不要求Temporal在线。

```bash
ergora issue review-link PROJECT TASK --revision REVISION --run-id RUN_ID --candidate-sha CANDIDATE_SHA --base-branch main --review-number 11 --reason '此资源用于审查原候选'
ergora issue review-link-show PROJECT SAVED_SHA256
```

首次返回`record`含不可变`sha256`和`scope_sha256`、完整来源／task／run／candidate／export身份、当前仓库和review原生ID、全文标题与正文、作者／状态／draft及各次读取摘要和时间。保存的是`operator_asserted_review_context`，`context_only=true`、`execution_authorized=false`、`proves_original_attempt=false`。它不确认原评论或标签attempt、不清除unknown、不批准、不证明资源由Ergora创建。原工单native ID也须与来源快照一致；原快照未冻结历史repo ID，仍不能排除namespace被重用的所有情况。

原task base、当前远端base tip和PR响应`base.sha`分别保留；当前base已前进允许保存，`base_matches_task_base=false`不会改写原基线。GitLab的`diff_refs`可能null或空，代表版本资料未就绪；非空`base_sha`是merge-base，`start_sha`是该版diff的目标commit，均不是当前target tip。`diff_version_head_matches_candidate`单独投影true／false／null，不覆盖MR的`sha`。state／draft按实际值保存，关闭或合并资源仍须符合上述当前refs条件。

一个原候选槽只能保存一个review。同目标／base再次调用返回原`record`、`already_saved=true`、`fresh_observations=false`，忽略新的reason；入口已查到原记录时不重新读取平台。两个首次请求并发时，后保存者可能已读取平台，最终仍返回先保存的原记录；`fresh_observations=false`只描述返回资料，不能证明本次没有发生读取。换number或base明确冲突，不能覆盖。`review-link-show`只需控制面保存记录，离线不要求token、原任务文件、Git或平台仍可见。该记录纳入schema v4备份，load与backup核同一身份合同；外部执行目录仍须单独备份。

HTTP保存入口为`POST /api/projects/PROJECT/candidate-review-links`，正文`revision/task_id/run_id/candidate_sha/base_branch/review_number/reason`，同源及`X-Ergora-Request: 1`保护；离线读取为`GET /api/projects/PROJECT/candidate-review-links/SAVED_SHA256`。首次正常关联向provider发五次有界GET，不持SQLite写锁；每次完整响应上限1MiB、20秒socket I/O、无redirect／retry，完整canonical关联另限1MiB，超限拒绝不截断。总墙钟不承诺20秒。各读不组成共同snapshot／CAS，也不能发现ABA；provider GET可能计算内部派生对象。本地保存不请求平台业务修改，不推送或创建／编辑／合并PR／MR。来源页可读取与保存完整工单；候选动作页面按[接入指南](../../projects/issues.md#project-issue-sources)继续。

控制台从原v7已导出任务的“检查原导出记录与恢复”进入“关联已有PR／MR”，明确填写base、PR number／MR iid和原因后“确认保存已有PR／MR关联”。首次发送固定字段；回复失败时保留原请求，点击“恢复原关联请求”。这不是只读status：原记录存在时返回它，尚无记录时可能重新读取平台并首次保存本地记录。不会自动重试；要修改首次选择，关闭后重新填写，原候选槽已有不同目标时仍由后端拒绝覆盖。

保存后请保留记录SHA。正式任务页顶部“按SHA读取PR／MR关联”可直接离线读取，即使原任务目录不可读、项目尚未登记或当前tracker已改绑；它只读本项目记录。也可在关联窗口下方按SHA读回。正文和完整JSON按安全文本展示，各种base／diff事实单独保留；SHA修改、关闭重开或切项目／视图使旧回复失效。原记录与当时的already_saved／fresh_observations不代表当前远端状态。
