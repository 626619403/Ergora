# R5：显存、重计算与卸载的 Agent／原生流程调研

检索与源码核对日期：2026-11-12。范围来自 [Megatron Bridge Agent Skills Reference][index]，承接[专家模板重整计划](../plans/2026-11-12-specialist-template-refresh.md)的 R5；技术与职责的关系见[纵横分类说明](2026-11-12-optimization-taxonomy.md)。本文只研究训练内存估算、激活重计算、激活／优化器／权重状态卸载及其自动选择流程。并行分片、执行图、诊断和恢复分别与 R4／R6／R7／R8 交接，不承担后续 X1–X3。

本轮没有安装依赖、运行模型／GPU／NPU、读取凭据或修改产品。来源为官方文档、固定源码和原论文／作者实现。GitHub 未认证 REST 元数据请求返回 403 限流，网页搜索连接器返回不可用；通过公开 GitHub HTML 的 `currentOid`／submodule 链接及固定 raw 源码完成核对。原响应、获取时间、SHA256 与失败回执留在本研究私有验收目录。`latest` 文档是当日观察，不等于固定版本；下文明确区分文档、源码可达能力和硬件实测。

## 结论与采用顺序

1. **先适配容量分析与受限候选流程。** Bridge 的三个 Skill 和 estimator 能直接帮助现有专家产生可核方案，但不是自主搜索 Agent。最小子模板应先产出“状态分解→合法候选→实际工具准入→配对测量→独立验收”的合同；没有可信实验消费者时保持只读提案。[Bridge Skill 索引][index]；[当前训练 preset](../../src/ergora/data/presets/presets.json)。
2. **自动化已有实物，职责不同。** PyTorch 有编译区域的预算驱动重计算；Gemini 有运行时自动 chunk 放置；MindSpeed SmartSwap 有完整采样／搜索／稳定执行闭环；Rockmate／OffMate 有预算、求解器和生成执行计划。它们是编译器、运行时或研究工作流，不能改名宣称为 LLM Agent。[PyTorch 预算接口][torch-graph]；[Gemini 放置策略][gemini-placement]；[SmartSwap][ms-smart]；[OffMate 实现][rock-front]。
3. **没有找到本轮可核、成熟且可直接导入的专用自主显存 Agent。** 在下述官方候选中，完整方向流程优先保留其原生控制循环，Ergora 只管理输入、资源上限、候选证据和验收；不重写内层调度，也不把通用训练库当成 Agent。
4. **卸载必须分成三种不同接口。** Bridge 层级激活卸载、Core 细粒度激活卸载与 HybridDeviceOptimizer 的优化器卸载具有不同的并行／重计算／图约束。官方 Skill 已有部分滞后，不能把“CPU offload 不支持 PP／CUDA Graph”当成所有卸载方式的统一规则。[固定 Core 配置][core-config]；[固定优化器配置][core-opt-config]。
5. **容量可行、数值正确、训练质量和端到端收益分别验收。** 未 OOM、短跑有限 loss、原生搜索器第一名，都不足以直接晋升。CPU 内存／NUMA／PCIe、每 rank 热点、optimizer 首次初始化、checkpoint／eval 瞬态和恢复后的下一步必须纳入。[Bridge memory Skill][memory-skill]；[recompute Skill][recompute-skill]。

## 从参考目录细化的职责

|参考条目|R5 实际决策|不能据此声称|
|---|---|---|
|`nemo-mbridge-perf-memory-tuning`|区分碎片、模型状态、激活和 workspace；预估最热 shard；选择下一组可测配置；LoRA＋SP 输入 re-gather|W&B／日志自动优化、一个 allocator 开关永远零成本、静态公式证明可运行|
|`nemo-mbridge-perf-activation-recompute`|按模型、attention backend、实测峰值选择模块边界；比较 selective／full／空 selective control|`core_attn` 是所有模型的最佳默认；重放 MoE 不增加通信|
|`nemo-mbridge-perf-cpu-offloading`|区分层级激活／可选权重与优化器卸载；测量 fraction、CPU 算力和传输代价|所有 CPU 卸载共享 PP=1 限制；更高卸载比例必然更高训练吞吐|
|Theoretical Memory Estimator|启动前容量筛选，输出组件与假设；运行后校准偏差|完整峰值／CPU RAM／offload 收益模拟器或自动搜索器|
|关联条目|FSDP／并行策略交 R4；CUDA Graph、packing 交 R6；snapshot／rank trace 交 R7；checkpoint／调度器交 R8；PEFT／模型适配交 R9|技术方向自动生成新的运行权限或一套互斥 Agent 类型|

前三项的官方 Skill 入口分别见 [memory][memory-skill]、[recompute][recompute-skill]、[offload][offload-skill]；estimator 见[独立文档][estimator-doc]。推荐将这些知识作为可被多个执行／诊断／审查职责引用的固定资源，而非把表格每行直接变成一个 Agent。

## 版本、许可和资源基线

下表是本轮实际读到的源码身份；不将主线自报版本号等同于已发布 wheel。完整 SHA 在固定链接中。

