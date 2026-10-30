# 计算、编译与内核方向：面向 H200 训练的 agent 工作协议

核对日期：2026-10-26。本文供总负责人拆任务与集成；不是已在当前仓库运行过的优化配方。已阅读用户提供的 WAM 工作经验及成果报告文本；下文历史实验只用于形成假设，不视为对当前代码的复现。公开资料以官方文档、作者仓库为主。PyTorch 的 `stable` 页面本次跳转到 2.14；实施时必须匹配实际安装版本，不能把最新文档中的选项直接加到旧版本。

## 1. 本方向负责什么

目标是减少完整训练更新的关键路径时间，覆盖主机提交、Dynamo/AOTAutograd/Inductor、CUDA Graph、张量形状与布局、attention、卷积、GEMM 周边与自定义 kernel。它不单独改变模型结构、训练目标、输入截断、有效 batch 或数值精度；这些变化需要负责人登记为另一类实验。

首先回答：当前慢的是 CPU 未及时提交、GPU 算得慢、重复计算、必要同步，还是其他组件造成的等待？只有时间线证明本方向能影响完成时间，才开展改动。`cudaStreamSynchronize` 的长条通常是 CPU 等待已经排队的工作；不能把它的 CPU 时长再加到 GPU kernel 时长上。

**三个基线要同时存在。**

|名称|用途|规则|
|语义参考 R0|检查候选是否保持约定数学行为|通常是已验证的 eager/高精度小规模参考；不必是最快实现|
|当前生产基线 B0|决定是否值得保留|包含已生效 compile、融合、布局、图、缓存与框架优化；禁止回退成朴素 PyTorch 再声称提速|
|候选 C1|单项与组合测试|相同输入契约、参数版本、梯度路径和计量边界；附开关与回滚方式|

用户 WAM 记录提示：2B 路径已采用 DiT/JVP 的 `reduce-overhead`，14B 路径采用分组 `default` 并另做冻结 Qwen 局部图。应先读取最终配置与调用链，不能把“开启 compile”当作所有任务的第一项新优化。

## 2. 方向 agent 的输入、过程与交付

### 2.1 任务必须提供的输入

```yaml
task_id: compute-001
baseline:
  commit: required
  effective_config: required
  image_digest: required
  torch_cuda_cudnn_triton_versions: required
  hardware: H200_Hopper
hotspot:
  callsite: required
  phase: forward_or_backward_or_jvp
  invocations_per_update: required
  critical_path_ms: measured_or_explicitly_unknown
  shapes_strides_offsets: required
contract:
  preserve: [model_math, loss_weights, sample_order, parameter_versions]
  required_paths: [forward, backward, jvp_if_used]
  numerical_thresholds: agreed_before_experiment
  representative_workloads: required
resources:
  gpu_lease: assigned_by_supervisor
  max_trials: bounded
  walltime_budget: bounded
deliverables:
  - reproducible_patch_and_rollback
  - raw_measurements_and_profile_paths
  - validation_results
  - handoff_with_keep_integrate_or_stop
```

### 2.2 执行顺序

1. **读取实际执行链。** 识别模块是否冻结、`grad_enabled`、autocast、checkpoint、JVP、参数共享、图缓存、分布式包装及实际 backend。记录 forward/backward/JVP 的真实调用次数。
2. **建立可回收时间预算。** 用关键路径中的暴露时间与可消除工作量给出收益上界；不能把所有 stream 的 kernel 时长相加作为上界。先解决重复工作、异常布局、明显 fallback，再考虑重写成熟 GEMM。
3. **重放真实局部问题。** 保存 shape、stride、storage offset、dtype、mask、requires_grad、权重版本及真实输入分布。纯随机 contiguous 张量只能用于补充边界测试。
4. **提出最多几个可证伪假设。** 每项写出预期减少的启动次数/字节/计算、可能新增的转换与缓冲成本、失败会看到什么。一次改变一个主要机制。
5. **局部验证后回到组件。** 先语义与导数，再无 profiler 的包装调用时间；通过后测试组件与完整更新。不要等所有 kernel 完工才做第一次整体集成。
6. **把失败留在记录中。** 保留配置、原始测量、失败原因、再次尝试的前提。负责人决定是否推进下一候选，方向 agent 不自行替换全局基线。

### 2.3 统一交付卡

