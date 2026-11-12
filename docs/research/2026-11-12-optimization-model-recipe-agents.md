# 模型、配方与框架适配：Agent、压缩流程和验证合同

检索日期：2026-11-12。覆盖 [Megatron Bridge Skill Reference][index] 的 Auto Recipe／Recipe Index、Adding Model Support、LLM／VLM Bridge Patterns、Recipe／Test Patterns、Model Verification Card、MLM／Bridge 训练关联及 verl／NeMo-RL E2E，并补核模型结构搜索、剪枝蒸馏和质量评价。只读公开源码、官方文档与作者论文；未安装依赖、下载权重、调用模型／GPU或复现收益。原件、失败响应、URL、时间和 SHA256 留在私有 `.ergora/checks/specialist-template-refresh/research/model-recipes/`。

**建议采用 Bridge 的模型／配方／验证知识合同，适配 ModelOpt 的原生剪枝蒸馏流程，把 FT-Agent 保留为有边界的文本微调流程候选。** 本次没有核到可直接接管“任意新架构→Bridge 适配→训练／推理／RL 全部验证”的成熟专用 Agent。确有真实微调 Agent、NAS 搜索器、转换库和 Skill，但职责不同，不能把 Hugging Face、ModelOpt 或 Bridge 改名为 Agent。无需整体导入 NeMo。

本报告复用 [R2 的低精度与量化结论](2026-11-12-optimization-quantization-agents.md)和 [R4 的并行／硬件配方研究](2026-11-12-optimization-parallelism-agents.md)，不重做格式、模型或并行工具目录。Bridge 主线固定 `55694838ce73cd23b00ff95bd00512aefb963ce0`，源码自报 `0.8.0`；R2 的 `v0.7.0` 是另一快照，其 provider、转换和验证说明不能直接代替本文 builder 路径。[Bridge 版本][bridge-version]、[依赖][bridge-deps]

## Skill Reference 实际交付了什么

|职责|可复用的真实内容|决定与边界|
|---|---|---|
|Auto Recipe／Recipe Index|按模型、任务、硬件和长度查找已导出的 Python 配方；library 走 `scripts/training/run_recipe.py`，benchmark 走 `train.sh` 或性能 harness。要求把收敛语义与执行映射分开。[recipe-skill]|**采用选择与变更合同。** 这是推荐 Skill 和配方索引，不是训练全部候选的搜索服务；配方清单与 mesh 校验复用 R4。mock、forced routing、timing-only 配方不能充当真实训练基线。|
|Adding Model Support／LLM Patterns|从 HF config／实现识别结构，经 `hf_config_to_model_config_kwargs()`、`mapping_registry()`、builder-backed `ModelConfig` 接入；Qwen3 是当前配置模式，旧 GLM／OLMoE 示例仅供映射和 layer spec 参考。[adding-skill][llm-pattern][qwen3-code]|**适配模型接入专家资料。** 新模型实现是需要代码审查和验证的开发工作，接 R10 六阶段流程；Skill 本身不会自动生成、执行并批准适配。先复用现有块，只有缺失计算／组合才加局部模型代码，不能为追逐某条数值结果随意替换生产算子。|
|VLM／audio bridge|联合 config＋builder＋模态 wrapper；新适配优先直接调用 HF 感知编码器，Bridge 管映射、插入位置、放置、冻结和梯度同步。`tie_word_embeddings` 与语言字段可能位于不同 config 层。[adding-skill][vlm-pattern]|**按具体模态适配。** 文本通过不授予图像、视频或音频支持；旧原生视觉塔也不构成新模型必须照搬的要求。相同处理后的模态输入、位置／mask、projector、冻结和同步都需单独验证。|
|Recipe／Test and Example Patterns|构造完整 `ConfigContainer`、注册配方与导出；配置单测、toy roundtrip、真实发布 checkpoint 的转换／生成例子各自承担不同证据。[recipe-pattern][test-pattern]|**采用分层交付要求。** 单测可先于权重获取完成，真实转换、logits、训练证据缺失时保留未验；不能用 toy 模型通过声称实权重支持。|
|MLM vs Bridge Training|`vanilla_gpt_pretrain_config` 与 MLM `pretrain_gpt.py` 的配置映射、小模型 mock loss correlation、MCore main／dev 切换规则。[mlm-skill][mlm-guide]|**适配迁移与回归检查。** 必须匹配初始化、数据顺序、seed、loss、LR／warmup／decay及精度；“BF16 rounding 内一致”还须转成具体候选的冻结容差。十步 mock 关联不证明下游收敛。Skill 的删除旧目录指令应在隔离候选目录实现，不能作为清理既有实验的通用权限。|
|Model Verification Card|12项核心 inventory，分别记录 CPU／GPU 双向转换、forward correlation、确定性生成、pretrain／SFT／导出／长上下文／PEFT／resume；性能项仅在该模型有 canonical recipe 时增加。[card-skill]|**采用证据结构，适配校验器。** `verified`、`unverified`、`unsupported`、`not_applicable` 是验证卡声明；schema 校验器不能替代实际运行、日志和产物核验。公开卡排除私有集群配置、作业身份和凭据，原始执行证据留私有。|
|verl／NeMo-RL E2E|Bridge 单测／转换之后，进入外部 RL 框架，按 smoke、checkpoint、并行、架构特性和 learning signal 分级；不让 Bridge 接管 rollout／reward／checkpoint 调度。[verl-skill][nrl-skill]|**采用兼容性验收层，按需适配执行入口。** 默认 smoke 只有少量更新；没有自动验证全部模态、optimizer resume、weight refit 或收敛。|

