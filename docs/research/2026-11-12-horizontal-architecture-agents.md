# X1：跨域架构设计、联合搜索与候选整合

检索日期：2026-11-12。承接 [R1–R10 分类与职责](2026-11-12-optimization-taxonomy.md)，重点补核跨方向的控制、真实输入输出和整合边界；不再重复库和 profiler 目录。公开源码、官方说明和作者论文均为只读研究，未安装依赖、调用模型、运行 GPU／NPU、训练或复现收益。原件、来源时间、SHA256、获取失败及复用关系保存在私有 `.ergora/checks/specialist-template-refresh/research/horizontal-architecture/`。获取源码和读取入口不构成执行验证。

**建议采用一个可跨多方向的架构提案职责，按问题调用完整的原生优化流程；不引入一个宣称能统管全部领域的“全能优化 Agent”。** 本轮深核六组实现：ModelOpt 的 Minitron／Puzzletron、nnScaler、Aceso、Galvatron-2、Unity／FlexFlow、FT-Agent。前五组主要是确定性搜索／编译系统，FT-Agent 是真实多角色 LLM 闭环，但范围是文本微调。没有核到同时覆盖任意模型结构、现代 MoE mesh、kernel／精度、训练质量与集群恢复且可直接导入的通用系统。这是本轮公开可读范围内的判断，不是穷尽性不存在声明。

## 先区分三种架构

|架构|改变的对象|本轮证据与不可互借的结论|
|---|---|---|
|模型架构|层数、宽度、attention／FFN、专家和模态计算；可能改变函数和学习目标|Minitron／Puzzletron 搜索结构后还需蒸馏和任务质量评价。结构合法、参数少或近似评分高不能证明质量达标。[ModelOpt][modelopt-readme]|
|运行架构|保持声明训练目标下的 tensor／operator／stage 划分、mesh、放置、通信、重计算和调度|nnScaler、Aceso、Galvatron、Alpa／Unity 属于主要候选。它们常联合优化计算、显存和通信，但不是任意模型结构搜索器。[nn-api][aceso-search][galva-search][unity-code]|
|代码架构|模块边界、依赖、接口和状态所有者|由 [R10 重构研究](2026-11-12-refactoring-workflow-agents.md)接原六阶段开发。Aider architect 等名称不能作为神经网络／分布式运行优化的能力证据；新模型 bridge 的开发也须走此出口。|

一个专家可以同时理解这三层，但每次干预必须声明改哪一层、哪些训练语义保持、哪些证据失效。上游“model architecture”与项目“software architecture”不能合并成一个支持标签。

## 发现范围与为何收敛到六组

先复核 [R4 并行研究](2026-11-12-optimization-parallelism-agents.md)、[R5 显存研究](2026-11-12-optimization-memory-agents.md)、[R6 执行图研究](2026-11-12-optimization-execution-graph-agents.md)、[R9 模型研究](2026-11-12-optimization-model-recipe-agents.md)的固定来源，再由官方仓库和作者论文补查联合控制实现。选择依据是可核的全局目标、跨技术搜索空间、候选交接和原生消费者，不以 Agent 命名、厂商或榜单排序。

|发现组|本轮处理|原因|
|---|---|---|
|ModelOpt、nnScaler、Aceso|复用纵向原件并补读控制源码，列入深核|分别代表质量／结构约束、算子到 pipeline 的分层搜索、瓶颈驱动的跨资源局部搜索。|
|Galvatron-2|新增固定源码、许可、成本模型／搜索／训练／checkpoint 核对，列入深核|Profiler→Search Engine→Runtime 同属原生系统，逐层并行、重计算、通信／显存成本共同进入选择。|
|Unity／FlexFlow|从 R6 补核当前联合图搜索和映射源码，列入深核|图改写与并行化共同搜索，能直接说明“各方向独立最优”为什么不足。当前接口与原论文 artifact 须分开。|
|FT-Agent|复用 R9，补核实际 LLM 会话创建点，列入深核|真实提案／编码／运行／反馈闭环，可比较确定性搜索与 Agent 协作；必须揭示内部资料和权限继承缺口。|
|Alpa、DeepSpeed Autotuning、MindSpeed SmartSwap、Rockmate／OffMate|按 R4／R5 保留比较，未再扩成独立深核|Alpa 的层内／层间分层设计有价值但停止积极维护；其余分别偏框架配置或内存子问题，不等于全球架构 Agent。|
|FlexSP、AutoML-Agent、Aider architect|保留边界，未扩展导入建议|FlexSP 是变长序列／动态 SP 的特定联合系统；AutoML-Agent 的现有任务／许可与 Bridge 目标不匹配；Aider 是代码架构协作。不能借名称把它们升级为本轮通用系统。[FlexSP][flexsp-paper]；其余见 R9／R10。|

覆盖训练与少量部署约束，不覆盖全部云资源调度、服务 SLO／多租户推理、所有 NAS／AutoML 或闭源平台。本轮未核到可复用的全局系统 MCP；不能把 HTTP 服务、Python API 或 CLI 统称为 MCP。搜索连接器及 GitHub REST 先前已不可用，本轮没有重试凭据或绕过限制；新增来源用公开 raw、仓库页面、codeload 和论文读取。两次公开 Git `ls-remote HEAD` 超时保持原样，Galvatron 身份来自官方页面 `currentOid` 与该完整 SHA 的成功源码归档，不称成功 Git Ref 核验。

