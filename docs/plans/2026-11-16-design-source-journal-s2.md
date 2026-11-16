# WA5-S2：原 approval journal 的设计来源存取 proposal

2026-11-16。**待 fresh 独立设计审的局部 proposal；没有本片源码、安装、运行或人类身份验收。** 本文只把[已审拆片的 S2 行及第 5 节](2026-11-16-design-gates-registration-and-journal.md)收敛成下一片的实施与验收合同，继续服从[WA5 详细设计](2026-11-16-design-knowledge-gates.md)及[用户 D1–D4](../delivery/2026-11-16-workflow-design-decisions.md)。它不开放任何设计批准或执行关卡。下文标作“拟”的函数、文件和字段都尚未实施，名称可在原 owner 内收敛，行为与验收边界不能省略。

## 1. 准确基线、依赖与交付边界

|输入|本稿实际读取的身份／边界|
|---|---|
|产品源码|`/home/wangxinhai/project/Ergora`，分支 `refactor/architecture-foundations`，HEAD `c540939d3b3f38f3851b0de965c9cd0f969eea77`；`src` tree `88b9ca4a1a3ab40e578b852465d8425ad9b2f0d2`，`tests` tree `11ca981bcc4e7b4c5de7d21dfdb9a3ba6098e64b`。读取时 `src/tests/pyproject.toml/scripts` 无工作树差异；根已有并行 docs 差异，全部保留。|
|a1|当前源码已含 inspection-only 的完整 packet reader 及两公共 reader 共用应用校验的修正。以当前实际代码为调用依据；[a1 交付](../delivery/2026-11-16-design-packet-inspection.md)／[独审](../delivery/2026-11-16-design-packet-inspection-source-review.md)保持自己的源码、安装及运行身份，不转授 S2。|
|已审依据|WA5 详设当前 SHA256 `5360d993ee7851f81237151f9ed2e5aba7a9f1f7dbf501f88e33dd18b61faa54`；D1–D4 `f4890512a56b7010b7ca4ca9b40aefa8a366a5b25f4ebe4d0e7fb73c73f37b68`。拆片本稿读取字节 SHA256 `bde47bee749ff973901beeebc6f148316b3ea2d2635e191ac5804942e142f984`；其[原审](../delivery/2026-11-16-design-gates-registration-and-journal-design-review.md)的 approve 只认证当时固定拆片，不认证本 proposal。|
|S1|原固定候选 `121ed2b` 及其后继修正均未作为本稿的产品基线；[原交付](../delivery/2026-11-16-design-policy-registration.md)已有自身模板提出的新 v1 FAILED 回执 finding。主控在本稿收尾时补充：修正版 `80cb39c` 定向92项通过，新安装／独审仍待闭合，尚未合入；此为主控交接事实，本轮未代验其原运行。不能因旧安装、原独审或这92项称 S1 已完成。|
|S2 与 S1 的关系|S2 可以在现有 v1 项目的原 a1 packet 任务下独立交付，不等 S1 成功发布。S2 不导入 `design_policy`、不迁移 State；集成时只核 S1 最终 registration 版本合同及原 v1 任务不变。F/J 才消费冻结 policy／owner。|

`docs/PLAN.md` 的恢复检查点可能滞后于上述实际 HEAD；主控负责统一更新 PLAN／交付，本稿不重写它们。后继实施应建授权的隔离树，重新固定精确 source/diff、完整新增文件及 source 配置；根后续 docs 提交不自动改变本稿源码基线。

**S2 的可观察产物：** 原任务下可显式保存两轮完整设计／报告和原答复；按原 operation ID 读回、恢复；原 `task plan` 与新增最小 `task design inspect` 确实返回完整源链及全文。所有记录均为 discussion / inspection-only：Agent 或 `reported-human` 原文不能闭合 Q／K 的 owner 处理，不能生成 resolution、seal、批准或执行权。知识原件到齐可显示“材料已提供”，仍须明确区分 owner 决定。

无 packet 的旧 plan 返回、普通 schema1 approve／cancel、原 receipt 和 signal payload 不增加字段或要求；已有 a1 profile／schema 字节、旧 admission1–11、definition1–7、283 份参考资源及原锁保持。S2 不承诺把讨论送进旧 work；旧批准仍按原合同处理，不能把 S2 文本存入 journal 说成“先讨论后执行”已受 runtime 强制。

## 2. 已核的真实调用路径与扩展 owner

