# WA5-S2：来源 journal 独立实现审查

2026-11-16。审查者：fresh-context agent `/root/design_source_journal_s2_source_review`。先读原始需求、固定 proposal、项目规则和完整变更，再沿真实消费者检查；没有继承作者或原模板的 verdict。审查中主控转来原模板的两个具体反例，本报告逐项独立回溯了实际公开调用链。唯一文档写入为本报告；另经主控单独授权，在本片私有 checks 下保存一个原安装候选的局部反例。

|审查轴|本轮结论|开放项|
|---|---|---|
|需求符合性|**request-changes**|3 项 P1。公开 source 调用可以改变 native 路由、首次 anchor 可以依赖伪造 preflight、版本化任务错误读取旧 requests root。|
|可维护性|**request-changes**|同三项分别越过传输入口、在线事实取得和 `WorkflowInput` 构造 owner；均有局部修正，不需要新服务、状态库或通用抽象。|

本结论只针对下面的固定 r1 候选。尚未审查或认证后继修正版；既有源码／安装通过不能关闭这些反例，也不能开放 F/J/G、可信人类批准或可执行 v12。

## 固定输入、范围与身份

|项目|实际核对|
|---|---|
|项目与只读源码树|项目根自己的 `docs/`；源码为 `.ergora/worktrees/design-source-journal-s2-r1`，分支 `feat/design-source-journal-s2-r1`。开始、收尾均 clean，HEAD `7592ed3628fdd476e3b8fd1680c05fe5391519cc`。主树同时存在其他 owner 的文档修改，未处理它们。|
|基线与完整差异|`7fc42177db11fbfe4c9adb33342ecb5da4ed0434..7592ed3628fdd476e3b8fd1680c05fe5391519cc`：7 文件，1969 insertions／19 deletions。逐字读取全部变更，包括两份新资源。`package-r1/source.patch` SHA256 `d232b86a785ee38532ceb5a45d83531a0d2cdcc485b12f079da61b49e75e9357` 已重核。|
|完整冻结 inventory|独立重算 `package-r1/frozen-inputs.json` 列出的全部 2107 个 tracked 文件字节、SHA、执行位：与只读树一致，差异 0。没有遗漏 untracked 产品文件。|
|原始需求|完整原 proposal 为 `design-review-r1/proposal.md`，197 行，SHA256 `fdf2c8a8bebac116a0b1a56556a4fcc1f3493e3fd93c2b2c1f3f87d65c185c0e` 已重核；同时读当前 [proposal](../plans/2026-11-16-design-source-journal-s2.md)、[独立设计审](2026-11-16-design-source-journal-s2-design-review.md)、[拆片的 S2／第 4–5 节](../plans/2026-11-16-design-gates-registration-and-journal.md)、完整[详细设计](../plans/2026-11-16-design-knowledge-gates.md)和 [D1–D4](2026-11-16-workflow-design-decisions.md)。|
|项目规则与质量依据|根、`src/ergora`、tests AGENTS；当前 PLAN／本片 delivery；组件变更协议、实际 pyproject 包资源／依赖／pytest 配置；`maintainable-project-delivery` 的 independent-review 与 `ergora-codebase-quality` 的 module-design／test-seams／repository-style。|

完整七路径：`reference_task_approval.py`、`reference.py`、`tasks.py`、`cli.py`、`data/design-profiles/design-source-storage-v1.json`、`data/schemas/task-design-source-v1.json`、`tests/test_task_plan.py`。相邻实际消费者包括 `_Submission` 的原 creation／registration／submission／run 绑定，`_Creation` 的 `safe_path/document/file_adapter/check_size/published`，原 adapter 的路径／有界 no-follow 读取／canonical publisher，`WorkflowInput` 的 factory／request root／adapter，`CompositionDevelopmentWorkflow.context`，`task_envelopes` 与 `task_design.inspect_packet`，原 schema／profile／contracts，以及原 plan／approval／HTTP 调用和相关 fixture。未改原参考、锁、State、definition、runtime 输入、预算、服务或其他产品文件。

