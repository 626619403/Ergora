# 优化多 agent 编排、实验资源与证据闭环

核对日期：2026-10-26。本文是供总报告合并的设计与审查材料，不是已部署系统。已读取两份用户 WAM 经验附件、旧 `build_quickstart.py` 和当前最小台账 `perf-build/perfctl.py`；不重复优化方向技术调研。下述工作流是针对这些材料提出的设计，官方平台能力依据列在文末。

## 1. 角色保持少，权责保持清楚

默认是一个协调者，按任务短时启动方向 agent；独立计量和数值审计是不同职责，可由同一名独立审计者在小项目中承担。人类担任唯一基线集成人；方向 agent 不能各自宣布一套“最新最优”。

| 角色 | 输入和产出 | 权限边界 |
|---|---|---|
| 协调者 | 当前基线、瓶颈、历史负结果 → 有界假设、任务依赖、实验计划、状态与交接 | 可申请实验、分派与停止任务；不能自行把缺失验证改成通过 |
| 按需方向 agent | 一个假设与允许改动 → 独立提交、最小复现、自检、资源需求、继续/停止建议 | 专属 worktree；不写其他任务、基线指针、受保护计量程序或阈值 |
| 独立计量审计 | 冻结候选与对照协议 → 在独立 runner 上取得原始观测、检查污染、重算结论 | 不修改候选以帮助其通过；使用受保护采集器、比较器与固定策略 |
| 独立数值/训练审计 | 契约、候选、参考、检查点 → 数值与训练质量证据，明确未覆盖部分 | 不把有限 loss、短测通过或作者自述改称收敛结论 |
| 唯一基线集成人 | 当前组合、独立证据、回退包 → 批准采用或拒绝，更新一个基线版本 | 只有此角色可推进正式基线；签字绑定候选/证据摘要，不批准模糊的“这次实验” |

“独立”首先指权限、执行来源和数据来源的分离，不是换一个模型名称。独立审计者可以使用与作者相同的模型，但必须拿到冻结代码、契约和原始输出，不能只复述作者总结。人不必通读全部实现，必须能看到：改了什么、不允许改变什么、完整更新收益、质量验证范围、实际运行证据、剩余风险与回退。

旧快速上手的 worktree、候选提交、只读审查、CI、人工合并应保留；优化场景额外需要资源归属、实验重放和统计口径。Git 分支隔离不提供 GPU、端口、共享内存、数据库、缓存或网络隔离。

## 2. 分开记录“候选是否值得采用”与“某次作业是否完成”

不要把 issue 的 Done、进程退出、调度器 Completed 和实验验证 PASS 混成一个状态。

### 候选生命周期

| 状态 | 进入条件 / 必需产物 | 退出条件 |
|---|---|---|
| DRAFT | 假设、目标负载、E/N/A 类型、允许改动、预期收益机制 | 人确认可改变的语义边界；基线和验收规则可执行 |
| EXPLORING | 一个方向任务、独立提交/工作区、资源上限与筛选计划 | 原始结果完整；得出停止或继续的理由，不以“agent 已结束”推进 |
| SCREENED | 局部正确性与筛选达到事先约定要求 | 冻结 candidate SHA、配置和产物，进入组合队列 |
| INTEGRATING | 明确 parent baseline、候选补丁集合、实际组合 SHA、独占验收预约 | 组合功能、数值、完整更新计量通过；失败拆组定位 |
| CONFIRMING | 需要覆盖的长程事件、步数/样本/时长、质量标准与恢复计划 | 约定的长程和质量证据齐备；允许无需长程的范围须在合同中预先写明 |
| READY_FOR_REVIEW | 当前组合、当前基线、独立证据、回退包均一致 | 唯一集成人针对确切版本批准采用或拒绝 |
| ADOPTED | 基线变更记录、parent baseline、正式代码/配置、证据引用 | 后续回退记为 REVERTED；旧记录永久保留 |

任一步可进入 BLOCKED、REJECTED、STALE 或 CANCELLED；给出原因、负责人和重开条件。STALE 不是删除结果：旧结果仍能解释当时的实验，但不能证明对新基线的收益。不要因基线更新抹掉有价值的负结果。

### 作业 attempt 生命周期

`PLANNED → SUBMITTING → SUBMITTED → RUNNING → SUCCEEDED / FAILED / CANCELLED`。

提交或取消响应不确定时进入 `RECONCILING`，核对平台事实后再推进；不能把超时当作“没提交”或“已取消”。一个 experiment 可以有多个 attempt，attempt 只追加，不覆盖失败运行。一个 attempt 可含若干基线/候选配对运行；每个运行还有独立 run ID。

最小持久字段：