## 全局控制与局部候选实际由谁负责

下表是上游实现的控制关系；“独立验收缺口”不表示上游没有测试，而是搜索返回值不能代替 Ergora 的最终候选批准。

|系统|谁定义全局约束|谁生成局部候选、怎样选择方向|跨域组合与独立验收缺口|
|---|---|---|---|
|Minitron／Puzzletron|调用者固定 teacher／模型、允许结构、校准数据、参数／memory／latency 目标；MIP 或 NAS 搜索器在该范围内求解|Minitron 用重要性与 top-K 子网评分；Puzzletron 构 replacement library、各块分数和统计，再由 MIP 选各层组合|结构、硬件友好宽度、质量 proxy 与资源预算共决策。求解约束和局部分数不保证蒸馏后排序／整模 latency；需重新蒸馏、质量与部署验收。[minitron-search][puzzle-plugin][modelopt-readme]|
|nnScaler AutoDist|调用者提供 graph、mesh、memory、指定 recompute modules／pipeline pivots、partition constraints 和 profile|SPMD solver 为局部子图求切分计划，pipeline solver 联合阶段边界／资源／成本；`parallelize_graph` 按选中 plan 改图并生成程序|共享参数、跨 stage tensor split 和重计算进入同一编译过程；不是把几份独立 TP／PP 建议拼接。计划的 `e2e_time` 是预测；实际数值、质量和端到端测量由消费者另验。[nn-config][nn-spmd][nn-pipeline][nn-api]|
|Aceso|CLI 固定 GPU 数、全局 batch、显存、stage 范围、profile 和试次／时间预算|`get_target_stage` 先处理超显存，否则按瓶颈时间选 stage；policy 按计算、通信、重计算成本比例排列动作；primitives 移算子、调 TP／DP／MBS 等|每个动作后重新预测全局时间／memory、更新受影响 stage 的 recompute；multi-hop 允许经过中间候选再解除瓶颈。搜索不是多名 LLM 专家投票；仍需配套训练器实测和独立语义／恢复验收。[aceso-policy][aceso-prims][aceso-search]|
|Galvatron-2|YAML／schema 固定模型、节点／GPU、每卡 memory、精度、GBS／chunk 范围、允许的并行维度和 profile|生成各层策略；外层枚举 batch／chunk／PP／TP-SP 组合，DP 在 memory 下优化层内和层间代价，再按预测吞吐选 JSON|重计算、分片、通信 overlap 系数、embedding／LM head 和持久 buffer 共同计成本。不能由“逐层最优”替代整模运行，改变 GBS 也不能再称同训练目标的纯执行优化。[galva-entry][galva-search][galva-dp]|
|Unity／FlexFlow|调用者提供 PCG、设备规格、cost estimator、substitution set、search config|在 unified parallel computation graph 上应用图替换，候选图再求 machine mapping；带去重的优先队列、budget、alpha 和 max ops 控制扩展|图代数变化和计算／通信映射共用一个成本评价，能探索先局部变差、再全局变好的组合。当前所核入口用 `RuntimeOnlyCostEstimator`，不能从名字推导完整显存／质量门禁。[unity-code][unity-subst]|
|FT-Agent|用户／benchmark adapter 固定基座、任务和允许资源；scenario 准备数据、环境和 baseline|提案模型依据历史选择任务／数据／训练配置假设，CoSTEER 分别生成数据代码与 LLaMA-Factory 配置；runner 执行、OpenCompass 评价、feedback 反馈 trace|`feedback`／`record` 串行保护 trace 一致性；它可以多项干预，但没有自然获得因果归因。没有任意 mesh／模型结构／Bridge 转换优化能力，也没有替外层冻结独立 test／验收门槛。[ft-proposal][ft-coder][ft-loop][ft-timer]|

### 1. ModelOpt：结构搜索与运行映射要有明确分界

固定 NVIDIA Model Optimizer `0.48.0`／`e2f328a19de789e73b91aca2908042388cf6d496`，Apache-2.0。[许可][modelopt-license]。Minitron 的实际入口为 `modelopt.torch.prune.prune(..., mode="mcore_minitron", constraints=..., config=...)`，Bridge 示例为 `prune_minitron.py`→`distill.py`→导出／评价；Puzzletron 是 YAML＋`torchrun examples/puzzletron/main.py --config ...`，支持 `--mip-only`。[剪枝实现][minitron-code][minitron-search]；[Puzzletron][puzzle-main][modelopt-readme]。

跨域价值在于**模型结构与硬件成本共决策**，不是替运行框架选择全部 mesh。Minitron 的示例剪枝路径明确要求仅 PP、TP／ETP=1；其 `weights+KV-cache` memory 约束是估算，不含完整训练状态和运行峰值。Puzzletron 的硬件友好 FFN 候选宽度、attention op／noop、分块评分和 runtime 统计进入全局组合；文档自身指出子块 runtime 非线性叠加，target 5 秒可得到整模 5.4 秒，必须对最后产物实测。[minitron-code][modelopt-readme]。

