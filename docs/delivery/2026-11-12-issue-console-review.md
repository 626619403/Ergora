# F7d-D1 独立两轴评审

评审日期：2026-11-12。协调者为新的独立审查者 `f7d_issue_console_review`；Spec 与 Standards 分别由两个 `fork_turns: none` 子审查者阅读原始要求后完成，未继承实现讨论。规则依据为 AIHERO `code-review`、`maintainable-project-delivery` 及 `codebase-design`。本记录属于 Ergora 自有 docs。

**最终判词：完整19文件候选的 Spec／Standards 均通过，开放 finding 0／0；SP1/P2 与 ST1/P3 均已关闭。** 精确提交 `d60a9d82be80a52d3e6ca0257772af3b3a26a084` 的 Git／ready／r4包、普通提交／推送、作者SSH Ref及自己的双OS七必要CI步骤原件均已核，F7d-D1精确交付终结。一次独立官方Ref限流403、两次REST 403及中间非终态／HTML 404保持，不称独立直接网络成功。后续D2不在本片判词范围。

## 固定范围与身份

基线为 `572c44e3f9621cd85d18447f14b436725df2eb64`，已直接解析核实；当前 HEAD 同基线，提交列表为空。标准三点差异为空，因此本次实际检查基线至工作区的差异，并完整读取新文件：

- `src/ergora/data/console/app.js`、`index.html`：导航登记。
- `src/ergora/data/console/issues.js`：未跟踪新文件，首轮 r2 为149行，SHA256 `0551a78ba990d3d4965f5f6ebcae45c5f0326ed84344e9c126e7de6d7900640b`；修正后 r3 为152行，SHA256 `99e12603cdb1f6aaa815b21fb91ff408a7b876902fcfd7faa5b149ae51bb87fd`。首轮记录时摘要取样已发生在修正之后，本次按两份原 wheel 分开更正，避免把149行身份与152行摘要混用。
- 原始规格为[本片计划](../plans/2026-11-12-issue-console.md)，进度入口为[交付记录](2026-11-12-issue-console.md)及[PLAN](../PLAN.md)。其他未提交的 C3b 文档是前片 CI 结案记账，不属于本片行为。

相邻调用者检查覆盖 `app/api/ui/state/tasks`、既有 Web 四个工单读取路由、`issues.show/capture/snapshots/snapshot`、快照身份所有者、打包规则及既有相关测试。首轮时 README／USAGE／架构更新、浏览器补验与内置审查证据尚待实现者提供，未把未完的交付门当作产品 finding；后续实证与最终范围分别记在下文。

## Standards

首轮开放 finding **0**，可维护性静态范围通过。

未发现违反 AGENTS、当前架构所有权或既有合同的产品变更。`issues.js` 是独立导航视图，唯一生产调用者为 `app.js`，其所有权按实际视图职责成立；展示、详情读取及分页函数保留为凝聚的私有实现。传输、DOM与页面选择沿原 `api/ui/state`，来源规范化、revision准入、数据库和 provider 分派仍由后端拥有。

检查了 smell baseline；没有形成 Duplicated Code、Middle Man 或 Speculative Generality 等 finding。与任务页相似的局部分页代码使用不同返回合同及展示，尚无足够理由增加共享请求框架。DOM／项目身份和序号保护有真实生命周期场景，不是无效断言。没有新增生产测试、CI、依赖、轮询或业务存储；每页明确请求20条，没有发现需删除的冗余测试／CI或明显性能问题。静态检查不替代实际运行成本测量。

## Spec

首轮开放 finding **1**，未修正时阻塞本片规格通过；同片修正复核见下文。

### SP1 — P2 / wrong：迟到的保存响应覆盖更新的历史页选择

