# c1d M6：正式 V2、SDK-v3 与 runtime 开放设计

2026-11-16。**仅静态设计，待新的 fresh 独立需求／维护性审查；未实施、未运行，不开放 schema3、ordinal1 或正式两轮。** 本页承接已接纳的 [measurement/index](2026-11-16-training-cycle-measurement-and-index.md)、[严格 wire](2026-11-16-training-cycle-measurement-wire.md)及其[最终设计复审](../delivery/2026-11-16-training-cycle-measurement-wire-review.md)、[容量分期](2026-11-16-training-cycle-measurement-capacity.md)及其[设计审查](../delivery/2026-11-16-training-cycle-measurement-capacity-design-review.md)、[M2/M3](2026-11-16-training-cycle-measurement-acceptance.md)、[父请求留存](2026-11-16-training-cycle-parent-request-retention.md)和 [M5 前驱/native gate](2026-11-16-training-cycle-predecessor-native-gates.md)。wire 的严格字段、版本、容量和原机会合同不在此重定。

[runtime-consumers](2026-11-16-training-cycle-runtime-consumers.md)是 c1b2b/c1c 首轮接线背景：其中“未注册正式 Workflow”和“尚无两个 v2 活动”属于当时的缺口。当前已有正式首轮 `TrainingCycleWorkflow` 及 request/observe.v2；本页只补新出生 schema3/program-v2 的正式消费者、完整 M1c-V/R、原最后 gate 的统一开放与真实两轮验收，不重复建立 c1c。

## 原始需求、身份与证据范围

原始目标是保留优化前后原 baseline/candidate、结果和算法／质量约束，按同一原 candidate 预算顺序消费出生时已经选定的 1..32 个候选；模板可组合、完整继承全部祖先资料，但权限逐级收窄。原六阶段、kernel 在 v3 总提案路径、candidate-bound evidence、人工 release/采用、attempt-before-send、unknown-only 对账、唯一 start/request/collect 机会、连续 BOOT 根和 cleanup reserve、父 stop／独立 reaper 均保持。循环不是新候选搜索器，不自动 release、approve 或晋升 baseline，不新增通用 human/design 产品关卡。WA4 D1–D4 尚待用户答复；既有 c1 授权允许继续设计本片，不代表这些新产品决定已获确认。

应用 maintainable-project-delivery 和 ergora-codebase-quality 的 module-design/test-seams；已读根／源码／测试 AGENTS、PLAN、组件协议的定义／执行证据／检查分支、上列计划及原审。**本任务只新增本页**；PLAN、交付、源码、测试与他人修改由根接续。新的独审由根另启，不递归审查报告。

调查主树 `refactor/architecture-foundations`，准确 HEAD `a0d533d13b4aae9441e3b6b920b27c2534353b87`。进入时已有他人的父留存交付文档差异，本页不覆盖。已终核的 M2/M3 产品为 `68ba793a2d2ff02e4cffe50a03cfcec38d67256a`，普通导入 `c6cfafb0b556c0cd36cf6f541e95ac4b15d3b254`；[最终源码／安装终核](../delivery/2026-11-16-training-cycle-measurement-acceptance-source-review.md)两轴 approve／0，源码 26+14、安装 26+14、core 实际 10MB reader、自身原模板各只认证其原范围。663 完整产品与原输入保持，不把这些结果写成正式 V2/v3 或 GPU/训练质量验收。

