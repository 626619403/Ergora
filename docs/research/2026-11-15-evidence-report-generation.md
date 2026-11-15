# HTML 报告：原文、现有能力与最小接入

日期：2026-11-15；调查基线 `f00bfdfd15173ceb0e961681679d6d3d62254bed`。本页区分基线已实现能力、公开作者经验和本片新增设计；实现／验收分别见[计划](../plans/2026-11-15-evidence-report-generation.md)及[交付](../delivery/2026-11-15-evidence-report-generation.md)。未读取业务仓库、组织聊天或未授权外部资料。

## 一手来源及可核范围

用户指定的 [Using Claude Code: The unreasonable effectiveness of HTML][A1] 已直接读取 HTML 全文，HTTP 200、111,233B、SHA256 `8649db23e654ee394f94bacb4310d8d6e032272580aa5635becadc52217a6ec3`。页面署名 Thariq Shihipar，发布时间 2026-05-20，明确是其个人使用经验与偏好。正文包含 Why use HTML、Getting started、Use cases、FAQ、Staying in the loop；本研究没有用搜索摘要代替全文。

页面的 Copy markdown 链接 [A1md] 实际 HTTP 403，17B、SHA256 `2938e9f1284180959e33ab1718d0793a72ff6e4cdb8108c34dcd14e69446de5c`，不据此声称 Markdown 全文已读。官方链接的 [anthropics/html-effectiveness][A2] 经公开 Git 只读查询／clone，固定 HEAD `58c305be97f47b26b678f2c07dec01d4242268ec`；此前 GitHub API commits 请求返回 rate-limit 403，失败保留，没有反复刷新或访问私有服务。

读取了该提交的 README、`11-status-report.html`、`12-incident-report.html` 与 `14-research-feature-explainer.html`，并检查 HTML 依赖／脚本声明。私有原件、HTTP metadata、Git clone 与文件身份保存在 ignored `.ergora/checks/evidence-report-generation/research/`。公开引用固定提交，工作指令为本项目重新撰写，没有复制示例业务代码。

|固定源码|实际支持的观察|
|---|---|
|[README][A2readme]，1,429B，SHA `4e30b49e98d0b40a542f33095cbb22324a4de865c24ff2d7322bab5fef9f3915`|独立 HTML、无需 build／依赖；明确全部产品名、场景及数据为虚构，展示数字不能用作实测证据。|
|[status report][A2status]，16,382B，SHA `6468f720bab1d016657a9ed25c1049ec42f1810b230f486a5f3130427614bc7c`|紧凑概览、交付表、carryover、SVG 图和来源页脚；没有脚本声明。样例只标 `git log / CI / deploy log` 来源，不能据此认证真实数据。|
|[incident report][A2incident]，15,491B，SHA `e787d6a64eca1ccd77fd9fa18849400356895ed2717ceb26dad2638fcc3261a9`|anchor 导航、时间线、root cause、impact 与 action items；没有脚本声明。状态徽章只是示例文字，不是可信状态机。|
|[feature explainer][A2feature]，12,330B，SHA `0e701f8fb778bdd05ce5b8f5cd8fbc820f6dfd0d1f258a47c200e7c0d3b6dbe7`|文件导航、逐步解释、代码片段、gotchas／FAQ；有内联脚本控制片段切换。Ergora 最小报告用静态／原生 details 保留可读性，无需复制该交互实现。|

## 原文讲了什么

以下是原文作者的经验，不能推导为所有读者或后端均有效的实验结论。[A1]

