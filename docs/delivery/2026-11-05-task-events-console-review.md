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

## 精确提交、发行与实时远端复核（CI 待完成）

同片审查者于 2026-11-05 追加。已独立核定精确提交 `8f1489cb0a85fc75ea6e6f3cbb42172ba37ba98c`，直接父提交为原 e77 基线。实际 10 文件包括两个已审 JS、README/USAGE/PLAN、前 a1/d 的终结记账及本片交付/审查；后续 b1 的 Python、测试和新记录未混入。

审查者从精确提交的内存 `git archive` 重新计算 349 个资源摘要，全部等于原 manifest 及实际 `0edb0516…` wheel；已提交的两个 JS 与此前审查字节相同。本报告当时的 41 行版本亦精确进入提交。八份提交文档的实际字节 SHA 全部匹配 `static-documents.json`；已读实际检查脚本、command 和 log，8 文档/201 本地链接及锚点/27 README parser 命令、零缺失的范围与 exit0 一致，未把 parser 检查称为命令业务执行。

已读 `push-a2-rsa-command.json` 及原日志：普通 `git push origin 8f1489c…:refs/heads/refactor/architecture-foundations` exit0，原日志为 `e77edca..8f1489c`，无强推。本审查者另实际执行只读 `git ls-remote origin refs/heads/refactor/architecture-foundations`，exit0 精确返回完整 `8f1489cb0a85fc75ea6e6f3cbb42172ba37ba98c`；只在该进程环境给既有 SSH 命令追加指定 RSA 身份，未修改 Git 配置或读取/输出私钥。

精确提交、原验收发行身份、正常推送及实时远端范围通过，无新增 findings；CI 仍待本片官方原 HTML 和必要双 OS 步骤核对。本次未安装、重跑测试或访问原业务运行，尚不形成完整终结通过结论。

## 精确双 OS CI 与同片终结复核

同片审查者于 2026-11-05 追加，以下官方抓取/远端记录时间为 2026-11-04 UTC，更新前文 CI 待完成的历史状态。

审查者实际只读获取 [Portability 41882469707](https://github.com/626619403/Ergora/actions/runs/41882469707)：18:52:42 和 18:56:07 两次原 run HTML 均为 `Status Success`，实际链接绑定完整 `8f1489cb0a85fc75ea6e6f3cbb42172ba37ba98c` 及 `portability.yml`。job-groups 的实际返回集合为 `126758220983`、`126758221866`；各原 job 页的 selectedJobId 精确匹配，无借用 a1 或后续 b1 的 CI。

- [Windows 3.12，126758220983](https://github.com/626619403/Ergora/actions/runs/41882469707/job/126758220983)：构建安装 wheel、包内参考身份、原生回归、PowerShell 5.1 安装升级全部 `success`，均存在 data-job-completed；日志 URL 分别精确绑定该完整 A2 SHA、job ID 和 `/logs/4`、`/logs/5`、`/logs/6`、`/logs/7`。setup/checkout/post/complete 亦全部成功。
- [Ubuntu 3.11，126758221866](https://github.com/626619403/Ergora/actions/runs/41882469707/job/126758221866)：构建安装 wheel、包内参考身份、原生回归全部 `success/completed`，日志 URL 精确绑定该完整 A2 SHA、job ID 和 `/logs/4`、`/logs/5`、`/logs/6`；setup/checkout/post/complete 亦成功。仅 Windows 专属步骤 `skipped`，与审查者另读精确 A2 workflow 的 runner.os 条件一致。两 job 没有 failure、cancelled 或 timed_out 步骤。

18:56:07–10 的实际源页身份如下；本次在内存直接解析官方响应，原 URL、字节数、SHA 和步骤属性保留于工具执行记录，没有把本地此前 In progress 的旧源文件称为已刷新。

|官方来源|实际字节数|SHA256|
|---|---:|---|
|run 41882469707|163626|`88b8574cba36275e30aa72301c26c8767e6d63145a22117c513d5ad2382ddd34`|
|job_groups_batch?attempt=1|371|`bbd3ff07323ac95c20004f94bd644904116f1b8431cdc4c7756f888c9634f6d7`|
|Windows job 126758220983|166382|`b5c8d1ce050b6e907e84a9c0515e34eb75d576d15013a1a8661926f545224e5b`|
|Ubuntu job 126758221866|168290|`d2a8821465563aea6dfbf72aa6f34823682d0a396223144779b71f54c865b93d`|

本次核验的是官方原 HTML 的步骤结论、完成标志和精确日志地址，未下载完整日志正文或提取测试数量。首次 job-groups 读取因 Accept 头返回 HTTP400，改用 application/json 后成功；一次只读本地检查的自动审批 deadline 未执行、单次重试成功，均不视为 CI 失败或安全拒绝。没有触发 CI、重跑测试、安装或操作业务 run。

审查者又于 18:56:51 实际以既有 RSA 传输只读 ls-remote，exit0，远端分支仍精确为 `8f1489cb0a85fc75ea6e6f3cbb42172ba37ba98c`。结合此前已独立核定的 10 文件提交、349 资源与原验收 wheel、真实/受控页面行为及原证据保护，**A2 的需求、可维护性、本地验收、精确提交/发行、正常推送/实时远端及精确双 OS 必要 CI 的同片终结审查通过，无未解决 findings。** 实现者另收口状态追加后的文档静态与成功源页归档；本结论只覆盖 F4.4a2，不关闭后续 b/c、完整 F4、F5 或 G0。