|现有路径|当前事实|S2 在该处的最小变化|
|---|---|---|
|`cli.py → tasks.plan → reference.task_plan → _task_operation('approval','inspect-plan')`|Linux；选择 registration 指定 `.venv/bin/python -P`，通过 PYTHONPATH 加载本包和原 native；不是应用解释器任意替代。|最小 CLI 的 source 动作仍进 `tasks`，沿同一个 approval component，不新建 design server／控制进程族。|
|`reference_task_approval.main → _plan → _Submission.submitted / lookup_run`|先验证原 creation／submission、run memo 和完整 history，再核原 plan envelope、receipt canonical SHA 与 artifact raw SHA；只允许当前 pending plan 的在线 inspection。|首次建立 source anchor 复用这一真实检查；网络观察在 control DB 事务外。已建立 source journal 的读回／恢复不重新查询服务。|
|`_read_design → _Creation.safe_path / adapter.read_raw`|native 读取安全、有界的 packet／source 事实，先排重复 source ID。`task_design.inspect_packet` 无身份权威。|新完整 packet 复用相同 typed ID、报告 media、绑定和知识事实检查；源链扫描、正文发布及恢复留在本 approval owner。|
|`reference.task_plan` 返回边界|应用 `contracts.StrictValidator` 校验内置 profile／packet，再运行纯检查并删掉内部 `design_read`；`task_approval('inspect-plan')` 明确转入它。|各 source 公共读写结果也必须完成应用校验再返回，不能透出新的未验证 handoff。提取必要的本地校验算法时留在 `reference.py`，不复制 validator。|
|`tasks._native_prepare → _Approval.run`|原应用短事务固定 project revision；native prepare 用非阻塞原 creation lock，网络 phase 在 DB 释放后；schema1 intent／attempt／result 在原 task-approvals 目录。|source 使用原 `_native_prepare` 的本地 revision reservation，单独的 source-kind 分支留原 approval 模块；不套 `_decision_prepare` 来冒充 owner 决定，不发送 signal。|
|`_Creation.published / _Submission.submitted`|离线也要求完整原 creation、当前 registration SHA／四投影、原 submission 与固定 run。|S2 保留这些恢复前置，不以当前 head 补写旧身份；跨登记迁移归 F。当前指定安装缺失时，原 `tasks._project/_task_operation` 会拒绝；本片的“离线”指无 Temporal 网络，不宣称脱离该解释器／原文件即可恢复。|

`_Approval.actor()` 的 `unix:<uid>:<getpass>` 仅是进程操作者。S2 可复用该事实值，不复用其 schema1 `principal_type:'human'`／`role:'owner'`。当前同 UID 安装没有自然人认证；来源记录的 assurance 固定为 `local-process-only`，可信动作保持 `human_channel_unavailable`。

## 3. 同一 journal 的最小格式与原件身份

### 3.1 路径、版本与 anchor

继续使用：

```text
ergora/task-approvals/<task>/<operation_id>.intent.json
                                           .result.json
artifacts/<task>/design/<raw_body_sha256>/body.<fixed_media_suffix>
artifacts/<task>/design/<packet_content_sha256>/packet.json
```

source **没有 `.attempt`、没有新的 head/current 文件**。`operation_id` 继续用原 `core.slug` 的文件名集合／长度；typed packet、Q/K/source/response ID 继续用 task-design schema 的集合，不能把含 `:/` 的 typed ID 当路径。source 与旧 approve 共用 operation 命名空间：任何相同 ID 的 schema／kind／正文冲突都在写入前拒绝，不换后缀绕过。schema1 逐原合同读取；只把显式 `schema_version:2, kind:'task-design-source-operation'` 识别为 source intent。

GET 从原 `_plan` 事实派生一个**不落盘**的 `source_anchor_sha256`，其 canonical 对象固定 `kind/schema_version`、task／creation SHA／submission SHA、workflow／run、seed receipt SHA、seed job SHA、seed packet canonical SHA 和包内 source-storage 资源的 `source_storage_contract_sha256`。后者是固定协议资源身份，与首条提交可收紧的有效 `source_storage_profile_sha256` 分列，因此选择较小限额不要求 GET 先写另一个anchor。anchor 不包含自身 SHA，seed packet 不反向包含 receipt SHA，无摘要循环。首次 source intent 保存这份 anchor 对象和原 seed packet／receipt／job 身份，后续 intent 精确引用它；不能只存一句 `validated:true`。

`parent_record_sha256` 的首值为该 anchor SHA，后续值为上一条 committed result 的 canonical SHA。无 source 时没有“初始化操作”或空 journal 写入。初始 packet 可以是 a1 已声明的 revision r：S2 只从精确 seed 开始验证本地后继，不伪称检查了 seed 的 r 之前链；首个新 packet 必须是 r＋1 且 previous 为 seed packet SHA。

### 3.2 Intent 与 result

新 schema 放在拟 `data/schemas/task-design-source-v1.json`，它是 source 协议资源 v1，持久 intent 判别仍为 schema2；不改变已发布的 `task-design-v1.json`。应用对 packet 和 response 分别复用原 schema／`$defs`，封闭 source transport 字段；不要复制整份 packet schema或在 native 造 validator。

