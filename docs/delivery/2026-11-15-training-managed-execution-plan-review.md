# B3.3c c0：独立计划审查

日期：2026-11-15。审查者：`training_managed_execution_plan_audit`，新的fresh-context独立上下文，未参与实现。先读原始要求，再读固定设计及真实owner／调用者。仅审设计；未实施或验收新的执行能力。

公共入口见[计划](../plans/2026-11-15-training-managed-execution.md)与[交付](2026-11-15-training-managed-execution.md)。下文`.ergora/checks/`路径指本地ignored证据，未随Git发布；历史原件按所列SHA256识别。

**当前结论：固定r2需求符合轴approve／结构维护轴approve，开放0／0。R1在设计层面关闭。** 下文保留r1原request-changes和探针；r2精确身份、续核与产品门禁见末节。

## r1结论与精确范围

需求符合轴：**request-changes**；结构维护轴：**request-changes**。一个共同阻断项R1：业务子树reap后，又给同一S增加发布子树，却继续使用“收到stopped即可强杀S”的条件。该顺序须先修正再实施。

基线为`75bc99d788a9cef292b7c41eb7e01ac03d13de47`，分支`refactor/architecture-foundations`。前置未提交B3.3b产品按`.ergora/checks/training-executor-protocol/product-scope-r1/scope.json`识别，清单SHA256 `1c9b7b80172258d6697a2e5d752c38abefb81aaf84019803ba2a20425e881287`，七个产品／测试文件与该原件逐字一致；本次不重新认证其本地产品结论、发布或CI。

原始要求为`.ergora/checks/training-managed-execution/raw-requirements.md`，SHA256 `217d6d5768acdc2d2a5543d0190206ebe5ad62b3fe1975fb9e0d709d93c6bf18`。审查以`.ergora/checks/training-managed-execution/design-scope-r1/scope.json`中的23份固定完整文件为准，清单SHA256 `dadb2647c00f81651c5d97cd2c973cbe8af25d5c05e8b76f590e929e6938bc8b`，每份大小／摘要均匹配。直接候选只有：

|固定候选|字节|SHA256|
|---|---:|---|
|`.ergora/checks/training-managed-execution/design-scope-r1/docs/plans/2026-11-15-training-managed-execution.md`|18350|`1f677bae546a03e9865d93ca6e41f4815001a37a910a159348a4bb9ae61f3483`|
|`.ergora/checks/training-managed-execution/design-scope-r1/docs/delivery/2026-11-15-training-managed-execution.md`|1097|`9699cbe926c2606c917668ed9113655519c5044114268132b9bc8425a13fb900`|

审中作者更新了前置计划的状态，并准备两份c文档r2；这些实时变化不改变本节r1判断，须以另一个固定候选续核。读取规则包括根与`src/ergora/AGENTS.md`、组件协议、`maintainable-project-delivery`独立brief及`ergora-codebase-quality`三份参考。邻接来源／摘要见`.ergora/checks/training-managed-execution/plan-audit/inspection.json`，SHA256 `bfd65756cd6f0051047eb2ccedf2a23b0af199b7ac3451ccde7e487015c01374`。

## R1：业务stopped帧之后再spawn publisher，会使原安全终止条件失效

**阻断；影响需求与结构维护两轴。** 位置为固定计划r1 **L79、L106**，对照其 **L41** 和现有[reference_training_budget.py](../../src/ergora/reference_training_budget.py) L144–147、L212–219，以及[processes.py](../../src/ergora/processes.py) L145–156。

现有phase之所以能在第一个完整stopped帧后强杀S，是因为`processes.run(supervised=True)`已经kill／wait直接helper并完成`_reap_children()`，随后S只读结果并发送帧，没有再创建子进程。r1却规定执行S先发业务reap帧，之后启动“受total期限监督的发布helper”；同段又允许total后杀“仅剩发布子树的S”。这时第一帧只证明先前业务树已停，不能证明后来publisher已被回收。

可达顺序是：原native业务结束并reap → S发送stopped → S启动发布helper → helper卡在存储操作 → total到期 → 父owner依据第一帧直接SIGKILL S。S不能再运行`processes.run`的finally回收，publisher仍可存活并继续写停止原件。这里不声称runner还活着；缺口是后来的发布子树失去reaper与期限owner，父侧也没有它的完成边界。