结构变更后须使旧并行计划、profile、编译图、kernel 形状和质量证据失效。Minitron 候选的 proxy 排名可能在短蒸馏后改变；Puzzletron 异构模型部署依赖教程指定的 AnyModel／vLLM fork，不能声称可直接交原版 vLLM 或 Bridge 任意 builder。代码许可不授予模型／数据使用权。**优先有条件适配 Minitron 完整子流程；Puzzletron 借鉴并按部署消费者适配，暂缓默认接入。** 细节与模态边界以 R9 为准。

### 2. nnScaler：从同一图求并行计划，保留编译所有者

固定 `d4aaaeb12db80c75e979d976a7147e6fb669607d`，源码 `0.8`、MIT。[许可][nn-license]。接口为 `nnscaler.parallelize(module, dummy_forward_args, pas_policy="autodist", compute_config=...)`，AutoDistConfig 定义 mesh、memory、ZeRO、指定重计算模块、pipeline、solver 和 profile。它生成可运行的 PyTorch 程序，**不是生成一份能直接导入 Bridge 的并行配方**；接口／依赖范围已由 R4 核定。[版本／依赖][nn-readme][nn-deps]。

本轮补核到三个关键约束：当前 AutoDist 仅支持 ZeRO stage 0／1、pipeline scheduler 必须为 `1f1b`，开启 pipeline 时非 DP solver 会被改为 DP；`recompute_modules` 是调用者指定的模块集合，不能宣传为任意 rematerialization 联合最优搜索。编译器加载或生成 `PipelineSearchOutput`，重建 recompute groups、stage 和 tensor partition；共享参数跨 stage 会插入 multiref 以处理梯度同步。[nn-config][nn-api]。

因此单体架构专家适合提供 pivot／mesh／可变范围和解释候选；完整搜索／编译留在 nnScaler 原生流程。`topk`、搜索进程数和 profile 并行控制搜索规模，不是 GPU-hours 或所有后代进程的硬预算。**借鉴分层约束与计划合同；仅在确有独立 PyTorch 编译消费者时适配完整子流程，暂缓为当前 Bridge 迁移框架。**

### 3. Aceso：最值得借鉴的是“资源冲突→动作→全局复算”

固定官方 `microsoft/SuperScaler` 的 `fa80ad02c1dc855ca85b591fb689a09598d2cb7e`，README 实为 Aceso Artifact，MIT；不把仓库名称当另一套已核 SuperScaler 产品。真实流程为 profile→`scripts/aceso_gpt_search.sh small`→JSON→训练器 `--flexpipe-config CONFIG_FILE`。artifact 全环境是 4 节点×8 V100 32GB、CUDA11.6／torch1.12／Apex／patched Megatron，小规模全链要求 4 GPU。[artifact][aceso-readme][aceso-license]。

`AcesoPrim` 给动作标注 time／memory／devices／workloads／efficiency／comm 的资源效应；policy 遇超显存先选减 memory 动作，再按瓶颈成本选通信、计算或重计算方向；动作迁移会更新两侧 stage 的 recompute，所有候选以最大 stage 时间和显存可行性重新评价。保存 visited／unexplored 候选并作 multi-hop，是系统性搜索；不能照抄“先让通信 Agent 优化，再让显存 Agent 优化”的覆盖式修改。[aceso-policy][aceso-prims][aceso-search]。

这些效应是 policy／成本模型的假设，真实 overlap 与新 kernel 会使预测失效；不是安全性证明。固定论文为 EuroSys’24 **Aceso: Efficient Parallel DNN Training through Iterative Bottleneck Alleviation**，本轮沿 R4 仅用出版信息和 artifact，不借未读到的 ACM 全文性能数字。[论文身份][aceso-paper]。**借鉴动作影响、瓶颈选择和全局复算，暂缓旧 runtime 接入。**

### 4. Galvatron-2：新增的完整联合运行系统候选

固定官方 `PKU-DAIR/Hetu-Galvatron` 的 `cea12ffb146a220643c8f99f9cb84294755d29f8`，`setup.py` 自报 `2.4.1`、Python≥3.8，Apache-2.0；未宣称该 SHA 已通过本机安装／发布验收。README 写 torch≥2.1.0，setup 写 torch≥2.0.1 并 pin `transformers==4.49.0`，还编译 `galvatron_dp_core`；须在自己的环境固定完整兼容栈。[源码][galva-readme][galva-setup][galva-license]。

原生步骤是 `profile_hardware`（含 nccl-tests、MPI／hostfile）和模型 computation／memory profile→模型 `search_dist.py <config.yaml> [overrides...]`→训练的 `galvatron_config_path` JSON。当前 `search_dist.py` 已使用 Hydra／嵌套 schema；旧 README 的裸 flag 说明不能代替当前入口。所核策略生成代码包含 PP、TP 或 SP、CP、DP type、checkpoint，schema默认 `disable_cp=1`；这是比 README“五维”表更具体的源码证据，**不据此宣称 EP、任意 MoE 或所有 CP 组合已经运行成功**。[galva-entry][galva-schema][galva-search][galva-models]。

DP 显式输入层内／层间代价和显存，并考虑持久 all-gather buffer、embedding／LM head、pipeline 成本；模型／硬件 profile 也包含 overlap coefficient。搜索仍是预测器，`max_throughput = gbsz / time_cost` 不会自动检查真实 loss、质量或最终通信竞争。固定训练目标时应冻结 `settle_bsz` 和数据成员，不允许以扩大 GBS 获得更高预测吞吐后沿用原质量实验。[galva-search][galva-dp]。

