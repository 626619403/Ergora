# 执行图与数据调度：Agent、搜索流程、工具与 Skill

检索日期：2026-11-12。R6 覆盖 CUDA Graphs、sequence packing、attention／fusion、microbatch 构造与调度、编译和数据流优化。用户给定的 [Megatron Bridge Agent Skills Reference][bridge-index]用于拆分职责，不要求导入 NeMo。以下仅依据官方源码、文档与作者论文；未安装依赖、调用模型、运行 GPU／多 rank 训练或复现性能。原件、获取状态与摘要留在私有 `.ergora/checks/specialist-template-refresh/research/execution-graph/`。

**建议采用执行图分析专家和独立评价合同，先适配有界的 capture／packing／attention A/B 子流程，再按真实瓶颈选择原生搜索系统。** 本轮可核的专用 LLM agent 是 **KernelAgent 的 Fuser 子图融合流程**；其公开前向验证不能直接成为训练图验收。DynaPipe、ZeroBubble、Mirage、TVM 等有自动优化，却不是 LLM agent。`torch.compile`、CUDA Graphs、FlashAttention、nvFuser 也不能改名为专用 agent。

## 职责拆分与候选身份

以下是可独立选择、评价的技术职责，不是互斥的 agent 类型；同一专家可以跨域，同一方向也可以替换工具。R1 已核的 KDA／ForgeKernel／AKG／GEAK 可接受其中的 kernel 任务，复用[既有研究](2026-11-12-optimization-kernel-agents.md)即可，跨域协作另由 X1–X3 汇总。

|职责|实际决策与可交付结果|最接近的可用实现|建议|
|---|---|---|---|
|R6a capture 与 host launch|是否 launch-bound、capture 区域／shape bucket、生命周期与摊销|PyTorch CUDA Graphs／CUDAGraph Trees；Bridge CUDA Skill 与实际 wrapper|**采用知识合同，适配有界 A/B**；不默认扩大 capture 范围。|
|R6b packing 与 batch 语义|offline／collate／worker buffer／跨 DP packing，边界、loss 权重和样本顺序|Bridge 四条 packing 路径；框架既有 collator＋varlen attention|**优先适配**现有框架消费者；四种模式分别准入。|
|R6c attention 与融合|backend、mask、layout、head shape、forward／backward 融合边界|SDPA／FlexAttention、FlashAttention、cuDNN Frontend、nvFuser；Fuser agent|**先采用库基线**；库覆盖不足再给 R1／Fuser 子图任务。|
|R6d microbatch 与 PP 调度|按长度构造微批、重排、拆分 B/W、内存约束与通信依赖|DynaPipe；ZeroBubble 自动搜索／runtime；PyTorch pipelining schedules|**条件适配原生流程**；收益必须覆盖训练 step 和调度成本。|
|R6e 编译与数据流|graph break／重编译、代数改写、tensor schedule、布局／存储规划|Inductor、TVM MetaSchedule、Mirage；Unity／TASO|**优先采用现有编译器诊断和有界搜索**；框架替换暂缓。|

下表短 SHA 对应本轮实际读取的固定源码，不能以可变 `main`／`latest` 当复现身份。许可列为根许可，CUDA／cuDNN、Triton／CuTe、Redis 和其他依赖仍需分别核定。