## 足以决策的实现候选与固定版本

|实现、快照与许可|可调用接口和真实形态|接入结论|
|---|---|---|
|**Megatron Bridge** `55694838ce73cd23b00ff95bd00512aefb963ce0`，自报 `0.8.0`，Apache-2.0。[bridge-license][bridge-deps]|**库／CLI／Skill／验证工具**。`AutoBridge.from_hf_pretrained(..., revision=...)`、`get_model_config()`、`get_model()`、`load_hf_weights()`、`export_hf_weights()`、`save_hf_pretrained()`；公共转换入口 `scripts/conversion/convert.sh import/export`。[autobridge][convert]|**采用知识合同，适配转换／验证消费者。** 该快照 Python `>=3.12,<3.13`；MCore／TE／torch／镜像须成套锁定。模型被注册、能创建 config 或导出部分 tensor，都不是完整支持证明。HF 权重导出不是 optimizer／RNG／数据位置的训练恢复格式。|
|**NVIDIA Model Optimizer 0.48.0**，tag 对应 `e2f328a19de789e73b91aca2908042388cf6d496`，Apache-2.0。[mopt-license]|**架构搜索工具和完整原生流程**。Minitron：`modelopt.torch.prune.prune(..., mode="mcore_minitron", constraints=..., config=...)`；Bridge 示例 `prune_minitron.py`→`distill.py`→HF export→质量／推理评价。Puzzletron：YAML＋`torchrun examples/puzzletron/main.py --config ...`，另有 `--mip-only`。[pruning-api][pruning-readme][mopt-bridge][puzzle-readme]|**优先适配 Minitron 剪枝→短蒸馏→评价流程。** 它会改变结构／训练语义，必须立新质量实验。Puzzletron 可借鉴并有条件适配；异构结构的导出／部署约束更强，不能与均匀裁剪当成同一 checkpoint 类型。低精度分支交 R2。|
|**RD-Agent 的 FT-Agent** `484776c211e4fbbeef03e0ec00d6bbee7362a4f4`，MIT；源码快照，不声称此功能已经由某个 PyPI release 验证。[ft-license][ft-guide]|**真实 LLM Agent＋完整微调闭环**。`rdagent llm_finetune --base-model ... --benchmark ... --loop-n ... --timeout ...`；内部提出假设、生成数据处理代码和 LLaMA-Factory config、fail-fast 检查、训练、OpenCompass 评价、反馈迭代。支持 `--path` 恢复 Agent session。[ft-entry][ft-loop][ft-runner]|**适配为可选文本 SFT／LoRA 子流程，暂缓直接运行接入。** 它不是 Bridge 模型转换 Agent，也不是结构 NAS；入口断言基座模型自动选择尚未实现。需要 Linux、训练环境、GPU、planner／数据处理／部分 judge API及独立数据条款。完整流程应保留内部角色和反馈机制，不只摘一个“模型专家”名称。|
|**EleutherAI lm-evaluation-harness** `d6de81643928d653435c431bae19945d41d32520`，自报 `0.4.14.dev0`，MIT。[eval-license][eval-deps]|**确定性评价工具**，有 `lm_eval --model hf/vllm/... --model_args ... --tasks ...` 和 Python `simple_evaluate()`；可记录样本、seed、few-shot、bootstrap与缓存。[eval-readme][eval-code]|**采用评价合同，适配稳定文本任务后端。** 开发分支不是稳定 release；不能把 MIT 许可延伸到每个 benchmark／模型。VLM 入口仍标 prototype；直接 Megatron backend 不支持 PP>1、EP+TP，不据此宣称任意 Bridge 模型可直接评价。[eval-mcore]|
|**verl** `3255f6b1b1fc978be03e8598bc48f4f48d714be0`；**NeMo-RL** `27fac5f3d6bd7fffe0b4b601b52784afb76c6c44`；均 Apache-2.0。[verl-license][nrl-license]|**外部训练框架／测试流程**。verl 有 `tests/special_e2e/run_ppo_trainer_megatron.sh`；NeMo-RL 有 `tests/functional/grpo_megatron.sh`、`sft_resume_diamond.sh`及 Megatron setup。[verl-wrapper][nrl-grpo][nrl-resume][nrl-setup]|**按目标框架适配 E2E，而非整体导入或称作优化 Agent。** 本轮只证明公开接口存在和边界，未证明这些独立 HEAD 与指定 Bridge 已构成可安装／可运行组合。|