|本次实际读取原件|raw SHA256|
|---|---|
|measurement-and-index|`4575d4f0dae80ea0ab822c002780acfa4decafa41c882b85f1c99509d4abb72d`|
|measurement-wire|`ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`|
|measurement-capacity|`c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`|
|measurement-acceptance|`2ecfa840f5c52b53cf9dbd3782a9a7b330b5421b19623eac9c70484ac3fa0bff`|
|parent-request-retention|`bf35924d01b665470fe5ba216f9e9e450162390498cff44dcdd5eb5ddb39bafe`|
|predecessor-native-gates|`8d5f84b36357a6f9ec6e524a1dc7d7af4e6ed22a6ae69e9b7ff8e32cba521044`|
|runtime-consumers|`d6d5f61c22ac81dda11832f0893f682359b3fe2c2a48377037ae7d4f0abba97d`|
|`reference_training_worker.py`|`522b9cf4a0db51cea6e4722e6136e005a825114ac1deee1f7e7dadc3b4292651`|
|`reference_training_runtime.py`|`280cf8699ee1b22577b85171835779369d922391c01e884bb46921b2547c7314`|
|`training_execution_protocol.py`|`a0b29a9412b2ab1b31341873e8cbeb24da0af5529ec40e541b5dd68c811e220a`|
|`training_cycles.py`|`0a96a1c14ede76510e7480299e0958d36296ba0e5895a63743e311d1a03ff110`|
|`reference_training_submission.py`|`9c775643b07a937690230cdb86bd19e0d6fc89fcdb092fbb50d7bc3856a7575c`|
|`reference_training_budget.py`|`1fde5981eb63aa50dcaaae427144528ff27d2ff4bba3345bc13fe1059a441cb4`|
|`reference_training_execution.py`|`f6b4a1ab90bdcaa3737b3c75abbaeaea6ee8afd029b3033cfbdc6a630531ad1b`|
|`reference_inputs.py`／`reference.py`|`c116d153b867aff6f013f1d980c9bf3c874d74013c2e32770d8b768c42aae09b`／`a3c53b2f8b15954709ec068a984d3623918acd5a55e3d18ed59c41ec977bdb30`|
|runtime tests／submission tests／operation fixture|`4b5d7ed4c3fc8d6fcae079821ccfa0617635aedbc6f0cf73c9c803437883e361`／`9e939917faefaf580d6f7cacf6f50bed5e40baaeae7a0ec8da837f722b318810`／`9d2b74660aafa296c3a596c0432415357942bd90164d883b1cff0c361cd82056`|

父留存在指定隔离树 `.ergora/worktrees/training-cycle-parent-retention`、基线 68ba793 三文件实施中，根给定 r1freeze `709e9ba2`；本次只看其实际 constructor 接口，未验整个 diff／冻结物／运行。不得固定其未审私有函数名或借用其试跑作为通过。其已审限定设计和[复核](../delivery/2026-11-16-training-cycle-parent-request-retention-design-review.md)是前置合同；M5 的[设计审查](../delivery/2026-11-16-training-cycle-predecessor-native-gates-design-review.md)也只批准设计，没有实现。实施前必须按各自最终固定候选重核上述身份和接口。

## 当前实现、缺口与真实调用图

|实际生产调用|当前事实|本片最小职责|
|---|---|---|
|`services.control/_prepare → reference.training_cycle_worker_command → cycle_main → _serve_cycle`|项目 revision／登记、应用 SDK、独立 cycle PID/event loop 已有；normal/stop 各一个 Worker／活动槽。服务只注册 v1 queue、旧类和六活动|在原服务内注册新版本，不增加新服务名、预算根或执行器；真实 argv、安装来源、注册与停止另验|
|`training_cycles.authorize_controller(program_version=2) → prepare_controller → _dispatch_controller`|schema3 storage-only 已有，六字段 intent 和封闭 type 映射已存在；`_controller_ready` 拒 schema3，dispatch 未核完整 input/Memo 容量|复用同一出生／claim／receipt 算法；M6 最终 gate 闭合后才可发送新类|
|`create_cycle_workflow → TrainingCycleWorkflow`|顶层可选 SDK／默认 sandbox 的旧首轮类已交付；只 ordinal0，不采测量|同 owner 新顶层 `TrainingCycleWorkflowV2`，保留旧类正文／旧 command 序列，不 patch 旧 history|
|`create_cycle_activities.invoke → _CycleOperation → S → processes.run(supervised=True) → H → _cycle_operation`|旧 six activities 已注册；operation-v2 只有内部 collect/reconcile 两 mode。SDK 父只监管，H 才读写原件|正式 v3 七活动、所有新 mode/source/context 的严格版本接线；H 的已有采集／发布／诊断算法继续复用|
|H `_round_operation → _round_gate/_round_local_gate/_round_previous → runtime.authenticate_round_collection + rounds.create/read + evidence + ExecutionRecords`|M2/M3 已有完整内部用例，原 SDK scheduled-event 完整扫描／decode 代码已存在；其内部服务替身不等于正式 V2 history|正式 creator 产生真实 command，真实 history 复验唯一 collect、恢复 existing-only 和本次完整 typed 结果|
|H `_candidate_operation/_CycleCandidate → training._prepare_submission → _Submission.dispatch → runtime lookup → CheckpointedClient.start_workflow`|旧源／原 intent／单次 attempt／固定 child run；ordinal0 与 schema3 门仍关闭|新 predecessor 在原 intent 出生前认证并冻结；不可由恢复的新观察替换；保留 attempt 同步后最后检查|
|`BudgetAdapter → LocalTrainingAdapter`；`Execution.check/request/admit → native_main → patched executor callback`|原 registry/execution/executor 锁、父共享许可、launch/attempt/ack/reaper 已有；budget.source、validate_context 显式拒 schema3|M5 同一严格本地 verifier 接到全部最后动作；M6 才验正向可达和同步后拒绝|

