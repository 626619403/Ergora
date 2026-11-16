# 优化报告 Skill／结构模板独立审查

2026-11-16。独立 reviewer：`optimization_report_skill_review`，fresh context；收到原始需求、准确基线、完整 tracked＋untracked 清单与实际验证材料，未继承作者实现对话。只写本审查记录及私有检查材料，未修改作者资源、主工作树或其他候选。

**需求符合性：APPROVE。可维护性：APPROVE。开放 finding：0。** 结论限于本片报告资源、实际冻结消费者和本地接缝；不代表原生模型报告、浏览器布局、真实优化收益、自动循环或发布验收。

## 候选与检查范围

基线／候选 HEAD 均为 `f8df8af90ae5ad2d9e64047b0b87197ce2bfb432`，分支 `feat/optimization-report-skill-r1`，实现未提交。已读本候选 PLAN、根／源码／测试 AGENTS、组件协议与[作者交付](2026-11-16-optimization-report-skill.md)。主线后继文档检查点 `b71680b` 与该基线的 `src/tests/scripts/.github/pyproject.toml` 无差异；不借其状态替代本候选实证。

审查完整 14 文件：双语 `EVIDENCE_REPORTS`／`WORKFLOW_DEFINITIONS` 四份入口、catalog、原 preset 测试接缝、作者交付、新作者包五文件及新 workflow 包两文件。私有 `candidate-files.json` SHA256 为 `52837434596ec61f5facea40e9769b1122c50c44b25a8a0576a544e54c27f700`；14 文件 SHA256、长度与执行位均独立读回一致。本审查记录不在该作者快照中。

|实际资源|版本|独立读回完整包 digest|
|---|---|---|
|`ergora-evidence-report-author`|2.0.0|`1e67f2a71986cf37601fcc5671e6f4bf5768da0749caf15019883b06186aa70c`|
|`ergora-evidence-report`|2.0.0|`7792b1d05fa3684897f82444db4e6f43dca7607ee434a56ec4596a671df47ad5`|

## 需求符合性证据

|原要求|实际实现与判断|
|---|---|
|专门 Skill、表格主导、直观比较与层次递进|[专门 Skill](../../src/ergora/data/presets/agents/ergora-evidence-report-author-v2/skills/ergora-optimization-report/SKILL.md)第12–32行与[占位模板](../../src/ergora/data/presets/agents/ergora-evidence-report-author-v2/skills/ergora-optimization-report/assets/optimization-report-template.md)依次给 scope／现状目标、源码流、冗余清单、可比 baseline／逐步结果、诊断、决定与剩余瓶颈。列数按实际指标适配，不强塞 MFU。|
|先解释算法、依赖、数据流和计算／组件／张量冗余|Skill第18–20行要求来源绑定的完整相关流程、forward/backward/update依赖、形状／dtype／layout／生命周期、图和文字／表格等价物；冗余保留证据状态、反证义务与有界检查。报告明确消费提供的分析，原 `training-flow-map` 保留分析 owner。|
|固定业务合同、可比范围与完整优化组合|Skill第12–14、24–34行要求读原约束，显式固定算法／结构／尺寸／精度等范围；不同阶段、硬件、精度或有效work分表，保留完整配置与真实前驱。组合收益绑定组合，不能造单项增益或累计不匹配消融。|
|配置、机制、吞吐、显存、正确性、MFU与实验位置清楚关联|训练表列及测量合同明确；每项自己的配置与机制、继承链、真实输出、原始样本与oracle范围可恢复。MFU口径缺失不猜值；短run、profile、结构图不充当质量或收益证明。失败、回归、unknown与缺原图均可追溯。|
|参考只抽结构，公开内容自包含|本地只读来源快照身份为user、revision1303，实际是含表格／原图的片段。公开新增内容只有通用组织规则和占位符；未发现其具体方法、实验数字／结果、图片或私有业务正文。私有来源URL／token扫描为零；14文件与片段的精确32字符窗口交集均为零，此检查只辅助排除逐字搬运，不证明语义。未新增外部读取依赖。|
|保持只读、六阶段及候选绑定证据，不开放循环|[workflow](../../src/ergora/data/presets/workflows/ergora-evidence-report-v2/workflow.json)第14–20、53–59行根叶权限均为`read=[definitions]`、无write/shell/network；catalog仍为`proposal-leaves`。来源采集、前驱运行、实验、采用与release继续由原owner持有；报告建议不是采用回执。|
|保留原 response 与静态 HTML 安全|通用 Skill 与原@1逐字节相同，保持`artifacts.response`中的`markdown/html/sources/limitations`四字段、HTML转义／静态CSP与同事实义务。新资源没有新增schema、MCP、后端、数据库或执行分派。|