仓库有 loss 曲线对齐脚本，是有价值的验收入口，但没有由脚本存在获得固定质量阈值／实际通过。checkpoint 也不能泛化：Llama 路径保存配置、scheduler、权重和每 rank optimizer；保存端明确不支持 DDP，GPT 分布式加载显式抛 `NotImplementedError`。本轮未核到这些路径完整持久化／恢复 RNG 和 data cursor 的证据。[对齐][galva-alignment]；[Llama][galva-checkpoint]；[GPT][galva-gpt-checkpoint]。**借鉴联合搜索，并在有该 runtime 的目标消费者时适配完整子流程；不把 JSON 翻译成 Bridge 配方或立即替换训练框架。**

README 的 Related Publications 同时列 Galvatron 与 FlexSP；后者 arXiv:2412.01523 是长尾变长序列／动态 SP 工作，不能作为当前 Galvatron-2 全部能力或收益的论文。Galvatron 原始论文是 VLDB 2022／arXiv:2211.13878；其作者结果也不能直接授予本次 2.4.1 源码或现代硬件。[galva-paper][flexsp-paper]。

### 5. Unity／FlexFlow：联合图搜索真实存在，当前稳定调用面仍需验

固定 FlexFlow Train `1c534e463395d2aebee4554e2e5b5ca9e8fa8b7d`、Apache-2.0。OSDI’22 Unity 把代数变换和并行化共同表达为 PCG substitutions，再分层搜索；这是跨 kernel／图／通信／映射设计的重要证据。[论文][unity-paper]；[许可][unity-license]。

补核当前源码的 `optimize_with_unity_algorithm(pcg, cost_estimator, resources, search_config, substitutions)`：先为候选图求 series-parallel decomposition 与最优 machine mapping，再在去重优先队列中应用替换并复算；`budget`、`alpha` 和 `max_num_ops` 约束搜索，输出 `SearchResult{pcg, machine_mapping}`。替换集合包含分片／复制／规约与 linear-activation fusion 等。[unity-code][unity-subst]。

不能把论文的 theorem prover 扩成对当前全部改写、IEEE 浮点、训练梯度和质量的证明；也不能从当前 `RuntimeOnlyCostEstimator` 接口推导完整 memory 约束。当前 README 的旧 Python／`--search-budget`／export-strategy 示例位于注释块，结合 R6 已核状态，本文只把 C++ 入口作为可读实现证据，未验证稳定 CLI／Python 闭环。**借鉴统一搜索空间与每次重求映射，暂缓当前框架迁移及整体子模板准入。**

### 6. FT-Agent：保留内部闭环，但逐会话继承是硬缺口

固定 RD-Agent `484776c211e4fbbeef03e0ec00d6bbee7362a4f4`、MIT。原生 `rdagent llm_finetune --base-model ... --benchmark ... --loop-n ... --timeout ...` 和 `--path` 恢复会话已由 R9 核到。它是文本 SFT／LoRA 流程，不是 NAS，也不输出 Bridge mesh／转换实现；自动选择基座在入口断言尚不支持。[入口／许可][ft-entry][ft-license]。

本轮补核到提案、数据代码生成、微调配置生成和反馈分别用 `APIBackend` 创建消息／chat session：提案依赖 scenario／history，coder 使用自身模板和 workspace／feedback，feedback 另建请求。**外层 prompt 或一份场景描述不证明完整祖先 Skill／上下文已进入每个内部会话。** 数据脚本还可调用配置的 strong／weak／embedding 模型，judge 也是独立外部调用面；不是只检查 planner 一次就够。[ft-proposal][ft-coder][ft-feedback][ft-settings]。

适配前须识别全部内部模型／工具调用点，逐会话注入并记录全部结构祖先资料的精确版本、完整字节／可读资源及读取证据；对动态生成的新调用也必须走受父权限约束的实际消费者，不能通过 API 环境变量或 Docker 自行扩大能力。不能观测或保证这一点的上游版本应保持 unsupported／暂缓，不把“opaque native workflow”当继承豁免。**借鉴与有条件适配完整 SFT 子流程；当前运行接入暂缓，不能只摘一个 FT-Agent 名称装成普通叶子。**

## 原生预算、产物与恢复：不能交给一个“best”字符串

