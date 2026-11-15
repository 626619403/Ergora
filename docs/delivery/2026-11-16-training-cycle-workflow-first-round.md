# c1c 首轮 TrainingCycleWorkflow 实施准备

日期：2026-11-16。状态：**只读准备完成，等待主控闭合 c1b2b 真实现场／完整产品终审并明确发出实施信号。** 本轮唯一写入为本记录；未改产品、tests、主 PLAN、他人报告或 283 reference，未构建、安装、执行测试、启动服务、访问业务训练仓库或 commit/push。

权威要求为[首轮详细设计](../plans/2026-11-16-training-cycle-workflow-first-round.md)和[独立设计审查](2026-11-16-training-cycle-workflow-first-round-design-review.md)。已读根、src、tests AGENTS、主 PLAN、组件协议及 `maintainable-project-delivery`、`ergora-codebase-quality` 的 owner／caller／测试接缝规则。本记录接续设计，不重做设计审查。当前设计文件 SHA256 为 `d01d5774d592e21178cdabc2a918a61c7ba7f32a673daf6ac321849b28a8dbcb`；独立报告内的 `104624…` 是其原审查样本，不改写历史身份。

## 静态基线与可继承证据

主树分支 `refactor/architecture-foundations`，HEAD `86356927cd88750717bb910502e3f7bd66aa41ba`；已有他人在途 docs。消费者专属树 `training-cycle-execution` 当前 HEAD `bcc304894622040a7d844f8c6f9ddfded65aa895`、工作区 clean，双亲为 r5 `585e3dabefdde93ac826dec0aa45aa5cb27f420e` 与 CI `7ed77c9c1eebc0e16c2f9024c62b0d4fd25b7220`。尚未把该候选导入主树。实施树／基线由主控发信号时确定，不在主树误用旧产品。

本轮实际重读三 owner 的 raw SHA256，均与前置记录相同：

|owner|SHA256|
|---|---|
|`reference_training_worker.py`|`d42d090b2988ff4a80376ee25692430cf28dd74117356682749f1149ed12176c`|
|`training_execution_protocol.py`|`b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`|
|`reference_training_execution.py`|`f6b4a1ab90bdcaa3737b3c75abbaeaea6ee8afd029b3033cfbdc6a630531ad1b`|

已实际重算前置 wheel SHA256：`55029a3b4b574b7934e40bc115b32ff4b99600a9e47894dbaf1c6c59937e5bba`，实际 SDK metadata 为 1.34.0。[安装报告](2026-11-16-training-cycle-execution-installed-checks.md)及[消费者交付末节](2026-11-16-training-cycle-execution-consumers.md)记录 source＝wheel＝core／SDK site 各663项、core 无 SDK、283 reference／依赖保持、183输入／462冻结运行文件、2236唯一 collect 节点、15项安装定向通过、SDK-free 真实 S/H inspect 与 scoped cleanup。这些是前置原证据；本轮只读了 driver、freeze summary、selected result／JUnit、core inspect result，未重跑或扩大验收范围。自身 Codex supplied-source approve 亦沿原报告归属，不替代真实现场或终审。

## 固定 producer 与消费边界

已沿专属树核生产链：`cycle_main → _serve_cycle → create_cycle_activities → _CycleOperation/S/H → _cycle_operation → _execution_candidate_operation`。normal 注册旧 inspect/start/reconcile 与两个新 v2，stop 独立 queue，各活动槽1；原预算 worker 保持8槽。当前没有正式 `TrainingCycleWorkflow`，normal 没有 workflows 注册，不能将旧活动测试或测试 Workflow 称为 c1c 已实现。

固定 wire 满足保守的首轮消费：六字段原输入、ordinal0、四旧 v1 保持；仅 observe-candidate／request-execution-or-observe v2 附 facts。facts 的 source operation 可来自 inspection 或 ordinary operations，不能只查后者。预算含 work／total／control／boot；candidate、submission、execution records、runtime、native 分项齐全。H 核完整父原件与固定 run，runtime COMPLETED 的 phase 来自原 outcome.status，故可表示 RELEASE_EXPIRED／INTEGRATION_TASK_CREATED。原 request owner 仍在锁内 publish 前后核 source／window。外来 runtime job 已使 runtime unconfirmed、整体 unknown，保留原观察。

以下没有新增 producer 扩展授权，消费者不得猜测补齐：

