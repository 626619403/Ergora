# AC5 C4b.1 独立审查：精确交付通过

**完整 20 文件候选及精确交付通过，Standards / Spec 开放 finding 均为 0，CEX-ST1 已关闭。** R2 产品/页面、实际自身模板、公开投影、精确 Git / 一次独立 HTTPS 均已核；自己的 CI 第三份官方样本双 OS 七必要步骤通过。不宣称 C4、AC5 或整个项目完成。

主审 `composition_exploration_review` 及独立 `spec_axis`、`standards_axis` 均从 fresh context 开始，读取原始要求、根 AGENTS、[本片计划](../plans/2026-11-10-composition-exploration.md)、[交付记录](2026-11-10-composition-exploration.md)、当前架构及必要调用邻居，按 `maintainable-project-delivery`、`code-review`、`codebase-design` 分轴审查；同片 R2 由原评审者分别续核。

基线与审查时 HEAD 均为 `a60a67e9333316ba094c69a1ed949484fbed8231`，分支 `refactor/architecture-foundations`；三点 diff 与提交范围为空，按明确授权审查 WIP。初始八文件候选为私有 `review-r1/`，初始产品 SHA256 为 `c81630de1ffebfbb04e66b7c5d4b3a4a4910b3a5353ee5fa3217a59569a0ca3e`；R2 仅删除下述三个重复字段，产品 SHA256 为 `22fad41ba596fadeba3cfcc02e9e84f2891326395339beca793846a1bddb4469`。

最终固定候选为私有 `final-candidate-r1/` 的 **20 文件：12 Markdown、5 JSON、2 PNG、1 JS**，identity SHA256 为 `e654f1b6a861451da6711479d86d54a92180c76af12737ee9cde10d91e2704be`。主审和两轴分别核全部大小/SHA；完整范围恰为 11 tracked + 9 untracked，原 tracked diff 相同，产品与已审 R2 相同。候选包含前片 C4a 精确终态续记，证据仍归前片；快照中的本文为上一阶段版本，本次最终结论单独记账，不倒改快照。

## Standards

**通过，硬规则违反、开放维护性 finding、阻塞问题均为 0。** 没有发现原所有者、依赖方向或已记录标准的违反。唯一生产消费者仍是 `definitions.js`；新增代表节点、显示投影、查找、重排与祖先定位均为该图内聚的私有算法，没有为单消费者引入新接口或框架。原请求/home/root 会话、编辑缓冲和 DOM 生命周期仍归原所有者。

fold、缺精确元数据、空查询、无图回退、位置恢复及条件重排均有可达用途；批量元素替换、尺寸调整及适配复用原 Cytoscape。没有新增断言、依赖、永久测试或 CI，也没有重复观察器、编译/材料读取或网络路径。未实测查找/重排性能，容量仍属 C6。

**CEX-ST1（P3，heuristic，已关闭）：重复的原边展示字段。** R1 `composition-graph.js:89` 写入的 `originalSource`、`originalTarget`、`originalLabel` 没有产品读取者；实际回查在 `160–164` 按 ID 直接读取完整 `relations`。主审及 Standards 轴逐字确认 R2 唯一产品差异是删除三个字段及相邻换行，原 ID / 关系事实不变，无新消费者、抽象或测试。修后包与实际页面原件已补核。原轴报告保存在私有 `independent/standards-r1.md`、`standards-r2.md`。

## Spec

**完整最终候选范围 no findings，开放 finding 0。** 独立实例路径维持同 ref 重复子工作流各自折叠；最外层已折叠结构祖先代表隐藏节点/端口，组内边不画伪自环。摘要边保留原 ID、类型和具名绑定，原始完整端点由关系 inspector 回查；完整实例、关系表与所有叶材料仍直接来自原 preview。

查找按精确 id/version/digest 元数据及原 preview 字段做字面词项交集，只高亮，未匹配结构仍显示；缺索引不推断专长。结果及定位只沿 `parent` 展开结构祖先，不将数据前驱当祖先。fold/query/选择/位置仍为 home/完整根 ref 下的内存显示状态。未发现编译、grant、调度、DSL、版本比较或正式交接越界。详细原轴结论保存在私有 `independent/spec-r1.md`、`spec-r2.md`。

## 行为、安装与历史证据边界

