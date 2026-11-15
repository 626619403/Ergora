# Q4.2b2 原登记上下文恢复：独立产品评审

日期：2026-11-15。Reviewer：fresh-context agent `training_frozen_recovery_audit`。依据原始八条合同及 R1–R5、仓库三级 `AGENTS.md`、组件变更协议，采用 `maintainable-project-delivery` independent-review brief、`ergora-codebase-quality` 的风格／模块／测试接缝 references；结构判断沿 `codebase-design`。未继承实施讨论或预设结论；实施过程中后送的范围和结果另行核实。

## 当前结论与范围

实施基线及本地评审时的 HEAD 均为 `6531967e6b6dd8d20ff5ad70d7ae3074c81aca35`，分支为 `refactor/architecture-foundations`。r1 至 r4 在本地评审时均为未提交固定产品范围。本报告的最终本地结论绑定固定源码 r4、对应非 editable 安装 r3 和下述实际原件；后续固定发布与自身 CI 的续核见末节。

**最终本地需求符合性：approve；可维护性：approve。需求／维护开放 finding 为 0／0，R1–R5 均已关闭。** 八条限定合同在源码、原 owner 与实际接缝范围内符合；现有测试及 guard 已核必要性，除 R2 已删除的两个不可达 guard 外，无应追加的抽象、测试矩阵或 CI job。完整八 suite 的 197 项绑定源码 r3；最后 r4 仅改变两个状态 owner 的字段投影，重新安装后复验其完整受影响两 suite 的 53 项，不能把两轮视为 250 个独立测试或 r4 重跑全部八 suite。

**发布终核：单行平台范围修复提交 `82ea3f163e0c29759eb6ebef93fb2e58d87e983a` 的固定发布需求／维护两轴 approve、开放 0／0；自己的 Portability run `43658729462`／attempt 1 已实际 completed/success，八 job、30／30 必要步骤全部成功，本片发布门禁关闭。** 原提交 `9c9ffeee…c682` 的真实 CI failure 与旧索引原样保留。下方本地通过结果与 R1–R5 的关闭保持其原范围，两次发布及各自 CI 的证据见末节；不认证后继 B3、真实服务或训练。

|范围|需求符合性|可维护性|开放项|
|---|---|---|---|
|固定源码 r1|request-changes：R1 的重复取消结果丢失所选原登记身份|request-changes：恢复结果身份由通用进程包装补造，遗漏嵌套结果|R1 历史实红保留|
|固定源码 r2|request-changes：R1 已关闭，R3 原竞态 fixture 与 R4 原 import 读取范围未修|request-changes：R2 的两处不可达重复 guard 未删|上述历史问题已在 r3 修正，原失败保留|
|固定源码 r3|request-changes：R5 的部分结果遗漏原 start 修订；原完整安装八 suite 已核 197 passed，R3 关闭|结构 approve；R2 已最小删除，未加新抽象／测试矩阵|R5 的 r3 实红保留，不转记后继修正|
|固定源码 r4|approve：R1–R5 已关闭，最终受影响两 suite 53 passed，当前安装／实际 CLI 已独立核实|approve：仅沿原 owner 修正，未改发送／对账或增抽象；当前源码自身模板亦 approve|本地需求／维护开放 0／0；发布与自己的适用 CI 尚待后续门禁|
|修复发布 `82ea3f16…983a`|approve：只为原 Linux prepare 场景补平台 marker，实际 Linux 场景仍通过|approve：原测试体／断言不变，完整产品树等于已审发布|固定发布开放 0／0；自己的 run `43658729462`／attempt 1 实际 success，八 job／30 必要步骤全成功，发布门禁已关闭|

固定材料位于 ignored `.ergora/checks/training-frozen-recovery/`：四轮 `source-scope-r1/` 至 `source-scope-r4/` 及其同名 `.json/.diff`。每轮均为七份产品 `cli.py`、`reference.py`、`reference_training_cancellation.py`、`reference_training_context.py`、`reference_training_submission.py`、`registrations.py`、`training.py`，以及原三份测试 `test_registrations.py`、`test_training_cancellation.py`、`test_training_submission.py`。逐文件核过大小及 SHA-256；本地终核时 r4 源码／测试与固定副本逐字一致，完整 r4 diff 等于基线至当时十文件的实际 Git diff；r3 核对在固定时成立，后继差异另核。发布后改以精确 commit blob 绑定本片。

|材料|SHA-256|
|---|---|
|r1 scope JSON|`b1bc752fdaeb95da545ce0d678adab8293ffba9a49d9cf8a5eee1794972ab483`|
|r1 完整 diff|`59586522d9e6d550370aa47cfe42e3d8b9036fb5e34f826e9d66965b0a38532f`|
|r2 scope JSON|`caf8da3715abcfe19511639a47a1af6d9c6d8fe8900c1127a3aac657117f56e8`|
|r2 完整 diff|`96b07c09d6b0ffc183f0206ee8030b3135c3e94cb16a7fe60300d7a2e6f5f82f`|
|r3 scope JSON|`67aaefbc357211217cb9231e9e5118045c937889ac778dd5a5f862b3bc994b01`|
|r3 完整 diff|`91d9ab70f64350baa61535158921eb6e643da6c1227c7cad1a5d9c0ae29bd151`|
|r4 scope JSON|`85bbfb9843fd680892e1bd7fce1381eb737e77b38d58be8eab99cafda2ac6f99`|
|r4 完整 diff|`ac6a486652dc08a40cf2f11a35ab2c2e266fac44d876b3aba3febf6836632e85`|

已在内存中按统一 diff 逐 hunk 比较固定 r1 与基线 Git blob，十文件全部还原到固定副本。没有修改产品、测试、计划或其他交付文档。

## R1 / P2：重复原 cancel 的嵌套状态缺少原登记身份（r2 已关闭）

**位置（r1）：** `src/ergora/reference.py:441`、`src/ergora/training.py:287`。

**可达情形：** 用显式旧登记取消原 run，第一次 dispatch 或后续 history 对账返回的顶层状态由 `_training_process` 后附 `original_registration`。以同一 request ID、run 和 reason 再次调用 `cancel` 时，取消 owner 返回 `{'created': False, 'cancellation': status}`；进程包装只给外层加字段，应用 `_cancellation` 第 288–290 行解开 `prepared['cancellation']` 后直接返回，所选原登记的 operation、摘要、execution 与登记 revision 均丢失。本地 `cancellation` 读取却仍带这些字段。