```text
experiment_id, manifest_digest, baseline_generation, baseline_id
candidate_commit, integration_commit, parent_candidate_ids
attempt_id, run_ids, phase, retry_owner, retry_budget
submission_key, requested_spec_digest, submit_intent_time
scheduler, cluster, job_id_or_uid, submit_time, restart_or_pod_identity
resource_lease_id, holder_epoch, heartbeat, allocated_nodes_and_devices
container_digest, effective_config_digest, data_checkpoint_refs
command, collector_version, validator_version, output_uri
observed_state, exit_codes, raw_artifact_digests, decision_receipt
```

冻结配置摘要必须来自最终生效配置，而不是只哈希启动命令或某个 YAML。数据/检查点的摘要必须能找到对应对象；只有 64 位十六进制字符串不能让人重新运行。

## 3. 并行探索，独占验收

分成两个资源队列：

- 探索队列：只读调查、代码实现、CPU 检查和已隔离的局部 GPU 实验可以并行。其数值或速度结果必须注明测量范围与共享资源情况。
- 验收队列：组合对照由唯一计量 runner 获取所需节点/拓扑的排他预约。不要在同一验收节点上并发方向实验；还要记录 CPU、内存、存储和网络竞争，不能只看 GPU 利用率。

独占的范围按实验边界选择：单卡局部比较、整机训练、跨机通信需要不同资源域。跨机网络与共享存储未必能完全独占，应记录并采用预定配对顺序与污染判据。发现干扰时标记受影响运行；保留原始窗口，不在看到结果后随意删掉慢样本。

租约记录是协调协议；GPU 分配由 Slurm/Kubernetes 等真正的资源调度器执行。两者不能互相冒充。租约过期也不意味着旧进程已经停止：接管者先核对/取消旧作业并确认资源释放，再启动新的独占验收。对结果提交使用递增 `holder_epoch` 或其他可验证的 fencing token，使失去租约的旧执行者不能发布正式结论。

### Slurm 接法

`sbatch --parsable` 的成功回执意味着作业已被控制器接收并分配 ID，不意味着开始运行，更不意味着实验成功。保存 cluster、job ID、提交时间与 attempt；用调度状态和 accounting 结果核对终态、各 step 退出码、实际节点等。[1][2]

验收申请可使用站点支持的 exclusive / reservation 策略，并与管理员确认实际 partition 规则。`--exclusive` 的行为受集群配置影响，不自动等于获得全部主机内存；不要只复制一个 flag 就宣称完整资源独占。[1]

Slurm requeue 可能使用同一个 job ID 从脚本开头重新执行；需要额外的启动/重启实例身份、独立输出目录和可恢复收据。仅以 job ID 做一次性执行键不足。[1][2]

### Kubernetes 接法

以确定性的 attempt 名称创建 Job，保存返回的 namespace、Job UID 和实际 spec 摘要。重放提交时，先查询同名对象并核对 UID/spec/ledger；不能用新的随机名称再次创建。Job 被 TTL 清理后，持久台账仍须阻止旧请求重新创建。

申请 GPU、CPU/内存、节点和拓扑约束，并按集群支持的专用节点/调度策略取得验收资源；一个 `coordination.k8s.io/Lease` 本身不分配 GPU。Lease 可协调 holder 与续租，[4] 但释放和接管仍须检查真实作业与设备占用。

Kubernetes 官方明确：即使 `parallelism=1`、`completions=1`、`restartPolicy=Never`，程序仍可能被启动两次。[3] 因此输出按实例隔离，最后用条件写入/唯一收据选定有效结果；不能依赖“单副本”获得 exactly-once 执行。

## 4. 幂等提交与唯一重试负责人

推荐流程：

1. 持久保存 `SUBMITTING` 意图、submission key、spec 摘要、attempt ID，再向调度器提交。
2. 收到回执立即保存平台身份，再进入 SUBMITTED。查询、恢复只使用这个身份和 spec，不凭 agent 记忆猜测。
3. 如果响应丢失，用 submission key / 可查标签核对现有作业；只读查询失败、accounting 延迟或结果不唯一时保持 RECONCILING。Slurm 的 job name/comment 并不天然保证唯一，必要时人工核对；不要承诺自动消除所有提交歧义。
4. 成功/失败/取消的原始状态与退出码完整入账。失去 agent 会话不应自动终止一个仍正常执行的 GPU job；新会话先 attach/observe，而非重投。
5. 只有指定 `retry_owner` 可以创建新 attempt；其余层只能报告状态或提出重试请求。创建新 attempt 前确认旧实例终止或已被隔离。