|候选|已核版本身份|许可核对|资源与采用判断|
|---|---|---|---|
|NVIDIA Megatron Bridge＋Core|Bridge `55694838`，`package_info.py` 为 **0.8.0**；gitlink 与 `.main.commit` 同指 Core `928ce7ce`|Bridge Apache-2.0；Core 根许可为 BSD 三条款并附第三方许可，逐文件保留 notice|NVIDIA GPU、匹配 PyTorch／TE／CUDA；当前 Bridge pyproject 要求 Python `>=3.12,<3.13`。**适配**三个 Skill 与实际配置，保留运行门禁。[版本][bridge-package]／[依赖][bridge-pyproject]／[gitlink][bridge-gitlink]／[许可][bridge-license]、[Core 许可][core-license]|
|PyTorch|stable 入口当日重定向到 **2.15**；`v2.15.0` 固定提交 `31a77fc9`|BSD 三条款及第三方 notice|checkpoint 为现有框架组件；预算接口自身仍标 prototype。**采用接口知识，条件适配预算求解**。[固定接口][torch-graph]／[checkpoint][torch-checkpoint]／[许可][torch-license]|
|DeepSpeed|`de6fcf18`，`version.txt` 为 **0.19.10**|Apache-2.0|ZeRO CPU／NVMe 有真实接口；Autotuner 与 DeepCompile 是不同原生流程。**适配已有 DeepSpeed workload；新编译卸载暂缓上线**。[版本][ds-version]／[许可][ds-license]|
|Colossal-AI Gemini|`297c8cf6`，`version.txt` 为 **0.5.0**|Apache-2.0及随附许可|`GeminiPlugin`＋chunk manager；CUDA 的 auto 放置不能外推到 NPU，源码明确 NPU 只允许 static。**条件适配**。[版本][gemini-version]／[插件][gemini-plugin]／[许可][gemini-license]|
|Ascend MindSpeed Core|`c047aaad` 的 master；README 推荐 MCore 0.12.1、CANN 9.0.0、PyTorch 2.7.1、TorchNPU 26.0.0；发行配套另有细表|根 LICENSE 为 BSD 三条款并附 Apache／MIT；docs 为 CC-BY-4.0。README 又有“仅供非商业目的”声明，口径须逐文件／用途澄清，不能只按厂商名认定可整包再分发|需要 Ascend＋CANN＋TorchNPU 自定义 allocator／hook；**借鉴原生流程，资源与许可明确后适配**。[配套][ms-readme]／[release notes][ms-versions]／[根许可][ms-license]／[文档许可][ms-doc-license]|
|Rockmate／HiRemate／OffMate|`c2f67845`；pyproject 为 **2.0.0**|MIT；ILP／CBC 等可选求解器依赖另核|PyTorch CUDA 单设备、样本输入、GPU／CPU 内存与求解时间。**借鉴联合优化，单 GPU 研究性适配**，不接跨节点生产流程。[配置与依赖][rock-pyproject]／[许可][rock-license]／[实现][rock-core]|

Core 的 fine-grained offload 文档文件头另有专有版权声明；根许可证不能自动覆盖带单独声明的文件。本报告引用事实与公开链接，不建议整份复制该文档；导入实现或 Skill 时核对应文件许可。[该文档][core-fine-doc]。

## Bridge：把估算、重计算与三类卸载分开

### 容量估算与状态分解

真实 API 为 `estimate_training_memory(cfg, num_microbatches=...)`，位于 `megatron.bridge.training.utils.theoretical_memory_utils`，返回结构化组件、参数数和 assumptions；`format_training_memory_estimate(..., unit="GB")`用于显示。它按最热 GPU shard 区分 dense／embedding、routed MoE expert 和 activation。对默认 Adam 状态模型，未分布式优化器时按 18 bytes／parameter，启用时按 `6 + 12 / shard_size`；dense 的 shard size 使用 DP×CP，expert 另用 expert-DP／ETP／EP 路径。这里的字节模型是该 estimator 的假设，不能套给低精度 moments、Muon、PEFT 冻结参数、其他 FSDP 实现或卸载之后的真实占用。[官方说明][estimator-doc]；[固定实现][estimator-src]。

该公式**不包含** allocator 碎片、CUDA／NCCL／dispatcher workspace、图池、routing imbalance、CPU offloading 和 full recompute。激活部分尤其依赖其 SP／selective-recompute 假设。建议输出“公式估算＋缺失项＋实测校准偏差”，容量不足可静态拒绝；低于卡容量只能进入试验，不能出具通过结论。[说明][estimator-doc]。

运行采样至少区分：低精度模型权重、FP32 master、梯度、Adam moments、激活、通信／算子临时区与图池；同时记录 GPU allocated／reserved、进程外设备占用、CPU RSS／pinned bytes、每节点总量与存储容量。`expandable_segments:True`是碎片候选，不是容量增加；官方 memory Skill 还列出 NCCL user-buffer／图注册的交互。LoRA 的 `sequence_parallel_input_regather=True`只对符合条件的非 expert column-parallel LoRA-A 生效，用 backward 再通信换保留激活，不能称为普通 checkpointing 或承诺通用收益。[memory Skill][memory-skill]。

### 重计算接口与数值边界

- Selective：`cfg.model.recompute_granularity="selective"`，显式 `recompute_modules=[...]`；空列表是有效 control。
- Full：`recompute_granularity="full"`，`recompute_method="uniform"`或`"block"`，指定`recompute_num_layers`；后者按 pipeline／virtual stage 解释。`distribute_saved_activations`与 SP 不能同时启用。
- 普通 attention、MLA、grouped MoE、dense FFN 的候选边界分别可包括 `core_attn`、`mla_up_proj`、`moe_act`、`mlp`。Fused／Flash Attention 已有内部 rematerialization，显式 `core_attn`可能增加时间而几乎不降峰；whole `moe`还会重放 routing、dispatch／combine 和 experts。不是所有模块组合都有意义。[Skill][recompute-skill]；[实际校验][core-config]。

