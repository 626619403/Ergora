# 证据报告生成：独立审查

日期：2026-11-15。审查者：fresh-context Agent `/root/evidence_report_generation_audit`，未继承实现讨论。片：BR2；工作树 `.ergora/worktrees/report-generation-guidance`，分支 `docs/report-generation-guidance`，HEAD／基线均为 `f00bfdfd15173ceb0e961681679d6d3d62254bed`。授权为只读源码／原件，仅写本报告。

|审查轴|结论|开放 finding|
|---|---|---|
|需求符合性|approve，限本地证据报告候选及所列实际验证范围|0|
|维护性|approve|0|

所审范围内未发现需修正的可达缺陷。该结论覆盖新增窄报告作者、原有消费者接入、证据留存及公开说明；发布、安装、异后端和系统性准确率仍有下文列出的未验范围。

## 精确范围与依据

原始要求是盘点总结／报告 Agent，参考指定 HTML 文章，用子 Agent 辅助报告生成并写任务计划；既有领域角色保留其职责，新增只读 `evidence-report` 单叶／Skill，保留机器可读原件，HTML 不接管原状态或批准。训练预算生命周期属于其他工作树，本候选没有纳入其变更。

完整候选为 3 个 modified、9 个 untracked 文件，逐一读取并重算身份：

- `docs/WORKFLOW_DEFINITIONS.md`、`src/ergora/data/presets/presets.json`、`tests/test_presets.py`。
- `docs/EVIDENCE_REPORTS.md` 及 `docs/{plans,delivery,research}/2026-11-15-evidence-report-generation.md`。
- `src/ergora/data/presets/agents/ergora-evidence-report-author/` 下的 `agent.json`、`instructions.md`、`skills/ergora-evidence-report/SKILL.md`。
- `src/ergora/data/presets/workflows/ergora-evidence-report/` 下的 `workflow.json`、`instructions.md`。

ignored 原件根为 `.ergora/checks/evidence-report-generation/`。`review/complete.patch` 为 52,374B，SHA256 `2b22aaa3ed135dc44f5cd6721dd951763f5ac0a72f92e625fd225d516b4e9fd3`；`review/files.json` SHA256 `a86583bd2dd667419194e7959124dad33b4ced254401b7bdd5e0d078f7602048`。12 份当前文件均与该清单的字节数／SHA 一致，本报告另列，不改变原 scope。

已读根、src、tests 的 AGENTS、组件变更协议及当前 `docs/PLAN.md`，并应用 maintainable-project-delivery 的 independent-review、ergora-codebase-quality 的职责／测试接缝、writing-for-agents、skill-creator 规则。该分支明确由主协调者维护统一排期；本片的独立计划与交付记录存在，没有把其他片的验收当作本片结果。

## 需求与维护性判断

基线 Git 对象独立盘点为 31 个 Agent 包、49 个 Workflow 包，含旧版本。检查其描述、专长及相关完整指令后，训练 flow-map／performance／measurement、三类 retrospective 的用途与研究表一致。`review_requests.report()`、`training_rounds` 和 bootstrap renderer 的真实消费者也支持文档对程序报告／索引的区分。新增通用作者具有具体发现入口、独立 `root/author` 和已有 CLI 消费者，未再建调度、渲染、发布或持久状态 owner。

新 Agent／Workflow 经原只读 inspector 重核，digest 分别为 `f82e5acec681e9f23506fad1289c179bca83d2253450d8ee7de85c92fbc37008`、`67541349b69458a58be8ee9e5fc7fccbe405aba4e0f106bac29342972022c441`；Skill 完整目录 digest 为 `42968e4a057ce46801f45105b1b122bb3e2640540c846360da915ef3955d292f`。Skill 只有一个自包含入口，描述与报告任务匹配，输出使用原 `summary/artifacts.response`，四字段内容被明确说明为作者约定。调用者没有因 envelope 合格就获得事实验证或批准。

沿 `workflow_definitions` 的资源合并、祖先权限／引用准入、manifest 完整树、输入编译，以及 `agent_runs`／`agents`／Codex backend 检查实际路径。原 manifest、prepared input 和保存的 run input 均经当前原 inspector 重核；实际图只有 root 与 author，grant／root／leaf 均为 read=[definitions]、write=[]、shell=false、network=[]。实际 prompt 含 root 指令、author 指令及完整 Skill 三份资源；祖先来源为 root、root/author。Skill 无额外附件，text-only 内联可覆盖其完整材料。原实际 argv 禁用 shell、web、MCP／环境 Skill 等读取入口，原生 stdout 没有工具事件；现有后端对宿主隔离的限制仍如实保留。

测试改动扩展既有冻结接缝，检查真实导入幂等、旧训练身份、角色／权限、完整继承与移走源库后的输入恢复，保护实际边界，没有新增提示措辞测试或重复框架。原 r1 XML／stdout 明确为一个通过、一个失败，失败行仅将新叶祖先写死为 root/map；r2 为两项通过、38 deselected、pytest CLI 4.62 秒。重建 r1 与当前测试只差该集合一行，原 traceback 支持此归属；r1 仍只具有“失败后重建”的身份，没有运行前冻结源码证明。XML 的 4.353／4.115 秒与 CLI 的 4.90／4.62 秒口径区分正确。