|部分|拟保存的最小字段／关系|
|---|---|
|原任务 binding|复用 `_Submission.expected` 的原 control-home、project、registration SHA、execution、task、creation SHA、spec SHA、workflow；覆盖 source 自己的 schema／operation 判别，另固定原 submission intent SHA、run ID、anchor 对象或其已保存引用。原 project revision 留在 intent，不随恢复重写。|
|操作 binding|`operation_id`、`operation:'publish-design'|'record-response'`、`parent_record_sha256`、单调 `material_revision`、`source_storage_profile_sha256`、原用户提交的 canonical 内容身份。virtual seed 的 material revision 为 1，每条 source commit 加 1；packet revision 只在 publish 增加，response 不增加 packet revision。|
|记录事实|服务端取得的 `recorded_actor:{id,assurance:'local-process-only'}` 与一次性的 `recorded_at`。客户端不能提交 recorded actor、role、principal、attestation 或 server 时间来覆盖它。`authored_by` 只是 response 声称的作者，必须原样标为 reported metadata。|
|完整提交|publish 的完整 packet 对象，或构造后的完整 response；正文清单中保存每件 `path/raw_sha256/bytes/media_type/text`，包含所有本次要发布的 UTF-8 原字节。恢复只依此完整 intent，不重新读最初 `--body-file`，不重新下载资料／生成报告。|
|commit result|确定性对象：`schema_version:2, kind:'task-design-source-commit', operation_id, intent_sha256, parent_record_sha256, material_revision`。由 intent 和已验证正文重新计算后必须相同。其 SHA 是下一条 parent；不在对象内存自身 SHA，不另存 mutable ready。|

完整正文在 intent 中的副本是**同 ID 中断恢复所需原件**，不替代 artifacts 中的完整来源；读时仍核 artifacts 实际字节。存摘要、临时本地路径或只能重跑模型取得的正文均不满足恢复合同。result 缺失的 intent／正文不进入 committed 当前视图；可作为精确 pending 操作显示。

外层 `expected_revision` 校验调用者当前控制项目 revision；恢复保留原 intent 内的出生 revision／actor／正文。原 registration 或 creation 漂移就 blocked，不把当前 project、binding、packet owner 或新的 S1 policy写进旧记录。相同 ID 重提先对原用户提交比较，不能把新 server 时间当成“不同内容”，也不能因已有 result 而忽略其正文损坏。

### 3.3 两种操作的领域约束

`publish-design` 提交完整新 packet；固定 task/request/profile/admission/manifest/seed job/design-profile 身份与 seed 的声明 owner，不把“改 owner”的文字当身份升级。保留原 work-unit 映射检查。revision／previous 依据当前 committed packet，不能依据 mtime、客户端 ready 或未提交 intent。任何实际冻结 spec/composition 执行字段不被本操作重写；需要改原任务的说明仅作为讨论保留，真实变更走 F/J 的 `requires_new_task` 合同，S2 不声称理解自由文本即可检测全部执行变化。

`record-response` 构造原 `$defs/response`：target packet SHA 必须是当前 committed packet；question IDs、choice IDs、source refs 都必须存在于该 packet／目标问题。`exact_text_ref` 由正文实际字节导出，`recorded_by/recorded_at` 由服务端填入。为满足原 response 的 typed ID 合同，`recorded_by` 用服务端 `unix:<uid>`；完整不受 ID 字符集限制的 `_Approval.actor()` 字符串另留 intent 的 recorded_actor，二者都不认证自然人。只允许 `origin:'agent'|'reported-human'`；`owner-channel` 或任何可信 actor 请求在 intent 前返回 unavailable。`supersedes_response_id` 可空；非空须指本链同 packet／同目标题的既存 response，不覆盖旧原文。response ID 在整个本链唯一；重复使用不能把旧 ID 换一份答案。

response 不修改 packet 的 questions／knowledge 状态，不生成 resolution，不跨 packet 自动继承回答；旧答复、被 supersede 的原文与旧 packet 保持可读。新资料应通过完整 publish 的 `source_records` 保存，response `source_refs` 引该 packet 的原件；不增加第三种“隐式补知识”mutation。完整来源满足供给条件时，纯 inspector 可显示 supplied facts，但 owner 处理仍 unavailable、`ready:false`。

## 4. 正文、media、安全 I/O 与容量

最小 CLI 的 `--body-file` 是一个完整 UTF-8 JSON source submission 包：publish 包含 `packet` 和 full source 对应的 `bodies[]`；respond 包含客户端可写 response 字段及 exact text。JSON 字符串解码后再 UTF-8 编码定义正文原字节，保留 CRLF、Unicode 和尾换行，不 trim／规范化／转 Markdown。此 JSON 包的排版不是 packet 的内容身份；packet 落盘采用原 canonical JSON 加换行，单列其实际 raw SHA 与 canonical packet SHA。

