# F7d-D2 来源任务页面独立审查

审查日期：2026-11-12。协调者 `f7d_source_task_console_review` 为本片新的 fresh-context 独立审查者；Spec 和 Standards 分别由两个 `fork_turns: none` 子审查者读取原始要求后完成，未继承作者讨论。依据为 AIHERO `code-review`、`maintainable-project-delivery`（含 independent-review）及 `codebase-design`。

**最终判词：完整20文件候选的 Spec／Standards 均通过，开放 finding 0／0；SP1/P3 状态记账已修正并由原 Spec 审查者复核关闭。包、安装检查、实际页面、内置审查全文读取、公开投影及拥有资源清理已核。** 精确提交 `c69dedf82512ce87d6a72a249626c26dadca4c3c` 的 Git／ready／最终静态、r1 包、普通提交／推送及作者 SSH Ref 原件通过；自己的 CI `43146853654` 原始 HTML／收据已独立离线核实双 OS 七必要步骤成功，**D2 的 S4 精确交付关闭**。独立官方 Ref 限流403及此前在途样本原样保留，不宣称评审者直接远端读取成功。下文待交付／待终态表述属于当时审查记录，最终状态以末节终核为准；本结论不关闭 D3a、F7 或项目整体。

## 固定范围与身份

项目及文档归属均为 Ergora；原始规格为[本片计划](../plans/2026-11-12-source-task-console.md)，实现／验证状态见[交付记录](2026-11-12-source-task-console.md)。基线及此次静态审查时的 HEAD 都为 `d60a9d82be80a52d3e6ca0257772af3b3a26a084`，`git log <baseline>..HEAD --oneline` 为空。因此实际审查对象为 `git diff <baseline> --` 加全部 untracked 正文；不以空的三点提交差异代替工作树。

最终清单与实际 **13个 tracked 差异＋7个 untracked 文件** 完全对应，共20件；文本差异、新正文／JSON、两张公开截图均已检查：

- 页面源码3件：`src/ergora/data/console/app.js`、`issues.js`、`tasks.js`。
- 入口／当前架构4件：`README.md`、`docs/PLAN.md`、`docs/USAGE.md`、`docs/architecture/current.md`。
- 上层计划2件：`docs/plans/2026-11-01-all-in-one.md`、`docs/plans/2026-11-11-project-trackers.md`。
- 本片新增7件：`docs/plans/2026-11-12-source-task-console.md`、`docs/delivery/2026-11-12-source-task-console.md`、本报告，以及 `docs/delivery/evidence/2026-11-12-source-task-console-{acceptance,self-review}.json` 和 `2026-11-12-source-task-console-{desktop,mobile}.png`。
- 前片 D1 记账4件：`docs/plans/2026-11-12-issue-console.md`、`docs/delivery/2026-11-12-issue-console.md`、`docs/delivery/2026-11-12-issue-console-review.md`、`docs/delivery/evidence/2026-11-12-issue-console-acceptance.json`。它们属于 d60a9d8 的交付／CI 记录，不作为 D2 的运行或 CI 证据。

最初两轴静态范围为8件 tracked＋2份新正文；同片最终复核已扩大到上述20件，新增材料未借旧模型判词覆盖。审查报告和后续状态记账不要求递归审查。

相邻所有者已核 `ui.js`、`api.js`、`state.js`、`task-composition.js`、`tasks._definition / _composition`、`issue_snapshots.snapshot`、`issue_sources.bind_snapshot`、既有 HTTP 路由与 `task-definition-v3`。亦核既有创建／恢复、受影响测试及唯一 portability 工作流；未改源码、安装、重跑产品／模型或写入外部平台。

## Standards

**最终审查通过；硬规范违例0，AIHERO possible smell 0。**

已按 AGENTS、两技能及 independent-review 核对完整工作树。app 只临时承接 SHA；来源表单及新私有函数留在 tasks owner，复用原 snapshot、composition、definition3 与创建／恢复路径。未读取来源、缺执行组合、迟到回复等 guard 均有可达保护对象；未复制 provider 准入或状态机。

新增 `resetSource / loadSource` 只服务本对话框的资料和生命周期，适合保留在现有 owner；没有据同文件重复调用虚构跨文件复用。`sourceSequence` 保护来源请求代际，原 `sequence` 保护冻结预览代际；它们分别处理不同的在途请求，不能据外观相似删除其中一个。