另核到真实 [AutoML-Agent 作者实现][automl-readme]（`9e0d842959a09d96c00768c14d73bd9df6d39023`），README 声明 CC BY-NC 4.0，Prompt Agent 依赖严格的 vLLM 0.4.1 和外部 LoRA adapter。其任务面主要是表格、图、时间序列等完整 AutoML；本次未核到可复用的 Bridge／现代 LLM 压缩接口及预算／恢复合同，**暂缓**。不因论文名含 AutoML 就替代上述专门工具；另试的根部 `LICENSE`／`agent_manager.py` 路径均404，只记录获取失败，不据此认定项目缺少实现，也不把未取得文件当成已审源码。

## 转换和数值一致：需要显式消费结果

当前 LLM 接入主线是 builder-backed config；部分已有模型仍走 legacy provider。模型 config、训练构建和转换构建必须代表相同计算，不能只让其中一条能运行。`AutoBridge` 提供懒加载／流式权重和模型特定映射钩子，但基类 `maybe_modify_loaded_hf_weight()` 默认只是读取 tensor；量化权重、scale、tied weights、QKV／MoE布局和特殊 norm 变换必须核具体 bridge，而非假定通用导入自动完成去量化。[autobridge][modelbridge][adding-skill]

**已核到不能仅凭 exit 0 晋升的具体入口。** 固定版 `compare_hf_and_megatron/compare.py` 计算 next-token match、最大／平均 logit 绝对差、cosine similarity，并为不匹配打印 ❌；该比较分支和主入口没有把这些数值失败转成非零退出。调用者必须解析并保存结构化结果、核数值和输入后判定，不能把命令完成当成功。验证卡 `validate_card.py` 检查 YAML、命令、字段和状态一致性，也不会替调用者运行训练或验证 checkpoint。[compare-code][card-validator]

Bridge 验证卡给出的 forward 门槛是同一输入 next token 相同且 cosine≥0.99，最大／平均绝对差是必须报告的诊断值，**不是其状态门槛**；这是单步功能关联，不能转称严格数值相等。无损转换另要求完整 key／shape／dtype／value 精确往返；有意改变表示才声明容差。适配应分别产出“序列化／完整性”“forward 关联”“生成”“有限训练”“恢复”“任务质量”结果，不能合成一个含义不清的 pass。[card-skill]

新证据还应覆盖持久 checkpoint 在新进程加载、实际 TP／PP／EP group、完整参数覆盖、相同 tokenizer／processor／token IDs／mask／位置，以及请求的全部模态。固定比较 helper 对视频明确限定 Nemotron Omni，不能让一个文本或单图 prompt 代表任意多模态路径。出现差异先定位最早模块，核映射、数学、精度和 routing；受控 module-swap 仅是诊断，不能因一次 swap 缩小差距就认定原实现正确。[adding-skill][compare-code]