|候选、固定版本与许可|真实接口与优化流程|资源／语义边界与选型|
|---|---|---|
|**LLM agent：KernelAgent／Fuser** `e064717`，Apache-2.0 [源码][fuser] [许可][fuser-license]|`python -m Fuser.auto_agent` 路由轻重路径；`python -m Fuser.pipeline --verify` 执行改写→提取 `subgraphs.json`→并行 `TritonKernelAgent`→重组→运行自测；保存 `.fuse/<run_id>/` 产物。[pipeline][fuser-pipeline] [composer][fuser-composer]|需要外部 LLM 后端、Triton 与目标 GPU，生成和计时均消耗预算。重组器要求对 PyTorch 前向结果 `allclose`、`PASS`＋exit0，测试也由 agent 生成；未核到自动训练 autograd／JVP 验收。**适配为子图候选生成流程**，外部冻结 reference 和梯度门禁。它与下行 NVIDIA nvFuser 是不同项目。|
|**工具：PyTorch 2.15.0** `31a77fc`，BSD 风格根许可 [compile 源码][torch-compile] [许可][torch-license]|`torch.compile(..., backend="inductor", fullgraph=..., dynamic=..., mode=...)`；`max-autotune` 会选择实现并默认启用 GPU CUDA graphs，`max-autotune-no-cudagraphs` 可分离两种干预；`torch.cuda.CUDAGraph`／`make_graphed_callables` 提供 capture。[CUDA 文档][torch-cuda] [Trees 固定源码][torch-trees]|`fullgraph=True` 要求单个编译图，不代表一次 CUDA capture；`dynamic=True` 也不代表一次 CUDA graph 接受任意形状。需记录 graph break、guards、重编译、fallback、实际 replay 和内存。**采用为首选工具基线**，不宣称专用 agent 或必然提速。|
|**工具：PyTorch SDPA／FlexAttention**，同上版本 [SDPA][torch-sdpa] [Flex 源码][torch-flex]|`F.scaled_dot_product_attention`＋`torch.nn.attention.sdpa_kernel` 控制实现；`flex_attention(..., score_mod=..., block_mask=...)`＋`torch.compile` 支持自定义 attention 模式。|SDPA 自动 backend 选择不是全模型搜索；mask 的 `True` 表示参与 attention，和 `MultiheadAttention` 相反；eval 时仍须显式把 `dropout_p` 置零。FlexAttention 在该版本仍为 prototype；CPU／MPS 路径不支持 backward。**采用 SDPA 基线，按 mask 需求适配 Flex**，不能跨设备推断训练支持。|
|**库：FlashAttention** `f63c472`，BSD-3-Clause [源码][flash] [许可][flash-license]|FA2 有 dense／`flash_attn_varlen_func` 及 autograd；FA3 Hopper 路径；FA4 使用 `flash_attn.cute.flash_attn_func`／`flash_attn_varlen_func`，固定实现有 backward。[FA4 interface][flash-cute]|FA2 CUDA 路径要求 CUDA≥12、PyTorch≥2.2，支持 Ampere／Ada／Hopper；FA3 README 仍标 beta，H100/H800、CUDA≥12.3，FP8 仅 forward；FA4 面向 Hopper／Blackwell，不能把不同代际功能合并成统一保证。**按 dtype／head_dim／mask／dropout／架构适配**。`flash_attn_with_kvcache` 明示无 backward，不能用于训练替换。|
|**库／plan 调优：cuDNN Frontend** `a964f7a`，Apache-2.0 [源码][cudnn] [许可][cudnn-license]|C++ Graph／Python `cudnn.pygraph` 描述子图；有 SDPA 与多种 MoE／norm／activation 融合、前后向实现。当前提供 ranked `graph.plans`、`select_plan(i)`、`selected_engine` 等可观察选择接口。|基础 Python 要求≥3.10、CUDA／driver、cuDNN≥8.5；具体新 attention／FP8／MXFP8 engine 有更严版本和 Hopper／Blackwell 条件，不能用最低安装版本推断全部功能。Frontend 的计算图与 CUDA launch graph 不同。**适配为 attention／融合后端**，记录实际命中 engine、workspace、backend 版本与训练导数。|
|**融合编译器：NVIDIA nvFuser** `5198f11`，BSD-3-Clause [源码][nvfuser] [许可][nvfuser-license]|面向 NVIDIA GPU 的 fusion code generator，Python／C++ 与多设备可选构建；不是 KernelAgent 的 Fuser，也不是独立 LLM agent。|固定 README：CUDA≥12.6、PyTorch≥2.9、C++20、GCC≥13.1／Clang≥19、LLVM≥18.1；PyTorch CUDA 与 toolkit 必须匹配。wheel 有 torch／CUDA 绑定，nightly extra 会替换 PyTorch。**有明确消费者时适配**；不因名字或旧 TorchScript 集成假定当前框架已接入。|
|**自动搜索：DynaPipe** `d8666ad`，Apache-2.0 [源码][dynapipe] [许可][dynapipe-license]|profile 成本／内存→动态规划拆分 global batch→微批重排与内存感知 pipeline／通信调度→指令执行；CPU planner 与训练重叠。`DynaPipeDataLoader` 产出 `(microbatches, execution_plan)`；执行端注册 instruction handler 后调用 `execute`。[loader][dynapipe-loader]|需要 CPU planner、Redis KV、C++／定制 allocator 扩展和训练框架 executor；默认可创建很多预处理 worker，资源不能遗漏。官方明示 experimental、只验证其 Megatron fork；不是给当前 Bridge 换一个 DataLoader 就可用。**借鉴合同，按强长度偏斜工作负载条件适配完整流程**；保留 Redis／worker／端口的原生命周期。|
|**自动搜索＋runtime：ZeroBubble** `39f2c18`，BSD-3-Clause 根许可及附带第三方许可 [源码][zb] [许可][zb-license]|profile F／B／W／通信→按内存限制搜索调度→插入通信／可选 offload→runtime。真实 CLI 含 `--zero-bubble-v-schedule`、`--zero-bubble-max-pending-backward`；runtime 接受 `ScheduledNode(F,B,W,...)`。[runtime][zb-runtime]|该 fork 的 runtime 文档明确当前不支持 Transformer Engine，需 legacy local model；不能导入为 Bridge TE 兼容实现。optimizer post-validation 涉及先 step 后检验、必要时 rollback，必须验证所有优化器状态。**借鉴并条件适配原生搜索**；优先比较已有框架／PyTorch schedule，避免整 fork 替换。|
|**调度工具：PyTorch pipelining**，2.15.0 [固定源码][torch-pp]|`PipelineStage` 与 `Schedule1F1B(..., loss_fn=...)`／`.step(...)`，含 interleaved、ZBV、DualPipeV 等实现；可执行 schedule 与搜索器是两个层次。|不是自动挑选最优 schedule 的 agent。stage 边界、P2P、split backward、microbatch 数与 `scale_grads` 都属于实际接口合同。**采用为已有 PyTorch 消费者的候选执行工具**，不假定与 Bridge runtime 可互换。|
|**自动搜索：TVM MetaSchedule 0.22.0** `9dbf3f2`，Apache-2.0 [固定接口][tvm] [许可][tvm-license]|`tune_tir(mod, target, work_dir, max_trials_global, ...)` 默认 XGBoost cost model／evolutionary search，可替换 builder／runner／space；JSON database 保存 trial，`compile_tir` 从记录查询 schedule。|需要对应 target toolchain、CPU 构建资源和真实目标测量；TIR 搜索不能替代模型导入、autograd 或全训练图集成。**有界适配算子／子图搜索工具**，工作目录缓存绑定源码／target／shape，搜索失败与未测状态保留。|
|**superoptimizer：Mirage** `ffe38df`，Apache-2.0 [源码][mirage] [接口][mirage-kernel] [许可][mirage-license]|`KNGraph.superoptimize(...)` 搜索 μGraph 的代数／kernel／block 变换，再编译、profile 选候选；有缓存、symbolic checkpoint 与部分 search time-limit 参数。README 另推荐 MPK 分支的 persistent multi-GPU inference。|不是 LLM agent；部分后端如 NKI 明示未实现。论文的有限域概率等价检验限指定程序类；API 的验证模式、缓存命中与实际浮点误差必须分别核查。MPK 解码接口不是训练图接口。**适配小子图搜索／借鉴 verifier，暂缓整训练图接入**。|
|**图改写研究：Unity／FlexFlow Train** `1c534e4`，Apache-2.0；**TASO** `f11782c`，Apache-2.0 [Unity 论文][unity-paper] [FlexFlow][flexflow] [许可][flexflow-license] [TASO][taso] [许可][taso-license]|Unity 将代数变换与并行化联合搜索；TASO 自动生成／验证 graph substitutions，`load_onnx→optimize→export_onnx` 是真实接口。|FlexFlow 已拆 Train／Serve；固定 Train README 的旧 Python／search 示例处于注释块，不能当当前稳定 API。TASO README 的主要性能证据是 V100 上预训练图的 inference，ONNX 往返不保证训练状态／梯度。**借鉴搜索空间与改写证明，暂缓框架迁移**。|

