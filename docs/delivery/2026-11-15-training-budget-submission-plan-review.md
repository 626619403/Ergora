# B3.2a 原训练预算提交设计：独立审查

本报告按轮保留；最新结论见末尾固定 r3 续核。原 r1 输入、finding 与当轮结论不覆盖。

日期：2026-11-15。审查者：`/root/training_budget_submission_plan_audit`，fresh-context 独立上下文；未参与设计编写或产品实施。按本项目 `AGENTS.md`、组件变更协议、`maintainable-project-delivery` 的 independent-review 与 `ergora-codebase-quality` 的 module-design／test-seams／repository-style 审查。授权仅含必要只读核查、ignored 核查索引和本报告；未运行测试、模型、训练、安装、服务或平台操作，未改产品、283 参考或其他共享文档。

## r1 结论与固定输入

- **需求轴：request-changes，开放阻断 3：R1、R2、R3。** 原预算进入原 intent、原 attempt 单次 slot、首 attempt 前确认独立 owner 的方向成立；实际 native create、可阻塞依赖与 fence 持久完成仍有下面的接缝缺口。
- **可维护性轴：request-changes，开放阻断 1：R2。** 同一个持续监管进程若直接承担可无限等待的 native 调用，调用者仍须猜测它是否能够处理截止；这项生命周期义务应由专用 owner 隐藏。没有发现需要另建训练账本、slot 表、start 客户端、通用调度器或插件总线的理由。

本轮只审 **B3.2a 具体实施设计 r1**，不重开已通过的 B3.0 合同，不认证 B3.1 的发布／CI，也不认证尚未实现的 B3.2b–e、B3.3、Q4.2c 或真实训练停止。

本地产品基线为 `b53bba613a3c02b14c69a6df9b0d526755d7e216`，parent `82ea3f163e0c29759eb6ebef93fb2e58d87e983a`。开始核查时 HEAD 为 parent，实施方在本轮只读核查期间提交了已验 B3.1；之后已直接核 HEAD 及下面 28 文件索引，所有已跟踪核查文件均逐字匹配该本地产品基线。没有预算绑定、连续 owner 或预算 adapter 的新实现。

|固定设计|字节|SHA256|
|---|---:|---|
|[具体设计 r1](../plans/2026-11-15-training-budget-submission.md)|7841|`f758ec8f36de4e051299acfbdac770af97ccfa623e4f285982fbd0ff3afbfd30`|

不可变副本与核查索引位于本地ignored目录`.ergora/checks/training-budget-submission/plan-audit/`下的`plan-r1.md`和`r1-index.json`，不随GitHub仓库分发。索引固定实际长度、SHA、基线匹配与分支；公开设计后续修订不覆盖这个r1输入。

已读根／源码／测试目录指引、`docs/PLAN.md` 当前检查点、[B3.0 r2 计划](../plans/2026-11-15-training-budget-executor.md)、[原计划独立审查](2026-11-15-training-budget-executor-plan-review.md)及当前 B3.1／B3.2 交付说明。主要实际路径：

`training.start/_submission` → `reference._training_process` → `_Submission.run/dispatch` → 原 Temporal client／workflow／`Activities.submit_or_lookup` → `LocalTrainingAdapter.create_job_if_absent`。另核 `_TrainingProject`、`training_cycles`／`budget_clock`、原 cancellation／runtime lookup、`processes`、训练 service／worker factory 和 native executor 的完成记录。原 `test_training_submission` 与 SDK fixture 仅作为接缝和状态转换证据阅读，没有执行。

## 阻断 finding

### R1 · P1 · 实际 native create 仍能在原预算或 owner 已 unknown 后获得许可

**设计位置：** r1 第 7–9、15、25–37 行。设计把新工作准入放在原 submission 和独立 owner；native create 只被要求看到 owner 已经写出的 fence。它同时承诺 owner 丢失、跨 boot、缺 `/proc`／原来源时不授予新工作。

