# F7c-C3：远端候选核对、分支发布与草稿 PR／MR 的边界

日期：2026-11-11。研究基线为 `b5ee397e6571f95393b0f8d6e9ee7e6d947b0935`，分支 `refactor/architecture-foundations`。已读取 AGENTS、[当前检查点](../PLAN.md)、[F7 计划](../plans/2026-11-11-project-trackers.md)、[C1 计划](../plans/2026-11-11-issue-writeback.md)、[C2a 计划](../plans/2026-11-11-issue-label-writeback.md)和相关所有者。工作树中的 C2a 实现及其独立审查／交付由主工作流负责，本文不属于 C2a 候选。

本文只新增研究文档；未修改产品、测试或计划，未读凭据、安装／运行 SDK、运行模型、发送真实 API 写入或 GraphQL、提交或推送。**观察**指本地源码或已取得的第一方文档／schema；**推导**是由这些事实得到的限制；**建议**是待实现合同；**未核**不是已通过行为。新网络预算止于 12 次无凭据 GET，逐次元数据见文末。

## 建议采用的下一片

**C3a 先实现只读远端候选核对。** 对一个原 v7 来源任务、原 creation／run／已导出精确 candidate，读取当前本地 Git 对象事实，以及冻结来源仓库的原生身份和两条指定 branch ref；分别比较 head 与 candidate、base 与原任务 base。CLI 与受保护 HTTP 消费同一个用例，不 push、不创建 PR／MR、不新增持久表或正式状态机。它有直接消费者：操作者先确认候选确实在所选远端，后续“显式关联已有草稿”再消费这一事实合同。[本地 export](../../src/ergora/reference_task_export.py)、[任务接口](../../src/ergora/tasks.py)、[GitHub refs][S8]、[GitLab branches][S7]

只读核对比“push 后立即 create”更小，原因是后者至少有两个独立副作用：分支可能已发布而 PR／MR 未建，创建已生效而响应丢失，或两个步骤之间 ref 改变。Git 的 `--atomic` 仅涉及同一次远端 ref 更新，不把托管平台 PR／MR API 包含进事务。REST 创建接口及本次所读 GraphQL 创建输入均没有 expected head／base SHA 条件，读后比较不能承诺原子绑定。[git-push][S2]、[GitHub pulls][S3]、[GitLab MR][S4]、[GH schema][S9]、[GL 固定参考][S10]

|建议分片|具体出口|留给后片的边界|
|---|---|---|
|C3a 当前最小片：只读核对|同一用例经 CLI／HTTP 返回仓库原生 ID、精确 ref／OID、本地原候选与 base 对比、逐次读取时间／摘要、实际覆盖与错误；默认只用 local fixture|没有远端创建收据；不把一致的当前 ref 称作原 attempt 成功，也不自动读取／选取任意现有 PR／MR|
|C3b 显式关联已有 PR／MR|操作者给定 repository＋number／project＋iid，按原生 ID 读回；本地记录“操作者在此时将这个资源关联到原候选”，重用 C3a 的候选事实|仅本地关联；不修改远端标题、正文、draft、issue link 或 refs；不冒充 Ergora 创建过该资源。先定义本域最小记录和 backup 校验，不为 C3a 提前建表|
|C3c 分支发布研究后再定片|只有明确满足“不覆盖任何既有人工 ref”的条件创建原语时，才设计一次显式发布与原 attempt 恢复|本轮不以 force 选项绕过限制；普通 push 的快进窗口尚不能满足该强合同，故不作为紧接着必须实现的动作|
|C3d 独立创建草稿|已有远端精确候选之后，另一次明确确认、一份原生创建请求、完整原响应核验；branch 发布和 PR／MR 创建分别保存自己的事实|不得把组合按钮包装成原子发布；严格的执行瞬间 head／base SHA 不变保证仍不可承诺，不能满足时显示 unsupported／blocked|

以上是研究建议，不是四片已经立项或通过。C3a／C3b 可以在没有自动 push 的情况下独立可用；原六阶段、candidate／approval、shared claim、既有 attempt-before-send 和 unknown 恢复保持，仍由原 Temporal／task 所有者管理正式执行。

## C3a 可直接转成计划的接口与归属

以下名称是建议，不表示源码已有这些入口。首片只支持原来源仓库内的两个分支；fork、跨项目目标和任意第二 remote 暂不推断。默认 head 名可取原 export branch，base branch 必须由操作者明确指定，不能把当前 default branch 默认为原任务 base。

