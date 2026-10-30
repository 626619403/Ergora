# 分布式训练与通信：给多 agent 优化系统的任务、约束和验收规范

核验日期：2026-10-26。范围：H200/Hopper 上的现有训练仓库，重点是 WAM 的 DeepSpeed ZeRO2 基线及其可能的扩展。本文读过用户提供的《从WAM优化实践到多Agent协作：工作流程与经验.md》和 `wam-report-reading.txt`；用户报告中的实验数字是历史证据，本次没有运行 GPU 实验，也没有访问其中的私有飞书或 GitLab 链接。

本文的推荐流程是工程设计建议；框架行为以末尾 12 项官方资料核验。`latest` 文档不是用户当前安装版本：真实实验必须保存 PyTorch、DeepSpeed、Megatron/Bridge、Transformer Engine、CUDA、驱动、NCCL、通信插件与容器的版本或 commit。

## 1. 首先保留什么，什么时候改变分布式策略

保留当前能复现的 ZeRO2 训练基线。先解决可见的通信尾部、rank 不均衡、重复归约和提交成本，不因为出现 FSDP、Megatron、EP 等新选项就迁移训练框架。只有容量、算力划分或网络规模的实测限制证明现有方案不足，才建立独立的并行策略候选；迁移成本、检查点兼容性和维护成本进入候选排序。

|策略|切分什么／主要通信|适合触发条件|具体检查及 H200 选型原则|
|---|---|---|---|
|DP，数据并行|不同副本处理不同数据，汇总梯度|单卡或一个模型并行组能容纳模型；希望增加有效吞吐|默认优先保持成熟路径。普通密集模型全局独立样本数由 DP 副本数决定，不把 TP/CP ranks 当新样本。先查样本、视角、有效 token 数是否各 rank 平衡。|
|ZeRO1／2|分别切分优化器状态；进一步切分梯度。ZeRO2 参数仍复制|状态/梯度占用明显，参数和激活仍放得下；当前 WAM 就在此处|检查谁拥有每片梯度、谁执行 optimizer、更新后参数如何同步。减少通信的目标是移除无用副本传输，不是减少必要的梯度贡献。|
|ZeRO3／FSDP2|再切分参数；按计算需要聚合参数，归约并切分梯度|参数复制使容量受限，或可释放显存支持更好的真实 batch/重算方案|额外参数通信可能反而变慢。以当前模型的模块边界分组，先用框架默认预取，再依据时间线改预取；记录参数临时聚合峰值。不要混用 FSDP1 的旧 API 与 FSDP2 API。|
|TP，张量并行；SP，序列并行|层内权重/计算切分；频繁层间集合通信。SP 分摊特定操作的序列激活|大层计算/权重单卡难容纳，或合理分片改善计算与容量|优先把频繁 TP 通信放在已核实的高速 NVLink 域；不能由“8 卡 H200”直接推断应 TP=8。测小矩阵退化、同步次数、通信资源争用。Megatron 的 SP 依赖 TP>1。|
|PP／VPP，流水线并行／交错流水线|按层或阶段切分；传递激活和激活梯度|模型深、单卡容量不足；层间传输比跨机 TP 更合适|按实际阶段耗时划分，不按层数机械均分。WAM 的冻结编码器、视频分支、动作分支必须一起计入依赖。检查微批数量、气泡、阶段不均、虚拟阶段带来的更多消息与内存。|
|CP，上下文并行|按实际注意力序列切分激活，交换所需 KV 等|真实 attention 序列造成激活/注意力容量瓶颈|WAM 文本 L192 不是视频注意力序列长度。先列视频 patch/token、视角、拼接和掩码后的真实长度。验证位置编码、causal/bidirectional mask、padding、packed 序列边界及反向。|
|EP／ETP，专家并行／专家内张量并行|在 ranks 间分布 routed experts；token dispatch/combine，专家内可能 TP|模型确有 token 路由的 MoE；专家容量或通信成为瓶颈|名为“动作专家”的密集组件不自动构成 MoE。先确认 router、top-k、专家数与真实激活参数。测每专家和每 rank token 数、all-to-all、padding/drop、辅助损失与热点专家。不要为“多 agent”而引入 MoE。|

