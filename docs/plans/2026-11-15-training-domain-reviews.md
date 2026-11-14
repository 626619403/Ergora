# Q2.1／Q2.2：预训练与后训练审查组合

日期：2026-11-15。承接 [Q 总计划](2026-11-15-domain-review-optimization-quality.md)和 [本地材料合同](../LOCAL_REVIEW.md)。基线 `ad168810b6caa9ed435d0b3fef833856c286edf9`，分支 `refactor/architecture-foundations`；开始时只有 Q1.1 发布／独立补核的记录更新未提交，产品与测试干净。Q1.1 的 Windows CI 仍在途，不预先宣布其完成。

后续 Q1 CI 的两项只读 Git 对象删除 fixture 失败已由独立五行测试修正单独发布为 `a38dd21891ac200c575e8520c49cc82f97c9d478`，产品未变。Q2 最终审查与发布差异以该完整提交为固定基线；不把 Q1 修正混入领域实现，也不预先认证其新 CI。

## 本片行为

新增两个可独立版本化的 reviewer 与领域子模板，再各用一个根组合把原结构／正确性／测试价值审查和领域专家显式 all-join。职责都是只读 reviewer，专长与后端独立；原通用模板及旧 preset 字节保持。默认 Claude Code，可通过原逐实例绑定改用受支持后端，回退记录真实原因，不声明消除相关错误。

预训练专家检查实际目标中的 loss／有效 token／mask／packing、梯度累积和更新时钟、精度、并行 collective、参数／梯度／优化器状态与 checkpoint／恢复。后训练专家先辨认 SFT／偏好／RL 算法，再查 rollout／样本分组／mask、reward／reference／policy、old/current log-prob、版本／陈旧性、异步生命周期和恢复。公式、阈值和不变项由目标框架与任务给出，不能把某个框架或算法当所有项目的默认值。

Skill 是 Ergora 根据 [Q0 一手研究](../research/2026-11-15-pr-mr-review-tools.md)编写的领域指导：借鉴固定 Bridge／slime 的具体合同，附可核来源与适用限制；不冒称迁入其训练器或官方 Agent，也不复制未核许可的 BBuf 全包。静态定义、真实叶调用和训练语义／GPU 验收分别记录。

## 所有权与复用

- 沿原 AgentDefinition、WorkflowDefinition、preset catalog、manifest、权限祖先、ReviewDAG 和 AgentBackend；不新增领域执行器、结果 Schema、调度器或实验／批准权威。
- 原三路审查作为嵌套子模板复用；领域 Agent 可单独取用，整体根也可按原协议用于正式 review stage。原静态边和 required／all-join 含义保持。
- 外部审查包先通过 `review read` 完整输出，再作为所选叶的完整任务输入。现有独立调用不自动运行根端口；Q2.3 的统一报告入口另片实现，当前不能用静态 all-join 冒充已运行全部分支。
- Skill 自包含，全部必要内容随包；外部 URL 是方法来源，不要求 reviewer 联网读取。目标源码／检查缺失时明确提出补证据，正文不授予 shell／网络权限。
- 用已有 JSON／资源摘要发布新身份，只在原 catalog 注册；不修改原通用定义、在途任务或旧模板摘要。保持 283 冻结参考。

## 验收

1. 新 preset 可离线安装／重试，冻结后移走活动库仍保留四个 required reviewer、完整父链资源、只读权限与原通用身份；正式 ReviewDAG 可采用同一嵌套合同。
2. 提供标准库 CPU 合同样例：预训练的不等有效 token 归一错误与有效配置变体；后训练的 mask／样本或权重版本错误与有效变体。独立确定性 oracle 证明例子实际差异，不依赖模型说对；不得把合成例子称为真实训练或普遍检出能力。
3. 安装后对每个领域的已知缺陷与有效变体真实调用只读叶，完整需求／源码／配置／检查与祖先资源交付核对；分别保存发现、漏报、误报和缺证据，模型输出不代替数值或多卡检查。
4. 在既有 preset／组合／权限与导入边界测试中补必要的冻结和正式准入保护，不测试提示词措辞，不增加 CI job。构建非 editable wheel 并核新数据、来源、安装和旧参考身份。
5. 更新真实使用入口；用 Ergora 原模板审本片，另起新 fresh-context 独立评审，修实证问题后普通推送／核自己的 CI。前片在途 CI 保持原身份，不因本片覆盖或改写。

Q2.3 统一运行／报告、远端采集／发表、Q3 算法图与 kernel 专家评估、Q4 多轮实验、Q5 目录协议及 Q6 最终发布保留各自范围。真实 B3／完整 Forge 等外部条件不由本片关闭。