|所有者|已观察事实|建议的窄增量与实际消费者|
|---|---|---|
|[tasks](../../src/ergora/tasks.py)、[reference_task_export](../../src/ergora/reference_task_export.py)|`export_status` 读保存的 intent／attempt／result；它不查询远端，且 `status` 不调用 `branch_sha` 验证当前本地 ref。原 export 只接受原完成的 REVIEW_READY candidate，曾通过本地条件 `update-ref create` 发布并处理原 claim|增加公开 `tasks.inspect_export(..., run_id, candidate_sha)`，由原 export owner 增只读操作：验证原收据／原 ID，给出原 spec `base_sha`、保存的 candidate、当前本地 export ref OID、candidate／base 对象是否为 commit。C3a 消费这一投影，不从观察层导入私有 `_Export`、解析原生 run 文件或重判 REVIEW_READY|
|[issue_backends](../../src/ergora/issue_backends.py)|已有本族 ABC／局部 registry、固定 API base、认证上下文、无 redirect／自动重试的有界 HTTP；本次工作树另有 C2a 的实际 GraphQL 标签能力|增加实际需要的只读方法，例如 `read_repository()` 与 `read_branch(repository_identity, branch)`。具体实现拥有 URL／编码／权限／原生映射；上层不按 provider 分派。后续按需增加 `read_review_request`，不预建通用 Forge SDK 或副作用接口|
|[tasks](../../src/ergora/tasks.py) 的共有来源／export 投影|现有 `issue_writebacks._candidate` 已消费 task／creation／export 与来源，但这是该模块私有函数，新观察会成为第二个真实消费者|把同一 source／creation／run／candidate／export linkage 上浮为 tasks 的窄公开接口，例如 `exported_source_candidate(...)`，委托原 snapshot／source 校验。原 writeback 和新观察都消费它；原 C1/C2 保存的 task/source 投影与 digest 字节保持，新增 base／本地对象事实不要悄悄加入旧 intent 格式|
|[issues](../../src/ergora/issues.py) 的观测用例|该模块已拥有 project-scoped observations、固定 binding／配置与 context_only 合同，已有 task context link 消费者|提供 `remote_candidate(state, project_id, task_id, *, expected_revision, run_id, candidate_sha, head_branch, base_branch)`；调用 tasks 的共有来源投影、原 export 只读对象投影和 backend，只拼接事实／比较。C3a 无需新用例模块，更不预建通用 publication／operation manager|
|[CLI](../../src/ergora/cli.py)、[HTTP](../../src/ergora/web.py)|现有 task／issue 用例均有双入口和当前修订保护|建议 `task remote-candidate PROJECT TASK --revision … --run-id … --candidate-sha … --head-branch … --base-branch …`，以及同一只读用例的受保护 HTTP 入口。HTTP 可用带显式参数的只读 POST；这只描述本地查询入口，不授权对 provider POST。两者不各自做 Git／HTTP 协议|
|[projects／bindings](../../src/ergora/projects.py)、[source](../../src/ergora/issue_sources.py)、[State](../../src/ergora/state.py)|项目修订、完整来源 API／namespace 与 immutable source snapshot 已有所有者|读取当次固定配置与原 v7 来源；相关 tracker binding 漂移拒绝，其他无关 Agent 设置变化按现有规则处理。网络期间不持 DB 写事务。C3a 不保存 canonical publication 记录、不改 State schema，也不创建后台队列|

`inspect_export` 应复用原取消／进程清理边界，只调用必要的本地 `symbolic-ref`／`rev-parse`／`cat-file`，不 fetch、checkout、update-ref、写 export intent 或重新释放 claim。原 `status=exported` 是历史已导出收据；“当前本地 branch 仍指向该 candidate”是新增观察，两者不能混作一个事实。[原状态与分支实现](../../src/ergora/reference_task_export.py)

**建议返回合同：** 原 project revision／配置摘要、原 source snapshot／creation／run／export 摘要；完整 candidate SHA 和任务 `base_sha`；当前本地 head ref／OID／对象类型；远端 API 身份、repository native ID／完整 namespace；明确的 `refs/heads/...` head／base 名、每次实际 OID、各自观察时间／响应摘要；`head_matches_candidate`、`base_matches_task_base`、`local_export_ref_matches_candidate` 分别给出 true／false／不可判断，并保留实际原因。顶层明确 `context_only=true`、`execution_authorized=false`、`proves_original_attempt=false`。不设置笼统的 publication success 或 safe-to-send 标志。

比较只要求精确全长 OID 相等，不用 branch 名、短 SHA、标题、GitHub `merge_commit_sha` 或 GitLab merge-base 替代 candidate。对象格式不被目标平台支持时具体拒绝，不把 40／64 位 SHA 互转。GitHub 文档的 refs 对象使用 SHA-1；本地 export 允许两种长度，这不证明该远端支持所有本地对象格式。[本地约束](../../src/ergora/reference_task_export.py)、[GH refs][S8]

**本片有用的拒绝／差异：** head 不可见、head 指向另一 commit、base 已前进、相关绑定变化、本地 export branch 被移走、原对象缺失，均应呈现具体差异；不隐式更新原 base、重新导出、fetch 任意远端历史或重新跑任务。判断祖先关系不是首片必要条件：原 base／candidate 已由原 task 所有者固定；如果未来消费者需要远端 merge-base，再单独定义所需对象和有界读取。

### 两家只读协议的实际差别

