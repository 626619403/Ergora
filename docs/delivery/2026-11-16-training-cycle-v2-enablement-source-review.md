# M6 正式 V2 执行接线：独立源码审查

2026-11-16。Reviewer 为新建、fresh-context 的独立源码 reviewer；使用 maintainable-project-delivery 的 independent-review 和 ergora-codebase-quality 的三个审查参考。本文是**初始冻结源码**的审查，不是最终 freeze、安装、真实 Temporal／CPU 两轮或发布验收。实施 owner 仍在补测试和验收；后续修订应在本片复核，不能把本文结论转授新源码。

## 范围与身份

已读根、`src/ergora`、`tests` 的 AGENTS，PLAN、活动计划／交付、组件协议的执行／证据、持久格式和检查条款；并对照原 M6、前驱/native gate、measurement/capacity 合同。历史设计状态和旧片运行结果不作为本片实现证明。当前活动片为既有已冻结有限候选的执行接线，不包含搜索、Profile scheduler、registry、DB、schema 或旧已发布定义改写。

- 分支：`feat/training-cycle-v2-enable-r1`；准确基线：`b71680bc2f2fabf5b10d5499104389391fa23a4f`，尚未提交。
- 初始输入：`.ergora/checks/optimization-loop-orchestration/m6-source-initial-r1/{manifest.json,complete.patch,files/}`。完整 patch SHA256：`7b97f2512a30e234d507310563604ab4aaff7b5cb2a59256e8d462d33a18bf96`。原输入未跟踪文件为 0；本报告不属于原八文件。
- reviewer 自行重算八文件 bytes／SHA256／执行位和完整 patch SHA，均与 manifest 相同；核验时工作树八文件仍与冻结副本逐字相同。开始时 branch、status、最近五个 commit 与基线一致。

|冻结文件|bytes|raw SHA256|
|---|---:|---|
|`src/ergora/reference_training_budget.py`|37263|`611912b7a7fe161132266a7722773aa872a7c75c267499f4444521dd6e0cf584`|
|`src/ergora/reference_training_worker.py`|180412|`dcc308cf075ea0f49d52cfcecad39face376e8340c438a561eac59fcbf88da3f`|
|`src/ergora/training_cycles.py`|38912|`1b29ef9b3a7c6400ae05ce2ba20e3f9e7336c34fb0aa3037e442ce0c43bc1647`|
|`src/ergora/training_execution_protocol.py`|119587|`1ecbaacb878de6c40a42ccc73bbcbd20a93b6b9d3565639b1bdf15cfdb852f81`|
|`tests/fixtures/training_controller_service.py`|19539|`3888738b68b9843a9404226f018ffc3c1586302983928486015413b9ed80aba6`|
|`tests/fixtures/training_submission_client.py`|11404|`4fb29fa371feb7a33d33f17b9de0237a2a8c29d9d02d2151480556832f251041`|
|`tests/test_training_cycle_controller.py`|102451|`d1e9111a0a15513303f0d30903146c3ec0e48428b0ac986806925e228b08af30`|
|`tests/test_training_submission.py`|272594|`4ca067e47664ef7593162e457888b3a24a9c22cea3e9e5f3cca1687288aff2ab`|

相邻只读路径包括原 submission、Execution、runtime、native admission patch／executor、evidence、原 ExperimentWorkflow 和现有 fixtures。没有修改产品、作者测试、原运行材料、PLAN 或其他交付；没有运行测试／反例、安装、服务、GPU／模型、commit 或 push。自行执行仅只读文件／Git、raw 身份核对和 Python AST 分析。

## 初始结论

|轴／范围|结论|开放项|
|---|---|---|
|原要求与执行接线，限定初始源码|**request-changes**|R1／P1：后继出生／start 路径未接 H 的当前完整前驱准入|
|维护性，限定本次四个产品 owner 的差异|**approve**|未发现独立的新增结构阻断 finding；R1 应留在原 H／evidence／runtime owner 闭合|
|完整 M6 验收|**pending**|最终源码、受影响回归、新安装、真实服务和 CPU 两候选、自身模板、最终复核／发布及本候选自己的 CI 尚未提供|

## R1 · P1 · 后继可以在紧邻前驱已不再可接受时出生并 start

**位置：** `reference_training_worker.py:1340` 的 `_candidate_operation`，以及 `reference_training_budget.py:263` 的 `BudgetedStart.source`。对照现有 H 算法 `reference_training_worker.py:1211` 的 `_round_previous`。

