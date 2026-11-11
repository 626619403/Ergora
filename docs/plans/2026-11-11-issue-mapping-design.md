# F7b.0：保存工单来源与显式 task 上下文关联（设计，未实现）

日期：2026-11-11。只读源码基线 `9f010079126f374c01272ecf2f0ec85284e4e2cc`，分支 `refactor/architecture-foundations`。本笔记供下一片定范围，不表示 F7b 已实现或正式派工已准入。上游要求见 [F7 分片](2026-11-11-project-trackers.md)、[总计划 F7／DS4](2026-11-01-all-in-one.md)；状态仍以 [PLAN](../PLAN.md) 和所属交付记录为准。

建议先交付：普通项目显式读取并保存不可变 snapshot；操作者将某个精确 snapshot 关联到同一控制面项目中已经 published 的原 creation intent。只提供可查询的上下文关系，不创建／提交 task，不改其输入、批准或权限，不接 webhook、poller、回写、Agent 或新的调度器。后续自动／人工派工入口的窄准入另片设计和验反例。

## 已核真实所有者

|所有者|当前事实及对本片的含义|
|---|---|
|[issues.py](../../src/ergora/issues.py)、[issue_backends.py](../../src/ergora/issue_backends.py)|`show` 从一个项目文档解析有效 tracker，单 GET 后返回完整 `issue-observation-v1`；项目／配置修订、API base、namespace、number／iid、native ID、正文、ETag、响应摘要与观察时刻均有，当前不保存。CLI／HTTP 是两个真实消费者。继续由 `issues` 持有保存／关联用例，不增加 storage／plugin Interface。|
|[projects.py](../../src/ergora/projects.py)|绑定保存会增加 revision，只有当前项目文档，没有旧修订表；不能只保存 configuration SHA 后声称能从新绑定复原旧来源配置。|
|[tasks.py](../../src/ergora/tasks.py)、[reference_task_creation.py](../../src/ergora/reference_task_creation.py)|`tasks.creation` 已由原所有者校验 intent／原生文件，返回 published／pending／conflict、intent SHA、compiled SHA 和原 created revision；它不启动执行。本片只复用这个结果，不自己解析正式合同或复制 `_Creation` 校验。|
|[reference_inputs.py](../../src/ergora/reference_inputs.py)、[reference_task_submission.py](../../src/ergora/reference_task_submission.py)|v1–v6 Input、submission intent、attempt-before-send、memo 与 unknown 对账已有原所有者。本片不增加 Input 版本，不触及这些运行入口。|
|[state.py](../../src/ergora/state.py)、[backups.py](../../src/ergora/backups.py)|现有 SQLite schema v1、16 张表，集中有序迁移／预迁移 DB 快照、事务与跨进程／Windows `file_lock` 已具备；完整离线备份绑定 DB 和状态目录普通文件。直接复用，不另建备份器。|
|[definition_bundles.py](../../src/ergora/definition_bundles.py)、[asset_trees.py](../../src/ergora/asset_trees.py)|定义库拥有 Agent／Workflow 的版本、指令／资源包与索引发布，目录对象和 index 之间允许留下完整未引用对象；不适合作为工单事实与多对多关联的 owner。可借鉴发布约束，不扩展成通用文档库。|
|research／source_snapshots／memory|分别拥有研究抓取及 raw 文件、研究状态、记忆修订；不得以相似的 JSON／摘要字段把工单事实塞进这些表。|

旧 [注册](../../src/ergora/registrations.py)／[正式 tracker 合同](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/contracts.py)没有 API host 或 native issue ID；[ingress](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/ingress.py)按 `kind/project/issue_id` 并 casefold namespace，明确保守地让不同 host 的同名空间共享 claim。这个旧行为及 283 冻结参考文件均保持。

## 存储选择

|问题|现有 State 内新增版本化 SQLite 表（建议）|不可变 JSON 原子文件|
|---|---|---|
|完整性／并发|唯一键和一次短事务处理重复保存／关联；无 DB 与来源文件的双写；本片网络 GET 不占写事务。|单文件发布容易，但 snapshot 与 link 两类对象、引用检查、并发去重、发现列表需要锁／发布顺序；额外索引又产生 index 与对象的恢复责任。|
|升级与旧 writer|必须增加真实 v2 迁移，替换所有旧表 writer fence；这是一项可验证的固定成本。|文件有自身版本仍需旧 writer／备份／索引协议；避开 DB 版本并不能免除这些责任。|
|备份／恢复|现有 DB snapshot 自动覆盖新表；领域校验接到现有备份验证即可。|现有离线全目录清单会包含新文件，仍需校验对象摘要及 link 引用。与独立执行目录也没有自动事务。|
|Windows|现有 sqlite3 与迁移锁已跨平台；不把项目 ID／namespace 当路径。|须避免大小写碰撞、保留名称、symlink／reparse point；暂存同卷、原子发布与目标存在语义都要覆盖 Windows。现有定义库不是可直接复用的工单发布 Interface。|
|查询／增长|按项目及目标 task 的实际查询建索引即可，有界读取 metadata。|无索引必须扫描；有索引则新增可重建索引协议、跨文件一致性和测试，现无收益支持这些成本。|