每次显式来源读取只有一个本地 GET，无新增轮询、全量循环或持久缓存；未新增 test、CI 或依赖，无本片重复运行设计。完整文本展示沿原安全 DOM helper。首段驱动中止后仅沿原 ID 续验，截图补段只补视口；没有为记账变化重复产品或模型。下文脚本耗时是其实际旅程范围，不推为稳定性能基准。

本轴只读，未安装或跑测试。最终20集合、公开投影／两图、生命周期／清理及模型范围已核；源码仍等于 r1 包和安装副本。当前记账补充不改变产品及原测试范围。D2 未交付自身提交／Ref／CI，本轴通过不关闭精确交付。

## Spec

**最终审查无产品缺项、产品越界或高置信实现错误；开放 finding 0。**

原规格第7–11行对应的临时 SHA 导航、显式完整离线读取、固定工单编号、definition3 与无来源 definition1／2 路径均已核。`tasks.js:194–202` 在同 SHA 已读取且有执行组合时提交 definition3；完整准入继续由原 schema、`tasks._definition` 和 `bind_snapshot` 拥有。

`sourceSha` 的 input 先重置来源，再冒泡到原表单的 input handler 使预览失效；清除按钮显式完成两者。来源读取由局部代际、creationLocked 及 dialog/content/view 存活保护，关闭重开替换 content；切项目的原 refresh 同步替换旧 view。正文沿 `node / pre` 安全文本显示；创建及未知结果继续沿原 ID 的 creation／resume，没有隐式执行或来源回写调用。

D1 的精确 Git／Ref 与 CI 各次样本单独保留。其原评审者已在原报告终核 CI43142680273 的11份原 body／收据及双 OS 七必要步骤并关闭 D1 精确交付；协调者已读该状态追加，不计作 D2 运行或 CI 证据。原规格第7–11行的实际页面行为、完整来源及旧对象保持已由下文原件补核。未知创建实测为已发布后的原 ID 读回，没有触发 pending 页面的 `resume-create`；不冒称本轮浏览器覆盖了该分支，原实现未改且相关既有安装套件已核。

**SP1/P3 已关闭：** 最终审查时计划第20行的 S1 仍写“待安装及页面验收”，与 S2 完成状态矛盾。最小修正为“已实现，安装及页面验收见S2”，原 Spec 审查者已核当前字节。此项为状态一致性问题，无需重跑产品。

## 包与安装验证

r1 wheel SHA256 为 `2773db5b6d67c09aab13893662ae538a95a6256cfade19bd5339ca8defc1e42d`。协调者独立从原文件重算：448件 source／installed 包文件集合及字节完全相同；wheel RECORD453行、installed RECORD458行的逐件 digest／size 无误；reference manifest 的283件冻结文件身份一致。三份改动 JS 的 module 语法检查与基线工作树 `git diff --check` 通过。

直接核读 r1 的 `installed-validation.json`、stdout 和 reference 原件：`test_issue_tasks / test_task_creation / test_web / test_architecture_boundaries` 共 **65 passed／pytest 110.52秒**，命令收据 exit0／113.11秒；`reference verify` exit0。两份 stdout SHA256 均与收据相同。没有重复运行这些检查。

## 实际页面、旧资料与清理终核

已读取驱动、原 stdout 的 Result、结构化结果及原 HTTP，而非只接受汇总布尔值：

- 首次默认 Chrome 不可用而退出，未跑产品；使用已有 headless 配置后成功，未安装软件。主段 **22项／8.78秒**后在私有 fieldset `isDisabled` 判断处中止，原失败保留。原 DOM 表明 fieldset 原生 `disabled`／`:disabled` 和内部 input 的有效禁用均成立；实际来源创建已发布，但回传被故障夹具替为503。
- 原 ID 续段 **21项／7.01秒**通过，查原 creation 得到 published 并进入正式任务详情，没有重发创建；补完 GitLab 大变更、缺来源拒绝、未登记提示和390px范围。两 provider 的完整安全来源、definition1／2／3 与 input6／7 各按实际步骤保留。
- 生命周期 **41项／11.34秒**通过。五处经过真实 HTTP 的浏览器延迟回复分别覆盖 SHA 编辑、清除、关闭重开、切项目及旧预览。修订变化明确拒绝；刷新后捕获修订2与执行修订3分别保留；改绑 manual 后历史仍完整可读，但来源正式准入拒绝。最终两视口截图补段仅 **2项／1.65秒**，未重跑前述旅程。

