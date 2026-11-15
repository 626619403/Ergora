# c1b2b 原执行请求与运行观察消费者

日期：2026-11-16。状态：**只读准备完成，产品未改，等待主控明确“服务片验收通过，开始实施”。** 本记录属于主项目 docs；实施范围以[已独立通过的 r2 设计](../plans/2026-11-16-training-cycle-execution-consumer.md)、[后续消费者顺序](../plans/2026-11-16-training-cycle-runtime-consumers.md)和[独立设计复核](2026-11-16-training-cycle-execution-consumer-design-review.md)为准。设计两轴 approve／开放 0 只认证设计，未转作本片源码、安装或真实服务证据。

## 准备基线与授权

专属源码工作树为 `training-cycle-execution`，只读检查 HEAD `af176cf6e79adb9c6ef6f32946672bc77cdb89de`，初查 clean；最近三提交为 af176cf、97a0bbf、eedba08。af176cf 只调整一项正常测试的显式控制窗口，产品同前置 97a0bbf。主 docs 的 PLAN 仍把服务 N32 混合 unknown／容量现场补验列为在途，本片不自行关闭该门槛。

已读根、源码和测试 AGENTS、主 PLAN、组件变更协议、r2 两份消费者计划及其设计复核；使用 `maintainable-project-delivery`、`ergora-codebase-quality` 的 owner／测试接缝规则。主控限定本阶段只写本记录，不改 PLAN、他人报告、产品、服务端口或其他工作树，不运行全 suite、不提交或推送。独立实现审查应在实际实施和定向证据具备后另行进行；本次准备不是该审查。

## 已核接缝及真实消费者

|既有 owner|源码观察与后续最小接入|
|---|---|
|`reference_training_worker.create_cycle_activities`|现有工厂使用真实 `activity.info()`、严格业务输入和 SDK converter 容量检查，再驱动 `_CycleOperation`；注册表目前只有四个 v1 action。新增两 v2 action 沿同工厂／normal 槽接入，旧四返回封套保持。`_serve_cycle` 的 normal／stop 独立槽仍由原入口持有。|
|`training_execution_protocol.validate_cycle_activity_request/context/operation`|已有六字段身份、完整 SDK 来源、mode/action 映射、candidate context 和 BOOT/window 验证；两新 mode 必须同时进入 CANDIDATE 与 WORK 集合，不能只接观察集合。原 `cycle_operation_remaining` 已能消费 compute∩固定 window。|
|`worker._cycle_operation`、`_cycle_submission/_cycle_target`|H 中 `_load`、`_activity_binding` 认证原授权和父 receipt；原 selector 从冻结 ordinal 取得候选并核 intent／owner。新局部 H 算法由 `_cycle_operation` 一处调用，隐藏请求与三类观察的组装；不需要新模块、manager、ledger 或缓存。|
|`worker._select_cycle_project`|既有初始化选择原安装和 native 配置。冷 H 的 `_dispatch_controller` 已进行该选择；新的普通 H 应只选择一次，随后复用 operation／intent／owner，不再借 public execute/status 产生新 helper 或当前 preflight。|
|`reference_training_execution.Execution.request/check/current`|`request` 已完整确认 revision／intent／固定 run／native raw SHA，在父共享许可和 execution.lock 内不可覆盖发布；`check` 核原父 history、子 run/memo、QUEUED 和 job。新增 H 直接调用它，不调用 public execute。`current` 目前只核原 compute／来源等，尚未消费本次 operation window；这是 r2 要求实际扩展的位置。|
|`reference_training_budget.BudgetedStart`／`Execution.admit`|原 root 等 request 并持唯一 launch 机会；已有空／部分 launch 一样消耗机会。新消费者不得调用 `ensure_owner`、重建 root、重新 admission 或 native execute。`request` 的 schema2 H 来源要求与 root `admit` 的既有上下文须分别处理，不能令 root 错用已结束的短 H window。|
|`training_execution_protocol.ExecutionRecords`|`load` 验原五类链、`request_record(actor)` 验 start attempt／receipt 和 native 完整请求及 raw SHA，`observe(durable=True)` 同步并重读同一链。无 request 时 `load` 不会读取 native，所以不能据此合成 native QUEUED；部分／损坏链不能当 not_requested，也不另写容错扫描器。|
|`reference_training_runtime.lookup/observe`|固定 receipt.run_id 的 lookup 核完整原 Experiment，caller 还需核原 memo；observe 返回实际 Temporal status、phase、完整 Binding，RUNNING query 与 COMPLETED outcome 分开。缺 receipt 不查 latest run、不补候选 receipt。|
|`agent_platform.training.LocalTrainingAdapter.poll_job`|`exact_job` 验原 Binding／job，poll 验 result Binding／job 后返回 native 原状态。它与 runtime phase、durable stopped 是独立事实；不调用 collect_and_gate，不推 accepted／next_allowed。|