|系统|可复用的原生预算／产物|恢复能力与外层必须补足的边界|
|---|---|---|
|ModelOpt|结构候选范围、top-K／score cache、Puzzletron replacement／statistics、目标资源与 realized checkpoint|Minitron 分数缓存恢复假定 score_func／过滤条件不变；`--mip-only` 复用前置产物，不是任意步骤恢复。蒸馏 checkpoint 是另一层状态；已有输出后 exit0 不等于当前候选完成。搜索／KD／评价总 GPU-hours 及 teacher 成本由原所有者控制，不能只算 MIP。[minitron-search][minitron-code][puzzle-main]|
|nnScaler|`topk`、solver、search 进程／profile 并行、`save_plan_path`／`load_plan_path`，生成代码和 profile|load plan 会跳过重搜；必须绑定 graph／shape／mesh／软件／precision／profile 身份。plan 不是训练 checkpoint。所核配置没有统一 GPU／CPU／墙钟硬截止，原所有者需约束完整进程树和 aggregate 成本。[nn-config][nn-api]|
|Aceso|`--max-num-trials`、`--max-num-hops`、`--time-budget-per-trial`、`--time-budget-total`，top config JSON、趋势和 summary CSV|`run_search(num_stages)` 各自应用搜索预算；多进程按 stage 数各跑一份，不能把 `total` 当全部 profile／训练／并发 worker 的总成本。未核通用持久搜索恢复 API；config／日志不是 optimizer／data 恢复。[aceso-utils][aceso-search]|
|Galvatron|degree 上限、batch／chunk 范围、parallel_search／worker；硬件和模型 profile、逐组合日志、最佳 JSON|所核 schema 没有统一 wall-time／GPU-hours／候选执行硬限；搜索枚举和训练分开。计划缓存／JSON不是完整恢复状态；checkpoint 支持按模型／DP type 单列，未知时先核原作业。[galva-schema][galva-search][galva-checkpoint]|
|Unity|当前 C++ search budget／alpha／max ops、候选 PCG／machine mapping、内部映射 cache|迭代预算不限制 profile／编译／真实训练成本。所核入口返回最优结果，没有完整持久训练恢复或 quality gate；旧 import/export flag 不作为已验证当前接口。[unity-code][unity-readme]|
|FT-Agent|loop数、step边界 timeout、coder loop、训练／数据处理 timeout、trace／会话快照、代码／配置／checkpoint／评价|数据／环境／baseline准备发生在 `loop.run()` 前；默认 full timeout 100小时、benchmark timeout 0。timer在步骤边界检查，不是硬截止。`--path`恢复 Agent session且可能裁掉后续日志，不证明训练 optimizer／RNG／数据位置恢复。[ft-entry][ft-settings][ft-timer]|

没有 GPU 时，现成 profile 上的 CPU 求解只输出估计／提案；旧 profile、合成 trace、mock run 或静态图不能升级为目标硬件收益。所有流程必须保留超时、OOM、崩溃、无收益和成本；未知状态先查原 native job／进程／checkpoint，不盲重提。固定版本的工具、依赖、驱动／镜像、目标硬件／互连、模型权重／数据许可分别检查，项目根开源许可不覆盖外部模型／数据／服务。

## 技术方向 × 职责：多对多关系

下表是 **D0 的职责建议**，不是上游自带六名 Agent 或本项目新功能。单个架构专家可在多行工作，同一方向也有多个独立职责；生成器不能自己批准验收。nnScaler／Aceso／Galvatron 等名字指工具／原生系统，不等于必须各建一个 AgentDefinition。

|技术方向|全局目标／约束与方向选择|局部候选与实现|测量／执行证据|独立审查与整合|
|---|---|---|---|---|
|模型结构／配方|架构提案者固定模型族、允许语义变化、目标质量与部署资源|模型专家＋ModelOpt 构候选、短 KD；代码适配交 R10|真实 checkpoint／导出、目标 runtime 命中与整模质量|质量审查者冻结 validation／test；整合者使旧 shape／plan 证据失效|
|并行／mesh／分片|架构提案者联合硬件、batch、head／expert整除及状态容量|并行专家用原生 nnScaler／Galvatron／配方流程；共享结构可由同一架构专家判断|原训练 runner 的全 rank step、group／layout、profile|数值／恢复审查与硬件拓扑审查；不拼接不同 runtime 的 plan|
|显存／重计算／卸载|容量专家与架构提案者区分状态、激活、workspace、host资源|显存专家／原生联合 solver；与 pipeline／graph／通信专家协商|每 rank 峰值、host pinned／RSS、搬运与 optimizer证据|审查异步顺序、更新／RNG、恢复和端到端代价；组合后重测|
|通信／重叠／拓扑|架构提案者确认关键路径／争用，禁止只优化带宽|通信专家／自动 tuner／kernel专家，反馈 mesh与SM／buffer需求|microbench解释局部机制，正常完整训练评价最终收益|全 rank 前进性、数学／梯度、慢 rank／失败退出及真实 overlap|
|执行图／packing／调度|图与数据专家联合长度分布、batch语义和可捕获范围|graph／kernel专家；原生编译／调度系统；架构专家核可组合性|backend实际命中、有效token、完整step与graph pool|mask／loss权重、参数版本、随机状态、重放／恢复及质量|
|kernel／低精度|架构提案者定位价值与质量／容差边界|同一 kernel专家可覆盖布局、fusion、precision、通信子图；调用R1／R2流程|真实路径命中、导数／误差、整模瓶颈变化|数值／质量审查独立于实现；性能审查重核新关键路径和旧profile|
|硬件／集群运行|资源所有者冻结授权资源／时长，架构专家据拓扑选可行方向|运行专家调用已授权原生runner；不能由模型自行申请更多节点|原生job ID、拓扑、rank状态、成本／清理／checkpoint|原所有者处置unknown／恢复；资源审核不代替模型质量审查|
|代码架构／框架接入|模块／兼容性专家固定真实消费者与状态所有者|R10六阶段的mapper／implementer等精确定义|受影响代码、兼容检查、原candidate与实际构建|独立Spec／Standards与既有六阶段批准；不让优化子系统另建账本|

角色和专长可以复用现有 `roles`／`specialties` 的多值定义，但每个 role 仍须逐项通过后端准入。领域标签没有写、shell、network 或 GPU 授权效力。[AgentDefinition 实现](../../src/ergora/agent_definitions.py)；[格式](../../src/ergora/data/schemas/agent-definition-v1.json)。

