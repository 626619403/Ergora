# 量化与低精度：Agent、搜索流程和工具接入

检索日期：2026-11-12。沿官方文档、固定版本源码及原始论文核对；未安装依赖、调用模型或运行 GPU，也未复现作者收益。稳定版本以官方 release/tag 为准；Model Optimizer 的 Skill 单独固定在 `9aeff419f3afa1b27e7bcc10dc6a90cc68df4d77`，不能把该提交的说明直接授予旧版库。

**建议采用 Model Optimizer 的真实量化接口，适配其配方搜索 Skill，自建一个薄的候选与独立评价流程。** 本轮没有找到同时具备公开实现、明确许可、现代 LLM 部署、预算及恢复合同的成熟通用量化 Agent。存在真实 RL Agent、LLM Agent 论文和官方 Agent Skill，但成熟度与责任边界不同。Megatron Bridge 的 [skills 索引][bridge-index]可作训练方向入口，不是自动量化系统的能力证明。

## 任务边界

训练低精度和推理压缩需要两个子流程。Transformer Engine（TE）使训练中的部分 GEMM、激活和梯度使用 FP8/NVFP4，并管理 scaling/amax；高精度状态仍存在。PTQ 则从已有权重校准、量化、打包并导出推理模型。QAT/QAD 是为恢复量化后质量而训练：ModelOpt 固定版本的常规 QAT 使用模拟量化、固定 scale、更新权重；QAD 另加载冻结 BF16 teacher，以 logits KL 指导 student，增加显存和计算成本。它们不能被描述为“整个训练、优化器和权重均为 INT4”。[训练配置][bridge-mixed]、[QAT/QAD 指南][mopt-qat]及 [NVFP4 原始论文][nvfp4-paper]分别支持这些判断。NVFP4 预训练论文的下游评价使用 BF16；训练启用 FP4 不证明已经取得可部署的 NVFP4 推理 checkpoint。[QAD 原始论文][qad-paper]也明确区分训练加速与推理精度恢复。

## 可调用实现比较

