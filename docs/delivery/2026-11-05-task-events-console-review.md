# F4.4a2 原运行事件页面独立审查

日期：2026-11-05（Asia/Shanghai）。审查者：`/root/task_events_console_review`，本片新建的 fresh-context 独立审查者。按本项目 `AGENTS.md`、`maintainable-project-delivery` 及其 independent-review brief 执行；先读原始 F4.4a2 验收、实际 diff 和相邻调用，再核交付叙述及原证据。

## 结论与范围

**需求符合性：本地通过。可维护性：通过。所审范围无 P1/P2/P3 findings，无待修源码问题。** 手动 GET、原游标续读、同一活动 dialog 单在途、无轮询、最近 200 行、错误保留原位置、关闭/替换/编辑 run/切任务/项目/离开页面后的回复失效及重开从头，均有源码和对应原始验收证据。不从事件片段、Temporal 闭合或计数推出开发成功。

精确提交、该提交的双 OS CI 与实时远端 SHA 尚未取得本片终结复核；本结论不表示 F4.4a2 已完成远端交付，也不关闭 F4、F5 或 G0。下一 b1 设计及其后续 Python/测试变更不在此报告范围。

- 基线/本次检查时 HEAD：`e77edca96c9e662d9ce4d96a186e00be9d446672`；分支 `refactor/architecture-foundations`。a2 行为 diff 仅 `src/ergora/data/console/tasks.js`（新增 86 行）与 `app.js`（帮助文案）。
- 公共及交付记录范围：`README.md`、`docs/USAGE.md`、`docs/PLAN.md` 的本片状态与未跟踪新文件 `docs/delivery/2026-11-05-task-events-console.md`，已实际读回。三个 2026-11-04 交付/审查文件的当前 diff 是前 a1/d 的状态归档，未算成本片新行为；下一 b1 的记录亦排除。
- 固定验收 wheel SHA256：`0edb05167a1541423605efc584e636d01beeb6a5a848b76aaa74aa514f30f9a2`。审查者从实际 wheel、两份现存 noneditable 安装及精确 e77 基线的内存 `git archive` 重新计算：349 个包资源全部匹配 manifest，两安装一致；相对基线恰好只有两个 JS 改变，冻结 283 文件全部保持。后续工作树 Python 不用于替代本片身份。
- 两个已审 JS SHA256：`tasks.js` 为 `1a9010c81a51299fb609fb4045aa778e1f87bc8a9c2522beb682bccf07ebe7c0`；`app.js` 为 `8cefd56afc9e18208cdb042d017665beecc2eab05a0e4230e287dd8376e91e08`。

## 源码、所有权与成本

实际入口为 `tasks.js:1005` 的已查询原 run 按钮，唯一生产调用者在同文件的原运行详情。新增 `eventsDialog`（329 行起）留在既有 `inspect` 所有者内，直接捕获固定 task/path、详情 sequence 和 run sequence；没有另建单调用框架、公共包装或假复用。`app.js` 只同步帮助。已检查 `tasksView` 的列表/详情/运行读取、`app.js` 的项目刷新及 tab 替换，以及 `ui.js` 的 `modal`/`table`/文本节点和 `api.js` 的 GET/HTTP 错误路径。

入口 guard 防止旧详情按钮替换当前 dialog；请求前的 active/busy/finished 分别保护已废弃作用域、重复读取和终态结束。await 后的 active 丢弃迟到结果，finally 的 active 避免修改已替换控件。关闭由 dialog.open、替换由 content.isConnected、任务由 detailSequence、run 编辑/重查由 runSequence、项目/tab 更换由 view.isConnected 失效。均有可达场景；无需重复校验后端已有的游标、事件 schema 或原 run 归属。

`after` 只在有效成功页后前进；HTTP 错误和 not_found 均保留已有片段/计数/原游标。RUNNING 空尾部保留非空 next_after，终态空游标停用按钮。原有安全文本节点承载所有事件字段；Activity/signal 字符串按 Unicode code point 最多遍历 257 次，显示前 256 个及省略号。没有 innerHTML、持久化事件历史或成功判定。