已用真实原`processes.run`构造这一顺序，业务执行仅为`python -c pass`，publisher用sleep代表阻塞；没有调用native executor、服务或训练。S返回`-9`后publisher的PID／start_ticks保持、状态仍为`S`；专用探针随后对该PID执行SIGKILL并`waitpid`收尾。原结果及清理事实保存在`.ergora/checks/training-managed-execution/plan-audit/probe-results.json`，SHA256 `2e7a116fcfa3f620d3a962efb769440998dec3cf0bf1393e3951c69a02acb28d`；探针为`.ergora/checks/training-managed-execution/plan-audit/probe.py`，SHA256 `dd1a23a01b041a1662ff4503d119db0a6fe6bc34179f271a7b56b63385a878fc`。它验证进程归属／终止顺序，不冒充真实fsync故障或c2产品测试。

最小修正是在业务reap帧后明确禁止S再spawn任何子进程，由该无子进程S直接读取／写入／同步停止记录及发送观察，父侧仍非阻塞监督total；卡住时只剩S自身可终止。若确需独立publisher，则给它单独的phase／reap边界，不能把业务stopped帧当作publisher已回收。补一个真实阻塞发布时跨total的接缝，检查业务树已reap、无遗留publisher、持久证明unknown且不重launch；本片允许的不可中断I/O overrun不能改记为已及时退出。

## 其余合同与结构取舍

已沿真实调用确认下列设计约束有合适owner，r1在这些方面没有新增阻断项；这仍只是计划判断：

- **出生与兼容。** 现有`owner_record()`严格读取schema1；新reader保留其字段与控制职责，新schema2能力只在原owner出生时产生。现有owner不可重启，普通start／queue／status／resume-start／旧登记恢复不产生执行请求。新能力与显式请求分开，未把升级二进制当作授权。
- **原run与权限。** `training → reference → _Submission`仍持应用入口；复用`reference_training_runtime.lookup`的固定run及完整初始Experiment核验，并另核原intent memo。原`native_request()`只核job ID，草案明确补完整四字段、Experiment／runner及原字节身份。原start slot、receipt、memo、authorization／clock不分叉。
- **不重执行与原锁内gate。** Popen之前持久消耗launch；已有launch、丢帧、Popen失败、hook前强杀均不重新返回许可。B3.3b的callback确在原executor.lock内、started／Git与业务try之前；不把外层execution锁或锁外预检当作替代。旧started、无hook接管及已有result的行为与前置协议相符。
- **并行停止。** c1保留原四mode与`run`合同，非阻塞生命周期留原`_BudgetPhase`／`BudgetedStart`；专用S继续复用唯一`processes.run`回收算法。执行与fence分支用同一clock，取消本地通知留原`_Cancellation`，远端signal仍只有原attempt／history入口。`completion()`及fence不得被先出现的native result提前结束，这是现有代码必须实际改变的路径。
- **依赖。** 选定native解释器拥有原MLflow等依赖，应用gate不借应用site-packages提供依赖。已有`reference.worker_command` L201–206实现临时导入`ergora`后立即pop父目录的bootstrap，且`tests/test_reference.py` L56–71已有真实shadow反例。应复用这段既有方式；无需另造package加载框架。当前`reference` source validator、`budget_clock`及其实际导入闭包可在Python `-S`中加载，无State／yaml／jsonschema／Temporal导入，native依赖解析仍保持原路径。该探针不证明未来gate或实际native venv可用，c2仍须用选定真实native解释器验证。

c1与c2可以各自形成完整验收片：c1只交付可并行监管的原phase生命周期，独立验旧串行合同、并发S／后代及阻塞互不影响；c2整体交付权限、请求、launch、锁内attempt／ack、实际原native过程、停止观察／恢复／取消和手册。各片自己的安装、原模板、新独立审查与发布／CI必须逐片完成，c3不能成为前两片延迟验收的理由。kernel专家仍在v3提案路径，本片没有模板改动、自动循环、采用权或真实训练收益主张。

实施时特别保留两个现有接缝的约束：`_BudgetPhase.__init__ → budget.path → _Submission.path → safe_file`也会触发`resolve／is_symlink`元数据I/O，须遵守草案“执行开始后父owner只做非阻塞控制”的总约束，不能只移动mkdir／stderr.open；非阻塞finish也不能在另一个phase仍需监管时进入无条件wait。它们目前属于明确设计约束的实施验收项，本审查未另报已发生的产品缺陷。