- `stop.v1` 没有 cycle 级 durable／admission drained／executor typed 汇总。只可记录唯一 stop command／transport 结果；query 的 cycle stop 字段保持 null／needs_reconciliation，不能以 envelope observed 或 operation_stopped 代替。若将来要求直接认证，须另立 producer wire 变更。
- receipt 早到、runtime SUBMITTING／native request 尚缺时，固定 producer 返回 runtime 已查、native unconfirmed，整体可能 unknown；其 problems 是文字，没有区分正常未发布与各种损坏的 typed reason。完整已认证分项可保存并有界只读观察；不得读错误文字重授 start/request。身份／source／clock认证缺失时保守对账，不在 Workflow 另读 refs／文件。
- start／reconcile v1 没有 work facts，只有旧 total observation；不能拿旧结果创建／延长 work 截止。cold facts 不等于 runtime 已查询，只有后续完整同 run、Binding/job 与双 QUEUED 才能请求。
- 本片没有 accepted archive／gate／rounds 可消费许可；native成功、reap、runtime phase 各自独立。c1d 前 ordinal1、measurement_accepted、selection_complete 始终禁用。

## 最小实施与已有接缝

收到信号后的首选产品改动只有原 `reference_training_worker.py`：模块级可选 SDK 导入／应用依赖 pass-through、真实模块级 decorated `TrainingCycleWorkflow`、显式工厂、run/status/request_stop 和少量内聚私有方法，以及 `_serve_cycle` normal 注册。`training_execution_protocol.py` 只在确有共享纯 shape 校验需要时调整；不预设改 runtime／submission／execution、增模块／manager／reader／账本。原 source-pin owner 已覆盖 worker，旧 live owner 不因换源码继续执行。

实际唯一工厂 caller 是 `_serve_cycle`；run/query/signal 是框架必要入口。已读新安装 SDK 的 `_definition.run`、sandbox `_runner._create_instance`、deterministic `_asyncio.wait`、`_workflow_instance._await_temporal_operation`、公开 payload converter／history info 源码：run 拒绝 locals 类，默认 sandbox 按 module/name 重导，wait 的 finally 只移除回调，直接 await activity 的取消会由 SDK 等待处理。因此仍按设计持有 ordinary handle、先取消请求并立即调独立 stop、shield 唯一 stop、最后传播 CANCELLED；本轮源码阅读不认证该时序已经运行。原 `_ErgoraPackage` 仅在真实新安装复现 package 导入失败时复用。

现有测试归属已按 bcc3048 核实：`tests/test_training_runtime.py` 有真实 SDK capacity、ActivityEnvironment 的 source／window 和真实 SDK service lifecycle 接缝；`tests/test_training_submission.py` 保留 `cycle_sdk_activity`、receipt前首活动、双 QUEUED／外来job／丢 completion、最后同步gate、完整 stop／capacity；`tests/test_training_cycle_controller.py` 有原 root、取消／交接／stop 及共享 `cycle_budget_root`。`training_controller_service.py`／`training_submission_client.py` 是真实 codec＋固定 history 的离线替身，不是实时 server。`tests/test_budget_workflow.py` 提供真实 local Temporal／Worker／package finder 使用先例，但不覆盖本类。优先沿这些文件补最小行为检查，不新加 CI job 或重复服务 fanout 矩阵。

## W0–W10 执行次序

下表均未执行；精确定义仍以权威设计为准。先取得主控前置终核／实施信号，再固定实际候选及输入。

|次序|节点及证据重点|
|---|---|
|1|W0：可选 SDK/core 缺失边界、模块身份及默认 sandbox 准备；正式 normal Worker 注册、原预算进程／stop槽保持。|
|2|W1：正式类真实首轮，receipt先到／SUBMITTING等待／双QUEUED；history一次start/request、原request/root/唯一launch与ordinal1缺席。|
|3|W2：command前后／fsync后丢completion，文件不存在亦不重授；原attempt／receipt／request／launch数量与SHA。|
|4|W3、W4：同run worker重启、成功／失败／终态history replay；A+remaining只收窄、v1不刷新work，排队／回传／timer及server暂停后BOOT最后gate无新publication。|
|5|W5、W6：normal真实阻塞下重复signal/cancel即时独立stop；唯一stop／total不续、CANCELLED与实际资源分列；native/reap/phase交错不接受测量、不写rounds、不发ordinal1。|
|6|W7、W8：全部ordinary失败亦计256，真实server history阈值与stop余量；实际Payloads含metadata的32KiB拒绝及完整query/outcome／stop失败保留。|
|7|W9：原身份／source／project／旧pin拒绝与显式本地恢复；只补与本片新增路径有关的回归。|
|8|W10：新candidate的新wheel、core／SDK site与输入冻结、283／依赖；正式默认sandbox真实首轮及代表性恢复／丢reply／取消；全自建进程、端口、Workflow收尾。新安装不能继承55029对新字节的认证。|

随后更新本片状态与主 PLAN（由主控协调），提交完整实际差异／验证给新的 fresh reviewer 做需求／维护性两轴，并跑自身原结构模板。CPU受控runner只证明控制／执行链，GPU、训练质量、真实接受／两轮、公共入口和 WA 未决人工设计另属后继。当前下一步为等待主控提供实际 c1b2b 现场／终审结果和实施信号。
