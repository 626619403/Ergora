# c1c：正式 TrainingCycleWorkflow 首轮与恢复停止

日期：2026-11-16。状态：**详细设计fresh-context需求／可维护性两轴approve／0；固定消费者前置现已完整闭合并导入01ef，准备按W0–W10实施；正式Workflow尚无运行验收。** 承接[原具体合同](2026-11-15-training-cycle-controller-contracts.md)、[c1实施顺序](2026-11-15-training-cycle-workflow.md)、[runtime消费者](2026-11-16-training-cycle-runtime-consumers.md)、[执行消费者r2](2026-11-16-training-cycle-execution-consumer.md)及其[独立设计复核](../delivery/2026-11-16-training-cycle-execution-consumer-design-review.md)。本片仅让原六字段总输入在真实 SDK 默认 sandbox 中驱动 ordinal=0；c1d 闭合前绝不派发 ordinal=1，不输出 measurement_accepted／selection_complete。

## 身份、前置与不变合同

本次主树只读检查 HEAD 为 `691809563c410cc1f9d93bc6f821b313f7a2772b`，分支 `refactor/architecture-foundations`；主树有其他在途 docs，未改动。已验服务候选 `af176cf6e79adb9c6ef6f32946672bc77cdb89de` 已实际合入该 HEAD；[服务最终报告](../delivery/2026-11-16-training-cycle-service-final-review.md)确认产品／测试同一、四活动、独立 normal／stop 配额及真实 N32 服务边界，不认证正式 Workflow 或本片。

c1b2b 正在专属 `training-cycle-execution` 工作树实施，HEAD 仍为 af176cf，三个源码 owner 及必要 tests/fixtures 有未提交变化，**没有固定本片可继承的产品验收**。本次只读所见如下；SHA 只标识调查样本，不是批准候选，实施者继续修改后必须重核：

|调查文件|样本 raw SHA256|
|---|---|
|`reference_training_worker.py`|`3b072bde0888cccfbc0951512955dc79b7745ad697c6302882efaac41f5e78cb`|
|`training_execution_protocol.py`|`b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`|
|`reference_training_execution.py`|`c105ac8d2b248169b46a4c8a5692dbda90c7642e7907e7f19969345de1c7ea90`|

进入本片产品实施前，主控须固定 c1b2b 的实际三 owner／wire 合同、适用源码及新非 editable core／SDK 安装／真实服务证据和 fresh 产品两轴审查；本设计通过不能填这些格。若固定结果改变下面的 facts 或 mode 语义，先修订本草案再实施，不在 Workflow 内兼容猜测两套结构。

保留原六阶段、schema2 出生同意、完整祖先资源／权限收窄、原候选绑定、attempt-before-send、单次 native launch、原连续 clock 与唯一 reaper。控制器不生成实验、不升级旧 schema1／source pin、不批准 release、不迁 baseline、不增加实验账本或第二调度器。原 283 reference 文件、原 ExperimentWorkflow、原预算进程／queue／8活动槽保持。WA4 尚待人决策的通用设计／知识关卡、Repeat 和任意 Hook 不在本片。

## 已核生产链与本片消费边界

|实际 owner／caller|已核事实及本片决定|
|---|---|
|[worker](../../src/ergora/reference_training_worker.py) `_serve_cycle` → `create_cycle_activities` → `_CycleOperation` → S/H → `_cycle_operation`|已合入版只注册 inspect/start/reconcile/stop 四个 v1 活动；normal、stop 各一个槽，normal 尚无 workflows。新正式类只注册到这个 normal Worker，不放进原 `_serve` 预算进程。|
|执行树同文件新 `_execution_candidate_operation`|初版在冷 inspect 与新 ordinary H 产生分项 facts；无 intent／owner 可表达 not_recorded／not_requested。两个 v2 活动才传 facts，旧四 v1 不传 compute facts。真实 S/H 验收仍待 c1b2b，不把静态可达当通过。|
|原 `_CycleCandidate`／`_candidate_operation`|唯一 offer、prepare/confirm/dispatch 共用原 operation window，交接 root 后短 H 退出不杀 root。Workflow 使用旧 start.v1；不持 root/PID，不重新 ensure_owner。|
|[submission](../../src/ergora/reference_training_submission.py) `status/reconcile/dispatch`|候选完整 intent／attempt／receipt 及同 run 的恢复仍归这里。只有独立 reconcile 活动可补同一 receipt；Workflow 无文件读写，也不从文件不存在推新机会。|
|[runtime](../../src/ergora/reference_training_runtime.py) `lookup_controller_submission`／`lookup_controller`|前者核 first/original run、started input／memo／type／queue，允许原关闭 run 的投递观察；后者要求同一父 run RUNNING，拥有最后执行 gate。不放宽后者来迁就恢复。|
|同文件 `lookup/observe`|子 run 固定原 receipt.run_id；原完整 Experiment/input/memo 和 Binding/job 仍由 H 核。RUNNING query／COMPLETED outcome 分开；COMPLETED 不等于测量接受。|
|[Execution](../../src/ergora/reference_training_execution.py) `request/check/current` → 原 root `admit`|c1b2b 新 H 调原 request；锁内 publish 前后消费完整本 H operation window。唯一 launch 与原 executor 仍归原 root，Workflow 不调 native execute。|
|[protocol](../../src/ergora/training_execution_protocol.py) `ExecutionRecords.observe(durable=True)`|durable／executor stopped 是原完整链同步与重读的事实；native terminal、runtime phase、stopped 分开消费。Workflow 不实现第二 reader。|
|原 `training.evidence`／`training_rounds.create`|本片不调用。accepted archive、精确 phase/outcome、durable stopped、完整 rounds 追加全闭合才允许 c1d 开放下一候选。|

