# c1b2b：原执行请求与有界运行观察消费者（设计草案）

日期：2026-11-16。状态：**r2独立设计复核两轴通过，尚未实现**。本片承接[已批准控制器合同](2026-11-15-training-cycle-controller-contracts.md)、[c1实施顺序](2026-11-15-training-cycle-workflow.md)与[后续消费者缺口](2026-11-16-training-cycle-runtime-consumers.md)。设计基线为隔离服务源码 `eedba08c8c112683a7946726aab3f4fd590f26d6`；主树 `478c98891522930817fa7005a8ac96e408f37230` 尚未包含服务产品。服务 R1–R4 源码复核与 package-r2 安装／真实验收分别记账，本页不声称后者完成。

## 事实、建议与未决

**r2修订状态。** [初次独立审查](../delivery/2026-11-16-training-cycle-execution-consumer-design-review.md)需求轴request-changes／2、维护性approve／0；已明确最后请求window gate、两mode工作窗口分类、双QUEUED等待、request一经调度不再请求及cold ref可在inspection中匹配。原reviewer已追加复核，两轴approve／开放0；仅设计finding关闭，产品仍未实施。前置服务后继候选97a0bbf的launch容量修正与新包验收另记，不把前置现场结果转作本片证明。

**已核事实。** 服务只有四个 v1 SDK 活动、normal／stop 各一个槽；没有正式 TrainingCycleWorkflow。H 的 snapshot 在父封套中只保留 ref；observation 只有 total／时钟，`observed` 不代表已提交、已执行或已接受。原 `Execution.request` 已执行完整确认、固定父 history 与子 run／QUEUED／job 检查；原预算根已等待 request 并通过 `Execution.admit` 消耗唯一 launch。新消费者不需要第二个 executor、root、reader 或 reaper。

**建议。** 保持四个旧活动及其已审封套，增加两个有明确版本的新活动：执行请求或观察、首轮运行观察。观察活动兼任首次冷 BOOT 的调度事实 producer。新结果同时保留完整原件 ref、父侧 inline 事实与 H 产生的小型 typed 投影，后继标准 sandbox Workflow 只消费 history 即可决定首轮调度和停止。本片不实现 Workflow、collect／accept、rounds 或后继。

**未决与门槛。** 下述两个新活动名称、v2 结果字段和保守冷 BOOT 时限是供 fresh 设计审查的具体建议，不是已实现 API。原授权已覆盖 schema2 自动执行，无需新增确认旁路。若未来需要跨 boot 恢复、源漂移后继续执行、计算期结束后继续正常轮询、自动重试不明请求或提前接受测量，均超出本片和原已批准合同，须另立产品决定；这里均不引入。服务终核与本设计 fresh 两轴审查仍是实施前置项。

## 已核真实调用链

源码链接相对于主仓库；以下事实针对上述服务 commit，主树同路径可能尚无服务新增部分。