**可达路径：** start 已 accepted，而 native activity 尚未执行；owner 在 fence 前被强杀，或宿主重启，之后原 activity 才消费该 start。原 [worker](../../src/ergora/data/reference/platform/upstream/temporal/perf_temporal/worker.py) 第 10–14 行从 `PERF_CLUSTER_ADAPTER` factory 构造 adapter；[原环境](../../src/ergora/data/reference/platform/local/agent_platform/core.py) 第 72–75 行选择原 queue／factory。[Activities.submit_or_lookup](../../src/ergora/data/reference/platform/upstream/temporal/perf_temporal/activities.py) 第 33–54 行与 [native create](../../src/ergora/data/reference/platform/local/agent_platform/training.py) 第 137–143 行均不读取新预算或 owner 身份。没有 fence 时，它们可以在原 compute 截止后创建 request。调用者后来拒绝 resume、原 clock 跨 boot 返回 unknown、禁止重新启动 owner，都不能撤回这次已经 accepted 的工作。

这不要求把任意强杀后的旧进程状态证明成已停止；问题是**之后真正创建新 request 的边界仍把预算 unknown 当作许可**。仅记录 unknown 没有满足 r1 的新工作准入合同。正常 accepted／held 两项自动 fence 验收也不能覆盖此分支。

**最小修正：** 在实际 create 的 registry 临界区内增加原预算／owner 的最终准入检查；绑定缺失、source／clock／owner unknown、原期限耗尽均不能返回新的创建许可。沿现有 `ClusterAdapter` factory 扩展应用 adapter，复用原 native create 算法，不改 283 参考，不复制 manifest／runner／baseline 检查。旧无预算路径与旧 queue 保持。

必须保证 budgeted workflow 实际由该 adapter 消费。一个固定版本的 budget task queue 与应用 worker 是可行的小接口；只改 client 环境并不会修改另一个已经运行的原 worker。同 queue 替换只有在能够证明所有 poller 都已替换时才等价。若采用独立 queue，应把协议路由固定进原不可变 intent，并让 managed queue 缺预算绑定明确失败，不能退回原无预算 adapter。

原 create 在取得 registry 锁后调用 `self.lookup_job`，因此可用有限作用域的 create 包装，在该虚调用中执行最终 gate，而无需复制 create。本 seam 依赖已固定 native 源码，仍须实施和回归：只在 create 的 task-local context 启用，不能用进程全局布尔值污染并发 activities；`fence_and_lookup`、原 job／完成读取和取消清理不能被过期的工作准入反向阻断。

**最小证据：** 从公开预算入口得到 accepted 后，在 fence 尚不存在时使真实 owner 失联，再放行实际 native create；由实际 managed adapter 拒绝新 request，原 intent／attempt／clock 保留、owner 不自动重启。另核 managed route 缺绑定不会被旧 worker 接走，以及原无预算仍走原路径。此项运行证据待实施，不能由手动 fence 或未来 executor 代替。

### R2 · P1 · 连续截止 owner 尚未隔离会阻塞其监管本身的依赖

**设计位置：** r1 第 23–29、33–35 行。设计明确 owner 不等待 submission 锁，且承认文件 I/O／系统调度没有硬实时保证；但未固定谁在 source／完成查询、native fence 或原取消调用阻塞时继续观察原截止与 cleanup reserve。

**源码事实：** [native registry_lock](../../src/ergora/data/reference/platform/local/agent_platform/training.py) 第 29–33 行使用阻塞 `flock`；其第 167–171 行 `async def fence_and_lookup` 内执行该同步锁和同步写入。[training_cycles.status](../../src/ergora/training_cycles.py) 第 332–350 行会进入第 316–329 行的原 ready 目录 `fsync` 与完整来源重读，亦不是可由 asyncio 超时打断的纯异步观察。原 source、project 和 native 完成读取也含同步文件／数据库操作。