这里有两类不同的 input：总循环六字段 `workflow_input`，以及原 submission 中完整 native Experiment input；[reference_inputs.WorkflowInput](../../src/ergora/reference_inputs.py)是既有六阶段任务输入族，不为了新增循环类再造一个通用输入继承层。循环 dispatch 使用原 controller intent／封闭 type 映射；child input、memo 和 spec 仍由原 submission/runtime owner 认证。实际完整对象不能被缩成身份子集来验容量或 history。

## 新版本的封闭路由与注册

以下精确值沿 wire，不使用当前授权内容或“最新 type”猜版本：

|合同|旧版永久保持|新正式版|
|---|---|---|
|出生／program|schema1 手工、schema2/program-v1|新 ID 的 schema3/program-v2；现有 ID 不升降级、不补 sources、不换 clock|
|总 Workflow type／input protocol|`TrainingCycleWorkflow`／`ergora-training-cycle-v1`|`TrainingCycleWorkflowV2`／`ergora-training-cycle-v2`|
|normal／stop queue|`ergora-training-cycle-v1`／`ergora-training-cycle-stop-v1`|`ergora-training-cycle-v2`／`ergora-training-cycle-stop-v2`|
|activity envelope|旧 activity.v1/v2 原 shape|schema_version=3／`ergora-training-cycle-activity-v3`，wire 的完整 facts+selection+measurement|
|operation|原 operation-v1 不变|`ergora-training-cycle-operation-v2`，原十字段 identity；完整 activity_context 留 payload|
|status/outcome|旧 workflow-v1 shape|schema_version=2／`ergora-training-cycle-workflow-v2`；wire 的完整 status 字段集合|
|budget worker／ExecutionRecords|原协议|仍 `ergora-training-budget-v1` 及原 records/context schema；不为循环版本另开 launch owner|

新七活动的名字恰为 `ergora.training_cycle.<action>.v3`：`start`、`reconcile`、`request-execution-or-observe`、`observe-candidate`、`collect-round`、`reconcile-round` 在新 normal queue；`stop` 在新 stop queue。所有 ordinary 和 stop 的 SDK retry policy 均 maximum_attempts=1，wrapper 对实际 attempt>1 仍只读／对账。无 inspect.v3。`create_cycle_workflow`／`create_cycle_activities` 由原协议 owner 的封闭版本映射选新类／集合，旧调用缺省仍取旧版；不把两个版本混进同一 action→名字字典后让上层猜。未知版本拒绝，不能改所有 `==2` 为 `>=2`。

每个新 ordinary request 恰为 `{workflow_input,ordinal,predecessor}`；ordinal0 的 predecessor=null，k>0 为 wire 的完整 `{prefix,acceptance}`。stop/signal 恰为 `{workflow_input,reason}`。原 source 九字段、namespace/service namespace、固定 workflow/run、精确类／活动名／queue、非 local activity、attempt 均核完整值。`start_context.controller` 携完整前驱；source、payload identity、原 request、intent binding 必须逐值相同，不能用一个“已验证”布尔值跨边界。

operation-v2 必须覆盖新 ordinary 所用 cold `inspect-controller-activity`、prepare/confirm/dispatch/reconcile-candidate、request-execution-candidate/observe-candidate、collect/reconcile-round，以及 stop writer/notify/drain/observe-execution；新 controller prepare/submit/reconcile 的本地入口也按新原授权选协议。cold snapshot 尚空时由已验证新 activity_context 选择，取得 snapshot 后再核 schema3；不再按“mode 是否 measurement”决定唯一允许的 protocol/schema。mode→action 精确表仍在 protocol：例如 request 的 SDK attempt>1 只能 observe，start attempt>1 只能 reconcile，collect attempt>1 只能 existing-only reconcile，不再 create。旧 operation-v1 与旧活动的 mode 表逐字语义保持。