因此选现有 `ergora.sqlite3` 中两张专属表，不选另一 DB，不引入 ORM／Repository 或可替换存储层。JSON 导出等有真实消费者时再加。

迁移必须保留历史 v1 的 16 表声明及 `_schema_v1` 语义，不把新表直接加入 v1 的 `_TABLES` 后伪装成旧布局。当前 48 个旧触发器将允许 writer 版本写死为 1；v2 须在同一迁移事务中替换全部旧表触发器，再保护两张新表。否则已打开的 v1 客户端仍可写旧表。旧 v0／v1 行、额外表／索引、文件资产不重写；新二进制拒绝未来版本，旧二进制拒绝 v2，失败回滚并保留已有预迁移备份。无需 downgrade；回退使用原备份。

## snapshot 的身份与时间

保存稳定 payload：

```text
schema_version: 1
observation: 完整 F7a issue-observation-v1，但去掉 observed_at
tracker_binding: 当次有效 tracker binding 的副本（只含配置，含凭据环境变量名，不含值）
```

`observation` 必须有 F7a 用例补充的 `project.id/revision` 和 `configuration_sha256`；不能接受缺来源的 Adapter 结果作为已保存项目 snapshot。`source.api_url` 使用当次 Adapter 解析后的完整 API base，保留 path／port；provider、namespace、number／iid 和 native ID分别保存。namespace 不统一 casefold，不从 `web_url`、Git remote、正文或当前绑定猜 host。选中的 API version／token_env 引用由当次 binding 保留；不冻结无关 Agent 配置或安装状态。

`snapshot_sha256` 对上述 payload 做明确的 canonical JSON SHA256（UTF-8、sort_keys、紧凑分隔、ensure_ascii=False、allow_nan=False）。摘要不含观察时间。既有 `response.sha256` 继续表示原 HTTP body 的字节摘要；ETag／updated_at 只作来源事实，不作为 CAS 或唯一版本。未保存原 HTTP body，不称可重建原生响应。

首次 INSERT 额外保存 `first_observed_at`，含义是首条成功落库观察的读取完成时间；并发时以成功插入者为准，不承诺跨请求或机器时钟的绝对最早时刻。每次 capture 回执另返回本次 `observed_at`。相同 payload 重读保留 snapshot 摘要和原 first time，只在本次回执呈现新 observed time，不 UPDATE 旧 snapshot，也不制造“最后读过”等于来源仍有效的状态。

不同正文、响应摘要、ETag、来源、项目修订或配置摘要会形成新 snapshot。即使 updated_at 没变也不能覆盖旧 snapshot。相同语义但不同原生 JSON 字节可保守地形成不同 snapshot；不先设计语义去重算法。独立工单之间、不同 host、不同配置修订之间都不合并。

建议表的最小列：

```text
issue_snapshots(
  project, snapshot_sha256, first_observed_at, document,
  PRIMARY KEY(project, snapshot_sha256))

issue_task_links(
  project, snapshot_sha256, task_id, creation_sha256,
  linked_at, document,
  PRIMARY KEY(project, snapshot_sha256, task_id, creation_sha256))
```

document 是各自版本化完整记录；可查询列必须与其内容及摘要一致。snapshot payload 不重复放原观察时间。仅对真实反向查询加 `(project, task_id, creation_sha256, snapshot_sha256)` 索引。无需 source_heads、task_heads、自动采用指针或通用事件表。使用 INSERT＋冲突后比较原记录，不用 REPLACE；不增加 UPDATE／DELETE 用例。

## capture、link 与恢复

**Capture：**先读取并固定一个项目文档，校验请求的 expected revision；同一份文档解析 binding／配置摘要并调用现有读逻辑，保持已注册项目 namespace 检查。`show` 与 `capture` 共用这个固定快照算法，不能 GET 后再读取当前项目来补历史配置。GET 结束才开短事务保存完整结果；保存期间发现同摘要时返回原记录。GET 期间绑定改变仍可保存明确标注旧 revision 的观察，与现有 `show` 的冻结快照语义一致，不把新绑定拼进旧响应。失败／超限／截断不保存半份 snapshot。