例如，accepted 已返回后，owner 在下一次来源或完成检查中等待同步 I/O 跨过 compute deadline，原 native create 可在这段无人落 fence 的窗口执行；或 owner 在 fence 的 registry 锁内一直等待，无法在 cleanup 耗尽时记录该动作尚未确认，也无法及时停止后续控制操作。给这些 `async` 方法再套 `asyncio.wait_for`，不能中断它们内部的同步阻塞。r1 的“不等 submission 锁”没有解决这些不同的等待边界。

**最小修正：** 让持有不可变 owner 身份／独占锁的专用进程保留监管职责，把会阻塞的 source／完成探测、原 fence 与取消清理放入它监督的短子进程。每阶段用同一原 clock 的实际 stop predicate／剩余阶段预算；在跨截止时停止普通探测并进入 fence／cleanup，cleanup 耗尽后不再启动控制操作。不能把 `processes.run(supervised=True)` 的 `timeout` 参数当作截止，原 [processes](../../src/ergora/processes.py) 第 130–138 行只看 stop predicate。需要 subreaper 时仅在该专用 owner 进程启用，不放进共享 CLI／HTTP。

这仍不保证不受内核 I/O 停顿影响，也不能凭杀掉 helper 证明 fence 未发生。阻塞／丢回复按原件对账并记 unknown；未确认 fence、迟到的 fence、控制面请求与 executor 停止继续分列。其价值是隔离可隔离的依赖等待，让同一 owner 能继续决定何时停止普通工作、如何使用原 reserve，而不是扩大硬实时承诺。

**最小证据：** 真实 owner 在一个受控阻塞的普通探测跨过 compute 时仍进入截止处理；真实持锁进程阻塞原 registry fence 时，监督层可观察 reserve 耗尽并保留 unknown，不冒称已 fence 或已停止。核 helper 进程收尾、原 owner／slot／clock 身份及实际耗时；不能只 mock 出一个超时异常。本项尚无运行证据。

### R3 · P2 · native fence 调用返回尚不足以成为“持久 fence 完成”

**设计位置：** r1 第 9、25、29、33–35 行。owner 元数据要求无覆盖和 fsync；native fence 的完成则直接依赖原 adapter 返回，未规定 fence 目录和新建父层的同步与原件重读顺序。

**源码事实与后果：** [native core.write](../../src/ergora/data/reference/platform/local/agent_platform/core.py) 第 39–47 行先 fsync temporary 文件，再 `os.link`；其第 52–53 行清理 temporary，没有 fsync 新目录项。`fence_and_lookup` 返回可以证明当前可见的精确 fence，却不能证明该目录项已完成持久化。若 owner 随后在另一目录保存了最终观察并退出，本地重启后 fence 目录项仍可能丢失；原 accepted workflow 可以继续存在，再由不读取预算的 native worker 晚到 create。原授权跨 boot 拒绝自身重发并不能阻断这条既已在途的路径。

R1 的 create gate 可以保守拒绝该新工作，但不能使 r1 所称的“持久 fence 完成”事实变真；这仍是独立的完成证据问题。

**最小修正：** 预算应用 owner 在原 adapter 成功之后，同步精确 fence 目录与本次必要的新建父层，再重读核完整 fence／binding，最后才保存 durable-fence 完成观察和其时间。保持 native 文件和 writer 不变。link 已可见而目录同步失败、被中断或超过 reserve 时，不删除／覆盖 fence，不宣称持久完成；在同一原预算内只能完成原目录项的同步和对账，不能重新起算、重写 start attempt 或重启 owner。最终观察自身的发布也须明确目录持久化顺序。

**最小证据：** 在真实 fence link 后的目录 fsync 接缝注入失败／延迟，核 owner 不提前发布持久完成、不把可见性当完成；恢复只 flush／核同一原 fence，原 bytes／intent／attempt／clock 保持。保留真实 owner 自动产生 fence 的顺序，不让测试另行手动 fence。本项尚无运行证据。

## 已成立的设计与最小接口约束

以下结论限静态设计及已读原源码，不是产品通过：