服务拓扑采用**同一现有 cycle 进程内四个 versioned Worker poller、两份业务配额**：v1/v2 normal poller 各注册本版本类及普通活动，共享一个 normal 执行许可；v1/v2 stop poller 各注册本版本 stop，共享另一个 stop 许可。各 SDK poller仍 max_concurrent_activities=1，共享许可只约束实际 invoke 生命周期，不共享 normal/stop 许可，也不把四 poller 称四份业务配额。许可由 `_serve_cycle` 一次构造、在实际 activity wrapper 持到原 operation/peer 全部 cleanup 返回；取消不能早放。这个单 owner 的局部 asyncio 许可不成为新 service/manager 或持久状态。

等共享许可也消耗已调度的 SDK deadline；在等待前固定原 cold/operation BOOT window，拿到许可后复用同一 window，不在拿到许可后重新构造冷窗口；SDK scheduled/start timeout继续限制整个activity，包括等待许可。随后与原 authorization/work/window 取 min。SDK 原 timeout 字段、converter 与此接线必须在固定安装实证；不能只靠本地 sleep 测一个 semaphore。旧 queue 的 payload/history/command 不变，混合版本共享槽仅改变排队时间，故需实测旧正常和 stop 不被新普通阻塞，记录可能更保守的超时拒绝。服务 shutdown 先停止并清理两 normal poller，保留两 stop poller可用，再停止 stop；fatal/取消/loop teardown 同样等实际 task。原 services CLI、argv、70秒 stopwait 与 budget worker 不变；若真实 SDK 注册或 lifecycle 不支持此拓扑，停止本子片并先审最小替代，不能默增配额或停掉旧 run 的消费者。

## 确定性有限循环及原机会

V2 在原顶层模块可由默认 sandbox 重新导入；core 无 SDK 仍可导入原只读代码。Workflow 只用 `workflow.now`、history、timer 和 typed inline facts；不读 Path/State、源文件、ref 或本地 clock。H 保存完整 observation/index；Workflow 不从 ref 补 facts。

1. 首个 command 是 observe-candidate.v3，仅一次 cold 引导。它固定真实 selection.count=N、common 和出生 measurement_sources 摘要、父 run 和原预算；首次不能确认 work/total 就停止／needs_reconciliation，不重开 cold。每个后续活动沿同 BOOT `D=min(旧D,scheduled_at+remaining)`，work/total 只缩，切轮、Worker 重启或对账不清空总截止。
2. 本轮依原事实决定 start 或只读 reconcile；每个候选 start_scheduled 在 command 前永久占用。原 attempt 已存在就只对账；lookup NOT_FOUND、发送未执行、reply 丢失均不返还。完整 intent 的 predecessor 由原 owner 一次保存。后续 request/observe 必须使用该原值，不能把 reconcile 后的新 acceptance 换入已出生 intent。
3. 原 child/runtime 与 native 共同 QUEUED、无 request/launch 且正面 source/window 才发一次 request-execution-or-observe；command 前占 request_scheduled。丢完成、SDK attempt>1、已有 launch、ack 或未知都只 observe，同一原预算根不重新 own／launch；原 existing result 早读仍允许。
4. 只有可信 native SUCCEEDED、原 phase 可接受且 durable/executor stopped 齐全才尝试 collect。archive 完整接受仍由本次 H 原 evidence owner 和最终 index 决定，Workflow 不从 phase 推 accepted。collect_scheduled 在调度前占用，ID 固定 `candidate-<k>-collect`、maximum_attempts=1；其他 ordinary ID 以本轮单调计数派生。即使 collect 未开始、返回 pending 或没有目标，也不再给 create：后续 reconcile-round 永远 existing-only。无现存完整目标时保守 unknown/停止，不为了稍后 archive 到达重新 publish。
5. H 以 `runtime.authenticate_round_collection` 完整扫描固定父 run（最多8000 events/8MiB），实际 converter decode 唯一原 collect 和当前 scheduled command 的完整 request/ID/type/queue。只有同一次 collect 首机会可 `rounds.create`；目标竞争输家和所有 reconcile只 `read`/同步原目标。丢 completion 时不要求未知 operation ID，不扫 operations/latest。恢复可重新形成自己的 observation/acceptance；已经出生的后继 intent 永不换绑。
6. `_consume` **先**核完整 received envelope 容量和严格 v3 shape，再核父固定身份、实际 source operation 在 inspection/operations中、当前 k/候选、原 binding/record库存、selection 三值不漂移和全部 measurement 关系。只有 status=observed、accepted、durable、ready=true 且 prefix/acceptance 同次完整正面，才把已确认 prefix 加到k+1；prefix.rounds=k+1、前缀/initial anchor与原值一致。坏 shape、容量、重复/迟到结果都不推进；进下一轮后不能消费旧 k 结果。
7. k+1<N 且最终 guard 仍正面才设置下一 k；仅本轮 identity／计数／三机会显示复位，旧机会和接受值仍由 history 恢复，总计数／deadline不归零。最后保留 ordinal=N−1、confirmed_rounds=N，outcome=`selected_rounds_observed`；未通过原 gate/质量/预算/来源的轮按原失败或 unknown 保留并停止。每轮256 ordinary commands（含 collect/reconcile），总 history8000 events/8MiB，先到即走唯一 stop；不能以 N×256 合法推导 history 一定容纳。