## 可维护性与真实消费者

所有配置沿现有 `workflow_definitions.install_preset`、`DefinitionLibrary`、资源编译、manifest冻结与input读回路径。`definition_bundles.py`第196–214行只把Skill的`SKILL.md`作为正文；因此新`agent.json`第39–43行把asset模板同时声明为context具有真实用途，避免仅把附件打包却不送入prompt。没有重复复制器、调度器或提示专用Python实现。

版本化保留是必要合同：独立比较原33项catalog与227个旧preset资源文件，配置／字节均保持；新版本内复制原通用Skill用于保持完整独立包，属于不可变历史版本，不是新增运行抽象。新测试只扩展已有真实冻结接缝，没有按heading或逐句文案添加断言。

## 独立检查与范围

1. 源码执行原冻结接缝的新`optimization-report`参数：**1 passed, 2 deselected in 0.62s**。调用原owner安装／重装、冻结、删除live定义库后准备input并读取完整继承材料；未调用外部后端。作者原3 passed／1.77s另保留其身份，未作为本次重跑结果。
2. 对原始bundle、manifest、frozen-input、CLI结果与脚本逐项检查，并用当前源码实际`inspect_bundle/inspect_manifest/inspect_input`重新读回：两包digest、全部冻结asset字节／执行位、根与叶来源、只读权限相符。模板全文及两份Skill均在prompt；material **24,489 bytes**、prompt **24,667 bytes**。`git diff --check`通过。
3. 使用明确标注synthetic的最小原始夹具，由本reviewer在已读Skill／模板的上下文中编写一次报告行为演示，再检查四字段JSON、Markdown／HTML相同表格与缺项、静态HTML/CSP及来源文本转义。演示覆盖组合收益、缺单项消融、不同硬件／有效work分表、无MFU口径、缺质量与图像、unsupported工具、失败试次与pending决定。合成输出／输入原件均留私有检查材料，不含参考文档结果；**这是人工上下文演示，不是Codex CLI或模板后端forward调用**，不能认证模型稳定性或事实准确率。
4. 原始检查与演示产物保留在该片私有review证据中。初次引用片段比较的默认SequenceMatcher数值因autojunk不用于逐字搬运判断，原件保留，后以精确32字符窗口交集替代；无产品失败被覆盖。

本轮无模型／GPU／训练／服务／外部API调用、依赖安装、commit或push。未重复无变化大套件；作者137链接与两Python导出示例的静态结果仅作为已读作者证据，不称本次全量重跑。新安装wheel、真实原生模板输出、浏览器布局、CI、采用和发布仍按[作者交付](2026-11-16-optimization-report-skill.md)保留未验范围。没有需作者修正的阻断finding；根可据本记录更新本片审查状态，后继运行必须绑定其准确候选。

## 同片最终安装与原生调用原件接纳（追加）

2026-11-16，同一独立reviewer按根交付的终态原件只读复核，未重跑测试／模型、构建或安装。**需求符合性与可维护性均维持APPROVE，开放finding 0；本片本地资源／新core安装／此次原生报告及原结构模板的原件接纳完成。** 上文“尚未验”的新安装与原生调用项仅记录初审时状态，由本节增补；浏览器、SDK矩阵、真实业务质量、CI和发布仍未验。

### 冻结身份与实际安装