以下行号均属于上述固定 r1 源码，而不是主树后来文档提交的行号。

## 阻断 findings

### F1／P1：source payload 可以把只读 source 调用改派成旧批准 dispatch

位置：`src/ergora/reference.py:883–899`，实际传输 `1003–1006`；消费者为 `reference_task_approval.py:899–904` 和 `_Approval.dispatch:826–843`。

`task_design_source(..., 'source-status', payload)` 没有关闭 payload 字段集合。`_task_operation` 先填 `project/control_home/operation/timeout`，随后展开 `**payload`，因此调用者传入的 `operation` 会覆盖参数所选动作。可达例子是 source-status payload 带 `operation:'dispatch'`、原 `decision_id` 和有效旧 `intent_sha256`：native main 进入 schema1 `_Approval`，在原 actor、期限、run、plan 条件满足时发布 owner receipt、attempt 并发送 `approve_plan`。返回的是无 `design_read` 的旧 approval 状态，`_checked_design_result` 会直接放行。

这不是绕过旧批准自身的 actor／plan 检查，但公开标作 source GET 的调用具有真实批准副作用，违反 source 不写旧 approval／attempt／signal 的硬合同。类似覆盖还涉及 `project/control_home/timeout`。CLI 正常构造的 payload 不含这些键，不能用 CLI happy path 排除直接公开 facade 的问题；`task_approval` 的 source 转发同样可达。

最小修正：在 source 公共边界按 operation 校验封闭、严格的 payload 字段，拒绝保留头字段；transport 最终写入权威的路由／project／control-home／timeout，避免数据覆盖其选择。保留原 approval owner 和旧 payload 合同，不新增另一套批准控制器。验证须在两个公共 source facade 上观察原反例在任何 native 调用／旧 intent、receipt、attempt、signal 前拒绝，并保留旧普通批准恢复正例。

### F2／P1：首次 anchor 允许调用者伪造在线 pending preflight

位置：`src/ergora/reference.py:887–899`；`reference_task_approval.py:287–310`、`632–663`。

公共 `task_design_source(..., 'source-prepare', payload)` 只校验 `payload['source']` 的结构，然后把调用者的完整 `preflight` 交给 native。`_source_seed` 检查调用者声称的 `phase:'AWAITING_PLAN_APPROVAL'`，从本地 envelope／receipt／artifact 重建 seed，并复制其 `history_plan_event_id`；此路径不做 `lookup_run/query/history`。因此调用者可从已有原件构造相同本地字段，或使用已经过时的旧 inspection，在从未完成真实在线观察／当前 run 已不再等待时创建首个 intent。正常 `tasks._publish_design_source` 会先调用 `design`，但直接两个公开 reference facade 都绕过这一步。

后续原件／SHA 自洽不能证明第一次在线观察曾发生；持久 seed 还会保存重建出的 queried／pending 声明。这违反 proposal 的首次真实 `_plan` 前置。问题不是要求所有后续离线读写重新联网；首条建立后仍应保留原离线恢复合同。

最小修正：公共 prepare 自己在控制 DB reservation 外取得并应用校验真实 source inspection，拒绝调用者提供的 preflight。正常 tasks 流程可把经过该边界取得的结果交给一个私有本地 prepare，使 `_native_prepare` 内只做非阻塞锁及本地身份重读；不能把在线查询移回 DB 事务。验证两个公共 facade 的伪造／过时 preflight 都在首条 intent 前失败，原在线路径通过，首条后的离线新操作和同 ID 恢复保持不连接服务。

### F3／P1：source seed 绕过版本化 adapter，组合任务读取错误请求目录

位置：`src/ergora/reference_task_approval.py:295`；对照同文件 `137–138`、`src/ergora/reference_task_creation.py:89–95` 和 `src/ergora/reference_inputs.py:41–42,114–130`。

