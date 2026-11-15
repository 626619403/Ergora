# c1b2a 独立 cycle 服务：产品两轴审查

日期：2026-11-16。审查者：fresh-context 独立 reviewer `cycle_service_product_review`。本轮只读源码、原件与 SDK，并仅写本报告；没有改产品、装包、启动服务、运行昂贵测试或提交。先读原 r2 合同与 controller contracts，再看实际 diff／调用者，最后读作者记录。应用 maintainable-project-delivery 的 independent-review、ergora-codebase-quality 的 module-design／test-seams／repository-style。

## 范围与结论

- 项目：Ergora；实际产品树 `.ergora/worktrees/training-cycle-service`。
- baseline：`6725e62511aa4a5b68baf684ec3cbc1f0470d3e6`；审查 HEAD：`fef7d98e30d5625e5ce37dc45e14904f76447775`。
- 产品差异仅 `reference.py`、`services.py`、`reference_training_worker.py`、`training_execution_protocol.py`。同时检查本片三个既有测试文件、两个 fixture 的差异，沿原 runtime lookup、training_cycles、budget_clock、candidate／S-H／reaper 调用链核查。
- 需求轴：**request changes，开放 4 项**。R1／R2 为关闭生命周期问题，R3 为完整结果丢失，R4 为容量错误分类丢失。安装与真实服务验收仍 pending；下列 finding 来自具体源码／SDK 路径，不以在途验收缺失作为产品 bug。
- 可维护性轴：**approve，独立开放 0 项**，限本轮所审查的所有权与抽象结构。行为 finding 不重复计为冗余抽象问题；需求轴修复后仍需复核实际改动。

本文产品行号均对应上述 HEAD。主树未合入本片时，须在指定实现树打开同名文件。

## Findings

### R1 — P1：启动验证失败后，无条件 shutdown 等待一个永远不会置位的事件

位置：`src/ergora/reference_training_worker.py:1098–1100`，入口 `:1090–1094`。

`_serve_cycle` 已看到某个 `worker.run()` 完成后，仍对每个 Worker 无条件先 `await worker.shutdown()`。实际安装的 Temporal SDK **1.34.0** 在 `Worker._run` 最前面执行 `await self._bridge_worker.validate()`，位于设置 `_started` 和实际关闭流程之前；若 namespace／连接验证抛错，`run()` 结束，但 `_shutdown_complete_event` 不会置位。`Worker.shutdown()` 只置 `_shutdown_event` 然后等待 `_shutdown_complete_event`，此时再没有代码会完成该等待。

最小情景：一个 Worker 的启动验证失败，另一个 Worker 已经运行；服务进入 finally 后卡在失败 Worker 的 shutdown。若 normal 失败，stop 的关闭步骤永远到不了；若 stop 失败，normal 关闭后仍无法退出。SIGTERM／重复取消也不能解除 shield cleanup，最终只能依赖外部强杀。单 Worker fatal／启动失败不能可靠结束两个 run／shutdown task。

独立内存探针直接使用已安装 SDK 的真实 `Worker.run()`／`shutdown()`，仅以 `Worker.__new__` 设置空 plugins、两个真实 asyncio.Event 和抛 `RuntimeError('namespace validation failed')` 的 bridge.validate；没有 server、活动或进程。输出：

```text
run_done: True run_exception: RuntimeError('namespace validation failed')
shutdown_waits_forever_after_validate_failure: True
```

第二行由 50ms `wait_for(worker.shutdown())` 超时、且 complete event 仍未置位证实；SDK 源码解释了为什么这不是时间不足。

最小修正：关闭协调器区分已经结束的 run 与仍在运行的 run，不能对启动失败后已结束的 run 盲等 shutdown；保留原异常并继续关闭其余 Worker。SDK 公开契约说明正常 `run()` 返回意味着关闭已完成，`shutdown()` 在验证失败前返回的这条路径却无完成保证。可围绕 run task 终态与 shutdown task 协调，避免依赖 SDK 私有事件；处理检查后 run 又失败的竞态。不要用固定超时放弃活动实际资源收尾。

验证：在现有服务接缝注入真实 SDK validate 失败，并保留另一 Worker 活动，确认异常可见、另一 Worker 收尾且两个任务终态；覆盖失败发生在关闭检查前后。

### R2 — P1：等 Worker.run 终态才发现 fatal，normal 会在 stop fatal 清理期间继续领取

位置：`src/ergora/reference_training_worker.py:1085–1094`。

