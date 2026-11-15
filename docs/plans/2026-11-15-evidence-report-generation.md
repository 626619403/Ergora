# 证据报告作者与 HTML 阅读视图

日期：2026-11-15。工作基线 `f00bfdfd15173ceb0e961681679d6d3d62254bed`，独立分支 `docs/report-generation-guidance`。统一排期由主工作树维护；本片不修改 `docs/PLAN.md`。

## 目标与现状

准确区分领域分析 Agent、来源绑定的复盘作者和程序生成报告，研究用户指定的 [Anthropic HTML 文章](https://claude.dev/blog/using-claude-code-the-unreasonable-effectiveness-of-html/)，交付一个可复用、只读、后端无关的证据报告作者。完整调查见[研究记录](../research/2026-11-15-evidence-report-generation.md)，实际检查见[交付记录](../delivery/2026-11-15-evidence-report-generation.md)。

基线发行目录有 31 个 Agent 包、49 个 Workflow 包，包含旧版本；没有专门的通用总结／报告作者。`review report` 的 JSON／Markdown、训练轮次索引和 bootstrap HTML 是程序读取／渲染原记录的路径，不能据此宣称已有报告 Agent。训练 flow-map／performance／measurement 和三类 retrospective 作者各有专门职责，保持原定义和身份。

## 最小实现

1. 新增 `ergora-evidence-report-author@1.0.0`、其完整自包含 Skill `ergora-evidence-report`，以及单叶根 `ergora-evidence-report@1.0.0`，preset 为 `evidence-report`。复用现有 `DefinitionLibrary`、资源摘要、完整 manifest、`prepare-from-manifest`、`check-input`、`run-input` 和 `inspect-run`；不新增 Python 服务、渲染器、后端或持久状态。
2. 原始需求、材料、身份和覆盖由操作者完整交给 `root/author`。报告作者返回现有 `summary/artifacts.response` envelope；response 中约定保存 Markdown、静态 HTML、来源表和限制。该内容约定不是新的可信证据 schema 或批准合同。结果仍由原运行记录归档。
3. HTML 为可选阅读视图：自包含 CSS／SVG、无需脚本、框架或 CDN；来源／覆盖／失败／反对意见／未验证范围与 Markdown 保持一致。量化图表只使用真实提供的测量值、单位、样本和比较身份；无数据时采用说明图或表格。HTML 不持有运行、发布、批准或第二状态。
4. root／leaf 均只允许 definitions 读取，write 为空、shell=false、network=[]。Skill 全文内联，可用 text-only；增加资源不扩大工具／网络权限。正文按后端无关合同编写，默认 Codex 仅为既有可替换 binding 请求。
5. 在既有工作流手册增加发现入口，独立操作页说明来源准备、精确调用、原件读取和显式导出；不重组其他模板，不改已发布包／旧 catalog 条目的语义，不安装应用／全局 Skill，不提交／推送／评论或修改业务仓库。

## 验收

|步骤|完成条件|状态|
|---|---|---|
|R1 调查|指定全文及官方示例源码的可核身份、文章观点与本地实现／建议分开；失败如实保留|已完成；指定 HTML 200 全文、Markdown 403、GitHub API 限额 403 及 gallery 固定提交／四份已读文件身份保持|
|R2 定义／资源|新包沿原 inspector／编译器通过，原包字节与旧 catalog 条目保持；Skill 通过 skill-creator validator|新包 inspector／Skill validator 通过；32 个旧 catalog 条目语义、216 个旧 preset 文件原字节保持|
|R3 消费链|沿既有 preset 冻结／继承接缝，核独立 manifest、叶权限、完整祖先资源与源库移走后可准备输入|修正参数化测试遗留 root/map 后 r2 两项通过／4.62 秒；新真实 CLI 定义／manifest／输入／准入已通过；不新增 CI|
|R4 发行包|构建非 editable wheel，核源码／wheel 所有新资源与未变参考身份，不安装新环境|wheel 构建／657 文件逐字及 283 参考通过；隔离解释器从解包 wheel 导入并读取新 preset 通过。没有新安装验收|
|R5 实际调用|用真实既有后端生成小报告，保存原输入／prompt／argv／stdout／stderr／result／读取观察；导出 HTML 必须来自原模型结果|Codex 原 run `3a08dd0bb80448269cfe222f79ef6d15` succeeded／89.084 秒；完整原件可核，直接解码 3,890B Markdown／6,181B HTML；静态检查与无凭据／空工具路径的原观察重读通过，19 原文件保持。Claude 未调用，不声称异后端|
|R6 交付|链接／完整 scope／diff／untracked／源包身份／真实验证／限制明确；交主协调者分配 fresh 独立审查|实现者检查与 70 本地链接目标通过；完整 12 文件 scope／diff／未跟踪清单和私有原件交主协调者。本片独立审查待分配，尚未标完整交付|

适用检查以既有定义、preset、manifest／资源和原结果读取路径为主；不为提示词文本新增测试或 CI，不以静态／CPU 小例认证训练、GPU、报告正确率、HTML 浏览器布局或异后端审查。