**版本漂移必须在准入时处理。** 当前 Skill 称 pinned Core 的 portable labels 只有八种，`mhc`需另用开发分支；本次 Bridge 实际 gitlink 的 `TransformerConfig`却已接受 `mhc`、`residual_stream`、若干 GDN／GDP／DSA 标签，并各有架构与图约束。因此 adapter 应从固定版本验证实际模块与参数，保存 resolved config；不能复制旧允许列表，也不能把“配置接受”称作该模型路径已实测正确。[Skill][recompute-skill]；[固定源码][core-config]。

重计算涉及 RNG、dropout、FP8 scaling／amax、collective replay 和自定义算子状态。固定 Core 对 whole-MoE／shared-expert recompute 与 overlap 的组合、FP8 delayed scaling、图范围交界均有明确限制；应调用原配置校验且保留错误，不删断言换取启动成功。[固定源码][core-config]。后续性能比较需固定 optimizer 边界、GBS、数据次序和训练 token 数；改变 MBS 时相应调整 accumulation，另验证浮点归约差异。[measurement contract][recompute-skill]。

### 卸载兼容矩阵

|机制|真实输入与状态|固定源码边界|自动化程度|
|---|---|---|---|
|层级激活／可选权重卸载|`model.cpu_offloading`、`cpu_offloading_num_layers`、`cpu_offloading_activations`、`cpu_offloading_weights`，另有 double buffering|PP 必须为1；`recompute_granularity`必须为 `None`；与 fine-grained offload 互斥；层数 `0 <= n < num_layers`|手选开关／层数，不是自动模块搜索。[Skill][offload-skill]／[Core 配置][core-config]|
|细粒度激活卸载|`fine_grained_activation_offloading=True`、`offload_modules`、`activation_offload_fraction`、`min_offloaded_tensor_size`、PP-rank delta／host buffer|是另一条实现，允许 PP／interleaved PP，并可与不冲突的 selective recompute 配合；模块依赖、图 backend／scope、版本和 inflight joins 均须匹配|首轮记录 group、后续按 margin／PP delta／fraction 放置，是启发式运行时策略，不是以全局吞吐为目标的通用搜索器。[配置][core-config]／[运行时][core-offload]／[文档][core-fine-doc]|
|优化器状态与计算卸载|`optimizer.optimizer_cpu_offload=True`、`optimizer_offload_fraction`、`overlap_cpu_optimizer_d2h_h2d`、`pin_cpu_grads`、`pin_cpu_params`；使用 `HybridDeviceOptimizer`|与层级激活路径不同，不受上述 PP=1 限制。当前 pin 还要求 precision-aware optimizer 路径及 AdamW／decoupled weight decay；普通 Megatron 包装要求 distributed optimizer，MFSDP-v2 另有分支；FP8 param gather 另受 delayed recipe 限制|fraction 由外部给定；内部划分 CPU／GPU 子优化器，不自动选择最优比例。[配置][core-opt-config]／[构建与包装][core-opt-init]／[Hybrid 实现][core-hybrid]|

两处易错细节：

- **图支持不能仅抄 Skill。** Skill 写所有 layer-level CPU offload 与 CUDA Graph 互斥；固定 Core 实际仅在 graph 不是 `full_iteration`时拒绝，Bridge 的 full-TE-layer 特定实现又保留自身 guard。故默认采用文档保守配置 `cuda_graph_impl="none"`；请求 full-iteration 例外时须核具体 model spec、runner 和真实捕获／回放，当前只证明存在配置例外，不证明整条 Bridge 组合已运行。[Skill][offload-skill]；[Core][core-config]；[Bridge model spec][bridge-te]。
- **fraction 不是通用字节百分比。** fine-grained 的 `activation_offload_fraction`按合并后的 eligible groups 数量与执行顺序选择，不是 bytes 比例；warmup 和 steady-state 的选择规则也不同。固定 pinned buffer 是每 rank 预留，图捕获占用保留地址；PP／VPP 多个 in-flight microbatch 可能要求为整迭代量而非一个 microbatch 配置 host 内存。[固定文档][core-fine-doc]；[运行时][core-offload]。

官方 optimizer-offload 短跑在 Qwen3-30B-A3B、TP2／PP2／EP4 上报告，25%–100% fraction 对应约3.8–15.3GB节省、1.9–4.2倍 step time，20步 loss 差异小于0.001。它说明 CPU Adam／传输代价必须量测，**不是其他硬件的线性预测、长期收敛证明或本轮实测**。[官方 offloading 文档][offload-doc]。

## 可执行自动流程与搜索器

### DeepSpeed：成熟卸载库、配置搜索器与新编译 pass 分开

ZeRO 真正覆盖 optimizer／gradient／parameter 状态：`zero_optimization.offload_optimizer`支持 CPU／NVMe，parameter offload 仅 stage3；NVMe 使用显式 `nvme_path`和 buffer 设置，优化器计算仍在 CPU。`pin_memory`、read／write pipeline、CPU Adam fraction 均为原生字段。ZeRO-Infinity 论文给出分层内存与 overlap 的系统实现，不能把论文硬件结果外推给任意 PCIe／NVMe 主机。[固定 offload config][ds-offload]；[ZeRO 文档][ds-zero]；[ZeRO-Infinity 论文][ds-infinity]。

