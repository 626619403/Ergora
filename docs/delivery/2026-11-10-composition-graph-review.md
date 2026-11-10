# AC5 C4a 独立审查：本地及精确交付通过

**C4a 本地及精确交付通过：Standards 开放 finding 0；Spec 历史 CG-1、CG-2、CG-3 均按最终 R4 的受影响证据关闭，开放 finding 0。** 实际自身模板、公开证据、精确 Git 对象、一次独立 HTTPS 读取及该提交自己的官方 CI 已核验。本结论不宣称 C4、AC5 或整个项目完成。

主审 `composition_graph_review` 及独立 `spec_axis`、`standards_axis` 初始均使用 fresh context，实际读取根 AGENTS、PLAN、[本片计划](../plans/2026-11-10-composition-graph.md)、[交付记录](2026-11-10-composition-graph.md)、[AC5 合同](../plans/2026-11-09-composition-console.md)、当前架构和 ADR0003，按 `maintainable-project-delivery` 与 `code-review` 分轴审查，本次由原评审者续核同片。基线与审查时 HEAD 均为 `45c2de47e9119d1f07616b3307331321d38155a4`；提交范围为空，明确审查非空 WIP diff 与 untracked 文件。

最终固定候选为私有 `final-candidate-r1/` 的 26 文件：15 Markdown、5 JSON、2 PNG、3 JS、1 CSS；identity SHA256 为 `3ccc5d48a73b3e617124c66bafe74e1c53f35b1fafee11b97b06116846dbe084`。主审和两轴分别核全部 bytes/SHA，零差异。快照中的本文仍是终核前版本；此处最终结论单独记账，不倒改快照。早期八文件、十二文件快照和原轴报告保留，最终结论覆盖完整 26 文件。

## Standards

**通过，开放 finding 0。** 未发现有证据的硬标准违反或值得报告的 smell。`composition-graph.js` 只由定义视图生产消费；compound 投影、递归几何、选择与共享完整 inspector 形成内聚的私有展示算法，拆分有具体所有权和可读性理由。`definitions.js` 继续拥有库、精确版本、请求世代与编辑缓冲；`app.js` 继续拥有 DOM 替换前 dispose、挂接后 mount。

摘要拒绝、幂等 mount/dispose、缺组件回退、join 可选字段和 grant 清除均有可达的身份或生命周期用途。最终 fit 修正复用随包 Cytoscape 原有尺寸观察和销毁机制。没有新增浏览器编译器、权限/调度逻辑、依赖、永久测试或 CI。最终轴报告及 187 项离线核查、275 个本地链接检查见私有 `independent/standards-final.md`、`standards-final-audit.json`；CG-2 的标准轴线索已交 Spec，不重复计数。

## Spec

**通过，开放 finding 0。** 完整实例路径使同一精确 Agent/子工作流的多个实例保持独立；包含、依赖与具名数据关系分型，绑定只投影原 input 或 node/output。图/键盘表格共享完整 inspector，保留实例事实、祖先资源正文和原编辑缓冲；join 没有伪定义入口。已发布根 ref/preview 摘要明确，元数据按 id/version/digest 匹配，会话按 home 与完整根 ref 隔离。C4b 折叠/查找/差异及 C5 正式交接仍属后续，未被声明为实现。

**CG-1（P2，已关闭）：持久页恢复未重新挂载。** 原 pagehide 销毁定义图，入口缺少 pageshow 恢复。R1 显式合成 persisted pagehide/pageshow 得到 `oldDestroyed:true/restored:false`。最终 `app.js:176` 对 definitions tab 的 persisted pageshow 复用原 render/mount；R3 的 4.98 秒恢复及 R4 的 2.60 秒复核均确认旧图销毁、新图存活。此为合成生命周期验证，不是自然 BFCache 命中证明。

**CG-2（P2，已关闭）：中间恢复修正丢失其他标签页的未提交表单。** R2 对所有 tab 的 persisted pageshow render，重建仅存 DOM 的资料表单；原负例 URL 从 `https://restore.example.invalid/source` 变空，budget 从 4321 变为 1000000，`submitted:false`。最终条件收窄为 `event.persisted && app.tab === 'definitions'`。R3 同脚本及 R4 恢复复核确认 URL/budget 原样保留，未提交或抓取资料。