- 原 intent 是正确的持久预算绑定位置；`load` 第 91–100 行现为精确旧形状校验，实施必须只为新的 budgeted intent 扩展可选字段验证，保持旧 intent／attempt／receipt／memo 的原算法。绑定后所有普通 prepare／dispatch／resume 从原件发现预算，选择器省略不授予无预算权限。
- 原 `.attempt.json` 足以作为单一不可归还 slot。`run` 第 310–342 行的原 submission 锁与 `CheckpointedClient.start_workflow` 第 236–240 行的 attempt-before-send 可以复用；attempt 之后 NOT_FOUND、取消或换 cycle 只能对账，不新增独立 slot 双写。
- 原 `_Submission.fence` 第 191–192 行拒绝 submitted／rejected 的手工合同应保持。预算 owner 沿精确 native fence seam 扩展；不把原手工 CLI 变成预算自动化入口，不在 held RPC 的 submission 锁后等待。
- 原取消通过 receipt、完整 Experiment 与 memo 核精确 run；`_Cancellation` 使用自己的取消锁，不需要反向获取 submission 锁。预算 owner 的自动 request ID／reason 应固定并保存，恢复原取消 intent／attempt／history，不能每轮生成新 ID 重发。来源／预算 unknown 与原 submitted receipt 应是分列事实，不能靠覆盖原 submission 状态使已有精确 receipt 无法清理。
- 匹配原 request／job 的 terminal native result 应先作为完成事实读取；有效成功、等待人工 release 的先前轮不统一 fence。不能只凭 Temporal COMPLETED、result 文件存在或原 receipt 判定 native 成功，也不能凭 owner 锁释放证明后代停止。B3.2 的 `executor_stop_confirmed` 保持未知。

建议只补实际消费者需要的窄接口：

|owner|最小职责与真实消费点|
|---|---|
|`training_cycles`|复用其完整 `_load`／来源／ready／耐久观察合同，提供必要的原授权与选定 admission 读取，不在新模块复制 authorizer／reader，也不重新 live-admit 或起钟。|
|`reference_training_budget`|对原 submission 隐藏绑定验证、连续 owner 启动／观察与其监督进程生命周期；对实际 managed adapter 隐藏同一原来源／clock／owner 的创建 gate。单一资源生命周期可放同一内聚模块，无需每个动作再建一个转发模块。|
|原 adapter factory／应用 worker|在本族协议构造处选择预算实现，真实 create 临界区核最终权限；原 workflow、manifest、runner、评分、归档和 release 算法继续由原 owner 处理。不要把具体 adapter 分派散到 CLI 或训练调度层。|
|原 submission／cancellation|继续拥有 intent／attempt／receipt、完整 Experiment／memo 对账与取消 signal 的单次发送；预算 owner 复用这些义务，不另写 start／signal 客户端。|

新 task queue、adapter 与监督 helper 如被采用，是对 R1／R2 的设计修正，须写入固定 r2 再复核；本报告没有把建议方案视为已经支持。

## 剩余证据与交接

R1–R3 修订前，B3.2a 保持待通过。修订后应核完整新字段／路由、helper／owner 的锁与进程寿命、fence durable 完成定义及失败边界。原 r1 身份和本轮 finding 保留，由同 reviewer 对固定 r2 续审，不递归审查本报告。

B3.2b–e 尚无本片运行证据：原入口的绑定／省略 selector／换 cycle 拒绝与 attempt 不重发、真实独立 owner 的 accepted-return／held-RPC 自动 fence、owner／source／clock unknown 下实际 native create 拒绝、阻塞和 fsync 故障、原取消 cleanup 与完成轮保留、新非 editable core／SDK、自身模板、fresh-context 产品两轴、普通发布与自己的 CI 均为待验。旧 B3.1 结果不转授这些行为。真实 Temporal、实际 executor／setsid 后代停止、GPU／质量／收益和后继自动循环继续分别保留其原义务；Kernel 专家仍在 v3 路径。

本轮仅执行文档／源码／测试读取、Git 状态与提交身份、标准库字节／SHA／基线核对和本报告的静态链接核查。未把任何测试阅读、历史报告或设计承诺记为新运行通过。