## 可选 SDK、模块身份与默认 sandbox

具体选择是**原被 pin 的 `ergora.reference_training_worker` 内、模块级条件定义的 decorated 类**，不新增 workflow 模块。Python 类名、`__name__`、`__qualname__` 均为 `TrainingCycleWorkflow`，`__module__='ergora.reference_training_worker'`，SDK `@workflow.defn(name='TrainingCycleWorkflow')`；run/query/signal 在同一模块级类上明确定义。增加 `create_cycle_workflow()` 显式返回这一类，唯一生产 caller 为 `_serve_cycle` 的 `Worker(..., workflows=[create_cycle_workflow()], ...)`。工厂不接 client、State、安装目录或候选，不创建局部类、不偷偷提交 Workflow。

装载布局如下，属于拟实现结构而非已经可用 API：

1. 模块顶部尝试导入可选 `temporalio.workflow`；仅捕获确切缺失顶层 `temporalio` 的 `ModuleNotFoundError`，设可选标记。安装存在但内部依赖损坏／版本错误继续可见失败，不把任意 ImportError 当“可用 core”。无 SDK 的 core 导入原 worker/protocol/runtime 仍成功；`create_cycle_workflow()` 被实际调用时明确报需 `ergora[temporal]`，不返回伪类。
2. SDK 可用时，原应用 owner imports 放进 `workflow.unsafe.imports_passed_through()`；无 SDK 时用 stdlib `nullcontext()` 保持原导入。这只让 State/reference/budget/execution 等既有依赖在 sandbox 导入时复用，**worker 本模块与 Workflow 类仍由默认 sandbox 重新导入**。不把整个 worker 放进 pass-through，不用 sandboxed=False、不调 `sandbox_unrestricted()`、不新增线程执行领域工作。
3. 在模块作用域的 SDK 可用分支定义真实 `@workflow.defn` 类，工厂只选已经定义的类。类只调用 SDK deterministic API、stdlib纯编码、protocol 的既有纯 shape validator／常量；不调用该模块其余持业务状态的方法。原 `_CREATING`／`_ROOT_OBSERVERS` 只归活动／预算运行，不由 Workflow 读写。
4. `_serve_cycle` normal Worker 增加该 workflows 列表；stop Worker 继续只有 stop activity，配额仍1。所有业务 SQLite、文件、锁、fsync、同步客户端都留 H／原 root；SDK父loop只有原异步监管与有界编码。原 normal-first 关闭时序保留，stop Worker 到 normal 的真实 S/H cleanup 退出后才关。
5. `cycle_main` 的当前安装路径与 SDK 默认 sandbox 对 package 的重导必须实测。现有 `reference_worker._ErgoraPackage` 是既有另一个入口的兼容方案；仅当新非 editable 安装实际复现 package发现失败时复用这个 owner 的现成 finder，不能为预防未知错误新造 importer。它不是默认已需的本片改动。

本次只读了已有 SDK 1.34.0 的源码：`workflow/_definition.py:140` 明确拒绝 run 的 `<locals>` qualname；`worker/workflow_sandbox/_runner.py:132–144` 按 `cls.__module__` 和 `cls.__name__` 执行 `from module import class`。因此不能在 serve／factory 内临时造 class，再靠导出 alias、改 qualname 或关闭 sandbox 绕过。上述可选导入布局仍须由真实默认 `SandboxedWorkflowRunner`、实际 Worker 注册和新安装重导分别证明，本次未执行这些检查。

## Workflow wire、query 与 stop signal