**影响：** 同一原取消的幂等返回不再携带一致来源身份，违反合同第二条的分别呈现要求；调用者无法从该返回审查当前 revision 与旧 execution 的关系。没有证据表明它重发信号或接管新 run，问题限于结果合同与所有权。

**最小修正：** 恢复身份在 `_TrainingProject` 核来源后形成，由 submission／cancellation 的真实状态返回持有；通用进程包装只传输结果。把重复 `cancel` 等于第一次完成状态的断言补进现有旧登记取消旅程即可。

**实证和复审：** 实施者追加原旅程断言后的 `source-context-red-r1` 为 1 failure，pytest 20.602 秒／外层 21.493 秒；独立解析 XML，缺少字段与上述源码路径一致。固定 r2 删除通用进程后附，`reference_training_context.py:40` 形成 `recovery_context`，由 submission 的 status／fence 及 cancellation 的 status／stop-status 返回携带。`source-context-green-r2` 同一断言 1 passed，pytest 21.398 秒／外层 22.293 秒。R1 在源码及该定向接缝关闭；r1 原失败不被覆盖。

## R2 / P3：新 start 的两个内部恢复 guard 在真实调用图中不可达（r3 已关闭）

**位置（r1／r2）：** `src/ergora/reference_training_submission.py:52` 与 `:210`。

**证据：** `run` 第 289–290 行已在调用任何动作前拒绝旧模式的 `prepare`、`check` 和 `dispatch`；允许的 `resume` 又在第 335–336 行拒绝无 attempt 的旧 start，有 attempt 时只进入 reconcile。因此旧模式没有路径进入 `preflight` 或 `dispatch`。全仓 `rg` 核真实 caller：两方法只被本文件的 run／dispatch 调用；cancellation／release 使用 `_Submission` 的身份、读取或状态方法，不调用这两个方法。

**影响：** 两处 guard 无法再保护任何生产可达失败，却把恢复分支散入普通启动算法，维护者须核对三组重复权限条件。它不是身份／外部输入／资源验证，不需要增加动态负例证明不可达分支。

**最小修正与验证：** 删除 `preflight` 和 `dispatch` 开头两段 recovery 拒绝，保留 `run` 的动作白名单、无 attempt 拒绝，以及独立的上层模块白名单与双进程来源校验。复用已有旧模式 prepare／check／dispatch 拒绝和无 attempt 恢复接缝，不增 suite 或 CI job。如另有真实调用入口，按其具体 caller 处置本项。

**修正复核：** 固定 r3 只删两处不可达 guard，原 `run` 动作白名单与无 attempt 拒绝均保留；父／子来源校验和上层模块白名单未动。独立核完整 r2→r3 diff 与真实 caller，R2 关闭；安装完整权限接缝最终结果另核。

## R3 / P2：原竞态测试绕过初始化，未建立新必需状态（r3 已关闭）

**位置（r1／r2）：** `tests/test_training_submission.py:607`。

**可达情形与影响：** 原测试用 `_Submission.__new__` 绕过 `_TrainingProject.__init__`，只设 `project`、`ident` 等部分属性。修改后的 `status` 首先读取 `project_revision`（r1）及 `recovery_context`（r2），fixture 均未设置，导致测试在目标 checkpoint 读取竞态前直接抛 `AttributeError`。这不是普通用户入口失效，但原完整 suite／CI 会失败，且该回归接缝尚未验证其独特并发风险。原 34 项定向未选中此测试。

**最小修正与验证：** 在同一 fixture 设置普通模式的 `recovery_context = {}` 和 `project_revision = operation.project['revision']`，保留原读取／发布交错及两个观测断言。不对产品加 fallback，不写新测试；先保留安装回归实红，再复验原测试及受影响接缝。

**来源与独立核实：** 自身原结构模板 `c4a0513e29e64063a1590e694f191286` 的 51.917 秒成功调用给出 `request-changes`，发现此项；独立评审随后逐行核 fixture 和实际 status 读取，结论一致。模板实际输入为 27 完整文件／534505B、三个祖先资源，属于所给源码文本审查，不认证私有原件、真实服务、CI 或训练。

**实红与修正：** `installed-tests-r1` 197 项中 196 passed、1 failed，pytest stdout 996.11 秒／XML suite 996.079 秒、外层 997.280 秒。独立核 XML，唯一失败正是首 `status` 读取缺少 `recovery_context`。固定 r3 只补上述两个普通模式属性；`source-fixes-green-r3` 原竞态与原 large-import 共两项通过，pytest 5.589 秒／外层 6.424 秒。完整修后安装八 suite 的 `installed-tests-r2` 已终态，固定原 35 文件、197 passed／零失败错误跳过；原竞态 0.012 秒实过，XML suite 1012.472 秒／stdout 1012.64 秒／外层 1013.803 秒。R3 完整关闭；该结果只绑定固定源码 r3，不转授后继 r4。

## R4 / P2：新的聚合值配额拒绝原 native 已支持的成功 import（r3 已关闭）

**位置（r1／r2）：** `src/ergora/registrations.py:90`；既有反例 `tests/test_registrations.py:407`。

**可达情形：** 原 `test_import_adopts_bounded_raw_json_even_when_its_pretty_encoding_is_larger` 将 110000 个短 argv 存在 compact JSON，单份 native 原件小于 1MiB，公开 import 成功并保留原字节。其 journal 含 definition 与 files 中的重复配置，合法原件的树值数超过 100000。新 reader 调 `parse_json(..., bounded=True)`，在核 published 来源前就拒绝该 journal，即使原件低于新的 32MiB 聚合字节界、摘要与 result 一致。父应用因此无法选择原 execution，后续原运行的读取／停止入口均被新配额封住。

**合同判断：** 64 层／100000 值是实施后追加的范围，不是已独立通过的原 r3 八条合同要求。只把这项限制写进手册不能保留原 native 已发表的合法配置；原 2.4MB 容量样本用一条长字符串，不覆盖大量合法短值。这里不是要求取消来源校验或任意 JSON 大小限制。

