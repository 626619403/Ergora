# AC5 C3c D2：资源修订接口独立实现审查

审查者 `/root/resource_interfaces_review`，新 fresh-context 实现审查，与 D1 设计评审者不同。产品基线为 `3baa619096a2ff95e2a29aedf179f3c614af103e`，分支 `refactor/architecture-foundations`。本报告以 [D1 r3 合同](../plans/2026-11-10-definition-resources.md#d1-固定接口r3独立设计复核通过)、[D2 计划](../plans/2026-11-10-definition-resource-interfaces.md)、项目 AGENTS 和用户原始要求为依据；D1 设计结论仅作为输入。

**最终独立结论：D2 固定提交 `80375d3647fbea585db77a08ab39e70915b01e96` 精确交付终结。** 完整 34 文件的 Spec／Standards、本候选 Git 对象、435 包文件／283 冻结身份、明确 HTTPS 远端及自己的 CI42779236273 双 OS 七必要步骤均通过；RIF-1–3 全部关闭，零开放 finding。R3 安装与实际旅程、两轮真实自身模板完整读取、11 份公开投影和清理均已独立核验。D3 页面资源会话及后续节点按各自门禁继续。

**R1 当时首审：Spec 需修改，2 项 P2；Standards 通过，零项独立 finding。RIF-1、RIF-2 当时均阻塞验收。** 以下首审证据及原红保持；修正与补充发现见后文。

## 固定身份与范围

先核 `.ergora/checks/ac5-definition-resource-interfaces/review-r1/identity.json`，其中 **21 份 tracked/untracked 快照 SHA256 全部一致**；初审时 live 文件也全部相同。HEAD 即上述基线，工作区为未提交实现。固定 `tracked.diff` SHA256 为 `a384eb20b1656e9e354fc77908899507cb437423437a5177de80bf523e3eb9e8`；身份核验原件为 `independent/initial-identity.json`。

完整受审文件分组如下，逐文件 SHA 以固定 identity 为准：

- 生产 5 文件：`src/ergora/{definition_bundles,agent_definitions,workflow_definitions,cli,web}.py`。
- 既有测试 2 文件：`tests/test_agent_definitions.py`、`tests/test_definition_console.py`。
- 手册 3 文件：`docs/{AGENT_DEFINITIONS,WORKFLOW_DEFINITIONS,USAGE}.md`。
- D1/D2 新文档 5 文件：`docs/plans/2026-11-10-definition-resources.md`、`docs/plans/2026-11-10-definition-resource-interfaces.md`、`docs/delivery/2026-11-10-definition-resources.md`、`docs/delivery/2026-11-10-definition-resources-design-review.md`、`docs/delivery/2026-11-10-definition-resource-interfaces.md`。
- 前片状态续记 6 文件：`docs/PLAN.md`、`docs/delivery/2026-11-10-definition-editor{,-review}.md`、`docs/plans/2026-11-09-composition-console.md`、`docs/plans/2026-11-10-definition-editor.md`、`docs/plans/2026-11-10-definition-revisions.md`。

已先读实际差异和必要调用者，再读作者叙述；额外只读检查 `asset_trees`、两类 inspector/当前准入与 Workflow 编译路径、现有 Portability CI、State、相关合同和当前架构。两个独立 fresh-context 子审分别完成 Spec 与 Standards；主审重新核实具体 finding。C3b 产品实现不重审，六份旧文档只核前片状态边界；D3 页面、嵌套画布、正式交接、容量及真实训练实验不在 D2 范围。

## Spec

### RIF-1（P2，R1 开放，后续本地关闭）：Windows 删除只读附件缺少目标文件 owner-write

- 位置：[definition_bundles.py](../../src/ergora/definition_bundles.py) R1 第 383–392 行，特别是 `delete` 分支直接 `target.unlink()`。
- 合同：[D1](../plans/2026-11-10-definition-resources.md)第 22 行要求只在新暂存树中调整“写入/删除所需的 owner 位”；第 29 行承诺普通文件 delete。当前只对父目录加写位，目标文件加写位仅出现在 write 分支。
- 可达场景：Windows 的只读文件不能直接 unlink。新增两类完整往返测试已经将原包全部文件移除写位，再删除 `remove.bin`（`test_definition_console.py` 第 171–188 行）；原 CI 的 Windows job 会运行这两个案例。Linux 目录写权限足够，因此现有 Linux 绿结果没有覆盖此平台语义。
- 独立证据：`independent/readonly-delete-probe.py` 沿两类真实 `revise(..., preview_resources=True)`，只在新暂存目标上应用 Windows readonly unlink 规则。两类都观察到目标 mode `0444` 后触发 `PermissionError`，原对象字节/mode 与索引保持。原结果为 `independent/readonly-delete-probe.json`；同时保存当前 Python 标准库 `TemporaryDirectory._rmtree` 对 PermissionError 先重设目标权限再 unlink 的既有处理。
- 最小纠正：在 delete 分支中，仅为新暂存 `target` 添加 owner-write，再 unlink；不改源或历史对象、不改 CI。已有两类往返测试可提供原生 Windows 回归，无需镜像实现新增测试。
- 限制：这是 Linux 上受控的 Windows 删除语义探针，**没有冒称已运行原生 Windows**。原生平台验证仍由该精确候选自己的 CI 证明。

### RIF-2（P2，R1 开放，后续本地关闭）：CLI 在最终拒绝前可先累积过量 base64

- 位置：[definition_bundles.py](../../src/ergora/definition_bundles.py) R1 第 135–147 行。目录转换器按每项 write 完整读取并把 base64 保留在操作对象内；总写字节和重复/重叠拒绝直到 `_apply_resource_changes` 第 353–373 行才执行。CLI 先完成 `_definition_revision_options`，才调用两类 revise。
- 合同：[D1](../plans/2026-11-10-definition-resources.md)第 30 行限定最多 1500 项、总写字节 10MB，第 34 行限定本地目录（含清单）也沿原树上限。一个受限本地目录并不自动限制按操作次数展开后的内存。
- 可达场景：1500 项都引用同一约 9MB 文件时，目录仍小于 10MB，但 loader 可在拒绝前保留约 18GB base64；可能先耗尽 CLI 进程内存。HTTP 原 4MB 上限不能保护 CLI 的目录输入。
- 独立证据：`independent/cli-loader-budget-probe.py` 对固定 R1 模块做低字节量复现：模拟目录只有 2 文件、1 目录、共 **63,729 字节**，清单 1500 项各引用同一 8192 字节文件。实际 loader 读取 **1500 次**，返回 **12,288,000 decoded 字节／16,386,000 base64 字符**，此后共同 owner 才报 `Resource writes exceed 10 MB`。原 schema 与 owner 前置校验未替换；只替换目录 inventory、清单来源和 rb 字节流。结果为 `independent/cli-loader-budget-probe.json`。没有执行 9MB×1500 或 OOM 实验。
- 最小纠正：loader 在每次读取后、编码并保留结果前累计写字节，超过 10MB 立即拒绝，从分配发生处封住内存放大。最终 owner 的总量与重复/重叠检查继续保护 HTTP/库入口；不要求再复制一套路径算法或引入通用 patch helper。

R1 当时除这两项外未发现缺失或越界实施：固定历史字节窗口及 `complete` 事实、有限操作和标准 JSON 通道、预览只更新声明摘要后完整当前准入、完整 digest/目录接受、重建比对且不自动刷新摘要、锁内已/未索引同摘要目录冲突拒绝，以及无资源参数兼容路径均与 D1 相符。历史 get/read 不要求今天后端；preview/check/publish 继续走当前完整准入。未新增页面实现、上传数据库或调度账本。

### RIF-3（P2，补充发现，后续本地关闭）：目录预算直到物理操作后才验证

- 位置：`_apply_resource_changes` 的前缀集合循环与 parents/mkdir 循环（R2 第 359–399 行）；500 目录/32 层的完整 `inventory_tree` 在资源操作完成后才运行。
- 合同：D1 第 30 行沿原 500 目录/32 层树上限。操作最大 1500、每路径最大 512 字符仍可使前缀集合和物理目录数远大于最终准入上限；HTTP 清单可小于 4MB，CLI 清单也不需携带文件。
- 独立证据：`independent/rif3-directory-budget-probe.py` 对 R2 源 `032eeff9…` 保持真实 schema/操作算法，只把 Path mkdir/chmod/stat 换成计数。**197 字节**单 mkdir 的 33 层路径已请求 34 次 mkdir/33 个目录；**17,071 字节**的 501 项平级 mkdir 已请求 1002 次 mkdir/501 个目录；两者在 `_apply` 中均未拒绝，直到后续完整 inventory 才会失败。原件为同名 JSON 和 `rif3-before-fix-definition_bundles.py`；没有物理目录洪泛。更大放大是该路径的推论，未实跑数万目录。
- 最小纠正：复用既有前缀循环维护原目录加预计新增目录的有限集合，超过 500 或目录层数超过 32 时，在集合继续增长和物理变更前拒绝。mkdir 计自身全路径，write 只计父目录，保留 32 层目录加末尾文件组件的有效请求。继续保留最终完整 inventory，不新增通用 helper 或第二套路径算法。

## Standards

**固定 R1 范围通过；无硬性标准违反，也无证据充分的 smell finding。** 这不覆盖 Spec 中的两个正确性缺口。

完整树和资源派生继续由已有 `DefinitionLibrary` 拥有，两类定义文件是两个真实生产消费者，CLI/HTTP 经原 use case 调用相同实现。删除此共同算法会把复制、摘要、接受身份和锁内发布知识散回消费者，符合 codebase-design 的 depth 与 locality。新增目录读取函数由 CLI 实际使用，留在拥有资源传输合同的原文件合理；局部 schema/操作方法和 CLI parser/options helper 有具体职责，不需要为单次调用新建模块或假想 seam。

已逐组核对新增控制流：操作 schema/数量/位图限制约束外部输入；路径与标准文件检查防止歧义和双来源；CLI 完整源 SHA 防止读取间变化；读取 offset/limit、固定基准、登记路径和完整 SHA 保护字节事实；接受对象和互斥旗标防止绕过资源采用；锁内暂存及现存目录检查防止旧对象复用丢目录；执行位回读拒绝平台无法实现的请求。文件/目录冲突继续由已有 mkdir/write/unlink 和完整树准入可见拒绝，无需新增通用 guard。RIF-2 则说明现有最终 guard 不能代替较早发生分配的输入转换预算。

新增 11 个参数化案例保护完整候选、未知附件/执行位/标准 JSON/空目录接受、已/未索引对象目录复用及两种入口的完整往返，针对可能静默出错的合同；未新增测试框架、依赖或 CI。两类完整往返在源码日志中分别为 3.26／4.00 秒，安装日志分别为 3.36／4.13 秒；没有删测试或延长 CI 的依据。读取每个窗口仍按 D1 经完整 get 核包，属于既定有界成本，不能据小包旅程宣称最大包/并发容量。

## 已核证据与剩余门禁

本审独立执行了 21 文件 SHA/分支/基线核对和两个小型 probe；未安装、启动模型或任务、修改产品/CI、提交、推送或请求外部服务。首轮旧包误导入、9 绿/2 只读 root 红、错误 suite 命令均按原记录保留，不把它们改写成当前产品红或旧包故意回归。只读 root 的最小 import/export 新副本 owner-write 改动已与固定源码核对。

- 已直接读原日志：`source-full-r2.log` 为 **183 passed／1 skipped／70.94 秒**；R1 `packaged-tests.log` 为 **191 passed／1 skipped／82.84 秒**。这里只证明这些日志的实际范围，不把 Linux 结果提升成 Windows 验证。
- 已读 R1 安装身份、三领域实际旅程与清理记录：wheel `26dfe4d4034cb26b8082b633dfc3a8155b113d41b7fb93164feddcb173a29396`，报告 435 包文件／283 冻结文件；旅程 **81 CLI／37 真实 HTTP／6 观测／47.56 秒**，单一 owned server 已按身份清理。其完整包对象与逐响应身份待最终固定材料再独立核，不能只继承 summary 的通过字段。
- R1 首审时自身真实模板正在原固定源上运行，当时尚未作为证据；其终态及后续修正分别在下文续核。原失败保持。
- 最终完整文件集（包括后补 architecture/status/公开证据）、自身模板完整读取/原回执/清理、文档链接与手册命令、普通精确 Git 对象、自己的必要 CI 和明确 HTTPS 仍分别待核。D3 及后续合同保持未实施。

R1 当时两轴计数：**Spec 2 项 P2，均开放；Standards 0 项。**

## 同片修正复核与 R1 自身模板续核

本审只读核 R1→R2 的生产最小 diff：`definition_bundles.py` 增加 loader read 后、base64 前累计 10MB，以及 delete 新暂存 target 的 owner-write；R2 源 SHA256 为 `032eeff9fc4c75168ae0cca0896fe2b423d7486869c05d71bb919923b6b4ba20`。新增十行预算回归在原 `test_agent_definitions.py`，用小目录/1500 重复项检查转换阶段拒绝，保护可能先耗尽内存的输入，有实际价值；无需镜像操作实现。原两类往返源码结果 **2 passed／18 deselected／9.72 秒**，直接读 `source-fix.log`，本审不重跑整组。

新原件均在 `independent/fix-r2/`，未覆盖 R1 探针/结果：

- 删除探针两类均观察到新暂存目标 **0644**，preview 成功；原目标仍为 **0444**，原字节/索引不变。RIF-1 的代码缺口本地关闭；原生 Windows 仍待自己的 CI，不把受控 Linux 探针改称原生验证。
- 同一预算探针在第 **1221** 次读取、保留前 **1220** 项／**9,994,240 decoded 字节**后提前拒绝，未对超预算项编码。预算内的两项重复仍由原 owner 拒绝，说明无需在 CLI 复制重复/重叠算法。RIF-2 本地关闭。
- 最小 diff、产品与测试 SHA、原 R1 原件 SHA 另存 `source-fix-identity.json`／`source-fix.diff`。补充 RIF-3 后整体 Spec 尚未通过，修后包不能继承 R1 接受身份。

R1 真实自身模板 run `6f7f4db7bfbe499d99ed47f94703228c`，**332.66 秒／succeeded／request-changes**，实际意见再次指出 RIF-1，没有指出 RIF-2。主审直接核固定 manifest/input/实际 run 的 digest、prompt、原 result 和响应 SHA；14 份保护源逐一从 `review-r1/files` 或固定 baseline Git 对象解析，避免把后续工作区错误要求成旧 R1。候选附件 **464,921 字节**／SHA `32949309be8339af99735190d33d71d39e978b2131037c15222ee0bd7e3336b1`，**18 页连续成功 UTF-8** 完整重建至 next_offset null，四份结构链指令/Skill 完整读取，无 failed/base64 页；原定义库已移除，实际 run 消费冻结输入。原件为 `independent/audit-model-r1-independent.py` 和 `model-read-audit-r1-independent.json`。

模板读取事实证明完整交付，不证明理解质量或正式 owner 批准；这是授权 Codex 回退，不宣称不同模型独立性。未重跑模型、服务或网络。

上述 R2 当时两轴计数：**Spec 共 3 项 P2，RIF-1/2 本地关闭、RIF-3 开放；Standards 0 项。**

## RIF-3 最小修正复核

R3 仅在原前缀循环维护 `planned_directories`，从已有完整目录初始化，对 mkdir 的全部前缀和 write 的父前缀累加，超过 500 或目录层数超过 32 即拒绝；delete 不计新增目录。所有操作仍在第一轮检查全部通过后才进入物理写入循环；最终 inventory 保留，分别保护分配前预算与实际完成树，没有新增 helper/框架。RIF-1/2 的修正仍原样存在。源码 SHA 为 `808044446301231422c6f9ae31a809bfaa071e495b85646f72f6151bd3f6b658`。

`independent/fix-r3/directory-budget-probe.py` 保持原两组输入，用计数式文件系统重测：33 层和 501 目录均在 **0 次 mkdir／0 次 write** 时拒绝；合法 **32 层目录＋第 33 个文件组件** 可写出完整字节，未误拒绝。三项原始结果、最小 diff、源与测试 SHA 及原红原件 SHA 均保存在同目录，原 RIF-3 计数探针和结果未覆盖。

已读原既有测试内的三个参数化回归：拦截目标 flood 路径，证明非法预算在分配前被拒绝；合法文件边界验证有效配置没有被测试倒逼收窄。它们针对本次已经实证的分配顺序和 off-by-one 风险，未复制生产实现；没有更改 CI 或新建测试框架。安装原 R2 红/绿与最终 R3 受影响结果见下文。

**RIF-3 本地关闭。当前 Spec 共 3 项 P2，全部本地关闭；Standards 0 项；零开放 finding。** 原生 Windows 和精确交付 CI/HTTPS 不由这些本地探针替代。

## R3 安装与实际旅程原件核验

独立直接读取 R3 wheel、source、安装目录及 RECORD：**435 文件**逐字节/SHA/RECORD 尺寸一致，wheel 为 `1b74ada0caa05f2a1360fa76f7e5b50027ea8ae3fc0c7cdd1819bedf096c1a23`。**283 冻结文件**与基线原 manifest/Git archive 对象一致，reference manifest 自身也与基线相同。R1→R3 包内只有 `definition_bundles.py` 发生三项修正，其余 434 文件相同；pyproject 与 Portability CI 未变。原件为 `independent/audit-package-r3.py`／`package-r3-audit.json`，没有重新构建安装。

RIF-3 原 R2 安装包的 `directory-regression-red.log` 为 **2 failed／1 passed／1.31 秒**，两红明确发生在 flood 路径首次物理分配，合法文件边界为绿；独立核 R2 安装源 SHA 仍为 `032eeff9…`，不是当前 R3。R3 `packaged-tests.log` 为 **46 passed／60 deselected／19.43 秒**，包括新增 4 个输入预算/目录边界案例及两类完整往返。原 R1 六组 **191 passed／1 skipped／82.84 秒** 保持其身份，R3 只继承未变部分，不将受影响 46 项称成完整 191 项重跑。

R3 实际三领域旅程 **81 CLI／37 真实 HTTP／6 观测／49.05 秒**。本审逐一核原 CLI stdout/stderr 及 HTTP request/response 的字节/记录 SHA，直接重算最终控制库、导出与再导入完整树：

- 六组 Agent/Workflow 的 CLI/HTTP、JSON/YAML 预览/检查/显式同候选重试回执一致；未接受附件变化的六次发布均 400；实际大于 4MB 的请求为 413。
- 建议正文、完整 digest/目录身份、全部 write 字节、普通未改附件和执行位、完整新旧 Skill 树及空目录与实际发布/导出/再导入对象一致；原只读对象仍与原来源树相同，完整 mode 未被资源修订改写。
- 两个二进制窗口按 next_offset 合并成完整原字节，末页的 complete 仍为 false；三份旧 manifest 与初次 prepare、后续 verify 的 digest 一致，没有正式 run。
- 独立核 R1/R2/R3 三个 owned HTTP 的 pid/starttime 与清理记录一致，均已 reaped，未杀其他进程。R3 服务不再具有原进程身份。

原件为 `independent/audit-journey-r3.py`／`journey-r3-audit.json`、`cleanup-and-regression-audit.json`。核验仅重读保存字节/对象，没有启动服务、模型、测试或命令旅程。完整窗口的 IO 仍经完整核包，49.05 秒只描述本轮小包实际旅程，不代表最大包或并发容量验收。第二轮模板与最终完整文档/公开证据、精确对象/CI/HTTPS 仍分别待核。

## 完整 34 文件提交前终核

最终固定材料 `review-final/{identity.json,tracked.diff,files/}` 的 **34 文件 SHA256 全部匹配**，核验时 live 也全部相同。identity SHA 为 `22131710716a009d190092d7f869ff3c263efdc395c2ee8565b7057c0a528423`，完整 tracked diff SHA 为 `3f2b9b6e383f92cbfcbfd4ec6ddb650c4a4e27b476f3b8bcefe88f5b52b942d4`。范围为 **5 生产、2 既有测试、16 文档、11 公开 JSON**；逐文件身份原件为 `independent/final-identity.json`。其中本报告属于同片状态续记，按 AGENTS 不递归审查报告。

已核最终全量差异和 R1 后新增部分：生产源只含三项最小修正；新增预算/目录回归对应实证分配风险；手册补充 PowerShell 5.1 的 UTF-8 输出方式；架构说明与真实共同调用链、当前准入、旧摘要和后续 D3 边界一致。计划和交付记录区分原红、R1 全组、R3 受影响组、实际旅程、模板意见和精确交付状态；C3b 六份续记没有借本片重写原实现或提前完成后续 C3c–d/C4–C6。未发现新的缺项、范围扩张或维护性问题。

第二轮真实自身模板 run `69f00da988634827a4e1f5687ca1e848`，**323.03 秒／succeeded／approve**。独立核原 manifest、准备/实际 input、prompt、原 result 与 response，以及 14 份保护源在最终固定快照或不变 baseline 中的字节身份。附件 **527,526 字节**／SHA `fe5e0f3a780398c76b27a8547015db6f33ccd5684fb38331eebbcb955b202bf1`，**21 页连续成功 UTF-8** 至 next_offset null，四份结构链指令/Skill 全量读取；零 failed/base64/重复页。原 result SHA 为 `0c011a0cfec443acb1f59f348c4adf14aa2fd52c7dc4ec732cc57d88c03152bd`，stream SHA 为 `64ffc51283c07cedf3793508a81a19b617e9f31fef6e45ead8fbe341cfc4b66a`。两轮原流只出现 task MCP list/read 与消息，没有 command/file_change/web_search 事件；未将模型意见当作正式批准或不同模型独立性。原件为 `independent/audit-model-r2-independent.py`、`model-read-audit-r2-independent.json`、`model-event-types.json`。

**11 份公开 JSON** 已逐一重算最终快照字节、发布清单 SHA 和全部 `source_artifacts` 的原始字节/长度/SHA，再递归比对每个字段与只替换个人目录的确定性投影；两份用于公开来源的 result 副本与实际 native result 逐字节一致。公开格式化投影 SHA 与 native SHA 各自保持，没有把去路径文件冒充原结果。报告、原红/修后探针、包/旅程和读取审计的实际范围一致；个人仓库/home 路径未进入公开投影。原件为 `independent/audit-public-evidence.py`／`public-evidence-audit.json`，来源发布清单实际位于本片私有根目录 `public-evidence.json`。

独立静态重查固定 **16 文档／248 链接／零缺失**，并实际调用当前 CLI parser 解析 **107 条 README/手册命令**；与 `static-documents-final.log` 和实际保存的 `static-documents.json` 一致。原件为 `independent/audit-documents-final.py`／`static-documents-final-audit.json`。静态结果只证明链接/锚点与语法，不替代此前真实 CLI/HTTP；本报告最终状态续记后仍需由作者刷新文档 SHA 记账，不要求产品重跑或递归评审。

|最终本地门禁|独立结论|
|---|---|
|Spec|完整 34 文件通过；RIF-1/2/3 均已关闭，零开放 finding|
|Standards|完整 34 文件通过；所有者、实际复用、新 guard 依据、回归价值/成本及 CI 范围均已核|
|安装与固定资源|R3 435 源/包/安装/RECORD、283 冻结原件、最小包差异及受影响 46 项通过|
|实际旅程与清理|R3 三领域六定义 81 CLI/37 HTTP 的原字节及完整树通过；三轮 owned HTTP 身份清理通过|
|自身模板与公开证据|首轮 request-changes 保留；第二轮 approve/完整读取及 11 公开投影已核|
|精确交付|本候选提交对象、自己的必要 CI、明确 HTTPS 尚待后续分别核验|

**本片提交前本地门禁终结。** 下一步由作者按原授权普通提交/推送并收集自己的必要 CI 和明确 HTTPS 原件，再核精确对象。D3 页面资源会话和其余后续节点继续依赖本片精确交付，当前结论不扩大其完成范围。


## 固定提交与明确 HTTPS 补核（CI 尚待终态）

独立对固定提交 **80375d3647fbea585db77a08ab39e70915b01e96** 执行 `git show`／`ls-tree`／`archive` 原对象读取：唯一父为 `3baa619096a2ff95e2a29aedf179f3c614af103e`，tree 为 `95ecb93d6030ee50986752aa66cde586b549d1fc`，完整差异恰为 ready 的 **34 文件**，逐文件 SHA256 全等。与已审 `review-final` 不同的五份文件仅续记本地门禁状态，产品与测试未改；本报告按 AGENTS 不递归评审。复核开始首次观察工作区 clean；随后作者继续状态和 D3 设计准备，固定对象核验没有以这些 live 文件替代已提交候选。

固定提交的 **435 文件**与 R3 wheel、非 editable 安装及 RECORD 逐字节/摘要/长度一致；wheel SHA256 保持 `1b74ada0caa05f2a1360fa76f7e5b50027ea8ae3fc0c7cdd1819bedf096c1a23`。**283 冻结文件**的 Git mode／kind／OID 全等父基线，reference manifest 亦相同。`pyproject.toml` 与原 portability workflow 未改，第二轮模板 **14 保护源**和已审 **11 公开 JSON**均等于相应已提交对象。作者提交与推送原 stdout/stderr/returncode 一致，但推送日志不替代远端读取。独立原件为 `independent/audit-exact-commit.py`、`exact-commit-audit.json`、`exact-commit-status-only.diff`。

**2026-11-10 08:06:16.452388 → 08:06:19.679944 UTC**，独立通过明确 `https://github.com/626619403/Ergora.git`，对 `refs/heads/refactor/architecture-foundations` 执行一次有界 `git ls-remote --refs`，退出 0，stdout 仅返回上述完整候选 SHA 和目标 ref，stderr 为空。运行 cwd 为仓库外 `/`，全局/系统配置禁用，未继承 Git/SSH/凭据配置或认证环境，helper/交互禁用，协议仅允许 HTTPS、TLS 验证开启、禁止重定向，外层限时 45 秒。原命令、环境变量名策略、stdout/stderr/trace 及 SHA 保存于 `independent/https-remote-01/`；未把代理配置值或凭据写入证据。

首条作者 CI 命令传错完整 SHA，`snapshot-01` 的匹配失败保留为命令错误，不归作产品或 CI 失败。独立离线核正确 `snapshot-02` 的 **五份官方原响应**，逐一重算 bytes/SHA；Actions 记录精确绑定本候选、目标 ref 和 `.github/workflows/portability.yml`，run 为 [42779236273](https://github.com/626619403/Ergora/actions/runs/42779236273)。job groups 恰为两组且 `hasMore=false`，两个 job 页均核 selectedJobId 与本候选的 step log URL。

该快照采样 **08:01:03–08:01:14 UTC**，run 及两 job 均 `In progress`：Linux `129704998892` 与 Windows `129704999307` 的 Build and install wheel、Packaged reference identity 已成功，两个 Native application regression 和 Windows PowerShell 5.1 installer and upgrade 尚无终态，故为 **七必要步骤四成功、CI 门禁未通过/待验**。没有借用 C3b 的旧 CI，没有轮询、取消或重跑。独立解析脚本和结果为 `independent/audit-ci.py`、`independent/ci-snapshot-02/ci-audit.json`。收到本候选后续官方终态原件后再补核；D3 产品实施仍依赖本片精确交付终结。


## 官方 CI 终态独立补核与精确交付终结

2026-11-10 的 `snapshot-04` 官方采样范围为 **08:15:27.395538 → 08:15:48.489443 UTC**。独立直接离线解析五份原响应，逐一重算 bytes／SHA256 并核精确 HTTPS URL；未只接受作者 summary。Actions 内嵌条目绑定完整提交 `80375d3647fbea585db77a08ab39e70915b01e96`、`refs/heads/refactor/architecture-foundations`、原 `.github/workflows/portability.yml` 与 [run42779236273](https://github.com/626619403/Ergora/actions/runs/42779236273)，状态为 `WORKFLOW_RUN_STATUS_COMPLETED`／`WORKFLOW_RUN_CONCLUSION_SUCCESS`，run 可见终态为 `Success`。

job groups 恰为两组、`totalCount=2`／`hasMore=false`；两个 job 的名称、页面 selectedJobId、链接、step log URL 均与本候选对应。**Linux `129704998892` 与 Windows `129704999307` 均 completed／success，七必要步骤全部 success 且 job_completed：**

|必要步骤|Linux ubuntu-latest／Python 3.11|Windows windows-latest／Python 3.12|
|---|---|---|
|Build and install wheel|success／completed|success／completed|
|Packaged reference identity|success／completed|success／completed|
|Native application regression|success／completed|success／completed|
|Windows PowerShell 5.1 installer and upgrade|按 Windows 条件正常 skipped|success／completed|

所有步骤未见 failure／cancelled／timed_out；Linux PowerShell skip 与已提交 workflow 的 Windows 条件一致，不属于七必要步骤。独立核验时间为 **2026-11-10T08:17:09.485846+00:00**，CI 门禁通过。原脚本与完整解析结果保存为 `independent/snapshot-04/{audit-ci.py,ci-audit.json,ci-audit.log}`；source 元数据中保留五原响应的 SHA／长度／取样时间与地址。

**D2 本候选精确交付已终结。** 前述 34 固定对象、435 源/包/安装/RECORD、283 冻结 mode/kind/OID、14 模板保护源及 11 公开 JSON 的独立核验，以及 08:06:16.452388→08:06:19.679944 UTC 的明确 HTTPS 同完整 SHA 均保持；此次只补本候选自己的官方 CI 终态，没有重复网络、测试、模型或服务。`snapshot-01` 错 SHA 命令与 `snapshot-02/03` 进行中原件全部保留，未改变历史观察；首轮模型 request-changes、各原红与修后证据亦保持。后续 D3 产品实施须满足其自己的设计和实施验收门禁，本结论只终结 D2。