run 入参仍是严格六字段 `protocol, control_home, project, cycle_id, input_sha256, authorization_sha256`，不增加候选数组、确认／actor、run、当前配置或 deadline。原总 producer 持 intent→唯一 attempt→start→固定 run receipt 与 memo；不改投递策略，不使用 continue-as-new，不跟随 retry/reset/新 run。Workflow activity request 仅构造原 `workflow_input` 与 ordinal=0，stop 另加 reason。活动名、queue 常量由原 protocol 取得：

|动作|活动／用途|
|---|---|
|初次与后续普通观察|`ergora.training_cycle.observe-candidate.v2`，ordinal0；唯一初次冷预算入口|
|唯一可能的新候选 start|`ergora.training_cycle.start.v1`，ordinal0；内部既有则只对账|
|原候选投递恢复|`ergora.training_cycle.reconcile.v1`，ordinal0；只补同一 receipt，不重发 start|
|唯一可能的执行请求|`ergora.training_cycle.request-execution-or-observe.v2`，ordinal0|
|停止|`ergora.training_cycle.stop.v1`，`ergora-training-cycle-stop-v1` queue|

建议 query 名 `status`，signal 名 `request_stop`；与原 ExperimentWorkflow 的 request_cancel/release 无关。signal 入参是 `{workflow_input, reason}`，复用原 stop request shape、完整六字段匹配与容量校验。只记录第一个合法停止意图并唤醒等待，不在 handler 中调活动、读文件、RPC或自动 cancel 子 Workflow；重复合法 signal不重开停止窗口、不调第二次 stop。reason完整保留，非法／过大输入在query中记录typed `last_signal_rejection`，不切片后采用，也不在signal handler抛未处理异常使同一坏signal无限失败Workflow Task；拒绝不会阻止之后有效的停止意图。signal到达时已经进入server history，应用校验不能撤销该事件。该 signal 在同一可信用户边界内是停止意图，不冒充 SSO／actor认证。

query／最终 outcome 定义为小型控制观察：`schema_version=1, protocol=ergora-training-cycle-workflow-v1, workflow_id, run_id, input_sha256, authorization_sha256, ordinal=0, phase, outcome, observation_count, start_scheduled, request_scheduled, last_normal_activity_id, stop_activity_id, stop_activity_status, last_facts_operation_id, last_signal_rejection, continuation='disabled_until_c1d'`。另有 `measurement_accepted=null, stop_durable=null, admission_drained=null, executor_stop_confirmed=null` 的未确认字段；不能用 stop transport成功填 true。正常 facts 中已有真实 executor_stop_confirmed 可作为单独 `candidate_executor_stop_confirmed`，不扩大成整个 cycle 的 stop证明。各字段随确定性内存状态由 history重建，query不改变计数、不刷新预算、不调活动。

query／outcome 不是完整报告的裁剪副本，其 schema从一开始只提供上述观察和 history activity IDs；完整活动封套及 ref 在 history／原 H文件里，沿原 owner查阅。无需将全部历次封套、候选清单或大错误再次拼进 query。大错误由原完整 failure／H日志保留，控制 outcome只给 typed reason 与原 activity ID；不把不完整文本称“完整异常”。每份传输仍须完整编码检查，无法容纳就可见拒绝，不能静默省字段。

## 首轮确定性状态与一次机会

状态只活在 Workflow 实例／history：`COLD_OBSERVING → STARTING/RECONCILING → WAITING_FOR_QUEUED → REQUESTING → OBSERVING_EXECUTION → FIRST_ROUND_OBSERVED`，任一阶段可转 `STOPPING → STOP_OBSERVED/NEEDS_RECONCILIATION`。这些是本控制器阶段，不冒充原实验六阶段或原 job状态。每次调度前先处理停止意图、预算、容量；所有分支只看已完成活动结果、已记录的 command 和 SDK deterministic时间。