本片只有只读 GET，没有 capture request ledger。顺序／并发重复 capture 可能再次 GET，相同 payload 仅一份 snapshot；重放时远端已变则保存新的 snapshot。响应丢失后可列出已存 metadata，或重新 capture；不宣称恢复了恰好同一次读取事件。稳定 Trigger 去重及一次派工由后续 observe／正式提交片负责，不能借本片的内容去重提前关闭 DS4。

**Link：**调用者明确给项目、snapshot SHA、task ID、creation intent SHA及当前 expected project revision。新建关系时在现有 State 短写保留中检查 revision、snapshot 所属项目及摘要，调用原 `tasks.creation`。只接受 `published`，且原 `intent_sha256` 与输入一致；记录其 `compiled_sha256`、`created_revision` 及 `intent_sha256`。pending 应先通过原 resume-create 完成；conflict、not_recorded、无原 intent 的 legacy task、另一控制目录／项目和摘要不符均不保存关系。不解析 task 文件，不调用 preview／create／start，不访问 Temporal。

保存的关系明确为 `context_only: true`、`relationship: operator_asserted_context`。其含义是操作者把此来源提供给这个精确 creation 的上下文关联；不是原合同的“原始输入已包含此工单”，不承诺运行中的 Agent 已读取它。这里不从旧 task 缺 host 的 triple 推导原生同一 issue，不授予源可写权或接单权，也不修改 ingress claim。完整来源身份只能由 snapshot 证明；正式任务来源身份的补足需要后续显式新合同。没有必要为这个上下文操作增加批准步骤。

一张工单／一个 snapshot 可关联多个 task；同一 task 可明确关联后续新 snapshot，旧关系保持。当前正式 task 不提供可覆写的 task revision：新工作修订使用原合同允许的新 task ID／creation；`created_revision` 是项目修订，不能显示成 task 修订。新 link 唯一键只防止同一上下文关系重复，不是工单执行占用或调度去重。

重复同一 link 在任何新 target 检查前返回原记录，保留原 linked_at；响应丢失／重启不会增加关系。已经保存的 snapshot／link 读取不解析当前 binding、不读环境变量、不调用 task／网络；binding 改为 manual、删掉 token 或来源下线也能阅读原事实。需要新关系时才按当前项目 revision 和真实 creation 校验，不用旧 link 代替当前正式准入。

不提供 UPDATE／删除关系，也不隐式把较新 snapshot 当作 task 已采用上下文；后续若确有撤回消费需求，应追加明确撤回事实，再由消费者显示，不能覆写历史。

## 最小 Interface 与受影响文件

`issues` 在既有 `show` 外增加五个完整用例：`capture`、`snapshots`、`snapshot`、`link_task`、`links`。CLI／HTTP 调同一 Interface，不按 GitHub／GitLab分派；`tasks.creation` 继续校验正式目标，不需要改其返回合同或增加第二套 target validator。

|操作|CLI／HTTP 建议|
|---|---|
|读取实时来源（保持）|`issue show PROJECT NUMBER`；现有 `GET /api/projects/{project}/issues/{number}`|
|保存一次来源|`issue capture PROJECT NUMBER --revision N`；`POST /api/projects/{project}/issues/{number}/snapshots`，body仅revision|
|列出已存 snapshot metadata|`issue snapshots PROJECT --limit N --after CURSOR`；`GET /api/projects/{project}/issue-snapshots`|
|离线读一份完整 snapshot|`issue snapshot PROJECT SHA`；`GET /api/projects/{project}/issue-snapshots/{sha}`|
|显式关联|`issue link-task PROJECT SNAPSHOT_SHA TASK --creation-sha256 SHA --revision N`；`POST /api/projects/{project}/issue-links`，body对应精确字段|
|查询关系|`issue links PROJECT --snapshot SHA` 或 `--task TASK`；`GET /api/projects/{project}/issue-links`，对应过滤|

列表需要有界分页，因为它们用于恢复响应丢失的保存及发现一个来源的多个关系；snapshot 列表只返回摘要、完整 source 定位、项目 revision、title及首次观察时间，不批量返回正文／binding。建议 limit 1–100，按不可变主键排序，用同一过滤范围的游标继续；不按可重复或倒退的时钟当唯一游标。link 列表也只返回关系 metadata；完整正文通过 snapshot SHA 单独读取。不得只回前 N 件却无截断／下一页说明。游标绑定原过滤条件；分页不承诺跨请求固定视图，期间新增且排序在游标之前的记录须从首页重新查询。

