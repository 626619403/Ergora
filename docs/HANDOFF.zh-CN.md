# Agent 工作交接

[English](HANDOFF.md) · 简体中文

更新于2026-11-16。本文件交接仍在进行的工作，不代表发布或项目全部完成。修改前先读根 [AGENTS.md](../AGENTS.md)、[PLAN.md](PLAN.md)、本交接的一种语言版本和相关交付最后进度，再核Git及实际进程；历史证据保留自己的候选与范围。按索引读取当前片，不要一次载入全部历史docs或递归扫描整个 `.ergora/` 占满上下文。

## 接续检查点 — 2026-11-16

最新已核公开提交 `e5a35558f29f11eed62c6dd28450da6d39f232df` 已普通推送并核远端完整OID同一。它自己的Portability run **43840394544已终态8/8 success，含Windows**；官方 `publication-r2/checks-web-32.*` 与latest快照绑定完整head、8个唯一job IDs和原生success标签，有界观察器0结束。产品src仍与 `6cec589f404b17f4828a70807d5e33d89fad3fa0` 逐字同一，仅有另片已审3行测试修正0478a6d、普通合入99c8503。原7fc/run43833234533的Windows失败与此前API403观察记录均保留，准确证据见[联合交付](delivery/2026-11-16-design-capacity-integration.md)。

S1原17受影响节点新安装通过，新fresh独审关闭F1/P2。V2b新安装41节点及两场N32均过，每场66分支；两个原结构模板都以已授权Codex回退完成。联合wheel `20068f1a…` 的core／SDK各669runtime文件同一，283参考、依赖及**联合32项／135.20秒**通过。709采样自有进程终核absent，2095份tracked输入与两安装未变。真实Temporal、完整M1c、晚期reader、CPU／GPU质量仍分别验收；设计执行、可信新自然人决定和schema3效果继续关闭。

PROJECTS82c1c84、WINDOWS13ea479、USAGE完整1272行73b7d61与后端指南2273a50均随核远端一致的文档227发布。B3四完整pair已各自全文／source／parser检查及新fresh两轴approve／0；Agent定义46017e1和工作流31ce9a3已提交未推送，最后137行模板入门七文件无finding、已提交d73de13。早先证据归因、history预算、actor归因P3均同片复核关闭。B3内容／验证／独审门已闭合，全部已随核远端一致的9f3发布；停止新B4作者工作直到根后继，B4–7仍开放。后端研究保持已审，统一fixed／preset／planner／automatic调参仍待后继。

S2 R2准确候选 `2ae107b84a3c928fc8c6e2b97820951af34c0cdb` 已单次源码123过、新安装41过、core／SDK各671完整identity／283参考／依赖过及原结构Codex模板APPROVE。同一fresh源码reviewer关闭F1–F3并独立读最终运行／身份／进程原件，两轴approve／0；R1 request-changes／112并集／安装30过与原反例分别保留。根普通合入 `2ff004d4c2c62c42c76928de96915b90837b54f7`，SRC treef6b71a4…同2ae、task_plan测试同一、e5 Windows修正保留，无merge-edits。窄双语source操作USAGE增量也已同一reviewer核approve，旧整guide字节不动。准确9f3e693498834f071cf20d0f25c18555554765f1已普通推送并核远端完整OID，自己的run43867345323首次1成功／7 in progress，终态待核，不继承e5绿；未添加默认seed producer，可信新自然人／F-J-G／真实Temporal/server／Windows／GPU／schema3效果等边界保持。准确候选和全部负结果见[S2交付](delivery/2026-11-16-design-source-journal-s2.md)。

文档2273a50ddd0a1f3474e502b151cf12da0d0d3b22已普通发布并核远端完整OID；自测试e5起均为Markdown变化，原workflow paths-ignore使本次无新适用产品CI，e5自己的8/8保持原身份。Agent定义已审七文件已提交46017e18095559a57a7d1fad5d0f64ffc06a0b6e、随9f3已发布；工作流／入门指南分别保持独立审查／发布状态。

