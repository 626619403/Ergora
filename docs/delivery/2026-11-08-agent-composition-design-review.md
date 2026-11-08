# AC0：Agent组合研究、设计与文档独立审查

日期：2026-11-08。评审者：fresh-context独立代理`agent_composition_design_review`。项目及文档根为Ergora及其`docs/`。本次收到原始需求、固定基线、12文件清单和实际检查范围后独立审查；未参与作者的设计过程。

**需求符合性（Spec）通过，范围内0项发现；可维护性（Standards）通过，范围内0项发现。** 结论适用于AC0研究、设计及文档修正。AC1–AC6的代码实现、真实装载和运行验收仍按各片出口完成；本报告不接替F6.1的精确交付终结。

## 范围与固定身份

基线及实际HEAD均为`b1dbe48a1b14e8e2ec59d4f44e30b2ea367fa1fe`，分支`refactor/architecture-foundations`。7个tracked文件检查了完整差异及受影响上下文；5个新文件全文阅读。源码按必要调用链只读检查，没有把此前全面源码评审的结论预设为本次设计通过。

冻结清单`review-scope.json`的SHA256为`63207c4209ac5028b564fc11b1b831c48f615fe46b400258cb377c97c911bbc8`；`review-tracked.diff`为`1436c4727b06adebd9f2f46a20fd839a3749a2074d44bde0a86a4bbad95557c5`。二者位于本地`.ergora/checks/agent-composition/`，不作为发行资源。本次重新计算全部文件身份，并确认实际tracked diff等于捕获文件。

|文件|字节|SHA256|
|---|---:|---|
|`README.md`|36327|`237dfd086a7e9ce53dcf5249c0b0591ae9d8cb4150e056f229b859c604aaf9d9`|
|`docs/INTEGRATIONS.md`|15062|`901bf225be8a2f7eeeacfc2ab4005491ef1e05d15276e73ea9bf7729e20efa8b`|
|`docs/PLAN.md`|67677|`8e217909449de362136987540d977fb424ba3ef9eb4fe09eca07b93a3506215e`|
|`docs/architecture/current.md`|33458|`ad7cafcf930293e108e3f82063c9abadbfb89fd6d3695bf772848cefd396c1c7`|
|`docs/architecture/decisions/0004-agent-composition.md`|11816|`9aa67fd1b0b51670332c38c852e76f19bdc77a54e2fae70a5b674ef56da1f99f`|
|`docs/delivery/2026-11-05-editor-comparison-review.md`|18645|`14f87990ee091fb85df05adfee08d9ac9b5afd2e9c67682f10ba9b581bf5aee2`|
|`docs/delivery/2026-11-08-agent-composition-review.md`|32191|`21153d3ff34f72355b1064ca0c3cc4aa600f52a5393514aac529bcd79d92e412`|
|`docs/plans/2026-11-01-all-in-one.md`|71867|`277bcfb388e610cebaa9d991fbf0cc64c1b9546378bf4bc55e518aaa24be4c9e`|
|`docs/plans/2026-11-05-low-code-editor.md`|6948|`ec6c47a49830fd0aa383bb358738699f815cf3d8321b02522b2bcd2bacf9f5a2`|
|`docs/plans/2026-11-08-agent-composition.md`|10165|`ca7fc11595f8ba17613ed5eda561e286ba7b319aa065b800294ef95acfa60833`|
|`docs/research/2026-11-08-agent-composition.md`|16142|`8b1719a59f7d1cdf6036b364bf4366e26ca0dc3045ec32d2aca9a53ed3e7fffb`|
|`docs/research/sources/2026-11-08-agent-composition.json`|12702|`994cab49e2f9c13812d425c8fffa0d91c0bba95ce2b587be639b62116599d992`|

已读项目`AGENTS.md`、AIHERO索引、`code-review`、`codebase-design`、`maintainable-project-delivery`及其`references/independent-review.md`。检查按需求与维护性两轴分别形成结论；文档切片使用固定工作树差异和新文件内容。

## Standards轴

