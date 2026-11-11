# F7c-C2b：GitLab 标签 ID 的固定版本接口合同

日期：2026-11-11。仓库基线 `b5ee397e6571f95393b0f8d6e9ee7e6d947b0935`，分支 `refactor/architecture-foundations`。本文接续 [C2 计划](../plans/2026-11-11-issue-label-writeback.md)及[已有标签研究](2026-11-11-issue-label-writeback.md)的 G6，按 `research` 技能只新增本文；未修改产品、测试或计划，未安装 SDK、运行模型、读凭据、发送真实 GraphQL、提交或推送。并行工作树中的 GitHub C2a 实现不属于本研究范围。

所有本轮成功网络来源固定为 GitLab `v18.5.0-ee` 的完整提交 `37cc4da7158316bb9b204cef9b056f16fff1df32`。版本与 SHA 的关联复用原研究 E5，不重复解析 tag。以下为该点位的静态接口证据和实现建议；不是 GitLab.com、任意 Self-Managed／Dedicated 实例或本地夹具的写入验收。观察当前源码时，`GitLabBackend` 仍继承标签动作的 unsupported 方法；[原生命周期](../../src/ergora/issue_writebacks.py)及[backend](../../src/ergora/issue_backends.py)中的 C2a 代码不能证明 C2b 已实现。

## 能落地的范围与不能承诺的范围

该版确实注册 **`updateIssue(input: UpdateIssueInput!)`**，可只传 `projectPath`、`iid`、单项 `addLabelIds` 和 `clientMutationId`；返回可选择 `clientMutationId`、`errors`、`issue`。普通 Issue 的标签 membership 可以从原 mutation 的 `issue.labels` 有限页实读，不必猜 DSL。[R2]（行13502–13535）、[R4]（行93）、[R5]、[R7]