publish 的每个 `access:'full'` source 必须随包提供正文，且声明 SHA／bytes／media 与之完全相同；`reference_only` 保留 reference、body 为 null，不进行网络或任意宿主文件读取。媒体沿 a1：`text/plain`、`text/markdown`、`text/html`、`application/json`；report_ref 必须 full/report/Markdown，html_ref 必须 full/report/HTML。response 原文先只接受 plain／Markdown，不把 JSON／HTML 的外观当成原人类答复。HTML仅返回原文／导出，本片无浏览器执行。

正文清单先排 source ID 重复、body path 冲突及遗漏，再读／写正文；typed ID 与正文路径分离。服务端只接受上述按 task、raw SHA 和固定媒体后缀派生的 managed 路径，拒绝客户端把原 receipt、旧 artifact、别的 task 或 journal 作为输出目标。相同正文／media 可共用一次 body 清单项，禁止相同 key 不同字节。packet 引用这些既定内容路径后才求 canonical SHA，packet 不含自身文件地址，避免循环。

原 `safe_file/_Creation.safe_path/read_raw/document` 继续拥有可信根、规范相对路径、非 symlink/reparse、普通文件、no-follow 和有界 UTF-8 读取；不存在的源、权限不足、摘要／长度漂移给具体 source ID，不截断。source 私有 raw publisher 仅因原 `publish/core.write` **只接受 JSON**而必要：在同目录临时写准确 bytes、flush/fsync、link 到不可变目标，已存在时有界读并逐字节比较；异常清理只清理本次临时件。留原 approval owner，不修改283参考的 publisher／Executor.artifact，也不抽通用 blob service。

拟新增最终的 source-storage 资源 `data/design-profiles/design-source-storage-v1.json`，真实消费者为应用输入／输出边界与 native source owner。它只规定存取容量，不是 design-policy、runtime profile 或临时 v12：原 a1 profile 不改字节。建议默认 `artifact_bytes=262144, inspection_bytes=1048576, operations=64, packet_revisions=32, intent_bytes=4194304, journal_bytes=16777216`。首次 submission 可显式给更小的 `storage_limits`，只能逐项收紧包内上限；缺省用上述资源，完整有效 profile／SHA 固定进首个 intent，后继操作不得提高或更换。硬安全界为 artifact≤262144、公开结果≤1048576、operation≤128、packet revision≤原a1 profile实际上限、intent≤原 `_INTENT_LIMIT` 的16MiB、扫描journal≤64MiB；native在读取可变profile前也保留这些实际IO硬界。profile各限额须为有限正整数，能容纳原seed和至少一条完整source操作；实际 prospective size 决定是否可写，不能按默认之间的倍数假定一定装得下。合法较小配置必须按实际关系工作；不能用测试把默认数值钉死为业务逻辑。

`journal_bytes` 对读取到的该任务 schema2 intent/result 实际原字节累计计数，包含 pending，防止先读无界目录再检查；operation 数量包含未提交尾部。每件正文、每份完整 intent、packet revision 和完整公开结果分别核对应上限。commit 前构造加入本次记录后的**完整**源链读回，并按原 `check_size` 的 UTF-8 JSON 编码计算 aggregate（与 `task plan` 原 seed materials 同返时也计入）；超限在 intent 前失败。不能截断正文、自动删历史、只返回前 N 条却称完整，或先 commit 一条永远读不出的 revision；当前限额不足时明确拆新任务。分页／大文件窗口是后继交互需求，不偷接本片授权。

为可恢复提交宣称持久时，在实际 source write use site 同步并重读**同一现存普通文件**与相关父目录：正文及其目录先确认，再发布 result，最后确认原 result 与父目录；新建目录也确认父项。原 publisher 只 fsync 临时文件，不能据此声称 link 已持久。fsync/重读失败不回报 durable，保留同 ID unknown／可恢复事实，不覆盖冲突文件。GET 不 fsync或补件；“已观察完整 result”与“此写调用已确认持久”分列，读请求不根据旧 JSON 布尔证明持久。

## 5. 唯一链、pending 尾部与 GET 无写

只枚举已知该 task 的受限 `task-approvals` 目录；先限条目数／文件大小，再以 schema／kind 分辨 source 和原 schema1 approval。新 reader 不重解释 schema1 的批准语义；不支持的持久版本、source orphan result／attempt、缺 intent、损坏 result 或 body 都显示带路径／ID 的 blocked／unknown，不跳过后取“最新正常件”。

从 anchor 起按 `material_revision` 和 parent SHA 重建唯一 committed 链，同时核每个 result→intent→body、原任务 binding、packet revision/previous、response 引用。链长、总 raw bytes、公开结果在各自配置内；同序号分叉、缺 parent、多个根、环或重复 response ID 均不能靠排序 mtime、改文件、选择较大 revision 修复。`source_chain_sha256` 仅指该 committed tail result SHA；它不是 J 的 `materials_sha256`、a1 的 `inspection_sha256` 或批准 binding。