|字段|要求|
|结论|保留 / 待集成 / 停止；禁止只写“看起来更快”|
|机制|哪个关键路径依赖被缩短，哪些代价增加|
|数值|参考与候选、输入范围、forward/gradient/JVP/更新检查、阈值、失败样本|
|时间|核心 kernel、完整包装调用、组件、完整 update 分别报告；未测写未测|
|资源|allocated/reserved/NVML 峰值，编译与 graph 数，启动与首次使用时间|
|证据|commit、配置、命令、设备与进程归属、原始日志、trace、候选补丁|
|适用域|已覆盖形状、相机数、训练目标、dtype、mask 与导数路径；域外 fallback|
|后续|待验证交互、回滚开关、重新尝试条件|

## 3. 热点驱动的候选树

|观测证据|先试的低成本候选|进一步候选|避免的误判|
|GPU 有空档，前后是密集短调用；CPU 提交迟到|移出日志/标量回读、合并小调用、减少重复 Python 调度|调整 compile 边界、局部 CUDA Graph|GPU 等数据或通信，不必然是 Python 慢|
|同一功能不断重编译，首次形状切换长停顿|查 guard 失败来源，有限 shape/path 预热|少量 shape bucket、局部 dynamic 维度、缓存预算调整|直接提高 recompile limit 可能掩盖逐步变化的 Python 标量|
|大量 pointwise/copy/transpose 围绕 GEMM|确认当前编译融合与 layout propagation|epilogue 融合、量化/打包融合、专用 Triton/CUDA|只计核心 GEMM，忽略包装的转换与写回|
|GEMM 实际地址错位、stride 异常、低效实现|检查分布式包装后的指针与 storage offset|不改数学语义的扁平缓冲 padding/布局修复|Tensor contiguous 不保证具体库所需的地址对齐|
|attention 占据关键路径且 backend 不理想|核对 SDPA/FlashAttention 实际选中实现|适配 Hopper 优化版本、packing/varlen 或局部融合|开了开关不等于使用该 kernel；forward 支持不等于 JVP 支持|
|VAE conv 热点且输入 shape 稳定|确认 cuDNN 算法选择、布局转换、重复编码|autotune、channels-last、邻近融合/graph plan|单卷积快，但全模块反复转 layout 更慢|
|张量工作被重复执行|先算低维条件再广播、合并兼容调用、删除未消费结果|跨组件计算重排，由负责人审查依赖|“冻结”不代表输入、增强、状态永不变化|
|大 GEMM 已接近当前形状的库性能|评估周边成本与调用组织|仅对特殊 shape 考虑 CUTLASS/CuTe/Triton|低 warp occupancy 或高 Tensor-pipe activity 单独都不能证明瓶颈|

优先级可以由“预计可回收完整毫秒 × 成功把握 ÷ 验证成本”排序，但这些值必须标记为估计。不要把估计写成测量。一次聚焦 1–3 个能解释当前瓶颈的候选。

## 4. torch.compile 与主机提交 agent

### 4.1 先建立编译地图

把每个热路径记录为：调用位置→Dynamo 区域→graph breaks→AOT 前反向→Inductor kernel/外部库调用→CUDA Graph 是否真正重放。用 `TORCH_TRACE`/`tlparse` 看全局区域，用 `TORCH_LOGS` 定位重编译和断图。[R1]

重点调查：每步变化的 Python int/float、`.item()`/`.cpu()`、tensor 驱动 Python 分支、日志/断言、循环内动态创建对象、训练目标与相机数切换，以及配置关闭后仍走旧缓存。低频 I/O 可保留在编译区域外；不为了消除一次无关断图扩大修改范围。

### 4.2 编译边界与模式分开测试

|维度|候选|如何判定|
|边界|单 block、少量 block 一组、组件整体|测融合收益、Python 调用、编译耗时、激活保活、反向梯度就绪时机|
|算法选择|`default` 与 `max-autotune-no-cudagraphs`|先隔离 autotune 的 kernel 选择收益，记录首次搜索成本|
|图重放|`reduce-overhead` 或当前版本支持的局部 graph|确认没有跳过捕获，衡量额外显存池、输入复制和生命周期|
|shape|有限静态 bucket、默认自动 dynamic、已知维度标记 dynamic|比较总运行收益与新增图/缓存数，不默认 `dynamic=True` 最快|

官方 API 明确：`fullgraph=True` 要求捕获单一计算图，不能满足时报错；它不等于 CUDA Graph。`max-autotune` 默认会启用 GPU 图，因此若要区分 autotune 与 replay 收益，应先用不带图的模式。`reduce-overhead` 可能增加工作区显存，且不保证每段都能捕获。[R2]