**可实现的有限合同：** 准备和发送前核原 REST native issue ID、实际返回的 GraphQL issue／project／label ID、精确标题及项目标签分类；冻结一个已存在、非 archived、标题不含 `::` 的项目标签 ID。只执行一次 ID 追加，严格匹配原完整 200 回执；未知状态只读观察。ID 路径避免按名称 find-or-create 和同名删除重建后的标签重定向。原研究 E14／E17 的 ID 分支和 G6 结论继续适用，本文没有重取那些服务代码。[R5]（行72–90）、[原 ID 路径证据](2026-11-11-issue-label-writeback.md#后补按-id-的-graphql-接口选择)

**不能保证：** `updateIssue` 的目标仍是可变 `projectPath`＋`iid`；完整 input 没有冻结原 issue ID、project ID、标签标题／版本或 expected membership 的条件。预检后改名为 scoped 的原 label ID 仍可能触发 EE 服务端互斥移除。若产品要求“任何竞态下绝不写另一原生 issue”或“绝不移除人工标签”，本接口不能凭本次证据满足，应继续显示该严格能力 unsupported。[R2]（完整 input）、[R5]（行40–55）、[R7]（行25–26）；[原 scoped callback 证据](2026-11-11-issue-label-writeback.md#后补按-id-的-graphql-接口选择)

## 注册、完整 input 与 payload

`GitlabSchema` 将 mutation 根设为 `Types::MutationType`；该类型 `mount_mutation Mutations::Issues::Update`。类的 `graphql_name` 为 `UpdateIssue`，生成参考明确记录公开字段 `Mutation.updateIssue` 及 input 类型 `UpdateIssueInput`，无需按 Ruby 常量猜 camelCase。[R11]（行27–28）、[R4]（行93）、[R5]（行5–6）、[R2]（行13502–13504）

下表为固定参考该 input 的**全部 18 个字段**，包括 EE／继承字段。除两项必填目标外，其余均 nullable；本动作仅发送表中标记的四项。未提供的其他字段应省略，不发送一组 `null`。[R2]（行13510–13527）

|字段|精确 GraphQL 类型|本动作|
|---|---|---|
|`projectPath`|`ID!`|发送冻结的项目完整路径；不是 project 全局 ID|
|`iid`|`String!`|发送冻结的项目内 iid 字符串|
|`addLabelIds`|`[ID!]`|发送一个实际读取、原样保存的 label GID|
|`clientMutationId`|`String`|发送本地固定动作摘要，仅核回显|
|`labelIds`|`[ID!]`|省略；文档明确为整套替换|
|`removeLabelIds`|`[ID!]`|省略|
|`confidential`|`Boolean`|省略|
|`description`|`String`|省略|
|`dueDate`|`ISO8601Date`|省略|
|`epicId`|`EpicID`|省略；17.5 deprecated|
|`healthStatus`|`HealthStatus`|省略|
|`locked`|`Boolean`|省略|
|`milestoneId`|`ID`|省略；显式 null 有移除语义|
|`stateEvent`|`IssueStateEvent`|省略|
|`timeEstimate`|`String`|省略；null／0 有移除语义|
|`title`|`String`|省略|
|`type`|`IssueType`|省略|
|`weight`|`Int`|省略|

`labelIds` 非空时与 `addLabelIds`／`removeLabelIds` 非空互斥；不以传空列表绕开替换语义。源码会把 label GID 经 `GitlabSchema.parse_gid(..., expected_type: Label).model_id` 转给服务，解析失败还有原值 fallback；建议只接受从受控读取得到的完整 GID，不采用裸整数字符串或自行合成 ID。[R5]（行59–63、72–90）

payload 的全部公开字段是 `clientMutationId: String`、`errors: [String!]!`、`issue: Issue`。因此必须同时核 top-level GraphQL errors 和 payload errors；`issue`／回显均可 null，空 `errors` 不证明标签实际加入。源码返回 `errors_on_object(issue)`，没有 assignment ID、追加次数或按 client key 查询结果的字段。[R2]（行13529–13535）、[R5]（行53–55）

## 可读取字段、目录分类与分页

|位置|已核真实 selection／参数|边界|
|---|---|---|
|`Query.project`|`project(fullPath: ID!): Project`|使用完整路径；可能返回 null [R2]（行1429–1439）|
|`Project`|`id: ID!`、`fullPath: ID!`、`issue(iid: String): Issue`|项目 iid 参数是字符串；本次只使用此定位参数 [R2]（行39241、39247、40292–40346）|
|`Issue`|`id: ID!`、`iid: String!`、`projectId: Int`、`type: IssueType`、`movedTo: Issue`、`labels: LabelConnection`|普通类型值为 `ISSUE`；没有 `project` 或 `repository` 字段 [R2]（行33912–33987、49429–49443）、[R8]|
|`Label`|`id: LabelID!`、`title: String!`、`archived: Boolean!`、`updatedAt: Time!`；另有颜色、描述等|没有 `name`、`project`、`group`、`isProjectLabel`、scope／owner 字段；不能复用 GitHub 的 label selection [R2]（行34338–34353）、[R9]|
|`Project.labels`|`title: String` 精确标题；`includeAncestorGroups: Boolean`；`archived: Boolean`；另有 `searchTerm`／`searchIn`|resolver 默认 `includeAncestorGroups=false`，不同于原研究中的 REST 默认；`archived=false`，`searchIn` 有默认值，不是必须显式传入的未知参数 [R2]（行40580–40598）、[R6]（行11–32）|
|`Issue.labels`|只有连接通用分页参数|完整参考没有 `ids`／`labelId`／`title` membership 过滤；不编造 `labels(ids: …)` [R2]（行33954、15169–15186）、[R8]（行46–49）|
|`LabelConnection`|`nodes: [Label]`、`edges: [LabelEdge]`、`pageInfo: PageInfo!`、`count: Int!`|不是 GitHub 的 `totalCount`；nodes 列表与其中元素可 null [R2]（行19342–19364）|
|分页|`first: Int`／`after: String`／`last: Int`／`before: String`；`hasNextPage: Boolean!`、`endCursor: String`|游标不透明；schema 默认页上限100，大多数连接适用，不能推断每个部署都恰好100 [R2]（行15175–15186、38310–38321）、[R11]（行31）、[R3]（行287–297）|

按名称准备时，可以用下方两条独立分页的目录 aliases 分类：`own` 仅项目，`available` 含祖先。推荐首片要求 `archived=false` 谓词下的完整精确标题结果为 `own={L}` 且 `available={L}`，每项返回标题逐字等于请求、未 archived，才选 L；这不证明不存在 archived 的同名项。`available` 有额外 ID 即可见祖先同名歧义；不能由某一页未见额外项证明唯一。`own` 的 ID 与容器 project ID 可记录项目归属；`available−own` 只说明祖先来源，不能猜具体 owner group。祖先支持若需要精确 group，须另补容器证据。原研究 E1／E2／E12 对项目／祖先同名与目录背景继续保留。[R6]（行24–27、40–71）；[原身份研究](2026-11-11-issue-label-writeback.md#标签身份名称不能代替-id-与所属命名空间)

两个 aliases 共用一次 HTTP，也不是数据库事务快照证明；分页期间、两条目录之间仍可变化。必须分别沿各自 `endCursor` 到 `hasNextPage=false`，重复游标、null 节点、权限部分结果、页／字节预算不足或 `own` 不再包含于 `available` 都拒绝准备。`count` 不能替代实际分页。按 ID 的写入已消除名称歧义，本段的同名拒绝是“名称作为准备入口、首片只选普通项目标签”的本地政策，不是 GraphQL 禁止对明确 group label ID 操作。[R2]、[R6]；分页并发结论是客户端推导，未做真实并发实验。

## 最小可执行 GraphQL 文本

以下文本的字段、类型和参数均来自上述固定参考，未向服务发送。示例每页20项以控制 query complexity；这是本地选择，不是 GitLab 上限。实际实例可能另有权限、schema、complexity或 feature flag 限制，读到不兼容即明确拒绝，不自动换接口。`$project`／`$iid` 来自原绑定／来源；初始游标为 null，后续只能只读分页。[R2]、[R3]（行287–313）

先核目标并读取当前 membership 一页；此文本也可供 observe 使用：

```graphql
query ErgoraGitLabLabelTarget($project: ID!, $iid: String!, $after: String) {
  project(fullPath: $project) {
    id
    fullPath
    issue(iid: $iid) {
      __typename
      id
      iid
      projectId
      type
      movedTo { id }
      labels(first: 20, after: $after) {
        nodes { id title archived updatedAt }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
```

目录使用真实 `title`，不使用单值 `Project.label(title:)` 来证明唯一性：

```graphql
query ErgoraGitLabLabelCatalog(
  $project: ID!, $title: String!, $ownAfter: String, $availableAfter: String
) {
  project(fullPath: $project) {
    id
    fullPath
    own: labels(
      title: $title, includeAncestorGroups: false, archived: false,
      first: 20, after: $ownAfter
    ) {
      nodes { id title archived updatedAt }
      pageInfo { hasNextPage endCursor }
    }
    available: labels(
      title: $title, includeAncestorGroups: true, archived: false,
      first: 20, after: $availableAfter
    ) {
      nodes { id title archived updatedAt }
      pageInfo { hasNextPage endCursor }
    }
  }
}
```

唯一 mutation 只带原冻结 input，不用 mutation 重读下一页：

```graphql
mutation ErgoraGitLabCandidateLabel($input: UpdateIssueInput!) {
  updateIssue(input: $input) {
    clientMutationId
    errors
    issue {
      __typename
      id
      iid
      projectId
      type
      movedTo { id }
      labels(first: 20) {
        nodes { id title archived updatedAt }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
```

variables 的构造是 `{"input":{"projectPath":原路径,"iid":原字符串,"addLabelIds":[实际返回的原label GID],"clientMutationId":原动作摘要}}`；此行是构造说明，中文占位不是可直接发送的 JSON。GraphQL 文本本身可与真实读取所得变量组成 POST JSON `{query, variables}`。不要用文档示例 `gid://gitlab/Label/1` 代替实际对象 ID。[R2]（行13510–13535、52629–52633）

## GID 与 REST native ID 的可验证关联

固定源码补足了“示例像数据库 ID”与“能核原对象”之间的证据：

- `Types::BaseObject#id` 调 `GitlabSchema.id_from_object(object)`，后者返回 `object.to_global_id`。`find_by_gid` 对 `ApplicationRecord` 直接用 `gid.model_class` 和 `gid.model_id` 加载记录。[R10]（行27–30）、[R11]（行57–66、88–109）
- `GlobalIDType` 明确说明 `gid://gitlab/User/1` 中模型是 ActiveRecord class，`1` 是数据库表的 record ID；typed scalar 还按 model class／祖先校验。`Label.id` 为 `GlobalIDType[Label]`，不是拿某个裸字符串后缀猜身份。[R12]（行6–16、80–100）、[R9]（行13–15）
- 固定参考分别示例 `gid://gitlab/Issue/1`、`gid://gitlab/Project/1`、`gid://gitlab/Label/1`；这些是格式示例，不证明穷尽 STI／兼容格式。[R2]（行52596–52600、52849–52853、52629–52633）

**实现建议：** 保留服务器实际返回的完整 GID，限定已核 schema 的返回容器／`__typename`、GitLab GID 应用及可解析结构，再将其中 model ID 与原 REST `id` 比较；issue 的 `iid` 另与原项目内 iid 比较，不能把 iid 当 native ID。`Issue.projectId` 的正整数应与已冻结 Project GID 的 model ID 互核。若另用 REST label／project 响应，其 native `id` 同样可与相应实际 GID 的 model ID 比较；REST 端字段合同沿原第一方研究，本轮没有重新抓 Projects API 文档。任何 ID 格式不认识或 native ID 不符都显式拒绝；不构造 GID、不静默换模型名／名称或用新对象替代原意图。[R2]、[R10]、[R11]、[R12]；[原 REST 身份证据](2026-11-11-issue-label-writeback.md#标签身份名称不能代替-id-与所属命名空间)

本轮未读取 `Gitlab::GlobalId.as_global_id` 或 Label 模型的重写，不能宣称 Label 的所有实际 GID 必定只用 `Label` 模型名，更不能用 `ProjectLabel`／`GroupLabel` 字样推断 owner。目录容器及实际 ID 是分类证据。官方还明确 GID 有 deprecation 周期；“实际服务器返回过”不等于跨版本永久有效。[R12]、[R3]（行183–192）

## 路由与定义竞态

|竞争|已核事实与可用处理|仍不能保证|
|---|---|---|
|project 路径 rename／transfer／删除后路径重用|input 只有 `projectPath`；基类 `find_object` 把 `parent_path`＋`iid` 传给 `resolve_issuable`。准备及发前比原 Issue／Project GID和完整路径，发现变化即拒绝 [R7]（行25–26）|没有 expected project／issue ID 条件；若服务端此时把路径＋iid 解析到另一有权限目标，原请求不能原子拒绝。旧路径是否跟 RedirectRoute，本轮未读内部 resolver，不作断言|
|issue move|可读取 `movedTo { id }`，源码从 `moved_to_id` 加载 Issue；发前发现非 null 可按首片政策拒绝 [R8]（行151–155、197–199）|没有“仍未移转”条件；不能保证读后移转时更新旧记录、拒绝、还是内部跟随。不能自动改用 movedTo 继续写|
|issue 删除／另对象占同路径＋iid|原 REST native ID 与 GID model ID 可在预检比对，原响应也须核相同 GID|普通 create 是否重用 iid、导入／恢复等何时允许复用，本轮未核；这里只给条件反例，不声称普通删除后一定复用。若路由确已指向另一 ID，原 input 没有它的前置条件|
|label 删除重建／失效|`addLabelIds` 绑定实际原对象 ID；原 ID 被删时不会因同名而改选新 ID，也不进入名称 create 路径；失效／不可用 ID 可被原服务过滤 [R5]；原 E14／E17|payload errors 为空仍可能没有 membership；必须读原返回页，不能根据 200 或同名新标签确认|
|原 label ID 在预检后被 rename 为 scoped|首片预检禁含 `::`，并核原 ID／精确 title／项目归属；原 EE callback 对执行时集合做 scope 互斥 [原研究 E19](2026-11-11-issue-label-writeback.md#标签身份名称不能代替-id-与所属命名空间)|完整 input 无 expected title／updatedAt、normal-only、保留同 scope 或 CAS 参数。未核到可用的原生条件；读前后 `updatedAt`、本地锁或 HTTP 头猜测均不能成为原子保护|

上述竞态结论区分了源码事实、客户端推导和未核行为。`movedTo` 是 nullable 且其目标受 `read_issue` 授权，返回 null 不能单独证明没有移转。[R8]（行13、154–155、197–199）即使原响应最终发现目标或标题不符，远端副作用也可能已发生；严格 receipt 能防止虚假确认，不能撤销错误目标更新或补回人的标签。禁止自动补偿、按新名称重选或重发。纯全局 issue ID 的 `workItemUpdate` 替代、服务端扩展／排他权限方案未在本轮核成可用合同；不能因为完整参考包含别的 mutation 就提前宣称它满足严格要求。

## 认证与严格原 200 确认建议

固定官方指南给实例 `/api/graphql`，使用 POST JSON 和 `Authorization: Bearer <token>`；列 OAuth、personal、project、group access token。部分 query 可匿名，mutation 总须认证；`read_api` 只足查询，mutation 需 `api`，同时仍受对象权限约束。[R3]（行31、53–91、114–121）、[R7]（行21）、[R6]（行7、43）

建议 GraphQL 从已接受的 REST `/api/v4` base 推导同实例 `/api/graphql`，不要拼成 `/api/v4/graphql`；这个推导是本地适配设计，目标路径由官方指南支持。保留已有 HTTPS／loopback 边界、外部 `token_env`、同一固定 token／actor 和有界传输；GraphQL 明确构造 Bearer，不把 REST 的 `PRIVATE-TOKEN` 直接当本轮已核 GraphQL header。凭据存在或 `/user` 成功不证明 label 写权限。未核到 fine-grained／job token 的此 mutation 合同，不自动宣称支持。[R3]；[原 backend](../../src/ergora/issue_backends.py)

推荐复用原 `issue_writebacks` 的唯一动作槽、显式确认、attempt-before-send、unknown 与独立 observation，不另建账本。一次原 mutation 的 receipt 至少满足：

1. 期望 HTTP **200**，完整响应在预算内，JSON 对象完整可解析；不跟 redirect／重试。保存原响应 digest。当前 backend 原有具体操作可声明预期状态，本段不是已经实现的 GitLab 适配。
2. top-level 无 GraphQL `errors`；建议沿现有 C2a 的保守门槛，出现该键即不确认。`data.updateIssue` 为非 null 对象，payload `errors` 必须是精确空数组，回显逐字等于冻结 `clientMutationId`。
3. `issue.__typename == "Issue"`、原完整 issue GID、字符串 iid、正整数 projectId 全相符，`type == ISSUE`；首片政策要求已选择的 `movedTo` 为 null。nullable、缺字段、错误类型或 data＋errors 均不形成 receipt。
4. `issue.labels` 非 null；所选有限页结构、每个选中的 node、`pageInfo` 都有效。原页中实际存在**原 label GID＋精确 title＋archived=false**，且游标与 `hasNextPage` 自洽。不因页中同名不同 ID 确认，不把 `count` 当 membership。
5. 原页正向命中即可形成本地接受的原返回 membership 证据，不要求翻完其他所有标签，也不证明本次首次添加。原页未命中、空页、null／部分结果或预算拒绝均保留 unknown；不能再次执行 mutation 翻页。后续 read query 只是当前事实，不补成丢失的原收据。
6. `clientMutationId` 只是回显，不是服务端去重／查询 attempt 的键。发送后崩溃、结果保存失败、丢响应、GraphQL／payload errors 都不允许清除 attempt 或推断“肯定未执行”。人工后来移除标签也不触发补发。

第2–4项是建议的客户端保守接受合同，强于仅看原服务 errors；第5–6项沿原 C1 因果合同。该 response selection 不带标签 owner 字段，因此 membership receipt 不能证明 label 分类／标题在整个远端执行区间内未变化；发前目录与原返回各自只是当时事实。未验证 REST `PRIVATE-TOKEN` 在 GraphQL 上的兼容性、真实 token／角色、通知／外部自动化、scope 竞争、真实 SaaS 或 Self-Managed 写入。

## 新读取账本及证据范围

本轮止于 **12 次无凭据 GET：11次200、1次404**，无自动重试／redirect、无 GraphQL请求。源码上限预设 **1,048,576B**；生成参考文档预设 **14,000,000B**，入门文档 **1,000,000B**。每次 `urllib` socket timeout 设15秒；它是单次 socket 操作超时，**不是总墙钟 deadline**。R2 连续读取完整3.44MB耗51.80秒，其余1.53–12.07秒；不能称全部请求15秒内结束。每个成功 body 的 declared length 均读尽，没有超限；原正文只保留在本轮进程内存，结束时释放，未新增源码／缓存文件。下表时间为 UTC 开始／结束，完整 URL 由每行引用给出。

|证据／固定 URL|开始→结束 UTC|状态／bytes／SHA256|实读证据范围|
|---|---|---|---|
|[R1]|12:13:32.486→12:13:34.082|404／32；`63f7f67ea6ef81dc7bf3bd7868cd068f6d025d70981a0f6685843007c3009a36`|旧 `reference/index.md` 路径失败；保留错误 body hash，不证明 schema 缺失|
|[R2]|12:13:53.486→12:14:45.289|200／3440732；`6a8282e0f41a236c620f177cd2f5eedfd646eca2f21d43b4e76062c287b40056`|完整生成参考下载；定向实读注册公开名／全部input与payload、Query.project、Project相关字段／issue／labels、完整Issue／Label字段表、连接／PageInfo、GID示例、IssueType；不是声称全文逐行审阅|
|[R3]|12:16:40.802→12:16:43.051|200／14839；`5db5334d83a95e690b53b50b2ecf1e5cd9d732bb241642e09637788667059226`|完整391行；endpoint、Bearer/token种类／scope、GID与版本变化、限制|
|[R4]|12:16:43.051→12:16:47.660|200／18880；`e8e34990f03156a43943d5bb49f533a07198e0421c3ea9b3780cb815871400f8`|完整下载，实读1–105行及update mount匹配；未借其他mount宣称别的mutation支持|
|[R5]|12:17:25.781→12:17:29.110|200／3021；`9c9cbc477232fc90a6e14db5087ae5c2b2a9e55a9b523e9a054377ce9914ac2f`|完整96行；这是G6同URL新一次GET，hash相同；为核基类／路由／parse细节而计入预算，不重复初查|
|[R6]|12:17:44.503→12:17:46.032|200／2286；`32e2ebabe4af3cda10027d51613fb99dc6e170b84569384461a470b8ccf5e4de`|完整74行；title与默认值／授权／Finder转交|
|[R7]|12:17:56.333→12:17:59.083|200／696；`db9ba15da18b55be6696dd7e8d6afd936ee6a1ffba6f89fb3cbd0de624551c60`|完整30行；两目标参数、nullable issue、授权与resolve_issuable调用；未读取其内部实现|
|[R8]|12:18:07.672→12:18:09.919|200／9436；`202cb291498730e7e36892827c354576fee398dc58c07bfd49975eff5cbd0c28`|实读1–100、140–219行及相关字段检索；Issue id／iid／labels／projectId／movedTo；未称已读取所有EE扩展|
|[R9]|12:18:09.919→12:18:21.994|200／666；`1a74c4c33315391919e240f90b5de273cb206a973d6bc8285119a50418453377`|完整25行；Label typed id／授权／连接；继承完整字段以R2为据|
|[R10]|12:18:50.951→12:18:53.050|200／1501；`3069f4768ff601523e009613edb4dfb029016d1847cb7c042e65d182aa8dca2e`|完整59行；BaseObject GID与scope|
|[R11]|12:19:39.701→12:19:41.401|200／6356；`9aac6c2aeb5fe816603a193e7f26c973f74068c2e7f1cd7fc28e5bf82ff8b5dc`|完整200行；mutation根、页上限、GID生成／解析／按model_id加载|
|[R12]|12:19:41.401→12:19:43.127|200／3467；`f2f79a38fd527b738e538fd60e2148ce8fb2c4f4298ee05020762ebb92488601`|完整109行；DB record id语义、typed GID类型校验及兼容边界|

R2 初次本地 heading 检索误用了不含反引号的字符串而无匹配，后定向读取成功；一次过宽的本地匹配输出被工具截断，所需字段随后按行重新读取。两者未增加 GET，截断输出不作为完整字段证据。原 E14／E17／E19、E5、REST权限／标签证据仅沿原研究引用，其原状态／时间／hash不计本轮成功或重新读取。

预算已用完。下一片仍需落实：真实目标版本的schema／权限读取与有界分页行为、GID非预期格式的明确拒绝、原返回严格映射、普通项目标签政策及剩余竞态的产品合同。`resolve_issuable` 内部路径重定向、issue iid复用／移转执行语义、GID模型重写、纯全局issue ID替代及任何服务端条件扩展未补取，不能靠未核字段消除这些缺口。本轮文档静态检查通过：12个来源定义、全部相对路径目标、三个GraphQL代码块围栏及尾空白；不把这些检查称作GraphQL运行验证，不运行产品／模型／真实账号验收。

## 第一方固定来源

[R1]: https://gitlab.com/api/v4/projects/278964/repository/files/doc%2Fapi%2Fgraphql%2Freference%2Findex.md/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R2]: https://gitlab.com/api/v4/projects/278964/repository/files/doc%2Fapi%2Fgraphql%2Freference%2F_index.md/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R3]: https://gitlab.com/api/v4/projects/278964/repository/files/doc%2Fapi%2Fgraphql%2F_index.md/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R4]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Ftypes%2Fmutation_type.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R5]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Fmutations%2Fissues%2Fupdate.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R6]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Fresolvers%2Flabels_resolver.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R7]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Fmutations%2Fissues%2Fbase.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R8]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Ftypes%2Fissue_type.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R9]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Ftypes%2Flabel_type.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R10]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Ftypes%2Fbase_object.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R11]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Fgitlab_schema.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[R12]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Ftypes%2Fglobal_id_type.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
