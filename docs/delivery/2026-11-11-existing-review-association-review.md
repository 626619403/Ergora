# F7c-C3b 独立审查

**当前判词：最终 28 件候选独立 Spec／Standards 均通过，开放 finding 0／0；SP1、ST1、ST2 已关闭。** 精确提交 `572c44e3f9621cd85d18447f14b436725df2eb64` 的 Git／ready／包、作者 Ref 和自己的双 OS 七必要步骤均已独立离线终核，R6 精确交付终结。原 push 超时与中间非终态／请求失败原件保留。以下保留各轮当时结论及同片复核。

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

## R6 精确 Git／ready／作者 Ref 原件：通过，CI 待终态

仅离线读取固定提交 **`572c44e3f9621cd85d18447f14b436725df2eb64`**，没有安装、产品／模型重跑或网络请求。禁 lazy fetch 和 object replacement，按 Git 对象头与原内容重算 commit 及 blob SHA1；唯一父提交为 **`ad331c854a6fbdbf6bacc3aac4350bb8d393713f`**。父→子差异恰为 28 件，全部普通 blob／`100644`；逐件大小、SHA256、mode 与 `commit-closure/ready-r1/manifest.json` 及封存完整副本相符，ready 清单 SHA256 **`29cb5c25f9b6fe0b89c26b4b7b68693fb2dd80ef39383c6d10783004ec3e0432`**。提交内审查报告保持已核快照 SHA **`5fa2dbf03d11791a7edc1c6e7bcd93b6245e6c58272769fc9707b5f97227d7b2`**；本节后续追加不是该提交内原字节。后续新片或工作树文档不改变本次候选身份。

r2 wheel 的 447 件包文件逐一等于该提交 `src/ergora` 的全部 447 件文件，METADATA 的 README body 也逐字等于提交内 README；wheel SHA 仍为 **`f39eabc3ecf596a1d82a06b2bf2c663f8e0160ec744450eed77969ca678b0169`**。没有重跑已核安装与套件。最后公开状态追加仅登记本地出口、关闭的 finding 与 R6 待核；`static-r3` 的 28 件文件身份逐一等于 ready，记录 367 个本地链接、六个当时加载秘密值及 issue 0，四份 JSON 再次可解析。秘密值扫描只作为作者有范围证据，本评审未读取凭据值。

普通 `git commit -m ...` 原回执退出 0／0.21 秒，原 stdout SHA `1447796c5b778e445088db3f5028685e1fe8c22e0c7a7d57ea3da6a1b2df3fe7`，stderr 空。随后普通 `git push origin HEAD:refs/heads/refactor/architecture-foundations` 的原脚本发生 **TimeoutExpired／60 秒**，没有 push 终态或退出 0 收据。`push-timeout-r1.json` 明确是依保留工具异常重建的说明，不能据后来远端状态把本次 push 改写为成功返回，也不补造 partial stdout/stderr。

后续作者实际 `git ls-remote --exit-code origin refs/heads/refactor/architecture-foundations` 原件退出 **0／2.4576 秒**；JSON 的 stdout 与独立保留 stdout 逐字相同，精确为该完整提交 SHA 和原分支，stdout SHA **`f9c0f9ecdbff4c2b731c9a0e2b5186e424d1cb344a475eb9339a889512cab6ae`**，stderr 空。这证明作者该次读取观察到远端已到候选，不证明原 push 进程成功退出；本评审没有独立联网确认。

首份 `ci-api-r1` 官方 REST runs／jobs 响应均为 HTTP 200，原 body 大小／SHA 与来源回执相符。精确 candidate、原分支、push event 和 `portability.yml` 对应 run **`43068731988`**；Windows job **`130691751127`**、Linux job **`130691751567`** 均为 queued、conclusion null、steps 空。该样本的 parser AssertionError 不能当作平台 CI 失败或通过；原非终态保留，等待自己的双 OS 必要步骤终态原件。

**本轮结论：精确 28 Git 对象／mode／ready、提交与 r2 包／README、作者同完整 Ref 原件均通过，无新增 finding。Spec／Standards 仍开放 0／0；R6 只剩本提交自己的 CI 终态及必要步骤原件终核，尚未关闭。**

## R6 自己的双 OS CI 原件终核：精确交付终结

