# WA5-S1 首次设计 policy 登记／State6 独立实现审查

2026-11-16。审查者：fresh-context agent `/root/design_policy_s1_implementation_review`。先读 D1–D4、已审拆片及原调用，再读完整源码差异，最后读作者交付和运行原件；未继承作者实现对话。唯一写入为本报告。

**当前同片源码复核：需求符合性 approve；可维护性 approve；开放 finding 0。** 修正版 `121ed2bf6a49713adb08d2b339bd9a490b1675e4` 已关闭 R1，核对过程和准确红绿证据见文末。这个结论只认证源码与所核接缝；修正版安装、原模板及部署验收分别记账。

首轮需求符合性 request-changes、可维护性 approve、开放 R1/P2 一项的原结论保留如下。R1 的交错登记会在拒绝前增加一个孤立 intent，违反首次登记的零增量边界；模块与依赖归属没有另一个维护性 finding。

|固定输入|独立核对|
|---|---|
|原始合同|[用户 D1–D4](2026-11-16-workflow-design-decisions.md)，SHA256 `f4890512a56b7010b7ca4ca9b40aefa8a366a5b25f4ebe4d0e7fb73c73f37b68`；[已审拆片](../plans/2026-11-16-design-gates-registration-and-journal.md)及[设计审查](2026-11-16-design-gates-registration-and-journal-design-review.md)，后者 SHA256 `bb12afc99d8f5883f67cead512daa9eff625f87d556a72a6166f18d288ea317e`。|
|方案原字节|原 `a94b4a5a95a674330e09e84b0c7596635bc985521c3f8d221ed996dbb07965ae` 原件与当前 `bde47bee749ff973901beeebc6f148316b3ea2d2635e191ac5804942e142f984` 均实核；对原件只作 16 个 `.py:行号` → `.py#L行号` 链接替换后，全文等于当前方案。|
|准确待审树|`.ergora/worktrees/design-policy-registration-fixed`；分支 `feat/design-policy-registration-fixed-r1`；HEAD `34f6e83dfff3bad26c4359b1c769388592b95fa4`；基线 `eba86805e5d50824eefb5e69edd0faab099cbf42`。开始与读取结束时工作树无差异。|
|完整差异|`.ergora/checks/design-policy-registration/fixed-r1/source.patch`，72,655B，SHA256 `17da337cd6f1508bade18d00091bc1a0028a76efc175148fb27d06a232f38098`；与实际 `git diff --binary --full-index` 字节完全相同。14 个完整文件的字节数、SHA、执行位逐项符合 `changed-files.json`。|
|完整输入|`fixed-r1/source-inputs.json` 的 2,072 项全部核过实际字节／执行位，无差异；manifest SHA256 `6e426f77b2408546df91fd4085d01695a0227717c75efc988fbb77f8322bf7ba`。作者基线 `3d632a78b6acc4f0027b2225e7771a5da927af81` 至本基线的变更与 S1 的 14 文件无交叠；作者 final 789 个 package／test 输入与本树的差异恰为独立 M6 的五文件。|
|规则与后读材料|根、`src/ergora`、`tests` AGENTS、PLAN、[组件协议](../architecture/component-change-protocols.md)；`maintainable-project-delivery` 的 independent-review；`ergora-codebase-quality` 的 module-design／test-seams／repository-style。源码之后读[作者交付](2026-11-16-design-policy-registration.md)及原 invocation、JUnit、raw、manifests。|

完整检查的生产改动是 `data/schemas/project-registration-v2.json`、`registrations.py`、`state.py`、`task_design.py`、`tasks.py`、`reference_executor.py`；测试改动是 `test_registrations.py`、`test_state_migrations.py`、`test_state_backups.py`、`test_task_creation.py`、`test_task_budget.py`、`test_composition_executor.py`、`test_budget_jobs.py` 和 `fixtures/reference_acceptance.py`。相邻只读追踪覆盖原 `reference.registration_io/_registration_main`、`projects`、`contracts`、native `project_for/Executor/claim`、`WorkflowInput/DirectJob/BudgetedJob` 及恢复 caller。首轮行号指 `34f6e83` 固定候选；修正版另在文末固定。