持久 snapshot／link 各明确记录版本及字段校验；复用已有 observation schema 校验内容，不复制厂商字段规则。无须为 list／capture 回执再造通用协议，不改旧 `issue-observation-v1` 或 WorkflowInput。HTTP mutation 自动沿现有 local origin／`x-ergora-request`／4 MB body保护；GET 保持无持久副作用。CLI 与 HTTP只做传输映射。

生产改动集中于 `issues.py`（算法／记录／查询／领域校验）、`state.py`（v2迁移及writer fence）、`backups.py`（调用领域检查）、CLI／Web入口及本域持久 schema；不增加泛用存储文件。`issues` 的备份校验入口直接接受现有 DB reader，检查摘要／列一致性／悬空 link，不构造 State、不触发迁移，也不访问外部执行目录。

完整离线备份已有全库快照与完整状态目录清单；新记录随其恢复。本域检查须兼容没有新表的 v0／v1 备份；v2 缺表或两表关系损坏则拒绝，不能为了校验旧备份先迁移它。预迁移快照仍只保证 DB 的原布局。备份器当前明确要求同平台、原 state home，不借新表声称跨 Windows／Linux迁移。正式 execution 目录可能在 control home 外，不能声称控制面备份包含它；恢复后已存关系仍可读，但新 link 或正式运行须由原所有者检验原 execution／creation，不能从 link 复制或重建 task。

## 实现片必须通过的反例

|可静默出错的风险|最小可验收证据|
|---|---|
|时间导致每次重读新版本；更新覆写旧内容|同项目修订的相同响应两次／并发 capture 仅一snapshot，原 first time保持；当前 observed time独立；同 updated_at 下改正文生成新snapshot，旧字节及旧link保持。|
|读取中换绑定／新绑定借用旧快照|沿现有本地 HTTP `on_read` 改 binding；保存原revision／完整source／当次binding，后改manual并清token仍可离线读；新capture按新绑定明确失败或生成新snapshot。|
|跨host／number与native ID串用|相同namespace／number／native ID、不同API base的snapshot必须不同；GitLab id与iid仍分开；旧hostless creation的link输出始终是asserted context，无身份核准或派工承诺。|
|错误目标／重放悄悄创建工作|用真实tasks.creation夹具覆盖published、pending、conflict、另一project／control、错intent SHA；错误不留link，published精确目标可关联；重复／并发link和丢响应后读回仅一关系。比较原creation／task／批准字节保持，start／Temporal／Agent调用为零。|
|多任务关系被最新状态替换|一个snapshot关联两个原task，再给其中一个task关联新snapshot；三个明确关系可按来源和task读回，旧对象／批准均保持；不把project revision解释成task revision。|
|新表升级破坏旧writer fence|真实v1夹具→v2及v0→v2保留旧行／资产／额外对象；故障和进程中断回滚；升级前已打开且writer函数返回1的连接对16旧表及新表均不能写；新State可正常写；新旧版本拒绝范围准确。|
|备份／恢复只保DB完整而丢语义|现有offline备份／verify／原位置restore后 snapshot／link／摘要相同；损坏document摘要或悬空link在备份发布前被本域检查拒绝；不需要reference安装或tracker连通。|
|传输入口行为分叉或无界读取|CLI与HTTP各覆盖capture→完整离线读→link→有界恢复查询；HTTP POST沿原保护拒绝缺header，GET不新增记录；分页跨相同时间点仍无漏项／重复；完整正文只在单snapshot读取。|

复用现有 [工单本地 HTTP 夹具](../../tests/test_project_issues.py)、[creation／恢复测试](../../tests/test_task_creation.py)、[迁移](../../tests/test_state_migrations.py)及[备份](../../tests/test_state_backups.py)，仅补上述新风险；不复制 F7a 所有 Adapter 参数反例，不再搭模型／CI框架。实现阶段更新本片计划／交付记录后再作新的完整独立审查。此次只读设计没有运行生产测试、安装、模型调用、外网请求或提交，也没有完成这些验收。

正式派工前的下一设计片仍须回答：完整来源身份怎样进入新版本 Input；所选任务实际能力怎样准入并保留项目 policy／可信checks；旧doctor依赖怎样按入口收窄；hostless casefold ingress的保守碰撞怎样保持兼容；所有入口如何使用同一claim；重放／机器人消息不扩大授权；submission attempt／memo／unknown仍如何用原ID恢复。本片的context link不能作为答案。