**最小修正与验证：** 仅从新 reader 移除 `bounded=True`，保留 32MiB／1MiB 实际读取字节界、ordinary-file／no-follow、duplicate／finite JSON、完整 published 身份和 schema／投影验证，不修改公共解析器和原 writer，也不引入新配额层。原树值检查在 `json.loads` 后执行，本来不避免首次解析分配；保留原 Python JSON 自身可解析／序列化范围即可。在既有 large legacy-import 测试尾部增加公开来源读回，另以成功 import 经实际子进程恢复补原顺序验收，无需新测试矩阵。

**处置与源码复核：** 固定源码 r3 仅移除新 reader 的 `bounded=True`，公共解析器／原 writer、字节界、strict duplicate／finite JSON 与完整来源校验均保持；既有 large-import 测试末尾增加来源读回，没有新增 suite／矩阵。活动计划已明确撤回实施追加树配额并保留原因。此项最初作为声明范围观察提出，复核原固定计划 r3 及既有成功 import 接缝后确认为兼容性 finding。

**原安装实红与同原件修后实绿：** `installed-legacy-capacity-red-r1` 5.223 秒、exit 1，stderr 明确在 `published_project` 的树值检查拒绝。独立核 `large-legacy-r1` 的公开成功 import 原 journal 为 3,967,190B、intent SHA／published result 匹配，四份 native 最大 551,122B 且内容等于发布投影；`checks.unused` 共 110001 个 argv 值（`echo` 加 110000 个 `x`）。`installed-legacy-capacity-green-r2` 以新非 editable reader 读取同一红例 journal／result／SQLite published 文档，1.119 秒、exit 0；独立核七个原件当前 SHA 等于记录的读取前 SHA。另以实际无 SDK CLI 子进程成功恢复同时含该大量合法短值和等价非默认 policy 顺序的原 import，详见证据表。没有服务、模型或 runner，R4 关闭。

## R5 / P2：部分恢复结果遗漏原 start 冻结修订（r4 已关闭）

**位置：** `src/ergora/reference_training_cancellation.py:94`、`:205`，`src/ergora/reference_training_submission.py:145`。

**可达情形：** 原登记 revision 为 1，合法 binding 变更后 start intent 冻结 revision 为 2，当前登记为 3。显式旧登记 `cancel`、`cancellation`、`resume-cancel` 和 `stop-status` 的真实状态 owner 只返回当前 `project_revision` 及 `original_registration.registration_project_revision`，没有返回已核 `self.start['project_revision']`。同样，`_Submission.status` 的 rejected 分支在后方添加 `submitted_revision` 之前返回，因此这个合法本地读取状态也缺少原 start 修订。普通 prepared／unknown／submitted 与 fence 分支则已有该字段或 `intent_project_revision`。

**影响与合同：** 固定计划第二条要求原登记／冻结 start／当前项目修订分别呈现；手册第 304 行明确把这项结果说明用于上述全部恢复命令。缺字段使调用者无法从该次结果审查三个 revision 的关系，尤其不能用取消 intent 的当前 revision 代替 start 修订。没有证据表明它选择了错误 run、改变权限或重发操作，问题限于恢复结果合同。此前“r3 无新源码阻塞项”的暂结论据此撤回；自身模板 approve 不覆盖此遗漏。

**最小修正与验证：** 在现有 `_Cancellation.status`／`stop_status` 从已验证的原 start 返回 `submitted_revision`，并在 `_Submission.status` 的所有已有 intent 分支保留该字段；不在通用进程包装补造，不新增 fallback／抽象。复用现有旧登记取消、停止观察及 rejected 状态接缝补断言，使登记／start／当前修订真正不同，不另建 suite 或矩阵。r3 原取消旅程让登记和 start 同为 1、当前为 2，且没有三 revision 断言，不能证明本项。独立评审仅作源码／合同及原件复核，没有自行运行反例或改产品、测试。

**实红与 r4 修正：** 实施者接受后，`source-revisions-red-r3` 在原 r3 非 editable 安装上执行新增的既有旅程断言，四场景均因 `KeyError: 'submitted_revision'` 实红；独立解析 XML，4 failed／49 deselected，pytest 44.657 秒／外层 45.572 秒。固定 r4 只在取消的两个真实结果及 submission 已有 intent 的共同结果补该字段，保留原发送逻辑；原取消 fixture 在 start 前增加一次合法 binding 修订，两个恢复旅程和既有 other-actor 拒绝的两个场景都核登记＜start＜当前修订。`source-revisions-green-r4` 同四场景 4 passed／49 deselected，pytest 74.146 秒／外层 75.071 秒。独立比较 r3→r4 全部 hunk，源码修正充分。当前新安装 `installed-tests-r3` 的完整受影响两原 suite 已终态 53 passed／零失败错误跳过，四个原红场景全部实过，XML 469.774 秒／stdout 469.82 秒／外层 471.034 秒、exit 0；R5 完整关闭。

## 已核合同、结构与测试价值