接续以[PLAN](PLAN.md)和各交付当前段为准：先发布已审USAGE／状态文档，修正并重验S2发现，再继续原晚期reader／真实服务／CPU和文档后继。**以下各节保留原04af234交接快照**，其“待做”等只指当时；不要据此重复已完成的17／N32／模板。

## 原恢复快照 — 04af234

从Ergora仓库根目录运行：

```bash
git status --short --branch
git log -5 --oneline
git worktree list
```

主工作分支为 `refactor/architecture-foundations`，本轮已核HEAD及最后核验的远端完整OID均为 `04af2344239306cb00458e89f81258093235f049`，其中已接纳联合产品为 `c540939d3b3f38f3851b0de965c9cd0f969eea77`。本页所述后继内容目前仅在本地，**尚未合入或推送**。默认分支是用户已设置的 `main`，其功能基线不同，不自动合main、不强推。

主checkout有未提交文档：已审双语指南、待语义独审的研究、进度更新及本交接文件；产品变更均在独立worktree。不要 `git add -A`、reset、覆盖其他作者文件或删除工作树。交接时共有41个工作树，包含历史／冻结证据；这不表示41个Agent在运行。

本阶段参与的5个子agent均已结束并停止写入，**活跃子agent为0，本阶段自有测试／模型／训练／服务命令也没有留在后台**。未审计或停止其他owner进程／服务。中断前的N32安装命令没有启动pytest或产品子进程，重跑前先读下文。

本地交接清单及可恢复文档快照在 `.ergora/checks/agent-handoff-2026-11-16-r1/`。它与所有 `.ergora/checks/`、`.ergora/worktrees/` 均为Git忽略的本机证据，不在GitHub。换机器需另行复制所需原件，或按完整patch重建准确候选。venv是安装证据，不是可跨机器直接搬用的环境。本次没有新建远端候选分支。

## 建议接续顺序

1. 在 **b28cd31** 闭合WA5-S1剩余回归／审查，不能继承旧绿：新安装运行原17个受影响节点，独立复核native-resolution F1，再用Ergora自身结构审查模板。P2须独立复核后才能关闭。
2. 在 **919a380** 闭合M6-V2b：用绝对可执行路径、新证据label，在新wheel安装运行两场N32，再跑原结构审查模板。源码独审及其他41个安装节点已过，N32安装结果仍缺失。
3. 显式stage已审首批文档并发布。先独立审查新后端参数研究，再在原配置／冻结边界设计四模式推理策略；当前不能把预设／自动选择写成已实现。
4. 代码候选各自过关后，普通集成到开发分支，构建／核必要联合安装，普通推送，核精确远端及该候选自己的CI；旧绿不能认证新代码。
5. 接续既定S2设计审、训练晚期reader／真实服务／CPU验收、可信非Agent节点、剩余双语批次，再按PLAN做一般Repeat／混合工作流执行，不新建第二调度器。

## 准确产品候选与证据

### WA5-S1：首次设计policy登记与v1兼容

|事项|身份／路径|
|---|---|
|最新固定产品|`b28cd316b63bb788c502a026f1ec971d5572242a`，`.ergora/worktrees/design-policy-registration-fixed-r4`，detached且干净|
|直接父产品|`80cb39cbc29b7e800a2dfefb09538732eecb5a68`，其原产品基线为 `c540939…`|
|作者冻结树|`.ergora/worktrees/design-native-resolution-receipt`，分支 `fix/design-native-resolution-receipt`；不再直接修改此冻结树|
|R4完整四文件patch|`.ergora/checks/design-policy-registration/native-resolution-fix-r4/source-final/complete.patch`；SHA256 `b374940f18021853aad15160bd5ccd6736a2cc67337b192f4db3248f25566809`|
|R3完整14文件基础|`.ergora/checks/design-policy-registration/fixed-r3/source.patch`；SHA256 `bbebaaa0435e7f5af8743ae597909723c3781387e083908dec91e0b23cd38af2`|
|新wheel／安装|`.ergora/checks/design-policy-registration/package-native-resolution-r4/`；wheel SHA256 `9736406796a6f2272cffdef1a878198a978c6d0bc5a4a1d0f80acd8cbd865040`|
|已装解释器|相对该片checks目录的 `package-native-resolution-r4/venv-r4-{core,sdk}/bin/python`|
|最新交付／开放审查|[交付](delivery/2026-11-16-design-policy-registration.md)、[v1兼容独审](delivery/2026-11-16-design-policy-registration-v1-compatibility-review.md)|

