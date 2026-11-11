# 逐项目 GitHub/GitLab 工单接入：F7 准备调研

日期：2026-11-11。本文是官方文档、发行包源码和公开只读 API 的定向核查，尚未实现 F7。仓库源码基线为 c1f31fcfa38ac25085e287c507377be422786026；C6d 文档提交 0252dec5c41be1c1f6f533d86d8f32d30d178ce3 不改变本文所读源码。要求来自[总计划 F7](../plans/2026-11-01-all-in-one.md#8-p1低代码更多真实工具与演进闭环)、[DS4](../plans/2026-11-01-all-in-one.md#l1-deepseek-agent-管理工具调研用户追加)及[其研究来源](2026-11-02-deepseek-agents.md)。

## 建议决策

首片采用项目级、描述驱动的只读 Source：选择 GitHub/GitLab、API 地址、项目命名空间和凭据环境变量名；按明确工单号读取、展示并保存有来源的观察。观察结果明确为 context_only，不派工、不改标签、不发评论。这个入口应能服务普通控制面项目，不以发布 reference 注册、安装完整运行时或启动 A2A/Symphony 为前提。正式任务映射和外部写入另片交付，继续走现有任务与批准所有者。

对如此小的读取面，建议先保留 stdlib 的窄 HTTP 适配，不新增 PyGithub/python-gitlab 依赖。两库都能省去未来较广的资源、分页和错误处理工作，但均没有替服务端补上 issue 写入 CAS。本次核查不能支持“拿到 ETag 就能阻止并发写覆盖”的保证。[GitHub 条件请求][GH-BEST]、[GitLab issue 更新][GL-ISSUES]及下面的 SDK 源码是这一判断的依据。

## 当前代码可以复用什么

以下均为代码静态事实，不等于本轮已运行远端接入。

|现有所有者|真实能力|F7 的复用与边界|
|---|---|---|
|[projects.py](../../src/ergora/projects.py)|普通项目、绑定、expected_revision 检查；effective_configuration 返回来源和规范化摘要|Source 配置及其修订应沿用项目绑定入口。普通项目创建本身不要求 reference 注册。|
|[components.py](../../src/ergora/components.py)、[组件目录](../../src/ergora/data/components.json)、[bindings.py](../../src/ergora/bindings.py)|描述、配置 schema、默认值和绑定校验由同一目录消费|目前没有 tracker/Source 层，不能称现有页面已支持。新增受支持工具应进入这套描述与校验，不再建一份厂商表单。增加层时须处理旧项目缺字段，现有兼容默认表不会自动覆盖新层。|
|[registrations.py](../../src/ergora/registrations.py)、[注册 schema](../../src/ergora/data/schemas/project-registration-v1.json)、[reference.py](../../src/ergora/reference.py)|正式注册拥有 tracker.kind/project，发布时检查一个 tracker 不被另一 reference 项目占用；保存意图和单向投影|继续保留一个业务项目/工单命名空间的归属；新 Source 不能让同一已注册项目静默观察另一个 namespace。当前注册合同没有 api_url/token_env，也不含 host 身份。|
|[tasks.py](../../src/ergora/tasks.py)、[任务定义](../../src/ergora/data/schemas/task-definition-v1.json)|正式任务需 published 注册；输入已有 issue_id，preview/create 冻结项目修订、绑定和请求；启动有原意图及原 run 恢复|后续一张 issue 可对应多个明确 task/revision；不能将只读观察直接送入 start 或自动创建批准。现有 issue_id 这个名字并不表示两家 API 的全局 id。|
|[旧 tracker.py](../../src/ergora/data/reference/platform/upstream/symphony/tracker.py)|urllib、20 秒、1 MiB 响应限制、拒绝重定向；读取 state/labels，拒绝 GitHub PR；GitLab project 整段 quote；只迁移 workflow labels|可复用小传输边界的做法。它丢弃响应头、没有条件读取/分页/typed observation，且要求 token；不能直接当作完整 Source。GET 后写标签存在并发窗口。|
|[Symphony 本地入口](../../src/ergora/data/reference/platform/local/agent_platform/symphony.py)|配置真实 GitHub/GitLab、token_env、api_url、独立目录、原生 Symphony 与 bridge；enable 还要求凭据和执行边界可用|这是自动处理工单的可选运行入口，不应成为只读观察或本地任务的前置依赖。实际文件位于 reference/platform/local。|
|[bridge.py](../../src/ergora/data/reference/platform/upstream/symphony/bridge.py)、[共享 ingress](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/ingress.py)|bridge 已有不可变请求摘要、runs/issue_heads、提交前意图及恢复；共享 ingress 持久独占一张 issue，确认清理/REVIEW_READY 才释放|复用正式派工/恢复及跨入口归属。它们处理 request/task 身份，不是现成 webhook Trigger 去重。不要新增竞争调度器。当前 ingress key 仅 kind/project/issue_id，项目名保守 casefold，同名不同 host 会共用 claim；自托管多 host 接入必须版本化扩展身份，不能静默改旧 key。|
|[research.py](../../src/ergora/research.py)|已有受预算的 stdlib 资料读取、进程期限、URL 校验及项目观察记录|可借鉴预算和失败表达；其通用下载会逐跳验证并跟随重定向，且没有 tracker 认证/响应头合同，不宜原样套在带凭据请求上。|

## API 身份、读取和更新的真实语义

### 工单号与项目边界

|事项|GitHub REST|GitLab REST v4|
|---|---|---|
|按项目读一张工单|GET /repos/{owner}/{repo}/issues/{issue_number}；路径用 number，不用响应的 id。owner/repo 不区分大小写。[官方 endpoint][GH-ISSUES]|GET /projects/:id/issues/:issue_iid；:id 是项目全局 ID 或整个 URL 编码的 namespace/path，issue_iid 是项目内编号。issue.id 全局唯一，iid 只在项目内唯一。[官方 endpoint][GL-ISSUES]、[id vs iid][GL-REST]|
|嵌套项目|owner/repo 恰为两段；API 地址另外配置。|group/subgroup/repo 必须作为项目路径整体编码，例如 group%2Fsubgroup%2Frepo；错误编码或代理提前解码可能导致 404。[编码规则][GL-REST]|
|Issue 与 PR/其他工单类型|Issues API 同时可返回 PR；pull_request 字段是官方区分方式。返回的 id 仍是 issue id，不是 pull request id。[GH-ISSUES]|必须按声明支持的 issue 类型准入；当前 issues endpoint 还涉及 incident/test_case 等，不能仅因有 iid 就宣称通用 work item 全部兼容。[GL-ISSUES]|
|移动与缺失|转仓可返回 301；无读权限可能 404；可见但已删除可为 410。禁止把任意 404 解释成“确认不存在”，也不能自动跨 namespace 接受转移。[GH-ISSUES]、[GH-BEST]|项目改路径可产生 GET 重定向；旧路径的多数写方法会返回 405。先重新核对原项目身份；不能跟随 Location 将凭据交给未核对的来源。[GL-REST]|

建议 Source 观察至少保留：配置修订/摘要、provider、规范化 API base URL（含路径前缀）与 origin、项目 namespace、远端 project/repository 身份（若取得）、路由编号 number/iid、响应 id、实际对象类型、updated_at、观察时间、响应/规范化内容摘要及请求结果。路由编号、远端全局 ID、任务 ID、Git branch 和 run ID 应分别保存。文本和更新时间只提供上下文与变更线索，均不构成权限。

API 地址须独立于业务 Git remote，支持明确配置的私有 GitLab/GitHub 服务。当前只核对 github.com 和 gitlab.com；API v4 不表示已核对某个 GitLab Self-Managed 版本。命名空间、token_env、api_url 的变更必须进入新的项目配置修订；环境变量的值不能进入配置、观察快照或错误正文。这是 F7 建议的本地合同，尚未实现。

### 标签和冲突

|操作|官方语义与后果|
|---|---|
|GitHub issue PATCH / labels PUT|issue PATCH 的 labels 以及 PUT /issues/{number}/labels 都替换已有整套 labels，空数组清空。不得用本地旧快照整套覆盖来宣称保留人的修改。[GH-ISSUES]、[GH-LABELS]|
|GitHub labels POST / DELETE|POST 在现有集合上加标签；DELETE /labels/{name} 删除指定标签。删除不存在标签为 404。旧实现先加目标再删源，允许部分结果后重试，但两请求不是事务，也没有“仅当 source 仍在时才删”的服务端条件。[GH-LABELS]|
|GitLab issue PUT|支持 add_labels/remove_labels；labels 是完整标签赋值，空字符串清空；添加不存在名称还可能创建项目标签。state_event=close/reopen 可改关闭状态。若未来只授权 workflow 标签，就不应顺带发送 title、description、state_event 或完整 labels。[GL-ISSUES]|
|GitHub 写入条件|官方明确：“Conditional requests for unsafe methods, such as POST, PUT, PATCH, and DELETE are not supported unless otherwise noted in the documentation for a specific endpoint.” 本次 issue/labels 文档没有给出例外。故 If-Match/ETag 写入 CAS 不属于可保证能力。[GH-BEST]|
|GitLab 写入条件|issue PUT 参数没有 documented expected_version/If-Match/CAS；updated_at 是具管理员/项目 owner 权限者可以设置的时间字段，不是“仅当原时间相等”的前置条件。通用状态码表出现 409 或 412，不代表这个 issue PUT 支持 CAS；412 的示例是删除资源时的 If-Unmodified-Since。[GL-ISSUES]、[GL-ERRORS]|

后续受约束写入可以在保存意图后重新读取、只改明确拥有的标签、记录各子步骤并读回对账，发现人的变化或不确定请求结果时保持 conflict/unknown。**这些措施只能缩小和发现部分竞争窗口，不能保证对并发人工改动的原子比较交换。** 严格的冲突拒绝要求已验证的服务端条件支持，或需要另选能提供该语义的操作；本次没有此证据。无论 SDK 或直接 HTTP，都不能把“读取后比较再写”叫 CAS。

### 条件读取、分页和失败

GitHub 多数 endpoint 返回 ETag，许多返回 Last-Modified；If-None-Match/If-Modified-Since 可做条件 GET，未变为 304。官方 rate-limit 优惠限定为正确携带 Authorization 且返回 304 的请求，本次无凭据公开读取未验证此优惠。请求地址、表示、排序和分页参数必须稳定；缓存应按完整 API base URL/配置/资源/表示隔离，304 应复用自己已核对的原快照，不能当作空 issue。[GH-BEST]

本次 GitLab 公开单工单也实际返回 ETag 和条件 GET 304，见下方实测；这仅证明该次 gitlab.com 资源的读取行为，不构成所有自托管版本或全部 endpoint 的缓存保证。缺少 ETag 时仍可完整 GET 并比较内容摘要，不要求模拟写入版本锁。

单工单 GET 是一个对象，无须为了首片预先做全库扫描。若后续读取标签列表、评论、timeline、项目 issues 或关联 MR，必须显式有界分页：GitHub 标签列表默认 30、最多 100；跟随 Link 的 rel=next；GitLab offset 默认 20、最多 100，并提供 Link/x-next-page，GitLab.com 某些总量头可能缺失。GitLab keyset 只对特定资源/排序开放，不能默认所有 issue 列表支持。首片不需要用 SDK 的 get_all 或隐式迭代读取整库。[GH-LABELS]、[GH-PAGE]、[GL-REST]

updated_after/since 过滤和 updated_at 都不是事件 ID，也不是一次完整分页的稳定数据库快照；后续轮询要保留边界重叠、稳定身份去重和实际覆盖游标，不能仅保存“本页最大时间”就称没有遗漏。GitHub 官方亦说明按 updated 排序会使项目跨页移动。[GH-BEST]、[GL-ISSUES]

网络超时、认证/授权失败、404、限流、响应过大/截断、非 JSON、schema 不匹配、跨来源重定向要能区分于“已读到工单”。限流遵守 Retry-After 等返回头并有截止预算；GitHub 还给出剩余额度为零时等待 reset，以及其他 secondary limit 至少等待一分钟的规则。GitLab 的 429 同样须遵守 Retry-After，不能无限自动重试。[GH-BEST]、[GL-ERRORS]

## 事件、机器人与分支关联

### DS4：传输去重不替代授权

|平台|官方事实|设计含义|
|---|---|---|
|GitHub webhook|X-GitHub-Event 与 action 标记事件；X-GitHub-Delivery 标记一次事件，手工 redelivery 保持同值。[GH-HOOK-BEST]|未来 Trigger 可以按 Source 身份/API origin 加 delivery ID 去重；先保存收据，重复收取不重复产生执行意图。delivery 去重只覆盖该传输身份，不自动合并所有不同订阅的业务重复。|
|GitHub issue_comment / sender|issue_comment 同时包括 issue 和 PR 评论；sender 有时是 ghost 占位用户，不保证可识别真实行为人。[GH-HOOK-EVENTS]|先检查实际目标、事件/action、来源配置及主体；不能因看见 sender 或某段评论文字就扩大授权。|
|GitLab webhook|17.4 引入 Idempotency-Key；19.0 引入 webhook-id，当前文档优先用 webhook-id，二者相等且重试保持。X-Gitlab-Event-UUID 在递归 webhook 链中会相同；X-Gitlab-Webhook-UUID 仅被描述为每个 webhook 的唯一 ID。[GL-HOOK]|按实际服务器版本使用有证据的消息 ID，保存选用字段；不能把 Event-UUID 当普遍独立事件唯一键，文档没有为 Webhook-UUID 给出同一消息跨重试保持的保证，不能据此承诺重放去重。旧版本缺稳定消息 ID 时应显式降级/拒绝自动派工。|
|GitLab 重复与内容|同一项目同时配置 group/project webhook 可触发两次；超时也可能重复。Issue Hook 有 action 和 changes.previous/current；Note Hook 提供 noteable_type、note ID、author_id、system 等。[GL-HOOK]、[GL-HOOK-EVENTS]|传输去重之外还要有明确的项目/对象/修订归属；系统消息、自身写回及机器人消息不能因形成新 delivery 就重新接单。不要把没有变化的 update 当新授权。|

机器人过滤不能只凭显示名、用户名后缀或某个用户字段。GitLab 官方还区分内部 bot、project/group bot，过滤参数覆盖也不同。[GL-USERS] 未来应保存已核对的主体 ID、目标对象、来源修订，以及自身写回的关联收据；未知主体或自动消息至多补充上下文。完整正文、评论、链接、Git 分支名称均为外部输入，不可自动改变工具、路径、预算或审批权限。主动接单先 observe，之后显式接受的任务/授权修订才进入既有正式流程；这是 DS4 要求，非平台 webhook 自带保证。

本片不需要开放 webhook 监听。若后续开放，GitHub secret 校验和 GitLab 实际版本支持的签名/secret 校验也必须先完成；当前 GitLab 文档已区分 19.0/19.1 signing token 支持，不能拿最新文档能力覆盖旧服务器。[GH-HOOK-BEST]、[GL-HOOK]

### branch、PR/MR 是关联，不是工单空间

GitHub 支持一张 issue 关联多个 branch；由关联 branch 建 PR 后会显示 PR 关联。PR 描述的 closing keyword 只有目标为默认分支时才建立相应语义并在合并时关闭 issue；普通 cross-reference、linked branch 和可以自动关闭 issue 的 PR 不是同一事实。REST timeline 的 cross-referenced.source 可能是 issue 或 PR，必须检查 source.issue.pull_request，不能把任意引用当作已经交付。[GH-BRANCH]、[GH-LINK]、[GH-EVENT-TYPES]

GitLab 区分 related_merge_requests 与 closed_by 两个只读 endpoint；后者表示合并后将关闭 issue 的 MR，不表示 MR 已合并。由 issue 创建 branch/MR 及描述/commit 的 closing pattern 有原生规则；默认分支、项目配置和权限会影响自动关闭。无需关闭的关联也有 GraphQL/Work items widget 入口，本轮不因此扩大成新 GraphQL 集成。[GL-ISSUES]、[GL-CREATE-MR]、[GL-MANAGE]

Ergora 后续应分别保存 issue 身份、多 task/revision、准确候选 SHA、仓库/branch、PR/MR 原生 ID/编号/URL及读取到的关系类型。分支用于候选隔离，不能复制出新的 tracker namespace；“远端有关联/已关闭”也不能替代本地六阶段、可信证据和候选批准。首片只显示有来源的观察，不创建 branch/PR/MR，不根据标题或正文猜测关联。

## SDK 与窄 HTTP 的成本

以下版本于 2026-11-11 从 PyPI 官方发行元数据取得，未安装。包自身均提供 py3-none-any wheel；这不等于已验证传递依赖在全部平台可安装。

|方案|已核版本与入口|依赖和维护判断|
|---|---|---|
|PyGithub|2.10.0；Python >=3.10；Issue.edit/add_to_labels/remove_from_labels/set_labels；GithubObject.update 实际发条件 GET；PaginatedList；Github(api_version=...) 可固定 REST 日期版本。[PYGH]、[PYGH-ISSUE-SRC]、[PYGH-OBJ-SRC]、[PYGH-CLIENT-SRC]、[PYGH-PAGE-SRC]|直接依赖 pynacl、requests、pyjwt[crypto]、typing-extensions、urllib3；签名/加密依赖扩大基础安装与平台依赖矩阵。issue 写方法没有自动附带资源写入版本保护；update 这个名字在此是刷新对象，不是 CAS 写。只有广泛使用仓库/PR/App 等对象时，这些能力才更可能抵偿依赖成本。|
|python-gitlab|8.6.0；Python >=3.10.0；project.issues.get(iid)，ProjectIssue._id_attr=iid；SaveMixin.save 将待更新属性交给 manager；原生 related_merge_requests/closed_by，分页 iterator。[PYGL]、[PYGL-ISSUES-DOC]、[PYGL-ISSUE-SRC]、[PYGL-SAVE-SRC]、[PYGL-CLIENT-SRC]|基础直接依赖 requests、requests-toolbelt；可选 GraphQL/CLI 补全/YAML 无须一起加入。通用 HTTP 可传 extra_headers、timeout/重试选项，但 Issue.save 不会自动获得远端 CAS；读取后修改 labels 再 save 仍可能发送旧的整套列表。自托管版本差异、领域授权和 Trigger 去重仍归 Ergora。|
|stdlib narrow HTTP|当前 Ergora Python >=3.11；已有 urllib、json、quote、拒绝重定向及大小限制用法|首片只有两种按编号 GET，免去两套 SDK、认证抽象和隐式对象加载。须显式负责超时/字节预算、凭据引用、URL/来源、状态头、JSON 校验和标准化观察；不扩写通用 Git 平台客户端。以后资源面实测扩大再评估可选 SDK，并保持在单一 adapter 后面。|

PyGithub 标签 v2.10.0 由 GitHub commit API 解析为 5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41；python-gitlab v8.6.0 为 51eb17e6e67a25157e04b0abc649221bd8ecc7fe。[标签解析一][PYGH-COMMIT]、[标签解析二][PYGL-COMMIT] 七次 raw.githubusercontent.com 源码读取超时，保留失败；随后直接下载官方 PyPI wheel，逐包校验元数据公布的 SHA256，并静态读取其 Issue、HTTP、对象/保存及分页实现。源码链接提供固定提交复核位置；本次成功取得的源码字节来自发行 wheel，不冒称 raw 请求成功。

- PyGithub wheel SHA256：192ada2a76e4afc7d6b37e500c9bfeba1731e6506697445a5ba1c4af8bf0b924。
- python-gitlab wheel SHA256：34fee7e5576cf01982c4bfa98f94d50e24733edb66beba3cb8ef286287723019。

## 首片建议验收与本轮证据范围

首片可以很小，但合同需可反证：

1. 普通本地项目无 reference 安装也可配置受支持 Source；local 模式无网络；未知 provider/字段、命名空间或凭据配置明确拒绝。已有注册项目的 tracker 归属仍唯一、改配置须核修订。
2. 固定 fixture 覆盖 GitHub id/number、GitLab id/iid/嵌套 namespace、GitHub PR 拒绝、请求边界和状态/响应摘要；一张明确编号读取不隐式扫描整库。
3. 明确拒绝重定向或核对后的显式重新配置；缺凭据、401/403/404/410、429、5xx、超时、超大/截断 JSON 和不兼容 payload 有独立失败。没有远端响应时不伪造空内容或成功。
4. 若实现条件读取，覆盖“有原快照时 304 复用”和“缺原快照时不能成功”；缓存身份绑定 origin、namespace、资源、表示及配置；更新时间/ETag/摘要均不变成权限或写锁。
5. 观察输入始终 context_only；正文、机器人消息、重放或更新不能触发任务、扩大授权或改变正式批准。后续业务去重及多任务映射保留原 request/task/run 身份，复用现有 ingress/Temporal。
6. 默认验收使用本地 fixture 服务，不向真实账号发送 issue/comment/label；公开只读实测另记准确覆盖，不替代未来有授权项目的写入/冲突验收。

本轮共执行 43 次无凭据 GET：33 次 HTTP 200、2 次 304、1 次 404、7 次网络超时；全部原始响应体、响应头、时间、请求 URL 和 SHA256 存在私有检查记录。读取时间为 2026-11-11 05:54–06:00 UTC。官方文档为读取时的滚动版本；GitHub REST 固定 2026-03-10，官方仍列 2022-11-28 至 2028-03-10 的支持窗口。[GH-VERSION]

公开 API 实测：

|实际 URL|结果与边界|
|---|---|
|https://api.github.com/repos/octocat/Hello-World/issues/1|200；响应 id=872858、number=1，含 pull_request，属于 PR；请求明确 X-GitHub-Api-Version: 2026-03-10，响应 selected 同值。后续 If-None-Match 返回 304。只证明原始 API 行为，未运行 Ergora adapter。|
|https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab/issues/1|200；project_id=278964、id=382515、iid=1；后续 If-None-Match 返回 304。未查询部署软件版本，不能推断自托管兼容。|

误用的 GitLab /api/rest/response_codes/ 文档地址返回 404，随后从官方 REST 页实际链接取得 /api/rest/troubleshooting/ 的状态码说明；不把 404 记作接口不可用。Read the Docs 的 latest/stable 文档只能作滚动说明，准确 SDK 结论以校验后的发行包为准。

未安装、导入或运行 SDK；未使用真实凭据；未发送任何写请求；未配置 webhook、启动 Agent、创建任务或实际制造并发人工修改。写入权限、服务端 CAS、自托管版本兼容、重启后业务去重和完整 F7 旅程均未实测。本文建议的是下一片边界，不能据此关闭 F7/DS4。

## 官方来源

正文各结论均有官方链接。下表说明取得方式，固定源码链接与成功读取的发行源码字节分开登记。

|来源组|实际访问及版本|
|---|---|
|GitHub 官方 REST、webhook、issue/branch 指南|正文链接页面均 HTTP 200；REST 按 2026-03-10 阅读；[API 版本表][GH-VERSION]说明默认版本与支持窗口。|
|GitLab 官方 issues、REST、webhook、用户及 MR 指南|正文链接页面均 HTTP 200；为读取当日滚动文档，包含 19.x 的版本历史，不能代替目标部署版本探测。错误的 response_codes 地址单独保持 404。|
|PyPI 官方元数据和发行 wheel|[PyGithub][PYGH] 2.10.0、[python-gitlab][PYGL] 8.6.0；元数据和 wheel 均 HTTP 200，wheel 哈希已核；没有安装。|
|SDK 固定提交和源码|两标签 commit API 均 HTTP 200；七份 raw 请求超时，静态实现结论来自上面校验后的 wheel，固定 blob 链接供另机复核。|
|SDK 维护者文档|[PyGithub Issue 文档][PYGH-DOC]、[python-gitlab issues][PYGL-ISSUES-DOC]及[分页/使用说明][PYGL-USAGE]均 HTTP 200；latest/stable 不等于固定发行版本。|
|公开单工单 API|上表两 URL 各 HTTP 200 后 304；无凭据，无写入；不是 Ergora 接入验收。|

[GH-ISSUES]: https://docs.github.com/en/rest/issues/issues?apiVersion=2026-03-10
[GH-LABELS]: https://docs.github.com/en/rest/issues/labels?apiVersion=2026-03-10
[GH-BEST]: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
[GH-PAGE]: https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api
[GH-VERSION]: https://docs.github.com/en/rest/about-the-rest-api/api-versions
[GH-HOOK-BEST]: https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks
[GH-HOOK-EVENTS]: https://docs.github.com/en/webhooks/webhook-events-and-payloads
[GH-LINK]: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue
[GH-BRANCH]: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-a-branch-for-an-issue
[GH-EVENT-TYPES]: https://docs.github.com/en/rest/using-the-rest-api/issue-event-types?apiVersion=2026-03-10
[GL-ISSUES]: https://docs.gitlab.com/api/issues/
[GL-REST]: https://docs.gitlab.com/api/rest/
[GL-ERRORS]: https://docs.gitlab.com/api/rest/troubleshooting/
[GL-HOOK]: https://docs.gitlab.com/user/project/integrations/webhooks/
[GL-HOOK-EVENTS]: https://docs.gitlab.com/user/project/integrations/webhook_events/
[GL-USERS]: https://docs.gitlab.com/api/users/
[GL-MANAGE]: https://docs.gitlab.com/user/project/issues/managing_issues/
[GL-CREATE-MR]: https://docs.gitlab.com/user/project/merge_requests/creating_merge_requests/
[PYGH]: https://pypi.org/pypi/PyGithub/json
[PYGL]: https://pypi.org/pypi/python-gitlab/json
[PYGH-COMMIT]: https://api.github.com/repos/PyGithub/PyGithub/commits/v2.10.0
[PYGL-COMMIT]: https://api.github.com/repos/python-gitlab/python-gitlab/commits/v8.6.0
[PYGH-ISSUE-SRC]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/Issue.py
[PYGH-OBJ-SRC]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/GithubObject.py
[PYGL-ISSUES-DOC]: https://python-gitlab.readthedocs.io/en/stable/gl_objects/issues.html
[PYGL-ISSUE-SRC]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/v4/objects/issues.py
[PYGL-SAVE-SRC]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/mixins.py
[PYGH-CLIENT-SRC]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/MainClass.py
[PYGH-PAGE-SRC]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/PaginatedList.py
[PYGL-CLIENT-SRC]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/client.py
[PYGH-DOC]: https://pygithub.readthedocs.io/en/latest/github_objects/Issue.html
[PYGL-USAGE]: https://python-gitlab.readthedocs.io/en/stable/api-usage.html