|事项|GitHub REST|GitLab REST v4|
|---|---|---|
|仓库身份|`GET /repos/{owner}/{repo}`，核 `id`、`node_id`、`full_name`、原 API URL；可见时读取 `clone_url`／`ssh_url`、default branch 作为元数据。普通名字不是永久 native ID [S5]|`GET /projects/:id` 支持 URL 编码的完整 namespace 或 numeric project ID；核 `id`、`path_with_namespace`、原 API URL，HTTP／SSH repo URL 只作已核元数据。得到 native project ID 后，后续本族请求优先用该 ID，避免继续依赖可变路径 [S6]|
|精确分支|`GET /repos/{owner}/{repo}/git/ref/heads/{branch}`（此 GET 路径为单数 `ref`）；核返回 `ref` 完全相等、`object.type=commit` 与完整 `object.sha`。**不能使用 matching-refs 的非空结果代替存在性**，该接口即使原 ref 不存在也会返回同前缀其他 ref [S8]|`GET /projects/{native_id}/repository/branches/{encoded_branch}`；核 `name` 及 `commit.id`，`protected`／`can_push` 只记录当时事实。分支含 `/` 时由 adapter 完整 URL 编码，不拆成 namespace [S7]|
|读权限|仓库 metadata(read)、refs contents(read)；公共资源文档允许匿名。读 PR 则另需 pull requests(read)，不可把已有 issues 权限当作全部仓库权限 [S3][S5][S8]|公共 project GET／branch GET 支持匿名；私有资源须真实可见。先前已核的 legacy token `read_api`／`api` 与项目资源范围适用于 API 读取；不把 `write_repository` 当全部 API 写权限 [S6][S7]、[原 scope 研究](2026-11-11-issue-label-writeback.md)|
|结果缺失／变化|repo GET 可返回 301；本工具不带凭据跟随。先拒绝并让操作者核原 binding/native ID，不能透明采用新 namespace。404只记录 `not-found-or-not-visible`，不当作已证明不存在／可以安全创建 [S5][S8]|字段随可见性／权限变化；404同样只记录 `not-found-or-not-visible`。仓库不可见与 ref 不可见都不能伪装成空列表或已证明未创建 [S6][S7]|

**推导：** 即使两条 ref 在同一次查询操作中都匹配，也只是分别读到的当前事实，不是服务端共同 snapshot。API 返回同一 candidate OID，只证明所观察 ref 命名了相同内容寻址 commit；不证明本地 repo 的 origin 属于该 provider repo、谁 push 了它，或这些 refs 在任何中间时段未改变。首次 C3a 直接以原冻结来源 binding 选 API 仓库，不从本地 `origin`、issue URL、commit author 或任意返回 URL推导新的授权目标。本轮没有核成两家“repo＋两ref放一个query”的完整 GraphQL selection；推荐直接采用上述三次 REST GET，不为减少请求数猜字段，也不把一个 GraphQL HTTP 请求自动视作原子快照。

**敏感字段边界：** GitHub repo 文档明确 `temp_clone_token` 可能随响应返回，属于临时凭据。只完整读尽响应并计算摘要，领域投影仅保留所需白名单字段；不因“完整响应”就把整个 repo JSON、headers 或临时 clone token写进公开文档、DB 或日志。merge 设置也受额外权限影响，字段未返回不等于 false。[S5]

## 普通 Git 发布能复用什么，不能承诺什么

**观察：** `ls-remote` 返回 `<oid> TAB <ref>`；`--exit-code` 在无匹配时返回 2，默认成功退出不表示必有匹配；patterns 是 glob；`--symref` 当前只报告 HEAD 的符号目标。它不提供 provider repository native ID，也不下载对象。若将来用于观察，需请求明确完整 ref 并再次精确比较返回名，不能把一次 exit 0、模糊匹配或 HEAD 当候选。[S1]

**观察：** 普通 `git push <url> <candidate_sha>:refs/heads/<branch>` 可创建分支，也允许快进既有分支。`--porcelain` 区分新 ref `*`、up-to-date `=`、快进、强制 `+`、删除 `-`、拒绝 `!`；文档另列 `remote failure`，包括网络断开而未报告结果。`--atomic` 是远端 refs 事务且要求服务端支持，不是“只准创建不存在分支”，也不覆盖 PR／MR API。[S2]

**推导：** “GET／ls-remote 看到不存在，再普通 push”仍可能在后续 push 的 advertisement 前出现人工 ref；若它指向 candidate 的祖先，普通 push 可快进它。因此不能同时把这一路径称为“普通 push”且承诺“绝不更新人工 ref”。新名字、随机 nonce、发后只接受 `*` 状态能降低碰撞或发现异常，不能撤销已经发生的快进。

官方 `--force-with-lease=<full-ref>:` 的空期望确有“该 ref 必须不存在”语义，但属于 force 选项族。本轮明确**不将该选项纳入下一片，也不建议用它改写既定不强推要求**。公开 REST create-ref／create-branch 有独立创建操作，但前提是候选对象已经存在于服务器；它们不把本地新 commit 的对象上传和 ref 创建变成一个已核合同。现有证据不足以给本项目自动发布一个既满足严格无覆盖、又完成任意新对象上传的实现承诺。[S2][S7][S8]