两个 Worker 没有注册 SDK `on_fatal_error`，服务仅等待 `worker.run()` 完成。SDK 1.34.0 的真实顺序是：内部 poller 异常 → 调用 `on_fatal_error`（若提供）→ initiate_shutdown → 等待活动真实完成 → 设置 complete event → 从 `run()` 抛出。故 run 终态是**清理完成通知**，不是 fatal 发生通知。

最小情景：stop Worker poller fatal 时，它已领到一个仍持有 S/H 的 stop 活动；该活动因实际存储／退出观察而继续清理。stop Worker 的 `run()` 尚未完成，`_serve_cycle` 仍等 FIRST_COMPLETED，normal Worker 则仍可领取新的 start／inspect。服务未按合同在单 Worker fatal 时进入 normal-first closing。正常 SIGTERM 路径的顺序不能证明该 fatal 路径正确。

证据：只读安装 SDK `temporalio.worker._worker.Worker._run`，其 `on_fatal_error` 回调在 initiate_shutdown／wait_all_completed 之前，而 `run` 异常在末尾重抛。没有用服务替身的即时抛错行为代替这段实际 SDK 语义。

最小修正：使用已有 SDK `on_fatal_error` 作为及时通知，将首个错误交给服务并触发同一 closing event；回调应迅速返回，不在回调内等自身 shutdown。仍按 normal 实际终态后关闭 stop 的协调顺序持有任务；与 R1 的启动验证失败路径分别处理。

验证：fatal 后让失败 Worker 的已有活动保持真实清理未完成，确认 normal 已停止领取并进入清理，而不是等失败 Worker 完全退出后才动作；保留原资源等待和最终 fatal 异常。

### R3 — P2：start 的父侧错误／清理事实在结果封套中丢失

位置：`src/ergora/reference_training_worker.py:1019–1021,1035–1039`；事实来源 `:305–307,331–345,372–383`。

adapter 收到 `candidate.run()` 的完整 outcome 后，仅把 `candidate.operations` 与 `candidate.results` 投影为 operations。`outcome` 自身除了 status／runtime_status 外均被丢弃。父侧 Popen 异常、input transfer 异常、窗口到期原因以及 `cleanup_problem` 并不属于 H stdout，也不在这两个列表中。

最小情景：prepare H 成功返回 new_offer、原 intent 已占用，随后 `Popen` 因文件描述符耗尽抛 `OSError`。candidate 返回 `status=unknown, reason=<完整 OS 错误>`；activity 最终只返回 prepare 的成功 ref 与 status unknown，没有原始 reason。这份 prepare stdout 没有记录后来的父侧错误，所以不能宣称它已被引用保存。未交接根通知异常后实际 wait 完成的 `cleanup_problem` 也同样丢失。调用方无法区分出生前、输入传送中或确认失败，更无法恢复完整原观察。

独立内存探针使用真实 SDK ActivityEnvironment／DataConverter 和当前 adapter，仅替换冷操作与 candidate 的无资源结果。candidate 返回 `reason='Popen: Too many open files'` 及 `cleanup_problem='notification failed'`，输出：

```text
start status: unknown
parent_error_retained: False cleanup_error_retained: False
```

这是投影接缝探针，不冒称真实 Popen 资源故障实验；真实可达异常来源已由上述 candidate 源码定位。

最小修正：把父侧 outcome 中没有原文件承载的完整事实保留为合适原 operation 的 inline 结果，并同时保留已验证的各 H 原始引用；不要把 prepare 的 ref 当作后续父侧错误的归档。保留固定封套合同，必要时在既有 inline 内表示父观察；超过容量则明确非重试失败并保留完整 worker 错误。无需增加新聚合账本或通用 result 框架。

验证：现有 candidate／SDK activity 接缝注入 prepare 后 Popen 失败及 cleanup_problem，核最终封套含完整原原因；长原因超限时不能悄悄丢字段以通过容量检查。

### R4 — P2：两条容量失败路径被降格为普通 unknown，未触发非重试容量拒绝

位置：`src/ergora/reference_training_worker.py:805–812` 与 `:901–906`；分类消费 `:1031–1034`。

第一条：stop 构造器在完整 request 超过 32KiB 时抛 `_CycleCapacityError`（`:68–70`），但 `stop_live_controller` 的 ValueError handler 将它统一改为 `status='unknown'`。所有 peer 会正确继续／收尾，但最终容量检查只识别 `capacity_exceeded`，因此该失败被当成普通完成结果返回。可达输入是业务 stop request 本身能装下，加入已验证 snapshot／context 后 stop-writer operation 才超限，例如较长 reason；其余不携带 reason 的 branch 仍可构造。

