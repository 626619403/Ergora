# Q3.3：保留 kernel 评估的按瓶颈优化提案路径

日期：2026-11-15。固定基线 `29cdcfe2f45a66dcaad1835c0860c24a78290529`；承接 [Q 总计划](2026-11-15-domain-review-optimization-quality.md)、[图谱](2026-11-15-training-flow-maps.md)和[测量合同](2026-11-15-training-measurement-contracts.md)。Q2 自己的 CI 已八 job／30必要步骤成功；Q3.1固定发布自己的 CI 单独跟踪，不用本片覆盖它。

## 要解决的具体问题

旧 v2 总路径以 analysis→kernel→measurement 组织，只读单叶需要操作者提供原任务及完整前驱；新增图谱未进入该总路径。用户要求 kernel 专家继续参与，同时允许实际干预为去冗余、解依赖、内存、通信或调度。新路径须固定这些职责、完整祖先资料和证据边界，不改旧 v1／v2 字节或伪造自动执行能力。

原 `WorkflowDefinition` schema 2 的单个绑定只能引用一个输入或节点输出，Agent 只接 `task`；`prepare-input/run-input` 不解析或执行依赖。用 map 的模型输出替换下一叶 task，会在后续消费者中丢掉原任务／源码。现阶段不为了一个静态配方新增拼接语法、格式或调度器：新根各阶段绑定原 root task，顺序仍由依赖边表达；每次实际单叶调用显式补齐全部原前驱结果。自动运行和机器校验跨叶材料另沿已有 owner 立片。

## 最小变化与 owner

- 新 `ergora-training-proposal@3.0.0`：flow map→并行 design/profile→kernel assessment→measurement，最终 all-join 保留全部阶段；原角色和完整 Skill 复用。
- 新 kernel-assessment 子模板：包装原 v2 kernel Agent，明确“无需 kernel 修改／证据不足／可提候选”的评估边界。它始终在新总路径中；不新建同职能 Agent 或修改原 kernel 版本。
- 根的原创自包含 Skill 给阶段资料交接和按证据选方向的方法，指向既有方向 preset；固定 root 不自动安装／挂接／运行全部方向。预算、实验、quality、恢复和采用仍归原 owner。
- 原 catalog／操作手册／一项组合冻结回归；两个公开小任务验证 CPU 去冗余无需 kernel 和 kernel/wrapper 候选设计的提案行为。合成或任务给定的信息保持相应标签，不作为真实GPU证据。

## 验收

1. 旧 v1／v2、独立图谱和新根可共装；只新增定义资源与 catalog 条目，不改运行owner／依赖／schema／283参考。新五叶保持只读、完整祖先与原后端可选性。
2. 新根的顺序、原 task 绑定和保留五叶的 all-join 可由原 compiler 核；移除活动定义库后冻结manifest仍可完整准备各叶，源码／父Skill／前驱原结果不被摘要替换。
3. 用非 editable 新安装和原 preset／架构／页面 catalog 检查；原包和CI各保留固定身份。两个小任务各通过 Ergora 显式运行五叶，保存全部原输入／输出并逐叶核 stdin 和完整前驱。分析两叶可独立运行，示例驱动不建立产品调度器。
4. 人工及新独立评审核：kernel 在两路径确实调用；CPU任务可结论无需算子修改，kernel任务可给有界候选及独立检查计划；测量叶面对缺真实训练证据须保留缺口。这只验提案／资料交接，不能宣布真实 kernel、训练质量或收益通过。
5. 更新[交付](../delivery/2026-11-15-training-bottleneck-path.md)／PLAN，完成自身模板、新 fresh-context 独立评审、普通发布与该候选自己的适用 CI。

Q2.3 独立审查统一报告、Q4 多轮证据／循环、Q5组件协议及严格发布验收保持下一片。真实GPU／B3和完整Forge的外部条件不因本片关闭。