框架事实依据：[S5]、[S8]、[S9]。表中的选型触发与 WAM 映射是本报告建议。对于常见密集 Megatron 布局，`world_size = TP × PP × CP × DP`；EP 不是在这个式子后面无条件再乘一项。专家与密集层的进程组存在不同划分，必须导出当前实现实际的 rank/group 映射。[S5]

长序列的进一步候选是分层 CP：将适合高速域的交换放在内层组，跨节点使用另一层交换。但纯 all-to-all CP 受每个 TP shard 可用 KV heads 及整除条件限制，不能只看 Q heads。Megatron Bridge 0.6.0 的分层 CP 使用 `a2a+p2p` 路径；它是特定实现方案，不是所有视频模型可直接打开的通用开关。[S7]

H200/Hopper 支持哪些优化与“当前服务器具备哪些互联能力”是两件事。先记录 GPU 型号、GPU/NIC/NUMA 连接和 NVSwitch 域，再选择通信后端。不要把 GB200/NVL72、B200 的配方或硬件常数套到 H200。NVLS 需要合适的第三代 NVSwitch/NVLink4 系统，单凭 GPU 是 H200 不能保证可用。[S1]

## 2. WAM 历史结果应怎样进入候选库

|已提供的历史证据|可支持的结论|不能支持的结论|
|---|---|---|
|单 owner Reduce：8 卡通信链 3.724→2.768 ms，少 0.956 ms|该通信链值得做正确性与 E2E 候选|完整训练提升 34.5%；任意 ZeRO 桶都能替换为 Reduce|
|同桶定向 Reduce 成组提交：完整更新 3935.131→3903.074 ms，吞吐约 +0.82%|合并提交可能抵消小包/回调成本|单独更早发每片梯度一定更快；当前新基线仍有相同收益|
|原结构 14B GAS4→16，同 80 逻辑轮约 +3.04% 吞吐|少做 optimizer 与参数同步可节省每逻辑轮时间|与 GAS4 有相同优化轨迹、相同更新次数或相同收敛速度|
|归约桶 2 亿元素、参数 AllGather 桶 5 亿元素，仅组合结果|这是特定框架/精度/形状的已用配置；单位是元素|“200 MB 桶”；桶本身的独立收益|
|宽度 7680 DiT 组合的 `MIN_CTAS=MAX_CTAS=32`：约 +0.58%|可在相同负载上复查 CTA 候选|原 H4096 模型、其他 NCCL 版本、任意 H200 网络都应固定 32|
|128 卡统一更新边界 GC：50 步窗口 1539→274 秒，预期约 270 秒|长 rank 停顿可远比通信内核效率重要|20 步短测能覆盖 GC；关闭 GC 永远不会积累内存|
|104 卡、448 卡生产长跑数据|证明相应配置完成了有价值的生产运行|没有同配置缩放对照时计算“扩展效率”|

2B 的通信 overlap 与非同步吞吐计时器也仅有组合证据。内部计时器不插入额外同步，不等于外层可以只测 CPU enqueue。历史 VAE＋大 FFN 出现约 97.5 ms 重叠但相关路径合计慢约 111.4 ms，正说明重叠面积不等于净收益。

## 3. 给 agent 的具体任务：按瓶颈临时派工

负责人维持唯一当前基线、固定工作负载、候选队列与资源租约；独立数值复核者可由全局验证 agent 承担。以下方向按需启动，不要求常驻四个 agent。

### 任务 A：分布式语义与拓扑审计

输入：最终启动命令和生效配置、训练循环、模型/优化器参数注册、数据采样规则、当前版本、生产节点清单。

操作：

1. 从真实 forward/backward/step 调用链标出每个逻辑目标、物理 backward、归约、梯度清零和参数更新边界；导出真实 optimizer-update counter，而不是猜日志里的 step。
2. 导出每个进程的 `global_rank/local_rank/device UUID/node/NIC/NUMA`，以及 DP/TP/PP/CP/EP 等进程组成员；检查跨节点映射、重复 device、错误网卡和分片整除条件。
3. 为每个参数类别列出参数副本、梯度副本、optimizer owner、归约组、归约算子、除数、归约 dtype、更新后同步方式。冻结参数、共享/tied 参数、动态未使用分支单列。
4. 列出一轮中各 rank 实际消费的样本/token/视角数，标明重复候选或多目标复用，不把它们都算作新增独立样本。
5. 检查启动时打印的 NCCL 和框架版本，与容器/依赖清单相互核对；不能只用系统另装的 `nccl-tests` 版本代表训练进程实际加载的版本。