容量工具有 `estimate_zero3_model_states_mem_needs_all_cold(total_params, largest_layer_params, num_gpus_per_node, num_nodes, additional_buffer_factor=...)`及 live-model 版本，也有 ZeRO2 对应版本；cold API不要求先实例化完整模型。它估计 model states，不能替代完整激活峰值和最大层 gather 的运行检查；`additional_buffer_factor`也不等于所有内存来源都已覆盖。[估算文档][ds-memory]；[固定 ZeRO3 实现][ds-estimate]。

Autotuner 是真实原生流程：profile model info→容量剪枝→尝试 ZeRO stage／MBS／相关配置→grid／random／model-based tuner→保存最佳配置；CLI 是 `deepspeed --autotuning tune ...`或`--autotuning run ...`，用户固定 optimizer、scheduler、精度。官方当前文档明确**不支持 offloading 搜索**。源码可接收实验节点／GPU资源并管理原生实验；这不等于跨网络拓扑的卸载规划器。其 throughput 指标只累加 DeepSpeed forward／backward／step 内部计时，小于完整训练 latency；晋升前重测端到端。[教程][ds-auto]；[固定 Autotuner][ds-tuner]。

同时，当日 **0.19.10** 主线已有独立 DeepCompile 路径：`compile.offload_activation`按预算挑固定 shape、至少5MB的激活到 pinned host；`offload_opt_states`在 forward／backward 时卸载 FP32 master／Adam moments，step 时回载，源码注明针对 GAS=1，累积会重复整个交换周期；与 parameter offload／其他 pass 有互斥。不能因为旧 Autotuner 不搜卸载而否认新 pass 存在，也不能由 config 字段直接宣布成熟完整工作流。本轮仅核 config、backend 和 pass 目录，未完整核各 pass 的数值／恢复／多节点测试，**暂缓执行接入，向 R6 提供固定来源**。[CompileConfig][ds-compile]；[backend][ds-compile-backend]；[pass 目录][ds-compile-passes]。

**建议：**已有 DeepSpeed workload 可适配原 ZeRO 估算／卸载操作及 Autotuner；不为获得一个搜索器而迁移整个 Megatron 训练栈。CPU／NVMe仍按每节点本地容量与带宽预算，集群 GPU 数增加不自动增加某个 rank 可用的本地主存。

### PyTorch：稳定 checkpoint 工具与 prototype 预算求解

`torch.utils.checkpoint.checkpoint(..., use_reentrant=False, context_fn=...)`与`create_selective_checkpoint_contexts`／`CheckpointPolicy`提供可直接复用的重计算边界。源码说明若重放与原 forward 因全局状态等产生差异，可能出现静默错误；默认 determinism check 主要比较 shape／dtype／device，不能代替输出、梯度和更新值对照。RNG管理保存CPU及一种非CPU device type；region 内迁到新设备、随机自定义算子等需要额外核验。[2.15 源码][torch-checkpoint]。

2.15 的 `torch.autograd.graph.region_activation_memory_budget(budget)`已提供区域入口，但函数自身明确为 **prototype**；仅在 `torch.compile`下生效，eager 下抛错。`budget`的0–1是相对于该区域完整 checkpoint 与默认 runtime strategy 的激活量，**不是 GPU 总显存百分比或 bytes 上限**。一个 compiled graph 只允许一个一致预算，默认要求全部 forward op 被覆盖；不同区域需考虑 graph break，opaque higher-order region 可能重复重算。原生 min-cut／knapsack选择保存或重算，编译器默认禁止预算求解重算 collectives；不得为追求内存取消其保护。[区域 API][torch-graph]；[配置][torch-config]；[partitioner][torch-part]。

`torch.autograd.graph.save_on_cpu(pin_memory=...)`可用来手工卸载保存的激活；FSDP2 `CPUOffloadPolicy`则将参数、梯度和 optimizer states 放在CPU，是 R4 分片消费者的候选。它们本身不搜索全模型策略。当前 `_functorch.config.enable_activation_offloading`仍被源码标为 testing-purpose内部开关，不将其包装为稳定公共自动卸载服务。[autograd 源码][torch-graph]；[FSDP2 说明][torch-fsdp]；[内部配置][torch-config]。

**建议：**采用公共 checkpoint知识与审查工具；仅对本来已编译、形状与算子受支持的 workload 适配区域预算求解。不要把内存预算 API当作跨节点总内存规划器。

### Gemini：自动状态放置运行时，不是全栈训练搜索

当前 `GeminiPlugin(placement_policy="auto", warmup_non_model_data_ratio=..., steady_cuda_cap_ratio=..., pin_memory=...)`会收集 warmup 的非模型占用和 chunk 访问顺序，由 `AutoPlacementPolicy`决定驱逐／预取；静态模式另用 `shard_param_frac`、`offload_optim_frac`、`offload_param_frac`。该插件有真实 ZeRO／额外 DP／TP process-group 配置和 checkpoint IO，可作为已有 Colossal-AI训练的原生消费者。[插件][gemini-plugin]；[manager][gemini-manager]；[placement policy][gemini-placement]。

运行时适应的是参数／优化器等 model-data chunk 的放置，激活的非模型峰值用于留空间，不能据此称它同时自动寻找任意 checkpoint／PP schedule。模型访问模式变化会影响warmup预测，host capacity／通信／梯度累积应在目标 workload 核；本轮未核其完整跨节点故障恢复或长跑收敛。尤其 NPU 在插件中被显式限制为 **static placement**，所以“支持CUDA和NPU”不意味着 auto 模式也跨设备支持。[固定插件][gemini-plugin]。

