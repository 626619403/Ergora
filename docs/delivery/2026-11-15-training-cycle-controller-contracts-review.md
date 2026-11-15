# Q4.2c0.1 具体合同独立两轴审查

日期：2026-11-15。审查者：fresh-context 独立 agent `training_cycle_controller_contracts_audit`。本审查直接接收原始需求、固定 baseline、完整 tracked／untracked 范围与实际检查边界，未继承作者的实施对话。先读项目规则与原始范围，再检查[具体合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、真实源码及相邻消费者；准备审查的 approve 不作为本次具体设计的结论。

## 两轴结论与阻塞项

|轴|固定 r1 结论|阻塞 finding|
|---|---|---|
|需求正确性|request-changes|R1：stop Worker 的 queue／配额没有固定与原阻塞 adapter 的进程及 event loop 边界|
|维护性|request-changes|同一 R1：取消通路仍可能隐式依赖原实验 Worker 的同步 I/O；没有另加抽象／复用 finding|

R1 是一个跨两轴的设计问题，不是两项独立缺陷。当前不放行 c0.1 具体设计进入实施；修订该边界及交付顺序后可由本 reviewer 复审。除此之外，在下述固定范围内未发现其他阻塞设计问题。本报告不认证控制器产品、旧 c2 的新验收、在途 CI、真实训练／GPU／质量或收益。

### R1（P2，阻塞）：独立 queue／Worker 配额不能隔离同进程阻塞

**位置。** 合同[源码决策表](../plans/2026-11-15-training-cycle-controller-contracts.md#L16)、[Worker 注册](../plans/2026-11-15-training-cycle-controller-contracts.md#L78)、[活动边界](../plans/2026-11-15-training-cycle-controller-contracts.md#L101)与[实施分片](../plans/2026-11-15-training-cycle-controller-contracts.md#L147)。合同已要求新的控制活动通过独立操作进程运行，并给 stop queue 单独 Worker／并发配额；但尚未固定它们与原 ExperimentWorkflow Activities 的进程／event loop 关系。表中又将“新 queue 的独立 stop 配额”留到 c2，晚于 c1 总 Workflow 与取消合同。

**源码证据。** 当前[主入口](../../src/ergora/reference_training_worker.py#L97)通过一个 `asyncio.run(_serve())` 运行；[`_serve`](../../src/ergora/reference_training_worker.py#L80)注册 `Activities(adapter)`。原 [`submit_or_lookup`](../../src/ergora/data/reference/platform/upstream/temporal/perf_temporal/activities.py#L29)最终 await [`BudgetAdapter.create_job_if_absent`](../../src/ergora/reference_training_worker.py#L27)，后者直接 await 原 native create；该方法在 [`registry_lock`](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L137)中同步执行阻塞 `fcntl.flock`，并在同一 async 调用链读取／写入文件。现有 lookup gate 还构造 [`State`](../../src/ergora/reference_training_worker.py#L42)，其 schema lock 也是同步路径。不同 Worker 实例的 activity slot 配额不会使这些同步调用让出同一个 Python event loop。

**可达场景与后果。** 若按 r1 在同一 `_serve` loop 中增设总 Workflow 和独立 stop queue 的 Worker，另一进程持原 registry lock 时，一个已排队 `submit_or_lookup` 即可阻塞该 loop。此时经 Temporal SDK 请求父 cancellation，合同第 3 节承诺的 catch → stop queue → 本地 stop writer／精确 owner 通知无法被消费；增加 stop slot 也无效。原 c2 独立 owner 仍可按墙钟停止，但这不能证明父取消已及时发布拒绝标记或通知活动执行。普通新控制活动移入 helper 只移走了新活动的 I/O，未移走原实验 Activities 的这条阻塞链。

**最小修正。** 固定一个与原 `training-budget-worker` 分开的 controller Worker 进程及 event loop：原进程继续持有原 ExperimentWorkflow 和原 adapter；新进程注册总 Workflow、把所有控制活动的文件／锁／等待放在受监管操作进程，并在其非阻塞 loop 上给 stop queue 保留独立 Worker 配额。沿现有 `reference_training_worker`／`reference`／`services` owner 增补真实服务入口即可，无需另造调度器或修改原 executor／reaper。将该执行边界、queue 注册与 stop 配额纳入 **c1 开放自动派发之前** 的交付，c2 只补公共 CLI／HTTP／服务操作交互。等效方案可以隔离原全部阻塞 Activities，但须列出实际覆盖的完整调用链，不能只写“独立 Worker”。

**后续实际验收。** 在原实验 Worker 的 registry gate 真实持锁，并分别让新控制 helper 的文件读取／fsync 阻塞；确认经 SDK 的父 cancellation 仍能被新 loop 处理，stop writer 与其他精确 owner 通知并行推进。保持受阻 gate，核晚到／已排队活动不越过已可见 stop，再释放锁对账原记录；分别报告 stop durable、drained 与原 stopped chain，不用最后墙钟回收代替取消通路通过。这些是实施后的检查，本次未运行。

## 固定输入与直接核对

Git HEAD／源码 baseline 为 `ac86043d9e11983750bf63b90c0dfcbeea05ea41`，分支为 `refactor/architecture-foundations`。独立逐件核实以下五份设计输入与 `design-r1/scope/` 的完整 bytes 相同：

|文件|字节数|SHA256|
|---|---:|---|
|`docs/plans/2026-11-15-training-cycle-controller-contracts.md`|24,432|`d2288eb2615396505fd6e8c0ed3c7796df316ff37732e2d32fd72c7839e54d38`|
|`docs/plans/2026-11-15-training-cycle-controller.md`|9,704|`347af594a6807523eeca8ad626b41a0f4890a8d12297cd68ae5c65bf0bcdc425`|
|`docs/delivery/2026-11-15-training-cycle-controller.md`|2,849|`4b77ab67e6b95c5f3af51ca9d65c3c9d456a7fea2ded3077b284689757f6cf13`|
|`docs/delivery/2026-11-15-training-cycle-controller-plan-review.md`|12,669|`688dfc1d4136c578b41c4e35a09261abaade13be6595729ac1663afbaecc4f6f`|
|`docs/PLAN.md`|58,196|`425c3c7932f93ab7df07a1090eb528a699f8d7db28bd1680c57797ce25aed772`|

已读根与源码目录 `AGENTS.md`、[组件变更协议](../architecture/component-change-protocols.md)及总计划，应用 `maintainable-project-delivery` 的 independent-review brief 和 `ergora-codebase-quality` 的 repository-style／module-design／test-seams 三份 reference。没有要求 Python 文档片运行不相关 linter 或训练 suite；当前 `pyproject.toml` 配置 pytest，未以其他仓库规范生成风格 finding。

对 `contracts-r1/source-manifest.json` 内 30 份产品源码／schema／native delta 的完整 414,552B，逐份重算 SHA，并比较当前文件、作者快照和 `git show ac86043:<path>`，三者完全相同。清单原 SHA256 为 `18c3ef33ccddee87b369b0ddf4996cba946d802e365e1d81a40b2e5eb4ffb393`。直接跟踪以下生产调用及格式，不把完整 bytes 身份相同等同于每行语义都已动态验收：

|核对项|原源码与设计判断|
|---|---|
|明确执行同意与记录身份|`training_cycles._authorization`／`authorize` 确实重建 schema1 且在 live checks 前占用 ID、冻结 clock；普通 ready 不含自动执行同意。出生式 schema2、同 ID 不升级、总 attempt-before-send、固定 input／memo／run 和每轮 controller binding 的方向可实施；原 `_Submission.load`／`prepare_binding`／`validate_binding` 的严格集合必须同步走明确新分支，不能只扩 UI 字段。|
|旧链与两个解释器|`training_execution_protocol.owner_record`／`ExecutionRecords`／`validate_context` 的 exact 字段、capability 和 `GATE_SOURCES` 集合真实存在。保留 key 集合和旧分支、只在新 owner 冻结新 source hash，离线 chain 不以当前 source 决定可读，符合原合同。新的共享父记录算法须使用纯 stdlib 子集；不能让应用侧复用当前会导入 native `dev_platform.contracts` 的 `_match`，也不能把 `State`／SDK 带入 native gate。合同已给出这一约束，产品接线尚待验。|
|父锁与 stop 线性化|原 submission 有原锁与唯一 attempt，worker lookup 在原 registry lock 内，版本化 native delta 的 admit callback 在原 executor lock 内且早于 Git／runner。父共享许可覆盖动作、stop 可见先拒绝、独立 writer／drain、父→原锁的单向顺序，与保留唯一 launch／reaper 相容。drain 与 stopped chain 分列正确；R1 是使这些用例能够被调度的前置问题。|
|测量接受及人工 release|原 `BudgetedStart.completion` 仅核 native terminal／gate／managed durable stop；原 Workflow 另有 GATING、AWAITING_RELEASE 和终态 outcome。合同联合核 receipt／history／memo、job／binding、accepted archive、实际 phase 和 durable stopped；只处理活动／未确认轮、保留已接受轮的 release 窗口，避免总结束统一取消旧轮。原 `Status`／`Outcome` 提供所需 binding、job、evidence SHA 或 report URI。|
|可信分类与统计|`perfctl.gate` 只在重算 comparison PASS 且原证明通过后产生 accepted gate；原 executor 可将失败合并为文本。合同不从 summary／未认证 runner 输出推断 quality failure 或 no-benefit，保留原 performance、quality_assessment 与 limitation，符合现格式能力。原 comparator 的 fixed-sample 与 multiple-search 限制也被保留。|
|容量与原结果留存|cycle／round schema 的 32 项界和 `training_rounds.create` 完整嵌入四类观察、序列化后核 10 MB 属实。原注释可直接映射；previous prefix／raw SHA、索引超限停止、项目漂移拒绝并保留原结果，不需要第二实验库。总 history 单独看实际 size／length，32 KiB 身份引用与原大文件分离，方向完整；实际编码／边界必须另验，不能由此宣称可完成 32 轮。|
|所有权与改动范围|新应用用例留在 `training_cycles`；父记录／许可由 application 与 native 两个真实消费者共享，放入已 pin 的 stdlib owner 有具体理由。新 Workflow 与活动是 SDK 注册接缝，不要求虚构多个生产 caller；无需建立泛型组件 ABC。原六阶段、实验／比较／批准 owner、kernel 专家路径和 283 冻结参考均未被本设计替换。|

本次还逐字读取原 native service 的 Temporal argv，核保存的 CLI 1.9.1／Server 1.32.0 版本输出与官方 v1.32.0 常量原件。两份官方来源的保存长度／SHA 与 metadata 一致，常量确有 2 MiB blob、2 MiB memo、50 MiB／51,200 events history error 和 10 MiB／10,240 events warning。这里只确认既存来源和默认值，没有运行 binary、启动新 server、探测其他部署配置或发起新网络请求。SDK history length／size 方法存在属于传入的实际检查；本 reviewer 未安装或加载该 SDK，真实 history 预算留给实施验收。

## 实际检查、证据与剩余验收

独立只读检查通过：HEAD／分支／status／最近提交、上述 30 份三方原件身份、五份固定设计身份、当前 tracked diff 与保存 `tracked.diff` 完全相同，及 `src`／`tests`／`scripts`／`.github`／`pyproject.toml` 相对 baseline diff 为空。`git diff --check` 通过；五份输入共 190 个本地链接目标存在，其中四份 controller 文档为 47 个，不含总计划的 143 个。该检查不认证锚点或外部 URL 可达。

独立检查脚本和结果只写入 ignored `.ergora/checks/training-cycle-controller/contracts-audit/`：`verify-inputs-r1.py`、`identity-checks-r1.json`、`local-links-r1.json`、`status-before-report.txt`。身份结果为 9,343B／SHA256 `6b7e262dd73bae9f05ad9d0dc98529c791e1bf493117d1947966bca037d0eda8`。唯一公开写入为本报告，没有修改产品、测试、依赖、Git、其他 docs 或外部系统。

R1 修订通过后仍须分别完成原计划的产品片：新旧授权／旧链、重复与部分持久化、最后 gate／attempt／ack 交错、独立 stop fan-out、完整总投递和 lost reply 对账、真实两轮与实际 phase／release、索引超限／项目漂移、SDK payload／history 和 worker／server 重启；再按各候选完成安装、适用检查、自身模板、独立产品审查、普通发布与自己的 CI。设计 approve 不能替代这些证据。前置 c2 固定发布及其 CI 由原 reviewer 续核，本审不替其终核。新可信 CPU 示例尚未实施，真实 ML／GPU／质量／收益及完整其他外部能力继续开放。

## 固定 r2 复审：两轴 approve，R1 在设计层关闭

本节由原独立 reviewer 追加；上文 r1 的 request-changes、场景、检查边界及原件身份全部保留。上文“当前”仅指固定 r1，最新具体设计结论以本节为准。

|轴|固定 r2 设计结论|开放阻塞|
|---|---|---|
|需求正确性|approve|0；R1 的进程／loop 边界及交付顺序已固定|
|维护性|approve|0；仍沿原 worker、reference、services owner，未引入第二调度器或执行器|

复审固定输入为 `design-r2/scope.json` 及其五份完整快照，baseline／HEAD 仍是 `ac86043d9e11983750bf63b90c0dfcbeea05ea41`。清单 SHA256 为 `cdfa1d0e5405a467d292e1341a553b5d88b540e1eb94127c8fccc753212f673c`；当前五文件逐份与冻结 r2 相同。与 r1 比较仅有两份设计输入改变：

|文件|r2 字节数|r2 SHA256|
|---|---:|---|
|`docs/plans/2026-11-15-training-cycle-controller-contracts.md`|26,401|`8c104bda13bb6cc7c97941330f9f9fb72a044d683d8ffd958085fda36d26091b`|
|`docs/delivery/2026-11-15-training-cycle-controller.md`|3,823|`47bbe91b37007160c5750a2f711ecaa004eb2e4c4a1c8f8b8a1653dee5fcb902`|

已直接读两份完整 r1→r2 diff，并重读实际 `_serve`／`BudgetAdapter`、`reference.training_budget_worker_command` 与 `services._prepare` 接缝。修订将 R1 的两项义务落到具体 owner 与验收顺序：

- 合同第 4 节的[新进程入口](../plans/2026-11-15-training-cycle-controller-contracts.md#L78)明确由 `reference_training_worker` 沿 `reference`／`services` 启动独立 `training-cycle-worker`，原 `training-budget-worker` 的 PID／`asyncio.run(_serve())`／原阻塞 adapter 保留；禁止把 controller／stop Worker 注册到原 loop。原 registry／State／文件阻塞因此不会以共用 event loop 的方式挡住新取消消费者。
- [新 loop 的义务](../plans/2026-11-15-training-cycle-controller-contracts.md#L80)覆盖全部新活动的业务文件、锁、同步 RPC 入口与等待，loop 只做异步进程／管道监管；普通活动与 stop Worker 各有配额。stop writer 和各 owner 通知仍分别隔离，不能用一个 helper 先等待写盘再开始通知，保留了原 R1 要保护的并行 fan-out。
- [c1.0](../plans/2026-11-15-training-cycle-controller-contracts.md#L152)与 c1.1 一起交付，明确“未通过不开放自动派发”，并要求两个真实 PID／loop／queue、原 registry／State／文件阻塞及新 helper 读／fsync 阻塞下的 SDK 父取消验收。[c2](../plans/2026-11-15-training-cycle-controller-contracts.md#L155)只补公共交互，消除了先开放循环、后补 stop 执行边界的顺序缺口。

这组修订足以关闭 **设计层** R1；它没有宣称新入口已经存在或真实持锁取消已通过。完整 diff 未改原授权／clock／旧链版本、唯一 start／launch、每轮身份、accepted archive／实际 phase／人工 release、分类及容量合同，r1 对这些范围的非阻塞判断保持。新的进程入口拥有实际 SDK 注册与隔离职责，复用现有 bootstrap／服务 owner 有具体用途，无需为它另立通用调度抽象。

独立重新核 30 份产品输入的当前 bytes＝原快照＝baseline，仍为 414,552B；追加前核原报告完整 12,178B／SHA256 `da3ff58387b32be95ae0d6d42aab71ba2a6ef5f0d103532f2eac7a600cdafb48`，与保存 r1 原件完全相同。五份 r2 文档的 191 个本地链接目标存在，未认证锚点或外部 URL。复审脚本、完整两份 diff、状态与结果保存于原 ignored 审计目录；`identity-checks-r2.json` 为 22,731B／SHA256 `be943c3428152b09385e2f563f7666c1426f4d5c6753fa047eaa2fe422fbf425`。Q5.2a 测试维护的独立准备文档不在本片设计输入，也没有借本次结论认证其测试修改或验收。

本轮只做文档／源码／身份及静态检查，没有修改产品或测试、安装依赖、启动服务、运行 SDK 取消／训练、提交／推送或外部写入。**两轴 approve 仅放行该固定 c0.1 具体设计**；须先闭合原计划的前置发布／CI 门禁，再按片实施。c1.0 的实际进程隔离、阻塞下取消与并行通知、原 gate 竞态和其他产品验收仍全部开放，不能将本次设计复审写成运行通过。原 r1 finding 及所有未验范围保持其历史身份。

复审收尾的只读范围检查已观察到独立 `tests/test_training_submission.py` 工作树差异；它属于 Q5.2a，不属于以上五份 r2 输入。本节只记录该范围分离，不审查或认证其行为。`src`／`scripts`／`.github`／`pyproject.toml` 仍无差异，30 份产品来源与 r2 五份设计身份保持，因此没有把全仓工作树误称为无产品／测试差异。