## 干预冲突与组合后重验

|交互|一手证据／失效原因|架构整合者必须做的协商|
|---|---|---|
|结构剪枝 × mesh／kernel／部署|宽度、层数和 attention替换改变形状、整除、通信和 runtime支持；Puzzletron局部latency不可线性相加|结构候选先完成所需短KD／支持确认，再生成其自己的mesh／profile；不继承原模型质量、plan或速度结论。[minitron-code][modelopt-readme]|
|TP／PP／DP与重计算 × 通信／显存|Aceso迁移动作要同时更新两侧重计算；Galvatron把层间重分布和持久buffer纳入代价|方向专家返回配置diff、需要资源和影响项；只在同一baseline上比较，不让后交付的config覆盖前一份。组合必须重验所有rank峰值和完整step。[aceso-prims][galva-dp]|
|graph × packing／动态CP／offload|R6所核Bridge global-batch packing仍拒绝CUDA graphs、PP／VPP、Megatron FSDP等；capture可能保留内存池并限制hook／随机状态|先过具体版本的原生validator，不能由总架构Agent“批准绕过”；合法组合再验mask／loss、峰值、重放和恢复。[R6](2026-11-12-optimization-execution-graph-agents.md)|
|kernel／精度 × overlap／pipeline|算子时长／workspace／浮点归约变化会改变stage平衡、通信暴露和profile假设|kernel通过后重新profile受影响的stage／collective；冻结precision与容差，先测单项，再测组合。微基准收益不相加。[R1](2026-11-12-optimization-kernel-agents.md)、[R2](2026-11-12-optimization-quantization-agents.md)、[R3](2026-11-12-optimization-communication-agents.md)|
|GBS／数据顺序／长度策略 × 质量与归因|Galvatron可搜索GBS，FT-Agent可同时改数据和训练配置；动态packing改变微批和loss权重|把改变训练语义的方案立新质量实验；至少保留baseline、单干预与组合测量，在预算内作有区分力的消融，无法识别贡献时报告“组合收益／归因未定”。[galva-search][ft-proposal]|

不能要求任意两个完整系统直接协商：nnScaler生成代码、Galvatron／Aceso JSON和ModelOpt checkpoint有各自消费者。没有共同runtime时，只能在上层比较独立候选或显式开发转换接口；文件都是JSON并不证明可以相互合并。所有组合候选有新的精确内容身份，必须重新跑受影响的正确性、质量、端到端性能和恢复门禁；父级最终采用决定不可交给原生 `best`／LLM feedback。

作者收益只按条件阅读：Unity论文报告七种DNN、最多32节点／192GPU、最高3.6×和优化少于20分钟，是OSDI’22实验，不能转为当前源码／现代MoE收益。FT-Dojo的13任务中10项最佳来自单B200、12小时、Qwen2.5-7B-Instruct、至多2000训练样本和指定planner／judge，不能授予mesh或结构搜索。R4记录的dynamic CP样例为88秒对static CP4的83秒；R6记录的TE capture样例为42.00秒对eager41.36秒。后两例说明“更动态／已capture／更复杂”仍可能无收益。以上均为作者材料，未在Ergora复现。[unity-paper][ft-paper]；后两例的固定来源与完整条件见R4／R6。

## 一个可组合的最小流程

建议先形成“跨域架构提案→选定原生方向流程→独立整合验收”的消费者。以下是现有 task正文、具名交接产物和适配验收的内容要求，**不是新DSL、新调度器或第二实验账本**；目前 training preset仍只读提案。

1. **原所有者冻结全局合同。** 输入精确模型／权重／tokenizer／数据revision、目标训练／服务行为、可改变变量、精度／optimizer／GBS／有效token与顺序、独立reference／质量阈值、目标GPU／互连／host／存储、完整代码／镜像／依赖和许可；同时冻结GPU-hours、wall-time、候选数、并发、API／下载预算及恢复位置。缺项时输出缺项或提案，不伪造实测。
2. **一个架构提案叶接R7基线。** 使用全部祖先资料，先区分质量／容量／算力／通信／host／调度问题，给有限的可行方向、拒绝理由和预计影响，不启动任意未授权环境。单体专家可跨并行、显存、图和precision，独立测量者仍审查其证据。
3. **选择一个与实际消费者相容的原生子流程。** 当前Bridge工作负载先选R4–R6对应的原runner／配方；需要结构压缩时用ModelOpt剪枝→短KD→评价；已有nnScaler／Galvatron环境时调用其完整profile→search→train。保留上游内部solver／角色、原native ID和预算，不拆成外层另一套搜索状态机。FT-Agent未解决逐内部会话继承和权限前不准入。
4. **局部候选交接。** 必交原生命令／resolved config、输入与产物身份、profile／plan／生成代码／checkpoint、预测和实测分列、实际硬件与资源消耗、失败／无收益、原进程与恢复状态。建议者不能仅交一句“best”；原所有者仍负责超时、全组停止与unknown。
5. **整合者协调冲突。** 从同一可信baseline隔离各候选，列出变量、受影响资源／语义与互斥条件；先保留局部对照，再对可行组合重求计划／重profile并作为新候选验证。预算不足就保留未验／归因未定，不把若干单项pass传递成组合pass。
6. **独立三类验收后再晋升。** 正确性验前向／所需导数／多个optimizer update、mask／routing／随机状态和分布式前进性；质量验固定token预算和独立目标任务；性能用正常无profiler完整step／服务路径的配对重复，同时报告所有rank峰值、setup／搜索／训练／评价总成本。再用原checkpoint／job完成适用的恢复对照。只有匹配原candidate的证据才能交原owner approval。

