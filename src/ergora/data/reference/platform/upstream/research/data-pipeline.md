# 数据管线、冻结特征与端到端计算重排：方向 agent 工作规程

核验日期：2026-10-26。本文依据用户提供的 WAM 工作流程与报告摘录，并核验下列公开官方文档。用户报告中的收益仅作为具体实验的历史记录；本文没有执行新的训练实验，不将这些数值外推到其他模型、集群或输入分布。

## 1. 任务边界与交付标准

本方向负责从样本索引到训练消费者之间的整条路径：索引与元数据、存储读取、视频寻帧与解码、随机增强、tokenizer/图像准备、DataLoader IPC、pin memory、H2D、冻结编码器，以及这些工作在一次完整参数更新中的位置。

优化目标是固定语义工作量下的完整训练更新时间。WAM 的工作量应以源视频窗口计量；同一窗口的多个视角不能被算成多个独立样本。GAS、源数据混合比例、各任务 loss 权重、每个 update 的有效窗口数必须固定。以最慢 rank 完成该 update 的时间为准；解码 FPS、GPU utilization、局部 kernel 时间只用于解释原因。

默认保留样本、帧时间、增强分布、参数版本与训练目标。改变采样、裁剪、编码质量、帧率、训练分辨率或缓存随机增强后的结果，是另一个算法实验，需要另立候选，不能混入实现等价性实验。

方向 agent 应交付：可复现基线；关键路径证据；一个主要因果假设；最小补丁与撤销方式；正确性证据；独占资源上的端到端对照；资源成本与适用条件；失败记录及重新尝试的条件。

## 2. 主管交给方向 agent 的可执行输入

| 输入 | 必须落实的内容 |
|---|---|
| 基线身份 | Git commit、未提交 diff、真实启动命令、解析后的有效配置、容器及依赖版本；现有优化开关的最终值 |
| 工作量 | 每个 update 的源窗口数、GAS、各数据源比例、任务图、loss 归一化、每 rank microbatch；不能只给 batch size |
| 输入语义 | manifest/hash、视频与标注版本；视角数、分辨率、帧索引/时间戳规则、动作对齐规则、裁剪与增强、tokenizer、文本长度 |
| 当前数据实现 | map/iterable dataset、sampler、worker 数、prefetch、persistent workers、collate、pin memory、缓存、每进程线程池；rank/worker 分片方式 |
| 机器拓扑 | rank→GPU→PCIe/NUMA→CPU cpuset；物理核、内存限额、共享内存限额、GPU 型号、存储协议与吞吐、网络竞争、视频 codec/profile/pixel format/是否 VFR |
| 冻结边界 | 哪些参数冻结、实际 eval/train 状态、dropout/BN、是否需要输入梯度、VAE 是否 posterior sampling、LoRA/EMA/在线更新、输出消费方 |
| 正确性合同 | 哪些内容要求逐样本精确一致；浮点容差；训练状态比较点；允许的随机等价条件；恢复训练与多 rank 的要求 |
| 性能证据 | 无 profiler 的 update 时间分布；短 trace；各阶段 CPU/GPU 事件；GPU 空洞；rank 尾部；RSS/PSS、page cache、pinned/shm/VRAM 与 FD 峰值 |
| 实验资源 | 可用 CPU 核/内存/磁盘/网络/GPU、运行时限、独占基准窗口、共享集群禁止操作、主管分配的候选编号 |

缺项先读配置与调用链，不能从配置字段名字推断实际行为。首次运行应打印“有效配置＋拓扑＋数据语义摘要”，由主管与基线对齐。

## 3. 先把等待归因到正确的层

沿以下边界记录等待与执行：`索引/元数据 → 读取 → seek/decode → 增强/tokenize → collate/IPC → pin → H2D → VAE/VLM → 训练消费者`。

记录 sample/window ID、rank、worker、epoch、update、microstep，并区分队列等待和实际处理时间。采样记录每段请求的帧数、去重后的唯一帧数、视频打开/seek 次数、压缩字节、产生张量字节和 cache 命中。CPU span 不能代表异步 GPU 工作完成；GPU 阶段采用事件/trace 建立关系，避免为测量而在每段插入全局同步。详细 profiler 运行用于诊断，最终吞吐采用关闭 profiler 的完整更新。