范围内无发现。领域对象的职责分别落在职能、定义、成员分配、实际运行、后端adapter及冻结manifest；现有多个后端是实际变化点，AC2的局部interface有具体消费者。命名专家采用数据包而非新增类，公开字段仍由组件描述拥有，未提出一个混合全部工具家族的注册框架。

[ADR0004](../architecture/decisions/0004-agent-composition.md)第73–89行及[AC计划](../plans/2026-11-08-agent-composition.md)第20–29行将资源装载、有效授权和摘要准入安排在正式多成员执行前；新版本桥接须先设计再编码。各片指向已有所有者、说明可验收出口，并保留旧run读取/恢复和单binding兼容。F6/F8/F10/D1的调整通过AC节点归属，没有同时引入第二套持久调度或把页面实现混入本片。

当前schema字段细节和新admission envelope桥接仍是AC3的待完成设计工作，记录清楚，未以本ADR作为可导入配置或实现验收。后续各片应继续核这些实际出口。

## Spec轴

范围内无发现。独立核对的重点如下：

|要求|实际核对与判断|
|---|---|
|当前与未来分开|README、当前架构和ADR均明确当前一角色一binding，新增组合尚未实现。全面源码评审的139项检查和283冻结身份仍绑定b1源码，未转作新设计的运行证明。|
|独立定义与互补成员|ADR第15–24、43–57行分别定义职能、AgentDefinition、成员、run与backend；专长在提示、Skill/资料及工作/覆盖分配中体现。示例覆盖kernel执行与结构/正确性审查；同职能可多实例，数量受真实资源与工作分配约束。标签不授予权限或构成质量证明。|
|后端策略可执行|ADR第59–61行在准入时比较解析后的实现家族，分别记录模型/提供方未知值；`prefer-distinct`展示同后端原因，`require-distinct`拒绝不满足配置，已冻结任务不因超时静默换后端。保留用户已有绑定和每成员预算。|
|权限、MCP及Skill真实装载|ADR第73–79行区分请求、授权上限、adapter可执行保证及实际装载，必需能力不满足时明确拒绝。冻结完整Skill树/来源，区分原生加载和文本参考；明确`stage_driver`忽略ambient配置的现状。AC3b要求Codex/Claude受支持路径的真实装载与拒绝证据。|
|原可信合同与多审查|ADR第57、65–69、87–89行保留单checkout写所有者、同候选审查、作者参与/session/委派来源排除、全部mandatory通过及原始finding。manifest摘要进入创建/批准准入，旧run不按当前活动版本重解释；监管者建议不获得可信批准权。|
|研究准确及限制可核|六个新框架的固定源码和六篇论文均给出读取范围；缓存身份与清单相符。抽查的接口及方法/限制支持研究中的对应摘要，未将论文数字或转载实验推广成Ergora效果。知乎/公众号未取得正文、转载未逐字认证、旧DeepSeek固定研究复用均有明确标注。|

Q-2公开手册修正可在文档范围关闭：[INTEGRATIONS](../INTEGRATIONS.md)第9–11行现在说明默认只读、显式override、当前容器/用户权限、有效binding查看入口及普通调用与正式外层monitor的分别。其内容与`agents.py:87–98`、`agent_runs.py:39–58`、`projects.py:46–65`及`reference_executor.py:83–86`一致。S-1与Q-1仍是AC1待修的源码发现，当前文档没有将它们关闭。

## 实际检查与限制