协调者独立重算全部 **120份 HTTP 请求／响应原字节、大小和 SHA**，与逐件收据及 trace 一致。13次本地 POST 恰为10次 preview＋3次原创建；三个创建分别为 `legacy-source-ui`、`source-gh-ui`、`source-gl-ui`，原 definition、revision、intent、preview 及七份合同内容一致。合同摘要按原规范的 canonical JSON 核对，不误称文件格式字节摘要。来源 v7 envelope 与原完整来源、preview 全文相同，来源创建503没有增加第二次同任务 POST。

使用只读 SQLite 连接核对六份旧快照的完整 payload、SHA、首次保存时间不变，并核原两份完整 manifest 树不变。外部 provider GET 总数仍为准备阶段的6，浏览器新增0，方法只有 GET。Agent／task-link／review-link／writeback 四表均0；运行队列、回执、产物、workspace、submission 不存在，原运行目录只有合同／创建记录。

拥有服务 PID＋starttime 已退出；两端口再次只读探测均关闭，原 HTTP／provider 线程停止，命名浏览器 close 收据 exit0。清理结论仅针对所属进程、端口、线程与浏览器，不推广到全系统。

## 内置模板完整读取与公开投影

实际内置结构审查 run `7c9365f47cdc4c9a94848b4ed75ee617` 为 Codex／gpt-6.1-sol／high，**approve／155.40秒**。协调者用原 installed inspector 核 manifest、prepared 和 actual 身份，再独立比较 prompt／stdin／protocol、admission binding／policy、scope/native 收据和原结果。原模板只增加局部版本、证据资源和材料限额，原提示／Skill 字节保持；没有正式执行授权。

从原 native 流核到1次 list 和13次 read：五 scope 均连续 UTF8 到 null；120,396字节附件由7页完成，两次 base64 回应在同 offset 缩小重读，失败调用0。八件完整附件的封存字节／长度／SHA 与原 index 相符；其中六件源码／schema 仍等于最终源码，两份计划／交付只代表冻结时刻。原结果 SHA256 `4826e5dad414510eb903885491c22041c554ab2f3da0e1eb8b300f3e7c428e54` 与原回执及公开结果相同；四个采样所属 PID＋starttime 无存活。模型范围没有扩大到后补公开文档、包、测试、浏览器或后端独立性。

公开[验收投影](evidence/2026-11-12-source-task-console-acceptance.json)逐字段等于原包／检查／分段浏览器／清理原件的对应字段，保留失败及分段范围；[自身投影](evidence/2026-11-12-source-task-console-self-review.json)等于去除私有路径后的原 identity／audit，original_result 完整相同。用量保持后端自报；cached input 为输入子集，不重复相加，不推费用、模型理解质量或成功不同后端独立性。

两张公开图已实际查看并与 final 原 PNG 逐字核同：桌面1440×1000／268,069字节／SHA256 `408633b13f143c1f872c9d0b73e51cb49bc0eae955c06a5bbe5d8606eb251a06`；移动390×844／80,567字节／SHA256 `28b984c74c59aea1b4ac70892c5b864de6a99e1b56ffe3969bddb2331845bd54`。完整 SHA 与来源可读，HTML 外观标题原样显示，正文通过原文本区域完整可滚动读取，不据截图推断真实平台兼容。

## 最终静态与交付边界

作者 `static-r1` 原收据覆盖20件、345个本地 Markdown 目标、6个当时加载的秘密值，JSON／whitespace／个人路径检查 issue0。协调者核对该收据的完整文件身份与实际20集合；之后 S1 更正、D1 CI 进展及上层／本片审查记账属于已读状态补充，不把旧 hash 当最终冻结字节。最终冻结前由作者补核相应静态身份；没有读取凭据值，也不把上述检查称为 anchors、外部 URL 或 Mermaid 渲染验收。

本轮未重新安装或运行产品、浏览器、Agent／模型。未验证真实 SaaS、原生 Windows 正式工作区执行、OS 隔离或重新运行六阶段；未取得 D2 自身提交／Ref／必要 CI，精确交付继续。D1 后补 CI 由其原评审者处理，范围不转授 D2。

**最终汇总：Standards 0项；Spec 共1项记账P3、已关闭、开放0。完整20文件候选的独立本地审查通过；普通提交／推送、精确 Git／Ref 和本提交自己的双 OS 必要 CI 待交付。**