|对象、固定版本与类别|真实能力和证据|限制与接入结论|
|---|---|---|
|**NVIDIA Model Optimizer 0.48.0**；Apache-2.0；优化库＋搜索算法|PTQ 有 FP8、NVFP4、INT8 SmoothQuant、INT4 AWQ 等；支持 Hugging Face 导出。`auto_quantize` 按层选择格式，可约束权重、active-MoE 或 KV-cache 的 effective bits。[源码][mopt-api]、[支持矩阵][mopt-ptq]|**采用工具、适配搜索**。格式支持逐模型不同；部分条目仅支持导出。NVFP4 推理需匹配 Blackwell 和运行时；TensorRT-LLM 路径注明版本 ≥1.2。搜索 API 明标实验性，结果未必可直接部署。Apache 许可不覆盖模型、数据和容器的全部条款。|
|**Transformer Engine v2.21.0**；Apache-2.0；训练算子库|有 FP8 current/delayed/block scaling、MXFP8、NVFP4 recipe；NVFP4 使用分块 scale、随机舍入及 Hadamard 变换。[recipe][te-recipe]、[硬件检查][te-support]|**采用训练工具**。FP8 可用性检查要求至少 SM8.9，Ada 另有 CUDA/cuBLASLt 条件；NVFP4 要求至少 SM10.0。MXFP8 对 SM12.0+ 明确拒绝“全部 GEMM 布局”支持。不能用“Blackwell”一词抹平数据中心卡与消费卡差异。它不搜索完整模型配方，也不提供质量验收 Agent。|
|**Megatron Bridge v0.7.0**；Apache-2.0；训练／转换集成|`MixedPrecisionConfig` 联动 model、optimizer、DDP；有 FP8 和独立 NVFP4 配置。ModelOpt PTQ/QAT 例程包含量化、恢复生成和导出。[训练][bridge-mixed]、[量化][bridge-quant]|**适配集成**。项目要求 Python 3.12；FP4/FP8 配置互斥，且需对应 TE 构建。此版量化指南明确自带例程是硬编码参考，QAT 表仅列 Llama-3-8B；规模化路径应核 ModelOpt 的 [Bridge 例程][mopt-bridge]，不能据通用格式列表声称任意模型已验证。|
|**Intel AutoRound v0.16.1**；Apache-2.0；PTQ 工具＋AutoScheme 搜索|支持 W2/3/4/8A16、NVFP4、MXFP 等配置；AutoScheme 结合层误差、平均位宽和共享层约束产生混合方案。[指南][ar-guide]、[生成接口][ar-code]|**适配第二工具**，适合低位权重与多硬件目标。量化端 CPU／CUDA／Intel GPU／Gaudi 支持不等于所有推理端都有高效 kernel。指南明确混合数据类型可调参但暂不能导出真实模型；embedding、model-free 模式也有限制。先限定可导出的单一格式族。|
|**Microsoft Olive v0.13.0**；MIT；ONNX 优化流水线＋搜索器|pass 搜索结合 accuracy/latency goals、候选 footprint、Pareto 结果与缓存；有 `max_iter`、`max_time`、`stop_when_goals_met`。[搜索源码][olive-search]、[engine][olive-engine]|**借鉴，ONNX 目标时适配**。停止条件仅在 joint 模式生效，且在步骤边界检查，不能代替外部硬超时；缓存不是完整 search state 恢复。源码在无候选满足 goals 时可退回忽略 goals 排序，因此“返回最佳模型”不能当质量通过。|
|**ModelOpt `quant-recipe-search`／`ptq`／`qad` Skill**；上述固定 SHA；仓库 Apache-2.0|不是独立 Agent runtime，而是供 Codex/Claude 等宿主消费的策略、执行和评价说明。配方搜索显式要求目标、BF16/FP16 baseline、AutoQuant 与人工对照、校准预算和迭代决策。[搜索 Skill][mopt-skill]、[PTQ 门禁][mopt-gate]|**适配专家资料与方向流程**。其评价说明还依赖 NEL、特定容器及部分内部 `modelopttools` 配置；[评价 Skill][mopt-eval]不能整包宣称公开可运行。其默认“每项差 1 个百分点”只是工具策略，应替换为任务自身门槛。|
|**MIT HAQ**；固定 `8228d126c800446fdc1cc263555d1e5aed7d9dfd`；MIT；真实 RL Agent|DDPG policy 逐层分配量化位宽，以硬件成本和准确率反馈训练；公开有搜索及 fine-tune 入口。[官方代码][haq-code]、[论文][haq-paper]|**借鉴，暂缓引入**。公开环境是 Python 3.7/PyTorch 1.1/CUDA10，主要为 ImageNet CNN；它是强化学习 Agent，不是现代 LLM 工具调用 Agent。历史硬件／模拟器成本不能迁移成当前 LLM 延迟收益。|

TE [官网 primer][te-primer]本轮标注 2.20.2，而最新 release 为 2.21.0；硬件限制以上述固定源码为准。安装时仍需锁定 CUDA、PyTorch、TE、Megatron-Core、Bridge 与推理框架的兼容组合，不能混用各项目 `latest` 示例。

## 搜索、预算和恢复的实际边界

ModelOpt 0.48.0 的默认梯度敏感度＋线性规划不是 LLM Agent；另有 forward-only KL 和 Aumann–Shapley 方法。校准和评分使用 `data_loader`，分别由 `num_calib_steps`、`num_score_steps` 限制；`checkpoint` 能恢复搜索状态、跳过昂贵评分。默认梯度方法需要 backward，PTQ 搜索也可能有较高显存开销。QKV 等融合组共享格式；禁止量化某层应使用明确 `disabled_layers`，不能假定普通 preset 的全局名称排除在搜索时仍生效。[API][mopt-api]

effective bits 是搜索成本模型，不能替代实际 checkpoint bytes、峰值显存或端到端吞吐。AutoRound 同样需要明确 scale/zero-point 是否计入位宽，并固定 `iters/nsamples/seqlen`；这是一组工作量旋钮，不是跨进程预算与恢复保证。[AutoScheme][ar-guide] 本轮未核到其持久搜索恢复合同，接入时应按独立候选重新执行，保存完整层配置，不能标记为无损续跑。