1. **一次冷观察。** 首 command 是 observe-candidate.v2 ordinal0，固定冷 SDK窗口10秒、最大attempt1。它可以从 inspection 或 ordinary operation返回 facts；只接受 source_operation_id 与同封套 inspection或operations中实际 operation_id匹配的投影。cold基础 facts合法不代表 runtime已查过。缺 facts／认证失败／未知预算则不start、不request、不自动再来一次冷探测。
2. **选择固定首候选。** 首份认证 facts 固定 candidate experiment_id／manifest_sha／project_revision及父 controller三字段；后续每次核同一六字段输入、同一 `workflow.info().workflow_id/run_id`、同一controller intent_sha、ordinal0及完整候选身份。H仍是完整原件认证owner，Workflow不凭 ref.path猜状态，也不重读 raw来“验证”ref。父run拒绝/漂移、source/project/clock身份未知均停止新效果。
3. **决定start或恢复。** 只有 `status=observed`、完整同一候选、budget valid且正、project_matches=true、parent_stop_visible=false、submission=not_recorded、attempt_saved=result_saved=false、execution=not_requested且无原记录摘要时，才调度一次 start.v1。`start_scheduled=true`在创建SDK command之前设置；已调度后不论成功、timeout、ActivityError、not_attempted或文件不存在都不再start。初始已prepared/unknown、有intent/attempt、已有execution等只恢复观察，不能接管无完整同一controller绑定的人工运行。submitted有固定run则直接观察；rejected／部分损坏／身份不明进入停止／对账。
4. **v1桥接。** start/reconcile的`observed`不是submitted许可，它们无compute facts。只保留其完整history结果并沿旧 observation收窄total；在同一已有work截止内调用下一次v2 observe，取真实submission。prepared/unknown且原attempt存在时允许旧reconcile作为有界恢复；其可能写同一receipt，不重新start。没有attempt的prepared无法靠对账证明已提交，单次恢复仍未submitted则needs_reconciliation，不无限循环碰运气。
5. **双QUEUED等待。** submitted／receipt先到不立即request。唯一request尚未调度时，继续有界observe，直到同时有runtime queried、terminal=false、phase=QUEUED、同一run及完整binding/job，native=QUEUED且同job，execution=not_requested，project_matches=true、parent_stop_visible=false及正预算。runtime=SUBMITTING且native未发布是正常可达等待；两者非原子，下一观察再核，不合成QUEUED。任一runtime/native/job身份冲突不重试效果。H最终仍重新核原job/父RUNNING/最后锁内window；Workflow就绪只决定是否请求。
6. **唯一request。** 调度前置 `request_scheduled=true`，最大attempt1。无论返回requested、existing_only、not_attempted、unconfirmed、失败或丢completion，之后只observe，不因request.json absence重新请求。不新建request-attempt账本；该机会消耗由这条 history command表达。初始已见request/launch/attempt/ack/stop记录，直接只观察，request_scheduled可保持false但既有链永久阻断新request。
7. **运行观察。** 分别保存runtime/native/execution；native SUCCEEDED不推gate/accepted，reap先到不推原phase，phase先到不推durable。RUNNING、launch_consumed／acknowledged等在预算内等待下一观察。明确native FAILED/CANCELLED、runtime失败/取消/NEEDS_RECONCILIATION、GATE_FAILED等转停止/对账，保留原typed state，不臆断“无收益／质量退化”。对RPC unconfirmed等未知只允许有界只读再观察，不恢复效果权。
8. **首轮交接终点。** 当同一run的native=SUCCEEDED，execution.durable_stop_confirmed=true且executor_stop_confirmed=true，runtime实际phase为AWAITING_RELEASE，或固定run outcome为RELEASE_EXPIRED／INTEGRATION_TASK_CREATED，才可结束为`first_round_observed_c1d_required`。这是“可交给接受层调查”的观察，不是measurement_accepted；本片不补archive／rounds，不判断原gate报告。原实验保留人工release窗口，正常终点不向子Workflow发cancel或统一停止旧轮。总run关闭后不能靠新安装从此终点继续ordinal1；c1d改变的是未来新授权运行的程序，旧历史只读恢复。

所有ordinary调度（含cold、start、reconcile、request、失败与仅观察）在发command前消耗首候选计数，**至多256**；SDK内部attempt全为1。正常SUBMITTING／RPC未知等待也计入，不以只统计成功或只统计poll的方式越界。等待节奏建议用确定性1秒timer，取`min(1秒, 剩余work)`；到点再核全部gate。不要发忙循环，不为短预算向上取整；该间隔仅调度节奏，不扩大control/compute。

未知的处理需要区分可消费分项和效果许可：完整本地事实可以在整体unknown中继续保存，明确SUBMITTING／native未发布可以等待；**只有整体observed且完整必要正面事实齐全才调新效果**。缺完整认证投影、坏链/source/父run、候选身份漂移、unknown clock或project不能靠普通重试治愈，停止并留原件。若c1b2b固定结果不能区分“正常尚未就绪”与认证失败，先把该分支保守归needs_reconciliation，并回报producer缺口，不能按error文字猜原因。

## 原截止的继承与回放

Workflow不用`time.time/monotonic`、本地BOOT、文件时间或H observed_at与服务器绝对时间相减。H的原BOOT/UTC连续性核对与最后effect gate仍是授权权威；SDK截止只增加更保守的上界。

设活动调度前的history时间为`A=workflow.now()`，结果处理时为`R=workflow.now()`，H末采样给`w=work_remaining_seconds`、`t=total_remaining_seconds`。首份可认证样本建立：