## S4 精确 Git／ready／普通推送与 Ref 原件

对象固定为 **`c69dedf82512ce87d6a72a249626c26dadca4c3c`**，唯一父提交为原基线 **`d60a9d82be80a52d3e6ca0257772af3b3a26a084`**。本节是提交后的状态追加，不将当前报告或未来工作树当作已提交字节。提交内本报告 SHA256 为 **`6ebf355fabb1bac8ebef14208f22304b7b3b4f292aeaf70ed5789c1fffab3bcf`**。

禁用 object replacement 与 lazy fetch 后，从原对象头与字节重算 commit、根 tree、118件所经中间 tree，以及所有候选／包 blob 的 SHA1。原根 tree 为 `dc8c148295e516770ce338daa1ca27ad4364b0ac`；父→子恰为20件差异，全部普通 blob／`100644`。每件原内容、大小、SHA256、mode 均与完整封存副本、ready 清单及 `static-r2` 身份一致。ready 清单 SHA256 为 **`17c8b88d214a2018121f6af0bca15453ebead7d6fc4c30c4bd89f2943674c4d0`**。

最终 `static-r2` 的20件全部等于 ready／提交，**347个本地 Markdown 目标／当时6个加载秘密值／issue0** 保持其原检查范围；没有读取凭据值，也不将其扩大为外部 URL、anchor 或 Mermaid 验收。已独立从精确提交的全部448件 `src/ergora` blob 逐字核同 r1 wheel 完整包集合；METADATA 的原 README body 也与提交内 README 逐字相同。wheel SHA256 仍为 **`2773db5b6d67c09aab13893662ae538a95a6256cfade19bd5339ca8defc1e42d`**。没有重装或重跑产品／模型。

普通提交原回执 **exit0／1.13秒**，stdout724B／SHA256 `770611869ca75a9e1d73c020e858b100b58827bd79c2b8a030181f418a940fc7`，stderr空。普通 push 原回执 **exit0／7.83秒**、`force:false`，stderr98B 明确从 d60a9d8 更新到 c69dedf，SHA256 **`1521850131be2822f22a2c6a4812bc364e5c3b5732fd6bf466cf5a861a4fb896`**，stdout空。没有重推或改写前片失败。

作者一次 SSH `ls-remote --exit-code` 原回执 **exit0／1.63秒**；86B stdout 逐字为完整候选 SHA、tab、`refs/heads/refactor/architecture-foundations` 和换行，SHA256 **`0bb2794ac4eb439b1c9e26a1ae977bcc174434d25135301466472f844813daa3`**，stderr空。这是作者该次实际 Ref 观察，不称评审者直接 SSH 成功。

评审者于 **`2026-11-12T03:16:12Z`** 只尝试一次匿名官方 Git Ref GET，URL 为 `https://api.github.com/repos/626619403/Ergora/git/ref/heads/refactor%2Farchitecture-foundations`；最终 URL 相同，无 retry／redirect／凭据读取，约 **1.29秒，HTTP403／280B**。原 body SHA256 为 **`cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`**，表示 API 限流。请求／响应身份与失败原件已保存；没有补造远端身份或宣称独立直接网络成功。

**本轮结论：精确20 Git／mode／ready／static-r2、448件 r1 包／README、普通提交及 push exit0、作者同完整 SSH Ref 原件通过，无新增 finding；Spec／Standards 仍开放0／0。自己的双 OS 必要 CI 终态待核，S4 精确交付尚未终结。**

## S4 本提交双 OS 必要 CI 终核