训练关联与恢复需要单独合同：MLM／Bridge 的 mock 小模型用于发现实现或配置迁移差异；真实模型另以固定数据和优化步骤验 loss／gradient／update。验证卡的约100步支持验证也明确不等于完整收敛；resume 要从中间 checkpoint 直接续跑到相同终点，恢复 optimizer／RNG，按其声明 loss sentinel 比较，不能重跑前半段“恢复”。其 `1e-6 + 0.01*abs(reference)` 是该卡的支持验收规则，不能自动授予任意任务或当作 exact resume。[mlm-skill][card-skill]

## 模型结构、剪枝和蒸馏的原生流程

**Minitron 是当前最小可适配路径。** 先用校准 forward 统计 activation importance，再在限定 depth／width 结构空间内筛可行子网，以 `score_func` 评价 top-K，裁切权重并保存新架构；之后通过蒸馏恢复质量。当前示例支持总参数、active 参数或估算 `weights+KV-cache` 的 BF16 memory 约束，最后一项不是实测训练显存，也不包含 optimizer、激活、workspace和所有 runtime 开销。`prune_minitron.py` 明确断言仅支持 PP，TP／ETP=1；不能套用训练配方中的任意 TP／EP mesh。[minitron-code][minitron-search]

示例默认 top-10／MMLU 子集评分是候选筛选信号；原论文和当前实现都支持先做轻量恢复再决定长期投入。官方 Nemotron tutorial 明确没有对每个 NAS 候选先做短 KD，建议分数接近时导出若干 top-K、各做短蒸馏后按目标任务选择；其 ablation 也警告 proxy 排名可能在蒸馏后变化。因此外层质量评价必须保留，不能以最高 pruning score 或 loss 降低自动批准最终结构。[minitron-search][nano-tutorial][nano-ablations]

模态与训练边界很具体：VLM 只剪／蒸馏语言塔，视觉／音频编码器和 projector不在剪枝目标内，保存的整模型会大于 `--prune_target_*`；VLM 禁止裁 `hidden_size`。用纯文本校准不会看到视觉 token。当前剪枝示例还会去掉 MTP head，标准自回归路径与 speculative decoding 能力必须分别记录。蒸馏脚本要求 teacher／student vocabulary相同、padding 后 logits宽度相容；“任意 teacher→任意 student”不成立。[minitron-code][distill-code]

恢复也分三层：Minitron 的 per-rank intermediate scores 可重用／恢复昂贵评分，源码假定 `score_func` 和候选 filter不变；这不是训练 optimizer恢复。示例发现目标已有 checkpoint marker／HF config会直接退出，因此“已有输出＋exit0”不能证明当前候选已完成。`distill.py` 则从 `<output_dir>/checkpoints` 自动续训；换结构、数据、GBS或 schedule时须使用新实验身份和目录。当前 Nemotron两阶段教程因 seq／GBS／CP改变，采用中间 HF导出再启动新阶段，不能称它是保留全部训练状态的连续恢复。[minitron-code][minitron-search][distill-code][nano-tutorial]

**Puzzletron 是第二级结构流程。** 它以各层不同 FFN宽度和 attention op／noop组成异构模型，通过 replacement library、子块评分／统计和 MIP组合搜索；支持 memory／参数约束以及 runtime统计驱动的 latency约束。`--mip-only`复用已完成的剪枝、替换库和统计；不是从任意中断点完整恢复。文档明确子块 runtime并非线性叠加，举例 target5秒得到整模5.4秒，所以 solver满足约束还须独立整模测量。[puzzle-readme][puzzle-main][puzzle-plugin]

部署是其主要准入条件：固定版教程要求 AnyModel 支持的 vLLM fork和 `feature/add_anymodel_to_vllm`分支，并说明是等待正式集成的临时路径；本轮未核该 PR之后状态。不能把这种异构 checkpoint声称能直接交给原版 vLLM／任意标准 HF架构加载。只有获得确切 runtime与导出支持，才适合从“借鉴”推进到运行适配。[puzzle-readme]

论文与收益不能混用：Minitron [原始论文][minitron-paper]研究 Nemotron-4家族的剪枝＋蒸馏，后续 [Llama-3.1技术报告][minitron31-paper]和模型卡是另一批模型；“最多40×更少训练 token”比较新增小模型从头训练，不是推理40×，且仍有 teacher和恢复训练成本。Puzzle [作者论文][puzzle-paper]对应异构结构方法，当前 ModelOpt脚本另有自己的版本与 runtime边界。Nemotron-3 tutorial的2.6×吞吐来自单H100、ISL32768／OSL1024的剪枝＋FP8组合；其完整恢复训练为100B tokens、约9k H100 GPU-hours的作者示例，不是本机证据，也不能借给只做剪枝或其他长度／并发的候选。[nano-tutorial]