至少覆盖三类状态：冷启动/索引初始化；预热后的稳定训练；数据源、视角或 shape 切换及 checkpoint/恢复。只用少量反复读取的视频容易把工作集完全装入 page cache，掩盖真实存储瓶颈。

| 观测 | 进一步分辨 | 第一批候选 | 不应直接做的事 |
|---|---|---|---|
| 开始训练前主机内存已很大 | rank/worker 是否各自复制 Python list、dict、字符串元数据；RSS 是否重复计入共享页 | lazy metadata、紧凑数组、只读 mmap、按字节限额的缓存 | 直接增加机器内存或 worker 数 |
| GPU 等 `next(loader)` | 队列是否经常空；是读盘、seek/decode、增强还是 collate/IPC | 从暴露在关键路径上的最大阶段入手；先消除重复工作 | 根据 CPU 总利用率猜瓶颈 |
| CPU 很忙，吞吐随 worker 增多下降 | worker×FFmpeg/BLAS/tokenizer 线程是否超额；远端 NUMA、上下文切换、内存带宽 | CPU/NUMA 亲和、线程限额、小范围 worker 扫描 | 所有 rank 都占满同一 NUMA 节点 |
| 数据已准备但 H2D 挡住训练 | 是否 pinned、是否同步复制、DMA/PCIe 是否饱和、是否已有可重叠计算 | loader pin memory、有限双缓冲、异步复制与事件 | 认为 `non_blocking=True` 自然产生计算重叠 |
| CPU 解码占关键路径 | codec/GOP、随机 seek、同文件同帧重复、批量 API、线程池 | 同次请求去重、批量取帧、精确帧映射；之后才比较 NVDEC | 不检查帧身份就改 approximate seek |
| GPU 解码后数据 FPS 更高，更新却更慢 | 后处理/resize/layout/HBM、解码表面和训练是否争资源 | 完整训练 A/B；缩小预取和解码并发；保留 CPU 路径 | 用独立解码 benchmark 宣布训练提速 |
| 已产生批次但消费者仍等待 | 冻结特征是否重复算；CPU/GPU 提交顺序；跨 stream 依赖 | 同 batch 复用、CPU 准备重排、有限下一 batch 编码预取 | 把多 stream 当成额外算力 |
| 扩卡后少数 rank 常拖尾 | shard/GOP/样本复杂度不均、远端存储、NUMA、分片或 padding | 每 rank 队列与尾延迟、确定性分片、局部 staging | 只报告平均 rank 时间 |

## 4. 候选顺序：先减少工作，再隐藏剩下的等待

下面是默认顺序，主管可依据“暴露的关键路径毫秒”调整；不是要求所有项目都实施。

1. **去除冗余与不必要的常驻对象。** 同一 `seek_mp4` 调用内，若多个逻辑视角要求相同视频和相同帧，解码一次，再为需要原地操作的视角创建独立张量，分别增强。重复 GT/reference、同一 batch 的多个训练目标、未变化的元数据均先审计。不要跨不同随机输入强行复用。
2. **收紧索引和缓存。** episode offset、合法窗口区间、排列等使用紧凑数组，避免完整 Python 对象图与 `.tolist()`；静态只读索引可 mmap，各 worker 从路径和布局重新打开。缓存必须有字节上限，记录命中、逐出、FD 数与最大驻留，而非只限制“条目数”。需要随机排列时保留其精确次序，不能用局部 shuffle 替换全局排列而不标记算法变化。
3. **调整 CPU 预算与 loader。** 在合理 cpuset 下扫少量 worker 数；限制每个 worker 内 FFmpeg、BLAS、tokenizer 的嵌套线程；保留训练主进程、通信与系统线程所需核。将纯 CPU、可序列化、与模型状态无关的 tokenizer/图像准备移入 workers；尝试批量 `__getitems__` 或批量解码，减少 Python 调用。`persistent_workers` 省初始化，也会保留缓存与 RNG 状态；每个 epoch 的更新要明确传递。
4. **设置有限预取和 H2D。** DataLoader 的 `prefetch_factor` 是每 worker 的批次数，不是总批数。粗估预算包含 `rank×worker×prefetch×batch bytes`，再加解码中间量、IPC、pinned 副本与冻结输出，实际以峰值测量。使用 DataLoader pin 线程或受控 pinned buffer，异步复制配合 consumer event；不要在关键路径临时 `.pin_memory()`。队列够用后停止加深。
5. **改善寻帧与存储局部性。** 批量读同一视频的帧；对不可变视频建立可校验的精确帧映射，避免重复扫描。小文件/object GET/随机 seek 主导时，再考虑本地 staging、tar/shard、索引旁车。用真实冷/热缓存、真实 shard 分布测试；不要把索引 mmap 的成功推广为网络视频文件 mmap 必然更快。
6. **比较 CPU 与 GPU 解码。** TorchCodec/NVDEC 或 DALI 是候选实现，不是先验赢家。先验兼容性包括 codec/profile、硬件、驱动/FFmpeg、CFR/VFR、输出色彩与帧身份。最终选型必须把训练计算、GPU 后处理、HBM/VRAM 和解码并发一起测。
7. **编排冻结计算。** 在数据 ready 后尽早提交当前 batch 的冻结编码；如依赖关系允许，仅预取一轮未来 batch 的冻结输出，然后逐步增加。每增加一层预取，都验证总生产速率和稳态等待，不能用提前灌满的队列隐藏欠账。
8. **最后考虑大规模格式迁移。** WebDataset/FFCV/自定义预解码格式有转换、存储、版本、恢复与维护成本。只有前面的证据表明瓶颈能被该格式解决时，才对一个代表性子集做候选，再决定是否迁移全量。

