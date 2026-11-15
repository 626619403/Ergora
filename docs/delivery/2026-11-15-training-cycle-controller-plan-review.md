# Q4.2c 控制器准备草案独立计划审查

日期：2026-11-15。审查者：fresh-context 独立 agent `training_cycle_controller_plan_audit`。范围为 [控制器准备草案](../plans/2026-11-15-training-cycle-controller.md)，即 c0.1 之前的源码问题、边界、分片和验收顺序；本文不固定新字段或 CLI，也不认证控制器实现。原始要求、前置状态和读写权限由主执行者直接提供，未继承实施对话；本审查没有改写 B3.3c2 或其独立终核报告。

## 两轴结论

|轴|计划层结论|适用范围|
|---|---|---|
|需求符合|approve|可继续 c0.1 的源码合同调查与具体设计；本次准备草案阻塞 finding 为 0|
|维护性|approve|保留原用例、Temporal history、预算／执行／证据 owner 的方向可行；本次准备草案维护性 finding 为 0|

草案保留了先梳理算法／依赖、去耦合去冗余、原 baseline 与质量合同、每轮原件，以及 v3 路径中的 kernel 专家。首版只消费明确选择的有限既有实验，候选生成、baseline 晋升、采用与人工 release 仍各有原入口。它明确要求独立自动执行同意、原 clock、单次 start／launch、unknown 对账、父停止的晚到准入及历史协议兼容，并将具体字段、调用点和容量策略留给 c0.1 及新的独立设计审查。按这一准备性范围，没有发现需要先修改草案才能继续调查的实证缺陷。

后续产品门禁仍按草案顺序执行：B3.3c2 的精确发布、自己的 CI 和原 reviewer 终核先闭合，再固定实施 baseline；c0.1 具体合同通过独立两轴审查后，才实施父停止／执行同意和自动派发。此结论不向这些门禁转授通过状态。

## 固定输入与检查范围

Git 基线为 `75285e3271bb93271eaea050ca7812cb0cd98b5a`，分支为 `refactor/architecture-foundations`；审查开始时 c2 为未提交工作树。被审草案为 9,139B，完整 SHA256 为 `7ec53f1f2adc758b555b38842cff37e311eb3741cb4eb5188e54dc9158391a8c`。

已读根与源码目录 `AGENTS.md`、[总计划](../PLAN.md)、[组件变更协议](../architecture/component-change-protocols.md)、[有界循环总计划](../plans/2026-11-15-bounded-training-cycles.md)、[受管执行计划](../plans/2026-11-15-training-managed-execution.md)及[执行记录合同](../plans/2026-11-15-training-execution-records.md)，并应用 `maintainable-project-delivery` 的 independent-review 和 `ergora-codebase-quality` 的 repository-style／module-design／test-seams reference。

直接检查 `training_cycles`、`reference_training_worker`、`reference_training_budget`、`reference_training_execution`、`training_execution_protocol`、`training_rounds`，及实际 start／runtime／cancel／evidence／release／project context 用例、原 native adapter／executor、版本化 admission delta、原 ExperimentWorkflow／Activities／models、原 comparator／perfctl 和两份 cycle／round schema。

共保存草案及 23 份产品文件的只读快照（329,795B）到 ignored `.ergora/checks/training-cycle-controller/plan-audit/`，清单为 `source-manifest.json`，SHA256 为 `a302d8220ec194d4cdefc7c01851c208c28574d0e475a2db944dcdc8b5d30007`。已核这 23 份源码逐份匹配 r6 core／SDK 两份包清单，且审查时未偏离快照。两份既有清单均记录 652 份产品及 source／wheel／installed 相等，wheel 为 `f1106d11b7c6b074b5f35c5a3d96208267735536cbdd549a6dbbb577f6c93a44`；这里只核设计输入身份，未重新执行整包、283 参考、产品验收或 CI。

## c0.1 必须落地的源码调查与验收

下列内容细化草案已经声明的后继义务，作为具体设计审查的输入；它们不是对尚未实施功能的产品 finding。