## 固定 r3 同片续核：设计两轴 approve

日期：2026-11-15。同一独立 reviewer 续核修订，没有参与产品实施。**需求轴 approve／开放 0；可维护性轴 approve／开放 0。R1–R3 在 B3.2a 具体设计层面关闭。** 当前仍未实现 B3.2 产品，下面的设计关闭不等于运行关闭或 B3.2b–e 通过。

### 本轮固定输入与检查范围

|版本|字节|SHA256|审查归属|
|---|---:|---|---|
|r2|12245|`13913de715bb2db97048ec083a62d4add430f117cecb01269751715abbe5ffdc`|已读完整修订；保持固定副本，未先行给该中间版通过结论|
|r3|12979|`1b14d600b7d58a41a4d3d5277fd9a435dd3b3eed6e843de1c8d835916b5b2b3a`|本轮最终具体设计，公开文件与固定原件逐字相同|

副本位于上述本地ignored目录中的`plan-r2.md`、`plan-r3.md`，续核索引为`r2-r3-index.json`，不提供GitHub下载链接。HEAD仍为`b53bba613a3c02b14c69a6df9b0d526755d7e216`；r1索引内已读产品／测试逐份核字节和SHA保持，未见B3.2产品变化。

本轮对照完整 r2、r3 与二者差异，重新核原 create 的 registry／虚调用、worker factory／queue 与 managed service 构造接缝，以及已读监督和写入行为。另按实施方提供的依赖事实直接读取 `contracts` 导入、native lock 的包声明、`pyproject.toml` 和原训练 service 命令；这四份新增身份亦固定于索引，没有运行环境探测、安装或试启动。

### R1–R3 关闭依据

|原 finding|固定 r3 的可核修正|设计处置|
|---|---|---|
|R1／P1：accepted 后 owner／source／clock unknown，实际 create 仍可获得许可|第 13 行把固定版本 queue 纳入原 intent canonical 身份；第 33–37 行明确新 queue／实际应用 adapter／独立预算 worker 的消费路径，不向旧 queue 回落。create 在原 registry 锁内的最后 `lookup_job` 虚调用核原来源、完整绑定、owner 与原 clock；缺 intent／budget／source、错 Experiment／queue、owner 失联或跨 boot 均拒绝新建。原 fence／poll／gate／release 与已有 job 读取不受该工作 gate 反向阻断；create 标记为 task-local，finally 重置。|关闭。实际准入不再仅依赖 owner 已经写出 fence；没有把 OS 停止 unknown 当作新建许可，也没有复制原 create 算法。|
|R2／P1：同步依赖会阻塞持续监管|第 41–43 行明确持续 owner 保留原时钟、身份和锁，把完整来源／DB／gate 探测、registry fence 和原取消放入专用受监督子进程。沿 `processes.run(supervised=True)` 的实际 stop predicate 按 compute／cleanup 原 clock 停止，不依赖其无效的 timeout 或 asyncio wait_for；compute 截止停止普通观察，随后只在原 reserve 内 fence／对账。阻塞、helper 失联、reserve 耗尽分列 unknown。|需求／维护的同一阻断关闭。可隔离的等待与持续监管有明确资源归属；未扩大为内核 I/O 硬实时或任意强杀后的停止保证。|
|R3／P2：可见 fence 被当作持久完成|第 43 行明确原 adapter 返回之后，实际同步 fences 目录与必要新建父层，再完整重读 fence／binding，只有这个顺序完成后才报告持久阻断；可见文件、helper 返回、owner／final 元数据 fsync 均不能代替它。第 60 行要求 fsync 失败／延迟、同原 fence 恢复只 flush／核原件，且不续期、不重启 owner。|关闭。当前可见、持久完成和未知状态已有不同预期，原 native writer 与 283 参考保持。|

r3 同时明确预算路径的原 attempt 完成目录 fsync 后才允许 RPC，首 owner 确认前持久化原 intent／owner 目录。原 intent／attempt 仍是唯一预算绑定／slot 权威；没有引入第二 slot 或可续期时钟。