默认把“新实验 attempt”的重试权交给 Temporal 实验协调层。模型调用的传输重试可以由 SDK 处理，但 GPU 提交、取消、结果发布、基线推进等副作用必须带稳定键。若允许 Slurm requeue 或 Kubernetes pod retry，它们属于同一 attempt 内可见的恢复；外层不能同时另起重复 Job。不要让 Symphony、LangGraph、shell 循环和集群调度器分别自行决定重新跑同一实验。

按原因处理：基础设施瞬态故障可按预先预算重试；数值失败、没有收益和契约不符进入科学结论，不通过“多跑几次直到 PASS”消除。原计划样本数不足或噪声大时，按预定义规则增加样本或输出 INCONCLUSIVE；不要事后挑种子、窗口或容差。

## 5. 组合、stale、长程与基线采用

用户 WAM 附件支持小测筛选后及时组合，并允许一批 3—5 个独立候选。此数字是实践建议，不是硬规则。每个补丁单独可撤销，组合清单绑定 parent baseline 与实际集成提交；共享编译边界、缓冲区或显存池的候选优先当成相互依赖，不简单相加单项收益。

组合失败时保持当前正式基线不变，保存失败组合；按依赖拆组或二分，重测实际子集。若组合已经采用后才发现长程问题，创建明确 revert/恢复记录，恢复代码、有效配置与必要的检查点兼容方案。删除一条开关不等于训练状态可回退。

以下变化使对应证据失效：候选/集成提交、目标基线代码或配置、负载/数据/初始检查点、影响结果的环境与硬件拓扑、计量/数值验证器或政策变化。影响哪些义务由差异与契约决定；不需要把所有旧资料全部重跑，但不能把旧结果无条件标为当前 PASS。保留完整 fingerprint 及可展开字段，避免摘要不一致时无法定位原因。

短测是筛选。长程确认至少覆盖合同指定的事件，例如动态输入路径切换、首次分配、缓存增长、周期性 GC、检查点保存与恢复；训练质量的时长、样本/seed 预算和指标由任务需求制定。有限 loss、某一步参数更新成功与收敛质量分开记录。E 类也可能需要长程稳定性确认；不能因为不要求完整训练质量评估而跳过它。N/A 类若质量缺失，应停在待确认，不能作为正式最优配方。

基线采用执行 compare-and-swap：只有 `expected_parent_generation` 仍等于当前基线，才能采用已审查组合；基线变更时旧待采用候选进入 STALE。Git 合并与台账更新跨系统，不应伪装成原子事务：先写采用意图与批准收据，完成受保护合并，记录实际 merge SHA，再推进基线指针；中途失败进入 RECONCILING，并暂停新的采用直到核对完成。

## 6. 报告信任界限与复现包

`PASS`、哈希与重算分别回答不同问题：

- agent 写的 PASS：一个声明。
- 文件 SHA256：所引用字节是否一致，不证明文件是谁生成或实验是否发生。
- 从输入数组重算比较：统计函数是否对这份输入产生相同结论，不证明数组来自指定训练。
- 可信 runner 收据 + 原始观测 + 调度平台事实 + 固定验证器 + 独立审计：才构成采用所需的证据链，仍只覆盖合同列出的范围。

最小复现包保存：源码与实际集成 SHA、完整生效配置、镜像/依赖版本、可访问的数据和检查点引用及摘要、命令、种子/数据顺序、分布式拓扑、采集器与验证器版本、调度身份、原始所有 rank 输出、窗口纳入规则、环境/资源记录、比较结果和审查收据。大数据不必拷入包，但对象版本和保留期必须可用。日志、验证器和统计 policy 不随候选任意修改。

门禁运行在受保护的 CI/审计 runner 上，执行器提交的 manifest、候选和报告都视为待验证输入。契约批准绑定 manifest digest；审查绑定 candidate/integration SHA；采用绑定 baseline generation 和 evidence digest。应对保留对象设置只追加或版本化策略，工作区删除前核对持久对象可读。

## 7. Temporal、LangGraph、Symphony 和 perfctl 的分工

| 工具 | 本方案职责 | 不承担的承诺 |
|---|---|---|
| Codex | 读代码、提出假设、实施候选与独立审查 | 模型文本不是资源锁、实验收据或批准记录 |
| Temporal Cloud | 现在接入：实验生命周期、durable timer、控制面重试、等待人工决定 | 不分配GPU；不自动保证外部副作用只执行一次；worker仍需运行 |
| LangGraph | 需要显式研究图时，管理有界的候选搜索与诊断步骤 | 不重新拥有GPU作业重试、正式审批和实验生命周期；checkpoint不回滚外部副作用 [5] |
| Symphony | 持续领取issue、运行Codex会话、管理工作区 [6] | 不承担GPU调度或正式实验重提交 |
| perfctl | 本地单协调者的manifest/证据一致性预检与归档 | 不是跨主机状态机、身份认证或训练正确性证明 |
| Slurm / Kubernetes | 真实资源、job/group、隔离策略与硬walltime | 终态不能替代科学结论和基线采用 |

