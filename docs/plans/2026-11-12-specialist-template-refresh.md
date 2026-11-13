# 专家模板重整：升级、方向研究与可复用流程

基线 `c38227747b002ba4137f65a4982de51ce247773e`，产品基线 `5ab6d350024de8515487d0bedb3b950be60ac867`。承接[总计划 F6/F8/F9/F10](2026-11-01-all-in-one.md)；当前进度见[交付记录](../delivery/2026-11-12-specialist-template-refresh.md)，具体目录对应和两条研究轴见[分类说明](../research/2026-11-12-optimization-taxonomy.md)。

## 原始目标与顺序

先升级本机日常安装并使用其 CLI／页面验证，再广泛调研、调整优化与重构模板的专家和流程。用户最初列举的量化、kernel、通信等是例子；按最新要求，研究方向以 [Megatron Bridge skills 索引](https://docs.nvidia.com/nemo/megatron-bridge/latest/skills-index.html)的实际职责继续细化，不固定为七类，也不要求整套导入。NVIDIA、华为等实现须回溯到具体官方项目、固定版本和原始论文，不凭厂商或自报排名认定效果。

单体 Agent 作为可替换专家；完整流程连同配套 Agent 作为可引用子模板，由该流程管理方向内的分工和交接。六阶段开发本身也应成为可复用流程模板。若现有运行接口不足以消费所选流程，先实现有真实消费者的最小组合／后端能力，再导入专家，不能用目录或静态图声称已经执行。

## 现状与约束

- 已有三个领域包：`repository-governance`、`large-change`、`training-optimization`。前两者映射正式六阶段的工作与审查；训练包目前是实验设计／profile／kernel／测量审查的只读提案组合，完整自动训练实验不是已完成能力。重构需求目前由治理／大型变更承担，需检查是否应提供明确的重构入口。
- 六阶段目前由固定参考合同及原 Temporal 所有者执行，不是可以直接在任意通用图中嵌套运行的节点。对外统一模板表达时保留既有 task／run／candidate／owner approval／unknown recovery，不建立第二调度或状态账本，不移动在途历史。
- 子模板权限不超过任一父级；资料、Skill 与上下文沿全部结构祖先累加并完整读取。追加权限需父子共同修订；资源不足明确拒绝。
- 配置／后端与模板解耦。逐实例选择实际支持的工具，优先执行／审查后端不同；不可用、同后端回退、仅静态或只读能力明确记录。
- 现有可信容器边界保持；无需宿主权限。新增硬件或外部服务只按真实可用范围验证，不把 CPU／合成响应当 GPU 收益。凭据保留外部变量引用。

## 可验收节点

|节点|可验收出口|状态|
|---|---|---|
|U0 前片交付|H1 精确候选自己的双 OS 必要 CI 与原独立终核完成；原失败／限流样本保持|已完成：5ab6d35自己的CI43170918496双OS七必要步骤及原评审精确终核通过|
|U1 日常安装升级|备份原安装身份／依赖与必要持久数据；升级标准 home 安装；CLI 实际加载新包，旧数据及项目保持，回退方法可用|完成：完整旧环境备份、离线升级、452产品文件／RECORD一致；新独立Spec／Standards开放0／0|
|U2 升级后旅程|新版 CLI、三组合导入／重复导入、完整 manifest／叶准入、页面及既有正式合同的必要操作；不误触业务写；记录当前支持和未验范围|完成：43命令／52检查／10HTTP通过，所属页面进程／端口清理；新独立原件重算通过|
|R1 kernel|NVIDIA KDA／ForgeKernel 及华为具名候选的一手实现、流程、硬件／语言、正确性与性能评价、许可和最小适配|[独立研究完成](../research/2026-11-12-optimization-kernel-agents.md)，已纳入D0|
|R2 低精度与压缩|训练／推理量化区分，校准／误差／质量门禁，附剪枝蒸馏适用性；区分 agent、搜索流程、库和 Skill|[量化独立研究完成](../research/2026-11-12-optimization-quantization-agents.md)，压缩与模型适配联动R9|
|R3 通信|collective／MoE／并行拓扑／重叠；真实自动搜索或 agent 实现与诊断工具分开，保留正确性与端到端证据|[独立研究完成](../research/2026-11-12-optimization-communication-agents.md)，已纳入D0|
|R4 并行策略与分片|TP／DP／PP／EP／CP、FSDP、分层与动态CP、vision DP over CP、MoE长上下文与硬件配方；搜索与推荐流程|[独立研究完成](../research/2026-11-12-optimization-parallelism-agents.md)，已纳入D0|
|R5 显存与卸载|memory tuning／estimator、activation recompute、CPU offload、优化器／激活／权重状态；容量与代价测量、自动搜索|[独立研究完成](../research/2026-11-12-optimization-memory-agents.md)，已纳入D0|
|R6 执行图与数据调度|CUDA Graphs、sequence packing、attention／fusion、microbatch重排／调度；编译和数据流优化，保持语义及质量|[独立研究完成](../research/2026-11-12-optimization-execution-graph-agents.md)，已纳入D0|
|R7 性能诊断与测量|Nsight Systems、PyTorch／跨层trace、分析陷阱与SQLite、memory snapshot；诊断agent／MCP、基线和可信测量|[独立研究完成](../research/2026-11-12-optimization-profiling-agents.md)，已纳入D0|
|R8 集群运行与恢复|multi-node Slurm／模板、resiliency／straggler／故障恢复；作业诊断agent和完整生命周期，权限与资源边界|[研究](../research/2026-11-12-optimization-cluster-agents.md)及[新独立事实／设计复核](../delivery/2026-11-12-cluster-research-review.md)通过，SP1／SP2关闭、开放0／0|
|R9 模型／配方与框架适配|recipe推荐、LLM／VLM bridge、模型验证卡、训练关联／数值一致、RL框架E2E；模型结构／剪枝蒸馏与框架选择|[独立研究完成](../research/2026-11-12-optimization-model-recipe-agents.md)，已纳入D0|
|R10 重构与开发流程|build／dependency／testing／CI／PR review相关成熟重构与治理agent；核六阶段模板及当前运行差距，给最小迁移方案|[独立研究完成](../research/2026-11-12-refactoring-workflow-agents.md)，已纳入D0|
|X1 横向架构与系统优化|在纵向研究后，核跨并行／显存／通信／图／硬件的架构设计与系统优化agent／流程；区分模型架构与代码架构|[研究完成](../research/2026-11-12-horizontal-architecture-agents.md)：六组系统／Galvatron补证，已入D0并完成独立审查|
|X2 横向kernel与端到端优化|在纵向研究后，核kernel agent覆盖精度、布局、融合、通信、图与服务集成的真实边界；复用R1证据并补跨域调用／交接|[研究完成](../research/2026-11-12-horizontal-kernel-agents.md)：四条真实流程、逐会话／最小接口缺口，已入D0并完成独立审查|
|X3 横向诊断／实验／评价协作|跨域瓶颈定位、候选搜索、预算／恢复、正确性／质量／性能独立审查、干预冲突与归因；成熟实现及论文|[研究完成](../research/2026-11-12-horizontal-experiment-agents.md)：AIDE／FT／Optuna／Tune及原评价owner，已入D0并完成独立审查|
|D0 汇总与优先级|按“技术方向×agent能力／职责”建多对多矩阵，逐项选择采用／适配／借鉴／暂缓；明确工具、子模板及自建边界与依赖顺序|[采用矩阵](../research/2026-11-12-specialist-adoption.md)及[新独立审查／补核](../delivery/2026-11-12-specialist-adoption-review.md)完成文档范围，Spec／Standards开放0／0|
|D1 最小运行补足|仅为选中真实流程补缺口，六阶段模板可引用且保留原所有者；模式、权限、输入输出、恢复和预算可验收|[D1a设计](2026-11-12-six-stage-native-consumer.md)完成；[B1完整材料](2026-11-12-six-stage-materials.md)本地出口／独立两轴通过，f394945已普通推送，精确原件及自己的CI43211896925双OS七必要步骤经原评审终核通过，B1精确交付终结。B2a已精确交付；B2b／c运行预算消费者及受控验证已接入、独立修正与最终出口继续，详见[总预算计划](2026-11-12-six-stage-budget.md)。[C单实例调用](../delivery/2026-11-13-six-stage-native-invocation.md)源码及非editable73项通过、完整独立两轴产品开放0／0；自身r1超时partial保留、r2完整聚焦175.93秒approve，最终完整独立两轴开放0／0、本地出口通过；发布继续，D真实旅程待实现|
|D2 模板与专家适配|新版本优化／重构模板，方向子模板、独立 Agent 定义／完整资源与可选后端；旧版本保持，公开说明可独立复现|按 D0／D1 分片|
|D3 实际执行与交付|适配包的实际叶／方向流程与六阶段衔接、适当 CPU／模型与可用硬件验证；自身审查＋新独立两轴，手册、正常推送及自己的必要 CI|按每实现片分别验收|

研究以当前可核官方来源和论文为准，每个方向独立文档，明确检索日期、版本、能力证据和未安装／未执行范围；没有可靠专用 agent 时直接说明，不以通用库改名充数。委派研究使用 fresh-context 并行 agent，最多占可用并发槽，分批完成；作者并行核代码／来源，作者研究在D0独立复核。研究者只写分配的报告，不安装、运行 GPU／模型、修改产品或替代审查结论。

## 方向与参考目录的对应

参考页把内容分为Getting Started、Adding Model Support、Performance Techniques、Cluster & Debugging；这不是现成自主agent清单。上表R4–R9将Performance与运行技能拆成可独立评价的职责，保留MoE长上下文／VLM等跨域专题为组合消费者。R10承接开发与验证技能；R1 kernel以及R2低精度是用户原需求和该站点训练／ModelOpt文档的补充方向。每个研究包内仍逐项记录具体Skill对应能力，不把多个独立决策压成一个全能专家。

初步编排按“资料与硬件清点→可信基线／诊断→按瓶颈选方向子流程→独立正确性／质量／性能评价→候选整合”组织；并行候选须在隔离实验或不同分支上执行，不能同时修改同一训练配置后失去归因。此为待D0确认的设计，尚不宣称通用图运行器已经存在。研究也须分开技术分类、实际可用工具和可执行流程，用户可调各层实现而不越父级权限。

用户追加横向关系：纵向技术分类不能直接成为互斥的agent类别，一个架构或kernel agent可能覆盖多类技术；每类技术也可能由多种职责互补。完成纵向研究后再开展X1–X3，核跨域真实流程而非重复候选清单。D0须同时记录技术能力、职责（执行／监管／审查等）、专长、所需工具／资源、输入输出和可组合关系；单个agent定义可被多个模板按固定版本引用。模板嵌套负责上下文与权限上限继承，协作边负责数据／依赖交接，不能以技术分类推导权限扩张或重复建立运行所有者。

X1–X3已收口，采用选择与D1拆分以[D0](../research/2026-11-12-specialist-adoption.md)为准：原六阶段先作为通用复用消费者，Forge保留为首个kernel方向适配。完整原生Agent系统若无法覆盖全部内部会话的材料、权限和总预算，完整模式保持unsupported，不因有CLI／SDK而准入。条件适配Optuna时在原runner消费有限参数建议，不直接安装研究dev快照；只有真实分布式试次需求才接Tune。确定性solver消费核定config／artifact，不伪造需要读取资料的模型会话。当前代码、测试和CI未变，三份横向研究均非运行或收益实测。

U1/U2 的机器身份、备份与原始输出留在 home 下私有验收目录；公开手册只描述通用用法。每节点更新本计划、交付和 [PLAN](../PLAN.md)；不将上一片测试或 CI 授给新行为。