### worker 依赖边界的补充澄清

r2 的同一应用 training-worker 注册两 queue，尚未固定合法解释器环境。直接读源码可确认：`training_cycles.py:12` 经 `contracts.py:7` 依赖 `jsonschema`；冻结 native `requirements.lock` 声明原 Temporal SDK，但没有 `jsonschema`。原 managed `training-worker` 经 `agent_platform.service` 使用 native SDK Python，应用 core 本身则不要求 Temporal extra。不能假设这两个环境天然具有对方的完整依赖。

r3 第 33、37 行已把它明确成两个独立可选服务：原 `training-worker`／queue／adapter／native SDK Python 保持；新增 `training-budget-worker` 仅消费预算 queue，使用安装了 Ergora 与 Temporal extra 的应用 Python，缺 SDK 明确失败。`services` 本域合成新 program，复用原 Supervisor 的必要资源设置，不改冻结 setup／lock，不拼另一环境的 site-packages。这个方向符合已有 service owner 和实际 reader 依赖，足以消除设计歧义；没有新开阻断。实际命令、导入、单独日志／服务身份与合法 core 环境保持仍须在产品片验证。

### 实施时必须保持的最小合同

以下是本轮通过的实现义务，尚非已核代码，也不另列计划 finding：

- 原 `training_cycles` 的完整 source／authorization／ready 验证应被复用。初次 intent 绑定完成 ready 的耐久观察，实际 create gate 随后只读同一原件，不在 registry 锁内调用会取得 cycle 锁和 flush 目录的 `status` 用例；最终 clock／owner 检查靠近 native 新 request 写入，不把早先的 ready／alive 快照当永久权限。
- 原 intent、attempt、owner 身份与最终观察的持久发布都须在对应 link 之后完成必要目录同步，并把这些耗时计入同一原 clock；所有无覆盖、容量、strict JSON／普通文件和精确 SHA 义务仍在其 owner。fence 的 durable 完成先于最终观察，不能只同步元数据文件而漏掉它的新目录项。
- create 的有限作用域 guard 只限制新工作；同一 native `lookup_job` 也被 fence 调用，必须保留 task-local 清理和真实并发接缝，避免过期预算反向禁止清理或旧成功轮 release。worker 路由与 source／owner 验证使用同一原 intent，不能引入第二份绑定来源。
- helper 不继承 submission／owner 的生命周期锁；原 owner 在其监督期间继续承担截止责任。停止一个 helper 后仍可能有未知副作用，必须按原件对账，不能据退出码推断没有 fence／signal。未来 executor 的交接 ack 前不能退出监管。
- 原 receipt／memo 对账与预算覆盖保持分列；固定取消 request ID／reason 恢复原取消 intent／attempt／history。匹配已完成先前轮先保留，不能因总循环期限、项目漂移或原 worker 的控制状态而统一加 fence。

### 仍待产品证据

第 58–63 行把原绑定／省略 selector、单次 slot、accepted-return／held-RPC 的真实 owner 自动 fence、owner 失联且无 fence 时实际 managed create 拒绝、普通探测阻塞越 compute、registry 锁跨 reserve、fence fsync 故障／同原件恢复、取消 cleanup 和先前完成轮保留全部列为本片自己的后续验收；不再依靠未来 B3.3／c 或测试手动 fence。

这些项目均未实现／未运行。新非 editable core／SDK、实际两个 service／queue／factory 命令、自身模板、fresh-context 产品两轴、普通发布与自己的 CI 仍待；原 B3.1 或 r1 源码阅读不转授结果。B3.2a 此次只关闭具体设计审查，B3.3 的真实 executor／后代停止、真实 Temporal、GPU／质量／收益及自动循环仍保持各自边界。

本次继续只写本报告与指定 ignored 索引／设计副本，静态核设计字节、来源身份、依赖声明和文档链接；没有运行测试、模型、安装、服务或平台操作。