|复用点|具体边界|
|---|---|
|原 export 的 Git／取消 owner|`reference_task_export.git_process` 已负责可取消 Git、进程组清理、禁 hooks 和部分环境隔离；原冻结 `core.git` 同步 timeout=120，不适合直接冒充新的有界网络 owner。扩展实际 Git 操作时在现有所有者内复用必要执行边界，不能让 CLI／Web 各写 subprocess|
|原进程清理机制|[processes](../../src/ergora/processes.py) 有 timeout／进程组和 Windows Job 清理；它是命令执行事实，不包含 Git remote 身份、ref CAS、远端 actor 或 PR 因果收据。原 export 自身是 Linux／WSL2 路径，不能凭通用 Windows runner 宣称其新网络 Git 已跨平台实测|
|将来固定的远端意图|Git 可有多个 `pushurl`、`url.*.insteadOf`／`pushInsteadOf` 重写；只冻结 remote 名或 `remote -v` 展示不足以约束实际目标。需检查最终唯一 endpoint／支持协议及配置影响，禁止任意 helper／receive-pack／push options 等隐式扩大操作。此处为待核实现建议，原 export 禁 hooks 不代表清除了全部 repo 级网络配置 [S2]|
|attempt 与恢复|保存原 intent、精确源 OID／目的 ref／endpoint 之后，先提交本动作 attempt 再最多一次网络 push。死在发送前也保留 unknown。事后相同 OID／ref、porcelain 丢失或 ref 不见，只能保存当前观察；本地 Unix actor／commit author 都不是托管平台 push actor。不能因当前 ref 匹配／不存在而自动重发或删除补偿|

新 branch 的 native receipt、后来人工删除／重建、服务端 hooks／CI／通知和真实传输权限都未实测。本轮没有执行任何 `ls-remote` 或远端 Git 命令；上面是官方协议与本地 owner 静态事实。

## 后片若创建草稿：必须冻结的原请求与原响应

以下是可验收的 **REST 方案合同建议**，不是 C3a 的实现范围。操作者必须先看到完整标题／正文、原候选、仓库身份、head／base 名及预检 OID、actor 与所有副作用开关，再按精确 intent digest 明确确认。原 intent 和逻辑 scope 一经建立不得重定位；提交 attempt 后只执行一次请求。C1/C2 的“未知不重发”原则继续成立。[原 writeback 生命周期](../../src/ergora/issue_writebacks.py)

|创建动作|明确且最小的 payload|完整原返回的必要核验|
|---|---|---|
|GitHub `POST /repos/{owner}/{repo}/pulls`|固定中性 `title`／`body`、`head`、`base`、`draft=true`、`maintainer_can_modify=false`；首片只支持同 repo。**不发 `issue`**：该参数会把现有 issue 的标题／正文／评论转换进 PR；不是普通关联。跨 repo 的 `head_repo`／fork 网络关系另片 [S3]|原完整 `201`，JSON 对象；`id`／`node_id`／`number`、原生 API URL与 `html_url`；`user.id=原actor`；raw title/body 精确相等；`state=open`、`draft=true`；`head.ref/sha/repo.id/node_id/full_name` 与冻结源匹配；`base.ref/sha/repo.id/node_id/full_name` 与冻结目标匹配；相关 switch 和 `created_at/updated_at`。URL只核其原生目标，不按任意返回 URL发带凭据请求。`head.repo=null`、缺必要字段或任一 SHA 漂移不能算完整候选确认 [S3]|
|GitLab `POST /projects/{native_id}/merge_requests`|固定 `source_branch`／`target_branch`、以 `Draft:` 开头的中性 `title`、中性 `description`；显式 `allow_collaboration=false`、`remove_source_branch=false`、`squash=false`；首片同 project，不发 labels、assignee、reviewer、milestone、merge_after、auto-merge 等。当前 REST create 表**没有独立 draft 参数**，draft 来自官方支持的标题前缀；不能照搬 GitHub payload [S4][S11]|要求原完整 `201` 及资源 JSON（POST→201规则沿[C1官方错误码研究](2026-11-11-issue-writeback.md)）；核 `id`／`iid`／`project_id`、`source_project_id`／`target_project_id`、原生 URL；`author.id=原actor`；title/description 精确相等；`state=opened`、`draft=true`；source/target branch 精确相等，`sha=原candidate`。保存实际协作／cleanup／squash／auto-merge字段和时间；若返回 `diff_refs`，head_sha 比 candidate、start_sha 比预检目标 tip，**base_sha 是 merge-base，不能当 target tip** [S4]|

“完整”首先是读尽原 HTTP body、未截断／未超限、正确成功状态和必要字段类型；随后才是业务匹配。不是把文档样例所有字段当 required schema，也不是只看状态码、URL 或 PR number。响应字节摘要与必要原生字段属于原收据；错误文本及无关／敏感字段不任意原样持久化。完整原响应的某字段值不合合同，远端副作用仍可能已发生；拒绝本地确认不会撤销远端创建。

**GitLab 的真实缺口：** 文档说明新建 MR 的 `diff_refs`／`changes_count` 最初为空，之后异步填充；prepared_at 只首次填入，并包括创建 diff／pipelines、检查 mergeability、关联 LFS 和通知等步骤。文档的 create 示例甚至是 `state=merged,draft=false`，它只能提供字段形状，不能直接当新草稿 fixture。若严格结果要求原 `201` 同时证明原 head／base SHA，而该部署返回空 diff_refs，不能用后来的 GET 伪造原201的 base 证据：保留原201已见 native ID／摘要为证据与原 unknown，不再创建。C3d 必须在计划中决定这个真实异步限制的支持范围，不能写“轮询后就证明创建瞬间精确 base”。[S4]