|检查|结果与实际范围|
|---|---|
|基线、分支、完整diff及12文件字节/SHA|全部一致，无范围外生产变更。F6旧审查者的追加按原证据保留，没有继承为本设计通过。|
|独立只读静态检查|对冻结清单中的11份Markdown重算412个本地文件/锚点，缺失为0；当前`src`的CLI parser接受30条README命令；`git diff --check`通过。未执行原静态脚本的文件写入段。|
|来源JSON及22缓存身份|解析成功；全部bytes/SHA在本地缓存匹配。摘要身份只证明字节，另做下列语义抽查。|
|六框架源码|定向核OpenAI Agent/MCP/as-tool，ADK模型/指令/子实例父关系/并行分支，LangGraph StateGraph/compile/context，AutoGen AssistantAgent与Team成员唯一性/终止限制，CrewAI配置及弃用字段，AgentScope构造和同成员串行/跨成员并行。未逐行等深审计这些文件。|
|论文与转载|从固定HTML抽取并核MAST非穷尽分类/不显著干预、AgentPrune适用条件与成本、AFlow数值评价/验证测试划分及review负收益、Puppeteer固定集合/终局奖励限制、MT-Bench self-enhancement保留结论；核转载的合成消息/时间替代编码与mock Worker。另经网页工具读取[固定Cordis v1](https://arxiv.org/pdf/2608.25512v1)的逆操作责任、外发副作用及外部沙箱限制段，与摘要相符。|
|当前调用合同|全文读`agents`、`agent_runs`、`bindings`、`stage_driver`、`reference_executor`，并定向核有效配置/CLI、原workflow作者/context及activities候选/审查门禁。源码保持只读。|

本次未安装依赖、调用真实模型、启动服务或浏览器、运行GPU/竞品/Windows、修改Git或外部状态。未复现论文、逐页审核Cordis证明，未独立认证转载与原文逐字一致；复用的DeepSeek与OpenHands/Forge旧研究未逐文件重新获取。此前139项源码检查及283文件身份没有重复执行，也不作为组合功能已交付的证据。

本报告是唯一写入文件。上述静态计数针对表内冻结的12文件，不包含本报告或随后状态追加。AC0归档仍需主代理同步处置和状态、刷新最终完整范围/静态，再按既有计划完成普通提交推送及远端核对；无新增阻塞finding。

两轴计数：Standards 0；Spec 0。旧源码S-1/Q-1保持待AC1，Q-2文档修正已核。

## AC0普通候选身份及归档复核

2026-11-08，同一评审者从Git对象固定核对普通候选`0f8e2a98dbfa42ea96657ef80fbf2bc356f57abe`。**候选身份、最终静态和审查后状态归档通过；精确CI仍待实际步骤核对，AC0交付终结暂保留pending。** 工作树随后开展的AC1.1代码不在本次范围。

候选唯一父为`b1dbe48a1b14e8e2ec59d4f44e30b2ea367fa1fe`，恰改15文件，集合及每个blob的bytes/SHA均等于本地`final-scope.json`。清单2,720字节，SHA256为`10e322b80fdb899cf0d31d45c7b05ce585e11d0c0dd92203b0345c3111c8c011`。`final-tracked.diff`仅捕获原已跟踪的8文件，30,347字节，SHA256为`fa877548e147e4a81d00db962a2a0671e7fe68f351bed4797eae4f26fceb1eb5`，逐字等于这8文件的实际Git差异；另7个新增文件从候选对象逐项核身份和内容。`src/`、依赖、tests和CI相对唯一父无差异。

与首轮审查相比，README、INTEGRATIONS、当前架构、ADR0004、研究正文、来源JSON及原F6评审追加保持首轮字节身份。本报告在候选中为原8,958字节，SHA256仍为`ae54ad88dd0ae9040949ad05acf7bbc6ae2b20025218f21a1ee7c8998dee7851`。其余变化逐项核为Q-2关闭、独立设计审查和F6.1终结、静态及交付状态的归档；六阶段、权限/资源准入、互补分工和后端策略没有改变。

共享源码报告仅修改作者回应中的Q-2关闭状态并追加归档；将这些状态变化逆向还原后，原32,191字节的完整SHA与首轮一致，原独立工作区保留。AC计划的状态行和末尾记录以同法还原为首轮10,165字节/SHA；三个既有计划的首轮内容从基线加原diff在内存重建，摘要一致，再逐项比较候选追加。新F6终结报告已全文读取，其结论绑定b1/原CI，主代理据此更新F6交付记录和节点；它没有扩大本AC0或新组合的实施状态。

独立从候选对象重算14份Markdown的434本地文件/锚点，缺失为0；30条README命令与最终静态记录相同并通过parser，parser源码字节与候选一致；22份缓存来源身份匹配候选来源JSON，`git diff --check b1dbe48… 0f8e2a9…`通过。最终`static-documents.json`的14文档集合及全部摘要均等于候选blob，文件4,150字节/SHA256 `d8b8d98f0a8c681e9b8df7f4a1bdb92ad6f3fae9f61ef847dc9f59126209616b`。这些计数绑定候选中尚未追加本节的报告版本。

已读主代理普通push/远端原记录：exit0，2026-11-08 13:02:35.595869 UTC远端分支为完整0f8候选。该时点属于主代理记录，本节尚未作新的独立即时远端查询。来源JSON在原push检查范围内，当前没有据Markdown过滤或其他候选的成功推断本候选CI成功。取得该候选两OS实际必要步骤及后续独立核对后，再追加同片终结。范围内无新增Standards或Spec finding。

## AC0精确CI、独立远端与完整终结

2026-11-08，同一评审者继续固定`0f8e2a98dbfa42ea96657ef80fbf2bc356f57abe`，重新从Git对象核15文件集合及全部blob身份，仍与上述final-scope一致。**需求符合性、可维护性、普通候选身份、最终静态、精确双OS必要CI步骤及独立即时远端核对均通过；AC0研究/设计/文档片可登记完成，无新增finding或未解决交付阻塞项。** 上节CI pending现由以下实际证据关闭。

本次直接解析官方最终run/job HTML，并对照候选内`.github/workflows/portability.yml`，没有仅采用主代理汇总JSON或总体Success。`ci-html-status.json`所列6份来源的bytes/SHA全部重算一致；三个关键原页面为：

|来源|字节数|SHA256|
|---|---:|---|
|`ci-run-latest.html`|157,527|`04e831df7997443bdaf13bc3db92778f0a87c0bb56e0da7682c9a5231d87d0ea`|
|`ci-job-128738902396.html`|160,168|`0ed5d220cdaba65ab33a23076d44f085751b6b0654eb8b28c2386f3e94e27122`|
|`ci-job-128738902829.html`|162,076|`7a38efa18151131a76729b23ac130acf096339ccc50450c45676dbc70b4a27fc`|

[Portability 42483036401](https://github.com/626619403/Ergora/actions/runs/42483036401)的原run页面含精确候选commit链接及Success；run选择原记录同时绑定完整候选、run ID及该workflow。两个job均有各自的最终HTML、对应`selectedJobId`及run引用。逐项核`check-step`状态、完成标记和成功步骤日志URL，结果为：

|必要步骤|[Windows / Python 3.12 · 128738902396](https://github.com/626619403/Ergora/actions/runs/42483036401/job/128738902396)|[Ubuntu / Python 3.11 · 128738902829](https://github.com/626619403/Ergora/actions/runs/42483036401/job/128738902829)|
|---|---|---|
|4 · Build and install wheel|success|success|
|5 · Packaged reference identity|success|success|
|6 · Native application regression|success|success|
|7 · Windows PowerShell 5.1 installer and upgrade|success|skipped，符合候选的Windows条件|

每个必要成功步骤的原日志URL均精确为`/626619403/Ergora/commit/0f8e2a98dbfa42ea96657ef80fbf2bc356f57abe/checks/<对应job>/logs/<对应步骤号>`。Windows全部10项success；Ubuntu9项success，仅上述Windows专用项skipped，无失败、取消或超时。已读`verify-ci.py`的逻辑，未执行其写JSON动作；本次没有重跑CI或逐条下载全部控制台日志。

随后复用已授权的`push.py`每命令SSH设置，独立实际执行只读`ls-remote`，exit0、耗时4.499秒。**2026-11-08 13:20:13.555710 UTC**返回`refs/heads/refactor/architecture-foundations`的完整SHA为`0f8e2a98dbfa42ea96657ef80fbf2bc356f57abe`，与固定候选一致。认证值仅在内存供该命令使用，未输出、落盘或修改；未推送、强推或更改配置。这是该明确时点的远端事实。

本次唯一写入为本报告的同片追加，候选中原报告与上节复核记录均保留。AC1.1工作树代码没有进入本次检查、静态或CI结论；S-1/Q-1仍由其各自实现片修复及审查。新组合、真实MCP/Skill装载、不同后端质量/速度、GPU及其他前述未验范围继续由AC后续节点承担，AC0完成不变更这些实施状态。
