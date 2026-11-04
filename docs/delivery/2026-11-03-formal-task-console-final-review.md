# F4.1 正式任务只读页面：独立最终复核

日期：2026-11-03。审查者：`formal_task_console_final_review`，全新上下文，未参与实现。按本项目 AGENTS、`maintainable-project-delivery` 的 independent-review 和 `review-pr` 执行；先读[原始 F4 需求](../plans/2026-11-01-all-in-one.md#f4-正式任务控制台与运行视图)、[LC1 研究](../research/2026-11-02-low-code-editors.md)，再读实际源码与相邻合同，最后核[初审及中间复核](2026-11-03-formal-task-console-read-review.md)、[作者记录](2026-11-03-formal-task-console.md)和原始证据。

## 结论与交付边界

需求合规：**F4.1 源码与本地验收通过**。R1–R3 已修正并有对应反例；本轮没有新增高置信度 correctness finding。正式任务分页、冻结输入/角色/工作单元、本地 submission、固定原 run 的状态/候选/结果均沿用 F3 API。未查询、not_found、查询失败及原生终态分别显示，session 不保存权威执行事实。

可维护性：**通过，无阻塞 finding**。页面归属、共享能力复用、请求隔离和成本边界与现有轻量前端一致；没有新增状态机、通用框架、依赖或构建链。

首次结论基于提交前的代码与本地证据。2026-11-04 同片续核确认 F4.1 提交 `11e89cf44eb29fe9064bd0015417cf6bc54fdc5e` 与原包相符，实时远端一致；精确两 OS CI 为 Cancelled，Linux 回归未完成，因此 **F4.1 仍未完整交付**。完整创建/提交、批准/取消/对账/导出页面及有界运行日志归 F4.2–F4.4；本次不审查随后开始的 F4.2a 工作区改动，完整 F4/F5/G0 未完成。

## 实际范围与候选身份

首次检查时基线与 HEAD 为 `2add1bf3435738509462e6978d7f83742422ea6f`，分支 `refactor/architecture-foundations`，变更尚未提交。依据 `git diff`、status 与全部未跟踪源码，而非仅依据作者列举；提交后的精确身份见末节。

- 生产文件：`src/ergora/data/console/` 下的 `app.js`、`index.html`、`overview.js`、`style.css`、`workflow.js` 和完整新文件 `tasks.js`。
- 文档：README、PLAN、USAGE、architecture/current、详细计划、作者记录及初审报告。本报告是额外审查记录。
- 没有 Python、测试、依赖、CI 或冻结 reference 改动；相邻 `api.js`、`ui.js`、`state.js`、projects/workflow 消费者及后端任务/原生 runtime 合同用于只读追踪。

审查者独立核对 wheel SHA256 `3f287ecebdf37324a7960661f65e07a9713cfc1d277aa439e01370b25f044021`：348 个 package 文件与当前源码、完整开发安装及无 SDK 基础安装逐项一致，两份安装均为此 wheel 的非 editable 安装；283 个冻结文件与既有基线身份相同。`app.js` SHA256 为 `7dc59f7eae5b16b44e86d39822466de948b39b3379e9f0ba61fd8cd5b31ddae5`，`tasks.js` 为 `319bae8857f0555a5b0a55223180a82bc2907866a29f8b500f896fc4f9199f44`，`workflow.js` 为 `a4837a871f8883e7a29ca7f6ca66f8422abc6e5e58e13455bac2dcb24e3eec83`。六资产完整身份保存在本片私有 `final-reviewer/static-identity.json`。

## R1–R3 的独立处置

|原 finding|源码与反例核对|处置|
|---|---|---|
|R1：项目切换至新 dashboard 返回前旧视图仍有效|[app.js:20](../../src/ergora/data/console/app.js#L20) 在所选项目与快照项目不同时同步卸载；成功与失败均受 refreshSequence 限制。任务回包仍核视图连接和本次查询序号。最终脚本真正阻塞 B dashboard，在其等待/失败时释放 A 详情或状态，并覆盖等待/失败中切标签、重试、A→B→A 后旧 A 详情与旧 B 错误。|关闭|
|R2：原生 phase 与六阶段名称不匹配|[tasks.js:7](../../src/ergora/data/console/tasks.js#L7) 明确映射 INVENTORY/PLANNING/IMPLEMENTING/INTEGRATING/VERIFYING/REVIEWING；[tasks.js:164](../../src/ergora/data/console/tasks.js#L164) 先排除 terminal。与原 workflow 的名称逐项核对，14 种受控投影包含六个活动阶段、初始化、待批准、清理、各终态及 terminal 仍携活动 phase 的反例。|关闭|
|R3：刷新卸载快照影响既有草稿保存回包|同项目刷新保留既有快照；[workflow.js:224](../../src/ergora/data/console/workflow.js#L224) 在访问 app.data.drafts 前同时核当前项目与实际快照项目。同项目保存待回→刷新，以及 A 保存待回→B→A 且新 A dashboard 未回时释放旧保存均已覆盖，后者不恢复旧工作流或访问空快照。|关闭|

这些保护位于拥有对应生命周期的原模块，不要求新状态层。清空快照仅用于项目归属变化；工作流自己的 epoch/revision 继续处理较新编辑。没有以公共刷新逻辑替代草稿编辑所有权。

## 需求、结构与成本

`tasks.js` 的唯一生产调用者是 `app.js` 的页面路由。它拥有一个完整正式任务页面，与已有视图的划分一致；同页的 facts/disclosure、分页、详情和 run 查询是凝聚的私有展示逻辑，不是为假设复用建立的公共抽象。overview 和左导航只负责进入已有路由，HTTP 与合同仍归原 api/tasks/runtime。

列表固定扫描上限 20，按服务端 next_after 前进，匹配项为空时仍允许游标翻页；异常记录单列。首入页面至多增加一次列表 GET 和两次并行详情/submission GET，只有明确读取原 run 才增加状态 GET，没有逐任务 Temporal 查询、轮询或长连接。工作单元沿原受支持模板的既有界限显示；JSON 披露使用原 DOM 工具。这里没有吞吐量、大任务容量或日志性能基准结论。

冻结绑定来自任务自身快照；缺少旧快照明确显示缺失，没有从当前项目配置补写历史。所有来源文本经现有 text node/pre 写入。Promise.allSettled 使回执读取失败不阻断可读合同；失败没有补造执行状态。列表、详情、run 请求序号分别处理重复读取、任务变化及 run 输入变化；视图连接检查处理离开页面，app 刷新代际处理项目转换。session 只记录项目、页面、任务和 run 选择，重载后页面明确要求重新查询状态。

README、USAGE、当前架构和活动记录对只读范围、状态归属及后续 F4.2–F4.4 的说明与源码一致。LC1 原来较粗的 F4.1 命名没有被用来声称正式启动/批准等完整旅程已经交付。

## 证据复核

审查者没有重跑浏览器。逐份比较以下原 CLI 的 Result 与保存 JSON，剥离 CLI 外层包装后比较实际执行代码体与保留脚本，均一致；五个命令 exit 0，无 CLI Error、无 pageerror。阶段反例中的受控 HTTP 503 会产生预期的资源错误，不等于页面脚本异常。

|最终候选材料|能证明的范围|
|---|---|
|browser-normal-clean|5 个真实原 run 的 phase/candidate 与 API 一致；41 GET；reload 恢复选择但状态明确重查；390px 无横向溢出、无可选 null 文本。|
|browser-boundaries-clean|真实 not_found、真实 API 扫描窗 2 的空页/前后游标；受控迟到 run/跨项目详情、缺角色快照、文本安全及缺注册；累计 75 GET。|
|browser-review-fixes-clean|R1/R2 的 14 种 phase 和真实等待窗口反例；新增 54 GET，以上三段累计 129 GET。|
|browser-refresh-draft|R3 的两个反例；22 请求含 2 个完全拦截、未转发后端的模拟 draft POST，其余为真实 GET。不能用它声称完成真实草稿持久化旅程。|
|browser-visual-clean|另 9 GET，真实原 run/candidate；390px scrollWidth=390。审查者实际查看桌面和手机 viewport 截图，中文可读；未执行的 visual-clean-v2 不作证据。|

失败辅助脚本、重复监听器造成的 123/225 计数以及中间包的 235 次累计记录均没有并入最终干净会话统计。真实 Temporal 停止/重开恢复记录属于旧 3cf 候选，不能改写为最终包重新执行；当前包有真实原 run 查询和受控失败窗口的直接证据。

独立核 `native-before.json`、`native-after.json` 以及当前实际文件，416 个路径及 SHA256 完全相同。范围是 tasks/requests/receipts/artifacts/approvals/fences 和选定 process/ergora JSON；不包含 SQLite 或日志，也不继承旧 104 文件快照的覆盖结论。

final-shutdown 的命令、脚本与结果明确核 5 个原 run 为 COMPLETED、最新 run 未变化、无 RUNNING workflow；正式 shutdown 返回 confirmed，随后 daemon not_running、socket/PID 消失，Temporal SQLite 保留。执行环境恢复时失效标记的 PID 不存在、socket 拒绝、inode/属主复核，以及 final-lifecycle 的 7233/8987 连接拒绝有各自记录；不是用 F3 旧停栈记录代替本次收尾。该状态来自保留的原始证据，审查者没有启停或查询服务。

首包 targeted-command/log 为原三个文件 44 passed、1 个既有 warning，pytest 43.47 秒；只作为相同后端消费者的历史定向结果，不声称验证最终 DOM。F3 的 711 项及其旧 CI 同样只保留原身份。首次本地审查时最终候选 CI 尚未取得，不能据上述历史结果推导；随后取得的实际结果见末节。

## 审查动作、限制与待续核

实际执行了 Git 范围/差异检查、348 文件与两安装字节核对、冻结 283 身份比较、13 个 ES 模块 Node 语法解析、git diff --check、416 文件三方 hash 比较，以及上述脚本/原输出/结果静态核算；包含本报告的 8 份变更 Markdown 共 305 个本地链接/锚点通过。审查核算只写本片私有 `final-reviewer/`；没有运行测试、模型、构建、安装、HTTP、浏览器或服务控制，没有改源码、提交、推送或打开凭据。

没有新增阻塞 finding。首次审查待续核的提交和远端身份现已核对；两 OS 验收仍缺 Linux 回归成功证据，不能关闭 F4.1。后续 CI 或修正按精确身份继续记录；F4.2 的新行为须使用下一位全新上下文审查者。

## 2026-11-04 同片提交、远端及精确 CI 续核

审查者只读检查提交 `11e89cf44eb29fe9064bd0015417cf6bc54fdc5e`，其父提交为原基线 `2add1bf3435738509462e6978d7f83742422ea6f`。该提交实际包含 14 个文件：6 个 console 资产和 8 份 Markdown，没有 Python、测试、依赖、CI 或冻结 reference 改动。通过 git ls-tree/cat-file 读取提交内全部 348 个 package blob，再独立计算 SHA256，与原 `3f287ecebdf37324a7960661f65e07a9713cfc1d277aa439e01370b25f044021` wheel、package-identity 和首次审查资产身份全部相符；其中冻结 reference 为 283 文件。两份安装与本地验收仍绑定这个原包，不能改绑到当前工作区。

本轮实际执行 `git ls-remote origin refs/heads/refactor/architecture-foundations`，返回同一完整 `11e89cf44eb29fe9064bd0015417cf6bc54fdc5e`，提交与当时实时远端一致。工作区的 tasks.js/style.css 后续差异属于 F4.2a，未读作 F4.1 候选，也没有要求它们与旧包相等。

精确 [Portability run 41662193234](https://github.com/626619403/Ergora/actions/runs/41662193234) 的官方 HTML 与 selection 记录均指向该完整提交；run 最终状态是 **Cancelled**。审查者直接读取原 HTML，而没有执行假定 Success 的 verify-ci.py。run 列出的两个 job ID 与各自 HTML 的 selectedJobId 一致，各已成功步骤的 log URL 绑定同一完整提交。

|精确 job|官方记录与可得结论|
|---|---|
|[Windows / Python 3.12，126007988855](https://github.com/626619403/Ergora/actions/runs/41662193234/job/126007988855)|job succeeded；Build and install wheel、Packaged reference identity、Native application regression、Windows PowerShell 5.1 installer and upgrade 全部 success。Windows 必要步骤通过。|
|[Ubuntu / Python 3.11，126007988217](https://github.com/626619403/Ergora/actions/runs/41662193234/job/126007988217)|job cancelled；构建安装和冻结身份步骤 success。官方 annotation 为 “The job has exceeded the maximum execution time of 20m0s”；Native application regression 的 data-conclusion 为 null，没有成功结论，回归未完成。|

上述证据位于本片私有 ci/ci-html-run-selection.json、ci-run-latest.html 和两份 ci-job HTML。原 run HTML SHA256 为 `0c9778443678e63b2449fd736732ec4d0ac33baaf3310305c969e22d253de84a`，Linux job HTML 为 `eeadf5578ad71d523eec83572b65a201e3b0db35d43b18bfae02b4c18127c210`，Windows job HTML 为 `7c25c96e46a5dca712a3e568fb5d801e38f9d0aa8a0eaccee1062f5b1f443892`。超时注释不能确定具体耗时测试或产品缺陷原因；本报告不补造 Linux 测试数量或通过结果，也不使用仍在诊断中的 local-regression.log 作通过证据。

本轮仅增加 Git blob/hash、官方 CI HTML 和实时远端的只读核对，写入只限本报告；没有运行测试、模型、构建、安装、服务或提交推送。源码/本地验收与可维护性结论保持通过，R1–R3 保持关闭；**精确两 OS 验收未通过，F4.1 完整交付继续待定**。本次状态补记不审查 F4.2a，也不重复启动本地服务。

## 2026-11-04 同源有效CI最终续核：F4.1通过

以下为原独立审查者`/root/formal_task_console_final_review`的最终续核，由根代理归档。审查者两次报告更新在执行前遭自动审批服务deadline，原待定结论保留为历史，不冒称当时已更新。

生产提交为`11e89cf44eb29fe9064bd0015417cf6bc54fdc5e`，同源CI候选为`2137a95418879d48cce557016caa5c7f0d6a6a1b`。审查者直接读取完整Git diff stat和实际workflow差异：仅CI日志包装及7份文档共8文件，应用/测试树不变，套件/矩阵/20分钟/退出码保持。结合前次独立348文件核算，仍绑定原`3f287ecebdf37324a7960661f65e07a9713cfc1d277aa439e01370b25f044021`包及冻结283；V4独立审查者另成功重核348 Git blob与旧wheel/manifest一致，原输出`3b376f`。当前F4.2a源码及安装不参与本片。

本审查者通过只读网页直接打开官方[run41679431542](https://github.com/626619403/Ergora/actions/runs/41679431542)及两job：run为Success，[Ubuntu126068814666](https://github.com/626619403/Ergora/actions/runs/41679431542/job/126068814666)和[Windows126068815158](https://github.com/626619403/Ergora/actions/runs/41679431542/job/126068815158)均succeeded。保存的selection/status绑定完整2137；Ubuntu构建安装/冻结身份/原生回归三项success，Windows另含PowerShell安装升级共四项success。V4审查者另直读selectedJobId及step log URL绑定各job和2137。

原HTML位于私有`ci-regression-progress/ci/`；已读身份记录中的run SHA为`c8604f4a5eea7338669bf8420e7bc4b492a07f37617e40c77769d2d8027c1aac`，Ubuntu为`45da850d4a9ea650d2432a32fc14a89b7cd3179cac9853082b7ffe336440cbb1`，Windows为`69f17a611be5113ef3e2e4ff9237bf61915490914008534d8723cd3cae273878`，本审查者本轮重hash脚本未执行，不记为亲算。live远端由V4审查者实际查询，退出0返回完整2137，输出`8056fc`，精确UTC未记录；本审查者自己的两次查询审批超时，未冒称成功。

旧CI41662193234仍为Linux超时取消；新CI补同源门禁，不证明旧超时根因或性能提升。原浏览器、416文件及停栈证据保持原身份。R1–R3关闭，0未解决findings，F4.1完整验收通过；F4.2a及完整F4不在此完成结论内。本轮未运行测试、模型、构建、安装、服务或提交推送。
