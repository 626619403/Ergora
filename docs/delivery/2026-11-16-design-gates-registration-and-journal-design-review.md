# WA5 后继登记／源记录／运行双门独立设计审查

2026-11-16。审查者：fresh-context agent `/root/wa5_storage_journal_design_review`。本轮先读原始要求、D1–D4 和实际生产 owner，再读拆片方案；只写本报告，未改源码、测试、PLAN、模板、CI 或其他交付。

**当前 r2：需求符合性 approve；可维护性 approve；开放 finding 0。** 首轮两轴 request-changes 及 3 项 finding（P1×2、P2×1）保留于下文；r2 定向复核与关闭依据见末节。本结论只认证拆片设计及验收接缝，不代表 S1/F/J/G 或可信人类部署已经实现。A 的最终闭合仍是独立前置，未预填通过。

## 固定输入与检查范围

|输入|本轮身份与范围|
|---|---|
|当前 r2 拆片方案|[2026-11-16-design-gates-registration-and-journal.md](../plans/2026-11-16-design-gates-registration-and-journal.md)，171 行／41,027B，SHA256 `a94b4a5a95a674330e09e84b0c7596635bc985521c3f8d221ed996dbb07965ae`。|
|首稿拆片身份|159 行／36,815B，SHA256 `8c8ae498a601f8379df157273df4d71080796a93ed7f4ba9a2b378dafc5940bf`；首轮结论为需求／维护性两轴 request-changes。以下 R1–R3 的原方案行号均指此首稿；不能当成 r2 仍存在的缺口。|
|原始要求|[workflow-evidence-and-human-gates](../plans/2026-11-15-workflow-evidence-and-human-gates.md)，SHA256 `3d5ed4f8f080b7b4099eaa998c2d9a5c767e6d7953b21ecd72b3f6e6d2763040`；[用户 D1–D4](2026-11-16-workflow-design-decisions.md)，SHA256 `f4890512a56b7010b7ca4ca9b40aefa8a366a5b25f4ebe4d0e7fb73c73f37b68`。旧冻结任务保持原合同，必要问题由有权 owner 明确处理，新受审材料重新批准，先设计／知识再可信检查。|
|已审详细设计|[WA5 r2](../plans/2026-11-16-design-knowledge-gates.md)，SHA256 `5360d993ee7851f81237151f9ed2e5aba7a9f1f7dbf501f88e33dd18b61faa54`，及其[独立设计审查](2026-11-16-design-knowledge-gates-design-review.md)。其通过只覆盖原范围。|
|主树|分支 `refactor/architecture-foundations`；HEAD `0a5a0ffb32cd2a247eaef49a008cb5692ffad47a`；`src` tree `a00fdd6469d823feb24b13365fea9bb1f27b822b`、`tests` tree `73e0aa9d7eb7d0fbb722fa509f69e8fe9fb80ce9`。开始及写报告前均未见主树源码／测试差异；已有并行 docs 差异保留。|
|a1|只读 `.ergora/worktrees/design-packet-inspection-fixed`，HEAD `a8d1855fb62513f5faeb8b3f9b1cfe4a38c1c0a2`。所见在途差异为 `reference.py` 公共 `task_approval(inspect-plan)` 转入应用校验及其 `test_task_plan.py` 回归；没有执行或认证最终修正版。A 仍是待准确闭合的依赖。|
|规则|根、`src/ergora`、`tests` AGENTS；[组件协议](../architecture/component-change-protocols.md)；`maintainable-project-delivery` 及 independent-review；`ergora-codebase-quality` 的 module-design、test-seams、repository-style。|

静态追踪了 `registrations → reference.registration_io → _registration_main`、`tasks → reference_creation_process → _Creation`、budget preparation、`_Submission → _Approval/_Cancellation`、`WorkflowInput` 工厂／worker／request-root、原 Workflow/Activities/FileAdapter、`reference_executor → BudgetedJob → processes.run`、State migrations 和 backups。阅读现有 registration／task creation／budget／migration／backup 等 fixture 以核可验收接缝；未运行它们。

## 首稿 R1／P1：空项目也不能沿现有发布合同从 v1 改登记为 v2（r2 已关闭）