位置：[`issues.js:91`](../../src/ergora/data/console/issues.js#L91) 的保存成功回调。原规格要求：“项目切换、tab离开、较晚响应不能覆盖新选择”。

可达场景：项目已有超过20份快照，操作者读取工单并启动较慢的“重新读取并保存快照”；保存等待期间点击下一页，已选择或已看到第2页。旧保存响应返回后只检查 `active()`，随后无条件执行 `pageIndex = 0`、`loadHistory()`。因此会跳回第1页，或以新增 `pageSequence` 淘汰用户更新的分页请求。`selected(sequence)` 只保护正文，未保护这条分页副作用。两个独立源码阅读路径均确认该场景；当前没有把首轮浏览器分页比较失败当作这一缺陷的动态复现。

最小修正：保存开始时记录历史请求代际，保存成功后仅在期间没有更新历史选择时重置并刷新；否则保留用户所选页和更新请求。需补验“保存等待→选择第2页→释放旧保存”的实际页面路径。

其余已读范围未发现 missing／partial／scope-creep：完整正文与来源记录经安全文本 DOM 展示，当前观察与保存事实有明确标签；manual／改绑项目仍可离线阅读旧来源；只有显式读取／保存触发 provider；没有任务创建、回写、授权、额外调度器或数据库。六阶段、candidate／approval／claim及冻结参考文件未被产品差异修改。

## 实际证据与边界

协调者与 Spec 审查者只读核对了 r2 私有原件：非 editable wheel，448包文件，两份 RECORD已核，源码与安装包同字节，283冻结；既有来源／快照／Web／架构四个 suite为 **45 passed / 227.60s**。运行器墙钟记录为242.67秒；没有混用两者。原 stdout SHA256与运行记录一致，`reference verify` exit0。本次未重跑测试、安装或联网。

浏览器首轮 `browser-main-r1.json` 的工具 exit0、内层 `passed:false`：18项完成后在 `previous restores same bounded page` 比较失败。已直接读原脚本和结果，等待函数只观察页号文字，而产品加载期间保留旧页号，故原件不足以独立判定分页产品错误；保留失败，等待按完成的表格与请求核对的补验。未将其宣称通过，也未据本地 loopback 范围推导真实 SaaS／Windows或正式六阶段验收。

首轮汇总：Standards **0**；Spec **1**，最严重项为 **SP1/P2**。待 SP1 修正及受影响补验后复核；最终文档、内置审查与完整浏览器证据仍待终核。

## r3 同片源码、安装与内置审查复核

SP1 的源码逻辑缺口已关闭，受影响动态补验仍待提供。Spec 原审查者复核了保存开始记录 `historySequence = pageSequence`，以及仅在序号未变化时重置并刷新历史；用户后续翻页／重新读取列表都会同步更新序号，因此旧保存不能覆盖更新的页选择。Standards 原审查者确认该 guard 位于分页状态的实际所有者，不与详情序号或DOM／项目检查重复；没有增加全局请求框架或业务状态。两轴均未发现新增 finding。

完整读取了新增 README、USAGE 与当前架构差异。显式读取、再次读取保存、页面修订、有界游标分页、摘要排序、全文离线读取、manual／改绑历史和文本展示说明均与真实四个用例一致。19个第一方 ES module 数量和模块图的新 `issues.js` 边正确；没有把后续来源任务／候选动作写成已提供的页面功能。当前计划和交付尚在跟进，不将其未完成状态计为产品缺陷。

协调者只读独立重算 r3 wheel SHA256 `bf7ab2c07cc8500a103e27e8ca57a25fbedc5c8349df06398c5cee92962505c0`、448个包文件、wheel／安装 RECORD453／458及283冻结，全部通过；当前源码与安装包逐字相同。相对 r2 只改变产品 `issues.js` 和发行元数据 METADATA／RECORD。没有将旧 r2 的45项结果冒称为 r3 重跑；新候选主页面原件 `browser-main-r3-start.json` 为 **38项／4.57秒／passed:true**、无页面错误，覆盖两provider完整主旅程、20＋4分页、正文和身份、文本呈现、manual／offline及390px。此前 r3 未点击导航的零检查超时、已关闭会话导致的生命周期未执行仍保留，不算通过；迟到保存及生命周期完整补验待终核。

内置结构模板 run `b0bf5ffbb79143069663015f1f68b3c6` 为 Codex／706.84秒／原结果 `approve`。协调者阅读审计脚本及原判词后，以 r3 安装环境重新执行其全部只读核验核心，去掉末尾报告写入：manifest→prepared／actual input→prompt／stdin／protocol→admission→五scope→native原件→原结果身份通过；完整 scope list及成功 UTF8 分页连续重建至 `next_offset:null`，无失败或base64代替全文。九份完整附件87,459B与冻结索引、当时实际输入及 r3 复核取样时所列九文件相同；四个采样所属进程均无存活。原结果摘要为 `52c4d5b9ea41bcc0ce80abfa68dc8a6dd5bb54227f900ac1535364da892a48df`。模板 verdict 只覆盖其冻结源，未借它批准后来 r4 展示或附件外的最终公开文档、浏览器、清理及交付；未称双后端成功、模型质量或平台权限验收。

本轮状态：Standards **0**；Spec源码开放 **0**，SP1的最终动态关闭仍待本候选补验及清理原件。提交／远端／自己的CI属于后续精确交付门，本轮不提前关闭。

## 最终 r4 全候选复核与本地出口

最终清单为19文件：本片15件包括4个产品文件 `app.js / index.html / issues.js / style.css`，README／PLAN／USAGE／当前架构，片计划／交付／本报告，以及验收JSON／自身审查JSON／两张PNG；另4件是 C3b 的原计划、交付、评审及验收JSON的精确交付记账。协调者完整核对这些差异与原件；两原轴审查者分别复核最终源码和公开使用／架构说明。C3b记账未扩大本片产品范围，也未借前片 CI 或模型判词批准本片。

最终 `issues.js` 为153行，SHA256 `e2650144e65df9c99d13debc75006d49bb8b648ee9e11a65a9b9f4878157d88a`；`style.css` SHA256 `4c09228e2e3759e269f6af561c14cec5cd9c404fcd3c2ddb3bdae1a1af25593f`。r4非 editable wheel SHA256 `6bb6d45e0411796ed97579e5f0ad01bc9e758c42b8a2242a6050d5ed71751660`。协调者独立重算448个包文件与当前源码／安装逐字一致、wheel／安装 RECORD453／458及283冻结，全部通过。相对 r3 仅产品 `issues.js / style.css` 和 RECORD 改变：历史每份资料改为单列编号／标题／来源／时间／查看按钮，复用既有长文本换行样式，加本视图560px滚动区；分页保持在滚动区外。无异步、后端、依赖或持久合同变化。

### Standards 最终复核

两原轴独立读完布局增量，未形成结构或 smell finding。新类仅约束实际来源历史所有者，复用 `table / task-choice / form-note`，完整保留元信息和原查看入口。没有为单视图新增全局抽象、重复后端验证或长期测试／CI；本片测试采用原后端套件及有具体静默错误风险的实际浏览器路径。最终实测未显示需阻塞的性能问题，循环读取和provider操作仍由显式点击驱动。

**ST1/P3（记账，已关闭）**：19文件终核发现 C3b 原计划 R6 状态仍写“原独立及自己的CI待核”，与同候选另外三份原结案记账不一致。依据 AGENTS 的计划／实际状态同步规则，要求只更正该状态；实现者已同步为 CI43068731988 第四样本双OS七必要步骤及原评审通过／精确终结，并保留原push60秒超时无终态。协调者读回确认。此项没有产品修改或新增验收要求。

### Spec 最终复核

**SP1/P2 已关闭**：最终 r4 原页面 `browser-capture-page-green.json` 为 **2项／2.36秒／passed:true**。实际持有原保存回复，先选择并显示第2页，再释放保存；第2页保持，额外历史请求 **0**。已读相应脚本、HTTP原件与结果，旧 r2 red 的额外 GET 保留为历史失败，没有冒称旧样本已观察到完成后的跳页。

最终 r4 主旅程原件为 **38项／4.48秒／passed:true**，两provider完整正文／身份、安全文本、重新读取保存、重复保存不变、20＋4游标往返、manual／平台失败时离线读取、失败可见及390px宽度均通过。r3 生命周期原件为 **18项／58.31秒／passed:true**，5处原HTTP延迟覆盖改编号、较晚快照、分页重置、离开tab及capture后切项目；另覆盖旧修订拒绝、已保存但回复503时不自动重发及provider失败不留部分快照。r3 这组结果保持其原包身份；r4标记／CSS增量由独立源码审查和受影响主旅程／SP1实际补验覆盖，不称r3生命周期在r4重跑。旧驱动 Promise、会话关闭和DOM代际等待失败仍按原件保留。

### 原件、公开投影与清理

协调者只读重算三轮共 **135** 份 HTTP 请求及响应原字节／SHA（r2／r3／r4为40／67／28）；每轮25份旧快照通过纯离线 loader 的完整payload／摘要／来源／首次时间验证，共75份。外部provider方法均为GET，本地非GET仅snapshot POST；Agent／任务关联／review关联／writeback表均0，无tasks目录，未发现意外派工或回写。r3／r4的所属PID已退出且原端口无LISTEN，三轮清理回执的服务／provider线程停止；命名浏览器close原回执exit0。结论限这些拥有的资源，不推导全系统进程清理。

两份公开JSON的运行／读取审计／原结果投影与私有原件逐项一致；两份公开PNG与 r4 原截图逐字一致并已实际查看，桌面与窄屏的标题／来源／时间可见，390px整页宽度为390。未声称锚点、外部URL、Mermaid渲染、真实SaaS账号、原生Windows正式执行或新六阶段模型验收。

作者 `static-r1` 原结果为 **19文件／206本地Markdown目标／6个已加载秘密值／issue0**，JSON／whitespace／个人home路径检查通过；协调者仅核其有范围结果和文件身份，不读取凭据值，并独立检查当前206个相对目标均存在、`git diff --check`通过。该静态样本之后的变化恰为 PLAN、本片计划／交付／验收JSON、本报告及 C3b 状态同步；均是已读记账，由实现者最终冻结前做相应静态补核，不把旧hash当最终字节。r2的45项／227.60秒与reference verify仍只属于r2，未冒称最终包再次运行。

**最终汇总：Standards 共1项记账P3、已关闭、开放0；Spec 共1项P2、已关闭、开放0。完整19文件的独立本地审查出口通过。** 普通提交／精确Git与Ref／本提交自己的双OS必要CI继续执行，未完成前不称本片精确交付终结。

## D4 精确 Git／ready／推送与 Ref 原件终核

对象固定为 **`d60a9d82be80a52d3e6ca0257772af3b3a26a084`**；后续同分支工作树不作为本次包或已交付产品的比对来源。只读核对本地原件，没有安装或重跑产品／模型。禁用 object replacement 与 lazy fetch 后，从原对象头和字节重算 commit／根tree及blob的SHA1；唯一父提交为原基线 **`572c44e3f9621cd85d18447f14b436725df2eb64`**，父→子差异恰为19文件，均为普通blob／`100644`。每件原内容、大小、SHA256及mode都与封存完整副本、ready清单和 `static-r2` 原文件身份一致。

ready清单 SHA256 为 **`65ea988b8c07ca1ae0260f358e1115fa18e23c25a7e68a0ff8d7f06f037db3b8`**；提交内本报告的原快照 SHA256 为 **`b6f510da04685ad4bf89e2339afb0a9d16a62ca7edcf7ddee8fb8dfba201331f`**。本节属于提交后的状态追加，不冒称原commit内字节。`static-r2` 的19件全部等于ready／提交，206本地目标、当时六个加载秘密值和issue0保持原检查范围；没有读取凭据值或将其推为外部URL／锚点／Mermaid验收。

已独立从该提交的全部448件 `src/ergora` blob，逐字比对 r4 wheel 的完整448件包文件并重算blob身份；文件集合及内容全部相同。wheel SHA256仍为 **`6bb6d45e0411796ed97579e5f0ad01bc9e758c42b8a2242a6050d5ed71751660`**，METADATA 中原始 README body也逐字等于提交内README。未使用未来工作树或重复运行已通过套件。

普通提交原回执 **exit0／1.16秒**，stdout SHA256 `017bd42a54af315fb8a796907430706bbaa6ad0715fbeab910a82b5509affe98`，stderr空。随后普通push原回执 **exit0／9.02秒**、`force:false`；原stderr明确从572c44e更新到d60a9d8，98B／SHA256 `ca90683f65cea99a70bcd6d204f8c375ac25f671134e8904b8f3f0c0a10ef3b8`，stdout空。没有重推或改写前片push超时。

作者一次SSH `ls-remote --exit-code` 原回执 **exit0／2.14秒**；86B stdout逐字为完整候选SHA、tab、`refs/heads/refactor/architecture-foundations`和换行，SHA256 **`49f44c38ae964ff220be897d8b69e356752f05abc151ab1228dbb5fb359996d0`**，stderr空。这证明作者该次实际Ref观察与候选相符，不称评审者直接SSH读取成功。

评审者另于 `2026-11-12T02:38:41Z` 只尝试 **一次**匿名官方Git Ref GET，路径为 `https://api.github.com/repos/626619403/Ergora/git/ref/heads/refactor%2Farchitecture-foundations`；最终URL相同，约1.00秒，实际 **HTTP403／280B**，body SHA256 **`cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`**，原响应表示API限流。没有读取凭据或重试；此失败不补造远端身份，也不冒称独立直接网络成功。

自己的CI首个官方API读取原件同为 **HTTP403／280B**；已核请求筛选精确完整候选、原body大小／SHA及来源收据相符。它只证明该次请求失败，没有run／job终态或必要步骤证据，不代表CI失败或通过。按当前授权不轮询，等待作者提供本提交自己的终态原件后同片终核。

**本轮结论：精确19 Git对象／mode／ready／static-r2、448件r4包／README、普通提交及push exit0、作者同完整SSH Ref原件通过，无新增finding；Spec／Standards仍开放0／0。自己的双OS必要CI终态待核，D4精确交付尚未终结。**

## D4 自己的双OS CI原件终核：精确交付终结

仍由同片原审查者离线核验，只追加本报告，没有网络、产品／模型重跑或D2源码读取。对象固定为 **`d60a9d82be80a52d3e6ca0257772af3b3a26a084`**、原19件ready及r4包；先前已核的Git／mode、包／README、普通push和作者Ref不受未来工作树变更影响。

独立重算四份run HTML、两份job HTML、commit-checks HTML、两份失败HTML及两份REST响应共 **11份**原body的大小／SHA；逐份与receipt中的请求URL、最终URL、HTTP状态相符。四份run页面均绑定原仓库、完整候选commit链接、原分支及 `portability.yml`，展示同一个push运行 **43142680273**。前三轮只记录 `In progress`；r1没有加载job ID，r2／r3只发现Windows ID，`required_steps_passed:false`保留，没有补造当时的Linux结果。

|run原件|HTTP／字节|原状态／body SHA256|
|---|---|---|
|`ci-run-html-r1`|200／150,627|In progress／`242931fec7e662a314451c0627a9593e4094a4b97394ef83b6ee790fd3f0cb3b`|
|`ci-run-html-r2`|200／153,386|In progress／`fb316c487829679890f0f3c99707add55d3d7d205c635a76971d4b1315d6767a`|
|`ci-run-html-r3`|200／153,386|In progress／`2a28852a9b6d6368cce9a17fe616cfd30fbdb0bd20ab75bb49d007ae021f5f51`|
|`ci-run-html-r4`|200／157,092|Success／`b71c10b67c77b35b485fa06a0c270b8204f03e915fd42bf7574df32fcc6681aa`|

第四份原run页面才完整发现两个job名称与ID：Windows／Python3.12为 **130933140723**，Linux／Python3.11为 **130933141021**。官方完整commit的 `commit-checks-html-r1` 同样绑定该run和两个job；其HTTP200、154,276B、body SHA256为 `b62438b07eeeeaee789dce8c8612e878c1f89d90e5c95fbca1b6d0326140d087`。没有把此前导航或matrix的404当作成功读取。

从固定提交内原workflow确认三个共同必要步骤和仅Windows执行的installer。独立解析两份原job HTML的 `check-step`，逐项核名称、step number、`success`、`data-job-completed`、有效起止时间及完整候选的log URL；所有必要步骤时间落在各自job区间，两个 `Complete job` 也均success／completed：

|原job|必要步骤与终态|原body|
|---|---|---|
|Windows 130933140723|4／4：Build and install wheel；Packaged reference identity；Native application regression；Windows PowerShell 5.1 installer and upgrade，step4–7全success／completed。回归完成02:49:20Z，installer完成02:50:05Z，job完成02:50:08Z|200／159,728B；SHA256 `06f06b0408d98c6d0552926c653a0c28267946eeeb06a53348dda451e08ec4df`|
|Linux 130933141021|3／3：Build and install wheel；Packaged reference identity；Native application regression，step4–6全success／completed。回归完成02:56:58Z，job完成02:56:59Z|200／161,641B；SHA256 `09cb0f37efd23603a80e0777d4dfe077b1305ebcbaa7b524029c22a490f068da`|

上述完成时间均为 `2026-11-12` UTC。Linux的Windows installer为skipped，符合原workflow条件，不计Linux必要步骤。七项 `data-log-url` 均精确位于 `/626619403/Ergora/commit/d60a9d82be80a52d3e6ca0257772af3b3a26a084/checks/JOB/logs/STEP`；这里只核HTML提供的身份及终态，没有读取完整job日志或推断未读取的测试计数。`ci-html-r4.json`的两份receipt摘要、body摘要与七项投影逐项等于原文，完整样本SHA256为 **`f23a8e0839eb31500a9d30689985ddde44ace73c001e37d693ebbd84534f7ec5`**。

历史失败原件保持：`ci-api-1/2`均为匿名REST限流403／280B、SHA256 `cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`；`ci-navigation-html-r1`为404／0B；`ci-matrix-html-r1`为404／226,121B、SHA256 `cb352bae884c061afc2b2e2fab4b3fd5659e4afdd0e1b53c7b312a8de9f1a516`。这些请求失败及前三份非终态没有回写为成功；本轮没有补做直接网络请求或宣称REST／全日志成功。

**D4最终结论：通过，F7d-D1对 `d60a9d82be80a52d3e6ca0257772af3b3a26a084` 的精确交付终结。** 原19Git／ready／r4包、普通提交／push exit0、作者同完整Ref及本提交自己的双OS七必要步骤闭合；Spec／Standards开放 **0／0**，无新增finding。原独立Ref403、驱动／构建失败、REST403、HTML404及分轮边界保持；D2、F7其余及项目整体不因此关闭。