交付：`group-map.json`、`ownership.csv`、`update-contract.md`、拓扑快照和最终生效配置；这些是建议产物名称，不是现成平台 API。

停止/转交：无法定位真实 owner、更新计数或归一化时，暂停通信改写，先补可验证的训练语义；不应在未知语义上用“loss 没爆”替代验证。

### 任务 B：通信关键路径诊断与有限调参

输入：任务 A 产物、同一 baseline 的完整更新时间、短窗口多 rank 时间线。

操作：

1. 对每类 collective 记录消息尺寸、次数、rank 组、梯度就绪时刻、入队时刻、设备开始/完成、下游消费等待；观察最慢 rank 的上游原因。
2. 将“通信本身慢”“等其他 rank”“CPU 很晚才提交”“计算被通信拖慢”分开。仅看到长 NCCL kernel 不能断言网卡带宽不足。
3. 先构造匹配实际 collective、dtype、root、尺寸范围、rank 布局的 `nccl-tests` 基线；小消息延迟和大消息带宽分开。它只筛选链路异常与通信候选。[S4]
4. 每轮只选少量有证据的候选：桶大小/分组边界、成熟 overlap 路径、有限预取、当前 NCCL 默认配置与一个 CTA 候选。比较完整更新净收益及峰值内存。
5. 把每项收益重新投射到当前关键路径：记录暴露的尾部少了多少、CPU 提交多了多少、并行计算慢了多少；不要将这三项当互不重叠的时间简单相加。

交付：一张标注最慢 rank 的依赖时间线、候选补丁、生效配置、原始分窗结果、保留/停止理由。通过后重新 profile，不继续追逐已经隐藏的通信时间。

停止/转交：若通信时间来自解码/GC/主机提交落后，交给相应方向；若可回收关键路径时间低于当前实验噪声或工程成本，停止调参。

### 任务 C：并行布局与容量联动

仅在内存限制、TP/PP/CP/EP 已有暴露瓶颈或生产扩容需求出现时启动。

1. 固定模型、数据与精度，列出当前每卡参数/梯度/优化器/激活/通信临时内存及峰值；提出至多三种实际可运行布局，不做无约束笛卡尔积搜索。
2. 每种布局同时估算容量、通信频率、每卡计算尺寸、流水线气泡与 batch 约束；优先在现有框架内改变分组/分片策略。
3. 为 TP 检查矩阵与 heads 整除、SP/TE 路径；为 PP 检查阶段耗时与微批排程；为 CP 检查真实 token 布局/掩码；为 MoE 检查路由计数与 dispatch/combine；分别写失败条件。
4. 需要换框架时，单独验证权重、优化器与检查点转换。先让新框架以可比较语义复现基线，再比较性能；不要把迁移和新精度、新 batch 同时打包。
5. 报告固定全局工作量和固定每副本工作量两种缩放实验；如只能运行一种，明确缺失另一种，不能互相推算。

交付：布局表、实际进程组图、数值对照、容量曲线、完整更新/有效吞吐、GPU-hours 和维护成本；不以单一 MFU 决策。

### 任务 D：跨机扩展与恢复验收

1. 在相同拓扑和软件栈上，逐级验证单节点、跨节点、代表性网络域、目标生产规模；每级先检查正确性再计时。
2. 采集各 rank 的完成分布、数据等待、GC、网卡/链路异常和 checkpoint 开销；诊断长尾时保留异常窗口，不随意删除。
3. 覆盖生产周期中的保存、恢复、动态形状/视角切换、首次分配、缓存增长、GC；不把只覆盖平稳 20 步的结果叫生产验收。
4. 在可控测试任务中注入单 rank/节点失败和保存失败；验证整组终止或框架支持的恢复路径、最后完整检查点选择、重复数据边界及无重复提交。

