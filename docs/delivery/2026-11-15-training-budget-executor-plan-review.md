# Q4.2b3 实施前独立计划审查

本报告按轮保留历史；**最新结论见末尾 r2 复核：需求／维护均 approve，开放 0／0。** 以下 r1 的身份、finding 与结论保持，不能作为当前开放状态读取。

日期：2026-11-15。审查者：`/root/training_budget_executor_plan_audit`，以 fresh-context 独立上下文开始；未参与计划编写或产品实施。授权仅为必要只读检查与本报告写入，未运行测试、安装、模型、训练、服务或外部操作。本报告审查计划可实施性，不是 b3 产品通过，也不重新验收 b2。

## 结论

- **需求合规：request-changes。** 开放阻塞 2 项：R1、R2。
- **可维护性：request-changes。** 开放阻塞 1 项：R1；它与需求轴为同一问题，不另计 finding。

当前计划正确保留原实验、提交／取消、训练器、比较门禁、归档、跟踪与人工 release 的权威；没有把六阶段 task 的 scope／model slots 充当训练授权。UTC／同 boot elapsed 的保守时钟、slot 不归还、已完成旧轮不统一 fence、专用进程 subreaper、SIGKILL／跨 boot／缺原件保留 unknown，以及容器权限边界均与原要求一致。B3.1／B3.2／B3.3 的拆分方向可保留，但下面两项须先固定，才能使各片独立可验，不能交给未来 c 补齐。

## 固定审查范围与身份

Git 分支为 `refactor/architecture-foundations`，HEAD 为 `6531967e6b6dd8d20ff5ad70d7ae3074c81aca35`。b2 尚有未提交产品／测试及待完成验收；逐项读取并核对其原 [r4 manifest](../../.ergora/checks/training-frozen-recovery/source-scope-r4.json)，完整 SHA256 为 `85bbfb9843fd680892e1bd7fce1381eb737e77b38d58be8eab99cafda2ac6f99`，其中七产品／三测试的当前字节、长度、SHA 与对应 `source-scope-r4/` 副本全部匹配。这里只固定计划所依赖的临时源码身份，不转授 b2 的测试、安装、自身模板或 CI 结果。实施仍须按计划换成 b2 实际发布身份，并遵守其前置门禁。

本次新文档固定为：

|文档|字节|SHA256|
|---|---:|---|
|[b3 计划](../plans/2026-11-15-training-budget-executor.md)|12617|`baa5f1670695d0853c15c39cfd074257f4a52ff82647699f0c7fb62760eb2d28`|
|[b3 交付](2026-11-15-training-budget-executor.md)|1281|`4fc5effd859fd5ea214e9f8e9b1b563fd148cc17f9c66ccfae8c28da470ff7c5`|

已读根与相关目录 `AGENTS.md`、`docs/PLAN.md` 当前检查点、[有界循环](../plans/2026-11-15-bounded-training-cycles.md)、[b1](../plans/2026-11-15-training-start-fence.md)、[b2](../plans/2026-11-15-training-frozen-recovery.md)、组件变更协议；按 `maintainable-project-delivery` 的 independent-review、`ergora-codebase-quality` 三份相关 reference 与 `codebase-design` 检查实际 owner、消费者、故障与验收 seam。

主要源码路径是 `training_cycles`／`training`／`registrations` → `reference._training_process` → `reference_training_submission`／`reference_training_context`／`reference_training_cancellation`，以及原 `ExperimentWorkflow`／`Activities` → `LocalTrainingAdapter` → `training_executor.process` → `Sandbox` → `process_job`。另外读了 `reference_budget`、`processes`、`stage_driver`、`reference_task_creation`、`reference_job_lifecycle` 及对应既有 training／budget／processes 测试中的相关情景；测试只作为接口和风险证据阅读，未执行。

## 阻塞 finding

### R1 · P1 · 从首次 start attempt 到 queued／executor 交接之间，没有明确的持续截止 owner

**位置：** [计划](../plans/2026-11-15-training-budget-executor.md) 第 29–30、46–48 行。B3.2 规定在 prepare／真正 attempt 前核原预算，并要求晚到 workflow 被 fence；B3.3 才定义“每个已排队 job 的专用 driver”。两者之间尚未说明哪个已存在、仍存活的 owner 会在截止时实际落下原 fence，以及谁承担交接前的取消和恢复。