**建议：**条件适配现有 Colossal-AI workload 的 auto 放置；不直接接成 Bridge 内部插件，不迁移训练框架来充数。

### MindSpeed：有实际自适应搜索，但多个机制不能混用

**SmartSwap 是本轮最完整的 Ascend 卸载闭环候选。**官方文档与源码对应：WarmUp采集tensor生命周期／必要时OOM rescue→SearchPolicy过滤候选、生成策略与模拟排布→Stable仅执行异步swap；入口`--smart-swap`。v2可选 activation优先或 activation＋optimizer策略，预算、冗余、最小tensor、带宽和搜索步数在`SwapPolicyConfig`中；真实 `SwapManager`维护阶段并把策略交给C++执行。[官方文档][ms-smart]；[manager][ms-smart-manager]；[配置][ms-smart-config]；[策略生成器][ms-smart-generator]。

边界同样明确：官方只适配静态序列，**未适配动态 MoE**；每卡换出量累加为节点 host 内存，文档例子8卡×30GB需至少240GB，尚未计其他进程／pinned scratch；自定义C++算子可能须补采集hook和构建链接。文档报告的TP／PP／重计算调整收益改变了布局，不能作为单独“swap本身快25%／28%”的因果证据。本轮未查到绑定该机制、同时完整披露多节点数值／恢复门禁的论文实验包，因此不追加系统级性能承诺。[SmartSwap][ms-smart]。

**Adaptive recompute 与联合 adaptive memory 是不同路径。**`--adaptive-recompute-device-size`、`--adaptive-recompute-profiling-step`对应 `GraphSolver`基于采样的成本／内存选择；`--adaptive-recompute-device-swap`在当前参数校验中明确**不能用于mcore models**，不能拿旧示例直接跑当前默认模型。`--adaptive-memory-optimization`又有独立`AdaptMemGraphSolver`／策略应用／optimizer.step hook，代码包含recompute、swap、OOM rescue以及历史策略缓存。[参数及互斥][ms-args]；[recompute controller][ms-adapt]／[solver][ms-adapt-solver]；[联合流程][ms-memory-opt]／[solver][ms-memory-solver]／[apply][ms-memory-apply]。

当前参数校验禁止 SmartSwap与adaptive selective recompute同开；联合memory路径与已有recompute、swap-attention、部分pipeline选项也互斥。联合solver显式建模PP／VPP在途microbatch，并在TP／DP组归约状态；这是分布式代码证据，**不等于任意跨节点组合已经验收**。缓存会读取软件／代码／模型相关信息生成身份，adapter仍应保存精确环境与原生policy，不把缓存文件当作训练checkpoint。[参数校验][ms-args]；[联合solver][ms-memory-solver]；[缓存][ms-memory-cache]。

另一个**Swap Optimizer**通过`--swap-optimizer`和`--swap-optimizer-times`在forward／backward期间卸载FP32权重副本／moments，step时分块回载到**NPU计算**，与CPU执行Adam的Bridge／ZeRO路径不同。官方限定distributed optimizer＋`fused_adamw`，与reuse-FP32-param／其他部分优化器特性不兼容；推荐按NPU对应NUMA绑核。[专属文档][ms-swap-opt]。

**建议：**借鉴采样→策略→稳定执行／失效重搜的设计；有授权Ascend资源且固定CANN／TorchNPU配套时，优先适配SmartSwap原生闭环。旧adaptive-swap、联合memory的入口可达性／测试矩阵、MoE、跨节点恢复和许可口径未核全，分别列为暂缓，不把开关存在写成普遍可用。

### Rockmate／HiRemate／OffMate：预算驱动的完整研究工作流

作者仓库把输入model、sample、GPU memory budget转换为新的`torch.nn.Module`：rkGB构图／测成本与带宽→分区→Rotor／层级ILP等solver→operation schedule→compiler生成forward／backward执行。Rockmate的原算法偏顺序网络，HiRemate放宽结构，OffMate联合weight／activation offload、rematerialization和CPU优化；OffMate还负责optimizer step，不应在外层再盲目执行一次step。[README][rock-readme]；[核心流程][rock-core]；[frontend][rock-front]；[OffMate作者原文][offmate-paper]。

**必须按源码修正接口。**README的`Offmate(model, sample, m_budget)`示例与当前签名不一致：第三个位置参数是`nlayers`，`budget`在其后。适配应使用`Offmate(model, sample, nlayers=..., budget=budget_bytes, ...)`等显式关键字，并检查solver配置；README的名称与部分示例也有漂移，不能照抄后声称可运行。当前Offmate使用HILP＋CBC、识别重复结构，核心硬编码CUDA device，不是任意分布式／动态模型的透明包装。[当前frontend][rock-front]；[核心][rock-core]。

作者原文报告单GPU十倍以内显存缩减、10%–50%开销等结果；只可作为所列模型／平台的作者报告。该流程需真实GPU profile、host RAM、traceable模型及solver时间；本轮未核多节点、checkpoint转换、恢复后optimizer状态、Flash／TE／FP8组合或生产训练生命周期，不能将“数学求解”当作这些门禁的替代。[原文][offmate-paper]；[依赖][rock-pyproject]。

