# F3.4e 与正式开发 CLI/API 阶段独立综合审查

2026-11-03，审查者 `/root/f3_completion_review`，全新独立上下文。先读取原 [F3 需求与验收](../plans/2026-11-01-all-in-one.md#f3-正式开发任务-cliapi)、[F3.4 验收拆分](2026-11-03-formal-task-acceptance.md)、AGENTS.md 和实际 tracked/untracked 差异，再对照作者的[阶段收口记录](2026-11-03-f3-completion.md)、[旅程记录](2026-11-03-formal-task-journeys.md)及 c/d 原独立报告。遵循 maintainable-project-delivery 的 independent-review 和 review-pr；本报告不替代各原实现切片及 c/d 的独立审查。

**需求符合性：范围内通过。** 当前两开发模板的统一 CLI/API 功能、最终发行身份、真实正常/异常旅程、恢复边界和手册/架构证据具备 F3 登记收口条件。本次无新增 findings；[c 审查](2026-11-03-formal-task-normal-review.md)和[d 审查](2026-11-03-formal-task-recovery-review.md)各自的一项证据范围 P2 均已关闭。提交、推送、远端 SHA 核对及最终状态登记仍由作者完成；本报告不声称这些交付动作已经完成。

**可维护性：范围内通过。** 本切片只整合文档与验收记录，没有生产、测试、依赖、构建或 CI 变化。抽查最终 F3 调用链、持久意图、原 ID 归属、条件分支导出、外部清理和 SQLite 锁边界后，当前架构表述与实际所有者一致；没有发现本切片新增抽象、重复状态机、越权归属或性能退化来源。

**精确身份与审查范围**

生产/测试身份为 `7139d1a85cdce13689d75471620da8dd143156a8`；入场及核算 HEAD 为文档提交 `a170dd12cf7f672e7dffb9c89ebc03b398506091`，分支 `refactor/architecture-foundations`。实际 `git diff` 相对入场基线包含 README.md、docs/USAGE.md、TRAINING.md、AGENT_BACKENDS.md、PROJECTS.md、PLAN.md、architecture/current.md、plans/2026-11-01-all-in-one.md 和 delivery/2026-11-03-formal-task-journeys.md；`git ls-files --others --exclude-standard` 另包含 f3-completion、formal-task-normal-review、formal-task-recovery-review 三份新报告。本报告为本次审查新增文件。

核对范围包括上述完整内容、公开说明的相邻段落，最终 tasks/CLI/Web、reference adapter、runtime/submission/approval/cancellation/export/reconciliation、services 与原 connection/ingress/执行器契约，以及固定发行、c/d 私有命令和原始证据。没有打开凭据文件，也没有执行模型、测试、构建、安装、服务启停、提交或推送；仅写本报告与授权的私有 completion-reviewer 目录。

**综合证据核对**

|验收项|本次独立复核与适用范围|
|---|---|
|最终发行身份|重新计算 wheel SHA256 为 `c7411ae956108c2e23544fd476c0106e95b65a1d77a3a19c20a14caa3f5f8ceb`；源码、wheel、开发安装和无 SDK 基础安装的347文件逐份一致，两安装均为非 editable。冻结清单283文件逐份匹配，37个顶层 Python/12个前端模块保持|
|回归与精确 CI|原最终回归命令退出0；原 log 为711 passed、19 skipped、36 subtests passed，1个既有 Starlette 弃用警告，1722.63秒。重算原最终审查索引的10份来源摘要/字节数均一致；直接解析保存的官方 HTML，确认 [CI41621015706](https://github.com/626619403/Ergora/actions/runs/41621015706) 的 Ubuntu3项、Windows4项必需步骤均 success，步骤 log URL 绑定完整7139候选。没有重跑或实时重新请求 CI，也没有把 Linux 计数套给 Windows|
|正常两模板闭环|独立读取302/326事件的完整原 history，核事件连续、原 spec 输入、提交 memo 和原完成 outcome；两原结果保持 REVIEW_READY。重新读取业务 Git，main/HEAD仍为各自原基线，正式导出分支及独立 checkout 精确命名记录中的候选。真实模型、可信检查、独立审查、4/11项候选测试的详细证据由 c 原审查负责，本次不重跑|
|异常/恢复|独立核92/81/40事件的三份原 history、spec/memo和终态；两取消结果仍为 CANCEL_UNCONFIRMED，检查失败仍为 BLOCKED，失败任务记录明确未调用模型且拒绝导出。173份原证据索引的摘要/字节数全部匹配；精确 claim、signal 和 worker/进程历史的细节由 d 原审查负责|
|CLI/API 重开与只读范围|直接核原正常44请求与恢复13请求，共57请求；正常104文件前后快照相等，当前字节摘要仍匹配。公开记录明确这104文件未覆盖8份批准 journal及2份 owner 回执；d也明确直接采样的是helper/child/driver/timeout，monitor只有持久 terminal 证据。没有用当前状态补造历史采样|
|最终专用栈关闭|核 close-services.py 与 completion-shutdown.json：先检查5个固定原run/latest为COMPLETED且本次 Temporal无RUNNING workflow，再由正式services shutdown返回confirmed/not_running。独立确认当前所管socket/PID文件消失且Temporal SQLite仍保留。服务已经关闭，本次没有再次发起workflow查询或复起栈|

本次实际执行 `PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -B .ergora/checks/f3-formal-journeys/completion-reviewer/audit.py` 通过，独立结果保存在同目录 audit.json。该脚本只读、hash、解析原 HTML/JSON、查询 Git 和解析 CLI 参数，不调用任务操作。它还独立确认生产/测试/脚本/依赖/CI相对7139无差异，以及README的26条独立ergora命令均由当前parser接受。首次核算12份目标文档的330个本地链接/锚点无缺失，加入本报告后的复核也通过，最新计数及逐文件摘要见audit.json；作者350口径另包含相对7139变动的两份b2原文档，二者不冲突。`git diff --check`通过。

**结构、契约与性能判断**

CLI 和 Web 的正式路由均消费 `tasks`，页面没有拥有工作流状态。`tasks._native_prepare`（src/ergora/tasks.py:298）只在短准备阶段保留项目 revision；远程派发进入原 task 锁后离开控制 SQLite 事务。reference 的专用子进程保持登记 CONFIG/STATE 与原运行时的可选依赖/全局配置边界，不把旧导入全局复用为 Web request-local。37个模块的 AST 导入检查包含函数内导入，未见环；动态执行桥仍需按实际运行边理解，不能从静态图推断全部依赖。

导出所有者在 `reference_task_export.py:142` 使用 Git prepare/commit 条件ref事务，检查符号引用和已checkout分支；原结果核对、写前attempt与unknown只核现存ref的恢复路径符合手册。`reference_task_reconciliation.py:253` 在原完整history/spec/memo和outcome检查点之后发布fence，重新逐job核证据，保存独立evidence后才调用原IngressLeases.release；先释放再保存result的中断由原意图恢复，不改写原outcome。配置校验、外部输入/持久化身份、租约和进程生命周期守卫均仍在实际所有者内。本次没有新增需要另设通用框架的生产复用点。

使用手册的逐操作恢复表与实现一致，区别提交/批准/取消意图、投递事实、六阶段结果和外部清理；README不把CLI退出0或requested写成验收成功。备份说明明确控制home备份不包含执行STATE、Temporal历史、业务Git和原claim证据，需要联合保存并停止相关写者；旧agentflow仍从shell取连接，统一入口由登记执行环境读取。冻结原两本v2.2手册和旧HTML只作为原身份资料，未声称已含新CLI能力。

原18秒受控远程对账记录中的跨项目写者19.9227ms与收口摘要相符；c的模型时间/并发2及d的命令墙钟只按原条件保留。e没有新增生产热路径，不能由此推导吞吐、内存、规模化或SLA无回归。完整history与逐job产物重验的成本属于现有证据合同，当前文档没有把小演示或无比较的耗时记录称为性能优化。

**结论限制与后续责任**

结论只覆盖当前可信Linux容器、固定发行和实际所选后端的F3开发CLI/API闭环。原协议夹具与真实Temporal服务演练继续分列；旧计划、候选/分支漂移、审查checkout变化及丢响应没有全部在当前真实服务中重新注入，不能扩张为恶意Agent隔离或真实网络故障验收。主机掉电、跨机接管、真实Windows/WSL2完整执行、更多真实后端、外部GitHub/GitLab操作、大任务/大产物/吞吐、GPU质量性能及真实provider费用仍未验。

F4正式页面/人工待办/日志投影、F5证据引用索引/预算展示、F9训练导航与原生实验闭环仍是后续计划，当前文档没有将其列为已实现。作者完成本次文档提交、推送和远端身份核对后，可以登记F3完成并进入F4；应保留本报告、c/d报告及所有上述限制。