**可达场景与源码：** 原 [training._submission](../../src/ergora/training.py) 第 254–271 行在两阶段调用后直接返回 receipt；[reference._training_process](../../src/ergora/reference.py) 第 428–441 行是一次调用期间的子进程，并不留下独立 deadline owner。远端 [ExperimentWorkflow](../../src/ergora/data/reference/platform/upstream/temporal/perf_temporal/workflow.py) 第 113–117 行随后才通过 activity 建 job；[Activities.submit_or_lookup](../../src/ergora/data/reference/platform/upstream/temporal/perf_temporal/activities.py) 第 29–54 行和 [LocalTrainingAdapter.create_job_if_absent](../../src/ergora/data/reference/platform/local/agent_platform/training.py) 第 123–144 行均不认识新训练预算，只会拒绝已经落盘的原 fence。

因此，start 在 compute deadline 前获回执、CLI 正常返回，而 activity 排队至 deadline 后才运行时，native request 仍可被创建；尚无 queued request，就无从启动计划中的 job driver。held RPC 跨过 deadline 也是同一空档。多做一次 preflight 或取消等待方不能补上它；既有 late-RPC 测试的 fence 来自另一次显式调用，不是自动截止机制。这个窗口不需要 SIGKILL、宿主权限缺失或异常重启就能发生。

**影响：** “截止后不创建新工作”和 B3.2 自身的晚到验收目前没有可落地的连续责任链；若把缺口留给 c，B3.2／B3.3 就不能按当前表格独立关闭。维护者也必须在 submission 与 driver 两处猜测谁持有同一 deadline，损害生命周期的 locality。

**最小修正：** 在计划中指定一个绑定同一训练授权的专用 owner，并在首 attempt gate／RPC 之前启动、确认其身份。它须独立于调用 CLI／activity，连续覆盖 RPC、等待 native request、queued 与实际 executor driver 交接，直到完成或清理；交接不得有无人持有截止责任的窗口。截止时沿原精确 fence／cancel owner 操作，不等待 in-flight submission 锁。可把尚未执行原 executor 的等待阶段放入同一专用生命周期，而无需建立候选调度器或第二实验状态表；若采用另一已验证 seam，须写出等价创建门禁和交接证据。明确这部分属于 B3.2，不能依赖 c。

**最小验收：** 从公开预算入口触发一次 accepted start，让 CLI 返回、native create 延迟到原 compute deadline 后，再放行原 activity；必须没有新增 request，原 slot／intent 保持。另以原 held-start 接缝证明 deadline 自动产生的精确 fence 先于迟到 native create 生效；控制 workflow 是否晚到另列，不声称其终态或进程停止。这些检查须由本片自己的证据完成。

### R2 · P2 · 首次 live admission 的计时起点与部分授权恢复顺序尚未固定

**位置：** [计划](../plans/2026-11-15-training-budget-executor.md) 第 28、37–40、59 行。计划要求首次授权重新核全部原 admission，并一次冻结时钟，但未规定哪一个先持久化，也未定义在检查到第 N 个候选时失败／丢回复后，同 ID 如何恢复尚未完成的授权。

**可达场景与源码：** 原 [training_cycles.create](../../src/ergora/training_cycles.py) 第 137–156 行先循环 `training.check_start`，最后才发布离线文件；它适合不授予执行的离线选择，不能直接沿用为有预算授权的顺序。[training.check_start](../../src/ergora/training.py) 第 114–123 行每次进入独立子进程；原 [preflight](../../src/ergora/reference_training_submission.py) 第 51–78 行包括记录、Git root／commit 与 comparator 检查。有效选择最多 32 个，原策略又允许很短的 wall。若先完成这些 live checks 再授权，检查已经可以超过整个 wall，随后仍取得一个满额新 deadline；若中途失败前没有原时钟记录，重试又会重新计时。这是普通慢 Git／存储或调用丢回复即可到达的情景。

**影响：** 用户的显式启动动作可能执行长时间未计入的准备／核验，且“同 ID／恢复不续时”的核心验收在部分失败时没有确定预期。既有离线 a2 不计时是已声明的合同，不应把这种顺序带入新的执行授权。

**最小修正：** 明确首次显式授权的不可变意图／原时钟先于全部昂贵 live admissions 持久化；输入、ID、当前 home／项目／登记来源先固定，未完成核验的记录不授予 prepare／dispatch／executor 权限。用匹配的完整 admission 完成记录区分 pending／ready。授权文件 fsync、所有 live checks、检查间等待和完成记录发布都消耗同一原时钟；部分失败／lost-ack 后读回同 ID 的原记录，不能删掉重授或重新 admit 后重开额度。新的字段／字节界／SHA 与 reader、writer 合同应随此顺序一起固定。