**建议：**借鉴联合放置／重计算成本模型与schedule证据；若后续确有单GPU全量微调消费者，可用独立研究子模板适配。跨节点生产接入暂缓。

### 历史算法：保留来源，不作为即插即用接入

|候选|原始贡献与实际实现|本次判断|
|---|---|---|
|Checkmate，固定`6041c777`|论文提出MILP求解tensor rematerialization；作者主仓当前README仍只支持TensorFlow 2.0，需CyLP／CBC，Apache-2.0；论文artifact另有分支。[实现][checkmate]／[论文][checkmate-paper]／[许可][checkmate-license]|**借鉴／暂缓**：算法有价值，不能宣称现成PyTorch／Bridge／跨节点搜索器|
|DTR，固定`eff53cc4`|在线逐tensor驱逐与按需重算，支持动态图的研究方向；仓库含模拟器与修改PyTorch的prototype，复现实验还有旧TF／求解器依赖。[实现][dtr]／[论文][dtr-paper]|**借鉴／暂缓**：本轮未核其可分发许可与当前PyTorch集成，不直接复用代码，也不宣称已适配分布式训练|

## 跨节点与测量门禁

以下是建议的候选晋升合同，属于R5设计推论；具体阈值由父任务冻结，不能由搜索器按结果自调。

|门禁|必须留下的证据|拒绝或降级条件|
|---|---|---|
|身份与可达性|代码／镜像／驱动／框架／TE／CANN版本，模型spec、精度、attention backend、resolved config，实际工具operation列表|只给latest文档、参数能解析却未走该实现、模块被silent fallback|
|容量|每rank初始化／forward／backward／grad sync／step／checkpoint／eval峰值；allocated与reserved；节点CPU RSS与pinned峰值；NVMe路径和可用量|只看rank0，遗漏optimizer第一次创建或图池；host总量超过父预算；依靠未授予的memlock／主机设置|
|数值|同初始权重／optimizer／RNG／数据，比较forward、梯度、下一次参数更新；FP8 amax／scaler与跳步；覆盖dropout、梯度累积、MoE路由和边界输入|仅finite loss或metadata determinism；未排查重复optimizer.step、stale async copy、alias／view、collective重放不一致|
|质量／收敛|相同GBS、token预算、数据顺序、optimizer步数的对照；约定loss轨迹／评估质量容差；必要的更长跑|改变batch／精度／优化器语义后仍称纯执行优化；用20步差值替代长期收敛|
|恢复|保存并重建weights、master、moments、scheduler、scaler、RNG、data cursor；恢复后连续更新与对照一致；native policy／cache绑定环境|只保存模型权重；把临时host备份当checkpoint；复用不匹配shape／拓扑／代码的policy；unknown时盲重提作业|
|性能|预热／编译／策略搜索与steady态分开；完整step和tokens/s/GPU的配对重复；CPU／传输／collective时间及波动；报告Pareto候选与搜索开销|只用求解器估算／内部timer／异形baseline；通过改TP／PP／MBS同时改变多因素而宣称单项收益|
|跨节点|明确每节点CPU／NUMA／PCIe／NVMe和网络拓扑，所有process group、PP在途量及最热rank；在目标节点数重复必要门禁|把多GPU源码当跨节点实测；假设远端RAM／NVMe可透明池化；用单GPUOffMate收益推集群|

资源不足时先输出unsupported／insufficient-resource及具体缺项。降低MBS、增加TP／PP、关闭重计算或图均会改变实验对象，应生成新候选并由R4／R6共同核；不能暗改后沿用原证据。异步卸载的正确stream／event顺序、FP8状态和全体rank一致的checkpoint属于正确性／恢复门禁，不能归为“性能小问题”。相关原生边界见[Core offload runtime][core-offload]、[PyTorch checkpoint][torch-checkpoint]、[Hybrid state处理][core-hybrid]、[DeepSpeed checkpoint][ds-checkpoint]。

## 可组合的最小子模板

建议名称为“内存容量与代价选择”，是一项**待实现的方向合同**，不是本轮新增产品能力。它可由架构、性能诊断或kernel流程按瓶颈调用；同一执行者可覆盖重计算、放置和并行交接，独立数值／测量审查职责可复用其他模板，不以技术分类重复创建运行所有者。

**输入**：冻结workload与初始checkpoint；可训练／冻结参数与optimizer状态种类；sequence／shape分布、MBS／GBS／accumulation、精度和attention；并行拓扑与节点资源；允许修改的变量；精确源码和可用工具；GPU／CPU／pinned／NVMe与时长／试验数预算；数值／质量／性能阈值；父run／candidate和恢复位置。缺初始状态、容量或工具能力时先返回缺项。

**方向流程**：

1. 接收R7提供的每rank峰值／snapshot摘要，分清碎片与容量、状态与激活；用Bridge／DeepSpeed cold estimator做有假设的筛选。
2. 逐版本校验架构、并行、图和optimizer组合，生成有限候选：allocator／LoRA再通信、selective／full边界、某一种offload路径及fraction。允许多维原生搜索时，冻结其搜索空间与其他因素。
3. 按真实能力选可选消费者：Bridge受控runner；PyTorch已编译区域；DeepSpeed原生Autotuner或显式卸载runner；Gemini auto；MindSpeed原生SmartSwap；单GPUOffMate。完整原生流程只给一次预算与输入，内部循环和policy由其自身管理。
4. 实验消费者以原native ID输出配置、日志、policy／schedule、每rank与每节点metrics、失败和checkpoint；调优阶段与正式测量分开。超时／失联先查原job／原checkpoint，输出unknown；只在确认旧实例状态后按原所有者规则恢复。
5. 独立审查给出容量可行、数值／质量／恢复、端到端收益的分别结论；晋升仍由父candidate与owner approval决定。外层只汇总Pareto集和边界，不把native exit0／一条“best policy”视为批准。