- **来源 owner 与容量。** `registrations.published_project` 由 `training._project` 在父应用选择 execution 前调用，再由 `_TrainingProject` 在子进程调用；两个真实生产文件共享一个合同。其私有 `_recovery_document` 隐藏 ordinary-file、链接／reparse、字节与严格 JSON 读取算法，单 owner 合理。没有新表、恢复账本、转发文件或第二客户端。核完整 journal SHA、published result、operation、registration SHA、四文件投影与 control home；仅规范 execution policy 的 allowlist 顺序。
- **实际容量原件。** 独立只读核 `journal-capacity-r1` 的 2,406,792 字节 journal 原始 SHA、canonical intent SHA、published result 与四份 native 内容，均与记录一致，单份最大 600,389 字节。32MiB journal／1MiB result 是分别声明的实际字节界，超限拒绝。额外树配额已按 R4 移除。该实证没有训练、runner 或服务主张。
- **读取兼容性。** 2.4MB 长字符串容量原件没有覆盖原成功 import 的大量短值；R4 单列这项真实支持差异，原生四文件大小限制与新聚合字节界仍须各自保留。
- **默认与旧模式。** 默认 `_TrainingProject.registration` 的四文件及 control home 校验保持；旧模式先核原 journal，不能靠外部 cycle 或通用 ignore 开关进入。七 CLI 组合选择／确认，未给 start／prepare／check／runner／批准恢复选项。原 prepared 只可读或显式 fence；旧 resume 必须有原 attempt。
- **修订与两阶段。** 原登记 revision 留在来源上下文，本次当前 revision 在应用事务内确认，取消新意图记录该当前 revision。submission／取消／停止观察均返回原 start 的 `submitted_revision`，fence 返回 `intent_project_revision`；r3 的部分输出遗漏已按 R5 在 r4 修正。当前项目已不选 training 时，旧登记入口不误用默认模板检查。`_submission`／`_cancellation` 退出 DB reservation 后才 RPC；`_setup` 只承载本地 fence。
- **unknown 和取消。** start reconcile 沿原 workflow、完整初始 Experiment、memo；NOT_FOUND 不清 attempt、不重发。取消继续用原固定 run、actor、request、reason、attempt-before-send 与信号历史。服务替身调用链使用真实 SDK 编解码及原 owner，但没有真实 Temporal 服务验收含义。
- **native 停止路径。** 独立读过参考 `LocalTrainingAdapter.lookup_job`／`poll_job`／`fence_and_lookup` 的实际文件访问：旧 mode 不重新读取当前 manifest／runner。新增 request 的 canonical job ID 与 started／result 的 binding／job ID 检查、fence 精确对象及原 `safe_file/document`，覆盖直接 native reader 曾信任的路径和身份；完整 Experiment 继续由原 adapter 核对。结果明确分开 control、executor observation、fence，不证明 OS／后代停止。
- **安装和连接。** 原 `validate_installation(training=True)` 保持参考 Python 身份校验；`core.environment` 固定 loopback `127.0.0.1:7233`、namespace `default` 和本地 adapter，不随 ambient endpoint 切换。服务 history／memo 缺失保留未确认；没有自动重建、迁移或替代服务。
- **结构与检查成本。** 无新增产品文件或跨层具体后端分派。新回归留在三份已有 suite，原 CI 已显式收录，未加 job。聚合容量、来源冲突、换登记执行目录、三 revision、unknown 单次发送、native 路径、嵌套幂等结果都能暴露静默错误；没有发现应删的重复测试。R2 是本轮发现的重复 guard；其他新增 guard 对应来源／持久身份／确认／操作权限的可达失败。
- **性能影响。** 显式恢复的父应用与子进程各自重新读取／解析／哈希 published 来源，增加有实际字节上界的本地工作；两处检查分别保护选择旧 execution 前与原安装执行内的来源，不能按重复 guard 删除。旧模式没有全目录搜索、额外数据库或后台轮询，普通模式仅增加常数字段。原容量、CLI 与 suite 时间是合同运行证据，未作对照基准，不能据此宣称性能收益或量化无回退。
- **保留项。** 独立按 manifest 核 283 份参考文件零 mismatch，并核相对基线无变化。v3 根及 kernel assessment／designer 路径未变，v3 仍保留 kernel 叶，允许评估无需 kernel 修改。没有训练、GPU、质量、收益、预算闭合或自动循环主张。

## 已收证据与尚缺验收

独立评审仅运行轻量只读哈希、JSON／XML／diff 解析与 Git／源码检查；没有执行 suite、安装、服务、模型、训练、commit、push、GitHub 写入或取消 CI。运行结果来自下列实际原件，按范围记录：