完整流程输出是可审的候选及未验范围，不是自动“采用”。没有增益应正常交付无收益结果；无法执行时保留估计与明确前置条件。本文不预设新的运行状态枚举或把源系统trace迁成正式账本。

## 接入Ergora时必须守住的实际接口

|现状或候选|当前已核事实|最小适配／准入要求|
|---|---|---|
|单体跨域架构专家|现有AgentDefinition可有多个roles／specialties，训练包已有experiment-planner／performance等只读提案职责|先采用纵向知识和本报告冲突规则，复用精确Agent定义；只读输出通过既有叶调用。新增执行能力必须另有实际后端与消费者，不能靠角色名称开启。|
|结构／方向子模板|WorkflowDefinition能固定结构嵌套、控制依赖和数据端口；`run-input`只运行所选叶，不执行前驱或整个图|可定义／预览资料与交接；选中完整原生系统后，D1先在原所有者中补真实启动／状态／产物／停止／恢复／预算消费者，再称可运行。[Workflow手册](../WORKFLOW_DEFINITIONS.md)|
|正式StageDAG|`StageDAG`从选定子树派生数据／依赖，约束同一角色、显式all-join和端口；Temporal仍调度，原executor／receipt所有者建立执行权威|不能拿它直接运行混合LLM／solver／GPU训练／动态反馈的通用图，也不另建executor或第二run表。[源码](../../src/ergora/review_dags.py)|
|祖先资料／Skill／上下文|现有完整root→leaf装配及task-mcp固定scope list/read可供普通叶读取，容量不足拒绝|适配后的每个内部Agent会话也须完整获得并读取全部结构祖先资源；只外层加载、仅传摘要／URI、只纳入静态manifest均不满足。不能通过兄弟／数据边获得资源继承或权限提升。|
|原生确定性solver／训练进程|nnScaler／Aceso／Galvatron／ModelOpt本身没有需伪装成Agent的内部LLM会话|完整祖先资料进入实际外层Agent；solver／训练进程消费核定config／数据／限制和精确artifact。原生MPI、Docker、SSH／多节点能力不等于父模板已授权；实际进程树、GPU／CPU／磁盘／网络动作仍受父范围和原runner约束。|
|FT-Agent等内部Agent系统|源码分别创建多个chat session与动态代码API调用，未核Ergora完整祖先注入／逐会话读取／工具约束|有真实拦截／注入和记录消费者后才适配；逐会话核完整资源、模型身份、调用／工具权限与预算，失败显式拒绝。opaque调用或不可控后代保持缺口，不以保留原生流程为由豁免。[ft-proposal][ft-coder][ft-feedback]|
|外部MCP／工具继承|AgentDefinition v1／WorkflowDefinition v2的resources只有instructions／context／skill；现有task-mcp实际仅固定scope list/read，**没有任意外部MCP endpoint合同**|若选中系统需要外部工具，逐项列实际operation、provider／版本、资源和父权限，并实现实际客户端／后端准入与验证。不能只新增描述字段后称MCP已继承，也不能由资源累加扩大工具授权。[Agent schema](../../src/ergora/data/schemas/agent-definition-v1.json)、[Workflow schema](../../src/ergora/data/schemas/workflow-definition-v2.json)|

父子权限取所有结构祖先上限，所有资料完整性和可读性同时满足；要增加权限须共同修订相关父子精确版本，旧任务保持。继承的是可核资源和权限上限，不是“祖先曾经通过的收益”。现有六阶段继续作为正式开发／审查／批准与恢复所有者；完整可引用六阶段模板化的迁移由R10／D1承接。

## D0选择建议与未验范围

|对象|建议|足够小的下一消费者|
|---|---|---|
|跨域架构提案职责与冲突／重验合同|**采用知识合同，适配现有单体专家**|在既有训练提案叶接收真实baseline和冻结任务，输出有限跨域候选／拒绝组合及交接；不新增运行引擎。|
|Minitron剪枝→短KD→评价|**有条件适配完整子模板，结构分支优先**|已有授权模型／数据和对应Bridge／ModelOpt环境后，固定PP限制、资源、质量和checkpoint消费者；与R9共用，不重复建账。|
|nnScaler／Galvatron-2|**借鉴联合搜索；按实际目标runtime适配完整子流程**|只在真正需要该原生栈的任务立片，先验目标profile、真实模型／训练、产物身份和恢复；不为模板展示迁移当前Bridge。|
|Aceso／Unity／Alpa|**借鉴控制算法，暂缓runtime导入**|把资源影响、multi-hop、分层／联合图搜索用于候选设计；分别存在旧栈、当前调用面或维护／恢复缺口，不组合成一个虚构“全局solver”。|
|FT-Agent|**借鉴内部闭环；保留条件适配，暂缓实际接入**|文本SFT真实消费者＋逐内部会话完整继承＋父权限和总预算可执行约束＋独立test／质量门禁；只满足CLI可调用不够。|

