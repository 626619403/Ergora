# 并行策略、分片与拓扑配方：工具、流程和 Skill 候选

检索日期：2026-11-12。本报告按用户给出的 [Megatron Bridge Skill Reference][index] 细分领域，覆盖 TP／DP／PP／EP／CP、Megatron FSDP、hierarchical／dynamic context parallel、vision DP over CP，以及 MoE 长上下文和硬件配方。只做官方文档、作者论文和公开源码的只读研究，未安装依赖、运行模型／GPU、复现性能或验证集群恢复。原件、抓取失败及 SHA256 保存在私有 `.ergora/checks/specialist-template-refresh/research/parallelism/`；这是一份接入建议，不是产品已支持的声明。

**建议先采用配方选择和约束检查的知识合同，适配有界候选生成→实际训练测量→独立验收流程。** 本次核对的官方项目中，没有找到可以直接作为通用 TP／PP／EP／CP／FSDP 搜索专家调用的专用 LLM Agent 或官方 MCP。存在的是 Agent 可读的 Skill、自动并行编译／搜索工具，以及需要训练运行器承接的完整实验流程。不能把 Megatron Core、nnScaler 或 Auto Configurator 改名为 Agent。技术方向也不是互斥 Agent 类型：架构设计 Agent 可以同时使用并行、显存、通信和 kernel 证据；本文只定义这一纵向能力的输入输出，跨域 Agent 的横向比较另做。

## 由实际 Skill Reference 得到的能力边界

|能力|真实实现与接口|约束、证据和接入结论|
|---|---|---|
|TP／SP、DP、PP／VP、EP／ETP、静态 CP|Bridge provider／`ConfigContainer` 字段，最终进入 MCore 进程组和训练调度；`run_recipe.py --recipe <函数名>` 支持字段覆盖。[parallel-skill][bridge-run][mcore-state]|**采用知识，适配运行器。** TP／SP 管层内切分，PP／VP 管层和调度，EP 管专家，CP 管序列；DP 是配置派生值。拓扑、KV heads、专家数、层／stage 切分、batch 整除共同决定合法性，不能只按参数规模套表。Skill 的规模／序列阈值是搜索起点，不能当正确性规则。|
|配方推荐与硬件映射|`nemo-mbridge-recipe-recommender` 是 Skill＋配方索引；library recipe 走 `scripts/training/run_recipe.py`，benchmark recipe 走 `scripts/training/train.sh` 或兼容性能 harness。[recipe-skill][recipe-index][bridge-harness]|**采用经过校准的选择流程。** “Auto Recipe”没有交付自动搜索服务。library 旨在功能训练，`perf_recipes` 是特定卡数、卡型、精度的吞吐配方；修改 benchmark 后即不再是原 canonical 配方。无需整体导入 NeMo。|
|Megatron FSDP|Bridge `dist.use_megatron_fsdp`、`ddp.use_megatron_fsdp`、`data_parallel_sharding_strategy="optim_grads_params"`、`checkpoint.ckpt_format="fsdp_dtensor"`。[fsdp-doc][fsdp-skill][bridge-config]|**有条件适配。** 分片模型状态，适合参数／梯度／优化器状态受限；不能代替 CP／重计算解决 activation 峰值。与 `use_torch_fsdp2` 互斥，禁止 `use_tp_pp_dp_mapping`。FSDP2 在此分支仍是实验路径，不能用相同名字替换。|
|Hierarchical CP（HCP）|`cp_comm_type="a2a+p2p"`、`hierarchical_context_parallel_sizes=[内层,外层]`，组内 a2a、组间 p2p；通过 MPU 路径创建层次组。[hcp-doc][hcp-skill][bridge-init]|**暂缓默认推荐；仅显式候选。** 适合 CP 需要超过当前 TP 下 KV head 限制，且网络有明确带宽层次的情况。要求乘积等于 CP、序列长度可被 `2*CP` 整除、TE≥1.12，并使用 `dist.use_decentralized_pg=False`。文档承认缺少专用 Bridge 端到端验收；先比较简单 a2a／p2p。|
|Dynamic CP|每个 packed microbatch 按最长序列动态选 CP group；Bridge 配置接 MCore `default_dynamic_cp` scheduler。[dynamic-doc][dynamic-readme][bridge-config]|**暂缓通用接入，允许专门适配实验。** 这是运行时调度算法，不是全局并行配置搜索。需要 global-batch packing、single dataloader、MBS1、正确 per-token loss，DP×CP pool 和最小组大小满足二次幂规则；依赖 MCore **dev pin**，与 HCP 一样不能假设 decentralized PG 可用。必须先看真实长度分布和热 rank 的显存。|
|Vision DP over CP|Nemotron Omni 的 `model.vision_dp_over_cp`；借语言 CP group，把完整图像／tubelet 分到各 rank，编码、投影后 gather。[vision-skill][vision-model]|**限定模型适配。** 不是 ring attention，也不是 `dist_train.vision_context_parallel_size`；后者给视觉塔自己的 rank／序列切分。前者默认开启但 CP1 时无效；提高 CP 可能同时悄然启用图像分片。可迁移的是 split→encode→project→gather 模式，不能声称所有 VLM 已支持。|
|MoE 长上下文、硬件／PP 配方|`moe-long-context` 和 `moe-hardware-configs` 的平台、CP、PP／VPP、recompute 搜索种子；实际配方仍是 Python config 函数。[long-skill][hardware-skill]|**采用候选生成方法，适配具体配方。** H100、B200、GB200／GB300 的行不能相互外推；长上下文改变 CP／DP 预算，常与重计算／offload 共决策。强制 router balance、精度、token dropping、GBS 改动可能改变训练语义，不能只按 TFLOPS 晋升。|

