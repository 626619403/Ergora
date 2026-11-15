# 后端审查说明与证据报告生成

日期：2026-11-15。用户在训练循环开发中追加两项并行任务，主线c1b1继续。两个任务各用从本地固定 `f00bfdfd15173ceb0e961681679d6d3d62254bed` 建立的独立工作分支，避免改变主线在审产品身份；工作区是持久目录，不依赖tmp。

|任务|原始要求／来源|交付与验收|当前状态|
|---|---|---|---|
|BR1 后端PR审查说明|参考[Claude Code文档](https://code.claude.com/docs/en/code-review)与[官方文章](https://claude.com/resources/articles/code-review)，在相应PR审查Skill解释Claude Code／Codex等后端差异|核官方能力、CLI／插件／托管产品和Ergora适配器的实际关系；说明认证／可用性／结果／副作用，模板保持后端可替换；已发布资源以新版本更新，保留旧包；既有资源／安装接缝及新的独立两轴审查|子agent在`docs/review-backend-guidance`盘点／实施，未合入主线|
|BR2 报告生成|盘点现有总结／报告agent或模板；参考[HTML报告文章](https://claude.dev/blog/using-claude-code-the-unreasonable-effectiveness-of-html/)改进报告辅助|明确程序报告和LLM作者；优先沿已有合适角色／资源，必要时提供窄的独立报告叶；保留机器可读原证据，HTML绑定真实来源／范围、静态自包含；真实小报告生成与原输出／资源链，新的独立两轴审查|子agent在`docs/report-generation-guidance`盘点／实施，未合入主线|

BR1／BR2各自在项目docs维护具体计划、来源和逐步交付，先报告真实现状与小范围。主控统一更新本页和总计划，审查后再接续合入、核版本及逐片普通发布。子任务不改全局Skill、既有已发布包、训练业务仓库、主线产品／index或平台评论；使用后端调用不会自动获得另一产品的托管审查能力。源码／静态指导／实际模型运行分别记录，缺认证或资料不可达不声称成功。

不要为说明文字引入第二调度器、报告服务、前端框架或新的CI矩阵。HTML是可阅读产物，不是新的运行状态、批准、实验测量或性能收益权威；现有原evidence与人工release保持。完成标准是小片实现、实际适用验证、独立复核和准确同步，而不是只写调研结论。