开放F1由两个真实安装反例证实：mutable native项目映射丢失时，新preclaim检查旁路了旧FAILED回执／poll owner。R4仅从已发布任务的 `project.json`、`binding.json` 读取必要policy身份，核native name／project ID及完整tracker关系；原constructor仍作完整mutable项目查找，原 `_execute`／DirectJob仍产生失败回执。固定身份缺失／不符继续fail-closed。不能简单吞所有resolver错误、另建回执路径，或放松v2／foreign-home的preclaim拒绝。

R4源码 **17 passed／89.72秒**，捕获299个自有进程身份，结束后均absent。新core／SDK安装各669个runtime包文件，source／wheel／site-packages字节和执行位同一，实际导入、283参考及依赖通过；core无SDK，SDK1.34.0。同一未改的原 `-I` probe在此新安装 **2.455秒通过**：FAILED＋agent-admission-error、poll同终态；claim／body各1，prepare／model／业务命令全0。实际executor SHA256为 `b6ca6c2b96a144d0cfd8785762f650bd01c430a5c5d0ed8388648dfa5f52184a`。

此安装绿例在 `native-resolution-fix-r4/green-original-installed-probe/`，原runner为 `native-resolution-fix-r4/probe-fixed.py`，不要复用已存在的输出label。源码绿、旧安装红分别保留。**原17节点的新安装运行、F1独立复核、自身模板仍未完成**；原13／119安装绿不转授。

原17节点选择保存在 `native-resolution-fix-r4/source-affected/invocation.json`，是composition executor、budget jobs和reference executor原五个入口的参数展开。用此选择和新安装的 `test-inputs/`，清除源码PYTHONPATH，保持原时限；不重跑无变化119大组。

### M6-V2b：完整SDK容量边界

|事项|身份／路径|
|---|---|
|固定产品|`919a38064f9e692ced4e6c2c8e70b0bd4b936a8e`，`.ergora/worktrees/training-cycle-v2-capacity-fixed-r1`，detached且干净|
|基线|`c540939d3b3f38f3851b0de965c9cd0f969eea77`，含已接纳V2a|
|作者树|`.ergora/worktrees/training-cycle-v2-capacity`，分支 `feat/training-cycle-v2-capacity`，已冻结|
|完整五文件冻结|`.ergora/checks/training-cycle-v2-capacity/impl-r1/freeze-r2/summary.json`及 `source.patch`；patch SHA256 `622a2ba0065162dc9839cc1d4c19048b372e2127bee9c9d433785e634dde49ab`|
|新wheel／安装|`.ergora/checks/training-cycle-v2-capacity/package-r1/`；wheel SHA256 `8fe43f445700845a4ee5e1e718ac6aacd5bcb73f031d03c0ff2ee7c4286b49d3`|
|交付／独审|[交付](delivery/2026-11-16-training-cycle-v2-capacity.md)、[源码独审](delivery/2026-11-16-training-cycle-v2-capacity-source-review.md)：两轴approve，0 findings|

唯一生产改动为 `reference_training_worker.py`：claim前及claim／fsync后的最终send前量完整Payloads／Memo，失败不退attempt；v3 wrapper发固定封闭错误；未经改写的默认converter先形成整棵Failure再量度／整体替换；通过公共SDK配置派生V2 client，V1不变。两个Workflow类AST都未改。不开放schema3效果或训练gate。