`_source_seed` 把 plan envelope 固定读为 `creation.path('requests/<task>/<job>.json')`。原 `WorkflowInput` 为 input2–11 选择各自的 `requests-composition-vN`，而 `_plan_materials` 已正确通过 `creation.file_adapter(submission.input)` 取得根。因此合法组合任务可以正常在线检查原 a1 packet，首次 source prepare 却在旧 root 缺件处失败；每次已有链扫描也会再次调用 `_source_seed`。不能通过复制旧 requests 文件或降选 legacy input 来修复。

已在**原非 editable r1 SDK 安装**取得授权的局部反例：使用历史真实 input2 文档，经实际 `execution_input`、`CompositionDevelopmentWorkflow.context`、`CompositionAdapter` 和原 `_Creation.file_adapter` 构造本地证据。原 `_plan_materials` 及应用 packet/schema 检查通过，正确 versioned 文件存在；随后原安装 `_source_seed` 抛 `FileNotFoundError`，路径明确落在 legacy `requests/`。失败前后 fixture 文件字节／文件名无变化。原件位于本片 checks 的 `reviewer-composition-root-r1/{probe.py,command.json,stdout.txt,stderr.txt,result.json}`；1.686 秒，runner rc0 表示成功观察预期反例，不表示 feature 通过。实际导入的 approval 模块 SHA256 `0417cb21447218732824d9292cd0167debbdb8d78264a8710955efe60b495a6f` 与 r1 同一。

最小修正：沿已有 `creation.file_adapter(submission.input).path('requests', relative)` 取得同一选定 root。补一个真正组合输入的 source 首次提交→离线读／恢复接缝，使用原 producer 的完整 context；保留 legacy 对照。当前局部反例的 submission ownership 为本地 stub，明确不认证完整 creation／submission／history／Temporal 服务；修后仍须实际应用/native 与新安装复验。

## 其余已核合同与可维护性

未发现需要另建 source 服务／journal 基类／存储框架的理由。链扫描、raw publisher、同 inode／原字节持久确认留在原 approval owner，具有具体锁和恢复职责；应用结构校验仍用原 contracts/schema，native 未加入 jsonschema。新 storage 资源由应用边界和 native owner 消费，按配置角色有必要。CLI 只解析完整 body-file 并调用 tasks，未增加 owner 身份开关或第二权威。

在已检查的实现中，schema2 intent 保存完整 submission、packet／response 和 UTF-8 bodies，result 最后发布；同 ID 比较原 actor／内容／parent／run／seed，缺 managed body 只由显式同 intent 恢复，已有冲突字节不覆盖。链按 parent 与 material revision 重建，一 pending 占尾，坏链不选择旧正常 head；schema1 与 source ID 冲突在写前拒绝。GET 使用现存 creation lock 的 O_RDONLY／共享锁、无 CREATE／fsync／补件，write 使用同原锁的排他模式。正文及相关目录、intent／result 的同 fd／raw 确认与 GET 仅观察 committed result 分开。

容量检查按有效较小 profile 工作，首次冻结完整 profile/SHA；单件 artifact、完整 intent、含 pending 的 raw journal 和完整 prospective 公共 JSON 分别有界，提交前核最终公开视图，无截断／分页／mutable head。应用在 commit/resume 前校验完整 intent inventory 对应的 submission／response，native 再于原锁内比对 inventory hash。完整正文与 original seed materials 一起计入公开结果。上述三项 finding 仍必须修复，不能由这些正确局部算法抵消。

response 只准 agent／reported-human，recorder 为 local-process-only；旧答案／历史 packet 原文保留，当前 inspector 不把响应当 resolution 或 readiness。source tail SHA 未冒名 J materials；普通 schema1 approve／cancel 的业务逻辑保持。没有新增 definition8／input12、seal、fence、clock、预算授权、model/stage 或 work 传播路径。F1 是唯一发现的可经 source facade 误入旧 signal owner 的路径，须在其真实入口关闭。

## 已有证据的独立核对与本轮实际检查

