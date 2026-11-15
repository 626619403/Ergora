# 并行后端审查／报告任务逐步记录

日期：2026-11-15。按[并行计划](../plans/2026-11-15-backend-review-and-reporting.md)创建两个以固定f00bfdfd为基线的独立worktree与分支：`docs/review-backend-guidance`、`docs/report-generation-guidance`。分别交子agent盘点、调研并完成最小资源／模板指导实现，主控继续c1b1所有权与生命周期工作。

两子任务均先要求返回现有角色／Skill与真实调用边界；之后在各自项目docs写具体计划和逐步交付。当前没有主线产品变更、后端原生功能验收、报告agent运行或合入／发布结论。下一步接收盘点，准确答复报告角色现状；待各自完整diff、资源版本与实际验证后安排新的独立审查。

BR1已盘点现有pretraining-review／posttraining-review入口及通用三路；实际Ergora后端走Codex exec／Claude print结构输出，没有自动封装托管Code Review。准备以两个领域根的新patch继承窄后端Skill，保留旧根与无关入口；官方能力与产品范围由该分支来源研究确定，不凭产品名称推测可用。BR2已确认现有领域分析／测量／复盘角色和程序报告均不是专用通用报告作者，正在补独立只读evidence-report叶。新定义／Skill／原资源接缝的源码验证已做，原参数化root路径问题的失败与修正由该分支分别记录；真实Codex小报告仍待，不称已安装／合入／发布。

## 恢复时的并行审查状态

BR1在独立分支已形成12文件候选，新的fresh-context reviewer已完成需求符合性／维护性两轴approve、开放0／0。主控已读该分支约定的独立报告；范围限文档／配置源码，核原来源、八叶完整Skill继承、216旧preset及旧对象／输入保持。非editable新安装、真实后端／厂商review、自身模板和发布尚未由该片验收；候选仍未合入主线。原报告保存在该分支`docs/delivery/2026-11-15-review-backend-guidance-review.md`。

BR2已完成只读报告叶候选及一次真实Codex小报告，新的fresh-context reviewer仍在独立核原DB／stdin／原输出／结果／HTML和资源边界，尚未给最终审查结论。不得将旧段落的“真实Codex仍待”作为最新状态，也不得把当前真实小报告扩大为已安装、浏览器或系统准确率验收。具体原件及未验范围继续以该分支`docs/delivery/2026-11-15-evidence-report-generation.md`为准。

两个分支都改preset目录索引，后续整合必须保留两者并验组合。用户再次要求防压缩遗失的[WA1–WA5](../plans/2026-11-15-workflow-evidence-and-human-gates.md)已登记，三路审计尚未启动；不会用BR1／BR2的窄结论替代全局工作流审计。
