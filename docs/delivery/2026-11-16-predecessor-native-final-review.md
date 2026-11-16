# M5 r7／native source-v2 r5：fresh 独立联合终核

2026-11-16。审查者：fresh-context reviewer `predecessor_native_final_review`，未参与实现。先读原要求、准确 Git diff、新资源和真实消费者，再读作者交付、旧审查及原始验证材料。采用 `maintainable-project-delivery` 的 independent-review brief 和 `ergora-codebase-quality` 的 module-design／test-seams／repository-style；已读根、src、tests 的 AGENTS、PLAN 和组件协议。

**需求符合性：approve。结构／维护性：approve。所审范围开放阻塞项 0；允许普通集成下述准确联合产品。** M5 原 R1 由显式 source-v2 的最终已安装真实 native 入口证据关闭；M5 单独的 v1 安装仍有原 SDK 依赖，旧模型 request-changes 和旧失败保持原结论。此批准不开放 schema3／ordinal1 效果，不认证 M6、正式 runtime／producer、真实两轮、训练或 GPU。

## 准确输入与独立身份核验

原合同为 [M5 前驱及最后准入设计](../plans/2026-11-16-training-cycle-predecessor-native-gates.md)、其从属的 [原 wire](../plans/2026-11-16-training-cycle-measurement-wire.md)，以及 [native 依赖隔离设计](../plans/2026-11-16-native-admission-dependency-isolation.md)。本文只写本报告；未编辑源码、安装、联网、运行测试／模型／长批、启动服务、commit 或 push，未读取 `inference.toml`。运行的检查仅为必要文件读取、Git、AST、raw SHA／bytes／执行位比较及既有结果解析。

