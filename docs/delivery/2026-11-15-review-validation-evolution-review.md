# Q2.4 R0：独立文档审查

日期：2026-11-15。审查者：fresh-context 独立 reviewer `review_validation_evolution_doc_audit`。本上下文只收到原要求、固定范围与实际证据简报，未继承实现者对话；已读根 `AGENTS.md`、`maintainable-project-delivery` 及其 independent-review reference、`ergora-codebase-quality` 的三个相关 reference。

**需求符合性：approve。结构／可维护性：approve。实质 finding：0；阻断：0。** 结论只覆盖本片研究与后继计划，不认证 R1–R4 产品能力、审查质量收益、平台批准或真实训练。报告和完成状态记账不需要递归审查。

## 原要求、基线与完整范围

原要求是继续原计划并保留 kernel 专家；本片响应用户追问：“你目前的 pr review 模板有参考这个吗？https://claude.dev/blog/solving-code-review-at-anthropic/”。验收要求为如实说明此前来源、按一手原文与现有实现逐项对照，把适合采用的差异写成可验收后继节点；不修改旧包／模板、权限、预算、正式／平台 approve 或训练人工 release。

审查基线为 HEAD `3947b1e28b2cbc27ddc53cab584cced0c8d971a6`，分支 `refactor/architecture-foundations`。完整读过以下五文件正文，包括三个未跟踪新文件；核对 `.ergora/checks/review-validation-evolution/review-scope-r1.json`、全文快照及 tracked diff。下列字节数／SHA256 均独立重算，快照与当次工作树逐字相同。

|文件|字节数|SHA256|
|---|---:|---|
|[PLAN](../PLAN.md)|73,917|`eeebcd338892aa476d423fa94e3cd6d96f5ab1654badf05788c1eea983963d28`|
|[领域总计划](../plans/2026-11-15-domain-review-optimization-quality.md)|31,333|`d3d406f802e2418ceae6e829856933732a8298900181262031986767472e71c1`|
|[本片后继计划](../plans/2026-11-15-review-validation-evolution.md)|5,370|`51a7e494521ea66954bbf7b66e6c7bcbb9da49ef4de29bc71f35a8a77946720a`|
|[本片交付](2026-11-15-review-validation-evolution.md)|1,956|`4963e2264a4e9171987765a591b6c2aac74115d09eea05b7e1f69179cdb7bd87`|
|[一手对照研究](../research/2026-11-15-anthropic-code-review-comparison.md)|25,782|`ae8b6f3a4e69af81fb3988e939d07fc2fc3a03950de700b4465bc668d39495de`|

研究报告保留其实际读取基线 `d1fcfa5b78e912004114f00275c32e6dfac6dcb0`，没有冒称运行过当前训练片。独立核该提交到本 R0 基线之间，相关 review owners、presets、evaluation 与 Portability 均无差异，因此该历史读取身份不使本片审查结论失配。相邻训练发布／CI补记在 R0 产品范围外；仅核 PLAN 所引原交付／原 reviewer 对本地 `3947b1e`、前片 `d1c7280` CI 终态及 `877e1e4` 当次 CI 在途的记录，不重审训练产品，也不替代其后继门禁。

## 一手来源与现状核对

