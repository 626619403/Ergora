# Q3.1：源码锚定的算法、执行与生命周期图谱

日期：2026-11-15。承接 [Q 总计划](2026-11-15-domain-review-optimization-quality.md)及 [Q0 架构研究](../research/2026-11-15-iterative-optimization-architecture.md)。Q2 已完成独立本地审查并固定为 `0b5b5f1ff7a3463fcb10cf5a05e5f7c7bcae7c62`，作为本片基线；其 628 产品原件／验收环境保留，不覆盖。开始时只有本片两份准备文档未提交。Q1 修正自己的 Windows CI 仍在途，Q2 精确远端发布另记。kernel 专家保留在后续总优化路径，专家评估与实际算子干预分开。

## 最小变化与现有 owner

新增独立版本化的只读流程分析 Agent、完整自包含 Skill 和单叶子模板，沿原 definitions／preset／manifest／AgentBackend；不改调度或训练 owner。方法复用固定 Bridge 工作流、TorchTitan Trainer／TrainingEngine、slime rollout／loss、SGLang cache 生命周期与 PyTorch profiler 研究，编写 Ergora 自己的指导；不迁入训练器或凭未测源码宣布可删除依赖。

输出沿原 proposal 文本合同，由根任务和原资源固定。首片不新增图数据库、图格式或循环调度器。节点／边附源提交、文件、函数或行、实际配置、执行 owner、已观察／推断／未知。分别呈现算法图、执行／通信／并行图和资源生命周期表；候选可并行边不表示实际已经重叠。Agent 工作流图不能替代目标训练流程图。

图谱至少调查初始化／恢复、数据／packing／mask、forward、loss、梯度累积／同步、optimizer／scheduler 时钟、保存／验证／下一次有效更新；后训练按真实算法加入 rollout／reward／样本组／policy 版本。分别追踪精度／参数／梯度／激活／RNG／队列与持久状态。缺少源码或 trace 时给明确覆盖边界和最小补资料请求，不冒称目标流程完整。

冗余分析须给可证伪假设、真实生产者／消费者、值和生命周期条件、必要依赖反例、最小判别测量、独立语义／恢复验证。先保留原始未改参照，再考虑最小改动；不能把数学零项、相同文本或配置声明当可删事实。源码图不证明实际瓶颈或收益。

## 验收与顺序

1. 沿现有 owner 注册不可变定义和 preset，不改旧版本；核新旧可共装、冻结资料、只读权限、原输入上限与后端可选择性。
2. 以 [W1](2026-11-14-workload-source-trial.md) 已捕获的真实参考源码十三文件／93,748B 为私有目标，通过 Ergora 新模板实际只读调用。重核原对象身份、完整 task 与全部父／叶资源；保持共享业务仓库 HEAD／status，标明外部 runtime 和未给源码缺口。不运行训练或修改业务实现。
3. 人工及独立核图中路径／函数／边与真实源码，至少一个可证伪去冗余假设和一个必须保留的依赖；缺证据给有界请求。公开记录不分发私有源码、内部服务或机器配置。
4. 安装非 editable 包，核产品源／wheel／安装身份及 283 冻结参考；沿已有 preset／input seam 做适当检查，真实文本演示不变成提示措辞测试。
5. 更新 [逐步交付](../delivery/2026-11-15-training-flow-maps.md)、使用手册与计划；原结构模板和新 fresh-context 独立审查通过后，普通提交／推送并核自己的适用 CI。前片自己的 CI 保持原身份，不为推进本片取消它。

Q3.2 继续由原 baseline／runner／evidence 提供机器可核的成对测量合同，仅在真实缺口有消费者时扩展。Q3.3 的新总 root 再将图谱、分析、kernel 专家评估和测量审查相连，保留 18 方向及无需算子改动路径。独立 `run-input` 不自动运行前驱；Q2.3 统一报告和 Q4 自动循环保持另片，不能由本片的文字图谱提前关闭。