`request_stop`、cancel、预算/来源拒绝走原独立 stop queue；ordinary TRY_CANCEL，stop WAIT_CANCELLATION_COMPLETED/shield，唯一 stop command／原 total 预算不重开。stop 结果保留全部原 2+2N 分支；operation_stopped、父 drain、Workflow 终态和执行器 durable stop 分开，cycle-level stop_durable/admission_drained/executor_stop_confirmed仍按 wire 为 null，不聚合伪证明。已接受旧轮的人工 release 窗口不被统一 cancel。server terminate 不保证清理，须沿原本地 stop/原件对账；不能开新 Workflow/run、reset、continue-as-new 或重试 cycle 来续预算。

以上终止／成本阈值是已接纳的有限选择、原 wall/cleanup/control、原比较门槛和协议容量界，没有新产品决策。任意探索 loop、自动生成候选、收益 plateau/patience、新花费上限、baseline 滚动、跨 BOOT继续或用户 human/design硬关卡均需另提具体需求和用户决定，本片不擅加。

## M1c-V：完整实际编码与 failure 边界

`B=32_768`、Memo `2_048`、`M=protocol.ARTIFACT_LIMIT=10_000_000`；全部按最终表示而非字符数。继续使用原 `_cycle_capacity` 的实际 client DataConverter/完整 Payloads（含 metadata），Workflow 使用该 Worker 对应 payload converter。当前连接默认 converter，无自定义 codec；本页不承诺任意 codec后的大小。验收须由实际 invoke/dispatch/registered Workflow 经过下面每个 owner，不允许只调用 capacity helper。

|真实边界／落点|完整计量与必要反例|失败后行为|
|---|---|---|
|controller dispatch H `_dispatch_controller`|原六字段完整 workflow_input 实际 encode 后 Payloads≤B；原 intent SHA memo 所有 key/value 的真实 Memo protobuf≤2048，在 claim 前核并在最终 send gate复核；不得拿原 input SHA代替完整 input|原 intent/claim/receipt和完整来源保持，未 send 不返还已有 claim；不改短路径或新 ID凑界|
|child submission／runtime|原完整 Experiment WorkflowInput/spec、memo、started history和receipt 精确匹配；原 input owner的界保持，不能把循环32KiB误作所有 native材料统一界|原 start attempt保留；lookup/consume/完整history失败只能 unknown|
|V2 run、ordinary/stop发送、signal入站|每个实际完整 request/input经Workflow converter≤B，包括完整predecessor或reason；signal拒绝只记有界拒绝码|不发送截断 command；拒绝signal不称已停|
|SDK activity入站与 assembled result|实际 invoke入站先核；result在全部facts+selection+measurement+acceptance、inspection、所有operations、外层identity及metadata组装后核；N32 stop完整2+2N分支，混合refs/inline unknown也计入|原operations/原件和peer cleanup保留，整体非重试失败，不删后几项／不按分支“各自小”视总量合法|
|V2 `_consume`、query/status/outcome|received envelope在读取facts前核完整Payloads；真实query与run最终返回也核 wire完整status，不只核prefix。测试同时保留最新prefix／全部stop字段|不推进ordinal/prefix，不构造更小“成功”；query真实错误与run needs_reconciliation分别记账|
|新operation-v2 request、H stdout、S frame|完整compact request无LF≤B；H stdout包含LF≤B；frame含十字段identity、result、_stdout_ref≤B，仅delimiter LF不计；失败replacement再核一次，仍超界就不发result，stopped控制帧仍65536B|原stdout/raw与真实stopped/收尾保留，无完整result为unknown；不借stopped更大界发业务结果|
|SDK ApplicationError／实际Failure protobuf|新 wrapper只发有界固定type/message、non_retryable小错误，无raw/reason/大traceback/details；用本次client实际failure converter编码其完整Failure（message、stack、cause、details及payload metadata）并核≤B，检查真实server存入/返回的Failure|大原件留原H/operation与已审诊断ref；不把成功Payloads检查当Failure检查。若SDK最终会自动加栈/cause而使本地测量不足，须在原SDK错误出口最小适配并复审，不声称已闭合|