**GitHub 的相邻字段不可借用：** `merge_commit_sha` 会随合并方式表达测试 merge commit／真正 merge／squash／rebase 的不同结果，不能拿它核 candidate。REST merge 的 `sha`、update-branch 的 `expected_head_sha` 和 GraphQL `UpdatePullRequestBranchInput.expectedHeadOid` 是其他写操作的条件；create pull request 输入并没有这些前置字段。不得为了获得 CAS 而调用 update-branch，因为它会改变候选。[S3][S9]

发送前以同次固定凭据取 `/user` native ID并重核原 actor、repo／head／base；当前 actor 认证能力沿原 C1 支持范围。GitHub App installation token 被 REST PR endpoint 支持，并不表示现有 `/user` actor 解析已支持它；未实现明确 App→bot 身份解析时仍应显示 unsupported。GitLab sudo／代用户、job token 和新 fine-grained token 的此动作支持也不能据凭据存在推定。[C1 主体边界](2026-11-11-issue-writeback.md)、[S3]

### 唯一 scope、已有关联与 unknown

**建议本域唯一语义槽：** 原 project＋task／creation＋run＋candidate＋export identity 的“候选评审发布／关联”只能固定一份原 PR／MR 目标。repo、head／base、actor、正文、snapshot 新摘要是冻结 operand／证据，不作为换一个值就能再创建的去重逃生口。同一语义槽的“显式关联已有资源”与“自动创建资源”也不能各开一个独立槽。一个真正新的业务候选仍由原任务所有者产生新身份，不能以重建 write ID、重选 SDK 或换 namespace 绕过旧 unknown。此 scope 是本地约束，不保证别人或另一系统没有创建第二个 PR／MR。

|看见的情况|必须保留的事实|
|---|---|
|完整且匹配的原创建响应和 result 已保存|保留原 PR／MR native ID和原收据；后来按号 GET 是当前事实。编辑／关闭／重开／删除不会擦除历史创建收据，也不触发再建|
|attempt 已保存，原响应丢失／截断／字段不符／result 保存失败|原操作 unknown。按精确 native ID（若确知）或显式列表只读查当前事实；查到唯一 marker、同作者、同 head/base／SHA 也不能归因为原 attempt。不得因为空列表、422 duplicate、404 或唯一命中自动补建或确认 exactly-once|
|操作者明确给出一个现有 PR／MR|核当前 native ID／number或iid、仓库、实际 author、draft、branch／SHA，保存“operator asserted association at time”及所读证据。existing author 可以不同于当前 reader；不能伪称是原发送 actor，也不将这份关联升格为原 unknown 的发送收据|
|原 PR／MR 已关闭、又重开，或同分支后来建新 PR／MR|仍固定原 native ID；state 是观察。不能取“当前 open 的那份”覆盖原关联，不能自动 reopen／新建。GitHub update 支持 open／closed；GitLab update 支持 close／reopen，GitLab还有删除 MR接口，均说明当前集合不是历史账本 [S3][S4]|
|人工改标题／正文／draft／target branch，head／base ref 改变|原意图／收据不变，另记 drift；不用“恢复”改回人工内容，不重新生成正文或批准。ref 从 A→B→A，或删除再以同名同 SHA重建，是 ABA：两次相等读不能证明中间未变化|

已有资源的显式关联也可能指向一个未来会关闭 issue 的 PR／MR；本地中性关联不能替它作“不关单”保证。若业务要求既有资源完全无 closing relation，还需读取它的真实关系／内容并承认读后竞态；首片不把这种检查写成已有原子保证。

### 列表与分页只证明本轮可见范围

GitHub `GET /repos/{owner}/{repo}/pulls` 默认只列 open，支持 `state=all`、head 的 `owner:branch`、base、sort／direction、每页最多100；这些是筛选，不是唯一约束。GitLab项目列表 `GET /projects/{id}/merge_requests` 支持 source_branch／target_branch／source_project_id，默认 scope 是 created_by_me，state 默认 all；若要查看其他作者或关闭资源，必须显式 `scope=all`／`state=all` 并仍检查原生身份。不要依赖仅新版本才有的 draft filter去证明旧部署没有草稿。[S3][S4]

后片可先只做操作者给定 ID的单资源读取，避免为“自动猜原创建”扩大扫描。确需列表时复用现有 pagination owner 的同源固定目标／过滤校验与有界 page、byte、deadline；continuation 仅来自原生 Link／X-Next-Page，不能凭少于100项断言历史不存在。翻页中新增、编辑、关闭／重开、权限变化和删除会漏项或重复；即便遍历到本轮最后一页也不构成历史稳定快照。分页页链／覆盖和 `proves_original_attempt=false` 必须可见。[既有分页第一方依据与限制](2026-11-11-issue-writeback.md)

## 中性内容与默认开关的真实副作用