每次打开或后续明确点击发一个 limit20/timeout20 的 GET，没有计时器、应用层重试或额外状态请求。同一活动 dialog 最多一个事件请求；关闭使回复失效，不取消已经发出的 GET。最多保存 200 行，concat 的临时数组最多 220 行，每次只重建至多 200×4 个表格单元；成本不随累计历史增长。后端的原验证/RPC和 1 MiB 响应边界保持 a1 合同，页面请求次数不当作 RPC 次数或性能基准。

没有新增生产模块、依赖、测试套件、CI 注册或断言。私有浏览器脚本覆盖真实来源、错误与资源生命周期，未把同一函数的实现另写成测试 oracle；已通过的 a1 Python 矩阵不因纯消费页面而重复扩跑。

## 独立核查的证据

原始材料位于私有 `.ergora/checks/f4-task-events-console/`，未复制运行数据或机器路径入公共文档。

1. **真实分页。** 独立解析 `browser-real.log` 的实际 Result，逐项等于 `browser-real-result.json`；command 中运行的源码与 `browser-real.js` 一致，exit0、84.37 秒。55 次 API 请求全部 GET，其中 41 次事件 GET，零 pageerror。两条原 run 为 329 事件/20 批及 348 事件/19 批；审查者直接从既存原 history JSON 重算摘要，逐事件比较 ID、类型、时间、Activity、scheduled_event_id、signal_name，全部相等。逐请求核 run/limit/timeout/原 next_after，首物理页 37 条的页内剩余无丢重；重开请求无 after 且整页等于原第一批。DOM 各批后缀/200 行、闭合尾部停用及静置无流量的断言已检查。
2. **受控边界。** `browser-boundaries-v2.log` 的实际 Result 与保存 JSON 相等，command 与实际 v2 脚本一致，exit0、52.31 秒。140 次 API GET，其中 21 次受控事件 GET，零 POST/pageerror。已检查实际脚本、原 cursor 序列及 11 项结果：503 原位置重试、not_found 保留、RUNNING 空尾部/手动新增/闭合、200 行后缀、256 code point/HTML 字面文本，以及六种作用域的在途防重入和迟到失效。背景 inert 上的合成操作只证明失效边界。原 `browser-boundaries.log` 的 55.48 秒 locator.evaluate 超时保留；实际失败在默认角色定位看不到 inert 背景“使用指南”，v2 的 includeHidden 修订与记录吻合，未把初轮计为通过。
3. **原证据保护。** 审查者直接比较 `native-before.json` 与 `native-after-verified.json`，解析内容完全相等：139 文件、三条原 history/outcome、两业务 repo 的 refs/worktrees/工作文件、3 claim/零 active lease。三份实际原 history 的规范 JSON SHA 与快照逐项相等。已读快照脚本的只读 SQLite、固定 run 查询及实际前/后 command/log；零 Running 是这些记录时点的观察，未在审查中重查业务服务。
4. **发行、语法和可读性。** 除上述实际 wheel/两安装/基线复算外，已核 HTTP identity 从本片 development 安装加载、13 模块 final-resource-syntax 与实际命令。审查者另轻量检查两个 JS 语法及所审 diff 空白，无错误。实际查看治理 390px、大改桌面、长字段 390px、帮助 390px 四张原截图；运行标识/动作/说明可读，表格沿既有内部滚动区查看。两个真实 run 的原布局值均为 viewport/page390、dialog/scroll352；不以几何检查单独代替截图阅读。

## 限制与收口

本次仅只读检查源码/原始证据、复算摘要和轻量语法/空白检查，并写本报告；没有安装、重跑浏览器/模型、查询原运行、取消、导出、对账、提交或推送。默认 sandbox 的 bwrap 启动失败后使用获批只读执行；未将基础设施失败记成检查成功。

没有需要修复复审的 findings。实现者须把本报告及实际结果回填本片交付记录与 PLAN，并保留“提交/精确 CI/实时远端待完成”。提交后由本审查者核精确 a2 提交与已验 wheel/资源身份、所有必要双 OS CI 步骤及实时远端，再追加同片终结结论。