未核到上述项目自带的通用 MCP 合同。若以后包装 CLI／Python API，应逐项声明支持操作、安装版本、目标设备、运行／只读能力，不能用一个 MCP 名称抹平这些差异。

## Bridge Skill 的可用部分与固定版本漂移

本轮读取 Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0`。根与两项 Skill 均为 Apache-2.0。[CUDA Skill][bridge-cuda-skill]适合复用“先证明 host gap→最窄 scope→capture 后稳态 A/B→最后组合重测”；[packing Skill][bridge-pack-skill]适合复用输入、对齐、mask、质量与资源约束。它们是指导 coding agent 使用框架的资料，不是已交付独立调度器。**以下差异说明不能直接复制 Skill 的 import／开关。**

|固定快照中的差异|可核源码与接入结论|
|---|---|
|CUDA Skill／文档表只列 `local + full_iteration` 和 TE scopes；实际工具已兼容新 MCore API。|[utils/cuda_graph.py][bridge-cuda-utils]在当前 API 可用时设置 `cuda_graph_impl="full_iteration"` 与 `cuda_graph_modules`，兼容旧 `cuda_graph_scope`；还接受带显式 modules 的 local per-layer capture。适配器必须探测实际 MCore 字段／枚举，不硬编码旧三值表。|
|“full iteration”不能直接解释为连 optimizer 都 capture。|[train.py][bridge-train]分别用 `FullCudaGraphWrapper` 包 forward/backward，用 `config.optimizer.optimizer_cuda_graph`＋可用性标记包 `optimizer.step`。必须分别记录实际生效范围；支持标记缺失时不能称 optimizer graph 已启用。|
|packing Skill 的 `...data.datasets.packed_sequence` import、旧 `sequence_batching.py` anchor 已过时。|实际 `PackedSequenceSpecs` 在 [data/packing/config.py][bridge-pack-config]，THD builder 在 [in_batch.py][bridge-pack-batch]，offline、Parquet、算法各有模块。使用真实 API／原框架 preprocessing，不承诺抽一份文件即可独立脱离 Bridge。|
|packing Skill 写 Energon native packing 拒绝 MTP；固定[packing 文档][bridge-pack-doc]已写 boundary-aware MTP。|[config.py][bridge-config]中的 runtime THD 门禁不再 blanket 拒绝 MTP；[Qwen3-VL text_model.py][bridge-qwen-mtp]会用 physical padded offsets 构造 MTP rolling 的 metadata。应按模型路径核 MTP 标签／mask，不能概括所有 VLM 均已运行验证。|
|packing Skill 未覆盖新增 global-batch packing。|[config.py][bridge-config]与[training/global_batch_packing.py][bridge-global]有真实接线，默认 `dp_balanced`，动态 CP 另有 scheduler／group 条件。它跨 DP 汇集长度、每 step 构造 pack，改变实际微批数；当前门禁仍拒绝 CUDA graphs／PP／VPP／Megatron FSDP／Mamba hybrid。不能因底层 pipeline 接收变长参数就称这些组合已支持。|
|CUDA 文档对 packed TE capture 仍有 blanket 警告，packing 文档／校验已有静态 metadata 路径。|[config.py][bridge-config]要求 offline graph 固定 token width；capture 包含 packed attention 时再要求 `pad_cu_seqlens=True`。这证明有准入分支，不能证明任意 TE／MCore 版本已成功执行；原[CUDA 文档][bridge-cuda-doc]的失败与旧容器记录保留。将该组合列独立 GPU 验收目标。|

四条 packing 路径须单列：offline 在数据集层预处理；in-batch 在一个 rank 的逻辑 microbatch 内拼接；Energon 只看单 worker 的候选 buffer；global-batch 才跨 DP 平衡。当前 Energon／global-batch runtime THD 校验要求 MBS1、per-token loss、`average_in_collective=False`、禁 CUDA graphs 和 PP；普通 in-batch 不应继承这整套禁用表。offline MBS1 与 in-batch 逻辑 MBS>1、物理 THD 单 row 也不能混为一谈。[packing 文档][bridge-pack-doc] [实际校验][bridge-config]

固定 alignment 应由 TP／CP／SP 与 eval topology 推导；offline 的内部 constituent-sequence 对齐与最终 pack width 是不同约束。固定 width 不能使 `cu_seqlens` 的数量自动固定，也不能用 padding 值冒充真实 sample 边界。native VLM buffer 计数的是**每 worker 的候选样本**，高分辨率图片／视频会占 host RAM；记录 worker RSS、首批延迟和数据恢复配置。该文档还明确 `progress.txt Tokens`／`time/tokens` 可统计配置容量，不能直接作为有效源 token 吞吐。[packing 文档][bridge-pack-doc]

## capture、attention 和训练语义的硬边界

**计算图改写、编译图、CUDA launch graph 是不同层。** 代数融合可以改变 kernel 与浮点规约次序；CUDA capture 主要复用 GPU 工作提交。即使二者一起启用，也应保留单独干预的 A/B。PyTorch `fullgraph` 不是 CUDA graph 开关，成功 compile／capture 不是实际 replay 或收益证据。[compile][torch-compile] [CUDA][torch-cuda]

单次普通 capture 要求 tensor size／layout 和地址满足 replay 合同；地址内容可以更新，不能以“新 batch 张量”悄悄替换静态输入后仍读旧数据。CPU side effects 不会随 replay 重跑，`.item()` 等 host sync 不可混入，跨 stream event 依赖必须在 capture 内正确汇合；对象、workspace、outputs 和 graph pool 的存活期须覆盖最后一次 replay。[PyTorch CUDA][torch-cuda] [CUDA 原生指南][cuda-guide] cuDNN 还规定其 execution plans／kernel code 与 CUDA graph 的 retention 关系；重建／反序列化后只保留旧 graph 对象并不充分。[cuDNN][cudnn]

“CUDA graph 完全不支持动态控制流”在当前版本也不准确：CUDA 原生已有 graph update／conditional nodes；PyTorch 2.15 文档支持特定 `torch.cond` 路径和 `backend="cudagraphs"`，但明确 **Inductor backend 的这条支持尚未提供**，示例为 inference。不能据此推断 Bridge 的任意数据相关 Python 分支、随机路由或训练 backward 可捕获。CUDAGraph Trees 可以对不同路径／每个新 shape 重新记录；频繁变长会增加 capture、内存和缓存成本，`dynamic=True` 的编译图也不会消除这一成本。[CUDA 原生][cuda-guide] [PyTorch CUDA][torch-cuda] [Trees][torch-trees]

随机数并非一律禁止；需使用对应版本的 graph-safe generator／tracker，核 dropout／采样状态在 replay 后前进、跨 rank 独立性及 checkpoint 恢复，而非固定重播同一随机 mask。`make_graphed_callables` 可以分别捕获 forward／backward，但不自动保证自定义算子的导数、优化器、AMP scaler、异常检查、hooks 与 recompute 均兼容。Bridge 中 TE RNG tracker、full-iteration NaN 检查限制、offload／recompute／MoE scope 的组合应按真实 MCore／TE 版本检查；把检查移出 capture 后仍需独立 finite-loss／gradient 门禁。[PyTorch CUDA][torch-cuda] [Bridge Skill][bridge-cuda-skill] [实际 wrapper][bridge-train]

packing 必须保存样本独立的 causal／prefix／document 边界、position IDs／RoPE、labels 与 loss mask；EOS 本身不是 attention 隔离证明。核 `cu_seqlens_q/kv`、padded physical offsets、max lengths 与真正传入 kernel 的 mask，防止跨样本 attention、MTP roll 越界、padding 进入 MoE auxiliary statistics。改变 truncation、pack membership、shuffle、drop-last 或 loss normalization 是训练变化，不能用“等 token slots”宣布质量不变。不同有效 token 数微批的 mean-of-means 可能改变梯度权重；应显式定义全局 loss 分子／分母，核 DP reduction 和 scheduler 的 `scale_grads`。[THD builder][bridge-pack-batch] [packing 文档][bridge-pack-doc] [PyTorch schedules][torch-pp]

attention 替换还需核 causal 的对齐方式（尤其 Q/KV 长度不等）、GQA／MQA、head_dim、stride、bias、滑窗、softcap、dropout 和 deterministic backward。FA3 FP8 forward、decode KV-cache、FA4 backward 是不同支持面；稀疏／近似 attention 若改变可见 token 则进入模型质量／架构评价，不能仅以 FP 容差视作数学等价优化。[SDPA][torch-sdpa] [FlashAttention][flash] [FA4][flash-cute]

## 作者实测与论文边界

- **CUDA capture 成功不等于加速。** Bridge Skill 自载 Qwen3-30B-A3B／H100／BF16／all-to-all 的一次样本：TE scopes 成功 capture，但 replay 5–8 平均 42.00 秒，对 eager 41.36 秒。原件／配置未由本项目复跑；这是上游记载的负例，不能替代新的目标栈 A/B。[Skill][bridge-cuda-skill]
- **DynaPipe 是完整训练优化系统。** [论文 v1][dynapipe-paper]在最多 4×p4d、32×A100 40GB、NVSwitch／400Gbps EFA、FLANv2 上报告 T5 最高4.39×、GPT最高3.25×；基线为 packing 的 Megatron＋DeepSpeed，且双方均搜索并行／checkpoint 等配置。不能把总收益全部归到微批重排，亦不能等同现代 varlen attention 基线。论文明确部分 GPT 时间预测误差来自未建模 DP all-reduce；CPU 规划是否被完全遮蔽取决于资源和 workload。
- **ZeroBubble 的“零”有条件。** [论文 v1][zb-paper]在最多32×A100 80GB、4节点 RoCE 上比较，报告同类内存约束最高23%、放宽内存31%；部分 bubble rate 表是 profile 参数驱动的理论计算，真实 trace 仍有额外 bubble。ZBV 的零 bubble 条件含 F/B/W 时长平衡；loss bitwise 检查是作者指定 seed／实现下的证据，未训练至 convergence，不能外推所有优化器／dropout／框架版本。
- **Mirage 的等价性证明有模型边界。** [OSDI25 论文][mirage-paper]在 A100／H100 上核 tensor-program 性能；有限域概率检验针对 Lax 程序，不证明 IEEE 浮点规约误差、任意非线性／控制流、随机状态或反向实现。其整模 latency 与 MPK inference 不构成训练 step 收益。
- **TASO／Unity 说明搜索空间，不提供当前 LLM 通用成绩。** TASO 的 V100 inference、Unity 的旧 DNN 训练／联合并行化实验及当前 FlexFlow API 状态须分别看待。KernelAgent 的 KernelBench 正确性或单核收益同样不能代替训练图的优化器状态和质量评价。[TASO][taso] [Unity][unity-paper] [KernelAgent][fuser]

以上均为作者报告，未在 Ergora 复现；不同硬件、baseline、数值目标和统计口径不横向排名。

## 最小方向子模板与独立评价

**单体专家**可先复用现有 performance analyst／kernel designer 的只读提案职责，增加本报告的执行图约束；其输出是带瓶颈证据的干预候选。**方向子模板**管理前置检查、原生工具或搜索流程、候选产物和外部门禁，不替代原 Temporal／runner、candidate、审批与 unknown 恢复所有者。

|子模板输入|必须输出|
|---|---|
|固定 workload／训练目标、源码和依赖身份；模型结构、dtype、shape／stride 分布、batch／optimizer／AMP、TP/DP/PP/EP/CP；实际 GPU／内存／host RAM／CPU／互连预算|可用工具／操作／版本矩阵；拒绝原因；实际命中的 backend／engine／graph scope、搜索空间和固定候选配置|
|可信 eager／compiled／library baseline；独立冻结 reference、所需 backward／JVP、随机性与质量容差|逐 attempt 的源码／IR／kernel／配置摘要、原命令／完整 stdout/stderr、capture／compile／search 记录、失败／超时和清理状态|
|数据 fingerprint、tokenizer／processor、样本 ID／长度／权重、pack／mask 规则、loss 分子分母、resume state|packing membership／边界／loss mask 摘要，真实源 token／loss-bearing token／padding 统计，样本漏／重／截断检查|
|可支配设备时长、CPU／RAM／磁盘、LLM token／费用、搜索试次与终止条件|稳定性能样本与离群规则、所有 rank 的结果、setup／稳态／总成本、正确性／质量／性能独立 verdict、可回退候选和 handoff|

最小执行顺序：

1. **建立基线与可行性。** 用同一框架、数据、precision、parallelism 和资源验证 eager／已有 compiled baseline，辨别 host gap、padding、attention、pipeline bubble 或 graph break。只选择对应分支；没有匹配 GPU／rank 数就输出未验证，不能用 CPU timing 替代。
2. **有界生成候选。** capture 从局部 scope／有限 buckets 开始；packing 从一种模式与一组 length／对齐参数开始；attention 先比较已有库。需要代码生成时调用固定 Fuser 原流程；需要动态调度时调用 DynaPipe／ZeroBubble 原接口并保留其内部 planner／runtime；TIR／μGraph 搜索按实际 target 和预算运行。禁止多个候选同时改同一训练配置而失去归因。
3. **外部门禁先于晋升。** 生成器不能改 reference、容差、质量样本、计时区间或自己批准结果。先验完整训练运算与内存安全，再测吞吐；组合候选重做相关门禁，库单项通过不可传递成任意组合通过。
4. **带状态交接与恢复。** 保存 native run ID、缓存／database／plan／data state、完整产物和失败；缓存不是执行证据。超时先核原进程／所有 rank／planner，再由原 owner 恢复或终止，不能盲目重提一组训练。checkpoint 恢复须连同随机数、optimizer、sampler／worker buffer、pack groups 和版本；旧 plan 不适用于新 topology／shape／precision。

独立评价至少拆成以下三个出口：

|评价责任|独立门禁与失败样本|
|---|---|
|正确性／训练语义|前向、输入／参数梯度、多个 optimizer step 后的参数与状态；需要的 JVP／高阶导数单列；随机数状态前进／恢复、AMP overflow、gradient clipping、recompute／hooks。packed／varlen 覆盖空或极短样本、边界、不同 Q/KV 长度、padding、不同有效 token 数；PP 覆盖 B/W 顺序、参数版本、P2P 匹配、慢 rank／失败全组退出。|
|数据与模型质量|样本 ID 无意外漏重、同等训练／token budget、真实 loss-bearing token 归一化；对齐 unpacked reference loss／grad 后再做有限训练稳定性和 convergence sentinel／目标验证指标。改变 truncation／顺序／稀疏 mask 时不能仅跑单步数值比较。|
|测量可信度|GPU 同步的完整 optimizer-step／端到端 wall time，多 rank 取真正关键路径；CUDA events 只解释具有正确依赖的 GPU 区间，不能用 host enqueue time 或各 stream kernel 时长之和代替 step。warmup／JIT／autotune／capture 与 replay 稳态分开，配对重复 A/B，最终吞吐不在 profiler 下测。报告 useful source／loss token/s、tail、显存与host RSS、dataloader／planner stall、compile／capture／search 成本和失败率。|

此外用 break-even 步数 `额外 setup 成本 / (baseline_step - candidate_step)` 说明摊销；分母不为正就没有该收益的 break-even。Graph pool、bucket 数、workspace／planner RAM 与编译并行度都受父任务预算约束。大 profile trace 交 R7 分析，原始正常训练计时仍是验收依据。[CUDA 计时与异步语义][torch-cuda]

## 跨域边界与采用顺序

- **R1 kernel／R2 precision：** 本方向负责图／wrapper 和实际调用命中；生成 kernel 或改变精度后，交 kernel／数值专家再核导数、误差、layout 和编译／capture 兼容。同一个 Fuser agent 可被多个子模板按固定版本引用。
- **R3 通信／R4 并行：** PP／微批／跨 DP packing 改变通信大小、顺序和 group 负载。kernel 更快会改变 F/B/W 平衡，graph replay 也会改变 launch／overlap；通信 SM 竞争与全 rank 前进性必须重新评价。动态 CP 的 group 选择由 R4 负责，R6 提供长度、pack 和调度合同。
- **R5 显存：** graph pools／buckets、激活生命周期、W 延后、recompute／offload 与 workspace 的峰值联合计算。自动搜索的估计峰值不能替代最终栈实测，Bridge 某组合拒绝也不能外推所有框架永久不支持。
- **R7–R9：** R7 提供可信 trace／关键路径；R8 提供资源、全组超时／清理与 checkpoint 恢复；R9 核模型族、VLM／MTP、mask 与训练质量。R6 不自行换框架、模型目标、调度所有者或追加硬件权限。

采用顺序为：**采用独立合同与现有库基线 → 适配只读执行图分析 → 为选中的现有框架补最小 capture／packing／attention A/B 消费者 → 按瓶颈接 Fuser 或有界编译搜索 → 有强变长／PP 需求才接动态调度完整流程。** DynaPipe／ZeroBubble 先借鉴再条件适配；Unity／TASO 和 MPK 整训练图迁移暂缓。Bridge Skill 以保留归属的知识和检查规则适配，不整套导入，不以静态图或文档新增宣称流程已经运行。当前 Ergora training preset 仍是只读 proposal-leaves，此研究没有改变该能力边界。

检索限制：搜索连接器返回不可调用；Google 返回缺结果的 JS 页面、DuckDuckGo 返回 challenge，Bing RSS 未给相关结果；GitHub commits API 返回403限流。官方 raw、版本文档、论文和 `git ls-remote` 可用，版本 Ref 和获取失败均保存。因而“未核到专用 agent／MCP”仅限本轮可读证据，不是穷尽性不存在声明。

[bridge-index]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills-index.html
[fuser]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/README.md
[fuser-license]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/LICENSE
[fuser-pipeline]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/Fuser/pipeline.py
[fuser-composer]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/Fuser/compose_end_to_end.py
[torch-compile]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/__init__.py
[torch-license]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/LICENSE
[torch-cuda]: https://docs.pytorch.org/docs/2.15/notes/cuda.html
[torch-trees]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/docs/source/user_guide/torch_compiler/torch.compiler_cudagraph_trees.md
[torch-sdpa]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/nn/functional.py
[torch-flex]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/nn/attention/flex_attention.py
[torch-pp]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/distributed/pipelining/schedules.py
[flash]: https://github.com/Dao-AILab/flash-attention/blob/f63c472c4dc19237c0635d6a629df065ff64796e/README.md
[flash-license]: https://github.com/Dao-AILab/flash-attention/blob/f63c472c4dc19237c0635d6a629df065ff64796e/LICENSE
[flash-cute]: https://github.com/Dao-AILab/flash-attention/blob/f63c472c4dc19237c0635d6a629df065ff64796e/flash_attn/cute/interface.py
[cudnn]: https://github.com/NVIDIA/cudnn-frontend/blob/a964f7a29b7adeb97063d6ee71c4576d80870b76/README.md
[cudnn-license]: https://github.com/NVIDIA/cudnn-frontend/blob/a964f7a29b7adeb97063d6ee71c4576d80870b76/LICENSE.txt
[nvfuser]: https://github.com/NVIDIA/Fuser/blob/5198f114e54ed87563533d8ff3a47bd4d872e739/README.md
[nvfuser-license]: https://github.com/NVIDIA/Fuser/blob/5198f114e54ed87563533d8ff3a47bd4d872e739/LICENSE
[dynapipe]: https://github.com/awslabs/optimizing-multitask-training-through-dynamic-pipelines/blob/d8666ad4e112d0241cb7fc025ce9bea72c32b924/README.md
[dynapipe-license]: https://github.com/awslabs/optimizing-multitask-training-through-dynamic-pipelines/blob/d8666ad4e112d0241cb7fc025ce9bea72c32b924/LICENSE
[dynapipe-loader]: https://github.com/awslabs/optimizing-multitask-training-through-dynamic-pipelines/blob/d8666ad4e112d0241cb7fc025ce9bea72c32b924/dynapipe/pipe/data_loader.py
[zb]: https://github.com/sail-sg/zero-bubble-pipeline-parallelism/blob/39f2c186a27580b7051eb51e0f651e1efd0a8170/README.md
[zb-license]: https://github.com/sail-sg/zero-bubble-pipeline-parallelism/blob/39f2c186a27580b7051eb51e0f651e1efd0a8170/LICENSE
[zb-runtime]: https://github.com/sail-sg/zero-bubble-pipeline-parallelism/blob/39f2c186a27580b7051eb51e0f651e1efd0a8170/docs/zero-bubble/pipeline_parallel_runtime.md
[tvm]: https://github.com/apache/tvm/blob/9dbf3f22ff6f44962472f9af310fda368ca85ef2/python/tvm/meta_schedule/tir_integration.py
[tvm-license]: https://github.com/apache/tvm/blob/9dbf3f22ff6f44962472f9af310fda368ca85ef2/LICENSE
[mirage]: https://github.com/mirage-project/mirage/blob/ffe38dff251017cdddeb1891cc808b43e7f51f25/README.md
[mirage-kernel]: https://github.com/mirage-project/mirage/blob/ffe38dff251017cdddeb1891cc808b43e7f51f25/python/mirage/kernel.py
[mirage-license]: https://github.com/mirage-project/mirage/blob/ffe38dff251017cdddeb1891cc808b43e7f51f25/LICENSE
[flexflow]: https://github.com/flexflow/flexflow-train/blob/1c534e463395d2aebee4554e2e5b5ca9e8fa8b7d/README.md
[flexflow-license]: https://github.com/flexflow/flexflow-train/blob/1c534e463395d2aebee4554e2e5b5ca9e8fa8b7d/LICENSE
[taso]: https://github.com/jiazhihao/TASO/blob/f11782c4db180ad7d1e7ff7f4bb82e574ac3b6b8/README.md
[taso-license]: https://github.com/jiazhihao/TASO/blob/f11782c4db180ad7d1e7ff7f4bb82e574ac3b6b8/LICENSE
[bridge-cuda-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-cuda-graphs/SKILL.md
[bridge-pack-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-sequence-packing/SKILL.md
[bridge-cuda-utils]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/utils/cuda_graph.py
[bridge-train]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/train.py
[bridge-pack-config]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/data/packing/config.py
[bridge-pack-batch]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/data/packing/in_batch.py
[bridge-pack-doc]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/docs/training/packed-sequences.md
[bridge-config]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/config.py
[bridge-qwen-mtp]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/models/qwen_vl/modelling_qwen3_vl/text_model.py
[bridge-global]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/global_batch_packing.py
[bridge-cuda-doc]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/docs/training/cuda-graphs.md
[cuda-guide]: https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/cuda-graphs.html
[dynapipe-paper]: https://arxiv.org/html/2311.10418v1
[zb-paper]: https://arxiv.org/html/2401.10241v1
[mirage-paper]: https://arxiv.org/html/2405.05751v3
[unity-paper]: https://www.usenix.org/conference/osdi22/presentation/unger