原前驱/native gate 设计要求 H 额外沿原 evidence owner 重新 inspect 完整 archive，并对紧邻前轮认证**当前**可接受的 runtime phase；native 保持只核本地历史原件。当前 `_round_previous` 已正确承担这一 H 职责：逐份重读 `training.evidence`，紧邻前轮调用 `_execution_candidate_operation`，再以 `round_state` 判定 accepted。但是其实际调用者只有 `_round_operation`，即本轮 collect/reconcile。

新开放的后继 prepare 只认证总 controller 的 RUNNING／namespace／history，随后进入 `training._prepare_submission`。intent 出生前、intent 同步后的 `BudgetedStart.require_active → source` 调用的是纯本地 `authenticate_cycle_candidate`。它核完整原观察、archive 原文件、index、链和 source pin，运行态判定来自保存的 `value['runtime']`；它有意不查 SDK。后续 confirm 和原 submission start 同样没有调用上述 H 当前前驱 gate，`check_controller_history` 查的也是总 controller。于是当前 H 准入被推迟到后继自己的 collection，已经晚于后继 intent／start。

**可达序列（源码证明，未冒称实际运行）：**

1. 轮 0 已在 `AWAITING_RELEASE` 接受并形成完整 observation／index；总 controller 仍 RUNNING，原 wall／work 有余量。
2. 原 `ExperimentWorkflow.request_cancel` 接受匹配取消。`cancel_and_confirm` 在原 `upstream/temporal/perf_temporal/workflow.py:79–82` 先置 `phase='CANCELLING'`，再等待 `cancel_exact_job` activity。这个实际异步间隙无需改写任何原本地 accepted archive／execution 文件；直接 server 终止前驱也可以保留这些本地字节。
3. 轮 1 的 start activity 到达真实 H。当前代码仅查询总 controller，纯本地认证仍能读取原完整 accepted observation，因而可写入轮 1 intent，并继续原 start。
4. 应当在出生前阻断的前驱当前 phase／archive 失效，只在轮 1 后续 `_round_operation → _round_previous` 才被发现。完整历史接受证据不能替代合同要求的当前 H 前驱准入。

**最小修正：** 在原 H 内复用／内聚现有前驱 archive 与紧邻前轮 SDK 判定，使后继 prepare 在 intent 出生前经过它，原后继 start 准入也不能仅查总 controller。处理尚未出生的 intent，不能先写 intent 再以“现存 intent”作为调用前提。保留原固定 operation／父 run、同一 BOOT／window、已有 source／stop／clock 同步后重核和不可换绑语义；不把 SDK／State 加进 native，不复制 archive reader、不增加账本或放宽预算。

**最小验证：** 沿现有真实 S/H、完整 accepted round 原件和 SDK 服务替身，保持前驱全部 raw 文件不动，只将前驱当前 phase 设为 `CANCELLING`（或固定 run 终态不再 accepted）；确认拒绝发生在后继 intent／start 前，并保留无新增 intent／attempt／send 的证据。补合法 `AWAITING_RELEASE`、原合法完成 outcome 的正向对照，以及后继 intent 已出生后新的 reconcile observation 不能换绑。服务替身只认证该边界，真实 Temporal／CPU 两轮仍单独验收。

## 已核的重要合同

- 四个产品改动沿既有 owner，没有新 scheduler、持久表、运行账本、通用插件或额外配置接口；原六阶段、release／采用和 baseline owner 不在 diff 中。新分支分别处理 schema3、schema2 和手工绑定，没有把未知版本宽化为 `>=2`。
- 新 `BudgetedStart.source`／`validate_context` 均先经过同一完整本地前驱认证；该算法反向到 ordinal0，绑定原 intent 中的 predecessor、完整 helper request／reply、同次 observation／prefix／acceptance、原 execution inventory、archive raw 文件、四 measurement 和原 owner capability 的 source／ROOT。当前 owner 尚未出生时不伪造25项授权 pin。
- 原 submission start 在 attempt 同步后重新 preflight／require_active，再以同一原 prepare source／window 做最后 `dispatch_remaining`。原 registry absent 分支仍走 `budget.require_active`，request／launch 在原 execution 锁和父许可内同步后再 `current`；没有退回已占用机会。
- native 无 result 路径在 executor lock 前取得自己的父共享许可，并持到真实 `process` 返回。callback 入口仍只接受 unused consumed launch；attempt／ack 后重读并精确匹配本次阶段，不把任意已有 ack 当成重新执行授权。最后 active 在 ack 同步后、callback 返回前。
- schema3 已有 result 保留原 inert read。outer 存在性检查后若 result 消失，callback 重新完整 validate 并取得父许可；可见 stop 或已占用 attempt／ack 都会拒绝新的执行。这里只确认源码路径，尚没有本 reviewer 的竞态运行证据。
- reviewer 自行比较完整 AST：`TrainingCycleWorkflow` 和 `TrainingCycleWorkflowV2` 对准确 baseline 均完全相同；本次没有修改已发布定义资源。此检查证明类正文保持，不替代实际 history replay。

