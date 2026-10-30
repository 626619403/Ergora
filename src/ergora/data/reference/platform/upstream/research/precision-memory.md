# 低精度、显存与检查点：三个方向 agent 的执行方案

研究日期：2026-10-26。基于用户提供的《WAM训练加速》和《从WAM优化实践到多Agent协作》附件，以及下列公开官方资料。本次未访问附件中的私有外链，未运行用户仓库、未复现实验。文中“附件报告”仅表示用户材料陈述；“建议”是待验证候选。

## 先给负责人的判断

WAM 的低精度路线已经明显超过“打开混合精度”阶段。下一轮不应让 agent 再笼统提议 FP8、SAC 或 8bit Adam，而应要求它找到当前关键路径里仍然昂贵、未覆盖或失效的具体调用，并回答：省下的 GEMM 时间是否大于量化、打包、布局转换、尺度更新和缓存成本？省下的显存是否帮助一个更快的完整方案？

附件原结构14B的4.9557样本/秒/卡，是GAS16、训练FFN/候选投影FP8、VAE FP8、优化器和通信等组合结果，不能归因于单一量化开关。部分FFN/VAE单项消融来自H7680宽浅模型，不应移植成H4096原模型的预期收益。附件对fast accumulation明确是有限值/更新通过、未测收敛；8bit优化器20步参数更新L2差1.574%、VAE latent NRMSE约3.8–3.9%都只属于各自短测证据。另一个附件记录过切回融合FP32 AdamW反而更快，说明优化器必须按当前基线重测。

建议设置三个可按任务唤起的方向 agent：①低精度计算与数值，②激活/显存容量，③优化器与持久检查点。另由未编写候选的验证者运行共同质量门禁。角色不是三套独立“最新基线”；资源、验收和合并仍归一个负责人。

## 一、低精度计算与数值 agent

### 1. 硬件与方法选择

| 精度/机制 | H200 的适用判断 | 本任务如何试 |
|---|---|---|
| BF16混合精度 | 作为现有训练参考；不要把所有归一化、归约、损失和优化器状态一并降精度 | 明确矩阵输入、累加、输出、master weight和状态dtype，保存实际backend开关 |
| TF32 | 是FP32矩阵乘/卷积的计算模式；不是更小的参数存储dtype，也不会直接加速已经执行BF16的GEMM | 仅在trace证明仍有显著FP32 GEMM/卷积时，做IEEE FP32对照；不要对JVP参考或敏感统计悄悄全局启用 |
| 普通FP8 E4M3/E5M2 | Hopper/H200可研究的主方向；数值取决于尺度粒度、算子及累加方案 | 先大矩阵训练FFN/无梯度候选；逐层、逐路径选择，不默认量化全部算子 |
| MXFP8、NVFP4 | Transformer Engine将这两条硬件支持路线放在Blackwell；不能把B200方案当H200原生加速能力 | 作为单独Blackwell迁移实验；在H200做模拟、存储压缩或解量化，不等同于原生FP4训练吞吐 |
| 8bit optimizer | 量化Adam状态，与FP8 Tensor Core计算是不同层次 | 交给第三方向独立比较，不和FP8速度结论混合 |

硬件与数值依据[S1][S5]。不要根据某库支持“FP4 tensor”就断言H200有对应Tensor Core指令。FP8不是稀疏计算；继续分别报告BF16等效MFU、精度加权MFU与完整有效吞吐。

### 2. 先调查，后挑真实候选

1. 从实际训练入口列出五条路径：训练DiT/FFN；cotrain的N4无梯度候选；选中候选的有梯度重算；冻结VAE/Qwen编码；MeanFlow解析JVP。记录每条路径的参数版本、RNG、输入形状、stride、调用频次、loss消费者。
2. 用真实捕获的输入建立微基准矩阵。至少覆盖原H4096与实验H7680各自真实M/N/K、1/2/3视角、不同目标、训练前中后段的激活范围；不只测试随机正态、连续矩阵和整除tile形状。
3. 将完整linear计时拆成amax/scale、cast/pack、布局转换、GEMM、输出与额外分配；训练路径包括forward/dX/dW。基准须对比当前compiled BF16和已有自定义FP8，而不是只对比eager框架。
4. 为每个候选保存“调用链确实命中”的trace和算子计数。浮点dtype变成FP8不等于FP8高效内核被调用。

候选按当前证据排序，通常从以下几项中选2–3个，不同时做全部：