```
D_work  = A + w
D_total = A + t
以后同类新样本：D = min(旧 D, A + 新 remaining)
在任意当前 history 时间 N：remaining = D - N
```

等价于收到结果时先算`w-(R-A)`／`t-(R-A)`再加到R。H末采样已经扣过H自己的耗时，这里故意再扣完整队列／活动／回传耗时，可能较早耗尽；**不使用R+remaining续满窗口**。旧v1 observation只可收窄D_total，不能产生或放宽D_work；无合法新样本时继续旧绝对界，失败不把预算重置为控制常量。各新样本boot_id须延续已认证样本，remaining必须有限数字（bool不算数字），负值保留耗尽含义；unknown/null不伪造0或新预算。

|窗口|精确规则|
|---|---|
|首次冷活动|调度前固定`D_cold=A+10s`，schedule_to_close=start_to_close=10s；只读，失败不再用另一10秒cold重获预算。没有任何预算样本时不调业务效果。|
|后续ordinary活动|在调度时N取`B=min(D_work-N, original_control_timeout_seconds, 10s)`；B≤0不调度。`D_op=N+B`记录在history command时序，SDK schedule_to_close=start_to_close=B，RetryPolicy(maximum_attempts=1)。各阶段timer、排队、网络、失败均自然扣原D_work/D_total。|
|同一次operation的control|原H cold/prepare的BOOT window及后续mode共享窗口由前片owner持有。SDK重放重新产生的是同一command，不以重放时刻重算新窗口。不得catch timeout后以新activity ID重发同一start/request。新的只读观察有新的有界operation，但它的B始终受从未延长的D_work约束；这与重开旧effect窗口不同。|
|停止|只用最近已认证并收窄的`D_total-N`作为stop SDK schedule_to_close/start_to_close，最大attempt1，使用独立stop queue；不拿work或control替代total。total未知／非正不新调effect，不给“清理额外10秒”；报告未确认，保留原本地stop／离线对账入口。|
|worker／server重启|A、D与计数都由原history重建；重放不得读取当前墙钟决定新效果。恢复有新workflow task时SDK deterministic now推进，先核旧D，再调下一只读观察/H最后gate。历史里已完成activity不再次执行；未完成SDK command重派同activity最多发生原attempt语义，不发新effect command。|

服务器history时钟与H BOOT并非同一时钟，保守扣减不宣称消除任意服务器时钟故障。服务器停机／重放虚拟时钟不足以给旧H权力：每次真实H、原root、native最后gate仍核同一授权BOOT与stop。验证必须包含server暂停／worker停机后原compute已尽，恢复不产新request/launch。没有新的H成功样本时，即使SDK clock信息不足也不从旧facts自动再授效果。控制器不会为了恢复把原clock换成新boot、刷新source pin或重建授权。

## 独立停止、取消与实际资源收尾

signal、SDK Workflow cancellation、正常预算尽、观察/history容量界、明确失败都进入同一个确定性停止出口。`stop_scheduled`在command前占用一次；stop.v1用原六字段与完整reason，走独立queue，所有已选候选的2+2N fanout仍由原stop owner生成，Workflow不按“仅首轮”裁剪分支。原stop本来就只做writer／drain／精确owner通知和execution观察，不自动给旧实验发Temporal cancel。