|owner／入口|实际调用与所拥有的约束|本片使用|
|---|---|---|
|[worker](../../src/ergora/reference_training_worker.py) `create_cycle_activities` → `_CycleOperation` → S/H → `_cycle_operation`|SDK info 来源；原六字段；完整操作身份；32 KiB 请求／frame；父 loop 异步监管；原 `processes.run` 回收|沿原工厂注册两个普通活动，沿原 S/H 增加两个 mode|
|同文件 `_cycle_submission`／`_cycle_target`|按冻结 candidates 的 ordinal 找原 `_Submission`，`CycleAdmission.bind` 核 controller／revision／ordinal，owner 绑定原 intent／authorization|使用一次选定的 operation／intent／owner；不从用户传 run 或 experiment_id|
|同文件 `_CycleCandidate`|唯一新 offer、独立预算根、confirm 后交接、既有 intent 只观察；短 H 退出不停止已交接 root|保留，执行消费者不构造它、不补 root|
|[submission](../../src/ergora/reference_training_submission.py) `load/status/reconcile`|完整 intent、attempt、receipt；`submitted` 才有固定 run；unknown 不重发；reconcile 沿原 SDK history 并写回原 receipt|普通观察只用 `status`；缺 receipt 交给旧 reconcile 活动，不复制其恢复写入|
|[execution](../../src/ergora/reference_training_execution.py) `check/current/request`|registration、原 owner 活性、完整 context／来源、父 history、固定子 run input／memo、QUEUED＋job；锁前／锁内／publish 后最后检查；完整 confirmation|H 构造原 request 参数并直接调用 `Execution.request()`，不再调用公共 execute 产生第二层 helper|
|[budget](../../src/ergora/reference_training_budget.py) `own/drive/helper` → `Execution.admit`|原 root 等待 request；父共享许可→execution.lock→唯一 launch；完整/空/部分 launch 都占机会；在内存收到 grant 才 execute|无新增入口，无 restart／ensure_owner|
|[protocol](../../src/ergora/training_execution_protocol.py) `ExecutionRecords.load/request_record/observe`|完整原 request／launch／attempt／ack／stopped、native raw SHA 与语义身份；durable 同链同步／重读|唯一执行链 reader；不写另一个 JSON 容错扫描器|
|同文件 `native_main`|原 executor 锁内全来源／phase／owner／clock／父 stop gate；attempt-before-ack；唯一原 supervisor/reaper|保持；SDK 来源留应用层，native 不导入 State／SDK|
|[training.status](../../src/ergora/training.py) → [runtime.lookup/observe](../../src/ergora/reference_training_runtime.py)|公开 status 先对当前 project 做 inspect/preflight；runtime 负责固定 run 完整 input、binding、实际 phase／outcome|H 直接复用原 runtime owner 与冻结 spec/run，避免对旧 run 恢复使用当前 preflight；不改公开 status|
|[LocalTrainingAdapter.poll_job](../../src/ergora/data/reference/platform/local/agent_platform/training.py)|`exact_job` 与原 result binding／job 匹配；返回 QUEUED/RUNNING/终态；不执行或 collect|H 对已核原 native request 构造原 `Job` 并调用 `poll_job`，不新增 native result reader，不调用 collect_and_gate|

`ExecutionRecords.observe` 的 `pending` 不能分辨 request／launch／ack，但其完整 `records` 能提供这一分辨。`execution_success` 仍为 null；executor_stop_confirmed 为 true 只证明原子树停止，不证明 job 成功。`Execution.current` 拒绝原 started/result/fence，因而不能对已有执行调用 request 然后把其拒绝当普通恢复；必须先在 H 判断既有原记录，转入观察。

## 新活动、mode 与兼容策略

新增 SDK 名称与 action 精确固定如下（建议）：

|SDK 名称|action|SDK 请求的全部 key|S/H mode|
|---|---|---|---|
|`ergora.training_cycle.request-execution-or-observe.v2`|`request-execution-or-observe`|`workflow_input`, `ordinal`|`request-execution-candidate`|
|`ergora.training_cycle.observe-candidate.v2`|`observe-candidate`|`workflow_input`, `ordinal`|`observe-candidate`|

`workflow_input` 仍严格只有 `protocol, control_home, project, cycle_id, input_sha256, authorization_sha256`；protocol 仍 `ergora-training-cycle-v1`。ordinal 是原零基下标。首版两新活动仅接受 ordinal=0；旧 start 对 ordinal≥1 的 `successor_not_enabled` 保持。不得添加 confirm、actor、project_revision、run_id、native SHA、候选数组、snapshot、deadline 或用户自述 source。

保留四个旧 SDK 名称、request key、`schema_version=1 / ergora-training-cycle-activity-v1` 封套与 queue；两个新活动使用 `schema_version=2 / ergora-training-cycle-activity-v2` 结果。新名称注册在同一 normal queue、共享同一个普通槽，不新增 queue 或服务。旧 stop 仍走专用槽。不得用替换旧 action 的返回结构来隐式升级已审 r2 历史。