代码许可还不等于模型／数据许可。官方剪枝默认 `Nemotron-Post-Training-Dataset-v2`为 gated，本轮公开读取返回401，未尝试登录、读取凭据或绕过。Puzzle教程也要求接受相应权重和数据条款。公开 Qwen3-8B卡声明 Apache-2.0，而 Llama-3.1-Minitron-4B卡声明 NVIDIA Open Model License；具体 teacher、student、tokenizer、校准／蒸馏数据、合成服务条款及派生模型义务要逐项记录，不能从 ModelOpt Apache或 RD-Agent MIT 推导。[mopt-bridge][puzzle-readme][qwen-card][minitron-card]

## FT-Agent：值得适配的真实 Agent，范围是文本微调

FT-Agent有可追到入口、循环、runner和配置的作者实现，能在任务／数据策略与训练配置之间迭代；当前 README还扩展了原 FT-Dojo以外的 benchmark adapter。其基座模型自动选择在入口中明确断言未支持，开放任务 `user_target_scenario`也尚未启用；不能据 docstring的 auto-select描述声称它会自动选模型／硬件。[ft-entry][ft-guide]

可调面是 benchmark adapter、允许的数据集／训练样本上限、基座 checkpoint、生成的数据代码、LLaMA-Factory配置、loop数、超时、planner／数据处理模型及API并发；输出包括代码、配置、训练 checkpoint、OpenCompass结果和历史trace。它没有输出可直接用于 Bridge的转换映射／模型builder，也没有证明 VLM、NAS或 RL rollout优化。先将其作为完整上游微调子流程，不把每个内部步骤拆成外层新增状态机。[ft-guide][ft-loop][ft-runner]

预算必须由原运行所有者补强。`--timeout`传给 `LoopBase`，timer在循环步骤检查，不能当作每个训练／API调用的硬截止；场景构造还会先准备所有注册数据、环境和baseline，然后才进入 `loop.run()`。配置默认 full training timeout为100小时、benchmark timeout为0；`--dataset`只约束准备后的选择。`--path`恢复Agent session并可能清理后续session日志，不等于恢复训练optimizer／数据位置；适配应保留原trace、显式限下载／API／GPU预算，并把恢复绑定到精确候选和原生执行身份。[ft-entry][ft-scenario][ft-settings][ft-timer]

论文 [FT-Dojo v1][ft-paper]的“13任务中10项最佳”来自单B200、12小时、Qwen2.5-7B-Instruct、每任务最多2000训练样本及指定planner／合成／judge模型；它证明该设置下闭环有价值，不证明通用配方最优、目标Bridge兼容或结构搜索收益。论文也记录了无因果诊断的多项干预导致波动。采用其validation反馈与独立test分离的方法，但把最终测试集、质量门槛和采用决定留给独立评价者；不能让搜索Agent修改这些目标。[ft-paper][ft-guide]

同仓 [Agent² RL-Bench][rlbench-guide]已有公开研究入口、原始模型baseline、逐次模型提交评价和有限时Agent运行；`run.py`对Agent子进程有timeout／进程组停止，但模型／数据准备及baseline评价发生在此前，且启动环境复制`os.environ`。它是评估自主RL工程能力的artifact，不是给Ergora替换正式训练所有者的运行服务；其自身scores／CSV只可作原生产物。本轮未完整审计grading server实现／各训练backend，**借鉴评价环境和预算口径，暂缓直接接入**，不把其[论文][rlbench-paper]或README的组件数当作已验能力。[rlbench-run]

## RL 下游 E2E 与版本配套