独立对基线逐项比较：32 个旧 catalog 条目语义及 216 个旧 preset 文件字节保持。657 个实际源码包文件与 wheel 文件集合／字节均一致，`source-manifest.json` 的全部 657 项匹配当前源；wheel SHA256 为 `3a95563aa38b1a6bdb79357bec630112718f705a3843995531319c911c833429`。当前 `reference.verify()` 再核为 PASS／283。解包 wheel 的既有隔离导入观察支持发行内容可读，文档准确保留“没有新应用安装验收”。

## 一手来源与真实报告链

直接核指定网页原件 111,233B／SHA256 `8649db23e654ee394f94bacb4310d8d6e032272580aa5635becadc52217a6ec3`，独立 HTML 文本解码与已保存全文除空白外一致；研究对个人经验、token 成本、报告用途与上下文能力的归属准确。HTML 200、Markdown 403、GitHub API 限额 403 原观察分别保留。本审查未重新请求网络或 API。

官方 gallery 本地 Git HEAD 与四份所引文件均匹配固定提交 `58c305be97f47b26b678f2c07dec01d4242268ec` 和记录 SHA。README 明确 sample data 全为虚构；status／incident 无 script，feature explainer 有一个内联 script。研究区分这些原例与本项目静态选择，Skill 明示虚构数字不是实验事实，真实验收样例也没有使用 gallery 数字。

真实 run 为 `3a08dd0bb80448269cfe222f79ef6d15`。以 SQLite `mode=ro&immutable=1` 读取的原记录与保存 run／observation 一致；原状态 succeeded，CLI command 原件记录 89.083525 秒。原记录、完整输入、实际 stdin 与模型输出逐项核对如下：

|原件／派生物|直接复核结果|
|---|---|
|完整 input|digest `bc26f668b7ad71c23fbe7e0b6bb49d39e6ff9283a6af2556b4f07e0645569abd`；prepared／saved 图和请求相同|
|prompt／实际 stdin|prepared、saved input、protocol、实际 stdin 逐字相同；12,496B，SHA `a7ddda17e473b38e2008a0fe01dd521604dfc9a01056c41a4c4b23743dce129b`|
|native stdout|13,076B，SHA `915c3d83e0d79200997d3b07afd72109ea537e7c9ca3914115659bc4d8fe2aeb`；一条 commentary 与一条 final，final 解析结果等于 native protocol result|
|native protocol result|12,094B，SHA `59df549ce27f3b501dc2c9dbaab39e9236075959b1dbd83273263b0971079acd`；与保存 result 解析后相同|
|保存的原 result|12,098B，SHA `6c9b22e1486fe60758827ade6c15bcf17cbf3fd07bff1dae1debbeda3546b662`；原 schema 合格，SHA 与原 run／observation 相同|
|response 原字符串|`views/report.json` 11,670B，SHA `140f61fd910fb3eba5878e5ca30cf84c8cd264f1f6c9c4416fc0067e7e279e11`|
|Markdown|3,890B，SHA `1feb15884bfe36d50fc8505b58e7cdcbb8de57d5bda1646389e3823587933db5`|
|HTML|6,181B，SHA `fc0d9bd7cf225cfa0969c0035de9fefa56920b8a673c907d6cff2d0b6a557adc`|

三份视图字节分别等于原 response 字符串及其 markdown／html 字符串的 UTF-8 编码；没有手写 HTML 或改写内容的迹象。native 与保存 result 的封套 JSON 序列化不同，response 内容相同。

实际任务完整内联 S1 JSON，原字节 SHA `fd512a5d22d7ff611830c728b92981ffc4b38dd126f2efbe299227060de8287c`。作者的来源表、两视图和 limitations 均明确只读操作者摘要、未读底层源码／XML／wheel、未重算身份。人工对读确认包身份、检查值、r1 失败及测试修正、所有未验项一致；秒数保留为记录耗时，没有构造成性能比较。合成探针两视图均保留原换行与字面值，且清楚标为合成显示文本。

独立 HTMLParser／原文检查覆盖本次 HTML 的 124 个标签：无 script、事件处理、主动表单／嵌入对象、外部资源、CSS import／URL；存在限制性 meta CSP，内部锚点可解析，探针作为文本保留。此为本次静态产物检查。原 offline-reread stdout 与 observation 相同，19 个原 run 文件在本次复核前后 SHA 保持；本审查没有再调用模型。

## 实际检查与未验范围

审查实际执行了当前源码只读 inspectors、基线字节／catalog 对比、完整源码与 wheel 对比、reference.verify、Skill quick_validate、独立结果链／静态 HTML 校验、70 个当前本地 Markdown 链接目标与 `git diff --check`；全部通过。原 r1／r2 pytest、CLI、解包 wheel 导入和无凭据原件重读通过阅读留存原件复核，未重新执行这些带写入的流程。本次临时内存核对脚本曾修正校验 API 参数及将 commentary 误计为 final 的检查假设，最终完成原件比较，未修改产品或原件。

Claude／其他后端、新应用安装、浏览器布局／打印／可访问性交互、系统性事实准确率、GPU／训练／正确性质量／性能收益均未验；未重复昂贵模型调用、安装、提交、推送、评论或发布。HTML 输出约定与模型事实准确性仍需调用者按原操作页检查；一次小例不提供通用 sanitizer 或准确率保证。模板当前属于未提交的本地候选，未取得其自身远端 CI／发布结论。

需求与维护性没有阻断 finding，无最小修正要求。主协调者可将本独立结论记回本片计划／交付；统一排期、固定候选与后续发布仍由其原流程处理。