### 工具适用范围

| 工具 | 适合解决 | 主要边界 |
|---|---|---|
| PyTorch DataLoader | worker 并行、批量取数、pin、预取与现有训练栈集成 | 不负责自动修正 rank/worker 重复、线程过量或数据语义；iterable dataset 必须正确分片 |
| TorchCodec | PyTorch 张量视频读取、CPU/CUDA 解码、批量按索引取帧 | exact/approximate 语义不同；自定义帧映射需版本和内容校验；确认实际 CUDA 解码及 fallback |
| NVIDIA DALI | 将读取/解码/增强流水线交给可控的 CPU/GPU 算子图 | 标准 `readers.video` 支持 CFR；真实 VFR 不能靠跳过检查变安全；调队列及 decode surfaces 会增加内存 |
| WebDataset | tar 分片顺序读、对象存储、多小文件读取开销 | Iterable 与 resampling 会影响 epoch/覆盖/恢复语义；并不消除视频内 GOP seek 成本 |
| FFCV | 适配其格式的图像/数组训练、编译化 CPU transforms 与缓存 | 需要转换和管线适配；不是任意多视角视频任务的 drop-in；当前官方调参文档的 `QUASI_RANDOM` 不支持 `distributed=True` |
| NumPy mmap 索引 | 大型静态紧凑索引共享、按需分页 | 不等于零物理内存/零 I/O；随机页面访问和网络存储仍可能慢 |

## 5. 必要正确性门禁

### 5.1 样本、帧与随机增强

保留一份小型 adversarial 数据集：多视角共享文件、不同文件相同 basename、长 GOP、边界/重复帧、不同时间基、真实 VFR、短视频、损坏文件、不同分辨率与字幕长度。逐窗口比较视频 ID、frame ID/PTS、动作时间、文本、view ID、采样权重与排除原因。

对 decode 输出检查通道次序、dtype/range、色彩转换、resize/crop、padding、维度/stride。CPU/GPU codec 或图像实现可能有数值差异，应由任务给定合理容差，并检查差异对后续特征/梯度的影响；“能播放”不是验收。

复用解码输出后，每个逻辑视角仍应执行其原本的随机增强。需要写入张量的变换必须隔离存储，避免一个视角的 crop/normalize 污染另一个。若为了跨 worker/预取深度保持确定性而引入由 `(epoch, sample ID, view, augmentation ID)` 派生的 RNG，它是明确的随机性设计变更：先固定新的参考序列，再比较候选，不能把改种子后的训练差异归因于性能补丁。PyTorch worker seed 不自动保证 NumPy、Python、FFmpeg 或自定义库全部正确初始化。[S1]

`in_order=False`、shuffle buffer、resampling、QUASI_RANDOM、丢弃慢样本均可能改变分布或顺序，必须单独登记。分布式要检查每 rank、每 worker 的 shard/window 覆盖；`DistributedSampler(drop_last=False)` 的尾部补齐会有有意重复，不能既忽略它，也误判为 loader bug。每 epoch 在创建 iterator 前调用 `set_epoch`。[S1]