把Temporal作为唯一正式实验生命周期所有者。Symphony按需现在接开发工单，LangGraph只在复杂搜索图确有价值时加入。所有跨层操作引用同一experiment与不可变manifest；禁止双方重试同一个外部提交。GPU任务中的scheduler/launcher恢复策略也必须纳入这一个重试计划。

交付包含可测试的Temporal工作流、worker、CLI、adapter协议、与perfctl的字段桥接规程。未配置真实adapter时拒绝启动；真实Cloud/GPU/SSO未在本次接入。参见temporal/README.md、PERFCTL_BRIDGE.md和VALIDATION.md。

## 8. 工具审查、修复与信任边界

本次进行了多轮独立审查和修复。当前perfctl已处理：规范路径与保留元数据保护、先快照后验证、比较器非零退出/超时、完整stale判断、实际配置/数据/初态绑定、结构化校验收据、归档再验证、注册时单次读取并原子写入，以及baseline快照完整性核验。14项回归测试通过；统计比较器另有9项自测通过。

这些检查只证明记录一致性。以下边界继续保留：

1. PASS与reviewer_id字符串、哈希不能认证执行者；受控runner、SSO/RBAC和独立审查负责真实来源与权限。
2. 比较输入可被重算，不等于从原始训练观测自动证明采集正确。项目adapter要保存并可重建完整转换链。
3. 验证器必须独立保护与固定版本，不能由候选作者随意修改。
4. 注册manifest不可覆盖，修改候选创建新experiment/revision；归档不是采用。失败与不确定实验仍保存在artifact store。
5. 台账的本地锁不构成跨主机资源锁；生产元数据、GPU租约与基线条件更新由外部平台实现。
6. 当前gate只回答对当前baseline是否符合记录条件；历史快照应独立检查，不冒充适用于新基线。

### 真实平台上线验收

- 重放提交只产生一个逻辑attempt；重复物理实例不会重复发布。
- 提交响应丢失、worker退出、作业requeue与取消超时进入明确恢复状态。
- 两个验收任务不会同时占用同一排他资源域；租约过期时先确认旧作业。
- manifest/artifact在外部修改、路径别名、归档污染与比较器异常不能通过。
- 基线或实际配置变化后旧证据不能采用；并发发布按parent generation裁决。
- 质量缺失、无收益、INCONCLUSIVE、生命周期未覆盖不会变成正式基线。
- 回退恢复完整代码/配置/适用训练状态，然后重新采集瓶颈。

## 9. 持续维护与面向人的概览

协调者只需维护六块：当前基线、瓶颈排序、候选状态、失败原因、运行中的任务及资源、下一步。每块链接到稳定证据，不把长聊天当数据库。恢复会话先读这六块和未决副作用清单。

每次采用后重新 profile，关闭不再相关的假设；每周检查过期租约/孤儿作业、失效 artifact 引用、旧兼容路径、长期未完成的确认、反复出现的失败。方向 agent 只修一个具体维护障碍，不能无界全仓重写。

优化代码的额外复杂性要有明确负责人、支持输入域、参考/回退路径、测试与收益证据。后续真实修改任务应由新上下文 agent 或未参与者抽查：定位和正确修改是否困难、影响多少模块、人工审查是否更重。不要用“优雅评分”或代码行数单独决定是否可维护。

## 官方资料（7 项）

1. [Slurm sbatch](https://slurm.schedmd.com/sbatch.html)：提交回执、parsable、exclusive、requeue。
2. [Slurm sacct](https://slurm.schedmd.com/sacct.html)：作业/step 状态和退出码；job ID 的重复记录与身份区分。
3. [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)：重试和重复启动语义。
4. [Kubernetes Leases](https://kubernetes.io/docs/concepts/architecture/leases/)：Lease 协调、续租、leader election。
5. [LangGraph Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api)：持久化、任务、副作用和恢复语义。原 durable-execution 入口现重定向到 persistence，以现行文档为准。
6. [OpenAI Symphony SPEC](https://github.com/openai/symphony/blob/main/SPEC.md)：单一调度状态、工作区、重试和明确非目标；§2.1/§18.2 的恢复边界。

用户提供的 WAM 附件是本方案的需求与经验依据，不属于已独立复跑的实验结果。本文不访问附件中的内部链接，也不把其中数字外推为一般硬件收益。

7. [Temporal Python SDK / Client](https://docs.temporal.io/develop/python/client/temporal-client)：Cloud连接、工作流调用与状态边界；部署模板的官方参考见 temporal/README.md。