分组编译的组大小是实验变量，不是经验常数。WAM 的“每 3 层”来自特定结构、重算和通信组合；变化后需要重测。禁止为了取悦编译器复制可训练 Parameter 或删除原模块注册，除非权重身份、optimizer state、checkpoint 名称映射均被独立验证。

### 4.3 有限形状先处理合法路径，再处理不必要变化

先列相机数×任务×batch×序列 bucket×grad 模式，记录真正出现的组合；不要机械预热全部笛卡尔积。对每个高频组合预热一次再循环切回，检查是否复用。动态维度必须在进入编译函数前标记；对于数据依赖的 Python 控制流，dynamic shape 不是通用修复。[R4]

提高 `recompile_limit` 仅用于已证明是有限合法变体且有内存预算的情况。改变文本截断上限、帧数、重复噪声数属于输入或算法改变，需要单列；padding 也必须验证 mask 和 loss normalization。

## 5. CUDA Graph agent

优先候选是形状有限、控制流稳定、CPU 介入少的热组件。例如冻结编码器的局部路径、稳定 DiT 组或短 AE 计算。先证明提交成本可见，再捕获；不要把整模型捕获作为成功标准。

**捕获前核对六件事：**

1. 输入、参数与临时缓冲的地址/生命周期契约；使用静态输入复制时计入复制成本。
2. forward、backward、JVP、checkpoint 重算与 optimizer 更新分别在哪里；图是否依赖更新前的参数值或导数状态。
3. 一次输出是否被多个目标、后续反向或下一轮消费；下一次 replay 是否覆盖尚未消费的存储。
4. 随机操作是否遵守训练所需 RNG 序列；既检查可复现性，也检查错误重复同一个 dropout/noise 的情形。
5. 是否存在 CPU operator、设备回读、不支持的 custom op、动态分配/分支导致跳过或重新捕获。
6. 每种 shape/path 的图数、活跃与保留显存以及完整任务余量。

CUDA Graph Trees 可以管理若干路径与内存复用，但不同输入 shape 仍可能生成多个录制。保留旧输出跨 replay 需要明确处理；`cudagraph_mark_step_begin()` 应对应真实的新迭代边界，不能每层或每次调用随意标记。需要复制旧输出时，把复制成本算入候选。[R3]

用“稳定形状→切换 1/2/3 视角→切回→延迟消费旧输出→训练/无梯度路径交替”的场景验收。若图私有池使更有收益的 batch/工作集无法装入，应缩小捕获范围或撤回。禁止每步清空 allocator/cuBLAS workspace 伪造低显存；那会破坏正常缓存与性能行为。

## 6. 形状、布局、GEMM 与融合 kernel agent

### 6.1 真实布局调查

对热点的 activation、weight、gradient，在分布式包装前后、首次 optimizer 更新后分别记录 shape、stride、storage_offset、data_ptr 对齐余数、dtype。WAM 曾出现扁平参数带来的错位；其历史“去掉 scalar bias”改变了参数集合，不能推广成通用保真修复。优先研究不改变数学语义的布局/packing 修复，再评估额外复制是否抵消收益。

先确认 GEMM 的 M/N/K、转置方向、batch/sequence 合并方式、调用频度。一个大矩阵很快，不代表其 dX/dW、JVP 或小 M 情况也快。训练 FFN 应覆盖 up/down 的 forward、dX、dW，以及实际采用的 JVP 路径。

### 6.2 候选逐级升级

1. 删除无用 materialization 与重复 reshape/copy；区分 view 与实际拷贝。
2. 保持连续 layout 贯穿一组算子，减少来回转置；必要转换纳入时间。
3. 合并相邻 pointwise、norm、bias/activation、cast/scale/pack；对比当前 Inductor 已生成的融合 kernel。
4. 扫有限 tile、warp、stage、split-K/persistent 候选；计入额外 workspace/reduction。
5. 明确存在库实现空缺或特殊 shape 时，再选 CUTLASS/CuTe/CUDA 内核重写。

H200 是 Hopper。Hopper 的 TMA、WGMMA/warp specialization 可作为适用候选；不要把 Blackwell 的 `tcgen05`、Tensor Memory、原生 NVFP4 或 B200/B300 的 tile/吞吐常量套入 H200。CUTLASS 文档明确区分 SM90 与 SM100 的实现结构。[R5][R6]

### 6.3 自定义 kernel 的接口验收