独立直接读取[文章官方 Markdown](https://claude.dev/blog/solving-code-review-at-anthropic.md)和[Code Review 官方文档](https://code.claude.com/docs/en/code-review.md)，再以 curl 重算响应正文：分别为 22,410B／`a322aa7632a44e82af40bf467cd89912eb870ea646bb5df7b4d51c80d8dd8577` 和 10,665B／`78ff48627f8e08e5551e254a963356b6988160a6b0edc873fc8772e3f301e06a`，与研究报告及主 agent 的 `primary-source-identities-r1.json` 一致。文章标题、作者、2026-10-15 日期与数字引述相符；这些是作者自述，本审查没有私有生产数据或因果效果证明。

1. **此前参考何物表述有依据。** 已读[历史工具研究](../research/2026-11-15-pr-mr-review-tools.md)全文，其第 2 节确实研究公共 CLI、官方 code-review／pr-review-toolkit、Action 和托管产品。对固定 HEAD 的 `docs`、`src`、`AGENTS.md`、`.github` 独立检索文章 slug、标题及作者标识，无直接命中。当前材料支持“未找到对该特定文章的直接引用”，不能证明全部历史或私人对话；研究第 60 行保留了这个限定，没有从相似设计反推来源。
2. **all-join 与逐 finding 复核正确区分。** [交付审查定义](../../src/ergora/data/presets/workflows/ergora-delivery-review/workflow.json)为 structure／correctness／test-value 三路，领域根再加一域 reviewer；instructions 要求保留所有原意见。[review_requests](../../src/ergora/review_requests.py)的 `report`（94–152 行）核精确输入与原 run，缺叶／坏原件／失败为 incomplete，完整时任一 request-changes 保留。结果仍是逐叶 decision 与原 response，没有候选 finding 的独立复核／投票处置。研究第 75–85 行没有把这些能力混称。
3. **正式 runtime 与外部消费者正确区分。** [reference_workflows](../../src/ergora/reference_workflows.py)的 `ReviewDAGWorkflow.stage`（261–303 行）按前驱及并发 scope 调度，并核独立 session；[review_dags](../../src/ergora/review_dags.py)的 `StageDAG` 支持有向无环依赖。外部 `review_requests._reviewer` 则调用 `require_root_task`，拒绝未运行前驱；prepare-input 只准备一叶，report 只读显式选定 runs。[preset catalog](../../src/ergora/data/presets/presets.json)也将领域入口标为 proposal-leaves。本片没有把正式任务调度移称为外部整图自动运行。
4. **三轮反思与上限的归因清楚。** 原文虽用 “A round cap” 小标题，实际披露的是三轮之后请作者退一步重想方案，没有自动关闭 PR 的硬状态机。研究第 41／102 行及交付末段准确保留此区别；R3 把显式有界和可配置上限作为 Ergora 后继设计选择，并未宣称原文已经给出它的唯一状态机或精确 diff-only 切换轮次。
5. **平台与质量边界保留。** 官方托管产品明确不执行被审代码，也不 approve／block PR；文章内部风险批准、thread 阻断、queue／flag／回退不能归给公共产品。现有 correctness／领域 Skill、只读工具限制、[原四次 CPU 合同记录](2026-11-15-training-domain-reviews.md)及[完整报告交付](2026-11-15-complete-review-reports.md)与研究相符。四例材料自带算术结果，不能用作盲测或总体效果；本片没有新增这类主张。Portability 及 tracked 平台文件清单也不证明远端 required-check 或批准策略。

## R1–R4 的归属、验收和优先级

本片是后继计划，具体机器结构和接缝设计尚未完成；计划把它们保留为 R1 开始前的工作，没有将候选方案当成已获产品验收。

|节点|独立判断|
|---|---|
|R1／P1|沿原 review_requests／review_dags／定义库与 agent run 是合理最小方向。计划先固定 finding 与来源身份、保留原意见和复核原件，要求真实缺陷／可证伪误报／缺证据三种流程。尤其明确外部入口尚不能消费前驱，必须实现并验收实际复核输入消费者；只新增 JSON 边不算完成。没有提前增加调度器或改变现有报告保守语义。|
|R2／P1|与 R1 成对评价，避免把更多 agent 或一致票当质量 oracle。现有 [evaluation](../../src/ergora/evaluation.py)确实拥有冻结 suite、可信 evaluator 文件身份、baseline／candidate 比较及 holdout；当前它面向 Skill 版本，不是已经建成的复合 reviewer 事故集。计划同时沿审查输入／结果 owner、先定真实消费者并固定模型／模板／输入／预算，足以约束后继设计；漏报、误报、严重度、耗时与可取得成本可验，没有计费观测时报告不可用。|
|R3／P2|在 R1/R2 后再接跨轮记录，避免先搭循环引擎。精确新 head／前轮链接、完整原包和必要上下文、旧 finding 生命周期、去重不合并不同缺陷，以及取消／耗尽／unknown 先读原记录均有可验收边界。后继片仍需固定实际配置范围和停止规则；本片没有冒称静态 DAG 支持回边。|
|R4／P2|风险先作有理由的提示，沿候选／批准／界面 owner，并以真实团队消费者为前提。新 head 的候选身份与批准绑定需核实；模型意见不取得正式／平台批准或训练人工 release 权力。没有引入原文内部 0／1／2 人自动放行、信任名单或平台写回授权。|

优先级合理：逐条核实与可信对照直接补当前已观察到的能力缺口；跨轮收敛依赖可追踪 finding 和质量证据，风险提示依赖真实使用者。对效果无益或成本不合适的结果，计划允许据证据调整／暂停后继采用。领域总计划第 35 行和现有 v3 flow→analysis→kernel→measurement 定义仍保留 kernel 专家，允许专家判断无需算子改动，没有改变旧模板。

## 检查与局限

独立轻量检查结果：五文件 SHA／字节／全文快照一致；261 个本地链接目标存在；无行末空白；相对固定 HEAD 的产品、测试、脚本、依赖及 CI diff 为空。完整读取本片 tracked diff 和全部新文档，另按上述具名函数、定义、Skill 与历史交付追踪事实。链接检查只证明目标存在，没有把它当成远端内容或全部锚点的认证。

未运行付费模型、suite、安装、训练或平台操作，未读取凭据，未提交／推送，只新增本报告。没有验证原模型是否始终遵循每项规范，也没有统计评估、多卡／训练正确性或性能结论。后继实现必须各自完成具体设计、实际调用／可信检查和新的独立审查；当前 approve 不转授它们。

R0 的研究与计划审查证据已齐，剩余是由实现者在本片交付／PLAN 如实记录本报告与实际完成状态；无待修实质 finding。