新 Workflow 后继的最小消费序列为：`observe-candidate.v2` 冷事实 → 必要时旧 `start.v1` 一次 → `observe-candidate.v2`／必要时旧 `reconcile.v1` → **预算内等待同run双QUEUED** → `request-execution-or-observe.v2` 一次 → `observe-candidate.v2` 有界轮询。submitted只允许继续观察；唯一request调度前必须同时取得runtime `queried / terminal=false / phase=QUEUED`、native `QUEUED`且同一完整binding／job、execution `not_requested`、project匹配、父stop未见及正compute／control剩余。SUBMITTING／native request尚未发布在原计数和预算内等待；缺原件为unconfirmed，不合成QUEUED。明确终态、身份冲突或预算耗尽走停止／对账。是否已调度request归Temporal history；一经调度，即便返回not_attempted或request文件不存在，也只观察，不再请求。该保守选择可能需要人工对账，不重授机会；无需inspect.v2／start.v2或将snapshot放入history。

S/H 操作仍用 `ergora-training-cycle-operation-v1`，是受同安装 source pin 控制的内部mode扩展，不改变旧mode key：两个新mode同时加入原`CYCLE_CANDIDATE_MODES`与`CYCLE_WORK_MODES`，不归冷`CYCLE_OBSERVATION_MODES`；bootstrap由原validator核对，实际remaining消费compute∩同一window，不落入total分支。各自 `start_context` **仅** `controller`；controller 使用原 `protocol, workflow_id, run_id, intent_sha256, ordinal`。payload 仍 `identity, snapshot, bootstrap, reason, start_context, activity_context`，reason=null。identity 仍原十个 key；两个 mode 的 ordinal=0。认证 mode→action 表明确限制：request mode 只来自新 request action，observe mode 可来自两个新 action；冷 `inspect-controller-activity` 可来自两个新 action。新请求 activity 的 attempt>1 强制只观察，绝不产生 request。

新 mode 的 H 结果写原完整 stdout/ref；mode 与投影 schema 在同一 source pin 下演进。旧授权／ready 的源码摘要不因升级自动换新：新源码不能替旧 owner 重授能力；若旧 source pin 不匹配，新动作拒绝，旧安装／离线原件对账保留。兼容四个旧 activity wire 合同不等于放松 GATE_SOURCES。无需修改原 native 283 文件或增加 schema1→schema2 转换。

## v2 最小结果合同

顶层精确 key 为：

```
schema_version, protocol, action, status, workflow_input, controller,
observation, inspection, operations, runtime_status, facts
```

facts 之前的十个字段沿旧封套的含义；schema_version/protocol 如上。`status=observed|unknown` 只表传输／观察是否完整，不授权任何下一动作。`inspection` 与 `operations` 保留原 `_activity_operation_result` 格式、完整 ref（含原路径／SHA）或 inline；父侧 outcome 比 H 原件多出的 timeout、cleanup_problem 等仍单独 inline，不能把 ref 声称为完整父结果。不得为省容量删除 stop 分支、截断 error/detail 或只存一部分 identity。

`facts` 为 null（未取得完整认证的投影）或如下精确结构；其中 null 永远是未证实，不是 false。字段只由 H 的完整原观察产生，父 loop 不读任何 ref 或业务文件。

|对象|精确 key／类型与含义|确定性消费者|
|---|---|---|
|`facts`|`source_operation_id: str`, `budget`, `candidate`, `submission`, `execution`, `runtime`, `native`, `request_outcome`|新 Workflow 以 source_operation_id 匹配inspection或operations中同一ref；投影来自 H，父失败不被抹平|
|`budget`|`state: valid|exhausted|unknown`, `work_remaining_seconds: finite number|null`, `total_remaining_seconds: finite number|null`, `control_timeout_seconds: int`, `boot_id: str`, `boottime_ns: int`, `observed_at: UTC str`|计算 compute∩control SDK 截止；total 为 stop 调度上限；原 BOOT 只作证据，Workflow 不读本地 clock|
|`candidate`|`ordinal: 0`, `experiment_id: str`, `manifest_sha256: str`, `project_revision: int`, `current_project_matches: bool|null`, `parent_stop_visible: bool|null`|首轮选定事实与动作阻断；不传候选列表、不生成后继许可|
|`submission`|`state: not_recorded|prepared|unknown|submitted|rejected`, `intent_sha256: str|null`, `workflow_id: str`, `run_id: str|null`, `attempt_saved: bool`, `result_saved: bool`|submitted＋原 receipt 是执行请求前提；prepared/unknown 只原 reconcile，不能新 start|
|`execution`|`state: not_requested|requested|launch_consumed|attempted|acknowledged|stop_observed|stopped|unknown`, `request_sha256: str|null`, `record_sha256: object`, `reap_record_observed: bool|null`, `durable_stop_confirmed: bool|null`, `executor_stop_confirmed: bool|null`|判断原请求存在／机会已消耗／原子树停止；record_sha256 沿原五类完整摘要映射|
|`runtime`|`state: not_queried|not_found|queried|unconfirmed`, `workflow_id: str|null`, `run_id: str|null`, `temporal_status: str|null`, `terminal: bool|null`, `phase: str|null`, `binding: object|null`, `job_id: str|null`|精确子 run、完整原 Binding 与实际 phase；不得把 COMPLETED 或终态本身等同 accepted|
|`native`|`state: not_queried|unconfirmed|QUEUED|RUNNING|SUCCEEDED|FAILED|CANCELLED`, `job_id: str|null`|区分原 result 已发布与 Workflow/reap 尚滞后；detail 原文保留完整 H 结果，不推导质量分类|
|`request_outcome`|`not_attempted|requested|existing_only|unconfirmed`|表达这次调用是否得到了原 request 完成观察，绝不是原执行成功|