- 原源码记录的 JUnit 已逐条比对：当前收集的 **112 个唯一节点**各有 individual passing run，ledger 无缺项；不是一次 112 全套通过。r5 为 66/66；r6 为 42 pass／1 failure（原并发测试假设立即成功）；r8 为修正后该节点 1 pass；r9 为 6 pass；r11 为只读锁 fixture 更新后的 1 pass。原失败保留。重算这些运行记录内全部 672 个 src 输入的 SHA／执行位均与 r1 一致，因此生产字节未因测试预期修正改变。
- 安装原件现已终态：`package-r1/installed-source-r1.*` 为 **30 passed／454.56 秒**，JUnit 30 tests／0 failure／0 error／0 skip，runner returncode0／455.745 秒。实际记录的 1380 个采样自有进程均在 wait 后 absent。覆盖两个原 approval 接缝、CLI 原文／三实际退出恢复、pending／坏链／容量／schema／只读等选定场景；没有组合 input2 或伪造 preflight／保留路由头反例。
- wheel SHA256 `f9b5394d6eac2f99b8c347b4b95a9a15d5adb3d7ee2000f59642eb7de3cab5af` 已独立重算；core／SDK manifest 中完整 **671 个运行包文件**逐件 source↔wheel↔site-packages 的字节、SHA、执行位独立比对，差异 0。记录的 core 无 SDK／SDK1.34.0、owner imports／283参考／依赖检查保持其原安装范围，本轮没有重新安装或运行这些检查。
- 本轮自行执行的产品相关 probe 只有主控明确授权的 F3 局部 installed-r1 反例；argv、isolated／禁 bytecode／清 PYTHONPATH 的显式参数、实际模块 SHA、原始 stdout/stderr、PID／start ticks／boot／wait 后 absent 均保留在独有目录。其余为 Git／diff／原文／调用链／SHA／XML／inventory 静态检查；`git diff --check` 无输出，原只读树仍 clean。

本轮没有运行广套件、安装、模型、服务、训练、GPU、commit 或 push，没有读取凭据。S2 的真实 Temporal、真实受保护人类通道、Windows 原生支持、断电／跨文件系统耐久性、业务质量和 publication／候选自己的 CI 均未由这些证据认证。公开旧产品的 8/8 CI 不转授本候选。

三项 P1 修正后需要同片复核准确新 delta、原反例的修后结果及相应新安装身份；保留原 r1 red 和全部原通过／失败。主控负责更新 PLAN／slice delivery，并分别收尾新候选原模板、整合／发布及其自己的 CI；本报告不代替这些门槛。

## 同片 R2 源码修正复核：2ae107b

本节是原 reviewer 对修正的同片复核，保留上文 R1 request-changes 与原安装反例，不把旧结论改写成通过。新源码树 `.ergora/worktrees/design-source-journal-s2-r2`／分支 `fix/design-source-journal-s2-r2`，准确 clean HEAD `2ae107b84a3c928fc8c6e2b97820951af34c0cdb`，原 7592 树／包未变。

|审查轴|R2 源码范围结论|当前验收边界|
|---|---|---|
|需求符合性|**approve；开放源码 finding 0**|F1–F3 的实际调用缺口已关闭，准确最终 src 的 12 项定向证据已核；完整模块和新安装运行不预先判通过。|
|可维护性|**approve；开放 finding 0**|保留传输／应用 schema／tasks reservation／WorkflowInput adapter 的原 owner；没有新服务、状态、runtime 版本或通用框架。|

已全文检查 7592→2ae 的四文件 delta（`reference.py`、`reference_task_approval.py`、`tasks.py`、`test_task_plan.py`），198 insertions／27 deletions，并重新沿所有 source 公共入口、tasks prepare／resume、generic lifecycle transport、原审批 dispatch 及版本化 adapter 的实际消费者核对。`package-r2/review-fix.patch` SHA256 `0e35d8500bef0decf7658e1ca59ec44256b86dd74a6ddff5161611ccf2f412d4`，完整 7fc→2ae patch SHA256 `00db26fc3408b12f26adf224cfa7dbf48e43f6d4297b93942cbd8677be7ab56f`，均独立重算相符；`frozen-inputs.json` 的全部 2107 tracked 文件字节／SHA／执行位与新树相同。