### 5.2 Checkpoint 与数据进度

checkpoint 应对齐一个明确的完成 update：模型/optimizer/scheduler、全局 step、各 rank 已消费的数据位置、sampler 与数据 RNG、数据源混合器、shard 内位置、shuffle buffer 和必要 worker 状态。预取队列已生产但未消费的样本，不等于训练进度。

优先在固定 world size 下验证“连续运行”和“中断恢复”后若干 update 的样本序列、loss、参数状态；弹性 world size 恢复是另外的语义问题。可以保存确定性游标并重建未消费预取，也可以使用经过验证的 stateful loader，但不能只保存主进程的 batch 计数就假定复杂 iterable 管线可精确恢复。TorchData `StatefulDataLoader` 聚合 worker 状态，不会自动汇总跨 rank 状态；默认快进策略与自定义 dataset/sampler 状态的能力不同。[S8]

### 5.3 冻结特征复用和失效

“参数冻结”只说明参数不更新，不说明输出恒定。缓存/预取的有效性至少取决于：

- 原始样本与内容版本、精确帧/时间戳、view、裁剪/增强结果、输入 dtype/shape；
- tokenizer/预处理版本、文本和 padding/mask、条件信息；
- 编码器权重 hash、config、eval/train 状态、精度/autocast、相关设备实现；
- stochastic VAE 的采样语义、随机状态或实际抽样值；dropout/BN 等批次和状态依赖；
- 输出需要的梯度路径以及所有消费者的预期参数版本。

优先顺序是：**同次请求内复用 → 同 batch 多消费者复用 → 有界下一 batch 预取 → 持久跨步缓存**。前两者最容易证明；持久缓存随机增强后的特征会悄悄固定增强，通常不能作为等价优化。

如果 VAE 每次从 posterior 采样，可以研究缓存确定性的 posterior 参数而保留每次抽样；但这仍须证明原实现的调用次数、独立性与 RNG 序列要求。不能默认把抽样结果永久缓存。冻结参数但仍需要梯度传回输入时，`no_grad`、detach 或离线特征会改变训练。LoRA、EMA、在线更新或训练模式状态一旦变化，就不能按“冻结编码器”处理。

### 5.4 异步数据与 buffer 生命周期

producer 记录 ready event，consumer 显式等待；直到复制/消费结束，pinned source、GPU staging tensor 和 graph 输出均不能被覆盖。跨 stream 使用 tensor 应保证 allocator 生命周期正确。双缓冲要证明两份 buffer 真正独立；graph replay 往往会覆盖静态输出，需要在必要边界复制，而不是无条件 clone 一切。异常、取消和 checkpoint 也必须释放队列、文件句柄与设备资源。

## 6. 端到端计算重排：明确依赖，再试重叠

| 候选 | 可执行方式 | 保持的关键不变量 | 特别要测的失败方式 |
|---|---|---|---|
| 多目标共享同一 Robot batch | 一个数据入口产生 batch，各目标引用相同输入，冻结特征只算一次 | 用户报告所述目标确实原本应使用同 batch；loss 归一化和梯度贡献不变 | 误把原本独立抽样的目标合并；引用被原地修改 |
| 提早提交 VAE，再做 CPU 文本/图像准备 | 数据 ready 后 enqueue VAE，主线程继续独立 CPU 工作 | 增强与 RNG 顺序、VAE 输入已确定、consumer 等待 | 主线程准备并不独立；为输出检查意外同步 |
| 下一 batch 冻结编码预取 | 当前 backward 期间运行未来 batch 的 VAE/VLM；先只保留一轮未来特征 | 与当前 optimizer 更新无关；未来样本与参数版本正确；有界存储 | HBM/SM 竞争抵消隐藏时间；预取队列未持续补充；checkpoint 进度错位 |
| Robot/Ego batch 合并编码后拆分 | 对同一兼容编码器拼接输入，按保存的 offset 拆回 | mask、position、padding、loss 权重、batch-dependent 行为不变 | shape/长度膨胀、峰值内存、BN 或随机实现导致不等价 |
| 候选评分的 GT/reference 去重 | 一次计算固定 reference，各候选用索引引用 | reference 确实与候选无关、没有原地写入 | 原本包含候选条件或随机抽样，复用改变目标 |

