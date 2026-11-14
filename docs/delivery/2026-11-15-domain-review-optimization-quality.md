# Q0：领域审查与循环优化的研究及计划

日期：2026-11-15。原始需求及验收节点见 [计划](../plans/2026-11-15-domain-review-optimization-quality.md)。固定基线 `871cc4b6b2c21420307a002bf5b983707720fe90`，分支 `refactor/architecture-foundations`，开始时工作树干净。

## 本片范围与状态

仅研究／计划／当前入口记录；不改生产代码、模板、依赖、CI、安装或业务仓库。Q1–Q6 均是后续实现，本片不关闭真实 B3 或完整 Forge。G1 已完成，原证据和旧失败保持。

|步骤|实际结果|
|---|---|
|恢复与盘点|已读 AGENTS、PLAN 当前／开放范围、G1 总计划、Git status／log；已读通用审查、优化组合、原 PR／MR 关联和训练 owners。|
|方法|应用 research、ergora-codebase-quality、ergora-performance-diagnosis 和 maintainable-project-delivery；已读设计／测试接缝／独立评审参考。|
|现状|28 preset；通用三路审查已存在；专用 pretraining／posttraining PR／MR 组合未在目录中出现。原 link_review 只关联原来源候选；v2 总优化模板固定经过 kernel，18 方向仍是只读提案。上述为源码观察，没有新运行验证。|
|一手研究|两个 fresh-context 研究者已完成[审查工具](../research/2026-11-15-pr-mr-review-tools.md)与[循环优化／组件架构](../research/2026-11-15-iterative-optimization-architecture.md)；公开固定源码、官方资料和五篇论文摘要，未安装／执行第三方工具；未读范围和失败请求逐份列明。|
|计划|已写 Q0–Q6 优先级、现有 owner、每片验收、语义与性能证据边界、局部组件协议和最终审查；已按研究收敛借鉴／接入／自实现／暂缓决定。|
|验证／独立审查／发布|源码静态数量与无产品差异已核；研究齐备后的五份 Markdown 152 条本地链接／fragment、116 引用定义、行尾空白检查通过。自身原模板已通过，独立终核／发布接续，见下文。|

## 尚未核实／未运行

未运行产品测试、领域 reviewer、真实训练或 GPU；没有新的性能／质量／后端多样性成功声明。研究只读公开源码／归档，没有执行其中代码、安装其依赖或向平台发送审查意见。论文仅读摘要；没有论文效果复现。最终文档／自身模板检查不代替产品与真实训练验收。

## 下一步

两份研究、计划、本地文档检查、自身原结构模板与新独立两轴审查已通过；接续最终全文件文档／差异检查、普通提交／推送当前开发分支并核远端身份与适用 CI。实施下一片为 Q1.1 精确本地 PR／MR 审查包；Q3.1／Q5.1 可独立盘点。

## 文档验证与自身模板

研究齐备后的 `check-docs-r1` 已检查当时五份变更 Markdown：152 条本地链接／简单 GFM fragment、116 个引用定义及行尾空白，错误 0。107 处外部 URL 只统计、不由此检查联网验证；一手内容来自两份研究及独立审查抽核。基线至当前 `src / tests / scripts / pyproject.toml / .github` 差异为空；没有为纯文档新增产品测试、CI 或依赖。初步123链接检查时两研究尚在途的缺项不改写为当时通过。

已通过既有非 editable 安装的原 `ergora-structure-review`，Codex 真实只读 text-only 调用 `0af8943512da46d994e2aa4da91e837f`：26.382777 秒，`succeeded / approve`，CLI exit 0。21 份完整计划／研究／源码，共 360,522B；任务、全部内联文件和三份声明的父／叶资料均在实际 stdin，准备 prompt 与实际 stdin 逐字一致。input digest `7c2e9325b800593cd3d9241392d7b6db04dfe9e2cba55c7d579d88b94ef89146`，原结果 SHA256 `d74aec37d5bb408332995c85fbbed771b0ba6af072a0f6c7f9e1ba576d056766`。

本次采用用户已授权的 Codex 替代，理由保留为此前较大 Claude 审查超时；没有本片 Claude 失败尝试或异后端成功声明。该模板只审当时所供文本，未核远程页面、磁盘其他文件、运行／发布或后续记账；新 fresh-context 独立评审另核原需求、源码、一手来源与实际原件。完整私有输入／回复和验证原件留在忽略的持久检查目录，不含入公开产品。

## 本地独立终核

新 fresh-context [独立报告](2026-11-15-domain-review-optimization-quality-review.md)需求符合性与可维护性两轴均 `approve`；实质 finding 0、开放阻断 0。评审者逐字核五份作者文档与完整 tracked／untracked 冻结范围，直接抽核 BBuf 固定归档、Claude 官方来源、Bridge／slime 与 TorchTitan 的非直观实现事实，并核自身模板 21 份正文／三份父叶资料、实际 stdin 和原结果摘要。

本地批准只覆盖 Q0 研究与计划。Q1–Q6、安装新工具、领域 reviewer 的检出能力、GPU／质量／加速和发布／CI 均不由该结论预批。后续完成状态只记账，不改两份研究及计划设计；最终包含新增文件的空白与链接检查、普通发布身份另列。