**首轮 R1／P2：锁前取得的首次登记资格，会在不同 config root 的交错请求中先落新 intent 后拒绝（修正版已关闭）。**

位置：[register 的锁前读取及锁内入口](../../.ergora/worktrees/design-policy-registration-fixed/src/ergora/registrations.py#L341)，[先写 intent 的 _reserve](../../.ergora/worktrees/design-policy-registration-fixed/src/ergora/registrations.py#L301)。

可达序列无需改原件：同一 control home、同一项目，两个合法首次请求都以 expected revision 0 读到 `before=None`，分别使用空 config A 和空 config B。B 的 v2 请求在 `_prepare` 后暂停；A 的 v1 请求取得 publication lock，完成首次登记并释放锁。B 随后取得相同 control-home lock，但锁内仅重读 **B 的**原生四投影，它们仍为空。B 调 `_reserve`，第 303 行先 `_record` 保存新的 operation intent；第 308 行才发现当前项目已经是 A 的 v1 并报 revision changed。先完成的是 v2、后到的是旧 v1 或另一 v2 也有同一问题。

DB 中的原项目和原生四文件不会被覆盖，但 registration journal 已增加一份孤立的新 intent。它明确违背 S1 的“已有 v1（含空登记）不得升级、已有 v2 不可重登记／降级，任何原 journal／reservation／native 写前拒绝”及零增量要求。首轮测试按串行请求覆盖已有项目和已有四投影，不能观察这个交错。首轮只作源码可达性判断；作者后续原候选红例确实复现，见文末。本审未自行执行复现。

最小修正是在 `register` 取得 `_publication_lock` 后、任何 `_record/_reserve` 前，重新读取当前 control 项目并核其与 `before` 一致；不一致直接拒绝。保留 `_reserve` 的事务内最终核验及“intent 先于 DB reservation”合同。可在原 `test_registrations.py` 用受控交错保留真实 `_reserve/_record`：让两个请求的预备期看到同一初态、分别选不同空 config root，先完整发布一个，再让另一个继续；拒绝后核现项目、所有 registration journals、四投影无新增。参数覆盖先胜 v1 后到 v2、先胜 v2 后到 v1／v2，属于同一个并发接缝，无需新框架或长服务测试。

|其余要求／维护性核对|所见事实与边界|
|---|---|
|正式 policy 的存储身份|v2 schema 与 v1 外层形状逐字段比较，除 version／新增 policy 外相同。完整 formal profile／owner 来源要求进入原 definition；profile SHA 与去自身 SHA 的 policy canonical SHA分别核验。Q/K namespace、跨类别／同 ID 异内容冲突、profile＋项目最低并集及配置容量留 registration owner；没有把 inspection profile 当 formal policy。|
|status／原恢复|`_validate_saved` 由 status、finish 和 published journal 共同消费，按嵌套版本校验并核 definition digest；原 journal／result 容器和四文件格式保持。status 返回完整 policy 与 requirements，明确 `execution_supported:false`／`human_channel_unavailable`；没有以 owner_id／JSON／UID／TTY 声称自然人已授权。|
|串行首次资格|已有 v1 含空登记，以及已有 v2 的重新登记／降级，均在 `_prepare` 入口拒绝。已有未登记 control project 且无四投影的首次 v2仍可进入原合同。任一原生投影已存在时 v2 拒绝；同 operation 的中断走原 resume。R1 是这条资格在并发下的剩余缺口。|
|容量与原件|新 `_intent` 按 `_record` 同一完整 pretty JSON／UTF-8 序列化核原 32 MiB 读界；register 在任何 publication 锁／journal／reservation／native 写之前检查，`_reserve` 消费相同 record。没有通过扩大 configured policy 限额或截断原文解决容量问题。|
|State6|只给原 21 个领域表换 63 个 writer triggers；表、行 JSON 与 journal 版本不变。沿原迁移事务／DB backup；旧已开 v5 连接在新 triggers 下不能写。失败回滚与 control-home inventory restore 是独立范围，外部 config/state 整体回退与软件降级未获认证。|
|出生与真实 pre-claim|两个应用出生入口在原预算／intent前调用同一纯规则；恢复入口未加出生 guard。`process` 在选择／构造 job 前拒绝，直接 `Executor` 在原 constructor 前拒绝；已跟到 `BudgetedJob.run` 的早 claim，未只检查未来 input hook。权威来自实际 native tracker、marker control-home 及 State project/repo。|
|v1 冻结兼容|新 `_admit_project` 不强迫旧 frozen selection 匹配当前 v1 registration SHA／execution roots；从旧 native root恢复的合同保留。没有增加 v2 旧任务豁免，也没有把更换 control home 当作无 policy 的旁路。|
|模块与依赖|没有新生产模块／服务／ABC／registry；正式配置接口是 schema 的实际角色。`require_execution_support` 有 tasks 与 executor 两个真实生产 caller，`task_design` AST仅导入 stdlib datetime；native 没新增 registrations／contracts／jsonschema 依赖。registration 的局部校验与 intent helper留原 owner，process／直接构造两处复用 IO admission 有各自真实 claim边界。|
|范围保护|准确 diff 未改 283 参考、presets、原锁、scripts、pyproject、a1 profile/schema或 input factory；未引入 definition8、input12、source F/J/G、可信 owner批准或新执行能力。standalone 旧 stack停用／隔离仍是单独部署责任。|

**首轮核过的运行证据与未验边界。** 本审只核原件，没有重跑测试或执行产品 probe；没有安装、模型、网络、服务、训练、commit、push、spawn 或改其他文件。

|记录|独立读取到的结果与身份|
|---|---|
|作者 `source-final-directed`|原 invocation／stdout／JUnit／result 均存在：83 passed，pytest 116.91 秒；manifest SHA256 `71a22bd2ec1d288cbad5acfad8c9c4b7c4abff9c3fa981df1fda57033c9d010b`。覆盖完整 registration 75、四个原 v1 frozen六阶段、wrong-state旧失败回执、新 legacy v1/v2与 Budgeted preclaim；不是全 runtime通过。|
|作者 `source-core-r3`|原 JUnit为164 passed／1 optional Web skip，pytest233.36秒，旧输入 SHA256 `4fbf928d2d6160cfca2482b63f18de6a76c4b47d308275d70a146954e7b09149`。与作者最终输入差 `registrations.py/reference_executor.py/test_registrations.py`；不能把旧候选完整 core运行写作当前候选的全套通过。|
|作者 `source-runtime-r3`|原 JUnit86 completed／13 failed、exit2；实际119 collected，33未执行。8个 composition失败与一个名义负例pass涉及隔离解释器加载主树State5；9个 model-log SHA全部实核，trace明确来自主树 stage_driver/state。另5项是作者过强 current SHA guard的真实兼容回归，最终定向83覆盖修后接缝。混装失败、名义pass、未执行与修后结果分别保留。|
|原失败与反例|`red-recovery-writer-bound` 原 JUnit一失败存在；`red-runtime-original-executor` 明确是当前v2前置＋原executor的有意混合回归，不能叫未改基线通过。其目的与原legacy fixture计数接缝一致。|
|首轮新包当时所见|已读 `package-r1/build-install-r1.json`：新非editable wheel、core/SDK安装和包身份检查各exit0；wheel SHA256 `cb736cc33eb018c7c59e4ec0ac2cd1a8c7ee614a0042a4d797171d744f8a200f`。两份原 reference报告各283／PASS／runtime_started false。安装runtime及原模板当时仍待主控准确结果后另核，不能以构建／包字节替代行为验收。|
|本审静态检查|14个Python／JSON完整差异、相邻调用与fixture阅读；变更Python AST解析；准确patch／14文件／2,072输入 SHA与执行位核对；方案16链接映射；`git diff --check`通过。无新执行结果。|

首轮结束时 R1 修复及其原并发接缝、同版安装必要恢复／composition／取消／预算接缝、原结构模板尚未在本报告闭合。下列同片复核只关闭 R1；历史运行身份继续保留。

**R1 同片定向复核：关闭，源码两轴 approve／开放 0。**

本轮先读准确两文件 diff、当前 `register` 与新测试的真实调用，再核红绿原件及作者交付补记。固定树仍为 `.ergora/worktrees/design-policy-registration-fixed`、分支 `feat/design-policy-registration-fixed-r1`；HEAD `121ed2bf6a49713adb08d2b339bd9a490b1675e4`、父 `34f6e83dfff3bad26c4359b1c769388592b95fa4`，无工作树差异。父到 HEAD 仅 `registrations.py` 两行及原 `test_registrations.py` 40行，合计42行。

准确 delta `.ergora/checks/design-policy-registration/source-r1-fixed/review-r1-fix.patch` 为3,722B／SHA256 `56c0ee1c3d1fd1f9f470b635e48176dbfdf7b9bdb1e762c9288292c0bd3dd404`，与实际两提交 `git diff --binary --full-index` 完全同一。相对集成基线 `eba8680` 的完整14文件diff为74,929B／SHA256 `59dc8c3171fa19c4cd595d2e27d20ef7d664fc1ae15f46a1c04bd544e79edc87`；与作者旧基线的完整patch `7f6133b9c49c95d4c638d385c804c65fda8af68cdf75e0b6bd4fcb85e73a543a`分别记账。

[修正版第351行](../../.ergora/worktrees/design-policy-registration-fixed/src/ergora/registrations.py#L351)在同一 control-home publication锁内重读 `_current` 并比较完整 `before`，不等就拒绝；它早于原生观察和任何 `_record/_reserve`，第308行的事务内核验保持。两个register都必须经过该锁，因此首轮交错中迟到调用会在此看到先到登记，不能再增加孤立intent。没有扩大锁域、改变恢复路径、改写旧原件或引入第二权威。

新回归只在原 `_prepare` 返回后插入一次真实竞争发布；内层使用同home的另一 `State`、合法正式定义和不同空config/runtime roots，原 `_prepare`、publication锁、`_reserve`、`_record`、native `registration_io` 均保留。三个版本组合覆盖v1升级、v2降级与重登记。原测试文件就是合适接缝；不需线程计时或服务替身来制造这个已明确的交错。测试除了文件集合，还比较全journal字节、winner config、project与SQLite逻辑全库，并确认late四投影／runtime没有产生。

|修正证据|独立核对与结论|
|---|---|
|原候选红例|`red-stale-first-registration` 的 invocation／raw／JUnit／result存在：3 failed，stdout3.79秒，exit1。与首轮原manifest逐项比较，只有新测试改变，670个原包输入全同；其source.tar全部789文件字节／执行位符合run manifest `323ae5e0aeaaee3840de61c7d08715410056830116d6bc980ad935cf5444494d`。|
|红例真实失败位置|三项 `[1-2]`、`[2-1]`、`[2-2]` 均先得到revision错误，再失败于多出一份journal的集合断言。直接读取各fixture原journal可见winner intent＋result与late无result intent，两个intent的before均为null，版本分别符合三种组合；没有把新的断言本身当通过。|
|修后原完整registration|`source-r1-fixed-registration` 原invocation明确跑完整 `tests/test_registrations.py`；stdout78 passed／59.18秒，JUnit78／0failure／0error／0skip，runner exit0。三项原交错node都通过，原v1／v2发布中断、CLI恢复、import与完整journal继续在同一组内。|
|修后输入身份|修后run的source.tar全部789输入字节／执行位符合manifest SHA256 `16f7647ce23b3ef8b7dd649d64db9157da34d6324cf7b3987b23c03ca698566f`。与根固定树比较只有原已审M6五文件差异；本片两文件相同。|
|新freeze完整性|`source-r1-fixed/complete-tree-manifest.json` SHA256 `ba51610eee994c0b31609451918b3d6140b2f2b9dbe3557e3765fa4023a61e6d`；2,065项与作者实际树逐字节／执行位全同，相对首轮完整tree差集恰为上述两文件。两文件AST和准确delta的 `git diff --check`通过。|

以上证据关闭 R1，未发现修正引入的新需求或维护性finding。本轮仍只读源码／AST／manifest及既有运行原件，没有重新执行测试或产品操作。首轮83、历史164／1skip、主控另报的首轮安装166及新修正版安装分别保留身份；不能转授为本修正版整套runtime通过。主控正在做新的同版安装和原模板，其准确结果尚未计入本报告。

真实 protected owner通道、F/J/G、旧项目迁移、standalone stack切换、跨根部署回退、真实Temporal／模型、发布与本候选CI继续各自验收；本次storage／负例的源码结论不能转授这些能力。
