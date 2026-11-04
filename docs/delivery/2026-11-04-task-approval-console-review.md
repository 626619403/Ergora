# F4.3b：计划批准页面独立审查

日期：2026-11-04。审查者：`/root/task_approval_console_review`，新的 fresh-context 独立上下文。按原始验收、实际差异及原始证据审查，遵循 `AGENTS.md`、maintainable-project-delivery / independent-review 和 review-pr；未以作者交付记录代替源码或运行证据。

需求符合性：**本地实现与验收范围通过**。可维护性：**通过**。在下列范围内没有正确性或可维护性 findings，无待修源码阻塞。精确提交、双 OS CI 和实时远端身份仍待提交后同片复核；本报告不将 F4.3b 或完整 F4 记为最终交付。

## 精确范围与身份

基线为 `14100cd8d9efca270e0a93d9a6c1b77fde9ed66c`，审查时 HEAD 未变化、实现未提交。

- 生产差异仅 `src/ergora/data/console/tasks.js` 新增143行及 `app.js` 帮助文案一行。没有 Python、测试、CI、依赖或冻结 reference 差异。
- 文档包括 README、USAGE、PLAN、当前架构、详细计划、F4主索引、F4.3a交付及其终结审查状态，以及未追踪的 `2026-11-04-task-approval-console.md`，共9份。后续切片的未追踪取消页面计划不属于本次实现与审查范围。
- 独立重算全部348个源码文件、最终 wheel、开发/base两份 non editable 安装，逐项相同；核实际 `direct_url.json`，没有 editable 安装。最终 wheel SHA256 为 `4fcdb979ef45cb68ebf03dba075b58bcbd114bb00b4aab9f3d65437d49f5ffbd`；283个冻结文件与前置身份保持。
- 独立打开真实批准验收包 `f81edfd0983604c98736d620c24314f8a1e7b29467c90d6dc91f36366f500bf1`，核其身份记录；与最终包唯一文件差为 `data/console/app.js` 的帮助文本。两包 `tasks.js` 逐字相同，其 SHA256 为 `eab8d69b6a3b46971f799144e49f8f2266a6f4856122a9dda5fbbec2e1521858`；最终 `app.js` 为 `b30c2badcec9de5cce34c8cecc1d79c03d5aec7f7b7011deb61f2b4f07c07f2b`。

## 正确性、所有权与必要分支

逐行追踪 `tasks.js:329` 的局部批准控制器及其详情/原运行调用者，核 `api.js`、`ui.js`、`web.py:303`、`tasks.py:181` 和 `reference_task_approval.py` 的原有合同。

- 原运行查询只有非终态 `AWAITING_PLAN_APPROVAL` 才提供材料入口（`tasks.js:608`）；固定该次 run/plan，完整 GET 成功并装入三份全文后才启用 decision 读取（`:441`）。原有后端负责原提交/run、待批状态、原回执和材料摘要/大小等不变量；页面没有复制校验算法或后端状态机。
- 新批准必须先 GET 稳定 decision，且仅 `plan` 已读与 `not_recorded` 同时成立才出现明确确认（`:364`）。POST 使用该记录的项目修订、固定 run/plan 和 `confirm: true`（`:388`）；后端仍在实际派发时重核当前计划，旧修订/状态不会由前端绕过。
- 既有 decision 在材料旁没有恢复按钮，需转到独立原记录；恢复只在无当前材料的原记录模式对 `prepared/unknown` 开放，并只传原 intent SHA。`requested` 没有再投递按钮，文案不声称批准被采用或六阶段完成。
- 写前保存原 ID 并锁定输入；读、写失败都保留原 ID 的读回入口。会话只保存项目/任务范围的选择，手工原 ID 查回以后端记录为准。读取失败、材料不完整与未知写回复分别有必要的处理分支，没有把失败降级成可批准的成功状态。
- `active/current`、详情/读取序号、内容连接与 `runSequence` 分别对应切任务/项目、编辑 ID、关闭/替换弹窗、改 run 和迟到回包的可达边界。写处理中标志阻止重复确认；关闭只使展示失效，不声称撤销后端操作。原 ID 模式不依赖当前待批 phase，符合批准后恢复要求。