交付：缩放曲线、生产窗口指标、恢复演练记录、可恢复状态清单、晋级/回退结论。生产故障不能由每个 agent 各自重启一个 rank。

## 4. 检查树：看到什么，下一步查什么

|观测|先判定|下一步|
|---|---|---|
|反向之后有暴露通信尾部|是梯度很晚就绪，还是已就绪但晚提交？|前者查编译/重算边界与桶布局；后者查回调、Python 提交与流依赖。再试更早归约，而不是先调网络参数。|
|很多细碎 collectives|每条消息是不是被框架分片或自定义 owner 路径拆小？|统计调用次数与每包尺寸；试桶内成组提交或适度增大桶，同时检查更晚启动造成的新尾部。|
|NCCL 条很长但链路 microbenchmark 正常|慢 rank 是否迟到？|对齐 collective sequence 与其梯度就绪事件，检查供数、GC、CPU 争用、计算形状、MoE 路由不均。|
|增加 overlap 后内核变慢|是否争抢 SM、HBM、L2、CPU 或 NIC？|比较无 overlap 与 overlap 的相同计算段和 E2E；减少预取深度或通信 CTA，不追求时间线更“满”。|
|参数 AllGather 频繁且占关键路径|是否在 ZeRO3/FSDP 按过细模块分组，或重算导致重复获取？|先调整分组与成熟预取；同时观察聚合参数生命周期和内存峰值。|
|PP 阶段大量空闲|微批不足还是阶段不均？|用各阶段的实际 fwd/bwd/通信时长划分；检查 VPP 的气泡收益是否超过额外消息开销。|
|只有跨机显著退化|选错 NIC、NUMA/PCIe 路径、链路/rail 异常，还是算法的跨机通信过密？|先做官方系统诊断，再测实际消息谱；只有系统健康后才调 NCCL。需要驱动/网络配置的改动交给集群 owner。[S3]|
|模型或序列 OOM|参数状态还是激活占主因？|前者考虑更深分片/TP/PP；后者考虑重算、合适 microbatch 或 CP。不能用 ZeRO3 当所有 OOM 的默认答案。|
|吞吐周期性崩落|是否碰到 GC、checkpoint、数据 epoch/分片切换？|按相同真实 update ID 关联全 rank 事件；让长测跨过这些周期，而不是增加短测次数。|
|少数 MoE ranks 极慢|热点专家、token 倾斜还是 dispatch 通信？|记录路由计数和专家计算；不能用丢 token、改 top-k 或改辅助损失偷偷换取吞吐。|

## 5. 候选清单与风险级别

|候选|必要证据／最小实验|主要风险与回退条件|
|---|---|---|
|修正 rank/NIC/NUMA 映射、清理陈旧调试环境变量|同一节点组/消息谱的前后对照；确认未改变模型语义|共享网络噪声会伪造收益；不要自动修改整个集群驱动、ACS/IOMMU 或交换机策略。|
|改变桶大小、按已就绪顺序分组|记录元素数、dtype、字节量、ready/launch/finish；看 E2E|更小桶使启动更早，也增加调用数；更大桶节约提交但更晚开始。DeepSpeed 的相关桶配置单位是元素。[S8]|
|通信与反向 overlap、参数预取|当前路径支持；存在足够可覆盖计算；显存余量充足|CPU 调度、SM/HBM 争用、额外 buffer 与生命周期变化。Megatron 的 DP/TP/PP/CP/EP overlap 不是一个可互换的开关。[S6]|
|FSDP2 分组/预取调整|已有 FSDP2 基线；显式查看参数聚合时间|预取更多层增加峰值；冻结/共享/动态执行顺序需覆盖。先默认隐式预取，再依据证据用显式控制。[S9]|
|自定义 owner Reduce／成组 Reduce|完整 owner 映射；高精度小模型的更新等价验证|归约根、rank 顺序、除数、buffer 生命周期、全局 norm/clip、溢出处理任何一项错误都可能静默改梯度。应有独立审查与可一键回退路径。|
|NCCL CTA 数候选|训练实际 NCCL 版本及真实消息谱；默认 vs 单个候选的 E2E|`NCCL_MIN_CTAS/MAX_CTAS` 自 2.17 支持；2.25 前上限 32，之后上限 64。它们会覆盖 communicator 配置；更多 CTA 争抢 GPU 资源，小消息也不保证达到设置值。默认自动选择为对照。[S1]|
|加大 GAS／改变 microbatch|先确认是否保持每次更新的全局目标与样本集合|固定 microbatch 加大 GAS 通常改变有效 batch 和更新频率。算法候选与保真系统优化分榜；不能仅验每逻辑轮吞吐。|
|TP/PP/CP/EP 布局或分片级别变化|容量或通信瓶颈明确；新进程组/检查点路径可验证|数值归约顺序、路由、调度与恢复复杂度增加。单节点提速不证明跨机提速。|
|异步检查点|保存的阻塞时间在关键路径，CPU/存储余量足够|快照 staging 与训练抢资源、CPU pinned memory、积压请求、未完成保存被误认为可恢复。默认只允许一个 outstanding 保存。[S11]|