| 候选 | 最小实验 | 通过以后才做 |
|---|---|---|
| 当前自定义FFN与torchao的tensorwise/rowwise/rowwise_with_gw_hp比较 | 同一真实形状比较完整forward+dX+dW时间与误差；最后一种保留较高精度dW计算，作为精度折中 | 明确哪些层/矩阵受益，保留小矩阵和敏感层BF16 fallback；不要为接入TE重写整网 |
| 减少重复量化与pack | 量化权重缓存只跨越权重不变的microbatch；比较缓存驻留与每轮重算开销 | 用真实更新版本号维护失效；验证ZeRO重建、恢复、EMA或手工load、参数替换均刷新 |
| N4候选FFN/大方阵投影FP8覆盖 | 在完全相同候选噪声、输入、权重版本上shadow运行；不仅比输出NRMSE，还比judge排序与选择 | 在实际选择逻辑下验证选中候选的有梯度重算与训练质量；不能假定no_grad使近似无害 |
| VAE热点卷积FP8及channels-last布局 | 只对附件识别的热点卷积做实际cuDNN支持探测；计入布局变换、量化、工作区 | latent分布、下游loss、视频/动作质量通过后扩大；冻结网络仍决定训练分布 |
| fast accumulation开关 | 对up/down的forward/dX/dW分别测，并给出累计更新漂移 | 作为独立数值变更；1%左右短窗收益必须超过噪声并通过长程门禁 |
| 现存FP32计算尝试TF32 | 确认FP32热点，不同时更改BF16/FP8配方 | 记录matmul和conv分别生效的精度开关与局部误差 |

torchao官方给出上述三类配方，也明确小矩阵可能因量化开销而更慢；公布的Llama/FSDP收益不能作为WAM预测[S3]。TE为microbatch内权重不变提供FP8缓存接口，是可借鉴的缓存生命周期[S2]。

### 3. 量化缓存必须成为可检查的协议

缓存key建议包含参数身份、显式weight_version、device、shape/stride、量化配方/尺度版本、输出布局。训练中一个真实optimizer update结束并完成必要参数同步后，版本前进；恢复检查点、load_state_dict、EMA切换和权重替换同样失效。只有确认所有相关依赖未变才复用。不要仅依据Python对象地址或“第几个逻辑轮”；ZeRO可能在同一对象内更新数据。

缓存寿命要覆盖forward/backward需要的同版本数据，不能在尚有反向消费者时复用写缓冲。若采用delayed scaling，还要明确amax历史何时更新、重算是否重复更新、恢复是否保存尺度状态。冻结权重可长期缓存，但冻结特征的key还需要样本、帧索引、增强、mask和预处理版本。

### 4. JVP单列，不能顺带通过

保留附件中JVP BF16旁路作为首轮默认。训练FFN的custom backward正确，不意味着torch.func JVP或解析JVP也正确；修改前向非线性、布局、量化语义后应明确“JVP对应哪个数学函数”。量化映射本身的不连续性，也使直接对量化算子做有限差分不是训练所需平滑导数的万能oracle。

建议在可承受的小形状上，用FP64平滑参考比较解析JVP；取多个方向和尺度，结合autodiff JVP/中心差分扫步长、JVP线性性及与VJP的内积关系。再在真实BF16输入上分别比较primal、tangent以及最终MeanFlow目标和各loss。若路径需要穿过custom autograd.Function，补其明确的JVP支持或显式BF16 fallback，并验证编译后仍走该路径。任何“目标由BF16网络导数构造而前向换成近似FP8网络”的选择，都应作为训练配方决定记录，不能称完全等价。

### 5. 接口与版本规则

截至调研，PyTorch 2.14文档已经存在公开`torch.nn.functional.scaled_mm`，含尺度配方与`use_fast_accum`参数[S4]。不能把“只有私有torch._scaled_mm”当作现在的事实。但用户安装版本未知；当前自定义封装若用私有算子，应固定PyTorch/CUDA/torchao/TE/cuDNN版本，在升级分支验证签名、输出、实际dispatcher、autograd/JVP与SAC，再决定迁移。不要要求生产仓库为一个新API盲目整体升级。

## 二、激活与显存容量 agent

### 1. 先交付一份按生命周期的内存账本

按rank和训练阶段测：初始化、第一轮、图capture、候选生成、选中候选重算、各次反向、真实更新、参数AllGather、检查点staging、输入形状切换。记录稳态峰值和冷启动/检查点峰值，不能只重置统计后保留最好的一段。