`impl-r1/` 源码证据：dispatch9过、最终4个超界参数过；runtime79过＋原history子进程10秒超时，原时限单独重验3.56秒过。N32源码两场均保留66分支：成功完整Payloads **19424B**、聚合 **37515B** 整体拒绝、最终SDK Failure **1205B**。`n32-summary.json`及独审保留准确原件与独立只读protobuf核验。

新安装各668包文件字节／执行位同一，core无SDK、SDK1.34.0、283参考与依赖过。**41个安装节点通过／52.85秒**，runner54.079秒；捕获133个自有进程身份，终核全absent。准确选择／argv／结果在 `package-r1/installed-selection.json`、`installed-capacity-targeted.command.json`、`.stdout`、`.xml`，是37个新增非N32参数节点＋4个受影响原接缝。

第一次N32安装runner在切换到copied-tests cwd后使用相对Python路径，FileNotFoundError，**pytest／产品子进程没有启动**。原空输出与 `package-r1/installed-n32-not-started.json` 保留。须用新label、绝对argv；从主checkout运行的下一条命令如下，**尚未执行通过**：

```bash
ergora_repo=$(git rev-parse --show-toplevel)
ergora_capacity="$ergora_repo/.ergora/checks/training-cycle-v2-capacity/package-r1"
"$ergora_capacity/venv-r1-sdk/bin/python" -I -B \
  "$ergora_capacity/run-installed-check.py" installed-n32-r2 \
  "$ergora_capacity/venv-r1-sdk/bin/python" -I -B -m pytest -q \
  tests/test_training_submission.py::test_cycle_v3_stop_completion_keeps_all_66_branches_and_originals \
  "--junitxml=$ergora_capacity/installed-n32-r2.xml" \
  "--basetemp=$ergora_capacity/installed-n32-r2-fixtures"
```

两参数串行，不与重检查并发；保留原预算及完整fanout。自身模板、集成发布和此候选自己的CI待做。真实Temporal／server追加Failure包装、完整M1c-V/R、每个10MB晚期reader与真实CPU两候选仍为后继验收；本地SDK／bridge替身不能认证它们或GPU质量。

## 最新配置需求及研究

用户要求每个Agent实例可配置由谁选择推理强度，支持 **固定档位／预设／规划阶段指定／框架自动** 四模式。目前可执行的只有显式原生值：Codex `reasoning_effort`、Claude Code `effort`，项目角色binding、Agent定义backend默认、正式任务逐实例完整binding override。正式review／work-unit DAG的并行已由原runtime及全部祖先并发配额控制。独立 `composition run-input` 只运行一个选中叶子，一般混合图和Repeat尚未完成。

[A6a–d计划](plans/2026-11-16-agent-reasoning-and-parallelism.md)已写四模式、原预算／冻结边界、版本化后端预设、缺少规划决定、不支持值与恢复；A6尚未实现。维持完整binding替换，不造字段merge，不占设计关卡预留definition8／input12。

子agent已完成完整[英文后端参数研究](research/2026-11-16-backend-runtime-options.md)／[中文](research/2026-11-16-backend-runtime-options.zh-CN.md)：20份官方／固定上游文件、5次本机版本／help读取，静态检查过，**独立语义审仍待做**。范围为Codex、Claude、DeepSeek Harness、mini-swe、ForgeKernel支持层与command；经Codex／provider使用ChatGPT不等于另一个注册backend。

设计应复用并核实这些结论：Claude环境优先级和组织／账户cap可能改变实际effort；`ultracode`是特殊组合，不能放到跨后端数字档位序列。记录requested／sent／native可观察值或unknown，不能补造实际应用值。候选新增项包括Codex service tier／verbosity、Claude有限turn／估算费用cap、DeepSeek明确SDK请求控制；原生估算／retry／session不能替代总预算、不可变任务合同及恢复owner，API字段不能直接声称CLI支持。

