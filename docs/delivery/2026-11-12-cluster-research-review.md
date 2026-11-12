# R8 集群运行与恢复研究独立审查

审查日期：2026-11-12。审查者：fresh-context 独立 reviewer（`cluster_research_review`）。按项目 `AGENTS.md`、当前计划及 `maintainable-project-delivery` 的 independent-review brief 执行；未继承作者的研究过程或预设结论。

## 当前结论与候选身份

同片修正复核已完成：**Spec 通过，Standards 通过，开放 finding 0／0；R8-SP1、R8-SP2 均关闭。** 本结论绑定修正后的完整 R8 研究稿：22,415 字节，SHA-256 `d9419364dc0c2c25876d715dd2640a370672535d2a8aef5755374476fb799b9a`。仓库检查点与产品基线均保持下述身份；修正只完善研究与后续准入合同，没有据此宣称运行适配或硬件验收完成。修正内容及实际复核见本文末节。

## 首审范围与结论

仓库检查点为 `42902bbe1af59059b287a38f0c9efa51a72dca4b`，产品基线为 `5ab6d350024de8515487d0bedb3b950be60ac867`。唯一受审候选是未跟踪的[完整 R8 研究稿](../research/2026-11-12-optimization-cluster-agents.md)，18,508 字节，SHA-256 `a11408ec35d58ef35762790641dfa21a3ed191e3a9fac237aadac41991b65012`。读取了当前 `docs/PLAN.md`、[本片计划](../plans/2026-11-12-specialist-template-refresh.md)及交付记录中的相关状态；工作树其他报告与计划改动不属于本次审查。没有提前审查 D0 或 X1–X3。

- **Spec：需修正，开放 2 项 P2。** 实际 agent、库／执行器、完整流程的区分，以及研究与硬件验收的区分基本准确；但 Slurm Templates 的关键漂移尚未展开，内部模型会话的父资源／权限传递也尚未成为准入门禁。
- **Standards：本次文档范围通过，开放 0 项。** 报告没有建立第二调度器或正式账本，没有把设计稿、主线源码、实际安装和硬件执行混写为同一种证据。此结论不替代上述 Spec 修正，也不代表任何执行适配已经可用。

## Findings（首审记录，现均关闭）

以下原始发现、严重度和最小修正保留首审候选的身份与行号；原链接所指工作文件已经修订，当前修正定位见末节。

### R8-SP1 · P2：尚未核清声明覆盖的 Slurm 模板与主 Skill 的启动形态差异

位置：[研究稿第 3 行](../research/2026-11-12-optimization-cluster-agents.md)、[第 17 行](../research/2026-11-12-optimization-cluster-agents.md)、[第 78 行](../research/2026-11-12-optimization-cluster-agents.md)。研究稿声明按 Multi-Node Slurm／Slurm Templates 拆分，却没有记录实际启动形态，也没有引用或分析该 Skill 指向的 `references/templates.md`。既有证据集中只有主 Skill，缺少该模板原件；本次仅为这个缺口补取一次固定提交的公开 GET，HTTP 200。