R1 主审独立重算八文件身份，并核 `definitions.js`、`app.js`、`ui.js`、原 CI 与 pyproject 均与基线相同；固定 JS 语法、候选空白检查通过。R1 的 436 文件/两份 RECORD 及 283 冻结身份通过，wheel SHA256 为 `52401a7eaa8508b6a12b28a37745107279df768d9ec0fd5bfbb8f622a67c4e35`，私有审计为 `independent/static-audit-r1.json`。该历史结果未升级为修后验收。

R2 主审重新独立核对源码/wheel/非 editable 安装 **436 个文件及两份 RECORD hash/size 全同**；wheel SHA256 为 `0aa34395e655fba62c7160ba8e7e8546b108a74cd02fff3edef42a54e850e0db`，**283 个冻结文件**仍与 manifest / 基线相同。修后 JS 语法和候选空白检查通过。没有新增或重跑未受影响的 Python 回归；两轴未重跑 UI、模型、安装或网络。

三份 R2 原生回执及执行代码均与所检查 driver 一致，主审和 Spec 轴分别核 native stdout/result JSON，未只采用汇总布尔值：

- 主旅程 `browser-main-r3.js` **12.935 秒通过**，覆盖三域 16/19/9 实例、重复/嵌套独立折叠、摘要关系回查、精确查找/拒绝 latest、保留未匹配结构、Enter 展开与前后定位、tab/版本和未应用编辑缓冲、缺 vendor 的表格/查找。完整 inspector 检查范围为三域各一个所选隐藏叶及重复实例叶，逐份核全部事实、各资源正文及 prompt，并非遍历全部叶。Spec 轴另从原 HTTP preview `0053` 重建最终图：34 原节点/31 边恰投影为 30 可见节点/28 条分型边（1 摘要），每条 ID、端点、标签和类型一致，无伪自环。
- 会话旅程 `browser-sessions-r1.js` **26.441 秒通过**，逐对象比较 A/B home 往返后的 query/fold/选择/可见坐标，核旧图销毁、合成 persisted 恢复及刷新重置。此为合成生命周期证据，不是自然 BFCache 命中；未重验未改变的迟到 preview 算法。
- 元数据/视口旅程 `browser-metadata-views-r1.js` **3.776 秒通过**。`routedOriginal` 与实际上游 HTTP `118/119` 相同，交付索引严格从 14 减至 13，只移除精确 1.0.0 条目而保留较新版本；缺口、专长不伪造、完整材料保持和恢复均有断言。仅受控浏览器投递变化，未修改原上游或定义。1440×1000 / 390×844 原截图已由主审查看，文档无横向溢出，画布/renderer 为 1076/1076、246/246；窄屏全览标签仍需缩放/定位，不承诺全览逐标签可读。

主审另核 **190 对原 HTTP** 的 bytes/SHA 与审计索引全同；12 份 R2 preview 与原准备 owner 输出完整对象全同，原 audit 脚本重算 owner 的范围已读核；四种实际安装静态资产与源同。**54 个完整旧对象树**的内容、执行位、目录及摘要不变，两个 UI home 的 agent_runs 均为 0；**23 个采样 owned 身份**在记录和当前核对中均已消失，只覆盖采样。私有主审证据为 `independent/product-browser-r2-audit.json`，Spec 另有 `spec-r2-audit.json`。上述秒数是顺序旅程耗时，不是单次搜索/布局性能或 C6 容量测量。

两份 R1 页面失败仍保留为失败：相对 API URL 缺 base、驱动写死 Codex 而原实例实际为 Claude-Code；最终按配置查询。未把失败升级为 R2，也未归为产品或模型缺陷；旧 fixture/startup 的失败和清理范围仍由交付记录保存。

## 实际自身模板与最终材料

实际 run `fd460f5c66594f82966a633b1cf1e9fc` 为 Codex / gpt-6.1-sol / high，原 run 与 SQLite 记录相同，**succeeded / approve，Spec / Standards 均通过**；原结果 SHA256 为 `7ecc9cd8129c633daf78f23e32bc22f06607362b16cc28f04cb03d6f644b8242`。主审重算 manifest、prepared/actual input 全树身份，核 6600 字节 stdin 与原 prompt/protocol 相同、原生最后消息与保存结果相同。证据修订 `1.0.72` 只调整版本/ref、候选资源和 material 上限，原内置指令/Skill 保持。