本轮证明范围为公开固定实现、控制和接口的静态证据，以及对Ergora现状的源码核对；没有证明任何候选在当前环境可安装、可启动、所有内部资源被实际读取、权限可强制收窄、跨节点运行／停止／恢复成功、长期收敛或性能达标。PDF原件已保存，但本环境没有PDF解析器，因此Unity性能陈述仅来自其官方会议页；Galvatron原论文不借未解析正文引用收益。初始猜测路径404、一次无关arXiv发现、Unity PDF首次TLS失败和随后成功均保留；未取得或无关内容不作能力证据。下一步只由D0选中具体消费者后立D1／D2验收，本文没有安装依赖、运行模型／GPU、修改产品或更新计划。

[modelopt-readme]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/puzzletron/README.md
[modelopt-license]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/LICENSE
[minitron-code]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/megatron_bridge/prune_minitron.py
[minitron-search]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/modelopt/torch/prune/plugins/mcore_minitron.py
[puzzle-main]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/examples/puzzletron/main.py
[puzzle-plugin]: https://github.com/NVIDIA/Model-Optimizer/blob/e2f328a19de789e73b91aca2908042388cf6d496/modelopt/torch/puzzletron/puzzletron_nas_plugin.py
[nn-readme]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/README.md
[nn-license]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/LICENSE
[nn-deps]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/requirements.txt
[nn-config]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/nnscaler/autodist/autodist_config.py
[nn-api]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/nnscaler/autodist/apis.py
[nn-spmd]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/nnscaler/autodist/spmd_solver.py
[nn-pipeline]: https://github.com/microsoft/nnscaler/blob/d4aaaeb12db80c75e979d976a7147e6fb669607d/nnscaler/autodist/pipeline_solver.py
[aceso-readme]: https://github.com/microsoft/SuperScaler/blob/fa80ad02c1dc855ca85b591fb689a09598d2cb7e/README.md
[aceso-license]: https://github.com/microsoft/SuperScaler/blob/fa80ad02c1dc855ca85b591fb689a09598d2cb7e/LICENSE.txt
[aceso-search]: https://github.com/microsoft/SuperScaler/blob/fa80ad02c1dc855ca85b591fb689a09598d2cb7e/search/aceso_search.py
[aceso-policy]: https://github.com/microsoft/SuperScaler/blob/fa80ad02c1dc855ca85b591fb689a09598d2cb7e/search/aceso_policy.py
[aceso-prims]: https://github.com/microsoft/SuperScaler/blob/fa80ad02c1dc855ca85b591fb689a09598d2cb7e/search/aceso_prims.py
[aceso-utils]: https://github.com/microsoft/SuperScaler/blob/fa80ad02c1dc855ca85b591fb689a09598d2cb7e/search/aceso_utils.py
[aceso-paper]: https://doi.org/10.1145/3627703.3629554
[galva-readme]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/README.md
[galva-setup]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/setup.py
[galva-license]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/LICENSE
[galva-models]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/galvatron/models/README.md
[galva-entry]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/galvatron/models/gpt/search_dist.py
[galva-search]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/galvatron/core/search_engine/search_engine.py
[galva-schema]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/galvatron/core/search_engine/args_schema.py
[galva-dp]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/galvatron/core/search_engine/dynamic_programming.py
[galva-alignment]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/galvatron/scripts/accuracy_alignment/README.md
[galva-checkpoint]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/galvatron/core/runtime/checkpoint/llama_adapter.py
[galva-gpt-checkpoint]: https://github.com/PKU-DAIR/Hetu-Galvatron/blob/cea12ffb146a220643c8f99f9cb84294755d29f8/galvatron/core/runtime/checkpoint/gpt_adapter.py
[galva-paper]: https://www.vldb.org/pvldb/vol16/p470-miao.pdf
[flexsp-paper]: https://arxiv.org/html/2412.01523v1
[unity-paper]: https://www.usenix.org/conference/osdi22/presentation/unger
[unity-readme]: https://github.com/flexflow/flexflow-train/blob/1c534e463395d2aebee4554e2e5b5ca9e8fa8b7d/README.md
[unity-license]: https://github.com/flexflow/flexflow-train/blob/1c534e463395d2aebee4554e2e5b5ca9e8fa8b7d/LICENSE
[unity-code]: https://github.com/flexflow/flexflow-train/blob/1c534e463395d2aebee4554e2e5b5ca9e8fa8b7d/lib/compiler/src/compiler/unity_algorithm/unity_algorithm.cc
[unity-subst]: https://github.com/flexflow/flexflow-train/blob/1c534e463395d2aebee4554e2e5b5ca9e8fa8b7d/lib/substitutions/src/substitutions/unity_substitution_set.cc
[ft-entry]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/app/finetune/llm/loop.py
[ft-license]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/LICENSE
[ft-proposal]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/scenarios/finetune/proposal/proposal.py
[ft-coder]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/components/coder/finetune/__init__.py
[ft-feedback]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/scenarios/finetune/dev/feedback.py
[ft-loop]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/scenarios/finetune/loop.py
[ft-settings]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/app/finetune/llm/conf.py
[ft-timer]: https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/utils/workflow/loop.py
[ft-paper]: https://arxiv.org/html/2603.01712v1