不发布“推荐所有 H200 使用这些 NCCL 环境变量”的通用脚本。实验结束后将候选环境变量连同适用拓扑、版本、消息谱写入配置，只保留获得净收益的项。系统健康检查与性能调参分开。

## 6. 梯度、归一化与更新语义：改通信前必须过的门

先写真实训练目标。例如对目标类型 t，若意图是按有效样本或 token 求均值：

`L = Σ_t α_t × [Σ_(rank,microbatch,item) w_(t,item) × loss_(t,item)] / N_t`

`N_t` 必须对应已约定的有效计数或权重和；不能默认等于 world size、名义 batch 或所有目标共同的计数。上式是建议的显式契约，不声称用户当前实现已经如此。

检查顺序：

1. 为每个目标选择正确分母：样本均值、有效 token 均值、每视频均值或其他。多视角、多候选和多目标复用是否增加权重，必须显式写明。
2. 统计每个参与者的有效计数。各 rank 长度/有效样本不同时，“各自平均后再平均”通常不是全体样本平均；使用总和/总计数或数学等价的加权路径。
3. 列清本地 loss 已除过什么、GAS 路径除过什么、集合通信是 SUM 还是 AVG、框架是否再除 DP size。普通 DDP 平均梯度；自定义 DDP comm hook 不会预先替用户除 world size，不能照搬除数。[S10]
4. 确认条件分支无有效样本时，是贡献零还是跳过整个目标；参与 collective 的 ranks 与调用顺序仍必须相容。active-rank SUM 的数值可以提前异步算，但必须在依赖消费者前完成且不改变分母定义。
5. 对普通等大、单目标 DP，可用 `B_update = B_micro_per_replica × GAS × DP_size` 做检查；混合模型并行不能用总 GPU 数代替 DP size。DeepSpeed 配置页给出了简单 DP 场景的 batch/GAS 关系，WAM 的多目标逻辑步还需要逐项计数。[S12]
6. 若加大 GAS 同时减小 microbatch，使每更新样本集合保持不变，也要覆盖 batch 相关运算、随机性、尾批、混合精度累加和 clipping 时机。若只增加 GAS，则优化器更新频率、Adam 动量/权重衰减次数、scheduler 时钟和每更新经验目标都会变化；应另做 time-to-quality 验收。
7. DDP 的 `no_sync()` 要包住对应 forward/backward；不能把这个 API 原样套给 ZeRO/FSDP。当前框架的累积与归约边界必须查本版本实现。[S10]

### Owner Reduce 的专项正确性清单