本地 source intent 准备之后、result 之前占住其唯一 parent／下一序号；未完成尾部只允许同 ID／同 intent 恢复。其他新 operation 返回现有 pending ID／SHA，不能抢相同 parent 另立分支；不添加 abandon／自动废弃动作。已 commit 的同 ID 即使后来又有新 tail，重提仍核原件后返回自己的历史结果。新不同 ID 使用旧 parent 则拒绝，要求读当前链后显式重提。

所有 mutation 复用原 task creation lock；source 与原 approval 串行但 **S2 不给 schema1 approve 增加 seal**。旧 approve 和 source 可能先后发生，来源提交不改变旧 receipt／run；明确展示这种 inspection-only 限度，J 才增加有权 prepared seal／废弃语义。

GET 不调用会以 `a+b` 打开的现 `file_lock`。有 source 时以 no-follow／O_RDONLY 打开该任务**已经存在的原 creation lock**，核普通文件及 fd/path 的 dev/inode，再取得同一 inode 上的共享读锁，期间有界读取一致前缀；不新建锁路径、不落空 intent、不恢复 pending、不发布 body/result、不发送 signal。source本地GET不查询服务；原 `task plan` 的在线查询仍按原合同。这个 Linux 本地读锁算法留 approval owner；其必要性是“稳定链读取且无 GET 文件创建”，不是新的锁族。原锁缺失／不普通／读取期间被替换则明确 blocked。超时／锁忙只报告读不可用，不隐式 mutation；读取时不持 control DB 事务。

无 packet 的 `tasks.plan` 仍原样返回且不检查 source 目录；显式 source 操作在无 packet 时在 intent／正文前失败。`source operation` GET 对未知 ID 只给 not_recorded，不建立 journal。整个 state/config 树的文件名与字节快照应相同，不能只用 signal=0 声称 GET 无写。

## 6. Mutation／同 ID resume 的具体顺序

1. **应用校验和首次 seed 观察。** `tasks` 校验 transport、operation ID、run／seed／parent SHA、原 UTF-8 内容、完整 packet／response schema及容量。尚无 anchor 时，在 DB 事务外沿真实 `reference.task_plan → native main → _plan` 取得原 history／seed；应用完成 a1 schema／领域校验，再进入 local prepare。不能让 `_native_prepare` 持 SQLite 等网络，也不把 service 叶替身当成产品旁路。
2. **短 revision reservation＋原锁。** `tasks._native_prepare` 保留原 project revision；native source prepare 非阻塞取 creation lock，调用原 `_Submission.submitted`，从原 request envelope／receipt／artifact重读并核同一 seed／原件。仅接受匹配的完整 preflight事实，不接受 validated 标志；两段之间字节漂移拒绝。这里核本地不可变身份，不把先前 observed phase 假称为与 Temporal 的原子事务。
3. **先处理原 ID 与尾部。** 已有 intent 就核种类、原 binding、parent、原正文及 actor；same bytes 返回其真实状态，不重建时间／身份。新 ID 必须在唯一链当前 tail，且没有其他 pending。先完成 prospective aggregate／字段检查，再写含完整正文的唯一 schema2 intent；此时不写 result，也无外部副作用。
4. **释放 DB 后提交正文。** native commit/resume 再取原 creation lock，验证 intent SHA、原 registration／creation／submission／anchor、唯一 parent／pending 归属，依据 intent 发布或逐字节确认同一正文和 packet；不从当前配置／本地 body-file 重算任何材料。只进行 bounded local IO，没有 signal、stage/model、预算 authorization 或 clock 更新。
5. **result 最后。** 全部正文、结构及读回身份同一后发布确定性 result，并确认文件及目录持久性；返回 committed。after-intent、部分正文后、result 前、中断于 result 可见后，都从同一 operation／intent SHA继续；GET 只描述。result 已有也要核所有原件，不能像普通 source 成功的早退假设一样跳过未确认尾部。
6. **身份／依赖漂移。** resume 保留原 recorder；当前进程身份不同则 blocked，不替换 original actor。原安装／登记／seed原件损坏或缺失明确说明；缺失的**本操作 managed body**可由同 intent 在显式 resume 重建准确字节，已有不同字节拒绝。恢复不修原 plan／registration、不开新 run、不续预算、不换 operation ID。离线读历史不重算旧 freshness／已声明观察时间。

已建立 anchor 后，source 的后继读写／恢复依原 journal 和本地原件，不需要活跃 SDK连接；不因为旧 workflow 已经前进就丢失同 ID source 恢复能力。native `main` 必须显式区分source本地读／prepare／commit与首次在线inspection，前者不调用 `environment()` 或连接服务；SDK异常类和原所选解释器可用性仍是现安装前置。它们报告 `runtime_status:'not_queried'`，不声称 run 仍 pending。若产品以后要求“旧 run 已开始就禁止任何讨论归档”，需要独立的实际消费者／并发合同；不能在 S2 隐式加一套 runtime phase 状态机。原 plan 在线 inspection 的 phase 要求保持。