第二条：真实 H stdout 超过 32KiB 时，S 调用 `_read_bytes(..., _CYCLE_LIMIT)` 直接抛普通 ValueError，发生在 frame 的 capacity 分类逻辑之前。S 已发 stopped 帧，随后无 result 帧退出；父侧因此返回通用“no complete in-budget result”unknown，丢掉容量分类。较大的合法 frozen snapshot 或完整 H exception reason 均可到达；原合同明确不保证所有这些内容都可装下，但要求明确容量拒绝。

独立内存探针使用真实 ActivityEnvironment／DataConverter 与当前 stop adapter，仅令 stop-writer 构造抛真实 `_CycleCapacityError`、其余 branch 完成，输出：

```text
stop status: observed
capacity_branch.result.inline.status: unknown
capacity_branch.result.inline.reason: Complete cycle operation request exceeds 32 KiB; nothing was truncated
```

这证明第一条分类丢失；第二条以实际 `_read_bytes` 和 S／父读取控制流为证，没有另跑真实大文件 fixture。

最小修正：在分支构造／运行记录中保留 typed capacity 状态，仍运行并等待其他已创建 peer，最后统一发非重试 `cycle_activity_capacity_exceeded`。S 对实际 stdout 读取容量失败也须产生可识别的容量结果并记录完整错误；没有完整验证 bytes 时不可伪造 ref。不能将所有 ValueError 都当成容量错误，也不能把 reason／分支截短来通过编码。

验证：业务输入低于上限而 operation request 超限；H stdout 本身超限；完整 frame 增加身份后超限；DataConverter metadata 使最终 Payloads 超限。这些在原接缝中分别核分类、peer 收尾、原件和未伪造引用。

## 需求与维护性核查范围

已据源码确认：独立 cycle 命令及 PID 入口；normal／stop queue 各 1 槽；原 budget Worker 8 槽未变；四个真实 SDK 活动的严格业务字段与 source 信息；H 核原 controller intent／attempt／receipt，缺 receipt 时用 activity 的实际 run 查询再记录；普通认证和最终执行 gate 分开；attempt>1 start 只 reconcile；ordinal>0 在 prepare／Popen 前拒绝；stop 完整 2+2N fanout，构造失败不抑制 peer；原单次 compute/control window、S-H/reaper 和未交接 Popen 持有原则仍在；已交接根不因服务正常关闭统一通知取消。

本片沿原 owner 扩展，没有新增产品模块、通用活动总线、第二账本或线程中的业务 I/O。`_activity_binding` 的 H 本地来源认证、`_cycle_capacity` 的 SDK 编码边界和 `_activity_operation_result` 的真实 ref／inline 投影各有明确职责；注册闭包属于 SDK 必要适配。protocol 的跨进程输入验证、candidate prepare 来源重读以及调用前认证保护不同的持久／时序边界，不应只因重复字段就删掉。未发现需要独立阻塞的冗余抽象／无消费者配置；R3／R4 要修复事实传递，不应扩展为新框架。

测试覆盖了真实 S/H 的既有生命周期、ActivityEnvironment 下的来源反例和完整 refs，不能单独证明实际 Worker fatal／启动验证语义。当前 start happy path／重复只对账测试不能揭示 R3 的父侧异常丢失；构造失败测试用普通 ValueError 和最终超大 inline，不能揭示 R4 的 typed operation 容量被吞。

## 验证、原件与开放验收

本轮执行：固定 diff 与邻接源码／SDK 源码只读分析、`git diff --check 6725e625 fef7d98`（通过）、上述两个短时无资源 Python 探针（一个 SDK shutdown 探针，一个包含 start／stop 的 adapter 投影探针）。使用已有 SDK Python、`-B`；未创建业务文件或真实服务资源。探针结论只覆盖所述接缝，不替代全链验收。

只读核对 package-r1 的 core／SDK manifest：均记录 663 产品文件，SHA256 `b7e282af7a9e154a6b61525ca36cbc9d834ef0d2c92fb701dae5bea69685fcfd`，source／wheel／installed 相等，变更四产品文件；SDK 为 1.34.0，core 无 SDK。这里核的是原记录，不是 reviewer 重建／安装或全文件重新认证。

作者记录中的源码 tests 保持其原范围。完整安装回归、真实 Temporal／Supervisor 的双 PID／双 queue、normal 存储阻塞时独立 stop、SIGTERM／SIGINT／重复取消／fatal／强杀 unknown、实际退出原件均由主控在途验收，**本轮 pending acceptance**。修复后的源码与新包不能继承旧包结果；应以新身份针对受影响行为复验，再由同一 reviewer 复核 R1–R4。

正式 TrainingCycleWorkflow、sandbox、execution／collect／接受与后继候选均不在本片，不据本审查声称自动训练循环或训练质量已验收。