- **唯一且正确的 owner**：每个参数切片由既定 rank 更新；检查尾部 padding、跨桶切片、共享/tied 参数、未使用参数和 group-local/global rank 映射。原生 NCCL 的 root 是 communicator rank；框架封装的 `dst`/`group_dst` 语义再单独核对，不能把 GPU device index 当 root。[S2]
- **必要贡献不丢失**：从 AllReduce 改为 Reduce 只意味着结果不必发给每个 rank；归约仍要收齐约定组的梯度。非 root 不能读取 Reduce 的结果充当完整梯度。
- **分片更新的消费者正确**：norm、clip、overflow/non-finite 判定、gradient logging 如需全局信息，必须有正确的跨片汇总；不能只看 owner 的局部 norm。
- **参数版本一致**：更新后参数同步到下一次需要它的消费者；验证相应副本一致、全局重建参数与参考更新一致。不同 pipeline stage 或真正分片参数不能直接要求整张本地张量相等。
- **异步生命周期正确**：Work/Future、CUDA event 和消费流依赖足够；send/recv/reduce buffer 不提前重用或释放；zero-copy 别名在通信结束前不能被下一轮 backward 覆写。
- **collective 序列正确**：所有参与者对 count、dtype、root、group 和调用顺序达成一致；成组提交的所有 ranks 按一致顺序进入。缺一个 rank 不是“少算一点”，可能挂起或损坏数据。[S2]
- **分层验证**：先用 FP64/FP32 小模型与可检查梯度比对，再在真实 BF16/FP8 路径比较输出、梯度、参数 delta、多步更新及代表损失。浮点归约顺序变化可能不逐位相同；阈值按误差基线制定，不能只检查 finite。

## 7. 资源与拓扑租约：并行探索，独占验收

资源租约由实际集群 scheduler/资源管理服务提供；agent 的 Markdown 或 JSON 记录不能替代真实资源隔离。允许独立无干扰的小实验并行；涉及跨 rank collective 时，把全组作为一个调度单元分配和释放。

建议最小记录结构如下，仅是数据契约，不是本次已实现的 API：

```yaml
lease_id: <调度器分配的唯一租约>
generation: <防止失效执行者写回结果的递增代号>
experiment_id: <唯一候选实验>
owner: <唯一提交与取消负责人>
baseline_commit: <固定版本>
candidate_commit: <固定版本>
workload_fingerprint: <数据、形状、更新目标、精度、配置摘要>
allocation:
  scheduler_job_id: <实际作业ID>
  nodes: []
  gpu_uuids: []
  rank_map_artifact: <进程组与节点映射文件>
  topology_fingerprint: <NVLink/NVSwitch、NIC、rail、NUMA摘要>
  sharing_policy: <哪些CPU/存储/网络域独占，哪些共享>
expires_at: <到期时刻>
heartbeat_at: <最后有效心跳>
retry_owner: <只允许一个系统负责本次作业级重试>
max_attempts: <有界次数>
artifacts_prefix: <本次尝试唯一只追加目录>
```

执行规则：

1. 不能先启动部分 ranks，再长期等待其他 agent 释放卡；使用 scheduler 支持的整组分配。每次尝试使用唯一端口/rendezvous 标识与输出目录。
2. GPU UUID 不重叠仍可能共享 CPU、内存带宽、NIC/rail、交换链路和存储；正式通信/E2E 对照要控制这些共同资源，至少记录无法隔离的条件。
3. 需要比较拓扑时明确这是实验变量；普通 A/B 必须使用同一拓扑与相近资源条件。分配变化就更新 fingerprint，不沿用“同环境”结论。
4. agent 超时不等于远程作业结束。重试前先按 job ID 查询/取消并确认旧尝试退出；lease generation 不匹配的结果只能归档，不能提升基线。
5. scheduler、elastic launcher、外层 agent 不得对同一失败各重试一遍。每个失败边界只有一个 retry owner，并设置总重试预算；无法证明恢复等价的失败窗口不进入性能结果。
6. 失败时取消本租约整个通信组，由 launcher 清理其进程；不按模糊进程名杀其他任务。终止、最后日志、未完成 checkpoint 和资源释放状态必须留证。
7. 同一基线的 E2E 晋级只由负责人串行验收并更新。多 agent 可以产出多个候选，不能各自宣称“最新最优”。

## 8. 从小规模到生产的验收阶梯

