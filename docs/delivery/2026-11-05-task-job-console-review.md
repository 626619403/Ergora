# F4.4b2 原job日志与材料页面独立审查

日期：2026-11-05。审查者：新的独立上下文 `/root/task_job_console_review`。本审查收到原始需求、基线、改动文件和私有证据位置，先读项目约束、原始diff及相邻调用，再读本片交付叙述；未继承实现讨论。

## 范围与身份

- 精确基线：`1dbe969e433348eda60d6bff0271c13cd729b6ba`。本片仍未提交，生产diff只有 `src/ergora/data/console/tasks.js`（新增局部job消费者及事件入口）和 `src/ergora/data/console/app.js`（帮助文案）。未改变b1 Python、冻结参考内容、依赖、CSS或持久格式。
- 已审公开记录：`README.md`、`docs/USAGE.md`、`docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md`及[本片交付记录](2026-11-05-task-job-console.md)。工作树中的b1审查终结记录与下一片 `2026-11-05-f4-completion.md` 不属于b2生产实现或本次结论。
- 当前 `tasks.js` SHA256：`8a08d0ce1b2f61f0cd984a767b76cd0919e0e590f65319c730b63153d4a16de7`；`app.js`：`b75f6794bf316699098fe9013fb7407dc058fd7056f1ea281241703f8ba03d0c`。
- 最终wheel SHA256：`43e1211ea12c7522b928881d10b1c0497489e6a0a68930bbf86f10eb260c8ca1`。审查时独立重算350资源，源码、wheel和两套非editable安装完全相同；283冻结文件逐个与上述Git基线相同。核对验收HTTP进程的完整命令行及实际返回的两个JS，其摘要也等于当前包。

## 需求符合性结论

**本地范围通过，无finding。**

1. `tasks.js:501` 仅在原事件API返回的 `dev_submit` 调度行提供入口。邻接API仅为调度事件生成activity字段；b1继续核原提交/run、连续history前缀、context与请求envelope。`jobDialog`在 `tasks.js:329` 固定原run和event ID，首次取得已发布回执后保存record并隐藏目录重读入口，所有材料请求携带该receipt SHA。
2. 材料名只来自原回执，选择本身不请求文本；用户明确点击才以 `limit=8192`、原字符offset读取。UTF-8解码、NUL/非文本、摘要与路径验证继续由原b1边界负责。成功仅替换当前窗，随后推进offset；失败或not_found不推进offset、不丢失已读窗。末尾停止，换材料归零清窗，重开重新取得目录。missing/not_found分别保持未知，不显示成功或提供虚构文本。
3. 局部busy防止重复在途读取。`active`核页面连接、任务详情世代、run世代、当前dialog内容及open；材料世代另使切换后的旧响应失效。成功、异常与finally均按其实际负责的作用域更新UI。关闭/替换、编辑run、切任务/项目及离页均不能让旧响应写入现页面。
4. 所有新调用通过无body的既有 `api` 发GET；无定时器、后台读取、原生写或另一个运行账本。回执published/SUCCEEDED与工作流采用、任务结果及外部清理明确分开。README、使用指南及帮助文案与实际窗口和恢复行为一致，也保留Linux/WSL2原生运行时及后端完整读取成本的限制。原正式六阶段契约未改变。

## 可维护性、复用与性能结论

**通过，无finding。**

- 新生产函数 `jobDialog` 只有事件表这个实际消费者，留在现有任务详情所有者内合理；`readIndex`、`readWindow`、`active`、`updateButton`及窗口世代是这个私有异步交互的内聚实现。未制造单消费者公共模块或通用框架。复用现有 `api`、`modal`、`select`、`facts`、`pre`和安全文本node；材料正文作为文本插入DOM。
- guard各有可达场景：busy防连点；finished防末尾继续；空选择防未选文本；页面/任务/run/dialog世代保护异步生命周期；材料世代保护在途换材料。网络失败、原run消失、回执变化与非文本失败在相应边界处理。未发现可以直接删除的重复参数检查或冗余守卫。
- 页面不累积材料全文，保留一个8192字符窗口和既有回执；事件表仍最多200条。每窗重核历史和全部产物摘要是复用b1的实际成本，未增加隐藏缓存或声称窗口限制就是总IO/内存上限。浏览器48.57/85.72秒包含导航、截图及等待，只支持各自旅程观察，不构成吞吐或大日志性能基准。

