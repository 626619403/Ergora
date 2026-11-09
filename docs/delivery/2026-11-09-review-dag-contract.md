# AC4.3a：只读审查DAG合同设计

日期：2026-11-09。固定基线 `91b09683aac9481d07a6cd1d2ea8da9777b25563`；只含本片合同/计划及前片交付记账，没有生产、schema、依赖或CI变更。前片自己的必要CI与即时HTTPS远端已终结，本片不借其CI证明新增执行功能。

## 本片出口

依据现有静态定义、任务创建/版本Input、原review/Executor与证据恢复调用链，形成[端口与来源合同](../plans/2026-11-09-review-dag-contract.md)。明确结构继承、执行依赖和数据端口三种关系，新能力显式选择、旧正式协议保持、前驱原件/候选/会话/预算/取消语义，以及下一运行片的可验收节点。

此前AC4.3a的实现出口调整为先固定可审合同，再由AC4.3b完整纵切片接通创建和运行；没有只为静态设计发布未支持的v4运行器或多余公共格式。合同里的字段仍为拟议，不能从文档推导已实现。

## 验证与审查状态

当前已完成原始要求及实际调用链梳理、合同初稿；计划/本片记录随节点更新。待新的fresh-context设计评审、文档链接/锚点与CLI静态核验、普通交付与实际远端。文档片不重跑前片模型或应用套件，不借前片CI声称新增执行功能。


## 设计审查修订与静态证据

新独立者提出DG-1来源语义与DG-2终结输出消歧。已按真实代码限定：start/resume保留原submission/memo归属，可信Workflow只取自身完成结果，Executor核原发布job/context/receipt与候选/摘要，关闭后才用原Inspection核history；不向原receipt加run_id，也不增加每叶查询。选定子树仍一个终结输出，投影链终点为显式all-join；嵌套子图可多具名输出，不加输出选择器。

另外保留两项实现风险：共享端口表不能自动去掉不同审计产物内部重复正文；现有MCP只暴露结构资源，不会自动获得动态端口。合同增加串行审计容量反例与实际装载方式的验收，未因此提前新增schema或通用存储层。

已用前片非editable包实际导入/preview/prepare-manifest/inspect目标串行后双并行审查图：5实例，层次为structure→{correctness,test-value}→gather，executable=false；原manifest再次核一致。原件保存在`.ergora/checks/ac4-dag-contract/static-example.py/json/log`。这仅证明当前格式能表示图，不证明新传递覆盖或端口已运行。原初轮四文档/60本地链接及79已有CLI parser静态通过；最终修订与审查报告加入后再核最终scope和链接。


## 本地设计门禁

[新独立设计评审](2026-11-09-review-dag-contract-review.md) Spec/Standards通过，DG-1/2关闭，terminal-only Inspection适用边界已澄清；没有新增生产bug或要求新的网络/账本能力。完整scope为7份Markdown，含前片精确提交/CI/远端终结记账；没有生产/schema/依赖/CI变更。最终链接与现有CLI parser静态核验另按实际结果登记，不为文档变更重跑应用套件或模型。下一个实现候选为AC4.3b，仍须自身模板及全新独立实现审查。

最终静态核验 **7份Markdown、102本地链接/锚点、79条已有CLI parser**通过，`git diff --check`通过。原件在`.ergora/checks/ac4-dag-contract/static-documents.json`；新独立者另核7份/100链接（最终两条互链加入前）通过。当前提交全为文档，按现有Portability的Markdown路径过滤不要求另跑应用CI，未借前片CI声称本片新功能通过。普通交付与精确远端另核。

本片已精确交付`e9b682c4be4f19aa11aca4717a7f6d86050278ed`（7文档）。同一独立者从Git对象逐份核原批准稿与完整清单，102链接/锚点通过，原CI的Markdown过滤适用；随后2026-11-09 07:09:15.760037 UTC明确HTTPS读取返回同完整SHA。完整终结见[独立报告](2026-11-09-review-dag-contract-review.md#精确提交对象及文档门禁终核)，后片WIP未纳入本片。