对每个重排画最小依赖图，标明数据 ready、参数版本、随机输入、stream event、消费者和 optimizer commit。跨 stream 重叠只改变调度，不创造独立的 SM、HBM 或 PCIe。NVDEC 的核心解码由专用硬件执行，但视频转 RGB、resize/layout、tensor 拷贝、surface/显存占用仍可能与训练竞争；因此需要整条管线的实测。[S9]

用户流程记录的一个失败案例中，重叠隐藏约 97.5 ms，但组件受干扰增时约 111.4 ms，净收益为负。这是本方向应保留的负例：必须同时报告“隐藏多少”和“被重叠的双方慢了多少”，不以 trace 上出现重叠作为成功。

## 7. WAM 既有结果如何转化为候选

以下来自本次提供的报告摘录，没有重新跑实验，也未访问其中私有链接。

| 报告条目 | 可沿用的假设 | 不能外推的部分 |
|---|---|---|
| lazy episode/subtitle；紧凑 shard snapshot＋mmap | 降低 rank/worker 的 Python 元数据复制；保持源视频和采样规则 | 报告中的约 220 GB 节点内存不代表通用预算，也不能只加 RSS 推算共享页 |
| 置换保持 NumPy int64，避免 `.tolist()` | 排列每索引 8 字节并保持顺序，减少 Python 对象膨胀 | 该项属于报告特定 Qwen dataset 场景 |
| `data.vlm_cpu_preprocess=True` | 移动 tokenizer/图像准备，减少主线程暴露等待 | 报告 +12.07% 与 AE compile 合并，不能全部归因于数据 worker |
| `model.vae_before_vlm_input_prepare=True` | 改提交顺序，让 GPU VAE 与 CPU 准备并行 | 报告 +7.16% 与 time conditioning 去重合并 |
| Ego ACCV/NVDEC | CPU 解码瓶颈场景中 GPU 解码可能合适 | 2B 特定配置 7.424→9.409 的结果不适用于全部 14B/CPU/GPU 组合 |
| `--strategy A-ENC` | 当前 backward 期间预取下一轮冻结 VAE/Qwen，仅有界一轮输出 | 4082.481→3888.173 ms 是该实验；要重新验证持续生产、资源竞争和状态恢复 |
| `--cpu-decode-reuse 1` / `GEACT_CPU_DECODE_REUSE=1` | 同次 seek_mp4 内相同路径＋帧去重，分视角复制后独立增强 | 5816.429→4167.056 ms 是另一个 CPU 瓶颈场景；20 个 update finite 不能证明训练等价或收敛 |

报告数字不要相加。候选整合后重新测完整栈，因为前一项可能消除后一项赖以成立的瓶颈。

## 8. 必须完成的验收与资源隔离

**正确性验收：** 小数据集逐样本/帧核对；相同参考输入的一步 forward、loss、gradient、optimizer 更新；多步随机与混合源覆盖；至少覆盖实际 rank 配置的分片逻辑；checkpoint 中断恢复；shape/view/source 切换；缓存键/逐出/失效。浮点容差需要与基线数值噪声一起解释。finite、单步 loss 接近、测试全部通过各自只能证明有限性质。

**端到端验收：** 固定 commit、硬件拓扑、有效配置、真实样本工作量和缓存条件；对 A/B 或 A/B/B/A 交错重复测量，按 update 完成时间报告中位数、尾延迟和变动范围。预先规定足以分辨目标收益的运行长度与重复次数；不凭一个较快片段选赢家。分别报告启动/索引建立/编译成本和稳态训练，涉及格式迁移、离线特征或本地缓存时还要报告一次性转换/填充成本与存储增量。

观察到的最低收益必须超过该基线的自然波动，且不靠少处理样本、改变尾批或漏算阶段获得。长跑覆盖预取和缓存多个周转周期、真实工作集、数据源/shape 变化和至少一次 checkpoint；检查 PSS、pinned、shm、VRAM、FD 是否有界。冷启动改善可以单独成立，但不能伪装成稳态训练提速。

**隔离规则：** 并行 agent 可做代码阅读、离线小样本校验和独立资源实验；最终基准由主管分配独占 GPU、CPU cpuset、内存与约定的存储/网络窗口。多个 agent 共享文件系统时，元数据扫描、缓存填充、解压和打包也会互相污染。不得在共享机器执行全局 `drop_caches`；冷缓存通过独立子集、独立缓存目录或经过授权的隔离节点控制。重 profiler、编译、数据格式转换和最终计时不要混跑。