|下游路径|固定源码核到的默认行为|适配所需的独立出口|
|---|---|---|
|verl Megatron|wrapper支持 `USE_MBRIDGE`、LoRA、DDP／可选FSDP、分开的actor／ref／critic／rollout mesh、`SAVE_FREQ`和`RESUME_MODE`；默认1训练步、LoRA rank0、保存／恢复关闭。Skill的Level0需要显式开启LoRA。[verl-wrapper][verl-skill]|验证worker实际加载指定Bridge checkout；确认算法、adapter target、非平凡parallelism和实际生效配置。当前wrapper已不读取Skill示例的`VANILLA_MBRIDGE`／`VALUE_VANILLA_MBRIDGE`，不能以设置旧变量证明覆盖了相应路径。checkpoint／adapter export另跑save+resume。|
|NeMo-RL Megatron GRPO|`grpo_megatron.sh`使用Qwen2.5-0.5B、2GPU、2steps，`checkpointing.enabled=false`，另检查token probability误差及ratio界。[nrl-grpo]|两步成功只覆盖小型文本GRPO。当前脚本要求`max(train/token_mult_prob_error)<1.05`；指标失败须定位generation与policy重算不一致，不能仅凭步数完成或放宽阈值通过。VLM／audio、LoRA、非colocated refit和checkpoint用各自variant。[nrl-skill]|
|NeMo-RL checkpoint／weight transfer|有独立SFT resume diamond测试、Bridge导入导出和Megatron setup，Skill另给non-colocated vLLM refit／delta transfer层。[nrl-resume][nrl-setup][nrl-skill]|区分权重导出完整性、policy→generation refit、optimizer／RNG／scheduler／数据位置恢复。外部框架继续拥有cadence与trainer状态；不在Bridge或方向模板再建checkpoint调度器。|

有一项可以在安装前直接拒绝的配套冲突：本轮固定Bridge声明 Python `>=3.12,<3.13`，而上述 NeMo-RL HEAD声明 `>=3.13.14,<3.14`，还使用自己的vendored Bridge和backend依赖组合。它们不能作为同一个Python环境的标准依赖组合直接拼接；这不意味着NeMo-RL无可用Bridge集成，而是必须选择其成套的、另行核验的snapshot，不能把两个独立`latest`当作已经兼容。[bridge-deps][nrl-deps]

原测试wrapper也不是无副作用的产品接口：NeMo-RL GRPO脚本会改global Git safe.directory并删除固定实验目录；verl脚本会自行准备／使用cache和模型输出。方向适配应将命令、目录、资源与环境注入改为候选限定接口，保留原框架行为证据，不扩大到宿主权限或任意目录清理。当前Skill提供的是验收方法，未解决本项目原有task／run／unknown recovery的消费者缺口。[nrl-grpo][verl-wrapper]

## 最小可引用子模板合同

建议先有“模型／配方适配与验证”子模板，再按需要引用“结构压缩”和“文本微调闭环”。技术标签不决定Agent种类；模型适配编码者、配方研究者、原生流程执行者和独立质量评价者可以是可替换实现，同一精确定义可以被多个模板引用。以下为建议合同，尚未实现或执行。

|合同面|最小输入／输出和权限|
|---|---|
|共同输入|精确源码／镜像／依赖、HF权重／config／tokenizer／processor revision及摘要；模型／任务／模态、结构和允许变更；数据来源／许可／split／预处理／顺序／seed；可跑baseline与原件；目标训练／推理／RL框架、硬件拓扑、长度／batch／并发分布；候选数、token／GPU-hours／wall-time／磁盘／API预算。未取得gated资料明确标缺，不能偷偷换数据或权重。|
|模型／配方适配输出|匹配的已导出recipe及可复现入口；config／builder／mapping覆盖与量化／模态限制；参数完整性、持久reload、forward／generation、有限训练／resume和目标框架E2E逐项结果。未支持／未验分开记录，schema pass不晋升runtime能力。代码变更交既有六阶段开发与审查。|
|结构压缩输出|有限结构空间／constraints、校准与proxy定义；每候选architecture／权重／score缓存身份；top-K短蒸馏及最终独立任务质量；可重载／可部署导出、真实峰值显存与完整训练／推理测量。memory估计、MIP目标、proxy score和实测结果分别保留。结构／precision／GBS改变明确立新语义实验。|
|FT-Agent输出|原生hypothesis／代码／训练config／数据manifest／validation反馈／checkpoint／trace，连同确切backbone与API用量；final test由外部独立角色执行。保留上游内部循环和session，不把其trace当第二正式状态账本。|
|权限上限|全部父级资料／Skill／上下文沿结构祖先累加读取；子流程权限不超过任一父级。模型与原始数据只读、候选输出和允许源码目录可写；GPU、训练／推理服务和外部API按已授权backend操作。只注入必要环境引用，不复制宿主全部环境；网络下载／远程代码／数据合成各按实际需要限定。运行适配保持现有可信容器边界，不要求Docker宿主权限或任意mount。|
|质量合同|在搜索前冻结baseline、训练语义、独立holdout和任务质量／稳定性门槛；转换无损与新结构质量门槛分开。文本、VLM、RL选择能激活变化的真实数据；greedy sample、cosine99、十步mock或2步GRPO各只授予其覆盖。测量固定推理ISL／OSL／batch／并发或训练token／step口径，报告全部rank峰值、耗时、失败和方差；对小样本／judge质量给出实际不确定性，不能跨tokenizer按绝对loss排名。|
|预算与恢复|launch前冻结candidate／attempt，执行后保存原生job／process身份和产物manifest；失联先查原身份，未知保持unknown，不盲目重启。搜索cache、Agent session、训练checkpoint和HF部署导出分别验证；已有目录／marker、process exit0或最高score不能证明完成。预算在准备／API／训练／评价全阶段约束，终止后确认所属执行已停止；失败和无收益保留。|
|独立采用出口|方向Agent不能修改reference、容差、test split或胜出门槛；独立评价者核精确candidate、原件、实际生效路径及恢复证据，原正式所有者决定采用。上下游协作边传递具名产物，不增加资源继承、提权或第二调度者。|