## 7. 真正的读消费者与最小 CLI

拟在 `tasks.py` 增加局部 source 用例，名称可为 `design`、`publish_design`、`record_design_response`、`design_operation`、`resume_design_operation`。它们接受已经读完的完整对象，不从领域函数读取任意 CLI 路径；CLI 只用 bytes→UTF-8 JSON 解析 `--body-file`。有害的非有限数、不可编码文本和未知字段在原应用边界拒绝；原 schema／`contracts` 继续是完整结构校验的单一 owner。

```text
ergora task design inspect <project> <task> --run-id R --plan-sha256 S
ergora task design publish <project> <task> --operation-id O --revision P \
  --run-id R --plan-sha256 S --parent-record-sha256 H --body-file publish.json
ergora task design respond <project> <task> --operation-id O --revision P \
  --run-id R --plan-sha256 S --parent-record-sha256 H --body-file response.json
ergora task design operation <project> <task> <operation_id>
ergora task design resume <project> <task> <operation_id> --revision P --intent-sha256 I
```

这些是来源存取命令，不加假的 owner confirm／human 开关。正式 `task approve` 的原确认和 schema1 合同不变；source CLI 输出始终包含 inspection-only／无 runtime 效果。网络只用于首次 seed inspection，timeout 沿原1–60秒；source本地阶段超时返回原 ID，不自动重试。resume 不收新的 body-file。

统一公开视图追加 `design.source_journal:{anchor, storage_profile, status, material_revision, source_chain_sha256, records[], pending[], current_packet, responses[], bodies[]}`。body 表按内容身份去重返回**完整 text**和原 SHA／bytes／media；records 指向同一表，不能只给摘要／路径冒充读全文。每个 packet 历史和 response 都可据记录定位；当前 packet 的 a1 inspection与 seed inspection分列，原 `design.packet`／seed materials 含义保留。本地 journal parent 链已经检查与 seed 更早 packet 链未检查分别展示，不把后者的 assurance 翻为 true。当前视图不接受 response 作为 readiness 输入，capabilities 的 approve_design／resolve_questions／execute 继续 false，actor assurance 明确 unavailable。

`tasks.plan` 在原有 a1 返回内附上同一源链视图；`tasks.design` 在已存在 anchor 时可离线返回它，未建立时沿原 a1 在线路径取得 seed 和可提交 parent，仍不落盘。所有 source mutation、operation GET 和这两个 reader 的 `reference` 公共入口共用应用校验，最终都移除内部 source/design handoff。尤其不要重犯 a1 的“`task_plan`校验了、`task_approval(inspect-*)`却绕过”的公开 callable 问题。

本片不扩 HTTP／console。后继只把同一 `tasks` 用例搬到原 route／dialog；没有前端 head、第二套 ready 或客户端身份。纯 CLI JSON 读回就是本片实际生产消费者，不把未实施页面／G1/G2写成已有 caller。

## 8. 拟影响文件与新增接口的必要性

|文件／原函数|拟变化及真实调用者|现成接口／维护性边界|
|---|---|---|
|`reference_task_approval.py` 的 `_plan/_read_design/main`|同模块内局部 source 准备、commit／status／链读取及 raw publisher；`_plan` 与 source inspection 共用源读算法。|原 `_Submission/_Creation`、creation lock、safe IO、canonical SHA。不要重构 schema1 `_Approval`、抽 journal 基类或加 source 控制器类；私有链算法与 raw publisher 有必要的 IO／恢复职责，单 caller 也留本 owner。|
|`reference.py` 的 `task_plan/task_approval/_task_operation`|新 source-kind 操作仍通过 approval component；公共结果在应用完整校验；source只读错误分类和本地／在线区别准确。|复用原所选解释器和 a1 校验；必要共享校验算法留本文件，不新建只转发一次的 service。读写双方不假设 native有 jsonschema。|
|`tasks.py` 的 `_native_prepare` 邻接用例|增加上节的 source 用例；DB 外首次 inspection，事务内仅本地非阻塞准备，DB 后 commit。|CLI 是现在的真实生产 caller；未来 HTTP只是计划，不能用它凑复用数。source 本地持久语义归 native，不进 State tasks表。|
|`cli.py` 的 task parser／dispatch|`design` 子组、完整 body-file、稳定 operation和原 intent resume。|调用同 `tasks`，不判断当前有效 owner／选 head，不复制领域检查。|
|新 `data/schemas/task-design-source-v1.json`／`data/design-profiles/design-source-storage-v1.json`|真实 source transport／持久格式与容量资源，应用和 native分别消费各自职责。|配置接口以角色评估，无需虚构第三个 caller。原 task-design schema／a1 profile只读复用，不增加运行profile／queue。|
|`tests/test_task_plan.py`／`tests/test_task_approval.py` 及必要原 fixture|扩下面的真实边界反例。|原测试文件已在 CI；不新开重复 job。只在跨进程叶注入故障，保留 main／owner／原文件链；不以 helper-only 代替。|
|既有任务手册及本片交付（实施时）|写清命令、原件语义、限额和 unavailable；更新主控 PLAN。|本轮唯一写本 proposal，不提前写“已实现”。|