|原件|已核结果与限度|
|---|---|
|`source-recovery-r1.json/.xml/.stdout`|固定 r1 源码定向 34 passed／80 deselected；pytest 235.970 秒／外层 236.906 秒。逐项核 XML；**未选中** `test_import_preserves_legacy_bytes_tasks_and_compatible_policy_order`，不能把成功 import 顺序归入这 34 项。|
|`source-context-red-r1`／`source-context-green-r2`|R1 同一旅程实红、修后实绿，详见上文；不代替完整 r2 回归。|
|`package-r1-core.json`／`package-r1-sdk.json`|独立实际读取 source、wheel 两安装全部 645 份产品，零多项／缺项／字节差异，均绑定固定 r2；wheel SHA `96257a7d228cf08cbd51c422b09600c494c63dc3eff272399be7db26f388cc10`。core 无 temporalio 路径，SDK 为 1.34.0；283 参考与依赖检查原件通过。安装编号 r1 不表示安装的是源码 r1。|
|`native-journey-r1`|12 条实际隔离安装 CLI，外层 25.998 秒；逐条核 stdout／stderr SHA 与退出码。57 原文件零改动、DB 前后 dump 与当前只读 dump 一致，仅所选 `candidate-a` fence 新增；原登记／start／当前 revision 为 1／2／3，旧上下文读回及 fence 幂等，无 attempt，无新 state 目录。拒绝缺确认、错 SHA、SDK 缺失、旧 revision、缺原 intent、旧 start 选项；没有服务／runner／训练调用。|
|`installed-tests-r1`|197 项中 196 passed／1 failed，唯一 R3 fixture 实红，原件保留；详情见 R3。|
|`source-fixes-green-r3`|原竞态与原 large-import 两项源码通过，5.589 秒；不代替完整安装回归。|
|`package-r2-core.json`／`package-r2-sdk.json`|新 wheel SHA `159b0469a7d86bf0b3b167ba479e135f53ffe03df4c7fab05d54ee031b3d37aa`。独立再次实际读取两安装全部 645 产品，与 source／wheel 零差异、零额外文件，绑定固定源码 r3；core 真无 SDK、SDK 1.34.0、依赖通过，283 参考保持。|
|`native-journey-r2`|新安装 12 条实际 CLI，26.498 秒；独立核 12 stdout／stderr 摘要，57 原文件与 DB dump 保持，只新增所选 candidate-a fence；三 revision 1／2／3、旧 execution、原 intent 和无新 state 均核。|
|`native-journey-import-r1`|19.942 秒，公开成功 legacy import 含 110001 argv 与 `['repository-governance', 'large-change']` 原 policy 顺序；新 core 无 SDK 的单条实际 CLI 子进程恢复成功。独立核原 journal／result／start SHA、输出摘要、三 revision 1／2／3；57 原文件与 DB dump保持、无新增文件／新 state。关闭原成功 import→子进程验收缺口。|
|`installed-tests-r2-scope.json`／`installed-tests-r2`|固定源码 r3 的八 suite 与 helpers／fixtures 共 35 文件；独立逐份核摘要，三份改动测试等于 r3 固定源码，索引 SHA `acb6a7e30763e08af8d241284de26204b2cfc20c53d80f8f2ce277b634bf9638`。原固定副本实际终态 197 passed／零失败错误跳过；八 suite 分别 61／13／15／40／15／13／13／27 项，XML 1012.472 秒／stdout 1012.64 秒／外层 1013.803 秒、exit 0、stderr 空。唯一已有 TestClient 弃用提示；原竞态与 large-import 实过，不把后继 r4 测试改动转记此轮。|
|`self-review-r1-codex`／`self-review-r2-codex`|首轮 succeeded／request-changes，R3 已独立确认。修后原模板 run `45cdc5becb614b48b5cdd937b89fda21`，49.414 秒、succeeded／approve；独立逐份核 27 完整文件／538411B 的 scope 哈希、完整 diff 与 task、实际 stdin 等于 prompt，三个祖先资源完整进入 stdin。input digest `04d5f6611962807c62a8ec10a8600ec266671e9ec806b5414dc351af18b328d5`；原 result 与 run result 逐字相同、SHA `d9686f7613a44288a433166d05cbc3ebbab6be08e1ddc14d2953eb3189413aa5`。仅认证此文本审查原件，不将其 approve 转授 R5、私有原件、安装运行或 CI。|
|`source-revisions-red-r3`／`source-revisions-green-r4`|R5 同四个既有旅程场景实红与修后源码实绿，分别 44.657／74.146 秒；原 XML／stdout 保留，详见 R5，不代替新安装完整受影响 suite。|
|`package-r3-core.json`／`package-r3-sdk.json`|对应固定源码 r4；wheel SHA `159b990ad50d8727626e64d8f5971ad3fed7fcab0b6b17d29d54b64ca1efe803`。独立实际读取 source／wheel／两安装各 645 产品，零字节差异、零额外／缺失文件，清单哈希全匹配；core 无 temporalio 模块或 metadata，SDK 为 1.34.0。283 参考 PASS 原件及依赖检查均通过；安装编号 r3 不表示源码 r3。|
|`installed-tests-r3-scope.json`／`installed-tests-r3`|对应固定源码 r4 的八 suite／helpers／fixtures 共 35 文件，独立逐份核摘要及当前工作树零差异；索引 SHA `640a4c7938f1437dd53230b5d9dabc2322781987943fea25ff04b897bf2b66ac`。本轮实际受影响的 submission／cancellation 两原 suite 共 40／13 项，终态 53 passed／零失败错误跳过，XML 469.774 秒／stdout 469.82 秒／外层 471.034 秒、exit 0、stderr 空；唯一已有 TestClient 弃用提示。R5 四个原红场景全部实过。终核重新确认 r4 十文件仍等于固定副本、完整 diff 等于实际基线 diff；原 r3 八 suite 结果不混记。|
|`native-final-r3`|当前源码 r4 的新非 editable 安装实际执行三条 `-I -B` CLI：core 原普通 submission、SDK 原同 binding fence 幂等、core 原成功 legacy import submission；6.224 秒、均 exit 0。独立核三 stdout／stderr SHA 与原期望结果逐字一致，三修订均 1／2／3；两 case 全部 370／346 文件 inventory 与记录相等，无额外文件，SQLite 只读 dump 等于各自原 before。无需服务／模型／runner，不把本地重读计为真实服务验收。|
|`self-review-r3-execution`／`self-review-r4-codex`|首个当前源码驱动 2.019 秒、exit 1，误改外部 `inference.toml` 来源路径导致 `FileNotFoundError`；独立核 stderr、无 native stdout、无 run record，未发模型调用，失败原件保留。只修 ignored 驱动路径后的 run `2dbe52a6edcc47adb36fd6f671d2d760`，37.056 秒／外层 39.567 秒、succeeded／approve。独立核 27 完整文件／545016B、完整 diff 与 task、三祖先资源均在 stdin，stdin 等于原输入及冻结 run prompt，task／prompt 摘要匹配 request。input digest `ff6bc64ec81bba42cb24cc9c3c3a635109aea47dc0b49a29894169e380dae5ea`；原 result 等于 run result，SHA `3c40b6cf799384ef5097c3b817850fbc8e13ebaa3be890988f32cd761c4192e1`。实际回复明确检查 R5 的取消／nested／rejected／stop 返回；范围仍是所给完整源码文本，不认证私有原件或运行。|

最终本地需求与维护两轴验收已完成。原 r3 完整安装八 suite、r4 受影响两 suite、各实际红绿、当前源码自身原模板、两新安装、当前安装三条重读与前轮普通／成功 legacy import 的实际 CLI、同一容量红例修后读取均已独立核过；结果范围分别记录，没有沿用旧候选的通过结果认证新改动。错源／错 home／operation／摘要／缺 result、actor／同 ID 异 Experiment／job／run／memo、symlink 和超时丢回复分别沿原接缝覆盖，无需复制新 CI 矩阵。

真实服务调用与 SDK 服务替身须继续分列，当前未见真实服务证据。本片不要求以 B3／GPU 或完整训练循环代替上述合同验收；不可续期预算、全周期资源停止、Temporal 父循环、真实 CPU 循环及真实 B3／完整 Forge 保持原后继义务。

## 固定发布与自身 CI 续核

普通发布提交为 `9c9ffeee517deff2ec8cd2ffe572744e3c2cd682`，parent 为 `6531967e6b6dd8d20ff5ad70d7ae3074c81aca35`，tree 为 `42c267272c6b427e8e8aa2d82f493bd3cb5cf298`。**固定发布需求与维护两轴 approve，身份开放 0／0；自己的 CI 已实际失败，验收为 request-changes，开放失败门禁 1 项。** 本节仅认证该精确提交及其自身 run，不跟随后继 b3 工作树变化。

独立核了全部 20 个实际 commit blob，逐份等于 `staged-r1.json`、`publication-r1-local.json`；完整 `staged-r1.diff` 等于基线至提交的实际 diff。七产品／三测试逐字等于本报告已审固定源码 r4；提交内全部 645 产品与最终 wheel `159b990a…efe803` 及两个安装相等。其余十文档为本片说明／记录、b1 终态同步和独立已审 b3 计划文档；b3 发布计划相对其固定 r2 原件仅同步审查状态，没有 b3 产品变更或运行认证。本报告在提交内的 blob 为 `41977923f5ad6d96e4188ab6b55e7681643ea1e9`，27953B／SHA `3d7f5af0b78847bca126da0b58fac07ac0083d66cdbf455a05e5ef0d85e9bedc`；此续核是后追加记录。