预算数值在 H 最后生成投影时重算，包含全部 RPC／同步／读取已耗时间，原观察不回填早先 inspection 数值。`observation` 同步取该末次 budget 的 total/clock；没有末次事实时保留实际冷观察并令 facts=null。有限负 remaining 保留真实耗尽含义，Workflow 只在正值调度。时钟异常时 remaining=null、state=unknown；不伪造零值来声称预算已耗尽。controller 使用已认证原三字段，不能因为投影里有 run 就绕父 receipt 核对。

各子观察可能局部失败：完整已核本地 submission/execution 保留，runtime 或 native 单独 unconfirmed，整体 status=unknown；原异常全文归 H 结果。损坏／部分 execution 原件不能映射为 not_requested，置 execution.state=unknown 并保留原文件，不尝试修复／补 slot。旧错误若在 H 投影形成前使进程失败，facts=null，由原完整失败 ref 和父 inline 表达即可，不为每类错误新增总异常层。

每个 input/result 都通过原 SDK converter 的 `Payloads(...).ByteSize()` 检查 ≤32 KiB，包含 encoding metadata；原 S/H 请求／stdout/frame 也各守原上限。对象较长、完整 Binding、ref 或错误超限则原容量错误整体拒绝，完整 H 原件／父日志保留，不截断。新增投影不修改原 10 MB cycle 或索引上限，不借服务器 2 MiB 默认扩本域合同。

## SDK 来源认证、权限与动作时序