**结果包建议：** `effective-config.json`、`topology.txt`、`sample-ledger.jsonl`、`stage-timings.jsonl`、`resource-peaks.json`、`resume-check.json`、补丁、准确命令、基线/候选完整日志；一页结论写“瓶颈证据→改动→正确性→E2E收益及波动→资源代价→适用范围→负例/撤销条件”。这些是待实现的交付格式，不表示本次已产出测量数据。

## 9. 精确资料与已核验事实

以下 10 项均为官方或项目维护者资料。滚动文档可能变化；实现前以锁定版本再核验接口。工程建议与资料事实在上文分开陈述。

| 编号与精确链接 | 已核验事实；本任务用途 |
|---|---|
| [S1 PyTorch DataLoader 文档](https://docs.pytorch.org/docs/2.14/data.html) | workers 访问父进程 Python 对象可导致很大的内存复制；文档建议非引用计数表示。`prefetch_factor` 按 worker 计；支持批量 `__getitems__`；iterable 副本需分片；`in_order=False` 有复现与分布风险。说明 worker seed、`DistributedSampler.set_epoch` 及 padding/drop_last 行为。 |
| [S2 PyTorch pinned memory 与 non_blocking 教程](https://docs.pytorch.org/tutorials/intermediate/pinmem_nonblock.html) | 去掉 host wait 不等于 GPU copy/compute 自动重叠。有效重叠取决于 pinned source、不同 stream 和 DMA 等条件；主线程临时 pin 有额外开销。用于 H2D 候选与 buffer 生命周期验证。 |
| [S3 PyTorch Performance Tuning Guide](https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html) | NUMA 的 CPU/内存局部性与线程设置影响性能，给出 `numactl --cpunodebind --membind` 示例。用于根据实际 GPU/NUMA 拓扑分配 rank 和 worker。 |
| [S4 TorchCodec VideoDecoder](https://meta-pytorch.org/torchcodec/stable/generated/torchcodec.decoders.VideoDecoder.html) | exact seek 与 approximate 的保证不同；支持自定义帧映射、批量取帧、CPU/CUDA、FFmpeg 线程控制。CUDA 实际路径和 fallback 需核对。用于降低重复 seek，保证帧/动作对齐。 |
| [S5 NVIDIA DALI readers.video](https://docs.nvidia.com/deeplearning/dali/user-guide/docs/operations/nvidia.dali.fn.readers.video.html) | 标准 reader 使用 FFmpeg/NVDECODE，支持 CFR；真实 VFR 下 `skip_vfr_check` 可能导致问题。decode surfaces、prefetch 与内存存在权衡；网络文件系统上 mmap 未必更佳。 |
| [S6 WebDataset 维护者仓库](https://github.com/webdataset/webdataset) | tar 分片支持顺序读和大规模存储；IterableDataset 下严格 epoch 平衡和分布式采样需要设计。用于判断小文件/对象存储问题是否适合分片，而不是承诺视频 decode 自动变快。 |
| [S7 FFCV Parameter Tuning](https://docs.ffcv.io/parameter_tuning.html) | 缓存选择取决于数据是否放得进内存；worker 多不必然快；QUASI_RANDOM 与全随机策略不同，所核验文档注明不支持 `distributed=True`。用于筛掉不适合原训练语义的格式替换。 |
| [S8 TorchData StatefulDataLoader](https://meta-pytorch.org/data/main/torchdata.stateful_dataloader.html) | 提供 `state_dict/load_state_dict`，可利用 dataset/sampler 状态；聚合 worker 状态，不自动聚合 rank 状态；默认可通过 batch 数快进。用于精确恢复的实现边界。 |
| [S9 NVIDIA NVDEC Application Note 13.0](https://docs.nvidia.com/video-technologies/video-codec-sdk/13.0/nvdec-application-note/index.html) | 核心视频解码使用专用硬件；codec/profile 支持与 GPU 代际相关。该事实不证明包含转换、拷贝和后处理的完整 GPU 视频管线对训练没有竞争。 |
| [S10 NumPy memmap](https://numpy.org/doc/stable/reference/generated/numpy.memmap.html) | 可按需访问文件局部而无需一次读取整个文件到内存，支持只读映射。用于静态紧凑索引；不应解释为无物理页开销或无存储读取。 |