**输出**：带identity／assumptions的容量分解；允许／拒绝组合及依据；候选配置diff与native policy／schedule；资源消耗与失败原件索引；匹配baseline的测量／质量报告；独立判词；`proposal_only`、`unsupported`、`insufficient_resource`、`unknown`、`no_gain`或`candidate_for_review`状态。静态估算只支持提案状态，不能直接产出训练通过。

**可选工具与父权限**：只读源码／公式工具默认足够做提案；snapshot解析、Nsight／torch profiler、GPU／NPU runner、CPU／NVMe telemetry和原生search分别声明是否可用及支持operation。子模板沿全部祖先完整读取资料／Skill／上下文，权限为所有父级的交集。它不能安装驱动／CANN、提升容器、修改主机memlock／时钟／NUMA／全局allocator，或自行申请节点与外部服务；只在父任务预授权的可信runner和资源内操作。报告资源约束与现有可行候选，不把工具缺失静默退化为模拟GPU收益。

**与现有Ergora的差距**：当前`training-optimization`仍为`proposal-leaves`，含实验设计／性能分析／kernel提案和测量审查；没有因本文新增训练执行或内存搜索消费者。D0可先选固定Skill知识与只读容量报告；选中原生流程后由D1增加真实消费者、artifact／状态／预算／unknown合同，再由D2建立子模板。维持原六阶段task／run／candidate、权限和恢复所有者，不添加第二账本或调度器。[当前preset](../../src/ergora/data/presets/presets.json)；[重整计划](../plans/2026-11-12-specialist-template-refresh.md)。

## 本轮证据边界

已核官方Skill对应职责、版本与许可原文、上述固定接口／部分控制流程、估算遗漏项和主要互斥；原生作者报告与本轮结果分开。没有做任何安装或训练验证，未证明目标机器容量、当前所有feature的运行入口、跨节点性能、长期收敛、checkpoint格式转换或恢复成功。OpenReview HiRemate页面返回challenge，其正文结论未核；不可用来源与旧路径失败回执保留，未用作能力证据。专用Agent的否定限于本轮可核候选，不是穷尽所有公开项目。采用／适配结论为后续D0选择建议，未导入整套参考目录，也未执行产品变更。

