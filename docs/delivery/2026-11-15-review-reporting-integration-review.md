# BR1／BR2 隔离整合：独立审查

日期：2026-11-15。Reviewer：fresh-context Agent `/root/review_reporting_combined_audit`，未继承实施会话。片：BR1／BR2 combined integration；分支 `integrate/review-reporting`，HEAD／固定基线均为 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`。先读原始要求与实际变更，再核实施记录和两份原独立报告，未沿用其 verdict。

|审查轴|结论|开放 finding|
|---|---|---|
|需求符合性／行为|approve，限本组合定义、文档、安装内容及所列实际证据|0|
|维护性／职责耦合／冗余|approve，限所审完整候选|0|

所审范围没有需要最小修正的实证 finding，没有源码阻断项。390px 原报告横向溢出仍是已记录的布局限制；本结论不把它变为窄屏通过，也不认证系统性报告准确率、厂商服务或主工作树 c1b1。

## 原始要求与完整候选

原始要求见[BR 并行计划](../plans/2026-11-15-backend-review-and-reporting.md)：指定两份 Claude Code 审查资料应进入对应 PR 审查 Skill，保持执行者／审查者后端可替换，区分 Ergora 普通结构化调用与原生命令、插件、CI 和托管服务；报告作者参考指定 HTML 文章，保留机器原件，生成来源绑定、静态自包含的阅读视图，不接管状态、执行、测量或批准。已发布资源不可改写，不增加重复调度、报告服务或 CI 矩阵。

已读根、src、tests 的 AGENTS、[组件变更协议](../architecture/component-change-protocols.md)、当前计划和本片计划／交付；采用 code-review 两轴、maintainable-project-delivery independent-review 及 ergora-codebase-quality 的规范、职责和测试接缝规则。本审查未再委派 reviewer。

完整 scope 是冻结 `review/files.json` 的 **27 文件：5 tracked 修改、22 untracked**。逐一读取变更及新增正文；当前文件和 `review/files/` 副本的字节数、SHA256、执行位均匹配清单。当前 Git 变更集合与这 27 项相同，无额外产品／测试改动。完整 patch **127,001B**，SHA256 `800083b0875dde6670af0a7f8def5e875f4299851aa43abb5efa510b9f421007`；反向 `git apply --check` 与 `git diff --check` 成功。`review/artifacts.json` 列出的 **1,024 个原件**逐项字节数／SHA256 均匹配。私有原件根为本树 ignored `.ergora/checks/review-reporting-integration/`；本报告另列，不改写原冻结候选。

27 项包括两个 1.0.1 审查根各三文件、报告 Agent 三文件和 Workflow 两文件、catalog、既有 preset 测试、三个用户手册、两源研究／计划／交付／原独立报告，以及组合计划／交付和总计划 checkpoint。两共享文件的实际合并同时保留两项能力，没有覆盖任一方 catalog 或手册入口。

## 需求符合性

[审查后端 Skill](../../src/ergora/data/presets/workflows/ergora-pretraining-review-v1.0.1/skills/ergora-review-backends/SKILL.md)第 12–26 行的能力归属与保存的官方来源及真实 driver 一致：`CodexBackend.command` 使用普通 `codex exec`，`ClaudeCodeBackend.command` 使用 `claude --print`／JSON；选择 binding 不会自动启动 native review、安装插件、启用服务或发评。Claude task-MCP 的 bare 环境凭据边界与已有实现一致。Skill 保留 backend、mode、独立会话、候选身份、覆盖和同后端回退原因，并把本地 advisory approve 与平台批准区分。

直接核 BR1 原 worktree `sources/index.json` 的 **24 项**来源原件身份；指定 overview／文章、local review、公开插件 command／manifest、Codex CLI／auth／GitHub／GitLab 及相关设置／CI 段落支持正文。当前托管 Team／Enterprise／Owner／GitHub App、额外计费、只读代码但写 PR 评论／check 的行为，与三月文章的历史 preview／估算分开；Claude 本地默认报告、fix／comment 副作用与 GitLab 条件，Codex 本地／两云平台的连接和发评边界亦分开。未发现将文档可用性冒充本机安装、订阅或实际调用的表述。

用本组合新安装的原 inspectors 直接重核两个新 manifest 和 **八份新输入**：两领域各四叶，叶仍只读；每份完整 prompt 均恰好包含一次来自 root 的共享 Skill 正文。独立旧通用根未升级，手册清楚限定继承范围。新根还原 version 并移除新增 Skill 后，与各自旧 definition 完全相等，instructions 原字节保持。

[报告 Skill](../../src/ergora/data/presets/agents/ergora-evidence-report-author/skills/ergora-evidence-report/SKILL.md)与[操作页](../EVIDENCE_REPORTS.md)把报告作者和程序 `review report` 分开；沿原 `DefinitionLibrary`、manifest、prepared input、`agent_runs` 和结果 artifact 消费。root／author 均为 read=[definitions]、write=[]、shell=false、network=[]；正文不需要联网或读取未提供的仓库。默认 Codex 可由已有调用接口覆盖，没有新增 backend 分派。四字段 JSON 是原 response 字符串内的作者约定，文档没有把 envelope 合格说成事实或 HTML 安全认证。

直接核指定 HTML 文章原件 **111,233B／SHA256 `8649db23e654ee394f94bacb4310d8d6e032272580aa5635becadc52217a6ec3`**，正文与记录的个人经验、HTML 用途和 token 取舍相符。官方 gallery 的本地 Git HEAD 为 `58c305be97f47b26b678f2c07dec01d4242268ec`，四份已引文件的字节数／SHA 均匹配；README 的虚构数据声明未被当成实测证据。静态、自包含、转义、来源／失败／反对／缺覆盖及测量身份要求是项目明确增加的报告约束，没有伪称原文证明准确率。

## 维护性与不可变身份

职责留在原定义／资源／composition／run owner，没有 Python 产品、schema、状态机、后端、依赖或 CI 变更。两个可独立导出的新根内保留同字节 Skill，是完整包所需的封装副本；长比较集中在研究文档，未散入每个叶。独立报告叶有实际 catalog／手册／CLI 消费者，不要求所有训练或优化角色承担通用报告职责。

直接复核得到：

- 原 **216 个 preset 文件**与基线字节／执行位相同；32 个旧 preset 名称保留，30 个无关条目不变。两领域仅选择新根并追加新依赖，新增 `evidence-report` 后共 33 项。
- 两领域旧 manifest 经原 inspector 接受。每领域旧完整包中的 **24 个 object 文件**在安装后库中保留全部字节／执行位，旧 index 映射仍在；**八对 old／again 输入**全树字节／执行位相等。没有把可追加的 index 文件整体要求为不可变。
- 原 inspectors 核得新 pretraining／posttraining 根 digest 为 `654b5c49875556a31e6982e33a066623106980d9bbc73366d5a45f4eaf4a118a`／`7023d0de86de0c61811b644bea6cd782057e3ee538ceba52c3c98f173b04bbca`，报告 Agent／根为 `f82e5acec681e9f23506fad1289c179bca83d2253450d8ee7de85c92fbc37008`／`67541349b69458a58be8ee9e5fc7fccbe405aba4e0f106bac29342972022c441`，与两源原身份相同。
- 依原打包边界独立比较 **663 个 source／wheel／site 产品文件**，集合、全部字节和执行位相同。wheel SHA256 为 `bd5352e7edd0e85d8c93fa9d958200757b13f385e355f92a8e4d04abed205276`。本次 `python -I -B` 实际从新 venv 的 site-packages 导入，`reference.verify()` 为 **PASS／283**；保存的 pip check 原件为通过。

`tests/test_presets.py:104` 只把已有冻结／脱离源库恢复接缝扩展为两个 profile，叶路径、role 和祖先集合跟随参数。它保护幂等安装、旧训练身份、只读权限与完整资源消费，没有新增措辞断言、测试文件或 CI。未发现需要删除的重复测试或为测试收窄有效配置的情况。

## 实际证据及限制

已直接读取两轮安装 pytest stdout／JUnit 和精确命令：r1 是 **49 passed／1 failed，70.84 秒**，唯一失败是旧 training-v2 用例按测试源码位置读取 data，而冻结输入未带原 preset data。r2 只补原 fixture，再单独运行此用例，**1 passed，2.33 秒**；不把它记作第二轮 50 项全绿。当前 r2 输入清单中是 **178 个原 tests／examples、228 个 preset data、5 个 pytest 字节码缓存**。`final-validation-check.json` 的旧 detail 标签将后两类粗计为 233；以实际 manifest 分类及交付正文的 228＋5 为准，不把缓存算原源码。这个旧私有摘要的计数标签不影响两轮真实结果或产品身份。

BR2 原真实 Codex run 为 `3a08dd0bb80448269cfe222f79ef6d15`。只读 SQLite 原记录与保存 run 相同；prepared／saved／protocol／实际 stdin 四份 prompt 逐字相同，**12,496B／SHA `a7ddda17e473b38e2008a0fe01dd521604dfc9a01056c41a4c4b23743dce129b`**。native final、native result、保存 result 和 observation 解析后相同；保存 result **12,098B／SHA `6c9b22e1486fe60758827ade6c15bcf17cbf3fd07bff1dae1debbeda3546b662`**。无 native 工具事件；原 input／prompt／result 均 available。

两视图直接等于原 response 解码字节：Markdown **3,890B**，HTML **6,181B／SHA `fc0d9bd7cf225cfa0969c0035de9fefa56920b8a673c907d6cff2d0b6a557adc`**。对照完整 S1 输入与两视图，包身份、数值、首轮失败、测试修正归属、仅摘要覆盖和所有未验项一致；未把原 BR2 的 657 文件／未安装事实改成组合后的 663 文件／新安装事实。合成显示探针作为带原换行的字面文本，没有伪造训练或性能数据。

组合浏览器脚本只服务这份原 HTML，未注入修复 CSS 或改写模型输出。直接核原 DOM／console／request 记录并视觉检查两张原截图：桌面 1280×900 的文档宽 1280；390×844 时文档宽 **460**，即 **70px 横向溢出**。两尺寸脚本节点为 0、内部锚点无缺失，字面探针保留；console 为 0，loopback 服务记录唯一 `GET /report.html` 200。CLI 的一个默认过滤 static request 不能扩大为全网络隔离。首轮 libcups 缺失导致完整 Chromium 未启动的失败仍保留，r2 使用既有 headless-shell；不称首轮通过。

本次审查实际执行的是读取、hash／字节／执行位比较、原 bundle／manifest／input inspectors、reference 校验及 Git 静态检查；pytest、安装、真实模型和浏览器运行只复核其原件，未重复执行。没有新模型调用、安装、提交、推送、平台写入、主工作树或源／测试修改；唯一新增文件为本报告。

没有验收厂商原生／托管／插件审查、Claude／异后端、通用 sanitizer、打印／可访问性、系统性事实准确率、GPU／训练／质量／性能、组合自身模板新调用或远端 CI／发布。静态 Skill 是作者指导，单次原报告不提供普遍输出保证；调用者仍沿操作页检查实际输出，并保留不合格原结果。上述边界与原交付一致，不构成本片新增产品缺陷。主控可记录本组合独立两轴 approve，随后沿原固定候选和发布门继续；本报告不替代这些后续门禁。

## README 发现入口补充复核（同片，doc-only）

日期：2026-11-15；同一独立 reviewer。仅复核新增的 `README.md` 差异及其所指的已审定义／手册，不重新运行安装、测试、模型或浏览器，也未重核原 1,024 证据件。README 当前 SHA256 为 `6a499398deee17e7702630a4574f94767a51eb1edb74ff8cb9b19cf2c2e1e30d`，与交接身份相同；相对固定基线的该文件 diff 为 4 insertions／1 deletion，diff SHA256 为 `83adf7de97411c6144794354c859ba8fbeb732f8e71ce7dd69faa3f39a89554c`。

需求和维护性均 **approve／开放 0／0**，没有需要修正的 finding：

- `README.md:18` 的报告发现行准确链接到操作页；完整提供材料、只读单叶、Markdown／自包含 HTML 和无新增采集／执行／批准权限，与已审 Skill、单叶定义和手册一致。
- `README.md:74` 的 33 个 preset 与当前 catalog 的 33 项相符，新增 `evidence-report` 确为 `proposal-leaves`；root／author 均仅 read=[definitions]、write=[]、shell=false、network=[]，没有扩大为自动采集或正式报告验收。
- `README.md:150` 链接领域手册的“选择专家和后端”，并准确区分结构化调用、原生命令、插件／自建 CI 与托管审查，未声称新增 Ergora CLI 模式或已启用服务。新增／改写行中的 7 个本地链接目标及适用 heading anchor 全部存在；`git diff --check -- README.md` 通过。

这是原组合候选之外的 README 文档补充结论。前文 27 文件候选、历史安装／运行观察、窄屏溢出、未验能力和发布门禁仍按各自原身份与范围保留，不将本次发现入口核对扩大为新的运行、准确率或主工作树产品验收。本次仅追加本报告，未修改 README、其他文件或主工作树，未提交／推送。