| 指标 | 表示什么 | 常见误判 |
|---|---|---|
| allocated及峰值 | PyTorch活跃tensor占用 | 不能代表全部进程/整卡占用 |
| reserved及峰值 | PyTorch缓存分配器管理的内存 | 不是全部活跃tensor；A与R不能相加 |
| NVML整卡/进程占用 | 驱动所见设备用量，采样粒度有限 | 包含上下文、第三方库等；与另一个时间点的R直接相减不能准确归因 |
| memory snapshot | 分配栈、块与生命周期、分配器内碎片 | NCCL等绕过PyTorch allocator的分配可能不可见 |
| CPU RSS/PSS、容器限额、pinned host、页缓存 | 主机容量与checkpoint/data worker压力 | pinned内存不是显存；共享页缓存不能按每worker的RSS简单累加 |
| graph私有池与缓存存活对象 | capture稳定地址与重放buffer所需容量 | Graph pool通常已体现在分配器统计里，不能再和R机械相加 |

官方分配器与graph生命周期依据[S7][S8]。`empty_cache()`不能释放活跃tensor，不应每步调用掩盖生命周期问题。分配器选项应在证据表明碎片是原因时试，不能把缓存增长、图池或仍被引用的输出统称“碎片”。

### 2. 先清生命周期，再做重算/分片

检查候选全集、评分参考、debug输出、日志张量、callback闭包、重算上下文、prefetch和graph输出是否被不必要地保留。每个提前释放点必须有最后消费者证据；独立stream上的消费者须完成或有正确record_stream/event依赖。

实验顺序建议：当前策略 → 少量region重算 → SAC保存昂贵算子 → 局部层组组合。不能一律SAVE全部GEMM：某些输出很大、保留会使并行分支峰值叠加；FP8省下的计算又可能改变最优保存策略。按“节省GiB、增加完整更新毫秒、可解锁的batch/缓存/并行方案”画Pareto表，选择最快可行方案而非最低显存。

附件已有整组重算使B6单项变慢、但支持B8的例子；这属于容量换吞吐机制。若增大microbatch，严格对照应尽量调整GAS保持有效batch、loss归一化和更新频率；无法保持时另列算法配方实验。

### 3. SAC+FP8的具体检查

附件按`aten._scaled_mm`保留FP8 GEMM输出；这是现有实现相关的策略，不是永久有效的算子名规则。agent需要在当前安装栈记录forward和backward/recompute操作，统计每类GEMM/quantize调用数、SAC策略命中、保存tensor字节数。升级到公开scaled_mm、TE custom op、库融合、编译分解后可能改变dispatcher边界；不得仅看配置里有字符串就宣称“避免了重算”。保存GEMM输出也不自动证明所有量化步骤都不再执行。

用非重算参考核对每个目标的梯度、共享参数更新、dropout/RNG和FP8 amax状态。PyTorch建议显式使用`use_reentrant=False`；默认determinism check检查shape/dtype/device，**不是数值相等验证**。重算时行为受全局状态影响可能静默产生错误梯度[S6]。WAM存在多目标、共享前缀、候选选择，必须覆盖这些组合，而不是只测独立block。

### 4. 扩大容量时要比较整套代价

ZeRO2已分片优化器状态与梯度，不能再把“状态/DP卡数”当新增收益。ZeRO3或FSDP2参数分片是另一类候选：可减少复制权重，但引入参数收集、prefetch、峰值和graph兼容性成本；先与通信方向联合小测。CPU/NVMe offload作为容量不足的候选，不能默认是速度优化[S10]。

与低精度方向一起测`SAC × FP8配方 × 图模式 × microbatch/GAS`少量有解释力的组合；不要笛卡尔积穷举。禁止两个方向同时修改同一checkpoint边界后仍称独立单变量。

## 三、优化器与持久检查点 agent

### 1. 优化器先看真实更新，而非每个逻辑轮

构建包含实际参数分片、真实梯度分布、梯度裁剪、weight decay、状态dtype的对照：当前融合FP32状态AdamW、8bit状态AdamW，以及必要的混合策略。测optimizer本体和随后参数同步，还要测完整有效训练吞吐。记录首次状态初始化，避免把冷启动隐藏在短测外。