ModelOpt 的 [QAD Skill][mopt-qad]提供 GPU-hour／循环预算、分段训练、非有限 loss 停止、checkpoint 评价和同输出目录恢复的具体指导。这是可借用的薄编排规则，不是已具备的可信调度器；训练 loss 持续下降也不能代替任务质量。最终采用仍需外部所有者检查候选、预算和回执。

## 专用 Agent 论文的可采用程度

- **HAQA，v2，2026-04-04**：静态硬件／目标 prompt＋动态日志驱动量化微调与部署参数迭代，目标满足或达到最大轮数停止；实验包含 Llama、视觉模型与不同设备。论文摘要仍写 **Code will be released**，未核到作者关联的公开可运行实现和恢复接口。**借鉴反馈合同，暂缓 Agent 接入**；不能把论文所报 2.3× 当通用收益。[正文 §3–4、附录 B][haqa]
- **APQF，v1，2026-08-06**：确有五职责 agentic 设计；QuantAgent 用 Brevitas 模拟不同整数位宽并做 QAT/KD，EvaluationAgent 是固定样本的确定性程序，不使用 LLM。实验是 CNN/ViT，不是 LLM FP8/NVFP4。官方仓库固定 `2535a260c53090fef502bb889972f3870a72cd66` 明说仅有说明和海报、实现私有；公开树未见许可证。**借鉴职责分离，暂缓依赖**。论文 BOPs 降幅不能作真实硬件加速证明。[论文 §3、§6][apqf-paper]、[代码可用性声明][apqf-repo]
- **AutoQS，v1，2026-11-09**：真实 LLM 搜索研究，固定权重位宽，只搜索每层／算子组 group size；校验稀疏修改、去重、低成本代理评分，每 5 轮最多一次真实 GPTQ，100 轮最多 20 次机会。它区分机会、实际尝试和成功评价；冻结后七任务评估不回灌搜索，但七任务中三项已用于搜索，不能称全部独立留出。没有评估运行延迟，也未保留 token/API 成本，本轮未定位公开官方实现。**借鉴多保真搜索和记账，暂缓导入**。[§3–4、附录 A/C/E][autoqs]

这些论文证明“让模型参与量化决策”有具体研究实现；它们没有消除校准偏差、目标硬件验证、代码许可或独立质量门禁。

## Ergora 最小接入方案

先加入可替换的**量化实验设计专家**：消费完整模型／tokenizer／任务资料、部署目标和已接受 baseline，输出支持矩阵、有限配方集合、校准计划、预算及质量标准。可适配 ModelOpt 配方搜索资料，保留现有 measurement reviewer；当前只读 proposal 运行边界应继续明确显示，不声称该专家已执行量化。

真正执行时再提供**量化搜索子模板**：配方提出 → 确定性兼容校验 → ModelOpt PTQ/AutoQuant 或受限 AutoRound → 导出／加载校验 → 开发集评价 → 目标硬件测量 → 冻结候选后的独立评价／测量审查 → 原所有者采用决定。LLM 决定有限的下一候选，库负责量化，确定性评价器负责分数；沿用现有 task/run/candidate、Temporal 与 unknown recovery，不新增状态账本。

最小输入应冻结权重、tokenizer、校准集／开发集／最终留出集的身份，量化覆盖、融合组、format/algorithm/group size、软硬件版本及生成设置；预算至少含候选数、GPU-hours、单次硬超时、QAD tokens/steps、LLM tokens 和磁盘上限。输出关联配方哈希、搜索状态、完整 checkpoint 身份、原始指标、失败和实际花费。外部 job 状态未知时先按原 job ID 对账，再决定续跑；恢复必须校验模型、数据与配置一致。