|阶段|运行内容|通过条件与不能推出的结论|
|---|---|---|
|0. 静态/小模型|owner/分母/进程组核对；小模型梯度与更新对照|证明实现基本语义；不能据此宣称真实模型快。|
|1. 单节点或最小可行模型组|真实形状、实际精度、所有目标；相应 collective 微测与完整更新|数值门禁通过；候选能减少真实完成时间；包含峰值内存。模型本来就无法单节点运行时，不强行制造不可比缩水模型作为性能基线。|
|2. 跨两节点或最小跨网络域|真实网卡/rail/NUMA；跨机 collectives；代表样本形状|消除错误链路/映射；无挂起、错误归约或明显尾部退化。两节点通过不代表交换网络大规模拥塞已覆盖。|
|3. 代表规模|覆盖计划生产的进程组基数、跨机架路径、路由/专家倾斜和 PP/CP 边界|记录多个交错 A/B 窗口；恢复测试通过；超出噪声的 E2E 净收益。规模由实际拓扑决定，不能机械规定所有任务只测 8/16/32 卡。|
|4. 生产 canary|目标配置、真实数据分布；跨越 GC/保存/动态形状等周期|有效吞吐、p95/p99 完成时间、稳定内存、checkpoint 可恢复、既定质量指标均达标；设回退阈值后才扩大生产采用。|

测量协议：

- 用完整真实 optimizer update 或固定数量的逻辑轮作计量单位；GAS 不同必须同时报告两者。 WAM 的 GAS16 应报告每四轮一次真实更新，以及按轮换算的吞吐。
- 外层必须观察所有必要 GPU/通信工作完成，并按参与 ranks 中最晚完成者决定边界。可在测量窗口边界统一对齐、离线汇总每 rank 时间；不要为了每个内部子阶段插入全局 barrier，破坏待测 overlap。
- cold start、编译、预热另记；稳态指标与包含定期 GC/保存的数据完整生产指标都保留。多节点时钟不直接混算：使用同一 update ID、每 rank 单调时钟区间和明确的窗口对齐协议。
- 原始异常窗口全部保留并解释；交换 A/B 顺序并重复配对。预先声明最小有意义改进（绝对 ms 与百分比）、测量噪声容忍和 p95 回退上限；不以一次快 0.5% 直接晋级。
- `nccl-tests` 的延迟、algbw/busbw、通信-only speedup 只作诊断。实际训练还存在就绪依赖、计算争用、更新、数据和保存；它们不能替代完整更新指标。[S4]
- 固定全局 batch/工作量属于强缩放思路；固定每 DP 副本工作量属于弱缩放思路。分别比较有效样本/秒与资源成本，且确认有效 batch 改变是否允许。没有匹配的小规模基线就不计算 scaling efficiency。
- 计入失败重试后的 GPU-hours 与 wall time。更高瞬时吞吐但更频繁 OOM、丢作业或恢复耗时更长的方案不一定更高效。

## 9. 检查点与容错的单独门禁

默认在明确完成的 optimizer-update 边界保存。若业务要在累积中途保存，必须同时保存部分梯度、累积计数及尚未消费数据状态；“只保存权重”不能恢复同一个训练过程。

保存契约按当前训练实现列全：模型参数和必要 buffer、optimizer 主权重/状态、scheduler、scaler或其他数值状态、RNG（含需要恢复的各设备/组件流）、采样器与数据游标、真实 update/逻辑轮计数、混合数据源状态、模型/路由相关持久状态、配置和代码版本。由框架原生 state-dict/checkpoint API 处理分片，不手工拼接并行布局来省事。

异步保存必须区分快照完成与持久化完成。DCP 会使用 CPU staging 以隔离训练继续修改的参数，增加 CPU 内存；官方建议多数场景限制为一个在途保存。它返回的 future 不是“已经可恢复”的证明。[S11]

验收步骤：

1. 对每个完成的 checkpoint 保存唯一标识、完整状态清单、提交完成标记；只有完整成功版本能成为 latest，失败或部分写入版本不能被加载。
2. 测保存期间完整训练吞吐、CPU/pinned memory、存储带宽和尾延迟；异步移动了时间不代表消除了成本。
3. 训练结束/退出前等待最后的保存完成并核验结果；不要只检查文件夹存在。
4. 先同布局恢复，验证下一批数据、下一次 update、loss/参数 delta；再单独测试实际框架和当前版本支持的 reshard/换卡数恢复。不假定任何 TP/PP/EP 改动都能无损加载 optimizer。
5. 保存进行中杀掉测试 rank、丢失测试节点、模拟保存失败：只从最后完整 checkpoint 恢复；说明最多重放多少数据、是否容忍 RNG/非确定性差异。
6. 把检查点频率作为独立系统决策，考虑保存成本和故障重做损失；不能为了漂亮的短测吞吐移除生产必需保存。

