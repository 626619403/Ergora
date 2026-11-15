# c1b2a 产品审查 R1–R4 修正

日期：2026-11-16。工作分支 `feat/training-cycle-service`，起点及当前 HEAD `fef7d98e30d5625e5ce37dc45e14904f76447775`；以下为未提交差异。依据主树同日产品审查 R1–R4 与[原 r2 合同](../plans/2026-11-15-training-cycle-service-boundary.md)。产品差异仅 `reference_training_worker.py`、`training_cycles.py`；测试沿原 `test_training_runtime.py`、`test_training_submission.py` 与 `fixtures/training_cycle_operations.py`。本记录不覆盖此前存在的其他未跟踪交付文档。

## 修正与原失败

|Finding|原实际失败|修正与验证|
|---|---|---|
|R1 SDK validation 失败后 shutdown 永等|真实 SDK 1.34.0 `Worker.run`/`shutdown`，仅 bridge/poller 替身：normal validation、stop validation、shutdown 已调用后 validation 才失败，三例均因服务未结束失败|逐 Worker 协调公开 run 与 shutdown task。run 已终态不调用 shutdown；运行中同时观察两任务，保留 run 至实际终态，再收齐 shutdown waiter。若 run validation 异常导致 waiter 无法完成，仅取消该已无 run cleanup 的 waiter。原异常保留，继续关闭 peer；无固定产品超时、无 SDK 私有事件依赖|
|R2 stop fatal 的活动 cleanup 阻塞时 normal 未关闭|真实 SDK poller fatal 已进入 `wait_all_completed`，服务仍未调用 normal shutdown；原测试超时失败|注册 SDK `on_fatal_error`，保存首错并立即置同一 closing event，回调不等自身 shutdown。测试在 stop cleanup 未释放时观察 normal 已 initiate_shutdown，随后两次取消服务任务，释放 cleanup 后核实际 finalize、原 fatal 异常与零残留 asyncio task|
|R3 父侧 reason/cleanup_problem 丢失|真实 SDK ActivityEnvironment、真实认证/prepare S-H，prepare 后注入 Popen OSError；另例真实创建根并注入 transfer 错误、实际 discard/wait 后注入 cleanup_problem；两例完整原因均未出现在封套。长父原因例原本未拒绝容量|保留全部原 S refs；将与最后 H 结果不同的父 outcome 作为同一实际 operation 的额外 inline 观察。仅去除已由原 refs/inline 承载的 preparation/confirmation 嵌套结果，不改固定封套 key 或 ref/inline 互斥。三个反例修后通过；长原因完整进入 SDK 容量拒绝，不通过丢字段缩短|
|R4 operation request/stdout 容量退化为 unknown|业务 request 本身小于 32KiB、加入 snapshot/context 后 stop writer 构造超限；真实 H 输出超过 32KiB；两例原本均未抛非重试容量错误。另有原 frame 增加身份后超限例作为已正常工作的对照|stop 构造与运行记录保留 typed capacity；所有可构造 peer 仍完成后 adapter 统一非重试拒绝。S 精确捕获真实 stdout 容量错误，保留 stdout/stderr 原件并返回 capacity inline，不伪造 ref。原 frame 容量回退仍保留已验证 ref；SDK Payloads metadata 超限仍明确拒绝|

R1/R2 测试使用真实 SDK 生命周期代码，fixture 初始化 SDK 内部 bridge/poller 接缝；产品代码只使用公开接口。测试 finally 仅为避免旧缺陷挂住 pytest 而释放 fixture 的 shutdown event；成功断言及无 pending task 核查在此 rescue 之前。它不是产品收尾机制，也不是实际 Temporal server 验收。

R3 的 cleanup_problem 例是投影接缝注入，根的创建、EOF、discard 与 wait 为真实 OS 行为；未冒称实测通知系统调用故障。通知失败仍等待真实根终态的原独立接缝 `test_cycle_candidate_root_cleanup_waits_after_notification_races` 未改。

R4 原 `_read_bytes` 只能以普通 ValueError 报容量，S 无法在不解析错误文案或复制安全 reader 的情况下精确分类。经主控确认，将原 worker 的同一 `_CycleCapacityError(ValueError)` 移到 `training_cycles` 原读取 owner，worker import 复用。仅超长读取抛此子类，旧 ValueError 捕获与完整原错误文案不变，普通文件/符号链接检查不变；未增加调用者可注入 exception class 参数或第二个近似异常类。该 owner 已属原 GATE_SOURCES。

容量 fixture 在故障前经原 `CycleAdmission.request_stop` 发布有效 stop，使 drain 能观察真实已停止准入。第一次探索运行未预先发布，writer 构造失败使 drain 合理等待原 stop；已用原 owner 显式发布后让其完成，未杀进程或取消 peer。保留探索记录，并以修正 fixture 的独立 baseline 重跑作为 R4 反例证据。

## 检查与身份

全部使用已有 SDK 验收解释器、显式 `PYTHONPATH=src` 导入本工作树源码，SDK 1.34.0。**这些是源码验证，不是新安装包验收**。原始日志、source-identity.json 与 changes.patch 在主树 ignored 检查目录 `review-fixes-r1`，由主控持有；没有重跑旧 76 项或 BR50。

- `lifecycle-before.txt`：4 failed，9.19 秒；覆盖 R1 三时序与 R2 持有 cleanup 的 fatal。
- `adapter-before.txt`：5 failed / 1 passed，133.81 秒；探索运行含上述原 owner 显式释放 drain，保留 R3 三反例及 R4 证据。
- `capacity-before.txt`：修正 fixture 后，2 failed / 1 passed，19.32 秒；两容量缺陷仍实际复现，原 frame 路径通过。
- `fixes-after.txt`：11 passed，36.38 秒；四生命周期、三父观察、三 operation/frame 容量、一个 SDK metadata 容量。其后仅整理 shutdown 协调器的重复 gather，并给生命周期测试增加零残留 task 断言；最终源码在下列受影响组复核生命周期。
- `affected-original-after.txt`：14 passed，103.44 秒；最终生命周期4项、SDK metadata、原 aggregate 容量、真实SDK来源/只对账/离线stop/66 refs/两类构造失败/正常start及最终来源复核。未扩大至旧完整suite。
- `git diff --check`：通过。

最终两产品文件 SHA256：

- `reference_training_worker.py`：`fbb6b9bb5f7513abceb25039bf606f2185e4eddc0808717705481c326778e14e`。
- `training_cycles.py`：`07215a1b1b1876c462333154ef834ef73f2a3b6020703270bfb3395c084f5972`。

## 交接边界

未提交、未推送。新非 editable core/SDK 包、真实 Temporal/Supervisor 双服务及信号/强杀验收由主控处理；旧包不能继承本次源码修正结果。fresh reviewer 须对实际差异复核 R1–R4，当前仅为作者修正及源码检查完成状态，不声明审查关闭。

原 H 可信来源、一次计算/控制窗口、唯一 reaper、完整候选引用、未交接根实际 wait 与已交接预算根自持保持。没有父 loop 业务文件读取、新账本或通用框架，没有以硬超时放弃实际清理。总 Workflow、后继候选、execution/collect、GPU 或训练质量均不在本次验收范围。