## 实际检查与未闭合门禁

实际做了固定23文件大小／SHA核对、前置七产品／测试文件逐字核对、真实owner／caller／锁与导入链阅读、Python `-S`导入探针和一个独立可收尾的进程顺序探针。没有运行测试矩阵、native executor、训练、Temporal、MLflow或GPU；没有安装依赖、修改产品、提交或推送。审查写入仅本报告及ignored `plan-audit/`。

当前r1开放：需求1／维护1，共同R1一项。先固定更正设计并由同reviewer续核，再按各产品片实施与验收。B3.3b精确发布／自身CI、c1／c2产品及安装／真实控制旅程均不能由本次c0审查替代；前置75bc的CI状态更新仍由其原交付记录核闭，不继承为c产品通过。真实B3训练、GPU／质量／性能、自动有限循环与人工采用继续保持原门禁。

## 固定r2续核

同一独立reviewer在正式记录r1结论后，读取了`.ergora/checks/training-managed-execution/design-corrections-r2/scope.json`及两份完整固定更正文档，并逐段比较全部r1→r2差异。r2清单SHA256为`2a24b23e3e98c9806f08ac9759dd2a2d38caac593525f92bac0ab34e1cafc206`，正确链接原r1清单；两份原件的大小／摘要及实时文档均匹配，原固定源码仍逐字相同。

|固定r2候选|字节|SHA256|
|---|---:|---|
|`.ergora/checks/training-managed-execution/design-corrections-r2/docs/plans/2026-11-15-training-managed-execution.md`|20010|`1b7af0c3245f41ce3a1a5d4f6f8e3fca7f383c5462ae6fa8ed0cd7f7bacf6e45`|
|`.ergora/checks/training-managed-execution/design-corrections-r2/docs/delivery/2026-11-15-training-managed-execution.md`|2056|`209db79f2ec8c984a8f68a0a0065c5350d909c528d32238e448e1c4e298d69bd`|

R1的最小更正已在计划r2 L41、L79、L106一致落实：先由原`processes.run`完整reap并发送匹配帧，此后同S直接读取attempt／ack、写入／同步stop并观察结果，禁止创建任何后续子进程。父侧据第一帧终止的对象因而确实只剩S自身，不再把后来publisher的回收错误归入早先业务帧。存储阻塞时，已观察业务回收与持久证明unknown仍分列；safe-reap不可被打断和不可中断I/O overrun合同保持。**R1仅在设计层面关闭**，实施还必须实际经过阻塞发布／跨total及无遗留子进程的接缝。

r2 L87同时明确复用现有`reference.worker_command`的包自身bootstrap，不新增另一套package spec加载路径；source validator／clock仍共用现有实现，未借此放宽原native解释器及依赖验收。其余改动是状态及问题处置记录，没有扩大执行权限、改变出生兼容／launch／原锁内gate，或把c1与c2验收合并。

前节指出的父侧`path → safe_file`元数据I/O及跨peer的阻塞finish继续作为c1具体验收义务：实际调用链要确保执行开始后的父侧路径处理不触碰业务文件系统，向全部peer请求停止后仍轮询全部peer，终止后的结果收集不再等待一个仍存活的S。r2的总约束已覆盖这两项，本次approve不将其记为已实施。

最终设计结论：**需求符合轴approve；结构维护轴approve；开放0／0。** 本次更正只需完整差异／链接／身份检查，没有理由重跑未改产品。完整差异保存在`.ergora/checks/training-managed-execution/plan-audit/r1-r2.diff`，SHA256 `b7e4cc31e801c6a8a886dc937298e2f46dcfb315a69953af357aa959658bb627`；复核结果为`.ergora/checks/training-managed-execution/plan-audit/r2-verification.json`，SHA256 `9e6a42e519bdb7a04c875efb3200ea1ea112c3beb83ed8260c568a723f5b7547`。原r1实证保持，不改记成修后产品通过。

下一步仍先闭合B3.3b自己的精确发布与CI，再固定实际实施基线交付c1。c1及c2各自的产品、非editable安装、原模板审查、新fresh-context产品审查、普通发布／自己的CI与c2真实Temporal短CPU旅程全部未由本次设计审查认证；真实B3／GPU／业务质量／性能收益、自动循环和人工采用继续开放。