## 10. 最小候选交接与晋级记录

每个通信或分布式候选只需交一份可复查记录，正文先报“完整更新时间节省多少”，再解释机制：

```text
候选名 / 唯一 experiment_id / agent owner
基线 commit、补丁 commit、最终生效配置、版本/容器摘要
允许改变：布局 / batch / GAS / 精度 / 算法（逐项 yes/no）
工作负载与更新契约：样本、视角、token、目标权重、分母、真实更新次数
资源：job_id、GPU/rank组、拓扑指纹、租约/attempt、干扰条件
假设：关键路径哪条依赖可缩短，预期回收多少 ms，新增什么成本
正确性：输出/梯度/参数更新/恢复检查，原始结果路径
局部性能：collective形状、次数、ready/launch/finish、通信-only边界
E2E：A/B原始窗口、顺序、最慢rank、median/p95、净收益、内存峰值
长测：GC、checkpoint、动态图、失败/重试、生产质量覆盖情况
结论：保留 / 待集成 / 停止；回退开关；何种条件变化值得重试
```

## 11. 已核验的一手资料（12 项）

以下链接均于 2026-10-26 打开核验。网页版本标签是此次检索结果，不代表用户环境；执行前必须对照已安装版本。正文仅引述具体机制，流程和验收设计是本报告的工程建议。

|编号|官方来源与核验范围|检索 ref，供主报告复核|
|---|---|---|
|S1|[NCCL 环境变量](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html)，页面标注 2.32.3；MIN/MAX_CTAS 的版本门槛与资源争用，NVLS 硬件边界。|`` / `` / ``|
|S2|[NCCL Collective Operations](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html)，2.32.3；Reduce 的 root、结果所在 rank、count/dtype 和 AllGather/ReduceScatter 排列。|`` / ``|
|S3|[NCCL Troubleshooting](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting.html)，2.32.3；先区分 GPU/NIC/拓扑、网络、runtime 与性能调参的官方入口。|``|
|S4|[NVIDIA nccl-tests](https://github.com/NVIDIA/nccl-tests)，官方仓库；性能/正确性测试、进程/rank 数、collective 参数、带宽解释入口。|`` / ``|
|S5|[Megatron Bridge Parallelisms Guide](https://docs.nvidia.com/nemo/megatron-bridge/latest/parallelisms.html)，latest；DP/TP/PP/SP/CP/EP 区分，DP size 计算与拓扑建议。|`` / ``|
|S6|[Megatron Bridge Communication Overlap](https://docs.nvidia.com/nemo/megatron-bridge/latest/training/communication-overlap.html)，latest；不同并行域有不同实现/前提，重叠并非普遍获益。|`` / `` / ``|
|S7|[Hierarchical Context Parallel](https://docs.nvidia.com/nemo/megatron-bridge/0.6.0/training/hierarchical-context-parallel.html)，明确固定为 0.6.0；a2a/p2p 的机制、KV heads 条件及拓扑层次。|`` / ``|
|S8|[DeepSpeed ZeRO 文档](https://deepspeed.readthedocs.io/en/latest/zero3.html)，页面标注 0.19.9；ZeRO stages、桶元素单位、归约/聚合与 overlap 配置。|`` / ``|
|S9|[PyTorch FSDP2 Tutorial](https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html)，页面标注 2.14.0+cu130；fully_shard、DTensor、模块聚合与隐式/显式预取。|`` / ``|
|S10|[PyTorch DDP API](https://docs.pytorch.org/docs/2.14/generated/torch.nn.parallel.DistributedDataParallel.html)，明确 2.14；梯度平均、no_sync 的 forward 范围、自定义 comm hook 的除数责任。|`` / `` / ``|
|S11|[PyTorch 异步分布式检查点](https://docs.pytorch.org/tutorials/recipes/distributed_async_checkpoint_recipe.html)，页面标注 2.14.0+cu130；CPU staging、内存成本、future 和在途保存限制。|`` / ``|
|S12|[DeepSpeed 配置文档](https://www.deepspeed.ai/docs/config-json/)，当前在线版；microbatch、GAS、train batch 的关系。未据此向旧环境推荐新配置字段。|`` / ``|