1. SDK 父 loop 先编码容量检查，严格校验两 key、六字段、ordinal、真实 `activity.info()`。拒绝 local activity；取得全部 `workflow_id, workflow_run_id, workflow_type, workflow_namespace, namespace, activity_id, activity_type, task_queue, attempt`，核 type=TrainingCycleWorkflow、normal queue、client.namespace 与两个 namespace 一致、注册 action 对应。source 由 SDK 产生，绝不接受业务 input 的复制品。
2. 创建原 cold `_CycleOperation(inspect-controller-activity)`。S/H 核请求全身份、父进程、固定 BOOT；H `_load` 校验 cycle raw SHA、authorization canonical SHA、schema2 出生同意与 ready，`_activity_binding` 核原 controller intent／attempt、完整六字段和固定 run。首次丢父 start reply 允许沿实际 SDK run 认证并补原父 receipt；不能跟随 reset/continue-as-new。
3. `_dispatch_controller` 复用 `lookup_controller_submission`，核 namespace、description 原 first run／type、started event 原 type／queue／完整 input／memo、first/original run／attempt／initiator。SDK info 本身不是充分认证。request 动作最终还须经 `BudgetedStart.check_controller_history` 证父仍 RUNNING；观察可保存原已关闭父状态但不转授动作权。
4. H 用冻结 ordinal 解析 `_cycle_submission/_cycle_target`；对完整原 owner、intent、receipt 与 native request 用既有 `ExecutionRecords`／`BudgetedStart.context` 重建。schema1、foreign ordinal／controller、缺 owner capability 或部分链均不进入 request。既有 request 或 launch/attempt/ack/stopped 直接只读；有 started/result/fence 同样不试 request，保留阻断观察。
5. 只有首个 request activity attempt、无既有执行链、原 submission=submitted、runtime实际QUEUED且job匹配、native实际QUEUED且完整原request存在、原 owner 活且预算／project／source／父 stop 通过，H 才调用 `Execution.request`。使用 `chain.request_record(authorization['controller']['actor_id'])` 得到完整原确认，写入同一 `_Submission.payload` 的 `expected_revision, intent_sha256, run_id, request_sha256, confirm=True, timeout`；这六项分别来自原 request 的 project_revision/start_intent_sha256/run_id/native_request_sha256/原出生同意/剩余窗口。actor 不来自 input；confirm 是复用原已批准 schema2 同意，不是新增 bypass。request 返回后重新观察原链，不把方法返回字符串当执行成功。
6. H把本次**完整已认证operation payload**通过既有`_Submission.payload.cycle_operation`交给原`Execution`，不只复制deadline；原protocol核本H的request mode、同controller／ordinal／候选intent、原source与父进程，activity action为v2 request且attempt=1。observe mode不取得发布能力。`Execution.check` 继续核原registration、owner/context/source，父固定history，子原spec/history/memo、QUEUED／job；异步验证在原锁外，外层同一次timeout包住整个coroutine。**原`Execution.current`在完成可能阻塞的同步身份读取后，于锁内实际publish前及发布同步后的最后gate直接重算该同一BOOT/window remaining**；compute／control／cold任一过期即拒绝，不只依赖异步timeout或S轮询。无cycle_operation的旧schema1人工路径保持；schema2新H不能省略该来源。父共享许可→execution.lock→不可覆盖request发布→最终current保留，预读不取代最后验证。不可中断OS调用仍可能在窗口后返回；同步后过期则unknown，原件不删除／不重发，不声称及时完成，原compute／stop／native最终gate仍独立生效。
7. 原预算根继续 `Execution.admit`，原 `check/current`、父许可、原锁和最后同步 gate 不变；唯一 launch 仍归原 root。native execute 的 source/owner/controller/clock/stop/executor 锁检查与唯一 reaper 不变。取消短 H 不会杀已交接 root；真正父 stop 另经原 stop queue 精确通知。

来源只在当前 H 选定一次 `_select_cycle_project`；native import/env 的初始化复用原路径。同一 H 复用已选 operation/intent/owner，不先调用 public execute/status 再重复发另一条 operation，也不增加“validated context”全局缓存。`BudgetedStart.source/context`、`Execution.check/current` 和 native 最后 gate 的重新读核跨异步／锁／进程边界，保护真实 TOCTOU；这些不是可删的重复 reader。可在本地组装投影时复用同一次已核链，但原 publish 后重载与 durable 同链重读仍必要。

## 冷 BOOT、普通动作、观察与停止截止

具体建议固定首次冷观察 **10 秒**；它不授效果权限。新活动每次进入 SDK 父 loop，先取一次 BOOT `started_ns`、`deadline_ns=started_ns+10s`，沿原 cold S/H传递。冷认证耗时算入该次活动；不得在内部失败、poll 或后续 mode 重建起点。

冷 inspect 取得原预算后，两个新活动的普通 H 共用由同一 started_ns 收窄的 window：

```
deadline = min(cold.deadline_ns,
               cold.started_ns + original_control_timeout_seconds * 1e9,
               original_clock.boottime_ns + (wall_seconds-cleanup_seconds) * 1e9)
```

每次 remaining 仍用原 `budget_clock.remaining`（同时检查 UTC／BOOT 连续性）与此固定 window 的较小值。window 已过即不 spawn 后续 H、不 request、不 RPC。prepare/dispatch 的原一次窗口不改；新 mode 使用本次请求／观察窗口，不误用旧 start 的已消耗窗口，也不把它扩成新 launch 许可。S pipe/wait、H 全 coroutine、最终同步和 post-stopped 结果读取都消费这一次窗口。`timeout` 不向上取整到公共 API 的 1 秒；直接复用原内部接口传实际正剩余浮点数。