## 读到的运行原件与限制

以下是实施 owner 的现有证据，reviewer 只读核 XML／stdout／stderr 和相关测试源码，未自行重跑。证据根为 `.ergora/checks/optimization-loop-orchestration/m6-r1/`。不同运行的源码不能彼此转授完整通过；initial source 身份核验见上表。

|原运行|实际终态|本次可确认范围|
|---|---|---|
|red-controller-dispatch-r1|2 failed／12.60s|原 schema3 关闭的两个 dispatch 红例|
|controller-dispatch-r2|14 passed／104.72s|两版本原 controller 单机会／恢复定向用例|
|dispatch-boundaries-r3|19 passed／97.00s|实际完整 SDK input／Memo 容量及旧无 controller 绑定拒绝|
|native-permit-red-r4|1 failed／20.04s|初始 fixture 未识别 v2 路由；不当作产品 permit 反证|
|native-permit-red-r5|1 failed／28.94s|真实 native attempt 路径缺自己的共享许可|
|native-permit-r6|11 passed、1 failed／240.66s|executor-lock 时父许可取得过晚的原失败保留|
|native-permit-r7|12 passed／237.31s|修后两版本5边界、无效绑定／已有结果定向验证；测试静态核到真实 `/proc/.../fdinfo` 的 FLOCK READ 检查|
|late-reader-r8|2 passed／121.10s|读取时已终态；两种所选 native installation 的 M−1／M／M+1 完整 UTF-8／LF、application／纯边界与真实 native dead-owner 拒绝。该 fixture 为合成已停止原库存，不是 live schema3 两轮|

late-reader-r8 的 stdout SHA256 为 `274e40fa479a8f85d31d90aa319c94455c573789289a0fa649021be74095c862`，XML 为 `06dce7be8ebfa2a70d3d77ee4cf04114f50c563e2ede794f795f9f7a4e2e7735`。初始 brief 中“运行中”只指当时时点；本次不覆盖其原过程或把两项通过扩成全片矩阵。

初始测试仍有关闭哨兵未迁移：`test_round_internal_collect_and_reconcile_keep_archive_and_execution_closed` 还要求 `BudgetedStart.source` 抛原 schema3 关闭错误，部分 v3 stop 注释也称关闭。这是实施中的回归／记录适配待办，已通知实施 owner；本报告未虚构它已运行失败或已修。最终应收齐受影响原节点，不能只用新增正例认证全片。

未验／不能关闭：R1 的实际边界反证与修后结果；最终完整源码 scope 和冻结身份；相应旧合同回归／history；准确新非 editable core／SDK 安装及实际 import 身份；原结构模板；真实 service 四 poller／两个独立许可、旧 queue 正向；真实两个 CPU 候选顺序 archive、丢回复／恢复／停止／预算／收尾；最终 fresh 同片复核、发布及本候选自己的适用 CI。没有 GPU、模型数值／质量或性能收益结论。原 V2a／V2b、原 M5 或旧 CI 的通过保持各自范围。

## R1 修正与最终限定源码复核

2026-11-17。同一独立 reviewer 的同片复核，保留上文准确初始结论、原失败和当时未验项。本节更新当前源码结论，不把初始 request-changes 改写为初审通过。r20 运行期间 reviewer 未改隔离树任何文件，仅在主树 ignored 检查目录记录便笺；root 通知运行终态并允许更新后，本次只追加本报告。没有修改产品／测试、运行测试、安装、服务、GPU／模型或 commit／push。

### 最终源码身份与13文件范围

分支和准确 baseline 保持 `feat/training-cycle-v2-enable-r1`／`b71680bc2f2fabf5b10d5499104389391fa23a4f`。最终行为输入为 `.ergora/checks/optimization-loop-orchestration/m6-r1/native-round-boundaries-r20/{inputs-before.json,source.patch,files/}`，**不是初始八文件 patch**。完整 tracked patch 为 **84293B**，SHA256 **`50a8b17a475512d0c8397b5252ab5016b479020030ec9d79c8456101d4d941de`**；2136项输入 manifest 的 SHA256 为 **`773d1a0540ce7be35f2e01ddadd27c93fe19038ca20c212413a46b37d5448f68`**，运行前后原件逐字相同。