- HTML 可以组合 table、CSS、SVG、图片和交互，比长 Markdown 更灵活地表达模块、差异、流程与空间关系；导航、颜色和可响应布局有助于作者本人阅读复杂内容。
- 最小使用方式是直接要求“make an HTML file/artifact”，先明确受众与用途；反复出现的模式才考虑 Skill。文章没有要求建设报告服务或引入渲染框架。
- 报告／研究／学习用例包括功能总结、周报、事故报告、技术解释与 SVG 图；示例强调单个 explainer 页面、关键代码段与 gotchas。代码审查、计划探索和一次性编辑器是其他分支。
- 作者看重分享与参与感；上传后可分享链接，但这不意味着任意报告已经获准公开。交互编辑器最后导出 JSON／prompt，仍由人把结果带回下一步。
- FAQ 承认 HTML 常比 Markdown 消耗更多 token；阅读率／效率判断来自个人经验，没有给出受控人类阅读实验、报告事实准确率或 Ergora 的收益测量。

原文使用 Claude Code 的 filesystem／MCP／browser／Git 上下文是其环境能力。它不授予本项目报告叶那些工具、资料或网络权限；本文也不把作者称“停用 Markdown”的个人偏好迁移为本项目规则。

## 基线当前有没有报告 Agent／模板

在 `data/presets` 精确盘点为 **31 个 Agent 包、49 个 Workflow 包**，包含旧版本。基线没有专门的通用总结／报告作者。下表列相近角色的精确身份，区别其真实职责。[E1]

|既有名称／版本|可以做什么|边界|
|---|---|---|
|`ergora-training-flow-analyst@1.0.0`；`training-flow-map` 根 `ergora-training-flow-map@1.0.0`|基于完整提供源码绘制训练算法／执行依赖图、生命周期表和可证伪冗余假设|专用训练分析；源码图不能证明实际瓶颈、并发或收益。[E2]|
|`ergora-performance-analyst@2.0.0`，亦保留 1.0.0|分析提供的 trace／memory／rank／数据路径并提出测量假设|分析已有证据，不采集 profile，不是通用报告作者。[E3]|
|`ergora-measurement-reviewer@2.0.0`，亦保留 1.0.0|审查原实验的正确性／质量／测量／不确定性|独立 reviewer；模型建议不授予实验采用或 release。[E3]|
|`ergora-retrospective-author@1.0.0`／`ergora-skill-retrospective@1.0.0`|从精确交接证据生成完整 Skill 候选，后接独立 reviewer|候选与既有 evaluation／adopt 分开，不是普通总结。[E4]|
|`ergora-memory-retrospective-author@1.0.1`／根 `ergora-memory-retrospective@1.0.1`（保留 1.0.0）|来源绑定的记忆正文候选／互补审查|明确 export/save／restore 保留原 owner。[E4]|
|`ergora-workflow-retrospective-author@1.0.0`／根 `ergora-workflow-retrospective@1.0.0`|有界根工作流修订候选／互补审查|不自动 import、新选 manifest 或运行。[E4]|

三种 retrospective 的 `root/propose` 作者与 `root/review` 是 LLM 调用。其作者 role 名为既有 `implementer`，不等于必然有 workspace 写权限。上述领域模板仍各自保留；不把报告指导塞入所有旧模板。

## 原结构化记录与公开导出路径

这些路径已经能生成／读取报告材料，但不是通用 LLM 报告角色。

|路径|真实行为与权威来源|
|---|---|
|`composition prepare-from-manifest / run-input / inspect-run`|原包冻结 task／composition／全部祖先资源；调用保存实际 binding、prompt、argv、stdout/stderr、结构化 result；`inspect-run` 按精确 run ID 核完整原 input／prompt／result，分别标 available。只读观察不重发模型，也不授予正式批准。[E5]|
|`review report --format json/markdown`|`review_requests.report()` 读取显式 source／manifest／叶→原 run 映射；逐叶核身份、完整覆盖、原状态及 reviewer 建议；同观察导出完整 JSON／Markdown，保留反对与 incomplete。它不调用报告作者、补跑叶或变成正式 all-join／平台批准。[E6]|
|`task evidence / task handoff`、`handoff verify/read`|读取原 job／receipt／artifact，导出可核交接 ZIP；选择的完整证据仍受原身份与容量约束。报告作者须由操作者把实际完整材料交给它，不能把列表或窗口称全读。[E7]|
|`training list / show / evidence / rounds-create / rounds-read`|原实验／归档记录与只读轮次索引；`training_rounds` 的 coverage 明确 `runtime_status:not_queried`、`authorization_status:not_evaluated`、`origin_authenticated:false`、`promotion_approved:false`。索引链接原观察，不执行／批准。[E8]|
|`reference/platform/bootstrap/report/build_report.py`|固定 bootstrap 手册 HTML、资源／模板／runtime 导出；代码执行渲染，不是 LLM 报告 Agent，也不应改成另一套任务状态。[E9]|