- 最终15文件快照manifest SHA256为`5b27f4e8d575e479662e08788e382892e0f3f738b94ae0eed9bbab47cc343bbe`，终态summary SHA256为`503f17edbb6376f49db2df6c14a9916b87846e34314ca683aa17d50497df5342`。追加前15文件字节／长度／执行位与manifest逐项相同，summary所列100个原件字节／长度／摘要全部重核。原作者14文件中仅交付状态改变，其他13文件保持初审身份；已读完整交付状态diff，未发现产品变化。
- 新非editable wheel SHA256为`9743064d74a72d1836570efc58dc66f8d53d00447da7cf0b060160181fdff82e`。独立逐项比较当前源码、810项固定构建输入及其staged副本、wheel ZIP原字节／执行位、实际安装文件，678个runtime文件全同，含283参考文件；实际安装文件集合也与wheel集合相等。原校验误计`AGENTS.md`的失败、初始脚本和修正均保留；修正仅改变私有verifier的runtime集合与沿原wheel恢复逻辑。
- 通过新安装自身Python，以`-I -B`真实导入`site-packages/ergora`，只读调用原reader核3份完整input及3份manifest；全部继承正文／模板均在prompt，实际`temporalio=false`、`mcp=false`。原CLI列表／导入和完整包消费原件相符，未将core安装称作SDK矩阵验收。

### 两次真实调用与原输出

|原入口与准确run|已核终态／调用记录|实际stdin与原回复身份|
|---|---|---|
|`ergora-evidence-report@2.0.0`／`root/author`，`0d21cc331ece424e963210d2231a05d5`|succeeded／exit0，149.034645秒；同新安装原CLI的text-only调用，实际Codex命令显式配置`gpt-6.1-sol`／`medium`|29,421 bytes，stdin SHA256 `1912dade8d5eef909f271191729735e0a53875c91e9ee259ad9de703e4e653e3`；原结果SHA256 `45e13b401a4d9e264fab7b2fbae71d615b716db43a39f1f5ca68f1d1f73aed36`|
|原`ergora-structure-review@1.0.0`／`root/review`，`0125866f2f144da787769f3cc711f517`|succeeded／exit0，39.446412秒；同新安装原CLI的text-only调用，实际Codex命令同上述配置；模型两轴APPROVE／无finding|354,120 bytes，stdin SHA256 `0e2c25b3161a744a1f5d1ea81c9b909b83fa416dfc4b739776d9267aed62142d`；原结果SHA256 `7d0bf68bd0712da9969feb2429c82cd16184c3af01b805f79005958e350aac7b`|

两次原始`inspect-run`观察、冻结input／prompt、实际stdin、native命令／事件、原结果逐项对应；stdin与冻结prompt逐字节一致，完整task及所有祖先资源在场。结构模板实际stdin还含19个完整scope文件共298,466 bytes、完整tracked／untracked diff及实际证据摘要，逐文件核摘要与全文入场；它读的是当时的原作者交付和初审记录，没有冒充已读后续状态。两次实际backend均为Codex，未称Claude或异后端通过；调用均不授予正式执行权限。

直接从原response字符串解码四字段，导出的Markdown／HTML与原payload相同；独立解析确认5表共68单元格在格式归一后完全对应，检查静态HTML、CSP、无event handler／主动URL／外部资源引用及来源脚本文本转义。另人工逐项对照synthetic原任务和两视图：组合收益只归完整组合，单项消融／质量／MFU口径缺项、scope B不可比、原图／profile缺失及采用pending均保留；模型还保留了夹具输入形状与有效更新work映射不明的缺口。未发现把合成数字当真实测量或把源结构当运行成本的主张。

已读两次原生stdout事件，各只有agent message，没有模型工具执行项。两次各采样到2个自有进程，原记录终态均无remaining identity；本reviewer再次以PID／starttime核4个已采样身份均不存在，结论只覆盖这些身份。

### 保留边界与记录版本

这一次真实模型报告调用扩展了初审的人工作用演示，仍只证明该synthetic夹具的单次调用及检查到的输出属性，不认证模型稳定性、事实准确率、真实训练／GPU／benchmark收益或浏览器布局。原结构模板APPROVE作为模型建议与本独立原件接纳分账。SDK矩阵、服务、真实业务训练、采用、发布与该候选自己的CI继续开放，由根按实际后继结果记录。

最终freeze和两次调用保存的初审报告SHA256仍为`b2faf6b070e2d6250349b08c658c18970965da8e47f58145e790e6830330b115`；本节只追加到该报告，旧前缀字节及所有冻结原件保持，不覆盖旧manifest或称旧摘要能代表追加后的报告。追加后新报告摘要单独交根记录；本轮没有新的产品修正或未关闭finding，不为纯状态记账递归审查。
