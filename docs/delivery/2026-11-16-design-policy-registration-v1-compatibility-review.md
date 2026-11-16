# WA5-S1 最终兼容修正版独立源码审查

2026-11-16。审查者：fresh-context agent `/root/design_registration_v1_compatibility_review`。先读原始要求、D1–D4、原合同及真实 caller，再读作者说明。产品只读；除本报告外，仅按主控追加的明确授权，在专属 `reviewer-native-resolution-r1` 目录运行、记录最小隔离反例，没有修改产品或原测试。

**需求符合性：request-changes；结构维护性：request-changes；开放 finding：1 项 P2。** 已修的 State 项目缺失／repo 错配与历史 status/resume 问题可关闭，但相邻的 native 项目查找仍被提前移出原回执 owner。新的真实安装对照确认：合法旧 job 的 native 配置丢失后，当前候选不再发布原 `FAILED` 终态。此前源码／安装通过不覆盖这一失败路径。

## 固定输入与完整范围

|输入|实际核对|
|---|---|
|产品树|只读 `.ergora/worktrees/design-policy-registration-fixed-r3`；baseline `c540939d3b3f38f3851b0de965c9cd0f969eea77`；HEAD `80cb39cbc29b7e800a2dfefb09538732eecb5a68`；工作树 clean，无未跟踪产品文件。|
|完整 diff|`.ergora/checks/design-policy-registration/fixed-r3/source.patch`，SHA256 `bbebaaa0435e7f5af8743ae597909723c3781387e083908dec91e0b23cd38af2`；与本轮 `git diff --full-index --binary <baseline> HEAD` 原字节相同。|
|完整输入|同目录 `source-inputs.json`，2,072 项，SHA256 `ba2c2fbabd746690fd8ae04be26ba22f55ddbdd5e8f320a81c8b0bcbfece947c`；逐项重核 bytes／SHA／执行位，差异 0。14 变更文件另与 `changed-files.json` 重核，差异 0。|
|生产变更 6 文件|`data/schemas/project-registration-v2.json`、`reference_executor.py`、`registrations.py`、`state.py`、`task_design.py`、`tasks.py`。完整阅读其 diff、新 schema、相关原实现与消费者。|
|测试变更 8 文件|`fixtures/reference_acceptance.py`、`test_budget_jobs.py`、`test_composition_executor.py`、`test_registrations.py`、`test_state_backups.py`、`test_state_migrations.py`、`test_task_budget.py`、`test_task_creation.py`；完整阅读 diff 与关键既有 fixture。没有新增 CI 分组或 job。|
|权威需求／设计|[原始要求](../plans/2026-11-15-workflow-evidence-and-human-gates.md)、[D1–D4](2026-11-16-workflow-design-decisions.md)、[设计与知识关卡](../plans/2026-11-16-design-knowledge-gates.md)、[登记与 journal 拆片](../plans/2026-11-16-design-gates-registration-and-journal.md)，及两份相应独立设计审查。S1 仅 storage／恢复／拒旧输入，不开放新设计执行。|
|仓库与审查规则|根、src、tests AGENTS；[组件变更协议](../architecture/component-change-protocols.md)；`maintainable-project-delivery` 及 independent-review；`ergora-codebase-quality` 的 repository-style／module-design／test-seams。|

主树的既有 docs 差异保留。作者原基线 `3d632a78b6acc4f0027b2225e7771a5da927af81` 的证据、早期审查和 119 项旧安装结果各保留原身份；本轮没有将其作为完整 `c540939 → 80cb39c` 的独立通过。reasoning／V2a 已审变更也不转授 S1 通过。

## F1／P2：native 项目查找仍提前越过 v1 的失败回执边界