公开 CLI／手册中的检查成功、运行进程成功、结果结构合格、事实验证和正式批准是不同观察。特别是 `artifacts.response` 的任意字符串不会因 result envelope 合格而自动成为可信报告。

## 本片采用与保留边界

以下为本项目实施选择，不冒称原文规范或已测得收益。

新增独立 `evidence-report` preset，只有 `root/author` 一叶，报告作者／Skill／Workflow 均从 1.0.0 起步，原包与旧 catalog 条目保持。其实现 owner 是既有定义、资源及 composition 用例；没有新的报告服务、renderer、数据库或业务仓库修改。默认 Codex 是可替换请求，正文与来源合同不依赖后端。

Skill 将原文的导航、SVG、紧凑表格、可折叠证据转为静态自包含 HTML 阅读视图，并保留 Markdown、来源表和限制，输出仍放原 response artifact。HTML 只读、无需脚本／CDN；引用原文与固定源码指明方法来源，Skill 全文离线可用。来源、失败、缺覆盖、少数意见和测量绑定是本项目补充的真实性要求。图表须指向真实原数据；官方 gallery 的虚构数字不进入验收样例。

原 JSON／Markdown／日志、原 run 与人工 release 继续作为其各自权威。HTML 不成为第二状态或批准入口。报告只覆盖操作者实际提供的证据，不自动获取 workspace／MCP／网络；root 与 leaf 均受只读 definitions ceiling，继承全文仍由原 compiler 准入。新的静态模板不意味着其他全部模板已接入，也不表示报告事实准确率、浏览器布局、训练质量或异后端调用已获验收；实际验证见交付记录。

[A1]: https://claude.dev/blog/using-claude-code-the-unreasonable-effectiveness-of-html/
[A1md]: https://claude.dev/blog/using-claude-code-the-unreasonable-effectiveness-of-html.md
[A2]: https://github.com/anthropics/html-effectiveness/tree/58c305be97f47b26b678f2c07dec01d4242268ec
[A2readme]: https://github.com/anthropics/html-effectiveness/blob/58c305be97f47b26b678f2c07dec01d4242268ec/README.md
[A2status]: https://github.com/anthropics/html-effectiveness/blob/58c305be97f47b26b678f2c07dec01d4242268ec/11-status-report.html
[A2incident]: https://github.com/anthropics/html-effectiveness/blob/58c305be97f47b26b678f2c07dec01d4242268ec/12-incident-report.html
[A2feature]: https://github.com/anthropics/html-effectiveness/blob/58c305be97f47b26b678f2c07dec01d4242268ec/14-research-feature-explainer.html
[E1]: ../../src/ergora/data/presets/presets.json
[E2]: ../../src/ergora/data/presets/agents/ergora-training-flow-analyst/skills/ergora-training-flow-map/SKILL.md
[E3]: ../TRAINING.md#可选的实验专家提案
[E4]: ../USAGE.md#生成来源绑定的skill复盘候选
[E5]: ../WORKFLOW_DEFINITIONS.md#按精确-id-读取原组合运行
[E6]: ../../src/ergora/review_requests.py
[E7]: ../USAGE.md#生成来源绑定的skill复盘候选
[E8]: ../../src/ergora/training_rounds.py
[E9]: ../../src/ergora/data/reference/platform/bootstrap/report/build_report.py
