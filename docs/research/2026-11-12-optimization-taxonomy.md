# 优化方向、专家能力与流程的两条轴

依据2026-11-12读取的[NVIDIA Megatron Bridge Agent Skills Reference][index]整理。此文用于分派和汇总[专家模板重整研究](../plans/2026-11-12-specialist-template-refresh.md)，不是已安装能力清单，也不要求导入整套Bridge。官方页把Skill定义为操作指南与经验证知识卡，含启用片段、代码锚点、约束、陷阱和验证步骤；不能由此推导存在一个自主优化agent。

## 纵向：按可测量的技术决策拆分

保留官方技能粒度，研究包只合并相邻的检索职责；表内技术项仍分别评价。一个研究包不等于一个agent，更不等于一个Python类。

|研究包|Skill Reference中的技术项或关联资源|需要分别回答的问题|
|---|---|---|
|R4 并行与分片|Parallelism Strategy Selection、Megatron FSDP、Hierarchical Context Parallel、Vision DP Over CP；MoE Long-Context与Hardware Configuration|TP/DP/PP/EP/CP如何选、是否有真实搜索器、mesh与资源是否相容；动态CP按相关训练文档补查。|
|R3 通信与重叠|TP / DP / PP Communication Overlap、MoE Dispatcher Selection、MoE Expert-Parallel Overlap、MoE Communication Overlap|选择哪个后端、哪些流量暴露在关键路径、与计算争用如何处理；微基准与完整训练分别评价。重叠主题可能共享实现，不能按页面数量复制agent。|
|R5 显存与状态搬运|Memory Tuning、Activation Recompute、CPU Offloading；关联memory estimator|分别核重计算粒度、激活／参数／优化器状态、host buffer与传输代价、自动搜索和恢复。|
|R6 执行图与数据调度|CUDA Graphs、Sequence Packing；关联attention优化、intra-microbatch重排及编译文档|capture/replay、动态形状、融合、packing语义与调度如何影响完整step，是否有可执行优化流程。|
|R7 诊断与测量|Nsight Systems Analysis、Memory Snapshot Analysis；分析陷阱与SQLite配方等附属资源|先识别瓶颈，再选择干预；trace不是吞吐基准，allocator快照不是全部显存，测量和解释分开保存。|
|R8 多节点运行与恢复|Multi-Node Slurm、Slurm Templates、Resiliency|资源申请、rank／作业身份、失联与停止、straggler和checkpoint恢复；工具存在不等于当前账号具有集群权限。|
|R9 配方、模型与框架适配|Auto Recipe与Recipe Index、MLM vs Bridge Training、Adding New Model Support、LLM/VLM Bridge Patterns、Recipe Patterns、Test and Example Patterns、Model Verification Card、verl／NeMo-RL E2E|配方推荐是Skill、检索器还是搜索流程；转换、训练、质量与数值关联如何验证；同一技术在LLM/VLM/RL中有哪些差异。|
|R10 开发与重构|Build and Dependency、Bump Dependency、Testing、CI/CD、Review PR|哪些操作可用成熟库或现有agent，哪些需要项目自己的合同；如何复用六阶段开发，而不把每个阶段都伪装成模型agent。|
|R2 低精度与压缩补充|站点关联的Mixed Precision、ModelOpt Quantization／Pruning／Knowledge Distillation|训练与推理分支、真实导出和质量／收敛门禁；不把关联导航中的主题说成索引已提供的自主agent。|
|R1 kernel补充|用户所需kernel设计；关联性能、attention及底层算子|NVIDIA／Ascend／AMD等真实agent或原生流程、正确性与导数、硬件与编译版本、端到端实际命中。|

官方“MoE Training Optimization Workflow”“MoE Long-Context”“MoE VLM”是跨多个技术项的场景，可作为横向流程的入口，不能仅放进一个互斥技术箱。低精度、模型压缩、kernel以及动态CP等补充项须核各自官方文档和实现，不能只引用索引标题作为支持证明。最新网页和固定源码可能漂移，具体接口与约束以各报告核定版本为准。

## 横向：按跨域能力与协作职责研究

纵向研究完成后再进行X1–X3，直接复用其固定证据，并补查跨域控制和交接的实现；不是再做一轮相同工具列表。

|横向研究|跨技术的真实工作|需要核的协作关系|
|---|---|---|
|X1 架构与系统设计|联动模型结构、并行mesh、显存、通信、执行图、硬件及完整训练／服务目标；代码架构重构另与R10衔接|谁提出全局约束、谁拥有局部候选、谁整合并处理相互干扰；模型架构、代码架构和运行架构不能混为一个承诺。|
|X2 kernel到端到端优化|布局／精度／融合／计算／通信／host runtime、子图到整模调用和真实命中|单体设计专家与完整搜索流程如何分别接入；外层只管理合同和交接，保留上游内部专家与预算。|
|X3 诊断、实验与独立评价|跨域瓶颈定位、有界候选搜索、多保真评价、预算与恢复、正确性／质量／性能审查|提案、执行、独立评价和采用由谁负责；如何防止共同修改导致失去归因，如何保留失败和无收益结果。|

例如kernel agent可能同时处理布局、低精度、图和通信算子；它不因被放入kernel模板就失去这些能力。反过来，通信方向也可能同时需要架构设计者、实现者、测量专家和审查者。**技术领域、职能、专家实现和工作流结构是不同维度。**

## 汇总和适配时的表示

D0用“技术方向×agent能力／职责”多对多矩阵比较候选，另列实现形态、硬件／服务依赖、实际接口、固定版本／许可、输入输出、预算／恢复和可信证据。能力标签只用于查找与选型，不授予工具权限，也不能证明效果。

现有[AgentDefinition](../AGENT_DEFINITIONS.md)允许多个`roles`和`specialties`，同一精确定义可被不同工作流和实例引用；[WorkflowDefinition](../WORKFLOW_DEFINITIONS.md)已区分结构嵌套、控制依赖和具名数据绑定。因此先复用现有格式，不为这份研究另建运行时分类语言。是否增加字段由真实消费者和D1验收决定，不能先建只有展示用途的第二执行合同。

结构父链累加全部声明资料、Skill和上下文，同时约束子权限；横向数据依赖不建立资源继承或权限提升。完整上游优化系统作为原生子流程候选，与只读专家、工具库和Skill分别标明；当前只支持静态提案的部分不能因新增关系图而宣称已经运行。最终采用仍须沿原task/run/candidate、可信评价和owner决定。

[index]: https://docs.nvidia.com/nemo/megatron-bridge/latest/skills-index.html