原 [reference_task_creation.prepare](../../src/ergora/reference_task_creation.py) 第 383–441 行已有“先保存原时钟，再开始昂贵工作，完成发布后再核期限”的机制参照；这里只能复用必要时钟／监督方式，不能把其 task scope、slots、工作目录或运行账本移作训练授权。

**最小验收：** 在首次和后续候选的原 admission 接缝注入耗时，使其跨过短原预算；核验不得在之后得到新的满额 deadline，也不得创建 start intent／attempt／native job。再保留一个已经落盘、只完成部分检查的同 ID 原件，恢复后核时钟与输入字节保持、未完成状态不授执行权；修复外部阻塞也不能重开原额度。无需为提示文字另立测试矩阵。

## 实施与验收的保留义务

以下是当前计划已接受的义务，不另列 finding，也不表示产品已经通过：

- B3.1 先固定新授权记录的 ID／版本、完整 source 与 registration 引用、control home／execution、候选顺序、原时刻、容量、普通文件规则和摘要用途；旧 `cycle-plan-v1` 继续只作离线输入。B3.2 要让原 prepare／dispatch／resume 都发现并核对已绑定的预算，不能只靠一次可省略的 CLI 参数；slot 与原 intent／attempt 的局部发布、崩溃和锁顺序须一并验收。
- 共享时钟只抽出 `reference_budget` 与训练 owner 两个真实消费者所需算法。原 task 文件形状、摘要、scope、policy、slots 和读回接口保持，原 budget suite 的兼容证据另跑，不借其历史通过。
- B3.3 的可行机制是专用 driver 监督调用原 `training_executor.process` 的子进程；原 Git、runner、archive、MLflow 均在该树中，Sandbox／process_job 的两个新 session 不能靠外层 killpg 覆盖。`processes.run(supervised=True)` 的 timeout 不执行截止，须实际 stop predicate；其 reap 可能耗时，不能在返回／匹配原停止记录前宣布完成。
- `reference_job_lifecycle.BudgetedJob` 已有专用 owner、supervise、停止 witness 与慢 fsync 后重核期限的机制可供对照，但其继承、task ledger、scope 与 receipt 属于 task，不能直接变成训练账本。训练记录应分别报告原 native result、控制面、实际回收、预算／取消与 unknown；native result 已存在不能代替 driver witness，迟到记录也不能冒称预算内成功。
- SIGKILL／driver 消失／跨 boot／缺 proc 保留 unknown，不自动重跑、不按名称或陈旧 PID 批量杀进程。没有可委派 cgroup 的容器边界已明确接受，无须为本片请求宿主权限。已完成旧轮与前后原件／可信质量／人工 release 保持，Kernel 专家继续在 v3 路径。
- 每个产品子片仍需自身固定源码、非 editable 安装、真实接口检查、自身原审查模板与 fresh-context 产品两轴审查。源码、SDK 替身、真实 Temporal、CPU、真实 GPU／训练质量分别记证；本报告没有把任何旧片结果转授 b3。

本次实际检查仅含文档、源码／测试阅读、Git 状态与身份，以及标准库只读字节／SHA 核对。未发现需要新建第二训练器、调度器、实验权威或插件框架的理由。R1／R2 修订后应由本 reviewer 对固定新版计划再核；通过后的结论也只限实施前合同。

## r2 同片独立复核：两轴 approve

日期：2026-11-15。由同一独立 reviewer 复核修订，不替换上述 r1 历史；未参与产品实施。本次需求合规 **approve／开放 0**，可维护性 **approve／开放 0**。R1、R2 在实施前合同层面关闭，未新增计划阻塞。

### 本轮固定输入与检查

|文档|字节|SHA256|
|---|---:|---|
|[计划 r2](../plans/2026-11-15-training-budget-executor.md)|17942|`831127e9aa6a5aad5d0f6fdc65f7cd3e4abf9f16c74203a4eb4d0233b81fe227`|
|[交付 r2](2026-11-15-training-budget-executor.md)|2047|`f49cec2f1b00aece44e3d5b6aeec471d3d4cc10b48b79eefba720fbd8624eef4`|