质量工具建议先使用固定文本任务的lm-eval HF／vLLM后端，保存模型revision、chat template、few-shot、生成参数、seed、task版本、逐样本输出和统计。`limit`仅作开发／筛选，最终任务评价用预先冻结的独立集合；cache须绑定模型／数据／评价版本。VLM prototype和直接Megatron backend的范围不足时明确unsupported，不用一个文本分数替代视觉／音频质量。[eval-code][eval-readme][eval-mcore]

## 跨域依赖与接入顺序

|依赖方向|R9提供／需要的交接|
|---|---|
|R2低精度|模型dtype／quantizer／scale与checkpoint表达、压缩后的架构及质量预算→PTQ／QAD／导出支持；先结构后量化或反向组合都立独立实验，不能把两次收益相乘作实测。|
|R3通信＋R4并行|结构／heads／专家／layer schedule和新参数量→合法mesh／stage与传输矩阵；剪枝脚本的PP-only能力与最终训练／服务mesh分别记录。硬件配方／搜索复用R4。|
|R5显存＋R6执行图／数据|teacher+student同时驻留、视觉塔、KV及新shape→实测峰值／recompute／offload／graph支持；packing、loss mask、token预算和模态插入保持训练质量合同。|
|R7测量＋R8集群恢复|提交完整训练／推理目标与baseline，消费可信时间／显存／trace及原生job／checkpoint恢复；不能把本地序列化或预测约束当集群实效。|
|R10开发流程|新bridge／builder／recipe代码、依赖配套、分层测试与公开验证卡进入既有六阶段；引用原运行所有者，不为模型方向复制开发状态机。|
|X1–X3后续横向|输出结构／框架能力、预算、质量和失败证据；全局架构决策、跨域搜索／诊断、干预冲突与归因另做，不由R9宣称已有全能优化Agent。|

实施优先为：**先采用模型／配方与验证卡合同，补真实转换／评价消费者；再适配Minitron的有限结构候选→短KD→独立评价；有明确文本SFT任务时适配FT-Agent完整子流程；RL按目标框架补其真实E2E，Puzzletron按异构部署需求另准入。** 目前只有只读提案接口的部分仍应显示只读，不因增加Skill、候选目录或关系图就声称已经训练、搜索或验证。

本轮94次公开GET保留80份200原件和14份失败响应（11×404、2×GitHub API403、1×gated数据401）；200中还包含没有取得可用检索结果的Google页面，未把它作为能力证据。搜索连接器本次不可调用，失败另存；六项目的公开`git ls-remote`结果用于绑定snapshot／tag。未继续扩展候选或修上游缺页，未改产品、计划、模板，未提交／推送。上述建议没有授予本机可安装性、GPU收益、完整收敛或异常恢复结论。