继续由原评审者离线核原件，只追加本报告；没有网络请求、产品／模型重跑或其他文档修改。对象固定为 **`572c44e3f9621cd85d18447f14b436725df2eb64`**、原 ready 和 r2 包；当前新片页面或文档变化不属于该提交。

独立重算四轮共七份实际 HTTP body 的大小／SHA，逐一核对原 receipt 的请求 URL、最终 URL 和状态，全部相符：

|保留原响应|HTTP／字节|body SHA256|
|---|---|---|
|`ci-api-r1/runs.json`|200／12,006|`5e7c295292622b412dbffc8edf498bd51c0f9e6705e755b6d6ae657dd46439b5`|
|`ci-api-r1/jobs.json`|200／1,746|`8d38defa75c2730fad270e4d5e3b2c0053732621ed4826eb8750110ae8267553`|
|`ci-api-r2/runs.json`|200／12,011|`d42c59f06d296c2d4d66ea0011da1c6191653f934b44bbce97805e4473aa9892`|
|`ci-api-r2/jobs.json`|200／4,558|`6fe57a731647fc3182b667e93b03ff61f01d777615639d328ad733a300014dc9`|
|`ci-api-r3/runs.json`|403／280|`cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`|
|`ci-api-r4/runs.json`|200／12,014|`584fcb60591e4d32d2802cad88cf1f61e092347dc0bdb8514bff4f9a3d1016ee`|
|`ci-api-r4/jobs.json`|200／5,208|`3c954cd5f13d8412303732c5dd48ac5e16e8a96aa7d600460e4694ebc56d6021`|

所有成功样本均绑定仓库／head repository `626619403/Ergora`、精确完整 candidate SHA、原分支、`push`、`.github/workflows/portability.yml`、run **`43068731988`** 与 attempt **1**，两个 job ID 始终相同。r1 为 queued、空 steps；原 collector 错把未来必要步骤当时已存在而触发 AssertionError，其后离线非终态投影准确保留，没有 CI 失败含义。r2 为 in_progress，两个回归仍在运行、Windows installer 尚待，`required_steps_passed: false` 保持。r3 是匿名限流 403，只有请求失败，不能补推当时 CI 状态。r4 才是 run／双 job 均 **completed／success**；这些历史样本没有回写为提前成功。

从该提交原 `portability.yml` 确认 Ubuntu／Python 3.11 与 Windows／Python 3.12 矩阵、三个共同必要步骤及 Windows 条件步骤。独立从 r4 jobs 原文选出七项，名称、step number、completed／success 和有效起止时间均与投影一致，完成时间落在各 job 内：

|job|必要步骤|终态原件|
|---|---|---|
|Windows `130691751127`|Build and install wheel；Packaged reference identity；Native application regression；Windows PowerShell 5.1 installer and upgrade|4／4 completed／success；回归完成 `2026-11-11T17:43:38Z`，installer 完成 `17:44:15Z`|
|Linux `130691751567`|Build and install wheel；Packaged reference identity；Native application regression|3／3 completed／success；回归完成 `2026-11-11T17:53:39Z`|

Linux 的 Windows installer 为 completed／skipped，与原 workflow 条件一致，不计为 Linux 必要步骤；两个 Complete job 也均 success。最终 `ci-api-r4/ci-sample.json` SHA256 **`42af2eae7e46e4f0de3203485a649f8d3021a1eb387e23d0a5ac01c20156d72d`** 与原文重建结果相符。这里只确认官方 REST 报告的精确身份、终态和必要步骤，没有下载完整 job 日志或推断未读取的测试计数，也不是评审者直接联网成功。

**R6 最终结论：通过，C3b 对 `572c44e3f9621cd85d18447f14b436725df2eb64` 的精确交付终结。** 已核的 28 Git／mode／ready、r2 包／README、作者同完整 Ref 和本提交自己的双 OS 七必要步骤闭合；Spec／Standards 开放 **0／0**，无新增 finding。原普通 push 仍是 60 秒 TimeoutExpired、无退出 0 收据，后来 Ref 和本次成功 CI 不能改写该进程结果。原模型超时、分轮失败、403 与非终态均保留；F7 其余和项目整体，以及前述真实平台／执行环境／历史身份限制，不因此关闭。