对两个新 action，原 cold H 分支在保持旧四 action 返回行为不变的前提下，另生成同结构的基础 facts（source_operation_id 为 cold 操作；仅原预算、candidate和已经完整读到的本地submission/execution，runtime/native不查询，request_outcome=not_attempted）。它不调用普通mode、不授动作权；后续H有完整结果时才由该结果取代基础投影。首次 `observe-candidate` 因而可在 cold 10 秒内返回已耗尽预算／本地绑定事实；没有正 compute 时不进入新 ordinary mode 的 runtime/native 观察。计算期结束后的 durable stop／owner通知沿原 stop 用例消费 total；不能用普通观察循环占用 cleanup 或不断给其新的冷恢复额度。用户之后的显式离线记录对账仍是原接口，不能延长原控制效果窗口。

后继 Workflow 调度选择如下，供 c1c 实施：

- 首次 observe 的 `schedule_to_close=start_to_close=10s`，maximum_attempts=1。这是不知道授权预算时唯一的冷只读探测；失败／facts=null 不调度业务效果，也不以新的冷探测自动刷预算。
- Workflow 在每次活动调度前记 `workflow.now()` 的 deterministic 时间 `scheduled_at`。收到 facts 后，用 `workflow.now()-scheduled_at` 从 H 返回的 work／total 再保守扣除，包含队列、执行和传输时间；timer 继续扣时间。它刻意可能多扣，不能把 H BOOT 与服务器 wall-clock 直接相减。
- 普通下一活动的 `B=min(adjusted_work, control_timeout_seconds, 10s)`，`schedule_to_close=start_to_close=B`；B≤0 不调度。request/start maximum_attempts=1；本片推荐 observe/reconcile 也为1，通过新历史活动有限轮询，不让 SDK retry 重置窗口。每次 ordinary 调度（含失败）消耗原每候选256观察计数；不增加仅成功才计数的路径。
- 本地 H 仍独立核原 BOOT/window、父许可及最后 gate；SDK schedule_to_close 是额外服务器期限，绝不当原 compute 授权。排队或晚执行消耗 SDK 截止；H 不因 SDK future 取消完成就声称本地回收。
- stop 从最近 facts 的 adjusted_total 导出 SDK schedule_to_close/start_to_close；非正或未知不新授 stop 效果窗口，返回停止未确认并留原本地对账入口／独立 root 预算停止。已有 stop 活动仍在 H 按原 total 复核；c1c 可见 cancellation 必须走既有专用 stop queue，并等待原监管清理，不以 terminate 或 SDK cancelled 替代 executor_stop_confirmed。

这里选择保守 10 秒上限可能在可用 control>10 秒时较早终止一次请求，但不会扩大原授权；没有截去原 control<10 秒的保护。若验收表明真实必要的合法查询不能在该上限内完成，调整冷常量／调度合同须回到本设计审查，不根据运行卡住临时续期。

## 运行观察的组合与恢复表

新 `observe-candidate` 在 H 选中冻结原 operation 后：读原 submission；无 receipt 不查询 latest run，不补 receipt；有 receipt 则用原 `lookup(client, original_spec, run_id=receipt.run_id)`、核原 memo，再 `observe`；以完整 Binding／job核对返回。然后调用原 `LocalTrainingAdapter.poll_job(Job(original_binding, original_job_id))` 和 `ExecutionRecords.observe(durable=True)`，最后生成预算／小型 facts。完整 runtime status/outcome、native Observation、execution observation 都进入同一个 H 原件，投影只选 Workflow 必要字段。读取不是原子快照，三个观察不相互推导，先后交错由下一有界观察核实。