[index]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills-index.html
[bridge-version]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/package_info.py
[bridge-deps]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/pyproject.toml
[bridge-license]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/LICENSE
[recipe-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-recipe-recommender/SKILL.md
[adding-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/adding-model-support/SKILL.md
[llm-pattern]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/adding-model-support/llm-patterns.md
[vlm-pattern]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/adding-model-support/vlm-patterns.md
[recipe-pattern]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/adding-model-support/recipe-patterns.md
[test-pattern]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/adding-model-support/tests-and-examples.md
[qwen3-code]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/models/qwen/qwen3_bridge.py
[mlm-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-mlm-bridge-training/SKILL.md
[mlm-guide]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/docs/megatron-lm-to-megatron-bridge.md
[card-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/create-model-verification-card/SKILL.md
[card-validator]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/create-model-verification-card/scripts/validate_card.py
[autobridge]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/models/conversion/auto_bridge.py
[modelbridge]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/models/conversion/model_bridge.py
[convert]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/scripts/conversion/convert.sh
[compare-code]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/examples/conversion/compare_hf_and_megatron/compare.py
[mopt-license]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/LICENSE
[pruning-api]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/modelopt/torch/prune/pruning.py
[pruning-readme]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/pruning/README.md
[mopt-bridge]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/megatron_bridge/README.md
[minitron-code]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/megatron_bridge/prune_minitron.py
[minitron-search]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/modelopt/torch/prune/plugins/mcore_minitron.py
[distill-code]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/megatron_bridge/distill.py
[puzzle-readme]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/puzzletron/README.md
[puzzle-main]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/puzzletron/main.py
[puzzle-plugin]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/modelopt/torch/puzzletron/puzzletron_nas_plugin.py
[nano-tutorial]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/megatron_bridge/tutorials/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16/README.md
[nano-ablations]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/megatron_bridge/tutorials/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16/ABLATIONS.md
[minitron-paper]: https://arxiv.org/html/2407.14679v1
[minitron31-paper]: https://arxiv.org/html/2408.11796v2
[puzzle-paper]: https://arxiv.org/html/2411.19146v1
[qwen-card]: https://huggingface.co/Qwen/Qwen3-8B/blob/main/README.md
[minitron-card]: https://huggingface.co/nvidia/Llama-3.1-Minitron-4B-Width-Base/blob/main/README.md
[ft-license]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/LICENSE
[ft-guide]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/app/finetune/llm/README.md
[ft-entry]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/app/finetune/llm/loop.py
[ft-loop]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/scenarios/finetune/loop.py
[ft-runner]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/scenarios/finetune/train/runner.py
[ft-scenario]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/scenarios/finetune/scen/scenario.py
[ft-settings]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/app/finetune/llm/conf.py
[ft-timer]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/utils/workflow/loop.py
[ft-paper]: https://arxiv.org/html/2603.01712v1
[rlbench-guide]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/scenarios/rl/autorl_bench/README.md
[rlbench-run]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/scenarios/rl/autorl_bench/run.py
[rlbench-paper]: https://arxiv.org/html/2604.10547v1
[automl-readme]: https://github.com/DeepAuto-AI/automl-agent/blob/9e0d842959a09d96c00768c14d73bd9df6d39023/README.md
[eval-readme]: https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/README.md
[eval-code]: https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/evaluator.py
[eval-mcore]: https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/models/megatron_lm.py
[eval-license]: https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/LICENSE.md
[eval-deps]: https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/pyproject.toml
[verl-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/verl-e2e-testing/SKILL.md
[nrl-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-rl-e2e-testing/SKILL.md
[verl-license]: https://github.com/verl-project/verl/blob/3255f6b1b1fc978be03e8598bc48f4f48d714be0/LICENSE
[nrl-license]: https://github.com/NVIDIA-NeMo/RL/blob/27fac5f3d6bd7fffe0b4b601b52784afb76c6c44/LICENSE
[verl-wrapper]: https://github.com/verl-project/verl/blob/3255f6b1b1fc978be03e8598bc48f4f48d714be0/tests/special_e2e/run_ppo_trainer_megatron.sh
[nrl-grpo]: https://github.com/NVIDIA-NeMo/RL/blob/27fac5f3d6bd7fffe0b4b601b52784afb76c6c44/tests/functional/grpo_megatron.sh
[nrl-resume]: https://github.com/NVIDIA-NeMo/RL/blob/27fac5f3d6bd7fffe0b4b601b52784afb76c6c44/tests/functional/sft_resume_diamond.sh
[nrl-setup]: https://github.com/NVIDIA-NeMo/RL/blob/27fac5f3d6bd7fffe0b4b601b52784afb76c6c44/nemo_rl/models/megatron/setup.py
[nrl-deps]: https://github.com/NVIDIA-NeMo/RL/blob/27fac5f3d6bd7fffe0b4b601b52784afb76c6c44/pyproject.toml