容量证据至少实际 B−1/B/B+1 的合法请求/封套、Memo2047/2048/2049、多字节UTF-8、各分支合界而聚合超界、H stdout合界而frame超界、完整failure实际编码与服务响应。不是每个helper各复制一套矩阵：由一组真实 producer→invoke→S/H→Workflow/SDK history覆盖相关最终owner，逐项说明哪些边界实际到达、哪些因较早拒绝没有到达。不能伪造非法shape凑长度后称合法边界通过。

父 assembled raw 超界只采用已批的失败专用流：同次UUID/immutable compact raw无LF，诊断S无业务后代、原完整clock/window watchdog、一次小确认、实际wait；正常成功wire不放宽。父不在SDK loop同步写完整raw、不另开线程／window、不把request诊断ref塞helper/stdout ref。磁盘、partial、deadline、取消或丢回复如实unknown，available材料保持；不能声称所有故障必然完整durable。当前父留存仍未整片验收；其内部collect/reconcile-v2接线不自动认证M6新增mode，须在M6原constructor和诊断控制validator同片明确接到严格的新mode表，语义仍仅按已批失败流。只要正常真实producer完整raw、故障unknown/收尾或新mode覆盖有缺项，全M1c/执行开放保持阻断。

## M1c-R 和 M5：在哪一候选、哪次最后检查开放

M2的真实core10MB `read_round_observation`只证明该reader。M1c-R须在**每个实际消费者**到达同一 `read_raw(path,ARTIFACT_LIMIT)`：H前驱再认证、CycleAdmission.bind、BudgetedStart.source、validate_context/Execution.current、native外层和executor callback实际后续阶段。index与observation的ref严格int bytes、普通同根固定路径、完整raw长度/SHA、观察LF、严格shape和全链绑定沿M5；不把默认1MiB全局改大，不重编码比raw。

合法>1MiB及M−1/M/M+1原件必须来自真实完整observation/index，分别经这些caller；最终动作正向或同步后拒绝在M6补到。M5早期关闭分支先拒绝时不能代验晚处reader/attempt/ack。全链最多31前轮，逐层沿原intent predecessor追到0、完整prefix逐值相等、原evidence.files和ExecutionRecords库存当前raw保持；不能只核最后SHA，不能扫描较短链或重采人工approval。

|原最后动作|M5应已接线且仍保留effect关闭|M6固定候选的实际正／负验收|
|---|---|---|
|H准备后继及原submission send|原predecessor出生前、intent同步后；原start attempt前和同步后send紧前|真实start成功；同步后改前驱/source/ROOT/stop/clock则保留attempt、无SDK send；已有intent不换绑|
|BudgetAdapter native create|父固定RUNNING认证后，原registry锁内lookup absent至create返回的source/window/stop检查|故意晚拿锁，H检查后漂移则无native request；已有job早读保持|
|Execution request/launch|原父许可和execution锁内publish前、文件同步后current|真实一次request/launch；同步后漂移保留已占文件、无execute spawn、不再offer|
|native外层和executor callback|外层父共享permit；executor锁内callback入场、attempt同步后ack前、ack同步后返回前，分阶段刷新原records|真实patched executor runner；attempt后拒绝无ack/started，ack后拒绝保留ack无started/runner；不以unused-launch checker拒绝自身阶段，不以已有ack授权重跑|
|collect/reconcile最终返回|最后parent RPC、最终index读后再完整本地source/project/ROOT/stop/clock，随后只纯投影|沿M2已修真实阻塞reader反例，在新正式history重复到实际invoke/consume边界，无late accepted推进|

ROOT/source继续原25项GATE_SOURCES精确集合 + 出生四measurement项，不新加任意路径配置。先核本轮原owner capability精确25及原manifest SHA，再由同一已pin `reference.verify()` 核包内283；另核所选安装descriptor/overrides/native interpreter/core/config/state，最后再核sources/stop/clock。四项只在schema3 authorization出生固定；25/manifest在原BudgetedStart.own的一次owner出生固定，ready不含它们。ordinal0 prepare尚无owner时只能核固定产品、四项、安装与ROOT一致性，不能补造授权manifest pin；owner出生同步后所有effect最后gate必须使用该原pin。native不导入State/SDK/jsonschema、不查询当前phase、不复制archive比较器。

