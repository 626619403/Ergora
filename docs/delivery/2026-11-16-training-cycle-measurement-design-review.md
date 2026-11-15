# c1d 测量接受与索引：独立设计审查

日期：2026-11-16。审查对象为[详细设计](../plans/2026-11-16-training-cycle-measurement-and-index.md)，33144 bytes，raw SHA256 `30569b28e5369b8932b54d651b5c10b714f90c05977ebcd4ca2d2ee247acf369`。本 reviewer 为本片新独立上下文，按 `maintainable-project-delivery` 的 independent-review brief 与 `ergora-codebase-quality` 的 module-design／repository-style 检查原需求、实际源码和持久合同；没有参与该设计的编写。

**需求轴 approve／开放0；维护性轴 approve／开放0，仅为设计结论。** 未发现需要阻断此设计的具体可达漏洞，不提出产品修订或补跑全套测试。该结论接受所列版本隔离、认证位置和恢复策略；不认证 c1d 已实现、不开放 ordinal1，也不把文档中的未来验收节点记为通过。新活动名字／严格 wire 字段集合及必要纯校验提取仍须按设计 M0 在实施前固定并审查。

## 审查身份与边界

独立读取主项目的根及源码 AGENTS、当前 PLAN、组件变更协议、[原具体合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、[c1 总计划](../plans/2026-11-15-training-cycle-workflow.md)和[严格首轮设计](../plans/2026-11-16-training-cycle-workflow-first-round.md)。实际主树 HEAD 为 `c52fc0a338118a19491ad7cd458b82cf2f146a9b`，分支 `refactor/architecture-foundations`；方案第7行的 `879654c`／当时 clean 是作者调查时点，不能当作本次现场状态。审查时主树已有 PLAN、消费者及 Windows 交付文档差异，另有 Windows clock skip 审查及本设计未跟踪文件；它们均未由本 reviewer 修改。

独立重算方案列出的八项产品 SHA，全部与方案第13–20行一致：worker `d42d090b…`、protocol `b8f8c829…`、rounds `d4ca342b…`、evidence `1ffce17c…`、runtime `1183a95c…`、budget `d002c88e…`、execution `f6b4a1ab…`、cycles `07215a1b…`。因此本次邻接源码判断适用于该实际产品基线，没有把 HEAD 的文档／测试差异混作产品改动。

父任务告知 c1c 在专属树推进至 `fa78747`；本审没有检查或运行该树，不替代其固定源码、W0–W10、新包、默认 sandbox、正式 Workflow 与独立产品验收。前片 bcc／wheel55029、真实六活动及 native CPU 只作为历史范围背景；其中故意缺 evidence 的原 gate=false 仍为负例。自己的 CI 是否最终成功未在本审查询。

## 已核事实与设计判断

|检查点|实际源码／原合同|设计判断|
|---|---|---|
|原索引的权限与完整性|[rounds](../../src/ergora/training_rounds.py) `_COVERAGE` 明确 origin_authenticated=false、authorization_status=not_evaluated、promotion_approved=false；`read/_check` 核 schema、轮内容 SHA、父链接、相同 initial anchor，但不查 native 来源／实际 phase／ExecutionRecords，也不重读 previous 文件。|设计第31、67、79、88、96行保留低覆盖声明；完整前缀必须与实际已确认 previous 原件逐项相等，并通过候选顺序、注释、project/revision 与 `_COMMON` 绑定。不会把合法低覆盖 index 单独变成下一轮授权。|
|测量接受的四类事实|[evidence.inspect](../../src/ergora/reference_training_evidence.py) 核原 gate、SUCCEEDED、archive、evidence content address、manifest、baseline、comparator 及 files；明确 runtime_status=not_queried、artifact_content_status=not_read。[runtime.observe](../../src/ergora/reference_training_runtime.py) 对 RUNNING query 原 Status，对 COMPLETED 取固定 run、不 follow 的 Outcome。Outcome 有 report_uri，没有 evidence_sha。|设计第58–75行分别要求 accepted archive、native SUCCEEDED、真实允许 phase／outcome、durable stopped；绑定完整原 start/input/memo/run/job/request。终态用原 report_uri 绑定 gate-report，没有发明 outcome 字段。没有把 gate、SDK COMPLETED 或 local approval 单独当接受，也不声称重新读完 archive 中全部 artifact。|
|原执行链持久确认|[protocol.ExecutionRecords](../../src/ergora/training_execution_protocol.py) `load/request_record/observe(durable=True)` 绑定 request→launch→attempt→ack→stopped、原 intent/owner/start/receipt/native；对现有文件 fsync、目录同步、raw 重读，成功后才给两个 stop-confirmed=true。其当前算法不比较 inode。|方案第34、66、85行正确区分：复用原链合同；对新增 rounds artifact 的同 inode／同 raw 同步确认由 collect owner 实现，不误称原链已有 inode 检查，不由 PID 消失、S/H 退出、父 drain 或 SDK timeout 推出 stopped。|
|出生版本与旧历史|[cycles](../../src/ergora/training_cycles.py) 当前授权严格只接受 schema1/2，controller type/input、[binding/context](../../src/ergora/training_execution_protocol.py) 和 [runtime controller history](../../src/ergora/reference_training_runtime.py) 同样严格；原合同禁止既有 ID 补同意、重开 clock。|显式 schema3、`ergora-training-cycle-v2` 与独立 `TrainingCycleWorkflowV2` 是可行且局部的版本选择。保留 schema1/2 和 c1c 原类／原 command 序列，比放宽旧 binding 或用当前文件决定旧 history 是否多轮更易审查。没有要求 owner 或普通 execution chain 无故一起升版；既有 ID 不升级。|
|measurement source 的实际覆盖|`GATE_SOURCES` 已含 worker/protocol/budget/execution/runtime/submission/context/training/cycles/reference、schema／contracts／State／asset helpers，但不含 rounds、evidence 或 rounds schema。evidence 的原生 perfctl／adapter 仍由原安装及冻结 reference 身份约束。`owner_record/source_capability/validate_sources` 当前严格原 key 集合。|第43–50、73、96、98–100行要求在新授权中额外冻结这三个固定路径的完整 SHA，并在 H 前后、后继 intent 出生及 source/context/native 最后 gate 比较实际字节，不能恢复时重采 SHA。该三项补的是实际采集／验证缺口，既不改旧 capability key 集合，也不赋予 index 认证权；若实现引入其他接受权依赖必须先扩审，不能泛化任意路径 inventory。这里是待实现的接线义务，当前源码没有该能力。|
|H 与 native 的最后准入|[BudgetedStart.source/require_active/check_controller_history](../../src/ergora/reference_training_budget.py)、[Execution.check/current/request/admit](../../src/ergora/reference_training_execution.py)、worker 锁内 adapter 及 protocol.native_main 已分别持有原来源、父 RUNNING、原锁和 attempt/ack gate；当前 ordinal>0 没有前驱认证。|第92–102行没有仅依赖 Workflow 顺序：后继原 intent 冻结 predecessor；共用本地 validator 在各原最后动作核完整前缀、前轮 archive／stop、原 source 和 clock。最多32层原 intent 递归保留更早认证，不能以较短 prefix 降级。native 不查询 Temporal，而核原 H 当时 phase 观察的不可换绑本地前置；该范围准确，未称 native 可认证实时 phase。|
|发布、恢复与唯一机会|[rounds.create](../../src/ergora/training_rounds.py) 只重采新增轮，保留 previous 原轮值；完整序列化后整体核 10MB/32轮；[publish_directory](../../src/ergora/asset_trees.py) 无覆盖 rename，没有 fsync。worker 已有实际 operation/helper/observation.json 归档位置。|第75、79–90行的额外观察文件是原 operation 证据，下一 H 要重读原件，不能自称批准或独立权威。collect 唯一可能发布机会由 history 在 command 前消耗；丢回复、目标缺失、新 operation ID 不返还机会。已存在目标只读确认同 artifact；同步后重读／最终接受不过则保留 unconfirmed。额外 fsync 局限新 collect，不静默改变所有目录发布者语义，也没有另建 index-attempt 账本。|
|资源、预算与容量|原合同要求祖先资源累积、权限收窄，原六阶段及人工 release 不变；c1c 给出一次 BOOT 授权、保守 D_work/D_total、活动及 history 界。原原生 reader 还有自身较长 timeout。|第39、102、117–130行要求读／RPC／rename／fsync／回传共用 operation window；不在 SDK loop 做存储，不持 SQLite 跨 RPC，父共享许可及 stop 独立 writer 不变。10,000,000B完整累计 index、32轮、完整编码32768B、memo2KiB、每轮256 ordinary command 和8000events/8MiB分别保留；不以32×256保证容量。没有资源模板或 grant 变更，不新增执行权、release、baseline 迁移或自动 integration task。|

## 维护性结论与实施约束

collect 的业务组合放在现有 worker 的 `_cycle_operation` 私有实现是合适的：真实消费者就是 SDK collect／对账，经既有 S/H 监管；删除这个组合会让调用者重新承担 evidence/runtime/stop/index 的顺序和原件一致性义务，并非只做转发的新模块。Workflow 只消费固定投影与准确 refs，原 evidence 保留 archive 语义，rounds 保留完整索引与离线读取，budget/execution 保留执行生命周期，所有权清楚。

纯前驱 validator 放在已 pin 的 protocol 有 budget、execution、worker 和 native 等不同生产文件的实际消费者；不是为虚构复用建框架。保留 stdlib-only／隔离 native 的限制是必要条件。设计明确禁止复制 evidence/comparator；若实现需要从 rounds/evidence 提取纯算法，应先证明真实隔离需求并复审原 owner 的最小提取，不把“实现时再说”当作已允许复制一套 reader。新增 pure validator 也不得反向引入 State、jsonschema 或 SDK。

本审开放 finding 为0，没有要求方案新增类、模块、配置开关、表或额外证据账本。以下是设计已声明、仍需履行的交付前置，并非本次发现的新漏洞：

1. M0 固定新活动名字／版本及严格 request/result/binding/predecessor 字段集合，区分 c1c 已有 activity v2 与新 Workflow/program v2；用原 owner 的版本分支实现，旧名字含义不放宽。本审未审不存在的最终 wire 表。
2. 实现时逐个核 schema_version==2 分支、actor、controller type/queue/input、ready/permission 与 source/context/native 路径是否纳入 schema3；不能只修改授权 writer 或只删除 ordinal0 guard。设计已把这些列入同片影响范围与 M1/M5。
3. M2–M6 核真实交错、同 artifact 恢复和最后 gate；新纯算法提取若超出本设计给出的最小绑定职责，应先复审提取方案。M7/M8 才提供新包、正式 V2 的实际两轮及真实恢复证据；CPU只验控制／数值 oracle／原 gate 合同，不能认证真实 GPU/ML 质量或累计统计收益。

## 事实、推断与未验范围

已核事实是本报告的文档字节／SHA、八项产品 SHA、上述函数及实际调用位置、原格式限制与持久行为。设计可行性及未见可达授权绕过是基于这些源码的静态判断；不是运行反例或实现正确性证明。设计包含准确的既有 API 缺口，没有把未来 source/predecessor 校验、同 inode index durability 或真实两轮说成已存在。

本审只做只读源码／文档／Git 状态及 hash 检查，并仅创建本报告；未运行测试、服务、安装、模型、训练、网络或 Git 写入，未修改产品、测试、方案、他人报告或 PLAN。报告相对链接及审查对象身份另做本地静态检查。后续产品按 M0–M8 的适用接缝验收，不因本次设计 approve 继承旧 wheel、旧测试 Workflow、前片 CI 或 c1c 的运行结论。