研究SHA256：英文 `1190b14d27c829dc980a8761910a958a61bf5bb04fcb3fa71af51b132066781d`，中文 `1eea39aa99e453f343ad3cae104d86fa1df134c22e03c1caa669d2038a0e72fd`。来源、失败、检查、完整patch及作者交接均在 `.ergora/checks/backend-runtime-options/`；先读 `handoff-summary.md`、`scope-manifest.json`、`source-manifest.json`、`research-static-checks.json`、`owned-research.patch`。本研究未运行模型、登录、安装、服务或真实计费／压缩验证。

## 文档与分支整理

[分批计划](plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md)、[交付](delivery/2026-11-16-bilingual-documentation-and-branch-cleanup.md)、[独审](delivery/2026-11-16-bilingual-documentation-batch1-review.md)。首批已有完整英文默认／中文互链的根README、文档入口、备份恢复、证据、测试五对文件。两轴approve；唯一P3已修正并复核：Linux CI20分钟，Windows `all`30分钟，开放finding为0。仍待发布。

作者初始12文件patch为 `.ergora/checks/bilingual-docs-branch-cleanup/owned-docs.patch`，SHA256 `f7c36f8ac620e63ea52a49312c601af44c13717290599108ceb6f5ebf383710b`。manifest文件raw SHA为 `572e8df98095f1be6cd42b373d6d7f94bf51214a1a1b29f6660c67d4333e6781`，其**内部scope摘要**是另一身份 `a734d6b178b9c78fb105d6ccdbf9f3ea585dd456a104e9a69367d59e76f844cb`。两个P3句子及根后继进度为后续改动，不能声称现行文件仍逐字等于初始patch。

仅在完整ref／OID备份后，用 `git branch -d` 删除三条已公开合入、无独有提交、无工作树的本地分支：`feat/evolution-console`、`feat/windows-support`、`research/multi-agent-evolution-20261028`。原清点38工作树全部保留，后继固定树解释较新数量；未删远端。原清点与回执在 `.ergora/checks/bilingual-docs-branch-cleanup/`。

batches2–7仍未完成：安装／项目手册，Agent／组合手册，训练／审查／改进手册，现行架构／词汇，其他维护入口，历史双语导航及必要的自包含HTML阅读视图。保留原报告／结论／证据，索引或摘要翻译不算完整手册。

## 子agent交接清单

本次接续涉及 **5个** 子agent：3个沿用实施／调研者，2个新启动独立审查者，现均completed。这不是项目全历史累计数；下列更早名字是历史线索，不是活跃任务。新会话未必能恢复同一handle，以文档／工作树为持久交接。

|Agent名称|职责与结果|持久产物／后继责任|
|---|---|---|
|`/root/bilingual_docs_branch_cleanup`|沿用：首批双语／本地分支清理，之后研究后端配置；已冻结结束，无在跑进程。|上述分批计划／交付及双语研究；batches2–7与研究独审未完。|
|`/root/design_policy_registration_impl`|沿用：R4 native查找／FAILED回执修正；源码17过，冻结结束。|`design-native-resolution-receipt`、`native-resolution-fix-r4/source-final/`、S1交付R4段；安装17／复核／模板交root。|
|`/root/training_v2_capacity_impl`|沿用：V2b五文件实现与源码检查；冻结结束。|`impl-r1/freeze-r2/`、V2b交付；新安装／模板／集成仍由root负责。|
|`/root/bilingual_docs_batch1_review`|新fresh reviewer；两轴approve，P3同片复核关闭。|上述review，SHA256 `e6394aee84545a6dee003857eb44eaee0d483f2c0d8135b7d2f8b48878e1247e`。可复核本片；下一完整实现片须新reviewer。|
|`/root/training_v2_capacity_source_review`|新fresh reviewer；两轴approve／0，只读独立解析原protobuf。|上述source review，SHA256 `045973534fad62b45c94372797402a859fe37db4be094459937e1a975a1e65df`，未重跑新安装或认证真实服务。|