8bit moments通常只减少参数相关状态；对激活主导的网络帮助有限，且部分小tensor仍使用32bit状态[S9]。它不会自动降低权重、master weight、全部梯度或激活，也不会自动快于融合AdamW。`zero_allow_untested_optimizer=True`只是放行配置，不是兼容性证明：检查分片state layout、state_dict保存/恢复、跨rank权重一致性、溢出/跳过更新、None/零梯度与step计数。

附件原结构组合报告约省10.24GiB/卡，应作为该参数数目/DP分片/实现下的历史测量，不推成新模型固定收益。若省下容量能换更少重算、更大的量化缓存或更好的microbatch，即使optimizer本体略慢也可能合算；反之应允许回到FP32状态。

GAS4→16改变真实更新频率和有效batch，不是单纯通信优化。固定总样本/视频窗口和更新定义，分别报告每逻辑轮、每真实更新、每样本、达到目标质量的时间；调整学习率或优化器超参数须另列，不与保真基线混合。

### 2. 两种checkpoint不要混用概念

activation checkpoint/recompute处理反向所需激活；持久训练checkpoint用于进程故障后恢复。后者应测保存对完整训练的摊销损耗、CPU/pinned峰值、I/O带宽与实际可恢复性。

先保持当前DeepSpeed保存方案正确，核对所有参与rank调用保存，以及model、optimizer、scheduler与额外client state[S11]。再考虑异步分片持久化。DCP方案是可研究的参考，不表示它能未经适配直接替换用户的DeepSpeed/自定义8bit optimizer序列化。

异步保存至少有三种状态：一致快照已暂存、后台I/O写完、完成清单已发布。下一次optimizer修改参数前，必须确认相关D2H staging已完成或采用等效快照隔离；不能认为async调用返回就已有稳定副本。最新DCP示例分别等待staging与upload future；也建议最多一个异步保存请求在途，避免CPU/pinned内存堆积[S12]。多个状态变量若在forward就会改变，例如FP8 amax历史，也必须纳入一致快照边界，不能只等待下一次optimizer.step。

### 3. 恢复验证必须是一次真训练实验

状态清单：模型/master weights、优化器moments与step、scheduler、GradScaler（若实际使用）、EMA、FP8 scales/amax历史、各rank RNG、采样器/数据游标与已消费样本序列、GAS内位置和未提交梯度、任务权重、配置和源码版本。优先只在真实更新边界保存，减少恢复中间累积状态的复杂度。量化缓存可重建，但恢复必须强制失效并重建；不可读取旧进程同名缓存。

对照“连续K步”与“前K1步→保存→退出→新进程加载→再K2步”；核对样本/RNG、step、各参数状态、下一次更新、短期loss。对合理非确定性设置预先定义的容差，不随结果放宽。另测一个rank写盘失败、磁盘不足、进程中断与不完整manifest：恢复器只接受已完成版本。改变world size/并行策略的恢复属于单独兼容性任务，不能由同拓扑恢复通过推断。

## 四、共同验收：短测筛选，长程质量决策

建议以五级门禁组织，不把所有候选都跑满生产规模，也不把20步finite当成质量结论。

| 门禁 | 必须检查的证据 | 通过能说明什么 |
|---|---|---|
| G0 调用与契约 | 已安装版本/硬件匹配；原始样本、augmentation、mask、权重版本一致；真实kernel命中；layout与尾块支持 | 测到的是计划中的实现 |
| G1 局部数值 | FP32/适当FP64参考；abs/rel误差、NRMSE与分位数、最大误差、cosine；NaN/Inf、零值/饱和率、outlier；dX/dW/JVP分别检查 | 在覆盖范围内局部误差受控 |
| G2 组件与短更新 | 四目标loss分别记录；梯度norm/clipping、更新norm/方向、零更新、尺度历史、跨rank一致性；N4选择翻转率及分数margin | 未发现短期失稳和接线错误 |
| G3 完整系统 | 独占验收；互换顺序复测；真实更新和完整数据等待；峰值、重编译、GC、缓存增长、checkpoint与恢复 | 完整性能改善可复现且生命周期覆盖充分 |
| G4 长程质量 | 固定数据预算/样本量、独立验证集、多个随机种子；跨学习率阶段/训练阶段；最终目标质量与time-to-quality | 可决定是否进入长期训练基线 |

阈值应由任务负责人事先确定：用同精度重复运行差异作为噪声参考，定义“可以接受的质量退化”，给统计区间或重复实验，不以“差异不显著”自动推导等价。小批量FP64可用来定位误差，不能替代真实shape上的分布与训练验证。

