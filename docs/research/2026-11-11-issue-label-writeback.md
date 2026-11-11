# F7c-C2：既有状态标签的显式追加与人工冲突边界

日期：2026-11-11。本次研究的仓库 HEAD 为 `472ff60a6d27c91ef5d5285f959e61d3b935341d`，分支 `refactor/architecture-foundations`；C1 评论回写仍在同一工作树内实现／验收。本文接续 [F7 计划](../plans/2026-11-11-project-trackers.md)、[准备研究](2026-11-11-project-trackers.md)和 [C1 研究](2026-11-11-issue-writeback.md)，只研究下一片 C2，不是当前 C1 提交／审查范围，也不表示产品已支持标签回写。本次只新增本文，没有修改产品／计划／测试、安装 SDK、执行模型、真实账号写入、读取凭据、提交或推送。

**后补接口选择：** 下文原建议及“GraphQL 未核”描述保留首轮 REST 研究范围。[按 ID 后补核查](#后补按-id-的-graphql-接口选择)已改变实现优先项：GitHub 应优先评估 `addLabelsToLabelable` 的原生 ID 输入；GitLab 已核 `updateIssue.addLabelIds` 可避免按名称新建／同名选择，但目标仍为 projectPath＋iid，且 scoped rename 竞态仍在。后补没有实现 C2，也未扩大当前 C1 候选。

## 结论与推荐范围

**GitHub `POST .../issues/{number}/labels` 和 GitLab `PUT .../issues/{iid}` 的单独 `add_labels`，都能避免客户端把旧的整套标签读回再覆盖；不能据此承诺无条件保留所有并发人工意图。** GitHub 文档把 POST 定义为向现有标签追加，PUT 是整套替换。GitLab 的普通标签追加以原集合与新增 ID 求并集，但有两个必须写入支持合同的例外：缺失名称可以新建项目标签；启用 scoped labels 时，追加同 scope 的不同值会移除原值。[GH-LABELS]（K1）、[GL-ISSUES]（K3）、[GL-CALLBACK]（E14）、[GL-SCOPED-CODE]（E19）、[GL-LABELS-USER]（E2）

**推荐最小可用动作：只为原 v7 来源、原 creation／run／已导出精确 candidate，显式追加一个已预检存在的普通标签。** 操作者审查并确认精确意图；GitHub 请求只含非空单项 `labels`，GitLab 只含非空单项 `add_labels`；不发送完整 `labels`、`remove_labels`、title／description、state／state_event 或订阅参数。GitLab 首片拒绝任何含 `::` 的名称，包括 nested scope；拒绝以一次追加实现工作流状态替换。既有“已导出”标签可以表达候选事实，不表示批准、合并或工单已处理完。[GH-LABELS]、[GL-ISSUES]、[GL-LABELS-USER]；候选约束沿 [C1 计划](../plans/2026-11-11-issue-writeback.md)与 [原 export](../../src/ergora/reference_task_export.py)

**必须区分两种承诺。** “准备和发送前都看见该原生标签，并只请求追加这个名称”可形成实用但有限的支持合同；“服务端执行时绝不创建标签、绝不命中删除重建后的同名标签、只要任何人改过就原子拒绝”不受这两个名称接口及本次证据支持。尤其 GitLab 在发前 GET 后删除标签，随后的 `add_labels` 仍可能创建新 ID 的同名项目标签。若业务强制要求绝不创建，当前 GitLab 操作应显示 unsupported，不能把概率较小当成保证；若强制要求精确原 label ID 的原子绑定，两家本次操作都不能宣称满足。另核按 ID 的其他原生操作属于后片，本文没有验证 GraphQL 替代方案。[GL-ISSUES]、[GL-AVAILABLE]（E17）、[GL-FIND-CREATE]（E18）、[GH-LABELS]、[GH-BEST]（K2）

这里的“可用”也不承诺通知静默。原生标签事件、通知、订阅参与和平台自动化的可见影响要在确认意图中说明；不为两家首个追加消费者引入通用副作用框架、后台重试队列或补偿删除。[GH-WEBHOOK]（K7）、[GL-LABELS-USER]、[GL-UPDATE]（E11）、[GL-ISSUES-BASE]（E15）

## 原生操作、权限与明确不发送的字段

|事项|GitHub REST|GitLab REST v4|
|---|---|---|
|窄写操作|`POST /repos/{owner}/{repo}/issues/{issue_number}/labels`；请求示例为 `{"labels":["bug"]}`，追加现有集合；成功 `200`，返回标签数组 [GH-LABELS]|`PUT /projects/:id/issues/:issue_iid`，只发 `{"add_labels":"bug"}`；名称是逗号分隔字符串，成功更新返回 issue 表示 [GL-ISSUES]、[GL-ERRORS]（K5）|
|与替换区别|`PUT .../labels` 明确移除旧标签并设置新集合；空数组会移除全部。不能把 set／issue edit 当 add [GH-LABELS]|`labels` 是整套赋值，空字符串清空；`add_labels`／`remove_labels` 才是局部意图。不得为满足通用 update 包装器而附带旧 `labels` [GL-ISSUES]|
|原权限|页面列 GitHub App user／installation token、fine-grained PAT；Issues(write) **或** Pull requests(write)。UI 指南另说明 triage 可应用／移除既有标签，write 可创建／编辑／删除标签；这两种权限描述不能相互替代，也不表示公开匿名可写 [GH-LABELS]、[GH-MANAGE]（E4）|现有 issue 的标签属于 metadata。当前矩阵列 Planner、Reporter、Security Manager、Developer、Maintainer、Owner 可编辑 metadata；Guest 只能在创建 issue 时设置 metadata，不能因本人可评论／编辑正文就推断可改既有标签 [GL-PERMISSIONS]（E6／E21）。固定源码同时检查 `update_issue` 和 `set_issue_metadata` [GL-API]（E9）、[GL-CALLBACK]|
|token 与 actor|受支持 token 的权限和资源范围仍由平台判断；`/user` 可核主体，不验证目标写权限。C2 应继续固定同次认证上下文并核原 actor [GH-LABELS]、[C1 研究](2026-11-11-issue-writeback.md)|已核 legacy personal／group／project token 的 `api` 为其资源范围内 API 读写，`read_api` 只有读；`write_repository` 是仓库 Git 权限，不能当作 issue 写权限。新 fine-grained token 的逐 endpoint 权限未核，不自动宣称兼容 [GL-TOKEN-SCOPES]（E20）。token scope 不取代项目角色和对象可见性|
|缺失名称|本次已核 POST 文档只写追加，另有独立 create-label endpoint；没有取得“缺失名称一定以某状态失败且绝不创建”的专属合同，不应编造 422 原因或绝不创建保证。推荐发前必须查到原 ID，缺失即不发送 [GH-LABELS]、[GH-MANAGE]|明确写明不存在就创建项目标签并赋予 issue。固定源码仅在有 `admin_label` 能力时创建；无能力可返回 nil 并被 compact，不能把 HTTP 200 等同于标签确已追加 [GL-ISSUES]、[GL-FIND-CREATE]、[GL-AVAILABLE]|
|成功不等于新增一次|返回集合没有 attempt ID／添加次数；原本已存在也不能据成功响应声称由本次首次加入 [GH-LABELS]|普通集合求并集；响应标签名没有每次操作 ID。目标已存在可以是无变化成功 [GL-CALLBACK]、[GL-ISSUES]|

**文档与固定源码的具体差异：** 滚动 GitLab issues 页“至少一个参数”摘要未列 `add_labels`／`remove_labels`，但同页属性表列出二者。固定 `v18.5.0-ee` 的 `IssuesHelpers.update_params_at_least_one_of` 明确包含二者，故该源码支持只发 `add_labels`；不能为了弥补摘要遗漏而附带全量标签或另一个有副作用参数。本文未运行该发行版，也没有据此确认所有 Self-Managed 版本。[GL-ISSUES]、[GL-API-HELPERS]（E13，行23–39）、[GL-API]（行323–354）

上述接口没有提供本次可用的只读“证明会写成功”操作。准备 GET、凭据存在、角色名称或 `/user` 成功都不是写权限验收；真实拒绝须记录原状态及未确认结果，不在错误正文保存 token。[GH-LABELS]、[GL-API]；[现有诊断与认证](../../src/ergora/issue_backends.py)

## 标签身份：名称不能代替 ID 与所属命名空间

|问题|核到的事实|C2 推荐合同|
|---|---|---|
|GitHub 标签所属|标签属于创建它的 repository，只能在该 repo 使用；读取／更新／删除标签均按名称路由，响应有唯一 `id`、`node_id`、`name`、资源 URL；标签可改名、删除，删除会移除 issue／PR 上的引用 [GH-LABELS]、[GH-MANAGE]|意图冻结 provider、完整 API base／版本、原 repo namespace、原 issue number＋native ID，以及标签 native ID＋精确返回名称。名称做完整 URL 编码；不要把 label ID 当 issue ID，也不要把可变名称当独立全局身份|
|GitLab project／group|project 标签只用于该项目；group 标签可用于该 group／子 group 的项目。project labels API 默认 `include_ancestor_groups=true`，单条按 ID **或** title 读取；返回 `is_project_label`。指南允许父／子 group 暂时存在同名标签 [GL-LABELS-API]（E1）、[GL-LABELS-USER]|首片可只支持明确 project label；即使如此也须检查当前可用祖先标签中的同名歧义。保存 ID、name、project／group 分类及能核实的所属容器，不能用一个裸名称或 `is_project_label=false` 猜出具体 group|
|同名解析|固定代码把所有可用 project／祖先 group 标签按 `title` 做 `index_by`，然后按名称取值；同名不同 ID 会被折叠。没有把“操作者选中的 label ID”传给公开 issue PUT 的办法 [GL-AVAILABLE]（行12–30）、[GL-FINDER]（E12）、[GL-API]|不能假定 project 总优先或同色就是同一标签；有两个精确同名候选就拒绝。只查 `include_ancestor_groups=false` 不能证明写时没有同名 group 标签。检索／分页预算不完整也不能据此认定唯一|
|promotion 与身份漂移|GitLab project label promote 后可能合并同 title 的其他标签；文档说新 group label 仍可保留旧 project label ID，相关引用与订阅被迁移 [GL-LABELS-USER]|仅比较 native ID 还不够，分类／所属 namespace 也须重核。promotion、rename、删除重建需要新准备；不能自动按新名称追踪旧意图|
|删除重建／改名窗口|两家都提供标签 rename／delete；这些写入没有与本次 add 原子绑定的 expected label ID 条件。GitLab 名称缺失还能创建新对象 [GH-LABELS]、[GL-LABELS-API]、[GL-FIND-CREATE]|准备与发前 lookup 对不上 ID／name／容器就不发送；读后再变仍可能命中另一对象或失败。响应／后续 GET 发现异样只记录 unknown／drift，不补偿删除一个可能属于人的标签|
|名称与编码|GitLab 公开参数是逗号分隔名称，固定实现还会 split／strip；scope 使用 `::`，nested scope 取最后一个 `::` 之前的全部内容 [GL-ISSUES]、[GL-AVAILABLE]、[GL-LABELS-USER]|单标签动作拒绝空名、逗号、控制字符、前后空白，以及 GitLab 的任何 `::`。用查回的精确名称，不自行 lower／casefold／Unicode 归一化来合并标签；本次没核到跨平台 label 名大小写等价合同|

**scoped 不是前端显示差别。** GitLab Premium／Ultimate 文档明确：一个 issue 不能同时拥有相同 key 的两个 `key::value`；赋予新值会替换旧值。`workflow::backend::review` 与 `workflow::backend::development` 同 scope，和 `workflow::frontend::review` 则不同。固定 EE callback 对并集再次做互斥过滤，这发生在服务端原操作中，不需要客户端发送 `remove_labels`。所以“只发送 add_labels 就不会删人的标签”是错误保证；首片拒绝 scoped 可避免主动请求这类替换，但不提供远端 rename 竞态的原子防护。[GL-LABELS-USER]、[GL-SCOPED-CODE]

现有 [issue 观察与 v7 snapshot](../../src/ergora/issue_sources.py)只保存标签名称，GitHub 也把 label 对象投影成名称；它们没有 label ID／所属容器。C2 所需身份应在新意图中由 backend 提供窄 lookup／有界 catalog 事实，不改旧 snapshot 的历史字节，不声称原 v7 已冻结标签 ID。[issue_backends.py](../../src/ergora/issue_backends.py)、[issue_sources.py](../../src/ergora/issue_sources.py)

## 原生及部署副作用如何进入支持合同

|事项|事实与证据|支持边界|
|---|---|---|
|新建标签|GitLab add 缺名可创建；GitHub 缺名的绝不创建保证本次未取得 [GL-ISSUES]、[GL-FIND-CREATE]、[GH-LABELS]|预检存在是前置事实，不冒称服务器“existing-only”开关。GitLab 若必须绝不新建，拒绝该操作；不自动 create、rename、promote 或 delete 标签定义|
|互斥标签移除|GitLab scoped label 加入可移除同 scope 标签 [GL-LABELS-USER]、[GL-SCOPED-CODE]|首片不支持 scoped；不能称“只会增加标签数量”|
|通知／事件|GitHub 有 issue `labeled`／`unlabeled` 事件，webhook 文档明确这些 action 对应 issue 标签增删；GitLab label 订阅者会在标签被赋予时收到通知，固定 update service 调用 relabeled 通知与 issue hooks／integrations [GH-EVENTS]（K6）、[GH-WEBHOOK]、[GL-LABELS-USER]、[GL-UPDATE]、[GL-ISSUES-BASE]|操作者确认中明确会产生原生活动及可能通知／自动化；不承诺投递次数、送达或静默。200 不代表后台通知／webhook 已完整执行，也不重试以追求这些后续效果|
|actor 的订阅／参与|GitHub 默认订阅指南列评论、开 issue、被分配、被 mention、改变线程状态等；没有把 label add 列为专属保证。GitLab 指南说 comment／edit 会成为 participant；固定代码里的显式 subscribe／unsubscribe 由 `subscription_event` 分支控制，labels API 的订阅又有独立 endpoint [GH-NOTIFICATIONS]（E23）、[GL-NOTIFICATIONS]（E3）、[GL-ISSUABLE]（E10，行483–488）、[GL-LABELS-API]|不调用订阅／取消订阅，不从例子 `subscribed:true` 推断本次自动订阅；也不承诺所有部署完全不改变 actor 参与状态／未来通知。需要精确“无订阅变化”的业务约束时，另核目标版本和账号政策|
|更新时间、system note、To-Do|固定 GitLab 源码更新 timestamp／updated_by、生成 system notes；标签实际变化进入 `has_changes?`，update service 会 resolve 当前用户针对该 target 的 To-Do，再处理新增标签通知 [GL-ISSUABLE]（行298–350、572–585）、[GL-UPDATE]（行43–68）|不能把局部参数宣传成只改一列。文档应说明平台原生记账与 To-Do 影响可能存在；这不是 Ergora 新增待办管理能力，首片不另做补偿|
|工单关闭|GitHub add-label endpoint 没有 state 参数；GitLab issue PUT 的 close／reopen 是 `state_event`，固定状态分支按它执行。标签本身未提供本文可引用的“标签名等于关闭指令”合同 [GH-LABELS]、[GL-ISSUES]、[GL-ISSUABLE]（行460–480）|只请求加标签，不发送 state_event／正文／quick actions／closing relation。原生事件可触发部署自定义机器人／自动化，故不能承诺整个账号永不关单。要求全局不关单须核具体部署，不能用“没调用 close endpoint”替代该核查|

这里不扩展通用副作用登记或自动化扫描器。上表是这一个实际操作的已知原生行为与明确限制；通知设置、订阅管理、标签生命周期、To-Do 管理、任意 webhook 后果和关闭自动化都是独立需求，不成为 C2 的额外写权限。[F7 计划](../plans/2026-11-11-project-trackers.md)、[C1 边界](../plans/2026-11-11-issue-writeback.md)

## 完整 200、幂等与 unknown 恢复

**两家本次 add 接口均没有查到 documented 客户端幂等 key、预先指定的唯一 operation ID 或标签写 CAS。** GitHub 官方还明确 unsafe methods 的条件请求不受支持，除非 endpoint 另说；本次 labels 页没有例外。GitLab issue PUT 参数没有 expected_version／If-Match；固定 service 内部虽有 `lock_version`，公开 API 只传 declared params，未把它声明为该 issue 更新参数。内部乐观锁和通用 409／412 状态码不能变成外部受支持 CAS。[GH-BEST]、[GH-LABELS]、[GL-ISSUES]、[GL-API]、[GL-ISSUABLE]（行303–306）、[GL-ERRORS]

**推荐把 acknowledged 定义为“本地原 attempt 的完整原生成功响应已核且保存”，不定义为“本次首次加上标签”。** 严格响应合同由实际消费者声明，不把官方示例中的所有可选字段都当必填。

|消费点|最小校验与限制|
|---|---|
|共同传输|固定原 API／路径、认证上下文和版本；无 redirect，无 unsafe 自动重试。200 body 完整、未超预算、有效 JSON；保存方法／路径／精确 payload 摘要、响应摘要、实际 HTTP 状态与时间。截断、超限、解析失败或持久化失败不能因为已收到 200 头就确认成功。沿 [现有传输](../../src/ergora/issue_backends.py)与 [C1 attempt](../../src/ergora/issue_writebacks.py)|
|GitHub 200|必须为完整 label 数组，目标的原 native label ID＋精确 name 对应项存在且不歧义；验证返回 label URL 是该受控 repo 的资源。该响应不含 issue native ID 或操作者身份；受控请求路径＋发前原 issue GET／actor GET 是辅助事实，不能伪造成服务端原子目标 ID／actor 回显。未命中原 label ID 就不能把“另一个同名标签”确认成原意图 [GH-LABELS]|
|GitLab 200|必须为普通 issue 对象，核原全局 issue ID、iid、类型和受控 namespace；`labels` 为完整名字数组且包含精确目标名。issue 响应通常只给名称，`with_labels_details` 的已核字段也没有 label ID；后续 catalog GET 能补当前身份观察，不能证明写入瞬间的 label ID。因此 receipt 应明说确认的是 named-label request，不能声称已原子绑定原 label ID。若产品要求后者，就不支持该操作 [GL-ISSUES]、[GL-LABELS-API]|
|已存在|在尚无 attempt 的新意图中，若当前 target 已带这个已核标签，可显示 `already_present` 并不发写请求；这是当前事实，不补造历史 acknowledged。若意图已经 unknown，就算现在存在也仍是 unknown。无论哪家，200 都不证明本次新增过一次 [GH-LABELS]、[GL-CALLBACK]|

**集合上的重复追加看似幂等，不等于带人工并发的操作幂等。** 假设第一次已经加上标签但响应丢失，随后人将它移除；重发会重新加入，直接覆盖人的新意图。GitLab scoped 标签还会替换人的新 scope 值，名称消失／重建又能改变目标 ID；原生通知／事件也没有与本地 attempt 一一绑定的承诺。因此，即使 body 完全相同，也不得据“set union”自动重试。[GH-LABELS]、[GL-LABELS-USER]、[GL-FIND-CREATE]；这是基于原生合同的并发反例，不是本次实际运行结果。

恢复只读原冻结目标：标签存在、完整集合等于预期、同 actor 的 `labeled` 活动、时间接近，均只能说明当前／历史可见事实，不能排除同账号手工执行。标签不存在可能是未发出，也可能是后来被删；无匹配不证明未执行。两家接口都没有可查询的本地 attempt key，故响应丢失、发送后崩溃、结果保存失败仍保留 unknown；换 write ID、重新 prepare 或换 SDK 不能绕过同一逻辑动作已有 attempt。已确认 receipt 与后来 drift 分开保存，不自动补偿／重发。[GH-LABELS]、[GH-EVENTS]、[GL-ISSUES]、[GL-LABELS-USER]；沿 [C1 研究的因果限制](2026-11-11-issue-writeback.md)

## 若要移除／替换，哪些冲突仍无法解决

|动作／竞争|不能保证的人工意图|推荐处理|
|---|---|---|
|GitHub add 目标，再 DELETE 源名称|两次请求不是事务；加后删前人可能重新赋予源标签、改名或删除重建。DELETE 没有“仅删除本次原版本的赋予”条件 [GH-LABELS]、[GH-BEST]|不列入首片。即使未来分别记 attempt，也只能如实表达 partial／unknown，不能失败后自动删目标或补回源|
|GitLab 同个 PUT 发送 add＋remove|参数可合并在一个请求，仍无“仅当源标签的赋予未被人修改”前置条件；remove 按名称，不记录谁拥有该次赋予 [GL-ISSUES]、[GL-CALLBACK]|一个 HTTP 请求不等于并发 CAS。没有原子冲突拒绝保证时，须显式采用可覆盖的状态迁移语义；不能把它包装成严格保留人工意图|
|读到 source→人删 source 又加回→机器人删 source|原生 ID／最终集合甚至可以和发前完全相同；读回比较看不见赋予关系的 ABA，标签“由机器人拥有”的名称约定也不提供排他权限 [GH-LABELS]、[GL-ISSUES]|若要求尊重这次人工重新赋予，只能依赖实际验证的服务端版本条件／排他所有权机制，或把迁移留给人。发前多读一次、发后反向补偿都不能解决|
|GitLab scoped add|服务端自动替换同 scope 标签，可能移除刚被人加入的值；本地锁只串行本地操作者 [GL-LABELS-USER]、[GL-SCOPED-CODE]|默认拒绝 scoped，不称 append-only；确需互斥工作流时另立动作与支持合同|
|完整 labels 读改写|旧集合缺少人刚加的无关标签，又可能恢复人刚移除的标签 [GH-LABELS]、[GL-ISSUES]|两家都不使用这条路径，也不把 SDK `.save()` 旧列表当保留人的修改|

严格要求“凡有人工冲突都拒绝”的移除／替换需求，本次没有能实现的写 CAS。可用的低耦合退路是保留人工工作流标签，只加一个表达已发生候选事实的普通标签；若一定要维护互斥状态，就另片明确接受冲突语义或选择经过核验的原生机制，不补建第二个任务状态机。[GH-LABELS]、[GH-BEST]、[GL-ISSUES]、[F7 计划](../plans/2026-11-11-project-trackers.md)

## 现成 SDK 对 C2 的实际影响

本次复用准备研究的原 wheel，重新核同 SHA 并静态读标签／更新消费者；没有安装、导入、运行或重新下载 SDK。固定发行源码与本次 GitLab 服务端源码是不同证据。[准备研究](2026-11-11-project-trackers.md)、[C1 SDK 核查](2026-11-11-issue-writeback.md)

|方案|本次实读事实|对 C2 的影响|
|---|---|---|
|PyGithub 2.10.0|`Issue.add_to_labels(*labels)` 将 `Label` 对象转成 `.name`，POST 后把 `(headers,data)` 留在局部变量，方法返回 None；`set_labels` 则 PUT。`Github.default_retry=GithubRetry()`，allowed_methods 包含 POST，403／5xx 有重试路径；`retry=None` 文档说明可关闭 [PYGH-ISSUE]（行404–410、572–578）、[PYGH-MAIN]、[PYGH-RETRY]|传 Label 对象没有获得按 ID 原子追加；高层 add 方法也没有把原完整 200 回执暴露给消费者。另 GET 不能替代该回执。若选 SDK，需要受控原请求结果适配、禁写重试／redirect及预算验证，不能只包 `.add_to_labels()` 就满足 receipt 合同|
|python-gitlab 8.6.0|ProjectIssue 使用 iid；SaveMixin 将修改属性传给 manager，UpdateMixin 默认 HTTP PUT 并返回 result；将 `issue.labels` 改成旧整套再 save 会发送该列表。HTTP 默认 `obey_rate_limit=True`、`max_retries=10`，429 循环没有按 method 排除 PUT；transient retry 默认 false [PYGL-ISSUES]、[PYGL-MIXINS]、[PYGL-CLIENT]、[PYGL-UTILS]|必须验证最终唯一 payload 是 `add_labels` 而非 `labels`；`max_retries=0` 并禁止 transient retry，连同底层 transport 核最多一次发送。只关 transient 并不足够。SDK 不补上名称／scope／CAS／因果合同|
|现有 stdlib backend|C1 已有受控传输、actor、原 issue 读取；当前所有非 GET 写入硬编码期望 201，且只实现评论 [issue_backends.py](../../src/ergora/issue_backends.py)|C2 的真实新消费者只需要窄 label lookup／必要 catalog、单次 add 和当前标签事实；200 期望值应随具体原生操作声明。优先复用已有 HTTP 边界，不为此引入两套 SDK 或通用远程操作执行器|

## 最小落地设计与后续验收建议

以下均为**推荐，未实施／未运行**。原 C1 候选验证、State、backup／migration、CLI／受保护 HTTP、后台运行准入各有所有者；本研究不借 C1 正在进行的验收称 C2 已通过。[当前 C1 计划](../plans/2026-11-11-issue-writeback.md)、[issue_writebacks.py](../../src/ergora/issue_writebacks.py)、[state.py](../../src/ergora/state.py)

1. 在同一个 issue-writeback 领域增加一个显式 `candidate-label-add` 动作。准备沿原 `tasks.creation / show / export_status` 和 v7 来源核原 creation、run、candidate、export；普通 context link、另一来源、非导出候选不能进入。意图另存当前标签身份／准入限制、actor、非空单项 operand、受控 method／path／payload 摘要。它是新动作合同，不能修改 C1 记录的 kind 或原 v7 snapshot。
2. 上层只消费同一 backend Interface；provider 负责名称查找、namespace／scope 事实、原请求和严格响应映射。CLI／HTTP 不各自拼 URL。复用本地事务的逻辑唯一性，动作 scope 以原来源＋creation／run／export候选＋“追加候选标签”语义槽固定；不要把新 write ID／label 改名／重建当成绕过未知的通道。确认前变 operand 可以新准备，但已有 attempt 不允许清空重试。
3. 准备与发送前核相同 tracker 绑定、原 native issue、候选、actor 与 label ID／名称／所属容器；GitLab scoped／同名／不完整目录具体拒绝。精确目标已存在且无 attempt 可不发。追加只依赖这些相关事实，不要求无关 Agent 配置、工单评论或标题全部不变；本地 expected_revision 在持久化关键点重核。额外 GET 只能发现部分 drift，不能成为 CAS。
4. DB 短事务先持久化唯一 attempt，提交后才执行一次原生请求；长网络 I/O 不持有共享写事务。两家只接受完整且匹配的 200 形成 receipt；发送前中断也可成为“可能未发送”的 unknown，牺牲自动补发以保护人工意图。status 离线；observe 只读标签／必要 lookup并说明覆盖，不升级因果状态。
5. 普通追加、目标原已存在、空 operand／逗号／scoped 拒绝、同名祖先标签、rename／delete-recreate、两并发 send 仅一次写、原200与丢失／截断200、attempt后中断、结果保存失败、人工删后不得重发，应成为下一片有价值的本地故障证据。用“发前已存在，发时被删”反例展示 GitLab新建窗口；strict no-create模式必须明确拒绝，不能以真实账号试错。
6. 单独记录收到成功后的观察 drift、通知／To-Do／外部自动化未验范围和目标服务器版本；本地夹具不证明 SaaS 或任意 Self-Managed 写权限／部署副作用。移除／替换、scoped 工作流、标签创建／订阅管理、PR／MR／branch 发布仍另片。完整实现再按 AGENTS 做实际自身与 fresh-context 审查，不把本文当产品验收。

## 本次证据与限制

本次网络窗口 **2026-11-11 11:23:51–11:30:21 UTC**，共 **23 次无凭据 GET：21 次200、2 次301**；没有写方法或真实账号 API。新文档读取最多3,000,000 B、固定源码／tag读取最多1,000,000 B，每次timeout15秒、拒绝自动redirect、无自动重试。GitHub旧通知页301后另一次GET只核Location，随后对已核官方canonical地址单独GET成功。PAT与权限页各重复一次，仅为取得其scope链接／保留空表格单元格的权限矩阵；同hash。未另写缓存／HTML／源码文件，只在本文保存元数据和引用；原准备研究缓存只读。几个初期本地大输出被工具截断，相关必要段落后定向复读，截断输出不作为完整读取证据。

**复用并重新核 hash 的旧证据：** 下列原HTTP读取时间为05:54–06:00 UTC，本次没有重取这些页面。旧两wheel也没有重取。原市场／SDK／只读API调研的43 GET及7次raw源码超时只沿[原记录](2026-11-11-project-trackers.md)保留，不计入本次23 GET，也不说本轮发生了这些失败。

|证据|旧官方页面／发行物|字节／SHA256|
|---|---|---|
|K1|[GH-LABELS]，原05:54:25开始，200|458192；`c13171e29fae63ed49734171c34b2ae885261a9aec48c29563aea9f9c19be470`|
|K2|[GH-BEST]，05:54:25，200|332122；`5b4dd59640d53a7d5b7c1d99f229f6ba09faec9bcb9b184585b144476d751cf2`|
|K3|[GL-ISSUES]，05:54:28，200|458433；`818c1cc2e9c11593cd11d10ce7148ae11895cfe46a266e3516c8dd3e13a91e07`|
|K4|[GL-REST]，05:54:28，200|74504；`1bd38c8370a0ab2f9a030ab263c802c0c0ee69937523cf6e123ac7a9085b0bc4`；本次只复核原分页／项目路径背景，不扩大能力|
|K5|[GL-ERRORS]，05:57:59，200|54129；`eaf5bba7af80955f4c0750c80f102d0a8e16ae0bf121eb21655848a41a0d1cdf`|
|K6|[GH-EVENTS]，06:00:20，200|1058422；`d260fe050d1645e8c943eb3f87a6fd76bd3b28d5278bc24d9c3465767f1f1d90`|
|K7|[GH-WEBHOOK]，05:54:27，200|923680；`2b17179ff4536dcc9d12651a0888acd45181c52f2ab0d25e47eebe9abbb96aa9`；定向读label事件与issues labeled区别|
|K8|PyGithub 2.10.0官方wheel|455554；`192ada2a76e4afc7d6b37e500c9bfeba1731e6506697445a5ba1c4af8bf0b924`；本次读Issue标签方法、MainClass、GithubRetry|
|K9|python-gitlab 8.6.0官方wheel|159654；`34fee7e5576cf01982c4bfa98f94d50e24733edb66beba3cb8ef286287723019`；本次读issues／labels／mixins／client／utils，未运行|

**本次新GET：** GitLab固定源码先由官方project278964的tag API解析 `v18.5.0-ee` 到完整 `37cc4da7158316bb9b204cef9b056f16fff1df32`，之后十个源码GET均为官方repository-files raw API并固定该SHA。它是一个点位的静态核查，不是最新部署／跨版本验证。下面时间均为UTC开始时间。

|证据|来源／结果|字节／SHA256或失败范围|
|---|---|---|
|E1|[GL-LABELS-API]，11:23:51，200|125618；`a90fcce25d4fd06f333bc69bab7bb7beca687f1f130dc8768cec153248d09b9c`|
|E2|[GL-LABELS-USER]，11:23:51，200|73840；`9499412ce68891838e3f30cbd1375bfcb855afc5895a0534492bd8135370f33c`|
|E3|[GL-NOTIFICATIONS]，11:23:51，200|81913；`d01d8b2e6970606c5b738c1adbc559a5d59e5384067bf6c0d2daa1dc4ef87423`|
|E4|[GH-MANAGE]，11:23:51，200|194662；`7a27edf89f9c9529074f6ef3a34c795adcba8c280e959459a83ca6b2f27628c7`|
|E5|[GL-SOURCE-TAG]，11:25:09，200|826；`083ee96302df30e6c238d3110a5a46060e8bde2ca7e9cc99deca0ed8ec0ff5d8`|
|E6|[GL-PERMISSIONS]，11:25:35，200|144332；`4f2e2df83c09b04ece35ca319055b4fd530d1cfa16792490fc67ec2e430cda78`|
|E7|[GL-PAT]，11:25:35，200|81326；`f44572678e4ab8f870637f5f48de3c226756b0e379514e6ce2e93c743898101f`；本页只链接scope页，未凭其标题猜scope|
|E8|GitHub旧about-notifications地址，11:25:35，301|拒绝redirect；未保存body／hash／首轮Location，不能算成功正文|
|E9|[GL-API]，11:26:04，200|24324；`070da2e98afd5df2c24639ad50e9fb199a496247b9694226830c1e881e0c6adc`|
|E10|[GL-ISSUABLE]，11:26:04，200|21640；`6c93b23add06682ae0a1356e8090d2519396a7e4fa4e497a4034858510dc914d`|
|E11|[GL-UPDATE]，11:26:04，200|9633；`16c5b52b0fb0a1427696599b0c167de68234a064536ddb20b8bd1aa6ebc6f913`|
|E12|[GL-FINDER]，11:26:04，200|5096；`d3295da6d71bba2cbc286631af552e0e27463580a19ace4ca6f45950c5f3b9ae`|
|E13|[GL-API-HELPERS]，11:27:58，200|2689；`0f95785f9f79d915ab8049af9abe90922316efa12f59bdc94ab9f24252913901`|
|E14|[GL-CALLBACK]，11:27:58，200|2714；`fc873a5bb1b04580291b8a8fe64c6303bc32bfa825080fbea71985414a9f5682`|
|E15|[GL-ISSUES-BASE]，11:27:58，200|5576；`e60673b4cd1e730975d0b309321195b0d9d76ef13c93ed1f20fd4995ad33b629`|
|E16|[GL-PAT]再读，11:27:59，200|81326；同E7hash；取得实际`/security/tokens/access_token_scopes/`链接|
|E17|[GL-AVAILABLE]，11:28:46，200|1868；`c70d24474ac29835aedd0599b8c06e1b13dae5dae839fd33ea87404dfc784fca`|
|E18|[GL-FIND-CREATE]，11:28:46，200|2073；`b96c8973058f7a61c2e48d111e87692b166202b9b59b1fae71e30f24bc8e6515`|
|E19|[GL-SCOPED-CODE]，11:28:46，200|1436；`4440deef63dd6a6babd5a5741739ffc551a16675d33320f8cf645165e04f1e70`|
|E20|[GL-TOKEN-SCOPES]，11:28:48，200|41778；`7a8931bacfd350e5a9557528f3282cae2d228a293b5fdeb1afed6238efddee98`|
|E21|[GL-PERMISSIONS]再读，11:30:02，200|144332；同E6hash；逐td保留空格位，核existing-issue metadata行与footnote59|
|E22|E8旧URL再GET，11:30:02，301|只核Location为`/en/subscriptions-and-notifications/concepts/about-notifications`，未跟随或保存body|
|E23|[GH-NOTIFICATIONS]，11:30:20，200|118798；`8143b9979c171d373247ae8880ab7a972e38d0e3d9759a4f302386d32aa67ea1`|

滚动GitHub REST页的`apiVersion=2026-03-10`只是本次原资料版本；产品现有默认仍由binding拥有，本文没有更改默认。GitLab页面包含较新的版本／角色／归档特性，不能据固定18.5源码或最新页面声称覆盖所有版本。尚未核：真实SaaS／Self-Managed标签写行为、目标版本与feature flags、SDK运行／底层故障、GitHub缺失label精确失败语义、完整notification投递／actor订阅变化、外部自动化、GraphQL按ID替代、真实并发与数据库隔离。本文只完成定向证据研究；本地产品／夹具／六阶段验收均未执行。

本文的本地相对链接、33个引用定义和尾空白最终静态核验通过。首个末轮检查脚本因多余括号以SyntaxError退出，修正脚本后重跑；这是文档检查，未执行产品测试。

## 后补：按 ID 的 GraphQL 接口选择

本节是同日 **11:48:48–11:51:55 UTC** 的追加核查；不改写上文名称 API 的事实。**推荐修正接口优先级，而非先实现名称方案再补绕路：GitHub 优先采用已核 ID mutation；GitLab 优先核其 ID 追加路径的目标部署与完整回执，再决定是否支持。** 没有原生 ID／schema／权限证据时显示 unsupported，不静默退回同名 REST。这里只复用现有有界 HTTP、来源／候选／attempt 所有者，不引入 SDK。[GH-GQL-SCHEMA]、[GL-GQL-UPDATE]；[现有 backend](../../src/ergora/issue_backends.py)

|核查点|官方 schema／固定源码与结论|
|---|---|
|GitHub 输入|FPT schema 的 `AddLabelsToLabelableInput` 有 `labelableId: ID!`（Issue／PR／Discussion）、`labelIds: [ID!]`、`clientMutationId: String`；新版还有互斥的 `labels: [LabelUpdateInput!]`。C2只发非空单个 `labelIds`，不发 suggestions／rationale 路径。不要把 REST 整数 `id` 当 GraphQL ID，也不要自行编码；由受控读取取得并核 repo／number／原 native ID 对应关系，再冻结不透明 GraphQL ID [GH-GQL-SCHEMA]、[GH-GQL-CALLS]|
|消除的名称窗口|ID 参数选择原 issue 和原 label 对象；改名不会使请求按旧名称命中另一个新对象，删除重建的同名标签也不是原 label ID。不再发送名称或 create-label 参数，故消除了本次 REST 的按名称查找／find-or-create 路径。不存在／不可见 ID 的具体错误、服务端副作用和部署兼容仍未写实测；不允许失败后按名称重新定位再写 [GH-GQL-SCHEMA]|
|实际 payload|`AddLabelsToLabelablePayload` **只有** `clientMutationId: String` 和 nullable `labelable: Labelable`。`Labelable` 本身没有 `id` 字段；需 `labelable { __typename ... on Issue { id number repository { id } ... } }` 才能核确实返回原 Issue。它没有“刚新增的 label IDs”、assignment ID、执行次数或 operation receipt 字段 [GH-GQL-SCHEMA]|
|membership 必须实读|`Issue.labels`／`Labelable.labels` 仅有 after／before／first／last／orderBy，没有 `labelId`／`ids` 过滤；返回 `LabelConnection` 的 nullable nodes／edges、pageInfo和totalCount。可在原 mutation 的有限一页 `nodes { id name repository { id } }` 中查目标，不能虚构 `labels(ids:...)`。单独 `node(id: labelId)` 只取标签对象，不证明属于该 issue。分页未见目标不代表不存在，也不能再次执行 mutation 来翻页 [GH-GQL-SCHEMA]|
|clientMutationId|已核输入与 payload 各有此字段，描述为 client 标识；只能作为预期回显核对。schema 没有重复 key 去重、按 key 查执行结果或 CAS 的合同，不能当服务端幂等键。丢响应后仅凭回显值、当前 membership或同账号活动仍不能证明原 attempt [GH-GQL-SCHEMA]；沿本研究的因果边界|

**严格原响应建议：** 200 只通过传输门槛；同一次完整 JSON 中还须无 top-level `errors`、payload非null、回显值匹配、Issue／repo ID匹配，以及原响应选中页确实含原 label ID。nullable／缺字段、`data` 与 `errors` 同时出现、selection的部分结果或超限／截断均不形成该严格 receipt；不能因 errors 就推断 mutation未执行。若原响应一页未含目标，仅保存不充分结果／unknown；后续只读分页是当前事实，不能冒充原响应或触发重发。正向目标匹配并不要求把其他所有标签翻完，也不证明本次首次新增。以上是建议的本地接受合同；本轮没有发送 mutation或实测 GitHub partial-200。GitLab 官方文档也展示授权失败的 top-level errors／null，以及部分 query 字段无 errors 但为null，因此只判“无errors”同样不够。[GH-GQL-SCHEMA]、[GL-GQL-DOC]

**GitLab 真实等价与剩余限制：** 固定 `37cc4da…` 的 `Mutations::Issues::Update`，GraphQL名 `UpdateIssue`，声明 `add_label_ids`／`remove_label_ids`／全量 `label_ids`；resolver明确为 `resolve(project_path:, iid:, **args)`，返回 `issue` 与 `errors`。因此确认的是 `updateIssue(input: {projectPath, iid, addLabelIds})`，**不是已核 `issueId` 目标接口**。label IDs 经 `parse_gid(...expected_type: Label)` 后进入原 `Issues::UpdateService`；旧已核 callback 的 ID分支只筛可用 IDs，不进入 `find_or_create_by_titles`。这避免缺名新建、同名 namespace选择和按名称删除重建的重定向；失效／无权 label ID仍可能被过滤而无变化，所以须核目标 membership，不能只看 payload.errors为空。[GL-GQL-UPDATE]、[GL-CALLBACK]（E14）、[GL-AVAILABLE]（E17）

**按 ID 不冻结 label 定义。** 同一个 GitLab label ID可以在发前检查后被改名成 `workflow::review`；原 EE callback仍按当前scope做互斥过滤，可能移除人的同scope标签。故单纯禁用准备时含 `::` 的名称仍不能提供“任何竞态下绝不移除人工标签”的严格保证。ID追加值得优先，但 strict保证仍须有经核验的标签定义条件／排他约束，否则明确该剩余风险或拒绝支持。GitHub这条已核input也没有label metadata版本条件。GitLab `workItemUpdate`等纯全局issue ID替代、完整IssueType／label connection返回schema、mutation注册／部署版本均未核；不在本文预造可执行GL selection或宣称其已可完整验收。[GL-SCOPED-CODE]、[GL-LABELS-USER]、[GH-GQL-SCHEMA]

|endpoint／认证归属|本次已核与适配要求|
|---|---|
|GitHub.com|`https://api.github.com/graphql`，查询／mutation通常POST JSON；官方说明PAT、App、OAuth及资源所需scope／permission。仅REST读权限不能推断mutation可写；`viewerCanLabel`也只是预检，发送时仍由平台授权 [GH-GQL-CALLS]、[GH-GQL-SCHEMA]|
|GitHub Enterprise Server|本次3.19官方调用指南给 `http(s)://HOSTNAME/api/graphql`，与REST `/api/v3`不同。工具仍沿现有HTTPS／loopback政策，不扩大为任意HTTP。读取的FPT schema不代表3.19 schema；本轮未取得该版mutation schema／真实token兼容，不因同名mutation自动支持任意GHES [GH-GQL-GHES]|
|GitLab.com／Self-Managed|实例的 `/api/graphql`，不是REST `/api/v4/graphql`。部分query可匿名，mutation必须认证；官方列OAuth、personal／project／group token和Bearer header。沿外部token_env取得值，不使用URL query token，也不把当前REST PRIVATE-TOKEN header不经核验直接套过来；scope与项目授权仍需满足。当前固定源码不表示所有实例已部署同一schema [GL-GQL-DOC]、[GL-TOKEN-SCOPES]|

**新增网络预算已止于8 GET：7次200、1次404，无真实GraphQL调用。** 每次timeout15秒、拒绝redirect／自动重试；GH schema读取上限7,000,000 B，失败的GL schema定位上限12,000,000 B，GL源码1,000,000 B，其余文档3,000,000 B。下表每行均为一次请求，时间UTC；同URL重复也逐次计数。未另存缓存文件。

|证据|URL／开始时间／结果|bytes／SHA256与实际范围|
|---|---|---|
|G1|[GH-GQL-SCHEMA]，11:48:48，200|1584905；`46f1d455d72ab784c6cb2b86e9b023df195dcfd2ed92099108b0faa5faa5d1fc`；完整下载，但工具输出截断，仅保留输入／payload前段，不据它断言完整schema|
|G2|[GH-GQL-CALLS]，11:48:48，200|264545；`fa22e065cced008aa24fd563675fd3680b49718740d74e44f9c2d54e7e34e0c3`|
|G3|[GL-GQL-SCHEMA-MISS]，11:48:48，404|定位的固定文件路径不存在；未保留error body／hash，不能据此称GitLab无静态schema|
|G4|[GL-GQL-DOC]，11:48:48，200|70859；`c557d838f16ef69def3ef7f30f774ae1778be7354db17e76897812366f884be3`|
|G5|[GH-GQL-SCHEMA]，11:50:43，200|1584905；同G1hash；定向提取正则转义错误，全部类型未命中，不计为字段核查成功|
|G6|[GL-GQL-UPDATE-RAW]，11:50:43，200|3021；`9c9cbc477232fc90a6e14db5087ae5c2b2a9e55a9b523e9a054377ce9914ac2f`；固定官方repository-files raw API完整源码|
|G7|[GH-GQL-SCHEMA]，11:51:51，200|1584905；同G1hash；改用行提取，完整核input／payload／Labelable／LabelConnection／PageInfo与Issue／Label／Query／Mutation／Repository所需字段，无截断|
|G8|[GH-GQL-GHES]，11:51:51，200|260824；`939e682f25305482fa01825a5492125ae03d07853fce0c7e3f637dfaadbb6e7a`；只核调用／认证／endpoint，未借它证明企业版mutation字段|

## 第一方来源

[GH-LABELS]: https://docs.github.com/en/rest/issues/labels?apiVersion=2026-03-10
[GH-BEST]: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
[GH-MANAGE]: https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels
[GH-NOTIFICATIONS]: https://docs.github.com/en/subscriptions-and-notifications/concepts/about-notifications
[GH-EVENTS]: https://docs.github.com/en/rest/using-the-rest-api/issue-event-types?apiVersion=2026-03-10
[GH-WEBHOOK]: https://docs.github.com/en/webhooks/webhook-events-and-payloads
[GL-ISSUES]: https://docs.gitlab.com/api/issues/
[GL-LABELS-API]: https://docs.gitlab.com/api/labels/
[GL-LABELS-USER]: https://docs.gitlab.com/user/project/labels/
[GL-PERMISSIONS]: https://docs.gitlab.com/user/permissions/
[GL-PAT]: https://docs.gitlab.com/user/profile/personal_access_tokens/
[GL-TOKEN-SCOPES]: https://docs.gitlab.com/security/tokens/access_token_scopes/
[GL-NOTIFICATIONS]: https://docs.gitlab.com/user/profile/notifications/
[GL-REST]: https://docs.gitlab.com/api/rest/
[GL-ERRORS]: https://docs.gitlab.com/api/rest/troubleshooting/
[GL-SOURCE-TAG]: https://gitlab.com/api/v4/projects/278964/repository/tags/v18.5.0-ee
[GL-API]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/lib/api/issues.rb
[GL-API-HELPERS]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/lib/api/helpers/issues_helpers.rb
[GL-ISSUABLE]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/app/services/issuable_base_service.rb
[GL-UPDATE]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/app/services/issues/update_service.rb
[GL-ISSUES-BASE]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/app/services/issues/base_service.rb
[GL-CALLBACK]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/app/services/issuable/callbacks/labels.rb
[GL-SCOPED-CODE]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/ee/app/services/ee/issuable/callbacks/labels.rb
[GL-AVAILABLE]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/app/services/labels/available_labels_service.rb
[GL-FIND-CREATE]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/app/services/labels/find_or_create_service.rb
[GL-FINDER]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/app/finders/labels_finder.rb
[PYGH-ISSUE]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/Issue.py
[PYGH-MAIN]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/MainClass.py
[PYGH-RETRY]: https://github.com/PyGithub/PyGithub/blob/5cdf6ab395c52efb652d0bc1f28fdf2e452b1b41/github/GithubRetry.py
[PYGL-ISSUES]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/v4/objects/issues.py
[PYGL-MIXINS]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/mixins.py
[PYGL-CLIENT]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/client.py
[PYGL-UTILS]: https://github.com/python-gitlab/python-gitlab/blob/51eb17e6e67a25157e04b0abc649221bd8ecc7fe/gitlab/utils.py
[GH-GQL-SCHEMA]: https://docs.github.com/public/fpt/schema.docs.graphql
[GH-GQL-CALLS]: https://docs.github.com/en/graphql/guides/forming-calls-with-graphql
[GH-GQL-GHES]: https://docs.github.com/en/enterprise-server@3.19/graphql/guides/forming-calls-with-graphql
[GL-GQL-DOC]: https://docs.gitlab.com/api/graphql/
[GL-GQL-UPDATE]: https://gitlab.com/gitlab-org/gitlab/-/blob/37cc4da7158316bb9b204cef9b056f16fff1df32/app/graphql/mutations/issues/update.rb
[GL-GQL-UPDATE-RAW]: https://gitlab.com/api/v4/projects/278964/repository/files/app%2Fgraphql%2Fmutations%2Fissues%2Fupdate.rb/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
[GL-GQL-SCHEMA-MISS]: https://gitlab.com/api/v4/projects/278964/repository/files/doc%2Fapi%2Fgraphql%2Freference%2Fgitlab_schema.graphql/raw?ref=37cc4da7158316bb9b204cef9b056f16fff1df32