**建议内容：** 标题只用固定的 `Ergora candidate <短显示值>`；GitLab额外固定 `Draft:` 前缀。正文使用固定事实句，给出完整 candidate、原 task／run／export 摘要、预检 head/base 名与完整 SHA、来源 native identity／snapshot 摘要；branch／run 等不透明值沿 C1 的转义方法放入普通文字。完整 SHA用于核对，短显示值不参与身份判断。只说明候选事实，不写“approved／done／closes／fixes”等业务结论，不复制 issue 标题、正文、提交信息或模型输出。

**观察与限制：** GitHub `issue` 创建参数是转换 issue；手工 linked PR／closing keyword 在相应默认分支 merge 时有关闭语义。GitLab此前已核官方说明：某些 GraphQL／Work items widget link 即使没有 closing pattern，也会在 MR merge时关闭 issue。因此“显式关联”不当然中性；默认只保存本地关联／普通受控引用，不调用关闭关系 API、不建由 issue 派生 branch／MR 的自动流程。现有 candidate 的 commit message 本身也可能含 closing pattern；本工具不能改写原 candidate 来清洗它，不承诺将来的合并绝不关单。[C1 的关闭关系纠正及原第一方证据](2026-11-11-issue-writeback.md)、[GitHub link][GH-LINK]、[GitLab issue管理][GL-MANAGE]

|默认开关／副作用|待实现时应怎样解释|
|---|---|
|draft|GitHub create 明确 `draft=true`，不是在 title 加 Draft 就当原生draft；GitLab 当前 RESTcreate 依官方 title 前缀并核原响应 draft=true。GitLab draft在移除 flag前阻止 merge，人工仍可变更。draft不等于本地 approval，不阻止通知、pipelines 或其他自动化 [S3][S4][S11]|
|maintainer edits／collaboration|GitHub GraphQL `maintainerCanModify` 默认 true，必须显式 false；REST也显式 false并核响应。GitLab显式 `allow_collaboration=false`；该字段只在 fork场景有意义，不能撤销原本就有 repo写权限的人的权限。两个 false都不是 refs锁 [S3][S4][S9]|
|source branch cleanup|GitLab请求 `remove_source_branch=false`，仍核 `should_remove_source_branch`／`force_remove_source_branch` 和可见项目设置；GitHub repo有 `delete_branch_on_merge` 设置。创建草稿不在本片删除 branch，也不能保证未来 merge者或项目设置不会删除；必需的字段不可见时按 unknown说明，不默认false [S4][S5][S6]|
|squash／merge方式|GitLab请求 `squash=false` 仍可能被项目 Require／Do not allow设置覆盖；不传时直接继承项目 squash option。GitHub create没有选择最终merge method的参数，不能用允许squash的repo设置推断实际merge结果。原candidate SHA不等于未来squash／rebase产物SHA [S3][S4][S5][S6]|
|通知、异步对象与CI|GitHubcreate明确触发通知，并会为mergeability生成不加入两端branch的测试merge commit；GitLab准备步骤包括pipelines、LFS、通知。不会主动调用merge并不意味着平台没有其他副作用，也不能承诺hooks／组织自动化无动作 [S3][S4]|

正文中的普通 issue引用可能产生cross-reference或通知；若要求首片连这种关系都不新增，可只保存native source身份与snapshot摘要于本地，不生成可被解析的 `#number`／issue链接。它不解决原commit、项目closing配置或外部自动化的副作用；这些不能靠措辞承诺消失。

## REST、GraphQL 与 SDK 的实际选择

|方案|本次第一方观察|对本项目的建议|
|---|---|---|
|现有 stdlib REST adapter|C3a只需repo和两条精确ref读取；GH／GL均有原生接口。REST创建可提供独立201原资源响应，但GH目标仍按owner/repo路由，GL可用已核numeric project ID；两家create均按branch name取head/base [S3][S4][S7][S8]|C3a沿现有adapter／无redirect／预算／字段映射，免增依赖。文档按2026-03-10阅读，不修改现有binding默认2022-11-28；版本不支持明确拒绝。REST201方案保留上文严格合同与路由／ref竞态，不称CAS|
|GitHub `createPullRequest`|完整FPT schema的 `CreatePullRequestInput` 有 required repositoryId、baseRefName、headRefName、title；可选headRepositoryId、draft(default=false)、maintainerCanModify(default=true)、body、clientMutationId；没有expectedHeadOid或expectedBaseOid。payload只有nullable pullRequest和clientMutationId [S9，行9484–9547]|若后片强制避免mutable repo namespace路由，真实returned repo Node ID比REST名字路由更合适；现有C2a已有GraphQL传输，不能笼统说“另引GraphQL成本太大”。但它仍不解决ref SHA竞态，也没有201：需另定完整200／无GraphQL errors／原ID与head/base的selection合同。不能拿clientMutationId当服务端幂等键|
|GitLab `mergeRequestCreate`|固定18.5参考输入为projectPath、sourceBranch、targetBranch、title，另有description、labels、mergeAfter、removeSourceBranch、clientMutationId；没有expected SHA、repository GID、draft／collaboration／squash参数。payload有errors、nullable mergeRequest、clientMutationId [S10，行9279–9305]|对本片无已证实CAS增益，且REST有更直接的开关。首片不为创建改用这条GraphQL、不猜不存在字段；不能由18.5字段推出最新／任意Self-Managed都相同。GHES／GitLab GraphQL endpoint与token差别沿既有研究，不在C3a发任何GraphQL|
|PyGithub 2.10.0／python-gitlab 8.6.0|沿前研究静态读且重算hash的官方发行wheel：PyGithub默认GithubRetry允许POST／部分403／5xx；python-gitlab默认rate-limit重试循环可重试POST，max_retries=10；依赖与lazy／分页边界也已记录。**本轮未重新读wheel或核PR/MR专用create方法** [C1 SDK证据E15/E16](2026-11-11-issue-writeback.md)、[原SDK取舍](2026-11-11-project-trackers.md)|不因资源面扩大就自动安装两个SDK。后片若引入，必须在adapter后实际验证写重试关闭、redirect关闭、完整响应／限额、实际create参数与故障计数；SDK不能提供本地scope、actor核验、ref CAS或原attempt因果证明。当前证据只支持已有重试／依赖结论，不冒称PR/MR创建代码已读或已跑|