1. 活动pending时，run持有SDK activity handle，通过SDK deterministic `workflow.wait`／`wait_condition`等待“活动完成或停止意图”；不得直接让run的可取消await把ordinary的实际清理变成进入stop前的阻塞。主run的取消等待必须shield保留ordinary handle，取消catch可先运行。signal唤醒wait后，或run捕获取消后，显式对ordinary handle请求取消，同时在有正D_total时立即调stop，**不等待ordinary取消完成才让stop排队**。SDK ordinary现使用`ActivityCancellationType.TRY_CANCEL`：发送取消请求、释放Workflow等待，不将handle状态称为实际资源停止；实际S/H／root／reaper的清理和等待仍由原活动及normal-first Worker关闭持有。最初r4选择WAIT_CANCELLATION_COMPLETED的历史决定由下述r5纠正取代。所有handle都有明确持有者，不新增未受控的后台派发任务。stop自身由独立保留的task/handle等待，重复signal／cancel不创建另一个stop，也不取消这个cleanup等待。
2. run捕获SDK可见的取消异常，保留原取消事实，进入同一stop出口；stop等待用SDK支持的shield模式防止再次task cancel丢弃唯一handle。停止完成／失败或原D_total到点后，记录结果并传播原取消，使总Workflow保持CANCELLED语义；signal停止则返回本片typed outcome。SDK抛CancelledError、ActivityTaskCanceled或父CANCELLED均不意味着S/H已停、许可排空或executor停止。
3. 若已发start/request正在RPC或同步fsync，原attempt/window/最后gate保护晚到动作；Workflow未知仍不再发。stop与ordinary cleanup并行，原S保留实际spawn／后代直到原reaper收尾。SDK deadline到期、服务shutdown与OS实际wait是分开的事实；本片不能把SDKtimeout变成operation_stopped=true，也不能为了等回收延长授权。原不可中断OS调用／进程cleanup的资源义务仍由service/S/reaper继续承担。
4. 停止过程中worker正常重启时，原stop command及ID由history恢复；SDK不增attempt，未完成command是否被server超时保持真实失败。后续不自动发另一个stop来重开total；操作者可用原独立本地stop/status/reconcile显式对账，仍消费原total和精确原件，不重start。服务正常关闭本身不等于业务stop，已交接root沿原合同保留自主预算收尾。
5. 最初cold尚未返回时signal可先记录，仍只等待这一次已有只读cold来取得total；不再进入start。SDK cancellation若使cold结果无法取得、facts=null或预算未知，则不能凭“总Workflow应清理”临时授一个stop SDK窗口；标记停止未确认，给原本地恢复路径。server terminate／外部SIGKILL没有可靠catch/finally，保留本地stop／固定run对账手册分支，绝不宣称自动清理已完成。
6. 正常首轮终点已确认原executor durable停止且处于release观察，不额外停止／取消旧轮；用户此时的stop只禁止后续控制效果，不能追认测量接受或release。首轮之外候选始终没被本Workflow start/request。

**当前stop事实缺口必须保留。** 旧stop.v1返回完整refs＋父inline，Workflow不读ref；没有可直接消费的cycle级`stop_durable/admission_drained/各executor` typed汇总。因此本片最多证明“唯一stop活动被调度／返回了完整观察封套”，最终stop字段保持null／needs_reconciliation，完整证明沿原文件／既有reader查。不得仅以envelope.status=observed或所有operation_stopped=true填业务停止成功。若产品要求query直接认证这些分项，须在原worker/protocol另做明确版本投影扩展并审查，不能静默改旧stop结果；本草案不擅加该产品。

## 容量、history与unknown的硬界

沿原合同，每个完整SDK input/activity result/signal/query response/outcome ≤32KiB（含实际Payload encoding metadata），memo≤2KiB；原plan／rounds≤10MB，选定列表1–32。Workflow不改server上限，不传大snapshot，不截reason、binding、身份、异常或stop分支。

活动请求／结果继续由原`_cycle_capacity`按实际client DataConverter编码；Workflow的纯input/signal/query/outcome投影用`workflow.payload_converter().to_payloads_wrapper(...).ByteSize()`或等价公开API同步计算完整Payloads。当前`perf_temporal.connection.connect`实际使用SDK默认converter且无codec；此设计验收只支持该已核边界，未来自定义codec／converter必须在真实边界重验，不能把纯JSON长度当其编码长度。本片不引入异步converter RPC、压缩器或传输文件新框架。拒绝的超限query可见报错；合法query与最终outcome必须由固定字段和真实编码验收，不能以返回空对象过关。

每次ordinary活动或等待timer之前核`workflow.info().get_current_history_length()`与`get_current_history_size()`；达到8000 events或8MiB便不再普通调度，转一次stop并终止，留余量而非continue-as-new。stop与最终固定投影占预留空间，不再递归poll或累计大结果。服务端已接收的外部signal可能瞬间增加history，应用guard不能承诺抵御无限外部signal或低于本域合同的部署上限；实际server拒绝必须保留unknown，不自动换run／调高上限。所有计数、history分支与已发command由history恢复，query不能重置。

容量失败、SDK ScheduleToClose／StartToClose timeout、原H late result、NOT_FOUND、RPC错误、完整source/identity漂移均不得转成功；能取得的原件留存，不删除partial记录重试。容量错误的完整未发送值仍由原活动日志／H归档，不在Workflow把其文本截成“成功的摘要”。停止的结果过32KiB可以导致stop活动非重试失败，仍不抹去已经完成的65个peer等真实原件；Workflow保存failure与activity ID并needs_reconciliation。

## 实施位置、实际caller与可维护性约束