|原 finding|实际修正与复核结论|
|---|---|
|F1／source 路由覆盖|`reference._source_request_payload` 按每个支持动作给出封闭必需字段，在任何 native 调用前拒绝路由保留头及其他未知字段。`task_design_source` 和 `task_approval` source 转发均经过此边界；private local prepare 也复用该输入检查。generic `_task_operation` 先展开 payload、最后填可信 project／home／operation／timeout，使所有原 lifecycle 调用的传输选择均不可被数据覆盖。未新增旧批准语义。两 facade 原 GET→真实旧 prepared approval dispatch 反例在旧源码实际失败，修后公开读取在 dispatch 前拒绝；其他保留头也有明确零 native 调用检查。**源码项关闭。**|
|F2／伪造首次 preflight|公共 source-prepare 不接受 preflight 字段，而先自行经同一公共 source-inspect 取得应用校验后的原 seed。已有 source 时该 inspect 仍可离线；首次仍经真实 `_plan`。tasks 在 `_native_prepare`／DB reservation 前完成 `design`，其后仅调用私有 `_prepare_design_source` 做本地校验／非阻塞 prepare；该 helper 不调用公共在线 prepare。resume 的 reservation 也使用该私有本地 helper。原 caller preflight 不能从两个 facade 进入；无 caller preflight 的首次公共 prepare 在 closed run 上确实只尝试 source-inspect 后失败，无 intent。未把 RPC 移入 DB 事务，也未增加客户端 validated 标志。**源码项关闭。**|
|F3／组合请求根|`_source_seed` 改用 `creation.file_adapter(submission.input).path('requests', relative)`，与 `_plan_materials` 取得同一版本化根；没有降级／复制 legacy requests。新 regression 复用原 `composed_creation` 的真实 agent/workflow/manifest/definition2，实际 preview/create/start，使用 `execution_input` 所选 Workflow 生产完整 context、所选 adapter 发布请求，原 main／submission／文件链与禁止 jsonschema 的 native bootstrap 保留。首次 source 提交成功，关闭 SDK connection 后离线公开 operation 读取成功，legacy 请求路径始终不存在且 GET 快照无变化。原局部 installed-r1 red 保留。**源码项关闭；新包运行另验。**|

测试变化有实际接缝必要性：原 native fixture 从手拼 legacy context 改为原 Workflow 的 context producer，并按 selected adapter 保存 envelope；新 composed fixture 隐藏的是同一原路径的版本选择，未替换 source owner／main。F1 用原 schema1 prepare 和真实 SDK signal 端口观察误派副作用，F2 用实际 closed run 而非只对 helper 输入字符串，另保留 public prepare 正向提交与字段边界。没有为了通过用例改变 storage 限额或产品行为。

实际证据复核：`impl-r2/red-boundaries-r1.*` 为旧生产字节上 **5 failed**／runner35.978秒，XML 显示两个 source GET 未拒绝 dispatch、两个 caller preflight 未拒绝，以及首次公共 prepare 实际直接调用 source-prepare 而非 source-inspect。`green-boundaries-r2` 的 7 pass 和 `composed-and-legacy-r3` 的 1 pass／2 fail 保留各自中间输入；它们的 `reference.py` 与最终 2ae 不同，不单独转授。r3 的 legacy fixture 错误 manifest 输入已修。`source-corrected-r4` 的 **12 passed**／pytest103.66秒／runner104.546秒，实际 JUnit 无 failure/error/skip，记录的全部 672 个 src 输入 SHA 与最终 2ae 完全相同，pytest wait 后 absent。

新包静态身份亦已独立核对：r2 wheel SHA256 `0d4a183149b2143e0d8ac60a27db37f969061b46cee4d5dc232b49ed97b45933`；core／SDK 各完整 671 个 runtime 文件的 source↔wheel↔site-packages 字节、SHA、执行位差异 0，core 无 SDK／SDK1.34.0。这是新安装身份的只读检查，尚未冒称已通过新安装运行。

