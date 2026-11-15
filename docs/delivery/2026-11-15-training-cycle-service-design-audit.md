# c1b2a 独立 cycle 服务：接口与生命周期设计审计

日期：2026-11-15。审计者：独立 fresh-context agent `cycle_service_design_interfaces`。这是下一片的设计调查／审查，**不是 c1b1 源码验收，也不是 cycle 服务实施或运行通过**。只写本报告与 ignored 的只读探针证据；没有改产品／测试／主计划／服务草案，没有安装、启动服务／模型、提交或推送。

**设计结论：方向可复用，但当前草案尚不能直接进入产品实施。** 需要先固定下文 A–D 的接口，尤其是补 receipt 前比较真实 SDK run、首版新 start 只允许 ordinal 0，以及没有已验证原件的 stop unknown 必须内联。需求轴为“待这些具体缺口闭合”；维护性轴为“现 owner 足够，按下述局部扩展可保持，无新增通用总线／process host／账本的理由”。后续实施仍须新的产品独立审查。

## 范围与实际证据

阅读了根及 `src/ergora/AGENTS.md`、[当前计划](../PLAN.md)、[服务草案](../plans/2026-11-15-training-cycle-service-boundary.md)、[已批准控制器合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、[c1 总计划](../plans/2026-11-15-training-cycle-workflow.md)、[c1b1 交付](2026-11-15-training-cycle-owner-lifecycle.md)、[组件协议](../architecture/component-change-protocols.md)，并核对下表 owner、对应 submission/runtime/services 测试与真实 S/H fixtures。使用 maintainable-project-delivery 的独立审查要求、ergora-codebase-quality 的 module-design／test-seams、codebase-design 的 Interface／Locality 原则；不递归委派 reviewer。

调查时分支 `refactor/architecture-foundations`，HEAD `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`。工作区已有他人的未提交产品／测试／文档，不能把 HEAD 当当前产品字节。前置安装包 SHA256 `565aefd026e01f83470af5e49a74d1743c3919779a4b4a217fc2dc56755eb29b`、r2 76 pass 与后续 r3 七项通过为委派背景／前置记录，本审计未重跑，也不替代其待完成的最终独立门禁。

|实际检查的当前文件|SHA256|
|---|---|
|`src/ergora/reference_training_worker.py`|`9e30d9a985a48181940a76309a4869611fcb97e045087dbcba7af0e4bf51319c`|
|`src/ergora/training_execution_protocol.py`|`9d6d1c24e0e8818aa964a1e3c750c2552c6bbcd79f5081daf45a110123936439`|
|`src/ergora/reference_training_submission.py`|`9c775643b07a937690230cdb86bd19e0d6fc89fcdb092fbb50d7bc3856a7575c`|
|`src/ergora/reference_training_runtime.py`|`1183a95c53a9550789983e245676a46637b5de748ddf32eb0ec5df9def46458a`|
|`src/ergora/services.py`|`052422632c6eb5e810ae0a1c2fac6d79739bf7bd85c8e5372428c0c7f5323c70`|
|`src/ergora/reference.py`|`87bd5d2c1c2eb92cc85f1bc0cb8387ae40092b8f4b7ea7bb07518efce2080aa4`|
|`src/ergora/training_cycles.py`|`37a9a2010377eeb99c35d87e444852d32a3ca2b14640d16e34ea4dc3e7f56fa6`|
|服务草案|`38c5590d7750fb45b02225944b48fab9a131d4bad1c8bf8512cca95d8911e3a6`|

SDK 只读 introspection 核到 Temporal Python 1.34.0 的真实 `activity.Info`、`Worker`、`Client.namespace` 和关闭源码；另用前置 r2 SDK 安装的 `DataConverter` 编码合成封套。证据位于本 agent 的 ignored 持久目录 `training-cycle-service-design-audit`，未读取凭据值。introspection JSON 48,571B／SHA256 `3eccee71978c05b6c1897d8319abc3e5ff2ad2e90799575d76c2b37a029c1b6b`；编码探针 JSON SHA256 `a7f759f6260ccfde73020ae827da8cf90f5c1f72a8a7e34a26ab0c003a2e3d4f`。初次 introspection 误以为内部 `_ActivityWorker` 有 `shutdown`，实际抛 AttributeError；随后按实际 `notify_shutdown`／`wait_all_completed` 重核。没有据内部不存在的方法设计能力。

## A. SDK 来源到原记录：固定小接口，先认证再动作

### 建议的活动名称和输入

在现 `reference_training_worker` 内增加可选装载的真实活动 adapter，首版仅注册四个名称：

|活动名称|业务参数的完整 key 集合|真实消费者|
|---|---|---|
|`ergora.training_cycle.inspect.v1`|`workflow_input`|只读活动，返回认证／预算事实与原件引用|
|`ergora.training_cycle.start.v1`|`workflow_input, ordinal`|`start_cycle_candidate`／`_CycleCandidate` 原 start 生命周期|
|`ergora.training_cycle.reconcile.v1`|`workflow_input, ordinal`|原 `_CycleOperation('reconcile-candidate')`，只有对账|
|`ergora.training_cycle.stop.v1`|`workflow_input, reason`|原 `stop_live_controller` 独立 fanout|

`workflow_input` 必须仍为原六字段，缺项／多项拒绝：`protocol, control_home, project, cycle_id, input_sha256, authorization_sha256`。它不接收 `controller`、candidate 列表、command、manifest、baseline、snapshot 或声明的 run。ordinal 用原 int 位置，reason 沿完整非空文本；完整 SDK input 超过 32KiB 时拒绝，不能裁剪 reason。这里只固定活动协议；不是新增公共 CLI／HTTP，也不是总 Workflow 已存在。

活动 adapter 从**本次真实 `activity.info()`**构造 `activity_source`，建议完整字段如下：

```
workflow_id, workflow_run_id, workflow_type, workflow_namespace,
namespace, activity_id, activity_type, task_queue, attempt
```

不传 task token。拒绝缺 Workflow 信息的 standalone activity、local activity、错误 type／queue；`workflow_type` 必须是 `TrainingCycleWorkflow`，`activity_type` 必须等于当前注册名。`namespace` 与 `workflow_namespace` 均须匹配服务实际连接的 namespace，首版不支持跨 namespace activity。attempt 和 activity_id 用于审计／辨别重投，不是新执行权或去重账本。start 的 attempt>1 只能观察／对账，不能产生 new_offer；同 attempt 的重复仍由原 intent 单次竞争保护。

SDK 来源只由可信 adapter 加入内部 operation，不能从业务参数反序列化出来。这是同一可信 Linux／WSL2 用户与被 pin 的源码之间的接口，不是跨 UID 认证或安全隔离。

### 建议的 H 封套和 mode

沿 `training_execution_protocol.validate_cycle_operation` 增加一个明确 mode：`inspect-controller-activity`。它是冷、有界、无候选副作用的 observation，`snapshot=None`；复用现 `inspect` 的单一 BOOT 截止。内部封套增加可选、严格的：

```
activity_context = {workflow_input, activity_source, service_namespace}
```

`service_namespace` 取自创建两个 Worker 所用的实际 SDK client，是 adapter 运行配置；不由业务输入提供。该上下文随本次 `prepare-candidate`、`confirm-candidate`、`dispatch-candidate`、`reconcile-candidate` 或停止分支传递；`cycle_start_source` 必须把它与原 prepare request 一并比较，后阶段不能替换。旧 c1b1 直接调用的无 context 封套保持原合同；新 SDK 活动必须带 context。不要把 SDK import 放入 stdlib protocol。

`_cycle_operation` 的新 mode 在 H 内按顺序：

1. `_load` 完整原 cycle／authorization／ready，重新核 raw input SHA、authorization canonical SHA、六字段完整一致，以及 `CycleAdmission.controller_intent()` 的完整 intent。
2. 核 SDK workflow ID／type／queue／namespace、原 attempt／receipt；有 receipt 时先比较其 run 与 SDK run，冲突立即返回拒绝／unknown，不修改任何记录。
3. 复用 `_dispatch_controller` 的原 reconcile 分支与 `lookup_controller_submission`；本 mode 永远不调用 `_claim_controller`／`start_workflow`。必要时在该 owner 内提取原 nested reconcile，保留其算法，而不是在 activity 类重写 lookup。
4. 返回认证事实、完整原 snapshot（仅供同一次活动的内存消费者）、原件引用和按原 clock 计算的 remaining。发给 Workflow 的结果使用下文 B 的小结果协议，不把 snapshot／launch 带回 history。

普通 inspect 活动即使输入正确，也不是 start 许可；H 返回认证之前只能进行原只读／同 attempt 补回执。所有实际 start 最后仍由原 `BudgetedStart`／submission／parent permit／固定 run history／原 compute∩control gate 决定。

### 首次活动早于 receipt：必须在写回之前核实际 run

现 `_dispatch_controller` 的 reconcile 用 `run_id=current['run_id']`；没有 receipt 时为 `None`。这个路径能认证原 first run，却没有把“正在调用活动的 SDK run”作为写回前的比较对象。不能先补一个 receipt 再发现活动来自别的 run。

新 mode 的明确规则：

- intent、唯一 attempt 必须已存在且完整；没有 attempt 的真实 activity 也不能为 controller 领取 slot。
- receipt 不存在时，向原 `lookup_controller_submission` 传 **`run_id=activity_source.workflow_run_id`**；核 description ID／run、first_run、started original／first execution、完整六字段 input、started 与 describe memo、类型／queue、非 retry／reset／continue-as-new。
- 比较得到的 run 等于实际 SDK run 后，才能调用原 `_record_controller(...run_id=that_exact_run)`。该函数继续重核 ready／authorization，沿原事务和无覆盖发布；并发客户端 receipt 只允许完全同一值。
- `NOT_FOUND`、远端不可用、损坏／缺失 attempt、不同 receipt、run／input／memo／type／queue 不符全部不产生新 attempt、不再次 start；保持 unknown／明确阻断并保留原件。不能凭“Temporal 已领取活动”创建 budget root。
- 只读认证可观察已关闭原 run；新 start 在 offer 前另核原 `lookup_controller` 的 RUNNING 语义，实际子实验 SDK start 和 native create 仍保留现有最后 gate。不能为历史查询放宽该执行 gate。

现 intent／attempt／receipt **没有 namespace 字段**，不能声称已从它们认证原始 namespace。正常活动在 H 连接所选 native 环境后核 `client.namespace == service_namespace == 两个 SDK namespace`，然后通过该 client 查询固定 run；这保持原记录版本。所选环境当前把 local namespace 固定为 `default`，但实现不应散布该字面量。跨配置／远端 namespace 迁移不属于本片。

停止活动不应因每个 notify 都查询 Temporal 才能运行：已有完整 receipt 时，各 H 使用原本地 receipt 与可信 adapter 的 `service_namespace` 核来源，复用现离线通知路径，不要求 SDK server 或安装仍可用；首次 receipt 缺失时只能沿上述同 attempt 对账，不能把来源自述当回执。现有显式本地 `stop_live_controller` 不新增远端认证前置，仍可用于服务／SDK 不可用时的原停止。**设计终核需明确接纳这个普通认证与已绑定停止的不同状态语义**，否则“强制远端认证”会回归原离线停止。

### 顺序门槛：本片新 start 只允许 ordinal 0

`CycleAdmission.bind` 证明 ordinal 属于原 admissions，并匹配完整选中观察；它不证明前一轮达到 accepted archive、实际 Workflow phase、durable stopped 和 rounds 索引。SDK Info 也没有这个证明。因此服务存在但 c1d 尚未实施时，不能让任意合法 ordinal 获得 new_offer。

本片 `start.v1` 的新动作只支持 ordinal 0；在产生 intent／Popen 前拒绝 ordinal>0，记录为 `successor_not_enabled`。`reconcile.v1` 可读同 run／同 ordinal 已存在的原 intent，但绝不补 prepare／owner／start。c1d 才在实际前驱接受与索引证据闭合后扩展新 start 的顺序 gate；不是放一个 `allow_next` 布尔给活动调用者。人工 schema1 和旧原始接口按原授权范围继续，不能借服务 adapter 偷渡下一候选。

## B. 完整 stop fanout 与 32KiB：引用真实文件，unknown 原样内联

### 现有可用与不可用的证据

现 `cycle_operation_main` 的 S 在启动 H 前保存 `operations/training-cycles/<operation_id>/request.json`；原 `processes.run` 保存 `helper/stdin.txt`、`helper/stdout.txt`、`helper/stderr.txt`。`observe-execution` 还保存真实 `helper/observation.json` 和 raw SHA。S 的 stopped 帧先于读取 H 输出发出。

但是 `_CycleOperation.observation` 中的父侧 unknown、`supervisor_returncode` 和 frame 接收状态目前只在内存；未 spawn 的分支甚至没有 operation 目录。**路径字符串不能证明文件存在，不能给每一分支一律发 result.json／stdout 引用，更不能称其为停止成功。** 不新增 stop aggregate、可变 current-round 或第二停止账本。

### 最小结果协议

活动返回一个严格的 `ergora-training-cycle-activity-v1` envelope，共同身份只保存一次：`schema_version, protocol, action, status, workflow_input, controller, observation, inspection, operations, runtime_status`。`controller` 为原 `workflow_id, run_id, intent_sha256`；`observation` 是 H 实测原 compute／total remaining 与原 clock 观察；检查失败时字段明确为 null／unknown，不填推测值。每种 action 的完整 key 集合在 protocol 固定，不使用任意 dict 截取实现。

stop 的 `operations` 必须完整、有序地覆盖 `stop-writer`、`drain`，然后每个原 ordinal 的 `notify-owner`／`observe-execution`，共 `2+2N`；每个分支至少内联：

```
mode, ordinal, operation_id, operation_stopped, supervisor_returncode,
result_ref OR inline
```

成功得到完整 H 结果时，S 可在**现有 stopped 帧之后**对已读的原 `helper/stdout.txt` raw bytes 计算 SHA256／长度，把 `result_ref={file:"helper/stdout.txt", bytes, sha256}` 加入其结果封套。引用的根由原 control_home 和 operation_id 推导；不接受活动传入的任意路径。H 本身已有 observation 引用继续保存在该 stdout 原文，不重写它。S 增加的元数据仍必须经过原完整 frame 容量检查；无法形成完整结果则保持 unknown，不能宣称引用已验。

adapter 使用该已验证引用替代重复的大 H 内容，同时保留父侧实际 stopped／returncode。原 `request.json` 的 SHA 可由已发送完整 encoded bytes 得到，但只有收到相应 S 帧、知道 request 已保存时才能声明已验证引用。完整结果仍由原文件拥有，不另写聚合副本。普通 start 返回 prepare／confirm／dispatch 各原 operation 引用；不得把私有 launch/environment 复制到 history。

没有完整、已验证文件结果时，必须使用 `inline` 保存该分支的**全部实际父侧 unknown／容量失败事实与完整 reason**；共同 identity／output 路径可按此新协议无损推导，不重复编码。未 spawn 的状态明确为 `operation_stopped=false, supervisor_returncode=null`；收到 stopped 但丢 result 与未 spawn 不能合并。不得把 unknown 映射成 not_started、durable stopped 或“没有执行”。

`stop_visible`、`stop_durable`、`admission_drained`、通知送达、`reap_record_observed`、`durable_stop_confirmed`、`executor_stop_confirmed` 的三值结果仍在对应原 H 结果；紧凑 envelope 只可声明观察／引用完整性，不新增推断的全局 stopped 布尔。server cancel／terminate 也不是这些事实的替代品。

每个分支在构造／启动失败时产生自己的完整 inline 失败，其余可构造分支继续；不能因 writer 的容量或某一个 owner 文件错误而取消 peer fanout。所有已创建实际任务都进入原统一取消／回收 finally。这里是原 fanout 用例内的失败局部性，不是第二调度器。

### 实际编码界与容量失败

探针用真实 SDK `DataConverter.default.encode([envelope])`，并以 `Payloads(payloads=...).ByteSize()` 计算包括 SDK metadata 的完整 protobuf payload 字节；没有只数 JSON 字符。合成 32 候选、66 分支的结果如下：

|完整合成封套|编码大小|结论|
|---|---:|---|
|66 个原 stdout 引用、每项保留实际 stopped／returncode|18,613B|此具体表示可装入 32KiB|
|66 个未 spawn unknown，全部完整内联原常见 reason|16,103B|不需要为未产生文件伪造引用|
|其中一个完整巨大中文异常|256,058B|明确超限；不截断|

这些数字证明表示可行，不证明任意授权／路径／异常都能放下，更不证明真实 server history 或 fanout 已通过。实际 input、每个完整 frame、activity result 仍各自测长。完整结果超过 32KiB 时以非重试容量失败 `cycle_activity_capacity_exceeded` 结束，不能报告 stop 成功或丢一部分 operations；已经产生的原文件和 worker 完整错误日志保留，明确本次没有完整 SDK completion。没有产生文件的巨大父侧异常不能变成“已留存原件”；只有完整 worker 日志可供诊断时须准确如此标注。下一次动作仍只能观察原件，不能因 completion 丢失重新授 start。

本片不承诺所有 32 候选在所有有效路径长度／异常下都可传输；若要求此绝对承诺，将需要不同的外部结果存储合同，超出本片“只复用原 operation 文件”的范围，应先修改设计而非临时加账本。

## C. 服务、Worker 配额、关闭与可选 SDK

### 命令与实际所有权

建议新增入口 `reference_training_worker.cycle_main(installation)`／异步 `_serve_cycle()`；`reference.training_cycle_worker_command(installation)` 用应用 `sys.executable` 与原预算 Worker 相同的 import bootstrap。真实调用链为：

```
services._prepare -> reference.training_cycle_worker_command -> cycle_main
  -> 所选 native 环境装载 -> 一个 cycle PID/event loop
  -> 普通 Worker + 独立 stop Worker
  -> async activity -> 原 _CycleOperation/_CycleCandidate/stop_live_controller
  -> S -> 原 processes.run(supervised=True) -> H/原 owner
```

`services.NAMES` 增加 `training-cycle-worker`，从原 `program:training-worker` 复制配置为独立管理项，`autostart=false`，日志分别为 `training-cycle-worker.log`／`.err.log`。不改原 budget Worker `_serve`／queue／8 槽或 283 参考文件。旧已运行 Supervisor 不会因 NAMES 多一项就装载新配置；缺项须明确拒绝并使用现显式 stop/shutdown/restart 流程，不隐式接管／刷新运行栈。

两个 cycle Worker 使用同一实际 client，但有各自的 task queue 和活动槽：

|Worker|queue|首版固定活动槽|注册内容|
|---|---|---:|---|
|normal|`ergora-training-cycle-v1`|1|inspect／start／reconcile 三项真实活动|
|stop|`ergora-training-cycle-stop-v1`|1|stop 真实活动|

这是首版配置选择，不是假设只能支持该默认值；本片不增加没人读取的调优参数。将来暴露范围后检查须跟随配置。**独立 stop queue 是必要条件**：同 queue 的 Worker 可能领取自己未注册的活动并失败，不能仅靠注册集不同来分流。独立槽也不是 OS 安全隔离；一个 adapter 在 loop 中同步 flock／fsync 仍会堵住两者，所以所有业务存储继续放 H。

首版不注册 `TrainingCycleWorkflow` 或 execution／collect／accept 的空壳活动。服务启动不自动发实验；测试用的最小 SDK Workflow 只能作为夹具，并如实标明。c1c 再处理正式类的可选模块装载、标准 sandbox 重新导入与 replay；b2a 不为不存在的正式类宣称 sandbox 通过。

### 关闭协议必须写入设计

SDK 1.34.0 的 `Worker.shutdown()` 发起 shutdown 并等待完成；其 run 文档与实现明确在 grace 后通知／取消活动，随后等待实际 activity task 完成。取消 `Worker.run()` 还可能取消关闭过程，因此应显式 shutdown、保留实际 run/shutdown tasks；不能用一个 timeout 后丢弃这些任务冒充完成。

建议首版 SIGTERM／SIGINT 设置进程停止事件；正常关闭顺序：

1. 标记 closing，normal 的新 start 不再领取新执行机会；显式发起 normal Worker shutdown。普通活动的 grace 取 0，使取消及时进入原 `_CycleCandidate`／`_CycleOperation` 清理，不能等原长预算结束才清理。
2. stop Worker 在 normal 的实际 S/H 和未交接 Popen 仍收尾时保持可运行；已领取 stop 使用原 total，取消时也持有原所有 branch tasks 直到实际 S/H 等待结束。normal 的关闭不能先 cancel stop task。
3. normal 完成后发起 stop Worker shutdown，等待所有已经产生的 S/H 完整退出观察；然后等待两个 Worker.run 的终态，再关闭 loop。重复取消沿原 shielding 处理，不先取消 loop 的所有任务。
4. 处理单个 Worker fatal error也走同一收尾流程；SDK fatal error本身不证明业务子树已回收。

这里“回收”包括真实 S/H、其原新 session 后代和**未交接**预算根的实际 handle／wait。已确认交接预算根沿 c1b1 可以跨活动／正常 loop 退出存活，其未来截止／清理由原 owner 负责；worker 服务关闭不自动变成 cycle stop，更不能统一取消历史已接受轮。`_ROOT_OBSERVERS` 只是观察任务，取消它不能报告活根已 wait／已停止。需要停止整个 cycle 时使用独立 stop 用例并分别核其 durable／执行链结果。

现从 training-worker 继承的 Supervisor `stopwaitsecs=15` 会在 SDK／原清理尚未结束时强杀 cycle PID；S/H 又在独立 session，不能假定 `killasgroup` 替代原 reaper。**此处是实施前尚待固定的具体 operational 合同**：建议新管理项采用显式较长的关闭观察期限（例如 70 秒，覆盖 60 秒冷观察配置与正常收尾余量），现 service control 的 1–60 秒返回仍可为 unconfirmed；不能因客户端等满就提前杀应用自己的清理任务。有限 stopwait 无法保证不可中断 OS spawn／I/O，最终 SIGKILL 只能记录“服务已退出、业务停止待对账”，不能承诺绝对有界且全部回收。精确秒数与强杀后的产品承诺需主控终核，不应暗继承 15 秒后称生命周期通过。

### SDK-free 与依赖方向

活动 decorators 和 Worker imports 仅在新入口／factory 实际启用时装载；现 worker 顶层无 temporalio import 的性质保持。`training_execution_protocol` 继续 stdlib-only；没有 State／SDK 反向 import。core 环境 import、离线记录读取／inspect／已有本地 stop 保持，启动 cycle 服务时 `services.control` 与直接入口均给出可见的 `ergora[temporal]` 缺项。Supervisor RUNNING 仍只表示 OS 服务状态，保留 `task_readiness=not_checked`，不能升级为队列注册／业务可用。

## D. 一次窗口、取消、恢复的具体规则

|路径|截止与取消行为|
|---|---|
|活动冷认证|一次固定 1–60 秒 BOOT observation 窗口，读原件、SDK 查询、同 attempt receipt 同步、result 读取都消费它；不得逐 RPC 或 H 重置。若拆成多个 H，必须复用原 bootstrap；现构造器对 observation 会新开窗口，需显式修正该调用方式|
|首候选 new start|认证完成后创建一次原 compute remaining∩control timeout 窗口；prepare／OS Popen／pipe transfer／confirm／dispatch 与最终结果消费同一个原 window；每个 H 重核原 source／parent／clock，不因 SDK活动重投或轮询续期|
|已存在 intent／attempt|不给 new_offer、不造替代 root；attempt 存在只走原 reconcile。lost completion 不是 resume 原 start 的许可|
|reconcile|本片用独立、有界的 observation 语义，只补同原事实；可以在 compute／total 已耗尽时观察，绝不把它转回执行窗口。SDK caller 的 timeout policy 在 c1c 固定，不能由恢复重开原授权|
|stop|冷读取有界；所有效果分支消费原 total，非正不 spawn。取消仍等待已创建分支实际回收；不能把 cancel 一组 Future 当 stop durable 或 reaped|
|取消首候选活动|交接前沿原 discard_root 保留晚到 Popen、关闭 stdin、精确通知并 wait；交接后不杀已独立 owner，后续只观察／显式 stop。原 slot／attempt 不回退|

活动 adapter 不能在 `finally` 无条件标 success 或返回一个未完整的结果；取消异常在原实际清理完成后继续传播。新总 Workflow 的 `maximum_attempts=1`、SDK timeout 导出、计数／history 限额和 c1d 接受门槛仍为后继片，并须早于自动派发上线；本片不能靠这些未来约定弥补当前接口允许重授的漏洞。

## 需要主控封闭的设计项与最小验收

|阻断项／最小修订|客观 acceptance|
|---|---|
|A1：固定新冷 H mode／activity_context；同 attempt reconcile 在补 receipt 前核真实 run|真实 SDK 编码路径令首活动先于客户端 receipt：相同 actual run 只补原 receipt，一次 controller start；不同 run／NOT_FOUND／reset／retry／input／memo／namespace／type／queue 不符在任何新 candidate intent／Popen 前阻断，原 attempt bytes／inode不变。不能只测纯 dict validator|
|A2：首版 new start ordinal 0；后继门槛仍归 c1d|原合法 ordinal 1 经真实 activity 请求明确拒绝，没有第二 intent／Popen／start；ordinal0 重复／lost activity completion 仍只有一个 offer／root／attempt。已有同 binding 的 reconcile 不补新动作|
|B1：结果 schema 和 S-owned 原 stdout ref；unknown 内联|实际 SDK 编码的 32 候选完整 `2+2N` 分支均出现、引用逐个存在／raw SHA一致、错误原件／错operation不接受；未 spawn／丢 result／post-stopped 阻塞的全部 unknown内联，未伪造引用；超限有明确非重试容量失败且保留已发生原事实。合成 18,613B 不代此检查|
|C1：两真实 OS Worker 服务、两 queue／配额、非阻塞 loop|经真实 Temporal 和 Supervisor 确认 budget PID != cycle PID；normal 与 stop 注册实际 queue。normal 活动占满其槽、H 持真实锁／fsync 阻塞时，stop 在自己的槽被领取，writer／另一 owner通知互不串行等待；不是靠 timer／fake Worker 或增大同一槽得到通过|
|C2：固定关闭秒数／强杀含义|真实 SIGTERM／SIGINT、重复 cancel、stop 活动取消、Worker fatal各路径：已有 S/H／新 session后代与未交接 root实际 wait／proc身份失活；已交接根按原合同存活后由原显式stop收尾并核回执。若被Supervisor强杀，结果明确未知，不报干净停止；不可中断 OS情况列为限制|
|兼容／来源|新非editable core/SDK：core不含SDK仍能import／离线观察；新服务真实拒绝缺SDK；旧schema1／schema2原件不升级、不续期；原budget queue／service和283参考bytes保持；已运行旧Supervisor缺新program时可见拒绝，不偷偷reload|

这些反例优先扩展既有 `test_training_submission.py` 的 controller dispatch／cycle operations／pending-root 接缝、`test_training_runtime.py` 的真实原入口、`test_services.py` 的 Supervisor 夹具与现架构检查；只有 SDK 路由／服务隔离部分需要真实 Temporal。测试 service 替身能验证编码与原 H 错身份，不能证明真实 poller 配额／关闭／标准 sandbox。

下一步是把 A1/A2、B1 和 C2 的具体选择合入主控服务设计并独立终核，固定前置 c1b1 产品基线后实施 b2a。execution／collect／正式总 Workflow／标准 sandbox／accepted-round／第二候选仍开放；本报告没有授权或证明这些后继能力已经存在。