开放不是先删 guard再补证据。M6实施先保留 `_controller_ready`、worker schema3拒绝、budget.source、validate_context及ordinal guard，完成新类/注册/wire和M5完整接线的静态审查与可达拒绝证据。再在**同一隔离M6片**逐点把新版本显式关闭改为严格已接通条件，连同全部版本/source表、容量和reader接线整体冻结为唯一待验收候选；不在冻结后继续改源码。该准确完整diff及容量/恢复证据由fresh审查，真实正向CPU两轮及安装/自身模板一起终核，才由根接纳导入；修正就另冻新候选并重核受影响证据。局部试运行期间只在授权隔离候选和新出生ID上验收，不向主产品宣布开放。任何位置未接、source/ROOT不齐或M1c未闭合就保留关闭，不以伪source/临时“trusted”参数绕过。

## 最小分期、证据与反例

下表是未来实施验收要求，本次全部未运行。各大项独立固定diff、更新PLAN/交付、保留失败与修后结果、自身原模板和新的fresh两轴；相同slice修finding可原reviewer复核，不要求审查报告再被审查。

|分片|最小完整交付／前置|客观验收与停点|
|---|---|---|
|R 前置父留存、M5-G/R|各自最终已审固定产品，按实际M2/M3接口重核；仅真实caller提取复用|原raw正常成功、故障unknown和全部peer/进程收尾；完整前驱/ROOT/最后gate接线，合法大reader各实际入口。此前仍关闭schema3效果|
|V1 正式V2与v3表达|worker/protocol/runtime及必要cycles原owner；严格类/表/mode/context/envelope、唯一collect与只读恢复；保留关闭|默认SDK sandbox真正Worker注册/重新导入；实际event/decode及未完成collect history，received-envelope/完整容量反例；旧v1三份原history replay与旧schema1/2/owner1/2，core可选SDK隔离。内部history/服务替身如实限定|
|V2 原服务与统一开放候选|V1与R已验；四poller/两业务配额、原argv/服务注册，完整M1c-V/R接线与原最后gate准备齐全|真实service CLI注册新/旧type与queues；normal长阻塞时stop仍完成原分支，混合版本无并发配额扩张；同冻结候选新出生schema3可真实start/create/request/launch/native，补齐所有reader和同步后反例，未通过不导入|
|V3 固定安装与真实CPU两轮|准确新非editable core/SDK/wheel、完整产品和冻结输入；原CPU资产/oracle/runner/Temporal均齐|至少两个既有候选真实顺序accepted archive，完整父/子history、全prefix和原五records；默认sandbox、replay/eviction/重启/取消/丢回复/预算/stop与真实进程收尾。只认证CPU控制与原数值合同；自身模板/fresh最终核后才称M6闭合|

真实CPU最小现场矩阵：

|场景|保留的真实边界与可验收结果|
|---|---|
|正常N=2|从真实services启动cycle/budget与原native worker/executor，经原dispatch一次送V2；两个实际Experiment fixed run/native job、原runner产成对数值、独立CPU oracle、原collect_and_gate accepted archive。父history有每轮唯一start/request/collect；prefix0/1、完整observation/五records逐字绑定，原baseline/manifest/质量阈值未变，无自动release/采用|
|父/子lookup与consume丢回复、晚到|分别在实际controller/child start送出后丢回复、collect发布/同步后丢H/SDK completion、返回后consume容量或shape拒绝。原attempt/launch/collect scheduled仍占用，lookup NOT_FOUND为unknown；reconcile existing-only，晚到旧ordinal不推进；已出生后继intent predecessor不被新观察替换|
|真实默认sandbox／版本恢复|固定包导出正式类，SDK默认sandbox Worker；原v1 histories与新真实V2完整history各按自己的type重放。实际Worker缓存eviction后再接任务、停/重启cycle服务和独立budget服务，重建同history状态，不新run/reset/continue-as-new/新clock；记录SDK版本、缓存配置及每个场景真正发生的eviction，不用仅构造sandbox对象代替。旧owner原source pin因新包变化时执行仍拒绝；能重放旧history不等于能用当前hash重授旧执行权，跨版本在途执行需保留对应原产品来源|
|机会消耗边界|start/request/collect command scheduled后活动没开始或服务掉线，恢复无新效果机会；index不存在仍不能create。child实际启动但receipt暂缺只对账同run；request/launch已占但无runner仍不重发。前轮phase/gate/reap按实际交错，不用合成accepted返回代验|
|取消/停止/预算|normal真实阻塞reader/fsync或registry等待时请求stop；重复signal、取消父Workflow、service graceful/fatal/实际SIGKILL再恢复分别记账。跨原BOOT/work边界继续只对账；total到期显式unknown，cleanup reserve仍原值。真实stop可见后锁内不spawn；server terminate不宣称reaped|
|容量完整链|真实N32 SDK-v3 stop全部refs/inline未知、实际完整Payloads/Failure/Memo/query/signal/outcome/receivedenvelope界；真实各10MB reader和超界诊断，源/ROOT/stop在最后读后变化；每个未到达的更晚gate明确未验，不借内部helper关闭|
|实际收尾|所有新建父/子Workflow终态分别核；原operation S/H、native runner/后代、budget root、诊断S/watchdog、managed services/监听与stdout refs按捕获完整PID/BOOT/start身份逐份核，实际wait/absent/unknown分别记。仅PID消失、SDKcancel、stopped帧或服务STOPPED都不代替executor durable stopped；不可回收如实保留未知及身份，不虚称全系统零残留|