**CG-3（P2，已关闭）：缩窄视口后立即 fit 使用旧尺寸。** R3 容器 246、renderer 1076，settled 诊断稍后恢复 246/246，因此不称永久失效。随包 Cytoscape 已有 ResizeObserver、window resize、MutationObserver、约 100ms debounce 与 destroy 清理。最终只在 `composition-graph.js:115` 起三处显式 fit 前调用原 resize，没有第二套观察器；R4 原探针 2.86 秒通过，桌面 1076/1076、缩窄后立即 fit 246/246，最终移动截图画布保持在边框内。

最终 Spec 报告与原件核查见私有 `independent/spec-final.md`、`spec-final-audit.json`。R1 headless 小图只验证了**引用同一 Agent 的两个独立叶实例**、2 条依赖、3 条具名数据边、初始选择与 dispose；先前“两个子工作流及叶子”的表述已更正，重复子工作流由实际页面和逐边审计另行支持。

## 行为、安装与历史证据边界

四轮均由主审独立比较源、wheel、非 editable 安装全部 436 包文件及两份 RECORD hash/size；最终 R4 wheel SHA256 为 `9d8e0a423859697f876fc5dc0a9d89bc6a7a6893f10c577f335f223d71534aad`，较 R3 仅 graph 三处 resize/fit 改动，283 冻结文件不变。旧 PLAN 与归档原字节一致，原 JS/空白检查通过。既有安装回归只在 R1 运行：**28 passed / 33.41 秒**，外层 35.87 秒；后续 frontend 修正使用受影响浏览器证据，不把 Python 回归当 JS 交互证明。

R1 `browser-main-02.json` 的 4.90 秒实际页面旅程覆盖三领域及重复实例修订，22 个叶 inspector 的事实、完整资源/prompt、真实鼠标选择/拖动、键盘选择、布局/精确跳转缓冲、grant 销毁和缺组件表格均通过；R2 相同范围 5.39 秒通过。R1 首份 4.37 秒原件完成全部 22 叶检查后，因驱动未滚回图便按坐标点击失败，第二份只补 `scrollIntoViewIfNeeded`，原红保留。主审另将最终重复根图与原 preview 逐条核对，11 条依赖和 20 条具名数据的具体端点/标签全部一致，不扩大到未保存逐边图的其他三个根。

**撤回 R1 重叠 lifecycle 三个 true 的独立 home/迟到验收含义，也不接受 R3 没有 held 原件的 late-grant true。** R1 合成事件直接复现 CG-1 的原红仍有效。R2 43.11 秒换 home 超时由私有 helper 在新库加载前选择旧 DOM 引起；原请求顺序支持诊断，修驱动等待本次库响应，无产品变化。当前 runner 的 `waitForFunction(async()=>false)` 诊断在 18ms 返回 false，说明旧异步等待无效；不泛化为上游 Playwright 通用行为。原失败和失效等待均保留。

最终 R4 用 `page.evaluate` 内实际 await 的有界 no-store 轮询返回具体 unfinished held 请求 **94、103**。主审及两轴核原 request/response、status、controls：release 前已观察对应 held，两者均 release 后完成，旧 A94 晚于新 B102；真实 grant 输入后才释放 103，完成后旧图仍缺席。13.85 秒严格顺序旅程通过、无 pageerror；首轮过早 release 的驱动失败原件保留。R4 视口/自然导航 2.05 秒通过，但自然 back/forward 为 reload，未证明 BFCache。相关私有审计为 `browser-r1-audit`、`browser-r1-bindings-audit`、`browser-r2-restore-audit`、`browser-r3-closure-audit`、`browser-r4-audit` 与 `package-r4-audit` 等，不为终核重复运行旅程。

## 实际自身模板与公开证据

实际 run `0a28acda087d4a76b48fa84515532c24` 为 Codex / gpt-6.1-sol / high，**201.64 秒，succeeded/approve**，其 Spec/Standards 均 approve、finding 0。证据修订 Agent/Workflow `1.0.71` 只加入候选 Skill、提高 material 上限至 450000 并固定精确 Agent ref，原内置模板指令字节不变；原定义库保留在 active control 外。沿用户授权使用 Codex 回退，不声称不同模型独立或正式 owner 批准。