|真实可达窗口|本片行为与可核结论|
|---|---|
|request 发布前丢 reply／H 被杀|原 request 可能不存在；Workflow 此次 request 已不明，只 observe，**absence 不授再次 request**。不补 budget root／launch；原预算尽时原 root清理。无需为恢复新增可重播 offer|
|request 可见／fsync 后丢 completion|原 request 原件存在即 existing_only，完整身份验证成功才 state=requested；request 返回丢失不妨碍原 root 一次 admit。发布部分／损坏则 unknown，不修复|
|两个请求并发／重复 SDK attempt|同 normal 槽限制本服务并发，原 execution.lock/publish 仍为跨进程最终保护。重试 attempt>1仅 observe；同时经过无 request 预读也不能覆盖异身份或授第二 launch|
|request pending、完整或部分 launch、无 attempt/ack|pending 不是“可重试”。完整 launch=launch_consumed；部分记录=unknown；已有 slot 一律保留，不重新 invoke admission 或 spawn execute|
|RPC late、activity cancel、H post-stopped 输出迟到|全 coroutine/pipe/result受原固定窗口；timeout后本次未知，晚回执保存原件但不放大权限。父仍保存完整 ref+inline；原 root独立继续／按原停止路径收尾|
|controller history/memo/input/run/namespace mismatch；子 run history/memo/binding/job mismatch|来源失败、facts缺失或对应子项 unconfirmed；不 request、不跟新 run、不改 receipt。身份冲突不自动循环重试|
|submitted receipt先于子Workflow创建job／进入QUEUED|唯一request尚未调度时继续观察双QUEUED；native request缺失为unconfirmed，不合成QUEUED。调度后任何结果均不再请求|
|原 phase QUEUED→RUNNING→AWAITING_RELEASE/其他终态|分别返回实际 temporal_status/terminal/phase；QUEUED只是 request必要条件之一；RUNNING不证明 ack；AWAITING_RELEASE不在本片接受测量|
|native result先于 reap|native终态可以保留；executor_stop_confirmed仍 null，继续原有界观察，不能接受或下轮|
|reap先于 Workflow phase更新|stopped 可为true，runtime仍旧phase或unconfirmed；不由reap推导成功／COMPLETED|
|native SUCCEEDED但gate失败／archive缺失|native状态原样保留；无accept／quality分类；c1d沿原 evidence/gate 权威另判|
|父 stop 与 request/launch交错|可见stop阻新共享准入；已经持许可的动作由原锁内及post-sync/native gate复核，已产生记录保留。drained与subtree stopped分别观察|
|compute尽、total仍有余量|不再request或普通轮询；stop消费原total，原root按原clock清理。SDK timeout不刷新预算|
|total尽／boot或clock不连续|不新spawn效果分支，不声称已停；保存原件与unknown。原 reaper 的资源回收义务不因为活动deadline结束而丢弃|
|project revision或注册/源码漂移|request沿原 owner gate拒绝。能够用冻结原 records核到的事实保留，live runtime/native因原安装/配置不可用则unconfirmed；不改source pin、换安装或用当前spec解释旧run|
|已交接owner正常完成或消失|observe不要求owner活才读取历史；缺 capability或owner死从不ensure_owner；普通观察不通知已交接root，原stop才精确通知|

不从 `status=observed`、`request_outcome=requested`、native SUCCEEDED、Temporal COMPLETED 或 stopped 的任一组合产生 `measurement_accepted`。本片 facts 不包含 accepted／next_allowed；c1d需要原 accepted archive、完整证据、实际phase、durable stopped及原rounds追加闭合后另行设计继续结果。

## 改动位置、函数消费者与克制

计划只修改三个既有应用 owner（具体以实施调查复核）：

|拟新增／调整函数|真实生产消费者|已有替代与理由|
|---|---|---|
|protocol 原 `validate_cycle_activity_request/context/operation` 与 mode/name集合扩展|worker SDK工厂、S/H解析／监管|不另建消息validator／新模块；旧四动作保持原路径|
|worker 原 `create_cycle_activities.invoke` 的两个 action 分支、`_serve_cycle` 注册|原服务入口|共享真实source／容量／cancel治理；不复制服务或建工作流通用调度器|
|worker `_cycle_operation`→局部 `_execution_candidate_operation(payload, plan, admission, active)`（名称建议）|只有 `_cycle_operation` 一处|一个内聚 H 算法，隐藏 execution request与只读观察组装；不搬为单独“manager”文件|
|同一 H 函数内部生成 facts／deadline|只有该 H 算法；inline schema读取者为后继 Workflow|先本地代码；确需共享时才提取私有 helper，不为 DTO 新建框架／缓存／ledger|
|`Execution.request/check/current` 原入口|新增H；旧execution_main／原root admit|人工确认及原admit语义保持；新H沿原payload传完整已核operation，原锁内current在同步读取后、发布前后核同一window。不建自动执行旁路或重授launch|