|拟改函数／位置|实际生产caller与已有替代|限定责任|
|---|---|---|
|原worker模块顶部可选SDK／pass-through导入、模块级TrainingCycleWorkflow、`create_cycle_workflow`|SDK sandbox按模块名重新导入；`_serve_cycle`一次工厂消费。已有`reference_workflows`是六阶段composition类，语义和source pin不同，不能把本类塞过去。|保留同一被pin owner；工厂是可选SDK构造边界，不是插件注册器。|
|`TrainingCycleWorkflow.run/status/request_stop`|Temporal真实run/query/signal三个框架入口。|run只编排首轮和停止，status纯投影，signal只记录意图。它们无第二个应用caller亦有明确框架方法必要性。|
|类内私有activity调用／结果消费／停止等待方法|仅本类run与其停止出口；不制造第二生产caller。|内聚隐藏command前计数／D界、v1/v2 facts消费及唯一stop生命周期；优先少量类方法，不建manager／backend／generic loop模块。|
|原worker `_serve_cycle`|原`cycle_main`，由既有reference/services启动。|normal添加workflows注册；不换process/queue/1:1配额，不动原budget入口。|
|protocol原常量／纯validator（若确有新增wire校验）|原worker框架入口／SDK活动和H已有使用。|只扩实际必要纯shape验证；无SDK／State依赖，不为Workflow状态另开schema账本。现有activity validator足够的输入直接复用。|

首选本片只改worker及必要已有tests/fixtures；不预设需要新production模块或改runtime/submission/execution。若c1b2b固定facts缺必要数据，记录最小producer缺口交原owner，不在消费者open文件或造另一个reader。新source bytes由未来新owner出生冻结；旧live owner不在升级后继续执行，新授权/新cycle身份与旧历史读取分开。原CLI/HTTP/public service交互仍c2，不借本片新增自动启用开关。

## 最小可达反例与真实验收

以下是后续实施验收要求，本次均未执行。优先扩原`tests/test_training_runtime.py`、controller/SDK现有测试与`tests/fixtures/training_controller_service.py`／`training_submission_client.py`；CI机械拆分合入后按实际归属迁移，不新增重复job。局部SDK sandbox／Replayer不等于真实server；替身原件不认证真实executor／训练质量。

|节点|最小可达反例／接缝|须取得的证据|
|---|---|---|
|W0 默认sandbox与无SDK|core解释器无temporalio；SDK在全新sandbox仅按module/name import；factory局部class方案原SDK会明确拒绝。|新core安装可导入原owner、factory可见缺SDK；SDK默认runner准备＋真实normal Worker注册TrainingCycleWorkflow，类的module/name/qualname固定，无sandbox关闭、无未pin新模块。保留原budget服务独立PID和注册。|
|W1 正常首轮／延迟就绪|真实start receipt先到，原子Workflow SUBMITTING/native request未发布；之后同run双QUEUED。|正式Workflow先observe等待，history只有一次start和一次request，真实原request→root→唯一launch，最终三事实分开、首轮交接状态、ordinal1从未派发；原release窗口保持。延迟可由harness在原job创建／首次poll边界控制，明确注明注入位置。|
|W2 发前/发后丢completion|start/request调度后，分别在publication前、fsync后失去activity completion；请求文件可能不存在。|真实history已有command则不发第二effect；submitted通过原reconcile、request只observe。核原attempt／request／launch数量与SHA、root身份不变，不只断言mock函数调用次数。最大attempt1及真实server activity状态分别核实。|
|W3 worker重启和history replay|在WAITING_FOR_QUEUED或request已发后停cycle worker，再重启同安装；另对实际导出history做Replayer。|同run、同A/D、同计数、同activity ID恢复，已完成活动不重跑、未知effect不新增command、不跟新run；原件／clock不变。失败/终态历史亦replay，不能仅验证一条happy path。|
|W4 排队／RPC／等待预算|H末样本w=配置的短余量，故意让activity排队/回传消费大部分余量；或在v1 start/reconcile之后才恢复v2。|真实SDK command timeout来自A+w而非R+w；新样本只收窄，v1不刷新work，timer消耗同D，非正无request。使用fixture配置导出断言，不固定某机秒数；server停机至BOOTcompute已尽再恢复无新publication。|
|W5 独立stop／重复取消|normal S/H真实锁/读/fsync阻塞；signal或SDK cancel在RPC/同步边界到达，再重复cancel；stop worker独立运行。|stop command立即去独立queue，不排在normal cleanup后；只有一次stop、未续total；真实2+2N refs/inline、父许可/原链分项、全部S/H/后代/reaper实际wait。CANCELLED与业务stop证明分列；total不足/服务不可用为unknown。|
|W6 三事实交错与c1d硬门|native成功先于reap，reap先于phase，AWAITING_RELEASE但archive/gate尚未读取；另GATE_FAILED/native FAILED。|不以任何单项或observed输出accepted；只在本页交接条件成立结束首轮，始终无ordinal1，无evidence/rounds写入，无旧轮Temporal cancel，负结果无伪质量分类。|
|W7 256与history界|正常未就绪及失败混合消耗到第256次；真实server运行history/size至门槛附近。|第257个ordinary command不存在；失败/重放不重置count；达到8000/8MiB前后guard行为及预留stop command用真实history核。局部SDK替身可补精确边界，但至少一次真实server阈值触发，不能只断言常量。|
|W8 SDK完整编码|含metadata恰过32KiB，长完整binding/reason，合法最大片段query/outcome，实际stop封套容量失败。|完整Payloads字节核验、超限整体拒绝、原始完整错误/refs保留，无截断，无重新start/换run。memo维持2KiB原gate；不重复服务片N32全矩阵认证无变化fanout。|
|W9 source／身份／旧安装|父memo/input/run/queue/type/namespace漂移，project/source drift，旧schema1和旧pin。|原H/最后gate拒绝新effect，不被Workflow positive facts绕过；完整历史读及原显式本地停止路径保持。旧包不计为新安装，worker改source后原owner无续权。|
|W10 真实包／服务与收尾|c1b2b固定基线后形成新candidate，不复用前片081aab45认证新源码。|新wheel→core/SDK site完整身份、283参考/依赖、冻结输入；实际默认sandbox正式Workflow正常首轮及代表性重启/丢reply/取消、独立queue；实际原request/root/native链与进程/端口/Workflow终态。CPU oracle／真实训练／GPU分列，不能由本片控制合同声称性能或质量收益。|