更早可用线索：`/root/design_registration_v1_compatibility_review` 提出了S1开放F1及真实安装反例；若上下文仍可用，请它作同片复核，否则给新fresh reviewer完整原要求／候选／证据。`/root/training_v2_capacity_design_review` 审过准确容量方案；`/root/design_source_journal_s2_plan` 只写静态S2 proposal，不能把作者写方案当设计通过。

更早环境列出的审查名字有持久报告：`agent_backends_review` → [后端审查](delivery/2026-11-08-agent-backends-review.md)；`agent_composition_design_review` → [组合设计审](delivery/2026-11-08-agent-composition-design-review.md)；`advisory_runtime_review` → [advisory审查](delivery/2026-11-09-advisory-runtime-review.md)；`agent_reasoning_options_review` → [推理字段审查](delivery/2026-11-16-agent-reasoning-options-review.md)。另曾列出 `agent_definitions_review`，本轮未重新确认其准确报告／上下文。这些不是新增当前任务，也不是全历史完整名单。

## 关键计划、任务记录与研究路径索引

以下均相对仓库根目录；它们是入口，不能仅凭计划正文宣称功能实现。

|主题|优先路径|
|---|---|
|架构与扩展owner|[当前架构](architecture/current.md)、[身份合同](architecture/contracts-and-identities.md)、[组件变更协议](architecture/component-change-protocols.md)、[领域词汇](../CONTEXT.md)、[原all-in-one计划](plans/2026-11-01-all-in-one.md)|
|组合／继承／执行|[Agent组合计划](plans/2026-11-08-agent-composition.md)、[组合研究](research/2026-11-08-agent-composition.md)、[嵌套工作流研究](research/2026-11-08-nested-workflows.md)、[Agent定义](AGENT_DEFINITIONS.md)、[工作流定义](WORKFLOW_DEFINITIONS.md)|
|设计／人类／知识关卡|[用户D1–D4](delivery/2026-11-16-workflow-design-decisions.md)、[工作流演进](plans/2026-11-15-workflow-design-and-execution-evolution.md)、[完整设计](plans/2026-11-16-design-knowledge-gates.md)、[S1／S2拆片](plans/2026-11-16-design-gates-registration-and-journal.md)、[S2 proposal](plans/2026-11-16-design-source-journal-s2.md)|
|训练循环实现／验收|[V2 runtime合同](plans/2026-11-16-training-cycle-v2-runtime.md)、[容量实施清单](plans/2026-11-16-training-cycle-capacity-implementation.md)、[容量分期](plans/2026-11-16-training-cycle-measurement-capacity.md)、[V2a交付](delivery/2026-11-16-training-cycle-v2-runtime.md)、[CPU素材清点](delivery/2026-11-16-training-cycle-v2-cpu-prerequisites.md)|
|审查流程／研究复用／报告|[review演进](plans/2026-11-15-review-validation-evolution.md)、[Anthropic比较](research/2026-11-15-anthropic-code-review-comparison.md)、[后端审查说明研究](research/2026-11-15-review-backend-guidance.md)、[复用审计](delivery/2026-11-15-workflow-research-reuse-audit.md)、[设计知识审计](delivery/2026-11-15-workflow-design-knowledge-audit.md)|
|优化／重构要求|[领域／优化／质量计划](plans/2026-11-15-domain-review-optimization-quality.md)、[迭代优化架构研究](research/2026-11-15-iterative-optimization-architecture.md)、[专家更新计划](plans/2026-11-12-specialist-template-refresh.md)、[专家presets计划](plans/2026-11-13-specialist-presets.md)、[重构preset交付](delivery/2026-11-13-refactoring-preset.md)|
|横纵专家调研|[分类](research/2026-11-12-optimization-taxonomy.md)、[采用矩阵](research/2026-11-12-specialist-adoption.md)、[kernel](research/2026-11-12-optimization-kernel-agents.md)、[执行图](research/2026-11-12-optimization-execution-graph-agents.md)、[横向架构](research/2026-11-12-horizontal-architecture-agents.md)、[重构Agent](research/2026-11-12-refactoring-workflow-agents.md)。其他纵向文件为 `2026-11-12-optimization-*.md`，横向为 `2026-11-12-horizontal-*.md`。|
|市场／DeepSeek研究|[landscape](research/2026-10-28-multi-agent-landscape.md)、[DeepSeek研究](research/2026-11-02-deepseek-agents.md)、[最新后端参数矩阵](research/2026-11-16-backend-runtime-options.md)|
|真实workload边界|[提案／实验交接](plans/2026-11-14-proposal-experiment-handoff.md)、[workload源码试用](delivery/2026-11-14-workload-source-trial.md)。用户提供Small-brain-scaling／forge-universal参考材料是给Ergora试用；不得在Ergora开发任务里直接改业务仓库，源码试读不是真实训练baseline／candidate结果。|
|已接纳联合包／CI|[联合交付](delivery/2026-11-16-reasoning-cycle-runtime-integration.md)；原件 `.ergora/checks/reasoning-cycle-runtime-integration/package-r1/`、`publication-r2/`。官方[run43819270365](https://github.com/626619403/Ergora/actions/runs/43819270365)，准确head04af234／attempt1／8jobs全success，含Windows；原API403和旧候选失败仍保留。|
|用户操作手册|[英文文档入口](README.md)／[中文](README.zh-CN.md)、[使用](USAGE.md)、[Windows](WINDOWS.md)、[项目](PROJECTS.md)、[本地审查](LOCAL_REVIEW.md)、[训练审查](TRAINING_REVIEW.md)。尚未迁移的手册维持原语言。|

## 工程与授权边界

用户已授权继续实施／测试和普通开发分支发布，不重复询问已获授权事项。已接受的设计决定要求重要框架／结构／算法／数据／权限／验收变化先调研设计并由人类决定，小变更按项目规则。owner字符串、UID、TTY、JSON或沉默都不构成可信人类批准通道。S1只是storage／拒执行，S2仍是待fresh设计审的静态提案；完整关卡之前不开放可执行definition8／input12或schema3效果。

复用原Temporal／reference、配置工厂和实际领域owner。`agent_backends`管原生选项，`bindings.development_snapshot`、`tasks._member`、`agent_runs._admission`管原选择／冻结，`agents.invoke`是共同实际调用边界，不在调度层散布后端名字分派。所有祖先资料／Skill累积，权限逐级收窄；保留candidate身份、原deadline、attempt-before-send、unknown对账、冻结恢复及唯一reaper。

每完整实现片新fresh独审两轴，同片修正可请同reviewer复核；大项另用Ergora自身结构审查模板，保存完整输入／真实原回复。此前Claude模板调用多次420秒超时，用户已授权Codex／ChatGPT回退，须记实际后端，不能声称异后端通过。旧私有self-review脚本指旧产品树，必须适配／冻结新脚本及输入，不能照旧scope直接运行。

适用skill包括 `maintainable-project-delivery`、`ergora-codebase-quality`及module-design／test-seams、`research`，当前Codex官方结论用OpenAI Docs。按新会话skill catalog定位本机SKILL.md，不能假设所有旧agent handle仍可恢复。凭据仅引用环境，ChatGPT key变量为 `LINGZHI_API_KEY`；不打印密钥／完整环境。当前容器／用户执行仅面向可信项目，未证明Agent间OS隔离，无宿主权限，不提权或绕审批。

长期内容留仓库／home，不用系统tmp或 `project/tmp`；不迁移用户运行home、不停其他owner服务、不改无关业务workload、不删历史证据、不扩大原测试预算、不重复无变化大组。源码、安装、本地服务替身、真实服务、业务质量、审查与发布各自认证。
