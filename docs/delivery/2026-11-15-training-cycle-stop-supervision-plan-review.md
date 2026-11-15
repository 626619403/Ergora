# Q4.2c0.2b2：停止监管接口的独立设计审查

日期：2026-11-15。审查者为新的 fresh-context reviewer，按原始[控制器合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、[b0 合同](../plans/2026-11-15-training-cycle-gates.md)和实际源码审查[监管接口草案](../plans/2026-11-15-training-cycle-stop-supervision.md)。本次只审设计，不是 b2a／b2b 实现或自动循环验收；b0 通过没有转授本接口。

**需求符合性：request-changes，开放 R1 一项。维护性：approve，开放维护性 finding 0 项。** asyncio 父侧、唯一原 reaper 和最小两帧 codec 的职责划分有源码依据，无须抽取通用 selector driver。产品实施前须补全冷启动 inspect 的时限／原 clock 交接接口；b1 完成后仍须按实际消费接口复核。本结论不关闭前置 a 片 CI 或任何产品门禁。

## 固定范围与身份

产品基线／当前 HEAD 均为 `07cbae2227d60c849df6ac96b4f96d3f71d80d43`，分支 `refactor/architecture-foundations`。独立重算 `.ergora/checks/training-cycle-gates/supervision-design-r1.json` 的全部 10 个文件，长度和 SHA256 全部相同；其中七份产品源码与该基线的 Git blob 逐字相同。

|设计文件|字节数|SHA256|
|---|---:|---|
|监管接口草案|7,934|`f0031d8718c9733f0877c26b3ead5493c875153bb5a6d4d3175ff477e2861d40`|
|b0–b3 计划|11,183|`b4dbedfc81c712d8aa8602f0c1631388ec5184e1c459aa7e7a582770e7161db5`|
|b 片交付|3,084|`a89dabb871e11b573af6b88465a5845ceb38b3e494ff80a8a6327da16fa37d64`|

七份清单源码是 `training_cycles.py`、`training_execution_protocol.py`、`reference_training_budget.py`、`reference_training_worker.py`、`processes.py`、`reference_task_export.py`、`reference_training_context.py`。另沿 `budget_clock`、`reference_training_execution`、submission、cancellation、`reference` 的启动／离线读取、registration、State、严格 JSON parser、现有测试接缝和架构边界读取相邻调用。`src/`、`scripts/`、`.github/`、`pyproject.toml` 相对基线无差异，也无 untracked 产品文件。

已读根及源码 `AGENTS.md`、当前 PLAN／活动交付、组件变更协议，以及 maintainable-project-delivery／ergora-codebase-quality 的独立审查、模块职责、仓库风格和测试接缝参考。本次仅写本报告；没有修改其他记录。

## R1（P2，需求）：冷启动 inspect 的 deadline 尚未成为可执行的接口合同

**位置：草案第 17–23、29 行。** 第 21 行要求 S 在任何 H 产生前安装“原父身份／clock watchdog”；第 29 行又规定先由 inspect 取得原 authorization／policy。第 17 行列出的 operation 身份没有 clock，第 29 行的“有限的调用观察窗口”没有定义输入字段、起点、deadline 或传给 S 的方式。对于公共本地 stop 的冷调用，不能先假定父侧已有已核 snapshot。

这不是原接口能够隐含补齐的能力。现有 `_BudgetPhase.expired` 依赖完整 cached context（[budget 第 82–86 行](../../src/ergora/reference_training_budget.py#L82)），`BudgetedStart.remaining` 从该 context 取原 authorization clock 和 policy（[第 428–432 行](../../src/ergora/reference_training_budget.py#L428)）；原 S 已在收到此 context 后才建立 `stopped()` callback（[第 236–249 行](../../src/ergora/reference_training_budget.py#L236)）。新冷 inspect 正是在解决“还没有这些已核数据”的情况。并且原 [processes 第 162–175 行](../../src/ergora/processes.py#L162)的 supervised 分支只看 `stop_requested()`，不会因传入有限 `timeout` 而停止；`process.wait(timeout=timeout)` 属于非 supervised 分支。

**可达情形及后果：** 冷 stop 只持 cycle 的完整身份，inspect H 在读取 authorization／cycle 原件时阻塞。此时 S 没有原 clock，按草案不能形成所要求的原 clock callback；仅把“有限窗口”作为 `processes.run` 的 timeout 参数也不会触发停止。若依赖父侧取消而没有明确 bootstrap deadline，初始化可能无限等候，后面的 writer／通知分支不会启动。这里可以如实返回身份未识别的 unknown，但仍须明确何时请求收尾；不能把此缺口归为已经进入原 reaper 后不可避免的 OS 回收延迟。

**最小修正：** 在现有 worker 内明确两类请求的参数／校验和生命周期，不新增预算 owner 或重新授权：

1. 冷 `inspect` 带调用开始前固定的有限 observation deadline，由父侧和 S 的 `stop_requested` 实际驱动；该窗口只允许读取，不执行 start、launch 或通知。说明 cancellation／deadline 在请求未完整交付、S 已创建和 H 已启动时各由哪个已保留的 task／handle 负责收尾。
2. inspect 返回的轻量 snapshot 明确携带完整原 clock／policy，并绑定该次核过的 input raw SHA 和 authorization canonical SHA。后续各 operation 把同一 snapshot 作为请求 payload；S 在任何 H 产生前用原 `budget_clock.validate/remaining` 建立 watchdog。实际计算剩余值必须包含 inspect 已耗时间；原 total 非正或 clock 不可用时不启动后继分支，不产生新 clock。
3. 说明 bootstrap 超时与原 total 耗尽都不构成 stopped 证明；沿现有匹配帧／reap规则收尾并保留 unknown 和实际延迟。复用 c1 snapshot 时走同样的完整绑定，不能以调用者任意延后的 deadline 续权。

设计复审可核上述字段、起点及调用顺序，不需要现在运行产品测试。b2b 产品验收须包含无 cached snapshot 的冷 inspect 原件阻塞，以及 inspect 返回时原 total 已耗尽两条真实路径；不能只验 warm context 的 watchdog。

## 已有源码支持的设计决定

- **asyncio 父侧足够承担此处 transport。** 原 `_BudgetPhase.start/poll/finish` 是同步 owner 的 selector pump（budget 第 121–210 行），而新 cycle 入口按合同拥有自己的 asyncio loop。使用 stdlib 异步子进程和独立 stdin／stdout／stderr／wait task 可以让已识别 peer 各自推进，无须让 cycle 继承预算目录、mode 或虚构 BudgetedStart。`shield` 必须包住仍可取回实际结果的 spawn task；草案保留 handle 并等待原 S 收尾的要求正确。它不把 Python future 的取消视为停止证明，也不承诺消除 OS 进程创建／回收本身的不可控尾部。
- **codec 有两个真实消费 owner。** 现有 `receive`（budget 第 88–119 行）只处理有限 UTF-8 JSON、身份／顺序、完整 process observation 和分帧容量，适合留在现有 stdlib protocol；budget 和新的 worker operation 分别是生产消费位置。protocol 的 `decode`（第 82–104 行）已有重复 key、非有限数和顶层对象拒绝，不需 parser 依赖。codec 不应取得 clock、spawn、取消或业务存储职责。b2a 仍须保留 budget 完整帧容量（65,536B／2 MiB）、输出路径校验、两帧顺序，以及 `finish` 的完整请求传送、exit code、空余 buffer、原时限成功条件；本设计审查没有验证迁移后的行为。
- **S／H 边界和停止后顺序成立。** 原 `processes.run(supervised=True)` 在 callback 预停时不会启动 H（processes 第 162 行），并在 finally 中 kill／wait／reap 后才返回（第 182–200 行）。原 budget 随后先发 stopped，再直接观察／存储结果（第 270–281 行）。草案要求 S 先装信号／watchdog、匹配 stopped 后不再 spawn、该帧前只 TERM／等待原 reap、该帧后原 total 尽时才 kill S，保持了这条边界。后继验收应保留创建中取消、H 前预停、回收中取消和 stopped 后结果阻塞的状态转换。
- **通知、writer、排空和原链观察的隔离符合原要求。** 草案第 31–35 行将 writer fsync、每个 ordinal 的原 intent／owner 查找、drain 和执行链观察分别放在 H，不把它们串行放入父 loop。`CycleAdmission` 自身明确为可能阻塞的存储 owner（protocol 第 204–209 行）；`stop_controller` 也明确为 storage-only（cycles 第 497–503 行），不能直接进入 live SDK loop。`processes.notify_identity`（第 29–53 行）提供 pidfd 与完整 PID／start_ticks／boot_id 再核，适合精确通知。
- **旧 owner 清理与新执行准入分开是必要约束。** 草案明确核原 cycle／ordinal、完整 controller binding、原 start intent／authorization SHA，而不把当前 source／project revision／SDK可用性作为精确清理前提。原 `owner_record`、`owner_active` 可用于结构／进程观察；不能在新通知路径误用 `require_active`、`Execution.check` 或 `validate_context` 来授权清理：后者即使 `live=False` 仍会执行 `validate_sources`（protocol 第 575 行）。离线执行链可直接复用 `ExecutionRecords.load/observe(durable=True)`，或现有 bundled SDK-free reader；公共 `reference.training_execution` 另有可失败的 current-sources 查询，不应成为通知的前置步骤。b1 尚未实现 controller binding，故这些具体消费签名仍须在 b1 后复核。
- **保留人工 release 和事实分列有实际依据。** 原 fence helper 先查 completion 再 fence（budget 第 559–573 行），`Execution.drive` 保留 monitor completed 分支（第 168–180 行）；草案不统一调用 Temporal cancel、不补造 stopped 链。此前已接受测量轮的人工 release、原 start／launch 单次机会、native source key 集合与 kernel 专家均保持。父 stop 可见、持久、许可 drained、通知结果和原执行链 executor stop 分别返回，不能由 operation stopped 帧推导训练子树已停。

## 检查、限制与后续门禁

完成静态源码／调用顺序检查、清单 10 文件长度／SHA256 核对、七份源码与基线 blob 比较、清单九个本地链接目标检查，以及 `git diff --check BASELINE -- docs`；均符合所述范围。只读取现有测试，未执行测试、安装、服务、Temporal RPC、网络、训练或 GPU；没有提交或推送。没有以这些静态检查认证新的产品行为或重验 283 冻结文件。

交接提供的 a 片官方 CI 身份为 run `43693023635`／attempt 1，七个 job success、Windows regression 仍运行，尚无终态。本次未查询网络，也不据历史或该状态关闭产品门禁。R1 修订并复审、b1 实现后接口重核、b2a／b2b 各自必要回归与实际进程收尾、新非 editable 安装、自身原结构模板、新 fresh-context 产品审查、普通发布与自己的 CI 均继续待办；c1 独立 worker／loop／stop queue、总 Workflow、c2 公开交互、真实两轮及业务训练／质量／收益仍未交付。

## r2 修订复核：R1 尚有 stopped 后的冷 inspect 尾部

复核草案 r2：10,147B，SHA256 `b921907deb05dafeb12313ed1c1ee7b11ae1d27d3681719450fe4dbaf67f0c2d`。第 17、19、21、29–33 行已明确 inspect-only 的 null input SHA 范围、完整 authorization SHA／原父身份、首次 spawn 前一次固定的 1–60 秒绝对 BOOTTIME 观察截止、实际 `stop_requested`、spawn task／handle 收尾，以及完整原 snapshot 后的 BOOTTIME／UTC／boot／discontinuity 检查。这些修订解决了 R1 的 bootstrap 输入和运行中 H watchdog 缺口，不引入新训练时钟或第二个 reaper。

**R1 暂未关闭，需求仍 request-changes；维护性仍 approve。** 第 23 行的 stopped 后 kill 条件仍只有“原 total 已尽”。冷 inspect 尚未取得原 total；若 S 已发出匹配 stopped 帧，随后在第 25 行所允许的直接结果读取中阻塞，`processes.run` 已返回，不再调用 `stop_requested`。父侧不能依靠尚未获得的原 total 收尾这个无后代的 S，因而冷观察仍可能无限等待。最小补充是把匹配 stopped 后的截止选择明确为：冷 inspect 用同一个首次固定的 bootstrap deadline，已核模式用原 total；满足相应截止后可 kill S，继续保留 unknown，不把它升级为业务停止成功。此时禁止再 spawn 和匹配 stopped 已保证 kill 的子树边界安全。后继验收应加入 cold inspect 已 stopped、结果读取阻塞这一条路径。仍未运行产品检查。

## r3 最终设计复审：R1 设计关闭

独立核草案 r3：10,699B，SHA256 `d8d049eb6b281c591e0f3716563adbffd2c87fa14f315a2b54851ef14f7d3692`，与 `.ergora/checks/training-cycle-gates/supervision-design-r3.json` 相同。第 23 行现已明确：匹配 stopped 前仅 TERM／等待原 reap，之后冷 inspect 继续用首次 spawn 前固定的同一 bootstrap 截止，已核模式使用原 total；相应截止耗尽后才 kill 无后代且禁止再 spawn 的 S，结果仍为 unknown。第 45 行补了 cold inspect stopped 后结果文件读取阻塞的实际验收窗口。该补充与 r2 的请求／clock 交接一起覆盖 R1 的运行中 H 和停止后 S 两段，不把原 run 的 timeout 或 future cancellation 当作回收证明。

**最终需求符合性：approve。最终维护性：approve。开放 finding：0／0；R1 仅在设计层关闭。** 只复核上述固定 r3 和本报告前已核的不可变 `07cbae2227d60c849df6ac96b4f96d3f71d80d43` 源码基线；后续 b1 的源码改动不在本设计认证范围内，也不由本报告验收。最初 request-changes 与 r2 尚未关闭的结论保持其原版本身份。

b1 完成后的接口前提复核仍为 b2 产品前置。冷 inspect 原件读取阻塞、inspect 返回时原 total 已尽、冷结果读取阻塞、实际 spawn 取消、writer／peer 业务 I/O 阻塞下其他 owner 通知、精确旧 owner 清理、前轮 release 和各进程真实收尾，均须由后继产品候选实际验证；当前没有这些产品通过结论。a6 的 CI／原 reviewer 接续由其原交付记录负责，本次未访问官方 CI，也不把初审时的 CI 状态当作当前终态。没有新增产品测试、安装或服务操作。