仅服务替身或手构controller/SDK source的正面用例不能关闭V2正式现场；必须由真实父Workflow调度产生activity.info、scheduled history与同namespace/run。真实CPU正向也不证明真实模型/GPU质量、性能收益或硬件容量。原c1c/M2负gate、失败脚本/探针、旧CI结果保持，不重写为新通过。

## 最小文件、已有库与尚缺条件

产品预计触及原 `reference_training_worker.py`（正式类、v3 invoke、服务许可/收尾、真实capacity）、`training_execution_protocol.py`（严格版本/mode/source表及M5共用本地认证）、`training_cycles.py`（原ready最后开放）、`reference_training_runtime.py`（已有认证复用，按正式history暴露的最小差异补），并承接M5的budget/execution/submission/context原owner差异。`reference.py/services.py/cli.py`不预设新增业务逻辑：现有`services start/status/logs/stop`和命令构造已能启动原服务，注册变化在worker；若实证缺可传的必要参数再以薄入口单列。公开controller授权/dispatch/status交互仍归原c2，不新增通用CLI或Web状态机。

复用SDK默认DataConverter/Payloads/Memo/Failure、Workflow timers/history、Worker/default sandbox、原runtime bounded stream/decode、protocol raw/SHA/sync与round纯内容验证、reference.verify/validate_installation、原submission、ExecutionRecords、rounds.create/read与唯一evidence/comparator。新类因SDK要求module级可重导入而有必要；新增私有逻辑留原owner，非多实现选择不造ABC/工厂/新文件。M5实际不同生产caller可共用protocol算法，worker保留State/SDK/archive/publish编排；不复制archive reader或manifest walker，不修改283原参考/原native patch/descriptor，不加第二账本/current-round/proof/cache。

验证沿原 `tests/test_training_runtime.py`、`tests/test_training_submission.py`、`tests/test_services.py`、`tests/fixtures/training_cycle_operations.py`及controller/evidence现成fixture，保留真锁/fd/S/H/reaper/SDK event/converter/callback；只替与该缺陷无关的外部依赖。新fixture分支必须到真实待验owner，不mock verifier为pass。纯迁移与新增语义分块审；无独立新接缝不加测试文件/CI job。检查成本由原参数/预算推导，不能为过测试扩大时限、删保护或重跑无变化全suite。

外部条件现均未在本片确认：准确安装及SDK版本、可用Temporal endpoint/namespace与管理权限、真实已登记项目/revision、两个既有CPU候选和完整baseline/manifest/成对数据、可信CPU oracle与原runner/安装、原不可续预算是否足以容纳全链I/O、磁盘/可捕获进程与服务收尾条件。任何缺项只阻断对应现场与开放，不伪造源/资料、不缩质量合同、不借模型/GPU可用性猜训练成功。真实GPU/模型验收另需实际工作负载、设备、teacher/student/judge或质量oracle、完整输入/预算/独立质量证据；不在本次静态设计授权内。

下一步：根先安排本页fresh设计审；父留存最终固定与M5实施闭合后，以该精确联合产品重核接口/源表，选择V1的最小完整实现。每片计划/交付持续更新，完整M1c与统一开放仍在最终候选验收后才关闭。本文本次只进行了只读文本/Git/指定SHA调查及新文档静态校验；未运行tests/probe/install/replay/network/model/services/训练，未commit/push，也没有产品通过结论。