新 H 不创建 root、不调用 native process、不重写 `ExecutionRecords`、不调用 training.evidence／training_rounds、不新增失败质量分类。标准 sandbox 的 decorated类／pass-through导入和纯确定性循环属于 c1c；当前协议能由其消费，不借测试Workflow注册宣称生产Workflow已存在。

## 客观验收节点与证据范围

本页为设计，只做源码／文档静态核对；未跑服务、安装或昂贵测试。实施后沿以下现有接缝取得观察证据，不以“实现里调用了某函数”的断言认证行为：

|节点|既有接缝／fixture|可核结果与反例|
|---|---|---|
|E0 协议与来源|`tests/test_training_submission.py` 的 `cycle_sdk_activity`、first_activity／retry／dispatch-recheck tests；`tests/fixtures/training_cycle_operations.py`|真实SDK info、首父receipt丢reply恢复；完整history/input/memo/queue/namespace/run变异被拒；旧四请求／封套保持；v2 input不接受业务自述权限|
|E1 一次request与唯一launch|同文件 `controller_admission`／`cycle_candidate`／`service`，request-writer等待、consumed-launch、startup-failure现有tests；native entry接缝|新SDK action→真实S/H→原Execution.request→原root admit；只一次launch。published前后丢reply、partial launch、并发、重复attempt不补slot。receipt后延迟job创建／首次poll时先观察双QUEUED；history已调度request则文件absence也不再请求（正式分支在c1c）|
|E2 真实状态交错|原 `tests/fixtures/training_submission_client.py`／`training_runtime_client.py`，`tests/test_training_runtime.py`，historical_execution fixture|服务返回固定run QUEUED/RUNNING/terminal；真实文件 publication与 reaper／phase延迟控制，分别观察native／runtime／durable；不能把模拟服务等同真实Temporal|
|E3 一次窗口与取消|现有operation fault／post-stopped、source drift、cold inspection、pending Popen／real descendants tests|异步核对后阻塞锁内current同步读取，operation过期且compute仍正时释放并允许H继续一次：不得新publish request／launch；两新mode在cold／control／compute各自最短时核同一window。normal父loop响应、stop槽可用；取消保留S/H及后代回收；预算从fixture配置取值|
|E4 权限与旧接口|schema1手动execute、schema2拒手动binding、原gate/stop竞态tests|人工完整确认不变；自动actor原生来源；project/source漂移、stop可见、原owner死均不进入新request；离线旧记录仍可读|
|E5 编码与完整性|`test_cycle_sdk_capacity_counts_metadata_and_rejects_without_truncation`、真实H frame容量／父inline回归|SDK metadata把边界推过32KiB时整体拒绝；ref包含完整原件，父late/cleanup错误没有被ref遗漏；0~32候选配置仍按支持范围，不靠删除字段过容量|
|E6 新非editable包|原core／SDK双环境安装流程及283参考／source pin检查|确认新source=wheel=site，core无SDK的历史读仍可用；新SDK normal注册5个普通活动＋原stop，共6个，槽仍1/1；旧安装不冒充新消费者|
|E7 真实Temporal与真实预算根|复用服务片 live harness，明确使用新的包／实际临时测试Workflow|原producer→两新activity→首候选原request／root／native链；独立budget/cycle PID、实际queue、阻塞／取消和原件收尾；不认证正式sandbox Workflow或训练质量|
|E8 c1c接续前的消费证明|后继标准SDK sandbox真实history／replay接缝|Workflow仅用六字段和v2 facts可完成预算计算／首轮分支，无open/path/本地clock；所有ref只留审计，unknown／capacity／256计数耗尽不重发。此项是后继交付，不计本片已完成|

对安装和live分别保存准确源码、包、冻结输入、命令与原输出、未验范围；新候选不继承 eedba08 服务通过结论。最终交主控 fresh-context 两轴设计review，按实证finding修订后再进入产品实施。本子任务仅创建本草案，不编辑PLAN／他人交付，不提交或推送。