[index]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills-index.html
[memory-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-memory-tuning/SKILL.md
[recompute-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-activation-recompute/SKILL.md
[offload-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-cpu-offloading/SKILL.md
[bridge-package]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/package_info.py
[bridge-pyproject]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/pyproject.toml
[bridge-gitlink]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/tree/55694838ce73cd23b00ff95bd00512aefb963ce0/3rdparty
[bridge-license]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/LICENSE
[core-license]: https://github.com/NVIDIA/Megatron-LM/blob/928ce7ce256b734f00f1c81ddd3a8958d6b61ebf/LICENSE
[estimator-doc]: https://docs.nvidia.com/nemo/megatron-bridge/latest/training/memory-estimator.html
[estimator-src]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/utils/theoretical_memory_utils.py
[core-config]: https://github.com/NVIDIA/Megatron-LM/blob/928ce7ce256b734f00f1c81ddd3a8958d6b61ebf/megatron/core/transformer/transformer_config.py
[core-opt-config]: https://github.com/NVIDIA/Megatron-LM/blob/928ce7ce256b734f00f1c81ddd3a8958d6b61ebf/megatron/core/optimizer/optimizer_config.py
[core-opt-init]: https://github.com/NVIDIA/Megatron-LM/blob/928ce7ce256b734f00f1c81ddd3a8958d6b61ebf/megatron/core/optimizer/__init__.py
[core-hybrid]: https://github.com/NVIDIA/Megatron-LM/blob/928ce7ce256b734f00f1c81ddd3a8958d6b61ebf/megatron/core/optimizer/cpu_offloading/hybrid_optimizer.py
[core-fine-doc]: https://github.com/NVIDIA/Megatron-LM/blob/928ce7ce256b734f00f1c81ddd3a8958d6b61ebf/docs/user-guide/features/fine_grained_activation_offloading.md
[core-offload]: https://github.com/NVIDIA/Megatron-LM/blob/928ce7ce256b734f00f1c81ddd3a8958d6b61ebf/megatron/core/pipeline_parallel/fine_grained_activation_offload.py
[bridge-te]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/models/gpt_full_te_layer_autocast_spec.py
[offload-doc]: https://docs.nvidia.com/nemo/megatron-bridge/latest/training/cpu-offloading.html
[torch-checkpoint]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/utils/checkpoint.py
[torch-graph]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/autograd/graph.py
[torch-config]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/_functorch/config.py
[torch-part]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/torch/_functorch/partitioners.py
[torch-fsdp]: https://docs.pytorch.org/docs/2.15/distributed.fsdp.fully_shard.html
[torch-license]: https://github.com/pytorch/pytorch/blob/31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457/LICENSE
[ds-version]: https://github.com/deepspeedai/DeepSpeed/blob/de6fcf18ba1d3395dbcf0c6d48060da263b82da8/version.txt
[ds-license]: https://github.com/deepspeedai/DeepSpeed/blob/de6fcf18ba1d3395dbcf0c6d48060da263b82da8/LICENSE
[ds-offload]: https://github.com/deepspeedai/DeepSpeed/blob/de6fcf18ba1d3395dbcf0c6d48060da263b82da8/deepspeed/runtime/zero/offload_config.py
[ds-zero]: https://deepspeed.readthedocs.io/en/latest/zero3.html
[ds-infinity]: https://arxiv.org/abs/2104.07857
[ds-memory]: https://deepspeed.readthedocs.io/en/latest/memory.html
[ds-estimate]: https://github.com/deepspeedai/DeepSpeed/blob/de6fcf18ba1d3395dbcf0c6d48060da263b82da8/deepspeed/runtime/zero/stage3.py
[ds-auto]: https://www.deepspeed.ai/tutorials/autotuning/
[ds-tuner]: https://github.com/deepspeedai/DeepSpeed/blob/de6fcf18ba1d3395dbcf0c6d48060da263b82da8/deepspeed/autotuning/autotuner.py
[ds-compile]: https://github.com/deepspeedai/DeepSpeed/blob/de6fcf18ba1d3395dbcf0c6d48060da263b82da8/deepspeed/compile/config.py
[ds-compile-backend]: https://github.com/deepspeedai/DeepSpeed/blob/de6fcf18ba1d3395dbcf0c6d48060da263b82da8/deepspeed/compile/backend.py
[ds-compile-passes]: https://github.com/deepspeedai/DeepSpeed/tree/de6fcf18ba1d3395dbcf0c6d48060da263b82da8/deepspeed/compile/passes
[ds-checkpoint]: https://deepspeed.readthedocs.io/en/latest/model-checkpointing.html
[gemini-version]: https://github.com/hpcaitech/ColossalAI/blob/297c8cf6d91cb0bff795cba961d3aea1e66fa370/version.txt
[gemini-license]: https://github.com/hpcaitech/ColossalAI/blob/297c8cf6d91cb0bff795cba961d3aea1e66fa370/LICENSE
[gemini-plugin]: https://github.com/hpcaitech/ColossalAI/blob/297c8cf6d91cb0bff795cba961d3aea1e66fa370/colossalai/booster/plugin/gemini_plugin.py
[gemini-manager]: https://github.com/hpcaitech/ColossalAI/blob/297c8cf6d91cb0bff795cba961d3aea1e66fa370/colossalai/zero/gemini/gemini_mgr.py
[gemini-placement]: https://github.com/hpcaitech/ColossalAI/blob/297c8cf6d91cb0bff795cba961d3aea1e66fa370/colossalai/zero/gemini/placement_policy.py
[ms-readme]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/README.md
[ms-versions]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/docs/zh/release_notes_core.md
[ms-license]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/LICENSE
[ms-doc-license]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/docs/LICENSE
[ms-smart]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/docs/zh/features/smart_swap.md
[ms-smart-manager]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/core/memory/smart_swap/swap_manager.py
[ms-smart-config]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/core/memory/smart_swap/swap_policy_config.py
[ms-smart-generator]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/core/memory/smart_swap/policy_generator.py
[ms-args]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/arguments.py
[ms-adapt]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/core/memory/adaptive_recomputing/adaptive_recompute.py
[ms-adapt-solver]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/core/memory/adaptive_recomputing/adaptive_recompute_solver.py
[ms-memory-opt]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/core/memory/adaptive_memory/adaptive_memory_opt.py
[ms-memory-solver]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/core/memory/adaptive_memory/adaptive_memory_solver.py
[ms-memory-apply]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/core/memory/adaptive_memory/adaptive_memory_apply.py
[ms-memory-cache]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/mindspeed/core/memory/adaptive_memory/adaptive_memory_cache.py
[ms-swap-opt]: https://github.com/Ascend/MindSpeed/blob/c047aaad23c8cb97e70198b1f06701562a8141ff/docs/zh/features/swap-optimizer.md
[rock-readme]: https://github.com/topal-team/rockmate/blob/c2f678455393c5d872a1adb099949fe25f682bd0/README.md
[rock-pyproject]: https://github.com/topal-team/rockmate/blob/c2f678455393c5d872a1adb099949fe25f682bd0/rockmate/pyproject.toml
[rock-license]: https://github.com/topal-team/rockmate/blob/c2f678455393c5d872a1adb099949fe25f682bd0/COPYING
[rock-front]: https://github.com/topal-team/rockmate/blob/c2f678455393c5d872a1adb099949fe25f682bd0/rockmate/src/rockmate/frontend.py
[rock-core]: https://github.com/topal-team/rockmate/blob/c2f678455393c5d872a1adb099949fe25f682bd0/rockmate/src/rockmate/rockmate.py
[offmate-paper]: https://inria.hal.science/hal-04660745
[checkmate]: https://github.com/parasj/checkmate/blob/6041c777422328bb8ceaf04b34e3f68575b76ea2/README.md
[checkmate-paper]: https://arxiv.org/abs/1910.02653
[checkmate-license]: https://github.com/parasj/checkmate/blob/6041c777422328bb8ceaf04b34e3f68575b76ea2/LICENSE
[dtr]: https://github.com/uwsampl/dtr-prototype/blob/eff53cc4804cc7d6246a6e5086861ce2b846f62b/README.md
[dtr-paper]: https://arxiv.org/abs/2006.09616
