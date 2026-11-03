# F4.1 正式任务只读页面：独立最终复核

日期：2026-11-03。审查者：`formal_task_console_final_review`，全新上下文，未参与实现。按本项目 AGENTS、`maintainable-project-delivery` 的 independent-review 和 `review-pr` 执行；先读[原始 F4 需求](../plans/2026-11-01-all-in-one.md#f4-正式任务控制台与运行视图)、[LC1 研究](../research/2026-11-02-low-code-editors.md)，再读实际源码与相邻合同，最后核[初审及中间复核](2026-11-03-formal-task-console-read-review.md)、[作者记录](2026-11-03-formal-task-console.md)和原始证据。

## 结论与交付边界

需求合规：**F4.1 源码与本地验收通过**。R1–R3 已修正并有对应反例；本轮没有新增高置信度 correctness finding。正式任务分页、冻结输入/角色/工作单元、本地 submission、固定原 run 的状态/候选/结果均沿用 F3 API。未查询、not_found、查询失败及原生终态分别显示，session 不保存权威执行事实。

可维护性：**通过，无阻塞 finding**。页面归属、共享能力复用、请求隔离和成本边界与现有轻量前端一致；没有新增状态机、通用框架、依赖或构建链。

这是提交前的代码与本地证据结论。当前候选提交、精确两 OS CI 和远端身份仍待实施者完成，再由本报告同片续核；此时不把 F4.1 标为完整交付。完整创建/提交、批准/取消/对账/导出页面及有界运行日志仍归 F4.2–F4.4，未实施；完整 F4/F5/G0 未完成。

## 实际范围与候选身份

检查时基线与 HEAD 为 `2add1bf3435738509462e6978d7f83742422ea6f`，分支 `refactor/architecture-foundations`，变更尚未提交。依据 `git diff`、status 与全部未跟踪源码，而非仅依据作者列举。

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

首包 targeted-command/log 为原三个文件 44 passed、1 个既有 warning，pytest 43.47 秒；只作为相同后端消费者的历史定向结果，不声称验证最终 DOM。F3 的 711 项及其旧 CI 同样只保留原身份。最终候选 CI 尚未取得，不能据上述历史结果推导。

## 审查动作、限制与待续核

实际执行了 Git 范围/差异检查、348 文件与两安装字节核对、冻结 283 身份比较、13 个 ES 模块 Node 语法解析、git diff --check、416 文件三方 hash 比较，以及上述脚本/原输出/结果静态核算。审查核算只写本片私有 `final-reviewer/`；没有运行测试、模型、构建、安装、HTTP、浏览器或服务控制，没有改源码、提交、推送或打开凭据。

没有新增阻塞 finding。下一步由实施者重核包含本报告的当前文档链接与差异、提交并推送精确候选，保存两 OS CI 和实时远端 SHA；随后同片补记最终身份复核，再关闭 F4.1。F4.2 的新行为须使用下一位全新上下文审查者。