Spec 轴独立解析 43 条模型事件和原 MCP 回执：1 次 list / 17 次成功 read 对应五份完整 scope 资源；252062 字节附件经 **12 个连续成功 UTF-8 页**读至 `next_offset:null`，offset 24000 的一次 base64 窗口以同 offset 较小 UTF-8 页重试，失败读取 0。18 份冻结证据与四份受保护源均按原字节核对。材料完整交付不推断理解质量；用户授权的 Codex 回退不构成不同模型独立或正式 owner 批准。

初次 run `386a39284b194df09f81388382374886` 保持 MCP 预检失败，没有原生推理 output/result；随后只读 probe 通过，实际推理输出仅一份。两次冻结 input/prompt 与 scope 资源内容相同，scope 的 `run_id` 元数据分别归原 run。成功后的外层私有驱动因漏定义 `protected` 退出 1，原脚本/stderr 保留；恢复记录明确 backend 退出 0 / outer 退出 1。**122.913023 秒**由原 started/finished wall-clock 重算，包含准备/预检，不冒充未保存的外层 monotonic。此次离线恢复未重跑模型。

五公开 JSON / 两 PNG 由主审拦截发布器写入并在内存重建，全部与固定候选逐字节相同；19 份声明原件 bytes/SHA 全部相符，两截图仍为原 PNG。路径/端口替换及省略范围明确。原生自报 input 1062144 已含 cached input 933248，output 1966，另报 reasoning output 454；与公开记录一致，不重复加总或当账单。模型/CLI 五个采样身份已消失，只覆盖采样。原件索引见[交付记录](2026-11-10-composition-exploration.md#实际自身模板与公开投影)。

主审最终审计为私有 `independent/final-material-audit.json`；两轴为 `standards-final.md` / `standards-final-audit.json`、`spec-final.md` / `spec-final-audit.json`。Standards 的 139 项离线核查、216 本地链接/锚点及五 JSON/JS/空白通过；前片 C4a 三样本的 15 份官方原响应与原精确 gate 支持其终态，第三样本双 OS 七必要步骤只授予 C4a。终核没有重跑已验 190 HTTP、安装、浏览器、模型或网络。

本地出口：**完整最终候选通过，Standards 0、Spec 0，CEX-ST1 关闭。** 精确交付状态见下节；跨浏览器、自然 BFCache 与 C6 容量未新增验证，四次所选隐藏叶及窄屏可读性限制保持原范围。

## 精确交付续核：通过

普通提交并推送 `8ce9aba51c54e368aa8625e6c6535e4ac6ccaa19` 的唯一父提交为上述基线。主审确认 ready 相对固定候选仅有四份状态文档续记及已核最终评审结果；精确提交的变更路径恰为 20 文件，每个 blob 的大小/字节/SHA256 与 ready 相同，产品和公开证据不变。436 个精确 Git 包文件与已验 R2 wheel/安装/两份 RECORD 身份相同，283 冻结文件仍与原 manifest / 基线相同；未重验安装或读取未来产品 WIP。

主审进行**一次只读 HTTPS GET** 读取 Git smart-HTTP ref 广告，HTTP 200、0.68 秒，分支 `refs/heads/refactor/architecture-foundations` 返回上述完整 SHA；未跟随重定向、重试或 SSH。私有原件为 `independent/exact-commit-audit.json`、`exact-https-ref.json` 及未改写 response。此观察只证明当时 ref，不代替自己的 CI。

本提交自己的 [CI42825342126](https://github.com/626619403/Ergora/actions/runs/42825342126) 第三份官方样本 `snapshot-03` 为 **Success**。主审离线核三份样本的 15 份原响应大小/SHA，独立解析官方 HTML / JSON：完整 SHA、分支和 Portability 工作流绑定正确，Ubuntu / Windows 两 job 均为 completed/success，**七必要步骤**全部 success 且 job-completed；前两份原样保持 In progress。精确 20 个 Git blobs 与不可变 ready 再核相同，未混入后续 C4b.2 工作树。

私有 `independent/ci-final-audit.json` 及终态 `review-exact-delivery-gate.json` 已保存，后者为 **pass / complete_acceptance:true**；原 pending `review-exact-delivery-gate-r1.json` 保留，不倒改历史。此次仅离线核官方原件与精确对象，没有网络、产品、浏览器、模型、安装或 CI 重跑。精确终态仅属于 C4b.1，不授予 C4b.2 或后续阶段通过。