纯 `task_design.inspect_packet` 原规则可不改；后继 J 有真正多 owner 消费者时再增加权威 readiness／materials identity，S2 不先造空 API。`registrations/state/task_envelopes/reference_inputs/workflows/executor/job_lifecycle/processes/web/console` 均不属于本片源码落点；若实施必须修改它们，先指出 S2 的具体可达遗漏，不能夹带 F/J/G。

## 9. 最小验收反例与实际跨进程接缝

下面均为**待执行**。先在旧产品重现真正可达失败，再在新固定候选检查受影响接缝；不为每字段复制同义矩阵，也不为本设计文档运行产品测试。

|风险／最小场景|必须观察的结果|最小真实接缝／限制|
|---|---|---|
|完整两轮＋答复|同一旧任务的 seed→publish r＋1→reported-human response→publish r＋2→agent response；完整 Markdown／可选 HTML、来源和两份原回答逐字节同一，parent/sequence与 packet revision分别正确；所有 Q 的 owner处理仍未决、ready/执行能力false。|扩 `test_task_plan.py` 原 pending packet和真实 submitted creation；真实 `tasks` publish／CLI respond 后，用新 `State`／新进程离线读回，再由在线 `tasks.plan` 读同链。关闭 service叶后离线read/operation/resume仍不connect。|
|intent 不含全文的恢复漏洞|在 intent 后、第一件正文后、result前分别中断；原 body-file删除或改字节；同 ID＋原 intent resume仍发布原完整内容，旧 parent占用，不产生 signal/attempt。|`test_task_approval.py` 的 journal 中断风格，故障仅注入新发布叶；至少一个“正文后/result前”用实际子进程退出，不只在helper上返回 prepared。|
|同 ID／分叉／旧批准命名冲突|same ID同内容返回原记录；变正文、kind、run、seed或parent拒绝；两个新 operation争同parent只有一个intent尾部，另一个明确指向其ID；与schema1同ID互拒且旧字节不变。|原并发 fixture与真实共享filesystem／creation lock；一个新进程做resume，另一个读/提交。独立 project的写不被网络等待占DB阻塞。|
|GET偷偷恢复／写锁|有pending／损坏正文时，`design inspect/operation`与原plan读取均不补件、不创建lock/intent/result、无signal；随后显式resume才补原件。|读取前后 state/config全文件名与字节快照；锁文件预先存在并检查只读打开。记录native child行为，不能只测 `read_only:true`。|
|不完整提交被当current／损坏链|未commit正文不改变tail；orphan result、缺parent／同序号分叉、错误intentSHA、已commit正文换字节或缺件，精确blocked，不跳到旧“正常”head。|对原落盘记录做最小授权fixture变形，沿实际公开reader读回；一个损坏场景覆盖完整chain约束，不堆仅检查报错字符串的测试。|
|media／ID／路径／容量静默错误|重复source ID在IO前拒绝；report不是Markdown、非法target、symlink/nonregular、无效UTF8、错SHA/bytes不能留下source intent；response的owner-channel/未知Q也在intent前拒绝。M−1/M完整返回，M＋1明确失败；aggregate满后新mutation零增量。|复用a1已有反例保护，新增只测source write可达的新失败。用至少一份较小非默认合法storage配置检查关系，分别核artifact/intent/journal/公开结果预算，不只锁默认常量。|
|native依赖被应用schema污染|真实 `tasks→reference→registration所选解释器→main→_Submission/_plan/source→safe files→应用schema` 全链可用；合法source全文返回，无效typed packet／response仍由应用拒绝，内部handoff不泄露。|扩现 `test_application_task_plan_uses_selected_native_python_without_jsonschema`：保留实际main及原文件链，仅替换 `connection.connect`／故障发布叶；所选解释器 `-B -S` 禁止jsonschema。原approval fixture会整段替main argv，只能保旧恢复，不能代验本项。|
|持久确认中断|正文目录确认后／result目录确认前失败，调用不能报告durable；GET不fsync；同IDresume确认同inode/原字节后成功，无第二result/head。|注入准确fsync/重读失败并核实际文件；测试只认证该本地确认算法，不冒称机器断电或跨文件系统容灾已验。|
|旧合同／无额外执行|无packet返回、普通schema1 exact-owner／attempt后unknown只对账原计数不变；source全程approvals／fences／task spec／creation／原budget clock字节不变，stage/model/可信命令starts=0。|沿既有 plan无packet＋approval两个关键原用例，以及本片场景的文件／调用计数；不因S2重跑无变化训练／GPU或全库。|

