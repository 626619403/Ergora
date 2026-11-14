# Q3.2：复用原语义、基线和成对测量合同

日期：2026-11-15。承接 [Q 总计划](2026-11-15-domain-review-optimization-quality.md)及 [Q3.1 图谱](2026-11-15-training-flow-maps.md)。本片固定基线 `2729b81a4c10e4bf8c77bd78ea4165b0a64cb0c0`；该提交本地审查完成，待前片 CI 终态后发布。没有变更业务仓库或训练资产的授权增量。

## 原 owner 与本片决定

现有 `training`／`reference_training_setup`／`reference_training_preparation` 负责项目基线、可信 runner 和实验；冻结参考的 `perfctl` 负责原证据绑定与归档，`compare_runs` 负责成对运行的统计筛选；`reference_training_evidence` 只读验证原归档。测量 reviewer 是建议性独立解释，不持有这些权限。[训练手册](../TRAINING.md#从专家提案填写原实验合同)已有逐字段说明，不再复制第二套合同或引入新评分器。

Q0 的固定 Bridge 工作流与 PyTorch profiler 研究已解释固定语义、完整完成窗口和诊断扰动。本片核现有实现能否满足这些义务；若发现真实缺口，记录并另立最小实现片，不修改 283 份参考以迁就样例。初始锚点与本轮参照分开、多轮归属及有界循环仍归 Q4。

## 最小产物与验收

1. 补用户入口：沿已安装包定位原 `demo.py`、`compare_runs.py` 和 `perfctl.py`，给一键 CPU 合同演示及重算命令；直接运行既有工具，不另建脚本、运行器、schema 或数据库。新目录保留原件，示例不能成为真实项目的批准。
2. 核字段与调用：原 baseline、完整提交、有效配置、workload／环境、数据／checkpoint、允许变化、独立正确性／质量、预登记统计政策、原比较器与全局窗口确实在其 owner 绑定。记录机器能查的内部一致性与仍需受信流程证明的真实性；没有实际性能／训练结论。
3. 用现有非 editable 安装环境执行原合成 demo／比较器／gate，保存全部原 stdout／stderr／产物。原检查覆盖过期基线、错配配置／数据／环境／初态、阈值漂移、过期或失败质量、重复 run 与不足样本；另观察无收益／不确定结果不会通过 gate。正例最多是 `ELIGIBLE_FOR_HUMAN_REVIEW`。
4. 复用原比较器、registry、基线与归档测试，不新增镜像实现的测试／CI。核 633 产品及 283 参考仍不变；更新计划／[交付](../delivery/2026-11-15-training-measurement-contracts.md)，运行自身结构模板，交新 fresh-context 独立审查后普通发布。

本片是已有能力的合同审计、操作入口和可重放验收，不声称新训练执行或统计方法。Q3.3 再组合图谱、分析、保留的 kernel 专家评估和测量；没有实测证据时明确请求补采集，不能要求专家制造一个 kernel 候选。