## 实际核查及边界

私有证据根为 `.ergora/checks/f4-task-job-console/`，原生数据不随报告公开。

- 独立读取原始diff及邻接 `tasksView`、run输入/状态、事件页、公共UI/API、Web路由、`tasks.job`、`reference_task_evidence`、`reference_task_events`和摘要实现。执行当前13个JS模块的 `node --input-type=module --check`，全部exit0；`git diff --check`通过。本片五份公开文档284个本地链接路径存在；不将其扩大为全库锚点检查。
- 核 `package-identity.json`、构建/安装命令记录与日志、两安装direct_url及 `final-resource-syntax.json`，独立读取源码/wheel/安装文件并重算摘要。未安装、未构建新包、未跑重型回归。
- **真实浏览器证据：** `browser-real.js`与实际command中执行文本相同；command exit0，48.57秒；从原log提取的完整结果与 `browser-real-result.json`逐项相同。47个GET对应47个200响应，零写/零pageerror。审查脚本只对写请求设拒绝guard，对读取使用fallback，两个原run均经真实事件56选择plan job。核实际目录/选择不读取/8192窗口/末尾停止/重开清窗/空闲无新增请求断言。
- 独立将两run的model-log和execution-plan共四份材料逐窗重建，严格比较原UTF-8文件、完整字节/字符计数、SHA、偏移及next_offset；12515/13886字节日志各两窗，4002/4198字节计划各一窗。原回执等于浏览器record、重开record及b1 CLI输出，canonical SHA一致；原history事件56确为dev_submit，解码context的job ID及SHA匹配。`browser-real-verified.json`的摘要结论获得独立重核。
- **受控浏览器证据：** `browser-boundaries-expanded.js`等于实际command中执行文本；command exit0，85.72秒，原log结果等于 `browser-boundaries-result.json`。183个GET中24个job GET被路由拦截；其余任务/项目/状态/事件读取仍走原服务。503/not_found/missing及手动恢复，网络/原run未知/回执变化/NUL失败后的原位置，8192 Unicode字符与HTML字面文本、单窗/末尾/无轮询，单在途与七种材料迟到作用域均有实际断言。背景inert控件的合成事件只验证作用域失效，不表示普通用户可穿透modal，也不作为真实原生故障证据。
- **原数据保护：** 核前后snapshot命令exit0、原日志、快照脚本及两份JSON完全相等；覆盖139文件、三history/outcome、三claim/零active、两业务repo refs/worktrees/工作文件。审查时又只读重算139当前文件及三份保存history的摘要，读取SQLite lease并核两repo当前refs/工作区，与快照相同。保存的history事件数为329/348/112，两个正常结果REVIEW_READY、原取消CANCEL_UNCONFIRMED保持；本审查未重新连接Temporal查询实时history。
- 实际查看两张390px截图：governance目录与large计划，文本可读、长SHA换行；原脚本的两run目录/材料及指南宽度断言均通过。未宣称查看其余截图，也未在审查中重新执行浏览器。

## Findings与待验项

已审范围无阻塞或非阻塞finding；无待修源码项。本地实现、发行身份及上述真实/受控证据可以进入本片提交阶段。

本片当前未提交，精确提交归档、推送后实时远端SHA、当前UI候选的官方双OS CI及同片最终复核仍待完成。b1既有回归/CI只保留其原身份与范围，不替代b2候选的精确CI。完整F4.4c组合重开/服务退出与完整F4/F5/G0均未由本审查关闭。
