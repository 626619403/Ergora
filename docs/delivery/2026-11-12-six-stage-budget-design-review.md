# B2 总预算独立设计审查

日期：2026-11-12。评审者为独立 fresh-context agent `budget_plan_review`；未参与设计或实现，未接收实现对话或预设通过结论。按项目 AGENTS、`maintainable-project-delivery` 的独立 brief 与 `codebase-design` 审查。本报告审的是设计，不是预算产品验收或 B1 缺陷复审。

**当前结论：r2 同片复核后，B2-SP1/B2-DS1 两项设计 finding 均关闭；本片设计范围内 Spec 与可维护性开放 finding 为0/0。** 可以按修订后的 B2a 推进实现。预算产品、正式入口行为、安装、实际模型、完整 Temporal 生命周期及产品独立审查仍未验。下文保留 r1 原判词和证据，末节记录关闭依据。

## 基线与范围

实际 HEAD 为 `f394945db894740ad23a81c62b4ad87c85a84511`。先读原 [D1/B2 合同](../plans/2026-11-12-six-stage-native-consumer.md)，再核 [B2 计划](../plans/2026-11-12-six-stage-budget.md)、[交付记录](2026-11-12-six-stage-budget.md)、当前 PLAN 与真实调用者。审查输入为私有 `six-stage-budget/plan-candidate-r1` 的九份 Markdown；清单 `plan-files-r1.json` 的 SHA256 为 `2b234bb56e44e8fc206eac0fbe13679cab71b41c7e24d12ffa189b66ca458908`。逐项读取字节，九份均与清单的尺寸/SHA及当前文件相等，`plan-tracked-r1.diff` 与相对产品基线的 tracked diff 相等。两份新 B2 文档也已完整读取。

九文件范围为 `docs/PLAN.md`，`docs/plans/` 下的 `2026-11-12-{six-stage-budget,six-stage-materials,six-stage-native-consumer,specialist-template-refresh}.md`，以及 `docs/delivery/` 下的 `2026-11-12-{six-stage-budget,six-stage-materials,six-stage-materials-review,specialist-template-refresh}.md`。主计划 r1 为 10,134 字节、SHA256 `8ef4d7ac985406fa6958f12348913dd7cc0a0f84dd65dbe719bf592a90a8fd74`；B2 交付记录为 2,018 字节、SHA256 `6370de8fc6e66ebf3e19c28f14416eb0049814a234f87d6c20352a3fa7049e74`。

只读核了 `tasks`、`reference_creation_process`、`reference_task_creation/submission/runtime`、`reference_inputs/workflows/worker/executor`、`review_dags`、`stage_driver`、`agent_runs`、`agents`、`processes`，以及冻结参考内相关 Executor、Sandbox、process_job、workflow、FileAdapter 的实际实现。冻结源码仅作事实证据，没有改动。没有运行测试、模型、安装、网络请求或受控进程探针；B1 的 295/58、模型 approve 和自己的 CI43211896925 均不作为 B2 验收。

## Spec 结论

**r1 需修正两项设计缺口，尚不能据此开始宣称全程预算闭合。** 方案 A 本身成立：预算实例放在原 creation，完整输入继续绑定原 SHA/memo/history，确定性 preview 不含当前时间，submission 的 attempt 后只 lookup，符合首次授权及恢复不重领的原要求。队列、owner、semaphore、重试、模型、可信命令和清理都被列入目标，没有另建调度器或正式账本，也没有扩大到 provider API/token/费用。