主审用 stdlib 重算 manifest、prepared、actual input 全树 digest，对账实际 stdin/protocol/prompt、scope/native receipt。原生最后 agent_message 解析后与保存 result 完全一致，result SHA256 为 `a7a72bfbfd6222b98b0a132e2e0d208ba63bac2a6bc6fc7eb0104e2c5c028d5a`。五 scope 全部完整交付；321066 字节候选经 14 个连续成功 UTF-8 页读至 `next_offset:null`，offset 24000 的 base64 窗口以同 offset 较小 UTF-8 页重试，失败读取 0。六保护源和附件 34 份完整条目均核身份，后续文档状态不倒改输入；材料交付不推断理解质量。

[五公开 JSON 与两截图索引](2026-11-10-composition-graph.md#v3-实际自身模板与公开证据)经主审拦截发布器全部写入、在内存重建，与固定候选逐字节相同；31 份去重原件 bytes/SHA 相符，两截图与 R4 原 PNG 字节相同。投影明确列出路径/端口替换及省略项。原生用量与公开记录相同：input 1360988 已含 cached input 1204480，output 3889，另报 reasoning output 1903；不重复加总或当账单。清理只核 40 个浏览器/服务和 4 个模型调用采样身份已消失，不扩大为全局进程保证。

主审最后补核为私有 `independent/final-material-audit.json`，两轴各有最终审计。本次终核没有模型/浏览器/产品/测试/安装/网络运行。摘要 retry 线索因受支持库禁止同 id/version 替换 digest，未构造手改索引缺陷。前片精确交付由原评审者单独终结，不替代本片提交/CI/HTTPS 门禁。

当前本地出口：**完整最终候选通过，Standards 0、Spec 开放 0、CG-1/2/3 关闭。** 精确交付按下节单独续记，不回写本地冻结候选。

## 精确交付续核：对象、HTTPS 与自己的 CI 通过

本片已普通提交并推送 `a60a67e9333316ba094c69a1ed949484fbed8231`，tree `b13d0f56ae488fe679e5decc40cc25cae29e1b3f`，唯一父提交为上述基线。主审直接读取精确 Git 对象：变更路径恰为已审 26 文件，每个 blob 的字节/大小/SHA256 与 `commit-closure/ready` 相同；较最终固定候选仅有本地 gate 已核的五份状态/审查记账差异。436 个精确提交包文件与原 R4 wheel、非 editable 安装及两份 RECORD 全部相同，283 冻结参考文件还与基线相同。没有从后续 C4b 工作树读取产品字节。

主审于 2026-11-10 独立进行**一次只读 HTTPS GET**，读取 Git smart-HTTP refs 原广告；HTTP 200，分支 `refs/heads/refactor/architecture-foundations` 返回完整 SHA `a60a67e9333316ba094c69a1ed949484fbed8231`，耗时 0.83 秒，未 SSH 或重试。私有原件为 `independent/exact-commit-audit.json`、`exact-https-ref.json` 及未改写 response。此观察只证明当时 ref，自己的 CI 单独核验。

自己的 [Portability CI 42817897236](https://github.com/626619403/Ergora/actions/runs/42817897236) 第三份官方样本在 2026-11-10 12:58:58 至 12:59:06 UTC 采集，主审只读离线核全部五份 HTML/JSON 原响应及其 bytes/SHA。Actions 嵌入状态为 completed/success，run 可见状态为 Success；工作流、分支、run 及精确提交完整 SHA 全部一致。job groups 明确 totalCount=2、hasMore=false，Windows job `129835576744` 和 Ubuntu job `129835577143` 均 completed/success。Windows 四项、Ubuntu 三项必要步骤全为 success 且带 job-completed 标记，其日志路径绑定完整 SHA 与对应 job；Ubuntu 的非必要 PowerShell 步骤按条件 skipped，不计作必要步骤成功。触发、各步骤起止、job 完成及采样时间顺序一致。

前两份样本保留 In progress，不计为通过；第三份原始终态才用于门禁。独立审计为私有 `independent/own-ci-final-audit.json`；未另取 CI 日志、重跑任务或新增网络/Git/产品/模型调用。结合已保存的精确对象/ready、本地 gate 和一次独立 HTTPS 证明，最终 `independent/review-exact-delivery-gate.json` 为 **pass / complete_acceptance:true**，仅结束 C4a。本节是后续审查记账，原提交 blob、固定候选及先前 pending gate 保持不变，C4b 工作树不属于此精确对象。