匿名官方 GitHub HTTPS GET 的 commit、完整 branch ref、runs、run、jobs 和 run HTML 六响应均 200，保留实际响应、元数据和 SHA；官方 parent／tree／20 文件 blob 与本地匹配，`refs/heads/refactor/architecture-foundations` 的完整 SHA 为上述新提交，另与普通远端 Ref 读取原件一致。只读采集、验证和响应原件在 ignored `.ergora/checks/training-frozen-recovery/ci/`；没有取消 CI、平台写入或重跑测试／模型／服务。

|固定证据|结果／SHA256|
|---|---|
|`ci/reviewer-publication-local-r1.json`|20 blob、r4 十文件、645 产品及最终两安装一致；`18123ca3a19ae36de0d3194ce45af4e963249c097a16cea395c7d05f3126639f`|
|`ci/reviewer-official-publication-r1.json`|官方提交／完整 Ref 与固定本地身份一致；`a20121f3f065a3517b4fa2525ce9ab996e31f323df20335d8bac2b71de940072`|
|`publication-r1.json`|普通发布及远端精确 Ref 原件；`9d92d00ef4160de938fd8bbb00bfb85a674aeec1c53daff42d00ecf61a4e1902`|
|`ci/reviewer-observe-r1/`|本提交唯一 Portability run [43655794070](https://github.com/626619403/Ergora/actions/runs/43655794070)，attempt 1、push、原分支及 `.github/workflows/portability.yml`；初次观察 `in_progress`，八 job／30 必要步骤已核身份，22 步已成功，未认证终态。|
|`ci/reviewer-observe-r2/validation.json`|第二次实际响应的同一 run／attempt 身份无冲突，plan 与 Linux group 2／3／4 已成功，25／30 必要步骤成功；run 仍 `in_progress`。|
|`ci/reviewer-observe-r3/validation.json`|第三次实际响应已核 plan 与六个 Linux job 全部成功、28／30 必要步骤成功；仅 Windows all 仍运行，无失败或身份冲突，run 仍 `in_progress`。|

适用范围由该提交中的原 portability workflow 与六组 `scripts/ci/linux-groups.json` 固定：plan、六个 Ubuntu／Python 3.11 group、Windows／Python 3.12 all，共八 job。必要步骤共 30 个：plan 的显式分组读取；七 native job 各自 Python 设置、wheel 构建安装、打包参考身份和原回归；另加 Windows PowerShell 5.1 安装／升级。以下终态已逐个核 API 与官方 job HTML 的同一 SHA／attempt／状态／步骤及精确开始结束时间；历史在途观察保持。

### 本提交实际 CI 终态：失败，不能转记成功

run `43655794070`／attempt 1 在 `2026-11-15T00:20:38Z` 为 `completed/failure`。独立终态采集 `ci/reviewer-terminal-r1/` 中，run／jobs API、run HTML、八份 job HTML 及 terminal ref 共 12 个响应均为官方 HTTPS GET／200；加前序观察共 33 个独立响应，全部原始字节／大小／SHA 与元数据相符。八 job 身份无冲突，30 个必要步骤在 API／HTML 的名字、序号、conclusion 与时间逐份匹配；29 步成功、1 步失败。

|job|ID|终态|
|---|---:|---|
|plan|132633893085|success|
|Ubuntu 3.11 group 0|132633921420|success|
|Ubuntu 3.11 group 1|132633921453|success|
|Ubuntu 3.11 group 2|132633921410|success|
|Ubuntu 3.11 group 3|132633921400|success|
|Ubuntu 3.11 group 4|132633921403|success|
|Ubuntu 3.11 group 5|132633921394|success|
|Windows 3.12 all|132633921393|failure|

Windows 的 `Native application regression` 为 `failure`，`2026-11-14T23:58:45Z` 至 `2026-11-15T00:19:41Z`；随后 `Windows PowerShell 5.1 installer and upgrade` 在 `00:19:41Z` 至 `00:20:33Z` 实际成功，job 在 `00:20:37Z` 结束失败。wheel 构建／安装及参考身份步骤均成功，不能用这些事实代替失败的回归。

公开 Windows HTML 的 annotation 原文为：

```text
FAILED tests/test_training_submission.py::test_original_registration_is_rechecked_in_the_selected_training_process - ValueError: Native training submission requires Linux; use the registered runtime in WSL2
= 1 failed, 1176 passed, 819 skipped, 16 subtests passed in 1253.82s (0:20:53) =
```

同页还有 `Process completed with exit code 1.`。原件 `ci/reviewer-terminal-r1/job-132633921393-page.body` 的 SHA 为 `7c1446b6c081bed17f1ee7895c9750426afa064181a7f3ab881140ccf1184820`；完整公开 DOM 文字保留为 `ci/reviewer-windows-terminal-text-r1.txt`。页面提示完整日志需登录，本评审未切换身份或取用凭据；上述具体失败确在匿名公开 annotation 中，已交实施者定位。terminal ref 仍为原完整 `9c9ffeee…c682`，未将后继 WIP 或其他 SHA 的结果混入。

终态验证原件 `ci/reviewer-ci-terminal-r1.json`，SHA `4562a8511d5b9a46b234ba9d761ce5ceef6f7c079ad924a98c97dad9ea99d4df`，身份／字节／HTML 对账 `violations=[]`、`evidence_integrity=approve`，实际 `ci_verdict=request-changes`。验证器 exit 1 对应该真实失败门禁。首次辅助验证曾因把并行根代理的另一格式诊断元数据纳入通配范围而 `KeyError: started_at`，未产出结论；已限定只认证本 reviewer 前缀原件，错误记录与原脚本保留在 `ci/reviewer-verifier-error-r1.json`，不与产品或 CI 的失败混淆。

独立终态索引 `ci/reviewer-verification-index-r1.json`：120 文件／5,541,877B，索引 27,027B／SHA `4ae3d930ea781513acdb341acd34e2e77904265c78bba13b82e8abfbc9369707`。已独立逐项重算全部 120 条大小／SHA，零差异；它覆盖本 reviewer 的原始响应／元数据／验证脚本及固定发布、本地验收锚点，保留 `own_ci_verdict=request-changes` 和一个失败步骤。活动报告不入索引以避免循环身份，后继产品不获认证。实施者须以固定发布基线最小修正、保留此失败并重新完成修复提交自己的适用 CI；本次没有取消或重跑 CI、修改测试／产品、合并、提交或推送。

### Windows 单行范围修正：源码两轴 approve，修复 CI 尚未认证

同 reviewer 按追加授权，只读审查固定 `9c9ffeee517deff2ec8cd2ffe572744e3c2cd682` 测试的单行修正及其 Linux 原件。**该限定源码需求符合性 approve、可维护性 approve，源码开放 0／0。** 上述发布提交自己的 CI failure 保持；本节不认证尚未提交的修复之发布、Windows 实测或自身 CI。

原失败测试首先调用 `reference.training_submission(..., 'prepare', ...)`，固定提交 `src/ergora/reference.py:384` 明确对非 `status` 的原生提交操作要求 `sys.platform == 'linux'`。测试在 Windows 尚未到达它要验证的“所选子进程重新核来源”就因该正常平台边界失败。修正在该测试前增加一行 `@pytest.mark.skipif(sys.platform != 'linux', reason='Original training preparation requires Linux/WSL2')`，与相邻原生 prepare／preflight 测试的范围一致；无需放宽产品平台或来源 guard。

独立核 `ci/windows-fix-r1/baseline.py` 逐字等于该提交的原测试 blob；`fixed.py` 恰好只插入这一个 marker。去掉新增 decorator 后，完整文件 AST 与基线相等；原测试体、fixture、全部断言及其他测试均未变，未新增 xfail、测试矩阵或 CI job。固定 35 份原测试／helper／fixture 的文件集合等于原最终 r3 安装测试 scope；每份摘要、长度均匹配，除目标文件这个 marker 外，逐字等于固定 `9c9ffeee…c682`，未混入后继 B3 测试或当前 WIP。

|修正证据|身份|
|---|---|
|原完整测试文件|48166B／SHA `26a2144830fb91dc3bcaac9ef1a3ea0ca3e82b7cf46f76f2040d44dfd69bc20e`|
|修后完整测试文件|48271B／SHA `ef09df7881066b3ccb1652d4583f8731a36cbcae1fd120d37b59e9e69e07f460`|
|`ci/windows-fix-r1/changes.diff`|SHA `b4fcd9268dc29352d088fe7c986d4f623ee32cc8245ff4b8ff525ec57f8ce009`|
|`ci/windows-fix-r1/identity.json`|SHA `785086415a27e05f527c1689d4ce8c9235c4299352a4b44f8e5ef648a715bb3b`|
|`ci/windows-fix-r1/scope.json`|35 份固定原文件／SHA `6e8a2a1d34e8af46748f5206c463cd2c41aabf427492aae4f12e9f0f6ca9f378`|

实际 `ci-windows-fix-source-r1` 使用原 b2 最终 r3 非 editable SDK 安装，以 `-I -B` 执行固定副本中的这个原场景。独立解析 `ci/windows-fix-r1/linux.xml`：1 passed／39 deselected，无失败、错误或跳过，XML suite 3.620 秒／外层 4.423 秒、exit 0；目标 testcase 实际执行，未被 marker 隐去。静态条件求值为 Linux=false、win32=true、darwin=true，仅认证条件与原平台边界一致，不冒称 Windows 实测。评审没有运行应用／测试／安装／模型，没有修改产品、测试、其他交付文档或 B3 WIP；后续须以这个固定 baseline 测试 blob 单独发布并核新 SHA 自己的适用 CI。

### 单行修复固定发布与自身 CI 续核

后续普通发布为 `82ea3f163e0c29759eb6ebef93fb2e58d87e983a`，parent 为上述实际失败提交 `9c9ffeee517deff2ec8cd2ffe572744e3c2cd682`，tree 为 `0b8b5312d557642bd5257105561e76fbd01ee976`。**该精确修复发布的需求符合性 approve、可维护性 approve，身份开放 0／0。** 初核时新提交自己的 CI 为 pending，以下在途原件保持，实际成功终态另列；首次 failure 原件与索引不改写。此节续核前一节尚未提交时的状态。

独立逐份核全部四个实际 commit blob，等于 `ci/windows-fix-r1/publication-staged.json`、`publication-local.json`，完整 staged diff 等于 parent 至该提交的实际 diff。四份仅为已审 marker 测试及三份交付／评审记录；目标测试 blob `c0df7165f0a019d6ad0c27144cd02e1a00f4ed41` 的 SHA 为 `ef09df7881066b3ccb1652d4583f8731a36cbcae1fd120d37b59e9e69e07f460`，逐字等于已审 `fixed.py`。新旧提交的完整 `src/ergora` tree 均为 `1b307e382143ed97ecb79463b475701be91a5abc`，没有 B3 产品、当前 WIP 或其他产品变更。本报告在新提交内的 blob 为 `d12ed4b439444b65723fba33ed62909ad0ecce53`，SHA `4fa07d6159580f29977083dcd8cc53c3c805586238e7af615eba092c00e232d6`；本节为后追加记录，不改称该已发表 blob 已含此节。

匿名官方 GitHub commit、完整 branch ref、runs、run、jobs、run HTML 六份发现响应均 200；官方 parent／tree／四份 blob 与固定本地身份相等，官方完整 Ref 与独立普通远端 Ref 原件均指向 `82ea3f163e0c29759eb6ebef93fb2e58d87e983a`。只读身份核实不借用另一 SHA 或后继工作树的运行结果。

|修复发布证据|结果／SHA256|
|---|---|
|`ci/windows-fix-r1/reviewer-publication-local-r1.json`|四 blob／完整 diff／固定 marker 与产品 tree 一致，`issues=[]`；`181514f7b98ed92b0f0acf714ab5cc279fa42aa509684dd3fb60287e4f5e5a03`|
|`ci/windows-fix-r1/reviewer-official-publication-r1.json`|官方身份、完整 Ref 与唯一自身 run 对上，`issues=[]`；`702c444f8e574689fe38a8c178efbf6915a565fb078a0c7c1de2af5700efc531`|
|`ci/windows-fix-r1/publication-staged.diff`|完整修复发布 diff SHA `3083510ecaeded92ac70a3964d9469273986c51cf62a92794ca8a5ac1bead993`|
|`ci/windows-fix-r1/remote-ref.txt`|完整精确 Ref 原件 SHA `e25c47ad99fc43db0aeb26036fd89aeac0e4b62a96bd26e4ca05e1999ccaccd6`|
|`ci/windows-fix-r1/reviewer-observe-r1/`|新自身 [Portability run 43658729462](https://github.com/626619403/Ergora/actions/runs/43658729462)，attempt 1／push／原分支／原 workflow；采集结束 `2026-11-15T00:34:21.611898Z`，run 为 `in_progress`，八 job 身份一致，22／30 必要步骤成功，无终态认证。|
|`ci/windows-fix-r1/reviewer-observe-r2/validation.json`|隔数分钟后第二次实际采集结束 `2026-11-15T00:38:30.614377Z`；plan 与 Linux group 0／1／2／3／4 均 success，group 5 和 Windows all 在途，27／30 必要步骤成功，`violations=[]`，run 仍 `in_progress`。|
|`ci/windows-fix-r1/reviewer-observe-r3/validation.json`|第三次实际采集结束 `2026-11-15T00:42:01.612383Z`，与前次隔约 3.5 分钟；同六个 job success、两 job 在途、27／30 必要步骤成功，`violations=[]`，无终态认证。|
|`ci/windows-fix-r1/reviewer-observe-r4/validation.json`|第四次采集结束 `2026-11-15T00:45:18.216253Z`；plan 与六个 Linux job 全部 success，28／30 必要步骤成功，仅 Windows all 仍运行，`violations=[]`。|
|`ci/windows-fix-r1/reviewer-observe-r5/validation.json`|第五次采集结束 `2026-11-15T00:48:32.627909Z`；仍为同七 job success、Windows all 在途、28／30 必要步骤成功，`violations=[]`，没有新增失败或终态声明。|
|`ci/windows-fix-r1/reviewer-observe-r6/validation.json`|第六次采集结束 `2026-11-15T00:51:39.735368Z`；同七 job success、Windows all 在途、28／30 必要步骤成功，`violations=[]`，run 仍 `in_progress`。|
|`ci/windows-fix-r1/reviewer-observe-r7/validation.json`|第七次采集结束 `2026-11-15T00:54:59.539687Z`；同一提交／attempt 已 `completed/success`，八 job／30 必要步骤全部 success，`violations=[]`；随后独立采集八 job HTML 与 terminal Ref，见下。|

本次沿同一 workflow 的八 job／30 必要步骤核新提交自己的实际终态；前一失败 run `43655794070` 的 120 文件索引 `4ae3d930…69707` 保持原字节和 `request-changes`。本评审仅作只读观察与证据解析，不运行测试、安装、模型、服务，不触及 B3 产品或其验收。

### 修复提交实际 CI 终态：成功，发布门禁关闭

run [43658729462](https://github.com/626619403/Ergora/actions/runs/43658729462)／attempt 1 在 `2026-11-15T00:54:43Z` 实际为 `completed/success`，绑定完整 `82ea3f163e0c29759eb6ebef93fb2e58d87e983a`、push、`refactor/architecture-foundations` 及 `.github/workflows/portability.yml`。终态采集 `ci/windows-fix-r1/reviewer-terminal-r1/` 于 `2026-11-15T00:55:12.742668Z` 完成：run／jobs API、run HTML、八份 job HTML、terminal Ref 共 12 响应均官方 HTTPS GET／200。连同六份发现响应和其后六轮三响应观察，共 36 个独立响应，全部原始字节、大小、SHA 与元数据一致。各次进度采集相隔至少数分钟；终态采集用于对账已观察到的完成状态。

|job|ID|实际终态|
|---|---:|---|
|plan|132643032877|success|
|Ubuntu 3.11 group 0|132643079512|success|
|Ubuntu 3.11 group 1|132643079528|success|
|Ubuntu 3.11 group 2|132643079505|success|
|Ubuntu 3.11 group 3|132643079584|success|
|Ubuntu 3.11 group 4|132643079519|success|
|Ubuntu 3.11 group 5|132643079514|success|
|Windows 3.12 all|132643079529|success|

30 个必要步骤逐个匹配 API 与官方 HTML 的同一 SHA／attempt、步骤名称、序号、conclusion 和精确开始结束时间，全部 success，`failed_steps=[]`。Windows wheel 构建安装、打包参考身份均 success；原失败的 `Native application regression` 在 `00:34:04Z` 至 `00:53:50Z` 实际 success，随后 `Windows PowerShell 5.1 installer and upgrade` 在 `00:53:50Z` 至 `00:54:38Z` 实际 success，job 在 `00:54:43Z` 成功完成。只据真实步骤状态认证其 CI 合同，不借前次公开失败的 pytest 数量填作本次测试计数。terminal 官方完整 Ref 仍指向精确 `82ea3f16…983a`，没有后继推送或其他 SHA 的结果混入。

终态独立验证 `ci/windows-fix-r1/reviewer-ci-terminal-r1.json` 为 55,690B／SHA `01582c4841538f1a4c69e2e3a9be14a1995a950f6c91cf9773193d821a6f3f95`，`violations=[]`、`evidence_integrity=approve`、`ci_verdict=approve`，验证器 exit 0。四份采集／验证／索引脚本均逐份匹配预先固定的 provenance 摘要，并静态解析通过；本次没有运行 suite、安装、应用、模型、服务，没有重跑或取消 CI、平台写入、commit 或 push。

最终修复证据索引 `ci/windows-fix-r1/reviewer-verification-index-r1.json`：107 文件／3,669,064B，索引本身 25,848B／SHA **`59f5d07b69cbbeb21c98e1308a11412b8b4570dbde3e4ee0bfe003ef4cc8cc1d`**。独立在索引生成后重新读取全部 107 条原件、计算长度与 SHA，零差异；结果 `reviewer-index-rehash-r1.json` 为 706B／SHA `83f07f8fa3a33dee3e97ac449de696697acfcd8c693d1a53bb58018105709378`，`issues=[]`／approve。该后验记录单列于索引之外；活动报告也排除，避免循环身份。索引连接原失败索引，重新核其 SHA 仍为 `4ae3d930ea781513acdb341acd34e2e77904265c78bba13b82e8abfbc9369707`，首次 failure 没有删除或转记为绿。

**该固定修复提交的需求符合性 approve、可维护性 approve，开放 0／0；自身适用 CI 实际 success，发布失败门禁已关闭。** 本地源码／安装与实际 Linux 场景的证据仍各绑定原固定范围，后继 B3 提交和工作树不获转授。本次不新增真实 Temporal 服务、runner、训练、GPU、性能、OS／后代停止或完整循环认证。