有限 slot 上界有源码依据。[WorkDelivery](../../src/ergora/review_dags.py#L233) 校验 work unit 与 implementer 叶一一对应；前阶段恰为 inventory/plan，review 逐叶调度，integrate/verify 不走模型。因此 `2 + work unit 数 + reviewer 数` 适用于本片支持形状，建议 reviewer 也应计入。slot 与确定性 job/process 的原 attempt 绑定、不因 unknown 退款，是保守且可恢复的方案；预留数、启动 attempt 和可核 native 命令仍须分别展示。

## 可维护性结论

**沿现有所有者推进可行；B2-DS1 的最终发布所有权必须先固定。** 将整个 job 移到独立进程有必要：[原 prepare 的阻塞 Git 锁](../../src/ergora/data/reference/platform/local/agent_platform/executor.py#L129)、构造和收集都在模型外，ThreadPool Future 无法停止这些线程。应迁移执行接缝，保留原调度和算法；不需要重写六阶段 Executor、增加 BudgetStore 或复制一套进程账本。

一个小 stdlib 预算 Module 可为 creation/submission、workflow 与进程所有者提供共同 Interface，保持身份、deadline 和有限 slot 的确定性计算；持久 attempt、terminal 和副作用归原所有者。B2a/b 暂不开放运行的分片合理，但 [输入注册表](../../src/ergora/reference_inputs.py#L348) 同时驱动 reader、worker 与 request roots，必须实际证明新输入不会自动注册可绕过预算的 worker。若为单独发布而产生空 Interface，按计划保留为同一未发布片，比再加一层过渡框架更简单。

## Findings

### B2-SP1 · P2：准备过程缺少覆盖整个生命周期的可停止所有者

- **位置：** r1 [预算计划](../plans/2026-11-12-six-stage-budget.md#L47) 第47行及 B2.0/B2a/B2c（第58–61行）；[交付记录](2026-11-12-six-stage-budget.md#L9) 第9、15行。
- **事实：** 计划要求先持久起点，但执行接缝探针与 B2c 明确包住的是 Executor job。现有 [tasks._project/_definition](../../src/ergora/tasks.py#L19) 在调用专用 creation 进程前完成安装身份遍历、manifest 检查、完整材料读取与冻结；[task_creation](../../src/ergora/reference_creation_process.py#L14) 仅给后面的子进程固定30秒，并由父进程清理临时目录。不能从“先保存一个 deadline”推得这些操作已受它停止。
- **可达场景与影响：** prepare 保存起点后，manifest 遍历、安装文件读取或编译阻塞，超过工作截止仍继续业务准备；调用者的固定30秒或事后 expired 检查既不停止前置读取，也不证明清理归属于同一预算。现有 B2a 的“到期不发布”检查不足以检出这个缺口。
- **最小修正：** 明确持久 prepare 后，整个安装遍历、`tasks._definition`、manifest/编译/临时材料收集与清理都进入可停止的 prepare worker，使用与 whole-job 相同的绝对 deadline/清理监督原语。父进程不得先无限期读完材料再给 compiler 套 timeout。preview 只读该实例已冻结的结果；恢复使用同一起点和原 attempt。将慢材料读取/编译和 prepare 清理未确认列入实际入口证据，不限于 job 探针。
- **状态：** r1 开放。此项是新预算设计缺口，不是要求改变 B1 已发布合同。

### B2-DS1 · P2：只延迟成功回执仍会让原 fence 错认资源已停止

- **位置：** r1 [预算计划](../plans/2026-11-12-six-stage-budget.md#L70) 第70行及 B2c（第61行）。本项同时影响 Spec 与结构，按一个 finding 计。
- **事实：** 计划只明确“清理确认后发布正式成功回执”。[reference_executor.process](../../src/ergora/reference_executor.py#L770) 在 child 执行后直接 verify/publish receipt，再更新原 jobs ledger（第795–799行）。[FileAdapter.fence](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/adapter.py#L187) 只检查是否存在可验证的终态 receipt；`FAILED`/`CANCELLED` 与 `SUCCEEDED` 都会使该 job 不再 unresolved。它不另核进程树停止。
- **可达场景与影响：** 新 whole-job worker 超期或异常，若沿当前 `process()` 先发布 FAILED/CANCELLED，而脱离进程组的后代或收集仍 unknown，原 fence 会返回 confirmed。仅把成功回执延后，或在外层包一层监督进程，都无法消除这个错误确认。
- **最小修正：** 固定新版本的原 job finalizer 为唯一正式发布者。child 只产出不可作为 terminal 的待核结果；整个拥有树停止、收集/hash 验证及预算判定完成后，finalizer 才唯一 verify/publish 并更新原 jobs ledger。清理未确认时不发布任何正式 terminal receipt，保存原 attempt/超时事实，使原 fence 继续 unresolved。恢复只核/收集同一次 attempt 的原结果，不重跑 body。这样可保留原 fence 算法和283冻结原件，无需新正式账本。
- **状态：** r1 开放。此项是 whole-job 迁移必须明确的所有权，不是本次修改旧执行版本。

## 风险、未验与下一出口

源码已经证明现有 supervised 路径依赖外部 TERM，[回收循环](../../src/ergora/processes.py#L75) 没有总截止，旧 monitor 又另建 session 并有自己的快照/等待。独立进程加 subreaper 的接缝值得验证，但尚不能断言已覆盖构造前、准备、清理中及 supervisor 自身退出的所有窗口。探针须核真实 PID/starttime、脱离组后代、阻塞锁/Git、重复入口不 spawn 和 cleanup unknown；之后仍要用实际 prepare 与正式 job 入口验证预算与最终发布，不能把原语探针替代产品出口。

UTC 与同 boot 单调时钟取更保守剩余量、拒绝跨 boot/主机/异常时钟恢复，是已写明的首片限制；实际支持形状须在准入处可拒绝。deadline 后的只读观察/安全收尾不应回补业务额度。a/b/c 的旧合同隔离、无模型容量准入、精确 input/memo、所有实际 spawn 与 slot 的关联仍待实现证据。

当前没有预算源码或 CI 变更，无法作实现性能或冗余测试判词。现有计划复用真实生命周期夹具、不添加算术同形测试或重复 CI 的方向合理；应先覆盖上述两个静默错误，再按受影响范围检查。完整 Temporal 生命周期、非 editable 安装、实际自身模板、新独立产品审查与本候选必要 CI 各自保持待做，完整六阶段实际旅程仍属于 D。

r1 时的下一出口是修订本片设计并同片复核 B2-SP1/B2-DS1，再确定 B2.0 探针支持的接缝和 B2a 实施范围。本报告不替代后续各产品片独立评审。

## r2 修正与进程原语证据同片复核

独立读取修订计划及交付全文，再核十文件 `plan-files-r2.json`（SHA256 `e80fe7d214ade08b4f488f68a4c52ef8c8ad034ee839fcb30189cf41c03418cf`）：追加本节前，十份尺寸/SHA均与当前字节相等。主计划为11,862字节、SHA256 `ac44c1e98b5b83b3681d4237c11471edb10d898ff37b2f81f2b73c895e7273ec`；B2交付为4,190字节、SHA256 `71047fc25ae24d8ea48c0657597d4d9389d42498c22888ae5945fc887a72701f`。清单内本报告的9,266字节记录对应本次追加前的 r1 报告，不声称自引用清单覆盖追加后的字节。

**Spec：两项关闭。** 修订计划第19、47–49、61行把安装身份遍历、整个 `tasks._definition`、manifest/编译/收集及临时目录清理交给同一绝对 deadline 下可停止的 prepare worker，并要求实际 prepare 入口的慢材料/编译与停止清理证据。父进程不再被允许先完成无期限材料读取；preview/create重核也通过此消费者。这已填齐 B2-SP1 所缺的所有者和可验收出口，关闭的是设计 finding。

修订计划第54、63、72行明确 child 不能复用 `process()` 末尾的正式发布，原 job finalizer 在整个拥有树退出且收集/hash/预算核对后，唯一发布 **SUCCEEDED、FAILED、CANCELLED 全部正式终态**，再更新原 jobs ledger。cleanup unknown不发terminal，原fence保持unresolved；恢复只核/收集原attempt，receipt已发而ledger中断则只补原状态更新。这既修正 B2-DS1 的可达错误确认，也明确了最终发布的 Interface，关闭该设计 finding。运行实现仍须证明这些顺序。

**可维护性：本设计范围开放0。** 该修正复用原创建记录、job、正式receipt、ledger和fence，不增加正式账本或调度层。prepare/job共用有限的监督原语具有实际消费者；独立worker的单一调用者也有明确的隔离/停止理由。新进程带来的启动和收集成本尚无产品测量，当前不作性能收益判词；不需要为设计补重复CI或算术同形测试。

探针原件由评审者只读核对，未重跑。读取了 `process-probe-prototype.py`、生成的 guardian、三例 budget/stage/进入记录、两次入口的stdout/stderr，以及 `result.json`。六份guardian原stdout逐字段等于汇总中去掉观察字段的结果；生成guardian与保存脚本逐字相等。脚本直接调用 `processes.run(supervised=True)`，在已消耗准备延迟后按固定 `work_deadline` 设置一次外部停止计时；监督逻辑没有重新授予原完整额度。

|原件场景|准备延迟|总额度/清理预留|从首次起点至guardian完成|首次采样身份|重复入口|
|---|---|---|---|---|---|
|另建session且忽略TERM的孙进程|0.8秒|3.2/1.0秒|2.261秒|3|工作截止后拒绝启动业务child|
|被真实flock阻塞的stage|0.8秒|3.2/1.0秒|2.314秒|2|工作截止后拒绝启动业务child|
|入口已过期|1.1秒|1.0/0.3秒|1.148秒|1（仅guardian）|拒绝启动业务child|

detached记录的孙进程PID172059与采样中的同PID/start_ticks `250356718` 对应；blocked stage PID172068在采样中，未产生 `lock-acquired.json`；expired例没有 `stage-entered.json`。三例两次入口的 `manual_cleanup` 和 `live_after_observation` 均为空，r2脚本在观察者代清理时明确断言失败。前两例在总额度内完成停止；第三例本来已超期，只证明业务child未启动，不把1.148秒称为1秒预算内完成。重复入口均发生在工作截止之后，每次仍会启动观察guardian；它不证明截止前重复、并发或持久attempt幂等。

本地Git对象 `8e160b345adf9eac00fe4142c3fd74bc29a07e97` 的唯一父提交为产品基线 `f394945db894740ad23a81c62b4ad87c85a84511`，差异恰为 `docs/prototypes/six-stage-budget/` 下的script、observed-r2、provenance和README四件。Git内script逐字等于私有探针（SHA256 `437f333811bdc660fd0d16ca06e9ab3f017e23dcbf2e64f80adfc9355eba857d`），observed-r2逐字等于result原件（SHA256 `341438d2b6806da951c5dd51a561a98f8911f7ac4b0d76016602a68470d37313`）。provenance标为运行后来源捕获；其中 `processes.py` SHA256 `8b71a48351a8823bf712ad0735b369e829d3a259010ce8aebec6792b42269eb2` 与当前源码及产品基线相同。已核作者普通push的命令/退出0记录及原stdout/stderr；没有独立联网核远端。主开发HEAD仍为产品基线，prototype不进入主开发产品或CI。

这些原件支持继续采用“独立进程＋原supervised原语”的接缝，不能替代新prepare、真实Git、Temporal、slot或正式receipt门禁验收，也没有证明清理失败有界、不可中断I/O、任意daemon停止或异常时钟恢复。r1缺少独立观察者代清理计数的限制保留，不借r1证明回收。下一可执行项为 B2a 的持久prepare与完整准备消费者；新start仍须阻断至 B2c 的正式生命周期验收。B1 CI与本设计结论分开。