门禁分开检查四件事：①权重覆盖、scale、元数据及 tokenizer/chat template 一致性；②开发集质量与逐任务退化，临界值重复测量；③真实后端的加载和目标负载吞吐／延迟／显存，包含 prefill/decode、KV-cache、长上下文或视觉任务；④冻结后的留出质量及独立审查。校准误差、KL/perplexity 只用于筛选，不能单独放行；训练分支另比较收敛、非有限梯度、恢复一致性和达到相同质量的总成本。没有满足门槛的候选就报告无解，不能输出一个“最佳”失败候选作为通过。

优先顺序：**采用 ModelOpt 工具 → 适配公开 Skill 核心和推理 PTQ 子模板 → 有目标硬件后验部署／质量 → 再适配 TE/Bridge 训练分支及 QAD**。AutoRound 是有具体格式需求时的第二适配；Olive 只在 ONNX 目标采用。HAQA/APQF/AutoQS 暂缓直接依赖，保留其方法证据。本报告提供选型与合同建议，不改变既有训练模板的执行能力。

[bridge-index]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills-index.html
[mopt-ptq]: https://github.com/NVIDIA/Model-Optimizer/blob/0.48.0/examples/hf_ptq/README.md
[mopt-api]: https://github.com/NVIDIA/Model-Optimizer/blob/0.48.0/modelopt/torch/quantization/model_quant.py
[mopt-qat]: https://github.com/NVIDIA/Model-Optimizer/blob/0.48.0/docs/source/guides/quantization_aware_training_and_distillation.rst
[mopt-bridge]: https://github.com/NVIDIA/Model-Optimizer/blob/0.48.0/examples/megatron_bridge/README.md
[te-recipe]: https://github.com/NVIDIA/TransformerEngine/blob/v2.21.0/transformer_engine/common/recipe/__init__.py
[te-support]: https://github.com/NVIDIA/TransformerEngine/blob/v2.21.0/transformer_engine/pytorch/quantization.py
[bridge-mixed]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/v0.7.0/docs/training/mixed-precision.md
[bridge-quant]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/v0.7.0/docs/modelopt/quantization.md
[ar-guide]: https://github.com/intel/auto-round/blob/v0.16.1/docs/step_by_step.md#autoscheme
[ar-code]: https://github.com/intel/auto-round/blob/v0.16.1/auto_round/auto_scheme/gen_auto_scheme.py
[olive-search]: https://github.com/microsoft/Olive/blob/v0.13.0/olive/search/search_strategy.py
[olive-engine]: https://github.com/microsoft/Olive/blob/v0.13.0/olive/engine/engine.py
[mopt-skill]: https://github.com/NVIDIA/Model-Optimizer/blob/9aeff419f3afa1b27e7bcc10dc6a90cc68df4d77/plugins/modelopt/skills/quant-recipe-search/SKILL.md
[mopt-gate]: https://github.com/NVIDIA/Model-Optimizer/blob/9aeff419f3afa1b27e7bcc10dc6a90cc68df4d77/plugins/modelopt/skills/ptq/references/checkpoint-validation.md
[mopt-eval]: https://github.com/NVIDIA/Model-Optimizer/blob/9aeff419f3afa1b27e7bcc10dc6a90cc68df4d77/plugins/modelopt/skills/evaluation/SKILL.md
[mopt-qad]: https://github.com/NVIDIA/Model-Optimizer/blob/9aeff419f3afa1b27e7bcc10dc6a90cc68df4d77/plugins/modelopt/skills/qad/SKILL.md
[haq-code]: https://github.com/mit-han-lab/haq/tree/8228d126c800446fdc1cc263555d1e5aed7d9dfd
[haq-paper]: https://arxiv.org/html/1811.08886v3
[haqa]: https://arxiv.org/html/2601.03484v2
[apqf-paper]: https://arxiv.org/html/2608.05499v1
[apqf-repo]: https://github.com/swapp-lab/APQF/blob/2535a260c53090fef502bb889972f3870a72cd66/README.md
[autoqs]: https://arxiv.org/html/2611.11975v1
[nvfp4-paper]: https://arxiv.org/html/2509.25149v1
[qad-paper]: https://arxiv.org/html/2601.20088v1
[te-primer]: https://docs.nvidia.com/deeplearning/transformer-engine/examples/fp8_primer.html