|产品|准确身份|本次重算的完整 diff SHA256|
|---|---|---|
|M5 r7|固定树 `training-cycle-predecessor-gates-fixed-r2`，HEAD `5bcecf37b615e3708ceb08acc329ba3dd0470f4a`，唯一父 `f6722141cfa9ed885993360161c004e47e8df3a5`；相对原基线 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`|11 文件，`61e1e11fbbc582453b3afeba3d20786eb2347c279fea3b4969285c0121f3b017`|
|native r5|固定树 `native-admission-dependency-v2-fixed`，HEAD `bc58be6781d35e7e4fbd54ad997df8a4743428a8`，唯一父为上述 M5 r7|native-only 11 文件，`3524d80f4d1c62688086cbaf9638ddc07c6d5a8f8f79118fecb87555273fbdc0`|

两固定树实际 working tree 均干净。已逐项重算 M5 的 853、native 的 855 项构建／测试源码输入，以及各自 179 份 test/example 副本，全部 raw bytes／SHA／执行位相同。原开发树的冻结差异没有被编辑或重新用于运行。

读完的 M5 diff 涵盖六产品文件 `reference_training_budget.py`、`reference_training_execution.py`、`reference_training_submission.py`、`reference_training_worker.py`、`training_cycles.py`、`training_execution_protocol.py`，及五份已有 fixture／测试。native diff 涵盖 `reference.py`、protocol、CLI、两个新增 v2 资源、`docs/TRAINING.md` 和五份已有 fixture／测试；新增资源完整正文在审查范围内。必要邻接读取包括原 reference training／executor／client、BudgetedStart、registry create、submission send、Execution、S/H 消费及 processes 收尾路径。

## 需求与维护性判断

下述行号均指最终 native r5 树；M5 未被本片覆盖的实现与父提交一致。

- **原完整链及库存。** `training_execution_protocol.py:1452` 绑定原完整 candidate intent；`:1496` 起的共享认证从实际 intent 的 predecessor 逐轮回到 0。固定 prefix 目录、完整 10 MB raw index／observation、每份原前轮 intent、acceptance 投影、原 H request／stdout 投影及父 fixed run 相互绑定。`round_report_binding:149` 核选中 manifest／spec／binding、annotation、revision、共同约束、anchor 和完整 prefix 延伸；没有 latest、替代目录或短链降级。`ExecutionRecords:1295` 沿真实 originals 生成完整 raw inventory，durable observe 后与保存观察精确比较；`:1608` 起对完整 evidence.files 沿既有 safe-file 和冻结 state/config 根核 raw。原 archive eligibility／比较器没有复制进 protocol。
- **当前 intent 及出生边界。** `protocol.py:1535–1538,1639` 通过原 `ExecutionRecords.document` 以原 16 MiB 容量读取当前实际 intent，按 canonical 身份比较，末端重读并保持入口存在性。已有 owner 时缺 intent 拒绝，合法空白重编码仍可读；真正 owner／intent 都未出生的 prepare 仍合法。原件或 pin 未被重新生成。
- **来源、ROOT、安装及原 clock。** `protocol.py:974–990` 先核本版本恰好 25 项出生 pin，再调用原 reference.verify 核 283 原件，核完整所选安装／descriptor 后重读来源并核原 interpreter 可用；`:1471` 核原四项 measurement 出生值，认证前后都执行。unborn prepare 没有虚构授权时已存在的 25 项 capability。parent stop、BOOT／UTC／work 继续消费原 clock，没有重开窗口或修改预算。
- **H 的额外职责完整保留。** `reference_training_worker.py:1210,1255,1281` 三次原 `_round_previous` 仍做 archive inspect，紧邻前轮仍核当前四事实／phase；全部阻塞 H／parent／index／local gate 返回后，`:1288` 再调用同一个纯认证算法。末端额外遍历关闭已复现的早轮漂移窗口，具有独立责任；原相邻重复 ROOT 遍历已删。没有采用 r5 探索中删除末 H 的方案。
- **真正动作门和恢复。** Budget.source `:263` 与 context `:1665` 都先认证再明确拒绝 schema3。submission `:234–262` 保留父共享许可和 attempt-before-send，同步后再 preflight／source／clock／stop；新 intent 写后也在原 owner 复核。registry absent 分支 `worker.py:1681–1690`、Execution.current `execution.py:53–72`、request／launch 原锁与 publish 后复核保持。没有退还已占用机会、换 UUID、补 ack／stopped 或把 unknown 变成可重发。
- **native 阶段与早读。** `native_main:1699` 保留所选 venv 的 sys.prefix 和 core ROOT／PYTHON／STATE／CONFIG 身份门；原 executor 在 executor.lock 内先读已有 result，才可能进入 callback。`:1714` 的真实 callback 和 `:1740` 的 active 绑定本次 stage，attempt、ack 各同步后重读；parent.check 返回后才核 fence／owner 和完整原 clock。没有允许旧 attempt 恢复执行或新增 reaper。schema3 在 callback 的 context 认证后关闭，尚不能声称其晚阶段正向效果已验。
- **原 operation window 没有丢失。** 共享认证只拥有原 cycle work clock，H 的 bootstrap 仍由真正结果消费者负责。`_CycleOperation._run:257–270` 仅在原 S 回收、两完整帧、EOF 且 `not self.expired()` 时接纳结果；`processes.run:196–197` 在 reap 后再采 should_stop。不能把超时 H 留存的 stdout 当成一次被接纳的成功。无需给纯算法再加 H 专属开关。
- **依赖隔离归原 owner。** 新 v2 bundle 直接从原 base 应用，实际 executor SHA 仍为 `feed0fa7574ad67e9d866adf41659d3288d1e4cc90178be2db830ea124388bca`。training.py 只移走顶层原 loader import，并在 run-local／approve 两个实际 CLI 分支局部导入同一个 `load_experiment`；没有新 loader／adapter／注入框架。reference 的封闭版本选择、完整 descriptor raw 核验及 protocol 的 `_capability` 分别隐藏安装身份和保存 shape 的职责，均有实际边界消费者。
- **版本和历史分开。** `protocol.py:896` 的保存 capability shape 校验不读当前安装；live validate_sources 另核所选版本。v1／v2 各恰好 25 键，只替换 descriptor 键；原四 measurement 和 execution PROTOCOL／owner schema 未变。legacy、owner1／owner2 null、旧 v1 history、已有 result 和安装不可用读取继续走原边界；没有旧 owner／authorization／clock 自动升级。最终 native 中 authenticate、native_main、validate_context、_round_sources、ExecutionRecords、CycleAdmission 等 AST 均与 M5 r7 父相同，worker／Execution 文件逐字等父。

上述守卫保护的是可达的持久身份、来源漂移、并发阶段和预算边界。纯计算迁回已有 protocol 后，worker、本地 budget/context/native 共用同一算法；State／SDK／archive／发布编排继续留原 owner。在审查范围内没有需要新模块、重复算法或额外兼容层的维护性缺陷。

## 最终安装与 R1 的直接证据

本次独立重算完整产品，不仅依赖已有 audit 的布尔结论：

|最终包|产品及原件核验|实际原 JUnit 终态|
|---|---|---|
|M5 package-r7|core／SDK 各 663 文件，source／wheel／两安装 bytes 与执行位全同；wheel `fafeede32f20d162a4b2977bb121afef80a8df48e07dcda720e44c4d37a3a02e`|5 passed，148.887 秒，0 error／failure／skip；driver exit 0|
|native package-r5|core／SDK 各 665 文件，同样全同；wheel `3c1ddaeb816d20841525d0be1f3139a59d0b62daaa98e14a75857481ce6e2fa7`|25 passed，161.775 秒，0 error／failure／skip；driver exit 0|

两包 core 原检查均无 Temporal，SDK 为 1.34.0；实际 imports 指向非 editable site-packages。两个固定产品的 manifest、v1 descriptor／patch 均逐字等原基线，283 原件逐项 raw 核验无差异；manifest SHA 仍为 `1f39b63b9c4966a0cd3d870047818924238615d10dcf7b85945814f7c8074943`。

关键原件是 native `package-r5/installed-affected-r5-cases/test_round_complete_observatio{0,1}/native-reader-results.json`。本次读取完整结果、对应测试／fixture 和原 observation，并逐项重算两份 native-reader-package：各 665 文件完整 bytes／执行位等已安装 core 产品，无额外产品文件。测试用原 reader 和原 verifier，没有重采来源、伪造 SDK／sys.modules／sys.prefix 或替换 validator。运行命令是所选 `.venv/bin/python -P -B`；v2 的 normal-native 分支不附 SDK site，拒导入 hook 在首次 executor import 之前安装。protocol 内原 sys.prefix／core 四路径门也保持，因此不是用 `-S` 的 base prefix 冒充真实 native。

|原记录／输入|本次直接核到的事实|结论范围|
|---|---|---|
|v2 正常 native，9,999,999 B 和 10,000,000 B|两次 rc0，均返回原 `Schema3 controller execution is not enabled`，`executor_sdk_loaded=false`；原 raw 实际达到对应长度，含唯一末 LF 与多字节 UTF-8|真实 native_main → executor → callback → 完整 context／前驱认证；**足以关闭本片 R1**|
|v2 pure `-P -S`|单列 authenticated=true／loaded=false|纯本地认证，未混同 whole-hook|
|v1 同样禁 SDK|真实 rc1，原 executor → training → client → Temporal traceback；另允许 SDK 的 native-sdk 记录 loaded=true 后到闭门|旧反例保留，v1 无 SDK 不予通过|
|v2 实际 native 漂移|应用 source、四 measurement、manifest、ROOT 均拒绝；保存的原执行链无新 started／result／runner|这些实际入口的负例，不把“未调用”当作缺 SDK 成功|
|descriptor／capability|安装 25 项中的原 reference／capability 入口核互换、缺失、格式、birth 漂移、版本混表和缺／额外项|并非单独一次 native descriptor 故障调用；共同安装 owner 被 native 复用|
|10,000,001 B|完整原超限 observation 留存，原 reader／H 容量拒绝，无 acceptance|未对超限输入调用 native reader，不扩称该路径已验|

最终 25 项还包含两个原 CLI loader 的真实校验语义、缺 SDK 时实际使用边界失败、安装缺失时的离线 history，以及 v1／v2 completed result 早读。它们不构成训练、tracking 或整个控制面无第三方依赖的认证。

## 原 finding 的红绿范围与模型材料

已直接读原失败日志和必要 case 原件，保留各自候选范围：r2 ack/interpreter 原例确实写出 started／FAILED result；r4 parent-work 在同 boot 的 work<0、total>0 时仍写 started，原晚前驱漂移仍发出 continuation_ready；r6 晚 current-intent 反例仍返回 accepted。当前源码保留其最小修正，未移走原 H phase 保护。

对应原绿色包括 r3 定向 7 项、r6 定向 8 项、r7 定向 4 项；原 ack-parent-work case 实测 work=-1.000157、total=168.999810，保留 ack／真实 stopped 而无 started／result，stderr 为原预算拒绝。r6 late-chain 原 result 为 unknown／原 raw pin 拒绝；r7 源码及最终安装 late-current-intent 原 result 均为 unknown／完整 current intent 身份拒绝，无 acceptance。旧结果不改写成最终联合套件运行；最终 r7 的 5 项和 native r5 的 25 项单列如上。本次没有重跑这些批次。

两个原结构模板的 scope 文件、complete.patch、task／prompt、完整祖先资源及 original-result 均已核读和重算：M5 18 个完整文件／862,310 B，native 16 个／830,415 B；每份文件与完整 diff 都在实际 task 内，三个祖先正文资源均在 prompt 内。prompt 的 963,759／880,790 B 和 SHA 分别等原 stdin 记录。M5 原 67.198 秒 request-changes 仅保留 R1；native 原 28.602 秒 approve 为 supplied-text 审查。两个 original-result SHA 均等 summary；没有把模型结论充作安装验收，也没有重调用刷判定。

## 收尾记录更正与最终边界

本次发现初次安装 audit 的“4 个完整身份”中有两个明示 synthetic_execution 三元组（pid2/start1、pid3/start2，boot 全零）。将它们计作真实进程会夸大捕获范围；该记录问题已在终核中关闭。作者保留原 audit SHA `6ed78128dc3ea1a344274ded4af26ca6dd850c17d02129c3d80f992db99549ad`，新增精确分类的 `final-installed-r7-r5-audit-r2.{py,json}`，JSON SHA 为 **`c9ef8c705ec82fe3678d5af1f9b2b4b0c955c0901fd4ea6d0f07c9ea0b318576`**。本次核读其精确排除条件和输出：247 份指定 JSON 可解析，2 个实际 pytest 父身份 absent／live0／unknown0，另 2 个合成身份与 pid1 出现数分列；同样输入／两安装／wheel／副本仍匹配。

[联合交付](2026-11-16-predecessor-native-final-acceptance.md)已准确更正这项口径，亦只重分类旧 31=29 实际+2 合成和实施者 191=189 实际+2 合成，不转授旧候选的现场收尾。本报告没有全局清点或捕获全部业务子进程的声明。native 直接子调用由原 subprocess.run 等待返回；原 S/H／reaper 的范围按各原记录保持。

至此，两轴 approve 和 R1 关闭只适用于准确 `bc58be6781d35e7e4fbd54ad997df8a4743428a8` 及其 M5 r7 父、显式 source-v2 新安装与上述验收范围。允许普通集成这一产品；CI 四文件配置另由其独立审查负责，本报告没有把 collector、旧候选 CI 或 Windows 未运行项当作正文／平台／时长验收。准确公开候选自己的官方 CI 仍须另记。

所有 schema3／ordinal1 start、create、request、launch、native 正向效果仍关闭；旧 v1／schema1/2／owner／pin／clock 不升级。M6 的正式 producer／runtime、完整 M1c、真实两个新候选 CPU 轮次、schema3 permit／晚阶段正向与故障、GPU／训练质量均留后继同候选验收，不由本报告授予。

## 同片普通集成身份复核

2026-11-16，追加只读身份及冲突处理复核。准确普通合并提交为 `1308e32833c8174351906429902190cbaa2a3aa7`，第一父 `bc35acd9d8d755042205c5626cc4badc52e7a91e`，第二父为已审 native r5 `bc58be6781d35e7e4fbd54ad997df8a4743428a8`，其 M5 r7 父链完整保留。

独立静态重核集成树：665 个完整产品文件的名字、raw bytes／SHA 和执行位均与 native package-r5 的冻结产品及实际 wheel 一致；wheel SHA 仍为 `3c1ddaeb816d20841525d0be1f3139a59d0b62daaa98e14a75857481ce6e2fa7`，`src/ergora` 相对已审候选无差异。855 项冻结输入只有 `scripts/ci/linux-groups.json` 和 `tests/test_training_cycle_controller.py` 两处预期差异。

CI JSON 逐字等已独审提交 `55dc51ccad454d978319a06e38f4fb3a1ce1d70f`，SHA256 为 `8ffe961f3e4578485186d864430b9f93becf5eed81bea37338a6aa0015e685ab`；六组、86 文件的完整 inventory multiset 相对候选不变，无删除或重复。配置的需求／维护性结论沿[原 CI 分组审查](2026-11-16-predecessor-native-ci-balance-review.md)保持，不把合并后的全部 JSON 差异概括为仅本轮四文件搬移。

controller 测试相对已审候选仅增加三条主线已有的 Linux skip，分别位于 `test_schema3_birth_retains_sources_bytes_and_one_clock`、`test_schema3_intent_is_local_and_all_execution_entries_remain_closed`、`test_controller_original_type_is_authenticated_read_only`。全部测试函数集合相同；`test_schema3_native_callback_refuses_before_executor_effects_and_keeps_completed_read` 的完整 AST（含 decorators／函数体）与候选一致，保留 `Managed native callback requires Linux` 及 `['managed', 'managed-v2']` 两种安装参数。冲突处理没有丢失 v2 覆盖、原平台保护或断言。

**准确集成产品继续保持需求符合性 approve、结构／维护性 approve，新增开放阻塞项 0。** 本次只复核同片集成身份与冲突处理，没有新增产品行为，也未重跑安装、测试或 collector；主树 collector 原件与准确公开候选自己的官方 CI 由[联合交付](2026-11-16-predecessor-native-final-acceptance.md)分别记账。本报告不授予新平台／时长／正式 CI 验收，前述 schema3／ordinal1 效果关闭及 M6／runtime／真实两轮／训练／GPU 边界保持。