位置：候选 [reference_executor.py 第 36 行](../../.ergora/worktrees/design-policy-registration-fixed-r3/src/ergora/reference_executor.py#L36)，以及 [process 第 743 行](../../.ergora/worktrees/design-policy-registration-fixed-r3/src/ergora/reference_executor.py#L743)。相邻原 owner 为 `_execute` 第 712–731 行、`DirectJob.run` 和原 `agent_platform.core.project_for`。

`_admit_project` 第一行调用 `original.project_for(spec['request'])`，该函数重新扫描当前 `CONFIG/projects/*.json` 并要求 tracker 恰有一个匹配。它现在由 `process` 在创建 `DirectJob`／进入 `_execute` 之前调用。虽然本轮修正已让 State 项目不存在回到原消费者处理，但 native 查找的 `Blocked`／文件读取错误仍直接逃出这个外层入口。

可达场景：用原 native `create_task` 冻结合法旧任务，沿原 `Activities.submit` 发布合法 inventory job；在消费前，native 项目配置丢失。原 `tasks/<task>/project.json`、`binding.json`、`compiled.json`、spec 和 envelope 完整不变。这不需要伪造 job、升级登记或触及设计 policy。

原 baseline 在 `Executor` 构造中执行同一 native 查找，失败由 `_execute` 捕获，绑定原 job／context 后发布 `FAILED` 与 `agent-admission-error`；`DirectJob`／adapter 验证和发布回执，原 poll 能取得终态。当前候选在外层抛 `Blocked`，没有回执。服务循环只会记录 rejected-envelope；Workflow 的原 poll 无法得到之前会有的失败终态，只能继续等待其原超时／预算边界。

本 reviewer 经主控授权运行了同一原 fixture 的最小扩展，两边均用新的非 editable 安装及 `python -I -B`，保留真实 native creation、Activities、process、DirectJob、adapter、poll。只删除已发布 job 对应的 mutable `CONFIG/projects/demo.json`，其余业务方法仅包计数，没有替换返回值。

|真实观察|c540939 安装|80cb39c 安装|
|---|---|---|
|实际 executor SHA256|`571726cfd47ab7fa0c4f0d86f1753501b4a502f76f182c365b2a7dc99105f5a6`|`f9b794a723e5dc73d6caef70c82151b6b3d8116218d586799aa76f1191901512`|
|process 结果|`FAILED`，artifact 为 `agent-admission-error`|抛 `Blocked: Register exactly one trusted project matching the task tracker`|
|原 poll／receipt 文件|读到同一 `FAILED`；文件存在|`null`；文件不存在|
|计数|`_execute=1, claim=1`；prepare／model／commands 全 0|全部 0|
|冻结 project 原字节|保持|保持|

原始 argv、过程 PID／start ticks、stdout／stderr、观察值与安装导入路径在 `.ergora/checks/design-policy-registration/reviewer-native-resolution-r1/{baseline,candidate}/`，聚合为该目录 `result.json`。两个 probe 均正常退出，已 wait 后 PID absent；这是对失败行为差异的 probe，不能把 runner exit0 写成产品回归通过。未运行模型、业务命令或真实服务。

**最小修正：** 保留 v2 和 foreign-home 的 preclaim 拒绝，但不要让旧 v1 的普通 native 配置失败越过原 `_execute` 回执 owner。将 preclaim 必需的登记身份读取与原 constructor 的完整 native 项目解析分开；对于已发布任务，可评估复用其正确绑定的原 project／binding／compiled 身份定位 State／marker，原 constructor 仍执行原配置校验并产生原失败回执。不能无条件吞掉所有查找错误后放行，也不需要新建通用项目 resolver、回执格式或第二异常收据路径。

验证只需把本真实反例接入已有 fixture，再核原 v2／foreign-home 两入口及 BudgetedJob 的 claim／业务 starts 仍为 0；旧合法任务在 native 配置缺失时原 poll 必须重新读到 `FAILED`。同源 duplicate-tracker／每种读取异常不必另铺重复矩阵。修正影响 source 后再做准确新安装的相应最小节点，不能继承这次 13 项通过。

维护性同样 request-changes 的理由是这一具体 owner 迁移：`_execute` 已拥有拒绝证据的 job 绑定、artifact 和正式 terminal 合同，新的 policy 识别检查把其既有错误旁路到服务循环；不是因为 helper 数量或文件长度。

## 其余需求与结构核对

|方面|本轮结论与边界|
|---|---|
|v2 完整 policy|显式 schema2 和嵌套 registration2 判别保留；profile／policy 原对象和 canonical SHA 纳入原 definition、marker digest、intent／result。最低 Q/K 并集、同 ID 异内容／跨类别冲突和配置容量由 registration owner 核；配置的 owner／assurance 没被冒充已认证身份。|
|首次资格与竞争|`_prepare` 拒已有登记的 v2 升级／替换／降级，含空 v1；原四投影存在时拒首次 v2。publication 锁内再核 `_current` 和 native 投影后才 `_reserve`，修复原首次登记交错的孤立 intent 窗口；保留事务内原 revision 重核。|
|status／resume 历史边界|新增 `_validate_saved` 仅用于 registration2 的 status／`_finish`，不把现行输入 schema 新加给 v1 历史读取。直接核 `4ffcfdde` 与父 `62c4d696396942fbad86fc21f56f9e854e3ed4d1` 的 tracker schema，历史 newline 原先确可接受。`published_project` 原本就有当前 schema 的完整来源校验，本轮没有放宽它；这与 status／resume 是不同合同。|
|v1 frozen selection|State 缺项目的异常回退只包项目查询，repo 比较仍在原无 snapshot 分支；没有再以当前 registration SHA 要求旧 frozen selection 匹配。已有四项缺 control／repo 错配对照的修正与源码相符；F1 是另一个 native 查找边界。|
|marker 路径|原 `core.slug` 对合法标识符直接返回原字符串；统一登记允许的字符／长度是其子集。没有真实大小写／下划线路径变换，不需要为该疑点改生产路径规则。foreign-home 明确拒绝是本片必要的 authority 收紧，与 markerless legacy 的原回执／恢复区分。|
|State6 与恢复|仅替换原所有领域表的 v5 writer triggers，沿原事务／预迁移 DB backup；测试扩充到已开 v5 连接及真实 v5 中断。control-home backup 不包含外部执行 config／state 的边界明确，没有承诺整体部署回退或在线旧服务切换安全。|
|任务出生与预算|两个实际入口 `_definition`／`_budget_project` 在创建／prepare intent 和预算授权前消费同一纯拒绝规则；恢复入口未新增这个出生 gate。process 与直接 Executor 两处 preclaim 确实各有真实消费者，BudgetedJob 的早 claim 说明外层检查有必要，F1 不要求删除它。|
|抽象与依赖|policy/schema 校验仍由 application registration/contracts 持有；native 只引入原纯 `task_design` 的窄规则。其真正生产消费者为 tasks 和 executor，避免把 jsonschema／State／SDK 混进共享纯合同。私有 union／saved-definition／intent helper 均隐藏本 owner 的实际义务，没有新的 policy service、ABC、registry 或单次空转发层。|
|版本／权限与范围|Input 仍最大 11、definition 仍最大 7；没有可执行 v12、设计批准、模板默认或可信 human 通道。完整 diff 未改原 reference、presets、Input factory、envelope 或 CI；原 127 锁、283 参考和祖先资源／权限合同未扩张。|
|测试价值|新增用例沿原 registration／State／creation／budget／Executor 接缝，分别保护持久完整性、两出生入口、早 claim 与历史读取；没有新增 CI job 或为每个字段复制同义矩阵。native 实际文件发布与中断恢复、旧原件对照比纯 helper 断言更能观察目标风险；现有 13 项未包含 F1 的配置缺失。|

以上“没有其他 finding”只限本轮完整变更及所追踪的相邻 caller；不认证后继 F/J/G 或生产部署。

## 实际检查、证据与未验范围

本轮实际执行了只读 Git／rg／分段源码和文档读取、完整 frozen input bytes／mode 校验，以及上述新增的两个最小安装 probe。没有自行重跑昂贵套件、安装、网络、模型、训练、服务、commit 或 push。唯一额外写入在主控明确授权的 reviewer 专属 probe 目录；未修改产品／原测试／其他报告。

已直接读取并核清以下历史与本候选证据的范围：

- `red-v1-compatibility-r2`：JUnit 6 项失败，原问题可达；`source-v1-compatibility-fixed-directed`：92 项、0 failure／error／skip，JUnit 285.600 秒，runner 286.525 秒。作者准确原 owner 对照与历史 schema 回放保留在 `original-v1-compatibility-probes-r2`；这些不是完整旧发行版安装。
- 主控新的 `package-v1-compatibility-r3`：同 wheel SHA256 `2d1f1830d46c1acee1d3374429f901b2bc4cb8c1d8477e2a1ff6cbc057eee4db`；core／SDK 包身份检查均记录 669 文件、source／wheel／installed 同一、真实 site-packages。已读实际 JUnit／stdout，13 项、0 failure／error／skip，JUnit 78.701 秒。此准确候选的这些入口通过，仍不能覆盖新 F1。

未实测线上 State 迁移／旧服务排空、standalone stack 隔离、外部多根整体恢复／软件降级、真实可信 owner 通道、真实人类设计旅程、后继 definition8／admission12／source journal／G1/G2、Temporal 服务故障恢复、发布或候选自己的公开 CI。S1 必须继续保持这些能力关闭或待验。

当前阻塞仅 F1：修正后以同一原 job／poll 反例和必要 preclaim 对照复核，再记录准确新源码／安装身份。主控保留原 80cb39c 和本报告的 request-changes 证据，不把旧通过转写到修后候选。


## 后继r4独立复核索引

本页原80cb39c request-changes与反例保持原身份。[新的fresh-context r4完整审查](2026-11-16-design-policy-registration-r4-review.md)已在准确b28cd316核新安装原probe／17回归和整个候选，需求与维护性均approve、开放findings0，原F1/P2关闭。后继结论不改写本页历史失败；普通合入与联合安装／发布见[当前交付](2026-11-16-design-policy-registration.md)。