W1/W2/W5的真实server场景使用同一项目既有live harness和全新授权，完整记录source／wheel／SDK/server／输入原件、每个实际command/result/history、原manifest/baseline/owner/request/launch/stopped身份和所有自建进程清理。不能以测试Workflow冒充本类，不能让fixture直接写期望facts替代producer。若现场只用CPU受控runner，明确它验证调度/执行链而非训练质量。真实质量oracle与两轮接受仍留c1d/d，不把本片扩成通用Repeat。

## 本草案已做／未做与交接

本次执行只有AGENTS/PLAN/组件协议、适用skills引用、原方案/设计复核/服务终报、实际owner与已有SDK源码的只读调查，Git/文件SHA核对及本文件文档检查；没有产品改动、测试／sandbox执行、安装／构建、网络、服务／训练、模型审查、commit/push。唯一写入是本页；未改PLAN或他人交付。

下一步由主控安排fresh-context设计两轴审查，重点核模块级可选SDK重导、A+w保守预算、history一次机会、取消/stop handle时序与stop事实缺口。处理实证finding并取得设计结论后，再由主控结合c1b2b固定产品/验收决定实施。c1d接受／rounds／后继、c2公共入口和WA4人决策边界继续开放。

## 独立设计审查接续

本草案已取得[fresh独立设计审查](../delivery/2026-11-16-training-cycle-workflow-first-round-design-review.md)需求／维护性两轴approve、开放0，仅设计层通过。c1b2b的job身份修正、准确源码固定与新包／真实服务／独立产品验收仍是实施前置；本页不认证正式类、默认sandbox、首轮运行或停止。前置闭合后按W0–W10逐节点实施和记账，不能借本设计结论越过实际验收。

2026-11-16接续：固定消费者bcc3048及wheel55029的新安装／SDK-free／自身模板／真实六活动和原预算根/native CPU现场均已[最终独立两轴approve／0](../delivery/2026-11-16-training-cycle-execution-product-review.md)，并真实导入开发树01ef。src／脚本／CI／配置与bcc逐字同一；tests仅多已另审的两行Windows提前skip。本片[静态实施准备](../delivery/2026-11-16-training-cycle-workflow-first-round.md)已核固定facts足够保守消费，stop汇总缺口及unconfirmed含义维持原设计，不改producer猜原因。实施前置现已闭合；之后新字节的新包、默认sandbox／正式类／history／真实首轮仍由本片逐项验收，不能继承前片的测试Workflow通过。

## r5 SDK取消策略的实施纠正

初始已审设计字节（SHA256 `d01d5774d592e21178cdabc2a918a61c7ba7f32a673daf6ac321849b28a8dbcb`）为ordinary选择WAIT_CANCELLATION_COMPLETED。真实W7取消现场及[独立最小诊断](../delivery/2026-11-16-training-cycle-eviction-diagnosis.md)证实SDK1.34已请求取消但尚未确认的handle会在eviction重复cancel时早返，导致Worker和Replayer挂起；此低层SDK选择现由[最小修补](../delivery/2026-11-16-training-cycle-eviction-fix.md)改为ordinary TRY_CANCEL，stop保持WAIT／shield。它不改变一次机会、原截止、原stop许可、S/H实际清理或业务停止证明合同。旧history／失败／设计审查仍按原字节身份保存，新源码／新包／新现场需分别验收，不能由此次设计纠正追认通过。