本次仅离线读取作者封存的官方公开 HTML 原字节及收据，不再请求网络、安装或重跑产品／测试／浏览器／模型。对象继续固定为 **`c69dedf82512ce87d6a72a249626c26dadca4c3c`**；当前工作树已有后片 D3a 改动，不以当前源码代替本提交。CI 为 [Portability run 43146853654](https://github.com/626619403/Ergora/actions/runs/43146853654)，分支 `refactor/architecture-foundations`，触发为 `push`／`2026-11-12T03:14:29Z`。

已独立重算全部 **10份 HTML 原 body 与对应收据**：5份 run、Linux 2份 job、Windows 1份 job，以及较早 Actions 列表和 commit checks 各1份。逐份 HTTP200、请求／最终 URL 相同，大小、SHA256 与收据相符；页面中的仓库、完整提交、分支、`portability.yml` 和 run／job 链接互相一致。原 `ci-run-html-r1` 至 `r4` 均为 `In progress`；Linux `ci-job-130946572425-html-r1` 中回归步骤仍为 `null`／在途、无完成时间和 `Complete job`。这些原件未被终态覆盖。作者 `ci-html-r1` 至 `r5` 的投影字段均与各自原 HTML 相符。

终态 run 原件为 `ci-run-html-r5`，采样于 **`2026-11-12T03:37:22.175228+00:00`**，状态 **`Success`**，body **157,162B／SHA256 `59ee8c4d5ec5aea5a34309295f44c3809581ce5684ea45219117635a179c3f65`**；收据 SHA256 **`d9eb847da1e53afc4e3e27cfc32289456838d2246fbed105d38d4120e9953852`**。

从精确提交读取 `.github/workflows/portability.yml`，SHA256 为 **`81c168fdb140f44ccfdca497003e452355c9164a6ed6f8dfb8fa31729a1943ca`**；其矩阵为 Ubuntu／Python3.11 与 Windows／Python3.12，共用必要步骤4–6，Windows 另需步骤7。以下 UTC 时间来自原 `<check-step>` 属性，七步均为 **`data-conclusion="success"`**、具有 `data-job-completed` 且开始／结束时间有效、顺序一致并处于对应 job 区间：

| OS／job | 步骤 | 开始–结束（2026-11-12 UTC） | 终态 |
| --- | --- | --- | --- |
| Windows／130946572914 | 4 Build and install wheel | 03:14:43–03:15:32 | success |
| Windows／130946572914 | 5 Packaged reference identity | 03:15:32–03:15:33 | success |
| Windows／130946572914 | 6 Native application regression | 03:15:33–03:29:26 | success |
| Windows／130946572914 | 7 Windows PowerShell 5.1 installer and upgrade | 03:29:26–03:30:22 | success |
| Ubuntu／130946572425 | 4 Build and install wheel | 03:14:35–03:14:55 | success |
| Ubuntu／130946572425 | 5 Packaged reference identity | 03:14:55–03:14:55 | success |
| Ubuntu／130946572425 | 6 Native application regression | 03:14:55–03:33:47 | success |

Windows 终态原件 `ci-job-130946572914-html-r1` 为 **160,311B／body SHA256 `021ebd48a741c6b8906f39e28b599ae938b541c98ed92bc1140fcf2317060267`**，收据 SHA256 **`70d342de0557018df46c193d0ff89f85aa9da507922015746a578f54e9d78004`**。Linux 终态原件 `ci-job-130946572425-html-r2` 为 **161,711B／body SHA256 `4536b72386fc2b76b850a16e95903977a567a7cf2ff544007b590c1b3eab0a57`**，收据 SHA256 **`3d86a49804facebc5099c931abd1df883ae19c214386c78fc6f5510f2d950280`**。两 job 原页面均为 `data-job-status="completed"`、可见 `succeeded`，`Complete job` 步骤15为 success，分别结束于 **03:30:24Z／03:33:47Z**；header 分别记录 **03:30:26Z／15m53s**、**03:33:49Z／19m17s**。Linux 步骤7为 **skipped**，与工作流的 Windows 条件一致。

七必要步及其余成功步骤的 `data-log-url` 均逐字指向 `/626619403/Ergora/commit/c69dedf82512ce87d6a72a249626c26dadca4c3c/checks/<本 job ID>/logs/<本步骤号>`。本核验确认官方 HTML 所示的本提交必要步骤终态，未取得完整 job 日志，不从页面推算测试数量或宣称新的本地运行。原匿名 REST CI 请求的 HTTP403／280B／SHA256 `cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735` 及前节独立 Ref403 继续保留，不改写为成功 REST／直接 Ref 读取。

**最终关闭结论：D2 的完整20文件 Spec／Standards 开放0／0，精确 Git／ready／包、普通提交／推送及作者 SSH Ref 原件通过；本提交自身双 OS 七必要 CI 步骤成功，S4 精确交付关闭。** 此追加仅更新审查与交付状态，不把后补报告字节称为 c69dedf 已提交内容；D1 证据不转作 D2，D3a／F7／项目整体及真实 SaaS、原生 Windows 正式工作区执行、OS 隔离、六阶段重跑和成功不同后端独立性均不在关闭范围。