reviewer 自行核对13个冻结文件 bytes／SHA256／执行位全部同一；终态后、追加报告前，再核当前2136项仍全部同一。最终 scope 为12个 tracked 文件和本报告，共13文件：

|范围|文件|
|---|---|
|7个产品 owner|`src/ergora/cli.py`、`reference_training_budget.py`、`reference_training_runtime.py`、`reference_training_submission.py`、`reference_training_worker.py`、`training_cycles.py`、`training_execution_protocol.py`（后六项均在 `src/ergora/`）|
|3个既有fixture|`tests/fixtures/training_controller_service.py`、`training_cycle_operations.py`、`training_submission_client.py`|
|2个既有测试文件|`tests/test_training_cycle_controller.py`、`tests/test_training_submission.py`|
|1个审查记录|`docs/delivery/2026-11-16-training-cycle-v2-enablement-source-review.md`；r20冻结其初始正文，本节为运行结束后的审查追加|

|产品 owner|r20 raw SHA256|
|---|---|
|`cli.py`|`86041cf5ce4663387e94fc4d99b7723083bf60c01faf7eb22d8c8555916da9ca`|
|`reference_training_budget.py`|`621346dc2633f82ea37bc9f7c0996eb21e756acebfa577257034ad0830050219`|
|`reference_training_runtime.py`|`5d8d1e343f81dd674db1494c093e7338e3f6062e9d9c5dad47f9f6d2f6d30c4c`|
|`reference_training_submission.py`|`1b860c4467b2e851850dd1afb3efe662403a3db90d4ee20c3f24f92cc519afc7`|
|`reference_training_worker.py`|`5d6a7ee33a9dede069949f3d5bd09c27b66154e40135de427967765a548cde0a`|
|`training_cycles.py`|`3bbad3014d779ef75668fe69dafd5b48170a93a95879dfaf7f1fb0758b456148`|
|`training_execution_protocol.py`|`e1f197675606d9f9c7f4408066619c7e6b4747e81c209bebaa2b77566d1df0d1`|

### R1的实际修正与两轴结论

|轴／范围|当前结论|
|---|---|
|R1及r20限定执行接线的需求符合性|**approve；R1已关闭**|
|r20限定结构／维护性|**approve；开放阻断finding 0**|
|完整M6交付／现场验收|**pending**；本节只认证准确源码和下列实际定向证据|

- `CycleAdmission._bound_selection` 认证真实完整 budget/controller binding、原父 intent／attempt／receipt、固定run和ordinal。`bind`仍核完整当前intent的candidate／observation。新 `authenticate_cycle_binding` 可在出生前读真实binding，不构造未来intent、dummy operation ID或validated缓存；原 `authenticate_cycle_candidate`保留当前完整intent／owner／capability和末尾重读。共用纯算法仍走完整链到0，保留同次index／observation／acceptance、原request／reply、execution inventory和archive原raw映射。出生前只验证实际存在的四measurement／ROOT／所选安装，不伪造尚未出生的25项owner pin。
- `check_cycle_predecessors`留在原budget/H层，实际消费者是worker出生／collection路径及BudgetedStart的原最后准入。它逐份沿原`training.evidence`重读archive；紧邻项额外读取固定run的完整input、Memo和当前phase、原native poll及durable execution，再交原`round_state`。最后重核父RUNNING、完整本地binding、stop、project和原allowance。更早owner可以正常退出，不引入第二archive reader。
- `observe_submission`把现成runtime读回迁到原SDK owner，由只读观察和最终准入共同调用，返回完整事实而非accepted布尔。实际namespace、连接和同一剩余窗口仍归调用者；protocol/native没有新增State／schema／SDK依赖。
- `_candidate_operation`在`_prepare_submission`之前和intent同步之后核前驱，confirm／dispatch继续复核。SDK等待不进入原DB reservation。已出生intent的恢复不产生新offer，不换predecessor。`_Submission.dispatch`在原start attempt同步后、send前再次`await`同一gate，随后保持原`require_active`、父stop和完整prepare source／原window的`dispatch_remaining`。已有attempt仍只对账。
- 原registry和Execution消费者的远端查询仍在各自业务锁之外；submission沿原锁及父共享许可持到实际send返回。同步后的本地source／clock／stop末核保持；没有把RPC说成与Temporal原子。native的外层许可、既有result早读以及attempt／ack精确本次阶段保持。
- 新CLI及`training_cycles.controller`仅接原storage和S/H owner，分别暴露显式出生同意／版本、原revision的prepare、单次submit、只对账reconcile／只读status和local stop的实际范围。没有新持久账本。已失效的统一schema3关闭测试被移除，原风险由版本／source／stop／clock／机会占用和真实正负接口承担；N32仍66分支，大reader仍保留dead-owner拒绝，native最后publication扩双版。