本节写入时完整 `r2-complete-source-r5` 尚无终态 command／JUnit，123 是预期节点数；新包 runtime、原结构模板、整合／发布及自身 CI 尚待实际结果。本 reviewer 本轮只读 delta／caller／hash／现存 XML 和包文件，未重跑测试或原 R1 probe、未安装、未执行模型／服务、未编辑源码／其他文档。源项关闭不等于整片完成；未验真实 Temporal／自然人／Windows／GPU／F-J-G 的边界保持。

## R2 终态证据与本地源码／安装门收尾

同一 reviewer 在上述静态复核后独立读取新终态原件，没有重跑未变的测试、安装或模型。准确候选仍为 clean `2ae107b84a3c928fc8c6e2b97820951af34c0cdb`；原 R1 request-changes、五个边界 red、原安装 F3 反例、r3 测试输入失败均完整保留。

|门槛／原件|本轮实际核对的终态与限度|
|---|---|
|完整源码运行 `impl-r2/r2-complete-source-r5.*`|单次 **123 passed／pytest676.68秒**；JUnit123个唯一 case／0 failure／0 error／0 skip，676.652秒；runner returncode0／677.752720秒。实际 argv、src PYTHONPATH、PID／start ticks／boot 与 wait 后 absent 已核，当前该进程也 absent。记录的全部672个 src SHA／执行位独立重算与最终2ae一致。这是 task_plan＋task_approval 当前完整模块运行，不再依靠R1的分批并集。|
|新非 editable 安装 `package-r2/installed-source-r2.*`|**41 passed／pytest530.28秒**；JUnit41个唯一 case／0 failure／0 error／0 skip，530.268秒；runner returncode0／531.400806秒。实际以新SDK安装的绝对 Python `-I -B` 在复制的 test-inputs cwd 运行，PYTHONPATH移除。核到新增组合 input2、两个 public prepare 正向、两个 facade 的路由／preflight 反例、其他保留头，以及两轮全文、CLI三退出／删body-file恢复、pending／坏链／容量／只读／持久确认和两旧approval接缝。原记录1656个采样自有进程均 wait 后 absent；本轮再次按 PID／start ticks检查也全部 absent。|
|运行后输入及包身份|读取 `post-source-tests-identity.json`／`post-installed-tests-identity.json`，并再次独立重算全部2107个冻结tracked文件及core／SDK各完整671个运行包文件：source↔wheel↔site-packages字节、SHA、执行位差异0。wheel仍为 `0d4a183149b2143e0d8ac60a27db37f969061b46cee4d5dc232b49ed97b45933`，树clean。没有把构建metadata标签里的r1字样当成旧包复用。|
|原结构模板 `self-review-r2-codex/`|实际Codex，exit0／succeeded／**80.514251秒，approve**。独立核对14个完整文件／463948字节scope与候选一致，完整patch SHA同00db26…；实际保存的stdin为600478字节、SHA256 `cd37a08d951318d2c7f910de957a19651c10ffe63629cc64a7450d3ebc985f68`，包含全部14文件、完整patch和3份继承资源全文。raw result SHA256 `c5d498469e7ec97f04cbad58c5669ff88fc3908e9f3fab74eb81f9716ffae149`与summary一致，原reply确为两轴approve。该模型明确说明没有Git／文件系统工具，仅审所供全文，不能独立认证包身份或运行；本报告没有扩大其结论。|

据已审完整实现、准确修正及上述自身新运行证据，**需求符合性 approve、可维护性 approve；开放 findings 0，F1–F3 的源码及所选新安装本地接缝均关闭**。S2 的本地源码／安装／原模板／独立复核门已闭合，可进入主控的普通整合及发布流程。新增双语操作说明仍须按其准确小段delta另核语义；本结论不提前认证尚未收到的文档。

