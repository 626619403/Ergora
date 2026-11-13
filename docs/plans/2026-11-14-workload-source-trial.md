# W1：真实参考源码的优化工作流试用

日期：2026-11-14。承接 [S1 技能补充](2026-11-14-engineering-skills.md)和 [B3 提案交接](2026-11-14-proposal-experiment-handoff.md)。用户提供一个有既存工作内容的业务项目及参考分支，用于测试 Ergora，明确不让本开发会话直接修改业务实现。

## 范围与验收

复用 S1 同一 noneditable 包及 `optimization-performance-diagnosis`，真实源码仅从固定 Git 对象读取。十三份原源码共 93,748B，完整身份与私有材料保存在本地被忽略的证据目录；公开不重新分发业务源码、内部服务和项目配置。

1. 先核固定参考身份、来源原件及共享仓库的 HEAD／status，保存选择范围。参考分支不是已批准的性能 baseline；不 checkout、fetch 或修改共享 WIP。
2. 通过原 CLI／task-MCP 显式调用原 design 和 profile 叶，逐次固定 manifest、input、原 result、实际后端与回退理由。各自收到完整源码及全部祖先 Skill／上下文，不隐式执行整图。
3. 将两个完整原结果明确交给 measurement，核真实 input／stdin 中的原前驱和连续资源交付。预算为三次显式、每次 240 秒的模型调用，无隐式重试；保留失败、unknown 和原身份。
4. 人工核原回复的代码依据、建议与缺项，独立审计来源、完整交接、权限、共享仓库与观察到的进程终态。实际训练、parser／profiler 执行、数据／权重读取、设备申请和候选采用均在本片范围外。
5. 更新[本片交付](../delivery/2026-11-14-workload-source-trial.md)，由新 fresh-context 独立评审核整个试用证据及公开脱敏范围，再普通发布当前开发分支。没有产品变更时不为记账重复昂贵回归；CI 按实际 workflow 选择记录，不借 S1 产品 CI 当本片模型或业务收益证明。

缺少已绑定模型／数据、目标设备与环境、真实基线／候选测量、独立质量 oracle 和正式预算时，保留 B3 开放。源码提案、成功调用或 measurement 的建议都不能替代原 runner／evidence SHA 批准和项目集成复验。

## 当前状态

步骤 1–4 完成：共享仓库的原 HEAD 和 213 条 status 字节保持；三个真实叶成功，measurement 返回补证据的 `request-changes`；十三源码在三份实际输入中逐字完整，两个原前驱明确交接，十五 inline／六参考 12,954B 完整读取。原回复已人工核对，采样进程收尾范围分别记录。新的 [fresh-context 独立终核](../delivery/2026-11-14-workload-source-trial-review.md)已通过，需求／维护性两轴开放 0／0；本地出口完成，普通发布待收口。三次调用采用用户已授权的 Codex 显式回退，独立会话不冒称异后端成功。