必须处理边界 shape、非理想 stride、尾部 mask、alias/in-place 契约、不同 stream、AMP、保存张量以及需要的反向/JVP。只实现 forward 的 kernel 可以用于已确认无导数的分支；不能悄悄替换训练分支。必须有域外 fallback，且记录 fallback 次数，防止“快路径只覆盖了测例”。

Triton/CUDA 候选除数值测试外，按改动风险使用 compute-sanitizer 检查越界与竞争。Triton 的 interpreter/debug 模式用于诊断，不能用于性能比较；正式测量需关闭调试插桩。[R9]

## 7. Attention 与 convolution agent

|子方向|必须保留的契约|候选与验证|
|标准 attention|causal 对齐、padding mask 语义、scale、dropout、GQA/MQA、head dim、varlen 边界|对比实际 SDPA backend 与适用 FlashAttention；记录 fallback；分别检查 forward/backward/JVP；不能仅根据包安装成功判断生效|
|线性 attention|递推状态、chunk 边界、归一化与门控语义|使用对应算法的融合实现，不能用 softmax FlashAttention 替换；状态缓存需跟参数/样本绑定|
|VAE conv|padding/stride/dilation/groups、时间轴因果性、dtype、冻结状态|固定常见 shape 后测试 cuDNN autotune、channels-last、邻近融合；统计 layout 转换与 workspace|
|训练 conv|dX/dW、梯度累积、determinism 要求|不能从冻结 VAE 前向收益推出训练总收益；完整前反向计时|

当前 FlashAttention 官方仓库已经列出面向 Hopper/Blackwell 的 FA4 CuTeDSL；FA3 部分列明 BF16/FP16 forward+backward、FP8 forward。版本号不能代替支持矩阵，尤其不应由“有 backward”推导“有 `torch.func.jvp` 或高阶导数”。针对用户实际 MeanFlow 路径，保留解析/参考 JVP，逐条验证后再扩大覆盖。[R10]

cuDNN 支持按启发式构建执行计划和运行时 autotune，也允许按 workspace 和数值属性筛选计划。候选应先在原 PyTorch 路径内试验；只有确认缺少融合或 plan 控制能力时才引入 cuDNN frontend，避免新增封装本身成为瓶颈。[R8]

## 8. 测量与正确性：本方向的最低门槛

### 8.1 分开报告三种成本

|成本|如何处理|
|冷启动|进程启动、首次导入/JIT、autotune、首次 graph capture；独立记录|
|稳态|代表性工作集完成编译/预热之后测量；不在每次迭代清 cache|
|切换与尾部|新相机数、任务/shape 切换、检查点/评估、图和缓存增长；单独覆盖|

编译和调优缓存目录按软件版本/实验身份隔离，同时明确是冷缓存还是复用缓存。比较同等预热条件；不要把 baseline 的首次编译与 candidate 的热缓存比较。预热充分性由“无新增编译/捕获、延迟稳定、内存不再增长”判断，不靠固定 10 步迷信。

### 8.2 计时边界

- CUDA events 可测一段 GPU 工作，但多 stream 时需保证所有被测依赖都汇合；单 stream event 不能自动表示完整训练完成。
- 包装调用计时覆盖输入准备、cast/pack、转换、分配、kernel、输出恢复；单独提供核心 kernel 时间仅用于解释。
- 完整 update 使用设备工作完成的 wall time，并按参与 rank 的完成情况统计；性能对照不用 NCU 采集过程。
- 多次独立窗口做 A/B 与换序比较；阈值同时考虑绝对毫秒、噪声、长期收益和维护成本。GPU 独占租约由负责人分配。

### 8.3 数值阶梯

1. 小规模 FP64/FP32 参考与 BF16 生产基线，确认数学与边界语义。
2. 真实分布和极值输入下的 forward；误差指标包括绝对误差、相对误差、NRMSE 及异常值，不只 cosine。
3. 训练路径的参数/输入梯度、grad accumulation 与一次 optimizer 更新；需要时用小规模 gradcheck/方向导数参考。
4. JVP 原值与 tangent 分别核对；解析 JVP、自动微分与有限差分只在适用精度/尺度上互相校验。
5. 多步固定样本 replay，再按精度/算法风险做短训与质量对照。loss 有限不等于梯度正确，更不等于收敛等价。

## 9. 可直接改成仓库脚本的命令模板

以下是接口模板，不是声称当前仓库已有这些文件。先让执行 agent 把 `train_entry.py`、`component_repro.py` 与参数映射到真实入口；不改变既有训练配置作为代价。工具选项以部署版本的 `--help` 为准。