这是 Linux 本地文件／原生依赖／受控SDK connection 端口下的验收。真实Temporal部署、自然人及受保护owner权限、Windows原生、机器断电／跨文件系统容灾、训练／GPU／业务质量、F/J/G和任何schema3实际效果仍未验／未开放。S2此刻仍未合入或发布；普通整合、准确公开候选自身CI属于主控下一范围，不能继承公开旧e5的8/8。PLAN和slice delivery由主控／文档owner按实际终态更新。

## 同片双语操作说明窄增量复核

本节仅审 `docs/USAGE.md` 新增42行和 `docs/zh-CN/USAGE.md` 新增41行的 S2 操作说明；不是重新审查此前已独审的完整指南。文档 baseline／当前本地合入为 `2ff004d4c2c62c42c76928de96915b90837b54f7`；独立核该提交的 src tree 与已审 `2ae107b84a3c928fc8c6e2b97820951af34c0cdb` 同为 `f6b71a4be022d03452b52400f88d8f85259ec73e`。这只确认文档对应的源码身份，不声称公开发布或自己的CI已完成。

**需求／语义 approve，可维护性 approve；开放文档 findings 0。** 最终准确两文件 patch 冻结在 `usage-docs-r2/complete.patch`，SHA256 `eab66d8ec47ac97332f983c3bb20ad43adfd91f204cf91185d020efd48ae2fef`，与实际 tracked diff 逐字相同。当前完整 English 文件 SHA256 `047f9ad4717fada4cb7f00a890f5ad2a86c5ea4176fede40768052a1dbc4fb9b`，中文 SHA256 `cf0f5e6147e8d5f7888fcc3214ecf512a32263b66e0914c80304dd49338f1491`。去掉各自新增 section 后，两份原指南字节均与 baseline 和冻结 before 原件完全相同。

同片首轮文档有两项需收紧的 P2 表述，均已在上述准确 r2 delta 复核关闭；原 `usage-docs-r1`／patch277c0000… 保留：

- U1：仅说UTF-8／排序键／紧凑JSON不足以唯一说明非ASCII packet的SHA。已双语明确 `ensure_ascii=False`、排序键、`separators=(',', ':')`、`allow_nan=False`、UTF-8及不追加尾换行，与实际 `task_envelopes.identity`／adapter canonical 相同。
- U2：笼统“无部分成功”容易掩盖已经落下的原操作。已改为完整committed视图不截断，并明确后继I/O／fsync／确认失败可能留下pending intent或可见result而本调用未确认持久，须先查原operation、按同ID／intent SHA明确恢复，不删除／覆盖／换ID。这与已验的真实退出及result确认失败接缝一致。

逐项核对已审CLI、source schema／storage profile和实际public view：真实统一创建／已提交任务及原accepted receipt内有效packet是前置，没有默认seed producer；首次真实在线seed观察与已anchored离线读／恢复分开，仍需原所选native安装／文件。完整packet／正文descriptor／受管路径／准确原字节、完整响应形状、parent和三种revision、两轮ID／同intent恢复、body-file不再需要、pending阻断、schema1命名空间及旧work不消费讨论均与实现一致。source tail没有冒名J materials，reported-human／client metadata不产生可信owner，Q/K resolution／seal／withdraw／执行／schema3效果和服务／人类／GPU验收均未夸大。

四个新fenced block双语逐字相同，且与r1未变。读取原六条CLI示例的纯 `parse_args` 结果为6／errors[]，实际使用r2已核非editable SDK、`-I -B`；数值project revision占位符替成1并去除shell重定向，没有调用handler／source API。r2只改两处说明文字，因此未重复parser。原194个local link／UTF-8／fence检查证据保留，本轮另核旧正文不变、两新section链接／代码块未变及准确两文件diff-check，无问题。本轮只写本报告，未编辑作者文档／源码／状态，也未运行产品测试、安装、模型或服务。

至此同片双语操作说明增量也已闭合，可由主控精确提交这两份已核文档。普通推送／公开候选自身CI及实际部署仍是后继；本节不转授旧CI，也不扩大上文源码／安装的本地验收边界。