同一 Bridge 提交 `55694838ce73cd23b00ff95bd00512aefb963ce0` 中，[主 Skill 第 16 行](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-multi-node-slurm/SKILL.md#L16)要求经过 Bridge `initialize.py` 的脚本优先使用 srun-native：Slurm 直接生成每 GPU 的训练进程；torchrun 路径则每节点只启动一个 launcher。主 Skill 还明确警告混用两者会把 8×8 变为每节点 64 个进程。[复制模板第 18 行](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-multi-node-slurm/references/templates.md#L18)仍为 `ntasks-per-node=1`，其名为 Bridge-Specific 的[命令体第 95 行](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-multi-node-slurm/references/templates.md#L95)仍使用 torchrun。这是需要按实际训练入口选择的文档漂移，不能把两份示例拼接成统一启动模板。

后果：后续“复用成熟提交入口”若直接复制模板或只保存笼统的 `resolved launch`，可能重复生成 rank、造成端口冲突；共享 `NEMO_HOME`、cache 和 container mounts 的要求也没有成为模板适配输入。作业获得 Slurm ID 并不能证明这些多节点合同正确。

最小修正：增加一小节及固定模板引用，说明两种启动形态、适用入口和进程数量关系，明确模板示例中的 8 是示例配置；补充所有节点共享路径／相同挂载及单进程预热阶段。把“生成的 launch 只能有一个 rank 生成所有者、配置下 nodes×每节点训练进程与 world size 一致、实际入口适用性已核”加入后续静态验收，再将全 rank 启动留给有权限的集群验收。无需本轮执行上游命令或修改上游模板。

### R8-SP2 · P2：原生流程内模型会话的继承与权限仍缺少可拒绝的准入条件

位置：[研究稿第 62 行](../research/2026-11-12-optimization-cluster-agents.md)、[第 64 行](../research/2026-11-12-optimization-cluster-agents.md)、[第 66 行](../research/2026-11-12-optimization-cluster-agents.md)、[第 74 行](../research/2026-11-12-optimization-cluster-agents.md)。报告正确保留 NVRx 的内部政策与恢复所有者，也要求单独配置模型 route／外发许可，但没有说明如何把父级资料、Skill、上下文送入每个内部真实模型会话，或原生接口无法传递时如何拒绝准入。只读日志副本、路径权限说明和 route 配置不能自动满足这项原始要求。

固定 NVRx 源码提供了具体反例：[`RestartAgentRequest`](https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/restart_agent/models.py#L425)只有 `log_path`、`job_id`、`cycle_id` 和 schema；[MCP 模块](https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/mcp_integration/module_definitions.py#L40)据此构造请求，没有 Ergora 父资源或 grant 参数；[L1 prompt](https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/restart_agent/l1/prompts.py#L18)自带日志证据任务与工具合同。支持配置化多模型的 [`build_restart_agent_runtime`](https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/restart_agent/agent_runtime.py#L527)又会在内部建立 model routes；外层叶接收完整 manifest，并不证明这些内部调用收到同一份资源或相同的权限上限。本仓库现有 [`workflow_definitions.py`](../../src/ergora/workflow_definitions.py)对结构内已知叶累加资料、检查权限和材料预算，也不能据此推导未知上游内部会话已经被覆盖。

后果：按目前建议接入带 L1 的原生流程，可能在外层叶满足继承检查后，内部模型仍只获得日志、使用独立 route／工具／请求预算。现有“先只读归因”的表述不能区分确定性工具与含内部模型的完整流程是否满足父级合同。这是拟议适配的准入缺口，不是本轮已经发生的权限越界。

最小修正：在最小子模板／验收中明确：所有内部实际模型 routes／sessions 都必须获得完整、固定身份的祖先资源，并记录实际发送输入的全文读取证据；工具、路径、网络和外发许可取全部父级上限，内部重试／模型用量归属原任务总预算。保留上游内部分析、历史与政策所有者。无法通过成熟接口传递并核验这些条件时，带模型的完整流程继续 unsupported；首片可明确采用 deterministic-only 接口，或先补有真实消费者的最小传递能力。容量不足必须拒绝，不能靠摘要替代完整继承。本轮无需实现该能力，但研究稿需要写清准入与未支持边界。

## 首审独立核查结果

以下结论来自原件与源码核对，并非重复采用作者判词：

|项目|核到的证据与适用范围|
|---|---|
|证据身份|重算既有 34 份 HTTP receipt：30 份 200、4 份 404，字节数及 SHA-256 均匹配；保留失败原件。NVRx tar 为 1,622,975 字节，SHA-256 `9c21e058929623b89525deaeb2fae5177639c7362622492495fec5ce124af478`，两份选择索引的 8 个文件与归档成员逐字一致。补取的固定 Slurm 模板为 4,744 字节，SHA-256 `215a6a6d6cefb8ade44ad00ca75836551bff9e2e911f69d323ff6887e1121413`，另存回执。|
|版本／许可|核对固定 URL、四项目 HEAD 观察记录、NeMo Run 0.13.0 和 Python≥3.10、Submitit Python≥3.11、NVRx README 支持表与 pyproject 的区别；Run／NVRx／SkyPilot Apache-2.0、Submitit MIT 有原件支持。四份 HEAD 记录是作者已完成命令的观察汇总，本次没有重新执行网络 Git，也不称独立实时 HEAD 核验。Slurm 26.05 是站点文档观察，未据此认定站点集群版本。|
|NeMo Run|`Experiment.from_id`、任务依赖、status／logs／cancel 确有实现；local status 常为 UNKNOWN，detach／DAG 支持随 executor 变化，报告没有把本地执行扩大成远程能力。`from_id` 还依赖原 Experiment 持久目录；`cancel` 捕获并打印异常，因此适配验收仍须观察原生终态，不能仅取调用返回作为已停止证据。|
|Submitit|checkpoint 文档确实限定首个 task 调用 hook，区分无 hook 的 preemption 与 time limit，且 preemption signal 依赖站点配置；序列化 callable 的重排队不能证明分布式模型、optimizer／RNG／sampler 恢复。报告的区分成立。|
|NVRx|Restart Agent 有实际 CLI、MCP 和核心源码，并非只有设计稿；官方将其标为 experimental。默认 history、先确定性发布、可选模型证据、deadline／closed attempt、空日志 degraded 的陈述有支持；MCP 模块本身不执行 restart。根 ARCHITECTURE 同时包含 proposed controller，legacy LogSage 源码专用边界也有明确原件。Bridge 的 Slurm-only 文档、旧 Skill non-Slurm 提示及已弃用 in-process API 没有被合并为实测支持矩阵。|
|SkyPilot|Managed Jobs 固定实现确有原 request 采用、恢复、取消和退避；Agent Sessions 官方文章日期和 limited early access 表述均匹配，INSTALL 的技能路径差异也存在。另核到 `launch(max_retry=None)`、恢复循环，以及 `recover_on_exit_codes` 可绕过用户错误重启计数：原生用户错误预算并非总预算。报告已把外层总预算交还 Ergora；D1 仍须核实预算耗尽后的原 ID 停止／unknown 对账及资源占用证据，不能把该研究当作预算已受控。|
|Slurm 与授权|官方原件支持 parsable ID、requeue 从脚本开头重跑、失败 dependency 不因前驱重排队自动修复、REST 认证与默认 JWT 过期；普通用户权限、站点 REST 启用和管理员部署职责的区分恰当。|

实际检查仅包括本地 Git 身份／状态、报告全文与本地链接、原件与归档哈希、固定源码及相关现有资源编译边界的只读核查，以及上述一次公开 GET。R8 的三个本地 Markdown 链接在终核时均存在。未安装或 import 上游包，未执行上游测试／CLI、模型、Slurm／SkyPilot 作业、GPU／多节点实验或故障注入；未核验任何真实账号、配额、认证或远端取消结果。没有提交或推送。

首审阻塞研究稿关闭的是 R8-SP1、R8-SP2 的文档修正与同片复核；缺少集群硬件本身不是本次研究不通过的理由。后续运行适配仍按报告的 CPU／离线、获授权集群、GPU 故障恢复三级分别验收，不能提前关闭未运行层级。

## 同片修正复核

同一 reviewer 于 2026-11-12 重新读取了修正后研究稿全文，并只读重核受影响的固定来源。此次不是新 fresh-context 首审；没有继承新的作者讨论，未扩大到 D0／X 或其他报告。精确候选为 22,415 字节，SHA-256 `d9419364dc0c2c25876d715dd2640a370672535d2a8aef5755374476fb799b9a`。

|原 finding|修正与独立复核|处置|
|---|---|---|
|R8-SP1 · P2|[新增 Slurm Templates 小节](../research/2026-11-12-optimization-cluster-agents.md)明确同快照主 Skill 与复制模板的差异，以 N／R 参数区分 srun-native 与 legacy launcher；要求唯一 rank 生成所有者、实际初始化入口和 world size 关系，并把配置静态核对与全 rank 集群启动分开。共享 repo／data／logs／cache／NEMO_HOME、相同容器映射和单进程 cache 预热已明确；[最小合同](../research/2026-11-12-optimization-cluster-agents.md)接住这些输入。重读固定 Skill、模板及各自回执，字节数与 SHA 保持一致，结论与来源相符。|关闭：文档最小修正充分。|
|R8-SP2 · P2|[新增内部模型准入段](../research/2026-11-12-optimization-cluster-agents.md)明确原 request／MCP 不自动传递父资源与 grant；要求逐实际 route／session 注入完整固定祖先资料、保存真实输入与读取证据，按全部父上限限制工具／路径／网络／外发并纳入原任务总预算。未支持传递、未知会话或容量不足时拒绝对应模式，首片可限 deterministic-only；[通用准入条件](../research/2026-11-12-optimization-cluster-agents.md)覆盖所有职责，并保留原内部政策与恢复所有者。重读归档内 request、MCP、L1 prompt 和 runtime route 构建源码，新增引用与所述缺口相符；未把将来必须实现的能力写成已有能力。|关闭：研究适配边界与验收门槛充分。|

实际复核：确认本地 HEAD 仍为 `42902bbe1af59059b287a38f0c9efa51a72dca4b`；重算修正稿及固定 NVRx tar 的 SHA-256，归档仍为 `9c21e058929623b89525deaeb2fae5177639c7362622492495fec5ce124af478`；读取上述受影响原件。修正稿的 33 个 reference 定义、53 次引用使用、三个本地 Markdown 链接及行尾空白检查无问题。当前审查报告的本地链接与空白也已检查。此次新网络请求 0、上游安装／import／执行 0、模型／集群／GPU／故障注入 0；没有提交或推送。

修正后完整研究稿在本次范围内无新增 finding。首审版本、两个 P2 及证据范围保留；当前研究关闭不授予后续产品适配、真实内层会话继承、原生停止／unknown 恢复或多节点收益的执行验收。