**A. 版本与设备快照**

```bash
python -m torch.utils.collect_env > run/torch-environment.txt
nvidia-smi -q > run/nvidia-smi.txt
nsys --version > run/nsys-version.txt
ncu --version > run/ncu-version.txt
git rev-parse HEAD > run/commit.txt
```

`run/` 应由调度器创建为唯一目录；另存有效配置、依赖锁、环境镜像与GPU租约。

**B. 编译诊断短跑**

```bash
TORCH_TRACE=run/torch-trace \
TORCH_LOGS=graph_breaks,recompiles,dynamic,perf_hints \
python train_entry.py <真实训练参数>

tlparse run/torch-trace
```

`<真实训练参数>` 是说明占位符，执行前替换；不把尖括号原样传给 shell。先用短跑定位，再关闭重日志做正式性能测量。trace 可能包含源代码，仅保存在被授权的工程环境。

**C. 稳态时间线**

```bash
nsys profile --trace=cuda,nvtx,osrt --sample=none \
  --capture-range=cudaProfilerApi --capture-range-end=stop \
  -o run/steady python train_entry.py <真实训练参数>
```

训练入口在预热完成后调用 `torch.cuda.cudart().cudaProfilerStart()`，完成指定窗口后调用 `cudaProfilerStop()`；边界处需确认待测 GPU 工作完成。分布式任务交给现有 launcher 集成采集，不为方便采集改成另一种训练拓扑。Nsys 可看到图重放；需要图节点细节时使用部署版本支持的 graph tracing 选项并评估额外开销。

**D. 只采一个真实热点**

```bash
ncu --list-sections

ncu --kernel-name-base demangled \
  --kernel-name 'regex:已从时间线确认的内核名称' \
  --launch-skip 10 --launch-count 1 \
  --section SpeedOfLight --section LaunchStats \
  --section Occupancy --section SchedulerStats \
  --section WarpStateStats --section MemoryWorkloadAnalysis \
  -o run/hotspot python component_repro.py
```

`launch-skip` 计数针对匹配的 kernel；10 是示例，必须按真实调用定位。实际 section 列表先核对。选择真实 stage/rank 的复现，不把平均随机 GEMM 当训练热点。NCU 的 `elapsed`/`active` 分母、memory throughput 子系统和 tensor activity 需要按指标定义解释；不将它们称为 MFU。[R7]

**E. 自定义内核检查**

```bash
compute-sanitizer --tool memcheck python component_repro.py
compute-sanitizer --tool racecheck python component_repro.py
TRITON_DEBUG=1 python component_repro.py
```

以上用于小范围诊断；正式测速移除 sanitizer 和调试开关。

## 10. 应明确写入失败库的负例与停止条件

|负例/停止条件|结论与后续|
|只赢 eager，输当前 compiled B0|停止推广；除非能改善未编译路径且确有暴露时间|
|核心 kernel 更快，包装调用或完整 update 不快|记录局部收益，定位转换/分配/同步/竞争；不能宣称训练提速|
|图重放减少 CPU 时间，但图池导致更小 batch 或内存风险|缩小捕获范围；比较最终可行配方|
|跨 stream 有显著重叠，但两侧都慢|以完整完成时间判定；WAM 历史案例重叠约97.5ms却合计变慢约111.4ms，说明竞争可超过重叠收益|
|编译暴露量化后主机更快，却多出GPU中间写回|停止该融合方式；研究真正减少写回的边界，不以CPU下降作为验收|
|性能只在一种干净连续张量上成立|补真实 offset/stride；域外保留明确 fallback|
|通过 forward 却缺训练所需 backward/JVP|不进入训练基线；可单独评估无导数分支|
|提高重编译限制后缓存仍持续增长|回到 guard/shape 调查；停止无界扩大限制|
|长程出现旧 graph 输出被覆盖、重复 RNG 或缓存版本过期|立即撤回；修复生命周期/版本契约后重新验证|
|成熟库大 GEMM 已接近所测 shape 的性能，而预计完整收益低于噪声|把算力转给其他热点；新 shape、软件版本或硬件变化后再开任务|
|改变模型宽深、token 截断、噪声重复数、精度或GAS才获得收益|改记结构/算法/训练配方实验，不能混入同任务保真加速|

两轮没有新证据或新机制、可回收时间低于当前更优候选、或者验证成本超过剩余收益时，提交停止结论。没有硬性要求所有方向常驻，也没有要求所有算子自研。