|问题与实际源码事实|c0.1 最小可审交付|后续行为验收|
|---|---|---|
|**总投递与明确执行同意。** [原 dispatch](../../src/ergora/reference_training_submission.py#L214)在查全初始输入后写唯一 attempt，再次 preflight／预算检查才投递；[原恢复](../../src/ergora/reference_training_submission.py#L284)核同 history／memo，未找到也不重发。[现有 authorize](../../src/ergora/training_cycles.py#L367)只冻结预算与 ready；[execute 请求](../../src/ergora/reference_training_execution.py#L58)另确认精确 revision／intent／run／native request。|给出总 Workflow 的稳定 ID、完整初始 input／memo、intent→attempt→receipt 和 lost-ack 对账调用点；明确操作者对有限列表的同意如何允许控制器为实际原 run 准备精确 execute 请求，且普通 authorize／读取／恢复不会产生该同意。复用原单实验客户端与记录，不复制另一套每轮 start／signal 实现。|总投递或 execute 回复丢失、重复 activity、服务重启，均保持同一总投递身份及原实验 attempt／run／launch；旧 cycle／owner 不因新入口获得自动执行许可。|
|**父停止的线性化边界。** [预算 require_active](../../src/ergora/reference_training_budget.py#L312)目前核原授权／owner／clock；[worker lookup](../../src/ergora/reference_training_worker.py#L34)在原 adapter 的 [registry lock 内 create](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L123)调用。另一个 [native active](../../src/ergora/training_execution_protocol.py#L436)在 attempt／ack 同步前后核 fence／owner／clock。仅在 activity 外层检查停止文件会留下后续创建窗口。|列清停止事实的作者、完整授权身份、普通文件与无覆盖持久化、可见与 durable／unknown 语义，以及 start、registry 锁内创建、executor 锁内最后 gate 各自与停止发布的先后关系。证明已生效停止事实如何阻止晚到 RPC／已排队 activity／已发布 execute 请求继续；明确哪些已获准工作转入原精确回收。|实际交错停在最后检查前后、持 registry／executor 锁、attempt／ack 同步和父取消后晚到的 activity；停止发布受阻时结果保持 unknown。活动子树沿原通知／唯一 reaper 清理，停止派发与远端取消确认分别观察。|
|**停止通路的依赖与阻塞。** [原 worker](../../src/ergora/reference_training_worker.py#L56)只注册 ExperimentWorkflow 和原 Activities，最大 activity 并发为 8；原 adapter 的 async 方法内仍有同步锁／文件操作。c2 的 [owner／S 监管](../../src/ergora/reference_training_budget.py#L222)通过独立进程隔离这些操作，S 的停止谓词只观察原 clock／进程／catchable signal。|画出实际 Workflow、activity、阻塞应用用例、helper 和停止 writer 的调用边界；确定注册／queue 及各 activity 的重试／超时／取消合同。新停止事实的发布和活动执行的停止不能依赖一个被原锁或 I/O 卡住的 event loop；保留 c2 父 owner 不读取业务磁盘的监管边界。|在真实锁／存储阻塞和 worker／server 重启下，父取消或原 deadline 仍能停止新派发并驱动原独立回收；仅取消 future 不算通过。|
|**严格历史协议兼容。** [owner reader](../../src/ergora/training_execution_protocol.py#L106)对 schema／capability 字段及 `GATE_SOURCES` exact set 严格检查；[完整 cached context](../../src/ergora/training_execution_protocol.py#L360)也有 exact 字段和出生 SHA。新增来源 key 或父级字段可能让既有 reader 直接拒绝旧原件，单改当前源码也会触发 live source 漂移。|逐项核现有集合是否已覆盖父停止谓词，选择原 owner 内最小改动；确需新增协议时给出明确版本读分支、出生能力和旧活 owner 处理。将离线原链读取与当前来源／live 执行准入分别固定，禁止回填旧记录。|原 schema1、c2 schema2 链、缺所选安装、来源漂移均可按其原合同观察；旧原件逐字保持。新代码不能据旧出生能力启动新动作。|
|**测量完成、实际阶段与 release。** [completion](../../src/ergora/reference_training_budget.py#L513)读取 native 终态／gate，并另核 managed durable stop；它未查询原 Workflow。原 Workflow [GATING→AWAITING_RELEASE](../../src/ergora/data/reference/platform/upstream/temporal/perf_temporal/workflow.py#L132)有独立时间窗，随后仍可能接收取消、批准或到期。[runtime](../../src/ergora/reference_training_runtime.py#L11)才核完整初始输入与精确 run。|给出允许进入下一轮的证据绑定：原 receipt／history／memo、job／binding、native result、durable stop、原 gate／accepted archive／evidence SHA 和实际 workflow 阶段；规定查询交错／unknown 的保守结果。总循环完成或取消只清理活动轮，保留已成功测量轮的原人工 release；若考虑 child Workflow，必须明确 parent-close 行为。|result 已写但后代未 reap、native 已完成但 Workflow 尚在旧 phase、原取消与 gate 交错、前轮等待 release 时后轮停止。均不凭 control 或 native 单一终态继续，也不自动 approve／统一 fence 既往成功轮。|
|**可信分类与统计边界。** [comparator](../../src/ergora/data/reference/platform/upstream/compare_runs.py#L152)确有 PASS／FAIL／INCONCLUSIVE、固定样本区间及不支持多次搜索校正的声明；[perfctl gate](../../src/ergora/data/reference/platform/upstream/perfctl.py#L112)将质量／证明／比较等失败抛出，原 [executor 失败报告](../../src/ergora/data/reference/platform/local/agent_platform/training_executor.py#L89)会合并成 archive／gate 拒绝；[evidence reader](../../src/ergora/reference_training_evidence.py#L40)对未通过门禁不提供 accepted archive。|固定“原报告字段→继续／停止／原因未知”的表及各字段的可信来源。成功的原 archive 可保留完整 performance；不能从 `GateDecision.summary`、自由文本或未通过原门禁的候选自述推断质量退化／无收益。冻结继续条件，并将原格式不足作为显式能力缺口。|成功、原门禁拒绝、无证据／不完整证明、比较 FAIL／INCONCLUSIVE 的原件各自留存；只能保留原来源足以证明的分类，不能修改统计样本／容差或声称累计显著收益。|
|**容量与每轮留存。** [cycle schema](../../src/ergora/data/schemas/training-cycle-v1.json#L20)允许最多 32 个有序候选，budget 当前只有 wall／cleanup／control timeout；候选顺序与唯一 attempt 决定有限试次。[rounds.create](../../src/ergora/training_rounds.py#L116)将 records／evidence／submission／approval 完整嵌入新不可变报告，不只是 SHA 列表，并在完整序列化后才核 10 MB。它还会调用当前 project 的公开观察用例。|列出真实部署 Temporal 的单 payload／history 界、controller 每次输入／结果的有界身份引用、索引实际字节预算和结果超限时的停止／留存规则。核 cycle 的 change／next_bottleneck 到原索引的映射，以及项目漂移时哪些既有观察可使用冻结来源、哪些只能明确报告缺口；不预建另一套实验账本或本地可变轮次状态。|接近 32 候选／10 MB、完整单轮结果逼近容量、追加索引失败、当前项目发生真实漂移与 history 恢复。原实验数据／报告始终保留；超限停止不截断，旧索引不改写，不能用索引离线完整性代替实时成功或授权。|

c0.1 的下一步可直接执行：以 c2 闭合后的固定源码和原格式为输入，给出上述记录／调用点／分类／容量决策及最小受影响文件清单，标注哪些原 owner 无需修改，再提交新的具体设计两轴审查。字段与 CLI 在这一步固定符合草案当前定位，无需为本次准备审查伪造实现或动态通过证据。

## 实际检查与限制

本次仅执行只读 Git 状态／分支／最近提交、文档与源码读取、原格式／调用关系核对、23 份所读产品文件与既有 r6 包清单的 SHA 比对，以及报告本地链接检查。私有原件包括 `source-manifest.json`、`package-inputs.json` 和 `identity-checks.json`。唯一公开写入为本报告；未修改产品、测试、依赖、Git、总计划或其他报告。

未构建／安装包、启动服务、执行模型或训练、运行产品 suite、昂贵验收或 CI。本审查不复核 c2 产品 finding 的关闭状态，不宣称 283 冻结参考的新验收，也不认证 CPU 训练质量、真实 ML／GPU 或收益。安装后的两轮 CPU 示例和真实 B3 的独立 workload／质量 oracle／设备条件继续按原后继计划验收。