新控制器和 `read/show` 私有函数归现有任务详情所有者，调用只在该模块内部，未为单个消费者新增共享层或包装 API。`node/pre` 继续将模型材料作为文本，`form/modal/facts` 复用现有交互和长标识布局。提交与批准的合同不同，当前局部实现没有需要额外通用化的重复算法。

成本审查：没有新轮询、自动重试、后台调度或逐任务运行查询；材料读取按用户操作触发，复用已有每材料256 KiB/总响应1 MiB边界。没有新增测试矩阵或重复后端重型 CI。浏览器脚本区分正常读取、受控异常和真实信号，检查行为与恢复结果，并非只复述实现。上述为代码和实际请求证据下的成本结论，不构成吞吐、延迟或费用改善声明。

## 实际核验

证据根为本片私有 `.ergora/checks/f4-task-approval-console/`，大文件与运行数据未进入公开文档。

- 审查者独立执行13个 ES 模块 Node 语法检查、包/安装/冻结身份核算、`git diff --check`，均通过。读原架构检查命令及 stdout：最终行为同源包的8项通过；没有将它当浏览器行为证明，也未重复完整后端回归。
- 逐份审计四个成功浏览器脚本、命令退出和原结果：只读22 GET；受控边界40页面请求/4拦截POST且零转发写，另1辅助GET；真实批准57请求/2真实POST；最终包只读25 GET。独立计数合计144页面请求/6POST，其中4次为夹具、2次为真实批准，均零 pageerror。
- 两模板材料正文与 API 返回逐字比较；独立重算六份正文的字节数/摘要和原计划回执摘要。真实批准均先完整材料、GET未记录 decision 后明确确认一次。large-change 的真实 POST 经 `route.fetch(maxRetries=0)`实际获得200/requested后才丢弃页面回复；reload、重复读取和清空选择后手填原 ID 均恢复原 requested，未再发信号。
- 九类受控边界包含 prepared/unknown恢复、已有原决策与当前材料分离、材料/记录失败、编辑 ID、关闭替换、改 run、旧修订及跨项目迟到写回复。它们仅证明 UI 传输边界，未记为真实原生故障/信号。
- 实际查看桌面材料及最终390px原记录截图；原始测量两项目均页面390、弹窗352/scroll352。初包长SHA段落溢出、最终首轮一次提交记录子进程超时及v2隐藏帮助点击失败均保留，不计入四段成功数；没有据后续成功宣称暂时超时根因已修。
- 审查者独立只读 SDK 核验（07:06:50 UTC，exit0）：原54文件摘要保持；两 run 的各112事件原前缀，以及已保存 native-after 的整个后续前缀保持。governance/large 分别329/348个连续事件，均 COMPLETED，且各只有事件113的一个 `approve_plan`。实时 intent/attempt/result/owner receipt、精确 run/plan/request 和 signal 摘要相互绑定，与浏览器结果一致。07:07:49 UTC额外只读结果确认两者 `outcome.status=REVIEW_READY`。原06:35的 native-after 仍是当时 RUNNING 快照，未被重写为终态。
- 核 README/USAGE/帮助和架构的实际行为，9份范围文档329个本地链接/锚点、27条 README CLI parser 命令独立通过。F4主索引的新检查点与其保留的历史正文区分明确；前片A的CI及包没有被用作本片双OS通过依据。

## 限制与交接

本轮只写本报告；未安装、提交、推送、批准、取消或恢复任何运行，未重跑重型回归或整段浏览器旅程。实际页面验收依据经核实的原脚本/日志/响应及截图，实时 SDK 核验只读且有事件/时间上限。非 Chromium 浏览器、Windows页面运行、大规模同时操作及最大材料渲染延迟未另测，不据当前证据推导性能保证。

下一步应提交上述精确范围，再由同一审查者核提交树/最终包身份、精确双OS必要CI步骤及实时远端。取消、外部清理、导出、F4.4和完整F4继续按各自切片验收；两演示run的 REVIEW_READY 事实不关闭这些后续责任。