GitHub RESTcreate需要 pull requests(write)，仓库/ref读取另需metadata／contents(read)；Git refs创建文档列contents(write)，部分场景还列workflows(write)，不能将PR写权限当Gitpush权限。GitLablegacy API token写入需api，Git-over-HTTP 的 write_repository与API权限不同；还受真实project角色、源branch权限、保护规则和feature可见性控制。本轮没有取得GitLab创建MR最小角色矩阵的完整新证据，因此不把某个角色／scope组合作跨部署必然可写保证。能读 `/user`／repo或can_push=true都不代替发送时授权。[S3][S5][S8]、[已核GitLab token范围](2026-11-11-issue-label-writeback.md)

GraphQL endpoint沿已有第一方证据：GitHub.com为 `/graphql`，GHES常规REST `/api/v3`对应 `/api/graphql`；GitLab实例为 `/api/graphql`，不是 `/api/v4/graphql`。这是后片adapter的实际来源／认证合同，不授权按返回URL或跨origin发送凭据。[C2a接口研究](2026-11-11-issue-label-writeback.md)、[GitLab固定GraphQL研究](2026-11-11-gitlab-label-ids.md)

## C3a 的最小验收与后片必须保留的反例

以下均为待实现验收建议，本次未跑产品测试。只使用确定性localfixture；不要求真实账号、模型或远端写入来证明只读合同。

1. 原v7任务／creation／run／export→当前本地对象投影→CLI／HTTP的真实衔接。head与candidate、base与原base均匹配，以及base前进／head不同／本地ref漂移三个不同结论；原export历史收据仍可读，不自动改base或重跑六阶段。
2. 两provider各一条正常协议旅程，核GitHubrepositoryID／完整ref／object.type与GitLabnative projectID／编码branch／commit.id；用同前缀其他ref反例证明matching结果不能替代精确ref。换namespace后nativeID不符、转移／301、错误repo、符号／非commit返回、缺字段具体失败。
3. 在两次ref读取之间改变head/base，输出各自时间／摘要及实际差异；A→B→A反例明确只能看到两端当前相等。base SHA不能借GitLabmerge-base、GitHub测试merge SHA或短SHA替代。
4. 认证缺失、可见性404、redirect、超限、截断、坏JSON、timeout与限流均不变成“ref不存在／空列表／可发布”。不返回凭据／temp_clone_token或任意原始服务错误。默认请求预算可直接采用repo＋head＋base三次GET；如为绑定nativeID另需重读repo，显式计入且不得声称原子snapshot。
5. 进程、数据库、Git refs和现有intent／attempt／result前后保持；网络provider只收到GET，本地Git只执行上述只读命令，无Temporal start／signal／claim释放、fetch／push／新PR／MR。CLI／HTTP调用同一用例；相关binding修订变化不能默默重定向。

后片写入必须另验：attempt之后发送前退出、服务端完成后丢响应、部分201、错误actor／repo／head／base、并发两发送、原nativeID编辑／关闭／重开／删除、分页漂移、ref删除重建与ABA；均不能自动补建。原201、当前观察、操作者显式关联三种因果事实分别保存，不靠增加通用副作用框架或第二正式账本解决。[C1的原实现与边界](../../src/ergora/issue_writebacks.py)

## 新读取账本、未核范围

本轮12次GET在 **2026-11-11 12:39:20–12:41:36 UTC** 执行：11次完整200、1次301未跟随；没有自动redirect、重试或其他HTTP方法。每次socket timeout=15秒；普通文档／schema上限3,000,000B，固定GitLab完整参考单独上限4,000,000B。**socket timeout不是总墙钟deadline**：S10完整3.44MB读取耗45.92秒。所有body与manifest保存在本片持久忽略原件中；下表byte／SHA256均已从落盘原件重新核算。公开URL无凭据，时间均UTC。