通信库、collective 实现和 overlap 搜索由 R3 负责。本方向输出并行 degree、rank／stage 映射、通信形态和合法组合；R3 返回后端可用性、正确性、带宽／延迟及 overlap 证据。`a2a+p2p` 在这里是策略约束，DeepEP／HybridEP 在这里是配方依赖；不重复认领它们的库适配或性能调优。

## 固定版本、真实自动搜索与公开调用面

下列 GitHub SHA 用公开 `git ls-remote` 核对。GitHub REST 的 commit／latest-release 请求遭遇 403，因此不宣称已经核到“最新发布版”。源码自报版本与 release 是不同证据。MindSpore 采用官方文档指向的 Gitee 固定 tag 和文件摘要，未核到该 tag 的完整 Git SHA。

|项目／快照、许可|交付形态和可调用入口|资源、搜索范围、正确性／恢复边界|决定|
|---|---|---|---|
|Megatron Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0`，源码自报 `0.8.0`；Apache2.0。[bridge-src][bridge-license]|**库／CLI／Skill／配方流程**。`run_recipe.py` 和 `train.sh` 运行已选配方；`setup_experiment.py` 解析／启动性能实验。未核到由这些入口自动搜索全部并行维度的专用 Agent。|此快照要求 Python≥3.12,<3.13、torch≥2.6；TE／MCore／CUDA 实际兼容必须按完整镜像／锁定依赖核。`.main.commit`=`928ce7ce256b734f00f1c81ddd3a8958d6b61ebf`，`.dev.commit`=`f78809f6d9c88f8638ea7822966f35057a63fd5c`，dynamic CP 需要后者；不能把两栈混为一次实验。[bridge-deps][mcore-pins] MCore 主体 BSD3，第三方文件另有许可，Bridge 的 Apache2.0 不覆盖全部外部栈。[mcore-license]|**采用 Skill／合同，适配实际原生运行器**；不整体导入。|
|NeMo 2.7.3 Auto Configurator，`1d4ee423806d461f9146ae982f9da8eb32495ae7`；Apache2.0。[nemo-runner][nemo-license]|**候选生成＋短训比较流程**。`AutoConfigurator(...)`→`generate_configs(...)`→逐候选调用 NeMo `Partial(pretrain,...)`→`get_results(...)`；示例 `auto_config.py --run_number ...` 与 `--get_results`。不是 Agent，也不是 Bridge 的 Auto Recipe。|源码限定 40／80GB 档和 A100／H100 假设，GPT 序列长度为 2K／4K／8K／16K／32K；CP／EP 不支持 `"auto"`，须显式列表，finetune 的 TP／PP 也须显式给定。候选可能 OOM；生成时 `resume=None`、不保存 last，不能当恢复训练器。NeMo 当前主仓库已转为 Speech，2.7.3 是 split 前最后版本；这个遗留 API 不等于当前 Bridge 兼容层。[nemo-example][nemo-readme]|**借鉴完整流程，暂缓直接依赖**。生成／比较方法可复用，先适配现有 Bridge 配方和原训练所有者。|
|Microsoft nnScaler `d4aaaeb12db80c75e979d976a7147e6fb669607d`，`0.8`；MIT。[nn-src][nn-license]|**自动并行编译／搜索工具**。`nnscaler.parallelize(module, dummy_forward_args, pas_policy="autodist", compute_config=...)`；`AutoDistConfig` 控制 mesh、memory、pipeline、DP／ILP solver、profile 和 plan 保存；也有 Trainer／`nnscaler-train`。[nn-api][nn-config][nn-search]|依赖文件为 torch≥2.0,≤2.6；README 仍写 torch<2.4、Python<3.11，存在文档差异，须另建兼容矩阵。搜索生成 PyTorch 程序，不生成可直接交给 Bridge 的 TP／PP 配方。需要真实 GPU／网络 profile；官方 quickstart 甚至展示缺通信 profile 时回退 MI200 数据的日志，不能把这种预测用作目标集群证据。计划可 `save_plan_path`／`load_plan_path`；恢复时须匹配生成代码和初始化非持久 buffer。[nn-deps][nn-api]|**借鉴搜索合同；有独立 PyTorch 编译需求时适配**，不侵入现有训练框架。|
|Microsoft `SuperScaler` 仓库当前 HEAD `fa80ad02c1dc855ca85b591fb689a09598d2cb7e`，README 实为 **Aceso Artifact**；MIT。[aceso-src][aceso-license]|**profile→search→train 完整研究流程**。`scripts/aceso_gpt_search.sh small` 调搜索器，输出 JSON config；训练器以 `--flexpipe-config CONFIG_FILE` 消费，存在 GPT／T5／ResNet 的配套脚本。[aceso-search]|小规模全链需要4 GPU，论文 artifact 的完整环境是4节点×8 V100 32GB、CUDA11.6／torch1.12／Apex／patched Megatron-LM。已有 profile 数据时搜索可在 CPU 做，但不代表新硬件性能验证。邻接 GPU 默认被视为高带宽相邻，复杂拓扑须调整；未核到专用 CP／EP／FSDP搜索、通用恢复 API 或 MCP。|**借鉴原生流程及预测校准方法，暂缓 runtime 接入**；旧训练栈不与当前 Bridge 原样拼接。|
|Alpa `b8078a9f75cb4c90cabb4550ee48c99ef394e209`；Apache2.0。[alpa-src][alpa-license]|**自动并行系统／编译工具**。JAX `@alpa.parallelize`，自动选择算子内／算子间和 pipeline 并行；不是 Agent。|官方 README 明确“不再积极维护，作为研究 artifact”。安装说明依赖定制 jaxlib0.3.22、旧 CUDA wheel；主 API 面是 JAX，PyTorch 前端实验性。[alpa-install] README 说核心算法合入 XLA，但其给定 `xla/hlo/experimental/auto_sharding` 路径在本次固定 XLA HEAD 返回404，未核实新路径，不把此链接当当前可用实现。|**借鉴分层搜索设计，暂缓直接接入**。|
|Huawei MindSpore `v2.7.0`，`auto_parallel.py` SHA256=`12f76d55013895bcbcba97f1fcc41f1b46593c162c1d963c0141879824c87630`；Apache2.0。[ms-api][ms-source][ms-license]|**自动布局框架接口**。`AutoParallel(network, parallel_mode="recursive_programming")` 为自动策略；`sharding_propagation` 从标注传播；`semi_auto` 为手动策略。`pipeline(...)`、operator／parameter strategy save/load 接口存在。|此版本 API 声明支持平台为 **Ascend**，不能从旧 `_auto_parallel_context` 的 GPU 能力外推这个新接口。传播模式不支持 dynamic shapes；functional API 不支持 data sinking。strategy 文件不是模型／优化器／数据位置的完整恢复快照。官方 API 指向 Gitee v2.7.0；GitHub mirror 本次 HEAD 缺新文件，不能混用作源码证据。此处仅核固定版本，不宣称 v2.7.0 是当前最新版本或完成 PanGu 全系统复现。|**借鉴／按 Ascend 需求适配独立 backend**，不称为并行设计 Agent，也不改写成 Bridge 插件。|

[DeepSpeed Autotuning][ds-tuning] 确有 `deepspeed --autotuning tune/run ...`，但官方说明重点是 ZeRO、microbatch 和相关配置，且内部 forward＋backward＋step 计时小于完整训练 step 时间。本次只作为搜索范围与测量口径的反例，未固定其源码版本，不列为已准入候选；框架配置搜索由后续方向研究覆盖。

## 论文回溯、源码反证与不能照抄的结论

- [nnScaler OSDI’24 原论文][nn-paper] 对应官方仓库及 AutoDist 实现，核心是约束下的 op-trans／op-assign／op-order 搜索空间，不是枚举几个 Megatron degree。论文报告的最高3.5×属于特定 DNN／约束和基线，不能转为本文 MoE 或目标集群的预期收益；本次未复现。
- [Alpa OSDI’22 论文][alpa-paper] 对应公开 Alpa 仓库，算子内切分与 pipeline 分层规划可供借鉴；论文存在不代表旧 JAX runtime 适合当前训练栈。Aceso 的正确论文是 **Aceso: Efficient Parallel DNN Training through Iterative Bottleneck Alleviation**，EuroSys’24，DOI [10.1145/3627703.3629554][aceso-paper]；标题／出版信息由 publisher 注册元数据核到，ACM全文403，本报告仅据官方 artifact 核流程，不引用论文性能数字。
- Bridge parallelism Skill 把 arXiv:2504.14960 标成 “Pangu Ultra MoE”，这是**来源名称错误**。该 ID 的当前 [v3 原文][folding-paper] 是 **MoE Parallel Folding: Heterogeneous Parallelism Mappings for Efficient Large-Scale MoE Model Training with Megatron Core**，公开实现指向 Megatron Core；v1 也不是上述 PanGu 标题。不能把这条引用作为华为方案的出处。实际 dense／expert mesh 解耦可在本次固定 MCore 的 `initialize_model_parallel` 核对。[mcore-state]
- [Ulysses 论文][ulysses-paper] 的 a2a head／sequence 转置和 [Ring Attention 论文][ring-paper] 的 ring 机制可解释 HCP 的组成；它们不是 NVIDIA Bridge 的专用 Agent，也不自动证明当前 HCP 集成正确。Bridge 的版本验证、进程组传递和 TE kernel 支持必须单独检查。[hcp-doc][bridge-init]

**最小卡数必须由合法 mesh 求得。** 对普通、无额外 GTP／自定义 layout 的 MCore 配置，令 `W=world_size`，源码要求 `W % (TP*PP*CP)==0`，以及 `W % (ETP*EP*PP)==0`，并检查 dense／expert pipeline group 一致、rank ordering 相容。EP 不在 dense mesh 上再乘一次；合法候选至少满足：

```text
DP  = W / (TP * PP * CP)
EDP = W / (ETP * EP * PP)
W_min = PP * lcm(TP * CP, ETP * EP)  # 只是基础整除下界，仍须过模型／rank约束
```

Skill 的 `PP * max(TP*CP, EP*ETP)` 仅在两个 mesh 大小相互整除等条件下退化成立；常见二次幂布局满足这一点，不代表任意配置都成立。裸乘所有维度会多配卡，裸用 max 又可能配出不能初始化的布局。当前 dev pin 还出现 GTP rematerialization 等额外 layout，必须让其原生 validator 消费，不能把上式当万能求解器。[parallel-skill][mcore-state]

还有两处验证入口差异必须保留：FSDP Skill 提供的 `tests/functional_tests/training/test_megatron_fsdp.py` 在 Bridge 固定 SHA 返回404，目录核对也没有该文件，不能照搬为“已有可运行验收”；HCP Skill 自己说明缺少专用 Bridge 端到端测试。可先复用配置约束，但运行接入前必须补定准确测试入口和自己的实际结果。[fsdp-skill][bridge-tests][hcp-skill]

## 对照测量、正确性和恢复的实际边界

|对象|已公开的一手证据|对 Ergora 验收的含义|
|---|---|---|
|Dynamic CP|官方八GB200／NVL72、NeMo26.06.01、MCore dev＋指定修复、随机初始化、4,000条 SWE-Rebench、12steps丢前4的结果：dynamic 88s，static CP4 83s，均108GB peak；九成样本被截到32K，几乎都需全CP4。selective recompute 75s只活4步，随后 NCCL OOM；loader workers 从16降2则254s。[dynamic-readme]|这是适用性与失败证据。不能把75s当获胜配置，也不能从局部 scheduler 示范推断训练加速。需记录长度直方图、每组实际使用率、新communicator开销、data wait及每rank reserved／allocated memory；有足够短序列才值得试。该数据没有训练收敛证明。|
|Vision DP over CP|Skill 给出16GPU、固定 batch／并行配置下三个数据集的A/B：step约降4%–5%，peak约降5%–11%，但未给可泛化的卡型／镜像完整矩阵。当前源码有两rank、小模型、`eval()`＋`no_grad()` 的encoder输出比较，图像数1／2／3，最大绝对差<1e-2。[vision-skill][vision-test]|可作候选证据，不能称完整训练梯度已验。必须另验训练 backward／loss、真实多图／视频数据与所有rank峰值；按图像**数量**分片会使末rank因图像大小／余数过热。placeholder路径无多节点训练证据，CP8未覆盖。|
|MoE硬件配方|Skill 明示平台行只是搜索种子。Qwen3 30B的299.352 TFLOPS/GPU 是多个设置共同调整后的16H100 canonical结果；早期单变量overlap A/B为244.039→287.305，不能把后者／前者混成因果证据。配方含force balance。[hardware-skill]|R4保留完整映射和资源；R3解释overlap。用自然routing另做训练验收，precision／GBS／routing改变应立新实验。MFU和TFLOPS不能跨精度、模型或框架直接排名。|
|NeMo Auto Configurator／nnScaler／Aceso|NeMo结果器只要求至少10个timing样本、丢首个后求平均并排序；没有替代loss／梯度正确性门禁。nnScaler cost model／Aceso profile库生成预测，再由训练验证；CPU搜索成功不是GPU收益。[nemo-results][nn-search][aceso-src]|分别保存预测与测量。profile、编译、通信组和cache的版本必须绑定候选；新硬件／内核／拓扑需重新校准。单次模型估计只用来筛候选。|
|FSDP及布局变更后恢复|官方文档说 `fsdp_dtensor` 采用DTensor／DCP并支持分片重映射；与非FSDP的`torch_dist`／zarr不能直接互载。源码还单独处理优化器、RNG、dataloader及旧metadata，不是只载权重。[fsdp-doc][bridge-ckpt]|“可重分片权重”不等于“完全一致续训”。接受前分别验同布局恢复、支持的目标布局转换、optimizer状态／step／LR、数据成员和顺序、RNG、processed tokens。布局变更使部分RNG无法原样恢复时，须显式记录；不能用加载成功宣称exact resume。本次未执行恢复。|

所有收益均为作者记录，本文没有统一硬件对照实验。三步 finite-loss smoke、生成计划成功、模型能载入都不构成完整训练正确性。外部验收至少要覆盖固定小批次的输出／loss、梯度或若干 optimizer update、CP 的全mask SFT rank、MoE路由／token不丢失，以及小规模恢复后的状态一致；容差要随精度和浮点归约顺序事先冻结。[recipe-skill][bridge-config]

## 最小可引用子模板合同

建议能力名为“并行与配方实验”，允许架构设计或训练优化流程引用。**Agent 负责假设和解释，原生工具负责搜索／训练，原有正式运行所有者负责状态、预算、审批和未知恢复。** 不在方向子模板另建训练调度／实验账本；下面是建议合同，尚未实现。

|合同面|最小要求|
|---|---|
|输入|精确模型／权重／tokenizer和数据revision，目标pretrain／SFT／PEFT，sequence与图像／视频长度分布，固定全局batch成员／顺序／token预算、optimizer／LR／精度／routing语义；当前可跑baseline及原件；每节点卡型／显存、NVLink域、节点／网络拓扑、CPU／存储；代码SHA、MCore main或dev pin、镜像digest及许可；允许变动的执行字段，GPU-hours／候选数／wall-time／并发上限。父模板的资料、Skill和权限完整继承。|
|能力准入|分别声明 `recommend_only`、`generate_configs`、`profile`、`launch_training`、`read_status`、`collect_metrics`、`checkpoint_resume` 是否可用及原生入口。没有GPU或集群授权时只能给提案；不能用CPU搜索、mock run或静态recipe表冒称已测训练。无兼容框架时显式unsupported。|
|约束检查|检查两mesh整除、rank／PP group一致、专家数／KV heads／SP／CP／序列和batch规则；HCP／dynamic CP的进程组路径；FSDP checkpoint格式；vision分片实际生效；精确backend／kernel支持。先原生validator，再最小初始化／正确性probe；失败保留原候选原因。|
|候选生成|优先最近library recipe＋少量合法布局，记录所有覆盖字段和理由。原生nnScaler／Aceso等完整搜索若被选中，保留其内部算法和plan，外层只调用入口／读结果。先保证完整step能运行，再用all-rank显存和关键路径决定降低TP、调整PP／CP／EP或MBS；不按单张卡或rank0估计放满。|
|执行和比较|候选精确绑定baseline、配置、数据和栈；至少把screening、单变量机制A/B、完整获胜组合验收分开。保持有效全局更新语义；预热后重复／配对测端到端tokens/s、step时间分布、所有rank峰值和资源成本，记录compile、data wait、checkpoint／eval与失败。mock／forced-balance benchmark不能替代自然routing和真实数据验收。|
|输出|`recommendation`（来源／版本／适用范围）、`candidate_manifest`（mesh、stage／rank映射、覆写字段、native plan摘要）、`experiment_evidence`（native job/run ID、完整命令／退出与原始日志、预测和实测分开、正确性／恢复／性能结果）、`decision`（keep／reject／no_gain／unsupported／failed／unknown及理由）。这些概念应映射到既有candidate与证据结构，不能创建第二套正式状态。|
|恢复|launch前固化候选及attempt、获得后保存native job ID；超时／断连先查原job和原产物，状态不明保留unknown，禁止盲目提交新训练。OOM、编译失败、无收益与超预算分别记录；原生exit0／最佳预测不自动晋升。checkpoint／layout转换只走已经验证的后端能力，未支持即拒绝；不静默换库／换模型／换precision重试。|
|独立出口|方向Agent不能修改reference、容差和胜出门槛；由可复用的独立测量／正确性审查角色核候选、baseline、实际生效路径和恢复证据。验证只授予这个固定候选；正式approval继续归原所有者。|

跨域边界应由产物表达，而不是按技术标签复制 Agent：架构设计提供层、attention／MoE结构和允许的语义变化；并行能力返回合法mesh与stage映射；通信能力返回传输／overlap兼容矩阵与trace；显存能力返回recompute／offload的峰值和时间代价；kernel／框架能力返回算子与编译支持；profile能力提供跨rank关键路径；集群恢复能力提供job与checkpoint恢复证据。一个可替换设计Agent可以同时消费这些信息，同一个测量／审查Agent也可以复用。[recipe-skill][nn-paper]

## 接入顺序与保留项

1. **先采用**精确配方／来源引用、语义与执行配置分离、mesh与资源约束、真实A/B及失败保留的合同。选择器先输出有限候选和可复现命令，资源不足明确拒绝，不要求整体引入NeMo。
2. **再适配**现有训练所有者的配置生成、原生启动／观察／产物消费能力；首个小流程可做library baseline的合法TP／PP／CP候选比较。没有这些真实消费者时，只能发布只读专家和流程提案。
3. **按确切瓶颈启用**FSDP、MoE／长上下文配方、指定Nemotron Omni视觉分片。先修准测试入口／版本差异，做自己的正确性和恢复验收。HCP与dynamic CP保持显式选择；当前反证不足以支持普遍默认。
4. **借鉴但暂缓直接运行接入**旧NeMo Auto Configurator、nnScaler、Aceso、Alpa及MindSpore异构backend，按实际PyTorch编译／Ascend任务再立独立适配片。它们提供可复用工具／搜索思想，不因此新增一个虚构Agent。

本次只写本报告和私有来源原件，没有修改产品、计划或模板，没有提交／推送。已核的108次公开GET包含86个成功原件和22次失败；失败含GitHub API403、文档／源码404、ACM403，均保留，后续成功没有覆盖原失败。公开引用使用稳定原URL，不包含Gitee重定向的临时签名。尚未证明任何候选在本机安装、GPU收益、完整训练收敛或异常恢复。

[index]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills-index.html
[parallel-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-parallelism-strategies/SKILL.md
[recipe-skill]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/nemo-mbridge-recipe-recommender/SKILL.html
[recipe-index]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/nemo-mbridge-recipe-recommender/references/recipe-index.html
[bridge-run]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/scripts/training/run_recipe.py
[bridge-harness]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/scripts/performance/setup_experiment.py
[bridge-src]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/tree/55694838ce73cd23b00ff95bd00512aefb963ce0
[bridge-license]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/LICENSE
[bridge-deps]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/pyproject.toml
[mcore-pins]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/scripts/switch_mcore.sh
[mcore-state]: https://github.com/NVIDIA/Megatron-LM/blob/f78809f6d9c88f8638ea7822966f35057a63fd5c/megatron/core/parallel_state.py
[mcore-license]: https://github.com/NVIDIA/Megatron-LM/blob/f78809f6d9c88f8638ea7822966f35057a63fd5c/LICENSE
[bridge-config]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/config.py
[bridge-init]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/initialize.py
[bridge-ckpt]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/training/checkpointing.py
[bridge-tests]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/tree/55694838ce73cd23b00ff95bd00512aefb963ce0/tests/functional_tests/training
[fsdp-doc]: https://docs.nvidia.com/nemo/megatron-bridge/latest/training/megatron-fsdp.html
[fsdp-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-megatron-fsdp/SKILL.md
[hcp-doc]: https://docs.nvidia.com/nemo/megatron-bridge/latest/training/hierarchical-context-parallel.html
[hcp-skill]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/nemo-mbridge-perf-hierarchical-context-parallel/SKILL.html
[dynamic-doc]: https://docs.nvidia.com/nemo/megatron-bridge/latest/training/dynamic-context-parallel.html
[dynamic-readme]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/examples/training_features/long_context/README.md
[vision-skill]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/nemo-mbridge-perf-vision-dp-over-cp/SKILL.html
[vision-model]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/src/megatron/bridge/models/nemotron_omni/modeling_nemotron_omni.py
[vision-test]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/tests/unit_tests/models/nemotron_omni/test_vision_dp_over_cp_distributed.py
[long-skill]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/nemo-mbridge-perf-moe-long-context/SKILL.html
[hardware-skill]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills/nemo-mbridge-perf-moe-hardware-configs/SKILL.html
[nemo-runner]: https://github.com/NVIDIA-NeMo/Speech/blob/1d4ee423806d461f9146ae982f9da8eb32495ae7/nemo/collections/llm/tools/auto_configurator/runner.py
[nemo-example]: https://github.com/NVIDIA-NeMo/Speech/blob/1d4ee423806d461f9146ae982f9da8eb32495ae7/examples/llm/auto_configurator/auto_config.py
[nemo-results]: https://github.com/NVIDIA-NeMo/Speech/blob/1d4ee423806d461f9146ae982f9da8eb32495ae7/nemo/collections/llm/tools/auto_configurator/core/calculate_performance.py
[nemo-readme]: https://github.com/NVIDIA-NeMo/Speech/blob/main/README.md
[nemo-license]: https://github.com/NVIDIA-NeMo/Speech/blob/1d4ee423806d461f9146ae982f9da8eb32495ae7/LICENSE
[nn-src]: https://github.com/microsoft/nnscaler/tree/d4aaaeb12db80c75e979d976a7147e6fb669607d
[nn-license]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/LICENSE
[nn-api]: https://nnscaler.readthedocs.io/en/latest/parallel_module.html
[nn-config]: https://nnscaler.readthedocs.io/en/latest/autodist/configuration.html
[nn-search]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/nnscaler/autodist/apis.py
[nn-deps]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/requirements.txt
[nn-paper]: https://www.usenix.org/conference/osdi24/presentation/lin-zhiqi
[aceso-src]: https://github.com/microsoft/SuperScaler/blob/fa80ad02c1dc855ca85b591fb689a09598d2cb7e/README.md
[aceso-license]: https://github.com/microsoft/SuperScaler/blob/fa80ad02c1dc855ca85b591fb689a09598d2cb7e/LICENSE.txt
[aceso-search]: https://github.com/microsoft/SuperScaler/blob/fa80ad02c1dc855ca85b591fb689a09598d2cb7e/search/aceso_search.py
[aceso-paper]: https://doi.org/10.1145/3627703.3629554
[alpa-src]: https://github.com/alpa-projects/alpa/blob/b8078a9f75cb4c90cabb4550ee48c99ef394e209/README.md
[alpa-license]: https://github.com/alpa-projects/alpa/blob/b8078a9f75cb4c90cabb4550ee48c99ef394e209/LICENSE
[alpa-install]: https://github.com/alpa-projects/alpa/blob/b8078a9f75cb4c90cabb4550ee48c99ef394e209/docs/install.rst
[alpa-paper]: https://arxiv.org/abs/2201.12023
[ms-api]: https://www.mindspore.cn/docs/en/r2.7.0/api_python/parallel/mindspore.parallel.auto_parallel.AutoParallel.html
[ms-source]: https://gitee.com/mindspore/mindspore/blob/v2.7.0/mindspore/python/mindspore/parallel/auto_parallel.py
[ms-license]: https://gitee.com/mindspore/mindspore/blob/v2.7.0/LICENSE
[folding-paper]: https://arxiv.org/abs/2504.14960v3
[ulysses-paper]: https://arxiv.org/abs/2309.14509
[ring-paper]: https://arxiv.org/abs/2310.01889
[ds-tuning]: https://www.deepspeed.ai/tutorials/autotuning/