SDK fixture、受保护通道替身、真实服务和自然人验收分别记账。上述跨进程例保护的是 launcher／依赖／原件链和本地恢复，不是 Temporal生产服务或人类通道。当前同 UID 的可验结果只有原文保存、进程来源及 unavailable，不能由测试 JSON／model approve关闭该限制。

## 10. 明确留给 F／J／G 的责任

|后继|本片不偷做的合同|
|---|---|
|F|最终 definition8／input12出生、冻结项目与模板policy/owner／applicability、初始packet正式生产、work传播；原 marker／四投影迁移、旧registration历史选择、旧creation/prepare/submission跨登记恢复、外部根一致回退。S2只保原前置，不补迁移豁免。|
|J|可信owner channel、逐ID resolution/waiver/假设／降低要求；完整权威materials SHA；approve prepared seal／显式request-revision废弃；reject/withdraw固定子cancel、原fence持久及停止尾部。S2 source_chain SHA不冒名上述绑定，reported-human不升级。|
|G|真正G1 authorize取原plan envelope的冻结policy；G2 adapter／executor preclaim／最后Popen短锁、work/review完整材料及saved formal-call恢复；原预算和实际回收。S2不注册新Workflow／adapter／queue，不产生新的runtime效果。|
|后继交互／部署|HTTP／页面同用例、受保护owner实际权限隔离、真实人类小旅程；可信脚本节点、一般Repeat／混合画布仍按D4之后顺序。|

本稿已对必要技术选项给保守建议：完整intent保正文；pending占原parent；GET只读原锁；CLI先交付；旧schema1审批不受source影响；缺安装／登记漂移不猜fallback。它们是落实已审约束的具体 proposal，交fresh设计审确认，不是新增产品授权或要求用户重答D1–D4。若审查发现存取边界必须改变旧批准／持久格式职责，应收回到正确后继片，不临时开启“半个”J/G。

## 11. 实施、安装与审查检查清单

- [ ] Fresh设计审先核本稿的实际owner、完整intent恢复、pending唯一链、只读锁和容量关系；两轴结论独立记录。本稿不能自标“已审”。
- [ ] 在准确隔离源码基线实现最小source schema/resource＋原owner＋真实tasks/CLI/read consumer；列tracked/untracked完整差异，不碰原参考、锁、环境或其他产品片。
- [ ] 固定新候选，执行第9节最小受影响原接缝，保存原红例／修后结果和未跑范围；核源码／配置前后身份，停止扩大已通过且未变的测试。
- [ ] 构建新的非editable wheel；分别安装core／SDK到任务自有持久检查目录，核site-packages真实导入、完整包资源与依赖同一、283参考及原127项锁不变。core无SDK的公开拒绝／schema校验与SDK选定native边界分别记录；不让 `-I` 子进程偷偷导入主树editable。
- [ ] 同一新安装沿真实CLI提交、丢回复／正文后中断、新进程离线read/resume和应用返回校验复验；所选native不临时安装jsonschema。不把源码hook测试或前代wheel的绿转授新包。
- [ ] 依仓库规则保存自身原结构模板的完整输入／实际后端／原回复，再交新的fresh源码需求与维护性审；修有证finding后复核。模板和代码审不认证自然人／G1/G2。
- [ ] 主控更新PLAN及本片交付，列S1的最终集成版本、未完成F/J/G、原安装可用性／原registration恢复限制。普通整合／发布、候选自身CI单独认证；未验不提前写完成。

## 12. 本轮实际工作与 fresh 审交接

本轮只读根／src／tests AGENTS、PLAN、组件协议、`maintainable-project-delivery`及 independent-review、上述D1–D4／详设／拆片／a1与S1交付，以及实际 `tasks/reference/approval/creation/submission/task_design`、原safe IO／lock、schema／CLI和测试fixture。仅运行读取、轻量Git、SHA和本文件静态检查；**没有跑产品tests、安装、服务、模型、网络、训练或GPU，没有读凭据／环境快照，没有改源码／环境／PLAN，没有commit/push。** 唯一写入为本文件；它没有自身验收证据路径，后继实施再建项目内交付／持久原件账本。

交主控发fresh设计审时附：原始任务范围、D1–D4、已审拆片及WA5详设、准确 `c540939d` src/tests身份、本稿完整原文和最终SHA、必要实际调用／fixture路径、仅静态阅读的事实，以及明确授权的独立设计审报告路径。重点反证“恢复必须重读body-file”“GET用a+b开锁”“同parent pending被新ID绕过”“公开source callable绕应用schema”“source链被误当权威materials”“schema1旧批准被悄悄seal”六类错误。后继开始实现前重核实际HEAD与S1状态，不把本稿或全局新安装通过当本片通过。