|证据／完整URL|开始→结束|status／bytes／SHA256|实际可用范围|
|---|---|---|---|
|[S1]|12:39:20→12:39:21|200／42155；`eec4afd81387d735fae9525cf2ac78419ac28f64864780eb5a4106f66c76a5de`|ls-remote格式、symref、patterns、exit-code；未执行Git网络命令|
|[S2]|12:39:21→12:39:26|200／158724；`dc6dfcbc6fbd03004faf23f761241a4a90ee6cd43d31310234d0533845495db3`|普通push／lease空期望／atomic／porcelain／remote failure／URL重写与多pushurl|
|[S3]|12:39:26→12:39:28|200／892408；`55d8396db608b89f40a42de3164de83c076669eca9de79a30540f3db9dc4eb8d`|RESTpulls的create／get／list／update、字段／权限、相邻merge／update-branch区别|
|[S4]|12:39:28→12:39:38|200／724730；`d76abdc831450458ea16e5e8cf74c6ed690ff77a3011ccb8ae045b50875d7b18`|RESTMRcreate／get／list／update／delete、diff_refs语义、异步空字段／准备步骤|
|[S5]|12:39:51→12:39:52|200／1414655；`dda154373bc705b6b26f3120f2e477ce8a4ec24e6e4b74bde7f9410093c66d8b`|get-repo身份／权限／301／temp_clone_token及可见的merge设置；未读真实repo|
|[S6]|12:39:52→12:40:04|200／572057；`9c971cee3d026cd3aa46ce22727661dcc94b061b3127a718b23151912e032b05`|project按ID／路径GET、nativeID／namespace／cloneURL、权限影响字段与merge设置|
|[S7]|12:40:04→12:40:05|200／104794；`1e5920dfb5f3669086b8fdac43c44b05621da8fe12d07dfd03ae47c61a523010`|精确branch GET／commit.id及create／delete表；不是对象上传实验|
|[S8]|12:40:05→12:40:06|200／347595；`8bad8465449b941bb2f9905c6a065d466bf45e2e71039346c2e34e3099d9e556`|精确ref与matching-ref差别、create／update字段与权限|
|[S9]|12:40:44→12:40:46|200／1584905；`46f1d455d72ab784c6cb2b86e9b023df195dcfd2ed92099108b0faa5faa5d1fc`|完整FPTschema，定向读CreatePullRequestInput／Payload与相邻expectedHeadOid；未发GraphQL|
|[S10]|12:40:46→12:41:32|200／3440732；`6a8282e0f41a236c620f177cd2f5eedfd646eca2f21d43b4e76062c287b40056`|固定37cc4da…／18.5完整生成参考，定向读mergeRequestCreate全部input／payload；未运行该版本|
|[S11]|12:41:32→12:41:35|200／37898；`3d1fcd4c955794adbe92160df5be5d620acbfef53328b7089875b25bf3fa98ee`|GitLabdraft标题前缀、状态／人工变更与ready通知|
|[S12]|12:41:35→12:41:36|301／111；`6f4360dfdf3dd09a33ca772cf1523df1f00aa379370576ba5dd86c27fca276dc`|GitHub创建PR指南旧地址重定向，未跟随、未取得指南正文；相关事实只引S3／S9，不能称本页阅读成功|

本地曾有一次并行读取依赖尚未生成的文本文件而返回“文件不存在”，随后从同份已保存body顺序生成并定向读回；另有过宽的本地检索输出被工具截断，关键合同已按段重新读取。两者未增加GET，截断输出不作为完整输入证据。此前issue关系、分页、actor、token和SDK结论按原研究原范围引用，**本轮没有重新取这些页面／wheel**。

未核：真实GitHub／GitLab账号及权限、Git-over-HTTP／SSH认证与最终transport endpoint、provider软件版本／feature flags、真实新建draft的完整响应、GitLab异步diff时序、PR/MR专用SDK实现、服务器ref创建冲突的完整执行语义、真实hooks／CI／通知／LFS副作用、平台的历史event因果能力和任何跨API事务。也未证明一个全局SHA／同名ref的历史唯一性。本文只支持C3a最小计划与后片限制，不能据此关闭F7c、宣称exactly-once、执行瞬间SHA CAS、自动发布完成或业务工单完成。

[S1]: https://git-scm.com/docs/git-ls-remote
[S2]: https://git-scm.com/docs/git-push
[S3]: https://docs.github.com/en/rest/pulls/pulls?apiVersion=2026-03-10
[S4]: https://docs.gitlab.com/api/merge_requests/
[S5]: https://docs.github.com/en/rest/repos/repos?apiVersion=2026-03-10
[S6]: https://docs.gitlab.com/api/projects/
[S7]: https://docs.gitlab.com/api/branches/
[S8]: https://docs.github.com/en/rest/git/refs?apiVersion=2026-03-10
[S9]: https://docs.github.com/public/fpt/schema.docs.graphql
[S10]: https://gitlab.com/api/v4/projects/278964/repository/files/doc%2Fapi%2Fgraphql%2Freference%2F_index.md/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[S11]: https://docs.gitlab.com/user/project/merge_requests/drafts/
[S12]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request
[GH-LINK]: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue
[GL-MANAGE]: https://docs.gitlab.com/user/project/issues/managing_issues/
