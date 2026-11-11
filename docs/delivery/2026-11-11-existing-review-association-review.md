# F7c-C3b 独立审查

**当前判词：最终 28 件候选独立 Spec／Standards 均通过，开放 finding 0／0；SP1、ST1、ST2 已关闭。** 最后文档字节的静态终核及 R6 精确交付仍分别执行，不以审查通过替代。以下先保留首轮发现，再记录同片复核。

审查日期：2026-11-12。审查者为本片新建的 Codex 独立上下文；另以两个 `fork_turns: none` 上下文分别完成 Spec 与 Standards 轴，先读原始规格和实际差异，再读作者叙述。只读源码、邻近所有者和证据；仅写本报告，没有修改产品、安装、联网、提交或运行产品套件。Standards 的小型复证仅用 `python -B` 和内存 SQLite，不写文件。

## 固定范围

基线为 `ad331c854a6fbdbf6bacc3aac4350bb8d393713f`，当时 HEAD 即此提交；审查对象是基线到完整未提交工作树的差异，不是空的 HEAD 三点差异。冻结材料位于 `.ergora/checks/f7-review-association/review-r1/`：

- `manifest.json` SHA256：`ad07358657fc072d6953a4d975a74355ca7ab3521c5928b05a1469dfa6869e09`。
- 25 件完整副本的字节数和 SHA256 全部独立重算相符，含 5 件 untracked 文件。
- `tracked.diff` SHA256：`887b17511dd9eec1349edecb81ab383c87e46b7d469d9fc8ec9a1e296f31d779`。逐 hunk 用基线原文在内存重建 20 件 tracked postimage，全部等于冻结副本。

25 件范围为 README；PLAN、USAGE、两份 architecture；C3a 两份 delivery、一份验收 JSON、一份 plan 的状态记账；总计划、F7 计划；C3b 原计划、研究、交付记录；`cli / contracts / issue_backends / issues / state / web`、`components.json`、新 `candidate-review-context-v1.json`；`test_issue_writebacks / test_review_associations / test_state_migrations`。原规格是[本片计划](../plans/2026-11-11-existing-review-association.md)。C3a 只核本片带入的状态记账，没有递归复审旧产品。

## Spec

**首轮判词：产品合同未发现可信缺陷或范围扩张；R4 尚有一项 P3 验收缺口。**