准备阶段没有观察到需要重开设计的矛盾。新增 source 检查仍有明确实施义务：把完整本 H operation 经原 `_Submission.payload.cycle_operation` 交到 Execution，使用原 protocol validator 和原 request.json 对照本 H mode/action/attempt、controller/ordinal、候选 intent、来源及父身份；不能只传 deadline 或复用 `cycle_start_source` 授权新 request mode。私有辅助函数若确需提取，只应承载这个内聚不变量，其生产消费者是原 Execution；不为未来调用者另建接口。

## 最小验证边界

优先扩展已有测试与 fixture。当前工作树 controller／SDK tests 仍位于 `tests/test_training_submission.py`；另一工作树的 CI 机械拆分不在本片编辑范围，未来整合再按实际迁移位置适配。

|行为／静默风险|现有接缝与必要观察|
|---|---|
|SDK 来源、旧合同和 v2 封套|`cycle_sdk_activity` 使用真实 SDK `ActivityEnvironment`／converter，跨真实 S/H；`controller_dispatch`、`training_controller_service` 提供原 history/memo 双。沿该路径增加两 action、ordinal=0、attempt>1 只观察、namespace/type/queue/run 漂移，保留旧四行为。它是本地 SDK 协议测试，不是真实 Temporal。|
|正常一次 request 到唯一 launch、丢回复和部分原件|复用 `controller_admission`、`cycle_candidate`、`service` 和现有 request-writer／consumed-launch tests；保留原 root、锁及链发布。断言原 request→唯一 launch，重复／重投／丢 completion／部分记录不补 root 或机会，而非仅 mock `Execution.request` 被调用。|
|receipt 早到、双 QUEUED|`training_submission_client` 的固定 run/query/native 接缝可延迟 job 或首次 poll；先记录 submitted＋SUBMITTING/native unconfirmed，再出现同 Binding/job 的双 QUEUED。request 一经调度永不重授的正式 history 分支仍属 c1c，本片仅证明 facts 足够表达等待和阻断。|
|最后同步读取过窗|扩展 `training_cycle_operations` 的真实 H 故障接缝，在异步验证之后、`current` 同步读取期间让 operation window 过期但 compute 仍正，再允许 H 继续一次；应无新 request/launch。不能只观察 S 已杀进程或外层 timeout。分别令 cold／control／compute 最短，核同一起点。|
|runtime/native/reap 交错|复用 runtime fixture、原执行历史读及真实本地 publication；覆盖 native result 早于 reap、reap 早于 phase，原事实分别返回，无接受或后继字段。|
|project/source/stop 漂移|沿已有最终 gate／controller pause／stop tests，使漂移发生在最后同步边界；应拒 request，保留已消费原件，不改变 schema1 人工确认和原 root 收尾。|
|容量及完整 ref/inline|复用 `test_cycle_sdk_capacity_counts_metadata_and_rejects_without_truncation`、真实 H frame 和父 late/cleanup tests；含新增 facts 的完整 v2 封套按 `Payloads.ByteSize()` 守 32 KiB，metadata 过界整体拒绝，不删字段／原错误／stop 分支。|

可用前置 `package-r3/venv-r3-sdk` 的已有解释器进行后续源码定向测试；须显式选择本工作树源码并记录实际 import 来源。该解释器及前置 wheel `081aab45` 仅是依赖环境，不会因此成为本片新安装结果。新非editable core／SDK、283参考／source pin、真实 Temporal 和独立预算根的 E6/E7 仍需在实施后分别验收。

## 当前实际检查和未验范围

本次仅执行 Git 身份／状态、`rg` 定位与文档／源码／fixture 阅读；核实前置 package-r3 SDK 环境目录存在，未执行其中解释器或声称重新安装。唯一写入为本记录。未运行测试、服务、训练、native executor、安装／构建、自身模型审查或独立产品审查，未修改任何产品／测试／资源／PLAN／其他报告，未 commit／push。

下一步由主控在服务终核后发出明确实施指令；再按 r2 先扩原三个 owner、沿上述最小接缝验证，并记录真实源码与证据身份。正式总 Workflow、标准 sandbox/history/replay、accepted／rounds／后继和 WA 人类设计关卡均另片交付。kernel v3、全部祖先资源与逐级收窄权限不在本片改动范围。