## 11. KDA 与 NVIDIA skills：怎么借用，不能怎么借用

**NVlabs/kda** 已核实为 Kernel Design Agents，公开仓库提供任务契约、规划、实现、逐步验证与候选记录流程，并注明早期研究原型。它的通用流程不绑定单一硬件，但公开 community wishlist 当前只接受 B200/B300。H200 可以迁移工作方法，不应照搬其硬件参数或将 wishlist 结果当H200证据。它 README 中的 quickstart 克隆目标目前指向 `mit-han-lab/kernel-design-agents`；因此接入前应核对仓库身份、版本与子模块，不能把两个路径静默视为同一个交付物。[R11]

**NVIDIA/skills** 是官方目录，技能从产品仓库同步，明确支持 Codex。当前目录含 `nemo-mbridge-perf-cuda-graphs`、`nemo-mbridge-perf-activation-recompute`、`nemo-mbridge-perf-memory-tuning`、`nemo-mbridge-perf-parallelism-strategies`、`nemo-mbridge-perf-tp-dp-comm-overlap` 等。它们服务 Megatron Bridge；WAM/DeepSpeed 任务借鉴判断与验证流程，开关必须映射到实际框架。安装前读具体技能与关联版本，不一次装入整个目录。[R12]

```bash
# 发现当前目录；本次调研未执行安装。
npx skills@latest add nvidia/skills --list

# 确认内容与版本后，按需安装一个方向。
npx skills@latest add nvidia/skills \
  --skill nemo-mbridge-perf-cuda-graphs --agent codex
```

这些 skill 不提供自动正确性保证。接入本工作流时补上三项本地契约：**比较当前 compile 基线；覆盖 backward/JVP；完整包装与整训验收。**

## 12. 经核验的主要公开资料

以下 12 项均已打开官方页面或作者仓库；页面内容不等于当前项目已具备对应版本。命令模板另核对了 Nsight Systems 官方 User Guide。

|编号|资料|用于哪个决定|
|---|---|---|
|R1|[PyTorch torch.compile Troubleshooting](https://docs.pytorch.org/docs/2.14/user_guide/torch_compiler/torch.compiler_troubleshooting.html)|TORCH_TRACE/tlparse、graph breaks、guards、重编译与缓存限制|
|R2|[PyTorch torch.compile API](https://docs.pytorch.org/docs/2.14/generated/torch.compile.html)|模式、fullgraph 与 CUDA Graph 的区别|
|R3|[PyTorch CUDAGraph Trees](https://docs.pytorch.org/docs/2.14/user_guide/torch_compiler/torch.compiler_cudagraph_trees.html)|图池、动态形状录制、旧输出生命周期、跳过原因|
|R4|[PyTorch Dynamic Shapes](https://docs.pytorch.org/docs/2.14/user_guide/torch_compiler/torch.compiler_dynamic_shapes.html)|自动 dynamic、输入维度标记与局部动态范围|
|R5|[NVIDIA Hopper Tuning Guide](https://docs.nvidia.com/cuda/hopper-tuning-guide/index.html)|Hopper 适用硬件机制；实际H200容量/带宽另以设备资料为准|
|R6|[NVIDIA CUTLASS Efficient GEMM](https://docs.nvidia.com/cutlass/latest/media/docs/cpp/efficient_gemm.html)|tile、split-K、warp specialization、persistent 与架构差异|
|R7|[NVIDIA Nsight Compute CLI](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html)|匹配真实kernel、launch过滤与section采集|
|R8|[NVIDIA cuDNN Frontend Overview](https://docs.nvidia.com/cudnn/latest/developer/overview/)|execution plans、autotune、workspace和数值属性筛选|
|R9|[Triton Debugging](https://triton-lang.org/main/programming-guide/chapter-3/debugging.html)|debug/interpreter与内存竞争检测|
|R10|[FlashAttention 作者仓库](https://github.com/Dao-AILab/flash-attention)|FA3/FA4、Hopper、前反向与版本支持边界|
|R11|[NVlabs Kernel Design Agents](https://github.com/NVlabs/kda)|任务契约、候选记录；研究原型与wishlist硬件限制|
|R12|[NVIDIA Agent Skills](https://github.com/NVIDIA/skills)|官方技能目录、当前名称与Codex安装入口|

具体技能文件与 KDA agent-flow 深层页面在本次读取中返回访问错误；其内容未被当作已完整阅读，本文对它们的说明以已打开 README 为限。