WAM的G4应至少覆盖：各目标验证loss、视频生成/时序一致性与条件遵循、动作误差和机器人任务成功率/安全约束相关指标（按现有评测体系选择）；候选judge分数与选择分布；每个噪声时间区间、视角、长短视频、异常动作幅值。冻结VAE近似可能持续改变训练输入；N4近似可能改变离散选择；JVP近似可能改变训练目标。它们的任务指标应分开归因，最后再验收组合。

不要规定“一律NRMSE<1%”或“一律2000步够用”。验证长度应覆盖尺度适应、warmup/学习率变化、实际checkpoint与阶段切换，并与训练目标和模型规模相称。预算高的优势是能保留BF16对照、运行多seed和独立验证，不是省略质量门禁后更快消耗GPU。

## 五、可交付给负责人的内容

三个方向统一提交：baseline/candidate commit；模型/权重版本；有效配置；路径与shape覆盖；局部和完整时间；A/R/N与host峰值；误差和quality证据；失败条件；维护成本；支持/回退表。结论限定为“局部快”“完整快但质量待验”“可合入”“停止”，而非只写“优化完成”。

对有限值通过而缺长程验证的候选，允许作为实验性配方保留，不能替换训练质量基线。首轮建议优先做：当前FP8权重cache生命周期审查、SAC实际命中与重算计数、融合FP32/8bit optimizer的完整更新对照，以及固定版本的恢复实验；这些都直接承接附件已有成果，通常比另起FP4研究更贴近H200当前问题。

形式化验证只用于很小且稳定的辅助逻辑：缓存版本失效、checkpoint提交状态机、分片索引映射等可选择性质/状态机测试，再按收益引入SMT/TLA+。它不能替代FP8误差、真实GPU行为或训练收敛评测，本节不建议证明整个训练栈。

## 官方资料索引（12项，均已联网核对）

1. [Transformer Engine：Using FP8 and FP4](https://docs.nvidia.com/deeplearning/transformer-engine/examples/fp8_primer.html)。Hopper FP8、Blackwell MXFP8/NVFP4、尺度配方。
2. [Transformer Engine PyTorch API](https://docs.nvidia.com/deeplearning/transformer-engine/api/pytorch.html)。`is_first_microbatch`与FP8权重缓存语义。
3. [torchao Quantized Training](https://docs.pytorch.org/ao/stable/workflows/training.html)。配方、forward/dX/dW、编译组合、量化成本与shape约束。
4. [PyTorch 2.14 functional.scaled_mm](https://docs.pytorch.org/docs/2.14/generated/torch.nn.functional.scaled_mm.html)。公开签名、scale recipe、fast accumulation。
5. [PyTorch Numerical accuracy](https://docs.pytorch.org/docs/2.14/notes/numerical_accuracy.html)。TF32、BF16 reduced-precision reduction和数值边界。
6. [PyTorch checkpoint API](https://docs.pytorch.org/docs/2.14/checkpoint.html)。SAC、non-reentrant、RNG、默认determinism check范围。
7. [PyTorch CUDA semantics](https://docs.pytorch.org/docs/2.14/notes/cuda.html)。A/R、allocator、stream、graph私有池生命周期。
8. [PyTorch Understanding CUDA Memory Usage](https://docs.pytorch.org/docs/2.14/torch_cuda_memory.html)。snapshot、非PyTorch分配与host pinned可见性。
9. [bitsandbytes 8-bit optimizers](https://huggingface.co/docs/bitsandbytes/main/en/optimizers)。参数相关状态节省、小tensor保留高精度及逐层配置。文档的泛化速度/精度宣传不作为WAM保证；main文档也不代表用户已安装版本。
10. [DeepSpeed ZeRO](https://deepspeed.readthedocs.io/en/latest/zero3.html)。stage状态归属、分片、offload。
11. [DeepSpeed Getting Started：Model Checkpointing](https://www.deepspeed.ai/getting-started/)。参与rank共同保存、optimizer/scheduler/client state。
12. [PyTorch DCP asynchronous checkpoint recipe](https://docs.pytorch.org/tutorials/recipes/distributed_async_checkpoint_recipe.html)。CPU staging、pinned容量、一份在途请求与staging/upload等待。

以上stable/latest/main页面可能继续变化。实施时记录实际安装版本，并把采用的页面/接口版本写入实验manifest；本报告没有替用户判断其环境已经支持上述最新API。