**SP1 · P3 · 真实 v7 旅程尚缺 HTTP 离线读回。** 冻结计划第 46 行要求“真实本地v7→Git export→…fresh CLI与HTTP离线读；只控制SDK端口”，状态却写为“HTTP同用例通过，仅SDK端口受控”。真实来源旅程在 [test_issue_writebacks.py](../../tests/test_issue_writebacks.py#L454) 保存后只做 fresh CLI show；[HTTP 用例](../../tests/test_review_associations.py#L276) 则继承受控 candidate/remote fixture，除了 Temporal SDK，还替换了任务 creation/show/export_status 与 inspect_export。按该状态验收时，会把受控任务的 HTTP 证据扩大为完整真实来源旅程；这里没有发现 HTTP 产品故障。最小修正是在已有两 provider 真实 v7 用例移除 token 后，针对同一 State、同一 saved SHA 做一次 TestClient GET，核完整 record 相等、外部调用数不变；只补验这两项，并准确区分已有 HTTP fixture 的范围。

其余合同经源码与调用者核对：首次只发五次 provider GET；当前 local/remote/review head、明确 base 名及 source native ID 都参与检查；GH number/id/node_id 与 GL iid/global id 分开；GH fork/null repo、GL source/target project、可空 diff_refs 和独立 diff head 比较符合要求。单候选 scope 不含 review/base/reason 等 operand；同目标返回原历史，异目标冲突。外部读取位于 SQLite 写事务外，最终短事务重核 revision 和 scope；同一 load 供保存、离线 show、backup 使用。State v4 更新全部旧表和新表 fence，旧备份按原版本处理。原 unknown/intent/claim 和 283 文件没有被新 context 改写。

## Standards

**首轮判词：通过，附一项非阻塞 P3 格式一致性建议；没有已证的文档硬性违规。**

**ST1 · P3 · 两个版本字段缺少严格整数声明。** 新 [schema](../../src/ergora/data/schemas/candidate-review-context-v1.json#L192) 的 `/$defs/review_request/properties/schema_version` 与[顶层版本](../../src/ergora/data/schemas/candidate-review-context-v1.json#L519) 仅有 `const: 1`，接受浮点 `1.0`。一份合法记录仅将这两处改为 `1.0` 并重算内容 SHA 后，实际公用 `_review_link` 仍接受，因而 offline show/backup 也接受。正常 writer 生成整数，正常保存旅程不受影响。[身份规范](../architecture/contracts-and-identities.md#L32) 规定声明为 `integer` 的值必须 `type(value) is int`、拒绝 `1.0`；第 34 行为评价旧格式单列宽松兼容例外。其余版本化格式通常显式声明整数。但规范未逐字要求所有新版本字段均声明整数，所以这是格式一致性判断项，不升级为产品 P2。最小修正仅为上述两处加 `"type": "integer"`，用已有损坏载入用例保护即可。

新增保存/读取用例由 `issues` 拥有；`_review_scope` 和 `_review_link` 是有具体本域职责的私有算法，后者有保存、离线读与 backup 三条真实路径。`review_path / review_request / read_review_request` 留在已有 `IssueBackend`，GH/GL 两个 Adapter 通过同一 Interface 执行；CLI 和 HTTP 没有 provider 分派。新 schema 同时承载公开保存合同与本族 observation 子合同，没有新增泛化 publication/scheduler/ledger。每个新增 guard 可对应外部输入、持久身份或事务竞争，未发现需删除的冗余防御。

测试主要保护可静默出错的身份混淆、并发、正文预算、历史重试、损坏备份与旧 writer；没有新增 CI 或独立重复旅程框架。静态确认网络不持写锁、事务内操作有明确 1 MiB 上限；没有做性能基准，也不从几项时长推导容量结论。

## 实际验证与独立核对

独立重算 source-r1–r5 的实际 stdout 摘要，均与 result.json 相符；读取了命令、失败栈和输入身份，不合并分轮结果冒称一次最终全绿：

|原件|实际结果|范围|
|---|---|---|
|source-r1|48 passed / 29.17 秒|早期原生读取、C3a 观察与架构；不是完整保存或发行|
|source-r2|77 passed、6 failed / 54.23 秒|六失败分别为 unknown 异常类型、超长 reason 和重复 CLI 参数，各两 provider|
|source-r3|原六项 6 passed / 5.77 秒|只修测试写法，相关产品字节未因此改变|
|source-r4|2 passed、8 failed / 58.46 秒|两 provider 真实 v7/本地 Git/fresh CLI 通过；八失败为 backup 测试局部变量遮模块|
|source-r5|原八项 8 passed / 7.74 秒|别名修正后旧 v0–v3、delete/WAL 备份与迁移补验|

r2 原四文件清单及 supplemental 六文件说明分别保留；补录说明不能反过来当作完整原始输入清单。后续 r3/r4/r5 的清单可追，相关产品在冻结快照中相符。源码结果只证明所列候选和范围。

后补 r1 新非 editable wheel 已独立检查原字节：wheel SHA256 为 `fb78f40363adaad20f52e5c97a9745d5e74d95f00492211928bd438034a5bc9e`；447 件包文件逐一等于源码/已安装文件，8 件本片产品文件又等于冻结副本；wheel/installed RECORD 分别 452/457 行的大小与摘要全部重算通过；283 件 reference 逐一符合 manifest；METADATA 的 README body 等于冻结 README。初次依赖网络超时保留；随后在同一全新 venv 用 uv 离线缓存和既有依赖版本成功安装，不是 editable，也没有借旧 ergora 包。

`r1/installed-validation.json` 与 stdout 摘要独立重算相符：八个受影响安装 suite **189 passed、1 skipped / 197.60 秒**（命令 199.69 秒）；安装包 `reference verify` 退出 0 / 0.27 秒。这里是读取作者实际原件和包身份，不是评审者重跑产品。r1 包不包含后续修正，不能提前替未来包验收。

实际自身模板首轮记录为 run `e61508dd3a094fb5bccbcaa167c206d5`，**timed_out / 604.71 秒，无 decision**。17 件完整附件共 472,872 字节；原诊断显示四祖先 scope 读到 null，但 candidate 只到 next_offset 144,000，不能称候选全文已读或模型通过。采样的四个所属进程无存活是作者有范围清理证据，不证明所有短命进程均被观察。后续收窄审查仍待原件，不能扩大首轮失败范围。

## 首轮出口与未验范围

SP1 开放，ST1 为开放建议；本片尚不能据首轮报告结案。下一步是同片最小修正/补证复核、新包的受影响验证，以及实际自身最终范围与文档终核；普通提交/推送、精确 Git/remote 和本提交自己的双 OS 必要 CI 均未由本轮判通过。

真实 SaaS/GHES/GitLab 部署、权限与延迟、原生 Windows 正式执行、六阶段真实模型运行和成功的不同执行/审查后端独立性未验。GET 是分时观察，非共同 snapshot/CAS，不能检测 ABA；v7 原来源未冻结历史 repo native ID，当前 source/native 检查不能补成历史仓库身份保证。关联只证明保存证据的一致性，不证明原 attempt、批准、当前远端不变或任务作者身份。

## 同片最终复核：28 件独立审查通过

再次由原两轴上下文分别核修正和最终完整候选。`review-r2/manifest.json` SHA256 为 `3d27ae55d53b73ee69902f67b4a05bbc294607a91b933bd3edbb912c2c0fd839`，27 件副本的大小／SHA 全部相符。与 r1 相比，产品只有新 schema 两处 `type: integer`；两份测试分别沿既有用例补 HTTP 和 float corruption。另核补件 `review-r2-addendum.json` 指向的 [INTEGRATIONS](../INTEGRATIONS.md)：17,164 字节、SHA256 `e90d3c882565d90e989413b0bf6e32baa496a5ffae1a08c4c061a172003ae79c`，冻结副本与现文相同；只更新早期工单段落的能力／未支持操作说明，没有扩张实现范围。因此完整候选为 28 件。

**SP1 关闭。** `native-http-r1` 两份保留原 HTTP body 的大小／SHA 与回执相符，逐字解析出的 record 等于 r1 真实 v7/本地 Git/fresh CLI 旅程的已存 SQL payload／scope，candidate 也一致；这是对原件的独立只读核对。新安装用例又在删除 token 后对同一 record 实际 HTTP GET，检查 200、全文相等及原 provider 调用数、Git／SDK／export 保持，已含于 r2 两 provider 通过范围。原受控 HTTP fixture 与真实来源旅程的范围在交付记录中分别说明。

**ST1 关闭。** 原 r1 installed loader 的内存 row 红复现保留，持久行未改。最终两处严格接受整数 `1`、拒绝 `1.0`；沿已有 corruption 参数的覆盖通过共用 load 和 backup 拒绝损坏记录，没有新框架或重复旅程。r2 原件是 **68 passed／101.06 秒**（命令 102.96 秒），stdout SHA `a45ac4156fef4f3f0932966b50b2a24efb4eacccc9ccfb53a5fa69d27dad3f69` 已独立重算；reference verify 退出 0／0.27 秒。新包 SHA `f39eabc3ecf596a1d82a06b2bf2c663f8e0160ec744450eed77969ca678b0169`、447 件源码／包／安装文件、两 RECORD 的 452／457 行及 283 reference 又逐一核符；r1→r2 包内容仅 schema 有差异，README 元数据保持。没有重复运行这些套件。

**ST2 · P3 · 可选 Web 测试依赖已关闭。** 复核发现 HTTP 补证直接 import FastAPI，安装 dev+temporal 而未装独立 web extra 时，原组合测试会在末尾模块缺失；同模块其他 HTTP 用例使用 `pytest.importorskip('fastapi')`。作者在原组合用例开头采用同样 skip，最终测试文件 31,217 字节、SHA256 `4cb2dd6bbde11087d599602eff084036ba2f26cc443113c05af5870af61661db`；相对 r2 只有这一行。已静态确认依赖声明、既有约定和补丁，不为 skip 一行重跑重旅程；68 项保持原运行身份，不称对最终测试字节重跑。产品、依赖和 CI 均未因此改变。

实际自身聚焦 run `51020a1029d94bd1b8cacf78aa38a7c4` 为 **approve／546.83 秒**。独立从实际 native 原流重建五份 scope：四份祖先／Skill 原文及 133,647 字节 candidate 的六个连续 UTF8 页，均到 `next_offset: null`，与 scope 原字节／SHA 一致，未见失败工具调用；原结果 SHA `407c061d997611e0acf8e62ba61ad5230f5c95d0babbbca6b40c78ed2cc4b7a4` 也相符。九件完整附件和先前版本的精确范围已核，不把这次 approve 外推给后来两处 schema、HTTP 测试或完整 CLI／HTTP／backup／usage／公开记账。首轮 17 件超时仍为失败，其重叠读取只影响诊断算法，不改写产品或模型状态。

最后又读了 r2 之后本片交付／两份总计划的状态追加，均准确保留独立／静态与精确交付的先后范围。新结构化验收 JSON 与原件一致，不含机器路径或凭据值。本报告初稿的五个相对链接曾错误使用冒号行号，已改为相对文件加 `#L`；独立核本报告全部本地文件目标存在，未声称锚点或外部 URL 验证。作者记录的六秘密值扫描仍只是其有范围证据，本评审没有读取凭据值。

**最终 Spec：通过，开放 0；最终 Standards：通过，开放 0。SP1、ST1、ST2 均关闭，完整 28 件独立审查出口完成。** 最后文档字节静态检查由作者随后终核；普通提交／推送、精确 Git／remote 和本提交自己的双 OS 必要 CI 属 R6，尚未由本报告证明。前述真实平台、原生 Windows、六阶段模型、不同后端与历史身份限制全部保持；F7 其余和项目整体不因此关闭。
