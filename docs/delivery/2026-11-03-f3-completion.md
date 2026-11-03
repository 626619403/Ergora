# F3：正式开发任务CLI/API阶段收口

日期2026-11-03，分支refactor/architecture-foundations。本记录为F3.4e，生产/测试基线与最终身份均为`7139d1a85cdce13689d75471620da8dd143156a8`；后续仅更新文档，不重建或复跑同一候选的完整回归。c正常旅程[独立审查](2026-11-03-formal-task-normal-review.md)与d异常/恢复[独立审查](2026-11-03-formal-task-recovery-review.md)均通过，各一项证据范围P2已修正复核关闭，无未解决findings。本阶段[新独立综合审查](2026-11-03-f3-completion-review.md)需求与可维护性均通过、无新增findings；提交推送与远端核对后登记完整F3完成。

## 交付与责任

同一个正式tasks用例已连接CLI/API的本地合同分页/详情、预览/创建/恢复、单次提交与原ID恢复、原生状态、精确计划批准、协作取消、闭合原run外部证据、显式终态对账与精确候选导出。HTTP只做传输适配，不持有工作流状态；Temporal继续拥有六阶段，原executor拥有候选/可信检查/只读monitor/独立审查，IngressLeases拥有原工单claim。没有新调度器、数据库表、通用插件平台或新增必装依赖。

写操作以当前revision和原任务身份准备，跨资源意图/attempt先于副作用；远程阶段释放共享控制SQLite写锁，只持原task锁。未知提交/信号不重发，未知导出不重复写ref；终态对账保存原outcome与独立清理evidence，不能把CANCEL_UNCONFIRMED改成成功或伪BLOCKED。导出使用Git条件ref事务，不checkout/merge/推送业务分支。旧入口任务保留原CLI/config/state，不迁移在途history。

37个顶层Python模块和12个前端模块保持原包结构。当前模块/调用/数据归属及正式序列图已在[当前架构](../architecture/current.md)核正，尤其统一export/reconcile替代文档中的旧导出指向；冻结reference283文件、原两本v2.2手册和旧HTML保持内容身份，当前使用说明由[使用手册](../USAGE.md)与[训练手册](../TRAINING.md)承接。没有将新CLI功能反写成旧HTML已包含的功能。

## 用户入口与手册

[README首个开发任务](../../README.md#首个开发任务)已改为统一注册、所选服务、preview/create/start、原run与精确批准、结果检查/export和取消/reconcile。使用手册补完整顺序、逐操作恢复表、旧CLI的Temporal环境区别及联合备份范围；训练手册明确实验evidence批准后如何交给正式开发任务，以及训练/Forge/开发取消归属。Agent与项目手册同步当前对账和服务入口，长期运行优先现有services，无需统一注册用户手改ini。

正式任务网页、人工待办/日志投影仍归F4；证据引用索引/预算展示归F5，训练导航与原生实验闭环归F9。文件请求/回执协议继续依赖可信执行器、原task ID不可复用和已接受执行边界，不宣称每Agent强隔离。主许可证选择、更多真实后端/RSI与远端能力继续按原计划，不因本阶段收口变成已支持。

## 固定发行与验证矩阵

|范围|原始身份与实际结果|
|---|---|
|发行|c7411ae956108c2e23544fd476c0106e95b65a1d77a3a19c20a14caa3f5f8ceb非editable wheel，347文件×源码/完整开发/无SDK基础安装一致；冻结283及原runtime身份保持|
|最终Linux回归|同7139源码最终711 passed、19 skipped、36 subtests passed，1个既有Starlette弃用警告，1722.63秒；仅vendored PYTHONPATH，应用来自site-packages|
|跨平台|[CI41621015706](https://github.com/626619403/Ergora/actions/runs/41621015706)，Ubuntu3项/Windows4项必需步骤success并绑定完整候选；Linux完整执行不套用于Windows|
|b2恢复边界|65输入/读取、修后9+1定向、独立5项、无SDK两模板27CLI、实际SQLite提交后丢响应恢复；18秒受控远程阶段跨项目写者19.92ms，同task明确busy|
|c真实正常旅程|两个全新业务repo/登记/原run，真实Codex5/4个model stage、history302/326事件、7/6原job；精确计划/候选、可信检查与独立review、正式export/独立worktree3/6可信检查及4/11 unittest、44HTTP/两轮重开；业务main不变|
|d真实取消恢复|两新原run，worker停止时各一取消信号、重开同run闭合CANCEL_UNCONFIRMED；8个直接采样的原helper/child/driver/timeout进程消失，独立清理evidence精确claim释放，13HTTP/原结果保持|
|d失败与只读|真实baseline behavior exit17阻断、未调用模型、BLOCKED不能export；独立冻结monitor dirty/HEAD两种126拒绝；范围分别是服务门禁和monitor，不扩大为恶意模型/OS隔离|
|协议故障|原最终回归的创建/提交/批准/取消/导出/对账interruption、丢响应、旧计划、候选/owner/分支漂移；与c/d实际服务范围分列|

完整命令/原始记录位置、失败与修正和精确业务身份见[b2记录](2026-11-03-task-reconciliation-write.md)与[c/d记录](2026-11-03-formal-task-journeys.md)。私有`.ergora/checks/f3-task-reconciliation-write/`保存发行/回归/精确CI，`.ergora/checks/f3-formal-journeys/`保存模型/服务/HTTP/history/候选/进程/ledger验证及辅助脚本；这些原始数据不提交公开仓库。

## 当前核对与未验边界

e只做文档/链接/CLI帮助、生产/测试与源码/wheel/两安装身份重核，不改已通过的运行代码。静态核对已确认347包文件与源码/原wheel/两非editable安装一致，冻结283文件、37个顶层Python及12个前端模块保持；README所有独立ergora命令均由当前CLI parser检查，生产/测试/构建/CI文件相对7139无差异，git diff --check通过。本地链接/锚点在d报告到位后重核通过。结果保存在私有checks的check-completion.py与completion-static.json，不为文档增加生产测试或测试框架。

独立d审查完成实时查询后，已重新核5个精确原run/latest均为COMPLETED，本次Temporal无RUNNING workflow；通过正式services shutdown关闭本次登记的专用栈，返回confirmed、daemon=not_running，所管socket与PID文件消失，Temporal SQLite保留。原服务状态和完整命令保存在completion-shutdown.json；没有管理旧栈或其他用户服务。该关闭不修改原outcome/导出/对账证据。

最终CI沿用相同生产/测试7139的精确成功，不为纯文档再建昂贵CI。独立综合审查已重核本表与原始证据、现有所有者/契约、资源及性能限制，并独立检查347文件/两安装/283冻结、五份原history/spec/memo、57 HTTP、173索引和正式shutdown。37个Python模块AST导入无环，README26条独立命令parser通过。审查明确保留当前Linux实测与Windows CI的范围区别、历史快照缺口和未验维度，详细原始核算见私有completion-reviewer/audit.py/json。

实测仅覆盖当前可信Linux容器中的小演示、所选Codex及原native协议；完整执行的真实Windows/WSL2、真实GitHub/GitLab收发、任意远端隔离、主机掉电/跨机接管、大产物/大量任务/持续吞吐、GPU质量/性能和provider真实费用不在本F3验收中。正常HTTP前后只对实际104文件做字节快照，批准journal/owner回执未纳入该前后对照。c/d和b2性能只按原条件记录，不推导优化比例或服务SLA。

剩余动作：提交并推送当前工作分支并核远端；之后进入F4页面。不会合并main、强推或创建PR/MR。