位置：方案[第 47 行](../plans/2026-11-16-design-gates-registration-and-journal.md#L47)，关联第 56、69、73、142 行。

方案允许“新项目，或可证明无任务的既存项目”登记 v2，并保持原四投影合同。但现 [publication_files](../../src/ergora/registrations.py#L64) 将 definition digest 放进 marker；增加 design policy 就改变 marker。真正的 [原生发布器](../../src/ergora/reference.py#L308) 对**已经存在且 canonical 内容不同**的任何四投影直接报 `Immutable registration conflict`。`registrations.register` 在 [_reserve 之前](../../src/ergora/registrations.py#L278) 已做此比较；`_finish/resume` 也调用同一不可覆盖发布器。现有测试允许的重新登记是原投影不变的情况，没有提供更新 marker 的接口。

因此，即使已经客观证明一个 v1 项目从未有任务，按 S1 所列 owner 和原发布合同仍无法完成 v1→v2。若实施者为满足这条验收而临时允许覆盖 marker，就新增了原生持久迁移、并发和中断恢复语义，尚未由本拆片设计定义。旧 creation 绑定当前登记的问题之前，还存在这个实际发布前置。

**最小纠正：** S1 明确只接真正的新登记：没有既存统一登记／原生四投影；已有 v1（包括空项目）的 v2 变更明确拒绝，保持原登记 intent/result、控制项目和四投影零增量。已有 control project 但尚未登记的支持范围可以按其原合同单独写清。将旧 marker 的精确比较、迁移发布顺序、旧登记与旧 creation 的读取／停止，以及中断恢复／回退列为后继同一迁移合同；后继实施前再给具体方案。无需为了首片新增覆盖原件的发布接口或扫描历史的框架。

**验证接缝：** 在 `test_registrations.py` 的真实 `register/status/resume/registration_io` 路径，保留一个无任何 task 的 v1 登记，提交仅增加 policy 的 v2；必须在登记意图和 native 写入之前显式拒绝，并核控制项目、原 journals、四投影保持。新项目 v2 的 pending／各发布中断／result 后恢复另验。仅 mock 掉 `registration_io` 或只比较 project JSON 看不到这一风险。

## 首稿 R2／P1：只在两个应用出生入口拦旧 definition，未覆盖受管 runtime 的 legacy 入口（r2 已关闭）

位置：方案[第 74 行](../plans/2026-11-16-design-gates-registration-and-journal.md#L74)，关联第 35、56、69、127–135、142 行。

方案把 S1 的拒降级落在 `tasks._definition/_budget_project`，后继 G2 又只扩 v12 的 Input/adapter。现有生产路径还有：

1. 原 [native CLI create](../../src/ergora/data/reference/platform/local/agent_platform/cli.py#L206) 调 `projects.create_task`，直接生成 legacy spec；其 [start](../../src/ergora/data/reference/platform/local/agent_platform/cli.py#L21) 只核原 execution allowlist／doctor／checks 后启动原 Workflow，不经过两个 `tasks` guard。S1 原生 execution 投影仍按旧 task type 放行。
2. 本版受管 [executor.process](../../src/ergora/reference_executor.py#L719) 从 published document 或 context spec 选 input，且 `request_roots()` 继续枚举 legacy 根。[LegacyInput 的两个准入 hook](../../src/ergora/reference_inputs.py#L78) 都继承空实现。
3. [Executor 构造](../../src/ergora/reference_executor.py#L35) 仅在 composition 路径要求原 control creation；`composition is None` 时会进入原 `super().__init__`。原构造已有 claim 等动作；随后非 composition 的项目检查也只核登记状态、目录、四文件和 task type，没有 design policy 检查。原 schema1 批准路径同样保留。

可达情形是：新 v2 项目本来应因完整关卡未开放／`human_channel_unavailable` 不能产生新的受管业务，但旧 native 工具产生原合法 legacy task，经本版 worker 和本版受管 executor 消费。它没有经过所列两条应用出生 guard，也没有选择 v12 的 G1/G2。该问题来自现有支持路径，不要求篡改 packet、审批 JSON 或当前 policy；State6 writer fence 也不阻止原 native 文件创建。这里是静态可达路径，未进行服务或业务复现。

**最小纠正：** 将新设计登记对旧输入的拒绝也落到已有受管 executor 的实际准入边界，在原 business claim／prepare／业务动作之前读取权威项目策略，拒绝在该项目上新产生的旧输入；不要只在新 v12 类加检查。旧 v1 项目继续原合同，未来已存在旧任务的豁免只能凭精确原 creation/prepare/registration binding。明确原 standalone worker/executor 不受新的应用 guard 控制，其部署切换需要沿原 service owner 核旧 stack 已停止／隔离；现 [managed services 的 legacy socket 拒绝](../../src/ergora/services.py#L186) 可以复用，不能声称其单独认证所有独立进程。无需改 283 份冻结参考或增加上层版本分派。

**验证接缝：** 给新设计项目一个由原 native contract 构造的合法旧 spec／job，通过真正 `reference_executor.process/Executor`，保留旧 request-root 的选择、原 State、原 claim/prepare 和业务启动边界；必须无新业务 body/model/可信命令启动。加一个旧 v1 项目对照，证明兼容未被统一禁用。将来允许旧任务升级后，再验精确旧 binding 的恢复及伪造“旧任务”不获豁免。原 `tasks.create/prepare` 拒绝且预算／意图增量 0 仍需保留，但不能替代这个 runtime 接缝。原 standalone 部署边界单独记录，不用 fixture 通过冒称旧运行器已安全切换。

## 首稿 R3／P2：offline backup/restore 的范围不足以承诺登记发布后的完整回滚（r2 已关闭）

位置：方案[第 77 行](../plans/2026-11-16-design-gates-registration-and-journal.md#L77)，关联第 73、75、142 行。

现 [backups.create](../../src/ergora/backups.py#L160) 只 inventory/copy 传入的 control home；[restore](../../src/ergora/backups.py#L189) 校验原 home 后只还原该目录。`execution.config_directory/state_directory` 是独立绝对路径，通常在 control home 外；原四投影、task-approval journals、原 receipts/fences 等不因 SQLite backup 而入包。State 的自动迁移前备份范围更窄，只有 DB。

若先备份 schema5 home，再迁移、发布 v2 登记，随后仅用原 offline restore 回退 control home，外部 config 仍有 v2 marker；若后继开放过原生状态，其 journals/fences 也仍保留。旧控制记录与 native 投影可能不一致，新项目甚至变成有 native owner marker、无相应 control 登记的状态。“先保留迁移后新原件”正确，但不会自动恢复这组一致性。`test_state_backups.py` 的一般 round-trip 不能证明登记发布后的部署可回退。

**最小纠正：** 明确区分“State6 失败的 DB 事务回滚”“control-home offline 恢复”和“v2 发布后的整体部署回退”。S1 可以只承诺前两者的准确范围，并明确发布后的软件降级／跨根回退尚未支持；保持新原件用于同版本恢复，不为回退修改 user_version 或删除 fence。外部 config/state 的协调快照、精确原登记投影、恢复顺序和中断失败行为与 R1 的后继迁移合同一起设计。无需为首片新建泛用 backup 服务。

**验证接缝：** 沿现 backup fixture 明确外部执行目录不在 inventory 的事实，源／安装分别记账。若交付整体回退承诺，必须在真实 v2 登记发布后还原 control home 与外部目录，再核 `registrations.status` 和原 creation／停止读取一致；未提供这项证据时不能把 State restore 的通过写成完整部署回滚通过。

## 其余核对与两轴结论的边界

|方面|静态结论|
|---|---|
|原始要求与 D1–D4|研究采用、设计／规范／取舍、客观验收、必要公司知识、逐轮原文、明确 owner 处理与修订均保留。没有让沉默或 `reported-human` 成为批准，也没有要求用户重答已决定的产品方向。|
|旧 creation 耦合|方案对 `_Creation.validate_record/published/preparation`、`_Submission`、approval/cancel 和 executor 的依赖判断正确。F 还需给出具体迁移方案，特别是当前四投影与旧原件如何分别核验；仅能找到一份历史 registration journal，不会自动使现 `check_registration()` 接受它。S1 不更新既存登记可避免先损坏旧任务，但不构成 F 已完成。|
|S1/S2 的可交付性|status／恢复／出生准入，以及 r2 补入的受管 executor 准入，是 S1 的真实消费者。S2 若有原 `tasks` 用例、最小 CLI 和完整读回，可以作为 inspection-only 材料存取独立验收。没有真实消费者的格式、空 adapter／Workflow 或临时 profile 不应单独成片；方案对此已有约束。|
|J 的最小合同|同 journal、result commit、两种 revision、完整 materials identity、prepared seal／明确废弃、attempt 后只对账、封存后新 task 的规则具备实际风险依据。source／链读取留原 approval owner，纯领域规则才共享，未见需要新事件平台或通用 journal 抽象。|
|withdraw 与进程|固定 cancel child、父 result 后继续尾部、creation→admission 锁序、释放外锁后原取消自行取锁，以及可见／持久／已停止分列均合理。最后启动检查确需在 `processes.run` 的真实 Popen 区间；collection/cleanup 保持原 owner。后继必须按所列跨 owner 中断和真实子树观察验收。|
|可信 human 与部署|方案如实把当前同 UID／无隔离通道列为 unavailable；TTY、confirm、UID 字符串、JSON 或 chmod 不产生更高 assurance。代码／安装的负例闭合与真实人类正向部署分别记账合理。本审没有验证任何实际 ACL、组织身份或终端部署，不能把这些描述当部署证明。|
|native 依赖与 a1|应用 schema、native 标准库身份／领域规则、安全完整读取的分界合理。A 必须以最后准确修正版完成原解释器与两公共入口验证；本审只看见修正代码，不转授旧 wheel、121 或先前源审通过。|
|验收接缝|G1 原 authorize context 无 admission、实际 plan envelope 取冻结 policy；G2 完整材料进真实 work/review 和 saved formal-call；unknown 不重发；真实锁／Popen／reaping 与 SDK fixture 分开，这些选择合适。新增 R1–R3 接缝后，不需为设计文档运行产品测试或扩大重复矩阵。|

首轮维护性 request-changes 针对实际发布／执行／恢复 owner 的遗漏：按首稿文件落点实施，会把 native marker 迁移、legacy runtime 准入和跨根恢复的义务留给未声明的调用者。r2 已按下节分别收窄或归回原 owner。已有 `WorkflowInput` 工厂、原 approval/cancel owner、纯 `task_design`、原 process guard 的分工可以继续；无需另建调度器、身份服务或配置框架。

本轮实际命令仅为本地 Git status／HEAD／tree／少量 diff、SHA／行字节数、`rg` 与分段文档源码读取；没有测试、probe、安装、模型、网络、服务、训练、凭据读取、commit 或 push。报告写完后仅检查本报告的链接、空白和修改范围。所有 schema6、v2 policy、source journal、G1/G2、最后启动及可信通道的产品验收仍未实施；A 的最终闭合仍由主控独立记账。

## r2 同片定向复核

本轮直接读取当前 r2 全文，并对照原 `reference._registration_main` 不可变发布、`_Creation` 当前登记绑定、`reference_executor.process/Executor` 与 `LegacyInput`、原 `backups.create/restore` 和 managed services 的旧 socket 边界；最终字节的第 41 行 owner 表、第 87 行 consumer 列表已同步纳入 S1 executor 准入，定向核对与上表 SHA 同一。主树 HEAD、src/tests tree 与首轮同一；没有产品实现差异或新增运行结果。复核范围为原三项及其相邻依赖／验收，不将作者的修订说明当成验证结果。

|Finding|r2 修订与独立核对|处置|
|---|---|---|
|R1／不可变 marker 与空项目升级|[第 47 行](../plans/2026-11-16-design-gates-registration-and-journal.md#L47) 明确只允许首次统一登记，原登记或原生四投影存在时不能按“空项目”豁免；所有既存 v1→v2 在 intent／reservation／native 发布前拒绝，原控制、journals 和四投影零增量。同 ID 的首次 v2 中断恢复保持。第 49、60 行将 marker／四投影迁移、旧 creation/prepare/submission 精确绑定、当前四文件核验及外部根一致恢复归为 F 的实施前独立合同；第 150 行的真实 registration 接缝可观察首轮风险。|关闭。S1 不隐含原生覆盖接口；既存登记迁移仍未设计完成或实施，不继承本次通过。|
|R2／旧输入的受管 runtime 准入|[第 78 行](../plans/2026-11-16-design-gates-registration-and-journal.md#L78) 将权威 v2 policy 检查落入真实 `process → Executor`，要求在原 business claim／prepare／副作用前覆盖旧 request root、`composition=None` 和 native CLI 合法旧 spec/job；文件 owner 和 S1 关闭条件均已加入 `reference_executor`。旧 v1 项目与冻结恢复保持，未来旧任务豁免须精确原 binding。第 80 行将 standalone stack 停用／隔离单列部署前置，不把 socket 检查当所有进程的证明。第 150 行新增真正 process/Executor pre-claim、新 v2 拒绝／旧 v1 对照及 claim/body/model/可信命令 starts=0；该接缝能观察原 hook 为空、budget job 早于构造 claim 等实际路径。|关闭。接口与验收合同足够；实际 guard、原 claim 顺序、旧任务兼容及 standalone 部署切换仍须各自证据。|
|R3／backup 的真实范围|[第 83 行](../plans/2026-11-16-design-gates-registration-and-journal.md#L83) 将 DB 事务回滚、control-home inventory 恢复和 v2 发布后的跨根部署回退／软件降级分别列明；后两种范围不混用，自动迁移备份只有 DB。外部 marker/receipts/fences/journals 不自动入包，同版本原件保持；跨根协调快照／恢复顺序／失败行为与 F 另行设计。第 85、150 行保留原 backup 回归并要求报告外部根未入 inventory 的事实；完整回退必须实际 v2 发布→多根恢复→status/creation/停止一致性后另验。|关闭。当前不承诺未提供的整体回退能力；没有扩大 backup 框架或绕过 fence。|

三项修订没有改变 D1–D4，也没有增加用户权限前置。当前需求／维护性两轴 approve，开放 0；这是设计和验证分片方向的静态结论。最小 S1 仍须等待 A 的准确最终闭合，并按自身源码／安装／原模板／fresh 独审完成验收。F 的原生登记迁移、J/G 可执行闭环、真实可信人类通道及正向旅程均继续待交付，本报告不认证任何新 profile 可运行。
