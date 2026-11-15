# c1b2b 执行消费者独立设计审查

日期：2026-11-16。Reviewer：fresh-context 独立 reviewer `cycle_execution_design_audit`。审查对象是尚未实施的设计；没有把不存在的新接口或未执行的验收视作产品缺陷。

**结论：需求轴 request-changes，开放 2 项；可维护性轴 approve，开放 0 项。** 现有 owner 选择和依赖方向合理，不需要新 executor、ledger、调度器或 reader。进入实施前须明确最后请求 gate 的一次窗口接入，以及提交确认到唯一请求活动之间的等待条件。两项均交主控修订草案，本审查未修改方案或产品。

## 范围与身份

- 主仓库 HEAD：`478c98891522930817fa7005a8ac96e408f37230`；服务产品尚未导入主树。
- 实际检查的产品树：`.ergora/worktrees/training-cycle-service`，HEAD `eedba08c8c112683a7946726aab3f4fd590f26d6`。下文源码行号均指此树此版本。
- 待审主树草案：[runtime consumers](../plans/2026-11-16-training-cycle-runtime-consumers.md)及[execution consumer](../plans/2026-11-16-training-cycle-execution-consumer.md)，均为未跟踪设计文件；以本次实际读取内容为准。
- 已读根及源码目录 `AGENTS.md`、`docs/PLAN.md`、组件变更协议、[原具体合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、c1 工作流计划，并按 `ergora-codebase-quality` 和 `maintainable-project-delivery` 的 independent-review brief 独立核对需求与维护性。
- 实际跟踪 `Execution.request/check/current/admit`、`BudgetedStart.source/context/require_active/check_controller_history`、SDK 工厂与 S/H、candidate root 交接、protocol 验证／窗口／执行链、runtime lookup／observe、native poll 与原 ExperimentWorkflow。未沿用前片测试通过结论认证新消费者。

## Findings

### R1 — P1：外层 coroutine timeout 尚不能把一次操作窗口接到最后 request gate

**位置：** execution 草案第 88、97–105、153 行；runtime 草案第 15–16 行。

草案要求整个 coroutine、最终同步和请求都消费同一收窄窗口，但接入方案只明确给 `_Submission.payload.timeout` 一个剩余浮点数并在外层加 timeout。现有 `reference_training_execution.py:50–60` 的 `Execution.current` 检查 project、原 context／compute、native 痕迹和解释器，不检查本次 operation 的固定 BOOT deadline；`request:72–77` 在同步 `current` 返回后直接 publish。`check:34` 的 payload timeout 是相对数值，之后也没有在同步发布边界扣除本次已耗时。

**可达情景：** 请求的异步 history 核对及时完成；随后锁内 `current` 的源文件／State 读取接近截止时阻塞，在截止后、S 下一次监管检查前返回。原 compute 仍为正，因此现有 `current` 通过并开始 `publish(request.json)`。`asyncio.timeout` 的取消不能在这一串同步调用之间运行；S 的监管回收也不是最后动作 gate（`processes.py:168–175` 按最多 0.2 秒等待轮询，worker `cycle_operation_main:869–895` 使用此监管）。原预算根随后只按自己的原 compute/context 接受 request（`Execution.admit:90–109`），不会知道这个请求活动的控制窗口已过。结果虽不会产生第二 launch，却可在草案声称禁止新 request 的窗口之后开始发布。

**最小修订：** 在设计中明确把固定 operation payload/window 交给原 `Execution` owner，并在原锁内完成同步身份核对后、实际 request 发布前，以及发布同步后的原最后 gate 检查同一剩余窗口；不能仅依赖外层异步 timeout 或父侧进程回收。保留既有人工路径语义，无窗口的旧手动请求不隐式取得新权限。若拟通过原 payload 的 `cycle_operation` 承载，应明确如何验证它属于本 H／controller／ordinal，而非复制一个未经核对的 deadline。

同时把新 request／observe modes 的窗口分类写明：当前 `training_execution_protocol.py:21–24,288–315,349–364` 只有 `CYCLE_WORK_MODES` 才允许并消费 compute∩window；只加入草案第 47 行明确写的 `CYCLE_CANDIDATE_MODES` 会使带 bootstrap 的新 mode 被拒绝，或使不带 bootstrap 的 mode 落入 total 分支。两新普通 mode 应明确接入所需的同一工作窗口规则，不能用旧 observation 分支只返回 bootstrap remaining。

**验证要求：** 沿现有 S/H fault 接缝，在异步检查之后、锁内最后同步验证期间阻塞到操作窗口已过但原 compute 仍有余量；允许解除阻塞后 H 获得一次运行机会，核实没有新 request publication／launch。另验证两 mode 在 compute／control／cold 三者分别最短时使用同一不可续期窗口。此项是应补的设计／后续行为证据，本次未运行。

### R2 — P2：submitted 到唯一 request 活动之间缺少明确的就绪等待分支

**位置：** execution 草案第 45、69、71–73、87、111–114 行；runtime 草案第 19 行。

草案最小序列在原 submitted／精确 run 确认后进入一次 request 活动，之后只 observe；request H 却要求实际 runtime 与 native 都已 QUEUED。尚未明确 Workflow 应先用哪些 facts 等待到这一条件，或收到 `request_outcome=not_attempted` 后如何处置尚未请求的正常候选。

**可达情景：** 原 `_Submission.dispatch` 在 start RPC 返回后立即保存 receipt（`reference_training_submission.py:284–288`），这不等待子 Workflow 的 job 创建。原 `ExperimentWorkflow` 从 INITIALIZING 进入 SUBMITTING，依次等待 `submit_or_lookup` 与首次 `poll_job` 后才把 phase 设为 QUEUED（原 `perf_temporal/workflow.py:32,113–122`）。因此正常活动排队即可得到 submitted，但 phase=SUBMITTING／native request 尚不存在。按草案字面序列调度唯一 request 后，它正确地不写请求；若之后永远只观察，原预算根会一直等待 request 到耗尽，首轮正常执行无法完成。若临时重新调度 request，则又需要区分“已不明请求”与“确知尚未尝试”，不能凭 request 文件 absence 重新授机会。

**最小修订：** 固定一个 history 可表达的首轮消费分支：在尚未调度唯一 request 活动时，submitted 只允许继续观察；只有同一已认证 run 的 runtime `terminal=false / phase=QUEUED / exact job`、native `QUEUED / same job`，以及无既有 execution、预算与父阻断事实符合要求，才调度该一次 request 活动。SUBMITTING／native 尚未存在在原观察计数和预算内等待，明确终态／身份冲突则停止或对账。request 一经调度而结果不明，仍按原要求只观察，不以 absence 再请求。无需新增 ledger；“是否已调度”归原 Workflow history。若选择收到明确 not_attempted 后允许再调度，应另行写清它与 unknown 的权限差别，不能留给实施临时决定。

**验证要求：** 后继消费证明须在真实 start receipt 已保存时延迟原 job 创建／首次 poll，确认消费者先观察、仅在双 QUEUED 后调度一次 request；另覆盖 request 活动发布前丢 completion 后即使文件不存在也只观察。本片的临时测试 Workflow可以验证活动事实，正式 sandbox/history 分支仍留 c1c，不提前宣称已验。

## 已闭合的设计点与维护性判断

六字段输入继续绑定冻结授权；SDK info、namespace、原父 started history／memo／first run 与 receipt 分别核对，未把业务自述 source 当认证。schema2 actor 可由原授权交给 `Execution.request`，原 check 本来就从同一授权选 actor；确认所需 revision／intent／run／native raw SHA 均有真实原件 owner。现有请求 gate 因而可复用，R1 只要求把新窗口接进该 owner。

request unknown 后只观察可由 history 保存唯一调度事实，不需另立 offer 或 request-attempt ledger；已有 request／launch／部分链保留原机会消耗，launch 和 reaper 仍由原预算根拥有。它不会因新的短 H 退出而被重新创建。执行事实与 `observed` 分离，未授予接受或后继许可。

Temporal status／phase 的真实 producer 是 `reference_training_runtime.observe:126–144`：RUNNING 查询原 Status，COMPLETED 读取固定 run Outcome，其他终态返回 NEEDS_RECONCILIATION。native 状态来自 `LocalTrainingAdapter.poll_job:146–153` 的原 Job／binding；durable stopped 来自 `ExecutionRecords.observe:908–933` 的同链同步／重读。草案把三者分别投影是合理的；不能在实现时把 runtime 顶层 state、phase、native state 合并成一个“执行状态”。c1d 的 accepted archive／evidence／rounds 仍明确另交付，当前 facts 没有接受证据不构成本片缺陷。

新活动使用独立 v2 名称与结果，保留旧四活动封套；原 stdlib protocol、可选 SDK 工厂、被 source-pin 的 worker 与 Execution 是合适的变更点。单调用局部 H 算法有内聚职责，不需要 manager、缓存或通用 DTO 框架。core 不装 SDK 的方向保持；实际 optional-import／安装／sandbox 兼容性仍待产品验收。

一项非阻断文字修正：第 66 行称 `source_operation_id` 可在 operations 找 ref，但第 107 行允许它指向 cold 操作，而 cold ref 按旧封套放在 inspection。应写为在 inspection 或 operations 中匹配同一操作身份，避免后继消费者在合法冷结果上拒绝事实。

## 实际检查与未验边界

本次执行只读 Git 身份／状态检查、`rg` 定位、带行号的文档与源码阅读；唯一写入为本报告。产品树初查 clean；结束前观察到 `tests/test_training_submission.py` 有并行工作改动，该测试差异未纳入本设计审查，未更改它。未运行服务、安装依赖／包、执行测试、发起训练、修改方案／产品、提交或推送。

以上 findings 是静态可达路径推理，尚无本次运行反例；报告未将其写成已复现故障。前片的真实 Temporal、包或测试证据只作为边界背景，没有认证新活动、正式总 Workflow、GPU／ML 质量或后继接受。修订两项后由主控提供具体新草案复审；实施必须另取得 E0–E7 适用证据，c1c／c1d 验收仍分别保留。

## r2 同 reviewer 复核

日期：2026-11-16。同一独立 reviewer 按主控回交的实际 r2 文本复核，未用修订说明代替阅读。准确 execution 草案 raw SHA-256 为 `ba481568fd4b29948b43f78ef1cc3e03c04d06f987289b9df6f8e86460271aaa`；runtime 草案为 `7c3c7f51be7e3ef887071a8f18f8a457ea780f8f5c8212123115a5261802bd19`。

**最新设计结论：需求轴 approve／开放 0；可维护性轴 approve／开放 0。** 原首次审查结论保留其历史范围，以下关闭仅指设计，不代表产品已经修复或通过运行验收。

- **R1 设计关闭。** r2 第 49 行明确两新普通 mode 同时进入 `CYCLE_CANDIDATE_MODES` 与 `CYCLE_WORK_MODES`，由原 validator 核 bootstrap，remaining 消费 compute∩固定 window；第 90、156 行明确通过原 payload 交完整已认证 operation，由原 owner 核 request action／attempt、本 H／父身份、controller／ordinal／候选 intent，并在锁内同步读取之后、实际 publish 前及同步后重算同一 BOOT/window。它已补上原先仅依赖 coroutine timeout 与 S 监管的缺口，旧人工确认和原 root admit 语义分别保留。不可中断 OS 调用晚返回被明确归 unknown、保留原件且不重发，没有冒称及时完成。第 169 行将“同步读取过窗、compute 仍正、允许 H 继续一次”的反例和三种最短窗口验证固定为后续验收。
- **R2 设计关闭。** r2 第 47、133 行明确 submitted 仅允许继续观察，原 request 尚未调度时等待同 run 的 runtime queried／非终态／QUEUED、native QUEUED、同完整 binding／job 及其余原阻断条件；SUBMITTING／native request 未发布不消耗唯一 request 调度。history 一经记录调度，即使 not_attempted 或 request 文件不存在也只观察，不以 absence 重新授机会。第 167、174 行将 receipt 先到、迟 job／首次 poll 的活动事实验证和正式 c1c history 消费验证分别归位。
- **非阻断 ref 位置问题关闭。** r2 第 68 行已允许 `source_operation_id` 在 inspection 或 operations 中匹配同一 ref，覆盖 cold 基础投影。

复核继续认可原 owner 复用、六字段输入、v2 名称隔离、Temporal／native／durable stop 分开以及 unknown 不重发的设计。没有新增维护性 finding。正式 Workflow、接受／rounds／后继仍属后续交付，未因本次设计通过而开放。

本次仅重读 r2、核文档 raw SHA／Git 身份与前置候选差异摘要，追加本报告。主树仍为 `478c98891522930817fa7005a8ac96e408f37230`；产品树已前进至 `97a0bbfae9687c15927f1437a374cd070baf0a94`，该前置服务容量修复不在本次产品验收范围，原源码调查基线仍为 eedba08。未改产品／方案／PLAN，未运行服务、测试、安装或训练。E0–E7、新安装／真实服务和 c1c／c1d 所需证据仍待各实施片取得。