重新读了两份完整文档、Git 状态及当前检查点；HEAD 仍为 `6531967e6b6dd8d20ff5ad70d7ae3074c81aca35`。b2 原 r4 manifest 的 SHA 仍为 `85bbfb9843fd680892e1bd7fce1381eb737e77b38d58be8eab99cafda2ac6f99`，十文件当前字节再次全部匹配。补核了原 `reference_training_submission.fence`、`reference_training_cancellation` 和登记来源 reader，检验新增责任是否仍能落在已核 owner。未运行 suite、安装、模型、训练、服务或外部操作；只写本报告。

本轮最终身份包含第 50 行补明的预算 owner 本地 fence 接缝：复用原 adapter 的 `fence_and_lookup`，核本预算归属与完整原 Experiment／job／路径，不借原手工 `fence-start` 放宽 submitted 后的接管权限。该澄清与已核源码一致，没有新增权限或改变本轮结论。最终两文档及本报告的本地链接均已静态核对，无缺失。

### Finding 关闭依据

|原 finding|r2 的可核修正|处置|
|---|---|---|
|R1／P1：首次 RPC 至 queued／driver 交接没有连续截止 owner|计划第 29、46–52 行明确在首 attempt gate／RPC 前，必须已有核实身份、同授权、独立于调用 CLI／activity 的 owner；它在 receipt 后继续持有 RPC／等待 request／queued／executor 交接至完成或清理的责任，交接 ack 前原 owner 仍监管。deadline／取消由其自动持久化原精确 fence，不等待提交锁；有 run 后沿原取消 owner 处理控制面。accepted 调用先返回再延迟 native create、held RPC 跨截止两项均归 B3.2 自己验，不由测试另行手工 fence，也不依赖 c。|需求、维护两轴的同一阻塞关闭。由明确连续 owner 隐藏生命周期义务，没有新建候选调度器或第二实验权威。|
|R2／P2：首次 live admissions 未明确进入原时钟，部分失败可重新计时|计划第 28、37–38、68–72 行明确先保存原授权／时钟，再做全部昂贵 live checks；pending 不授 prepare／dispatch／executor 权限，完整 ready 后仍核来源与剩余预算。授权 fsync、各候选检查、等待和完成存储都消耗原时钟，慢 fsync 后再核截止。部分中断／lost-ack 的同 ID 只用原输入与原时钟，在原剩余时间内补只读核验，不能删记录重授。|需求阻塞关闭。短预算跨首次／后续检查与部分失败恢复现在都有可检验的预期。|

新增的持久合同还固定原 `cycle.json` 字节及 10 MB／32 候选上限、授权与 ready 各 1 MiB、原 bytes SHA 与 canonical SHA 的不同用途、普通文件／严格 JSON 和同 ID 冲突语义。第 41 行要求原 prepare／dispatch／resume 发现已绑定预算，缺来源不能退回无预算模式，消除了只靠可省略 CLI selector 的歧义。共享时钟仍仅服务两个真实消费者，旧 task 账本及 283 参考不变；专用 driver 的资源职责足以支持其独立进程位置，未引入单次转发模块的要求。

### 产品片仍须履行的具体证据

这些是已接受的实施义务，不是本轮开放 finding：

- **本地 fence 的实际接缝。** 原 `_Submission.fence` 第 191–192 行仍按手工合同拒绝首次对 submitted／rejected 状态新增 fence；原 `_Cancellation.prepare` 只冻结取消意图，远端 signal 也不能替代本地截止 fence。预算 owner 应在确认其原授权／实验归属后，沿已核原 `LocalTrainingAdapter.fence_and_lookup` 或等价的应用扩展 seam 落盘；不能直接调用原手工 `fence-start` 并假定 accepted 情景可用，也不能为此全局放宽手工接管权限。r2 的原 adapter／registry lock 合同允许这项局部接入，accepted／held 两项验收会直接检出错误实现。
- **每片完成边界。** B3.1 仍须完成 reader／writer／固定字段的同一合同和原 task 兼容；B3.2 固定 slot／原 intent／attempt 的发布与锁顺序、连续 owner 及无选择参数绕过；B3.3 才证明原 executor 全树、真实 setsid 后代与归档／跟踪停止。原 native result 及 Temporal 终态不能代替 driver 停止 witness，迟到存储不能冒称预算内成功。
- **独立证据归属。** b2 实际发布 Git 身份与自己的 CI 前置门禁仍须落实，未把其本地验收转授 b3。各产品子片仍需自己的固定源码、非 editable 安装、原模板与 fresh-context 产品审查；真实 Temporal、CPU、GPU／质量与容器权限边界继续分别记录。

本轮通过的是 **B3.0 实施前合同**。没有执行预算、没有实际派发／训练，也没有资源停止或自动循环完成主张。