reviewer再次自行比较完整AST：**`TrainingCycleWorkflow`和`TrainingCycleWorkflowV2`对准确baseline均完全相同**，不是只比方法名或摘要。已发布定义资源不在diff中。AST保持不替代真实history replay。

### 原红例、修后边界和最终定向运行

以下均为实施owner实际运行，reviewer独立读回stdout／XML／command和相关fixture／test源码，没有自行重跑。证据均在 `.ergora/checks/optimization-loop-orchestration/m6-r1/`，保留各自源码范围。

|原运行|实际终态与可认证范围|
|---|---|
|`previous-phase-red-r10`|1 failed、1 passed／27.84s。SDK替身只返回CANCELLING，旧产品仍出生beta intent；原R1反例成立。stdout SHA `f1a74ce4f08bff286d86af2d16d576de4c95e9e022690ea0587da4b5905d4d98`。|
|`previous-phase-r13`|2 passed／25.57s；当次合法与CANCELLING出生前对照。|
|`previous-boundaries-r14`|4 passed／50.54s；合法、出生前失效、intent出生后失效及实际SDK查询等待时SQLite BEGIN IMMEDIATE仍可取得。alpha job原文件精确不变，失效场景无beta attempt／job；出生后失效保留原intent且不生owner。|
|`last-controller-gate-r15`|1 passed／24.84s；真实attempt同步后父closed，attempt字节／inode不变、starts=0、无native job，恢复仍只对账。它认证最后查询边界，不单独认证真实前驱phase在beta attempt后的交错。|
|`controller-boundaries-r19`|**36 passed／252.42s**（JUnit252.421、runner254.617661s），exit0、未超时、2136输入前后同一，原command记录420采样自有进程、remaining_owned=[]、observer_errors=[]。覆盖原controller恢复、完整SDK input／Memo双门、CLI、最后父gate和原claim／手工拒绝。|
|`native-round-boundaries-r20`|**35 passed／819.34s**（JUnit819.335、runner820.473855s），exit0、未超时、2136输入前后同一；原command记录1473采样自有进程、remaining_owned=[]、observer_errors=[]，stderr为0B。覆盖双版native最后source／ROOT／clock及五停止边界、两selected installation的大reader、N32全部66分支及整体容量拒绝、完整原件／早轮链／最后blocking reader／source／stop和丢回复existing-only恢复。|

r19与r20完整manifest对比只有`tests/test_training_submission.py`不同，生产文件全部同一；不把36项称为r20新增native／round节点。r20实际九个pytest选择展开为35项，XML没有failure／error／skip。进程收尾只认证原runner捕获的自有集合，不声称全系统零残留。

|最终原件|SHA256|
|---|---|
|r19 `command.json`|`976b88e6823fb7afac77379516c20c4479f21cb5d1514df2e5bdc75e72aacc17`|
|r19 `junit.xml`|`2eb072a24737e05c5df0ef5f46f959021ab58229ab02352a326c5096cc526464`|
|r20 `command.json`|`e52b9119730d751784c9817b7ee7dbb2c065582830961ca299d167778ff46594`|
|r20 `junit.xml`|`73fdd2ba0b2b55ef61d6b49cbf6b2d2972b9de83e67d849c94433438f7be58e1`|
|r20 `stdout.txt`|`c765898d12cfaf4852acd7ee51d5d4d05458d34a9d667696dde3bddfbdcc6cab`|

当前限定源码审查门已闭合；**未验的新安装、原自身结构模板、真实Temporal服务及旧queue正向、两个CPU候选顺序archive、真实丢回复／重启／取消／预算／停止与完整收尾、整合后候选复核／发布及自己的CI仍pending**。源码定向、fixture创建的selected native installation和SDK服务替身不等于新非editable应用包／真实服务验收。无GPU、模型质量、数值／性能收益结论；后继普通merge或新包不能自动继承不同输入的完整验收。
